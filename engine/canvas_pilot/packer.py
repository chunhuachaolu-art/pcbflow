# -*- coding: utf-8 -*-
"""packer —— 每轮盲包: SVG（载体先例=E0 SVG）+ JSON 机器事实。

**禁项**（任务书 §4.5）: 引擎基线几何、门值（判据/预算上限）、预算余量、
oracle——facts 与 SVG 的 data-* 机器事实域白名单化（leak_check 强制）,
打包器输出抽样核对注记先例。

模型可见信息=画板数字反馈: lattice、锚、每网连通态、已落铜形状表、上轮
拒收原因码、剩余未连通数、当前轮序号（无总上限=不构成预算泄漏）。
"""
from . import instantiate as inst
from . import verify as _verify

# facts 键白名单（机器事实域; 出白名单的键=泄漏嫌疑 fail-closed）
FACTS_TOP_KEYS = {"canvas_version", "round", "board_id", "lattice", "layer_ids",
                  "width_mm", "via_radius_mm", "nets", "shapes", "vias",
                  "last_rejections", "unrouted_nets", "note"}

NET_COLORS = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
              "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080",
              "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000"]


def net_color(net_id, net_order):
    idx = net_order.index(net_id) if net_id in net_order else 0
    return NET_COLORS[idx % len(NET_COLORS)]


def pack_svg(state, round_no, last_rejections):
    """画板 SVG（viewBox=workspace mm; 图元带 data-* 机器事实）。"""
    ws = state.board["workspace"]
    lat = state.lattice
    w = ws["x_max"] - ws["x_min"]
    h = ws["y_max"] - ws["y_min"]
    net_order = [n["net_id"] for n in state.board["nets"]]
    holes = state.board.get("holes") or []
    parts = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.4f %.4f %.4f %.4f" '
        'font-family="monospace">' % (ws["x_min"], ws["y_min"], w, h))
    parts.append('<rect x="%.4f" y="%.4f" width="%.4f" height="%.4f" '
                 'fill="#111318" data-role="board-outline" '
                 'data-x-min="%.4f" data-y-min="%.4f" data-x-max="%.4f" '
                 'data-y-max="%.4f"/>' % (ws["x_min"], ws["y_min"], w, h,
                                          ws["x_min"], ws["y_min"],
                                          ws["x_max"], ws["y_max"]))
    # 板边禁布带（0.2mm, v5.drc.EDGE_CLEARANCE_MM 同带画板可视）
    m = 0.2
    parts.append('<rect x="%.4f" y="%.4f" width="%.4f" height="%.4f" '
                 'fill="none" stroke="#ff4444" stroke-width="0.08" '
                 'stroke-dasharray="0.8 0.6" data-role="edge-keepout" '
                 'data-margin-mm="0.2"/>' % (ws["x_min"] + m, ws["y_min"] + m,
                                             w - 2 * m, h - 2 * m))
    # lattice 网格线（pitch 网格; 淡色; data-pitch 机器事实）
    parts.append('<g stroke="#26292f" stroke-width="0.04" '
                 'data-role="lattice" data-pitch-mm="%s" '
                 'data-origin="%s,%s" data-i-max="%d" data-j-max="%d">' % (
                     lat.pitch, lat.x0, lat.y0, lat.i_max, lat.j_max))
    for i in range(lat.i_max + 1):
        x = lat.x0 + i * lat.pitch
        parts.append('<line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f"/>' % (
            x, ws["y_min"], x, ws["y_max"]))
    for j in range(lat.j_max + 1):
        y = lat.y0 + j * lat.pitch
        parts.append('<line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f"/>' % (
            ws["x_min"], y, ws["x_max"], y))
    parts.append('</g>')
    # 板固孔（data-role=hole, data-drill）
    parts.append('<g data-role="holes" data-count="%d">' % len(holes))
    for k, hh in enumerate(holes):
        cx, cy = hh["pos_mm"]
        r = float(hh["drill_mm"]) / 2.0 + 0.25  # 禁布带可视化（0.25 同 drc 带值）
        parts.append('<circle cx="%.4f" cy="%.4f" r="%.4f" fill="none" '
                     'stroke="#5a4a2f" stroke-width="0.03" data-hole="%d" '
                     'data-drill-mm="%s" data-keepout-mm="0.25"/>' % (
                         cx, cy, r, k, hh["drill_mm"]))
        parts.append('<circle cx="%.4f" cy="%.4f" r="%.4f" fill="#0c0d10" '
                     'stroke="#77694d" stroke-width="0.03" data-hole="%d"/>' % (
                         cx, cy, float(hh["drill_mm"]) / 2.0, k))
    parts.append('</g>')
    # 端点焊盘（按网着色）+ 锚格点标记
    parts.append('<g data-role="pads">')
    for p in state.board["partitions"]:
        pid = p["partition_id"]
        net_id = state.partition_net(pid)
        color = net_color(net_id, net_order)
        items = p["geometry"].get("pad_terminals") or []
        eps = state.board_endpoint_mm(pid)
        anchors = state.anchors[pid]
        for k, (ex, ey) in enumerate(eps):
            item = items[k] if k < len(items) else {"shape": "circle",
                                                    "size_mm": [1.0]}
            size = item["size_mm"]
            anchor = ",".join(str(x) for x in anchors[k])
            if item["shape"] == "circle":
                parts.append('<circle cx="%.4f" cy="%.4f" r="%.4f" '
                             'fill="%s" fill-opacity="0.75" stroke="#ffffff" '
                             'stroke-width="0.05" data-pad="%s#%d" '
                             'data-net="%s" data-anchor="%s"/>' % (
                                 ex, ey, float(size[0]) / 2.0, color, pid, k,
                                 net_id, anchor))
            else:
                hw, hh2 = float(size[0]) / 2.0, float(size[1]) / 2.0
                parts.append('<rect x="%.4f" y="%.4f" width="%.4f" '
                             'height="%.4f" fill="%s" fill-opacity="0.75" '
                             'stroke="#ffffff" stroke-width="0.05" '
                             'data-pad="%s#%d" data-net="%s" '
                             'data-anchor="%s"/>' % (
                                 ex - hw, ey - hh2, 2 * hw, 2 * hh2, color,
                                 pid, k, net_id, anchor))
    parts.append('</g>')
    # 已落铜段（按网着色; polyline）
    parts.append('<g data-role="copper-segs">')
    for s in state.segs:
        pts, _stub = inst.segment_mm(state, s)
        d = "M " + " L ".join("%.4f %.4f" % (p[0], p[1]) for p in pts)
        color = net_color(s["net_id"], net_order)
        parts.append('<path d="%s" fill="none" stroke="%s" '
                     'stroke-width="%.2f" stroke-linecap="round" '
                     'stroke-linejoin="round" data-shape="%s" data-net="%s" '
                     'data-layer="%s" data-grid="%s"/>' % (
                         d, color, _verify.WIDTH_MM, s["shape_id"],
                         s["net_id"], s["layer"],
                         " ".join("%d,%d" % (g[0], g[1]) for g in s["grid"])))
    parts.append('</g>')
    # via（按网着色圆环）
    parts.append('<g data-role="vias">')
    for v in state.vias:
        mm = state.lattice.to_mm(*v["grid"])
        color = net_color(v["net_id"], net_order)
        parts.append('<circle cx="%.4f" cy="%.4f" r="0.3" fill="%s" '
                     'fill-opacity="0.9" stroke="#ffffff" stroke-width="0.05" '
                     'data-shape="%s" data-net="%s" '
                     'data-grid="%d,%d"/>' % (
                         mm[0], mm[1], color, v["shape_id"], v["net_id"],
                         v["grid"][0], v["grid"][1]))
    parts.append('</g>')
    # 上轮拒收标记（幽灵提案: 红 x 标在拒收动作的首 waypoint）
    parts.append('<g data-role="last-rejections">')
    for k, rj in enumerate(last_rejections or []):
        g = rj.get("grid_hint")
        if not g or not state.lattice.in_bounds(*g):
            continue
        mm = state.lattice.to_mm(*g)
        parts.append('<path d="M %.3f %.3f L %.3f %.3f M %.3f %.3f L %.3f '
                     '%.3f" stroke="#ff2222" stroke-width="0.12" '
                     'data-rejection="%d" data-code="%s"/>' % (
                         mm[0] - 0.2, mm[1] - 0.2, mm[0] + 0.2, mm[1] + 0.2,
                         mm[0] - 0.2, mm[1] + 0.2, mm[0] + 0.2, mm[1] - 0.2,
                         k, rj.get("code", "?")))
    parts.append('</g>')
    parts.append('</svg>')
    return "\n".join(parts)


def pack_facts(state, round_no, last_rejections):
    """JSON 机器事实（键白名单域; leak_check 强制）。"""
    nets = []
    for n in state.board["nets"]:
        nid = n["net_id"]
        pid = n["partitions"][0]
        eps = state.board_endpoint_mm(pid)
        nets.append({
            "net_id": nid,
            "partition_id": pid,
            "endpoints_mm": [[round(e[0], 4), round(e[1], 4)] for e in eps],
            "endpoint_anchors": [list(a) for a in state.anchors[pid]],
            "routed": bool(state.connectivity.get(nid)),
            "seg_shape_ids": [s["shape_id"] for s in state.segs
                              if s["net_id"] == nid],
            "via_grids": [list(v["grid"]) for v in state.vias
                          if v["net_id"] == nid],
        })
    shapes = [{"shape_id": s["shape_id"], "net_id": s["net_id"],
               "layer": s["layer"], "grid": [list(g) for g in s["grid"]]}
              for s in state.segs]
    vias = [{"shape_id": v["shape_id"], "net_id": v["net_id"],
             "grid": list(v["grid"])} for v in state.vias]
    unrouted = [nid for nid in state.connectivity if not state.connectivity[nid]]
    facts = {
        "canvas_version": "canvas-facts/0.1.0",
        "round": round_no,
        "board_id": state.board["board_id"],
        "lattice": state.lattice.as_dict(),
        "layer_ids": state.signal_layers(),
        "width_mm": _verify.WIDTH_MM,
        "via_radius_mm": 0.3,
        "nets": nets,
        "shapes": shapes,
        "vias": vias,
        "last_rejections": last_rejections or [],
        "unrouted_nets": unrouted,
        "note": "grid coords are integer lattice indices; mm coords are "
                "canvas-owned (pads/hole/lattice facts); actions use integer "
                "grid indices only",
    }
    leak_check(facts)
    return facts


# 禁项词表（值域黑名单扫描——门值/预算词出现在 facts 任何字符串值=泄漏）
_FORBIDDEN_SUBSTRINGS = ("baseline", "budget", "oracle", "g_cp", "G-CP",
                         "max_rounds", "rounds_max", "quota", "deadline")


def leak_check(facts):
    """禁项自检（打包器输出抽样核对强制面; 违者 ValueError）。"""
    import json
    text = json.dumps(facts, sort_keys=True).lower()
    extra = set(facts) - FACTS_TOP_KEYS
    if extra:
        raise ValueError("facts 顶层键越白名单: %s" % sorted(extra))
    for bad in _FORBIDDEN_SUBSTRINGS:
        if bad.lower() in text:
            raise ValueError("facts 疑似禁项泄漏: %r" % (bad,))
    return True
