"""pcbflow.v4_1.geometry -- 精确焊盘几何基元与 clearance 精确距离引擎。

设计（全部解析闭式，零采样，零近似——custom 基元除外，见下）：

Minkowski 核表示：KiCad 四类焊盘形态全部 = 「核 ⊕ 半径 r 圆盘」：

==========================  =============================  ====================
形态（KiCad shape）          核（板坐标系，含旋转变换）      r
==========================  =============================  ====================
circle  （圆）               点                             max(w,h)/2 *
oval    （椭圆=胶囊/stadium） 长轴方向线段，长 |w-h|          min(w,h)/2
rect    （矩形）              矩形（w×h，含旋转）             0
roundrect（圆角矩形）         内缩矩形 (w-2r)×(h-2r)          rratio*min(w,h)
custom  （自定义基元）**      基元顶点包围盒矩形（保守超集）   0
==========================  =============================  ====================

注[1] circle 的 w!=h 属畸形输入：KiCad 实际取单一轴为直径；本引擎取
max(w,h) 为直径（两种解释的保守超集，漏报=0 方向）。w==h 时为精确圆。

注[2] custom = backlog 不实现（任务书 §3 E1）；解析器提取其基元顶点，
几何上以顶点包围盒为保守超集建模（多报不少报），并在结果中显式登记
conservative_approximation，绝不静默。

距离恒等式（对任意点集 S 与闭集 K 成立）：
    dist(S, K ⊕ D_r) = dist(S, K) - r
由此一切 clearance 统一为：

    clearance(A, B) = dist(coreA, coreB) - rA - rB

核只有三种形态：点 / 线段 / 凸多边形（矩形）。两两距离（6 组合）全部
解析闭式（线段-线段标准算法；线段/点-凸多边形=不相交时对边最小距离
——凸集间最小距离在边对上取得，精确；相交时置 0 触发负 clearance 判
违例，穿透深度按核计为下界并标记 overlap=True，不冒充精确深度）。

旋转：焊盘总旋转 = footprint 旋转 + pad 相对旋转（KiCad >= 6 板文件
语义：pad (at) 第三元为 footprint 相对角）。核顶点/端点在构造时变换到
板坐标系；距离计算与旋转无关（刚体变换不变量）。

自检锚（G1.1 根因几何）：U1.109 roundrect 1.5x0.3 rratio 0.25 @
(47.675, 23.65)；LTDC_R7 倒角段 (48.1263,23.15)->(48.638432,23.362132)
w=0.15 → 本引擎预测 clearance 0.157043mm，kicad-cli 实测 0.1571mm
（tests/test_v4_1_regression_g11.py 复核）。

本模块零 IO、零子进程、零网络、零 wall-clock；纯函数、确定性。
"""

from __future__ import annotations

import math

__all__ = [
    "SUPPORTED_SHAPES", "PadGeom", "GeomError",
    "seg_seg_dist", "point_seg_dist", "point_point_dist",
    "point_polygon_distance", "seg_polygon_distance",
    "polygon_polygon_distance", "cores_distance",
    "clearance_between_items", "GeomItem",
]

#: 支持的精确形态（custom=保守包围盒近似，backlog）
SUPPORTED_SHAPES = ("circle", "oval", "rect", "roundrect", "custom")

_EPS = 1e-12


class GeomError(ValueError):
    """几何校验 fail-closed（缺字段/非法枚举/非有限数/形状退化/离格）。"""


# ---------------------------------------------------------------- 基础距离

def _finite(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise GeomError("%s 非数值（fail-closed）: %r" % (what, v))
    v = float(v)
    if not math.isfinite(v):
        raise GeomError("%s 非有限数（fail-closed）: %r" % (what, v))
    return v


def point_point_dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)


def point_seg_dist(px, py, ax, ay, bx, by):
    """点到线段距离（精确；零长线段退化为点距）。"""
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    if l2 <= _EPS:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * vx + (py - ay) * vy) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _on_segment(ax, ay, bx, by, px, py):
    return (min(ax, bx) - _EPS <= px <= max(ax, bx) + _EPS
            and min(ay, by) - _EPS <= py <= max(ay, by) + _EPS
            and abs(_orient(ax, ay, bx, by, px, py)) <= _EPS)


def _segments_intersect(p1x, p1y, p2x, p2y, p3x, p3y, p4x, p4y):
    d1 = _orient(p3x, p3y, p4x, p4y, p1x, p1y)
    d2 = _orient(p3x, p3y, p4x, p4y, p2x, p2y)
    d3 = _orient(p1x, p1y, p2x, p2y, p3x, p3y)
    d4 = _orient(p1x, p1y, p2x, p2y, p4x, p4y)
    if ((d1 > _EPS and d2 < -_EPS) or (d1 < -_EPS and d2 > _EPS)) and \
            ((d3 > _EPS and d4 < -_EPS) or (d3 < -_EPS and d4 > _EPS)):
        return True
    for (ox, oy, ax, ay, px, py) in (
            (p1x, p1y, p2x, p2y, p3x, p3y),
            (p1x, p1y, p2x, p2y, p4x, p4y),
            (p3x, p3y, p4x, p4y, p1x, p1y),
            (p3x, p3y, p4x, p4y, p2x, p2y)):
        if abs(_orient(ox, oy, ax, ay, px, py)) <= _EPS \
                and _on_segment(ox, oy, ax, ay, px, py):
            return True
    return False


def seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    """线段-线段距离（精确；相交=0）。"""
    if _segments_intersect(ax, ay, bx, by, cx, cy, dx, dy):
        return 0.0
    return min(
        point_seg_dist(ax, ay, cx, cy, dx, dy),
        point_seg_dist(bx, by, cx, cy, dx, dy),
        point_seg_dist(cx, cy, ax, ay, bx, by),
        point_seg_dist(dx, dy, ax, ay, bx, by),
    )


def _point_in_convex_polygon(px, py, poly):
    """点是否在凸多边形内/边上（含边界；poly=顶点环列表）。"""
    n = len(poly)
    if n == 0:
        raise GeomError("空多边形（fail-closed）")
    sign = 0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        o = _orient(x1, y1, x2, y2, px, py)
        if abs(o) <= _EPS:
            continue
        s = 1 if o > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return True


def _polygon_edges(poly):
    n = len(poly)
    for i in range(n):
        yield poly[i], poly[(i + 1) % n]


def _point_in_polygon_or_edge(px, py, poly):
    if len(poly) == 1:
        return math.hypot(px - poly[0][0], py - poly[0][1]) <= _EPS
    if len(poly) == 2:
        return point_seg_dist(px, py, poly[0][0], poly[0][1],
                              poly[1][0], poly[1][1]) <= _EPS
    return _point_in_convex_polygon(px, py, poly)


def _convex_polygons_intersect(pa, pb):
    """两凸核（1/2/n 顶点）是否相交（含边界）。"""
    if len(pa) == 1:
        return _point_in_polygon_or_edge(pa[0][0], pa[0][1], pb)
    if len(pb) == 1:
        return _point_in_polygon_or_edge(pb[0][0], pb[0][1], pa)
    if len(pa) == 2 and len(pb) == 2:
        return _segments_intersect(pa[0][0], pa[0][1], pa[1][0], pa[1][1],
                                   pb[0][0], pb[0][1], pb[1][0], pb[1][1])
    # 一般：线段对相交 或 顶点落入对方
    for (a1, a2) in _polygon_edges(pa):
        for (b1, b2) in _polygon_edges(pb):
            if _segments_intersect(a1[0], a1[1], a2[0], a2[1],
                                   b1[0], b1[1], b2[0], b2[1]):
                return True
    for v in pa:
        if _point_in_polygon_or_edge(v[0], v[1], pb):
            return True
    for v in pb:
        if _point_in_polygon_or_edge(v[0], v[1], pa):
            return True
    return False


def point_polygon_distance(px, py, poly):
    """点到凸多边形核距离（精确；内含=0 触发负 clearance）。"""
    if _point_in_polygon_or_edge(px, py, poly):
        return 0.0
    best = math.inf
    for (a, b) in _polygon_edges(poly):
        d = point_seg_dist(px, py, a[0], a[1], b[0], b[1])
        if d < best:
            best = d
    return best


def seg_polygon_distance(ax, ay, bx, by, poly):
    """线段到凸多边形核距离（精确；相交=0）。"""
    if _point_in_polygon_or_edge(ax, ay, poly) or \
            _point_in_polygon_or_edge(bx, by, poly):
        return 0.0
    best = math.inf
    for (c, d) in _polygon_edges(poly):
        ds = seg_seg_dist(ax, ay, bx, by, c[0], c[1], d[0], d[1])
        if ds < best:
            best = ds
    return best


def polygon_polygon_distance(pa, pb):
    """凸多边形核间距离（精确；相交=0）。"""
    if _convex_polygons_intersect(pa, pb):
        return 0.0
    best = math.inf
    for (a1, a2) in _polygon_edges(pa):
        for (b1, b2) in _polygon_edges(pb):
            d = seg_seg_dist(a1[0], a1[1], a2[0], a2[1],
                             b1[0], b1[1], b2[0], b2[1])
            if d < best:
                best = d
    return best


def cores_distance(core_a, core_b):
    """两核（顶点列表：1=点 / 2=线段 / >=4=凸多边形环）间精确距离。"""
    na, nb = len(core_a), len(core_b)
    if na == 1 and nb == 1:
        return point_point_dist(core_a[0][0], core_a[0][1],
                                core_b[0][0], core_b[0][1])
    if na == 1:
        return point_polygon_distance(core_a[0][0], core_a[0][1], core_b)
    if nb == 1:
        return point_polygon_distance(core_b[0][0], core_b[0][1], core_a)
    if na == 2 and nb == 2:
        return seg_seg_dist(core_a[0][0], core_a[0][1],
                            core_a[1][0], core_a[1][1],
                            core_b[0][0], core_b[0][1],
                            core_b[1][0], core_b[1][1])
    if na == 2:
        return seg_polygon_distance(core_a[0][0], core_a[0][1],
                                    core_a[1][0], core_a[1][1], core_b)
    if nb == 2:
        return seg_polygon_distance(core_b[0][0], core_b[0][1],
                                    core_b[1][0], core_b[1][1], core_a)
    return polygon_polygon_distance(core_a, core_b)


# ---------------------------------------------------------------- 焊盘基元

def _rotate(x, y, cos_t, sin_t):
    """KiCad 画布约定（y-down，正角 CCW 视觉）：见 p3_revc_staging 同源
    映射 x'=x*cos+y*sin, y'=-x*sin+y*cos（只读参考其口径；本模块独立
    实现）。"""
    return (x * cos_t + y * sin_t, -x * sin_t + y * cos_t)


class PadGeom:
    """精确焊盘几何（Minkowski 核表示；构造即校验，fail-closed）。

    参数均为板坐标系（焊盘中心、总旋转弧度）或焊盘局部参数（w/h/r）。
    core 返回局部核顶点经旋转平移后的板坐标顶点列表。
    """

    __slots__ = ("shape", "x", "y", "w", "h", "radius", "rotation_deg",
                 "pad_id", "net_id", "layers", "conservative_approximation",
                 "_core", "_cos", "_sin")

    def __init__(self, shape, x, y, w, h, rotation_deg, radius=None,
                 pad_id="", net_id="", layers=(), primitive_pts=None):
        if shape not in SUPPORTED_SHAPES:
            raise GeomError("非法形态枚举（fail-closed）: %r" % (shape,))
        self.shape = shape
        self.x = _finite(x, "pad.x")
        self.y = _finite(y, "pad.y")
        self.w = _finite(w, "pad.w")
        self.h = _finite(h, "pad.h")
        self.rotation_deg = _finite(rotation_deg, "pad.rotation")
        self.pad_id = str(pad_id)
        self.net_id = net_id if net_id is None else str(net_id)
        self.layers = tuple(layers)
        if self.w <= 0.0 or self.h <= 0.0:
            raise GeomError("形状退化：零/负尺寸（fail-closed）w=%r h=%r"
                            % (w, h))
        self.conservative_approximation = None
        self._cos = math.cos(math.radians(self.rotation_deg))
        self._sin = math.sin(math.radians(self.rotation_deg))
        self._core = self._build_core(shape, radius, primitive_pts)

    # -- 核构造 ------------------------------------------------------

    def _to_board(self, lx, ly):
        rx, ry = _rotate(lx, ly, self._cos, self._sin)
        return (self.x + rx, self.y + ry)

    def _build_core(self, shape, radius, primitive_pts):
        if shape == "circle":
            # 精确圆（w==h）；w!=h 畸形取 max 轴直径=保守超集
            r = max(self.w, self.h) / 2.0
            if r <= 0.0:
                raise GeomError("形状退化：圆半径<=0（fail-closed）")
            return [self._to_board(0.0, 0.0)], r
        if shape == "oval":
            r = min(self.w, self.h) / 2.0
            if r <= 0.0:
                raise GeomError("形状退化：椭圆半径<=0（fail-closed）")
            if self.w >= self.h:
                half = (self.w - self.h) / 2.0
                a, b = self._to_board(-half, 0.0), self._to_board(half, 0.0)
            else:
                half = (self.h - self.w) / 2.0
                a, b = self._to_board(0.0, -half), self._to_board(0.0, half)
            return [a, b], r
        if shape == "rect":
            pts = [self._to_board(sx * self.w / 2.0, sy * self.h / 2.0)
                   for (sx, sy) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            return pts, 0.0
        if shape == "roundrect":
            if radius is None:
                raise GeomError("roundrect 缺圆角半径参数（fail-closed）")
            r = _finite(radius, "roundrect.radius")
            if r < 0.0 or r > min(self.w, self.h) / 2.0 + _EPS:
                raise GeomError("圆角半径越界（fail-closed）r=%r 限 [0, "
                                "min(w,h)/2=%r]" % (r, min(self.w, self.h) / 2.0))
            r = min(r, min(self.w, self.h) / 2.0)
            cw, ch = self.w - 2.0 * r, self.h - 2.0 * r
            if cw < -_EPS or ch < -_EPS:
                raise GeomError("roundrect 内缩核负尺寸（fail-closed）")
            cw = max(cw, 0.0)
            ch = max(ch, 0.0)
            pts = [self._to_board(sx * cw / 2.0, sy * ch / 2.0)
                   for (sx, sy) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            return pts, r
        # custom：backlog 不实现；保守顶点包围盒超集（显式登记不静默）
        self.conservative_approximation = (
            "custom 基元 backlog 未实现：以基元顶点(经旋转)轴对齐包围盒"
            "为保守超集建模（只多报不少报）")
        if primitive_pts:
            board_pts = [self._to_board(px, py)
                         for (px, py) in primitive_pts]
        else:
            board_pts = [self._to_board(sx * self.w / 2.0, sy * self.h / 2.0)
                         for (sx, sy) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        xs = [p[0] for p in board_pts]
        ys = [p[1] for p in board_pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        return [(x1, y1), (x1, y0), (x0, y0), (x0, y1)], 0.0

    @property
    def core(self):
        """核顶点（板坐标；1=点，2=线段，4=凸多边形环）。"""
        return self._core[0]

    @property
    def core_radius(self):
        return self._core[1]

    def bbox(self):
        """保守包围盒（含圆角半径与旋转；报告/空间索引用）。"""
        r = self.core_radius
        xs = [p[0] for p in self._core[0]]
        ys = [p[1] for p in self._core[0]]
        return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)

    def distance_to_point(self, px, py):
        """点到焊盘边界距离（外正；核距-r 恒等式）。"""
        px = _finite(px, "query.x")
        py = _finite(py, "query.y")
        return point_polygon_distance(px, py, self._core[0]) - \
            self.core_radius

    def distance_to_segment(self, ax, ay, bx, by):
        """线段（中心线）到焊盘边界距离（精确，Minkowski 恒等式）。"""
        return seg_polygon_distance(_finite(ax, "seg.ax"), _finite(ay, "seg.ay"),
                                    _finite(bx, "seg.bx"),
                                    _finite(by, "seg.by"),
                                    self._core[0]) - self.core_radius


# ---------------------------------------------------------------- 物项

class GeomItem:
    """clearance 物项统一核表示（track/via/pad）。

    kind ∈ {"track", "via", "pad"}；layer=所属铜层（via=跨度层集合，
    pad=THT 为全部铜层）；net=网名。
    """

    __slots__ = ("kind", "net", "layers", "core", "radius", "src",
                 "conservative_approximation")

    def __init__(self, kind, net, layers, core, radius, src=None,
                 conservative_approximation=None):
        if kind not in ("track", "via", "pad"):
            raise GeomError("非法物项类型（fail-closed）: %r" % (kind,))
        if radius < 0.0 or not math.isfinite(radius):
            raise GeomError("非法半径（fail-closed）: %r" % (radius,))
        if not core:
            raise GeomError("空核（fail-closed）")
        self.kind = kind
        self.net = net
        self.layers = frozenset(layers)
        self.core = tuple(core)
        self.radius = float(radius)
        self.src = src if src is not None else {}
        self.conservative_approximation = conservative_approximation

    @classmethod
    def from_track(cls, net, layer, width, ax, ay, bx, by, src=None):
        ax = _finite(ax, "track.ax")
        ay = _finite(ay, "track.ay")
        bx = _finite(bx, "track.bx")
        by = _finite(by, "track.by")
        w = _finite(width, "track.width")
        if w <= 0.0:
            raise GeomError("走线零/负宽度（fail-closed）w=%r" % (width,))
        return cls("track", net, {layer}, [(ax, ay), (bx, by)], w / 2.0,
                   src=src)

    @classmethod
    def from_via(cls, net, size, layers, x, y, src=None):
        x = _finite(x, "via.x")
        y = _finite(y, "via.y")
        s = _finite(size, "via.size")
        if s <= 0.0:
            raise GeomError("via 零/负尺寸（fail-closed）size=%r" % (size,))
        return cls("via", net, set(layers), [(x, y)], s / 2.0, src=src)

    @classmethod
    def from_pad(cls, pad: PadGeom, copper_layers, src=None):
        return cls("pad", pad.net_id, set(copper_layers), pad.core,
                   pad.core_radius, src=src,
                   conservative_approximation=pad.conservative_approximation)

    def shares_layer(self, other):
        return bool(self.layers & other.layers)


def clearance_between_items(a: GeomItem, b: GeomItem):
    """两物项精确 clearance（= 核距 - 双方半径）。

    核相交（物项重叠）时核距=0 → clearance = -(ra+rb)（穿透深度按核计
    下界，标记 overlap；量级仅报告用，判违例只需 <0）。不同层返回 None
    （无 clearance 约束）。
    """
    if not a.shares_layer(b):
        return None
    d = cores_distance(a.core, b.core)
    overlap = d <= _EPS
    return {
        "clearance_mm": d - a.radius - b.radius,
        "overlap": overlap,
        "same_layer": True,
    }
