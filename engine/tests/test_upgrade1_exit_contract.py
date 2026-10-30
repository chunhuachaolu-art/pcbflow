# -*- coding: utf-8 -*-
"""升级件①测试（2026-09-14，出口合同升级 D1-D5；docs/up1-exit-contract-design.md）。

覆盖：
- D1 schema 追加键：pad_terminals（分区级）/via_model（板级）可选——老板零回归；
  语义校验（shape↔size 维数、layers 形态）fail-closed；
- D1 adapter：真实 pad（绝对坐标/尺寸/层跨/形状/旋转外接盒）落 pad_terminals、
  via_model 孔径众数、退化分区同一 pad 双项；
- D1/D2 世界模型：真实焊盘铜与过孔铜入 v5.drc 场景（R5 逐对、归责 routes），
  焊盘不入容量；隐式 anchor 不入场景（合成板端子抽象归导出侧）；
- D2/D3 executor：孔铜严格 R5（无同分区豁免）、孔-孔最小孔心距 2r+R5、
  回流孔错位环序、via-plan 披露；
- D4 executor/export：全程折线焊盘心→焊盘心、过孔落折线顶点、回流孔
  [T,R,T] 桩段双侧相连、单点 stub 提升、导出 via 同网同点去重；
- D5 export：pad_terminals 逐项画法、via_model 孔径、anchor 随 route 层、
  ribbon 组网逐网落段；
- ④对账：退化分区零长声明与真实焊盘铜并存（零铜声明不产生 route 铜）；
- 三件 D 层对抗板（d1-pad-obstacle / d3-hole-offset / d4-dangling-seal）
  全链 ROUTED+feasible+双跑字节等。

零 out/v5-p5 接触；零 kicad-cli 依赖（DRC 实测在 out/v5-upg1 scratch 驱动）。
"""
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.adapters.kicad_adapter import convert_bytes_with_report  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.executor import execute_candidate  # noqa: E402
from v5.kicad_export import (via_model_params, write_kicad_pcb,  # noqa: E402
                             kicad_pcb_bytes)
from v5.metrics import clearance as clr  # noqa: E402
from v5.route_check import (ROUTES_SCHEMA_VERSION, RouteCheckError,  # noqa: E402
                            _BoardView, check_routes, validate_routes)
from v5.executor import _return_via_offsets, _via_min_hole  # noqa: E402

BOARDS = os.path.join(ROOT, "boards", "d")

_CACHE = {}


def _load(bid):
    if bid not in _CACHE:
        with open(os.path.join(BOARDS, "%s.board.v1.json" % bid),
                  encoding="utf-8") as f:
            _CACHE[bid] = load_board(json.load(f))
    return _CACHE[bid]


def _cand(board, layers=None):
    parts = [p["partition_id"] for p in board["partitions"]]
    lay = layers or {p["partition_id"]: p["layer_policy"]
                     for p in board["partitions"]}
    return {"candidate_id": "C-U1", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": parts, "layer_assignment": lay,
            "polylines": {}, "generation_trace": []}


def _exec(bid):
    key = ("exec", bid)
    if key not in _CACHE:
        board = _load(bid)
        _CACHE[key] = (board, execute_candidate(board, _cand(board)))
    return _CACHE[key]


# ---------------------------------------------------------------- 夹具板构造

SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True}]
WS = {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 12.0}


def make_board(board_id, partitions, nets, zones=None, stackup=None,
               via_model=None):
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup or SIG,
        "workspace": dict(WS),
        "zones": zones or [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_upgrade1_exit_contract.py",
                       "source_sha256": "0" * 64},
    }
    if via_model is not None:
        board["via_model"] = via_model
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def part(pid, a, b, ptype="MISC", width=0.2, **geo):
    g = {"endpoints": [list(a), list(b)]}
    g.update(geo)
    return {"partition_id": pid, "ptype": ptype, "layer_policy": "F.Cu",
            "planned_width": width, "current_a": 0, "geometry": g,
            "speed_class": "low_speed",
            "width_prior": {"w_min": width, "w_max": 0.4}}


def net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def routes_doc(board, entries):
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": ROUTES_SCHEMA_VERSION, "board_id": board["board_id"],
            "board_sha256": sha, "routes": entries, "negotiation_log": ["t"],
            "provenance": {"generator": "v5.executor/0.2.0", "board_sha256": sha}}


def entry(pid, nid, layer, pts, width=0.2, tv=None, rv=None):
    return {"partition_id": pid, "net_id": nid, "layer": layer,
            "polyline": [list(p) for p in pts], "width": width,
            "transition_vias": [list(v) for v in (tv or [])],
            "return_vias": [list(v) for v in (rv or [])]}


# ---------------------------------------------------------------- D1 schema

def test_schema_optional_keys_old_board_zero_regression():
    """追加键可选：不带 pad_terminals/via_model 的老板零回归载入（②后基线板）。"""
    board = _load("demo-03-small-mixed")
    for p in board["partitions"]:
        assert "pad_terminals" not in p["geometry"]
    assert "via_model" not in board


@pytest.mark.parametrize("mutation, frag", [
    ({"shape": "circle", "size_mm": [1.0, 2.0], "layers": ["F.Cu"]}, "size_mm"),
    ({"shape": "rect", "size_mm": [1.0], "layers": ["F.Cu"]}, "size_mm"),
    ({"shape": "circle", "size_mm": [0.0], "layers": ["F.Cu"]}, "size_mm"),
    ({"shape": "circle", "size_mm": [1.0], "layers": ["Nope.Cu"]}, "layers"),
    ({"shape": "circle", "size_mm": [1.0], "layers": "top"}, "layers"),
])
def test_pad_terminals_semantic_fail_closed(mutation, frag):
    """pad_terminals 语义校验 fail-closed（_BoardView 归一口，键路径报错；
    shape 枚举/endpoint 枚举/schema 面由 L0 载入拦，另测）。"""
    item = {"endpoint": 0}
    item.update(mutation)
    board = make_board("up1-bad", [part("P1", (2, 5), (18, 5),
                                        pad_terminals=[item])],
                       [net("N1", ["P1"])])
    with pytest.raises(RouteCheckError) as ei:
        _BoardView(board)
    assert "pad_terminals" in str(ei.value) and frag in str(ei.value)


def test_pad_terminals_schema_enum_fail_closed():
    """schema 面：shape/endpoint 枚举外值在 L0 载入即拒（键路径）。"""
    from v5.schema_loader import SchemaViolation
    item = {"endpoint": 0, "shape": "hex", "size_mm": [1.0], "layers": ["F.Cu"]}
    with pytest.raises(SchemaViolation):
        make_board("up1-bad2", [part("P1", (2, 5), (18, 5),
                                     pad_terminals=[item])],
                   [net("N1", ["P1"])])


def test_via_model_fail_closed():
    board = make_board("up1-badvm", [part("P1", (2, 5), (18, 5))],
                       [net("N1", ["P1"])], via_model={"drill_mm": 0.0,
                                                       "annular_mm": 0.1})
    with pytest.raises(RouteCheckError):
        _BoardView(board)


def test_via_model_params_default_and_override():
    board = make_board("up1-vm", [part("P1", (2, 5), (18, 5))], [net("N1", ["P1"])])
    vm = via_model_params(board)
    assert vm == {"drill": 0.3, "annular": 0.15, "size": 0.6, "radius": 0.3}
    board2 = make_board("up1-vm2", [part("P1", (2, 5), (18, 5))],
                        [net("N1", ["P1"])],
                        via_model={"drill_mm": 0.4, "annular_mm": 0.2})
    assert via_model_params(board2)["radius"] == pytest.approx(0.4)


# ---------------------------------------------------------------- D1 adapter

MINI_UP1 = """(kicad_pcb (version 20211014) (host up1 "t")
  (general (thickness 1.6))
  (layers (0 F.Cu signal) (31 B.Cu signal) (44 Edge.Cuts user))
  (net 0 "")
  (net 1 "SIG")
  (net 2 "ONE")
  (module M:U1 (layer F.Cu) (at 10 10 90)
    (pad 1 smd rect (at 1 0) (size 2 1) (layers "F.Cu") (net 1 "SIG"))
    (pad 2 thru_hole circle (at 0 -2) (size 1.4 1.4) (drill 0.7) (layers *.Cu) (net 1 "SIG"))
    (pad 3 smd oval (at 0 2) (size 0.8 0.5) (layers "F.Cu" "B.Cu") (net 2 "ONE")))
  (via (at 5 5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1 "SIG")))
"""


def _mini_up1_bytes():
    return MINI_UP1.encode("utf-8")


def test_adapter_lands_pad_terminals_and_via_model():
    board, report = convert_bytes_with_report(_mini_up1_bytes(), "up1-mini",
                                              "synthetic://up1-mini")
    parts = {p["partition_id"]: p for p in board["partitions"]}
    sig = parts["PT-SIG"]
    items = sig["geometry"]["pad_terminals"]
    # 端点=最远两 pad（旋转 90° 后的 rect 外接盒 / circle 原样）
    shapes = sorted(i["shape"] for i in items)
    assert shapes == ["circle", "rect"]
    for i in items:
        if i["shape"] == "rect":
            # 局部 (1,0) size 2x1 旋 90°：中心 (10,9)，外接盒 1x2
            assert i["size_mm"] == [pytest.approx(1.0), pytest.approx(2.0)]
            assert i["endpoint"] in (0, 1)
        else:
            assert i["size_mm"] == [pytest.approx(1.4)]
            assert i["layers"] == "all"          # *.Cu → "all"
    one = parts["PT-ONE"]
    # V5-R1 翻转（2026-09-25）：单 pad 退化网=同一 pad 单项（endpoint=0，
    # 逐 pad 化；旧 0.3.0 双项 0/1 口径由 R1-REPORT §2 披露），oval→rect
    oitems = one["geometry"]["pad_terminals"]
    assert [i["endpoint"] for i in oitems] == [0]
    assert oitems[0]["shape"] == "rect"
    assert oitems[0]["layers"] == ["F.Cu", "B.Cu"]
    assert board["via_model"] == {"drill_mm": 0.4, "annular_mm": 0.2}
    assert report["pad_terminal_count"] == 3
    assert report["pad_terminal_skipped"] == 0


def test_adapter_via_model_absent_without_usable_vias():
    text = MINI_UP1.replace(
        '(via (at 5 5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1 "SIG"))',
        "")
    board, _r = convert_bytes_with_report(text.encode("utf-8"), "up1-mini2",
                                          "synthetic://up1-mini2")
    assert "via_model" not in board
    # 场景半径回退缺省 0.3
    assert _BoardView(board).via_radius == pytest.approx(0.3)


def test_adapter_board_sha_changes_for_pads():
    """pad_terminals/via_model 入板 → board_sha256 随之变（重转重冻语义）。"""
    text = MINI_UP1.replace('(pad 3 smd oval (at 0 2) (size 0.8 0.5)',
                            '(pad 3 smd oval (at 0 2) (size 0.9 0.5)')
    board2, _r = convert_bytes_with_report(text.encode("utf-8"), "up1-mini",
                                           "synthetic://up1-mini")
    board1, _r = convert_bytes_with_report(_mini_up1_bytes(), "up1-mini",
                                           "synthetic://up1-mini")
    assert board1["provenance"]["board_sha256"] != \
        board2["provenance"]["board_sha256"]


# ---------------------------------------------------------------- D1/D2 场景

def test_real_pad_in_scene_r5_attributed_and_capacity_excluded():
    """真实焊盘铜入场景：他网 route 距焊盘 <R5 → 归责 infeasible（D1）；
    焊盘不入容量（端子非布线占用）。"""
    pads = [{"endpoint": 0, "shape": "rect", "size_mm": [2.0, 2.0],
             "layers": ["F.Cu"]},
            {"endpoint": 1, "shape": "rect", "size_mm": [2.0, 2.0],
             "layers": ["F.Cu"]}]
    zones = [{"zone_id": "C1", "kind": "corridor", "layers": "signal",
              "rect": {"x_min": 9.0, "y_min": 0.0, "x_max": 11.0,
                       "y_max": 12.0}, "capacity": 2.0}]
    board = make_board("up1-scene",
                       [part("PB", (10, 5), (10, 5), pad_terminals=pads),
                        part("P1", (1, 6.4), (19, 6.4))],
                       [net("NB", ["PB"]), net("N1", ["P1"])], zones=zones)
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 6.4], [19.0, 6.4]])])
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    r5 = [v for v in rep["attributed_violations"] if v["rule"] == "R5"]
    assert r5 and any("pad" in s for v in r5 for s in v["subjects"])
    # 容量只计 route 0.2（焊盘在走廊口不入容量）
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [0.2]



def test_via_copper_in_scene_r5():
    """过孔铜入场景（D2）：孔位距他网走线 <R5 → 归责 infeasible。"""
    board = make_board("up1-viascene",
                       [part("P1", (1, 8), (19, 8)),
                        part("P2", (1, 5.2), (19, 5.2))],
                       [net("N1", ["P1"]), net("N2", ["P2"])])
    doc = routes_doc(board, [
        entry("P1", "N1", "F.Cu", [[1.0, 8.0], [10.0, 8.0]], tv=[[10.0, 8.0]],
              rv=[[11.25, 8.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 8.0], [19.0, 8.0]], tv=[[10.0, 8.0]],
              rv=[[11.25, 8.0]]),
        entry("P2", "N2", "F.Cu", [[1.0, 5.2], [19.0, 5.2]])])
    rep = check_routes(board, doc)
    # 回流孔 (11.25,8) 半径 0.3 距 N2 线 (y=5.2) 2.5 → 合规；过渡孔 (10,8) 同；
    # 孔-线 R5 全对 ≥0.5 → 孔侧无违例
    vias_r5 = [v for v in rep["violations"] if v["rule"] == "R5"
               and any("via" in s for s in v["subjects"])]
    assert vias_r5 == []
    assert rep["feasible"] is True
    # 对照：孔位贴他网线（距 0.2）→ 归责
    board2 = make_board("up1-viascene2",
                        [part("P1", (1, 8), (19, 8)),
                         part("P2", (1, 7.5), (19, 7.5))],
                        [net("N1", ["P1"]), net("N2", ["P2"])])
    doc2 = routes_doc(board2, [
        entry("P1", "N1", "F.Cu", [[1.0, 8.0], [10.0, 8.0]], tv=[[10.0, 8.0]],
              rv=[[11.25, 8.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 8.0], [19.0, 8.0]], tv=[[10.0, 8.0]],
              rv=[[11.25, 8.0]]),
        entry("P2", "N2", "F.Cu", [[1.0, 7.5], [19.0, 7.5]])])
    rep2 = check_routes(board2, doc2)
    bad = [v for v in rep2["attributed_violations"] if v["rule"] == "R5"
           and any("via" in s for s in v["subjects"])]
    assert bad, "孔-线 R5 应归责"


def test_implicit_anchor_not_in_scene():
    """隐式 anchor 不入 v5 场景（文档化决定）：他网路线穿过端点抽象区
    （无 pad_terminals）不产生焊盘 R5。"""
    board = make_board("up1-implicit",
                       [part("PA", (10, 5), (10, 5)),       # 退化无 pad_terminals
                        part("P1", (1, 5), (19, 5))],
                       [net("NA", ["PA"]), net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 5.0], [19.0, 5.0]])])
    view = _BoardView(board)
    assert view.implicit_pads["PA"] is True and view.pad_items["PA"] == []
    rep = check_routes(board, doc)
    assert rep["feasible"] is True


def test_fourth_reconciliation_degenerate_with_real_pad():
    """④对账：退化分区带真实 pad_terminals——零长条目零铜（无 route 铜），
    真实焊盘铜以固定铜入场景（他网近距 → 归责）。"""
    pads = [{"endpoint": 0, "shape": "circle", "size_mm": [1.0],
             "layers": ["F.Cu"]},
            {"endpoint": 1, "shape": "circle", "size_mm": [1.0],
             "layers": ["F.Cu"]}]
    board = make_board("up1-recon",
                       [part("PD", (10, 5), (10, 5), pad_terminals=pads),
                        part("P1", (1, 5.4), (19, 5.4))],
                       [net("ND", ["PD"]), net("N1", ["P1"])])
    doc = routes_doc(board, [
        entry("PD", "ND", "F.Cu", [[10.0, 5.0], [10.0, 5.0]]),
        entry("P1", "N1", "F.Cu", [[1.0, 5.4], [19.0, 5.4]])])
    validate_routes(board, doc)
    rep = check_routes(board, doc)
    # 零长声明不产生 route 铜（其自身无违例）；真实焊盘铜 vs 他网 route → 归责
    assert any(v["rule"] == "R5" for v in rep["attributed_violations"])
    subjects = [s for v in rep["attributed_violations"] if v["rule"] == "R5"
                for s in v["subjects"]]
    assert any("pad" in s for s in subjects)


# ---------------------------------------------------------------- D3 单元

def test_return_via_offsets_contract():
    """D3 错位环序（升级件⑤ F2 扩容后契约；0.2.0 版契约钉 0.25mm/8 向域与其
    首候选 (1.25,0)，随枚举域扩容同步——披露于 F12 汇报）：全部 ≥ 2r+R5（缺省
    1.1）且 ≤ R4 上限 2.0；确定性；落 pitch/2 子栅格；首候选=最小距离马步环
    (1.0,0.5)（1.118）；旧域 24 候选仍全部在场（约束零放松）。"""
    min_hole, max_d, pitch = 1.1, 2.0, 0.25
    offs = _return_via_offsets(min_hole, max_d, pitch)
    assert offs == _return_via_offsets(min_hole, max_d, pitch)
    assert offs[0] == (1.0, 0.5)
    assert len(offs) == 84
    for dx, dy in offs:
        d = math.hypot(dx, dy)
        assert min_hole - 1e-9 <= d <= max_d + 1e-9
        assert abs(dx / (pitch / 2) - round(dx / (pitch / 2))) < 1e-9
        assert abs(dy / (pitch / 2) - round(dy / (pitch / 2))) < 1e-9
    # 旧 0.2.0 枚举域（0.25mm 栅格 8 向）逐项仍在场
    old_spots = {(1.25, 0.0), (1.5, 0.0), (1.75, 0.0), (2.0, 0.0),
                 (0.0, 1.25), (0.0, 1.5), (0.0, 1.75), (0.0, 2.0),
                 (1.0, 1.0), (1.25, 1.25)}
    for base in sorted(old_spots):
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            spot = (base[0] * sx, base[1] * sy)
            if min_hole - 1e-9 <= math.hypot(*spot) <= max_d + 1e-9:
                assert spot in offs, spot


def test_via_min_hole_formula():
    board = make_board("up1-mh", [part("P1", (2, 5), (18, 5))],
                       [net("N1", ["P1"])])
    assert _via_min_hole(_BoardView(board)) == pytest.approx(2 * 0.3 + 0.5)
    board2 = make_board("up1-mh2", [part("P1", (2, 5), (18, 5))],
                        [net("N1", ["P1"])],
                        via_model={"drill_mm": 0.4, "annular_mm": 0.2})
    assert _via_min_hole(_BoardView(board2)) == pytest.approx(2 * 0.4 + 0.5)


# ---------------------------------------------------------------- 夹具 1：焊盘障碍板

def test_fixture_pad_obstacle_detour():
    """d1-pad-obstacle：他网真实 2x2 焊盘挡道 → 路线绕行（铜缘 ≥R5）；
    退化分区（带真实焊盘）零长 trivially satisfied。"""
    board, res = _exec("d1-pad-obstacle")
    assert res["verdict"] == "ROUTED"
    doc = res["routes"]
    assert check_routes(board, doc)["feasible"] is True
    nb = [e for e in doc["routes"] if e["net_id"] == "NB"]
    assert len(nb) == 1 and nb[0]["polyline"] == [[10.0, 6.0], [10.0, 6.0]]
    rect = {"x_min": 9.0, "y_min": 5.0, "x_max": 11.0, "y_max": 7.0}
    mind = min(clr.segment_rect_distance(tuple(p), tuple(q), rect)
               for e in doc["routes"] if e["net_id"] == "NA"
               for p, q in zip(e["polyline"][:-1], e["polyline"][1:]))
    assert mind >= 0.5 - 1e-9
    # 路线确实绕行了（非直线）
    na = next(e for e in doc["routes"] if e["net_id"] == "NA")
    assert any(abs(p[1] - 6.0) > 1e-9 for p in na["polyline"])
    assert any("degenerate: zero-length partition trivially satisfied" in l
               for l in doc["negotiation_log"])


def test_fixture_pad_obstacle_export_draws_real_pad():
    board, res = _exec("d1-pad-obstacle")
    txt = kicad_pcb_bytes(board, res["routes"]).decode("utf-8")
    assert '(pad 1 smd rect (at 0 0) (size 2.0 2.0) (layers "F.Cu")' in txt
    # NA 的隐式 anchor 仍画（rect 1.0，层=其 route 层 F.Cu）
    assert '(pad 1 smd rect (at 0 0) (size 1.0 1.0) (layers "F.Cu")' in txt


# ---------------------------------------------------------------- 夹具 2：孔错位板

def test_fixture_hole_offset_d3_and_stubs():
    """d3-hole-offset：F.Cu 走廊被 ribbon 占满 → 中途换层；过渡/回流孔错位
    ≥2r+R5 且 ≤R4；[T,R,T] 桩段在相邻两层 entry 的折线顶点上。"""
    board, res = _exec("d3-hole-offset")
    assert res["verdict"] == "ROUTED"
    doc = res["routes"]
    assert check_routes(board, doc)["feasible"] is True
    nh = [e for e in doc["routes"] if e["net_id"] == "NH"]
    tvs = sorted({(v[0], v[1]) for e in nh for v in e["transition_vias"]})
    rvs = sorted({(v[0], v[1]) for e in nh for v in e["return_vias"]})
    assert len(tvs) == 1 and len(rvs) == 1   # 中途一孔（终点 B.Cu 直收）
    min_hole = _via_min_hole(_BoardView(board))
    layers = {e["layer"] for e in nh}
    assert layers == {"F.Cu", "B.Cu"}
    for tv in tvs:
        near = min(math.hypot(tv[0] - rv[0], tv[1] - rv[1]) for rv in rvs)
        assert min_hole - 1e-9 <= near <= 2.0 + 1e-9
    # 每个孔点（过渡+回流）是 ≥2 个 entry 的折线顶点（双侧相连，D4）
    for pt in tvs + rvs:
        on = sum(1 for e in nh
                 if any(abs(p[0] - pt[0]) <= 1e-9 and abs(p[1] - pt[1]) <= 1e-9
                        for p in e["polyline"]))
        assert on >= 2, "孔点须双侧相连 @%s" % (pt,)
    # via-plan 披露（D3）
    assert any("via-plan" in l and "D3" in l for l in doc["negotiation_log"])


def test_fixture_hole_offset_export_dedup_and_sizes():
    board, res = _exec("d3-hole-offset")
    txt = kicad_pcb_bytes(board, res["routes"]).decode("utf-8")
    assert txt.count("(via ") == 2     # 1 过渡 + 1 回流（同网同点去重后）
    assert '(size 0.6) (drill 0.3)' in txt   # via_model 缺省口径


# ---------------------------------------------------------------- 夹具 3：悬空板

def test_fixture_dangling_seal_full_coverage():
    """d4-dangling-seal：端点焊盘异层（F.Cu/B.Cu）→ 端点过孔 + 单点 stub
    提升 [T,R,T]；全程折线 pad 心→pad 心；可行。"""
    board, res = _exec("d4-dangling-seal")
    assert res["verdict"] == "ROUTED"
    doc = res["routes"]
    assert check_routes(board, doc)["feasible"] is True
    nd = [e for e in doc["routes"] if e["net_id"] == "ND"]
    assert {e["layer"] for e in nd} == {"F.Cu", "B.Cu"}
    first, last = nd[0]["polyline"][0], nd[-1]["polyline"][-1]
    assert [first[0], first[1]] == [2.0, 5.0]
    assert [last[0], last[1]] == [18.0, 5.0]
    # 导出：异层锚点焊盘 + 2 孔（T 与 R 各一，去重后）
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert txt.count("(via ") == 2
    assert '(pad 1 smd circle (at 0 0) (size 1.2 1.2) (layers "B.Cu")' in txt
    assert '(pad 1 smd rect (at 0 0) (size 1.0 1.0) (layers "F.Cu")' in txt


# ---------------------------------------------------------------- D5 导出

def test_export_via_model_sizes_and_dedup():
    board = make_board("up1-expvm",
                       [part("P1", (2, 5), (18, 5))],
                       [net("N1", ["P1"])],
                       via_model={"drill_mm": 0.4, "annular_mm": 0.2})
    doc = routes_doc(board, [
        entry("P1", "N1", "F.Cu", [[2.0, 5.0], [10.0, 5.0]], tv=[[10.0, 5.0]],
              rv=[[11.25, 5.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 5.0], [18.0, 5.0]], tv=[[10.0, 5.0]],
              rv=[[11.25, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert txt.count("(via ") == 2          # 衔接孔双方披露 → 去重后一孔 + 回流孔
    assert "(size 0.8) (drill 0.4)" in txt  # via_model 透传


def test_export_implicit_anchor_follows_route_layers():
    """隐式 anchor 层=该网 route entry 层（首 entry 层=端点 a、末 entry 层=
    端点 b）——换层网两端锚点分别落 F.Cu/B.Cu。"""
    board = make_board("up1-anchor",
                       [part("P1", (2, 5), (18, 5))], [net("N1", ["P1"])])
    doc = routes_doc(board, [
        entry("P1", "N1", "F.Cu", [[2.0, 5.0], [10.0, 5.0]], tv=[[10.0, 5.0]],
              rv=[[8.75, 5.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 5.0], [18.0, 5.0]], tv=[[10.0, 5.0]],
              rv=[[11.25, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    lines = txt.splitlines()
    mods = [l for l in lines if "(module " in l]
    assert '(module "V5-anchor-P1-a" (layer "F.Cu") (at 2.0 5.0)' in \
        " ".join(mods)
    assert '(module "V5-anchor-P1-b" (layer "B.Cu") (at 18.0 5.0)' in \
        " ".join(mods)


def test_export_ribbon_group_per_net_segments():
    """ribbon 组网逐网落段：组内每网一份全带中心线段（锚点皆有本网铜）。"""
    band = part("BS", (10.0, 2.0), (10.0, 18.0), ptype="BUS", width=0.15,
                copper_band=[9.2, 10.8], occupancy_mm=1.6)
    board = make_board("up1-ribbon",
                       [dict(band, ptype="BUS")],
                       [net("B0", ["BS"]), net("B1", ["BS"])])
    doc = routes_doc(board, [entry("BS", "B0", "F.Cu",
                                   [[10.0, 2.0], [10.0, 18.0]], width=1.6)])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    segs = [l for l in txt.splitlines() if l.strip().startswith("(segment")]
    assert len(segs) == 2        # B0 + B1 各一
    assert any("(net 1)" in l.split("(layer")[-1] for l in segs)
    assert any("(net 2)" in l.split("(layer")[-1] for l in segs)


# ---------------------------------------------------------------- 确定性

@pytest.mark.parametrize("bid", ["d1-pad-obstacle", "d3-hole-offset",
                                 "d4-dangling-seal"])
def test_fixtures_double_run_byte_equal(bid):
    """确定性红线：三夹具同输入双跑 canonical 字节等（含协商日志）。"""
    board = _load(bid)
    r1 = execute_candidate(board, _cand(board))
    r2 = execute_candidate(board, _cand(board))
    assert r1["verdict"] == r2["verdict"] == "ROUTED"
    assert canonical.canonical_json(r1["routes"]) == \
        canonical.canonical_json(r2["routes"])
    assert r1["negotiation_log"] == r2["negotiation_log"]
    assert r1["per_net"] == r2["per_net"]


@pytest.mark.parametrize("bid", ["d1-pad-obstacle", "d3-hole-offset",
                                 "d4-dangling-seal"])
def test_fixtures_export_double_run_byte_equal(bid):
    board, res = _exec(bid)
    b1 = kicad_pcb_bytes(board, res["routes"])
    b2 = kicad_pcb_bytes(board, execute_candidate(board, _cand(board))["routes"])
    assert b1 == b2
