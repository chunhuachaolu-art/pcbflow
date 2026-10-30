"""V4.2 M2 engine tests: greedy arms, priorities, safety, determinism."""

import json
import os

import pytest

from pcbflow.v4exp.grid import canonical_json
from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.family import generate_f12_board
from pcbflow.v4_2.gt import incumbent_run
from pcbflow.v4_2.m2 import (BUDGET_K, baseline_priority, flag_priority,
                             greedy_arm, net_contribution, run_pair)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")


def _board(name):
    with open(os.path.join(_CMP, name), "r", encoding="utf-8") as f:
        return json.load(f)


def test_net_contribution_matches_metrics():
    """Contribution sum must reconcile with the solver objective."""
    board = _board("board-snapshot-hol-f6-01.json")
    run = incumbent_run(board)
    assert run["status"] == "sat"
    contrib = net_contribution(run)
    m = run["metrics"]
    total = round(sum(contrib.values()), 4)
    assert abs(total - (m["total_length_mm"] + m["via_count"] * 8.0
                        + m["bend_count"] * 0.5)) < 0.05


def test_baseline_priority_deterministic_worst_first():
    board = _board("board-snapshot-hol-f6-01.json")
    run = incumbent_run(board)
    p = baseline_priority(run)
    contrib = net_contribution(run)
    assert p == sorted(p, key=lambda nid: (-contrib[nid], nid))
    assert set(p) == {n["net_id"] for n in board["nets"]}


def test_greedy_arm_improves_monotonically_within_budget():
    board = generate_f12_board("hol-f12-01").to_obj()
    inc = incumbent_run(board)
    assert inc["status"] == "sat"
    res = greedy_arm(board, inc, baseline_priority)
    assert res["improvement"] >= 0.0
    assert res["evaluations"] <= BUDGET_K
    if res["applied"]:
        assert (inc["metrics"]["objective"] - res["improvement"]
                == res["final"]["metrics"]["objective"])
        # monotone: every applied net strictly improved the objective
        assert res["improvement"] > 0
    # G-M2a safety
    assert sum(res["final"]["metrics"]["violations"].values()) == 0
    assert res["final"]["metrics"]["all_connected"] is True


def test_greedy_determinism_double_run():
    board = _board("board-snapshot-hol-f8-01.json")
    inc = incumbent_run(board)
    a = greedy_arm(board, inc, baseline_priority)
    b = greedy_arm(board, inc, baseline_priority)
    assert canonical_json(a) == canonical_json(b)


def test_treatment_respects_flags_only_no_fallback():
    board = _board("board-snapshot-hol-f8-02.json")
    inc = incumbent_run(board)
    # empty flags: incumbent returned unchanged, budget unspent
    empty = greedy_arm(board, inc, lambda _c: [])
    assert empty["improvement"] == 0.0
    assert empty["evaluations"] == 0
    assert empty["final"]["route_manifest_sha256_at_run"] == \
        inc["route_manifest_sha256_at_run"]
    # a synthetic flag on some net: arm may only move flagged nets
    nid = sorted(n["net_id"] for n in board["nets"])[0]
    res = greedy_arm(board, inc, lambda _c, _n=nid: [_n])
    assert res["applied"] in ([], [nid])


def test_flag_priority_maps_routes_to_nets_in_flag_order():
    board = _board("board-snapshot-hol-f6-01.json")
    flags = [
        {"route_id": "n3-S01", "verdict": "no_flag", "reason_code": "uncertain",
         "evidence": "x"},
        {"route_id": "n2-S02", "verdict": "flag_bad", "reason_code": "detour_excess",
         "evidence": "x"},
        {"route_id": "n5-S01", "verdict": "flag_bad", "reason_code": "clearance_risk",
         "evidence": "x"},
        {"route_id": "n2-S02", "verdict": "flag_bad", "reason_code": "detour_excess",
         "evidence": "x"},
    ]
    assert flag_priority(flags, board) == ["n2", "n5"]
    assert flag_priority([], board) == []


def test_run_pair_shape_and_replay_field():
    board = _board("board-snapshot-hol-f8-01.json")
    inc = incumbent_run(board)
    # synthetic flags: flag the worst contributor for a real test
    worst = baseline_priority(inc)[0]
    flags = [{"route_id": worst + "-S01", "verdict": "flag_bad",
              "reason_code": "detour_excess", "evidence": "x"}]
    res = run_pair(board, flags)
    assert res["status"] == "ok"
    assert res["flagged_nets"] == [worst]
    assert res["baseline"]["evaluations"] <= BUDGET_K
    assert res["treatment"]["evaluations"] <= BUDGET_K
    # replay determinism over identical recorded flags
    again = run_pair(board, flags)
    assert res["canonical_pair"] == again["canonical_pair"]
