"""S16 会话测试：TL-6 环路健康度/readiness 投影（SPEC-v3.0-PROPOSAL §4）。

覆盖：
- 四指标投影正负向（纯函数、fail-closed 语义）：
  * 人工队列长度：open 计数+reason 分布+事件序号时间窗（禁 wall-clock）、
    终态事件闭合后清零、账本链篡改 → blocked（trust invalid，无数值）；
  * Critic 一致率：分母 0 → not_available（不冒充数值）、有人工 verdict →
    比值、record hash 不符 → blocked、invalid run 不进分母；
  * Proposer 接受率：human_approved_machine_blocked → adoption=0/2（机器
    门 fail 原因在案）、机器门全绿 → 1.0、无完整 disposition →
    not_available、处置记录缺 fact_refs → blocked；
  * 跨板回测不回退率：空执行面 → not_available（语料在库≠执行分母）、
    有回测 → 比值；
- 辅助刻度：DAG blocked/physics coverage（coverage≠pass）/freshness
  （revision 绑定，wall-clock=not_available）/queue aging（事件序号）；
- readiness matrix：9 行+production_signoff_ready=false+TL-6 自引行+
  缺证据指针 raise；
- open_production_blockers：BL-1..BL-4；
- gate 谓词四条（投影可计算性/分母诚实性/not_available 不冒充数值/证据
  hash 对账）正负向+gate record（result=pass 仅断言投影完整性，exit_gate
  独立=blocked、closure_claimed=false）；
- byte-exact：同参两次 build canonical 字节一致。

纯内存构造（生成器模式）：零子进程/零写盘/零网络；仅集成锚一条按
test_tl5_s10_batch 模式 importlib 装载编排脚本，对 out/ 实况只读复核。
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


# ---------------------------------------------------------------------------
# 指标一：人工队列长度
# ---------------------------------------------------------------------------

def test_manual_queue_value_reason_window():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-x", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    m = hp.project_manual_queue(
        events, ledger_path="out/x/queue-event-ledger.jsonl",
        ledger_sha256=_sha("ledger"))
    assert m["status"] == "value" and m["value"] == 1
    for k in hp.DESCRIPTOR_KEYS:
        assert k in m
    assert m["denominator"] is None
    assert m["denominator_basis"] == "count_metric_no_denominator"
    assert m["baseline"] is None and m["baseline_basis"]
    assert m["aux"]["by_reason_code"] == {"critic_auto_route_blocked": 1}
    assert m["aux"]["open_items"] == ["ITEM-x"]
    w = m["window"]
    assert w["unit"] == "ledger_event_seq"
    assert w["wall_clock"].startswith("not_used")
    assert m["aux"]["human_capacity"].startswith("not_available")


def test_manual_queue_closed_item_excluded():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-x", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    _ev(events, event="assign", item_id="ITEM-x", seq=1)
    _ev(events, event="approve", item_id="ITEM-x", seq=2,
        actor="human-final", actor_role="human_final")
    m = hp.project_manual_queue(
        events, ledger_path="l.jsonl", ledger_sha256=_sha("l"))
    assert m["status"] == "value" and m["value"] == 0
    assert m["aux"]["open_items"] == []
    assert m["window"]["events_since_oldest_enqueue"] is None


def test_manual_queue_blocked_on_chain_tamper():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-x", seq=0,
        reason="r", critic_ref=_sha("rec"))
    tampered = [dict(events[0], reason_code="forged")]
    m = hp.project_manual_queue(
        tampered, ledger_path="l.jsonl", ledger_sha256=_sha("l"))
    assert m["status"] == "blocked"
    assert m["value"] is None and m["numerator"] is None
    assert m["reason"].startswith("trust_invalid")


def test_manual_queue_evidence_pointer_format():
    m = hp.project_manual_queue(
        [], ledger_path="out/x/ledger.jsonl", ledger_sha256=_sha("l"))
    e = m["evidence"][0]
    assert e["path"] == "out/x/ledger.jsonl"
    assert e["sha256"] == _sha("l") and e["sha256_8"] == _sha("l")[:8]


# ---------------------------------------------------------------------------
# 指标二：Critic 一致率
# ---------------------------------------------------------------------------

def _critic_run(**over):
    base = {"run_id": "CR-run-r1", "critic_status": "executed",
            "input_hashes_match": True, "critic_ref": _sha("rec"),
            "in_calibrated_range": False, "flags_total": 7,
            "abstain_count": 1,
            "board_flag_counts": {"bm11": 5, "launchxl": 2}}
    base.update(over)
    return base


def _record_evidence():
    return [{"run_id": "CR-run-r1", "path": "out/x/record.json",
             "sha256": _sha("rec")}]


def test_critic_agreement_not_available_zero_denominator():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-r1", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    m = hp.project_critic_agreement([_critic_run()], events,
                                    record_evidence=_record_evidence())
    assert m["status"] == "not_available"
    assert m["denominator"] == 0
    assert m["value"] is None and m["numerator"] is None
    assert m["reason"].startswith("denominator_zero")
    aux = m["aux"]
    assert aux["runs_executed_valid"] == 1
    assert aux["runs_with_human_verdict"] == 0
    for k in ("precision", "recall", "fpr", "fnr"):
        assert aux[k].startswith("not_available")
    assert aux["abstain_count"] == 1 and aux["flags_total"] == 7
    assert aux["worst_board_by_flags"] == "bm11"
    assert aux["in_calibrated_range_observed"] == [False]


def test_critic_agreement_value_with_human_verdict():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-r1", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    _ev(events, event="assign", item_id="ITEM-r1", seq=1)
    _ev(events, event="review", item_id="ITEM-r1", seq=2,
        actor="human-reviewer", actor_role="human_reviewer")
    _ev(events, event="approve", item_id="ITEM-r1", seq=3,
        actor="human-final", actor_role="human_final")
    m = hp.project_critic_agreement(
        [_critic_run(human_supports_flags=1)], events,
        record_evidence=_record_evidence())
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (1, 1, 1.0)


def test_critic_agreement_blocked_on_hash_mismatch():
    m = hp.project_critic_agreement(
        [_critic_run(input_hashes_match=False)], [],
        record_evidence=_record_evidence())
    assert m["status"] == "blocked"
    assert m["reason"].startswith("trust_invalid")


def test_critic_agreement_invalid_run_not_in_denominator():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-r1", seq=0,
        reason="r", critic_ref=_sha("rec"))
    m = hp.project_critic_agreement(
        [_critic_run(critic_status="invalid")], events,
        record_evidence=_record_evidence())
    assert m["status"] == "not_available"
    assert m["aux"]["runs_executed_valid"] == 0


# ---------------------------------------------------------------------------
# 指标三：Proposer 接受率
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


def _patch_evidence():
    return [{"path": "out/x/patch.json", "sha256": _sha("p")}]


def test_proposer_acceptance_machine_blocked_zero_over_two():
    m = hp.project_proposer_acceptance(
        _candidates(), _disposition(), _machine_gate_blocked(),
        patch_evidence=_patch_evidence())
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"], m["value"]) == (0, 2, 0.0)
    assert m["aux"]["adoption_status"] == "human_approved_machine_blocked"
    assert m["aux"]["machine_gate_fail_reason"] and "机器门 fail" \
        in m["aux"]["machine_gate_fail_reason"]
    kv = m["aux"]["by_kind_version"]
    assert kv["policy_parameter_candidate@closed_form_smoke_v1"][
        "blocked"] == 2
    rbw = m["aux"]["reject_blocked_waive_reasons"]
    assert (rbw["reject"], rbw["waive"], rbw["blocked"]) == (0, 0, 2)
    cov = m["aux"]["proposal_coverage"]
    assert cov == {"profiles_with_candidates": 2, "profiles_in_scope": 2}
    assert m["aux"]["proposal_count_floor"].startswith("not_available")


def test_proposer_acceptance_one_when_gate_green():
    gate = {k: True for k in _machine_gate_blocked()}
    m = hp.project_proposer_acceptance(
        _candidates(), _disposition(), gate,
        patch_evidence=_patch_evidence())
    assert m["status"] == "value" and m["value"] == 1.0
    assert m["aux"]["adoption_status"] == "adopted"


def test_proposer_acceptance_not_available_without_disposition():
    m = hp.project_proposer_acceptance(
        _candidates(), {"kind": None, "fact_refs": []},
        _machine_gate_blocked(), patch_evidence=_patch_evidence())
    assert m["status"] == "not_available"
    assert m["denominator"] == 0 and m["value"] is None


def test_proposer_acceptance_blocked_on_bad_disposition_record():
    m = hp.project_proposer_acceptance(
        _candidates(), {"kind": "accept"}, _machine_gate_blocked(),
        patch_evidence=_patch_evidence())
    assert m["status"] == "blocked"
    assert m["reason"].startswith("trust_invalid")


# ---------------------------------------------------------------------------
# 指标四：跨板回测不回退率
# ---------------------------------------------------------------------------

def test_non_regression_not_available_without_backtests():
    m = hp.project_non_regression(
        [], evidence=[{"path": "out/x/gate.json", "sha256": _sha("g")}])
    assert m["status"] == "not_available"
    assert m["denominator"] == 0 and m["value"] is None
    assert m["aux"]["holdout_corpus_available"] is True
    assert m["aux"]["holdout_execution_denominator"] == 0
    assert "D18" in m["reason"]


def test_non_regression_value_with_backtests():
    backtests = [{"board": "h1", "metrics_ok": True, "whitelist_ok": True},
                 {"board": "h2", "metrics_ok": False,
                  "whitelist_ok": True}]
    m = hp.project_non_regression(
        backtests, evidence=[{"path": "out/x/gate.json",
                              "sha256": _sha("g")}])
    assert m["status"] == "value" and m["value"] == 0.5
    assert (m["numerator"], m["denominator"]) == (1, 2)


# ---------------------------------------------------------------------------
# 辅助刻度 / readiness / blockers
# ---------------------------------------------------------------------------

def test_auxiliary_scales_content():
    aux = hp.auxiliary_scales(
        tl3_coverage={"required_scope": ["PHY-IMP-1"],
                      "covered_scope": ["PHY-IMP-1"], "missing_scope": [],
                      "coverage_complete": True},
        dag_nodes=[{"node": "a"}, {"node": "b"}, {"node": "c"}],
        queue_summary={"oldest_item_id": "ITEM-run-r1",
                       "oldest_item_seq": 0, "last_event_seq": 0,
                       "age_events": 0},
        physics_report_revision="smoke-r1",
        gate_inputs_revision="smoke-r1")
    assert aux["dag_blocked"]["count"] == 3
    pc = aux["physics_coverage"]
    assert pc["coverage_complete"] is True and pc["gate_result"] == "fail"
    assert "不等于结果通过" in pc["note"]
    fr = aux["required_report_freshness"]
    assert fr["fresh_at_projection"] is True
    assert fr["wall_clock_age"].startswith("not_available")
    qa = aux["queue_aging"]
    assert qa["unit"] == "ledger_event_seq" and qa["age_events"] == 0
    for v in aux["not_tracked_here"].values():
        assert "not_available" in v


def test_readiness_matrix_rows_and_self_reference():
    ev = {"TL-0-G1": [{"path": "out/a.json", "sha256": _sha("a")}],
          "TL-1-G1": [{"path": "out/b.json", "sha256": _sha("b")}],
          "TL-2": [{"path": "out/c.json", "sha256": _sha("c")}],
          "TL-3-G1": [{"path": "out/d.json", "sha256": _sha("d")}],
          "TL-4-G": [{"path": "out/e.json", "sha256": _sha("e")}],
          "TL-5-G": [{"path": "out/f.json", "sha256": _sha("f")}],
          "TD7-QUAL-G": [{"path": "out/g.json", "sha256": _sha("g")}],
          "production_signoff_ready": [{"path": "out/h.json",
                                        "sha256": _sha("h")}]}
    matrix = hp.readiness_matrix(ev)
    assert len(matrix["rows"]) == 9
    assert matrix["production_signoff_ready"] is False
    by_key = {r["gate"]: r for r in matrix["rows"]}
    assert by_key["TL-0-G1"]["status"] == "pass"
    assert by_key["TL-3-G1"]["status"] == "fail"
    assert by_key["TL-4-G"]["status"] == "fail"
    assert by_key["TL-5-G"]["status"] == "pass"
    assert by_key["TD7-QUAL-G"]["status"] == "archived"
    tl6 = by_key["TL-6"]
    assert tl6["status"] == "blocked"
    assert tl6["evidence"][0]["self_reference"] is True
    assert tl6["evidence"][0]["sha256"] is None
    with pytest.raises(ValueError, match="缺证据指针"):
        hp.readiness_matrix({"TL-0-G1": ev["TL-0-G1"]})


def test_open_blockers_four():
    blockers = hp.open_production_blockers()
    assert [b["blocker_id"] for b in blockers] == \
        ["BL-1", "BL-2", "BL-3", "BL-4"]
    titles = " ".join(b["title"] for b in blockers)
    for kw in ("布线引擎", "TL-3", "TL-4", "Critic"):
        assert kw in titles


# ---------------------------------------------------------------------------
# 载荷组装 + gate 谓词
# ---------------------------------------------------------------------------

def _fixtures_and_projection():
    events = []
    _ev(events, event="enqueue", item_id="ITEM-r1", seq=0,
        reason="critic_auto_route_blocked", critic_ref=_sha("rec"))
    metrics = [
        hp.project_manual_queue(events, ledger_path="out/l.jsonl",
                                ledger_sha256=_sha("l")),
        hp.project_critic_agreement([_critic_run()], events,
                                    record_evidence=_record_evidence()),
        hp.project_proposer_acceptance(
            _candidates(), _disposition(), _machine_gate_blocked(),
            patch_evidence=_patch_evidence()),
        hp.project_non_regression(
            [], evidence=[{"path": "out/gate.json",
                           "sha256": _sha("g")}]),
    ]
    aux = hp.auxiliary_scales(
        tl3_coverage={"required_scope": ["PHY-IMP-1"],
                      "covered_scope": ["PHY-IMP-1"], "missing_scope": [],
                      "coverage_complete": True},
        dag_nodes=[{"node": "a"}, {"node": "b"}, {"node": "c"}],
        queue_summary={"oldest_item_id": "ITEM-r1", "oldest_item_seq": 0,
                       "last_event_seq": 0, "age_events": 0},
        physics_report_revision="smoke-r1",
        gate_inputs_revision="smoke-r1")
    ev = {"TL-0-G1": [{"path": "out/a.json", "sha256": _sha("a")}],
          "TL-1-G1": [{"path": "out/b.json", "sha256": _sha("b")}],
          "TL-2": [{"path": "out/c.json", "sha256": _sha("c")}],
          "TL-3-G1": [{"path": "out/d.json", "sha256": _sha("d")}],
          "TL-4-G": [{"path": "out/e.json", "sha256": _sha("e")}],
          "TL-5-G": [{"path": "out/f.json", "sha256": _sha("f")}],
          "TD7-QUAL-G": [{"path": "out/g.json", "sha256": _sha("g")}],
          "production_signoff_ready": [{"path": "out/h.json",
                                        "sha256": _sha("h")}]}
    matrix = hp.readiness_matrix(ev)
    projection = hp.build_projection(
        session_date="2026-09-05", evaluator_code_sha256=_sha("mod"),
        metrics=metrics, aux_scales=aux, matrix=matrix,
        blockers=hp.open_production_blockers(),
        corpus_denominator=hp.corpus_denominator_block(
            {"pcbbenchmarks-r1": 2, "pcbench-r1": 81, "kicad-demos-r1": 17},
            {}))
    measured = {"out/l.jsonl": _sha("l"), "out/x/record.json": _sha("rec"),
                "out/x/patch.json": _sha("p"), "out/gate.json": _sha("g"),
                "out/a.json": _sha("a"), "out/b.json": _sha("b"),
                "out/c.json": _sha("c"), "out/d.json": _sha("d"),
                "out/e.json": _sha("e"), "out/f.json": _sha("f"),
                "out/g.json": _sha("g"), "out/h.json": _sha("h")}
    return projection, measured


def test_build_projection_and_all_predicates_pass():
    projection, measured = _fixtures_and_projection()
    assert projection["corpus_denominator"]["total_boards"] == 100
    assert projection["readiness_matrix"]["production_signoff_ready"] \
        is False
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == []
    assert all(p["value"] for p in predicates)
    assert [p["id"] for p in predicates] == [
        "projection_computability", "denominator_honesty",
        "not_available_not_value", "evidence_hash_reconciliation"]


def test_gate_record_pass_projection_but_exit_blocked():
    projection, measured = _fixtures_and_projection()
    proj_sha = hashing.sha256_text(
        hashing.canonical_json_bytes(projection).decode("utf-8"))
    predicates, failures = hp.gate_predicates(projection, measured)
    gate = hp.build_gate_record(
        projection=projection, projection_sha256=proj_sha,
        projection_path="out/v3-tl6/health-projection.json",
        predicates=predicates, failure_codes=failures, inputs=[],
        evaluator_code_sha256=_sha("mod"))
    assert gate["gate_record"]["result"] == "pass"
    assert gate["gate_record"]["failure_codes"] == []
    exit_gate = gate["gate_record"]["exit_gate"]
    assert exit_gate["gate_id"] == "TL-6-G"
    assert exit_gate["result"] == "blocked"
    assert exit_gate["closure_claimed"] is False
    assert exit_gate["open_blockers"] == ["BL-1", "BL-2", "BL-3", "BL-4"]
    assert "不断言 TL-6 出口门通过" in exit_gate["note"]


def test_predicate_p2_fails_on_arithmetic_mismatch():
    projection, measured = _fixtures_and_projection()
    for m in projection["metrics"]:
        if m["metric_id"] == "proposer_acceptance_rate":
            m["value"] = 0.5  # 与 0/2 不符
    _, failures = hp.gate_predicates(projection, measured)
    assert any(f.startswith("denominator_dishonest") for f in failures)


def test_predicate_p3_fails_when_na_carries_value():
    projection, measured = _fixtures_and_projection()
    for m in projection["metrics"]:
        if m["status"] == "not_available":
            m["value"] = 0.85  # 冒充数值
    _, failures = hp.gate_predicates(projection, measured)
    assert any(f.startswith("na_mimics_value") for f in failures)


def test_predicate_p4_fails_on_hash_mismatch():
    projection, measured = _fixtures_and_projection()
    measured["out/l.jsonl"] = _sha("forged")
    _, failures = hp.gate_predicates(projection, measured)
    assert any(f.startswith("evidence_hash_mismatch") for f in failures)


def test_predicate_p1_fails_on_missing_descriptor():
    projection, measured = _fixtures_and_projection()
    del projection["metrics"][0]["threshold"]
    _, failures = hp.gate_predicates(projection, measured)
    assert any(f.startswith("projection_incomplete") for f in failures)


def test_build_projection_rejects_bad_metric_sets():
    projection, _ = _fixtures_and_projection()
    with pytest.raises(ValueError, match="指标缺失"):
        hp.build_projection(
            session_date="2026-09-05", evaluator_code_sha256=_sha("m"),
            metrics=projection["metrics"][:3], aux_scales={},
            matrix=projection["readiness_matrix"], blockers=[],
            corpus_denominator={})
    bad = dict(projection["metrics"][0], metric_id="made_up")
    with pytest.raises(ValueError, match="未知指标"):
        hp.build_projection(
            session_date="2026-09-05", evaluator_code_sha256=_sha("m"),
            metrics=[bad], aux_scales={}, matrix=None, blockers=[],
            corpus_denominator={})


def test_evidence_ref_validation():
    with pytest.raises(ValueError, match="非法路径"):
        hp.evidence_ref("C:\\abs\\path.json", _sha("x"))
    with pytest.raises(ValueError, match="非法路径"):
        hp.evidence_ref("out/../secrets.json", _sha("x"))
    with pytest.raises(ValueError, match="非法 sha256"):
        hp.evidence_ref("out/x.json", "deadbeef")


def test_projection_payload_byte_exact_rebuild():
    p1, _ = _fixtures_and_projection()
    p2, _ = _fixtures_and_projection()
    assert hashing.canonical_json_bytes(p1) == \
        hashing.canonical_json_bytes(p2)


# ---------------------------------------------------------------------------
# 集成锚：真实 out/ 实况投影（只读）——口径与门状态绑定
# ---------------------------------------------------------------------------

_S16_SPEC = importlib.util.spec_from_file_location(
    "s16_health_orchestrate",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "s16_health_orchestrate.py"))
s16 = importlib.util.module_from_spec(_S16_SPEC)
_S16_SPEC.loader.exec_module(s16)


def test_real_out_projection_integration():
    hashes = s16.measure_hashes()
    projection, _, _ = s16.build_everything(hashes)
    measured = {s16.EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    assert failures == [] and all(p["value"] for p in predicates)
    metrics = {m["metric_id"]: m for m in projection["metrics"]}
    # S17 起 ITEM-run-r1 已按人工处置闭合（QE-000001 assign/QE-000002
    # approve，APR-0007）：out/ 实况活算的队列长度=0（S16 冻结投影文件
    # 仍记 1 不受影响；本锚断言的是实况重算值）。
    assert metrics["manual_queue_length"]["value"] == 0
    # 人工 verdict 出现（APR-0007 accept=支持旗标 advisory 登记）：
    # 一致率首次可算 = 支持旗标 1/有效分歧项 1（s16 编排 fail-closed
    # 装配，evidence 绑 disposition 文件实测 hash）。
    agreement = metrics["critic_agreement_rate"]
    assert agreement["status"] == "value"
    assert agreement["numerator"] == 1 and agreement["denominator"] == 1
    assert agreement["value"] == 1.0
    assert metrics["proposer_acceptance_rate"]["value"] == 0.0
    assert metrics["cross_board_non_regression_rate"]["status"] == \
        "not_available"
    assert projection["corpus_denominator"]["total_boards"] == 100
    assert projection["auxiliary_scales"]["dag_blocked"]["count"] == 3
