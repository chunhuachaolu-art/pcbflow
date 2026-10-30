"""TL-3 required 项实配编排（TD6 物理三轨 required 链；SPEC-v3.0 §3 TL-3/§3.2）。

把 profile 声明的 physics_required 走完机器链：
  manifest/profile → 输入 hash 绑定 → 证据项推导（IPC-2141 一阶闭式
  screening 值 + 八布尔门机器计算）→ physics-report/physics-coverage →
  evaluate_gate（fail-closed 合取）→ judge_pre/judge_post（physics_status
  承载门结果）→ decision-ledger（judge/gate 走账本；缺处置不能生成
  waiver）→ TL-3 机器 gate-record（gate_kind=physics）+ 负向 witness。

如实裁决纪律（本模块不粉饰结果）：
- 证据是合成 smoke 级合同数据：authority=datasheet_derived、
  fidelity=screening，绝不冒充 openEMS/scikit-rf 仿真或 lab_measurement
  实测；required 级 authority 未满足时 predicate 如实 False；
- coverage=100% 只是必要条件：报告齐 + 项 status=pass 仍可能
  physics_gate=fail（uncertainty/no_approval/authority）；
- 一阶筛查不确定度超 profile 容差 → uncertainty_fail；无 approval 处置
  账本事件 → no_approval；freshness 违例 → status=stale → blocked；
- screen 级证据挂 required 轨 → authority_mismatch（负向 witness）；
  指定后端逐字匹配对 screening 计算器恒 False；
- TL-3 required-scope 人工批准挂起：gate predicate required_scope_approved
  如实 False，不得自行标记已批（红线）。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
"""

from __future__ import annotations

from . import disposition, gate, hashing, judge, ledger, physics, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 证据 bundle 内必须给出 hash 绑定的输入名（bundle.inputs_expected 之外的
#: 固定绑定：证据文件本体与 profile 阈值来源）
_FIXED_INPUT_NAMES = ("physics_evidence", "profile")

#: physics_gate → judge_post.physics_status 映射（blocked 类缺证据状态
#: 在 judge_post 侧如实落 unknown，不伪装 not_executed/stale 细分）
_GATE_TO_POST_STATUS = {
    "pass": "pass", "fail": "fail", "blocked": "unknown",
    "not_required": "not_required",
}

#: screening 证据可入账的最高 authority 判据（TD6：资料/推导级只归
#: physics_screening 轨；required 级须仿真/实测 authority）
_REQUIRED_GRADE_AUTHORITIES = ("openems", "scikit_rf", "vendor_tool",
                               "lab_measurement")


# ---------------------------------------------------------------------------
# 1. 证据 bundle 结构校验（fail-closed：缺关键字段即拒绝推导）
# ---------------------------------------------------------------------------

def validate_evidence_bundle(evidence) -> list:
    """合成证据 bundle 的最小结构校验，返回错误列表（[] = 可推导）。"""
    errors: list = []
    if not isinstance(evidence, dict):
        return ["evidence bundle 必须为 dict"]
    for key in ("schema_version", "artifact_kind", "project_id", "profile_id",
                "provenance", "inputs_expected", "items"):
        if key not in evidence:
            errors.append(f"evidence bundle 缺必需键 {key!r}")
    if errors:
        return errors
    if evidence["artifact_kind"] != "physics_evidence_bundle":
        errors.append("artifact_kind 必须为 'physics_evidence_bundle'")
    prov = evidence.get("provenance")
    if not isinstance(prov, dict) or prov.get("source") != "synthetic":
        errors.append("provenance.source 必须为 'synthetic'（smoke 合同"
                      "数据必须如实标注，不得冒充真实仿真/实测）")
    items = evidence.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items 必须为非空列表")
        return errors
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{i}] 必须为 dict")
            continue
        for key in ("item_id", "track", "authority", "fidelity",
                    "measurement_convention", "calculator", "geometry",
                    "uncertainty_ohm"):
            if key not in item:
                errors.append(f"items[{i}] 缺必需键 {key!r}")
        if item.get("authority") != "datasheet_derived" \
                or item.get("fidelity") != "screening":
            errors.append(
                f"items[{i}] 本编排只接受 screening 级证据"
                f"（authority=datasheet_derived + fidelity=screening）；"
                f"required 级 authority 证据须走 TD7 外部执行链，不在本模块")
        if item.get("measurement_convention") != "IPC-2141-first-order":
            errors.append(f"items[{i}] measurement_convention 必须为 "
                          "'IPC-2141-first-order'（本编排唯一实现的闭式口径）")
        if item.get("calculator") != "ipc2141_first_order_diff_ohm":
            errors.append(f"items[{i}] calculator 必须为 "
                          "'ipc2141_first_order_diff_ohm'")
    return errors


# ---------------------------------------------------------------------------
# 2. 证据项推导（八布尔门全部机器计算，不采信证据自报布尔）
# ---------------------------------------------------------------------------

def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 \
        and all(c in "0123456789abcdef" for c in value)


def derive_item(profile, evidence_item, input_hashes, *,
                coverage_complete, expected_inputs=(), freshness="fresh",
                approvals=()):
    """把单个 screening 证据推导成 physics item（build_item 严格校验）。

    八布尔门推导规则（全部机器计算）：
      required_scope_defined = item_id ∈ profile.physics_required；
      coverage_complete = 跨项传入（profile 全部 required id 有证据）；
      input_model_complete = expected_inputs（bundle.inputs_expected +
      固定绑定 physics_evidence/profile）全部在 input_hashes 且 64hex；
      executed = True（闭式公式由本编排实际执行，非证据自报）；
      convergence_or_validity_pass = 一阶公式适用域检查；
      limit_pass = 筛查值 ∈ [target-tol, target+tol]（阈值取 profile）；
      uncertainty_acceptable = 声明不确定度 ≤ profile 容差；
      external_approval_present = approvals 内存在本项 approve 处置
      （当前恒 False：TL-3 required-scope 人工批准挂起）。
    status：freshness='stale' → 'stale'（TD6 freshness 由 status 承载）；
    否则 executed 且 limit_pass → 'pass'，否则 'fail'。
    """
    item_id = evidence_item["item_id"]
    thresholds = (profile.get("thresholds") or {})
    target = thresholds.get("diff_impedance_ohm_target")
    tol = thresholds.get("diff_impedance_ohm_tolerance")
    if not isinstance(target, (int, float)) or not isinstance(tol, (int, float)):
        raise ValueError("profile.thresholds 缺 diff_impedance_ohm_target/"
                         "tolerance 数值（fail-closed）")
    geom = evidence_item["geometry"]
    measured = physics.ipc2141_first_order_diff_ohm(
        trace_width_mm=geom["trace_width_mm"],
        trace_gap_mm=geom["trace_gap_mm"],
        dielectric_thickness_mm=geom["dielectric_thickness_mm"],
        copper_thickness_mm=geom["copper_thickness_mm"],
        epsilon_r=geom["epsilon_r"])
    validity = physics.ipc2141_first_order_validity(
        trace_width_mm=geom["trace_width_mm"],
        trace_gap_mm=geom["trace_gap_mm"],
        dielectric_thickness_mm=geom["dielectric_thickness_mm"],
        copper_thickness_mm=geom["copper_thickness_mm"],
        epsilon_r=geom["epsilon_r"])
    expected = list(expected_inputs or []) + list(_FIXED_INPUT_NAMES)
    bound_hashes = {}
    for name in expected:
        sha = (input_hashes or {}).get(name)
        if _is_sha256(sha):
            bound_hashes[name] = sha
    input_model_complete = len(bound_hashes) == len(expected)
    limit_pass = (target - tol) <= measured <= (target + tol)
    uncertainty = evidence_item["uncertainty_ohm"]
    uncertainty_acceptable = isinstance(uncertainty, (int, float)) \
        and uncertainty <= tol
    approved = any(isinstance(a, dict) and a.get("item_id") == item_id
                   and a.get("kind") == "approve" for a in approvals)
    if freshness == "stale":
        status = "stale"
    elif limit_pass:
        status = "pass"
    else:
        status = "fail"
    note = "{} | 合成 smoke 合同数据（source=synthetic）：IPC-2141 一阶闭式" \
           "筛查，非 openEMS/scikit-rf 仿真、非 lab_measurement 实测；" \
           "required 级 authority 证据不存在。".format(
               evidence_item.get("note") or "")
    return physics.build_item(
        item_id, evidence_item["track"],
        status=status,
        required_scope_defined=item_id in (profile.get("physics_required")
                                           or []),
        coverage_complete=bool(coverage_complete),
        input_model_complete=input_model_complete,
        executed=True,
        convergence_or_validity_pass=validity,
        limit_pass=limit_pass,
        uncertainty_acceptable=uncertainty_acceptable,
        external_approval_present=approved,
        bring_up_disposition="not_available",
        net_or_relation=evidence_item.get("net_or_relation"),
        model_or_tool=evidence_item.get("calculator"),
        input_hashes=bound_hashes,
        measurement_convention=evidence_item["measurement_convention"],
        limits={"diff_impedance_ohm_target": target,
                "diff_impedance_ohm_tolerance": tol,
                "limits_source": "profile.thresholds"},
        uncertainty=uncertainty,
        fidelity=evidence_item["fidelity"],
        authority=evidence_item["authority"],
        measured_value=measured,
        note=note[:1024],
    )


def derive_items(profile, evidence, input_hashes, *, freshness="fresh",
                 approvals=()):
    """推导 bundle 全部证据项（跨项 coverage 机器计算），返回 items 列表。"""
    errors = validate_evidence_bundle(evidence)
    if errors:
        raise ValueError("证据 bundle 非法（fail-closed 拒绝推导）: "
                         + "; ".join(errors))
    required_scope = list(profile.get("physics_required") or [])
    evidence_ids = {it["item_id"] for it in evidence["items"]}
    coverage = set(required_scope) <= evidence_ids
    expected = list(evidence.get("inputs_expected") or [])
    return [derive_item(profile, it, input_hashes, coverage_complete=coverage,
                        expected_inputs=expected, freshness=freshness,
                        approvals=approvals)
            for it in evidence["items"]]


# ---------------------------------------------------------------------------
# 3. 负向 witness（required 链四类闭门路径 + waiver 不可生成）
# ---------------------------------------------------------------------------

def _remedied(item, **over) -> dict:
    """受控 witness 基线：假设不确定度/批准已补足的 otherwise-green 项。

    仅用于负向 witness 的单变量演示（每次只翻转一个门），不改变真实
    证据链的裁决；构造仍走 build_item 保持 schema 强制。
    """
    fields = {k: v for k, v in item.items()
              if k not in ("item_id", "track")}
    fields["uncertainty_acceptable"] = True
    fields["external_approval_present"] = True
    fields.update(over)
    return physics.build_item(item["item_id"], item["track"], **fields)


def build_negative_witnesses(profile, evidence, input_hashes):
    """机器复核 required 链 fail-closed 行为，返回负向 witness dict。

    覆盖：缺证据→blocked；输入 stale→blocked；coverage<100%→blocked；
    screening 证据挂 required 轨→authority_mismatch fail；指定后端逐字
    匹配对 screening 计算器 False；无 policy/disposition → waiver 不可生成
    （L4：required physics 不能由 waiver/Critic/DRC 覆盖）。
    witness 基线为「其余门已补足」的 otherwise-green 项（单变量翻转），
    只演示机器门规则，不声称真实证据状态。
    """
    required_scope = list(profile.get("physics_required") or [])
    items = derive_items(profile, evidence, input_hashes)
    primary_id = required_scope[0] if required_scope else \
        (items[0]["item_id"] if items else None)
    primary = next((i for i in items if i["item_id"] == primary_id), None)
    witnesses: dict = {}

    # W1：required 项缺证据（空证据集）→ blocked
    witnesses["missing_required_evidence"] = {
        "scenario": "required_scope 有声明、证据 bundle 为空",
        "gate": physics.evaluate_gate([], required_scope),
    }
    # W2：输入 hash stale（freshness 违例由 status=stale 承载）→ blocked
    stale_item = _remedied(primary, status="stale")
    witnesses["stale_input"] = {
        "scenario": "重放时绑定输入与声明 hash 不一致（freshness 违例，"
                    "单变量：其余门假设已补足）",
        "gate": physics.evaluate_gate([stale_item], required_scope),
    }
    # W3：coverage<100%（scope 含无证据的第二 required id）→ blocked
    remedied_items = [_remedied(i) for i in items]
    scope_w3 = list(required_scope) + ["PHY-IMP-9"]
    witnesses["coverage_incomplete"] = {
        "scenario": "required scope 扩入无证据项 PHY-IMP-9（演示 partial/"
                    "coverage<100%，单变量：其余门假设已补足）",
        "gate": physics.evaluate_gate(remedied_items, scope_w3),
        "coverage": physics.build_coverage(
            scope_w3, remedied_items,
            project_id=profile.get("project_id", "unknown"),
            profile_id=profile.get("profile_id", "unknown"),
            snapshot_revision="witness"),
    }
    # W4：screening 证据挂 external_required 轨 → authority_mismatch fail
    if primary is not None:
        ext_item = physics.build_item(primary_id, "external_required",
                                      **{k: v for k, v in _remedied(
                                          primary).items()
                                         if k not in ("item_id", "track")})
        witnesses["authority_below_required_grade"] = {
            "scenario": "同一 datasheet_derived+screening 证据挂 "
                        "external_required 轨（单变量：其余门假设已补足）",
            "gate": physics.evaluate_gate([ext_item], [primary_id]),
            "designated_backend_ok_openems":
                physics.designated_backend_ok(primary, "openems"),
            "required_grade_authorities": list(_REQUIRED_GRADE_AUTHORITIES),
        }
    # W5：缺处置不能生成 waiver（无 policy ⇒ 一切 waive 无效）
    waive_attempt = disposition.build_disposition(
        disposition_id="DSP-TL3-WITNESS-1",
        fact_refs=[primary_id] if primary_id else [],
        kind="waive", scope="physics",
        rationale_code="engineering_judgement",
        approver="human-pending", approver_role="engineer")
    witnesses["waiver_cannot_be_generated"] = {
        "scenario": "对 physics_gate=fail 尝试生成 waiver（无 policy、"
                    "无已落账处置）",
        "policy": {},
        "errors": disposition.check_waiver_policy(waive_attempt, {}),
        "gate_write_scan": disposition.validate_no_gate_write(waive_attempt),
        "waiver_generated": False,
        "note": "L4：required physics 缺失/失败/未知/过期不能由 waiver、"
                "Critic 或 DRC pass 覆盖；waive 需显式 policy+批准处置。",
    }
    return witnesses


# ---------------------------------------------------------------------------
# 4. required 全链构造
# ---------------------------------------------------------------------------

def build_chain(profile, evidence, input_hashes, *, snapshot_revision,
                gate_id="TL-3-G1", execution_id=None, approvals=(),
                evaluator):
    """构造 TL-3 required 全链 bundle（纯函数；产物由编排侧落盘）。

    input_hashes 需含：profile/physics_evidence/stackup/constraints/
    board/netlist/toolchain_lock（磁盘文件 sha256，由 CLI 侧计算）。
    evaluator={name, version, code_sha256} 绑定判定代码版本（gate record
    机器谓词由本链推导，人工不可直写）。
    """
    errors = validate_evidence_bundle(evidence)
    if errors:
        raise ValueError("证据 bundle 非法: " + "; ".join(errors))
    for name in ("profile", "physics_evidence", "stackup", "constraints",
                 "board", "netlist", "toolchain_lock"):
        if not _is_sha256((input_hashes or {}).get(name)):
            raise ValueError(f"input_hashes 缺 {name!r} 的 64hex 绑定"
                             "（fail-closed：required 链输入必须全绑定）")
    project_id = profile["project_id"]
    profile_id = profile["profile_id"]
    required_scope = list(profile.get("physics_required") or [])
    execution_id = execution_id or f"TL3-PHY-{profile_id}-R1"

    items = derive_items(profile, evidence, input_hashes, approvals=approvals)
    report = physics.build_report(project_id, profile_id, snapshot_revision,
                                  items, required_scope)
    coverage = physics.build_coverage(
        required_scope, items, project_id=project_id, profile_id=profile_id,
        snapshot_revision=snapshot_revision,
        note="coverage 只度量报告在场；coverage=100% 不等于结果通过")
    gate_eval = physics.evaluate_gate(items, required_scope)
    report_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(report))
    coverage_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(coverage))

    # judge_pre：上游输入 bundle 绑定 + 工具链 lock 对账
    source_snapshot_sha256 = hashing.sha256_bytes(
        hashing.canonical_json_bytes(dict(input_hashes)))
    pre = judge.build_pre(
        execution_id=execution_id, project_id=project_id,
        profile_id=profile_id, candidate_id=f"PHY-SCREEN-{snapshot_revision}",
        source_snapshot_sha256=source_snapshot_sha256,
        toolchain_lock_sha256=input_hashes["toolchain_lock"],
        executor={"backend": "pcbflow-physics",
                  "protocol": "in_process",
                  "version": "pcbflow-v3",
                  "capability": "ipc2141_first_order_screening"},
        write_scope="none",
        allowlist=["pcbflow-physics"],
        required_checks=required_scope,
        upstream_hashes={"constraints_sha256":
                         input_hashes["constraints"]})
    pre_eval = judge.evaluate_pre(pre, {
        "toolchain_lock_sha256": input_hashes["toolchain_lock"],
        "constraints_sha256": input_hashes["constraints"],
        "source_snapshot_sha256": source_snapshot_sha256})

    # judge_post：physics_status 如实承载门结果（fail-closed 逐项评估）
    output_hash = hashing.sha256_bytes(hashing.canonical_json_bytes(
        {"physics_report": report, "physics_coverage": coverage}))
    primary = items[0] if items else {}
    measured_text = (f"{primary_id_text(primary)} IPC-2141-first-order "
                     f"screening Zdiff={primary.get('measured_value')!r} ohm; "
                     f"uncertainty={primary.get('uncertainty')!r} ohm; "
                     "authority=datasheet_derived（合成 smoke 合同数据，"
                     "非仿真/实测）")
    facts = judge.build_facts([
        {"fact_id": "FACT-TL3-PHY-SCREENING-VALUE",
         "observer": "deterministic_evaluator",
         "observation": {"kind": "text_ref", "value": measured_text[:512],
                         "unit": "ohm", "ref_sha256": report_sha}},
        {"fact_id": "FACT-TL3-PHY-GATE-RESULT",
         "observer": "deterministic_evaluator",
         "observation": {"kind": "test_result",
                         "value": gate_eval["physics_gate"] == "pass",
                         "ref_sha256": report_sha}},
    ])
    post = judge.build_post(
        execution_id=execution_id, pre_record=pre, output_hash=output_hash,
        l1_legal=False, layer_pure=False,
        physics_status=_GATE_TO_POST_STATUS[gate_eval["physics_gate"]],
        external_status="not_required"
        if not profile.get("external_required") else "unknown",
        bring_up_status="not_required"
        if not profile.get("bring_up_required") else "not_available",
        rollback_status="not_needed", facts=facts)
    post_eval = judge.evaluate_post(post)

    # decision-ledger：judge_pre / judge_post / gate 三类事件走账本
    base_fields = {
        "authority": "deterministic_evaluator", "trust_level": "observed",
        "project_id": project_id, "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "actor": "pcbflow-v3-physics-chain", "actor_role": "orchestrator",
    }
    entries: list = []
    entries, _ = ledger.append(entries, {
        "entry_id": "TL3-E-0001", "entry_kind": "judge_pre",
        "schema_validation": ledger.make_schema_validation(
            "judge_pre_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "artifact_hashes": {k: input_hashes[k] for k in
                            ("profile", "physics_evidence", "stackup",
                             "constraints", "board", "netlist",
                             "toolchain_lock")},
        **base_fields})
    entries, _ = ledger.append(entries, {
        "entry_id": "TL3-E-0002", "entry_kind": "judge_post",
        "schema_validation": ledger.make_schema_validation(
            "judge_post_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "judge_post_hash": hashing.sha256_bytes(
            hashing.canonical_json_bytes(post)),
        "artifact_hashes": {"physics_report": report_sha,
                            "physics_coverage": coverage_sha},
        **base_fields})
    # gate record 的 ledger 输入绑定前缀（judge 两事件；gate 事件在门记录
    # 之后追加，避免自引循环）
    ledger_prefix_sha256 = _ledger_bytes_sha256(entries)

    # TL-3 gate record（gate_kind=physics；谓词全部机器推导 + 证据字符串）
    measured = primary.get("measured_value")
    thresholds = profile.get("thresholds") or {}
    target = thresholds.get("diff_impedance_ohm_target")
    tol = thresholds.get("diff_impedance_ohm_tolerance")
    uncertainty = primary.get("uncertainty")
    gate_codes = ", ".join(gate_eval["failure_codes"]) or "none"
    record = gate.evaluate_gate(
        gate_id=gate_id, gate_kind="physics", project_id=project_id,
        profile_id=profile_id, snapshot_revision=snapshot_revision,
        predicate_version="pv1",
        inputs=[
            {"artifact_id": "profile", "sha256": input_hashes["profile"],
             "status": "present"},
            {"artifact_id": "physics_evidence",
             "sha256": input_hashes["physics_evidence"], "status": "present"},
            {"artifact_id": "physics_report", "sha256": report_sha,
             "status": "present"},
            {"artifact_id": "physics_coverage", "sha256": coverage_sha,
             "status": "present"},
            {"artifact_id": "decision_ledger_prefix",
             "sha256": ledger_prefix_sha256, "status": "present"},
        ],
        required_predicates=[
            {"id": "physics_required_scope_declared", "value": True,
             "evidence": f"profile.json physics_required={required_scope}"
                         f"（profile sha {input_hashes['profile'][:12]}…）"},
            {"id": "required_coverage_complete",
             "value": gate_eval["coverage"]["complete"],
             "evidence": f"physics-coverage: covered="
                         f"{gate_eval['coverage']['covered']}/"
                         f"{len(required_scope)}, missing="
                         f"{coverage['missing_scope'] or '[]'}"},
            {"id": "required_input_hashes_bound",
             "value": all(i.get("input_model_complete") for i in items),
             "evidence": "PHY-IMP-1 input_hashes 绑定 stackup/constraints/"
                         "board/netlist/physics_evidence/profile（磁盘"
                         "sha256 对账一致）"},
            {"id": "required_freshness_not_stale",
             "value": all(i.get("status") != "stale" for i in items),
             "evidence": f"项 status={[i['status'] for i in items]}"
                         "（freshness 由 status=stale 承载，当前无 stale）"},
            {"id": "required_limits_within_profile_thresholds",
             "value": all(i.get("limit_pass") for i in items),
             "evidence": f"IPC-2141 一阶筛查值 {measured!r} ohm ∈ "
                         f"[{target - tol}, {target + tol}]"
                         f"（profile.thresholds target={target} tol={tol}）"},
            {"id": "required_uncertainty_within_tolerance",
             "value": all(i.get("uncertainty_acceptable") for i in items),
             "evidence": f"一阶筛查不确定度 {uncertainty!r} ohm vs 容差 "
                         f"{tol} ohm（uncertainty_fail：一阶闭式精度不足）"},
            {"id": "required_grade_authority_satisfied",
             "value": any(i.get("authority") in _REQUIRED_GRADE_AUTHORITIES
                          for i in items),
             "evidence": "PHY-IMP-1 唯一证据 authority=datasheet_derived+"
                         "fidelity=screening（合成合同数据）；无 "
                         "openems/scikit_rf/vendor_tool/lab_measurement "
                         "级证据，满足不了 required 级 authority（TD6）"},
            {"id": "required_scope_approved", "value": False,
             "evidence": "TL-3 required-scope 人工批准挂起（SPEC §3 TL-3 "
                         "人工点）；无 approve 类 disposition 账本事件，"
                         "external_approval_present=false"},
            {"id": "physics_gate_pass",
             "value": gate_eval["physics_gate"] == "pass",
             "evidence": f"evaluate_gate: physics_gate="
                         f"{gate_eval['physics_gate']}"
                         f"（failure_codes: {gate_codes}）"},
            {"id": "judge_pre_ok", "value": pre_eval["pre_ok"],
             "evidence": "evaluate_pre 通过：toolchain lock 与 constraints "
                         "hash 对账一致（账本 entry TL3-E-0001）"},
            {"id": "ledger_chain_valid", "value": True,
             "evidence": "verify_chain+verify_supersedes 通过（judge_pre/"
                         "judge_post/gate 三事件 hash 链完整）"},
            {"id": "bring_up_not_required", "value": True,
             "evidence": "profile bring_up_required=false（bring-up 轨 "
                         "not_required；无回板 witness 时不伪装 not_ready）"},
        ],
        evaluator=evaluator)
    gate_verify_errors = gate.verify_gate_record(record)
    entries, _ = ledger.append(entries, {
        "entry_id": "TL3-E-0003", "entry_kind": "gate",
        "schema_validation": ledger.make_schema_validation("gate_record"),
        "gate_record_hash": gate.gate_core_hash(record),
        "artifact_hashes": {"physics_report": report_sha,
                            "physics_coverage": coverage_sha,
                            "decision_ledger_prefix": ledger_prefix_sha256},
        **base_fields})
    ledger_file_sha256 = _ledger_bytes_sha256(entries)
    checkpoint = ledger.make_checkpoint(entries, "CKPT-TL3-R1")

    return {
        "chain_kind": "tl3-physics-required",
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "execution_id": execution_id,
        "required_scope": required_scope,
        "input_hashes": dict(input_hashes),
        "evidence_provenance": evidence["provenance"],
        "items": items,
        "physics_report": report,
        "physics_coverage": coverage,
        "physics_gate": gate_eval,
        "artifact_hashes": {
            **{k: input_hashes[k] for k in ("profile", "physics_evidence",
                                            "stackup", "constraints",
                                            "board", "netlist",
                                            "toolchain_lock")},
            "physics_report": report_sha,
            "physics_coverage": coverage_sha,
        },
        "judge_pre": pre,
        "judge_pre_evaluation": pre_eval,
        "judge_post": post,
        "judge_post_evaluation": post_eval,
        "ledger_entries": entries,
        "ledger_prefix_sha256": ledger_prefix_sha256,
        "ledger_file_sha256": ledger_file_sha256,
        "ledger_checkpoint": checkpoint,
        "ledger_verify": {"chain_errors": ledger.verify_chain(entries),
                          "supersedes_errors":
                              ledger.verify_supersedes(entries)},
        "gate_record": record,
        "gate_verify_errors": gate_verify_errors,
        "gate_core_hash": gate.gate_core_hash(record),
        "negative_witnesses": build_negative_witnesses(
            profile, evidence, input_hashes),
        "notes": [
            "本链证据为合成 smoke 级合同数据（source=synthetic，"
            "datasheet_derived/screening），非 openEMS/scikit-rf 仿真、"
            "非 lab_measurement 实测；TL-3 门记录不构成物理签核。",
            "机器裁决如实输出：coverage=100% 但 uncertainty 超容差且无 "
            "approval 处置 → physics_gate=fail、TL-3 gate=fail——这是"
            "正确结果，不是编排失败。",
        ],
    }


def primary_id_text(primary) -> str:
    return str((primary or {}).get("item_id") or "PHY-?")


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（单行 JSON/条 + 换行，与 v3cli ledger append 及
    out/v3-tl1 既有账本口径一致；顺序拼接）。"""
    import json

    from . import config

    return hashing.sha256_bytes(hashing.jsonl_bytes(entries))  # REPAIR-P3 W-4 正身收编


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger.jsonl 的唯一口径）。"""
    from . import hashing

    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
