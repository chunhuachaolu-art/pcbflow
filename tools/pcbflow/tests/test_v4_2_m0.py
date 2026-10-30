"""V4.2 M0 probe tests: mirror byte-parity (P0-a) + subnet leg parity (P0-b).

Anchors (fail-closed): the 12 reuse scenario snapshots under
out/v4-comparative-experiment/ (f6/f8 holdout read-only subset + f1 simple
family subset, taskbook §3 M0 baseline).  Missing anchor files fail the
tests -- they are never silently skipped.
"""

import json
import os

import pytest

from pcbflow.v4exp.grid import (V4ExpError, GridWorld, canonical_json,
                                geometry_from_routes)
from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.mirror import MIRROR_SCHEMA, solve_board_injected
from pcbflow.v4_2.leg import subnet_resolve

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")

REUSE_NAMES = (
    ["board-snapshot-hol-f1-%02d.json" % i for i in (17, 18, 19, 20)]
    + ["board-snapshot-hol-f6-%02d.json" % i for i in (1, 2, 3, 4)]
    + ["board-snapshot-hol-f8-%02d.json" % i for i in (1, 2, 3, 4)]
)

_MISSING = [n for n in REUSE_NAMES if not os.path.isfile(os.path.join(_CMP, n))]
assert not _MISSING, "missing reuse scenario anchors: %s" % _MISSING


def _board(name):
    with open(os.path.join(_CMP, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _request(board):
    return {"route_order": sorted(n["net_id"] for n in board["nets"]),
            "group": "A"}


# ---------------------------------------------------------------- P0-a mirror

@pytest.mark.parametrize("name", REUSE_NAMES)
def test_mirror_byte_parity(name):
    board = _board(name)
    req = _request(board)
    frozen = solve_board(board, req)
    mirror = solve_board_injected(board, req)
    assert canonical_json(mirror) == canonical_json(frozen)


def test_mirror_zero_valued_bias_is_noop():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    world = GridWorld(board)
    frozen = solve_board(board, req)
    inc = solve_board_injected(board, req)
    # zero-valued bias over a central rect on F.Cu must not flip any bit
    rect = list(board["board"]["bbox_mm"])
    rect = [rect[0] + (rect[2] - rect[0]) * 0.25,
            rect[1] + (rect[3] - rect[1]) * 0.25,
            rect[0] + (rect[2] - rect[0]) * 0.75,
            rect[1] + (rect[3] - rect[1]) * 0.75]
    fcu = world.layer_index["F.Cu"]
    bias = {(fcu, ix, iy): 0.0
            for (ix, iy) in world.cells_in_rect(rect, 0.0)}
    assert bias
    mirror = solve_board_injected(board, req, cost_bias=bias)
    assert canonical_json(mirror) == canonical_json(frozen)
    assert canonical_json(mirror) == canonical_json(inc)


def test_negative_bias_rejected():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    with pytest.raises(V4ExpError):
        solve_board_injected(board, req, cost_bias={(0, 0, 0): -0.5})


def test_cost_bias_changes_search():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    world = GridWorld(board)
    baseline = solve_board(board, req)
    assert baseline["status"] == "sat"
    rect = list(board["board"]["bbox_mm"])
    rect = [rect[0] + (rect[2] - rect[0]) * 0.25,
            rect[1] + (rect[3] - rect[1]) * 0.25,
            rect[0] + (rect[2] - rect[0]) * 0.75,
            rect[1] + (rect[3] - rect[1]) * 0.75]
    fcu = world.layer_index["F.Cu"]
    bias = {(fcu, ix, iy): 5.0
            for (ix, iy) in world.cells_in_rect(rect, 0.0)}
    inj = solve_board_injected(board, req, cost_bias=bias)
    assert inj["schema"] == MIRROR_SCHEMA
    assert inj["solver_version"].endswith("+v4_2-mirror-1")
    assert inj["injections"]["cost_bias_cells"] == len(bias)
    assert (inj["route_manifest_sha256_at_run"]
            != baseline["route_manifest_sha256_at_run"])
    if inj["status"] == "sat":
        assert sum(inj["metrics"]["violations"].values()) == 0


def test_hard_keepout_changes_search():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    world = GridWorld(board)
    baseline = solve_board(board, req)
    assert baseline["status"] == "sat"
    geo = geometry_from_routes(world, baseline["routes"], baseline["vias"])
    ko = {li: set(cells) for li, cells in geo["n1"].items() if cells}
    assert ko
    inj = solve_board_injected(board, req, hard_keepout=ko)
    assert inj["schema"] == MIRROR_SCHEMA
    assert sum(inj["injections"]["hard_keepout_cells_by_layer"].values()) > 0
    changed = (inj["route_manifest_sha256_at_run"]
               != baseline["route_manifest_sha256_at_run"])
    assert changed or inj["status"] == "failed"
    if inj["status"] == "sat":
        assert sum(inj["metrics"]["violations"].values()) == 0


# ------------------------------------------------------------- P0-b subnet leg

_SHARED_FIELDS = ("routes", "vias", "metrics", "status")


@pytest.mark.parametrize("name", REUSE_NAMES)
def test_leg_full_deletion_parity(name):
    board = _board(name)
    req = _request(board)
    frozen = solve_board(board, req)
    leg = subnet_resolve(board, req, frozen,
                         deleted_nets=list(req["route_order"]),
                         reroute_order=req["route_order"])
    for field in _SHARED_FIELDS:
        assert canonical_json(leg[field]) == canonical_json(frozen[field]), field
    assert leg["metrics"]["search_nodes"] == frozen["metrics"]["search_nodes"]


def test_leg_partial_delete_keeps_others_byte_exact():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    incumbent = solve_board(board, req)
    assert incumbent["status"] == "sat"
    leg = subnet_resolve(board, req, incumbent, deleted_nets=["n3"])
    assert leg["status"] == "sat"
    kept = [r for r in incumbent["routes"] if r["net_id"] != "n3"]
    assert canonical_json(leg["routes"][:len(kept)]) == canonical_json(kept)
    rerouted = [r for r in leg["routes"] if r["net_id"] == "n3"]
    assert rerouted
    assert sum(leg["metrics"]["violations"].values()) == 0
    assert leg["metrics"]["all_connected"] is True


def test_leg_determinism_double_run():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    incumbent = solve_board(board, req)
    a = subnet_resolve(board, req, incumbent, deleted_nets=["n3", "n1"])
    b = subnet_resolve(board, req, incumbent, deleted_nets=["n3", "n1"])
    assert canonical_json(a) == canonical_json(b)


def test_leg_rejects_bad_inputs():
    board = _board("board-snapshot-hol-f6-01.json")
    req = _request(board)
    incumbent = solve_board(board, req)
    with pytest.raises(V4ExpError):
        subnet_resolve(board, req, incumbent, deleted_nets=["n99"])
    with pytest.raises(V4ExpError):
        subnet_resolve(board, req, incumbent, deleted_nets=["n1", "n2"],
                       reroute_order=["n1"])
    with pytest.raises(V4ExpError):
        subnet_resolve(board, req, incumbent, deleted_nets=["n1", "n1"])
