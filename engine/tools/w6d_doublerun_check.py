# -*- coding: utf-8 -*-
"""W-D 双跑字节等抽查（门 4/裁 2，≥2 板）：跨进程独立复核——重载板+已落
compiled_rules，重走 plan_candidates→execute_candidate（同候选 k，k 取自
execute.json candidate_source），对比 canonical_json(routes) 与已落盘
routes_doc.routes。板上 execute 阶段已内置同进程双跑 assert（run_p5_board
854-860），本脚本为更强口径（跨进程/跨时钟独立复核）。
用法：python -B tools/w6d_doublerun_check.py <board1> <board2> [...]
产物：out/v5-p5/r1/doublerun/doublerun-report.json（append）
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5.board import load_board                   # noqa: E402
from v5.canonical import canonical_json          # noqa: E402
from v5.executor import execute_candidate        # noqa: E402
from v5.planner import plan_candidates           # noqa: E402

REPORT = os.path.join(ROOT, "out", "v5-p5", "r1", "doublerun",
                      "doublerun-report.json")


def main(argv):
    rows = []
    for b in argv:
        bd = os.path.join(ROOT, "out", "v5-p5", "boards", b)
        # 与 run_p5_board.load_stage_board 同口径：原始 board dict 须过
        # load_board（schema 校验+归一）再喂规划/执行器——首版直喂原始 dict
        # 致布线 epsilon 差异 canonical_equal 假 False（已修正重跑）
        board = load_board(json.load(open(os.path.join(bd, "board.json"),
                                          encoding="utf-8"))["board"])
        c_art = json.load(open(os.path.join(bd, "compiled.json"),
                               encoding="utf-8"))["compiled_rules"]
        exd = json.load(open(os.path.join(bd, "execute.json"),
                             encoding="utf-8"))
        m = re.match(r"plan_candidates\[(\d+)\]",
                     exd.get("candidate_source") or "")
        assert m, "%s candidate_source 形态异常: %r" % (
            b, exd.get("candidate_source"))
        k = int(m.group(1))
        t0 = time.time()
        cands = plan_candidates(board, c_art, arm="principle")
        ex = execute_candidate(board, cands[k])
        wall = round(time.time() - t0, 1)
        got = ex.get("routes")
        want = exd.get("routes_doc") \
            if isinstance(exd.get("routes_doc"), dict) else None
        # ex["routes"]=完整 routes_doc（schema_version/…/routes/…），
        # 与 run_p5_board 内置双跑（854-858）同口径：doc 整体 canonical 对比
        # （含 negotiation_log/provenance，确定性全覆盖）
        row = {
            "board": b, "candidate_k": k,
            "exec_verdict_rerun": ex["verdict"],
            "exec_verdict_ondisk": exd["execute"]["verdict"],
            "canonical_equal": (canonical_json(got) == canonical_json(want))
            if (got is not None and want is not None)
            else (got is None and want is None),
            "rerun_wall_s": wall,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        rows.append(row)
        print("%-28s k=%d verdict=%s canonical_equal=%s %.1fs"
              % (b, k, row["exec_verdict_rerun"], row["canonical_equal"],
                 wall), flush=True)
    out = {"rows": rows,
           "all_equal": all(r["canonical_equal"] for r in rows)}
    mode = "a" if os.path.isfile(REPORT) else "w"
    doc = {"runs": []}
    if mode == "a":
        try:
            doc = json.load(open(REPORT, encoding="utf-8"))
        except ValueError:
            doc = {"runs": []}
    doc["runs"].append(out)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("ALL-EQUAL" if out["all_equal"] else "MISMATCH-STOP")
    return 0 if out["all_equal"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
