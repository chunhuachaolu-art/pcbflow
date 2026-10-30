# -*- coding: utf-8 -*-
"""ED-X 修复批 W-X5 辅件（任务书 V5-R1-EDX-EXPORT-FIX-2026-09-26 W-X5
「驱动若不支持离线消费=tools/ 内最小加载器新件」授权分支）：W-D 四板
run-result.json 的 execute 键回填。

背景：09-25 队列 B 于 execute 阶段崩（ED-2 审计误杀）→ 四板 run-result
停在 convert 子集形态（无 execute/check 键）；09-26/27 W-D 重跑补齐
execute.json 等盘上产物但 export 阶段崩（ED-X）→ write_run_result 未执行。
本件从盘上 execute.json 回填 run["execute"]（字段形态逐一同 run_p5_board
execute 段落码）。double_run_equal=True 系 W-D 实跑内建断言（execute 段
先双跑 assert 后落盘，run_p5_board 854-860）的如实转录，另有 W-X4 跨进程
双跑抽查独立佐证（crypto/badgeleds）。不改世界树语义、不改阶段产物；
merge 语义=run_p5_board.write_run_result 同款（历史键保留、stages_run
并集——本件不新增阶段、note 如实披露回填性质）。

用法：python -B tools/edx_runresult_backfill.py <board1> <board2> [...]
产物：boards/<b>/run-result.json 原位更新（sidecar 包装同源）+ stdout 读数。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from run_p5_board import GENERATOR, VERSION, board_dir, write_stage  # noqa: E402


def backfill(board_id):
    odir = board_dir(board_id)
    with io.open(os.path.join(odir, "execute.json"), encoding="utf-8") as f:
        exd = json.load(f)
    ex = exd["execute"]
    rr_path = os.path.join(odir, "run-result.json")
    with io.open(rr_path, encoding="utf-8") as f:
        prev = (json.load(f).get("run") or {})
    run = dict(prev)
    run["execute"] = {
        "selection_verdict": exd.get("selection_verdict"),
        "candidate_source": exd.get("candidate_source"),
        "n_candidates": exd.get("n_candidates"),
        "rotate_budget": exd.get("rotate_budget"),
        "tried_candidates": exd.get("tried_candidates") or [],
        "exec_verdict": ex["verdict"],
        "per_net_count": len(ex.get("per_net") or []),
        "negotiation_log_entries": len(ex.get("negotiation_log") or []),
        "routed": exd.get("routes_doc") is not None,
        "double_run_equal": True,
        "execute_json": "out/v5-p5/boards/%s/execute.json" % board_id,
    }
    run["result_merge_note"] = (
        "ED-X 修复批 execute 键回填（tools/edx_runresult_backfill.py；"
        "源=盘上 execute.json〔W-D 实跑产物，含内建双跑 assert〕；"
        "check/export/drc 键由本批 --stages check,export,drc 离线补跑"
        "写入；stages_run 不变）")
    bsha = json.load(io.open(os.path.join(odir, "board.json"),
                             encoding="utf-8"))["board"]["provenance"]["board_sha256"]
    write_stage(rr_path, {"run": run}, bsha)
    print("%s: execute 键回填 exec_verdict=%s source=%s routed=%s"
          % (board_id, ex["verdict"], exd.get("candidate_source"),
             run["execute"]["routed"]))
    return run["execute"]


def main(argv):
    if not argv:
        raise SystemExit("用法：edx_runresult_backfill.py <board> [...]")
    for b in argv:
        backfill(b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
