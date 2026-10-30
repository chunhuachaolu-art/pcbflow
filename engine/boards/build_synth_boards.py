# -*- coding: utf-8 -*-
"""第四代参数化合成板生成器 v0（A2-SYNTHBOARD-R1 W1，2026-09-30）。

与既有三代 builder 的差异：**参数化旋钮 + 可布性构造保证**（不是事后标注）。

旋钮（全部记录进每板 sidecar）：
  workspace_mm / layers(2|4|6 信号层) / net_count / pad_layout_mode
  (random|paired|clustered) / obstacle_density(low|mid|high，难度旋钮) /
  via_budget(参考解允许的换层次数) / seed（random.Random 种子，无时钟无真随机）。

可布性构造保证（v5 引擎世界模型口径，事实源=v5/executor.py 与 v5/route_check.py
探盘核读）：
  - 构造可布板（routable=True）：先为每网铺**参考路径**（曼哈顿折线+层指派，
    同层参考路径中心线两两 ≥ LANE_SEP_MM=1.5 ≥ R5=0.5），再放障碍（keepout
    zones / 板固孔），障碍与全部参考路径保持 CLEAR 距离（按难度 0.9/0.75/0.6，
    ≥ 逃逸阶梯最大位移与栅格吸附余量）。参考路径联合构成一个可行解 witness
    ——引擎侧该解逐条合法（R5 中心线口径、R6 禁布 gap>0、板边 0.2mm 禁布带、
    孔禁布带均由构造间距满足），故「至少一条可行解存在」由构造给出。
  - 构造不可布板（routable=False）：**构造性全层焊盘密封**——在封锁目标网
    的端点上叠一枚异网 all-layer 通孔焊盘（pad_terminals layers="all" →
    v5 世界模型逐信号层各一枚矩形固定铜，见 v5/route_check._pad_scene_items）。
    密封垫半尺寸 ≥ 引擎逃逸阶梯最大位移（_ESCAPE_RADII=3 格 × GRID_PITCH
    0.25 = 0.75mm）+ 栅格吸附上界（0.25×√2/2 ≈ 0.177mm）+ 安全余量，故任一
    尝试计划的起种节点都深陷垫内：R5 中心线口径下从垫内节点出发的每条 8 向
    边与每个换层孔（via_gap_blocked）距垫面 0 < R5-EPS 全封，A* 零展开；
    rip-up 只摘 route: 铜（fixed: 焊盘铜不可摘），封锁不可协商解除——保证无解。

铁律（继承 boards/build_demo_boards.py 惯例）：
  - stdlib only（random 只用 random.Random(seed) 确定性驱动）；不 import
    tests/ 下任何模块；不 import 既有三个 builder（构造代码独立）。
  - 同输入同字节可重复（无 wall-clock、无真随机、无主机路径入板内容）；
    文件字节 = v5.canonical.canonical_json(board)。
  - 写盘前逐板 v5.board.load_board fail-closed 自检（schema + provenance 链
    + 跨字段合同），另跑构造保证自查（guarantee_check）并把结果记进 sidecar。
  - provenance：source_type=synthetic、source_sha256=本生成器脚本字节哈希
    （authoring provenance：脚本即源）、source_uri 用仓库相对键、
    board_sha256 链式重算。
  - principle_registry 恰一条 partition_granularity 先验（L1 fail-closed，
    v5/partition.py:60「0 条或 ≥2 条 fail-closed」）。

输出：<repo>/boards/synth-r1/<board_id>.board.v1.json + <board_id>.sidecar.json
（sidecar 带 provenance 头 + 全旋钮值 + guarantee_type + witness；板侧
sidecar 不经 v5.sidecar.write_sidecar——该助手只准写 out/ 下，板侧文件直写
canonical 字节）。
"""
import hashlib
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synth-r1")
_SCRIPT_PATH = os.path.abspath(__file__)
GENERATOR_VERSION = "synthgen v1.0.0"

# ---------------------------------------------------------------- 世界事实常量
# （探盘核读单源：v5/executor.py GRID_PITCH/_ESCAPE_RADII/_RIPUP_ESCAPE_REACH_MM、
#  v5/drc.py EDGE_CLEARANCE_MM/HOLE_TO_HOLE_MM、demo 板 hard_rules R1–R6）
GRID_PITCH_MM = 0.25            # 引擎 A* 基线栅距
R5_MM = 0.5                     # R5 中心线净距（v5 中心线口径）
EDGE_BAND_MM = 0.2              # D6-3 板边禁布带（workspace 内缩）
ESCAPE_REACH_MM = 0.75          # 逃逸阶梯最大位移（3 格 × 0.25）
SNAP_BOUND_MM = GRID_PITCH_MM * math.sqrt(2.0) / 2.0   # 栅格吸附位移上界 ≈0.177
HOLE_MARGIN_MM = 0.25           # HOLE_TO_HOLE_MM 板固孔禁布带
VIA_RADIUS_MM = 0.3             # via_model 缺省孔铜半径（kicad_export 缺省）
# 密封垫半尺寸下界 = 逃逸位移 + 吸附上界 + 安全余量（保证全部起种节点深陷垫内）
SEAL_HALF_FLOOR_MM = ESCAPE_REACH_MM + SNAP_BOUND_MM + 0.35   # ≈ 1.277

# 构造间距（同层参考路径中心线/端点/障碍三类）
LANE_SEP_MM = 1.5               # 同层参考路径中心线最小间距（R5 0.5 + 1.0 安全带）
ENDPOINT_SEP_MM = 2.5           # 异网端点（含对异网参考路径）最小间距
BORDER_MARGIN_MM = 1.0          # 端点/参考路径离板边最小距离（≥ 0.2 边带 + 余量）
OB_CLEAR_MM = {"low": 0.9, "mid": 0.75, "high": 0.6}   # 障碍-参考路径净空（难度旋钮）
OB_KEEPOUTS = {"low": 2, "mid": 4, "high": 7}          # keepout 目标数
OB_HOLES = {"low": 0, "mid": 2, "high": 4}             # 板固孔目标数
MIN_GAP_BY_DIFFICULTY = {"low": 3.0, "mid": 2.0, "high": 1.5}  # 粒度先验 min_gap
TRACK_HALF_MM = 0.1             # planned_width 0.2 的半宽（孔禁布带核算用）

_STACKUPS = {
    2: [("F.Cu", "h"), ("B.Cu", "any")],
    4: [("F.Cu", "h"), ("In1.Cu", "v"), ("In2.Cu", "v"), ("B.Cu", "any")],
    6: [("F.Cu", "h"), ("In1.Cu", "v"), ("In2.Cu", "v"),
        ("In3.Cu", "v"), ("In4.Cu", "v"), ("B.Cu", "any")],
}

_HARD_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}


class ConstructionError(ValueError):
    """旋钮组合构造失败（fail-closed；矩阵调整须在 PREREG 冻结前完成）。"""


# ---------------------------------------------------------------- 几何原语（stdlib）
def _snap(v):
    return round(v * 4.0) / 4.0


def _pt_seg_dist(p, a, b):
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    px, py = float(p[0]), float(p[1])
    dx, dy = bx - ax, by - ay
    dd = dx * dx + dy * dy
    if dd <= 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / dd))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _segments_cross(a1, a2, b1, b2):
    """两线段是否相交（含端点触/共线重叠；eps 防浮点毛刺）。"""
    eps = 1e-9

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        if v > eps:
            return 1
        if v < -eps:
            return -1
        return 0

    def on_seg(p, q, r):
        return (min(p[0], r[0]) - eps <= q[0] <= max(p[0], r[0]) + eps
                and min(p[1], r[1]) - eps <= q[1] <= max(p[1], r[1]) + eps)

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)
    if o1 != o2 and o3 != o4:
        return True
    for o, p, q, r in ((o1, a1, b1, a2), (o2, a1, b2, a2),
                       (o3, b1, a1, b2), (o4, b1, a2, b2)):
        if o == 0 and on_seg(p, q, r):
            return True
    return False


def _seg_seg_dist(a1, a2, b1, b2):
    """两线段最小距离（**相交=0**——相交点可在两段内部，四端点距离皆>0，
    故必须先做相交判定；本 bug 曾致跨线漏检，已被生成面测试抓出）。"""
    if _segments_cross(a1, a2, b1, b2):
        return 0.0
    return min(_pt_seg_dist(a1, b1, b2), _pt_seg_dist(a2, b1, b2),
               _pt_seg_dist(b1, a1, a2), _pt_seg_dist(b2, a1, a2))


def _pt_rect_dist(p, rect):
    dx = max(rect[0] - p[0], 0.0, p[0] - rect[2])
    dy = max(rect[1] - p[1], 0.0, p[1] - rect[3])
    return math.hypot(dx, dy)


def _seg_rect_dist(p, q, rect):
    if _pt_rect_dist(p, rect) <= 0.0 or _pt_rect_dist(q, rect) <= 0.0:
        return 0.0
    edges = ((rect[0], rect[1], rect[0], rect[3]),
             (rect[2], rect[1], rect[2], rect[3]),
             (rect[0], rect[1], rect[2], rect[1]),
             (rect[0], rect[3], rect[2], rect[3]))
    return min(_seg_seg_dist(p, q, (e[0], e[1]), (e[2], e[3])) for e in edges)


def _poly_rect_dist(poly, rect):
    """折线（点列）到轴对齐矩形的最小距离。"""
    if len(poly) == 1:
        return _pt_rect_dist(poly[0], rect)
    return min(_seg_rect_dist(poly[i], poly[i + 1], rect)
               for i in range(len(poly) - 1))


def _poly_pt_dist(poly, p):
    if len(poly) == 1:
        return math.hypot(poly[0][0] - p[0], poly[0][1] - p[1])
    return min(_pt_seg_dist(p, poly[i], poly[i + 1])
               for i in range(len(poly) - 1))


def _poly_poly_dist(pa, pb):
    if len(pa) == 1:
        return _poly_pt_dist(pb, pa[0])
    if len(pb) == 1:
        return _poly_pt_dist(pa, pb[0])
    return min(_seg_seg_dist(pa[i], pa[i + 1], pb[j], pb[j + 1])
               for i in range(len(pa) - 1) for j in range(len(pb) - 1))


def _pt_circle_dist(p, c, r):
    return max(0.0, math.hypot(p[0] - c[0], p[1] - c[1]) - r)


def _poly_circle_dist(poly, c, r):
    if len(poly) == 1:
        return _pt_circle_dist(poly[0], c, r)
    return max(0.0, min(_pt_seg_dist(c, poly[i], poly[i + 1])
                        for i in range(len(poly) - 1)) - r)


def _rect_circle_dist(rect, c, r):
    return max(0.0, _pt_rect_dist(c, rect) - r)


# ---------------------------------------------------------------- 理念条目（模板复制自
# build_demo_boards.py::_granularity_principle 形状；构造代码独立，不 import）

def _principle_source_hash(entry):
    view = dict(entry)
    view.pop("source_hash")
    return canonical.canonical_sha256(view)


def _granularity_principle(board_tag, min_gap_mm):
    entry = {
        "principle_id": "P-PART-GRAN-%s" % board_tag,
        "name": "分区聚类粒度先验",
        "intent": {"protects": "走廊通行容量不被过度细分侵占",
                   "sacrifices": "细粒度局部分配自由"},
        "scope": "partitioning",
        "protected_resources": ["corridor_capacity"],
        "target_freedom": "corridor",
        "priority": 50,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": "partition_granularity",
                          "params": {"min_gap_mm": min_gap_mm,
                                     "group_types": ["BUS", "DIFF"]}},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["TASKBOOK-A2-SYNTHBOARD-R1-2026-09-30 §3 W1"],
        "version": "1.0.0",
        "source_hash": "",
    }
    entry["source_hash"] = _principle_source_hash(entry)
    return entry


# ---------------------------------------------------------------- 20 板冻结矩阵
# PREREG-SYNTHBOARD-R1 §20 板矩阵的本体（单源）；seal 字段仅不可布板有：
#   endpoint 0|1 = 密封锁的是封锁目标网的哪个端点；half_mm = 密封垫半尺寸。
BOARD_SPECS = [
    # ---- 10 构造可布板（syn-r*）
    dict(board_id="syn-r01", routable=True, difficulty="low", layers=2,
         size_mm=(40.0, 30.0), nets=5, mode="paired", via_budget=0, seed=101),
    dict(board_id="syn-r02", routable=True, difficulty="low", layers=2,
         size_mm=(40.0, 30.0), nets=6, mode="random", via_budget=0, seed=102),
    dict(board_id="syn-r03", routable=True, difficulty="low", layers=2,
         size_mm=(45.0, 32.0), nets=6, mode="clustered", via_budget=0, seed=103),
    dict(board_id="syn-r04", routable=True, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=8, mode="paired", via_budget=0, seed=104),
    dict(board_id="syn-r05", routable=True, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=8, mode="random", via_budget=1, seed=105),
    dict(board_id="syn-r06", routable=True, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=10, mode="clustered", via_budget=0, seed=106),
    dict(board_id="syn-r07", routable=True, difficulty="high", layers=2,
         size_mm=(55.0, 38.0), nets=10, mode="random", via_budget=2, seed=107),
    dict(board_id="syn-r08", routable=True, difficulty="high", layers=4,
         size_mm=(70.0, 48.0), nets=12, mode="paired", via_budget=0, seed=108),
    dict(board_id="syn-r09", routable=True, difficulty="high", layers=6,
         size_mm=(70.0, 50.0), nets=12, mode="clustered", via_budget=0, seed=109),
    dict(board_id="syn-r10", routable=True, difficulty="high", layers=6,
         size_mm=(80.0, 55.0), nets=14, mode="random", via_budget=2, seed=110),
    # ---- 10 构造不可布板（syn-u*，同族旋钮 + 全层焊盘密封）
    dict(board_id="syn-u01", routable=False, difficulty="low", layers=2,
         size_mm=(40.0, 30.0), nets=5, mode="paired", via_budget=0, seed=201,
         seal=dict(endpoint=0, half_mm=1.6)),
    dict(board_id="syn-u02", routable=False, difficulty="low", layers=2,
         size_mm=(40.0, 30.0), nets=6, mode="random", via_budget=0, seed=202,
         seal=dict(endpoint=1, half_mm=1.8)),
    dict(board_id="syn-u03", routable=False, difficulty="low", layers=2,
         size_mm=(45.0, 32.0), nets=6, mode="clustered", via_budget=0, seed=203,
         seal=dict(endpoint=0, half_mm=1.6)),
    dict(board_id="syn-u04", routable=False, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=8, mode="paired", via_budget=0, seed=204,
         seal=dict(endpoint=1, half_mm=2.2)),
    dict(board_id="syn-u05", routable=False, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=8, mode="random", via_budget=0, seed=205,
         seal=dict(endpoint=0, half_mm=2.2)),
    dict(board_id="syn-u06", routable=False, difficulty="mid", layers=4,
         size_mm=(60.0, 40.0), nets=10, mode="clustered", via_budget=0, seed=206,
         seal=dict(endpoint=0, half_mm=2.4)),
    dict(board_id="syn-u07", routable=False, difficulty="high", layers=2,
         size_mm=(55.0, 38.0), nets=10, mode="random", via_budget=0, seed=207,
         seal=dict(endpoint=1, half_mm=2.6)),
    dict(board_id="syn-u08", routable=False, difficulty="high", layers=4,
         size_mm=(70.0, 48.0), nets=12, mode="paired", via_budget=0, seed=208,
         seal=dict(endpoint=0, half_mm=2.8)),
    dict(board_id="syn-u09", routable=False, difficulty="high", layers=6,
         size_mm=(70.0, 50.0), nets=12, mode="clustered", via_budget=0, seed=209,
         seal=dict(endpoint=1, half_mm=3.0)),
    dict(board_id="syn-u10", routable=False, difficulty="high", layers=6,
         size_mm=(80.0, 55.0), nets=14, mode="random", via_budget=0, seed=210,
         seal=dict(endpoint=0, half_mm=3.2)),
]

_SIDEcar_NOTE = ("v0 口径：端点=隐式端子（无显式 pad_terminals，不入 v5 场景；"
                 "不可布板的密封垫是唯一显式焊盘）")


# ---------------------------------------------------------------- 参考路径构造

def _layer_of_direction(layers, horizontal):
    for lid, d in layers:
        if horizontal and d == "h":
            return lid
        if not horizontal and d == "v":
            return lid
    return layers[-1][0]


class _Placed:
    """一条已铺参考路径（单层或带 1 via 的两层）。"""

    def __init__(self, net_id, pid, a, b, segs, layer, layer2=None, via=None):
        self.net_id = net_id
        self.pid = pid
        self.a, self.b = a, b
        self.segs = segs            # [(pts, layer)...]；pts 为折线点列
        self.layer = layer
        self.layer2 = layer2        # 两层 Z 参考时的第二层
        self.via = via              # via 点（两层参考）

    def polys_on(self, layer):
        return [pts for pts, lay in self.segs if lay == layer]

    def witness(self):
        return {"net_id": self.net_id, "partition_id": self.pid,
                "endpoints": [list(self.a), list(self.b)],
                "segments": [{"layer": lay, "polyline": [list(p) for p in pts]}
                             for pts, lay in self.segs],
                "via": (list(self.via) if self.via else None)}


def _endpoint_ok(pt, placed, seal_disk, W, H, own=None):
    if not (BORDER_MARGIN_MM <= pt[0] <= W - BORDER_MARGIN_MM
            and BORDER_MARGIN_MM <= pt[1] <= H - BORDER_MARGIN_MM):
        return False
    for pl in placed:
        if own is not None and pl.pid == own:
            continue
        if math.hypot(pl.a[0] - pt[0], pl.a[1] - pt[1]) < ENDPOINT_SEP_MM:
            return False
        if math.hypot(pl.b[0] - pt[0], pl.b[1] - pt[1]) < ENDPOINT_SEP_MM:
            return False
        for pts, _lay in pl.segs:
            if _poly_pt_dist(pts, pt) < ENDPOINT_SEP_MM:
                return False
        if pl.via is not None and \
                math.hypot(pl.via[0] - pt[0], pl.via[1] - pt[1]) < ENDPOINT_SEP_MM:
            return False
    if seal_disk is not None:
        c, r = seal_disk
        if math.hypot(c[0] - pt[0], c[1] - pt[1]) < r:
            return False
    return True


def _path_ok(segs, placed, layer_of_seg, W, H, seal_disk, via=None):
    """新参考路径合法性：同层段距 ≥ LANE_SEP；段在边带内；不进密封盘。"""
    for pts, lay in segs:
        for p in pts:
            if not (BORDER_MARGIN_MM - 1e-9 <= p[0] <= W - BORDER_MARGIN_MM + 1e-9
                    and BORDER_MARGIN_MM - 1e-9 <= p[1]
                    <= H - BORDER_MARGIN_MM + 1e-9):
                return False
        if seal_disk is not None and _poly_pt_dist(pts, seal_disk[0]) < seal_disk[1]:
            return False
    for pl in placed:
        for pts_a, lay_a in segs:
            for pts_b in pl.polys_on(lay_a):
                if _poly_poly_dist(pts_a, pts_b) < LANE_SEP_MM:
                    return False
        if via is not None:
            for pts_b, _lay in pl.segs:
                if _poly_pt_dist(pts_b, via) < ENDPOINT_SEP_MM:
                    return False
    if via is not None and seal_disk is not None and \
            math.hypot(via[0] - seal_disk[0][0], via[1] - seal_disk[0][1]) \
            < seal_disk[1]:
        return False
    return True


def _place_paired(rng, n, W, H, layers, seal_disk):
    step = (H - 2.0 * BORDER_MARGIN_MM) / (n + 1)
    if step < max(LANE_SEP_MM, ENDPOINT_SEP_MM):
        raise ConstructionError("paired 泳道间距不足: step=%.3f" % step)
    layer = _layer_of_direction(layers, True)
    placed = []
    for k in range(n):
        yk = _snap(BORDER_MARGIN_MM + step * (k + 1))
        xl = _snap(rng.uniform(BORDER_MARGIN_MM + 0.5, BORDER_MARGIN_MM + 2.5))
        xr = _snap(W - BORDER_MARGIN_MM
                   - rng.uniform(0.5, 2.5))
        a, b = (xl, yk), (xr, yk)
        p = _Placed(None, None, a, b, [((a, b), layer)], layer)
        # paired 泳道天然满足间距；仍过 _path_ok/_endpoint_ok 防边角冲突
        if not (_endpoint_ok(a, placed, seal_disk, W, H)
                and _endpoint_ok(b, placed, seal_disk, W, H)
                and _path_ok(p.segs, placed, layer, W, H, seal_disk)):
            raise ConstructionError("paired 第 %d 泳道放置冲突" % k)
        placed.append(p)
    return placed


def _place_clustered(rng, n, W, H, layers, seal_disk):
    n_cl = max(2, min(4, n // 4))
    while n % n_cl != 0 and n_cl > 2:
        n_cl -= 1
    per = n // n_cl
    layer = _layer_of_direction(layers, True)
    usable_w, usable_h = W - 2 * BORDER_MARGIN_MM, H - 2 * BORDER_MARGIN_MM
    box_w = min(16.0, usable_w / 2.2)
    box_h = min(14.0, usable_h / 2.2)
    lane_step = max(LANE_SEP_MM, ENDPOINT_SEP_MM)
    need_h = per * lane_step + 1.5
    if need_h > box_h:
        box_h = need_h
    if box_h * 2 + 2.0 > usable_h or box_w * 2 + 2.0 > usable_w:
        raise ConstructionError("clustered 簇盒放不下: n=%d" % n)
    cols = 2 if n_cl > 2 else 1
    rows = (n_cl + cols - 1) // cols
    gap_x = (usable_w - cols * box_w) / (cols + 1)
    gap_y = (usable_h - rows * box_h) / (rows + 1)
    placed = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= n_cl:
                break
            x0 = BORDER_MARGIN_MM + gap_x * (col + 1) + box_w * col
            y0 = BORDER_MARGIN_MM + gap_y * (row + 1) + box_h * row
            for j in range(per):
                yk = _snap(y0 + 0.75 + j * lane_step)
                xl = _snap(rng.uniform(x0 + 0.5, x0 + box_w * 0.35))
                xr = _snap(x0 + box_w - rng.uniform(0.5, box_w * 0.35))
                a, b = (xl, yk), (xr, yk)
                p = _Placed(None, None, a, b, [((a, b), layer)], layer)
                if not (_endpoint_ok(a, placed, seal_disk, W, H)
                        and _endpoint_ok(b, placed, seal_disk, W, H)
                        and _path_ok(p.segs, placed, layer, W, H, seal_disk)):
                    raise ConstructionError("clustered 网放置冲突: 簇 %d 线 %d"
                                            % (idx, j))
                placed.append(p)
            idx += 1
    return placed


def _place_random(rng, n, W, H, layers, seal_disk, via_budget):
    lay_ids = [lid for lid, _d in layers]
    placed = []
    for i in range(n):
        ok = False
        for _try in range(600):
            a = (_snap(rng.uniform(BORDER_MARGIN_MM, W - BORDER_MARGIN_MM)),
                 _snap(rng.uniform(BORDER_MARGIN_MM, H - BORDER_MARGIN_MM)))
            b = (_snap(rng.uniform(BORDER_MARGIN_MM, W - BORDER_MARGIN_MM)),
                 _snap(rng.uniform(BORDER_MARGIN_MM, H - BORDER_MARGIN_MM)))
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 6.0:
                continue
            if not (_endpoint_ok(a, placed, seal_disk, W, H)
                    and _endpoint_ok(b, placed, seal_disk, W, H)):
                continue
            h_first = rng.random() < 0.5
            prim = lay_ids[i % len(lay_ids)]
            if i < via_budget and len(lay_ids) >= 2:
                # 两层 Z 参考（via_budget 计数）：拐点换层，via 记 witness
                second = lay_ids[(i + 1) % len(lay_ids)]
                corner = (b[0], a[1]) if h_first else (a[0], b[1])
                seg1, seg2 = ((a, corner), prim), ((corner, b), second)
                p = _Placed(None, None, a, b, [seg1, seg2], prim, second, corner)
                if _path_ok(p.segs, placed, prim, W, H, seal_disk, via=corner) \
                        and _path_ok(p.segs, placed, second, W, H, seal_disk):
                    ok = True
                    break
            else:
                corner = (b[0], a[1]) if h_first else (a[0], b[1])
                p = _Placed(None, None, a, b, [((a, corner), prim),
                                               ((corner, b), prim)], prim)
                if _path_ok(p.segs, placed, prim, W, H, seal_disk):
                    ok = True
                    break
        if not ok:
            raise ConstructionError("random 网放置耗尽: 第 %d 网" % i)
        placed.append(p)
    return placed


def _place_blocked_target(rng, W, H, W_eff, placed, seal_half):
    """不可布板：密封垫放右侧保留带（常规网已铺在 [0, W_eff] 子区，带内空）。

    返回 (seal_center, far_endpoint)；自由对端在全板找（≥ 密封半尺寸+1.5
    离密封心、≥ 端点间距离他网）。"""
    x_lo = W_eff + seal_half + 0.6
    x_hi = W - seal_half - 0.6
    y_lo = BORDER_MARGIN_MM + seal_half + 0.6
    y_hi = H - BORDER_MARGIN_MM - seal_half - 0.6
    if x_lo > x_hi or y_lo > y_hi:
        raise ConstructionError("密封保留带放不下垫（half=%.2f）" % seal_half)
    for _try in range(400):
        c = (_snap(rng.uniform(x_lo, x_hi)), _snap(rng.uniform(y_lo, y_hi)))
        # 带内空，只防常规网端点意外贴带界（W_eff 边距已含）
        clash = False
        for pl in placed:
            for pts, _lay in pl.segs:
                if _poly_pt_dist(pts, c) < seal_half + 1.0:
                    clash = True
                    break
            if math.hypot(pl.a[0] - c[0], pl.a[1] - c[1]) < seal_half + 1.0 or \
                    math.hypot(pl.b[0] - c[0], pl.b[1] - c[1]) < seal_half + 1.0:
                clash = True
            if clash:
                break
        if clash:
            continue
        for _t2 in range(400):
            b = (_snap(rng.uniform(BORDER_MARGIN_MM, W - BORDER_MARGIN_MM)),
                 _snap(rng.uniform(BORDER_MARGIN_MM, H - BORDER_MARGIN_MM)))
            if math.hypot(b[0] - c[0], b[1] - c[1]) < seal_half + 1.5:
                continue
            if not _endpoint_ok(b, placed, None, W, H):
                continue
            return c, b
    raise ConstructionError("封锁目标网放置耗尽")


def _place_keepouts(rng, n_ko, W, H, refs, clear, seal_rect, endpoints):
    kos = []
    for _ in range(n_ko):
        placed_ko = None
        for _try in range(500):
            w = _snap(rng.uniform(2.0, 6.0))
            h = _snap(rng.uniform(2.0, 6.0))
            x0 = _snap(rng.uniform(0.5, W - 0.5 - w))
            y0 = _snap(rng.uniform(0.5, H - 0.5 - h))
            rect = (x0, y0, x0 + w, y0 + h)
            bad = False
            for pl in refs:
                for pts, _lay in pl.segs:
                    if _poly_rect_dist(pts, rect) < clear:
                        bad = True
                        break
                if bad:
                    break
            if not bad:
                for ep in endpoints:
                    if _pt_rect_dist(ep, rect) < max(1.5, clear):
                        bad = True
                        break
            if not bad and seal_rect is not None and \
                    _rect_dist(rect, seal_rect) < max(clear, 0.5):
                bad = True
            if not bad:
                for r2 in kos:
                    if _rect_dist(rect, (r2[0], r2[1], r2[0] + r2[2],
                                         r2[1] + r2[3])) < 0.5:
                        bad = True
                        break
            if not bad:
                placed_ko = (x0, y0, w, h)
                break
        if placed_ko is not None:
            kos.append(placed_ko)
    return kos


def _rect_dist(ra, rb):
    dx = max(ra[0] - rb[2], rb[0] - ra[2], 0.0)
    dy = max(ra[1] - rb[3], rb[1] - ra[3], 0.0)
    return math.hypot(dx, dy)


def _place_holes(rng, n_h, W, H, refs, clear, seal_rect, endpoints, kos):
    holes = []
    for _ in range(n_h):
        got = None
        for _try in range(500):
            r = rng.choice((0.3, 0.45, 0.6))
            c = (_snap(rng.uniform(BORDER_MARGIN_MM, W - BORDER_MARGIN_MM)),
                 _snap(rng.uniform(BORDER_MARGIN_MM, H - BORDER_MARGIN_MM)))
            bad = False
            for pl in refs:
                for pts, _lay in pl.segs:
                    if _poly_circle_dist(pts, c, r) < clear + r + \
                            HOLE_MARGIN_MM + TRACK_HALF_MM:
                        bad = True
                        break
                if bad:
                    break
            if not bad:
                for ep in endpoints:
                    if _pt_circle_dist(ep, c, r) < 1.5 + r:
                        bad = True
                        break
            if not bad and seal_rect is not None:
                if _rect_circle_dist(seal_rect, c, r) < 1.0 + r:
                    bad = True
            if not bad:
                for (kx, ky, kw, kh) in kos:
                    if _rect_circle_dist((kx, ky, kx + kw, ky + kh), c, r) \
                            < 0.25 + r:
                        bad = True
                        break
            if not bad:
                for (hx, hy, hr) in holes:
                    if math.hypot(hx - c[0], hy - c[1]) < hr + r + 0.75:
                        bad = True
                        break
            if not bad:
                got = (c[0], c[1], r)
                break
        if got is not None:
            holes.append(got)
    return holes


# ---------------------------------------------------------------- 单板构造

def build_synth_board(spec):
    """旋钮 spec → (board dict, sidecar dict)。确定性：同 spec 同字节。"""
    rng = random.Random(spec["seed"])
    W, H = spec["size_mm"]
    difficulty = spec["difficulty"]
    routable = spec["routable"]
    clear = OB_CLEAR_MM[difficulty]
    layers = _STACKUPS[spec["layers"]]
    lay_ids = [lid for lid, _d in layers]

    seal = spec.get("seal") if not routable else None
    if seal is not None and seal["half_mm"] < SEAL_HALF_FLOOR_MM:
        raise ConstructionError("密封垫半尺寸 %.3f 低于下界 %.3f"
                                % (seal["half_mm"], SEAL_HALF_FLOOR_MM))

    # 1) 常规网参考路径（不可布板：常规网铺在 [0, W_eff] 子区，右侧留密封带）
    mode = spec["mode"]
    reserve = 2.0 * seal["half_mm"] + 3.0 if seal is not None else 0.0
    W_eff = W - reserve
    if seal is not None and W_eff < 3.0 * BORDER_MARGIN_MM + 8.0:
        raise ConstructionError("密封保留带挤压常规网区: W_eff=%.1f" % W_eff)
    if mode == "paired":
        placed = _place_paired(rng, spec["nets"], W_eff, H, layers, None)
    elif mode == "clustered":
        placed = _place_clustered(rng, spec["nets"], W_eff, H, layers, None)
    elif mode == "random":
        placed = _place_random(rng, spec["nets"], W_eff, H, layers, None,
                               spec["via_budget"])
    else:
        raise ConstructionError("未知 pad_layout_mode: %r" % mode)

    for i, pl in enumerate(placed):
        pl.net_id = "N%02d" % (i + 1)
        pl.pid = "P%02d" % (i + 1)

    seal_center = None
    blocked = None
    if not routable:
        c, b = _place_blocked_target(rng, W, H, W_eff, placed, seal["half_mm"])
        if seal["endpoint"] == 0:
            a_pt, b_pt = c, b
        else:
            a_pt, b_pt = b, c
        blocked = _Placed("NBLK", "PBLK", a_pt, b_pt, [], lay_ids[0])
        blocked_layer = lay_ids[0]
        seal_center = c

    # 2) 障碍（keepout zones + 板固孔）：避开全部参考路径 clear 带
    endpoints = [pl.a for pl in placed] + [pl.b for pl in placed]
    seal_rect = None
    if seal_center is not None:
        hs = seal["half_mm"]
        seal_rect = (seal_center[0] - hs, seal_center[1] - hs,
                     seal_center[0] + hs, seal_center[1] + hs)
        endpoints = [blocked.b]
    kos = _place_keepouts(rng, OB_KEEPOUTS[difficulty], W, H, placed, clear,
                          seal_rect, endpoints)
    holes = _place_holes(rng, OB_HOLES[difficulty], W, H, placed, clear,
                         seal_rect, endpoints, kos)

    # 3) 板装配
    partitions = []
    nets = []
    for pl in placed:
        partitions.append({
            "partition_id": pl.pid, "ptype": "MISC",
            "geometry": {"endpoints": [[pl.a[0], pl.a[1]], [pl.b[0], pl.b[1]]]},
            "layer_policy": pl.layer,
            "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0.0, "speed_class": "low_speed",
            "planned_width": 0.2,
            "note": "synth 参考路径层 %s%s" % (
                pl.layer, ("+%s via" % pl.layer2) if pl.layer2 else ""),
        })
        nets.append({"net_id": pl.net_id, "net_class": "MISC",
                     "partitions": [pl.pid]})
    if blocked is not None:
        partitions.append({
            "partition_id": blocked.pid, "ptype": "MISC",
            "geometry": {"endpoints": [[blocked.a[0], blocked.a[1]],
                                       [blocked.b[0], blocked.b[1]]]},
            "layer_policy": blocked_layer,
            "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0.0, "speed_class": "low_speed",
            "planned_width": 0.2,
            "note": "封锁目标网：端点 %d 落密封垫心（构造性阻断）"
                    % seal["endpoint"],
        })
        nets.append({"net_id": "NBLK", "net_class": "MISC",
                     "partitions": [blocked.pid]})
        hs = seal["half_mm"]
        partitions.append({
            "partition_id": "PSEAL", "ptype": "MISC",
            "geometry": {"endpoints": [[seal_center[0], seal_center[1]],
                                       [seal_center[0], seal_center[1]]],
                         "pad_terminals": [
                             {"endpoint": 0, "layers": "all", "shape": "rect",
                              "size_mm": [2.0 * hs, 2.0 * hs]},
                             {"endpoint": 1, "layers": "all", "shape": "rect",
                              "size_mm": [2.0 * hs, 2.0 * hs]}]},
            "layer_policy": lay_ids[0],
            "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0.0, "speed_class": "low_speed",
            "planned_width": 0.2,
            "note": "密封载体网（退化分区 + all-layer 通孔焊盘 %.1fx%.1fmm）："
                    "R5 中心线口径下封锁目标网端点逃逸邻域全层封死"
                    % (2.0 * hs, 2.0 * hs),
        })
        nets.append({"net_id": "NSEAL", "net_class": "MISC",
                     "partitions": ["PSEAL"]})

    zones = [{"zone_id": "KO%02d" % (i + 1), "kind": "keepout",
              "rect": {"x_min": kx, "y_min": ky, "x_max": kx + kw,
                       "y_max": ky + kh},
              "layers": "all",
              "note": "合成障碍（难度 %s；离参考路径净空 ≥ %.2fmm）"
                      % (difficulty, clear)}
             for i, (kx, ky, kw, kh) in enumerate(kos)]
    holes_doc = [{"pos_mm": [hx, hy], "drill_mm": 2.0 * hr, "plated": False,
                  "shape": "circle"} for (hx, hy, hr) in holes]

    board = {
        "schema_version": "v5.board.v1",
        "board_id": spec["board_id"],
        "stackup": [{"id": lid, "kind": "signal",
                     "preferred_direction": d, "available": True}
                    for lid, d in layers],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": W, "y_max": H},
        "zones": zones,
        "partitions": partitions,
        "nets": nets,
        "hard_rules": _HARD_RULES,
        "principle_registry": [
            _granularity_principle(spec["board_id"].upper().replace("-", ""),
                                   MIN_GAP_BY_DIFFICULTY[difficulty])],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "synthetic:boards/build_synth_boards.py#%s"
                          % spec["board_id"],
            "source_sha256": _sha256_file(_SCRIPT_PATH),
            "adapter": GENERATOR_VERSION,
        },
    }
    if holes_doc:
        board["holes"] = holes_doc

    # 4) 构造保证自查 + sidecar
    guarantee = _guarantee_check(spec, board, placed, kos, holes, seal_rect,
                                 seal, seal_center, blocked, clear, W, H)
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    load_board(board)  # fail-closed：schema + 哈希链 + 跨字段

    witness = {"reference_paths": [pl.witness() for pl in placed]} \
        if routable else {
        "blocked_net": "NBLK", "blocked_partition": "PBLK",
        "blocked_endpoint_index": seal["endpoint"],
        "seal": {"partition": "PSEAL", "net": "NSEAL",
                 "center_mm": [seal_center[0], seal_center[1]],
                 "size_mm": [2.0 * seal["half_mm"], 2.0 * seal["half_mm"]],
                 "pad_layers": "all（逐信号层一枚矩形固定铜）",
                 "escape_bound_mm": round(ESCAPE_REACH_MM + SNAP_BOUND_MM, 4),
                 "seal_half_mm": seal["half_mm"]},
        "other_nets_reference_paths": [pl.witness() for pl in placed],
        "rationale": ("封锁目标网端点逃逸邻域（≤ %.3fmm）整体落入异网 all-layer "
                      "焊盘铜内：R5 中心线口径下 8 向边/换层孔距垫面 0 < R5-EPS "
                      "全封，A* 零展开；rip-up 只摘 route: 铜，fixed: 焊盘不可摘"
                      "——构造性无解" % (ESCAPE_REACH_MM + SNAP_BOUND_MM))}
    sidecar = {
        "provenance": {"generator": "boards/build_synth_boards.py",
                       "generator_version": GENERATOR_VERSION,
                       "board_sha256": board["provenance"]["board_sha256"]},
        "board_id": spec["board_id"],
        "board_file": "%s.board.v1.json" % spec["board_id"],
        "knobs": {"workspace_mm": {"x": W, "y": H}, "layers": spec["layers"],
                  "net_count": spec["nets"], "pad_layout_mode": mode,
                  "obstacle_density": difficulty, "via_budget":
                      spec["via_budget"], "seed": spec["seed"]},
        "difficulty": difficulty,
        "routable": routable,
        "guarantee_type": ("constructed-routable" if routable else
                           "constructed-block:all-layer-pad-seal"),
        "witness": witness,
        "placed": {"n_nets_normal": len(placed),
                   "n_nets_total": len(nets),
                   "n_keepouts_placed": len(kos),
                   "n_keepouts_target": OB_KEEPOUTS[difficulty],
                   "n_holes_placed": len(holes),
                   "n_holes_target": OB_HOLES[difficulty],
                   "n_vias_in_reference": sum(1 for pl in placed
                                              if pl.via is not None)},
        "guarantee_check": guarantee,
        "endpoint_note": _SIDEcar_NOTE,
        "engine_facts": {"grid_pitch_mm": GRID_PITCH_MM, "r5_mm": R5_MM,
                         "escape_reach_mm": ESCAPE_REACH_MM,
                         "via_radius_mm": VIA_RADIUS_MM,
                         "lane_sep_mm": LANE_SEP_MM,
                         "obstacle_clear_mm": clear},
    }
    return board, sidecar


def _guarantee_check(spec, board, placed, kos, holes, seal_rect, seal,
                     seal_center, blocked, clear, W, H):
    """构造保证自查（独立重算，不信任放置过程内部状态）。"""
    checks = {}
    # G1 同层参考路径中心线间距 ≥ LANE_SEP
    worst = None
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            for pts_a, lay_a in placed[i].segs:
                for pts_b in placed[j].polys_on(lay_a):
                    d = _poly_poly_dist(pts_a, pts_b)
                    worst = d if worst is None else min(worst, d)
    checks["g1_min_same_layer_path_gap_mm"] = (None if worst is None
                                               else round(worst, 4))
    if worst is not None and worst < LANE_SEP_MM - 1e-9:
        raise ConstructionError("G1 失守: %.4f" % worst)
    # G2 障碍-参考路径净空
    worst_k = None
    for pl in placed:
        for pts, _lay in pl.segs:
            for (kx, ky, kw, kh) in kos:
                d = _poly_rect_dist(pts, (kx, ky, kx + kw, ky + kh))
                worst_k = d if worst_k is None else min(worst_k, d)
    checks["g2_min_keepout_path_gap_mm"] = (None if worst_k is None
                                            else round(worst_k, 4))
    if worst_k is not None and worst_k < clear - 1e-9:
        raise ConstructionError("G2 失守: %.4f" % worst_k)
    worst_h = None
    for pl in placed:
        for pts, _lay in pl.segs:
            for (hx, hy, hr) in holes:
                d = _poly_circle_dist(pts, (hx, hy), hr)
                worst_h = d if worst_h is None else min(worst_h, d)
    checks["g3_min_hole_path_gap_mm"] = (None if worst_h is None
                                         else round(worst_h, 4))
    if worst_h is not None and worst_h < clear - 1e-9:
        raise ConstructionError("G3 失守: %.4f" % worst_h)
    # G4 参考路径/端点在板边禁布带内缩界内
    ok = True
    for pl in placed:
        for pts, _lay in pl.segs:
            for p in pts:
                if not (BORDER_MARGIN_MM <= p[0] <= W - BORDER_MARGIN_MM
                        and BORDER_MARGIN_MM <= p[1] <= H - BORDER_MARGIN_MM):
                    ok = False
    checks["g4_paths_inside_border_margin"] = ok
    if not ok:
        raise ConstructionError("G4 失守")
    # G5（不可布板）密封覆盖逃逸邻域 + 他网参考离密封净空
    if seal_center is not None and blocked is not None:
        bound = ESCAPE_REACH_MM + SNAP_BOUND_MM
        checks["g5_seal_half_mm"] = seal["half_mm"]
        checks["g5_escape_bound_mm"] = round(bound, 4)
        if seal["half_mm"] < bound + 0.25:
            raise ConstructionError("G5 失守: 密封半尺寸不足")
        worst_s = None
        for pl in placed:
            for pts, _lay in pl.segs:
                d = _poly_rect_dist(pts, seal_rect)
                worst_s = d if worst_s is None else min(worst_s, d)
        checks["g5_min_other_path_gap_to_seal_mm"] = (None if worst_s is None
                                                      else round(worst_s, 4))
        # 他网参考路径对密封矩形 ≥ R5(0.5)+0.25 裕量（放置盘半径 half+1.0 已含）
        if worst_s is not None and worst_s < 0.75 - 1e-9:
            raise ConstructionError("G5 失守: 他网参考路径贴密封垫")
        far = blocked.b if seal["endpoint"] == 0 else blocked.a
        checks["g5_blocked_far_endpoint_gap_mm"] = round(
            math.hypot(far[0] - seal_center[0], far[1] - seal_center[1]), 4)
        if math.hypot(far[0] - seal_center[0], far[1] - seal_center[1]) \
                < seal["half_mm"] + 1.5:
            raise ConstructionError("G5 失守: 封锁网对端贴密封垫")
    checks["all_passed"] = True
    return checks


def _sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- 落盘

def build_all(out_dir=OUT_DIR):
    """构造 20 板并按 canonical 字节写盘（板 + sidecar）。

    返回 [(board_path, sidecar_path, 文件 sha256, 是否字节有变)]。
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for spec in BOARD_SPECS:
        board, sidecar = build_synth_board(spec)
        data = canonical.canonical_json(board)
        bpath = os.path.join(out_dir, "%s.board.v1.json" % board["board_id"])
        changed = True
        if os.path.exists(bpath):
            with open(bpath, "rb") as f:
                changed = f.read() != data
        with open(bpath, "wb") as f:
            f.write(data)
        spath = os.path.join(out_dir, "%s.sidecar.json" % board["board_id"])
        with open(spath, "wb") as f:
            f.write(canonical.canonical_json(sidecar))
        results.append((bpath, spath, hashlib.sha256(data).hexdigest(), changed))
    return results


def main():
    for bpath, spath, digest, changed in build_all():
        print("%s  sha256=%s…  %s" % (bpath, digest[:16],
                                      "内容有变，已覆写" if changed
                                      else "零 diff 覆写"))
        print("  sidecar: %s" % spath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
