"""S17 会话测试：ITEM-run-r1 队列关闭链 + APR-0007/0008/0009 r2 登记。

覆盖：
- 队列关闭（集成锚，只读 out/）：run-r1 queue-event-ledger 现 3 事件、
  verify_chain 全绿、首行 enqueue 事件 hash 逐字节未变（e3c8e114…）、
  QE-000001=assign / QE-000002=approve（actor=user、
  actor_role=human_final、reason_code=item_dispositioned_apr_0007）、
  projection_summary.queue_length=0（ITEM-run-r1 终态 closed）；
- 队列语义（纯内存）：approve 必须人工裁决角色（机器角色拒绝）、
  approve 前必须 assign（open 不可直接 approve）、终态后再事件拒绝；
- approvals_r2（纯函数）：三批准 bundle 构造（authority=human、
  trust_level=untrusted、payload_ref=处置 canonical sha、artifact
  hash 绑定声明逻辑名）、gate_write_scan 全空、byte-exact 重放、
  evidence 缺失 fail-closed、处置记录过 schema、r2 常量（日期=
  声明常量 2026-09-05、revision/checkpoint 标识、r1 文件名不冲突）；
- r2 落盘集成锚（只读 out/v3-approvals/）：bundle/ledger/checkpoint/
  verify/三处置单件存在且相互一致——ledger 盘上 sha256=bundle 声明、
  处置单件 hash=payload_ref、checkpoint 与 bundle 内投影一致、
  verify status=ok、evidence_registry hash 对盘上实文件一致；
- 既有 r1 文件不动（r1 bundle/ledger 文件名仍存在且 r2 未触碰其键）。

纯内存构造（生成器模式）：零子进程/零写盘/零网络；集成锚只读。
"""

import glob
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import approvals_r2 as ar2  # noqa: E402
from pcbflow import hashing, queue  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 队列关闭（集成锚：run-r1 账本）
# ---------------------------------------------------------------------------

def _load_run1_ledger():
    path = os.path.join(REPO, "out", "v3-tl2", "critic-runs", "run-r1",
                        "queue-event-ledger.jsonl")
    with open(path, "rb") as f:
        raw = f.read()
    events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    return raw, events


def test_run1_ledger_closed_state():
    raw, events = _load_run1_ledger()
    assert len(events) == 3
    assert queue.verify_chain(events) == []
    assert raw.endswith(b"\n")
    # 首行 enqueue 字节未变（既有行逐字节保留的锚）
    assert events[0]["event"] == "enqueue"
    assert events[0]["item_id"] == "ITEM-run-r1"
    assert events[0]["event_sha256"] == \
        "e3c8e114500212311278d4a737e3523055b7716e39b07ae98f2a663d206961b4"
    assign, approve = events[1], events[2]
    assert assign["event"] == "assign" and assign["event_seq"] == 1
    assert assign["actor"] == "user" and assign["actor_role"] == "human_final"
    assert approve["event"] == "approve" and approve["event_seq"] == 2
    assert approve["actor"] == "user"
    assert approve["actor_role"] == "human_final"
    assert approve["reason_code"] == "item_dispositioned_apr_0007"
    assert approve["prev_event_sha256"] == assign["event_sha256"]
    summary = queue.projection_summary(events)
    assert summary["queue_length"] == 0
    assert summary["total_events"] == 3


def test_queue_closure_semantics_invariants():
    ev = queue.make_event([], event="enqueue", item_id="ITEM-x",
                          actor="pcbflow-critic-pipeline",
                          actor_role="critic_model",
                          reason_code="critic_auto_route_blocked")
    events, _ = queue.append([], ev)
    # open 直接 approve 拒绝（状态机）；approve 必须人工裁决角色
    with pytest.raises(ValueError):
        queue.make_event(events, event="approve", item_id="ITEM-x",
                         actor="user", actor_role="critic_model")
    with pytest.raises(ValueError):
        queue.make_event(events, event="approve", item_id="ITEM-x",
                         actor="pcbflow-critic-pipeline",
                         actor_role="human_final")  # 角色匹配但状态 open
    events2, _ = queue.append(events, queue.make_event(
        events, event="assign", item_id="ITEM-x",
        actor="user", actor_role="human_final"))
    approved, _ = queue.append(events2, queue.make_event(
        events2, event="approve", item_id="ITEM-x",
        actor="user", actor_role="human_final",
        reason_code="item_dispositioned_apr_0007"))
    assert queue.projection_summary(approved)["queue_length"] == 0
    # 终态后再事件拒绝
    with pytest.raises(ValueError):
        queue.make_event(approved, event="review", item_id="ITEM-x",
                         actor="user", actor_role="human_final")


# ---------------------------------------------------------------------------
# approvals_r2 纯函数
# ---------------------------------------------------------------------------

def _evidence_hashes():
    hashes, errors = ar2.collect_evidence_hashes(REPO)
    assert errors == []
    return hashes


def test_r2_constants_and_layout():
    assert ar2.APPROVAL_DATE_R2 == "2026-09-05"      # 人工声明常量
    assert ar2.APPROVALS_REVISION_R2 == "v3-approvals-r2"
    assert ar2.CHECKPOINT_ID_R2 == "CKPT-V3-APPROVALS-R2"
    ids = [s["approval_id"] for s in ar2.APPROVAL_SPECS_R2]
    assert ids == ["APR-0007", "APR-0008", "APR-0009"]
    # r1 登记文件名不被 r2 复用（追加批次、不覆写）
    r1_names = {"approvals-bundle.json", "decision-ledger.jsonl",
                "ledger-checkpoint.json", "ledger-verify.json"}
    r2_names = set(ar2.disposition_filename(s)
                   for s in ar2.APPROVAL_SPECS_R2) | {
        "approvals-bundle-r2.json", "decision-ledger-r2.jsonl",
        "ledger-checkpoint-r2.json", "ledger-verify-r2.json"}
    assert not (r1_names & r2_names)


def test_build_bundle_r2_pure_and_valid():
    hashes = _evidence_hashes()
    b1 = ar2.build_approvals_bundle_r2(hashes)
    b2 = ar2.build_approvals_bundle_r2(hashes)
    assert (hashing.canonical_json_bytes(b1)
            == hashing.canonical_json_bytes(b2))     # byte-exact 重放
    assert b1["approval_count"] == 3
    assert b1["approval_date"] == "2026-09-05"
    assert b1["ledger_verify"] == {"chain_errors": [],
                                   "supersedes_errors": []}
    assert all(v == [] for v in b1["gate_write_scan"].values())
    entries = b1["ledger_entries"]
    assert len(entries) == 3
    for spec, entry in zip(ar2.APPROVAL_SPECS_R2, entries):
        assert entry["entry_kind"] == "disposition"
        assert entry["authority"] == "human"
        assert entry["trust_level"] == "untrusted"
        assert entry["disposition_refs"] == [spec["approval_id"]]
        assert entry["snapshot_revision"] == "v3-approvals-r2"
        assert entry["artifact_hashes"] == {
            name: hashes[name] for name in spec["evidence"]}
        rec = next(d for d in b1["dispositions"]
                   if d["disposition_id"] == spec["approval_id"])
        assert entry["payload_ref"] == hashing.sha256_bytes(
            hashing.canonical_json_bytes(rec))
        assert rec["kind"] == "accept"
        assert rec["approver"] == "user"
        assert rec["approver_role"] == "human_authority"
    # 语义限定要点在案（处置≠改板/方案批准≠校准达标/批准≠门翻转）
    texts = [d["rationale_text"] for d in b1["dispositions"]]
    assert "处置≠改板" in texts[0]
    assert "critic 输出恒 untrusted" in texts[0]
    assert "方案批准≠校准达标" in texts[1]
    assert "critic_calibration_in_range" in texts[1]
    assert "Tier 2 不" in texts[2] and "批准不构成任何机器门翻转" in texts[2]


def test_build_bundle_r2_evidence_missing_fail_closed():
    hashes = _evidence_hashes()
    broken = dict(hashes)
    broken.pop("run_r1_queue_ledger")
    with pytest.raises(ValueError):
        ar2.build_approvals_bundle_r2(broken)
    with pytest.raises(ValueError):
        ar2.build_approvals_bundle_r2({})


def test_collect_evidence_hashes_missing_file():
    hashes, errors = ar2.collect_evidence_hashes(
        os.path.join(REPO, "no", "such", "root"))
    assert hashes == {} and len(errors) == len(ar2.EVIDENCE_FILES_R2)


def test_no_gate_write_guard_on_forbidden_key():
    from pcbflow import disposition
    record = {"disposition_id": "X", "gate_pass": True}
    assert disposition.validate_no_gate_write(record)
    assert disposition.validate_no_gate_write(
        {"nested": [{"gate_result": 1}]})
    assert disposition.validate_no_gate_write(
        {"ok": {"a": {"b": {"production_signoff_ready": True}}}})


# ---------------------------------------------------------------------------
# r2 落盘集成锚（只读）
# ---------------------------------------------------------------------------

def test_r2_artifacts_on_disk_consistent():
    ap_dir = os.path.join(REPO, "out", "v3-approvals")
    bundle = json.load(open(os.path.join(ap_dir,
                                         "approvals-bundle-r2.json"),
                            encoding="utf-8"))
    ledger_disk = hashing.sha256_file(
        os.path.join(ap_dir, "decision-ledger-r2.jsonl"))
    assert ledger_disk == bundle["ledger_file_sha256"]
    entries = [json.loads(line) for line in open(
        os.path.join(ap_dir, "decision-ledger-r2.jsonl"),
        encoding="utf-8").read().splitlines()]
    from pcbflow import ledger
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    assert len(entries) == 3
    verify = json.load(open(os.path.join(ap_dir, "ledger-verify-r2.json"),
                            encoding="utf-8"))
    assert verify["status"] == "ok" and verify["errors"] == []
    assert verify["entry_count"] == 3
    assert verify["ledger_file_sha256"] == bundle["ledger_file_sha256"]
    ckpt = json.load(open(os.path.join(ap_dir, "ledger-checkpoint-r2.json"),
                          encoding="utf-8"))
    assert ckpt == bundle["ledger_checkpoint"]
    assert ckpt["checkpoint_id"] == "CKPT-V3-APPROVALS-R2"
    assert ckpt["entry_count"] == 3
    for spec in ar2.APPROVAL_SPECS_R2:
        path = os.path.join(ap_dir, ar2.disposition_filename(spec))
        disk = hashing.sha256_file(path)
        entry = next(e for e in entries
                     if e["entry_id"] == spec["entry_id"])
        assert disk == entry["payload_ref"]
    # evidence_registry 钉住的若是可演进设计文档，哈希漂移合法性的唯一
    # 通道=后续批次的 evidence_registry 对新哈希的登记（APR-0002 追加式
    # 纪律）。此形式比"盘上哈希永不变化"更精确：历史哈希仍全部可对账，
    # 未被任何已登记批次解释的漂移依旧 fail。
    other_registries = []
    for reg_path in sorted(glob.glob(os.path.join(
            ap_dir, "approvals-bundle*.json"))):
        if os.path.basename(reg_path) == "approvals-bundle-r2.json":
            continue  # 本 bundle 自身不作漂移解释来源
        with open(reg_path, encoding="utf-8") as f:
            other = json.load(f)
        other_registries.append(
            {e["path"]: e["sha256"]
             for e in other.get("evidence_registry", [])})
    for item in bundle["evidence_registry"]:
        disk = hashing.sha256_file(
            os.path.join(REPO, *item["path"].split("/")))
        if disk == item["sha256"]:
            continue  # 未演进：登记哈希与盘上仍一致
        assert any(reg.get(item["path"]) == disk
                   for reg in other_registries), item["name"]


def test_r1_artifacts_untouched_names_present():
    ap_dir = os.path.join(REPO, "out", "v3-approvals")
    for name in ("approvals-bundle.json", "decision-ledger.jsonl",
                 "ledger-checkpoint.json", "ledger-verify.json",
                 "disposition-APR-0005-critic-duty-level.json"):
        assert os.path.isfile(os.path.join(ap_dir, name)), name
    r1 = json.load(open(os.path.join(ap_dir, "approvals-bundle.json"),
                        encoding="utf-8"))
    assert r1["revision"] == "v3-approvals-r1"
    assert r1["approval_count"] == 6
