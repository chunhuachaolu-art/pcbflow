"""FB-1 三臂配对实验编排（编排侧脚本；kicad-cli 调用留在 Bash）。

三臂全部在 out/coreboard-fb1/<arm>/ 的 p3 快照副本上执行；live 板零写、
datasets/ 零写、历史 out/ 产物零回写。底座板（③ 重放 + 既有 6 批 = 55
committed）由 pcbflow CLI（residual replay_board）落盘，本脚本只做：
  attempt  剩余 6 断点在底座板上的重跑（ripup=False/True 两臂各自独立产
           物）；ripup=True 直接消费 pcbagent Router.route_net(ripup=True)
           （route_grid.py 不改）；任何 SAT 候选装配拆线+落铜候选板。
  judge    批判定：候选板 DRC（Bash 侧 kicad-cli 产物 JSON）vs 底座基线
           DRC → 新增 error=0 才接受（晋升候选板为工作板）；否则整批回滚
           （候选板移入 rejected/，工作板字节不动）并记账。
  final    终检判定：severity-all 终板 vs 底座基线 vs 重放前基线双口径。

确定性：产物 JSON 无 wall-clock/主机路径；日期=声明常量 FB1_DATE。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import fb1_experiment, hashing, residual_cmd, route_grid  # noqa: E402

FB1_DATE = "2026-09-11"
FB1_ROOT = REPO / "out" / "coreboard-fb1"
BOARD_NAME = "stm32h743-coreboard-revc.kicad_pcb"
MUTE = lambda *_a: None


def _rel_repo(path):
    """仓库相对 POSIX 路径（绝对/相对输入均可；越界时返回绝对路径）。"""
    p = Path(os.path.abspath(str(path)))
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return p.as_posix()


def _sha(path):
    return hashing.sha256_file(str(path))


def _arm_dir(arm):
    d = FB1_ROOT / arm
    if not d.is_dir():
        raise SystemExit("臂目录不存在：%s" % d)
    return d


def _working_board(arm):
    return _arm_dir(arm) / "workspace" / "p3-replay" / BOARD_NAME


def _open_rows_on(bm):
    """当前板镜像 → 61 断点行（residual 同源排序与 row_id 映射）。"""
    rows = residual_cmd._read_opens_rows(bm)
    return {("RPL-%03d" % i): row
            for i, row in enumerate(sorted(rows, key=lambda r: (r["net"],
                                                                r["distance_mm"])))}


def cmd_attempt(args):
    arm_dir = _arm_dir(args.arm)
    board_path = _working_board(args.arm)
    ledger = json.loads((FB1_ROOT / "ledger-61rows.json").read_text(
        encoding="utf-8"))
    open_ids = sorted(r["row_id"] for r in ledger["rows"]
                      if not r["committed_in_baseline"])
    if args.rows:
        want = [x.strip() for x in args.rows.split(",") if x.strip()]
        bad = [x for x in want if x not in open_ids]
        if bad:
            raise SystemExit("--rows 不在开行集合：%s" % bad)
        open_ids = [x for x in open_ids if x in want]
    ripup = args.ripup == "true"

    bm = route_grid.board_model(str(board_path.parent))
    by_row = _open_rows_on(bm)
    rows_meta = {r["row_id"]: r for r in ledger["rows"]}
    for rid in open_ids:
        if rid not in by_row:
            raise SystemExit("行 %s 未能在当前板上重解析（opens 行映射漂移）"
                             % rid)
        if by_row[rid]["net"] != rows_meta[rid]["net"]:
            raise SystemExit("行 %s 网名漂移：%s != %s"
                             % (rid, by_row[rid]["net"], rows_meta[rid]["net"]))

    reg = residual_cmd._registry_maps("out/coreboard-fb1/" + args.arm)
    attempts = []
    for rid in open_ids:
        row = by_row[rid]
        meta = rows_meta[rid]
        if not ripup:
            r = route_grid.route_one(
                bm, row["net"], row["ax"], row["ay"], row["alayers"],
                row["bx"], row["by"], row["blayers"])
            norm = dict(r)
            norm["ripup_net"] = None
            norm["ripup_plan"] = None
            mode = "route_grid.route_one（ripup=False，主链同口径）"
        else:
            pa = bm["pa"]
            router = pa["Router"](bm["mirror"],
                                  legality=pa["Legality"](bm["mirror"]),
                                  corridor_of=None, log=MUTE)
            plan = router.route_net(
                row["net"], (row["ax"], row["ay"],
                             frozenset(row["alayers"])),
                (row["bx"], row["by"], frozenset(row["blayers"])),
                ripup=True)
            norm = fb1_experiment.normalize_plan(plan)
            mode = "Router.route_net(ripup=True)（pcbagent 锁定 adapter 直调）"
        attempts.append({
            "row_id": rid, "net": row["net"], "net_id": meta["net_id"],
            "bus_id": meta.get("bus_id"),
            "status": "SAT" if norm["ok"] else "UNKNOWN",
            "fail": norm["fail"], "blocks": norm["blocks"][:3],
            "ripup_net": norm["ripup_net"],
            "ripup_replan_length_mm": (norm["ripup_plan"] or {}).get(
                "length_mm") if norm.get("ripup_plan") else None,
            "norm": norm, "mode": mode,
        })

    sat = [a for a in attempts if a["norm"]["ok"]]
    routes, ripped_nets, ripup_account = [], [], []
    for a in sat:
        routes.append(fb1_experiment.plan_to_route(
            a["norm"], row_id=a["row_id"], net_id=a["net_id"],
            bus_id=a["bus_id"]))
        for (rnet, replan) in fb1_experiment.ripup_ops_of(a["norm"]):
            routes.append(fb1_experiment.plan_to_route(
                replan, row_id=None, net_id=a["net_id"], bus_id=None))
            ripped_nets.append(rnet)
            ripup_account.append({
                "ripped_net": rnet,
                "removed_nodes": fb1_experiment.count_net_nodes(
                    board_path.read_text(encoding="utf-8"), rnet),
                "needed_by_row": a["row_id"],
                "needed_by_net": a["net"],
                "why": ("洪泛封堵归因：该网铜为 %s 断点的实际阻塞者"
                        % a["row_id"]),
                "replan": {"segments": len(replan["segments"]),
                           "vias": len(replan["vias"]),
                           "length_mm": replan["length_mm"]},
            })
    ripped_nets = sorted(set(ripped_nets))
    if routes:
        if len(routes) > 10:
            raise SystemExit("批超限：routes=%d > 10（§10.4 批纪律）" % len(routes))
        board_text = board_path.read_text(encoding="utf-8")
        candidate, spans = fb1_experiment.apply_ripup_commit(
            board_text, routes, ripped_nets)
        # 候选板必须以规范板名落独立子目录（.kicad_pro 同名同目录）：
        # kicad-cli 按板文件名解析同名 .kicad_pro，名字不配即落默认规则，
        # 产生伪违规（FB1 实测踩坑：courtyards/track_width 假 error）。
        cand_dir = board_path.parent / "candidate"
        cand_dir.mkdir(exist_ok=True)
        pro = board_path.with_suffix(".kicad_pro")
        if pro.exists():
            shutil.copyfile(pro, cand_dir / pro.name)
        cand_path = cand_dir / BOARD_NAME
        cand_path.write_text(candidate, encoding="utf-8")
    else:
        spans = []
        candidate = None

    report = {
        "schema_version": fb1_experiment.FB1_SCHEMA,
        "artifact_kind": "fb1_attempt_report",
        "dataset": fb1_experiment.FB1_DATASET, "arm": args.arm,
        "ripup": ripup,
        "premise": (fb1_experiment.RIPUP_PREMISE if ripup else
                    {"premise": "no_ripup", "note": "主链冻结语义同口径"}),
        "board": {"path": str(board_path.relative_to(REPO)),
                  "sha256": _sha(board_path)},
        "open_rows": open_ids,
        "attempts": [{k: v for k, v in a.items() if k != "norm"}
                     for a in attempts],
        "proposed": {"routes": len(routes), "ripped_nets": ripped_nets,
                     "removed_spans": len(spans),
                     "ripup_account": ripup_account},
        "candidate_board_sha256": (hashing.sha256_bytes(
            candidate.encode("utf-8")) if candidate else None),
        "note": "attempts 相互独立规划（底座板障碍口径），同批互检由批 DRC "
                "裁决（§10.4）；ripup=False 臂复用 route_grid.route_one，"
                "route_grid.py 零改动",
    }
    sys.stdout.write(hashing.json_dumps(report) + "\n")


def cmd_judge(args):
    arm_dir = _arm_dir(args.arm)
    board_path = _working_board(args.arm)
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    cand_drc = json.loads(Path(args.candidate_drc).read_text(encoding="utf-8"))
    verdict = fb1_experiment.batch_verdict(baseline, cand_drc)
    verdict.update({
        "schema_version": fb1_experiment.FB1_SCHEMA,
        "artifact_kind": "fb1_batch_judgement",
        "dataset": fb1_experiment.FB1_DATASET, "arm": args.arm,
        "label": args.label, "date": FB1_DATE,
        "baseline_drc": _rel_repo(args.baseline),
        "candidate_drc": _rel_repo(args.candidate_drc),
        "unconnected": residual_cmd._unconn_count(cand_drc),
    })
    if args.candidate and verdict["accepted"]:
        pre = _sha(board_path)
        shutil.move(args.candidate, board_path)
        verdict["board_write"] = {
            "promoted": True, "board_sha256_before": pre,
            "board_sha256_after": _sha(board_path)}
    elif args.candidate:
        rej = arm_dir / "rejected"
        rej.mkdir(exist_ok=True)
        dest = rej / (args.label.replace("/", "_") + "-board.kicad_pcb")
        shutil.move(args.candidate, dest)
        verdict["board_write"] = {
            "promoted": False, "rollback": "whole-batch（候选板移入 "
            "rejected/，工作板字节未动）",
            "rejected_board": _rel_repo(dest),
            "board_sha256_unchanged": _sha(board_path)}
        verdict["board_write"]["note"] = (
            "候选板在 rejected/ 存证；候选板必须在项目目录（.kicad_pro 同级）"
            "做 DRC，否则 kicad-cli 落默认规则——本臂已修正该路径纪律")
    else:
        verdict["board_write"] = {"promoted": None,
                                  "note": "无候选板（纯判定）"}
    led_path = arm_dir / "batch-ledger.json"
    led = (json.loads(led_path.read_text(encoding="utf-8"))
           if led_path.exists() else {"arm": args.arm, "batches": []})
    led["batches"].append(verdict)
    acc = [b for b in led["batches"] if b["accepted"]]
    led["zero_new_errors_so_far"] = all(b["new_errors_vs_baseline"] == 0
                                        for b in led["batches"])
    led["zero_new_errors_accepted_batches"] = (
        all(b["new_errors_vs_baseline"] == 0 for b in acc) if acc else None)
    led["rejected_batches"] = [b["label"] for b in led["batches"]
                               if not b["accepted"]]
    led["note"] = ("zero_new_errors_so_far=含被拒批的全程原始口径；"
                   "被拒批已整批回滚（工作板字节未变），终态以 "
                   "zero_new_errors_accepted_batches + final gate 为准")
    led_path.write_text(hashing.json_dumps(led) + "\n", encoding="utf-8")
    sys.stdout.write(hashing.json_dumps(verdict) + "\n")


def cmd_final(args):
    arm_dir = _arm_dir(args.arm)
    board_path = _working_board(args.arm)
    substrate = json.loads(Path(args.substrate_all).read_text(encoding="utf-8"))
    preroute = json.loads(Path(args.preroute_all).read_text(encoding="utf-8"))
    final = json.loads(Path(args.final_all).read_text(encoding="utf-8"))
    v_sub = fb1_experiment.batch_verdict(substrate, final)
    v_pre = fb1_experiment.batch_verdict(preroute, final)
    out = {
        "schema_version": fb1_experiment.FB1_SCHEMA,
        "artifact_kind": "fb1_final_gate", "dataset": fb1_experiment.FB1_DATASET,
        "arm": args.arm, "date": FB1_DATE,
        "board_sha256": _sha(board_path),
        "unconnected": residual_cmd._unconn_count(final),
        "final_vs_substrate": v_sub,
        "final_vs_preroute": v_pre,
        "hard_gate_zero_new_error": (v_sub["new_errors_vs_baseline"] == 0
                                     and v_pre["new_errors_vs_baseline"] == 0),
    }
    sys.stdout.write(hashing.json_dumps(out) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fb1_arm_orchestrate")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("attempt")
    p.add_argument("--arm", required=True, choices=("arm0", "arm1", "arm2"))
    p.add_argument("--ripup", required=True, choices=("false", "true"))
    p.add_argument("--rows", default=None,
                   help="逗号分隔 row_id 过滤（缺省=全部开行；分批回退用）")
    p.set_defaults(func=cmd_attempt)

    p = sub.add_parser("judge")
    p.add_argument("--arm", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate-drc", required=True)
    p.add_argument("--candidate", default=None)
    p.set_defaults(func=cmd_judge)

    p = sub.add_parser("final")
    p.add_argument("--arm", required=True)
    p.add_argument("--substrate-all", required=True)
    p.add_argument("--preroute-all", required=True)
    p.add_argument("--final-all", required=True)
    p.set_defaults(func=cmd_final)

    args = ap.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
