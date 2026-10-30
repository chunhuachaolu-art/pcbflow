"""V4.2 M3 tests: per-net mirror parity, constraint validator, arms."""

import json
import os

import pytest

from pcbflow.v4exp.grid import GridWorld, canonical_json
from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.constraints import (build_negative_set, injection_spec,
                                      validate_constraints)
from pcbflow.v4_2.gt import incumbent_run
from pcbflow.v4_2.m3 import M3_SUFFIX, gain_pct, run_arm
from pcbflow.v4_2.mirror import solve_board_injected

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")


def _board(name):
    with open(os.path.join(_CMP, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _req(board):
    return {"route_order": sorted(n["net_id"] for n in board["nets"]),
            "group": "A"}


# ------------------------------------------------------------ mirror per-net

def test_per_net_empty_maps_byte_parity():
    board = _board("board-snapshot-hol-f6-01.json")
    frozen = solve_board(board, _req(board))
    mirror = solve_board_injected(board, _req(board),
                                  cost_bias_by_net={},
                                  hard_keepout_by_net={})
    assert canonical_json(mirror) == canonical_json(frozen)


def test_per_net_bias_touches_only_listed_net():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _req(board)
    world = GridWorld(board)
    baseline = solve_board(board, req)
    assert baseline["status"] == "sat"
    # bias the LAST stable-order net's incumbent path, only for that net
    last = req["route_order"][-1]
    from pcbflow.v4exp.grid import geometry_from_routes
    geo = geometry_from_routes(world, baseline["routes"], baseline["vias"])
    fcu = world.layer_index["F.Cu"]
    bias = {(fcu, ix, iy): 5.0 for (ix, iy) in geo[last].get(fcu, set())}
    assert bias
    inj = solve_board_injected(board, req, cost_bias_by_net={last: bias})
    assert inj["schema"] == "pcbflow.v4_2.solver-run-mirror/1"
    # earlier nets byte-identical; the listed net differs (or failed)
    base_by_net = {}
    for r in baseline["routes"]:
        base_by_net.setdefault(r["net_id"], []).append(r)
    inj_by_net = {}
    for r in inj["routes"]:
        inj_by_net.setdefault(r["net_id"], []).append(r)
    for nid in base_by_net:
        if nid != last:
            assert canonical_json(inj_by_net[nid]) == canonical_json(base_by_net[nid])
    assert (canonical_json(inj_by_net.get(last, []))
            != canonical_json(base_by_net[last])) or inj["status"] == "failed"


# ------------------------------------------------------------------ validator

def test_validator_negative_set_full_block():
    board = _board("board-snapshot-hol-f6-01.json")
    cases = build_negative_set(board)
    assert len(cases) >= 30
    cats = {cid.rsplit("_", 1)[0] for cid, _ in cases}
    assert len(cats) >= 6
    for cid, payload in cases:
        v = validate_constraints(board, payload)
        assert not v["ok"], cid
        assert v["violations"], cid


def test_validator_accepts_legal_and_empty():
    board = _board("board-snapshot-hol-f6-01.json")
    nid = sorted(n["net_id"] for n in board["nets"])[0]
    v = validate_constraints(board, {
        "constraints": {"corridor": [{"layer": "F.Cu",
                                      "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
                        "keepout": []}, "nets": [nid]})
    assert v["ok"] and v["constraints"]["nets"] == [nid]
    empty = validate_constraints(board, {
        "constraints": {"corridor": [], "keepout": []}, "nets": [nid]})
    assert empty["ok"]
    empty_all = validate_constraints(board, {
        "constraints": {"corridor": [], "keepout": []}, "nets": [nid]})
    assert empty_all["ok"]


def test_injection_spec_cells():
    board = _board("board-snapshot-hol-f6-01.json")
    world = GridWorld(board)
    nid = sorted(n["net_id"] for n in board["nets"])[0]
    v = validate_constraints(board, {
        "constraints": {"corridor": [{"layer": "F.Cu",
                                      "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
                        "keepout": [{"layer": "B.Cu",
                                     "rect_mm": [20.0, 5.0, 21.0, 8.0]}]},
        "nets": [nid]})
    assert v["ok"]
    spec = injection_spec(board, v["constraints"])
    fcu = world.layer_index["F.Cu"]
    bcu = world.layer_index["B.Cu"]
    assert set(spec["cost_bias_by_net"]) == {nid}
    assert all(k[0] == fcu and spec["cost_bias_by_net"][nid][k] == 5.0
               for k in spec["cost_bias_by_net"][nid])
    assert spec["hard_keepout_by_net"][nid][bcu]


# --------------------------------------------------------------------- arms

def test_run_arm_blocked_falls_back_to_baseline_bytes():
    board = _board("board-snapshot-hol-f6-01.json")
    bad = {"constraints": {"keepout": [{"layer": "F.Cu",
                                        "rect_mm": [0.0, 0.0, 40.0, 30.0]}],
                           "corridor": []}, "nets": ["n1"]}
    arm = run_arm(board, bad)
    assert arm["arm_status"] == "blocked"
    assert canonical_json(arm["treatment_result"]) == \
        canonical_json(arm["baseline_result"])


def test_run_arm_ok_safety_and_determinism():
    board = _board("board-snapshot-hol-f6-01.json")
    nid = sorted(n["net_id"] for n in board["nets"])[0]
    payload = {"constraints": {
        "corridor": [{"layer": "F.Cu", "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
        "keepout": []}, "nets": [nid]}
    a = run_arm(board, payload)
    b = run_arm(board, payload)
    assert a["arm_status"] == "ok"
    assert canonical_json(a["treatment_result"]) == \
        canonical_json(b["treatment_result"])
    if a["treatment_status"] == "sat":
        assert sum(a["treatment_result"]["metrics"]["violations"].values()) == 0
    assert gain_pct(a) is not None


def test_task_text_carries_contract_and_ningque():
    text = M3_SUFFIX
    for token in ("corridor", "keepout", "rect_mm", "nets", "2.0 mm",
                  "empty", "at most 3"):
        assert token in text
