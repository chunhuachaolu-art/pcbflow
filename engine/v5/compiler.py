# -*- coding: utf-8 -*-
"""L0.5 理念编译器（V5.0-DEV-TASKBOOK §3.8 编译协议，P1）。

管线（每步一个可独立测试的纯函数；注册表 = board["principle_registry"] 裸条目数组）：

    principle_registry → resolve_scope → build_conflict_graph
      → compile_rules → semantic_checks → coverage_report → 工件 v5.compiled_rules.v1

入口 compile_board(board)：board 先过 v5.board.load_board（fail-closed 校验 + 哈希链复算），
返回 (工件 dict, canonical 字节指纹)；工件在出口处自校验过
schemas/compiled_rules.v1.schema.json（schema_loader 的 glob 注册表自动收编该文件）。

七问义务中本编译器落地的合同（schema 管不到的语义层，全部 fail-closed）：
  1. 第 4 问（如何编译）：compiled_rule 为 object 必须含非空字符串键 "kind"；为 string 只允许
     "check_only"（进 check_only 披露列表）；其余一律 CompilerError——不可编译又不披露=违规。
  2. 第 5/6 问（与谁冲突/谁让位）：声明式冲突边 = conflicts_with ∪ yields_to，winner 预解析：
     priority 高者胜；yields_to 显式让位覆盖 priority 裁决；priority 相等时 principle_id
     字典序小者胜（确定性 tie-break，与声明方向无关、两侧对称）。
     引用不存在的 principle_id → CompilerError 带键路径；双向 yields_to（互相让位）无确定
     winner → CompilerError；自身冲突/自身让位 → CompilerError；principle_id 重复 → CompilerError。
  3. 理念地板：hard_or_soft=="hard" 而 overridable==true → CompilerError（hard 不可覆盖）。
  4. 篡改检测：source_hash != sha256(canonical(剔除 source_hash 后的条目)) → CompilerError。
  5. 第 7 问口径：evidence_refs 为空数组不报错，进 coverage.evidence_insufficient（依据不足披露）。
  6. 覆盖率 100% 门：compiled + check_only 必须 == total，否则 CompilerError（管线 bug 断言）；
     空注册表视为平凡覆盖（coverage_pct=100.0）。

scope 语法（确定性解析，大小写敏感，逗号分隔多值，token 去首尾空白）：
    "partitioning"    → 命中板全部分区；
    "partition:<id>"  → partition_id 精确命中该分区，并连带命中引用它的 net
                        （net.partitions 含该分区 id 的全部网）；<id> 不在板 partitions
                        里 → CompilerError（未知引用 fail-closed，与 board 载入器
                        nets→partitions 跨查同口径——这是直接对象引用，不同于下面
                        三种选择器的"零命中仅 warning"语义）；
    "zone:<zone_id>"  → 命中该 zone_id 的 zone；
    "ptype:<P>"       → 命中该 ptype 的全部分区（P ∈ board.v1 ptype 枚举，原样精确匹配）；
    "net_class:<x>"   → 命中该 net_class 的全部网。
    token 不属上述任何形态 → CompilerError（语法非法，fail-closed）；
    zone:/ptype:/net_class: 语法合法但分区/zone/net 合计零命中 → 记 warning 不报错
    （warnings 随解析结果返回）。

边界说明：P1 本模块只产 basis="declared" 的声明式边。P2 起新增七对冲突全枚举
（§5.1 理念冲突电池）：PAIR_TEMPLATES 固化七对模板（rule_kinds 以 7 块对抗板
adv-01..adv-07 实际 kind 为准），detect_principle_pairs 逐对检查注册表两侧命中并给
winner/loser/yield_scope 预案，build_full_conflict_graph 把声明边与模板命中对合并为
组合工件（basis="declared+template" 去重）。三者均为纯函数，不改变既有五步管线
与 coverage_report 语义，也不进 v1 工件 schema（组合工件由调用方按需直调获取）。
"""
import hashlib

from . import board as board_mod
from . import canonical, schema_loader

ARTIFACT_VERSION = "v5.compiled_rules.v1"

# scope token 允许的 "<kind>:" 前缀集合（"partitioning" 是无冒号裸 token）
_SCOPE_KINDS = ("zone", "ptype", "net_class", "partition")


class CompilerError(ValueError):
    """编译协议违例（fail-closed）；path 为注册表内的键路径。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


# ---------------------------------------------------------------- a. scope 解析

def resolve_scope(registry, board):
    """把每条 principle 的 scope 字符串确定性解析到具体对象（纯函数）。

    返回 {principle_id: {"raw", "partitions", "zones", "nets", "warnings"}}；
    三个命中列表均为去重排序的 id 列表；scope 整体零命中时 warnings 恰含一条（不报错）。
    """
    resolutions = {}
    for i, entry in enumerate(registry):
        pid = entry.get("principle_id", "<#%d>" % i)
        raw = entry.get("scope", "")
        partitions, zones, nets = set(), set(), set()
        for token in (t.strip() for t in raw.split(",")):
            if not token:
                continue  # 容忍空 token（如尾逗号）；空白 scope 由 schema minLength 拦截
            if token == "partitioning":
                partitions.update(p.get("partition_id") for p in board.get("partitions", []))
                continue
            kind, sep, value = token.partition(":")
            if not sep or not value or kind not in _SCOPE_KINDS:
                raise CompilerError(
                    "principle_registry[%d].scope" % i,
                    "scope token %r 语法非法（允许 partitioning / partition:<id> /"
                    " zone:<id> / ptype:<P> / net_class:<x>）" % token)
            if kind == "zone":
                zones.update(z.get("zone_id") for z in board.get("zones", [])
                             if z.get("zone_id") == value)
            elif kind == "ptype":
                partitions.update(p.get("partition_id") for p in board.get("partitions", [])
                                  if p.get("ptype") == value)
            elif kind == "partition":
                # 直接对象引用：未知分区 id fail-closed（区别于选择器形态的 warning）
                if not any(p.get("partition_id") == value
                           for p in board.get("partitions", [])):
                    raise CompilerError(
                        "principle_registry[%d].scope" % i,
                        "partition:<id> 引用不存在的分区 %r（未知引用 fail-closed）" % value)
                partitions.add(value)
                nets.update(n.get("net_id") for n in board.get("nets", [])
                            if value in n.get("partitions", []))
            else:  # net_class
                nets.update(n.get("net_id") for n in board.get("nets", [])
                            if n.get("net_class") == value)
        warnings = []
        if not partitions and not zones and not nets:
            warnings.append("scope %r 未命中任何分区/zone/net" % raw)
        resolutions[pid] = {
            "raw": raw,
            "partitions": sorted(partitions),
            "zones": sorted(zones),
            "nets": sorted(nets),
            "warnings": warnings,
        }
    return resolutions


# ---------------------------------------------------------------- b. 冲突图

def build_conflict_graph(registry):
    """声明式冲突图（纯函数）：nodes = principle_id 排序；edges = conflicts_with ∪ yields_to。

    边形如 {"a", "b"(端点字典序), "basis": "declared", "winner", "loser", "resolution"}：
      - resolution == "priority"：priority 高者胜（相等时 id 字典序小者胜，对称确定）；
      - resolution == "yields_to"：声明方显式让位，对方胜——覆盖 priority 裁决。
    边按 (a, b) 去重排序保证确定性；同一对端点的 yields_to 声明覆盖 priority 声明。
    """
    by_id = {}
    for i, entry in enumerate(registry):
        pid = entry.get("principle_id")
        if not isinstance(pid, str) or not pid:
            raise CompilerError("principle_registry[%d].principle_id" % i,
                                "principle_id 缺失或非字符串")
        if pid in by_id:
            raise CompilerError("principle_registry[%d].principle_id" % i,
                                "principle_id 重复: %r" % pid)
        by_id[pid] = entry

    def winner_by_priority(x, y):
        px = by_id[x].get("priority", 0)
        py = by_id[y].get("priority", 0)
        if px != py:
            return x if px > py else y
        return min(x, y)  # 确定性 tie-break：id 字典序小者胜（对称，与声明方向无关）

    edges = {}
    for i, entry in enumerate(registry):
        pid = entry["principle_id"]
        pol = entry.get("conflict_policy", {})
        for j, ref in enumerate(pol.get("conflicts_with", [])):
            path = "principle_registry[%d].conflict_policy.conflicts_with[%d]" % (i, j)
            if ref == pid:
                raise CompilerError(path, "自身冲突（self-loop）无意义")
            if ref not in by_id:
                raise CompilerError(path, "指向不存在的 principle_id %r（声明者 %r）" % (ref, pid))
            winner = winner_by_priority(pid, ref)
            pair = (min(pid, ref), max(pid, ref))
            old = edges.get(pair)
            if old is None or old["resolution"] != "yields_to":  # yields_to 优先，不被覆盖回
                edges[pair] = {"a": pair[0], "b": pair[1], "basis": "declared",
                               "winner": winner,
                               "loser": ref if winner == pid else pid,
                               "resolution": "priority"}
        for j, ref in enumerate(pol.get("yields_to", [])):
            path = "principle_registry[%d].conflict_policy.yields_to[%d]" % (i, j)
            if ref == pid:
                raise CompilerError(path, "自身让位（self-loop）无意义")
            if ref not in by_id:
                raise CompilerError(path, "指向不存在的 principle_id %r（声明者 %r）" % (ref, pid))
            winner = ref  # 声明方显式让位：对方（被让位者）胜
            pair = (min(pid, ref), max(pid, ref))
            old = edges.get(pair)
            if old is not None and old["resolution"] == "yields_to" and old["winner"] != winner:
                raise CompilerError(path, "互相 yields_to（%r 与 %r 双向让位），winner 无法确定"
                                    % (pid, ref))
            edges[pair] = {"a": pair[0], "b": pair[1], "basis": "declared",
                           "winner": winner, "loser": pid, "resolution": "yields_to"}
    return {"nodes": sorted(by_id), "edges": [edges[k] for k in sorted(edges)]}


# ---------------------------------------------------------------- c. 规则编译

def compile_rules(registry):
    """每条原则产 compiled rule 或 check_only 披露（纯函数）。

    返回 (rules, check_only)；两列表均按注册表声明序（确定性）。
    compiled_rule 为字符串时只允许 "check_only"；为 object 时必须含非空字符串键 "kind"，
    其余键原样并入 predicate；否则 CompilerError（不可编译又不披露=违规）。
    前置条件：条目已过 principle_registry.v1 schema（compile_board 路径由 load_board 保证）。
    """
    rules, check_only = [], []
    for i, entry in enumerate(registry):
        pid = entry["principle_id"]
        path = "principle_registry[%d].compiled_rule" % i
        cr = entry.get("compiled_rule")
        if isinstance(cr, str):
            if cr != "check_only":
                raise CompilerError(path, "字符串 compiled_rule 只允许 \"check_only\"，得到 %r"
                                    "（不可编译又不披露=违规）" % cr)
            check_only.append({"principle_id": pid, "reason": "explicit check_only"})
            continue
        if not isinstance(cr, dict):
            raise CompilerError(path, "compiled_rule 类型 %s 不合法（须为 object 或"
                                      " \"check_only\"）" % type(cr).__name__)
        kind = cr.get("kind")
        if not isinstance(kind, str) or not kind:
            raise CompilerError(path, "compiled_rule 对象必须含非空字符串键 \"kind\""
                                      "（不可编译又不披露=违规）")
        po = cr.get("proof_obligations", [])
        if not isinstance(po, list) or not all(isinstance(x, str) for x in po):
            raise CompilerError(path + ".proof_obligations", "proof_obligations 必须是字符串数组")
        pol = entry.get("conflict_policy", {})
        yt = list(pol.get("yields_to", []))
        if yt:
            fallback = "让位链: %s（按声明序显式让位；这些冲突的 winner=对方）" % ", ".join(yt)
        else:
            fallback = ("无显式让位；冲突按 priority=%d 高者胜（相等时 principle_id 字典序小者胜）"
                        % entry["priority"])
        rules.append({
            "compiled_rule_id": "%s#%s" % (pid, entry["version"]),
            "principle_id": pid,
            "generator_target": entry["target_freedom"],
            "predicate": dict({"rule_kind": kind},
                              **{k: v for k, v in cr.items() if k != "kind"}),
            "action": {"strategy": kind, "priority": entry["priority"]},
            "priority": entry["priority"],
            "conflicts_with": list(pol.get("conflicts_with", [])),
            "fallback": fallback,
            "proof_obligations": list(po),
            "enforcement": entry["enforcement"],
        })
    return rules, check_only


# ---------------------------------------------------------------- d. 七问语义校验

def semantic_checks(registry):
    """七问语义校验（schema 管不到的合同，fail-closed）。返回 evidence_insufficient 列表。

    - hard_or_soft=="hard" 而 overridable==true → CompilerError（理念地板不可覆盖）；
    - source_hash 不复算（sha256(canonical(剔除 source_hash 后的条目))) → CompilerError（篡改检测）；
    - evidence_refs 为空数组 → 不报错，principle_id 进返回列表（七问第 7 问「依据不足」口径）。
    """
    insufficient = []
    for i, entry in enumerate(registry):
        pid = entry.get("principle_id", "<#%d>" % i)
        if entry.get("hard_or_soft") == "hard" and entry.get("overridable") is True:
            raise CompilerError("principle_registry[%d].overridable" % i,
                                "hard 理念 %r 不可覆盖（overridable 必须为 false，理念地板）" % pid)
        view = {k: v for k, v in entry.items() if k != "source_hash"}
        recomputed = hashlib.sha256(canonical.canonical_json(view)).hexdigest()
        declared = entry.get("source_hash")
        if declared != recomputed:
            raise CompilerError("principle_registry[%d].source_hash" % i,
                                "source_hash 不复算（篡改检测）：声明 %s，重算 %s"
                                % (declared, recomputed))
        if entry.get("evidence_refs") == []:
            insufficient.append(pid)
    return insufficient


# ---------------------------------------------------------------- e. 覆盖率报告

def coverage_report(registry, rules, check_only, evidence_insufficient):
    """覆盖率报告 + 编译覆盖率 100% 门：compiled+check_only 必须 == total（管线 bug 则断言失败）。"""
    total = len(registry)
    n_compiled, n_check_only = len(rules), len(check_only)
    if n_compiled + n_check_only != total:
        raise CompilerError("coverage", "编译覆盖率 100%% 门失守：total=%d，compiled=%d，"
                                        "check_only=%d（管线 bug）" % (total, n_compiled, n_check_only))
    pct = 100.0 if total == 0 else 100.0 * (n_compiled + n_check_only) / total
    return {"total": total,
            "compiled": n_compiled,
            "check_only": n_check_only,
            "coverage_pct": pct,
            "evidence_insufficient": list(evidence_insufficient)}


# ---------------------------------------------------------------- f. 七对冲突模板与全量冲突图（P2，§5.1 理念冲突电池）

# 七对冲突模板（§5.1 冲突电池七对的固化枚举；pair_id 从 §5.1 七对命名按 kebab-case 推导，
# 与 7 块对抗板 adv-01..adv-07 一一对应）。每对两侧的 rule_kinds = 该侧在对应对抗板
# 注册表中实际出现的 compiled_rule.kind 集合（逐对注明出处板；每板恰好携带一对冲突原则，
# 另有一中性 partition_granularity 条目不参与任何一对）。
# 模板只刻画"哪些 kind 构成一对"，不预制 winner——winner/loser 一律从命中条目自身的
# priority / yields_to 确定性裁决（见 detect_principle_pairs），与声明式协议同一规则。
PAIR_TEMPLATES = (
    {
        # 出处板 adv-01-pwr-vs-bus：P-PWR-PRIORITY(80) vs P-BUS-INTEGRITY(40)
        "pair_id": "pwr-vs-bus",
        "sides": [
            {"role": "power", "rule_kinds": ["power_corridor_priority"]},
            {"role": "bus", "rule_kinds": ["ribbon_whole_route"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：电源 vs 普通总线（板 adv-01-pwr-vs-bus）",
    },
    {
        # 出处板 adv-02-clk-vs-short：P-CLK-ISOLATE(60) vs P-SHORT-RUN(30)
        "pair_id": "clk-vs-short",
        "sides": [
            {"role": "clock", "rule_kinds": ["sensitive_clearance"]},
            {"role": "short", "rule_kinds": ["short_run"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：时钟 vs 短线偏好（板 adv-02-clk-vs-short）",
    },
    {
        # 出处板 adv-03-diff-vs-capacity：P-DIFF-PAIRING(70) vs P-CORRIDOR-BUDGET(45)
        "pair_id": "diff-vs-capacity",
        "sides": [
            {"role": "diff_pair", "rule_kinds": ["diff_pair_coupling"]},
            {"role": "corridor_capacity", "rule_kinds": ["corridor_capacity_budget"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：差分对 vs 走廊容量（板 adv-03-diff-vs-capacity）",
    },
    {
        # 出处板 adv-04-xtalk-vs-vias：P-XTALK-BUDGET(65) vs P-VIA-FRUGAL(35)
        "pair_id": "xtalk-vs-vias",
        "sides": [
            {"role": "crosstalk", "rule_kinds": ["crosstalk_budget"]},
            {"role": "via", "rule_kinds": ["via_frugal"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：串扰预算 vs 过孔数量（板 adv-04-xtalk-vs-vias）",
    },
    {
        # 出处板 adv-05-eqlen-vs-layerpref：P-EQLEN-GROUP(60) vs P-LAYER-PREF(40)
        "pair_id": "eqlen-vs-layerpref",
        "sides": [
            {"role": "equal_length", "rule_kinds": ["equal_length_group"]},
            {"role": "layer_pref", "rule_kinds": ["layer_preference"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：等长组 vs 层优选（板 adv-05-eqlen-vs-layerpref）",
    },
    {
        # 出处板 adv-06-copper-vs-completion：P-COMPLETION(75) vs P-COPPER-GUARD(55)——完成性赢
        "pair_id": "copper-vs-completion",
        "sides": [
            {"role": "copper_guard", "rule_kinds": ["existing_copper_guard"]},
            {"role": "completion", "rule_kinds": ["completion_first"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：既有铜保护 vs 新网络完成性（板 adv-06-copper-vs-completion）",
    },
    {
        # 出处板 adv-07-objection-vs-floor：P-R1-FLOOR(100, hard) vs P-WIDTH-SLIM(45, soft)——硬地板赢
        "pair_id": "objection-vs-floor",
        "sides": [
            {"role": "objection", "rule_kinds": ["width_push"]},
            {"role": "invariant_floor", "rule_kinds": ["r1_width_floor"]},
        ],
        "basis": "V5.0-DEV-TASKBOOK §5.1 理念冲突电池：软先验 objection vs 不变式地板（板 adv-07-objection-vs-floor）",
    },
)


def _rule_kind(entry):
    """取条目的 compiled_rule.kind；check_only / 缺 kind / 非法形状 → None（不参与模板命中）。"""
    cr = entry.get("compiled_rule")
    if isinstance(cr, dict):
        kind = cr.get("kind")
        if isinstance(kind, str) and kind:
            return kind
    return None


def _pair_verdict(entry_a, entry_b, pair_id):
    """裁决一对命中条目的 (winner, loser, resolution)，规则与 build_conflict_graph 一致：

    yields_to 显式让位 > priority 高者胜 > 同 priority 时 principle_id 字典序小者胜
    （确定性，与两侧声明方向无关）；互相 yields_to 无确定 winner → CompilerError。
    """
    a_id, b_id = entry_a["principle_id"], entry_b["principle_id"]
    a_yields = b_id in entry_a.get("conflict_policy", {}).get("yields_to", [])
    b_yields = a_id in entry_b.get("conflict_policy", {}).get("yields_to", [])
    if a_yields and b_yields:
        raise CompilerError("detect_principle_pairs[%s]" % pair_id,
                            "互相 yields_to（%r 与 %r 双向让位），winner 无法确定" % (a_id, b_id))
    if a_yields:
        return b_id, a_id, "yields_to"
    if b_yields:
        return a_id, b_id, "yields_to"
    pa, pb = entry_a.get("priority", 0), entry_b.get("priority", 0)
    if pa != pb:
        return (a_id, b_id, "priority") if pa > pb else (b_id, a_id, "priority")
    return min(a_id, b_id), max(a_id, b_id), "priority"  # tie-break：id 字典序小者胜


def _yield_scope(loser_entry, winner, resolution):
    """从 loser 的 yields_to 让位链 / priority 裁决确定性生成预案一句话（恒非空）。"""
    loser = loser_entry["principle_id"]
    yt = list(loser_entry.get("conflict_policy", {}).get("yields_to", []))
    if winner in yt:
        return ("预案: %s 让位于 %s；让位范围=loser 的 yields_to 显式让位链: %s"
                % (loser, winner, ", ".join(yt)))
    if resolution == "priority":
        return ("预案: %s 让位于 %s；让位范围=二者冲突的全部作用域（loser 无显式 yields_to "
                "让位链，按 priority=%d 高者胜裁决，相等时 principle_id 字典序小者胜）"
                % (loser, winner, loser_entry.get("priority", 0)))
    return "预案: %s 让位于 %s（无让位链亦无 priority 裁决依据）" % (loser, winner)


def detect_principle_pairs(registry, board=None):
    """七对冲突全枚举（纯函数，§5.1 冲突电池 P2 门）。

    对 PAIR_TEMPLATES 逐对检查：注册表中两侧是否各有 principle 命中（判据=条目
    compiled_rule 为 object 且含非空字符串 kind，且 kind ∈ 该侧 rule_kinds；
    check_only / 无 kind 条目不参与）。同侧多命中时取
    (priority 降序, principle_id 升序) 首位——确定性且与注册表声明序无关。

    命中 → {"pair_id", "present": True,
            "principles": {"a": sides[0] 命中者, "b": sides[1] 命中者},
            "winner", "loser", "yield_scope"}（winner/loser 按 _pair_verdict 预解析，
            与声明式冲突图同一规则；yield_scope 为从 priority/yields_to 确定性生成的
            预案一句话：谁让位、让位范围=loser 的 yields_to 让位链描述）。
    未命中 → {"pair_id", "present": False}。
    返回 7 对全量列表（按 pair_id 排序）。board 参数为本期预留位（当前命中判据只看
    kind、与 scope 无关，board 传 None 即可）；空注册表 → 7 对全 present=False。
    """
    candidates = []
    for entry in registry:
        pid = entry.get("principle_id")
        if not isinstance(pid, str) or not pid:
            continue  # 无合法 principle_id 的条目无法进枚举报告（声明边路径由 build_conflict_graph 拦）
        kind = _rule_kind(entry)
        if kind is not None:
            candidates.append((kind, entry))
    results = []
    for tpl in PAIR_TEMPLATES:
        hits = []
        for side in tpl["sides"]:
            side_hits = [e for k, e in candidates if k in side["rule_kinds"]]
            best = min(side_hits,
                       key=lambda e: (-e.get("priority", 0), e["principle_id"])) \
                if side_hits else None
            hits.append(best)
        if hits[0] is None or hits[1] is None:
            results.append({"pair_id": tpl["pair_id"], "present": False})
            continue
        winner, loser, resolution = _pair_verdict(hits[0], hits[1], tpl["pair_id"])
        results.append({
            "pair_id": tpl["pair_id"],
            "present": True,
            "principles": {"a": hits[0]["principle_id"], "b": hits[1]["principle_id"]},
            "winner": winner,
            "loser": loser,
            "yield_scope": _yield_scope(hits[1] if loser == hits[1]["principle_id"] else hits[0],
                                        winner, resolution),
        })
    results.sort(key=lambda r: r["pair_id"])
    return results


def build_full_conflict_graph(board):
    """组合冲突图（P2 门：§5.1 七对冲突全部可枚举、有 winner/loser 预案）。

    = 既有声明式边（build_conflict_graph）∪ detect_principle_pairs 的 present 对
    （basis="template"）；同一对 principle 既有声明边又命中模板 → 合并为一条，
    basis="declared+template"（winner/loser/resolution 以声明边为准——显式协议优先于
    模板推定）。节点=注册表全部 principle_id。形状沿用 conflict_graph 结构并新增
    "pairs"（detect_principle_pairs 全量 7 块，按 pair_id 排序）；edges 按 (a,b) 排序。

    board 为 v5.board.v1（load_board 产物或同形 dict），只读其 "principle_registry"
    （缺键视为空表）；注册表内容仍受 build_conflict_graph 的 fail-closed 校验约束。
    """
    registry = board.get("principle_registry") or []
    declared = build_conflict_graph(registry)
    pairs = detect_principle_pairs(registry)
    edges = {(e["a"], e["b"]): dict(e) for e in declared["edges"]}
    for block in pairs:
        if not block["present"]:
            continue
        pair = tuple(sorted((block["principles"]["a"], block["principles"]["b"])))
        old = edges.get(pair)
        if old is None:
            loser_entry = next((e for e in registry
                                if e.get("principle_id") == block["loser"]), {})
            loser_yt = loser_entry.get("conflict_policy", {}).get("yields_to", [])
            resolution = "yields_to" if block["winner"] in loser_yt else "priority"
            edges[pair] = {"a": pair[0], "b": pair[1], "basis": "template",
                           "winner": block["winner"], "loser": block["loser"],
                           "resolution": resolution}
        else:
            old["basis"] = "declared+template"
    return {"nodes": declared["nodes"],
            "edges": [edges[k] for k in sorted(edges)],
            "pairs": pairs}


# ---------------------------------------------------------------- 入口

def compile_board(board):
    """入口：board 先过 v5.board.load_board → 五步编译管线 → (工件 dict, canonical 字节指纹)。

    工件形状 v5.compiled_rules.v1（schemas/compiled_rules.v1.schema.json，出口自校验）：
    {"artifact", "board_id", "board_sha256", "rules", "check_only", "conflict_graph", "coverage"}。
    scope 解析结果（命中列表与 warnings）不进工件 v1，由调用方按需直调 resolve_scope 获取。
    """
    validated = board_mod.load_board(board)
    registry = validated["principle_registry"]
    resolve_scope(registry, validated)  # scope 语法/命中校验（未命中 warning 不阻断，非法语法即报错）
    graph = build_conflict_graph(registry)
    rules, check_only = compile_rules(registry)
    evidence_insufficient = semantic_checks(registry)
    coverage = coverage_report(registry, rules, check_only, evidence_insufficient)
    artifact = {
        "artifact": ARTIFACT_VERSION,
        "board_id": validated["board_id"],
        "board_sha256": validated["provenance"]["board_sha256"],
        "rules": rules,
        "check_only": check_only,
        "conflict_graph": graph,
        "coverage": coverage,
    }
    schema_loader.validate(artifact, schema_loader.load_schema("compiled_rules.v1.schema.json"),
                           schema_loader.default_registry(), "")
    return artifact, canonical.canonical_json(artifact)
