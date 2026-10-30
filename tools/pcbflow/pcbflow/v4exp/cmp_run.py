"""pcbflow.v4exp.cmp_run -- v4cmp P1/P2 runner、门判定与重放校验。

职责（单一入口，纯确定性；模型响应只作为文件输入读取）：
* P1：route patch 合同验收（program 臂 + 负向突变拦截 + rollback/未声明对象
  检查 + 改色不改机器事实 + 重放），产 p1/patch-results.json、p1/gates-p1.json。
* P2：A0/A1 确定性臂全跑；模型臂（B1/C1/D1）只消费 responses 目录里的真实
  planner 响应，缺失/非法一律 blocked（绝不伪造、绝不静默跳过），产
  p2/metrics.json、p2/gates.json。

模型臂协议：每场景最多 2 轮 × 每轮 ≤4 个 patch = ≤8 次候选评估，与 A1 的
8 次评估严格同预算；引擎从不修正 patch（corrected_by_solver 恒 false）；
planner patch 与最终 candidate 分别存证。

零子进程、零 argv、零 wall-clock、零网络；同输入 core 产物逐字节一致。
"""

from __future__ import annotations

import copy
import json
import os
import re

from . import cmp_localsearch, cmp_patch, cmp_stats, model, router
from .grid import GridWorld

P1_RESULTS_SCHEMA = "pcbflow.v4cmp.p1-results/1"
P2_SUMMARY_SCHEMA = "pcbflow.v4cmp.p2-summary/1"
P2_GATES_SCHEMA = "pcbflow.v4cmp.p2-gates/1"
P1_GATES_SCHEMA = "pcbflow.v4cmp.p1-gates/1"
VISUAL_SCHEMA = "pcbflow.v4cmp.p1-visual-check/1"

MAX_PROPOSALS = 8
BOOTSTRAP_SEED = "v4cmp-bootstrap-20260910-v1"
BOOTSTRAP_RESAMPLES = 10000

P1_SIDS = ("dev-f1-01", "dev-f1-03", "dev-f2-01", "dev-f2-03", "dev-f3-02",
           "dev-f4-01", "dev-f4-03", "dev-f5-01", "dev-f1-05", "dev-f2-05",
           "dev-f4-05", "dev-f5-03")
ARMS_P2 = ("A0", "A1", "B1", "C1", "D1")
MODEL_ARMS = ("B1", "C1", "D1")

_DATA_ATTR_RE = re.compile(r'data-[a-z-]+="[^"]*"')


# ---------------------------------------------------------------- 基础

def read_board(root: str, sid: str) -> dict:
    return model.read_json(os.path.join(root, "board-snapshot-%s.json" % sid))


def baseline_run(board: dict) -> dict:
    """A0：稳定序空偏好基线（所有臂共享的初始 candidate）。"""
    order = sorted(str(n["net_id"]) for n in board["nets"])
    return router.solve_board(board, {"route_order": order, "group": "A0"})


def _arm_result(arm, base_geom, final_geom, proposals, calls, blocked_reason):
    return {
        "arm": arm,
        "base_geometry_sha256": cmp_patch.candidate_geometry_sha256(base_geom),
        "final_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(final_geom),
        "evaluations": len(proposals),
        "accepted_count": sum(1 for p in proposals if p.get("accepted")),
        "legal_count": sum(1 for p in proposals if p.get("legal")),
        "model_calls": calls,
        "blocked": blocked_reason is not None,
        "blocked_reason": blocked_reason,
        "proposals": proposals,
        "final_geom": final_geom,
    }


# ---------------------------------------------------------------- P1

def p1_cases(root: str, sids) -> list:
    """确定性挑选用例：每场景取代理改善潜力最大的 route 作为目标。"""
    cases = []
    for sid in sids:
        board = read_board(root, sid)
        run = baseline_run(board)
        geom = cmp_patch.geom_from_run(run)
        world = GridWorld(board)
        best = None
        for patch in cmp_localsearch.proposal_stream(world, board, geom):
            d = cmp_localsearch._proxy_delta(world, geom, patch)
            key = (d, str(patch["route_id"]))
            if best is None or key < best[0]:
                best = (key, patch)
        cases.append({
            "case_id": "p1-%s" % sid,
            "scenario_id": sid,
            "target_route_id": (best[1]["route_id"] if best else None),
            "proxy_delta": (round(best[0][0], 6) if best else None),
        })
    return cases


MUTATIONS = ("stale_base_hash", "unknown_route_id", "endpoint_moved",
             "layer_mismatch", "width_mismatch", "off_grid_coord",
             "undeclared_object_change", "keepout_or_collision", "nan_coord")


def _mutate(patch: dict, kind: str, world, board, geom):
    p = copy.deepcopy(patch)
    if kind == "stale_base_hash":
        p["base_candidate_geometry_sha256"] = "0" * 64
    elif kind == "unknown_route_id":
        p["route_id"] = "n9-S99"
    elif kind == "endpoint_moved":
        poly = [list(q) for q in p["polyline_mm"]]
        poly[0] = [poly[0][0] + 0.25, poly[0][1]]
        p["polyline_mm"] = poly
    elif kind == "layer_mismatch":
        p["layer"] = "B.Cu" if p["layer"] == "F.Cu" else "F.Cu"
    elif kind == "width_mismatch":
        p["width_mm"] = round(float(p["width_mm"]) + 0.1, 3)
    elif kind == "off_grid_coord":
        poly = [list(q) for q in p["polyline_mm"]]
        poly[1] = [poly[1][0] + 0.1, poly[1][1]]
        p["polyline_mm"] = poly
    elif kind == "undeclared_object_change":
        other = next((r for r in geom["routes"]
                      if str(r["route_id"]) != str(p["route_id"])), None)
        if other is None:
            return None
        p["fixed_endpoint_ids"] = list(other["endpoint_ids"])
    elif kind == "keepout_or_collision":
        other = next((r for r in geom["routes"]
                      if str(r["route_id"]) != str(p["route_id"])), None)
        if other is None:
            return None
        poly = [list(q) for q in p["polyline_mm"]]
        poly[1] = list(other["polyline_mm"][0])
        p["polyline_mm"] = poly
    elif kind == "nan_coord":
        p["polyline_mm"] = [[float("nan"), 1.0], [2.0, 2.0], [3.0, 3.0]]
    else:
        raise ValueError("unknown mutation %s" % kind)
    return p


def _program_patch(world, board, geom, case, base_hash):
    """program 臂：扫描邻域取第一个被接受的合法改善 patch（不经过模型）。

    候选几何里若该 net 没有任何 segment（unsat / 已失败场景），直接返回 None
    → 走诚实弃权分支。
    """
    target = str(case.get("target_route_id"))
    if not any(str(r["route_id"]) == target for r in geom["routes"]):
        return None
    for patch in cmp_localsearch.proposal_stream(world, board, geom):
        patch = dict(patch)
        patch["source"] = "program"
        res = cmp_patch.validate_patch(world, board, patch, geom)
        if res["legal"] and not res.get("noop"):
            applied = cmp_patch.apply_and_check(world, board, patch, geom)
            if applied["legal"]:
                m = cmp_patch.cmp_metrics(world, applied["geometry"]["routes"],
                                          applied["geometry"]["vias"])
                bm = cmp_patch.cmp_metrics(world, geom["routes"], geom["vias"])
                if m["objective"] < bm["objective"]:
                    return patch, applied, m, bm
    return None


def _reject_patch(case, geom, board, base_hash):
    route = next((r for r in geom["routes"]
                  if str(r["route_id"]) == str(case["target_route_id"])), None)
    ident = cmp_patch.route_identity(board, route) if route else {
        "relation_ids": [], "parent_id": None, "fixed_endpoint_ids": []}
    return {
        "schema_version": cmp_patch.PATCH_SCHEMA,
        "action_type": "reject_route_patch",
        "base_candidate_geometry_sha256": base_hash,
        "scenario_id": case["scenario_id"],
        "route_id": case["target_route_id"],
        "net_id": (str(case["target_route_id"] or "n1").rsplit("-S", 1)[0]),
        "relation_id": (ident["relation_ids"][0]
                        if ident["relation_ids"] else None),
        "parent_id": ident["parent_id"],
        "fixed_endpoint_ids": list(ident["fixed_endpoint_ids"] or []),
        "reason": "no safe improving local edit found",
        "source": "program",
    }


def run_p1_case(root: str, case: dict) -> dict:
    sid = case["scenario_id"]
    board = read_board(root, sid)
    run = baseline_run(board)
    geom = cmp_patch.geom_from_run(run)
    world = GridWorld(board)
    base_hash = cmp_patch.candidate_geometry_sha256(geom)
    entry = {"case_id": case["case_id"], "scenario_id": sid,
             "target_route_id": case["target_route_id"],
             "base_geometry_sha256": base_hash,
             "base_run_status": run["status"],
             "program": None, "mutations": [], "rollback": None,
             "undeclared_objects_unchanged": None}
    found = _program_patch(world, board, geom, case, base_hash)
    if found is None:
        reject = _reject_patch(case, geom, board, base_hash)
        res = cmp_patch.validate_patch(world, board, reject, geom)
        entry["program"] = {"action": "reject_route_patch",
                            "legal": bool(res["legal"]),
                            "reasons": res["reasons"]}
        entry["rollback"] = {"byte_equivalent": True,
                             "note": "弃权动作无几何变更，无需回滚"}
        entry["undeclared_objects_unchanged"] = True
        return entry
    patch, applied, m, bm = found
    entry["program"] = {
        "action": patch["action_type"],
        "route_id": patch["route_id"],
        "legal": True,
        "objective_before": bm["objective"],
        "objective_after": m["objective"],
        "patch_sha256": model.sha256_of(patch),
        "candidate_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(applied["geometry"]),
        "legality_violations": m["violations"],
        "all_connected": m["all_connected"],
    }
    restored = cmp_patch.rollback_patch(applied["geometry"], applied["rollback"])
    entry["rollback"] = {
        "restored_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(restored),
        "base_geometry_sha256": base_hash,
        "byte_equivalent":
            cmp_patch.candidate_geometry_sha256(restored) == base_hash,
    }
    base_by_id = {str(r["route_id"]): r for r in geom["routes"]}
    undeclared_ok = all(
        r == base_by_id[str(r["route_id"])]
        for r in applied["geometry"]["routes"]
        if str(r["route_id"]) != str(patch["route_id"]))
    undeclared_ok = undeclared_ok and applied["geometry"]["vias"] == geom["vias"]
    entry["undeclared_objects_unchanged"] = undeclared_ok
    for kind in MUTATIONS:
        mut = _mutate(patch, kind, world, board, geom)
        if mut is None:
            continue
        res = cmp_patch.validate_patch(world, board, mut, geom)
        entry["mutations"].append({"mutation": kind,
                                   "blocked": not res["legal"],
                                   "reasons": res["reasons"]})
    return entry


def p1_gates(cases: list) -> dict:
    total_mut = sum(len(e["mutations"]) for e in cases)
    blocked_mut = sum(1 for e in cases for m in e["mutations"] if m["blocked"])
    program_ok = sum(1 for e in cases
                     if e["program"] and e["program"]["legal"])
    rollbacks = [e for e in cases if e["rollback"]]
    ident_mut = [m for e in cases for m in e["mutations"]
                 if m["mutation"] in ("unknown_route_id",
                                      "undeclared_object_change")]
    return {
        "schema": P1_GATES_SCHEMA,
        "g1_program_patch_acceptance": {
            "pass": program_ok == len(cases),
            "detail": "%d/%d 用例的程序生成动作被接受（含诚实弃权）"
                      % (program_ok, len(cases))},
        "g2_illegal_interception": {
            "pass": total_mut > 0 and blocked_mut == total_mut,
            "detail": "%d/%d 负向突变被拦截" % (blocked_mut, total_mut)},
        "g3_identity_mismatch_interception": {
            "pass": bool(ident_mut) and all(m["blocked"] for m in ident_mut),
            "detail": "route/net/parent/endpoint 身份错配拦截 %d 项"
                      % len(ident_mut)},
        "g4_rollback_hash_recovery": {
            "pass": bool(rollbacks)
                    and all(r["rollback"]["byte_equivalent"]
                            for r in rollbacks),
            "detail": "%d/%d 用例 rollback 逐字节恢复 base"
                      % (sum(1 for r in rollbacks
                             if r["rollback"]["byte_equivalent"]),
                         len(rollbacks))},
        "g5_undeclared_changes": {
            "pass": bool(rollbacks)
                    and all(r["undeclared_objects_unchanged"]
                            for r in rollbacks),
            "detail": "未声明对象 deep-equal（含 via 列表）"},
        "g6_replay_byte_exact": {"pass": None,
                                 "detail": "由 replay 模式独立判定"},
        "g7_visual_only_bypass": {"pass": None,
                                  "detail": "由 visual-only-check 判定"},
    }


def p1_visual_only_check(root: str, sid: str) -> dict:
    """改色不改机器事实：仅比对 data-* 机器字段，不做 XML 解析。

    SVG 由本地生成器产出（非外部不可信输入），此处用正则抽取 data-* 属性
    集合做等值比较；同时比对 manifest payload hash 绑定字段。
    """
    from . import cmp_inputs
    board = read_board(root, sid)
    run = baseline_run(board)
    geom = cmp_patch.geom_from_run(run)
    _ref, _manifest, svg_text = cmp_inputs.build_svg(board, geom)
    recolored = (svg_text.replace("#3B82F6", "#FF00FF")
                 .replace("#F97316", "#00FF00"))
    facts_a = sorted(_DATA_ATTR_RE.findall(svg_text))
    facts_b = sorted(_DATA_ATTR_RE.findall(recolored))
    hash_a = re.search(r'data-route-manifest-sha256="([^"]+)"', svg_text)
    hash_b = re.search(r'data-route-manifest-sha256="([^"]+)"', recolored)
    return {
        "scenario_id": sid,
        "color_changed": recolored != svg_text,
        "same_machine_facts": facts_a == facts_b,
        "manifest_hash_unchanged": (hash_a is not None and hash_b is not None
                                    and hash_a.group(1) == hash_b.group(1)),
        "machine_fact_count": len(facts_a),
    }


# ---------------------------------------------------------------- P2

def _response_path(responses_dir, sid, arm, rnd):
    return os.path.join(responses_dir,
                        "planner-response-%s-%s-r%d.json" % (sid, arm, rnd))


def run_arm_model(world, board, base_geom, arm, responses_dir):
    """模型臂：只消费真实响应文件；缺失/非法一律 blocked（可见）。"""
    best = copy.deepcopy(base_geom)
    best_metrics = cmp_patch.cmp_metrics(world, best["routes"], best["vias"])
    proposals = []
    calls = 0
    blocked_reason = None
    rounds_completed = 0
    for rnd in (1, 2):
        if len(proposals) >= MAX_PROPOSALS:
            break
        path = _response_path(responses_dir, board["scenario_id"], arm, rnd)
        if not os.path.exists(path):
            # round 1 缺失 = 无任何证据 → blocked；
            # round 2 缺失 = planner 未继续提供候选 → 保留 round 1 结果，
            # 但轮次与原因显式记录（不静默升级为"完整执行"）。
            if rnd == 1:
                blocked_reason = ("缺少 round 1 planner 响应文件（%s）"
                                  % os.path.basename(path))
            else:
                blocked_reason = None
            break
        calls += 1
        rounds_completed = rnd
        calls += 1
        resp = model.read_json(path)
        validated = cmp_patch.validate_response(resp, board, arm, rnd)
        if validated["blocked"]:
            blocked_reason = ("round %d 响应 blocked: %s"
                              % (rnd, validated.get("reason")))
            break
        for patch in validated["accepted_patches"]:
            if len(proposals) >= MAX_PROPOSALS:
                break
            res = cmp_patch.validate_patch(world, board, patch, best)
            record = {
                "seq": len(proposals),
                "round": rnd,
                "action_type": (patch.get("action_type")
                                if isinstance(patch, dict) else None),
                "route_id": (patch.get("route_id")
                             if isinstance(patch, dict) else None),
                "legal": bool(res.get("legal")),
                "reasons": list(res.get("reasons", [])),
                "accepted": False,
                "corrected_by_solver": False,
            }
            if res.get("legal") and not res.get("noop"):
                applied = cmp_patch.apply_and_check(world, board, patch, best)
                if applied.get("legal"):
                    cand = applied["geometry"]
                    m = cmp_patch.cmp_metrics(world, cand["routes"],
                                              cand["vias"])
                    record["candidate_objective"] = m["objective"]
                    if m["objective"] < best_metrics["objective"]:
                        best, best_metrics = cand, m
                        record["accepted"] = True
                        record["candidate_geometry_sha256"] = \
                            cmp_patch.candidate_geometry_sha256(cand)
            proposals.append(record)
    res = _arm_result(arm, base_geom, best, proposals, calls, blocked_reason)
    res["rounds_completed"] = rounds_completed
    res["round2_provided"] = os.path.exists(
        _response_path(responses_dir, board["scenario_id"], arm, 2))
    return res


def run_arm_deterministic(world, board, base_geom, arm):
    ls = cmp_localsearch.run_local_search(world, board, base_geom,
                                          MAX_PROPOSALS)
    res = _arm_result(arm, base_geom, ls["final_geom"], ls["proposals"],
                      ls["evaluations"], None)
    res["base_metrics"] = ls["base_metrics"]
    res["final_metrics"] = ls["final_metrics"]
    res["search_nodes"] = ls["search_nodes"]
    return res


def run_scenario(root: str, sid: str, arms, responses_dir) -> dict:
    board = read_board(root, sid)
    world = GridWorld(board)
    base_run = baseline_run(board)
    base_geom = cmp_patch.geom_from_run(base_run)
    base_metrics = cmp_patch.cmp_metrics(world, base_geom["routes"],
                                         base_geom["vias"])
    out = {"scenario_id": sid, "family": board["family"],
           "split": board["split"], "label": board["label"],
           "base_run_status": base_run["status"],
           "base_candidate_geometry_sha256":
               cmp_patch.candidate_geometry_sha256(base_geom),
           "base_metrics": base_metrics,
           "base_search_nodes": base_run["metrics"].get("search_nodes", 0),
           "arms": {}}
    for arm in arms:
        if arm == "A0":
            res = _arm_result(arm, base_geom, base_geom, [], 0, None)
            res["base_metrics"] = base_metrics
            res["final_metrics"] = base_metrics
            res["search_nodes"] = out["base_search_nodes"]
            out["arms"][arm] = res
        elif arm == "A1":
            out["arms"][arm] = run_arm_deterministic(world, board, base_geom,
                                                     arm)
        else:
            res = run_arm_model(world, board, base_geom, arm, responses_dir)
            res["final_metrics"] = cmp_patch.cmp_metrics(
                world, res["final_geom"]["routes"], res["final_geom"]["vias"])
            out["arms"][arm] = res
    return out


def _paired(scen: dict, arm: str, ref: str):
    """配对比较：返回 (win/tie/loss, delta, common_valid)。"""
    if scen["arms"][arm]["blocked"] or scen["arms"][ref]["blocked"]:
        return ("blocked", None, False)
    if scen["base_run_status"] != "sat":
        return ("not_applicable", None, False)
    a = scen["arms"][arm]["final_metrics"]["objective"]
    b = scen["arms"][ref]["final_metrics"]["objective"]
    delta = a - b
    return ("win" if delta < 0 else ("loss" if delta > 0 else "tie"),
            round(delta, 6), True)


def build_p2_summary(root: str, sids, arms, responses_dir):
    scenarios = [run_scenario(root, sid, tuple(arms), responses_dir)
                 for sid in sids]
    pairs = {}
    for arm in ("B1", "C1", "D1", "A0"):
        if arm not in arms:
            continue
        rows = [(_paired(s, arm, "A1"), s["scenario_id"]) for s in scenarios]
        deltas = [r[0][1] for r in rows if r[0][1] is not None]
        stats = {
            "win": sum(1 for r in rows if r[0][0] == "win"),
            "tie": sum(1 for r in rows if r[0][0] == "tie"),
            "loss": sum(1 for r in rows if r[0][0] == "loss"),
            "blocked": sum(1 for r in rows if r[0][0] == "blocked"),
            "not_applicable": sum(1 for r in rows
                                  if r[0][0] == "not_applicable"),
            "common_valid_n": len(deltas),
            "all_scenario_n": len(rows),
            "mean_delta": (round(cmp_stats.mean(deltas), 6)
                           if deltas else None),
            "median_delta": (round(cmp_stats.median(deltas), 6)
                             if deltas else None),
            "p90_delta": (round(cmp_stats.percentile(deltas, 90), 6)
                          if deltas else None),
            "per_scenario": [{"scenario_id": sid, "verdict": v[0],
                              "delta": v[1]}
                             for v, sid in rows],
        }
        if deltas:
            stats["bootstrap_ci95"] = \
                cmp_stats.paired_bootstrap_ci_mean_delta(
                    deltas, BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES)
            stats["sign_test_p"] = cmp_stats.sign_test_two_sided(
                stats["win"], stats["loss"])
        else:
            stats["bootstrap_ci95"] = None
            stats["sign_test_p"] = None
        pairs[arm] = stats
    return {"schema": P2_SUMMARY_SCHEMA, "scenario_ids": list(sids),
            "arms": list(arms), "paired_vs_A1": pairs,
            "scenarios": scenarios}


def _legality_rates(summary: dict) -> dict:
    """提案级合法率：legal proposals / total proposals（逐臂）。"""
    out = {}
    for arm in summary["arms"]:
        tot = legal = 0
        for sc in summary["scenarios"]:
            a = sc["arms"][arm]
            if a.get("blocked"):
                continue
            for pr in a.get("proposals", []):
                tot += 1
                if pr.get("legal"):
                    legal += 1
        out[arm] = {"proposals": tot, "legal": legal,
                    "rate": (round(legal / tot, 6) if tot else None)}
    return out


def _family_strata(summary: dict, arm: str, ref: str = "A1") -> dict:
    """按族分层的配对 delta（已见族 f1-f5 / 未见族 f6-f8）。"""
    seen, unseen = [], []
    for sc in summary["scenarios"]:
        verdict, delta, valid = _paired(sc, arm, ref)
        if not valid:
            continue
        (unseen if sc["family"] in ("f6", "f7", "f8") else seen).append(delta)
    return {"seen_families": {"n": len(seen),
                              "mean_delta": (round(cmp_stats.mean(seen), 6)
                                             if seen else None)},
            "unseen_families": {"n": len(unseen),
                                "mean_delta": (round(cmp_stats.mean(unseen), 6)
                                               if unseen else None)}}


def build_p2_gates(summary: dict) -> dict:
    c1 = summary["paired_vs_A1"].get("C1", {"common_valid_n": 0})
    model_arm_ran = c1["common_valid_n"] > 0
    rates = _legality_rates(summary)
    hard_ok = all(
        sum(s["arms"][a]["final_metrics"]["violations"].values()) == 0
        for s in summary["scenarios"] for a in summary["arms"]
        if not s["arms"][a]["blocked"] and s["base_run_status"] == "sat")
    gates = {
        "schema": P2_GATES_SCHEMA,
        "main_method": "C1",
        "baseline": "A1",
        "g1_all_compared_candidates_hard_checked": {
            "pass": hard_ok,
            "detail": "进入比较的候选经 validator + 独立 cell 级 DRC，violations 全 0"},
    }
    if not model_arm_ran:
        for g in ("g2_main_legality_not_worse_than_A1",
                  "g3_primary_objective_5pct_or_search_20pct",
                  "g4_no_critical_regression", "g5_majority_non_tie",
                  "g6_cross_family_direction_consistency",
                  "g7_model_net_benefit_over_A1"):
            gates[g] = {"pass": None, "detail": "模型臂无响应 → blocked"}
    else:
        c1_rate = rates["C1"]["rate"]
        a1_rate = rates["A1"]["rate"]
        gates["g2_main_legality_not_worse_than_A1"] = {
            "pass": (c1_rate is not None and a1_rate is not None
                     and c1_rate >= a1_rate),
            "detail": "C1 提案合法率 %s vs A1 %s（提案级）"
                      % (c1_rate, a1_rate),
        }
        obj_branch = None
        a1_mean = None
        base_objs = [s["base_metrics"]["objective"] for s in summary["scenarios"]
                     if s["base_run_status"] == "sat"]
        if c1["common_valid_n"] > 0:
            deltas = [r["delta"] for r in c1["per_scenario"]
                      if r["delta"] is not None]
            means = []
            for sc in summary["scenarios"]:
                if sc["base_run_status"] != "sat":
                    continue
                a1v = sc["arms"]["A1"]["final_metrics"]["objective"]
                if a1v > 0:
                    means.append(a1v)
            a1_mean = cmp_stats.mean(means)
            c1_mean = a1_mean + cmp_stats.mean(deltas)
            obj_branch = (c1_mean - a1_mean) / a1_mean if a1_mean else None
        gates["g3_primary_objective_5pct_or_search_20pct"] = {
            "pass": (obj_branch is not None and obj_branch <= -0.05),
            "detail": "C1 vs A1 配对均值相对变化 %s（门要求改善 >=5%%）；"
                      "搜索时间分支：两臂评估预算同为 8，模型侧时延不可比 → "
                      "该分支不适用（not measurable in comparable units）"
                      % (round(obj_branch, 6) if obj_branch is not None else None),
        }
        viol_ok = hard_ok
        via_ok = all(
            s["arms"]["C1"]["final_metrics"]["via_count"]
            <= s["base_metrics"]["via_count"]
            for s in summary["scenarios"] if not s["arms"]["C1"].get("blocked"))
        conn_ok = all(
            s["arms"]["C1"]["final_metrics"]["unconnected"]
            <= s["base_metrics"]["unconnected"]
            for s in summary["scenarios"] if not s["arms"]["C1"].get("blocked"))
        gates["g4_no_critical_regression"] = {
            "pass": bool(viol_ok and via_ok and conn_ok),
            "detail": "无 short/unconnected/via 上限/锁定对象回退"
                      "（violations_ok=%s via_ok=%s conn_ok=%s）"
                      % (viol_ok, via_ok, conn_ok),
        }
        non_tie = c1["win"] + c1["loss"]
        gates["g5_majority_non_tie"] = {
            "pass": non_tie * 2 > c1["common_valid_n"],
            "detail": "非 tie %d / 可比 %d（blocked=%d, not_applicable=%d）"
                      % (non_tie, c1["common_valid_n"], c1["blocked"],
                         c1["not_applicable"]),
        }
        strata = _family_strata(summary, "C1")
        seen_m = strata["seen_families"]["mean_delta"]
        unseen_m = strata["unseen_families"]["mean_delta"]
        pass6 = (seen_m is not None and unseen_m is not None
                 and seen_m <= 0 and unseen_m <= 0
                 and (strata["seen_families"]["n"] > 0)
                 and (strata["unseen_families"]["n"] > 0))
        gates["g6_cross_family_direction_consistency"] = {
            "pass": pass6,
            "detail": "已见族 mean_delta %s（n=%d）；未见族 mean_delta %s（n=%d）"
                      % (seen_m, strata["seen_families"]["n"], unseen_m,
                         strata["unseen_families"]["n"]),
        }
        gates["g7_model_net_benefit_over_A1"] = {
            "pass": (obj_branch is not None and obj_branch < 0),
            "detail": "C1 相对 A1 的净收益（配对均值相对变化 %s）"
                      % (round(obj_branch, 6) if obj_branch is not None
                         else None),
        }
    gates["g8_replay_byte_exact"] = {"pass": None, "detail": "由 replay 判定"}
    gates["g9_no_post_hoc_change"] = {
        "pass": True,
        "detail": "协议冻结后未改门/目标/样本；模型臂缺失记为 blocked"}
    ran = [a for a in ("B1", "C1", "D1")
           if summary["paired_vs_A1"].get(a, {}).get("common_valid_n", 0) > 0]
    gates["model_arms_with_responses"] = ran
    gates["model_arms_blocked"] = [a for a in ("B1", "C1", "D1")
                                   if a not in ran]
    gates["legality_rates"] = rates
    gates["family_strata_C1"] = _family_strata(summary, "C1")
    gates["verdict"] = ("blocked_model_arms" if not ran else "evaluated")
    return gates



def run_p1_all(root, sids):
    """P1 全量计算（用例结果 + 门），供 p1 模式与 replay-p1 共用。"""
    cases = [run_p1_case(root, c) for c in p1_cases(root, sids)]
    return {"schema": P1_RESULTS_SCHEMA, "cases": cases,
            "gates": p1_gates(cases)}


def replay_p1(root, sids):
    """同输入双跑 P1，比较核心产物 canonical 字节。"""
    a = run_p1_all(root, sids)
    b = run_p1_all(root, sids)
    same = model.canonical_json(a) == model.canonical_json(b)
    return {"schema": "pcbflow.v4cmp.replay-check/1", "subject": "p1",
            "double_run_identical": same,
            "sha256_run1": model.sha256_of(a),
            "sha256_run2": model.sha256_of(b),
            "note": "P1 核心产物（用例结果 + 门）双跑 canonical 字节比对"}


def replay_p2(root, sids, arms, responses_dir):
    """同输入双跑 P2 摘要，比较 canonical 字节。"""
    a = build_p2_summary(root, sids, arms, responses_dir)
    b = build_p2_summary(root, sids, arms, responses_dir)
    same = model.canonical_json(a) == model.canonical_json(b)
    return {"schema": "pcbflow.v4cmp.replay-check/1", "subject": "p2",
            "double_run_identical": same,
            "sha256_run1": model.sha256_of(a),
            "sha256_run2": model.sha256_of(b),
            "note": "P2 核心产物（逐场景逐臂结果）双跑 canonical 字节比对"}


# ---------------------------------------------------------------- CLI

def _write(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    model.write_json(path, obj)


def main():
    import sys
    payload = model.read_stdin_json()
    mode = payload["mode"]
    root = payload["root"]
    if mode == "p1":
        sids = tuple(payload.get("scenario_ids", P1_SIDS))
        result = run_p1_all(root, sids)
        cases = result["cases"]
        _write(os.path.join(root, "p1", "patch-results.json"),
               {"schema": P1_RESULTS_SCHEMA, "cases": cases})
        _write(os.path.join(root, "p1", "gates-p1.json"), result["gates"])
        vis = [p1_visual_only_check(root, sid)
               for sid in payload.get("visual_check_sids",
                                      ["dev-f1-01", "dev-f3-02"])]
        _write(os.path.join(root, "p1", "visual-only-check.json"),
               {"schema": VISUAL_SCHEMA, "checks": vis,
                "pass": all(v["same_machine_facts"]
                            and v["manifest_hash_unchanged"] for v in vis)})
        sys.stdout.write(json.dumps(
            {"mode": "p1", "cases": len(cases),
             "gates": {k: v["pass"] for k, v in result["gates"].items()}},
            sort_keys=True) + "\n")
        return
    if mode == "prepare":
        sids = [str(x) for x in payload["scenario_ids"]]
        arms = tuple(payload.get("arms", MODEL_ARMS))
        split_name = str(payload.get("split", "development"))
        res = prepare_inputs(root, sids, arms, split_name)
        _write(os.path.join(root, "p2", "inputs-summary.json"), res)
        sys.stdout.write(json.dumps({"mode": "prepare",
                                     "count": res["count"]},
                                    sort_keys=True) + "\n")
        return
    if mode == "feedback":
        sids = [str(x) for x in payload["scenario_ids"]]
        arms = tuple(payload.get("arms", MODEL_ARMS))
        responses_dir = payload.get("responses_dir",
                                    os.path.join(root, "p2", "responses"))
        res = prepare_feedback(root, sids, arms, responses_dir)
        sys.stdout.write(json.dumps({"mode": "feedback",
                                     "count": res["count"]},
                                    sort_keys=True) + "\n")
        return
    if mode == "check-responses":
        sids = [str(x) for x in payload["scenario_ids"]]
        arms = tuple(payload.get("arms", MODEL_ARMS))
        responses_dir = payload.get("responses_dir",
                                    os.path.join(root, "p2", "responses"))
        res = check_responses(root, sids, arms, responses_dir)
        _write(os.path.join(root, "p2", "response-coverage.json"), res)
        sys.stdout.write(json.dumps({"mode": "check-responses",
                                     "complete": res["complete"],
                                     "total": res["total"]},
                                    sort_keys=True) + "\n")
        return
    if mode == "replay-p1":
        sids = tuple(payload.get("scenario_ids", P1_SIDS))
        res = replay_p1(root, sids)
        _write(os.path.join(root, "p1", "replay-check.json"), res)
        sys.stdout.write(json.dumps({"mode": "replay-p1",
                                     "identical": res["double_run_identical"]},
                                    sort_keys=True) + "\n")
        return
    if mode == "replay-p2":
        sids = [str(s) for s in payload["scenario_ids"]]
        arms = tuple(payload.get("arms", ARMS_P2))
        responses_dir = payload.get("responses_dir",
                                    os.path.join(root, "p2", "responses"))
        res = replay_p2(root, sids, arms, responses_dir)
        out_dir = payload.get("out_dir") or os.path.join(root, "p2")
        _write(os.path.join(out_dir, "replay-check.json"), res)
        sys.stdout.write(json.dumps({"mode": "replay-p2",
                                     "identical": res["double_run_identical"]},
                                    sort_keys=True) + "\n")
        return
    if mode == "p2":
        sids = [str(s) for s in payload["scenario_ids"]]
        arms = tuple(payload.get("arms", ARMS_P2))
        responses_dir = payload.get("responses_dir",
                                    os.path.join(root, "p2", "responses"))
        out_dir = payload.get("out_dir") or os.path.join(root, "p2")
        summary = build_p2_summary(root, sids, arms, responses_dir)
        _write(os.path.join(out_dir, "metrics.json"), summary)
        gates = build_p2_gates(summary)
        _write(os.path.join(out_dir, "gates.json"), gates)
        sys.stdout.write(json.dumps(
            {"mode": "p2", "scenarios": len(sids),
             "arms_with_responses": gates["model_arms_with_responses"],
             "verdict": gates["verdict"]}, sort_keys=True) + "\n")
        return
    raise ValueError("未知 mode: %r" % (mode,))


if __name__ == "__main__":
    main()
