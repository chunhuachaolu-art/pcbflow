# -*- coding: utf-8 -*-
"""LIVE2B-S2 纯函数测试（不碰 live 板；几何用注入/合成数据）。"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import live2s2_proposal as P  # noqa: E402


# ---- parse_item_desc --------------------------------------------------------
def test_parse_item_desc_track_via_pad_unknown():
    g = P.parse_item_desc("走线 [3V3] (21.5000,19.1500)-(21.4500,19.1000) w=0.2")
    assert g["kind"] == "track" and g["net"] == "3V3"
    assert (g["x1"], g["y1"], g["x2"], g["y2"]) == (21.5, 19.15, 21.45, 19.1)
    v = P.parse_item_desc("过孔 [GND] (39.6925,57.6375) size=0.6 drill=0.3")
    assert v["kind"] == "via" and v["size"] == 0.6 and v["drill"] == 0.3
    d = P.parse_item_desc("U2 焊盘 49 [3V3] (41.4000,56.3500) rect 1.51x0.458")
    assert d["kind"] == "pad" and d["ref"] == "U2" and d["number"] == "49"
    assert d["net"] == "3V3" and d["x"] == 41.4
    assert P.parse_item_desc("别的描述") is None
    assert P.parse_item_desc("") is None


# ---- widened_bbox / route_bbox / exits_region -------------------------------
def test_widened_bbox_clamps_to_board():
    bb = P.widened_bbox((0.0, 0.0, 70.0, 70.0), 2.0, 3.0, 5.0, 4.0, 8.0)
    assert bb == (0.0, 0.0, 13.0, 12.0)
    bb2 = P.widened_bbox((0.0, 0.0, 70.0, 70.0), 40.0, 56.0, 45.0, 59.5, 5.0)
    assert bb2 == (35.0, 51.0, 50.0, 64.5)


def test_route_bbox_and_exits_region():
    segs = [[0, 41.4, 52.85, 48.65, 59.4773]]
    bb = P.route_bbox(segs, [])
    assert bb == [41.4, 52.85, 48.65, 59.4773]
    assert P.exits_region(bb, [40.4, 55.35, 46.2, 60.45]) is True
    inside = P.exits_region([41.0, 56.0, 45.0, 59.0],
                            [40.4, 55.35, 46.2, 60.45])
    assert inside is False
    assert P.exits_region(None, [0, 0, 1, 1]) is None


# ---- landing_points ---------------------------------------------------------
def test_landing_points_order_dedup_exclude_topk():
    items = [
        ("走线 [3V3] (41.7850,59.4770)-(42.0000,60.0000) w=0.2", [0]),
        ("过孔 [3V3] (10.0000,10.0000) size=0.6 drill=0.3", [0, 6]),
        ("C9 焊盘 1 [3V3] (43.0000,59.0000) roundrect 0.9x0.95", [0]),
        ("走线 [3V3] (41.7860,59.4780)-(42.5000,60.0000) w=0.2", [0]),
    ]
    pts = P.landing_points(items, 41.4, 56.35, top_k=4,
                           exclude_xy=(41.785, 59.477))
    assert len(pts) <= 4
    d = [p["dist_to_a_mm"] for p in pts]
    assert d == sorted(d)
    assert all(abs(p["x"] - 41.785) > 0.1 or abs(p["y"] - 59.477) > 0.1
               for p in pts)
    kinds = {p["kind"] for p in pts}
    assert kinds <= {"track_end", "via", "pad"}
    assert any(p["layers"] == [0, 6] for p in pts)


# ---- closure_verdict --------------------------------------------------------
def _route(ok=True):
    return {"net": "3V3", "ok": ok, "fail": None if ok else "A* 不可达",
            "blocks": [], "width": 0.2, "via_size": 0.6, "via_drill": 0.3,
            "refine_rounds": 1,
            "segments": [[0, 41.4, 56.35, 48.65, 59.4773]], "vias": [],
            "length_mm": 4.5}


def test_closure_verdict_sat_with_independent_ok():
    steps = [{"margin_mm": 3.0, "route": _route(False)},
             {"margin_mm": 5.0, "route": _route(True)}]
    row = P.closure_verdict("RPL-019", "3V3", steps, [],
                            [40.4, 55.35, 46.2, 60.45],
                            {"all_ok": True})
    assert row["live2s2_status"] == "SAT"
    assert row["witness"]["margin_mm"] == 5.0
    assert row["witness"]["exits_s1_corridor_region"] is True
    assert row["route_plan"]["uuid"] and len(row["route_plan"]["segments"]) == 1


def test_closure_verdict_independent_fail_downgrades_to_unknown():
    steps = [{"margin_mm": 5.0, "route": _route(True)}]
    row = P.closure_verdict("RPL-019", "3V3", steps, [],
                            [40.4, 55.35, 46.2, 60.45], {"all_ok": False})
    assert row["live2s2_status"] == "UNKNOWN"
    assert row["unknown_reason"] == "unknown:independent_check_failed"


def test_closure_verdict_no_witness_unknown():
    steps = [{"margin_mm": 3.0, "route": _route(False)}]
    row = P.closure_verdict("RPL-019", "3V3", steps, [],
                            [40.4, 55.35, 46.2, 60.45], None)
    assert row["live2s2_status"] == "UNKNOWN"
    assert "no_witness" in row["unknown_reason"]


# ---- 板文本：footprint_at / move_footprint / strip_copper --------------------
_BOARD = (
    '(kicad_pcb (version "20241229")\r\n'
    '(footprint "R_0603"\r\n'
    '\t(layer "F.Cu")\r\n'
    '\t(uuid "u-c5")\r\n'
    '\t(at 10 10 90)\r\n'
    '\t(property "Reference" "C5" (at 0 0 0) (layer "F.SilkS")\r\n'
    '\t\t(uuid "r-c5")\r\n'
    '\t)\r\n'
    '\t(pad "1" smd roundrect (at -0.75 0 90) (size 0.9 0.95)\r\n'
    '\t\t(layers "F.Cu") (net "3V3") (uuid "p1"))\r\n'
    ')\r\n'
    '\t(segment\r\n'
    '\t\t(start 9.25 10)\r\n'
    '\t\t(end 8.0 10)\r\n'
    '\t\t(width 0.2)\r\n'
    '\t\t(layer "F.Cu")\r\n'
    '\t\t(net "3V3")\r\n'
    '\t\t(uuid "s-1")\r\n'
    '\t)\r\n'
    '\t(segment\r\n'
    '\t\t(start 0 0)\r\n'
    '\t\t(end 1 1)\r\n'
    '\t\t(width 0.2)\r\n'
    '\t\t(layer "F.Cu")\r\n'
    '\t\t(net "GND")\r\n'
    '\t\t(uuid "s-2")\r\n'
    '\t)\r\n'
    '\t(via buried\r\n'
    '\t\t(at 9.25 10)\r\n'
    '\t\t(size 0.6)\r\n'
    '\t\t(drill 0.3)\r\n'
    '\t\t(layers "F.Cu" "In2.Cu")\r\n'
    '\t\t(net "3V3")\r\n'
    '\t\t(uuid "v-1")\r\n'
    '\t)\r\n'
    ')\r\n'
    ')\r\n'
)


def test_footprint_at_and_move():
    x, y, rot = P.footprint_at(_BOARD, "C5")
    assert (x, y, rot) == (10.0, 10.0, 90.0)
    t2 = P.move_footprint(_BOARD, "C5", 1.0, -0.5)
    assert P.footprint_at(t2, "C5") == (11.0, 9.5, 90.0)
    assert t2.count('(net "3V3")') == _BOARD.count('(net "3V3")')


def test_move_footprint_rejects_out_of_bound():
    try:
        P.move_footprint(_BOARD, "C5", 3.0, 0.0)
        raise AssertionError("应拒绝超界移位")
    except ValueError:
        pass


def test_strip_copper_hits_and_misses():
    segs = [{"layer_name": "F.Cu", "x1": 8.0, "y1": 10.0, "x2": 9.25,
             "y2": 10.0, "net": "3V3"}]
    vias = [{"x": 9.25, "y": 10.0, "net": "3V3"}]
    t2, n = P.strip_copper(_BOARD, segs, vias)
    assert n == {"segments": 1, "vias": 1}
    assert "(uuid \"s-1\")" not in t2 and "(uuid \"v-1\")" not in t2
    assert "(uuid \"s-2\")" in t2
    try:
        P.strip_copper(_BOARD, [{"layer_name": "F.Cu", "x1": 8.0, "y1": 10.0,
                                 "x2": 9.25, "y2": 10.0, "net": "GND"}], [])
        raise AssertionError("应报账单项未命中")
    except ValueError:
        pass


# ---- disturbance_bill -------------------------------------------------------
def test_disturbance_bill_classifies_target_and_other():
    pad_prims = [("padprim", 9.25, 10.0)]
    pads = [{"number": "1", "net": "3V3", "prims": pad_prims,
             "x": 9.25, "y": 10.0, "layers": [0]},
            {"number": "2", "net": "GND", "prims": pad_prims,
             "x": 9.25, "y": 10.0, "layers": [0]}]

    def dist(x, y, prim):
        return 0.0 if prim[1:] == (x, y) else 1.0

    tracks = [
        {"layer": 0, "layer_name": "F.Cu", "net": "3V3", "width": 0.2,
         "x1": 9.25, "y1": 10.0, "x2": 8.0, "y2": 10.0},
        {"layer": 0, "layer_name": "F.Cu", "net": "GND", "width": 0.15,
         "x1": 9.25, "y1": 10.0, "x2": 7.0, "y2": 9.0},
        {"layer": 0, "layer_name": "F.Cu", "net": "GND", "width": 0.15,
         "x1": 50.0, "y1": 50.0, "x2": 51.0, "y2": 50.0},
    ]
    vias = [{"x": 9.25, "y": 10.0, "net": "3V3", "size": 0.6, "drill": 0.3}]
    bill = P.disturbance_bill("C5", pads, tracks, vias, "3V3", dist)
    assert bill["counts"]["segments_total"] == 2
    assert bill["counts"]["target_net_own"] == 2   # seg 3V3 + via 3V3
    assert bill["counts"]["other_net"] == 1
    assert bill["other_nets"] == ["GND"]
    other = [s for s in bill["segments"] if s["cls"] == "other_net"]
    assert other[0]["dangling_xy"] == [7.0, 9.0]
    own = [s for s in bill["segments"] if s["cls"] == "target_net_own"]
    assert own[0]["dangling_xy"] == [8.0, 10.0]


# ---- 候选生成 / 排序 / 收行账 ------------------------------------------------
def test_candidate_moves_bounded_and_radial():
    mv = P.candidate_moves((11.0, 10.0), (9.25, 10.0))
    assert all(abs(m["dx"]) <= 2.0 and abs(m["dy"]) <= 2.0 for m in mv)
    radial = [m for m in mv if m["label"].startswith("radial")]
    assert radial and all(abs(m["dx"] + m["dy"]) > 0 for m in radial)
    away = radial[0]
    assert away["dx"] > 0   # 远离口袋端点（口袋在 -x 侧）


def test_rank_candidates_and_closable_rows():
    evals = [
        {"candidate_id": "b", "closable_rows": 1, "other_net_items": 4,
         "total_items": 6},
        {"candidate_id": "a", "closable_rows": 1, "other_net_items": 2,
         "total_items": 3},
        {"candidate_id": "c", "closable_rows": 0, "other_net_items": 0,
         "total_items": 2},
    ]
    ranked = P.rank_candidates(evals)
    assert [e["candidate_id"] for e in ranked] == ["a", "b", "c"]
    base = {"3V3": "SAT", "GNDA": "UNSAT"}
    verdicts = {"GNDA": {"status": "SAT"}, "3V3": {"status": "UNKNOWN"}}
    gl = P.closable_rows_of(verdicts, base)
    assert gl == {"gained": ["GNDA"], "lost": ["3V3"], "closable_rows": 1}


def test_pocket_side():
    assert P.pocket_side(571, 12) == "B"
    assert P.pocket_side(12, 571) == "A"
    assert P.pocket_side(5, 5) == "A"
    assert P.pocket_side(None, None) is None


# ---- 验收门账本 -------------------------------------------------------------
def test_failure_set_diff_gates():
    d = P.failure_set_diff(["FAILED a", "ERROR b"], ["ERROR b", "FAILED c"])
    assert d["gates_ok"] is False and d["new_failures"] == ["FAILED c"]
    d2 = P.failure_set_diff(["FAILED a", "ERROR b"], ["ERROR b", "FAILED a"])
    assert d2["gates_ok"] is True and d2["new_failures"] == []
    assert d2["unchanged_count"] == 2


def test_module_constants_contract():
    assert P.MOVE_MAX_MM == 2.0
    assert P.MAX_CANDIDATES_TOTAL == 5
    assert P.CLOSURE_MARGIN_LADDER[0] == 3.0   # 首项=pcbagent L3_MARGIN 原口径
    assert "U1" in P.ANCHOR_REFS and "J4" in P.ANCHOR_REFS
