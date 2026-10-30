# -*- coding: utf-8 -*-
"""L2 拥塞规划器（SPEC §3）：治"布局与详细布线之间缺拥塞评估"的病。

模型（全确定性，无随机；调参集中在 config.L2_*）：
- 粗网格：L2_CELL 见方覆盖板 bbox，信号层 F/In2 各一张（routing-spec §5 层职责）。
- 占用/容量：每格 SUB×SUB 子采样点；点被"既有铜+膨胀半径"或"孔+孔距"或
  "板边+边距"覆盖记堵。格自由宽 = cell×(1−堵点比例)，容量 =
  floor(自由宽/(参考线宽+参考间距))。占用图净无关（全部既有铜都是障碍）；
  候选网自身铜/端点格在布该网时视作可达（同电位）。
- PathFinder 协商（§3.2）：逐代全拆重布（固定网序，routing-spec §9 顺序），
  进格代价 = (格基长×层系数 + 历史) × present，present = 1+PFAC×max(0,占用−容量)；
  历史每代按过载网数累加。零过载（绿）或 max_iter 代止（红=布局超容）。
- 断点命中：断点对最终走廊穿越"末代过载格"（占用电位数>容量）计命中（§3.4 门）。

产物（SPEC §3.3）：本模块全部在内存生成，build_products() 返回
{文件名: 文本内容} 字典（corridors.json / congestion-{F,In2}.svg /
placement-feedback.md / escape-audit.md），由调用方（cli / tests 驱动脚本）
负责落盘——本模块零文件写操作。
逃逸审计：每封装每侧边"开口焊盘 fanout 可达数 + 带内额外车道" vs 需求数，
对症 3V3 22 条卡引脚场一类。
"""
from __future__ import annotations

import csv
import json
import math
import time
from collections import defaultdict
from heapq import heappush, heappop

import numpy as np

from . import config as C
from . import geometry as G
from .mirror import BoardMirror

LAYERS = C.L2_SIGNAL_LAYERS                       # (0, 6)
LAYER_NAME = {C.LAYER_F: "F.Cu", C.LAYER_IN2: "In2.Cu"}
NL = len(LAYERS)
LANE_UNIT = C.L2_CLR_REF + C.L2_W_LANE           # 候选车道距 0.35mm（0.15+0.2）
BLOCK_R = C.L2_CLR_REF + C.L2_W_LANE / 2.0       # 新道中心判堵半径 0.275mm
SUB = C.L2_SUB
SUB_OFF = [(i - (SUB - 1) / 2.0) * (1.0 / SUB) for i in range(SUB)]


def classify_net(name: str) -> str:
    for pref, key in C.L2_NET_CLASS_PATTERNS:
        if name.startswith(pref):
            return key
    return C.L2_NET_CLASS_DEFAULT


# ---------------- 网格与占用 ----------------

class Grid:
    def __init__(self, bbox, cell=C.L2_CELL, pad=1.0):
        x0, y0, x1, y1 = bbox
        self.cell = cell
        self.x0 = math.floor((x0 - pad) / cell) * cell
        self.y0 = math.floor((y0 - pad) / cell) * cell
        self.nx = max(1, int(math.ceil((x1 + pad - self.x0) / cell)))
        self.ny = max(1, int(math.ceil((y1 + pad - self.y0) / cell)))

    def cell_of(self, x, y):
        ix = int((x - self.x0) // self.cell)
        iy = int((y - self.y0) // self.cell)
        return (min(max(ix, 0), self.nx - 1), min(max(iy, 0), self.ny - 1))

    def center(self, ix, iy):
        return (self.x0 + (ix + 0.5) * self.cell,
                self.y0 + (iy + 0.5) * self.cell)


class Occupancy:
    """blocked[li,iy,ix]=堵点数；cap[li]=参考道容量（int8）。"""

    def __init__(self, mirror: BoardMirror, grid: Grid):
        t0 = time.perf_counter()
        self.grid = grid
        blocked = np.zeros((NL, grid.ny, grid.nx), dtype=np.int16)
        er = C.MIN_COPPER_EDGE_CLEARANCE + C.L2_W_LANE / 2.0
        for (ex1, ey1, ex2, ey2) in mirror.edge_segs:
            self._mark_prim(blocked, (("seg", ex1, ey1, ex2, ey2), 0.0), er)
        for h in mirror.holes:
            self._mark_prim(blocked, h.prim, C.MIN_HOLE_CLEARANCE, h.layers)
        for it in mirror.items:
            for L in it.layers:
                if L not in LAYERS:
                    continue
                for prim in it.prims:
                    self._mark_prim(blocked, prim, BLOCK_R, (L,))
        self.blocked = np.minimum(blocked, SUB * SUB)
        self.frac = self.blocked.astype(np.float32) / float(SUB * SUB)
        self.cap = np.floor(grid.cell * (1.0 - self.frac) / LANE_UNIT
                            + 1e-9).astype(np.int8)
        self.build_s = time.perf_counter() - t0

    def _mark_prim(self, blocked, prim, rad, layers=LAYERS):
        g = self.grid
        bb = G.prim_bbox(prim)
        ix1, iy1 = g.cell_of(bb[0] - rad, bb[1] - rad)
        ix2, iy2 = g.cell_of(bb[2] + rad, bb[3] + rad)
        for L in layers:
            if L not in LAYERS:
                continue
            li = LAYERS.index(L)
            bl = blocked[li]
            for iy in range(iy1, iy2 + 1):
                cy = g.y0 + (iy + 0.5) * g.cell
                for ix in range(ix1, ix2 + 1):
                    cx = g.x0 + (ix + 0.5) * g.cell
                    n = 0
                    for dx in SUB_OFF:
                        px = cx + dx * g.cell
                        for dy in SUB_OFF:
                            py = cy + dy * g.cell
                            if G.pt_prim_dist(px, py, prim) <= rad:
                                n += 1
                    if n:
                        bl[iy, ix] += n


# ---------------- 布线网描述 ----------------

class RouteNet:
    __slots__ = ("rid", "real_net", "cls", "terminals", "prio", "pair_meta")

    def __init__(self, rid, real_net, terminals, pair_meta=None):
        self.rid = rid
        self.real_net = real_net          # usage 归并按真实网名（同网多对合并计数）
        self.cls = classify_net(real_net)
        self.terminals = terminals        # [(x, y, frozenset(layers))]
        self.prio = C.L2_ROUTE_PRIORITY.get(self.cls, 9)
        self.pair_meta = pair_meta        # 断点对元数据（opens.csv 行）


def endpoint_layers(desc: str):
    """opens.csv 端点描述 → 可用信号层集合。"""
    if "PTH" in desc:
        return frozenset(LAYERS)
    if "In2.Cu" in desc:
        return frozenset((C.LAYER_IN2,))
    if "F.Cu" in desc:
        return frozenset((C.LAYER_F,))
    return frozenset(LAYERS)


def parse_opens_csv(path: str):
    """→ (pairs, gnd)；pairs=[(net, (fx,fy,fl), (tx,ty,tl), row)]，GND 行单列。"""
    pairs, gnd = [], []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            net = row["net"].strip()
            item = (net,
                    (float(row["from_x_mm"]), float(row["from_y_mm"]),
                     endpoint_layers(row["from"])),
                    (float(row["to_x_mm"]), float(row["to_y_mm"]),
                     endpoint_layers(row["to"])),
                    row)
            (gnd if net == "GND" else pairs).append(item)
    return pairs, gnd


# ---------------- Planner ----------------

class Planner:
    def __init__(self, mirror: BoardMirror, cell=C.L2_CELL, log=print):
        self.m = mirror
        self.log = log
        self.grid = Grid(mirror.bbox(), cell)
        self.occ = Occupancy(mirror, self.grid)
        self.hist = np.zeros((NL, self.grid.ny, self.grid.nx), dtype=np.float32)
        self.nets = []
        self.paths = {}                   # rid → path dict
        self._mst = {}                    # rid → [(i,j)]（netlist 模式树边）
        self._edge_paths = {}             # rid → [(i, j, nodes)]
        self._own_cache = {}
        self.netlist_pads = {}            # net → [Pad]（netlist 模式端点序）

    # ---- 网构建 ----

    def add_pairs(self, pairs):
        """断点对模式（当前板）：每对一条 2 端点布线，同真实网共享归并。"""
        for k, (net, A, B, row) in enumerate(
                sorted(pairs, key=lambda p: (p[0], p[1][0], p[2][0]))):
            rid = f"{net}~{k:02d}"
            self.nets.append(RouteNet(rid, net,
                                      [(A[0], A[1], A[2]), (B[0], B[1], B[2])],
                                      pair_meta=row))

    def add_netlist(self):
        """整板模式（p3 布线前）：全部信号网按焊盘组端点（GND 走平面不布）。"""
        by_net = defaultdict(list)
        for p in self.m.pads:
            if p.net and p.net != "GND":
                by_net[p.net].append(p)
        for net in sorted(by_net):
            pads = sorted(by_net[net], key=lambda p: (p.ref, p.number))
            if len(pads) < 2:
                continue
            terms = []
            for p in pads:
                ls = frozenset(l for l in p.layers if l in LAYERS) \
                    or frozenset(LAYERS)
                terms.append((p.x, p.y, ls))
            self.nets.append(RouteNet(net, net, terms))
            self.netlist_pads[net] = pads

    def items_of_net(self, net):
        idxs = self.m._items_by_net.get(net, [])
        return [self.m.items[i] for i in idxs]

    def own_cells(self, real_net, extra_cells=()):
        """该网既有铜覆盖格 ∪ 额外格（端点）：布该网时视为可达（同电位）。
        走线沿段按 cell/2 步距全采样（保证自身铜链格连续，A* 可沿既有逃逸
        走出引脚场）；点/多边形取 bbox 角+心。"""
        if real_net not in self._own_cache:
            g = self.grid
            cells = set()
            for it in self.items_of_net(real_net):
                for prim in it.prims:
                    core, r = prim
                    if core[0] == "seg":
                        x1, y1, x2, y2 = core[1], core[2], core[3], core[4]
                        L = math.hypot(x2 - x1, y2 - y1)
                        n = max(1, int(L / (g.cell / 2.0)))
                        dx, dy = x2 - x1, y2 - y1
                        plen = math.hypot(dx, dy)
                        if plen < 1e-12:
                            px, py = -dy, dx
                        else:
                            px, py = -dy / plen, dx / plen
                        for k in range(n + 1):
                            t = k / n
                            bx, by = x1 + dx * t, y1 + dy * t
                            cells.add(g.cell_of(bx, by))
                            cells.add(g.cell_of(bx + px * r, by + py * r))
                            cells.add(g.cell_of(bx - px * r, by - py * r))
                    else:
                        x1, y1, x2, y2 = G.prim_bbox(prim)
                        for cx, cy in ((x1, y1), (x1, y2), (x2, y1), (x2, y2),
                                       ((x1 + x2) / 2, (y1 + y2) / 2)):
                            cells.add(g.cell_of(cx, cy))
            self._own_cache[real_net] = cells
        return self._own_cache[real_net] | set(extra_cells)

    # ---- PathFinder 主循环 ----

    def run(self, max_iter=C.L2_MAX_ITER):
        t0 = time.perf_counter()
        order = sorted(self.nets, key=lambda r: (r.prio, r.real_net, r.rid))
        self.converged = False
        self.overload = set()
        self.usage_final = {}
        for gen in range(1, max_iter + 1):
            self.gen_used = gen
            usage = {}
            self._edge_paths = {}
            for r in order:
                path = self._route_net(r, usage)
                self.paths[r.rid] = path
                self._tally(usage, path, r.real_net)
            self.usage_final = usage
            over = []
            for k, v in usage.items():
                c = int(self.occ.cap[k[0], k[2], k[1]])
                # 自网独占的零容量格（自身焊盘/走线所在）不算过载；
                # 两网以上挤进 max(cap,1) 之外才是真拥塞
                limit = max(c, 1)
                if len(v) > limit:
                    over.append((k, len(v) - limit))
            self.overload = {k for k, _n in over}
            total_over = sum(n for _k, n in over)
            self.log(f"  gen {gen:02d}: 过载格 {len(over)}（超额 {total_over} 网）"
                     f" 占用格 {len(usage)}")
            if not over:
                self.converged = True
                break
            for (li, ix, iy), n in over:
                self.hist[li, iy, ix] += n * C.L2_HSTEP
        self.run_s = time.perf_counter() - t0
        self._finalize()
        return self

    def _tally(self, usage, path, real_net):
        for (li, ix, iy) in path["nodes"]:
            usage.setdefault((li, ix, iy), set()).add(real_net)

    def _finalize(self):
        """末代过载集 → 逐网命中（布线失败也算命中：无可达走廊即极端拥塞）。"""
        for r in self.nets:
            path = self.paths.get(r.rid)
            if path is None:
                continue
            hit_cells = [nd for nd in path["nodes"] if nd in self.overload]
            path["overload_cells"] = len(hit_cells)
            path["hit"] = bool(hit_cells) or not path["ok"]

    # ---- 单网布线（MST + A*）----

    def _route_net(self, r, usage):
        terms = r.terminals
        if len(terms) == 2:
            p = self._astar(r, terms[0], terms[1], usage)
            paths = [(0, 1, p)]
        else:
            n = len(terms)
            edges = []
            for i in range(n):
                for j in range(i + 1, n):
                    d = (abs(terms[i][0] - terms[j][0]) +
                         abs(terms[i][1] - terms[j][1]))
                    edges.append((d, i, j))
            edges.sort()
            par = list(range(n))

            def find(i):
                while par[i] != i:
                    par[i] = par[par[i]]
                    i = par[i]
                return i

            mst = []
            for (d, i, j) in edges:
                ri, rj = find(i), find(j)
                if ri != rj:
                    par[ri] = rj
                    mst.append((i, j))
                    if len(mst) == n - 1:
                        break
            self._mst[r.rid] = mst
            paths = []
            for (i, j) in mst:
                paths.append((i, j, self._astar(r, terms[i], terms[j], usage)))
        nodes, vias, ok, fail, segs = [], [], True, None, []
        disp_total = 0
        epaths = []
        for (i, j, p) in paths:
            disp_total += p.get("disp_cells", 0)
            if not p["ok"]:
                ok, fail = False, p["fail"]
            else:
                nodes.extend(p["nodes"])
                vias.extend(p["vias"])
                segs.extend(p["segments"])
            epaths.append((i, j, p["nodes"]))
        self._edge_paths[r.rid] = epaths
        dedup = []
        for nd in nodes:
            if not dedup or dedup[-1] != nd:
                dedup.append(nd)
        return {"rid": r.rid, "net": r.real_net, "cls": r.cls, "ok": ok,
                "fail": fail, "nodes": dedup, "vias": vias, "segments": segs,
                "overload_cells": 0, "hit": False, "disp_cells": disp_total}

    # ---- A*（4 邻 + 层迁移；确定性 tie-break）----

    def _astar(self, r, tA, tB, usage):
        g = self.grid
        NX, NY = g.nx, g.ny
        real = r.real_net
        extra = {g.cell_of(x, y) for (x, y, _ls) in r.terminals}
        own = self.own_cells(real, extra)
        own_nodes = set()
        for (ix, iy) in own:
            for li in range(NL):
                own_nodes.add((li * NY + iy) * NX + ix)
        INF = float("inf")
        size = NL * NY * NX
        gs = np.full(size, INF, dtype=np.float32)
        came = np.full(size, -1, dtype=np.int64)
        closed = np.zeros(size, dtype=bool)

        def enc(li, ix, iy):
            return (li * NY + iy) * NX + ix

        gx, gy = g.cell_of(tB[0], tB[1])
        bcx, bcy = g.center(gx, gy)

        def hfun(ix, iy):
            cx, cy = g.center(ix, iy)
            return abs(cx - bcx) + abs(cy - bcy)

        heap = []
        cnt = 0
        six, siy = g.cell_of(tA[0], tA[1])
        start_ls = sorted(tA[2]) or list(LAYERS)
        for L in start_ls:
            if L not in LAYERS:
                continue
            li = LAYERS.index(L)
            nd = enc(li, six, siy)
            if gs[nd] > 0.0:
                gs[nd] = 0.0
                heappush(heap, (hfun(six, siy), cnt, nd))
                cnt += 1
        goal_cell = (gx, gy)
        end_li, end_ix, end_iy = 0, six, siy
        found = False
        while heap:
            _f, _c, nd = heappop(heap)
            if closed[nd]:
                continue
            closed[nd] = True
            li, rem = divmod(nd, NY * NX)
            iy, ix = divmod(rem, NX)
            if (ix, iy) == goal_cell:
                found = True
                end_li, end_ix, end_iy = li, ix, iy
                break
            gnd = gs[nd]
            for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < NX and 0 <= jy < NY):
                    continue
                jn = enc(li, jx, jy)
                if closed[jn]:
                    continue
                c = self._enter_cost(r, li, jx, jy, usage, own_nodes, jn)
                if c is None:
                    continue
                ng = gnd + c
                if ng < gs[jn] - 1e-9:
                    gs[jn] = ng
                    came[jn] = nd
                    heappush(heap, (ng + hfun(jx, jy), cnt, jn))
                    cnt += 1
            jl = 1 - li
            jn = enc(jl, ix, iy)
            if not closed[jn]:
                c = self._enter_cost(r, jl, ix, iy, usage, own_nodes, jn)
                if c is not None:
                    ng = gnd + c + C.L2_VIA_EQ_MM
                    if ng < gs[jn] - 1e-9:
                        gs[jn] = ng
                        came[jn] = nd
                        heappush(heap, (ng + hfun(ix, iy), cnt, jn))
                        cnt += 1
        if not found:
            return {"rid": r.rid, "net": real, "cls": r.cls, "ok": False,
                    "fail": "A* 不可达（搜索空间耗尽）",
                    "nodes": [], "vias": [], "segments": [],
                    "overload_cells": 0, "hit": False, "disp_cells": 0}
        nodes = []
        nd = enc(end_li, end_ix, end_iy)
        while nd != -1:
            l2, rem = divmod(nd, NY * NX)
            iy2, ix2 = divmod(rem, NX)
            nodes.append((l2, ix2, iy2))
            nd = came[nd]
        nodes.reverse()
        disp = 0
        for (l2, ix2, iy2) in nodes:
            if int(self.occ.cap[l2, iy2, ix2]) <= 0 and (ix2, iy2) not in own:
                disp += 1
        vias = []
        for a, b in zip(nodes, nodes[1:]):
            if a[0] != b[0] and (a[1], a[2]) == (b[1], b[2]):
                vias.append((a[1], a[2]))
        return {"rid": r.rid, "net": real, "cls": r.cls, "ok": True,
                "fail": None, "nodes": nodes, "vias": vias,
                "segments": _compress(nodes, g),
                "overload_cells": 0, "hit": False, "disp_cells": disp}

    def _enter_cost(self, r, li, ix, iy, usage, own_nodes, node_enc):
        """进格代价（SPEC §3.2 协商语义：零容量格不硬封锁，付拆让代价穿越）。
        own（本网铜/端点格）免拆让与历史。"""
        cap = int(self.occ.cap[li, iy, ix])
        is_own = node_enc in own_nodes
        s = usage.get((li, ix, iy))
        if s:
            n = len(s) - (1 if r.real_net in s else 0)
        else:
            n = 0
        over = n - cap
        present = 1.0 + C.L2_PFAC * over if over > 0 else 1.0
        mult = C.L2_LAYER_PREF[r.cls][li]
        if is_own:
            return self.grid.cell * mult
        cost = self.grid.cell * mult + float(self.hist[li, iy, ix])
        if cap <= 0:
            cost += C.L2_RIPUP_COST_MM   # 该格已被既有铜占满：进入=需推挤让位
        return cost * present

    # ---- 直线采样（次级判据）----

    def straight_line_cells(self, A, B):
        """端点直线采样的格序列（次级判据用）：每格展开双信号层 3 元组。"""
        step = self.grid.cell / 2.0
        ax, ay = A[0], A[1]
        bx, by = B[0], B[1]
        dist = math.hypot(bx - ax, by - ay)
        n = max(1, int(dist / step))
        out = []
        for k in range(n + 1):
            t = k / n
            ix, iy = self.grid.cell_of(ax + (bx - ax) * t, ay + (by - ay) * t)
            for li in range(NL):
                out.append((li, ix, iy))
        return out


# ---------------- 走廊压缩 ----------------

def _compress(nodes, grid):
    """格序列 → 共线压缩段 [{"layer","from","to"}]；层变点切分。"""
    if not nodes:
        return []
    segs = []
    cur_li = nodes[0][0]
    cur = [nodes[0]]
    for nd in nodes[1:]:
        if nd[0] != cur_li:
            segs.append(_seg_of(cur, cur_li, grid))
            cur_li, cur = nd[0], [nd]
            continue
        if len(cur) > 1:
            px, py = cur[-1][1] - cur[-2][1], cur[-1][2] - cur[-2][2]
            nx_, ny_ = nd[1] - cur[-1][1], nd[2] - cur[-1][2]
            if (px, py) == (nx_, ny_):
                cur.append(nd)
            else:
                segs.append(_seg_of(cur, cur_li, grid))
                cur = [cur[-1], nd]
        else:
            cur.append(nd)
    segs.append(_seg_of(cur, cur_li, grid))
    return [s for s in segs if s]


def _seg_of(cells, li, grid):
    if not cells:
        return None
    x1, y1 = grid.center(cells[0][1], cells[0][2])
    x2, y2 = grid.center(cells[-1][1], cells[-1][2])
    return {"layer": LAYER_NAME[LAYERS[li]],
            "from": [round(x1, 4), round(y1, 4)],
            "to": [round(x2, 4), round(y2, 4)]}


# ---------------- 逃逸审计（SPEC §3.3-4）----------------

SIDE_VEC = {"N": (0, -1), "S": (0, 1), "W": (-1, 0), "E": (1, 0)}
SIDE_ZH = {"N": "北", "S": "南", "W": "西", "E": "东"}


def _pad_side(p, cx, cy, hx, hy):
    dx = (p.x - cx) / hx
    dy = (p.y - cy) / hy
    if abs(dx) >= abs(dy):
        return "E" if dx > 0 else "W"
    return "S" if dy > 0 else "N"


def _fanout_ok(mirror, pad, outward, depth=C.L2_ESCAPE_DEPTH, step=0.125):
    """焊盘沿 outward 能否拉出一条本网走线（0.125mm 采样，精确几何）。
    障碍=异网铜（同网豁免）、异网孔、板边。返回 (ok, blocker_desc)。"""
    w = C.L2_CLASS_WIDTH[classify_net(pad.net)]
    rad = C.L2_CLR_REF + w / 2.0
    ls = sorted(l for l in pad.layers if l in LAYERS)
    if not ls:
        return False, "焊盘不在信号层"
    L = ls[0] if C.LAYER_F in ls else ls[-1]
    dx, dy = outward
    if pad.shape == "circle":
        half = pad.w / 2.0
    else:
        half = abs(dx) * pad.w / 2.0 + abs(dy) * pad.h / 2.0
    sx, sy = pad.x + dx * half, pad.y + dy * half
    n = max(1, int(depth / step))
    for k in range(n + 1):
        px, py = sx + dx * step * k, sy + dy * step * k
        for it in mirror.query_copper(L, px, py, px, py, extra=rad + 0.05):
            if it.net and it.net == pad.net:
                continue
            if min(G.pt_prim_dist(px, py, pr) for pr in it.prims) < rad - 1e-9:
                return False, it.desc
        for h in mirror.query_holes(L, px, py, px, py, extra=rad + 0.05):
            if h.net and h.net == pad.net:
                continue
            if G.pt_prim_dist(px, py, h.prim) < C.MIN_HOLE_CLEARANCE - 1e-9:
                return False, h.desc
        for (ex1, ey1, ex2, ey2) in mirror.edge_segs:
            if G.seg_pt_dist(px, py, ex1, ey1, ex2, ey2) < \
                    C.MIN_COPPER_EDGE_CLEARANCE + w / 2.0 - 1e-9:
                return False, "板边 copper_edge_clearance"
    return True, None


def build_pad_side_map(mirror: BoardMirror):
    """{(ref, pad_number): (ref, side)}——逃逸审计侧面归属（与 escape_audit
    同一分类口径：封装 pad 质心 + bbox 半跨向角分类）。≥4 盘封装才参与。"""
    fps = defaultdict(list)
    for p in mirror.pads:
        fps[p.ref].append(p)
    out = {}
    for ref, pads in fps.items():
        if len(pads) < 4:
            continue
        cx = sum(p.x for p in pads) / len(pads)
        cy = sum(p.y for p in pads) / len(pads)
        hx = (max(p.x for p in pads) - min(p.x for p in pads)) / 2.0 + 0.05
        hy = (max(p.y for p in pads) - min(p.y for p in pads)) / 2.0 + 0.05
        for p in pads:
            out[(ref, p.number)] = (ref, _pad_side(p, cx, cy, hx, hy))
    return out


def escape_audit(mirror: BoardMirror, occ: Occupancy, grid: Grid,
                 open_pads, all_mode=False, log=print):
    """每封装每侧边：需求(开口焊盘数) vs 供给(fanout 可达 + 带内额外车道)。
    all_mode=True（p3 整板模式）：全部焊盘皆需求。逐侧返回行 dict 列表。"""
    fps = defaultdict(list)
    for p in mirror.pads:
        fps[p.ref].append(p)
    open_keys = {(p.ref, p.number) for p in open_pads}
    li = LAYERS.index(C.LAYER_F)
    rows = []
    for ref in sorted(fps):
        pads = fps[ref]
        if len(pads) < 4:
            continue
        cx = sum(p.x for p in pads) / len(pads)
        cy = sum(p.y for p in pads) / len(pads)
        hx = (max(p.x for p in pads) - min(p.x for p in pads)) / 2.0 + 0.05
        hy = (max(p.y for p in pads) - min(p.y for p in pads)) / 2.0 + 0.05
        pad_cells = {grid.cell_of(p.x, p.y) for p in pads}
        for side in ("N", "E", "S", "W"):
            side_pads = [p for p in pads
                         if _pad_side(p, cx, cy, hx, hy) == side]
            demand_pads = [p for p in side_pads
                           if all_mode or (p.ref, p.number) in open_keys]
            if not demand_pads:
                continue
            fan_ok, fan_bad = 0, []
            for p in demand_pads:
                ok, blocker = _fanout_ok(mirror, p, SIDE_VEC[side])
                if ok:
                    fan_ok += 1
                else:
                    fan_bad.append((p.number, blocker))
            extra = 0
            depth_cells = int(math.ceil(C.L2_ESCAPE_DEPTH / grid.cell))
            if side in ("N", "S"):
                iys = sorted({grid.cell_of(p.x, p.y)[1] for p in side_pads})
                ix_lo = grid.cell_of(min(p.x for p in side_pads), cy)[0]
                ix_hi = grid.cell_of(max(p.x for p in side_pads), cy)[0]
                edge = iys[0] if side == "N" else iys[-1]
                step = -1 if side == "N" else 1
                for d in range(1, depth_cells + 1):
                    iy = edge + step * d
                    if not (0 <= iy < grid.ny):
                        break
                    for ix in range(ix_lo, ix_hi + 1):
                        if (ix, iy) not in pad_cells:
                            extra += int(occ.cap[li, iy, ix])
            else:
                ixs = sorted({grid.cell_of(p.x, p.y)[0] for p in side_pads})
                iy_lo = grid.cell_of(cx, min(p.y for p in side_pads))[1]
                iy_hi = grid.cell_of(cx, max(p.y for p in side_pads))[1]
                edge = ixs[0] if side == "W" else ixs[-1]
                step = -1 if side == "W" else 1
                for d in range(1, depth_cells + 1):
                    ix = edge + step * d
                    if not (0 <= ix < grid.nx):
                        break
                    for iy in range(iy_lo, iy_hi + 1):
                        if (ix, iy) not in pad_cells:
                            extra += int(occ.cap[li, iy, ix])
            supply = fan_ok + extra
            rows.append({
                "ref": ref, "side": side, "side_zh": SIDE_ZH[side],
                "demand": len(demand_pads), "fanout_ok": fan_ok,
                "extra_lanes": extra, "supply": supply,
                "insufficient": len(demand_pads) > supply,
                "fanout_blocked": fan_bad,
                "open_nets": sorted({p.net for p in demand_pads if p.net}),
            })
    return rows


# ---------------- 产物（全部内存生成，调用方落盘）----------------

def _stress_color(n, cap):
    if n <= 0:
        return "#f2f2f0"
    if cap <= 0:
        return "#cfcfcf"
    r = n / cap
    if r <= 0.5:
        return "#a5d6a7"
    if r <= 1.0:
        return "#ffd54f"
    if r <= 2.0:
        return "#ff8a65"
    return "#e53935"


def render_svg(planner, li, paths_to_draw=None, title="") -> str:
    """拥塞热图 SVG 文本（末代 usage + 走廊叠画）。"""
    g = planner.grid
    w_mm = g.nx * g.cell
    h_mm = g.ny * g.cell
    usage = planner.usage_final
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="-2 -2 {w_mm + 4:.1f} {h_mm + 4:.1f}" '
             f'font-family="monospace">',
             f'<rect x="-2" y="-2" width="{w_mm + 4:.1f}" '
             f'height="{h_mm + 4:.1f}" fill="white"/>',
             f'<rect x="{g.x0}" y="{g.y0}" width="{w_mm:.1f}" '
             f'height="{h_mm:.1f}" fill="none" stroke="black" '
             f'stroke-width="0.2"/>']
    cap_l = planner.occ.cap[li]
    frac_l = planner.occ.frac[li]
    for iy in range(g.ny):
        for ix in range(g.nx):
            n = len(usage.get((li, ix, iy), ()))
            blocked = frac_l[iy, ix] > 0 and cap_l[iy, ix] <= 0
            if n == 0 and not blocked:
                continue
            x, y = g.x0 + ix * g.cell, g.y0 + iy * g.cell
            color = _stress_color(n, int(cap_l[iy, ix])) if n else "#cfcfcf"
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{g.cell}" '
                         f'height="{g.cell}" fill="{color}" '
                         f'fill-opacity="0.85"/>')
    if paths_to_draw:
        for segs in paths_to_draw:
            for s in segs:
                (x1, y1), (x2, y2) = s["from"], s["to"]
                parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" '
                             f'x2="{x2:.3f}" y2="{y2:.3f}" '
                             f'stroke="#0b409c" stroke-width="0.12" '
                             f'stroke-opacity="0.8"/>')
    parts.append(f'<text x="{g.x0}" y="{g.y0 - 0.6}" font-size="1.6">'
                 f'{title}（绿&lt;50% 黄=满 红=过载 灰=堵死）</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def l2_config_snapshot():
    out = {}
    for k in dir(C):
        if k.startswith("L2_"):
            v = getattr(C, k)
            if not callable(v):
                out[k] = list(v) if isinstance(v, tuple) else v
    return out


def _cluster_cells(planner, li):
    """末代过载格（单层）贪心聚簇（确定性：按 (iy,ix) 排序后吸收相邻）。"""
    g = planner.grid
    cells = sorted(((ix, iy) for (l, ix, iy) in planner.overload if l == li))
    clusters = []
    for (ix, iy) in cells:
        for cl in clusters:
            if cl["ix1"] - 1 <= ix <= cl["ix2"] + 1 \
                    and cl["iy1"] - 1 <= iy <= cl["iy2"] + 1:
                cl["ix1"] = min(cl["ix1"], ix)
                cl["iy1"] = min(cl["iy1"], iy)
                cl["ix2"] = max(cl["ix2"], ix)
                cl["iy2"] = max(cl["iy2"], iy)
                break
        else:
            clusters.append({"ix1": ix, "iy1": iy, "ix2": ix, "iy2": iy})
    out = []
    for cl in clusters:
        x1 = g.x0 + cl["ix1"] * g.cell
        y1 = g.y0 + cl["iy1"] * g.cell
        x2 = g.x0 + (cl["ix2"] + 1) * g.cell
        y2 = g.y0 + (cl["iy2"] + 1) * g.cell
        near = _near_footprints(planner.m, (x1 + x2) / 2, (y1 + y2) / 2, 6.0)
        out.append({"layer": LAYER_NAME[LAYERS[li]],
                    "bbox_mm": [round(x1, 2), round(y1, 2),
                                round(x2, 2), round(y2, 2)],
                    "cells": (cl["ix2"] - cl["ix1"] + 1) *
                             (cl["iy2"] - cl["iy1"] + 1),
                    "near_footprints": near})
    out.sort(key=lambda c: (-c["cells"], c["bbox_mm"]))
    return out


def _near_footprints(mirror, x, y, maxd):
    fps = defaultdict(list)
    for p in mirror.pads:
        fps[p.ref].append(p)
    out = []
    for ref, pads in fps.items():
        cx = sum(p.x for p in pads) / len(pads)
        cy = sum(p.y for p in pads) / len(pads)
        d = math.hypot(cx - x, cy - y)
        if d <= maxd:
            out.append((d, ref))
    out.sort()
    return [r for _d, r in out]


def build_products(planner, board_tag, escape_rows, gate_note="") -> dict:
    """SPEC §3.3 四产物 → {文件名: 文本内容}（corridors.json /
    congestion-F.svg / congestion-In2.svg / placement-feedback.md /
    escape-audit.md）。落盘由调用方负责。"""
    nets = []
    for r in sorted(planner.nets, key=lambda r: r.rid):
        path = planner.paths[r.rid]
        nets.append({
            "rid": r.rid, "net": r.real_net, "class": r.cls,
            "ok": path["ok"], "fail": path["fail"],
            "hit": path["hit"], "overload_cells": path["overload_cells"],
            "disp_cells": path.get("disp_cells", 0),
            "terminals": [[round(t[0], 4), round(t[1], 4),
                           sorted(LAYER_NAME[l] for l in t[2] if l in LAYER_NAME)]
                          for t in r.terminals],
            "segments": path["segments"],
            "vias": [[round(planner.grid.x0 + (ix + 0.5) * planner.grid.cell, 4),
                      round(planner.grid.y0 + (iy + 0.5) * planner.grid.cell, 4)]
                     for (ix, iy) in path["vias"]],
            "pair": dict(r.pair_meta) if r.pair_meta else None,
        })
    cj = {
        "board": board_tag,
        "tool": "pcbagent L2 planner (SPEC §3)",
        "deterministic": True,
        "config": l2_config_snapshot(),
        "grid": {"cell_mm": planner.grid.cell, "nx": planner.grid.nx,
                 "ny": planner.grid.ny, "x0": planner.grid.x0,
                 "y0": planner.grid.y0},
        "generations": getattr(planner, "gen_used", 0),
        "converged_zero_overuse": getattr(planner, "converged", False),
        "run_seconds": round(getattr(planner, "run_s", 0.0), 1),
        "overload_cells": len(planner.overload),
        "nets": nets,
    }
    draw = [planner.paths[r.rid]["segments"] for r in planner.nets]
    return {
        "corridors.json": json.dumps(cj, ensure_ascii=False, indent=1),
        "congestion-F.svg": render_svg(planner, 0, draw,
                                       f"congestion F.Cu [{board_tag}]"),
        "congestion-In2.svg": render_svg(planner, 1, draw,
                                         f"congestion In2.Cu [{board_tag}]"),
        "placement-feedback.md": _placement_feedback_md(planner, board_tag),
        "escape-audit.md": _escape_audit_md(escape_rows, board_tag, gate_note),
    }


def _placement_feedback_md(planner, board_tag):
    L = ["# 布局反馈（placement-feedback）", "",
         f"- 板：{board_tag}　工具：pcbagent L2（SPEC §3.3-3）",
         f"- PathFinder：{getattr(planner, 'gen_used', 0)} 代，"
         f"{'零过载收敛（绿）' if getattr(planner, 'converged', False) else '未收敛（红=布局超容）'}，"
         f"末代过载格 {len(planner.overload)}",
         "",
         "持续过载簇（末代 usage>capacity）与邻近封装（只建议不执行）：", ""]
    n = 0
    for li in range(NL):
        for cl in _cluster_cells(planner, li):
            n += 1
            L.append(f"{n}. **{cl['layer']}** 簇 bbox(mm)={cl['bbox_mm']}"
                     f"（{cl['cells']} 格）邻近封装："
                     f"{', '.join(cl['near_footprints']) or '（空旷区）'}")
    if n == 0:
        L.append("（无过载簇）")
    L += ["", "建议语义：", "",
          "- 簇位于两封装之间 → 通道容量不足：考虑其一移开/旋转让出通道，",
          "  或批准 routing-spec §5.1 的 A0 布局微调（U1 北移 0.8 / U2 南移 1.2）。",
          "- 簇环绕引脚场（U1/U2 四周）→ 逃逸容量不足：见 escape-audit.md。",
          "- 本文件为 advisory，不作裁决；详细布线准入以 gate.json 为准。", ""]
    return "\n".join(L)


def _escape_audit_md(rows, board_tag, gate_note=""):
    L = ["# 逃逸容量审计（escape-audit，SPEC §3.3-4）", "",
         f"- 板：{board_tag}　口径：需求=侧边开口焊盘数（整板模式=全部焊盘），"
         f"供给=fanout 可达数 + 逃逸带内额外车道（带深 {C.L2_ESCAPE_DEPTH}mm，"
         f"0.125mm 采样，通道判堵半径=间距+线宽/2）",
         "- 方向按屏幕坐标：北=−y 南=+y 西=−x 东=+x", ""]
    L.append("| 封装 | 侧 | 需求 | fanout可达 | 带内额外道 | 供给 | 判定 |")
    L.append("|---|---|---:|---:|---:|---:|---|")
    for r in rows:
        L.append(f"| {r['ref']} | {r['side_zh']}({r['side']}) | {r['demand']} | "
                 f"{r['fanout_ok']} | {r['extra_lanes']} | {r['supply']} | "
                 f"{'**不足**' if r['insufficient'] else '可'} |")
    ins = [r for r in rows if r["insufficient"]]
    L += ["", f"不足侧合计：{len(ins)}", ""]
    for r in ins:
        blocked = ", ".join(f"pad{n}:{(b or '?')[:40]}" for n, b in
                            r["fanout_blocked"][:6])
        L.append(f"- {r['ref']} {r['side_zh']}侧：需求 {r['demand']} > 供给 "
                 f"{r['supply']}；被堵 fanout：{blocked or '—'}；"
                 f"开口网：{', '.join(r['open_nets'][:8])}"
                 f"{'…' if len(r['open_nets']) > 8 else ''}")
    if gate_note:
        L += ["", gate_note]
    return "\n".join(L) + "\n"
