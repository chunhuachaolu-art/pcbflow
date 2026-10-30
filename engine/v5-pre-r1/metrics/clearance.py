# -*- coding: utf-8 -*-
"""间距度量原语（P0 四模块之一）。

只提供确定性几何距离计算；"是否违例"的判定语义在 v5.drc（A9 单源）。
坐标单位 mm。支持：点、线段（折线逐段）、圆（焊盘 r=0.15 型）、矩形铜带。
所有距离函数在浮点下保持确定：同输入双跑同结果。
"""
import math

EPS = 1e-9


def point_point(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment(p, a, b):
    """点到线段最短距离（退化：a==b 时为点距）。"""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    seg_len2 = dx * dx + dy * dy
    if seg_len2 < EPS:
        return point_point(p, a)
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / seg_len2
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _on_segment(p, a, b):
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def segment_segment(p1, p2, p3, p4):
    """线段对最短距离。相交返回 0.0；共线重叠返回 0.0；擦边（端点接触）返回 0.0。"""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and \
       abs(d1) > EPS and abs(d2) > EPS and abs(d3) > EPS and abs(d4) > EPS:
        return 0.0
    if abs(d1) < EPS and _on_segment(p1, p3, p4):
        return 0.0
    if abs(d2) < EPS and _on_segment(p2, p3, p4):
        return 0.0
    if abs(d3) < EPS and _on_segment(p3, p1, p2):
        return 0.0
    if abs(d4) < EPS and _on_segment(p4, p1, p2):
        return 0.0
    return min(
        point_segment(p1, p3, p4), point_segment(p2, p3, p4),
        point_segment(p3, p1, p2), point_segment(p4, p1, p2),
    )


def polyline(points):
    """折线两两相邻段列表。"""
    return list(zip(points[:-1], points[1:]))


def polyline_polyline(pts_a, pts_b):
    return min(segment_segment(a1, a2, b1, b2)
               for a1, a2 in polyline(pts_a) for b1, b2 in polyline(pts_b))


def segment_rect_distance(a, b, rect):
    """线段到轴对齐矩形的最短距离（矩形内/边上为 0）。"""
    x0, y0, x1, y1 = rect["x_min"], rect["y_min"], rect["x_max"], rect["y_max"]
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    best = float("inf")
    for (cx, cy), (nx, ny) in zip(corners, corners[1:]):
        best = min(best, segment_segment(a, b, (cx, cy), (nx, ny)))
    # 端点在矩形内部
    for p in (a, b):
        if x0 - EPS <= p[0] <= x1 + EPS and y0 - EPS <= p[1] <= y1 + EPS:
            best = 0.0
    return best


def pad_rect_distance(center, radius, rect):
    """圆焊盘到矩形距离（圆心到矩形距离 − r，夹断到 0 当相交）。"""
    x0, y0, x1, y1 = rect["x_min"], rect["y_min"], rect["x_max"], rect["y_max"]
    cx, cy = center
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    return max(0.0, math.hypot(dx, dy) - radius)


def pad_pad_distance(c1, r1, c2, r2):
    return max(0.0, point_point(c1, c2) - r1 - r2)


def pad_segment_distance(center, radius, a, b):
    return max(0.0, point_segment(center, a, b) - radius)


def rect_rect_gap(rect_a, rect_b):
    """两轴对齐矩形间隙（重叠/接触 = 0）。"""
    ax0, ay0, ax1, ay1 = rect_a
    bx0, by0, bx1, by1 = rect_b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy)


def parallel_overlap_length(a1, a2, b1, b2, axis):
    """两平行线段在同一轴向上的重叠长度（R2 平行长度核算用）。axis: 'x' or 'y'。

    两段须在同一坐标（同 x 或同 y 带内）；否则重叠为 0。
    """
    idx = 0 if axis == "x" else 1
    lo_a, hi_a = sorted((a1[idx], a2[idx]))
    lo_b, hi_b = sorted((b1[idx], b2[idx]))
    return max(0.0, min(hi_a, hi_b) - max(lo_a, lo_b))
