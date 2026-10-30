"""V4exp SVG + route-manifest 生成（data-pcbflow-schema="v4-svg-route-1"）。

坐标合同：不翻转不镜像，sx = x_mm - (xmin - M)、sy = y_mm - (ymin - M)，
M = 2.0mm；viewBox 从 "0 0" 起，W/H = bbox 宽高 + 2M；数值一律 6 位小数。
颜色只是可视化编码（class + 图例），机器事实全在 data-* 属性。

manifest：schema_version "v4-route-manifest-1"；manifest_payload_sha256 =
对整对象按合同规则（canonical、递归剔除 *_sha256 键，含该键本身与
board_snapshot_sha256）的 sha256，同时写进 SVG 根节点
data-route-manifest-sha256。

多层段拆分在 ref_route 已完成（换层处断成两个 route，via parent 取换层前
那段）；本模块只做合同序列化。f5 等 reference_unrouted 场景 routes 为空
时照样出 SVG（board+pads+keepout+图例）。

stdin 收 {"board_path": "...", "ref_routes_path": "...", "out_dir": "..."}；
写 route-manifest-<sid>.json + route-preview-<sid>.svg。零 argv。
"""

from __future__ import annotations

import os

from . import model
from .model import (Board, LEGEND_VERSION, MARGIN_MM, SVG_COORD_SYSTEM,
                    SVG_SCHEMA, SVG_Y_AXIS, fmt3, fmt6)

# 图例配色（颜色仅图例/渲染编码，不承载机器事实）
LEGEND_COLORS = {
    "signal": "#3B82F6", "clock": "#F97316", "bus_trunk": "#22C55E",
    "bus_member": "#06B6D4"}
VIA_COLOR = "#111111"
PAD_FILL = "#9CA3AF"
KEEPOUT_COLOR = "#111111"
BOARD_EDGE_COLOR = "#111111"


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_manifest(board: Board, ref: dict) -> dict:
    manifest = {
        "schema_version": model.MANIFEST_SCHEMA_VERSION,
        "scenario_id": board.scenario_id,
        "board_snapshot_sha256": model.sha256_of(board.to_obj()),
        "svg_coordinate_system": SVG_COORD_SYSTEM,
        "legend_version": LEGEND_VERSION,
        "rules": board.rules.to_obj(),
        "relations": [r.to_obj() for r in board.relations],
        "routes": ref["routes"],
        "vias": ref["vias"]}
    manifest["manifest_payload_sha256"] = model.sha256_of(manifest)
    return manifest


def _style_block() -> str:
    return (
        "  <style>\n"
        "    .route{fill:none;stroke-linecap:square;stroke-linejoin:miter}\n"
        "    .route-baseline{stroke-width:0.3}\n"
        "    .route-signal{stroke:" + LEGEND_COLORS["signal"] + "}\n"
        "    .route-clock{stroke:" + LEGEND_COLORS["clock"] + "}\n"
        "    .route-bus_trunk{stroke:" + LEGEND_COLORS["bus_trunk"] + "}\n"
        "    .route-bus_member{stroke:" + LEGEND_COLORS["bus_member"] + "}\n"
        "    .layer-BCu{stroke-dasharray:1.2 0.6}\n"
        "    .via{fill:none;stroke:" + VIA_COLOR + ";stroke-width:0.12}\n"
        "    .pad{fill:" + PAD_FILL + ";stroke:#4B5563;stroke-width:0.08}\n"
        "    .keepout{fill:none;stroke:" + KEEPOUT_COLOR
        + ";stroke-width:0.1;stroke-dasharray:0.8 0.4}\n"
        "    .board-edge{fill:#FFFFFF;stroke:" + BOARD_EDGE_COLOR
        + ";stroke-width:0.15}\n"
        "    .legend-label{font-size:1.4px;fill:#111111}\n"
        "  </style>\n")


def _class_of(route: dict) -> str:
    layer = "F" if route["layer"] == "F.Cu" else "B"
    return (f"route route-{route['line_type']} route-{route['state']}"
            f" layer-{layer}Cu")


def _route_group(route: dict, sx, sy) -> str:
    d = "M " + " L ".join(f"{fmt6(p[0] - sx)} {fmt6(p[1] - sy)}"
                          for p in route["polyline_mm"])
    lines = [
        f'<g id="route-{_esc(route["route_id"])}"'
        f' data-object-kind="route_segment"'
        f' data-route-id="{_esc(route["route_id"])}"'
        f' data-net-id="{_esc(route["net_id"])}"'
        f' data-relation-id="{_esc(" ".join(route["relation_ids"]))}"'
        f' data-line-type="{route["line_type"]}" data-parent-id=""',
        f'     data-layer="{route["layer"]}"'
        f' data-width-mm="{fmt3(route["width_mm"])}"'
        f' data-state="{route["state"]}" data-source="{route["source"]}"',
        f'     data-endpoint-start="{_esc(route["endpoint_ids"][0])}"'
        f' data-endpoint-end="{_esc(route["endpoint_ids"][1])}"'
        f' data-constraint-refs="{_esc(",".join(route["constraint_refs"]))}">',
        f'  <path id="geom-{_esc(route["route_id"])}" d="{d}"'
        f' class="{_class_of(route)}"/>',
        "</g>"]
    return "\n".join(lines)


def _via_circle(via: dict, sx, sy) -> str:
    cx, cy = via["center_mm"][0] - sx, via["center_mm"][1] - sy
    r = via["drill_mm"] / 2 + via["annular_ring_mm"]
    return (
        f'<circle id="via-{_esc(via["via_id"])}" data-object-kind="via"'
        f' data-via-id="{_esc(via["via_id"])}"'
        f' data-net-id="{_esc(via["net_id"])}"'
        f' data-parent-id="{_esc(via["parent_id"])}"'
        f' data-from-layer="{via["from_layer"]}"'
        f' data-to-layer="{via["to_layer"]}"'
        f' data-drill-mm="{fmt3(via["drill_mm"])}"'
        f' data-annular-ring-mm="{fmt3(via["annular_ring_mm"])}"'
        f' cx="{fmt6(cx)}" cy="{fmt6(cy)}" r="{fmt6(r)}"/>')


def _legend(sx, sy, w, h) -> str:
    rows = [("line-signal", "signal"), ("line-clock", "clock"),
            ("line-bus_trunk", "bus_trunk"), ("line-bus_member", "bus_member"),
            ("via", "via"), ("pad", "pad"), ("keepout", "keepout")]
    x0, y0 = w - 14.0, 1.6
    out = [f'<g id="legend" data-legend-version="{LEGEND_VERSION}">',
           f'  <rect x="{fmt6(x0 - 0.8)}" y="{fmt6(y0 - 1.0)}"'
           f' width="13.0" height="{fmt6(1.9 * len(rows) + 1.2)}"'
           f' fill="#FFFFFF" fill-opacity="0.85"'
           f' stroke="#111111" stroke-width="0.08"/>']
    for i, (kind, label) in enumerate(rows):
        cy = y0 + 1.9 * i
        sw = f'  <g id="legend-item-{kind}">'
        if kind.startswith("line-"):
            lt = kind[5:]
            sw += (f'<line x1="{fmt6(x0)}" y1="{fmt6(cy)}"'
                   f' x2="{fmt6(x0 + 3.0)}" y2="{fmt6(cy)}"'
                   f' stroke="{LEGEND_COLORS[lt]}" stroke-width="0.4"/>')
        elif kind == "via":
            sw += (f'<circle cx="{fmt6(x0 + 1.5)}" cy="{fmt6(cy)}" r="0.5"'
                   f' fill="none" stroke="{VIA_COLOR}" stroke-width="0.16"/>')
        elif kind == "pad":
            sw += (f'<rect x="{fmt6(x0)}" y="{fmt6(cy - 0.5)}" width="1.6"'
                   f' height="1.0" fill="{PAD_FILL}"/>')
        else:
            sw += (f'<rect x="{fmt6(x0)}" y="{fmt6(cy - 0.5)}" width="1.6"'
                   f' height="1.0" fill="none" stroke="{KEEPOUT_COLOR}"'
                   f' stroke-width="0.12" stroke-dasharray="0.5 0.3"/>')
        sw += (f'<text x="{fmt6(x0 + 4.0)}" y="{fmt6(cy + 0.5)}"'
               f' class="legend-label">{label}</text></g>')
        out.append(sw)
    out.append("</g>")
    return "\n".join(out)


def build_svg(board: Board, manifest: dict) -> str:
    x0, y0, x1, y1 = board.bbox_mm
    sx, sy = x0 - MARGIN_MM, y0 - MARGIN_MM
    w, h = (x1 - x0) + 2 * MARGIN_MM, (y1 - y0) + 2 * MARGIN_MM
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"'
             f' data-pcbflow-schema="{SVG_SCHEMA}"'
             ' data-board-snapshot-sha256="'
             + manifest["board_snapshot_sha256"] + '"'
             ' data-route-manifest-sha256="'
             + manifest["manifest_payload_sha256"] + '"'
             f' data-coordinate-system="{SVG_COORD_SYSTEM}"'
             f' data-y-axis="{SVG_Y_AXIS}"'
             f' viewBox="0 0 {fmt6(w)} {fmt6(h)}"'
             ' preserveAspectRatio="xMidYMid meet">',
             '  <title id="board-title">' + _esc(board.scenario_id)
             + '</title>']
    parts.append(_style_block().rstrip("\n"))
    parts.append(
        f'  <rect id="board-edge" data-object-kind="board_edge"'
        f' x="{fmt6(0.0)}" y="{fmt6(0.0)}" width="{fmt6(w)}"'
        f' height="{fmt6(h)}" class="board-edge"/>')
    for k in board.keepouts:
        rx, ry = k.rect_mm[0] - sx, k.rect_mm[1] - sy
        rw = k.rect_mm[2] - k.rect_mm[0]
        rh = k.rect_mm[3] - k.rect_mm[1]
        parts.append(
            f'  <rect id="keepout-{_esc(k.keepout_id)}"'
            f' data-object-kind="keepout"'
            f' data-keepout-id="{_esc(k.keepout_id)}"'
            f' data-layers="{" ".join(k.layers)}"'
            f' x="{fmt6(rx)}" y="{fmt6(ry)}" width="{fmt6(rw)}"'
            f' height="{fmt6(rh)}" class="keepout"/>')
    for p in board.pads:
        px, py = p.x_mm - p.w_mm / 2 - sx, p.y_mm - p.h_mm / 2 - sy
        parts.append(
            f'  <rect id="pad-{_esc(p.pad_id)}" data-object-kind="pad"'
            f' data-pad-id="{_esc(p.pad_id)}"'
            f' data-net-id="{_esc(p.net_id)}" data-layer="{p.layer}"'
            f' x="{fmt6(px)}" y="{fmt6(py)}" width="{fmt6(p.w_mm)}"'
            f' height="{fmt6(p.h_mm)}" class="pad"/>')
    for r in board.relations:
        parts.append(
            f'  <g id="relation-{_esc(r.relation_id)}"'
            f' data-object-kind="route_relation"'
            f' data-relation-id="{_esc(r.relation_id)}"'
            f' data-relation-type="{r.relation_type}"'
            f' data-member-ids="{_esc(" ".join(r.members))}"></g>')
    for route in manifest["routes"]:
        parts.append("  " + _route_group(route, sx, sy).replace("\n",
                                                                "\n  "))
    for via in manifest["vias"]:
        parts.append("  " + _via_circle(via, sx, sy))
    parts.append("  " + _legend(sx, sy, w, h).replace("\n", "\n  "))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build(board: Board, ref: dict) -> tuple:
    """返回 (manifest_obj, svg_text)。纯函数，无副作用。"""
    manifest = build_manifest(board, ref)
    return manifest, build_svg(board, manifest)


def main() -> None:
    import json as _json
    import sys
    cfg = model.read_stdin_json()
    board = model.board_from_obj(model.read_json(cfg["board_path"]))
    ref = model.read_json(cfg["ref_routes_path"])
    if ref["scenario_id"] != board.scenario_id:
        raise ValueError("ref-routes 与 board 的 scenario_id 不一致")
    manifest, svg = build(board, ref)
    out_dir = cfg.get("out_dir") or "out/v4-experiment"
    os.makedirs(out_dir, exist_ok=True)
    mpath = os.path.join(out_dir,
                         f"route-manifest-{board.scenario_id}.json")
    spath = os.path.join(out_dir,
                         f"route-preview-{board.scenario_id}.svg")
    model.write_json(mpath, manifest)
    with open(spath, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    sys.stdout.write(_json.dumps(
        {"scenario_id": board.scenario_id,
         "manifest": mpath.replace("\\", "/"),
         "svg": spath.replace("\\", "/"),
         "routes": len(manifest["routes"]), "vias": len(manifest["vias"])},
        sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
