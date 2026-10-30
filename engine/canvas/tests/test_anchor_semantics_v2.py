# -*- coding: utf-8 -*-
"""V6-ANCHOR-R1 新增探针测试（AJ-4: 修复后须≥基线且新增探针测试）。

口径 v2（anchor semantics v2, 真端点绑定）断言面:
- 首末点绑定: 物理铜以真实端点 mm 起/终, 锚格 mm 不进折线;
- body 仍=格点 mm; L 形先 x 后 y;
- 双端绑定无 body / 单点退化 / 非锚端 三分支;
- facts 口径版本=canvas-state/0.3.0+anchor_semantics=v2;
- 合成贴门翻案一例（端点位移使旧口径拒收、真几何过阈→v2 接受）。
"""
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from canvas import instantiate as cinst          # noqa: E402
from canvas import state as cst                  # noqa: E402
from canvas import validate as cval              # noqa: E402
from v5 import board as v5board                  # noqa: E402
from v5 import drc as vdrc                       # noqa: E402


def _board(endpoints_t, pad_t=None, endpoints_f=None, pad_f=None,
           board_id="anchor-v2-test"):
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 16.0,
                      "y_max": 12.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PT", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": endpoints_t,
                          "pad_terminals": pad_t or []}},
        ],
        "nets": [{"net_id": "NET-T", "partitions": ["PT"]}],
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
        "provenance": {"source_type": "synthetic", "source_uri": board_id,
                       "source_sha256": "0" * 64, "adapter": "anchor-v2-test",
                       "board_sha256": None},
    }
    if endpoints_f is not None:
        board["partitions"].append(
            {"partition_id": "PF", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": endpoints_f,
                          "pad_terminals": pad_f or []}})
        board["nets"].append({"net_id": "NET-F", "partitions": ["PF"]})
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)


def _state(board):
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(board, "<anchor-v2-test>",
                         board["provenance"]["board_sha256"], lat,
                         cst.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def _offgrid_state():
    """PT e0=(3.23,3.19)→锚(6,6)（Δ=(0.23,0.19) 非零位移）; e1=(12,9) 在格。"""
    return _state(_board([[3.23, 3.19], [12.0, 9.0]]))


def _seg(st, grid, pid="PT"):
    return {"shape_id": "t:seg", "net_id": "NET-T", "partition_id": pid,
            "layer": "F.Cu", "grid": [list(g) for g in grid],
            "width_class": "min"}


def test_head_binding_true_endpoint_not_anchor_grid():
    st = _offgrid_state()
    pts, stub = cinst.segment_mm(st, _seg(st, [(6, 6), (6, 10), (12, 10)]))
    lat_mm = st.lattice.to_mm(6, 6)
    assert pts[0] == (3.23, 3.19)
    assert lat_mm not in pts                     # 锚格 mm 不进物理铜
    assert pts[-1] == st.lattice.to_mm(12, 10)
    assert stub["head"] == (0, 2)                # real→corner→mm(6,10)
    assert stub["tail"] is None                  # 尾端非锚


def test_head_binding_l_shape_x_first():
    st = _offgrid_state()
    pts, _ = cinst.segment_mm(st, _seg(st, [(6, 6), (6, 7)]))
    # 先 x 后 y: real(3.23,3.19)→(3.0,3.19)→(3.0,3.5)
    assert pts == [(3.23, 3.19), (3.0, 3.19), (3.0, 3.5)]


def test_both_ends_bound_body_stays_grid_mm():
    st = _offgrid_state()
    pts, stub = cinst.segment_mm(st, _seg(st, [(6, 6), (8, 6), (24, 18)]))
    assert pts == [(3.23, 3.19), (4.0, 3.19), (4.0, 3.0),
                   (12.0, 3.0), (12.0, 9.0)]
    assert stub["head"] == (0, 2)                # real→corner→首 body 点
    assert stub["tail"] == (2, 4)                # 末 body 点→corner→real2


def test_no_interior_two_anchor_direct():
    st = _offgrid_state()
    pts, stub = cinst.segment_mm(st, _seg(st, [(6, 6), (24, 18)]))
    assert pts == [(3.23, 3.19), (12.0, 3.19), (12.0, 9.0)]
    assert stub["head"] == (0, 2)
    assert stub["tail"] == (0, 2)                # 双端绑定无 body: 直连两端点


def test_unbound_start_plain_grid():
    st = _offgrid_state()
    pts, stub = cinst.segment_mm(st, _seg(st, [(7, 6), (9, 6)]))
    assert pts[0] == st.lattice.to_mm(7, 6)
    assert stub["head"] is None and stub["tail"] is None


def test_facts_version_v2():
    st = _offgrid_state()
    facts = st.facts()
    assert facts["canvas_version"] == "canvas-state/0.3.0"
    assert facts["anchor_semantics"] == "v2"


def test_threshold_band_flip_accepted():
    """贴门翻案: 对端焊盘真几何 gap≥阈而锚格几何 gap<阈 → v2 判接受。

    对端 PF pad 圆 r0.2 @(2.80,2.50); 候选 NET-T 头绑定腿真几何
    (3.23,3.19)→(3.0,3.19)→(3.0,3.5): 真几何 gap≈0.518>0.5 过阈。"""
    board = _board([[3.23, 3.19], [12.0, 9.0]],
                   pad_t=[{"endpoint": 1, "shape": "rect",
                           "size_mm": [0.2, 0.2], "layers": "all"}],
                   endpoints_f=[[2.80, 2.50], [14.5, 2.0]],
                   pad_f=[{"endpoint": 0, "shape": "circle",
                           "size_mm": [0.4], "layers": "all"},
                          {"endpoint": 1, "shape": "rect",
                           "size_mm": [0.4, 0.4], "layers": "all"}])
    st = _state(board)
    action = {"action": "route", "net_id": "NET-T", "layer": "F.Cu",
              "waypoints": [[6, 6], [6, 18], [24, 18]]}
    ok, code, _detail = cval.validate_edit(st, action)
    assert ok, "真几何过阈段被拒: code=%s" % code
    fake = {"shape_id": "t:seg", "net_id": "NET-T", "partition_id": "PT",
            "layer": "F.Cu",
            "grid": [list(p) for p in
                     cinst.expand_waypoints(action["waypoints"])],
            "width_class": "min"}
    cu = cinst.seg_copper(st, fake)
    pad = [c for c in cval._scene(st)
           if c.cid == "pad:PF:0" and c.layer == "F.Cu"][0]
    gap = vdrc._actual_gap(cu, pad)
    assert gap >= 0.5 - 1e-9, "引擎铜 gap=%s < 阈（真几何未生效）" % gap
