# -*- coding: utf-8 -*-
"""v5.drc —— DRC authority 唯一内部实现（任务书 A9，U7 混合案内源）。

全工程唯一的间距/违例判定：validator、席位 harness、执行器、SVG 视图一律调用本模块，
禁止任何并行/旁路实现（静态扫描测试化）。判定带模块版本号进证据链。
外权威 = kicad-cli DRC（P5 验收口径，不在本模块）。

几何原语取自 v5.metrics.clearance；本模块是唯一把几何事实升格为违例判定的地方。
"""
from .metrics import clearance, envelope

VERSION = "v5.drc/0.2.0"   # 0.2.0=P5⑥ D6-3：check_edge_clearance 板边距判定入权威
                           # （0.1.0=P4 首版）


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


def _actual_gap(cu_a, cu_b):
    """两铜元素实际最小间隙（浮点确定）。跨层返回 None（层间由叠层介质保证）。"""
    if cu_a.layer != cu_b.layer:
        return None
    if cu_a.band and cu_b.band:
        return clearance.rect_rect_gap(cu_a.band, cu_b.band)
    if cu_a.pad and cu_b.pad:
        (c1, r1), (c2, r2) = cu_a.pad, cu_b.pad
        return clearance.pad_pad_distance(c1, r1, c2, r2)
    if cu_a.pad and cu_b.polyline:
        (c, r), pts = cu_a.pad, cu_b.polyline
        return min(clearance.pad_segment_distance(c, r, a, b)
                   for a, b in clearance.polyline(pts))
    if cu_a.polyline and cu_b.pad:
        return _actual_gap(cu_b, cu_a)
    if cu_a.polyline and cu_b.band:
        return min(clearance.segment_rect_distance(a, b, {"x_min": cu_b.band[0],
                                                          "y_min": cu_b.band[1],
                                                          "x_max": cu_b.band[2],
                                                          "y_max": cu_b.band[3]})
                   for a, b in clearance.polyline(cu_a.polyline))
    if cu_a.band and cu_b.polyline:
        return _actual_gap(cu_b, cu_a)
    if cu_a.polyline and cu_b.polyline:
        return clearance.polyline_polyline(cu_a.polyline, cu_b.polyline)
    if cu_a.pad and cu_b.band:
        return clearance.pad_rect_distance(cu_a.pad[0], cu_a.pad[1],
                                           {"x_min": cu_b.band[0], "y_min": cu_b.band[1],
                                            "x_max": cu_b.band[2], "y_max": cu_b.band[3]})
    if cu_a.band and cu_b.pad:
        return _actual_gap(cu_b, cu_a)
    raise ValueError("不支持的铜几何对: %s/%s" % (cu_a.cid, cu_b.cid))


# ---------------------------------------------------------------- 判定（唯一源）

def check_clearance(coppers, min_clearance_mm, same_net_exempt=True):
    """R5：任意两个不同网络同层铜（含焊盘）间距 ≥ min_clearance_mm。

    擦边（距离恰好 == min_clearance_mm）合规；"<" 才违例。
    """
    violations = []
    checked = 0
    coppers = list(coppers)
    for i in range(len(coppers)):
        for j in range(i + 1, len(coppers)):
            a, b = coppers[i], coppers[j]
            if same_net_exempt and a.net_id == b.net_id:
                continue
            gap = _actual_gap(a, b)
            if gap is None:
                continue
            checked += 1
            if gap < min_clearance_mm - clearance.EPS:
                violations.append(Violation(
                    "R5", a.cid, b.cid,
                    {"gap_mm": round(gap, 10), "required_mm": min_clearance_mm,
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


def check_edge_clearance(coppers, workspace, margin_mm=EDGE_CLEARANCE_MM):
    """D6-3：铜判定点落入板边禁布带 → 违例（rule="edge_clearance"）。

    禁布带 = workspace 内缩 margin_mm 的环带（edge_inner_rect，唯一轮廓源）；
    擦边（判定点距边恰 = margin_mm）合规、"<" 才违例（与 check_clearance
    的 R5 口径一致）。全信号层同带（层间无差，调用方无需逐层过滤——plane
    层铜本属 R6 违例，此处照判不豁免）。逐违例点一枚 Violation（data.pos
    供 route_check edge_violations 消费接口映射与 D6-4 同位归责）；序 =
    输入序 × 点序，确定性。独立判定器（不入 check_all 聚合——编排层是否
    升格为可行门由 route_check/executor 的 D6-3 落点决定，见各自 docstring）。"""
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


def check_all(coppers, hard_rules, sensitive_rects=(), keepout_rects=(),
              capacity_checks=(), width_checks=(), plane_layers=()):
    """总检入口：R5 + R2 + R6 + capacity + R1（容量/宽度事实由调用方核算传入）。

    返回 DRCReport（带模块版本号，进证据链）。
    """
    violations = []
    v5, checked = check_clearance(coppers, hard_rules["R5"]["min_clearance_mm"])
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
