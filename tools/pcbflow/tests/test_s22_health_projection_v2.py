"""S22 会话测试：TL-6 健康度重投影 v2（四指标活算+readiness 逐格重评+差异表）。

覆盖：
- 多账本队列投影：两 run 均 closed → open=0（per-ledger 分列）、open 合并、
  任一账本链篡改 → blocked（trust invalid）、计数型 denominator_basis；
- Critic 一致率 v2：装配侧两 run 人工全量支持 → 2/2（部分支持 → 1/2）、
  trust invalid → blocked、旗标级 precision/recall=not_available 的诚实
  理由、校准侧实测单列（calibration_side_measured 与装配侧分列不混写）；
- Proposer 接受率 v2：0/2 human_approved_machine_blocked + 前一 revision
  基线 0.0；
- 跨板不回退 v2：执行分母仍 0（not_available 不变）+ k9 参考态证据层
  单列进 aux（17/17 consistency + D19(b) 5 板不稳 + 1 板 DRC 不可得，
  不入 TL-5 门分母）；
- 语料分母 v2：三库 100 板不变 + 转换域覆盖 83→100；
- readiness matrix v2：9 行、TL-2 状态变更（partial_pass_queue_closed）、
  TL-6 自引 -v2、signoff=false、缺证据 raise；
- open_production_blockers_v2：BL-4 重评=种子在案/未达标/阈值待人工批准
  （不翻 resolved）、BL-1..3 不变；
- 逐格差异表 build_projection_diff：changed/added/removed、bool 与 int
  类型变更不混同、确定性；
- v2 载荷组装+四谓词+gate record（exit_gate 独立 blocked）+身份字段；
- v1 函数语义回归锚（同参调用仍产出 v3-tl6-r1 语义）；
- 集成锚：真实 out/ 实况（只读）——s22 编排重建与盘上三产物对账，
  v1 冻结件 hash 先验断言（防覆写）。

纯内存构造（生成器模式）：零子进程/零网络；集成锚仅只读 out/。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing, health_projection as hp  # noqa: E402
from pcbflow import queue as queue_mod  # noqa: E402


def _sha(seed: str) -> str:
    return hashing.sha256_text(seed)


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


# ---------------------------------------------------------------------------
# 指标一：多账本队列投影
# ---------------------------------------------------------------------------

def test_manual_queue_multi_both_closed_zero():
    ledgers = [
        {"path": "out/v3-tl2/critic-runs/run-r1/queue-event-ledger.jsonl",
         "sha256": _sha("l1"), "events": _closed_ledger("ITEM-run-r1", "r1")},
        {"path": "out/v3-tl2/critic-runs/run-r2/queue-event-ledger.jsonl",
         "sha256": _sha("l2"), "events": _closed_ledger("ITEM-run-r2", "r2")},
    ]
    m = hp.project_manual_queue_multi(ledgers, baseline=1,
                                      baseline_basis="前一 revision 值 1")
    assert m["status"] == "value" and m["value"] == 0
    assert m["revision"] == hp.PROJECTION_REVISION_V2
    assert m["baseline"] == 1 and m["baseline_basis"] == "前一 revision 值 1"
    assert m["denominator"] is None
    assert m["denominator_basis"] == "count_metric_no_denominator"
    for k in hp.DESCRIPTOR_KEYS:
        assert k in m
    assert m["aux"]["open_items"] == []
    assert m["aux"]["input_volume"]["ledgers"] == 2
    assert m["aux"]["input_volume"]["events_total"] == 6
    per = m["window"]["ledgers"]
    assert [p["queue_length"] for p in per] == [0, 0]
    assert all(p["events_since_oldest_enqueue"] is None for p in per)
    assert m["window"]["unit"] == "ledger_event_seq_multi"
    assert m["window"]["wall_clock"].startswith("not_used")
    # by_* 只统计当前 open items（queue.projection_summary 语义）：
    # 两账本全 closed → reason 分布为空（open=0 的诚实空集）。
    assert m["aux"]["by_reason_code"] == {}
    assert [e["path"] for e in m["evidence"]] == \
        [l["path"] for l in ledgers]


def test_manual_queue_multi_open_merged():
    open_events = []
    _ev(open_events, event="enqueue", item_id="ITEM-r3", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("r3"))
    ledgers = [
        {"path": "out/a/ledger.jsonl", "sha256": _sha("l1"),
         "events": _closed_ledger("ITEM-r1", "r1")},
        {"path": "out/b/ledger.jsonl", "sha256": _sha("l2"),
         "events": open_events},
    ]
    m = hp.project_manual_queue_multi(ledgers)
    assert m["status"] == "value" and m["value"] == 1
    assert m["aux"]["open_items"] == ["ITEM-r3"]
    per = m["window"]["ledgers"]
    assert per[0]["queue_length"] == 0 and per[1]["queue_length"] == 1
    assert per[1]["events_since_oldest_enqueue"] == 0


def test_manual_queue_multi_blocked_on_chain_tamper():
    events = _closed_ledger("ITEM-r1", "r1")
    tampered = [dict(events[0], reason_code="forged")]
    ledgers = [
        {"path": "out/a/ledger.jsonl", "sha256": _sha("l1"),
         "events": _closed_ledger("ITEM-r1", "r1")},
        {"path": "out/b/ledger.jsonl", "sha256": _sha("l2"),
         "events": tampered},
    ]
    m = hp.project_manual_queue_multi(ledgers)
    assert m["status"] == "blocked"
    assert m["value"] is None and m["numerator"] is None
    assert "trust_invalid" in m["reason"]
    assert "out/b/ledger.jsonl" in m["reason"]


# ---------------------------------------------------------------------------
# 指标二：Critic 一致率 v2（装配侧 + 校准侧分列）
# ---------------------------------------------------------------------------

def _critic_run(run_id, ref_seed, flags, abstain, boards, supported):
    return {"run_id": run_id, "critic_status": "executed",
            "input_hashes_match": True, "critic_ref": _sha(ref_seed),
            "in_calibrated_range": False, "flags_total": flags,
            "abstain_count": abstain, "board_flag_counts": boards,
            "human_supports_flags": supported}


def _two_run_fixture(supported=(True, True)):
    events = (_closed_ledger("ITEM-r1", "rec1")
              + _closed_ledger("ITEM-r2", "rec2"))
    critic_runs = [
        _critic_run("CR-run-r1", "rec1", 7, 1,
                    {"bm11": 5, "launchxl": 2}, supported[0]),
        _critic_run("CR-run-r2", "rec2", 12, 5,
                    {"data-manager": 4, "flatpack2": 3,
                     "karabas-reva": 3, "karabas-wifi": 2}, supported[1]),
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
    calibration_observation = [
        {"source_id": "calibration-metric-v1", "path": "out/x/cal1.json",
         "sha256": _sha("cal1"), "sha256_8": _sha("cal1")[:8],
         "metric_version": "calibration-metric-v1", "gt_count": 4,
         "gt_recall": 0.25, "reader_precision_vs_seed_gt": 0.2,
         "advisory_note": "校准域种子实测（非门）"},
        {"source_id": "calibration-metric-v2", "path": "out/x/cal2.json",
         "sha256": _sha("cal2"), "sha256_8": _sha("cal2")[:8],
         "metric_version": "calibration-metric-v2", "gt_count": 4,
         "gt_recall": 0.25, "reader_precision_vs_seed_gt": 0.142857,
         "advisory_note": "校准域种子实测（非门）"},
    ]
    return events, critic_runs, record_evidence, calibration_observation


def test_critic_agreement_v2_two_runs_supported_two_over_two():
    events, runs, evidence, cal = _two_run_fixture()
    m = hp.project_critic_agreement_v2(
        runs, events, record_evidence=evidence,
        calibration_observation=cal,
        baseline_basis="前一 revision not_available——基线仍未建立")
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (2, 2, 1.0)
    assert m["revision"] == hp.PROJECTION_REVISION_V2
    aux = m["aux"]
    assert aux["runs_total"] == 2
    assert aux["runs_executed_valid"] == 2
    assert aux["runs_with_human_verdict"] == 2
    assert aux["flags_total"] == 19 and aux["abstain_count"] == 6
    assert aux["worst_board_by_flags"] == "bm11"  # 5 旗，count 最大
    assert aux["in_calibrated_range_observed"] == [False]
    # 旗标级 precision/recall：诚实 not_available（不冒充数值）
    for k in ("precision", "recall", "fpr", "fnr"):
        assert aux["flag_level_metrics"][k].startswith("not_available")
    assert "未对旗标逐条判对错" in aux["flag_level_metrics"]["note"]
    # 校准侧实测单列（与装配侧分列，不混写）
    assert [b["source_id"] for b in aux["calibration_side_measured"]] == \
        ["calibration-metric-v1", "calibration-metric-v2"]
    assert aux["calibration_side_measured"][1][
        "reader_precision_vs_seed_gt"] == 0.142857
    assert "分列" in aux["calibration_side_basis"]
    assert "proposal_only" in aux["calibration_note"]
    assert "恒 False" in aux["calibration_note"]
    assert [e["path"] for e in m["evidence"]] == [
        "out/x/rec1.json", "out/x/apr7.json",
        "out/x/rec2.json", "out/x/apr10.json"]


def test_critic_agreement_v2_partial_support_half():
    events, runs, evidence, cal = _two_run_fixture(supported=(True, False))
    m = hp.project_critic_agreement_v2(
        runs, events, record_evidence=evidence,
        calibration_observation=cal)
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (1, 2, 0.5)


def test_critic_agreement_v2_blocked_on_hash_mismatch():
    events, runs, evidence, cal = _two_run_fixture()
    runs[1]["input_hashes_match"] = False
    m = hp.project_critic_agreement_v2(
        runs, events, record_evidence=evidence,
        calibration_observation=cal)
    assert m["status"] == "blocked"
    assert m["value"] is None and m["numerator"] is None
    assert "trust_invalid" in m["reason"]


# ---------------------------------------------------------------------------
# 指标三/四：Proposer v2 + 跨板不回退 v2
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


def test_proposer_acceptance_v2_machine_blocked_with_baseline():
    m = hp.project_proposer_acceptance_v2(
        _candidates(), _disposition(), _machine_gate_blocked(),
        patch_evidence=[{"path": "out/x/patch.json", "sha256": _sha("p")}],
        baseline=0.0, baseline_basis="前一 revision 值 0.0 作基线")
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (0, 2, 0.0)
    assert m["baseline"] == 0.0
    assert m["aux"]["adoption_status"] == "human_approved_machine_blocked"
    assert m["revision"] == hp.PROJECTION_REVISION_V2


def test_non_regression_v2_reference_layer_single_listed():
    ref_batch = {
        "batch_id": "k9-route-check-batch-r1",
        "path": "out/x/batch.json", "sha256": _sha("batch"),
        "sha256_8": _sha("batch")[:8],
        "boards_consistency_pass": 17, "boards_total": 17,
        "all_consistency_pass": True,
        "d19b_dual_severity_unstable_boards": 5,
        "drc_unavailable_boards": 1,
        "scope_note": "参考态复现验证，不是 autotune 不回退执行面；"
                      "不入 TL-5 门分母",
        "honest_caveats_note": "D19(b) 5 板不稳+1 板 DRC 不可得（不虚构计数）",
    }
    m = hp.project_non_regression_v2(
        [],
        evidence=[{"path": "out/x/gate2l.json", "sha256": _sha("g2")}],
        evidence_extra=[{"path": "out/x/batch.json",
                         "sha256": _sha("batch")}],
        reference_batch=ref_batch)
    assert m["status"] == "not_available"
    assert m["denominator"] == 0 and m["value"] is None
    assert m["revision"] == hp.PROJECTION_REVISION_V2
    rb = m["aux"]["reference_state_batch"]
    assert rb["batch_id"] == "k9-route-check-batch-r1"
    assert rb["boards_consistency_pass"] == 17
    assert rb["d19b_dual_severity_unstable_boards"] == 5
    assert rb["drc_unavailable_boards"] == 1
    assert "不入 TL-5 门分母" in rb["scope_note"]
    assert "不虚构" in rb["honest_caveats_note"] or "如实" in \
        rb["honest_caveats_note"]
    assert [e["path"] for e in m["evidence"]] == \
        ["out/x/gate2l.json", "out/x/batch.json"]
    # 执行分母语义不变：语料可用性与不回退证据解耦仍在
    assert m["aux"]["holdout_execution_denominator"] == 0


# ---------------------------------------------------------------------------
# 语料分母 v2 / readiness v2 / blockers v2
# ---------------------------------------------------------------------------

def test_corpus_denominator_v2_conversion_coverage():
    block = hp.corpus_denominator_block_v2(
        {"pcbbenchmarks-r1": 2, "pcbench-r1": 81, "kicad-demos-r1": 17},
        {"kicad-demos-r1": {"train": 14, "validation": 0, "holdout": 3}},
        conversion_coverage={
            "boards_total": 100, "s16_baseline_coverage": 83,
            "basis": "83+17=100（S18 入账口径）",
            "k9_r2_manifest": {"path": "out/x/m.json",
                               "sha256": _sha("m"),
                               "sha256_8": _sha("m")[:8]},
            "note": "TL-5 门分母与 BL 清单语义不变"})
    assert block["total_boards"] == 100
    cov = block["conversion_domain_coverage"]
    assert cov["boards_total"] == 100 and cov["s16_baseline_coverage"] == 83
    assert "37 profile" in block["note"]
    assert "83→100" in block["note"]
    assert "门分母语义不变" in block["note"]


def _matrix_evidence():
    keys = ["TL-0-G1", "TL-1-G1", "TL-2", "TL-3-G1", "TL-4-G", "TL-5-G",
            "TD7-QUAL-G", "production_signoff_ready"]
    return {k: [{"path": f"out/x/{k}.json", "sha256": _sha(k)}]
            for k in keys}


def test_readiness_matrix_v2_rows():
    matrix = hp.readiness_matrix_v2(_matrix_evidence())
    assert len(matrix["rows"]) == 9
    assert matrix["production_signoff_ready"] is False
    by_key = {r["gate"]: r for r in matrix["rows"]}
    assert by_key["TL-2"]["status"] == "partial_pass_queue_closed"
    assert "APR-0007/0010" in by_key["TL-2"]["note"]
    assert "两账本队列=0" in by_key["TL-2"]["note"]
    assert "恒 blocked" in by_key["TL-2"]["note"]
    assert by_key["TL-0-G1"]["status"] == "pass"
    assert by_key["TL-3-G1"]["status"] == "fail"
    assert by_key["TL-4-G"]["status"] == "fail"
    assert by_key["TL-5-G"]["status"] == "pass"
    assert "不入本门分母" in by_key["TL-5-G"]["note"]
    assert by_key["TD7-QUAL-G"]["status"] == "archived"
    assert by_key["TL-6"]["status"] == "blocked"
    self_ref = by_key["TL-6"]["evidence"][0]
    assert self_ref["path"] == "out/v3-tl6/health-projection-v2.json"
    assert self_ref["self_reference"] is True
    assert by_key["production_signoff_ready"]["status"] == "false"
    with pytest.raises(ValueError, match="缺证据指针"):
        hp.readiness_matrix_v2({"TL-0-G1": _matrix_evidence()["TL-0-G1"]})


def test_open_blockers_v2_bl4_honest_not_resolved():
    blockers = hp.open_production_blockers_v2()
    assert [b["blocker_id"] for b in blockers] == \
        ["BL-1", "BL-2", "BL-3", "BL-4"]
    bl4 = blockers[3]
    assert bl4["status"].startswith("open")
    for kw in ("种子在案", "未达标", "proposal_only", "待人工批准",
               "恒 False"):
        assert kw in bl4["detail"]
    assert "resolved" not in bl4["status"]
    paths = " ".join(e["path"] for e in bl4["evidence"])
    assert "calibration-domain-v2.json" in paths
    assert "calibration-run-v2.json" in paths
    assert "calibration-process-v1.md" in paths
    # BL-1..3 与 v1 内容一致（零变化）
    base = hp.open_production_blockers()
    for i in range(3):
        assert blockers[i] == base[i]


# ---------------------------------------------------------------------------
# 逐格差异表
# ---------------------------------------------------------------------------

def test_build_projection_diff_changed_added_removed():
    old = {"projection_id": "HP-a", "revision": "r1",
           "a": 1, "b": [1, 2], "c": {"d": 3, "e": 4}, "flag": True}
    new = {"projection_id": "HP-b", "revision": "r2",
           "a": 2, "b": [1, 2, 3], "c": {"d": 3, "e": 5}, "extra": 9,
           "flag": 1}
    diff = hp.build_projection_diff(old, new)
    assert diff["diff_schema"] == hp.DIFF_SCHEMA
    assert diff["from_projection_id"] == "HP-a"
    assert diff["to_projection_id"] == "HP-b"
    changes = {c["path"]: c for c in diff["changes"]}
    assert changes["a"]["kind"] == "changed"
    assert (changes["a"]["before"], changes["a"]["after"]) == (1, 2)
    assert changes["b[2]"]["kind"] == "added"
    assert changes["extra"]["kind"] == "added"
    assert changes["c.e"]["kind"] == "changed"
    assert changes["flag"]["kind"] == "changed"  # bool True vs int 1
    # projection_id 与 revision 身份字段同为 changed
    assert changes["projection_id"]["kind"] == "changed"
    assert changes["revision"]["kind"] == "changed"
    assert diff["summary"] == {"added": 2, "removed": 0, "changed": 5}
    # 确定性
    assert hashing.canonical_json_bytes(
        hp.build_projection_diff(old, new)) == \
        hashing.canonical_json_bytes(diff)


def test_build_projection_diff_removed_and_symmetry():
    old = {"a": 1, "gone": {"x": 1}, "lst": [1, 2, 3]}
    new = {"a": 1, "lst": [1]}
    diff = hp.build_projection_diff(old, new)
    changes = {c["path"]: c for c in diff["changes"]}
    assert changes["gone"]["kind"] == "removed"
    assert changes["gone"]["before"] == {"x": 1}
    assert changes["lst[1]"]["kind"] == "removed"
    assert changes["lst[2]"]["kind"] == "removed"
    assert "a" not in changes  # 未变不出现
    assert diff["summary"] == {"added": 0, "removed": 3, "changed": 0}


def test_build_projection_diff_on_real_projection_pair():
    """对真实形状的投影对：v1 形状最小桩 vs v2 形状最小桩——revision/身份/
    状态变化逐格落表（不含任何 IO）。"""
    old = {"projection_id": "HP-v3-tl6-v3-tl6-r1", "revision": "v3-tl6-r1",
           "metrics": [{"metric_id": "manual_queue_length",
                        "status": "value", "value": 1}]}
    new = {"projection_id": "HP-v3-tl6-v3-tl6-r2", "revision": "v3-tl6-r2",
           "metrics": [{"metric_id": "manual_queue_length",
                        "status": "value", "value": 0}]}
    diff = hp.build_projection_diff(old, new)
    changes = {c["path"]: c for c in diff["changes"]}
    assert changes["metrics[0].value"]["before"] == 1
    assert changes["metrics[0].value"]["after"] == 0
    assert changes["revision"]["after"] == "v3-tl6-r2"


# ---------------------------------------------------------------------------
# v2 载荷组装 + 谓词 + 身份字段 + v1 回归锚
# ---------------------------------------------------------------------------

def _v2_payload_and_measured():
    events, runs, evidence, cal = _two_run_fixture()
    metrics = [
        hp.project_manual_queue_multi(
            [{"path": "out/x/ledger1.jsonl", "sha256": _sha("l1"),
              "events": _closed_ledger("ITEM-r1", "rec1")},
             {"path": "out/x/ledger2.jsonl", "sha256": _sha("l2"),
              "events": _closed_ledger("ITEM-r2", "rec2")}],
            baseline=1, baseline_basis="前一 revision 值 1"),
        hp.project_critic_agreement_v2(
            runs, events, record_evidence=evidence,
            calibration_observation=cal,
            baseline_basis="前一 revision not_available"),
        hp.project_proposer_acceptance_v2(
            _candidates(), _disposition(), _machine_gate_blocked(),
            patch_evidence=[{"path": "out/x/patch.json",
                             "sha256": _sha("p")}],
            baseline=0.0, baseline_basis="前一 revision 值 0.0 作基线"),
        hp.project_non_regression_v2(
            [],
            evidence=[{"path": "out/x/gate2l.json", "sha256": _sha("g2")}],
            evidence_extra=[{"path": "out/x/batch.json",
                             "sha256": _sha("batch")}],
            reference_batch={"batch_id": "k9-route-check-batch-r1",
                             "path": "out/x/batch.json",
                             "sha256": _sha("batch"),
                             "all_consistency_pass": True,
                             "scope_note": "参考态证据层",
                             "honest_caveats_note": "如实"}),
    ]
    aux = hp.auxiliary_scales(
        tl3_coverage={"required_scope": ["PHY-IMP-1"],
                      "covered_scope": ["PHY-IMP-1"], "missing_scope": [],
                      "coverage_complete": True},
        dag_nodes=[{"node": "a"}, {"node": "b"}, {"node": "c"}],
        queue_summary={"oldest_item_id": None, "oldest_item_seq": None,
                       "last_event_seq": 2, "age_events": None},
        physics_report_revision="smoke-r1",
        gate_inputs_revision="smoke-r1")
    matrix = hp.readiness_matrix_v2(_matrix_evidence())
    projection = hp.build_projection_v2(
        session_date="2026-09-05", evaluator_code_sha256=_sha("mod"),
        metrics=metrics, aux_scales=aux, matrix=matrix,
        blockers=hp.open_production_blockers_v2(),
        corpus_denominator=hp.corpus_denominator_block_v2(
            {"pcbbenchmarks-r1": 2, "pcbench-r1": 81,
             "kicad-demos-r1": 17}, {},
            conversion_coverage={"boards_total": 100,
                                 "s16_baseline_coverage": 83,
                                 "basis": "83+17",
                                 "k9_r2_manifest": {
                                     "path": "out/x/m.json",
                                     "sha256": _sha("m"),
                                     "sha256_8": _sha("m")[:8]},
                                 "note": "语义不变"}))
    measured = {"out/x/ledger1.jsonl": _sha("l1"),
                "out/x/ledger2.jsonl": _sha("l2"),
                "out/x/rec1.json": _sha("rec1"),
                "out/x/apr7.json": _sha("apr7"),
                "out/x/rec2.json": _sha("rec2"),
                "out/x/apr10.json": _sha("apr10"),
                "out/x/patch.json": _sha("p"),
                "out/x/gate2l.json": _sha("g2"),
                "out/x/batch.json": _sha("batch"),
                **{f"out/x/{k}.json": _sha(k)
                   for k in ("TL-0-G1", "TL-1-G1", "TL-2", "TL-3-G1",
                             "TL-4-G", "TL-5-G", "TD7-QUAL-G",
                             "production_signoff_ready")}}
    return projection, measured


def test_v2_payload_predicates_pass_exit_blocked():
    projection, measured = _v2_payload_and_measured()
    assert projection["revision"] == "v3-tl6-r2"
    assert projection["projection_id"] == "HP-v3-tl6-v3-tl6-r2"
    assert projection["evaluator"]["version"] == "1.1"
    assert projection["session_date"] == "2026-09-05"
    assert projection["readiness_matrix"]["production_signoff_ready"] is False
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == []
    assert all(p["value"] for p in predicates)
    proj_sha = hashing.sha256_text(
        hashing.canonical_json_bytes(projection).decode("utf-8"))
    gate = hp.build_gate_record_v2(
        projection=projection, projection_sha256=proj_sha,
        projection_path="out/v3-tl6/health-projection-v2.json",
        predicates=predicates, failure_codes=failures, inputs=[],
        evaluator_code_sha256=_sha("mod"))
    gr = gate["gate_record"]
    assert gr["result"] == "pass"
    assert gr["snapshot_revision"] == "v3-tl6-r2"
    assert gr["exit_gate"]["gate_id"] == "TL-6-G"
    assert gr["exit_gate"]["result"] == "blocked"
    assert gr["exit_gate"]["closure_claimed"] is False
    assert gr["exit_gate"]["open_blockers"] == \
        ["BL-1", "BL-2", "BL-3", "BL-4"]


def test_v2_payload_byte_exact_rebuild():
    p1, _ = _v2_payload_and_measured()
    p2, _ = _v2_payload_and_measured()
    assert hashing.canonical_json_bytes(p1) == \
        hashing.canonical_json_bytes(p2)


def test_v1_function_semantics_unchanged():
    """v1 回归锚：v2 增量不得改变 v1 函数的输出语义（revision/结构）。"""
    events = []
    _ev(events, event="enqueue", item_id="ITEM-x", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    m = hp.project_manual_queue(
        events, ledger_path="out/x/l.jsonl", ledger_sha256=_sha("l"))
    assert m["revision"] == "v3-tl6-r1"
    assert m["window"]["unit"] == "ledger_event_seq"
    block = hp.corpus_denominator_block({"a": 2}, {})
    assert "KiCad5 20171130" in block["note"]
    assert "conversion_domain_coverage" not in block
    matrix = hp.readiness_matrix(_matrix_evidence())
    by_key = {r["gate"]: r for r in matrix["rows"]}
    assert by_key["TL-2"]["status"] == "partial_pass_with_open_queue"
    assert by_key["TL-6"]["evidence"][0]["path"] == \
        "out/v3-tl6/health-projection.json"
    assert hp.PROJECTION_REVISION == "v3-tl6-r1"


# ---------------------------------------------------------------------------
# 集成锚：真实 out/ 实况（只读）——s22 编排重建与盘上产物对账
# ---------------------------------------------------------------------------

_S22_SPEC = importlib.util.spec_from_file_location(
    "s22_health_orchestrate_v2",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "s22_health_orchestrate_v2.py"))
s22 = importlib.util.module_from_spec(_S22_SPEC)
_S22_SPEC.loader.exec_module(s22)


def test_real_out_projection_v2_integration():
    hashes = s22.measure_hashes()
    projection = s22.build_everything(hashes)
    measured = {s22.EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == [] and all(p["value"] for p in predicates)
    metrics = {m["metric_id"]: m for m in projection["metrics"]}
    # 指标一：两 run 均 closed（APR-0007/0010）→ open=0
    assert metrics["manual_queue_length"]["status"] == "value"
    assert metrics["manual_queue_length"]["value"] == 0
    assert metrics["manual_queue_length"]["baseline"] == 1
    # 指标二：装配侧一致率=2/2（人工对两 run 旗标全量支持）
    agreement = metrics["critic_agreement_rate"]
    assert agreement["status"] == "value"
    assert agreement["numerator"] == 2 and agreement["denominator"] == 2
    assert agreement["value"] == 1.0
    aux = agreement["aux"]
    assert aux["flags_total"] == 19 and aux["abstain_count"] == 6
    cal = aux["calibration_side_measured"]
    assert [(b["gt_recall"], b["reader_precision_vs_seed_gt"])
            for b in cal] == [(0.25, 0.2), (0.25, 0.142857)]
    # 指标三：0/2 human_approved_machine_blocked 维持
    proposer = metrics["proposer_acceptance_rate"]
    assert proposer["value"] == 0.0
    assert proposer["aux"]["adoption_status"] == \
        "human_approved_machine_blocked"
    # 指标四：not_available 维持 + k9 参考态证据层单列
    nonreg = metrics["cross_board_non_regression_rate"]
    assert nonreg["status"] == "not_available"
    rb = nonreg["aux"]["reference_state_batch"]
    assert rb["batch_id"] == "k9-route-check-batch-r1"
    assert (rb["boards_consistency_pass"], rb["boards_total"]) == (17, 17)
    assert rb["d19b_dual_severity_unstable_boards"] == 5
    assert rb["drc_unavailable_boards"] == 1
    # readiness/BL/语料
    by_key = {r["gate"]: r for r in projection["readiness_matrix"]["rows"]}
    assert by_key["TL-2"]["status"] == "partial_pass_queue_closed"
    assert len(projection["open_production_blockers"]) == 4
    assert projection["corpus_denominator"]["total_boards"] == 100
    assert projection["corpus_denominator"][
        "conversion_domain_coverage"]["boards_total"] == 100


def test_real_out_diff_and_frozen_v1_unchanged():
    hashes = s22.measure_hashes()
    # P1-C 起注：health_projection.py 在 S22 冻结后追加了 v3 增量段（P1-C
    # 指标语义更正），模块 code hash 随之演进（e471f09d…→当前）。v2 冻结件
    # evaluator.code_sha256 声明的是「产出该冻结件的模块身份」；本测试断言
    # =冻结件可由其声明身份精确重现（逐字节），故把重建的 evaluator 身份
    # pin 回冻结件自声明值（其余输入 hash 仍全部盘上实测；v1/v2 函数语义
    # 若有漂移仍会被逐字节比对捕获——断言不放宽）。活重建语义等价性由
    # test_real_out_projection_v2_integration（谓词全绿+逐键相等）保障。
    frozen_v2 = json.loads(
        (s22.REPO / "out/v3-tl6/health-projection-v2.json")
        .read_text(encoding="utf-8"))
    hashes = dict(hashes, module=frozen_v2["evaluator"]["code_sha256"])
    projection = s22.build_everything(hashes)
    proj_bytes = hashing.canonical_json_bytes(projection)
    proj_sha = hashing.sha256_text(proj_bytes.decode("utf-8"))
    diff_payload = s22.build_diff_payload(projection, proj_sha, hashes)
    # v1 冻结件先验锚（防覆写 fail-closed 机制本身受测）
    assert diff_payload["from"]["sha256"] == s22.FROZEN_V1_SHA256
    assert diff_payload["from"]["sha256_8"] == "98677d11"
    assert diff_payload["to"]["sha256"] == proj_sha
    assert diff_payload["frozen_v1_unchanged"] is True
    dsum = diff_payload["diff"]["summary"]
    assert dsum["changed"] > 0 and dsum["added"] > 0
    changes = {c["path"]: c
               for c in diff_payload["diff"]["changes"]}
    assert changes["readiness_matrix.rows[2].status"]["after"] == \
        "partial_pass_queue_closed"
    assert changes["metrics[0].value"]["after"] == 0
    assert changes["metrics[1].status"]["after"] == "value"
    assert "resolved" not in \
        changes["open_production_blockers[3].status"]["after"]
    # 盘上 v1 三冻结件未被本包覆写（只读红线）
    assert hashing.sha256_file(
        str(s22.REPO / "out/v3-tl6/health-projection.json")) == \
        s22.FROZEN_V1_SHA256
    assert hashing.sha256_file(
        str(s22.REPO / "out/v3-tl6/health-projection-gate.json")
    ).startswith("66135e61")
    # 盘上三新产物与同参重建逐字节一致（byte-exact 落盘验证）
    assert (s22.REPO / "out/v3-tl6/health-projection-v2.json").read_bytes() \
        == proj_bytes
    on_disk_gate = json.loads(
        (s22.REPO / "out/v3-tl6/health-projection-gate-v2.json")
        .read_text(encoding="utf-8"))
    assert on_disk_gate["gate_record"]["projection_ref"]["sha256"] == \
        proj_sha
    on_disk_diff = json.loads(
        (s22.REPO / "out/v3-tl6/projection-diff-v1-to-v2.json")
        .read_text(encoding="utf-8"))
    assert on_disk_diff["diff"]["summary"] == dsum
