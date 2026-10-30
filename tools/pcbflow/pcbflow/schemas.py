"""v3.0 schema 注册表与严格验证器（SPEC-v3.0-PROPOSAL TD1/TD4..TD7/TD11/§1.3/§1.4）。

设计约束：
- 零第三方依赖、零 IO、纯函数（生成器模式沿用；jsonschema 库仅测试交叉验证用）。
- 支持的 JSON Schema 子集（本包 schema 全部落在此子集内）：
  type/required/properties/additionalProperties/enum/const/pattern/items/
  minItems/maxItems/minLength/maxLength/minimum/maximum/oneOf/anyOf。
- fail-closed：未知 schema 名、结构不符、多余键（additionalProperties=false）一律
  返回非空错误列表；L7 缺证据闭门律的验证器侧落地。
- schema 本身 canonical JSON 哈希入注册表（schema_hash），供 ledger/gate 绑定
  「验证时用的是哪一版 schema」。
"""

from __future__ import annotations

import re

from . import hashing

SCHEMA_V3 = "3.0"
REGISTRY_VERSION = "3.0"

_HASH64 = "^[0-9a-f]{64}$"
_REL_POSIX = "^[A-Za-z0-9._/+-]+$"   # 相对路径（正斜杠；禁 .. 与盘符）


# ---------------------------------------------------------------------------
# 验证器引擎（子集实现；错误信息带 JSON path，供 gate failure_codes 引用）
# ---------------------------------------------------------------------------

def _type_ok(spec_type: str, value) -> bool:
    if spec_type == "object":
        return isinstance(value, dict)
    if spec_type == "array":
        return isinstance(value, list)
    if spec_type == "string":
        return isinstance(value, str)
    if spec_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if spec_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if spec_type == "boolean":
        return isinstance(value, bool)
    if spec_type == "null":
        return value is None
    raise ValueError(f"unknown type spec: {spec_type}")


def _validate(spec, value, path: str, errors: list) -> None:
    if "const" in spec and value != spec["const"]:
        errors.append(f"{path}: const 违例（期望 {spec['const']!r}，得到 {value!r}）")
        return
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{path}: enum 外取值 {value!r}（合法集 {spec['enum']}）")
        return
    if "type" in spec:
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        if not any(_type_ok(t, value) for t in types):
            errors.append(f"{path}: 类型不符（期望 {'|'.join(types)}，"
                          f"得到 {type(value).__name__}）")
            return
    if isinstance(value, str):
        if "pattern" in spec and not re.search(spec["pattern"], value):
            errors.append(f"{path}: 不匹配 pattern {spec['pattern']}（值 {value[:60]!r}）")
        if "minLength" in spec and len(value) < spec["minLength"]:
            errors.append(f"{path}: 短于 minLength={spec['minLength']}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            errors.append(f"{path}: 超出 maxLength={spec['maxLength']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{path}: 小于 minimum={spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"{path}: 大于 maximum={spec['maximum']}")
    if isinstance(value, list):
        if "minItems" in spec and len(value) < spec["minItems"]:
            errors.append(f"{path}: 少于 minItems={spec['minItems']}")
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            errors.append(f"{path}: 多于 maxItems={spec['maxItems']}")
        if "items" in spec:
            for i, item in enumerate(value):
                _validate(spec["items"], item, f"{path}[{i}]", errors)
    if isinstance(value, dict):
        props = spec.get("properties", {})
        for name in spec.get("required", []):
            if name not in value:
                errors.append(f"{path}: 缺 required 键 {name!r}")
        for k, v in value.items():
            if k in props:
                _validate(props[k], v, f"{path}.{k}", errors)
            elif spec.get("additionalProperties") is False:
                errors.append(f"{path}: 多余键 {k!r}（additionalProperties=false）")
            elif isinstance(spec.get("additionalProperties"), dict):
                _validate(spec["additionalProperties"], v,
                          f"{path}.{k}", errors)
    for combinator, expect in (("oneOf", 1), ("anyOf", 0)):
        if combinator in spec:
            matched = sum(
                1 for sub in spec[combinator]
                if not _collect_errors(sub, value, path))
            if matched != expect if combinator == "oneOf" else matched <= expect:
                errors.append(f"{path}: {combinator} 不满足"
                              f"（匹配 {matched} 个子 schema，要求 "
                              f"{'恰好 1' if combinator == 'oneOf' else '≥1'}）")


def _collect_errors(spec, value, path: str) -> list:
    """在子 schema 内收集错误（oneOf/anyOf 探测用；不外抛）。"""
    errs: list = []
    try:
        _validate(spec, value, path, errs)
    except Exception as exc:  # 引擎自身缺陷按验证失败处理（fail-closed）
        errs.append(f"{path}: validator 内部错误 {exc}")
    return errs


def validate(schema_name: str, obj) -> list:
    """严格验证：返回错误列表（[] = 合法）。未知 schema 名 fail-closed。"""
    if schema_name not in SCHEMAS:
        return [f"$: 未知 schema 名 {schema_name!r}（注册表 v{REGISTRY_VERSION}）"]
    return _collect_errors(SCHEMAS[schema_name], obj, "$")


def is_valid(schema_name: str, obj) -> bool:
    return not validate(schema_name, obj)


def validate_spec(spec: dict, obj) -> list:
    """对注册表外的局部 schema（子集语法）验证对象（B 类模块局部合同用）。"""
    return _collect_errors(spec, obj, "$")


def schema_hash(schema_name: str) -> str:
    """schema 规范化哈希（版本化绑定：ledger/gate 记录用哪一版 schema 验证）。"""
    return hashing.sha256_text(hashing.json_dumps(
        {"name": schema_name, "schema_version": REGISTRY_VERSION,
         "schema": SCHEMAS[schema_name]}))


# ---------------------------------------------------------------------------
# 通用子 schema 片段
# ---------------------------------------------------------------------------

_SHA256_FIELD = {"type": "string", "pattern": _HASH64}
_ID_FIELD = {"type": "string", "minLength": 1, "maxLength": 128}
_NULLABLE_SHA = {"oneOf": [{"type": "null"}, {"type": "string",
                                              "pattern": _HASH64}]}
_NULLABLE_ID = {"oneOf": [{"type": "null"}, _ID_FIELD]}
# str→非负 int 计数映射（REPAIR-P3 W-5 新增；counts/totals 共用；
# 仅新条目引用，不进任何既有 schema 哈希）
_STR_INT_MAP = {"type": "object",
                "additionalProperties": {"type": "integer", "minimum": 0}}


# ---------------------------------------------------------------------------
# §1.4 gate-record（TL/TD 门；核心 JSON 无 wall-clock——时间只在
# evaluation_metadata 且不参加核心 hash）
# ---------------------------------------------------------------------------

_GATE_RECORD = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "gate_id", "gate_kind", "project_id",
                 "profile_id", "snapshot_revision", "predicate_version",
                 "inputs", "required_predicates", "fact_refs",
                 "disposition_refs", "cycle_check", "result", "failure_codes",
                 "evaluator", "evaluation_metadata"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "gate_id": _ID_FIELD,
        "gate_kind": {"enum": ["training_loop", "product", "physics",
                               "production"]},
        "project_id": _ID_FIELD,
        "profile_id": _ID_FIELD,
        "snapshot_revision": _ID_FIELD,
        "predicate_version": _ID_FIELD,
        "inputs": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["artifact_id", "sha256", "status"],
            "properties": {
                "artifact_id": _ID_FIELD,
                "sha256": _NULLABLE_SHA,
                "status": {"enum": ["present", "stale", "missing"]}}}},
        "required_predicates": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "value"],
            "properties": {"id": _ID_FIELD, "value": {"type": "boolean"},
                           "evidence": {"type": "string",
                                        "maxLength": 512}}}},
        "fact_refs": {"type": "array", "items": _ID_FIELD},
        "disposition_refs": {"type": "array", "items": _ID_FIELD},
        "cycle_check": {"type": "object", "additionalProperties": False,
                        "required": ["acyclic", "topological_order"],
                        "properties": {
                            "acyclic": {"type": "boolean"},
                            "topological_order": {"type": "array",
                                                  "items": _ID_FIELD},
                            "cycle_nodes": {"type": "array",
                                            "items": _ID_FIELD}}},
        "result": {"enum": ["pass", "fail", "blocked"]},
        "failure_codes": {"type": "array", "items": _ID_FIELD},
        "evaluator": {"type": "object", "additionalProperties": False,
                      "required": ["name", "version", "code_sha256"],
                      "properties": {"name": _ID_FIELD, "version": _ID_FIELD,
                                     "code_sha256": _SHA256_FIELD}},
        "evaluation_metadata": {"type": "object", "additionalProperties": False,
                                "required": ["evaluated_at", "host",
                                             "elapsed_s"],
                                "properties": {
                                    "evaluated_at": _NULLABLE_ID,
                                    "host": _NULLABLE_ID,
                                    "elapsed_s": {"oneOf": [
                                        {"type": "null"},
                                        {"type": "number",
                                         "minimum": 0}]}}},
    },
}


# ---------------------------------------------------------------------------
# §1.4 disposition record（Human 处置；无事实改写权）
# ---------------------------------------------------------------------------

_DISPOSITION = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "disposition_id", "fact_refs", "kind",
                 "scope", "rationale_code", "approver", "approver_role"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "disposition_id": _ID_FIELD,
        "fact_refs": {"type": "array", "minItems": 1, "items": _ID_FIELD},
        "kind": {"enum": ["accept", "reject", "waive", "defer",
                          "known_open"]},
        "scope": {"enum": ["candidate", "constraint", "checker", "physics",
                           "external", "waiver_policy", "adoption",
                           "profile", "corpus"]},
        "rationale_code": _ID_FIELD,
        "rationale_text": {"type": "string", "maxLength": 4096},
        "approver": _ID_FIELD,
        "approver_role": _ID_FIELD,
        "waiver_policy_ref": _NULLABLE_ID,
        "expiry": _NULLABLE_ID,
        "supersedes": {"type": "array", "items": _ID_FIELD},
    },
}


# ---------------------------------------------------------------------------
# §1.3 judge_pre / judge_post / judge_fact
# ---------------------------------------------------------------------------

_JUDGE_COMMON = {
    "project_id": _ID_FIELD, "profile_id": _ID_FIELD,
    "candidate_id": _ID_FIELD,
    "source_snapshot_sha256": _SHA256_FIELD,
    "staging_snapshot_sha256": _NULLABLE_SHA,
    "constraints_sha256": _NULLABLE_SHA, "structures_sha256": _NULLABLE_SHA,
    "registry_sha256": _NULLABLE_SHA, "ff_plan_sha256": _NULLABLE_SHA,
    "policy_sha256": _NULLABLE_SHA, "toolchain_lock_sha256": _SHA256_FIELD,
    "executor": {"type": "object", "additionalProperties": False,
                 "required": ["backend", "protocol", "version", "capability"],
                 "properties": {
                     "backend": _ID_FIELD, "protocol": _ID_FIELD,
                     "version": _NULLABLE_ID, "capability": _ID_FIELD}},
    "request_or_argv_hash": _NULLABLE_SHA,
}

_JUDGE_PRE = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "judge_kind", "execution_id",
                 "write_scope", "allowlist", "required_checks",
                 "patch_preconditions"] ,
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "judge_kind": {"const": "judge_pre"},
        "execution_id": _ID_FIELD,
        **_JUDGE_COMMON,
        "write_scope": {"enum": ["staging_only", "none"]},
        "allowlist": {"type": "array", "items":
                      {"type": "string", "pattern": _REL_POSIX,
                       "maxLength": 512}},
        "required_checks": {"type": "array", "items": _ID_FIELD},
        "patch_preconditions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "value"],
            "properties": {"id": _ID_FIELD, "value": {"type": "boolean"}}}},
        "pre_ok": {"type": "boolean"},
    },
}

# judge_fact 不得含处置语义键（§1.3 红线；validator 侧强制）
_FACT_FORBIDDEN = ("accept", "reject", "waive", "approved", "waived",
                   "disposition", "gate_pass")

_JUDGE_FACT_ITEM = {
    "type": "object", "additionalProperties": False,
    "required": ["fact_id", "observer", "observation"],
    "properties": {
        "fact_id": _ID_FIELD,
        "observer": {"enum": ["kicad_cli", "deterministic_evaluator",
                              "replay", "solver", "test_manifest",
                              "external_backend"]},
        "observation": {"type": "object", "additionalProperties": False,
                        "required": ["kind", "value"],
                        "properties": {
                            "kind": {"enum": ["count", "boolean", "hash_equality",
                                              "solver_tri_state", "layer_purity",
                                              "test_result", "text_ref"]},
                            "value": {"oneOf": [{"type": "integer"},
                                                {"type": "boolean"},
                                                {"type": "string",
                                                 "maxLength": 512}]},
                            "unit": {"type": "string", "maxLength": 64},
                            "ref_sha256": _NULLABLE_SHA}},
        "immutable": {"const": True},
    },
}

_JUDGE_POST = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "judge_kind", "execution_id",
                 "pre_record_ref", "output_hash", "l1_legal", "layer_pure",
                 "drc_batch_ref", "drc_final_ref", "erc_ref",
                 "test_manifest_hash", "replay_ref", "solver",
                 "external_status", "physics_status", "bring_up_status",
                 "rollback_status"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "judge_kind": {"const": "judge_post"},
        "execution_id": _ID_FIELD,
        "pre_record_ref": _SHA256_FIELD,
        **_JUDGE_COMMON,
        "output_hash": _NULLABLE_SHA,
        "l1_legal": {"type": "boolean"},
        "layer_pure": {"type": "boolean"},
        "drc_batch_ref": _NULLABLE_SHA,   # severity-error 批检产物 hash
        "drc_final_ref": _NULLABLE_SHA,   # severity-all 终检产物 hash
        "erc_ref": _NULLABLE_SHA,
        "test_manifest_hash": _NULLABLE_SHA,
        "replay_ref": _NULLABLE_SHA,
        "solver": {"type": "object", "additionalProperties": False,
                   "required": ["status", "proof_ref"],
                   "properties": {
                       "status": {"enum": ["SAT", "UNSAT", "UNKNOWN"]},
                       "proof_ref": _NULLABLE_SHA}},
        "external_status": {"enum": ["pass", "fail", "unknown",
                                     "not_available", "not_executed",
                                     "stale", "not_required"]},
        "physics_status": {"enum": ["pass", "fail", "unknown",
                                    "not_available", "not_executed",
                                    "stale", "not_required"]},
        "bring_up_status": {"enum": ["pass", "fail", "unknown",
                                     "not_available", "not_executed",
                                     "stale", "not_required"]},
        "rollback_status": {"enum": ["not_needed", "armed", "executed",
                                     "failed"]},
        "facts": {"type": "array", "items": _JUDGE_FACT_ITEM},
        "post_ok": {"type": "boolean"},
    },
}


# ---------------------------------------------------------------------------
# TD1 decision-ledger entry（追加式 hash 链；schema_validation 内嵌）
# ---------------------------------------------------------------------------

_LEDGER_ENTRY = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "entry_seq", "entry_id",
                 "entry_kind", "prev_entry_sha256", "entry_sha256",
                 "ledger_head_sha256", "authority", "trust_level",
                 "schema_validation"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "entry_seq": {"type": "integer", "minimum": 0},
        "entry_id": _ID_FIELD,
        "entry_kind": {"enum": ["proposal", "judge_pre", "execution",
                                "judge_post", "critic", "disposition",
                                "gate", "checkpoint", "adoption",
                                "backtest", "signoff", "queue_event",
                                "supersede", "revoke"]},
        "prev_entry_sha256": _NULLABLE_SHA,   # 首条= Genesis，恒 null
        "entry_sha256": _SHA256_FIELD,        # 记录体（不含自身）canonical hash
        "ledger_head_sha256": _SHA256_FIELD,
        "project_id": _NULLABLE_ID, "profile_id": _NULLABLE_ID,
        "snapshot_revision": _NULLABLE_ID,
        "candidate_id": _NULLABLE_ID,
        "proposal_id": _NULLABLE_ID, "proposal_sha256": _NULLABLE_SHA,
        "judge_pre_hash": _NULLABLE_SHA, "judge_post_hash": _NULLABLE_SHA,
        "judge_fact_refs": {"type": "array", "items": _SHA256_FIELD},
        "execution_ref": _NULLABLE_SHA,
        "critic_run_hash": _NULLABLE_SHA,
        "disposition_refs": {"type": "array", "items": _ID_FIELD},
        "gate_record_hash": _NULLABLE_SHA,
        "artifact_hashes": {"type": "object",
                            "additionalProperties":
                                {"type": "string", "pattern": _HASH64}},
        "toolchain_lock_sha256": _NULLABLE_SHA,
        "authority": {"enum": ["kicad_cli", "deterministic_evaluator",
                               "solver", "replay", "test_manifest",
                               "external_backend", "critic_model",
                               "human", "ledger_validator"]},
        "trust_level": {"enum": ["untrusted", "observed", "verified"]},
        "actor": _NULLABLE_ID, "actor_role": _NULLABLE_ID,
        "provenance_refs": {"type": "array", "items": _SHA256_FIELD},
        "schema_validation": {"type": "object", "additionalProperties": False,
                              "required": ["schema_name", "schema_sha256",
                                           "valid"],
                              "properties": {
                                  "schema_name": _ID_FIELD,
                                  "schema_sha256": _SHA256_FIELD,
                                  "valid": {"type": "boolean"},
                                  "errors": {"type": "array",
                                             "items": {"type": "string",
                                                       "maxLength": 512}}}},
        "supersedes": {"type": "array", "items": _SHA256_FIELD},
        "revokes": {"type": "array", "items": _SHA256_FIELD},
        "payload_ref": _NULLABLE_SHA,   # 大负载（报告等）只挂 hash 不内联
    },
}


# ---------------------------------------------------------------------------
# TD4 critic run record + TD5 路由字段
# ---------------------------------------------------------------------------

_CRITIC_RUN = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "critic_run_id", "candidate_id",
                 "critic_status", "model", "input_hashes",
                 "schema_validation", "flags"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "critic_run_id": _ID_FIELD,
        "candidate_id": _ID_FIELD,
        "project_id": _NULLABLE_ID, "profile_id": _NULLABLE_ID,
        "snapshot_revision": _NULLABLE_ID,
        "critic_status": {"enum": ["executed", "not_executed", "error",
                                   "invalid", "stale"]},
        "model": {"type": "object", "additionalProperties": False,
                  "required": ["provider", "version", "approved"],
                  "properties": {
                      "provider": _ID_FIELD, "version": _NULLABLE_ID,
                      "approved": {"type": "boolean"},
                      "prompt_template_sha256": _NULLABLE_SHA,
                      "config_sha256": _NULLABLE_SHA}},
        "input_hashes": {"type": "object",
                         "additionalProperties":
                             {"type": "string", "pattern": _HASH64}},
        "input_hashes_match": {"type": "boolean"},
        "schema_validation": {"type": "object", "additionalProperties": False,
                              "required": ["valid"],
                              "properties": {
                                  "valid": {"type": "boolean"},
                                  "schema_sha256": _NULLABLE_SHA}},
        "flags": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["category", "confidence"],
            "properties": {
                "category": {"enum": ["silk_readability", "courtyard_crowding",
                                      "placement_pattern_anomaly",
                                      "suspicious_reroute", "doc_artifact_mismatch",
                                      "other_advisory"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence_ref": _NULLABLE_SHA,
                "location": {"type": "string", "maxLength": 256}}}},
        "calibration": {"type": "object", "additionalProperties": False,
                        "required": ["in_calibrated_range"],
                        "properties": {
                            "in_calibrated_range": {"type": "boolean"},
                            "domain_ref": _NULLABLE_SHA}},
        "evidence_refs": {"type": "array", "items": _SHA256_FIELD},
        "profile_promotion_state": {"enum": ["not_promoted", "shadow",
                                             "noise_reduction",
                                             "full_jury", "candidate"]},
        "advisory_only": {"const": True},
        "critic_outcome": {"enum": ["advisory", "blocked"]},
        "auto_route": {"type": "object", "additionalProperties": False,
                       "required": ["eligible", "status", "failed_conditions"],
                       "properties": {
                           "eligible": {"type": "boolean"},
                           "status": {"enum": ["queue_deprioritized",
                                               "manual_queue",
                                               "critic_auto_route_blocked"]},
                           "failed_conditions": {"type": "array",
                                                 "items": _ID_FIELD}}},
    },
}


# ---------------------------------------------------------------------------
# TD5 queue event（追加式 queue-event-ledger.jsonl）
# ---------------------------------------------------------------------------

_QUEUE_EVENT = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "event_id", "event_seq", "event",
                 "item_id", "actor", "actor_role", "prev_event_sha256",
                 "event_sha256"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "event_id": _ID_FIELD,
        "event_seq": {"type": "integer", "minimum": 0},
        "event": {"enum": ["enqueue", "assign", "review", "escalate",
                           "approve", "reject", "downgrade", "expire"]},
        "item_id": _ID_FIELD,
        "project_id": _NULLABLE_ID, "profile_id": _NULLABLE_ID,
        "snapshot_revision": _NULLABLE_ID,
        "fact_ref": _NULLABLE_SHA, "gate_ref": _NULLABLE_SHA,
        "critic_ref": _NULLABLE_SHA,
        "actor": _ID_FIELD, "actor_role": _ID_FIELD,
        "reason_code": _NULLABLE_ID,
        "prev_event_sha256": _NULLABLE_SHA,
        "event_sha256": _SHA256_FIELD,
        "supersedes": {"type": "array", "items": _ID_FIELD},
    },
}


# ---------------------------------------------------------------------------
# TD6 physics/bring-up 三轨合同
# ---------------------------------------------------------------------------

_PHYSICS_STATUS = {"enum": ["pass", "fail", "unknown", "not_available",
                            "not_executed", "stale"]}

_PHYSICS_ITEM = {
    "type": "object", "additionalProperties": False,
    "required": ["item_id", "track", "status", "required_scope_defined",
                 "coverage_complete", "input_model_complete", "executed",
                 "convergence_or_validity_pass", "limit_pass",
                 "uncertainty_acceptable", "external_approval_present",
                 "bring_up_disposition"],
    "properties": {
        "item_id": _ID_FIELD,
        "track": {"enum": ["physics_screening", "external_required",
                           "bring_up"]},
        "status": dict(_PHYSICS_STATUS),
        "required_scope_defined": {"type": "boolean"},
        "coverage_complete": {"type": "boolean"},
        "input_model_complete": {"type": "boolean"},
        "executed": {"type": "boolean"},
        "convergence_or_validity_pass": {"type": "boolean"},
        "limit_pass": {"type": "boolean"},
        "uncertainty_acceptable": {"type": "boolean"},
        "external_approval_present": {"type": "boolean"},
        "bring_up_disposition": {"enum": ["not_available", "pass", "fail",
                                          "deferred"]},
        "net_or_relation": {"type": "string", "maxLength": 256},
        "model_or_tool": _NULLABLE_ID, "model_version": _NULLABLE_ID,
        "input_hashes": {"type": "object",
                         "additionalProperties":
                             {"type": "string", "pattern": _HASH64}},
        "measurement_convention": _NULLABLE_ID,
        "limits": {"type": "object",
                   "additionalProperties": {"type": ["number", "string"]}},
        "uncertainty": {"type": ["number", "null"]},
        "fidelity": _NULLABLE_ID,
        "authority": {"enum": ["openems", "scikit_rf", "vendor_tool",
                               "lab_measurement", "datasheet_derived",
                               "none"]},
        "review_ref": _NULLABLE_SHA,
        "approval_ref": _NULLABLE_SHA,
        "measured_value": {"type": ["number", "string", "null"]},
        "note": {"type": "string", "maxLength": 1024},
    },
}

_PHYSICS_REPORT = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project_id", "profile_id",
                 "snapshot_revision", "items", "physics_gate"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "project_id": _ID_FIELD, "profile_id": _ID_FIELD,
        "snapshot_revision": _ID_FIELD,
        "items": {"type": "array", "items": _PHYSICS_ITEM},
        "physics_gate": {"enum": ["pass", "fail", "blocked", "not_required"]},
        "gate_failure_codes": {"type": "array", "items": _ID_FIELD},
    },
}

_PHYSICS_COVERAGE = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project_id", "profile_id",
                 "snapshot_revision", "required_scope",
                 "covered_scope", "coverage_complete"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "project_id": _ID_FIELD, "profile_id": _ID_FIELD,
        "snapshot_revision": _ID_FIELD,
        "required_scope": {"type": "array", "items": _ID_FIELD},
        "covered_scope": {"type": "array", "items": _ID_FIELD},
        "coverage_complete": {"type": "boolean"},
        "missing_scope": {"type": "array", "items": _ID_FIELD},
        "note": {"type": "string", "maxLength": 1024},
    },
}

# 真实回板记录（TD6：板/序列号/Rev、治具、固件、原始测量、环境、operator、
# 逐项结果；缺任一必需字段即 not_available——fail-closed）
_BRING_UP_REPORT = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project_id", "profile_id", "board_serial",
                 "board_revision", "fixture", "firmware_version",
                 "test_software_version", "raw_measurements", "environment",
                 "operator", "input_hash", "output_hash", "items",
                 "bring_up_status"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "project_id": _ID_FIELD, "profile_id": _ID_FIELD,
        "board_serial": _ID_FIELD, "board_revision": _ID_FIELD,
        "fixture": _ID_FIELD, "firmware_version": _ID_FIELD,
        "test_software_version": _ID_FIELD,
        "raw_measurements": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["measurement_id", "quantity", "value", "unit"],
            "properties": {
                "measurement_id": _ID_FIELD,
                "quantity": _ID_FIELD,
                "value": {"type": ["number", "string"]},
                "unit": _ID_FIELD,
                "limit": {"type": ["number", "string", "null"]},
                "pass": {"type": "boolean"}}}},
        "environment": {"type": "object",
                        "additionalProperties": {"type": "string"}},
        "operator": _ID_FIELD,
        "input_hash": _SHA256_FIELD, "output_hash": _SHA256_FIELD,
        "items": {"type": "array", "items": _ID_FIELD},
        "bring_up_status": dict(_PHYSICS_STATUS),
    },
}


# ---------------------------------------------------------------------------
# TD7 外部执行引擎 execution record（CLI 与 MCP 分列；不受信任子系统）
# ---------------------------------------------------------------------------

_EXTERNAL_EXECUTION = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "execution_id", "project_id", "profile_id",
                 "source_snapshot_sha256", "staging_path_sha256", "backend",
                 "protocol", "tool_version", "toolchain_lock_sha256",
                 "request_sha256", "response_sha256", "argv_or_rpc_hash",
                 "started_by", "timeout_s", "resource_limits",
                 "network_policy", "write_scope", "live_board_touched"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "execution_id": _ID_FIELD,
        "project_id": _ID_FIELD, "profile_id": _ID_FIELD,
        "candidate_id": _NULLABLE_ID,
        "source_snapshot_sha256": _SHA256_FIELD,
        "staging_path_sha256": _SHA256_FIELD,
        "backend": {"enum": ["freerouting-cli-jar", "freerouting-mcp",
                             "kicad-cli", "deterministic-internal"]},
        "protocol": {"enum": ["cli-argv", "mcp-jsonrpc", "rest", "internal"]},
        "tool_version": _NULLABLE_ID,
        "toolchain_lock_sha256": _SHA256_FIELD,
        "request_sha256": _NULLABLE_SHA,
        "response_sha256": _NULLABLE_SHA,
        "argv_or_rpc_hash": _NULLABLE_SHA,
        "started_by": _ID_FIELD,
        "timeout_s": {"type": "integer", "minimum": 1},
        "resource_limits": {"type": "object", "additionalProperties": False,
                            "required": ["max_threads"],
                            "properties": {
                                "max_threads": {"type": "integer",
                                                "minimum": 1},
                                "max_memory_mb": {"type": ["integer", "null"],
                                                  "minimum": 1}}},
        "network_policy": {"enum": ["deny", "loopback_only"]},
        "write_scope": {"enum": ["staging_only", "none"]},
        "live_board_touched": {"type": "boolean"},
        "exit_status": {"type": ["integer", "null"]},
        "fallback_reason": _NULLABLE_ID,
        "peer_identity": _NULLABLE_ID,        # MCP 专用：固定 peer 标识
        "method_allowlist": {"type": "array",
                             "items": {"type": "string", "maxLength": 128}},
    },
}


# ---------------------------------------------------------------------------
# TD11 proposal patch（execution_allowed 恒 false；操作白名单五类）
# ---------------------------------------------------------------------------

_PROPOSAL_PATCH = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "patch_id", "base_revision",
                 "base_artifact_hash", "target_scope", "operation_kind",
                 "changes", "preconditions", "expected_affected_nodes",
                 "rollback_plan", "proposer_id", "rationale",
                 "evidence_refs", "random_seed", "determinism_claim",
                 "execution_allowed"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "patch_id": _ID_FIELD,
        "base_revision": _ID_FIELD,
        "base_artifact_hash": _SHA256_FIELD,
        "target_scope": _ID_FIELD,
        "operation_kind": {"enum": ["policy_parameter_candidate",
                                    "route_order_candidate",
                                    "threshold_candidate",
                                    "advisory_checker_candidate",
                                    "profile_text_candidate"]},
        "changes": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["path", "op", "value"],
            "properties": {
                "path": {"type": "string", "pattern": _REL_POSIX,
                         "maxLength": 512},
                "op": {"enum": ["set", "propose"]},
                "value": {}}}},
        "preconditions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "value"],
            "properties": {"id": _ID_FIELD, "value": {"type": "boolean"}}}},
        "expected_affected_nodes": {"type": "array", "items": _ID_FIELD},
        "rollback_plan": {"type": "string", "maxLength": 4096},
        "proposer_id": _ID_FIELD,
        "model_version": _NULLABLE_ID,
        "prompt_template_hash": _NULLABLE_SHA,
        "rationale": {"type": "string", "maxLength": 8192},
        "evidence_refs": {"type": "array", "items": _SHA256_FIELD},
        "random_seed": {"type": ["integer", "null"]},
        "determinism_claim": {"enum": ["byte_exact", "semantic",
                                       "not_claimed"]},
        "execution_allowed": {"const": False},
    },
}


# ---------------------------------------------------------------------------
# TD3 搜索空间声明（autotuning 参数空间；低自由度合同）
# ---------------------------------------------------------------------------

_SEARCH_SPACE = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "space_id", "profile_id", "parameters"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "space_id": _ID_FIELD, "profile_id": _ID_FIELD,
        "parameters": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "kind", "domain"],
            "properties": {
                "name": _ID_FIELD,
                "kind": {"enum": ["integer", "float", "enum", "boolean"]},
                "domain": {"type": "object", "additionalProperties": False,
                           "required": ["values"],
                           "properties": {
                               "values": {"type": "array", "minItems": 1},
                               "min": {"type": "number"},
                               "max": {"type": "number"},
                               "step": {"type": "number",
                                        "exclusiveMinimum": 0}}},
                "unit": {"type": "string", "maxLength": 64},
                "normalization": {"enum": ["none", "min_max", "z_score",
                                           "rank"]},
                "tolerance": {"type": "number", "minimum": 0}}}},
        "max_parameter_count": {"type": "integer", "minimum": 1},
        "min_samples_per_kind": {"type": "integer", "minimum": 1},
        "max_step": {"type": ["number", "null"]},
        "outlier_policy": {"enum": ["keep", "winsorize", "trim",
                                    "blocked"]},
        "confidence_interval": {"type": ["number", "null"],
                                "exclusiveMinimum": 0},
        "explore_real_execution_ratio": {"type": "number", "minimum": 0,
                                         "maximum": 1},
        "optimizer": _NULLABLE_ID,
        "record_env": {"type": "object",
                       "additionalProperties": {"type": "string"}},
    },
}


# ---------------------------------------------------------------------------
# TD10 project manifest / profile（v2.1 §4.2/§5.2 吸收 + v3.0 扩展字段：
# 参数搜索域、dataset split、executable allowlist、后端声明；null=缺失输入
# 永不回退——L7 缺证据闭门律）
# ---------------------------------------------------------------------------

_INPUT_PATH = {"oneOf": [{"type": "null"},
                         {"type": "string", "pattern": _REL_POSIX,
                          "maxLength": 512}]}

_PROJECT_MANIFEST = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project_id", "profile_id", "eda",
                 "inputs", "outputs"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "project_id": _ID_FIELD,
        "profile_id": _ID_FIELD,
        "eda": {"type": "object", "additionalProperties": False,
                "required": ["name"],
                "properties": {"name": _ID_FIELD,
                               "version": _NULLABLE_ID}},
        "inputs": {"type": "object", "additionalProperties": False,
                   "required": ["board", "schematic", "netlist", "placement",
                                "stackup", "constraints", "structures",
                                "toolchain_lock", "identity_map"],
                   "properties": {k: dict(_INPUT_PATH) for k in (
                       "board", "schematic", "netlist", "placement",
                       "stackup", "constraints", "structures",
                       "toolchain_lock", "identity_map")}},
        "backtest": {"type": "object", "additionalProperties": False,
                     "properties": {k: {"oneOf": [
                         dict(_INPUT_PATH),
                         {"type": "array", "items": dict(_INPUT_PATH)}]}
                         for k in ("opens", "reference_layout",
                                   "reference_route", "drc_baseline",
                                   "datasets")}},
        "policy": {"type": "object", "additionalProperties": False,
                   "properties": {k: dict(_INPUT_PATH) for k in (
                       "profile", "core_policy", "feedforward_policy",
                       "optimization_policy", "model_policy")}},
        "external_authority": {"type": "object", "additionalProperties": False,
                               "properties": {k: dict(_INPUT_PATH)
                                              for k in ("impedance", "si",
                                                        "pi", "thermal",
                                                        "emc", "dfm")}},
        "params": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "kind", "domain"],
            "properties": {
                "name": _ID_FIELD,
                "kind": {"enum": ["integer", "float", "enum", "boolean"]},
                "domain": {"type": "object", "additionalProperties": False,
                           "required": ["values"],
                           "properties": {
                               "values": {"type": "array", "minItems": 1},
                               "min": {"type": "number"},
                               "max": {"type": "number"},
                               "step": {"type": "number",
                                        "exclusiveMinimum": 0}}},
                "unit": {"type": ["string", "null"], "maxLength": 64},
                "source": _NULLABLE_ID}}},
        "critical_nets": {"type": "array", "items": _ID_FIELD},
        "dataset_splits": {"oneOf": [{"type": "null"},
                                     {"type": "object",
                                      "additionalProperties": False,
                                      "properties": {k: {"type": "array",
                                                         "items": _ID_FIELD}
                                                     for k in ("train",
                                                               "validation",
                                                               "holdout",
                                                               "external_eval")}}]},
        "outputs": {"type": "object", "additionalProperties": False,
                    "required": ["root"],
                    "properties": {
                        "root": {"type": "string", "pattern": _REL_POSIX,
                                 "maxLength": 256},
                        "preserve_history": {"type": "boolean"}}},
        "toolchain": {"type": "object", "additionalProperties": False,
                      "properties": {
                          "lock_path": dict(_INPUT_PATH),
                          "executable_allowlist": {"type": "array",
                                                   "items": {"type": "string",
                                                             "maxLength": 512}},
                          "backend_declarations": {"type": "array",
                                                   "items": {"type": "object",
                                                             "additionalProperties": True}}}},
        "path_base": {"enum": ["workspace_root", "manifest_dir"]},
        "compatibility": {"type": "object", "additionalProperties": False,
                          "required": ["mode"],
                          "properties": {
                              "mode": {"enum": ["explicit_manifest",
                                                "compatibility_default"]},
                              "warning": {"type": "boolean"}}},
    },
}

_PROFILE = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "profile_id"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "profile_id": _ID_FIELD,
        "project_id": _NULLABLE_ID,
        "layers": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "role"],
            "properties": {"name": _ID_FIELD,
                           "role": {"enum": ["signal", "plane", "power"]}}}},
        "kicad_cli": {"type": "object", "additionalProperties": False,
                      "required": ["drc_batch_severity",
                                   "drc_final_severity", "refill_policy"],
                      "properties": {
                          "drc_batch_severity": {
                              "const": "severity-error"},
                          "drc_final_severity": {
                              "const": "severity-all"},
                          "refill_policy": {"enum": ["none",
                                                     "kicad-cli-refill"]}}},
        "critical_net_set": {"type": "array", "items": _ID_FIELD},
        "physics_required": {"type": "array", "items": _ID_FIELD},
        "external_required": {"type": "array", "items": _ID_FIELD},
        "bring_up_required": {"type": "boolean"},
        "measurement_conventions": {"type": ["object", "null"],
                                    "additionalProperties":
                                        {"type": "string"}},
        "thresholds": {"type": "object",
                       "additionalProperties": {"type": ["number", "string",
                                                         "boolean"]}},
        "anchors": {"type": "array", "items": _ID_FIELD},
        "keepouts": {"type": "array", "items": {
            "type": "object", "additionalProperties": True}},
    },
}


# ---------------------------------------------------------------------------
# P2 采纳追加（APR-0012 @2026-09-06，追加式）：三类设计对象角色声明 v1
# （contract=pcbflow.artifact_roles#artifact-role-declaration-v1；spec 从
# pcbflow/artifact_roles.py 构造器实际输出形状+tests/test_p2_artifact_roles.py
# 夹具忠实推导。追加式注册：REGISTRY_VERSION 保持 3.0 不动——schema_hash
# 逐条独立（输入={name, REGISTRY_VERSION, schema}），追加不改既有条目
# 哈希、不破坏 disposition-APR-0002 冻结基线可复现性；语义限定见
# out/v3-approvals/disposition-APR-0012-schema-registration.json。
# 角色条件约束经 anyOf 表达（analysis 恒 None check_scope / staging 必填
# transform+check_scope+rule_dependencies / source loss_notes 恒 None、
# transform 恒无或 identity）。「staging ≥1 执行类能力」「staging 声明
# 分析能力须 loss_notes 为空」「loss_notes 非空 dict」为语义约束，超出本
# 验证器子集表达力（无 contains/minProperties），由 pcbflow.artifact_roles
# 构造器/validate_declaration 单一事实源强制——schema=形状合同，模块=
# 语义 authority。）
# ---------------------------------------------------------------------------

_ART_ROLE_CAPS_ALL = ["analysis_stats", "analysis_topology",
                      "analysis_features", "tool_loadable",
                      "tool_checkable", "tool_transform_target"]
_ART_ROLE_CAPS_ANALYSIS = ["analysis_stats", "analysis_topology",
                           "analysis_features"]
_ART_ROLE_CHECK_SCOPES = ["bare_board_default_rules", "project_custom_rules"]

_ARTIFACT_ROLE_DECLARATION = {
    "type": "object",
    "additionalProperties": False,
    "required": ["contract", "proposal_status", "role", "artifact_id",
                 "format_id", "format_version", "capabilities",
                 "source_binding", "transform", "output_sha256",
                 "rule_dependencies", "check_scope", "loss_notes"],
    "properties": {
        "contract": {"const":
                     "pcbflow.artifact_roles#artifact-role-declaration-v1"},
        "proposal_status": {"type": "string", "minLength": 1},
        "role": {"enum": ["source_design_package",
                          "normalized_analysis_model",
                          "staging_execution_package"]},
        "artifact_id": {"type": "string", "minLength": 1},
        "format_id": {"type": "string", "minLength": 1},
        "format_version": {"type": "string", "minLength": 1},
        "capabilities": {"type": "array", "minItems": 1, "maxItems": 6,
                         "items": {"enum": _ART_ROLE_CAPS_ALL}},
        "source_binding": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "manifest_ref", "entry_key",
                         "source_sha256"],
            "properties": {
                "kind": {"enum": ["dataset_manifest_entry"]},
                "manifest_ref": {"type": "string", "minLength": 1},
                "entry_key": {"type": "string", "minLength": 1},
                "source_sha256": _SHA256_FIELD}},
        "transform": {"oneOf": [
            {"type": "null"},
            {"type": "object", "additionalProperties": False,
             "required": ["description", "tool", "tool_version", "saved_by"],
             "properties": {
                 "description": {"type": "string", "minLength": 1},
                 "tool": {"type": "string", "minLength": 1},
                 "tool_version": {"type": "string", "minLength": 1},
                 "saved_by": {"type": "string", "minLength": 1}}}]},
        "output_sha256": _SHA256_FIELD,
        "rule_dependencies": {"type": "array",
                              "items": {"type": "string", "minLength": 1}},
        "check_scope": {"oneOf": [{"type": "null"},
                                  {"enum": _ART_ROLE_CHECK_SCOPES}]},
        "loss_notes": {"oneOf": [
            {"type": "null"},
            {"type": "object", "additionalProperties":
                {"type": "string", "minLength": 1}},
            {"type": "array", "minItems": 1,
             "items": {"type": "string", "minLength": 1}}]},
    },
    "anyOf": [
        {   # source：loss_notes 恒 None；transform 恒无（None 或 identity）
            "properties": {
                "role": {"const": "source_design_package"},
                "transform": {"oneOf": [
                    {"type": "null"},
                    {"type": "object", "required": ["description"],
                     "properties": {"description": {"const": "identity"}}}]},
                "loss_notes": {"type": "null"}}},
        {   # analysis：check_scope 恒 None（非执行对象）；capabilities 仅
            # 分析类；transform 必填对象；loss_notes 必填非空
            "properties": {
                "role": {"const": "normalized_analysis_model"},
                "check_scope": {"type": "null"},
                "capabilities": {"items": {"enum": _ART_ROLE_CAPS_ANALYSIS}},
                "transform": {"type": "object"},
                "loss_notes": {"oneOf": [
                    {"type": "object", "additionalProperties":
                        {"type": "string", "minLength": 1}},
                    {"type": "array", "minItems": 1,
                     "items": {"type": "string", "minLength": 1}}]}}},
        {   # staging：transform 必填对象；check_scope 必填显式（禁混称）；
            # rule_dependencies 必填非空
            "properties": {
                "role": {"const": "staging_execution_package"},
                "transform": {"type": "object"},
                "check_scope": {"enum": _ART_ROLE_CHECK_SCOPES},
                "rule_dependencies": {"minItems": 1}}},
    ],
}


# ---------------------------------------------------------------------------
# P2-7 采纳追加（@2026-09-10，追加式）：逐旗标人工裁定记录 v1
# （contract=pcbflow.critic#critic-flag-verdict-v1；evaluation-protocol-v2
# P2-7「逐旗标人工裁定」/P2-5「三分口径」的数据载体。追加式注册：
# REGISTRY_VERSION 保持 3.0 不动——schema_hash 逐条独立
# （输入={name, REGISTRY_VERSION, schema}），追加不改既有条目哈希、不破坏
# disposition-APR-0002 冻结基线可复现性。verdict 为 fail-closed 封闭四值集：
# confirmed（裁定为真报）/false_positive（裁定为误报）/unadjudicated
# （尚无人工裁定）/uncertain（人工判读后仍不能定）；前两值为「可判定」侧，
# 后两值与无裁定记录（pending）不计入判断一致率分母任何一侧（P2-5）。
# critic_run_record_sha256=被裁定 critic run 记录体的 canonical sha256
# （provenance 绑定；schema 层可选、聚合语义层强制，见
# pcbflow.critic.flag_verdict_agreement 的 fail-closed 校验）。）
# ---------------------------------------------------------------------------

_CRITIC_FLAG_VERDICT_V1 = {
    "type": "object", "additionalProperties": False,
    "required": ["verdict_record_id", "critic_run_id", "flag_id",
                 "verdict", "adjudicator", "declared_date"],
    "properties": {
        "schema_version": {"const": SCHEMA_V3},
        "verdict_record_id": _ID_FIELD,
        "critic_run_id": _ID_FIELD,
        "flag_id": _ID_FIELD,
        "verdict": {"enum": ["confirmed", "false_positive",
                             "unadjudicated", "uncertain"]},
        "adjudicator": _ID_FIELD,
        "declared_date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
        "critic_run_record_sha256": _SHA256_FIELD,
        "evidence_ref": _NULLABLE_SHA,
        "note": {"type": "string", "maxLength": 512},
    },
}


# ---------------------------------------------------------------------------
# observation 线采纳追加（@2026-09-12，追加式）：跨板学习 observation 行 v1
# （contract=pcbflow.observation#observation-row-v1；D-OBS-4 追加式注册，
# REGISTRY_VERSION 保持 3.0 不动——schema_hash 逐条独立
# （输入={name, REGISTRY_VERSION, schema}），追加不改既有条目哈希、不破坏
# disposition-APR-0002 冻结基线可复现性。schema=out/v3-obs-proposal/
# OBSERVATION-SCHEMA-PROPOSAL.md 冻结版（ADJUDICATION-2026-09-12 R9/R18）
# §2 六组字段；行构造单一事实源=pcbflow.observation（纯函数，行对象先过
# 本 schema 再落盘）。要点：快照组六键 nullable sha256、missing_basis_reason
# 必填非空（D-OBS-6 显式 null 纪律，R11 policy_hash=null 落此）；features
# 白名单=board 级五键硬编码（R17 最小集收窄，D-OBS-5 防泄漏：参考态
# routed 派生计数不入）；prediction/actual.value 可 null 但必须同对象带
# 非空 not_available_reason（anyOf 表达）；label 残差/相对残差双键或整行
# null；evaluation_metadata 三键恒 null 且不进行 required（§2.6，不进
# row_core_sha256）；stage 枚举=主路径六段；action 枚举=SPEC §7.2 十动作
# + null。）
# ---------------------------------------------------------------------------

_OBSERVATION_ROW_V1 = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "observation_id", "run_id", "project_id", "profile_id",
        "board_revision", "stage",
        "registry_snapshot_hash", "structures_hash", "constraints_sha256",
        "placement_snapshot_sha256", "board_snapshot_sha256", "policy_hash",
        "missing_basis_reason",
        "row_id", "net_id", "relation_id", "resource_id",
        "features", "action", "prediction", "actual", "actual_source",
        "label", "label_convention", "measurement_convention",
        "leakage_group", "split", "row_core_sha256",
    ],
    "properties": {
        "observation_id": {"type": "string", "pattern": "^[A-Za-z0-9._+-]+$"},
        "run_id": {"type": "string", "minLength": 1},
        "project_id": _ID_FIELD,
        "profile_id": _ID_FIELD,
        "board_revision": {"type": "string", "minLength": 1},
        "stage": {"enum": ["audit", "compile", "enum", "feedforward",
                           "manifest", "route_check"]},
        "registry_snapshot_hash": _NULLABLE_SHA,
        "structures_hash": _NULLABLE_SHA,
        "constraints_sha256": _NULLABLE_SHA,
        "placement_snapshot_sha256": _NULLABLE_SHA,
        "board_snapshot_sha256": _NULLABLE_SHA,
        "policy_hash": _NULLABLE_SHA,
        "missing_basis_reason": {"type": "string", "minLength": 1},
        "row_id": {"type": "string", "minLength": 1},
        "net_id": _NULLABLE_ID,
        "relation_id": _NULLABLE_ID,
        "resource_id": _NULLABLE_ID,
        "features": {
            "type": "object", "additionalProperties": False,
            "required": ["footprint_count", "named_net_count", "net_count",
                         "pad_count", "unnamed_net_count"],
            "properties": {
                "footprint_count": {"type": "integer", "minimum": 0},
                "named_net_count": {"type": "integer", "minimum": 0},
                "net_count": {"type": "integer", "minimum": 0},
                "pad_count": {"type": "integer", "minimum": 0},
                "unnamed_net_count": {"type": "integer", "minimum": 0},
            },
        },
        "action": {"enum": [None, "reserve_escape_slots", "reserve_corridor",
                            "assign_preferred_layer", "reserve_lane",
                            "reserve_via_budget",
                            "reserve_return_stitching",
                            "protect_power_loop", "protect_keepout",
                            "set_route_order", "propose_pin_swap"]},
        "prediction": {
            "type": "object", "additionalProperties": False,
            "required": ["value", "unit", "basis", "model"],
            "properties": {
                "value": {"oneOf": [{"type": ["number", "string"]},
                                    {"type": "null"}]},
                "unit": {"oneOf": [{"type": "string", "minLength": 1},
                                   {"type": "null"}]},
                "basis": {"type": "array",
                          "items": {"type": "string", "minLength": 1}},
                "model": {"type": "string", "minLength": 1},
                "not_available_reason": {"type": "string", "minLength": 1},
            },
            "anyOf": [
                {"properties": {"value": {"type": ["number", "string"]}}},
                {"required": ["not_available_reason"],
                 "properties": {"not_available_reason":
                                {"type": "string", "minLength": 1}}},
            ],
        },
        "actual": {
            "type": "object", "additionalProperties": False,
            "required": ["value", "unit"],
            "properties": {
                "value": {"oneOf": [{"type": ["number", "string"]},
                                    {"type": "null"}]},
                "unit": {"oneOf": [{"type": "string", "minLength": 1},
                                   {"type": "null"}]},
                "not_available_reason": {"type": "string", "minLength": 1},
            },
            "anyOf": [
                {"properties": {"value": {"type": ["number", "string"]}}},
                {"required": ["not_available_reason"],
                 "properties": {"not_available_reason":
                                {"type": "string", "minLength": 1}}},
            ],
        },
        "actual_source": {
            "type": "object", "additionalProperties": False,
            "required": ["path", "field", "sha256", "authority"],
            "properties": {
                "path": {"type": "string", "pattern": _REL_POSIX},
                "field": {"type": "string", "minLength": 1},
                "sha256": _SHA256_FIELD,
                "authority": {"type": "string", "minLength": 1},
                "note": {"type": "string", "minLength": 1},
            },
        },
        "label": {
            "type": ["object", "null"], "additionalProperties": False,
            "required": ["residual", "relative_residual"],
            "properties": {
                "residual": {"oneOf": [{"type": "number"},
                                       {"type": "null"}]},
                "relative_residual": {"oneOf": [{"type": "number"},
                                                {"type": "null"}]},
            },
        },
        "label_convention": {"type": "string", "minLength": 1},
        "measurement_convention": {"type": "string", "minLength": 1},
        "leakage_group": {"type": "string", "minLength": 1},
        "split": {
            "type": "object", "additionalProperties": False,
            "required": ["dataset_id", "role", "board_id", "manifest_ref"],
            "properties": {
                "dataset_id": {"type": "string", "minLength": 1},
                "role": {"enum": ["train", "validation", "holdout",
                                  "external_eval"]},
                "board_id": {"type": "string", "minLength": 1},
                "manifest_ref": {
                    "type": "object", "additionalProperties": False,
                    "required": ["path", "sha256"],
                    "properties": {
                        "path": {"type": "string", "pattern": _REL_POSIX},
                        "sha256": _SHA256_FIELD}},
            },
        },
        "evaluation_metadata": {
            "type": "object", "additionalProperties": False,
            "required": ["evaluated_at", "host", "elapsed_s"],
            "properties": {
                "evaluated_at": {"const": None},
                "host": {"const": None},
                "elapsed_s": {"const": None},
            },
        },
        "row_core_sha256": _SHA256_FIELD,
    },
}


# REPAIR-P3 W-5 采纳追加（@2026-09-22，追加式）：toolchain_lock 四孤儿名入册
# （contract=pcbflow.compile_cmd/envelope 的 SPEC §1/§2.1 核心产物格式轴；
# toolchain_lock.json schema_versions.{constraints,coverage,envelope,
# impedance_targets}=="1.1" 此前不在注册表内=第四套版本轴孤儿名，本次按
# DOC-NAMING-CONVENTION §12 r8 命名语法 <名称>-v<N> 追加注册）。
# 追加式纪律（Option C，2026-09-21 用户批）：REGISTRY_VERSION 保持 3.0 不动，
# 既有条目零改动——schema_hash 逐条独立（输入={name, REGISTRY_VERSION,
# schema}），追加不改既有哈希、不破坏 disposition-APR-0002 冻结基线。
# 名字后缀 v1=注册代次（先例 artifact-role-declaration-v1 等），条目内
# schema_version 字段钉产物格式全版本（constraints/coverage/impedance
# const "1.1"=config.SCHEMA_*；envelope 历史实例 1.0/1.1/1.3 并存故收
# 主版本 pattern ^1\\.[0-9]+$，const 钉死会误拒既有合法件）。
# schema 形状忠实推导依据=out/{revc-a1,revc-a2,revc-a3} 三份产物实例 +
# 34 份 envelope 实例全量键集/可空性扫描 + compile_cmd.py 构建器/
# envelope.py build_envelope 的枚举合同（注册测试=tests/test_p3_schema_registry.py
# 全实例回放+负向变体+jsonschema 交叉对拍）。
# ---------------------------------------------------------------------------

_CONSTRAINTS_V1 = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project", "tool", "tool_version",
                 "counts", "constraints"],
    "properties": {
        "schema_version": {"const": "1.1"},
        "project": _ID_FIELD,
        "tool": {"const": "pcbflow"},
        "tool_version": _ID_FIELD,
        "counts": {"type": "object", "additionalProperties": False,
                   "required": ["total", "by_type", "by_domain",
                                "by_authority"],
                   "properties": {
                       "total": {"type": "integer", "minimum": 0},
                       "by_type": _STR_INT_MAP,
                       "by_domain": _STR_INT_MAP,
                       "by_authority": _STR_INT_MAP}},
        "constraints": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "type", "domain", "statement", "checker",
                         "implementation", "implementation_status",
                         "implementation_version", "authority",
                         "enforcement_mode", "waivable", "earliest_stage",
                         "final_stage", "params", "scope", "source_anchor",
                         "source_revision", "source_uri"],
            "properties": {
                "id": _ID_FIELD,
                "type": {"enum": ["hard", "soft", "diagnostic"]},
                "domain": _ID_FIELD,
                "statement": {"type": "string", "minLength": 1,
                              "maxLength": 2048},
                "checker": _ID_FIELD,
                "implementation": _ID_FIELD,
                "implementation_status": _ID_FIELD,
                "implementation_version": _ID_FIELD,
                "authority": _ID_FIELD,
                "enforcement_mode": {"enum": ["hard", "soft",
                                              "diagnostic"]},
                "waivable": {"type": "boolean"},
                "earliest_stage": {"type": "integer", "minimum": 1,
                                   "maximum": 7},
                "final_stage": {"type": "integer", "minimum": 1,
                                "maximum": 7},
                "params": {"type": "object"},
                "scope": {"type": "object"},
                "source_anchor": {"type": "object"},
                "source_revision": _ID_FIELD,
                "source_uri": {"type": "string", "minLength": 1,
                               "maxLength": 512}}}}},
}

_COVERAGE_V1 = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project", "missing_sources",
                 "unmapped_nets", "catch_all_only_nets",
                 "unconnected_pad_nets", "uncovered_groups",
                 "uncovered_pins", "critical_pins_basis", "uncovered_layers",
                 "layer_binding", "ambiguous_selectors",
                 "unimplemented_checkers", "nine_group_comparison",
                 "tolerance_mismatches", "net_class_binding", "source_notes",
                 "pending_decisions", "fallback", "totals"],
    "properties": {
        "schema_version": {"const": "1.1"},
        "project": _ID_FIELD,
        "missing_sources": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["source", "desc", "impact", "blocks"],
            "properties": {k: {"type": "string", "minLength": 1,
                               "maxLength": 512}
                           for k in ("source", "desc", "impact", "blocks")}}},
        "unmapped_nets": {"type": "array",
                          "items": {"type": "string", "minLength": 1}},
        "catch_all_only_nets": {"type": "array",
                                "items": {"type": "string",
                                          "minLength": 1}},
        "unconnected_pad_nets": {"type": "object", "additionalProperties":
                                     False,
                                 "required": ["count", "note", "members"],
                                 "properties": {
                                     "count": {"type": "integer",
                                               "minimum": 0},
                                     "note": {"type": "string",
                                              "maxLength": 1024},
                                     "members": {"type": "array",
                                                 "items": {"type": "string",
                                                           "minLength": 1}}}},
        "uncovered_groups": {"type": "array",
                             "items": {"type": "string", "minLength": 1}},
        "uncovered_pins": {"type": "array",
                           "items": {"type": "string", "minLength": 1}},
        "critical_pins_basis": {"type": "string", "minLength": 1,
                                "maxLength": 2048},
        "uncovered_layers": {"type": "array",
                             "items": {"type": "string", "minLength": 1}},
        "layer_binding": {"type": "object",
                          "additionalProperties": {"type": "array",
                                                   "items": {"type": "string",
                                                             "minLength": 1}}},
        "ambiguous_selectors": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "kind", "title", "status"],
            "properties": {
                "id": {"type": "string", "minLength": 1,
                       "maxLength": 2048},
                "kind": {"type": "string", "minLength": 1,
                         "maxLength": 2048},
                "title": {"type": "string", "minLength": 1,
                          "maxLength": 2048},
                "status": {"type": "string", "minLength": 1,
                           "maxLength": 2048},
                "applied_to": {"type": "array",
                               "items": {"type": "string", "minLength": 1}},
                "constraint_refs": {"type": "array",
                                    "items": {"type": "string",
                                              "minLength": 1}},
                "approver": {"type": "string", "minLength": 1,
                             "maxLength": 2048},
                "decided_on": {"type": "string", "minLength": 1,
                               "maxLength": 2048},
                "decision": {"type": "string", "minLength": 1,
                             "maxLength": 2048},
                "proposal": {"type": "string", "minLength": 1,
                             "maxLength": 2048},
                "review": {"type": "string", "minLength": 1,
                           "maxLength": 2048},
                "script_side": {"type": "string", "minLength": 1,
                                "maxLength": 2048},
                "spec_side": {"type": "string", "minLength": 1,
                              "maxLength": 2048}}}},
        "unimplemented_checkers": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["checker", "implementation_status"],
            "properties": {
                "checker": _ID_FIELD,
                "implementation_status": _ID_FIELD}}},
        "nine_group_comparison": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["group", "status", "constraint_id"],
            "properties": {
                "group": _ID_FIELD,
                "status": {"type": "string", "minLength": 1},
                "constraint_id": _ID_FIELD,
                "ambiguity": {"type": ["string", "null"]},
                "canonical_basis": {"type": ["string", "null"]},
                "canonical_members": {"type": ["array", "null"],
                                      "items": {"type": "string"}},
                "board_actual_members": {"type": ["array", "null"],
                                         "items": {"type": "string"}},
                "script_members": {"type": ["array", "null"],
                                   "items": {"type": "string"}},
                "script_nets_missing_on_board": {"type": ["array", "null"],
                                                 "items": {"type": "string"}},
                "script_ref": {"type": ["string", "null"]},
                "spec_members_basis": {"type": ["string", "null"]},
                "spec_script_match": {"type": ["boolean", "null"]},
                "diff": {"type": ["object", "null"]},
                "tolerance": {"type": ["object", "null"]}}}},
        "tolerance_mismatches": {"type": "array",
                                 "items": {"type": "object"}},
        "net_class_binding": {"type": "object",
                              "additionalProperties": {
                                  "type": "object",
                                  "additionalProperties": False,
                                  "required": ["count", "members"],
                                  "properties": {
                                      "count": {"type": "integer",
                                                "minimum": 0},
                                      "members": {"type": "array",
                                                  "items": {"type": "string",
                                                            "minLength":
                                                                1}}}}},
        "source_notes": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "note"],
            "properties": {
                "id": _ID_FIELD,
                "note": {"type": "string", "minLength": 1,
                         "maxLength": 2048}}}},
        "pending_decisions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "item", "source"],
            "properties": {
                "id": _ID_FIELD,
                "item": {"type": "string", "minLength": 1},
                "source": {"type": "string", "minLength": 1},
                "impact": {"type": "array",
                           "items": {"type": "string", "minLength": 1}},
                "line": {"type": ["integer", "string"]}}}},
        "fallback": {"type": "object", "additionalProperties": False,
                     "required": ["backend", "capabilities",
                                  "fallback_reason", "fidelity"],
                     "properties": {
                         "backend": _ID_FIELD,
                         "capabilities": {"type": "array",
                                          "items": {"type": "string",
                                                    "minLength": 1}},
                         "fallback_reason": {"type": "string",
                                             "minLength": 1},
                         "fidelity": {"type": "string", "minLength": 1}}},
        "totals": _STR_INT_MAP,
    },
}

_IMPEDANCE_TARGETS_V1 = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project", "basis", "stackup",
                 "targets"],
    "properties": {
        "schema_version": {"const": "1.1"},
        "project": _ID_FIELD,
        "basis": {"type": "string", "minLength": 1, "maxLength": 2048},
        "stackup": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["layer", "role"],
            "properties": {"layer": _ID_FIELD, "role": _ID_FIELD}}},
        # 两形态 targets（compile_cmd._impedance_targets 实产）：
        # 预估差分对（几何双键 geom_*）与单端降权行（est_* 区间串+adopted）
        "targets": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "anyOf": [
                {"required": ["net_class", "impedance_ohm", "tolerance_pct",
                              "geom_width_mm", "geom_spacing_mm", "layer",
                              "status", "note"]},
                {"required": ["net_class", "impedance_ohm", "tolerance_pct",
                              "est_width_mm", "adopted_width_mm", "status",
                              "note"]},
            ],
            "properties": {
                "net_class": _ID_FIELD,
                "impedance_ohm": {"type": "number", "minimum": 0},
                "tolerance_pct": {"type": "number", "minimum": 0},
                "geom_width_mm": {"type": "number", "minimum": 0},
                "geom_spacing_mm": {"type": "number",
                                    "minimum": 0},
                "layer": _ID_FIELD,
                "est_width_mm": {"type": "string", "minLength": 1},
                "adopted_width_mm": {"type": "number",
                                     "minimum": 0},
                "status": _ID_FIELD,
                "note": {"type": "string", "minLength": 1,
                         "maxLength": 2048}}}},
    },
}

# envelope：SPEC §2.1 统一输出信封。schema_version 收主版本 pattern
# （历史实例 1.0/1.1/1.3 并存）；command_kind=v1.3 增量键，历史值域含
# fc2_two_targets（超 build_envelope 断言集 {core,advisory}），故只收类型
# 不收 enum；inputs 三键恒在、artifacts.sha256 可缺席（84/136 在场）。
_ENVELOPE_V1 = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "tool", "tool_version", "command",
                 "status", "verdict", "deterministic", "determinism_claim",
                 "inputs", "config_sha256", "spec_refs", "artifacts",
                 "metrics", "diagnostics", "waivers", "solver",
                 "run_metadata", "data"],
    "properties": {
        "schema_version": {"type": "string",
                           "pattern": "^1\\.[0-9]+$"},
        "tool": {"const": "pcbflow"},
        "tool_version": _ID_FIELD,
        "command": _ID_FIELD,
        "command_kind": {"type": "string", "minLength": 1, "maxLength": 64},
        "status": {"enum": ["ok", "failed", "blocked", "unknown"]},
        "verdict": {"enum": ["pass", "fail", "waived", "yellow", "red"]},
        "deterministic": {"type": "boolean"},
        "determinism_claim": {"enum": ["byte_exact", "semantic",
                                       "not_claimed"]},
        "inputs": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["path", "role", "sha256"],
            "properties": {
                "path": {"type": "string", "minLength": 1, "maxLength": 512},
                "role": {"type": "string", "minLength": 1, "maxLength": 128},
                "sha256": _SHA256_FIELD}}},
        "config_sha256": _NULLABLE_SHA,
        "spec_refs": {"type": "array",
                      "items": {"type": "string", "minLength": 1,
                                "maxLength": 512}},
        "artifacts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["path", "role"],
            "properties": {
                "path": {"type": "string", "minLength": 1, "maxLength": 512},
                "role": {"type": "string", "minLength": 1, "maxLength": 128},
                "sha256": _SHA256_FIELD}}},
        "metrics": {"type": "object"},
        "diagnostics": {"type": "array"},
        "waivers": {"type": "array"},
        "solver": {"type": "object"},
        "run_metadata": {"type": "object"},
        "data": {"type": "object"},
    },
}


# ---------------------------------------------------------------------------
# 注册表（名称 → schema；新增 schema 必须同步测试快照）
# ---------------------------------------------------------------------------

SCHEMAS = {
    "gate_record": _GATE_RECORD,
    "disposition_record": _DISPOSITION,
    "judge_pre_record": _JUDGE_PRE,
    "judge_post_record": _JUDGE_POST,
    "decision_ledger_entry": _LEDGER_ENTRY,
    "critic_run_record": _CRITIC_RUN,
    "queue_event": _QUEUE_EVENT,
    "physics_report": _PHYSICS_REPORT,
    "physics_coverage": _PHYSICS_COVERAGE,
    "bring_up_report": _BRING_UP_REPORT,
    "external_execution_record": _EXTERNAL_EXECUTION,
    "proposal_patch": _PROPOSAL_PATCH,
    "search_space": _SEARCH_SPACE,
    "project_manifest": _PROJECT_MANIFEST,
    "profile": _PROFILE,
    # P2 采纳追加（APR-0012 @2026-09-06；追加式，既有条目零改动）
    "artifact-role-declaration-v1": _ARTIFACT_ROLE_DECLARATION,
    # P2-7 采纳追加（@2026-09-10；追加式，既有条目零改动）
    "critic-flag-verdict-v1": _CRITIC_FLAG_VERDICT_V1,
    # observation 线采纳追加（@2026-09-12；追加式，既有条目零改动）
    "observation-row-v1": _OBSERVATION_ROW_V1,
    # REPAIR-P3 W-5 采纳追加（@2026-09-22；追加式，既有条目零改动）——
    # toolchain_lock.schema_versions 四孤儿名入册（命名语法=<名称>-v<N>，
    # DOC-NAMING §12 r8；映射 constraints→constraints-v1、coverage→coverage-v1、
    # envelope→envelope-v1、impedance_targets→impedance_targets-v1，
    # 条目内 const/pattern 钉 "1.1" 产物格式轴）
    "constraints-v1": _CONSTRAINTS_V1,
    "coverage-v1": _COVERAGE_V1,
    "envelope-v1": _ENVELOPE_V1,
    "impedance_targets-v1": _IMPEDANCE_TARGETS_V1,
}

# judge_fact 观察键禁区（§1.3：fact 不得含处置语义）
FACT_FORBIDDEN_KEYS = frozenset(_FACT_FORBIDDEN)
