# -*- coding: utf-8 -*-
"""CANVAS-PILOT-R1 根编排脚本（Bash 驱动; 模型席位=编排体 Agent 工具派发）。

子命令:
  init <board>            新画板状态（首块状态落盘; prereg 前仅建设期自检用）
  new-round <board>       打包下一轮盲包 → 轮号+路径
  ingest <board> <round> <batch.json>   fail-closed 收批
  status <board>          连通/DRC 读数
  export <board>          终态 → v5.routes.v1 复核 + staging kicad_pcb 导出
  drc <board>             kicad-cli DRC（P5-UP3-aggregate-v1: 5 跑×至多 3 轮）
  ledger-verify           台账全链重算
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canvas_pilot import loop  # noqa: E402
from canvas_pilot.ledger import Ledger  # noqa: E402


def ledger():
    return Ledger(os.path.join(loop.OUT, "ledger.jsonl"))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, board = argv[1], argv[2] if len(argv) > 2 else None
    lg = ledger()
    if cmd == "init":
        st = loop.new_canvas_state(board)
        loop.save_state(st)
        lg.append("canvas_init", {"board": board,
                                  "board_sha256": st.board_sha256,
                                  "lattice": st.lattice.as_dict(),
                                  "anchors": st.anchors})
        print(json.dumps({"board": board, "board_sha256": st.board_sha256,
                          "lattice": st.lattice.as_dict()}, indent=1))
        return 0
    if cmd == "new-round":
        n, rd = loop.new_round(board, lg)
        print(json.dumps({"round": n, "dir": rd}, indent=1))
        return 0
    if cmd == "ingest":
        n = int(argv[3])
        res = loop.ingest(board, n, argv[4], lg)
        print(json.dumps({k: res[k] for k in (
            "board", "round", "outcome", "accepted", "rejected",
            "routed_nets", "total_nets", "unrouted") if k in res},
                         indent=1, ensure_ascii=False))
        return 0
    if cmd == "status":
        print(json.dumps(loop.status(board), indent=1, ensure_ascii=False))
        return 0
    if cmd == "export":
        return cmd_export(board, lg)
    if cmd == "drc":
        return cmd_drc(board, lg)
    if cmd == "ledger-verify":
        ok, n, bad = lg.verify()
        print(json.dumps({"ok": ok, "records": n, "first_bad": bad}))
        return 0 if ok else 1
    print(__doc__)
    return 2


def cmd_export(board, lg):
    from v5.route_check import validate_routes
    from v5.kicad_export import kicad_pcb_bytes
    st = loop.load_state(board)
    doc = loop.build_routes_doc(st)
    validate_routes(st.board, doc)  # v5 同源复核（fail-closed 抛错即败）
    staging = os.path.join(loop.OUT, "final", board)
    os.makedirs(staging, exist_ok=True)
    pcb = kicad_pcb_bytes(st.board, doc)
    path = os.path.join(staging, "canvas-final.kicad_pcb")
    with open(path, "wb") as f:
        f.write(pcb)
    with open(os.path.join(staging, "canvas-final.routes.json"), "wb") as f:
        from v5.canonical import canonical_json
        f.write(canonical_json(doc))
    import hashlib
    sha = hashlib.sha256(pcb).hexdigest()
    lg.append("final_export", {"board": board, "pcb_sha256": sha,
                               "routes_n": len(doc["routes"])})
    print(json.dumps({"pcb": path, "pcb_sha256": sha,
                      "routes_n": len(doc["routes"])}, indent=1))
    return 0


def cmd_drc(board, lg):
    """kicad-cli DRC, P5-UP3-aggregate-v1 口径（每轮 5 跑、至多 3 轮、无
    全等轮=union-max+披露）。只跑 staging 副本（红线②）。"""
    import subprocess
    import tempfile
    staging = os.path.join(loop.OUT, "final", board)
    src = os.path.join(staging, "canvas-final.kicad_pcb")
    kicad = "F:/kicad/bin/kicad-cli.exe"
    runs = []
    for k in range(5):
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, "run.kicad_pcb")
            data = open(src, "rb").read()
            open(tmp, "wb").write(data)
            p = subprocess.run(
                [kicad, "pcb", "drc", "--format", "json", "--severity-all",
                 "--output", os.path.join(td, "drc.json"), tmp],
                capture_output=True, text=True, timeout=600, cwd=td)
            rep = open(os.path.join(td, "drc.json"), "r",
                       encoding="utf-8").read()
            runs.append(rep)
    uniq = set(runs)
    import hashlib
    lg.append("drc_runs", {
        "board": board, "n_runs": len(runs), "n_distinct": len(uniq),
        "digests": [hashlib.sha256(r.encode("utf-8")).hexdigest()[:16]
                    for r in runs]})
    out = os.path.join(staging, "drc-aggregate.json")
    agg = {"n_runs": len(runs), "n_distinct": len(uniq),
           "runs_identical": len(uniq) == 1,
           "runs": [json.loads(r) for r in runs]}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=1)
    viol = agg["runs"][0].get("violations", []) if agg["runs"] else []
    print(json.dumps({"n_runs": agg["n_runs"], "identical": agg["runs_identical"],
                      "violations_run0": len(viol), "report": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
