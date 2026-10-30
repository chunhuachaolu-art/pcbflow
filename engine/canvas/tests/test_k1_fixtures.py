# -*- coding: utf-8 -*-
"""Lane-K1 测试共享夹具（test_k1_* 族，不入 tests/ 根）。

- 真板=badgeleds-do-electronics 只读加载（json.load 取 ["board"] 体 →
  v5.board.load_board 全校验——合同 §0 称 load_board_file 为 wrap 件，实码
  不解包（顶层 schema 校验即败），故按 v1 先例（canvas_pilot.loop.load_board）
  取体后走 v5.board.load_board；详见 lane-k1 REPORT 偏差披露）。
- 合成微板=schema 完整最小合法 board dict（v5.board.load_board 可过校验与
  哈希链），几何手工布点使各违例码可确定触发。
"""
import copy
import json
import os

from v5 import board as v5board

from canvas import state as cst

REAL_BOARD_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "out", "v5-p5", "boards-pre-r1", "badgeleds-do-electronics", "board.json"))

_REAL_CACHE = {}


def real_board():
    """(board, board_path, board_sha256)——真板只读，全测试共享缓存。"""
    if not _REAL_CACHE:
        with open(REAL_BOARD_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        board = v5board.load_board(raw["board"])   # schema+跨字段+哈希链
        _REAL_CACHE["board"] = board
        _REAL_CACHE["sha"] = board["provenance"]["board_sha256"]
    return _REAL_CACHE["board"], REAL_BOARD_PATH, _REAL_CACHE["sha"]


def real_state():
    board, path, sha = real_board()
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(board, path, sha, lat, cst.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def _synth_board(via_model=None):
    """合成微板: workspace (0,0)-(14,10)，pitch 0.5 → 格点域 28×20。

    分区/网（端点 mm，格点=mm/0.5）:
    - NET-A / PA:   (2,2)-(10,2)   → 锚 (4,4)-(20,4)
    - NET-B / PB:   (2,8)-(10,8)   → 锚 (4,16)-(20,16)
    - NET-C / PC1:  (11,5)-(13,5)  → 锚 (22,10)-(26,10)
          / PC2:  (1,5)-(3,5)    → 锚 (2,10)-(6,10)   （双分区网）
    板固孔 1 枚: (7,5) drill 0.8 → 禁布: track <0.8 / via(缺省 r0.3) <0.95。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "synth-k1",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 14.0, "y_max": 10.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PA", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 2.0], [10.0, 2.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "PB", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 8.0], [10.0, 8.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "PC1", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[11.0, 5.0], [13.0, 5.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "PC2", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[1.0, 5.0], [3.0, 5.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
        ],
        "nets": [
            {"net_id": "NET-A", "partitions": ["PA"]},
            {"net_id": "NET-B", "partitions": ["PB"]},
            {"net_id": "NET-C", "partitions": ["PC1", "PC2"]},
        ],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "holes": [{"drill_mm": 0.8, "plated": True,
                   "pos_mm": [7.0, 5.0], "shape": "circle"}],
        "principle_registry": [],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "canvas-k1-fixture",
            "source_sha256": "0" * 64,
            "adapter": "canvas-k1",
            "board_sha256": None,
        },
    }
    if via_model is not None:
        board["via_model"] = via_model
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)   # fail-closed 自证（schema+哈希链）


def synth_state(via_model=None):
    board = _synth_board(via_model=via_model)
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(board, "<synth-k1>",
                         board["provenance"]["board_sha256"], lat,
                         cst.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def batch(actions, round_no=1):
    """动作列表 → 批文本（末尾自动补 submit——已含 submit 则不重复）。"""
    acts = list(actions)
    if not any(isinstance(a, dict) and a.get("action") == "submit"
               for a in acts):
        acts.append({"action": "submit"})
    return json.dumps({"round": round_no, "actions": acts})


def run_batch(st, actions, round_no=1):
    """parse+apply 一步跑（语义层结果列表）。"""
    from canvas import protocol as cpr
    return cpr.apply_batch(st, cpr.parse_batch(batch(actions, round_no),
                                               round_no), round_no)


def apply_ok(st, actions, round_no=1):
    """跑批并断言全部 accepted（submit 除外无 code）。"""
    results = run_batch(st, actions, round_no=round_no)
    for r in results:
        assert r["accepted"], "夹具批被拒: %r" % (r,)
    return results
