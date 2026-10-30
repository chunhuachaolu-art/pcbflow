# -*- coding: utf-8 -*-
"""EXP-S1 执行器（层计划通道 ≥4 层复测；四臂 × 9 场景 × 4 轮）。

臂：LP（层计划，序=lex）/ TIER（档位）/ FULL（全序参照）/ COMBO（层计划×档位，
H3 exploratory）。全部 GLM-5.3 Flash 子智能体（harness 内）。R0 暖启动=引擎侧
确定性编码实测。只读复用 s1_scenarios（其只读复用 pcbflow.v4exp.router；
零写入 pcbflow 仓）。

子命令：
  init      R0 基线实测并初始化四臂状态（已存在则拒绝）
  ceilings  通道天花板：LP/COMBO 空间精确枚举(≤cap)否则预注册抽样；TIER 满射
            档位枚举；FULL 全排列 oracle（n≤6 可枚举）。落 ceilings.json
  pack      --arm --sid --round 生成该场景该轮裁决包
  submit    --arm --sid --round --slates <json> 校验+求解+入账
  replay    展开确定性自检（每臂 3 场景重放）
  report    H1/G-Q1..Q3 判读与终判枚举

判分键不落任何包内：包只含板事实与该场景自身实测，永不含基线对比、天花板/
oracle/门值或另一臂数据（盲测边界，判读只在主会话）。
"""

import argparse
import hashlib
import itertools
import json
import os
import re
import sys

ROOT = "E:/ZCodeData/ZCodeProject/route-v5"
OUT = os.path.join(ROOT, "out", "guide-exp-s1")
STATE = os.path.join(OUT, "state")
ROUNDS = os.path.join(OUT, "rounds")
MODEL = os.path.join(OUT, "model-runs")
CEIL = os.path.join(OUT, "ceilings")
sys.path.insert(0, ROOT)
import s1_scenarios as s1  # noqa: E402

ARMS = ("LP", "TIER", "FULL", "COMBO")
N_ROUNDS = 4
PROBE_BUDGET = 3
TIER_CAP = 20000       # TIER 空间精确枚举上限（满射档位 ≤540/场景，远低于）
PLAN_CAP = 5000        # 计划空间精确枚举上限，超出走预注册抽样
COMBO_CAP = 5000
SAMPLE_N = 600         # 抽样规模（预注册冻结）
SALT_CEIL = "ceil-v1"  # 抽样盐（预注册冻结）
SEED_SALT = "s1-sample-v1"


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def state_path(arm):
    return os.path.join(STATE, "%s.json" % arm)


def load_state(arm):
    return _load(state_path(arm))


def save_state(arm, st):
    _write(state_path(arm), st)


# ---------------------------------------------------------------- 展开器

def expand_lp(sid, proposal):
    """LP：{net: 钉值|null}；序=lex；prefs=非空钉。非法钉/未知网 → None。"""
    plan = proposal.get("plan")
    if not isinstance(plan, dict):
        return None
    clean = {}
    for nid, v in plan.items():
        if nid not in s1.net_ids_of(sid):
            return None
        if v is None:
            continue
        if not s1.pin_valid(sid, nid, v):
            return None
        clean[nid] = v
    order, prefs = s1.expand_plan(sid, clean)
    return {"order": order, "plan": clean, "prefs": prefs}


def expand_tier(sid, proposal):
    """TIER：{net: 1|2|3} 三档全非空；序=sort by (tier, net_id)。"""
    tiers = proposal.get("tiers")
    if not isinstance(tiers, dict):
        return None
    nets = s1.net_ids_of(sid)
    if sorted(tiers) != sorted(nets):
        return None
    vals = {}
    for nid, v in tiers.items():
        if v not in (1, 2, 3) or (isinstance(v, bool)):
            return None
        vals[nid] = v
    if set(vals.values()) != {1, 2, 3}:
        return None
    order = sorted(nets, key=lambda n: (vals[n], n))
    return {"order": [str(x) for x in order], "tiers": vals}


def expand_full(sid, proposal):
    """FULL：完整排列。"""
    order = proposal.get("route_order")
    if not isinstance(order, list):
        return None
    order = [str(x) for x in order]
    nets = s1.net_ids_of(sid)
    if sorted(order) != sorted(nets) or len(set(order)) != len(nets):
        return None
    return {"order": order}


def expand_combo(sid, proposal):
    """COMBO：{plan, tiers}；序=档位展开，prefs=层计划。"""
    t = expand_tier(sid, proposal)
    if t is None:
        return None
    p = expand_lp(sid, proposal)
    if p is None:
        return None
    return {"order": t["order"], "tiers": t["tiers"], "plan": p["plan"],
            "prefs": p["prefs"]}


EXPANDERS = {"LP": expand_lp, "TIER": expand_tier, "FULL": expand_full,
             "COMBO": expand_combo}


def proposal_of(slate, arm):
    """从 agent json 提取该臂提案段。LP/TIER/FULL 直接顶层兼容 + 专字段。"""
    if arm == "LP":
        return {"plan": slate.get("plan") or slate.get("layer_plan")}
    if arm == "TIER":
        return {"tiers": slate.get("tiers")}
    if arm == "FULL":
        return {"route_order": slate.get("route_order")}
    return {"plan": slate.get("plan") or slate.get("layer_plan"),
            "tiers": slate.get("tiers")}


# ---------------------------------------------------------------- 求解与记录

def measure(sid, order, plan=None, group="S1"):
    r = s1.solve_s1(sid, order, plan or {}, group)
    run = r.pop("run")
    r["per_net"] = sa_contrib(run)
    routed = {rt["net_id"] for rt in run.get("routes", [])}
    r["failed_net"] = next((x for x in r["order"] if x not in routed), None)
    return r


def sa_contrib(run):
    per = {}
    for rt in run.get("routes", []):
        c = per.setdefault(rt["net_id"], {"length_mm": 0.0, "vias": 0,
                                          "bends": 0})
        pts = rt.get("polyline_mm") or []
        for a, b in zip(pts, pts[1:]):
            c["length_mm"] += abs(b[0] - a[0]) + abs(b[1] - a[1])
        for a, b, d in zip(pts, pts[1:], pts[2:]):
            if (b[0] - a[0], b[1] - a[1]) != (d[0] - b[0], d[1] - b[1]):
                c["bends"] += 1
    for v in run.get("vias", []):
        per.setdefault(v["net_id"], {"length_mm": 0.0, "vias": 0, "bends": 0})
        per[v["net_id"]]["vias"] += 1
    for nid, c in per.items():
        c["contribution"] = round(c["length_mm"] + 8.0 * c["vias"]
                                  + 0.5 * c["bends"], 4)
    return per


def solve_expanded(sid, arm, expanded, group):
    return measure(sid, expanded["order"], expanded.get("plan"), group)


# ---------------------------------------------------------------- R0 暖启动

def warm_proposal(arm, sid):
    """R0 编码公式（预注册冻结）：lex 序 → 三档连续段（LP 臂不切段）。"""
    nets = s1.net_ids_of(sid)
    n = len(nets)
    if arm == "LP":
        return {"plan": {}}
    if arm == "TIER":
        c1 = -(-n // 3)
        c2 = -(-(n - c1) // 2)
        tiers = {}
        for i, nid in enumerate(nets):
            tiers[nid] = 1 if i < c1 else (2 if i < c1 + c2 else 3)
        return {"tiers": tiers}
    if arm == "FULL":
        return {"route_order": list(nets)}
    c1 = -(-n // 3)
    c2 = -(-(n - c1) // 2)
    tiers = {}
    for i, nid in enumerate(nets):
        tiers[nid] = 1 if i < c1 else (2 if i < c1 + c2 else 3)
    return {"plan": {}, "tiers": tiers}


# ---------------------------------------------------------------- 天花板

def tier_space_list(sid):
    nets = s1.net_ids_of(sid)
    out = []
    for tup in itertools.product((1, 2, 3), repeat=len(nets)):
        if set(tup) != {1, 2, 3}:
            continue
        out.append(dict(zip(nets, tup)))
    return out


def plan_space_list(sid):
    space = s1.plan_space(sid)
    total = 1
    for v in space.values():
        total *= len(v)
    nets = s1.net_ids_of(sid)
    if total > PLAN_CAP:
        plans = s1.sample_plans(sid, SAMPLE_N, SEED_SALT + "|" + SALT_CEIL)
        return plans, "sample%d" % SAMPLE_N, total
    combos = [dict(zip(nets, tup))
              for tup in itertools.product(*[space[n] for n in nets])]
    return combos, "exact", total


def combo_space_list(sid):
    plans, pmode, ptotal = plan_space_list(sid)
    tiers = tier_space_list(sid)
    total = ptotal * len(tiers)
    if total > COMBO_CAP:
        rng_seed = hashlib.sha256((SEED_SALT + "|combo|" + SALT_CEIL + "|"
                                   + sid).encode()).digest()
        import random
        rng = random.Random(int.from_bytes(rng_seed[:4], "big"))
        picks = []
        seen = set()
        tries = 0
        while len(picks) < SAMPLE_N and tries < SAMPLE_N * 20:
            tries += 1
            p = rng.choice(plans)
            t = rng.choice(tiers)
            key = (tuple(sorted(p.items())), tuple(sorted(t.items())))
            if key in seen:
                continue
            seen.add(key)
            picks.append({"plan": p, "tiers": t})
        return picks, "sample%d" % SAMPLE_N, total
    combos = []
    for p in plans:
        for t in tiers:
            combos.append({"plan": p, "tiers": t})
    return combos, "exact", total


def proposals_for_channel(arm, sid):
    """返回 [(proposal_dict, expander)]；proposal 一律按展开器输入形状包装。
    FULL=全排列。"""
    if arm == "LP":
        plans, mode, total = plan_space_list(sid)
        return [({"plan": p}, "LP") for p in plans], mode, total
    if arm == "TIER":
        ts = tier_space_list(sid)
        return [({"tiers": t}, "TIER") for t in ts], "exact", len(ts)
    if arm == "COMBO":
        cs, mode, total = combo_space_list(sid)
        return [(c, "COMBO") for c in cs], mode, total
    if arm == "FULL":
        nets = s1.net_ids_of(sid)
        perms = list(itertools.permutations(nets))
        return [({"route_order": list(p)}, "FULL") for p in perms], \
            "exact", len(perms)
    raise ValueError(arm)


def _ceil_worker(arg):
    sid, arm, proposal = arg
    ex = EXPANDERS[arm](sid, proposal)
    if ex is None:
        return {"invalid": True}
    r = solve_expanded(sid, arm, ex, "S1-CEIL")
    r.pop("per_net", None)
    return {"sid": sid, "arm": arm, "proposal": proposal,
            "objective": r["objective"], "all_connected": r["all_connected"],
            "order": r["order"]}


def cmd_ceilings(args):
    os.makedirs(CEIL, exist_ok=True)
    from multiprocessing import Pool
    arms = [a.strip().upper() for a in args.arms.split(",")] \
        if args.arms else list(ARMS)
    out = {}
    if os.path.exists(os.path.join(CEIL, "ceilings.json")):
        out = _load(os.path.join(CEIL, "ceilings.json"))["per"]
        for a in arms:
            out.pop(a, None)
    meta = {}
    for arm in arms:
        out[arm] = {}
        for sid in s1.ORDERED_SIDS:
            props, mode, total = proposals_for_channel(arm, sid)
            jobs = [(sid, arm, p) for p, _ in props]
            with Pool(args.procs) as pool:
                rows = pool.map(_ceil_worker, jobs)
            invalid = sum(1 for r in rows if r and r.get("invalid"))
            if invalid:
                raise RuntimeError(
                    "ceil %s %s：%d 个提案在空间内被判非法=空间/展开器不一致"
                    % (arm, sid, invalid))
            sat = [r for r in rows if r and not r.get("invalid")
                   and r["all_connected"]]
            best = min(sat, key=lambda r: (r["objective"], r["order"])) \
                if sat else None
            out[arm][sid] = {"mode": mode, "space": total,
                             "evaluated": len(jobs),
                             "sat_count": len(sat),
                             "ceiling": best["objective"] if best else None,
                             "argmin_order": best["order"] if best else None,
                             "argmin_proposal": best["proposal"] if best
                             else None}
            meta["%s/%s" % (arm, sid)] = mode
            print("ceil %s %s %s space=%d sat=%d ceiling=%s"
                  % (arm, sid, mode, total, len(sat),
                     out[arm][sid]["ceiling"]))
    _write(os.path.join(CEIL, "ceilings.json"), {
        "note": "通道天花板；sampleN=预注册抽样(盐 %s, seed %s)下界估计非穷举"
                "——cceil 以其为分母偏保守（真天花板≤抽样值）"
                % (SALT_CEIL, SEED_SALT),
        "per": out})
    print("ceilings: done ->", os.path.join(CEIL, "ceilings.json"))


# ---------------------------------------------------------------- 包生成

def board_facts(sid):
    board = s1.load_board(sid)
    L = []
    bb = board["board"]
    L.append("【板】bbox [%g,%g]×[%g,%g] mm；信号层（4 层）：%s"
             % (bb["bbox_mm"][0], bb["bbox_mm"][1], bb["bbox_mm"][2],
                bb["bbox_mm"][3], "、".join(bb["layers"])))
    ru = board["rules"]
    width_txt = "、".join("%s %g" % (k, v)
                          for k, v in sorted(ru["width_mm"].items()))
    layer_txt = "；".join("%s 仅 %s" % (k, "/".join(v))
                          for k, v in sorted(ru["allowed_layers"].items())
                          if k != "default")
    L.append("【规则】格点 %g mm；不同网络铜净距 ≥%g mm；线宽：%s；过孔 pad %g/"
             "hole %g mm（过孔焊盘 3×3 邻域同时占用两层=稀缺资源；过孔可在"
             "任意层对间转换）%s"
             % (ru["grid_mm"], ru["clearance_mm"], width_txt,
                ru["via"]["pad_mm"], ru["via"]["hole_mm"],
                ("；类层约束：" + layer_txt) if layer_txt else ""))
    L.append("【成本模型（仅用于决策，禁止输出数值）】总成本 = 走线总长 + "
             "8×过孔数 + 0.5×拐弯数，越小越好。每层可自由走线；换层必经过孔。")
    L.append("")
    L.append("【焊盘】（layer=焊盘所在层；网两端焊盘层不同时必须含两端）")
    for p in sorted(board["pads"], key=lambda p: p["pad_id"]):
        L.append("  %s：(%g,%g) %g×%g mm，%s，属 %s"
                 % (p["pad_id"], p["x_mm"], p["y_mm"], p["w_mm"], p["h_mm"],
                    p["layer"], p["net_id"]))
    L.append("")
    L.append("【网络】")
    for n in sorted(board["nets"], key=lambda n: n["net_id"]):
        L.append("  %s [%s]：%s" % (n["net_id"], n["net_class"],
                                    "–".join(n["endpoints"])))
    rels = board.get("relations") or []
    if rels:
        L.append("")
        L.append("【关系（分组事实，仅供决策参考）】")
        for r in sorted(rels, key=lambda r: r["relation_id"]):
            L.append("  %s（%s）：%s" % (r["relation_id"], r["relation_type"],
                                         "、".join(r["members"])))
    L.append("")
    L.append("【禁布区】（layers=该矩形在这些层上禁布）")
    for k in board["keepouts"]:
        L.append("  %s layers=%s rect=%s"
                 % (k["keepout_id"], "/".join(k["layers"]),
                    json.dumps(k["rect_mm"])))
    return L


def fmt_plan(plan):
    if not plan:
        return "（全自动）"
    return "、".join("%s=%s" % (k, v) for k, v in sorted(plan.items()))


def fmt_tiers(tiers):
    if not tiers:
        return "（无）"
    return "、".join("%s=T%d" % (n, tiers[n])
                     for n in sorted(tiers, key=lambda x: (tiers[x], x)))


def fmt_feedback(sid, rd, arm):
    m = rd["main"]
    lines = []
    if m["all_connected"]:
        lines.append("引擎实测：全部连通；总成本 %s" % m["objective"])
    else:
        lines.append("引擎实测：**未能全部连通（该方案 routing 失败，整跑终止）"
                     "**；失败网：%s。已布部分逐网贡献：" % m.get("failed_net"))
    lines.append("逐网成本贡献（走线长 + 8×过孔 + 0.5×拐弯；过孔与拐弯顺序敏感"
                 "——先布走直、后布让路）：")
    for nid in m["order"]:
        c = (m.get("per_net") or {}).get(nid)
        if c:
            lines.append("  %s：长度 %s mm，过孔 %d，拐弯 %d，贡献 %s"
                         % (nid, round(c["length_mm"], 2), c["vias"],
                            c["bends"], c["contribution"]))
    if rd.get("probes"):
        lines.append("你的探针实测：")
        for p in rd["probes"]:
            if p["all_connected"]:
                lines.append("  [%s] 总成本 %s（全部连通）"
                             % (p["label"], p["objective"]))
            else:
                lines.append("  [%s] **routing 失败**（失败网 %s）"
                             % (p["label"], p.get("failed_net")))
    return lines


def contract_text(arm, sid):
    nets = s1.net_ids_of(sid)
    if arm == "LP":
        return (
            "【通道与输出合同】你只掌控一项：**层计划**——为每个网指定允许层集"
            "（布线顺序固定为编号序 n1→n%d，不在你掌控内）。钉值字母表：\n"
            "  null（自动，不限制）/ \"F.Cu\" / \"B.Cu\" / \"In1.Cu\" / "
            "\"In2.Cu\" / \"INNER\"（内层对 {In1,In2}）/ \"F_I1\"（F+In1）/ "
            "\"F_I2\"（F+In2）/ \"F_B\"（F+B）。\n"
            "硬约束：钉集必须**包含该网两个焊盘所在的层**（焊盘层固定，见【焊盘】"
            "表），否则该网无法布通、整跑失败；钉集与该网类别允许层求交后生效"
            "（clock 类网仅内层对可用）。限制越多自由度越小：钉少了会逼网绕行/"
            "失败，钉对了能 reserved 稀缺资源给后布的网。\n"
            "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
            "单个对象：{\"scenario_id\": \"%s\", \"plan\": {\"<net_id>\": "
            "<钉值|null>, …}（未列出的网=自动）, \"reason\": \"<一句话>\", "
            "\"probes\": [{\"label\": \"<短名>\", \"plan\": {…}}…]}。"
            "probes 是你想让引擎代测的至多 %d 个备选层计划（可不填）。"
            % (len(nets), sid, PROBE_BUDGET))
    if arm == "TIER":
        return (
            "【通道与输出合同】你只掌控一项：**布线档位**——给每个网指定档位 "
            "1/2/3（1=最先布），三档都必须至少有一个网。展开规则（确定性）："
            "先布档位 1 的全部网（按编号升序），再档位 2，再档位 3。"
            "先布的网可走直路，后布的让路绕行。\n"
            "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
            "单个对象：{\"scenario_id\": \"%s\", \"tiers\": {\"<net_id>\": "
            "<1|2|3>, …（每网恰一个，三档全非空）}, \"reason\": \"<一句话>\", "
            "\"probes\": [{\"label\": \"<短名>\", \"tiers\": {…}}…]}。"
            "probes=至多 %d 个备选档位分配（可不填）。" % (sid, PROBE_BUDGET))
    if arm == "FULL":
        return (
            "【通道与输出合同】你掌控**完整布线顺序**（每个网恰好一次）。引擎按"
            "你的顺序逐网布线：先布的可走直路，后布的让路绕行；任一网失败则整跑"
            "停止（无拆除重布）。层选择由引擎自动优化，你不可指定。\n"
            "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
            "单个对象：{\"scenario_id\": \"%s\", \"route_order\": [\"<net_id>\","
            " …完整排列每个恰好一次], \"reason\": \"<一句话>\", \"probes\": "
            "[{\"label\": \"<短名>\", \"route_order\": […]}…]}。probes=至多 %d "
            "个备选排列（可不填）。" % (sid, PROBE_BUDGET))
    return (
        "【通道与输出合同】你掌控两项：**层计划**（钉值字母表与硬约束同 LP 通道："
        "null/F.Cu/B.Cu/In1.Cu/In2.Cu/INNER/F_I1/F_I2/F_B，钉集必含焊盘层）与"
        "**布线档位**（每网 1/2/3，三档全非空；展开=档位 1 按编号序，再档位 2，"
        "再档位 3）。\n"
        "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
        "单个对象：{\"scenario_id\": \"%s\", \"plan\": {…}, \"tiers\": {…}, "
        "\"reason\": \"<一句话>\", \"probes\": [{\"label\": \"<短名>\", "
        "\"plan\": {…}, \"tiers\": {…}}…]}。probes=至多 %d 个备选（可不填）。"
        % (sid, PROBE_BUDGET))


def cmd_pack(args):
    st = load_state(args.arm)
    sc_st = st["scenarios"][args.sid]
    if args.round != sc_st["round"] + 1:
        raise SystemExit("pack: 场景 %s 当前轮=%d，请求轮=%d 不连续"
                         % (args.sid, sc_st["round"], args.round))
    nets = s1.net_ids_of(args.sid)
    L = []
    L.append("# EXP-S1 第 %d 轮（%s-%s）" % (args.round, args.arm, args.sid))
    L.append("")
    if args.arm in ("LP", "COMBO"):
        L.append("你在多轮迭代中为一个确定性搜索式布线引擎提供**层计划**"
                 + ("与**布线档位**" if args.arm == "COMBO" else "")
                 + "：它按给定顺序/约束逐网布线并实测回报；你依据实测修订策略。"
                 "铁律：不输出任何数值。")
    elif args.arm == "TIER":
        L.append("你在多轮迭代中为一个确定性搜索式布线引擎提供**布线档位**："
                 "它按档位展开序逐网布线并实测回报；你依据实测修订策略。"
                 "铁律：不输出任何数值。")
    else:
        L.append("你在多轮迭代中引导一个确定性搜索式布线引擎：它严格按你给的"
                 "顺序逐网布线并实测回报；你依据实测修订策略。铁律：不输出任何"
                 "数值。")
    L.append("")
    L.append("# 排序裁决包 %s" % args.sid)
    L.append("")
    L.append("你是 PCB 布线裁决器。下面是一张 4 层板的完整机器事实（结构化"
             "文本，非图像）。任一网布线失败则整跑立即停止（无拆除重布）。"
             "请给出你认为最终总成本最低的方案。")
    L.append("")
    L.extend(board_facts(args.sid))
    L.append("")
    L.append("【网络清单】%s" % "、".join(nets))
    L.append("")
    L.append("【默认策略（基线）】%s" % {
        "LP": "全部网自动层（不钉任何层）+编号序",
        "TIER": "编号序切成三档（前 ⌈n/3⌉ 个 T1，次 ⌈(n−⌈n/3⌉)/2⌉ 个 T2，余 T3）",
        "FULL": "编号序 n1→n%d" % len(nets),
        "COMBO": "全部网自动层+编号序切三档（同 TIER 描述）"}[args.arm])
    L.append("")
    L.append("【你此前各轮的提案与引擎实测】")
    for rr in range(0, sc_st["round"] + 1):
        rd = sc_st["rounds"][str(rr)]
        m = rd["main"]
        L.append("— 第 %d 轮 —" % rr)
        if m.get("plan") is not None or args.arm in ("LP", "COMBO"):
            L.append("你的层计划：%s" % fmt_plan(m.get("plan")))
        if m.get("tiers") is not None or args.arm in ("TIER", "COMBO"):
            L.append("你的档位：%s" % fmt_tiers(m.get("tiers")))
        if args.arm == "FULL":
            L.append("你的排序：%s" % "、".join(m["order"]))
        L.extend(fmt_feedback(args.sid, rd, args.arm))
    L.append("")
    L.append("【第 %d 轮任务】给出本场景的新提案（实测显示已无可改进时允许"
             "坚持原案）。" % args.round)
    L.append(contract_text(args.arm, args.sid))
    text = "\n".join(L) + "\n"
    path = os.path.join(ROUNDS, "round-%d" % args.round,
                        "%s-%s-pack.md" % (args.arm, args.sid))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("pack: %s (%d bytes)" % (path, len(text.encode("utf-8"))))


# ---------------------------------------------------------------- 提交求解

def parse_slates(path):
    raw = open(path, encoding="utf-8").read()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    text = m.group(1) if m else raw
    return json.loads(text)


def cmd_submit(args):
    st = load_state(args.arm)
    sc_st = st["scenarios"][args.sid]
    if args.round != sc_st["round"] + 1:
        raise SystemExit("submit: 场景 %s 当前轮=%d，请求轮=%d 不连续"
                         % (args.sid, sc_st["round"], args.round))
    raw = open(args.slates, encoding="utf-8").read()
    run_dir = os.path.join(MODEL, "%s-%s" % (args.arm, args.sid))
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "round-%d-response.json" % args.round),
              "w", encoding="utf-8", newline="\n") as f:
        f.write(raw)
    try:
        slate = parse_slates(args.slates)
    except Exception as e:
        slate = {}
        print("submit: json 解析失败 %s" % e)
    if slate.get("scenario_id") != args.sid:
        st["invalid_count"] += 1
        save_state(args.arm, st)
        _write(os.path.join(run_dir, "round-%d-INVALID.json" % args.round),
               {"reason": "sid_mismatch", "got": slate.get("scenario_id")})
        print("submit: INVALID（累计无效 %d）" % st["invalid_count"])
        return
    main_ex = EXPANDERS[args.arm](args.sid, proposal_of(slate, args.arm))
    if main_ex is None:
        st["invalid_count"] += 1
        save_state(args.arm, st)
        _write(os.path.join(run_dir, "round-%d-INVALID.json" % args.round),
               {"reason": "invalid_proposal_for_channel"})
        print("submit: INVALID 提案（累计无效 %d）" % st["invalid_count"])
        return
    rd = {"main": solve_expanded(args.sid, args.arm, main_ex,
                                 "S1-%s" % args.arm), "probes": []}
    rd["main"]["plan"] = main_ex.get("plan")
    rd["main"]["tiers"] = main_ex.get("tiers")
    seen = {"|".join(main_ex["order"])}
    if args.arm in ("LP", "COMBO"):
        seen.add("|".join(sorted((k or "", str(v))
                                 for k, v in (main_ex.get("plan")
                                              or {}).items())))
    probes = slate.get("probes") or []
    if isinstance(probes, dict):
        probes = [probes]
    for p in probes[:PROBE_BUDGET]:
        if not isinstance(p, dict):
            continue
        ex = EXPANDERS[args.arm](args.sid, proposal_of(p, args.arm))
        if ex is None:
            continue
        key = "|".join(ex["order"])
        if args.arm in ("LP", "COMBO"):
            key += "#" + "|".join(sorted((k or "", str(v))
                                         for k, v in (ex.get("plan")
                                                      or {}).items()))
        if key in seen:
            continue
        seen.add(key)
        r = solve_expanded(args.sid, args.arm, ex, "S1-%s-PROBE" % args.arm)
        r["plan"] = ex.get("plan")
        r["tiers"] = ex.get("tiers")
        r["label"] = str(p.get("label", "p"))[:24]
        rd["probes"].append(r)
    sc_st["rounds"][str(args.round)] = rd
    sc_st["round"] = args.round
    save_state(args.arm, st)
    print("submit: %s-%s round %d ok（main sat=%s obj=%s, probes=%d）"
          % (args.arm, args.sid, args.round, rd["main"]["all_connected"],
             rd["main"]["objective"], len(rd["probes"])))


# ---------------------------------------------------------------- 重放自检

def cmd_replay(_):
    ok = True
    for arm in ("LP", "TIER", "COMBO"):
        for sid in s1.ORDERED_SIDS[:3]:
            ex1 = EXPANDERS[arm](sid, warm_proposal(arm, sid))
            ex2 = EXPANDERS[arm](sid, warm_proposal(arm, sid))
            if json.dumps(ex1, sort_keys=True) != json.dumps(ex2,
                                                             sort_keys=True):
                ok = False
                print("replay: %s %s 不确定" % (arm, sid))
    print("replay: %s" % ("PASS（3 臂×3 场景字节等）" if ok else "FAIL"))
    if not ok:
        raise SystemExit(1)


# ---------------------------------------------------------------- 判读

def rank_key(r):
    return r["objective"] if r.get("all_connected") else float("inf")


def cmd_report(_):
    ceil = _load(os.path.join(CEIL, "ceilings.json"))["per"]
    # 只读派发臂（prereg §0：LP/COMBO void_by_H1 零会话；init 为四臂建了状态）
    live = [a for a in ("TIER", "FULL") if os.path.exists(state_path(a))]
    rows = []
    for sid in s1.ORDERED_SIDS:
        base = load_state(live[0])["scenarios"][sid]["rounds"]["0"]["main"]
        row = {"sid": sid, "base": base["objective"]}
        for arm in live:
            st = load_state(arm)
            rfin = st["scenarios"][sid]["round"]
            fin = st["scenarios"][sid]["rounds"][str(rfin)]["main"]
            row[arm] = fin["objective"] if fin["all_connected"] else None
            row[arm + "_sat"] = fin["all_connected"]
            row[arm + "_r"] = rfin
            c = ceil[arm][sid]["ceiling"]
            row[arm + "_ceil"] = c
            if c is not None and row[arm] is not None:
                denom = base["objective"] - c
                row[arm + "_cceil"] = round(
                    (base["objective"] - row[arm]) / denom, 4) \
                    if denom > 1e-9 else "no_headroom"
            else:
                row[arm + "_cceil"] = -1 if row[arm] is None else None
        rows.append(row)
    print("== EXP-S1 终表（live 臂=%s）==" % live)
    for r in rows:
        cells = " ".join("%s=%s(cceil %s)" % (a, r[a], r[a + "_cceil"])
                         for a in live)
        print("  %(sid)s base=%(base)s " % r + cells)

    def cceils(arm):
        vals = [r[arm + "_cceil"] for r in rows
                if isinstance(r[arm + "_cceil"], float)]
        return (sum(vals) / len(vals)) if vals else None, len(vals)
    gq1 = {}
    for arm in live:
        reg = sum(1 for r in rows if r[arm] is not None
                  and r[arm] > r["base"] * 1.01)
        unsat = sum(1 for r in rows if not r[arm + "_sat"])
        gq1[arm] = reg
        print("G-Q1 %s：回退>1%% 场景=%d，非 sat 终局=%d" % (arm, reg, unsat))
    print("G-Q2 均值 cceil：")
    for arm in live:
        m, k = cceils(arm)
        print("  %s：mean=%s（有效分母 %d/9）" % (arm, m, k))
    probes, informative, beat = 0, 0, 0
    for arm in live:
        st = load_state(arm)
        for sid in s1.ORDERED_SIDS:
            for k, rd in st["scenarios"][sid]["rounds"].items():
                for p in rd["probes"]:
                    probes += 1
                    if p["all_connected"] == rd["main"]["all_connected"] \
                            and p["objective"] != rd["main"]["objective"]:
                        informative += 1
                    if rank_key(p) < rank_key(rd["main"]):
                        beat += 1
    print("G-Q3 机制：probes=%d informative=%d beat_main=%d（情势注记照登）"
          % (probes, informative, beat))
    print("H1（层计划咬合面）：见 ceilings.json LP 列与本预注册 §2 ——"
          "引擎侧已判 h1_negative（4 轮设计迭代零咬合，模型阶段按条件结构作废）")
    rounds_done = min(load_state(a)["scenarios"][s]["round"]
                      for a in live for s in s1.ORDERED_SIDS)
    print("rounds_completed(min across live arms)=%d（<4 终判须标注 "
          "time_capped）" % rounds_done)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    c = sub.add_parser("ceilings")
    c.add_argument("--arms", default="")
    c.add_argument("--procs", type=int, default=12)
    p = sub.add_parser("pack")
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--sid", required=True)
    p.add_argument("--round", type=int, required=True)
    s = sub.add_parser("submit")
    s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--sid", required=True)
    s.add_argument("--round", type=int, required=True)
    s.add_argument("--slates", required=True)
    sub.add_parser("replay")
    sub.add_parser("report")
    args = ap.parse_args()
    {"init": cmd_init, "ceilings": cmd_ceilings, "pack": cmd_pack,
     "submit": cmd_submit, "replay": cmd_replay,
     "report": cmd_report}[args.cmd](args)


def cmd_init(_):
    if any(os.path.exists(state_path(a)) for a in ARMS):
        raise SystemExit("init: 状态文件已存在，拒绝覆盖（零回写纪律）")
    os.makedirs(STATE, exist_ok=True)
    base = {}
    for sid in s1.ORDERED_SIDS:
        r = measure(sid, s1.net_ids_of(sid), {}, "S1-R0")
        base[sid] = r
        print("R0 %s sat=%s obj=%s" % (sid, r["all_connected"],
                                       r["objective"]))
    for arm in ARMS:
        st = {"arm": arm, "invalid_count": 0,
              "scenarios": {}}
        for sid in s1.ORDERED_SIDS:
            wp = warm_proposal(arm, sid)
            ex = EXPANDERS[arm](sid, wp)
            rd = {"main": solve_expanded(sid, arm, ex, "S1-R0-%s" % arm),
                  "probes": []}
            rd["main"]["plan"] = ex.get("plan")
            rd["main"]["tiers"] = ex.get("tiers")
            st["scenarios"][sid] = {"round": 0,
                                    "rounds": {"0": rd}}
        save_state(arm, st)
    print("init: 四臂状态就绪（R0=暖启动实测；LP 基线=lex+全自动）")


if __name__ == "__main__":
    main()
