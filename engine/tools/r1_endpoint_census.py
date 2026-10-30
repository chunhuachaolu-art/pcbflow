# -*- coding: utf-8 -*-
"""V5-R1 W-2 端点数普查表（D8 孔普查同式；任务书钉值锚）。

读世界 boards/（R1 换版后）逐板逐网：pad 数/去重端点数/拓扑边数/分支点数/
求解段分布/拓扑总长。输出 JSON（out/v5-p5/r1/endpoint-census.json）+ 钉值
普查摘要（stdout）：每板 {网数, 2端网数, 3+端网数, 最大端点数, Steiner 点数,
method 直方图}。旧世界对照（boards-pre-r1/ 同板旧 topology 缺失 → 端点折叠
2 端=每网 2 点口径）不在此表（W-6 拓扑质量指标另出）。
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = os.path.join(ROOT, "out", "v5-p5", "boards")


def census_board(board):
    parts = {p["partition_id"]: p for p in board["partitions"]}
    rows = []
    hist = collections.Counter()
    for net in board["nets"]:
        pid = net["partitions"][0]
        p = parts[pid]
        eps = p["geometry"]["endpoints"]
        uniq = []
        for pt in eps:
            if pt not in uniq:
                uniq.append(pt)
        topo = (board.get("topology") or {}).get(pid) or {}
        hist[topo.get("provenance", {}).get("method", "?")] += 1
        rows.append({
            "net_id": net["net_id"],
            "pads": len(p["geometry"].get("pad_terminals") or []),
            "terminal_nodes": len(uniq),
            "topology_edges": len(topo.get("edges") or []),
            "steiner_points": len(topo.get("nodes") or [])
            - int(topo.get("terminal_count") or 0),
            "total_mm": topo.get("total_mm"),
            "method": topo.get("provenance", {}).get("method", "?"),
        })
    deg_hist = collections.Counter(r["terminal_nodes"] for r in rows)
    return {
        "net_count": len(rows),
        "nets": rows,
        "multi_terminal_nets": sum(1 for r in rows if r["terminal_nodes"] > 2),
        "max_degree": max((r["terminal_nodes"] for r in rows), default=0),
        "degree_histogram": {str(k): v for k, v in sorted(deg_hist.items())},
        "steiner_points_total": sum(r["steiner_points"] for r in rows),
        "topology_total_mm": round(
            sum(r["total_mm"] or 0.0 for r in rows), 6),
        "method_histogram": dict(sorted(hist.items())),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards-dir", default=BOARDS)
    ap.add_argument("--out", default=os.path.join(
        ROOT, "out", "v5-p5", "r1", "endpoint-census.json"))
    args = ap.parse_args(argv)
    out = {}
    for name in sorted(os.listdir(args.boards_dir)):
        bj = os.path.join(args.boards_dir, name, "board.json")
        if not os.path.isfile(bj):
            continue
        with open(bj, encoding="utf-8") as f:
            doc = json.load(f)
        board = doc["board"] if "board" in doc and "schema_version" not in \
            doc else doc
        out[name] = census_board(board)
        c = out[name]
        print("%-32s nets=%3d multi=%3d maxdeg=%3d sp=%4d methods=%s"
              % (name, c["net_count"], c["multi_terminal_nets"],
                 c["max_degree"], c["steiner_points_total"],
                 c["method_histogram"]), flush=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("WRITTEN %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
