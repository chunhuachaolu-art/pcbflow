"""④ 细布 dry-run：匝道（最小费用最大流）+ 车道（共享池流分配）（FC1/FC3）。

SPEC v1.3 §10.1 步骤 1/2、§10.2 route view 消费、§10.3 求解器三态、
§16.4 route dry-run 验收。内存 dry-run：零写板、零 live commit、零 --save-board。

匝道：逐 IC 引脚场，transit 网 →（pad,side）净空通道 二部匹配，MCMF，
费用=直线/单折/出口侧偏好；flow<demand → UNSAT+最小割证书。
车道：走廊共享车道池（按 signal layer 分池，C-0053 ceil(N/2) 离散化），
bus→(layer,lane) 直接指派边，MCMF；干道层偏好=控制（registry allowed 硬权限内）。

④ 控制升级（consumer-gate-4 已批，FC3 会话）：protect_keepout 通道命中从
advisory 罚价升级为候选接受语义——M 系数 dominating 正常费用总和，MCMF 先
最小化控制违例数、再最小化正常费用（lex 首位，fc3-D1）；max-flow 阶段不受
费用影响 → 物理可行性与 SAT/UNSAT 三态红线不变；控制违例逐 run/逐赋值单列，
不与 UNSAT（物理不可布）混淆。未绑计划=FC1 收官态零扰动。

通道几何与 audit_cmd.escape_check（C2）同口径（直线/±45° 单折、同 ref 焊盘
不互堵）；测试强制聚合等价。所有失败带 §1.4 归因与回退建议；无证书不写 UNSAT。
"""

from __future__ import annotations

import datetime
import json
import math
import os
import socket
import sys

from . import config, flow, hashing, route_view

SIDE_ORDER = ("N", "E", "S", "W")
LANE_MARGIN_MM = 0.6  # C-0053 需求宽公差项（车道池离散化扣除）


# ---- 匝道几何（C2 同口径） --------------------------------------------------
def _channel_geom(board):
    pads = board["pads"]
    depth = config.AUDIT_ESCAPE_DEPTH_MM
    half = config.AUDIT_CHANNEL_HALF_MM

    def rect_blocks(rect, own_ref):
        for q in pads:
            if q["ref"] == own_ref:
                continue
            qx0 = q["x"] - q["w"] / 2 - half
            qx1 = q["x"] + q["w"] / 2 + half
            qy0 = q["y"] - q["h"] / 2 - half
            qy1 = q["y"] + q["h"] / 2 + half
            if not (qx1 < rect[0] or qx0 > rect[2] or qy1 < rect[1]
                    or qy0 > rect[3]):
                return True
        return False

    def seg_rect(x0, y0, x1, y1):
        return (min(x0, x1) - half, min(y0, y1) - half,
                max(x0, x1) + half, max(y0, y1) + half)

    def channel_clear(pad, side):
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
        paths = [[seg_rect(cx, cy, cx + ux * depth, cy + uy * depth)]]
        for sign in (1.0, -1.0):
            jx, jy = -uy * sign, ux * sign
            mx, my = cx + ux * half_d, cy + uy * half_d
            ex, ey = mx + jx * half_d, my + jy * half_d
            paths.append([seg_rect(cx, cy, mx, my), seg_rect(mx, my, ex, ey)])
        results = [all(not rect_blocks(r, pad["ref"]) for r in p)
                   for p in paths]
        clear = any(results)
        return clear, ("straight" if (clear and results[0]) else
                       ("dogleg" if clear else "blocked"))

    return channel_clear


def _keepout_regions(view_ctx, ext):
    """protect_keepout 控制组 → (refs 集合, 膨胀 bbox, 组员网集合)。"""
    board = view_ctx["board"]
    net_pads = {}
    for p in board["pads"]:
        if p["net"]:
            net_pads.setdefault(p["ref"], set()).add(p["net"])
    regions = []
    for g in ext.get("keepout_groups") or []:
        refs = [r for r in g["refs"] if r in board["footprints"]]
        if not refs:
            continue
        boxes = [board["footprints"][r]["bbox"] for r in refs]
        bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes))
        m = g["keepout_mm"]
        infl = (bbox[0] - m, bbox[1] - m, bbox[2] + m, bbox[3] + m)
        member_nets = set()
        for r in refs:
            member_nets |= net_pads.get(r, set())
        regions.append({"refs": sorted(refs), "bbox": infl,
                        "member_nets": member_nets, "control_id":
                            g["control_id"]})
    return regions


def _channel_keepout_hit(regions, pad, rects):
    """通道段矩形与 keepout 区域相交即罚（组员 ref/共享非 GND 网豁免，FF4-D1）。"""
    for reg in regions:
        if pad["ref"] in reg["refs"]:
            continue
        if pad["net"] and pad["net"] != "GND" and pad["net"] in reg[
                "member_nets"]:
            continue
        for r in rects:
            if not (r[2] < reg["bbox"][0] or r[0] > reg["bbox"][2]
                    or r[3] < reg["bbox"][1] or r[1] > reg["bbox"][3]):
                return reg["control_id"]
    return None


# ---- 匝道求解 ---------------------------------------------------------------
def solve_ramp(view_ctx, ext):
    """逐 ref：transit 网 →（pad,side）净空通道 MCMF。返回 (rows, field_rows,
    solver_runs)。三态：SAT（全匹配）/ UNSAT（证书）/ UNKNOWN（registry 缺档）。
    registry 缺档的 transit 网不进流（缺 basis→UNKNOWN 登记），不静默丢弃。"""
    view = view_ctx["view"]
    board = view_ctx["board"]
    esc = view_ctx["esc"]
    name_of = {n["net_id"]: n["net_name"] for n in view["nets"]}
    id_of_name = {n["net_name"]: n["net_id"] for n in view["nets"]}
    bus_of = {n["net_id"]: n["bus_id"] for n in view["nets"]}
    seed_sides = view_ctx["seed_sides"]
    reserved_fields = {r["field"]: r for r in
                       (ext.get("escape_reserved_fields") or [])}
    regions = _keepout_regions(view_ctx, ext)
    channel_clear = _channel_geom(board)

    # ref → transit 网名（含 registry 缺档者；仅计有逃逸需求者）
    ref_names = {}
    for key, f in esc["fields"].items():
        if f["transit_nets"]:
            ref_names.setdefault(f["ref"], set()).update(f["transit_nets"])

    rows, field_rows, runs = [], [], []
    for ref in sorted(ref_names):
        all_names = sorted(ref_names[ref])
        unmapped_names = [x for x in all_names if x not in id_of_name]
        net_ids = sorted(id_of_name[x] for x in all_names
                         if x in id_of_name)
        pads_at = [p for p in board["pads"] if p["ref"] == ref]
        pad_by_net = {}
        for p in pads_at:
            if p["net"]:
                pad_by_net.setdefault(p["net"], []).append(p)

        # 通道清单（净空者）
        channels = []
        for nid in net_ids:
            for p in pad_by_net.get(name_of[nid], []):
                for side in sorted(set(p["side"]), key=SIDE_ORDER.index):
                    clear, path = channel_clear(p, side)
                    if not clear:
                        continue
                    rects = _channel_rects(p, side)
                    ko = _channel_keepout_hit(regions, p, rects)
                    cost = (route_view.RAMP_COST_STRAIGHT if path == "straight"
                            else route_view.RAMP_COST_DOGLEG)
                    sd = seed_sides.get(bus_of.get(nid, ""), {}).get(ref)
                    if sd and side != sd:
                        cost += route_view.RAMP_COST_SIDE_MISMATCH
                    channels.append({"net_id": nid, "pad": p["num"],
                                     "side": side, "path": path,
                                     "cost": cost, "keepout": ko})

        # ④ 控制升级（consumer-gate-4；fc3-D1）：M dominating 全部正常费用
        # （每边 ≤ DOGLEG+SIDE_MISMATCH、匹配边 ≤ len(channels)），MCMF 总费
        # = M×控制违例数 + 正常费 → 先最小化违例、再正常费（lex）。
        m_factor = 0
        if regions:
            m_factor = (len(channels)
                        * (route_view.RAMP_COST_DOGLEG
                           + route_view.RAMP_COST_SIDE_MISMATCH) + 1)

        # 槽位：每侧净空通道按沿轴坐标排序（slot=该侧第几道）
        slot_of = {}
        pad_xy = {p["num"]: (p["x"], p["y"]) for p in pads_at}
        for side in SIDE_ORDER:
            grp = [c for c in channels if c["side"] == side]
            grp.sort(key=lambda c: ((pad_xy[c["pad"]][0] if side in "NS"
                                     else pad_xy[c["pad"]][1]), c["pad"]))
            for i, c in enumerate(grp):
                slot_of[(c["net_id"], c["pad"], c["side"])] = i

        row = {
            "ref": ref, "demand_transit_nets": len(all_names),
            "demand_registered": len(net_ids),
            "unmapped_transit_nets": unmapped_names,
            "assignments": [], "unmatched": [],
            "reserved_control_ids": sorted(
                r["control_id"] for k, r in reserved_fields.items()
                if k.split("|")[0] == ref),
        }
        if not net_ids:
            # 全部缺档 → UNKNOWN（missing_basis），不虚构求解结果
            row.update({"solver_status": "UNKNOWN", "flow": None,
                        "run_id": None,
                        "reason": "missing_basis:net_not_in_registry"})
            rows.append(row)
            continue

        names = (["SRC"] + ["net:%s" % nid for nid in net_ids]
                 + ["ch:%s.%s:%s" % (ref, c["pad"], c["side"])
                    for c in channels] + ["SNK"])
        idx = {nm: i for i, nm in enumerate(names)}
        nid_idx = {nid: 1 + i for i, nid in enumerate(net_ids)}
        k = len(net_ids)
        mcmf = flow.MinCostFlow(len(names))
        for i in range(k):
            mcmf.add_edge(0, 1 + i, 1, 0)
        # 网到通道边按 (cost, pad, side) 稳定序插入（确定性 tie-break）；
        # keepout 命中边叠加 M 系数（lex 首位=控制违例数；物理可行性不变）
        edge_ref = {}
        for j in sorted(range(len(channels)),
                        key=lambda x: (channels[x]["cost"]
                                       + (m_factor if channels[x]["keepout"]
                                          else 0),
                                       channels[x]["pad"],
                                       SIDE_ORDER.index(
                                           channels[x]["side"]))):
            c = channels[j]
            e = mcmf.add_edge(nid_idx[c["net_id"]], 1 + k + j, 1,
                              c["cost"] + (m_factor if c["keepout"] else 0))
            edge_ref[j] = e
        for j in range(len(channels)):
            mcmf.add_edge(1 + k + j, len(names) - 1, 1, 0)
        demand = len(net_ids)
        fvalue, fcost = mcmf.solve(0, len(names) - 1)
        matched = [j for j, e in edge_ref.items() if mcmf.residual_of(e) == 0]

        status = "SAT" if fvalue == demand else "UNSAT"
        viol = (fcost // m_factor) if m_factor else 0
        normal_cost = fcost - viol * m_factor
        run = {"run_id": "RAMP-%s" % ref, "kind": "ramp", "scope":
               {"ref": ref}, "solver": "min_cost_max_flow",
               "status": status, "flow": fvalue, "demand": demand,
               "cost": normal_cost,
               "keepout_control_violations": viol,
               "control_violation_cost": viol * m_factor,
               "channels_clear": len(channels),
               "keepout_penalized": sum(1 for c in channels if c["keepout"])}
        if status == "UNSAT":
            cert = flow.min_cut_certificate(
                mcmf, 0, len(names) - 1, fvalue, names)
            run["certificate"] = cert
            assert cert["verified"], cert
        runs.append(run)

        for j in sorted(matched, key=lambda x: (channels[x]["net_id"],
                                                channels[x]["pad"],
                                                SIDE_ORDER.index(
                                                    channels[x]["side"]))):
            c = channels[j]
            row["assignments"].append({
                "net_id": c["net_id"], "net_name": name_of[c["net_id"]],
                "ref": ref, "pad": c["pad"], "side": c["side"],
                "slot": slot_of[(c["net_id"], c["pad"], c["side"])],
                "path": c["path"], "cost": c["cost"],
                "keepout_control": c["keepout"]})
        matched_nets = {channels[j]["net_id"] for j in matched}
        row["unmatched"] = [
            {"net_id": nid, "net_name": name_of[nid], "ref": ref,
             "reason": "no_clear_channel(min_cut_certified)"
             if status == "UNSAT" else "unmatched"}
            for nid in net_ids if nid not in matched_nets]
        row.update({"solver_status": status, "flow": fvalue,
                    "run_id": run["run_id"]})
        rows.append(row)

    # 场级对账（ref|side）：escaped ≤ 该侧净空通道数（对全字段断言）
    esc_by_key = {}
    for r in rows:
        for a in r["assignments"]:
            key = r["ref"] + "|" + a["side"]
            esc_by_key[key] = esc_by_key.get(key, 0) + 1
    demand_keys = set()
    for f in view["escape_fields"]:
        used = esc_by_key.get(f["field"], 0)
        demand_keys.add(f["field"])
        field_rows.append({
            "field": f["field"], "ref": f["ref"], "side": f["side"],
            "escaped": used,
            "supply_clear_channels": f["supply_clear_channels"],
            "demand_transit_nets": f["demand_transit_nets"],
            "c2_blocked_transit_nets": f["blocked_transit_nets"],
            "margin_channels": f["supply_clear_channels"] - used,
            "reserved": f["field"] in reserved_fields,
        })
    for key, f in esc["fields"].items():
        assert esc_by_key.get(key, 0) <= f["supply_clear_channels"], key
    return rows, field_rows, runs


def _channel_rects(pad, side):
    """通道段矩形（keepout 相交判定用；与 channel_clear 同几何）。"""
    half = config.AUDIT_CHANNEL_HALF_MM
    depth = config.AUDIT_ESCAPE_DEPTH_MM
    cx, cy = pad["x"], pad["y"]
    ux, uy = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (1.0, 0.0),
              "W": (-1.0, 0.0)}[side]
    half_d = depth / 2

    def seg_rect(x0, y0, x1, y1):
        return (min(x0, x1) - half, min(y0, y1) - half,
                max(x0, x1) + half, max(y0, y1) + half)

    out = [seg_rect(cx, cy, cx + ux * depth, cy + uy * depth)]
    for sign in (1.0, -1.0):
        jx, jy = -uy * sign, ux * sign
        mx, my = cx + ux * half_d, cy + uy * half_d
        ex, ey = mx + jx * half_d, my + jy * half_d
        out.extend([seg_rect(cx, cy, mx, my), seg_rect(mx, my, ex, ey)])
    return out


# ---- 车道求解 ---------------------------------------------------------------
def _layer_rank_of(view_ctx):
    st = view_ctx["structures"]
    ranks = (st.get("priorities", {}).get("layer_preference", {})
             .get("ranks")) or []
    return [r.split("=")[0].strip() for r in ranks
            if isinstance(r, str) and r.split("=")[0].strip()]


def _bus_allowed_layers(view):
    """总线允许层=成员网 allowed_layers 交集（任一成员未解析→跳过该成员）。"""
    bus_layers = {}
    for n in view["nets"]:
        if not n["bus_id"]:
            continue
        cur = bus_layers.setdefault(n["bus_id"], None)
        if n["allowed_layers"]:
            s = set(n["allowed_layers"]) & set(view["signal_layers"])
            bus_layers[n["bus_id"]] = s if cur is None else (cur & s)
    return bus_layers


def solve_lanes(view_ctx, ext):
    """逐走廊组：bus→(layer,lane) 直接指派 MCMF。返回 (rows, runs)。"""
    view = view_ctx["view"]
    groups = {}
    for c in view["corridors"]:
        groups.setdefault(c["corridor"], []).append(c)
    allowed = _bus_allowed_layers(view)
    ranks = _layer_rank_of(view_ctx)
    pref = ext.get("preferred_layers") or {}
    order_ctrl = (ext.get("route_order") or {}).get("order")
    reserved = {r["bus"]: r for r in (ext.get("reserve_lane") or [])}

    def order_key(bus_id):
        if order_ctrl:
            return (order_ctrl.index(bus_id) if bus_id in order_ctrl
                    else len(order_ctrl), bus_id)
        rank = next((b["route_order_rank"] for b in view["buses"]
                     if b["bus_id"] == bus_id), 999)
        return (rank, bus_id)

    def trunk_seq(bus_id):
        """干道层优先序：控制偏好 > registry preferred > structures ranks >
        config 层序；全部限定 allowed∩signal 硬权限内（FF4-D3）。"""
        av = allowed.get(bus_id) or set()
        seq = []
        if bus_id in pref and pref[bus_id] in av:
            seq.append(pref[bus_id])
        for src in ([next((n["preferred_layer"] for n in view["nets"]
                           if n["bus_id"] == bus_id
                           and n["preferred_layer"] in av), None)] +
                    [l for l in ranks if l in av] +
                    [l for l in view["signal_layers"] if l in av]):
            if src and src not in seq:
                seq.append(src)
        return seq, sorted(av, key=lambda x: (view["signal_layers"].index(x),))

    rows, runs = [], []
    for corridor in sorted(groups):
        rows_c = sorted(groups[corridor], key=lambda x: x["bus_id"])
        gap = rows_c[0]["gap_mm"]
        usable = gap - LANE_MARGIN_MM
        pool_supply = {layer: max(0, int(math.floor(
            usable / view["lane_pitch_mm"] + 1e-9)))
            for layer in view["signal_layers"]}
        buses = [c["bus_id"] for c in rows_c]
        bus_seq = {b: trunk_seq(b) for b in buses}
        demand_of = {c["bus_id"]: int(math.ceil(c["member_count"] / 2))
                     for c in rows_c}
        # 预留（本计划无 reserve_lane 条目；机制在位：池容量预扣）
        reserve_note = {}
        for b in buses:
            if b in reserved:
                rv = reserved[b].get("action", {}).get("reserve_lanes")
                if isinstance(rv, int) and rv > 0:
                    for layer in pool_supply:
                        pool_supply[layer] = max(0, pool_supply[layer] - rv)
                    reserve_note[b] = rv

        names = ["SRC"]
        for b in sorted(buses):
            names.append("bus:%s" % b)
        for layer in view["signal_layers"]:
            for i in range(pool_supply[layer]):
                names.append("lane:%s:%s:%d" % (corridor, layer, i))
        names.append("SNK")
        idx = {nm: i for i, nm in enumerate(names)}
        mcmf = flow.MinCostFlow(len(names))
        src_edges = {}
        for b in sorted(buses):
            src_edges[b] = mcmf.add_edge(idx["SRC"], idx["bus:%s" % b],
                                         demand_of[b], 0)
        lane_edges = []
        for b in sorted(buses, key=order_key):
            seq, av_sorted = bus_seq[b]
            for layer in av_sorted:
                cost = 0 if layer == (seq[0] if seq else None) else \
                    route_view.LANE_COST_OTHER_LAYER
                for i in range(pool_supply[layer]):
                    e = mcmf.add_edge(idx["bus:%s" % b],
                                      idx["lane:%s:%s:%d"
                                          % (corridor, layer, i)], 1, cost)
                    lane_edges.append((b, layer, i, e))
        for layer in view["signal_layers"]:
            for i in range(pool_supply[layer]):
                mcmf.add_edge(idx["lane:%s:%s:%d" % (corridor, layer, i)],
                              idx["SNK"], 1, 0)
        demand = sum(demand_of.values())
        fvalue, fcost = mcmf.solve(idx["SRC"], idx["SNK"])
        status = "SAT" if fvalue == demand else "UNSAT"
        run = {"run_id": "LANE-%s" % corridor, "kind": "lane", "scope":
               {"corridor": corridor, "buses": sorted(buses)},
               "solver": "min_cost_max_flow", "status": status,
               "flow": fvalue, "demand": demand, "cost": fcost,
               "pool_supply": {k: v for k, v in sorted(pool_supply.items())
                               if v >= 0}, "reserved_lanes": reserve_note}
        if status == "UNSAT":
            cert = flow.min_cut_certificate(mcmf, idx["SRC"], idx["SNK"],
                                            fvalue, names)
            run["certificate"] = cert
            assert cert["verified"], cert
        runs.append(run)

        assign = []
        taken = {}
        for (b, layer, i, e) in lane_edges:
            if mcmf.residual_of(e) == 0:
                assign.append({"bus_id": b, "layer": layer, "lane": i})
                taken.setdefault((b, layer), []).append(i)
        bus_rows = []
        for b in sorted(buses):
            seq, av_sorted = bus_seq[b]
            per_layer = []
            for layer in sorted({l for (bb, l) in taken if bb == b},
                                key=lambda x: av_sorted.index(x)
                                if x in av_sorted else 99):
                lanes_l = sorted(taken[(b, layer)])
                gaps = any(lanes_l[i + 1] != lanes_l[i] + 1
                           for i in range(len(lanes_l) - 1))
                per_layer.append({
                    "layer": layer, "lanes": lanes_l,
                    "count": len(lanes_l), "contiguous": not gaps,
                    "trunk_preferred": layer == (seq[0] if seq else None)})
            bus_rows.append({
                "bus_id": b, "demand_lanes": demand_of[b],
                "assigned": sum(p["count"] for p in per_layer),
                "trunk_seq": seq, "allowed_layers": av_sorted,
                "per_layer": per_layer,
                "status": "assigned" if any(per_layer) else
                          ("deficit" if status == "UNSAT" else "unassigned"),
            })
        rows.append({
            "corridor": corridor, "buses": sorted(buses),
            "gap_mm": gap, "usable_mm": round(usable, 3),
            "pitch_mm": view["lane_pitch_mm"],
            "demand_lanes": demand, "flow": fvalue,
            "solver_status": status, "run_id": run["run_id"],
            "pool_supply": run["pool_supply"], "bus_rows": bus_rows,
        })
    return rows, runs


# ---- 产物组装 ---------------------------------------------------------------
def _via_accounting(view_ctx, lane_rows, plan):
    view = view_ctx["view"]
    trunk_of = {}
    for row in lane_rows:
        for b in row["bus_rows"]:
            trunk = next((p["layer"] for p in b["per_layer"]
                          if p["trunk_preferred"]),
                         b["trunk_seq"][0] if b["trunk_seq"] else None)
            trunk_of[b["bus_id"]] = trunk
    member_count = {b["bus_id"]: b["member_count"] for b in view["buses"]}
    per_bus, total = [], 0
    policy_conflicts = []
    for bus_id in sorted(trunk_of):
        trunk = trunk_of[bus_id]
        vias = 0 if trunk in (None, "F.Cu") else 2 * member_count[bus_id]
        total += vias
        per_bus.append({"bus_id": bus_id, "trunk_layer": trunk,
                        "member_count": member_count[bus_id],
                        "planned_vias": vias})
    nets_of_bus = {}
    for n in view["nets"]:
        if n["bus_id"]:
            nets_of_bus.setdefault(n["bus_id"], []).append(n)
    for n in [x for b in sorted(nets_of_bus) for x in nets_of_bus[b]]:
        vp = n.get("via_policy") or {}
        if vp.get("policy") == "max_count" and vp.get("max_count") is not None \
                and trunk_of.get(n["bus_id"]) not in (None, "F.Cu") \
                and 2 > vp["max_count"]:
            policy_conflicts.append({"net_id": n["net_id"],
                                     "net_name": n["net_name"],
                                     "via_policy_max": vp["max_count"],
                                     "planned": 2})
    vb = None
    if plan:
        for r in plan.get("resources") or []:
            if r.get("resource_id") == "via_budget:board":
                vb = {"state": r.get("state"),
                      "supply": (r.get("supply") or {}).get("value"),
                      "demand": total,
                      "margin": ((r.get("margin") or {}).get("value")
                                 if r.get("margin") else None)}
    if vb is None:
        vb = {"state": "missing_basis", "supply": None, "demand": total,
              "margin": None, "note": "未绑计划；FF-1 账本 via_budget="
                                      "missing_basis（fab 能力表缺源，待人工 #4）"}
    return {"per_bus": per_bus, "planned_vias_total": total,
            "via_budget": vb, "via_policy_conflicts":
                sorted(policy_conflicts, key=lambda x: x["net_id"]),
            "note": "干道层往返 F→trunk→F=2 vias/网（derived 一阶口径）；"
                    "供给 missing_basis→UNKNOWN，不编造 green"}


def build_products(out_dir_rel=config.load_project_manifest().out_dirs["route"],
                   ff_plan_path=None,
                   placement_layout_path=None):
    """placement_layout_path（opt-in，IT 会话）：③ 布局提案覆盖板几何做 ④
    dry-run 对照（route_view.placement_override 单列；缺省=None=默认路径
    逐字节不变）。"""
    t0 = datetime.datetime.now(datetime.timezone.utc)
    live_before = hashing.sha256_file(config.REVC_BOARD)
    p3_before = hashing.sha256_file(config.AUDIT_P3_BOARD)
    view_ctx = route_view.build_route_view(
        out_dir_rel, placement_layout_path=placement_layout_path)
    view = view_ctx["view"]

    binding = None
    plan = None
    plan_sha = None
    cascade = False
    cascade_binding = None
    if ff_plan_path:
        reads = []
        plan, plan_sha = route_view.ff_consume.load_plan(ff_plan_path, reads)
        current, st_basis = route_view.ff_consume.apply_plan_structures_basis(
            plan, view["snapshot"], reads)
        cascade = ((plan.get("snapshot") or {}).get("placement_basis")
                   == "it_adopted_cascade")
        if cascade:
            # CAS1：计划 placement 绑定=采纳快照（§9.4 批准路径）——④ 几何
            # 必须来自同一 it-layout：确定性转换回算 CSV hash 与计划绑定
            # 逐字节核对，匹配才切换绑定的现值；失配/缺覆盖→保持 p3 现值，
            # binding 如实 stale（不静默消费）
            ovr = view_ctx.get("placement_override")
            if ovr is None:
                cascade_binding = {
                    "status": "blocked_no_override",
                    "note": "级联计划需 --placement-from-layout（采纳布局"
                            "几何）；缺失→绑定保持 p3 现值→stale 如实"}
            else:
                from . import coplace_cmd
                with open(ovr["layout_path"], encoding="utf-8") as f:
                    lay_obj = json.load(f)
                adopted_sha = hashing.sha256_bytes(
                    coplace_cmd.to_placement_csv(lay_obj))
                match_layout = (ovr["layout_sha256"]
                                == (plan.get("snapshot") or {}).get(
                                    "adopted_layout_sha256"))
                match_csv = (adopted_sha
                             == (plan.get("snapshot") or {}).get(
                                 "placement_snapshot_sha256"))
                cascade_binding = {
                    "status": ("matched" if (match_layout and match_csv)
                               else "mismatch"),
                    "layout_sha_match": match_layout,
                    "converted_csv_sha_match": match_csv,
                    "converted_csv_sha256": adopted_sha,
                    "note": "§9.4 转换证明闭环：it-layout 经 to_placement_csv "
                            "回算与计划 placement 绑定核对；确认点 #4 已批",
                }
                if match_layout and match_csv:
                    current["placement_snapshot_sha256"] = adopted_sha
                    ovr["mode"] = "it_adoption_cascade"
                    view["mode"] = "it_adoption_cascade"
                ovr["cascade_binding"] = cascade_binding
        binding = route_view.ff_consume.snapshot_binding(
            plan, current, structures_basis=st_basis)
        if binding["all_match"]:
            ext, applied, ignored, conflicts = \
                route_view.interpret_controls_route(plan, view_ctx, reads)
        else:
            # stale/conflict：controls 不应用（不静默消费）；dry-run 以无控制
            # 基线跑，authority 保持 planning_advisory（FF-4 同语义）
            ext, applied, ignored, conflicts = {}, [], [
                {"control_id": c.get("control_id"), "kind": c.get("kind"),
                 "target": c.get("target"),
                 "reason": "stale_plan：snapshot hash 不匹配，controls 不应用"}
                for c in (plan.get("controls") or [])], []
        consumption = _build_consumption(plan, plan_sha, binding, ext,
                                         applied, ignored, conflicts, reads)
    else:
        ext, applied, ignored, conflicts = {}, [], [], []
        consumption = None

    ramp_rows, field_rows, ramp_runs = solve_ramp(view_ctx, ext)
    lane_rows, lane_runs = solve_lanes(view_ctx, ext)
    via = _via_accounting(view_ctx, lane_rows, plan)

    conflicts_out = []
    rollbacks = []
    for r in ramp_rows:
        if r["solver_status"] == "UNSAT":
            nid_list = [u["net_id"] for u in r["unmatched"]]
            conflicts_out.append({
                "resource_id": "escape_slots:%s" % r["ref"], "kind":
                    "escape_slots",
                "blocking_net_ids": nid_list,
                "supply": _field_supply(view, r["ref"]), "demand":
                    r["demand_registered"], "reserve": 0,
                "margin": _field_supply(view, r["ref"])
                - r["demand_registered"],
                "basis": ["audit_cmd.escape_check（C2 同源）", "C-0037"],
                "conflicting_controls": r["reserved_control_ids"],
                "suggested_rollback_stage": 3,
                "certificate_run": r["run_id"]})
            rollbacks.append({
                "resource_id": "escape_slots:%s" % r["ref"],
                "suggested_rollback_stage": 3,
                "action": "③ 布局/骨架重优化（引脚场净空随位姿；锚件不动）"})
    for row in lane_rows:
        if row["solver_status"] == "UNSAT":
            blocked = [b["bus_id"] for b in row["bus_rows"]
                       if b["assigned"] < b["demand_lanes"]]
            conflicts_out.append({
                "resource_id": "bus_lane:%s" % row["corridor"], "kind":
                    "bus_lane",
                "blocking_net_ids": sorted({
                    n["net_id"] for n in view["nets"]
                    if n["bus_id"] in blocked}),
                "supply": sum(row["pool_supply"].values()), "demand":
                    row["demand_lanes"], "reserve": 0,
                "margin": sum(row["pool_supply"].values())
                - row["demand_lanes"],
                "basis": ["C-0053 ceil(N/2)×0.35 离散车道", "audit C4 gap"],
                "conflicting_controls": [], "suggested_rollback_stage": 3,
                "certificate_run": row["run_id"]})
            rollbacks.append({
                "resource_id": "bus_lane:%s" % row["corridor"],
                "suggested_rollback_stage": 3,
                "action": "③ 走廊/层/骨架重优化；架构级不足升 ② 人工"})

    runs = ramp_runs + lane_runs
    certs = [r for r in runs if "certificate" in r]
    solver_summary = {
        "runs_total": len(runs),
        "by_status": {s: sum(1 for r in runs if r["status"] == s)
                      for s in sorted({r["status"] for r in runs})},
        "certificates_verified": sum(1 for c in certs
                                     if c["certificate"]["verified"]),
        "unsat_without_certificate": sum(1 for r in runs
                                         if r["status"] == "UNSAT"
                                         and "certificate" not in r),
        "three_state_note": "SAT=witness 赋值；UNSAT=min-cut 证书；"
                            "缺 basis/依赖缺失=UNKNOWN（§10.3）",
    }

    live_after = hashing.sha256_file(config.REVC_BOARD)
    p3_after = hashing.sha256_file(config.AUDIT_P3_BOARD)
    zero_write = {
        "live_board_sha256": live_before,
        "live_board_sha256_after_build": live_after,
        "p3_board_sha256": p3_before,
        "unchanged": live_before == live_after and p3_before == p3_after,
        "save_board_used": False,
        "live_commit_called": False,
        "mode": "in_memory_dry_run（生成器模式：零落盘、零子进程、零写板）",
    }
    controls_block = {
        "bound": plan is not None,
        "applied": len(applied),
        "ignored": len(ignored),
        "ignored_all_have_reason": all(i.get("reason") for i in ignored),
        "parsed": (None if plan is None else
                   (len(applied) + len(ignored) == len(plan.get("controls")
                                                    or [])
                    and all(i.get("reason") for i in ignored))),
    }

    order_ctrl = ext.get("route_order") or {}
    plan_obj = {
        "schema_version": route_view.ROUTE_SCHEMA,
        "artifact_kind": "route_plan",
        "mode": "fc1_dry_run_planning",
        "authority": "planning_advisory（dry-run 规划面；零写板、零 live commit）",
        "registry_snapshot_hash": view["registry_snapshot_hash"],
        "snapshot": view["snapshot"],
        "plan_binding": {
            "bound": plan is not None,
            "plan_id": (plan or {}).get("plan_id"),
            "feedforward_plan_hash": plan_sha,
            "stale_plan": (binding or {}).get("stale_plan"),
            "stale_plan_reason": (binding or {}).get("stale_plan_reason"),
            "authority_effective":
                ("upgraded_for_candidate_acceptance（consumer-gate-4 已批："
                 "keepout=lex 控制违例；max-flow 物理可行性与三态红线不变）"
                 if (binding or {}).get("all_match") else
                 "planning_advisory（绑定 stale/conflict：控制未应用）")
                if plan is not None else
                "planning_advisory（未绑计划：无控制可消费；④ consumer gate "
                "批准件=out/revc-fd1/approvals/consumer-gate-4.json）",
        },
        "route_order": {
            "control_order": order_ctrl.get("order"),
            "dropped_unknown": order_ctrl.get("dropped_unknown"),
            "effective_order": [b["bus_id"] for b in sorted(
                view["buses"], key=lambda b: (b["route_order_rank"],
                                              b["bus_id"]))],
        },
        "ramps": ramp_rows,
        "ramp_fields_account": field_rows,
        "lanes": lane_rows,
        "via_accounting": via,
        "stitching": (ext.get("stitching") or
                      {"status": "not_bound（未绑计划；控制面未消费）"}),
        "solver_runs": runs,
        "solver_summary": solver_summary,
        "resource_conflicts": conflicts_out,
        "rollback_suggestions": rollbacks,
        "controls_consumed": controls_block,
        "pins": view["pins"],
        "zero_write": zero_write,
        "consumption_artifact": ("route-consumption.json" if consumption
                                 else None),
        "note": "FC1 dry-run 只覆盖 §10.1 步骤 1/2（匝道/车道）；描线与残网"
                "SAT/ILP=FC2（SPEC §15）。route target/失败/冲突一律 "
                "net_id/relation_id（§10.2）",
    }
    if view_ctx.get("placement_override"):
        if cascade and (cascade_binding or {}).get("status") == "matched":
            plan_obj["mode"] = "it_adoption_cascade"
        elif cascade:
            plan_obj["mode"] = "it_adoption_cascade_unverified"
        else:
            plan_obj["mode"] = "keepout_iteration_dry_run"
        plan_obj["placement_override"] = view_ctx["placement_override"]

    products = {}
    consumption_obj = consumption if consumption is not None else {
        "schema_version": route_view.ROUTE_SCHEMA,
        "artifact_kind": "route_consumption",
        "applied": False,
        "note": "未绑计划（--feedforward-plan 缺省）：④ 控制面无计划可消费；"
                "本产物仅在绑定计划时生成（CLI 契约同 ff_consumption）",
    }
    for name, obj in (("route_view", view), ("route_plan", plan_obj),
                      ("consumption", consumption_obj)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data,
                          "sha256": hashing.sha256_bytes(data)}

    env = _build_envelope(view_ctx, plan_obj, products, out_dir_rel,
                          binding, ff_plan_path)
    env_bytes = hashing.canonical_json_bytes(env)
    products["envelope"] = {"obj": env, "bytes": env_bytes,
                            "sha256": hashing.sha256_bytes(env_bytes)}

    report = _build_report_md(view, plan_obj, env)
    products["report"] = {"obj": None,
                          "bytes": report.encode(config.ENCODING),
                          "sha256": hashing.sha256_bytes(
                              report.encode(config.ENCODING))}
    for art in env["artifacts"]:
        if art["path"].endswith("route-report.md"):
            art["sha256"] = products["report"]["sha256"]

    t1 = datetime.datetime.now(datetime.timezone.utc)
    products["run_manifest"] = {"obj": {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "tool_version": config.TOOL_VERSION,
        "command": "route", "out_dir": out_dir_rel,
        "input_sha256": {i["path"]: i["sha256"] for i in env["inputs"]},
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT,
                                                        "SPEC.md")),
        "registry_snapshot_sha256": view["registry_snapshot_hash"],
        "feedforward_plan_sha256": plan_sha,
        "route_impl_sha256": _impl_hashes(),
        "pcbagent_adapter_lock": route_view.pcbagent_adapter_lock(),
        "schema_version": route_view.ROUTE_SCHEMA,
    }}
    return products


def _field_supply(view, ref):
    return sum(f["supply_clear_channels"] for f in view["escape_fields"]
               if f["ref"] == ref)


def _impl_hashes():
    out = {}
    here = os.path.dirname(os.path.abspath(__file__))
    for m in ("route_view.py", "route_cmd.py", "flow.py"):
        with open(os.path.join(here, m), "rb") as f:
            out[m] = hashing.sha256_bytes(f.read())
    return out


def _build_consumption(plan, plan_sha, binding, ext, applied, ignored,
                       conflicts, reads):
    declared = sorted(a["control_id"] for a in applied)
    actually_read = sorted({r["field"].split("]")[0].split("[")[-1]
                            for r in reads
                            if r["field"].startswith("controls[")
                            and not r["field"].startswith("controls[conflict")
                            and r["field"].split("]")[0].split("[")[-1]})
    derived = _derived_rows(ext)
    return {
        "schema_version": route_view.ROUTE_SCHEMA,
        "artifact_kind": "route_consumption",
        "plan_id": plan.get("plan_id"),
        "feedforward_plan_hash": plan_sha,
        "feedforward_registry_snapshot_hash":
            (plan.get("snapshot") or {}).get("registry_snapshot_hash"),
        "plan_authority": plan.get("authority"),
        "consumer_gate": route_view.ROUTE_CONSUMER_GATE,
        "authority_effective": ("upgraded_for_candidate_acceptance"
                                if binding["all_match"] else
                                "planning_advisory（stale/conflict 未应用）"),
        "snapshot_check": binding,
        "stale_plan_reason": binding["stale_plan_reason"],
        "conflict": binding["conflict"],
        "controls_declared_consumed": declared,
        "controls_applied": sorted(applied, key=lambda a: a["control_id"]),
        "controls_actually_read": actually_read,
        "controls_derived": derived,
        "controls_ignored": sorted(ignored, key=lambda i: i["control_id"]),
        "control_conflicts": conflicts,
        "zero_present_kinds": ext.get("zero_present_kinds") or [],
        "application": {
            "reserve_escape_slots": {
                "reserved_fields": [f["field"] for f in
                                    (ext.get("escape_reserved_fields") or [])],
                "effect": "匝道场预留登记：demand 预订；缺额进 "
                          "resource_conflicts（§1.4 归因）"},
            "assign_preferred_layer": {
                "per_bus": dict(sorted((ext.get("preferred_layers") or
                                        {}).items())),
                "notes": ext.get("preferred_layer_notes") or [],
                "effect": "车道干道层偏好（registry allowed_layers 硬权限内）"},
            "protect_keepout": {
                "groups": [{"scope": g["scope"], "refs": g["refs"],
                            "keepout_mm": g["keepout_mm"]}
                           for g in (ext.get("keepout_groups") or [])],
                "effect": "匝道通道 keepout 进入候选接受（lex 首位=控制违例"
                          "数；非禁布，物理可行性/三态不变）"},
            "set_route_order": {
                "order": (ext.get("route_order") or {}).get("order"),
                "effect": "总线处理序（车道分配插边序；确定性）"},
            "reserve_return_stitching": ext.get("stitching"),
            "reserve_via_budget": ext.get("via_budget_reserve") or [],
            "reserve_lane": ext.get("reserve_lane") or [],
        },
        "consumption_contract": {
            "actually_read": reads,
            "derived": [d["derived"] for d in derived],
            "ignored": [i["control_id"] for i in ignored],
            "fallback": None,
            "fidelity": "full（④ 一阶模型：场级通道匹配/离散车道池；"
                        "⑥ DRC=精确权威；actually_read=真实字段访问点）",
        },
        "note": "§10.2 消费证据；controls 升级依据=out/revc-fd1/approvals/"
                "consumer-gate-4.json（NEXT.md 待人工 #7 已批）；分列不混淆"
                "（§16.2-14）：declared∪ignored=actually_read、"
                "declared∩ignored=∅",
    }


def _derived_rows(ext):
    rows = []
    for f in ext.get("escape_reserved_fields") or []:
        rows.append({"target": "field:" + f["field"],
                     "derived": "匝道预留=demand 预订（C2 口径）；缺额归因"
                                " min-cut 证书"})
    for bus, layer in sorted((ext.get("preferred_layers") or {}).items()):
        rows.append({"target": "bus:" + bus,
                     "derived": "车道干道层偏好 → %s（allowed 硬权限内）"
                                % layer})
    for g in ext.get("keepout_groups") or []:
        rows.append({"target": g["scope"],
                     "derived": "keepout=refs bbox 外扩 %gmm；通道命中=控制"
                                "违例（lex M 系数前置，违例数逐 run 单列）"
                                % g["keepout_mm"]})
    if ext.get("route_order"):
        rows.append({"target": "board:revc",
                     "derived": "route_order=总线插边序（确定性 tie-break）"})
    if ext.get("stitching"):
        rows.append({"target": "board:revc",
                     "derived": "缝合预留登记（无求解；供给 missing_basis）"})
    return sorted(rows, key=lambda r: r["target"])


def _build_envelope(view_ctx, plan_obj, products, out_dir_rel, binding,
                    ff_plan_path):
    """⑥ 路由 envelope 装配（SPEC v1.3 §16.4）：五轴 gate + ramp/视图绑定。

    gate 五轴=route_view 注册绑定/controls 解析消费/资源冲突归属可证/
    solver 三态（unsat_without_certificate==0）/板 hash 零写（另加
    no_live_commit 声明）；binding 在场时叠 controls 消费门。ramp 命中
    统计与视图产物登记随后装配；产物 bytes/sha 由 products 侧带入。
    """
    view = view_ctx["view"]
    runs = plan_obj["solver_runs"]
    run_by_id = {r["run_id"]: r for r in runs}
    gate = {
        "route_view_registry_bound": True,
        "controls_parsed": plan_obj["controls_consumed"]["parsed"],
        "resource_conflicts_attributed": all(
            c["certificate_run"] in run_by_id
            and run_by_id[c["certificate_run"]].get("certificate", {})
            .get("verified") and c["blocking_net_ids"]
            for c in plan_obj["resource_conflicts"]),
        "solver_three_state": plan_obj["solver_summary"][
            "unsat_without_certificate"] == 0,
        "board_hash_unchanged": plan_obj["zero_write"]["unchanged"],
        "no_live_commit_or_save_board": True,
        "spec_ref": "SPEC v1.3 §16.4",
    }
    if binding is not None:
        gate["controls_consumer_gate_approved"] = \
            route_view.ROUTE_CONSUMER_GATE["approved"]
    ramp_sat = sum(1 for r in plan_obj["ramps"]
                   if r["solver_status"] == "SAT")
    ramp_unsat = sum(1 for r in plan_obj["ramps"]
                     if r["solver_status"] == "UNSAT")
    ramp_unknown = sum(1 for r in plan_obj["ramps"]
                       if r["solver_status"] == "UNKNOWN")
    lane_sat = sum(1 for r in plan_obj["lanes"]
                   if r["solver_status"] == "SAT")
    lane_unsat = sum(1 for r in plan_obj["lanes"]
                     if r["solver_status"] == "UNSAT")
    metrics = {
        "mode": plan_obj["mode"],
        "nets_total": len(view["nets"]),
        "buses_total": len(view["buses"]),
        "escape_fields_with_demand": view["escape_fields_with_demand"],
        "board_only_nets": len(view["board_only_nets"]),
        "unmapped_transit_nets": len(view["unmapped_transit_nets"]),
        "ramp_refs_total": len(plan_obj["ramps"]),
        "ramp_refs_sat": ramp_sat,
        "ramp_refs_unsat": ramp_unsat,
        "ramp_refs_unknown": ramp_unknown,
        "ramp_nets_unmatched": sum(len(r["unmatched"])
                                   for r in plan_obj["ramps"]),
        "lane_corridors_total": len(plan_obj["lanes"]),
        "lane_corridors_sat": lane_sat,
        "lane_corridors_unsat": lane_unsat,
        "planned_vias_total": plan_obj["via_accounting"][
            "planned_vias_total"],
        "via_budget_state": plan_obj["via_accounting"]["via_budget"][
            "state"],
        "resource_conflicts": len(plan_obj["resource_conflicts"]),
        "solver_runs": plan_obj["solver_summary"]["runs_total"],
        "controls_applied": plan_obj["controls_consumed"]["applied"],
        "controls_ignored": plan_obj["controls_consumed"]["ignored"],
        "board_write": False,
    }
    if binding is not None:
        metrics["keepout_control_violations"] = sum(
            r["keepout_control_violations"] for r in plan_obj["solver_runs"]
            if r["kind"] == "ramp")
    inputs = [
        {"path": "out/revc-a3/net-registry.json",
         "sha256": view["snapshot"]["registry_snapshot_hash"],
         "role": "registry"},
        {"path": "out/revc-a3/structures.json",
         "sha256": view["snapshot"]["structures_sha256"],
         "role": "structures"},
        {"path": "out/revc-a3/constraints.json",
         "sha256": view["snapshot"]["constraints_sha256"],
         "role": "constraints"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": view["snapshot"]["board_snapshot_sha256"], "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/placement.csv",
         "sha256": view["snapshot"]["placement_snapshot_sha256"],
         "role": "placement"},
    ]
    if ff_plan_path:
        inputs.append({"path": ff_plan_path.replace("\\", "/"),
                       "sha256": plan_obj["plan_binding"]
                       ["feedforward_plan_hash"], "role":
                       "feedforward_plan"})
    if view_ctx.get("placement_override"):
        inputs.append({"path": view_ctx["placement_override"]["layout_path"],
                       "sha256": view_ctx["placement_override"]
                       ["layout_sha256"], "role": "placement_override"})
    inputs.append({"path": "out/revc-b1/layout.json",
                   "sha256": view["pins"]["fc2_replay_target"]["sha256"],
                   "role": "fc2_replay_target_pin"})
    inputs.append({"path": view["pins"]["live_board_zero_write_witness"]
                   ["path"],
                   "sha256": view["pins"]["live_board_zero_write_witness"]
                   ["sha256"], "role": "zero_write_witness"})
    artifacts = [
        {"path": out_dir_rel + "/route-view.json",
         "sha256": products["route_view"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/route-plan.json",
         "sha256": products["route_plan"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/route-consumption.json",
         "sha256": products["consumption"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/route-report.md", "role": "human_report"},
    ]
    status = "ok"
    if binding is not None and not binding["all_match"]:
        status = "blocked"
    gate_ok = (gate["solver_three_state"] and gate["board_hash_unchanged"]
               and gate["no_live_commit_or_save_board"]
               and gate["route_view_registry_bound"]
               and gate["resource_conflicts_attributed"])
    env = {
        "schema_version": route_view.ROUTE_SCHEMA,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "command": "route", "command_kind": "core",
        "status": status,
        "verdict": "pass" if (gate_ok and status == "ok") else
                   ("yellow" if gate_ok else "fail"),
        "deterministic": True, "determinism_claim": "byte_exact",
        "inputs": inputs, "config_sha256": None,
        "spec_refs": ["tools/pcbflow/SPEC.md#§10", "tools/pcbflow/SPEC.md#§15-FC1",
                      "tools/pcbflow/SPEC.md#§16.4"],
        "artifacts": artifacts,
        "metrics": metrics,
        "diagnostics": [
            {"id": "fc1_planning_advisory",
             "title": "④ dry-run=规划面：匝道 UNSAT（带 min-cut 证书）与 "
                      "FF-1 账本赤字同源，red≠架构致命（§8.5/§10.3）"},
            {"id": "fc2_scope_note",
             "title": "描线/残网 SAT/ILP=FC2；本产物未实现 §10.1 步骤 3/4，"
                      "如实 specified（§10.5）"},
            {"id": "pcbagent_reuse_note",
             "title": "pcbagent Grid/Region/Legality/DRC adapter 已锁内容 "
                      "hash（run_manifest）；FC1 核心路径零依赖——匝道/车道"
                      "=精确组合流，网格启发式复用留 FC2 描线"},
        ] + ([] if binding is None else
             [{"id": "fc3_controls_upgraded",
               "title": "④ 控制升级生效（consumer-gate-4）：keepout=lex 控制"
                        "违例（M 系数前置）；max-flow 物理可行性与 SAT/UNSAT "
                        "三态不变；违例≠物理不可布；锚件/硬门阈值/历史 B 门"
                        "不追改"}])
        + (([{"id": "cas1_it_adoption",
              "title": "CAS1 级联收口 ④ 重发（it_adoption_cascade）：计划绑定"
                       "=采纳快照（FF-REVC-0004），it-layout 几何经转换证明"
                       "闭环核对（cascade_binding）；moved refs=%d；零写板、"
                       "live 板仅作 hash 见证"
              % view_ctx["placement_override"]["moved_count"]}]
            if plan_obj["mode"] == "it_adoption_cascade" else
            [{"id": "cas1_binding_unverified",
              "title": "级联计划几何未核实（cascade_binding 失配/缺失）：绑定"
                       "保持 p3 现值→stale 如实，控制不应用"}
             ] if plan_obj["mode"] == "it_adoption_cascade_unverified" else
            [{"id": "it_placement_override",
              "title": "IT 布局覆盖 dry-run（--placement-from-layout）：moved "
                       "refs=%d；计划绑定仍对 p3 基线快照（覆盖变量单列 "
                       "placement_override）；零写板、live 板仅作 hash 见证"
              % view_ctx["placement_override"]["moved_count"]}]
            if view_ctx.get("placement_override") else [])),
        "waivers": [],
        "solver": {
            "runs_total": plan_obj["solver_summary"]["runs_total"],
            "by_status": plan_obj["solver_summary"]["by_status"],
            "certificates_verified":
                plan_obj["solver_summary"]["certificates_verified"],
        },
        "run_metadata": {},
        "data": {"gate": gate, "zero_write": plan_obj["zero_write"],
                 "pins": view["pins"]},
    }
    return env


def _build_report_md(view, plan_obj, env):
    m = env["metrics"]
    bound_upgraded = plan_obj["plan_binding"]["bound"] and \
        plan_obj["plan_binding"]["stale_plan"] is False
    auth_line = ("- mode：%s；authority=upgraded_for_candidate_acceptance"
                 "（consumer-gate-4 已批；keepout=lex 控制违例；零写板）"
                 % m["mode"] if bound_upgraded else
                 "- mode：%s；authority=planning_advisory（零写板）"
                 % m["mode"])
    lines = [
        "# PCBFlow ④ route dry-run 报告（FC1/FC3）", "",
        auth_line,
        "- registry snapshot：`%s…`（route view 绑定，§10.2）"
        % view["registry_snapshot_hash"][:16],
        "- 网数 %d（excluded %d 列账于 registry）；板独有网 %d（missing_basis "
        "列账）；registry 缺档 transit 网 %d"
        % (m["nets_total"], view["excluded_nets_count"],
           m["board_only_nets"], m["unmapped_transit_nets"]),
        "",
        "## 匝道（§10.1 步骤 1：引脚场 MCMF）", "",
        "- refs 有逃逸需求 %d：SAT %d / UNSAT %d（UNSAT 均带 min-cut 证书）；"
        "未匹配网 %d" % (m["ramp_refs_total"], m["ramp_refs_sat"],
                         m["ramp_refs_unsat"], m["ramp_nets_unmatched"]),
    ]
    if bound_upgraded:
        lines.append("  - keepout 控制违例（lex 首位，非禁布）：%d"
                     % m.get("keepout_control_violations", 0))
    for r in plan_obj["ramps"]:
        if r["solver_status"] == "UNSAT":
            lines.append("  - `%s`：demand %d，flow %d；未匹配 %s（证书 %s）"
                         % (r["ref"], r["demand_transit_nets"], r["flow"],
                            ", ".join(u["net_name"] for u in r["unmatched"]),
                            r["run_id"]))
    lines += ["", "## 车道（§10.1 步骤 2：走廊离散车道池）", ""]
    for row in plan_obj["lanes"]:
        parts = ["%s=%d/%s道" % (b["bus_id"], b["assigned"],
                                 b["demand_lanes"])
                 for b in row["bus_rows"]]
        lines.append("- `%s`：gap %.3f→池 %s；SAT=%s；%s"
                     % (row["corridor"], row["gap_mm"],
                        row["pool_supply"], row["solver_status"],
                        "，".join(parts)))
    lines += [
        "",
        "## 过孔/缝合/顺序",
        "",
        "- 计划过孔合计 %d（F→trunk→F 口径）；via_budget=%s"
        % (m["planned_vias_total"], m["via_budget_state"]),
        "- 缝合预留：%s" % (plan_obj["stitching"] or {}),
        "- route order（控制）：%s" % plan_obj["route_order"]["control_order"],
        "",
        "## 零写证据与 FC2 钉死",
        "",
        "- live 板 sha256（见证）：%s…" % plan_obj["zero_write"][
            "live_board_sha256"][:16],
        "- FC2 重放靶：`out/revc-b1/layout.json`（NEXT #5 已批）",
        "- 快照副本协议：%s" % view["pins"]["snapshot_copy_protocol"],
        "",
        "人读视图非事实源；核心产物见 route-view/route-plan/"
        "route-consumption.json。",
    ]
    return "\n".join(lines) + "\n"
