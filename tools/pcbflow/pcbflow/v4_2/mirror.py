"""P0-a mirror: v4exp solver with injectable cost bias / hard keepout.

Verdict context (out/v4.2-seat/m0/probe-a-verdict.json): v4exp
router.solve_board has no per-cell cost-bias entry point (_astar costs are
frozen constants, request corridors are waypoint chains, and blocked sets
are binary), and pcbflow/v4exp/ is a read-only package (taskbook §2.2).
The M3 constraint seat therefore cannot inject corridor bias into the
frozen solver.  This module is the taskbook-anticipated fallback path: a
faithful mirror of pcbflow.v4exp.router's search semantics plus two
injection hooks:

  cost_bias    : {(layer_idx, ix, iy): extra_step_cost}  -- soft, >= 0,
                 added to the move-step cost of entering that cell
                 (corridor = discourage; never speeds anything up);
  hard_keepout : {layer_idx: iterable((ix, iy))}         -- hard block,
                 unioned into the per-layer blocked sets (keepout).

With both hooks empty the emitted result is byte-identical to
v4exp.router.solve_board canonical JSON; tests/test_v4_2_m0.py enforces
this over the full reuse scenario set (taskbook §3 M0 P0-a parity gate).
Injected runs are marked with MIRROR_SCHEMA and an ``injections`` summary
so they can never be confused with frozen-solver runs.

Semantics copied verbatim from pcbflow/v4exp/router.py (read-only import of
its helpers where possible): heap ordering (f, tie, g), DIRS order, tie
counter, via-site double-occupancy check, run splitting, route/via
emission rounding, metric computation, result hashing.
"""

import heapq
import hashlib

from pcbflow.v4exp.grid import V4ExpError, canonical_json
from pcbflow.v4exp import router as _frozen

_INF = 1 << 60

#: Frozen-solver run schema (identical bytes requirement when not injected).
RUN_SCHEMA = _frozen.RUN_SCHEMA
#: Injected-run schema -- never byte-comparable against frozen runs.
MIRROR_SCHEMA = "pcbflow.v4_2.solver-run-mirror/1"
MIRROR_VERSION_SUFFIX = "+v4_2-mirror-1"


def _astar_mirror(world, blocked, allowed_layers, start, goal, goal_any_layer,
                  cost_bias=None):
    """Turn-aware A* over states (ix, iy, layer, dir) -- mirror of
    v4exp router._astar with an optional non-negative per-cell move-cost
    bias.  With cost_bias empty the search sequence and result are
    identical to the frozen implementation.
    """
    sx, sy, sl = start
    if not world.in_bounds(sx, sy) or (sx, sy) in blocked[sl]:
        return None, 0
    if goal_any_layer:
        goal_cells = {(goal[0], goal[1], li) for li in allowed_layers}
    else:
        goal_cells = {(goal[0], goal[1], goal[2])}
    start_key = (sx, sy, sl, _frozen.START_DIR)
    if (sx, sy, sl) in goal_cells:
        return [(sx, sy, sl, "start")], 0

    def h(x, y):
        return abs(x - goal[0]) + abs(y - goal[1])

    best = {start_key: 0}
    came = {}
    heap = [(h(sx, sy), 0, 0, start_key)]
    tie = 0
    expanded = 0
    while heap:
        _f, _t, g, key = heapq.heappop(heap)
        if g > best.get(key, _INF):
            continue  # stale heap entry
        expanded += 1
        x, y, li, d = key
        if (x, y, li) in goal_cells:
            steps = []
            cur = key
            while cur is not None:
                px, py, pl, _pd = cur
                prev, kind = came.get(cur, (None, "start"))
                steps.append((px, py, pl, kind))
                cur = prev
            steps.reverse()
            return steps, expanded
        for nd in range(4):
            dx, dy = _frozen.DIRS[nd]
            nx, ny = x + dx, y + dy
            if not world.in_bounds(nx, ny) or (nx, ny) in blocked[li]:
                continue
            if d == _frozen.START_DIR or nd == d:
                step_cost = 1
            else:
                step_cost = 1 + _frozen.TURN_PENALTY_CELLS
            if cost_bias:
                step_cost += cost_bias.get((li, nx, ny), 0.0)
            ng = g + step_cost
            nkey = (nx, ny, li, nd)
            if ng < best.get(nkey, _INF):
                best[nkey] = ng
                came[nkey] = (key, "move")
                tie += 1
                heapq.heappush(heap, (ng + h(nx, ny), tie, ng, nkey))
        for lj in allowed_layers:
            if lj == li:
                continue
            if not _frozen._via_site_ok(world, blocked, x, y, li, lj):
                continue
            ng = g + _frozen.VIA_COST_CELLS
            nkey = (x, y, lj, d)
            if ng < best.get(nkey, _INF):
                best[nkey] = ng
                came[nkey] = (key, "via")
                tie += 1
                heapq.heappush(heap, (ng + h(x, y), tie, ng, nkey))
    return None, expanded


def _route_single_net_injected(world, state, nid, pref_layer_names,
                               waypoints_mm, hard_keepout=None,
                               cost_bias=None):
    """Mirror of v4exp router._route_single_net with keepout/bias hooks.

    hard_keepout cells are unioned into the per-layer blocked sets before
    the search; cost_bias is forwarded to _astar_mirror.
    """
    out = {"ok": False, "routes": [], "vias": [], "cells": None, "search_nodes": 0}
    allowed = set(world.net_allowed_layer_indices(nid))
    if pref_layer_names is not None:
        allowed &= {world.layer_index[s] for s in pref_layer_names
                    if s in world.layer_index}
    if not allowed:
        return out
    pad_a = world.pad_by_id[world.net_endpoints[nid][0]]
    pad_b = world.pad_by_id[world.net_endpoints[nid][1]]
    start = (world.cell_x(pad_a["x_mm"]), world.cell_y(pad_a["y_mm"]),
             world.layer_index[str(pad_a["layer"])])
    goal = (world.cell_x(pad_b["x_mm"]), world.cell_y(pad_b["y_mm"]),
            world.layer_index[str(pad_b["layer"])])
    if start[2] not in allowed or goal[2] not in allowed:
        return out

    static = world.static_blocked_for_net(nid)
    dyn = state.blocked_from_others(nid)
    blocked = {}
    for li in range(len(world.layers)):
        s = set(static.get(li, ()))
        s |= dyn.get(li, set())
        if hard_keepout:
            s |= set(hard_keepout.get(li, ()))
        blocked[li] = s

    allowed_sorted = sorted(allowed)
    chain = [(start[0], start[1])]
    for w in waypoints_mm or []:
        chain.append((world.cell_x(w[0]), world.cell_y(w[1])))
    chain.append((goal[0], goal[1]))

    steps = []
    cur = start
    nodes = 0
    for i in range(1, len(chain)):
        tx, ty = chain[i]
        if i == len(chain) - 1:
            seg, exp = _astar_mirror(world, blocked, allowed_sorted, cur,
                                     goal, False, cost_bias)
        else:
            seg, exp = _astar_mirror(world, blocked, allowed_sorted, cur,
                                     (tx, ty, cur[2]), True, cost_bias)
        nodes += exp
        if seg is None:
            out["search_nodes"] = nodes
            return out
        steps.extend(seg if not steps else seg[1:])
        last = seg[-1]
        cur = (last[0], last[1], last[2])
    out["search_nodes"] = nodes

    # ---- split the concatenated step list into layer runs and vias ----
    n_layers = len(world.layers)
    cells = {li: set() for li in range(n_layers)}
    runs = []
    net_vias = []
    cur_layer = steps[0][2]
    cur_cells = [(steps[0][0], steps[0][1])]
    cells[cur_layer].add(cur_cells[0])
    for (x, y, li, kind) in steps[1:]:
        if kind == "via":
            net_vias.append((x, y, cur_layer, li))
            r = _frozen.VIA_FOOTPRINT_RADIUS_CELLS
            for lj in (cur_layer, li):
                for ddx in range(-r, r + 1):
                    for ddy in range(-r, r + 1):
                        cells[lj].add((x + ddx, y + ddy))
            runs.append({"layer": cur_layer, "cells": cur_cells})
            cur_layer = li
            cur_cells = [(x, y)]
        else:
            if li != cur_layer:
                raise V4ExpError("internal: layer change without a via step")
            px, py = cur_cells[-1]
            cur_cells.append((x, y))
            cells[li].add((x, y))
    runs.append({"layer": cur_layer, "cells": cur_cells})

    # ---- emit route/via dicts ----
    width = world.net_width(nid)
    routes = []
    vias = []
    prev_ep = str(pad_a["pad_id"])
    n_via = 0
    for idx, run in enumerate(runs):
        rid = "%s-S%02d" % (nid, idx + 1)
        poly = [[round(world.center_mm_x(x), 2), round(world.center_mm_y(y), 2)]
                for (x, y) in run["cells"]]
        routes.append({
            "route_id": rid,
            "net_id": nid,
            "layer": world.layers[run["layer"]],
            "width_mm": width,
            "polyline_mm": poly,
            "endpoint_ids": [prev_ep, str(pad_b["pad_id"])],
            "state": "candidate",
            "source": "solver",
        })
        if idx < len(runs) - 1:
            n_via += 1
            vx, vy, lf, lt = net_vias[idx]
            vid = "%s-V%02d" % (nid, n_via)
            routes[-1]["endpoint_ids"][1] = vid
            vias.append({
                "via_id": vid,
                "parent_id": rid,
                "net_id": nid,
                "from_layer": world.layers[lf],
                "to_layer": world.layers[lt],
                "center_mm": [round(world.center_mm_x(vx), 2),
                              round(world.center_mm_y(vy), 2)],
                "drill_mm": world.via_hole_mm,
                "annular_ring_mm": round((world.via_pad_mm - world.via_hole_mm) / 2.0, 3),
                "state": "candidate",
                "source": "solver",
            })
            prev_ep = vid
    out["routes"] = routes
    out["vias"] = vias
    out["cells"] = cells
    out["ok"] = True
    return out


def solve_board_injected(board, request, cost_bias=None, hard_keepout=None,
                         cost_bias_by_net=None, hard_keepout_by_net=None):
    """Mirror of v4exp router.solve_board with injection hooks.

    request keys are unchanged (route_order, layer_preferences,
    corridor_preferences, protected_net_ids, group).  cost_bias values must
    be >= 0 (corridor semantics only discourage).  When all hooks are empty
    the returned dict is byte-identical (canonical JSON) to the frozen
    solver's; injected runs switch schema/version and carry an
    ``injections`` summary block.

    Per-net maps (M3 constraint seat): cost_bias_by_net =
    {net_id: {(layer_idx, ix, iy): cost}}, hard_keepout_by_net =
    {net_id: {layer_idx: iterable((ix, iy))}} -- applied ONLY to the listed
    net's search; per-net entries override global ones on the same cell.
    Empty per-net maps are normalized away (byte-parity preserved).
    """
    raw_bias = cost_bias or {}
    for v in list(raw_bias.values()) + [float(v) for m in
                                        (cost_bias_by_net or {}).values()
                                        for v in m.values()]:
        if float(v) < 0.0:
            raise V4ExpError("cost_bias values must be >= 0 (corridor "
                             "semantics only discourage)")
    # normalize: zero-valued bias entries and empty keepout sets are no-ops
    # and must not flip the run into "injected" (byte-parity guarantee)
    cost_bias = {k: float(v) for k, v in raw_bias.items() if float(v) != 0.0} or None
    hard_keepout = {li: set(c) for li, c in (hard_keepout or {}).items() if c} or None
    per_bias = {nid: {k: float(v) for k, v in m.items() if float(v) != 0.0}
                for nid, m in (cost_bias_by_net or {}).items()}
    per_bias = {nid: m for nid, m in per_bias.items() if m} or None
    per_ko = {nid: {li: set(c) for li, c in m.items() if c}
              for nid, m in (hard_keepout_by_net or {}).items()}
    per_ko = {nid: m for nid, m in per_ko.items() if m} or None

    from pcbflow.v4exp.grid import GridWorld, RoutedState

    world = GridWorld(board)
    order = [str(s) for s in request.get("route_order", [])]
    if sorted(order) != sorted(world.net_ids) or len(set(order)) != len(order):
        raise V4ExpError("route_order must list every net exactly once")
    pos = {nid: i for i, nid in enumerate(order)}
    protected = [str(s) for s in request.get("protected_net_ids", [])]
    prot = set(protected)
    for p in protected:
        if p not in pos:
            raise V4ExpError("protected net %s missing from route_order" % p)
        for nid in order:
            if nid not in prot and pos[nid] < pos[p]:
                raise V4ExpError(
                    "protected net %s must be routed before %s" % (p, nid))
    prefs = {}
    for item in request.get("layer_preferences", []):
        prefs[str(item["net_id"])] = [str(s) for s in item.get("layers", [])]
    corridors = {}
    for item in request.get("corridor_preferences", []):
        corridors[str(item["net_id"])] = [[float(a), float(b)]
                                          for a, b in item.get("waypoints_mm", [])]
    group = str(request.get("group", "A"))

    state = RoutedState()
    routes = []
    vias = []
    actions = []
    failed_at = None
    search_nodes = 0
    for i, nid in enumerate(order):
        net_bias = dict(cost_bias) if cost_bias else {}
        if per_bias and nid in per_bias:
            net_bias.update(per_bias[nid])
        net_ko = {}
        if hard_keepout:
            net_ko.update({li: set(c) for li, c in hard_keepout.items()})
        if per_ko and nid in per_ko:
            for li, c in per_ko[nid].items():
                net_ko[li] = net_ko.get(li, set()) | set(c)
        res = _route_single_net_injected(world, state, nid, prefs.get(nid),
                                         corridors.get(nid),
                                         net_ko or None,
                                         net_bias or None)
        search_nodes += res["search_nodes"]
        if res["ok"]:
            state.add_net(nid, res["cells"])
            routes.extend(res["routes"])
            vias.extend(res["vias"])
            actions.append({"seq": i, "op": "route", "net_id": nid, "status": "ok",
                            "route_ids": [r["route_id"] for r in res["routes"]],
                            "via_ids": [v["via_id"] for v in res["vias"]]})
        else:
            failed_at = nid
            actions.append({"seq": i, "op": "route", "net_id": nid,
                            "status": "failed"})
            break  # no rip-up, no reordering: single-order failure stops the run

    metrics = _frozen._compute_metrics(world, routes, vias)
    metrics["search_nodes"] = search_nodes
    metrics["ripup_count"] = 0
    violations_sum = sum(metrics["violations"].values())
    if failed_at is None and metrics["all_connected"] and violations_sum == 0:
        status = "sat"
    else:
        status = "failed"

    injected = bool(cost_bias) or bool(hard_keepout) or bool(per_bias) or bool(per_ko)
    result = {
        "schema": MIRROR_SCHEMA if injected else RUN_SCHEMA,
        "scenario_id": world.scenario_id,
        "group": group,
        "solver_version": (_frozen.SOLVER_VERSION + MIRROR_VERSION_SUFFIX)
                          if injected else _frozen.SOLVER_VERSION,
        "route_manifest_sha256_at_run": hashlib.sha256(
            canonical_json({"routes": routes, "vias": vias}).encode("utf-8")
        ).hexdigest(),
        "actions_digest": hashlib.sha256(
            canonical_json(actions).encode("utf-8")
        ).hexdigest(),
        "status": status,
        "routes": routes,
        "vias": vias,
        "metrics": metrics,
    }
    if injected:
        bias_cells = len(cost_bias) if cost_bias else 0
        ko_cells = ({li: len(set(cells)) for li, cells in sorted(hard_keepout.items())}
                    if hard_keepout else {})
        result["injections"] = {"cost_bias_cells": bias_cells,
                                "hard_keepout_cells_by_layer": ko_cells}
    if failed_at is not None:
        result["failed_at"] = failed_at
    return result
