"""V4exp PNG 渲染（PIL）：board + ref-routes + manifest -> route-preview-<sid>-<WxH>.png。

四个分辨率：1200x675、1568x872、1600x900、2400x1350；
fit-inside（等比、xMidYMid meet 语义）+ 每边 >= 20px 留白。
配色与 SVG 图例一致（signal 蓝 #3B82F6、clock 橙 #F97316、bus_trunk 绿
#22C55E、bus_member 青蓝 #06B6D4、via 黑圈、pad 灰、keepout 黑虚线框）。
内容：board edge、keepout 虚线、pad、route、via、每条 route 中点旁
route_id 标签、图例框、左上角 scenario_id、右下角 mm 比例尺。

确定性：PIL 默认渲染确定；不写任何时间戳/元数据；同输入两张 PNG
逐字节一致。stdin 收 {"board_path","ref_routes_path","manifest_path",
"out_dir"}（相对路径）。零 argv。
"""

from __future__ import annotations

import os

from . import model
from .model import Board, fmt3

RESOLUTIONS = [(1200, 675), (1568, 872), (1600, 900), (2400, 1350)]
MARGIN_PX = 24

RGB = {
    "signal": (59, 130, 246), "clock": (249, 115, 22),
    "bus_trunk": (34, 197, 94), "bus_member": (6, 182, 212)}
VIA_RGB = (17, 17, 17)
PAD_FILL = (156, 163, 175)
PAD_EDGE = (75, 85, 99)
KEEPOUT_RGB = (17, 17, 17)
EDGE_RGB = (17, 17, 17)
TEXT_RGB = (17, 17, 17)
BG_RGB = (255, 255, 255)

SCALE_BAR_MM = 5.0


def _font(px: int):
    from PIL import ImageFont
    px = max(9, int(px))
    try:
        return ImageFont.load_default(size=px)
    except TypeError:
        return ImageFont.load_default()


def _text_xy(dr, xy, text, font, anchor="la"):
    dr.text(xy, text, fill=TEXT_RGB, font=font, anchor=anchor)


def _dashed_segment(dr, p0, p1, dash, gap, color, width):
    import math
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        a = (p0[0] + ux * pos, p0[1] + uy * pos)
        b = (p0[0] + ux * end, p0[1] + uy * end)
        dr.line([a, b], fill=color, width=width)
        pos = end + gap


def _dashed_rect(dr, box, dash, gap, color, width):
    x0, y0, x1, y1 = box
    _dashed_segment(dr, (x0, y0), (x1, y0), dash, gap, color, width)
    _dashed_segment(dr, (x1, y0), (x1, y1), dash, gap, color, width)
    _dashed_segment(dr, (x1, y1), (x0, y1), dash, gap, color, width)
    _dashed_segment(dr, (x0, y1), (x0, y0), dash, gap, color, width)


def _polyline_midpoint(points):
    """按折线弧长取中点（mm 坐标）。"""
    import math
    total = 0.0
    segs = []
    for a, b in zip(points, points[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, d))
        total += d
    if total <= 0:
        return points[0]
    half = total / 2
    for a, b, d in segs:
        if half <= d:
            t = half / d if d else 0.0
            return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
        half -= d
    return points[-1]


def render(board: Board, ref: dict, manifest: dict, width: int, height: int):
    """渲染单张 PNG 图像（返回 PIL Image，不落盘）。纯函数。"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, height), BG_RGB)
    dr = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = board.bbox_mm
    bw, bh = bx1 - bx0, by1 - by0
    scale = min((width - 2 * MARGIN_PX) / bw, (height - 2 * MARGIN_PX) / bh)
    ox = (width - bw * scale) / 2
    oy = (height - bh * scale) / 2

    def P(x, y):
        return (ox + (x - bx0) * scale, oy + (y - by0) * scale)

    # board edge
    dr.rectangle([P(bx0, by0), P(bx1, by1)], fill=BG_RGB,
                 outline=EDGE_RGB, width=2)
    # keepouts（虚线）
    dash = max(3.0, 0.8 * scale)
    for k in board.keepouts:
        kx0, ky0 = P(k.rect_mm[0], k.rect_mm[1])
        kx1, ky1 = P(k.rect_mm[2], k.rect_mm[3])
        _dashed_rect(dr, [kx0, ky0, kx1, ky1], dash, dash, KEEPOUT_RGB, 2)
    # pads
    for p in board.pads:
        dr.rectangle([P(p.x_mm - p.w_mm / 2, p.y_mm - p.h_mm / 2),
                      P(p.x_mm + p.w_mm / 2, p.y_mm + p.h_mm / 2)],
                     fill=PAD_FILL, outline=PAD_EDGE, width=1)
    # routes（按图例配色）
    f_label = _font(max(10, round(height / 56)))
    label_ascent = f_label.size if hasattr(f_label, "size") else 12
    for route in ref["routes"]:
        color = RGB.get(route["line_type"], RGB["signal"])
        pts = [P(q[0], q[1]) for q in route["polyline_mm"]]
        lw = max(1, int(round(route["width_mm"] * scale * 1.6)))
        dr.line(pts, fill=color, width=lw, joint="curve")
        mid = _polyline_midpoint(route["polyline_mm"])
        mx, my = P(mid[0], mid[1])
        _text_xy(dr, (mx + 4, my - label_ascent - 4),
                 route["route_id"], f_label)
    # vias（黑圈）
    for via in ref["vias"]:
        r_px = max(3.0, (via["drill_mm"] / 2 + via["annular_ring_mm"])
                   * scale)
        cx, cy = P(via["center_mm"][0], via["center_mm"][1])
        dr.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px],
                   outline=VIA_RGB, width=2)
    # 左上角 scenario_id
    f_title = _font(max(12, round(height / 36)))
    _text_xy(dr, (12, 10), board.scenario_id, f_title)
    # 右下角 mm 比例尺
    bar_px = SCALE_BAR_MM * scale
    x1b = width - 16
    y1b = height - 18
    dr.line([(x1b - bar_px, y1b), (x1b, y1b)], fill=TEXT_RGB, width=2)
    for tx in (x1b - bar_px, x1b):
        dr.line([(tx, y1b - 4), (tx, y1b + 4)], fill=TEXT_RGB, width=2)
    _text_xy(dr, (x1b - bar_px / 2, y1b + 6), f"{fmt3(SCALE_BAR_MM)} mm",
             _font(max(9, round(height / 60))), anchor="ma")
    # 图例框（右上）
    _draw_legend(dr, width, ref)
    return img


def _draw_legend(dr, width: int, ref: dict) -> None:
    f = _font(max(9, round(width / 110)))
    row_h = int(f.size * 1.7) if hasattr(f, "size") else 16
    entries = [("line", "signal", RGB["signal"]),
               ("line", "clock", RGB["clock"]),
               ("line", "bus_trunk", RGB["bus_trunk"]),
               ("line", "bus_member", RGB["bus_member"]),
               ("via", "via", VIA_RGB),
               ("pad", "pad", PAD_FILL),
               ("keepout", "keepout", KEEPOUT_RGB)]
    box_w = max(120, int(width * 0.13))
    pad = 8
    box_h = row_h * len(entries) + 2 * pad
    x0 = width - box_w - 12
    y0 = 12
    dr.rectangle([x0, y0, x0 + box_w, y0 + box_h], fill=(255, 255, 255),
                 outline=TEXT_RGB, width=1)
    sw_x0 = x0 + pad
    tx = x0 + pad + 34
    for i, (kind, label, color) in enumerate(entries):
        cy = y0 + pad + row_h * i + row_h // 2
        if kind == "line":
            dr.line([(sw_x0, cy), (sw_x0 + 26, cy)], fill=color,
                    width=max(2, row_h // 4))
        elif kind == "via":
            r = row_h // 3
            dr.ellipse([sw_x0 + 13 - r, cy - r, sw_x0 + 13 + r, cy + r],
                       outline=color, width=2)
        elif kind == "pad":
            dr.rectangle([sw_x0 + 4, cy - row_h // 4, sw_x0 + 22,
                          cy + row_h // 4], fill=color, outline=PAD_EDGE)
        else:
            _dashed_rect(dr, [sw_x0 + 4, cy - row_h // 4, sw_x0 + 22,
                              cy + row_h // 4], 3.0, 2.0, color, 1)
        dr.text((tx, cy), label, fill=TEXT_RGB, font=f, anchor="lm")


def render_all(board: Board, ref: dict, manifest: dict, out_dir: str):
    """渲染四档分辨率并落盘；返回写入的相对路径列表（确定序）。"""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for w, h in RESOLUTIONS:
        img = render(board, ref, manifest, w, h)
        path = os.path.join(
            out_dir, f"route-preview-{board.scenario_id}-{w}x{h}.png")
        img.save(path, format="PNG")
        paths.append(path.replace("\\", "/"))
    return paths


def main() -> None:
    import json as _json
    import sys
    cfg = model.read_stdin_json()
    board = model.board_from_obj(model.read_json(cfg["board_path"]))
    ref = model.read_json(cfg["ref_routes_path"])
    manifest = model.read_json(cfg["manifest_path"])
    if ref["scenario_id"] != board.scenario_id \
            or manifest["scenario_id"] != board.scenario_id:
        raise ValueError("输入文件 scenario_id 不一致")
    if len(manifest["routes"]) != len(ref["routes"]) \
            or len(manifest["vias"]) != len(ref["vias"]):
        raise ValueError("manifest 与 ref-routes 的 route/via 数量不一致")
    paths = render_all(board, ref, manifest,
                       cfg.get("out_dir") or "out/v4-experiment")
    sys.stdout.write(_json.dumps(
        {"scenario_id": board.scenario_id, "pngs": paths},
        sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
