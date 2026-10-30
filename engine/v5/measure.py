# -*- coding: utf-8 -*-
"""候选测量（A4 度量权归引擎）：确定性成本核算。

成本模型参数化（V2 场景口径为默认）：
  cost = detour_rate × excess_len + direction_rate × wrong_dir_len
       + via_cost × transition_vias + return_cost × return_vias
- excess_len = 折线总长 − 两端点直线距离（欧氏）
- wrong_dir：按层优选方向（h 层计垂直段，v 层计水平段，any 层不计）
- 换层过渡孔配 1 回流孔（R4）：回流孔数 = 过渡孔数（P0 简化账，R4 几何核查在 P4 执行器）

候选携带 candidate provenance；本模块只测量不选择（终选在 L6）。
"""
import math

from . import canonical
from .drc import VERSION as DRC_VERSION

MEASURER_VERSION = "v5.measure/0.1.0"

DEFAULT_COST_MODEL = {
    "detour_rate": 0.5,
    "direction_rate": 0.2,
    "via_cost": 4.0,
    "return_cost": 1.0,
}


def polyline_length(pts):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def wrong_direction_length(pts, preferred_direction):
    """逆向长度：h 层计垂直段，v 层计水平段，any 层 0。"""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        if preferred_direction == "h":
            total += abs(y2 - y1)
        elif preferred_direction == "v":
            total += abs(x2 - x1)
    return total


def route_cost(route, layer_directions, cost_model=None):
    """单网成本。route: {"net_id", "layer", "polyline", "transition_vias"}。

    transition_vias 可省略：默认按 0（单层走线）。换层网由执行器给孔数，
    P0 黄金夹具按 V2 判分键口径显式给 2（进出走廊各一）。
    """
    cm = dict(DEFAULT_COST_MODEL)
    if cost_model:
        cm.update(cost_model)
    pts = route["polyline"]
    length = polyline_length(pts)
    straight = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
    excess = max(0.0, length - straight)
    direction = layer_directions.get(route["layer"], "any")
    wrong = wrong_direction_length(pts, direction)
    vias = float(route.get("transition_vias", 0))
    returns = vias  # R4：每过渡孔配 1 回流孔
    cost = (cm["detour_rate"] * excess + cm["direction_rate"] * wrong
            + cm["via_cost"] * vias + cm["return_cost"] * returns)
    return {
        "net_id": route["net_id"],
        "length_mm": round(length, 10),
        "straight_mm": round(straight, 10),
        "excess_mm": round(excess, 10),
        "wrong_direction_mm": round(wrong, 10),
        "transition_vias": int(vias),
        "return_vias": int(returns),
        "cost": round(cost, 10),
    }


def measure_assignment(routes, layer_directions, cost_model=None):
    """候选分配测量：逐网成本 + 总成本。确定性输出（按输入序，canonical 落盘）。"""
    per_net = [route_cost(r, layer_directions, cost_model) for r in routes]
    total = round(sum(r["cost"] for r in per_net), 10)
    return {
        "measurer_version": MEASURER_VERSION,
        "drc_version": DRC_VERSION,
        "per_net": per_net,
        "total_cost": total,
    }


def measure_assignment_bytes(routes, layer_directions, cost_model=None) -> bytes:
    return canonical.canonical_json(measure_assignment(routes, layer_directions, cost_model))
