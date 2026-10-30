"""V4.2 M2 paired deletion-experiment engine (prereg-m2).

Both arms share the reorder re-solve semantics dictated by the M1
structural theorem (delete-and-replace is an identity; improvement is only
reachable through reordering): candidate net nid is evaluated by
solve_board over [current_order minus nid] + [nid] (move-last), first-
improvement greedy with K=8 re-solve budget, arm-specific candidate
priority.

- baseline arm: deterministic worst-first (per-net objective contribution
  in the CURRENT solution, descending, ties by net_id -- recomputed each
  greedy round);
- treatment arm: model-flagged nets only, first-flag appearance order; no
  deterministic fallback (empty flags => incumbent returned unchanged).

The model output enters ONLY candidate selection (never geometry, never
validation); every committed final is a solve_board output asserted
DRC-clean and fully connected (G-M2a).  Fully deterministic given the
recorded flags (G-M2d replay).
"""

from pcbflow.v4exp.grid import canonical_json
from pcbflow.v4exp.router import solve_board

BUDGET_K = 8
_VIA_OBJ = 8.0
_BEND_OBJ = 0.5
_STRICT = 1e-9


def net_contribution(run):
    """Per-net objective contribution of the CURRENT solution (length +
    vias*8.0 + bends*0.5), deterministic, from emitted route/via dicts."""
    out = {}
    for r in run["routes"]:
        nid = str(r["net_id"])
        poly = r["polyline_mm"]
        length = sum(((poly[i][0] - poly[i - 1][0]) ** 2
                      + (poly[i][1] - poly[i - 1][1]) ** 2) ** 0.5
                     for i in range(1, len(poly)))
        bends = 0
        for i in range(2, len(poly)):
            dx1 = poly[i - 1][0] - poly[i - 2][0]
            dy1 = poly[i - 1][1] - poly[i - 2][1]
            dx2 = poly[i][0] - poly[i - 1][0]
            dy2 = poly[i][1] - poly[i - 1][1]
            if (dx1 > 0) != (dx2 > 0) or (dy1 > 0) != (dy2 > 0):
                bends += 1
        d = out.setdefault(nid, {"length": 0.0, "vias": 0, "bends": 0})
        d["length"] += length
        d["bends"] += bends
    for v in run["vias"]:
        out.setdefault(str(v["net_id"]), {"length": 0.0, "vias": 0, "bends": 0})
        out[str(v["net_id"])]["vias"] += 1
    return {nid: round(c["length"] + c["vias"] * _VIA_OBJ + c["bends"] * _BEND_OBJ, 6)
            for nid, c in out.items()}


def _reorder(board, current_order, nid):
    return [x for x in current_order if x != nid] + [nid]


def greedy_arm(board, incumbent, priority_nets, k=BUDGET_K):
    """First-improvement greedy over move-last reorder re-solves.

    priority_nets: iterable of net ids in arm priority order (candidates).
    Deterministic; a net already in last position is skipped free (identity
    by construction).  Returns a result dict (final solution + trace).
    """
    current = incumbent
    current_order = sorted(n["net_id"] for n in board["nets"])
    budget = k
    search_nodes = incumbent["metrics"]["search_nodes"]
    applied = []
    evaluations = 0
    while budget > 0:
        found = False
        for nid in priority_nets(current):
            if budget <= 0:
                break
            if nid == current_order[-1]:
                continue  # identity by construction, free skip
            order = _reorder(board, current_order, nid)
            leg = solve_board(board, {"route_order": order, "group": "A"})
            budget -= 1
            evaluations += 1
            search_nodes += leg["metrics"]["search_nodes"]
            if (leg["status"] == "sat"
                    and leg["metrics"]["objective"]
                    < current["metrics"]["objective"] - _STRICT):
                current = leg
                current_order = order
                applied.append(nid)
                found = True
                break
        if not found:
            break
    final = current
    # G-M2a hard safety assertions (solve_board outputs are DRC-clean by
    # construction; asserted regardless)
    if final["status"] == "sat":
        assert sum(final["metrics"]["violations"].values()) == 0
        assert final["metrics"]["all_connected"] is True
    return {
        "final": final,
        "final_order": current_order,
        "applied": applied,
        "evaluations": evaluations,
        "search_nodes_total": search_nodes,
        "improvement": round(incumbent["metrics"]["objective"]
                             - final["metrics"]["objective"], 6),
    }


def baseline_priority(current):
    """Worst-first: contribution in the CURRENT solution, desc, ties by id."""
    contrib = net_contribution(current)
    return sorted(contrib, key=lambda nid: (-contrib[nid], nid))


def flag_priority(flags, board):
    """Model-flagged nets only, first-flag appearance order."""
    seen = []
    net_ids = {n["net_id"] for n in board["nets"]}
    for f in flags or []:
        if f.get("verdict") != "flag_bad":
            continue
        rid = str(f.get("route_id", ""))
        nid = rid.rsplit("-S", 1)[0]
        if nid in net_ids and nid not in seen:
            seen.append(nid)
    return seen


def run_pair(board, model_flags):
    """Incumbent + both arms for one scenario. Model output only selects."""
    req = {"route_order": sorted(n["net_id"] for n in board["nets"]),
           "group": "A"}
    incumbent = solve_board(board, req)
    if incumbent["status"] != "sat":
        return {"status": "excluded_failed_incumbent",
                "incumbent_status": incumbent["status"]}
    flagged = flag_priority(model_flags, board)
    base = greedy_arm(board, incumbent, baseline_priority)
    treat = greedy_arm(board, incumbent, lambda _cur, _f=tuple(flagged): list(_f))
    return {
        "status": "ok",
        "incumbent_objective": incumbent["metrics"]["objective"],
        "baseline": {k: base[k] for k in ("final_order", "applied",
                                          "evaluations",
                                          "search_nodes_total", "improvement")},
        "baseline_final_objective": base["final"]["metrics"]["objective"],
        "treatment": {k: treat[k] for k in ("final_order", "applied",
                                            "evaluations",
                                            "search_nodes_total",
                                            "improvement")},
        "treatment_final_objective": treat["final"]["metrics"]["objective"],
        "flagged_nets": flagged,
        "canonical_pair": canonical_json({
            "baseline": {k: base[k] for k in ("final_order", "applied",
                                              "evaluations", "improvement")},
            "treatment": {k: treat[k] for k in ("final_order", "applied",
                                                "evaluations",
                                                "improvement")},
            "flagged_nets": flagged}),
    }
