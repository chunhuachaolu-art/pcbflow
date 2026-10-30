# -*- coding: utf-8 -*-
"""v5.drc —— DRC authority 唯一内部实现（任务书 A9，U7 混合案内源）。

全工程唯一的间距/违例判定：validator、席位 harness、执行器、SVG 视图一律调用本模块，
禁止任何并行/旁路实现（静态扫描测试化）。判定带模块版本号进证据链。
外权威 = kicad-cli DRC（P5 验收口径，不在本模块）。

几何原语取自 v5.metrics.clearance；本模块是唯一把几何事实升格为违例判定的地方。
"""
import math

from .metrics import clearance, envelope

# OPT-04 第一刀（EXEC-R2）：几何语义声明接线——仅登记+版本可查出口，不触
# 下方任何判定/带值/容差实现（薄委托契约见 geometry_semantics 模块 docstring；
# executor 席接线由 OPT-09 单写者负责）。
from . import geometry_semantics as _geometry_semantics   # noqa: E402
_geometry_semantics.declare_consumer("drc")               # 幂等登记
GEOMETRY_SEMANTICS_VERSION = _geometry_semantics.VERSION  # 消费方可验出口

VERSION = "v5.drc/0.4.0"   # 0.4.0=V5-R7：R5 per-netclass 网对取值（max(class_a,
                           # class_b)，中心线口径不变）+ net_classes 单源归一/
                           # 取值助手 + 真实板轮廓边距带 OutlineBand（W-3；矩形
                           # 外环⇒与 workspace 矩形带逐位同式=缺省路径零漂移）
                           # （0.3.0=V5-D8 板固孔；0.2.0=P5⑥ D6-3 edge；0.1.0=P4）


class Violation:
    def __init__(self, rule, subject_a, subject_b, data):
        self.rule = rule
        self.subject_a = subject_a
        self.subject_b = subject_b
        self.data = data

    def as_dict(self):
        return {
            "rule": self.rule,
            "subjects": [self.subject_a, self.subject_b],
            "data": self.data,
        }


class DRCReport:
    def __init__(self, violations, checked_pairs, drc_version=VERSION):
        self.violations = violations
        self.checked_pairs = checked_pairs
        self.drc_version = drc_version

    @property
    def clean(self):
        return not self.violations

    def as_dict(self):
        return {
            "drc_version": self.drc_version,
            "clean": self.clean,
            "violation_count": len(self.violations),
            "checked_pairs": self.checked_pairs,
            "violations": [v.as_dict() for v in self.violations],
        }


# ---------------------------------------------------------------- 铜几何视图

class Copper:
    """一个铜元素：折线（带半宽）或焊盘（圆）或矩形带。layer 必填；同层才做 R5。"""

    def __init__(self, net_id, cid, layer, polyline=None, pad=None, band=None,
                 half_width=0.1):
        self.net_id = net_id
        self.cid = cid
        self.layer = layer
        self.polyline = polyline
        self.pad = pad          # (center, radius)
        self.band = band        # (x0, y0, x1, y1)
        self.half_width = half_width

    def as_rect(self):
        """实际铜外接矩形（非包络）。"""
        pts = []
        if self.polyline:
            pts.extend(self.polyline)
        if self.pad:
            (cx, cy), r = self.pad
            pts.extend([(cx - r, cy - r), (cx + r, cy + r)])
        if self.band:
            pts.extend([(self.band[0], self.band[1]), (self.band[2], self.band[3])])
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def envelope(self, margin=envelope.DEFAULT_MARGIN):
        return envelope.expand_rect(self.as_rect(), margin)


def _cu_rect(cu):
    """铜外接矩形缓存（R1 性能件：铜几何不可变，缓存=同值复用，零舍入差异）。"""
    r = getattr(cu, "_perf_rect", None)
    if r is None:
        r = cu.as_rect()
        try:
            cu._perf_rect = r
        except AttributeError:
            pass
    return r


def _cu_seg_bbs(cu):
    """折线逐段包围盒缓存（R1 性能件；纯 min/max 零舍入，下界剪枝用）。"""
    if not cu.polyline:
        return None
    bbs = getattr(cu, "_perf_segbbs", None)
    if bbs is None:
        pts = cu.polyline
        bbs = [(min(a[0], b[0]), min(a[1], b[1]),
                max(a[0], b[0]), max(a[1], b[1]))
               for a, b in zip(pts[:-1], pts[1:])]
        try:
            cu._perf_segbbs = bbs
        except AttributeError:
            pass
    return bbs


_PRUNE_SLACK = 1e-12   # R1 性能件：下界剪枝安全裕度（≫rect_rect_gap 舍入上
                       # 偏差 ~1e-15；被剪段真距离必 > 当前最优 → min 逐位不变；
                       # 等价论证见 perf/PERF-R1-REPORT.md）


def _actual_gap(cu_a, cu_b):
    """两铜元素实际最小间隙（浮点确定）。跨层返回 None（层间由叠层介质保证）。
    R1 性能件：折线三分支以段级包围盒 rect_rect_gap 精确下界剪枝（距离原语
    与 min 选取序不变，min 结果逐位相同）。"""
    if cu_a.layer != cu_b.layer:
        return None
    if cu_a.band and cu_b.band:
        return clearance.rect_rect_gap(cu_a.band, cu_b.band)
    if cu_a.pad and cu_b.pad:
        (c1, r1), (c2, r2) = cu_a.pad, cu_b.pad
        return clearance.pad_pad_distance(c1, r1, c2, r2)
    if cu_a.pad and cu_b.polyline:
        (c, r), pts = cu_a.pad, cu_b.polyline
        best = float("inf")
        bb = (c[0], c[1], c[0], c[1])   # 圆心=退化矩形（下界=点到段 bbox 距）
        thresh = None
        for (a, b), sb in zip(clearance.polyline(pts), _cu_seg_bbs(cu_b)):
            # D-ORACLE-1（V6-ANCHOR-R1 批内发现+修复）: 距离原语=点到段−r,
            # 剪枝下界须同为 rect_rect_gap−r; 原实现漏减 r 致 bbox 距 ∈
            # [best, best+r) 的更近段被误剪（min 高估、违例漏判）。
            if thresh is not None and \
                    clearance.rect_rect_gap(bb, sb) - r >= thresh:
                continue
            d = clearance.pad_segment_distance(c, r, a, b)
            if d < best:
                best = d
                thresh = best + _PRUNE_SLACK
        return best
    if cu_a.polyline and cu_b.pad:
        return _actual_gap(cu_b, cu_a)
    if cu_a.polyline and cu_b.band:
        band_d = {"x_min": cu_b.band[0], "y_min": cu_b.band[1],
                  "x_max": cu_b.band[2], "y_max": cu_b.band[3]}
        band_t = (band_d["x_min"], band_d["y_min"],
                  band_d["x_max"], band_d["y_max"])
        best = float("inf")
        thresh = None
        for (a, b), sb in zip(clearance.polyline(cu_a.polyline),
                              _cu_seg_bbs(cu_a)):
            if thresh is not None and \
                    clearance.rect_rect_gap(sb, band_t) >= thresh:
                continue
            d = clearance.segment_rect_distance(a, b, band_d)
            if d < best:
                best = d
                thresh = best + _PRUNE_SLACK
        return best
    if cu_a.band and cu_b.polyline:
        return _actual_gap(cu_b, cu_a)
    if cu_a.polyline and cu_b.polyline:
        bbs_a = _cu_seg_bbs(cu_a)
        bbs_b = _cu_seg_bbs(cu_b)
        rb = _cu_rect(cu_b)
        best = float("inf")
        thresh = None
        for (a1, a2), sa in zip(clearance.polyline(cu_a.polyline), bbs_a):
            if thresh is not None and clearance.rect_rect_gap(sa, rb) >= thresh:
                continue   # 整段 a 对 b 整线下界已 ≥ best+slack → 全 b 段可剪
            for (b1, b2), sb in zip(clearance.polyline(cu_b.polyline), bbs_b):
                if thresh is not None and \
                        clearance.rect_rect_gap(sa, sb) >= thresh:
                    continue
                d = clearance.segment_segment(a1, a2, b1, b2)
                if d < best:
                    best = d
                    thresh = best + _PRUNE_SLACK
        return best
    if cu_a.pad and cu_b.band:
        return clearance.pad_rect_distance(cu_a.pad[0], cu_a.pad[1],
                                           {"x_min": cu_b.band[0], "y_min": cu_b.band[1],
                                            "x_max": cu_b.band[2], "y_max": cu_b.band[3]})
    if cu_a.band and cu_b.pad:
        return _actual_gap(cu_b, cu_a)
    raise ValueError("不支持的铜几何对: %s/%s" % (cu_a.cid, cu_b.cid))


# ---------------------------------------------------------------- net class（V5-R7 W-2）

def normalize_net_classes(net_classes):
    """board.net_classes → {name: {"clearance_mm": f, "width_mm": f,
    "members": tuple(sorted)}}（单源归一口；消费面 fail-closed）。

    形状/数值非法（非 dict 项、clearance_mm/width_mm 缺或非 ≥0 有限数值、
    members 非 str 列表、项缺三键）抛 ValueError。幂等：members 容 list/tuple
    （本口产物 tuple 可再入）。schema 只能表达「是对象」
    （schema_loader 无 patternProperties 面，topology 同例），per-class 结构由
    本口单源核。None/{} → {}（缺省=缺省类=R5 标量语义，零漂移）。"""
    if net_classes is None:
        return {}
    if not isinstance(net_classes, dict):
        raise ValueError("net_classes 须为对象 {name→class}，实得 %s"
                         % type(net_classes).__name__)
    out = {}
    for name, cls in net_classes.items():
        if not isinstance(name, str) or not name:
            raise ValueError("net_classes 键须为非空字符串，实得 %r" % (name,))
        if not isinstance(cls, dict):
            raise ValueError("net_classes[%r] 须为对象，实得 %s"
                             % (name, type(cls).__name__))
        vals = {}
        for key in ("clearance_mm", "width_mm"):
            v = cls.get(key)
            if (not isinstance(v, (int, float)) or isinstance(v, bool)
                    or not math.isfinite(float(v)) or float(v) < 0.0):
                raise ValueError("net_classes[%r].%s 须为 ≥0 有限数值，实得 %r"
                                 % (name, key, v))
            vals[key] = float(v)
        members = cls.get("members")
        if not isinstance(members, (list, tuple)) or not all(
                isinstance(m, str) and m for m in members):
            raise ValueError("net_classes[%r].members 须为非空字符串列表，实得 %r"
                             % (name, members))
        if len(set(members)) != len(members):
            raise ValueError("net_classes[%r].members 成员重复: %r"
                             % (name, sorted(m for m in set(members)
                                             if members.count(m) > 1)))
        out[name] = {"clearance_mm": vals["clearance_mm"],
                     "width_mm": vals["width_mm"],
                     "members": tuple(sorted(members))}
    return out


def net_clearance_map(nc_normalized, default_mm):
    """归一 net_classes → {net_id: 有效间距}（仅 ≥1 类成员网；多类=其类 max，
    同 KiCad 多净类指派语义）。无类网不入 map（消费方以 default_mm 兜底）。"""
    out = {}
    for cls in nc_normalized.values():
        c = cls["clearance_mm"]
        for net in cls["members"]:
            if net not in out or c > out[net]:
                out[net] = c
    return out


def max_net_class_clearance(nc_normalized, default_mm):
    """保守障碍栅格取值（任务书 §4 风险②首版口径）：max(缺省, 全类 clearance)。

    executor 障碍膨胀/via 膨胀/D3 孔心距用它（只紧不松：任何网对所需间距 ≤
    该值）。nc 为空 ⇒ 原样返回 default_mm（缺省路径逐位零漂移）。"""
    best = float(default_mm)
    for cls in nc_normalized.values():
        if cls["clearance_mm"] > best:
            best = cls["clearance_mm"]
    return best


# ---------------------------------------------------------------- 判定（唯一源）

def check_clearance(coppers, min_clearance_mm, same_net_exempt=True,
                    net_clearance=None):
    """R5：任意两个不同网络同层铜（含焊盘）间距 ≥ 所需间距（中心线口径）。

    V5-R7 W-2：net_clearance（net_clearance_map 产物）在场时所需间距=网对
    两侧有效间距的 max（无类网=min_clearance_mm=缺省类）；violation data 的
    required_mm=网对值。None ⇒ 全对 min_clearance_mm（缺省路径，与 0.3.0
    逐位一致——分支与比较序零改动）。
    擦边（距离恰好 == 所需间距）合规；"<" 才违例。
    R1 性能件：对级 bbox 精确下界预滤——rect_rect_gap(as_rect_a, as_rect_b)
    ≥ 所需-EPS+SLACK 的对不可能违例（真间隙 ≥ 下界-舍入差 > 阈值），
    跳过 _actual_gap；checked 计数由「gap 为 None ⟺ 跨层」单独维护（与原
    逐对计数逐位一致），违例对的枚举序（i<j 字典序）与 gap 浮点值不变，
    violation data（round(gap,10)）逐位一致。
    """
    violations = []
    checked = 0
    coppers = list(coppers)
    nonviol_lb = min_clearance_mm - clearance.EPS + _PRUNE_SLACK
    for i in range(len(coppers)):
        a = coppers[i]
        ra = _cu_rect(a)
        for j in range(i + 1, len(coppers)):
            b = coppers[j]
            if same_net_exempt and a.net_id == b.net_id:
                continue
            if a.layer != b.layer:
                continue   # gap=None 情形（原口径：跨层不计 checked）
            checked += 1
            required = min_clearance_mm
            if net_clearance is not None:
                ta = net_clearance.get(a.net_id, min_clearance_mm)
                tb = net_clearance.get(b.net_id, min_clearance_mm)
                required = ta if ta >= tb else tb
                lb = required - clearance.EPS + _PRUNE_SLACK
            else:
                lb = nonviol_lb
            if clearance.rect_rect_gap(ra, _cu_rect(b)) >= lb:
                continue   # 对级预滤：下界已合规 → 不可能违例
            gap = _actual_gap(a, b)
            if gap < required - clearance.EPS:
                violations.append(Violation(
                    "R5", a.cid, b.cid,
                    {"gap_mm": round(gap, 10), "required_mm": required,
                     "layer": a.layer}))
    return violations, checked


def check_envelope_overlap(coppers, margin=envelope.DEFAULT_MARGIN, min_clearance_mm=0.5):
    """保守包络叠加扫描（诊断性质，非违例）：返回重叠对与伪影标记。

    包络重叠不代表实际冲突（外扩伪影），是否真违例须以 check_clearance 为准；
    伪影=包络响警但实际间隙 ≥ min_clearance（真冲突不存在）。
    """
    overlaps = []
    coppers = list(coppers)
    for i in range(len(coppers)):
        for j in range(i + 1, len(coppers)):
            a, b = coppers[i], coppers[j]
            if a.net_id == b.net_id or a.layer != b.layer:
                continue
            ea, eb = a.envelope(margin), b.envelope(margin)
            if envelope.envelopes_overlap(ea, eb):
                gap = _actual_gap(a, b)
                is_artifact = gap is not None and gap >= min_clearance_mm - clearance.EPS
                overlaps.append({
                    "subjects": [a.cid, b.cid],
                    "layer": a.layer,
                    "overlap_depth_mm": round(envelope.envelope_overlap_depth(ea, eb), 10),
                    "actual_gap_mm": None if gap is None else round(gap, 10),
                    "artifact": is_artifact,
                })
    return overlaps


def check_ana_proximity(coppers, sensitive_rects, min_distance_mm, max_parallel_mm):
    """R2：信号铜与敏感区边界距离 < min_distance 且累计平行长度 > max_parallel → 违例。"""
    violations = []
    for cu in coppers:
        if not cu.polyline:
            continue
        for rect_id, rect in sensitive_rects:
            nearest = min(clearance.segment_rect_distance(a, b, rect)
                          for a, b in clearance.polyline(cu.polyline))
            if nearest >= min_distance_mm:
                continue
            parallel = 0.0
            for a, b in clearance.polyline(cu.polyline):
                if abs(a[0] - b[0]) <= clearance.EPS:
                    # 垂直段：与敏感区 y 跨投影求交（平行于竖直边界）
                    lo, hi = sorted((a[1], b[1]))
                    overlap = min(hi, rect["y_max"]) - max(lo, rect["y_min"])
                    if overlap > 0:
                        parallel += overlap
                if abs(a[1] - b[1]) <= clearance.EPS:
                    # 水平段：与敏感区 x 跨投影求交（平行于水平边界）
                    lo, hi = sorted((a[0], b[0]))
                    overlap = min(hi, rect["x_max"]) - max(lo, rect["x_min"])
                    if overlap > 0:
                        parallel += overlap
            if parallel > max_parallel_mm:
                violations.append(Violation(
                    "R2", cu.cid, rect_id,
                    {"distance_mm": round(nearest, 10), "required_mm": min_distance_mm,
                     "parallel_mm": round(parallel, 10), "max_parallel_mm": max_parallel_mm}))
    return violations


def check_width(planned_width, required_min_mm, partition_id):
    """R1：电源网线宽 < 载流下限 → 违例（判定语义唯一源）。"""
    if planned_width < required_min_mm - clearance.EPS:
        return Violation("R1", partition_id, None,
                         {"planned_mm": planned_width, "required_min_mm": required_min_mm})
    return None


def check_capacity(occupancy_mm, capacity_mm, corridor_id):
    """走廊溢出判定（占用核算事实来自 metrics.capacity）。"""
    if occupancy_mm > capacity_mm + clearance.EPS:
        return Violation("capacity", corridor_id, None,
                         {"occupancy_mm": occupancy_mm, "capacity_mm": capacity_mm})
    return None


def check_keepout(coppers, keepout_rects, plane_layers=()):
    """R6：铜落在禁布区/plane 层 → 违例。"""
    violations = []
    for cu in coppers:
        if cu.layer in plane_layers:
            violations.append(Violation("R6", cu.cid, "plane:" + cu.layer, {"layer": cu.layer}))
            continue
        rect = cu.as_rect()
        for rect_id, ko in keepout_rects:
            if clearance.rect_rect_gap(rect, ko) <= 0.0:
                violations.append(Violation("R6", cu.cid, rect_id,
                                            {"layer": cu.layer, "keepout": list(ko)}))
    return violations


# ---------------------------------------------------------------- 板边距（P5⑥ D6-3）

#: 轮廓带栅格化网格边长（mm）：边登记进整数格桶，查询取点周 3×3 桶候边精判
#: （≥EDGE_CLEARANCE_MM ⇒ 距点 <margin 的边必在候选集；超集预选+解析精判，
#: 与 executor._build_spatial 粗网格同构=R5-W0 栅格化选型同构）。
OUTLINE_GRID_CELL = 2.0
#: 轮廓 containment 判定的弧离散弦数（sub-µm 级弦高；贴边行为由解析距离判定
#: 主导，离散只影响远离边界处的内外归属，量级披露于此）。
OUTLINE_RAY_CHORDS = 64
_TAU = 2.0 * math.pi


def _arc_geometry(s, m, e):
    """三点弧 → (center_x, center_y, r, a0, a1, ccw)；共线/退化 → None。"""
    d = 2.0 * (s[0] * (m[1] - e[1]) + m[0] * (e[1] - s[1]) + e[0] * (s[1] - m[1]))
    if d == 0.0 or not math.isfinite(d):
        return None
    r1 = s[0] * s[0] + s[1] * s[1]
    rm = m[0] * m[0] + m[1] * m[1]
    re_ = e[0] * e[0] + e[1] * e[1]
    ux = (r1 * (m[1] - e[1]) + rm * (e[1] - s[1]) + re_ * (s[1] - m[1])) / d
    uy = (r1 * (e[0] - m[0]) + rm * (s[0] - e[0]) + re_ * (m[0] - s[0])) / d
    r = math.hypot(s[0] - ux, s[1] - uy)
    if not (math.isfinite(ux) and math.isfinite(uy) and math.isfinite(r)) \
            or r > 1e9:
        return None
    a0 = math.atan2(s[1] - uy, s[0] - ux)
    am = math.atan2(m[1] - uy, m[0] - ux)
    a1 = math.atan2(e[1] - uy, e[0] - ux)
    ccw = ((am - a0) % _TAU) <= ((a1 - a0) % _TAU)
    return (ux, uy, r, a0, a1, ccw)


def _angle_on_arc(angle, a0, a1, ccw):
    """angle 是否落在 a0→a1 弧扫掠内（端点含）。"""
    if ccw:
        return ((angle - a0) % _TAU) <= ((a1 - a0) % _TAU)
    return ((a0 - angle) % _TAU) <= ((a0 - a1) % _TAU)


def _point_arc_distance(p, s, m, e):
    """点到三点弧的精确距离（角在扫掠内=|心距−r|；否则到近端点）。"""
    g = _arc_geometry(s, m, e)
    if g is None:
        return clearance.point_segment(p, s, e)
    ux, uy, r, a0, a1, ccw = g
    ap = math.atan2(p[1] - uy, p[0] - ux)
    if _angle_on_arc(ap, a0, a1, ccw):
        return abs(math.hypot(p[0] - ux, p[1] - uy) - r)
    return min(clearance.point_point(p, s), clearance.point_point(p, e))


def _edge_point_distance(p, edge):
    """点到轮廓边的距离（segment=点段距；arc=解析弧距）。"""
    if edge[0] == "segment":
        return clearance.point_segment(p, edge[1], edge[2])
    return _point_arc_distance(p, edge[1], edge[2], edge[3])


def _edge_chords(edge, k=OUTLINE_RAY_CHORDS):
    """边 → k 弦折线顶点列（首尾钉端点；containment 射线法用）。"""
    if edge[0] == "segment":
        return [edge[1], edge[2]]
    s, m, e = edge[1], edge[2], edge[3]
    g = _arc_geometry(s, m, e)
    if g is None:
        return [s, e]
    ux, uy, r, a0, a1, ccw = g
    span = ((a1 - a0) % _TAU) if ccw else ((a0 - a1) % _TAU)
    sign = 1.0 if ccw else -1.0
    pts = [s]
    for t in range(1, k):
        ang = a0 + sign * span * (t / k)
        pts.append((ux + r * math.cos(ang), uy + r * math.sin(ang)))
    pts.append(e)
    return pts


def _point_in_poly(p, poly_pts):
    """射线法（含边界=在内；水平右向射线，纯比较确定）。"""
    n = len(poly_pts)
    for i in range(n):
        a, b = poly_pts[i], poly_pts[(i + 1) % n]
        if _on_poly_seg(a, b, p):
            return True
    inside = False
    for i in range(n):
        a, b = poly_pts[i], poly_pts[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return inside


def _on_poly_seg(a, b, p):
    """p 在线段 ab 上（容差 1e-12）。"""
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > 1e-12:
        return False
    return (min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12
            and min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12)


def _outline_edge_from_json(item, path):
    """outline_mm 元素 dict → 边元组（"segment"/"arc"）；结构非法 ValueError。"""
    if not isinstance(item, dict):
        raise ValueError("%s 须为对象，实得 %s" % (path, type(item).__name__))
    typ = item.get("type")
    if typ not in ("segment", "arc"):
        raise ValueError("%s.type 须为 segment|arc，实得 %r" % (path, typ))
    def _pt(key, required=True):
        v = item.get(key)
        if v is None and not required:
            return None
        if (not isinstance(v, (list, tuple)) or len(v) != 2
                or not all(isinstance(c, (int, float)) and not isinstance(c, bool)
                           and math.isfinite(float(c)) for c in v)):
            raise ValueError("%s.%s 须为 [x, y] 有限数值对，实得 %r"
                             % (path, key, v))
        return (float(v[0]), float(v[1]))
    s = _pt("start_mm")
    e = _pt("end_mm")
    if typ == "arc":
        m = _pt("mid_mm")
        return ("arc", s, m, e)
    return ("segment", s, e)


def _outline_loop_from_json(items, path, chain_tol):
    """outline_mm 环（元素列）→ 边元组列；链接闭合校验（容差 chain_tol）。"""
    if not isinstance(items, list) or len(items) < 3:
        raise ValueError("%s 须为 ≥3 元素的环列表（schema minItems=3 同式），"
                         "实得 %s 项" % (path, len(items) if isinstance(items, list)
                                          else type(items).__name__))
    edges = [_outline_edge_from_json(it, "%s[%d]" % (path, i))
             for i, it in enumerate(items)]
    for i in range(len(edges)):
        nxt = edges[(i + 1) % len(edges)]
        if math.hypot(edges[i][-1][0] - nxt[1][0],
                      edges[i][-1][1] - nxt[1][1]) > chain_tol:
            raise ValueError("%s[%d] 终点与下一元素起点断链（bad outline，"
                             "容差 %g mm）" % (path, i, chain_tol))
    return tuple(edges)


def _edge_reg_bbox(edge):
    """边 → 登记桶用 bbox（段=端点框；弧=三端点+扫掠内轴向极值的精确外接框
    ——弦折线在弧凸侧之内、会低估外扩，登记框取解析极值防漏登记）。"""
    pts = [edge[1], edge[-1]]
    if edge[0] == "segment":
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))
    s, m, e = edge[1], edge[2], edge[3]
    g = _arc_geometry(s, m, e)
    if g is None:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))
    ux, uy, r, a0, a1, ccw = g
    for k in range(4):
        ang = k * (math.pi / 2.0)
        if _angle_on_arc(ang, a0, a1, ccw):
            pts.append((ux + r * math.cos(ang), uy + r * math.sin(ang)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def normalize_outline(outline_mm, chain_tol=1e-4):
    """board.outline_mm → {"outer": (边...), "holes": [(边...),...]}（单源归一）。

    结构/链接闭合校验 fail-closed（ValueError；adapter 产出的 outline 已过
    更强校验——自交/孔嵌套在源侧把门，消费侧双保险校形状+闭合）。"""
    if not isinstance(outline_mm, dict):
        raise ValueError("outline_mm 须为对象 {outer, holes}，实得 %s"
                         % type(outline_mm).__name__)
    outer = _outline_loop_from_json(outline_mm.get("outer"), "outline_mm.outer",
                                    chain_tol)
    holes_raw = outline_mm.get("holes")
    if not isinstance(holes_raw, list):
        raise ValueError("outline_mm.holes 须为环列表，实得 %s"
                         % type(holes_raw).__name__)
    holes = tuple(_outline_loop_from_json(h, "outline_mm.holes[%d]" % i,
                                          chain_tol)
                  for i, h in enumerate(holes_raw))
    return {"outer": outer, "holes": holes}


class OutlineBand:
    """板轮廓边距带（V5-R7 W-3，判定单源）：判定点 p 入带 ⟺ p 出板（外环外或
    孔环内）或 p 到任一轮廓边距离 < margin−EPS（双侧带；与 edge_inner_rect 的
    擦边口径同向）。

    栅格化掩码：全部边按 OUTLINE_GRID_CELL 整数格桶登记（bbox 覆盖格），查询
    取点周 3×3 桶候边做解析距离精判（段=point_segment、弧=外接圆解析）；超集
    预选+精确判定=executor 粗网格同构（R5-W0 栅格化选型同构）。containment
    （外环内/孔环外）=离散折线（OUTLINE_RAY_CHORDS 弦）射线法。**零漂移机制**：
    矩形外环（4 段轴对齐）下 point_blocked 与 workspace 矩形带逐位同式——内
    侧距离=轴距离精确、外侧点=containment 拒绝（等价旧内矩形越界判定）。"""

    def __init__(self, outline):
        if not isinstance(outline, dict) or "outer" not in outline:
            raise ValueError("OutlineBand 须取 normalize_outline 产物")
        self.outer = outline["outer"]
        self.holes = tuple(outline.get("holes", ()))
        self._edges = tuple(self.outer) + tuple(
            e for h in self.holes for e in h)
        cell = OUTLINE_GRID_CELL
        self._cell = cell
        grid = {}
        for idx, edge in enumerate(self._edges):
            x0, y0, x1, y1 = _edge_reg_bbox(edge)
            for cx in range(int(math.floor(x0 / cell)),
                            int(math.floor(x1 / cell)) + 1):
                for cy in range(int(math.floor(y0 / cell)),
                                int(math.floor(y1 / cell)) + 1):
                    grid.setdefault((cx, cy), []).append(idx)
        self._grid = grid
        self._outer_poly = self._loop_poly(self.outer)
        self._hole_polys = [self._loop_poly(h) for h in self.holes]

    @staticmethod
    def _loop_poly(loop):
        pts = []
        for edge in loop:
            chords = _edge_chords(edge)
            pts.extend(chords[:-1])   # 末点=下一起点，去重拼接
        return pts

    def _candidates(self, p):
        cell = self._cell
        cx = int(math.floor(p[0] / cell))
        cy = int(math.floor(p[1] / cell))
        seen = set()
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for idx in self._grid.get((cx + dx, cy + dy), ()):
                    if idx not in seen:
                        seen.add(idx)
                        out.append(idx)
        return out

    def point_blocked(self, p, margin_mm=None):
        """判定点是否入带（出板或距边 <margin−EPS；margin 缺省=带值单源）。"""
        if margin_mm is None:
            margin_mm = EDGE_CLEARANCE_MM
        pt = (float(p[0]), float(p[1]))
        if not _point_in_poly(pt, self._outer_poly):
            return True
        for poly in self._hole_polys:
            if _point_in_poly(pt, poly):
                return True
        thresh = margin_mm - clearance.EPS
        for idx in self._candidates(pt):
            if _edge_point_distance(pt, self._edges[idx]) < thresh:
                return True
        return False


EDGE_CLEARANCE_MM = 0.2
# D6-3 带值（合同钉值，用户 2026-09-16 照准）：= kicad-cli 生效缺省
# copper_edge_clearance 0.2mm。board.json **现无**显式边距规则字段（考证
# 2026-09-17：schemas/board.v1.schema.json 顶层键与 hard_rules 仅 R1..R6、
# 唯一 clearance 键为 R5 netclass min_clearance_mm；v5/board.py 同查无命中），
# 故为常量单源；执行/检查两侧同值同源（避免新 config-gap）。板 json 若未来
# 落显式边距字段，由此处改为读取（板值优先），调用方合同不变。


def edge_inner_rect(workspace, margin_mm=EDGE_CLEARANCE_MM):
    """workspace 内缩 margin_mm 的内矩形；禁布带 = workspace − 内矩形 环带。

    轮廓唯一源 = workspace 矩形（board.py:40-45 校验，kicad_export.py:698
    gr_rect@Edge.Cuts 同源转录）——禁止第二轮廓源。内矩形凸 ⇒ 折线段触带
    ⟺ 端点触带、矩形带触带 ⟺ 角点触带（逐点判定完备，无需逐段求交）。
    workspace 任一边长 ≤ 2·margin 时内矩形退化反转，任何判定点均违例
    （保守方向=fail-closed，与 R5 擦边口径同向）。"""
    x0, y0, x1, y1 = (float(v) for v in workspace)
    m = float(margin_mm)
    return (x0 + m, y0 + m, x1 - m, y1 - m)


def _edge_points_of(cu):
    """铜的边距判定点集（中心线口径）：折线=顶点、矩形带=角点、焊盘=圆心。
    与 v5 世界模型的中心线 R5 口径同族（铜以中心线/中心点入模，物理展宽由
    half_width/半径另计——边距带只钉中心线，物理铜缘口径差归 D6-4 分类器
    披露，不在本判定内引入第二几何）。"""
    if cu.polyline:
        return [(float(p[0]), float(p[1])) for p in cu.polyline]
    if cu.band is not None:
        return [(float(cu.band[0]), float(cu.band[1])),
                (float(cu.band[2]), float(cu.band[1])),
                (float(cu.band[0]), float(cu.band[3])),
                (float(cu.band[2]), float(cu.band[3]))]
    if cu.pad is not None:
        (c, _r) = cu.pad
        return [(float(c[0]), float(c[1]))]
    return []


def check_edge_clearance(coppers, workspace, margin_mm=EDGE_CLEARANCE_MM,
                         outline_band=None):
    """D6-3：铜判定点落入板边禁布带 → 违例（rule="edge_clearance"）。

    禁布带（V5-R7 W-3 起双源）：outline_band（OutlineBand，真实板轮廓
    board.outline_mm）在场 ⇒ 轮廓带（出板/入孔/距边 <margin−EPS，判定单源
    =OutlineBand.point_blocked——矩形外环与 workspace 矩形带逐位同式）；
    否则 = workspace 内缩 margin_mm 环带（edge_inner_rect，缺省路径零漂移）。
    擦边（判定点距边恰 = margin_mm）合规、"<" 才违例（与 check_clearance
    的 R5 口径一致）。全信号层同带（层间无差，调用方无需逐层过滤——plane
    层铜本属 R6 违例，此处照判不豁免）。逐违例点一枚 Violation（data.pos
    供 route_check edge_violations 消费接口映射与 D6-4 同位归责）；序 =
    输入序 × 点序，确定性。独立判定器（不入 check_all 聚合——编排层是否
    升格为可行门由 route_check/executor 的 D6-3 落点决定，见各自 docstring）。"""
    if outline_band is not None:
        violations = []
        for cu in coppers:
            for (x, y) in _edge_points_of(cu):
                if outline_band.point_blocked((x, y), margin_mm):
                    violations.append(Violation(
                        "edge_clearance", cu.cid, "board-edge",
                        {"pos": [x, y], "net_id": cu.net_id,
                         "layer": cu.layer, "margin_mm": float(margin_mm)}))
        return violations
    ix0, iy0, ix1, iy1 = edge_inner_rect(workspace, margin_mm)
    violations = []
    for cu in coppers:
        for (x, y) in _edge_points_of(cu):
            if (x < ix0 - clearance.EPS or x > ix1 + clearance.EPS
                    or y < iy0 - clearance.EPS or y > iy1 + clearance.EPS):
                violations.append(Violation(
                    "edge_clearance", cu.cid, "board-edge",
                    {"pos": [x, y], "net_id": cu.net_id, "layer": cu.layer,
                     "margin_mm": float(margin_mm)}))
    return violations


# ---------------------------------------------------------------- 板固孔禁布（V5-D8）

HOLE_TO_HOLE_MM = 0.25
# D8 带值（合同钉值，用户 2026-09-22 裁定③）：= kicad-cli 生效缺省
# hole_to_hole 0.25mm。board.json **现无**显式孔距规则字段（考证 2026-09-22：
# schemas/board.v1.schema.json hard_rules 仅 R1..R6、唯一间距键 R5
# min_clearance_mm[netclass] 与 copper_edge_clearance 族均无孔-孔键；本件
# schema 扩展仅增 holes 数据键、未增规则键），故为常量单源；执行/检查两侧
# 同值同源（避免新 config-gap）。板 json 若未来落显式孔距规则字段，由此处
# 改为读取（板值优先），调用方合同不变（D6-3 同构）。
#
# 口径披露（PREREG-D8 §2.3 冻结）：kicad hole_to_hole 判钻孔对（引擎过孔取
# 钻半径=drill/2，缺省 0.15）；v5 世界模型过孔只有铜盘半径 via_r
# （=drill/2+annular，缺省 0.3）——v5 侧判式用 via_r 恒 ≥ kicad 判式
# （单向保守 0.15mm 豁免带宽：v5 拒的 kicad 必不放过，反之不保证）。


def normalize_holes(board_holes):
    """board.holes[] → [(x, y, r)] 归一（判定/消费单源）。

    r = drill_mm/2（adapter 侧已收口：oval 项 drill_mm=max(a,b) 保守外接圆）。
    输入 None/[] → []（旧语义=空清单，零行为）。非法项（drill_mm≤0/pos 非
    数值）fail-closed 抛 ValueError（schema 校验之上双保险，判定侧零静默）。"""
    out = []
    for h in board_holes or []:
        d = float(h["drill_mm"])
        if not (d > 0.0):
            raise ValueError("holes[].drill_mm 非正 %r（fail-closed）" % (d,))
        out.append((float(h["pos_mm"][0]), float(h["pos_mm"][1]), d / 2.0))
    return out


def hole_via_blocked(hole_pos, hole_r, via_pt, via_r,
                     margin_mm=HOLE_TO_HOLE_MM):
    """谓词（判定单源）：引擎过孔铜盘 (via_pt, via_r) 是否触板固孔 (hole_pos,
    hole_r) 禁布带——point_point < hole_r + margin + via_r 即真。

    消费方：executor.via_blocked（障碍面零豁免）、route_check hole_violations
    复核面（同式）。零同网豁免（板固孔无网信息；kicad hole_to_hole 同网不
    豁免，wave6 14 条违例全为引擎过孔 vs 同网板固 PTH 实证口径）。"""
    return clearance.point_point(hole_pos, via_pt) \
        < hole_r + margin_mm + via_r - clearance.EPS


def hole_track_blocked(hole_pos, hole_r, p, q, half_width,
                       margin_mm=HOLE_TO_HOLE_MM):
    """谓词（判定单源）：走线段 (p,q)（半宽 half_width）是否触板固孔禁布带
    ——point_segment(hole_pos, p, q) < hole_r + margin + half_width 即真。

    消费方：executor.edge_blocked（障碍面；端点豁免由调用方先筛——见其
    docstring）、route_check hole_violations 复核面（同式同豁免）。"""
    return clearance.point_segment(hole_pos, p, q) \
        < hole_r + margin_mm + half_width - clearance.EPS


def hole_inherent_pairs(holes_norm, margin_mm=HOLE_TO_HOLE_MM):
    """板固有孔对披露（V5-D8 §2 分类 board-inherent 的几何事实源）：任两孔
    钻孔边缘距（心距−r1−r2）< 0.25 → 板设计固有、非布线可避。

    返回 [(i, j, edge_gap)]（i<j 输入序，edge_gap=round(心距−r1−r2, 10)，
    可为负），供分类器/报告披露；不入 engine 违例、不入判据二分子（用户
    裁定④口径）。O(n²)（n=板固孔数 ≤ 数百，一次性诊断，非热路径）。"""
    pairs = []
    for i in range(len(holes_norm)):
        xi, yi, ri = holes_norm[i]
        for j in range(i + 1, len(holes_norm)):
            xj, yj, rj = holes_norm[j]
            gap = clearance.point_point((xi, yi), (xj, yj)) - ri - rj
            if gap < margin_mm - clearance.EPS:
                pairs.append((i, j, round(gap, 10)))
    return pairs


def check_hole_keepout(holes_norm, via_points, via_r,
                       margin_mm=HOLE_TO_HOLE_MM):
    """engine 孔违例判定器（v5 权威自查；route_check 复核面消费）：
    引擎布线过孔点 vs 板固孔，hole_via_blocked 同式。

    via_points=[(net_id, partition_id, (x, y))]（routes 文档口径）；
    返回 Violation 列表（rule="hole_to_hole"，subjects=[via 主体, hole:i]，
    data 带 gap_mm/required_mm/两侧半径）。"""
    violations = []
    for net_id, pid, pt in via_points:
        for i, (hx, hy, hr) in enumerate(holes_norm):
            d = clearance.point_point((hx, hy), pt)
            if hole_via_blocked((hx, hy), hr, pt, via_r, margin_mm):
                violations.append(Violation(
                    "hole_to_hole", "via:%s:%s" % (net_id, pid), "hole:%d" % i,
                    {"gap_mm": round(d - hr - via_r, 10),
                     "required_mm": margin_mm,
                     "hole_r_mm": hr, "via_r_mm": via_r}))
    return violations


def check_all(coppers, hard_rules, sensitive_rects=(), keepout_rects=(),
              capacity_checks=(), width_checks=(), plane_layers=(),
              net_classes=None):
    """总检入口：R5 + R2 + R6 + capacity + R1（容量/宽度事实由调用方核算传入）。

    V5-R7 W-2：net_classes（board.net_classes 原始 dict）在场且非空 ⇒ R5 按
    网对类别取值（normalize_net_classes→net_clearance_map 单源）；None/空 ⇒
    R5 标量（缺省路径逐位零漂移）。返回 DRCReport（带模块版本号，进证据链）。
    """
    violations = []
    nc_map = net_clearance_map(normalize_net_classes(net_classes),
                               hard_rules["R5"]["min_clearance_mm"]) \
        if net_classes else None
    v5, checked = check_clearance(coppers, hard_rules["R5"]["min_clearance_mm"],
                                  net_clearance=nc_map)
    violations.extend(v5)
    violations.extend(check_ana_proximity(
        coppers, sensitive_rects,
        hard_rules["R2"]["min_distance_mm"], hard_rules["R2"]["max_parallel_mm"]))
    violations.extend(check_keepout(coppers, keepout_rects, plane_layers))
    for corridor_id, occ, cap in capacity_checks:
        v = check_capacity(occ, cap, corridor_id)
        if v:
            violations.append(v)
    for partition_id, planned, required in width_checks:
        v = check_width(planned, required, partition_id)
        if v:
            violations.append(v)
    return DRCReport(violations, checked)
