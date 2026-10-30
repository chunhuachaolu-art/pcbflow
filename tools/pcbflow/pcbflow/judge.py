"""§1.3 双阶段 Judge（judge_pre → Executor → judge_post；TD1/TL-1）。

红线（本模块机器侧落地）：
- pre fail-closed：toolchain_lock_sha256 必须 64hex、两侧（记录与
  context_inputs）在场且一致、
  记录内声明的全部上游 required hash 必须在 context_inputs 中在场且一致、
  write_scope 只允许 staging_only/none、allowlist 为空且 required_checks
  非空、patch precondition 未满足——任一命中 pre_ok=False，Executor 不得启动；
- post fail-closed：output_hash 缺失、l1_legal/layer_pure 非 True、批/终检
  DRC ref 缺失、external/physics/bring_up 非 pass 且非 not_required、
  rollback_status=failed 均 fail；solver 无 proof 只能 UNKNOWN（v1.3 继承
  不变式），SAT/UNSAT 无 proof_ref 视为凭空断言 fail；UNKNOWN 三态如实
  记 unknown_solver=True 而不伪装成 fail；
- 缺 pre 的 post 不可采纳：adoption_check 强制 post.pre_record_ref
  落在 pre 记录 canonical hash 集内；
- judge_fact 不可变且不得含 accept/reject/waive 语义：build_facts 对
  schemas.FACT_FORBIDDEN_KEYS 违例抛 ValueError，每条 immutable=True。

P1-B 修正声明（版本化：修正以加严方式落地，v1 保留可解释）：
- evaluate_pre：toolchain_lock_sha256 两侧必须在场且匹配——context_inputs
  缺该键（None/缺失）一律 fail，不再静默跳过比对；
- build_post：提供的 execution_id 必须与 pre_record["execution_id"] 一致，
  不一致 ValueError（post 只能绑定同一次执行）；
- adoption_check_v2：绑定级采纳检查（pre_record_ref 命中 canonical hash +
  execution_id 一致 + 拷贝上下文字段逐一相等 + 提供实测 context_inputs 时
  复跑 pre 门）；v1 adoption_check 原样保留，用于解释历史冻结记录。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
"""

from __future__ import annotations

import copy
import re

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

#: pre 允许的写域（live board 恒零写；TD7 默认 staging-only）
WRITE_SCOPES = ("staging_only", "none")

#: 上游 hash 字段（evaluate_pre 逐一与 context_inputs 对账；声明即 required）
UPSTREAM_HASH_FIELDS = (
    "source_snapshot_sha256",      # schema 必填，恒 required
    "staging_snapshot_sha256",
    "constraints_sha256",
    "structures_sha256",
    "registry_sha256",
    "ff_plan_sha256",
    "policy_sha256",
    "request_or_argv_hash",
)

#: executor 块键（version 可空，其余必填）
_EXECUTOR_KEYS = ("backend", "protocol", "version", "capability")

#: post 从 pre 继承的执行上下文字段（同一 execution_id 上下文不得漂移）
_COPY_FROM_PRE = (
    "project_id", "profile_id", "candidate_id",
    "source_snapshot_sha256", "staging_snapshot_sha256",
    "constraints_sha256", "structures_sha256", "registry_sha256",
    "ff_plan_sha256", "policy_sha256", "toolchain_lock_sha256",
    "request_or_argv_hash",
)

#: post 侧外部/物理/bring-up 状态的免检值（其余一律 fail）
_POST_OK_EXTERNAL = ("pass", "not_required")

#: judge_fact item schema（judge_post_record.properties.facts.items；
#: 注册表内嵌形状，不修改 schemas.py）
_FACT_ITEM_SPEC = schemas.SCHEMAS["judge_post_record"]["properties"]["facts"]["items"]

#: build_facts 顶层允许键（多余键 fail-closed 拒绝，防夹带）
_FACT_INPUT_KEYS = frozenset({"fact_id", "observer", "observation"})


def _norm_executor(executor) -> dict:
    """executor 块归一化：只保留四个 schema 键；backend/protocol/capability 必填。"""
    if not isinstance(executor, dict):
        raise ValueError("executor 必须为 dict（backend/protocol/version/capability）")
    norm: dict = {}
    for key in _EXECUTOR_KEYS:
        value = executor.get(key)
        if key != "version" and value is None:
            raise ValueError(f"executor 缺必填键 {key!r}")
        norm[key] = value
    return norm


# ---------------------------------------------------------------------------
# judge_pre
# ---------------------------------------------------------------------------

def build_pre(*, execution_id, project_id, profile_id, candidate_id,
              source_snapshot_sha256, toolchain_lock_sha256, executor,
              write_scope="staging_only", allowlist=(), required_checks=(),
              upstream_hashes=None, patch_preconditions=()) -> dict:
    """按 judge_pre_record schema 构造 pre 记录（违例即 ValueError）。

    upstream_hashes 只接受 UPSTREAM_HASH_FIELDS 内的键（声明即 required，
    evaluate_pre 时与 context 逐一对账）。
    """
    record = {
        "schema_version": SCHEMA_VERSION,
        "judge_kind": "judge_pre",
        "execution_id": execution_id,
        "project_id": project_id,
        "profile_id": profile_id,
        "candidate_id": candidate_id,
        "source_snapshot_sha256": source_snapshot_sha256,
        "staging_snapshot_sha256": None,
        "constraints_sha256": None,
        "structures_sha256": None,
        "registry_sha256": None,
        "ff_plan_sha256": None,
        "policy_sha256": None,
        "toolchain_lock_sha256": toolchain_lock_sha256,
        "executor": _norm_executor(executor),
        "request_or_argv_hash": None,
        "write_scope": write_scope,
        "allowlist": list(allowlist),
        "required_checks": list(required_checks),
        "patch_preconditions": [dict(p) for p in patch_preconditions],
    }
    for key, value in (upstream_hashes or {}).items():
        if key not in UPSTREAM_HASH_FIELDS:
            raise ValueError(f"upstream_hashes 未知上游字段 {key!r}"
                             f"（合法集 {UPSTREAM_HASH_FIELDS}）")
        record[key] = value
    errs = schemas.validate("judge_pre_record", record)
    if errs:
        raise ValueError(f"judge_pre 记录非法（fail-closed）: {errs}")
    return record


def evaluate_pre(record: dict, context_inputs: dict) -> dict:
    """pre 门评估：返回 {pre_ok: bool, failed: [str]}（fail-closed）。

    任一命中即 pre_ok=False（Executor 不得启动）：
    toolchain_lock_sha256 非 64hex、context_inputs 缺该键或与 context 不
    一致（P1-B：两侧必须在场且匹配，缺侧不再静默放行）；记录声明的任一
    上游 required hash 在 context_inputs 缺失/不一致；write_scope 非
    staging_only/none；allowlist 为空且 required_checks 非空；任一 patch
    precondition value 非 True。
    """
    failed: list = []
    ctx = context_inputs or {}
    tcl = record.get("toolchain_lock_sha256") if isinstance(record, dict) else None
    if not isinstance(tcl, str) or not _HEX64_RE.search(tcl):
        failed.append("toolchain_lock_sha256 缺失或非 64 位小写十六进制")
    else:
        ctx_tcl = ctx.get("toolchain_lock_sha256")
        if ctx_tcl is None:
            failed.append("context_inputs 缺 toolchain_lock_sha256"
                          "（两侧必须在场且匹配）")
        elif ctx_tcl != tcl:
            failed.append("toolchain_lock_sha256 与 context 不一致（环境漂移）")
    for field in UPSTREAM_HASH_FIELDS:
        declared = record.get(field)
        if declared is None:
            continue  # 未声明者不强制（声明即 required）
        actual = ctx.get(field)
        if actual is None:
            failed.append(f"上游 required hash 缺失：{field} 声明 "
                          f"{declared[:12]}…，context_inputs 未提供")
        elif actual != declared:
            failed.append(f"上游 hash 不一致：{field} 声明 "
                          f"{declared[:12]}…，context 实测 {actual[:12]}…")
    if record.get("write_scope") not in WRITE_SCOPES:
        failed.append(f"write_scope={record.get('write_scope')!r} 非 "
                      f"{WRITE_SCOPES}（Executor 不得启动）")
    if not record.get("allowlist") and record.get("required_checks"):
        failed.append("allowlist 为空且 required_checks 非空"
                      "（必需检查无白名单落点，禁止裸跑）")
    for precond in record.get("patch_preconditions") or []:
        if precond.get("value") is not True:
            failed.append(f"patch precondition 未满足: {precond.get('id')!r}")
    return {"pre_ok": not failed, "failed": failed}


# ---------------------------------------------------------------------------
# judge_post
# ---------------------------------------------------------------------------

def pre_record_sha256(pre_record: dict) -> str:
    """pre 记录 canonical hash（entry_body 式：整记录 canonical_json_bytes）。"""
    return hashing.sha256_bytes(hashing.canonical_json_bytes(pre_record))


def build_post(*, execution_id, pre_record, output_hash=None, l1_legal=False,
               layer_pure=False, drc_batch_ref=None, drc_final_ref=None,
               erc_ref=None, test_manifest_hash=None, replay_ref=None,
               solver=None, external_status="not_required",
               physics_status="not_required", bring_up_status="not_required",
               rollback_status="not_needed", facts=()) -> dict:
    """按 judge_post_record schema 构造 post 记录（违例即 ValueError）。

    pre_record_ref = pre 记录 canonical hash；execution_id 必须与
    pre_record["execution_id"] 一致（P1-B 执行 ID 绑定，post 只能绑定
    同一次执行）；执行上下文字段从 pre 记录复制（同一 execution_id 不得
    漂移）；solver 缺省 UNKNOWN/无 proof（无 proof 只能 UNKNOWN）；缺省
    输出证据一律 None/False（fail-closed，由 evaluate_post 判 fail）。
    """
    if not isinstance(pre_record, dict):
        raise ValueError("pre_record 必须为 judge_pre 记录 dict")
    if pre_record.get("judge_kind") != "judge_pre":
        raise ValueError("pre_record.judge_kind 必须为 'judge_pre'"
                         "（post 只能绑定 pre，缺 pre 的 post 不可采纳）")
    pre_exec = pre_record.get("execution_id")
    if execution_id != pre_exec:
        raise ValueError(
            f"post.execution_id {str(execution_id)[:12]}… 与 "
            f"pre_record.execution_id {str(pre_exec)[:12]}… 不一致"
            "（P1-B 执行 ID 绑定：post 只能绑定同一次执行）")
    solv = ({"status": "UNKNOWN", "proof_ref": None} if solver is None else
            {"status": solver.get("status", "UNKNOWN"),
             "proof_ref": solver.get("proof_ref")})
    record = {
        "schema_version": SCHEMA_VERSION,
        "judge_kind": "judge_post",
        "execution_id": execution_id,
        "pre_record_ref": pre_record_sha256(pre_record),
        "executor": _norm_executor(pre_record.get("executor") or {}),
    }
    for key in _COPY_FROM_PRE:
        record[key] = pre_record.get(key)
    record.update({
        "output_hash": output_hash,
        "l1_legal": l1_legal,
        "layer_pure": layer_pure,
        "drc_batch_ref": drc_batch_ref,
        "drc_final_ref": drc_final_ref,
        "erc_ref": erc_ref,
        "test_manifest_hash": test_manifest_hash,
        "replay_ref": replay_ref,
        "solver": solv,
        "external_status": external_status,
        "physics_status": physics_status,
        "bring_up_status": bring_up_status,
        "rollback_status": rollback_status,
        "facts": [copy.deepcopy(f) for f in facts],
    })
    for fact in record["facts"]:
        errs = schemas.validate_spec(_FACT_ITEM_SPEC, fact)
        if errs:
            raise ValueError(f"fact 非法: {errs}")
    errs = schemas.validate("judge_post_record", record)
    if errs:
        raise ValueError(f"judge_post 记录非法（fail-closed）: {errs}")
    return record


def evaluate_post(record: dict) -> dict:
    """post 门评估：返回 {post_ok, failed, unknown_solver}（三态如实）。

    fail 项：output_hash 缺失；l1_legal/layer_pure 非 True；drc_batch_ref
    （severity-error 批检）或 drc_final_ref（severity-all 终检）缺失；
    solver 声称 SAT/UNSAT 但无 proof_ref（无 proof 只能 UNKNOWN）；
    external/physics/bring_up 非 pass 且非 not_required；
    rollback_status=failed。solver UNKNOWN 不 fail，如实记
    unknown_solver=True（三态：SAT|UNSAT|UNKNOWN）。
    """
    failed: list = []
    unknown_solver = False
    if record.get("output_hash") is None:
        failed.append("output_hash 缺失（无输出哈希不可采信）")
    if record.get("l1_legal") is not True:
        failed.append("l1_legal 非 True")
    if record.get("layer_pure") is not True:
        failed.append("layer_pure 非 True")
    if record.get("drc_batch_ref") is None:
        failed.append("drc_batch_ref 缺失（severity-error 批检产物）")
    if record.get("drc_final_ref") is None:
        failed.append("drc_final_ref 缺失（severity-all 终检产物）")
    solver = record.get("solver") or {}
    status = solver.get("status")
    if status == "UNKNOWN":
        unknown_solver = True  # 三态如实：UNKNOWN 不是 fail，也不冒充证明
    elif status in ("SAT", "UNSAT"):
        if solver.get("proof_ref") is None:
            failed.append(f"solver 声称 {status} 但无 proof_ref"
                          f"（无 proof 只能 UNKNOWN）")
    else:
        failed.append(f"solver.status 非法取值 {status!r}"
                      f"（SAT|UNSAT|UNKNOWN）")
    for field in ("external_status", "physics_status", "bring_up_status"):
        value = record.get(field)
        if value not in _POST_OK_EXTERNAL:
            failed.append(f"{field}={value!r} 非 pass 且非 not_required")
    if record.get("rollback_status") == "failed":
        failed.append("rollback_status=failed（回滚失败）")
    return {"post_ok": not failed, "failed": failed,
            "unknown_solver": unknown_solver}


def adoption_check(pre_entries_sha, post_record: dict) -> list:
    """缺 pre 的 post 不可采纳（§1.3）：post.pre_record_ref 必须在 pre 集内。

    pre_entries_sha：已落账 judge_pre 记录 canonical hash 的集合。
    """
    errors: list = []
    ref = (post_record.get("pre_record_ref")
           if isinstance(post_record, dict) else None)
    if not isinstance(ref, str) or not ref:
        return ["post 缺 pre_record_ref（无法证明存在对应 judge_pre）"]
    if ref not in set(pre_entries_sha):
        errors.append(f"缺 pre 的 post 不可采纳：pre_record_ref "
                      f"{ref[:12]}… 不在已落账 pre 引用集内")
    return errors


def adoption_check_v2(pre_records, post_record: dict, *,
                      context_inputs=None) -> list:
    """P1-B 绑定级采纳检查（§1.3）：返回错误列表，空 = 可采纳。

    a) post.pre_record_ref 必须命中 pre_records 中某条记录的 canonical
       hash（pre_record_sha256）；未命中即不可采纳（与 v1 语义对齐）；
    b) 命中的 pre 与 post 的 execution_id 必须一致（执行 ID 绑定）；
    c) post 从 pre 继承的上下文字段（_COPY_FROM_PRE 全集 + executor 块）
       必须与该 pre 逐一相等——防手改 post 的拷贝字段伪造绑定；
    d) context_inputs 提供时：对命中的 pre 复跑 evaluate_pre 并要求
       pre_ok=True（pre 未通过的 post 不可采纳）。

    pre_records：judge_pre 记录 dict 列表（canonical hash 由本函数计算，
    与 v1 的 pre_entries_sha 集合入参不同）。
    context_inputs：受控编排层的实测执行上下文。调用方（受控编排层）
    应当提供；未提供不视为错误，但 d 项不适用、绑定证明力下降。
    """
    errors: list = []
    if not isinstance(post_record, dict):
        return ["post 必须为 judge_post 记录 dict"]
    ref = post_record.get("pre_record_ref")
    if not isinstance(ref, str) or not ref:
        return ["post 缺 pre_record_ref（无法证明存在对应 judge_pre）"]
    matched = [r for r in (pre_records or []) if isinstance(r, dict)
               and pre_record_sha256(r) == ref]
    if not matched:
        return [f"缺 pre 的 post 不可采纳：pre_record_ref "
                f"{ref[:12]}… 不在已落账 pre 引用集内（adoption_check_v2）"]
    pre = matched[0]
    if post_record.get("execution_id") != pre.get("execution_id"):
        errors.append(
            f"执行 ID 绑定断裂：post.execution_id "
            f"{str(post_record.get('execution_id'))[:12]}… 与命中 pre 的 "
            f"execution_id {str(pre.get('execution_id'))[:12]}… 不一致"
            "（不可采纳）")
    for key in _COPY_FROM_PRE:
        if post_record.get(key) != pre.get(key):
            errors.append(f"拷贝上下文字段 {key} 与命中 pre 不一致"
                          "（手改 post 拷贝字段=绑定伪造，不可采纳）")
    if post_record.get("executor") != pre.get("executor"):
        errors.append("executor 块与命中 pre 不一致"
                      "（手改 post 拷贝字段=绑定伪造，不可采纳）")
    if context_inputs is not None:
        verdict = evaluate_pre(pre, context_inputs)
        if not verdict.get("pre_ok"):
            errors.append("pre 未通过 evaluate_pre"
                          "（pre 未通过的 post 不可采纳）: "
                          + "; ".join(verdict.get("failed") or []))
    return errors


# ---------------------------------------------------------------------------
# judge_fact（不可变观察；禁区键强制）
# ---------------------------------------------------------------------------

def build_facts(observation_list) -> list:
    """把观察 dict 列表构造成 fact item（违例抛 ValueError）。

    每个 observation：{fact_id, observer, observation:{kind, value,
    unit?, ref_sha256?}}。顶层与 observation 内的键均不得含
    schemas.FACT_FORBIDDEN_KEYS（accept/reject/waive/approved/waived/
    disposition/gate_pass——事实不得携带处置语义）；多余顶层键拒绝；
    每条 immutable=True（不可变标记由构造方强制写入）。
    """
    facts: list = []
    for obs in observation_list:
        if not isinstance(obs, dict):
            raise ValueError(f"observation 必须为 dict，"
                             f"得到 {type(obs).__name__}")
        forbidden = set(obs) & schemas.FACT_FORBIDDEN_KEYS
        nested = obs.get("observation")
        if isinstance(nested, dict):
            forbidden |= set(nested) & schemas.FACT_FORBIDDEN_KEYS
        if forbidden:
            raise ValueError(
                f"judge_fact 键含处置语义禁区 {sorted(forbidden)}"
                f"（FACT_FORBIDDEN_KEYS；事实不得携带 accept/reject/waive 语义）")
        extra = set(obs) - _FACT_INPUT_KEYS
        if extra:
            raise ValueError(f"observation 多余顶层键 {sorted(extra)}"
                             f"（允许集 {sorted(_FACT_INPUT_KEYS)}）")
        item = {
            "fact_id": obs.get("fact_id"),
            "observer": obs.get("observer"),
            "observation": copy.deepcopy(obs.get("observation")),
            "immutable": True,
        }
        errs = schemas.validate_spec(_FACT_ITEM_SPEC, item)
        if errs:
            raise ValueError(f"fact 非法: {errs}")
        facts.append(item)
    return facts


def facts_bundle_hash(facts) -> str:
    """facts 列表 canonical hash（bundle 绑定用；顺序敏感）。"""
    return hashing.sha256_bytes(hashing.canonical_json_bytes(list(facts)))
