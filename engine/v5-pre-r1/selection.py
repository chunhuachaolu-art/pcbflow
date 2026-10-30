# -*- coding: utf-8 -*-
"""L6 引擎终选与三态判定（任务书 A4 执行合同 + §3.6 三态合同；P3 交付）。

职责（V5.0-DEV-TASKBOOK §4 L6）：
- 对全部候选**无上限逐一测量**（measure.measure_assignment，A4/U8 不设限）+
  v5.drc 判定（候选折线与板内固定铜构建 Copper 场景后 check_all，A9 唯一内源）；
- 非法/不可行候选 fail-closed 滤除并逐条计数入台账（滤除原因 = DRC 违例条目键路径 /
  度量不可行的具体键路径）；
- 可行者按实测目标值升序取最优；同分 tie-break = 候选注册序在前（即 candidate_id 序，
  A4/U8 确定性要求）；
- 三态判定（§3.6）：
  * SAT   → 验收件（无证书；best+ledger 经 staging 写 out_dir）；
  * UNSAT → failcert.build_unsat_cert：unsat_core 由台账中的容量/宽度不可行算术转出，
    必须过独立复核器 failcert.verify；
  * UNKNOWN → 资源耗尽 = 操作者裁定形态（build_unknown_cert：achieved/blocked_at/budget
    如实——本阶段 budget 为 "selection 测试注入" 类占位 + 真实 measured 数）。
    不可机械复核的不可行主张（如纯 R5/R6 滤除，当前复核器只支持 capacity/width 条目）
    按 §3.6「不可复核的不可行主张一律降记 UNKNOWN」处置。
- 落盘经 StagingTransaction 原子提交；文件带 sidecar 合规 provenance 头。
  证书文件本体受 failcert.v1 additionalProperties:false 约束保持**纯证书形态**
  （可直接独立 verify），其 provenance 头记入同事务的 <board>.selection.json
  （cert_sha256 对账）——最小文档化决定。

候选合同（planner 产出形状，本模块按形状消费）：
  {"candidate_id","arm","provenance","route_order","layer_assignment","polylines",
   "generation_trace"}

度量口径注记（确定性）：
- transition_vias 候选合同不携带 → 依 measure 模块缺省 0（单层走线）；
- DRC 场景铜 = 候选折线（中心线）+ 板内固定铜（既布 ROUTED 分区端点折线、带
  geometry.copper_band 的固定 ribbon 铜带矩形）；端点焊盘几何归 L7 执行器细化，本层不建模；
- 判定编排（全部出自 v5.drc，无旁路几何实现）：
  * R5/R2/capacity/R1 走 check_all 聚合（折线级精确判定）；
  * R6 禁布区用 v5.drc.check_keepout 对**逐段分解铜**精查——check_keepout 的折线
    bbox 形态对绕行走线过保守（V2 场景合法绕行解的 bbox 必然扫过 K1/K2），逐段
    bbox 消除该伪影；对角段 bbox 仍偏保守（保守方向=误杀不漏放，fail-closed）；
  * 违例归责：仅含候选铜（cid 前缀 "cand:"）的违例或 capacity/R1 才滤除候选；
    固定铜互扰（如 V2 表内播种缺陷 P4 带↔P9）= 板内固有缺陷，归席位 A/L8 业务，
    不归责候选、不重复计入每候选。
- 走廊容量按（走廊 × 信号层）核算：固定铜按声明占用（geometry.occupancy_mm）或计划宽，
  候选铜按分区计划宽；条目序 = 固定铜（板注册序）在前、候选铜按 route_order；
- R1 宽度核查只对被布线且 current_a>0 的分区（planned_width < 保守下限 → R1）。

理念账本骨架（§3.8 六问的引擎侧最小实现）：从 candidates.generation_trace 与滤除记录
自动归类 生效/被忽略/冲突裁决/致淘汰/无可观测影响/依据不足；generation_trace 兼容
planner 合同形态（rule/freedom/effect）与 principle_id 夹具形态，priority 缺省时查板
principle_registry 兜底（查不到 → 0）；完整账本是 L8 的事，本阶段给数据源。
"""
import math
import os

from . import canonical, failcert, staging
from . import board as board_mod
from .drc import Copper, check_all, check_keepout
from .measure import measure_assignment
from .metrics import capacity as cap_mod
from .metrics import clearance
from .metrics import width_prior as wp

SELECTION_VERSION = "v5.selection/0.1.0"
GENERATOR = "v5.selection"

# 理念账本六态（§3.8 六问）
PL_EFFECTIVE = "生效"          # 有生成留痕且候选可行（消费痕进最优/可行解）
PL_IGNORED = "被忽略"          # principle 臂候选留痕为空（编译规则未被消费）
PL_ARBITRATED = "冲突裁决"     # 候选被 DRC 滤除且留痕关联，priority 让位（loser 注记）
PL_ELIMINATED = "致淘汰"       # 候选被 DRC 滤除且留痕关联（胜者/单留痕）
PL_NO_OBSERVABLE = "无可观测影响"  # 注册表在册但本批无任何消费痕，且存在可行候选
PL_INSUFFICIENT = "依据不足"   # 其余（无留痕/仅非法候选留痕/无可行候选无对照）


class SelectionError(ValueError):
    pass


# ---------------------------------------------------------------- 板视图（只读）

def _zone_rect(zone):
    """zone.rect 归一为 (x0, y0, x1, y1)。"""
    rect = zone["rect"]
    if isinstance(rect, dict):
        return (float(rect["x_min"]), float(rect["y_min"]),
                float(rect["x_max"]), float(rect["y_max"]))
    return (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))


class _BoardView:
    """板的确定性只读视图（L0 已 fail-closed 校验，本层不重复载入校验）。"""

    def __init__(self, board):
        self.board = board
        self.board_id = board["board_id"]
        self.provenance = board.get("provenance", {})
        self.board_sha256 = board_mod.compute_board_sha256(board)
        self.partitions = {p["partition_id"]: p for p in board.get("partitions", [])}
        self.partition_order = [p["partition_id"] for p in board.get("partitions", [])]
        self.net_of = {}
        for net in board.get("nets", []):
            for pid in net.get("partitions", []):
                self.net_of[pid] = net["net_id"]
        self.layers = {l["id"]: l for l in board.get("stackup", [])}
        self.layer_directions = {lid: l.get("preferred_direction", "any")
                                 for lid, l in self.layers.items()}
        self.plane_layers = tuple(sorted(
            lid for lid, l in self.layers.items() if l.get("kind") == "plane"))
        zones = board.get("zones", [])
        self.keepouts = [(z["zone_id"], _zone_rect(z))
                         for z in zones if z.get("kind") == "keepout"]
        self.sensitives = [(z["zone_id"], z["rect"])
                           for z in zones if z.get("kind") == "sensitive"]
        self.corridors = [z for z in zones if z.get("kind") == "corridor"]
        self.registry_ids = sorted({p["principle_id"]
                                    for p in board.get("principle_registry", [])
                                    if isinstance(p, dict) and p.get("principle_id")})


# ---------------------------------------------------------------- 场景固定铜

def _fixed_coppers(view):
    """板内固定铜（板分区注册序）：ROUTED 既布折线 + copper_band ribbon 铜带。

    返回 (coppers, declared_occupancy)；declared_occupancy 以铜 cid 为键。
    """
    coppers = []
    declared = {}
    for pid in view.partition_order:
        p = view.partitions[pid]
        geo = p.get("geometry") or {}
        layer = p.get("layer_policy")
        net = view.net_of.get(pid, pid)
        half = float(p.get("planned_width", 0.2)) / 2.0
        band = geo.get("copper_band")
        if band:
            (x0, y0), (x1, y1) = geo["endpoints"][0], geo["endpoints"][1]
            lo, hi = sorted((float(band[0]), float(band[1])))
            if abs(float(x1) - float(x0)) <= clearance.EPS:
                # 竖直 ribbon：band 给 x 区间，y 跨取端点
                rect = (lo, min(float(y0), float(y1)), hi, max(float(y0), float(y1)))
            else:
                # 水平 ribbon：band 给 y 区间，x 跨取端点
                rect = (min(float(x0), float(x1)), lo, max(float(x0), float(x1)), hi)
            coppers.append(Copper(net, "fixed:%s" % pid, layer, band=rect, half_width=half))
            if geo.get("occupancy_mm") is not None:
                declared["fixed:%s" % pid] = float(geo["occupancy_mm"])
        elif p.get("ptype") == "ROUTED" and geo.get("endpoints"):
            pts = [[float(pt[0]), float(pt[1])] for pt in geo["endpoints"]]
            coppers.append(Copper(net, "fixed:%s" % pid, layer, polyline=pts,
                                  half_width=half))
    return coppers, declared


# ---------------------------------------------------------------- 候选核验（度量侧）

def _rej(cid, kind, path, rule, detail, **extra):
    rec = {"candidate_id": cid, "kind": kind, "path": path, "rule": rule,
           "detail": detail}
    rec.update(extra)
    return rec


def _polyline_ok(pts):
    if not isinstance(pts, (list, tuple)) or len(pts) < 2:
        return None
    out = []
    for pt in pts:
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            return None
        x, y = pt[0], pt[1]
        for v in (x, y):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                return None
            if not math.isfinite(v):
                return None
        out.append([float(x), float(y)])
    return out


def _validate_candidate(view, cand, idx):
    """度量侧结构核验（fail-closed）。

    返回 (errors, routes, ordered, cid_led, layers_map, polylines_norm)。
    errors 非空时后续条目为空（候选不进测量环）。
    """
    if not isinstance(cand, dict):
        cid_led = "cand[%d]" % idx
        return ([_rej(cid_led, "measure", "candidate", None, "候选必须是 dict")],
                [], [], cid_led, {}, {})
    raw_cid = cand.get("candidate_id")
    cid_led = raw_cid if isinstance(raw_cid, str) and raw_cid else "cand[%d]" % idx
    errors = []
    polylines = cand.get("polylines")
    layers = cand.get("layer_assignment")
    if not isinstance(polylines, dict):
        errors.append(_rej(cid_led, "measure", "polylines", None, "缺失或非 dict"))
        polylines = {}
    if not isinstance(layers, dict):
        errors.append(_rej(cid_led, "measure", "layer_assignment", None, "缺失或非 dict"))
        layers = {}
    pids = sorted(set(map(str, polylines)) | set(map(str, layers)))
    norm_poly = {}
    norm_layers = {}
    for pid in pids:
        if pid not in view.partitions:
            errors.append(_rej(cid_led, "measure", "polylines/%s" % pid, None,
                               "指向不存在的分区 %r" % pid))
            continue
        if pid not in layers:
            errors.append(_rej(cid_led, "measure", "layer_assignment.%s" % pid, None,
                               "缺层分配"))
            continue
        if pid not in polylines:
            errors.append(_rej(cid_led, "measure", "polylines.%s" % pid, None, "缺折线"))
            continue
        layer = layers[pid]
        info = view.layers.get(layer)
        if info is None:
            errors.append(_rej(cid_led, "measure", "layer_assignment.%s" % pid, None,
                               "未知层 %r" % (layer,)))
        elif info.get("kind") != "signal" or not info.get("available", False):
            errors.append(_rej(cid_led, "measure", "layer_assignment.%s" % pid, None,
                               "层 %r 不可布线（非信号层或不可用）" % (layer,)))
        pts = _polyline_ok(polylines[pid])
        if pts is None:
            errors.append(_rej(cid_led, "measure", "polylines.%s" % pid, None,
                               "折线须为 ≥2 个 [x,y] 有限数值坐标点"))
            continue
        norm_poly[pid] = pts
        norm_layers[pid] = layer
    if errors:
        return errors, [], [], cid_led, {}, {}
    route_order = cand.get("route_order")
    ordered = []
    if isinstance(route_order, list):
        for pid in route_order:
            if isinstance(pid, str) and pid in norm_poly and pid not in ordered:
                ordered.append(pid)
    ordered.extend(pid for pid in sorted(norm_poly) if pid not in ordered)
    routes = [{"net_id": view.net_of.get(pid, pid), "layer": norm_layers[pid],
               "polyline": norm_poly[pid], "transition_vias": 0}
              for pid in ordered]
    return errors, routes, ordered, cid_led, norm_layers, norm_poly


# ---------------------------------------------------------------- 容量/宽度核算

def _rect_dict(rect):
    return {"x_min": rect[0], "y_min": rect[1], "x_max": rect[2], "y_max": rect[3]}


def _copper_in_rect(cu, rect_d):
    """铜中心线几何是否进入矩形（间隙 ≤ EPS）。事实核算，判定归 v5.drc。"""
    if cu.band is not None:
        return clearance.rect_rect_gap(cu.band, (rect_d["x_min"], rect_d["y_min"],
                                                 rect_d["x_max"], rect_d["y_max"])) \
            <= clearance.EPS
    if cu.pad is not None:
        return clearance.pad_rect_distance(cu.pad[0], cu.pad[1], rect_d) <= clearance.EPS
    return min(clearance.segment_rect_distance(a, b, rect_d)
               for a, b in clearance.polyline(cu.polyline)) <= clearance.EPS


def _capacity_checks(view, cand_coppers, fixed_coppers, declared):
    """逐（走廊×信号层）占用核算。返回 (capacity_checks, meta)。

    meta[corridor_layer_id] = {"terms": [...], "capacity_mm": c}——供 UNSAT 证书转出。
    """
    checks, meta = [], {}
    for zone in view.corridors:
        rect = _zone_rect(zone)
        rect_d = _rect_dict(rect)
        cap = float(zone["capacity"])
        by_layer = {}
        for cu in list(cand_coppers) + list(fixed_coppers):
            info = view.layers.get(cu.layer)
            if info is None or info.get("kind") != "signal":
                continue
            if _copper_in_rect(cu, rect_d):
                by_layer.setdefault(cu.layer, []).append(cu)
        for layer in sorted(by_layer):
            group = by_layer[layer]
            fixed_part = [cu for cu in group if cu.cid.startswith("fixed:")]
            cand_part = [cu for cu in group if not cu.cid.startswith("fixed:")]
            entries = []
            for cu in fixed_part + cand_part:   # 条目序 = 板注册序在前，候选按 route_order
                entries.append(cap_mod.CapacityEntry(
                    cu.net_id, cu.half_width * 2.0,
                    declared_occupancy=declared.get(cu.cid)))
            occ = cap_mod.corridor_occupancy(entries)
            clid = "%s/%s" % (zone["zone_id"], layer)
            checks.append((clid, occ, cap))
            meta[clid] = {"terms": [float(e.occupancy) for e in entries],
                          "capacity_mm": cap}
    return checks, meta


def _width_checks(view, ordered_pids):
    """被布线且有电流分区的 R1 宽度核算。返回 (width_checks, meta)。"""
    checks, meta = [], {}
    r1 = view.board.get("hard_rules", {}).get("R1", {})
    for pid in ordered_pids:
        p = view.partitions[pid]
        cur = float(p.get("current_a") or 0.0)
        if cur <= 0:
            continue
        required = wp.conservative_min_width(
            cur, fab_min_mm=0.0,
            k_per_amp=float(r1.get("k_a", wp.DEFAULT_K_PER_AMP)),
            floor_mm=float(r1.get("floor_mm", wp.DEFAULT_FLOOR_MM)))
        planned = float(p.get("planned_width") or 0.0)
        checks.append((pid, planned, required))
        meta[pid] = {"planned_mm": planned, "required_min_mm": required}
    return checks, meta


# ---------------------------------------------------------------- DRC 判定编排

def _run_drc(view, cand_coppers, fixed_coppers, cap_checks, w_checks):
    """DRC 判定编排（全部经 v5.drc，无旁路几何实现）。

    R5/R2/capacity/R1 走 check_all 聚合（折线级精确判定）；R6（禁布区+plane 层）用
    check_keepout 对逐段分解铜精查——check_keepout 的折线 bbox 形态对绕行走线过保守
    （V2 场景合法绕行解的 bbox 必然扫过 K1/K2），逐段 bbox 消除该伪影；对角段 bbox
    仍偏保守（保守方向 = 误杀不漏放，fail-closed）。返回合并违例列表
    （聚合序在前、R6 在后，确定性）。
    """
    scene = list(cand_coppers) + list(fixed_coppers)
    report = check_all(scene, view.board["hard_rules"],
                       sensitive_rects=view.sensitives,
                       capacity_checks=cap_checks,
                       width_checks=w_checks)
    r6 = check_keepout(_segment_coppers(scene), view.keepouts, view.plane_layers)
    return list(report.violations) + list(r6)


def _segment_coppers(coppers):
    """折线铜逐段分解为单段铜（R6 精查用）；带/焊盘原样保留。"""
    out = []
    for cu in coppers:
        if cu.polyline:
            for k, (a, b) in enumerate(clearance.polyline(cu.polyline)):
                out.append(Copper(cu.net_id, "%s#seg%d" % (cu.cid, k), cu.layer,
                                  polyline=[[a[0], a[1]], [b[0], b[1]]],
                                  half_width=cu.half_width))
        else:
            out.append(cu)
    return out


def _candidate_attribution(violation):
    """违例归责：仅候选责任违例滤除候选。

    capacity/R1（走廊占用/宽度由候选布线选择触发）恒归责候选；其余规则按违例主体
    是否含候选铜（cid 前缀 "cand:"）判定；固定铜互扰（双 fixed，如 V2 表内播种缺陷
    P4 带↔P9）= 板内固有缺陷，归席位 A/L8 业务，不归责候选。
    """
    if violation.rule in ("capacity", "R1"):
        return True
    for s in (violation.subject_a, violation.subject_b):
        if isinstance(s, str) and s.startswith("cand:"):
            return True
    return False


# ---------------------------------------------------------------- UNSAT 证书转出

def _fmt_num(v):
    return "%.10g" % v


def _capacity_core_entry(meta):
    terms = [round(t, 10) for t in meta["terms"]]
    cap = meta["capacity_mm"]
    n = len(terms)
    total = round(sum(terms) + cap_mod.NET_NET_SPACING * (n - 1), 10) if n else 0.0
    if n:
        arith = "%s+%s×%d=%s > %s" % ("+".join(_fmt_num(t) for t in terms),
                                      _fmt_num(cap_mod.NET_NET_SPACING), n - 1,
                                      _fmt_num(total), _fmt_num(cap))
    else:
        arith = "0 > %s" % _fmt_num(cap)
    return {"constraint": "capacity",
            "data": {"occupancy_terms": terms, "capacity_mm": cap},
            "arithmetic": arith}


def _width_core_entry(meta):
    w, m = meta["planned_mm"], meta["required_min_mm"]
    return {"constraint": "width",
            "data": {"planned_mm": w, "required_min_mm": m},
            "arithmetic": "%s < %s" % (_fmt_num(w), _fmt_num(m))}


def _unsat_core(rejections, cap_meta_by_cand, width_meta_by_cand):
    """从台账滤除记录转出可机械复核的 unsat_core（capacity/width），canonical 去重。"""
    core, seen = [], set()
    for r in rejections:
        if r["kind"] != "drc":
            continue
        entry = None
        if r["rule"] == "capacity" and r.get("subject"):
            meta = cap_meta_by_cand.get(r["candidate_id"], {}).get(r["subject"])
            if meta:
                entry = _capacity_core_entry(meta)
        elif r["rule"] == "R1" and r.get("partition"):
            meta = width_meta_by_cand.get(r["candidate_id"], {}).get(r["partition"])
            if meta:
                entry = _width_core_entry(meta)
        if entry is None:
            continue
        key = canonical.canonical_sha256(entry)
        if key not in seen:
            seen.add(key)
            core.append(entry)
    return core


# ---------------------------------------------------------------- 理念账本骨架

def _normalize_trace(trace):
    """generation_trace 规整：str → principle_id；dict → principle_id + priority。

    dict 兼容两形态：含 principle_id（测试夹具形态）或含 rule（planner 合同形态
    rule/freedom/effect，取 rule 为 principle_id）；两者都不含 → 跳过该条。
    priority 缺省记 None，由 _principle_ledger 按板 principle_registry 查表兜底
    （查不到 → 0）。
    """
    out = []
    if not isinstance(trace, list):
        return out
    for item in trace:
        if isinstance(item, str) and item:
            out.append({"principle_id": item, "priority": None})
        elif isinstance(item, dict):
            pid = item.get("principle_id") or item.get("rule")
            if not pid:
                continue
            prio = item.get("priority")
            out.append({"principle_id": str(pid),
                        "priority": prio if isinstance(prio, (int, float)) else None})
    return out


def _principle_ledger(view, candidates, outcome, objectives):
    """P3 批次理念账本骨架（§3.8 六问的引擎侧自动归类）。

    决策树（先见定态，按下列次序处理，保证确定性）：
      1. 留痕出现在可行候选 → 生效；
      2. 留痕出现在 DRC 滤除候选：该候选留痕内 priority 非最高者 → 冲突裁决（loser 注记），
         最高者（含单留痕）→ 致淘汰；
      3. 留痕仅出现在度量非法候选 → 依据不足；
      4. 全批无留痕：存在 principle 臂空留痕候选 → 被忽略；存在可行候选 → 无可观测影响；
         其余 → 依据不足。
    priority 缺省（留痕未携带）时按 principle_id 查板 principle_registry 的 priority
    查表兜底，查不到 → 0（planner 留痕形态 rule/freedom/effect 不携带 priority）。
    """
    registry_prio = {}
    for p in view.board.get("principle_registry", []):
        if isinstance(p, dict) and p.get("principle_id"):
            registry_prio[str(p["principle_id"])] = p.get("priority", 0)

    traces, arm_empty_principle = {}, []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        cid = cand.get("candidate_id") if isinstance(cand.get("candidate_id"), str) \
            and cand.get("candidate_id") else "cand[?]"
        items = _normalize_trace(cand.get("generation_trace"))
        for it in items:
            if it["priority"] is None:
                rp = registry_prio.get(it["principle_id"], 0)
                it["priority"] = rp if isinstance(rp, (int, float)) else 0
        traces[cid] = items
        if cand.get("arm") == "principle" and not items:
            arm_empty_principle.append(cid)

    ledger, first_status = [], {}

    def note(pid, status, evidence):
        if pid not in first_status:
            first_status[pid] = status
            ledger.append({"principle_id": pid, "status": status,
                           "evidence": evidence})

    # 1. 生效
    for cid in sorted(traces):
        if outcome.get(cid) != "feasible":
            continue
        for item in traces[cid]:
            note(item["principle_id"], PL_EFFECTIVE,
                 "候选 %s 可行（实测目标 %s）且生成留痕消费该编译规则"
                 % (cid, _fmt_num(objectives.get(cid, 0.0))))
    # 2. 致淘汰 / 冲突裁决（DRC 滤除且留痕关联，按 priority 注记）
    for cid in sorted(traces):
        if outcome.get(cid) != "drc":
            continue
        items = traces[cid]
        if not items:
            continue
        max_prio = max(it["priority"] for it in items)
        for item in items:
            if item["priority"] < max_prio:
                note(item["principle_id"], PL_ARBITRATED,
                     "候选 %s 被 DRC 滤除；priority %s 让位于 %s（冲突裁决 loser）"
                     % (cid, _fmt_num(item["priority"]), _fmt_num(max_prio)))
            else:
                note(item["principle_id"], PL_ELIMINATED,
                     "候选 %s 因 DRC 违例被 fail-closed 滤除，生成留痕关联该规则" % cid)
    # 3. 仅非法候选留痕 → 依据不足
    for cid in sorted(traces):
        if outcome.get(cid) != "measure":
            continue
        for item in traces[cid]:
            note(item["principle_id"], PL_INSUFFICIENT,
                 "留痕仅出现在度量非法候选 %s 中，消费行为不可信" % cid)
    # 4. 全批无留痕的注册表理念
    any_feasible = any(v == "feasible" for v in outcome.values())
    for pid in view.registry_ids:
        if pid in first_status:
            continue
        if arm_empty_principle:
            note(pid, PL_IGNORED,
                 "principle 臂候选 %s 生成留痕为空，编译规则未被消费"
                 % sorted(arm_empty_principle)[0])
        elif any_feasible:
            note(pid, PL_NO_OBSERVABLE, "本批无可观测消费痕，且存在可行候选")
        else:
            note(pid, PL_INSUFFICIENT, "无生成留痕、无 principle 臂对照且无可行候选")
    ledger.sort(key=lambda e: e["principle_id"])
    return ledger


# ---------------------------------------------------------------- 三态与落盘

def _scope_nets(view, candidates):
    nets = set()
    for cand in candidates:
        if isinstance(cand, dict) and isinstance(cand.get("polylines"), dict):
            for pid in cand["polylines"]:
                nid = view.net_of.get(pid)
                if nid:
                    nets.add(nid)
    return sorted(nets)


def _build_unknown_cert(view, candidates, measured, rejected):
    if measured == 0:
        blocked = "候选集为空（无可测候选），无法给出可行解或可机械复核的不可行证明"
    else:
        blocked = ("全部 %d 个候选被 fail-closed 滤除（纯 DRC 硬规则滤除，当前独立复核器"
                   "不支持该类条目的机械复算），不可行主张按 §3.6 降记 UNKNOWN" % rejected)
    return failcert.build_unknown_cert(
        view.provenance, _scope_nets(view, candidates),
        achieved={"nets_connected": 0, "nets_total": len(view.board.get("nets", []))},
        blocked_at={"description": blocked},
        budget={"consumed": {"candidates_measured": measured,
                             "candidates_rejected": rejected},
                "limit": {"candidates_max": "unbounded（A4/U8 不设限）",
                          "note": "selection 测试注入占位：P3 阶段候选集由测试/规划器"
                                  "注入，无独立搜索预算"}})


def _write_out(view, result, cert, out_dir):
    """staging 事务原子提交：selection/ledger/证书三件（SAT 无证书件）。"""
    board_id = view.board_id
    header = {"generator": GENERATOR, "generator_version": SELECTION_VERSION,
              "board_sha256": view.board_sha256}
    cert_bytes = failcert.cert_bytes(cert) if cert is not None else None
    selection_doc = {"provenance": header, "board_id": board_id,
                     "verdict": result["verdict"], "best": result["best"],
                     "per_candidate": result["per_candidate"]}
    if cert_bytes is not None:
        # 证书本体保持纯 failcert.v1 形态（additionalProperties:false），
        # provenance 头以 cert_sha256 对账记入 selection 件（最小文档化决定）。
        selection_doc["cert_kind"] = "failcert.v1"
        selection_doc["cert_sha256"] = canonical.sha256_bytes(cert_bytes)
    ledger_doc = {"provenance": header, "board_id": board_id,
                  "verdict": result["verdict"], "ledger": result["ledger"]}
    staging_root = os.path.join(out_dir, "_staging")
    tx = staging.StagingTransaction(staging_root, out_dir, "%s.selection" % board_id)
    try:
        tx.write_json("%s.selection.json" % board_id, selection_doc)
        tx.write_json("%s.selection-ledger.json" % board_id, ledger_doc)
        if cert_bytes is not None:
            tx.write_bytes("%s.failcert.json" % board_id, cert_bytes)
        tx.commit()
    except Exception:
        tx.rollback()
        raise


# ---------------------------------------------------------------- 主入口

def select_best(board, candidates, out_dir=None):
    """A4 终选 + §3.6 三态判定。返回
    {"verdict": "SAT|UNSAT|UNKNOWN", "best": 候选|None,
     "ledger": {"measured", "rejected", "rejection_reasons", "principle_ledger"},
     "per_candidate": [{candidate_id, feasible, objective, drc_violations}]}。

    out_dir 给定时经 StagingTransaction 原子落盘（SAT=验收件无证书；
    UNSAT/UNKNOWN 附 <board>.failcert.json 纯证书件，可独立 failcert.verify）。
    """
    view = _BoardView(board)
    if candidates is None:
        candidates = []
    if not isinstance(candidates, list):
        raise SelectionError("candidates 必须是 list（A4 全测，逐候选注册序）")

    fixed_coppers, declared = _fixed_coppers(view)
    per_candidate = []
    rejections = []
    outcome = {}            # cid -> feasible | drc | measure
    objectives = {}         # cid -> 实测目标值（可行者）
    cap_meta_by_cand = {}   # cid -> {corridor_layer_id: meta}
    width_meta_by_cand = {}  # cid -> {partition_id: meta}

    for idx, cand in enumerate(candidates):
        errors, routes, ordered, cid, layers_map, poly_map = \
            _validate_candidate(view, cand, idx)
        if errors:
            rejections.extend(errors)
            outcome[cid] = "measure"
            per_candidate.append({"candidate_id": cid, "feasible": False,
                                  "objective": None, "drc_violations": None})
            continue
        try:
            m = measure_assignment(routes, view.layer_directions)
        except Exception as exc:  # 度量不可行 fail-closed（含浮点异常）
            rejections.append(_rej(cid, "measure", "measure_assignment", None,
                                   "度量失败: %s" % exc))
            outcome[cid] = "measure"
            per_candidate.append({"candidate_id": cid, "feasible": False,
                                  "objective": None, "drc_violations": None})
            continue
        cand_coppers = [
            Copper(view.net_of.get(pid, pid), "cand:%s:%s" % (cid, pid),
                   layers_map[pid], polyline=poly_map[pid],
                   half_width=float(view.partitions[pid].get("planned_width", 0.2)) / 2.0)
            for pid in ordered]
        cap_checks, cap_meta = _capacity_checks(view, cand_coppers, fixed_coppers,
                                                declared)
        w_checks, w_meta = _width_checks(view, ordered)
        violations = _run_drc(view, cand_coppers, fixed_coppers, cap_checks, w_checks)
        cap_meta_by_cand[cid] = cap_meta
        width_meta_by_cand[cid] = w_meta
        cand_violations = [v for v in violations if _candidate_attribution(v)]
        if cand_violations:
            for i, v in enumerate(violations):
                if not _candidate_attribution(v):
                    continue   # 固定铜互扰=板内固有缺陷，不归责候选（见模块注记）
                vd = v.as_dict()
                extra = {}
                if v.rule == "capacity":
                    extra["subject"] = v.subject_a
                elif v.rule == "R1":
                    extra["partition"] = v.subject_a
                rejections.append(_rej(cid, "drc", "drc.violations[%d]" % i, v.rule,
                                       "%s: %s" % (v.rule, vd["subjects"]), **extra))
            outcome[cid] = "drc"
            per_candidate.append({"candidate_id": cid, "feasible": False,
                                  "objective": None,
                                  "drc_violations": len(cand_violations)})
            continue
        outcome[cid] = "feasible"
        objectives[cid] = m["total_cost"]
        per_candidate.append({"candidate_id": cid, "feasible": True,
                              "objective": m["total_cost"], "drc_violations": 0})

    feasible = sorted(objectives, key=lambda c: (objectives[c], c))
    if feasible:
        verdict, best, cert = "SAT", _find_candidate(candidates, feasible[0]), None
    else:
        core = _unsat_core(rejections, cap_meta_by_cand, width_meta_by_cand)
        measured = len(per_candidate)
        rejected = measured - len(feasible)
        if core:
            verdict, best = "UNSAT", None
            cert = failcert.build_unsat_cert(view.provenance,
                                             _scope_nets(view, candidates), core)
        else:
            verdict, best = "UNKNOWN", None
            cert = _build_unknown_cert(view, candidates, measured, rejected)

    ledger = {"measured": len(per_candidate),
              "rejected": sum(1 for pc in per_candidate if not pc["feasible"]),
              "rejection_reasons": rejections,
              "principle_ledger": _principle_ledger(view, candidates, outcome,
                                                    objectives)}
    result = {"verdict": verdict, "best": best, "ledger": ledger,
              "per_candidate": per_candidate}
    if out_dir is not None:
        _write_out(view, result, cert, out_dir)
    return result


def _find_candidate(candidates, cid):
    """按 candidate_id 取回原候选（注册序首个匹配；合同保证 id 唯一）。"""
    for cand in candidates:
        if isinstance(cand, dict) and cand.get("candidate_id") == cid:
            return cand
    raise SelectionError("可行候选 %s 在注册表中不可回取（内部一致性破坏）" % cid)
