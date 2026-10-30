# -*- coding: utf-8 -*-
"""V8-PILOT-060 D-5 随改断言: V_CLEARANCE detail @cand 最近点对坐标。

canvas/validate._new_violations 的 R5 新增违例 detail 追加
`` @cand=(x,y) vs (x2,y2)``（候选铜 vs 对位铜，mm round 4 位）——
**advisory 定位辅助，裁决仍以 gap 值为准**（gap=v5.drc.check_clearance
单源，本套断言同时核 gap 数值与坐标几何一致性）。
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from canvas import validate as V             # noqa: E402
from canvas.state import Lattice, CanvasState, anchor_map   # noqa: E402
from v5 import board as v5board              # noqa: E402
from v5 import drc                           # noqa: E402


def _board():
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "v8-d5-detail",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 16.0, "y_max": 12.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PT", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[3.23, 3.19], [12.0, 9.0]]}},
            {"partition_id": "PF", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[3.5, 6.0], [14.5, 2.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "circle",
                               "size_mm": [0.4], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [0.4, 0.4], "layers": "all"}]}},
        ],
        "nets": [
            {"net_id": "NET-T", "partitions": ["PT"]},
            {"net_id": "NET-F", "partitions": ["PF"]},
        ],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "holes": [],
        "principle_registry": [],
        "provenance": {
            "source_type": "synthetic", "source_uri": "v8-pilot060-d5",
            "source_sha256": "0" * 64, "adapter": "v8-pilot060",
            "board_sha256": None},
    }
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)


def _st(board):
    lat = Lattice.from_board(board)
    st = CanvasState(board, "<v8-d5>", board["provenance"]["board_sha256"],
                     lat, anchor_map(board, lat))
    st.recompute_connectivity()
    return st


ROUTE = {"action": "route", "net_id": "NET-T", "layer": "F.Cu",
         "waypoints": [[6, 6], [6, 18], [24, 18]]}
# PT 端点 (3.23,3.19)→锚(6,6)、(12,9)→锚(24,18); PF#0 圆 pad 心
# (3.5,6.0) r=0.2 → 候选竖线 x=3.0 的裸距 0.5−0.2=0.3 < R5 ⇒ 违例。


def test_detail_cand_coords_pad_polyline():
    st = _st(_board())
    ok, code, detail = V.validate_edit(st, ROUTE)
    assert not ok and code == "V_CLEARANCE"
    assert detail == ("pad:PF:0|cand:seg gap=0.3 "
                      "@cand=(3.0,6.0) vs (3.3,6.0)")
    m = re.search(r"@cand=\((-?\d+\.\d+),(-?\d+\.\d+)\) vs "
                  r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", detail)
    (x1, y1), (x2, y2) = (float(m.group(1)), float(m.group(2))), \
                         (float(m.group(3)), float(m.group(4)))
    # advisory 坐标几何一致性: 点对距 == gap（round 4 位容差）
    assert abs(math.hypot(x1 - x2, y1 - y2) - 0.3) <= 5e-4
    # cand 点在候选折线上（x=3.0 竖线段上）
    assert abs(x1 - 3.0) <= 5e-4
    # 对位点在 pad 圆缘（心 (3.5,6.0) r=0.2）
    assert abs(math.hypot(x2 - 3.5, y2 - 6.0) - 0.2) <= 5e-4


def test_gap_value_unchanged_vs_drc():
    """裁决单源不变: detail 前段 gap 与 v5.drc._actual_gap 逐位一致。"""
    from canvas import instantiate as inst
    st = _st(_board())
    ok, code, detail = V.validate_edit(st, ROUTE)
    gap = float(re.search(r"gap=([-0-9.eE+]+)", detail).group(1))
    fake = {"shape_id": "cand:seg", "net_id": "NET-T", "partition_id": "PT",
            "layer": "F.Cu",
            "grid": [list(p) for p in
                     inst.expand_waypoints(ROUTE["waypoints"])],
            "width_class": V._effective_width_class(st, "NET-T")}
    cand = inst.seg_copper(st, fake)
    pad = [c for c in V._scene(st)
           if c.cid == "pad:PF:0" and c.layer == "F.Cu"][0]
    assert gap == round(drc._actual_gap(cand, pad), 10)


def test_detail_cand_coords_crossing():
    """交叉零距: 最近点对= 交点对（坐标重合、gap=0.0）。"""
    board = _board()
    # PF#0 pad 挪到候选竖线正上 (3.0,6.0) r=0.2 → 圆心在折线上，gap=0
    for p in board["partitions"]:
        if p["partition_id"] == "PF":
            p["geometry"]["endpoints"][0] = [3.0, 6.0]
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(
        board)
    v5board.load_board(board)
    st = _st(board)
    ok, code, detail = V.validate_edit(st, ROUTE)
    assert not ok and code == "V_CLEARANCE"
    m = re.search(r"@cand=\((-?\d+\.\d+),(-?\d+\.\d+)\) vs "
                  r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", detail)
    assert m, detail
    assert m.group(1) == m.group(3) and m.group(2) == m.group(4)


def test_nearest_pair_geometry_matrix():
    """_nearest_pair 全几何对（中心线/圆心口径）数值面。"""
    a = drc.Copper("N1", "a", "F.Cu",
                   polyline=[(0.0, 0.0), (0.0, 10.0)], half_width=0.15)
    b = drc.Copper("N2", "b", "F.Cu",
                   polyline=[(2.0, 5.0), (4.0, 5.0)], half_width=0.15)
    (pa, pb) = V._nearest_pair(a, b)
    assert pa == (0.0, 5.0) and pb == (2.0, 5.0)   # 首点在 ca
    pad = drc.Copper("N2", "p", "F.Cu", pad=((5.0, 0.0), 0.2))
    (q1, q2) = V._nearest_pair(a, pad)
    assert q1 == (0.0, 0.0) and q2 == (4.8, 0.0)
    band = drc.Copper("N2", "bd", "F.Cu", band=(1.0, -1.0, 3.0, 1.0))
    (q1, q2) = V._nearest_pair(a, band)
    assert abs(q1[0] - 0.0) < 1e-9 and abs(q2[0] - 1.0) < 1e-9
    p1 = drc.Copper("N1", "p1", "F.Cu", pad=((0.0, 0.0), 0.2))
    p2 = drc.Copper("N2", "p2", "F.Cu", pad=((1.0, 0.0), 0.2))
    assert V._nearest_pair(p1, p2) == ((0.2, 0.0), (0.8, 0.0))
    b1 = drc.Copper("N1", "b1", "F.Cu", band=(0.0, 0.0, 1.0, 1.0))
    b2 = drc.Copper("N2", "b2", "F.Cu", band=(3.0, 0.0, 4.0, 1.0))
    assert V._nearest_pair(b1, b2) == ((1.0, 0.5), (3.0, 0.5))
    # r4: -0.0 归一
    assert V._r4(-1e-9) == 0.0
