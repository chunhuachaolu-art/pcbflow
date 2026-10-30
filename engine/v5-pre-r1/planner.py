# -*- coding: utf-8 -*-
"""L5② 引擎默认规划器（V5.0-DEV-TASKBOOK §4 L5、A10：注册表编译规则的确定性执行器）。

入口 plan_candidates(board, compiled_artifact, arm="principle") → 候选列表（纯函数，
无随机无时间戳，同输入双跑 canonical 字节相等）。候选形状=selection 消费合同（逐字）：

    {"candidate_id": "C-001"（按生成序连续编号）,
     "arm": "principle" | "no-principle",
     "provenance": {"generator": "v5.planner/0.1.0",
                    "rules_consumed": [principle_id 排序],
                    "compiled_sha256": <compiled_artifact 的 canonical sha256>},
     "route_order": [分区 id 全列表],
     "layer_assignment": {分区 id: 层 id},
     "polylines": {分区 id: [[x,y],[x,y]]},      # P3 范围=端点直线（P4 执行器再细化）
     "generation_trace": [{"rule": principle_id,
                           "freedom": "ordering|allocation|layer_plan|corridor",
                           "effect": "一句话"}]}

四自由度（A10 语义；规则处理序：layer_plan → corridor → ordering → allocation，
同阶段规则按 (-priority, principle_id) 确定性排序）：

1. ordering：默认键 = (ptype 阶梯, partition_id)，阶梯 CLK>HS>BUS>PWR>MISC 与
   v5.pkg.ROUTING_LADDER 一致；阶梯未列的 ptype（DIFF/ANA/ROUTED）归入末档
   （低速杂项兜底，文档化决定）。ordering 规则改写键序，动作按 kind 二分：
   - 默认动作=前移提升：scope 命中的分区升至队首（键类 0；语义=保护/需提前承诺的
     分区先注册，如既有铜保护——既布铜几何固定，先注册后继者避让）；
   - kind=="short_run" 且 params.prefer=="min_length"：命中分区在同类同档内按端点
     直线长度升序前移（键 (0, 长度)，未命中者键 (1, 0)）——引擎自算几何事实的
     序数使用，不违 A1。
   多条 ordering 规则命中同一分区=并集提升（类 0），效果各自留痕。
2. layer_plan：每分区 layer_policy 展开为合法层集合（对照 stackup：仅 kind=="signal"
   且 available==true 的层；policy=="any" → 全部信号层按 stackup 序；展开为空集 =
   板数据矛盾，fail-closed PlannerError）。layer_plan 规则按 priority 施加偏好排序：
   params.layer（单层 id）在命中分区的偏好序中稳定前置；params.ptypes（可选）扩大
   命中集；偏好层不在合法集/已在首位=无变化，如实留痕。
3. corridor：走廊 zone（kind=="corridor"）几何命中的分区（命中判据与 L2
   envelope_plan 同口径：端点包围盒与走廊矩形 gap≤1e-9，或 copper_band x 跨与走廊
   x 跨有交且 y 跨有交）。corridor 规则影响过廊分区的顺序偏好：命中分区在所属
   ptype 档内前移（键类 1，低于 ordering 提升的类 0，高于普通分区类 2；语义=
   routing_ladder「同档位先占用稀缺资源（走廊）者在前」）。规则作用域 reach：
   scope 命中的走廊 zone → 其几何穿越分区；scope 只命中分区 → 该集合与全板走廊
   穿越者求交。过廊层偏好仅在 params 具名层（layer/layers）时重排——现存规则均未
   具名层，effect 如实披露（泛化为容量感知选层属测量环职权，本版不做）。
4. allocation：本阶段=分区→层指派组合的确定性枚举。组合键 = partition_id 字典序
   排列的层 id 元组；枚举序 = 各位置按该分区「偏好序层表」（经 layer_plan/corridor
   重排后）的字典序（itertools.product，右位先变）。**组合截断披露（工程边界，
   文档化）**：每板每臂最多保留前 24 个组合（MAX_COMBINATIONS，按组合键字典序
   截断）；U8 的「不设限」针对 L6 测量终选，候选生成的组合学截断是生成侧工程
   边界，此处如实披露。allocation 规则本阶段无可施加的层指派约束（其作用点在
   宽度/成对/执行器几何侧），按条留痕如实披露（不伪造效果）。

双臂（P5-G4 三臂对账基础）：arm="no-principle"（诊断臂）忽略全部编译规则——纯
阶梯+partition_id 字典序+层集合 stackup 序首元素（走廊前移亦属规则驱动，诊断臂
关闭，以最大化 ①vs② 的理念增益对照口径）；generation_trace=[]、rules_consumed=[]。
两臂可同板运行。

生成留痕硬要求：arm="principle" 时 compiled_artifact["rules"] 的每条 rule（即每条
generator_target 命中的编译规则）必须出现在 generation_trace；scope 零命中的规则
留痕 effect="scope 零命中"。出口自断言（覆盖率 100% 的管线 bug 守卫）。
rules_consumed = generation_trace 中出现的 principle_id 去重排序（含零命中留痕条目
——被生成器评估过即消费）。

文档化最小决定（偏离披露）：
1. 本模块不重复 load_board 全量校验（上游 L0 已 fail-closed）；只对消费字段做
   键路径化 fail-closed 检查，并交叉核对 artifact.board_sha256 与板 provenance
   （双方齐备且不等 → PlannerError，防错板错工件配对）。
2. 逐候选出口自检 validate_candidate（含于生成，防御性管线守卫）。
3. 截断披露落在本 docstring + MAX_COMBINATIONS 常量 + 专项测试；候选载荷形状由
   selection 合同逐字冻结，不加额外披露键。
"""
import itertools
import math
import re

from . import canonical
from .compiler import resolve_scope
from .metrics import clearance

PLANNER_VERSION = "v5.planner/0.1.0"
ARTIFACT_VERSION = "v5.compiled_rules.v1"
# 组合截断上限（每板每臂；见模块 docstring「组合截断披露」）
MAX_COMBINATIONS = 24
_EPS = 1e-9
# ptype 阶梯（与 v5.pkg.ROUTING_LADDER 一致）；未列 ptype 归入末档（文档化）
LADDER_RANKS = {"CLK": 0, "HS": 1, "BUS": 2, "PWR": 3, "MISC": 4}
UNLISTED_RANK = 4
_FREEDOMS = ("ordering", "allocation", "layer_plan", "corridor")
_TRACE_STAGES = ("layer_plan", "corridor", "ordering", "allocation")
_CANDIDATE_ID_RE = re.compile(r"^C-\d{3}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_POLICY_SPLIT_RE = re.compile(r"[,，;；]")


class PlannerError(ValueError):
    """规划器 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise PlannerError(path, msg)


# ---------------------------------------------------------------- 板/工件轻检

def _signal_layer_ids(board):
    """stackup 中可用信号层 id 列表（保持 stackup 序）。"""
    return [str(layer["id"]) for layer in board.get("stackup", [])
            if layer.get("kind") == "signal" and layer.get("available") is True]


def _expand_policy(partition, signal_ids, path):
    """layer_policy → 合法层偏好序（stackup 序为基）；"any" → 全部信号层。"""
    policy = str(partition.get("layer_policy", ""))
    tokens = [t.strip() for t in _POLICY_SPLIT_RE.split(policy) if t.strip()]
    if "any" in tokens or not tokens:
        layers = list(signal_ids)
    else:
        layers = [t for t in tokens if t in signal_ids]
    _require(layers, path,
             "layer_policy %r 展开为空合法层集（仅命名 plane/不可用层）=板数据矛盾"
             % policy)
    return layers


def _check_board_shape(board):
    """消费字段轻检（不重复 load_board；见 docstring 决定 1）。"""
    _require(isinstance(board, dict), "board", "须为 dict")
    parts = board.get("partitions")
    _require(isinstance(parts, list) and parts, "board.partitions",
             "分区表缺失或为空")
    seen = set()
    for i, part in enumerate(parts):
        pid = part.get("partition_id")
        _require(isinstance(pid, str) and pid, "board.partitions[%d].partition_id" % i,
                 "分区 id 缺失或非字符串")
        _require(pid not in seen, "board.partitions[%d].partition_id" % i,
                 "分区 id 重复: %r" % pid)
        seen.add(pid)
        eps = part.get("geometry", {}).get("endpoints")
        _require(isinstance(eps, list) and len(eps) == 2
                 and all(isinstance(pt, (list, tuple)) and len(pt) == 2
                         and all(isinstance(n, (int, float)) and not isinstance(n, bool)
                                 for n in pt)
                         for pt in eps),
                 "board.partitions[%d].geometry.endpoints" % i,
                 "端点须恰为 2 个 [x,y] 数值点")
    _require(isinstance(board.get("stackup"), list) and board["stackup"],
             "board.stackup", "叠层缺失或为空")


def _check_artifact(compiled_artifact):
    _require(isinstance(compiled_artifact, dict), "compiled_artifact", "须为 dict")
    _require(compiled_artifact.get("artifact") == ARTIFACT_VERSION,
             "compiled_artifact.artifact",
             "须为 %r，得到 %r" % (ARTIFACT_VERSION, compiled_artifact.get("artifact")))
    for rule in compiled_artifact.get("rules", []):
        _require(rule.get("generator_target") in _FREEDOMS,
                 "compiled_artifact.rules[%s].generator_target" % rule.get("principle_id"),
                 "自由度 %r 不在四自由度枚举内" % (rule.get("generator_target"),))


def _cross_check_artifact_board(board, compiled_artifact):
    """板↔工件指纹交叉核对（双方齐备且不等 → fail-closed，防错配对）。"""
    board_sha = (board.get("provenance") or {}).get("board_sha256")
    art_sha = compiled_artifact.get("board_sha256")
    if board_sha is not None and art_sha is not None and board_sha != art_sha:
        raise PlannerError(
            "compiled_artifact.board_sha256",
            "与板 provenance.board_sha256 不匹配（%s != %s）：工件与板错配对"
            % (art_sha, board_sha))


# ---------------------------------------------------------------- 几何辅助

def _partition_bbox(partition):
    """端点包围盒 (x0, y0, x1, y1)（升序）。"""
    xs = sorted(pt[0] for pt in partition["geometry"]["endpoints"])
    ys = sorted(pt[1] for pt in partition["geometry"]["endpoints"])
    return (xs[0], ys[0], xs[-1], ys[-1])


def _hits_rect(partition, rect):
    """分区是否几何命中矩形（与 L2 envelope_plan 走廊命中同口径，见 docstring 3）。"""
    bbox = _partition_bbox(partition)
    if clearance.rect_rect_gap(bbox, rect) <= _EPS:
        return True
    band = partition["geometry"].get("copper_band")
    if band is None:
        return False
    band_overlap = max(band[0], rect[0]) <= min(band[1], rect[2]) + _EPS
    ys_overlap = max(bbox[1], rect[1]) <= min(bbox[3], rect[3]) + _EPS
    return band_overlap and ys_overlap


def _corridor_crossers(board):
    """{partition_id: 命中的走廊 zone_id 排序列表}（仅 kind=="corridor" 的 zone）。"""
    corridors = [(z["zone_id"],
                  (z["rect"]["x_min"], z["rect"]["y_min"],
                   z["rect"]["x_max"], z["rect"]["y_max"]))
                 for z in board.get("zones", []) if z.get("kind") == "corridor"]
    crossers = {}
    for part in board["partitions"]:
        hit = sorted(zid for zid, rect in corridors if _hits_rect(part, rect))
        if hit:
            crossers[part["partition_id"]] = hit
    return crossers, sorted(zid for zid, _ in corridors)


def _straight_length(partition):
    """端点直线距离（欧氏；round 10 与 v5.measure 同口径）。"""
    (x1, y1), (x2, y2) = partition["geometry"]["endpoints"]
    return round(math.hypot(x2 - x1, y2 - y1), 10)


# ---------------------------------------------------------------- 规则效用

def _stage_rules(rules, freedom):
    """同自由度规则按 (-priority, principle_id) 确定性排序。"""
    picked = [r for r in rules if r.get("generator_target") == freedom]
    return sorted(picked, key=lambda r: (-r["priority"], r["principle_id"]))


def _rule_params(rule):
    params = rule.get("predicate", {}).get("params")
    return params if isinstance(params, dict) else {}


def _scope_of(scopes, rule):
    """规则的 scope 解析结果（resolve_scope 产物）；缺失视作零命中。"""
    res = scopes.get(rule.get("principle_id"))
    if res is None:
        return {"raw": "", "partitions": [], "zones": [], "nets": [],
                "warnings": ["scope 解析缺失"]}
    return res


def _apply_layer_plan_rules(rules, scopes, parts, pids, pref, trace):
    """layer_plan 阶段：params.layer 在命中分区偏好序中稳定前置；params.ptypes 扩大命中集。"""
    for rule in _stage_rules(rules, "layer_plan"):
        res = _scope_of(scopes, rule)
        params = _rule_params(rule)
        affected = list(res["partitions"])
        for pid in pids:
            if parts[pid].get("ptype") in (params.get("ptypes") or []) \
                    and pid not in affected:
                affected.append(pid)
        affected.sort()
        if res["warnings"]:
            effect = "scope 零命中"
        elif not params.get("layer"):
            effect = ("命中 %d 个分区: [%s]，规则未指定偏好层，层序保持"
                      % (len(affected), ", ".join(affected)))
        else:
            layer = str(params["layer"])
            changed = []
            for pid in affected:
                if layer in pref[pid] and pref[pid][0] != layer:
                    pref[pid] = [layer] + [x for x in pref[pid] if x != layer]
                    changed.append(pid)
            if changed:
                effect = ("层偏好重排 %d 个分区: [%s] 偏好层 [%s] 前置"
                          % (len(changed), ", ".join(changed), layer))
            else:
                effect = ("命中 %d 个分区但偏好层 [%s] 已在首位或不在合法层集，层序保持"
                          % (len(affected), layer))
        trace.append({"rule": rule["principle_id"], "freedom": "layer_plan",
                      "effect": effect})


def _corridor_reach(rule, res, crossers, corridor_ids):
    """corridor 规则的 (受影响分区, 涉及走廊 zone 列表)。语义见模块 docstring 3。"""
    zids = [z for z in res["zones"] if z in corridor_ids]
    if zids:
        zset = set(zids)
        affected = sorted(p for p, zs in crossers.items() if zset & set(zs))
        return affected, zids
    if res["partitions"]:
        affected = sorted(p for p in res["partitions"] if crossers.get(p))
        involved = sorted({z for p in affected for z in crossers[p]})
        return affected, involved
    return [], []


def _apply_corridor_rules(rules, scopes, crossers, corridor_ids, trace,
                          corridor_elevated):
    """corridor 阶段：过廊分区在所属 ptype 档内前移（键类 1）。"""
    for rule in _stage_rules(rules, "corridor"):
        res = _scope_of(scopes, rule)
        affected, zids = _corridor_reach(rule, res, crossers, corridor_ids)
        params = _rule_params(rule)
        named_layers = ([str(params["layer"])] if params.get("layer")
                        else [str(x) for x in (params.get("layers") or [])])
        if res["warnings"]:
            effect = "scope 零命中"
        elif not affected:
            if zids or res["partitions"]:
                effect = "命中走廊对象但无分区几何穿越，排序无增量"
            else:
                effect = "scope 未命中走廊对象，排序无增量"
        else:
            corridor_elevated.update(affected)
            effect = ("过廊分区同档位排序前移 %d 个: [%s]（走廊 [%s] 稀缺资源先行）"
                      % (len(affected), ", ".join(affected), ", ".join(zids)))
            if named_layers:
                effect += "；过廊层偏好具名 [%s]（本阶段仅披露，选层属测量环）" \
                          % ", ".join(named_layers)
        trace.append({"rule": rule["principle_id"], "freedom": "corridor",
                      "effect": effect})


def _apply_ordering_rules(rules, scopes, pids, trace, ordering_elevated,
                          short_run_hits):
    """ordering 阶段：默认=scope 命中分区前移提升（类 0）；short_run=同档长度升序前移。"""
    for rule in _stage_rules(rules, "ordering"):
        res = _scope_of(scopes, rule)
        params = _rule_params(rule)
        kind = rule.get("predicate", {}).get("rule_kind")
        hits = list(res["partitions"])
        if res["warnings"]:
            effect = "scope 零命中"
        elif not hits:
            effect = "scope 未命中分区，键序保持"
        elif kind == "short_run" and params.get("prefer") == "min_length":
            short_run_hits.update(hits)
            effect = ("短线偏好: 分区 [%s] 同档内按端点直线长度升序前移"
                      % ", ".join(hits))
        else:
            ordering_elevated.update(hits)
            if len(hits) == len(pids):
                effect = "命中全部分区，键序无增量变化"
            else:
                effect = ("排序前移 %d 个分区: [%s]（命中分区升至队首）"
                          % (len(hits), ", ".join(hits)))
        trace.append({"rule": rule["principle_id"], "freedom": "ordering",
                      "effect": effect})


def _apply_allocation_rules(rules, scopes, total, truncated, trace):
    """allocation 阶段：枚举本身即本阶段自由度；规则无可施加的层指派约束，如实披露。"""
    for rule in _stage_rules(rules, "allocation"):
        res = _scope_of(scopes, rule)
        kind = rule.get("predicate", {}).get("rule_kind")
        if res["warnings"]:
            effect = "scope 零命中"
        else:
            effect = ("分配自由度=层指派组合枚举: 全板 %d 组合%s；%s 本阶段无可施加的"
                      "层指派约束（作用点在宽度/成对/执行器侧），如实披露"
                      % (total,
                         "，截断保留前 %d（组合键字典序）" % MAX_COMBINATIONS
                         if truncated else "（未截断）",
                         kind))
        trace.append({"rule": rule["principle_id"], "freedom": "allocation",
                      "effect": effect})


# ---------------------------------------------------------------- 生成入口

def plan_candidates(board, compiled_artifact, arm="principle"):
    """引擎默认规划器入口（纯函数）：board + 编译工件 → 候选列表。

    arm="principle"（主路径，A10）：四自由度全部由编译规则驱动，全规则留痕。
    arm="no-principle"（诊断臂）：忽略全部编译规则（纯阶梯+字典序+层集合首元素），
    generation_trace=[]、rules_consumed=[]。两臂可同板运行（P5-G4 对账基础）。
    """
    _require(arm in ("principle", "no-principle"), "arm",
             "须为 'principle' 或 'no-principle'，得到 %r" % (arm,))
    _check_artifact(compiled_artifact)
    _check_board_shape(board)
    _cross_check_artifact_board(board, compiled_artifact)

    parts = {p["partition_id"]: p for p in board["partitions"]}
    pids = sorted(parts)
    signal_ids = _signal_layer_ids(board)
    _require(signal_ids, "board.stackup", "无可用信号层（kind==signal 且 available）")
    pref = {pid: _expand_policy(parts[pid], signal_ids,
                                "board.partitions[%s].layer_policy" % pid)
            for pid in pids}

    rules = list(compiled_artifact.get("rules", []))
    trace = []
    # 排序键元数据：cls（0=ordering 提升 / 1=走廊同档前移 / 2=普通）、len_key（short_run）
    order_meta = {pid: {"cls": 2, "len_key": (1, 0.0)} for pid in pids}

    if arm == "principle":
        scopes = resolve_scope(board.get("principle_registry") or [], board)
        crossers, corridor_ids = _corridor_crossers(board)
        ordering_elevated, corridor_elevated, short_run_hits = set(), set(), set()

        _apply_layer_plan_rules(rules, scopes, parts, pids, pref, trace)
        _apply_corridor_rules(rules, scopes, crossers, corridor_ids, trace,
                              corridor_elevated)
        _apply_ordering_rules(rules, scopes, pids, trace, ordering_elevated,
                              short_run_hits)
        for pid in ordering_elevated:
            order_meta[pid]["cls"] = 0
        for pid in corridor_elevated - ordering_elevated:
            order_meta[pid]["cls"] = 1
        for pid in short_run_hits:
            order_meta[pid]["len_key"] = (0, _straight_length(parts[pid]))

    def _order_key(pid):
        rank = LADDER_RANKS.get(str(parts[pid].get("ptype")), UNLISTED_RANK)
        return (order_meta[pid]["cls"], rank, order_meta[pid]["len_key"], pid)

    route_order = sorted(pids, key=_order_key)

    # allocation：组合枚举（组合键=partition_id 字典序的层元组；各位置按偏好序字母表）
    total = 1
    for pid in pids:
        total *= len(pref[pid])
    truncated = total > MAX_COMBINATIONS
    combos = list(itertools.islice(itertools.product(*[pref[p] for p in pids]),
                                   MAX_COMBINATIONS))

    if arm == "principle":
        _apply_allocation_rules(rules, scopes, total, truncated, trace)
        # 覆盖率 100% 管线 bug 守卫：每条编译规则必须已留痕（含 scope 零命中）
        traced = {t["rule"] for t in trace}
        missing = sorted({r["principle_id"] for r in rules} - traced)
        _require(not missing, "generation_trace",
                 "生成侧消费覆盖率失守：规则 %s 未留痕（管线 bug）" % missing)

    compiled_sha = canonical.canonical_sha256(compiled_artifact)
    rules_consumed = sorted({t["rule"] for t in trace})
    candidates = []
    for idx, combo in enumerate(combos):
        endpoints = {pid: [list(parts[pid]["geometry"]["endpoints"][0]),
                           list(parts[pid]["geometry"]["endpoints"][1])]
                     for pid in pids}
        candidate = {
            "candidate_id": "C-%03d" % (idx + 1),
            "arm": arm,
            "provenance": {"generator": PLANNER_VERSION,
                           "rules_consumed": list(rules_consumed),
                           "compiled_sha256": compiled_sha},
            "route_order": list(route_order),
            "layer_assignment": dict(zip(pids, combo)),
            "polylines": endpoints,
            "generation_trace": [dict(t) for t in trace],
        }
        validate_candidate(candidate, board)  # 逐候选合法性自查（防御性管线守卫）
        candidates.append(candidate)
    return candidates


# ---------------------------------------------------------------- 合法性自查

def validate_candidate(candidate, board):
    """候选合法性自查（fail-closed 报键路径）：层指派全在 stackup 可用信号层；
    route_order 恰为全部分区（无重无漏）；polylines 与层指派键一致且恰为该分区
    端点直线（P3 合同）；双臂留痕合同（no-principle 臂 trace/rules 必空）。
    通过则原样返回 candidate。"""
    _require(isinstance(candidate, dict), "candidate", "须为 dict")
    for key in ("candidate_id", "arm", "provenance", "route_order",
                "layer_assignment", "polylines", "generation_trace"):
        _require(key in candidate, "candidate", "缺少必填键 %s" % key)

    cid = candidate["candidate_id"]
    _require(isinstance(cid, str) and _CANDIDATE_ID_RE.match(cid),
             "candidate.candidate_id", "须形如 C-001（按生成序连续编号），得到 %r" % (cid,))
    arm = candidate["arm"]
    _require(arm in ("principle", "no-principle"), "candidate.arm",
             "须为 'principle' 或 'no-principle'，得到 %r" % (arm,))

    prov = candidate["provenance"]
    _require(isinstance(prov, dict), "candidate.provenance", "须为 dict")
    _require(isinstance(prov.get("generator"), str)
             and prov["generator"].startswith("v5.planner"),
             "candidate.provenance.generator", "须为 v5.planner 生成器标识")
    consumed = prov.get("rules_consumed")
    _require(isinstance(consumed, list)
             and all(isinstance(x, str) and x for x in consumed),
             "candidate.provenance.rules_consumed", "须为非空字符串数组（可为空表）")
    _require(isinstance(prov.get("compiled_sha256"), str)
             and _SHA256_RE.match(prov.get("compiled_sha256", "")),
             "candidate.provenance.compiled_sha256", "须为 64 位十六进制 sha256")

    parts = {p["partition_id"]: p for p in board.get("partitions", [])}
    order = candidate["route_order"]
    _require(isinstance(order, list) and all(isinstance(x, str) for x in order),
             "candidate.route_order", "须为分区 id 字符串数组")
    _require(len(order) == len(set(order)), "candidate.route_order", "含重复分区")
    _require(sorted(order) == sorted(parts), "candidate.route_order",
             "不恰为全部分区（缺 %s，多 %s）"
             % (sorted(set(parts) - set(order)), sorted(set(order) - set(parts))))

    signal_ids = set(_signal_layer_ids(board))
    assignment = candidate["layer_assignment"]
    _require(isinstance(assignment, dict), "candidate.layer_assignment", "须为 dict")
    _require(set(assignment) == set(parts), "candidate.layer_assignment",
             "键须恰为全部分区 id")
    for pid, layer in assignment.items():
        _require(layer in signal_ids, "candidate.layer_assignment[%s]" % pid,
                 "层 %r 不在 stackup 可用信号层 %s" % (layer, sorted(signal_ids)))

    polylines = candidate["polylines"]
    _require(isinstance(polylines, dict), "candidate.polylines", "须为 dict")
    _require(set(polylines) == set(assignment), "candidate.polylines",
             "键须与 layer_assignment 一致（层与折线配对）")
    for pid, poly in polylines.items():
        ok_shape = (isinstance(poly, list) and len(poly) == 2
                    and all(isinstance(pt, (list, tuple)) and len(pt) == 2
                            and all(isinstance(n, (int, float))
                                    and not isinstance(n, bool) for n in pt)
                            for pt in poly))
        _require(ok_shape, "candidate.polylines[%s]" % pid,
                 "P3 合同=恰为 2 个 [x,y] 数值点的端点直线")
        expected = [list(pt) for pt in parts[pid]["geometry"]["endpoints"]]
        _require([list(pt) for pt in poly] == expected,
                 "candidate.polylines[%s]" % pid,
                 "与分区端点直线不符（期望 %s，得到 %s）" % (expected, poly))

    trace = candidate["generation_trace"]
    _require(isinstance(trace, list), "candidate.generation_trace", "须为数组")
    for i, entry in enumerate(trace):
        _require(isinstance(entry, dict)
                 and {"rule", "freedom", "effect"} <= set(entry),
                 "candidate.generation_trace[%d]" % i,
                 "须含 rule/freedom/effect 三键")
        _require(isinstance(entry.get("rule"), str) and entry["rule"],
                 "candidate.generation_trace[%d].rule" % i, "须为非空字符串")
        _require(entry.get("freedom") in _FREEDOMS,
                 "candidate.generation_trace[%d].freedom" % i,
                 "须在四自由度枚举内")
        _require(isinstance(entry.get("effect"), str) and entry["effect"],
                 "candidate.generation_trace[%d].effect" % i, "须为非空一句话")
    if arm == "no-principle":
        _require(trace == [] and consumed == [],
                 "candidate.generation_trace",
                 "诊断臂合同：generation_trace 与 rules_consumed 必须为空")
    return candidate
