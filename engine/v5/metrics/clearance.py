# -*- coding: utf-8 -*-
"""间距度量原语（P0 四模块之一）。

只提供确定性几何距离计算；"是否违例"的判定语义在 v5.drc（A9 单源）。
坐标单位 mm。支持：点、线段（折线逐段）、圆（焊盘 r=0.15 型）、矩形铜带。
所有距离函数在浮点下保持确定：同输入双跑同结果。

NUMBA-R1（perf 件）：point_segment / segment_segment / segment_rect_distance
的浮点距离内核以 njit 编译（仅 cache=True，禁 fastmath/parallel）。hypot 采用
CPython 3.12 ``math.hypot``＝``vector_norm``（Modules/mathmodule.c :2470-2519，
依赖 dl_fast_sum/dl_split/dl_mul :104-176）的**逐行精确移植**——numba 内建
math.hypot 与 CPython 逐位不等（perf/numba_probe.py P3：8431/50000），字节等门
下不可用；移植版经 perf/verify_mhypot_b.py ≥1e7 随机对+对抗样本零 mismatch
逐位对拍。缺 numba 时自动回落纯 Python 路径（同一源码、math.hypot，与 R1
proto 行为逐位一致）。判定/分支代码与 R1 优化版逐字相同，仅距离内核替换。
"""
import math

try:
    from numba import njit as _njit
    _HAS_NUMBA = True
except ImportError:
    _njit = None
    _HAS_NUMBA = False

EPS = 1e-9

# ---------------------------------------------------------------------------
# NUMBA-R1 内核：CPython 3.12 math.hypot（vector_norm, n=2）的精确移植。
# 源：perf/_data/cpython-3.12-mathmodule.c（3.12 分支 raw 镜像件）。
# 运算序列与 C 逐行对应；递归分支（max_e < -1023）至多一层
# （(2^-1074..2^-1024)/DBL_MIN 全为 normal），以顺序重算展开并保持
# 「DBL_MIN * (h / scale)」的乘法次序逐位一致。
# ---------------------------------------------------------------------------

_DBL_MIN = 2.2250738585072014e-308   # C DBL_MIN = 2^-1022
_SPLIT = 134217729.0                 # Veltkama 常量 2^27 + 1


def _dl_split(x):
    # mathmodule.c dl_split（Dekker 5.5/5.6）
    t = x * _SPLIT
    hi = t - (t - x)
    lo = x - hi
    return hi, lo


def _dl_mul(x, y):
    # mathmodule.c dl_mul（UNRELIABLE_FMA 分支同款，Dekker 5.12 / mul12）：
    # 与 fma 分支在 vector_norm 缩放域内产生逐位相同的 (z, zz)（误差项均精确）。
    hx, lx = _dl_split(x)
    hy, ly = _dl_split(y)
    p = hx * hy
    q = hx * ly + lx * hy
    z = p + q
    zz = p - z + q + lx * ly
    return z, zz


def _dl_fast_sum(a, b):
    # mathmodule.c dl_fast_sum（Neumaier 补偿和，前置 |a| >= |b| 在调用域恒成立）
    x = a + b
    y = (a - x) + b
    return x, y


def _hypot_py(x, y):
    # math_hypot(:2622) + vector_norm(:2470) n=2 精确移植（njit 与纯 Python 共用此源）。
    ax = math.fabs(x)
    ay = math.fabs(y)
    # max 初值 0.0、仅 x > max 时更新（:2626/:2644-2646 逐行）；
    # nan 不更新（found_nan 兜底）、±0 不写回（保 +0.0）
    mx = 0.0
    if ax > mx:
        mx = ax
    if ay > mx:
        mx = ay
    if math.isinf(mx):
        return mx
    if math.isnan(ax) or math.isnan(ay):
        return math.nan
    if mx == 0.0:
        return mx
    e = math.frexp(mx)[1]
    rescaled = False
    if e < -1023:
        # :2488-2494 subnormal 归一（vec[i] /= DBL_MIN 后递归；至多一层）
        ax = ax / _DBL_MIN
        ay = ay / _DBL_MIN
        mx = mx / _DBL_MIN
        e = math.frexp(mx)[1]
        rescaled = True
    scale = math.ldexp(1.0, -e)
    csum = 1.0
    frac1 = 0.0
    frac2 = 0.0
    # 循环按 vec[0]=|x|、vec[1]=|y| 次序展开（:2498-2509）
    x = ax * scale
    pr_hi, pr_lo = _dl_mul(x, x)
    sm_hi, sm_lo = _dl_fast_sum(csum, pr_hi)
    csum = sm_hi
    frac1 += pr_lo
    frac2 += sm_lo
    x = ay * scale
    pr_hi, pr_lo = _dl_mul(x, x)
    sm_hi, sm_lo = _dl_fast_sum(csum, pr_hi)
    csum = sm_hi
    frac1 += pr_lo
    frac2 += sm_lo
    h = math.sqrt(csum - 1.0 + (frac1 + frac2))
    pr_hi, pr_lo = _dl_mul(-h, h)
    sm_hi, sm_lo = _dl_fast_sum(csum, pr_hi)
    csum = sm_hi
    frac1 += pr_lo
    frac2 += sm_lo
    x = csum - 1.0 + (frac1 + frac2)
    h += x / (2.0 * h)
    v = h / scale
    if rescaled:
        v = _DBL_MIN * v          # :2493 DBL_MIN * vector_norm(...)
    return v


if _HAS_NUMBA:
    # 重绑定：jit 助手后，上层函数编译时全局名解析到 Dispatcher（纯 Python
    # 路径不受影响——Dispatcher 亦可从纯 Python 调用）。
    _dl_split = _njit(cache=True)(_dl_split)
    _dl_mul = _njit(cache=True)(_dl_mul)
    _dl_fast_sum = _njit(cache=True)(_dl_fast_sum)
    _hypot = _njit(cache=True)(_hypot_py)
else:
    _hypot = math.hypot


def point_point(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _point_segment_core(px, py, ax, ay, bx, by):
    """point_segment 本体（R1 版逐字，仅 tuple 解包外提 + hypot→_hypot）。"""
    dx = bx - ax
    dy = by - ay
    seg_len2 = dx * dx + dy * dy
    if seg_len2 < EPS:
        return _hypot(px - ax, py - ay)      # point_point(p, a) 同式
    t = ((px - ax) * dx + (py - ay) * dy) / seg_len2
    t = max(0.0, min(1.0, t))
    return _hypot(px - (ax + t * dx), py - (ay + t * dy))


def _segment_segment_core(p1x, p1y, p2x, p2y, p3x, p3y, p4x, p4y):
    """segment_segment 本体（R1 版逐字，_cross/_on_segment 内联展开）。"""
    # d1 = _cross(p3, p4, p1)
    d1 = (p4x - p3x) * (p1y - p3y) - (p4y - p3y) * (p1x - p3x)
    # d2 = _cross(p3, p4, p2)
    d2 = (p4x - p3x) * (p2y - p3y) - (p4y - p3y) * (p2x - p3x)
    # d3 = _cross(p1, p2, p3)
    d3 = (p2x - p1x) * (p3y - p1y) - (p2y - p1y) * (p3x - p1x)
    # d4 = _cross(p1, p2, p4)
    d4 = (p2x - p1x) * (p4y - p1y) - (p2y - p1y) * (p4x - p1x)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and \
       abs(d1) > EPS and abs(d2) > EPS and abs(d3) > EPS and abs(d4) > EPS:
        return 0.0
    if abs(d1) < EPS and (min(p3x, p4x) - EPS <= p1x <= max(p3x, p4x) + EPS and
                          min(p3y, p4y) - EPS <= p1y <= max(p3y, p4y) + EPS):
        return 0.0
    if abs(d2) < EPS and (min(p3x, p4x) - EPS <= p2x <= max(p3x, p4x) + EPS and
                          min(p3y, p4y) - EPS <= p2y <= max(p3y, p4y) + EPS):
        return 0.0
    if abs(d3) < EPS and (min(p1x, p2x) - EPS <= p3x <= max(p1x, p2x) + EPS and
                          min(p1y, p2y) - EPS <= p3y <= max(p1y, p2y) + EPS):
        return 0.0
    if abs(d4) < EPS and (min(p1x, p2x) - EPS <= p4x <= max(p1x, p2x) + EPS and
                          min(p1y, p2y) - EPS <= p4y <= max(p1y, p2y) + EPS):
        return 0.0
    # min(a,b,c,d)：四值恒 >= +0.0（_hypot 不出 -0.0/nan 于有限输入），
    # 平铺 pair-min 与原 min 四元在值域逐位同结果。
    return min(min(_point_segment_core(p1x, p1y, p3x, p3y, p4x, p4y),
                   _point_segment_core(p2x, p2y, p3x, p3y, p4x, p4y)),
               min(_point_segment_core(p3x, p3y, p1x, p1y, p2x, p2y),
                   _point_segment_core(p4x, p4y, p1x, p1y, p2x, p2y)))


def _segment_rect_core(ax, ay, bx, by, x0, y0, x1, y1):
    """segment_rect_distance 本体（R1 版逐字：端点在内先判早退 + 四边 min）。"""
    if x0 - EPS <= ax <= x1 + EPS and y0 - EPS <= ay <= y1 + EPS:
        return 0.0
    if x0 - EPS <= bx <= x1 + EPS and y0 - EPS <= by <= y1 + EPS:
        return 0.0
    best = math.inf
    best = min(best, _segment_segment_core(ax, ay, bx, by, x0, y0, x1, y0))
    best = min(best, _segment_segment_core(ax, ay, bx, by, x1, y0, x1, y1))
    best = min(best, _segment_segment_core(ax, ay, bx, by, x1, y1, x0, y1))
    best = min(best, _segment_segment_core(ax, ay, bx, by, x0, y1, x0, y0))
    return best


if _HAS_NUMBA:
    # 与 _dl_* 同款重绑定（lazy 编译：首调时全局名已解析到 Dispatcher）
    _point_segment_core = _njit(cache=True)(_point_segment_core)
    _segment_segment_core = _njit(cache=True)(_segment_segment_core)
    _segment_rect_core = _njit(cache=True)(_segment_rect_core)

_point_segment_fast = _point_segment_core
_segment_segment_fast = _segment_segment_core
_segment_rect_fast = _segment_rect_core


def point_segment(p, a, b):
    """点到线段最短距离（退化：a==b 时为点距）。"""
    return _point_segment_fast(p[0], p[1], a[0], a[1], b[0], b[1])


def segment_segment(p1, p2, p3, p4):
    """线段对最短距离。相交返回 0.0；共线重叠返回 0.0；擦边（端点接触）返回 0.0。"""
    return _segment_segment_fast(p1[0], p1[1], p2[0], p2[1],
                                 p3[0], p3[1], p4[0], p4[1])


def polyline(points):
    """折线两两相邻段列表。"""
    return list(zip(points[:-1], points[1:]))


def polyline_polyline(pts_a, pts_b):
    return min(segment_segment(a1, a2, b1, b2)
               for a1, a2 in polyline(pts_a) for b1, b2 in polyline(pts_b))


def segment_rect_distance(a, b, rect):
    """线段到轴对齐矩形的最短距离（矩形内/边上为 0）。
    R1 性能件：端点在矩形内先判早退——与原实现（先算四角段距离再清零）
    返回值逐位相同：内=0.0（原亦清零为 0.0），外=四段 min（原样）；
    判定语义零变化（perf/PROFILE-R1.md §8.3）。"""
    return _segment_rect_fast(a[0], a[1], b[0], b[1],
                              rect["x_min"], rect["y_min"],
                              rect["x_max"], rect["y_max"])


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
