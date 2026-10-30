"""V4.2 M1 tests: f12 family, deterministic GT, blinded inspector packages.

prereg: out/v4.2-seat/m1/prereg-m1.json (written before any M1 run).
"""

import json
import os

import pytest

from pcbflow.v4exp.cmp_scenarios import canonical_geometry_hash
from pcbflow.v4exp.grid import canonical_json
from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.family import F12_IDS, emit, generate_f12_board
from pcbflow.v4_2.gt import EPSILON, gt_for_scenario, incumbent_run
from pcbflow.v4_2.inspector import (assign_pids, blind, inspector_task,
                                    package_svg)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")
REUSE = (["board-snapshot-hol-f6-%02d.json" % i for i in (1, 2, 3, 4)]
         + ["board-snapshot-hol-f8-%02d.json" % i for i in (1, 2, 3, 4)])


def _board(name):
    with open(os.path.join(_CMP, name), "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ family f12

def test_f12_deterministic_and_unique():
    boards = [generate_f12_board(sid).to_obj() for sid in F12_IDS]
    again = [generate_f12_board(sid).to_obj() for sid in F12_IDS]
    for a, b in zip(boards, again):
        assert canonical_json(a) == canonical_json(b)
    hashes = {canonical_geometry_hash(b) for b in boards}
    assert len(hashes) == len(F12_IDS)  # no duplicate geometry
    for b in boards:
        assert b["family"] == "f12" and b["schema"] == "pcbflow.v4exp.board/1"


def test_f12_emit_byte_stable(tmp_path):
    h1 = emit(str(tmp_path / "a"))
    h2 = emit(str(tmp_path / "b"))
    assert h1 == h2 and len(h1) == len(F12_IDS)


def test_f12_solves_and_gt_runs():
    sat = 0
    for sid in F12_IDS:
        board = generate_f12_board(sid).to_obj()
        run = incumbent_run(board)
        if run["status"] == "sat":
            sat += 1
            gt = gt_for_scenario(board)
            assert gt["status"] == "ok"
            assert gt["n_routes"] == len(run["routes"])
            assert gt["per_route"]
    assert sat >= 1  # satisfiable-by-construction sanity (coverage disclosed in report)


# ------------------------------------------------------------------------ GT

@pytest.mark.parametrize("name", REUSE)
def test_gt_determinism_and_shape(name):
    board = _board(name)
    a = gt_for_scenario(board)
    b = gt_for_scenario(board)
    assert canonical_json(a) == canonical_json(b)
    if a["status"] == "ok":
        assert a["epsilon"] == EPSILON
        assert 0.0 <= a["random_baseline"] <= 1.0
        for nid, per in a["per_net"].items():
            if per["leg_status"] == "sat":
                assert per["improvable"] == (per["improvement"] > EPSILON)
            else:
                assert per["improvable"] is False


def test_gt_spot_manual_check():
    """Independent quick check: recompute one net's improvement directly."""
    board = _board("board-snapshot-hol-f6-01.json")
    from pcbflow.v4_2.gt import reorder_run
    inc = incumbent_run(board)
    assert inc["status"] == "sat"
    nid = sorted(n["net_id"] for n in board["nets"])[0]
    leg = reorder_run(board, nid)
    gt = gt_for_scenario(board)
    if leg["status"] == "sat":
        direct = round(inc["metrics"]["objective"]
                       - leg["metrics"]["objective"], 6)
        assert gt["per_net"][nid]["improvement"] == direct
    else:
        assert gt["per_net"][nid]["improvement"] is None


def test_identity_lemma_delete_replace():
    """Structural lemma (prereg note 2): delete+replace improvement == 0.0
    for every net on a sat incumbent."""
    board = _board("board-snapshot-hol-f6-01.json")
    from pcbflow.v4_2.gt import identity_check
    res = identity_check(board)
    assert res["status"] == "ok"
    assert res["all_zero"] is True
    assert res["per_net"]


# -------------------------------------------------------------- inspector I/O

ALL_SIDS = (["cal-f12-%02d" % i for i in range(1, 9)]
            + ["hol-f6-%02d" % i for i in (1, 2, 3, 4)]
            + ["hol-f8-%02d" % i for i in (1, 2, 3, 4)])


def test_pid_assignment_deterministic_no_position_leak():
    p1 = assign_pids(ALL_SIDS)
    p2 = assign_pids(ALL_SIDS)
    assert p1 == p2
    assert sorted(p1.values()) == ["p%02d" % (i + 1) for i in range(16)]
    # pid must not correlate with sid order (deterministic shuffle)
    first_two = [sid for sid in ALL_SIDS if p1[sid] in ("p01", "p02")]
    assert first_two != ALL_SIDS[:2]


@pytest.mark.parametrize("name", REUSE[:3] + REUSE[4:7])
def test_blinding_strips_identity(name):
    sid = name.replace("board-snapshot-", "").replace(".json", "")
    board = _board(name)
    run = incumbent_run(board)
    if run["status"] != "sat":
        pytest.skip("failed incumbent: no package to blind")
    svg = package_svg(board, run)
    assert 'data-pcbflow-schema="v4-svg-route-2"' in svg
    pid = assign_pids(ALL_SIDS)[sid]
    blinded = blind(svg, sid, pid)
    assert sid not in blinded
    assert pid in blinded


def test_inspector_task_text_carries_contract():
    board = _board("board-snapshot-hol-f6-01.json")
    run = incumbent_run(board)
    svg = package_svg(board, run)
    task = inspector_task(svg, "p07")
    for token in ("detour_excess", "blocks_escape", "2.0 mm",
                  "EXACTLY ONE entry", "flags", "abstain"):
        assert token in task["user"] + task["system"]
