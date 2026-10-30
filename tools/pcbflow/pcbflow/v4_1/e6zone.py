"""pcbflow.v4_1.e6zone -- zone/铺铜重灌交互负向集（E6 G6.1）。

任务书 §3 E6 + K7：SW_NODE 教训场景化——信号层铺铜重灌（refill）后
shorting 检测的负向测试集。事故锚（只读参照）：

- pcbagent B3 r2/r3（tools/pcbagent/PHASE-REPORT-4.md §4）：SW_NODE 经
  5V-ripup 后 CLI 两次抓到 L1 放行的违规（U3 pad7[5V] vs SW_NODE 孔
  shorting，2.77mm）——L1 未建模「信号铺铜 vs 新孔」的重灌语义；
- apply1（out/coreboard-apply1/PROGRESS.md）：无 refill 口径 +6 stale/
  awaiting-refill 类（GPIO_PE2 3 埋孔 vs In1.Cu 存量 GND 填充）；
- E4（DEV-E4-004）：staging 基线 16 err（无 refill）vs sealed 战役 refill
  口径 10——E4 引擎对 zone 是「存储态填充」建模（无 refill）。

口径边界（E4-report §9.4：zone 填充以存储态多边形建模）。本模块把该
边界变成**有牙齿的测试**：

1. `audit_zone_refill_interactions(board_text)`：静态审计四类重灌交互
   旗标（见 _FLAG_DOCS）；任一旗标 ⇒ commit_blocked_without_refill_drc
   =true——引擎链不得在未过重灌口径 DRC 前提交（fail-closed 语义）；
2. `candidate_zone_exposure(...)`：候选几何（track/via/pad）与 zone
   outline/存储填充 bbox 相交 ⇒ zone_interaction_unverifiable_for_
   candidate（advisory 预检不建模 zone——E1 已登记 limitation；本旗标
   把「zone 在场时 clean 不可作终判」升级为机器可检）；
3. `refill_divergence(drc_norefill, drc_refill)`：kicad-cli 双口径 DRC
   差分（violation 键集 + unconnected 键集）；差分非空=divergent（存储
   态语义在重灌下改变连通/违例语义）——静默通过禁止；
4. `build_scenario_boards()`：ZN-0..ZN-4 场景板构造（确定性合成板 +
   E6 staging 复制口径见编排侧；KiCad 10 可解析格式沿 e2parity 先例）。

判定几何用保守超集（bbox+采样点+边相交；方向=漏报 0，宁可误旗标）。
kicad-cli 仍是唯一 authority：本模块零子进程，oracle 调用经 e6prl
guard 由编排侧执行。零网络、零 wall-clock。
"""

from __future__ import annotations

import json
import math
import re

from . import DECLARED_DATE
from .board_parse import parse_board_text

__all__ = ["ZONE_AUDIT_SCHEMA", "audit_zone_refill_interactions",
           "candidate_zone_exposure", "refill_divergence",
           "extract_zones", "build_scenario_boards", "zone_flag_classes"]

ZONE_AUDIT_SCHEMA = "pcbflow.v4_1.e6-zone-refill-audit/1"

#: 旗标类语义文档（进结果 dict；负向集判据的机器可读部分）
_FLAG_DOCS = {
    "zone_unfilled_refill_will_pour":
        "zone 启用填充但无任何 stored filled_polygon——重灌将新增引擎"
        "未见铜（连通/违例语义改变），提交前必须过重灌口径 DRC",
    "stored_fill_foreign_overlap":
        "既有 item（段/via/pad）与异网 zone 存储填充重叠（存储态未重灌"
        "的 stale 冲突；SW_NODE 原型类）——无 refill 口径下可见 shorting/"
        "clearance，refill 后语义可能翻转",
    "awaiting_refill_same_net":
        "同网 item（via/pad）落在 zone outline 内但不接触该网存储填充"
        "（悬浮；apply1 GPIO_PE2 原型类）——无 refill 口径 unconnected，"
        "refill 后热焊盘连接（unconnected 语义翻转）",
    "zone_interaction_unverifiable_for_candidate":
        "候选几何与 zone（outline 或存储填充）bbox 相交且共享层——"
        "advisory 预检/checker 不建模 zone（E1 limitation），clean 不可"
        "作终判；必须批 DRC（含重灌口径）裁决",
}


def zone_flag_classes():
    return sorted(_FLAG_DOCS)


# ================================================================ 几何（保守超集）

def _bbox_of_pts(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_overlap(a, b, pad=0.0):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0]
                or a[3] + pad < b[1] or b[3] + pad < a[1])


def _point_in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        if (y1 > py) != (y2 > py):
            xc = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if xc > px:
                inside = not inside
    return inside


def _dist_point_seg(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    l2 = vx * vx + vy * vy
    if l2 <= 0.0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * vx + (py - y1) * vy) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))


def _circle_hits_poly(cx, cy, r, poly):
    """圆 vs 多边形（保守超集：内点或边距<r 或中心在内）。"""
    if _point_in_poly(cx, cy, poly):
        return True
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        if _dist_point_seg(cx, cy, x1, y1, x2, y2) <= r:
            return True
    return False


def _seg_hits_poly(ax, ay, bx, by, half_w, poly):
    """线段（含半宽）vs 多边形（保守超集：端点/中点内、边距、bbox）。"""
    if _point_in_poly(ax, ay, poly) or _point_in_poly(bx, by, poly):
        return True
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    if _point_in_poly(mx, my, poly):
        return True
    # 边-边距离粗判：采样段上 9 点（保守超集方向）
    for i in range(9):
        t = (i + 1) / 10.0
        px, py = ax + t * (bx - ax), ay + t * (by - ay)
        n = len(poly)
        for k in range(n):
            x1, y1 = poly[k]
            x2, y2 = poly[(k + 1) % n]
            if _dist_point_seg(px, py, x1, y1, x2, y2) <= half_w:
                return True
    return False


# ================================================================ zone 解析

def _balanced_block(text, start):
    """自 '(' 起的平衡括号块（字符串跳过；e4revc._raster_zone_fills 同式）。"""
    depth, i, n = 0, start, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


def extract_zones(board_text):
    """板文本 -> zone 模型列表（确定性；解析失败项跳过并计数）。

    模型字段：net/layers（zone layer 列表）/fill_enabled/outline_pts/
    fills（[{layer, pts}]）/bbox/zone_index；skipped=未解析块计数。
    """
    zones = []
    skipped = 0
    for m in re.finditer(r'\(zone[\s)]', board_text):
        block = _balanced_block(board_text, m.start())
        if not block.startswith("(zone"):
            skipped += 1
            continue
        netm = re.search(r'\(net\s+"([^"]+)"\)', block)
        if netm is None:
            skipped += 1
            continue
        layers = []
        lm = re.search(r'\(layers\s+((?:"[^"]+"\s*)+)\)', block)
        if lm:
            layers = re.findall(r'"([^"]+)"', lm.group(1))
        else:
            lm1 = re.search(r'\(layer\s+"([^"]+)"\)', block)
            if lm1:
                layers = [lm1.group(1)]
        fill_enabled = re.search(r'\(fill\s+yes', block) is not None
        om = re.search(r'\(polygon\s+(?:\(layer\s+"[^"]+"\)\s*)?\(pts'
                       r'((?:\s*\(xy[^)]*\))+)\s*\)', block, re.DOTALL)
        outline = []
        if om:
            outline = [(float(a), float(b)) for a, b in re.findall(
                r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', om.group(1))]
        fills = []
        for fm in re.finditer(r'\(filled_polygon\s*\(layer "([^"]+)"\)'
                              r'.*?\(pts((?:\s*\(xy[^)]*\))+)\s*\)',
                              block, re.DOTALL):
            pts = [(float(a), float(b)) for a, b in re.findall(
                r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', fm.group(2))]
            if len(pts) >= 3:
                fills.append({"layer": fm.group(1), "pts": pts})
        if not layers or len(outline) < 3:
            skipped += 1
            continue
        zones.append({
            "net": netm.group(1), "layers": layers,
            "fill_enabled": fill_enabled, "outline_pts": outline,
            "fills": fills,
            "bbox": _bbox_of_pts(outline),
            "zone_index": len(zones),
        })
    return zones, skipped


def _shared_layer(item_layers, zone):
    zl = set(zone["layers"])
    if "*" in zl or "*.Cu" in zl:
        return True
    return bool(set(item_layers) & zl)


# ================================================================ 审计（G6.1 核心）

def audit_zone_refill_interactions(board_text):
    """板文本 -> 重灌交互旗标审计（fail-closed：任一旗标阻断无重灌提交）。

    判定方向=保守超集（漏旗标 0：宁可多旗标交 DRC 裁决，不静默放行）。
    """
    zones, skipped = extract_zones(board_text)
    parsed = parse_board_text(board_text)
    flags = []

    def _flag(cls, **kw):
        rec = {"flag": cls, "doc": _FLAG_DOCS[cls]}
        rec.update(kw)
        flags.append(rec)

    for z in zones:
        if z["fill_enabled"] and not z["fills"]:
            _flag("zone_unfilled_refill_will_pour",
                  zone_net=z["net"], zone_layers=sorted(z["layers"]),
                  stored_fill_polygons=0)

    for z in zones:
        for s in parsed["segments"]:
            if s["net"] == z["net"]:
                continue  # 同网豁免（填充对同网 retreat 不改语义）
            hw = float(s["width"]) / 2.0
            ib = (min(s["x1"], s["x2"]) - hw, min(s["y1"], s["y2"]) - hw,
                  max(s["x1"], s["x2"]) + hw, max(s["y1"], s["y2"]) + hw)
            for f in z["fills"]:
                if f["layer"] != s["layer"]:
                    continue
                fb = _bbox_of_pts(f["pts"])
                if _bbox_overlap(ib, fb) and _seg_hits_poly(
                        float(s["x1"]), float(s["y1"]), float(s["x2"]),
                        float(s["y2"]), hw, f["pts"]):
                    _flag("stored_fill_foreign_overlap", zone_net=z["net"],
                          item_kind="segment", item_net=s["net"],
                          item_uuid=s["uuid"], layer=f["layer"])
                    break
        for v in parsed["vias"]:
            if v["net"] == z["net"]:
                # 同网 via：outline 内且不触本网存储填充=awaiting refill
                for li in z["layers"]:
                    if li not in v["layers"] and "*" not in v["layers"]:
                        continue
                    if not _point_in_poly(float(v["x"]), float(v["y"]),
                                          z["outline_pts"]):
                        continue
                    touches = any(
                        _circle_hits_poly(float(v["x"]), float(v["y"]),
                                          float(v["size"]) / 2.0, f["pts"])
                        for f in z["fills"] if f["layer"] == li)
                    if z["fills"] and not touches:
                        _flag("awaiting_refill_same_net", zone_net=z["net"],
                              item_kind="via", item_net=v["net"],
                              item_uuid=v["uuid"], layer=li)
                        break
                continue
            # 异网 via vs 存储填充重叠（SW_NODE 原型）
            for f in z["fills"]:
                if not _shared_layer([f["layer"]], z):
                    continue
                if _circle_hits_poly(float(v["x"]), float(v["y"]),
                                     float(v["size"]) / 2.0, f["pts"]):
                    _flag("stored_fill_foreign_overlap", zone_net=z["net"],
                          item_kind="via", item_net=v["net"],
                          item_uuid=v["uuid"], layer=f["layer"])
                    break
        for p in parsed["pads"]:
            if not p["layers"]:
                continue
            net = str(p["net_id"])
            if net == z["net"]:
                continue
            ib = (p["x_mm"] - p["w_mm"] / 2.0, p["y_mm"] - p["h_mm"] / 2.0,
                  p["x_mm"] + p["w_mm"] / 2.0, p["y_mm"] + p["h_mm"] / 2.0)
            for f in z["fills"]:
                if f["layer"] not in p["layers"]:
                    continue
                fb = _bbox_of_pts(f["pts"])
                if _bbox_overlap(ib, fb) and (
                        _point_in_poly(p["x_mm"], p["y_mm"], f["pts"])
                        or _circle_hits_poly(p["x_mm"], p["y_mm"],
                                             min(p["w_mm"], p["h_mm"]) / 2.0,
                                             f["pts"])):
                    _flag("stored_fill_foreign_overlap", zone_net=z["net"],
                          item_kind="pad", item_net=net,
                          item_uuid=p["pad_id"], layer=f["layer"])
                    break

    blocked = bool(flags)
    return {
        "schema": ZONE_AUDIT_SCHEMA,
        "declared_date": DECLARED_DATE,
        "zones": [{"net": z["net"], "layers": sorted(z["layers"]),
                   "fill_enabled": z["fill_enabled"],
                   "stored_fill_polygons": len(z["fills"])}
                  for z in zones],
        "zones_unparsed": skipped,
        "flags": sorted(flags, key=lambda f: (f["flag"],
                                              str(f.get("item_uuid", "")))),
        "flag_classes_present": sorted({f["flag"] for f in flags}),
        "commit_blocked_without_refill_drc": blocked,
        "conservatism": "bbox+采样+边距保守超集（漏旗标 0 方向；多旗标"
                        "交 kicad-cli 双口径 DRC 裁决）",
    }


def candidate_zone_exposure(candidate_kind, net, layers, bbox, board_text):
    """候选几何（track/via/pad 的 bbox+层）vs zone 交互不可判定旗标。

    E1 预检/checker 不建模 zone（已登记 limitation）；本函数把「候选
    落在 zone 交互域内 ⇒ advisory clean 不可作终判」变成机器可检——
    链上必须以批 DRC（含重灌口径）裁决。
    """
    zones, _skipped = extract_zones(board_text)
    hits = []
    for z in zones:
        if net == z["net"]:
            continue
        if not _shared_layer(layers, z):
            continue
        if _bbox_overlap(bbox, z["bbox"]):
            fills_layers = sorted({f["layer"] for f in z["fills"]})
            hits.append({"zone_net": z["net"],
                         "zone_layers": sorted(z["layers"]),
                         "stored_fill_layers": fills_layers})
    exposed = bool(hits)
    result = {
        "schema": ZONE_AUDIT_SCHEMA,
        "declared_date": DECLARED_DATE,
        "candidate": {"kind": candidate_kind, "net": net,
                      "layers": list(layers),
                      "bbox": [round(v, 6) for v in bbox]},
        "zone_hits": hits,
        "flag": ("zone_interaction_unverifiable_for_candidate"
                 if exposed else None),
        "advisory_clean_usable_as_final_verdict": not exposed,
    }
    if exposed:
        result["doc"] = _FLAG_DOCS[
            "zone_interaction_unverifiable_for_candidate"]
    return result


# ================================================================ 双口径差分

def _viol_key(v):
    items = sorted(str(i.get("description", "")) for i in v.get("items", []))
    return (str(v.get("type", "")), tuple(items),
            str(v.get("severity", "")))


def _unc_key(u):
    items = sorted(str(i.get("description", "")) for i in u.get("items", []))
    return tuple(items)


def refill_divergence(drc_norefill, drc_refill):
    """kicad-cli 双口径 DRC 差分（violation+unconnected 键集）。

    divergent = 任一键集差分非空：存储态填充语义在重灌下改变连通/违例
    语义——引擎链在存储态口径下的判定不可直接外推，须 fail-closed。
    """
    a = drc_norefill if isinstance(drc_norefill, dict) else json.loads(
        drc_norefill)
    b = drc_refill if isinstance(drc_refill, dict) else json.loads(
        drc_refill)
    va = {_viol_key(v) for v in a.get("violations", [])}
    vb = {_viol_key(v) for v in b.get("violations", [])}
    ua = {_unc_key(u) for u in a.get("unconnected_items", [])}
    ub = {_unc_key(u) for u in b.get("unconnected_items", [])}
    viol_added = sorted([list(k) for k in (vb - va)])
    viol_removed = sorted([list(k) for k in (va - vb)])
    unc_added = sorted([list(k) for k in (ub - ua)])
    unc_removed = sorted([list(k) for k in (ua - ub)])
    divergent = bool(viol_added or viol_removed or unc_added or unc_removed)
    return {
        "schema": ZONE_AUDIT_SCHEMA,
        "declared_date": DECLARED_DATE,
        "violations_norefill": len(va),
        "violations_refill": len(vb),
        "unconnected_norefill": len(ua),
        "unconnected_refill": len(ub),
        "violation_added_under_refill": viol_added,
        "violation_removed_under_refill": viol_removed,
        "unconnected_added_under_refill": unc_added,
        "unconnected_removed_under_refill": unc_removed,
        "divergent": divergent,
        "verdict": "divergent" if divergent else "consistent",
        "fail_closed_rule": "divergent ⇒ 存储态口径判定不可外推；提交"
                            "链必须以重灌口径 DRC 复核后裁（禁静默通过）",
    }


# ================================================================ 场景板构造

def _f(v):
    s = ("%.6f" % float(v)).rstrip("0")
    return s + "0" if s.endswith(".") else s


def _board_text_2l(items):
    lines = [
        "(kicad_pcb",
        '\t(version 20260206)',
        '\t(generator "pcbnew")',
        '\t(generator_version "10.0")',
        "\t(general",
        "\t\t(thickness 1.6)",
        "\t)",
        '\t(paper "A4")',
        "\t(layers",
        '\t\t(0 "F.Cu" signal)',
        '\t\t(31 "B.Cu" signal)',
        '\t\t(13 "F.Paste" user)',
        '\t\t(15 "B.Paste" user)',
        '\t\t(1 "F.Mask" user)',
        '\t\t(3 "B.Mask" user)',
        '\t\t(5 "F.SilkS" user "F.Silkscreen")',
        '\t\t(7 "B.SilkS" user "B.Silkscreen")',
        '\t\t(25 "Edge.Cuts" user)',
        "\t)",
        "\t(gr_rect",
        "\t\t(start 0 0)",
        "\t\t(end 60 40)",
        '\t\t(stroke (width 0.05) (type default))',
        "\t\t(fill no)",
        '\t\t(layer "Edge.Cuts")',
        '\t\t(uuid "e6fr0000-0000-0000-0000-000000000000")',
        "\t)",
    ]
    lines.extend(items)
    lines.append(")")
    return "\n".join(lines) + "\n"


def _segment(uuid, net, layer, x1, y1, x2, y2, width):
    return ("\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t"
            "(width %s)\n\t\t(layer \"%s\")\n\t\t(net \"%s\")\n\t\t"
            "(uuid \"%s\")\n\t)"
            % (_f(x1), _f(y1), _f(x2), _f(y2), _f(width), layer, net,
               uuid))


def _via(uuid, net, l1, l2, x, y, size=0.6, drill=0.3):
    return ("\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t"
            "(layers \"%s\" \"%s\")\n\t\t(net \"%s\")\n\t\t"
            "(uuid \"%s\")\n\t)"
            % (_f(x), _f(y), _f(size), _f(drill), l1, l2, net, uuid))


def _footprint_smd(uuid, net, x, y, w=1.2, h=1.2, ref="ES1",
                   layer="F.Cu"):
    return ("\t(footprint \"E6-SMD\"\n\t\t(layer \"%s\")\n\t\t"
            "(at %s %s)\n\t\t(property \"Reference\" \"%s\" (at 0 0) "
            '(layer "F.SilkS"))\n'
            "\t\t(pad \"1\" smd rect (at 0 0) (size %s %s)\n\t\t\t"
            "(layers \"%s\") (net \"%s\") (uuid \"%s\"))\n\t)"
            % (layer, _f(x), _f(y), ref, _f(w), _f(h), layer, net, uuid))


def _zone(uid, net, layer, outline, fills=(), fill_yes=True,
          island_removal_mode=0):
    zl = ['\t(zone',
          '\t\t(net "%s")' % net,
          '\t\t(layer "%s")' % layer,
          '\t\t(uuid "%s")' % uid,
          '\t\t(hatch edge 0.5)',
          '\t\t(connect_pads',
          '\t\t\t(clearance 0.2)',
          '\t\t)',
          '\t\t(min_thickness 0.2)',
          '\t\t(fill %s' % ("yes" if fill_yes else "no"),
          '\t\t\t(thermal_gap 0.5)',
          '\t\t\t(thermal_bridge_width 0.5)',
          '\t\t\t(island_removal_mode %d)' % island_removal_mode,
          '\t\t)',
          '\t\t(polygon',
          '\t\t\t(pts',
          ]
    for (x, y) in outline:
        zl.append('\t\t\t\t(xy %s %s) ' % (_f(x), _f(y)))
    zl.append('\t\t\t)')
    zl.append('\t\t)')
    for (flayer, fpts) in fills:
        zl.append('\t\t(filled_polygon')
        zl.append('\t\t\t(layer "%s")' % flayer)
        zl.append('\t\t\t(pts')
        for (x, y) in fpts:
            zl.append('\t\t\t\t(xy %s %s) ' % (_f(x), _f(y)))
        zl.append('\t\t\t)')
        zl.append('\t\t)')
    zl.append('\t)')
    return "\n".join(zl)


def _minimal_pro():
    return {
        "board": {"3dviewports": [], "design_settings": [],
                  "layer_presets": [], "viewports": []},
        "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [],
                      "pinned_symbol_libs": []},
        "meta": {"filename": "case.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [{
                "bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                "line_style": 0, "microvia_drill": 0.1, "name": "Default",
                "pcb_color": "rgba(0, 0, 0, 0.000000)",
                "schematic_color": "rgba(0, 0, 0, 0.000000)",
                "track_width": 0.25, "via_diameter": 0.8, "via_drill": 0.4,
                "wire_width": 6}],
            "netclass_assignments": {}, "netclass_patterns": []},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {},
    }


#: 存储填充矩形辅助（含中央洞=外环-内环两多边形，even-odd 语义）
def _rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def build_scenario_boards():
    """ZN-0..ZN-4 确定性场景板（负向集输入；ZN-5 真板走编排侧复制）。

    每项 {"scenario_id", "board_text", "pro_obj", "guard_expect",
    "oracle_expect"}；uuid 内容派生（e2parity 先例）。
    """
    sc = {}

    # ---- ZN-0 负对照：无 zone 的连通合法小板（guard 零旗标+双口径一致）
    sc["ZN-0-no-zone-negative-control"] = {
        "board_text": _board_text_2l([
            _footprint_smd("e6a00000-0000-0000-0000-000000000000",
                           "nA", 10, 10),
            _footprint_smd("e6a00001-0000-0000-0000-000000000001",
                           "nA", 20, 10),
            _segment("e6a00002-0000-0000-0000-000000000002", "nA",
                     "F.Cu", 10, 10, 20, 10, 0.25),
        ]),
        "pro_obj": _minimal_pro(),
        "guard_expect": [],
        "oracle_expect": "双口径一致（无 zone ⇒ refill 无语义改变面）",
    }

    # ---- ZN-1 SW_NODE 原型：异网 via 打进存储填充（stale overlap）
    # SIG 全连通：B.Cu pad(55,20)+段(30..55,20)+via(30,20 F-B 跨度)；
    # 唯一 F.Cu SIG 铜=via 环，落在 P5V 存储填充 (25,15)-(45,25) 内。
    fill1 = _rect_pts(25, 15, 45, 25)
    sc["ZN-1-stale-fill-foreign-via"] = {
        "board_text": _board_text_2l([
            _footprint_smd("e6b00000-0000-0000-0000-000000000000",
                           "P5V", 30, 8),
            _segment("e6b00001-0000-0000-0000-000000000001", "P5V",
                     "F.Cu", 30, 8, 30, 16, 0.25),
            _footprint_smd("e6b00002-0000-0000-0000-000000000002",
                           "SIG", 55, 20, layer="B.Cu"),
            _segment("e6b00003-0000-0000-0000-000000000003", "SIG",
                     "B.Cu", 30, 20, 55, 20, 0.25),
            _via("e6b00004-0000-0000-0000-000000000004", "SIG",
                 "F.Cu", "B.Cu", 30, 20),
            _zone("e6b00005-0000-0000-0000-000000000005", "P5V", "F.Cu",
                  _rect_pts(24, 14, 46, 26),
                  fills=[("F.Cu", fill1)]),
        ]),
        "pro_obj": _minimal_pro(),
        "guard_expect": ["stored_fill_foreign_overlap"],
        "oracle_expect": "norefill：shorting（SIG via vs P5V 存储填充）；"
                         "refill：铜 retreat ⇒ 该违例消失 → divergent",
    }

    # ---- ZN-2 未灌铜 zone：outline 无填充，同网双 pad 仅可经倒铜连通
    sc["ZN-2-unfilled-zone-pour"] = {
        "board_text": _board_text_2l([
            _footprint_smd("e6c00000-0000-0000-0000-000000000000",
                           "ZNET", 30, 10),
            _footprint_smd("e6c00001-0000-0000-0000-000000000001",
                           "ZNET", 30, 30),
            _zone("e6c00002-0000-0000-0000-000000000002", "ZNET", "F.Cu",
                  _rect_pts(24, 6, 36, 34), fills=[]),
        ]),
        "pro_obj": _minimal_pro(),
        "guard_expect": ["zone_unfilled_refill_will_pour"],
        "oracle_expect": "norefill：unconnected 含 ZNET（两 pad 无铜连"
                         "通）；refill：倒铜+热焊盘连通 ⇒ unconnected "
                         "差分非空",
    }

    # ---- ZN-3 apply1 原型：同网两片铜仅可经重灌连通（awaiting refill）
    # G 片1=padA(28,20 F) 在存储填充(24..32)内；片2=B.Cu padB(55,20)+
    # 段+via(35,20 F-B)；via 在 outline(24..46) 内但存储填充未及。
    outline3 = _rect_pts(24, 14, 46, 26)
    partial_fill = _rect_pts(24, 14, 32, 26)  # 存储填充只到 x=32（stale）
    sc["ZN-3-awaiting-refill-same-net"] = {
        "board_text": _board_text_2l([
            _footprint_smd("e6d00000-0000-0000-0000-000000000000",
                           "G", 28, 20),
            _footprint_smd("e6d00001-0000-0000-0000-000000000001",
                           "G", 55, 20, layer="B.Cu"),
            _segment("e6d00002-0000-0000-0000-000000000002", "G",
                     "B.Cu", 35, 20, 55, 20, 0.25),
            _via("e6d00003-0000-0000-0000-000000000003", "G",
                 "F.Cu", "B.Cu", 35, 20),
            _zone("e6d00004-0000-0000-0000-000000000004", "G", "F.Cu",
                  outline3, fills=[("F.Cu", partial_fill)]),
        ]),
        "pro_obj": _minimal_pro(),
        "guard_expect": ["awaiting_refill_same_net"],
        "oracle_expect": "norefill：G 两片（unconnected G）；refill：填充"
                         "扩及 outline+热焊盘接 via ⇒ unconnected 差分",
    }

    # ---- ZN-4 存储填充 vs 异网走线（ZN-1 的 track 形态）
    # SIG 全连通：F.Cu pad(55,20)+段(20..55,20) 横穿 P5V 存储填充。
    fill4 = _rect_pts(25, 15, 45, 25)
    sc["ZN-4-stale-fill-foreign-track"] = {
        "board_text": _board_text_2l([
            _footprint_smd("e6e00000-0000-0000-0000-000000000000",
                           "P5V", 30, 8),
            _segment("e6e00001-0000-0000-0000-000000000001", "P5V",
                     "F.Cu", 30, 8, 30, 16, 0.25),
            _footprint_smd("e6e00002-0000-0000-0000-000000000002",
                           "SIG", 55, 20),
            _segment("e6e00003-0000-0000-0000-000000000003", "SIG",
                     "F.Cu", 20, 20, 55, 20, 0.25),
            _zone("e6e00004-0000-0000-0000-000000000004", "P5V", "F.Cu",
                  _rect_pts(24, 14, 46, 26),
                  fills=[("F.Cu", fill4)]),
        ]),
        "pro_obj": _minimal_pro(),
        "guard_expect": ["stored_fill_foreign_overlap"],
        "oracle_expect": "norefill：SIG 段 vs P5V 存储填充 shorting；"
                         "refill：retreat ⇒ 消除 → divergent",
    }
    return sc
