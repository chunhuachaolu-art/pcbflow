# -*- coding: utf-8 -*-
"""v5_diag_inherent.py — 「板固有不可布」witness 自动归因器（V5-SMALLWAVE A1，
2026-09-23；方法移植源=out/v5-p5/diag-failed8/diag_failed8.py + itemize_fixed.py，
判据冻结于 route-v5/V5-SMALLWAVE-TASKBOOK-2026-09-23.md §1.A1）。

1.1.0（V5-DIAG-REPLAY-R1 W-1，2026-10-02；合同范围冻结件=
out/v5-p5/diag-replay-r1/PREREG-DIAG-REPLAY-R1.md §3）：重放合同对齐
executor 0.9.0 双面——
- 0.9.0 主锚面：replay_capture 镜像 0.9.0 主环（SC-1 事前短路
  _preflight_seal_shortcircuit＋多端网 Steiner 边序 _edge_sequences/
  _run_net_ladder/MST 回退/_ripup_retry 新签名），短路终态构造捕获态供
  witness（类摘除/宽度探针在短路捕获态上运行）；verdict_provenance
  出口读数对账（execute.json 顶层在键时）。
- 0.8.0 存档忠实重放面：现役 0.9.0 引擎重放 0.8.0 档案——0.9.0-only
  单行（preflight-seal-abstain 披露行）不入 0.8.0 档案对账集；短路
  整路行集与 0.8.0 阶梯体不可互strip（属语义分歧=MISMATCH 如实报，不
  以 0.9.0 面吞并 0.8.0 档案语义）；verdict_provenance（0.9.0-only 面）
  不入 0.8.0 档案对账集。
- 对齐只改本归因器消费面，不改 executor（任务书 W-1 条款）。
- 板文档读取 wrap 容差：顶层含 board 键（真实板 wrap）取 doc["board"]
  裸化，合成板裸文档直读（exec-eng-r1.runner 双源同口径）。

1.1.1（判读修复轮，2026-10-02；D-J3 工具面根因）：SC-1 短路捕获态的
类摘除解锁测试改在**密封域**度量（摘类→复跑 _seal_survey_rows 普查→
S(e) 是否解封）——1.1.0 的梯面试点口径在短路捕获态会混入另端无关阻断
（syn-u02 另端在 keepout 内：六类摘除均「A* 空间耗尽」→误报
undetermined，破门 D-J3「10/10 出真实三分类」）；梯面六行保留为
ladder_removal_unlock 诊断披露（不参与终判）。同时修复 1.0.0 起两处
探针态泄漏：holes/edge 摘除后未还原（泄漏进宽度探针）+ 空间粗网格未
随 holes 变更失效（holes 摘除在引擎谓词面实际无效）。

对一块 FAILED 板做只读根因诊断（四件套：忠实重放→失败网捕获态→类摘除
解锁测试/通道扫描/端点密封普查→三分类终判），**只诊断、不产生记分牌主张**
（沿用诊断批红线 5：不写 boards/ 任何数据面、不进 gate/记分牌）。

用法（二选一）：
  python tools/v5_diag_inherent.py --board <板名> [--boards-root DIR]
  python tools/v5_diag_inherent.py --board-json PATH --execute-json PATH
可选：--json PATH|-（机器输出；- = stdout）、--net NET（预期失败网核对）、
      --itemize-fixed（固定铜逐项指认段）、--skip-width-probes（跳过 (c)
      判别宽度探针）、--pitches "0.25,0.125,0.0625"（密封普查栅距档）。

流程与判据（冻结）：
1. 忠实重放：以 execute.json 末轮候选（tried_candidates[-1].index）镜像
   execute_candidate 主环（引擎私有件原样调用），negotiation_log 与
   boards/<b>/execute.json 对账——0.6.1 起容差=「剔除 geom-secondary 行后
   逐字节等」（log-only 披露行，任务书 §1.A3；raw 逐字节等亦单独报告）；
   不一致=合同缺口（exit 3，不分类）。
2. witness（捕获态上）：端点几何/端点密封普查（r0+r1×八向锚节点出边/
   换层边，逐层带原因标记；三档 pitch）/直连走廊通道扫描（41 采样点，逐层
   两侧最近障碍 vs 需求 2×R5）/阻塞类摘除解锁测试（六类：routes/vias/
   holes/edge/fixed/all-geometric；缩减阶梯=计划[0:10]+[90:106]，解锁=
   充分性证据；fixed 摘除同步网级门场景源 ctx.fixed——两类口径一致）。
3. 宽度探针（(c) 判别）：0.25/0.2 直传完整阶梯（诊断性降带值）。
4. 终判（冻结）：routes 类摘除解锁→(b) 引擎；fixed 类摘除解锁且 routes
   仍锁→(a) 板固有；仅宽度规则面解锁→(c) 带值；均未命中→undetermined
   （证据不足，保守不归类、只披露）。
"""
import argparse
import copy
import io
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import v5.executor as EX  # noqa: E402
from v5.board import load_board  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import _Context, _run_attempt_ladder, _ripup_retry  # noqa: E402
from v5.executor import _resolve_width, _exhaustion_cause, _validate_candidate  # noqa: E402
from v5.executor import (_edge_sequences, _fixed_shape_entry,  # noqa: E402
                         _run_net_ladder)
from v5.measure import polyline_length  # noqa: E402
from v5.metrics import clearance  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.route_check import (FIXED_CID_PREFIX, ROUTE_CID_PREFIX,  # noqa: E402
                            _BoardView)

TOOL_VERSION = "v5.diag_inherent/1.1.1"
GEOM2_MARK = " geom-secondary="
# 0.9.0-only 单行标记（SC-1 短路披露行族；0.8.0 存档面对账剔除项，
# PREREG-DIAG-REPLAY-R1 §3.2——短路主链五行不在此列：整路行集属语义分歧）
V090_ONLY_MARKS = (" preflight-seal-survey:", " preflight-seal-abstain:")
SC_CAUSE_PREFIX = "sealed-short-circuit"
DEFAULT_BOARDS_ROOT = os.path.join(ROOT, "out", "v5-p5", "boards")
DEFAULT_PITCHES = (0.25, 0.125, 0.0625)
WIDTH_PROBE_MMS = (0.25, 0.2)
# 类摘除缩减阶梯（与诊断批同式：引擎阶梯确定性前缀+细档窗口段）
_REDUCED_LADDER_SLICES = ((0, 10), (90, 106))


def jload(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def jdump(path, obj):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


# ---------------------------------------------------------------- 忠实重放
# （execute_candidate 主环镜像：引擎私有件原样调用；1.1.0 对齐 0.9.0 主环=
#  SC-1 事前短路（入口、任何阶梯之前）+0.8.0 多端网 Steiner 边序
#  （_edge_sequences/_run_net_ladder/MST 回退）+0.6.1 geom-secondary 披露行
#  ——镜像同步，保证重放与现役引擎逐字节同形）

def _short_circuit_capture(ctx, view, route_order, layer_assignment,
                           negotiation_log):
    """SC-1 短路终态捕获态构造（1.1.0）：executor 0.9.0 _preflight_seal_
    shortcircuit 返回 FAILED 短路 dict 时，从 _seal_survey_rows 复取首命中
    密封行（partition/net/端点/密封 cids），以「密封端点×分区另端」为
    witness 试点构造 capture（类摘除/宽度探针在此捕获态上运行；cause 取
    短路证据链 exhaustion-cause 行原文，与引擎行集同源）。"""
    rows = EX._seal_survey_rows(ctx, route_order)
    hit = next(r for r in rows if r["sealed"])
    pid = hit["partition"]
    ends = EX._dedup_endpoints(
        view.partitions[pid]["geometry"]["endpoints"])
    idx = hit["endpoint_index"]
    a_pt = (float(hit["endpoint"][0]), float(hit["endpoint"][1]))
    b_raw = ends[(idx + 1) % len(ends)] if len(ends) >= 2 else ends[0]
    b_pt = (float(b_raw[0]), float(b_raw[1]))
    cause = None
    for line in negotiation_log:
        if " exhaustion-cause=" in line:
            cause = line.split(" exhaustion-cause=", 1)[1]
            break
    return {
        "ctx": ctx, "pid": pid, "net_id": hit["net"], "width": hit["width"],
        "a_pt": a_pt, "b_pt": b_pt, "layer": layer_assignment[pid],
        "attempts": 0,
        "cause": cause or (SC_CAUSE_PREFIX + "（全层异网固定铜密封构造性无解，"
                                          "事前短路类）"),
        "n_committed": len(ctx.route_coppers), "short_circuit": True,
        "sealed_endpoint_index": idx,
        "attachment_points": hit["n_points"],
        "sealing_cids": list(hit["sealing_cids"]),
        "route_order": list(route_order)}


def replay_capture(board, candidate):
    view = _BoardView(board)
    route_order, layer_assignment = _validate_candidate(board, candidate)
    ctx = _Context(board)
    negotiation_log = []
    # 0.9.0 SC-1 事前短路（任何阶梯之前；非密封板零 log 增量——与 0.8.0
    # 主环逐字节相等的锚语义）
    short = EX._preflight_seal_shortcircuit(ctx, route_order, negotiation_log)
    if short is not None:
        capture = _short_circuit_capture(ctx, view, route_order,
                                         layer_assignment, negotiation_log)
        return {"verdict": "FAILED", "per_net": short["per_net"],
                "negotiation_log": negotiation_log, "capture": capture,
                "short_circuit": True}
    per_net = []
    failed = False
    exec_of = {}            # 0.8.0+ 5 槽执行参数账（rip-up 原序重布用）
    budget = {"total": 0}   # 候选级全局 rip-up 轮数账
    capture = None

    for pid in route_order:
        partition = view.partitions[pid]
        if view.ribbon_partition(pid) or view.fixed_partition(pid):
            entry, kind = _fixed_shape_entry(view, partition, pid)
            if entry is None:
                negotiation_log.append(
                    "partition=%s fixed-shape failed: %s" % (pid, kind))
                per_net.append({"partition_id": pid,
                                "net_id": view.net_of.get(pid, pid),
                                "status": "failed", "attempts": 0})
                failed = True
                break
            ctx.entries.append(entry)
            negotiation_log.append(
                "partition=%s committed fixed-shape (%s)" % (pid, kind))
            per_net.append({"partition_id": pid, "net_id": entry["net_id"],
                            "status": kind, "attempts": 0})
            continue
        ends = partition["geometry"]["endpoints"]
        uniq_ends = EX._dedup_endpoints(ends)
        if len(uniq_ends) <= 1:
            layer = layer_assignment[pid]
            width0 = float(partition.get("planned_width", 0.2))
            pt0 = [float(ends[0][0]), float(ends[0][1])]
            nets0 = view.nets_by_partition.get(pid) or [view.net_of.get(pid, pid)]
            for net_id in nets0:
                ctx.entries.append({
                    "partition_id": pid, "net_id": net_id, "layer": layer,
                    "polyline": [list(pt0), list(pt0)], "width": width0,
                    "transition_vias": [], "return_vias": []})
                negotiation_log.append(
                    "net=%s partition=%s degenerate: zero-length partition "
                    "trivially satisfied" % (net_id, pid))
                per_net.append({"partition_id": pid, "net_id": net_id,
                                "status": "degenerate", "attempts": 0})
            continue
        nets = view.nets_by_partition.get(pid) or [view.net_of.get(pid, pid)]
        width = _resolve_width(view, partition, pid)
        edges_seq, mst_seq, edge_fail = _edge_sequences(view, pid, partition)
        if edge_fail is not None:
            raise EX.ExecutorError("partitions.%s.geometry" % pid, edge_fail)
        a_pt = ends[0]
        b_pt = ends[1]
        for net_id in nets:
            committed, attempts, reason, entries, vias_n, fail_ab = \
                _run_net_ladder(ctx, pid, net_id, width, edges_seq,
                                layer_assignment[pid], negotiation_log)
            ripup_cause = None
            active_edges = edges_seq
            if not committed and mst_seq is not None:
                negotiation_log.append(
                    "net=%s partition=%s topology-fallback-mst: topology "
                    "edges exhausted, retrying with MST edge order (%d edges)"
                    % (net_id, pid, len(mst_seq)))
                committed, m_att, reason, entries, vias_n, fail_ab = \
                    _run_net_ladder(ctx, pid, net_id, width, mst_seq,
                                    layer_assignment[pid], negotiation_log)
                attempts += m_att
                active_edges = mst_seq
            if not committed:
                fb = fail_ab or (a_pt, b_pt)
                info, ripup_cause, n_extra = _ripup_retry(
                    ctx, pid, net_id, width, fb[0], fb[1],
                    layer_assignment[pid], negotiation_log, exec_of, budget,
                    None,
                    edges_seq=active_edges if len(active_edges) > 1 else None)
                attempts += n_extra
                if info is not None:
                    attempts, vias_n, entries, _rerouted = info
                    committed = True
                    negotiation_log.append(
                        "net=%s partition=%s committed via ripup: total "
                        "attempts=%d" % (net_id, pid, attempts))
            if committed:
                exec_of[net_id] = (pid, width,
                                   active_edges if len(active_edges) > 1
                                   else None,
                                   fail_ab or (a_pt, b_pt),
                                   layer_assignment[pid])
                per_net.append({"partition_id": pid, "net_id": net_id,
                                "status": "routed", "attempts": attempts})
                continue
            fb = fail_ab or (a_pt, b_pt)
            negotiation_log.append(
                "net=%s partition=%s FAILED after %d attempts: %s"
                % (net_id, pid, attempts, reason))
            cause = ripup_cause
            if cause is None:
                cause = _exhaustion_cause(ctx, pid, net_id, width, fb[0], fb[1])
            negotiation_log.append(
                "net=%s partition=%s exhaustion-cause=%s" % (net_id, pid, cause))
            negotiation_log.append(
                "net=%s partition=%s geom-secondary=%s"
                % (net_id, pid,
                   EX._geom_secondary_attr(ctx, pid, net_id, width,
                                           fb[0], fb[1])))
            capture = {
                "ctx": ctx, "pid": pid, "net_id": net_id, "width": width,
                "a_pt": (float(fb[0][0]), float(fb[0][1])),
                "b_pt": (float(fb[1][0]), float(fb[1][1])),
                "layer": layer_assignment[pid], "attempts": attempts,
                "cause": cause, "n_committed": len(ctx.route_coppers)}
            per_net.append({"partition_id": pid, "net_id": net_id,
                            "status": "failed", "attempts": attempts})
            failed = True
            break
        if failed:
            break
    return {"verdict": "FAILED" if failed else "ROUTED",
            "per_net": per_net, "negotiation_log": negotiation_log,
            "capture": capture, "short_circuit": False}


def strip_geom2(log):
    return [l for l in log if GEOM2_MARK not in l]


def strip_v090_only(log):
    """0.9.0-only 单行剔除（0.8.0 存档面对账容差；PREREG §3.2）：仅
    preflight-seal-survey/abstain 披露单行——短路主链（FAILED/exhaustion-
    cause/geom-secondary/basis 四行）不剔：整路短路与 0.8.0 阶梯体互不可
    strip，属语义分歧须如实报 MISMATCH。"""
    return [l for l in log if not any(m in l for m in V090_ONLY_MARKS)]


def detect_execute_face(ex_doc):
    """execute.json 版本面定面（消费面推断链，PREREG §2.2/§3；execute.json
    不内嵌 executor 版本字段）：0.9.0 主锚面标记=顶层 verdict_provenance 在
    （exec-eng-r1.runner 落键）或 log 含 preflight-seal 行；否则=0.8.0 存档
    面。返回 (face, markers)。"""
    log = ex_doc.get("execute", {}).get("negotiation_log") or []
    has_prov = ("verdict_provenance" in ex_doc)
    has_sc_row = any((" preflight-seal-survey:" in l)
                     or (" short-circuit-basis:" in l) for l in log)
    markers = {"verdict_provenance_top": has_prov,
               "short_circuit_row": has_sc_row,
               "generator": (ex_doc.get("provenance") or {}).get("generator")}
    if has_prov or has_sc_row:
        return "0.9.0-main", markers
    return "0.8.0-archive", markers


# ---------------------------------------------------------------- witness

def _ob_point_distance(ob, p):
    return ob.distance_to(p, p)


def _closest_point_on_ob(ob, p):
    cu = ob.cu
    if cu.pad is not None:
        return cu.pad[0]
    if cu.band is not None:
        x0, y0, x1, y1 = cu.band
        return (min(max(p[0], x0), x1), min(max(p[1], y0), y1))
    best, bd = None, float("inf")
    for a, b in zip(cu.polyline[:-1], cu.polyline[1:]):
        ax, ay = float(a[0]), float(a[1])
        bx, by = float(b[0]), float(b[1])
        dx, dy = bx - ax, by - ay
        t = 0.0 if (dx == 0 and dy == 0) else max(
            0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy)
                     / (dx * dx + dy * dy)))
        q = (ax + t * dx, ay + t * dy)
        d = clearance.point_point(p, q)
        if d < bd:
            best, bd = q, d
    return best


def _ring_reasons(ctx, pid, net_id, width, center_pt, pitch):
    """端点吸附节点邻域出边封死普查（带原因标记）：r0=吸附节点自身出边/换层
    边，r1=八向 1 格逃逸锚节点的出边（与 executor geom-secondary 普查同构，
    本件保留逐原因直方图与多档 pitch——witness 摘要用）。"""
    view = ctx.view
    layers = list(view.signal_layers)
    x0, y0, x1, y1 = view.workspace
    ix = int(round((center_pt[0] - x0) / pitch))
    iy = int(round((center_pt[1] - y0) / pitch))
    out = []

    def probe_node(rtag, jx, jy):
        pt = (x0 + jx * pitch, y0 + jy * pitch)
        if not (x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1):
            return
        for li, layer in enumerate(layers):
            for dx, dy in EX._DIRS8:
                q = (pt[0] + dx * pitch, pt[1] + dy * pitch)
                if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
                    continue
                r = ctx.edge_blocked(layer, pt, q, net_id, pid, width)
                out.append((rtag, layer, (dx, dy), r))
            for lj in range(len(layers)):
                if lj != li:
                    r = ctx.edge_blocked(layers[lj], pt, pt, net_id, pid, width)
                    out.append((rtag + "-via", layers[lj], (0, 0), r))

    probe_node("r0", ix, iy)
    for dx, dy in EX._DIRS8:
        probe_node("r1", ix + dx, iy + dy)
    hist = {}
    n_open = 0
    for _r, _l, _d, reason in out:
        hist[reason] = hist.get(reason, 0) + 1
        if reason is None:
            n_open += 1
    return {"n_edges": len(out), "n_open": n_open,
            "reasons": {str(k): v for k, v in sorted(
                hist.items(), key=lambda kv: (-kv[1], str(kv[0])))}}


def _channel_scan(ctx, net_id, a_pt, b_pt, r5, n_samples=41):
    """直连走廊最窄通道普查（中心线口径：min(d_left+d_right) vs 需求 2×R5）。"""
    layers = list(ctx.view.signal_layers)
    dx, dy = b_pt[0] - a_pt[0], b_pt[1] - a_pt[1]
    L = math.hypot(dx, dy) or 1e-9
    nx, ny = -dy / L, dx / L
    per_layer = {}
    for layer in layers:
        obs = [ob for ob in ctx.obstacles
               if ob.cu.layer == layer and ob.cu.net_id != net_id]
        if not obs:
            per_layer[layer] = None
            continue
        worst = None
        for k in range(n_samples):
            t = k / float(n_samples - 1)
            p = (a_pt[0] + dx * t, a_pt[1] + dy * t)
            d_left = d_right = float("inf")
            cl = cr = None
            for ob in obs:
                d = _ob_point_distance(ob, p)
                if d > 2.0:
                    continue
                cp = _closest_point_on_ob(ob, p)
                side = (cp[0] - p[0]) * nx + (cp[1] - p[1]) * ny
                if side < 0 and d < d_left:
                    d_left, cl = d, ob
                elif side > 0 and d < d_right:
                    d_right, cr = d, ob
            if d_left + d_right != float("inf"):
                gap = d_left + d_right
                if worst is None or gap < worst[0]:
                    worst = (gap, round(t, 4), round(d_left, 4),
                             round(d_right, 4),
                             cl.cu.cid if cl else None,
                             cr.cu.cid if cr else None)
        per_layer[layer] = worst
    return {"demand_2r5": 2.0 * r5, "per_layer": per_layer}


def _direct_blocker_census(ctx, pid, net_id, width, a_pt, b_pt):
    """失败区阻塞普查（引擎口径）：直连段带与端点逃逸邻域盘内各类障碍计数。"""
    view = ctx.view
    r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
    reach = EX._RIPUP_ESCAPE_REACH_MM
    corr_hw = width / 2.0 + r5
    disc = reach + r5
    route_nets, fixed_n, via_n = {}, 0, 0
    for ob in ctx.obstacles:
        cu = ob.cu
        if cu.net_id == net_id:
            continue
        d_seg = ob.distance_to(a_pt, b_pt)
        d_eps = min(_ob_point_distance(ob, a_pt), _ob_point_distance(ob, b_pt))
        if not ((d_seg < corr_hw) or (d_eps < disc)):
            continue
        if cu.cid.startswith(ROUTE_CID_PREFIX):
            key = cu.net_id
            route_nets.setdefault(key, {"n_coppers": 0, "min_d_direct": 9e9})
            route_nets[key]["n_coppers"] += 1
            route_nets[key]["min_d_direct"] = min(
                route_nets[key]["min_d_direct"], round(d_seg, 4))
        elif cu.cid.startswith(FIXED_CID_PREFIX):
            fixed_n += 1
    for vnet, _vpid, vpt in ctx.via_points:
        if vnet == net_id:
            continue
        if clearance.pad_segment_distance(
                vpt, float(view.via_radius), a_pt, b_pt) < r5 - clearance.EPS \
                or min(clearance.point_point(vpt, a_pt),
                       clearance.point_point(vpt, b_pt)) < disc:
            via_n += 1
    holes_hit = []
    eps_pts = ctx._pid_endpoints.get(pid)
    for hx, hy, hr in ctx.holes:
        if eps_pts is not None and (
                (abs(hx - eps_pts[0][0]) <= 1e-9
                 and abs(hy - eps_pts[0][1]) <= 1e-9)
                or (abs(hx - eps_pts[1][0]) <= 1e-9
                    and abs(hy - eps_pts[1][1]) <= 1e-9)):
            continue
        if EX.hole_track_blocked((hx, hy), hr, a_pt, b_pt, width / 2.0):
            holes_hit.append([round(hx, 3), round(hy, 3), round(hr, 3)])
    engine_blockers = EX._ripup_blocker_ids(ctx, net_id, width, a_pt, b_pt,
                                            reach)
    return {"r5": r5, "route_blocker_nets": route_nets,
            "fixed_coppers_in_zone": fixed_n,
            "other_via_points_in_zone": via_n,
            "holes_blocking_direct": holes_hit,
            "engine_ripup_blocker_set": engine_blockers}


def _net_ladder(ctx, pid, net_id, width, a_pt, b_pt, layer, plans=None):
    log = []
    ok, att, reason, _e, _v = _run_attempt_ladder(
        ctx, pid, net_id, width, a_pt, b_pt, layer, log, plans=plans)
    return ok, att, reason


def _class_removal_unlock(ctx, cap, klass, plans):
    """阻塞类摘除解锁测试（梯面试点口径）：ctx 快照→摘类→单网阶梯→恢复。
    fixed 类同时摘 A* 栅格（ctx.obstacles）与网级门场景源（ctx.fixed）——
    只摘栅格会被 _net_gate 的 R5 复核抓回，两类口径须一致（诊断批 stm32
    实测）。1.1.1 修复：holes/edge 摘除后还原（1.0.0 起泄漏进后续宽度
    探针）+ 空间粗网格随 holes 集变更失效（_gen 递增——1.0.0 起 holes
    摘除在引擎谓词面实际无效：gh 网格滞留旧孔集）。"""
    net_id, pid, width = cap["net_id"], cap["pid"], cap["width"]
    a_pt, b_pt, layer = cap["a_pt"], cap["b_pt"], cap["layer"]
    snap = ctx.snapshot()
    saved_fixed = list(ctx.fixed)
    saved_holes = ctx.holes
    saved_edge_inner = ctx.edge_inner
    try:
        if klass == "routes":
            ctx.obstacles = [ob for ob in ctx.obstacles if not (
                ob.cu.cid.startswith(ROUTE_CID_PREFIX)
                and ob.cu.net_id != net_id)]
            ctx.route_coppers = [cu for cu in ctx.route_coppers
                                 if cu.net_id == net_id]
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == net_id]
            ctx._rebuild_ledger()
            ctx._gen += 1
        elif klass == "vias":
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == net_id]
            ctx._gen += 1
        elif klass == "holes":
            ctx.holes = []
            ctx._gen += 1   # gh 网格失效（孔集变更）
        elif klass == "edge":
            x0, y0, x1, y1 = ctx.view.workspace
            ctx.edge_inner = (x0, y0, x1, y1)
        elif klass == "fixed":
            ctx.obstacles = [ob for ob in ctx.obstacles
                             if not ob.cu.cid.startswith(FIXED_CID_PREFIX)]
            ctx.fixed = [cu for cu in ctx.fixed
                         if not cu.cid.startswith(FIXED_CID_PREFIX)]
            ctx._rebuild_ledger()
            ctx._gen += 1
        elif klass == "all-geometric":
            ctx.obstacles = [ob for ob in ctx.obstacles
                             if ob.cu.net_id == net_id]
            ctx.route_coppers = [cu for cu in ctx.route_coppers
                                 if cu.net_id == net_id]
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == net_id]
            ctx.holes = []
            ctx.fixed = []
            x0, y0, x1, y1 = ctx.view.workspace
            ctx.edge_inner = (x0, y0, x1, y1)
            ctx._rebuild_ledger()
            ctx._gen += 1
        else:
            raise ValueError("unknown class: %s" % klass)
        ok, att, reason = _net_ladder(ctx, pid, net_id, width, a_pt, b_pt,
                                      layer, plans=plans)
        return {"class": klass, "unlocked": bool(ok),
                "attempts": att, "reason": reason}
    finally:
        ctx.restore(snap)
        ctx.fixed = saved_fixed
        if ctx.holes is not saved_holes:
            ctx.holes = saved_holes
            ctx._gen += 1
        ctx.edge_inner = saved_edge_inner


_SEAL_CLASSES = ("routes", "vias", "holes", "edge", "fixed", "all-geometric")


def _seal_removal_unlock(ctx, cap, klass):
    """SC-1 短路捕获态类摘除解锁测试（**密封域**口径，1.1.1）：封锁事实
    =端点附着闭包 S(e) 全层被固定铜 R5 封死（exec-eng-r1 DESIGN §1.5 谓
    词=_seal_survey_rows，只计 fixed: 前缀铜）——「解锁」=摘类后复跑密封
    普查、该端点 S(e) 不再全封。梯面试点口径在短路捕获态会混入另端无关
    阻断（syn-u02 另端在 keepout 内：六类梯面摘除均耗尽→误报
    undetermined），密封域口径直接度量封锁事实本身；routes/vias/holes/
    edge 类在普查谓词面外（fixed-only 判定世界，单调性见 executor
    docstring W-1 节）——仍实测复跑（如实落 sealed 读数）。"""
    pid, idx = cap["pid"], cap["sealed_endpoint_index"]
    snap = ctx.snapshot()
    saved_fixed = list(ctx.fixed)
    saved_holes = ctx.holes
    saved_edge_inner = ctx.edge_inner
    try:
        if klass == "routes":
            ctx.obstacles = [ob for ob in ctx.obstacles if not (
                ob.cu.cid.startswith(ROUTE_CID_PREFIX)
                and ob.cu.net_id != cap["net_id"])]
            ctx.route_coppers = [cu for cu in ctx.route_coppers
                                 if cu.net_id == cap["net_id"]]
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == cap["net_id"]]
            ctx._rebuild_ledger()
            ctx._gen += 1
        elif klass == "vias":
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == cap["net_id"]]
            ctx._gen += 1
        elif klass == "holes":
            ctx.holes = []
            ctx._gen += 1
        elif klass == "edge":
            x0, y0, x1, y1 = ctx.view.workspace
            ctx.edge_inner = (x0, y0, x1, y1)
        elif klass == "fixed":
            ctx.obstacles = [ob for ob in ctx.obstacles
                             if not ob.cu.cid.startswith(FIXED_CID_PREFIX)]
            ctx.fixed = [cu for cu in ctx.fixed
                         if not cu.cid.startswith(FIXED_CID_PREFIX)]
            ctx._rebuild_ledger()
            ctx._gen += 1
        elif klass == "all-geometric":
            ctx.obstacles = [ob for ob in ctx.obstacles
                             if ob.cu.net_id == cap["net_id"]]
            ctx.route_coppers = [cu for cu in ctx.route_coppers
                                 if cu.net_id == cap["net_id"]]
            ctx.via_points = [vp for vp in ctx.via_points
                              if vp[0] == cap["net_id"]]
            ctx.holes = []
            ctx.fixed = []
            x0, y0, x1, y1 = ctx.view.workspace
            ctx.edge_inner = (x0, y0, x1, y1)
            ctx._rebuild_ledger()
            ctx._gen += 1
        else:
            raise ValueError("unknown class: %s" % klass)
        rows = EX._seal_survey_rows(ctx, cap["route_order"])
        row = next((r for r in rows
                    if r["partition"] == pid
                    and r["endpoint_index"] == idx), None)
        if row is None:
            return {"class": klass, "unlocked": False, "attempts": 0,
                    "reason": "seal-survey: 普查行缺失（分区/端点不匹配）"}
        reading = "S(e) sealed_pairs=%d/%d" % (row["sealed_pairs"],
                                               row["n_pairs"])
        return {"class": klass, "unlocked": not row["sealed"],
                "attempts": 0,
                "reason": ("seal-survey: %s→%s" % (
                    reading, "仍全封" if row["sealed"] else "解封"))}
    finally:
        ctx.restore(snap)
        ctx.fixed = saved_fixed
        if ctx.holes is not saved_holes:
            ctx.holes = saved_holes
            ctx._gen += 1
        ctx.edge_inner = saved_edge_inner


def analyze_witness(ctx, cap, pitches):
    view = ctx.view
    pid, net_id, width = cap["pid"], cap["net_id"], cap["width"]
    a_pt, b_pt = cap["a_pt"], cap["b_pt"]
    partition = view.partitions[pid]
    r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
    pads = view.pad_items.get(pid, ())
    endpoint_geo = {
        "endpoints": [[round(a_pt[0], 4), round(a_pt[1], 4)],
                      [round(b_pt[0], 4), round(b_pt[1], 4)]],
        "direct_len_mm": round(clearance.point_point(a_pt, b_pt), 4),
        "pad_terminals": [
            {"endpoint": it["endpoint"], "layers": it.get("pad_layers"),
             "shape": it.get("shape"), "size_mm": it.get("size"),
             "max_half_mm": round(max(float(s) for s in it["size"]) / 2.0, 4),
             "through_hole": it.get("through_hole")}
            for it in pads],
        "width_mm": width,
        "width_prior": partition.get("width_prior"),
        "planned_width_in_board": partition.get("planned_width", 0.2),
        "current_a": partition.get("current_a"),
    }
    ix0, iy0, ix1, iy1 = ctx.edge_inner
    endpoint_geo["endpoint_in_edge_band"] = [
        not (ix0 <= p[0] <= ix1 and iy0 <= p[1] <= iy1) for p in (a_pt, b_pt)]
    sealing = {"start": {}, "goal": {}}
    for pitch in pitches:
        sealing["start"]["pitch_%g" % pitch] = _ring_reasons(
            ctx, pid, net_id, width, a_pt, pitch)
        sealing["goal"]["pitch_%g" % pitch] = _ring_reasons(
            ctx, pid, net_id, width, b_pt, pitch)
    census = _direct_blocker_census(ctx, pid, net_id, width, a_pt, b_pt)
    channel = _channel_scan(ctx, net_id, a_pt, b_pt, r5)
    plans = list(EX._attempt_plans())
    reduced = []
    for lo, hi in _REDUCED_LADDER_SLICES:
        reduced.extend(plans[lo:hi])
    removal = []
    for klass in ("routes", "vias", "holes", "edge", "fixed", "all-geometric"):
        t0 = time.time()
        if cap.get("short_circuit"):
            row = _seal_removal_unlock(ctx, cap, klass)   # 密封域口径（1.1.1）
        else:
            row = _class_removal_unlock(ctx, cap, klass, reduced)
        row["wall_s"] = round(time.time() - t0, 1)
        removal.append(row)
    ladder_rows = None
    if cap.get("short_circuit"):
        # 梯面试点六行降为诊断披露（短路捕获态另端无关阻断混入面；不参与
        # 终判——class_removal_unlock=密封域口径）。计划面=基线 5 变体
        # （keepout/板边带等不可达混入在前几次尝试即定局；fixed/all-geometric
        # 摘除打开搜索空间后全空间耗尽 ~70s/类——诊断披露不减证据只减墙钟）
        ladder_rows = []
        for klass in _SEAL_CLASSES:
            t0 = time.time()
            row = _class_removal_unlock(ctx, cap, klass, reduced[:5])
            row["wall_s"] = round(time.time() - t0, 1)
            ladder_rows.append(row)
    order = ("routes", "vias", "holes", "edge", "fixed", "all-geometric")
    minimal = next((k for k in order
                    if any(r["class"] == k and r["unlocked"]
                           for r in removal)), None)
    out = {"endpoint_geometry": endpoint_geo, "endpoint_sealing": sealing,
           "blocker_census": census, "channel_scan": channel,
           "class_removal_unlock": removal,
           "minimal_removal_class_to_unlock": minimal,
           "removal_ladder_note": ("缩减阶梯=计划%s（基线+细化+0.0625 细档段），"
                                   "解锁判定为充分性证据%s" % (
                                       "+".join("[%d:%d]" % s
                                                for s in _REDUCED_LADDER_SLICES),
                                       "；短路捕获态=密封域口径（摘类→复跑"
                                       " seal-survey 普查→S(e) 解封判）"
                                       if cap.get("short_circuit") else ""))}
    if ladder_rows is not None:
        out["ladder_removal_unlock"] = ladder_rows
        out["ladder_removal_note"] = (
            "梯面试点六行（诊断披露，不参与终判）：短路捕获态下另端无关"
            "阻断（keepout/板边带等非类摘除面）会混入梯面读数——1.1.0 曾"
            "以此口径误报 undetermined（syn-u02），1.1.1 起终判面=密封域")
    if cap.get("short_circuit"):
        out["short_circuit"] = {
            "sealed_endpoint_index": cap["sealed_endpoint_index"],
            "attachment_points": cap["attachment_points"],
            "sealing_cids": cap["sealing_cids"],
            "note": ("SC-1 事前短路捕获态（executor 0.9.0 sealed-short-"
                     "circuit）：类摘除=密封域口径（摘类→复跑 seal-survey"
                     "→S(e) 解封判），宽度探针=密封端点×分区另端梯面试点"
                     "（(c) 判别保留面）")}
    return out


def itemize_fixed(ctx, cap, top=8):
    """固定铜逐项指认（可选段）：失败区内板固有固定铜逐枚 cid/层/距离。"""
    r5 = float(ctx.view.hard_rules.get("R5", {})
               .get("min_clearance_mm", 0.5))
    corr_hw = cap["width"] / 2.0 + r5
    disc = EX._RIPUP_ESCAPE_REACH_MM + r5
    rows = []
    for ob in ctx.obstacles:
        cu = ob.cu
        if cu.net_id == cap["net_id"] or not cu.cid.startswith(
                FIXED_CID_PREFIX):
            continue
        d_seg = ob.distance_to(cap["a_pt"], cap["b_pt"])
        d_eps = min(_ob_point_distance(ob, cap["a_pt"]),
                    _ob_point_distance(ob, cap["b_pt"]))
        if d_seg < corr_hw or d_eps < disc:
            rows.append({"cid": cu.cid, "layer": cu.layer,
                         "d_direct": round(d_seg, 3),
                         "d_endpoint_min": round(d_eps, 3),
                         "kind": ("pad" if cu.pad is not None else
                                  ("band" if cu.band is not None else "poly"))})
    rows.sort(key=lambda r: min(r["d_direct"], r["d_endpoint_min"]))
    return {"n_fixed_in_zone": len(rows), "nearest_fixed": rows[:top]}


# ---------------------------------------------------------------- 宽度探针

def run_width_probes(ctx, cap, width_mms=WIDTH_PROBE_MMS):
    """>(c) 判别宽度探针：快照恢复→降 width→完整阶梯（诊断性，不宣称）。"""
    snap = ctx.snapshot()
    probes = []
    try:
        for w in width_mms:
            t0 = time.time()
            log = []
            ok, att, reason, _e, _v = _run_attempt_ladder(
                ctx, cap["pid"], cap["net_id"], w, cap["a_pt"], cap["b_pt"],
                cap["layer"], log)
            probes.append({"width_mm": w, "unlocked": bool(ok),
                           "attempts": att, "reason": reason,
                           "wall_s": round(time.time() - t0, 1)})
    finally:
        ctx.restore(snap)
    return probes


# ---------------------------------------------------------------- 终判（冻结）

FROZEN_CRITERIA = ("(b) routes 类摘除解锁→引擎；(a) fixed 类摘除解锁且 routes "
                   "仍锁→板固有；(c) 仅宽度规则面解锁→带值；均未命中→"
                   "undetermined（保守不归类，只披露）")


def classify(witness, width_probes):
    removal = {r["class"]: r["unlocked"] for r in
               witness["class_removal_unlock"]}
    width_unlock = [p["width_mm"] for p in width_probes if p.get("unlocked")]
    if removal.get("routes"):
        cls, note = ("(b) 引擎能力缺口",
                     "routes 类摘除即解锁（冻结判据）：摘他网已布铜可布——"
                     "rip-up 阻塞集选择/联合重解深度面（不宣称现有放松可解）")
    elif removal.get("fixed"):
        cls, note = ("(a) 板设计固有不可布",
                     "fixed 类摘除解锁且 routes 类摘除仍锁（冻结判据命中）："
                     "封死面=板固有固定铜（焊盘场）")
    elif width_unlock and not removal.get("all-geometric"):
        cls, note = ("(c) 规则带值瓶颈",
                     "仅宽度规则面解锁（冻结判据）：width_mm=%s（诊断性降带值）"
                     % "、".join(str(w) for w in width_unlock))
    else:
        cls, note = ("undetermined（证据不足）",
                     "冻结三分类均未命中（各类摘除与宽度探针均未解锁）——"
                     "保守不归类，仅披露 witness")
    return {"class": cls, "note": note, "frozen_criteria": FROZEN_CRITERIA,
            "removal_unlock_classes": sorted(
                k for k, v in removal.items() if v),
            "width_unlock_mm": width_unlock}


# ---------------------------------------------------------------- 主流程

def diagnose(board_json, execute_json, board_name=None,
             pitches=DEFAULT_PITCHES, skip_width=False, itemize=False,
             expect_net=None):
    t0 = time.time()
    with io.open(board_json, encoding="utf-8") as f:
        _bdoc = json.load(f)
    # wrap 容差（1.1.0）：真实板 wrap 文档（顶层 {adapter_report, board,
    # provenance}）取 doc["board"] 裸化；合成板裸文档直读
    bd = load_board(_bdoc["board"] if isinstance(_bdoc, dict)
                    and "board" in _bdoc else _bdoc)
    ex_doc = jload(execute_json)
    face, face_markers = detect_execute_face(ex_doc)
    last_idx = ex_doc["tried_candidates"][-1]["index"]
    _c_art, _fp = compile_board(bd)
    cands = plan_candidates(bd, _c_art, arm="principle")
    cand = copy.deepcopy(cands[last_idx])
    t1 = time.time()
    rep = replay_capture(bd, cand)
    replay_wall = time.time() - t1
    recorded = ex_doc["execute"]["negotiation_log"]
    mine = rep["negotiation_log"]
    n_geom2 = sum(1 for l in mine if GEOM2_MARK in l)
    n_v090 = sum(1 for l in mine if any(m in l for m in V090_ONLY_MARKS))
    # 对账（1.1.0 双面）：
    #   raw=逐字节等；mod=双侧剔除 log-only/单行披露行后等（0.6.1 geom-
    #   secondary 行两侧同剔=0.6.0 档案容差沿用；0.8.0 存档面另剔 0.9.0-only
    #   单行——短路主链不剔，整路短路与 0.8.0 阶梯体互不可 strip）
    faithful_raw = (mine == recorded)
    mine_mod = strip_geom2(mine)
    rec_mod = strip_geom2(recorded)
    basis_mod = "equal-mod-geom-secondary（0.6.1 log-only 行）"
    if face == "0.8.0-archive":
        mine_mod = strip_v090_only(mine_mod)
        rec_mod = strip_v090_only(rec_mod)
        basis_mod = ("equal-mod-geom-secondary+v090-only-rows（0.6.1 "
                     "log-only 行+0.9.0 短路披露单行不入 0.8.0 对账集）")
    faithful_mod = (mine_mod == rec_mod)
    # verdict_provenance 出口读数对账（0.9.0 面；0.8.0 档案无此键=不计数）
    recorded_prov = ex_doc.get("verdict_provenance")
    sel = ex_doc.get("selection_verdict")
    mine_prov = EX._verdict_provenance(
        rep["verdict"], sel,
        short_circuit=bool(rep.get("short_circuit"))) if sel is not None \
        else None
    prov_match = (None if recorded_prov is None
                  else bool(recorded_prov == mine_prov))
    faithful = bool((faithful_raw or faithful_mod)
                    and prov_match is not False)
    replay = {
        "verdict": rep["verdict"],
        "execute_face": face,
        "execute_face_markers": face_markers,
        "short_circuit_replay": bool(rep.get("short_circuit")),
        "faithful": faithful,
        "faithful_raw_byte_equal": bool(faithful_raw),
        "faithful_basis": ("byte-equal" if faithful_raw else
                           (basis_mod if faithful_mod else "MISMATCH")),
        "verdict_provenance_recorded": recorded_prov,
        "verdict_provenance_replay": mine_prov,
        "verdict_provenance_match": prov_match,
        "n_log_lines": len(mine), "n_recorded_lines": len(recorded),
        "n_geom_secondary_lines": n_geom2,
        "n_v090_only_lines": n_v090,
        "n_candidates": len(cands), "base_candidate_index": last_idx,
        "wall_s": round(replay_wall, 1)}
    if rep["verdict"] != "FAILED" or rep["capture"] is None:
        replay["note"] = ("重放未复现失败（verdict=%s）——本工具面向 FAILED 板"
                          % rep["verdict"])
        return {"tool": TOOL_VERSION, "engine_version": EX.EXECUTOR_VERSION,
                "board": board_name or board_json,
                "replay": replay, "witness": None, "verdict": None,
                "disclosure": "只读诊断，不产生记分牌主张",
                "wall_s": round(time.time() - t0, 1)}, 2
    if not replay["faithful"]:
        first_div = next((("%d: 重放=%s / 档案=%s" % (i, a, b))
                          for i, (a, b) in enumerate(zip(mine_mod, rec_mod))
                          if a != b), None)
        replay["note"] = ("重放 negotiation_log 与 execute.json 不一致"
                          "（len %d vs %d%s）——合同缺口，不分类"
                          % (len(mine), len(recorded),
                             ("；首分歧 " + first_div) if first_div
                             else "（长度差）"))
        return {"tool": TOOL_VERSION, "engine_version": EX.EXECUTOR_VERSION,
                "board": board_name or board_json,
                "replay": replay, "witness": None, "verdict": None,
                "disclosure": "只读诊断，不产生记分牌主张",
                "wall_s": round(time.time() - t0, 1)}, 3
    cap = rep["capture"]
    ctx = cap["ctx"]
    if expect_net is not None and cap["net_id"] != expect_net:
        return {"tool": TOOL_VERSION, "engine_version": EX.EXECUTOR_VERSION,
                "board": board_name or board_json, "replay": replay,
                "witness": None, "verdict": None,
                "error": "失败网不符：%s vs 预期 %s" % (cap["net_id"],
                                                      expect_net),
                "disclosure": "只读诊断，不产生记分牌主张",
                "wall_s": round(time.time() - t0, 1)}, 4
    witness = analyze_witness(ctx, cap, pitches)
    width_probes = ([] if skip_width else run_width_probes(ctx, cap))
    itemized = (itemize_fixed(ctx, cap) if itemize else None)
    verdict = classify(witness, width_probes)
    doc = {
        "tool": TOOL_VERSION,
        "engine_version": EX.EXECUTOR_VERSION,
        "board": board_name or board_json,
        "board_json": os.path.abspath(board_json),
        "execute_json": os.path.abspath(execute_json),
        "replay": replay,
        "failed_net": {"net": cap["net_id"], "partition": cap["pid"],
                       "attempts": cap["attempts"],
                       "exhaustion_cause": cap["cause"],
                       "width_mm": float(cap["width"]),
                       "prefix_committed_coppers": cap["n_committed"]},
        "witness": witness,
        "width_probes": width_probes,
        "itemized_fixed": itemized,
        "verdict": verdict,
        "disclosure": "只读诊断，不产生记分牌主张（解锁/摘除均为诊断性判定）",
        "wall_s": round(time.time() - t0, 1)}
    return doc, 0


def _human_summary(doc):
    L = []
    if doc.get("verdict") is None:
        L.append("重放未成立：%s" % doc["replay"].get("note", ""))
        return "\n".join(L)
    v = doc["verdict"]
    w = doc["witness"]
    L.append("板 %s 引擎 %s" % (doc["board"], doc["engine_version"]))
    L.append("重放：%s（%s；%d 行 log，geom-secondary +%d 行；对象面=%s%s）"
             % (doc["replay"]["verdict"], doc["replay"]["faithful_basis"],
                doc["replay"]["n_log_lines"],
                doc["replay"]["n_geom_secondary_lines"],
                doc["replay"].get("execute_face", "?"),
                "，短路终态" if doc["replay"].get("short_circuit_replay")
                else ""))
    pm = doc["replay"].get("verdict_provenance_match")
    if pm is not None:
        L.append("verdict_provenance 对账：%s（%s）"
                 % ("一致" if pm else "不一致",
                    doc["replay"].get("verdict_provenance_recorded")))
    L.append("失败网：%s（partition=%s，attempts=%d，cause=%s）"
             % (doc["failed_net"]["net"], doc["failed_net"]["partition"],
                doc["failed_net"]["attempts"],
                doc["failed_net"]["exhaustion_cause"]))
    L.append("阻塞类摘除：%s（最小解锁类=%s）"
             % ("/".join("%s=%s" % (r["class"], "解锁" if r["unlocked"]
                                    else "仍锁")
                         for r in w["class_removal_unlock"]),
                w["minimal_removal_class_to_unlock"] or "无"))
    if doc.get("width_probes"):
        L.append("宽度探针：%s" % "/".join(
            "%g=%s" % (p["width_mm"], "解锁(诊断性)" if p["unlocked"]
                       else "仍锁") for p in doc["width_probes"]))
    L.append("终判：%s（%s）" % (v["class"], v["note"]))
    L.append("披露：%s" % doc["disclosure"])
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="「板固有不可布」witness 自动归因器（只读诊断）")
    ap.add_argument("--board", help="板名（--boards-root/<名>/board.json）")
    ap.add_argument("--boards-root", default=DEFAULT_BOARDS_ROOT,
                    help="板树根（默认 out/v5-p5/boards）")
    ap.add_argument("--board-json", help="显式 board.json 路径")
    ap.add_argument("--execute-json", help="显式 execute.json 路径"
                    "（--board-json 时必填）")
    ap.add_argument("--json", default=None,
                    help="机器输出 json 路径（- = stdout）")
    ap.add_argument("--net", default=None, help="预期失败网（核对）")
    ap.add_argument("--itemize-fixed", action="store_true",
                    help="固定铜逐项指认段")
    ap.add_argument("--skip-width-probes", action="store_true",
                    help="跳过 (c) 判别宽度探针")
    ap.add_argument("--pitches", default=",".join(str(p) for p
                                                  in DEFAULT_PITCHES),
                    help="密封普查栅距档（逗号分隔，默认 0.25,0.125,0.0625）")
    args = ap.parse_args(argv)

    if args.board:
        bdir = os.path.join(args.boards_root, args.board)
        board_json = os.path.join(bdir, "board.json")
        execute_json = os.path.join(bdir, "execute.json")
        name = args.board
    elif args.board_json:
        if not args.execute_json:
            ap.error("--board-json 需要 --execute-json")
        board_json = args.board_json
        execute_json = args.execute_json
        name = None
    else:
        ap.error("需要 --board 或 --board-json")
    pitches = tuple(float(p) for p in args.pitches.split(",") if p.strip())

    doc, code = diagnose(board_json, execute_json, board_name=name,
                         pitches=pitches, skip_width=args.skip_width_probes,
                         itemize=args.itemize_fixed, expect_net=args.net)
    print(_human_summary(doc))
    if args.json == "-":
        json.dump(doc, sys.stdout, ensure_ascii=False, indent=1,
                  sort_keys=True)
        sys.stdout.write("\n")
    elif args.json:
        jdump(args.json, doc)
        print("json: %s" % os.path.abspath(args.json))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
