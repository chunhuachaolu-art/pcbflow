# -*- coding: utf-8 -*-
"""GUIDE-PILOT-R1 导引试点执行器（判据与流程见 GUIDE-PILOT-R1-PREREG-2026-09-16.md）。

只读复用 seat_ab_r1a（其自身只读复用 pcbflow.v4exp）；零写入 pcbflow/datasets。
产物根：<ENGINE_ROOT>/out/guide-pilot-r1/
子命令：
  init    从 R1a S3 已测数据建 round-0 暖启动状态（GUIDE-1/GUIDE-2 同起点）
  pack    --arm A --round k [--sid S]：生成第 k 轮盲包（agent 可见；无基线/oracle/门值）
  submit  --arm A --round k [--sid S] --slates <json>：校验+实测主 slate 与探针，推进状态
  report  终判（仅主会话；读 oracle/baseline 冻结事实算 G-P1..P4）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seat_ab_r1a as sa  # noqa: E402

OUT = os.path.join(sa.ROOT, "out", "guide-pilot-r1")
M_SIDS = ["cal-f2-13", "cal-f2-15", "cal-f4-16", "cal-f4-13", "cal-f4-15"]
PROBE_BUDGET = 3
N_ROUNDS = 4
ARMS = ("GUIDE-1", "GUIDE-2")
S3_OUT = os.path.join(sa.OUT, "model-runs", "S3", "output.json")
S3_MEASURE = os.path.join(sa.OUT, "model-runs", "S3-measure.json")


def state_path(arm):
    return os.path.join(OUT, "state", "%s.json" % arm)


def load_state(arm):
    with open(state_path(arm), encoding="utf-8") as f:
        return json.load(f)


def save_state(arm, st):
    sa.write_json(state_path(arm), st)


def arm_tag(arm):
    return "GP-%s" % arm


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


def scenario_section(sid, sc, prev_round, for_probe_arm):
    nets = sa.net_ids_of(sid)
    # 剥掉 R1a 包内嵌的单场景输出合同（与本试点的臂级合同冲突，以外层合同为准）
    base = sa.build_package_text(sid).split("【输出合同】")[0].rstrip()
    lines = [base, ""]
    prev = last_round(sc, prev_round)
    lines.append("【你上一轮（第 %d 轮）的提案与引擎实测】" % prev_round)
    lines.append("你上轮排序：%s" % "、".join(prev["route_order"]))
    lines.append("引擎实测：总成本 %g；全部连通：%s；违例：%s" % (
        prev["objective"], "是" if prev["all_connected"] else "否",
        json.dumps(prev["violations"], ensure_ascii=False, sort_keys=True)))
    lines.append("逐网成本贡献（走线长 + 8×过孔 + 0.5×拐弯；逐网贡献里的过孔与拐弯是顺序敏感的"
                 "——先布走直、后布让路；重成本集中在后布网络就值得提前）：")
    for nid in nets:
        c = prev["per_net_contribution"].get(nid) or {}
        lines.append("  %s：长度 %g mm，过孔 %d，拐弯 %d，贡献 %g" % (
            nid, c.get("length_mm", 0.0), c.get("vias", 0), c.get("bends", 0),
            c.get("contribution", 0.0)))
    pr = probe_rows(sc, prev_round)
    if pr:
        lines.append("你上轮点名的探针（引擎实测，未影响你的主排序）：")
        for p in pr:
            lines.append("  探针「%s」%s → 总成本 %g" % (
                p["label"], "、".join(p["route_order"]), p["objective"]))
    lines.append("")
    lines.append("【第 %d 轮任务】给出本%s的新排序提案（实测显示已无可改进时允许坚持原序）。"
                 % (prev_round + 1, "场景" if for_probe_arm else "全部 %d 个场景" % len(M_SIDS)))
    return "\n".join(lines)


def guide1_contract():
    return ("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
            "为 5 个对象的数组，每个："
            '{"scenario_id": "<cal-…>", "route_order": ["<net_id>", …完整排列每个恰好一次], '
            '"reason": "<一句话>"}，覆盖 %s。' % "、".join(M_SIDS))


def guide2_contract(sid):
    return ("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），单个对象："
            '{"scenario_id": "%s", "route_order": ["<net_id>", …完整排列每个恰好一次], '
            '"reason": "<一句话>", "probes": [{"label": "<短名>", "route_order": [<完整排列>]}…]}。'
            "probes 是你想让引擎代测的至多 %d 个备选排列（可不填）——用它检验你的顺序敏感假设，"
            "下一轮你会拿到每个探针的实测总成本。" % (sid, PROBE_BUDGET))


def cmd_init(_):
    with open(S3_OUT, encoding="utf-8") as f:
        slates = {e["scenario_id"]: e for e in json.load(f)}
    with open(S3_MEASURE, encoding="utf-8") as f:
        meas = {r["scenario_id"]: r for r in json.load(f)["rows"]}
    for arm in ARMS:
        sc = {}
        for sid in M_SIDS:
            s, m = slates[sid], meas[sid]
            assert sorted(s["route_order"]) == sa.net_ids_of(sid), sid
            sc[sid] = {"rounds": [{"round": 0, "route_order": list(s["route_order"]),
                                   "objective": m["objective"],
                                   "all_connected": m["all_connected"],
                                   "violations": m["violations"],
                                   "per_net_contribution": m["per_net_contribution"]}],
                       "probes": []}
        save_state(arm, {"arm": arm, "round": 0, "scenarios": sc})
    print("init: round=0 暖启动（S3 slate+账本）for %s" % ", ".join(ARMS))


def cmd_pack(args):
    st = load_state(args.arm)
    assert st["round"] == args.round - 1, "state.round=%d, want pack for round %d" % (
        st["round"], args.round)
    rd = os.path.join(OUT, "rounds", "round-%d" % args.round)
    os.makedirs(rd, exist_ok=True)
    header = ("# GUIDE-PILOT 第 %d 轮（%s）\n\n"
              "你在多轮迭代中引导一个确定性搜索式布线引擎：它严格按你给的顺序逐网布线并实测回报；"
              "你依据实测修订策略。铁律：只给排序与探针点名，不输出任何数值。\n"
              % (args.round, args.arm))
    if args.arm == "GUIDE-1":
        parts = [header]
        for sid in M_SIDS:
            parts.append(scenario_section(sid, st["scenarios"][sid], args.round - 1, False))
        parts.append(guide1_contract())
        text = "\n".join(parts)
        path = os.path.join(rd, "GUIDE-1-pack.md")
        open(path, "w", encoding="utf-8").write(text)
        print("pack GUIDE-1 round %d -> %s (%d bytes)" % (args.round, path, len(text)))
    else:
        sid = args.sid
        assert sid in M_SIDS, sid
        text = "\n".join([header,
                          scenario_section(sid, st["scenarios"][sid], args.round - 1, True),
                          guide2_contract(sid)])
        path = os.path.join(rd, "GUIDE-2-%s-pack.md" % sid)
        open(path, "w", encoding="utf-8").write(text)
        print("pack GUIDE-2 %s round %d -> %s (%d bytes)" % (sid, args.round, path, len(text)))


def validate_order(sid, order):
    return sorted(str(x) for x in order) == sa.net_ids_of(sid)


def measure_one(sid, order, tag):
    r = sa.solve(sid, [str(x) for x in order], tag)
    m = r["metrics"]
    return {"route_order": [str(x) for x in order], "objective": m["objective"],
            "all_connected": m["all_connected"], "status": r["status"],
            "violations": m["violations"], "search_nodes": m["search_nodes"],
            "per_net_contribution": sa.net_contributions(r)}


def cmd_submit(args):
    st = load_state(args.arm)
    with open(args.slates, encoding="utf-8") as f:
        payload = json.load(f)
    rd = os.path.join(OUT, "rounds", "round-%d" % args.round)
    results = {"arm": args.arm, "round": args.round, "scenarios": {}, "invalid": []}
    if args.arm == "GUIDE-1":
        entries = payload if isinstance(payload, list) else payload["slates"]
        by_sid = {e["scenario_id"]: e for e in entries}
        sids = M_SIDS
    else:
        e = payload[0] if isinstance(payload, list) else payload
        by_sid = {e["scenario_id"]: e}
        sids = [args.sid or e["scenario_id"]]
    # 每场景独立校验：上轮须为 args.round-1 且本轮未交（幂等，防重复推进）
    for sid in sids:
        last = st["scenarios"][sid]["rounds"][-1]["round"]
        assert last == args.round - 1, "sid=%s last_round=%d want %d" % (sid, last, args.round - 1)
    for sid in sids:
        e = by_sid.get(sid)
        if e is None:
            results["invalid"].append({"scenario_id": sid, "reason": "missing"})
            continue
        order = [str(x) for x in e.get("route_order", [])]
        if not validate_order(sid, order):
            results["invalid"].append({"scenario_id": sid, "reason": "not_a_complete_permutation",
                                       "got": order})
            continue
        main = measure_one(sid, order, "%s-R%d" % (arm_tag(args.arm), args.round))
        main["reason"] = e.get("reason", "")
        probes, over_budget = [], 0
        for p in (e.get("probes") or [])[:PROBE_BUDGET + 1]:
            porder = [str(x) for x in p.get("route_order", [])]
            if len(probes) >= PROBE_BUDGET:
                over_budget += 1
                continue
            if not validate_order(sid, porder):
                results["invalid"].append({"scenario_id": sid, "reason": "bad_probe",
                                           "label": p.get("label", "")})
                continue
            pm = measure_one(sid, porder, "%s-R%d-PROBE" % (arm_tag(args.arm), args.round))
            probes.append({"label": p.get("label", ""), "route_order": pm["route_order"],
                           "objective": pm["objective"],
                           "per_net_contribution": pm["per_net_contribution"]})
        results["scenarios"][sid] = {"main": main, "probes": probes,
                                     "probes_over_budget": over_budget}
        # 推进状态（场景级）
        sc = st["scenarios"][sid]
        sc["rounds"].append(dict(round=args.round, **main))
        sc["probes"].extend([dict(round=args.round, **p) for p in probes])
    # 全部场景齐本轮才推进臂轮次
    if all(any(r["round"] == args.round for r in st["scenarios"][s]["rounds"]) for s in M_SIDS):
        st["round"] = args.round
    save_state(args.arm, st)
    rname = "%s-result.json" % args.arm if args.arm == "GUIDE-1" else "%s-%s-result.json" % (
        args.arm, sids[0])
    sa.write_json(os.path.join(rd, rname), results)
    for sid in sids:
        r = results["scenarios"].get(sid)
        if r:
            print("submit %s R%d %s: obj=%g sat=%s probes=%d" % (
                args.arm, args.round, sid, r["main"]["objective"],
                r["main"]["all_connected"], len(r["probes"])))
    if results["invalid"]:
        print("invalid:", json.dumps(results["invalid"], ensure_ascii=False))


def cmd_report(_):
    with open(os.path.join(sa.OUT, "p0", "oracle-summary.json"), encoding="utf-8") as f:
        oracle = {e["scenario_id"]: e["best_objective"] for e in json.load(f)}
    with open(os.path.join(sa.OUT, "p0", "baseline-summary.json"), encoding="utf-8") as f:
        base = {e["scenario_id"]: e["objective"] for e in json.load(f)}
    st1, st2 = load_state("GUIDE-1"), load_state("GUIDE-2")

    def r4(st, sid):
        return last_round(st["scenarios"][sid], 4)["objective"]

    print("=== GUIDE-PILOT-R1 终判（主会话判读）===")
    print("%-12s %7s %7s %8s %8s" % ("scenario", "oracle", "base", "G1-R4", "G2-R4"))
    for sid in M_SIDS:
        print("%-12s %7g %7g %8g %8g" % (sid, oracle[sid], base[sid], r4(st1, sid), r4(st2, sid)))
    # G-P1
    g2_f213 = r4(st2, "cal-f2-13")
    gp1 = ("convergence_positive" if g2_f213 <= 295.0
           else "convergence_negative" if g2_f213 > 305.5 else "convergence_partial")
    print("G-P1 f2-13 收敛: %s (G2-R4=%g, oracle=284.5, S3起点=305.5)" % (gp1, g2_f213))
    # G-P2
    wins = sum(1 for sid in M_SIDS if r4(st2, sid) < r4(st1, sid))
    losses = sum(1 for sid in M_SIDS if r4(st2, sid) > r4(st1, sid))
    big2 = r4(st2, "cal-f2-13") < r4(st1, "cal-f2-13") and r4(st2, "cal-f2-15") < r4(st1, "cal-f2-15")
    noreg = all(r4(st2, s) <= r4(st1, s) for s in M_SIDS)
    gp2 = ("probe_value" if wins >= 3 or (big2 and noreg)
           else "probe_negative" if losses >= 3 else "probe_inconclusive")
    print("G-P2 探针价值: %s (G2 胜 %d/负 %d)" % (gp2, wins, losses))
    # G-P3
    g1_13, g2_13 = r4(st1, "cal-f4-13"), r4(st2, "cal-f4-13")
    gp3 = ("recovered" if min(g1_13, g2_13) <= base["cal-f4-13"]
           else "regression_entrenched" if min(g1_13, g2_13) > 135.0 else "partial_recovery")
    print("G-P3 f4-13 恢复: %s (G1-R4=%g G2-R4=%g, base=%g)" % (
        gp3, g1_13, g2_13, base["cal-f4-13"]))
    # G-P4 轨迹
    print("G-P4 轨迹（round0..4 objective）:")
    for arm, st in (("G1", st1), ("G2", st2)):
        for sid in M_SIDS:
            traj = [last_round(st["scenarios"][sid], k)["objective"] for k in range(5)]
            print("  %s %-12s %s" % (arm, sid, " -> ".join("%g" % t for t in traj)))
    verdict = ("pilot_positive" if gp1 == "convergence_positive" and gp2 != "probe_negative"
               else "pilot_negative" if (gp1 == "convergence_negative" or gp2 == "probe_negative")
               and gp1 != "convergence_positive" else "pilot_partial")
    print("PILOT VERDICT: %s" % verdict)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("pack")
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--round", required=True, type=int)
    p.add_argument("--sid")
    s = sub.add_parser("submit")
    s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--round", required=True, type=int)
    s.add_argument("--sid")
    s.add_argument("--slates", required=True)
    sub.add_parser("report")
    args = ap.parse_args()
    {"init": cmd_init, "pack": cmd_pack, "submit": cmd_submit, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
