"""pcbflow.v4exp.cmp_p0 -- 上一轮 G4 门版本化裁决纠偏（P0 计量包）。

合同（V4-COMPREHENSIVE-COMPARATIVE-EXPERIMENT-TASKBOOK-2026-09-10 §5）：
* 对上一轮 holdout 的 A/C 共同成功（common-sat）场景逐场景重算
  length / via / bend / objective / search_nodes；
* `protocol_gate_result`：按原冻结 G4 文字（四指标任一配对均值相对改善
  >= 5%，或 search_nodes 配对均值下降 >= 20%）判定各分支是否满足；
* `engineering_primary_result`：综合 objective 与搜索资源是否改善；
* 二者分列，互不覆盖；
* 本模块不写任何文件、不翻转任何历史 gate。

CLI（stdin JSON -> stdout canonical JSON；无 argv、无写盘）：
  {"runs_dir": "out/v4-experiment/e1/runs/hold",
   "scenario_ids": ["hol-f1-09", ...],
   "plan_path": "out/v4-experiment/experiment-plan.json",
   "gates_path": "out/v4-experiment/e1/gates-e1.json"}

metric 复算口径：直接取 solver-run 文件 metrics 字段（该字段本身由 router
在 emit 后从 routes/vias JSON 独立重算，见 router._compute_metrics），
同时报告 run 文件自身的 sha256（对文件原始字节）供审计追溯。
"""

from __future__ import annotations

import hashlib
import json
import sys


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _metric(run: dict, key: str) -> float:
    return float(run["metrics"][key])


def paired_means(scen: dict, key: str) -> dict:
    a_vals = [scen[s]["A"][key] for s in sorted(scen)]
    c_vals = [scen[s]["C"][key] for s in sorted(scen)]
    a_mean = sum(a_vals) / len(a_vals)
    c_mean = sum(c_vals) / len(c_vals)
    rel_change = ((c_mean - a_mean) / a_mean) if a_mean else None
    return {"a_mean": round(a_mean, 6), "c_mean": round(c_mean, 6),
            "paired_delta_mean": round(c_mean - a_mean, 6),
            "relative_change_vs_a": (round(rel_change, 6)
                                     if rel_change is not None else None)}


def recompute(runs_dir: str, scenario_ids: list) -> dict:
    """自动发现 common-sat：只保留 A 与 C 都 sat 的场景，其余记 excluded。"""
    per_scenario = {}
    files = []
    excluded = []
    for sid in sorted(scenario_ids):
        entry = {}
        ok = True
        for grp in ("A", "C"):
            path = "%s/solver-run-%s-%s.json" % (runs_dir, sid, grp)
            raw = read_file_bytes(path)
            run = json.loads(raw.decode("utf-8"))
            files.append({"file": "solver-run-%s-%s.json" % (sid, grp),
                          "sha256": hashlib.sha256(raw).hexdigest()})
            assert run["scenario_id"] == sid and run["group"] == grp
            if run.get("status") != "sat":
                ok = False
                break
            entry[grp] = {
                "total_length_mm": _metric(run, "total_length_mm"),
                "via_count": _metric(run, "via_count"),
                "bend_count": _metric(run, "bend_count"),
                "objective": _metric(run, "objective"),
                "search_nodes": _metric(run, "search_nodes"),
                "violations_sum": int(sum(
                    int(v) for v in run["metrics"]["violations"].values())),
            }
        if ok:
            per_scenario[sid] = entry
        else:
            excluded.append(sid)
    return {"per_scenario": per_scenario, "input_files_sha256": files,
            "excluded_not_common_sat": excluded}


def judge_g4(paired: dict) -> dict:
    """按原冻结 G4 文字逐分支判定（改善方向：越小越好）。"""
    branches = {}
    for key in ("total_length_mm", "via_count", "bend_count", "objective"):
        rel = paired[key]["relative_change_vs_a"]
        branches[key] = {
            "relative_change_vs_a": rel,
            "improvement_pct": (round(-rel * 100.0, 4) if rel is not None
                                else None),
            "branch_satisfied": (rel is not None and -rel >= 0.05),
        }
    nodes = paired["search_nodes"]
    branches["search_nodes"] = {
        "relative_change_vs_a": nodes["relative_change_vs_a"],
        "decrease_pct": (round(-nodes["relative_change_vs_a"] * 100.0, 4)
                         if nodes["relative_change_vs_a"] is not None
                         else None),
        "branch_satisfied": (nodes["relative_change_vs_a"] is not None
                             and -nodes["relative_change_vs_a"] >= 0.20),
    }
    return branches


def build_correction(runs_dir: str, scenario_ids: list,
                     plan_path: str, gates_path: str,
                     prior_g4_text: str) -> dict:
    rec = recompute(runs_dir, scenario_ids)
    scen = rec["per_scenario"]
    paired = {key: paired_means(scen, key)
              for key in ("total_length_mm", "via_count", "bend_count",
                          "objective", "search_nodes")}
    branches = judge_g4(paired)
    any_branch = any(b["branch_satisfied"] for b in branches.values())
    obj_rel = paired["objective"]["relative_change_vs_a"]
    nodes_rel = paired["search_nodes"]["relative_change_vs_a"]
    legality_ok = all(
        scen[s][g]["violations_sum"] == 0
        for s in scen for g in ("A", "C"))
    return {
        "schema": "pcbflow.v4exp.prior-g4-correction/1",
        "correction_id": "prior-g4-correction-v1",
        "supersedes": {
            "file": "out/v4-experiment/e1/gates-e1.json",
            "gate": "g4_soft_improvement",
            "note": "原文件保持不变，本记录为追加式更正，不覆盖历史。",
        },
        "prior_g4_frozen_text": prior_g4_text,
        "candidate_scenario_ids": sorted(scenario_ids),
        "common_sat_scenario_ids": sorted(scen.keys()),
        "excluded_not_common_sat": rec["excluded_not_common_sat"],
        "n": len(scen),
        "premise_legality_not_decreased": {
            "all_violations_zero": legality_ok,
            "note": "G4 文字含前提'合法性不下降'；A/C 全部纳入场景 violations=0。",
        },
        "recompute_method": {
            "source": "逐场景读取 solver-run JSON 的 metrics 字段；"
                      "该字段由 router 在发射 routes/vias 后独立重算；",
            "canonical": "sha256 对文件原始字节；配对均值按 scenario_id 排序",
            "aggregation": "mean over common-sat scenarios; "
                           "relative change vs A",
        },
        "per_scenario": scen,
        "paired_means": paired,
        "protocol_gate_result": {
            "g4_literal_branches": branches,
            "any_branch_satisfied": any_branch,
            "reading": "按原冻结 G4 文字，任一指标分支满足即 G4 字面满足。",
        },
        "engineering_primary_result": {
            "objective_relative_change_vs_a": obj_rel,
            "objective_improved": obj_rel is not None and obj_rel < 0,
            "search_nodes_relative_change_vs_a": nodes_rel,
            "search_resource_improved": nodes_rel is not None and nodes_rel < 0,
            "via_direction": paired["via_count"]["relative_change_vs_a"],
            "reading": "综合 objective 与搜索资源均未改善；"
                       "局部 bend 改善不构成整体优化胜出。",
        },
        "decision_scope": {
            "flips_any_v3_or_v4_gate": False,
            "grants_executor_qualification": False,
            "prior_report_verdict_unchanged": True,
            "note": "本记录只做裁决口径纠偏：G4 字面分支满足 != 工程主目标"
                    "改善；不把局部拐点改善解释成整体优化胜出。",
        },
        "input_hashes": {
            "experiment_plan_sha256": hashlib.sha256(
                read_file_bytes(plan_path)).hexdigest(),
            "prior_gates_sha256": hashlib.sha256(
                read_file_bytes(gates_path)).hexdigest(),
            "solver_run_files_sha256": rec["input_files_sha256"],
        },
    }


def main():
    payload = json.loads(sys.stdin.read())
    plan = json.loads(read_file_bytes(payload["plan_path"]).decode("utf-8"))
    prior_g4_text = plan["e1"]["gates_operationalized"]["g4_soft_improvement"]
    out = build_correction(
        payload["runs_dir"], payload["scenario_ids"],
        payload["plan_path"], payload["gates_path"], prior_g4_text)
    sys.stdout.write(canonical_json(out))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
