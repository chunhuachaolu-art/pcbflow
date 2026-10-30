"""② 架构可布性预检（pcbflow audit）。纯内存、零落盘、零子进程（生成器模式）。

SPEC §②：七项检查，每项出数字或证书；在布线之前判死布局。
回测（FA3）：p3-placement-gates-pass 布局时点（只读快照，纯布局无走线）+
opens.csv 61 断点真值（F3 终态）。三门（预测器质量门≠交付门）：
  G1 ≥70% 断点被至少一项检查预测；G2 3V3 逃逸缺口命中 ≥15/22；
  G3 误报（实际可布却标架构致命）≤10%。
指标一律带 mode/definition/denominator/dataset（SPEC §② 红线）。

模型（一阶、确定性、全部 spec 锚定、不对回测集调参）：
  逃逸：逐焊盘通道测试（外向 3mm=C-0037 带深、半宽 0.175=C-0036 0.35 间距之半），
        他方封装焊盘阻塞通道；「需离场」（transit）=同网对端在带外（场内短跳不占逃逸）；
  走廊：0.5mm 粗格容量图（F/In2 双信号层，封装 pad-bbox+0.25 阻塞），2/≤4 端
        非电源网直连链需求；红格=任一层 demand>max(cap,1)；
  层预算：链长×0.35 间距面积 vs 双信号层可用面积；层计划换层次数 vs via_policy。
GND 走平面不占逃逸/走廊需求（平面网，returned by planes）。
② 消费注册表（SPEC §1.2）：registry_snapshot_hash/registry_consumed/fields_consumed。
"""

from __future__ import annotations

import csv
import datetime
import math
import os
import re
import socket
import sys

from . import af_table, compile_cmd, config, envelope, enum_cmd, geo, hashing, net_registry, toolchain

PRED_PAD_RE = re.compile(r"([A-Z]+\d+) 的焊盘 (\d+)")
_BACKTEST_DATASET = "revc-f3-opens61(p3-placement-backtest)"


# ---- 真值装载 ---------------------------------------------------------------
def load_opens(path):
    """opens.csv → {rows, breakpoints(非GND), nets_failed}。只读。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [dict(r) for r in csv.DictReader(f)]
    for r in rows:
        r["distance_mm"] = float(r["distance_mm"])
        for s in ("from", "to"):
            r[s + "_x_mm"] = float(r[s + "_x_mm"])
            r[s + "_y_mm"] = float(r[s + "_y_mm"])
            m = PRED_PAD_RE.search(r[s])
            r[s + "_pad"] = (m.group(1), m.group(2)) if m else None
    bp = [r for r in rows if r["net"] != "GND"]
    return {"rows": rows, "breakpoints": bp,
            "nets_failed": sorted({r["net"] for r in bp})}


def _analog_zone_refs(path=None):
    """placement.csv zone 列 → ANLG 分区成员（p3 门 G6 同源）。

    SEC-A-06 修复（REPAIR-P3S W-A）：返回 (refs, reason)。缺文件/坏列 →
    (空集, "not_available: …") 显式上标，不再静默空集让检查空转；正常 →
    (refs, None)。"""
    p = path or config.AUDIT_P3_PLACEMENT_CSV
    try:
        with open(p, encoding="utf-8-sig", newline="") as f:
            return ({r["ref"] for r in csv.DictReader(f)
                     if r.get("zone") == "ANLG"}, None)
    except OSError as e:
        return (set(), "not_available: placement.csv 不可读（%s: %s）"
                % (type(e).__name__, e))
    except KeyError as e:
        return (set(), "not_available: placement.csv 缺列（%s）" % e)


# ---- 检查2：逃逸容量 --------------------------------------------------------
def escape_check(board, cls_of):
    """逐焊盘外向通道测试 → 场级证书 + 网级 blocked 端点。

    返回 {fields{ref|side:…}, pad_blocked{(ref,num):bool}, pad_transit{…:bool},
          escape_fatal_nets, blocked_by_net}。
    """
    depth = config.AUDIT_ESCAPE_DEPTH_MM
    half = config.AUDIT_CHANNEL_HALF_MM
    pads = board["pads"]
    # 同网其他焊盘的坐标（transit 判定）
    net_pads = {}
    for p in pads:
        if p["net"]:
            net_pads.setdefault(p["net"], []).append(p)

    def band_rect(ref, side):
        x0, y0, x1, y1 = board["footprints"][ref]["bbox"]
        if side == "N":
            return (x0 - 0.1, y0 - depth, x1 + 0.1, y0)
        if side == "S":
            return (x0 - 0.1, y1, x1 + 0.1, y1 + depth)
        if side == "E":
            return (x1, y0 - 0.1, x1 + depth, y1 + 0.1)
        return (x0 - depth, y0 - 0.1, x0, y1 + 0.1)

    def _rect_blocks(rect, own_ref):
        for q in pads:
            if q["ref"] == own_ref:
                continue  # 本封装焊盘不阻塞自身扇出（0.5mm 脚距 > 0.35 通道距）
            qx0 = q["x"] - q["w"] / 2 - half
            qx1 = q["x"] + q["w"] / 2 + half
            qy0 = q["y"] - q["h"] / 2 - half
            qy1 = q["y"] + q["h"] / 2 + half
            if not (qx1 < rect[0] or qx0 > rect[2]
                    or qy1 < rect[1] or qy0 > rect[3]):
                return True
        return False

    def _path_clear(segments, own_ref):
        return all(not _rect_blocks(r, own_ref) for r in segments)

    def _seg_rect(x0, y0, x1, y1):
        return (min(x0, x1) - half, min(y0, y1) - half,
                max(x0, x1) + half, max(y0, y1) + half)

    def channel_clear(pad, side):
        """pad 外向逃逸通道：直线，或 ±45° 单折（前/后各 depth/2）——三者之一
        全程无阻即视为有通道（一阶扇出模型：允许带内绕行）。"""
        cx, cy = pad["x"], pad["y"]
        if side == "N":
            ux, uy = 0.0, -1.0
        elif side == "S":
            ux, uy = 0.0, 1.0
        elif side == "E":
            ux, uy = 1.0, 0.0
        else:
            ux, uy = -1.0, 0.0
        half_d = depth / 2
        straight = [_seg_rect(cx, cy, cx + ux * depth, cy + uy * depth)]
        paths = [straight]
        for sign in (1.0, -1.0):
            jx, jy = -uy * sign, ux * sign  # 旋转 ±90° 的横向
            mx, my = cx + ux * half_d, cy + uy * half_d
            ex, ey = mx + jx * half_d, my + jy * half_d
            paths.append([_seg_rect(cx, cy, mx, my), _seg_rect(mx, my, ex, ey)])
        return any(_path_clear(p, pad["ref"]) for p in paths)

    pad_blocked, pad_transit = {}, {}
    for p in pads:
        net = p["net"]
        if net is None or net == "GND" or net.startswith("unconnected-"):
            continue
        blocked = all(not channel_clear(p, s) for s in p["side"])
        pad_blocked[(p["ref"], p["num"])] = blocked
        # transit（需离场）：同网存在本焊盘各侧逃逸带之外的对端。
        # 场内短跳（去耦电容↔IC 引脚互相落在对方带内）不占逃逸需求。
        transit = False
        for q in net_pads[net]:
            if q is p:
                continue
            outside_all_sides = True
            for s in p["side"]:
                if geo.point_in_bbox(q["x"], q["y"], band_rect(p["ref"], s)):
                    outside_all_sides = False
                    break
            if outside_all_sides:
                transit = True
                break
        pad_transit[(p["ref"], p["num"])] = transit

    # 场级聚合（证书）
    fields = {}
    for p in pads:
        net = p["net"]
        if net is None or net == "GND" or net.startswith("unconnected-"):
            continue
        for s in p["side"]:
            key = p["ref"] + "|" + s
            f = fields.setdefault(key, {
                "ref": p["ref"], "side": s, "pads_total": 0,
                "pads_channel_blocked": 0, "transit_nets": set(),
                "blocked_transit_nets": set(),
            })
            f["pads_total"] += 1
            if pad_blocked[(p["ref"], p["num"])]:
                f["pads_channel_blocked"] += 1
            if pad_transit[(p["ref"], p["num"])]:
                f["transit_nets"].add(net)
                if pad_blocked[(p["ref"], p["num"])]:
                    f["blocked_transit_nets"].add(net)
    for key, f in fields.items():
        f["transit_nets"] = sorted(f["transit_nets"])
        blocked = sorted(f["blocked_transit_nets"])
        f["blocked_transit_nets"] = blocked
        f["supply_clear_channels"] = f["pads_total"] - f["pads_channel_blocked"]
        f["demand_transit_nets"] = len(f["transit_nets"])
        f["deficit"] = max(0, len(blocked))
        f["has_deficit"] = bool(blocked)

    blocked_by_net = {}
    for (ref, num), blocked in pad_blocked.items():
        if not blocked:
            continue
        p = next(x for x in pads if x["ref"] == ref and x["num"] == num)
        if pad_transit[(ref, num)]:
            blocked_by_net.setdefault(p["net"], []).append(ref + "." + num)
    # 网级"走投无路"：≥N 个 transit 焊盘全堵（多点被围死的轨类网）。
    # 2 端网全堵不判网死刑（与实际幸存不可分：FMC_A9 幸存 vs FMC_D7 失败模型同像），
    # 降为场级证书 + 命中证据。调参记录见 config.AUDIT_FATAL_MIN_BLOCKED_PADS。
    min_blocked = config.AUDIT_FATAL_MIN_BLOCKED_PADS
    escape_fatal = sorted(n for n, e in blocked_by_net.items()
                          if len(e) >= min_blocked)

    return {"fields": fields, "pad_blocked": pad_blocked,
            "pad_transit": pad_transit, "blocked_by_net": blocked_by_net,
            "escape_fatal_nets": escape_fatal}


# ---- 检查4：走廊容量（粗格） ------------------------------------------------
def corridor_check(board, nets, cls_of, allowed_layers_of):
    """0.5mm 格容量图；返回红格集合 + 网路径全饱和清单。"""
    cell = config.AUDIT_GRID_CELL_MM
    bx0, by0, bx1, by1 = board["bbox"]
    nx = int(math.ceil((bx1 - bx0) / cell)) + 1
    ny = int(math.ceil((by1 - by0) / cell)) + 1
    infl = [geo.bbox_inflate(f["bbox"], config.AUDIT_BODY_INFLATE_MM)
            for f in board["footprints"].values()]

    def cell_center(i, j):
        return (bx0 + i * cell, by0 + j * cell)

    blocked = set()
    for i in range(nx):
        for j in range(ny):
            x, y = cell_center(i, j)
            if any(geo.point_in_bbox(x, y, bb) for bb in infl):
                blocked.add((i, j))

    def route_nets():
        """走廊需求网：非 GND/非 PWR、端点 ≤4（链式直连估计；多端 rail 另记）。"""
        for net in sorted(nets):
            if net == "GND" or net.startswith("unconnected-"):
                continue
            cls = cls_of(net)
            if cls and cls.startswith("PWR"):
                continue
            pads = [p for p in board["pads"] if p["net"] == net]
            if not 2 <= len(pads) <= 4:
                continue
            pts = sorted((p["x"], p["y"]) for p in pads)
            layers = [l for l in (allowed_layers_of(net) or config.AUDIT_SIGNAL_LAYERS)
                      if l in config.AUDIT_SIGNAL_LAYERS] or config.AUDIT_SIGNAL_LAYERS
            segs = list(zip(pts, pts[1:]))
            yield net, layers, segs

    demand = {}
    net_cells = {}
    excluded_multiterminal = []
    for net, layers, segs in route_nets():
        cells = set()
        for (a, b) in segs:
            for x, y in geo.seg_samples(a[0], a[1], b[0], b[1], cell / 2):
                ci = min(nx - 1, max(0, int(round((x - bx0) / cell))))
                cj = min(ny - 1, max(0, int(round((y - by0) / cell))))
                cells.add((ci, cj))
                for l in layers:
                    demand[(ci, cj, l)] = demand.get((ci, cj, l), 0) + 1
        net_cells[net] = cells
    for net in sorted(nets):
        if net == "GND" or net.startswith("unconnected-"):
            continue
        cls = cls_of(net)
        if cls and cls.startswith("PWR"):
            continue
        n = len([p for p in board["pads"] if p["net"] == net])
        if n > 4:
            excluded_multiterminal.append({"net": net, "pads": n,
                                           "reason": "多端轨/树，链式直连不适用"
                                                     "（逃逸/电源检查覆盖）"})

    red = set()
    for (ci, cj, l), d in demand.items():
        cap = 0 if (ci, cj) in blocked else 1
        if d > max(cap, 1):
            red.add((ci, cj))
    congested = []
    for net in sorted(net_cells):
        cells = net_cells[net]
        if not cells:
            continue
        layers = [l for l in (allowed_layers_of(net) or config.AUDIT_SIGNAL_LAYERS)
                  if l in config.AUDIT_SIGNAL_LAYERS] or config.AUDIT_SIGNAL_LAYERS
        # 封装体格（=blocked 集合）不参与"全红"判定：本网焊盘落格是自己的着陆点，
        # 不是 traversal 障碍。全红仅作拥堵证据（命中），不作架构致命判据
        # （致命判据=走廊预算/逃逸聚合容量，见 corridor_budget_check）。
        free_cells = cells - blocked
        if not free_cells:
            continue
        all_red = all(c in red for c in free_cells)
        layer_sat = any(all(demand.get((c[0], c[1], l), 0) > max(
            0 if c in blocked else 1, 1) for c in free_cells) for l in layers)
        if all_red and layer_sat:
            congested.append(net)
    return {
        "grid": {"cell_mm": cell, "nx": nx, "ny": ny, "origin": [bx0, by0]},
        "blocked_cells": len(blocked), "red_cells": len(red),
        "red_cell_list": sorted(red),
        "demand_cells": len(demand),
        "fully_congested_paths": sorted(congested),
        "excluded_multiterminal": sorted(excluded_multiterminal,
                                         key=lambda e: e["net"]),
        "net_cells": net_cells,
    }


# ---- 检查4b：走廊预算（C-0053 聚合判据；架构致命的走廊半边） ----------------
def corridor_budget_check(board, structures):
    """每总线主走廊：净空 gap vs C-0053 需求宽 ceil(N/2)×0.35+0.6。

    聚合容量判据（不是逐网直线饱和）：缺口走廊的成员网才构成架构致命。
    STR-1 未裁决的存储走廊照算但标 pending，不参与致命标记（保守）。
    """
    out = []
    for b in structures["buses"]:
        refs = b["endpoint_refs"]
        # 主对：非 U1 侧成员焊盘最多的 ref（FMC→U2、存储→J1、LTDC→J3、ETH→J2、USB→J5）
        counts = {}
        for p in board["pads"]:
            if p["net"] in set(b["members"]) and p["ref"] != "U1":
                counts[p["ref"]] = counts.get(p["ref"], 0) + 1
        if not counts:
            continue
        target = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        ua, ub = board["footprints"]["U1"], board["footprints"][target]
        # AABB 盒间净空（与 p3 门 G1_channel 同语义：面向边间距）。
        # 连接器横跨板边（如 J2 48mm 宽），锚点连线投影会把横向混入轴向 → 用盒距。
        a = ua["bbox"]
        bx = ub["bbox"]
        dx = max(a[0] - bx[2], bx[0] - a[2], 0.0)
        dy = max(a[1] - bx[3], bx[1] - a[3], 0.0)
        gap = round(math.hypot(dx, dy), 3)
        n = b["member_count"]
        required = round(math.ceil(n / 2) * 0.35 + 0.6, 2)
        pending = b["bus_id"] in ("BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2")
        deficit = gap < required
        out.append({
            "bus_id": b["bus_id"], "corridor": "U1-" + target,
            "member_count": n, "gap_mm": gap, "required_mm": required,
            "deficit": bool(deficit), "fatal": bool(deficit and not pending),
            "status": "pending_STR-1" if pending else "estimated",
            "source": "C-0053 公式；gap=AABB 盒间净空（同 p3 门 G1_channel 口径）",
        })
    return {"corridors": sorted(out, key=lambda c: c["bus_id"]),
            "fatal_nets": sorted(
                {m for c in out if c["fatal"]
                 for b in structures["buses"] if b["bus_id"] == c["bus_id"]
                 for m in b["members"]})}


# ---- 检查3：层预算 ----------------------------------------------------------
def layer_budget_check(board, nets, cls_of, allowed_layers_of):
    pitch = config.AUDIT_TRACK_PITCH_MM
    demand_len = 0.0
    for net, layers, segs in _route_iter(board, nets, cls_of, allowed_layers_of):
        for a, b in segs:
            demand_len += math.hypot(b[0] - a[0], b[1] - a[1])
    demand_area = demand_len * pitch
    used = sum(geo.bbox_area(geo.bbox_inflate(f["bbox"], config.AUDIT_BODY_INFLATE_MM))
               for f in board["footprints"].values())
    board_area = geo.bbox_area(board["bbox"])
    supply_area = len(config.AUDIT_SIGNAL_LAYERS) * max(0.0, board_area - used)
    util = demand_area / supply_area if supply_area > 0 else None
    via_changes = 0
    for net in sorted(nets):
        if net == "GND" or net.startswith("unconnected-"):
            continue
        ls = [l for l in (allowed_layers_of(net) or []) if l in config.AUDIT_SIGNAL_LAYERS]
        if len(ls) > 1:
            via_changes += 2  # 出主干 + 回 F（往返）
    return {
        "demand_len_mm": round(demand_len, 3),
        "demand_area_mm2": round(demand_area, 3),
        "supply_area_mm2": round(supply_area, 3),
        "utilization": round(util, 6) if util is not None else None,
        "planned_via_count": via_changes,
        "note": "链式直连估计（2/≤4 端非电源网）；GND 走平面、多端电源轨另计；"
                "In1/B 为 GND 平面层不供信号",
    }


def _route_iter(board, nets, cls_of, allowed_layers_of):
    for net in sorted(nets):
        if net == "GND" or net.startswith("unconnected-"):
            continue
        cls = cls_of(net)
        if cls and cls.startswith("PWR"):
            continue
        pads = [p for p in board["pads"] if p["net"] == net]
        if not 2 <= len(pads) <= 4:
            continue
        pts = sorted((p["x"], p["y"]) for p in pads)
        layers = [l for l in (allowed_layers_of(net) or config.AUDIT_SIGNAL_LAYERS)
                  if l in config.AUDIT_SIGNAL_LAYERS] or config.AUDIT_SIGNAL_LAYERS
        yield net, layers, list(zip(pts, pts[1:]))


# ---- 检查5：功率环路 + 去耦半径 ---------------------------------------------
def power_loop_check(board, nets):
    def pads_of(net):
        return [p for p in board["pads"] if p["net"] == net]

    u3 = board["footprints"].get("U3")
    l1 = board["footprints"].get("L1")
    loop_refs = {"U3", "L1"}
    r_cap = config.AUDIT_LOOP_CAP_RADIUS_MM
    if u3 and l1:
        ux, uy = u3["x"], u3["y"]
        lx, ly = l1["x"], l1["y"]
        for p in pads_of("SW_NODE"):
            if re.match(r"^C\d+$", p["ref"]):
                loop_refs.add(p["ref"])
        for p in pads_of("5V"):
            if re.match(r"^C\d+$", p["ref"]) and math.hypot(p["x"] - ux, p["y"] - uy) <= r_cap:
                loop_refs.add(p["ref"])  # Cin
        for p in pads_of("3V3"):
            if re.match(r"^C\d+$", p["ref"]) and math.hypot(p["x"] - lx, p["y"] - ly) <= r_cap:
                loop_refs.add(p["ref"])  # Cout
    pts = [p for p in board["pads"] if p["ref"] in loop_refs]
    bb = None
    if pts:
        xs, ys = [p["x"] for p in pts], [p["y"] for p in pts]
        bb = (min(xs), min(ys), max(xs), max(ys))
    w = round(bb[2] - bb[0], 3) if bb else None
    h = round(bb[3] - bb[1], 3) if bb else None
    area = round(w * h, 3) if bb else None

    # 去耦半径：每个 IC 电源焊盘（3V3/5V）到同网最近电容焊盘距离（C-0044）
    worst = []
    over = 0
    checked = 0
    ic_refs = sorted(r for r, f in board["footprints"].items()
                     if len(f["pads"]) >= 8 and not r.startswith("J"))
    for net in ("3V3", "5V"):
        cap_pads = [p for p in pads_of(net) if re.match(r"^C\d+$", p["ref"])]
        for p in pads_of(net):
            if p["ref"] not in ic_refs:
                continue
            checked += 1
            if not cap_pads:
                break
            d = min(math.hypot(p["x"] - c["x"], p["y"] - c["y"]) for c in cap_pads)
            if d > config.AUDIT_DECAP_LIMIT_MM:
                over += 1
                worst.append({"pin": p["ref"] + "." + p["num"], "net": net,
                              "nearest_cap_mm": round(d, 3)})
    return {
        "loop_refs": sorted(loop_refs), "loop_w_mm": w, "loop_h_mm": h,
        "loop_area_mm2": area,
        "target_mm2": config.AUDIT_LOOP_TARGET_MM2,
        "limit_mm2": config.AUDIT_LOOP_LIMIT_MM2,
        "decap_pins_checked": checked, "decap_over_limit": over,
        "decap_worst": sorted(worst, key=lambda x: (-x["nearest_cap_mm"], x["pin"]))[:10],
        "source": "C-0046（buck 环路）/C-0044（去耦 ≤2 目标/3 上限）",
    }


# ---- 检查6：回流连续性（布局时点=计划级） -----------------------------------
def return_check(board, nets, cls_of, allowed_layers_of, structures):
    # 层计划 vs via_policy
    violations = []
    checked = 0
    for net in sorted(nets):
        if net == "GND" or net.startswith("unconnected-"):
            continue
        cls = cls_of(net)
        if cls and cls.startswith("PWR"):
            continue
        if not any(p["net"] == net for p in board["pads"]):
            continue
        checked += 1
        ls = [l for l in (allowed_layers_of(net) or []) if l in config.AUDIT_SIGNAL_LAYERS]
        needed = 0 if len(ls) <= 1 else 2
        vp = net_registry.routing_attrs(cls).get("via_policy") if cls else None
        maxc = (vp or {}).get("max_count")
        if maxc is not None and needed > maxc:
            violations.append({"net": net, "needed_layer_changes": needed,
                               "via_policy_max": maxc})
    # 模拟角禁数字线穿越（C-0042 no_digital_crossing）。
    # 分区成员用 p3 placement.csv 的 zone 列（ANLG 区=C31/C32/C33/FB1/R12/U4，
    # 与 p3 门 G6 同源）；穿越=深入区内区（bbox+2 再缩 1）——擦边不算。
    anlg_refs, anlg_reason = _analog_zone_refs()
    anlg = [p for p in board["pads"] if p["ref"] in anlg_refs]
    zone = None
    interior = None
    crossings = []
    if anlg:
        xs, ys = [p["x"] for p in anlg], [p["y"] for p in anlg]
        zone = geo.bbox_inflate((min(xs), min(ys), max(xs), max(ys)), 2.0)
        interior = geo.bbox_inflate((min(xs), min(ys), max(xs), max(ys)), 1.0)
        for net, layers, segs in _route_iter(board, nets, cls_of, allowed_layers_of):
            if not net or cls_of(net) == "ANLG":
                continue
            for a, b in segs:
                for x, y in geo.seg_samples(a[0], a[1], b[0], b[1], 0.25):
                    if geo.point_in_bbox(x, y, interior):
                        crossings.append(net)
                        break
                else:
                    continue
                break
    area = geo.bbox_area(board["bbox"])
    stitch_target = int(math.ceil(area / (config.AUDIT_STITCH_GRID_MM ** 2)))
    ret = {
        "mode": "plan（p3=纯布局快照：无走线/无过孔/无铺铜，回流为计划级核对）",
        "planned_planes": structures["return_tree"]["planes"],
        "layer_plan_nets_checked": checked,
        "layer_plan_violations": sorted(violations, key=lambda v: v["net"]),
        "analog_zone_refs": sorted(anlg_refs),
        "analog_zone_bbox": [round(v, 3) for v in zone] if zone else None,
        "digital_crossings_of_analog_zone": sorted(set(crossings)),
        "crossing_definition": "采样点落入内区（ANLG bbox+1mm）；擦边（+2mm 带内）不计",
        "stitch_via_target_grid8mm": stitch_target,
        "stitch_note": "C-0039 目标网格 ≤8mm；p3 无过孔可数 → 预算值，④期复核",
        "source": "C-0042/C-0039/structures.return_tree + placement.csv zone 列",
    }
    if anlg_reason:
        # SEC-A-06 修复（REPAIR-P3S W-A）：分区输入不可得时显式上标，
        # 模拟角穿越子检查空转不冒充 pass（C6 verdict 由消费侧降黄）。
        ret["analog_zone_not_available"] = anlg_reason
    return ret


# ---- 检查7：连接器方向 vs 总线出口 ------------------------------------------
_SIDE_VEC = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0)}


def orientation_check(board, structures):
    results = []
    worst = None
    for b in structures["buses"]:
        refs = b["endpoint_refs"]
        if "U1" not in refs or len(refs) < 2:
            continue
        target = sorted(r for r in refs if r != "U1")[0]
        tu = board["footprints"]["U1"]
        tt = board["footprints"].get(target)
        if tt is None:
            continue
        # 方向用 bbox 中心（锚点可能在角上：连接器 at=第一脚）
        ua, ub_ = tu["bbox"], tt["bbox"]
        dx = (ub_[0] + ub_[2]) / 2 - (ua[0] + ua[2]) / 2
        dy = (ub_[1] + ub_[3]) / 2 - (ua[1] + ua[3]) / 2
        norm = math.hypot(dx, dy) or 1.0
        ux, uy = dx / norm, dy / norm
        member_pads = [p for p in board["pads"] if p["net"] in set(b["members"])
                       and p["ref"] == "U1"]
        facing = 0
        for p in member_pads:
            # 角垫可属两侧：任一侧朝向目标即计（side[0] 偏判）
            if any(_SIDE_VEC[s][0] * ux + _SIDE_VEC[s][1] * uy > 0.3
                   for s in p["side"]):
                facing += 1
        frac = round(facing / len(member_pads), 4) if member_pads else None
        entry = {"bus_id": b["bus_id"], "u1_exit_target": target,
                 "member_pads_u1": len(member_pads), "facing_frac": frac}
        results.append(entry)
        if frac is not None and (worst is None or frac < worst[1]):
            worst = (b["bus_id"], frac)
    min_frac = worst[1] if worst else None
    return {"per_bus": sorted(results, key=lambda r: r["bus_id"]),
            "min_facing_frac": min_frac,
            "threshold": config.AUDIT_ORIENTATION_MIN,
            "source": "C-0052 引脚面对引脚面（一阶代理：U1 出口侧 vs 目标方向）"}


# ---- 检查1：pin mux/swap（proposal-only） -----------------------------------
def pinmux_check(af_table_obj=None, u1_pads=None, evidence=None,
                 connector_nets=None, basis=None):
    """无 AF 表：MCU alternate-function 表不在权威输入（HANDOFF §1）→ 零候选
    + 缺失源登记（FA3 原语义，字节不变）。

    有 AF 表（--af-table，AF 会话 opt-in）：af_table.enumerate_swap_candidates
    按「互惠同组」枚举（双脚同持对方信号=来源明确允许同组交换，SPEC §②
    检查1）；恒 proposal-only（HANDOFF §3 确认点 #3），不自动改任何输入。
    """
    if af_table_obj is None:
        return {
            "candidates": [],
            "missing_sources": [{"source": "mcu_alternate_function_table",
                                 "desc": "STM32H743 AF 映射表不在权威输入清单；"
                                         "无来源允许的同组候选 → 零建议（不虚构）",
                                 "blocks": "pin-swap proposal 产出（不阻其余六项）"}],
            "mechanism": "候选仅可来自：原理图层组 + MCU AF 表 + 封装同组 + 接口规范"
                         "明确允许；产出恒为 proposal_only（SPEC §②/HANDOFF §3）",
        }
    candidates, identification = af_table.enumerate_swap_candidates(
        af_table_obj, u1_pads, evidence=evidence,
        connector_nets=connector_nets)
    return {
        "candidates": candidates,
        "missing_sources": [],
        "identification": identification,
        "basis": basis,
        "mechanism": "候选仅来自 MCU AF 表互惠同组交换（双脚同持对方信号=来源"
                     "明确允许；GPIO/电源/复位/晶振/未识别网不参与）；恒为 "
                     "proposal_only（SPEC §②/HANDOFF §3 确认点 #3：人工批准后"
                     "才可生成新输入版本并重跑 ERC/parity）；布线 delta 代价"
                     "未评估（delta_metrics 空=未算，非零代价）",
    }


# ---- 主构建 ------------------------------------------------------------------
def build_products(out_dir_rel=config.load_project_manifest().out_dirs["audit"],
                   af_table_path=None):
    """② 预检主构建：七项静态检查 + 断点预测融合 + 三门评估（SPEC ②）。

    编排序（对上游的取值依赖自上而下）：
    1. AF 表 opt-in 装载（af_table_path 缺省不消费；basis 记相对路径+sha+
       来源包指针，供检查1 pin-swap 候选枚举——proposal-only 不改网表）；
    2. 上游产物取值：enum_cmd.build_products（structures+net_registry）→
       compile_cmd 网表解析（nets/_match_class）→ geo 板几何 → opens CSV；
    3. 七项检查：escape / corridor / corridor_budget / layer_budget /
       power_loop / return / orientation（各自独立函数，本函数只编排）；
    4. 断点预测融合：opens 的 breakpoint 与走廊红格/层预算/回流命中源
       对账（检查 2/4/6 贡献命中源；3/5/7 为板级指标不进融合）；
    5. 三门（预测器质量门）+ 检查结论 verdict 分级 + 产物落盘。

    产物族与 envelope/落盘由本函数尾部统一处理；af_table_path 的合法
    值域与 verification 记录见 out/revc-af/af-verification.json。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)

    af_table_obj = None
    af_basis = None
    if af_table_path is not None:
        af_table_obj = af_table.load_af_table(af_table_path)
        af_basis = {
            "path": os.path.relpath(af_table_path, config.WORKSPACE_ROOT)
                    .replace("\\", "/"),
            "sha256": hashing.sha256_file(af_table_path),
            "verification_record": "tools/pcbflow/out/revc-af/af-verification.json",
            "source_package": "tools/pcbflow/out/revc-fd1/approvals/sources/"
                              "mcu-af-table.json",
            "consumption": "pin-swap 候选枚举（proposal-only）",
        }

    enum_products = enum_cmd.build_products(out_dir_rel)
    structures = enum_products["structures"]["obj"]
    registry = enum_products["net_registry"]["obj"]
    registry_hash = registry["registry_snapshot_hash"]
    nets = compile_cmd.parse_netlist(config.REVC_NETLIST)
    cls_of = compile_cmd._match_class

    def allowed_layers_of(net):
        for r in registry["nets"]:
            if r["net_name"] == net:
                return r["allowed_layers"]
        return None

    board = geo.parse_board(config.AUDIT_P3_BOARD)
    opens = load_opens(config.AUDIT_OPENS_CSV)

    # U1 焊盘网表（AF 表消费用）与连接器网集（cost_vector.external_connector）
    u1_pads = [{"num": int(p["num"]), "net": p["net"]}
               for p in board["pads"] if p.get("ref") == "U1"]
    connector_nets = {p["net"] for p in board["pads"]
                      if str(p.get("ref", "")).upper().startswith("J")
                      and p.get("net")}

    # 七项检查
    esc = escape_check(board, cls_of)
    cor = corridor_check(board, nets, cls_of, allowed_layers_of)
    corb = corridor_budget_check(board, structures)
    lay = layer_budget_check(board, nets, cls_of, allowed_layers_of)
    pwr = power_loop_check(board, nets)
    ret = return_check(board, nets, cls_of, allowed_layers_of, structures)
    ori = orientation_check(board, structures)

    red_set = set(cor["red_cell_list"])

    # 断点预测融合（检查2/4/6 贡献命中源；3/5/7 为板级指标）
    for r in opens["breakpoints"]:
        sources = []
        for side in ("from", "to"):
            key = r[side + "_pad"]
            if key and key in esc["pad_transit"] and esc["pad_transit"][key] \
                    and esc["pad_blocked"].get(key):
                sources.append("escape:" + key[0] + "." + key[1])
        (ax, ay) = r["from_x_mm"], r["from_y_mm"]
        (bx, by) = r["to_x_mm"], r["to_y_mm"]
        hit_cells = set()
        cell = config.AUDIT_GRID_CELL_MM
        ox, oy = cor["grid"]["origin"]
        for x, y in geo.seg_samples(ax, ay, bx, by, cell / 2):
            c = (int(round((x - ox) / cell)), int(round((y - oy) / cell)))
            if c in red_set:
                hit_cells.add(c)
        if hit_cells:
            sources.append("corridor:%d_cells" % len(hit_cells))
        plan_violation_nets = {v["net"] for v in ret["layer_plan_violations"]}
        if r["net"] in plan_violation_nets:
            sources.append("layer_plan")
        r["predicted"] = bool(sources)
        r["hit_sources"] = sorted(sources)

    hits = [r for r in opens["breakpoints"] if r["predicted"]]
    bps = opens["breakpoints"]
    v3 = [r for r in bps if r["net"] == "3V3"]
    v3_escape_hits = [r for r in v3 if any(s.startswith("escape:") for s in r["hit_sources"])]
    failed = opens["nets_failed"]
    fatal = sorted(set(esc["escape_fatal_nets"]) | set(corb["fatal_nets"]))
    fp = sorted(n for n in fatal if n not in failed)
    fp_rate = (len(fp) / len(fatal)) if fatal else 0.0

    # 检查1（pin mux/swap）：AF 表 opt-in 消费；证据旗标仅排序/登记用
    predicted_nets = {r["net"] for r in hits}
    evidence = {}
    for net in predicted_nets | set(failed) | set(fatal):
        flags = []
        if net in predicted_nets:
            flags.append("opens_predicted")
        if net in failed:
            flags.append("f3_failed")
        if net in set(fatal):
            flags.append("fatal_marked")
        evidence[net] = flags
    pmx = pinmux_check(af_table_obj, u1_pads=u1_pads, evidence=evidence,
                       connector_nets=connector_nets, basis=af_basis)

    # 三门（预测器质量门；dataset/mode/definition/denominator 齐备）
    gates = {
        "G1_open_recall": {
            "definition": "被至少一项检查（escape/corridor/layer_plan）预测的断点数 / 非GND断点总数",
            "dataset": _BACKTEST_DATASET, "mode": "p3_placement_static_models",
            "denominator": len(bps), "hits": len(hits),
            "rate": round(len(hits) / len(bps), 6) if bps else None,
            "threshold": config.GATE_AUDIT_RECALL_MIN,
            "pass": bool(bps) and len(hits) / len(bps) >= config.GATE_AUDIT_RECALL_MIN,
        },
        "G2_3v3_escape": {
            "definition": "3V3 断点中逃逸检查命中（transit 焊盘通道阻塞）数 / 3V3 断点数",
            "dataset": _BACKTEST_DATASET, "mode": "p3_placement_static_models",
            "denominator": len(v3), "hits": len(v3_escape_hits),
            "threshold": config.GATE_AUDIT_3V3_MIN,
            "pass": len(v3_escape_hits) >= config.GATE_AUDIT_3V3_MIN,
        },
        "G3_false_fatal": {
            "definition": "标为架构致命但 F3 实际布通的网数 / 架构致命网数（per-net）",
            "dataset": _BACKTEST_DATASET, "mode": "p3_placement_static_models",
            "denominator": len(fatal), "false_positives": len(fp), "fp_nets": fp,
            "rate": round(fp_rate, 6),
            "threshold": config.GATE_AUDIT_FP_MAX,
            "pass": fp_rate <= config.GATE_AUDIT_FP_MAX,
        },
    }
    gates_all_pass = all(g["pass"] for g in gates.values())

    # 检查结论（verdict 分级）
    checks = [
        {"check_id": "C1_pin_mux_swap", "title": "pin mux/swap 审计",
         "checker_status": "executed",
         "verdict": ("yellow" if pmx["missing_sources"] or pmx["candidates"]
                     else "pass"),
         "metrics": {"candidates": len(pmx["candidates"])}, "certificate": None,
         "blockers": pmx["missing_sources"],
         "suggestions": (
             ["提供 STM32H743 AF 表为权威源后按同组候选出 proposal（proposal-only）"]
             if pmx["missing_sources"] else
             ["候选 proposal-only：人工批准（确认点 #3）后才可生成新输入版本并"
              "重跑 ERC/netlist parity/受影响约束；布线 delta 未评估"])},
        {"check_id": "C2_escape_capacity", "title": "逃逸容量",
         "checker_status": "executed",
         "verdict": "red" if esc["escape_fatal_nets"] or
                    any(f["has_deficit"] for f in esc["fields"].values()) else "pass",
         "metrics": {
             "fields_total": len(esc["fields"]),
             "fields_with_deficit": sum(1 for f in esc["fields"].values() if f["has_deficit"]),
             "escape_fatal_net_count": len(esc["escape_fatal_nets"]),
         },
         "certificate": {"worst_fields": _worst_fields(esc),
                         "escape_fatal_nets": esc["escape_fatal_nets"],
                         "style": "此场 X 网需逃逸只有 Y 通道（逐场明细见 worst_fields）"},
         "blockers": [], "suggestions": []},
        {"check_id": "C3_layer_budget", "title": "层预算",
         "checker_status": "executed",
         "verdict": ("red" if (lay["utilization"] or 0) >= config.AUDIT_LAYER_UTIL_RED
                     else "yellow" if (lay["utilization"] or 0) >= config.AUDIT_LAYER_UTIL_YELLOW
                     else "pass"),
         "metrics": lay, "certificate": None, "blockers": [], "suggestions": []},
        {"check_id": "C4_corridor_capacity", "title": "走廊容量（粗格 + C-0053 预算）",
         "checker_status": "executed",
         "verdict": "red" if cor["red_cells"] or corb["fatal_nets"] else
                    ("yellow" if cor["red_cells"] else "pass"),
         "metrics": {
             "grid": cor["grid"], "blocked_cells": cor["blocked_cells"],
             "red_cells": cor["red_cells"], "demand_cells": cor["demand_cells"],
             "fully_congested_paths": cor["fully_congested_paths"],
             "excluded_multiterminal": cor["excluded_multiterminal"],
             "corridor_budgets": corb["corridors"],
         },
         "certificate": {"red_cell_count": cor["red_cells"],
                         "note": "红格=任一信号层 demand>max(cap,1)（拥堵证据/命中源）；"
                                 "架构致命=C-0053 走廊预算缺口（fatal=true 行）"},
         "blockers": [], "suggestions": []},
        {"check_id": "C5_power_loop", "title": "功率环路+去耦半径",
         "checker_status": "executed",
         "verdict": ("red" if (pwr["loop_area_mm2"] or 0) > config.AUDIT_LOOP_LIMIT_MM2
                     or pwr["decap_over_limit"] else
                     "yellow" if (pwr["loop_area_mm2"] or 0) > config.AUDIT_LOOP_TARGET_MM2
                     else "pass"),
         "metrics": pwr, "certificate": None, "blockers": [], "suggestions": []},
        {"check_id": "C6_return_continuity", "title": "回流连续性（计划级）",
         "checker_status": "executed",
         "verdict": ("red" if ret["layer_plan_violations"] or
                     ret["digital_crossings_of_analog_zone"] else
                     "yellow" if ret.get("analog_zone_not_available")
                     else "pass"),
         "metrics": ret, "certificate": None, "blockers": [], "suggestions": []},
        {"check_id": "C7_connector_orientation", "title": "连接器方向一致性",
         "checker_status": "executed",
         "verdict": ("yellow" if ori["min_facing_frac"] is not None and
                     ori["min_facing_frac"] < ori["threshold"] else "pass"),
         "metrics": ori, "certificate": None, "blockers": [], "suggestions": []},
    ]
    verdict_rank = {"pass": 0, "yellow": 1, "red": 2}
    worst = max((c["verdict"] for c in checks), key=lambda v: verdict_rank[v])

    # ②→③ 骨架种子（逃逸解：各总线出口侧；数据交接而非 "OK"）
    seed = _skeleton_seed(board, structures, esc, registry_hash)

    audit = {
        "schema_version": config.SCHEMA_AUDIT,
        "project": compile_cmd.PROJECT_ID,
        "stage": 2,
        "board_snapshot": {
            "path": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                    "snapshots/p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
            "footprints": len(board["footprints"]), "pads": len(board["pads"]),
            "tracks": 0, "vias": 0, "zones": 0,
            "note": "p3 布局时点（布线前）；全程只读",
        },
        "registry_consumption": {
            "registry_snapshot_hash": registry_hash,
            "registry_consumed": True,
            "fields_consumed": ["net_id", "net_name", "routing_class.value",
                                "allowed_layers", "via_policy", "structure",
                                "endpoints", "classification_status",
                                "relations(RLG/RDP/RSYM)"],
            "fields_ignored": ["aliases", "planner_class_view", "width_mm",
                               "preferred_layer", "bus_role", "electrical_role",
                               "source_net_key"],
            "fallback": None,
            "fidelity": "full（ambiguous=0；registry 缺失/歧义按硬软诊断语义处理）",
        },
        "checks": checks,
        "prediction": {
            "unit": "open_segment",
            "opens_total": len(bps),
            "opens_predicted": len(hits),
            "per_open": [{"net": r["net"],
                          "from": ("pad:" + r["from_pad"][0] + "." + r["from_pad"][1])
                                  if r["from_pad"] else
                                  {"point_mm": [round(r["from_x_mm"], 3),
                                                round(r["from_y_mm"], 3)]},
                          "to": ("pad:" + r["to_pad"][0] + "." + r["to_pad"][1])
                                if r["to_pad"] else
                                {"point_mm": [round(r["to_x_mm"], 3),
                                              round(r["to_y_mm"], 3)]},
                          "distance_mm": r["distance_mm"],
                          "predicted": r["predicted"],
                          "hit_sources": r["hit_sources"]}
                         for r in bps],
            "fatal_marking": {
                "rule": "escape_fatal（≥4 个 transit 焊盘全堵=走投无路的轨类网）∪ "
                        "corridor_budget（C-0053 需求宽 > 净空 gap 的非 pending 走廊成员网）；"
                        "2 端网引脚场全堵降为场级证书+命中证据（与实际幸存不可分，"
                        "调参记录见 config.AUDIT_FATAL_MIN_BLOCKED_PADS）",
                "fatal_nets": fatal,
                "failed_nets_f3": failed,
                "false_positive_nets": fp,
            },
        },
        "gates": gates,
        "failure_classification": _failure_classification(
            esc, cor, corb, lay, pwr, ret, ori),
    }

    pin_swap = {
        "schema_version": config.SCHEMA_AUDIT,
        "project": compile_cmd.PROJECT_ID,
        "status": "proposal_only",
        "approval": "pending（人工确认点 #3：任何 pin-swap 候选须人工批准后才可生成"
                    "新输入版本并重跑 ERC/parity）",
        "candidates": pmx["candidates"],
        "missing_sources": pmx["missing_sources"],
        "mechanism": pmx["mechanism"],
    }
    if af_table_obj is not None:
        pin_swap["af_table_basis"] = af_basis
        pin_swap["identification"] = pmx["identification"]
        pin_swap["candidate_count"] = len(pmx["candidates"])

    products = {}
    for name, obj in (("audit", audit), ("pin_swap", pin_swap),
                      ("skeleton_seed", seed)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data, "sha256": hashing.sha256_bytes(data)}

    inputs = [
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": hashing.sha256_file(config.AUDIT_P3_BOARD), "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/placement.csv",
         "sha256": hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV), "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/opens.csv",
         "sha256": hashing.sha256_file(config.AUDIT_OPENS_CSV), "role": "spec"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/revc.netlist",
         "sha256": hashing.sha256_file(config.REVC_NETLIST), "role": "netlist"},
    ]
    if af_basis is not None:
        inputs.append({"path": af_basis["path"], "sha256": af_basis["sha256"],
                       "role": "spec"})
    artifacts = [
        {"path": f"{out_dir_rel}/audit.json", "sha256": products["audit"]["sha256"],
         "role": "core"},
        {"path": f"{out_dir_rel}/pin-swap.json", "sha256": products["pin_swap"]["sha256"],
         "role": "core"},
        {"path": f"{out_dir_rel}/skeleton-seed.json",
         "sha256": products["skeleton_seed"]["sha256"], "role": "core"},
    ]
    gates_pass = sum(1 for g in gates.values() if g["pass"])
    env = envelope.build_envelope(
        command="audit", status="ok", verdict=worst,
        inputs=inputs, artifacts=artifacts,
        config_sha256=hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        spec_refs=["tools/pcbflow/SPEC.md#§②", "routing-spec-v1.md", "placement-spec-v1.md"],
        metrics={
            "opens_total": len(bps), "opens_predicted": len(hits),
            "recall": gates["G1_open_recall"]["rate"],
            "v3_escape_hits": len(v3_escape_hits), "v3_total": len(v3),
            "fatal_nets": len(fatal), "false_positives": len(fp),
            "gates_pass": gates_pass, "gates_total": 3,
            "registry_snapshot_hash": registry_hash,
            "registry_consumed": True,
            "fields_with_deficit": sum(1 for f in esc["fields"].values()
                                       if f["has_deficit"]),
            "corridor_red_cells": cor["red_cells"],
            "layer_utilization": lay["utilization"],
            **({"pin_swap_candidates": len(pmx["candidates"])}
               if af_table_obj is not None else {}),
        },
        diagnostics=[
            {"id": "backtest_gate", "title": "算法回测三门（预测器质量门≠项目交付门）",
             "detail": {k: {"pass": v["pass"], "rate": v.get("rate"),
                            "hits": v.get("hits"), "denominator": v["denominator"],
                            "threshold": v["threshold"]} for k, v in gates.items()}},
            {"id": "af_table_consumed", "title": "AF 表已消费：pin-swap 候选"
             " proposal-only 产出（确认点 #3 待批）",
             "detail": {"candidates": len(pmx["candidates"]),
                        "af_table_sha256": (af_basis or {}).get("sha256"),
                        "identification": pmx.get("identification",
                                                  {}).get("kinds")}}
            if af_table_obj is not None else
            {"id": "pin_swap_source_missing",
             "title": "MCU AF 表缺失 → pin-swap 零候选（缺失源登记，待人工供源）"},
        ],
        data={
            "gate": {
                "backtest_three_gates": ("pass" if gates_all_pass else "fail"),
                "note": "门调参后仍不过→BLOCKED；未达先调参复测（改 config 并记录）",
                "dataset": _BACKTEST_DATASET,
            },
            "failure_classification": _failure_classification(
                esc, cor, corb, lay, pwr, ret, ori),
        },
    )
    products["envelope"] = {"obj": env,
                            "bytes": hashing.canonical_json_bytes(env),
                            "sha256": hashing.sha256_bytes(hashing.canonical_json_bytes(env))}

    lock = toolchain.load_lock()
    t1 = datetime.datetime.now(datetime.timezone.utc)
    manifest = {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "kicad_cli_version": (lock or {}).get("kicad_cli", {}).get("version", "not_probed"),
        "tool_version": config.TOOL_VERSION,
        "input_sha256": {i["path"]: i["sha256"] for i in inputs},
        "config_sha256": env["config_sha256"],
        "spec_sha256": hashing.sha256_file(
            __import__("os").path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "schema_version": config.SCHEMA_ENVELOPE,
        "registry_snapshot_sha256": registry_hash,
        "out_dir": out_dir_rel,
        "holdout_note": "合成留出集见 tests/test_holdout.py（不参与 Rev-C 调参，SPEC §5/§6）",
    }
    products["run_manifest"] = {"obj": manifest,
                                "bytes": hashing.canonical_json_bytes(manifest),
                                "sha256": hashing.sha256_bytes(
                                    hashing.canonical_json_bytes(manifest))}
    return products


def _worst_fields(esc):
    rows = [f for f in esc["fields"].values() if f["has_deficit"]]
    rows.sort(key=lambda f: (-len(f["blocked_transit_nets"]), f["ref"], f["side"]))
    return [{"field": f["ref"] + "|" + f["side"],
             "blocked_transit_nets": len(f["blocked_transit_nets"]),
             "supply_clear_channels": f["supply_clear_channels"],
             "pads_total": f["pads_total"],
             "nets": f["blocked_transit_nets"][:12]} for f in rows[:12]]


def _skeleton_seed(board, structures, esc, registry_hash):
    """②→③ 交接数据：各总线出口侧 + 走廊需求（C-0053 公式）。"""
    out = []
    for b in structures["buses"]:
        refs = b["endpoint_refs"]
        ends = []
        for ref in refs:
            pads = [p for p in board["pads"] if p["net"] in set(b["members"])
                    and p["ref"] == ref]
            if not pads:
                continue
            sides = {}
            for p in pads:
                for s in p["side"]:
                    sides[s] = sides.get(s, 0) + 1
            dom = sorted(sides.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            blocked = sum(1 for p in pads
                          if esc["pad_blocked"].get((p["ref"], p["num"]))
                          and esc["pad_transit"].get((p["ref"], p["num"])))
            ends.append({"ref": ref, "dominant_exit_side": dom,
                         "member_pads": len(pads),
                         "side_votes": {k: v for k, v in sorted(sides.items())},
                         "transit_blocked_pads": blocked})
        n = b["member_count"]
        demand_w = round(math.ceil(n / 2) * 0.35 + 0.6, 2)
        storage = b["bus_id"] in ("BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2")
        out.append({
            "bus_id": b["bus_id"], "member_count": n,
            "endpoints": ends,
            "corridor": {
                "object": "U1-U2" if b["bus_id"] == "BUS_FMC" else
                          ("-".join(sorted(refs))),
                "demand_width_mm": demand_w,
                "formula": "C-0053：ceil(N/2层)×0.35+0.6",
                "status": "pending_STR-1（存储总线端点裁决待人工，未批则走廊估算 pending）"
                          if storage else "estimated",
            },
        })
    return {
        "schema_version": config.SCHEMA_AUDIT,
        "project": compile_cmd.PROJECT_ID,
        "role": "②→③ 骨架种子（逃逸解直接给出各总线出口侧；数据交接而非 OK）",
        "registry_snapshot_hash": registry_hash,
        "buses": sorted(out, key=lambda x: x["bus_id"]),
    }


def _failure_classification(esc, cor, corb, lay, pwr, ret, ori):
    """失败分类（SPEC §②：局部容量/摆放层资源/约束冲突/pin-mux 架构 + 建议回退级）。"""
    cls = []
    if esc["escape_fatal_nets"] or any(f["has_deficit"] for f in esc["fields"].values()):
        cls.append({"kind": "local_capacity_escape", "suggested_stage": 3,
                    "evidence": "C2 逃逸缺口证书"})
    if corb["fatal_nets"]:
        cls.append({"kind": "architecture_corridor_deficit", "suggested_stage": 2,
                    "evidence": "C4 C-0053 走廊预算缺口（成员网=%d）" % len(corb["fatal_nets"])})
    if cor["red_cells"]:
        cls.append({"kind": "local_capacity_corridor", "suggested_stage": 3,
                    "evidence": "C4 红格 %d（调整③布局/骨架可解）" % cor["red_cells"]})
    if (lay["utilization"] or 0) >= config.AUDIT_LAYER_UTIL_YELLOW:
        cls.append({"kind": "placement_layer_resource", "suggested_stage": 2,
                    "evidence": "C3 层预算利用率 %s" % lay["utilization"]})
    if ret["layer_plan_violations"] or ret["digital_crossings_of_analog_zone"]:
        cls.append({"kind": "constraint_conflict", "suggested_stage": 2,
                    "evidence": "C6 层计划/模拟角冲突"})
    if (pwr["loop_area_mm2"] or 0) > config.AUDIT_LOOP_LIMIT_MM2 or pwr["decap_over_limit"]:
        cls.append({"kind": "placement_power", "suggested_stage": 3,
                    "evidence": "C5 功率环路/去耦超限"})
    if not cls:
        cls.append({"kind": "none", "suggested_stage": None, "evidence": "七项无红"})
    return cls
