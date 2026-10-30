"""pcbflow.v4_1.solver2 -- E3 求解适配层（动作空间 v2 的求解宿主；堵 K3）。

任务书 §3 E3：动作作用于"v4_1 求解适配层"——本模块即该适配层（派发词明
确许可"可新建 solver 适配模块进领地"）。v4exp/ 全部只读（零字节改动）：
GridWorld/RoutedState/dilate/separation_violation 经 import 复用，A* 结构
按 v4exp.router 冻结算法逐行镜像（同 DIRS 序、同 (f, tie, g, key) 堆序、
同 tie 计数、同 goal-on-pop 语义），保证 flat 成本下与 v4exp.router 输出
逐字节一致（112 场景全域验证，见 regression-112.json）。

相对 v4exp.router 的两处**显式扩展**（其余逐字节镜像）：

1. via 成本可插拔（costmodel.ViaCostModel）：层跳代价 = 模型按跨度计价
   （贯通/盲/埋差异化；flat 模型=v1 8.0 恒值）——A* 在每个格点的每个
   目标层试探真实跨度成本（"逐层试探成本"），而非固定 32 cells；
2. via 足迹 span-aware：via 障碍/足迹落在跨度**全部层**（layerstack 栈
   序闭区间——E2 KiCad 语义进搜索），v1 只落两端层。2 层栈上两语义
   逐字节等价（唯一跨度 F..B 两端=全栈），112 域等价性不破。

度量合同：solver-run JSON schema/字段与 v4exp 冻结口径一致；metrics 内
objective 恒为冻结公式（1.0*len + 8.0*via + 0.5*bend——与历史产物可比），
分层成本目标另报 objective_layered（诊断字段，不进冻结 objective）。

CLI：
  python -m pcbflow.v4_1.solver2 --mode regression --out out/v4.1-engineering/e3
  python -m pcbflow.v4_1.solver2 --mode ablation   --out out/v4.1-engineering/e3
（canonical JSON；零 wall-clock；v4exp 进程内 import 零子进程；板快照与
manifest 只读零回写。）

零网络、零模型 API；同输入逐字节一致。
"""

from __future__ import annotations

import hashlib
import heapq

from ..v4exp.grid import (GRID_MM, V4ExpError, GridWorld, RoutedState,
                          VIA_FOOTPRINT_RADIUS_CELLS, canonical_json,
                          dilate, separation_violation)
from ..v4exp.router import (DIRS, OBJ_BEND, OBJ_LENGTH_MM, OBJ_VIA,
                            SOLVER_VERSION, START_DIR, TURN_PENALTY_CELLS,
                            VIA_COST_CELLS, _center_in_rect)
from . import DECLARED_DATE
from .canonical import write_canonical_json
from .costmodel import ViaCostModel, via_span_class
from .layerstack import LayerStack

__all__ = ["solve_board2", "metrics_span_aware", "Solver2Error"]

SOLVER2_VERSION = "v4_1-solver2-1"
RUN_SCHEMA = "pcbflow.v4exp.solver-run/1"   # 输出载体合同与 v4exp 一致
_INF = 1 << 60


class Solver2Error(ValueError):
    """适配层合同违例。"""


# ---------------------------------------------------------------- span 语义

def _span_layers(world: GridWorld, la, lb):
    """层索引闭区间（栈序；layerstack 语义；两端含）。"""
    lo, hi = (la, lb) if la <= lb else (lb, la)
    return list(range(lo, hi + 1))


def _via_site_ok2(world, blocked, x, y, la, lb):
    """span-aware 版 _via_site_ok：3x3 足迹须在跨度全部层空闲。"""
    span = _span_layers(world, la, lb)
    r = VIA_FOOTPRINT_RADIUS_CELLS
    for li in span:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                xx, yy = x + dx, y + dy
                if not world.in_bounds(xx, yy):
                    return False
                if (xx, yy) in blocked[li]:
                    return False
    if (x, y) in blocked[lb]:
        return False
    return True


def _astar2(world, blocked, allowed_layers, start, goal, goal_any_layer,
            cost):
    """v4exp.router._astar 的镜像 + 跨度成本 cost(la, lb)->cells。

    堆序/邻域序/tie 计数/goal-on-pop 与 v4exp 逐行一致；唯一差异：
    via 边代价从常数 VIA_COST_CELLS 换为 cost(li, lj)，via 位置合法性
    从两端层足迹换为全跨度层足迹。
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
            if not _via_site_ok2(world, blocked, x, y, li, lj):
                continue
            ng = g + cost(li, lj)
            nkey = (x, y, lj, d)
            if ng < best.get(nkey, _INF):
                best[nkey] = ng
                came[nkey] = (key, "via")
                tie += 1
                heapq.heappush(heap, (ng + h(x, y), tie, ng, nkey))
    return None, expanded


def _route_single_net2(world, state, nid, pref_layer_names, waypoints_mm,
                       cost):
    """v4exp.router._route_single_net 镜像（span-aware 足迹 + 跨度成本）。"""
    out = {"ok": False, "routes": [], "vias": [], "cells": None,
           "search_nodes": 0}
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
            seg, exp = _astar2(world, blocked, allowed_sorted, cur, goal,
                               False, cost)
        else:
            seg, exp = _astar2(world, blocked, allowed_sorted, cur,
                               (tx, ty, cur[2]), True, cost)
        nodes += exp
        if seg is None:
            out["search_nodes"] = nodes
            return out
        steps.extend(seg if not steps else seg[1:])
        last = seg[-1]
        cur = (last[0], last[1], last[2])
    out["search_nodes"] = nodes

    # ---- 拆层段与 via（足迹落跨度全部层） ----
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
            for lj in _span_layers(world, cur_layer, li):
                for ddx in range(-r, r + 1):
                    for ddy in range(-r, r + 1):
                        cells[lj].add((x + ddx, y + ddy))
            runs.append({"layer": cur_layer, "cells": cur_cells})
            cur_layer = li
            cur_cells = [(x, y)]
        else:
            if li != cur_layer:
                raise Solver2Error("internal: layer change without a via step")
            px, py = cur_cells[-1]
            cur_cells.append((x, y))
            cells[li].add((x, y))
    runs.append({"layer": cur_layer, "cells": cur_cells})

    # ---- 输出 route/via dict（字段口径与 v4exp 一致） ----
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
                "annular_ring_mm": round((world.via_pad_mm
                                          - world.via_hole_mm) / 2.0, 3),
                "state": "candidate",
                "source": "solver",
            })
            prev_ep = vid
    out["routes"] = routes
    out["vias"] = vias
    out["cells"] = cells
    out["ok"] = True
    return out


# ---------------------------------------------------------------- 度量

def _reachable4(per, via_pairs, src, dst):
    """BFS 连通（4 邻域；v4exp.router._reachable 镜像）。"""
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


def _geometry_from_routes_span(world, routes, vias):
    """geometry_from_routes 镜像 + via 足迹落跨度全部层。"""
    per_net = {}
    for r in routes:
        nid = str(r["route_id"]).rsplit("-S", 1)[0]
        per = per_net.setdefault(
            nid, {li: set() for li in range(len(world.layers))})
        li = world.layer_index[str(r["layer"])]
        prev = None
        for p in r["polyline_mm"]:
            cx, cy = world.cell_x(p[0]), world.cell_y(p[1])
            per[li].add((cx, cy))
            if prev is not None:
                sx = (cx > prev[0]) - (cx < prev[0])
                sy = (cy > prev[1]) - (cy < prev[1])
                wx, wy = prev[0] + sx, prev[1] + sy
                while (wx, wy) != (cx, cy):
                    per[li].add((wx, wy))
                    wx += sx
                    wy += sy
            prev = (cx, cy)
    for v in vias:
        nid = str(v["via_id"]).rsplit("-V", 1)[0]
        per = per_net.setdefault(
            nid, {li: set() for li in range(len(world.layers))})
        cx = world.cell_x(v["center_mm"][0])
        cy = world.cell_y(v["center_mm"][1])
        lf = world.layer_index[str(v["from_layer"])]
        lt = world.layer_index[str(v["to_layer"])]
        r = VIA_FOOTPRINT_RADIUS_CELLS
        for li in _span_layers(world, lf, lt):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    per[li].add((cx + dx, cy + dy))
    return per_net


def metrics_span_aware(world, routes, vias, cost_model=None):
    """v4exp._compute_metrics 镜像（span-aware via 几何）+ 分层目标诊断。

    冻结键（all_connected/shorts/unconnected/violations/total_length_mm/
    via_count/bend_count/objective/...）口径与 v4exp.router 逐字段一致；
    附加 objective_layered（分层 via 成本目标；cost_model=None 时=冻结值）。
    """
    geom = _geometry_from_routes_span(world, routes, vias)
    n_layers = len(world.layers)

    via_pairs = {}
    for v in vias:
        cx = world.cell_x(v["center_mm"][0])
        cy = world.cell_y(v["center_mm"][1])
        lf = world.layer_index[str(v["from_layer"])]
        lt = world.layer_index[str(v["to_layer"])]
        via_pairs.setdefault((cx, cy), []).append((lf, lt))

    unconnected = 0
    for nid in world.net_ids:
        pad_a = world.pad_by_id[world.net_endpoints[nid][0]]
        pad_b = world.pad_by_id[world.net_endpoints[nid][1]]
        src = (world.cell_x(pad_a["x_mm"]), world.cell_y(pad_a["y_mm"]),
               world.layer_index[str(pad_a["layer"])])
        dst = (world.cell_x(pad_b["x_mm"]), world.cell_y(pad_b["y_mm"]),
               world.layer_index[str(pad_b["layer"])])
        per = geom.get(nid)
        if per is None or not _reachable4(per, via_pairs, src, dst):
            unconnected += 1

    present = [nid for nid in world.net_ids if nid in geom]

    shorts = 0
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            a, b = present[i], present[j]
            for li in range(n_layers):
                if separation_violation(geom[a].get(li, ()),
                                        geom[b].get(li, ())):
                    shorts += 1
                    break

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

    total_len_cells = 0
    bend_count = 0
    for nid in present:
        from ..v4exp.cmp_patch import _seg_order_key
        segs = sorted(
            (r for r in routes
             if str(r["route_id"]).rsplit("-S", 1)[0] == nid),
            key=lambda r: _seg_order_key(str(r["route_id"])))
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
    objective = (OBJ_LENGTH_MM * total_length_mm + OBJ_VIA * len(vias)
                 + OBJ_BEND * bend_count)
    if cost_model is None:
        objective_layered = objective
    else:
        via_cost = sum(cost_model.cost_mm(str(v["from_layer"]),
                                          str(v["to_layer"])) for v in vias)
        objective_layered = (OBJ_LENGTH_MM * total_length_mm + via_cost
                             + OBJ_BEND * bend_count)

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
        "objective_layered": objective_layered,
        "search_nodes": 0,
        "ripup_count": 0,
    }


# ---------------------------------------------------------------- 求解入口

def _flat_cost(_la, _lb):
    return VIA_COST_CELLS


def solve_board2(board, request, cost_model=None):
    """适配层求解入口（v4exp.router.solve_board 合同 + 可插 via 成本）。

    cost_model=None：flat（v1 等价；与 v4exp.router 逐字节一致——112 域
    验证）。cost_model=ViaCostModel(...)：层跳按跨度计价。
    输出 run dict 字段与 v4exp 冻结口径一致（solver2_version 附加诊断键）。
    """
    world = GridWorld(board)
    layers = list(world.layers)
    if cost_model is None:
        cost = _flat_cost
    else:
        if list(cost_model.stack.names) != layers:
            raise Solver2Error("cost_model 层栈与板层不一致: %r vs %r"
                               % (list(cost_model.stack.names), layers))
        table = {}

        def cost(la, lb):
            key = (la, lb) if la <= lb else (lb, la)
            v = table.get(key)
            if v is None:
                v = cost_model.cost_cells(layers[la], layers[lb], GRID_MM)
                table[key] = v
            return v

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
        res = _route_single_net2(world, state, nid, prefs.get(nid),
                                 corridors.get(nid), cost)
        search_nodes += res["search_nodes"]
        if res["ok"]:
            state.add_net(nid, res["cells"])
            routes.extend(res["routes"])
            vias.extend(res["vias"])
            actions.append({"seq": i, "op": "route", "net_id": nid,
                            "status": "ok",
                            "route_ids": [r["route_id"] for r in res["routes"]],
                            "via_ids": [v["via_id"] for v in res["vias"]]})
        else:
            failed_at = nid
            actions.append({"seq": i, "op": "route", "net_id": nid,
                            "status": "failed"})
            break  # 与 v4exp 冻结行为一致：单序失败即停（rip-up 为 E4 域）

    metrics = metrics_span_aware(world, routes, vias, cost_model)
    metrics["search_nodes"] = search_nodes
    metrics["ripup_count"] = 0
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
        "solver2_version": SOLVER2_VERSION,
        "via_cost_model": (cost_model.as_dict() if cost_model is not None
                           else {"flat": True, "params": {"flat_via_mm": 8.0}}),
        "route_manifest_sha256_at_run": hashlib.sha256(
            canonical_json({"routes": routes, "vias": vias}).encode("utf-8")
        ).hexdigest(),
        "actions_digest": hashlib.sha256(
            canonical_json(actions).encode("utf-8")).hexdigest(),
        "status": status,
        "routes": routes,
        "vias": vias,
        "metrics": metrics,
    }
    if failed_at is not None:
        result["failed_at"] = failed_at
    return result


# ---------------------------------------------------------------- 回归/消融

_PREREG_SHA256 = "d4885d96696e427d4849ae119d6f32f4aa4f8c2f8a4c110ab8c2952529e7d963"
_REG_SCHEMA = "pcbflow.v4_1.e3-regression/1"
_ABL_SCHEMA = "pcbflow.v4_1.e3-ablation/1"


def _load_manifest_112(root):
    import json
    with open(root + "/out/v4-comparative-experiment/scenario-manifest.json",
              encoding="utf-8") as f:
        return json.load(f)


def _read_board(root, sid):
    import json
    with open("%s/out/v4-comparative-experiment/board-snapshot-%s.json"
              % (root, sid), encoding="utf-8") as f:
        return json.load(f)


def _baseline_run(board):
    from ..v4exp import router
    order = sorted(str(n["net_id"]) for n in board["nets"])
    return router.solve_board(board, {"route_order": order, "group": "A0"})


def _layer_dist(world, routes, vias):
    """层分布诊断（E2 报告口径：route 段数/长度 + via 跨度分类直方图）。"""
    per_count = {name: 0 for name in world.layers}
    per_len = {name: 0.0 for name in world.layers}
    for r in routes:
        name = str(r["layer"])
        per_count[name] = per_count.get(name, 0) + 1
        pts = r["polyline_mm"]
        length = sum(((float(b[0]) - float(a[0])) ** 2
                      + (float(b[1]) - float(a[1])) ** 2) ** 0.5
                     for a, b in zip(pts, pts[1:]))
        per_len[name] = round(per_len.get(name, 0.0) + length, 6)
    span_hist = {}
    for v in vias:
        cls = via_span_class(str(v["from_layer"]), str(v["to_layer"]),
                             list(world.layers))
        span_hist[cls] = span_hist.get(cls, 0) + 1
    return {"per_layer_route_count": per_count,
            "per_layer_length_mm": per_len,
            "via_span_histogram": span_hist}


def _in2_stats(world, routes):
    name = "In2.Cu"
    if name not in world.layer_index:
        return {"in2_route_count": 0, "in2_length_mm": 0.0,
                "in2_length_share": 0.0}
    dist = _layer_dist(world, routes, [])
    total = sum(dist["per_layer_length_mm"].values())
    ln = dist["per_layer_length_mm"].get(name, 0.0)
    return {"in2_route_count": dist["per_layer_route_count"].get(name, 0),
            "in2_length_mm": ln,
            "in2_length_share": (round(ln / total, 6) if total > 0 else 0.0)}


def run_regression_112(root):
    """G3.2：112 场景配对回归（baseline v4exp vs challenger E3 栈）。"""
    from ..v4exp.cmp_patch import cmp_metrics, geom_from_run
    from .action2 import refine_v2
    from ..v4exp.grid import GridWorld

    manifest = _load_manifest_112(root)
    sids = [s["scenario_id"] for s in manifest["scenarios"]]
    records = []
    byte_equal_flat = 0
    for sid in sids:
        board = _read_board(root, sid)
        world = GridWorld(board)
        base = _baseline_run(board)
        model = ViaCostModel(list(world.layers))   # 分层默认参数
        chall = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]), "group": "E3"},
            cost_model=model)
        # flat 臂字节等价证据（适配层正确性）
        flat_run = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]), "group": "A0"})
        byte_equal_flat += int(
            flat_run["routes"] == base["routes"]
            and flat_run["vias"] == base["vias"]
            and {k: v for k, v in flat_run["metrics"].items()
                 if k != "objective_layered"}
            == {k: v for k, v in base["metrics"].items()})
        # 精化（v2 动作；冻结 objective 严格改善才接受）
        refined = refine_v2(world, board, chall, max_proposals=32)
        final = refined["final_geom"]
        base_geom = geom_from_run(base)
        bm = cmp_metrics(world, base_geom["routes"], base_geom["vias"])
        cm = cmp_metrics(world, final["routes"], final["vias"])
        records.append({
            "scenario_id": sid,
            "family": next(s["family"] for s in manifest["scenarios"]
                           if s["scenario_id"] == sid),
            "baseline": {"status": base["status"],
                         "objective": bm["objective"],
                         "via_count": bm["via_count"],
                         "violations_sum": sum(bm["violations"].values()),
                         "all_connected": bm["all_connected"]},
            "challenger": {"status": chall["status"],
                           "objective_initial": chall["metrics"]["objective"],
                           "objective_final": cm["objective"],
                           "via_count": cm["via_count"],
                           "violations_sum": sum(cm["violations"].values()),
                           "all_connected": cm["all_connected"],
                           "refine_evaluations": refined["evaluations"],
                           "refine_accepted": refined["accepted_count"]},
            "paired_delta_objective": round(cm["objective"] - bm["objective"], 6),
            "initial_byte_equal_baseline": (
                chall["routes"] == base["routes"]
                and chall["vias"] == base["vias"]),
        })
    deltas = [r["paired_delta_objective"] for r in records]
    sat_b = sum(1 for r in records if r["baseline"]["status"] == "sat")
    sat_c = sum(1 for r in records if r["challenger"]["status"] == "sat")
    viol_b = sum(1 for r in records
                 if r["baseline"]["violations_sum"] == 0)
    viol_c = sum(1 for r in records
                 if r["challenger"]["violations_sum"] == 0)
    result = {
        "schema": _REG_SCHEMA,
        "declared_date": DECLARED_DATE,
        "prereg_sha256": _PREREG_SHA256,
        "domain": "out/v4-comparative-experiment/scenario-manifest.json（112）",
        "paired_metric": "cmp_patch.cmp_metrics objective（冻结公式）",
        "records": records,
        "summary": {
            "scenario_count": len(records),
            "paired_delta_max_mm": max(deltas) if deltas else None,
            "paired_delta_min_mm": min(deltas) if deltas else None,
            "tolerance_mm": 0.0,
            "g32_objective_not_worse": all(d <= 0.0 for d in deltas),
            "sat_baseline": sat_b, "sat_challenger": sat_c,
            "violations_zero_baseline": viol_b,
            "violations_zero_challenger": viol_c,
            "g32_legality_not_lower": (sat_c >= sat_b and viol_c >= viol_b),
            "improved": sum(1 for d in deltas if d < 0),
            "equal": sum(1 for d in deltas if d == 0),
            "degraded": sum(1 for d in deltas if d > 0),
            "solver2_flat_byte_equal_v4exp": "%d/%d"
                                             % (byte_equal_flat, len(records)),
            "initial_solve_byte_equal_baseline": "%d/%d" % (
                sum(1 for r in records if r["initial_byte_equal_baseline"]),
                len(records)),
        },
    }
    return result


def run_ablation(root):
    """G3.3：via 成本消融（flat-8mm vs 分层默认；f9/f10 + 112 域）。

    报告门（prereg）：两臂同适配层同检查器（metrics_span_aware，冻结
    objective 口径 + objective_layered 诊断），逐域登记 objective/via 数/
    层分布（含 In2 利用率）；不设胜出判据，差异如实登记。
    """
    from ..v4exp.grid import GridWorld
    from .mlchain import mlboard_to_v4exp_board
    from .mlfamily import generate_all_ml

    def arm_solve(board, flat):
        world = GridWorld(board)
        model = ViaCostModel(list(world.layers), flat=flat)
        run = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]),
            "group": "E3-ABL"}, cost_model=model)
        dist = _layer_dist(world, run["routes"], run["vias"])
        in2 = _in2_stats(world, run["routes"])
        return {
            "status": run["status"],
            "objective_frozen": run["metrics"]["objective"],
            "objective_layered": run["metrics"]["objective_layered"],
            "via_count": run["metrics"]["via_count"],
            "total_length_mm": run["metrics"]["total_length_mm"],
            "bend_count": run["metrics"]["bend_count"],
            "violations_sum": sum(run["metrics"]["violations"].values()),
            "unconnected": run["metrics"]["unconnected"],
            "search_nodes": run["metrics"]["search_nodes"],
            "route_count": len(run["routes"]),
            "per_layer_route_count": dist["per_layer_route_count"],
            "per_layer_length_mm": dist["per_layer_length_mm"],
            "via_span_histogram": dist["via_span_histogram"],
            "in2": in2,
        }

    # ---- 域 1：f9/f10 多层族（20 场景；跨度分化域）----
    ml_records = []
    for ml in generate_all_ml():
        board = mlboard_to_v4exp_board(ml)
        flat = arm_solve(board, flat=True)
        layered = arm_solve(board, flat=False)
        ml_records.append({
            "scenario_id": ml["scenario_id"],
            "family": ml["family"],
            "label": ml["label"],
            "flat": flat,
            "layered": layered,
        })

    # ---- 域 2：f1–f8 112 场景（预期 2 层退化逐字节一致）----
    sids_records = []
    manifest = _load_manifest_112(root)
    byte_equal = 0
    for s in manifest["scenarios"]:
        sid = s["scenario_id"]
        board = _read_board(root, sid)
        flat_run = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]), "group": "E3-ABL"},
            cost_model=None)
        world = GridWorld(board)
        layered_model = ViaCostModel(list(world.layers))
        layered_run = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]), "group": "E3-ABL"},
            cost_model=layered_model)
        be = (flat_run["routes"] == layered_run["routes"]
              and flat_run["vias"] == layered_run["vias"]
              and flat_run["metrics"]["objective"]
              == layered_run["metrics"]["objective"])
        byte_equal += int(be)
        sids_records.append({"scenario_id": sid, "byte_equal_flat_layered": be})

    def _agg(recs, arm):
        obj_f = sum(r[arm]["objective_frozen"] for r in recs)
        obj_l = sum(r[arm]["objective_layered"] for r in recs)
        vias = sum(r[arm]["via_count"] for r in recs)
        routes = sum(r[arm]["route_count"] for r in recs)
        sat = sum(1 for r in recs if r[arm]["status"] == "sat")
        layer_counts = {}
        layer_len = {}
        span_hist = {}
        for r in recs:
            for k, v in r[arm]["per_layer_route_count"].items():
                layer_counts[k] = layer_counts.get(k, 0) + v
            for k, v in r[arm]["per_layer_length_mm"].items():
                layer_len[k] = round(layer_len.get(k, 0.0) + v, 6)
            for k, v in r[arm]["via_span_histogram"].items():
                span_hist[k] = span_hist.get(k, 0) + v
        in2_len = layer_len.get("In2.Cu", 0.0)
        total_len = sum(layer_len.values())
        return {
            "objective_frozen_total": round(obj_f, 6),
            "objective_layered_total": round(obj_l, 6),
            "via_count_total": vias,
            "route_count_total": routes,
            "sat_count": sat,
            "per_layer_route_count": layer_counts,
            "per_layer_length_mm": layer_len,
            "via_span_histogram": span_hist,
            "in2_route_count": layer_counts.get("In2.Cu", 0),
            "in2_length_mm": in2_len,
            "in2_length_share": (round(in2_len / total_len, 6)
                                 if total_len > 0 else 0.0),
        }

    return {
        "schema": _ABL_SCHEMA,
        "declared_date": DECLARED_DATE,
        "prereg_sha256": _PREREG_SHA256,
        "arms": ["flat-8mm（v1 等价）", "layered-default（prereg 默认参数表）"],
        "multilayer_family": {
            "records": ml_records,
            "flat": _agg(ml_records, "flat"),
            "layered": _agg(ml_records, "layered"),
        },
        "synthetic_112": {
            "note": "2 层栈唯一跨度=贯通 → 分层默认逐字节退化为 flat（核证）",
            "byte_equal_records": "%d/%d" % (byte_equal, len(sids_records)),
        },
    }


def main(argv=None):
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.solver2")
    ap.add_argument("--mode", required=True, choices=["regression", "ablation"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--root", default=".")
    ns = ap.parse_args(argv)
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    if ns.mode == "regression":
        res = run_regression_112(ns.root)
        write_canonical_json(out / "regression-112.json", res)
        s = res["summary"]
        print("regression-112: %d scenarios, delta_max=%s, degraded=%d, "
              "sat %d->%d, flat-byte-equal %s"
              % (s["scenario_count"], s["paired_delta_max_mm"],
                 s["degraded"], s["sat_baseline"], s["sat_challenger"],
                 s["solver2_flat_byte_equal_v4exp"]))
        ok = (s["g32_objective_not_worse"] and s["g32_legality_not_lower"])
        return 0 if ok else 1
    res = run_ablation(ns.root)
    write_canonical_json(out / "ablation-via-cost.json", res)
    ml = res["multilayer_family"]
    print("ablation: f9/f10 flat via=%d layered via=%d, "
          "flat In2 routes=%d layered In2 routes=%d; 112 byte-equal %s"
          % (ml["flat"]["via_count_total"], ml["layered"]["via_count_total"],
             ml["flat"]["in2_route_count"], ml["layered"]["in2_route_count"],
             res["synthetic_112"]["byte_equal_records"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
