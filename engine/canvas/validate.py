# -*- coding: utf-8 -*-
"""canvas.validate -- v5.drc 绑定验证器（合同 §1 Lane-K1）。

两入口:
- validate_edit(st, action, batch_ctx=None) -> (accepted, code|None, detail):
  逐编辑局部检查。受影响铜对走 v5.drc 同源函数族（check_clearance /
  check_edge_clearance / hole_via_blocked / hole_track_blocked / normalize_holes
  ——**禁止平行实现几何判定**，本件只做归责（差集法: base 场景违例键集 vs
  含候选 full 场景键集，新增违例归责候选——板固有 pad 贴边/板固孔对在 base
  已在、不归责候选，与 v5.route_check「板内固有缺陷不归责 routes」纪律同构）。
- validate_full(st) -> v5.drc.DRCReport: 全态检查（铜全集调 v5.drc.check_all
  同源 + edge/hole 独立判定器聚合——edge/hole 不入 check_all 是 v5.drc 侧
  设计（其 docstring），聚合归本入口）。

布间/放置合法性**不在本件铜面路径内**（canvas.placecheck; 其 verdict 显式
标注"新 validator，非 v5.drc 移植"）。**接线已收口（编排体 2026-09-25,
lane-m4 §5 接线契约 + lane-m5 §6 遗留）**:
  1. validate_edit 的 move/rotate/flip 分支 → canvas.placecheck.check_placement
     （相对→绝对折算单源=protocol.absolute_candidate; 分区存在性=
     E_UNKNOWN_PARTITION; 板框=V_PLACEMENT_EDGE; 布间=V_PLACEMENT_COLLISION）;
  2. apply 侧（protocol.apply_batch）落 merge_candidate 完整覆盖;
  3. validate_full 不并入放置合法性（两层 verdict 口径不同源，防混淆——
     全场放置检查独立调 placecheck.check_all_placements，调用方消费）;
  4. tuning 分支 R6 前置拒收（V_KEEPOUT）——复用 canvas.tuning.r6_violations
     同源三件套（zone_rects+drc.check_keepout+instantiate.tuning_copper），
     全态兜底仍=validate_full check_all→R6。
循环 import（validate↔instantiate、validate↔tuning）用函数内局部导入解。
"""
import math

from v5 import drc
from v5.metrics import clearance as _cl
from v5.kicad_export import via_model_params

# ---- 原因码（词表单源=canvas.protocol；此处仅引用，几何判定归本件）----
from . import protocol as _p

#: tuning.kind 枚举（合同 §2: {"accordion","detour"}；键集冻结于激活跑 prereg）
TUNING_KINDS = ("accordion", "detour")
#: tuning.params 键集（原型键集；合同钉死"随 kind 冻结于 prereg"，此处为
#: 缺省接受集，prereg 冻结后不改义只收紧）
TUNING_PARAM_KEYS = {
    "accordion": {"amp_mm", "count"},
    "detour": {"offset_mm"},
}


def width_class_vocab(board):
    """板 netclass 宽度词表 {class_name: width_mm}（V_UNKNOWN_WIDTH_CLASS
    判定与 instantiate 网宽换算的单源）。

    **词表来源**（缺省推导，函数级披露）:
    - 显式表优先: board["netclasses"]（{"<class>": width_mm}）——board.v1
      schema 现无此键，为预留位；落显式键即改由板值单源。
    - 缺省表=板 hard_rules/partitions 推导:
      * R1.floor_mm（载流下限）为下界锚；
      * w_min = min(partitions.width_prior.w_min)（无 prior 回退 floor）；
      * w_max = max(partitions.width_prior.w_max)（回退 floor）；
      * 若 w_min > w_max（跨分区 prior 交叉）交换保序；
      * 三档: "min"=w_min, "nom"=round((w_min+w_max)/2, 6), "max"=w_max。
    词表冻结于激活跑 prereg（合同 §2 注：缺省表=板 hard_rules 推导，冻结
    留给 prereg——本函数是推导实现，不改判定义）。"""
    explicit = board.get("netclasses")
    if isinstance(explicit, dict) and explicit:
        out = {}
        for name in sorted(explicit):
            w = float(explicit[name])
            if not (w > 0.0):
                raise ValueError("netclasses[%r] 宽度非正" % (name,))
            out[name] = round(w, 9)
        return out
    hard = board.get("hard_rules", {})
    floor = float(hard.get("R1", {}).get("floor_mm", 0.2))
    priors = [(p.get("width_prior") or {}) for p in board.get("partitions", [])
              if isinstance(p.get("width_prior"), dict)]
    w_mins = [float(w["w_min"]) for w in priors
              if isinstance(w.get("w_min"), (int, float))
              and not isinstance(w.get("w_min"), bool)]
    w_maxs = [float(w["w_max"]) for w in priors
              if isinstance(w.get("w_max"), (int, float))
              and not isinstance(w.get("w_max"), bool)]
    w_min = min(w_mins) if w_mins else floor
    w_max = max(w_maxs) if w_maxs else floor
    if w_min > w_max:
        w_min, w_max = w_max, w_min
    w_min = max(w_min, 0.05)
    return {"min": round(w_min, 9),
            "nom": round((w_min + w_max) / 2.0, 6),
            "max": round(w_max, 9)}


def default_width_class(st):
    """未设网档时的缺省档（"min"——构造上 ≥ R1.floor 的档，缺省保守）。"""
    return "min"


def _scene(st, extra_coppers=()):
    """全铜场景（pad 场+段+via+tuning，确定性序；局部导入解 circular）。"""
    from . import instantiate as inst
    coppers = inst.pad_coppers(st)
    for sid in sorted(st.segs):
        coppers.append(inst.seg_copper(st, st.segs[sid]))
    coppers.extend(inst.via_coppers(st))
    for sid in sorted(st.tunings):
        cu = inst.tuning_copper(st, st.tunings[sid])
        if cu is not None:
            coppers.append(cu)
    coppers.extend(extra_coppers)
    return coppers


def _vkey(v):
    return (v.rule, str(v.subject_a), str(v.subject_b),
            drc_json(v.data))


def drc_json(data):
    import json
    return json.dumps(data, sort_keys=True)


def ws_tuple(board):
    ws = board["workspace"]
    return (float(ws["x_min"]), float(ws["y_min"]),
            float(ws["x_max"]), float(ws["y_max"]))


def _viol_keys(coppers, board):
    """场景 → (R5+edge 违例键集合, R5 违例列表, edge 违例列表)。

    同源调用: v5.drc.check_clearance（same_net_exempt=True）+
    v5.drc.check_edge_clearance（workspace 语义=D6-3 板边禁布带）。"""
    r5v, _checked = drc.check_clearance(
        coppers, board["hard_rules"]["R5"]["min_clearance_mm"],
        same_net_exempt=True)
    edgev = drc.check_edge_clearance(coppers, ws_tuple(board))
    keys = set(_vkey(v) for v in r5v) | set(_vkey(v) for v in edgev)
    return keys, r5v, edgev


# ----------------------------------------------- V_CLEARANCE 定位辅助（D-5）
# 中心线/圆心口径最近点对（advisory）: 折线×折线=逐段对最近点、折线×pad=
# 段上最近点+圆缘点、pad×pad=心连线、band=矩形钳位。只进 detail 文本，
# 不参与 gap 数值与裁决（裁决单源=v5.drc.check_clearance）。

def _r4(v):
    """mm 坐标 round 4 位（-0.0 归一 +0.0，确定性显示）。"""
    return round(float(v), 4) + 0.0


def _closest_pt_seg(p, a, b):
    """点 p 在线段 ab 上的最近点（钳位投影; 退化段=端点 a）。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    if l2 <= 0.0:
        return (a[0], a[1])
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2
    t = max(0.0, min(1.0, t))
    return (a[0] + t * dx, a[1] + t * dy)


def _seg_seg_closest(p1, p2, p3, p4):
    """两线段最近点对 → (q_on_p1p2, q_on_p3p4, dist)。真相交=交点对;
    其余取四端点对邻段钳位投影候选的最小者（先到者胜，确定性）。"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    d1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    d2 = (x4 - x3) * (y2 - y3) - (y4 - y3) * (x2 - x3)
    d3 = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    d4 = (x2 - x1) * (y4 - y1) - (y2 - y1) * (x4 - x1)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
        if den != 0.0:
            t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / den
            t = max(0.0, min(1.0, t))
            q = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
            return q, q, 0.0
    cands = ((p1, _closest_pt_seg(p1, p3, p4)),
             (p2, _closest_pt_seg(p2, p3, p4)),
             (_closest_pt_seg(p3, p1, p2), p3),
             (_closest_pt_seg(p4, p1, p2), p4))
    best = None
    for qa, qb in cands:
        d = math.hypot(qa[0] - qb[0], qa[1] - qb[1])
        if best is None or d < best[2]:
            best = (qa, qb, d)
    return best


def _clamp_rect(p, band):
    """点钳位到轴对齐矩形边界/内部。"""
    return (min(max(p[0], band[0]), band[2]),
            min(max(p[1], band[1]), band[3]))


def _rect_clamp_dist(p, band):
    dx = max(band[0] - p[0], 0.0, p[0] - band[2])
    dy = max(band[1] - p[1], 0.0, p[1] - band[3])
    return math.hypot(dx, dy)


def _poly_rect_closest(pts, band):
    """折线×矩形带最近点对（逐段凸函数三分搜索——钳位距离沿段凸，
    80 轮缩至双精度分辨率内; advisory 定位，4 位小数口径下精确）。"""
    best = None
    for a, b in zip(pts[:-1], pts[1:]):
        lo, hi = 0.0, 1.0
        for _ in range(80):
            m1 = lo + (hi - lo) / 3.0
            m2 = hi - (hi - lo) / 3.0
            p1 = (a[0] + m1 * (b[0] - a[0]), a[1] + m1 * (b[1] - a[1]))
            p2 = (a[0] + m2 * (b[0] - a[0]), a[1] + m2 * (b[1] - a[1]))
            if _rect_clamp_dist(p1, band) <= _rect_clamp_dist(p2, band):
                hi = m2
            else:
                lo = m1
        t = (lo + hi) / 2.0
        q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        d = _rect_clamp_dist(q, band)
        if best is None or d < best[2]:
            best = (q, _clamp_rect(q, band), d)
    return best


def _nearest_pair(ca, cb):
    """两铜最近点对 → ((x,y) on ca, (x,y) on cb)。几何对覆盖 v5.drc
    _actual_gap 全分支（裁决原语同域）; 坐标为 advisory 定位，不参与裁决。"""
    def _seg_pad_closest(pts, pad):
        (c, r) = pad
        best = None
        for a, b in zip(pts[:-1], pts[1:]):
            q = _closest_pt_seg(c, a, b)
            vx, vy = q[0] - c[0], q[1] - c[1]
            vlen = math.hypot(vx, vy)
            if vlen <= r:
                # 圆与折线重叠（gap=0）: 最近点对= 折线与圆缘的交点
                # （沿段解 |a+t(b-a)-c|²=r² 取最小根; 数值无根回退心/缘点）
                roots = []
                dx, dy = b[0] - a[0], b[1] - a[1]
                qa = (a[0] - c[0], a[1] - c[1])
                A = dx * dx + dy * dy
                B = 2.0 * (qa[0] * dx + qa[1] * dy)
                C = qa[0] * qa[0] + qa[1] * qa[1] - r * r
                if A > 0.0:
                    disc = B * B - 4.0 * A * C
                    if disc >= 0.0:
                        sq = math.sqrt(disc)
                        for t in ((-B - sq) / (2.0 * A), (-B + sq) / (2.0 * A)):
                            if 0.0 <= t <= 1.0:
                                roots.append((a[0] + t * dx, a[1] + t * dy))
                if roots:
                    x = min(roots)
                    cand = (x, x, 0.0)
                else:
                    cand = (q, (c[0] + r, c[1]) if vlen <= 0.0 else
                            (c[0] + r * vx / vlen, c[1] + r * vy / vlen),
                            0.0)
            else:
                bnd = (c[0] + r * vx / vlen, c[1] + r * vy / vlen)
                cand = (q, bnd, vlen - r)
            if best is None or cand[2] < best[2]:
                best = cand
        return best

    if ca.band and cb.band:
        return (_clamp_rect(((cb.band[0] + cb.band[2]) / 2.0,
                             (cb.band[1] + cb.band[3]) / 2.0), ca.band),
                _clamp_rect(((ca.band[0] + ca.band[2]) / 2.0,
                             (ca.band[1] + ca.band[3]) / 2.0), cb.band))
    if ca.pad and cb.pad:
        (c1, r1), (c2, r2) = ca.pad, cb.pad
        vx, vy = c2[0] - c1[0], c2[1] - c1[1]
        vlen = math.hypot(vx, vy)
        if vlen <= 0.0:
            return (c1, c2)
        return ((c1[0] + r1 * vx / vlen, c1[1] + r1 * vy / vlen),
                (c2[0] - r2 * vx / vlen, c2[1] - r2 * vy / vlen))
    if ca.pad and cb.polyline:
        q, bnd, _d = _seg_pad_closest(cb.polyline, ca.pad)
        return (bnd, q)
    if ca.polyline and cb.pad:
        q, bnd, _d = _seg_pad_closest(ca.polyline, cb.pad)
        return (q, bnd)
    if ca.polyline and cb.band:
        q, rq, _d = _poly_rect_closest(ca.polyline, cb.band)
        return (q, rq)
    if ca.band and cb.polyline:
        q, rq, _d = _poly_rect_closest(cb.polyline, ca.band)
        return (rq, q)
    if ca.pad and cb.band:
        (c, r) = ca.pad
        rq = _clamp_rect(c, cb.band)
        vx, vy = rq[0] - c[0], rq[1] - c[1]
        vlen = math.hypot(vx, vy)
        bnd = c if vlen <= 0.0 else \
            (c[0] + r * vx / vlen, c[1] + r * vy / vlen)
        return (bnd, rq)
    if ca.band and cb.pad:
        pb, pr = _nearest_pair(cb, ca)
        return (pr, pb)
    if ca.polyline and cb.polyline:
        best = None
        for a1, a2 in zip(ca.polyline[:-1], ca.polyline[1:]):
            for b1, b2 in zip(cb.polyline[:-1], cb.polyline[1:]):
                qa, qb, d = _seg_seg_closest(a1, a2, b1, b2)
                if best is None or d < best[2]:
                    best = (qa, qb, d)
        return (best[0], best[1])
    raise ValueError("不支持的铜几何对: %s/%s" % (ca.cid, cb.cid))


def _cand_locate_suffix(v, cand_ids, by_cid):
    """R5 违例 → `` @cand=(x,y) vs (x2,y2)`` 定位后缀（advisory; 候选铜上
    一点 vs 对位铜上一点，mm round 4 位）。无法定位（subjects 非候选对/
    几何对不支持）= 空串，detail 保持旧形态。"""
    layer = (v.data or {}).get("layer")

    def _pick(cid):
        pool = by_cid.get(cid) or []
        same = [c for c in pool if c.layer == layer]
        return (same or pool or [None])[0]

    ca, cb = _pick(v.subject_a), _pick(v.subject_b)
    if ca is None or cb is None:
        return ""
    if v.subject_b in cand_ids and v.subject_a not in cand_ids:
        cand, other = cb, ca
    else:
        cand, other = ca, cb
    try:
        (x1, y1), (x2, y2) = _nearest_pair(cand, other)
    except ValueError:
        return ""
    return " @cand=(%s,%s) vs (%s,%s)" % (_r4(x1), _r4(y1),
                                          _r4(x2), _r4(y2))


def _new_violations(st, extra_coppers):
    """差集归责: full 场景相对 base 场景的新增违例（空列表=候选合法）。

    0.6.0（V8-PILOT-060 D-5）: R5 新增违例 detail 追加最近点对坐标
    `` @cand=(x,y) vs (x2,y2)``（候选铜上一点 vs 对位铜上一点，mm、round
    4 位，中心线/圆心口径——见 _nearest_pair docstring）。**advisory 定位
    辅助**: 坐标出自本件独立最近点几何，不参与 gap 数值与裁决; 裁决仍以
    detail 前段 gap 值（v5.drc.check_clearance 单源）为准。"""
    board = st.board
    base_scene = _scene(st)
    full_scene = _scene(st, extra_coppers)
    base_keys, _b5, _be = _viol_keys(base_scene, board)
    full_keys, f5, fe = _viol_keys(full_scene, board)
    new_keys = full_keys - base_keys
    if not new_keys:
        return []
    cand_ids = {c.cid for c in extra_coppers}
    by_cid = {}
    for c in full_scene:
        by_cid.setdefault(c.cid, []).append(c)
    for v in list(f5) + list(fe):
        if _vkey(v) in new_keys:
            if v.rule == "R5":
                return [{"code": _p.V_CLEARANCE,
                         "detail": "%s|%s gap=%s%s" % (
                             v.subject_a, v.subject_b, v.data.get("gap_mm"),
                             _cand_locate_suffix(v, cand_ids, by_cid))}]
            return [{"code": _p.V_EDGE,
                     "detail": "%s pos=%s" % (v.subject_a, v.data.get("pos"))}]
    return [{"code": _p.V_CLEARANCE, "detail": "unattributed new violation"}]


def _net_endpoint_mm(st, net_id):
    """网全部分区的覆盖后真实端点 mm（孔端点豁免集，route_check 同式）。"""
    out = []
    for pid in st.net_partitions(net_id):
        out.extend(st.effective_endpoint_mm(pid))
    return out


def r6_prefilter_detail(st, coppers):
    """R6 前置拒收 detail（lane-m2x §6.2 缝披露收口: route/via 落铜动作
    与 tuning 同式前置; keepout 非空才有意义）。同源三件套=zone_rects（本件）
    +drc.check_keepout+tuning.plane_layers——零平行实现。None=不触区。"""
    _sensitive, keepout = zone_rects(st.board)
    if not keepout:
        return None
    from . import tuning as _tn
    for v in drc.check_keepout(coppers, keepout,
                               _tn.plane_layers(st.board)):
        zid = None
        data = getattr(v, "data", None)
        if isinstance(data, dict):
            zid = data.get("zone_id")
        return "zone:%s" % (zid or getattr(v, "subject_b", None) or "R6")
    return None


def _hole_exempt(st, net_id):
    """端点豁免孔索引（孔心与网分区任一覆盖后端点重合 EPS 内——
    v5.route_check._hole_violations 与 executor.edge_blocked 同式同豁免）。"""
    eps = _net_endpoint_mm(st, net_id)
    holes = drc.normalize_holes(st.board.get("holes"))
    exempt = set()
    for hi, (hx, hy, _hr) in enumerate(holes):
        for ex, ey in eps:
            if abs(hx - ex) <= _cl.EPS and abs(hy - ey) <= _cl.EPS:
                exempt.add(hi)
                break
    return exempt


def _check_track_holes(st, net_id, pts, half_width):
    """候选折线 vs 板固孔（track face; hole_track_blocked 同源; 端点豁免）。"""
    holes = drc.normalize_holes(st.board.get("holes"))
    exempt = _hole_exempt(st, net_id)
    for hi, (hx, hy, hr) in enumerate(holes):
        if hi in exempt:
            continue
        for a, b in zip(pts[:-1], pts[1:]):
            if drc.hole_track_blocked((hx, hy), hr, a, b, half_width):
                return [{"code": _p.V_HOLE_TRACK,
                         "detail": "hole:%d seg %s-%s" % (hi, a, b)}]
    return []


def _check_via_holes(st, mm, grid):
    """候选 via vs 板固孔（零豁免; hole_via_blocked 同源）。"""
    holes = drc.normalize_holes(st.board.get("holes"))
    vm = via_model_params(st.board)
    for hi, (hx, hy, hr) in enumerate(holes):
        if drc.hole_via_blocked((hx, hy), hr, mm, vm["radius"]):
            return [{"code": _p.V_HOLE_VIA,
                     "detail": "hole:%d at %s" % (hi, list(grid))}]
    return []


def _effective_width_class(st, net_id):
    return st.widths.get(net_id, default_width_class(st))


# ---------------------------------------------------------------- 逐编辑

def validate_edit(st, action, batch_ctx=None):
    """逐编辑局部检查。batch_ctx（可选）= 批内累积视图
    {"via_grids": {net_id: {grid}}, "route_pts": {net_id: {grid}}}——
    跨层链「鸡生蛋」解法（v1 同语义）: 段附着集 ∪ 批内 via 动作格点、
    via on-path 集 ∪ 批内 route waypoints。缺省 None=单动作视图。"""
    act = action.get("action")
    if act == "route":
        return _v_route(st, action, batch_ctx)
    if act == "via":
        return _v_via(st, action, batch_ctx)
    if act == "ripup":
        return _v_ripup(st, action)
    if act == "width_class":
        return _v_width_class(st, action)
    if act == "move":
        return _v_move(st, action)
    if act == "rotate":
        return _v_rotate(st, action)
    if act == "flip":
        return _v_flip(st, action)
    if act == "tuning":
        return _v_tuning(st, action)
    if act == "submit":
        return (True, None, None)
    return (False, _p.E_UNKNOWN_ACTION, repr(act))


def _v_route(st, a, batch_ctx):
    from . import instantiate as inst
    net_id = a["net_id"]
    if net_id not in st.known_nets():
        return (False, _p.E_UNKNOWN_NET, net_id)
    layer = a["layer"]
    if layer not in st.signal_layers():
        return (False, _p.E_UNKNOWN_LAYER, str(layer))
    pids = st.net_partitions(net_id)
    pid = pids[0]      # 多分区网路由粒度随 M2 落；缺省取网首分区（确定性）
    expanded = inst.expand_waypoints(a["waypoints"])
    for g in expanded:
        if not st.lattice.in_bounds(*g):
            return (False, _p.E_GRID_OUT_OF_BOUNDS, list(g))
    anchors = set()
    for p in pids:
        for x in st.effective_anchors(p):
            anchors.add(tuple(x))
    if len(expanded) < 2:
        # 同锚重合退化网（网内全部分区端点锚同格）零长 route 合法化
        # （D-CT-022 协议原语补位，2026-09-25 用户裁定）: 单点恰为该网唯一
        # 锚 → 接受（几何面=点零延展，孔/间距/R6 检查天然无对象；端点豁免
        # 语义一致）。其余零长照拒。
        if len(expanded) == 1 and anchors == {tuple(expanded[0])}:
            return (True, None, None)
        return (False, _p.V_SELF_SNAG, "展开后零长")
    vias = set(st.via_grids(net_id))
    if batch_ctx:
        vias |= batch_ctx.get("via_grids", {}).get(net_id, set())
    h, t = tuple(expanded[0]), tuple(expanded[-1])
    for pt, side in ((h, "head"), (t, "tail")):
        if pt not in anchors and pt not in vias:
            return (False, _p.V_ENDPT_NOT_ATTACHED,
                    "%s %s 须为端点锚或本网 via 格点" % (side, list(pt)))
    cls = _effective_width_class(st, net_id)
    w = net_width(st, net_id, cls)
    fake = {"shape_id": "cand:seg", "net_id": net_id, "partition_id": pid,
            "layer": layer, "grid": [list(p) for p in expanded],
            "width_class": cls}
    pts, _stub = inst.segment_mm(st, fake)
    for v in _check_track_holes(st, net_id, pts, w / 2.0):
        return (False, v["code"], v["detail"])
    cand = inst.seg_copper(st, fake)
    r6 = r6_prefilter_detail(st, [cand])
    if r6:
        return (False, _p.V_KEEPOUT, r6)
    for v in _new_violations(st, [cand]):
        return (False, v["code"], v["detail"])
    return (True, None, None)


def _v_via(st, a, batch_ctx):
    from . import instantiate as inst
    net_id = a["net_id"]
    if net_id not in st.known_nets():
        return (False, _p.E_UNKNOWN_NET, net_id)
    grid = tuple(a["grid"])
    if not st.lattice.in_bounds(*grid):
        return (False, _p.E_GRID_OUT_OF_BOUNDS, list(grid))
    if grid in st.via_grids(net_id):
        return (False, _p.V_DUPLICATE_VIA, list(grid))
    on_path = any(tuple(p) == grid for sid in sorted(st.segs)
                  if st.segs[sid]["net_id"] == net_id
                  for p in st.segs[sid]["grid"])
    on_path = on_path or any(tuple(p) == grid for sid in sorted(st.tunings)
                             if st.tunings[sid]["net_id"] == net_id
                             for p in st.tunings[sid]["grid"])
    if not on_path and batch_ctx:
        on_path = grid in batch_ctx.get("route_pts", {}).get(net_id, set())
    if not on_path:
        return (False, _p.V_VIA_OFF_PATH, list(grid))
    mm = st.lattice.to_mm(*grid)
    for v in _check_via_holes(st, mm, list(grid)):
        return (False, v["code"], v["detail"])
    fake = {"shape_id": "cand:via", "net_id": net_id, "grid": list(grid)}
    vc = inst.via_coppers(st, [fake])
    r6 = r6_prefilter_detail(st, vc)
    if r6:
        return (False, _p.V_KEEPOUT, r6)
    for v in _new_violations(st, vc):
        return (False, v["code"], v["detail"])
    return (True, None, None)


def _v_ripup(st, a):
    if "net_id" in a:
        net_id = a["net_id"]
        if net_id not in st.known_nets():
            return (False, _p.E_UNKNOWN_NET, net_id)
        had = (any(s["net_id"] == net_id for s in st.segs.values())
               or any(v["net_id"] == net_id for v in st.vias.values())
               or any(t["net_id"] == net_id for t in st.tunings.values()))
        if not had:
            return (False, _p.V_RIPUP_UNKNOWN, net_id)
        return (True, None, None)
    sid = a["shape_id"]
    if sid not in st.segs and sid not in st.vias and sid not in st.tunings:
        return (False, _p.V_RIPUP_UNKNOWN, sid)
    return (True, None, None)


def _v_width_class(st, a):
    net_id = a["net_id"]
    if net_id not in st.known_nets():
        return (False, _p.E_UNKNOWN_NET, net_id)
    cls = a["class"]
    vocab = width_class_vocab(st.board)
    if cls not in vocab:
        return (False, _p.V_UNKNOWN_WIDTH_CLASS,
                "%s 不在板词表 %s" % (cls, sorted(vocab)))
    return (True, None, None)


def _v_move(st, a):
    # placecheck 接线（lane-m4 §5）; 格点越界真实判在前（target 是格点）
    target = a["target"]
    if not st.lattice.in_bounds(*target):
        return (False, _p.E_GRID_OUT_OF_BOUNDS, list(target))
    return _check_placement_action(st, a)


def _v_rotate(st, a):
    turns = a["turns"]
    if not isinstance(turns, int) or isinstance(turns, bool):
        return (False, _p.E_NON_INTEGER_GRID, "turns=%r 非整数" % (turns,))
    if turns not in (1, 2, 3):
        return (False, _p.E_GRID_OUT_OF_BOUNDS, "turns=%r 越界 {1,2,3}" % (turns,))
    return _check_placement_action(st, a)


def _v_flip(st, a):
    return _check_placement_action(st, a)


def _check_placement_action(st, a):
    """move/rotate/flip 共用放置判定（placecheck 接线核心）。

    序（lane-m4 §5 检查序对齐）: 分区存在(E_UNKNOWN_PARTITION) →
    相对→绝对折算（protocol.absolute_candidate 单源） →
    check_placement(board, lattice, placements, pid, candidate)
    → (ok, code, detail) 直通。min_gap/same_net_exempt 用 placecheck
    缺省（R5 阈值单源+同网豁免）。"""
    from . import placecheck as _pc
    pid = a["partition_id"]
    if pid not in st.known_partitions():
        return (False, _p.E_UNKNOWN_PARTITION, pid)
    cand = _p.absolute_candidate(st, a)
    ok, code, detail = _pc.check_placement(
        st.board, st.lattice, st.placements, pid, cand)
    if ok:
        return (True, None, None)
    return (False, code, detail)


def _v_tuning(st, a):
    from . import instantiate as inst
    net_id = a["net_id"]
    if net_id not in st.known_nets():
        return (False, _p.E_UNKNOWN_NET, net_id)
    kind = a["kind"]
    if kind not in TUNING_KINDS:
        return (False, _p.V_TUNING_KIND,
                "%r 不在 %s" % (kind, list(TUNING_KINDS)))
    params = a["params"]
    if not isinstance(params, dict):
        return (False, _p.V_TUNING_PARAMS, "params 须为平铺数值对象")
    bad = _tuning_params_bad(kind, params)
    if bad:
        return (False, _p.V_TUNING_PARAMS, bad)
    grid = _p.tuning_base_grid(st, net_id)   # 基线=网首段（合同 §2 无 grid 键）
    if not grid:
        return (False, _p.V_TUNING_PARAMS, "网无基线段（tuning 悬空）")
    # R6 前置拒收（lane-m5 §6 遗留接线; 同源三件套单源=canvas.tuning）
    from . import tuning as _tn
    for v in _tn.r6_violations(st, net_id, kind, params,
                               group_id=a["group_id"]):
        return (False, _p.V_KEEPOUT,
                "zone:%s" % (v.get("data", {}).get("zone_id")
                             or v.get("subject_b") or "R6"))
    fake_tun = {"shape_id": "cand:tun", "net_id": net_id,
                "group_id": a["group_id"], "kind": kind,
                "grid": grid, "params": dict(params)}
    cls = _effective_width_class(st, net_id)
    w = net_width(st, net_id, cls)
    pts = inst.tuning_polyline_mm(st, fake_tun)
    for v in _check_track_holes(st, net_id, pts, w / 2.0):
        return (False, v["code"], v["detail"])
    cand = inst.tuning_copper(st, fake_tun)
    for v in _new_violations(st, [cand]):
        return (False, v["code"], v["detail"])
    return (True, None, None)


def _tuning_params_bad(kind, params):
    """参数键集/数值域检查（V_TUNING_PARAMS 判定；键集=缺省接受集，
    冻结于激活跑 prereg）。"""
    allowed = TUNING_PARAM_KEYS[kind]
    if set(params) != allowed:
        return "键集须= %s（实得 %s）" % (sorted(allowed), sorted(params))
    for k in sorted(params):
        v = params[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return "%s=%r 非数值" % (k, v)
    if kind == "accordion":
        if not (float(params["amp_mm"]) > 0.0):
            return "amp_mm=%r 须为正" % (params["amp_mm"],)
        if isinstance(params["count"], float) or not (int(params["count"]) >= 1):
            return "count=%r 须为 ≥1 整数" % (params["count"],)
    else:
        if float(params["offset_mm"]) == 0.0:
            return "offset_mm=0（detour 须非零侧移）"
    return None


def net_width(st, net_id, cls):
    from . import instantiate as inst
    return inst.net_width_mm(st, net_id, cls)


# ---------------------------------------------------------------- 全态

def zone_rects(board):
    """board.zones → (sensitive_rects, keepout_rects)（check_all 消费形态:
    sensitive=dict 形 / keepout=元组形——v5.drc.check_ana_proximity 与
    check_keepout 各自的消费口径）。"""
    sensitive, keepout = [], []
    for z in board.get("zones") or []:
        rect = z.get("rect") or {}
        try:
            r4 = (float(rect["x_min"]), float(rect["y_min"]),
                  float(rect["x_max"]), float(rect["y_max"]))
        except (KeyError, TypeError, ValueError):
            continue
        if z.get("kind") == "keepout":
            keepout.append((z.get("zone_id", "zone"), r4))
        elif z.get("kind") == "sensitive":
            sensitive.append((z.get("zone_id", "zone"),
                              {"x_min": r4[0], "y_min": r4[1],
                               "x_max": r4[2], "y_max": r4[3]}))
    return sensitive, keepout


def validate_full(st):
    """全态检查 → v5.drc.DRCReport。

    同源聚合: check_all（R5/R2/R6/capacity/width；zones→sensitive/keepout
    透传）+ check_edge_clearance（D6-3 板边带）+ 孔双面（track 端点豁免/
    via 零豁免，谓词同源）。width_checks=每有铜网 (net, 档宽 mm, R1.floor)。
    放置合法性不在本入口（接线点 3 裁决: 两层 verdict 口径不同源不并入
    DRCReport——全场放置检查独立调 placecheck.check_all_placements）。"""
    from . import instantiate as inst
    board = st.board
    hard = board["hard_rules"]
    coppers = _scene(st)
    sensitive, keepout = zone_rects(board)
    width_checks = []
    for net_id in sorted(st.known_nets()):
        has_copper = (any(s["net_id"] == net_id for s in st.segs.values())
                      or any(v["net_id"] == net_id for v in st.vias.values()))
        if has_copper:
            w = net_width(st, net_id, _effective_width_class(st, net_id))
            width_checks.append((net_id, w, float(hard["R1"]["floor_mm"])))
    report = drc.check_all(coppers, hard, sensitive_rects=sensitive,
                           keepout_rects=keepout, width_checks=width_checks)
    extra = list(drc.check_edge_clearance(coppers, ws_tuple(board)))
    holes = drc.normalize_holes(board.get("holes"))
    vm = via_model_params(board)
    for sid in sorted(st.vias):
        v = st.vias[sid]
        mm = st.lattice.to_mm(*v["grid"])
        for hi, (hx, hy, hr) in enumerate(holes):
            if drc.hole_via_blocked((hx, hy), hr, mm, vm["radius"]):
                extra.append(drc.Violation(
                    "hole_to_hole", v["shape_id"], "hole:%d" % hi,
                    {"via_r_mm": vm["radius"], "hole_r_mm": hr}))
    exempt_by_net = {net_id: _hole_exempt(st, net_id)
                     for net_id in sorted(st.known_nets())}
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        pts, _stub = inst.segment_mm(st, seg)
        hw = net_width(st, seg["net_id"], seg["width_class"]) / 2.0
        for hi, (hx, hy, hr) in enumerate(holes):
            if hi in exempt_by_net.get(seg["net_id"], ()):
                continue
            for a, b in zip(pts[:-1], pts[1:]):
                if drc.hole_track_blocked((hx, hy), hr, a, b, hw):
                    extra.append(drc.Violation(
                        "hole_to_hole", seg["shape_id"], "hole:%d" % hi,
                        {"face": "track", "half_width_mm": hw}))
                    break
    if extra:
        return drc.DRCReport(list(report.violations) + extra,
                             report.checked_pairs)
    return report
