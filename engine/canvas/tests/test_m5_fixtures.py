# -*- coding: utf-8 -*-
"""Lane-M5 测试共享夹具（test_m5_* 族，不入 tests/ 根）。

- 合成长度组夹具板 synth-m5: board.v1 **无长度组字段**（审计结论见
  canvas.tuning docstring）——长度组人口用本夹具板 + budget 注入目标长度表。
- 几何布点使 R6 避撞各面可确定触发（zones 逐坐标对齐 tuning 折返/侧移的
  参数化几何，见 _m5_board docstring 的档位推演）。
- 真板路径 = badgeleds 只读复用 canvas.tests.test_k1_fixtures.real_state
  （no_length_groups 路径，不产 tuning 动作）。
"""
from v5 import board as v5board

from canvas import state as cst
from canvas.tests.test_k1_fixtures import run_batch


def _m5_board(y_max=12.0, zones=True):
    """synth-m5 板: workspace (0,0)-(20,y_max)，pitch 0.5。

    分区/网（端点 mm，格点=mm/0.5）:
    - NET-T1 / PT1: (2,2)-(10,2)  → 锚 (4,4)-(20,4)    基线 8.0mm（y=2）
    - NET-T2 / PT2: (2,9)-(10,9)  → 锚 (4,18)-(20,18)  基线 8.0mm（y=9）

    keepout zones（layers="signal"; v5.drc.check_keepout 用外接矩形、
    接触即违例 rect_rect_gap ≤ 0——zone 边界恰贴 tuning 几何触点）:
    - Z1（T1 下侧）y∈[2.5,4.5]: 拦 NET-T1 accordion（折返 y=2+amp，
      amp≥0.5 触 2.5）与 detour +（首腿 bump rect y∈[2,2.5] 触 2.5）；
      detour −（bump y∈[1.5,2]）净空 → LG-OPEN 应选 detour −0.5。
    - Z2（T2 下侧）y∈[9.5,11.5] + Z3（T2 上侧）y∈[6.5,8.5]: 拦 NET-T2
      全部合法档（accordion +u 向 y=9+amp 触 Z2; detour ±0.5 bump 触
      Z2/Z3）→ LG-BOXED 无合法档（全拒收面）。
    pad_terminals 0.6×0.6（端点带 y∈[±0.3]）: 对 Z1/Z2/Z3 各留 0.2mm
    净空——板固有 pad 不进 zone（validate_full 对调参后态全净，违例只归
    调参几何、归责面纯净）。
    y_max=11.4 且 zones=False 的变体 = 板边禁布带测试（NET-T2 accordion
    amp 2.5 → y=11.5 > 11.4−0.2 内矩形界 → edge_clearance）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "synth-m5",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0,
                      "y_max": float(y_max)},
        "zones": ([
            {"zone_id": "Z1", "kind": "keepout", "layers": "signal",
             "rect": {"x_min": 1.0, "y_min": 2.5, "x_max": 11.0, "y_max": 4.5}},
            {"zone_id": "Z2", "kind": "keepout", "layers": "signal",
             "rect": {"x_min": 1.0, "y_min": 9.5, "x_max": 11.0, "y_max": 11.5}},
            {"zone_id": "Z3", "kind": "keepout", "layers": "signal",
             "rect": {"x_min": 1.0, "y_min": 6.5, "x_max": 11.0, "y_max": 8.5}},
        ] if zones else []),
        "partitions": [
            {"partition_id": "PT1", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 2.0], [10.0, 2.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [0.6, 0.6], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [0.6, 0.6], "layers": "all"}]}},
            {"partition_id": "PT2", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 9.0], [10.0, 9.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [0.6, 0.6], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [0.6, 0.6], "layers": "all"}]}},
        ],
        "nets": [
            {"net_id": "NET-T1", "partitions": ["PT1"]},
            {"net_id": "NET-T2", "partitions": ["PT2"]},
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
            "source_type": "synthetic",
            "source_uri": "canvas-m5-fixture",
            "source_sha256": "0" * 64,
            "adapter": "canvas-m5",
            "board_sha256": None,
        },
    }
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)   # fail-closed 自证（schema+哈希链）


def m5_state(y_max=12.0, zones=True):
    """已布线态: 两网经 protocol route 动作落直线段（经缝建态，非私拼 seg）。

    NET-T1 waypoints (4,4)→(20,4)；NET-T2 (4,18)→(20,18)（各 8.0mm 基线，
    grid 单位步展开——detour 最长腿并列取首腿，bump 恒在 x∈[2,2.5]）。"""
    board = _m5_board(y_max=y_max, zones=zones)
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(board, "<synth-m5>",
                         board["provenance"]["board_sha256"], lat,
                         cst.anchor_map(board, lat))
    st.recompute_connectivity()
    run_batch(st, [
        {"action": "route", "net_id": "NET-T1", "layer": "F.Cu",
         "waypoints": [[4, 4], [20, 4]]},
        {"action": "route", "net_id": "NET-T2", "layer": "F.Cu",
         "waypoints": [[4, 18], [20, 18]]},
    ])
    assert all(st.connectivity.values()), "夹具布线未连通: %r" % (st.connectivity,)
    return st


#: M5 长度组 budget（目标长度表注入——board.v1 无长度组字段的替代人口）。
M5_BUDGET = {
    "length_groups": {
        "LG-OPEN": {"nets": ["NET-T1"], "target_mm": 9.0, "tol_mm": 0.3},
        "LG-BOXED": {"nets": ["NET-T2"], "target_mm": 8.9, "tol_mm": 0.3},
    }
}
