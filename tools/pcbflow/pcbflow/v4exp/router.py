"""pcbflow.v4exp.router -- sequential A* maze router for the V4 experiment.

CLI contract: read exactly one JSON request from stdin, compute, print the
solver-run JSON on stdout and (when "out_path" is present) also write it to
that file.  File writing stays trivially simple so static-source hooks stay
happy; the shell orchestrates redirection.

Determinism: no clock reads, no randomness anywhere; identical input yields
byte-identical output.  Search runs on integer cell costs.

Frozen objective:  obj = 1.0*total_length_mm + 8.0*via_count + 0.5*bend_count.
A* edge costs mirror these weights on the lattice:
1 cell move = 0.25 mm, a layer via = 32 cells = 8 mm, a turn = 2 cells = 0.5 mm.
The emitted metrics are always recomputed independently from the emitted
routes/vias JSON, never from A* internals.
"""

import hashlib
import heapq
import json
import os
import sys

try:
    from .grid import (GRID_MM, VIA_FOOTPRINT_RADIUS_CELLS, V4ExpError, GridWorld,
                       RoutedState, canonical_json, dilate, geometry_from_routes,
                       separation_violation)
except ImportError:  # direct file run: python pcbflow/v4exp/router.py
    from grid import (GRID_MM, VIA_FOOTPRINT_RADIUS_CELLS, V4ExpError, GridWorld,
                      RoutedState, canonical_json, dilate, geometry_from_routes,
                      separation_violation)

SOLVER_VERSION = "v4exp-router-1"
RUN_SCHEMA = "pcbflow.v4exp.solver-run/1"

TURN_PENALTY_CELLS = 2   # 0.5 mm bend weight / 0.25 mm grid
VIA_COST_CELLS = 32      # 8.0 mm via weight / 0.25 mm grid
OBJ_LENGTH_MM = 1.0
OBJ_VIA = 8.0
OBJ_BEND = 0.5
RIPUP_CORRIDOR_GROW = 10  # V4-RIPUP-R1 §1.2: candidate-ranking corridor box growth

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR_INDEX = {(-1, 0): 0, (1, 0): 1, (0, -1): 2, (0, 1): 3}
START_DIR = 4  # sentinel: no direction yet at the path start

_INF = 1 << 60


def _via_site_ok(world, blocked, x, y, la, lb):
    """A via at (x, y) between layers la and lb: centre cell free on lb and
    the full 3x3 footprint free on BOTH layers (double occupancy rule)."""
    if (x, y) in blocked[lb]:
        return False
    r = VIA_FOOTPRINT_RADIUS_CELLS
    for li in (la, lb):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                xx, yy = x + dx, y + dy
                if not world.in_bounds(xx, yy):
                    return False
                if (xx, yy) in blocked[li]:
                    return False
    return True


def _astar(world, blocked, allowed_layers, start, goal, goal_any_layer):
    """Turn-aware A* over states (ix, iy, layer, dir).

    start/goal are (ix, iy, layer).  When goal_any_layer is true the goal is
    the goal cell on any allowed layer (used for corridor waypoints).
    Returns (steps, expanded) with steps a list of
    (ix, iy, layer, kind), kind in {"start", "move", "via"}; or (None, n).
    """
    sx, sy, sl = start
    if not world.in_bounds(sx, sy) or (sx, sy) in blocked[sl]:
        return None, 0
    if goal_any_layer:
        goal_cells = {(goal[0], goal[1], li) for li in allowed_layers}
    else:
        goal_cells = {(goal[0], goal[1], goal[2])}
    start_key = (sx, sy, sl, START_DIR)
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
            dx, dy = DIRS[nd]
            nx, ny = x + dx, y + dy
            if not world.in_bounds(nx, ny) or (nx, ny) in blocked[li]:
                continue
            if d == START_DIR or nd == d:
                step_cost = 1
            else:
                step_cost = 1 + TURN_PENALTY_CELLS
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
            if not _via_site_ok(world, blocked, x, y, li, lj):
                continue
            ng = g + VIA_COST_CELLS
            nkey = (x, y, lj, d)
            if ng < best.get(nkey, _INF):
                best[nkey] = ng
                came[nkey] = (key, "via")
                tie += 1
                heapq.heappush(heap, (ng + h(x, y), tie, ng, nkey))
    return None, expanded


def _route_single_net(world, state, nid, pref_layer_names, waypoints_mm):
    """Route one net against the current RoutedState.

    Returns {"ok", "routes", "vias", "cells", "search_nodes"}.
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
            seg, exp = _astar(world, blocked, allowed_sorted, cur, goal, False)
        else:
            seg, exp = _astar(world, blocked, allowed_sorted, cur,
                              (tx, ty, cur[2]), True)
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
            r = VIA_FOOTPRINT_RADIUS_CELLS
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


def _center_in_rect(world, cx, cy, rect):
    x = world.center_mm_x(cx)
    y = world.center_mm_y(cy)
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def _reachable(per, via_pairs, src, dst):
    """BFS connectivity over one net's lattice geometry plus its vias."""
    if (src[0], src[1]) not in per.get(src[2], ()):
        return False
    stack = [src]
    seen = {src}
    while stack:
        x, y, li = stack.pop()
        if (x, y, li) == dst:
            return True
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            node = (nx, ny, li)
            if node not in seen and (nx, ny) in per.get(li, ()):
                seen.add(node)
                stack.append(node)
        for (lf, lt) in via_pairs.get((x, y), ()):
            other = None
            if lf == li:
                other = lt
            elif lt == li:
                other = lf
            if other is None:
                continue
            node = (x, y, other)
            if node not in seen:
                seen.add(node)
                stack.append(node)
    return False


def _compute_metrics(world, routes, vias):
    """Independent re-check: rebuild everything from the emitted JSON only."""
    geom = geometry_from_routes(world, routes, vias)
    n_layers = len(world.layers)

    via_pairs = {}
    for v in vias:
        cx = world.cell_x(v["center_mm"][0])
        cy = world.cell_y(v["center_mm"][1])
        lf = world.layer_index[str(v["from_layer"])]
        lt = world.layer_index[str(v["to_layer"])]
        via_pairs.setdefault((cx, cy), []).append((lf, lt))

    # connectivity per net against the board's own endpoint pads
    unconnected = 0
    for nid in world.net_ids:
        pad_a = world.pad_by_id[world.net_endpoints[nid][0]]
        pad_b = world.pad_by_id[world.net_endpoints[nid][1]]
        src = (world.cell_x(pad_a["x_mm"]), world.cell_y(pad_a["y_mm"]),
               world.layer_index[str(pad_a["layer"])])
        dst = (world.cell_x(pad_b["x_mm"]), world.cell_y(pad_b["y_mm"]),
               world.layer_index[str(pad_b["layer"])])
        per = geom.get(nid)
        if per is None or not _reachable(per, via_pairs, src, dst):
            unconnected += 1

    present = [nid for nid in world.net_ids if nid in geom]

    # pairwise centre-line separation per layer (frozen rule).  Clearance is
    # a same-layer concept: crossing on different layers is legal, and a
    # via already participates on both of its layers through its footprint.
    shorts = 0
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            a, b = present[i], present[j]
            for li in range(n_layers):
                if separation_violation(geom[a].get(li, ()), geom[b].get(li, ())):
                    shorts += 1
                    break

    # per-route permission / width / keepout re-check
    layer_viol = 0
    width_viol = 0
    keepout_viol = 0
    for r in routes:
        nid = str(r["route_id"]).rsplit("-S", 1)[0]
        li = world.layer_index[str(r["layer"])]
        if li not in world.net_allowed_layer_indices(nid):
            layer_viol += 1
        if abs(float(r["width_mm"]) - world.net_width(nid)) > 1e-9:
            width_viol += 1
        for p in r["polyline_mm"]:
            cx = world.cell_x(p[0])
            cy = world.cell_y(p[1])
            for rect, lis in world.keepouts:
                if li in lis and _center_in_rect(world, cx, cy, rect):
                    keepout_viol += 1

    # length and bends rebuilt from polylines (cell-exact)
    total_len_cells = 0
    bend_count = 0
    for nid in present:
        segs = sorted((r for r in routes
                       if str(r["route_id"]).rsplit("-S", 1)[0] == nid),
                      key=lambda r: int(str(r["route_id"])[-2:]))
        pts = []
        for s in segs:
            for p in s["polyline_mm"]:
                c = (world.cell_x(p[0]), world.cell_y(p[1]))
                if not pts or pts[-1] != c:
                    pts.append(c)
        for i in range(1, len(pts)):
            total_len_cells += max(abs(pts[i][0] - pts[i - 1][0]),
                                   abs(pts[i][1] - pts[i - 1][1]))
        for i in range(2, len(pts)):
            d1 = (pts[i - 1][0] - pts[i - 2][0], pts[i - 1][1] - pts[i - 2][1])
            d2 = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            if d1 != d2:
                bend_count += 1
    total_length_mm = total_len_cells * GRID_MM
    objective = (OBJ_LENGTH_MM * total_length_mm
                 + OBJ_VIA * len(vias)
                 + OBJ_BEND * bend_count)

    # congestion diagnostic: per-cell multiplicity of dilated net footprints,
    # counted per layer (crossing on different layers is not congestion)
    cong = {}
    for nid in present:
        for li in range(n_layers):
            for c in dilate(geom[nid].get(li, ())):
                key = (li, c[0], c[1])
                cong[key] = cong.get(key, 0) + 1
    max_mult = max(cong.values()) if cong else 0

    return {
        "all_connected": unconnected == 0,
        "shorts": shorts,
        "unconnected": unconnected,
        "violations": {
            "clearance": shorts,
            "width": width_viol,
            "layer": layer_viol,
            "keepout": keepout_viol,
        },
        "total_length_mm": total_length_mm,
        "via_count": len(vias),
        "bend_count": bend_count,
        "max_congestion_overlap_cells": max(0, max_mult - 1),
        "objective": objective,
        "search_nodes": 0,
        "ripup_count": 0,
    }


def _snapshot_state(state):
    """Deep-copy both cells and dilated sets (ripup rollback snapshot)."""
    return ({k: {li: set(s) for li, s in v.items()} for k, v in state.cells.items()},
            {k: {li: set(s) for li, s in v.items()} for k, v in state.dilated.items()})


def _restore_state(state, snap):
    state.cells = {k: {li: set(s) for li, s in v.items()} for k, v in snap[0].items()}
    state.dilated = {k: {li: set(s) for li, s in v.items()} for k, v in snap[1].items()}


def _ripup_attempt(world, state, order, pos, nid, prefs, corridors, prot, routes, vias):
    """V4-RIPUP-R1 v1 (prereg-v4-ripup-r1.md §1.2): bounded deterministic
    single-net ripup-and-reroute for the just-failed net.

    Candidates: every earlier routed net except protected ones, ranked by
    decreasing overlap between their dilated copper and the failed net's
    corridor box (endpoint pads' cell bbox grown by RIPUP_CORRIDOR_GROW
    cells), ties broken by route position.  Scan-and-try: remove candidate
    X, retry N through the normal engine path; if N still fails, restore
    and continue; if N routes, immediately re-route X with its original
    request.  Both succeed -> accept (state keeps N and the re-routed X;
    the caller swaps X's old routes/vias for the new geometry); any other
    outcome -> full rollback to the failure-point state, next candidate.
    Candidates exhausted -> failed audit action, caller breaks as before.
    Deterministic: no clock, no randomness; at most `pos` attempts.
    """
    tried, attempts, search_nodes = [], 0, 0
    pads = [world.pad_by_id[p] for p in world.net_endpoints[nid]]
    xs = [world.cell_x(p["x_mm"]) for p in pads]
    ys = [world.cell_y(p["y_mm"]) for p in pads]
    cbox = set()
    for x in range(min(xs) - RIPUP_CORRIDOR_GROW, max(xs) + RIPUP_CORRIDOR_GROW + 1):
        for y in range(min(ys) - RIPUP_CORRIDOR_GROW, max(ys) + RIPUP_CORRIDOR_GROW + 1):
            cbox.add((x, y))

    def overlap(X):
        return sum(1 for _li, cells in state.dilated.get(X, {}).items()
                   for c in cells if c in cbox)

    cands = [X for X in order[:pos] if X not in prot]
    cands.sort(key=lambda X: (-overlap(X), order.index(X)))
    for X in cands:
        attempts += 1
        tried.append(X)
        snap = _snapshot_state(state)
        state.cells.pop(X)
        state.dilated.pop(X)
        res_n = _route_single_net(world, state, nid, prefs.get(nid), corridors.get(nid))
        search_nodes += res_n["search_nodes"]
        if not res_n["ok"]:
            _restore_state(state, snap)
            continue
        state.add_net(nid, res_n["cells"])
        res_x = _route_single_net(world, state, X, prefs.get(X), corridors.get(X))
        search_nodes += res_x["search_nodes"]
        if res_x["ok"]:
            state.add_net(X, res_x["cells"])
            audit = {"seq": pos, "op": "ripup", "net_id": nid, "status": "ok",
                     "candidates_tried": list(tried), "ripped": [X],
                     "attempts": attempts}
            return {"ok": True, "ripped": [X],
                    "routes": res_n["routes"] + res_x["routes"],
                    "vias": res_n["vias"] + res_x["vias"],
                    "actions": [audit], "search_nodes": search_nodes}
        _restore_state(state, snap)
    audit = {"seq": pos, "op": "ripup", "net_id": nid, "status": "failed",
             "candidates_tried": list(tried), "ripped": [], "attempts": attempts}
    return {"ok": False, "ripped": [], "routes": [], "vias": [],
            "actions": [audit], "search_nodes": search_nodes}


def solve_board(board, request):
    """Pure solver entry: board dict + request dict -> solver-run dict.

    request keys: route_order (required), layer_preferences,
    corridor_preferences, protected_net_ids, group (optional, default "A"),
    anchor_exemption (optional bool, default False; V4-E4 contract).
    anchor_exemption=True enables the start/endpoint anchor-area exemption:
    every pad owned by the net being routed has its pad-rectangle body
    cells subtracted from that net's static blocked set (see
    GridWorld.static_blocked_for_net), so neighbour margin growth no
    longer seals the net's own anchor cells.  Opt-in: absent or False
    reproduces the pre-E4 behaviour byte-for-byte; _astar itself is
    unchanged.  Escape beyond the pad body is not guaranteed.
    """
    world = GridWorld(board, anchor_exemption=bool(request.get("anchor_exemption", False)))
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
    # V4-RIPUP-R1 (prereg-v4-ripup-r1.md §1.1): opt-in "ripup" switch.  Absent
    # or False reproduces the pre-ripup behaviour byte-for-byte (gate G-0);
    # any non-bool value fails closed.
    ripup = request.get("ripup", False)
    if not isinstance(ripup, bool):
        raise V4ExpError("request['ripup'] must be a bool")

    state = RoutedState()
    routes = []
    vias = []
    actions = []
    failed_at = None
    search_nodes = 0
    ripup_count = 0
    for i, nid in enumerate(order):
        res = _route_single_net(world, state, nid, prefs.get(nid), corridors.get(nid))
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
            if not ripup:
                break  # no rip-up, no reordering: single-order failure stops the run
            att = _ripup_attempt(world, state, order, i, nid, prefs, corridors, prot,
                                 routes, vias)
            search_nodes += att["search_nodes"]
            actions.extend(att["actions"])
            if att["ok"]:
                failed_at = None  # ripup succeeded: the run is live again
                for x in att["ripped"]:
                    routes[:] = [r for r in routes if r["net_id"] != x]
                    vias[:] = [v for v in vias if v["net_id"] != x]
                routes.extend(att["routes"])
                vias.extend(att["vias"])
                ripup_count += len(att["ripped"])
                actions.append({"seq": i, "op": "route", "net_id": nid, "status": "ok",
                                "route_ids": [r["route_id"] for r in att["routes"]
                                              if r["net_id"] == nid],
                                "via_ids": [v["via_id"] for v in att["vias"]
                                            if v["net_id"] == nid]})
            else:
                break

    metrics = _compute_metrics(world, routes, vias)
    metrics["search_nodes"] = search_nodes
    metrics["ripup_count"] = ripup_count
    violations_sum = sum(metrics["violations"].values())
    if failed_at is None and metrics["all_connected"] and violations_sum == 0:
        status = "sat"
    else:
        status = "failed"

    result = {
        "schema": RUN_SCHEMA,
        "scenario_id": world.scenario_id,
        "group": group,
        "solver_version": SOLVER_VERSION,
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
    if failed_at is not None:
        result["failed_at"] = failed_at
    return result


def write_result(result, out_path):
    """Persist a result dict as canonical JSON (deterministic bytes)."""
    d = os.path.dirname(str(out_path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(str(out_path), "w", encoding="utf-8") as f:
        f.write(canonical_json(result))
        f.write("\n")


def main():
    payload = json.loads(sys.stdin.read())
    with open(payload["board_path"], "r", encoding="utf-8") as f:
        board = json.load(f)
    result = solve_board(board, payload)
    out_path = payload.get("out_path")
    if out_path:
        write_result(result, str(out_path))
    sys.stdout.write(canonical_json(result))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
