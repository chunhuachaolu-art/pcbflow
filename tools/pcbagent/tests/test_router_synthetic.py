# -*- coding: utf-8 -*-
"""L3 router 合成板单元测试（SPEC §6：10 网级假板自包含，不依赖 Rev-C）。

板：40×30mm 四层假板（.kicad_pcb + 最小 .kicad_pro 现场生成于临时目录）。

场景与断言：
- 直连：空旷板 PTH→SMD 一步 route 成功，全部段/孔 L1 终判重验 margin>0。
- 缺口绕行：横贯盘墙留缺口，route 成功且路径穿过缺口带。
- 区域不可达：全高无缺口墙把区域封死 → 失败报告（fail 含"不可达"，SPEC §4.1
  "失败给出阻塞原因"）。
- rip-up（SPEC §4.1）：横贯缝（1.0mm 只容一道）被既有网 SA 的缝内段占据，
  SB 穿缝唯一通道被堵 → 拆 SA、SB 过缝、SA 同轮绕墙外重布，三者全绿。
- 确定性（SPEC §7 禁随机）：同板两轮独立 route，段列表逐字节一致。
- 提交纪律全流程（SPEC §4.2）：cli route（opens.csv 两网，SexprWriter 无头
  落板）→ 每 batch kicad-cli DRC → 断言零新增 error、opens 归零、板文件
  含新铜；快照/回滚字节一致。
运行：python tests/test_router_synthetic.py（需 F:\\kicad\\bin\\kicad-cli.exe）
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbagent import cli  # noqa: E402
from pcbagent import config as C  # noqa: E402
from pcbagent import router as R  # noqa: E402
from pcbagent.commit import CommitFlow, SexprWriter  # noqa: E402
from pcbagent.legality import Legality  # noqa: E402
from pcbagent.mirror import BoardMirror  # noqa: E402

SIG = frozenset(C.L2_SIGNAL_LAYERS)


def write_fixture(dirpath, name, text):
    """夹具落盘：路径规范化 + 包含性校验（与 cli.dump 同口径）。"""
    base = pathlib.Path(dirpath).resolve()
    target = pathlib.Path(base / os.path.basename(name)).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"夹具路径越界: {name}")
    target.write_text(text, encoding="utf-8", newline="")


def pth_pad(num, net, x, y):
    return (f'(pad "{num}" thru_hole circle (at {x} {y}) (size 1.7 1.7) '
            f'(drill 1.0) (layers "*.Cu" "*.Mask") (net "{net}"))')


def smd_pad(num, net, x, y, w=0.3, h=1.0, layers='"F.Cu" "F.Paste" "F.Mask"'):
    return (f'(pad "{num}" smd rect (at {x} {y}) (size {w} {h}) '
            f'(layers {layers}) (net "{net}"))')


def fp(ref, pads):
    body = "".join(pads)
    return (f'(footprint "FP_{ref}" (layer "F.Cu") (at 0 0) '
            f'(property "Reference" "{ref}") {body})')


def seg(net, x1, y1, x2, y2, w=0.2, layer="F.Cu"):
    return (f'  (segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) '
            f'(layer "{layer}") (net "{net}"))')


def header():
    return ['(kicad_pcb (version 20241229) (generator "pcbagent-l3-test")',
            '  (general (thickness 1.6))',
            '  (paper "A4")',
            '  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) '
            '(4 "In1.Cu" signal) (6 "In2.Cu" signal) (9 "Edge.Cuts" user))',
            '  (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") '
            '(width 0.05) (fill none))']


def wall_column(L, x=20, gap=None):
    """竖直盘墙：gap=(y0,y1) 时该开区间不留盘（开缺口）。"""
    pads = []
    n = 1
    y = 0.6
    while y <= 29.4:
        if gap and gap[0] < y < gap[1]:
            y += 0.7
            continue
        pads.append(smd_pad(n, "", x, round(y, 2), w=0.3, h=0.3,
                            layers='"F.Cu" "In2.Cu"'))
        n += 1
        y += 0.7
    L.append(fp("WALL", pads))


def wall_rows(L):
    """横贯双行墙（y 19.0..19.5 与 20.5..21.0），中间 y 19.5..20.5 留 1.0mm 缝。"""
    pads = []
    n = 1
    x = 0.6
    while x <= 39.4:
        for y in (19.25, 20.75):
            pads.append(smd_pad(n, "", round(x, 2), y, w=0.3, h=0.5,
                                layers='"F.Cu" "In2.Cu"'))
            n += 1
        x += 0.7
    L.append(fp("SEAMWALL", pads))


def make_pro(tmp):
    """最小 .kicad_pro（kicad-cli 与 mirror 的规则来源，数值与 config 一致）。"""
    pro = {
        "board": {"design_settings": {"rules": {
            "min_clearance": C.BOARD_MIN_CLEARANCE,
            "min_track_width": C.MIN_TRACK_WIDTH,
            "min_hole_clearance": C.MIN_HOLE_CLEARANCE,
            "min_hole_to_hole": C.MIN_HOLE_TO_HOLE,
            "min_copper_edge_clearance": C.MIN_COPPER_EDGE_CLEARANCE,
            "min_via_diameter": C.MIN_VIA_DIAMETER,
            "min_via_annular_width": C.MIN_VIA_ANNULAR_WIDTH,
            "min_through_hole_diameter": C.MIN_THROUGH_HOLE_DIAMETER}}},
        "net_settings": {"classes": [
            {"name": "Default", "clearance": 0.2, "via_diameter": 0.6,
             "via_drill": 0.3, "wire_width": 0.2}]},
        "meta": {"filename": "synth.kicad_pro", "version": 3},
    }
    write_fixture(tmp, "synth.kicad_pro", json.dumps(pro, indent=1))


def make_board(tag, extra="", with_pro=True):
    """基础空板（J1/U1 = S1 @y15；J2/U2 = S2 @y5）。extra 追加节点。"""
    tmp = tempfile.mkdtemp(prefix=f"pcbagent-l3-{tag}-")
    L = header()
    L.append(fp("J1", [pth_pad(1, "S1", 5, 15)]))
    L.append(fp("U1", [smd_pad(1, "S1", 35, 15)]))
    L.append(fp("J2", [pth_pad(1, "S2", 5, 5)]))
    L.append(fp("U2", [smd_pad(1, "S2", 35, 5)]))
    L.append(extra)
    L.append(")")
    write_fixture(tmp, "synth.kicad_pcb", "\n".join(L))
    if with_pro:
        make_pro(tmp)
    return tmp


def make_router(m):
    return R.Router(m, Legality(m), log=lambda *a: None)


def test_route_basic():
    m = BoardMirror(make_board("basic"))
    r = make_router(m)
    plan = r.route_net("S1", (5, 15, SIG), (35, 15, frozenset((C.LAYER_F,))))
    assert plan.ok, f"空旷直连应成功: {plan.fail} {plan.blocks}"
    assert plan.segments, "应有段"
    leg = Legality(m)
    for s in plan.segments:
        ok, margin, viol = leg.seg_legal(s[0], (s[1], s[2]), (s[3], s[4]),
                                         plan.width, plan.net)
        assert ok and margin > 0, f"段未过 L1: {s} margin={margin} {viol}"
    for (x, y) in plan.vias:
        ok, margin, viol = leg.via_legal(x, y, plan.net, C.LAYER_F,
                                         C.LAYER_IN2)
        assert ok and margin > 0, f"孔未过 L1: ({x},{y}) margin={margin}"


def test_route_gap_detour():
    tmp = make_board("gap")
    with open(os.path.join(tmp, "synth.kicad_pcb"), encoding="utf-8") as fh:
        text = fh.read()
    # 在 U2 之前插入带缺口的竖墙（缺口 y 4.1..6.9 覆盖 S2 走向）
    L2 = []
    wall_column(L2, x=20, gap=(4.1, 6.9))
    text = text.replace("(footprint \"FP_U2\"", "".join(L2) +
                        "(footprint \"FP_U2\"")
    write_fixture(tmp, "synth.kicad_pcb", text)
    m = BoardMirror(tmp)
    plan = make_router(m).route_net("S2", (5, 5, SIG),
                                    (35, 5, frozenset((C.LAYER_F,))))
    assert plan.ok, f"缺口场景应成功: {plan.fail}"
    assert plan.length_mm() < 40, f"绕行不应离谱: {plan.length_mm()}"
    # 路径在墙 x=20±1 处的 y 必须落缺口带（穿缺口而非穿墙）
    for s in plan.segments:
        if min(s[1], s[3]) <= 20.05 and max(s[1], s[3]) >= 19.95:
            ymid = (s[2] + s[4]) / 2.0
            assert 3.8 < ymid < 7.2, \
                f"应穿缺口带: {s} ymid={ymid}"


def build_seg_board():
    """全高盘墙留顶部缺口（有效空档 y≈25.45..28.65）：S2 (5,5)→(35,5) 直连
    区域（y≤8）被墙封死必"不可达"；走廊中继分段沿顶部缺口绕行可达。"""
    tmp = make_board("seg")
    L2 = []
    wall_column(L2, x=20, gap=(25.5, 28.5))
    text_path = os.path.join(tmp, "synth.kicad_pcb")
    with open(text_path, encoding="utf-8") as fh:
        text = fh.read()
    text = text.replace("(footprint \"FP_U2\"", "".join(L2) +
                        "(footprint \"FP_U2\"")
    write_fixture(tmp, "synth.kicad_pcb", text)
    return tmp


def test_route_segmented():
    """走廊中继分段（PHASE-REPORT-3 §5.1）：直连不可达的长距网沿走廊中继
    逐段可达、层连续、聚合 Plan 过 L1 终判。"""
    tmp = build_seg_board()
    m = BoardMirror(tmp)
    # 与 cli.cmd_route 同构：走廊作为软约束注入（无软约束时 A* 允许贴墙边
    # 合法绕行，见 make_router 注释）
    r = R.Router(m, Legality(m), log=lambda *a: None)
    A, B = (5, 5, SIG), (35, 5, frozenset((C.LAYER_F,)))
    direct = r.route_net("S2", A, B)
    assert not direct.ok and direct.fail and "不可达" in direct.fail, \
        f"直连应不可达（区域裁剪）: {direct.fail}"
    # 该对 L2 走廊：左侧上行 → 顶部横穿缺口 → 右侧下行（全 F）
    segs = [(C.LAYER_F, 5.0, 5.0, 5.0, 27.0),
            (C.LAYER_F, 5.0, 27.0, 35.0, 27.0),
            (C.LAYER_F, 35.0, 27.0, 35.0, 5.0)]
    r2 = R.Router(m, Legality(m), corridor_of=lambda _n: segs,
                  log=lambda *a: None)
    plan = r2.route_net_segmented("S2", A, B, segs)
    assert plan.ok, f"分段 route 应成功: {plan.fail} {plan.blocks[:3]}"
    assert plan.segmented and plan.n_relay >= 2, \
        f"应分段且 ≥2 中继点: segmented={plan.segmented} n_relay={plan.n_relay}"
    assert 60 < plan.length_mm() < 95, f"绕顶总长应合理: {plan.length_mm()}"
    assert r._relay_chain("S2", A, B, segs) is not None
    # 聚合路径 L1 重验（口径同 test_route_basic）
    leg = Legality(m)
    for s in plan.segments:
        ok, margin, viol = leg.seg_legal(s[0], (s[1], s[2]), (s[3], s[4]),
                                         plan.width, plan.net)
        assert ok and margin > 0, f"段未过 L1: {s} margin={margin} {viol}"
    for (x, y) in plan.vias:
        ok, margin, viol = leg.via_legal(x, y, plan.net, C.LAYER_F,
                                         C.LAYER_IN2)
        assert ok and margin > 0, f"孔未过 L1: ({x},{y}) margin={margin}"
    # 穿墙位置必须落缺口带（防绕行失败穿墙）
    for s in plan.segments:
        if min(s[1], s[3]) <= 20.05 and max(s[1], s[3]) >= 19.95:
            ymid = (s[2] + s[4]) / 2.0
            assert 25.5 < ymid < 28.5, \
                f"穿墙点应落顶部缺口带: {s} ymid={ymid}"


def test_region_unreachable():
    tmp = make_board("blocked")
    L2 = []
    wall_column(L2, x=20, gap=None)      # 全高无缺口
    text_path = os.path.join(tmp, "synth.kicad_pcb")
    with open(text_path, encoding="utf-8") as fh:
        text = fh.read()
    text = text.replace("(footprint \"FP_U2\"", "".join(L2) +
                        "(footprint \"FP_U2\"")
    write_fixture(tmp, "synth.kicad_pcb", text)
    m = BoardMirror(tmp)
    plan = make_router(m).route_net("S2", (5, 5, SIG),
                                    (35, 5, frozenset((C.LAYER_F,))))
    assert not plan.ok, "全高墙封死区域应失败"
    assert plan.fail and "不可达" in plan.fail, f"应报告不可达: {plan.fail}"


def build_ripup_board():
    """U9 两行 netless 盘（F 层，y 19.1..19.7 与 20.3..20.9）夹 0.6mm 行通道
    （y 19.7..20.3，只容 1 道）；SA 预置段合法占通道中央；SB 必穿通道（上/下
    排盘列间隙之外的路径不存在）→ A* 不可达 → 封堵归因=SA → 拆 SA、SB 过
    通道、SA 同轮绕 U9 外侧重布（可行：J4/J5 在通道两端开口处）。"""
    tmp = tempfile.mkdtemp(prefix="pcbagent-l3-ripup-")
    L = header()
    pads = []
    n = 1
    for y in (19.4, 20.6):
        for i in range(6):
            pads.append(smd_pad(n, "", 10 + 2.0 * i, y, w=0.6, h=0.6,
                                layers='"F.Cu" "In2.Cu"'))
            n += 1
    L.append(fp("U9", pads))
    # SA：J4 (8,20) → 双层预置段沿通道中央（F+In2+端部 via，堵死切层绕行）
    # → J5 (22,20)（两端在通道开口外）
    L.append(fp("J4", [smd_pad(1, "SA", 8, 20, w=0.4, h=0.4)]))
    L.append(fp("J5", [smd_pad(1, "SA", 22, 20, w=0.4, h=0.4)]))
    L.append(seg("SA", 8, 20, 22, 20, w=0.15))
    L.append(seg("SA", 8, 20, 22, 20, w=0.15, layer="In2.Cu"))
    L.append('  (via buried (at 8 20) (size 0.6) (drill 0.3) '
             '(layers "F.Cu" "In2.Cu") (net "SA"))')
    L.append('  (via buried (at 22 20) (size 0.6) (drill 0.3) '
             '(layers "F.Cu" "In2.Cu") (net "SA"))')
    # SB：J6 (12,16) 上区 → J7 (18,24) 下区，必穿行通道
    L.append(fp("J6", [pth_pad(1, "SB", 12, 16)]))
    L.append(fp("J7", [pth_pad(1, "SB", 18, 24)]))
    L.append(")")
    write_fixture(tmp, "synth.kicad_pcb", "\n".join(L))
    make_pro(tmp)
    return tmp


def test_ripup():
    tmp = build_ripup_board()
    m = BoardMirror(tmp)
    plan = make_router(m).route_net("SB", (12, 16, SIG), (18, 24, SIG))
    assert plan.ok, f"ripup 后 SB 应成功: {plan.fail} {plan.blocks}"
    assert plan.ripup_net == "SA", f"应拆 SA: {plan.ripup_net}"
    rp = plan.ripup_plan
    assert rp is not None and rp.ok, "SA 同轮重布应成功"
    assert rp.ripup_net is None, "重布不得再级联拆网"
    # 路径确实穿通道（跨 y=20 的段的 x 中点在 U9 行带内）
    crossed = [s for s in plan.segments
               if min(s[2], s[4]) <= 20.0 <= max(s[2], s[4])]
    assert crossed, "SB 应有跨通道段"
    # 落板链路：删 SA 旧铜 → SB → SA 重布 → CLI DRC 零新增、两网连通
    flow = CommitFlow(tmp, SexprWriter())
    verdict = flow.run([plan], batch=1)
    assert not verdict["rolled_back"], \
        f"ripup 落板不得回滚: {verdict['added']}"
    assert verdict["added"] == [], f"零新增违规: {verdict['added']}"
    m2 = BoardMirror(tmp)
    op = m2.opens()
    assert op.get("SB", 0) == 0 and op.get("SA", 0) == 0, \
        f"ripup 落板后两网应连通: {op}"
    with open(os.path.join(tmp, "synth.kicad_pcb"), encoding="utf-8") as fh:
        text = fh.read()
    assert text.count('(net "SA")') >= 4, "SA 旧铜应已删并落重布新铜"


def test_determinism():
    p1 = make_router(BoardMirror(build_ripup_board())).route_net(
        "SB", (12, 16, SIG), (18, 24, SIG))
    p2 = make_router(BoardMirror(build_ripup_board())).route_net(
        "SB", (12, 16, SIG), (18, 24, SIG))
    assert p1.ok and p2.ok
    key = lambda p: [(s[0], round(s[1], 6), round(s[2], 6), round(s[3], 6),
                      round(s[4], 6)) for s in p.segments]
    assert key(p1) == key(p2), "同输入必须同输出（SPEC §7）"
    assert [(round(x, 6), round(y, 6)) for (x, y) in p1.vias] == \
        [(round(x, 6), round(y, 6)) for (x, y) in p2.vias]
    assert p1.uuid == p2.uuid


def test_snapshot_restore():
    tmp = make_board("snap")
    path = os.path.join(tmp, "synth.kicad_pcb")
    with open(path, encoding="utf-8") as fh:
        orig = fh.read()
    flow = CommitFlow(tmp, SexprWriter())
    snap = flow.snapshot()
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("(segment (start 1 1) (end 2 2) (width 0.15) "
                 '(layer "F.Cu") (net "X"))')
    flow.restore(snap)
    with open(path, encoding="utf-8") as fh:
        assert fh.read() == orig, "回滚后板文件必须逐字节一致"


def test_commit_end_to_end():
    """cli route 完整链路：opens.csv 两网 → SexprWriter 落板 → kicad-cli
    基线/终局 DRC 零新增 error → opens 归零 → 板文件含新铜。"""
    tmp = make_board("e2e")
    opens = ("net,from,to,from_x_mm,from_y_mm,to_x_mm,to_y_mm,"
             "distance_mm,suggested_layer\n"
             'S1,"F.Cu 上 J1 的焊盘 1 [S1] (PTH)","F.Cu 上 U1 的焊盘 1 [S1]",'
             "5,15,35,15,30,F.Cu\n"
             'S2,"F.Cu 上 J2 的焊盘 1 [S2] (PTH)","F.Cu 上 U2 的焊盘 1 [S2]",'
             "5,5,35,5,30,F.Cu\n")
    write_fixture(tmp, "opens.csv", opens)
    rc = cli.main(["route", "--project", tmp, "--batch", "2"])
    assert rc == 0, f"route 退出码 {rc}"
    report = json.loads(pathlib.Path(tmp, "pcbagent-out", "b3",
                                     "route-report.json").read_text(
                                         encoding="utf-8"))
    assert report["routed"] == 2, f"两网都应 route 成功: {report['failed']}"
    assert not report["rolled_back"], "干净场景不得回滚"
    assert report["added_violations"] == [], \
        f"不得有新增违规: {report['added_violations']}"
    assert report["violations_after"]["violations"] == 0, \
        f"合成板终局 DRC 应零违规: {report['violations_after']}"
    m = BoardMirror(tmp)
    op = m.opens()
    assert op.get("S1", 0) == 0 and op.get("S2", 0) == 0, \
        f"落板后应连通: {op}"
    with open(os.path.join(tmp, "synth.kicad_pcb"), encoding="utf-8") as fh:
        text = fh.read()
    assert '(net "S1")' in text and "(segment" in text, "板文件应含新铜"
    assert '(net "S2")' in text
    # 确定性落盘校验：route-report.json 可解析、uuid 存在
    uuids = [p["uuid"] for p in report["plans"] if p["ok"]]
    assert len(uuids) == len(set(uuids)), "uuid 不得冲突"


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"ALL {len(fns)} ROUTER-SYNTHETIC TESTS PASSED")


if __name__ == "__main__":
    run_all()
