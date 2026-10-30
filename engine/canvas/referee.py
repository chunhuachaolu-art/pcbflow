# -*- coding: utf-8 -*-
"""canvas.referee -- 确定性粗可布性评分器（合同 §1 Lane-M4 伴件）。

**无随机源**（无 random/无时间/无 dict 迭代序渗入——一切聚合按 sorted 序
构建; 输出 round(·,9) 保 canonical 字节稳定）。粗可布性=布局质量的确定性
代理量，供 M4 runner 的接受准则与基线臂对照; **不是**任何 DRC 判据
（合法性判定归 canvas.placecheck / canvas.validate / v5.drc）。

输入态与占位模型:
- 各分区 pad 场外接矩形（覆盖后）——复用 canvas.placecheck.pad_field_rects
  （覆盖合成与 canvas.state 同源，本件不另写覆盖算术）。
- 格点 c=(i,j) 被分区 q 占位 ⇔ c 的格点 mm（lattice.to_mm）落入 q 的
  pad 场外接矩形（含边界）; cells_by_pid[q] = q 的占位格点集。

三分量公式（构建期披露; **具体式与权重激活跑 prereg 冻结，冻结后不改义**;
权重注入点=score(..., weights=...)）:
- escape（逃逸, 越高越好）: 对每分区每端点锚（覆盖后 effective_anchors,
  格点）做 4 邻域 BFS（可穿越占位格点; 出 lattice 域的格点视作占位），
  d=到首个非占位格点的最短步数，上限 CAP=8; 端点分量
  ep = 1 - min(d, CAP)/(CAP+1)（d=0 ⇒ ep=1; 完全封死 ⇒ ep=1/(CAP+1)>0）;
  escape = 全端点 ep 的算术均值（无端点 ⇒ 1.0）。
- corridor（走廊, 越高越好）: 全部分区对（sorted 组合序，**含同网对**——
  走廊衡量物理拥堵，不分网，与 placecheck 的同网豁免差异在此披露）:
  A/B 外接矩形中心的 snap 格点之间的 L 形走廊（先 x 后 y 单位步展开，
  canvas.instantiate.expand_waypoints 同构）格点集 P;
  占用比 occ = |{c∈P: c 落入第三分区（∉{A,B}）外接矩形}| / |P|;
  corridor = 1 - 全对 occ 均值（无分区对 ⇒ 1.0）。
- capacity（容量余量, 越高越好）: 1 - |∪cells_by_pid| / |lattice 域格点数|
  （域空 ⇒ 1.0）。

total = w["escape"]·escape + w["corridor"]·corridor + w["capacity"]·capacity
缺省 DEFAULT_WEIGHTS = {"escape": 0.4, "corridor": 0.3, "capacity": 0.3}
（构建期值——prereg 冻结点; weights 注入须给全三键且非负，否则
ValueError fail-closed）。

score(board, lattice, placements, weights=None)
  -> {"escape", "corridor", "capacity", "total", "weights_used"}

输入契约: placements 须为 placecheck 域检查口径合法的覆盖（malformed
条目自然抛错 = fail-closed，本件不重复域检查）。"""
import math
from collections import deque
from itertools import combinations

from . import placecheck as _pc
from .instantiate import expand_waypoints as _expand

#: escape BFS 步数上限（构建期参数，prereg 冻结点）
CAP = 8
#: 缺省权重（构建期值; 注入点=score(weights=...)，prereg 冻结后不改义）
DEFAULT_WEIGHTS = {"escape": 0.4, "corridor": 0.3, "capacity": 0.3}

_KEYS = ("escape", "corridor", "capacity")


def _checked_weights(weights):
    out = {}
    for k in _KEYS:
        if k not in weights:
            raise ValueError("weights 缺键 %s（须给全 %s）" % (k, list(_KEYS)))
    extra = set(weights) - set(_KEYS)
    if extra:
        raise ValueError("weights 合同外键 %s" % sorted(extra))
    for k in _KEYS:
        v = weights[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) \
                or float(v) < 0.0:
            raise ValueError("weights[%s]=%r 须为非负数" % (k, v))
        out[k] = float(v)
    return out


def _rect_cells(lattice, rect):
    """外接矩形 → 占位格点集（格点 mm 含边界落于矩形; 域 clamp）。"""
    p = lattice.pitch

    def rng(lo_v, hi_v, origin, hi_bound):
        i0 = int(math.ceil((lo_v - origin) / p - 1e-9))
        i1 = int(math.floor((hi_v - origin) / p + 1e-9))
        return max(0, i0), min(hi_bound, i1)

    i0, i1 = rng(rect[0], rect[2], lattice.x0, lattice.i_max)
    j0, j1 = rng(rect[1], rect[3], lattice.y0, lattice.j_max)
    return {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)}


def _escape_dist(start, blocked, lattice, cap):
    """端点锚 → 最近非占位格点 BFS 步数（≤cap; 可穿占位格点;
    出域格点视作占位——开阔区须在域内）。"""
    if start not in blocked:
        return 0
    seen = {start}
    q = deque([(start, 0)])
    while q:
        (i, j), d = q.popleft()
        if d >= cap:
            continue
        for nb in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if nb in seen:
                continue
            seen.add(nb)
            if nb not in blocked and lattice.in_bounds(*nb):
                return d + 1
            q.append((nb, d + 1))
    return cap


def score(board, lattice, placements, weights=None):
    """确定性粗可布性评分（三分量+加权 total; 无随机源; 公式见模块
    docstring——具体式与权重激活跑 prereg 冻结）。"""
    w = dict(DEFAULT_WEIGHTS) if weights is None else _checked_weights(weights)
    pids = sorted(p["partition_id"] for p in board["partitions"])
    rects = _pc.pad_field_rects(board, lattice, placements)
    cells_by_pid = {pid: _rect_cells(lattice, rects[pid]) for pid in pids}
    blocked = set()
    for pid in pids:
        blocked |= cells_by_pid[pid]
    n_total = (lattice.i_max + 1) * (lattice.j_max + 1)
    capacity = 1.0 - (len(blocked) / float(n_total)) if n_total else 1.0
    # ---- escape
    anchors = []
    view = _pc.PlacementsView(board, lattice, placements)
    for pid in pids:
        for a in view.effective_anchors(pid):
            anchors.append((int(a[0]), int(a[1])))
    if anchors:
        escape = sum(
            1.0 - min(_escape_dist(e, blocked, lattice, CAP), CAP)
            / float(CAP + 1) for e in anchors) / len(anchors)
    else:
        escape = 1.0
    # ---- corridor
    cell_owners = {}
    for pid in pids:
        for c in cells_by_pid[pid]:
            cell_owners.setdefault(c, set()).add(pid)
    pairs = list(combinations(pids, 2))
    if pairs:
        occs = []
        for a, b in pairs:
            ca = lattice.snap((rects[a][0] + rects[a][2]) / 2.0,
                              (rects[a][1] + rects[a][3]) / 2.0)
            cb = lattice.snap((rects[b][0] + rects[b][2]) / 2.0,
                              (rects[b][1] + rects[b][3]) / 2.0)
            path = [tuple(p) for p in _expand([[ca[0], ca[1]], [cb[0], cb[1]]])]
            if not path:
                path = [ca]
            occ = sum(1 for c in path
                      if any(o for o in cell_owners.get(c, ())
                             if o != a and o != b)) / float(len(path))
            occs.append(occ)
        corridor = 1.0 - sum(occs) / len(occs)
    else:
        corridor = 1.0
    total = (w["escape"] * escape + w["corridor"] * corridor
             + w["capacity"] * capacity)
    return {"escape": round(escape, 9), "corridor": round(corridor, 9),
            "capacity": round(capacity, 9), "total": round(total, 9),
            "weights_used": {k: w[k] for k in sorted(w)}}
