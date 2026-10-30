"""P1-C 会话测试：TL-6 健康度重投影 v3（指标语义拆分更正）。

覆盖：
- 处置完成率（流程指标）：2 run 全处置 → 1.0（2/2）、definition 含
  「流程指标」且声明不表示/不代理任何旗标判断正确性、hash mismatch →
  blocked、分母 0 → not_available；
- 判断一致率（质量指标）：not_available、denominator=0、value/numerator
  为 None（不冒充数值）、reason 命中「逐旗标」、旗标计数 aux+校准侧实测
  分列（不混写）；
- build_projection_v3 指标集校验（缺失/未知 → ValueError）；
- gate_predicates 对 v3 最小载荷四谓词全绿（证据指针指向真实在盘文件，
  hash=盘上实测注入）；
- readiness_matrix_v3：9 行、TL-2 note 含「流程指标」、signoff=false、
  缺证据 raise；
- open_production_blockers_v3：BL-4 detail 补「队列闭合≠旗标正确性结论」、
  BL-1..3 与其余字段零变化；
- metric-correction-note 构造函数：v2 冻结锚 990bbf98、零门翻转声明、
  锚不符 → ValueError；
- v1/v2 函数行为不变的冒烟（project_critic_agreement_v2 对同参输入仍产出
  与 v2 冻结件同构值；v1 身份常量/矩阵语义不变）；
- 语料分母 v3（corpus-r2-r1 并入）：四库实测 total=137、显式 split 键
  （train_val_candidate/holdout_pool）诚实分列、real_profiles_in_domain=37
  沿用、fail-closed 对账（合计不符/键不在域 → ValueError）；
- 集成锚：真实 out/ 实况（只读）——s23 编排重建（四库分母新口径）与盘上
  四产物 byte-exact 对账（2026-09-21 corpus by_dataset 收尾件：s23 main()
  已落盘重生成四库 137 口径；v1/v2 六冻结件不受影响）、v1/v2 冻结件 hash
  先验断言（防覆写）。

纯内存构造（生成器模式）：零子进程/零网络；集成锚仅只读 out/ 与
datasets/（corpus-r2-r1 manifest 经 s23 实测装配）。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing, health_projection as hp  # noqa: E402
from pcbflow import queue as queue_mod  # noqa: E402

_REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 证据指针使用的真实在盘文件（只读）——hash 一律盘上实测注入
_REAL_EVIDENCE_PATHS = (
    "out/v3-tl2/critic-runs/run-r1/critic-run-record-CR-run-r1.json",
    "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json",
    "out/v3-tl2/critic-runs/run-r2/critic-run-record-CR-run-r2.json",
    "out/v3-approvals/disposition-APR-0010-item-run-r2-disposition.json",
    "out/v3-tl2/critic-runs/run-r1/queue-event-ledger.jsonl",
    "out/v3-tl2/critic-runs/run-r2/queue-event-ledger.jsonl",
    "out/v3-tl0/gate-record-smoke-2l.json",
    "out/v3-tl0/gate-record-smoke-4l.json",
    "out/v3-tl1/gate-record.json",
    "out/v3-tl3/gate-record.json",
    "out/v3-tl3/physics-coverage.json",
    "out/v3-tl4/gate-record-tl4-v2-smoke-2l.json",
    "out/v3-tl4/gate-record-tl4-v2-smoke-4l.json",
    "out/v3-tl4/proposal-patch-smoke-2l.json",
    "out/v3-tl4/proposal-patch-smoke-4l.json",
    "out/v3-approvals/disposition-APR-0004-tl4-adoption-disposition.json",
    "out/v3-tl5/gate-record-tl5-v4.json",
    "out/v3-tl5/dataset-manifest-kicad-demos-r2.json",
    "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json",
    "out/v3-td7/gate-record-td7.json",
    "out/v3-archive/disposition-ARC-0001-td7-line-archive.json",
    "out/v3-archive/disposition-ARC-0002-toolchain-lock-proposal.json",
    "out/v3-archive/disposition-ARC-0003-d20-batch-gate-semantics.json",
    "out/v3-archive/disposition-ARC-0004-freerouting-v241-upgrade.json",
)


def _sha(seed: str) -> str:
    return hashing.sha256_text(seed)


def _measured_real() -> dict:
    """盘上实测 hash（P4 证据对账注入；读-only）。"""
    return {p: hashing.sha256_file(os.path.join(_REPO_DIR, p))
            for p in _REAL_EVIDENCE_PATHS}


def _ev(events, *, event, item_id, seq, actor="critic-pipeline",
        actor_role="critic_model", reason=None, critic_ref=None):
    refs = {"critic_ref": critic_ref} if critic_ref else None
    ev = queue_mod.make_event(
        events, event=event, item_id=item_id, actor=actor,
        actor_role=actor_role, reason_code=reason, refs=refs)
    events.append(ev)
    return ev


def _closed_ledger(item_id, ref_seed):
    events = []
    _ev(events, event="enqueue", item_id=item_id, seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha(ref_seed))
    _ev(events, event="assign", item_id=item_id, seq=1)
    _ev(events, event="approve", item_id=item_id, seq=2,
        actor="human-final", actor_role="human_final")
    return events


def _critic_run(run_id, ref_seed, flags, abstain, boards,
                hashes_match=True):
    return {"run_id": run_id, "critic_status": "executed",
            "input_hashes_match": hashes_match, "critic_ref": _sha(ref_seed),
            "in_calibrated_range": False, "flags_total": flags,
            "abstain_count": abstain, "board_flag_counts": boards}


_REC1 = "out/v3-tl2/critic-runs/run-r1/critic-run-record-CR-run-r1.json"
_APR7 = "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json"
_REC2 = "out/v3-tl2/critic-runs/run-r2/critic-run-record-CR-run-r2.json"
_APR10 = "out/v3-approvals/disposition-APR-0010-item-run-r2-disposition.json"
_LEDGER1 = "out/v3-tl2/critic-runs/run-r1/queue-event-ledger.jsonl"
_LEDGER2 = "out/v3-tl2/critic-runs/run-r2/queue-event-ledger.jsonl"


def _two_run_v3_fixture(hashes_match=(True, True), measured=None):
    """v3 双 run 夹具：不携带 human_supports_flags（该推导正是 v2 语义
    混用的缺陷源，v3 指标不消费它）；evidence 指向真实在盘文件。"""
    events = (_closed_ledger("ITEM-r1", "rec1")
              + _closed_ledger("ITEM-r2", "rec2"))
    critic_runs = [
        _critic_run("CR-run-r1", "rec1", 7, 1,
                    {"bm11": 5, "launchxl": 2}, hashes_match[0]),
        _critic_run("CR-run-r2", "rec2", 12, 5,
                    {"data-manager": 4, "flatpack2": 3,
                     "karabas-reva": 3, "karabas-wifi": 2}, hashes_match[1]),
    ]
    m = measured if measured is not None else {
        _REC1: _sha("rec1"), _APR7: _sha("apr7"),
        _REC2: _sha("rec2"), _APR10: _sha("apr10")}
    record_evidence = [
        {"run_id": "CR-run-r1", "path": _REC1, "sha256": m[_REC1]},
        {"run_id": "APR-0007", "path": _APR7, "sha256": m[_APR7]},
        {"run_id": "CR-run-r2", "path": _REC2, "sha256": m[_REC2]},
        {"run_id": "APR-0010", "path": _APR10, "sha256": m[_APR10]},
    ]
    calibration_observation = [
        {"source_id": "calibration-metric-v1", "path": "out/x/cal1.json",
         "sha256": _sha("cal1"), "sha256_8": _sha("cal1")[:8],
         "gt_recall": 0.25, "reader_precision_vs_seed_gt": 0.2,
         "advisory_note": "校准域种子实测（非门）"},
        {"source_id": "calibration-metric-v2", "path": "out/x/cal2.json",
         "sha256": _sha("cal2"), "sha256_8": _sha("cal2")[:8],
         "gt_recall": 0.25, "reader_precision_vs_seed_gt": 0.142857,
         "advisory_note": "校准域种子实测（非门）"},
    ]
    return events, critic_runs, record_evidence, calibration_observation


# ---------------------------------------------------------------------------
# 指标：处置完成率（流程）
# ---------------------------------------------------------------------------

def test_disposition_completion_two_runs_all_disposed():
    events, runs, evidence, _cal = _two_run_v3_fixture()
    m = hp.project_critic_disposition_completion(
        runs, events, record_evidence=evidence)
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (2, 2, 1.0)
    assert m["revision"] == hp.PROJECTION_REVISION_V3
    assert m["metric_id"] == "critic_disposition_completion_rate"
    # definition 含「流程指标」字样，并显式否认旗标判断正确性语义
    assert "流程指标" in m["definition"]
    assert "不表示、不代理任何旗标判断正确性" in m["definition"]
    # 九描述字段齐全 + 基线诚实标注（拆分新增指标无前值可作基线）
    for k in hp.DESCRIPTOR_KEYS:
        assert k in m
    assert m["baseline"] is None
    assert "不构成基线" in m["baseline_basis"]
    assert "语义混用值" in m["baseline_basis"]
    aux = m["aux"]
    assert aux["metric_kind"] == "process"
    assert aux["runs_total"] == 2 and aux["runs_executed_valid"] == 2
    assert aux["runs_with_disposition_terminal"] == 2
    assert aux["disposed_run_ids"] == ["CR-run-r1", "CR-run-r2"]
    assert aux["runs_awaiting_disposition"] == []
    assert aux["terminal_event_kinds"] == {"approve": 2}
    assert "不表示、不代理任何旗标判断正确性" in aux["note"]
    assert [e["path"] for e in m["evidence"]] == [_REC1, _APR7, _REC2, _APR10]


def test_disposition_completion_partial_and_awaiting():
    """仅一个 run 闭合 → 1/2；另一 run 记入 awaiting（流程簿账如实）。"""
    events, runs, evidence, _cal = _two_run_v3_fixture()
    open_events = []
    _ev(open_events, event="enqueue", item_id="ITEM-r2", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec2"))
    m = hp.project_critic_disposition_completion(
        runs, _closed_ledger("ITEM-r1", "rec1") + open_events,
        record_evidence=evidence)
    assert (m["numerator"], m["denominator"], m["value"]) == (1, 2, 0.5)
    assert m["aux"]["runs_awaiting_disposition"] == ["CR-run-r2"]


def test_disposition_completion_blocked_on_hash_mismatch():
    events, runs, evidence, _cal = _two_run_v3_fixture()
    runs[1]["input_hashes_match"] = False
    m = hp.project_critic_disposition_completion(
        runs, events, record_evidence=evidence)
    assert m["status"] == "blocked"
    assert m["value"] is None and m["numerator"] is None
    assert "trust_invalid" in m["reason"]
    assert m["revision"] == hp.PROJECTION_REVISION_V3


def test_disposition_completion_denominator_zero():
    events, runs, evidence, _cal = _two_run_v3_fixture()
    for r in runs:
        r["critic_status"] = "blocked"
    m = hp.project_critic_disposition_completion(
        runs, events, record_evidence=evidence)
    assert m["status"] == "not_available"
    assert m["denominator"] == 0
    assert m["value"] is None and m["numerator"] is None
    assert "denominator_zero" in m["reason"]


# ---------------------------------------------------------------------------
# 指标：判断一致率（质量，not_available）
# ---------------------------------------------------------------------------

def test_judgment_agreement_not_available_no_per_flag_verdict():
    events, runs, evidence, cal = _two_run_v3_fixture()
    m = hp.project_critic_judgment_agreement(
        runs, events, record_evidence=evidence,
        calibration_observation=cal)
    assert m["metric_id"] == "critic_judgment_agreement_rate"
    assert m["status"] == "not_available"
    assert m["denominator"] == 0
    assert m["value"] is None and m["numerator"] is None  # 不冒充数值
    assert "逐旗标" in m["reason"]
    assert "APR-0007/0010" in m["reason"]
    assert "不得由修正程序代创标签" in m["reason"]
    assert m["revision"] == hp.PROJECTION_REVISION_V3
    for k in hp.DESCRIPTOR_KEYS:
        assert k in m
    aux = m["aux"]
    assert aux["metric_kind"] == "quality"
    assert aux["flags_total"] == 19 and aux["abstain_count"] == 6
    assert aux["runs_executed_valid"] == 2
    for k in ("precision", "recall", "fpr", "fnr"):
        assert aux["flag_level_metrics"][k].startswith("not_available")
    assert "队列闭合" in aux["flag_level_metrics"]["note"]
    # 校准侧实测分列（与装配侧不混写；非门）
    assert [b["source_id"] for b in aux["calibration_side_measured"]] == \
        ["calibration-metric-v1", "calibration-metric-v2"]
    assert "分列" in aux["calibration_side_basis"]
    assert "proposal_only" in aux["calibration_note"]


def test_judgment_agreement_blocked_on_hash_mismatch():
    events, runs, evidence, cal = _two_run_v3_fixture(hashes_match=(True,
                                                                    False))
    m = hp.project_critic_judgment_agreement(
        runs, events, record_evidence=evidence,
        calibration_observation=cal)
    assert m["status"] == "blocked"
    assert "trust_invalid" in m["reason"]


# ---------------------------------------------------------------------------
# v3 载荷组装：指标集校验 + 谓词 + 身份字段
# ---------------------------------------------------------------------------

def _candidates():
    return [
        {"patch_id": "PP-2L", "kind": "policy_parameter_candidate",
         "version": "closed_form_smoke_v1", "profile": "smoke-2l"},
        {"patch_id": "PP-4L", "kind": "policy_parameter_candidate",
         "version": "closed_form_smoke_v1", "profile": "smoke-4l"},
    ]


def _disposition():
    return {"disposition_id": "APR-0004", "kind": "accept",
            "scope": "adoption",
            "fact_refs": ["PP-2L", "PP-4L", "TL-4-G"]}


def _machine_gate_blocked():
    return {"holdout_non_regression_evidenced": False,
            "judge_post_ok": False, "adoption_machine_gate_pass": False}


_GATE2L = "out/v3-tl4/gate-record-tl4-v2-smoke-2l.json"
_GATE4L = "out/v3-tl4/gate-record-tl4-v2-smoke-4l.json"
_PATCH2L = "out/v3-tl4/proposal-patch-smoke-2l.json"
_APR4 = "out/v3-approvals/disposition-APR-0004-tl4-adoption-disposition.json"
_BATCH = "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json"


def _matrix_evidence(measured):
    return {
        "TL-0-G1": [
            {"path": "out/v3-tl0/gate-record-smoke-2l.json",
             "sha256": measured["out/v3-tl0/gate-record-smoke-2l.json"]},
            {"path": "out/v3-tl0/gate-record-smoke-4l.json",
             "sha256": measured["out/v3-tl0/gate-record-smoke-4l.json"]}],
        "TL-1-G1": [{"path": "out/v3-tl1/gate-record.json",
                     "sha256": measured["out/v3-tl1/gate-record.json"]}],
        "TL-2": [
            {"path": _REC1, "sha256": measured[_REC1]},
            {"path": _LEDGER1, "sha256": measured[_LEDGER1]},
            {"path": _APR7, "sha256": measured[_APR7]},
            {"path": _REC2, "sha256": measured[_REC2]},
            {"path": _LEDGER2, "sha256": measured[_LEDGER2]},
            {"path": _APR10, "sha256": measured[_APR10]}],
        "TL-3-G1": [
            {"path": "out/v3-tl3/gate-record.json",
             "sha256": measured["out/v3-tl3/gate-record.json"]},
            {"path": "out/v3-tl3/physics-coverage.json",
             "sha256": measured["out/v3-tl3/physics-coverage.json"]}],
        "TL-4-G": [
            {"path": _GATE2L, "sha256": measured[_GATE2L]},
            {"path": _GATE4L, "sha256": measured[_GATE4L]},
            {"path": _APR4, "sha256": measured[_APR4]}],
        "TL-5-G": [
            {"path": "out/v3-tl5/gate-record-tl5-v4.json",
             "sha256": measured["out/v3-tl5/gate-record-tl5-v4.json"]},
            {"path": "out/v3-tl5/dataset-manifest-kicad-demos-r2.json",
             "sha256": measured[
                 "out/v3-tl5/dataset-manifest-kicad-demos-r2.json"]},
            {"path": _BATCH, "sha256": measured[_BATCH]}],
        "TD7-QUAL-G": [
            {"path": "out/v3-td7/gate-record-td7.json",
             "sha256": measured["out/v3-td7/gate-record-td7.json"]},
            {"path": "out/v3-archive/disposition-ARC-0001-td7-line-archive.json",
             "sha256": measured[
                 "out/v3-archive/disposition-ARC-0001-td7-line-archive.json"]},
            {"path": "out/v3-archive/disposition-ARC-0002-toolchain-lock-proposal.json",
             "sha256": measured[
                 "out/v3-archive/disposition-ARC-0002-toolchain-lock-proposal.json"]},
            {"path": "out/v3-archive/disposition-ARC-0003-d20-batch-gate-semantics.json",
             "sha256": measured[
                 "out/v3-archive/disposition-ARC-0003-d20-batch-gate-semantics.json"]},
            {"path": "out/v3-archive/disposition-ARC-0004-freerouting-v241-upgrade.json",
             "sha256": measured[
                 "out/v3-archive/disposition-ARC-0004-freerouting-v241-upgrade.json"]}],
        "production_signoff_ready": [
            {"path": "out/v3-tl3/gate-record.json",
             "sha256": measured["out/v3-tl3/gate-record.json"]},
            {"path": _GATE2L, "sha256": measured[_GATE2L]}],
    }


def _v3_metric_set(events, runs, evidence, cal, measured):
    return [
        hp.project_manual_queue_multi(
            [{"path": _LEDGER1, "sha256": measured[_LEDGER1],
              "events": _closed_ledger("ITEM-r1", "rec1")},
             {"path": _LEDGER2, "sha256": measured[_LEDGER2],
              "events": _closed_ledger("ITEM-r2", "rec2")}],
            revision=hp.PROJECTION_REVISION_V3,
            baseline=0, baseline_basis="前一 revision 值 0 作基线"),
        hp.project_critic_disposition_completion(
            runs, events, record_evidence=evidence),
        hp.project_critic_judgment_agreement(
            runs, events, record_evidence=evidence,
            calibration_observation=cal),
        hp.project_proposer_acceptance_v2(
            _candidates(), _disposition(), _machine_gate_blocked(),
            patch_evidence=[
                {"path": _PATCH2L, "sha256": measured[_PATCH2L]},
                {"path": "out/v3-tl4/proposal-patch-smoke-4l.json",
                 "sha256": measured[
                     "out/v3-tl4/proposal-patch-smoke-4l.json"]},
                {"path": _GATE2L, "sha256": measured[_GATE2L]},
                {"path": _GATE4L, "sha256": measured[_GATE4L]},
                {"path": _APR4, "sha256": measured[_APR4]}],
            revision=hp.PROJECTION_REVISION_V3,
            baseline=0.0, baseline_basis="前一 revision 值 0.0 作基线"),
        hp.project_non_regression_v2(
            [],
            evidence=[{"path": _GATE2L, "sha256": measured[_GATE2L]},
                      {"path": _GATE4L, "sha256": measured[_GATE4L]}],
            evidence_extra=[{"path": _BATCH, "sha256": measured[_BATCH]}],
            reference_batch={"batch_id": "k9-route-check-batch-r1",
                             "path": _BATCH, "sha256": measured[_BATCH],
                             "all_consistency_pass": True,
                             "scope_note": "参考态证据层",
                             "honest_caveats_note": "如实"},
            revision=hp.PROJECTION_REVISION_V3),
    ]


def _minimal_v3_payload_and_measured():
    """测试内构造的最小 v3 载荷；证据指针指向真实在盘文件，hash=盘上实测
    注入（P4 可对账）。"""
    measured = _measured_real()
    events, runs, evidence, cal = _two_run_v3_fixture(measured=measured)
    metrics = _v3_metric_set(events, runs, evidence, cal, measured)
    aux = hp.auxiliary_scales(
        tl3_coverage={"required_scope": ["PHY-IMP-1"],
                      "covered_scope": ["PHY-IMP-1"], "missing_scope": [],
                      "coverage_complete": True},
        dag_nodes=[{"node": "a"}, {"node": "b"}, {"node": "c"}],
        queue_summary={"oldest_item_id": None, "oldest_item_seq": None,
                       "last_event_seq": 2, "age_events": None},
        physics_report_revision="smoke-r1",
        gate_inputs_revision="smoke-r1")
    matrix = hp.readiness_matrix_v3(_matrix_evidence(measured))
    projection = hp.build_projection_v3(
        session_date="2026-09-05", evaluator_code_sha256=_sha("mod"),
        metrics=metrics, aux_scales=aux, matrix=matrix,
        blockers=hp.open_production_blockers_v3(),
        corpus_denominator=hp.corpus_denominator_block_v3(
            {"pcbbenchmarks-r1": 2, "pcbench-r1": 81, "kicad-demos-r1": 17,
             "corpus-r2-r1": 37},
            {"corpus-r2-r1": {"train": 0, "validation": 0, "holdout": 0,
                              "train_val_candidate": 31,
                              "holdout_pool": 6}},
            conversion_coverage={"boards_total": 100,
                                 "s16_baseline_coverage": 83,
                                 "basis": "83+17",
                                 "k9_r2_manifest": {
                                     "path": "out/x/m.json",
                                     "sha256": _sha("m"),
                                     "sha256_8": _sha("m")[:8]},
                                 "note": "语义不变"}))
    return projection, measured


def test_build_projection_v3_metric_set_validation():
    measured = _measured_real()
    events, runs, evidence, cal = _two_run_v3_fixture(measured=measured)
    metrics = _v3_metric_set(events, runs, evidence, cal, measured)
    aux = hp.auxiliary_scales(
        tl3_coverage={}, dag_nodes=[], queue_summary={},
        physics_report_revision="a", gate_inputs_revision="a")
    matrix = hp.readiness_matrix_v3(_matrix_evidence(measured))
    base_kwargs = dict(
        session_date="2026-09-05", evaluator_code_sha256=_sha("mod"),
        aux_scales=aux, matrix=matrix,
        blockers=hp.open_production_blockers_v3(),
        corpus_denominator=hp.corpus_denominator_block({}, {}))
    # 缺一 → ValueError（缺失）
    with pytest.raises(ValueError, match="指标缺失"):
        hp.build_projection_v3(metrics=metrics[:4], **base_kwargs)
    # 未知指标 → ValueError（未知；v2 已停用指标在 v3 域=未知）
    stranger = dict(metrics[0])
    stranger["metric_id"] = "critic_agreement_rate"
    with pytest.raises(ValueError, match="未知指标"):
        hp.build_projection_v3(metrics=metrics + [stranger], **base_kwargs)
    # 全集 → 通过，身份字段为 v3
    p = hp.build_projection_v3(metrics=metrics, **base_kwargs)
    assert p["revision"] == "v3-tl6-r3"
    assert p["projection_id"] == "HP-v3-tl6-v3-tl6-r3"
    assert p["evaluator"]["version"] == "1.2"
    assert "指标语义更正重投影（P1-C）" in p["mode"]
    assert "拆分为处置完成率（流程）与判断一致率（not_available）" in p["mode"]
    assert [m["metric_id"] for m in p["metrics"]] == \
        list(hp.METRIC_IDS_V3)


def test_v3_payload_predicates_pass_exit_blocked():
    projection, measured = _minimal_v3_payload_and_measured()
    assert projection["readiness_matrix"]["production_signoff_ready"] is False
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == []
    assert all(p["value"] for p in predicates)
    assert [p["id"] for p in predicates] == [
        "projection_computability", "denominator_honesty",
        "not_available_not_value", "evidence_hash_reconciliation"]
    proj_sha = hashing.sha256_text(
        hashing.canonical_json_bytes(projection).decode("utf-8"))
    gate = hp.build_gate_record_v3(
        projection=projection, projection_sha256=proj_sha,
        projection_path="out/v3-tl6/health-projection-v3.json",
        predicates=predicates, failure_codes=failures, inputs=[],
        evaluator_code_sha256=_sha("mod"))
    gr = gate["gate_record"]
    assert gr["result"] == "pass"
    assert gr["snapshot_revision"] == "v3-tl6-r3"
    assert gr["exit_gate"]["gate_id"] == "TL-6-G"
    assert gr["exit_gate"]["result"] == "blocked"
    assert gr["exit_gate"]["closure_claimed"] is False
    assert gr["exit_gate"]["open_blockers"] == \
        ["BL-1", "BL-2", "BL-3", "BL-4"]
    metrics = {m["metric_id"]: m for m in projection["metrics"]}
    assert (metrics["critic_disposition_completion_rate"]["numerator"],
            metrics["critic_disposition_completion_rate"]["denominator"]) == \
        (2, 2)
    assert metrics["critic_judgment_agreement_rate"]["status"] == \
        "not_available"
    assert metrics["critic_judgment_agreement_rate"]["denominator"] == 0


def test_v3_payload_byte_exact_rebuild():
    p1, _ = _minimal_v3_payload_and_measured()
    p2, _ = _minimal_v3_payload_and_measured()
    assert hashing.canonical_json_bytes(p1) == \
        hashing.canonical_json_bytes(p2)


# ---------------------------------------------------------------------------
# readiness v3 / blockers v3
# ---------------------------------------------------------------------------

def test_readiness_matrix_v3_rows():
    matrix = hp.readiness_matrix_v3(_matrix_evidence(_measured_real()))
    assert len(matrix["rows"]) == 9
    assert matrix["production_signoff_ready"] is False
    assert matrix["self_signoff_forbidden"] == "L7 缺证据闭门律"
    by_key = {r["gate"]: r for r in matrix["rows"]}
    tl2 = by_key["TL-2"]
    assert tl2["status"] == "partial_pass_queue_closed"
    assert "流程指标" in tl2["note"]
    assert "处置完成率 2/2=流程指标" in tl2["note"]
    assert "判断一致率 not_available" in tl2["note"]
    assert "自动分流仍 blocked" in tl2["note"]
    tl6 = by_key["TL-6"]
    assert tl6["status"] == "blocked"
    assert "指标语义更正重投影" in tl6["note"]
    self_ref = tl6["evidence"][0]
    assert self_ref["path"] == "out/v3-tl6/health-projection-v3.json"
    assert self_ref["self_reference"] is True
    assert by_key["production_signoff_ready"]["status"] == "false"
    assert by_key["TL-3-G1"]["status"] == "fail"
    assert by_key["TL-4-G"]["status"] == "fail"
    assert by_key["TL-5-G"]["status"] == "pass"
    with pytest.raises(ValueError, match="缺证据指针"):
        hp.readiness_matrix_v3({"TL-0-G1": [
            {"path": "out/x/a.json", "sha256": _sha("a")}]})


def test_open_blockers_v3_bl4_appended_only():
    blockers = hp.open_production_blockers_v3()
    v2_blockers = hp.open_production_blockers_v2()
    assert [b["blocker_id"] for b in blockers] == \
        ["BL-1", "BL-2", "BL-3", "BL-4"]
    # BL-1..3 零变化
    for i in range(3):
        assert blockers[i] == v2_blockers[i]
    # BL-4：仅 detail 追加一句，其余字段零变化；不翻 resolved
    bl4, bl4_v2 = blockers[3], v2_blockers[3]
    assert bl4["detail"].startswith(bl4_v2["detail"])
    assert "队列闭合≠旗标正确性结论（P1-C 更正）" in bl4["detail"]
    assert bl4["detail"].endswith("队列闭合≠旗标正确性结论（P1-C 更正）")
    for k in bl4_v2:
        if k != "detail":
            assert bl4[k] == bl4_v2[k]
    assert bl4["status"].startswith("open")


# ---------------------------------------------------------------------------
# metric-correction-note 构造函数
# ---------------------------------------------------------------------------

def _note_v2_hash() -> str:
    return hp.V2_FROZEN_PROJECTION_ANCHOR + "0" * 56


def test_metric_correction_note_constructor():
    projection, _measured = _minimal_v3_payload_and_measured()
    proj_sha = hashing.sha256_text(
        hashing.canonical_json_bytes(projection).decode("utf-8"))
    note = hp.build_metric_correction_note(
        session_date="2026-09-05",
        v2_projection_sha256=_note_v2_hash(),
        v3_projection=projection,
        v3_projection_sha256=proj_sha)
    # 更正对象：v2 冻结 hash 锚（990bbf98）+ 被更正指标
    assert note["corrects"]["sha256_8"] == "990bbf98"
    assert note["corrects"]["path"] == "out/v3-tl6/health-projection-v2.json"
    assert note["corrects"]["overwritten"] is False
    assert note["corrected_metric"]["metric_id"] == "critic_agreement_rate"
    assert note["corrected_metric"]["v2_frozen_value"] == 1.0
    assert note["corrected_metric"]["v2_frozen_fraction"] == "2/2"
    # 拆分后的两个指标 id 与定义
    split_ids = [s["metric_id"] for s in note["split_into"]]
    assert split_ids == ["critic_disposition_completion_rate",
                         "critic_judgment_agreement_rate"]
    assert note["split_into"][0]["metric_kind"] == "process"
    assert note["split_into"][0]["v3_fraction"] == "2/2"
    assert note["split_into"][1]["metric_kind"] == "quality"
    assert note["split_into"][1]["v3_status"] == "not_available"
    assert "逐旗标" in note["split_into"][1]["reason"]
    # 改名/定义变化清单
    kinds = {c["metric_id"]: c["change_kind"]
             for c in note["renames_and_definition_changes"]}
    assert kinds["critic_agreement_rate"] == "retired_split"
    assert kinds["critic_disposition_completion_rate"] == "added"
    assert kinds["critic_judgment_agreement_rate"] == "added"
    assert kinds["proposer_acceptance_rate"] == "unchanged"
    # 零门翻转声明 + readiness 影响
    assert note["readiness_impact"]["zero_gate_flip"] is True
    assert "零门翻转" in note["readiness_impact"]["declaration"]
    assert note["readiness_impact"]["gate_flips"] == []
    assert note["readiness_impact"]["tl6_exit_gate"] == "TL-6-G 仍 blocked"
    assert note["readiness_impact"]["production_signoff_ready"] is False
    assert "blocked" in note["readiness_impact"]["auto_triage"]
    # v1/v2 冻结件清单 + 不覆写声明
    frozen = note["frozen_files_no_overwrite"]
    anchors = {f["path"]: f["sha256_8"] for f in frozen["files"]}
    assert anchors["out/v3-tl6/health-projection.json"] == "98677d11"
    assert anchors["out/v3-tl6/health-projection-v2.json"] == "990bbf98"
    assert anchors["out/v3-tl6/projection-diff-v1-to-v2.json"] == "da22f874"
    assert "零写入、零删除" in frozen["declaration"]
    assert "不覆写" in frozen["declaration"]
    assert note["superseded_metric_ids"] == ["critic_agreement_rate"]
    assert note["successor_metric_ids"] == [
        "critic_disposition_completion_rate", "critic_judgment_agreement_rate"]
    # 确定性
    note2 = hp.build_metric_correction_note(
        session_date="2026-09-05",
        v2_projection_sha256=_note_v2_hash(),
        v3_projection=projection, v3_projection_sha256=proj_sha)
    assert hashing.canonical_json_bytes(note) == \
        hashing.canonical_json_bytes(note2)


def test_metric_correction_note_rejects_wrong_anchor():
    projection, _measured = _minimal_v3_payload_and_measured()
    with pytest.raises(ValueError, match="先验锚不符"):
        hp.build_metric_correction_note(
            session_date="2026-09-05",
            v2_projection_sha256="deadbeef" + "0" * 56,
            v3_projection=projection, v3_projection_sha256=_sha("v3"))


# ---------------------------------------------------------------------------
# v1/v2 函数行为不变的冒烟
# ---------------------------------------------------------------------------

def _two_run_v2_fixture(supported=(True, True)):
    """v2 夹具（同 tests/test_s22_health_projection_v2.py 语义）。"""
    events = (_closed_ledger("ITEM-r1", "rec1")
              + _closed_ledger("ITEM-r2", "rec2"))

    def run(run_id, seed, flags, abstain, boards, sup):
        d = _critic_run(run_id, seed, flags, abstain, boards)
        d["human_supports_flags"] = sup
        return d

    critic_runs = [
        run("CR-run-r1", "rec1", 7, 1, {"bm11": 5, "launchxl": 2},
            supported[0]),
        run("CR-run-r2", "rec2", 12, 5,
            {"data-manager": 4, "flatpack2": 3, "karabas-reva": 3,
             "karabas-wifi": 2}, supported[1]),
    ]
    record_evidence = [
        {"run_id": "CR-run-r1", "path": "out/x/rec1.json",
         "sha256": _sha("rec1")},
        {"run_id": "APR-0007", "path": "out/x/apr7.json",
         "sha256": _sha("apr7")},
        {"run_id": "CR-run-r2", "path": "out/x/rec2.json",
         "sha256": _sha("rec2")},
        {"run_id": "APR-0010", "path": "out/x/apr10.json",
         "sha256": _sha("apr10")},
    ]
    return events, critic_runs, record_evidence


def test_v1_v2_functions_smoke_unchanged():
    """v1/v2 冒烟：v3 增量不得改变其输出语义（同参重跑仍 v2 冻结件同构）。"""
    events, runs, evidence = _two_run_v2_fixture()
    m2 = hp.project_critic_agreement_v2(
        runs, events, record_evidence=evidence,
        calibration_observation=[],
        baseline_basis="前一 revision not_available")
    assert m2["status"] == "value"
    assert (m2["numerator"], m2["denominator"], m2["value"]) == (2, 2, 1.0)
    assert m2["revision"] == hp.PROJECTION_REVISION_V2 == "v3-tl6-r2"
    assert m2["metric_id"] == "critic_agreement_rate"
    aux = m2["aux"]
    assert aux["flags_total"] == 19 and aux["abstain_count"] == 6
    for k in ("precision", "recall", "fpr", "fnr"):
        assert aux["flag_level_metrics"][k].startswith("not_available")
    m1 = hp.project_critic_agreement(runs, events,
                                     record_evidence=evidence)
    assert (m1["numerator"], m1["denominator"], m1["value"]) == (2, 2, 1.0)
    assert m1["revision"] == hp.PROJECTION_REVISION == "v3-tl6-r1"
    # v1 身份常量与矩阵语义不变
    assert hp.METRIC_IDS == ("manual_queue_length", "critic_agreement_rate",
                             "proposer_acceptance_rate",
                             "cross_board_non_regression_rate")
    assert hp.PROJECTION_REVISION_V3 == "v3-tl6-r3"
    assert hp.METRIC_IDS_V3 == ("manual_queue_length",
                                "critic_disposition_completion_rate",
                                "critic_judgment_agreement_rate",
                                "proposer_acceptance_rate",
                                "cross_board_non_regression_rate")
    matrix = hp.readiness_matrix(_matrix_evidence(_measured_real()))
    by_key = {r["gate"]: r for r in matrix["rows"]}
    assert by_key["TL-2"]["status"] == "partial_pass_with_open_queue"
    assert by_key["TL-6"]["evidence"][0]["path"] == \
        "out/v3-tl6/health-projection.json"
    # _metric_base_v3 校验域不与 v1 混域
    with pytest.raises(ValueError, match="未知指标"):
        hp._metric_base_v3("critic_agreement_rate", dataset="d",
                           definition="x", denominator=None, baseline=None,
                           threshold="t", window=None, profile="p")


# ---------------------------------------------------------------------------
# 语料分母 v3：四库实测装配（corpus-r2-r1 并入；显式 split 键诚实分列）
# ---------------------------------------------------------------------------

def _cov_min() -> dict:
    return {"boards_total": 100, "s16_baseline_coverage": 83,
            "basis": "83+17=100（S18 入账口径）",
            "k9_r2_manifest": {"path": "out/x/m.json", "sha256": _sha("m"),
                               "sha256_8": _sha("m")[:8]},
            "note": "口径不变"}


def test_corpus_denominator_block_v3_four_libraries():
    """v3 语料分母：四库实测装配 + corpus-r2-r1 显式 split 键诚实分列。"""
    by_dataset = {"pcbbenchmarks-r1": 2, "pcbench-r1": 81,
                  "kicad-demos-r1": 17, "corpus-r2-r1": 37}
    by_split = {
        "pcbbenchmarks-r1": {"train": 1, "validation": 0, "holdout": 1},
        "kicad-demos-r1": {"train": 14, "validation": 0, "holdout": 3},
        "corpus-r2-r1": {"train": 0, "validation": 0, "holdout": 0,
                         "train_val_candidate": 31, "holdout_pool": 6},
    }
    block = hp.corpus_denominator_block_v3(
        by_dataset, by_split, conversion_coverage=_cov_min())
    # total=四库之和（137）；corpus 库板数如实入 by_dataset
    assert block["total_boards"] == 137
    assert block["by_dataset"]["corpus-r2-r1"] == 37
    # 诚实口径：31 板 train/val-candidate=候选未定 split（显式键，不虚报
    # train/validation）；6 板 holdout-pool=预冻结池（显式键，不计 holdout）
    assert block["by_split"]["corpus-r2-r1"] == {
        "train": 0, "validation": 0, "holdout": 0,
        "train_val_candidate": 31, "holdout_pool": 6}
    assert "train_val_candidate" in block["note"]
    assert "holdout_pool" in block["note"]
    assert "不虚报" in block["note"]
    assert "预冻结池" in block["note"]
    # real_profiles_in_domain 沿用 v1 的 37（TL-5 门分母，不随入库增长）
    assert block["real_profiles_in_domain"] == 37
    assert "不随 corpus-r2-r1 入库增长" in block["note"]
    # 转换域覆盖透传；v1 块无 v3 增量键
    assert block["conversion_domain_coverage"]["boards_total"] == 100
    plain = hp.corpus_denominator_block(by_dataset, by_split)
    assert "conversion_domain_coverage" not in plain
    assert plain["total_boards"] == 137


def test_corpus_denominator_block_v3_fail_closed():
    """v3 fail-closed：by_split 合计与 by_dataset 不符 / 键不在域 → raise。"""
    cov = _cov_min()
    with pytest.raises(ValueError, match="不符"):
        hp.corpus_denominator_block_v3(
            {"a": 5}, {"a": {"train": 3, "holdout": 1}},  # 4 != 5
            conversion_coverage=cov)
    with pytest.raises(ValueError, match="不在"):
        hp.corpus_denominator_block_v3(
            {"a": 4}, {"a": {"train": 4}, "ghost": {"holdout_pool": 1}},
            conversion_coverage=cov)


# ---------------------------------------------------------------------------
# 集成锚：真实 out/ 实况（只读）——s23 编排重建与盘上四产物对账
# ---------------------------------------------------------------------------

_S23_SPEC = importlib.util.spec_from_file_location(
    "s23_health_orchestrate_v3",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "s23_health_orchestrate_v3.py"))
s23 = importlib.util.module_from_spec(_S23_SPEC)
_S23_SPEC.loader.exec_module(s23)

FROZEN_FILES = {
    "out/v3-tl6/health-projection.json": s23.FROZEN_V1_SHA256,
    "out/v3-tl6/health-projection-gate.json": s23.FROZEN_V1_GATE_SHA256,
    "out/v3-tl6/health-projection.sha256": s23.FROZEN_V1_SIDECAR_SHA256,
    "out/v3-tl6/health-projection-v2.json": s23.FROZEN_V2_SHA256,
    "out/v3-tl6/health-projection-gate-v2.json": s23.FROZEN_V2_GATE_SHA256,
    "out/v3-tl6/projection-diff-v1-to-v2.json": s23.FROZEN_V2_DIFF_SHA256,
}


def test_real_out_projection_v3_integration():
    hashes = s23.measure_hashes()
    projection = s23.build_everything(hashes)
    measured = {s23.EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == [] and all(p["value"] for p in predicates)
    assert [m["metric_id"] for m in projection["metrics"]] == \
        list(hp.METRIC_IDS_V3)
    metrics = {m["metric_id"]: m for m in projection["metrics"]}
    # 指标一：两 run 均 closed（APR-0007/0010）→ open=0（复用 multi 账本）
    assert metrics["manual_queue_length"]["status"] == "value"
    assert metrics["manual_queue_length"]["value"] == 0
    assert metrics["manual_queue_length"]["baseline"] == 0
    # 指标二：处置完成率 2/2（流程指标）
    disp = metrics["critic_disposition_completion_rate"]
    assert disp["status"] == "value"
    assert (disp["numerator"], disp["denominator"], disp["value"]) == \
        (2, 2, 1.0)
    assert "流程指标" in disp["definition"]
    assert "不表示、不代理任何旗标判断正确性" in disp["definition"]
    # 指标三：判断一致率 not_available（无逐旗标 verdict）
    judg = metrics["critic_judgment_agreement_rate"]
    assert judg["status"] == "not_available"
    assert judg["denominator"] == 0
    assert judg["value"] is None and judg["numerator"] is None
    assert "逐旗标" in judg["reason"]
    cal = judg["aux"]["calibration_side_measured"]
    assert [(b["gt_recall"], b["reader_precision_vs_seed_gt"])
            for b in cal] == [(0.25, 0.2), (0.25, 0.142857)]
    # 指标四/五：复用 v2 语义
    assert metrics["proposer_acceptance_rate"]["value"] == 0.0
    assert metrics["proposer_acceptance_rate"]["aux"]["adoption_status"] == \
        "human_approved_machine_blocked"
    assert metrics["cross_board_non_regression_rate"]["status"] == \
        "not_available"
    # readiness/BL/语料/身份（语料=S23 起四库实测口径，137 板）
    by_key = {r["gate"]: r for r in projection["readiness_matrix"]["rows"]}
    assert by_key["TL-2"]["status"] == "partial_pass_queue_closed"
    assert len(projection["open_production_blockers"]) == 4
    assert projection["corpus_denominator"]["total_boards"] == 137
    assert projection["corpus_denominator"]["by_dataset"][
        "corpus-r2-r1"] == 37
    assert projection["corpus_denominator"]["by_split"][
        "corpus-r2-r1"]["train_val_candidate"] == 31
    assert projection["corpus_denominator"]["by_split"][
        "corpus-r2-r1"]["holdout_pool"] == 6
    assert projection["revision"] == "v3-tl6-r3"
    assert projection["evaluator"]["version"] == "1.2"


def test_real_out_four_artifacts_and_frozen_unchanged():
    """集成锚（corpus-r2-r1 并入语料分母后的口径）——byte-exact 单锚：

    - 重建锚（当前模块，只读）：s23.build_everything 实测装配四库分母
      （total=137，corpus-r2-r1=37 板 manifest 实测、显式 split 键分列），
      四谓词全绿、diff/更正说明锚定 v2 冻结件；
    - 盘上锚（只读）：v1/v2 六冻结件 hash 先验对账不变；盘上 v3 四件
      =s23 main() 落盘重生成（2026-09-21 corpus by_dataset 收尾件），
      与重建载荷逐字节一致（byte-exact；「盘上前版冻结+重建版新口径」
      双锚过渡已完成历史使命，收口为单锚，不放宽冻结件对账）。
    """
    hashes = s23.measure_hashes()
    projection = s23.build_everything(hashes)
    proj_bytes = hashing.canonical_json_bytes(projection)
    proj_sha = hashing.sha256_text(proj_bytes.decode("utf-8"))
    measured = {s23.EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == [] and all(p["value"] for p in predicates)
    gate = hp.build_gate_record_v3(
        projection=projection, projection_sha256=proj_sha,
        projection_path=s23.V3_PROJECTION,
        predicates=predicates, failure_codes=failures,
        inputs=s23.gate_inputs(hashes),
        evaluator_code_sha256=hashes["module"])
    diff_payload = s23.build_diff_payload(projection, proj_sha)
    note_payload = s23.build_note_payload(projection, proj_sha)

    # 重建锚：四库实测分母（corpus-r2-r1 manifest 实测装配，不硬编码）
    cd = projection["corpus_denominator"]
    assert cd["total_boards"] == 137
    assert cd["by_dataset"]["corpus-r2-r1"] == 37
    assert cd["by_split"]["corpus-r2-r1"] == {
        "train": 0, "validation": 0, "holdout": 0,
        "train_val_candidate": 31, "holdout_pool": 6}
    assert cd["real_profiles_in_domain"] == 37
    assert "train_val_candidate" in cd["note"]
    assert "holdout_pool" in cd["note"]
    cov = cd["conversion_domain_coverage"]
    assert cov["boards_total"] == 100
    assert cov["s16_baseline_coverage"] == 83
    assert cov["corpus_r2_parse_gate"]["boards"] == 37
    assert cov["corpus_r2_parse_gate"]["kicad5_bucket_20171130"] == 9
    assert cov["corpus_r2_parse_gate"]["modern_bucket_20241229"] == 7
    # 重建 gate：四谓词全绿 + exit_gate blocked 如实
    gr_rebuilt = gate["gate_record"]
    assert all(p["value"] for p in gr_rebuilt["required_predicates"])
    assert gr_rebuilt["exit_gate"]["result"] == "blocked"
    assert gr_rebuilt["snapshot_revision"] == "v3-tl6-r3"

    # 盘上锚：四件=s23 main() 落盘重生成（四库 137 新口径），与重建载荷
    # 逐字节一致（byte-exact；追加式并入 corpus-r2-r1，既有三库注册名
    # pcbbenchmarks-r1/pcbench-r1/kicad-demos-r1 零变化）
    rebuilt_bytes = {
        "health-projection-v3.json": proj_bytes,
        "health-projection-gate-v3.json": hashing.canonical_json_bytes(gate),
        "projection-diff-v2-to-v3.json":
            hashing.canonical_json_bytes(diff_payload),
        "metric-correction-note-v1.json":
            hashing.canonical_json_bytes(note_payload),
    }
    disk = {}
    for rel, want in rebuilt_bytes.items():
        path = s23.REPO / "out/v3-tl6" / rel
        assert path.is_file(), f"缺新件 {rel}"
        assert path.read_bytes() == want, \
            f"盘上件与重建载荷非 byte-exact: {rel}"
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict)
        disk[rel] = parsed
    assert disk["health-projection-v3.json"][
        "corpus_denominator"]["total_boards"] == 137
    assert disk["health-projection-v3.json"]["corpus_denominator"][
        "by_dataset"] == {"corpus-r2-r1": 37, "kicad-demos-r1": 17,
                          "pcbbenchmarks-r1": 2, "pcbench-r1": 81}

    # v1/v2 六冻结件 hash 未变（只读红线；读盘对账）
    for rel, expect in FROZEN_FILES.items():
        assert hashing.sha256_file(str(s23.REPO / rel)) == expect, \
            f"冻结件被改动：{rel}"

    # diff 载荷（重建 v3 vs v2 冻结原件，从盘读不重算）锚 + 语料并入差异格
    assert diff_payload["from"]["sha256"] == s23.FROZEN_V2_SHA256
    assert diff_payload["from"]["sha256_8"] == "990bbf98"
    assert diff_payload["to"]["sha256"] == proj_sha
    assert diff_payload["frozen_v2_unchanged"] is True
    changes = {c["path"]: c for c in diff_payload["diff"]["changes"]}
    assert changes["metrics[1].metric_id"]["after"] == \
        "critic_disposition_completion_rate"
    assert changes["metrics[2].metric_id"]["after"] == \
        "critic_judgment_agreement_rate"
    assert changes["metrics[2].status"]["after"] == "not_available"
    assert changes["revision"]["after"] == "v3-tl6-r3"
    assert changes["corpus_denominator.total_boards"] == \
        {"path": "corpus_denominator.total_boards", "kind": "changed",
         "before": 100, "after": 137}
    assert changes["corpus_denominator.by_dataset.corpus-r2-r1"] == \
        {"path": "corpus_denominator.by_dataset.corpus-r2-r1",
         "kind": "added", "after": 37}

    # 更正说明锚定盘上 v2 冻结 hash + 零门翻转（重建版与盘上重生成版同锚）
    assert note_payload["corrects"]["sha256_8"] == "990bbf98"
    assert note_payload["readiness_impact"]["zero_gate_flip"] is True
    assert disk["metric-correction-note-v1.json"]["corrects"][
        "sha256_8"] == "990bbf98"
    assert disk["metric-correction-note-v1.json"]["readiness_impact"][
        "zero_gate_flip"] is True
    # 盘上重生成版 gate：谓词全绿 + exit_gate blocked 如实
    gr = disk["health-projection-gate-v3.json"]["gate_record"]
    assert all(p["value"] for p in gr["required_predicates"])
    assert gr["exit_gate"]["result"] == "blocked"
    assert gr["snapshot_revision"] == "v3-tl6-r3"
