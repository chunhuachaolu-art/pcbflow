"""LIVE2B-S2：3V3 零拆收口尝试 + 布局迭代提案 + 铜扰动账单（纯函数核）。

背景（S1，out/coreboard-live2b-s1）：6 目标网全部 UNSAT(verified)；其中 3V3
RPL-019 的证书只到 corridor scope（[40.4,55.35,46.2,60.45]），板级强化梯
UNKNOWN 且记录了候选通径。LIVE-1（out/coreboard-live-apply1）在 pcbagent
Router 原口径搜索窗（端点 bbox+L3_MARGIN=3mm）下含端点变体均 UNKNOWN。

本模块只放纯函数（零落盘、零子进程、不碰板文件；驱动与 kicad-cli 留编排侧
scripts/live2s2_run.py 与 Bash）：
- 任务 1：搜索窗梯（margin 只是搜索参数——合法性仍由 _try_route 内
  Region/A*+L1 终判裁决，ripup1_campaign._replan_net_excl 同一先例）、同网
  落点枚举（连通分量内 pad/via/走线端）、witness 独立复核账、S1 corridor
  证书一致性核对（witness 必须出走廊窗，否则与 verified 割矛盾）。
- 任务 2：铜扰动账单（被移 ref 各 pad 上有既有走线端点/过孔的清单，逐项
  目标网自身/他网分类）、板文本级移位与剥除（board_writer 同口径）、候选
  微移位生成（锚件永不入候选）、候选排序。

合同红线：SAT 必带 witness（Router plan.ok=L1 终判全过 + 端点落铜）；UNSAT
必须 verify=true 证书；其余 UNKNOWN；禁自动改判；route_grid.py 零改动。
"""

from __future__ import annotations

import math
import re

from . import board_writer

LIVE2S2_SCHEMA = "1.0"
LIVE2S2_ARTIFACT_KIND = "live2s2_closure_and_proposal"
LIVE2S2_DATASET = "coreboard-live2b-s2"
LIVE2S2_DATE = "2026-09-11"

LIVE_BOARD_SHA_PREFIX = "8029f5ff"
PROTECTED = (("pcbflow/config.py", "f515c348"),
             ("toolchain_lock.json", "d43dad89"))

# 锚件（out/revc-a2/structures.json 已批 10 只；keepout_iter/coplace 同源，
# 编排侧开工对账，不符即停）——永不生成移位候选。
ANCHOR_REFS = ("J1", "J2", "J3", "J4", "J5", "U1", "U2", "U6", "Y1", "Y2")

# 任务 1 搜索窗梯（mm）：首项 3.0 = pcbagent C.L3_MARGIN 原口径（route_one
# 等价）；后续只放大搜索窗（搜索参数，非语义变更）。有界：不无限加窗。
CLOSURE_MARGIN_LADDER = (3.0, 5.0, 8.0, 12.0, 20.0)
LANDING_TOP_K = 4              # 同网落点枚举上限（按到 A 距离升序）
LANDING_DEDUP_MM = 0.2

# 任务 2 有界微移位
MOVE_MAX_MM = 2.0
MOVE_MAGNITUDES = (1.0, 2.0)
MAX_CANDIDATES_TOTAL = 5
POCKET_NEAR_MM = 5.0           # 候选 ref = 口袋端点 5mm 内有焊盘的非锚件（放宽
                               # 定义：3mm 内除 C5 外无非锚件；报告声明）
BLOCKER_REF_MM = 7.0           # 放宽 2：S1 证书直方图 top 堵网上、口袋端点 7mm
                               # 内有焊盘的非锚件（其走线=口袋墙的一部分）
BLOCKER_TOP_NETS = 5
CANDIDATE_REFS_PER_NET = 2
TOUCH_TOL = 1e-6               # 走线端点"落在焊盘上"的表面距离容差（pcbagent
                               # C.TOUCH_TOL 同值）

# ---- 通用 -----------------------------------------------------------------
_DESC_TRACK = re.compile(r"走线 \[([^\]]*)\] \(([-\d.]+),([-\d.]+)\)-\(([-\d.]+),"
                         r"([-\d.]+)\) w=([-\d.]+)")
_DESC_VIA = re.compile(r"过孔 \[([^\]]*)\] \(([-\d.]+),([-\d.]+)\) size=([-\d.]+)"
                       r" drill=([-\d.]+)")
_DESC_PAD = re.compile(r"([A-Za-z]+\d+) 焊盘 (\S+) \[([^\]]*)\] \(([-\d.]+),"
                       r"([-\d.]+)\)")
_AT_RE = re.compile(r"\(at +(-?[\d.]+) +(-?[\d.]+)(?: +(-?[\d.]+))?\)")
_NUM = r"(-?[\d.]+)"


def parse_item_desc(desc):
    """pcbagent CopperItem.desc → 几何 dict（kind=track/via/pad）；不识别 → None。"""
    m = _DESC_TRACK.match(desc or "")
    if m:
        return {"kind": "track", "net": m.group(1),
                "x1": float(m.group(2)), "y1": float(m.group(3)),
                "x2": float(m.group(4)), "y2": float(m.group(5)),
                "width": float(m.group(6))}
    m = _DESC_VIA.match(desc or "")
    if m:
        return {"kind": "via", "net": m.group(1),
                "x": float(m.group(2)), "y": float(m.group(3)),
                "size": float(m.group(4)), "drill": float(m.group(5))}
    m = _DESC_PAD.match(desc or "")
    if m:
        return {"kind": "pad", "ref": m.group(1), "number": m.group(2),
                "net": m.group(3), "x": float(m.group(4)),
                "y": float(m.group(5))}
    return None


def widened_bbox(board_bb, ax, ay, bx, by, margin_mm):
    """端点 bbox 外扩 margin 并夹紧板框（ripup1_campaign.bbox_of 同式）。"""
    return (max(min(ax, bx) - margin_mm, board_bb[0]),
            max(min(ay, by) - margin_mm, board_bb[1]),
            min(max(ax, bx) + margin_mm, board_bb[2]),
            min(max(ay, by) + margin_mm, board_bb[3]))


def normalize_plan(plan, net):
    """pcbagent Plan → route_one 同口径归一化 dict（无 wall-clock）。"""
    segs = [[int(L), round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)]
            for (L, x1, y1, x2, y2) in plan.segments]
    vias = [[round(x, 4), round(y, 4)] for (x, y) in plan.vias]
    return {
        "net": net, "ok": bool(plan.ok), "fail": plan.fail,
        "blocks": [str(b) for b in (plan.blocks or [])][:3],
        "width": plan.width, "via_size": plan.via_size,
        "via_drill": plan.via_drill,
        "refine_rounds": plan.refine_rounds,
        "segments": segs, "vias": vias,
        "length_mm": round(sum(math.hypot(s[3] - s[1], s[4] - s[2])
                               for s in segs), 3),
    }


# ---- 任务 1：落点枚举 / witness 账 -----------------------------------------
def landing_points(component_descs_layers, ax, ay, top_k=LANDING_TOP_K,
                   dedup_mm=LANDING_DEDUP_MM, exclude_xy=None):
    """B 侧连通分量 items（[(desc, layers)]）→ 到 A 距离升序的落点清单。

    落点=pad 中心（层=焊盘层∩信号层）、via 中心（F/In2 双层）、走线两端
    （走线层）。近重复（<dedup_mm）去重；exclude_xy（如权威 B 端点）剔除。
    纯函数；layers 取调用方给的 pcbagent 层号集合。"""
    pts = []
    for (desc, layers) in component_descs_layers:
        g = parse_item_desc(desc)
        if not g:
            continue
        ls = sorted(int(l) for l in layers)
        if g["kind"] == "pad":
            pts.append({"x": g["x"], "y": g["y"], "layers": ls,
                        "kind": "pad", "desc": desc})
        elif g["kind"] == "via":
            pts.append({"x": g["x"], "y": g["y"], "layers": ls,
                        "kind": "via", "desc": desc})
        else:
            for (x, y) in ((g["x1"], g["y1"]), (g["x2"], g["y2"])):
                pts.append({"x": x, "y": y, "layers": ls,
                            "kind": "track_end", "desc": desc})
    for p in pts:
        p["dist_to_a_mm"] = round(math.hypot(p["x"] - ax, p["y"] - ay), 4)
    pts.sort(key=lambda p: (p["dist_to_a_mm"], p["kind"], p["x"], p["y"]))
    out = []
    for p in pts:
        if exclude_xy and math.hypot(p["x"] - exclude_xy[0],
                                     p["y"] - exclude_xy[1]) < dedup_mm:
            continue
        if any(math.hypot(p["x"] - q["x"], p["y"] - q["y"]) < dedup_mm
               for q in out):
            continue
        out.append(p)
        if len(out) >= top_k:
            break
    return out


def route_bbox(segments, vias):
    """witness 铜的 bbox（round4）。"""
    xs, ys = [], []
    for s in segments:
        xs += [s[1], s[3]]
        ys += [s[2], s[4]]
    for (x, y) in vias:
        xs.append(x)
        ys.append(y)
    if not xs:
        return None
    return [round(min(xs), 4), round(min(ys), 4),
            round(max(xs), 4), round(max(ys), 4)]


def exits_region(bbox, region_mm, eps=1e-6):
    """witness bbox 是否越出 S1 走廊证书区域（越出=与 restricted 割一致）。"""
    if bbox is None or region_mm is None:
        return None
    return bool(bbox[0] < region_mm[0] - eps or bbox[1] < region_mm[1] - eps
                or bbox[2] > region_mm[2] + eps
                or bbox[3] > region_mm[3] + eps)


def closure_verdict(row_id, net, ladder_steps, landing_trials,
                    s1_cert_region, independent_check):
    """任务 1 verdict 行（纯装配）。

    ladder_steps：[{margin_mm, route}]（route=normalize_plan）；首个 ok 即
    witness（SAT）。landing_trials：[{landing, steps:[...]}]。
    independent_check：编排侧对 witness 的独立复核账（fresh Legality 逐段/
    逐孔 + 端点落铜 + 出走廊窗一致性）。"""
    witness_step = next((s for s in ladder_steps if s["route"]["ok"]), None)
    status = "SAT" if witness_step else "UNKNOWN"
    if status == "SAT" and independent_check and \
            not independent_check.get("all_ok"):
        # 独立复核不过（含未出 S1 走廊窗的一致性核对）：不改判 SAT（合同
        # 红线）——如实降为 UNKNOWN 并记原因
        status = "UNKNOWN"
    w = witness_step["route"] if witness_step else None
    row = {
        "row_id": row_id, "net": net,
        "live2s2_status": status,
        "upgrade_from": "S1: UNSAT(corridor-scope cert) + board_strengthen "
                        "UNKNOWN(candidate path)",
        "premise": "zero-ripup（他网铜与自网已落铜均冻结障碍；只加铜不拆铜）",
        "method": "搜索窗梯 %s mm（首项=L3_MARGIN 原口径）× 精确端点对 + "
                  "同网落点枚举 top-%d" % (list(CLOSURE_MARGIN_LADDER),
                                       LANDING_TOP_K),
        "witness": None if not w else {
            "margin_mm": witness_step["margin_mm"],
            "segments": len(w["segments"]), "vias": len(w["vias"]),
            "length_mm": w["length_mm"],
            "refine_rounds": w["refine_rounds"],
            "bbox_mm": route_bbox(w["segments"], w["vias"]),
            "exits_s1_corridor_region":
                exits_region(route_bbox(w["segments"], w["vias"]),
                             s1_cert_region),
        },
        "route_plan": None if not w else {
            "net": net, "width": w["width"], "via_size": w["via_size"],
            "via_drill": w["via_drill"], "segments": w["segments"],
            "vias": w["vias"],
            "uuid": board_writer.route_uuid(
                {"net": net, "segments": w["segments"], "vias": w["vias"]}),
        },
        "ladder": [{"margin_mm": s["margin_mm"], "ok": s["route"]["ok"],
                    "fail": s["route"]["fail"], "blocks": s["route"]["blocks"],
                    "segments": len(s["route"]["segments"]),
                    "vias": len(s["route"]["vias"]),
                    "refine_rounds": s["route"]["refine_rounds"],
                    "region_bbox_mm": s.get("region_bbox_mm")}
                   for s in ladder_steps],
        "landing_enumeration": landing_trials,
        "independent_check": independent_check,
        "s1_cert_region_mm": s1_cert_region,
        "unknown_reason": None if status == "SAT" else
            ("unknown:no_witness_within_ladder(有界搜索窗梯内无 witness；"
             "板级候选通径仍未证合法，不自动改判)"
             if not witness_step else
             "unknown:independent_check_failed"),
        "restricted_declarations": [
            "SAT=pcbagent Router._try_route(plan, 放大 bbox) 的 plan.ok（Region/"
            "A*+L1 终判全过 + 端点落铜），margin 仅搜索参数（ripup1_campaign."
            "_replan_net_excl 同一先例），ripup=False 冻结语义不变",
            "S1 走廊证书（restricted，区域窗 %s）与本 witness 不矛盾：witness "
            "必须出窗（exits_s1_corridor_region=true 才一致）" % (s1_cert_region,),
            "witness 是提案（route_plan），本包零写 live；应用与否由用户拍板",
        ],
    }
    return row


# ---- 任务 2：板文本级移位 / 剥除 -------------------------------------------
def footprint_at(board_text, ref):
    """板文本 → ref 封装自身 (at x y rot)（第一处 (at)，apply_placement 同口径）。"""
    for (s, e) in board_writer._top_level_nodes(board_text, "footprint"):
        node = board_text[s:e]
        m = re.search(r'\(property "Reference" "([^"]+)"', node)
        if not m or m.group(1) != ref:
            continue
        ma = _AT_RE.search(node)
        if not ma:
            raise ValueError("footprint %s 缺 (at)" % ref)
        return (float(ma.group(1)), float(ma.group(2)),
                float(ma.group(3) or 0.0))
    raise ValueError("ref %s 未命中板文件" % ref)


def move_footprint(board_text, ref, dx, dy):
    """ref 微移位 (dx,dy)（rot 不变）→ 新板文本（board_writer.apply_placement）。"""
    if math.hypot(dx, dy) > MOVE_MAX_MM + 1e-9:
        raise ValueError("移位 %.3f mm 超出上限 %.1f mm" % (math.hypot(dx, dy),
                                                        MOVE_MAX_MM))
    x, y, rot = footprint_at(board_text, ref)
    return board_writer.apply_placement(
        board_text, [{"ref": ref, "x": round(x + dx, 4),
                      "y": round(y + dy, 4), "rot": rot}])


def _node_field(node, tag):
    m = re.search(r"\(%s +%s +%s\)" % (tag, _NUM, _NUM), node)
    return (float(m.group(1)), float(m.group(2))) if m else None


def _node_str(node, tag):
    m = re.search(r'\(%s +"([^"]*)"\)' % tag, node)
    return m.group(1) if m else None


def _close(a, b, tol=1e-4):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def strip_copper(board_text, segments, vias):
    """按账单剥除 segment/via 顶层节点（几何+网名匹配；未命中即报错）。

    segments：[{layer_name, x1,y1,x2,y2, net}]（无序端点匹配）；
    vias：[{x,y,net}]。返回 (新文本, 剥除计数)。"""
    want_seg = list(segments)
    want_via = list(vias)
    hit_seg = [False] * len(want_seg)
    hit_via = [False] * len(want_via)
    drop = []
    for (s, e) in board_writer._top_level_nodes(board_text, "segment"):
        node = board_text[s:e]
        st, en = _node_field(node, "start"), _node_field(node, "end")
        layer, net = _node_str(node, "layer"), _node_str(node, "net")
        for i, w in enumerate(want_seg):
            if hit_seg[i] or w["net"] != net or w["layer_name"] != layer:
                continue
            p, q = (w["x1"], w["y1"]), (w["x2"], w["y2"])
            if (_close(st, p) and _close(en, q)) or \
                    (_close(st, q) and _close(en, p)):
                hit_seg[i] = True
                drop.append((s, e))
                break
    for (s, e) in board_writer._top_level_nodes(board_text, "via"):
        node = board_text[s:e]
        at, net = _node_field(node, "at"), _node_str(node, "net")
        for i, w in enumerate(want_via):
            if hit_via[i] or w["net"] != net:
                continue
            if at and _close(at, (w["x"], w["y"])):
                hit_via[i] = True
                drop.append((s, e))
                break
    if not all(hit_seg) or not all(hit_via):
        raise ValueError("账单项未命中板文本：seg=%s via=%s"
                         % ([w for w, h in zip(want_seg, hit_seg) if not h],
                            [w for w, h in zip(want_via, hit_via) if not h]))
    drop.sort()
    pieces, last = [], 0
    for (s, e) in drop:
        # 连同节点前导缩进空白一起剥（保持文本整洁；不影响 s-expr 语义）
        s2 = s
        while s2 > last and board_text[s2 - 1] in " \t":
            s2 -= 1
        pieces.append(board_text[last:s2])
        last = e
        # 吞掉节点后的行尾
        if board_text.startswith("\r\n", last):
            last += 2
        elif board_text.startswith("\n", last):
            last += 1
    pieces.append(board_text[last:])
    return "".join(pieces), {"segments": len(want_seg), "vias": len(want_via)}


# ---- 任务 2：铜扰动账单 -----------------------------------------------------
def disturbance_bill(ref, ref_pads, tracks, vias, target_net, pt_prim_dist,
                     tol=TOUCH_TOL):
    """被移 ref 的精确铜扰动账单（几何判定：走线端点/过孔中心落在该 ref 任一
    焊盘 prim 表面距 ≤ tol）。

    ref_pads：[{number, net, prims:[prim…]}]；tracks：[{layer, layer_name,
    x1,y1,x2,y2,width,net}]；vias：[{x,y,net,size,drill}]；pt_prim_dist：
    pcbagent geometry.pt_prim_dist（注入，保持纯函数可测）。
    逐项分类：target_net_own（=目标网自身）/ other_net。"""
    seg_items, via_items = [], []
    for t in tracks:
        hit_pad = None
        for (x, y, end) in ((t["x1"], t["y1"], "start"),
                            (t["x2"], t["y2"], "end")):
            for pd in ref_pads:
                if pd["net"] != t["net"]:
                    continue
                if any(pt_prim_dist(x, y, prim) <= tol for prim in pd["prims"]):
                    hit_pad = (pd["number"], end)
                    break
            if hit_pad:
                break
        if hit_pad:
            seg_items.append({
                "kind": "segment", "net": t["net"],
                "cls": "target_net_own" if t["net"] == target_net
                else "other_net",
                "pad": "%s.%s" % (ref, hit_pad[0]), "attached_end": hit_pad[1],
                "layer": t["layer"], "layer_name": t["layer_name"],
                "x1": t["x1"], "y1": t["y1"], "x2": t["x2"], "y2": t["y2"],
                "width": t["width"],
                # 悬空端（重布落点）：非落焊盘的那一端
                "dangling_xy": [t["x2"], t["y2"]] if hit_pad[1] == "start"
                else [t["x1"], t["y1"]],
            })
    for v in vias:
        for pd in ref_pads:
            if pd["net"] != v["net"]:
                continue
            if any(pt_prim_dist(v["x"], v["y"], prim) <= tol
                   for prim in pd["prims"]):
                via_items.append({
                    "kind": "via", "net": v["net"],
                    "cls": "target_net_own" if v["net"] == target_net
                    else "other_net",
                    "pad": "%s.%s" % (ref, pd["number"]),
                    "x": v["x"], "y": v["y"], "size": v["size"],
                    "drill": v["drill"],
                })
                break
    items = seg_items + via_items
    nets = sorted({it["net"] for it in items})
    return {
        "ref": ref, "target_net": target_net,
        "segments": seg_items, "vias": via_items,
        "counts": {
            "segments_total": len(seg_items), "vias_total": len(via_items),
            "target_net_own": sum(1 for it in items
                                  if it["cls"] == "target_net_own"),
            "other_net": sum(1 for it in items if it["cls"] == "other_net"),
        },
        "nets": nets,
        "other_nets": sorted(n for n in nets if n != target_net),
        "rule": "走线端点/过孔中心到该 ref 任一同网焊盘 prim 表面距 ≤ %g mm"
                % tol,
    }


# ---- 任务 2：候选生成 / 排序 -----------------------------------------------
def pocket_side(fwd_closure, rev_closure):
    """A/B 侧闭包规模对比 → 口袋端点（闭包小者=被围端点）。"""
    if fwd_closure is None and rev_closure is None:
        return None
    if rev_closure is None:
        return "A"
    if fwd_closure is None:
        return "B"
    return "A" if fwd_closure <= rev_closure else "B"


def nearby_refs(pads, cx, cy, radius_mm=POCKET_NEAR_MM,
                anchors=ANCHOR_REFS, exclude_refs=(), nets=None):
    """口袋端点 radius 内有焊盘的非锚件 ref（按最近焊盘距离升序）。

    pads：[{ref, number, net, x, y}]。锚件与 exclude_refs 永不入选；nets 给定
    时只计该网集上的焊盘（堵网 ref 放宽规则）。"""
    best = {}
    for p in pads:
        if p["ref"] in anchors or p["ref"] in exclude_refs:
            continue
        if nets is not None and p["net"] not in nets:
            continue
        d = math.hypot(p["x"] - cx, p["y"] - cy)
        if d <= radius_mm and (p["ref"] not in best or d < best[p["ref"]]):
            best[p["ref"]] = d
    return [{"ref": r, "nearest_pad_mm": round(d, 4)}
            for r, d in sorted(best.items(), key=lambda kv: (kv[1], kv[0]))]


def spoke_cert_rules(cut_groups):
    """spoke 型证书割组 → 逐层封闭规则直方图（端点自锁机制说明用）。"""
    rules = {}
    for g in cut_groups or []:
        if g.get("kind") != "spoke":
            continue
        for layer in (g.get("why") or {}).get("per_layer") or []:
            w = layer.get("why") or {}
            key = "%s:%s" % (layer.get("closed"), w.get("rule"))
            rules[key] = rules.get(key, 0) + len(g.get("items") or [])
    return dict(sorted(rules.items()))


def candidate_moves(ref_xy, pocket_xy, magnitudes=MOVE_MAGNITUDES):
    """ref 相对口袋端点的径向外移（8 向吸附）× 幅度 + 两侧切向 1.5mm。

    返回 [{dx, dy, label}]（|d| ≤ MOVE_MAX_MM；确定性顺序）。"""
    vx, vy = ref_xy[0] - pocket_xy[0], ref_xy[1] - pocket_xy[1]
    n = math.hypot(vx, vy)
    if n < 1e-9:
        ux, uy = 1.0, 0.0
    else:
        ang = math.atan2(vy, vx)
        snapped = round(ang / (math.pi / 4)) * (math.pi / 4)
        ux, uy = math.cos(snapped), math.sin(snapped)
    ux, uy = round(ux, 6), round(uy, 6)
    out = []
    for mag in magnitudes:
        if mag > MOVE_MAX_MM + 1e-9:
            continue
        out.append({"dx": round(ux * mag, 4), "dy": round(uy * mag, 4),
                    "label": "radial_away_%.1fmm" % mag})
    tx, ty = -uy, ux
    for sgn, name in ((1, "tangent_ccw"), (-1, "tangent_cw")):
        out.append({"dx": round(sgn * tx * 1.5, 4), "dy": round(sgn * ty * 1.5, 4),
                    "label": "%s_1.5mm" % name})
    return out


def rank_candidates(evals):
    """候选评估行 → 排序（可收目标行数降序、他网扰动段数升序、总扰动升序、
    候选 id 字典序）。evals：[{candidate_id, closable_rows, other_net_items,
    total_items, …}]。"""
    return sorted(evals, key=lambda e: (-int(e.get("closable_rows", 0)),
                                        int(e.get("other_net_items", 0)),
                                        int(e.get("total_items", 0)),
                                        str(e.get("candidate_id"))))


def closable_rows_of(per_net_verdicts, baseline_status):
    """移位后逐网 verdict 与基线（S1/S2 三态）对比 → 新收行（基线非 SAT →
    SAT）与退化行（基线 SAT → 非 SAT）。"""
    gained, lost = [], []
    for net, v in sorted(per_net_verdicts.items()):
        b = baseline_status.get(net)
        if v["status"] == "SAT" and b != "SAT":
            gained.append(net)
        if v["status"] != "SAT" and b == "SAT":
            lost.append(net)
    return {"gained": gained, "lost": lost, "closable_rows": len(gained)}


def failure_set_diff(pre_ids, post_ids):
    """开工/收工失败集差集（live2s1_experiment 同式；gates_ok ⟺ 无新增）。"""
    pre, post = set(pre_ids or []), set(post_ids or [])
    return {"new_failures": sorted(post - pre), "fixed": sorted(pre - post),
            "unchanged_count": len(pre & post), "gates_ok": not (post - pre)}
