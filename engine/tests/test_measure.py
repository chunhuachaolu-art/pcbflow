# -*- coding: utf-8 -*-
"""measure 成本核算：绕行/逆向/过孔罚分与确定性。"""
from v5.measure import (DEFAULT_COST_MODEL, measure_assignment, measure_assignment_bytes,
                        polyline_length, route_cost, wrong_direction_length)

DIRS = {"F.Cu": "h", "In1.Cu": "v", "B.Cu": "any", "In2.Cu": "any"}


def test_polyline_length_manhattan_equivalent():
    assert polyline_length([[0, 0], [3, 0], [3, 4]]) == 7.0


def test_wrong_direction_h_layer_counts_vertical():
    assert wrong_direction_length([[0, 0], [0, 5], [2, 5]], "h") == 5.0


def test_wrong_direction_v_layer_counts_horizontal():
    assert wrong_direction_length([[0, 0], [0, 5], [2, 5]], "v") == 2.0


def test_wrong_direction_any_layer_zero():
    assert wrong_direction_length([[0, 0], [0, 5], [2, 5]], "any") == 0.0


def test_straight_route_zero_cost():
    route = {"net_id": "N", "layer": "B.Cu", "polyline": [[0, 0], [0, 10]]}
    assert route_cost(route, DIRS)["cost"] == 0.0


def test_detour_cost_rate():
    route = {"net_id": "N", "layer": "B.Cu", "polyline": [[0, 0], [4, 0], [4, 10], [0, 10]]}
    r = route_cost(route, DIRS)
    assert r["excess_mm"] == 8.0
    assert r["cost"] == 4.0  # 0.5×8


def test_via_and_return_costs():
    route = {"net_id": "N", "layer": "B.Cu", "transition_vias": 2,
             "polyline": [[0, 0], [0, 10]]}
    assert route_cost(route, DIRS)["cost"] == 10.0  # 2×4 + 2×1


def test_default_cost_model_v2():
    assert DEFAULT_COST_MODEL == {"detour_rate": 0.5, "direction_rate": 0.2,
                                  "via_cost": 4.0, "return_cost": 1.0}


def test_measure_assignment_total_and_versions():
    routes = [
        {"net_id": "A", "layer": "F.Cu", "polyline": [[0, 0], [0, 10]]},
        {"net_id": "B", "layer": "B.Cu", "transition_vias": 1, "polyline": [[0, 0], [0, 10]]},
    ]
    m = measure_assignment(routes, DIRS)
    assert m["total_cost"] == 2.0 + 5.0  # A: 0.2×10; B: 4+1
    assert m["measurer_version"].startswith("v5.measure/")
    assert m["drc_version"].startswith("v5.drc/")


def test_measure_bytes_double_run_equal():
    routes = [{"net_id": "A", "layer": "F.Cu", "polyline": [[0, 0], [3.7, 0], [3.7, 9.2]]}]
    assert measure_assignment_bytes(routes, DIRS) == measure_assignment_bytes(routes, DIRS)


def test_measure_is_pure_no_clock_no_host_paths():
    import json
    routes = [{"net_id": "A", "layer": "B.Cu", "polyline": [[0, 0], [1, 1]]}]
    text = measure_assignment_bytes(routes, DIRS).decode()
    obj = json.loads(text)
    assert not any(k in text.lower() for k in ("time", "host", "user", "tmp"))


def test_custom_cost_model_override():
    route = {"net_id": "N", "layer": "B.Cu", "polyline": [[0, 0], [4, 0], [4, 10], [0, 10]]}
    r = route_cost(route, DIRS, cost_model={"detour_rate": 1.0})
    assert r["cost"] == 8.0
