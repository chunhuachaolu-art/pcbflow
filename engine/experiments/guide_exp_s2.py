# -*- coding: utf-8 -*-
"""EXP-S2 执行器（粗通道缩放测试：档位/波次 vs 全序，n=8/12/16 × 3 场景）。

臂：TIER（档位）/ WAVE（波次）/ FULL（全序参照）× 9 场景 = 27 agent 位（全部
GLM-5.3 Flash 子智能体，harness 内，由夜班会话驱动）。R0 暖启动 = 引擎侧确定性
编码实测（三臂 R0 展开均=编号序，同一次实测共享）。只读复用 s2_scenarios（其
只读复用 pcbflow.v4exp.router；零写入 pcbflow 仓）。

探针预算（H3 两档，冻结公式）：每 (通道, 网数档) 的 {a,b,c} 中恰一个 B=5，
其余 B=3；B=5 字母 = {a,b,c}[(channel_idx+tier_idx)%3]，channel_idx
TIER=0/WAVE=1/FULL=2，tier_idx n08=0/n12=1/n16=2。包文本与 state 均记录 B。

单解超时：单次 solve 超过 EVAL_TIMEOUT_S[网数档] 记 eval_timeout 不崩溃、计入
台账（主提案超时→沿用上轮 standing；探针超时→记 eval_timeout 无 objective）。
T_solve 阶梯为常量易改（冻结值见 IMPL-REPORT.md）。

子命令：
  init     R0 实测并初始化三臂状态（已存在则拒绝）
  pack     --arm --sid --round 生成该场景该轮裁决包（盲边界：只含板事实与本
           场景本臂自身历史实测）
  submit   --arm --sid --round --slates <json|md> 校验+求解+入账；主提案无效
           →invalid_count+沿用上轮 standing（R0 兜底）
  report   机械产出 G-Q0/G-Q1/G-Q2'/G-Q3/H2/H3 表（判决解读留给主会话）

判分键不落任何包内：包永不含基线对比、参照/天花板/门值、他臂数据、数值输出权。
冒烟/隔离运行：设环境变量 S2_EXEC_OUT=<目录> 可把 state/rounds/model-runs 移
到别处（p0 板快照仍读正式根）。
"""

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import re
import sys

ROOT = "E:/ZCodeData/ZCodeProject/route-v5"
OUT = os.environ.get("S2_EXEC_OUT",
                     os.path.join(ROOT, "out", "guide-exp-s2"))
STATE = os.path.join(OUT, "state")
ROUNDS = os.path.join(OUT, "rounds")
MODEL = os.path.join(OUT, "model-runs")
P0 = os.path.join(ROOT, "out", "guide-exp-s2", "p0")  # 板快照恒读正式 p0
sys.path.insert(0, ROOT)
import s2_scenarios as s2  # noqa: E402

ARMS = ("TIER", "WAVE", "FULL")
N_ROUNDS = 4
CHANNEL_IDX = {"TIER": 0, "WAVE": 1, "FULL": 2}
TIER_IDX = {"n08": 0, "n12": 1, "n16": 2}
LETTERS = ("a", "b", "c")
#: 单解超时阶梯（秒；常量易改）。冻结值 60/150/300（TIER_IDX n08/n12/n16），
#: 依据 p0/solve-time.json（仅 wave6 共跑的非竞争口径：max 4.4/7.9/18.7s；
#: 构建期 6-worker 竞争下 n16 实测 ~84s/解）取 ~14-16x 非竞争 max、~3.5x
#: 竞争 max 的裕量——防伪 eval_timeout，同时兜住病理长磨。详见 IMPL-REPORT。
EVAL_TIMEOUT_S = {"n08": 60.0, "n12": 150.0, "n16": 300.0}
PROBE_B_HIGH = 5
PROBE_B_LOW = 3


def tier_of(sid):
    return sid.split("-")[1]


def letter_of(sid):
    return sid.split("-")[2]


def probe_budget(arm, sid):
    """H3 冻结公式：{a,b,c}[(channel_idx+tier_idx)%3] 取 B=5，其余 B=3。"""
    idx = (CHANNEL_IDX[arm] + TIER_IDX[tier_of(sid)]) % 3
    return PROBE_B_HIGH if letter_of(sid) == LETTERS[idx] else PROBE_B_LOW


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


def accepted_sids():
    man = _load(os.path.join(P0, "manifest.json"))["scenarios"]
    return [s for s in sorted(man) if not man[s].get("void")]


# ---------------------------------------------------------------- 展开器

def expand_tier(sid, proposal):
    """TIER：{net: 1|2|3} 三档全非空（满射）；序=sort by (tier, net_id)。"""
    tiers = proposal.get("tiers")
    if not isinstance(tiers, dict):
        return None
    nets = s2.net_ids_of(sid)
    if sorted(map(str, tiers.keys())) != sorted(nets):
        return None
    vals = {}
    for k, v in tiers.items():
        if isinstance(v, bool) or v not in (1, 2, 3):
            return None
        vals[str(k)] = v
    if set(vals.values()) != {1, 2, 3}:
        return None
    order = sorted(nets, key=lambda n: (vals[n], n))
    return {"order": [str(x) for x in order], "tiers": vals}


def expand_wave(sid, proposal):
    """WAVE：2–3 有序非空块；展开=块拼接、块内 net_id 字典序。"""
    waves = proposal.get("waves")
    nets = s2.net_ids_of(sid)
    if not isinstance(waves, list) or not (2 <= len(waves) <= 3):
        return None
    flat = []
    for w in waves:
        if not isinstance(w, list) or not w:
            return None
        flat.extend(str(x) for x in w)
    if sorted(flat) != sorted(nets) or len(set(flat)) != len(nets):
        return None
    norm = [sorted(str(x) for x in w) for w in waves]
    order = []
    for w in norm:
        order.extend(w)
    return {"order": order, "waves": norm}


def expand_full(sid, proposal):
    """FULL：完整排列。"""
    order = proposal.get("route_order")
    if not isinstance(order, list):
        return None
    order = [str(x) for x in order]
    nets = s2.net_ids_of(sid)
    if sorted(order) != sorted(nets) or len(set(order)) != len(nets):
        return None
    return {"order": order}


EXPANDERS = {"TIER": expand_tier, "WAVE": expand_wave, "FULL": expand_full}


def proposal_of(slate, arm):
    if arm == "TIER":
        return {"tiers": slate.get("tiers")}
    if arm == "WAVE":
        return {"waves": slate.get("waves")}
    return {"route_order": slate.get("route_order")}


def warm_proposal(arm, sid):
    """R0 冻结编码：TIER=lex 三连续段切分（S1 公式 ⌈n/3⌉,⌈(n−⌈n/3⌉)/2⌉,余）；
    WAVE=lex 两等块（⌈n/2⌉+余）；FULL=lex。lex=net_id 字典序（sorted，
    与展开规则同序），故三臂 R0 展开均=字典序=基线，实测一次共享。"""
    nets = s2.baseline_order(sid)
    n = len(nets)
    if arm == "TIER":
        c1 = -(-n // 3)
        c2 = -(-(n - c1) // 2)
        tiers = {}
        for i, nid in enumerate(nets):
            tiers[nid] = 1 if i < c1 else (2 if i < c1 + c2 else 3)
        return {"tiers": tiers}
    if arm == "WAVE":
        h = -(-n // 2)
        return {"waves": [nets[:h], nets[h:]]}
    return {"route_order": list(nets)}


# ---------------------------------------------------------------- 求解（带超时）

def sa_contrib(run):
    """逐网 length + 8*vias + 0.5*bends（与 seat_ab_r1a/scale_r1 同口径）。"""
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


def _solve_child(sid, order, group, q):
    """子进程：直呼 router.solve_board，只回传小结果（含逐网贡献）。"""
    try:
        board = s2.load_board(sid)
        run = s2.router.solve_board(board, {"route_order": order,
                                            "group": group})
        m = run["metrics"]
        routed = {rt["net_id"] for rt in run.get("routes", [])}
        failed_net = next((x for x in order if x not in routed), None)
        q.put(("ok", {
            "order": [str(x) for x in order],
            "objective": m["objective"] if m["all_connected"] else None,
            "all_connected": m["all_connected"], "status": run["status"],
            "violations": m["violations"], "nodes": m["search_nodes"],
            "failed_net": failed_net,
            "per_net": sa_contrib(run) if run.get("routes") else {}}))
    except Exception as e:  # 子进程内任何异常都不得炸掉主流程
        q.put(("err", repr(e)))


def measure(sid, order, group):
    """带 T_solve 超时的单解；超时返回 eval_timeout 记录（不崩溃）。"""
    order = [str(x) for x in order]
    q = mp.Queue()
    p = mp.Process(target=_solve_child, args=(sid, order, group, q))
    p.start()
    try:
        kind, payload = q.get(timeout=EVAL_TIMEOUT_S[tier_of(sid)])
        p.join(15)
    except Exception:
        p.terminate()
        p.join()
        return {"order": order, "objective": None, "all_connected": None,
                "status": "eval_timeout", "violations": None, "nodes": None,
                "failed_net": None, "per_net": {}, "eval_timeout": True}
    if kind == "err":
        return {"order": order, "objective": None, "all_connected": None,
                "status": "child_error:%s" % payload, "violations": None,
                "nodes": None, "failed_net": None, "per_net": {},
                "eval_timeout": False, "child_error": payload}
    payload["eval_timeout"] = False
    return payload


# ---------------------------------------------------------------- init

def cmd_init(_):
    if any(os.path.exists(state_path(a)) for a in ARMS):
        raise SystemExit("init: 状态文件已存在，拒绝覆盖（零回写纪律）")
    os.makedirs(STATE, exist_ok=True)
    sids = accepted_sids()
    if not sids:
        raise SystemExit("init: 无已验收场景（见 p0/manifest.json）")
    for sid in sids:
        r0 = measure(sid, s2.baseline_order(sid), "S2-R0")
        if r0.get("child_error") or r0["all_connected"] is None:
            print("R0 %s: %s" % (sid, r0["status"]))
        else:
            print("R0 %s sat=%s obj=%s" % (sid, r0["all_connected"],
                                           r0["objective"]))
        for arm in ARMS:
            wp = warm_proposal(arm, sid)
            ex = EXPANDERS[arm](sid, wp)
            assert ex is not None and ex["order"] == s2.baseline_order(sid)
            main = dict(r0)
            main["carried"] = False
            main["invalid_main"] = None
            main["eval_timeout_main"] = bool(r0.get("eval_timeout"))
            main["tiers"] = ex.get("tiers")
            main["waves"] = ex.get("waves")
            main["proposal"] = wp
            st = load_state(arm) if os.path.exists(state_path(arm)) else {
                "arm": arm, "invalid_count": 0, "eval_timeouts": 0,
                "scenarios": {}}
            st["scenarios"][sid] = {
                "round": 0, "probe_budget": probe_budget(arm, sid),
                "rounds": {"0": {"main": main, "probes": [],
                                 "carried": False, "invalid_main": None}}}
            save_state(arm, st)
    print("init: 三臂状态就绪（R0=lex 暖启动实测，三臂同值共享；"
          "探针 B 已按 H3 公式入 state）")


# ---------------------------------------------------------------- 包生成

def fmt_tiers(tiers):
    return "、".join("%s=T%d" % (n, tiers[n])
                     for n in sorted(tiers, key=lambda x: (tiers[x], x)))


def fmt_waves(waves):
    return " ".join("第%d波[%s]" % (i + 1, ",".join(w))
                    for i, w in enumerate(waves))


def board_facts(sid):
    board = s2.load_board(sid)
    L = []
    bb = board["board"]
    L.append("【板】bbox [%g,%g]×[%g,%g] mm；信号层（2 层）：%s"
             % (bb["bbox_mm"][0], bb["bbox_mm"][1], bb["bbox_mm"][2],
                bb["bbox_mm"][3], "、".join(bb["layers"])))
    ru = board["rules"]
    width_txt = "、".join("%s %g" % (k, v)
                          for k, v in sorted(ru["width_mm"].items()))
    layer_txt = "；".join("%s 仅 %s" % (k, "/".join(v))
                          for k, v in sorted(ru["allowed_layers"].items())
                          if k != "default")
    L.append("【规则】格点 %g mm；不同网络铜净距 ≥%g mm；线宽：%s；过孔 pad %g/"
             "hole %g mm（过孔焊盘在 3×3 邻域内同时占用两层=稀缺资源）%s"
             % (ru["grid_mm"], ru["clearance_mm"], width_txt,
                ru["via"]["pad_mm"], ru["via"]["hole_mm"],
                ("；类层约束：" + layer_txt) if layer_txt else ""))
    L.append("【成本模型（仅用于决策，禁止输出数值）】总成本 = 走线总长 + "
             "8×过孔数 + 0.5×拐弯数，越小越好。clock 类网只能走 F.Cu，必须从"
             "禁布区缝里过。")
    L.append("")
    L.append("【焊盘】")
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


def fmt_feedback(rd):
    m = rd["main"]
    lines = []
    if m.get("eval_timeout_main") or m.get("status") == "eval_timeout":
        lines.append("引擎实测：该方案单解超过时限，未出结果（沿用上轮 "
                     "standing）。")
    elif m["all_connected"]:
        lines.append("引擎实测：全部连通；总成本 %s" % m["objective"])
    else:
        lines.append("引擎实测：**未能全部连通（该方案 routing 失败，整跑终止）"
                     "**；失败网：%s。已布部分逐网贡献：" % m.get("failed_net"))
    if m.get("all_connected"):
        lines.append("逐网成本贡献（走线长 + 8×过孔 + 0.5×拐弯；过孔与拐弯顺序"
                     "敏感——先布走直、后布让路）：")
    for nid in m["order"]:
        c = (m.get("per_net") or {}).get(nid)
        if c:
            lines.append("  %s：长度 %s mm，过孔 %d，拐弯 %d，贡献 %s"
                         % (nid, round(c["length_mm"], 2), c["vias"],
                            c["bends"], c["contribution"]))
    if rd.get("probes"):
        lines.append("你的探针实测：")
        for p in rd["probes"]:
            if p.get("eval_timeout"):
                lines.append("  [%s] 单解超过时限，未出结果" % p["label"])
            elif p["all_connected"]:
                lines.append("  [%s] 总成本 %s（全部连通）"
                             % (p["label"], p["objective"]))
            else:
                lines.append("  [%s] **routing 失败**（失败网 %s）"
                             % (p["label"], p.get("failed_net")))
    return lines


def channel_header(arm, rnd):
    if arm == "TIER":
        return ("# EXP-S2 第 %d 轮（TIER 档位臂）\n\n"
                "你在多轮迭代中引导一个确定性搜索式布线引擎：它把你给的档位分配"
                "展开成布线顺序（1 档最先布，同档按 net_id 字典序）逐网布线并实测"
                "回报；先布走直、后布让路，你依据实测修订档位分配。铁律：只给档位"
                "与探针点名，不输出任何数值。\n" % rnd)
    if arm == "WAVE":
        return ("# EXP-S2 第 %d 轮（WAVE 波次臂）\n\n"
                "你在多轮迭代中引导一个确定性搜索式布线引擎：它把你给的波次划分"
                "展开成布线顺序（波次依次布，波内按 net_id 字典序；须 2–3 个非空"
                "波）逐网布线并实测回报，你依据实测修订波次划分。铁律：只给波次与"
                "探针点名，不输出任何数值。\n" % rnd)
    return ("# EXP-S2 第 %d 轮（FULL 全序臂）\n\n"
            "你在多轮迭代中引导一个确定性搜索式布线引擎：它严格按你给的顺序逐网"
            "布线并实测回报；你依据实测修订策略。铁律：只给排序与探针点名，不输出"
            "任何数值。\n" % rnd)


def default_strategy(arm, sid):
    n = len(s2.net_ids_of(sid))
    return {
        "TIER": "字典序切成三档（前 ⌈n/3⌉ 个 T1，次 ⌈(n−⌈n/3⌉)/2⌉ 个 T2，"
                "余 T3；展开后=字典序）",
        "WAVE": "字典序切成两等波（前 ⌈n/2⌉ 个第 1 波，余第 2 波；展开后="
                "字典序）",
        "FULL": "net_id 字典序：%s" % "、".join(s2.baseline_order(sid))}[arm]


def contract_text(arm, sid):
    sid_n = len(s2.net_ids_of(sid))
    b = probe_budget(arm, sid)
    tail = ("probes 是你想让引擎代测的至多 %d 个同空间备选提案（可不填）——用它"
            "检验你的顺序敏感假设，下一轮你会拿到每个探针的实测结果。" % b)
    if arm == "TIER":
        return ("【通道与输出合同】你只掌控一项：**布线档位**——给每个网指定档位 "
                "1/2/3（1=最先布），三档都必须至少有一个网。展开规则（确定性）："
                "先布档位 1 的全部网（按编号升序），再档位 2，再档位 3。"
                "先布的网可走直路，后布的让路绕行。\n"
                "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本"
                "数值），单个对象：{\"scenario_id\": \"%s\", \"tiers\": "
                "{\"<net_id>\": <1|2|3>, …（每网恰一个，三档全非空）}, "
                "\"reason\": \"<一句话>\", \"probes\": [{\"label\": "
                "\"<短名>\", \"tiers\": {…同形}}…]}。1=最先布，3=最后布。%s"
                % (sid, tail))
    if arm == "WAVE":
        return ("【通道与输出合同】你只掌控一项：**布线波次**——把全部网络划分成"
                " 2–3 个有序非空波（第 1 波最先布）。展开规则（确定性）：波次依次"
                "布，波内按 net_id 字典序。先布的网可走直路，后布的让路绕行。\n"
                "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本"
                "数值），单个对象：{\"scenario_id\": \"%s\", \"waves\": "
                "[[\"<net_id>\", …], …] 恰 2–3 个非空波、覆盖全部 %d 个网络每个"
                "恰好一次}, \"reason\": \"<一句话>\", \"probes\": [{\"label\": "
                "\"<短名>\", \"waves\": […同形]}…]}。波次依次布，波内按 net_id "
                "字典序。%s" % (sid, sid_n, tail))
    return ("【通道与输出合同】你掌控**完整布线顺序**（每个网恰好一次）。引擎按"
            "你的顺序逐网布线：先布的可走直路，后布的让路绕行；任一网失败则整跑"
            "停止（无拆除重布）。层选择由引擎自动优化，你不可指定。\n"
            "【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
            "单个对象：{\"scenario_id\": \"%s\", \"route_order\": "
            "[\"<net_id>\", …完整排列每个恰好一次], \"reason\": \"<一句话>\", "
            "\"probes\": [{\"label\": \"<短名>\", \"route_order\": […]}…]}。"
            "probes=至多 %d 个备选排列（可不填）。%s" % (sid, b, tail))


def _pack_text(arm, sid, rnd):
    """裁决包全文（确定性；历史只含第 0..rnd−1 轮）。rnd ≤ 当前轮+1：允许
    重建旧轮包（历史轮次不可变 → 字节等，G-Q0 用）；操作侧的"只能打包下一
    轮"由 cmd_pack 另行强制。"""
    st = load_state(arm)
    sc_st = st["scenarios"][sid]
    if rnd < 1 or rnd > sc_st["round"] + 1:
        raise SystemExit("pack: 场景 %s 当前轮=%d，请求轮=%d 不可重建"
                         % (sid, sc_st["round"], rnd))
    nets = s2.net_ids_of(sid)
    L = [channel_header(arm, rnd).rstrip()]
    L.append("")
    L.append("# 排序裁决包 %s" % sid)
    L.append("")
    L.append("你是 PCB 布线裁决器。下面是一张 2 层板的完整机器事实（结构化文本，"
             "非图像）。任一网布线失败则整跑立即停止（无拆除重布）。请给出你认为"
             "最终总成本最低的方案。")
    L.append("")
    L.extend(board_facts(sid))
    L.append("")
    L.append("【网络清单】%s" % "、".join(nets))
    L.append("")
    L.append("【默认策略（R0 暖启动）】%s" % default_strategy(arm, sid))
    L.append("")
    L.append("【你此前各轮的提案与引擎实测】")
    for rr in range(0, rnd):
        rd = sc_st["rounds"][str(rr)]
        m = rd["main"]
        L.append("— 第 %d 轮 —" % rr)
        if rd.get("carried"):
            L.append("（该轮主提案%s，沿用上轮 standing；上轮方案与实测如下）"
                     % ("无效" if rd.get("invalid_main") else "单解超时"))
        if arm == "TIER" and m.get("tiers"):
            L.append("你的档位：%s" % fmt_tiers(m["tiers"]))
        if arm == "WAVE" and m.get("waves"):
            L.append("你的波次：%s" % fmt_waves(m["waves"]))
        if arm == "FULL":
            L.append("你的排序：%s" % "、".join(m["order"]))
        L.append("引擎展开布线序：%s" % "、".join(m["order"]))
        L.extend(fmt_feedback(rd))
    L.append("")
    L.append("【第 %d 轮任务】给出本场景的新提案（实测显示已无可改进时允许坚持"
             "原案）。本场景你的探针预算=每轮至多 %d 个。" % (rnd,
                                                           probe_budget(arm,
                                                                        sid)))
    L.append(contract_text(arm, sid))
    return "\n".join(L) + "\n"


def cmd_pack(args):
    sc_st = load_state(args.arm)["scenarios"][args.sid]
    if args.round != sc_st["round"] + 1 or args.round > N_ROUNDS:
        raise SystemExit("pack: 场景 %s 当前轮=%d，请求轮=%d 不连续/越界"
                         % (args.sid, sc_st["round"], args.round))
    text = _pack_text(args.arm, args.sid, args.round)
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
    return json.loads(text), raw


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
        slate, _ = parse_slates(args.slates)
    except Exception as e:
        slate = None
        print("submit: json 解析失败 %s" % e)
    prev_main = sc_st["rounds"][str(sc_st["round"])]["main"]
    B = probe_budget(args.arm, args.sid)
    rd = {"probes": [], "carried": False, "invalid_main": None,
          "eval_timeout_main": False, "probe_budget": B,
          "probes_ignored": 0}
    if slate is None:
        rd["invalid_main"] = "unparseable_json"
    elif slate.get("scenario_id") != args.sid:
        rd["invalid_main"] = "sid_mismatch"
    else:
        main_ex = EXPANDERS[args.arm](args.sid,
                                      proposal_of(slate, args.arm))
        if main_ex is None:
            rd["invalid_main"] = "invalid_proposal_for_channel"
        else:
            main_r = measure(args.sid, main_ex["order"],
                             "S2-%s-R%d" % (args.arm, args.round))
            if main_r.get("eval_timeout"):
                st["eval_timeouts"] = st.get("eval_timeouts", 0) + 1
                rd["eval_timeout_main"] = True
                rd["carried"] = True
                rd["main"] = dict(prev_main)
                print("submit: %s-%s round %d eval_timeout（沿用 standing）"
                      % (args.arm, args.sid, args.round))
            elif main_r.get("child_error"):
                rd["invalid_main"] = "solver_error"
                print("submit: %s-%s round %d solver_error %s"
                      % (args.arm, args.sid, args.round,
                         main_r["child_error"]))
            else:
                main_r["carried"] = False
                main_r["invalid_main"] = None
                main_r["eval_timeout_main"] = False
                main_r["tiers"] = main_ex.get("tiers")
                main_r["waves"] = main_ex.get("waves")
                main_r["proposal"] = proposal_of(slate, args.arm)
                rd["main"] = main_r
                # 探针：≤B，序数封印（按给出顺序取前 B 个合法且展开序不重复者）
                seen = {"|".join(main_ex["order"])}
                probes = slate.get("probes") or []
                if isinstance(probes, dict):
                    probes = [probes]
                for p in probes:
                    if not isinstance(p, dict):
                        continue
                    if len(rd["probes"]) >= B:
                        rd["probes_ignored"] += 1
                        continue
                    ex = EXPANDERS[args.arm](args.sid,
                                             proposal_of(p, args.arm))
                    if ex is None:
                        continue
                    key = "|".join(ex["order"])
                    if key in seen:
                        continue
                    seen.add(key)
                    r = measure(args.sid, ex["order"],
                                "S2-%s-R%d-PROBE" % (args.arm, args.round))
                    r["label"] = str(p.get("label", "p"))[:24]
                    r["order"] = ex["order"]
                    r["tiers"] = ex.get("tiers")
                    r["waves"] = ex.get("waves")
                    r["proposal"] = proposal_of(p, args.arm)
                    rd["probes"].append(r)
    if rd.get("invalid_main"):
        st["invalid_count"] += 1
        rd["carried"] = True
        rd["main"] = dict(prev_main)
        _write(os.path.join(run_dir, "round-%d-INVALID.json" % args.round),
               {"reason": rd["invalid_main"]})
        print("submit: INVALID 主提案（累计无效 %d，沿用 standing）"
              % st["invalid_count"])
    sc_st["rounds"][str(args.round)] = rd
    sc_st["round"] = args.round
    save_state(args.arm, st)
    if not rd.get("carried"):
        print("submit: %s-%s round %d ok（main sat=%s obj=%s, probes=%d）"
              % (args.arm, args.sid, args.round,
                 rd["main"]["all_connected"], rd["main"]["objective"],
                 len(rd["probes"])))


# ---------------------------------------------------------------- report

def rank_key(r):
    return r["objective"] if r.get("all_connected") else float("inf")


def _final_main(st, sid):
    sc_st = st["scenarios"][sid]
    return sc_st["rounds"][str(sc_st["round"])]["main"]


def cmd_report(_):
    sids = accepted_sids()
    ref = _load(os.path.join(P0, "reference.json"))["per"]
    states = {a: load_state(a) for a in ARMS}
    rep = {"scenarios": sids, "arms": {}, "gates": {}}

    # ---- G-Q0 确定性重放
    q0 = {"expand_determinism": True, "pack_replay": [], "engine_replay": []}
    tier_probe = []
    for t in ("n08", "n12", "n16"):
        cand = [s for s in sids if tier_of(s) == t]
        if cand:
            tier_probe.append(cand[0])
    for arm in ARMS:
        for sid in tier_probe:
            e1 = EXPANDERS[arm](sid, warm_proposal(arm, sid))
            e2 = EXPANDERS[arm](sid, warm_proposal(arm, sid))
            if json.dumps(e1, sort_keys=True) != json.dumps(e2, sort_keys=True):
                q0["expand_determinism"] = False
        for sid in sids:
            sc_st = states[arm]["scenarios"][sid]
            for rr in range(1, sc_st["round"] + 1):
                pth = os.path.join(ROUNDS, "round-%d" % rr,
                                   "%s-%s-pack.md" % (arm, sid))
                if os.path.exists(pth):
                    disk = open(pth, encoding="utf-8", newline="").read()
                    try:
                        regen = _pack_text_hist(arm, sid, rr)
                        q0["pack_replay"].append(
                            {"arm": arm, "sid": sid, "round": rr,
                             "byte_equal": disk == regen})
                    except SystemExit:
                        pass
                    break
    for sid in tier_probe:
        r0 = measure(sid, s2.baseline_order(sid), "S2-Q0-REPLAY")
        m0 = states["TIER"]["scenarios"][sid]["rounds"]["0"]["main"]
        q0["engine_replay"].append({
            "sid": sid, "objective_equal":
                r0["objective"] == m0["objective"],
            "per_net_equal": r0["per_net"] == m0["per_net"]})
    q0["pack_replay_all_equal"] = all(x["byte_equal"] for x
                                      in q0["pack_replay"])
    q0["engine_replay_all_equal"] = all(
        x["objective_equal"] and x["per_net_equal"]
        for x in q0["engine_replay"])
    print("G-Q0: 展开确定=%s pack重放=%s（%d 份）引擎重放=%s（%d 场景）"
          % (q0["expand_determinism"], q0["pack_replay_all_equal"],
             len(q0["pack_replay"]), q0["engine_replay_all_equal"],
             len(q0["engine_replay"])))
    rep["gates"]["G-Q0"] = q0

    # ---- G-Q1 非劣 / G-Q2' 逐场景配对 closure
    rows = []
    for sid in sids:
        base = states[ARMS[0]]["scenarios"][sid]["rounds"]["0"]["main"][
            "objective"]
        row = {"sid": sid, "tier": tier_of(sid), "base": base,
               "ref": ref[sid]["ref"]}
        for arm in ARMS:
            st = states[arm]
            fin = _final_main(st, sid)
            row[arm] = fin["objective"] if fin["all_connected"] else None
            row[arm + "_sat"] = fin["all_connected"]
            denom = base - row["ref"]
            if not fin["all_connected"]:
                row[arm + "_closure"] = -1
            elif denom > 1e-9:
                row[arm + "_closure"] = round((base - fin["objective"])
                                              / denom, 4)
            else:
                row[arm + "_closure"] = "no_headroom"
        rows.append(row)
    print("\n== G-Q1/G-Q2' 逐场景表（closure=(基线−终轮)/(基线−参照)；"
          "终轮非 SAT 记 −1）==")
    print("%-10s %8s %8s | %8s %8s %8s | %7s %7s %7s" % (
        "sid", "base", "ref", "TIER", "WAVE", "FULL",
        "clT", "clW", "clF"))
    for r in rows:
        print("%-10s %8s %8s | %8s %8s %8s | %7s %7s %7s" % (
            r["sid"], r["base"], r["ref"],
            r["TIER"] if r["TIER_sat"] else "UNSAT",
            r["WAVE"] if r["WAVE_sat"] else "UNSAT",
            r["FULL"] if r["FULL_sat"] else "UNSAT",
            r["TIER_closure"], r["WAVE_closure"], r["FULL_closure"]))
    for arm in ARMS:
        reg = [r["sid"] for r in rows if r[arm] is not None
               and r[arm] > r["base"] * 1.01 + 1e-9]
        unsat = [r["sid"] for r in rows if not r[arm + "_sat"]]
        cl = [r[arm + "_closure"] for r in rows
              if isinstance(r[arm + "_closure"], (int, float))
              and r[arm + "_closure"] != -1]
        rep["arms"][arm] = {
            "regression_sids": reg, "regression_count": len(reg),
            "unsat_finals": unsat,
            "mean_closure": round(sum(cl) / len(cl), 4) if cl else None,
            "n_valid_closure": len(cl)}
        print("G-Q1 %s：回退>1%% 场景=%d %s；非 SAT 终局=%d；均值 closure=%s"
              "（有效 %d/%d）" % (arm, len(reg), reg or "", len(unsat),
                                rep["arms"][arm]["mean_closure"], len(cl),
                                len(rows)))
    # G-Q2' 配对方向（H1）：TIER vs FULL、WAVE vs FULL
    print("\n== G-Q2' 配对方向（H1；closure 比较，含 −1 哨兵）==")
    pair = {}
    for t in ("n08", "n12", "n16"):
        sub = [r for r in rows if r["tier"] == t]
        entry = {"n": len(sub)}
        for ch in ("TIER", "WAVE"):
            wins = sum(1 for r in sub
                       if _clv(r[ch + "_closure"]) > _clv(r["FULL_closure"]))
            loss = sum(1 for r in sub
                       if _clv(r[ch + "_closure"]) < _clv(r["FULL_closure"]))
            entry[ch] = {"gt_full": wins, "lt_full": loss,
                         "eq": len(sub) - wins - loss}
        pair[t] = entry
        print("  %s: TIER>Full %d / < %d / = %d；WAVE>Full %d / < %d / = %d"
              % (t, entry["TIER"]["gt_full"], entry["TIER"]["lt_full"],
                 entry["TIER"]["eq"], entry["WAVE"]["gt_full"],
                 entry["WAVE"]["lt_full"], entry["WAVE"]["eq"]))
    rep["gates"]["G-Q2p"] = pair

    # ---- G-Q3 探针机制
    gq3 = {"probes": 0, "informative": 0, "beat_main": 0, "promoted": 0,
           "eval_timeout": 0}
    for arm in ARMS:
        st = states[arm]
        for sid in sids:
            sc_st = st["scenarios"][sid]
            for rr in range(1, sc_st["round"] + 1):
                rd = sc_st["rounds"][str(rr)]
                main = rd["main"]
                nxt = sc_st["rounds"].get(str(rr + 1))
                for p in rd["probes"]:
                    gq3["probes"] += 1
                    if p.get("eval_timeout"):
                        gq3["eval_timeout"] += 1
                        continue
                    if p["all_connected"] == main["all_connected"] \
                            and p["objective"] != main["objective"]:
                        gq3["informative"] += 1
                    if rank_key(p) < rank_key(main):
                        gq3["beat_main"] += 1
                    if nxt and not nxt.get("carried") \
                            and nxt["main"]["order"] == p["order"]:
                        gq3["promoted"] += 1
    print("\nG-Q3: probes=%d informative=%d beat_main=%d promoted=%d "
          "eval_timeout=%d" % (gq3["probes"], gq3["informative"],
                               gq3["beat_main"], gq3["promoted"],
                               gq3["eval_timeout"]))
    rep["gates"]["G-Q3"] = gq3

    # ---- H2 全序退化描述表
    print("\n== H2 描述表（invalid/停滞/轮至最优/非SAT 终局/超时）==")
    h2 = {}
    for arm in ARMS:
        st = states[arm]
        h2[arm] = {"invalid_mains": st["invalid_count"],
                   "eval_timeouts": st.get("eval_timeouts", 0),
                   "per_tier": {}}
        for t in ("n08", "n12", "n16"):
            sub = [s for s in sids if tier_of(s) == t]
            stag = 0
            best_rounds = []
            unsat = 0
            for s in sub:
                sc_st = st["scenarios"][s]
                best_v, best_r = None, None
                for rr in range(0, sc_st["round"] + 1):
                    m = sc_st["rounds"][str(rr)]["main"]
                    if rr >= 1 and not sc_st["rounds"][str(rr)].get(
                            "carried") \
                            and m["order"] == sc_st["rounds"][str(rr - 1)][
                                "main"]["order"]:
                        stag += 1
                    if m["all_connected"] and (
                            best_v is None or m["objective"] < best_v - 1e-9):
                        best_v, best_r = m["objective"], rr
                if best_r is not None:
                    best_rounds.append(best_r)
                if not _final_main(st, s)["all_connected"]:
                    unsat += 1
            h2[arm]["per_tier"][t] = {
                "n_scen": len(sub), "stagnation_rounds": stag,
                "mean_round_to_best": round(sum(best_rounds)
                                            / len(best_rounds), 2)
                if best_rounds else None,
                "unsat_finals": unsat}
            print("  %s %s: 停滞轮=%d 轮至最优均值=%s 非SAT终局=%d"
                  % (arm, t, stag,
                     h2[arm]["per_tier"][t]["mean_round_to_best"], unsat))
        print("  %s 合计: invalid_mains=%d eval_timeouts=%d"
              % (arm, st["invalid_count"], st.get("eval_timeouts", 0)))
    rep["gates"]["H2"] = h2

    # ---- H3 探针预算两档对比
    print("\n== H3 描述表（B=5 vs B=3；B=5 字母={a,b,c}[(ch+tier)%%3]）==")
    h3 = {}
    for arm in ARMS:
        h3[arm] = {}
        for t in ("n08", "n12", "n16"):
            sub = [s for s in sids if tier_of(s) == t]
            rows3 = []
            for s in sub:
                st = states[arm]
                sc_st = st["scenarios"][s]
                b = sc_st["probe_budget"]
                p_tot = p_inf = p_beat = 0
                for rr in range(1, sc_st["round"] + 1):
                    rd = sc_st["rounds"][str(rr)]
                    main = rd["main"]
                    for p in rd["probes"]:
                        p_tot += 1
                        if p.get("eval_timeout"):
                            continue
                        if p["all_connected"] == main["all_connected"] \
                                and p["objective"] != main["objective"]:
                            p_inf += 1
                        if rank_key(p) < rank_key(main):
                            p_beat += 1
                row = {"sid": s, "B": b, "probes": p_tot,
                       "informative": p_inf, "beat_main": p_beat,
                       "final_closure": next(
                           r[arm + "_closure"] for r in rows
                           if r["sid"] == s)}
                rows3.append(row)
                print("  %s %s B=%d probes=%d informative=%d beat=%d "
                      "closure=%s" % (arm, s, b, p_tot, p_inf, p_beat,
                                      row["final_closure"]))
            hi = [r for r in rows3 if r["B"] == PROBE_B_HIGH]
            lo = [r for r in rows3 if r["B"] == PROBE_B_LOW]
            h3[arm][t] = {
                "rows": rows3,
                "B5": {"n": len(hi), "probes": sum(r["probes"] for r in hi),
                       "informative": sum(r["informative"] for r in hi)},
                "B3": {"n": len(lo), "probes": sum(r["probes"] for r in lo),
                       "informative": sum(r["informative"] for r in lo)}}
    rep["gates"]["H3"] = h3

    # ---- 完成度（partial 语义：仅停臂/预算触发，无时钟触发）
    rounds_done = {arm: min(states[arm]["scenarios"][s]["round"]
                            for s in sids) for arm in ARMS}
    partial = any(v < N_ROUNDS for v in rounds_done.values())
    reason = {"stopped_arm": [a for a in ARMS if states[a]["invalid_count"]
                              >= 2], "eval_timeouts": {
        a: states[a].get("eval_timeouts", 0) for a in ARMS}}
    print("\nrounds_completed(min per arm)=%s；partial=%s（触发源=%s；"
          "无时钟触发——用户 2026-09-19 令撤销 09:00 硬停）"
          % (rounds_done, partial, json.dumps(reason, ensure_ascii=False)))
    rep["rounds_completed"] = rounds_done
    rep["partial"] = {"flag": partial, "reason": reason}
    _write(os.path.join(OUT, "report.json"), rep)
    print("report -> %s" % os.path.join(OUT, "report.json"))


def _clv(x):
    """closure 值归一：no_headroom/None → 视为无信息（按 0 计），−1 保留。"""
    if isinstance(x, (int, float)):
        return float(x)
    return 0.0


def _pack_text_hist(arm, sid, rnd):
    """G-Q0 用：以当前 state 重建历史第 rnd 轮包文本（历史轮次不变则字节等）。"""
    return _pack_text(arm, sid, rnd)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("pack")
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--sid", required=True)
    p.add_argument("--round", type=int, required=True)
    s = sub.add_parser("submit")
    s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--sid", required=True)
    s.add_argument("--round", type=int, required=True)
    s.add_argument("--slates", required=True)
    sub.add_parser("report")
    args = ap.parse_args()
    {"init": cmd_init, "pack": cmd_pack, "submit": cmd_submit,
     "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
