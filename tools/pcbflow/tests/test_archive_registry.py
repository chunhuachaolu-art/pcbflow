"""S13-ARCHIVE TD7 线收档登记测试（disposition 域语义+链完整性+确定性）。

2026-09-04 用户裁决「TD7 线收档并总结经验」的登记红线：
  - human authority 只出现在 disposition 类 entry 且恒 untrusted
    （处置是决定不是事实，validator 白名单强制）；
  - 收档处置不得携带门写禁区键（validate_no_gate_write），不重算不改写
    任何机器门与冻结产物（TD7-QUAL-G pass 记录/TL-4-G fail/TL-3-G1
    fail/TL-2 not reached 全部冻结只读）；
  - kind=reject 非 waive：schema enum 内唯一的关线语义（archived/
    not_adopted/closed_by_archive 决策词由 decision_summary 与
    rationale_code/text 承载），不解除任何机器谓词；
  - evidence 指针=磁盘实读 sha256（缺一 fail-closed 拒绝构造）；
  - 生成器纪律：同输入 byte-exact、无 wall-clock（日期为人工声明常量）。

依赖 cwd=pcbflow 根（既有测试约定）；库级用合成 hash，CLI 级用临时
evidence 树，不触碰 out/ 冻结产物。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import archive, hashing, ledger, v3cli
from pcbflow import disposition as disposition_mod


def _fake_hashes():
    return {name: hashing.sha256_text(name)
            for name, _ in archive.EVIDENCE_FILES}


def _build():
    return archive.build_archive_bundle(_fake_hashes())


def _run_cli(capsys, argv):
    rc = v3cli.main(argv)
    out = capsys.readouterr().out
    return rc, out, json.loads(out)


# ---------------------------------------------------------------------------
# 库级：结构与语义
# ---------------------------------------------------------------------------

def test_bundle_four_dispositions_chain_valid():
    bundle = _build()
    assert bundle["disposition_count"] == 4
    assert [d["disposition_id"] for d in bundle["dispositions"]] == \
        [s["archive_id"] for s in archive.ARCHIVE_SPECS]
    assert bundle["ledger_verify"] == {"chain_errors": [],
                                       "supersedes_errors": []}
    assert bundle["archive_date"] == "2026-09-04"
    assert bundle["actor"] == {"actor": "user",
                               "actor_role": "human_authority"}
    assert bundle["decision_summary"] == {
        "ARC-0001": "archived",
        "ARC-0002": "not_adopted",
        "ARC-0003": "closed_by_archive",
        "ARC-0004": "closed_by_archive"}


def test_human_authority_disposition_untrusted_only():
    for e in _build()["ledger_entries"]:
        assert e["entry_kind"] == "disposition"
        assert e["authority"] == "human"
        assert e["trust_level"] == "untrusted"   # 处置恒不可升级
        assert e["actor"] == "user"
        assert e["actor_role"] == "human_authority"
        assert e["snapshot_revision"] == "v3-archive-r1"


def test_no_gate_write_in_any_disposition():
    bundle = _build()
    for d in bundle["dispositions"]:
        assert disposition_mod.validate_no_gate_write(d) == []
    assert set(map(tuple, bundle["gate_write_scan"].values())) == {()}


def test_archive_dispositions_reject_kind_not_waiver():
    # 收档走 reject（schema enum 内唯一关线语义）；非 waive=无豁免语义
    for d in _build()["dispositions"]:
        assert d["kind"] == "reject"
        assert disposition_mod.check_waiver_policy(d, {}) == []


def test_missing_evidence_fail_closed():
    hashes = _fake_hashes()
    hashes.pop("s12_quality_matrix")
    with pytest.raises(ValueError):
        archive.build_archive_bundle(hashes)


def test_frozen_gate_status_note_present():
    note = _build()["frozen_machine_gate_status"]
    assert "TD7-QUAL-G" in note and "冻结只读" in note
    assert "TL-4-G fail" in note and "维持" in note
    assert "TL-3-G1 fail 维持" in note
    assert "not reached 维持" in note
    assert "kind=reject 非 waive" in note


def test_semantics_recorded_per_disposition():
    texts = {d["disposition_id"]: d["rationale_text"]
             for d in _build()["dispositions"]}
    for text in texts.values():
        assert "2026-09-04" in text        # 收档日期（人工声明常量）
    # ARC-0001：关线 + 资格引用 + 质量结论 + 重开条件
    t1 = texts["ARC-0001"]
    assert archive.TD7_QUAL_GATE_CORE_HASH16 in t1
    assert "9/9 次运行全部被验证链拒收" in t1
    assert "类宽×0.75" in t1 and "死锁" in t1
    assert "不得引用为现行外部执行/布线能力" in t1
    assert "重走 qualification" in t1 and "不得沿用本资格结论" in t1
    # ARC-0002：not_adopted + 锁零改动
    t2 = texts["ARC-0002"]
    assert archive.TOOLCHAIN_LOCK_SHA256_16 in t2
    assert "零改动" in t2 and "optional/null" in t2
    assert "不因重开而复活" in t2
    # ARC-0003/0004：closed_by_archive + 不预支结论
    assert "closed_by_archive" in texts["ARC-0003"].replace(
        "closed_by_archive：", "closed_by_archive")  # 决策词在场
    assert "不再议" in texts["ARC-0003"]
    assert "门语义零改动" in texts["ARC-0003"]
    assert "不追" in texts["ARC-0004"]
    assert "不构成对 v2.4.1 的任何评估结论" in texts["ARC-0004"]
    assert "新包重走 qualification" in texts["ARC-0004"]


def test_reopen_condition_recorded_in_bundle():
    bundle = _build()
    assert "重走 qualification" in bundle["reopen_condition"]
    assert "不得沿用" in bundle["reopen_condition"]


# ---------------------------------------------------------------------------
# 链与落盘字节口径
# ---------------------------------------------------------------------------

def test_ledger_jsonl_round_trip_verifies():
    bundle = _build()
    data = archive.ledger_file_bytes(bundle["ledger_entries"])
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


def test_artifact_hashes_bind_declared_evidence_only():
    bundle = _build()
    hashes = _fake_hashes()
    by_id = {e["disposition_refs"][0]: e
             for e in bundle["ledger_entries"]}
    for spec in archive.ARCHIVE_SPECS:
        assert by_id[spec["archive_id"]]["artifact_hashes"] == \
            {name: hashes[name] for name in spec["evidence"]}
    # toolchain_lock 提案处置必须绑定锁文件与提案双证据（零改动可复核）
    assert set(by_id["ARC-0002"]["artifact_hashes"]) == \
        {"td7_toolchain_lock_proposal", "toolchain_lock"}


def test_deterministic_byte_exact():
    a = hashing.canonical_json_bytes(_build())
    b = hashing.canonical_json_bytes(_build())
    assert a == b


def test_evidence_registry_paths_repo_relative_posix():
    for ev in _build()["evidence_registry"]:
        assert not os.path.isabs(ev["path"])
        assert "\\" not in ev["path"] and ":" not in ev["path"]
        assert ".." not in ev["path"]


# ---------------------------------------------------------------------------
# CLI（v3cli archive build；临时 evidence 树，不碰 out/）
# ---------------------------------------------------------------------------

def _make_evidence_tree(root):
    for _, relpath in archive.EVIDENCE_FILES:
        p = os.path.join(root, *relpath.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(b"evidence-stub")
    return root


def test_v3cli_archive_build_e2e(capsys, tmp_path):
    root = _make_evidence_tree(str(tmp_path))
    rc, raw, d = _run_cli(capsys, ["archive", "--select", "build",
                                    "--root", root])
    assert rc == 0
    assert d["status"] == "ok"
    assert d["disposition_count"] == 4
    # stdout 恰为 canonical JSON（byte-exact 判定）
    assert raw.encode("utf-8") == hashing.canonical_json_bytes(d)
    # 主机路径不入产物（--root 的 tmp 绝对路径不得泄漏）
    assert str(tmp_path) not in raw
    # evidence hash 为磁盘实读值
    stub = hashing.sha256_text("evidence-stub")
    assert all(ev["sha256"] == stub for ev in d["evidence_registry"])


def test_v3cli_archive_build_missing_evidence_blocked(capsys, tmp_path):
    rc, _, d = _run_cli(capsys, ["archive", "--select", "build",
                                 "--root", str(tmp_path)])
    assert rc == 2
    assert d["status"] == "blocked"
    assert any("缺失" in e for e in d["errors"])


def test_disposition_filename_convention():
    spec = archive.ARCHIVE_SPECS[0]
    assert archive.disposition_filename(spec) == \
        "disposition-ARC-0001-td7-line-archive.json"
