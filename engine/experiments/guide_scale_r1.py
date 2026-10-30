# -*- coding: utf-8 -*-
"""GUIDE-SCALE-R1 执行器（双臂消融，场景级轮次状态）。

臂：SA（无探针）+ SB（每轮 ≤3 探针）× 4 场景 = 8 agent，全部 GLM-5.3 Flash
子智能体（harness 内）。R0 暖启动 = 编号序基线实测（两臂同起点同值）。
只读复用 scale_scenarios（其只读复用 pcbflow.v4exp.router；零写入 pcbflow 仓）。

子命令：
  init     测 R0 基线并初始化两臂状态文件（已存在则拒绝）
  pack     --arm --sid --round 生成该场景该轮裁决包
  submit   --arm --sid --round --slates <json> 校验+求解+入账
  report   出 G-S1..G-S4 判读与终判枚举

判分键不落任何包内：包只含板事实与该场景自身实测，永不含基线对比、
null/参照顶/枚举锚点、门值或另一臂数据（盲测边界，判读只在主会话）。
"""

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = "E:/ZCodeData/ZCodeProject/route-v5"
OUT = os.path.join(ROOT, "out", "guide-scale-r1")
STATE = os.path.join(OUT, "state")
ROUNDS = os.path.join(OUT, "rounds")
MODEL = os.path.join(OUT, "model-runs")
P0 = os.path.join(OUT, "p0")
sys.path.insert(0, ROOT)
import scale_scenarios as sc  # noqa: E402

ARMS = {"SA": False, "SB": True}  # arm -> has_probe_channel
N_ROUNDS = 4
PROBE_BUDGET = 3
N_COST_KEYS = re.compile(r"\b\d+(\.\d+)?\b")


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


# ---------------------------------------------------------------- R0/求解

def baseline_order(sid):
    return sc.net_ids_of(sid)


def measure(sid, order, group):
    r = sc.solve_scale(sid, order, group)
    run = r.pop("run")
    routed = {rt["net_id"] for rt in run.get("routes", [])}
    r["failed_net"] = next((x for x in r["order"] if x not in routed), None)
    r["per_net"] = sa_contrib(run) if r["all_connected"] else sa_contrib(run)
    return r


def sa_contrib(run):
    """逐网 length + 8*vias + 0.5*bends（与 seat_ab_r1a.net_contributions 同口径）。"""
    per = {}
    for rt in run.get("routes", []):
        c = per.setdefault(rt["net_id"], {"length_mm": 0.0, "vias": 0, "bends": 0})
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


def cmd_init(_):
    if os.path.exists(state_path("SA")) or os.path.exists(state_path("SB")):
        raise SystemExit("init: 状态文件已存在，拒绝覆盖（零回写纪律）")
    base = {}
    for sid in sc.ORDERED_SIDS:
        r = measure(sid, baseline_order(sid), "SCALE-R0")
        base[sid] = r
        print("R0 %s sat=%s obj=%s" % (sid, r["all_connected"], r["objective"]))
    for arm in ARMS:
        st = {"arm": arm, "invalid_count": 0,
              "scenarios": {sid: {"round": 0,
                                  "rounds": {"0": {"main": dict(base[sid]),
                                                   "probes": []}}}
                            for sid in sc.ORDERED_SIDS}}
        save_state(arm, st)
    print("init: 两臂状态就绪（R0=编号序基线实测，两臂同值）")


# ---------------------------------------------------------------- 包生成

def fmt_round_feedback(sid, rd, has_probe):
    m = rd["main"]
    lines = []
    if m["all_connected"]:
        lines.append("引擎实测：全部连通；总成本 %s" % m["objective"])
        lines.append("逐网成本贡献（走线长 + 8×过孔 + 0.5×拐弯；过孔与拐弯是顺序"
                     "敏感的——先布走直、后布让路；重成本集中在后布网络就值得提前）：")
        for nid in m["order"]:
            c = m["per_net"].get(nid)
            if c:
                lines.append("  %s：长度 %s mm，过孔 %d，拐弯 %d，贡献 %s"
                             % (nid, round(c["length_mm"], 2), c["vias"],
                                c["bends"], c["contribution"]))
    else:
        lines.append("引擎实测：**未能全部连通（该顺序 routing 失败，整跑终止）**；"
                     "失败网：%s（其后各网未布）。已布部分逐网贡献：" % m["failed_net"])
        for nid in m["order"]:
            c = m["per_net"].get(nid)
            if c:
                lines.append("  %s：长度 %s mm，过孔 %d，拐弯 %d，贡献 %s"
                             % (nid, round(c["length_mm"], 2), c["vias"],
                                c["bends"], c["contribution"]))
    if has_probe and rd.get("probes"):
        lines.append("你的探针实测：")
        for p in rd["probes"]:
            if p["all_connected"]:
                lines.append("  [%s] 总成本 %s（全部连通）" % (p["label"], p["objective"]))
            else:
                lines.append("  [%s] **routing 失败**（失败网 %s）"
                             % (p["label"], p.get("failed_net")))
    return lines


def cmd_pack(args):
    st = load_state(args.arm)
    sc_st = st["scenarios"][args.sid]
    if args.round != sc_st["round"] + 1:
        raise SystemExit("pack: 场景 %s 当前轮=%d，请求轮=%d 不连续"
                         % (args.sid, sc_st["round"], args.round))
    has_probe = ARMS[args.arm]
    board = sc.load_board(args.sid)
    nets = sc.net_ids_of(args.sid)
    L = []
    L.append("# GUIDE-SCALE 第 %d 轮（%s-%s）" % (args.round, args.arm, args.sid))
    L.append("")
    L.append("你在多轮迭代中引导一个确定性搜索式布线引擎：它严格按你给的顺序逐网"
             "布线并实测回报；你依据实测修订策略。铁律：只给排序"
             + ("与探针点名" if has_probe else "") + "，不输出任何数值。")
    L.append("")
    L.append("# 排序裁决包 %s" % args.sid)
    L.append("")
    L.append("你是 PCB 布线排序裁决器。下面是一张板的完整机器事实（结构化文本，"
             "非图像）。布线引擎将按你给出的顺序逐网布线：先布的网络可走直路，"
             "后布的网络让路绕行；任一网布线失败则整跑立即停止（无拆除重布）。"
             "请给出你认为最终总成本最低的完整布线顺序。")
    L.append("")
    bb = board["board"]
    L.append("【板】bbox [%g,%g]×[%g,%g] mm；信号层：%s"
             % (bb["bbox_mm"][0], bb["bbox_mm"][1], bb["bbox_mm"][2],
                bb["bbox_mm"][3], "、".join(bb["layers"])))
    ru = board["rules"]
    width_txt = "、".join("%s %g" % (k, v) for k, v in sorted(ru["width_mm"].items()))
    layer_txt = "；".join("%s 仅 %s" % (k, "/".join(v))
                          for k, v in sorted(ru["allowed_layers"].items())
                          if k != "default")
    L.append("【规则】格点 %g mm；不同网络铜净距 ≥%g mm；线宽：%s；过孔 pad %g/"
             "hole %g mm%s（注意：过孔焊盘在其 3×3 邻域内同时占用两层，是稀缺资源）"
             % (ru["grid_mm"], ru["clearance_mm"], width_txt,
                ru["via"]["pad_mm"], ru["via"]["hole_mm"],
                ("；" + layer_txt) if layer_txt else ""))
    L.append("【成本模型（仅用于排序，不要求输出数值）】总成本 = 走线总长 + 8×过孔数"
             " + 0.5×拐弯数，越小越好。")
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
    L.append("")
    if rels:
        L.append("【关系（分组事实，仅供排序参考）】")
        for r in sorted(rels, key=lambda r: r["relation_id"]):
            L.append("  %s（%s）：%s" % (r["relation_id"], r["relation_type"],
                                         "、".join(r["members"])))
    L.append("")
    L.append("【禁布区】")
    for k in board["keepouts"]:
        L.append("  %s" % json.dumps(k, sort_keys=True))
    L.append("")
    L.append("【默认策略（基线）】按编号序：%s" % "、".join(nets))
    L.append("")
    L.append("【你此前各轮的提案与引擎实测】")
    for rr in range(0, sc_st["round"] + 1):
        rd = sc_st["rounds"][str(rr)]
        L.append("— 第 %d 轮 —" % rr)
        L.append("你的排序：%s" % "、".join(rd["main"]["order"]))
        L.extend(fmt_round_feedback(args.sid, rd, has_probe))
    L.append("")
    L.append("【第 %d 轮任务】给出本场景的新排序提案（实测显示已无可改进时允许"
             "坚持原序）。" % args.round)
    L.append("【输出合同】最终回复只输出一个 json 代码块（不得输出任何成本数值），"
             "单个对象：")
    if has_probe:
        L.append('{"scenario_id": "%s", "route_order": ["<net_id>", …完整排列'
                 "每个恰好一次], \"reason\": \"<一句话>\", \"probes\": "
                 '[{"label": "<短名>", "route_order": [<完整排列>]}…]}。'
                 "probes 是你想让引擎代测的至多 %d 个备选排列（可不填）——用它检验"
                 "你的顺序敏感假设，下一轮你会拿到每个探针的实测结果。"
                 % (args.sid, PROBE_BUDGET))
    else:
        L.append('{"scenario_id": "%s", "route_order": ["<net_id>", …完整排列'
                 "每个恰好一次], \"reason\": \"<一句话>\"}" % args.sid)
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
    os.makedirs(os.path.join(MODEL, "%s-%s" % (args.arm, args.sid)),
                exist_ok=True)
    with open(os.path.join(MODEL, "%s-%s" % (args.arm, args.sid),
                           "round-%d-response.json" % args.round),
              "w", encoding="utf-8", newline="\n") as f:
        f.write(raw)
    slate = parse_slates(args.slates)
    nets = sc.net_ids_of(args.sid)
    order = [str(x) for x in slate.get("route_order", [])]
    if slate.get("scenario_id") != args.sid or sorted(order) != sorted(nets) \
            or len(set(order)) != len(nets):
        st["invalid_count"] += 1
        save_state(args.arm, st)
        _write(os.path.join(MODEL, "%s-%s" % (args.arm, args.sid),
                            "round-%d-INVALID.json" % args.round),
               {"reason": "not_complete_permutation_or_sid_mismatch",
                "got": order})
        print("submit: INVALID slate（累计无效 %d）" % st["invalid_count"])
        return
    rd = {"main": measure(args.sid, order, "SCALE-%s" % args.arm), "probes": []}
    if ARMS[args.arm]:
        seen = {"|".join(order)}
        for p in (slate.get("probes") or [])[:PROBE_BUDGET]:
            po = [str(x) for x in p.get("route_order", [])]
            key = "|".join(po)
            if sorted(po) != sorted(nets) or len(set(po)) != len(nets) \
                    or key in seen:
                continue
            seen.add(key)
            r = measure(args.sid, po, "SCALE-%s-PROBE" % args.arm)
            r["label"] = str(p.get("label", "p"))[:24]
            rd["probes"].append(r)
    sc_st["rounds"][str(args.round)] = rd
    sc_st["round"] = args.round
    save_state(args.arm, st)
    print("submit: %s-%s round %d ok（main sat=%s obj=%s, probes=%d）"
          % (args.arm, args.sid, args.round, rd["main"]["all_connected"],
             rd["main"]["objective"], len(rd["probes"])))


# ---------------------------------------------------------------- 判读

def rank_key(r):
    return r["objective"] if r["all_connected"] else float("inf")


def cmd_report(_):
    sa, sb = load_state("SA"), load_state("SB")
    null = _load(os.path.join(P0, "null-summary.json"))["per"]
    try:
        ceil = _load(os.path.join(P0, "reference-ceiling.json"))["per"]
    except Exception:
        ceil = {}
    denom, rows = [], []
    for sid in sc.ORDERED_SIDS:
        nu = null[sid]
        spread = (nu["objective_max"] / nu["objective_min"] - 1) \
            if nu["sat_count"] else -1
        is_denom = nu["sat_rate"] >= 0.5 and spread >= 0.01
        if is_denom:
            denom.append(sid)
        sa4 = sa["scenarios"][sid]["rounds"].get(str(N_ROUNDS))
        sb4 = sb["scenarios"][sid]["rounds"].get(str(N_ROUNDS))
        base = sa["scenarios"][sid]["rounds"]["0"]["main"]
        rows.append({
            "sid": sid, "denom": is_denom, "null_spread": round(spread, 4),
            "base_obj": base["objective"], "base_sat": base["all_connected"],
            "SA_R4": sa4["main"]["objective"] if sa4 else None,
            "SA_R4_sat": sa4["main"]["all_connected"] if sa4 else None,
            "SB_R4": sb4["main"]["objective"] if sb4 else None,
            "SB_R4_sat": sb4["main"]["all_connected"] if sb4 else None,
            "null_min": nu["objective_min"], "null_p95": nu["objective_p95"],
            "ref_best": ceil.get(sid, {}).get("reference_best")})
    print("== GUIDE-SCALE-R1 终表（成本门分母=%s）==" % denom)
    for r in rows:
        print("  %(sid)s denom=%(denom)s base=%(base_obj)s SA_R4=%(SA_R4)s "
              "SB_R4=%(SB_R4)s null[min=%(null_min)s p95=%(null_p95)s] "
              "ref=%(ref_best)s" % r)
    # G-S1
    g1_ok = all(r["SB_R4_sat"] and r["SB_R4"] <= r["base_obj"]
                for r in rows if r["denom"])
    g1_null = sum(1 for r in rows if r["denom"] and r["SB_R4_sat"]
                  and r["SB_R4"] <= r["null_min"])
    g_s1 = ("scale_value" if g1_ok and g1_null >= 1
            else "partial" if g1_ok else "not_demonstrated")
    # G-S2 消融
    sb_wins = sum(1 for r in rows if r["denom"]
                  and rank_key({"objective": r["SB_R4"], "all_connected": r["SB_R4_sat"]})
                  < rank_key({"objective": r["SA_R4"], "all_connected": r["SA_R4_sat"]}))
    sa_wins = sum(1 for r in rows if r["denom"]
                  and rank_key({"objective": r["SA_R4"], "all_connected": r["SA_R4_sat"]})
                  < rank_key({"objective": r["SB_R4"], "all_connected": r["SB_R4_sat"]}))
    g_s2 = ("probe_targeting_value" if sb_wins >= 2
            else "probe_harmful" if sa_wins >= 2 else "inconclusive")
    # G-S3 否决
    reg = sum(1 for r in rows if r["denom"] and ((not r["SB_R4_sat"])
              or r["SB_R4"] > r["base_obj"] * 1.01))
    g_s3 = "clean" if reg == 0 else "regression_%d" % reg
    # G-S4 机制
    probes = sum(len(sc_st["rounds"][k]["probes"])
                 for sid_ in sc.ORDERED_SIDS
                 for sc_st in [sb["scenarios"][sid_]]
                 for k in sc_st["rounds"])
    probe_informative = 0
    probe_beat_main = 0
    for sid_ in sc.ORDERED_SIDS:
        sc_st = sb["scenarios"][sid_]
        for k, rd in sc_st["rounds"].items():
            for p in rd["probes"]:
                if p["all_connected"] == rd["main"]["all_connected"] \
                        and p["objective"] != rd["main"]["objective"]:
                    probe_informative += 1
                if rank_key(p) < rank_key(rd["main"]):
                    probe_beat_main += 1
    print("G-S1=%s（SB 全部 ≤基线且 SAT：%s；≤null_min 场景数=%d）" %
          (g_s1, g1_ok, g1_null))
    print("G-S2=%s（SB 胜 %d / SA 胜 %d / 分母 %d）" %
          (g_s2, sb_wins, sa_wins, len(denom)))
    print("G-S3=%s" % g_s3)
    print("G-S4: probes=%d informative=%d beat_main=%d" %
          (probes, probe_informative, probe_beat_main))
    verdict = "scale_positive" if (g_s1 == "scale_value"
                                   and g_s2 == "probe_targeting_value"
                                   and reg == 0) else (
        "scale_negative" if g_s2 == "probe_harmful" or g_s1 == "not_demonstrated"
        else "scale_partial")
    print("PILOT VERDICT: %s" % verdict)
    rounds_done = min(sa["scenarios"][s]["round"] for s in sc.ORDERED_SIDS)
    print("rounds_completed=%d（若 <4 终判须标注 time_capped）" % rounds_done)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("pack")
    p.add_argument("--arm", required=True, choices=sorted(ARMS))
    p.add_argument("--sid", required=True)
    p.add_argument("--round", type=int, required=True)
    s = sub.add_parser("submit")
    s.add_argument("--arm", required=True, choices=sorted(ARMS))
    s.add_argument("--sid", required=True)
    s.add_argument("--round", type=int, required=True)
    s.add_argument("--slates", required=True)
    sub.add_parser("report")
    args = ap.parse_args()
    {"init": cmd_init, "pack": cmd_pack, "submit": cmd_submit,
     "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
