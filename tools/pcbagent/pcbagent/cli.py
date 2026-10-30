# -*- coding: utf-8 -*-
"""pcbagent 命令面（SPEC §0）。B1：mirror-info；B2：congestion /
escape-audit / corridors；B3：route（L3 区域路由器 + 提交纪律）；
B4：verify（diff 回归）/ length（九组等长）/ render / audit-checklist。"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import sys
import time

from . import config as C


def dump(dirpath, name, text):
    """产物落盘：路径规范化 + 包含性校验（目标必须落在 dirpath 内）。"""
    base = pathlib.Path(dirpath).resolve()
    target = pathlib.Path(base / os.path.basename(name)).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"产物路径越界: {name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")


def cmd_mirror_info(args):
    from .mirror import BoardMirror
    t0 = time.perf_counter()
    m = BoardMirror(args.project)
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    opens = m.opens()
    opens_s = time.perf_counter() - t0
    signal_opens = {k: v for k, v in opens.items() if k != "GND"}
    out = {
        "project": args.project,
        "load_seconds": round(load_s, 2),
        "opens_seconds": round(opens_s, 2),
        "stats": m.stats(),
        "opens_total": sum(opens.values()),
        "opens_gnd": opens.get("GND", 0),
        "opens_signal": sum(signal_opens.values()),
        "opens_by_net": dict(sorted(opens.items(), key=lambda kv: -kv[1])),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_congestion(args):
    """L2 拥塞分析（SPEC §3）：热图+走廊+布局反馈+逃逸审计 → pcbagent-out/。"""
    from .mirror import BoardMirror
    from . import planner as P
    project = args.project
    pairs = None
    pairs_path = args.pairs or os.path.join(project, "opens.csv")
    if os.path.isfile(pairs_path):
        pairs, _gnd = P.parse_opens_csv(pairs_path)
    m = BoardMirror(project)
    pl = P.Planner(m, cell=args.cell)
    t0 = time.perf_counter()
    if pairs and not args.netlist:
        pl.add_pairs(pairs)
        mode = f"pairs({len(pairs)})"
    else:
        pl.add_netlist()
        mode = "netlist"
    pl.run(max_iter=args.max_iter)
    open_pads = list(m.pads) if mode == "netlist" else _open_pads_of(m, pairs)
    esc = P.escape_audit(m, pl.occ, pl.grid, open_pads,
                         all_mode=(mode == "netlist"))
    prods = P.build_products(pl, f"{os.path.basename(project)} [{mode}]", esc)
    out_dir = os.path.join(project, "pcbagent-out", "b2",
                           "current" if mode.startswith("pairs") else "p3")
    for name, text in prods.items():
        dump(out_dir, name, text)
    summary = {
        "project": project, "mode": mode,
        "nets": len(pl.nets), "generations": pl.gen_used,
        "converged": pl.converged, "overload_cells": len(pl.overload),
        "hits": sum(1 for r in pl.nets if pl.paths[r.rid]["hit"]),
        "run_s": round(time.perf_counter() - t0, 1),
        "out_dir": out_dir,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


def _open_pads_of(mirror, pairs):
    out = []
    for (net, A, B, _row) in pairs:
        for (x, y) in ((A[0], A[1]), (B[0], B[1])):
            bp, bd = None, None
            for p in mirror.pads:
                if p.net != net:
                    continue
                d = (p.x - x) ** 2 + (p.y - y) ** 2
                if bd is None or d < bd:
                    bp, bd = p, d
            if bp is not None and bd <= 4.0:
                out.append(bp)
    return out


def cmd_escape_audit(args):
    """L2 逃逸容量审计（可单独跑，SPEC §3.3-4）。"""
    from .mirror import BoardMirror
    from . import planner as P
    m = BoardMirror(args.project)
    pl = P.Planner(m)
    pairs = None
    pairs_path = args.pairs or os.path.join(args.project, "opens.csv")
    if os.path.isfile(pairs_path):
        pairs, _gnd = P.parse_opens_csv(pairs_path)
    open_pads = list(m.pads) if (args.netlist or not pairs) \
        else _open_pads_of(m, pairs)
    esc = P.escape_audit(m, pl.occ, pl.grid, open_pads,
                         all_mode=args.netlist or not pairs)
    md = P._escape_audit_md(esc, os.path.basename(args.project))
    out_dir = os.path.join(args.project, "pcbagent-out", "b2")
    dump(out_dir, "escape-audit.md", md)
    dump(out_dir, "escape-audit.json",
         json.dumps(esc, ensure_ascii=False, indent=1))
    print(md)
    return 0


def cmd_corridors(args):
    """L2 单网走廊查询：读已缓存的 corridors.json（先跑 congestion）。"""
    from . import planner as P
    cand = os.path.join(args.project, "pcbagent-out", "b2", "current",
                        "corridors.json")
    if not os.path.isfile(cand):
        cand = os.path.join(args.project, "pcbagent-out", "b2", "p3",
                            "corridors.json")
    if not os.path.isfile(cand):
        print("未找到 corridors.json——先跑: python -m pcbagent.cli congestion "
              "--project <工程>", file=sys.stderr)
        return 2
    data = json.loads(pathlib.Path(cand).read_text(encoding="utf-8"))
    hits = [n for n in data["nets"]
            if n["net"] == args.net or n["rid"] == args.net]
    if not hits:
        print(json.dumps({"net": args.net, "found": False,
                          "available_nets": sorted({n["net"] for n in data["nets"]})},
                         ensure_ascii=False, indent=1))
        return 1
    print(json.dumps({"source": cand, "entries": hits},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_verify(args):
    """L4 verify（SPEC §5）：DRC 封装 + 与基线 diff 出回归清单。
    基线 = --baseline 显式文件 > 上次快照 verify-last.json > 无（首跑建立）。
    本次 DRC 快照滚动为 verify-last.json；报告落 pcbagent-out/b4/。
    退出码：1 当且仅当出现基线没有的新增违规（存量违规不算失败）。"""
    import shutil
    from . import bridge as B
    report, md, raw = B.verify_flow(args.project, baseline_path=args.baseline,
                                    out_json=args.output)
    out_dir = os.path.join(args.project, "pcbagent-out", C.B4_OUT_SUBDIR)
    dump(out_dir, "verify-report.json",
         json.dumps(report, ensure_ascii=False, indent=1))
    dump(out_dir, "verify-report.md", md)
    shutil.copyfile(raw, os.path.join(out_dir, "verify-last.json"))
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if report["regression"] else 0


def cmd_length(args):
    """L4 length（SPEC §5）：九组等长报告（移植 revc/length-report.py 口径）。
    报告生成本身即成功（组 pass 与否是数据，不是命令失败）；--strict 才按
    all_pass 定退出码（等长后处理属 F4/GUI 阶段）。"""
    from .mirror import BoardMirror
    from . import bridge as B
    m = BoardMirror(args.project)
    rep = B.length_report(m)
    md = B.length_report_md(rep, os.path.basename(args.project))
    out_dir = os.path.join(args.project, "pcbagent-out", C.B4_OUT_SUBDIR)
    dump(out_dir, "length-report.json",
         json.dumps(rep, ensure_ascii=False, indent=1))
    dump(out_dir, "length-report.md", md)
    brief = {"project": args.project, "all_pass": rep["all_pass"],
             "out_dir": out_dir,
             "groups": {g: {"pass": e.get("pass"),
                            **({"worst_abs_delta_mm": e["worst_abs_delta_mm"]}
                               if "worst_abs_delta_mm" in e else
                               {"intra_pair_delta_mm": e["intra_pair_delta_mm"]}
                               if "intra_pair_delta_mm" in e else
                               {"note": e.get("note")})}
                        for g, e in rep["groups"].items()}}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    return 0 if (not args.strict or rep["all_pass"]) else 1


def cmd_render(args):
    """L4 render（SPEC §5）：分层 SVG（kicad-cli 导出，供 VLM 审计/人看）。"""
    from . import bridge as B
    layers = args.layers.split(",") if args.layers else None
    r = B.render_layers(args.project, layers=layers)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


def cmd_audit_checklist(args):
    """L4 audit-checklist（SPEC §5）：routing-spec §4 视觉审计清单
    （附每网铜长/过孔/分层证据；视觉判定留给人/VLM，advisory 非裁决）。"""
    from .mirror import BoardMirror
    from . import bridge as B
    m = BoardMirror(args.project)
    data, md = B.audit_checklist(m)
    out_dir = os.path.join(args.project, "pcbagent-out", C.B4_OUT_SUBDIR)
    dump(out_dir, "audit-checklist.json",
         json.dumps(data, ensure_ascii=False, indent=1))
    dump(out_dir, "audit-checklist.md", md)
    print(md)
    return 0


def _load_corridors_full(project):
    """corridors.json 一次加载、双口径：
    - soft：net → 合并段集（L3 软约束参考，多对网合并为超集无害）；
    - pair：(net, fx, fy, tx, ty) → 该断点对的走廊段（中继分段骨架，
      pair 坐标来自 opens.csv 同源，round 3 位作键精确匹配）。
    返回 (soft_get, pair_map)；无缓存文件返回 (None, {})。"""
    lname = {"F.Cu": C.LAYER_F, "In2.Cu": C.LAYER_IN2}
    for sub in ("current", "p3"):
        path = os.path.join(project, "pcbagent-out", "b2", sub,
                            "corridors.json")
        if not os.path.isfile(path):
            continue
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        soft, pair = {}, {}
        for n in data.get("nets", []):
            segs = [(lname[s["layer"]], s["from"][0], s["from"][1],
                     s["to"][0], s["to"][1])
                    for s in n.get("segments", []) if s["layer"] in lname]
            if not segs:
                continue
            soft.setdefault(n["net"], []).extend(segs)
            p = n.get("pair") or {}
            try:
                key = (n["net"], round(float(p["from_x_mm"]), 3),
                       round(float(p["from_y_mm"]), 3),
                       round(float(p["to_x_mm"]), 3),
                       round(float(p["to_y_mm"]), 3))
            except (KeyError, TypeError, ValueError):
                continue
            pair.setdefault(key, segs)
        return soft.get, pair
    return None, {}


def _route_targets(mirror, net, pairs_path):
    """route 目标 [(net, A, B)]，A/B=(x, y, frozenset(layers))。
    --net X：opens.csv 里该网全部对；无行则该网焊盘确定性最近链。
    batch：opens.csv 全部信号对（行序即 S4 实战顺序，免检短跳在前）。"""
    from .planner import parse_opens_csv
    sig_layers = frozenset(C.L2_SIGNAL_LAYERS)
    pairs = []
    if pairs_path and os.path.isfile(pairs_path):
        pairs, _gnd = parse_opens_csv(pairs_path)
    if net:
        sel = [p for p in pairs if p[0] == net]
        if sel:
            return [(p[0], p[1], p[2]) for p in sel]
        pads = sorted((pd for pd in mirror.pads
                       if pd.net == net and not pd.npth),
                      key=lambda p: (p.ref, p.number))
        terms = []
        for p in pads:
            ls = frozenset(l for l in p.layers if l in sig_layers) or sig_layers
            terms.append((p.x, p.y, ls))
        if len(terms) < 2:
            return []
        chain = [terms[0]]
        rest = terms[1:]
        while rest:
            cur = chain[-1]
            rest.sort(key=lambda t: (t[0] - cur[0]) ** 2 + (t[1] - cur[1]) ** 2)
            chain.append(rest.pop(0))
        return [(net, chain[i], chain[i + 1])
                for i in range(len(chain) - 1)]
    return [(p[0], p[1], p[2]) for p in pairs]


def cmd_route(args):
    """L3 route（SPEC §4）：区域 A* + L1 终判 + ripup → 提交纪律落板。

    长距断点对（直线 ≥L3_SEG_MIN_MM 且有该对 L2 走廊）自动走走廊中继
    分段（PHASE-REPORT-3 §5.1）。--dry-run：只规划与 L1 终判，不落板。"""
    from .mirror import BoardMirror
    from .legality import Legality
    from . import router as R
    from .commit import CommitFlow, SexprWriter, KipyWriter
    from .bridge import run_drc, DrcResult
    project = args.project
    log = print
    m = BoardMirror(project)
    leg = Legality(m)
    soft_corr, pair_corr = _load_corridors_full(project)
    router = R.Router(m, leg, corridor_of=soft_corr, log=log)

    def plan_one(net, A, B):
        dist = math.hypot(B[0] - A[0], B[1] - A[1])
        segs = None
        if pair_corr:
            segs = pair_corr.get((net, round(A[0], 3), round(A[1], 3),
                                  round(B[0], 3), round(B[1], 3)))
        if (not args.no_segment) and segs and dist >= C.L3_SEG_MIN_MM:
            return router.route_net_segmented(
                net, A, B, segs, ripup=not args.no_ripup)
        return router.route_net(net, A, B, ripup=not args.no_ripup)

    targets = _route_targets(m, args.net,
                             args.pairs or os.path.join(project, "opens.csv"))
    if args.start:
        targets = targets[args.start:]
    if args.limit:
        targets = targets[:args.limit]
    if not targets:
        print(json.dumps({"error": "无 route 目标（查 --net / opens.csv）"},
                         ensure_ascii=False))
        return 2
    log(f"[route] 目标 {len(targets)} 边"
        f"（{len({t[0] for t in targets})} 网）"
        f"{' [dry-run]' if args.dry_run else ''}")

    baseline = None
    if not args.dry_run:
        if args.baseline_json:
            with open(args.baseline_json, encoding="utf-8") as fh:
                baseline = DrcResult(json.load(fh), project)
        else:
            log("[route] 跑基线 DRC…")
            baseline = run_drc(project)
    writer = KipyWriter(log) if args.kipy else SexprWriter()
    flow = CommitFlow(project, writer, baseline=baseline, log=log)

    def gen():
        for (net, A, B) in targets:
            m.sync()
            yield plan_one(net, A, B)

    if args.dry_run:
        plans = []
        for (net, A, B) in targets:
            m.sync()
            plans.append(plan_one(net, A, B))
        n_ok = sum(1 for p in plans if p.ok)
        summary = {"project": project, "dry_run": True, "targets": len(targets),
                   "routed": n_ok,
                   "failed": [{"net": p.net, "fail": p.fail,
                               "blocks": p.blocks[:3]}
                              for p in plans if not p.ok],
                   "plans": [p.to_dict() for p in plans]}
        print(json.dumps({k: v for k, v in summary.items() if k != "plans"},
                         ensure_ascii=False, indent=1))
        out_dir = os.path.join(project, "pcbagent-out", "b3")
        dump(out_dir, "route-report.json",
             json.dumps(summary, ensure_ascii=False, indent=1))
        return 0 if n_ok else 1

    verdict = flow.run(gen(), batch=args.batch,
                       on_applied=lambda p: m.sync())
    n_ok = sum(1 for p in verdict["plans"] if p["ok"])
    summary = {
        "project": project, "targets": len(targets),
        "routed": n_ok, "committed": verdict["written_plans"],
        "rolled_back": verdict["rolled_back"],
        "added_violations": verdict["added"],
        "violations_after": verdict["violations_after"],
        "writer": writer.name, "run_s": verdict["run_s"],
        "failed": [{"net": p["net"], "fail": p["fail"],
                    "blocks": p["blocks"][:3]}
                   for p in verdict["plans"] if not p["ok"]],
        "plans": verdict["plans"],
    }
    out_dir = os.path.join(project, "pcbagent-out", "b3")
    dump(out_dir, "route-report.json",
         json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "plans"},
                     ensure_ascii=False, indent=1))
    return 0 if (n_ok and not verdict["rolled_back"]) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pcbagent",
                                 description="KiCad 布线规划/合法性/验证工具链")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("mirror-info", help="板镜像统计（pads/tracks/vias/nets/断点）")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_mirror_info)

    p = sub.add_parser("verify",
                       help="L4：kicad-cli DRC 封装 + 与基线 diff（回归检测）")
    p.add_argument("--project", required=True)
    p.add_argument("--output", default=None,
                   help="DRC 原始 JSON 落点（默认 <工程>/pcbagent-out/b4/verify-drc.json）")
    p.add_argument("--baseline", default=None,
                   help="基线 DRC JSON（默认上次 verify-last.json；无则首跑建立）")
    p.add_argument("--no-refill", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("length",
                       help="L4：九组等长报告（routing-spec §3 口径）")
    p.add_argument("--project", required=True)
    p.add_argument("--strict", action="store_true",
                   help="存在 FAIL 组时退出码 1（默认报告生成即 0）")
    p.set_defaults(func=cmd_length)

    p = sub.add_parser("render", help="L4：分层 SVG 渲染（kicad-cli 导出）")
    p.add_argument("--project", required=True)
    p.add_argument("--layers", default=None,
                   help="逗号分隔层名（默认 F/In1/In2/B.Cu+双丝印+Edge.Cuts）")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("audit-checklist",
                       help="L4：routing-spec §4 视觉审计清单（advisory）")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_audit_checklist)

    p = sub.add_parser("congestion", help="L2 拥塞分析（热图/走廊/布局反馈/逃逸审计）")
    p.add_argument("--project", required=True)
    p.add_argument("--pairs", default=None,
                   help="断点对 CSV（默认 <工程>/opens.csv 存在即用）")
    p.add_argument("--netlist", action="store_true",
                   help="强制整板 netlist 模式（忽略 opens.csv）")
    p.add_argument("--cell", type=float, default=0.5)
    p.add_argument("--max-iter", type=int, default=C.L2_MAX_ITER)
    p.set_defaults(func=cmd_congestion)

    p = sub.add_parser("escape-audit", help="L2 引脚场逃逸容量审计（可单独跑）")
    p.add_argument("--project", required=True)
    p.add_argument("--pairs", default=None)
    p.add_argument("--netlist", action="store_true")
    p.set_defaults(func=cmd_escape_audit)

    p = sub.add_parser("corridors", help="L2 单网走廊查询（查已缓存 corridors.json）")
    p.add_argument("--project", required=True)
    p.add_argument("--net", required=True)
    p.set_defaults(func=cmd_corridors)

    p = sub.add_parser("route", help="L3 区域路由（A*+L1 终判+ripup → 提交纪律落板）")
    p.add_argument("--project", required=True)
    p.add_argument("--net", default=None,
                   help="单网（opens.csv 该网全部对；无行则焊盘最近链）")
    p.add_argument("--pairs", default=None,
                   help="断点对 CSV（默认 <工程>/opens.csv）")
    p.add_argument("--batch", type=int, default=C.L3_BATCH,
                   help="CLI 复核批大小（默认 10，SPEC §4.2）")
    p.add_argument("--limit", type=int, default=None, help="只处理前 N 条")
    p.add_argument("--start", type=int, default=None, help="跳过前 N 条")
    p.add_argument("--dry-run", action="store_true",
                   help="只规划+L1 终判，不落板")
    p.add_argument("--no-ripup", action="store_true", help="禁用拆迁")
    p.add_argument("--no-segment", action="store_true",
                   help="禁用走廊中继分段（全部直连式 route）")
    p.add_argument("--kipy", action="store_true",
                   help="kipy IPC 落板（需运行中 KiCad 实例；默认 s-expr 直写）")
    p.add_argument("--baseline-json", default=None,
                   help="既有 DRC JSON 作基线（跳过现场基线跑）")
    p.set_defaults(func=cmd_route)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
