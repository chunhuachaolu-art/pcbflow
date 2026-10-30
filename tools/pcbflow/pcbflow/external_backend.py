"""TD7 外部执行引擎 backend 合同（SPEC-v3.0-PROPOSAL §TD7）。

Freerouting CLI/JAR（历史证据，historical_only）与 freerouting-mcp
（proposal_only/not_implemented）分列；两类外部引擎均视为不受信任子系统：

- 默认 network=deny、write_scope=staging_only、live_board_touched=false；
- 普通 CLI 不得访问网络；MCP 仅允许 Manifest 显式声明的 loopback/Unix
  endpoint、固定 peer identity 和 method allowlist，禁止公网；
- 禁止 shell 字符串拼接、".." 路径遍历、非 allowlist 可执行文件与
  非 allowlist 绝对路径；
- 崩溃/超时/非零退出/输出验证乱序一律 blocked 并隔离 staging；
  引擎自报 score/unrouted 不具 authority。

生成器模式（Mimosa 钩子约束）：零子进程、零写盘、零网络；纯函数、无
wall-clock、标准库 only。本模块只做合同构造与判定，不执行任何外部引擎。

伴生字段约定：不可变 execution record（schema "external_execution_record"）
只存 argv_or_rpc_hash；raw argv（list[str]）与 rpc_method（str）作为瞬态
伴生字段供 validate_policy 检查，不进入 schema 严格 record
（schemas 的 additionalProperties=false 会拒绝多余键）。用法：

    rec = build_execution_record(..., argv_or_rpc=["java", "-jar", ...])
    #   构造时自动 canonical 哈希并剥离 raw argv（record 保持 schema 纯净）
    errs = validate_policy({**rec, "argv_or_rpc": ["java", "-jar", ...]}, decl)
"""

from __future__ import annotations

import re

from . import hashing, schemas

# ---------------------------------------------------------------------------
# 常量（TD7 合同内聚；改动任一值必须同步负向测试）
# ---------------------------------------------------------------------------

RECORD_SCHEMA = "external_execution_record"
SCHEMA_VERSION = schemas.SCHEMA_V3            # "3.0"

# 后端 / 协议分列（CLI 历史证据 vs MCP proposal_only）
CLI_PROTOCOL = "cli-argv"
MCP_PROTOCOL = "mcp-jsonrpc"
CLI_BACKENDS = frozenset({"freerouting-cli-jar", "kicad-cli"})
MCP_BACKENDS = frozenset({"freerouting-mcp"})

# 记录侧默认隔离策略
DEFAULT_NETWORK_POLICY = "deny"
DEFAULT_WRITE_SCOPE = "staging_only"
DEFAULT_LIVE_BOARD_TOUCHED = False
DEFAULT_MAX_THREADS = 1

# 协议绑定的网络策略（cli 恒禁网；mcp 仅 loopback/Unix socket）
NETWORK_POLICY_CLI = "deny"
NETWORK_POLICY_MCP = "loopback_only"

# loopback endpoint 合法前缀；前缀后必须紧跟 authority 结束符（:/?#）或
# 字符串结束——封堵 "http://localhost.evil.com" 这类公网域名前缀绕过
_LOOPBACK_ENDPOINT_PREFIXES = ("http://127.0.0.1", "http://localhost",
                               "unix://")
_ENDPOINT_AUTHORITY_DELIMS = ":/?#"

# 路径安全
_PARENT_SEGMENT = ".."
_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:\\")
_POSIX_ABS_PREFIX = "/"
_PATH_SEGMENT_SPLIT_RE = re.compile(r"[\\/]+")

# 外部输出验证 stage 固定顺序（TD7：乱序/跳级/缺级即违例）
STAGE_ORDER = ("schema_size_validation", "l1_layer_purity",
               "drc_batch_severity_error", "drc_final_severity_all",
               "rollback_ledger_graph")
STAGE_STATUSES = frozenset({"pass", "fail", "not_executed"})
BLOCKING_STAGE_STATUSES = frozenset({"fail", "not_executed"})

# 退出码分类
EXIT_OK = 0

# pipeline 结论
PIPELINE_VERIFIED_CANDIDATE = "verified_candidate"
PIPELINE_BLOCKED = "blocked"

# capability 声称值
CLAIM_HISTORICAL_ONLY = "historical_only"
CLAIM_PROPOSAL_ONLY = "proposal_only"
CLAIM_LOCKED = "locked"
CLAIM_NOT_LOCKED = "not_locked"

# 证据分列政策（常量 False：CLI 与 MCP 证据不得互充）
CROSS_BACKEND_EVIDENCE_TRANSFER = False

# 引擎自报不采信（TD7：自报 score/unrouted 无 authority）
ENGINE_SELF_REPORT_INCLUDED = False
ENGINE_SELF_REPORT_NOTE = (
    "外部引擎自报的 score/unrouted/日志不具 authority；pipeline 结论只由"
    "固定顺序验证 stage 的机器证据决定，不得以 fallback 成功或 GUI 观察替代。")

CLAIMS_NOTE = (
    "freerouting CLI 仅有历史实跑证据（ASM-PHASE-REPORT-8，Freerouting"
    " 2.3.0 JAR/JRE 命令行与 SES 链），不得充当 freerouting-mcp 的"
    " capability；toolchain_lock 的 freerouting.optional=true /"
    " version=null 是事实记录，不得为形成产品能力改写；freerouting/jdk"
    " 仅在实际调用时锁定（locked_when_called）。")

SEPARATION_NOTE = (
    "CLI（历史证据）与 MCP（proposal_only）execution record 分列归档；"
    "任一侧证据不得转移到另一侧充当 capability 或验证结论。")

QUARANTINE_NOTE = (
    "blocked 时 staging 目录隔离：崩溃、超时、非零退出、验证乱序/失败"
    "的输出不得进入 live board 或后续流水线。")


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _canonical_hash(obj) -> str:
    """canonical JSON 哈希（复用 hashing 的确定性序列化；纯函数）。"""
    return hashing.sha256_text(hashing.json_dumps(obj))


def _has_parent_segment(element: str) -> bool:
    """元素按 / 与 \\ 切分后是否含 ".." 路径段（遍历禁令）。"""
    return _PARENT_SEGMENT in _PATH_SEGMENT_SPLIT_RE.split(element)


def _is_absolute_path(element: str) -> bool:
    """Windows 盘符绝对路径（^[A-Za-z]:\\）或 POSIX 绝对路径（^/）。"""
    return bool(_WINDOWS_ABS_RE.match(element)) or \
        element.startswith(_POSIX_ABS_PREFIX)


def _is_loopback_endpoint(endpoint) -> bool:
    """endpoint 是否为合同允许的 loopback/Unix 形态（fail-closed）。"""
    if not isinstance(endpoint, str) or not endpoint:
        return False
    for prefix in _LOOPBACK_ENDPOINT_PREFIXES:
        if endpoint.startswith(prefix):
            rest = endpoint[len(prefix):]
            return (not rest) or rest[0] in _ENDPOINT_AUTHORITY_DELIMS
    return False


# ---------------------------------------------------------------------------
# 1) execution record 构造
# ---------------------------------------------------------------------------

def build_execution_record(
    *,
    execution_id: str,
    project_id: str,
    profile_id: str,
    source_snapshot_sha256: str,
    staging_path_sha256: str,
    backend: str,
    protocol: str,
    tool_version: str | None,
    toolchain_lock_sha256: str,
    request_sha256: str | None = None,
    response_sha256: str | None = None,
    argv_or_rpc_hash: str | None = None,
    started_by: str,
    timeout_s: int,
    **overrides,
) -> dict:
    """按 schema "external_execution_record" 构造不可变执行记录。

    - 默认 network_policy="deny"、write_scope="staging_only"、
      live_board_touched=False、resource_limits={"max_threads": 1}；
      **overrides 可覆盖任何字段（含默认隔离字段与可选字段
      exit_status/fallback_reason/candidate_id/peer_identity/
      method_allowlist），未知键由 schema additionalProperties=false 拒绝。
    - overrides 可带瞬态伴生字段 argv_or_rpc（list[str]）或 rpc_method
      （str）：构造方只对其做 canonical 哈希（若 argv_or_rpc_hash 未显式
      给出）后剥离，record 保持 schema 纯净；argv_or_rpc 为 str（shell
      字符串拼接）直接 ValueError。
    - 构造后自检 schema：不合法抛 ValueError（错误信息带 JSON path）。
    """
    extra = dict(overrides)
    raw_argv_or_rpc = extra.pop("argv_or_rpc", None)
    rpc_method = extra.pop("rpc_method", None)
    if isinstance(raw_argv_or_rpc, str):
        raise ValueError(
            "argv_or_rpc 禁止 shell 字符串拼接（必须 list[str] 逐参数）")
    if raw_argv_or_rpc is not None and argv_or_rpc_hash is None:
        argv_or_rpc_hash = _canonical_hash(raw_argv_or_rpc)
    if rpc_method is not None and argv_or_rpc_hash is None:
        argv_or_rpc_hash = _canonical_hash({"rpc_method": rpc_method})

    record = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": execution_id,
        "project_id": project_id,
        "profile_id": profile_id,
        "source_snapshot_sha256": source_snapshot_sha256,
        "staging_path_sha256": staging_path_sha256,
        "backend": backend,
        "protocol": protocol,
        "tool_version": tool_version,
        "toolchain_lock_sha256": toolchain_lock_sha256,
        "request_sha256": request_sha256,
        "response_sha256": response_sha256,
        "argv_or_rpc_hash": argv_or_rpc_hash,
        "started_by": started_by,
        "timeout_s": timeout_s,
        "resource_limits": {"max_threads": DEFAULT_MAX_THREADS},
        "network_policy": DEFAULT_NETWORK_POLICY,
        "write_scope": DEFAULT_WRITE_SCOPE,
        "live_board_touched": DEFAULT_LIVE_BOARD_TOUCHED,
    }
    record.update(extra)

    errors = schemas.validate(RECORD_SCHEMA, record)
    if errors:
        raise ValueError(
            f"{RECORD_SCHEMA} 构造违例: " + "; ".join(errors))
    return record


# ---------------------------------------------------------------------------
# 2) manifest 侧声明 vs 记录侧见证的策略校验（fail-closed，返回全部违例）
# ---------------------------------------------------------------------------

def validate_policy(record: dict, declaration: dict) -> list:
    """校验 execution record 是否符合 manifest 侧后端声明。

    declaration 形如：
      {backend, protocol, executable_allowlist: [...],
       method_allowlist: [...], path_allowlist: [...],
       endpoint: str|None, peer_identity: str|None}

    规则（fail-closed；返回所有违例字符串，[] = 通过）：
    - backend/protocol 必须与 declaration 一致；record.protocol 必须是
      cli-argv 或 mcp-jsonrpc（TD7 外部引擎合同覆盖范围）。
    - cli-argv：network_policy 必须 "deny"；argv_or_rpc（list[str] 伴生
      字段，可缺省则跳过对应子检查）首元素必须 ∈ executable_allowlist；
      各元素不得含 ".." 路径段；绝对路径（^[A-Za-z]:\\ 或 ^/）必须是
      path_allowlist 字面量。
    - mcp-jsonrpc：network_policy 必须 "loopback_only"；endpoint 必须
      loopback/Unix（前缀 + authority 结束符）；peer_identity 与
      method_allowlist 非空；record["rpc_method"] 必须 ∈
      method_allowlist（缺省即违例——无法验证 method 权限）。
    - 两协议通用：argv_or_rpc 为 str（shell 拼接）违例；
      live_board_touched=true 违例；write_scope != staging_only 违例。
    """
    errors: list = []

    if not isinstance(declaration, dict):
        return ["declaration 必须为 dict"]
    if not isinstance(record, dict):
        return ["record 必须为 dict"]

    exec_allow = declaration.get("executable_allowlist")
    method_allow = declaration.get("method_allowlist")
    path_allow = declaration.get("path_allowlist")
    for name, val in (("executable_allowlist", exec_allow),
                      ("method_allowlist", method_allow),
                      ("path_allowlist", path_allow)):
        if not isinstance(val, list):
            errors.append(f"declaration.{name} 必须为 list"
                          f"（得到 {type(val).__name__}）")

    rec_backend = record.get("backend")
    dec_backend = declaration.get("backend")
    rec_proto = record.get("protocol")
    dec_proto = declaration.get("protocol")
    if rec_backend != dec_backend:
        errors.append(f"backend 不一致：record={rec_backend!r} vs "
                      f"declaration={dec_backend!r}")
    if rec_proto != dec_proto:
        errors.append(f"protocol 不一致：record={rec_proto!r} vs "
                      f"declaration={dec_proto!r}")

    # 记录侧见证（两种协议通用）
    if record.get("live_board_touched") is True:
        errors.append("live_board_touched=true 违反外部引擎合同"
                      "（live board 零写见证）")
    if record.get("write_scope") != DEFAULT_WRITE_SCOPE:
        errors.append(f"write_scope={record.get('write_scope')!r} 违例"
                      f"（必须 {DEFAULT_WRITE_SCOPE!r}）")

    argv = record.get("argv_or_rpc")
    if isinstance(argv, str):
        errors.append("argv_or_rpc 是 shell 字符串而非 list"
                      "（禁止 shell 拼接）")

    if rec_proto == CLI_PROTOCOL:
        _validate_cli_policy(record, argv, exec_allow, path_allow, errors)
    elif rec_proto == MCP_PROTOCOL:
        _validate_mcp_policy(record, declaration, method_allow, errors)
    else:
        errors.append(f"protocol {rec_proto!r} 不在 TD7 外部引擎合同覆盖"
                      f"范围（{CLI_PROTOCOL}/{MCP_PROTOCOL}）")
    return errors


def _validate_cli_policy(record, argv, exec_allow, path_allow,
                         errors: list) -> None:
    """cli-argv 协议子检查：禁网、可执行 allowlist、路径遍历/绝对路径。"""
    network = record.get("network_policy")
    if network != NETWORK_POLICY_CLI:
        errors.append(f"cli-argv 协议 network_policy 必须 "
                      f"{NETWORK_POLICY_CLI!r}（得到 {network!r}）")
    if argv is None:
        return  # 伴生字段缺省：仅 hash 见证，argv 级子检查跳过
    if not isinstance(argv, list):
        return  # 非 list 非 str：既无法逐参检查也无 shell 特征，交由上层
    if not argv:
        errors.append("argv 为空数组：缺可执行文件首元素")
        return
    head = argv[0]
    if not (isinstance(head, str) and isinstance(exec_allow, list)
            and head in exec_allow):
        errors.append(f"可执行文件首元素 {head!r} 不在 "
                      f"executable_allowlist")
    for i, element in enumerate(argv):
        if not isinstance(element, str):
            errors.append(f"argv[{i}] 非 str"
                          f"（得到 {type(element).__name__}）")
            continue
        if _has_parent_segment(element):
            errors.append(f"argv[{i}] 含 '..' 路径段（路径遍历禁令）："
                          f"{element[:80]!r}")
        if (_is_absolute_path(element)
                and not (isinstance(path_allow, list)
                         and element in path_allow)):
            errors.append(f"argv[{i}] 是非 allowlist 绝对路径（拒绝）："
                          f"{element[:80]!r}")


def _validate_mcp_policy(record, declaration, method_allow,
                         errors: list) -> None:
    """mcp-jsonrpc 协议子检查：loopback、peer、method allowlist。"""
    network = record.get("network_policy")
    if network != NETWORK_POLICY_MCP:
        errors.append(f"mcp-jsonrpc 协议 network_policy 必须 "
                      f"{NETWORK_POLICY_MCP!r}（得到 {network!r}）")

    endpoint = declaration.get("endpoint")
    if not _is_loopback_endpoint(endpoint):
        errors.append(f"endpoint {endpoint!r} 非 loopback/Unix（仅允许 "
                      "http://127.0.0.1、http://localhost、unix:// 前缀；"
                      "禁止公网与任意回调）")

    peer = declaration.get("peer_identity")
    if not (isinstance(peer, str) and peer):
        errors.append("declaration.peer_identity 缺失或为空"
                      "（MCP 必须固定 peer identity）")
    if not (isinstance(method_allow, list) and method_allow):
        errors.append("declaration.method_allowlist 缺失或为空"
                      "（MCP 必须 method allowlist）")

    rpc_method = record.get("rpc_method")
    if rpc_method is None:
        errors.append("record 未携带 rpc_method 伴生字段，"
                      "无法验证 method 权限（fail-closed）")
    elif not (isinstance(method_allow, list)
              and rpc_method in method_allow):
        errors.append(f"rpc method {rpc_method!r} 不在 method_allowlist"
                      "（越权）")

    rec_peer = record.get("peer_identity")
    if rec_peer is not None and rec_peer != peer:
        errors.append(f"record.peer_identity {rec_peer!r} 与 declaration "
                      f"{peer!r} 不一致")


# ---------------------------------------------------------------------------
# 3) capability 声称（lock 状态如实派生；CLI 历史证据不得充当 MCP capability）
# ---------------------------------------------------------------------------

def capability_claims(toolchain_lock: dict) -> dict:
    """从 toolchain lock 派生外部引擎 capability 声称（不改写 lock 状态）。

    - freerouting_cli：version 为 None 且 optional=true → "historical_only"
      （仅 ASM-PHASE-REPORT-8 历史证据）；version 非 None → "locked"；
      version 为 None 且非 optional → "not_locked"。
    - freerouting_mcp：恒 "proposal_only"（proposal/not_implemented，
      与 freerouting.version 无关——MCP 资格须单独 qualification）。
    - kicad_cli：version 非 null → "locked"；否则 "not_locked"。
    - claims_note：CLI 历史证据不得充当 MCP capability；lock 的
      optional/null 状态是事实记录，不得改写。
    """
    lock = toolchain_lock if isinstance(toolchain_lock, dict) else {}
    freerouting = lock.get("freerouting") or {}
    kicad_cli = lock.get("kicad_cli") or {}
    fr_version = freerouting.get("version")
    fr_optional = freerouting.get("optional") is True
    kc_version = kicad_cli.get("version")

    if fr_version is None:
        freerouting_cli = (CLAIM_HISTORICAL_ONLY if fr_optional
                           else CLAIM_NOT_LOCKED)
    else:
        freerouting_cli = CLAIM_LOCKED

    return {
        "freerouting_cli": freerouting_cli,
        "freerouting_mcp": CLAIM_PROPOSAL_ONLY,
        "kicad_cli": (CLAIM_LOCKED if kc_version is not None
                      else CLAIM_NOT_LOCKED),
        "derived_from": {
            "freerouting_optional": freerouting.get("optional"),
            "freerouting_version": fr_version,
            "kicad_cli_version": kc_version,
        },
        "claims_note": CLAIMS_NOTE,
    }


# ---------------------------------------------------------------------------
# 4) 外部输出验证序列评估（乱序/跳级/失败 ⇒ blocked + 隔离 staging）
# ---------------------------------------------------------------------------

def assess_output(record: dict, stages: list) -> dict:
    """按固定顺序评估外部输出的验证 stage 序列，给出 pipeline 结论。

    stages = 按序 [{stage, status, detail?}]；stage ∈ STAGE_ORDER，
    status ∈ {pass, fail, not_executed}。

    - 顺序校验：观察序列必须与 STAGE_ORDER 完全一致（乱序/跳级/缺级/
      重复/未知 stage 均为错误）。
    - 记录侧退出码：record["exit_status"] 缺省（crash_or_unknown）或
      非零（nonzero_exit）均为错误——崩溃、超时、非零退出的输出不得
      进入验证通过态（TD7）。
    - 任一错误或任一 stage fail/not_executed ⇒ pipeline_status="blocked"
      且 quarantine_staging=True；全部 pass 且无错误 ⇒
      "verified_candidate"。
    - engine_self_report_included 恒 False：引擎自报分数不具 authority。
    """
    errors: list = []
    observed: list = []

    stage_entries = stages if isinstance(stages, list) else []
    if not stage_entries:
        errors.append("stages 必须为非空 list")

    for i, entry in enumerate(stage_entries):
        if not isinstance(entry, dict):
            errors.append(f"stages[{i}] 非 dict"
                          f"（得到 {type(entry).__name__}）")
            continue
        stage = entry.get("stage")
        status = entry.get("status")
        if stage not in STAGE_ORDER:
            errors.append(f"stages[{i}].stage {stage!r} 不在固定 stage 集")
            continue
        if status not in STAGE_STATUSES:
            errors.append(f"stages[{i}].status {status!r} 非法"
                          f"（pass|fail|not_executed）")
        observed.append(stage)

    duplicated = sorted({s for s in observed if observed.count(s) > 1})
    if duplicated:
        errors.append(f"stage 重复：{duplicated}")
    order_valid = tuple(observed) == STAGE_ORDER
    if not order_valid:
        errors.append(f"stage 顺序违例（乱序/跳级/缺级）：期望 "
                      f"{list(STAGE_ORDER)}，得到 {observed}")

    exit_cls = classify_exit(
        record.get("exit_status") if isinstance(record, dict) else None)
    if exit_cls["blocked"]:
        errors.append(f"外部引擎退出异常（{exit_cls['kind']}），"
                      "输出不得进入验证通过态")

    failed_stages = [entry.get("stage") for entry in stage_entries
                     if isinstance(entry, dict)
                     and entry.get("status") in BLOCKING_STAGE_STATUSES]
    blocked = bool(errors) or bool(failed_stages)

    return {
        "execution_id": (record.get("execution_id")
                         if isinstance(record, dict) else None),
        "pipeline_status": (PIPELINE_BLOCKED if blocked
                            else PIPELINE_VERIFIED_CANDIDATE),
        "quarantine_staging": blocked,
        "stage_order_valid": order_valid,
        "expected_stage_sequence": list(STAGE_ORDER),
        "observed_stage_sequence": observed,
        "failed_stages": failed_stages,
        "exit_classification": exit_cls,
        "errors": errors,
        "engine_self_report_included": ENGINE_SELF_REPORT_INCLUDED,
        "engine_self_report_note": ENGINE_SELF_REPORT_NOTE,
        "quarantine_note": QUARANTINE_NOTE,
    }


# ---------------------------------------------------------------------------
# 5) 证据分列（CLI 历史证据与 MCP proposal 证据不得互充）
# ---------------------------------------------------------------------------

def separate_evidence(cli_records: list, mcp_records: list) -> dict:
    """分列两 backend 的 execution record canonical hash 列表。

    - 每条 record 做 canonical JSON 哈希后归入对应侧列表；
    - 侧别 backend 一致性与 schema 合法性做 fail-closed 检查（记入
      errors，不中断哈希计算）；
    - 同一 record 同时出现在两侧 ⇒ 错误（cross-backend transfer）；
    - cross_backend_evidence_transfer 恒 False（政策常量：CLI 与 MCP
      证据不得互充 capability 或验证结论）。
    """
    errors: list = []
    cli_hashes: list = []
    mcp_hashes: list = []

    for label, records, allowed, out_hashes in (
            ("cli", cli_records or [], CLI_BACKENDS, cli_hashes),
            ("mcp", mcp_records or [], MCP_BACKENDS, mcp_hashes)):
        for i, rec in enumerate(records):
            if not isinstance(rec, dict):
                errors.append(f"{label}_records[{i}] 非 dict")
                continue
            backend = rec.get("backend")
            if backend not in allowed:
                errors.append(f"{label}_records[{i}] backend {backend!r} "
                              f"不属于 {label} 侧分列集")
            schema_errors = schemas.validate(RECORD_SCHEMA, rec)
            if schema_errors:
                errors.append(f"{label}_records[{i}] schema 违例："
                              + "; ".join(schema_errors[:3]))
            out_hashes.append(_canonical_hash(rec))

    overlap = sorted(set(cli_hashes) & set(mcp_hashes))
    if overlap:
        errors.append("同一 execution record 同时出现在 CLI 与 MCP 分列"
                      f"（cross-backend transfer）：{overlap}")

    return {
        "cli_execution_hashes": cli_hashes,
        "mcp_execution_hashes": mcp_hashes,
        "cli_record_count": len(cli_hashes),
        "mcp_record_count": len(mcp_hashes),
        "cross_backend_evidence_transfer": CROSS_BACKEND_EVIDENCE_TRANSFER,
        "separation_note": SEPARATION_NOTE,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# 6) 崩溃/超时判定助手
# ---------------------------------------------------------------------------

def classify_exit(exit_status) -> dict:
    """退出码分类：None→crash_or_unknown（blocked）；0→ok；
    非零 int→nonzero_exit（blocked）；bool/非 int 见证类型亦按
    crash_or_unknown 处理（fail-closed，bool 是 int 子类需显式排除）。"""
    if exit_status is None:
        return {"kind": "crash_or_unknown", "blocked": True,
                "note": "无退出码见证：按崩溃/超时/未知处理（TD7 blocked）"}
    if isinstance(exit_status, bool) or not isinstance(exit_status, int):
        return {"kind": "crash_or_unknown", "blocked": True,
                "note": f"非法退出码见证类型 "
                        f"{type(exit_status).__name__}（fail-closed）"}
    if exit_status == EXIT_OK:
        return {"kind": "ok", "blocked": False,
                "note": "退出码 0；输出仍须通过全部固定顺序验证 stage"}
    return {"kind": "nonzero_exit", "blocked": True,
            "note": f"非零退出码 {exit_status}（TD7 blocked 并隔离 staging）"}
