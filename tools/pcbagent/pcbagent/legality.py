# -*- coding: utf-8 -*-
"""L1 合法性 API（SPEC §2）：毫秒级实时反馈原语。

- 规则来源：.kicad_pro net classes（网络类感知）+ 板级 rules（config.py）。
- 实现：bbox 桶索引粗筛 → geometry.prim 精确数学（seg-seg/prim-prim/绕数，含旋转）；
  禁止栅格近似下结论。
- 返回 (ok, margin, violator)：margin = min(实际表面间距 − 要求间距)，≥0 即合法；
  violator 为最紧约束的障碍描述（kicad-cli 永远赢：冲突时 L1 错）。
- CLI 口径要点（详见 config 注释）：hole_to_hole=warning 不计；--refill-zones 下
  zone 填充会为新铜让位（REFILL_ADAPTS_ZONE），过孔钻孔跨平面层须满足重灌约束。
"""
from __future__ import annotations

import math

from . import config as C
from . import geometry as G
from .mirror import _span_layers

BIG_MARGIN = 10.0


class Legality:
    def __init__(self, mirror):
        self.m = mirror
        # rip-up 期间被拆网的铜（id 集）：终判视同已删（落板时 commit 真删）。
        # 默认空集 = B1 探针电池行为完全不变。
        self.ignore_ids = set()

    # ---------- 对外接口 ----------

    def seg_legal(self, layer, p1, p2, width, net):
        """段候选：layer 上 (p1→p2) 宽 width 的走线。"""
        x1, y1 = p1
        x2, y2 = p2
        seg_len = math.hypot(x2 - x1, y2 - y1)
        if seg_len < C.EPS:
            return (False, -C.MIN_TRACK_WIDTH, "track_segment_length(零长段)")
        if width < C.MIN_TRACK_WIDTH - C.EPS:
            return (False, width - C.MIN_TRACK_WIDTH, "track_width")
        if C.ENFORCE_TRACK_ANGLE_45 and not G.seg_angle_ok(x1, y1, x2, y2):
            return (False, -1.0, "track_angle(非45°整倍数)")
        prim = (("seg", x1, y1, x2, y2), width / 2.0)
        margin, viol = self._check_copper(layer, [prim], net)
        m, v = self._check_edge([prim], net)
        if m < margin:
            margin, viol = m, v
        m, v = self._check_holes(layer, [prim], net)
        if m < margin:
            margin, viol = m, v
        m, v = self._check_zones(layer, [prim], net)
        if m < margin:
            margin, viol = m, v
        return (margin >= 0.0, margin, viol)

    def via_legal(self, x, y, net, from_layer, to_layer, size=None, drill=None):
        """过孔候选：盘径 size / 钻径 drill（None 则取该网网络类默认值）。"""
        if size is None or drill is None:
            cd, cdd = self.m.via_params_of(net)
            size = size if size is not None else cd
            drill = drill if drill is not None else cdd
        if size < C.MIN_VIA_DIAMETER - C.EPS:
            return (False, size - C.MIN_VIA_DIAMETER, "via_diameter")
        if drill < C.MIN_THROUGH_HOLE_DIAMETER - C.EPS:
            return (False, drill - C.MIN_THROUGH_HOLE_DIAMETER, "drill_out_of_range")
        if (size - drill) / 2.0 < C.MIN_VIA_ANNULAR_WIDTH - C.EPS:
            return (False, (size - drill) / 2.0 - C.MIN_VIA_ANNULAR_WIDTH,
                    "annular_width")
        span = _span_layers(from_layer, to_layer)
        # 候选盘为精确圆；CLI 的圆形多边形化（内接，inset ≤ max_error 0.005mm）
        # 以 CIRCLE_POLY_SAGITTA 等效余量计入各检查（B1 门五组边界探针实证）
        disk = (("pt", x, y), size / 2.0)
        margin, viol = BIG_MARGIN, ""
        for L in span:
            m, v = self._check_copper(L, [disk], net, cand_circular=True)
            if m < margin:
                margin, viol = m, v
            # 候选钻孔 vs 其它网的铜（hole_clearance，error 级）
            m, v = self._check_holes_copper(L, x, y, drill, net)
            if m < margin:
                margin, viol = m, v
            # 候选盘铜 vs 其它孔（CLI 实证：via 盘落 NPTH 孔内报 hole_clearance）
            m, v = self._check_copper_vs_holes(L, [disk], net)
            if m < margin:
                margin, viol = m, v
            m, v = self._check_holes_hole(L, x, y, drill, net)
            if m < margin:
                margin, viol = m, v
        # refill 让位校验（跨平面层）：盘缘让位半径 = size/2 + clearance
        # 须 ≥ 孔半径 + hole_clearance（直接用 size 算，与 prim 表示无关）
        for L in span:
            for z in self.m.zones_on(L):
                if z.net and z.net == net:
                    continue
                give = size / 2.0 + self.m.clearance_between(net, z.net)
                need = drill / 2.0 + C.MIN_HOLE_CLEARANCE
                if give < need - C.EPS:
                    m = give - need
                    if m < margin:
                        margin, viol = m, \
                            f"zone_refill_hole(重灌让位不足) vs [{z.net}] @layer{L}"
        m, v = self._check_edge([disk], net, cand_circular=True)
        if m < margin:
            margin, viol = m, v
        return (margin >= 0.0, margin, viol)

    def pad_legal(self, rect, layer, net):
        """焊盘候选：layer 上轴对齐矩形 rect=(x1,y1,x2,y2)。"""
        x1, y1, x2, y2 = rect
        prim = (G.rect_poly(x1, y1, x2, y2), 0.0)
        margin, viol = self._check_copper(layer, [prim], net)
        m, v = self._check_edge([prim], net)
        if m < margin:
            margin, viol = m, v
        m, v = self._check_holes(layer, [prim], net)
        if m < margin:
            margin, viol = m, v
        m, v = self._check_zones(layer, [prim], net)
        if m < margin:
            margin, viol = m, v
        return (margin >= 0.0, margin, viol)

    # ---------- 内部检查 ----------

    def _check_copper(self, layer, prims, net, cand_circular=False):
        """候选 prims vs 该层其它网铜。返回 (margin, violator)。

        圆形参与者（候选过孔盘、存量过孔盘）按 CLI 多边形化口径加
        CIRCLE_POLY_SAGITTA 等效余量；线段/焊盘精确。"""
        bb = _prims_bbox(prims)
        req_max = self._max_clearance()
        cands = self.m.query_copper(layer, bb[0], bb[1], bb[2], bb[3],
                                    extra=max(p[1] for p in prims) + req_max + 0.05)
        margin, viol = BIG_MARGIN, ""
        for it in cands:
            if id(it) in self.ignore_ids:
                continue  # rip-up 拆除中：视同已删
            if it.net and it.net == net:
                continue  # 同网不查（kicad-cli 同口径）
            if it.net == "" and net == "":
                continue  # 双无网不构成短路
            req = self.m.clearance_between(net, it.net)
            bias = C.CIRCLE_POLY_SAGITTA * ((1 if cand_circular else 0) +
                                            (1 if it.kind == "via" else 0))
            for pa in prims:
                for pb in it.prims:
                    m = G.prim_dist(pa, pb) + bias - req
                    if m < margin:
                        margin, viol = m, it.desc
        return margin, viol

    def _check_edge(self, prims, net, cand_circular=False):
        """候选铜 vs 板边（copper_edge_clearance）。候选为圆时加等效余量。"""
        margin, viol = BIG_MARGIN, ""
        if not self.m.edge_segs:
            return margin, viol
        bias = C.CIRCLE_POLY_SAGITTA if cand_circular else 0.0
        bb = _prims_bbox(prims)
        if not _near_edge(self.m, bb):
            return margin, viol
        for pa in prims:
            core = pa[0]
            r = pa[1]
            if core[0] == "pt":
                for (ex1, ey1, ex2, ey2) in self.m.edge_segs:
                    m = (G.seg_pt_dist(core[1], core[2], ex1, ey1, ex2, ey2) - r
                         + bias) - C.MIN_COPPER_EDGE_CLEARANCE
                    if m < margin:
                        margin, viol = m, "板边 copper_edge_clearance"
            elif core[0] == "seg":
                for (ex1, ey1, ex2, ey2) in self.m.edge_segs:
                    m = (G.seg_seg_dist(core[1], core[2], core[3], core[4],
                                        ex1, ey1, ex2, ey2) - r) \
                        - C.MIN_COPPER_EDGE_CLEARANCE
                    if m < margin:
                        margin, viol = m, "板边 copper_edge_clearance"
            else:
                for (ex1, ey1, ex2, ey2) in self.m.edge_segs:
                    m = (G.seg_poly_dist(ex1, ey1, ex2, ey2, core[1]) - r) \
                        - C.MIN_COPPER_EDGE_CLEARANCE
                    if m < margin:
                        margin, viol = m, "板边 copper_edge_clearance"
        return margin, viol

    def _check_holes(self, layer, prims, net):
        """候选铜 vs 本层存在的钻孔（hole_clearance）。同网孔豁免。
        孔为圆形（多边形化）→ +CIRCLE_POLY_SAGITTA；要求一律 MIN_HOLE_CLEARANCE。"""
        bb = _prims_bbox(prims)
        cands = self.m.query_holes(layer, bb[0], bb[1], bb[2], bb[3],
                                   extra=max(p[1] for p in prims) +
                                   C.MIN_HOLE_CLEARANCE + 0.05)
        margin, viol = BIG_MARGIN, ""
        for h in cands:
            if id(h) in self.ignore_ids:
                continue
            if h.net and h.net == net:
                continue
            for pa in prims:
                m = G.prim_dist(pa, h.prim) + C.CIRCLE_POLY_SAGITTA \
                    - C.MIN_HOLE_CLEARANCE
                if m < margin:
                    margin, viol = m, f"hole_clearance vs {h.desc}"
        return margin, viol

    def _check_holes_copper(self, layer, x, y, drill, net):
        """候选过孔钻孔 vs 其它网铜（hole_clearance，本层）。
        候选孔为圆形（多边形化）→ +CIRCLE_POLY_SAGITTA。"""
        cands = self.m.query_copper(layer, x, y, x, y, extra=drill / 2.0 +
                                    C.MIN_HOLE_CLEARANCE + 0.05)
        margin, viol = BIG_MARGIN, ""
        for it in cands:
            if id(it) in self.ignore_ids:
                continue
            if it.net and it.net == net:
                continue
            if it.net == "" and net == "":
                continue
            for pb in it.prims:
                m = G.pt_prim_dist(x, y, pb) - drill / 2.0 \
                    + C.CIRCLE_POLY_SAGITTA - C.MIN_HOLE_CLEARANCE
                if m < margin:
                    margin, viol = m, f"hole_clearance(孔-铜) vs {it.desc}"
        return margin, viol

    def _check_copper_vs_holes(self, layer, prims, net):
        """候选盘铜 vs 其它孔（hole_clearance，error 级）——via 盘落 NPTH 孔内实测。
        双圆（候选盘 + 孔）→ +2×CIRCLE_POLY_SAGITTA。"""
        bb = _prims_bbox(prims)
        cands = self.m.query_holes(layer, bb[0], bb[1], bb[2], bb[3],
                                   extra=max(p[1] for p in prims) +
                                   C.MIN_HOLE_CLEARANCE + 0.05)
        margin, viol = BIG_MARGIN, ""
        for h in cands:
            if id(h) in self.ignore_ids:
                continue
            if h.net and h.net == net:
                continue
            for pa in prims:
                m = G.prim_dist(pa, h.prim) + 2 * C.CIRCLE_POLY_SAGITTA \
                    - C.MIN_HOLE_CLEARANCE
                if m < margin:
                    margin, viol = m, f"hole_clearance(铜-孔) vs {h.desc}"
        return margin, viol

    def _check_holes_hole(self, layer, x, y, drill, net):
        """候选孔 vs 其它孔（hole_to_hole，CLI severity=warning，默认不计）。"""
        if not C.HOLE_TO_HOLE_ENFORCE:
            return BIG_MARGIN, ""
        cands = self.m.query_holes(layer, x, y, x, y, extra=drill / 2.0 +
                                   C.MIN_HOLE_TO_HOLE + 0.05)
        margin, viol = BIG_MARGIN, ""
        for h in cands:
            if id(h) in self.ignore_ids:
                continue
            if h.net and h.net == net:
                continue
            hc = h.prim[0]
            d = G.seg_pt_dist(hc[1], hc[2], x, y, x, y) if hc[0] == "pt" else \
                G.seg_pt_dist(x, y, hc[1], hc[2], hc[3], hc[4])
            m = d - drill / 2.0 - h.prim[1] - C.MIN_HOLE_TO_HOLE
            if m < margin:
                margin, viol = m, f"hole_to_hole vs {h.desc}"
        return margin, viol

    def _check_zones(self, layer, prims, net):
        """候选铜 vs 同层 zone 填充（仅在 REFILL_ADAPTS_ZONE=False 时作静态否决；
        CLI --refill-zones 真值口径下 zone 会为新铜重灌让位，默认跳过）。
        过孔的重灌让位校验在 via_legal 内直接用 size/drill 计算。"""
        if not C.REFILL_ADAPTS_ZONE:
            margin, viol = BIG_MARGIN, ""
            for z in self.m.zones_on(layer):
                if z.net and z.net == net:
                    continue
                req = self.m.clearance_between(net, z.net)
                m = _prims_rings_margin(prims, z, req)
                if m < margin:
                    margin, viol = m, f"zone [{z.net}] @layer{layer}"
            return margin, viol
        return BIG_MARGIN, ""

    def _max_clearance(self):
        classes = self.m.net_classes.values()
        return max((c.clearance for c in classes), default=C.BOARD_MIN_CLEARANCE)


# ---------- 工具 ----------

def _prims_bbox(prims):
    x1 = y1 = float("inf")
    x2 = y2 = -float("inf")
    for p in prims:
        a, b, c, d = G.prim_bbox(p)
        x1, y1 = min(x1, a), min(y1, b)
        x2, y2 = max(x2, c), max(y2, d)
    return x1, y1, x2, y2


def _prims_rings_margin(prims, zone, req):
    """候选 prims 与 zone 填充实体的最小（距离−req）；进实体=−req。"""
    margin = BIG_MARGIN
    for pa in prims:
        core, r = pa
        if core[0] == "pt":
            if G.pt_in_rings(core[1], core[2], zone.rings):
                m = -req
            else:
                m = _pt_rings_dist(core[1], core[2], zone.edges) - r - req
        elif core[0] == "seg":
            x1, y1, x2, y2 = core[1], core[2], core[3], core[4]
            if G.pt_in_rings(x1, y1, zone.rings) or G.pt_in_rings(x2, y2, zone.rings) \
                    or G.seg_crosses_rings(x1, y1, x2, y2, zone.edges):
                m = -req
            else:
                m = _seg_rings_dist(x1, y1, x2, y2, zone.edges) - r - req
        else:
            poly = core[1]
            inside = any(G.pt_in_rings(px, py, zone.rings) for (px, py) in poly)
            crossed = False
            for c0, c1 in zip(poly, poly[1:] + poly[:1]):
                if G.seg_crosses_rings(c0[0], c0[1], c1[0], c1[1], zone.edges):
                    crossed = True
                    break
            if inside or crossed:
                m = -req
            else:
                m = min(_seg_rings_dist(c0[0], c0[1], c1[0], c1[1], zone.edges)
                        for c0, c1 in zip(poly, poly[1:] + poly[:1])) - r - req
        if m < margin:
            margin = m
    return margin


def _pt_rings_dist(px, py, edges):
    return min(G.seg_pt_dist(px, py, *e) for e in edges)


def _seg_rings_dist(x1, y1, x2, y2, edges):
    return min(G.seg_seg_dist(x1, y1, x2, y2, *e) for e in edges)


def _near_edge(mirror, bb):
    """bbox 是否接近任一板边段（外扩 2mm 粗筛）。"""
    x1, y1, x2, y2 = bb
    for (ex1, ey1, ex2, ey2) in mirror.edge_segs:
        bx1, by1 = min(ex1, ex2) - 2.0, min(ey1, ey2) - 2.0
        bx2, by2 = max(ex1, ex2) + 2.0, max(ey1, ey2) + 2.0
        if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2):
            return True
    return False
