"""tests/test_v4_1_e3_solver2 -- E3 求解适配层测试（flat 字节等价 + 分层行为）。

依据：任务书 §3 E3；prereg-e3.json → g32_regression_112.byte_equality_check
（solver2(flat) 与 v4exp.router 逐字节一致=适配层正确性证据）。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow.v4exp import router
from pcbflow.v4exp.grid import GridWorld
from pcbflow.v4_1 import solver2
from pcbflow.v4_1.costmodel import ViaCostModel

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")

_SMOKE_SIDS = ["dev-f1-01", "dev-f2-03", "dev-f4-01", "cal-f5-13",
               "hol-f6-02", "hol-f8-03"]


def _board(sid):
    with open(os.path.join(_CMP, "board-snapshot-%s.json" % sid),
              encoding="utf-8") as f:
        return json.load(f)


def _order(board):
    return sorted(str(n["net_id"]) for n in board["nets"])


@pytest.mark.parametrize("sid", _SMOKE_SIDS)
def test_flat_mode_byte_equal_v4exp(sid):
    """flat 成本下 solver2 与 v4exp.router 输出逐字节一致（含全部冻结 metrics 键）。"""
    board = _board(sid)
    order = _order(board)
    base = router.solve_board(board, {"route_order": order, "group": "A0"})
    flat = solver2.solve_board2(board, {"route_order": order, "group": "A0"})
    assert flat["routes"] == base["routes"]
    assert flat["vias"] == base["vias"]
    assert flat["status"] == base["status"]
    for k, v in base["metrics"].items():
        assert flat["metrics"][k] == v
    assert flat["schema"] == "pcbflow.v4exp.solver-run/1"


@pytest.mark.parametrize("sid", _SMOKE_SIDS)
def test_layered_default_degenerate_on_two_layer(sid):
    """2 层栈上分层默认与 flat（=v1）逐字节一致（贯通唯一跨度=8.0 锚）。"""
    board = _board(sid)
    order = _order(board)
    world = GridWorld(board)
    flat = solver2.solve_board2(board, {"route_order": order, "group": "T"})
    layered = solver2.solve_board2(
        board, {"route_order": order, "group": "T"},
        cost_model=ViaCostModel(list(world.layers)))
    assert layered["routes"] == flat["routes"]
    assert layered["vias"] == flat["vias"]
    assert layered["metrics"]["objective"] == flat["metrics"]["objective"]


def test_cost_model_stack_mismatch_fail_closed():
    board = _board("dev-f1-01")
    order = _order(board)
    bad = ViaCostModel(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
    with pytest.raises(solver2.Solver2Error):
        solver2.solve_board2(board, {"route_order": order, "group": "T"},
                             cost_model=bad)


def test_run_dict_contract():
    board = _board("dev-f1-01")
    order = _order(board)
    run = solver2.solve_board2(board, {"route_order": order, "group": "X"})
    assert run["solver2_version"] == solver2.SOLVER2_VERSION
    assert run["via_cost_model"]["flat"] is True
    assert "objective_layered" in run["metrics"]
    assert run["metrics"]["objective_layered"] == run["metrics"]["objective"]
    # 确定性：同输入两次运行逐字节一致
    run2 = solver2.solve_board2(board, {"route_order": order, "group": "X"})
    assert json.dumps(run, sort_keys=True) == json.dumps(run2, sort_keys=True)


def test_route_order_contract_inherited():
    board = _board("dev-f1-01")
    with pytest.raises(Exception):
        solver2.solve_board2(board, {"route_order": ["n1"], "group": "X"})


def test_span_aware_metrics_equals_cmp_metrics_on_two_layer():
    """2 层域上 span-aware 度量与 v4exp 冻结独立 checker cmp_metrics 同判。"""
    from pcbflow.v4exp.cmp_patch import cmp_metrics
    board = _board("dev-f4-01")
    order = _order(board)
    run = solver2.solve_board2(board, {"route_order": order, "group": "A0"})
    world = GridWorld(board)
    mine = solver2.metrics_span_aware(world, run["routes"], run["vias"])
    ref = cmp_metrics(world, run["routes"], run["vias"])
    for k in ("all_connected", "unconnected", "shorts", "via_count",
              "bend_count", "total_length_mm", "objective"):
        assert mine[k] == ref[k], k


def test_multilayer_layered_solve_runs_and_reports():
    """f9 多层域：分层默认臂可解且 objective_layered 诊断键存在。"""
    from pcbflow.v4_1.mlchain import mlboard_to_v4exp_board
    from pcbflow.v4_1.mlfamily import generate_ml_scenario
    board = mlboard_to_v4exp_board(generate_ml_scenario("dev-f9-01"))
    order = _order(board)
    world = GridWorld(board)
    run = solver2.solve_board2(
        board, {"route_order": order, "group": "T"},
        cost_model=ViaCostModel(list(world.layers)))
    assert run["status"] == "sat"
    assert run["via_cost_model"]["flat"] is False
    assert "objective_layered" in run["metrics"]
    # span-aware 度量下零违例（self-consistent 求解输出）
    m = solver2.metrics_span_aware(world, run["routes"], run["vias"])
    assert sum(m["violations"].values()) == 0
    assert m["all_connected"] is True
