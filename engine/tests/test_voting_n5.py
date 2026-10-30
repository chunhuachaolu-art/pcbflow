# -*- coding: utf-8 -*-
"""N=5 诊断扩编合同测试（voting.py 用户裁定扩展 2026-09-14；多数门 n//2+1）。"""
import pytest

from v5.voting import VotingError, majority_gate, tally


def _ballot(aid, order, subjects):
    return {"agent_id": aid, "registration_order": order,
            "board_sha256": "b" * 64, "pkg_sha256": "p" * 64,
            "problem_items": [{"subject": s, "kind": "K", "note": ""}
                              for s in subjects],
            "confidence_rank": [], "raw_ref": "runs/%s" % aid}


def test_majority_gate_formula():
    assert majority_gate(2) == 2 and majority_gate(3) == 2 and majority_gate(5) == 3


def test_n5_gate_three_fifths():
    t = tally([_ballot("A%d" % i, i, ss) for i, ss in enumerate(
        [["S1", "S2"], ["S1"], ["S1", "S3"], [], ["S1"]], start=1)])
    assert [m["subject"] for m in t["majority_items"]] == ["S1"]
    assert t["majority_items"][0]["evidence"] == "4/5"
    assert t["downgraded"] is False and t["tie_note"] is None
    # 少数派双向归因：A4 漏列 S1；A1(S2)/A3(S3) 提出未入台账 subject——共 3 票
    assert len(t["minority_dissents"]) == 3
    by_id = {d["agent_id"]: d for d in t["minority_dissents"]}
    assert by_id["A4"]["missing_majority_subjects"] == ["S1"]
    assert by_id["A1"]["unledgered_subjects"] == ["S2"]
    assert by_id["A3"]["unledgered_subjects"] == ["S3"]


def test_n5_exactly_at_gate():
    t = tally([_ballot("A%d" % i, i, ss) for i, ss in enumerate(
        [["S1"], ["S2"], ["S1"], ["S2"], ["S1"]], start=1)])
    assert [m["subject"] for m in t["majority_items"]] == ["S1"]
    assert t["majority_items"][0]["evidence"] == "3/5"


def test_n5_tie_all_below_gate():
    t = tally([_ballot("A%d" % i, i, ["S%d" % i]) for i in range(1, 6)])
    assert t["majority_items"] == []
    assert t["tie_note"] and "3 票多数门" in t["tie_note"]


def test_n4_failclosed():
    with pytest.raises(VotingError):
        tally([_ballot("A%d" % i, i, []) for i in range(1, 5)])
