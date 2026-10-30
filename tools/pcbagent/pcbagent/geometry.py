# -*- coding: utf-8 -*-
"""精确几何内核（mm，float）。全部距离为表面-表面真值，禁用栅格近似下结论。

统一形状模型：prim = (core, r)
  core ∈ {('pt',x,y), ('seg',x1,y1,x2,y2), ('poly',[(x,y),...])}（poly 须为凸）
  r ≥ 0 为 Minkowski 半径：prim 实体 = core ⊕ 圆盘 r
  走线=(seg,w/2)；过孔盘=(pt,size/2)；钻孔=(pt,drill/2)（椭圆钻=seg 轴+drill/2）；
  圆焊盘=(pt,r)；椭圆焊盘=(seg,r)；矩形=(poly,0)；圆角矩形=(内缩poly, rratio)；
  自定义焊盘=多个 prim 的并（距离取 min）。
两 prim 距离 = dist_core_core − r1 − r2（相交则 0）。
旋转角采用 KiCad 文件坐标（y 向下），rot_pt 为"屏幕逆时针"约定。
"""
from __future__ import annotations

import math

EPS = 1e-9


# ---------- 基本原语 ----------

def rot_pt(x: float, y: float, deg: float):
    """KiCad 约定点旋转（y 向下坐标系，角度为屏幕逆时针）。"""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (c * x + s * y, -s * x + c * y)


def seg_pt_dist(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 < EPS * EPS:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _orient(ax, ay, bx, by, cx, cy) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _onseg(px, py, x1, y1, x2, y2) -> bool:
    return (min(x1, x2) - EPS <= px <= max(x1, x2) + EPS and
            min(y1, y2) - EPS <= py <= max(y1, y2) + EPS)


def seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy) -> float:
    """线段-线段距离（含共线/端点接触，修复 p5_ground M2 轴对齐粗检缺陷）。"""
    o1 = _orient(ax, ay, bx, by, cx, cy)
    o2 = _orient(ax, ay, bx, by, dx, dy)
    o3 = _orient(cx, cy, dx, dy, ax, ay)
    o4 = _orient(cx, cy, dx, dy, bx, by)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
        return 0.0
    if abs(o1) < 1e-12 and _onseg(cx, cy, ax, ay, bx, by):
        return 0.0
    if abs(o2) < 1e-12 and _onseg(dx, dy, ax, ay, bx, by):
        return 0.0
    if abs(o3) < 1e-12 and _onseg(ax, ay, cx, cy, dx, dy):
        return 0.0
    if abs(o4) < 1e-12 and _onseg(bx, by, cx, cy, dx, dy):
        return 0.0
    return min(seg_pt_dist(ax, ay, cx, cy, dx, dy),
               seg_pt_dist(bx, by, cx, cy, dx, dy),
               seg_pt_dist(cx, cy, ax, ay, bx, by),
               seg_pt_dist(dx, dy, ax, ay, bx, by))


def pt_poly_dist(px, py, poly) -> float:
    """点-凸多边形：内部/边上=0，否则到边最小距离。"""
    n = len(poly)
    inside = True
    best = float("inf")
    sign = 0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        d = seg_pt_dist(px, py, x1, y1, x2, y2)
        if d < best:
            best = d
        o = _orient(x1, y1, x2, y2, px, py)
        if abs(o) > EPS:
            s = 1 if o > 0 else -1
            if sign == 0:
                sign = s
            elif s != sign:
                inside = False
    # 凸多边形：所有叉积同号 ⇔ 内部
    if inside:
        return 0.0
    return best


def pt_in_poly(px, py, poly) -> bool:
    return pt_poly_dist(px, py, poly) <= EPS


def seg_poly_dist(x1, y1, x2, y2, poly) -> float:
    """段-凸多边形（修复 p5_ground '只查端点漏中段'缺陷：中段穿入判 0）。"""
    if pt_in_poly(x1, y1, poly) or pt_in_poly(x2, y2, poly):
        return 0.0
    n = len(poly)
    best = float("inf")
    for i in range(n):
        px1, py1 = poly[i]
        px2, py2 = poly[(i + 1) % n]
        d = seg_seg_dist(x1, y1, x2, y2, px1, py1, px2, py2)
        if d <= EPS:
            return 0.0
        if d < best:
            best = d
    return best


def poly_poly_dist(pa, pb) -> float:
    """两凸多边形：相交=0，否则边界最小距离。"""
    for (px, py) in pa:
        if pt_in_poly(px, py, pb):
            return 0.0
    for (px, py) in pb:
        if pt_in_poly(px, py, pa):
            return 0.0
    best = float("inf")
    na, nb = len(pa), len(pb)
    for i in range(na):
        ax, ay = pa[i]
        bx, by = pa[(i + 1) % na]
        for j in range(nb):
            cx, cy = pb[j]
            dx, dy = pb[(j + 1) % nb]
            d = seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy)
            if d <= EPS:
                return 0.0
            if d < best:
                best = d
    return best


# ---------- prim（core ⊕ r）距离 ----------

def _core_kinds(core):
    return core[0]


def prim_dist(p1, p2) -> float:
    """两 prim 表面距离（相交/重叠=0）。"""
    d = _core_dist(p1[0], p2[0])
    return max(0.0, d - p1[1] - p2[1])


def _core_dist(c1, c2) -> float:
    k1, k2 = c1[0], c2[0]
    if k1 == "pt" and k2 == "pt":
        return math.hypot(c1[1] - c2[1], c1[2] - c2[2])
    if k1 == "pt" and k2 == "seg":
        return seg_pt_dist(c1[1], c1[2], c2[1], c2[2], c2[3], c2[4])
    if k1 == "seg" and k2 == "pt":
        return seg_pt_dist(c2[1], c2[2], c1[1], c1[2], c1[3], c1[4])
    if k1 == "seg" and k2 == "seg":
        return seg_seg_dist(c1[1], c1[2], c1[3], c1[4], c2[1], c2[2], c2[3], c2[4])
    if k1 == "pt" and k2 == "poly":
        return pt_poly_dist(c1[1], c1[2], c2[1])
    if k1 == "poly" and k2 == "pt":
        return pt_poly_dist(c2[1], c2[2], c1[1])
    if k1 == "seg" and k2 == "poly":
        return seg_poly_dist(c1[1], c1[2], c1[3], c1[4], c2[1])
    if k1 == "poly" and k2 == "seg":
        return seg_poly_dist(c2[1], c2[2], c2[3], c2[4], c1[1])
    if k1 == "poly" and k2 == "poly":
        return poly_poly_dist(c1[1], c2[1])
    raise ValueError(f"unknown cores {k1}/{k2}")


def prim_bbox(p):
    """(x1,y1,x2,y2) 含 Minkowski 半径的外接框。"""
    core, r = p
    k = core[0]
    if k == "pt":
        x, y = core[1], core[2]
        return (x - r, y - r, x + r, y + r)
    if k == "seg":
        return (min(core[1], core[3]) - r, min(core[2], core[4]) - r,
                max(core[1], core[3]) + r, max(core[2], core[4]) + r)
    xs = [p0[0] for p0 in core[1]]
    ys = [p0[1] for p0 in core[1]]
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)


def seg_prim_dist(x1, y1, x2, y2, p) -> float:
    """候选段（线宽另计）到 prim 的表面距离 = core 距离 − p.r。"""
    seg = ("seg", x1, y1, x2, y2)
    return max(0.0, _core_dist(seg, p[0]) - p[1])


def pt_prim_dist(px, py, p) -> float:
    pt = ("pt", px, py)
    return max(0.0, _core_dist(pt, p[0]) - p[1])


# ---------- 多环多边形（zone 填充：外环+孔，nonzero winding）----------

def _winding(px, py, ring) -> int:
    w = 0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if y1 <= py:
            if y2 > py and _orient(x1, y1, x2, y2, px, py) > 0:
                w += 1
        else:
            if y2 <= py and _orient(x1, y1, x2, y2, px, py) < 0:
                w -= 1
    return w


def pt_in_rings(px, py, rings) -> bool:
    """rings=多个环（外环与孔绕向相反）：非零总绕数 ⇔ 在实体铜内。"""
    w = 0
    for ring in rings:
        w += _winding(px, py, ring)
    return w != 0


def seg_crosses_rings(x1, y1, x2, y2, ring_edges) -> bool:
    """段是否穿过任一环边（ring_edges: [(x1,y1,x2,y2),...]）。"""
    for (ex1, ey1, ex2, ey2) in ring_edges:
        if seg_seg_dist(x1, y1, x2, y2, ex1, ey1, ex2, ey2) <= EPS:
            return True
    return False


# ---------- 其它 ----------

def seg_angle_ok(x1, y1, x2, y2, tol_deg=1e-6) -> bool:
    """段方向是否为 45° 整倍数（track_angle 规则）。"""
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
    m = ang % 45.0
    return min(m, 45.0 - m) < tol_deg or math.hypot(x2 - x1, y2 - y1) < EPS


def rect_poly(x1, y1, x2, y2):
    """轴对齐矩形 → 凸 poly（有序）。"""
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def inset_rect_poly(cx, cy, hw, hh, inset):
    """圆角矩形内缩核：中心 (cx,cy) 半宽 hw 半高 hh，内缩 inset；若非法返回 None。"""
    whw, whh = hw - inset, hh - inset
    if whw < -EPS or whh < -EPS:
        return None
    if whw < EPS or whh < EPS:
        # 退化成线/点：给一个极小核
        whw = max(whw, EPS)
        whh = max(whh, EPS)
    return [(cx - whw, cy - whh), (cx + whw, cy - whh),
            (cx + whw, cy + whh), (cx - whw, cy + whh)]
