"""pcbflow.v4exp.cmp_localsearch -- A1 等预算确定性局部搜索。

与模型臂（B1/C1/D1）完全同构的评估循环：同一 validator、同一独立 checker、
同样每场景 8 次候选评估、同样"严格改善才接受"的贪心规则；差别只在提案来源
（本模块为确定性八方向邻域，模型臂为 planner 响应）。

邻域（冻结，八方向几何合同；按预期价值排序，避免预算被弱提案吃光）：
0. replace_subpath（拐角倒角）：把拐点替换为 45° 倒角（省 0.586 格/格）；
1. replace_subpath（最短八方向替身）：以固定端点为端点，枚举对角优先/轴向
   优先两类最短八方向折线及其偏移变体——直接攻击 total_length；
2. replace_subpath（拐点微调）：对 3 顶点 route 的拐点，枚举保持两邻段为
   轴/45° 的邻近格点，按 (|Δ|₁, x, y) 排序；
3. insert_via_candidate：单 segment、无 via、有内部折点且存在其它允许层的 net；
4. move_vertex：对每个内部折点，k∈{1,2,3} 格 × 8 方向。

提案顺序 = (动作类型秩 → route_id 升序 → 参数序)，无时钟、无随机、无 argv、
无子进程；同输入逐字节一致。
"""

from __future__ import annotations

import copy

from . import cmp_patch
from .cmp_patch import (MAX_VERTEX_MOVE_CELLS, PATCH_SCHEMA,
                        _expand_polyline_cells, candidate_geometry_sha256,
                        cmp_metrics, segment_kind, validate_patch)

DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
CORNER_MAX_CELLS = 4
SHORTCUT_OFFSETS = (0, 1, 2)


def _sign(v):
    return (v > 0) - (v < 0)


def _routes_sorted(geom: dict) -> list:
    return sorted(geom.get("routes", []),
                  key=lambda r: (str(r.get("net_id")), str(r.get("route_id"))))


def _patch_header(world, board, route, geom, action):
    ident = cmp_patch.route_identity(board, route)
    return {
        "schema_version": PATCH_SCHEMA,
        "action_type": action,
        "base_candidate_geometry_sha256": candidate_geometry_sha256(geom),
        "scenario_id": board["scenario_id"],
        "route_id": route["route_id"],
        "net_id": route["net_id"],
        "relation_id": (ident["relation_ids"][0]
                        if ident["relation_ids"] else None),
        "parent_id": None,
        "fixed_endpoint_ids": list(route["endpoint_ids"]),
        "reason": "deterministic local search candidate",
        "source": "deterministic-search",
    }


def _proposal_key(patch: dict):
    return (patch["action_type"], str(patch.get("route_id")),
            str(patch.get("polyline_mm")), str(patch.get("via_mm")),
            str(patch.get("to_layer")))


def _compress_runs(world, polyline):
    """把逐格折线压缩为"直线段端点"序列（共线点合并）。

    router 输出的折线是逐格链（每个格心一个点），任何编辑都会超过
    MAX_SUBPATH_VERTICES；patch 语义只关心几何形状，故先生成压缩形式再编辑。
    """
    if not isinstance(polyline, list) or len(polyline) < 2:
        return None
    pts = [(world.cell_x(p[0]), world.cell_y(p[1])) for p in polyline]
    keep = [pts[0]]
    for i in range(1, len(pts) - 1):
        d1 = (_sign(pts[i][0] - pts[i - 1][0]),
              _sign(pts[i][1] - pts[i - 1][1]))
        d2 = (_sign(pts[i + 1][0] - pts[i][0]),
              _sign(pts[i + 1][1] - pts[i][1]))
        if d1 != d2:
            keep.append(pts[i])
    keep.append(pts[-1])
    return [[world.center_mm_x(x), world.center_mm_y(y)] for x, y in keep]


def _route_cost_estimate(world, polyline_mm):
    """route 局部代价代理：欧氏长度 + 0.5*bend 数（与冻结目标同权重）。

    仅用于候选排序（不调用 checker、不占用评估预算）；模型侧同样可以自行
    推理候选代价，故不构成不公平信息优势。
    """
    if not polyline_mm:
        return None
    pts = [(world.cell_x(p[0]), world.cell_y(p[1])) for p in polyline_mm]
    length = 0.0
    for a, b in zip(polyline_mm, polyline_mm[1:]):
        dx = float(b[0]) - float(a[0])
        dy = float(b[1]) - float(a[1])
        length += (dx * dx + dy * dy) ** 0.5
    bends = 0
    dirs = []
    for a, b in zip(pts, pts[1:]):
        d = (_sign(b[0] - a[0]), _sign(b[1] - a[1]))
        if d != (0, 0):
            dirs.append(d)
    for i in range(1, len(dirs)):
        if dirs[i] != dirs[i - 1]:
            bends += 1
    return length + 0.5 * bends


def _proxy_delta(world, geom, patch):
    """候选相对当前几何的代理改善量（越小越好）。"""
    route_id = str(patch.get("route_id"))
    base_route = next((r for r in geom["routes"]
                       if str(r.get("route_id")) == route_id), None)
    if base_route is None:
        return float("inf")
    base_cost = _route_cost_estimate(
        world, _compress_runs(world, base_route.get("polyline_mm")))
    if patch["action_type"] == "insert_via_candidate":
        return 8.0  # via 成本主导，排最后
    new_cost = _route_cost_estimate(world, patch.get("polyline_mm"))
    if base_cost is None or new_cost is None:
        return float("inf")
    return new_cost - base_cost


def _legal_polyline_shape(world, polyline) -> bool:
    return _expand_polyline_cells(world, polyline) is not None


# ------------------------------------------------------------ 动作 0：最短替身

def _shortest_replacements(world, board, route, geom):
    """整条 route 中部替换为最短八方向折线（端点钉死）的确定性候选。"""
    poly = route.get("polyline_mm")
    if not isinstance(poly, list) or len(poly) < 2:
        return
    a, b = poly[0], poly[-1]
    ax, ay = world.cell_x(a[0]), world.cell_y(a[1])
    bx, by = world.cell_x(b[0]), world.cell_y(b[1])
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return
    sx, sy = _sign(dx), _sign(dy)
    step = min(abs(dx), abs(dy))
    rest_x = abs(dx) - step
    rest_y = abs(dy) - step
    anchors = [
        (ax + sx * step, ay + sy * step),   # 对角优先
        (ax + sx * rest_x, ay),             # 轴向优先（先 x）
        (ax, ay + sy * rest_y),             # 轴向优先（先 y）
    ]
    seen = set()
    for k in SHORTCUT_OFFSETS:
        offsets = ((0, 0),) if k == 0 else (
            (k, 0), (-k, 0), (0, k), (0, -k),
            (k, k), (-k, -k), (k, -k), (-k, k))
        for cx, cy in anchors:
            for ox, oy in offsets:
                px, py = cx + ox, cy + oy
                if (px, py) == (ax, ay) or (px, py) == (bx, by):
                    continue
                if not world.in_bounds(px, py) or (px, py) in seen:
                    continue
                seen.add((px, py))
                poly_mm = [list(a),
                           [world.center_mm_x(px), world.center_mm_y(py)],
                           list(b)]
                if not _legal_polyline_shape(world, poly_mm):
                    continue
                p = _patch_header(world, board, route, geom,
                                  "replace_subpath")
                p.update({"layer": route["layer"],
                          "width_mm": route["width_mm"],
                          "polyline_mm": poly_mm})
                yield p


# ------------------------------------------------------- 动作 0：拐角倒角

def _chamfer_candidates(world, board, route, geom, s_max=4):
    """拐角倒角：把拐点替换为两个退让点，间以精确 45° 段。

    对拐点 i（入向 d_in、出向 d_out、两腿长 L1/L2），取 s=1..min(L1,L2,s_max)：
    新折线 ... p_{i-1} -> q1 -> q2 -> p_{i+1} ...，q1 = p_i - s*d_in、
    q2 = p_i + s*d_out，两邻段保持轴对齐、中段为 45°，倒角恒缩短路径
    （省 0.586*s 格）且向内收缩，通常不破坏净距与 keepout。
    """
    poly = _compress_runs(world, route.get("polyline_mm"))
    if not poly or len(poly) < 3:
        return
    pts = [(world.cell_x(p[0]), world.cell_y(p[1])) for p in poly]
    for i in range(1, len(pts) - 1):
        d_in = (_sign(pts[i][0] - pts[i - 1][0]),
                _sign(pts[i][1] - pts[i - 1][1]))
        d_out = (_sign(pts[i + 1][0] - pts[i][0]),
                 _sign(pts[i + 1][1] - pts[i][1]))
        if d_in == (0, 0) or d_out == (0, 0) or d_in == d_out:
            continue  # 共线点不是拐角
        l1 = max(abs(pts[i][0] - pts[i - 1][0]), abs(pts[i][1] - pts[i - 1][1]))
        l2 = max(abs(pts[i + 1][0] - pts[i][0]), abs(pts[i + 1][1] - pts[i][1]))
        for s in range(1, min(l1, l2, s_max) + 1):
            q1 = (pts[i][0] - s * d_in[0], pts[i][1] - s * d_in[1])
            q2 = (pts[i][0] + s * d_out[0], pts[i][1] + s * d_out[1])
            new_mm = [list(p) for p in poly[:i]] + [
                [world.center_mm_x(q1[0]), world.center_mm_y(q1[1])],
                [world.center_mm_x(q2[0]), world.center_mm_y(q2[1])]] +                 [list(p) for p in poly[i + 1:]]
            if len(new_mm) > 8:
                continue
            if not _legal_polyline_shape(world, new_mm):
                continue
            p = _patch_header(world, board, route, geom, "replace_subpath")
            p.update({"layer": route["layer"], "width_mm": route["width_mm"],
                      "polyline_mm": new_mm})
            yield p


def chamfer_stream(world, board, geom, s_max=4):
    """倒角候选专用顺序：s 由小到大外层，route 升序内层。"""
    routes = _routes_sorted(geom)
    for s in range(1, s_max + 1):
        for route in routes:
            for patch in _one_size_chamfers(world, board, route, geom, s):
                yield patch


def _one_size_chamfers(world, board, route, geom, s):
    for patch in _chamfer_candidates(world, board, route, geom, s_max=s):
        poly = patch.get("polyline_mm")
        # 只保留"该尺寸恰好等于 s"的候选（生成器内部按升序产出）
        if _chamfer_size(poly) == s:
            yield patch


def _chamfer_size(poly):
    """倒角段的对角格数（45° 段的曼哈顿半长）。"""
    if not isinstance(poly, list):
        return None
    for a, b in zip(poly, poly[1:]):
        dx = abs(round((b[0] - a[0]) / 0.25))
        dy = abs(round((b[1] - a[1]) / 0.25))
        if dx and dy and dx == dy:
            return dx
    return None


# ------------------------------------------------------------ 动作 1：拐点微调

def _corner_candidates(world, board, route, geom):
    poly = _compress_runs(world, route.get("polyline_mm"))
    if not poly or len(poly) != 3:
        return
    a, c, b = poly[0], poly[1], poly[2]
    ac = (world.cell_x(a[0]), world.cell_y(a[1]))
    cc = (world.cell_x(c[0]), world.cell_y(c[1]))
    bc = (world.cell_x(b[0]), world.cell_y(b[1]))
    cands = []
    for dx in range(-CORNER_MAX_CELLS, CORNER_MAX_CELLS + 1):
        for dy in range(-CORNER_MAX_CELLS, CORNER_MAX_CELLS + 1):
            p = (cc[0] + dx, cc[1] + dy)
            if p == cc or not world.in_bounds(*p):
                continue
            if segment_kind(ac[0], ac[1], p[0], p[1]) is None:
                continue
            if segment_kind(p[0], p[1], bc[0], bc[1]) is None:
                continue
            cands.append((abs(dx) + abs(dy), p[0], p[1]))
    for _d, x, y in sorted(cands):
        p = _patch_header(world, board, route, geom, "replace_subpath")
        p.update({"layer": route["layer"], "width_mm": route["width_mm"],
                  "polyline_mm": [list(a),
                                  [world.center_mm_x(x), world.center_mm_y(y)],
                                  list(b)]})
        yield p


# ------------------------------------------------------------ 动作 2：via

def _via_candidates(world, board, route, geom):
    nid = str(route["net_id"])
    net_routes = [r for r in geom["routes"] if str(r["net_id"]) == nid]
    net_vias = [v for v in geom["vias"] if str(v["net_id"]) == nid]
    if len(net_routes) != 1 or net_vias:
        return
    poly = _compress_runs(world, route.get("polyline_mm"))
    if not poly or len(poly) < 3:
        return
    allowed = [world.layers[li] for li in world.net_allowed_layer_indices(nid)]
    others = [l for l in sorted(allowed) if l != str(route["layer"])]
    if not others:
        return
    for i in range(1, len(poly) - 1):
        for to_layer in others:
            p = _patch_header(world, board, route, geom,
                              "insert_via_candidate")
            p.update({"layer": route["layer"],
                      "via_mm": [poly[i][0], poly[i][1]],
                      "to_layer": to_layer})
            yield p


# ------------------------------------------------------------ 动作 3：顶点微移

def _move_vertices(world, board, route, geom):
    poly = route.get("polyline_mm")
    if not isinstance(poly, list) or len(poly) < 3:
        return
    for i in range(1, len(poly) - 1):
        for k in range(1, MAX_VERTEX_MOVE_CELLS + 1):
            for dx, dy in DIRS8:
                newpoly = [list(p) for p in poly]
                newpoly[i] = [round(newpoly[i][0] + 0.25 * k * dx, 3),
                              round(newpoly[i][1] + 0.25 * k * dy, 3)]
                if newpoly[i] == list(poly[i]):
                    continue
                if not _legal_polyline_shape(world, newpoly):
                    continue
                p = _patch_header(world, board, route, geom, "move_vertex")
                p.update({"layer": route["layer"],
                          "width_mm": route["width_mm"],
                          "polyline_mm": newpoly})
                yield p


ACTION_ORDER = (chamfer_stream, _shortest_replacements,
                _corner_candidates, _via_candidates, _move_vertices)


def proposal_stream(world, board, geom):
    """按冻结束序产出候选 patch。

    顺序 = 代理改善量升序（同值按 (动作秩, route_id, 参数) 确定排序）。
    代理只用候选自身的长度/弯折估计（与冻结目标同权重），不调用 checker，
    因此"评估 8 个候选"的预算与模型臂完全一致。
    """
    routes = _routes_sorted(geom)
    scored = []
    rank = 0
    for gen in (_chamfer_candidates, _shortest_replacements,
                _corner_candidates, _move_vertices):
        rank += 1
        for route in routes:
            for patch in gen(world, board, route, geom):
                scored.append((_proxy_delta(world, geom, patch), rank,
                               str(patch.get("route_id")), _proposal_key(patch),
                               patch))
    for patch in chamfer_stream(world, board, geom):
        scored.append((_proxy_delta(world, geom, patch), 0,
                       str(patch.get("route_id")), _proposal_key(patch),
                       patch))
    via_rank = 9
    for route in routes:
        for patch in _via_candidates(world, board, route, geom):
            scored.append((_proxy_delta(world, geom, patch), via_rank,
                           str(patch.get("route_id")), _proposal_key(patch),
                           patch))
    scored.sort(key=lambda t: (t[0], t[1], t[2], str(t[3])))
    for _d, _r, _n, _k, patch in scored:
        yield patch


def run_local_search(world, board, base_geom: dict, max_proposals: int = 8):
    """A1 主循环：≤max_proposals 次评估，严格改善才接受，返回可审计记录。"""
    best = copy.deepcopy(base_geom)
    best_metrics = cmp_metrics(world, best["routes"], best["vias"])
    base_metrics = copy.deepcopy(best_metrics)
    base_hash = candidate_geometry_sha256(base_geom)
    tried = set()
    proposals = []
    accepted = 0
    improved = True
    # 每次接受改善后必须从新的 best 重建提案流（base hash 绑定当前候选）。
    while improved and len(proposals) < max_proposals:
        improved = False
        for patch in proposal_stream(world, board, best):
            if len(proposals) >= max_proposals:
                break
            key = _proposal_key(patch)
            if key in tried:
                continue
            tried.add(key)
            res = validate_patch(world, board, patch, best)
            record = {
                "seq": len(proposals),
                "action_type": patch["action_type"],
                "route_id": patch.get("route_id"),
                "base_candidate_geometry_sha256": patch[
                    "base_candidate_geometry_sha256"],
                "legal": bool(res.get("legal")),
                "reasons": list(res.get("reasons", [])),
                "accepted": False,
                "corrected_by_solver": False,
            }
            if res.get("legal") and not res.get("noop"):
                applied = cmp_patch.apply_and_check(world, board, patch, best)
                if applied.get("legal"):
                    cand = applied["geometry"]
                    cand_metrics = cmp_metrics(world, cand["routes"],
                                               cand["vias"])
                    record["candidate_objective"] = cand_metrics["objective"]
                    if cand_metrics["objective"] < best_metrics["objective"]:
                        best = cand
                        best_metrics = cand_metrics
                        accepted += 1
                        record["accepted"] = True
                        record["candidate_geometry_sha256"] = \
                            candidate_geometry_sha256(cand)
                        improved = True
            proposals.append(record)
            if improved:
                break
    return {
        "arm": "A1",
        "base_geometry_sha256": base_hash,
        "final_geometry_sha256": candidate_geometry_sha256(best),
        "final_geom": best,
        "evaluations": len(proposals),
        "accepted_count": accepted,
        "base_metrics": base_metrics,
        "final_metrics": best_metrics,
        "search_nodes": 0,
        "proposals": proposals,
    }
