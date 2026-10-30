# -*- coding: utf-8 -*-
"""canvas_pilot 测试装配: 仓库根入 sys.path（v5 同源导入）+ 公共夹具。"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402


def micro_board():
    """合成微板（2 网 2 分区, 无板固孔; 冒烟与 fail-closed 夹具）。

    workspace 10×8mm, pitch 0.5 → 21×17 格; N1 上行带/N2 下行带平行布局
    （单层可干净全连通）; 显式 circle pad_terminals（v5 契约: circle 的
    size_mm 恰 1 值）。调用方须自落 provenance.board_sha256（load_board
    同款落链, 见 smoke 用例）。"""
    return {
        "board_id": "micro-smoke",
        "schema_version": "v5.board.v1",
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "nets": [
            {"net_id": "N1", "partitions": ["PT1"]},
            {"net_id": "N2", "partitions": ["PT2"]},
        ],
        "partitions": [
            {"partition_id": "PT1", "ptype": "MISC", "speed_class": "unknown",
             "layer_policy": "any",
             "width_prior": {"w_max": 0.4, "w_min": 0.2, "w_typ": 0.3},
             "geometry": {
                 "endpoints": [[0.5, 0.5], [9.5, 0.5]],
                 "pad_terminals": [
                     {"endpoint": 0, "layers": "all", "shape": "circle",
                      "size_mm": [1.0]},
                     {"endpoint": 1, "layers": "all", "shape": "circle",
                      "size_mm": [1.0]}]}},
            {"partition_id": "PT2", "ptype": "MISC", "speed_class": "unknown",
             "layer_policy": "any",
             "width_prior": {"w_max": 0.4, "w_min": 0.2, "w_typ": 0.3},
             "geometry": {
                 "endpoints": [[0.5, 7.5], [9.5, 7.5]],
                 "pad_terminals": [
                     {"endpoint": 0, "layers": "all", "shape": "circle",
                      "size_mm": [1.0]},
                     {"endpoint": 1, "layers": "all", "shape": "circle",
                      "size_mm": [1.0]}]}},
        ],
        "holes": [],
        "zones": [],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0, "y_max": 8.0},
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "available": True,
             "preferred_direction": "any"},
            {"id": "B.Cu", "kind": "signal", "available": True,
             "preferred_direction": "any"},
        ],
    }


@pytest.fixture
def micro_state():
    from canvas_pilot import lattice as _lat
    from canvas_pilot import state as _state
    board = micro_board()
    lat = _lat.Lattice.from_board(board, 0.5)
    anchors = _lat.anchor_map(board, lat)
    st = _state.CanvasState(board, "<memory>", "0" * 64, lat, anchors)
    st.recompute_connectivity()
    return st


BADGELEDS = os.path.join(ROOT, "out", "v5-p5", "boards",
                         "badgeleds-do-electronics", "board.json")


def load_badgeleds():
    raw = json.load(open(BADGELEDS, "rb"))
    return raw["board"] if "board" in raw else raw


@pytest.fixture(scope="module")
def badgeleds_board():
    return load_badgeleds()
