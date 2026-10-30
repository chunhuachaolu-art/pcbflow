"""V4.2 M1 deterministic GT: per-route improvable labels via delete+reorder.

prereg-m1 note 2 (GT v1.1): the original delete-and-replace definition is a
structural identity on DRC-clean sequential incumbents (obstacle superset +
deterministic A* reproduces the original path; measured 0.0 on 87/87 nets
across 16 scenarios -- kept as the structural lemma record).  v1.1:
route r improvable iff incumbent_objective - solve_board(others in stable
order + [net(r) LAST]).objective > epsilon.  The flagged net is re-inserted
last; other nets re-route freely without its early occupation.  Zero model,
fully deterministic (test-enforced double-run).
"""

from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.leg import subnet_resolve

#: prereg-m1 epsilon (taskbook draft 0.5; user confirmation pending at the
#: M1-exit band freeze -- changing it later = new prereg version + full GT re-run)
EPSILON = 0.5


def incumbent_request(board):
    return {"route_order": sorted(n["net_id"] for n in board["nets"]),
            "group": "A"}


def incumbent_run(board):
    return solve_board(board, incumbent_request(board))


def reorder_run(board, nid):
    """solve_board with net nid moved LAST (delete + reorder re-solve)."""
    stable = sorted(n["net_id"] for n in board["nets"])
    order = [x for x in stable if x != nid] + [nid]
    return solve_board(board, {"route_order": order, "group": "A"})


def identity_check(board):
    """Structural lemma record: single-net delete+replace improvements are
    all exactly 0.0 on a sat incumbent (prereg note 2 evidence)."""
    inc = incumbent_run(board)
    if inc["status"] != "sat":
        return {"status": "excluded_failed_incumbent"}
    req = incumbent_request(board)
    vals = []
    for r in inc["routes"]:
        nid = str(r["net_id"])
        if any(v["net"] == nid for v in vals):
            continue
        leg = subnet_resolve(board, req, inc, [nid])
        vals.append({"net": nid,
                     "improvement": (round(inc["metrics"]["objective"]
                                           - leg["metrics"]["objective"], 6)
                                     if leg["status"] == "sat" else None)})
    return {"status": "ok", "per_net": vals,
            "all_zero": all(v["improvement"] == 0.0 for v in vals)}


def gt_for_scenario(board, epsilon=EPSILON):
    inc = incumbent_run(board)
    out = {"epsilon": epsilon, "gt_version": "v1.1-reorder-last",
           "incumbent_status": inc["status"],
           "incumbent_objective": inc["metrics"].get("objective"),
           "incumbent_manifest_sha256": inc["route_manifest_sha256_at_run"],
           "per_net": {}, "per_route": {}, "n_routes": 0,
           "random_baseline": None}
    if inc["status"] != "sat":
        out["status"] = "excluded_failed_incumbent"
        return out
    stable = sorted(n["net_id"] for n in board["nets"])
    for nid in stable:
        leg = reorder_run(board, nid)
        if leg["status"] == "sat":
            imp = round(out["incumbent_objective"]
                        - leg["metrics"]["objective"], 6)
            out["per_net"][nid] = {"improvement": imp,
                                   "improvable": imp > epsilon,
                                   "leg_status": "sat",
                                   "leg_search_nodes":
                                       leg["metrics"].get("search_nodes")}
        else:
            out["per_net"][nid] = {"improvement": None, "improvable": False,
                                   "leg_status": leg["status"],
                                   "leg_search_nodes":
                                       leg["metrics"].get("search_nodes")}
    for r in inc["routes"]:
        out["per_route"][str(r["route_id"])] = {
            "net_id": str(r["net_id"]),
            "improvable": out["per_net"][str(r["net_id"])]["improvable"]}
    out["n_routes"] = len(inc["routes"])
    improvable = sum(1 for v in out["per_route"].values() if v["improvable"])
    out["random_baseline"] = (round(improvable / out["n_routes"], 4)
                              if out["n_routes"] else None)
    out["status"] = "ok"
    return out
