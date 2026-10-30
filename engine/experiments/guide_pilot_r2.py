# -*- coding: utf-8 -*-
"""GUIDE-PILOT-R2 粗粒度导引通道三臂执行器（判据见 GUIDE-PILOT-R2-PREREG-2026-09-16.md）。

只读复用 seat_ab_r1a（其自身只读复用 pcbflow.v4exp）；零写入 pcbflow/datasets。
三臂：GUIDE-3 档位（tiers→(tier,net_id) 排序）、GUIDE-4 层计划（layer_preferences 硬约束，
布线序固定字典序）、GUIDE-5 波次（2–3 非空波，波内字典序）。
产物根：<ENGINE_ROOT>/out/guide-pilot-r2/
子命令：
  init    R0 暖启动（S3 序冻结公式编码后重测）+ 通道天花板枚举（--ceilings 单独跑）
  pack    --arm A --round k --sid S：生成第 k 轮盲包（agent 可见；无基线/oracle/天花板/门值）
  submit  --arm A --round k --sid S --slates <json>：校验+展开+实测主提案与探针，推进状态
  report  终判（仅主会话；读 oracle/baseline/R1 参照/天花板算 G-Q0..Q3）
"""
import argparse
import hashlib
import itertools
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seat_ab_r1a as sa  # noqa: E402

OUT = os.path.join(sa.ROOT, "out", "guide-pilot-r2")
M_SIDS = ["cal-f2-13", "cal-f2-15", "cal-f4-16", "cal-f4-13", "cal-f4-15"]
PROBE_BUDGET = 3
N_ROUNDS = 4
ARMS = ("GUIDE-3", "GUIDE-4", "GUIDE-5")
S3_MEASURE = os.path.join(sa.OUT, "model-runs", "S3-measure.json")
R1_G2_STATE = os.path.join(sa.ROOT, "out", "guide-pilot-r1", "state", "GUIDE-2.json")
TIER_VALS = (1, 2, 3)


# ---------------------------------------------------------------- 展开/校验

def expand_tiers(sid, tiers):
    """返回 (ok, order 或 reason)。三档全部非空；每网恰一档 ∈{1,2,3}。"""
    nets = sa.net_ids_of(sid)
    if not isinstance(tiers, dict):
        return False, "tiers_not_object"
    if sorted(map(str, tiers.keys())) != nets:
        return False, "tiers_not_full_coverage"
    vals = {}
    for k, v in tiers.items():
        if v not in TIER_VALS:
            return False, "bad_tier_value:%s=%r" % (k, v)
        vals[str(k)] = v
    if set(vals.values()) != set(TIER_VALS):
        return False, "tiers_must_use_all_three"
    order = sorted(nets, key=lambda n: (vals[n], n))
    return True, order


def expand_waves(sid, waves):
    """返回 (ok, order 或 reason)。恰 2–3 个非空波，覆盖全部网各一次。"""
    nets = sa.net_ids_of(sid)
    if not isinstance(waves, list) or not (2 <= len(waves) <= 3):
        return False, "waves_count_must_be_2_or_3"
    flat = []
    for w in waves:
        if not isinstance(w, list) or not w:
            return False, "wave_not_nonempty_list"
        flat.extend(str(x) for x in w)
    if sorted(flat) != nets:
        return False, "waves_not_full_coverage"
    order = []
    for w in waves:
        order.extend(sorted(str(x) for x in w))
    return True, order


def expand_plan(sid, plan):
    """返回 (ok, (order, prefs) 或 reason)。每网 "F.Cu" 或 null；序固定字典序。"""
    nets = sa.net_ids_of(sid)
    if not isinstance(plan, dict):
        return False, "layer_plan_not_object"
    if sorted(map(str, plan.keys())) != nets:
        return False, "layer_plan_not_full_coverage"
    prefs = []
    for k, v in plan.items():
        if v is None:
            continue
        if v != "F.Cu":
            return False, "bad_plan_value:%s=%r" % (k, v)
        prefs.append({"net_id": str(k), "layers": ["F.Cu"]})
    return True, (nets, prefs)


def expand(arm, sid, proposal):
    if arm == "GUIDE-3":
        return expand_tiers(sid, proposal.get("tiers"))
    if arm == "GUIDE-5":
        return expand_waves(sid, proposal.get("waves"))
    return expand_plan(sid, proposal.get("layer_plan"))


def solve_full(sid, order, prefs, tag):
    req = {"route_order": [str(x) for x in order], "group": tag}
    if prefs:
        req["layer_preferences"] = prefs
    r = sa.router.solve_board(sa.board_of(sid), req)
    m = r["metrics"]
    out = {"route_order": [str(x) for x in order],
           "objective": m["objective"], "all_connected": m["all_connected"],
           "status": r["status"], "violations": m["violations"],
           "search_nodes": m["search_nodes"],
           "per_net_contribution": sa.net_contributions(r)}
    if "failed_at" in r:
        out["failed_at"] = r["failed_at"]
    used = {}
    for rt in r["routes"]:
        used.setdefault(rt["net_id"], set()).add(rt["layer"])
    out["per_net_layers"] = {k: sorted(v) for k, v in sorted(used.items())}
    return out


def proposal_repr(arm, proposal):
    """agent 可读的单行提案描述。"""
    if arm == "GUIDE-3":
        t = proposal["tiers"]
        return "档位 " + "、".join(
            "%s→%d档" % (n, t[n]) for n in sorted(t, key=lambda x: (t[x], x)))
    if arm == "GUIDE-5":
        return "波次 " + " ".join(
            "第%d波[%s]" % (i + 1, ",".join(sorted(w))) for i, w in enumerate(proposal["waves"]))
    p = proposal["layer_plan"]
    return "层计划 " + "、".join(
        "%s→%s" % (n, "仅F.Cu" if p[n] == "F.Cu" else "自动") for n in sorted(p))


def warmup_proposal(arm, sid, s3_order):
    """R0 冻结编码公式（prereg §3）。返回 (proposal, order, prefs)。"""
    n = len(s3_order)
    if arm == "GUIDE-3":
        c1 = math.ceil(n / 3)
        c2 = math.ceil((n - c1) / 2)
        chunks = [s3_order[:c1], s3_order[c1:c1 + c2], s3_order[c1 + c2:]]
        tiers = {nid: i + 1 for i, ch in enumerate(chunks) for nid in ch}
        proposal = {"tiers": tiers}
        ok, order = expand_tiers(sid, tiers)
        assert ok
        return proposal, order, []
    if arm == "GUIDE-5":
        h = math.ceil(n / 2)
        proposal = {"waves": [s3_order[:h], s3_order[h:]]}
        ok, order = expand_waves(sid, proposal["waves"])
        assert ok
        return proposal, order, []
    proposal = {"layer_plan": {nid: None for nid in s3_order}}
    ok, op = expand_plan(sid, proposal["layer_plan"])
    assert ok
    return proposal, op[0], op[1]


# ---------------------------------------------------------------- 状态

def state_path(arm):
    return os.path.join(OUT, "state", "%s.json" % arm)


def load_state(arm):
    with open(state_path(arm), encoding="utf-8") as f:
        return json.load(f)


def save_state(arm, st):
    sa.write_json(state_path(arm), st)


def last_round(sc, upto=None):
    rs = sc["rounds"]
    if upto is None:
        return rs[-1]
    for r in reversed(rs):
        if r["round"] == upto:
            return r
    raise KeyError(upto)


def probe_rows(sc, rnd):
    return [p for p in sc["probes"] if p["round"] == rnd]


# ---------------------------------------------------------------- init / ceilings

def cmd_init(args):
    with open(S3_MEASURE, encoding="utf-8") as f:
        s3 = {r["scenario_id"]: r for r in json.load(f)["rows"]}
    for arm in ARMS:
        sc = {}
        for sid in M_SIDS:
            proposal, order, prefs = warmup_proposal(arm, sid, s3[sid]["route_order"])
            m = solve_full(sid, order, prefs, "GP2-%s-R0" % arm)
            sc[sid] = {"rounds": [dict(round=0, proposal=proposal, **m)], "probes": []}
        save_state(arm, {"arm": arm, "round": 0, "invalid_mains": 0, "scenarios": sc})
        for sid in M_SIDS:
            r0 = sc[sid]["rounds"][0]
            print("init %s %s: R0 obj=%g sat=%s order=%s" % (
                arm, sid, r0["objective"], r0["all_connected"], "、".join(r0["route_order"])))
    print("init: round=0 暖启动完成 for %s" % ", ".join(ARMS))


def _enum_channel(arm, sid):
    """穷举臂决策空间，返回 {展开键: (proposal, order, prefs)}（去重）。"""
    nets = sa.net_ids_of(sid)
    space = {}
    if arm == "GUIDE-3":
        for combo in itertools.product(TIER_VALS, repeat=len(nets)):
            tiers = dict(zip(nets, combo))
            ok, order = expand_tiers(sid, tiers)
            if ok and tuple(order) not in space:
                space[tuple(order)] = ({"tiers": tiers}, order, [])
    elif arm == "GUIDE-5":
        for k in (2, 3):
            for combo in itertools.product(range(k), repeat=len(nets)):
                waves = [[] for _ in range(k)]
                for nid, wi in zip(nets, combo):
                    waves[wi].append(nid)
                ok, order = expand_waves(sid, waves)
                if ok and tuple(order) not in space:
                    space[tuple(order)] = ({"waves": waves}, order, [])
    else:
        for combo in itertools.product(("F.Cu", None), repeat=len(nets)):
            plan = dict(zip(nets, combo))
            ok, op = expand_plan(sid, plan)
            if ok:
                key = (tuple(op[0]), tuple(map(json.dumps, op[1])))
                if key not in space:
                    space[key] = ({"layer_plan": plan}, op[0], op[1])
    return space


def cmd_ceilings(_):
    res = {}
    cache = {}
    for arm in ARMS:
        res[arm] = {}
        for sid in M_SIDS:
            space = _enum_channel(arm, sid)
            best = None
            sat = 0
            for key, (proposal, order, prefs) in sorted(space.items()):
                ck = (sid, tuple(order), json.dumps(prefs, sort_keys=True))
                if ck not in cache:
                    cache[ck] = solve_full(sid, order, prefs, "GP2-CEIL")
                m = cache[ck]
                if m["all_connected"]:
                    sat += 1
                    if best is None or m["objective"] < best["objective"]:
                        best = dict(m, proposal=proposal)
            res[arm][sid] = {"space_size": len(space), "sat_count": sat,
                             "ceiling": best["objective"] if best else None,
                             "argmin_proposal": best["proposal"] if best else None,
                             "argmin_order": best["route_order"] if best else None}
            print("ceil %s %s: space=%d sat=%d ceiling=%s" % (
                arm, sid, len(space), sat,
                best["objective"] if best else "NONE"))
    # G-Q0 重放确定性抽查：各臂 f2-13 argmin 重跑字节等
    for arm in ARMS:
        sid = "cal-f2-13"
        b = res[arm][sid]
        m1 = solve_full(sid, b["argmin_order"],
                        expand(arm, sid, b["argmin_proposal"])[1][1] if arm == "GUIDE-4" else [],
                        "GP2-REPLAY")
        assert abs(m1["objective"] - b["ceiling"]) < 1e-9, (arm, sid)
    sa.write_json(os.path.join(OUT, "ceilings", "ceilings.json"), res)
    print("ceilings -> %s" % os.path.join(OUT, "ceilings", "ceilings.json"))


# ---------------------------------------------------------------- pack

def channel_header(arm, rnd):
    if arm == "GUIDE-3":
        return ("# GUIDE-PILOT-R2 第 %d 轮（GUIDE-3 档位臂）\n\n"
                "你在多轮迭代中引导一个确定性搜索式布线引擎：它把你给的档位分配展开成布线顺序"
                "（1 档最先布，同档按 net_id 字典序）逐网布线并实测回报；先布走直、后布让路，"
                "你依据实测修订档位分配。铁律：只给档位与探针点名，不输出任何数值。\n" % rnd)
    if arm == "GUIDE-4":
        return ("# GUIDE-PILOT-R2 第 %d 轮（GUIDE-4 层计划臂）\n\n"
                "你在多轮迭代中引导一个确定性搜索式布线引擎：布线顺序由引擎固定为 net_id 字典序；"
                "你决定每张网的层计划——仅顶层（F.Cu，该网禁止过孔、禁止走底层）或自动（引擎自选层与过孔）。"
                "引擎逐网布线并实测回报，你依据实测修订层计划。铁律：只给层计划与探针点名，不输出任何数值。\n" % rnd)
    return ("# GUIDE-PILOT-R2 第 %d 轮（GUIDE-5 波次臂）\n\n"
            "你在多轮迭代中引导一个确定性搜索式布线引擎：它把你给的波次划分展开成布线顺序"
            "（波次依次布，波内按 net_id 字典序；须 2–3 个非空波）逐网布线并实测回报；"
            "你依据实测修订波次划分。铁律：只给波次与探针点名，不输出任何数值。\n" % rnd)


def ledger_lines(arm, sid, sc, prev_round):
    nets = sa.net_ids_of(sid)
    prev = last_round(sc, prev_round)
    lines = ["【你上一轮（第 %d 轮）的提案与引擎实测】" % prev_round,
             "你上轮提案：%s" % proposal_repr(arm, prev["proposal"]),
             "引擎展开布线序：%s" % "、".join(prev["route_order"]),
             "引擎实测：总成本 %g；全部连通：%s；违例：%s" % (
                 prev["objective"], "是" if prev["all_connected"] else "否",
                 json.dumps(prev["violations"], ensure_ascii=False, sort_keys=True))]
    lines.append("逐网成本贡献（走线长 + 8×过孔 + 0.5×拐弯；重成本集中在后布/受挤压的网络就值得"
                 "提前或给它留层）：")
    for nid in nets:
        c = prev["per_net_contribution"].get(nid) or {}
        lines.append("  %s：长度 %g mm，过孔 %d，拐弯 %d，贡献 %g" % (
            nid, c.get("length_mm", 0.0), c.get("vias", 0), c.get("bends", 0),
            c.get("contribution", 0.0)))
    if arm == "GUIDE-4":
        lay = prev.get("per_net_layers", {})
        lines.append("逐网实际用层（层计划是否咬合看这里）：")
        for nid in nets:
            lines.append("  %s：%s" % (nid, "/".join(lay.get(nid, [])) or "未布"))
    pr = probe_rows(sc, prev_round)
    if pr:
        lines.append("你上轮点名的探针（引擎实测，未影响你的主提案）：")
        for p in pr:
            lines.append("  探针「%s」%s → 总成本 %g" % (
                p["label"], proposal_repr(arm, p["proposal"]), p["objective"]))
    return lines


def channel_contract(arm, sid):
    n = len(sa.net_ids_of(sid))
    tail = ("probes 是你想让引擎代测的至多 %d 个同空间备选提案（可不填）——用它检验你的假设，"
            "下一轮你会拿到每个探针的实测总成本。" % PROBE_BUDGET)
    if arm == "GUIDE-3":
        return ("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），单个对象："
                '{"scenario_id": "%s", "tiers": {"<net_id>": 1或2或3, …全部 %d 个网络每个恰好一次，'
                '三个档位每档至少一网}, "reason": "<一句话>", "probes": '
                '[{"label": "<短名>", "tiers": {…同形}}…]}。1=最先布，3=最后布。%s' % (sid, n, tail))
    if arm == "GUIDE-4":
        return ("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），单个对象："
                '{"scenario_id": "%s", "layer_plan": {"<net_id>": "F.Cu" 或 null, …全部 %d 个网络'
                '每个恰好一次}, "reason": "<一句话>", "probes": '
                '[{"label": "<短名>", "layer_plan": {…同形}}…]}。"F.Cu"=该网只许走顶层（禁过孔），'
                "null=引擎自动。%s" % (sid, n, tail))
    return ("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），单个对象："
            '{"scenario_id": "%s", "waves": [["<net_id>", …], …] 恰 2–3 个非空波、覆盖全部 %d 个'
            '网络每个恰好一次}, "reason": "<一句话>", "probes": '
            '[{"label": "<短名>", "waves": […同形]}…]}。波次依次布，波内按 net_id 字典序。%s' % (
                sid, n, tail))


def cmd_pack(args):
    st = load_state(args.arm)
    assert st["round"] == args.round - 1, "state.round=%d, want pack for round %d" % (
        st["round"], args.round)
    assert args.sid in M_SIDS, args.sid
    rd = os.path.join(OUT, "rounds", "round-%d" % args.round)
    os.makedirs(rd, exist_ok=True)
    base = sa.build_package_text(args.sid).split("【输出合同】")[0].rstrip()
    lines = [channel_header(args.arm, args.round), base, "",
             "\n".join(ledger_lines(args.arm, args.sid, st["scenarios"][args.sid],
                                    args.round - 1)), "",
             "【第 %d 轮任务】给出本场景的新提案（实测显示已无可改进时允许坚持原提案）。"
             % args.round, "", channel_contract(args.arm, args.sid)]
    text = "\n".join(lines)
    path = os.path.join(rd, "%s-%s-pack.md" % (args.arm, args.sid))
    open(path, "w", encoding="utf-8").write(text)
    print("pack %s %s round %d -> %s (%d bytes)" % (
        args.arm, args.sid, args.round, path, len(text)))


# ---------------------------------------------------------------- submit

def proposal_valid(arm, sid, e):
    """返回 (proposal 或 None, invalid_reason 或 None)。"""
    if arm == "GUIDE-3":
        key = "tiers"
    elif arm == "GUIDE-4":
        key = "layer_plan"
    else:
        key = "waves"
    if e.get(key) is None:
        return None, "missing_" + key
    ok, res = expand(arm, sid, e)
    if not ok:
        return None, res
    return {key: e[key]}, None


def cmd_submit(args):
    st = load_state(args.arm)
    with open(args.slates, encoding="utf-8") as f:
        payload = json.load(f)
    e = payload[0] if isinstance(payload, list) else payload
    sid = e.get("scenario_id") or args.sid
    assert sid == args.sid, "sid mismatch: %s vs %s" % (sid, args.sid)
    sc = st["scenarios"][sid]
    last = sc["rounds"][-1]["round"]
    assert last == args.round - 1, "sid=%s last_round=%d want %d" % (sid, last, args.round - 1)
    rd = os.path.join(OUT, "rounds", "round-%d" % args.round)
    os.makedirs(rd, exist_ok=True)
    results = {"arm": args.arm, "round": args.round, "scenario_id": sid,
               "main": None, "probes": [], "invalid": []}
    proposal, bad = proposal_valid(args.arm, sid, e)
    if bad:
        results["invalid"].append({"scenario_id": sid, "reason": bad})
        st["invalid_mains"] = st.get("invalid_mains", 0) + 1
    else:
        ok, res = expand(args.arm, sid, proposal)
        order, prefs = (res if args.arm == "GUIDE-4" else (res, []))
        main = solve_full(sid, order, prefs, "GP2-%s-R%d" % (args.arm, args.round))
        main["round"] = args.round
        main["proposal"] = proposal
        main["reason"] = e.get("reason", "")
        results["main"] = main
        for p in (e.get("probes") or [])[:PROBE_BUDGET + 1]:
            if len(results["probes"]) >= PROBE_BUDGET:
                results["invalid"].append({"scenario_id": sid, "reason": "probe_over_budget"})
                continue
            pp, pbad = proposal_valid(args.arm, sid, p)
            if pbad:
                results["invalid"].append({"scenario_id": sid, "reason": "bad_probe:" + pbad,
                                           "label": p.get("label", "")})
                continue
            ok, res = expand(args.arm, sid, pp)
            porder, pprefs = (res if args.arm == "GUIDE-4" else (res, []))
            pm = solve_full(sid, porder, pprefs, "GP2-%s-R%d-PROBE" % (args.arm, args.round))
            results["probes"].append({"label": p.get("label", ""), "proposal": pp,
                                      "objective": pm["objective"],
                                      "all_connected": pm["all_connected"],
                                      "route_order": pm["route_order"]})
        sc["rounds"].append(main)
        sc["probes"].extend([dict(round=args.round, **p) for p in results["probes"]])
    if all(any(r["round"] == args.round for r in st["scenarios"][s]["rounds"]) for s in M_SIDS):
        st["round"] = args.round
    save_state(args.arm, st)
    sa.write_json(os.path.join(rd, "%s-%s-result.json" % (args.arm, sid)), results)
    if results["main"]:
        m = results["main"]
        print("submit %s R%d %s: obj=%g sat=%s probes=%d invalid=%d" % (
            args.arm, args.round, sid, m["objective"], m["all_connected"],
            len(results["probes"]), len(results["invalid"])))
    else:
        print("submit %s R%d %s: INVALID (%s)" % (
            args.arm, args.round, sid, json.dumps(results["invalid"], ensure_ascii=False)))


# ---------------------------------------------------------------- report

def cmd_report(_):
    with open(os.path.join(sa.OUT, "p0", "oracle-summary.json"), encoding="utf-8") as f:
        oracle = {e["scenario_id"]: e["best_objective"] for e in json.load(f)}
    with open(os.path.join(sa.OUT, "p0", "baseline-summary.json"), encoding="utf-8") as f:
        base = {e["scenario_id"]: e["objective"] for e in json.load(f)}
    with open(os.path.join(OUT, "ceilings", "ceilings.json"), encoding="utf-8") as f:
        ceil = json.load(f)
    with open(R1_G2_STATE, encoding="utf-8") as f:
        r1g2 = json.load(f)
    states = {arm: load_state(arm) for arm in ARMS}

    def rfin(st, sid):
        """臂最终完成轮（G3 按 v1.1 停机条款收口于 R3，其余 R4）。"""
        return last_round(st["scenarios"][sid])["objective"]

    rep = {"gates": {}, "arms": {}, "arm_final_round": {}}
    for arm in ARMS:
        rep["arm_final_round"][arm] = states[arm]["round"]
    print("=== GUIDE-PILOT-R2 终判（主会话判读；臂口径=各自最终完成轮）===")
    print("%-12s %7s %7s %8s %8s %8s %8s  %s" % (
        "scenario", "oracle", "base", "G3-fin", "G4-fin", "G5-fin", "R1全序", "天花板G3/G4/G5"))
    for sid in M_SIDS:
        c = ceil["GUIDE-3"][sid]["ceiling"], ceil["GUIDE-4"][sid]["ceiling"], ceil["GUIDE-5"][sid]["ceiling"]
        print("%-12s %7g %7g %8g %8g %8g %8g  %g/%g/%g" % (
            sid, oracle[sid], base[sid], rfin(states["GUIDE-3"], sid),
            rfin(states["GUIDE-4"], sid), rfin(states["GUIDE-5"], sid),
            last_round(r1g2["scenarios"][sid], 4)["objective"], c[0], c[1], c[2]))
    for arm in ARMS:
        st = states[arm]
        reg = [s for s in M_SIDS if rfin(st, s) > base[s] * 1.01 + 1e-9]
        gq1 = "not_viable" if len(reg) >= 2 else ("with_regression" if len(reg) == 1 else "pass")
        cc, nohead = [], []
        for s in M_SIDS:
            b, c, g = base[s], ceil[arm][s]["ceiling"], rfin(st, s)
            if c is None or not last_round(st["scenarios"][s])["all_connected"]:
                cc.append(-1.0)
            elif abs(b - c) < 1e-9:
                nohead.append(s)
                continue
            else:
                cc.append((b - g) / (b - c))
        mean_cc = sum(cc) / len(cc) if cc else -1.0
        gq2 = "channel_extracts_value" if mean_cc >= 0.5 else "weak"
        n_inf = n_promo = n_tot = 0
        for s in M_SIDS:
            sc = st["scenarios"][s]
            for p in sc["probes"]:
                n_tot += 1
                rnd = p["round"]
                main_obj = last_round(sc, rnd)["objective"]
                if p["all_connected"] and p["objective"] < main_obj:
                    n_inf += 1
                    nxt = [r for r in sc["rounds"] if r["round"] == rnd + 1]
                    if nxt and nxt[0]["proposal"] == p["proposal"]:
                        n_promo += 1
        gq3 = "mechanism_active" if n_tot and n_inf / n_tot >= 0.25 else "mechanism_weak"
        verdict = ("viable_positive" if gq1 == "pass" and gq2 == "channel_extracts_value"
                   else "not_viable" if gq1 == "not_viable" or
                   (gq2 == "weak" and mean_cc < 0.25 and n_promo == 0) else "viable_weak")
        rep["arms"][arm] = {"regression_sids": reg, "gq1": gq1, "mean_cceil": mean_cc,
                            "no_headroom": nohead, "gq2": gq2, "probes_total": n_tot,
                            "probes_informative": n_inf, "probes_promotion": n_promo,
                            "gq3": gq3, "verdict": verdict,
                            "invalid_mains": st.get("invalid_mains", 0)}
        print("%s: G-Q1=%s(回退场景=%s) mean_cceil=%.3f G-Q2=%s 探针 %d/%d 有效 %d 晋升 "
              "G-Q3=%s invalid_mains=%d → %s" % (
                  arm, gq1, reg or "无", mean_cc, gq2, n_inf, n_tot, n_promo, gq3,
                  st.get("invalid_mains", 0), verdict))
    traj_ok = all(
        last_round(states[a]["scenarios"][s])["round"] == states[a]["round"]
        for a in ARMS for s in M_SIDS)
    rep["gates"]["G-Q0_replay_and_rounds_complete"] = traj_ok
    print("G-Q0 轮次完整: %s" % traj_ok)
    sa.write_json(os.path.join(OUT, "report.json"), rep)
    print("report -> %s" % os.path.join(OUT, "report.json"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("ceilings")
    p = sub.add_parser("pack")
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--round", required=True, type=int)
    p.add_argument("--sid", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--round", required=True, type=int)
    s.add_argument("--sid", required=True)
    s.add_argument("--slates", required=True)
    sub.add_parser("report")
    args = ap.parse_args()
    {"init": cmd_init, "ceilings": cmd_ceilings, "pack": cmd_pack,
     "submit": cmd_submit, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
