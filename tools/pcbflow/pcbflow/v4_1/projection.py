"""pcbflow.v4_1.projection -- manifest 直读投影（E5，堵 K5）。

载体格式与 planner 输入格式分离：SVG 保留 canonical 载体地位不进模型输入；
本模块从 board/route manifest（pcbflow.v4exp.board/1 板快照 + solver 候选
几何）直接读取并构造**结构化坐标视图**给 planner：

- 对象表：pads（坐标/尺寸/层/所属 net）、keepouts（矩形/层）、nets
  （类/端点/派生跨度摘要）、relations（关系摘要）；
- 候选几何（可选）：routes/vias 的 manifest 原字段，板 mm 坐标系**零换算**
  （对比先例 SVG 臂的 +2.0mm 渲染边距帧换算——K5 摩擦源）；
- 零泄露：不含 label/family/split/seed（planner 盲化）；
- 确定性：同输入同输出字节（排序与 canonical 序固化；确定性测试看护）。

只读依赖：pcbflow.v4exp.cmp_inputs.enrich_reference（候选几何身份字段
补齐，先例冻结语义零改动）；本模块零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

from .canonical import dumps_canonical
from ..v4exp import cmp_inputs

PROJECTION_SCHEMA = "pcbflow.v4_1.projection/1"

COORDINATE_FRAME = {
    "note": "坐标值与 board/route manifest 原值逐字节一致，零换算零边距",
    "origin": "bottom-left",
    "system": "board_mm",
    "units": "mm",
    "y_axis": "down-positive",
}

_ROUTE_FIELDS = ("route_id", "net_id", "relation_ids", "line_type",
                 "parent_id", "layer", "width_mm", "polyline_mm",
                 "endpoint_ids", "state", "source")
_VIA_FIELDS = ("via_id", "net_id", "parent_id", "from_layer", "to_layer",
               "center_mm", "state", "source")


def _span_summary(board: dict, net: dict) -> dict:
    """net 两端点的确定性派生摘要（坐标、位移、直线距离）。"""
    pads = {str(p["pad_id"]): p for p in board.get("pads", [])}
    eps = []
    for pid in net.get("endpoints", []):
        p = pads.get(str(pid))
        if p is None:
            return {"endpoint_objects": None}
        eps.append({"pad_id": str(pid), "x_mm": p["x_mm"], "y_mm": p["y_mm"],
                    "layer": str(p["layer"])})
    a, b = eps[0], eps[1]
    dx = round(float(b["x_mm"]) - float(a["x_mm"]), 3)
    dy = round(float(b["y_mm"]) - float(a["y_mm"]), 3)
    return {"dx_mm": dx, "dy_mm": dy,
            "straight_line_mm": round((dx * dx + dy * dy) ** 0.5, 3),
            "endpoint_objects": eps}


def build_projection(board: dict, candidate_geometry: dict | None = None) -> dict:
    """board manifest（+可选候选几何）→ 结构化坐标视图投影。

    确定性：pads 按 pad_id、nets 按 net_id、keepouts 按 keepout_id、
    relations 按 relation_id、routes 按 (net_id, route_id)、vias 按
    (net_id, via_id) 排序；数值原样透传不重格式化。
    """
    if not isinstance(board, dict) or "scenario_id" not in board:
        raise ValueError("board manifest 缺失或非法")

    pads = sorted(board.get("pads", []),
                  key=lambda p: str(p.get("pad_id")))
    nets = []
    for n in sorted(board.get("nets", []),
                    key=lambda n: str(n.get("net_id"))):
        nets.append({
            "net_id": str(n["net_id"]),
            "net_class": str(n.get("net_class")),
            "endpoints": [str(e) for e in n.get("endpoints", [])],
            "span_summary": _span_summary(board, n),
        })
    keepouts = sorted(board.get("keepouts", []),
                      key=lambda k: str(k.get("keepout_id")))
    relations = sorted(board.get("relations", []),
                       key=lambda r: str(r.get("relation_id")))

    out = {
        "schema": PROJECTION_SCHEMA,
        "scenario_id": str(board["scenario_id"]),
        "coordinate_frame": dict(COORDINATE_FRAME),
        "board": {
            "bbox_mm": list(board["board"]["bbox_mm"]),
            "layers": list(board["board"]["layers"]),
        },
        "rules": _deep_copy(board.get("rules", {})),
        "pads": _deep_copy(pads),
        "nets": nets,
        "keepouts": _deep_copy(keepouts),
        "relations": _deep_copy(relations),
    }
    if candidate_geometry is not None:
        reference = cmp_inputs.enrich_reference(board, candidate_geometry)
        routes = sorted(reference.get("routes", []),
                        key=lambda r: (str(r.get("net_id")),
                                       str(r.get("route_id"))))
        vias = sorted(reference.get("vias", []),
                      key=lambda v: (str(v.get("net_id")),
                                     str(v.get("via_id"))))
        out["candidate_geometry"] = {
            "note": "solver 候选几何，坐标=板 mm（零换算）",
            "routes": [{k: _deep_copy(r.get(k)) for k in _ROUTE_FIELDS}
                       for r in routes],
            "vias": [{k: _deep_copy(v.get(k)) for k in _VIA_FIELDS}
                     for v in vias],
        }
    return out


def _deep_copy(value):
    import copy
    return copy.deepcopy(value)


def projection_canonical_bytes(projection: dict) -> bytes:
    """canonical 字节（确定性测试用：同输入同输出字节）。"""
    return dumps_canonical(projection).encode("utf-8")
