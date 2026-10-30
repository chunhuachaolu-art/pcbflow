"""APPROVALS-1 人工批准登记测试（disposition 域语义+链完整性+确定性）。

2026-09-03 用户六项批准（「全部允许」）的登记红线：
  - human authority 只出现在 disposition 类 entry 且恒 untrusted
    （处置是决定不是事实，validator 白名单强制）；
  - 批准不得携带门写禁区键（validate_no_gate_write），不改机器门裁决
    语义（TL-3 fail / TL-4-G blocked / TL-2 not reached 保持）；
  - 批准 kind=accept 非 waive：机器门缺口不得由豁免绕过（合取关系）；
  - evidence 指针=磁盘实读 sha256（缺一 fail-closed 拒绝构造）；
  - 生成器纪律：同输入 byte-exact、无 wall-clock（日期为人工声明常量）。

依赖 cwd=pcbflow 根（既有测试约定）；库级用合成 hash，CLI 级用临时
evidence 树，不触碰 out/ 冻结产物。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import approvals, hashing, ledger, v3cli
from pcbflow import disposition as disposition_mod


def _fake_hashes():
    return {name: hashing.sha256_text(name)
            for name, _ in approvals.EVIDENCE_FILES}


def _build():
    return approvals.build_approvals_bundle(_fake_hashes())


def _run_cli(capsys, argv):
    rc = v3cli.main(argv)
    out = capsys.readouterr().out
    return rc, out, json.loads(out)


# ---------------------------------------------------------------------------
# 库级：结构与语义
# ---------------------------------------------------------------------------

def test_bundle_six_approvals_chain_valid():
    bundle = _build()
    assert bundle["approval_count"] == 6
    assert [d["disposition_id"] for d in bundle["dispositions"]] == \
        [s["approval_id"] for s in approvals.APPROVAL_SPECS]
    assert bundle["ledger_verify"] == {"chain_errors": [],
                                       "supersedes_errors": []}
    assert bundle["approval_date"] == "2026-09-03"
    assert bundle["approver"] == {"actor": "user",
                                  "actor_role": "human_authority"}


def test_human_authority_disposition_untrusted_only():
    for e in _build()["ledger_entries"]:
        assert e["entry_kind"] == "disposition"
        assert e["authority"] == "human"
        assert e["trust_level"] == "untrusted"   # 处置恒不可升级
        assert e["actor"] == "user"
        assert e["actor_role"] == "human_authority"


def test_no_gate_write_in_any_disposition():
    bundle = _build()
    for d in bundle["dispositions"]:
        assert disposition_mod.validate_no_gate_write(d) == []
    assert set(map(tuple, bundle["gate_write_scan"].values())) == {()}


def test_approvals_are_accept_not_waiver():
    # 批准走 accept：与机器门合取；空 policy 下 waive 全拒的语义不被触碰
    for d in _build()["dispositions"]:
        assert d["kind"] == "accept"
        assert disposition_mod.check_waiver_policy(d, {}) == []


def test_missing_evidence_fail_closed():
    hashes = _fake_hashes()
    hashes.pop("tl4_proposal_patch_smoke_4l")
    with pytest.raises(ValueError):
        approvals.build_approvals_bundle(hashes)


def test_frozen_gate_status_note_present():
    bundle = _build()
    assert "TL-3-G1 physics_gate=fail（保持）" \
        in bundle["frozen_machine_gate_status"]
    assert "TL-4-G=blocked（保持）" in bundle["frozen_machine_gate_status"]
    assert "not reached（保持）" in bundle["frozen_machine_gate_status"]


def test_semantics_recorded_per_approval():
    texts = {d["disposition_id"]: d["rationale_text"]
             for d in _build()["dispositions"]}
    for text in texts.values():
        assert "2026-09-03" in text        # 批准日期（人工声明常量）
    assert "绝不能把门翻成 pass" in texts["APR-0003"]
    assert "human_approved_machine_blocked" in texts["APR-0004"]
    assert "not reached" in texts["APR-0005"]
    assert "仅限语料获取用途" in texts["APR-0006"]
    assert "不构成新增机器门裁决" in texts["APR-0001"]
    assert "不得回写本批准" in texts["APR-0002"]


# ---------------------------------------------------------------------------
# 链与落盘字节口径
# ---------------------------------------------------------------------------

def test_ledger_jsonl_round_trip_verifies():
    bundle = _build()
    data = approvals.ledger_file_bytes(bundle["ledger_entries"])
    assert hashing.sha256_bytes(data) == bundle["ledger_file_sha256"]
    entries = [json.loads(line) for line in data.decode("utf-8").splitlines()]
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    assert ledger.verify_against_checkpoint(
        entries, bundle["ledger_checkpoint"]) == []


def test_payload_ref_binds_disposition_file_bytes():
    bundle = _build()
    for e, d in zip(bundle["ledger_entries"], bundle["dispositions"]):
        raw = hashing.canonical_json_bytes(d)
        assert e["payload_ref"] == hashing.sha256_bytes(raw)
        assert e["disposition_refs"] == [d["disposition_id"]]


def test_deterministic_byte_exact():
    a = hashing.canonical_json_bytes(_build())
    b = hashing.canonical_json_bytes(_build())
    assert a == b
    # schema 基线 hash 来自注册表实算（稳定）
    s1 = approvals.schema_baseline_hashes()
    s2 = approvals.schema_baseline_hashes()
    assert s1 == s2 and set(s1) == {
        "schema_decision_ledger_entry", "schema_disposition_record",
        "schema_gate_record"}


def test_evidence_registry_paths_repo_relative_posix():
    for ev in _build()["evidence_registry"]:
        if not ev["path"].startswith("schemas.py:registry:"):
            assert not os.path.isabs(ev["path"])
            assert "\\" not in ev["path"] and ":" not in ev["path"]
            assert ".." not in ev["path"]


# ---------------------------------------------------------------------------
# CLI（v3cli approvals build；临时 evidence 树，不碰 out/）
# ---------------------------------------------------------------------------

def _make_evidence_tree(root):
    for _, relpath in approvals.EVIDENCE_FILES:
        p = os.path.join(root, *relpath.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(b"evidence-stub")
    return root


def test_v3cli_approvals_build_e2e(capsys, tmp_path):
    root = _make_evidence_tree(str(tmp_path))
    rc, raw, d = _run_cli(capsys, ["approvals", "--select", "build",
                                   "--root", root])
    assert rc == 0
    assert d["status"] == "ok"
    assert d["approval_count"] == 6
    # stdout 恰为 canonical JSON（byte-exact 判定）
    assert raw.encode("utf-8") == hashing.canonical_json_bytes(d)
    # 主机路径不入产物（--root 的 tmp 绝对路径不得泄漏）
    assert str(tmp_path) not in raw
    # evidence hash 为磁盘实读值
    stub = hashing.sha256_text("evidence-stub")
    assert all(ev["sha256"] == stub for ev in d["evidence_registry"]
               if not ev["path"].startswith("schemas.py:"))


def test_v3cli_approvals_build_missing_evidence_blocked(capsys, tmp_path):
    rc, _, d = _run_cli(capsys, ["approvals", "--select", "build",
                                 "--root", str(tmp_path)])
    assert rc == 2
    assert d["status"] == "blocked"
    assert any("缺失" in e for e in d["errors"])
