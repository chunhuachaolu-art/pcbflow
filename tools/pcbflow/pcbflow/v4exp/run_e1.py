"""pcbflow.v4exp.run_e1 -- E1 四组对照 runner（A/B/C/D）。

CLI（stdin JSON -> stdout；无 argv）：
  {"scenario_ids": ["dev-f1-01", ...],
   "groups": ["A", "B", "C", "D"],
   "source_dir": "out/v4-experiment",
   "actions_dir": "out/v4-experiment/e1",
   "out_dir": "out/v4-experiment/e1/runs",
   "replay": false                          # 可选；true 时进入重放比对模式
  }

组语义：
* A 组：空动作基线 -- route_order 取 net_id 稳定序（字典序），无任何偏好；
* B/C/D 组：读取 actions_dir 下的 validated-actions-<sid>-<group>.json
  （validator 产物，solver 只消费 validated-actions）。文件缺失或
  blocked=true => 记 solver-run status="unknown"、routes/vias 为空、
  metrics 为空对象、blocked_from="validator"（UNKNOWN 必须可见，绝不静默
  跳过）。validator 放行但 router 拒绝动作（如 protect 未排在 route_order
  前部）=> status="unknown"、blocked_from="router"，同样可见。

正常模式：每场景 x 组写 solver-run-<sid>-<group>.json（复用 C1 router 的
solve_board 输出结构与确定性落盘字节），全部完成后写 e1-summary.json
（按组聚合 {sat_rate, mean_objective_sat, total_violations, blocked_count,
unknown_count} + 逐场景明细）。summary 中的 label 来自板快照，仅用于实验
侧分析，从不进入任何 planner 输入。

replay 模式：不写任何 run 文件；按同一输入重算每个 solver-run 的字节，
与 out_dir 下已有文件逐字节比对，写 replay-check-e1.json（逐文件
same/diff，无时间戳）。

零子进程、零 argv、零 wall-clock、零网络；同输入重放逐字节一致。
"""

from __future__ import annotations

import os

try:
    from . import model, router
    from .grid import V4ExpError
except ImportError:  # direct file run: python pcbflow/v4exp/run_e1.py
    import model
    import router
    from grid import V4ExpError

SUMMARY_SCHEMA = "pcbflow.v4exp.e1-summary/1"
REPLAY_SCHEMA = "pcbflow.v4exp.replay-check/1"
GROUP_ORDER = ("A", "B", "C", "D")
PLANNER_GROUPS = ("B", "C", "D")


# ---------------------------------------------------------------- 单次运行

def _unknown_run(sid, group, blocked_from, reason):
    """UNKNOWN 必须可见：status=unknown、metrics 全空、来源与原因入档。"""
    return {"schema": router.RUN_SCHEMA, "scenario_id": sid, "group": group,
            "solver_version": router.SOLVER_VERSION, "status": "unknown",
            "blocked_from": blocked_from, "blocked_reason": str(reason),
            "routes": [], "vias": [], "metrics": {}}


def _validated_path(actions_dir, sid, group):
    return os.path.join(actions_dir,
                        "validated-actions-%s-%s.json" % (sid, group))


def compute_run(board, group, actions_dir):
    """一个 (board, group) 的 run 字典；只计算，不落盘。"""
    sid = str(board["scenario_id"])
    if group not in GROUP_ORDER:
        raise ValueError("未知组 %r（允许 %r）" % (group, GROUP_ORDER))
    if group == "A":
        request = {"route_order": sorted(str(n["net_id"])
                                         for n in board["nets"]),
                   "group": "A"}
    else:
        path = _validated_path(actions_dir, sid, group)
        name = os.path.basename(path)
        if not os.path.exists(path):
            return _unknown_run(sid, group, "validator",
                                "validated-actions 文件缺失: %s" % name)
        validated = model.read_json(path)
        if validated.get("blocked"):
            return _unknown_run(sid, group, "validator",
                                "validator blocked: %s"
                                % validated.get("reason"))
        acc = validated.get("accepted")
        if not isinstance(acc, dict):
            return _unknown_run(sid, group, "validator",
                                "validated-actions 缺少 accepted 对象")
        request = {"route_order": list(acc["route_order"]), "group": group,
                   "corridor_preferences":
                       list(acc.get("corridor_preferences", [])),
                   "layer_preferences":
                       list(acc.get("layer_preferences", [])),
                   "protected_net_ids": list(acc.get("protect", []))}
    try:
        return router.solve_board(board, request)
    except V4ExpError as exc:
        return _unknown_run(sid, group, "router",
                            "router 拒绝动作: %s" % exc)


# ---------------------------------------------------------------- 聚合

def _violation_sum(run_dict):
    metrics = run_dict.get("metrics") or {}
    violations = metrics.get("violations") or {}
    return int(sum(int(v) for v in violations.values()))


def _run_detail(board, group, run_dict, name):
    metrics = run_dict.get("metrics") or {}
    obj = metrics.get("objective")
    return {
        "scenario_id": str(board["scenario_id"]),
        "family": str(board["family"]),
        "split": str(board["split"]),
        "label": str(board["label"]),
        "group": group,
        "status": str(run_dict.get("status")),
        "blocked_from": run_dict.get("blocked_from"),
        "objective": (float(obj) if obj is not None else None),
        "total_violations": _violation_sum(run_dict),
        "run_file": name,
    }


def build_summary(sids, groups, boards, details):
    by_group = {}
    for d in details:
        by_group.setdefault(d["group"], []).append(d)
    groups_summary = {}
    for g in groups:
        ds = by_group.get(g, [])
        n = len(ds)
        sat = sum(1 for d in ds if d["status"] == "sat")
        failed = sum(1 for d in ds if d["status"] == "failed")
        unknown = sum(1 for d in ds if d["status"] == "unknown")
        objs = [d["objective"] for d in ds
                if d["status"] == "sat" and d["objective"] is not None]
        blocked_from_counts = {}
        for d in ds:
            bf = d.get("blocked_from")
            if bf:
                blocked_from_counts[bf] = blocked_from_counts.get(bf, 0) + 1
        groups_summary[g] = {
            "runs": n,
            "sat_count": sat,
            "failed_count": failed,
            "unknown_count": unknown,
            "sat_rate": (round(sat / n, 6) if n else None),
            "mean_objective_sat": (round(sum(objs) / len(objs), 6)
                                   if objs else None),
            "total_violations": sum(d["total_violations"] for d in ds),
            "blocked_count": blocked_from_counts.get("validator", 0),
            "blocked_from_counts": blocked_from_counts,
        }
    return {"schema": SUMMARY_SCHEMA, "scenario_ids": list(sids),
            "groups": list(groups), "groups_summary": groups_summary,
            "runs": details}


# ---------------------------------------------------------------- 主流程

def _run_text(run_dict):
    """run 文件的确定性字节：canonical JSON + 单个 LF，二进制落盘。

    与 router.write_result 的差别仅在换行处理：write_result 用文本模式
    （Windows 上 \n 会被翻译成 \r\n，字节随平台漂移）；本 runner 固定 LF
    字节，保证"同输入重放逐字节一致"与平台无关。内容结构完全一致。
    """
    return (router.canonical_json(run_dict) + "\n").encode("utf-8")


def _write_run(path, run_dict):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(_run_text(run_dict))


def run(scenario_ids, groups, source_dir, actions_dir, out_dir,
        replay=False):
    bad_groups = [g for g in groups if g not in GROUP_ORDER]
    if bad_groups:
        raise ValueError("groups 只允许 A|B|C|D，收到 %r" % (bad_groups,))
    groups_known = [g for g in GROUP_ORDER if g in set(groups)]
    sids = sorted(set(str(s) for s in scenario_ids))
    if not sids:
        raise ValueError("scenario_ids 不能为空")

    boards = {}
    for sid in sids:
        path = os.path.join(source_dir, "board-snapshot-%s.json" % sid)
        if not os.path.exists(path):
            raise ValueError("板快照缺失: %s" % path)
        boards[sid] = model.read_json(path)

    if not replay:
        os.makedirs(out_dir, exist_ok=True)

    details = []
    replay_files = []
    for sid in sids:
        board = boards[sid]
        for g in groups_known:
            run_dict = compute_run(board, g, actions_dir)
            name = "solver-run-%s-%s.json" % (sid, g)
            text = _run_text(run_dict)
            if replay:
                path = os.path.join(out_dir, name)
                if not os.path.exists(path):
                    replay_files.append({"file": name, "same": False,
                                         "detail": "磁盘上缺失该 run 文件"})
                else:
                    with open(path, "rb") as f:
                        same = f.read() == text
                    replay_files.append({"file": name, "same": same,
                                         "detail": (None if same else
                                                    "重算字节与磁盘文件不一致")})
            else:
                _write_run(os.path.join(out_dir, name), run_dict)
            details.append(_run_detail(board, g, run_dict, name))

    if replay:
        check = {"schema": REPLAY_SCHEMA, "scenario_ids": sids,
                 "groups": groups_known, "files": replay_files,
                 "all_same": all(e["same"] for e in replay_files)}
        model.write_json(os.path.join(out_dir, "replay-check-e1.json"), check)
        return check
    summary = build_summary(sids, groups_known, boards, details)
    model.write_json(os.path.join(out_dir, "e1-summary.json"), summary)
    return summary


def main():
    payload = model.read_stdin_json()
    result = run(payload["scenario_ids"], payload["groups"],
                 payload["source_dir"], payload["actions_dir"],
                 payload["out_dir"],
                 replay=bool(payload.get("replay", False)))
    import sys
    sys.stdout.write(router.canonical_json(result))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
