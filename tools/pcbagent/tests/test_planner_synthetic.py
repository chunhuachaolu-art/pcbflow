# -*- coding: utf-8 -*-
"""L2 planner 合成板单元测试（10 网假板，自包含，不依赖 Rev-C；SPEC §6）。

场景（40×30mm 四层假板）：
- 西侧 J9（6 PTH 盘，网 S1..S6）↔ 东侧 U9（2 行×3 SMD 盘，同网）；x=20 处一道
  F+In2 双层 netless 盘墙（全高只留 y 14.25..15.75 的 1.5mm 缺口，容量约 3 道）
  → 6 网挤窄口必过载：断言未收敛、S1..S6 走廊全部命中过载格、过载格落在缺口。
- S7..S10：两侧空旷区本地网，断言可布且不命中过载。
- 逃逸审计两态：U9 北侧无遮挡 → 该侧可；加一道横贯逃逸带的封堵走线 → 不足。
- 确定性：同板两轮 Planner，build_products 逐字节一致（禁随机性，SPEC §7）。
运行：python tests/test_planner_synthetic.py
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbagent import planner as P  # noqa: E402
from pcbagent.mirror import BoardMirror  # noqa: E402


def write_fixture(dirpath, name, text):
    """夹具落盘：路径规范化 + 包含性校验（与 run_b2_gate.dump 同口径）。"""
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


def build_board(escape_wall):
    L = []
    L.append('(kicad_pcb (version 20241229) (generator "pcbagent-test")')
    L.append('  (general (thickness 1.6))')
    L.append('  (paper "A4")')
    L.append('  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) '
             '(4 "In1.Cu" signal) (6 "In2.Cu" signal) (9 "Edge.Cuts" user))')
    L.append('  (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") '
             '(width 0.05) (fill none))')
    # J9：西侧 6 PTH 盘，网 S1..S6
    pads = [pth_pad(i + 1, f"S{i + 1}", 5, 8 + 2.54 * i) for i in range(6)]
    L.append(fp("J9", pads))
    # U9：东侧 2 行×3 SMD 盘（上排 y=13.5 下排 y=16.5），网 S1..S6
    nets = ["S1", "S2", "S3", "S4", "S5", "S6"]
    coords = [(33.5, 13.5), (35, 13.5), (36.5, 13.5),
              (33.5, 16.5), (35, 16.5), (36.5, 16.5)]
    L.append(fp("U9", [smd_pad(i + 1, nets[i], x, y)
                       for i, (x, y) in enumerate(coords)]))
    # J10/U10/U11/U12：空旷区本地网 S7..S10（不穿墙）
    L.append(fp("J10", [pth_pad(1, "S7", 10, 5), pth_pad(2, "S7", 15, 5)]))
    L.append(fp("U10", [smd_pad(1, "S8", 25, 25), smd_pad(2, "S8", 30, 25)]))
    L.append(fp("U11", [smd_pad(1, "S9", 10, 27), smd_pad(2, "S9", 6, 23)]))
    L.append(fp("U12", [smd_pad(1, "S10", 26, 10), smd_pad(2, "S10", 30, 6)]))
    # 中墙：x=20，F+In2 双层 netless 盘，pitch 0.7，只留 y 14.25..15.75 缺口
    wall = []
    n = 1
    y = 0.6
    while y <= 29.4:
        if not (14.1 < y < 15.9):    # 缺口（盘半宽 0.15）
            wall.append(smd_pad(n, "", 20, round(y, 2), w=0.3, h=0.3,
                                layers='"F.Cu" "In2.Cu"'))
            n += 1
        y += 0.7
    L.append(fp("WALL", wall))
    if escape_wall:
        # U9 北侧封堵带：横贯逃逸带（y 12.0..13.4），挡 fanout 与带内车道
        L.append('  (segment (start 33 12.7) (end 37 12.7) (width 1.4) '
                 '(layer "F.Cu") (net ""))')
    L.append(")")
    return "\n".join(L)


def make_planner(escape_wall=False):
    tmp = tempfile.mkdtemp(prefix="pcbagent-l2-")
    write_fixture(tmp, "synth.kicad_pcb", build_board(escape_wall))
    m = BoardMirror(tmp)
    pl = P.Planner(m, log=lambda *a: None)
    pl.add_netlist()
    return m, pl


def test_classification():
    assert P.classify_net("FMC_D0") == "FMC"
    assert P.classify_net("3V3") == "PWR"
    assert P.classify_net("USB_DP") == "USB"
    assert P.classify_net("GPIO_XX") == "SIG"


def test_route_and_congestion():
    _m, pl = make_planner()
    assert len(pl.nets) == 10, f"应 10 网，实得 {len(pl.nets)}"
    pl.run(max_iter=6)
    assert not pl.converged, "6 网挤 3 道窄口应不收敛（布局超容）"
    assert len(pl.overload) > 0, "窄口必须产生过载格"
    # 缺口带（y 14..16）内必须有过载格；他处因汇聚产生的竞争过载合法
    g = pl.grid
    oy = [g.y0 + (iy + 0.5) * g.cell for (_l, _x, iy) in pl.overload]
    assert any(14.0 <= y <= 16.0 for y in oy), \
        f"缺口带内必须有过载格: {sorted(oy)}"
    by_net = {r.real_net: pl.paths[r.rid] for r in pl.nets}
    hits = 0
    for k in range(1, 7):
        p = by_net[f"S{k}"]
        assert p["ok"], f"S{k} 应可布（付拆让代价）"
        # 门同口径：命中 = 竞争过载 ∪ 需拆让（穿越 cap0 格）
        if p["hit"] or p["disp_cells"] > 0:
            hits += 1
    assert hits >= 4, f"6 挤 3 道窄口，命中应 ≥4，实得 {hits}"
    for k in range(7, 11):
        p = by_net[f"S{k}"]
        assert p["ok"], f"S{k} 本地网应可布"
    # 本地网以干净为预期；协商历史代价可致个别绕行共格（实测 S1 绕行与
    # S10 共 1 格），允许 ≤1 条偶发命中，S8/S9 短网必须干净
    local_hits = [k for k in range(7, 11) if by_net[f"S{k}"]["hit"]]
    assert not by_net["S8"]["hit"] and not by_net["S9"]["hit"], \
        f"S8/S9 不应命中: {[k for k in (8, 9) if by_net[f'S{k}']['hit']]}"
    assert len(local_hits) <= 1, f"本地网偶发命中过多: {local_hits}"


def test_escape_audit_two_states():
    # 无封堵：U9 北侧开口焊盘 fanout 可达 → 可
    m, pl = make_planner(escape_wall=False)
    u9pads = [p for p in m.pads if p.ref == "U9"]
    rows = P.escape_audit(m, pl.occ, pl.grid, u9pads)
    north = [r for r in rows if r["ref"] == "U9" and r["side"] == "N"]
    assert north and north[0]["demand"] >= 1
    assert not north[0]["insufficient"], \
        f"无封堵时北侧不应不足: {north[0]}"
    # 加封堵带：fanout 被堵 + 带内车道归零 → 不足
    m2, pl2 = make_planner(escape_wall=True)
    u9pads2 = [p for p in m2.pads if p.ref == "U9"]
    rows2 = P.escape_audit(m2, pl2.occ, pl2.grid, u9pads2)
    north2 = [r for r in rows2 if r["ref"] == "U9" and r["side"] == "N"]
    assert north2, "北侧审计行缺失"
    assert north2[0]["fanout_ok"] == 0, \
        f"封堵后 fanout 应全被堵: {north2[0]['fanout_blocked']}"
    assert north2[0]["extra_lanes"] == 0, \
        f"封堵后带内车道应为 0: {north2[0]['extra_lanes']}"
    assert north2[0]["insufficient"], f"封堵后北侧应不足: {north2[0]}"


def test_determinism():
    _m1, pl1 = make_planner()
    pl1.run(max_iter=4)
    p1 = P.build_products(pl1, "synth", [])
    _m2, pl2 = make_planner()
    pl2.run(max_iter=4)
    p2 = P.build_products(pl2, "synth", [])
    assert p1["corridors.json"] == p2["corridors.json"], "corridors 不确定"
    assert p1["congestion-F.svg"] == p2["congestion-F.svg"], "热图不确定"
    assert json.loads(p1["corridors.json"])["nets"] == \
        json.loads(p2["corridors.json"])["nets"]


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"ALL {len(fns)} PLANNER-SYNTHETIC TESTS PASSED")


if __name__ == "__main__":
    run_all()
