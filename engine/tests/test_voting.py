# -*- coding: utf-8 -*-
"""v5.voting 单测（A6 计票规则；P3 交付规格）：

- 3 票 2 同 1 异 → 入台账（2/3）+ 少数派整票全文在场；
- 3 票全同 → 3/3、无少数派；
- 3 票各异 → 平票不入台账 + tie_note 按先注册 agent 序留痕；
- 2 票同 → 2/2 入台账 + downgraded + 置信降档标注；
- 2 票 1 同 1 异 → 不入台账；
- provenance 不齐（board_sha256/pkg_sha256）→ ValueError；
- 双跑字节等 + 无副作用（入参不被改动）；
- 形状 fail-closed（票数/必填键/重复注册序）；
- subject 规范化与未入台账 subject 的全文留痕；
- A6 作用域封口：产物恰含四键，无注册表/规则改写通道。
"""
import copy

import pytest

from v5 import canonical
from v5.voting import VotingError, normalize_subject, tally

BOARD_SHA = "a" * 64
PKG_SHA = "b" * 64


def ballot(agent_id, order, subjects, kind="width_defect", note="低于 R1 下限",
           board_sha=BOARD_SHA, pkg_sha=PKG_SHA, rank=None):
    """构造一张合形状序数票（默认值齐备，便于单字段变异）。"""
    return {
        "agent_id": agent_id,
        "registration_order": order,
        "board_sha256": board_sha,
        "pkg_sha256": pkg_sha,
        "problem_items": [{"subject": s, "kind": kind, "note": note}
                          for s in subjects],
        "confidence_rank": rank if rank is not None else list(subjects),
        "raw_ref": "out/run-%s/response-raw.md" % agent_id,
    }


# --------------------------------------------------------------- 多数门与少数派

def test_two_of_three_enters_ledger_with_minority_fulltext():
    """3 票 2 同 1 异：2/3 入台账；异见票整票全文进 minority_dissents。"""
    b1 = ballot("agent-a", 1, ["P8 计划宽低于 R1 下限"])
    b2 = ballot("agent-b", 2, ["P8 计划宽低于 R1 下限"])
    b3 = ballot("agent-c", 3, ["P9 串扰超预算"])
    result = tally([b3, b1, b2])  # 故意乱序传入：先注册序由 registration_order 定
    assert set(result) == {"majority_items", "minority_dissents",
                           "downgraded", "tie_note"}
    assert result["majority_items"] == [
        {"subject": "P8 计划宽低于 R1 下限", "evidence": "2/3",
         "voters": ["agent-a", "agent-b"]}]
    assert result["downgraded"] is False
    assert result["tie_note"] is None
    dissents = result["minority_dissents"]
    assert len(dissents) == 1
    d = dissents[0]
    assert d["agent_id"] == "agent-c"
    assert d["registration_order"] == 3
    assert d["missing_majority_subjects"] == ["P8 计划宽低于 R1 下限"]
    assert d["unledgered_subjects"] == ["P9 串扰超预算"]
    # 少数派全文留痕：整票逐字在场（含 problem_items 全文）
    assert d["ballot"]["problem_items"] == b3["problem_items"]
    assert d["ballot"]["confidence_rank"] == b3["confidence_rank"]
    assert d["ballot"]["raw_ref"] == b3["raw_ref"]


def test_three_of_three_unanimous():
    """3 票全同：3/3 入台账，无少数派，无降档，无平票注。"""
    ballots = [ballot("a", 1, ["X"]), ballot("b", 2, ["X"]), ballot("c", 3, ["X"])]
    result = tally(ballots)
    assert result["majority_items"] == [
        {"subject": "X", "evidence": "3/3", "voters": ["a", "b", "c"]}]
    assert result["minority_dissents"] == []
    assert result["downgraded"] is False
    assert result["tie_note"] is None


def test_all_different_tie_not_in_ledger_with_tie_note():
    """3 票各异：平票全部不入台账；tie_note 按先注册 agent 序留痕；三票全文在场。"""
    ballots = [ballot("a", 1, ["问题甲"]), ballot("b", 2, ["问题乙"]),
               ballot("c", 3, ["问题丙"])]
    result = tally(ballots)
    assert result["majority_items"] == []
    assert result["downgraded"] is False
    note = result["tie_note"]
    assert note is not None and "平票" in note
    # 按先注册 agent 序留痕：a@1 在 b@2 前，b@2 在 c@3 前（确定性 tie-break 留痕）
    assert note.index("问题甲（a@1）") < note.index("问题乙（b@2）") < note.index("问题丙（c@3）")
    # 三票互为少数派：整票全文全部留痕
    assert [d["agent_id"] for d in result["minority_dissents"]] == ["a", "b", "c"]
    assert all(d["unledgered_subjects"] for d in result["minority_dissents"])


def test_unledgered_subject_preserved_via_dissent_fulltext():
    """多数成立但个别 agent 多提了未入台账 subject：该票全文（含多提项）留痕。"""
    b1 = ballot("a", 1, ["X", "Y"])
    b2 = ballot("b", 2, ["X"])
    b3 = ballot("c", 3, [])
    result = tally([b1, b2, b3])
    assert result["majority_items"] == [
        {"subject": "X", "evidence": "2/3", "voters": ["a", "b"]}]
    dissents = result["minority_dissents"]
    assert [d["agent_id"] for d in dissents] == ["a", "c"]  # 先注册序
    a_entry = dissents[0]
    assert a_entry["unledgered_subjects"] == ["Y"]
    assert a_entry["missing_majority_subjects"] == []
    assert a_entry["ballot"]["problem_items"] == b1["problem_items"]  # Y 全文在整票内
    c_entry = dissents[1]
    assert c_entry["missing_majority_subjects"] == ["X"]
    assert c_entry["unledgered_subjects"] == []


# --------------------------------------------------------------- N=2 降档

def test_two_ballots_same_downgraded():
    """N=2 缺席降档：2/2 才入台账 + downgraded=True + 置信降档标注。"""
    result = tally([ballot("a", 1, ["X"]), ballot("b", 2, ["X"])])
    assert result["majority_items"] == [
        {"subject": "X", "evidence": "2/2", "voters": ["a", "b"]}]
    assert result["downgraded"] is True
    assert result["tie_note"] is not None and "降档" in result["tie_note"]
    assert result["minority_dissents"] == []


def test_two_ballots_split_not_in_ledger():
    """N=2 一同一异：须 2/2，1 票 subject 不入台账；降档标注与平票留痕并陈。"""
    result = tally([ballot("a", 1, ["X"]), ballot("b", 2, ["Y"])])
    assert result["majority_items"] == []
    assert result["downgraded"] is True
    assert "平票" in result["tie_note"] and "降档" in result["tie_note"]
    assert {d["agent_id"] for d in result["minority_dissents"]} == {"a", "b"}


# --------------------------------------------------------------- provenance 对账

def test_provenance_mismatch_raises_valueerror():
    """同源同 hash 是 A6 硬要求：board_sha256 / pkg_sha256 不齐 → ValueError。"""
    base = [ballot("a", 1, ["X"]), ballot("b", 2, ["X"]), ballot("c", 3, ["X"])]
    bad_board = [base[0], base[1],
                 ballot("c", 3, ["X"], board_sha="f" * 64)]
    with pytest.raises(ValueError) as ei:
        tally(bad_board)
    assert "board_sha256" in str(ei.value)
    bad_pkg = [base[0], base[1], ballot("c", 3, ["X"], pkg_sha="e" * 64)]
    with pytest.raises(ValueError) as ei:
        tally(bad_pkg)
    assert "pkg_sha256" in str(ei.value)


# --------------------------------------------------------------- 确定性与无副作用

def test_double_run_bytes_equal_and_input_untouched():
    """双跑 canonical 字节相等（§3.4）；入参票不被改动（纯函数无副作用）。"""
    ballots = [ballot("a", 1, ["X", "Y"]), ballot("b", 2, ["X"]),
               ballot("c", 3, ["Z"])]
    snapshot = copy.deepcopy(ballots)
    r1 = tally(ballots)
    r2 = tally(ballots)
    assert canonical.canonical_json(r1) == canonical.canonical_json(r2)
    assert ballots == snapshot  # 计票不改票


def test_result_has_no_registry_rewrite_channel():
    """A6 作用域封口：产物只含事实聚合四键，无注册表/compiled_rule 改写通道。"""
    result = tally([ballot("a", 1, ["X"]), ballot("b", 2, ["X"]),
                    ballot("c", 3, ["X"])])
    assert set(result) == {"majority_items", "minority_dissents",
                           "downgraded", "tie_note"}
    for key in ("registry", "compiled_rule", "priority", "rules"):
        assert key not in result
    assert all(set(item) == {"subject", "evidence", "voters"}
               for item in result["majority_items"])


# --------------------------------------------------------------- 形状 fail-closed

@pytest.mark.parametrize("mutate,frag", [
    (lambda bs: bs[:1], "票数"),                                        # N=1
    (lambda bs: bs + [ballot("d", 4, ["X"])], "票数"),                  # N=4
    (lambda bs: [{k: v for k, v in bs[0].items() if k != "raw_ref"}] + bs[1:],
     "raw_ref"),                                                        # 缺必填键
    (lambda bs: [bs[0], ballot("a", 2, ["X"])], "agent_id"),            # agent 重复
    (lambda bs: [ballot("a", 7, ["X"]), ballot("b", 7, ["X"])] + bs[2:],
     "registration_order"),                                             # 注册序重复
    (lambda bs: [dict(bs[0], problem_items=[{"subject": " ", "kind": "k",
                                             "note": "n"}])] + bs[1:],
     "subject"),                                                        # 空 subject
])
def test_ballot_shape_fail_closed(mutate, frag):
    ballots = [ballot("a", 1, ["X"]), ballot("b", 2, ["X"]), ballot("c", 3, ["X"])]
    with pytest.raises(VotingError) as ei:
        tally(mutate(ballots))
    assert frag in str(ei.value)


# --------------------------------------------------------------- subject 规范化

def test_subject_normalization_counts_as_same_key():
    """规范化键：首尾/连续空白折叠后同键；台账记规范化形态。"""
    b1 = ballot("a", 1, ["  P8  线宽缺陷 "])
    b2 = ballot("b", 2, ["P8 线宽缺陷"])
    b3 = ballot("c", 3, ["别的缺陷"])
    result = tally([b1, b2, b3])
    assert result["majority_items"] == [
        {"subject": "P8 线宽缺陷", "evidence": "2/3", "voters": ["a", "b"]}]


def test_normalize_subject_function():
    assert normalize_subject("  A\t B  ") == "A B"
    assert normalize_subject("X") == "X"
