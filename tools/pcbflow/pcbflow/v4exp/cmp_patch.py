"""Fail-closed v4 route patch contract and independent candidate metrics.

Planner data is untrusted.  This module intentionally does not repair malformed
input: malformed structure, non-finite numbers, stale geometry, or an ambiguous
identity is rejected.  Geometry checks operate on the integer lattice and expand
every axis-aligned segment, rather than checking only declared vertices.
"""

from __future__ import annotations

import copy
import math
import re

from . import model
from .grid import (DILATION_RADIUS_CELLS, GRID_MM, VIA_FOOTPRINT_RADIUS_CELLS,
                   GridWorld, dilate, geometry_from_routes,
                   separation_violation)
from .router import OBJ_BEND, OBJ_LENGTH_MM, OBJ_VIA

PATCH_SCHEMA = "v4-route-patch/1"
RESPONSE_SCHEMA = "pcbflow.v4cmp.planner-response/1"
VALIDATED_PATCH_SCHEMA = "pcbflow.v4cmp.validated-patch/1"
VALIDATED_RESPONSE_SCHEMA = "pcbflow.v4cmp.validated-response/1"

ACTION_TYPES = ("replace_subpath", "move_vertex", "insert_via_candidate",
                "reject_route_patch")
SOURCES = ("planner", "deterministic-search", "program", "human")
ARMS = ("B0", "B1", "C0", "C1", "D0", "D1", "P1-B", "P1-C", "P1-D", "P1-E")

MAX_VERTEX_MOVE_CELLS = 4
MAX_SUBPATH_VERTICES = 8
MIN_SUBPATH_VERTICES = 3
MIN_BEND_SPACING_CELLS = 2
MAX_PATCHES_PER_CALL = 4
MAX_REASON_CHARS = 200
MAX_NOTES_CHARS = 400
UNCERTAINTY_LEVELS = ("low", "medium", "high")

KEYS_COMMON = ("schema_version", "action_type",
               "base_candidate_geometry_sha256", "scenario_id",
               "net_id", "relation_id", "parent_id",
               "fixed_endpoint_ids", "reason", "source")
KEYS_WIRE = ("route_id", "layer", "width_mm", "polyline_mm")
KEYS_VIA = ("route_id", "layer", "via_mm", "to_layer")
KEYS_REJECT = ("route_id",)  # route_id 可为 null（无已布线 segment 时）
RESPONSE_ROOT_KEYS = ("schema", "scenario_id", "board_snapshot_sha256",
                      "arm", "round", "patches", "notes", "uncertainty")

_SEG_ORDER_RE = re.compile(r"-S(\d+)([a-z]?)$")
_VIA_ID_RE = re.compile(r"-V(\d+)$")


def _rej(reason: str) -> dict:
    return {"legal": False, "reasons": [str(reason)]}


def _ok(**extra) -> dict:
    out = {"legal": True, "reasons": []}
    out.update(extra)
    return out


def _sign(v):
    """Signum for lattice deltas: -1 / 0 / +1."""
    return (v > 0) - (v < 0)


def _is_num(value) -> bool:
    """True only for finite real JSON numbers (bool is deliberately excluded)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


#: sys.float_info.max（int 有限性上界，_finite_tree 内联判定用）
_FLT_MAX = 1.7976931348623157e308


def _finite_tree(value) -> bool:
    """迭代栈版（SEC-PERF 2026-09-19）：与旧递归版语义逐位一致——
    bool/None/str 过；int/float 按 _is_num 数值有限性（|int| 超过
    float 上限时旧版 float() Overflow→False，本版以区间比较等价实现）；
    list/dict 全员检查（dict 键必须 str）；其余类型 False。
    差分对拍见 tools/_r5_scratch/secperf_golden_localsearch.py。
    """
    stack = [value]
    push = stack.append
    pop = stack.pop
    isfinite = math.isfinite
    while stack:
        v = pop()
        t = type(v)
        if t is float:
            if not isfinite(v):
                return False
        elif t is int:
            # 与 _is_num 的 isfinite(float(v)) 等价（float(int) 仅在
            # |v| > sys.float_info.max 时 Overflow）
            if v > _FLT_MAX or v < -_FLT_MAX:
                return False
        elif t is str:
            continue
        elif t is list:
            stack.extend(v)
        elif t is dict:
            for k, vv in v.items():
                if type(k) is not str and not isinstance(k, str):
                    return False
                push(vv)
        elif v is None or t is bool:
            continue
        elif isinstance(v, str) or isinstance(v, bool) or v is None:
            continue
        elif isinstance(v, (int, float)):
            if not _is_num(v):
                return False
        elif isinstance(v, list):
            stack.extend(v)
        elif isinstance(v, dict):
            for k, vv in v.items():
                if not isinstance(k, str):
                    return False
                push(vv)
        else:
            return False
    return True


def _route_net(route):
    if isinstance(route, dict) and route.get("net_id") is not None:
        return str(route["net_id"])
    rid = str(route.get("route_id", "")) if isinstance(route, dict) else ""
    return rid.rsplit("-S", 1)[0]


def _route_segment_net(route_id):
    return str(route_id).rsplit("-S", 1)[0]


def _seg_order_key(route_id: str):
    m = _SEG_ORDER_RE.search(str(route_id))
    if not m:
        return (1 << 30, str(route_id), "")
    return (int(m.group(1)), str(m.group(2)), str(route_id))


def _invalid_metrics() -> dict:
    """A finite, same-shape metric result for malformed/untrusted geometry."""
    return {
        "all_connected": False,
        "shorts": 1,
        "unconnected": 1,
        "violations": {"clearance": 1, "width": 1, "layer": 1,
                        "keepout": 1},
        "total_length_mm": 0.0,
        "via_count": 0,
        "bend_count": 0,
        "max_congestion_overlap_cells": 0,
        "objective": 0.0,
        "search_nodes": 0,
        "ripup_count": 0,
    }


def candidate_geometry_sha256(geom: dict) -> str:
    """Hash only ``{routes, vias}``, using the model hash contract.

    Invalid/non-finite input returns an empty hash instead of allowing an
    exception or a non-portable NaN representation to cross the trust boundary.
    """
    try:
        if (not isinstance(geom, dict) or "routes" not in geom
                or "vias" not in geom or not _finite_tree(geom["routes"])
                or not _finite_tree(geom["vias"])):
            return ""
        return model.sha256_of({"routes": geom["routes"],
                                "vias": geom["vias"]})
    except Exception:
        return ""


def geom_from_run(run: dict) -> dict:
    try:
        if not isinstance(run, dict):
            return {"routes": [], "vias": []}
        return {"routes": copy.deepcopy(run.get("routes", [])),
                "vias": copy.deepcopy(run.get("vias", []))}
    except Exception:
        return {"routes": [], "vias": []}


def segment_kind(ax, ay, bx, by):
    """返回轴对齐/45° 段的步进类型，非法返回 None。

    v4cmp 几何合同（冻结）：折线段只允许轴对齐或精确 45°（八方向），
    与任务书 §6.2 示例一致；其余角度一律非法。
    """
    if ax == bx and ay == by:
        return None
    dx, dy = abs(bx - ax), abs(by - ay)
    if dx == 0 or dy == 0:
        return "axis"
    if dx == dy:
        return "diagonal"
    return None


def _expand_polyline_cells(world: GridWorld, polyline) -> list | None:
    """把折线展开为经过的每个格心（含段内部）；八方向合同，非法返回 None。

    读取侧对 solver 产物保持宽容：单点退化段（router 在换层/端点处会产出）
    返回单格；重复相邻点按零长段跳过。patch 侧由 _validate_polyline 另行
    严格拒绝这两类退化（见该函数内显式检查）。

    内联版（SEC-PERF 2026-09-19）：cell_x/cell_y、_is_num、segment_kind、
    _sign 逐语义内联（判定次序与旧版一致），输出逐位不变；差分对拍见
    tools/_r5_scratch/secperf_golden_localsearch.py。
    """
    if not isinstance(polyline, list) or len(polyline) < 1:
        return None
    ox = world.origin_x
    oy = world.origin_y
    isfinite = math.isfinite
    points = []
    append_pt = points.append
    for p in polyline:
        if not isinstance(p, list) or len(p) != 2:
            return None
        vx, vy = p[0], p[1]
        # _is_num 内联（先类型门后有限性，次序同旧版）
        if (isinstance(vx, bool) or not isinstance(vx, (int, float))
                or isinstance(vy, bool) or not isinstance(vy, (int, float))):
            return None
        try:
            fx = float(vx)
            fy = float(vy)
            if not (isfinite(fx) and isfinite(fy)):
                return None
            # world.cell_x/cell_y 内联
            append_pt((int(round((fx - ox) / GRID_MM)),
                       int(round((fy - oy) / GRID_MM))))
        except Exception:
            return None
    if len(points) == 1:
        return [points[0]]
    cells = [points[0]]
    append = cells.append
    for a, b in zip(points, points[1:]):
        ax, ay = a
        bx, by = b
        if ax == bx and ay == by:
            continue
        # segment_kind 内联：axis（dx/dy 之一为 0）或 diagonal（dx==dy）
        dx = bx - ax if bx >= ax else ax - bx
        dy = by - ay if by >= ay else ay - by
        if dx == 0 or dy == 0 or dx == dy:
            sx = (bx > ax) - (bx < ax)
            sy = (by > ay) - (by < ay)
        else:
            return None
        cur_x = ax
        cur_y = ay
        while cur_x != bx or cur_y != by:
            cur_x += sx
            cur_y += sy
            append((cur_x, cur_y))
    return cells


def _expanded_route(world, route):
    if not isinstance(route, dict):
        return None
    return _expand_polyline_cells(world, route.get("polyline_mm"))


def _polyline_length_mm(polyline):
    """折线欧氏总长（mm）；数值非有限返回 None（单点/重复点按 0 长容忍）。"""
    if not isinstance(polyline, list) or len(polyline) < 1:
        return None
    total = 0.0
    for a, b in zip(polyline, polyline[1:]):
        if (not isinstance(a, list) or not isinstance(b, list)
                or len(a) != 2 or len(b) != 2
                or not all(_is_num(v) for v in (a[0], a[1], b[0], b[1]))):
            return None
        total += math.hypot(float(b[0]) - float(a[0]),
                            float(b[1]) - float(a[1]))
    return total


def _route_identity_in_context(board: dict, route: dict, routes: list) -> dict:
    identity = route_identity(board, route)
    if identity.get("parent_id") is not None:
        return identity
    try:
        rid = str(route["route_id"])
        nid = _route_net(route)
        eps = route.get("endpoint_ids")
        if not isinstance(eps, list) or not eps:
            return identity
        candidates = []
        first = str(eps[0])
        for other in routes:
            if not isinstance(other, dict) or str(other.get("route_id")) == rid:
                continue
            if _route_net(other) != nid:
                continue
            oe = other.get("endpoint_ids")
            if isinstance(oe, list) and oe and str(oe[-1]) == first:
                candidates.append(str(other.get("route_id")))
        if len(candidates) == 1:
            identity["parent_id"] = candidates[0]
    except Exception:
        pass
    return identity


def route_identity(board: dict, route: dict) -> dict:
    """Return the patch identity derived from board facts and a solver route.

    Solver routes intentionally have no relation metadata.  Relation ids are
    therefore reconstructed from board relations; endpoint ids remain the
    immutable route chain identity.  An explicit route parent is authoritative;
    chain inference is done by the validator when the complete route list is
    available.
    """
    try:
        nid = _route_net(route)
        relations = board.get("relations", []) if isinstance(board, dict) else []
        relation_ids = sorted(str(r["relation_id"]) for r in relations
                              if isinstance(r, dict)
                              and nid in [str(x) for x in r.get("members", [])]
                              and isinstance(r.get("relation_id"), str))
        eps = route.get("endpoint_ids")
        fixed = copy.deepcopy(eps) if isinstance(eps, list) else None
        parent = route.get("parent_id")
        if parent is not None:
            parent = str(parent)
        return {"relation_ids": relation_ids, "parent_id": parent,
                "fixed_endpoint_ids": fixed}
    except Exception:
        return {"relation_ids": [], "parent_id": None,
                "fixed_endpoint_ids": None}


def _relation_matches(actual, expected_ids) -> bool:
    """Accept the schema's singular relation_id and a list for multi-relations."""
    if not expected_ids:
        return actual is None
    if len(expected_ids) == 1:
        return actual == expected_ids[0] or actual == expected_ids
    return actual == expected_ids


def _route_matches(base_geom, route_id):
    routes = base_geom.get("routes") if isinstance(base_geom, dict) else None
    if not isinstance(routes, list):
        return []
    return [r for r in routes if isinstance(r, dict)
            and str(r.get("route_id")) == str(route_id)]


def _via_id_next(nid, vias):
    used = {str(v.get("via_id")) for v in vias if isinstance(v, dict)}
    maximum = 0
    for v in vias:
        if not isinstance(v, dict) or str(v.get("net_id")) != str(nid):
            continue
        m = _VIA_ID_RE.search(str(v.get("via_id", "")))
        if m:
            maximum = max(maximum, int(m.group(1)))
    candidate = f"{nid}-V{maximum + 1:02d}"
    while candidate in used:
        maximum += 1
        candidate = f"{nid}-V{maximum + 1:02d}"
    return candidate


def _via_footprint(world, via):
    if not isinstance(via, dict):
        return None
    if (not _is_num(via.get("center_mm", [None, None])[0])
            if isinstance(via.get("center_mm"), list)
            and len(via.get("center_mm")) == 2 else True):
        return None
    center = via.get("center_mm")
    if (not isinstance(center, list) or len(center) != 2
            or not _is_num(center[0]) or not _is_num(center[1])):
        return None
    try:
        cx, cy = world.cell_x(center[0]), world.cell_y(center[1])
        lf = world.layer_index[str(via["from_layer"])]
        lt = world.layer_index[str(via["to_layer"])]
    except Exception:
        return None
    r = VIA_FOOTPRINT_RADIUS_CELLS
    footprint = {(cx + dx, cy + dy)
                 for dx in range(-r, r + 1)
                 for dy in range(-r, r + 1)}
    return cx, cy, lf, lt, footprint


def _static_breakdown(world, nid):
    """Return static blocked cells plus a keepout-only map for diagnostics."""
    static = world.static_blocked_for_net(nid)
    keepout = {li: set() for li in range(len(world.layers))}
    margin = world.clearance_mm + world.net_width(nid) / 2.0
    for rect, lis in world.keepouts:
        for li in lis:
            keepout[li] |= world.cells_in_rect(rect, margin)
    return static, keepout


def _geometry_drc(world: GridWorld, routes: list, vias: list) -> dict:
    """Full cell-level DRC; route pair clearance is counted by cmp_metrics."""
    out = {"clearance": 0, "width": 0, "layer": 0, "keepout": 0}
    route_cells = []
    for route in routes:
        if not isinstance(route, dict):
            out["clearance"] += 1
            continue
        nid = _route_net(route)
        cells = _expanded_route(world, route)
        try:
            li = world.layer_index[str(route["layer"])]
            allowed = world.net_allowed_layer_indices(nid)
            if li not in allowed:
                out["layer"] += 1
            if (not _is_num(route.get("width_mm"))
                    or abs(float(route["width_mm"]) - world.net_width(nid)) > 1e-9):
                out["width"] += 1
        except Exception:
            out["layer"] += 1
            cells = None
        if cells is None:
            out["clearance"] += 1
            continue
        static, keepout = _static_breakdown(world, nid)
        for cell in cells:
            if not world.in_bounds(*cell):
                out["clearance"] += 1
            if cell in keepout.get(li, set()):
                out["keepout"] += 1
            elif cell in static.get(li, set()):
                out["clearance"] += 1
        route_cells.append((nid, li, set(cells)))

    # 跨 net 路线对净距由 cmp_metrics 的 shorts 统一计数（此处不重复计数；
    # 同 net 接触/相交合法）。via 相关的冲突不在别处计数，故留在本函数内。
    via_items = []
    for via in vias:
        fp = _via_footprint(world, via)
        if fp is None:
            out["clearance"] += 1
            continue
        _cx, _cy, lf, lt, footprint = fp
        nid = str(via.get("net_id", ""))
        try:
            allowed = world.net_allowed_layer_indices(nid)
            if lf not in allowed or lt not in allowed or lf == lt:
                out["layer"] += 1
        except Exception:
            out["layer"] += 1
        static, keepout = _static_breakdown(world, nid)
        for li in (lf, lt):
            for cell in footprint:
                if not world.in_bounds(*cell):
                    out["clearance"] += 1
                if cell in keepout.get(li, set()):
                    out["keepout"] += 1
                elif cell in static.get(li, set()):
                    out["clearance"] += 1
        via_items.append((nid, lf, lt, footprint))
        # The footprint must not enter a different net's dilated route.
        for rnid, rli, rcells in route_cells:
            if rnid != nid and rli in (lf, lt) \
                    and footprint & dilate(rcells, DILATION_RADIUS_CELLS):
                out["clearance"] += 1

    # Distinct-net via footprints cannot touch on either participating layer.
    for i, (na, la, lta, fa) in enumerate(via_items):
        for nb, lb, ltb, fb in via_items[i + 1:]:
            if na == nb:
                continue
            if ((la in (lb, ltb) or lta in (lb, ltb))
                    and fa & dilate(fb, DILATION_RADIUS_CELLS)):
                out["clearance"] += 1
    return out


def _route_bends(cells):
    if not cells or len(cells) < 3:
        return []
    directions = []
    for a, b in zip(cells, cells[1:]):
        d = (_sign(b[0] - a[0]), _sign(b[1] - a[1]))
        if d == (0, 0):
            continue
        directions.append(d)
    bends = []
    for i in range(1, len(directions)):
        if directions[i] != directions[i - 1]:
            # Cell index of the bend, not the declared vertex index.
            bends.append(i)
    return bends


def _reachable(per, via_pairs, src, dst):
    if (src[0], src[1]) not in per.get(src[2], ()):
        return False
    stack = [src]
    seen = {src}
    while stack:
        x, y, li = stack.pop()
        if (x, y, li) == dst:
            return True
        # 8 邻域连通：八方向合同下 45° 段的格心只对角相邻；对纯曼哈顿几何
        # 结果与 4 邻域一致（路径本身 4 连通），故与 solver 口径不冲突。
        for dx, dy in ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                       (0, 1), (1, -1), (1, 0), (1, 1)):
            nx, ny = x + dx, y + dy
            node = (nx, ny, li)
            if node not in seen and (nx, ny) in per.get(li, ()):
                seen.add(node)
                stack.append(node)
        for lf, lt in via_pairs.get((x, y), ()):
            other = lt if lf == li else (lf if lt == li else None)
            if other is None:
                continue
            node = (x, y, other)
            if node not in seen:
                seen.add(node)
                stack.append(node)
    return False


def cmp_metrics(world: GridWorld, routes: list, vias: list) -> dict:
    """Independent metrics mirror of ``router._compute_metrics``.

    The result always has the router metric keys.  Malformed input is converted
    to a finite failing result instead of escaping an exception.
    """
    try:
        if not isinstance(world, GridWorld) or not isinstance(routes, list) \
                or not isinstance(vias, list) or not _finite_tree(routes) \
                or not _finite_tree(vias):
            return _invalid_metrics()
        geom = geometry_from_routes(world, routes, vias)
        n_layers = len(world.layers)
        via_pairs_by_net = {}
        for v in vias:
            fp = _via_footprint(world, v)
            if fp is None:
                return _invalid_metrics()
            cx, cy, lf, lt, _ = fp
            nid = str(v["net_id"])
            via_pairs_by_net.setdefault(nid, {}).setdefault((cx, cy), []).append((lf, lt))

        unconnected = 0
        for nid in world.net_ids:
            pad_a = world.pad_by_id[world.net_endpoints[nid][0]]
            pad_b = world.pad_by_id[world.net_endpoints[nid][1]]
            src = (world.cell_x(pad_a["x_mm"]), world.cell_y(pad_a["y_mm"]),
                   world.layer_index[str(pad_a["layer"])])
            dst = (world.cell_x(pad_b["x_mm"]), world.cell_y(pad_b["y_mm"]),
                   world.layer_index[str(pad_b["layer"])])
            per = geom.get(nid)
            if per is None or not _reachable(per, via_pairs_by_net.get(nid, {}), src, dst):
                unconnected += 1

        present = [nid for nid in world.net_ids if nid in geom]
        shorts = 0
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                for li in range(n_layers):
                    if separation_violation(geom[a].get(li, ()), geom[b].get(li, ())):
                        shorts += 1
                        break

        drc = _geometry_drc(world, routes, vias)
        # Route-pair shorts are included once in clearance; all other cell DRC
        # violations come from the full post-check above.
        clearance = shorts + drc["clearance"]
        total_length_mm = 0.0
        bend_count = 0
        for nid in present:
            segs = sorted((r for r in routes if _route_net(r) == nid),
                          key=lambda r: _seg_order_key(r.get("route_id", "")))
            for seg in segs:
                cells = _expanded_route(world, seg)
                if not cells:
                    return _invalid_metrics()
                length_mm = _polyline_length_mm(seg.get("polyline_mm"))
                if length_mm is None:
                    return _invalid_metrics()
                total_length_mm += length_mm
                bends = _route_bends(cells)
                bend_count += len(bends)
        # 长度按段欧氏长（八方向合同：轴对齐段 == 格数*0.25，与 solver 口径一致；
        # 45° 段按 sqrt(2)*格数，比曼哈顿更短，如实计为收益）。
        total_length_mm = round(total_length_mm, 6)
        objective = (OBJ_LENGTH_MM * total_length_mm + OBJ_VIA * len(vias)
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
            "violations": {"clearance": clearance, "width": drc["width"],
                           "layer": drc["layer"], "keepout": drc["keepout"]},
            "total_length_mm": total_length_mm,
            "via_count": len(vias),
            "bend_count": bend_count,
            "max_congestion_overlap_cells": max(0, max_mult - 1),
            "objective": objective,
            "search_nodes": 0,
            "ripup_count": 0,
        }
    except Exception:
        return _invalid_metrics()


def board_net(board: dict, net_id):
    try:
        for n in board.get("nets", []):
            if isinstance(n, dict) and str(n.get("net_id")) == str(net_id):
                return n
    except Exception:
        pass
    return None


def validate_patch_structure(patch, board: dict) -> dict:
    """Fail-closed schema, type, and action whitelist validation."""
    try:
        if not isinstance(patch, dict):
            return _rej("patch 不是 JSON 对象")
        at = patch.get("action_type")
        if at not in ACTION_TYPES:
            return _rej("action_type 非法: %r" % (at,))
        if at in ("replace_subpath", "move_vertex"):
            allowed = set(KEYS_COMMON) | set(KEYS_WIRE)
        elif at == "insert_via_candidate":
            allowed = set(KEYS_COMMON) | set(KEYS_VIA)
        else:
            allowed = set(KEYS_COMMON) | set(KEYS_REJECT)
        unknown = set(patch) - allowed
        if unknown:
            return _rej("未知键 %r（白名单外一律拒绝）" % sorted(unknown))
        missing = [k for k in allowed if k not in patch]
        if missing:
            return _rej("缺失必需键 %r" % sorted(missing))
        if patch.get("schema_version") != PATCH_SCHEMA:
            return _rej("schema_version 非法: %r" % (patch.get("schema_version"),))
        if not isinstance(board, dict) or patch.get("scenario_id") != board.get("scenario_id"):
            return _rej("scenario_id 与板不一致")
        if patch.get("source") not in SOURCES:
            return _rej("source 非法: %r" % (patch.get("source"),))
        if not isinstance(patch.get("net_id"), (str, int)) or isinstance(patch.get("net_id"), bool):
            return _rej("net_id 缺失或非法")
        if at == "reject_route_patch":
            # 诚实弃权：net_id 与 base hash 仍须绑定（可审计），但不要求绑定
            # 一条具体 route——候选几何里该 net 可能根本没有已布线 segment
            # （如 unsat 场景），此时弃权必须合法可用。
            rid = patch.get("route_id")
            if rid is not None and not isinstance(rid, (str, int)):
                return _rej("route_id 必须为字符串/整数或 None")
        elif not isinstance(patch.get("route_id"), (str, int)) or isinstance(patch.get("route_id"), bool):
            return _rej("route_id 缺失或非法")
        reason = patch.get("reason")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > MAX_REASON_CHARS:
            return _rej("reason 缺失、为空或超长")
        fixed = patch.get("fixed_endpoint_ids")
        if (not isinstance(fixed, list)
                or not all(isinstance(x, str) and x for x in fixed)):
            return _rej("fixed_endpoint_ids 缺失或结构非法")
        if patch.get("parent_id") is not None and not isinstance(patch.get("parent_id"), str):
            return _rej("parent_id 必须为字符串或 None")
        if patch.get("relation_id") is not None and not isinstance(patch.get("relation_id"), (str, list)):
            return _rej("relation_id 必须为字符串、列表或 None")
        if at in ("replace_subpath", "move_vertex"):
            if not isinstance(patch.get("layer"), str) or not isinstance(patch.get("polyline_mm"), list):
                return _rej("wire 字段结构非法")
        elif at == "insert_via_candidate":
            if not isinstance(patch.get("layer"), str) or not isinstance(patch.get("to_layer"), str):
                return _rej("via 层字段结构非法")
        return _ok()
    except Exception:
        return _rej("patch structure exception")


def _validate_route_identity(board, patch, base_geom, routes):
    matches = _route_matches(base_geom, patch.get("route_id"))
    if len(matches) != 1:
        return _rej("route_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("route_id"), len(matches)))
    route = matches[0]
    route_nid = _route_net(route)
    if route_nid != str(patch.get("net_id")):
        return _rej("net_id 与 route 身份不一致")
    if len([r for r in routes if _route_net(r) == route_nid
            and str(r.get("route_id")) == str(patch.get("route_id"))]) != 1:
        return _rej("route_id/net_id 身份不唯一")
    ident = _route_identity_in_context(board, route, routes)
    if ident.get("fixed_endpoint_ids") != patch.get("fixed_endpoint_ids"):
        return _rej("fixed_endpoint_ids 与 base route 不一致")
    if ident.get("parent_id") != patch.get("parent_id"):
        return _rej("parent_id 与 route endpoint 链不一致")
    if not _relation_matches(patch.get("relation_id"), ident.get("relation_ids", [])):
        return _rej("relation_id 与 board relation 身份不一致")
    return _ok(route=route, identity=ident)


def _validate_polyline(world, patch, route, at):
    poly = patch.get("polyline_mm")
    if (not isinstance(poly, list) or len(poly) < 2
            or not all(isinstance(p, list) and len(p) == 2
                       and _is_num(p[0]) and _is_num(p[1]) for p in poly)):
        return _rej("polyline_mm 结构畸形")
    base_poly = route.get("polyline_mm")
    if not isinstance(base_poly, list) or len(base_poly) < 2:
        return _rej("base route polyline 畸形")
    try:
        for idx, tag in ((0, "起点"), (-1, "终点")):
            if (world.cell_x(poly[idx][0]) != world.cell_x(base_poly[idx][0])
                    or world.cell_y(poly[idx][1]) != world.cell_y(base_poly[idx][1])):
                return _rej("%s endpoint 被移动" % tag)
        if at == "move_vertex":
            if len(poly) != len(base_poly):
                return _rej("move_vertex 折点数不一致")
            diff = [i for i in range(len(poly))
                    if (world.cell_x(poly[i][0]), world.cell_y(poly[i][1]))
                    != (world.cell_x(base_poly[i][0]), world.cell_y(base_poly[i][1]))]
            if len(diff) != 1 or diff[0] in (0, len(poly) - 1):
                return _rej("move_vertex 必须恰好移动一个非端点折点")
            i = diff[0]
            dx = abs(world.cell_x(poly[i][0]) - world.cell_x(base_poly[i][0]))
            dy = abs(world.cell_y(poly[i][1]) - world.cell_y(base_poly[i][1]))
            if max(dx, dy) > MAX_VERTEX_MOVE_CELLS:
                return _rej("move_vertex 位移超过上限")
        elif not MIN_SUBPATH_VERTICES <= len(poly) <= MAX_SUBPATH_VERTICES:
            return _rej("replace_subpath 折点数超出允许范围")
        # patch 折线严格化：不得有重复相邻点、必须 >=2 点、段必须轴/45°
        for a, b in zip(poly, poly[1:]):
            if [float(a[0]), float(a[1])] == [float(b[0]), float(b[1])]:
                return _rej("polyline 不得含重复相邻点")
        if len(poly) < 2:
            return _rej("polyline 至少 2 点")
        if any(segment_kind(world.cell_x(a[0]), world.cell_y(a[1]),
                            world.cell_x(b[0]), world.cell_y(b[1])) is None
               for a, b in zip(poly, poly[1:])):
            return _rej("polyline 段必须轴对齐或精确 45°")
        cells = _expand_polyline_cells(world, poly)
        if cells is None:
            return _rej("polyline 必须为非重复的轴/45° 段")
        for p, cell in zip(poly, [
                (world.cell_x(p[0]), world.cell_y(p[1])) for p in poly]):
            if (abs(world.center_mm_x(cell[0]) - float(p[0])) > 1e-6
                    or abs(world.center_mm_y(cell[1]) - float(p[1])) > 1e-6):
                return _rej("polyline 点不在网格中心")
        if not all(world.in_bounds(*c) for c in cells):
            return _rej("polyline 出工作区")
        # 8 方向合同的退化形态检查：禁止立即反向（U 型回折），
        # 允许 1 格 45° 倒角（这是正常的八方向布线特征，不是 zigzag）。
        for i in range(1, len(poly) - 1):
            d1 = (_sign(world.cell_x(poly[i][0]) - world.cell_x(poly[i - 1][0])),
                  _sign(world.cell_y(poly[i][1]) - world.cell_y(poly[i - 1][1])))
            d2 = (_sign(world.cell_x(poly[i + 1][0]) - world.cell_x(poly[i][0])),
                  _sign(world.cell_y(poly[i + 1][1]) - world.cell_y(poly[i][1])))
            if d1 != (0, 0) and d2 != (0, 0) and d1 == (-d2[0], -d2[1]):
                return _rej("polyline 含立即反向（U 型回折）段")
        bends = _route_bends(cells)
        for a, b in zip(bends, bends[1:]):
            if b - a < MIN_BEND_SPACING_CELLS:
                return _rej("相邻弯折之间路径 cell 距离小于最小间距")
        return _ok()
    except Exception:
        return _rej("polyline validation exception")


def _validate_via_full(world, board, patch, base_geom):
    try:
        nid = str(patch["net_id"])
        routes = base_geom["routes"]
        vias = base_geom["vias"]
        net_routes = [r for r in routes if _route_net(r) == nid]
        net_vias = [v for v in vias if str(v.get("net_id")) == nid]
        if len(net_routes) != 1 or net_vias:
            return _rej("insert_via_candidate 仅允许单 segment 且无既有 via 的 net")
        route = net_routes[0]
        via_mm = patch.get("via_mm")
        if (not isinstance(via_mm, list) or len(via_mm) != 2
                or not _is_num(via_mm[0]) or not _is_num(via_mm[1])):
            return _rej("via_mm 结构畸形")
        vx, vy = world.cell_x(via_mm[0]), world.cell_y(via_mm[1])
        if (abs(world.center_mm_x(vx) - float(via_mm[0])) > 1e-6
                or abs(world.center_mm_y(vy) - float(via_mm[1])) > 1e-6):
            return _rej("via_mm 不在网格中心")
        cells = _expand_polyline_cells(world, route.get("polyline_mm"))
        points = route.get("polyline_mm")
        inner = {(world.cell_x(p[0]), world.cell_y(p[1])) for p in points[1:-1]}
        if cells is None or (vx, vy) not in inner:
            return _rej("via_mm 必须是该 segment 的内部折点")
        to_layer = str(patch.get("to_layer"))
        if to_layer not in world.layer_index:
            return _rej("to_layer 不是板层")
        fl = world.layer_index[str(route["layer"])]
        tl = world.layer_index[to_layer]
        if tl == fl or tl not in world.net_allowed_layer_indices(nid):
            return _rej("to_layer 不在 net 允许层或与当前层相同")
        fp = _via_footprint(world, {"center_mm": via_mm,
                                    "from_layer": route["layer"],
                                    "to_layer": to_layer,
                                    "net_id": nid})
        if fp is None or not all(world.in_bounds(*c) for c in fp[4]):
            return _rej("via footprint 出工作区")
        return _ok()
    except Exception:
        return _rej("via validation exception")


def validate_patch_geometry(world: GridWorld, board: dict, patch: dict,
                            base_geom: dict) -> dict:
    """Validate hash, route identity, immutable endpoints and action geometry."""
    try:
        want = candidate_geometry_sha256(base_geom)
        if not isinstance(patch.get("base_candidate_geometry_sha256"), str) \
                or not want or patch.get("base_candidate_geometry_sha256") != want:
            return _rej("base_candidate_geometry_sha256 不匹配")
        routes = base_geom.get("routes")
        if not isinstance(routes, list) or not isinstance(base_geom.get("vias"), list):
            return _rej("base geometry 结构非法")
        net = board_net(board, patch.get("net_id"))
        if net is None:
            return _rej("net_id 未知")
        at = patch["action_type"]
        if at == "reject_route_patch":
            rid = patch.get("route_id")
            if rid is None:
                return _ok()
            matches = _route_matches(base_geom, rid)
            if len(matches) > 1:
                return _rej("route_id 在 base 中不唯一")
            return _ok()
        ident = _validate_route_identity(board, patch, base_geom, routes)
        if not ident["legal"]:
            return ident
        route = ident["route"]
        try:
            li = world.layer_index.get(str(patch.get("layer")))
            if li is None or li not in set(world.net_allowed_layer_indices(str(net["net_id"]))):
                return _rej("layer 不是 net 的允许层")
            if str(route.get("layer")) != str(patch.get("layer")):
                return _rej("layer 与 base route 不一致")
            if at in ("replace_subpath", "move_vertex"):
                if (not _is_num(patch.get("width_mm"))
                        or abs(float(patch["width_mm"]) - float(route["width_mm"])) > 1e-9
                        or abs(float(route["width_mm"]) - world.net_width(str(net["net_id"]))) > 1e-9):
                    return _rej("width_mm 与 base/规则不一致")
                return _validate_polyline(world, patch, route, at)
            return _validate_via_full(world, board, patch, base_geom)
        except Exception:
            return _rej("geometry validation exception")
    except Exception:
        return _rej("geometry validation exception")


def _apply_patch_unchecked(world: GridWorld, patch: dict, base_geom: dict):
    at = patch["action_type"]
    if at == "reject_route_patch":
        return copy.deepcopy(base_geom), {"kind": "noop",
                                          "base_geometry": copy.deepcopy(base_geom)}
    route_id = str(patch["route_id"])
    base_routes = base_geom["routes"]
    new_routes = []
    removed = None
    added_route_ids = []
    added_via_ids = []
    if at in ("replace_subpath", "move_vertex"):
        for route in base_routes:
            if str(route["route_id"]) == route_id:
                removed = copy.deepcopy(route)
                nr = copy.deepcopy(route)
                nr["polyline_mm"] = [[model.mm(float(p[0])), model.mm(float(p[1]))]
                                      for p in patch["polyline_mm"]]
                nr["source"] = str(patch["source"])
                nr["state"] = "candidate"
                new_routes.append(nr)
                added_route_ids.append(route_id)
            else:
                new_routes.append(copy.deepcopy(route))
        rb = {"kind": "polyline", "route_id": route_id,
              "original_route": removed, "base_geometry": copy.deepcopy(base_geom)}
        return {"routes": new_routes, "vias": copy.deepcopy(base_geom["vias"])}, rb

    nid = str(patch["net_id"])
    via_mm = [model.mm(float(patch["via_mm"][0])), model.mm(float(patch["via_mm"][1]))]
    to_layer = str(patch["to_layer"])
    via_id = _via_id_next(nid, base_geom["vias"])
    for route in base_routes:
        if str(route["route_id"]) != route_id:
            new_routes.append(copy.deepcopy(route))
            continue
        removed = copy.deepcopy(route)
        poly = route["polyline_mm"]
        idx = next(i for i in range(1, len(poly) - 1)
                   if world.cell_x(poly[i][0]) == world.cell_x(via_mm[0])
                   and world.cell_y(poly[i][1]) == world.cell_y(via_mm[1]))
        ea, eb = route["endpoint_ids"][0], route["endpoint_ids"][1]
        ra_id = f"{route_id}a"
        rb_id = f"{route_id}b"
        ra = copy.deepcopy(route)
        ra.update({"route_id": ra_id,
                   "polyline_mm": [list(p) for p in poly[:idx + 1]],
                   "endpoint_ids": [ea, via_id], "state": "candidate",
                   "source": str(patch["source"])})
        rb_route = copy.deepcopy(route)
        rb_route.update({"route_id": rb_id,
                         "polyline_mm": [list(p) for p in poly[idx:]],
                         "layer": to_layer, "endpoint_ids": [via_id, eb],
                         "state": "candidate", "source": str(patch["source"]),
                         "parent_id": ra_id})
        new_routes.extend([ra, rb_route])
        added_route_ids.extend([ra_id, rb_id])
    via = {"via_id": via_id, "parent_id": added_route_ids[0], "net_id": nid,
           "from_layer": str(removed["layer"]), "to_layer": to_layer,
           "center_mm": via_mm, "drill_mm": world.via_hole_mm,
           "annular_ring_mm": model.mm((world.via_pad_mm - world.via_hole_mm) / 2.0),
           "state": "candidate", "source": str(patch["source"])}
    added_via_ids.append(via_id)
    return {"routes": new_routes,
            "vias": copy.deepcopy(base_geom["vias"]) + [via]}, \
        {"kind": "via_split", "route_id": route_id,
         "original_route": removed, "added_route_ids": added_route_ids,
         "added_via_ids": added_via_ids, "base_geometry": copy.deepcopy(base_geom)}


def check_candidate_geometry(world: GridWorld, board: dict, geom: dict,
                             baseline_metrics: dict | None = None) -> dict:
    """Run full post-apply DRC and enforce zero violations/connectivity monotonicity."""
    try:
        if (not isinstance(geom, dict) or not isinstance(geom.get("routes"), list)
                or not isinstance(geom.get("vias"), list)):
            return _rej("candidate geometry 结构非法")
        metrics = cmp_metrics(world, geom["routes"], geom["vias"])
        reasons = []
        violations = metrics.get("violations", {})
        if not all(_is_num(v) and math.isfinite(float(v)) for v in violations.values()):
            reasons.append("candidate metrics 非有限")
        elif sum(float(v) for v in violations.values()) != 0:
            reasons.append("candidate metrics violations != 0")
        if isinstance(baseline_metrics, dict):
            base_unconnected = baseline_metrics.get("unconnected")
            cand_unconnected = metrics.get("unconnected")
            if (_is_num(base_unconnected) and _is_num(cand_unconnected)
                    and cand_unconnected > base_unconnected):
                reasons.append("all_connected/unconnected 劣化")
            elif not _is_num(base_unconnected) or not _is_num(cand_unconnected):
                reasons.append("baseline metrics 非法")
        if reasons:
            return {"legal": False, "reasons": reasons, "metrics": metrics}
        return {"legal": True, "reasons": [], "metrics": metrics}
    except Exception:
        return _rej("candidate post-check exception")


def validate_patch(world: GridWorld, board: dict, patch: dict,
                   base_geom: dict) -> dict:
    """Complete fail-closed validation, including construction and post-check."""
    try:
        st = validate_patch_structure(patch, board)
        if not st["legal"]:
            st["action_type"] = patch.get("action_type") if isinstance(patch, dict) else None
            return st
        at = patch["action_type"]
        g = validate_patch_geometry(world, board, patch, base_geom)
        if not g["legal"]:
            g["action_type"] = at
            return g
        if at == "reject_route_patch":
            return {"legal": True, "reasons": [], "action_type": at, "noop": True}
        baseline = cmp_metrics(world, base_geom.get("routes", []), base_geom.get("vias", []))
        candidate, _ = _apply_patch_unchecked(world, patch, base_geom)
        post = check_candidate_geometry(world, board, candidate, baseline)
        post["action_type"] = at
        post["noop"] = False
        if post["legal"]:
            post["candidate_metrics"] = post.get("metrics")
        return post
    except Exception:
        return {"legal": False, "reasons": ["patch validation exception"],
                "action_type": patch.get("action_type") if isinstance(patch, dict) else None}


def apply_patch(world: GridWorld, board: dict, patch: dict, base_geom: dict):
    """Apply only a patch accepted by validate_patch; invalid input is rejected."""
    result = validate_patch(world, board, patch, base_geom)
    if not result.get("legal"):
        raise ValueError("patch rejected: " + "; ".join(result.get("reasons", [])))
    try:
        return _apply_patch_unchecked(world, patch, base_geom)
    except Exception as exc:
        raise ValueError("patch apply failed") from exc


def apply_and_check(world: GridWorld, board: dict, patch: dict, base_geom: dict):
    """Convenience API returning validation, candidate geometry and rollback record."""
    result = validate_patch(world, board, patch, base_geom)
    if not result.get("legal"):
        return result
    candidate, rollback = _apply_patch_unchecked(world, patch, base_geom)
    result = dict(result)
    result["geometry"] = candidate
    result["rollback"] = rollback
    return result


def rollback_patch(new_geom: dict, rb: dict) -> dict:
    """Restore the exact deep-copied base geometry (including split ordering)."""
    try:
        if not isinstance(rb, dict):
            raise ValueError("rollback record malformed")
        if "base_geometry" in rb:
            return copy.deepcopy(rb["base_geometry"])
        if rb.get("kind") == "noop":
            return copy.deepcopy(new_geom)
        # Compatibility with records produced by the previous implementation.
        if rb.get("kind") == "polyline":
            routes = [copy.deepcopy(rb["original_route"])
                      if str(r.get("route_id")) == str(rb.get("route_id")) else copy.deepcopy(r)
                      for r in new_geom.get("routes", [])]
            return {"routes": routes, "vias": copy.deepcopy(new_geom.get("vias", []))}
        if rb.get("kind") == "via_split":
            routes = []
            added = set(rb.get("added_route_ids", []))
            inserted = False
            for r in new_geom.get("routes", []):
                if str(r.get("route_id")) in added:
                    if not inserted:
                        routes.append(copy.deepcopy(rb["original_route"]))
                        inserted = True
                else:
                    routes.append(copy.deepcopy(r))
            vias = [copy.deepcopy(v) for v in new_geom.get("vias", [])
                    if str(v.get("via_id")) not in set(rb.get("added_via_ids", []))]
            return {"routes": routes, "vias": vias}
    except Exception as exc:
        raise ValueError("rollback failed") from exc
    raise ValueError("未知 rollback kind %r" % (rb.get("kind"),))


def validate_response(response, board: dict, expected_arm: str,
                      expected_round: int) -> dict:
    """Planner response wrapper validator; malformed responses are blocked."""
    sid = str(board.get("scenario_id")) if isinstance(board, dict) else ""

    def blocked(reason):
        return {"schema": VALIDATED_RESPONSE_SCHEMA, "scenario_id": sid,
                "arm": expected_arm, "round": expected_round,
                "blocked": True, "reason": str(reason), "rejections": [],
                "accepted_patches": []}
    try:
        if not isinstance(response, dict):
            return blocked("response 不是 JSON 对象")
        unknown = set(response) - set(RESPONSE_ROOT_KEYS)
        if unknown:
            return blocked("根级未知键 %r" % sorted(unknown))
        if response.get("schema") != RESPONSE_SCHEMA:
            return blocked("schema 非法")
        if response.get("scenario_id") != sid:
            return blocked("scenario_id 不一致")
        got = response.get("board_snapshot_sha256")
        want = model.sha256_of(board)
        if not isinstance(got, str) or got != want:
            return blocked("board_snapshot_sha256 stale/缺失")
        if response.get("arm") not in ARMS or response.get("arm") != expected_arm:
            return blocked("arm 非法或不一致")
        if response.get("round") != expected_round:
            return blocked("round 不一致")
        patches = response.get("patches")
        if not isinstance(patches, list):
            return blocked("patches 缺失或不是列表")
        notes = response.get("notes", "")
        if notes is None:
            notes = ""
        if not isinstance(notes, str) or len(notes) > MAX_NOTES_CHARS:
            return blocked("notes 非字符串或超长")
        rejections = []
        unc = response.get("uncertainty")
        if unc is not None and unc not in UNCERTAINTY_LEVELS:
            rejections.append({"item": "uncertainty", "reason": "非枚举值"})
        accepted = []
        for i, p in enumerate(patches):
            if i >= MAX_PATCHES_PER_CALL:
                rejections.append({"item": "patches[%d]" % i,
                                   "reason": "超过候选预算 K=%d，截断" % MAX_PATCHES_PER_CALL})
            else:
                accepted.append(p)
        return {"schema": VALIDATED_RESPONSE_SCHEMA, "scenario_id": sid,
                "arm": expected_arm, "round": expected_round,
                "blocked": False, "rejections": rejections,
                "accepted_patches": accepted}
    except Exception:
        return blocked("response validation exception")
