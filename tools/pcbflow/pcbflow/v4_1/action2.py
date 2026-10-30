"""pcbflow.v4_1.action2 -- 多段链重构动作空间 v2 + patch 合同 v2（E3；堵 K3）。

任务书 §3 E3：删 via / 加 via / 层重排 / 段拆并四类动作，作用于
pcbflow.v4_1.solver2 求解适配层输出的候选几何（{routes, vias} 链）；
多层语义直接复用 E2 layerstack（栈序闭区间/span 分类）与 solver2 的
span-aware 足迹度量。

patch 合同 v2（向后兼容 v1，冻结不破）：

* schema "v4-route-patch/1"：整体委托 pcbflow.v4exp.cmp_patch.validate_patch
  ——v1 四动作（replace_subpath/move_vertex/insert_via_candidate/
  reject_route_patch）语义逐字节不变（P1 81/81 负向集全数保留通过）；
* schema "v4-route-patch/2"：v1 四动作照旧（键合同与校验同 v1，仅 schema
  串放开——经 v1 委托实现）+ 五个新动作：
    delete_via      via_id + keep_layer：删 via 并把两侧段并在 keep_layer
    insert_via      route_id + layer + via_mm + to_layer：任意段内部折点处
                    加 via 换层（解除 v1"单段且无 via"限制；下游 via 跨度
                    级联更新）
    reorder_layers  route_id + layer(新层)：段换层（相邻 via 跨度级联更新；
                    禁止产生退化跨度）
    split_segment   route_id + split_mm：同层拆段（新 joint 端点）
    merge_segments  route_id + merge_with_route_id：同层相邻 joint 并段

链级语义（与 v1 子路径级的差别，显式登记）：合并折线不设 v1 的
MAX_SUBPATH_VERTICES/弯折最小间距上限（那是子路径编辑卫生规则）；
结构合法性=轴/45°、格心、界内、无重复相邻点、无立即反向（U 回折）、
端点不动；硬合法性=apply 后全量 DRC（span-aware：via 足迹按
layerstack 闭区间落全部跨度层）零违例 + unconnected 单调不劣化。

fail-closed：结构/身份/几何任一失败即拒绝；未知键白名单外一律拒绝；
本模块绝不修复畸形输入。零 IO/零子进程/零网络/零 wall-clock。

CLI：python -m pcbflow.v4_1.action2 --out out/v4.1-engineering/e3
  → negative-set-v2.json（G3.1 新动作负向集台账）
  → p1-replay-v1.json（P1 12 用例 v2 validator 重放：12/12 接受 + 81/81 拦截）
"""

from __future__ import annotations

import copy
import math

from ..v4exp import cmp_patch
from ..v4exp.cmp_patch import (ACTION_TYPES as V1_ACTION_TYPES, PATCH_SCHEMA,
                               SOURCES, _expand_polyline_cells,
                               _is_num, _relation_matches, _route_net,
                               _seg_order_key, _via_id_next,
                               board_net, candidate_geometry_sha256,
                               cmp_metrics, segment_kind, validate_patch)
from ..v4exp.grid import GridWorld
from . import DECLARED_DATE
from .canonical import write_canonical_json
from .layerstack import LayerStack
from .solver2 import SOLVER2_VERSION, metrics_span_aware

__all__ = [
    "validate_patch2", "apply_patch2", "apply_and_check2", "rollback2",
    "refine_v2", "v2_proposal_stream", "NEW_ACTION_TYPES", "PATCH_SCHEMA_V2",
]

PATCH_SCHEMA_V2 = "v4-route-patch/2"

DELETE_VIA = "delete_via"
INSERT_VIA = "insert_via"
REORDER_LAYERS = "reorder_layers"
SPLIT_SEGMENT = "split_segment"
MERGE_SEGMENTS = "merge_segments"

NEW_ACTION_TYPES = (DELETE_VIA, INSERT_VIA, REORDER_LAYERS,
                    SPLIT_SEGMENT, MERGE_SEGMENTS)
ALL_ACTION_TYPES = tuple(V1_ACTION_TYPES) + NEW_ACTION_TYPES

KEYS_COMMON = ("schema_version", "action_type",
               "base_candidate_geometry_sha256", "scenario_id",
               "net_id", "relation_id", "parent_id",
               "fixed_endpoint_ids", "reason", "source")
KEYS_DELETE_VIA = ("via_id", "keep_layer")
KEYS_INSERT_VIA = ("route_id", "layer", "via_mm", "to_layer")
KEYS_REORDER = ("route_id", "layer")
KEYS_SPLIT = ("route_id", "split_mm")
KEYS_MERGE = ("route_id", "merge_with_route_id")

_V2_KEYS = {
    DELETE_VIA: KEYS_DELETE_VIA,
    INSERT_VIA: KEYS_INSERT_VIA,
    REORDER_LAYERS: KEYS_REORDER,
    SPLIT_SEGMENT: KEYS_SPLIT,
    MERGE_SEGMENTS: KEYS_MERGE,
}

MAX_REASON_CHARS = cmp_patch.MAX_REASON_CHARS

_PREREG_SHA256 = "d4885d96696e427d4849ae119d6f32f4aa4f8c2f8a4c110ab8c2952529e7d963"


def _rej(reason):
    return {"legal": False, "reasons": [str(reason)]}


def _sign(v):
    return (v > 0) - (v < 0)


# ---------------------------------------------------------------- 结构校验

def _validate_structure_v2(patch, board):
    if not isinstance(patch, dict):
        return _rej("patch 不是 JSON 对象")
    at = patch.get("action_type")
    if at not in NEW_ACTION_TYPES:
        return _rej("action_type 非法: %r" % (at,))
    allowed = set(KEYS_COMMON) | set(_V2_KEYS[at])
    unknown = set(patch) - allowed
    if unknown:
        return _rej("未知键 %r（白名单外一律拒绝）" % sorted(unknown))
    missing = [k for k in allowed if k not in patch]
    if missing:
        return _rej("缺失必需键 %r" % sorted(missing))
    if patch.get("schema_version") != PATCH_SCHEMA_V2:
        return _rej("schema_version 非法: %r" % (patch.get("schema_version"),))
    if not isinstance(board, dict) \
            or patch.get("scenario_id") != board.get("scenario_id"):
        return _rej("scenario_id 与板不一致")
    if patch.get("source") not in SOURCES:
        return _rej("source 非法: %r" % (patch.get("source"),))
    if not isinstance(patch.get("net_id"), (str, int)) \
            or isinstance(patch.get("net_id"), bool):
        return _rej("net_id 缺失或非法")
    if at == DELETE_VIA:
        if not isinstance(patch.get("via_id"), (str, int)) \
                or isinstance(patch.get("via_id"), bool):
            return _rej("via_id 缺失或非法")
        if not isinstance(patch.get("keep_layer"), str):
            return _rej("keep_layer 缺失或非法")
    else:
        if not isinstance(patch.get("route_id"), (str, int)) \
                or isinstance(patch.get("route_id"), bool):
            return _rej("route_id 缺失或非法")
    if at == INSERT_VIA:
        if not isinstance(patch.get("layer"), str) \
                or not isinstance(patch.get("to_layer"), str):
            return _rej("via 层字段结构非法")
        vm = patch.get("via_mm")
        if (not isinstance(vm, list) or len(vm) != 2
                or not _is_num(vm[0]) or not _is_num(vm[1])):
            return _rej("via_mm 结构畸形")
    elif at == REORDER_LAYERS:
        if not isinstance(patch.get("layer"), str):
            return _rej("layer 缺失或非法")
    elif at == SPLIT_SEGMENT:
        sm = patch.get("split_mm")
        if (not isinstance(sm, list) or len(sm) != 2
                or not _is_num(sm[0]) or not _is_num(sm[1])):
            return _rej("split_mm 结构畸形")
    elif at == MERGE_SEGMENTS:
        if not isinstance(patch.get("merge_with_route_id"), (str, int)) \
                or isinstance(patch.get("merge_with_route_id"), bool):
            return _rej("merge_with_route_id 缺失或非法")
    reason = patch.get("reason")
    if not isinstance(reason, str) or not reason.strip() \
            or len(reason) > MAX_REASON_CHARS:
        return _rej("reason 缺失、为空或超长")
    fixed = patch.get("fixed_endpoint_ids")
    if (not isinstance(fixed, list)
            or not all(isinstance(x, str) and x for x in fixed)):
        return _rej("fixed_endpoint_ids 缺失或结构非法")
    if patch.get("parent_id") is not None \
            and not isinstance(patch.get("parent_id"), str):
        return _rej("parent_id 必须为字符串或 None")
    if patch.get("relation_id") is not None \
            and not isinstance(patch.get("relation_id"), (str, list)):
        return _rej("relation_id 必须为字符串、列表或 None")
    return {"legal": True, "reasons": []}


# ---------------------------------------------------------------- 链工具

def _chain_routes(routes, nid):
    return sorted((r for r in routes if _route_net(r) == str(nid)),
                  key=lambda r: _seg_order_key(str(r.get("route_id", ""))))


def _route_by_id(routes, rid):
    return [r for r in routes if isinstance(r, dict)
            and str(r.get("route_id")) == str(rid)]


def _via_by_id(vias, vid):
    return [v for v in vias if isinstance(v, dict)
            and str(v.get("via_id")) == str(vid)]


def _interior_vertex_indices(world, route):
    """折线内部折点索引列表（格心判等；含逐格链的全部内部点）。"""
    poly = route.get("polyline_mm")
    if not isinstance(poly, list) or len(poly) < 3:
        return []
    out = []
    for i in range(1, len(poly) - 1):
        p = poly[i]
        if (isinstance(p, list) and len(p) == 2
                and _is_num(p[0]) and _is_num(p[1])):
            out.append(i)
    return out


def _point_on_center(world, p):
    cx, cy = world.cell_x(p[0]), world.cell_y(p[1])
    return (abs(world.center_mm_x(cx) - float(p[0])) <= 1e-6
            and abs(world.center_mm_y(cy) - float(p[1])) <= 1e-6)


def _validate_chain_polyline(world, poly):
    """链级折线结构合法性（轴/45°、格心、界内、无重复相邻、无 U 回折）。

    显式不设 v1 子路径的折点数上限与弯折最小间距（见模块 docstring）。
    """
    if (not isinstance(poly, list) or len(poly) < 2
            or not all(isinstance(p, list) and len(p) == 2
                       and _is_num(p[0]) and _is_num(p[1]) for p in poly)):
        return _rej("折线结构畸形")
    for a, b in zip(poly, poly[1:]):
        if [float(a[0]), float(a[1])] == [float(b[0]), float(b[1])]:
            return _rej("折线不得含重复相邻点")
    for p in poly:
        if not _point_on_center(world, p):
            return _rej("折线点不在网格中心")
    cells = _expand_polyline_cells(world, poly)
    if cells is None:
        return _rej("折线段必须轴对齐或精确 45°")
    if not all(world.in_bounds(*c) for c in cells):
        return _rej("折线出工作区")
    for i in range(1, len(poly) - 1):
        d1 = (_sign(world.cell_x(poly[i][0]) - world.cell_x(poly[i - 1][0])),
              _sign(world.cell_y(poly[i][1]) - world.cell_y(poly[i - 1][1])))
        d2 = (_sign(world.cell_x(poly[i + 1][0]) - world.cell_x(poly[i][0])),
              _sign(world.cell_y(poly[i + 1][1]) - world.cell_y(poly[i][1])))
        if d1 != (0, 0) and d2 != (0, 0) and d1 == (-d2[0], -d2[1]):
            return _rej("折线含立即反向（U 型回折）段")
    return {"legal": True, "reasons": []}


def _identity_of(board, route, routes):
    return cmp_patch._route_identity_in_context(board, route, routes)


def _check_identity(patch, board, route, routes, fixed_want):
    ident = _identity_of(board, route, routes)
    if list(patch.get("fixed_endpoint_ids")) != list(fixed_want):
        return _rej("fixed_endpoint_ids 与链身份不一致")
    if ident.get("parent_id") != patch.get("parent_id"):
        return _rej("parent_id 与链身份不一致")
    if not _relation_matches(patch.get("relation_id"),
                             ident.get("relation_ids", [])):
        return _rej("relation_id 与 board relation 身份不一致")
    return {"legal": True, "reasons": []}


# ---------------------------------------------------------------- 几何校验

def _validate_geometry_v2(world, board, patch, base_geom):
    try:
        want = candidate_geometry_sha256(base_geom)
        if not isinstance(patch.get("base_candidate_geometry_sha256"), str) \
                or not want \
                or patch.get("base_candidate_geometry_sha256") != want:
            return _rej("base_candidate_geometry_sha256 不匹配")
        routes = base_geom.get("routes")
        vias = base_geom.get("vias")
        if not isinstance(routes, list) or not isinstance(vias, list):
            return _rej("base geometry 结构非法")
        net = board_net(board, patch.get("net_id"))
        if net is None:
            return _rej("net_id 未知")
        at = patch["action_type"]
        nid = str(net["net_id"])
        allowed = set(world.net_allowed_layer_indices(nid))
        if at == DELETE_VIA:
            return _validate_delete_via(world, board, patch, base_geom,
                                        routes, vias, allowed)
        if at == INSERT_VIA:
            return _validate_insert_via(world, board, patch, base_geom,
                                        routes, vias, allowed)
        if at == REORDER_LAYERS:
            return _validate_reorder(world, board, patch, base_geom,
                                     routes, vias, allowed)
        if at == SPLIT_SEGMENT:
            return _validate_split(world, board, patch, base_geom,
                                   routes, vias, allowed)
        return _validate_merge(world, board, patch, base_geom,
                               routes, vias, allowed)
    except Exception:
        return _rej("v2 geometry validation exception")


def _neighbors_of_segment(base_geom, route):
    """返回 (上游 via, 下游 via)（无则 None）——按 endpoint 链。"""
    vias = base_geom["vias"]
    routes = base_geom["routes"]
    eps = route.get("endpoint_ids")
    up = dn = None
    if isinstance(eps, list) and len(eps) == 2:
        cand_up = [v for v in vias if isinstance(v, dict)
                   and str(v.get("via_id")) == str(eps[0])]
        cand_dn = [v for v in vias if isinstance(v, dict)
                   and str(v.get("via_id")) == str(eps[1])]
        if len(cand_up) == 1:
            up = cand_up[0]
        if len(cand_dn) == 1:
            dn = cand_dn[0]
    return up, dn


def _validate_delete_via(world, board, patch, base_geom, routes, vias,
                         allowed):
    matches = _via_by_id(vias, patch.get("via_id"))
    if len(matches) != 1:
        return _rej("via_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("via_id"), len(matches)))
    via = matches[0]
    nid = str(patch.get("net_id"))
    if str(via.get("net_id", "")) != nid:
        return _rej("net_id 与 via 身份不一致")
    va, vb = str(via.get("from_layer")), str(via.get("to_layer"))
    a_list = [r for r in routes if isinstance(r, dict)
              and str(r.get("endpoint_ids", [None, None])[-1])
              == str(patch.get("via_id"))]
    b_list = [r for r in routes if isinstance(r, dict)
              and str(r.get("endpoint_ids", [None, None])[0])
              == str(patch.get("via_id"))]
    if len(a_list) != 1 or len(b_list) != 1:
        return _rej("via 两侧段不唯一（A=%d B=%d，须各恰 1）"
                    % (len(a_list), len(b_list)))
    seg_a, seg_b = a_list[0], b_list[0]
    if _route_net(seg_a) != nid or _route_net(seg_b) != nid:
        return _rej("via 两侧段与 net_id 不一致")
    keep = str(patch.get("keep_layer"))
    if keep not in (str(seg_a.get("layer")), str(seg_b.get("layer"))):
        return _rej("keep_layer %r 不在两侧段层 %r 内"
                    % (keep, sorted({str(seg_a.get("layer")),
                                     str(seg_b.get("layer"))})))
    if keep not in {world.layers[i] for i in allowed}:
        return _rej("keep_layer 不是 net 的允许层")
    pa, pb = seg_a.get("polyline_mm"), seg_b.get("polyline_mm")
    if not isinstance(pa, list) or not isinstance(pb, list) \
            or len(pa) < 1 or len(pb) < 1:
        return _rej("两侧段折线畸形")
    if (world.cell_x(pa[-1][0]), world.cell_y(pa[-1][1])) != \
            (world.cell_x(pb[0][0]), world.cell_y(pb[0][1])):
        return _rej("两侧段在 via 处不共点")
    # 相邻 via 跨度级联：并段后上游 via.to / 下游 via.from := keep_layer；
    # 级联后同层跨度（退化）拒绝
    up_via = next((v for v in vias if isinstance(v, dict)
                   and str(v.get("via_id")) == str(seg_a["endpoint_ids"][0])),
                  None)
    down_via = next((v for v in vias if isinstance(v, dict)
                     and str(v.get("via_id"))
                     == str(seg_b["endpoint_ids"][1])), None)
    if up_via is not None and str(up_via.get("from_layer")) == keep:
        return _rej("并段将产生退化 via 跨度（上游 via 同层）")
    if down_via is not None and str(down_via.get("to_layer")) == keep:
        return _rej("并段将产生退化 via 跨度（下游 via 同层）")
    if abs(float(seg_a.get("width_mm", -1)) - float(seg_b.get("width_mm", -2))) \
            > 1e-9:
        return _rej("两侧段宽度不一致（无法并段）")
    # 单点退化段（router 换层/端点处产出；v1 读取侧同宽容）：并段取另一侧
    if len(pb) == 1:
        merged = [list(p) for p in pa]
    elif len(pa) == 1:
        merged = [list(p) for p in pb]
    elif keep == str(seg_a.get("layer")):
        merged = [list(p) for p in pa] + [list(p) for p in pb[1:]]
    else:
        merged = [list(p) for p in pa[:-1]] + [list(p) for p in pb]
    if len(merged) < 2:
        return _rej("并段折线退化（两侧均为单点）")
    # 端点不动（链两端）
    if (world.cell_x(merged[0][0]), world.cell_y(merged[0][1])) != \
            (world.cell_x(pa[0][0]), world.cell_y(pa[0][1])):
        return _rej("并段起点被移动")
    if (world.cell_x(merged[-1][0]), world.cell_y(merged[-1][1])) != \
            (world.cell_x(pb[-1][0]), world.cell_y(pb[-1][1])):
        return _rej("并段终点被移动")
    shape = _validate_chain_polyline(world, merged)
    if not shape["legal"]:
        return shape
    ident = _check_identity(patch, board, seg_a, routes,
                            [str(seg_a["endpoint_ids"][0]),
                             str(seg_b["endpoint_ids"][1])])
    if not ident["legal"]:
        return ident
    return {"legal": True, "reasons": [],
            "seg_a": seg_a, "seg_b": seg_b, "via": via,
            "keep_layer": keep, "merged_polyline": merged}


def _validate_insert_via(world, board, patch, base_geom, routes, vias,
                         allowed):
    matches = _route_by_id(routes, patch.get("route_id"))
    if len(matches) != 1:
        return _rej("route_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("route_id"), len(matches)))
    route = matches[0]
    if _route_net(route) != str(patch.get("net_id")):
        return _rej("net_id 与 route 身份不一致")
    ident = _check_identity(patch, board, route, routes,
                            [str(x) for x in route["endpoint_ids"]])
    if not ident["legal"]:
        return ident
    if str(route.get("layer")) != str(patch.get("layer")):
        return _rej("layer 与 base route 不一致")
    fl = world.layer_index.get(str(patch.get("layer")))
    tl = world.layer_index.get(str(patch.get("to_layer")))
    if tl is None:
        return _rej("to_layer 不是板层")
    if tl == fl or tl not in allowed:
        return _rej("to_layer 不在 net 允许层或与当前层相同")
    vm = patch.get("via_mm")
    if not _point_on_center(world, vm):
        return _rej("via_mm 不在网格中心")
    idx = None
    poly = route.get("polyline_mm")
    for i in _interior_vertex_indices(world, route):
        if (world.cell_x(poly[i][0]), world.cell_y(poly[i][1])) == \
                (world.cell_x(vm[0]), world.cell_y(vm[1])):
            idx = i
            break
    if idx is None:
        return _rej("via_mm 必须是该 segment 的内部折点")
    # 下游 via 跨度级联：R 末端的 via from_layer 将变 to_layer
    _up, dn = _neighbors_of_segment(base_geom, route)
    if dn is not None:
        dn_to = world.layer_index.get(str(dn.get("to_layer")))
        if dn_to == tl:
            return _rej("insert_via 将产生退化 via 跨度（下游 via 同层）")
    # via 足迹界内（跨度语义：闭区间各层同一 xy 平面界内判定）
    cx, cy = world.cell_x(vm[0]), world.cell_y(vm[1])
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if not world.in_bounds(cx + dx, cy + dy):
                return _rej("via footprint 出工作区")
    return {"legal": True, "reasons": [], "route": route,
            "split_index": idx, "to_layer": str(patch.get("to_layer")),
            "down_via": dn}


def _validate_reorder(world, board, patch, base_geom, routes, vias, allowed):
    matches = _route_by_id(routes, patch.get("route_id"))
    if len(matches) != 1:
        return _rej("route_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("route_id"), len(matches)))
    route = matches[0]
    if _route_net(route) != str(patch.get("net_id")):
        return _rej("net_id 与 route 身份不一致")
    ident = _check_identity(patch, board, route, routes,
                            [str(x) for x in route["endpoint_ids"]])
    if not ident["legal"]:
        return ident
    new_layer = str(patch.get("layer"))
    tl = world.layer_index.get(new_layer)
    if tl is None:
        return _rej("layer 不是板层")
    if tl not in allowed:
        return _rej("layer 不是 net 的允许层")
    if new_layer == str(route.get("layer")):
        return _rej("layer 与当前层相同（层重排须换层）")
    up, dn = _neighbors_of_segment(base_geom, route)
    if up is not None:
        if str(up.get("from_layer")) == new_layer:
            return _rej("层重排将产生退化 via 跨度（上游 via 同层）")
    if dn is not None:
        if str(dn.get("to_layer")) == new_layer:
            return _rej("层重排将产生退化 via 跨度（下游 via 同层）")
    return {"legal": True, "reasons": [], "route": route,
            "new_layer": new_layer, "up_via": up, "down_via": dn}


def _validate_split(world, board, patch, base_geom, routes, vias, allowed):
    matches = _route_by_id(routes, patch.get("route_id"))
    if len(matches) != 1:
        return _rej("route_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("route_id"), len(matches)))
    route = matches[0]
    if _route_net(route) != str(patch.get("net_id")):
        return _rej("net_id 与 route 身份不一致")
    ident = _check_identity(patch, board, route, routes,
                            [str(x) for x in route["endpoint_ids"]])
    if not ident["legal"]:
        return ident
    sm = patch.get("split_mm")
    if not _point_on_center(world, sm):
        return _rej("split_mm 不在网格中心")
    idx = None
    poly = route.get("polyline_mm")
    for i in _interior_vertex_indices(world, route):
        if (world.cell_x(poly[i][0]), world.cell_y(poly[i][1])) == \
                (world.cell_x(sm[0]), world.cell_y(sm[1])):
            idx = i
            break
    if idx is None:
        return _rej("split_mm 必须是该 segment 的内部折点")
    return {"legal": True, "reasons": [], "route": route, "split_index": idx}


def _validate_merge(world, board, patch, base_geom, routes, vias, allowed):
    a_matches = _route_by_id(routes, patch.get("route_id"))
    if len(a_matches) != 1:
        return _rej("route_id %r 在 base 中出现 %d 次（须恰 1 次）"
                    % (patch.get("route_id"), len(a_matches)))
    b_matches = _route_by_id(routes, patch.get("merge_with_route_id"))
    if len(b_matches) != 1:
        return _rej("merge_with_route_id 在 base 中出现 %d 次（须恰 1 次）"
                    % len(b_matches))
    seg_a, seg_b = a_matches[0], b_matches[0]
    if str(seg_a.get("route_id")) == str(seg_b.get("route_id")):
        return _rej("merge 两段不得为同一段")
    nid = str(patch.get("net_id"))
    if _route_net(seg_a) != nid or _route_net(seg_b) != nid:
        return _rej("net_id 与段身份不一致")
    if str(seg_a.get("layer")) != str(seg_b.get("layer")):
        return _rej("merge 仅允许同层相邻段")
    joint = str(seg_a.get("endpoint_ids", [None, None])[-1])
    if str(seg_b.get("endpoint_ids", [None, None])[0]) != joint:
        return _rej("两段不按 endpoint 链相邻（A 末端 != B 首端）")
    # joint 必须是拆分 joint：不是 pad、不是 via
    if joint in {str(p.get("pad_id")) for p in board.get("pads", [])}:
        return _rej("merge 边界是 pad（链端，不可并）")
    if _via_by_id(vias, joint):
        return _rej("merge 边界是 via（须用 delete_via）")
    if abs(float(seg_a.get("width_mm", -1))
           - float(seg_b.get("width_mm", -2))) > 1e-9:
        return _rej("两段宽度不一致（无法并段）")
    pa, pb = seg_a.get("polyline_mm"), seg_b.get("polyline_mm")
    if not isinstance(pa, list) or not isinstance(pb, list):
        return _rej("段折线畸形")
    if (world.cell_x(pa[-1][0]), world.cell_y(pa[-1][1])) != \
            (world.cell_x(pb[0][0]), world.cell_y(pb[0][1])):
        return _rej("两段在 joint 处不共点")
    merged = [list(p) for p in pa] + [list(p) for p in pb[1:]]
    shape = _validate_chain_polyline(world, merged)
    if not shape["legal"]:
        return shape
    ident = _check_identity(patch, board, seg_a, routes,
                            [str(seg_a["endpoint_ids"][0]),
                             str(seg_b["endpoint_ids"][1])])
    if not ident["legal"]:
        return ident
    return {"legal": True, "reasons": [], "seg_a": seg_a, "seg_b": seg_b,
            "merged_polyline": merged}


# ---------------------------------------------------------------- 应用

def _joint_id_next(route_id, geom):
    used = set()
    for r in geom["routes"]:
        if isinstance(r, dict) and isinstance(r.get("endpoint_ids"), list):
            used.update(str(e) for e in r["endpoint_ids"])
    for v in geom["vias"]:
        if isinstance(v, dict):
            used.add(str(v.get("via_id")))
    n = 1
    while "%s-J%02d" % (route_id, n) in used:
        n += 1
    return "%s-J%02d" % (route_id, n)


def _apply_patch2_unchecked(world, patch, base_geom, info):
    at = patch["action_type"]
    routes = [copy.deepcopy(r) for r in base_geom["routes"]]
    vias = [copy.deepcopy(v) for v in base_geom["vias"]]
    rb = {"kind": "v2_" + at,
          "base_geometry": copy.deepcopy(base_geom)}

    if at == DELETE_VIA:
        via, seg_a, seg_b = info["via"], info["seg_a"], info["seg_b"]
        merged = copy.deepcopy(seg_a)
        merged.update({
            "layer": info["keep_layer"],
            "polyline_mm": [list(p) for p in info["merged_polyline"]],
            "endpoint_ids": [str(seg_a["endpoint_ids"][0]),
                             str(seg_b["endpoint_ids"][1])],
            "state": "candidate",
            "source": str(patch["source"]),
        })
        new_routes = []
        replaced = False
        for r in routes:
            if str(r.get("route_id")) == str(seg_b.get("route_id")):
                continue
            if str(r.get("route_id")) == str(seg_a.get("route_id")) and \
                    not replaced:
                new_routes.append(merged)
                replaced = True
            else:
                new_routes.append(r)
        # 相邻 via 级联：上游 via.to / 下游 via.from := keep_layer；
        # 下游 via 的 parent 指向并段结果
        up_via = next((v for v in vias if isinstance(v, dict)
                       and str(v.get("via_id"))
                       == str(seg_a["endpoint_ids"][0])), None)
        down_via = next((v for v in vias if isinstance(v, dict)
                         and str(v.get("via_id"))
                         == str(seg_b["endpoint_ids"][1])), None)
        if up_via is not None:
            up_via["to_layer"] = info["keep_layer"]
        if down_via is not None:
            down_via["from_layer"] = info["keep_layer"]
            down_via["parent_id"] = str(seg_a.get("route_id"))
        vias = [v for v in vias
                if str(v.get("via_id")) != str(via.get("via_id"))]
        rb.update({"removed_via_id": str(via.get("via_id")),
                   "removed_route_ids": [str(seg_b.get("route_id"))],
                   "added_route_ids": [str(seg_a.get("route_id"))]})
        return {"routes": new_routes, "vias": vias}, rb

    if at == INSERT_VIA:
        route = info["route"]
        idx = info["split_index"]
        to_layer = info["to_layer"]
        nid = str(patch["net_id"])
        rid = str(route["route_id"])
        via_id = _via_id_next(nid, vias)
        ra_id, rb_id = rid + "a", rid + "b"
        poly = route["polyline_mm"]
        ra = copy.deepcopy(route)
        ra.update({"route_id": ra_id,
                   "polyline_mm": [list(p) for p in poly[:idx + 1]],
                   "endpoint_ids": [str(route["endpoint_ids"][0]), via_id],
                   "state": "candidate", "source": str(patch["source"])})
        rbseg = copy.deepcopy(route)
        rbseg.update({"route_id": rb_id,
                      "polyline_mm": [list(p) for p in poly[idx:]],
                      "layer": to_layer,
                      "endpoint_ids": [via_id,
                                       str(route["endpoint_ids"][1])],
                      "state": "candidate",
                      "source": str(patch["source"]),
                      "parent_id": ra_id})
        via = {"via_id": via_id, "parent_id": ra_id, "net_id": nid,
               "from_layer": str(route["layer"]), "to_layer": to_layer,
               "center_mm": [float(patch["via_mm"][0]),
                             float(patch["via_mm"][1])],
               "drill_mm": world.via_hole_mm,
               "annular_ring_mm": round((world.via_pad_mm
                                         - world.via_hole_mm) / 2.0, 3),
               "state": "candidate", "source": str(patch["source"])}
        new_routes = []
        for r in routes:
            if str(r.get("route_id")) == rid:
                new_routes.extend([ra, rbseg])
            else:
                new_routes.append(r)
        new_vias = list(vias)
        if info.get("down_via") is not None:
            dvid = str(info["down_via"].get("via_id"))
            for v in new_vias:
                if str(v.get("via_id")) == dvid:
                    v["from_layer"] = to_layer
                    v["parent_id"] = rb_id
        new_vias.append(via)
        rb.update({"removed_route_ids": [rid],
                   "added_route_ids": [ra_id, rb_id],
                   "added_via_ids": [via_id]})
        return {"routes": new_routes, "vias": new_vias}, rb

    if at == REORDER_LAYERS:
        route = info["route"]
        new_layer = info["new_layer"]
        rid = str(route["route_id"])
        new_routes = []
        for r in routes:
            if str(r.get("route_id")) == rid:
                r2 = copy.deepcopy(r)
                r2["layer"] = new_layer
                r2["state"] = "candidate"
                r2["source"] = str(patch["source"])
                new_routes.append(r2)
            else:
                new_routes.append(r)
        for v in vias:
            if info.get("up_via") is not None and \
                    str(v.get("via_id")) == str(info["up_via"].get("via_id")):
                v["to_layer"] = new_layer
            if info.get("down_via") is not None and \
                    str(v.get("via_id")) == str(info["down_via"].get("via_id")):
                v["from_layer"] = new_layer
        rb.update({"reordered_route_id": rid, "new_layer": new_layer})
        return {"routes": new_routes, "vias": vias}, rb

    if at == SPLIT_SEGMENT:
        route = info["route"]
        idx = info["split_index"]
        rid = str(route["route_id"])
        joint = _joint_id_next(rid, base_geom)
        ra_id, rb_id = rid + "a", rid + "b"
        poly = route["polyline_mm"]
        ra = copy.deepcopy(route)
        ra.update({"route_id": ra_id,
                   "polyline_mm": [list(p) for p in poly[:idx + 1]],
                   "endpoint_ids": [str(route["endpoint_ids"][0]), joint],
                   "state": "candidate", "source": str(patch["source"])})
        rbseg = copy.deepcopy(route)
        rbseg.update({"route_id": rb_id,
                      "polyline_mm": [list(p) for p in poly[idx:]],
                      "endpoint_ids": [joint,
                                       str(route["endpoint_ids"][1])],
                      "state": "candidate",
                      "source": str(patch["source"]),
                      "parent_id": ra_id})
        new_routes = []
        for r in routes:
            if str(r.get("route_id")) == rid:
                new_routes.extend([ra, rbseg])
            else:
                new_routes.append(r)
        for v in vias:
            if str(v.get("parent_id")) == rid:
                v["parent_id"] = rb_id
        rb.update({"removed_route_ids": [rid],
                   "added_route_ids": [ra_id, rb_id],
                   "joint_id": joint})
        return {"routes": new_routes, "vias": vias}, rb

    # MERGE_SEGMENTS
    seg_a, seg_b = info["seg_a"], info["seg_b"]
    merged = copy.deepcopy(seg_a)
    merged.update({
        "polyline_mm": [list(p) for p in info["merged_polyline"]],
        "endpoint_ids": [str(seg_a["endpoint_ids"][0]),
                         str(seg_b["endpoint_ids"][1])],
        "state": "candidate",
        "source": str(patch["source"]),
    })
    new_routes = []
    replaced = False
    for r in routes:
        if str(r.get("route_id")) == str(seg_b.get("route_id")):
            continue
        if str(r.get("route_id")) == str(seg_a.get("route_id")) and \
                not replaced:
            new_routes.append(merged)
            replaced = True
        else:
            new_routes.append(r)
    for v in vias:
        if str(v.get("parent_id")) == str(seg_b.get("route_id")):
            v["parent_id"] = str(seg_a.get("route_id"))
    rb.update({"removed_route_ids": [str(seg_b.get("route_id"))],
               "added_route_ids": [str(seg_a.get("route_id"))]})
    return {"routes": new_routes, "vias": vias}, rb


# ---------------------------------------------------------------- 合同入口

def _check_candidate_span(world, geom, baseline_metrics=None):
    """apply 后全量检查（span-aware 口径 + unconnected 单调不劣化）。"""
    try:
        if (not isinstance(geom, dict)
                or not isinstance(geom.get("routes"), list)
                or not isinstance(geom.get("vias"), list)):
            return _rej("candidate geometry 结构非法")
        metrics = metrics_span_aware(world, geom["routes"], geom["vias"])
        reasons = []
        if sum(float(v) for v in metrics["violations"].values()) != 0:
            reasons.append("candidate violations != 0（span-aware 口径）")
        if isinstance(baseline_metrics, dict):
            base_u = baseline_metrics.get("unconnected")
            cand_u = metrics.get("unconnected")
            if (isinstance(base_u, (int, float))
                    and isinstance(cand_u, (int, float))
                    and cand_u > base_u):
                reasons.append("unconnected 劣化")
        if reasons:
            return {"legal": False, "reasons": reasons, "metrics": metrics}
        return {"legal": True, "reasons": [], "metrics": metrics}
    except Exception:
        return _rej("candidate post-check exception")


def validate_patch2(world, board, patch, base_geom):
    """patch 合同 v2 总入口（v1 委托 + v2 新动作全量校验）。"""
    try:
        if not isinstance(patch, dict):
            return _rej("patch 不是 JSON 对象")
        schema = patch.get("schema_version")
        if schema == PATCH_SCHEMA:
            return validate_patch(world, board, patch, base_geom)
        if schema != PATCH_SCHEMA_V2:
            return _rej("schema_version 非法: %r" % (schema,))
        at = patch.get("action_type")
        if at in V1_ACTION_TYPES:
            # v2 schema 下的 v1 动作：键合同与校验语义与 v1 一致——
            # 仅 schema 串放开（拷贝改牌后整体委托 v1 validator）
            delegated = copy.deepcopy(patch)
            delegated["schema_version"] = PATCH_SCHEMA
            return validate_patch(world, board, delegated, base_geom)
        st = _validate_structure_v2(patch, board)
        if not st["legal"]:
            st = dict(st)
            st["action_type"] = at
            return st
        g = _validate_geometry_v2(world, board, patch, base_geom)
        if not g["legal"]:
            g = dict(g)
            g["action_type"] = at
            return g
        baseline = cmp_metrics(world, base_geom.get("routes", []),
                               base_geom.get("vias", []))
        candidate, _rb = _apply_patch2_unchecked(world, patch, base_geom, g)
        post = _check_candidate_span(world, candidate, baseline)
        post = dict(post)
        post["action_type"] = at
        post["noop"] = False
        if post["legal"]:
            post["candidate_metrics"] = post.get("metrics")
        return post
    except Exception:
        return {"legal": False,
                "reasons": ["patch v2 validation exception"],
                "action_type": patch.get("action_type")
                if isinstance(patch, dict) else None}


def apply_patch2(world, board, patch, base_geom):
    result = validate_patch2(world, board, patch, base_geom)
    if not result.get("legal"):
        raise ValueError("patch rejected: " + "; ".join(result.get("reasons", [])))
    schema = patch.get("schema_version")
    if schema == PATCH_SCHEMA_V2 and \
            patch.get("action_type") in NEW_ACTION_TYPES:
        g = _validate_geometry_v2(world, board, patch, base_geom)
        return _apply_patch2_unchecked(world, patch, base_geom, g)
    if schema == PATCH_SCHEMA_V2:
        delegated = copy.deepcopy(patch)
        delegated["schema_version"] = PATCH_SCHEMA
        return cmp_patch._apply_patch_unchecked(world, delegated, base_geom)
    return cmp_patch._apply_patch_unchecked(world, patch, base_geom)


def apply_and_check2(world, board, patch, base_geom):
    result = validate_patch2(world, board, patch, base_geom)
    if not result.get("legal"):
        return result
    candidate, rollback = apply_patch2(world, board, patch, base_geom)
    result = dict(result)
    result["geometry"] = candidate
    result["rollback"] = rollback
    return result


def rollback2(_new_geom, rb):
    """恢复 base 几何（v2 记录统一携带 base_geometry 深拷贝）。"""
    if not isinstance(rb, dict) or "base_geometry" not in rb:
        raise ValueError("rollback record malformed（v2 记录须含 base_geometry）")
    return copy.deepcopy(rb["base_geometry"])


# ---------------------------------------------------------------- 提案流

def _compress(world, polyline):
    from ..v4exp.cmp_localsearch import _compress_runs
    return _compress_runs(world, polyline)


def _patch_header2(world, board, geom, action, **kw):
    nid = kw.get("net_id")
    route = kw.get("route")
    ident = cmp_patch.route_identity(board, route) if route is not None else {
        "relation_ids": [], "parent_id": None, "fixed_endpoint_ids": []}
    header = {
        "schema_version": PATCH_SCHEMA_V2,
        "action_type": action,
        "base_candidate_geometry_sha256": candidate_geometry_sha256(geom),
        "scenario_id": board["scenario_id"],
        "net_id": nid,
        "relation_id": (ident["relation_ids"][0]
                        if ident["relation_ids"] else None),
        "parent_id": (route or {}).get("parent_id")
        if route is not None else None,
        "fixed_endpoint_ids": list((route or {}).get("endpoint_ids", []))
        if route is not None else [],
        "reason": "v2 multi-segment chain refactor candidate",
        "source": "deterministic-search",
    }
    header.update({k: v for k, v in kw.items()
                   if k not in ("net_id", "route")})
    return header


def _delete_via_candidates(world, board, geom):
    for via in sorted((v for v in geom["vias"] if isinstance(v, dict)),
                      key=lambda v: str(v.get("via_id"))):
        nid = str(via.get("net_id", ""))
        for keep in sorted({str(via.get("from_layer")),
                            str(via.get("to_layer"))}):
            p = _patch_header2(world, board, geom, DELETE_VIA,
                               net_id=nid, route=None)
            # 链身份：并段结果的端点 = 两侧段链端
            seg_a = next((r for r in geom["routes"] if isinstance(r, dict)
                          and str(r.get("endpoint_ids", [None, None])[-1])
                          == str(via.get("via_id"))), None)
            seg_b = next((r for r in geom["routes"] if isinstance(r, dict)
                          and str(r.get("endpoint_ids", [None, None])[0])
                          == str(via.get("via_id"))), None)
            if seg_a is None or seg_b is None:
                continue
            p["fixed_endpoint_ids"] = [str(seg_a["endpoint_ids"][0]),
                                       str(seg_b["endpoint_ids"][1])]
            p["parent_id"] = seg_a.get("parent_id")
            ident = cmp_patch.route_identity(board, seg_a)
            p["relation_id"] = (ident["relation_ids"][0]
                                if ident["relation_ids"] else None)
            p["via_id"] = str(via.get("via_id"))
            p["keep_layer"] = keep
            yield p


def _merge_candidates(world, board, geom):
    routes = [r for r in geom["routes"] if isinstance(r, dict)]
    via_ids = {str(v.get("via_id")) for v in geom["vias"]
               if isinstance(v, dict)}
    for seg_a in sorted(routes, key=lambda r: str(r.get("route_id"))):
        joint = str(seg_a.get("endpoint_ids", [None, None])[-1])
        if joint in via_ids:
            continue  # via 边界走 delete_via
        seg_b = next((r for r in routes
                      if str(r.get("endpoint_ids", [None, None])[0]) == joint
                      and str(r.get("route_id"))
                      != str(seg_a.get("route_id"))), None)
        if seg_b is None:
            continue
        if str(seg_a.get("layer")) != str(seg_b.get("layer")):
            continue
        p = _patch_header2(world, board, geom, MERGE_SEGMENTS,
                           net_id=_route_net(seg_a), route=seg_a)
        p["route_id"] = str(seg_a.get("route_id"))
        p["fixed_endpoint_ids"] = [str(seg_a["endpoint_ids"][0]),
                                   str(seg_b["endpoint_ids"][1])]
        p["merge_with_route_id"] = str(seg_b.get("route_id"))
        yield p


def _reorder_candidates(world, board, geom):
    for route in sorted((r for r in geom["routes"] if isinstance(r, dict)),
                        key=lambda r: str(r.get("route_id"))):
        nid = _route_net(route)
        allowed = [world.layers[i] for i in world.net_allowed_layer_indices(nid)]
        for new_layer in sorted(allowed):
            if new_layer == str(route.get("layer")):
                continue
            p = _patch_header2(world, board, geom, REORDER_LAYERS,
                               net_id=nid, route=route)
            p["route_id"] = str(route.get("route_id"))
            p["layer"] = new_layer
            yield p


def _split_candidates(world, board, geom):
    for route in sorted((r for r in geom["routes"] if isinstance(r, dict)),
                        key=lambda r: str(r.get("route_id"))):
        poly = _compress(world, route.get("polyline_mm"))
        if not poly or len(poly) < 3:
            continue
        for i in range(1, len(poly) - 1):
            p = _patch_header2(world, board, geom, SPLIT_SEGMENT,
                               net_id=_route_net(route), route=route)
            p["route_id"] = str(route.get("route_id"))
            p["split_mm"] = [float(poly[i][0]), float(poly[i][1])]
            yield p


def _insert_via_candidates(world, board, geom):
    for route in sorted((r for r in geom["routes"] if isinstance(r, dict)),
                        key=lambda r: str(r.get("route_id"))):
        nid = _route_net(route)
        allowed = [world.layers[i] for i in world.net_allowed_layer_indices(nid)]
        others = [l for l in sorted(allowed)
                  if l != str(route.get("layer"))]
        if not others:
            continue
        poly = _compress(world, route.get("polyline_mm"))
        if not poly or len(poly) < 3:
            continue
        for i in range(1, len(poly) - 1):
            for to_layer in others:
                p = _patch_header2(world, board, geom, INSERT_VIA,
                                   net_id=nid, route=route)
                p["route_id"] = str(route.get("route_id"))
                p["layer"] = str(route.get("layer"))
                p["via_mm"] = [float(poly[i][0]), float(poly[i][1])]
                p["to_layer"] = to_layer
                yield p


def v2_proposal_stream(world, board, geom):
    """确定性 v2 提案流（动作秩 delete_via < merge < reorder < split < insert_via；
    同秩内对象 id/参数升序；无时钟无随机，同输入逐字节一致）。"""
    for gen in (_delete_via_candidates, _merge_candidates,
                _reorder_candidates, _split_candidates,
                _insert_via_candidates):
        yield from gen(world, board, geom)


# ------------------------------------------------------------ 合成基座

def synthetic_chain_base():
    """合成 4 层板 + 手工三 via 之字形链（delete_via / reorder_layers 正例）。

    ml 族求解输出里单段重排/删 via 恒非法（墙/pad 层物理阻止）——本基座
    用跨度交错链（F..B / B..In1 / In1..B）使中链 V2 删除（keep=In1）与
    S3 段重排（In1→In2）成为真实合法动作；同时提供异网段（n2）供身份
    类突变。板规则与 v4exp 合成域同族（grid 0.25/clearance 0.2/宽 0.3/
    via 0.6/0.3）。
    """
    sid = "e3syn-zigzag-01"
    board = {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": sid,
        "split": "dev",
        "family": "e3syn",
        "seed": 0,
        "board": {"bbox_mm": [0, 0, 20, 10],
                  "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]},
        "rules": {
            "grid_mm": 0.25,
            "clearance_mm": 0.2,
            "width_mm": {"default": 0.3},
            "via": {"pad_mm": 0.6, "hole_mm": 0.3},
            "allowed_layers": {"default": ["F.Cu", "In1.Cu", "In2.Cu",
                                           "B.Cu"]},
        },
        "pads": [
            {"pad_id": "p1", "net_id": "n1", "layer": "F.Cu",
             "x_mm": 2.0, "y_mm": 5.0, "w_mm": 1.0, "h_mm": 1.0},
            {"pad_id": "p2", "net_id": "n1", "layer": "B.Cu",
             "x_mm": 18.0, "y_mm": 5.0, "w_mm": 1.0, "h_mm": 1.0},
            {"pad_id": "q1", "net_id": "n2", "layer": "F.Cu",
             "x_mm": 4.0, "y_mm": 1.0, "w_mm": 1.0, "h_mm": 1.0},
            {"pad_id": "q2", "net_id": "n2", "layer": "F.Cu",
             "x_mm": 8.0, "y_mm": 1.0, "w_mm": 1.0, "h_mm": 1.0},
        ],
        "nets": [
            {"net_id": "n1", "net_class": "default", "endpoints": ["p1", "p2"]},
            {"net_id": "n2", "net_class": "default", "endpoints": ["q1", "q2"]},
        ],
        "keepouts": [],
        "relations": [],
        "label": "satisfiable",
    }

    def seg(rid, layer, pts, eps, parent=None):
        return {"route_id": rid, "net_id": "n1", "layer": layer,
                "width_mm": 0.3,
                "polyline_mm": [[round(x, 2), round(y, 2)]
                                for (x, y) in pts],
                "endpoint_ids": eps, "parent_id": parent,
                "state": "candidate", "source": "solver"}

    def line(x0, x1, y):
        return [(x0 + 0.25 * i, y) for i in range(int((x1 - x0) / 0.25) + 1)]

    def via(vid, parent, fl, tl, x):
        return {"via_id": vid, "parent_id": parent, "net_id": "n1",
                "from_layer": fl, "to_layer": tl, "center_mm": [x, 5.0],
                "drill_mm": 0.3, "annular_ring_mm": 0.15,
                "state": "candidate", "source": "solver"}

    n2_pts = [(x, 1.0) for x in
              [4.0 + 0.25 * i for i in range(int((8.0 - 4.0) / 0.25) + 1)]]
    s03_pts = ([(10.0 + 0.25 * i, 5.0) for i in range(9)]
               + [(12.0, 5.25 + 0.25 * i) for i in range(4)]
               + [(12.0 + 0.25 * i, 6.0) for i in range(1, 9)]
               + [(14.0, 5.75 - 0.25 * i) for i in range(4)])
    routes = [
        seg("n1-S01", "F.Cu", line(2.0, 6.0, 5.0), ["p1", "n1-V01"]),
        seg("n1-S02", "B.Cu", line(6.0, 10.0, 5.0),
            ["n1-V01", "n1-V02"], parent="n1-S01"),
        seg("n1-S03", "In1.Cu", s03_pts, ["n1-V02", "n1-V03"],
            parent="n1-S02"),
        seg("n1-S04", "B.Cu", line(14.0, 18.0, 5.0),
            ["n1-V03", "p2"], parent="n1-S03"),
        {"route_id": "n2-S01", "net_id": "n2", "layer": "F.Cu",
         "width_mm": 0.3,
         "polyline_mm": [[round(x, 2), round(y, 2)] for (x, y) in n2_pts],
         "endpoint_ids": ["q1", "q2"], "parent_id": None,
         "state": "candidate", "source": "solver"},
    ]
    vias = [
        via("n1-V01", "n1-S01", "F.Cu", "B.Cu", 6.0),
        via("n1-V02", "n1-S02", "B.Cu", "In1.Cu", 10.0),
        via("n1-V03", "n1-S03", "In1.Cu", "B.Cu", 14.0),
    ]
    return sid, board, {"routes": routes, "vias": vias}


def _proposal_key2(patch):
    return (patch.get("action_type"), str(patch.get("route_id")),
            str(patch.get("via_id")), str(patch.get("merge_with_route_id")),
            str(patch.get("keep_layer")), str(patch.get("layer")),
            str(patch.get("to_layer")), str(patch.get("via_mm")),
            str(patch.get("split_mm")))


def _concat_bend_objective(world, routes, vias):
    """防 artifact 守卫口径：bend 按逐网拼接链计数（对段拆并不变）。

    cmp_metrics（v4exp 冻结口径）bend 按段内计数——段边界处的方向变化
    不计 bend。split_segment 把拐点变成段边界即"消失"一个 bend（-0.5），
    属度量 artifact 非真实改善；本口径在拼接链上数 bend，拆/并段下不变，
    用于精化接受守卫（DEV-E3-001）。
    """
    from ..v4exp.cmp_patch import _expanded_route, _route_bends
    per_net = {}
    for r in routes:
        nid = _route_net(r)
        per_net.setdefault(nid, []).append(r)
    bend_count = 0
    for nid, segs in per_net.items():
        segs = sorted(segs, key=lambda r: _seg_order_key(str(r.get("route_id", ""))))
        pts = []
        for s in segs:
            cells = _expanded_route(world, s)
            if not cells:
                return None
            for c in cells:
                if not pts or pts[-1] != c:
                    pts.append(c)
        bend_count += len(_route_bends(pts))
    m = cmp_metrics(world, routes, vias)
    if m["objective"] == 0.0 and m["shorts"] == 1 and m["unconnected"] == 1 \
            and not routes:
        return None  # invalid_metrics 哨兵
    return (m["total_length_mm"] + 8.0 * len(vias) + 0.5 * bend_count)


def refine_v2(world, board, run, max_proposals=32):
    """v2 动作精化环（A1 同构：评估预算内贪心、严格改善才接受）。

    接受判据（DEV-E3-001 守卫后）：cmp_metrics 冻结 objective 严格下降
    **且** 拼接链口径 objective（_concat_bend_objective）同步严格下降
    ——段拆并类动作借"段边界 bend 不计"度量 artifact 刷出的假改善被
    守卫拦截；G3.2 配对不劣化的结构性根不变（接受只会真改善）。
    """
    import copy as _copy
    best = {"routes": _copy.deepcopy(run.get("routes", [])),
            "vias": _copy.deepcopy(run.get("vias", []))}
    base_metrics = cmp_metrics(world, best["routes"], best["vias"])
    best_metrics = dict(base_metrics)
    best_guard = _concat_bend_objective(world, best["routes"], best["vias"])
    proposals = []
    accepted = 0
    if run.get("status") != "sat" or best_guard is None:
        return {"arm": "E3-refine-v2", "evaluations": 0, "accepted_count": 0,
                "base_metrics": base_metrics, "final_metrics": best_metrics,
                "final_geom": best,
                "note": "非 sat 求解不精化（unsat/failed 场景）"}
    tried = set()
    improved = True
    while improved and len(proposals) < max_proposals:
        improved = False
        for patch in v2_proposal_stream(world, board, best):
            if len(proposals) >= max_proposals:
                break
            key = _proposal_key2(patch)
            if key in tried:
                continue
            tried.add(key)
            res = validate_patch2(world, board, patch, best)
            record = {
                "seq": len(proposals),
                "action_type": patch["action_type"],
                "object_id": str(patch.get("via_id")
                                 or patch.get("route_id")),
                "legal": bool(res.get("legal")),
                "reasons": list(res.get("reasons", [])),
                "accepted": False,
            }
            if res.get("legal") and not res.get("noop"):
                applied = apply_and_check2(world, board, patch, best)
                if applied.get("legal"):
                    cand = applied["geometry"]
                    cand_metrics = cmp_metrics(world, cand["routes"],
                                               cand["vias"])
                    cand_guard = _concat_bend_objective(
                        world, cand["routes"], cand["vias"])
                    record["candidate_objective"] = cand_metrics["objective"]
                    if (cand_guard is not None
                            and cand_metrics["objective"]
                            < best_metrics["objective"]
                            and cand_guard < best_guard):
                        best = cand
                        best_metrics = cand_metrics
                        best_guard = cand_guard
                        accepted += 1
                        record["accepted"] = True
                        record["candidate_geometry_sha256"] = \
                            candidate_geometry_sha256(cand)
                        improved = True
            proposals.append(record)
            if improved:
                break
    return {
        "arm": "E3-refine-v2",
        "base_geometry_sha256": candidate_geometry_sha256(
            {"routes": run.get("routes", []),
             "vias": run.get("vias", [])}),
        "final_geometry_sha256": candidate_geometry_sha256(best),
        "evaluations": len(proposals),
        "accepted_count": accepted,
        "base_metrics": base_metrics,
        "final_metrics": best_metrics,
        "final_geom": best,
        "proposals": proposals,
    }


# ---------------------------------------------------------------- G3.1 台账

NEG_KINDS = ("stale_base_hash", "unknown_object_id", "endpoint_chain_break",
             "layer_illegal", "unknown_key_injection", "off_grid_coord",
             "identity_mismatch", "post_check_collision", "nan_coord")


def _mutate_v2(patch, kind, world, board, geom):
    """新动作负向突变（P1 九类同族映射；结构不适用返回 None）。"""
    p = copy.deepcopy(patch)
    routes = geom["routes"]
    other_route = next((r for r in routes
                        if str(r.get("route_id")) != str(p.get("route_id"))
                        and str(r.get("route_id")) != str(p.get(
                            "merge_with_route_id"))), None)
    other_net = next((str(n.get("net_id")) for n in board.get("nets", [])
                      if str(n.get("net_id")) != str(p.get("net_id"))), None)
    at = p["action_type"]
    if kind == "stale_base_hash":
        p["base_candidate_geometry_sha256"] = "0" * 64
    elif kind == "unknown_object_id":
        if at == DELETE_VIA:
            p["via_id"] = "n9-V99"
        elif at == MERGE_SEGMENTS:
            p["merge_with_route_id"] = "n9-S99"
        else:
            p["route_id"] = "n9-S99"
    elif kind == "endpoint_chain_break":
        p["fixed_endpoint_ids"] = list(reversed(p["fixed_endpoint_ids"]))
    elif kind == "layer_illegal":
        if at == DELETE_VIA:
            stack = list(world.layers)
            pair = {str(p.get("keep_layer"))}
            cand = [l for l in stack if l not in pair]
            if not cand:
                return None
            p["keep_layer"] = sorted(cand)[0]
        elif at == INSERT_VIA:
            p["to_layer"] = str(p.get("layer"))
        elif at == REORDER_LAYERS:
            p["layer"] = "Edge.Cuts"
        elif at == MERGE_SEGMENTS:
            # 跨层并段：把 merge 指到同网异层段（若唯一相邻段同层则跳过）
            nid = str(p.get("net_id"))
            cand = [r for r in routes
                    if _route_net(r) == nid
                    and str(r.get("route_id")) != str(p.get("route_id"))
                    and str(r.get("route_id"))
                    != str(p.get("merge_with_route_id"))
                    and str(r.get("layer")) != str(
                        next((x.get("layer") for x in routes
                              if str(x.get("route_id"))
                              == str(p.get("route_id"))), None))]
            if not cand:
                return None
            p["merge_with_route_id"] = str(sorted(
                cand, key=lambda r: str(r.get("route_id")))[0]["route_id"])
        else:
            return None
    elif kind == "unknown_key_injection":
        p["width_mm"] = 0.99
    elif kind == "off_grid_coord":
        if at == INSERT_VIA:
            p["via_mm"] = [float(p["via_mm"][0]) + 0.1, float(p["via_mm"][1])]
        elif at == SPLIT_SEGMENT:
            p["split_mm"] = [float(p["split_mm"][0]) + 0.1,
                             float(p["split_mm"][1])]
        else:
            return None
    elif kind == "identity_mismatch":
        if other_route is None:
            return None
        p["fixed_endpoint_ids"] = [str(x) for x in
                                   other_route["endpoint_ids"]]
    elif kind == "post_check_collision":
        return None  # 由专用探针补（见 negative_set_probe）
    elif kind == "nan_coord":
        if at == INSERT_VIA:
            p["via_mm"] = [float("nan"), float(p["via_mm"][1])]
        elif at == SPLIT_SEGMENT:
            p["split_mm"] = [float(p["split_mm"][0]), float("nan")]
        else:
            return None
    else:
        raise ValueError("unknown mutation %s" % kind)
    return p


def _first_legal_patch(world, board, geom, action_type, max_scan=400):
    """确定性找一个合法 v2 patch（含 apply 检查）供突变基准。"""
    scanned = 0
    for patch in v2_proposal_stream(world, board, geom):
        if patch["action_type"] != action_type:
            continue
        scanned += 1
        if scanned > max_scan:
            return None
        res = validate_patch2(world, board, patch, geom)
        if res.get("legal") and not res.get("noop"):
            return patch
    return None


def build_negative_set(bases, max_scan=400):
    """G3.1 台账：bases=[(scenario_id, board, geom)]；返回 records+summary。

    post_check_collision 探针：对 insert_via/reorder_layers/delete_via
    枚举变体（to_layer/keep_layer 各候选），取 post-check 拒绝的首个；
    无则跳过（如实计数）。
    """
    records = []
    for sid, board, geom in bases:
        world = GridWorld(board)
        stack = list(world.layers)
        for at in NEW_ACTION_TYPES:
            base_geom = geom
            if at == MERGE_SEGMENTS:
                # merge 需先有 joint：确定性应用一个合法 split
                split_patch = _first_legal_patch(world, board, geom,
                                                 SPLIT_SEGMENT, max_scan)
                if split_patch is None:
                    continue
                applied = apply_and_check2(world, board, split_patch, geom)
                if not applied.get("legal"):
                    continue
                base_geom = applied["geometry"]
            valid = _first_legal_patch(world, board, base_geom, at, max_scan)
            if valid is None:
                records.append({
                    "scenario_id": sid, "action_type": at,
                    "valid_patch_found": False, "mutations": [],
                })
                continue
            # 合法基准（正方向证据）
            pos = validate_patch2(world, board, valid, base_geom)
            pos_applied = apply_and_check2(world, board, valid, base_geom)
            restored = rollback2(pos_applied["geometry"],
                                 pos_applied["rollback"]) \
                if pos_applied.get("legal") else None
            entry = {
                "scenario_id": sid, "action_type": at,
                "valid_patch_found": True,
                "valid_patch_action": valid,
                "valid_legal": bool(pos.get("legal")),
                "rollback_byte_equal": bool(
                    pos_applied.get("legal") and restored is not None
                    and candidate_geometry_sha256(restored)
                    == candidate_geometry_sha256(base_geom)),
                "mutations": [],
            }
            for kind in NEG_KINDS:
                if kind == "post_check_collision":
                    muts = _collision_probe(world, board, valid, base_geom,
                                            stack)
                    if not muts:
                        entry["mutations"].append({
                            "mutation": kind, "applicable": False})
                        continue
                    for mut in muts:
                        res = validate_patch2(world, board, mut, base_geom)
                        entry["mutations"].append({
                            "mutation": kind, "applicable": True,
                            "blocked": not res["legal"],
                            "reasons": res["reasons"]})
                    continue
                mut = _mutate_v2(valid, kind, world, board, base_geom)
                if mut is None:
                    entry["mutations"].append({
                        "mutation": kind, "applicable": False})
                    continue
                res = validate_patch2(world, board, mut, base_geom)
                entry["mutations"].append({
                    "mutation": kind, "applicable": True,
                    "blocked": not res["legal"], "reasons": res["reasons"]})
            records.append(entry)
    total = sum(1 for e in records for m in e["mutations"]
                if m.get("applicable"))
    blocked = sum(1 for e in records for m in e["mutations"]
                  if m.get("applicable") and m.get("blocked"))
    valid_pos = [e for e in records if e.get("valid_patch_found")]
    return {
        "schema": "pcbflow.v4_1.e3-negative-set/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": _PREREG_SHA256,
        "mutation_kinds": list(NEG_KINDS),
        "records": records,
        "summary": {
            "action_types": list(NEW_ACTION_TYPES),
            "valid_patch_cases": len(valid_pos),
            "mutations_total": total,
            "mutations_blocked": blocked,
            "g31_scale_ge_81": total >= 81,
            "g31_all_intercepted": total > 0 and blocked == total,
            "positive_all_legal": all(e.get("valid_legal")
                                      for e in valid_pos),
            "positive_rollback_all_byte_equal": all(
                e.get("rollback_byte_equal") for e in valid_pos),
        },
    }


def _collision_probe(world, board, valid, base_geom, stack):
    """post_check_collision 探针：枚举层变体取 post-check 拒绝者（≤4 个）。"""
    at = valid["action_type"]
    out = []
    if at == INSERT_VIA:
        for to_layer in sorted(stack):
            if to_layer == str(valid.get("layer")):
                continue
            mut = copy.deepcopy(valid)
            mut["to_layer"] = to_layer
            res = validate_patch2(world, board, mut, base_geom)
            if not res["legal"] and any("violations" in r or "劣化" in r
                                        for r in res.get("reasons", [])):
                out.append(mut)
            if len(out) >= 2:
                break
    elif at == REORDER_LAYERS:
        for new_layer in sorted(stack):
            if new_layer == str(valid.get("layer")):
                continue
            mut = copy.deepcopy(valid)
            mut["layer"] = new_layer
            res = validate_patch2(world, board, mut, base_geom)
            if not res["legal"] and any("violations" in r or "劣化" in r
                                        for r in res.get("reasons", [])):
                out.append(mut)
            if len(out) >= 2:
                break
    elif at == DELETE_VIA:
        for keep in sorted(stack):
            mut = copy.deepcopy(valid)
            mut["keep_layer"] = keep
            res = validate_patch2(world, board, mut, base_geom)
            if not res["legal"] and any("violations" in r or "劣化" in r
                                        for r in res.get("reasons", [])):
                out.append(mut)
            if len(out) >= 2:
                break
    return out


# ---------------------------------------------------------------- P1 重放

def replay_p1(root):
    """P1 12 用例在 patch 合同 v2 下的重放（只读重生成；零回写）。"""
    from ..v4exp import cmp_run
    cases = cmp_run.p1_cases(root, cmp_run.P1_SIDS)
    entries = []
    for case in cases:
        sid = case["scenario_id"]
        board = cmp_run.read_board(root, sid)
        run = cmp_run.baseline_run(board)
        geom = cmp_patch.geom_from_run(run)
        world = GridWorld(board)
        base_hash = candidate_geometry_sha256(geom)
        found = cmp_run._program_patch(world, board, geom, case, base_hash)
        if found is None:
            reject = cmp_run._reject_patch(case, geom, board, base_hash)
            res = validate_patch2(world, board, reject, geom)
            entries.append({
                "case_id": case["case_id"], "scenario_id": sid,
                "program_action": "reject_route_patch",
                "unmutated_accepted_v2": bool(res["legal"]),
                "mutations": [],
            })
            continue
        patch = found[0]
        res = validate_patch2(world, board, patch, geom)
        muts = []
        for kind in cmp_run.MUTATIONS:
            mut = cmp_run._mutate(patch, kind, world, board, geom)
            if mut is None:
                continue
            r2 = validate_patch2(world, board, mut, geom)
            muts.append({"mutation": kind, "blocked": not r2["legal"],
                         "reasons": r2["reasons"]})
        entries.append({
            "case_id": case["case_id"], "scenario_id": sid,
            "program_action": patch["action_type"],
            "unmutated_accepted_v2": bool(res["legal"]),
            "mutations": muts,
        })
    total = sum(len(e["mutations"]) for e in entries)
    blocked = sum(1 for e in entries for m in e["mutations"] if m["blocked"])
    accepted = sum(1 for e in entries if e["unmutated_accepted_v2"])
    return {
        "schema": "pcbflow.v4_1.e3-p1-replay/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": _PREREG_SHA256,
        "source": "out/v4-comparative-experiment（板快照只读重生成；"
                  "历史产物零回写）",
        "sids": list(cmp_run.P1_SIDS),
        "entries": entries,
        "summary": {
            "program_acceptance_v2": "%d/%d" % (accepted, len(entries)),
            "v1_mutations_total": total,
            "v1_mutations_blocked_v2": blocked,
            "backward_compat_81_of_81": total == 81 and blocked == 81,
            "program_acceptance_all": accepted == len(entries),
        },
    }


# ---------------------------------------------------------------- CLI

def _ml_bases(sids):
    from .mlfamily import generate_ml_scenario
    from .mlchain import mlboard_to_v4exp_board
    from .solver2 import solve_board2
    bases = []
    for sid in sids:
        board = mlboard_to_v4exp_board(generate_ml_scenario(sid))
        run = solve_board2(board, {"route_order": sorted(
            str(n["net_id"]) for n in board["nets"]), "group": "E3-NEG"})
        if run["status"] != "sat" or not run["vias"]:
            continue
        bases.append((sid, board,
                      {"routes": run["routes"], "vias": run["vias"]}))
    return bases


def main(argv=None):
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.action2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--root", default=".")
    ns = ap.parse_args(argv)
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)

    bases = _ml_bases(["dev-f9-01", "dev-f9-02", "dev-f9-03",
                       "dev-f10-01", "dev-f10-02", "dev-f10-03"])
    bases.append(synthetic_chain_base())
    neg = build_negative_set(bases)
    write_canonical_json(out / "negative-set-v2.json", neg)
    s = neg["summary"]
    print("negative-set-v2: valid=%d cases, mutations=%d, blocked=%d, "
          "scale>=81=%s, all_intercepted=%s"
          % (s["valid_patch_cases"], s["mutations_total"],
             s["mutations_blocked"], s["g31_scale_ge_81"],
             s["g31_all_intercepted"]))

    replay = replay_p1(ns.root + "/out/v4-comparative-experiment")
    write_canonical_json(out / "p1-replay-v1.json", replay)
    r = replay["summary"]
    print("p1-replay-v1: program acceptance %s, v1 mutations %d blocked %d, "
          "81/81=%s" % (r["program_acceptance_v2"], r["v1_mutations_total"],
                        r["v1_mutations_blocked_v2"],
                        r["backward_compat_81_of_81"]))
    ok = (s["g31_scale_ge_81"] and s["g31_all_intercepted"]
          and s["positive_all_legal"] and s["positive_rollback_all_byte_equal"]
          and r["backward_compat_81_of_81"] and r["program_acceptance_all"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
