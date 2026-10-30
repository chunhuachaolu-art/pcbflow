# -*- coding: utf-8 -*-
"""SEAT-AB-R1a 场景语料 A/B 确定性执行器。

只读复用 pcbflow.v4exp（sys.path 注入，零写入 pcbflow 仓）。
产物根：<ENGINE_ROOT>/out/seat-ab-r1a/
子命令：
  baseline   16 门控场景 sorted(net_id) 基线 + 重放确定性
  oracle     全排列枚举 oracle（n<=6，最多 720 排列/场景）
  synthetic  合成 slate 预检（倒序 + 2 个种子随机序）
  packages   生成 16 份排序盲包 + INDEX.json（sha256）
  measure    --slates <json> --arm <名>：校验并求解模型 slate
  feedback   --arm <名>：由 measure 产物生成 pass2 反馈文件
"""
import argparse
import hashlib
import itertools
import json
import os
import random
import sys

PCBFLOW_ROOT = "<WORKSPACE>/tools/pcbflow"
sys.path.insert(0, PCBFLOW_ROOT)
from pcbflow.v4exp import cmp_scenarios as cs, router  # noqa: E402

ROOT = "<ENGINE_ROOT>"
OUT = os.path.join(ROOT, "out", "seat-ab-r1a")
GATED_FAMILIES = ("f1", "f2", "f3", "f4")  # f5=结构性 unsat（全排列 0 sat，2026-09-13 P0 实测）


def gated_sids():
    return sorted(s for s in cs.all_scenario_ids()
                  if s.startswith("cal-") and s.split("-")[1] in GATED_FAMILIES)


def board_of(sid):
    return cs.generate_scenario(sid, attempt=0)


def net_ids_of(sid):
    return sorted(str(n["net_id"]) for n in board_of(sid)["nets"])


def solve(sid, order, group):
    return router.solve_board(board_of(sid),
                              {"route_order": [str(x) for x in order], "group": group})


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)


def net_contributions(run):
    """逐网 length + 8*vias + 0.5*bends（与 objective 同口径；bends=折线方向变化数）。"""
    per = {}
    for r in run.get("routes", []):
        c = per.setdefault(r["net_id"], {"length_mm": 0.0, "vias": 0, "bends": 0})
        pts = r.get("polyline_mm") or []
        for a, b in zip(pts, pts[1:]):
            c["length_mm"] += abs(b[0] - a[0]) + abs(b[1] - a[1])
        for a, b, d in zip(pts, pts[1:], pts[2:]):
            if (b[0] - a[0], b[1] - a[1]) != (d[0] - b[0], d[1] - b[1]):
                c["bends"] += 1
    for v in run.get("vias", []):
        per.setdefault(v["net_id"], {"length_mm": 0.0, "vias": 0, "bends": 0})
        per[v["net_id"]]["vias"] += 1
    for nid, c in per.items():
        c["contribution"] = round(c["length_mm"] + 8.0 * c["vias"] + 0.5 * c["bends"], 4)
    return per


# ---------------------------------------------------------------- 子命令

def cmd_baseline(_):
    rows = []
    for sid in gated_sids():
        order = net_ids_of(sid)
        r1 = solve(sid, order, "SEAT-AB-A0")
        r2 = solve(sid, order, "SEAT-AB-A0")
        det = json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
        m = r1["metrics"]
        rows.append({"scenario_id": sid, "route_order": order,
                     "objective": m["objective"], "search_nodes": m["search_nodes"],
                     "all_connected": m["all_connected"], "status": r1["status"],
                     "deterministic_replay": det})
        write_json(os.path.join(OUT, "p0", "baseline-%s.json" % sid), r1)
    write_json(os.path.join(OUT, "p0", "baseline-summary.json"), rows)
    print("baseline: n=%d all_sat=%s replay_all=%s" % (
        len(rows), all(r["all_connected"] for r in rows),
        all(r["deterministic_replay"] for r in rows)))


def cmd_oracle(_):
    rows = []
    for sid in gated_sids():
        nets = net_ids_of(sid)
        sat_objs = {}
        for perm in itertools.permutations(nets):
            r = solve(sid, list(perm), "SEAT-AB-ORACLE")
            if r["metrics"]["all_connected"]:
                sat_objs.setdefault(r["metrics"]["objective"], []).append(list(perm))
        best = min(sat_objs) if sat_objs else None
        row = {"scenario_id": sid, "nets": len(nets),
               "permutations": 1 if len(nets) == 0 else 0 or 1,
               "sat_order_count": sum(len(v) for v in sat_objs.values()),
               "best_objective": best,
               "best_orders_sample": sat_objs[best][:3] if best is not None else [],
               "objective_distribution": {str(k): len(v) for k, v in sorted(sat_objs.items())}}
        row["permutations"] = 1
        for k in range(2, len(nets) + 1):
            row["permutations"] *= k
        rows.append(row)
        write_json(os.path.join(OUT, "p0", "oracle-%s.json" % sid), row)
    write_json(os.path.join(OUT, "p0", "oracle-summary.json"), rows)
    print("oracle: n=%d all_have_sat=%s" % (
        len(rows), all(r["best_objective"] is not None for r in rows)))


def cmd_synthetic(_):
    rows = []
    for sid in gated_sids():
        nets = net_ids_of(sid)
        variants = {"reversed": list(reversed(nets))}
        for i, seed in enumerate((hash(sid) % (2 ** 31), (hash(sid) + 1) % (2 ** 31))):
            rnd = random.Random(seed)
            v = list(nets)
            rnd.shuffle(v)
            variants["shuffle-%d" % (i + 1)] = v
        for name, order in variants.items():
            r = solve(sid, order, "SEAT-AB-SYN")
            m = r["metrics"]
            rows.append({"scenario_id": sid, "variant": name, "route_order": order,
                         "objective": m["objective"], "all_connected": m["all_connected"],
                         "search_nodes": m["search_nodes"]})
    write_json(os.path.join(OUT, "p0", "synthetic-summary.json"), rows)
    by_sid = {}
    for r in rows:
        by_sid.setdefault(r["scenario_id"], []).append(r["objective"])
    spread = {k: (min(v), max(v)) for k, v in by_sid.items()}
    print("synthetic: %d runs, per-scenario objective spread (min,max):" % len(rows))
    for k in sorted(spread):
        print("  %s %s" % (k, spread[k]))


def build_package_text(sid):
    b = board_of(sid)
    lines = []
    lines.append("# 排序裁决包 %s" % sid)
    lines.append("")
    lines.append("你是 PCB 布线排序裁决器。下面是一张板的完整机器事实（结构化文本，非图像）。"
                 "布线引擎将按你给出的顺序逐网布线：先布的网络可走直路，后布的网络让路绕行；"
                 "任一网布线失败则整跑立即停止（无拆除重布）。请给出你认为最终总成本最低的完整布线顺序。")
    lines.append("")
    bb = b["board"]
    lines.append("【板】bbox [%g,%g]×[%g,%g] mm；信号层：%s" % (
        bb["bbox_mm"][0], bb["bbox_mm"][1], bb["bbox_mm"][2], bb["bbox_mm"][3],
        "、".join(bb["layers"])))
    ru = b["rules"]
    width_txt = "、".join("%s %g" % (k, v) for k, v in sorted(ru["width_mm"].items()))
    layer_txt = "；".join("%s 仅 %s" % (k, "/".join(v))
                          for k, v in sorted(ru["allowed_layers"].items()) if k != "default")
    lines.append("【规则】格点 %g mm；不同网络铜净距 ≥%g mm；线宽：%s；过孔 pad %g/hole %g mm%s" % (
        ru["grid_mm"], ru["clearance_mm"], width_txt,
        ru["via"]["pad_mm"], ru["via"]["hole_mm"],
        ("；" + layer_txt) if layer_txt else ""))
    lines.append("【成本模型（仅用于排序，不要求输出数值）】总成本 = 走线总长 + 8×过孔数 + 0.5×拐弯数，越小越好。")
    lines.append("")
    lines.append("【焊盘】")
    for p in sorted(b["pads"], key=lambda p: p["pad_id"]):
        lines.append("  %s：(%g,%g) %g×%g mm，%s，属 %s" % (
            p["pad_id"], p["x_mm"], p["y_mm"], p["w_mm"], p["h_mm"], p["layer"], p["net_id"]))
    lines.append("")
    lines.append("【网络】")
    for n in sorted(b["nets"], key=lambda n: n["net_id"]):
        lines.append("  %s [%s]：%s" % (n["net_id"], n["net_class"], "–".join(n["endpoints"])))
    rels = b.get("relations") or []
    lines.append("")
    if rels:
        lines.append("【关系（分组事实，仅供排序参考）】")
        for r in sorted(rels, key=lambda r: r["relation_id"]):
            lines.append("  %s（%s）：%s" % (
                r["relation_id"], r["relation_type"], "、".join(r["members"])))
    else:
        lines.append("【关系】无")
    kos = b.get("keepouts") or []
    lines.append("")
    if kos:
        lines.append("【禁布区】")
        for k in kos:
            lines.append("  %s" % json.dumps(k, ensure_ascii=False, sort_keys=True))
    else:
        lines.append("【禁布区】无")
    lines.append("")
    lines.append("【默认策略（基线）】按 net_id 字典序：%s" % "、".join(net_ids_of(sid)))
    lines.append("")
    lines.append("【输出合同】最终回复只输出一个 json 代码块（枚举值逐字使用，不得发明字段；"
                 "不得输出任何成本数值），形状：")
    lines.append('{"scenario_id": "%s", "route_order": ["<net_id>", ...（%d 个网络的完整排列，每个恰好一次）], '
                 '"reason": "<一句话理由>"}' % (sid, len(net_ids_of(sid))))
    lines.append("")
    return "\n".join(lines)


def cmd_packages(_):
    pkg_dir = os.path.join(OUT, "packages")
    os.makedirs(pkg_dir, exist_ok=True)
    index = []
    for sid in gated_sids():
        text = build_package_text(sid)
        name = "pkg-%s.md" % sid
        with open(os.path.join(pkg_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
        index.append({"scenario_id": sid, "file": name, "bytes": len(text.encode("utf-8")),
                      "sha256": sha256_text(text), "net_count": len(net_ids_of(sid))})
    write_json(os.path.join(OUT, "packages", "INDEX.json"), index)
    print("packages: %d files -> %s" % (len(index), pkg_dir))


def cmd_measure(args):
    with open(args.slates, encoding="utf-8") as f:
        payload = json.load(f)
    entries = payload["slates"] if isinstance(payload, dict) else payload
    rows, invalid = [], []
    by_sid = {e["scenario_id"]: e for e in entries}
    for sid in gated_sids():
        e = by_sid.get(sid)
        if e is None:
            invalid.append({"scenario_id": sid, "reason": "missing"})
            continue
        order = [str(x) for x in e.get("route_order", [])]
        expect = net_ids_of(sid)
        if sorted(order) != expect:
            invalid.append({"scenario_id": sid, "reason": "not_a_complete_permutation",
                            "got": order, "expected_nets": expect})
            continue
        r = solve(sid, order, "SEAT-AB-%s" % args.arm)
        m = r["metrics"]
        rows.append({"scenario_id": sid, "route_order": order,
                     "objective": m["objective"], "search_nodes": m["search_nodes"],
                     "all_connected": m["all_connected"], "status": r["status"],
                     "violations": m["violations"],
                     "per_net_contribution": net_contributions(r)})
    write_json(os.path.join(OUT, "model-runs", "%s-measure.json" % args.arm),
               {"arm": args.arm, "rows": rows, "invalid": invalid})
    print("measure %s: valid=%d invalid=%d sat=%d" % (
        args.arm, len(rows), len(invalid), sum(1 for r in rows if r["all_connected"])))


def cmd_feedback(args):
    with open(os.path.join(OUT, "model-runs", "%s-measure.json" % args.arm), encoding="utf-8") as f:
        data = json.load(f)
    fb = []
    for r in data["rows"]:
        fb.append({"scenario_id": r["scenario_id"],
                   "your_route_order": r["route_order"],
                   "engine_measured": {
                       "all_connected": r["all_connected"],
                       "objective": r["objective"],
                       "search_nodes": r["search_nodes"],
                       "per_net_contribution": r["per_net_contribution"],
                       "violations": r["violations"]}})
    write_json(os.path.join(OUT, "model-runs", "%s-feedback.json" % args.arm),
               {"arm": args.arm, "note": "引擎对你上一轮排序的实测结果；不含任何基线或参考臂数值；"
                                         "请据此修订或坚持你的排序提案。", "results": fb})
    print("feedback %s: %d scenarios" % (args.arm, len(fb)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("baseline")
    sub.add_parser("oracle")
    sub.add_parser("synthetic")
    sub.add_parser("packages")
    m = sub.add_parser("measure")
    m.add_argument("--slates", required=True)
    m.add_argument("--arm", required=True)
    fb = sub.add_parser("feedback")
    fb.add_argument("--arm", required=True)
    args = ap.parse_args()
    {"baseline": cmd_baseline, "oracle": cmd_oracle, "synthetic": cmd_synthetic,
     "packages": cmd_packages, "measure": cmd_measure, "feedback": cmd_feedback}[args.cmd](args)


if __name__ == "__main__":
    main()
