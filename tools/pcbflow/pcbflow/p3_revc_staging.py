"""pcbflow.p3_revc_staging -- PAPER-P1-1B Rev-C staging 确定性执行器（纯函数）。

协议：out/v4-exec/p3-revc/protocol/protocol-p3-revc-v1.json（R4 预注册冻结）。
批准件：out/v4-exec/p3-revc-approval/APR-P3-REVC-r1.json（四动作子集）。

职责（单一职责；本模块零 IO、零子进程、零网络、零 wall-clock、零主机路径；
落盘全部由编排侧 scripts/p3_revc_run.py 完成）：

1. 解析真实板快照文本（KiCad 20260206 方言；segment/via/zone/footprint）；
2. 构建复查包同形板模型（scenario_id=p3-revc-staging-r1；模型内嵌
   source_snapshot_sha256 → srp board_snapshot_sha256 传递绑定快照文件）；
3. 链（chain）抽取：同网同层 segment 端点精确重合拼接 → 折点压缩折线；
4. 冻结选网规则（协议 §net_selection_rule）→ 池 + 批次（≤10 网/批）；
5. 冻结动作语义（协议 §action_subset.concrete_semantics）：
   - replace_subpath = 拐角 45° 倒角（s 阶梯升序；s ≤ 0.5×min(两邻段长)）；
   - move_vertex = 轴对齐双单段腿角点 8 罗盘向位移（步长 0.25/0.5 升序）；
   - insert_via_candidate = 结构性前置（网须双铜层均有既有几何）→ 池内单层
     网恒 0 提案；
   - reject_route_patch = 无候选过预检时的诚实弃权。
6. advisory 几何预检（R6：恒不能清 DRC 旗/改门；kicad-cli 唯一 authority）：
   v4_1 精确几何引擎（pcbflow.v4_1.precheck.check_patch——patch 终态全段
   复查：插入段+被改端点旧段；Minkowski 核精确焊盘几何+逐网 net class
   clearance，保守带 0.01mm 宁误报不漏报；R27 接线，旧 pad=min(w,h)/2
   中心距近似已移除——P3REVC-BATCH-01 漏报根因）；角区三角形内无任何
   pad/via 中心（防断链）；
7. 板文本手术（只 splice 不重序列化）：坐标修改=段节点内 token 级替换；
   新增段=board_writer.apply_routes 落盘链（eol="auto" 保 CRLF）；
8. paired 目标指标（逐网长度/折角/segment 差）。

确定性：全链无随机源；一切序=确定性阶梯+字典序；uuid=内容派生 sha256
（board_writer.route_uuid 同源命名空间）。同输入同输出。
"""

from __future__ import annotations

import math
import re

from . import sexpr_min
from .board_writer import route_uuid as _bw_route_uuid
from .v4_1.board_parse import parse_board_text as _v41_parse_board_text
from .v4_1.netclasses import (NetClassNotAvailable, load_netclasses,
                              netclass_table_from_declared_defaults)
from .v4_1.precheck import (AdvisoryPrecheckV41, PrecheckBlocked,
                            build_geom_items)

SCHEMA = "pcbflow.paperexec.p3revc-staging/1"
PATCH_SCHEMA = "pcbflow-p3revc-patch-1"
SCENARIO_ID = "p3-revc-staging-r1"
SOURCE = "deterministic_executor"

#: 冻结常量（协议 §action_subset / §criteria；改值=改协议=违规）
CLEARANCE_MM = 0.2
CHAMFER_LADDER_MM = (0.3, 0.6, 0.9, 1.2)
MOVE_STEPS_MM = (0.25, 0.5)
MOVE_DIRS_8 = ((1, 0), (-1, 0), (0, 1), (0, -1),
               (1, 1), (1, -1), (-1, 1), (-1, -1))
MAX_NET_SEGMENTS = 8
MIN_LEG_FOR_CHAMFER_MM = 0.6      # s_min=0.3 且 s ≤ 0.5×腿长 → 腿长须 ≥0.6
TRIANGLE_OBS_GUARD_MM = 0.05      # A/B 端与 pad/via 中心最小距离（防重叠断链）
LAYER_IDX = {"F.Cu": 0, "B.Cu": 2, "In1.Cu": 4, "In2.Cu": 6}
LAYER_SHORT = {"F.Cu": "F", "B.Cu": "B", "In1.Cu": "I1", "In2.Cu": "I2"}

REJECTION_CLASSES = ("base_hash_mismatch", "endpoint_moved",
                     "keepout_or_collision", "off_grid_coord",
                     "width_mismatch", "layer_mismatch", "unknown_identity",
                     "undeclared_change", "illegal_geometry", "other")

_NUM_RE = re.compile(r"-?\d+\.?\d*")
_Q6 = 6


# ---------------------------------------------------------------- 解析侧

def _find_first(node, tag):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == tag:
            return c
    return None


def _floats(node, n):
    return [float(v) for v in node[1:1 + n]]


def _q6(v):
    return round(float(v), _Q6)


def parse_board_text(text):
    """板文本 → 结构模型（纯函数）。只收编本执行器域内事实；其余零解释。"""
    top = sexpr_min.parse(text)
    roots = [n for n in top if isinstance(n, list) and n and n[0]
             == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError("expect exactly one kicad_pcb root, got %d"
                         % len(roots))
    root = roots[0]
    segments, vias, zone_nets, pads = [], [], set(), []
    copper_layers, edge_pts = [], []
    for c in root[1:]:
        if not isinstance(c, list) or not c:
            continue
        tag = c[0]
        if tag == "segment":
            st, en = _find_first(c, "start"), _find_first(c, "end")
            w, ly = _find_first(c, "width"), _find_first(c, "layer")
            nt, uid = _find_first(c, "net"), _find_first(c, "uuid")
            if None in (st, en, w, ly, nt, uid):
                raise ValueError("segment 节点缺必需子节点（fail-closed）")
            segments.append({
                "uuid": uid[1], "net": nt[1], "layer": ly[1],
                "width": float(w[1]),
                "x1": float(st[1]), "y1": float(st[2]),
                "x2": float(en[1]), "y2": float(en[2]),
            })
        elif tag == "via":
            at = _find_first(c, "at")
            size, drill = _find_first(c, "size"), _find_first(c, "drill")
            lys, nt = _find_first(c, "layers"), _find_first(c, "net")
            uid = _find_first(c, "uuid")
            if None in (at, size, drill, lys, nt, uid):
                raise ValueError("via 节点缺必需子节点（fail-closed）")
            vias.append({
                "uuid": uid[1], "net": nt[1],
                "x": float(at[1]), "y": float(at[2]),
                "size": float(size[1]), "drill": float(drill[1]),
                "l1": lys[1], "l2": lys[2],
            })
        elif tag == "zone":
            nt = _find_first(c, "net")
            if nt is not None and isinstance(nt[1], str):
                zone_nets.add(nt[1])
        elif tag == "footprint":
            pads.extend(_footprint_pads(c))
        elif tag == "layers":
            for sub in c[1:]:
                if isinstance(sub, list) and len(sub) >= 2 \
                        and isinstance(sub[1], str) \
                        and sub[1].endswith(".Cu"):
                    copper_layers.append(sub[1])
        elif tag in ("gr_line", "gr_rect", "gr_arc", "gr_circle"):
            ly = _find_first(c, "layer")
            if ly is not None and ly[1] == "Edge.Cuts":
                for sub in c[1:]:
                    if isinstance(sub, list) and sub and sub[0] in (
                            "start", "end", "center", "mid") \
                            and len(sub) >= 3:
                        edge_pts.append((float(sub[1]), float(sub[2])))
    return {"segments": segments, "vias": vias,
            "zone_nets": sorted(zone_nets), "pads": pads,
            "copper_layers": copper_layers, "edge_points": edge_pts}


def _footprint_pads(fp_node):
    """footprint → 绝对坐标 pad 列表（渲染 advisory 用；旋转=KiCad 画布
    约定 y-down/正角 CCW 的映射 x'=x·cosθ+y·sinθ, y'=−x·sinθ+y·cosθ）。"""
    ref = None
    for sub in fp_node[1:]:
        if isinstance(sub, list) and sub and sub[0] == "property" \
                and len(sub) >= 3 and sub[1] == "Reference":
            ref = sub[2]
            break
    if ref is None:
        raise ValueError("footprint 缺 Reference property（fail-closed）")
    at = _find_first(fp_node, "at")
    if at is None or len(at) < 3:
        raise ValueError("footprint %s 缺 (at)（fail-closed）" % ref)
    fx, fy = float(at[1]), float(at[2])
    rot = math.radians(float(at[3])) if len(at) > 3 and at[3] != "" else 0.0
    cs, sn = math.cos(rot), math.sin(rot)
    out = []
    for pad in sexpr_min.find_all(fp_node, "pad"):
        pid = pad[1]
        pat = _find_first(pad, "at")
        psize = _find_first(pad, "size")
        plys = _find_first(pad, "layers")
        pnet = _find_first(pad, "net")
        if None in (pat, psize, plys):
            raise ValueError("pad %s.%s 缺必需子节点（fail-closed）"
                             % (ref, pid))
        px, py = float(pat[1]), float(pat[2])
        ax = fx + px * cs + py * sn
        ay = fy - px * sn + py * cs
        layer = None
        for lv in plys[1:]:
            if isinstance(lv, str) and lv.endswith(".Cu"):
                layer = "F.Cu" if lv == "*.Cu" else lv
                break
        if layer is None:
            continue  # 非铜层 pad（如 NPTH 标注）不进渲染模型
        out.append({
            "pad_id": "%s.%s" % (ref, pid),
            "net_id": pnet[1] if pnet is not None else "",
            "x_mm": _q6(ax), "y_mm": _q6(ay),
            "w_mm": float(psize[1]), "h_mm": float(psize[2]),
            "layer": layer,
        })
    return out


# ---------------------------------------------------------------- 链抽取

def _pkey(x, y):
    return (_q6(x), _q6(y))


def build_chains(parsed):
    """同网同层 segment 端点精确重合（1e-6 量化）拼接 → 链列表。

    每链：{"net","layer","widths","seg_idx":[...],"polyline":[[x,y]...]}；
    折线=折点压缩（共线中间点剔除）；链序与折线方向=字典序确定性。
    """
    groups = {}
    for i, s in enumerate(parsed["segments"]):
        groups.setdefault((s["net"], s["layer"]), []).append(i)
    chains = []
    for (net, layer) in sorted(groups):
        idxs = groups[(net, layer)]
        adj = {}
        for i in idxs:
            s = parsed["segments"][i]
            a, b = _pkey(s["x1"], s["y1"]), _pkey(s["x2"], s["y2"])
            adj.setdefault(a, []).append((i, b))
            adj.setdefault(b, []).append((i, a))
        degree = {p: len(v) for p, v in adj.items()}
        terminals = sorted(p for p, d in degree.items() if d != 2)
        used = set()
        chains_here = []

        for t in terminals:
            for (i, other) in sorted(adj[t]):
                if i not in used:
                    used.add(i)
                    pts, segs = [t], [i]
                    cur = other
                    pts.append(cur)
                    while degree.get(cur, 0) == 2:
                        nxt = None
                        for (j, o2) in sorted(adj[cur]):
                            if j not in used:
                                used.add(j)
                                segs.append(j)
                                nxt = o2
                                break
                        if nxt is None:
                            break
                        pts.append(nxt)
                        cur = nxt
                    chains_here.append((pts, segs))
        # 纯环（无 terminal 残留）：字典序最小点破环（下方通用路径）
        remaining = [i for i in idxs if i not in used]
        while remaining:
            start_seg = min(remaining,
                            key=lambda i: sorted([
                                _pkey(parsed["segments"][i]["x1"],
                                      parsed["segments"][i]["y1"]),
                                _pkey(parsed["segments"][i]["x2"],
                                      parsed["segments"][i]["y2"])]))
            s = parsed["segments"][start_seg]
            a, b = _pkey(s["x1"], s["y1"]), _pkey(s["x2"], s["y2"])
            begin = min(a, b)
            pts, segs = [begin], []
            cur = begin
            while True:
                nxt = None
                for (j, o2) in sorted(adj[cur]):
                    if j not in used:
                        used.add(j)
                        segs.append(j)
                        nxt = o2
                        break
                if nxt is None:
                    break
                pts.append(nxt)
                cur = nxt
                if _pkey(cur[0], cur[1]) == begin:
                    break
            remaining = [i for i in remaining if i not in used]
            chains_here.append((pts, segs))
        for pts, segs in chains_here:
            widths = sorted({parsed["segments"][i]["width"] for i in segs})
            poly = _compress(pts)
            chains.append({"net": net, "layer": layer, "widths": widths,
                           "seg_idx": segs, "polyline": poly})
    chains.sort(key=lambda c: (c["net"], c["layer"],
                               tuple(c["polyline"][0]),
                               tuple(c["polyline"][-1])))
    for k, c in enumerate(chains):
        c["chain_no"] = k + 1
    return chains


def _compress(pts):
    """共线中间点剔除（纯函数；保留折点）。"""
    if len(pts) <= 2:
        return [list(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        ax, ay = out[-1]
        bx, by = pts[i]
        cx, cy = pts[i + 1]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - ax)
        if abs(cross) > 1e-9:
            out.append(pts[i])
    out.append(pts[-1])
    return [list(p) for p in out]


# ---------------------------------------------------------------- 板模型

def build_board_model(parsed, snapshot_sha256):
    """快照模型 → 复查包同形 board dict（内嵌 source_snapshot_sha256；
    srp._sha256_of 不剥 hash 键 → manifest.board_snapshot_sha256 传递绑定
    快照文件实测 hash）。"""
    xs, ys = [], []
    for p in parsed["pads"]:
        xs.append(p["x_mm"])
        ys.append(p["y_mm"])
    for s in parsed["segments"]:
        xs += [s["x1"], s["x2"]]
        ys += [s["y1"], s["y2"]]
    for v in parsed["vias"]:
        xs.append(v["x"])
        ys.append(v["y"])
    for (x, y) in parsed["edge_points"]:
        xs.append(x)
        ys.append(y)
    if not xs:
        raise ValueError("空板几何（fail-closed）")
    x0, x1 = math.floor(min(xs) * 2) / 2, math.ceil(max(xs) * 2) / 2
    y0, y1 = math.floor(min(ys) * 2) / 2, math.ceil(max(ys) * 2) / 2
    nets = sorted({s["net"] for s in parsed["segments"]}
                  | {v["net"] for v in parsed["vias"]}
                  | {p["net_id"] for p in parsed["pads"] if p["net_id"]})
    return {
        "scenario_id": SCENARIO_ID,
        "source_snapshot_sha256": snapshot_sha256,
        "board": {"bbox_mm": [x0, y0, x1, y1],
                  "layers": parsed["copper_layers"] or ["F.Cu"]},
        "rules": {"clearance_mm": CLEARANCE_MM,
                  "width_mm": {"default": 0.2},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3}},
        "nets": [{"net_id": n, "net_class": "default"} for n in nets],
        "pads": parsed["pads"],
        "keepouts": [],
        "relations": [],
    }


# ---------------------------------------------------------------- 选网

def plan_pool(parsed, chains):
    """协议 §net_selection_rule 冻结规则 → (pool 行列表, 批次映射)。"""
    net_segs = {}
    for c in chains:
        net_segs.setdefault(c["net"], []).append(c)
    via_nets = {v["net"] for v in parsed["vias"]}
    zone_nets = set(parsed["zone_nets"])
    rows = []
    for net in sorted(net_segs):
        cs = net_segs[net]
        n_segs = sum(len(c["seg_idx"]) for c in cs)
        layers = {c["layer"] for c in cs}
        if len(layers) != 1:
            continue
        if not (2 <= n_segs <= MAX_NET_SEGMENTS):
            continue
        if net in via_nets or net in zone_nets:
            continue
        if not all(len(c["widths"]) == 1 for c in cs):
            continue
        if not any(_chamferable_corners(c) for c in cs):
            continue
        rows.append({"net_id": net, "layer": sorted(layers)[0],
                     "segment_count": n_segs, "chain_count": len(cs)})
    rows.sort(key=lambda r: (r["segment_count"], r["net_id"]))
    batches = {}
    for bi in range(3):
        chunk = rows[bi * 10:(bi + 1) * 10]
        if not chunk:
            break
        batches["batch-%02d" % (bi + 1)] = [r["net_id"] for r in chunk]
    return rows, batches


def _chamferable_corners(chain):
    """链内可倒角折点数（两邻段长 ≥ MIN_LEG_FOR_CHAMFER_MM）。"""
    poly, n = chain["polyline"], 0
    for k in range(1, len(poly) - 1):
        l1 = _dist(poly[k - 1], poly[k])
        l2 = _dist(poly[k], poly[k + 1])
        if l1 >= MIN_LEG_FOR_CHAMFER_MM and l2 >= MIN_LEG_FOR_CHAMFER_MM:
            n += 1
    return n


# ---------------------------------------------------------------- 预检

def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _seg_len(s):
    return math.hypot(s["x2"] - s["x1"], s["y2"] - s["y1"])


def _point_seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    denom = vx * vx + vy * vy
    if denom <= 1e-12:
        return math.hypot(wx, wy)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _seg_seg_dist(s1, s2):
    """中心线段-段最小距离（含平行/相交退化；负值=相交以 0 记）。"""
    (a, b), (c, d) = s1, s2
    if _segments_intersect(a, b, c, d):
        return 0.0
    return min(_point_seg_dist(c[0], c[1], a[0], a[1], b[0], b[1]),
               _point_seg_dist(d[0], d[1], a[0], a[1], b[0], b[1]),
               _point_seg_dist(a[0], a[1], c[0], c[1], d[0], d[1]),
               _point_seg_dist(b[0], b[1], c[0], c[1], d[0], d[1]))


def _orient(a, b, p):
    v = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)


def _segments_intersect(a, b, c, d):
    return (_orient(a, b, c) * _orient(a, b, d) <= 0
            and _orient(c, d, a) * _orient(c, d, b) <= 0)


def _point_in_triangle(p, tA, tB, tC):
    s1 = _orient(tA, tB, p)
    s2 = _orient(tB, tC, p)
    s3 = _orient(tC, tA, p)
    return (s1 >= 0 and s2 >= 0 and s3 >= 0) or \
           (s1 <= 0 and s2 <= 0 and s3 <= 0)


def build_foreign_index(parsed, protected_nets):
    """异网障碍索引（同层 segment + via + 同层 pad；protected_nets=本批网，
    对它们零预检约束——批内网互不约束与 kicad-cli 批内同网判定一致口径）。
    另返回全量 pad/via 中心表（断链守卫用，不分网）。"""
    segs_by_layer, vias, pads_by_layer = {}, [], {}
    for s in parsed["segments"]:
        segs_by_layer.setdefault(s["layer"], []).append(
            (s, (s["x1"], s["y1"], s["x2"], s["y2"])))
    for v in parsed["vias"]:
        vias.append(v)
    for p in parsed["pads"]:
        pads_by_layer.setdefault(p["layer"], []).append(p)
    return {"segs": segs_by_layer, "vias": vias, "pads": pads_by_layer,
            "protected": set(protected_nets)}


def _build_v41_precheck(parsed, board_text, kicad_pro_obj, protected_nets):
    """staging parsed + 板文本 -> v4_1 精确预检器（R27 接线；只读 import
    pcbflow.v4_1 冻结接口）。

    - board_text 必需：v4_1 精确焊盘几何（shape/旋转/圆角/铜层集）只有板
      文本携带，staging parsed 不含；缺失=fail-closed ValueError（旧
      pad=min(w,h)/2 近似已移除，不得静默回退漏报方向错误口径）；
    - 段数交叉守恒断言（staging 与 v4_1 双解析对同一板文本）；
    - net class 源：kicad_pro_obj（与板内 net_class 节点二选一，多源
      ambiguous fail-closed 由 v4_1.load_netclasses 承担）；全缺回退协议
      冻结 CLEARANCE_MM declared defaults（可追溯）。
    """
    if board_text is None:
        raise ValueError(
            "v4_1 预检资产缺失（fail-closed）：board_text 未提供。旧近似"
            "预检（pad=min(w,h)/2，P3REVC-BATCH-01 漏报根因）已按 R27 接线"
            "移除；候选生成必须传入板文本供 pcbflow.v4_1 精确几何解析，"
            "可选 kicad_pro_obj 作 net class 源")
    parsed_v41 = _v41_parse_board_text(board_text)
    if len(parsed_v41["segments"]) != len(parsed["segments"]):
        raise ValueError(
            "v4_1 解析段数 %d ≠ staging 解析段数 %d（fail-closed 双解析"
            "守恒断言）" % (len(parsed_v41["segments"]),
                            len(parsed["segments"])))
    try:
        net_table = load_netclasses(board_text=board_text,
                                    kicad_pro_obj=kicad_pro_obj)
    except NetClassNotAvailable:
        net_table = netclass_table_from_declared_defaults(
            CLEARANCE_MM,
            source_note="p3_revc_staging 协议冻结 CLEARANCE_MM=%.2f"
                        "（declared defaults；板内无 net_class 节点且未提供"
                        " kicad_pro_obj）" % CLEARANCE_MM)
    return AdvisoryPrecheckV41(build_geom_items(parsed_v41), net_table,
                               protected_nets=protected_nets)


def _v41_gate(parsed, cand, v41pre):
    """patch 终态全段 v4_1 精确预检门（check_patch 直入口）。返回
    (ok, reason, result)；blocked 传播转诚实弃权 reason，不吞。"""
    try:
        r = v41pre.check_patch(parsed, cand)
    except PrecheckBlocked as exc:
        return False, "precheck_blocked:%s" % exc, None
    if r["verdict"] == "clean":
        return True, None, r
    if r["verdict"] == "blocked":
        return False, "precheck_blocked:%s" % "; ".join(
            r.get("blocked_reasons") or []), r
    viol = [v for seg in r["per_segment"] for v in seg["violations"]]
    hard = [v for v in viol if v["flag_class"] == "hard_violation"]
    worst = (hard or viol)[0]
    pred = worst["pred_clearance_mm"]
    need = worst["required_mm"]
    if worst["flag_class"] != "hard_violation":
        need = need + v41pre.band
    return False, ("clearance_fail:v41:%s:%s:%s:d=%s<%.4f"
                   % (worst["flag_class"], worst["item_kind"],
                      worst["item_ref"],
                      "overlap" if pred is None else "%.4f" % pred,
                      need)), r


def _v41_precheck_record(r):
    """v4_1 check_patch 结果 -> patch["precheck"] 记录（结构兼容：保留
    legacy 键位，旧中心距口径随近似退役置 None；新增 engine 自描述键）。"""
    mins = [seg["min_foreign_clearance_mm"] for seg in r["per_segment"]
            if seg["min_foreign_clearance_mm"] is not None]
    return {
        "clearance_mm": CLEARANCE_MM,
        "engine": r["engine"],
        "precheck_schema": r["schema"],
        "v41_verdict": r["verdict"],
        "checked_segments": len(r["per_segment"]),
        "min_foreign_clearance_mm": None if not mins else _q6(min(mins)),
        "min_foreign_centerline_dist_mm": None,
        "corner_region_obstacle_free": True,
        "limitations": list(r["limitations"]),
    }


def _obstacle_free_triangle(tA, tB, tC, fidx):
    """角区三角形内无任何 pad/via 中心（任意网；防同网 via-in-track 断链）。"""
    obstacles = [(v["x"], v["y"], "via", v["net"]) for v in fidx["vias"]]
    for (layer_p, plist) in fidx["pads"].items():
        obstacles += [(p["x_mm"], p["y_mm"], "pad", p["net_id"])
                      for p in plist]
    for (x, y, kind, net) in obstacles:
        if _point_in_triangle((x, y), tA, tB, tC):
            return False, (kind, net)
        if _dist((x, y), tA) < TRIANGLE_OBS_GUARD_MM \
                or _dist((x, y), tC) < TRIANGLE_OBS_GUARD_MM:
            return False, (kind, net)
    return True, None


def _adjacent_segment(segs, C, toward):
    """折点 C 的相邻段：端点==C 且方向朝 toward 的段 → (seg, 另一端点)。"""
    best = None
    for s in segs:
        p1 = (s["x1"], s["y1"])
        p2 = (s["x2"], s["y2"])
        if _pkey(*p1) == C:
            other = p2
        elif _pkey(*p2) == C:
            other = p1
        else:
            continue
        vx, vy = C[0] - other[0], C[1] - other[1]
        wx, wy = C[0] - toward[0], C[1] - toward[1]
        cross = vx * wy - vy * wx
        dot = vx * wx + vy * wy
        if abs(cross) < 1e-9 and dot > 1e-9:
            best = (s, other)
            break
    return best if best else (None, None)


# ---------------------------------------------------------------- 候选生成

def _route_id(chain, chains_index):
    return "%s#%s#S%02d" % (chain["net"], LAYER_SHORT.get(chain["layer"],
                                                           chain["layer"]),
                            chains_index[id(chain)])


def generate_batch_candidates(parsed, chains, net_ids, snapshot_sha256,
                              board_text=None, kicad_pro_obj=None):
    """一批网的确定性候选（每网至多 1 个；无候选过预检 → reject 记录）。

    board_text=v4_1 精确预检必需（fail-closed，见 _build_v41_precheck）；
    kicad_pro_obj=net class 源（缺省回退协议冻结 CLEARANCE_MM）。
    返回 {"patches":[...], "rejections":[...], "chains_index": {...}}。
    """
    by_net = {}
    for c in chains:
        by_net.setdefault(c["net"], []).append(c)
    cidx = {id(c): i + 1 for i, c in enumerate(
        sorted(chains, key=lambda c: (c["net"], c["layer"],
                                      tuple(c["polyline"][0]),
                                      tuple(c["polyline"][-1]))))}
    v41pre = _build_v41_precheck(parsed, board_text, kicad_pro_obj,
                                 set(net_ids))
    fidx = build_foreign_index(parsed, set(net_ids))
    patches, rejections = [], []
    for net in net_ids:
        got = None
        reasons = []
        for chain in by_net.get(net, []):
            rid = _route_id(chain, cidx)
            cand, why = _chain_candidate(parsed, chain, rid, fidx, v41pre)
            if cand is not None:
                cand["scenario_id"] = SCENARIO_ID
                cand["source"] = SOURCE
                cand["schema_version"] = PATCH_SCHEMA
                cand["snapshot_sha256"] = snapshot_sha256
                patches.append(cand)
                got = rid
                break
            reasons.extend(why)
        if got is None:
            rejections.append({
                "route_id": "%s#*" % net,
                "reason_class": _dominant_class(reasons),
                "reasons": reasons[:8] or ["no_structural_candidate"],
            })
    return {"patches": patches, "rejections": rejections}


def _dominant_class(reasons):
    for r in reasons:
        if r.startswith("clearance_fail:"):
            return "keepout_or_collision"
        if r.startswith("obstacle_in_corner_region:"):
            return "keepout_or_collision"
    return "illegal_geometry" if reasons else "other"


def _chain_candidate(parsed, chain, rid, fidx, v41pre):
    """单链确定性候选：倒角阶梯 → move_vertex 罗盘 → (None, reasons)。"""
    poly = chain["polyline"]
    layer = chain["layer"]
    width = chain["widths"][0]
    segs = [parsed["segments"][i] for i in chain["seg_idx"]]
    reasons = []
    if len(poly) < 3 or len(segs) < 2:
        return None, ["chain_not_patchable:fewer_than_2_segments"]
    for k in range(1, len(poly) - 1):
        C = tuple(poly[k])
        s_prev, other_prev = _adjacent_segment(segs, C, poly[k - 1])
        s_next, other_next = _adjacent_segment(segs, C, poly[k + 1])
        if s_prev is None or s_next is None:
            reasons.append("corner_mapping_failed:k%d" % k)
            continue
        if s_prev is s_next:
            reasons.append("corner_mapping_failed:same_segment:k%d" % k)
            continue
        len_prev = _dist(other_prev, C)
        len_next = _dist(other_next, C)
        # ---- replace_subpath（倒角阶梯）----
        s_max = 0.5 * min(len_prev, len_next)
        for s in CHAMFER_LADDER_MM:
            if s > s_max - 1e-9:
                reasons.append("chamfer_s_out_of_range:%s>%.3f" % (s, s_max))
                continue
            d1 = ((C[0] - other_prev[0]) / len_prev,
                  (C[1] - other_prev[1]) / len_prev)
            d2 = ((other_next[0] - C[0]) / len_next,
                  (other_next[1] - C[1]) / len_next)
            A = (C[0] - s * d1[0], C[1] - s * d1[1])
            B = (C[0] + s * d2[0], C[1] + s * d2[1])
            ok_obs, obs = _obstacle_free_triangle(A, C, B, fidx)
            if not ok_obs:
                reasons.append("obstacle_in_corner_region:%s:%s"
                               % (obs[0], obs[1]))
                continue
            cand = _chamfer_patch(chain, rid, k, s, A, C, B, width,
                                  s_prev, s_next, None, parsed)
            ok, why, r = _v41_gate(parsed, cand, v41pre)
            if not ok:
                reasons.append(why)
                continue
            cand["precheck"] = _v41_precheck_record(r)
            return cand, []
        # ---- move_vertex（轴对齐双单段腿限定）----
        prev_straight = abs(other_prev[0] - C[0]) < 1e-9 or \
            abs(other_prev[1] - C[1]) < 1e-9
        next_straight = abs(other_next[0] - C[0]) < 1e-9 or \
            abs(other_next[1] - C[1]) < 1e-9
        if not (prev_straight and next_straight):
            reasons.append("move_vertex_skipped:legs_not_axis_aligned")
            continue
        if len_prev < 0.5 or len_next < 0.5:
            reasons.append("move_vertex_skipped:legs_too_short")
            continue
        for step in MOVE_STEPS_MM:
            for (dx, dy) in MOVE_DIRS_8:
                Cp = (C[0] + step * dx, C[1] + step * dy)
                cand = _move_patch(chain, rid, k, step, (dx, dy), C, Cp,
                                   width, s_prev, s_next, other_prev,
                                   other_next, None, parsed)
                ok, why, r = _v41_gate(parsed, cand, v41pre)
                if not ok:
                    reasons.append("clearance_fail:move:%s" % why)
                    continue
                ok_obs, obs = _obstacle_free_triangle(other_prev, C,
                                                      other_next, fidx)
                if not ok_obs:
                    reasons.append("obstacle_in_corner_region:%s:%s"
                                   % (obs[0], obs[1]))
                    continue
                cand["precheck"] = _v41_precheck_record(r)
                return cand, []
    return None, reasons


def _chamfer_patch(chain, rid, k, s, A, C, B, width, s_prev, s_next,
                   min_d, parsed):
    del parsed
    return {
        "action_type": "replace_subpath",
        "patch_id": "P#%s#ch#S%02d#k%d" % (rid, chain["chain_no"], k),
        "net_id": chain["net"], "route_id": rid,
        "layer": chain["layer"], "width_mm": width,
        "polyline_mm": [[_q6(A[0]), _q6(A[1])], [_q6(B[0]), _q6(B[1])]],
        "old_subpath_mm": [[_q6(A[0]), _q6(A[1])], [_q6(C[0]), _q6(C[1])],
                           [_q6(B[0]), _q6(B[1])]],
        "corner_index": k, "s_mm": s,
        "fixed_endpoint_ids": ["open:%s:a" % rid, "open:%s:b" % rid],
        "parent_id": None, "relation_id": None,
        "reason": "corner chamfer (deterministic ladder s=%.2fmm); "
                  "shortens route, endpoints fixed" % s,
        "text_ops": {
            "modify": [
                {"uuid": s_prev["uuid"],
                 "replace_coord": [_q6(C[0]), _q6(C[1])],
                 "new_coord": [_q6(A[0]), _q6(A[1])]},
                {"uuid": s_next["uuid"],
                 "replace_coord": [_q6(C[0]), _q6(C[1])],
                 "new_coord": [_q6(B[0]), _q6(B[1])]},
            ],
            "insert_segment": {
                "net": chain["net"], "layer": chain["layer"],
                "width": width,
                "start": [_q6(A[0]), _q6(A[1])],
                "end": [_q6(B[0]), _q6(B[1])],
            },
        },
        "precheck": {"clearance_mm": CLEARANCE_MM,
                     "min_foreign_centerline_dist_mm": _q6(min_d or 0.0),
                     "corner_region_obstacle_free": True},
    }


def _move_patch(chain, rid, k, step, d, C, Cp, width, s_prev, s_next,
                other_prev, other_next, min_d, parsed):
    del parsed
    return {
        "action_type": "move_vertex",
        "patch_id": "P#%s#mv#S%02d#k%d" % (rid, chain["chain_no"], k),
        "net_id": chain["net"], "route_id": rid,
        "layer": chain["layer"], "width_mm": width,
        "moved_corner_index": k,
        "old_corner_mm": [_q6(C[0]), _q6(C[1])],
        "new_corner_mm": [_q6(Cp[0]), _q6(Cp[1])],
        "step_mm": step, "direction": list(d),
        "fixed_endpoint_ids": ["open:%s:a" % rid, "open:%s:b" % rid],
        "parent_id": None, "relation_id": None,
        "polyline_mm": None,  # 由编排侧按链折线重算填充
        "reason": "corner move (deterministic step=%.2fmm dir=%s); "
                  "endpoints fixed" % (step, d),
        "text_ops": {
            "modify": [
                {"uuid": s_prev["uuid"],
                 "replace_coord": [_q6(C[0]), _q6(C[1])],
                 "new_coord": [_q6(Cp[0]), _q6(Cp[1])]},
                {"uuid": s_next["uuid"],
                 "replace_coord": [_q6(C[0]), _q6(C[1])],
                 "new_coord": [_q6(Cp[0]), _q6(Cp[1])]},
            ],
            "insert_segment": None,
        },
        "precheck": {"clearance_mm": CLEARANCE_MM,
                     "min_foreign_centerline_dist_mm": _q6(min_d or 0.0)},
    }


# ---------------------------------------------------------------- 文本手术

def _top_spans(text, tag):
    """深度 1 指定 tag 顶层节点 [(start,end)]（括号平衡；board_writer 同法）。"""
    out = []
    depth = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif ch == "(":
            depth += 1
            if depth == 2:
                j = i + 1
                while j < n and text[j] not in " \t\r\n()":
                    j += 1
                if text[i + 1:j] == tag:
                    k2 = j
                    d = 1
                    instr = False
                    while k2 < n and d > 0:
                        c2 = text[k2]
                        if instr:
                            if c2 == "\\":
                                k2 += 2
                                continue
                            if c2 == '"':
                                instr = False
                        elif c2 == '"':
                            instr = True
                        elif c2 == "(":
                            d += 1
                        elif c2 == ")":
                            d -= 1
                        k2 += 1
                    out.append((i, k2))
                    depth -= 1
                    i = k2
                    continue
        elif ch == ")":
            depth -= 1
        i += 1
    return out


def _sub_span(node_text, tag):
    """节点文本内首个 (tag ...) 子节点 span。"""
    i = node_text.find("(%s" % tag)
    if i < 0:
        i = node_text.find("(%s " % tag)
    if i < 0:
        i = node_text.find("\n(%s" % tag)
    if i < 0:
        return None
    depth = 0
    j = i
    n = len(node_text)
    instr = False
    while j < n:
        ch = node_text[j]
        if instr:
            if ch == "\\":
                j += 2
                continue
            if ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return (i, j + 1)
        j += 1
    return None


def apply_patches(board_text, patches):
    """板文本 + patch 列表 → challenger 板文本（splice 手术；未触字节
    原样保留；新增段走 board_writer.apply_routes 落盘链，eol=auto）。"""
    from . import board_writer as bw
    edits = []
    inserts = []
    uuid_spans = None
    for p in patches:
        for mod in p["text_ops"]["modify"]:
            if uuid_spans is None:
                uuid_spans = {}
                for (a, b) in _top_spans(board_text, "segment"):
                    seg_text = board_text[a:b]
                    mu = re.search(r'\(uuid "([^"]+)"\)', seg_text)
                    if mu:
                        uuid_spans[mu.group(1)] = (a, b)
            if mod["uuid"] not in uuid_spans:
                raise ValueError("uuid %s 不在板文本（fail-closed）"
                                 % mod["uuid"])
            a, b = uuid_spans[mod["uuid"]]
            seg_text = board_text[a:b]
            target = None
            for tag in ("start", "end"):
                sp = _sub_span(seg_text, tag)
                if sp is None:
                    continue
                sub = seg_text[sp[0]:sp[1]]
                nums = [m for m in _NUM_RE.finditer(sub)]
                if len(nums) < 2:
                    continue
                x = float(nums[0].group())
                y = float(nums[1].group())
                if _pkey(x, y) == tuple(mod["replace_coord"]):
                    gx = nums[0].start() + sp[0] + a
                    gy = nums[1].start() + sp[0] + a
                    ge = nums[1].end() + sp[0] + a
                    target = (gx, gy, ge)
                    break
            if target is None:
                raise ValueError("段 %s 内未找到待替换坐标 %s（fail-closed）"
                                 % (mod["uuid"], mod["replace_coord"]))
            new_xy = "%.4f %.4f" % (mod["new_coord"][0], mod["new_coord"][1])
            edits.append((target[0], target[1], target[2], new_xy))
        ins = p["text_ops"].get("insert_segment")
        if ins:
            inserts.append(ins)
    edits.sort(key=lambda e: e[0], reverse=True)
    for (s0, s1, s2, rep) in edits:
        board_text = board_text[:s0] + rep + board_text[s2:]
    if inserts:
        routes = []
        for ins in inserts:
            li = LAYER_IDX[ins["layer"]]
            route = {
                "net": ins["net"],
                "segments": [(li, ins["start"][0], ins["start"][1],
                              ins["end"][0], ins["end"][1])],
                "vias": [],
                "width": ins["width"],
                "via_size": 0.6, "via_drill": 0.3,
            }
            route["uuid"] = _bw_route_uuid(route)
            routes.append(route)
        board_text = bw.apply_routes(board_text, routes, eol="auto")
    return board_text


# ---------------------------------------------------------------- 几何投影

def candidate_scope_geom(parsed, chains, net_ids, patches):
    """批网 scope 的 (baseline_geom, candidate_geom)（srp 可消费形状；
    vias=批网 via（池内网恒空，如实保留结构）。"""
    by_net = {}
    for c in chains:
        by_net.setdefault(c["net"], []).append(c)
    ordered = sorted(chains, key=lambda c: (c["net"], c["layer"],
                                            tuple(c["polyline"][0]),
                                            tuple(c["polyline"][-1])))
    cidx = {id(c): i + 1 for i, c in enumerate(ordered)}
    patches_by_route = {}
    for p in patches:
        patches_by_route[p["route_id"]] = p
    base_routes, cand_routes = [], []
    for net in net_ids:
        for chain in by_net.get(net, []):
            rid = _route_id(chain, cidx)
            width = chain["widths"][0]
            eps = ["open:%s:a" % rid, "open:%s:b" % rid]
            common = {
                "route_id": rid, "net_id": net,
                "relation_ids": [], "line_type": "signal",
                "layer": chain["layer"], "width_mm": width,
                "endpoint_ids": eps,
                "constraint_refs": ["C-clearance-%03d"
                                    % int(round(CLEARANCE_MM * 1000)),
                                    "C-width-%03d"
                                    % int(round(width * 1000))],
                "parent_id": None,
            }
            base_routes.append(dict(common, polyline_mm=chain["polyline"],
                                    state="baseline", source="baseline"))
            p = patches_by_route.get(rid)
            if p is None:
                cand_routes.append(dict(common,
                                        polyline_mm=chain["polyline"],
                                        state="baseline",
                                        source="baseline"))
            else:
                cand_routes.append(dict(
                    common, polyline_mm=_patched_polyline(chain, p),
                    state="candidate", source="solver"))
    net_set = set(net_ids)
    vias = []
    vi_sorted = sorted((v for v in parsed["vias"] if v["net"] in net_set),
                       key=lambda v: (v["x"], v["y"]))
    for i, v in enumerate(vi_sorted, 1):
        vias.append({
            "via_id": "V#%s#%03d" % (v["net"], i), "net_id": v["net"],
            "parent_id": None, "from_layer": v["l1"], "to_layer": v["l2"],
            "center_mm": [v["x"], v["y"]], "drill_mm": v["drill"],
            "annular_ring_mm": (v["size"] - v["drill"]) / 2.0,
            "state": "baseline", "source": "baseline",
        })
    return {"routes": base_routes, "vias": list(vias)}, \
        {"routes": cand_routes, "vias": list(vias)}


def _patched_polyline(chain, p):
    poly = [list(pt) for pt in chain["polyline"]]
    k = p["corner_index"]
    if p["action_type"] == "replace_subpath":
        A, B = p["polyline_mm"]
        new_poly = poly[:k] + [list(A), list(B)] + poly[k + 1:]
        return _compress(new_poly)
    if p["action_type"] == "move_vertex":
        new_poly = [list(pt) for pt in poly]
        new_poly[k] = list(p["new_corner_mm"])
        return _compress(new_poly)
    raise ValueError("未知动作 %s（fail-closed）" % p["action_type"])


def paired_metrics(base_geom, cand_geom, patches, net_ids):
    """协议 §criteria 目标指标：逐网长度/折角/segment 数配对差。"""
    def _by_net(geom):
        out = {}
        for r in geom["routes"]:
            out.setdefault(r["net_id"], []).append(r)
        return out

    def _polylen(poly):
        return sum(_dist(a, b) for a, b in zip(poly, poly[1:]))

    def _bends(poly):
        return max(0, len(poly) - 2)

    b, c = _by_net(base_geom), _by_net(cand_geom)
    per_net = []
    for net in net_ids:
        blen = sum(_polylen(r["polyline_mm"]) for r in b.get(net, []))
        clen = sum(_polylen(r["polyline_mm"]) for r in c.get(net, []))
        bbend = sum(_bends(r["polyline_mm"]) for r in b.get(net, []))
        cbend = sum(_bends(r["polyline_mm"]) for r in c.get(net, []))
        per_net.append({
            "net_id": net,
            "baseline_length_mm": round(blen, 4),
            "challenger_length_mm": round(clen, 4),
            "length_delta_mm": round(clen - blen, 4),
            "baseline_bends": bbend, "challenger_bends": cbend,
            "bend_delta": cbend - bbend,
            "actions": [p["action_type"] for p in patches
                        if p["net_id"] == net],
        })
    return {
        "per_net": per_net,
        "totals": {
            "length_delta_mm": round(sum(r["length_delta_mm"]
                                         for r in per_net), 4),
            "bend_delta": sum(r["bend_delta"] for r in per_net),
            "patched_nets": sum(1 for r in per_net if r["actions"]),
        },
    }
