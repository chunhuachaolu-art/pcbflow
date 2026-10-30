# -*- coding: utf-8 -*-
"""staging/rollback：原子提交、中断注入回滚无残留、append-only。"""
import json
import os

import pytest

from v5 import staging
from v5.staging import (StagingError, StagingTransaction, assert_no_residue,
                        evidence_list, recover)


@pytest.fixture()
def roots(tmp_path):
    return str(tmp_path / "staging"), str(tmp_path / "evidence")


def test_commit_moves_files_atomically(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-1")
    tx.write_bytes("board.metrics.json", b"{}")
    tx.write_bytes("sub/board.view.json", b"[]")
    tx.commit()
    assert open(os.path.join(f, "run-1", "board.metrics.json"), "rb").read() == b"{}"
    assert open(os.path.join(f, "run-1", "sub", "board.view.json"), "rb").read() == b"[]"
    assert not os.path.exists(os.path.join(s, "run-1"))
    assert tx.committed


def test_rollback_leaves_no_residue(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-2")
    tx.write_bytes("a.json", b"1")
    tx.rollback()
    assert_no_residue(s)
    assert evidence_list(f) == []
    assert tx.rolled_back


def test_interrupt_injection_recovers(roots):
    """中断注入：commit 前崩溃 → recover() 清 staging，final 无半成品。"""
    s, f = roots
    tx = StagingTransaction(s, f, "run-3")
    tx.write_bytes("partial.json", b"x")
    simulated_crash = True  # 此处不 commit，模拟进程死亡
    assert simulated_crash
    cleaned = recover(s, f)
    assert "run-3" in cleaned
    assert_no_residue(s)
    assert evidence_list(f) == []


def test_interrupt_during_commit_keeps_final_consistent(roots, monkeypatch):
    """commit 中途崩（第一文件已 replace、第二未及）→ recover 后 final 只含已提交项，
    无半成品目录（append-only 语义下已 replace 的文件保留）。"""
    s, f = roots
    tx = StagingTransaction(s, f, "run-4")
    tx.write_bytes("a.json", b"A")
    tx.write_bytes("b.json", b"B")
    real_replace = os.replace
    state = {"calls": 0}

    def flaky_replace(src, dst):
        state["calls"] += 1
        if state["calls"] == 2:
            raise RuntimeError("injected crash")
        return real_replace(src, dst)

    monkeypatch.setattr(staging.os, "replace", flaky_replace)
    with pytest.raises(RuntimeError):
        tx.commit()
    assert os.path.exists(os.path.join(f, "run-4", "a.json"))
    assert not os.path.exists(os.path.join(f, "run-4", "b.json"))
    monkeypatch.undo()
    cleaned = recover(s, f)
    assert "run-4" in cleaned
    assert sorted(evidence_list(f)) == ["run-4/a.json"]


def test_double_commit_rejected(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-5")
    tx.write_bytes("x.json", b"1")
    tx.commit()
    with pytest.raises(StagingError):
        tx.commit()


def test_rollback_after_commit_rejected(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-6")
    tx.write_bytes("x.json", b"1")
    tx.commit()
    with pytest.raises(StagingError):
        tx.rollback()


def test_write_after_commit_rejected(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-7")
    tx.write_bytes("x.json", b"1")
    tx.commit()
    with pytest.raises(StagingError):
        tx.write_bytes("y.json", b"2")


def test_empty_commit_rejected(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-8")
    with pytest.raises(StagingError):
        tx.commit()


def test_path_traversal_rejected(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-9")
    with pytest.raises(StagingError):
        tx.write_bytes("../escape.json", b"1")


def test_write_json_is_canonical(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-10")
    tx.write_json("doc.json", {"b": 1, "a": 2})
    tx.commit()
    raw = open(os.path.join(f, "run-10", "doc.json"), "rb").read()
    assert raw == b'{"a":2,"b":1}'


def test_journal_tracks_files(roots):
    s, f = roots
    tx = StagingTransaction(s, f, "run-11")
    tx.write_bytes("one.json", b"1")
    journal = json.load(open(os.path.join(s, "run-11", "_journal.json"), encoding="utf-8"))
    assert journal["state"] == "writing" and journal["files"] == ["one.json"]
