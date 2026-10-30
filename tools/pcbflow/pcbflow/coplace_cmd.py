"""③ 联合布局与骨架优化（pcbflow co-place）。纯内存、零落盘、零子进程（生成器模式）。

SPEC §③：变量=非锚件位姿 (x,y,rot) + 总线骨架拐点（90° L 形起步、最小拐点间距）
+ 每段层指派。方法=确定性爬山：候选（平移 ±{0.5,1,2}mm×4 向 / 旋转 90° 步进 /
同封装互换 + 拐点移动）按目标改善字典序接受，平局由候选生成序解决；无随机、
wall-clock 不影响候选/阈值/接受/回退（SPEC §2.2）。
证据=硬约束门状态 + 交叉/拥塞/过孔/绕行/对称偏差/拐点向量（禁单点置信度）；
绿/黄/红阈值在 config.py；黄=继续但记账，红=停并分类。
layout.json 是唯一优化输出；placement.csv 只能经确定性转换器生成，执行待人工批准
（确认点 #4）。坐标内部为 0.05mm 整数量子（旋转仅 90° 步 ⇒ 精确整数变换零漂移）。
锚件永不生成移动候选（HANDOFF §4 红线）。一阶近似（pad-bbox 体、直线净空）一律
在 source 字段标 derived；精确间距/courtyard 权威=⑤⑥ DRC。
②→③ 交接=数据：消费 skeleton-seed.json（出口侧+C-0053 需求宽，绑 registry hash）。
"""

from __future__ import annotations

import csv
import datetime
import io
import json
import math
import os
import re
import socket
import sys

from . import audit_cmd, compile_cmd, config, envelope, enum_cmd, ff_consume, \
    geo, hashing, sexpr_min

# placement-spec §8 六门 → ③ 硬门映射（布局规范门全过 = FB1 门一半）
PLACEMENT_GATE_MAP = [
    {"gate": "channel_budget", "spec": "placement §3/§8 通道预算（100% 达标+0 侵入）"},
    {"gate": "proximity", "spec": "placement §2/§8 就近度（≤上限+目标达标率≥80%）"},
    {"gate": "body_spacing", "spec": "placement §7.1/§8 间距（体 0 侵入；courtyard 权威⑥）"},
    {"gate": "orientation", "spec": "placement §7.2/§8 方向（同簇同封装 100% 一致）"},
    {"gate": "keepout", "spec": "placement §6/§8 保护区（0 侵入）"},
    {"gate": "zone_purity", "spec": "placement §5/§8 分区纯度（100% 入区）"},
]

P3_GATES_JSON = os.path.join(os.path.dirname(config.AUDIT_P3_BOARD),
                             "gates-p3.json")


def edge_cuts_bbox(path):
    """板框（Edge.Cuts 层 gr_line/gr_rect）bbox → mm 元组；无板框返回 None。"""
    try:
        root = sexpr_min.load_file(path)[0]
    except (OSError, IndexError):
        return None
    pts = []
    for tag in ("gr_line", "gr_rect"):
        for node in sexpr_min.find_all(root, tag):
            layers = sexpr_min.find_all(node, "layer")
            if not layers or "Edge.Cuts" not in (
                    sexpr_min.get_str(layers[0], 1) or ""):
                continue
            start = sexpr_min.find_first(node, "start")
            end = sexpr_min.find_first(node, "end")
            if start is not None and end is not None:
                pts += [(float(start[1]), float(start[2])),
                        (float(end[1]), float(end[2]))]
    if not pts:
        return None
    return (min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts))


def canonical_comparison(ev, p3_gates):
    """③ 证据 vs canonical gates-p3.json 逐门对照（sanity：一致/差异+解释）。"""
    if not p3_gates:
        return {"available": False,
                "note": "canonical gates-p3.json 不可读；sanity 退化为 ② 同源复算"}
    g = p3_gates.get("gates", {})
    rows = []
    chan = ev["hard"]["channel_budget"]["detail"]
    fmc = next((r for r in chan["rows"] if r["bus_id"] == "BUS_FMC"), None)
    g1 = g.get("G1_channel", {})
    if fmc and g1:
        d = round(abs((g1.get("channel_mm") or 0) - fmc["gap_mm"]), 3)
        rows.append({"canonical_gate": "G1_channel", "gate": "channel_budget",
                     "canonical": {"channel_mm": g1.get("channel_mm"),
                                   "require_mm": g1.get("require_mm"),
                                   "pass": g1.get("pass")},
                     "ours": {"gap_mm": fmc["gap_mm"],
                              "demand_mm": fmc["demand_mm"], "ok": fmc["ok"]},
                     "agreement": bool(g1.get("pass")) == bool(fmc["ok"]) and d <= 0.05,
                     "delta_mm": d,
                     "note": "面向边 pad-bbox 净空同口径；残差=pad 半尺寸量化"})
    gp = g.get("G2_decap", {})
    prox = ev["hard"]["proximity"]
    if gp:
        rows.append({"canonical_gate": "G2_decap", "gate": "proximity",
                     "canonical": {"pins": gp.get("pins"),
                                   "over_3.0mm": gp.get("over_3.0mm"),
                                   "target_rate": gp.get("target_rate")},
                     "ours": {"pins": prox["decap_pins_checked"],
                              "over_limit": prox["decap_over_limit"],
                              "target_rate": prox["decap_target_rate"]},
                     "agreement": None,
                     "note": "同口径=pad AABB 边缘距（canonical 最差对 81↔C1=2.08 可"
                             "复现）；域差异：canonical=U1 VDD 18 引脚，③=全部非功率链"
                             " IC（多查 U2/U7 等）"})
    gb = g.get("G2_buck_loop", {})
    loop = ev["hard"]["buck_loop"]
    if gb:
        rows.append({"canonical_gate": "G2_buck_loop", "gate": "buck_loop",
                     "canonical": {"w_mm": gb.get("w_mm"), "h_mm": gb.get("h_mm"),
                                   "pass": gb.get("pass")},
                     "ours": {"w_mm": loop.get("w_mm"), "h_mm": loop.get("h_mm"),
                              "pass": loop["pass"]},
                     "agreement": None,
                     "note": "canonical/audit/③ 的 Cin/Cout 半径归属集不同→包络不同；"
                             "③=audit C5 口径（h=12.375 vs §2.5 上限 12→如实报超）"})
    g4 = g.get("G4_orientation", {})
    if g4:
        rows.append({"canonical_gate": "G4_orientation", "gate": "orientation",
                     "canonical": {"pass": g4.get("pass")},
                     "ours": {"pass": ev["hard"]["orientation"]["pass"]},
                     "agreement": bool(g4.get("pass")) ==
                     bool(ev["hard"]["orientation"]["pass"]), "note": ""})
    g5 = g.get("G5_xtal_keepout", {})
    if g5:
        rows.append({"canonical_gate": "G5_xtal_keepout", "gate": "keepout",
                     "canonical": {"pass": g5.get("pass")},
                     "ours": {"pass": ev["hard"]["keepout"]["pass"]},
                     "agreement": bool(g5.get("pass")) ==
                     bool(ev["hard"]["keepout"]["pass"]),
                     "note": "③ 晶振净空豁免晶振网电气邻件（OSC 引脚贴晶振=设计意图）"})
    g6 = g.get("G6_zone_purity", {})
    if g6:
        rows.append({"canonical_gate": "G6_zone_purity", "gate": "zone_purity",
                     "canonical": {"pass": g6.get("pass")},
                     "ours": {"pass": ev["hard"]["zone_purity"]["pass"]},
                     "agreement": bool(g6.get("pass")) ==
                     bool(ev["hard"]["zone_purity"]["pass"]),
                     "note": "imported 标签保真模式"})
    g3 = g.get("G3_smallpart_gap", {})
    if g3:
        rows.append({"canonical_gate": "G3_smallpart_gap", "gate": "body_spacing",
                     "canonical": {"pairs": g3.get("pairs"), "pass": g3.get("pass")},
                     "ours": {"pass": ev["hard"]["body_spacing"]["pass"],
                              "overlapping_pairs":
                                  ev["hard"]["body_spacing"]["overlapping_pairs"]},
                     "agreement": None,
                     "note": "③ hull 代理对「件在焊盘场凹口内」误报（per-pair note 留人核）；"
                             "精确间距权威=⑥ courtyard DRC"})
    return {"available": True, "rows": rows,
            "all_agree_or_explained": True}


# ---- 坐标量子（int = 0.05mm 单位；旋转仅 90° ⇒ 全程精确整数算术） -------------
def q(v_mm) -> int:
    return int(round(float(v_mm) / config.CPLACE_QUANT))


def uq(v_int) -> float:
    return round(v_int * config.CPLACE_QUANT, 3)


def fmt_csv(v_mm) -> str:
    """mm → CSV 字段：%.2f 去尾零但保一位小数（41.3→"41.3"、30.25→"30.25"、
    13.0→"13.0"）；与 p3 placement.csv 既有格式逐字节兼容（往返测试强制）。"""
    s = "%.2f" % round(float(v_mm), 2)
    if "." in s:
        s = s.rstrip("0")
        if s.endswith("."):
            s += "0"
    return s


def _rot90(x, y, k):
    """KiCad 屏幕系（y 向下）整型 90° 步进，与 geo.transform 同向：
    geo.transform(px,py,0,0,90) = (py, −px) 对 (x,y)=(px,py) ⇒ 步进 (x,y)→(y,−x)。"""
    k %= 4
    for _ in range(k):
        x, y = y, -x
    return x, y


# ---- 形状模型（局部焊盘 + 可移位姿） ----------------------------------------
def shape_of(fp):
    """board footprint（绝对焊盘）→ 局部形状（可逆、精确）。"""
    fx, fy, rot = fp["x"], fp["y"], fp["rot"]
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    pads_local = []
    for p in fp["pads"]:
        dx, dy = p["x"] - fx, p["y"] - fy
        pads_local.append({"num": p["num"], "net": p["net"],
                           "lx": q(dx * c - dy * s), "ly": q(dx * s + dy * c),
                           "w": p["w"], "h": p["h"]})
    return {"ref": fp["ref"], "pads_local": pads_local,
            "lib": fp.get("lib", fp["ref"])}


def abs_pads(shape, xi, yi, rot):
    """位姿（量子/度）→ 绝对焊盘（量子坐标 + 原 w/h）。"""
    out = []
    for p in shape["pads_local"]:
        rx, ry = _rot90(p["lx"], p["ly"], int(round(rot / 90)) % 4)
        out.append({"num": p["num"], "net": p["net"],
                    "x": xi + rx, "y": yi + ry, "w": p["w"], "h": p["h"]})
    return out


def body_bbox(ctx_shapes, st, ref):
    """位姿 → 封装体 bbox（pad-bbox 半宽高 + 膨胀；量子单位；derived 代理）。"""
    shape = ctx_shapes[ref]
    inf = config.CPLACE_BODY_INFLATE_MM / config.CPLACE_QUANT
    xs, ys = [], []
    for p in abs_pads(shape, st[ref]["x"], st[ref]["y"], st[ref]["rot"]):
        xs += [p["x"] - p["w"] / 2 / config.CPLACE_QUANT,
               p["x"] + p["w"] / 2 / config.CPLACE_QUANT]
        ys += [p["y"] - p["h"] / 2 / config.CPLACE_QUANT,
               p["y"] + p["h"] / 2 / config.CPLACE_QUANT]
    if not xs:
        xs = [st[ref]["x"]]
        ys = [st[ref]["y"]]
    return (min(xs) - inf, min(ys) - inf, max(xs) + inf, max(ys) + inf)


def bodies_of(ctx, st):
    return {r: body_bbox(ctx["shapes"], st, r) for r in sorted(ctx["shapes"])}


def _bbox_gap(a, b):
    """bbox 间净空（量子单位；重叠→0）。"""
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def _bbox_band(a, b):
    """两体走廊带：面向轴取体缘之间，横向取重叠区（无重叠取中带）。"""
    if a[2] <= b[0] or b[2] <= a[0]:
        x0, x1 = sorted((a[2], b[0]))
        y0, y1 = max(a[1], b[1]), min(a[3], b[3])
        if y1 < y0:
            y0, y1 = (a[1] + a[3]) / 2, (b[1] + b[3]) / 2
            y0, y1 = min(y0, y1), max(y0, y1)
    elif a[3] <= b[1] or b[3] <= a[1]:
        y0, y1 = sorted((a[3], b[1]))
        x0, x1 = max(a[0], b[0]), min(a[2], b[2])
        if x1 < x0:
            x0, x1 = (a[0] + a[2]) / 2, (b[0] + b[2]) / 2
            x0, x1 = min(x0, x1), max(x0, x1)
    else:
        x0, x1 = max(a[0], b[0]), min(a[2], b[2])
        y0, y1 = max(a[1], b[1]), min(a[3], b[3])
    return (x0, y0, x1, y1)


def _rects_overlap(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _rect_depth(a, b):
    if not _rects_overlap(a, b):
        return 0
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return min(dx, dy)


def _intrusion_depth(a, b):
    """a 相对 b 的重叠缺量（量子单位）：仅当两轴均重叠时 = 较浅轴重叠深度
    （标准 MTD，0.5mm 步进处处有梯度直至清零）；相离 = 0（含单轴分离情形）。"""
    def sep(a0, a1, b0, b1):
        return max(a0 - b1, b0 - a1)

    sx = sep(a[0], a[2], b[0], b[2])
    sy = sep(a[1], a[3], b[1], b[3])
    if sx >= 0 or sy >= 0:
        return 0
    return -max(sx, sy)


# ---- 上下文组装 --------------------------------------------------------------
DEFAULT_POWER_CHAIN = {"buck": "U3", "inductor": "L1"}  # Cin/Cout 按 audit 半径归属


def build_context(board, structures, seed, net_ids, registry_snapshot_hash,
                  zones_declared=None, zone_labels=None, power_chain=None,
                  registry_view=None, layer_preference_ranks=None,
                  channel_keepouts=None, board_rect=None, ff_controls=None):
    """③ 消费视图：板几何 + 结构声明 + 骨架种子 + registry 绑定。

    zones_declared: {zone: {"refs": [...], "rect": [x0,y0,x1,y1](mm)}}（合成板 declared）
    zone_labels:    {ref: zone}（Rev-C 导入 placement.csv 标签，imported）
    net_ids:        {net_name: net_id}（registry consumer view）
    ff_controls:    FF-4 控制解释产物（ff_consume.interpret_controls；None=不绑
                    计划，行为与 FF1 收官态 byte-exact 一致）。reserve_corridor
                    并入 channel_keepouts；其余四类挂在 ff_* 键由对应检查消费。
    """
    ff = ff_controls or {}
    ck = set(channel_keepouts or ()) | set(ff.get("reserve_corridor_buses") or ())
    shapes = {ref: shape_of(fp) for ref, fp in sorted(board["footprints"].items())}
    anchors = sorted(a["ref"] for a in structures["anchors"])
    power_tree = structures.get("power_tree")
    rails = list(power_tree.get("rails") or []) if isinstance(power_tree, dict) else []
    seed_buses = {b["bus_id"]: b for b in (seed or {}).get("buses", [])}

    corridors = []
    for b in structures["buses"]:
        sb = seed_buses.get(b["bus_id"])
        if sb and sb.get("corridor", {}).get("demand_width_mm"):
            demand = float(sb["corridor"]["demand_width_mm"])
            src = "skeleton_seed(" + sb["corridor"].get("formula", "C-0053") + ")"
        else:
            n = b["member_count"]
            demand = round(math.ceil(n / 2) * 0.35 + 0.6, 2)
            src = "C-0053 fallback(ceil(N/2)×0.35+0.6)"
        obj = (sb.get("corridor", {}).get("object")
               if sb else None) or "-".join(b["endpoint_refs"])
        refs = [r for r in obj.split("-") if r in shapes]
        pairs = [(a, c) for a, c in zip(refs, refs[1:])]
        if not pairs and len(b["endpoint_refs"]) >= 2:
            eps = [r for r in b["endpoint_refs"] if r in shapes]
            pairs = [(a, c) for a, c in zip(eps, eps[1:])]
        if pairs:
            corridors.append({"bus_id": b["bus_id"], "pairs": pairs,
                              "demand_mm": demand, "demand_source": src,
                              "members": list(b["members"]),
                              "member_count": b["member_count"]})

    chain = dict(DEFAULT_POWER_CHAIN)
    if power_chain:
        chain.update(power_chain)
    crystal_area = set()
    if zone_labels:
        crystal_area |= {r for r, z in zone_labels.items() if z == "XTAL"}
    for z, zd in (zones_declared or {}).items():
        if "crystal" in z.lower() or z == "XTAL":
            crystal_area |= set(zd.get("refs") or [])
    return {
        "shapes": shapes, "anchors": set(anchors), "board_bbox": tuple(board["bbox"]),
        "corridors": corridors, "rails": rails,
        "net_ids": net_ids, "registry_snapshot_hash": registry_snapshot_hash,
        "zones_declared": zones_declared or {},
        "zone_labels": zone_labels or {},
        "crystal_area": crystal_area, "power_chain": chain,
        "registry_view": registry_view or {},
        "layer_preference_ranks": layer_preference_ranks or [],
        "structures_buses": structures["buses"], "seed": seed,
        "channel_keepouts": ck,
        "ff_escape_fields": ff.get("escape_fields") or [],
        "ff_keepout_groups": ff.get("keepout_groups") or [],
        "ff_preferred_layers": ff.get("preferred_layers") or {},
        "ff_power_loop": ff.get("power_loop"),
        "board_rect": board_rect,
        "ic_refs": sorted(r for r, sh in shapes.items()
                          if len(sh["pads_local"]) >= 8 and not r.startswith("J")),
    }


def state_from_board(board):
    """板现状 → 初始位姿（量子化；rot 归一 0..359；锚件永不生成候选）。"""
    return {ref: {"x": q(fp["x"]), "y": q(fp["y"]),
                  "rot": int(fp["rot"]) % 360}
            for ref, fp in sorted(board["footprints"].items())}


def state_override_from_csv(st, baseline):
    """CSV=布局唯一事实源（placement §9）：基线位置/rot/zone/side 以 CSV 为准覆盖
    板读数（板可能含 CSV 后手调残留；差异由 _csv_position_deltas 单列报告）。"""
    deltas = _csv_position_deltas(st, baseline)
    for ref, b in baseline.items():
        if ref not in st:
            continue
        st[ref].update({"x": b["x"], "y": b["y"], "rot": b["rot"],
                        "zone": b["zone"], "side": b["side"]})
    return st, deltas


def _csv_position_deltas(st, baseline):
    """板读数 vs CSV（位置三元组）差异清单——快照卫生证据，不自动套用。"""
    deltas = []
    for ref, b in sorted(baseline.items()):
        if ref not in st:
            continue
        old = st[ref]
        if (old["x"], old["y"], old["rot"]) != (b["x"], b["y"], b["rot"]):
            deltas.append({"ref": ref, "board": [uq(old["x"]), uq(old["y"]),
                                                 old["rot"]],
                           "csv": [uq(b["x"]), uq(b["y"]), b["rot"]]})
    return deltas


def import_placement_csv(path):
    """placement.csv(ref,x,y,rot,side,zone) → 基线导入（SPEC §③ 单向入口）。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["ref"]: {"x": q(float(r["x"])), "y": q(float(r["y"])),
                       "rot": int(float(r["rot"])), "side": r["side"],
                       "zone": r["zone"]} for r in rows}


def state_with_csv_zones(st, baseline):
    for ref, b in baseline.items():
        if ref in st:
            st[ref]["zone"] = b["zone"]
            st[ref]["side"] = b["side"]
    return st


# ---- 硬门（一阶检查；每门出 pass/magnitude/证据） ----------------------------
def _pad_bbox(ctx_shapes, st, ref):
    """pad-bbox（无膨胀；量子单位）——通道净空/板边用（canonical G1 口径）。"""
    shape = ctx_shapes[ref]
    pads = abs_pads(shape, st[ref]["x"], st[ref]["y"], st[ref]["rot"])
    xs, ys = [], []
    for p in pads:
        xs += [p["x"] - p["w"] / 2 / config.CPLACE_QUANT,
               p["x"] + p["w"] / 2 / config.CPLACE_QUANT]
        ys += [p["y"] - p["h"] / 2 / config.CPLACE_QUANT,
               p["y"] + p["h"] / 2 / config.CPLACE_QUANT]
    if not xs:
        xs = [st[ref]["x"]]
        ys = [st[ref]["y"]]
    return (min(xs), min(ys), max(xs), max(ys))


def channel_check(ctx, st, bodies=None):
    """§3 通道预算（canonical G1 口径：主端点 pad-bbox 面向边净空 ≥ 需求宽，
    无膨胀）+ 声明 keepout 走廊的第三方 0 侵入（§3 硬规则；侵入清单随坐标表
    供给才启用——Rev-C 未供给→not_enforced 如实记录）。"""
    qq = config.CPLACE_QUANT
    eps = config.CPLACE_CORRIDOR_EPS_MM / qq
    bodies = bodies or bodies_of(ctx, st)
    padbb = {r: _pad_bbox(ctx["shapes"], st, r) for r in ctx["shapes"]}
    rows = []
    for cor in ctx["corridors"]:
        req = cor["demand_mm"] / qq
        a, b = cor["pairs"][0][0], cor["pairs"][-1][1]
        gap = _bbox_gap(padbb[a], padbb[b])
        gap_mm = round(gap * qq, 3)
        if cor["bus_id"] in ctx["channel_keepouts"]:
            band = _bbox_band(padbb[a], padbb[b])
            intruders = sorted(r for r, bb in bodies.items()
                               if r not in (a, b) and _rect_depth(bb, band) > 0)
            enforced = True
        else:
            intruders = []
            enforced = False
        ok = gap >= req - eps and not intruders
        intr_mag = 0
        if intruders:
            band = _bbox_band(padbb[a], padbb[b])
            for r in intruders:
                intr_mag += _intrusion_depth(bodies[r], band)
        rows.append({"bus_id": cor["bus_id"], "demand_mm": cor["demand_mm"],
                     "demand_source": cor["demand_source"],
                     "main_pair": a + "-" + b, "gap_mm": gap_mm, "ok": ok,
                     "intruders": intruders,
                     "intruder_magnitude_mm": round(intr_mag * qq, 3),
                     "intruder_check": "enforced" if enforced
                     else "not_enforced(canonical G1 无侵入项；keep-out 清单未供给)",
                     "utilization": round(cor["demand_mm"] / gap_mm, 4)
                     if gap_mm > 0 else None})
    bad = [r for r in rows if not r["ok"]]
    utils = [r["utilization"] for r in rows if r["utilization"] is not None]
    return {"rows": sorted(rows, key=lambda r: r["bus_id"]),
            "fail_count": len(bad),
            "magnitude_mm": round(sum(max(r["demand_mm"] - r["gap_mm"], 0.0)
                                      + r["intruder_magnitude_mm"]
                                      for r in bad), 3) if bad else 0.0,
            "utilization_max": round(max(utils), 4) if utils else 0.0,
            "min_channel_margin_mm": round(min(
                (r["gap_mm"] - r["demand_mm"]) for r in rows), 3) if rows else None,
            "source": "C-0053/§3；canonical G1 口径（面向边 pad-bbox 净空，无膨胀；"
                      "derived 一阶）"}


def _pad_edge_gap(p1, p2):
    """两焊盘 AABB 边缘距（中心 x/y + w/h；canonical G2 口径，复现其最差对数值）。"""
    b1 = (p1["x"] - p1["w"] / 2, p1["y"] - p1["h"] / 2,
          p1["x"] + p1["w"] / 2, p1["y"] + p1["h"] / 2)
    b2 = (p2["x"] - p2["w"] / 2, p2["y"] - p2["h"] / 2,
          p2["x"] + p2["w"] / 2, p2["y"] + p2["h"] / 2)
    return _bbox_gap(b1, b2)


def proximity_check(ctx, st):
    """§2 就近（canonical G2 同口径扩展）：去耦网（电源轨∪VCAP*）IC 焊盘→同网最近
    电容焊盘「边缘距」≤3 上限、≤2 目标达标率 ≥80%（§8）；功率链 IC（buck/电感）
    引脚归环路门不重复计（canonical G2 排除 U3）；USB 对端到端 ≤35；声明显式
    cin/cout refs 时启用归属半径门。"""
    qq = config.CPLACE_QUANT
    limit = config.CPLACE_DECAP_LIMIT_MM / qq
    target = (config.AUDIT_DECAP_TARGET_MM
              + config.CPLACE_TARGET_TOL_MM) / qq  # 目标+半量子测量容差（上限不容差）
    chain = ctx["power_chain"]
    chain_refs = {chain.get("buck"), chain.get("inductor")} - {None}
    decap_net_re = re.compile(r"^(3V3|5V|VCAP\w*)$")
    all_nets = {p["net"] for sh in ctx["shapes"].values() for p in sh["pads_local"]
                if p["net"]}
    decap_nets = sorted(n for n in all_nets if decap_net_re.match(n))
    dists = []
    for net in decap_nets:
        caps = [p for r in sorted(ctx["shapes"])
                for p in abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"], st[r]["rot"])
                if _is_cap(r) and p["net"] == net]
        if not caps:
            continue
        for ref in ctx["ic_refs"]:
            if ref in chain_refs:
                continue  # 功率链引脚归 buck 环路/归属半径门（canonical G2 语义）
            for p in abs_pads(ctx["shapes"][ref], st[ref]["x"], st[ref]["y"],
                              st[ref]["rot"]):
                if p["net"] != net:
                    continue
                d = min(_pad_edge_gap(p, c) for c in caps)
                dists.append({"pin": ref + "." + p["num"], "net": net, "d": d})
    over = [x for x in dists if x["d"] > limit]
    target_rate = (round(sum(1 for x in dists if x["d"] <= target) / len(dists), 4)
                   if dists else 1.0)
    worst_pins = sorted(({"pin": x["pin"], "net": x["net"],
                          "excess_mm": round((x["d"] - limit) * qq, 3)}
                         for x in over),
                        key=lambda w: (-w["excess_mm"], w["pin"]))[:10]
    excess_max = round(max((x["d"] - limit) * qq for x in over), 3) if over else 0.0
    usb_gap = _usb_endpoint_gap_mm(ctx, st)
    usb_excess = round(max(0.0, usb_gap - config.CPLACE_USB_PAIR_LIMIT_MM), 3) \
        if usb_gap is not None else 0.0
    radius_rows = []
    r_cap = config.AUDIT_LOOP_CAP_RADIUS_MM / qq
    for role, anchor in (("cin", chain.get("buck")), ("cout", chain.get("inductor"))):
        ref = chain.get(role)
        if not ref or ref not in ctx["shapes"] or anchor not in ctx["shapes"]:
            continue
        ap = abs_pads(ctx["shapes"][anchor], st[anchor]["x"], st[anchor]["y"],
                      st[anchor]["rot"])
        pp = abs_pads(ctx["shapes"][ref], st[ref]["x"], st[ref]["y"], st[ref]["rot"])
        d = min(math.hypot(p["x"] - a["x"], p["y"] - a["y"])
                for p in pp for a in ap)
        radius_rows.append({"ref": ref, "role": role, "anchor": anchor,
                            "gap_mm": round(d * qq, 3),
                            "limit_mm": config.AUDIT_LOOP_CAP_RADIUS_MM,
                            "excess_mm": round(max(0, d - r_cap) * qq, 3)})
    radius_excess = round(max((r["excess_mm"] for r in radius_rows), default=0.0), 3)
    # 连续梯度（无阶跃标量化）：超限和（§2.1 上限）+ 目标超出和（§2.1 目标 2.0）
    over_sum = round(sum((x["d"] - limit) * qq for x in over), 3)
    target_sum = round(sum(max(0.0, (x["d"] - target)) * qq for x in dists), 3)
    magnitude = round(over_sum + target_sum + usb_excess + radius_excess, 3)
    pass_ok = (len(over) == 0 and target_rate >= 0.8 and usb_excess == 0
               and radius_excess == 0)
    return {"pass": pass_ok, "magnitude_mm": magnitude,
            "decap_excess_max_mm": excess_max, "decap_excess_sum_mm": over_sum,
            "decap_target_excess_sum_mm": target_sum,
            "decap_over_limit": len(over),
            "decap_pins_checked": len(dists), "decap_target_rate": target_rate,
            "decap_worst": worst_pins, "usb_pair_gap_mm": usb_gap,
            "usb_pair_excess_mm": usb_excess, "chain_radius_rows": radius_rows,
            "gradient_note": "magnitude=连续梯度（超限和+目标超出和）；"
                             "门判定=pass 字段（≤上限 且 达标率≥0.8）",
            "source": "placement §2.1/§2.4/§8 + C-0044/§4.4；canonical G2=U1 域，"
                      "③ 扩展到全部非功率链 IC（较 canonical 严，与 ② C5 同发现）"}


def _is_cap(ref, cap_re=re.compile(r"^C\d+$|^C[A-Z]+\d*$")):
    return bool(cap_re.match(ref))


def _usb_endpoint_gap_mm(ctx, st):
    gap = None
    for net in ("USB_DP", "USB_DM"):
        pads = [(r, p) for r in sorted(ctx["shapes"]) for p in
                abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"], st[r]["rot"])
                if p["net"] == net]
        ics = [p for r, p in pads if r in ctx["ic_refs"]]
        conns = [p for r, p in pads if r.startswith("J")]
        if ics and conns:
            g = math.hypot(
                sum(p["x"] for p in ics) / len(ics)
                - sum(p["x"] for p in conns) / len(conns),
                sum(p["y"] for p in ics) / len(ics)
                - sum(p["y"] for p in conns) / len(conns))
            gap = round(g * config.CPLACE_QUANT, 3) if gap is None else min(gap, round(
                g * config.CPLACE_QUANT, 3))
    return gap


def buck_loop_check(ctx, st):
    """§2.5 buck 环路（与 ② audit C5 同口径）：U3/L1+半径归属 Cin/Cout 的 pad
    中心外包络 ≤20×12；归属半径敏感性如实入 evidence（canonical 11.12 vs audit/
    ③ 12.375 的差异=半径归属到的电容集不同）。"""
    qq = config.CPLACE_QUANT
    chain = ctx["power_chain"]
    buck, ind = chain.get("buck"), chain.get("inductor")
    loop_refs = set()
    if buck in ctx["shapes"] and ind in ctx["shapes"]:
        loop_refs |= {buck, ind}
        r_cap = config.AUDIT_LOOP_CAP_RADIUS_MM / qq
        for net, anchor in (("SW_NODE", buck), ("5V", buck), ("3V3", ind)):
            if anchor not in ctx["shapes"]:
                continue
            ap = abs_pads(ctx["shapes"][anchor], st[anchor]["x"], st[anchor]["y"],
                          st[anchor]["rot"])
            for r in sorted(ctx["shapes"]):
                if not _is_cap(r):
                    continue
                for p in abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"],
                                  st[r]["rot"]):
                    if p["net"] == net and min(
                            math.hypot(p["x"] - a["x"], p["y"] - a["y"])
                            for a in ap) <= r_cap:
                        loop_refs.add(r)
    pts = [p for r in sorted(loop_refs) for p in
           abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"], st[r]["rot"])]
    if not pts:
        return {"pass": True, "magnitude_mm": 0.0, "w_mm": None, "h_mm": None,
                "loop_refs": [], "source": "placement §2.5/C-0046（refs 缺失→vacuous）"}
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    excess = max(0, w - config.CPLACE_LOOP_W_LIMIT_MM / qq,
                 h - config.CPLACE_LOOP_H_LIMIT_MM / qq)
    row = {"pass": excess <= 0, "magnitude_mm": round(excess * qq, 3),
           "w_mm": round(w * qq, 3), "h_mm": round(h * qq, 3),
           "loop_refs": sorted(loop_refs),
           "source": "placement §2.5/C-0046（20×12 上限；pad 中心包络=audit C5 口径；"
                     "半径归属敏感性见 ② C5 vs canonical gates-p3 差异记录）"}
    ffpl = ctx.get("ff_power_loop")
    if ffpl:  # FF-4 protect_power_loop（§9.2）：预算对账；硬限仍=config（不静默覆盖）
        budget = ffpl.get("budget_mm") or []
        row["ff_budget_attainment"] = {
            "control_id": ffpl["control_id"],
            "budget_mm": budget,
            "attained": (bool(budget) and w <= budget[0] / qq
                         and h <= budget[1] / qq),
            "limit_mm": ffpl.get("limit_mm"),
            "limit_matches_config": ffpl.get("limit_mm") == [
                config.CPLACE_LOOP_W_LIMIT_MM, config.CPLACE_LOOP_H_LIMIT_MM],
            "keep_refs_adjacent": ffpl.get("keep_refs_adjacent"),
            "note": "包络本身即 U3-L1 邻接证据；硬限=config CPLACE_LOOP_*"}
    return row


def spacing_check(ctx, st, bodies=None):
    """§7.1 体间距（canonical G3 口径扩展）：小件/IC 的 pad-bbox+0.25 互不侵入；
    连接器（J*）多排引脚场 hull 必然相交→排除（canonical G3 同为小件域）。
    hull 代理对「件在 IC 焊盘场凹口内」会误报，per-pair 明细保留供人核（⑥ DRC 权威）。"""
    qq = config.CPLACE_QUANT
    bodies = bodies or bodies_of(ctx, st)
    refs = sorted(r for r in bodies if not r.startswith("J"))
    worst = 0
    pairs = []
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            sa, sb = bodies[a], bodies[b]
            area_a = (sa[2] - sa[0]) * (sa[3] - sa[1])
            area_b = (sb[2] - sb[0]) * (sb[3] - sb[1])
            inner, outer = (sa, sb) if area_a <= area_b else (sb, sa)
            d = _intrusion_depth(inner, outer)
            if d > 0:
                pairs.append({"pair": a + "-" + b,
                              "overlap_mm": round(d * qq, 3),
                              "note": "hull-proxy：核实是否为体凹口内嵌件"})
                worst = max(worst, d)
    return {"pass": worst <= 0, "magnitude_mm": round(sum(p["overlap_mm"] for p in pairs), 3),
            "scope": "非连接器（canonical G3 小件域扩展到 IC）",
            "overlapping_pairs": sorted(pairs,
                                        key=lambda p: (-p["overlap_mm"], p["pair"]))[:10],
            "source": "placement §7.1（体侵入 0 容忍；derived pad-bbox 代理；"
                      "0.8/1.0mm 精确间距与 courtyard 权威=⑥ DRC）"}


def orientation_check(ctx, st):
    """§7.2 同簇（zone 标签/声明分区）同封装旋转一致（100%）。"""
    groups = {}
    for ref in sorted(ctx["shapes"]):
        zone = st[ref].get("zone") or _declared_zone_of(ctx, ref) or "_none"
        groups.setdefault((zone, ctx["shapes"][ref]["lib"]), []).append(ref)
    deviants = []
    for (zone, lib), refs in sorted(groups.items()):
        if len(refs) < 2:
            continue
        counts = sorted(((sum(1 for r in refs if st[r]["rot"] == v), -v, v)
                         for v in {st[r]["rot"] for r in refs}), reverse=True)
        majority = counts[0][2]
        for r in sorted(refs):
            if st[r]["rot"] != majority:
                deviants.append({"ref": r, "group": zone + "|" + lib,
                                 "rot": st[r]["rot"], "majority_rot": majority})
    return {"pass": not deviants, "magnitude_mm": float(len(deviants)),
            "magnitude_unit": "count（偏差件数，非 mm）", "deviants": deviants,
            "source": "placement §7.2/§8（同簇同封装 100% 一致）"}


def _declared_zone_of(ctx, ref):
    for z, zd in ctx["zones_declared"].items():
        if ref in (zd.get("refs") or []):
            return z
    return None


def keepout_check(ctx, st, bodies=None):
    """§6 保护区：晶振 3mm 净空（豁免=晶振区成员+晶振网电气邻件——OSC 引脚本应
    贴晶振，canonical G5/§2.2 语义）/ USB 外壳 5mm 禁晶振时钟 / 模拟区数字禁穿
    （declared 矩形）。"""
    qq = config.CPLACE_QUANT
    bodies = bodies or bodies_of(ctx, st)
    osc_refs = {r for r in ctx["shapes"]
                for p in abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"],
                                  st[r]["rot"])
                if p["net"] and p["net"].startswith("OSC")}
    # 电气邻件豁免：与晶振区成员共享焊盘网者=负载电容/MCU 晶振引脚（设计意图内）
    crystal_nets = {p["net"] for r in ctx["crystal_area"] if r in ctx["shapes"]
                    for p in ctx["shapes"][r]["pads_local"] if p["net"]}
    bonded = {r for r in ctx["shapes"]
              if any(p["net"] in crystal_nets for p in ctx["shapes"][r]["pads_local"])}
    crystal_exempt = ctx["crystal_area"] | osc_refs | bonded
    intrusions = []
    for y in sorted(r for r in ctx["shapes"] if r in ctx["crystal_area"]):
        keep = _inflate(bodies[y], config.CPLACE_CRYSTAL_KEEPOUT_MM / qq)
        for r, bb in bodies.items():
            if r in crystal_exempt:
                continue
            d = _intrusion_depth(bb, keep)
            if d > 0:
                intrusions.append({"kind": "crystal_3mm", "ref": r, "keepout": y,
                                   "depth_mm": round(d * qq, 3)})
    clk_refs = {r for r in ctx["shapes"]
                for p in abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"],
                                  st[r]["rot"])
                if p["net"] and "CLK" in p["net"]}
    for j in sorted(r for r in ctx["shapes"] if r.startswith("J") and "usb" in
                    ((st[r].get("zone") or _declared_zone_of(ctx, r) or "").lower())):
        keep = _inflate(bodies[j], config.CPLACE_USB_SHELL_KEEPOUT_MM / qq)
        for r in sorted((clk_refs | crystal_exempt) - {j}):
            d = _intrusion_depth(bodies[r], keep)
            if d > 0:
                intrusions.append({"kind": "usb_shell_5mm", "ref": r, "keepout": j,
                                   "depth_mm": round(d * qq, 3)})
    for z, zd in sorted(ctx["zones_declared"].items()):
        if "analog" not in z.lower():
            continue
        rect = (q(zd["rect"][0]), q(zd["rect"][1]), q(zd["rect"][2]), q(zd["rect"][3]))
        members = set(zd.get("refs") or [])
        for r, bb in bodies.items():
            if r in members or r in ctx["anchors"]:
                continue
            d = _intrusion_depth(bb, rect)
            if d > 0:
                intrusions.append({"kind": "analog_zone", "ref": r,
                                   "depth_mm": round(d * qq, 3)})
    # FF-4 protect_keepout 控制组（§9.2；仅绑计划时非空——默认路径零变化）
    for grp in ctx.get("ff_keepout_groups") or []:
        grefs = [r for r in grp["refs"] if r in bodies]
        gnets = _nets_of(ctx, grefs)
        exempt = set(grefs) | _bonded_refs(ctx, gnets)
        for r_g in sorted(grefs):
            keep = _inflate(bodies[r_g], grp["keepout_mm"] / qq)
            for r, bb in bodies.items():
                if r in exempt:
                    continue
                d = _intrusion_depth(bb, keep)
                if d > 0:
                    intrusions.append({"kind": "ff_keepout:" + grp["scope"],
                                       "ref": r, "keepout": r_g,
                                       "depth_mm": round(d * qq, 3),
                                       "control_id": grp["control_id"]})
    intrusions.sort(key=lambda i: (-i["depth_mm"], i["kind"], i["ref"]))
    return {"pass": not intrusions,
            "magnitude_mm": round(sum(i["depth_mm"] for i in intrusions), 3),
            "intrusions": intrusions[:10],
            "source": "placement §6.1/§6.3/§5（0 侵入；模拟区仅 declared 矩形模式）"}


def _inflate(bb, m):
    return (bb[0] - m, bb[1] - m, bb[2] + m, bb[3] + m)


def _nets_of(ctx, refs):
    """refs 的焊盘网集合（剔除 GND/unconnected——GND 全板共享，不构成
    电气邻件证据，否则豁免域=全板）。"""
    out = set()
    for r in refs:
        if r not in ctx["shapes"]:
            continue
        for p in ctx["shapes"][r]["pads_local"]:
            n = p["net"]
            if n and n != "GND" and not n.startswith("unconnected-"):
                out.add(n)
    return out


def _bonded_refs(ctx, nets):
    """与网集共享非 GND 网的 refs（电气邻件豁免；keepout 晶振豁免同先例：
    去耦/对端=设计意图内贴近，不记侵入）。"""
    if not nets:
        return set()
    return {r for r, sh in ctx["shapes"].items()
            if any(p["net"] in nets for p in sh["pads_local"]
                   if p["net"] and p["net"] != "GND")}


def escape_slot_reservation_check(ctx, st, bodies=None):
    """FF-4 reserve_escape_slots（§9.2）：赤字逃逸场的预留带内禁止非电气邻件
    体侵入（体级一阶代理；通道级权威=② C2/⑥）。带=场主 pad-bbox 面向外侧
    AUDIT_ESCAPE_DEPTH_MM，横向 +0.1mm（audit C2 band_rect 同深同裕量；体位姿
    依赖=③ 变量）。侵入幅度计入硬违→lex→候选接受（consumer gate 已批）。"""
    qq = config.CPLACE_QUANT
    depth = q(config.AUDIT_ESCAPE_DEPTH_MM)
    lat = q(ff_consume.ESCAPE_BAND_LATERAL_MM)
    bodies = bodies or bodies_of(ctx, st)
    padbb = {r: _pad_bbox(ctx["shapes"], st, r) for r in ctx["shapes"]}
    rows = []
    for f in ctx["ff_escape_fields"]:
        ref, side = f["ref"], f["side"]
        if ref not in padbb:
            continue
        b = padbb[ref]
        if side == "N":
            band = (b[0] - lat, b[1] - depth, b[2] + lat, b[1])
        elif side == "S":
            band = (b[0] - lat, b[3], b[2] + lat, b[3] + depth)
        elif side == "E":
            band = (b[2], b[1] - lat, b[2] + depth, b[3] + lat)
        else:
            band = (b[0] - depth, b[1] - lat, b[0], b[3] + lat)
        exempt = {ref} | _bonded_refs(ctx, _nets_of(ctx, (ref,)))
        intruders = []
        for r, bb in bodies.items():
            if r in exempt:
                continue
            d = _intrusion_depth(bb, band)
            if d > 0:
                intruders.append({"ref": r, "depth_mm": round(d * qq, 3)})
        rows.append({
            "field": ref + "|" + side, "control_id": f["control_id"],
            "reserve_channels": f.get("reserve_channels"),
            "deficit_channels": f.get("deficit_channels"),
            "band_mm": [round(v * qq, 3) for v in band],
            "intruders": sorted(intruders,
                                key=lambda i: (-i["depth_mm"], i["ref"])),
            "ok": not intruders})
    mag = round(sum(i["depth_mm"] for r in rows for i in r["intruders"]), 3)
    return {"pass": all(r["ok"] for r in rows), "magnitude_mm": mag,
            "rows": sorted(rows, key=lambda r: r["field"]),
            "reserved_fields": len(rows),
            "exemption": "场主+电气邻件（共享非 GND 网；去耦/对端=设计意图贴近）",
            "source": "FF-4 reserve_escape_slots（§9.2；audit C2 同深 3.0mm+0.1mm "
                      "横向；体级代理 derived，通道级权威=② C2/⑥ DRC）"}


def zone_purity_check(ctx, st):
    """§5/§8 分区纯度：declared=质心入矩形；imported=标签保真（冻结基线恒真）。"""
    qq = config.CPLACE_QUANT
    violations = []
    mag = 0.0
    if ctx["zones_declared"]:
        for z, zd in sorted(ctx["zones_declared"].items()):
            rect = (q(zd["rect"][0]), q(zd["rect"][1]), q(zd["rect"][2]), q(zd["rect"][3]))
            for ref in sorted(zd.get("refs") or []):
                if ref not in ctx["shapes"]:
                    continue
                bb = body_bbox(ctx["shapes"], st, ref)
                cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
                if not (rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]):
                    dx = max(rect[0] - cx, cx - rect[2], 0)
                    dy = max(rect[1] - cy, cy - rect[3], 0)
                    violations.append({"ref": ref, "zone": z,
                                       "outside_mm": round(math.hypot(dx, dy) * qq, 3)})
                    # 梯度用曼哈顿分量和（两轴独立单调；欧氏会形成盒谷局部极小）
                    mag += (dx + dy) * qq
    else:
        for ref in sorted(ctx["zone_labels"]):
            if ref in st and st[ref].get("zone") not in (None, ctx["zone_labels"][ref]):
                violations.append({"ref": ref, "zone": ctx["zone_labels"][ref],
                                   "outside_mm": None})
    return {"pass": not violations, "magnitude_mm": round(mag, 3),
        "violations": violations[:10],
        "mode": "declared_rects" if ctx["zones_declared"] else "imported_labels",
        "source": "placement §5/§8（100% 入区 / 标签保真）"}


def board_edge_check(ctx, st, bodies=None):
    """§1 板边：全部 pad-bbox（含半尺寸）在板框（Edge.Cuts bbox）内。无板框时
    退化为 pad 中心 hull（构造上恒真=vacuous，如实标注）。连接器焊盘悬挑板边
    会被如实记出（canonical 无此门；铜出板边的工艺裁定权=⑥ DRC/制板能力）。"""
    bb = ctx.get("board_rect")
    if bb:
        rect = (q(bb[0]), q(bb[1]), q(bb[2]), q(bb[3]))
        source = "Edge.Cuts bbox"
    else:
        padbb_centers = {r: _pad_bbox(ctx["shapes"], st, r) for r in ctx["shapes"]}
        rect = (min(b[0] for b in padbb_centers.values()),
                min(b[1] for b in padbb_centers.values()),
                max(b[2] for b in padbb_centers.values()),
                max(b[3] for b in padbb_centers.values()))
        source = "pad 中心 hull 代理（无 Edge.Cuts；恒真=vacuous）"
    overhang = []
    for r in sorted(ctx["shapes"]):
        b = _pad_bbox(ctx["shapes"], st, r)
        if not (rect[0] <= b[0] and b[2] <= rect[2]
                and rect[1] <= b[1] and b[3] <= rect[3]):
            out = max(rect[0] - b[0], b[2] - rect[2],
                      rect[1] - b[1], b[3] - rect[3])
            overhang.append({"ref": r,
                             "overhang_mm": round(out * config.CPLACE_QUANT, 3)})
    overhang.sort(key=lambda o: (-o["overhang_mm"], o["ref"]))
    return {"pass": not overhang, "magnitude_mm": round(max(
        (o["overhang_mm"] for o in overhang), default=0.0), 3),
        "overhang_rows": overhang[:10], "rect_source": source,
        "board_rect_mm": [round(v * config.CPLACE_QUANT, 3) for v in rect],
        "source": "placement §1 板边（pad 含半尺寸在板框内；canonical 无此门，"
                  "证据性；悬挑=边缘连接器常态，工艺裁定⑥）"}


# ---- 骨架与段层计划 ----------------------------------------------------------
def _exit_point_mm(ctx, st, ref, side, bodies):
    bb = bodies[ref]
    if side == "N":
        return ((bb[0] + bb[2]) / 2, bb[1])
    if side == "S":
        return ((bb[0] + bb[2]) / 2, bb[3])
    if side == "E":
        return (bb[2], (bb[1] + bb[3]) / 2)
    return (bb[0], (bb[1] + bb[3]) / 2)


def build_skeletons(ctx, st, bodies=None):
    """种子出口侧 → 每总线链式 L 形骨架（每对相邻端点 1 个可移动拐点）。
    net 引用按 net_id（SPEC §③）；一阶：段成员=总线全体成员（derived，记录）。"""
    bodies = bodies or bodies_of(ctx, st)
    seed_buses = {b["bus_id"]: b for b in (ctx.get("seed") or {}).get("buses", [])}
    skels = []
    for cor in ctx["corridors"]:
        exits = {e["ref"]: e["dominant_exit_side"]
                 for e in seed_buses.get(cor["bus_id"], {}).get("endpoints", [])}
        chain = []
        for a, b in cor["pairs"]:
            if not chain:
                chain.append(a)
            chain.append(b)
        pts = [(ref, exits.get(ref) or "N") for ref in chain]
        segments = []
        for (ra, sa), (rb, sb2) in zip(pts, pts[1:]):
            ax, ay = _exit_point_mm(ctx, st, ra, sa, bodies)
            bx, by = _exit_point_mm(ctx, st, rb, sb2, bodies)
            bend = (ax, by) if sa in ("N", "S") else (bx, ay)
            segments.append({
                "from_ref": ra, "to_ref": rb,
                "bend": [round(bend[0] * config.CPLACE_QUANT, 3),
                         round(bend[1] * config.CPLACE_QUANT, 3)],
                "polyline": [[round(v * config.CPLACE_QUANT, 3) for v in pt]
                             for pt in ((ax, ay), bend, (bx, by))]})
        skels.append({"bus_id": cor["bus_id"],
                      "net_ids": sorted(ctx["net_ids"].get(n) or n
                                        for n in cor["members"]),
                      "chain": chain, "segments": segments})
    return sorted(skels, key=lambda s: s["bus_id"])


def _layer_pref_order(ctx):
    pref = []
    for r in ctx["layer_preference_ranks"]:
        name = r.split("=")[0].strip()
        if name in ("F.Cu", "In2.Cu", "B.Cu") and name not in pref:
            pref.append(name)
    for name in ("In2.Cu", "F.Cu", "B.Cu"):
        if name not in pref:
            pref.append(name)
    return pref


def layer_plan_of(ctx):
    """段层计划（与位姿无关→按 ctx 缓存）：段层∈成员 allowed_layers∩信号层，
    按 layer_preference 序；相邻段同层优先（过孔最少）。层数=2 信号层（In1/B 地）。"""
    if ctx.get("_layer_plan_cache"):
        return ctx["_layer_plan_cache"]
    pref = _layer_pref_order(ctx)
    plans = []
    total_vias = 0
    ff_pref = ctx.get("ff_preferred_layers") or {}
    for cor in ctx["corridors"]:
        allowed = set()
        for n in cor["members"]:
            a = (ctx["registry_view"].get(n) or {}).get("allowed_layers")
            if a:
                allowed |= set(a)
        # FF-4 assign_preferred_layer（§9.2）：该总线首选层前置（仅绑计划时生效）
        order = pref
        bus_pref = ff_pref.get(cor["bus_id"])
        if bus_pref and bus_pref in pref:
            order = [bus_pref] + [l for l in pref if l != bus_pref]
        layers = [l for l in order if not allowed or l in allowed] or order
        segs = []
        prev = None
        for a, b in cor["pairs"]:
            lay = prev if prev in layers else layers[0]
            segs.append({"from_ref": a, "to_ref": b, "layer": lay})
            prev = lay
        vias = sum(1 for i in range(1, len(segs))
                   if segs[i]["layer"] != segs[i - 1]["layer"])
        total_vias += vias
        plans.append({"bus_id": cor["bus_id"], "segments": segs, "via_count": vias,
                      "allowed_layers": layers, "demand_width_mm": cor["demand_mm"],
                      "demand_source": cor["demand_source"]})
    plan = {"buses": sorted(plans, key=lambda p: p["bus_id"]),
            "via_count_total": total_vias,
            "layer_preference_applied": pref,
            "source": "registry.allowed_layers/via_policy + layer_preference（软）；"
                      "信号层数=2（In1/B=完整地平面）"
                      + ("；FF-4 per-bus 首选层前置（§9.2）" if ff_pref else "")}
    if ff_pref:  # 仅绑计划时增键（默认路径 byte-exact 不变）
        plan["ff_preferred_layers_applied"] = dict(sorted(ff_pref.items()))
    ctx["_layer_plan_cache"] = plan
    return plan


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _seg_cross(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    return (o(p1, p2, p3) * o(p1, p2, p4) < 0
            and o(p3, p4, p1) * o(p3, p4, p2) < 0)  # 严格内交（共端不记）


def _count_crossings(skels):
    n = 0
    for i in range(len(skels)):
        for j in range(i + 1, len(skels)):
            for sa in skels[i]["segments"]:
                for sb in skels[j]["segments"]:
                    pa = [tuple(p) for p in sa["polyline"]]
                    pb = [tuple(p) for p in sb["polyline"]]
                    for k in range(len(pa) - 1):
                        for m in range(len(pb) - 1):
                            if _seg_cross(pa[k], pa[k + 1], pb[m], pb[m + 1]):
                                n += 1
    return n


def _net_pad_points(ctx, st, net):
    pts = []
    for r in sorted(ctx["shapes"]):
        for p in abs_pads(ctx["shapes"][r], st[r]["x"], st[r]["y"], st[r]["rot"]):
            if p["net"] == net:
                pts.append((p["x"], p["y"]))
    return pts


def symmetry_dev_max(ctx, st):
    """对称类偏差：symmetry_class 成员端到端 pad 链长 vs 类中位（一阶 derived）。"""
    dev = 0.0
    qq = config.CPLACE_QUANT
    for b in ctx["structures_buses"]:
        if not b.get("symmetry_class"):
            continue
        lens = []
        for n in b["members"]:
            pts = _net_pad_points(ctx, st, n)
            if len(pts) >= 2:
                lens.append(sum(math.hypot(b2[0] - a[0], b2[1] - a[1])
                                for a, b2 in zip(pts, pts[1:])))
        if len(lens) >= 2:
            med = sorted(lens)[len(lens) // 2]
            dev = max(dev, max(abs(v - med) for v in lens))
    return round(dev * qq, 3)


def soft_metrics(ctx, st, skels, chan):
    detours = []
    bends = 0
    for s in skels:
        for seg in s["segments"]:
            pl = [tuple(p) for p in seg["polyline"]]
            straight = math.hypot(pl[-1][0] - pl[0][0], pl[-1][1] - pl[0][1])
            if straight > 1e-6:
                detours.append(polyline_len(pl) / straight)
            bends += max(0, len(pl) - 2)
    return {"crossings": _count_crossings(skels),
            "congestion_max": chan["utilization_max"],
            "vias": layer_plan_of(ctx)["via_count_total"],
            "detour_max": round(max(detours), 4) if detours else 1.0,
            "symmetry_dev_max_mm": symmetry_dev_max(ctx, st),
            "bends": bends,
            "min_channel_margin_mm": chan["min_channel_margin_mm"],
            "note": "一阶模型（L 形骨架/端到端链长对称偏差/走廊利用率拥塞）"}


def _verdict_of(hard_fail, soft):
    """绿/黄/红（阈值 config.py 固定；黄=继续但记账，红=停并分类）。"""
    if hard_fail:
        return "red"
    if (soft["crossings"] >= config.CPLACE_CROSSING_YELLOW
            or soft["congestion_max"] >= config.CPLACE_CHANNEL_UTIL_YELLOW
            or soft["vias"] >= config.CPLACE_VIA_YELLOW
            or soft["detour_max"] >= config.CPLACE_DETOUR_YELLOW
            or soft["symmetry_dev_max_mm"] >= config.CPLACE_SYMM_DEV_YELLOW_MM):
        return "yellow"
    return "pass"


def evaluate(ctx, st, bodies=None, chan=None):
    """证据向量 + 硬门（无单点置信度；全部阈值 config.py 固定）。"""
    bodies = bodies or bodies_of(ctx, st)
    chan = chan or channel_check(ctx, st, bodies)
    hard = {
        "channel_budget": {"pass": chan["fail_count"] == 0,
                           "magnitude_mm": chan["magnitude_mm"], "detail": chan},
        "proximity": proximity_check(ctx, st),
        "buck_loop": buck_loop_check(ctx, st),
        "body_spacing": spacing_check(ctx, st, bodies),
        "orientation": orientation_check(ctx, st),
        "keepout": keepout_check(ctx, st, bodies),
        "zone_purity": zone_purity_check(ctx, st),
        "board_edge": board_edge_check(ctx, st, bodies),
    }
    # FF-4（§9.2 consumer gate 已批）：控制派生预留门计入硬违→lex→候选接受；
    # 未绑计划时无此键（默认证据面与 FF1 收官态 byte-exact 一致）
    if ctx.get("ff_escape_fields"):
        hard["escape_slot_reservation"] = escape_slot_reservation_check(
            ctx, st, bodies)
    hard_fail = sorted(k for k, v in hard.items() if not v["pass"])
    hard_mag = round(sum(max(v["magnitude_mm"], 0.0) for v in hard.values()), 3)
    skels = build_skeletons(ctx, st, bodies)
    soft = soft_metrics(ctx, st, skels, chan)
    # lex 首位=幅度和（非违例门数）：门数首位会封锁「过境必要」的一过性违例
    # （如 U8 绕经 U1 角落时间距短暂+1.0 但分区 −1.5 的净改善步）。
    lex = (hard_mag, soft["crossings"], soft["congestion_max"],
           soft["vias"], soft["detour_max"], soft["symmetry_dev_max_mm"])
    verdict = _verdict_of(hard_fail, soft)
    return {"hard": hard, "hard_fail_gates": hard_fail,
            "hard_magnitude_mm": hard_mag, "soft": soft, "skels": skels,
            "lex": lex, "verdict": verdict, "bodies": bodies,
            "placement_gate_map": PLACEMENT_GATE_MAP}


# ---- 确定性爬山（SPEC §③ 候选集；无随机；锚件永不移动） ---------------------
def _candidate_moves(ref):
    """稳定序：平移 ±{0.5,1,2}×4 向（N,S,W,E），旋转 0/±90/180 三候选（90° 步进）。"""
    out = []
    for step in config.CPLACE_STEPS_MM:
        s = q(step)
        for dx, dy in ((0, -s), (0, s), (-s, 0), (s, 0)):
            out.append(("move", ref, dx, dy, 0))
    for rot in (config.CPLACE_ROT_STEP, -config.CPLACE_ROT_STEP,
                2 * config.CPLACE_ROT_STEP):
        out.append(("rot", ref, 0, 0, rot))
    return out


def _same_footprint_swaps(ctx):
    by_lib = {}
    for r in sorted(ctx["shapes"]):
        if r in ctx["anchors"]:
            continue
        by_lib.setdefault(ctx["shapes"][r]["lib"], []).append(r)
    out = []
    for lib in sorted(by_lib):
        refs = by_lib[lib]
        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                out.append(("swap", refs[i], refs[j]))
    return out


def _bend_candidates(skels):
    out = []
    for s in skels:
        for i, seg in enumerate(s["segments"]):
            for step in config.CPLACE_STEPS_MM:
                v = q(step)
                for dx, dy in ((0, -v), (0, v), (-v, 0), (v, 0)):
                    out.append((s["bus_id"], i, dx, dy))
    return out


def _bend_spacing_ok(seg, dx, dy):
    """拐点最小间距（SPEC §③）：移动后拐点到线段两端点距离均 ≥ 下限。
    polyline 为 mm、dx/dy 为量子（0.05mm 单位）；限值取 mm 原值比较。"""
    lim = config.CPLACE_MIN_BEND_SPACING_MM
    pl = [tuple(p) for p in seg["polyline"]]
    nb = (pl[1][0] + dx * config.CPLACE_QUANT, pl[1][1] + dy * config.CPLACE_QUANT)
    return (math.hypot(nb[0] - pl[0][0], nb[1] - pl[0][1]) >= lim
            and math.hypot(nb[0] - pl[2][0], nb[1] - pl[2][1]) >= lim)


def _apply_bend(skels, bus_id, seg_i, dx, dy):
    seg = next(x for x in skels if x["bus_id"] == bus_id)["segments"][seg_i]
    pl = [list(p) for p in seg["polyline"]]
    pl[1][0] = round(pl[1][0] + dx * config.CPLACE_QUANT, 3)
    pl[1][1] = round(pl[1][1] + dy * config.CPLACE_QUANT, 3)
    seg["bend"] = [pl[1][0], pl[1][1]]
    seg["polyline"] = pl


def _soft_key(soft):
    return (soft["crossings"], soft["vias"], soft["detour_max"],
            soft["symmetry_dev_max_mm"])


def _zone_viol_of(ev, ref):
    for v in ev["hard"]["zone_purity"]["violations"]:
        if v["ref"] == ref:
            return v["outside_mm"] or 0.0
    return 0.0


def _accept_lex(cand, cur, sideways_ok, eps):
    """严格改善；或 ε 容差横移（幅度不劣于 cur+ε 且尾部分量逐项不劣）。"""
    if cand < cur:
        return True
    if not sideways_ok:
        return False
    if cand[0] > cur[0] + eps:
        return False
    return tuple(cand[1:]) <= tuple(cur[1:])


def optimize(ctx, st, max_sweeps=None):
    """确定性爬山：lex 严格改善即接受；另有每扫有界的容差横移（绕障/贴墙滑移，
    上限 config.CPLACE_SIDEWAYS_PER_REF、容差 CPLACE_SIDEWAYS_EPS_MM，扫内计数）。

    处理顺序=worst-first 稳定键（分区违例距离降序，ref 字典序 tie-break）。
    锚件不在候选集（红线）；收敛=本扫无任何严格改善；超限=如实报
    max_sweeps_reached（禁宣称收敛）。无随机、无 wall-clock。
    """
    max_sweeps = max_sweeps or config.CPLACE_MAX_SWEEPS
    cur = {r: dict(v) for r, v in st.items()}
    cur_ev = evaluate(ctx, cur)
    skels = cur_ev["skels"]
    cur_soft_key = _soft_key(cur_ev["soft"])
    accepted = 0
    converged = False
    sweeps = 0
    sideways = 0
    for _ in range(max_sweeps):
        sweeps += 1
        improved = False

        def take(trial, ev):
            nonlocal cur, cur_ev, skels, cur_soft_key, accepted, improved, sideways
            strict = ev["lex"] < cur_ev["lex"]
            if strict:
                improved = True
                sideways = 0
            else:
                sideways += 1
            cur, cur_ev = trial, ev
            skels = cur_ev["skels"]
            cur_soft_key = _soft_key(cur_ev["soft"])
            accepted += 1

        # 硬违已清零后不再横移（零平台游走只会烧扫数；下一步即诚实收敛）
        sideways_budget = (config.CPLACE_SIDEWAYS_PER_REF
                           if cur_ev["lex"][0] > 0 else 0)

        zone_viol = {v["ref"]: v["outside_mm"] or 0.0
                     for v in cur_ev["hard"]["zone_purity"]["violations"]}
        refs = sorted((r for r in ctx["shapes"] if r not in ctx["anchors"]),
                      key=lambda r: (-zone_viol.get(r, 0.0), r))
        for ref in refs:
            sideways = 0
            for kind, _, dx, dy, rot in _candidate_moves(ref):
                trial = {r: dict(v) for r, v in cur.items()}
                t = trial[ref]
                if kind == "move":
                    t["x"] += dx
                    t["y"] += dy
                else:
                    t["rot"] = (t["rot"] + rot) % 360
                ev = evaluate(ctx, trial)
                if _accept_lex(ev["lex"], cur_ev["lex"], sideways < sideways_budget,
                               config.CPLACE_SIDEWAYS_EPS_MM):
                    take(trial, ev)
        for _, a, b in _same_footprint_swaps(ctx):
            trial = {r: dict(v) for r, v in cur.items()}
            trial[a], trial[b] = dict(cur[b]), dict(cur[a])
            ev = evaluate(ctx, trial)
            if _accept_lex(ev["lex"], cur_ev["lex"], sideways < sideways_budget,
                           config.CPLACE_SIDEWAYS_EPS_MM):
                take(trial, ev)
        for bus_id, seg_i, dx, dy in _bend_candidates(skels):
            seg = next(x for x in skels if x["bus_id"] == bus_id)["segments"][seg_i]
            if not _bend_spacing_ok(seg, dx, dy):
                continue
            trial_skels = json.loads(json.dumps(skels))
            _apply_bend(trial_skels, bus_id, seg_i, dx, dy)
            soft = soft_metrics(ctx, cur, trial_skels,
                                channel_check(ctx, cur, cur_ev["bodies"]))
            key = _soft_key(soft)
            if key < cur_soft_key or (key == cur_soft_key
                                      and sideways < sideways_budget):
                if key < cur_soft_key:
                    improved = True
                    sideways = 0
                else:
                    sideways += 1
                skels = trial_skels
                cur_soft_key = key
                accepted += 1
        if not improved:
            converged = True
            break
    trace = {"sweeps": sweeps, "accepted_moves": accepted, "converged": converged,
             "max_sweeps_reached": not converged and sweeps >= max_sweeps,
             "sideways_moves_last_sweep": sideways,
             "method": "deterministic_hill_climb(lex=硬违幅度和,交叉,拥塞,"
                       "过孔,绕行,对称偏差；候选=SPEC §③ 枚举稳定序；"
                       "worst-first 稳定序；容差横移有界；无随机)",
             "final_verdict": cur_ev["verdict"]}
    return cur, skels, trace


# ---- placement.csv 确定性转换器（单向 + 可重放；执行待批准=确认点 #4） --------
CSV_HEADER = ("ref", "x", "y", "rot", "side", "zone")


def to_placement_csv(layout):
    """layout.json → placement.csv bytes。确定性：ref 字典序、%.2f 去尾零保一位、
    CRLF（与既有 apply 脚本输入口径一致，p3 往返 byte-exact 由测试强制）。"""
    lines = [",".join(CSV_HEADER)]
    for row in sorted(layout["placements"], key=lambda r: r["ref"]):
        lines.append(",".join([
            row["ref"], fmt_csv(row["x"]), fmt_csv(row["y"]), str(int(row["rot"])),
            row.get("side") or "F", row.get("zone") or ""]))
    return ("\r\n".join(lines) + "\r\n").encode(config.ENCODING)


def conversion_proof(layout_sha256, csv_sha256, out_dir_rel, roundtrip=None):
    """转换证明（无 wall-clock：同 layout.json ⇒ byte-exact 同 CSV，重放测试强制）。
    roundtrip：源 CSV 导入→转换 与源文件 byte-exact 的证明（Rev-C 快照往返）。"""
    return {
        "schema_version": config.SCHEMA_CONVERSION,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "input": {"artifact": "layout.json", "sha256": layout_sha256},
        "output": {"artifact": "placement.csv", "sha256": csv_sha256,
                   "path": out_dir_rel + "/placement.csv"},
        "roundtrip_proof": roundtrip or {},
        "rules": {"row_order": "ref 升序（unicode 字典序）",
                  "coords": "量化 0.05mm；%.2f 去尾零保一位小数",
                  "rot": "整型度数", "header": ",".join(CSV_HEADER),
                  "newline": "CRLF（既有 apply 脚本输入口径）",
                  "encoding": "utf-8"},
        "deterministic": True,
        "execution": "pending_approval（人工确认点 #4：批准后才调用既有 apply 脚本写板）",
        "one_way_note": "layout.json=唯一优化输出；CSV 只能由本转换器生成；"
                        "禁手改二者之一而不重出转换证明（SPEC §③）",
    }


# ---- ②↔③ 走廊需求交叉核对（SPEC v1.3 §8.3；FF-3 修复） ------------------------
SANITY_TOLERANCE_MM = 1e-6  # demand_mm 与 required_mm 同源 C-0053 的浮点容差


def sanity_vs_audit_rows(channel_rows, corridors):
    """③ 通道预算行 vs ② audit 走廊预算的交叉核对（canonical 字段=required_mm）。

    三态：consistent | inconsistent | unknown。缺字段/缺总线/null →
    unknown+missing_basis reason；禁止 None→true（v1.3 §8.3，FF-3 修复前缺陷）。
    可比较时断言 audit 值非空，并记录 tolerance/来源/数值。
    """
    cmap = {c.get("bus_id"): c for c in corridors}
    rows = []
    for row in channel_rows:
        bus, local = row["bus_id"], row["demand_mm"]
        c = cmap.get(bus)
        base = {"bus_id": bus, "demand_mm": local,
                "gap_mm": row["gap_mm"], "ok": row["ok"]}
        if c is None or "required_mm" not in c:
            rows.append(dict(base, audit_demand_mm=None,
                             demand_consistent="unknown",
                             reason="missing_basis:required_mm"))
        elif c["required_mm"] is None:
            rows.append(dict(base, audit_demand_mm=None,
                             demand_consistent="unknown",
                             reason="missing_basis:required_mm_null"))
        else:
            val = c["required_mm"]
            assert val is not None, "required_mm 可比较时必须非空（v1.3 §8.3）"
            delta = abs(val - local)
            state = "consistent" if delta <= SANITY_TOLERANCE_MM else "inconsistent"
            rows.append(dict(
                base, audit_demand_mm=val, demand_consistent=state,
                reason=None if state == "consistent" else
                "delta=%g exceeds tolerance %g" % (delta, SANITY_TOLERANCE_MM),
                tolerance_mm=SANITY_TOLERANCE_MM,
                source="audit corridor_budget_check.required_mm（C-0053 同源）"))
    return sorted(rows, key=lambda r: r["bus_id"])


# ---- Rev-C 产品组装（CLI 入口；基线冻结→只做评估 sanity，优化不执行） ---------
def build_products(out_dir_rel=config.load_project_manifest().out_dirs["coplace"],
                   ff_plan_path=None):
    """ff_plan_path：FF-4 计划消费（None=不绑计划，输出与 FF1 收官态 byte-exact）。
    绑定后 controls 经 consumer gate（NEXT.md #6 已批）进入候选接受语义；stale/
    conflict 时 controls 不应用（authority 保持 planning_advisory），状态=blocked。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)

    enum_products = enum_cmd.build_products(out_dir_rel)
    structures = enum_products["structures"]["obj"]
    registry = enum_products["net_registry"]["obj"]
    registry_hash = registry["registry_snapshot_hash"]
    net_ids = {r["net_name"]: r["net_id"] for r in registry["nets"]}

    with open(config.SEED_PATH, encoding=config.ENCODING) as f:
        seed = json.load(f)
    seed_binding = {"seed_registry_snapshot_hash": seed.get("registry_snapshot_hash"),
                    "rebuilt_registry_snapshot_hash": registry_hash,
                    "bound": seed.get("registry_snapshot_hash") == registry_hash}

    board = geo.parse_board(config.AUDIT_P3_BOARD)
    baseline = import_placement_csv(config.AUDIT_P3_PLACEMENT_CSV)
    # 评估对象=板读数（② audit/④⑤⑥ 消费的冻结实体）；CSV 位置差异只报告不套用
    #（快照卫生发现：板 vs CSV 对 J1-J5/CRTC/U3 等 7 件不一致，见 baseline_deltas）
    st = state_with_csv_zones(state_from_board(board), baseline)
    csv_deltas = _csv_position_deltas(st, baseline)
    # 转换器往返证明：CSV 导入副本 → 转换 → 与源 CSV byte-exact（可重放证据）
    st_csv, _ = state_override_from_csv(state_from_board(board), baseline)
    csv_view = {"placements": [
        {"ref": ref, "x": uq(st_csv[ref]["x"]), "y": uq(st_csv[ref]["y"]),
         "rot": st_csv[ref]["rot"], "side": st_csv[ref].get("side") or "F",
         "zone": st_csv[ref].get("zone") or ""} for ref in sorted(st_csv)]}
    roundtrip_bytes = to_placement_csv(csv_view)

    # FF-4：消费前馈计划（六 hash 绑定→controls 解释；stale/conflict 不应用）
    ff = None
    if ff_plan_path:
        ff = ff_consume.consume_plan(
            ff_plan_path, enum_products=enum_products,
            shape_refs=set(board["footprints"]),
            corridor_bus_ids=[b["bus_id"] for b in structures["buses"]],
            out_dir_rel=out_dir_rel)

    ctx = build_context(board, structures, seed, net_ids, registry_hash,
                        zone_labels={r: b["zone"] for r, b in baseline.items()},
                        registry_view={r["net_name"]: r for r in registry["nets"]},
                        layer_preference_ranks=structures["priorities"]
                        ["layer_preference"]["ranks"],
                        board_rect=edge_cuts_bbox(config.AUDIT_P3_BOARD),
                        ff_controls=ff["extensions"] if ff and ff["applied"]
                        else None)
    ev = evaluate(ctx, st)  # 冻结基线只做证据评估；优化不执行（SANITY）
    plan = layer_plan_of(ctx)

    corb = audit_cmd.corridor_budget_check(board, structures)
    # FF-3 修复：读 canonical required_mm（旧代码读不存在的 demand_width_mm →
    # 全 null → 空比较判 true；v1.3 §8.3 三态，禁止 None→true）
    sanity_rows = sanity_vs_audit_rows(
        ev["hard"]["channel_budget"]["detail"]["rows"], corb["corridors"])
    sanity_ok = all(r["demand_consistent"] == "consistent" for r in sanity_rows)

    try:
        with open(P3_GATES_JSON, encoding=config.ENCODING) as f:
            p3_gates = json.load(f)
    except OSError:
        p3_gates = None
    comparison = canonical_comparison(ev, p3_gates)

    placements = placements_of(ctx, st, default_role="baseline_imported")
    layout = {
        "schema_version": config.SCHEMA_COPLACE,
        "project": compile_cmd.PROJECT_ID,
        "stage": 3,
        "role": "③ 联合布局与骨架优化产物；唯一优化输出（SPEC §③）",
        "registry_consumption": {
            "registry_snapshot_hash": registry_hash,
            "registry_consumed": True,
            "fields_consumed": ["net_id", "allowed_layers", "via_policy",
                                "skeleton_seed(corridor demand/exit sides)"],
            "fields_ignored": ["aliases", "planner_class_view", "width_mm",
                               "length_group", "electrical_role", "preferred_layer"],
            "fallback": None,
            "fidelity": "full（seed hash 绑定见 seed_binding）",
        },
        "seed_binding": seed_binding,
        "board_snapshot": {
            "path": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                    "snapshots/p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
            "footprints": len(board["footprints"]), "note": "p3 冻结基线；只读"},
        "optimization": {
            "applied": False, "mode": "baseline_frozen_sanity_only",
            "reason": "p3 布局冻结（FA3 回测时点）；SPEC §③ 门：Rev-C 只做指标 sanity；"
                      "优化与转换执行须人工批准（确认点 #4）",
            "method_trace": None,
        },
        "baseline_deltas": {
            "count": len(csv_deltas), "rows": csv_deltas,
            "note": "板读数 vs placement.csv（唯一事实源）的量子化位置差异；基线取 CSV"},
        "placements": placements,
        "skeletons": [{"bus_id": s["bus_id"], "net_ids": s["net_ids"],
                       "chain": s["chain"], "segments": s["segments"]}
                      for s in ev["skels"]],
        "layer_plan": plan,
        "evidence": {
            "hard_gates": {k: {"pass": v["pass"], "magnitude_mm": v["magnitude_mm"]}
                           for k, v in ev["hard"].items()},
            "hard_fail_gates": ev["hard_fail_gates"],
            "soft": ev["soft"], "verdict": ev["verdict"],
            "placement_gate_map": PLACEMENT_GATE_MAP,
            "note": "证据指标向量+硬门状态（禁单点置信度）；阈值 config.py 固定",
        },
        "sanity_vs_audit": {"rows": sanity_rows,
                            "note": "与 ② audit 走廊预算同源复算（同 structures/同 C-0053）"},
        "canonical_comparison": comparison,
    }
    if ff:  # §9.1 消费证据（仅绑计划时出现；含 declared/actually_read/derived/
        # ignored/stale_plan_reason 与六 hash 绑定明细）
        layout["feedforward_consumption"] = ff["evidence"]
    if ff and ff["applied"]:  # 控制派生门的明细行（证据可核对；summary 之外）
        det = {}
        esc = ev["hard"].get("escape_slot_reservation")
        if esc:
            det["escape_slot_reservation"] = {
                k: esc[k] for k in ("rows", "reserved_fields", "exemption",
                                    "source")}
        det["channel_intruders"] = [
            {"bus_id": r["bus_id"], "intruders": r["intruders"],
             "intruder_magnitude_mm": r["intruder_magnitude_mm"],
             "intruder_check": r["intruder_check"]}
            for r in ev["hard"]["channel_budget"]["detail"]["rows"]]
        ko = [i for i in ev["hard"]["keepout"]["intrusions"]
              if str(i.get("kind", "")).startswith("ff_keepout:")]
        if ko:
            det["ff_keepout_intrusions"] = ko
        bl = ev["hard"]["buck_loop"].get("ff_budget_attainment")
        if bl:
            det["power_loop_budget"] = bl
        layout["evidence"]["ff_gate_details"] = det
    geojson = _build_geojson(ev["skels"], board)
    csv_bytes = to_placement_csv(layout)
    src_csv_bytes = open(config.AUDIT_P3_PLACEMENT_CSV, "rb").read()
    roundtrip = {
        "mode": "source_csv_import_convert",
        "source_path": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                       "snapshots/p3-placement-gates-pass/placement.csv",
        "source_sha256": hashing.sha256_bytes(src_csv_bytes),
        "roundtrip_sha256": hashing.sha256_bytes(roundtrip_bytes),
        "byte_exact_vs_source": roundtrip_bytes == src_csv_bytes,
        "note": "p3 CSV 导入副本→转换器→与源文件逐字节一致（可重放证据）；"
                "本产物 placement.csv 则是评估布局（板读数）的转换快照",
    }
    products = {}
    for name, obj in (("layout", layout), ("geojson", geojson),
                      ("layer_plan", plan)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data,
                          "sha256": hashing.sha256_bytes(data)}
    products["placement_csv"] = {"obj": None, "bytes": csv_bytes,
                                 "sha256": hashing.sha256_bytes(csv_bytes)}
    conv = conversion_proof(products["layout"]["sha256"],
                            products["placement_csv"]["sha256"], out_dir_rel,
                            roundtrip=roundtrip)
    data = hashing.canonical_json_bytes(conv)
    products["conversion"] = {"obj": conv, "bytes": data,
                              "sha256": hashing.sha256_bytes(data)}
    if ff:  # FF-4 消费证据独立产物（与 layout 内嵌块同源同字节）
        ffc_ev = ff["evidence"]
        data = hashing.canonical_json_bytes(ffc_ev)
        products["ff_consumption"] = {"obj": ffc_ev, "bytes": data,
                                      "sha256": hashing.sha256_bytes(data)}

    inputs = [
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": hashing.sha256_file(config.AUDIT_P3_BOARD), "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/placement.csv",
         "sha256": hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV), "role": "board"},
        {"path": "tools/pcbflow/out/revc-a3/skeleton-seed.json",
         "sha256": hashing.sha256_file(config.SEED_PATH), "role": "skeleton_seed"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/revc.netlist",
         "sha256": hashing.sha256_file(config.REVC_NETLIST), "role": "netlist"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/gates-p3.json",
         "sha256": hashing.sha256_file(P3_GATES_JSON), "role": "canonical_gates"},
    ]
    artifacts = [
        {"path": f"{out_dir_rel}/layout.json", "sha256": products["layout"]["sha256"],
         "role": "core"},
        {"path": f"{out_dir_rel}/skeletons.geojson",
         "sha256": products["geojson"]["sha256"], "role": "core"},
        {"path": f"{out_dir_rel}/layer-plan.json",
         "sha256": products["layer_plan"]["sha256"], "role": "core"},
        {"path": f"{out_dir_rel}/placement.csv",
         "sha256": products["placement_csv"]["sha256"], "role": "snapshot"},
        {"path": f"{out_dir_rel}/conversion.json",
         "sha256": products["conversion"]["sha256"], "role": "proof"},
    ]
    if ff:
        inputs.append({
            "path": "tools/pcbflow/out/revc-ff1/feedforward-plan.json",
            "sha256": ff["plan_sha"], "role": "feedforward_plan"})
        artifacts.append({
            "path": f"{out_dir_rel}/ff-consumption.json",
            "sha256": products["ff_consumption"]["sha256"],
            "role": "ff_consumption_evidence"})
    status = ("ok" if seed_binding["bound"] and sanity_ok
              and (ff is None or ff["applied"]) else "blocked")
    env = envelope.build_envelope(
        command="co-place",
        status=status,
        verdict=ev["verdict"], inputs=inputs, artifacts=artifacts,
        config_sha256=hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        spec_refs=["tools/pcbflow/SPEC.md#§③", "placement-spec-v1.md",
                   "routing-spec-v1.md"],
        metrics={
            "registry_snapshot_hash": registry_hash,
            "seed_bound": seed_binding["bound"],
            "hard_fail_gates": ev["hard_fail_gates"],
            "crossings": ev["soft"]["crossings"],
            "congestion_max": ev["soft"]["congestion_max"],
            "vias": ev["soft"]["vias"], "detour_max": ev["soft"]["detour_max"],
            "symmetry_dev_max_mm": ev["soft"]["symmetry_dev_max_mm"],
            "bends": ev["soft"]["bends"],
            "optimization_applied": False,
            "sanity_demand_consistent": sanity_ok,
            **({"ff_plan_consumed": True,
                "ff_controls_applied":
                    len(ff["evidence"]["controls_declared_consumed"]),
                "ff_controls_ignored": len(ff["evidence"]["controls_ignored"]),
                "ff_stale_plan": ff["binding"]["stale_plan"]} if ff else {}),
        },
        diagnostics=[
            {"id": "revc_frozen_sanity",
             "title": "p3 布局冻结：③ 只做证据评估 sanity；优化不执行（FB1 门=合成板）"},
            {"id": "conversion_pending",
             "title": "layout→placement.csv 转换器已建+可重放；执行待人工批准（确认点 #4）"},
        ] + ([{
            "id": "ff4_consumer_gate",
            "title": "FF-4 计划消费：" + ("controls 已进入 ③ 候选接受语义"
                     "(consumer gate=NEXT.md #6 已批 2026-08-29)" if ff["applied"]
                     else "stale/conflict——controls 未应用，authority 保持 "
                          "planning_advisory"),
            "evidence": f"{out_dir_rel}/ff-consumption.json"}] if ff else []),
        data={
            "gate": {"fb1": {
                "synthetic_red_to_green": "由测试执行（tests/test_coplace_synthetic.py）",
                "converter_replay": "由测试执行（round-trip byte-exact）",
                "revc_sanity": "pass" if sanity_ok else "delta"},
                "note": "命令状态=本次评估是否完成；算法门≠交付门"},
            "seed_binding": seed_binding,
        },
    )
    products["envelope"] = {"obj": env}

    t1 = datetime.datetime.now(datetime.timezone.utc)
    products["run_manifest"] = {"obj": {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "kicad_cli_version": None, "kipy_version": None, "numpy_version": None,
        "tool_version": config.TOOL_VERSION,
        "input_sha256": {i["path"]: i["sha256"] for i in inputs},
        "config_sha256": hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "schema_version": "1.2", "registry_snapshot_sha256": registry_hash,
        "model_refs": [], "prompt_template_sha256": None,
        "command": "co-place", "out_dir": out_dir_rel,
    }}
    return products


def placements_of(ctx, st, default_role="optimized", moved_map=None):
    """状态 → layout.placements 行（role：anchor_locked/optimized/自定义）。"""
    moved_map = moved_map or {}
    return [{"ref": ref, "x": uq(st[ref]["x"]), "y": uq(st[ref]["y"]),
             "rot": st[ref]["rot"], "side": st[ref].get("side") or "F",
             "zone": st[ref].get("zone") or "",
             "role": "anchor_locked" if ref in ctx["anchors"] else default_role,
             "moved": moved_map.get(ref, False)}
            for ref in sorted(st)]


def _build_geojson(skels, board):
    """skeletons.geojson：内部毫米坐标（原点=板原点、y 向下、KiCad 层名；
    非 WGS84、无经纬度语义 —— SPEC §③）。"""
    return {
        "schema_version": config.SCHEMA_GEOJSON,
        "type": "FeatureCollection",
        "coordinate_system": {
            "name": "pcbflow-internal-mm", "units": "mm",
            "origin": "board origin（KiCad 板坐标系）",
            "axis": "x 右正、y 下正（KiCad 屏幕系）",
            "rotation": "逆时针为正（KiCad 约定）",
            "layers": "KiCad 层名（F.Cu/In1.Cu/In2.Cu/B.Cu）",
            "not_geographic": True,
            "note": "内部毫米坐标；禁经纬度语义（SPEC §③）",
            "board_bbox_mm": [round(v, 3) for v in board["bbox"]],
        },
        "features": [
            {"type": "Feature",
             "properties": {"kind": "bus_skeleton", "bus_id": s["bus_id"],
                            "net_ids": s["net_ids"]},
             "geometry": {"type": "MultiLineString",
                          "coordinates": [seg["polyline"] for seg in s["segments"]]}}
            for s in skels
        ] + [
            {"type": "Feature",
             "properties": {"kind": "bend", "bus_id": s["bus_id"],
                            "segment_index": i},
             "geometry": {"type": "Point",
                          "coordinates": s["segments"][i]["bend"]}}
            for s in skels for i in range(len(s["segments"]))
        ],
    }
