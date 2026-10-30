"""P0-b subnet re-solve leg (B8 semantics on the synthetic domain).

route_grid.route_one_added (Rev-C chain) treats same-batch settled nets as
injected existing copper (added_prims); this module is the synthetic-domain
equivalent required by taskbook §3 M0 P0-b:

  nets NOT in the deletion set are pre-loaded into a RoutedState from the
  incumbent result via grid.geometry_from_routes (the frozen independent
  reconstruction view -- parses only emitted JSON, never solver-internal
  state), and only the deleted nets are re-routed with frozen
  v4exp.router._route_single_net semantics (read-only import; zero drift
  by construction).

Parity anchor (taskbook: "agrees with full-scenario re-solve when the
deletion set is empty"): deleting every net and re-routing in the
incumbent request's route_order reproduces solve_board byte-for-byte on
the shared fields (routes/vias/metrics/status/search_nodes), because the
pre-loaded state is then empty and the search sequence is identical.
tests/test_v4_2_m0.py enforces this over the full reuse scenario set.
"""

import hashlib

from pcbflow.v4exp.grid import (V4ExpError, RoutedState, canonical_json,
                                geometry_from_routes)
from pcbflow.v4exp.router import _route_single_net, _compute_metrics

SUBNET_SCHEMA = "pcbflow.v4_2.subnet-resolve/1"


def subnet_resolve(board, request, incumbent, deleted_nets, reroute_order=None):
    """Re-route ``deleted_nets`` with all other nets fixed as existing copper.

    board/request: the scenario snapshot and the solver request the
    incumbent was produced under (route_order validated as in solve_board;
    layer/corridor preferences are honoured for the re-routed nets).
    incumbent: a solver-run result dict (frozen or mirror schema).
    deleted_nets: iterable of net ids to delete and re-route.
    reroute_order: optional explicit order (default: stable sorted).

    Deterministic: same inputs -> same canonical bytes (double-run guard in
    tests).  The returned dict never mutates the incumbent (kept route
    dicts are re-serialized as-is).
    """
    from pcbflow.v4exp.grid import GridWorld

    world = GridWorld(board)
    order = [str(s) for s in request.get("route_order", [])]
    if sorted(order) != sorted(world.net_ids) or len(set(order)) != len(order):
        raise V4ExpError("route_order must list every net exactly once")
    deleted = [str(n) for n in deleted_nets]
    if len(set(deleted)) != len(deleted):
        raise V4ExpError("deleted_nets must not repeat")
    unknown = [n for n in deleted if n not in set(world.net_ids)]
    if unknown:
        raise V4ExpError("deleted nets not on board: %s" % ",".join(unknown))
    reroute = [str(n) for n in reroute_order] if reroute_order is not None \
        else sorted(deleted)
    if sorted(reroute) != sorted(deleted):
        raise V4ExpError("reroute_order must be a permutation of deleted_nets")

    prefs = {}
    for item in request.get("layer_preferences", []):
        prefs[str(item["net_id"])] = [str(s) for s in item.get("layers", [])]
    corridors = {}
    for item in request.get("corridor_preferences", []):
        corridors[str(item["net_id"])] = [[float(a), float(b)]
                                          for a, b in item.get("waypoints_mm", [])]

    kept_routes = [r for r in incumbent["routes"]
                   if str(r["net_id"]) not in set(deleted)]
    kept_vias = [v for v in incumbent["vias"]
                 if str(v["net_id"]) not in set(deleted)]
    geo = geometry_from_routes(world, incumbent["routes"], incumbent["vias"])
    kept_nets = [nid for nid in world.net_ids if nid not in set(deleted)]
    missing = [nid for nid in kept_nets if nid not in geo]
    if missing:
        raise V4ExpError("incumbent has no geometry for kept nets: %s"
                         % ",".join(missing))

    state = RoutedState()
    for nid in kept_nets:
        state.add_net(nid, geo[nid])

    routes = list(kept_routes)
    vias = list(kept_vias)
    actions = []
    failed_at = None
    search_nodes = 0
    for i, nid in enumerate(reroute):
        res = _route_single_net(world, state, nid, prefs.get(nid),
                                corridors.get(nid))
        search_nodes += res["search_nodes"]
        if res["ok"]:
            state.add_net(nid, res["cells"])
            routes.extend(res["routes"])
            vias.extend(res["vias"])
            actions.append({"seq": i, "op": "subnet_resolve", "net_id": nid,
                            "status": "ok",
                            "route_ids": [r["route_id"] for r in res["routes"]],
                            "via_ids": [v["via_id"] for v in res["vias"]]})
        else:
            failed_at = nid
            actions.append({"seq": i, "op": "subnet_resolve", "net_id": nid,
                            "status": "failed"})
            break

    metrics = _compute_metrics(world, routes, vias)
    metrics["search_nodes"] = search_nodes
    metrics["ripup_count"] = 0
    violations_sum = sum(metrics["violations"].values())
    if failed_at is None and metrics["all_connected"] and violations_sum == 0:
        status = "sat"
    else:
        status = "failed"

    result = {
        "schema": SUBNET_SCHEMA,
        "scenario_id": world.scenario_id,
        "group": str(request.get("group", "A")),
        "base_solver_version": str(incumbent.get("solver_version", "unknown")),
        "base_route_manifest_sha256_at_run":
            incumbent.get("route_manifest_sha256_at_run"),
        "deleted_nets": deleted,
        "reroute_order": reroute,
        "status": status,
        "routes": routes,
        "vias": vias,
        "metrics": metrics,
        "route_manifest_sha256_at_run": hashlib.sha256(
            canonical_json({"routes": routes, "vias": vias}).encode("utf-8")
        ).hexdigest(),
        "actions_digest": hashlib.sha256(
            canonical_json(actions).encode("utf-8")
        ).hexdigest(),
    }
    if failed_at is not None:
        result["failed_at"] = failed_at
    return result
