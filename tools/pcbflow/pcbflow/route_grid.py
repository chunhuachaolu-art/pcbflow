"""④ FC2：描线 + 残网三态求解内核（SPEC v1.3 §10.1 步骤 3/4、§10.3、§15 FC2）。

组成（生成器模式：零落盘、零子进程；写板仅限快照副本且经 board_writer）：

1. 描线（§10.1 步骤 3）：复用 pcbagent 锁定 adapter（Region/A* + L1 精确终判；
   NEXT.md adapter 锁=revc-fc1/run-manifest-route.json，内容 hash 钉死于
   run-manifest）。dry-run 与重放板均 ripup=False（冻结语义：不拆既有铜）。
2. 残网三态（§10.1 步骤 4/§10.3）：
   - SAT：Router witness + L1 终判全过（witness 即证据）；
   - UNSAT：受限阻塞证书——硬阻塞栅格模型（0.05mm 格上点/段距 <
     要求间距−EPS 才判堵，不确定带不虚堵）+ 源侧 BFS 闭包 + 割元素逐条
     几何论据 + 独立复核器（论据数值重算 + 仅信任割条目的封闭性 BFS）；
     证书作用域=restricted（格心 4 邻格网/单窗/端点 8 邻辐条），如实随行；
   - UNKNOWN：区域超窗 / 无 witness 且模型内存在候选通径（不足证）/
     registry 缺档（missing_basis）/ 求解预算耗尽。
   无证书不写 UNSAT（HANDOFF §4 红线）。

pcbagent adapter 经 sys.path 显式挂载（tools/）；被导入模块逐一文本扫描
拒绝 subprocess（bridge.py 有 subprocess，禁入 pcbflow 导入链）。
常量内聚本模块，config.py 零新增（FC1 惯例）。
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import deque

from . import config, hashing

# ---- FC2 常量（内聚本模块） --------------------------------------------------
FC2_SCHEMA = "1.3"

# 回测输入（只读；HANDOFF 输入表：b3=靶 1 冻结布局=S4 上界同一板态）
F3_FROZEN_BOARD = os.path.join(
    config.REVC_DIR, "pcbagent-out", "b3", "snapshot-01.kicad_pcb")
OPENS_TRUTH_NOTE = "opens.csv=65 行（61 信号+4 GND）；FC2 分母=61 信号断点"

# 证书模型（restricted scope，逐份随行）
CERT_RES_MM = 0.05            # 格距（=pcbagent L3_RES 同量级）
CERT_EPS_MM = 1e-9            # 硬阻塞判定的严格内缩（不确定带开放）
CERT_MARGIN_MM = 1.0          # 证书区域窗=端点 bbox 外扩（restricted）
CERT_WINDOW_NODES = 600_000   # 模型节点窗（2 信号层格 + 过孔位）
CERT_SPOKE_NEIGHBORS = 8      # 端点辐条=8 邻格心（模型定义内穷举）
CERT_HOLE_CLEARANCE = 0.25    # min_hole_clearance（.kicad_pro rules）
CERT_EDGE_CLEARANCE = 0.5     # min_copper_edge_clearance

# pcbagent adapter 消费面（run-manifest 实锁；bridge.py 拒绝）
PCBAGENT_ADAPTER_FILES = ("mirror.py", "legality.py", "geometry.py",
                          "router.py", "planner.py", "config.py", "sexpr.py")


def pcbagent_fc2_lock():
    """FC2 实际消费的 pcbagent 模块内容 hash（run-manifest 用）。"""
    base = os.path.join(config.WORKSPACE_ROOT, "tools", "pcbagent", "pcbagent")
    out = {"available": os.path.isdir(base), "modules": {},
           "subprocess_scan": "import-chain text-scan; bridge.py rejected"}
    for name in PCBAGENT_ADAPTER_FILES:
        p = os.path.join(base, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                out["modules"][name] = hashing.sha256_bytes(f.read())
    return out


def load_adapter():
    """导入 pcbagent adapter（几何/合法性/镜像/路由），导入链无 subprocess。

    sys.path 挂 tools/pcbagent（包根=tools/pcbagent/pcbagent；挂 tools/ 会
    命中无 __init__ 的同名命名空间目录——实测坑）。"""
    pkg_root = os.path.join(config.WORKSPACE_ROOT, "tools", "pcbagent")
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    import pcbagent.geometry as pa_geometry
    import pcbagent.legality as pa_legality
    import pcbagent.mirror as pa_mirror
    import pcbagent.planner as pa_planner
    import pcbagent.router as pa_router
    for mod in (pa_geometry, pa_legality, pa_mirror, pa_planner, pa_router):
        with open(mod.__file__, "rb") as f:
            src = f.read().decode("utf-8", "replace")
        if "import subprocess" in src or "from subprocess" in src:
            raise RuntimeError("pcbagent adapter 导入链含 subprocess: %s"
                               % mod.__name__)
    return {"BoardMirror": pa_mirror.BoardMirror,
            "Legality": pa_legality.Legality,
            "Router": pa_router.Router,
            "LAYERS": pa_router.LAYERS,
            "geometry": pa_geometry,
            "router_mod": pa_router}


def board_model(project_dir):
    """只读板镜像（pcbagent BoardMirror）+ 事实 hash。"""
    pa = load_adapter()
    mirror = pa["BoardMirror"](project_dir)
    with open(mirror.pcb_path, "rb") as f:
        sha = hashing.sha256_bytes(f.read())
    return {"mirror": mirror, "pcb_path": mirror.pcb_path,
            "pcb_sha256": sha, "pa": pa}


# ---- 描线（§10.1 步骤 3，pcbagent 锁定 adapter） ----------------------------
def _endpoint_closure_fail(plan, ax, ay, alayers, bx, by, blayers):
    """C1 端点闭合防御断言（REPAIR-P3S W-B；M0 锚变更用户已授权 2026-09-22）。

    Router 收官判定只核坐标不核端点层（VERIFY-1 ETH_REF_CLK 假闭合立案，
    out/coreboard-verify1/ §5 第 4 条）；本函数在 route_one/route_one_added
    返回前对终态做单网复核（电气口径）：
    - 端点闭合：端点坐标处存在段端点且其层 ∈ 允许集；或端点坐标处有 via
      过渡（合法形态=端点打孔下内层再走线，via 提供到允许层的过渡——
      test_fb1_ripup_accounting 真实分布实证；adapter 世界 via 跨全信号
      层对）。提案 §5.3 回退条款：段序形状假设与真实分布不相容时按
      「任一段命中端点坐标且该段层∈允许集」落断言；
    - vias 链路（连通分量口径）：两端点锚点须落同一连通分量。
    返回违例细目列表（调用侧 ok=False + fail="endpoint_layer_violation"
    诚实失败）或 None（通过——通过路径输出与旧版逐字节一致，零误伤）。
    """
    if not plan.ok:
        return None
    segs = list(plan.segments or [])
    vias = list(plan.vias or [])
    al, bl = set(alayers), set(blayers)
    details = []
    if not segs:
        if (abs(ax - bx) > 1e-6) or (abs(ay - by) > 1e-6):
            details.append("空路径但两端点坐标不同")
        return details or None
    parent = {}

    def _find(n):
        while parent.setdefault(n, n) != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def _union(p, q):
        rp, rq = _find(p), _find(q)
        if rp != rq:
            parent[rp] = rq

    def _key(x, y):
        return (round(x, 3), round(y, 3))

    for (L, x1, y1, x2, y2) in segs:
        _union((L,) + _key(x1, y1), (L,) + _key(x2, y2))
    for (vx, vy) in vias:
        anchors = [n for n in list(parent)
                   if abs(n[1] - vx) <= 1e-3 and abs(n[2] - vy) <= 1e-3]
        for i in range(1, len(anchors)):
            _union(anchors[0], anchors[i])

    def _anchor_nodes(x, y, allowed):
        nodes = [n for n in parent
                 if abs(n[1] - x) <= 1e-3 and abs(n[2] - y) <= 1e-3]
        via_hit = any(abs(vx - x) <= 1e-3 and abs(vy - y) <= 1e-3
                      for (vx, vy) in vias)
        if via_hit and nodes:
            return list(nodes)          # via 过渡：端点处全层锚点可达
        return [n for n in nodes if n[0] in allowed]

    a_anchors = _anchor_nodes(ax, ay, al)
    b_anchors = _anchor_nodes(bx, by, bl)
    if not a_anchors:
        details.append("a 端 (%r,%r) 无允许层落点且无 via 过渡"
                       % (ax, ay))
    if not b_anchors:
        details.append("b 端 (%r,%r) 无允许层落点且无 via 过渡"
                       % (bx, by))
    if a_anchors and b_anchors and not any(
            _find(p) == _find(q) for p in a_anchors for q in b_anchors):
        details.append("vias 链路分量复核：两端点锚点不在同一连通分量")
    return details or None


def route_one(bm, net, ax, ay, alayers, bx, by, blayers, log=None):
    """单断点描线：Router.route_net（ripup=False，冻结语义）。纯内存。

    返回归一化 dict（无 wall-clock 字段；run_s 不入核心产物）。"""
    pa = bm["pa"]
    router = pa["Router"](bm["mirror"],
                          legality=pa["Legality"](bm["mirror"]),
                          corridor_of=None, log=log or (lambda *_a: None))
    plan = router.route_net(net, (ax, ay, frozenset(alayers)),
                            (bx, by, frozenset(blayers)), ripup=False)
    ep_details = _endpoint_closure_fail(plan, ax, ay, alayers, bx, by, blayers)
    out = {
        "net": net,
        "ok": bool(plan.ok and ep_details is None),
        "fail": ("endpoint_layer_violation" if ep_details is not None
                 else plan.fail),
        "blocks": [str(b) for b in (plan.blocks or [])],
        "width": plan.width,
        "via_size": plan.via_size, "via_drill": plan.via_drill,
        "refine_rounds": plan.refine_rounds,
        "region_mm": round(plan.region_mm, 3),
        "segments": [[int(L), round(x1, 4), round(y1, 4),
                      round(x2, 4), round(y2, 4)]
                     for (L, x1, y1, x2, y2) in plan.segments],
        "vias": [[round(x, 4), round(y, 4)] for (x, y) in plan.vias],
        "length_mm": round(sum(math.hypot(x2 - x1, y2 - y1)
                               for (_L, x1, y1, x2, y2) in plan.segments), 3),
    }
    if ep_details is not None:
        out["endpoint_audit"] = ep_details
    return out


def route_one_added(bm, net, ax, ay, alayers, bx, by, blayers,
                    added_routes=None, log=None):
    """单断点描线（同批先落网感知版）：与 route_one 同一 Region/A*+L1 路径，
    但把 added_routes（同批已规划网 route dict 列表）作为 added_prims 注入
    Region（pcbagent Region 原生语义：带网名按 clearance_between 取距）。

    L1 终判仍只对静态镜像铜（pcbagent 原口径）；同批互检由批 DRC 裁决
    （§10.4）。added_routes 中与目标同网的 route 跳过（同电位不互堵；
    Region 对 added_prims 无同网豁免——pcbagent 原用法只注入异网铜）。"""
    pa = bm["pa"]
    added_prims = _routes_to_added_prims(
        [r for r in (added_routes or []) if r["net"] != net])
    router = pa["Router"](bm["mirror"],
                          legality=pa["Legality"](bm["mirror"]),
                          corridor_of=None, log=log or (lambda *_a: None))
    plan = router._fresh_plan(net, (ax, ay, frozenset(alayers)),
                              (bx, by, frozenset(blayers)))
    bbox = router._region_bbox(plan)
    p = router._try_route(plan, bbox, added_prims=added_prims)
    ep_details = _endpoint_closure_fail(p, ax, ay, alayers, bx, by, blayers)
    out = {
        "net": net,
        "ok": bool(p.ok and ep_details is None),
        "fail": ("endpoint_layer_violation" if ep_details is not None
                 else p.fail),
        "blocks": [str(b) for b in (p.blocks or [])],
        "width": p.width,
        "via_size": p.via_size, "via_drill": p.via_drill,
        "refine_rounds": p.refine_rounds,
        "region_mm": round(p.region_mm, 3),
        "segments": [[int(L), round(x1, 4), round(y1, 4),
                      round(x2, 4), round(y2, 4)]
                     for (L, x1, y1, x2, y2) in p.segments],
        "vias": [[round(x, 4), round(y, 4)] for (x, y) in p.vias],
        "length_mm": round(sum(math.hypot(x2 - x1, y2 - y1)
                               for (_L, x1, y1, x2, y2) in p.segments), 3),
    }
    if ep_details is not None:
        out["endpoint_audit"] = ep_details
    return out


def _routes_to_added_prims(routes):
    """route dict 列表 → pcbagent Region added_prims（(prim, L|set, net)）。"""
    prims = []
    for r in routes:
        for (L, x1, y1, x2, y2) in r["segments"]:
            prims.append(((("seg", x1, y1, x2, y2), r["width"] / 2.0),
                          L, r["net"]))
        for (x, y) in r["vias"]:
            prims.append(((("pt", x, y), r["via_size"] / 2.0),
                          frozenset((0, 6)), r["net"]))
    return prims


def layer_ids_of(descs, pa_layers):
    """opens.csv 端点层描述 → pcbagent 层号集合。"""
    m = {"F.Cu": [pa_layers[0]], "In2.Cu": [pa_layers[1]],
         "B.Cu": [2], "In1.Cu": [4]}
    out = []
    for d in descs:
        out.extend(m.get(d, [pa_layers[0], pa_layers[1]]))
    return out or [pa_layers[0], pa_layers[1]]


# ---- 受限阻塞证书（§10.3 UNSAT 证据） ---------------------------------------
class _PrimIndex:
    """区域内异网铜/孔的空间桶索引（1mm 桶），供格阻塞与边检查近邻查询。"""

    BUCKET = 1.0

    def __init__(self, bm, net, bb, layer_ids):
        G = bm["pa"]["geometry"]
        m = bm["mirror"]
        self.g = G
        self.copper = []      # (layer, prim, req, bbox)
        self.holes = []       # (prim, bbox)
        self.edge_segs = []   # (x1,y1,x2,y2)
        self._buckets = {}    # (bx,by) -> [(kind, idx, layer)]
        extra = 1.5
        for L in layer_ids:
            for it in m.query_copper(L, bb[0], bb[1], bb[2], bb[3],
                                     extra=extra):
                if it.net and it.net == net:
                    continue
                req = m.clearance_between(net, it.net)
                for prim in it.prims:
                    pb = G.prim_bbox(prim)
                    self.copper.append((L, prim, req, pb))
            for h in m.query_holes(L, bb[0], bb[1], bb[2], bb[3],
                                   extra=extra):
                self.holes.append((h.prim, G.prim_bbox(h.prim)))
        self.edge_segs = list(m.edge_segs)
        for i, (_L, _p, _r, pb) in enumerate(self.copper):
            self._put("cu", i, pb)
        for i, (_p, pb) in enumerate(self.holes):
            self._put("ho", i, pb)
        for i, (x1, y1, x2, y2) in enumerate(self.edge_segs):
            self._put("ed", i, (min(x1, x2), min(y1, y2),
                                max(x1, x2), max(y1, y2)))

    def _put(self, kind, idx, pb):
        b = self.BUCKET
        for bx in range(int(math.floor(pb[0] / b)),
                        int(math.floor(pb[2] / b)) + 1):
            for by in range(int(math.floor(pb[1] / b)),
                            int(math.floor(pb[3] / b)) + 1):
                self._buckets.setdefault((bx, by), []).append((kind, idx))

    def near(self, x0, y0, x1, y1):
        """bbox 近邻项：铜 (layer, prim, req, bbox)、孔 (prim, bbox)、边。"""
        b = self.BUCKET
        cu, ho, ed = [], [], []
        seen = set()
        for bx in range(int(math.floor(x0 / b)),
                        int(math.floor(x1 / b)) + 1):
            for by in range(int(math.floor(y0 / b)),
                            int(math.floor(y1 / b)) + 1):
                for (kind, i) in self._buckets.get((bx, by), ()):
                    if (kind, i) in seen:
                        continue
                    seen.add((kind, i))
                    if kind == "cu":
                        cu.append(self.copper[i])
                    elif kind == "ho":
                        ho.append(self.holes[i])
                    else:
                        ed.append(self.edge_segs[i])
        return cu, ho, ed


def build_cert_model(bm, net, width, via_size, via_drill,
                     ax, ay, bx, by, margin_mm=CERT_MARGIN_MM,
                     window_nodes=None):
    """受限栅格模型（硬阻塞语义：点/段距 < 要求−EPS 才判堵）。

    window_nodes：模型节点窗上限（实验参数化入口，WIN-1）；None（默认）=
    调用时读模块常量 CERT_WINDOW_NODES（600_000）——冻结链全部调用点零
    改动、行为字节不变，且保持既有测试对常量的调用时 monkeypatch 语义。

    返回 (model, None) 或 (None, (unknown_reason, detail))。"""
    if window_nodes is None:
        window_nodes = CERT_WINDOW_NODES
    G = bm["pa"]["geometry"]
    m = bm["mirror"]
    board_bb = m.bbox()
    x0 = max(min(ax, bx) - margin_mm, board_bb[0])
    y0 = max(min(ay, by) - margin_mm, board_bb[1])
    x1 = min(max(ax, bx) + margin_mm, board_bb[2])
    y1 = min(max(ay, by) + margin_mm, board_bb[3])
    nx = int(math.floor((x1 - x0) / CERT_RES_MM)) + 1
    ny = int(math.floor((y1 - y0) / CERT_RES_MM)) + 1
    nodes = 3 * nx * ny
    if nodes > window_nodes:
        return None, ("region_over_window",
                      {"nodes": nodes, "window": window_nodes})
    layer_ids = list(bm["pa"]["LAYERS"])
    hw = width / 2.0
    pad = hw + 0.5
    idx = _PrimIndex(bm, net, (x0 - pad, y0 - pad, x1 + pad, y1 + pad),
                     layer_ids)

    def center(ix, iy):
        return (x0 + ix * CERT_RES_MM, y0 + iy * CERT_RES_MM)

    # 格硬阻塞：逐 prim 的局部窗口扫描（bbox + req + hw 外的格不查）
    cell_blocked = {L: set() for L in layer_ids}
    for (L, prim, req, pb) in idx.copper:
        rad = req + hw
        ix0 = max(0, int(math.floor((pb[0] - rad - x0) / CERT_RES_MM)))
        ix1 = min(nx - 1, int(math.ceil((pb[2] + rad - x0) / CERT_RES_MM)))
        iy0 = max(0, int(math.floor((pb[1] - rad - y0) / CERT_RES_MM)))
        iy1 = min(ny - 1, int(math.ceil((pb[3] + rad - y0) / CERT_RES_MM)))
        thr = rad - CERT_EPS_MM
        bl = cell_blocked[L]
        for iy in range(iy0, iy1 + 1):
            cy = y0 + iy * CERT_RES_MM
            for ix in range(ix0, ix1 + 1):
                if (ix, iy) in bl:
                    continue
                cx = x0 + ix * CERT_RES_MM
                if G.pt_prim_dist(cx, cy, prim) < thr:
                    bl.add((ix, iy))
    for (prim, pb) in idx.holes:
        rad = CERT_HOLE_CLEARANCE + hw
        ix0 = max(0, int(math.floor((pb[0] - rad - x0) / CERT_RES_MM)))
        ix1 = min(nx - 1, int(math.ceil((pb[2] + rad - x0) / CERT_RES_MM)))
        iy0 = max(0, int(math.floor((pb[1] - rad - y0) / CERT_RES_MM)))
        iy1 = min(ny - 1, int(math.ceil((pb[3] + rad - y0) / CERT_RES_MM)))
        thr = rad - CERT_EPS_MM
        for L in layer_ids:
            bl = cell_blocked[L]
            for iy in range(iy0, iy1 + 1):
                cy = y0 + iy * CERT_RES_MM
                for ix in range(ix0, ix1 + 1):
                    if (ix, iy) in bl:
                        continue
                    cx = x0 + ix * CERT_RES_MM
                    if G.pt_prim_dist(cx, cy, prim) < thr:
                        bl.add((ix, iy))
    for (x1e, y1e, x2e, y2e) in idx.edge_segs:
        rad = CERT_EDGE_CLEARANCE + hw
        ix0 = max(0, int(math.floor((min(x1e, x2e) - rad - x0)
                                    / CERT_RES_MM)))
        ix1 = min(nx - 1, int(math.ceil((max(x1e, x2e) + rad - x0)
                                        / CERT_RES_MM)))
        iy0 = max(0, int(math.floor((min(y1e, y2e) - rad - y0)
                                    / CERT_RES_MM)))
        iy1 = min(ny - 1, int(math.ceil((max(y1e, y2e) + rad - y0)
                                        / CERT_RES_MM)))
        thr = rad - CERT_EPS_MM
        for L in layer_ids:
            bl = cell_blocked[L]
            for iy in range(iy0, iy1 + 1):
                cy = y0 + iy * CERT_RES_MM
                for ix in range(ix0, ix1 + 1):
                    if (ix, iy) in bl:
                        continue
                    cx = x0 + ix * CERT_RES_MM
                    if G.seg_pt_dist(cx, cy, x1e, y1e, x2e, y2e) < thr:
                        bl.add((ix, iy))

    # 过孔位硬阻塞（盘径/钻径两口径；孔与板边含其中）
    via_blocked = set()
    for iy in range(ny):
        cy = y0 + iy * CERT_RES_MM
        for ix in range(nx):
            cx = x0 + ix * CERT_RES_MM
            hit = None
            cu, ho, ed = idx.near(cx - 1.0, cy - 1.0, cx + 1.0, cy + 1.0)
            for (L, prim, req, _pb) in cu:
                if G.pt_prim_dist(cx, cy, prim) \
                        < req + via_size / 2 - CERT_EPS_MM:
                    hit = ("copper", L, req)
                    break
            if hit is None:
                for (prim, _pb) in ho:
                    if G.pt_prim_dist(cx, cy, prim) \
                            < CERT_HOLE_CLEARANCE + via_drill / 2 \
                            - CERT_EPS_MM:
                        hit = ("hole", None, CERT_HOLE_CLEARANCE)
                        break
            if hit is None:
                for (ex1, ey1, ex2, ey2) in ed:
                    if G.seg_pt_dist(cx, cy, ex1, ey1, ex2, ey2) \
                            < CERT_EDGE_CLEARANCE + via_size / 2 \
                            - CERT_EPS_MM:
                        hit = ("edge", None, CERT_EDGE_CLEARANCE)
                        break
            if hit is not None:
                via_blocked.add((ix, iy))

    model = {
        "net": net, "width": width, "via_size": via_size,
        "via_drill": via_drill, "x0": x0, "y0": y0, "nx": nx, "ny": ny,
        "res": CERT_RES_MM, "layer_ids": layer_ids,
        "cell_blocked": cell_blocked, "via_blocked": via_blocked,
        "index": idx, "ax": ax, "ay": ay, "bx": bx, "by": by,
        "margin_mm": margin_mm, "G": G, "mirror": m,
    }
    return model, None


def _model_cell(model, x, y):
    return (min(max(int(round((x - model["x0"]) / model["res"])), 0),
                model["nx"] - 1),
            min(max(int(round((y - model["y0"]) / model["res"])), 0),
                model["ny"] - 1))


def _model_center(model, ix, iy):
    return (model["x0"] + ix * model["res"], model["y0"] + iy * model["res"])


def _open_cell(model, L, ix, iy):
    return (ix, iy) not in model["cell_blocked"].get(L, set())


def _seg_closed(model, L, x1, y1, x2, y2):
    """模型边/辐条封闭判定：可证明非法（距 < 要求−EPS）→ (True, 论据)。"""
    G = model["G"]
    hw = model["width"] / 2.0
    cu, ho, ed = model["index"].near(min(x1, x2) - 1.0, min(y1, y2) - 1.0,
                                     max(x1, x2) + 1.0, max(y1, y2) + 1.0)
    for (LL, prim, req, pb) in cu:
        if LL != L:
            continue
        d = G.seg_prim_dist(x1, y1, x2, y2, prim)
        if d < req + hw - CERT_EPS_MM:
            return True, {"rule": "clearance", "req": req, "dist": round(d, 6),
                          "prim_bbox": [round(v, 6) for v in pb]}
    for (prim, pb) in ho:
        d = G.seg_prim_dist(x1, y1, x2, y2, prim)
        if d < CERT_HOLE_CLEARANCE + hw - CERT_EPS_MM:
            return True, {"rule": "hole_clearance",
                          "req": CERT_HOLE_CLEARANCE,
                          "dist": round(d, 6),
                          "prim_bbox": [round(v, 6) for v in pb]}
    for (ex1, ey1, ex2, ey2) in ed:
        d = G.seg_seg_dist(x1, y1, x2, y2, ex1, ey1, ex2, ey2)
        if d < CERT_EDGE_CLEARANCE + hw - CERT_EPS_MM:
            return True, {"rule": "copper_edge_clearance",
                          "req": CERT_EDGE_CLEARANCE, "dist": round(d, 6)}
    return False, None


def _cell_why(model, L, ix, iy):
    """格硬阻塞的论据（重算首个命中 prim）。"""
    G = model["G"]
    cx, cy = _model_center(model, ix, iy)
    hw = model["width"] / 2.0
    cu, ho, ed = model["index"].near(cx - 1.0, cy - 1.0, cx + 1.0, cy + 1.0)
    for (LL, prim, req, pb) in cu:
        if LL != L:
            continue
        d = G.pt_prim_dist(cx, cy, prim)
        if d < req + hw - CERT_EPS_MM:
            return {"rule": "clearance", "req": req, "dist": round(d, 6),
                    "prim_bbox": [round(v, 6) for v in pb]}
    for (prim, pb) in ho:
        d = G.pt_prim_dist(cx, cy, prim)
        if d < CERT_HOLE_CLEARANCE + hw - CERT_EPS_MM:
            return {"rule": "hole_clearance", "req": CERT_HOLE_CLEARANCE,
                    "dist": round(d, 6),
                    "prim_bbox": [round(v, 6) for v in pb]}
    for (ex1, ey1, ex2, ey2) in ed:
        d = G.seg_pt_dist(cx, cy, ex1, ey1, ex2, ey2)
        if d < CERT_EDGE_CLEARANCE + hw - CERT_EPS_MM:
            return {"rule": "copper_edge_clearance",
                    "req": CERT_EDGE_CLEARANCE, "dist": round(d, 6)}
    return {"rule": "unknown", "note": "重算未命中（不应发生）"}


def _via_why(model, ix, iy):
    G = model["G"]
    cx, cy = _model_center(model, ix, iy)
    cu, ho, ed = model["index"].near(cx - 1.0, cy - 1.0, cx + 1.0, cy + 1.0)
    vs, vd = model["via_size"], model["via_drill"]
    for (LL, prim, req, pb) in cu:
        d = G.pt_prim_dist(cx, cy, prim)
        if d < req + vs / 2 - CERT_EPS_MM:
            return {"rule": "clearance(via)", "req": req, "dist": round(d, 6),
                    "prim_bbox": [round(v, 6) for v in pb]}
    for (prim, pb) in ho:
        d = G.pt_prim_dist(cx, cy, prim)
        if d < CERT_HOLE_CLEARANCE + vd / 2 - CERT_EPS_MM:
            return {"rule": "hole_clearance(via_drill)",
                    "req": CERT_HOLE_CLEARANCE, "dist": round(d, 6),
                    "prim_bbox": [round(v, 6) for v in pb]}
    for (ex1, ey1, ex2, ey2) in ed:
        d = G.seg_pt_dist(cx, cy, ex1, ey1, ex2, ey2)
        if d < CERT_EDGE_CLEARANCE + vs / 2 - CERT_EPS_MM:
            return {"rule": "copper_edge_clearance(via)",
                    "req": CERT_EDGE_CLEARANCE, "dist": round(d, 6)}
    return {"rule": "unknown", "note": "重算未命中（不应发生）"}


def solve_cert(model):
    """证书求解：A/B 端点 8 邻辐条 → 源侧 BFS（4 邻格网 + 同格位过孔）。

    返回 dict：
      reachable_b=True  → 模型内存在候选通径（模型开放≠L1 合法，不足证）；
      reachable_b=False → UNSAT 证书（s_side 闭包 + 割元素逐条论据）。
    """
    layer_ids = model["layer_ids"]
    hw = model["width"] / 2.0
    a_cell = _model_cell(model, model["ax"], model["ay"])
    b_cell = _model_cell(model, model["bx"], model["by"])

    def spokes(px, py, acc):
        out = []
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ix, iy = acc[0] + di, acc[1] + dj
                if not (0 <= ix < model["nx"] and 0 <= iy < model["ny"]):
                    continue
                cx, cy = _model_center(model, ix, iy)
                for L in layer_ids:
                    if not _open_cell(model, L, ix, iy):
                        continue
                    closed, why = _seg_closed(model, L, px, py, cx, cy)
                    if not closed:
                        out.append({"node": (L, ix, iy),
                                    "justification": None})
                        break
        return out

    sa = spokes(model["ax"], model["ay"], a_cell)
    sb = spokes(model["bx"], model["by"], b_cell)
    sb_nodes = {(L, ix, iy) for s in sb
                for (L, ix, iy) in [s["node"]]}

    seen = set()
    came = {}
    dq = deque()
    for s in sa:
        n = s["node"]
        if n not in seen:
            seen.add(n)
            came[n] = ("spoke", "A", s["justification"])
            dq.append(n)
    hit_b = None
    while dq:
        n = dq.popleft()
        if n in sb_nodes:
            hit_b = n
            break
        (L, ix, iy) = n
        moves = []
        for (dix, diy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jx, jy = ix + dix, iy + diy
            if 0 <= jx < model["nx"] and 0 <= jy < model["ny"]:
                moves.append(("edge", L, ix, iy, jx, jy))
        if (ix, iy) not in model["via_blocked"]:
            for LL in layer_ids:
                if LL != L and _open_cell(model, LL, ix, iy) \
                        and all(_open_cell(model, l2, ix, iy)
                                for l2 in layer_ids):
                    moves.append(("via", LL, ix, iy))
        for mv in moves:
            if mv[0] == "edge":
                (_k, LL, x_ix, x_iy, jx, jy) = mv
                nb = (LL, jx, jy)
                if nb in seen or not _open_cell(model, LL, jx, jy):
                    continue
                cx, cy = _model_center(model, ix, iy)
                dx, dy = _model_center(model, jx, jy)
                closed, why = _seg_closed(model, LL, cx, cy, dx, dy)
                if closed:
                    continue
                seen.add(nb)
                came[nb] = (n, ("edge", (ix, iy), (jx, jy)), why)
                dq.append(nb)
            else:  # via
                (_k, LL, x_ix, x_iy) = mv
                nb = (LL, ix, iy)
                if nb in seen:
                    continue
                seen.add(nb)
                came[nb] = (n, ("via", (ix, iy)), None)
                dq.append(nb)
    if hit_b is not None:
        return {"reachable_b": True, "hit_node": list(hit_b),
                "spokes_b": len(sb_nodes),
                "note": "模型内存在候选通径（模型开放≠L1 合法；不足证→UNKNOWN）"}

    # UNSAT 证书：源侧闭包的出边全部列出（逐条论据）。
    # 模型迁移=同层 4 邻边 + 同格位过孔；跨层异格不是迁移，不列割。
    # 产物按 (kind, layer, why) 分组聚合（大闭包的边界可达数万条，分组省
    # 一个数量级体积；复核器逐 item 数值重算）。
    groups = {}
    order = []

    def add_cut(kind, layer, why, item):
        key = (kind, layer, json.dumps(why, sort_keys=True))
        if key not in groups:
            groups[key] = {"kind": kind, "why": why, "items": []}
            if layer is not None:
                groups[key]["layer"] = layer
            order.append(groups[key])
        groups[key]["items"].append(item)

    if not seen:
        # 闭包为空 ⟺ 全部 A 辐条封闭：割=封闭辐条清单
        for (ix, iy) in a_open_spoke_cells_closed(model, layer_ids):
            add_cut("spoke", None, _spoke_why(model, ix, iy), [ix, iy])
    else:
        for n in sorted(seen):
            (L, ix, iy) = n
            for (dix, diy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jx, jy = ix + dix, iy + diy
                if not (0 <= jx < model["nx"] and 0 <= jy < model["ny"]):
                    add_cut("boundary", None,
                            {"rule": "cert_scope_window"},
                            [L, ix, iy, dix, diy])
                    continue
                nb = (L, jx, jy)
                if nb in seen:
                    continue
                if not _open_cell(model, L, jx, jy):
                    add_cut("cell", L, _cell_why(model, L, jx, jy),
                            [jx, jy])
                else:
                    cx, cy = _model_center(model, ix, iy)
                    dx, dy = _model_center(model, jx, jy)
                    closed, why = _seg_closed(model, L, cx, cy, dx, dy)
                    if closed:
                        add_cut("edge", L, why, [ix, iy, jx, jy])
                    else:
                        # 开放邻格却未访问：闭包不封闭（BFS 与割不一致）
                        return {"reachable_b": False, "cert_broken": True,
                                "note": "闭包不封闭（开放邻格未访问）"}
            for LL in layer_ids:
                if LL == L or (LL, ix, iy) in seen:
                    continue
                if (ix, iy) in model["via_blocked"]:
                    add_cut("via", None, _via_why(model, ix, iy),
                            [ix, iy])
                elif not all(_open_cell(model, l2, ix, iy)
                             for l2 in layer_ids):
                    for l2 in layer_ids:
                        if not _open_cell(model, l2, ix, iy):
                            add_cut("cell", l2, _cell_why(model, l2, ix, iy),
                                    [ix, iy])
                else:
                    return {"reachable_b": False, "cert_broken": True,
                            "note": "闭包不封闭（开放过孔未访问）"}
    return {
        "reachable_b": False,
        "s_side_size": len(seen),
        "cut_groups": order,
        "cut_count": sum(len(g["items"]) for g in order),
        "spokes_a": [[list(s["node"]), s["justification"]] for s in sa],
        "spokes_b_open": sorted(list(x) for x in sb_nodes),
        "scope": {
            "model": "restricted_lattice_center_4neigh_vias",
            "res_mm": CERT_RES_MM, "margin_mm": model["margin_mm"],
            "region_mm": [round(model["x0"], 3), round(model["y0"], 3),
                          round(model["x0"] + (model["nx"] - 1) * model["res"],
                                3),
                          round(model["y0"] + (model["ny"] - 1) * model["res"],
                                3)],
            "hard_block_rule": "pt/seg_prim_dist < req + halfwidth - eps",
            "restriction_note":
                "证书证明：模型化路线空间（0.05mm 格心 4 邻格网 + 同格位过孔、"
                "端点 8 邻辐条、区域窗内、ripup=False 冻结铜）不存在合法路线；"
                "模型开放格未证合法，本证书为 restricted blocking "
                "certificate（SPEC §10.3），不等价于全域物理不可布",
        },
    }


def _spoke_why(model, ix, iy):
    """A 辐条 (ix,iy) 全层封闭的论据（每层：格堵或段堵）。"""
    layers = model["layer_ids"]
    reasons = []
    for L in layers:
        if not _open_cell(model, L, ix, iy):
            reasons.append({"layer": L, "closed": "cell",
                            "why": _cell_why(model, L, ix, iy)})
            continue
        cx, cy = _model_center(model, ix, iy)
        closed, why = _seg_closed(model, L, model["ax"], model["ay"],
                                  cx, cy)
        reasons.append({"layer": L, "closed": "edge" if closed else "OPEN",
                        "why": why})
    return {"per_layer": reasons}


def a_open_spoke_cells_closed(model, layer_ids):
    """全部层均封闭的 A 辐条格（闭包为空时的割内容）。"""
    out = []
    a_cell = _model_cell(model, model["ax"], model["ay"])
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ix, iy = a_cell[0] + di, a_cell[1] + dj
            if not (0 <= ix < model["nx"] and 0 <= iy < model["ny"]):
                continue
            open_any = False
            for L in layer_ids:
                if not _open_cell(model, L, ix, iy):
                    continue
                cx, cy = _model_center(model, ix, iy)
                closed, _w = _seg_closed(model, L, model["ax"],
                                         model["ay"], cx, cy)
                if not closed:
                    open_any = True
                    break
            if not open_any:
                out.append((ix, iy))
    return sorted(out)


def verify_cert(model, cert):
    """独立复核：割组论据逐 item 数值重算 + 仅信任割条目的封闭性 BFS。

    与 solve_cert 不共享 BFS 状态；开放性判定取保守方向（未列割=开放），
    故 BFS 逸出闭包即证书无效。"""
    if cert.get("reachable_b") is not False or cert.get("cert_broken"):
        return False
    layer_ids = model["layer_ids"]
    b_cell = _model_cell(model, model["bx"], model["by"])

    def center(ix, iy):
        return (model["x0"] + ix * model["res"],
                model["y0"] + iy * model["res"])

    # 1) 割组论据逐 item 数值重算（分组格式：kind/layer/why + items）
    cut_edges = set()
    cut_cells = set()
    cut_vias = set()
    cut_spokes = set()
    boundary = set()
    for g in cert.get("cut_groups", []):
        kind = g["kind"]
        layer = g.get("layer")
        why = g.get("why") or {}
        for item in g["items"]:
            if kind == "edge":
                (ix, iy, jx, jy) = item
                x1, y1 = center(ix, iy)
                x2, y2 = center(jx, jy)
                closed, _w = _seg_closed(model, layer, x1, y1, x2, y2)
                if not closed:
                    return False
                cut_edges.add((layer, (ix, iy), (jx, jy)))
            elif kind == "cell":
                (ix, iy) = item
                w = _cell_why(model, layer, ix, iy)
                if w.get("rule") == "unknown":
                    return False
                cut_cells.add((layer, (ix, iy)))
            elif kind == "via":
                (ix, iy) = item
                w = _via_why(model, ix, iy)
                if w.get("rule") == "unknown":
                    return False
                cut_vias.add((ix, iy))
            elif kind == "boundary":
                (L, ix, iy, dix, diy) = item
                boundary.add(((L, ix, iy), (dix, diy)))
            elif kind == "spoke":
                (ix, iy) = item
                # 辐条必须全层封闭：任一层格开放且段开放 → 证书失效
                for L in layer_ids:
                    if not _open_cell(model, L, ix, iy):
                        continue
                    cx, cy = center(ix, iy)
                    closed, _w = _seg_closed(model, L, model["ax"],
                                             model["ay"], cx, cy)
                    if not closed:
                        return False
                cut_spokes.add((ix, iy))
            else:
                return False

    # 2) 辐条重算（证书声明的开放辐条必须真的开放）
    seen = set()
    dq = deque()
    for item in cert["spokes_a"]:
        node = tuple(item[0])
        (L, ix, iy) = node
        if not _open_cell(model, L, ix, iy):
            return False
        closed, _w = _seg_closed(model, L, model["ax"], model["ay"],
                                 *center(ix, iy))
        if closed:
            return False
        if node not in seen:
            seen.add(node)
            dq.append(node)
    sb_open = {tuple(x) for x in cert.get("spokes_b_open", [])}
    # 3) 仅信任割条目的封闭性 BFS（未列割=开放，保守方向）
    while dq:
        n = dq.popleft()
        (L, ix, iy) = n
        if n in sb_open or (ix, iy) == b_cell:
            return False
        for (dix, diy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jx, jy = ix + dix, iy + diy
            if not (0 <= jx < model["nx"] and 0 <= jy < model["ny"]):
                if ((L, ix, iy), (dix, diy)) not in boundary:
                    return False  # 未列的出窗迁移
                continue
            nb = (L, jx, jy)
            if nb in seen:
                continue
            if (L, (ix, iy), (jx, jy)) in cut_edges:
                continue
            if (L, (jx, jy)) in cut_cells:
                continue
            seen.add(nb)
            dq.append(nb)
        if (ix, iy) not in cut_vias:
            for LL in layer_ids:
                nb = (LL, ix, iy)
                if nb in seen or (LL, (ix, iy)) in cut_cells:
                    continue
                seen.add(nb)
                dq.append(nb)
    return True
