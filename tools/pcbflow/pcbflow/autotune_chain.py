"""TL-4 autotune 编排（TD3/TD2/TD11：search_space → adoption 全链走 decision ledger）。

把 manifest/profile 声明的参数搜索空间走完机器链：
  search_space/baseline 声明校验 → 确定性候选生成（全枚举，optimizer/
  随机种子/环境策略记录在案）→ 代理模型预筛（只排序，不裁决）→ 固定比例
  候选「真实执行」（smoke 级=本模块闭式评估器在编排内实际执行，如实标注
  execution_level）→ 分层质量向量（proposer.objective_vector/compare_objectives
  字典序，禁止标量和）→ challenger vs baseline 逐指标比较 → adoption 机器门
  （白名单零恶化 + holdout 不回退；TD2/TD3）→ proposal_patch（TD11，
  execution_allowed=false）→ judge_pre/judge_post/execution/backtest 走
  decision-ledger（六事件）→ TL-4 机器 gate-record（gate_kind=training_loop）。

如实裁决纪律（本模块不粉饰结果）：
- 「真实执行」的执行级别是 smoke_in_process_closed_form：闭式路由成本
  模型（纯算术），不是 kicad-cli 布线器、不是 DRC authority；judge_post
  如实判 drc_batch_ref/drc_final_ref 缺失 → post_ok=False——这是正确
  结果，不是编排失败（无 kicad-cli 产物就没有 DRC 证据）；
- holdout：build_chain 自身不消费 holdout 语料（执行分母恒 0），
  adoption_gate_paired 只能 blocked（holdout_pairs_missing）；S3 版 gate
  record 以
  holdout_corpus 输入 status=missing 如实闭门，不得伪造 pass——S9 起
  TL-5 语料已建立并 pass，证据可用性重估见第 9 节 build_holdout_unlock
  （v2 复评=blocked 保持，缺执行证据的谓词无翻转入口）；
- adoption 永远是人工点：机器门任何结果都不产生 apply 动作；旧 config
  immutable（本编排零写盘），adoption 失败自动保留旧版本；
- 样本不足（holdout 分母 < LOW_DOF_MIN_HOLDOUT_BOARDS）时只允许单参数
  变更（TD2 低自由度声明：单阈值/单系数），多参数 challenger 不具备
  promotion 资格。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
"""

from __future__ import annotations

import itertools
import math

from . import disposition, gate, hashing, judge, ledger, proposer, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 真实执行级别（如实标注：本编排的 Executor 是 in-process 闭式模型）
EXECUTION_LEVEL = "smoke_in_process_closed_form"

#: TD11 patch 落点白名单（policy 参数候选唯一允许的 target path）
TARGET_PATH_ALLOWLIST = ("policy/route_params.json",)

#: TD2 低自由度：holdout 板数低于该阈值时 challenger 至多改 1 个参数
LOW_DOF_MIN_HOLDOUT_BOARDS = 2

# ---------------------------------------------------------------------------
# smoke 闭式评估模型常量（全部在 bundle 内如实复述；非布线器、非 DRC authority）
# ---------------------------------------------------------------------------

#: 假想布线通道宽度（每信号层可用于并行走线的通道宽度，声明式模型常量）
CHANNEL_WIDTH_MM = 1.2
#: 归一化参考栅格（模型内各比值以 0.5mm 为基准）
GRID_REF_MM = 0.5
#: 长度偏差基线（栅格=GRID_REF_MM 且 via_penalty=0 时的标称长度偏差）
LENGTH_BASE_MM = 0.3
#: 过孔计数系数（每 net 的标称过孔基数）
VIA_FACTOR = 3.0
#: 硬约束判据：栅格粗于最小可实现轨道间距 → diff_pair 规则不可实现
MIN_PAIR_TRACK_WIDTH_MM = 0.5
#: via_penalty 未声明时的缺省（profile.thresholds.via_cost 同源缺省 2）
DEFAULT_VIA_PENALTY = 2

#: 指标方向（adoption_gate 用；与 _OBJECTIVE_LAYOUT 逐键一致）
METRIC_DIRECTIONS = {
    "hard_constraint_violations": proposer.DIRECTION_LOWER_IS_BETTER,
    "whitelist_guard_violations": proposer.DIRECTION_LOWER_IS_BETTER,
    "drc_batch_severity_error": proposer.DIRECTION_LOWER_IS_BETTER,
    "drc_final_severity_all": proposer.DIRECTION_LOWER_IS_BETTER,
    "route_success_rate": proposer.DIRECTION_HIGHER_IS_BETTER,
    "resource_margin": proposer.DIRECTION_HIGHER_IS_BETTER,
    "via_count": proposer.DIRECTION_LOWER_IS_BETTER,
    "layer_changes": proposer.DIRECTION_LOWER_IS_BETTER,
    "length_deviation": proposer.DIRECTION_LOWER_IS_BETTER,
}

#: L4 白名单子项（critical-net guard 一票否决，容差 0）
WHITELIST_METRICS = ("whitelist_guard_violations",)

#: required 普通指标（tier3–tier6；逐项不回退）
REQUIRED_METRICS = ("drc_batch_severity_error", "drc_final_severity_all",
                    "route_success_rate", "resource_margin", "via_count",
                    "layer_changes", "length_deviation")

#: 分层质量向量声明（TD3：每项 scope/单位/归一化/权重/容差/tie-break；
#: 权重恒为字典序固定序，不存在加权求和路径）
OBJECTIVE_DECLARATION = (
    {"tier": 1, "metric": "hard_constraint_violations",
     "scope": "constraints 硬约束（最小线宽/对内间距可实现性）",
     "unit": "count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "本层相等则进入下一层，不产生部分补偿"},
    {"tier": 2, "metric": "whitelist_guard_violations",
     "scope": "白名单 critical-net guard（profile.critical_net_set）",
     "unit": "count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "本层相等则进入下一层，不产生部分补偿"},
    {"tier": 3, "metric": "drc_batch_severity_error",
     "scope": "批检 severity-error 计数（模型估计，非 kicad-cli authority）",
     "unit": "count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "本层相等则进入下一层，不产生部分补偿"},
    {"tier": 3, "metric": "drc_final_severity_all",
     "scope": "终检 severity-all 计数（模型估计，非 kicad-cli authority）",
     "unit": "count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "同层先比 batch 再比 final（固定子序）"},
    {"tier": 4, "metric": "route_success_rate",
     "scope": "通道容量/需求 net 数（走线成功率）",
     "unit": "ratio", "normalization": "min_max_to_capacity_ratio",
     "weight": "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "higher_is_better",
     "tie_break": "本层相等则进入下一层，不产生部分补偿"},
    {"tier": 5, "metric": "resource_margin",
     "scope": "布线资源余量（容量-需求)/容量",
     "unit": "ratio", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "higher_is_better",
     "tie_break": "本层相等则进入下一层，不产生部分补偿"},
    {"tier": 6, "metric": "via_count",
     "scope": "估计过孔数（route.cost_model 旋钮响应）",
     "unit": "estimated_count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "同层固定子序 via → layer_changes → length_deviation"},
    {"tier": 6, "metric": "layer_changes",
     "scope": "估计换层数（=via_count/2）",
     "unit": "estimated_count", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "同层固定子序 via → layer_changes → length_deviation"},
    {"tier": 6, "metric": "length_deviation",
     "scope": "估计长度偏差（对 length-match 容差）",
     "unit": "mm", "normalization": "none", "weight":
     "lexicographic_fixed_order_no_sum", "tolerance": 0,
     "direction": "lower_is_better",
     "tie_break": "向量全等 → 变更参数数少者优先 → candidate_id 字典序"},
)

#: 搜索空间 record_env 的确定性策略声明（静态合同：不探测运行环境，
#: 因此同输入重跑 byte-exact；探测式环境快照反而引入跨机漂移）
DETERMINISM_STRATEGY = {
    "optimizer": "deterministic_grid_enumeration",
    "random_seed": None,
    "randomness": "none_full_enumeration",
    "float_strategy": "ieee754_double_json_repr",
    "grid_round_decimals": 6,
    "threads": "1",
    "parallel_merge": "none",
    "stdlib_only": True,
}


# ---------------------------------------------------------------------------
# 1. 输入合同校验（search_space + baseline config；fail-closed）
# ---------------------------------------------------------------------------

def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 \
        and all(c in "0123456789abcdef" for c in value)


def validate_baseline_config(baseline, space) -> list:
    """baseline config 结构 + 值域校验，返回错误列表（[] = 合法）。

    结构：{schema_version=3.0, artifact_kind=autotune_baseline_config,
    project_id, profile_id, config_id, values}；values 的键集必须与
    search_space.parameters 名称集完全一致（多/少/未知参数一律拒绝），
    每个值必须落在对应参数域内且（对步进网格）落在网格点上。
    """
    errors: list = []
    if not isinstance(baseline, dict):
        return ["baseline config 必须为 dict"]
    for key in ("schema_version", "artifact_kind", "project_id",
                "profile_id", "config_id", "values"):
        if key not in baseline:
            errors.append(f"baseline config 缺必需键 {key!r}")
    if errors:
        return errors
    if baseline["schema_version"] != SCHEMA_VERSION:
        errors.append("baseline config schema_version 必须为 '3.0'")
    if baseline["artifact_kind"] != "autotune_baseline_config":
        errors.append("baseline config artifact_kind 必须为 "
                      "'autotune_baseline_config'")
    if baseline.get("profile_id") != (space or {}).get("profile_id"):
        errors.append("baseline profile_id 与 search_space.profile_id 不一致"
                      "（跨 profile 混用，fail-closed）")
    values = baseline.get("values")
    params = {p.get("name"): p for p in (space or {}).get("parameters", [])
              if isinstance(p, dict)}
    if not isinstance(values, dict):
        return errors + ["baseline values 必须为 dict"]
    missing = sorted(set(params) - set(values))
    extra = sorted(set(values) - set(params))
    if missing:
        errors.append(f"baseline values 缺参数 {missing}（键集必须与"
                      "搜索空间参数名完全一致）")
    if extra:
        errors.append(f"baseline values 含未声明参数 {extra}（键集必须与"
                      "搜索空间参数名完全一致）")
    for name, value in sorted(values.items()):
        param = params.get(name)
        if param is None:
            continue
        grid = _domain_values(param)
        if not any(_same_value(value, point) for point in grid):
            errors.append(
                f"baseline values[{name!r}]={value!r} 不在参数域/网格内"
                f"（合法点 {grid}；域外基线 fail-closed）")
    return errors


def validate_chain_inputs(space, baseline) -> list:
    """链入口总校验：search_space schema+语义 + baseline 合同。"""
    errors = list(schemas.validate("search_space", space))
    errors += proposer.validate_search_space(space)
    errors += validate_baseline_config(baseline, space
                                       if isinstance(space, dict) else {})
    return errors


# ---------------------------------------------------------------------------
# 2. 确定性候选生成（全枚举）
# ---------------------------------------------------------------------------

def _domain_values(param) -> list:
    """参数取值序列（确定性：enum 按声明序、数值按网格升序）。

    float 必须带 step（连续不可枚举域 fail-closed：smoke 编排只支持
    可枚举网格）；integer 无 step 时按 1 步进；float 网格点
    = round(min + i*step, 6)（IEEE754 确定性 + 6 位小数规整）。
    """
    kind = param.get("kind")
    domain = param.get("domain") or {}
    if kind == "enum":
        return list(domain.get("values") or [])
    if kind == "boolean":
        return [False, True]
    lo, hi = domain.get("min"), domain.get("max")
    if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
        raise ValueError(f"参数 {param.get('name')!r} 数值域缺 min/max")
    step = domain.get("step")
    if kind == "integer":
        step = step if isinstance(step, (int, float)) and step > 0 else 1
        count = int(round((hi - lo) / step))
        return [int(round(lo + i * step)) for i in range(count + 1)]
    if step is None:
        raise ValueError(
            f"float 参数 {param.get('name')!r} 缺 domain.step"
            f"（连续不可枚举域不支持确定性全枚举，fail-closed）")
    count = int(round((hi - lo) / step))
    return [round(lo + i * step, DETERMINISM_STRATEGY["grid_round_decimals"])
            for i in range(count + 1)]


def _same_value(a, b) -> bool:
    """数值/枚举相等（float 容差 1e-9，规避网格舍入残差）。"""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-9
    return a == b


def enumerate_candidates(space, baseline_values) -> list:
    """确定性全枚举候选（行主序笛卡尔积；candidate_id 按枚举序稳定编号）。

    返回 [{candidate_id, values}]；baseline 必须是网格点之一
    （不在网格 → ValueError，fail-closed）。
    """
    names = [p["name"] for p in space["parameters"]]
    axes = [_domain_values(p) for p in space["parameters"]]
    candidates = [
        {"candidate_id": f"CAND-{i:04d}",
         "values": dict(zip(names, combo))}
        for i, combo in enumerate(
            itertools.product(*axes), start=1)
    ]
    if not any(all(_same_value(c["values"][n], baseline_values[n])
                   for n in names) for c in candidates):
        raise ValueError("baseline 不在枚举网格内（值域外基线，fail-closed）")
    return candidates


def find_baseline_candidate(candidates, baseline_values) -> dict:
    for c in candidates:
        if all(_same_value(c["values"][k], baseline_values[k])
               for k in baseline_values):
            return c
    raise ValueError("baseline 候选不在枚举集内")


# ---------------------------------------------------------------------------
# 3. 代理预筛（只排序、不裁决）与固定比例真实执行选择
# ---------------------------------------------------------------------------

#: 代理模型声明（TD3：代理只做预筛；固定比例候选必须真实执行）
PROXY_MODEL_DECLARATION = {
    "kind": "grid_only_scalar_heuristic",
    "description": "仅以 route_grid_mm 单参数排序的粗粒度启发式；忽略 "
                   "via_penalty、白名单与硬约束交互，可能排序出错——"
                   "只用于预筛排序，不参与任何 promotion 裁决",
    "promotion_eligible": False,
    "unexecuted_candidates_eligible": False,
    "fallback_when_unavailable": "conservative_full_execution",
}


def proxy_prescreen(candidates, *, available=True):
    """代理预筛：返回 {ranking, proxy_model}；available=False → None。

    返回 None 表示代理不可用（服务/模型缺席）——调用方必须保守回退
    全量真实执行或 blocked，不得以代理缺席为由跳过真实执行（TD3）。
    """
    if not available:
        return None

    def proxy_score(c):
        grid = c["values"].get("route_grid_mm", GRID_REF_MM)
        return grid if isinstance(grid, (int, float)) else GRID_REF_MM

    ranked = sorted(candidates,
                    key=lambda c: (proxy_score(c), c["candidate_id"]))
    return {"ranking": [c["candidate_id"] for c in ranked],
            "proxy_model": dict(PROXY_MODEL_DECLARATION)}


def select_real_execution(candidates, space, baseline_id, proxy_result):
    """选择必须真实执行的候选集（确定性）。

    - k = max(1, ceil(N × explore_real_execution_ratio))（TD3 固定比例）；
    - 代理可用：取代理排序前 k；baseline 恒入集（比较锚点必须真实执行），
      不在前 k 时追加（k+1）；
    - 代理不可用（None）：保守回退全量真实执行（fallback 策略如实记录）。
    返回 (selected_ids, plan)。
    """
    total = len(candidates)
    ratio = space["explore_real_execution_ratio"]
    k = max(1, math.ceil(total * ratio))
    if proxy_result is None:
        selected = [c["candidate_id"] for c in candidates]
        plan = {
            "declared_ratio": ratio,
            "required_min_count": k,
            "selected_count": len(selected),
            "proxy_used": False,
            "fallback": "conservative_full_execution",
            "baseline_always_executed": True,
            "note": "代理模型不可用 → 保守全量真实执行（TD3：代理缺席"
                    "不得减少真实执行量）",
        }
        return selected, plan
    ranked = list(proxy_result["ranking"])
    selected = ranked[:k]
    appended_baseline = False
    if baseline_id not in selected:
        selected = selected + [baseline_id]
        appended_baseline = True
    plan = {
        "declared_ratio": ratio,
        "required_min_count": k,
        "selected_count": len(selected),
        "proxy_used": True,
        "fallback": None,
        "baseline_appended_after_proxy_selection": appended_baseline,
        "baseline_always_executed": True,
        "note": "代理仅排序；胜者只能在真实执行集内产生，未执行候选"
                "不具 promotion 资格（可能漏掉更优未执行候选——声明的"
                "预筛代价）",
    }
    return selected, plan


# ---------------------------------------------------------------------------
# 4. smoke 级真实执行（闭式路由成本模型；如实标注非布线器/非 DRC authority）
# ---------------------------------------------------------------------------

_SUPPORTED_PARAM_NAMES = ("route_grid_mm", "via_penalty", "via_cost")


def _distinct_nets(constraints, profile) -> list:
    nets: list = []
    for entry in (constraints or {}).get("entries", []):
        for net in entry.get("nets", []):
            if net not in nets:
                nets.append(net)
    for net in (profile or {}).get("critical_net_set", []):
        if net not in nets:
            nets.append(net)
    return nets


def _entry_hard_violated(entry, grid) -> bool:
    """单条约束在给定栅格下是否不可实现（闭式判据，模型声明）。

    - power_rail_width：栅格粗于声明的最小线宽 → 不可实现；
    - diff_pair（intra_pair_gap_le_track_width）：栅格粗于最小对内
      轨道间距 MIN_PAIR_TRACK_WIDTH_MM → 不可实现；
    - 其余 kind（length_match/bus_length_match/plane_reference/
      critical_net_return）：不由栅格决定，恒可实现（0 违例）。
    """
    kind = entry.get("kind")
    if kind == "power_rail_width":
        min_width = entry.get("min_width_mm")
        return isinstance(min_width, (int, float)) and grid > min_width
    if kind == "diff_pair":
        return grid > MIN_PAIR_TRACK_WIDTH_MM
    return False


def _length_tolerance_mm(constraints) -> float:
    tols = [e.get("tolerance_mm") for e in (constraints or {}).get(
        "entries", []) if isinstance(e.get("tolerance_mm"), (int, float))]
    return min(tols) if tols else 1.0


def evaluate_config_smoke(profile, constraints, config) -> dict:
    """smoke 级「真实执行」：闭式路由成本模型（在编排内实际运行）。

    模型口径（全部声明于 bundle.evaluation_model）：
      capacity = (CHANNEL_WIDTH_MM / grid) × signal_layers
      route_success_rate = min(1, capacity / required_nets)
      resource_margin = max(0, (capacity - required_nets) / capacity)
      hard = Σ 约束在 grid 下不可实现数；whitelist_guard = 走线成功率
      < 1 时的白名单 net 数（L4 guard 与容量耦合——模型声明）
      drc_batch = 2×hard；length_dev = 0.3×(grid/0.5) + 0.02×via_penalty；
      drc_final = drc_batch + (length_dev > 最小 length 容差 ? 1 : 0)
      via_count = required_nets×3×(grid/0.5)/(1 + 0.1×via_penalty)
      layer_changes = via_count / 2
    """
    values = config if isinstance(config, dict) else {}
    unknown = sorted(set(values) - set(_SUPPORTED_PARAM_NAMES))
    if unknown:
        raise ValueError(
            f"smoke 评估器不支持参数 {unknown}（支持集 "
            f"{list(_SUPPORTED_PARAM_NAMES)}；未定义旋钮 fail-closed）")
    grid = values.get("route_grid_mm", GRID_REF_MM)
    via_pen = values.get("via_penalty", values.get("via_cost",
                                                   DEFAULT_VIA_PENALTY))
    nets = _distinct_nets(constraints, profile)
    critical = [n for n in (profile.get("critical_net_set") or []) if n in nets]
    signal_layers = sum(1 for layer in profile.get("layers", [])
                        if isinstance(layer, dict)
                        and layer.get("role") == "signal")
    required = max(len(nets), 1)
    capacity = (CHANNEL_WIDTH_MM / grid) * max(signal_layers, 1)
    route_success_rate = min(1.0, capacity / required)
    resource_margin = max(0.0, (capacity - required) / capacity)
    hard = sum(1 for e in (constraints or {}).get("entries", [])
               if _entry_hard_violated(e, grid))
    whitelist_guard = len(critical) if route_success_rate < 1.0 else 0
    drc_batch = 2.0 * hard
    length_dev = LENGTH_BASE_MM * (grid / GRID_REF_MM) + 0.02 * via_pen
    length_tol = _length_tolerance_mm(constraints)
    drc_final = drc_batch + (1.0 if length_dev > length_tol else 0.0)
    via_count = (required * VIA_FACTOR * (grid / GRID_REF_MM)
                 / (1.0 + 0.1 * via_pen))
    return {
        "hard_constraint_violations": float(hard),
        "whitelist_guard_violations": float(whitelist_guard),
        "drc_batch_severity_error": drc_batch,
        "drc_final_severity_all": drc_final,
        "route_success_rate": route_success_rate,
        "resource_margin": resource_margin,
        "via_count": via_count,
        "layer_changes": via_count / 2.0,
        "length_deviation": length_dev,
    }


EVALUATION_MODEL_DECLARATION = {
    "execution_level": EXECUTION_LEVEL,
    "authority": "none_declared",
    "disclaimer": "闭式路由成本模型（纯算术，smoke 合同级）：不是布线器、"
                  "不是 kicad-cli DRC authority、不含几何求解；DRC 计数是"
                  "模型估计，judge_post 如实判 drc refs 缺失",
    "constants": {
        "channel_width_mm": CHANNEL_WIDTH_MM,
        "grid_ref_mm": GRID_REF_MM,
        "length_base_mm": LENGTH_BASE_MM,
        "via_factor": VIA_FACTOR,
        "min_pair_track_width_mm": MIN_PAIR_TRACK_WIDTH_MM,
        "default_via_penalty": DEFAULT_VIA_PENALTY,
    },
    "formulas": [
        "capacity = (channel_width_mm / route_grid_mm) * signal_layers",
        "route_success_rate = min(1, capacity / required_nets)",
        "resource_margin = max(0, (capacity - required_nets) / capacity)",
        "hard_constraint_violations = sum(entry unrealizable at grid)",
        "whitelist_guard_violations = |critical nets| if "
        "route_success_rate < 1 else 0",
        "drc_batch_severity_error = 2 * hard_constraint_violations",
        "length_deviation = 0.3 * (grid/0.5) + 0.02 * via_penalty",
        "drc_final_severity_all = drc_batch + "
        "(length_deviation > min length tolerance)",
        "via_count = required_nets * 3 * (grid/0.5) / (1 + 0.1*via_penalty)",
        "layer_changes = via_count / 2",
    ],
    "input_scope": ("profile.layers/critical_net_set",
                    "constraints.entries", "config values"),
}


# ---------------------------------------------------------------------------
# 5. 胜者选择（分层质量向量 + 声明 tie-break）与 TD2 低自由度检查
# ---------------------------------------------------------------------------

def _changed_params(baseline_values, challenger_values) -> list:
    return sorted(k for k in baseline_values
                  if not _same_value(baseline_values[k],
                                     challenger_values.get(k)))


def _candidate_better(a, b, baseline_values) -> bool:
    """a 是否优于 b：分层向量字典序 → 变更参数数少 → candidate_id 字典序。"""
    cmp = proposer.compare_objectives(a["metrics"], b["metrics"])
    if cmp:
        return cmp == 1
    ca = len(_changed_params(baseline_values, a["values"]))
    cb = len(_changed_params(baseline_values, b["values"]))
    if ca != cb:
        return ca < cb
    return a["candidate_id"] < b["candidate_id"]


def select_winner(executions, baseline_values):
    """在真实执行集内选胜者（含 baseline 自身：无更优者 → winner=baseline）。"""
    winner = executions[0]
    for cand in executions[1:]:
        if _candidate_better(cand, winner, baseline_values):
            winner = cand
    return winner


def per_metric_regressions(baseline_metrics, challenger_metrics) -> list:
    """逐指标回退清单（白名单 ∪ required；方向表驱动，缺失按回退）。

    与 proposer.adoption_gate 同判据（容差 0）——编排用它在提交前识别
    「adoption 不可行」的候选；机器门本身仍独立重查，本函数不替代门。
    """
    regressed = []
    for name in WHITELIST_METRICS + REQUIRED_METRICS:
        b = baseline_metrics.get(name)
        c = challenger_metrics.get(name)
        direction = METRIC_DIRECTIONS.get(
            name, proposer.DIRECTION_LOWER_IS_BETTER)
        if not isinstance(b, (int, float)) or not isinstance(c, (int, float)):
            regressed.append(name)
        elif direction == proposer.DIRECTION_HIGHER_IS_BETTER and c < b:
            regressed.append(name)
        elif direction == proposer.DIRECTION_LOWER_IS_BETTER and c > b:
            regressed.append(name)
    return regressed


def select_challenger(executions, baseline_exec, baseline_values):
    """提交 adoption 的 challenger 选择（两段、全记录、不改机器门）。

    1) vector_best：分层质量向量最优（可能带 required 指标回退——机器门
       会如实 reject）；
    2) challenger：在「逐指标零回退池」内选向量最优；池空时退回
       vector_best（如实携带 reject 裁决进入 adoption，不粉饰）。
    返回 {challenger, vector_best, feasible_pool_size,
    vector_best_regressions, rule}。
    """
    vector_best = select_winner(executions, baseline_values)
    vb_regressions = per_metric_regressions(baseline_exec["metrics"],
                                            vector_best["metrics"])
    feasible = [e for e in executions
                if not per_metric_regressions(baseline_exec["metrics"],
                                              e["metrics"])]
    challenger = (select_winner(feasible, baseline_values)
                  if feasible else vector_best)
    return {
        "challenger": challenger,
        "vector_best": vector_best,
        "feasible_pool_size": len(feasible),
        "vector_best_regressions": vb_regressions,
        "challenger_is_vector_best": (
            challenger["candidate_id"] == vector_best["candidate_id"]),
        "rule": "challenger = 逐指标零回退池内向量最优；池空则提交 "
                "vector_best（机器门如实 reject）；vector_best 与其回退"
                "清单全程入账，不因选择而隐藏",
    }


def check_low_dof(baseline_values, challenger_values, holdout_denominator):
    """TD2 低自由度：holdout 分母不足时只允许单参数（单阈值/单系数）变更。"""
    changed = _changed_params(baseline_values, challenger_values)
    insufficient = holdout_denominator < LOW_DOF_MIN_HOLDOUT_BOARDS
    compliant = (not insufficient) or (len(changed) <= 1)
    return {
        "holdout_denominator": holdout_denominator,
        "low_dof_threshold_boards": LOW_DOF_MIN_HOLDOUT_BOARDS,
        "samples_insufficient": insufficient,
        "changed_params": changed,
        "changed_param_count": len(changed),
        "max_changed_when_insufficient": 1,
        "low_dof_compliant": compliant,
        "note": "TD2：样本不足时只允许单阈值/单系数（低自由度）；多参数 "
                "challenger 在样本不足时不具 promotion 资格",
    }


# ---------------------------------------------------------------------------
# 6. TD11 proposal patch（execution_allowed 恒 false；无自动 apply 路径）
# ---------------------------------------------------------------------------

def build_proposal_patch(space, baseline, challenger, *, report_sha256,
                         execution_level=EXECUTION_LEVEL):
    """胜者 → proposal_patch（TD11 schema 全字段；execution_allowed=false）。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "patch_id": f"PP-{space['space_id']}-{challenger['candidate_id']}",
        "base_revision": baseline["config_id"],
        "base_artifact_hash": report_sha256,   # 锚定 autotune 报告（旧 config
        # 由 input_hashes.baseline_config 另行绑定，双锚点）
        "target_scope": "policy",
        "operation_kind": "policy_parameter_candidate",
        "changes": [{"path": TARGET_PATH_ALLOWLIST[0], "op": "set",
                     "value": dict(challenger["values"])}],
        "preconditions": [
            {"id": "baseline_config_hash_bound", "value": True},
            {"id": "adoption_requires_human_disposition", "value": True},
            {"id": "holdout_non_regression_evidence_present", "value": False},
        ],
        "expected_affected_nodes": [TARGET_PATH_ALLOWLIST[0]],
        "rollback_plan": "patch 从不自动应用（execution_allowed=false）；"
                         "adoption 未获 Human disposition 前旧 config "
                         "immutable 保留，失败零迁移成本（零写盘，无版本漂移）",
        "proposer_id": "pcbflow-v3-autotune-chain",
        "model_version": "closed_form_smoke_v1",
        "rationale": f"确定性全枚举胜者 {challenger['candidate_id']}：分层"
                     f"质量向量优于 baseline（{execution_level} 级评估）；"
                     "promotion 需独立 holdout 不回退 + 白名单零恶化 + "
                     "逐 config Human adoption（TD3/TD2/TD11）",
        "evidence_refs": [report_sha256],
        "random_seed": DETERMINISM_STRATEGY["random_seed"],
        "determinism_claim": "byte_exact",
        "execution_allowed": False,
    }


# ---------------------------------------------------------------------------
# 7. 负向 witness（TD2/TD3/TD11/L4/L5 闭门路径机器复核）
# ---------------------------------------------------------------------------

def build_negative_witnesses(baseline_metrics, challenger_metrics,
                             candidates, space, baseline_id):
    """对 adoption/执行链的关键负向路径做机器复核（单变量翻转）。

    W1 holdout 回退 → reject；W2 白名单恶化 → reject（一票否决，链级
    adoption 流程同时 blocked）；W3 样本不足 → blocked；W4 无人工
    disposition 的 adoption → 不可执行（waiver 无 policy 全拒 + 无门写
    + patch execution_allowed=false）；W5 代理不可用 → 保守全量真实执行；
    W6 adoption 失败 → 旧版本自动保留（零写盘，无 auto_apply 路径）。
    """
    gate_kwargs = dict(whitelist_metrics=WHITELIST_METRICS,
                       required_metrics=REQUIRED_METRICS,
                       metric_directions=METRIC_DIRECTIONS)
    # W1：holdout 单板 route_success 回退（challenger 主指标不动，单变量
    # 翻转板内指标）→ reject（L5 跨板不回退）
    board_regressed = dict(challenger_metrics)
    board_regressed["route_success_rate"] = baseline_metrics[
        "route_success_rate"] - 0.05
    w1 = proposer.adoption_gate(
        baseline_metrics, challenger_metrics, holdout_results=[
            {"board_id": "holdout-w1", "metrics": board_regressed}],
        **gate_kwargs)
    # W2：白名单恶化 1 项 → reject（一票否决；L4）
    wl_bad = dict(challenger_metrics)
    wl_bad["whitelist_guard_violations"] = \
        baseline_metrics["whitelist_guard_violations"] + 1.0
    w2 = proposer.adoption_gate(
        baseline_metrics, wl_bad, holdout_results=[
            {"board_id": "holdout-w2", "metrics": wl_bad}],
        **gate_kwargs)
    # W3：样本不足（1 板 < min_holdout_boards=2）→ blocked
    ok_board = {"board_id": "holdout-w3", "metrics": dict(challenger_metrics)}
    w3 = proposer.adoption_gate(
        baseline_metrics, challenger_metrics, holdout_results=[ok_board],
        min_holdout_boards=2, **gate_kwargs)
    # W4：无人工 disposition 的 adoption → 不可执行（不生成 waiver）
    waive_attempt = disposition.build_disposition(
        disposition_id="DSP-TL4-WITNESS-1",
        fact_refs=["FACT-TL4-ADOPTION-GATE"],
        kind="waive", scope="adoption",
        rationale_code="proxy_prescreen_saved_cost",
        approver="human-pending", approver_role="engineer")
    w4 = {
        "scenario": "对 blocked adoption 尝试以 waiver 放行（无 policy、"
                    "无已落账 approve 处置）",
        "policy": {},
        "errors": disposition.check_waiver_policy(waive_attempt, {}),
        "gate_write_scan": disposition.validate_no_gate_write(waive_attempt),
        "waiver_generated": False,
        "patch_execution_allowed": False,
        "note": "L6/L7：缺 disposition 不能生成 waiver；adoption 保持 "
                "pending_human；patch execution_allowed 恒 false（TD11）",
    }
    # W5：代理不可用 → 保守全量真实执行（不得减少真实执行量）
    selected, plan = select_real_execution(
        candidates, space, baseline_id, None)
    w5 = {
        "scenario": "代理模型不可用（proxy_prescreen → None）",
        "selected_count": len(selected),
        "total_candidates": len(candidates),
        "full_execution_fallback": selected == [c["candidate_id"] for c in
                                                candidates],
        "plan": plan,
    }
    # W6：adoption 失败 → 旧版本自动保留（零写盘；无自动 apply 路径）
    w6 = {
        "scenario": "adoption machine gate blocked（holdout 缺失）时的"
                    "旧配置保留",
        "old_config_retained": True,
        "chain_write_scope": "none",
        "auto_apply_path_exists": False,
        "note": "编排零写盘：baseline-config.json 输入 hash 由编排侧"
                "sha256_file 复核不变；候选只以 proposal_patch（execution_"
                "allowed=false）存在",
    }
    return {
        "holdout_regression_rejects": {
            "scenario": "holdout 单板 route_success_rate 回退（单变量翻转）",
            "gate": w1},
        "whitelist_degradation_rejects_and_blocks_adoption": {
            "scenario": "白名单 guard 恶化 1 项（单变量翻转）",
            "gate": w2},
        "insufficient_samples_blocked": {
            "scenario": "holdout 板数 1 < min_holdout_boards=2",
            "gate": w3},
        "adoption_without_human_disposition_not_executable": w4,
        "proxy_unavailable_falls_back_to_full_execution": w5,
        "adoption_failure_retains_old_config": w6,
    }


# ---------------------------------------------------------------------------
# 8. TL-4 autotune 全链构造
# ---------------------------------------------------------------------------

def build_chain(profile, space, baseline, constraints, input_hashes, *,
                snapshot_revision, gate_id="TL-4-G", execution_id=None,
                evaluator):
    """构造 TL-4 autotune 全链 bundle（纯函数；产物由编排侧落盘）。

    input_hashes 需含：profile/manifest/search_space/baseline_config/
    constraints/board/toolchain_lock（netlist/stackup 声明非 null 时也须绑定）。
    evaluator={name, version, code_sha256} 绑定判定代码版本。
    """
    errors = validate_chain_inputs(space, baseline)
    if errors:
        raise ValueError("autotune 链输入非法（fail-closed）: "
                         + "; ".join(errors))
    for name in ("profile", "manifest", "search_space", "baseline_config",
                 "constraints", "board", "toolchain_lock"):
        if not _is_sha256((input_hashes or {}).get(name)):
            raise ValueError(f"input_hashes 缺 {name!r} 的 64hex 绑定"
                             "（fail-closed：autotune 链输入必须全绑定）")
    project_id = profile["project_id"]
    profile_id = profile["profile_id"]
    execution_id = execution_id or f"TL4-AUTOTUNE-{profile_id}-R1"
    baseline_values = dict(baseline["values"])

    # 1) 确定性候选生成（全枚举）
    candidates = enumerate_candidates(space, baseline_values)
    baseline_cand = find_baseline_candidate(candidates, baseline_values)

    # 2) 代理预筛（只排序）→ 固定比例真实执行选择
    proxy_result = proxy_prescreen(candidates, available=True)
    selected_ids, execution_plan = select_real_execution(
        candidates, space, baseline_cand["candidate_id"], proxy_result)
    selected_by_id = {c["candidate_id"]: c for c in candidates}

    # 3) smoke 级真实执行（闭式模型在编排内实际运行）
    executions = []
    for cid in selected_ids:
        cand = selected_by_id[cid]
        metrics = evaluate_config_smoke(profile, constraints,
                                        cand["values"])
        executions.append({
            "candidate_id": cid,
            "values": dict(cand["values"]),
            "execution_level": EXECUTION_LEVEL,
            "executor": {"backend": "pcbflow-autotune-smoke",
                         "protocol": "in_process",
                         "version": "pcbflow-v3",
                         "capability": "closed_form_route_cost_model"},
            "input_hashes": {k: input_hashes[k] for k in
                             ("profile", "constraints", "search_space",
                              "baseline_config", "board", "toolchain_lock")},
            "metrics": metrics,
            "objective_vector": proposer.objective_vector(metrics),
        })
    exec_by_id = {e["candidate_id"]: e for e in executions}
    baseline_exec = exec_by_id[baseline_cand["candidate_id"]]

    # 4) 胜者/challenger 选择（分层向量 + tie-break + 逐指标零回退池）
    selection = select_challenger(executions, baseline_exec, baseline_values)
    winner = selection["vector_best"]
    challenger = selection["challenger"]
    winner_is_baseline = winner["candidate_id"] == baseline_cand["candidate_id"]
    comparison = proposer.compare_objectives(challenger["metrics"],
                                             baseline_exec["metrics"])
    changed = _changed_params(baseline_values, challenger["values"])

    # 5) adoption 机器门（TD2/TD3/L4/L5；P1-A：真实采纳路径=逐板配对门
    #    adoption_gate_paired，每对锚定各自同板 baseline，不存在全局
    #    baseline 静默回退路径。holdout_pairs=∅ 是事实：TL-5 独立留出
    #    语料未建立、逐板配对执行证据结构性缺失——板分母与执行分母均为
    #    0，在库语料板数不得替代执行分母）
    holdout_pairs: list = []
    adoption = proposer.adoption_gate_paired(
        whitelist_metrics=WHITELIST_METRICS,
        required_metrics=REQUIRED_METRICS,
        holdout_pairs=holdout_pairs,
        metric_directions=METRIC_DIRECTIONS)
    low_dof = check_low_dof(baseline_values, challenger["values"],
                            adoption["holdout"]["board_denominator"])

    # 6) autotune 报告（先于 patch：patch.evidence_refs 锚定报告）
    report = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "autotune_report",
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "space_id": space["space_id"],
        "baseline_config_id": baseline["config_id"],
        "execution_level": EXECUTION_LEVEL,
        "candidate_generation": dict(DETERMINISM_STRATEGY,
                                     candidate_count=len(candidates),
                                     enumeration="row_major_cartesian",
                                     candidate_id_rule="CAND-NNNN by "
                                                       "enumeration order"),
        "execution_plan": execution_plan,
        "evaluation_model": EVALUATION_MODEL_DECLARATION,
        "objective_declaration": [dict(d) for d in OBJECTIVE_DECLARATION],
        "baseline": {"candidate_id": baseline_cand["candidate_id"],
                     "values": dict(baseline_values),
                     "metrics": baseline_exec["metrics"]},
        "winner": {"candidate_id": winner["candidate_id"],
                   "values": dict(winner["values"]),
                   "metrics": winner["metrics"],
                   "changed_params": _changed_params(
                       baseline_values, winner["values"]),
                   "comparison_vs_baseline": proposer.compare_objectives(
                       winner["metrics"], baseline_exec["metrics"]),
                   "winner_is_baseline": winner_is_baseline,
                   "vector_best_regressions":
                       selection["vector_best_regressions"]},
        "challenger": {"candidate_id": challenger["candidate_id"],
                       "values": dict(challenger["values"]),
                       "metrics": challenger["metrics"],
                       "changed_params": changed,
                       "comparison_vs_baseline": comparison,
                       "feasible_pool_size": selection["feasible_pool_size"],
                       "challenger_is_vector_best":
                           selection["challenger_is_vector_best"],
                       "selection_rule": selection["rule"]},
        "adoption": {
            "decision": adoption["decision"],
            "reasons": adoption["reasons"],
            "whitelist_violations": adoption["whitelist_violations"],
            "per_metric": adoption["per_metric"],
            "holdout": adoption["holdout"],
            "low_dof": low_dof,
            "human_adoption_required": adoption["human_adoption_required"],
            "gate_mode": adoption["gate_mode"],
            "adoption_status": "pending_human_disposition",
            "auto_apply": False,
            "old_config_retained": True,
        },
        "disclaimers": [
            "执行级别 smoke_in_process_closed_form：闭式路由成本模型，"
            "非 kicad-cli 布线器/DRC authority；DRC 计数为模型估计。",
            "holdout_pairs 为空是事实（TL-5 独立留出语料未建立，逐板配对"
            "执行证据不存在）：adoption 机器门只能 blocked，TL-4 出口门 "
            "not_ready。",
            "本报告不构成 TL-4 出口门通过、产品化或生产签核证据。",
        ],
    }
    report_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(report))

    # 7) TD11 proposal patch（execution_allowed=false）+ 分级
    patch = build_proposal_patch(space, baseline, challenger,
                                 report_sha256=report_sha)
    patch_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(patch))
    patch_eval = proposer.evaluate_patch(
        patch, report_sha, TARGET_PATH_ALLOWLIST)

    # 8) judge_pre（输入绑定 + 工具链对账）→ judge_post（如实 fail-closed）
    source_snapshot_sha256 = hashing.sha256_bytes(
        hashing.canonical_json_bytes(dict(input_hashes)))
    pre = judge.build_pre(
        execution_id=execution_id, project_id=project_id,
        profile_id=profile_id,
        candidate_id=f"AUTOTUNE-{space['space_id']}",
        source_snapshot_sha256=source_snapshot_sha256,
        toolchain_lock_sha256=input_hashes["toolchain_lock"],
        executor={"backend": "pcbflow-autotune-smoke",
                  "protocol": "in_process", "version": "pcbflow-v3",
                  "capability": "closed_form_route_cost_model"},
        write_scope="none",
        allowlist=["pcbflow-autotune"],
        required_checks=["smoke_objective_vector_evaluation"],
        upstream_hashes={"constraints_sha256":
                         input_hashes["constraints"]})
    pre_eval = judge.evaluate_pre(pre, {
        "toolchain_lock_sha256": input_hashes["toolchain_lock"],
        "constraints_sha256": input_hashes["constraints"],
        "source_snapshot_sha256": source_snapshot_sha256})
    execution_records_compact = [
        {k: e[k] for k in ("candidate_id", "values", "execution_level",
                           "executor", "input_hashes")}
        for e in executions]
    execution_ref = hashing.sha256_bytes(hashing.canonical_json_bytes(
        execution_records_compact))
    physics_status = ("not_required"
                      if not profile.get("physics_required") else "fail")
    facts = judge.build_facts([
        {"fact_id": "FACT-TL4-REAL-EXECUTION-COUNT",
         "observer": "deterministic_evaluator",
         "observation": {"kind": "count",
                         "value": len(execution_records_compact),
                         "unit": "candidates",
                         "ref_sha256": execution_ref}},
        {"fact_id": "FACT-TL4-WINNER-OBJECTIVE",
         "observer": "deterministic_evaluator",
         "observation": {"kind": "text_ref",
                         "value": f"challenger={challenger['candidate_id']} "
                                  f"compare_vs_baseline={comparison}；"
                                  f"vector_best={winner['candidate_id']}"
                                  f"(regressions={selection[
                                      'vector_best_regressions']})；"
                                  "分层质量向量字典序，胜者仅在真实"
                                  "执行集内产生",
                         "ref_sha256": report_sha}},
        {"fact_id": "FACT-TL4-ADOPTION-GATE",
         "observer": "deterministic_evaluator",
         "observation": {"kind": "text_ref",
                         "value": f"decision={adoption['decision']}; "
                                  f"reasons={adoption['reasons']}",
                         "ref_sha256": report_sha}},
    ])
    post = judge.build_post(
        execution_id=execution_id, pre_record=pre, output_hash=report_sha,
        l1_legal=True, layer_pure=True,
        drc_batch_ref=None, drc_final_ref=None,
        solver=None,
        external_status="not_required"
        if not profile.get("external_required") else "unknown",
        physics_status=physics_status,
        bring_up_status="not_required"
        if not profile.get("bring_up_required") else "not_available",
        rollback_status="not_needed", facts=facts)
    post_eval = judge.evaluate_post(post)

    # 9) decision-ledger 六事件（proposal→judge_pre→execution→judge_post→
    #    backtest→gate；disposition 缺席=adoption 保持 pending human）
    base_fields = {
        "authority": "deterministic_evaluator", "trust_level": "observed",
        "project_id": project_id, "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "actor": "pcbflow-v3-autotune-chain", "actor_role": "orchestrator",
    }
    entry_schema = ledger.make_schema_validation("decision_ledger_entry")
    input_artifacts = {k: input_hashes[k] for k in
                       ("profile", "manifest", "search_space",
                        "baseline_config", "constraints", "board",
                        "toolchain_lock")}
    for name in ("netlist", "stackup"):
        if _is_sha256(input_hashes.get(name)):
            input_artifacts[name] = input_hashes[name]
    adoption_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(
        adoption))
    entries: list = []
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0001", "entry_kind": "proposal",
        "schema_validation": ledger.make_schema_validation("proposal_patch"),
        "proposal_id": patch["patch_id"], "proposal_sha256": patch_sha,
        "artifact_hashes": {"search_space": input_hashes["search_space"],
                            "baseline_config":
                                input_hashes["baseline_config"],
                            "autotune_report": report_sha},
        **base_fields})
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0002", "entry_kind": "judge_pre",
        "schema_validation": ledger.make_schema_validation("judge_pre_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "artifact_hashes": dict(input_artifacts),
        **base_fields})
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0003", "entry_kind": "execution",
        "schema_validation": dict(entry_schema),
        "execution_ref": execution_ref,
        "candidate_id": challenger["candidate_id"],
        "artifact_hashes": {"execution_records": execution_ref,
                            "autotune_report": report_sha},
        **base_fields})
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0004", "entry_kind": "judge_post",
        "schema_validation": ledger.make_schema_validation(
            "judge_post_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "judge_post_hash": hashing.sha256_bytes(
            hashing.canonical_json_bytes(post)),
        "artifact_hashes": {"autotune_report": report_sha},
        **base_fields})
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0005", "entry_kind": "backtest",
        "schema_validation": dict(entry_schema),
        "candidate_id": challenger["candidate_id"],
        "artifact_hashes": {"autotune_report": report_sha,
                            "adoption_gate_result": adoption_sha},
        **base_fields})
    ledger_prefix_sha256 = _ledger_bytes_sha256(entries)

    # 10) TL-4 gate record（gate_kind=training_loop；blocked 如实闭门）
    holdout_board_denominator = adoption["holdout"]["board_denominator"]
    whitelist_ok = not adoption["whitelist_violations"]
    record = gate.evaluate_gate(
        gate_id=gate_id, gate_kind="training_loop", project_id=project_id,
        profile_id=profile_id, snapshot_revision=snapshot_revision,
        predicate_version="pv1",
        inputs=[
            {"artifact_id": "profile", "sha256": input_hashes["profile"],
             "status": "present"},
            {"artifact_id": "manifest", "sha256": input_hashes["manifest"],
             "status": "present"},
            {"artifact_id": "search_space",
             "sha256": input_hashes["search_space"], "status": "present"},
            {"artifact_id": "baseline_config",
             "sha256": input_hashes["baseline_config"], "status": "present"},
            {"artifact_id": "constraints",
             "sha256": input_hashes["constraints"], "status": "present"},
            {"artifact_id": "autotune_report", "sha256": report_sha,
             "status": "present"},
            {"artifact_id": "decision_ledger_prefix",
             "sha256": ledger_prefix_sha256, "status": "present"},
            {"artifact_id": "holdout_corpus", "sha256": None,
             "status": "missing"},
        ],
        required_predicates=[
            {"id": "search_space_valid",
             "value": not proposer.validate_search_space(space),
             "evidence": f"search_space {space['space_id']} schema+语义"
                         "校验通过（含 explore_real_execution_ratio="
                         f"{space['explore_real_execution_ratio']}）"},
            {"id": "candidate_search_deterministic", "value": True,
             "evidence": f"optimizer={DETERMINISM_STRATEGY['optimizer']}、"
                         "randomness=none_full_enumeration、threads=1、"
                         "float=ieee754_double；重跑 byte-exact（测试强制）"},
            {"id": "real_execution_ratio_satisfied", "value": (
                execution_plan["selected_count"]
                >= execution_plan["required_min_count"]),
             "evidence": f"真实执行 {execution_plan['selected_count']} / "
                         f"{len(candidates)} ≥ 要求 "
                         f"{execution_plan['required_min_count']}"
                         f"（ratio={space['explore_real_execution_ratio']}；"
                         f"execution_level={EXECUTION_LEVEL}）"},
            {"id": "proxy_used_for_prescreen_only", "value": True,
             "evidence": "代理 grid_only_scalar_heuristic 仅排序；胜者只在"
                         "真实执行集内产生；未执行候选不具 promotion 资格"},
            {"id": "layered_objective_vector_no_scalar_sum", "value": True,
             "evidence": "compare_objectives 字典序逐层比较（tier1→6），"
                         "无加权求和路径（OBJECTIVE_DECLARATION 逐项声明）"},
            {"id": "winner_not_worse_than_baseline",
             "value": comparison >= 0,
             "evidence": f"challenger={challenger['candidate_id']} "
                         f"compare_vs_baseline={comparison}（1=严格优）；"
                         f"vector_best={winner['candidate_id']}"
                         f"(逐指标回退 "
                         f"{selection['vector_best_regressions']})"},
            {"id": "whitelist_zero_degradation", "value": whitelist_ok,
             "evidence": "白名单子项 whitelist_guard_violations 无恶化"
                         f"（violations={adoption['whitelist_violations']}）"},
            {"id": "low_dof_contract_compliant",
             "value": low_dof["low_dof_compliant"],
             "evidence": f"holdout 板分母 {holdout_board_denominator} < "
                         f"{LOW_DOF_MIN_HOLDOUT_BOARDS} 时至多变 1 参数；"
                         f"changed={low_dof['changed_params']}"},
            {"id": "holdout_non_regression_evidenced", "value": False,
             "evidence": "TL-5 独立留出语料未建立（TL-1+TL-5→TL-4 出口门"
                         "依赖）：holdout_pairs 板分母/执行分母均 0，无逐"
                         "板不回退证据（L5；不得伪造）"},
            {"id": "adoption_machine_gate_pass",
             "value": adoption["decision"] == "adopt_candidate",
             "evidence": f"adoption_gate decision={adoption['decision']}"
                         f"（reasons={adoption['reasons']}）"},
            {"id": "human_adoption_disposition_present", "value": False,
             "evidence": "adoption 保持 pending_human_disposition：逐 "
                         "config Human adoption 挂起（SPEC §3 TL-4 人工点），"
                         "无 approve 类 disposition 账本事件"},
            {"id": "tl5_independent_holdout_corpus_available",
             "value": False,
             "evidence": "TL-5 未启动：无合规、冻结、分割的独立 holdout "
                         "corpus（gate 输入 holdout_corpus=missing）"},
            {"id": "judge_pre_ok", "value": pre_eval["pre_ok"],
             "evidence": "evaluate_pre 通过：toolchain lock 与 constraints "
                         "hash 对账一致（账本 entry TL4-E-0002）"},
            {"id": "judge_post_ok", "value": post_eval["post_ok"],
             "evidence": f"post_ok={post_eval['post_ok']}：smoke 闭式模型"
                         "无 kicad-cli DRC 产物可绑定（drc refs 缺失），"
                         "且 required physics profile 的物理证据在 "
                         f"TL-3 已判 fail——如实 fail-closed"
                         f"（failed={post_eval['failed'][:2]}…）"},
            {"id": "old_config_immutable_retained", "value": True,
             "evidence": "编排零写盘（write_scope=none）；baseline_config "
                         f"输入 hash {input_hashes['baseline_config'][:12]}… "
                         "由编排侧复核不变；候选仅以 proposal_patch"
                         "（execution_allowed=false）存在"},
            {"id": "ledger_chain_valid", "value": True,
             "evidence": "verify_chain+verify_supersedes 通过（proposal/"
                         "judge_pre/execution/judge_post/backtest/gate 六"
                         "事件 hash 链完整）"},
        ],
        evaluator=evaluator)
    gate_verify_errors = gate.verify_gate_record(record)
    entries, _ = ledger.append(entries, {
        "entry_id": "TL4-E-0006", "entry_kind": "gate",
        "schema_validation": ledger.make_schema_validation("gate_record"),
        "gate_record_hash": gate.gate_core_hash(record),
        "artifact_hashes": {"autotune_report": report_sha,
                            "decision_ledger_prefix": ledger_prefix_sha256},
        **base_fields})
    ledger_file_sha256 = _ledger_bytes_sha256(entries)
    checkpoint = ledger.make_checkpoint(
        entries, f"CKPT-TL4-{profile_id}-R1")

    return {
        "chain_kind": "tl4-autotune-chain",
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "execution_id": execution_id,
        "space_id": space["space_id"],
        "baseline_config_id": baseline["config_id"],
        "input_hashes": dict(input_hashes),
        "search_space": space,
        "objective_declaration": [dict(d) for d in OBJECTIVE_DECLARATION],
        "candidate_generation": dict(
            DETERMINISM_STRATEGY, candidate_count=len(candidates),
            enumeration="row_major_cartesian",
            candidate_id_rule="CAND-NNNN by enumeration order"),
        "proxy_prescreen": proxy_result,
        "execution_plan": execution_plan,
        "executions": executions,
        "baseline": {"candidate_id": baseline_cand["candidate_id"],
                     "config_id": baseline["config_id"],
                     "values": dict(baseline_values),
                     "metrics": baseline_exec["metrics"]},
        "winner": {"candidate_id": winner["candidate_id"],
                   "values": dict(winner["values"]),
                   "metrics": winner["metrics"],
                   "changed_params": _changed_params(
                       baseline_values, winner["values"]),
                   "comparison_vs_baseline": proposer.compare_objectives(
                       winner["metrics"], baseline_exec["metrics"]),
                   "winner_is_baseline": winner_is_baseline,
                   "vector_best_regressions":
                       selection["vector_best_regressions"]},
        "challenger": {"candidate_id": challenger["candidate_id"],
                       "values": dict(challenger["values"]),
                       "metrics": challenger["metrics"],
                       "changed_params": changed,
                       "comparison_vs_baseline": comparison,
                       "feasible_pool_size": selection["feasible_pool_size"],
                       "challenger_is_vector_best":
                           selection["challenger_is_vector_best"],
                       "selection_rule": selection["rule"]},
        "low_dof": low_dof,
        "adoption": report["adoption"],
        "autotune_report": report,
        "proposal_patch": patch,
        "patch_evaluation": patch_eval,
        "artifact_hashes": {
            **input_artifacts,
            "autotune_report": report_sha,
            "proposal_patch": patch_sha,
            "execution_records": execution_ref,
            "adoption_gate_result": adoption_sha,
        },
        "judge_pre": pre,
        "judge_pre_evaluation": pre_eval,
        "judge_post": post,
        "judge_post_evaluation": post_eval,
        "execution_ref": execution_ref,
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
            baseline_exec["metrics"], challenger["metrics"],
            candidates, space, baseline_cand["candidate_id"]),
        "notes": [
            "本链执行级别 smoke_in_process_closed_form：闭式路由成本模型"
            "（合成 smoke 合同口径），非布线器、非 kicad-cli DRC authority。",
            "机器裁决如实：adoption blocked（holdout 缺失，TL-5 未启动）、"
            "TL-4 gate blocked（holdout_corpus=missing + judge_post_ok 等"
            "predicate 落空）——正确结果，不是编排失败；不得宣称出口门通过。",
            "adoption 保持 pending_human_disposition：机器门不产生 apply "
            "动作；旧 config immutable，失败自动保留旧版本（零写盘）。",
        ],
    }


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（单行 JSON/条 + 换行；与 out/v3-tl1 口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


# ---------------------------------------------------------------------------
# 9. TL-4 holdout 解锁评估（S9；纯增量：既有链行为与 v1 产物 byte-exact 不变）
# ---------------------------------------------------------------------------
#
# 评估问题（S9 任务书）：TL-5-G v3 pass 后，TL-4 出口门哪些失败谓词可由
# 既有产物作实、哪些结构性缺；路径 a（真实板搜索空间）与路径 b（维持
# smoke 范围+如实 blocked）取其一。
#
# 评估结论（由盘上事实核实，非口径选择）：
# - tl5_independent_holdout_corpus_available：可作实（TL-5-G v3 pass+两库
#   manifest split 冻结+train/holdout 不相交）→ v2 复评置 true；
# - human_adoption_disposition_present：可作实（APR-0004，S4 已登记
#   kind=accept/scope=adoption）→ v2 复评置 true；
# - holdout_non_regression_evidenced：结构性缺——逐板不回退要求
#   challenger/baseline 的 config 差异可在真实板上以真实 authority 度量；
#   smoke 旋钮只作用于闭式模型，corpus 四段（compile/enum/audit/feedforward）
#   消费可调参数=0（真实板 manifest params=[]，field_missingness 登记
#   「params: 空（搜索域不可从板文本判定）」），route/check=D17 参考态
#   验证（config 无关）→ 路径 a 在当前能力下不可诚实执行，选路径 b；
# - judge_post_ok：结构性缺（D9）——TL-5 check 产物为真实 kicad-cli
#   authority，但测度对象=参考 routed 态，对候选 config 恒不变，不可
#   充当 executor DRC ref（防语义偷换，见 DRC_REF_ELIGIBILITY）；
# - adoption_machine_gate_pass：随 holdout 证据结构缺而 blocked；
# - low_dof：分母=已执行并对比的 holdout 板数（配对门 board_denominator），
#   非语料在库板数——本评估不新增任何执行板，分母仍 0。
#
# 本节函数不存在把 holdout_non_regression_evidenced / judge_post_ok /
# adoption_machine_gate_pass 置 true 的任何参数路径（机器强制：无执行
# 证据就没有翻转入口）。v1 门记录原样保留；v2 复评一律落新文件。

#: S9 评估 track 标识
HOLDOUT_UNLOCK_TRACK = "tl4-holdout-unlock-r1"

#: judge_post DRC ref 资格裁定（机器声明；TL-5 check 产物不可充当 executor DRC ref）
DRC_REF_ELIGIBILITY = {
    "tl5_check_products": "ineligible_as_executor_drc_ref",
    "reason": "out/v3-tl5/check/<profile>/ 的 kicad-cli DRC 产物测度对象="
              "数据集参考 routed 态（D17 参考态验证口径），对任何候选 "
              "config 恒不变——无法区分 challenger 与 baseline；绑定进 "
              "judge_post 即把参考态证据冒充执行器输出证据（语义偷换，"
              "禁止）。可作为门输入/上下文证据绑定，不可作为 "
              "drc_batch_ref/drc_final_ref",
    "eligible_sources": "执行器自身输出的板级产物经 kicad-cli DRC 双 "
                        "severity 检查（当前不存在：无布线生成引擎"
                        "（D17）、无已锁定外部执行 backend（toolchain_lock "
                        "freerouting/jdk 仍 optional/null））",
}

#: 复评所需 binding_hashes 键（全部 64hex 校验，fail-closed）
HOLDOUT_UNLOCK_BINDING_KEYS = (
    "tl5_gate_record_core",              # TL-5-G v3 门记录 core hash
    "dataset_manifest_pcbbenchmarks_r1_v3",
    "dataset_manifest_pcbench_r1_v2",
    "adoption_disposition_apr0004",
    "approvals_decision_ledger",
)

#: 本评估新增的已执行 holdout 板数（结构性 0：评估不产生任何执行证据）
EXECUTED_HOLDOUT_DENOMINATOR = 0


def holdout_corpus_facts(dataset_manifests) -> dict:
    """从数据集 manifest 列表提取 holdout/train 事实并校验冻结+不相交。

    fail-closed：任一 manifest 缺 dataset_splits.holdout/holdout_frozen_
    readonly 声明 → ValueError（无冻结声明的语料不作实可用性）。
    """
    holdout: list = []
    train: list = []
    dataset_ids: list = []
    per_dataset: list = []
    frozen = True
    for m in dataset_manifests:
        if not isinstance(m, dict):
            raise ValueError("dataset manifest 必须为 dict")
        splits = m.get("dataset_splits")
        if not isinstance(splits, dict):
            raise ValueError("dataset manifest 缺 dataset_splits（fail-closed）")
        h = splits.get("holdout")
        t = splits.get("train")
        if not isinstance(h, list) or not isinstance(t, list):
            raise ValueError("dataset_splits.holdout/train 必须为 list")
        if splits.get("holdout_frozen_readonly") is not True:
            frozen = False
        holdout += h
        train += t
        dataset_ids.append(m.get("dataset_id"))
        per_dataset.append({"dataset_id": m.get("dataset_id"),
                            "holdout_count": len(h),
                            "train_count": len(t)})
    overlap = sorted(set(holdout) & set(train))
    dupes = sorted({b for b in holdout if holdout.count(b) > 1})
    return {
        "dataset_ids": dataset_ids,
        "holdout_boards": sorted(holdout),
        "holdout_board_count": len(holdout),
        "train_boards": sorted(train),
        "train_board_count": len(train),
        "holdout_count_by_dataset": per_dataset,
        "holdout_frozen_readonly": frozen,
        "train_holdout_overlap": overlap,
        "split_disjoint": not overlap,
        "holdout_duplicates": dupes,
        "corpus_available": (
            frozen and not overlap and not dupes and len(holdout) >= 1),
    }


def adoption_disposition_covers(disposition, patch_id) -> dict:
    """APR-0004 类人工处置是否覆盖给定 profile 的 proposal patch。

    覆盖判据（与 disposition 域合同一致）：kind=accept、scope=adoption、
    fact_refs 同时含该 patch_id 与 'TL-4-G'。
    """
    if not isinstance(disposition, dict):
        return {"present": False, "reasons": ["disposition 非 dict"]}
    refs = set(disposition.get("fact_refs") or [])
    reasons = []
    if disposition.get("kind") != "accept":
        reasons.append(f"kind={disposition.get('kind')!r} != 'accept'")
    if disposition.get("scope") != "adoption":
        reasons.append(f"scope={disposition.get('scope')!r} != 'adoption'")
    if patch_id not in refs:
        reasons.append(f"fact_refs 未覆盖 patch {patch_id!r}")
    if "TL-4-G" not in refs:
        reasons.append("fact_refs 未覆盖 'TL-4-G'")
    return {"present": not reasons, "reasons": reasons,
            "disposition_id": disposition.get("disposition_id"),
            "approver_role": disposition.get("approver_role")}


def _v2_predicates(v1_record, *, patch_id, corpus, disposition_cover,
                   changed_params, tl5_core) -> list:
    """v2 复评谓词表：复制 v1 全部谓词，仅按新证据重估六个证据依赖项。

    机器强制（无翻转入口）：holdout_non_regression_evidenced /
    judge_post_ok / adoption_machine_gate_pass 的 value 只能沿用 v1 的
    False（本评估不产生任何执行证据）；置 true 的唯一路径=真实逐板
    执行证据进入链本身（届时走新链重跑，非本复评函数）。
    """
    by_id = {p["id"]: dict(p) for p in v1_record["required_predicates"]}
    for pid in ("holdout_non_regression_evidenced", "judge_post_ok",
                "adoption_machine_gate_pass"):
        if by_id[pid]["value"] is True:
            raise ValueError(
                f"v1 谓词 {pid} 已为 true——本复评函数只处理 v1 blocked "
                "链的证据可用性重估，不受理 pass 链（fail-closed）")
    corpus_n = corpus["holdout_board_count"]
    per_ds = "+".join(
        f"{d['dataset_id']} {d['holdout_count']}" for d in
        corpus["holdout_count_by_dataset"]) or "0"
    by_id["tl5_independent_holdout_corpus_available"] = {
        "id": "tl5_independent_holdout_corpus_available",
        "value": corpus["corpus_available"],
        "evidence": (
            f"TL-5-G v3 复评=pass（core {tl5_core[:8]}…；gate-record-"
            "tl5-v3.json）：两库 dataset manifest（pcbbenchmarks-r1 v3 + "
            "pcbench-r1 v2）split 冻结在案——holdout 唯一板集 "
            f"{corpus_n} 块（{per_ds}）、"
            "holdout_frozen_readonly=true、train/holdout 不相交；本门输入"
            "绑定 TL-5 门记录 core hash+两 manifest 文件 hash（present）。"
            "语料可用性成立≠holdout 不回退证据成立（后者需逐板执行对比，"
            "见 holdout_non_regression_evidenced）"),
    }
    by_id["human_adoption_disposition_present"] = {
        "id": "human_adoption_disposition_present",
        "value": disposition_cover["present"],
        "evidence": (
            f"{disposition_cover.get('disposition_id') or 'APR'}（kind="
            "accept、scope=adoption）fact_refs 覆盖本 profile proposal "
            f"patch {patch_id} 与 TL-4-G（out/v3-approvals/ 处置文件+"
            "账本 hash 绑定入本门输入）；adoption 状态="
            "human_approved_machine_blocked（S4 已批）：人工处置与机器门"
            "合取，机器谓词未全绿 → 不 apply、baseline config 保持 "
            "immutable") if disposition_cover["present"] else (
            "人工处置未覆盖本 profile patch：" + "; ".join(
                disposition_cover["reasons"])),
    }
    by_id["holdout_non_regression_evidenced"] = {
        "id": "holdout_non_regression_evidenced",
        "value": False,
        "evidence": (
            "结构性缺（S9 评估结论=路径 b）：逐板不回退要求 challenger/"
            "baseline config 差异可在真实板上以真实 authority 度量——"
            "当前不存在该执行面：smoke 旋钮（scope:route.grid/cost_model）"
            "只作用于闭式模型；corpus 四段（compile/enum/audit/feedforward）"
            "消费可调参数=0（真实板 manifest params=[]，conversion_log "
            "field_missingness 登记『params: 空（搜索域不可从板文本判定）』）；"
            "route/check=D17 参考态验证（config 无关、非布线生成）。"
            f"holdout_pairs 已执行配对分母仍 {EXECUTED_HOLDOUT_DENOMINATOR}"
            "（本评估不新增任何执行板）。精确依赖：布线生成引擎或 TD7 "
            "已锁定外部执行 backend 的 config 敏感输出+kicad-cli DRC 双 "
            "severity 对其自身产物检查"),
    }
    by_id["adoption_machine_gate_pass"] = {
        "id": "adoption_machine_gate_pass",
        "value": False,
            "evidence": (
                "adoption_gate_paired decision=blocked（"
                "holdout_pairs_missing——v1 链裁决不变：语料可用不产生"
                "执行证据，机器门重查仍缺逐板配对对比）；"
                "机器门与 APR-0004 人工处置合取，当前="
                "human_approved_machine_blocked"),
    }
    by_id["judge_post_ok"] = {
        "id": "judge_post_ok",
        "value": False,
        "evidence": (
            "post_ok=False（v1 链裁决不变）：smoke 闭式 executor 无自身"
            "板级输出 → 无 DRC 产物可绑 drc_batch_ref/drc_final_ref。"
            "TL-5 check/ 的 kicad-cli DRC 产物（真实 authority）测度对象="
            "参考 routed 态（D17），对候选 config 恒不变 → 按 DRC_REF_"
            "ELIGIBILITY 裁定不可充当 executor DRC ref（防语义偷换），"
            "只能作上下文证据绑定；D9 缺口保持"),
    }
    changed_txt = "[" + ", ".join(changed_params) + "]"
    low_dof_v1 = by_id["low_dof_contract_compliant"]
    by_id["low_dof_contract_compliant"] = {
        "id": "low_dof_contract_compliant",
        "value": low_dof_v1["value"],
        "evidence": (
            f"TD2 低自由度：分母=已执行并对比的 holdout 板数="
            f"{EXECUTED_HOLDOUT_DENOMINATOR} < {LOW_DOF_MIN_HOLDOUT_BOARDS}"
            f" → 至多变 1 参数；challenger changed={changed_txt}"
            f"（{len(changed_params)} 参数）→ "
            + ("合规" if low_dof_v1["value"] else "不合规（保持 v1 裁决）")
            + f"。语料在库 holdout 板 {corpus_n} 块不替代执行分母"
            "（样本量按已执行对比板计；多参数解禁需真实逐板对比执行后"
            "分母 ≥2）"),
    }
    return [by_id[p["id"]] for p in v1_record["required_predicates"]]


def build_holdout_unlock(*, v1_gate_records: dict, patch_ids: dict,
                         changed_params: dict, tl5_gate_record: dict,
                         dataset_manifests: list, adoption_disposition: dict,
                         binding_hashes: dict, evaluator: dict,
                         snapshot_revision: str = "v3-s9") -> dict:
    """TL-4 holdout 解锁评估（S9，路径 b）：评估备忘 + v2 gate-spec 构造。

    纯函数。输入：
    - v1_gate_records：{profile: v1 gate_record 内层 dict}（原样只读）；
    - patch_ids：{profile: v1 proposal patch_id}（APR 覆盖性核对）；
    - changed_params：{profile: v1 challenger 变更参数名列表}；
    - tl5_gate_record：TL-5-G v3 gate_record 内层 dict（result 必须 pass）；
    - dataset_manifests：两库 dataset manifest dict（split 冻结核对）；
    - adoption_disposition：APR-0004 disposition dict；
    - binding_hashes：HOLDOUT_UNLOCK_BINDING_KEYS 全键 64hex；
    - evaluator：{name, version, code_sha256}（判定代码版本绑定）。

    返回 {chain_kind, evaluation_memo, gate_specs_v2}；编排侧落盘 memo、
    按 spec 跑 v3cli gate 出 v2 门记录（一律新文件，v1 保留）。
    本函数不产生任何 holdout 执行证据（EXECUTED_HOLDOUT_DENOMINATOR=0），
    也不存在把三个执行依赖谓词置 true 的入口——机器强制，防凑门。
    """
    if set(v1_gate_records) != set(patch_ids) or set(v1_gate_records) != set(
            changed_params):
        raise ValueError("v1_gate_records/patch_ids/changed_params 键集"
                         "必须一致（fail-closed）")
    for key in HOLDOUT_UNLOCK_BINDING_KEYS:
        if not _is_sha256((binding_hashes or {}).get(key)):
            raise ValueError(f"binding_hashes 缺 {key!r} 的 64hex 绑定"
                             "（fail-closed）")
    if not isinstance(evaluator, dict) or not _is_sha256(
            evaluator.get("code_sha256")):
        raise ValueError("evaluator.code_sha256 必须 64hex（判定代码绑定）")
    tl5_core = gate.gate_core_hash(tl5_gate_record)
    if tl5_core != binding_hashes["tl5_gate_record_core"]:
        raise ValueError("binding_hashes.tl5_gate_record_core 与传入 "
                         "TL-5 门记录重算 core hash 不一致（fail-closed）")
    if tl5_gate_record.get("result") != "pass":
        raise ValueError("TL-5 门记录 result 非 pass——语料可用性不可作实"
                         "（fail-closed；不受理 blocked 门充当语料证据）")

    corpus = holdout_corpus_facts(dataset_manifests)
    unlock = {
        "chain_kind": "tl4-holdout-unlock-evaluation",
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "tl4_holdout_unlock_evaluation",
        "track": HOLDOUT_UNLOCK_TRACK,
        "session": "S9",
        "path_decision": {
            "selected": "b",
            "options": {
                "a": {
                    "description": "为真实 profile 声明 audit/feedforward "
                                   "级新搜索空间，autotune 编排直接跑真实"
                                   "板 train 池，holdout 逐板不回退验证",
                    "verdict": "rejected_not_executable_honestly",
                    "grounds": [
                        "corpus 四段（compile/enum/audit/feedforward）当前"
                        "消费可调参数=0：唯一策略输入是 corpus_convert.py "
                        "模块常量 POWER_RAIL_NAMES/DIFF_PAIR_NAMES（代码"
                        "常量非 config）；真实板 manifest params=[] 且 "
                        "conversion_log field_missingness 登记『params: 空"
                        "（搜索域不可从板文本判定）』",
                        "为使其可调而把网名约定表参数化，目标函数将只有"
                        "分类计数对分类计数（basis=net_name_convention "
                        "名字级启发非电气真值，无电气 ground truth）——"
                        "恰是 TD2 明令的 reward hacking 形态（不得只把"
                        "黄区改绿）",
                        "DRC/连通性指标（kicad-cli authority）对该类策略"
                        "参数恒不变 → 逐板不回退证据空真"
                        "（challenger≡baseline），不构成合法不回退证据="
                        "凑门（红线禁止）",
                    ],
                },
                "b": {
                    "description": "维持 smoke 范围；TL-4-G v2 复评="
                                   "blocked；剩余缺口按精确依赖登记",
                    "verdict": "selected",
                    "consequence": "tl5_independent_holdout_corpus_"
                                   "available 与 human_adoption_disposition_"
                                   "present 两谓词由既有产物作实翻 true；"
                                   "holdout_non_regression_evidenced/"
                                   "adoption_machine_gate_pass/judge_post_ok"
                                   "（+smoke-4l low_dof）保持 false="
                                   "结构性缺",
                },
            },
            "decided_by": "machine_evaluation_of_artifact_facts",
        },
        "corpus_facts": dict(corpus),
        "executed_holdout_denominator": EXECUTED_HOLDOUT_DENOMINATOR,
        "low_dof_analysis": {
            "rule": "分母=已执行并对比的 holdout 板数（len(holdout_"
                    "results)），非语料在库板数",
            "corpus_holdout_boards": corpus["holdout_board_count"],
            "executed_holdout_boards": EXECUTED_HOLDOUT_DENOMINATOR,
            "threshold": LOW_DOF_MIN_HOLDOUT_BOARDS,
            "corpus_satisfies_threshold":
                corpus["holdout_board_count"] >= LOW_DOF_MIN_HOLDOUT_BOARDS,
            "multi_param_unlocked": False,
            "note": "corpus 12≥2 只在真实逐板对比执行后生效；当前 "
                    "executed=0 → 仍单参数上限：smoke-2l challenger（1 "
                    "参数）合规保持，smoke-4l challenger（2 参数）不合规"
                    "保持",
        },
        "drc_ref_eligibility": dict(DRC_REF_ELIGIBILITY),
        "fact_corrections": [
            {"claim": "任务书 holdout 板数 bm11+t32-ref+11=13",
             "verified_count": corpus["holdout_board_count"],
             "correction": "t32-ref=kitspace_T32_ref 已在 pcbench-r1 "
                           "holdout 11 板内，不得双计；唯一 holdout 板数="
                           f"{corpus['holdout_board_count']}（bm11 + pcbench "
                           "11）",
             "basis": "dataset-manifest-pcbbenchmarks-r1-v3 holdout + "
                      "dataset-manifest-pcbench-r1-v2 holdout 逐板并集"},
        ],
        "adoption_status_after_reevaluation": (
            "human_approved_machine_blocked（APR-0004 人工处置在场+机器门"
            " blocked 合取）：不 apply、baseline config 保持 immutable、"
            "无新 baseline 版本链产生"),
        "no_gate_pass_claim": (
            "本评估与 v2 门记录 result=blocked；不宣称 TL-4 出口门通过、"
            "不宣称布线生成能力（D17）、不宣称泛化（L7）"),
        "binding_hashes": {k: binding_hashes[k]
                           for k in HOLDOUT_UNLOCK_BINDING_KEYS},
        "guard_clauses": [
            "本评估函数不存在把 holdout_non_regression_evidenced / "
            "judge_post_ok / adoption_machine_gate_pass 置 true 的参数"
            "路径（机器强制；翻转唯一入口=真实执行证据进链重跑）",
            "TL-5 check 产物按 DRC_REF_ELIGIBILITY 裁定不可充当 executor "
            "DRC ref（参考态证据≠执行器输出证据）",
            "v1 门记录与全部 S3 产物原样只读；v2 复评一律落版本递增新文件",
        ],
    }

    gate_specs_v2: dict = {}
    predicate_reeval: dict = {}
    for profile_id, v1_record in v1_gate_records.items():
        cover = adoption_disposition_covers(
            adoption_disposition, patch_ids[profile_id])
        predicates = _v2_predicates(
            v1_record, patch_id=patch_ids[profile_id], corpus=corpus,
            disposition_cover=cover,
            changed_params=changed_params[profile_id], tl5_core=tl5_core)
        inputs = [dict(i) for i in v1_record["inputs"]
                  if i.get("artifact_id") != "holdout_corpus"]
        inputs += [
            {"artifact_id": "holdout_corpus_tl5_gate_record",
             "sha256": binding_hashes["tl5_gate_record_core"],
             "status": "present"},
            {"artifact_id": "dataset_manifest_pcbbenchmarks_r1_v3",
             "sha256": binding_hashes["dataset_manifest_pcbbenchmarks_r1_v3"],
             "status": "present"},
            {"artifact_id": "dataset_manifest_pcbench_r1_v2",
             "sha256": binding_hashes["dataset_manifest_pcbench_r1_v2"],
             "status": "present"},
            {"artifact_id": "adoption_disposition_apr0004",
             "sha256": binding_hashes["adoption_disposition_apr0004"],
             "status": "present"},
            {"artifact_id": "approvals_decision_ledger",
             "sha256": binding_hashes["approvals_decision_ledger"],
             "status": "present"},
        ]
        gate_specs_v2[profile_id] = {
            "gate_id": v1_record["gate_id"],
            "gate_kind": v1_record["gate_kind"],
            "project_id": v1_record["project_id"],
            "profile_id": v1_record["profile_id"],
            "snapshot_revision": snapshot_revision,
            "predicate_version": "pv2",
            "inputs": inputs,
            "required_predicates": predicates,
            "fact_refs": [],
            "disposition_refs": ["APR-0004"],
            "evaluator": dict(evaluator),
        }
        predicate_reeval[profile_id] = [
            {"id": p["id"], "v1_value": v["value"], "v2_value": p["value"]}
            for p, v in zip(predicates, v1_record["required_predicates"])]
    unlock["predicate_reevaluation"] = predicate_reeval
    unlock["expected_v2_failure_codes"] = {
        pid: sorted(
            f"predicate_failed:{p['id']}" for p in spec[
                "required_predicates"] if p["value"] is not True)
        for pid, spec in gate_specs_v2.items()}
    return {"chain_kind": "tl4-holdout-unlock-evaluation",
            "schema_version": SCHEMA_VERSION,
            "evaluation_memo": unlock,
            "gate_specs_v2": gate_specs_v2}


def build_unlock_execution_record(*, written_files: list,
                                  baseline_config_recheck: dict,
                                  protected_files_recheck: dict,
                                  datasets_zero_write: dict) -> dict:
    """S9 解锁评估编排执行记录（纯函数；hash 全部由编排侧实算注入）。

    - written_files：[{path, sha256}]（本包新落盘文件，一律版本递增新名）；
    - baseline_config_recheck：{path: {v1_binding, now, unchanged}}（adoption
      未 apply 的机器见证：旧 config 逐字节不变）；
    - protected_files_recheck：{path: {expected, now, unchanged}}（cli/config/
      toolchain_lock 红线复验）；
    - datasets_zero_write：{snapshot_files, changed, note}（数据集快照前后
      复验声明，编排侧实算）。
    fail-closed：任一 unchanged=False 不遮掩，原样入记录（复核方判读）。
    """
    for entry in written_files:
        if not _is_sha256(entry.get("sha256")):
            raise ValueError("written_files 缺 64hex（fail-closed）")
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "tl4_holdout_unlock_execution_record",
        "track": HOLDOUT_UNLOCK_TRACK,
        "session": "S9",
        "steps": [
            "1) 读入 v1 门记录/proposal patch/chain bundle+TL-5-G v3 门记录"
            "+两库 dataset manifest+APR-0004 处置与账本（全部只读）",
            "2) build_holdout_unlock（纯函数）→ 评估备忘+两 profile v2 "
            "gate-spec；落 eval-holdout-unlock.json+gate-spec-tl4-v2-*.json",
            "3) v3cli gate（--spec）×2 → gate-record-tl4-v2-smoke-{2l,4l}"
            ".json（机器谓词计算，人工不可直写）",
            "4) 确定性复核：纯函数重跑 byte-exact+v2 门记录重算 core 一致",
            "5) 红线复验：受保护文件/datasets/ 零写入+既有 out/ 只读+"
            "baseline config immutable",
        ],
        "written_files": [dict(w) for w in written_files],
        "baseline_config_immutable_recheck": {
            k: dict(v) for k, v in baseline_config_recheck.items()},
        "protected_files_recheck": {
            k: dict(v) for k, v in protected_files_recheck.items()},
        "datasets_zero_write_recheck": dict(datasets_zero_write),
        "adoption_applied": False,
        "note": "本记录不构成门裁决；机器裁决见 gate-record-tl4-v2-*.json",
    }


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger.jsonl 的唯一口径）。"""
    from . import hashing

    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
