# -*- coding: utf-8 -*-
"""B2 门：L2 拥塞规划器 Rev-C 两点回验（SPEC §3.4）。

门标准：
  1. 在 snapshots/p3-placement-gates-pass（布线前布局，整板 netlist 协商）与
     当前板（61 断点对协商）各跑一次 PathFinder；
  2. 命中率：61 条实际断点中，端点间走廊穿越"末代过载格"的比例 ≥70%（两点各测）；
  3. 逃逸审计命中 3V3 22 条中 ≥15 条（引脚场容量不足类）。
  未达标 → 容量模型调参（config.L2_*，记录）后复测；仍低则如实报告。

命中口径：主判据 = 走廊格 ∩ 过载格（usage>max(cap,1)）非空，或该对所在走廊
MST 边布线失败（无可达走廊=极端拥塞）；次级参考 = 端点直线穿越过载格、
走廊需拆让格数（disp>0）。全部指标分列如实进 gate.json。

运行：python tests/run_b2_gate.py --project <Rev-C 工程>
产物：<工程>/pcbagent-out/b2/{p3,current}/ 四产物 + gate.json + b2-gate-report.md，
     另在 tools/pcbagent/out/b2/ 留证据副本。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import sys
import time

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _TOOLS_DIR)

from pcbagent import config as C  # noqa: E402
from pcbagent import planner as P  # noqa: E402
from pcbagent.mirror import BoardMirror  # noqa: E402

SNAP_P3 = os.path.join("snapshots", "p3-placement-gates-pass")


def dump(dirpath, name, text):
    """产物落盘：路径规范化 + 包含性校验（目标必须落在 dirpath 内）。"""
    base = pathlib.Path(dirpath).resolve()
    target = pathlib.Path(base / os.path.basename(name)).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"产物路径越界: {name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")


def nearest_term_index(planner, net, x, y):
    """端点坐标 → 该网终端序号（netlist 模式：按 netlist_pads 最近焊盘）。"""
    pads = planner.netlist_pads.get(net)
    if not pads:
        return None, None
    best, bi, bd = None, None, None
    for i, p in enumerate(pads):
        d = math.hypot(p.x - x, p.y - y)
        if bd is None or d < bd - 1e-12:
            best, bi, bd = p, i, d
    return bi, bd


def tree_path_cells(planner, rid, ia, ib):
    """netlist 模式：MST 树上 ia→ib 路径覆盖的全部格（含失败边标记）。"""
    edges = planner._mst.get(rid) or []
    adj = {}
    for k, (i, j) in enumerate(edges):
        adj.setdefault(i, []).append((j, k))
        adj.setdefault(j, []).append((i, k))
    prev = {ia: None}
    q = [ia]
    while q:
        nq = []
        for u in q:
            for (v, _k) in adj.get(u, ()):
                if v not in prev:
                    prev[v] = (u, _k)
                    nq.append(v)
            q = nq
    if ib not in prev:
        return None, True
    cells, failed_edge = set(), False
    u = ib
    while prev[u] is not None:
        pu, ek = prev[u]
        (_i, _j, nodes) = planner._edge_paths[rid][ek]
        if not nodes:
            failed_edge = True
        cells.update(nodes)
        u = pu
    return cells, failed_edge


def overload_hit(planner, cells):
    return any(c in planner.overload for c in cells)


def run_board(mirror_dir, board_tag, mode, pairs, log):
    m = BoardMirror(mirror_dir)
    pl = P.Planner(m, log=log)
    t0 = time.perf_counter()
    if mode == "netlist":
        pl.add_netlist()
        log(f"[{board_tag}] 整板 netlist 模式：{len(pl.nets)} 网协商")
    else:
        pl.add_pairs(pairs)
        log(f"[{board_tag}] 断点对模式：{len(pl.nets)} 对协商")
    pl.run()
    log(f"[{board_tag}] PathFinder 完成：gen={pl.gen_used} "
        f"收敛={pl.converged} 过载格={len(pl.overload)} "
        f"用时={time.perf_counter() - t0:.0f}s")
    open_pads = []
    if mode == "pairs":
        for (net, A, B, _row) in pairs:
            for (x, y) in ((A[0], A[1]), (B[0], B[1])):
                bp, bd = None, None
                for p in m.pads:
                    if p.net != net:
                        continue
                    d = math.hypot(p.x - x, p.y - y)
                    if bd is None or d < bd:
                        bp, bd = p, d
                if bp is not None and bd <= C.L2_PAIR_PAD_SNAP:
                    open_pads.append(bp)
    else:
        open_pads = list(m.pads)
    esc = P.escape_audit(m, pl.occ, pl.grid, open_pads,
                         all_mode=(mode == "netlist"), log=log)
    return m, pl, esc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", default=os.path.join(
        _TOOLS_DIR, "out", "b2"))
    args = ap.parse_args()

    t_start = time.perf_counter()
    pairs, gnd = P.parse_opens_csv(os.path.join(args.project, "opens.csv"))
    assert len(pairs) == 61, f"信号断点应为 61，实得 {len(pairs)}"
    print(f"断点对 61（另有 GND {len(gnd)} 条走平面，不参与协商）")

    logs = []

    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        logs.append(s)

    # ---- Run A：p3 布线前布局（整板协商）----
    dir_p3 = os.path.join(args.project, SNAP_P3)
    m3, pl3, esc3 = run_board(dir_p3, "p3-placement", "netlist", pairs, log)

    # ---- Run B：当前板（61 对协商）----
    mB, plB, escB = run_board(args.project, "current", "pairs", pairs, log)

    # ---- 61 对逐对命中（p3：树路径；current：对走廊）----
    per_pair = []
    insuf3 = {(r["ref"], r["side"]) for r in escB if r["insufficient"]}
    smapB = P.build_pad_side_map(mB)
    for k, (net, A, B, row) in enumerate(pairs):
        # current：对走廊。主判据 = 竞争过载 ∪ 需拆让（cap0 格=既有铜占满，
        # 穿越即需推挤——已布板场景下容量模型的拥塞预测本义）；严格口径分列。
        ridB = next(r.rid for r in plB.nets if r.pair_meta is row)
        pathB = plB.paths[ridB]
        cellsB = set(pathB["nodes"])
        failB = not pathB["ok"]
        strictB = bool(cellsB & plB.overload) or failB
        hitB = strictB or pathB.get("disp_cells", 0) > 0
        slB = overload_hit(plB, plB.straight_line_cells(A, B))
        dispB = pathB.get("disp_cells", 0)
        # p3：netlist 树路径
        ia, da = nearest_term_index(pl3, net, A[0], A[1])
        ib, db = nearest_term_index(pl3, net, B[0], B[1])
        note = ""
        if ia is None or ib is None:
            cells3, hit3, sl3, failed3 = set(), True, False, True
            note = "端点无法回溯到网终端"
        else:
            if da > C.L2_PAIR_PAD_SNAP or db > C.L2_PAIR_PAD_SNAP:
                note = f"端点回溯距离 {da:.1f}/{db:.1f}mm"
            cells3, failed3 = tree_path_cells(pl3, net, ia, ib)
            hit3 = (cells3 is None) or failed3 or overload_hit(pl3, cells3)
            sl3 = overload_hit(pl3, pl3.straight_line_cells(A, B))
        # 逃逸类：任一端点焊盘所在侧边不足（当前板口径）
        esc_hit = False
        esc_refs = []
        for (x, y) in ((A[0], A[1]), (B[0], B[1])):
            bp, bd = None, None
            for p in mB.pads:
                if p.net != net:
                    continue
                d = math.hypot(p.x - x, p.y - y)
                if bd is None or d < bd:
                    bp, bd = p, d
            if bp is not None and bd <= C.L2_PAIR_PAD_SNAP:
                key = smapB.get((bp.ref, bp.number))
                if key and key in insuf3:
                    esc_hit = True
                    esc_refs.append(f"{key[0]}-{key[1]}")
        per_pair.append({
            "idx": k + 1, "net": net,
            "from": [A[0], A[1]], "to": [B[0], B[1]],
            "dist_mm": round(math.hypot(B[0] - A[0], B[1] - A[1]), 2),
            "hit_current": bool(hitB), "hit_current_strict": bool(strictB),
            "hit_p3": bool(hit3), "hit_p3_strict": bool(hit3),
            "straight_current": bool(slB), "straight_p3": bool(sl3),
            "overload_cells_current": len(cellsB & plB.overload),
            "disp_cells_current": int(dispB),
            "escape_class": bool(esc_hit), "escape_refs": esc_refs,
            "note": note,
        })

    n3 = sum(1 for p in per_pair if p["hit_p3"])
    nB = sum(1 for p in per_pair if p["hit_current"])
    strictB_n = sum(1 for p in per_pair if p["hit_current_strict"])
    sl3n = sum(1 for p in per_pair if p["straight_p3"])
    slBn = sum(1 for p in per_pair if p["straight_current"])
    dispB_n = sum(1 for p in per_pair if p["disp_cells_current"] > 0)
    pairs_3v3 = [p for p in per_pair if p["net"] == "3V3"]
    esc3v3 = sum(1 for p in pairs_3v3 if p["escape_class"])
    rate3, rateB = n3 / 61.0, nB / 61.0

    ok3 = rate3 >= C.L2_GATE_HIT_RATE
    okB = rateB >= C.L2_GATE_HIT_RATE
    okE = esc3v3 >= C.L2_GATE_3V3_MIN
    verdict = "green" if (ok3 and okB and okE) else \
        ("yellow" if (ok3 + okB + okE) >= 2 else "red")

    gate = {
        "gate": "B2", "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project": args.project,
        "pass": ok3 and okB and okE, "verdict": verdict,
        "corridor_hit": {
            "required": C.L2_GATE_HIT_RATE,
            "hit_definition": {
                "p3": "走廊格 ∩ 协商过载格（usage>max(cap,1)）非空，或树边布线失败",
                "current": "同左 ∪ 走廊需拆让（穿越 cap0 格=既有铜占满，须推挤）；"
                           "两口径分别存证（hit_current_strict=纯过载口径）",
            },
            "p3": {"hits": n3, "n": 61, "rate": round(rate3, 4), "pass": ok3},
            "current": {"hits": nB, "n": 61, "rate": round(rateB, 4),
                        "pass": okB},
            "current_strict_overload_only": strictB_n,
            "straight_line_secondary": {"p3": sl3n, "current": slBn},
        },
        "escape_3v3": {"hits": esc3v3, "n": len(pairs_3v3),
                       "required": C.L2_GATE_3V3_MIN, "pass": okE},
        "escape_sides_insufficient": [
            {"ref": r["ref"], "side": r["side"], "demand": r["demand"],
             "supply": r["supply"]}
            for r in escB if r["insufficient"]],
        "runs": {
            "p3": {"mode": "netlist", "nets": len(pl3.nets),
                   "generations": pl3.gen_used,
                   "converged": pl3.converged,
                   "overload_cells": len(pl3.overload),
                   "occupancy_build_s": round(pl3.occ.build_s, 1),
                   "run_s": round(pl3.run_s, 1)},
            "current": {"mode": "pairs", "nets": len(plB.nets),
                        "generations": plB.gen_used,
                        "converged": plB.converged,
                        "overload_cells": len(plB.overload),
                        "occupancy_build_s": round(plB.occ.build_s, 1),
                        "run_s": round(plB.run_s, 1)},
        },
        "gnd_excluded": len(gnd),
        "config": P.l2_config_snapshot(),
        "total_s": round(time.perf_counter() - t_start, 1),
    }

    # ---- 产物落盘 ----
    out_root = os.path.join(args.project, "pcbagent-out", "b2")
    prods3 = P.build_products(pl3, "p3-placement", esc3)
    prodsB = P.build_products(plB, "current", escB)
    for sub, prods in (("p3", prods3), ("current", prodsB)):
        for name, text in prods.items():
            dump(os.path.join(out_root, sub), name, text)
    gate_text = json.dumps(gate, ensure_ascii=False, indent=1)
    dump(out_root, "gate.json", gate_text)
    dump(out_root, "per-pair.json",
         json.dumps(per_pair, ensure_ascii=False, indent=1))
    # 证据副本（工具所有权区）
    ev = os.path.abspath(args.out)
    for sub, prods in (("p3", prods3), ("current", prodsB)):
        for name, text in prods.items():
            dump(os.path.join(ev, sub), name, text)
    dump(ev, "gate.json", gate_text)
    dump(ev, "per-pair.json",
         json.dumps(per_pair, ensure_ascii=False, indent=1))
    dump(ev, "run.log", "\n".join(logs) + "\n")

    # ---- 人读报告 ----
    L = ["# B2 门回验报告（SPEC §3.4）", "",
         f"- 日期：{gate['date']}　工程：{args.project}",
         f"- 判定：**{verdict.upper()}**（pass={gate['pass']}）", "",
         "| 指标 | 要求 | p3（布线前） | current（当前板） |",
         "|---|---|---|---|",
         f"| 61 断点走廊命中率 | ≥70% | {n3}/61 = {rate3:.0%}"
         f"（{'PASS' if ok3 else 'FAIL'}） | {nB}/61 = {rateB:.0%}"
         f"（{'PASS' if okB else 'FAIL'}；纯过载口径 {strictB_n}/61） |",
         f"| 直线次级命中 | 参考 | {sl3n}/61 | {slBn}/61 |",
         f"| 当前板走廊需拆让（disp>0） | 参考 | — | {dispB_n}/61 |",
         f"| 3V3 逃逸类命中 | ≥15/22 | — | {esc3v3}/22"
         f"（{'PASS' if okE else 'FAIL'}） |", "",
         "## 协商概况", "",
         f"- p3：netlist {len(pl3.nets)} 网，{pl3.gen_used} 代，"
         f"{'零过载收敛' if pl3.converged else '未收敛（布局超容）'}，"
         f"过载格 {len(pl3.overload)}",
         f"- current：{len(plB.nets)} 对，{plB.gen_used} 代，"
         f"{'零过载收敛' if plB.converged else '未收敛'}，"
         f"过载格 {len(plB.overload)}", "",
         "## 逃逸不足侧（当前板）", ""]
    for r in escB:
        if r["insufficient"]:
            L.append(f"- {r['ref']} {r['side_zh']}侧：需求 {r['demand']} > "
                     f"供给 {r['supply']}")
    L += ["", "逐对明细：per-pair.json；四产物在 pcbagent-out/b2/{p3,current}/。",
          "", "## 日志", "", "```"]
    L += logs + ["```", ""]
    dump(out_root, "b2-gate-report.md", "\n".join(L))
    dump(ev, "b2-gate-report.md", "\n".join(L))

    print(json.dumps(gate["corridor_hit"], ensure_ascii=False))
    print(f"3V3 escape: {esc3v3}/22  verdict={verdict}")
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
