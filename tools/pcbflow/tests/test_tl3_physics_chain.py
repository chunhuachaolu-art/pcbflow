"""TL-3 required 项实配编排测试（smoke-4l PHY-IMP-1 全链；SPEC-v3.0 §3 TL-3）。

依赖 cwd=pcbflow 根（既有测试约定）。使用真实 profiles/smoke-4l 合同输入：
profile.json + inputs/physics-evidence.json（合成 smoke 级证据，如实标注
synthetic/datasheet_derived）。断言的是红线行为：
  - coverage=100% 不等于通过（coverage 完整 + 项 status=pass →
    physics_gate 仍 fail：uncertainty 超容差 + 无 approval 处置）；
  - screening 级证据满足不了 required 级 authority（predicate 如实 False）；
  - judge_pre/post、ledger 三事件、gate-record 机器可复核、hash 绑定；
  - 负向四路径：缺证据/stale/coverage<100% → blocked；authority 不满足 →
    fail（非 pass）；缺处置不能生成 waiver；
  - 生成器纪律：stdout canonical JSON byte-exact、无 wall-clock、无主机路径。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import hashing, physics, physics_chain, schemas, v3cli
from pcbflow import disposition as disposition_mod
from pcbflow import gate as gate_mod
from pcbflow import judge as judge_mod
from pcbflow import ledger as ledger_mod

PROFILE_DIR = os.path.join("profiles", "smoke-4l")
PROFILE_PATH = os.path.join(PROFILE_DIR, "profile.json")
EVIDENCE_PATH = os.path.join(PROFILE_DIR, "inputs", "physics-evidence.json")
MANIFEST_PATH = os.path.join(PROFILE_DIR, "manifest.json")

ARGV_CHAIN = ["physics", "--select", "required-chain",
              "--profile", PROFILE_PATH,
              "--evidence", EVIDENCE_PATH,
              "--snapshot-revision", "smoke-r1"]


def _load_inputs():
    profile = json.load(open(PROFILE_PATH, encoding="utf-8"))
    evidence = json.load(open(EVIDENCE_PATH, encoding="utf-8"))
    hashes, errors = v3cli._chain_input_hashes(MANIFEST_PATH, EVIDENCE_PATH)
    assert errors == []
    return profile, evidence, hashes


def _build():
    profile, evidence, hashes = _load_inputs()
    return physics_chain.build_chain(
        profile, evidence, hashes, snapshot_revision="smoke-r1",
        evaluator={"name": "pcbflow-v3-physics-chain", "version": "1.0",
                   "code_sha256": hashing.sha256_file(
                       physics_chain.__file__)})


# ---------------------------------------------------------------------------
# IPC-2141 一阶计算器
# ---------------------------------------------------------------------------

def test_ipc2141_value_and_validity_domain():
    geom = dict(trace_width_mm=0.30, trace_gap_mm=0.20,
                dielectric_thickness_mm=0.21, copper_thickness_mm=0.035,
                epsilon_r=4.2)
    value = physics.ipc2141_first_order_diff_ohm(**geom)
    assert value == pytest.approx(90.107, abs=0.01)
    assert physics.ipc2141_first_order_validity(**geom) is True
    # w/h 超出公式适用域 → validity False（fail-closed）
    wide = dict(geom, trace_width_mm=1.0)   # w/h ≈ 4.76
    assert physics.ipc2141_first_order_validity(**wide) is False
    with pytest.raises(ValueError):
        physics.ipc2141_first_order_diff_ohm(**dict(geom, epsilon_r=0))


# ---------------------------------------------------------------------------
# 证据 bundle 校验（合成标注强制）
# ---------------------------------------------------------------------------

def test_evidence_bundle_rejects_non_synthetic_and_wrong_grade():
    _, evidence, _ = _load_inputs()
    assert physics_chain.validate_evidence_bundle(evidence) == []
    tampered = json.loads(json.dumps(evidence))
    tampered["provenance"]["source"] = "lab_measurement"
    errs = physics_chain.validate_evidence_bundle(tampered)
    assert any("synthetic" in e for e in errs)
    sim = json.loads(json.dumps(evidence))
    sim["items"][0]["authority"] = "openems"
    errs = physics_chain.validate_evidence_bundle(sim)
    assert any("screening" in e for e in errs)
    profile, _, hashes = _load_inputs()
    with pytest.raises(ValueError):
        physics_chain.derive_items(profile, {
            "schema_version": "3.0",
            "artifact_kind": "physics_evidence_bundle",
            "project_id": "smoke-4l", "profile_id": "smoke-4l",
            "provenance": {"source": "synthetic"}, "items": []}, hashes)
    broken = {"schema_version": "3.0"}
    assert physics_chain.validate_evidence_bundle(broken)


# ---------------------------------------------------------------------------
# 证据项推导（八布尔门机器计算）
# ---------------------------------------------------------------------------

def test_derive_items_booleans_all_machine_computed():
    profile, evidence, hashes = _load_inputs()
    items = physics_chain.derive_items(profile, evidence, hashes)
    assert len(items) == 1
    item = items[0]
    assert item["item_id"] == "PHY-IMP-1"
    assert item["track"] == "physics_screening"
    assert item["status"] == "pass"                      # 筛查值在带内
    assert item["required_scope_defined"] is True
    assert item["coverage_complete"] is True
    assert item["input_model_complete"] is True
    assert item["executed"] is True
    assert item["convergence_or_validity_pass"] is True
    assert item["limit_pass"] is True                    # 90.1 ∈ [85,95]
    assert item["uncertainty_acceptable"] is False       # 9.0 > 5.0
    assert item["external_approval_present"] is False    # 人工批准挂起
    assert item["authority"] == "datasheet_derived"
    assert item["fidelity"] == "screening"
    assert item["measurement_convention"] == "IPC-2141-first-order"
    assert set(item["input_hashes"]) == {
        "stackup", "constraints", "board", "netlist",
        "physics_evidence", "profile"}
    assert item["input_hashes"]["stackup"] == hashing.sha256_file(
        os.path.join(PROFILE_DIR, "inputs", "stackup.json"))
    assert 85.0 <= item["measured_value"] <= 95.0
    # 合成标注透传：绝不冒充真实仿真/实测
    assert "synthetic" in item["note"] and "非 lab_measurement" in item["note"]


def test_derive_items_input_gap_breaks_input_model_complete():
    profile, evidence, hashes = _load_inputs()
    broken = dict(hashes)
    del broken["stackup"]
    item = physics_chain.derive_items(profile, evidence, broken)[0]
    assert item["input_model_complete"] is False
    assert "stackup" not in item["input_hashes"]


def test_derive_items_stale_freshness():
    profile, evidence, hashes = _load_inputs()
    item = physics_chain.derive_items(profile, evidence, hashes,
                                      freshness="stale")[0]
    assert item["status"] == "stale"


# ---------------------------------------------------------------------------
# 全链：report/coverage/judge/ledger/gate
# ---------------------------------------------------------------------------

def test_chain_report_fail_with_full_coverage():
    bundle = _build()
    report = bundle["physics_report"]
    assert schemas.is_valid("physics_report", report)
    assert report["physics_gate"] == "fail"
    assert report["gate_failure_codes"] == ["no_approval",
                                            "uncertainty_fail"]
    coverage = bundle["physics_coverage"]
    assert schemas.is_valid("physics_coverage", coverage)
    assert coverage["coverage_complete"] is True          # 报告齐
    assert coverage["missing_scope"] == []
    assert bundle["physics_gate"]["coverage"] == {
        "covered": 1, "complete": True}
    # coverage=100% 不等于通过：门仍 fail（必要非充分）
    assert report["physics_gate"] != "pass"


def test_chain_judge_pre_ok_post_fail_on_physics_status():
    bundle = _build()
    assert bundle["judge_pre_evaluation"]["pre_ok"] is True
    post = bundle["judge_post"]
    assert post["physics_status"] == "fail"
    assert schemas.is_valid("judge_post_record", post)
    ev = bundle["judge_post_evaluation"]
    assert ev["post_ok"] is False
    assert any("physics_status" in f for f in ev["failed"])
    # 双阶段绑定：post.pre_record_ref 落在 pre 记录 canonical hash
    assert post["pre_record_ref"] == judge_mod.pre_record_sha256(
        bundle["judge_pre"])
    assert judge_mod.adoption_check(
        {judge_mod.pre_record_sha256(bundle["judge_pre"])}, post) == []


def test_chain_ledger_three_events_and_checkpoint():
    bundle = _build()
    entries = bundle["ledger_entries"]
    assert [e["entry_kind"] for e in entries] == [
        "judge_pre", "judge_post", "gate"]
    assert [e["entry_id"] for e in entries] == [
        "TL3-E-0001", "TL3-E-0002", "TL3-E-0003"]
    assert ledger_mod.verify_chain(entries) == []
    assert ledger_mod.verify_supersedes(entries) == []
    assert ledger_mod.verify_against_checkpoint(
        entries, bundle["ledger_checkpoint"]) == []
    # 账本文件字节 hash = 单行 JSON/条 + 换行（v3cli ledger append 口径）
    assert bundle["ledger_file_sha256"] == hashing.sha256_bytes(
        physics_chain.ledger_file_bytes(entries))
    data = physics_chain.ledger_file_bytes(entries).decode("utf-8")
    assert [json.loads(line) for line in data.splitlines()] == entries
    # gate 输入绑定的 ledger 前缀 = judge 两事件（避免自引循环）
    assert bundle["ledger_prefix_sha256"] == hashing.sha256_bytes(
        physics_chain.ledger_file_bytes(entries[:2]))


def test_chain_gate_record_fail_with_evidence_bound_predicates():
    bundle = _build()
    record = bundle["gate_record"]
    assert record["gate_kind"] == "physics"
    assert record["result"] == "fail"
    assert record["failure_codes"] == [
        "predicate_failed:required_uncertainty_within_tolerance",
        "predicate_failed:required_grade_authority_satisfied",
        "predicate_failed:required_scope_approved",
        "predicate_failed:physics_gate_pass",
    ]
    assert bundle["gate_verify_errors"] == []
    assert gate_mod.verify_gate_record(record) == []
    assert len(bundle["gate_core_hash"]) == 64
    # 输入 hash 绑定可复核：physics_report 输入 = canonical bytes sha
    inp = {i["artifact_id"]: i["sha256"] for i in record["inputs"]}
    assert inp["physics_report"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(bundle["physics_report"]))
    assert inp["physics_coverage"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(bundle["physics_coverage"]))
    assert inp["profile"] == hashing.sha256_file(PROFILE_PATH)
    # 全部 predicate 带证据字符串（True/False 断言均需证据）
    assert all(p.get("evidence") for p in record["required_predicates"])
    pred = {p["id"]: p["value"] for p in record["required_predicates"]}
    assert pred["physics_required_scope_declared"] is True
    assert pred["required_coverage_complete"] is True
    assert pred["required_uncertainty_within_tolerance"] is False
    assert pred["required_grade_authority_satisfied"] is False
    assert pred["required_scope_approved"] is False    # 人工批准挂起
    assert pred["physics_gate_pass"] is False
    # evaluation_metadata 三字段恒 null（无 wall-clock）
    assert record["evaluation_metadata"] == {
        "evaluated_at": None, "host": None, "elapsed_s": None}


def test_chain_notes_disclaim_production():
    bundle = _build()
    text = json.dumps(bundle, ensure_ascii=False)
    assert "不构成物理签核" in text
    assert bundle["evidence_provenance"]["source"] == "synthetic"


# ---------------------------------------------------------------------------
# 负向 witness 四路径 + waiver 不可生成
# ---------------------------------------------------------------------------

def test_negative_witnesses_fail_closed_paths():
    bundle = _build()
    w = bundle["negative_witnesses"]
    g1 = w["missing_required_evidence"]["gate"]
    assert g1["physics_gate"] == "blocked"
    assert "missing_report" in g1["failure_codes"]
    g2 = w["stale_input"]["gate"]
    assert g2["physics_gate"] == "blocked"
    assert "status_stale" in g2["failure_codes"]
    g3 = w["coverage_incomplete"]["gate"]
    assert g3["physics_gate"] == "blocked"
    assert "missing_report" in g3["failure_codes"]
    assert g3["coverage"]["complete"] is False
    assert w["coverage_incomplete"]["coverage"]["missing_scope"] == [
        "PHY-IMP-9"]
    g4 = w["authority_below_required_grade"]["gate"]
    assert g4["physics_gate"] == "fail"                  # 非 pass
    assert "authority_mismatch" in g4["failure_codes"]
    assert w["authority_below_required_grade"][
        "designated_backend_ok_openems"] is False


def test_waiver_cannot_be_generated_without_disposition():
    bundle = _build()
    w = bundle["negative_witnesses"]["waiver_cannot_be_generated"]
    assert w["waiver_generated"] is False
    assert w["errors"]                                   # 无 policy ⇒ 全拒
    assert w["gate_write_scan"] == []                    # 且不写门
    # 即使给出 policy，PHY-IMP-1 不在 waivable 清单 → 不可豁免（L4）
    attempt = disposition_mod.build_disposition(
        disposition_id="DSP-TL3-WITNESS-2", fact_refs=["PHY-IMP-1"],
        kind="waive", scope="physics",
        rationale_code="engineering_judgement", approver="human-pending",
        approver_role="engineer",
        waiver_policy_ref="policy-tl3-smoke", expiry="next-revision")
    errs = disposition_mod.check_waiver_policy(attempt, {
        "waivable_check_ids": ["C-1001"],                # physics 不在列
        "allowed_reason_codes": ["engineering_judgement"],
        "allowed_approver_roles": ["engineer"]})
    assert any("不可豁免" in e for e in errs)


# ---------------------------------------------------------------------------
# v3cli E2E + 生成器纪律
# ---------------------------------------------------------------------------

def _run_cli(capsys, argv):
    rc = v3cli.main(argv)
    out = capsys.readouterr().out
    return rc, out, json.loads(out)


def test_v3cli_required_chain_e2e(capsys):
    rc, raw, d = _run_cli(capsys, ARGV_CHAIN)
    assert rc == 1                              # gate=fail → exit 1（如实）
    assert d["command"] == "v3-physics"
    assert d["select"] == "required-chain"
    assert d["status"] == "failed"
    assert d["physics_gate"]["physics_gate"] == "fail"
    assert d["gate_record"]["result"] == "fail"
    assert d["ledger_verify"] == {"chain_errors": [],
                                  "supersedes_errors": []}
    assert d["gate_verify_errors"] == []
    # evaluator 绑定判定代码版本（gate 人工不可直写）
    assert d["gate_evaluator_bound"]["code_sha256"] == \
        hashing.sha256_file(physics_chain.__file__)


def test_v3cli_required_chain_byte_exact_and_clean(capsys):
    _, raw1, _ = _run_cli(capsys, ARGV_CHAIN)
    _, raw2, _ = _run_cli(capsys, ARGV_CHAIN)
    assert raw1 == raw2                          # 重跑 byte-exact
    assert raw1 == hashing.canonical_json_bytes(
        json.loads(raw1)).decode("utf-8")        # stdout 即 canonical JSON
    assert "C:\\\\" not in raw1                  # 无主机路径
    assert "evaluated_at" in raw1                # 元数据字段在场
    assert json.loads(raw1)["gate_record"][
        "evaluation_metadata"]["evaluated_at"] is None   # 且恒 null


def test_v3cli_required_chain_missing_input_blocked(capsys):
    rc, _, d = _run_cli(capsys, ["physics", "--select", "required-chain",
                                 "--profile", PROFILE_PATH,
                                 "--evidence",
                                 "profiles/smoke-4l/inputs/nope.json"])
    assert rc == 2                               # 输入缺失 → blocked
    assert d["status"] == "blocked"
    assert any("physics_evidence" in e for e in d["errors"])


def test_v3cli_required_chain_needs_both_args(capsys):
    rc, _, d = _run_cli(capsys, ["physics", "--select", "required-chain"])
    assert rc == 4 or rc == 1
    assert d["status"] == "failed"


def test_v3cli_physics_gate_select_unchanged(capsys, tmp_path):
    """既有 gate select 合同不回归：对既有 report 评估、恒 status=ok。"""
    report = {"schema_version": "3.0", "project_id": "p", "profile_id": "q",
              "snapshot_revision": "r", "items": [], "physics_gate":
              "not_required"}
    p = tmp_path / "report.json"
    p.write_text(json.dumps(report), encoding="utf-8")
    rc, _, d = _run_cli(capsys, ["physics", "--report", str(p)])
    assert rc == 0 and d["status"] == "ok"
    assert d["physics_gate"] == "not_required"
