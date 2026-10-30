"""Proposer patch 治理与 autotuning 搜索空间/adoption 门（SPEC-v3.0 TD11/TD3/TD2）。

生成器模式（零子进程/零写盘）、纯函数、无 wall-clock、仅标准库。

TD11 红线（本模块机器侧落地）：
- Proposer 只能提交 proposal_patch.json；execution_allowed 恒 false
  （schema const 强制 + 语义层友好重复断言）；
- operation_kind 白名单五类（候选类）；六类高危操作显式禁止——语义层在
  schema enum 之前先宽松检查原始字段值，补一条明确禁类提示；
- changes[].path 必须落在调用方给定的 target_path_allowlist 内；
- 涉敏 scope（constraints/structures/registry_identity/toolchain/
  external_requirement/production_policy/board_write，target_scope 命中或
  changes[].path 首段前缀命中）只能成为 human_review_candidate，不能自动
  apply——本模块任何返回值都不存在 auto_apply 字段。

TD3/TD2 红线：
- 搜索空间必须显式声明固定真实执行比例 explore_real_execution_ratio ∈ (0,1]
  （缺省即 fail-closed 报错：代理模型只能预筛，探索候选必须真实执行）；
- adoption 机器门：白名单指标零恶化（容差 0）+ required 指标不回退 +
  holdout 逐板不回退（L5 跨板）；holdout 缺失/板数不足 → blocked；
  机器门通过（adopt_candidate）仍需 Human disposition——
  human_adoption_required 恒 True，机器门不是 adoption authority；
- 目标为分层质量向量（objective_vector/compare_objectives）：字典序逐层
  比较，低层劣化不可被高层补偿，None 视为最劣，禁止标量和。

P1-A（真实采纳路径机器门）：真实采纳资格只能由 adoption_gate_paired
判定（逐板同板配对 baseline/challenger 证据，结构上不存在全局 baseline
静默回退路径，两个分母防重复板伪装多样本）；adoption_gate 是显式的
global_baseline_legacy 模式（合成/历史比较），其结果不得作为真实采纳
资格。
"""

from __future__ import annotations

import re

from . import schemas

# ---------------------------------------------------------------------------
# TD11 常量：操作白名单（五类）/ 禁类（六类）/ 敏感 scope
# ---------------------------------------------------------------------------

ALLOWED_OPERATION_KINDS = (
    "policy_parameter_candidate",
    "route_order_candidate",
    "threshold_candidate",
    "advisory_checker_candidate",
    "profile_text_candidate",
)

FORBIDDEN_OPERATION_KINDS = (
    "board_write",
    "direct_constraint_mutation",
    "direct_gate_mutation",
    "waiver_creation",
    "identity_reallocation",
    "runtime_self_update",
)

SENSITIVE_SCOPES = (
    "constraints",
    "structures",
    "registry_identity",
    "toolchain",
    "external_requirement",
    "production_policy",
    "board_write",
)

# evaluate_patch 状态（TD11：涉敏 → 人工审查；非法 → blocked；否则入 adoption 流程）
PATCH_STATUS_ELIGIBLE = "eligible_for_adoption_flow"
PATCH_STATUS_HUMAN_REVIEW = "human_review_candidate"
PATCH_STATUS_BLOCKED = "blocked"

# adoption_gate 决策（TD2/TD3/L4/L5：机器门通过 ≠ adoption）
DECISION_REJECT = "reject"
DECISION_BLOCKED = "blocked"
DECISION_ADOPT_CANDIDATE = "adopt_candidate"

# 指标方向约定：未显式声明方向的指标一律按 lower_is_better 保守处理
DIRECTION_LOWER_IS_BETTER = "lower_is_better"
DIRECTION_HIGHER_IS_BETTER = "higher_is_better"

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_num(x) -> bool:
    """数值判定（bool 不算数值——fail-closed，布尔当缺失处理）。"""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ---------------------------------------------------------------------------
# TD11 patch 验证与分级
# ---------------------------------------------------------------------------

def validate_patch(patch, target_path_allowlist) -> list:
    """验证 proposal patch：schema 严格验证 + TD11 语义检查。

    检查顺序（禁类提示必须在 schema enum 报错之外单独给出）：
      1. operation_kind 原始值 ∈ FORBIDDEN_OPERATION_KINDS → 明确禁类错误；
      2. execution_allowed 必须恒 False（schema const 已强制，此处友好重复断言）；
      3. schemas.validate("proposal_patch", ...) 严格验证；
      4. changes[].path ∈ target_path_allowlist（None/空白名单 → 全部拒绝）；
      5. base_artifact_hash 必须为 64 位小写十六进制。

    返回错误列表（[] = 合法）；纯函数，无 IO。
    """
    errors: list = []

    # 1) 宽松预检：禁类 operation_kind（schema enum 会另报一条；这里补明确提示）
    if isinstance(patch, dict):
        kind = patch.get("operation_kind")
        if kind in FORBIDDEN_OPERATION_KINDS:
            errors.append(
                f"operation_kind {kind!r} 属于 TD11 禁止操作类"
                f"（{list(FORBIDDEN_OPERATION_KINDS)}）；Proposer 不得写板、"
                f"直改约束/门/身份、创建 waiver 或自我更新 runtime")

    # 2) execution_allowed 恒 false（语义层友好重复断言）
    if isinstance(patch, dict) and patch.get("execution_allowed") is not False:
        errors.append(
            "execution_allowed 必须恒为 false（TD11：proposal patch 无执行权限，"
            "执行只能由 judge/execution 链在人类 disposition 之后发起）")

    # 3) schema 严格验证（enum/const/required/additionalProperties fail-closed）
    errors.extend(schemas.validate("proposal_patch", patch))

    # 4) target path allowlist（语义层；schema 不知道项目级 allowlist）
    allowlist = set(target_path_allowlist or ())
    if isinstance(patch, dict) and isinstance(patch.get("changes"), list):
        for i, change in enumerate(patch["changes"]):
            if not isinstance(change, dict) or "path" not in change:
                continue  # 结构问题由 schema 报告
            path = change["path"]
            if isinstance(path, str) and path not in allowlist:
                errors.append(
                    f"changes[{i}].path {path!r} 不在 target_path_allowlist"
                    f"（TD11：应用前必须通过 target path/field allowlist）")

    # 5) base_artifact_hash 64 位小写十六进制（语义层友好重复断言）
    if isinstance(patch, dict) and "base_artifact_hash" in patch:
        base_hash = patch["base_artifact_hash"]
        if not isinstance(base_hash, str) or not _HEX64_RE.match(base_hash):
            errors.append(
                "base_artifact_hash 必须是 64 位小写十六进制 sha256"
                f"（得到 {base_hash!r}；TD11：base hash 是应用前置门）")

    return errors


def evaluate_patch(patch, base_artifact_sha256, target_path_allowlist) -> dict:
    """对 patch 分级：blocked / human_review_candidate / eligible_for_adoption_flow。

    - validate_patch 报错 → blocked（reasons=错误列表）；
    - patch.base_artifact_hash ≠ 当前 base_artifact_sha256 → blocked
      （stale patch，TD11 base hash 门）；
    - target_scope ∈ SENSITIVE_SCOPES 或 changes[].path 首段命中敏感 scope
      → human_review_candidate（reasons 前缀 sensitive_scope:）；
    - 其余 → eligible_for_adoption_flow（仅表示可进入 adoption 流程，
      不表示任何执行或采纳决定）。

    返回值恒为 {status, reasons}，不存在 auto_apply 字段——本模块不授予
    自动执行/自动采纳权。
    """
    errors = validate_patch(patch, target_path_allowlist)
    if errors:
        return {"status": PATCH_STATUS_BLOCKED, "reasons": errors}

    base_hash = patch.get("base_artifact_hash")
    if base_hash != base_artifact_sha256:
        return {"status": PATCH_STATUS_BLOCKED, "reasons": [
            f"base_artifact_hash_mismatch: patch 锚定 {base_hash!r}，"
            f"当前 base_artifact_sha256={base_artifact_sha256!r}"
            f"（TD11：base hash 不匹配的 stale patch 不得进入后续门）"]}

    reasons: list = []
    if patch.get("target_scope") in SENSITIVE_SCOPES:
        reasons.append(f"sensitive_scope:target_scope={patch['target_scope']!r}")
    for i, change in enumerate(patch.get("changes") or []):
        path = change.get("path") if isinstance(change, dict) else None
        first_segment = path.split("/", 1)[0] if isinstance(path, str) else ""
        if first_segment in SENSITIVE_SCOPES:
            reasons.append(
                f"sensitive_scope:path_prefix={first_segment!r}"
                f"（changes[{i}].path={path!r}）")
    if reasons:
        return {"status": PATCH_STATUS_HUMAN_REVIEW, "reasons": reasons}
    return {"status": PATCH_STATUS_ELIGIBLE, "reasons": []}


# ---------------------------------------------------------------------------
# TD3 搜索空间声明验证
# ---------------------------------------------------------------------------

def validate_search_space(space) -> list:
    """验证 autotuning 搜索空间声明：schema + 低自由度语义合同。

    语义检查（schema 之外的 fail-closed 落地）：
    - enum 参数 domain.values 非空；
    - integer/float 参数必须同时声明 domain.min/max 且 min < max（缺一即错）；
    - domain.step 若存在必须严格 > 0（validator 子集不实现 exclusiveMinimum，
      语义层必须兜底）；
    - max_parameter_count ≥ len(parameters)（TD2 低自由度：参数数不得超声明）；
    - explore_real_execution_ratio 必须显式声明且 ∈ (0,1]（缺省即报错：
      TD3 固定比例探索候选必须真实执行，比例不得为 0 或未声明）。

    返回错误列表（[] = 合法）；纯函数。
    """
    errors = list(schemas.validate("search_space", space))
    if not isinstance(space, dict):
        return errors  # 结构错误已由 schema 报告；语义层无从继续

    params = space.get("parameters")
    param_list = params if isinstance(params, list) else []
    for i, param in enumerate(param_list):
        if not isinstance(param, dict) or not isinstance(param.get("domain"), dict):
            continue  # 结构错误由 schema 报告
        kind = param.get("kind")
        name = param.get("name") if isinstance(param.get("name"), str) else f"[{i}]"
        domain = param["domain"]

        if kind == "enum":
            values = domain.get("values")
            if not isinstance(values, list) or len(values) == 0:
                errors.append(
                    f"parameters[{i}]({name}): enum 参数 domain.values 必须非空")

        if kind in ("integer", "float"):
            lo, hi = domain.get("min"), domain.get("max")
            if not _is_num(lo) or not _is_num(hi):
                errors.append(
                    f"parameters[{i}]({name}): {kind} 参数必须同时声明"
                    f"数值 domain.min 与 domain.max（缺一即 fail-closed）")
            elif not lo < hi:
                errors.append(
                    f"parameters[{i}]({name}): domain.min={lo!r} 必须严格小于"
                    f" domain.max={hi!r}")

        step = domain.get("step")
        if step is not None and (not _is_num(step) or step <= 0):
            errors.append(
                f"parameters[{i}]({name}): domain.step={step!r} 必须严格 > 0")

    max_count = space.get("max_parameter_count")
    if max_count is not None and len(param_list) > max_count:
        errors.append(
            f"max_parameter_count={max_count!r} 小于实际参数个数 "
            f"{len(param_list)}（TD2 低自由度合同：声明的最大参数数不得被超出）")

    ratio = space.get("explore_real_execution_ratio")
    if ratio is None:
        errors.append(
            "缺 explore_real_execution_ratio（TD3：固定比例探索候选必须真实"
            "执行；搜索空间必须显式声明该比例，不得省略）")
    elif not _is_num(ratio) or not 0 < ratio <= 1:
        errors.append(
            f"explore_real_execution_ratio={ratio!r} 必须在 (0,1] 内"
            f"（TD3：真实执行比例不得为 0、不得 >1）")

    return errors


# ---------------------------------------------------------------------------
# TD2/TD3/L4/L5 adoption 机器门
# ---------------------------------------------------------------------------

def _compare_metric(baseline_metrics, challenger_metrics, name, directions) -> dict:
    """单指标不回退比较：容差 0，任一侧缺失/非数值 → fail-closed 判回退。"""
    direction = directions.get(name, DIRECTION_LOWER_IS_BETTER)
    raw_b = baseline_metrics.get(name) if isinstance(baseline_metrics, dict) else None
    raw_c = (challenger_metrics.get(name)
             if isinstance(challenger_metrics, dict) else None)
    detail = {"metric": name, "baseline": raw_b, "challenger": raw_c,
              "direction": direction}
    if not _is_num(raw_b) or not _is_num(raw_c):
        detail["regressed"] = True
        detail["reason"] = ("missing_or_non_numeric_baseline"
                            if not _is_num(raw_b)
                            else "missing_or_non_numeric_challenger")
        return detail
    if direction == DIRECTION_HIGHER_IS_BETTER:
        detail["regressed"] = raw_c < raw_b
    else:
        detail["regressed"] = raw_c > raw_b
    detail["delta"] = raw_c - raw_b
    return detail


def adoption_gate(
    baseline_metrics: dict,
    challenger_metrics: dict,
    *,
    whitelist_metrics: tuple,
    required_metrics: tuple,
    holdout_results: list,
    min_holdout_boards: int = 1,
    metric_directions: dict | None = None,
) -> dict:
    """challenger config 的 adoption 机器门（逐指标、逐板、白名单零恶化）。

    metrics 为 {name: number}；holdout_results 每项 {board_id, metrics:{...}}。
    指标方向：默认 lower_is_better；可用 metric_directions={name: 方向} 显式
    声明 higher_is_better（未知方向值 → ValueError，程序员错误）。

    规则（决策优先级与合同一致：reject > blocked(缺证据) > adopt_candidate）：
    - whitelist 任一指标恶化（challenger 严格劣于 baseline，容差 0）→ reject；
    - required_metrics 任一回退 → reject（per_metric 逐项给出方向与回退标记；
      任一侧缺失/非数值按回退处理，fail-closed）；
    - holdout_results 为空 → blocked（holdout_missing）；
    - holdout 板数 < min_holdout_boards → blocked（holdout_insufficient）；
    - holdout 任一板任一 required/白名单指标相对 baseline 回退 → reject
      （L5 跨板不回退；板内指标缺失同样按回退处理）；
    - 全过 → adopt_candidate：仅机器门通过，仍需 Human disposition。

    P1-A 模式标记（只加键，不改变行为）：返回值含
    gate_mode="global_baseline_legacy"——本函数是全局 baseline 的合成/
    历史比较模式（holdout_results 每项仅 {board_id, metrics}，逐板比较
    全部锚定同一全局 baseline），不得用于真实采纳资格；真实采纳路径
    必须用 adoption_gate_paired（逐板同板配对，杜绝跨板回退被全局基线
    掩盖）。

    返回 {decision, reasons, whitelist_violations, per_metric,
    holdout:{denominator, non_regressed_boards, non_regression_rate,
    regressed_boards, violations}, human_adoption_required, gate_mode}；
    human_adoption_required 恒 True——机器门不是 adoption authority。
    """
    if (not isinstance(min_holdout_boards, int)
            or isinstance(min_holdout_boards, bool) or min_holdout_boards < 1):
        raise ValueError("min_holdout_boards 必须为 ≥1 的整数")

    directions = dict(metric_directions) if metric_directions else {}
    for metric, direction in directions.items():
        if direction not in (DIRECTION_LOWER_IS_BETTER,
                             DIRECTION_HIGHER_IS_BETTER):
            raise ValueError(
                f"指标 {metric!r} 的方向声明 {direction!r} 非法"
                f"（{DIRECTION_LOWER_IS_BETTER}|{DIRECTION_HIGHER_IS_BETTER}）")

    whitelist_metrics = tuple(whitelist_metrics)
    required_metrics = tuple(required_metrics)

    # L4：白名单零恶化（一票否决）+ required 不回退
    whitelist_violations = []
    for metric in whitelist_metrics:
        detail = _compare_metric(baseline_metrics, challenger_metrics,
                                 metric, directions)
        if detail["regressed"]:
            whitelist_violations.append(detail)
    per_metric = {
        metric: _compare_metric(baseline_metrics, challenger_metrics,
                                metric, directions)
        for metric in required_metrics
    }
    required_regressed = [m for m, d in per_metric.items() if d["regressed"]]

    # L5：holdout 逐板不回退（与门指标 = 白名单 ∪ required，保序去重）
    holdout_metrics = whitelist_metrics + tuple(
        m for m in required_metrics if m not in whitelist_metrics)
    boards = list(holdout_results or [])
    holdout_violations = []
    regressed_boards = []
    for board in boards:
        board_id = board.get("board_id") if isinstance(board, dict) else None
        board_metrics = (board.get("metrics", {})
                         if isinstance(board, dict) else {})
        board_detail = [
            _compare_metric(baseline_metrics, board_metrics, metric, directions)
            for metric in holdout_metrics]
        if any(d["regressed"] for d in board_detail):
            regressed_boards.append(board_id)
            for d in board_detail:
                if d["regressed"]:
                    holdout_violations.append({"board_id": board_id, **d})
    denominator = len(boards)
    non_regressed = denominator - len(regressed_boards)
    rate = (non_regressed / denominator) if denominator else 0.0
    holdout_summary = {
        "denominator": denominator,
        "non_regressed_boards": non_regressed,
        "non_regression_rate": rate,
        "regressed_boards": regressed_boards,
        "violations": holdout_violations,
    }

    # 决策（优先级：reject > blocked > adopt_candidate）
    reasons: list = []
    if whitelist_violations:
        decision = DECISION_REJECT
        reasons.append("whitelist_regression: 白名单指标零恶化被违反（一票否决）")
    elif required_regressed:
        decision = DECISION_REJECT
        reasons.append(
            f"required_metric_regression: required 指标回退 {required_regressed}")
    elif denominator == 0:
        decision = DECISION_BLOCKED
        reasons.append("holdout_missing: 缺独立 holdout 证据（fail-closed）")
    elif denominator < min_holdout_boards:
        decision = DECISION_BLOCKED
        reasons.append(
            f"holdout_insufficient: holdout 板数 {denominator} < "
            f"min_holdout_boards={min_holdout_boards}")
    elif holdout_violations:
        decision = DECISION_REJECT
        reasons.append(
            "holdout_board_regression: L5 跨板不回退被违反"
            f"（回退板 {regressed_boards}）")
    else:
        decision = DECISION_ADOPT_CANDIDATE

    return {
        "decision": decision,
        "reasons": reasons,
        "whitelist_violations": whitelist_violations,
        "per_metric": per_metric,
        "holdout": holdout_summary,
        # 机器门通过也只产生 candidate：adoption 必须经 Human disposition
        "human_adoption_required": True,
        # P1-A：显式标记=全局 baseline 合成/历史比较模式，不得用于真实采纳资格
        "gate_mode": "global_baseline_legacy",
    }


# ---------------------------------------------------------------------------
# P1-A：逐板配对 adoption 机器门（真实采纳路径；L5 逐板不回退的严格落地）
# ---------------------------------------------------------------------------

def _hex64(value) -> bool:
    """64 位小写十六进制 sha256 判定。"""
    return isinstance(value, str) and bool(_HEX64_RE.match(value))


def _nonempty_str(value) -> bool:
    """非空字符串判定（空白串也视为空——fail-closed）。"""
    return isinstance(value, str) and value.strip() != ""


def _validate_pair_side(side, side_name, gate_metrics, pair_board_id,
                        pair_profile_id, reasons) -> None:
    """配对单侧证据验证（fail-closed）：非法项追加机器可读原因。

    检查项：config_id/execution_id 非空字符串；output_sha256 为 64hex；
    metrics 为 dict、每个值均为数值（bool 不算数值）且门指标一个不缺；
    可选回显 board_id/profile_id 必须与对级一致（错板/错 profile 防护）；
    可选 check_refs 必须为 {name: 64hex}。
    注意：baseline.config_id 与 challenger.config_id 不要求相等（候选
    config 本就可以不同）——不存在把候选整体 hash 相等当作有效性条件的
    检查。
    """
    if not isinstance(side, dict):
        reasons.append(f"{side_name}_invalid: 侧记录不是 dict")
        return
    for key in ("config_id", "execution_id"):
        if not _nonempty_str(side.get(key)):
            reasons.append(f"{side_name}.{key}_invalid: 必须为非空字符串")
    if not _hex64(side.get("output_sha256")):
        reasons.append(f"{side_name}.output_sha256_invalid: "
                       "必须是 64 位小写十六进制 sha256")
    metrics = side.get("metrics")
    if not isinstance(metrics, dict):
        reasons.append(
            f"{side_name}.metrics_invalid: 必须为 {{name: number}} dict")
    else:
        for metric in gate_metrics:
            if metric not in metrics:
                reasons.append(f"{side_name}.metric_missing:{metric}")
        for name, value in metrics.items():
            if not _is_num(value):
                reasons.append(f"{side_name}.metric_non_numeric:{name}")
    echo_board = side.get("board_id")
    if echo_board is not None and echo_board != pair_board_id:
        reasons.append(f"{side_name}.board_id_echo_mismatch: 侧回显 "
                       f"{echo_board!r} ≠ 对级 {pair_board_id!r}（错板防护）")
    echo_profile = side.get("profile_id")
    if echo_profile is not None and echo_profile != pair_profile_id:
        reasons.append(f"{side_name}.profile_id_echo_mismatch: 侧回显 "
                       f"{echo_profile!r} ≠ 对级 {pair_profile_id!r}"
                       "（错 profile 防护）")
    check_refs = side.get("check_refs")
    if check_refs is not None and (
            not isinstance(check_refs, dict)
            or not all(_hex64(v) for v in check_refs.values())):
        reasons.append(f"{side_name}.check_refs_invalid: "
                       "必须为 {name: 64hex} dict")


def adoption_gate_paired(*, whitelist_metrics, required_metrics,
                         holdout_pairs, min_holdout_boards: int = 1,
                         metric_directions: dict | None = None) -> dict:
    """逐板配对 adoption 机器门（P1-A：真实采纳路径专用）。

    与 legacy adoption_gate（gate_mode=global_baseline_legacy）的本质
    区别：本函数不接收任何全局 baseline 参数——每条配对记录自带同一
    (board_id, profile_id, design_inputs_sha256, toolchain_lock_sha256)
    下的 baseline/challenger 两侧执行证据，逐指标比较逐对锚定各自的
    baseline，结构上杜绝"跨板回退被全局基线掩盖"的静默回退路径；
    legacy 全局/合成比较模式不得用于真实采纳资格。

    holdout_pairs 每项形状：
      {board_id, profile_id, design_inputs_sha256(64hex),
       toolchain_lock_sha256(64hex),
       baseline:   {config_id, execution_id, output_sha256(64hex),
                    metrics:{name: number}, board_id?, profile_id?,
                    check_refs?:{name: 64hex}},
       challenger: {同形状}}

    配对有效性（任一不满足 → 该对排除出两个分母、进 excluded_pairs 附
    原因，fail-closed）：结构/类型/64hex 格式非法；任一侧缺任一门指标
    （门指标=whitelist∪required，保序去重）或 metrics 含非数值（bool
    不算数值）；任一侧回显 board_id/profile_id 与对级不一致（错板/错
    profile 防护）。

    两个分母（缺一不可，防重复板伪装多样本）：
    - board_denominator=有效配对中唯一 (profile_id, board_id,
      design_inputs_sha256, toolchain_lock_sha256) 组数；
    - execution_denominator=有效配对条数。

    决策梯（与既有合同优先级一致：reject > blocked > adopt_candidate）：
    - 任一有效配对白名单指标恶化 → reject（一票否决）；
    - 任一有效配对 required 指标回退 → reject；
    - 有效板数 == 0 → blocked（holdout_pairs 为空=holdout_pairs_missing；
      有输入但全部无效=no_valid_pairs）；
    - 有效板数 < min_holdout_boards → blocked（holdout_pairs_insufficient）；
    - 任一有效板任一门指标逐对回退 → reject（L5 逐板不回退）；
    - 其余 → adopt_candidate：仅机器门候选，仍需 Human disposition。

    指标方向与容差同 legacy：默认 lower_is_better，metric_directions 可
    显式声明 higher_is_better（未知方向值 → ValueError）；容差 0，缺失/
    非数值 fail-closed 判回退（有效配对内不会出现：已在有效性阶段排除）。
    min_holdout_boards 非 ≥1 整数、holdout_pairs 非 list/tuple/None →
    ValueError（程序员错误，fail-closed）。

    返回 {decision, reasons, whitelist_violations, per_metric（按配对
    聚合明细，每项含 pair_index/board_id/profile_id）, holdout:{
    board_denominator, execution_denominator, non_regressed_boards,
    non_regression_rate, regressed_boards, violations, excluded_pairs},
    human_adoption_required, gate_mode:"paired_v1"}；
    human_adoption_required 恒 True——机器门不是 adoption authority。
    纯函数，无 IO，无 wall-clock。
    """
    if (not isinstance(min_holdout_boards, int)
            or isinstance(min_holdout_boards, bool) or min_holdout_boards < 1):
        raise ValueError("min_holdout_boards 必须为 ≥1 的整数")

    directions = dict(metric_directions) if metric_directions else {}
    for metric, direction in directions.items():
        if direction not in (DIRECTION_LOWER_IS_BETTER,
                             DIRECTION_HIGHER_IS_BETTER):
            raise ValueError(
                f"指标 {metric!r} 的方向声明 {direction!r} 非法"
                f"（{DIRECTION_LOWER_IS_BETTER}|{DIRECTION_HIGHER_IS_BETTER}）")

    whitelist_metrics = tuple(whitelist_metrics)
    required_metrics = tuple(required_metrics)
    # 门指标 = 白名单 ∪ required（保序去重，与 legacy L5 逻辑一致）
    gate_metrics = whitelist_metrics + tuple(
        m for m in required_metrics if m not in whitelist_metrics)

    if holdout_pairs is None:
        pairs_input: list = []
    elif isinstance(holdout_pairs, (list, tuple)):
        pairs_input = list(holdout_pairs)
    else:
        raise ValueError("holdout_pairs 必须为 list/tuple（None 视为空）")

    # 1) 配对有效性（fail-closed）：任一非法 → 排除出两个分母并附原因
    valid: list = []                 # (pair_index, pair, group_key)
    excluded_pairs: list = []
    for index, pair in enumerate(pairs_input):
        pair_reasons: list = []
        board_id = profile_id = None
        if not isinstance(pair, dict):
            pair_reasons.append("pair_not_dict: 配对记录不是 dict")
        else:
            board_id = pair.get("board_id")
            profile_id = pair.get("profile_id")
            if not _nonempty_str(board_id):
                pair_reasons.append("board_id_invalid: 必须为非空字符串")
            if not _nonempty_str(profile_id):
                pair_reasons.append("profile_id_invalid: 必须为非空字符串")
            if not _hex64(pair.get("design_inputs_sha256")):
                pair_reasons.append("design_inputs_sha256_invalid: "
                                    "必须是 64 位小写十六进制 sha256")
            if not _hex64(pair.get("toolchain_lock_sha256")):
                pair_reasons.append("toolchain_lock_sha256_invalid: "
                                    "必须是 64 位小写十六进制 sha256")
            for side_name in ("baseline", "challenger"):
                _validate_pair_side(pair.get(side_name), side_name,
                                    gate_metrics, board_id, profile_id,
                                    pair_reasons)
        if pair_reasons:
            excluded_pairs.append({"pair_index": index,
                                   "board_id": board_id,
                                   "profile_id": profile_id,
                                   "reasons": pair_reasons})
            continue
        valid.append((index, pair, (profile_id, board_id,
                                    pair["design_inputs_sha256"],
                                    pair["toolchain_lock_sha256"])))

    # 2) 逐对逐指标比较（每对锚定各自的 baseline——不存在全局锚点）
    whitelist_violations: list = []
    per_metric = {metric: [] for metric in required_metrics}
    violations: list = []
    board_groups: list = []          # 唯一组键，first-seen 序（确定性）
    regressed_boards: list = []
    seen_regressed: set = set()
    for index, pair, group_key in valid:
        context = {"pair_index": index,
                   "board_id": pair["board_id"],
                   "profile_id": pair["profile_id"]}
        pair_regressed = False
        for metric in gate_metrics:
            detail = _compare_metric(pair["baseline"]["metrics"],
                                     pair["challenger"]["metrics"],
                                     metric, directions)
            detail = {**context, **detail}
            if not detail["regressed"]:
                continue
            pair_regressed = True
            violations.append(detail)
            if metric in whitelist_metrics:
                whitelist_violations.append(detail)
            if metric in required_metrics:
                per_metric[metric].append(detail)
        if group_key not in board_groups:
            board_groups.append(group_key)
        if pair_regressed and group_key not in seen_regressed:
            seen_regressed.add(group_key)
            regressed_boards.append({
                "profile_id": group_key[0], "board_id": group_key[1],
                "design_inputs_sha256": group_key[2],
                "toolchain_lock_sha256": group_key[3]})

    board_denominator = len(board_groups)
    execution_denominator = len(valid)
    non_regressed = board_denominator - len(regressed_boards)
    rate = (non_regressed / board_denominator) if board_denominator else 0.0
    holdout_summary = {
        "board_denominator": board_denominator,
        "execution_denominator": execution_denominator,
        "non_regressed_boards": non_regressed,
        "non_regression_rate": rate,
        "regressed_boards": regressed_boards,
        "violations": violations,
        "excluded_pairs": excluded_pairs,
    }

    # 3) 决策梯（与既有合同优先级一致：reject > blocked > adopt_candidate）
    required_regressed = [m for m, d in per_metric.items() if d]
    reasons: list = []
    if whitelist_violations:
        decision = DECISION_REJECT
        reasons.append("whitelist_regression: 白名单指标零恶化被违反（一票否决）")
    elif required_regressed:
        decision = DECISION_REJECT
        reasons.append(
            f"required_metric_regression: required 指标回退 {required_regressed}")
    elif board_denominator == 0:
        decision = DECISION_BLOCKED
        if not pairs_input:
            reasons.append("holdout_pairs_missing: 缺逐板配对 holdout 证据"
                           "（fail-closed）")
        else:
            reasons.append(
                f"no_valid_pairs: 配对输入 {len(pairs_input)} 条全部无效"
                "（excluded_pairs 附原因；fail-closed）")
    elif board_denominator < min_holdout_boards:
        decision = DECISION_BLOCKED
        reasons.append(
            f"holdout_pairs_insufficient: 有效 holdout 板数 "
            f"{board_denominator} < min_holdout_boards="
            f"{min_holdout_boards}")
    elif violations:
        decision = DECISION_REJECT
        reasons.append(
            "holdout_board_regression: L5 逐板不回退被违反"
            f"（回退板 {regressed_boards}）")
    else:
        decision = DECISION_ADOPT_CANDIDATE

    return {
        "decision": decision,
        "reasons": reasons,
        "whitelist_violations": whitelist_violations,
        "per_metric": per_metric,
        "holdout": holdout_summary,
        # 机器门通过也只产生 candidate：adoption 必须经 Human disposition
        "human_adoption_required": True,
        "gate_mode": "paired_v1",
    }


# ---------------------------------------------------------------------------
# TD3 分层质量向量（字典序比较，禁止标量和）
# ---------------------------------------------------------------------------

# 布局：(tier 键, metrics 中的约定键名, tier 内子键(None=标量层), 高者优先?)
_OBJECTIVE_LAYOUT = (
    ("tier1_hard_constraints", "hard_constraint_violations", None, False),
    ("tier2_whitelist_guard", "whitelist_guard_violations", None, False),
    ("tier3_drc", "drc_batch_severity_error", "batch_severity_error", False),
    ("tier3_drc", "drc_final_severity_all", "final_severity_all", False),
    ("tier4_route_success", "route_success_rate", None, True),
    ("tier5_resource_margin", "resource_margin", None, True),
    ("tier6_ordinary", "via_count", "via_count", False),
    ("tier6_ordinary", "layer_changes", "layer_changes", False),
    ("tier6_ordinary", "length_deviation", "length_dev", False),
)

OBJECTIVE_METRIC_KEYS = tuple(item[1] for item in _OBJECTIVE_LAYOUT)


def objective_vector(metrics: dict) -> dict:
    """从 metrics 按约定键名提取分层质量向量（TD3：不用未定义总和）。

    返回 {tier1_hard_constraints, tier2_whitelist_guard,
    tier3_drc:{batch_severity_error, final_severity_all},
    tier4_route_success, tier5_resource_margin,
    tier6_ordinary:{via_count, layer_changes, length_dev}, missing}。
    缺失或非数值的叶 → None（比较时视为最劣），并把其约定键名记入 missing。
    """
    source = metrics if isinstance(metrics, dict) else {}
    vector: dict = {}
    missing: list = []
    for tier, metric_key, sub_key, _higher in _OBJECTIVE_LAYOUT:
        raw = source.get(metric_key)
        value = raw if _is_num(raw) else None
        if value is None:
            missing.append(metric_key)
        if sub_key is None:
            vector[tier] = value
        else:
            vector.setdefault(tier, {})[sub_key] = value
    vector["missing"] = missing
    return vector


def _as_vector(obj) -> dict:
    """compare_objectives 入参归一化：已是向量则原样，否则按 metrics 提取。"""
    if isinstance(obj, dict) and "tier1_hard_constraints" in obj:
        return obj
    return objective_vector(obj)


def _leaf(vector, tier, sub_key):
    if sub_key is None:
        return vector.get(tier)
    nested = vector.get(tier)
    return nested.get(sub_key) if isinstance(nested, dict) else None


def _tolerance_for(tolerances, tier, metric_key, sub_key) -> float:
    """容差查找：约定键名 / 子键 / "tier.子键" 三种写法皆可；非法值按 0。"""
    for key in (metric_key, sub_key, f"{tier}.{sub_key or metric_key}"):
        if key in tolerances:
            tol = tolerances[key]
            if _is_num(tol) and tol >= 0:
                return tol
            return 0.0
    return 0.0


def _cmp_leaf(value_a, value_b, higher_is_better, tol) -> int:
    """单叶比较：None 最劣；|a-b| ≤ tol 视为相等；返回 -1/0/1（a 视角）。"""
    a_ok, b_ok = _is_num(value_a), _is_num(value_b)
    if not a_ok and not b_ok:
        return 0
    if not a_ok:
        return -1
    if not b_ok:
        return 1
    if abs(value_a - value_b) <= tol:
        return 0
    a_better = value_a > value_b if higher_is_better else value_a < value_b
    return 1 if a_better else -1


def compare_objectives(a, b, tolerances: dict | None = None) -> int:
    """分层质量向量字典序比较：返回 -1（a 劣）/ 0（相等）/ 1（a 优）。

    - a/b 可为 objective_vector 产物或原始 metrics dict（自动归一化）；
    - 逐层逐叶按 _OBJECTIVE_LAYOUT 顺序比较，首个分出胜负的叶决定结果：
      低层（tier1 硬约束）劣化不可被高层（tier6 普通目标）改善补偿；
    - tier1/2/3/6 低者优先；tier4 走线成功率、tier5 资源余量高者优先；
    - None 视为最劣（比任何数值都差，两个 None 相等）；
    - tolerances={约定键名: 容差}（也接受子键或 "tier.子键" 写法）：
      |a-b| ≤ 容差视为相等；默认全零容差。
    - 禁止标量和：本函数不存在任何加权求和路径。
    """
    vector_a, vector_b = _as_vector(a), _as_vector(b)
    tolerances = tolerances or {}
    for tier, metric_key, sub_key, higher in _OBJECTIVE_LAYOUT:
        tol = _tolerance_for(tolerances, tier, metric_key, sub_key)
        cmp_result = _cmp_leaf(
            _leaf(vector_a, tier, sub_key),
            _leaf(vector_b, tier, sub_key),
            higher, tol)
        if cmp_result:
            return cmp_result
    return 0
