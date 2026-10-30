# -*- coding: utf-8 -*-
"""L3 区域受限详细路由器（SPEC §4）：治"无实时反馈修正"的病。

架构（SPEC §4.1）：
- 区域 = 网端点 bbox + L3_MARGIN 边距裁到板内；区域内精细栅格（L3_RES）建
  静态障碍图：异网铜/孔/板边按 (间距要求 + 候选线宽/2) 膨胀标记，同网铜豁免
  （同电位可达）。坑 5 的粗格格心偏移以自定区域原点天然规避。
- A* on (x, y, layer)：信号层 F/In2（Rev-C 层职责），8 邻 45° 纪律（对角步
  要求两正交邻格可用，防切角），层迁移 = 过孔候选（独立 via 位图约束）。
- L2 走廊软约束：走廊格集外的格加 L3_CORRIDOR_COST_MM（有走廊可走时用）。
- L1 精确终判：候选路径转 45° 段后逐段 seg_legal、逐孔 via_legal（SPEC §4.1
  "栅格作搜索，L1 作终判"）；终判失败 → 失败 prim 覆盖格加障碍 → 重搜
  （≤L3_MAX_REFINE 轮）。margin 已含 CLI 圆形多边形化余量，margin>0 即过。
- 区域内拆迁（rip-up，SPEC §4.1）：重搜耗尽后的阻塞 violator 为可拆邻网
  （非 L3_RIPUP_FORBIDDEN、焊盘 ≥2）时，预算 L3_RIPUP_BUDGET 内临时移除其
  铜重搜本网，被拆网同轮重布；任一失败即内存回滚（障碍恢复）继续下一候选。
  全程纯内存不动板文件——落板只走 commit.py 提交纪律（§4.2）。
- 每网报告：成功（段/孔/用时）或失败（阻塞 violator 清单 + 建议人工动作）。
"""
from __future__ import annotations

import hashlib
import math
import re
import time
from heapq import heappush, heappop

import numpy as np

from . import config as C
from . import geometry as G
from .planner import classify_net

LAYERS = C.L2_SIGNAL_LAYERS                       # (F=0, In2=6)
NL = len(LAYERS)
NET_RE = re.compile(r"\[([^\[\]]+)\]")


def plan_uuid(plan):
    """新铜 uuid：内容 sha256 派生（确定性，SPEC §7 禁随机；同内容同 uuid 天然去重）。"""
    h = hashlib.sha256()
    h.update(plan.net.encode("utf-8"))
    for (L, x1, y1, x2, y2) in plan.segments:
        h.update(f"S{L}:{x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f};".encode("utf-8"))
    for (x, y) in plan.vias:
        h.update(f"V:{x:.4f},{y:.4f};".encode("utf-8"))
    d = h.hexdigest()
    return "-".join((d[:8], d[8:12], d[12:16], d[16:20], d[20:32]))


class Plan:
    """route 结果（成功或失败报告），commit 的输入单元。"""

    def __init__(self, net, A, B):
        self.net = net
        self.cls = classify_net(net)
        self.A, self.B = A, B             # (x, y, frozenset(layers))
        self.ok = False
        self.fail = None                  # 失败原因
        self.blocks = []                  # 阻塞 violator 描述清单
        self.segments = []                # [(layer, x1, y1, x2, y2)]
        self.vias = []                    # [(x, y)]
        self.width = C.L3_CLASS_WIDTH.get(self.cls, 0.2)
        self.via_size, self.via_drill = C.L3_VIA_SIZE, C.L3_VIA_DRILL
        self.refine_rounds = 0
        self.ripup_net = None             # 本网成功依赖的被拆网（单段模式）
        self.ripup_plan = None            # 被拆网的重布 Plan
        self.ripups = []                  # 分段模式聚合的 [(net, 重布 Plan)]
        self.segmented = False            # 走廊中继分段 route
        self.n_relay = 0                  # 中继点数（分段模式）
        self.run_s = 0.0
        self.region_mm = 0.0

    def ripup_ops(self):
        """本 plan 依赖的拆迁 [(net, 重布 Plan|None)]（commit 落板序用）。"""
        if self.ripups:
            return list(self.ripups)
        if self.ripup_net:
            return [(self.ripup_net, self.ripup_plan)]
        return []

    def to_dict(self):
        d = {
            "net": self.net, "cls": self.cls, "ok": self.ok,
            "fail": self.fail, "blocks": self.blocks,
            "width": self.width,
            "A": [self.A[0], self.A[1]], "B": [self.B[0], self.B[1]],
            "segments": [{"layer": "F.Cu" if L == C.LAYER_F else "In2.Cu",
                          "from": [x1, y1], "to": [x2, y2]}
                         for (L, x1, y1, x2, y2) in self.segments],
            "vias": [[x, y] for (x, y) in self.vias],
            "length_mm": round(self.length_mm(), 3),
            "refine_rounds": self.refine_rounds,
            "segmented": self.segmented,
            "n_relay": self.n_relay,
            "ripup_net": self.ripup_net,
            "ripup_plan": self.ripup_plan.to_dict() if self.ripup_plan else None,
            "ripups": [{"net": rn,
                        "plan": rp.to_dict() if rp else None}
                       for (rn, rp) in self.ripups],
            "run_s": round(self.run_s, 2),
            "region_mm": round(self.region_mm, 1),
        }
        if self.ok:
            d["uuid"] = self.uuid
        return d

    @property
    def uuid(self):
        """新铜 uuid（内容派生，落板时刻取值）。"""
        return plan_uuid(self)

    def length_mm(self):
        total = 0.0
        for (_L, x1, y1, x2, y2) in self.segments:
            total += math.hypot(x2 - x1, y2 - y1)
        return total


# ---------------- 区域障碍栅格 ----------------

class Region:
    """区域精细栅格障碍模型：blocked[NL][ny][nx] 线位、vblocked[ny][nx] 过孔位。

    excluded_items：临时移除的铜（rip-up）；added_prims：内存中已规划未落板的
    新铜 prim 集（同批前网/重布时当作既有障碍）。"""

    def __init__(self, mirror, net, width, via_size, via_drill, bbox, res,
                 excluded_items=(), added_prims=()):
        self.m = mirror
        self.net = net
        self.width = width
        self.via_size = via_size
        self.via_drill = via_drill
        self.res = res
        x0, y0, x1, y1 = bbox
        self.x0 = math.floor(x0 / res) * res
        self.y0 = math.floor(y0 / res) * res
        self.nx = max(1, int(math.ceil((x1 - self.x0) / res)) + 1)
        self.ny = max(1, int(math.ceil((y1 - self.y0) / res)) + 1)
        self.blocked = np.zeros((NL, self.ny, self.nx), dtype=bool)
        self.vblocked = np.zeros((self.ny, self.nx), dtype=bool)
        self.excluded = set(id(it) for it in excluded_items)
        # added_prims 项 = (prim, L) 或 (prim, L, net)——带网名者按
        # clearance_between 取间距（ripup 重布场景：S4 实测 0.15 硬编码
        # 会让重布铜贴上主 plan 新铜 0.05mm，CLI 判 clearance 整批回滚）
        self.added_prims = [
            (it[0], it[1], it[2] if len(it) > 2 else None)
            for it in added_prims]
        self._corr = None

    # ---- 坐标 ----

    def cell_of(self, x, y):
        return (min(max(int(round((x - self.x0) / self.res)), 0), self.nx - 1),
                min(max(int(round((y - self.y0) / self.res)), 0), self.ny - 1))

    def center(self, ix, iy):
        return (self.x0 + ix * self.res, self.y0 + iy * self.res)

    def bbox_all(self):
        return (self.x0, self.y0,
                self.x0 + (self.nx - 1) * self.res, self.y0 + (self.ny - 1) * self.res)

    # ---- 构建 ----

    def build(self):
        m = self.m
        bx0, by0, bx1, by1 = self.bbox_all()
        rad_line = self.width / 2.0 + C.L3_BLOCK_EXTRA
        rad_via = self.via_size / 2.0 + C.L3_BLOCK_EXTRA
        rad_hole_line = C.MIN_HOLE_CLEARANCE + self.width / 2.0 + C.L3_BLOCK_EXTRA
        rad_hole_via = C.MIN_HOLE_CLEARANCE + self.via_size / 2.0 + C.L3_BLOCK_EXTRA
        for L in LAYERS:
            for it in m.query_copper(L, bx0, by0, bx1, by1,
                                     extra=rad_via + C.BUCKET):
                if id(it) in self.excluded or (it.net and it.net == self.net):
                    continue
                req = m.clearance_between(self.net, it.net)
                for prim in it.prims:
                    self._block_prim(prim, req + rad_line, (L,), rad_via + req)
        for it in self.added_prims:
            prim, Ls, pnet = it
            req = self.m.clearance_between(self.net, pnet) if pnet \
                else C.BOARD_MIN_CLEARANCE
            for L in (Ls if isinstance(Ls, (set, frozenset)) else (Ls,)):
                if L not in LAYERS:
                    continue
                self._block_prim(prim, req + rad_line, (L,), rad_via + req)
        for h in m.query_holes(LAYERS[0], bx0, by0, bx1, by1,
                               extra=rad_hole_via + C.BUCKET):
            if h.net and h.net == self.net:
                continue
            self._block_prim(h.prim, rad_hole_line, h.layers, rad_hole_via)
        er = C.MIN_COPPER_EDGE_CLEARANCE
        for (ex1, ey1, ex2, ey2) in m.edge_segs:
            self._block_prim((("seg", ex1, ey1, ex2, ey2), 0.0),
                             er + rad_line, LAYERS, er + rad_via)

    def _block_prim(self, prim, rad_line, layers, rad_via=None):
        """prim 膨胀 rad_line 标线位障碍；rad_via 给定时以更大半径标过孔位障碍。"""
        g = self
        bb = G.prim_bbox(prim)
        ix1, iy1 = g.cell_of(bb[0] - rad_line, bb[1] - rad_line)
        ix2, iy2 = g.cell_of(bb[2] + rad_line, bb[3] + rad_line)
        for L in layers:
            if L not in LAYERS:
                continue
            bl = g.blocked[LAYERS.index(L)]
            for iy in range(iy1, iy2 + 1):
                cy = g.y0 + iy * g.res
                for ix in range(ix1, ix2 + 1):
                    cx = g.x0 + ix * g.res
                    if G.pt_prim_dist(cx, cy, prim) <= rad_line:
                        bl[iy, ix] = True
        if rad_via is not None:
            ix1, iy1 = g.cell_of(bb[0] - rad_via, bb[1] - rad_via)
            ix2, iy2 = g.cell_of(bb[2] + rad_via, bb[3] + rad_via)
            for iy in range(iy1, iy2 + 1):
                cy = g.y0 + iy * g.res
                for ix in range(ix1, ix2 + 1):
                    cx = g.x0 + ix * g.res
                    if G.pt_prim_dist(cx, cy, prim) <= rad_via:
                        g.vblocked[iy, ix] = True

    # ---- 走廊 ----

    def set_corridor(self, segs):
        """L2 粗走廊段栅格化为格集（软约束参考集）。segs=[(layer, x1,y1,x2,y2)]"""
        self._corr = {LAYERS.index(L): set() for (L, *_r) in segs
                      if L in LAYERS}
        for (L, x1, y1, x2, y2) in segs:
            if L not in LAYERS:
                continue
            ci = self._corr[LAYERS.index(L)]
            dist = math.hypot(x2 - x1, y2 - y1)
            n = max(1, int(dist / (self.res / 2.0)))
            for k in range(n + 1):
                t = k / n
                ix, iy = self.cell_of(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
                ci.add((ix, iy))

    def corridor_cost(self, li, ix, iy):
        if self._corr is None:
            return 0.0
        return 0.0 if (ix, iy) in self._corr.get(li, ()) \
            else C.L3_CORRIDOR_COST_MM

    # ---- 动态加障（终判失败重搜）----

    def block_candidate(self, seg, rad):
        (_L, x1, y1, x2, y2) = seg
        dist = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(dist / (self.res / 2.0)))
        ax1, ay1, ax2, ay2 = min(x1, x2) - rad, min(y1, y2) - rad, \
            max(x1, x2) + rad, max(y1, y2) + rad
        ix1, iy1 = self.cell_of(ax1, ay1)
        ix2, iy2 = self.cell_of(ax2, ay2)
        for li in range(NL):
            bl = self.blocked[li]
            for iy in range(iy1, iy2 + 1):
                cy = self.y0 + iy * self.res
                for ix in range(ix1, ix2 + 1):
                    cx = self.x0 + ix * self.res
                    if G.seg_pt_dist(cx, cy, x1, y1, x2, y2) <= rad:
                        bl[iy, ix] = True

    def block_via(self, x, y, rad):
        ix1, iy1 = self.cell_of(x - rad, y - rad)
        ix2, iy2 = self.cell_of(x + rad, y + rad)
        for iy in range(iy1, iy2 + 1):
            cy = self.y0 + iy * self.res
            for ix in range(ix1, ix2 + 1):
                cx = self.x0 + ix * self.res
                if math.hypot(cx - x, cy - y) <= rad:
                    self.vblocked[iy, ix] = True

    def protect(self, pts):
        """端点附近强制清障（起终点格起步兜底；范围极小 L3_START_FREE_R）。"""
        for (x, y) in pts:
            ix, iy = self.cell_of(x, y)
            r = int(math.ceil(C.L3_START_FREE_R / self.res))
            for li in range(NL):
                bl = self.blocked[li]
                for iy2 in range(max(0, iy - r), min(self.ny, iy + r + 1)):
                    for ix2 in range(max(0, ix - r), min(self.nx, ix + r + 1)):
                        bl[iy2, ix2] = False


# ---------------- Router ----------------

class Router:
    def __init__(self, mirror, legality=None, corridor_of=None, log=print):
        self.m = mirror
        self.leg = legality
        self.corridor_of = corridor_of    # callable(net) -> [(L, x1,y1,x2,y2)] | None
        self.log = log

    # ---- 对外 ----

    def route_net(self, net, A, B, ripup=True):
        """单断点/单边 route。A/B = (x, y, frozenset(layers))。纯内存。"""
        t0 = time.perf_counter()
        plan = self._fresh_plan(net, A, B)
        bbox = self._region_bbox(plan)
        plan.region_mm = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        p = self._try_route(plan, bbox, excluded_items=())
        if p.ok or not ripup:
            p.run_s = time.perf_counter() - t0
            return p
        # rip-up：终判阻塞 violator 中的可拆邻网，预算内逐个尝试
        cands = self._ripup_candidates(p)
        for cand in cands[:C.L3_RIPUP_BUDGET]:
            removed = [self.m.items[i]
                       for i in self.m._items_by_net.get(cand, [])]
            cand_terms = self._net_endpoints(cand)
            if len(cand_terms) < 2:
                continue
            self.log(f"  [ripup] {net} 被 [{cand}] 阻塞，试拆 {cand} "
                     f"（{len(removed)} 项铜）重搜")
            # 被拆网铜在 L1 终判里也视同已删（落板时 commit 真删；
            # finally 恢复——ripup 失败回滚后终判口径还原）
            self.leg.ignore_ids = {id(it) for it in removed}
            try:
                p2 = self._try_route(self._fresh_plan(net, A, B), bbox,
                                     excluded_items=removed)
                if not p2.ok:
                    continue
                # 被拆网同轮重布：本网新铜 prims 也作障碍；重布失败=回滚内存
                rp = self._replan_net(cand, cand_terms, self._plan_prims(p2))
                if rp is not None:
                    p = p2
                    p.ripup_net = cand
                    p.ripup_plan = rp
                    break
                self.log(f"  [ripup] [{cand}] 重布失败，回滚内存继续")
            finally:
                self.leg.ignore_ids = set()
        p.run_s = time.perf_counter() - t0
        return p

    # ---- 走廊中继分段 route（PHASE-REPORT-3 §5.1）----

    def route_net_segmented(self, net, A, B, segs, ripup=True):
        """长距网分段 route：沿该断点对的 L2 走廊每 L3_SEG_INTERVAL_MM 取
        中继点，逐段 route_net（子段 i+1 的起点层约束 = 子段 i 的到达层，
        保证中继点层连续），全部成功后聚合为单 Plan。任一子段失败即整体
        失败（内存态自动丢弃）；两个子段拆同一网时保守判失败。纯内存。"""
        t0 = time.perf_counter()
        whole = self._fresh_plan(net, A, B)
        whole.segmented = True
        wps = self._relay_chain(net, A, B, segs)
        if wps is None:
            whole.fail = "走廊中继点构建失败（该对无可用走廊段）"
            whole.run_s = time.perf_counter() - t0
            return whole
        a_ls = frozenset(l for l in A[2] if l in LAYERS) or frozenset(LAYERS)
        b_ls = frozenset(l for l in B[2] if l in LAYERS) or frozenset(LAYERS)
        arrival = a_ls
        last = len(wps) - 2
        for i in range(last + 1):
            P, Q = wps[i], wps[i + 1]
            sub = self.route_net(net,
                                 (P[0], P[1], arrival),
                                 (Q[0], Q[1], b_ls if i == last else arrival),
                                 ripup=ripup)
            whole.refine_rounds += sub.refine_rounds
            whole.region_mm = max(whole.region_mm, sub.region_mm)
            if not sub.ok:
                whole.fail = (f"子段 {i + 1}/{last + 1} 失败"
                              f"（中继 ({P[0]:.2f},{P[1]:.2f})→"
                              f"({Q[0]:.2f},{Q[1]:.2f})）：{sub.fail}")
                whole.blocks = sub.blocks
                whole.run_s = time.perf_counter() - t0
                return whole
            if not sub.segments:
                whole.fail = f"子段 {i + 1} 退化为无铜段"
                whole.run_s = time.perf_counter() - t0
                return whole
            arrival = frozenset({sub.segments[-1][0]})
            # 前段以过孔收尾时中继点已完成换层：后段可从任意信号层起步
            # （孔坐标是格心，与中继点差可达半格）
            vtol = C.L3_RES / 2.0 + C.TOUCH_TOL
            if any(math.hypot(vx - Q[0], vy - Q[1]) <= vtol
                   for (vx, vy) in sub.vias):
                arrival = frozenset(LAYERS)
            whole.segments.extend(sub.segments)
            whole.vias.extend(sub.vias)
            if sub.ripup_net:
                if any(rn == sub.ripup_net for (rn, _rp) in whole.ripups):
                    whole.fail = (f"子段 {i + 1} 与先前子段拆同网 "
                                  f"[{sub.ripup_net}]，保守回滚整体")
                    whole.run_s = time.perf_counter() - t0
                    return whole
                whole.ripups.append((sub.ripup_net, sub.ripup_plan))
        # 聚合重验（各子段已各自过 L1；同网铜互不约束，拼接不引入新相邻，
        # 此处作防御性兜底）+ 两端点落铜
        bad = self._verify(whole)
        if bad:
            whole.ok = False
            whole.fail = "聚合后 L1 终判失败（防御性兜底，不应发生）"
            whole.blocks = [b for (_k, _m, b, _o) in bad]
        elif not self._endpoints_touch(whole):
            whole.ok = False
            whole.fail = "聚合后端点未落铜（防御性兜底，不应发生）"
        else:
            whole.ok, whole.fail, whole.blocks = True, None, []
            whole.n_relay = len(wps) - 2
        whole.run_s = time.perf_counter() - t0
        return whole

    def _relay_free(self, net, width, x, y):
        """中继点净空检查：该点在任一信号层满足对异网铜（含 netless）与
        孔的间距口径（与 Region 障碍标记同口径：req + width/2 + extra）。"""
        rad = width / 2.0 + C.L3_BLOCK_EXTRA
        for L in LAYERS:
            ok = True
            for it in self.m.query_copper(L, x, y, x, y, extra=rad + 0.3):
                if it.net and it.net == net:
                    continue
                req = self.m.clearance_between(net, it.net)
                for prim in it.prims:
                    if G.pt_prim_dist(x, y, prim) <= req + rad:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            for h in self.m.query_holes(L, x, y, x, y, extra=rad + 0.4):
                if h.net and h.net == net:
                    continue
                if G.pt_prim_dist(x, y, h.prim) \
                        <= C.MIN_HOLE_CLEARANCE + rad:
                    ok = False
                    break
                if not ok:
                    break
            if ok:
                return True
        return False

    def _relay_chain(self, net, A, B, segs):
        """A→走廊→B 折线沿弧长每 L3_SEG_INTERVAL_MM 切中继点。中继点必须
        落在净空位（L2 走廊是协商语义，可穿越占用格；硬交接点若落在异网铜
        间距禁区内则子段必死——S4 dry-run 实测 70% 中继点中招）：候选位无
        净空时沿弧长 ±0.5mm 步进滑到最近净空位（窗口 ±0.6×interval；
        无净空位则原位硬切，由子段诚实失败）。
        返回 [(x, y)]（含 A/B 首末，相邻点距 ≥0.3mm）；走廊段空返回 None。"""
        if not segs:
            return None
        pts = [(A[0], A[1])]
        for (_L, x1, y1, x2, y2) in segs:
            for (px, py) in ((x1, y1), (x2, y2)):
                if math.hypot(px - pts[-1][0], py - pts[-1][1]) > 1e-6:
                    pts.append((px, py))
        if math.hypot(B[0] - pts[-1][0], B[1] - pts[-1][1]) > 1e-6:
            pts.append((B[0], B[1]))
        total = sum(math.hypot(pts[i + 1][0] - pts[i][0],
                               pts[i + 1][1] - pts[i][1])
                    for i in range(len(pts) - 1))

        def point_at(d):
            done = 0.0
            for j in range(len(pts) - 1):
                seg_len = math.hypot(pts[j + 1][0] - pts[j][0],
                                     pts[j + 1][1] - pts[j][1])
                if done + seg_len >= d - 1e-9:
                    t = (d - done) / seg_len if seg_len > 1e-12 else 0.0
                    return (pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t,
                            pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t)
                done += seg_len
            return pts[-1]

        width = C.L3_CLASS_WIDTH.get(classify_net(net), 0.2)
        iv = C.L3_SEG_INTERVAL_MM
        out = [pts[0]]
        k = 1
        while k * iv <= total - 0.25 * iv:
            d = k * iv
            p = point_at(d)
            if not self._relay_free(net, width, p[0], p[1]):
                step, nmax = 0.5, int(0.6 * iv / 0.5)
                for j in range(1, nmax + 1):
                    for dd in (d + j * step, d - j * step):
                        if not (0.3 < dd < total - 0.3):
                            continue
                        q = point_at(dd)
                        if self._relay_free(net, width, q[0], q[1]):
                            p = q
                            break
                    if p != point_at(d):
                        break
            if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= 0.3:
                out.append(p)
            k += 1
        out.append(pts[-1])
        return out

    # ---- 单轮 try（构建障碍 → A* → 转段 → L1 终判 → 失败加障重搜）----

    def _try_route(self, plan, bbox, excluded_items=(), added_prims=()):
        m = self.m
        region = Region(m, plan.net, plan.width, plan.via_size,
                        plan.via_drill, bbox,
                        C.L3_RES, excluded_items, added_prims)
        region.build()
        corr = None
        if self.corridor_of:
            corr = self.corridor_of(plan.net)
            if corr:
                region.set_corridor(corr)
        region.protect([(plan.A[0], plan.A[1]), (plan.B[0], plan.B[1])])
        fails = []
        for rnd in range(1, C.L3_MAX_REFINE + 1):
            plan.refine_rounds = rnd
            nodes = self._astar(plan, region)
            if nodes is None:
                plan.ok, plan.fail = False, \
                    "A* 不可达（区域/层约束下无自由格路径）"
                if rnd == 1 and not plan.blocks:
                    # 首轮不可达：洪泛封堵归因（谁挡死唯一通道——ripup 依据）
                    plan.blocks = self._flood_blockers(plan, region,
                                                       excluded_items)
                return plan
            segs, vias = self._to_segments(plan, nodes, region)
            plan.segments, plan.vias = segs, vias
            bad = self._verify(plan)
            if not bad and not self._endpoints_touch(plan):
                plan.ok, plan.fail = False, \
                    "端点未落铜（A* 到达层与端点层约束不符，疑端点层描述缺失）"
                return plan
            if not bad:
                plan.ok, plan.fail, plan.blocks = True, None, []
                return plan
            fails = [b for (_kind, _m, b, _o) in bad]
            # 精确重标：按失败对象把候选线位/孔位加障后重搜
            for (kind, _m, _b, obj) in bad:
                if kind == "seg":
                    region.block_candidate(obj, plan.width / 2.0 + C.L3_BLOCK_EXTRA)
                else:
                    region.block_via(obj[0], obj[1],
                                     plan.via_size / 2.0 + C.L3_BLOCK_EXTRA)
            plan.blocks = fails
        plan.ok, plan.fail = False, \
            f"L1 终判重搜 {C.L3_MAX_REFINE} 轮仍失败（候选线位与既有约束冲突）"
        return plan

    def _fresh_plan(self, net, A, B):
        return Plan(net, A, B)

    def _region_bbox(self, plan):
        mb = self.m.bbox()
        xs = (plan.A[0], plan.B[0])
        ys = (plan.A[1], plan.B[1])
        x0 = min(xs) - C.L3_MARGIN
        y0 = min(ys) - C.L3_MARGIN
        x1 = max(xs) + C.L3_MARGIN
        y1 = max(ys) + C.L3_MARGIN
        if mb:
            x0, y0 = max(x0, mb[0]), max(y0, mb[1])
            x1, y1 = min(x1, mb[2]), min(y1, mb[3])
        return (x0, y0, x1, y1)

    def _net_endpoints(self, net):
        """被拆网重布端点：全部非 NPTH 焊盘（≥2 已在 ripup 侧检查）。"""
        pads = sorted((pd for pd in self.m.pads if pd.net == net and not pd.npth),
                      key=lambda p: (p.ref, p.number))
        if len(pads) < 2:
            return []
        terms = []
        for p in pads:
            ls = frozenset(l for l in p.layers if l in LAYERS) or frozenset(LAYERS)
            terms.append((p.x, p.y, ls))
        # 全部焊盘 → 逐对 MST 由调用方语义保证：重布按链式最近邻逐边（与
        # L2 netlist MST 同精神的确定性替代：这里取首焊盘 + 其余按最近链）
        chain = [terms[0]]
        rest = terms[1:]
        while rest:
            cur = chain[-1]
            rest.sort(key=lambda t: (t[0] - cur[0]) ** 2 + (t[1] - cur[1]) ** 2)
            chain.append(rest.pop(0))
        return chain

    def _plan_prims(self, plan):
        """plan 新铜 → prim 集合（ripup 重布时作障碍；带网名按类对间距膨胀）。"""
        out = []
        for (L, x1, y1, x2, y2) in plan.segments:
            out.append(((("seg", x1, y1, x2, y2), plan.width / 2.0), L,
                        plan.net))
        for (x, y) in plan.vias:
            out.append(((("pt", x, y), plan.via_size / 2.0), frozenset(LAYERS),
                        plan.net))
        return out

    def _flood_blockers(self, plan, region, excluded_items=()):
        """A* 不可达时的封堵归因（SPEC §4.1 "被谁挡"）：从起点洪泛可达格，
        可达集边界的堵格反查覆盖它的异网铜/孔，返回 violator 描述清单
        （ripup 候选依据；确定性顺序）。"""
        from collections import deque
        NX, NY = region.nx, region.ny
        ax, ay = region.cell_of(plan.A[0], plan.A[1])
        a_ls = [li for li in range(NL) if LAYERS[li] in plan.A[2]] or \
            list(range(NL))
        seen = np.zeros((NL, NY, NX), dtype=bool)
        dq = deque()
        for li in a_ls:
            if not region.blocked[li, ay, ax]:
                seen[li, ay, ax] = True
                dq.append((li, ax, ay))
        while dq:
            li, ix, iy = dq.popleft()
            for (dx, dy) in ((1, 0), (0, 1), (-1, 0), (0, -1),
                             (1, 1), (1, -1), (-1, 1), (-1, -1)):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < NX and 0 <= jy < NY):
                    continue
                if seen[li, jy, jx] or region.blocked[li, jy, jx]:
                    continue
                if dx != 0 and dy != 0 and (
                        region.blocked[li, iy, jx] or
                        region.blocked[li, jy, ix]):
                    continue
                seen[li, jy, jx] = True
                dq.append((li, jx, jy))
            jl = 1 - li
            if not region.vblocked[iy, ix] and not seen[jl, iy, ix] \
                    and not region.blocked[jl, iy, ix]:
                seen[jl, iy, ix] = True
                dq.append((jl, ix, iy))
        excluded = set(id(it) for it in excluded_items)
        owners = {}
        cells = set()
        for li in range(NL):
            lc = LAYERS[li]
            ys, xs = np.nonzero(seen[li])
            for ix, iy in zip(xs.tolist(), ys.tolist()):
                for (dx, dy) in ((1, 0), (0, 1), (1, 1), (-1, 1)):
                    jx, jy = ix + dx, iy + dy
                    if 0 <= jx < NX and 0 <= jy < NY \
                            and not seen[li, jy, jx] \
                            and region.blocked[li, jy, jx]:
                        cells.add((lc, jx, jy))
        rad = plan.width / 2.0 + C.L3_BLOCK_EXTRA
        for (lc, ix, iy) in sorted(cells):
            cx, cy = region.center(ix, iy)
            for it in self.m.query_copper(lc, cx, cy, cx, cy, extra=rad + 0.1):
                if id(it) in excluded or (it.net and it.net == plan.net):
                    continue
                req = self.m.clearance_between(plan.net, it.net)
                for prim in it.prims:
                    if G.pt_prim_dist(cx, cy, prim) <= req + rad:
                        # netless 铜（墙等）不可拆：不加 [net] 标记，不进
                        # ripup 候选（只作 violator 报告）
                        desc = f"{it.desc}（封堵归因）" if not it.net else \
                            f"[{it.net}] {it.desc}（封堵归因）"
                        if desc not in owners:
                            owners[desc] = it.net
                        break
        return list(owners)

    def _ripup_candidates(self, plan):
        """阻塞 violator 描述 → 可拆网候选（次数降序 + 字典序，禁随机）。"""
        cnt = {}
        for b in plan.blocks:
            mt = NET_RE.search(b)
            if not mt:
                continue
            n = mt.group(1)
            if n and n != plan.net and n not in C.L3_RIPUP_FORBIDDEN:
                cnt[n] = cnt.get(n, 0) + 1
        return [k for k in sorted(cnt, key=lambda k: (-cnt[k], k))]

    # ---- A*（8 邻 45° + 层迁移；确定性 tie-break）----

    def _astar(self, plan, region):
        res = region.res
        NX, NY = region.nx, region.ny
        A, B = plan.A, plan.B
        ax, ay = region.cell_of(A[0], A[1])
        bx, by = region.cell_of(B[0], B[1])
        a_ls = set(l for l in A[2] if l in LAYERS) or set(LAYERS)
        b_ls = set(l for l in B[2] if l in LAYERS) or set(LAYERS)
        size = NL * NY * NX
        INF = float("inf")
        gs = np.full(size, INF, dtype=np.float32)
        came = np.full(size, -1, dtype=np.int64)
        closed = np.zeros(size, dtype=bool)
        bcx, bcy = region.center(bx, by)

        def enc(li, ix, iy):
            return (li * NY + iy) * NX + ix

        def hfun(ix, iy):
            cx, cy = region.center(ix, iy)
            dx, dy = abs(cx - bcx), abs(cy - bcy)
            return min(dx, dy) + (max(dx, dy) - min(dx, dy))  # octile

        layer_coef = [C.L2_LAYER_PREF[plan.cls][LAYERS.index(L)]
                      for L in LAYERS]
        heap = []
        cnt = 0
        for L in sorted(a_ls):
            li = LAYERS.index(L)
            nd = enc(li, ax, ay)
            gs[nd] = 0.0
            heappush(heap, (hfun(ax, ay), cnt, nd))
            cnt += 1
        found = False
        end_nd = -1
        while heap:
            _f, _c, nd = heappop(heap)
            if closed[nd]:
                continue
            closed[nd] = True
            li, rem = divmod(nd, NY * NX)
            iy, ix = divmod(rem, NX)
            if (ix, iy) == (bx, by) and LAYERS[li] in b_ls:
                found = True
                end_nd = nd
                break
            gcur = gs[nd]
            for (dx, dy) in ((1, 0), (0, 1), (-1, 0), (0, -1),
                             (1, 1), (1, -1), (-1, 1), (-1, -1)):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < NX and 0 <= jy < NY):
                    continue
                if not region.blocked[li, jy, jx]:
                    if dx != 0 and dy != 0:
                        # 对角防切角：两正交邻格均须可用
                        if region.blocked[li, iy, jx] or \
                                region.blocked[li, jy, ix]:
                            continue
                        step = res * math.sqrt(2.0)
                    else:
                        step = res
                    cost = step * layer_coef[li] + \
                        region.corridor_cost(li, jx, jy)
                    jn = enc(li, jx, jy)
                    if closed[jn]:
                        continue
                    ng = gcur + cost
                    if ng < gs[jn] - 1e-9:
                        gs[jn] = ng
                        came[jn] = nd
                        heappush(heap, (ng + hfun(jx, jy), cnt, jn))
                        cnt += 1
            # 层迁移（F↔In2 唯一对；via 位图约束）
            jl = 1 - li
            jn = enc(jl, ix, iy)
            if not closed[jn] and not region.vblocked[iy, ix]:
                ng = gcur + C.L3_VIA_COST_MM
                if ng < gs[jn] - 1e-9:
                    gs[jn] = ng
                    came[jn] = nd
                    heappush(heap, (ng + hfun(ix, iy), cnt, jn))
                    cnt += 1
        if not found:
            return None
        nodes = []
        nd = end_nd
        while nd != -1:
            l2, rem = divmod(int(nd), NY * NX)
            iy2, ix2 = divmod(rem, NX)
            # int() 截断 numpy 标量（np.int64 会传播成 np.float64 坐标）；
            # 层由 A* 内部索引转回 KiCad 层常量（F=0/In2=6），后续 L1/落板直用
            nodes.append((int(LAYERS[int(l2)]), int(ix2), int(iy2)))
            nd = int(came[nd])
        nodes.reverse()
        return nodes

    # ---- 格路径 → 45° 段 + 孔 ----

    def _to_segments(self, plan, nodes, region):
        """格路径 → (段列表, 孔列表)。同格层迁移处记孔；共线合并；首末点用
        精确端点坐标（与格心差 < res/2；CLI 不查角度——B1 校准实证）。
        层迁移点保留两层两个条目（若原地替换，路径首/末动作即打孔时会把
        端点侧铜段端点吞掉，产生"从错误层出发"的假段——S4 实测修）。"""
        pts, vias = [], []
        for (li, ix, iy) in nodes:
            cx, cy = region.center(ix, iy)
            if pts and pts[-1][1] == cx and pts[-1][2] == cy:
                if pts[-1][0] != li:      # 同格层迁移：记孔并保留两层条目
                    vias.append((cx, cy))
                    pts.append((li, cx, cy))
                continue
            pts.append((li, cx, cy))
        if not pts:
            return [], []
        # 首末同格层迁移的边界两点吸附到精确端点（保证端点段层正确且可触）
        if len(pts) >= 2 and pts[1][1] == pts[0][1] and pts[1][2] == pts[0][2]:
            pts[1] = (pts[1][0], plan.A[0], plan.A[1])
        if len(pts) >= 2 and pts[-2][1] == pts[-1][1] \
                and pts[-2][2] == pts[-1][2]:
            pts[-2] = (pts[-2][0], plan.B[0], plan.B[1])
        pts[0] = (pts[0][0], plan.A[0], plan.A[1])
        pts[-1] = (pts[-1][0], plan.B[0], plan.B[1])
        segs = []
        cur = None                        # [layer, x0, y0, dir]
        prev = pts[0]
        for p in pts[1:]:
            li, x, y = p
            if cur is None:
                cur = [li, prev[1], prev[2], None]
            if li != cur[0]:              # 层切换：闭段并从迁移格重新起步
                segs.append((cur[0], cur[1], cur[2], prev[1], prev[2]))
                cur = [li, prev[1], prev[2], None]
            dx, dy = x - prev[1], y - prev[2]
            n = max(abs(dx), abs(dy))
            if n <= 1e-12:
                prev = p
                continue
            u = (round(dx / n, 9), round(dy / n, 9))
            if cur[3] is None:
                cur[3] = u
            elif cur[3] != u:
                segs.append((cur[0], cur[1], cur[2], prev[1], prev[2]))
                cur = [li, prev[1], prev[2], u]
            prev = p
        if cur is not None:
            segs.append((cur[0], cur[1], cur[2], prev[1], prev[2]))
        segs = [s for s in segs
                if math.hypot(s[3] - s[1], s[4] - s[2]) > 1e-9]
        return segs, vias

    def _replan_net(self, net, terms, added_prims):
        """被拆网重布：链式端点逐边 route（确定性最近链），全部边成功才算
        成功；返回聚合 Plan，任一边失败返回 None（内存态自动丢弃即回滚）。"""
        whole = Plan(net, terms[0], terms[-1])
        for i in range(len(terms) - 1):
            sub = self._fresh_plan(net, terms[i], terms[i + 1])
            r = self._try_route(sub, self._region_bbox(sub),
                                added_prims=added_prims)
            if not r.ok:
                return None
            whole.segments.extend(r.segments)
            whole.vias.extend(r.vias)
            whole.refine_rounds += r.refine_rounds
        whole.ok = True
        return whole

    # ---- L1 终判 ----

    def _endpoints_touch(self, plan):
        """两端点必须被本 plan 的铜在端点层集内接触（防悬空铜：端点层描述
        缺失时 A* 可能在错误层到达——opens.csv 局限的兜底，SPEC §4.2 精神）。
        段用精确触（TOUCH_TOL）；孔允许端点半格内（栅格量化固有误差，
        端点收尾打孔是合法形态：孔盘 0.6 ≫ 半格偏移，物理重叠）。"""
        via_tol = C.L3_RES / 2.0 + C.TOUCH_TOL
        for (pt, ls) in ((plan.A, plan.A[2]), (plan.B, plan.B[2])):
            ok = False
            for (L, x1, y1, x2, y2) in plan.segments:
                if L not in ls:
                    continue
                if G.seg_pt_dist(pt[0], pt[1], x1, y1, x2, y2) <= C.TOUCH_TOL:
                    ok = True
                    break
            if not ok:
                for (x, y) in plan.vias:
                    if math.hypot(x - pt[0], y - pt[1]) <= via_tol:
                        ok = True
                        break
            if not ok:
                return False
        return True

    def _verify(self, plan):
        """逐段 seg_legal / 逐孔 via_legal。返回失败清单
        [(kind, margin, violator, obj)]；空 = 全过。"""
        if self.leg is None:
            return []
        bad = []
        for seg in plan.segments:
            ok, margin, viol = self.leg.seg_legal(seg[0], (seg[1], seg[2]),
                                                  (seg[3], seg[4]),
                                                  plan.width, plan.net)
            if not ok:
                bad.append(("seg", margin, viol, seg))
        for (x, y) in plan.vias:
            ok, margin, viol = self.leg.via_legal(x, y, plan.net,
                                                  LAYERS[0], LAYERS[1],
                                                  size=plan.via_size,
                                                  drill=plan.via_drill)
            if not ok:
                bad.append(("via", margin, viol, (x, y)))
        return bad
