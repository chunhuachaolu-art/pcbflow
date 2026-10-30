"""TL-1 裁决账本与双阶段 Judge/disposition/gate 合成测试（SPEC-v3.0 TD1/§1.2-§1.5）。

全部合成数据：不依赖真实板卡、外部执行或既有 out/ 产物。
断言的是红线行为：hash 链可验、trust 白名单 fail-closed、缺 pre 的
post 不可采纳、fact 无处置语义、waive 无 policy 即无效、处置无门写权、
gate 由机器谓词计算人工不可直写。
"""

import copy

import pytest

from pcbflow import disposition, gate, hashing, judge, ledger


def _h(ch: str) -> str:
    return ch * 64


# ---------------------------------------------------------------------------
# 合成工厂：ledger
# ---------------------------------------------------------------------------

def _entry_body(**over):
    """合法 entry 构造体（make_entry 关键字参数集）。"""
    body = {
        "entry_id": "E-0000",
        "entry_kind": "judge_pre",
        "authority": "deterministic_evaluator",
        "trust_level": "observed",
        "schema_validation": ledger.make_schema_validation(
            "decision_ledger_entry"),
        "project_id": "revc-coreboard",
        "profile_id": "revc-tbd1",
    }
    body.update(over)
    return body


def _chain3():
    entries = []
    for i, kind in enumerate(("judge_pre", "execution", "judge_post")):
        entries, _ = ledger.append(
            entries, _entry_body(entry_id=f"E-{i:04d}", entry_kind=kind))
    return entries


# ---------------------------------------------------------------------------
# 链：构造 / 篡改 / seq / Genesis
# ---------------------------------------------------------------------------

def test_make_entry_genesis_and_body_hash():
    entry = ledger.make_entry(None, **_entry_body())
    assert entry["entry_seq"] == 0
    assert entry["prev_entry_sha256"] is None
    assert entry["ledger_head_sha256"] == hashing.sha256_text(
        "GENESIS:" + entry["entry_sha256"])
    # entry_body_sha256 剔除 entry_sha256 与 ledger_head_sha256 两字段
    body = {k: v for k, v in entry.items()
            if k not in ("entry_sha256", "ledger_head_sha256")}
    assert entry["entry_sha256"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(body))
    assert ledger.verify_chain([entry]) == []


def test_make_entry_schema_violation_raises():
    with pytest.raises(ValueError):
        ledger.make_entry(None, **_entry_body(entry_kind="nonsense_kind"))
    with pytest.raises(ValueError):
        ledger.make_entry(None, **{"authority": "deterministic_evaluator",
                                   "trust_level": "observed",
                                   "entry_kind": "judge_pre",
                                   "schema_validation":
                                       ledger.make_schema_validation(
                                           "decision_ledger_entry")})
        # ↑ 缺 entry_id：schema required 缺项 fail-closed


def test_chain_three_legal_entries_verify_clean():
    entries = _chain3()
    assert [e["entry_seq"] for e in entries] == [0, 1, 2]
    assert entries[1]["prev_entry_sha256"] == entries[0]["entry_sha256"]
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []


def test_chain_tamper_detected():
    entries = _chain3()
    entries[1] = dict(entries[1], project_id="evil-board")
    errs = ledger.verify_chain(entries)
    assert errs
    assert any("entry_sha256" in e for e in errs)


def test_chain_seq_gap_detected():
    entries = _chain3()
    entries[2]["entry_seq"] = 9  # 跳号（hash 同时失配，但 seq 错误必须单独报出）
    errs = ledger.verify_chain(entries)
    assert any("entry_seq" in e for e in errs)


def test_chain_genesis_prev_must_be_null():
    entries = _chain3()
    entries[0] = dict(entries[0], prev_entry_sha256=_h("9"))
    errs = ledger.verify_chain(entries)
    assert any("prev_entry_sha256" in e for e in errs)


# ---------------------------------------------------------------------------
# trust_level 白名单（validator 强制）
# ---------------------------------------------------------------------------

def test_trust_critic_model_observed_rejected():
    entry = ledger.make_entry(
        None, **_entry_body(authority="critic_model", trust_level="observed"))
    errs = ledger.verify_chain([entry])
    assert any("trust_level" in e for e in errs)


def test_trust_human_disposition_untrusted_accepted():
    entry = ledger.make_entry(
        None, **_entry_body(entry_kind="disposition", authority="human",
                            trust_level="untrusted", entry_id="E-D1",
                            disposition_refs=["D-0001"]))
    assert ledger.verify_chain([entry]) == []


def test_trust_human_observed_rejected():
    entry = ledger.make_entry(
        None, **_entry_body(entry_kind="disposition", authority="human",
                            trust_level="observed"))
    errs = ledger.verify_chain([entry])
    assert any("trust_level" in e for e in errs)
    # human 也不得出现在非 disposition 类 entry（处置不是事实）
    entry2 = ledger.make_entry(
        None, **_entry_body(entry_kind="judge_pre", authority="human",
                            trust_level="untrusted"))
    errs2 = ledger.verify_chain([entry2])
    assert any("disposition" in e for e in errs2)


def test_trust_note_documents_three_levels():
    for word in ("untrusted", "observed", "verified"):
        assert word in ledger.trust_policy_note


# ---------------------------------------------------------------------------
# supersedes（追加式结构校验）
# ---------------------------------------------------------------------------

def test_supersedes_missing_reference_rejected():
    entries = []
    entries, _ = ledger.append(entries, _entry_body(entry_id="E-0000"))
    entries, _ = ledger.append(entries, _entry_body(
        entry_id="E-0001", supersedes=[_h("f")]))
    errs = ledger.verify_supersedes(entries)
    assert any("不存在" in e for e in errs)


def test_supersedes_double_supersede_rejected():
    entries = []
    entries, e0 = ledger.append(entries, _entry_body(entry_id="E-0000"))
    target = e0["entry_sha256"]
    entries, _ = ledger.append(entries, _entry_body(
        entry_id="E-0001", supersedes=[target]))
    entries, _ = ledger.append(entries, _entry_body(
        entry_id="E-0002", supersedes=[target]))  # 第二次 supersede
    errs = ledger.verify_supersedes(entries)
    assert any("重复 supersede" in e for e in errs)


# ---------------------------------------------------------------------------
# append fail-closed 与 checkpoint
# ---------------------------------------------------------------------------

def test_append_fail_closed_on_broken_chain():
    entries = _chain3()
    entries[1] = dict(entries[1], project_id="evil-board")
    with pytest.raises(ValueError):
        ledger.append(entries, _entry_body(entry_id="E-X"))


def test_checkpoint_verify_ok_and_truncation_detected():
    entries = _chain3()
    ckpt = ledger.make_checkpoint(entries, "CK-0001")
    assert ckpt["entry_count"] == 3
    assert ckpt["entry_seq"] == 2
    assert ckpt["entries_cum_sha256"] == hashing.sha256_text(
        "".join(e["entry_sha256"] for e in entries))
    assert ledger.verify_against_checkpoint(entries, ckpt) == []
    # 截断后与 checkpoint 不一致
    errs = ledger.verify_against_checkpoint(entries[:2], ckpt)
    assert errs
    assert any("entry_count" in e for e in errs)


# ---------------------------------------------------------------------------
# 合成工厂：judge
# ---------------------------------------------------------------------------

def _pre():
    return judge.build_pre(
        execution_id="EXEC-0001",
        project_id="revc-coreboard",
        profile_id="revc-tbd1",
        candidate_id="CAND-0001",
        source_snapshot_sha256=_h("a"),
        toolchain_lock_sha256=_h("b"),
        executor={"backend": "deterministic-internal", "protocol": "internal",
                  "version": "1", "capability": "route-v1"},
        write_scope="staging_only",
        allowlist=("staging/board.kicad_pcb",),
        required_checks=("drc_batch", "drc_final"),
        upstream_hashes={"constraints_sha256": _h("c")},
        patch_preconditions=())


def _ctx():
    return {"source_snapshot_sha256": _h("a"),
            "toolchain_lock_sha256": _h("b"),
            "constraints_sha256": _h("c")}


def _post(**over):
    kw = dict(
        execution_id="EXEC-0001",
        pre_record=_pre(),
        output_hash=_h("d"),
        l1_legal=True,
        layer_pure=True,
        drc_batch_ref=_h("e"),
        drc_final_ref=_h("f"),
        erc_ref=_h("1"),
        test_manifest_hash=_h("2"),
        replay_ref=_h("3"),
        solver={"status": "UNSAT", "proof_ref": _h("7")})
    kw.update(over)
    return judge.build_post(**kw)


# ---------------------------------------------------------------------------
# judge：evaluate_pre fail-closed 各项
# ---------------------------------------------------------------------------

def test_pre_ok_with_full_context():
    result = judge.evaluate_pre(_pre(), _ctx())
    assert result == {"pre_ok": True, "failed": []}


def test_pre_toolchain_not_64hex_rejected():
    record = _pre()
    record["toolchain_lock_sha256"] = "not-a-hash"
    result = judge.evaluate_pre(record, _ctx())
    assert result["pre_ok"] is False
    assert any("toolchain_lock_sha256" in e for e in result["failed"])


def test_pre_upstream_required_hash_missing_rejected():
    ctx = dict(_ctx())
    del ctx["constraints_sha256"]
    result = judge.evaluate_pre(_pre(), ctx)
    assert result["pre_ok"] is False
    assert any("constraints_sha256" in e for e in result["failed"])
    # 声明与实测不一致同样拒绝
    ctx2 = dict(_ctx(), constraints_sha256=_h("e"))
    assert judge.evaluate_pre(_pre(), ctx2)["pre_ok"] is False


def test_pre_write_scope_illegal_rejected():
    record = _pre()
    record["write_scope"] = "live_board"
    result = judge.evaluate_pre(record, _ctx())
    assert result["pre_ok"] is False
    assert any("write_scope" in e for e in result["failed"])


def test_pre_empty_allowlist_with_required_checks_rejected():
    record = _pre()
    record["allowlist"] = []
    result = judge.evaluate_pre(record, _ctx())
    assert result["pre_ok"] is False
    assert any("allowlist" in e for e in result["failed"])


def test_pre_patch_precondition_unmet_rejected():
    record = _pre()
    record["patch_preconditions"] = [{"id": "base_hash_match",
                                      "value": False}]
    result = judge.evaluate_pre(record, _ctx())
    assert result["pre_ok"] is False
    assert any("precondition" in e for e in result["failed"])


# ---------------------------------------------------------------------------
# judge：evaluate_post / adoption / facts
# ---------------------------------------------------------------------------

def test_post_ok_full_evidence():
    result = judge.evaluate_post(_post())
    assert result["post_ok"] is True
    assert result["failed"] == []
    assert result["unknown_solver"] is False


def test_post_missing_output_hash_fails():
    result = judge.evaluate_post(_post(output_hash=None))
    assert result["post_ok"] is False
    assert any("output_hash" in e for e in result["failed"])


def test_post_missing_drc_refs_fail():
    result = judge.evaluate_post(_post(drc_batch_ref=None, drc_final_ref=None))
    assert result["post_ok"] is False
    assert any("drc_batch_ref" in e for e in result["failed"])
    assert any("drc_final_ref" in e for e in result["failed"])


def test_post_solver_unknown_is_three_state_not_fail():
    result = judge.evaluate_post(
        _post(solver={"status": "UNKNOWN", "proof_ref": None}))
    assert result["unknown_solver"] is True
    assert result["post_ok"] is True  # 三态如实：UNKNOWN 不是 fail
    # 无 proof 只能 UNKNOWN：SAT 声称无 proof → fail
    sat_no_proof = judge.evaluate_post(
        _post(solver={"status": "SAT", "proof_ref": None}))
    assert sat_no_proof["post_ok"] is False


def test_post_external_status_fail():
    result = judge.evaluate_post(_post(physics_status="fail"))
    assert result["post_ok"] is False
    assert any("physics_status" in e for e in result["failed"])
    assert judge.evaluate_post(_post(rollback_status="failed"))["post_ok"] is False


def test_adoption_check_requires_pre():
    pre = _pre()
    post = _post()
    assert post["pre_record_ref"] == judge.pre_record_sha256(pre)
    assert judge.adoption_check({judge.pre_record_sha256(pre)}, post) == []
    errs = judge.adoption_check(set(), post)
    assert errs
    assert any("不可采纳" in e for e in errs)


def test_build_facts_forbidden_key_raises():
    facts = judge.build_facts([
        {"fact_id": "F-1", "observer": "kicad_cli",
         "observation": {"kind": "count", "value": 3, "unit": "errors"}}])
    assert facts[0]["immutable"] is True
    # observation 内含 'accept'（处置语义禁区）→ ValueError
    with pytest.raises(ValueError):
        judge.build_facts([
            {"fact_id": "F-2", "observer": "kicad_cli",
             "observation": {"kind": "boolean", "value": True,
                             "accept": True}}])
    # 顶层含 'waive' 同样拒绝
    with pytest.raises(ValueError):
        judge.build_facts([
            {"fact_id": "F-3", "observer": "replay",
             "waive": True,
             "observation": {"kind": "hash_equality", "value": "same"}}])


def test_facts_bundle_hash_deterministic():
    facts = judge.build_facts([
        {"fact_id": "F-1", "observer": "replay",
         "observation": {"kind": "hash_equality", "value": "same"}}])
    assert judge.facts_bundle_hash(facts) == judge.facts_bundle_hash(
        copy.deepcopy(facts))


# ---------------------------------------------------------------------------
# 合成工厂：disposition
# ---------------------------------------------------------------------------

_POLICY = {
    "waivable_check_ids": ["CHK-DRC-FINAL"],
    "allowed_reason_codes": ["R-QUALITY-TOL"],
    "allowed_approver_roles": ["senior_engineer"],
}


def _disp(**over):
    kw = dict(
        disposition_id="D-0001",
        fact_refs=["CHK-DRC-FINAL"],
        kind="waive",
        scope="checker",
        rationale_code="R-QUALITY-TOL",
        approver="zhang",
        approver_role="senior_engineer",
        waiver_policy_ref="POL-WAIVE-1",
        expiry="REV-D")
    kw.update(over)
    return disposition.build_disposition(**kw)


# ---------------------------------------------------------------------------
# disposition：waiver policy / 门写禁区 / 追加式索引
# ---------------------------------------------------------------------------

def test_waive_without_policy_invalid():
    errs = disposition.check_waiver_policy(_disp(), {})
    assert errs
    assert any("policy" in e for e in errs)


def test_waive_policy_missing_list_fail_closed():
    # policy 缺 allowed_approver_roles 键 → 空集全拒
    policy = {"waivable_check_ids": ["CHK-DRC-FINAL"],
              "allowed_reason_codes": ["R-QUALITY-TOL"]}
    errs = disposition.check_waiver_policy(_disp(), policy)
    assert any("allowed_approver_roles" in e for e in errs)


def test_waive_unauthorized_role_invalid():
    policy = dict(_POLICY, allowed_approver_roles=["chief_engineer"])
    errs = disposition.check_waiver_policy(_disp(), policy)
    assert any("approver_role" in e for e in errs)


def test_waive_non_waivable_fact_invalid():
    errs = disposition.check_waiver_policy(
        _disp(fact_refs=["CHK-SAFE-1", "CHK-DRC-FINAL"]), _POLICY)
    assert any("CHK-SAFE-1" in e for e in errs)


def test_waive_full_policy_valid():
    assert disposition.check_waiver_policy(_disp(), _POLICY) == []
    # 非 waive 处置不受 waiver policy 约束
    assert disposition.check_waiver_policy(
        _disp(kind="reject"), {}) == []


def test_validate_no_gate_write_detects_forbidden_keys():
    assert disposition.validate_no_gate_write(_disp()) == []
    smuggled = dict(_disp(), gate_pass=True)
    errs = disposition.validate_no_gate_write(smuggled)
    assert any("gate_pass" in e for e in errs)
    nested = dict(_disp(), rationale_text="ok")
    nested_bad = {"disposition_id": "D-9", "extra": {"signoff_pass": True}}
    assert any("signoff_pass" in e
               for e in disposition.validate_no_gate_write(nested_bad))
    del nested  # 仅示意合法嵌套不误报


def test_apply_supersedes_marks_and_preserves_original():
    old = _disp(disposition_id="D-0001")
    new = _disp(disposition_id="D-0002", kind="reject")
    index = {"D-0001": old}
    old_snap = copy.deepcopy(old)
    index_snap = copy.deepcopy(index)
    new_index = disposition.apply_supersedes(index, "D-0001", new)
    # 原 dict 与原索引内容不变（追加式：不改写既有记录）
    assert old == old_snap
    assert index == index_snap
    assert new_index["D-0001"]["superseded_by"] == "D-0002"
    assert "D-0001" in new_index["D-0002"]["supersedes"]
    # 已被取代的处置不可再次 supersede
    with pytest.raises(ValueError):
        disposition.apply_supersedes(
            new_index, "D-0001", _disp(disposition_id="D-0003"))


# ---------------------------------------------------------------------------
# 合成工厂：gate
# ---------------------------------------------------------------------------

def _inp(artifact_id="art-1", status="present", sha=None):
    return {"artifact_id": artifact_id, "sha256": sha or _h("1"),
            "status": status}


def _pred(pid, value=True, evidence="out/gate-evidence.json"):
    d = {"id": pid, "value": value}
    if evidence is not None:
        d["evidence"] = evidence
    return d


def _gk(**over):
    kw = dict(
        gate_id="TL-1-G1",
        gate_kind="training_loop",
        project_id="revc-coreboard",
        profile_id="revc-tbd1",
        snapshot_revision="rev-0002",
        predicate_version="pv-1",
        inputs=[_inp()],
        required_predicates=[_pred("schema_valid")],
        fact_refs=(),
        disposition_refs=(),
        graph_report=None,
        evaluator={"name": "pcbflow.gate", "version": "1",
                   "code_sha256": _h("9")})
    kw.update(over)
    return gate.evaluate_gate(**kw)


def _graph(acyclic=True, **over):
    rep = {"acyclic": acyclic, "topological_order": ["n1", "n2"],
           "cycle_nodes": [], "stale_nodes": [], "unresolved_inputs": [],
           "cross_revision_edges": [], "future_label_violations": []}
    rep.update(over)
    return rep


# ---------------------------------------------------------------------------
# gate：机器谓词判定
# ---------------------------------------------------------------------------

def test_gate_stale_input_blocked():
    rec = _gk(inputs=[_inp(status="stale")])
    assert rec["result"] == "blocked"
    assert "stale_input" in rec["failure_codes"]


def test_gate_missing_input_blocked():
    rec = _gk(inputs=[_inp("art-x", status="missing")])
    assert rec["result"] == "blocked"
    assert "missing_input" in rec["failure_codes"]


def test_gate_predicate_false_fails():
    rec = _gk(required_predicates=[
        _pred("schema_valid"), _pred("drc_final_clean", value=False)])
    assert rec["result"] == "fail"
    assert "predicate_failed:drc_final_clean" in rec["failure_codes"]


def test_gate_true_without_evidence_blocked():
    rec = _gk(required_predicates=[_pred("schema_valid", evidence=None)])
    assert rec["result"] == "blocked"
    assert any(c.startswith("evidence_missing:")
               for c in rec["failure_codes"])


def test_gate_all_pass():
    rec = _gk()
    assert rec["result"] == "pass"
    assert rec["failure_codes"] == []
    assert rec["evaluation_metadata"] == {"evaluated_at": None,
                                          "host": None, "elapsed_s": None}
    assert gate.verify_gate_record(rec) == []


def test_gate_product_requires_graph_report():
    rec = _gk(gate_kind="product")
    assert rec["result"] == "blocked"
    assert "graph_report_missing" in rec["failure_codes"]
    ok = _gk(gate_kind="product", graph_report=_graph())
    assert ok["result"] == "pass"
    assert ok["cycle_check"]["acyclic"] is True


def test_gate_graph_cycle_blocked():
    rec = _gk(graph_report=_graph(acyclic=False, cycle_nodes=["n2"]))
    assert rec["result"] == "blocked"
    assert "cycle_detected" in rec["failure_codes"]
    assert rec["cycle_check"]["acyclic"] is False
    stale = _gk(graph_report=_graph(stale_nodes=["n1"]))
    assert stale["result"] == "blocked"
    assert "stale_nodes" in stale["failure_codes"]


def test_gate_core_hash_excludes_evaluation_metadata():
    rec = _gk()
    h1 = gate.gate_core_hash(rec)
    rec2 = copy.deepcopy(rec)
    rec2["evaluation_metadata"] = {"evaluated_at": "2026-09-01T00:00:00Z",
                                   "host": "host-a", "elapsed_s": 1.5}
    assert gate.gate_core_hash(rec2) == h1
    # 核心字段变化则 hash 变化
    rec3 = copy.deepcopy(rec)
    rec3["result"] = "fail"
    assert gate.gate_core_hash(rec3) != h1


def test_verify_gate_record_injected_true_without_evidence():
    rec = _gk()
    injected = copy.deepcopy(rec)
    injected["required_predicates"] = [{"id": "schema_valid", "value": True}]
    errs = gate.verify_gate_record(injected)
    assert any("evidence" in e for e in errs)


def test_verify_gate_record_injected_pass_mismatch():
    rec = _gk(required_predicates=[
        _pred("schema_valid"), _pred("drc_final_clean", value=False)])
    assert rec["result"] == "fail"
    forged = copy.deepcopy(rec)
    forged["result"] = "pass"       # 人工直写 pass
    forged["failure_codes"] = []    # 伪装无失败码
    errs = gate.verify_gate_record(forged)
    assert any("重算" in e or "pass" in e for e in errs)
    # 无 evaluator.code_sha256 → 错误
    no_eval = copy.deepcopy(rec)
    no_eval["evaluator"] = {"name": "x", "version": "1"}
    errs2 = gate.verify_gate_record(no_eval)
    assert errs2  # schema required + 64hex 检查均应报错
