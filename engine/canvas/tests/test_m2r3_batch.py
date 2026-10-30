# -*- coding: utf-8 -*-
"""M2R3 D-CT-034 batch semantics regression tests.

These tests exercise the isolated consistent batch seam without touching any
frozen M2R2 artifacts.  Legacy ``apply_batch`` remains covered by the K1 suite.
"""
import copy

import pytest

from canvas import protocol as cpr
from canvas import validate as cval
from canvas.tests.test_k1_fixtures import synth_state

SUB = {"action": "submit"}


def _route(net, points, layer="F.Cu"):
    return {"action": "route", "net_id": net,
            "waypoints": [list(p) for p in points], "layer": layer}


def _via(net, grid):
    return {"action": "via", "net_id": net, "grid": list(grid)}


def test_reorder_is_barrier_scoped_and_idempotent():
    route_carrier = _route("NET-A", [(4, 4), (12, 4), (20, 4)])
    via = _via("NET-A", (12, 4))
    route_endpoint = _route("NET-A", [(12, 4), (20, 4)], "B.Cu")
    actions = [
        {"action": "width_class", "net_id": "NET-A", "class": "nom"},
        route_endpoint,
        via,
        route_carrier,
        {"action": "ripup", "net_id": "NET-A"},
        _via("NET-A", (12, 4)),
        _route("NET-A", [(4, 4), (12, 4)], "B.Cu"),
        SUB,
    ]
    got = cpr.reorder_batch(actions)
    # The first route/via segment cannot cross width_class, and the second
    # segment cannot cross ripup.  submit remains the final barrier.
    assert got[0] == actions[0]
    assert got[4] == actions[4]
    assert got[-1] == SUB
    assert cpr.reorder_batch(got) == got
    assert got != actions
    # Returned actions are copies, not aliases into the caller's nested lists.
    got[1]["waypoints"][0][0] = 999
    assert actions[1]["waypoints"][0][0] != 999


def test_consistent_batch_accepts_forward_via_on_expanded_route():
    st = synth_state()
    route = _route("NET-A", [(4, 4), (20, 4)])
    via = _via("NET-A", (12, 4))
    legacy = synth_state()
    legacy_res = cpr.apply_batch(legacy, [via, route, SUB])
    assert legacy_res[0]["accepted"] is False
    assert legacy_res[0]["code"] == cpr.V_VIA_OFF_PATH

    res = cpr.apply_consistent_batch(st, [via, route, SUB])
    assert [r["accepted"] for r in res] == [True, True, True], res
    assert st.via_grids("NET-A") == {(12, 4)}
    assert st.connectivity["NET-A"] is True


def test_fixed_point_removes_route_attached_only_to_rejected_via(monkeypatch):
    st = synth_state()
    original = cval.validate_edit

    def reject_via(inner, action, batch_ctx=None):
        if action.get("action") == "via":
            return False, cpr.V_HOLE_VIA, "synthetic forced via rejection"
        return original(inner, action, batch_ctx)

    monkeypatch.setattr(cval, "validate_edit", reject_via)
    route = _route("NET-A", [(4, 4), (12, 4)])
    via = _via("NET-A", (12, 4))
    res = cpr.apply_consistent_batch(st, [via, route, SUB])
    assert res[0]["accepted"] is False
    assert res[0]["code"] == cpr.V_HOLE_VIA
    assert res[1]["accepted"] is False
    assert res[1]["code"] == cpr.V_ENDPT_NOT_ATTACHED
    assert not st.segs and not st.vias


def test_fixed_point_removes_carrier_via_when_all_routes_rejected(monkeypatch):
    st = synth_state()
    original = cval.validate_edit

    def reject_route(inner, action, batch_ctx=None):
        if action.get("action") == "route":
            return False, cpr.V_CLEARANCE, "synthetic forced route rejection"
        return original(inner, action, batch_ctx)

    monkeypatch.setattr(cval, "validate_edit", reject_route)
    route = _route("NET-A", [(4, 4), (12, 4), (20, 4)])
    via = _via("NET-A", (12, 4))
    res = cpr.apply_consistent_batch(st, [route, via, SUB])
    assert res[0]["accepted"] is False
    assert res[0]["code"] == cpr.V_CLEARANCE
    assert res[1]["accepted"] is False
    assert res[1]["code"] == cpr.V_VIA_OFF_PATH
    assert not st.segs and not st.vias


def test_existing_via_support_survives_duplicate_batch_via():
    st = synth_state()
    st.add_via("NET-A", [12, 4])
    st.recompute_connectivity()
    duplicate = _via("NET-A", (12, 4))
    route = _route("NET-A", [(4, 4), (12, 4)])
    res = cpr.apply_consistent_batch(st, [duplicate, route, SUB])
    assert res[0]["accepted"] is False
    assert res[0]["code"] == cpr.V_DUPLICATE_VIA
    assert res[1]["accepted"] is True
    assert st.via_grids("NET-A") == {(12, 4)}
    assert len(st.segs) == 1


def test_consistent_batch_does_not_pollute_sequences_on_retries(monkeypatch):
    st = synth_state()
    before = st.sha256()
    original = cval.validate_edit
    calls = {"n": 0}

    def reject_once(inner, action, batch_ctx=None):
        if action.get("action") == "route" and calls["n"] == 0:
            calls["n"] += 1
            return False, cpr.V_CLEARANCE, "first pass rejection"
        return original(inner, action, batch_ctx)

    monkeypatch.setattr(cval, "validate_edit", reject_once)
    route = _route("NET-A", [(4, 4), (20, 4)])
    res = cpr.apply_consistent_batch(st, [route, SUB])
    assert res[0]["accepted"] is False
    assert st.sha256() == before
    assert st._seg_seq == 0


def test_reorder_does_not_mutate_input_actions():
    actions = [_via("NET-A", (12, 4)), _route("NET-A", [(4, 4), (20, 4)]), SUB]
    snapshot = copy.deepcopy(actions)
    cpr.reorder_batch(actions)
    assert actions == snapshot
