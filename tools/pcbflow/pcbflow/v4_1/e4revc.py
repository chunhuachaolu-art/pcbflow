"""pcbflow.v4_1.e4revc -- E4 L2/L3：Rev-C 真实板 required-rows 批纪律推进
（堵 K4；任务书 §3 E4 + §0.2.1 + FC2 纪律）。

链路（全部确定性，零网络零模型零子进程；kicad-cli 由 Bash 侧在批目录
相对路径执行，本模块只读其产物）：

1. 行派生 derive_rows：staging 基线 DRC（severity-error）unconnected_items
   -> required rows（GND 行排除，先例 opens.csv 65=61 信号+4 GND）；逐
   item 提取 pos/layer/类别（track/pad/via），层不可解析=fail-closed 剔除
   单行并登记；
2. 板投影 build_projection：v4_1.board_parse（A 路径）解析既有铜 -> v4exp
   格点世界（0.25mm；bbox=Edge.Cuts 外接矩形）；既有铜 raster 阻挡按逐
   item 精确 margin（required_clearance + 两侧半宽，宽铜/大 pad 按真实
   尺寸）——比 v4exp 均质假设保守，登记为 E4 投影口径；板边 clearance
   （0.5+w/2）亦入阻挡；
3. 求解 route_row：solver2._astar2（v4exp 冻结 A* 镜像；分层 via 成本
   默认）+ 端点 snap 阶梯（格点 8 邻内最近可用格，真实端点以 stitch 段
   缝合，预检把关）-> KiCad segment/via 文本节点（内容派生 uuid）；
4. 预检：AdvisoryPrecheckV41（build_geom_items+近场 bbox 预过滤——只
   加速不改判定集）逐段/via 复查；net class 表=live .kicad_pro 载入；
5. rip-up 升级梯（G4.2 五级）：T1 批回滚/T2 同批重排（批级，batch_record
   与重规划侧）/T3 局部换层/T4 局部 rip-up（阻挡归因撕网+连通性恢复
   重布，恢复失败=弃用零板面变化）/T5 走廊重分配（北/南绕行 waypoint）；
   逐触发入 ripup-ledger；
6. 批纪律：pre/post hash、批 DRC 双口径、零新增 severity-error 硬门、
   整批回滚、prl 卫生（prl_hygiene.check_and_restore）。

CLI ops（编排）：
  stage-init / rows / batch-plan / batch-apply / batch-record /
  l3-rows / g43 / progress

红线：零 live 板写（一切 staging 快照副本）；受保护三文件零变化；
datasets/ 零写入；无 wall-clock（declared_date 常量）。
"""

from __future__ import annotations

import hashlib
import math
import re

from . import DECLARED_DATE
from .board_parse import parse_board_text
from .canonical import write_canonical_json
from .costmodel import ViaCostModel
from .geometry import clearance_between_items
from .netclasses import load_netclasses
from .precheck import AdvisoryPrecheckV41, build_geom_items

__all__ = [
    "derive_rows", "extract_net_name", "parse_drc_item_desc",
    "build_world_for_row", "rasterize_existing_copper",
    "route_row", "row_ladder_route", "emit_ops", "apply_ops_to_text",
    "E4RevcError", "precheck_ops",
]

GRID_MM = 0.25
_NEW_VIA_SIZE = 0.6
_NEW_VIA_DRILL = 0.3
#: 板边（Edge.Cuts）铜间距约束（b3/final-drc copper_edge_clearance 报文：
#: "板边" 约束 间距 0.5000 mm）
_EDGE_CLEARANCE_MM = 0.5
#: 端点 snap 搜索半径（格点数）。逐级核验（2 -> 4 -> 10，DEV-E4-001）：
#: 真距诊断显示行端点最近可用格在 ring 3-10（0.75-2.5mm，引脚场逃逸
#: 走廊）；prereg『8 邻』口径不足以触达。半径 10 + stitch 段由精确
#: 预检（同网豁免+异网 0.2 精确 clearance）+ 批 DRC 把关，fail 方向安全
_SNAP_RADIUS_CELLS = 10
#: T4 局部 rip-up 的最大撕网数
_RIPUP_MAX_NETS = 3


class E4RevcError(ValueError):
    """E4 Rev-C 链 fail-closed。"""


# ================================================================ 行派生

_NET_BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
_TRACK_LAYER_RE = re.compile(r"\(([A-Za-z0-9_.]+\.Cu)\)")
_PAD_LAYER_RE = re.compile(r"^([A-Za-z0-9_.]+\.Cu) 上 ")


def extract_net_name(desc):
    """item 描述 -> 网名（[net] 括号；缺=无主行 None）。"""
    m = _NET_BRACKET_RE.search(desc or "")
    return m.group(1) if m else None


def parse_drc_item_desc(desc):
    """item 描述 -> {kind, layer, ref}（层不可解析=fail-closed None 层）。

    已知形态（b3/b4 DRC 实测）：
      走线 [3V3] (F.Cu), 长度: 4.5763 mm
      F.Cu 上 U1 的焊盘 23 [3V3]
      过孔 [net] (x,y) size=... drill=...
    """
    kind = "unknown"
    layer = None
    ref = None
    d = desc or ""
    if d.startswith("走线"):
        kind = "track"
        m = _TRACK_LAYER_RE.search(d)
        layer = m.group(1) if m else None
    elif "焊盘" in d:
        kind = "pad"
        m = _PAD_LAYER_RE.match(d)
        layer = m.group(1) if m else None
        pm = re.match(r"^(?:[A-Za-z0-9_.]+\.Cu) 上 (\S+) 的焊盘 (\S+)", d)
        if pm:
            ref = "%s.%s" % (pm.group(1), pm.group(2))
    elif d.startswith("过孔"):
        kind = "via"
    return {"kind": kind, "layer": layer, "ref": ref}


def _item_pos(item):
    pos = item.get("pos") or {}
    return float(pos.get("x")), float(pos.get("y"))


def derive_rows(drc_obj, exclude_nets=("GND",)):
    """staging 基线 DRC（severity-error run）-> 行记录列表。

    行=unconnected_items 元素；required=网非排除集（默认 GND）。
    层解析失败/无网的行进 dropped（fail-closed 登记不静默猜）。
    确定性序：(net, ax, ay, bx, by, row_signature)。
    """
    items = drc_obj.get("unconnected_items") or []
    rows, dropped = [], []
    for k, row in enumerate(items):
        its = row.get("items") or []
        if len(its) < 2:
            dropped.append({"index": k, "reason": "items<2"})
            continue
        a, b = its[0], its[1]
        na = extract_net_name(a.get("description", ""))
        nb = extract_net_name(b.get("description", ""))
        if na is None or nb is None or na != nb:
            dropped.append({"index": k, "reason": "net_mismatch:%r/%r"
                            % (na, nb)})
            continue
        pa = parse_drc_item_desc(a.get("description", ""))
        pb = parse_drc_item_desc(b.get("description", ""))
        ax, ay = _item_pos(a)
        bx, by = _item_pos(b)
        sig = "%s|%.4f,%.4f|%.4f,%.4f" % (na, ax, ay, bx, by)
        rec = {
            "row_index": k,
            "net": na,
            "a": {"kind": pa["kind"], "layer": pa["layer"], "ref": pa["ref"],
                  "x": round(ax, 6), "y": round(ay, 6),
                  "desc": a.get("description", "")},
            "b": {"kind": pb["kind"], "layer": pb["layer"], "ref": pb["ref"],
                  "x": round(bx, 6), "y": round(by, 6),
                  "desc": b.get("description", "")},
            "row_signature": sig,
        }
        if na in exclude_nets:
            rec["class"] = "excluded_gnd"
        else:
            rec["class"] = "required"
        rows.append(rec)
    rows.sort(key=lambda r: (r["net"], r["a"]["x"], r["a"]["y"],
                             r["b"]["x"], r["b"]["y"], r["row_signature"]))
    for i, r in enumerate(rows):
        r["row_id"] = "E4R-%03d" % (i + 1)
    return rows, dropped


# ================================================================ 板投影

def extract_board_bbox(text):
    """Edge.Cuts 外接矩形（gr_line/gr_rect/gr_arc/gr_circle 顶点收集）。

    假设板轮廓为其外接矩形（Rev-C 实况矩形板；非矩形板=保守超集，
    登记于调用侧 limitations）。
    """
    from ..p3_revc_staging import _top_spans
    pts = []
    for tag in ("gr_line", "gr_rect", "gr_arc", "gr_circle"):
        for (a, b) in _top_spans(text, tag):
            node = text[a:b]
            if '"Edge.Cuts"' not in node:
                continue
            for t2 in ("start", "end", "center", "mid"):
                for pm in re.finditer(
                        r'\(%s\s+(-?[\d.]+)\s+(-?[\d.]+)\)' % t2, node):
                    pts.append((float(pm.group(1)), float(pm.group(2))))
    if not pts:
        raise E4RevcError("Edge.Cuts 顶点为空（fail-closed）")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def _seg_point_dist2(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 <= 1e-18:
        return (px - x1) ** 2 + (py - y1) ** 2
    t = ((px - x1) * dx + (py - y1) * dy) / L2
    t = max(0.0, min(1.0, t))
    qx, qy = x1 + t * dx, y1 + t * dy
    return (px - qx) ** 2 + (py - qy) ** 2


def _rotated_pad_half_extents(w, h, rot_deg):
    """旋转 pad 的轴对齐包围盒半延展（保守超集）。"""
    t = math.radians(rot_deg or 0.0)
    c, s = abs(math.cos(t)), abs(math.sin(t))
    return (w * c + h * s) / 2.0, (w * s + h * c) / 2.0


class RevCProjection:
    """Rev-C 板 -> v4exp 格点世界 + 既有铜 raster 阻挡（逐网合并缓存）。

    raster 口径（E4 投影，登记不静默）：
    - 既有段（layer L, width ws, net N）：格心到段中心线距离 <
      required_clearance(N,M) + w_new/2 + ws/2 的格全部阻挡（新走线 M）；
    - 既有 via（size s）：格心距 < clearance + w_new/2 + s/2（跨度全层）；
    - 既有 pad：旋转包围盒半延展 + clearance + w_new/2 的矩形扩张（保守
      超集；custom 基元按顶点包围盒）；
    - 板边：格心超出 [x0+edge+m, x1-edge-m] 阻挡（edge=0.5 板边约束）；
    - 同网/同批 protected 网铜不阻挡（批纪律：批内互不约束，批 DRC 兜底）。
    """

    def __init__(self, board_text, kicad_pro_obj=None, net_table=None,
                 new_via_size=_NEW_VIA_SIZE):
        self.text = board_text
        name_map = net_names_from_text(board_text)
        self.parsed = parsed_with_names(parse_board_text(board_text),
                                        name_map)
        self.name_map = name_map
        self.copper = list(self.parsed["copper_layers"])
        if net_table is not None:
            self.net_table = net_table
        else:
            self.net_table = load_netclasses(board_text=board_text,
                                             kicad_pro_obj=kicad_pro_obj)
        self.bbox = extract_board_bbox(board_text)
        self.new_via_size = new_via_size
        default_clearance = self._default_clearance()
        if default_clearance is None:
            # SEC-A-07 修复（REPAIR-P3S W-A）：Default clearance 不可解析
            # 时不构造投影（回退默认值=放行方向，已废除），由批编排侧
            # 按整批 blocked/notes 记录。
            raise E4RevcError("RevCProjection 构造失败：%s"
                              % self.default_clearance_error)
        # v4exp 板 dict（GridWorld 载体；端点 pad 按行注入）
        self._base_board = {
            "schema": "pcbflow.v4exp.board/1",
            "scenario_id": "e4revc-projection",
            "split": "development", "family": "f1", "seed": 0,
            "board": {"bbox_mm": list(self.bbox),
                      "layers": list(self.copper)},
            "rules": {
                "grid_mm": GRID_MM,
                "clearance_mm": default_clearance,
                "width_mm": {"default": 0.2, "clock": 0.2},
                "via": {"pad_mm": new_via_size, "hole_mm": _NEW_VIA_DRILL},
                "allowed_layers": {"default": list(self.copper),
                                   "clock": list(self.copper)},
            },
            "pads": [], "nets": [], "keepouts": [], "relations": [],
            "label": "satisfiable",
        }
        from ..v4exp.grid import GridWorld
        self.world = GridWorld(self._base_board)
        self._per_net_cells = None   # net -> {layer_idx: set(cells)}

    def _default_clearance(self):
        """Default 网类 clearance。

        SEC-A-07 修复（REPAIR-P3S W-A）：解析失败不再静默回退 0.2mm（回退
        = 阻挡图偏小 = 放行方向）。失败 ⇒ 记 self.default_clearance_error
        并返回 None；__init__ 检到即抛 E4RevcError，批编排侧（op_batch_plan）
        按整批 blocked/notes 记录。"""
        try:
            return self.net_table.resolve("Default").clearance_mm
        except Exception as e:
            self.default_clearance_error = (
                "net 表 Default clearance 解析失败（%s: %s）——SEC-A-07 "
                "口径：不回退默认值，批记 blocked" % (type(e).__name__, e))
            return None

    # ------------------------------------------------------------ 阻挡

    def per_net_cells(self):
        """既有铜逐网 raster（惰性缓存；含板边阻挡项 __edge__）。"""
        if self._per_net_cells is not None:
            return self._per_net_cells
        w = self.world
        per = {}
        edge = {"__edge__": {li: set() for li in range(len(self.copper))}}
        margin_edge = _EDGE_CLEARANCE_MM + 0.1  # +max 半宽（宽 0.2 以下）
        for li in range(len(self.copper)):
            banned = set()
            for ix in range(w.nx):
                for iy in range(w.ny):
                    x = w.center_mm_x(ix)
                    y = w.center_mm_y(iy)
                    if (x < self.bbox[0] + margin_edge
                            or x > self.bbox[2] - margin_edge
                            or y < self.bbox[1] + margin_edge
                            or y > self.bbox[3] - margin_edge):
                        banned.add((ix, iy))
            edge["__edge__"][li] = banned
        per.update(edge)

        def _cells_of_segment(seg, margin):
            x1, y1, x2, y2 = seg["x1"], seg["y1"], seg["x2"], seg["y2"]
            lo_x = min(x1, x2) - margin
            hi_x = max(x1, x2) + margin
            lo_y = min(y1, y2) - margin
            hi_y = max(y1, y2) + margin
            ix0 = max(int(math.ceil((lo_x - w.origin_x) / GRID_MM - 1e-9)), 0)
            ix1 = min(int(math.floor((hi_x - w.origin_x) / GRID_MM + 1e-9)),
                      w.nx - 1)
            iy0 = max(int(math.ceil((lo_y - w.origin_y) / GRID_MM - 1e-9)), 0)
            iy1 = min(int(math.floor((hi_y - w.origin_y) / GRID_MM + 1e-9)),
                      w.ny - 1)
            m2 = margin * margin
            out = set()
            for ix in range(ix0, ix1 + 1):
                px = w.center_mm_x(ix)
                for iy in range(iy0, iy1 + 1):
                    py = w.center_mm_y(iy)
                    if _seg_point_dist2(px, py, x1, y1, x2, y2) < m2:
                        out.add((ix, iy))
            return out

        for seg in self.parsed["segments"]:
            net = str(seg["net"])
            li = w.layer_index.get(str(seg["layer"]))
            if li is None:
                continue
            margin = self._margin_for(net, float(seg["width"]))
            per.setdefault(net, {l: set() for l in range(len(self.copper))})
            per[net].setdefault(li, set()).update(
                _cells_of_segment(seg, margin))
        for v in self.parsed["vias"]:
            net = str(v["net"])
            r = float(v["size"]) / 2.0
            margin = self._margin_for(net, 0.2) + r
            ix = w.cell_x(v["x"])
            iy = w.cell_y(v["y"])
            rad = int(math.ceil(margin / GRID_MM))
            for li in (w.layer_index[s] for s in v["layers"]
                       if s in w.layer_index):
                cells = set()
                for dx in range(-rad, rad + 1):
                    for dy in range(-rad, rad + 1):
                        cx = w.center_mm_x(ix + dx)
                        cy = w.center_mm_y(iy + dy)
                        if (cx - v["x"]) ** 2 + (cy - v["y"]) ** 2 \
                                < margin * margin:
                            cells.add((ix + dx, iy + dy))
                per.setdefault(net, {l: set() for l in
                                     range(len(self.copper))})
                per[net].setdefault(li, set()).update(cells)
        for p in self.parsed["pads"]:
            net = str(p["net_id"])
            if not p["layers"]:
                continue
            hw, hh = _rotated_pad_half_extents(float(p["w_mm"]),
                                               float(p["h_mm"]),
                                               float(p["rotation_deg"] or 0.0))
            margin = self._margin_for(net, 0.2)
            for lname in p["layers"]:
                li = w.layer_index.get(lname)
                if li is None:
                    continue
                x0 = p["x_mm"] - hw - margin
                x1 = p["x_mm"] + hw + margin
                y0 = p["y_mm"] - hh - margin
                y1 = p["y_mm"] + hh + margin
                ix0 = max(int(math.ceil((x0 - w.origin_x) / GRID_MM - 1e-9)),
                          0)
                ix1 = min(int(math.floor((x1 - w.origin_x) / GRID_MM + 1e-9)),
                          w.nx - 1)
                iy0 = max(int(math.ceil((y0 - w.origin_y) / GRID_MM - 1e-9)),
                          0)
                iy1 = min(int(math.floor((y1 - w.origin_y) / GRID_MM + 1e-9)),
                          w.ny - 1)
                cells = {(ix, iy) for ix in range(ix0, ix1 + 1)
                         for iy in range(iy0, iy1 + 1)}
                per.setdefault(net, {l: set() for l in
                                     range(len(self.copper))})
                per[net].setdefault(li, set()).update(cells)
        self._per_net_cells = per
        self._raster_zone_fills(per)
        self._per_net_cells = per
        return per

    def _raster_zone_fills(self, per):
        """zone 填充多边形入 raster（GND 平面=真实铜；保守建模）。

        (zone (net "N") ... (filled_polygon (layer "L") (pts (xy ..) ..)))
        -> 扫描线 even-odd 内点集 + margin Chebyshev 膨胀（保守超集：
        膨胀半径 ceil(margin/grid) >= 精确 margin 带）。E1 limitation
        （预检不建模 zone）在 E4 投影侧以 raster 方式补上（DRC 仍为
        唯一 authority）。
        """
        w = self.world
        for zm in re.finditer(r'\(zone\s*\(net "([^"]+)"\)', self.text):
            znet = zm.group(1)
            zstart = zm.start()
            depth, i, n = 0, zstart, len(self.text)
            while i < n:
                c = self.text[i]
                if c == '"':
                    i += 1
                    while i < n:
                        if self.text[i] == "\\":
                            i += 2
                            continue
                        if self.text[i] == '"':
                            break
                        i += 1
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            ztext = self.text[zstart:i + 1]
            for fm in re.finditer(
                    r'\(filled_polygon\s*\(layer "([^"]+)"\)(.*?)'
                    r'\(pts((?:\s*\(xy[^)]*\))++)\s*\)', ztext,
                    re.DOTALL):
                lname = fm.group(1)
                li = w.layer_index.get(lname)
                if li is None:
                    continue
                pts = [(float(a), float(b)) for a, b in re.findall(
                    r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', fm.group(3))]
                if len(pts) < 3:
                    continue
                margin = self._margin_for(znet, 0.0)
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                iy0 = max(int(math.ceil(
                    (min(ys) - w.origin_y) / GRID_MM - 1e-9)), 0)
                iy1 = min(int(math.floor(
                    (max(ys) - w.origin_y) / GRID_MM + 1e-9)), w.ny - 1)
                inside = set()
                for iy in range(iy0, iy1 + 1):
                    py = w.center_mm_y(iy)
                    xints = []
                    for k in range(len(pts)):
                        x1, y1 = pts[k]
                        x2, y2 = pts[(k + 1) % len(pts)]
                        if (y1 > py) != (y2 > py):
                            xints.append(x1 + (py - y1) * (x2 - x1)
                                         / (y2 - y1))
                    xints.sort()
                    for k2 in range(0, len(xints) - 1, 2):
                        xa, xb = xints[k2], xints[k2 + 1]
                        jx0 = max(int(math.ceil(
                            (xa - w.origin_x) / GRID_MM - 1e-9)), 0)
                        jx1 = min(int(math.floor(
                            (xb - w.origin_x) / GRID_MM + 1e-9)), w.nx - 1)
                        for ix in range(jx0, jx1 + 1):
                            inside.add((ix, iy))
                # margin 带=逐边 capsule 精确 raster（避免整集 Chebyshev
                # 膨胀的 ~0.2mm 过挡：首跑 radius 扩 4 仍 45 行端点全挡的
                # 根因核验=GND 填充膨胀过保守，DEV-E4-001 附注）
                cells = set(inside)
                for k in range(len(pts)):
                    x1, y1 = pts[k]
                    x2, y2 = pts[(k + 1) % len(pts)]
                    lo_x = min(x1, x2) - margin
                    hi_x = max(x1, x2) + margin
                    lo_y = min(y1, y2) - margin
                    hi_y = max(y1, y2) + margin
                    jx0 = max(int(math.ceil(
                        (lo_x - w.origin_x) / GRID_MM - 1e-9)), 0)
                    jx1 = min(int(math.floor(
                        (hi_x - w.origin_x) / GRID_MM + 1e-9)), w.nx - 1)
                    jy0 = max(int(math.ceil(
                        (lo_y - w.origin_y) / GRID_MM - 1e-9)), 0)
                    jy1 = min(int(math.floor(
                        (hi_y - w.origin_y) / GRID_MM + 1e-9)), w.ny - 1)
                    m2 = margin * margin
                    for ix in range(jx0, jx1 + 1):
                        px = w.center_mm_x(ix)
                        for iy in range(jy0, jy1 + 1):
                            py = w.center_mm_y(iy)
                            if _seg_point_dist2(px, py, x1, y1, x2,
                                                y2) < m2:
                                cells.add((ix, iy))
                per.setdefault(znet, {l: set()
                                      for l in range(len(self.copper))})
                per[znet].setdefault(li, set()).update(cells)


    def _margin_for(self, net, other_width):
        """新走线（0.2 假定半宽域）对既有 item 的 raster margin。"""
        try:
            clr = self.net_table.required_clearance(net, net)
        except Exception:
            clr = self._default_clearance()
        return clr + 0.2 / 2.0 + other_width / 2.0

    def blocked_for(self, net, protected=(), extra_nets=()):
        """行网视角阻挡图 {layer_idx: set(cells)}。

        - 排除本网与 protected（同批）铜；
        - extra_nets：T4 撕除网（其铜暂不计阻挡）；
        - 板边阻挡恒在。
        """
        per = self.per_net_cells()
        exempt = {net} | set(protected) | set(extra_nets)
        out = {li: set() for li in range(len(self.copper))}
        for n, layers in per.items():
            if n in exempt:
                continue
            for li, cells in layers.items():
                if cells:
                    out[li] |= cells
        return out

    # ------------------------------------------------------------ 端点

    def endpoint_cells(self, ep, blocked, allowed_layers):
        """端点 -> 候选 (cell, layer) 列表（snap 阶梯：最近可用格优先）。

        层候选：track=其层；pad=解析层或 pad 全铜层集（THT 全层）；
        via=跨层全层。层不在 allowed_layers 的剔除。
        """
        w = self.world
        cand_layers = []
        if ep["kind"] == "track" and ep["layer"]:
            cand_layers = [ep["layer"]]
        elif ep["kind"] == "pad":
            pads = self._find_pad(ep)
            if pads:
                cand_layers = [l for l in pads["layers"]
                               if l in w.layer_index]
            elif ep["layer"]:
                cand_layers = [ep["layer"]]
        elif ep["kind"] == "via":
            cand_layers = list(self.copper)
        if not cand_layers:
            cand_layers = [ep["layer"]] if ep["layer"] else list(self.copper)
        cand_layers = [l for l in cand_layers if l in w.layer_index]
        if not cand_layers:
            return []
        ix0 = w.cell_x(ep["x"])
        iy0 = w.cell_y(ep["y"])
        cands = []
        for lname in cand_layers:
            li = w.layer_index[lname]
            if li not in allowed_layers:
                continue
            for dx in range(-_SNAP_RADIUS_CELLS, _SNAP_RADIUS_CELLS + 1):
                for dy in range(-_SNAP_RADIUS_CELLS, _SNAP_RADIUS_CELLS + 1):
                    ix, iy = ix0 + dx, iy0 + dy
                    if not w.in_bounds(ix, iy):
                        continue
                    if (ix, iy) in blocked[li]:
                        continue
                    d2 = dx * dx + dy * dy
                    cands.append((0, d2, lname, ix, iy, None))
        cands.sort()
        return cands

    def net_components(self, net):
        """网铜连通分量（保守合并判据；惰性缓存）。

        判据：同层段端点重合（1e-6）/ 段-段真交 / via 跨度层上半径接触 /
        pad 包围盒内段端点（THT 全层）。保守方向：只在这些确证接触上
        合并（本表只用于挂接候选的分量限定，宁可少合并不多合并）。
        """
        cache = getattr(self, "_comp_cache", None)
        if cache is None:
            cache = self._comp_cache = {}
        if net in cache:
            return cache[net]
        segs = [i for i, s in enumerate(self.parsed["segments"])
                if str(s["net"]) == net]
        vias = [i for i, v in enumerate(self.parsed["vias"])
                if str(v["net"]) == net]
        pads = [i for i, p in enumerate(self.parsed["pads"])
                if str(p["net_id"]) == net]
        parent = {}

        def find(x):
            while parent.get(x, x) != x:
                parent[x] = parent.get(parent[x], parent[x])
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for i in segs + vias + pads:
            parent.setdefault(i, i)
        for a_i in range(len(segs)):
            for b_i in range(a_i + 1, len(segs)):
                sa = self.parsed["segments"][segs[a_i]]
                sb = self.parsed["segments"][segs[b_i]]
                if sa["layer"] != sb["layer"]:
                    continue
                touch = False
                for (x1, y1) in ((sa["x1"], sa["y1"]), (sa["x2"], sa["y2"])):
                    for (x2, y2) in ((sb["x1"], sb["y1"]),
                                     (sb["x2"], sb["y2"])):
                        if abs(x1 - x2) <= 1e-6 and abs(y1 - y2) <= 1e-6:
                            touch = True
                if not touch and _segments_cross(sa, sb):
                    touch = True
                if touch:
                    union(segs[a_i], segs[b_i])
        for vi in vias:
            v = self.parsed["vias"][vi]
            r = float(v["size"]) / 2.0
            for si in segs:
                s = self.parsed["segments"][si]
                if s["layer"] not in v["layers"]:
                    continue
                for (x1, y1) in ((s["x1"], s["y1"]), (s["x2"], s["y2"])):
                    d = math.hypot(x1 - v["x"], y1 - v["y"])
                    if d <= r + float(s["width"]) / 2.0 + 1e-9:
                        union(vi, si)
                        break
        for pi in pads:
            p = self.parsed["pads"][pi]
            hw, hh = _rotated_pad_half_extents(
                float(p["w_mm"]), float(p["h_mm"]),
                float(p["rotation_deg"] or 0.0))
            for si in segs:
                s = self.parsed["segments"][si]
                if s["layer"] not in p["layers"]:
                    continue
                for (x1, y1) in ((s["x1"], s["y1"]), (s["x2"], s["y2"])):
                    if (abs(x1 - p["x_mm"]) <= hw + 1e-9
                            and abs(y1 - p["y_mm"]) <= hh + 1e-9):
                        union(pi, si)
                        break
        seg_comp = {segs[i]: find(segs[i]) for i in range(len(segs))}
        comp_segments = {}
        for si, c in seg_comp.items():
            comp_segments.setdefault(c, []).append(si)
        out = {"seg_comp": seg_comp, "comp_segments": comp_segments}
        cache[net] = out
        return out

    def endpoint_component(self, net, ep):
        """端点 item 所在分量（段端点匹配 1e-4 / pad 包围盒接触反查）。"""
        comps = self.net_components(net)
        if ep.get("kind") == "track":
            for si, c in comps["seg_comp"].items():
                s = self.parsed["segments"][si]
                for (x1, y1) in ((s["x1"], s["y1"]), (s["x2"], s["y2"])):
                    if abs(x1 - ep["x"]) <= 1e-4 and abs(y1 - ep["y"]) <= 1e-4:
                        return c
            return None
        if ep.get("kind") == "pad":
            pad = self._find_pad(ep)
            if pad is None:
                return None
            hw, hh = _rotated_pad_half_extents(
                float(pad["w_mm"]), float(pad["h_mm"]),
                float(pad["rotation_deg"] or 0.0))
            for si, c in comps["seg_comp"].items():
                s = self.parsed["segments"][si]
                if s["layer"] not in pad["layers"]:
                    continue
                for (x1, y1) in ((s["x1"], s["y1"]), (s["x2"], s["y2"])):
                    if (abs(x1 - pad["x_mm"]) <= hw + 1e-9
                            and abs(y1 - pad["y_mm"]) <= hh + 1e-9):
                        return c
            return None
        return None

    def own_component_candidates(self, net, ep, blocked, allowed_layers,
                                 other_xy, cap=12):
        """本网组件全域挂接候选（DEV-E4-003 mechanics）。

        行端点 buried 在引脚场时 ring 内可能无可用格；本网铜（raster
        豁免=可走）延展全板——以组件上任意格为起点等价解决该行（同组件
        电学连通）。挂接点=格心到本网最近同层段的垂足（在本网中心线上
        =真实触摸连通）。候选按距对端端点排序（短路由优先），cap 12。
        """
        w = self.world
        cand_layers = []
        if ep["kind"] == "track" and ep["layer"]:
            cand_layers = [ep["layer"]]
        elif ep["kind"] == "pad":
            pads = self._find_pad(ep)
            if pads:
                cand_layers = [l for l in pads["layers"]
                               if l in w.layer_index]
            elif ep["layer"]:
                cand_layers = [ep["layer"]]
        elif ep["kind"] == "via":
            cand_layers = list(self.copper)
        if not cand_layers:
            cand_layers = [ep["layer"]] if ep["layer"] else list(self.copper)
        comp = self.endpoint_component(net, ep)
        if comp is None:
            return []
        comp_segs = [self.parsed["segments"][si] for si in
                     self.net_components(net)["comp_segments"].get(comp, [])]
        if not comp_segs:
            return []
        margin = 0.4  # 本网带（可走带；attach 垂足保证真实接触）
        out = []
        ox, oy = other_xy
        for lname in cand_layers:
            if lname not in w.layer_index:
                continue
            li = w.layer_index[lname]
            if li not in allowed_layers:
                continue
            cells = set()
            for s in comp_segs:
                if s["layer"] != lname:
                    continue
                lo_x = min(s["x1"], s["x2"]) - margin
                hi_x = max(s["x1"], s["x2"]) + margin
                lo_y = min(s["y1"], s["y2"]) - margin
                hi_y = max(s["y1"], s["y2"]) + margin
                jx0 = max(int(math.ceil(
                    (lo_x - w.origin_x) / GRID_MM - 1e-9)), 0)
                jx1 = min(int(math.floor(
                    (hi_x - w.origin_x) / GRID_MM + 1e-9)), w.nx - 1)
                jy0 = max(int(math.ceil(
                    (lo_y - w.origin_y) / GRID_MM - 1e-9)), 0)
                jy1 = min(int(math.floor(
                    (hi_y - w.origin_y) / GRID_MM + 1e-9)), w.ny - 1)
                m2 = margin * margin
                for ix in range(jx0, jx1 + 1):
                    px = w.center_mm_x(ix)
                    for iy in range(jy0, jy1 + 1):
                        py = w.center_mm_y(iy)
                        if _seg_point_dist2(px, py, s["x1"], s["y1"],
                                            s["x2"], s["y2"]) < m2:
                            cells.add((ix, iy))
            for (ix, iy) in cells:
                if not w.in_bounds(ix, iy):
                    continue
                cx, cy = w.center_mm_x(ix), w.center_mm_y(iy)
                att = self._projectonto_own_segments(comp_segs, lname,
                                                     cx, cy)
                if att is None:
                    continue
                d2o = (cx - ox) ** 2 + (cy - oy) ** 2
                out.append((1, d2o, lname, ix, iy, att))
        out.sort()
        return out[:cap]

    def _projectonto_own_segments(self, segs, layer, cx, cy):
        best, bd = None, None
        for s in segs:
            if str(s["layer"]) != layer:
                continue
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            if L2 <= 1e-18:
                t = 0.0
            else:
                t = ((cx - x1) * dx + (cy - y1) * dy) / L2
                t = max(0.0, min(1.0, t))
            px, py = x1 + t * dx, y1 + t * dy
            d2 = (cx - px) ** 2 + (cy - py) ** 2
            if bd is None or d2 < bd:
                best, bd = (px, py), d2
        return best

    def _projectonto_own_segment(self, net, layer, cx, cy):
        """(cx,cy) -> 本网同层最近段上垂足（无同层段=None）。"""
        best, bd = None, None
        for s in self.parsed["segments"]:
            if str(s["net"]) != net or str(s["layer"]) != layer:
                continue
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            if L2 <= 1e-18:
                t = 0.0
            else:
                t = ((cx - x1) * dx + (cy - y1) * dy) / L2
                t = max(0.0, min(1.0, t))
            px, py = x1 + t * dx, y1 + t * dy
            d2 = (cx - px) ** 2 + (cy - py) ** 2
            if bd is None or d2 < bd:
                best, bd = (px, py), d2
        return best

    def _find_pad(self, ep):
        """端点描述 ref/坐标 -> 解析产物中的 pad 记录（最近匹配）。"""
        if ep.get("ref"):
            for p in self.parsed["pads"]:
                if p["pad_id"] == ep["ref"]:
                    return p
        best, bd = None, None
        for p in self.parsed["pads"]:
            d2 = (p["x_mm"] - ep["x"]) ** 2 + (p["y_mm"] - ep["y"]) ** 2
            if bd is None or d2 < bd:
                best, bd = p, d2
        if best is not None and bd is not None and bd <= 0.04:
            return best
        return None



def _point_in_poly_margin(px, py, poly, margin):
    """点在多边形内（even-odd）或距边 < margin（保守：入 raster）。"""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xin:
                inside = not inside
        if _seg_point_dist2(px, py, x1, y1, x2, y2) < margin * margin:
            return True
    return inside


# ================================================================ 求解

def _layer_cost_fn(proj):
    model = ViaCostModel(list(proj.copper))

    def cost(la, lb):
        return model.cost_cells(proj.copper[la], proj.copper[lb], GRID_MM)
    return cost


def _merge_runs(path_steps):
    """A* steps -> [(layer_idx, [(ix, iy), ...])]（via 步为界拆段）。"""
    runs = []
    cur_layer = path_steps[0][2]
    cur_cells = [(path_steps[0][0], path_steps[0][1])]
    for (x, y, li, kind) in path_steps[1:]:
        if kind == "via":
            runs.append((cur_layer, cur_cells))
            cur_layer = li
            cur_cells = [(x, y)]
        else:
            if li != cur_layer:
                raise E4RevcError("internal: 层变无 via 步")
            if (x, y) != cur_cells[-1]:
                cur_cells.append((x, y))
    runs.append((cur_layer, cur_cells))
    return runs


def _compress_cells(cells):
    """格点序列 -> 折线顶点（共线压缩）。"""
    if len(cells) <= 2:
        return list(cells)
    pts = [cells[0]]
    for i in range(1, len(cells) - 1):
        dx1 = cells[i][0] - cells[i - 1][0]
        dy1 = cells[i][1] - cells[i - 1][1]
        dx2 = cells[i + 1][0] - cells[i][0]
        dy2 = cells[i + 1][1] - cells[i][1]
        if (dx1, dy1) != (dx2, dy2):
            pts.append(cells[i])
    pts.append(cells[-1])
    return pts


def route_row(proj, row, blocked=None, protected=(), layer_pref=None,
              waypoints_cells=None):
    """单行 A0 求解（给定阻挡图/层偏好/waypoint 走廊）。

    返回 dict：ok / reason / path / runs / vias_pos / search_nodes /
    start_cell / goal_cell / snapped。
    """
    from ..v4_1.solver2 import _astar2
    w = proj.world
    net = row["net"]
    if blocked is None:
        blocked = proj.blocked_for(net, protected=protected)
    allowed = [w.layer_index[l] for l in proj.copper]
    if layer_pref:
        pref_idx = [w.layer_index[l] for l in layer_pref
                    if l in w.layer_index]
        allowed = pref_idx or allowed
    allowed_sorted = sorted(set(allowed))
    ca = proj.endpoint_cells(row["a"], blocked, allowed_sorted)
    cb = proj.endpoint_cells(row["b"], blocked, allowed_sorted)
    own_a = proj.own_component_candidates(net, row["a"], blocked,
                                          allowed_sorted,
                                          (row["b"]["x"], row["b"]["y"]))
    own_b = proj.own_component_candidates(net, row["b"], blocked,
                                          allowed_sorted,
                                          (row["a"]["x"], row["a"]["y"]))
    cand_a = list(ca[:3]) + list(own_a[:4])
    cand_b = list(cb[:3]) + list(own_b[:4])
    if not cand_a or not cand_b:
        return {"ok": False, "reason": "endpoint_no_free_cell",
                "search_nodes": 0}
    cost = _layer_cost_fn(proj)
    best = None
    for cda in cand_a:
        (_pa, _da, la, ax, ay, atta) = cda
        for cdb in cand_b:
            (_pb, _db, lb, bx, by, attb) = cdb
            start = (ax, ay, w.layer_index[la])
            goal = (bx, by, w.layer_index[lb])
            if waypoints_cells:
                steps = []
                cur = start
                nodes = 0
                chain = [(bx, by)]
                okall = True
                for (wx, wy) in waypoints_cells:
                    seg, exp = _astar2(w, blocked, allowed_sorted, cur,
                                       (wx, wy, cur[2]), True, cost)
                    nodes += exp
                    if seg is None:
                        okall = False
                        break
                    steps.extend(seg if not steps else seg[1:])
                    cur = (seg[-1][0], seg[-1][1], seg[-1][2])
                if okall:
                    seg, exp = _astar2(w, blocked, allowed_sorted, cur,
                                       goal, False, cost)
                    nodes += exp
                    if seg is not None:
                        steps.extend(seg if not steps else seg[1:])
                        best = (steps, nodes, start, goal, atta, attb)
                        break
            else:
                seg, exp = _astar2(w, blocked, allowed_sorted, start,
                                   goal, False, cost)
                if seg is not None:
                    best = (seg, exp, start, goal, atta, attb)
                    break
        if best:
            break
    if best is None:
        return {"ok": False, "reason": "astar_unreachable",
                "search_nodes": 0}
    steps, nodes, start, goal, atta, attb = best
    runs = _merge_runs(steps)
    return {"ok": True, "reason": None, "runs": runs, "search_nodes": nodes,
            "start": start, "goal": goal,
            "attach_a": atta, "attach_b": attb,
            "snapped_a": [w.center_mm_x(start[0]), w.center_mm_y(start[1]),
                          proj.copper[start[2]]],
            "snapped_b": [w.center_mm_x(goal[0]), w.center_mm_y(goal[1]),
                          proj.copper[goal[2]]]}


def row_width(proj, net):
    """行网既有主导宽度（DRC 宽度域最安全口径）；无既有段=0.2。"""
    widths = [float(s["width"]) for s in proj.parsed["segments"]
              if str(s["net"]) == net]
    if not widths:
        return 0.2
    hist = {}
    for wv in widths:
        hist[round(wv, 4)] = hist.get(round(wv, 4), 0) + 1
    return sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def route_to_ops(proj, row, res):
    """A* 结果 -> KiCad ops（segment/via；端点真实坐标缝合）。

    返回 {ops: [...], segments_n, vias_n, length_mm}。
    """
    w = proj.world
    net = row["net"]
    width = row_width(proj, net)
    ops = []
    length_mm = 0.0
    runs = res["runs"]
    atta = res.get("attach_a") or [row["a"]["x"], row["a"]["y"]]
    attb = res.get("attach_b") or [row["b"]["x"], row["b"]["y"]]
    for k, (li, cells) in enumerate(runs):
        pts = _compress_cells(cells)
        poly = [[w.center_mm_x(ix), w.center_mm_y(iy)] for (ix, iy) in pts]
        if k == 0:
            poly[0] = list(atta)
        if k == len(runs) - 1:
            poly[-1] = list(attb)
        # 去重可能产生的零长首点（真实端点恰在格心）
        clean = [poly[0]]
        for p in poly[1:]:
            if abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) \
                    > 1e-9:
                clean.append(p)
        poly = clean
        if len(poly) == 1 and len(runs) == 1:
            # 退化同格桥：A/B 组件挂接带在同一格重叠且不同垂足——
            # 单段桥 atta->attb（同网微桥，预检+接触核验把关）
            if (abs(atta[0] - attb[0]) > 1e-6
                    or abs(atta[1] - attb[1]) > 1e-6):
                poly = [list(atta), list(attb)]
            else:
                continue
        for i in range(1, len(poly)):
            ops.append({
                "op": "segment", "net": net, "layer": proj.copper[li],
                "width": width,
                "start": [round(poly[i - 1][0], 6),
                          round(poly[i - 1][1], 6)],
                "end": [round(poly[i][0], 6), round(poly[i][1], 6)],
            })
            length_mm += ((poly[i][0] - poly[i - 1][0]) ** 2
                          + (poly[i][1] - poly[i - 1][1]) ** 2) ** 0.5
        if k < len(runs) - 1:
            nli = runs[k + 1][0]
            vx = w.center_mm_x(pts[-1][0])
            vy = w.center_mm_y(pts[-1][1])
            ops.append({
                "op": "via", "net": net,
                "at": [round(vx, 6), round(vy, 6)],
                "size": proj.new_via_size, "drill": _NEW_VIA_DRILL,
                "layers": [proj.copper[min(li, nli)],
                           proj.copper[max(li, nli)]],
            })
    return {"ops": ops, "segments_n": sum(1 for o in ops
                                          if o["op"] == "segment"),
            "vias_n": sum(1 for o in ops if o["op"] == "via"),
            "length_mm": round(length_mm, 6), "width": width}


# ================================================================ 预检

def _ops_bbox(ops, pad=0.35):
    xs, ys = [], []
    for o in ops:
        if o["op"] == "segment":
            xs.extend([o["start"][0], o["end"][0]])
            ys.extend([o["start"][1], o["end"][1]])
        else:
            xs.append(o["at"][0])
            ys.append(o["at"][1])
    if not xs:
        return None
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _item_bbox(it):
    core = it.core
    xs = [p[0] for p in core]
    ys = [p[1] for p in core]
    r = it.radius
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)


def _bbox_gap(a, b):
    gx = max(a[0] - b[2], b[0] - a[2], 0.0)
    gy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return (gx * gx + gy * gy) ** 0.5


def precheck_ops(parsed, net_table, ops, protected=(), band_mm=0.01):
    """候选 ops -> v4_1 预检（近场 bbox 预过滤加速；判定集不变）。

    返回 {verdict, violations[], blocked_reasons[], min_clear}。
    verdict: clean / band / violation / blocked。
    """
    from .geometry import GeomItem, GeomError
    bb = _ops_bbox(ops)
    if bb is None:
        return {"verdict": "blocked", "violations": [],
                "blocked_reasons": ["ops 为空"], "min_clear": None}
    cand_layers = set()
    for o in ops:
        if o["op"] == "segment":
            cand_layers.add(o["layer"])
        else:
            cand_layers.update(o["layers"])
    near_items = []
    for it in build_geom_items(parsed):
        if it.net in protected:
            continue
        if not (it.layers & cand_layers):
            continue
        ib = _item_bbox(it)
        if _bbox_gap(bb, ib) > band_mm + 1.0:
            continue  # 候选对角半径 <=0.35+item 半径已计入 1.0 缓冲
        near_items.append(it)
    violations = []
    blocked = []
    min_clear = None
    for oi, o in enumerate(ops):
        try:
            if o["op"] == "segment":
                cand = GeomItem.from_track(
                    o["net"], o["layer"], o["width"],
                    o["start"][0], o["start"][1], o["end"][0], o["end"][1])
            else:
                cand = GeomItem.from_via(
                    o["net"], o["size"], o["layers"],
                    o["at"][0], o["at"][1])
        except GeomError as exc:
            blocked.append(str(exc))
            continue
        for it in near_items:
            if it.net == o["net"] or it.net in protected:
                continue
            if not (cand.layers & it.layers):
                continue
            res = clearance_between_items(cand, it)
            if res is None:
                continue
            pred = res["clearance_mm"]
            required = net_table.required_clearance(o["net"], it.net)
            if min_clear is None or pred < min_clear:
                min_clear = pred
            hard = res["overlap"] or pred < required - 1e-12
            band = (not hard) and pred < required + band_mm - 1e-12
            if hard or band:
                violations.append({
                    "op_index": oi, "op": o["op"],
                    "item_kind": it.kind,
                    "item_ref": it.src.get("uuid") or it.src.get("pad_id"),
                    "item_net": it.net,
                    "pred_clearance_mm": None if res["overlap"]
                    else round(pred, 6),
                    "required_mm": round(required, 6),
                    "overlap": res["overlap"],
                    "flag_class": "hard_violation" if hard
                    else "conservative_band",
                })
    if blocked:
        return {"verdict": "blocked", "violations": violations,
                "blocked_reasons": blocked, "min_clear": min_clear}
    hard_n = sum(1 for v in violations
                 if v["flag_class"] == "hard_violation")
    return {"verdict": "violation" if hard_n else (
        "band" if violations else "clean"),
        "violations": violations, "blocked_reasons": [],
        "min_clear": None if min_clear is None else round(min_clear, 6)}


# ================================================================ 文本手术

def _e4_uuid(payload):
    h = hashlib.sha256(b"pcbflow-e4:" + payload.encode("utf-8")).hexdigest()
    return "-".join((h[:8], h[8:12], h[12:16], h[16:20], h[20:32]))


def _fmt(v):
    s = ("%.6f" % float(v)).rstrip("0")
    return s + "0" if s.endswith(".") else s


def _via_kind(layers, copper):
    order = [copper.index(l) for l in layers if l in copper]
    if not order:
        return ""
    lo, hi = min(order), max(order)
    if lo == 0 and hi == len(copper) - 1:
        return ""            # 贯通
    outer = {0, len(copper) - 1}
    return "blind" if (lo in outer or hi in outer) else "buried"


def emit_ops(ops, copper, eol="\r\n"):
    """ops -> KiCad 节点文本（CRLF 板口径；uuid 内容派生）。"""
    out = []
    for o in ops:
        if o["op"] == "segment":
            payload = "S|%s|%s|%s|%s,%s,%s,%s" % (
                o["net"], o["layer"], _fmt(o["width"]),
                _fmt(o["start"][0]), _fmt(o["start"][1]),
                _fmt(o["end"][0]), _fmt(o["end"][1]))
            out.append(eol.join([
                "\t(segment",
                "\t\t(start %s %s)" % (_fmt(o["start"][0]),
                                       _fmt(o["start"][1])),
                "\t\t(end %s %s)" % (_fmt(o["end"][0]), _fmt(o["end"][1])),
                "\t\t(width %s)" % _fmt(o["width"]),
                '\t\t(layer "%s")' % o["layer"],
                '\t\t(net "%s")' % o["net"],
                '\t\t(uuid "%s")' % _e4_uuid(payload),
                "\t)",
            ]) + eol)
        else:
            kind = _via_kind(o["layers"], copper)
            head = "\t(via %s" % kind if kind else "\t(via"
            payload = "V|%s|%s|%s,%s,%s,%s" % (
                o["net"], _fmt(o["size"]), _fmt(o["at"][0]),
                _fmt(o["at"][1]), o["layers"][0], o["layers"][1])
            out.append(eol.join([
                head,
                "\t\t(at %s %s)" % (_fmt(o["at"][0]), _fmt(o["at"][1])),
                "\t\t(size %s)" % _fmt(o["size"]),
                "\t\t(drill %s)" % _fmt(o["drill"]),
                '\t\t(layers "%s" "%s")' % (o["layers"][0],
                                            o["layers"][1]),
                '\t\t(net "%s")' % o["net"],
                '\t\t(uuid "%s")' % _e4_uuid(payload),
                "\t)",
            ]) + eol)
    return "".join(out)


def apply_ops_to_text(board_text, ops, remove_segment_uuids=()):
    """板文本 + 新增 ops（+ 可选段删除）-> 新板文本（splice 手术）。"""
    from ..p3_revc_staging import _top_spans
    from ..board_writer import dominant_eol
    eol = dominant_eol(board_text)
    text = board_text
    if remove_segment_uuids:
        kill = set(remove_segment_uuids)
        spans = []
        for (a, b) in _top_spans(text, "segment"):
            m = re.search(r'\(uuid\s+"([^"]+)"\)', text[a:b])
            if m and m.group(1) in kill:
                spans.append((a, b))
        for (a, b) in sorted(spans, reverse=True):
            text = text[:a] + text[b:]
    nodes = emit_ops(ops, _copper_from_text(text), eol=eol)
    stripped = text.rstrip()
    if not stripped.endswith(")"):
        raise E4RevcError("板文本非预期结尾（缺根闭合括号）")
    tail = text[len(stripped):]
    return stripped[:-1] + nodes + ")" + tail


def _copper_from_text(text):
    """板文本铜层表（栈序）——复用 board_parse 的层序提取。"""
    parsed = parse_board_text(text)
    return list(parsed["copper_layers"])


def apply_ops_to_text(board_text, ops, remove_segment_uuids=(),
                      remove_via_uuids=()):
    """板文本 + 新增 ops（+ 可选段/via 删除）-> 新板文本（splice 手术）。"""
    from ..p3_revc_staging import _top_spans
    from ..board_writer import dominant_eol
    eol = dominant_eol(board_text)
    text = board_text
    for tag, kills in (("segment", set(remove_segment_uuids)),
                       ("via", set(remove_via_uuids))):
        if not kills:
            continue
        spans = []
        for (a, b) in _top_spans(text, tag):
            m = re.search(r'\(uuid\s+"([^"]+)"\)', text[a:b])
            if m and m.group(1) in kills:
                spans.append((a, b))
        for (a, b) in sorted(spans, reverse=True):
            text = text[:a] + text[b:]
    nodes = emit_ops(ops, _copper_from_text(text), eol=eol)
    stripped = text.rstrip()
    if not stripped.endswith(")"):
        raise E4RevcError("板文本非预期结尾（缺根闭合括号）")
    tail = text[len(stripped):]
    return stripped[:-1] + nodes + ")" + tail


# ================================================================ 网名映射

def net_names_from_text(text):
    """顶层 (net N "NAME") 节点 -> {N: NAME}（KiCad 10 名字权威）。"""
    out = {}
    for m in re.finditer(r'\(net\s+(\d+)\s+"([^"]*)"\)', text):
        out[m.group(1)] = m.group(2)
    return out


def parsed_with_names(parsed, name_map):
    """解析产物 net 字段（编号）-> 网名（类表/emit 同一语义域）。"""
    def nm(n):
        return name_map.get(str(n), str(n))
    segs = [dict(s, net=nm(s["net"])) for s in parsed["segments"]]
    vias = [dict(v, net=nm(v["net"])) for v in parsed["vias"]]
    pads = [dict(p, net_id=nm(p["net_id"])) for p in parsed["pads"]]
    return dict(parsed, segments=segs, vias=vias, pads=pads)


# ================================================================ rip-up 梯

_LAYER_PREF_LADDER = [
    None,
    ["In1.Cu", "In2.Cu"],
    ["In2.Cu"],
    ["F.Cu"],
    ["B.Cu"],
]


def corridor_waypoints(proj, row, side):
    """T5 走廊 waypoint（格点 cell）：北/南绕行（中点横向偏移）。"""
    w = proj.world
    mx = (row["a"]["x"] + row["b"]["x"]) / 2.0
    my = (row["a"]["y"] + row["b"]["y"]) / 2.0
    cy = (proj.bbox[1] + proj.bbox[3]) / 2.0
    if side == "north":
        wy = proj.bbox[1] + 2.0 + (0.35 * abs(my - proj.bbox[1]))
    else:
        wy = proj.bbox[3] - 2.0 - (0.35 * abs(proj.bbox[3] - my))
    del cy
    return (w.cell_x(mx), w.cell_y(wy))


def _net_chains_2terminal(proj, net):
    """网铜（segments+vias）连通分量 -> [(A_xy_layer, B_xy_layer)]。

    仅返回恰 2 端点的分量（路径形）；多端点/环网返回空（不可安全替换，
    如实跳过登记）。端点=度 1 的节点；坐标分层取该网铜所在层。
    """
    segs = [s for s in proj.parsed["segments"] if str(s["net"]) == net]
    vias = [v for v in proj.parsed["vias"] if str(v["net"]) == net]
    adj = {}

    def _add(p, q):
        adj.setdefault(p, set()).add(q)
        adj.setdefault(q, set()).add(p)

    for s in segs:
        a = (round(s["x1"], 4), round(s["y1"], 4), s["layer"])
        b = (round(s["x2"], 4), round(s["y2"], 4), s["layer"])
        _add(a, b)
        # via 触点（同坐标异层）连接
        for v in vias:
            vp = (round(v["x"], 4), round(v["y"], 4))
            if (round(s["x1"], 4), round(s["y1"], 4)) == vp[:2] or \
                    (round(s["x2"], 4), round(s["y2"], 4)) == vp[:2]:
                for l in v["layers"]:
                    _add(a, (vp[0], vp[1], l))
                    _add(b, (vp[0], vp[1], l))
    for v in vias:
        vp = (round(v["x"], 4), round(v["y"], 4))
        for i, l1 in enumerate(v["layers"]):
            for l2 in v["layers"][i + 1:]:
                _add((vp[0], vp[1], l1), (vp[0], vp[1], l2))
    # 连通分量
    seen = set()
    comps = []
    for node in adj:
        if node in seen:
            continue
        stack, comp = [node], set()
        while stack:
            cur = stack.pop()
            if cur in comp:
                continue
            comp.add(cur)
            for nb in adj[cur]:
                if nb not in comp:
                    stack.append(nb)
        seen |= comp
        comps.append(comp)
    out = []
    for comp in comps:
        terms = [n for n in comp if len(adj[n]) == 1]
        if len(terms) == 2:
            out.append((terms[0], terms[1]))
    return out


def _ops_cells(proj, ops):
    """ops -> 附加阻挡格（T4 恢复布线时新铜互避）。"""
    w = proj.world
    out = {li: set() for li in range(len(proj.copper))}
    for o in ops:
        if o["op"] == "segment":
            li = w.layer_index[o["layer"]]
            margin = 0.2 / 2.0 + float(o["width"]) / 2.0 + 0.05
            x1, y1 = o["start"]
            x2, y2 = o["end"]
            lo_x, hi_x = min(x1, x2) - margin, max(x1, x2) + margin
            lo_y, hi_y = min(y1, y2) - margin, max(y1, y2) + margin
            ix0 = max(int(math.ceil((lo_x - w.origin_x) / GRID_MM - 1e-9)), 0)
            ix1 = min(int(math.floor((hi_x - w.origin_x) / GRID_MM + 1e-9)),
                      w.nx - 1)
            iy0 = max(int(math.ceil((lo_y - w.origin_y) / GRID_MM - 1e-9)), 0)
            iy1 = min(int(math.floor((hi_y - w.origin_y) / GRID_MM + 1e-9)),
                      w.ny - 1)
            m2 = margin * margin
            for ix in range(ix0, ix1 + 1):
                px = w.center_mm_x(ix)
                for iy in range(iy0, iy1 + 1):
                    py = w.center_mm_y(iy)
                    if _seg_point_dist2(px, py, x1, y1, x2, y2) < m2:
                        out[li].add((ix, iy))
        else:
            r = float(o["size"]) / 2.0 + 0.15
            ix, iy = w.cell_x(o["at"][0]), w.cell_y(o["at"][1])
            rad = int(math.ceil(r / GRID_MM))
            for lname in o["layers"]:
                li = w.layer_index[lname]
                for dx in range(-rad, rad + 1):
                    for dy in range(-rad, rad + 1):
                        cx = w.center_mm_x(ix + dx)
                        cy = w.center_mm_y(iy + dy)
                        if (cx - o["at"][0]) ** 2 + (cy - o["at"][1]) ** 2 \
                                < r * r:
                            out[li].add((ix + dx, iy + dy))
    return out


def blocking_nets(proj, row, top_k=_RIPUP_MAX_NETS):
    """行直连走廊上的阻挡归因：沿线采样阻挡格 -> 最近既有铜网 top-K。"""
    w = proj.world
    blocked = proj.blocked_for(row["net"])
    per = proj.per_net_cells()
    samples = []
    ax, ay, bx, by = row["a"]["x"], row["a"]["y"], row["b"]["x"], row["b"]["y"]
    n_steps = max(8, int(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 / 0.5))
    for i in range(n_steps + 1):
        t = i / n_steps
        x, y = ax + t * (bx - ax), ay + t * (by - ay)
        ix, iy = w.cell_x(x), w.cell_y(y)
        for li in range(len(proj.copper)):
            if (ix, iy) in blocked[li]:
                samples.append((ix, iy, li))
    if not samples:
        return []
    owner = {}
    for net, layers in per.items():
        if net == "__edge__":
            continue
        for li, cells in layers.items():
            for c in cells:
                owner[(c[0], c[1], li)] = net
    hist = {}
    for s in samples:
        n = owner.get(s)
        if n is not None and n != row["net"]:
            hist[n] = hist.get(n, 0) + 1
    ranked = sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))
    return [n for (n, _c) in ranked[:top_k]]



def _segments_cross(sa, sb):
    """两段真交（proper crossing；共享端点情形由调用侧端点判据覆盖）。"""
    def _o(p, q, r):
        return ((r[1] - p[1]) * (q[0] - p[0])
                - (r[0] - p[0]) * (q[1] - p[1]))
    p1, p2 = (sa["x1"], sa["y1"]), (sa["x2"], sa["y2"])
    q1, q2 = (sb["x1"], sb["y1"]), (sb["x2"], sb["y2"])
    o1, o2 = _o(p1, p2, q1), _o(p1, p2, q2)
    o3, o4 = _o(q1, q2, p1), _o(q1, q2, p2)
    if o1 * o2 < -1e-12 and o3 * o4 < -1e-12:
        return True
    return False


def _verify_real_contact(proj, net, ops):
    """ops 两端真实电学接触核验（诚实性门，DEV-E4-003 附注）。

    attach 点必须真实触摸本网铜：段端点到本网同层段中心线距离 <=
    (两侧半宽)（重叠=连通）；或落本网 pad 包围盒（同层）；或 via 对其
    跨度每层在本网铜 within via 半径+w_own/2。核验不过=候选弃用
    （raster 格心贴近 != 电学接触）。
    """
    if not ops:
        return False, "no_ops"
    first = ops[0]
    last = ops[-1]
    w_new = float(next((o["width"] for o in ops if o["op"] == "segment"),
                       0.2))

    def _seg_ok(pt, layer):
        px, py = pt
        for s in proj.parsed["segments"]:
            if str(s["net"]) != net or str(s["layer"]) != layer:
                continue
            d = math.sqrt(_seg_point_dist2(px, py, s["x1"], s["y1"],
                                           s["x2"], s["y2"]))
            if d <= (float(s["width"]) + w_new) / 2.0 + 1e-9:
                return True
        for p in proj.parsed["pads"]:
            if str(p["net_id"]) != net or layer not in p["layers"]:
                continue
            hw, hh = _rotated_pad_half_extents(
                float(p["w_mm"]), float(p["h_mm"]),
                float(p["rotation_deg"] or 0.0))
            if (abs(px - p["x_mm"]) <= hw + w_new / 2.0 + 1e-9
                    and abs(py - p["y_mm"]) <= hh + w_new / 2.0 + 1e-9):
                return True
        return False

    def _via_ok(o):
        r = float(o["size"]) / 2.0
        for lname in o["layers"]:
            hit = False
            for s in proj.parsed["segments"]:
                if str(s["net"]) != net or str(s["layer"]) != lname:
                    continue
                d = math.sqrt(_seg_point_dist2(
                    o["at"][0], o["at"][1], s["x1"], s["y1"],
                    s["x2"], s["y2"]))
                if d <= r + float(s["width"]) / 2.0 + 1e-9:
                    hit = True
                    break
            if not hit:
                for p in proj.parsed["pads"]:
                    if str(p["net_id"]) != net or lname not in p["layers"]:
                        continue
                    hw, hh = _rotated_pad_half_extents(
                        float(p["w_mm"]), float(p["h_mm"]),
                        float(p["rotation_deg"] or 0.0))
                    if (abs(o["at"][0] - p["x_mm"]) <= hw + r + 1e-9
                            and abs(o["at"][1] - p["y_mm"]) <= hh + r
                            + 1e-9):
                        hit = True
                        break
            if not hit:
                for v in proj.parsed["vias"]:
                    if str(v["net"]) != net or lname not in v["layers"]:
                        continue
                    if math.hypot(o["at"][0] - v["x"],
                                  o["at"][1] - v["y"])                             <= r + float(v["size"]) / 2.0 + 1e-9:
                        hit = True
                        break
            if not hit:
                return False
        return True

    # ---- 首端 ----
    if first["op"] == "segment":
        if not _seg_ok(first["start"], first["layer"]):
            return False, "end_a_no_real_contact"
    else:
        if not _via_ok(first):
            return False, "end_a_via_no_contact"
    # ---- 末端 ----
    if last["op"] == "segment":
        if not _seg_ok(last["end"], last["layer"]):
            return False, "end_b_no_real_contact"
    else:
        if not _via_ok(last):
            return False, "end_b_via_no_contact"
    return True, None


def _try_attempt(proj, row, protected, parsed_named, blocked, layer_pref,
                 waypoints_cells=None, extra_blocked=None):
    """一次尝试：route -> ops -> 预检。返回 (status, payload)。"""
    if extra_blocked:
        merged = {li: set(blocked.get(li, set())) | extra_blocked.get(li, set())
                  for li in range(len(proj.copper))}
        blocked = merged
    res = route_row(proj, row, blocked=blocked, protected=protected,
                    layer_pref=layer_pref, waypoints_cells=waypoints_cells)
    if not res["ok"]:
        return "search_fail", {"reason": res["reason"]}
    ops_pack = route_to_ops(proj, row, res)
    ok_contact, contact_reason = _verify_real_contact(proj, row["net"],
                                                      ops_pack["ops"])
    if not ok_contact:
        return "precheck_reject", {
            "reason": contact_reason,
            "ops": ops_pack["ops"], "segments_n": ops_pack["segments_n"],
            "vias_n": ops_pack["vias_n"],
            "length_mm": ops_pack["length_mm"], "width": ops_pack["width"],
            "precheck": {"verdict": "no_real_contact", "min_clear": None,
                         "hard_n": 0, "band_n": 0, "violations": []},
            "snapped": [res["snapped_a"], res["snapped_b"]],
            "search_nodes": res["search_nodes"]}
    pc = precheck_ops(parsed_named, proj.net_table, ops_pack["ops"],
                      protected=protected)
    rec = {
        "ops": ops_pack["ops"], "segments_n": ops_pack["segments_n"],
        "vias_n": ops_pack["vias_n"], "length_mm": ops_pack["length_mm"],
        "width": ops_pack["width"], "precheck": {
            "verdict": pc["verdict"],
            "min_clear": pc["min_clear"],
            "hard_n": sum(1 for v in pc["violations"]
                          if v["flag_class"] == "hard_violation"),
            "band_n": sum(1 for v in pc["violations"]
                          if v["flag_class"] == "conservative_band"),
            "violations": pc["violations"][:12],
        },
        "snapped": [res["snapped_a"], res["snapped_b"]],
        "search_nodes": res["search_nodes"],
    }
    if pc["verdict"] in ("clean", "band"):
        return "accept", rec
    return "precheck_reject", rec


def row_ladder_route(proj, row, protected=(), parsed_named=None,
                     ledger=None):
    """行级 rip-up 梯（A0 -> T3 -> T5 -> T4；T1/T2 为批级由编排侧执行）。

    返回 {status, accepted, trail}：status=committed_candidate /
    no_candidate。trail 逐级尝试与结果（入 ripup-ledger）。
    """
    if parsed_named is None:
        parsed_named = proj.parsed
    net = row["net"]
    blocked = proj.blocked_for(net, protected=protected)
    trail = []

    def _log(level, detail):
        trail.append({"level": level, "detail": detail})

    # ---- A0 + T3 局部换层 ----
    for pref in _LAYER_PREF_LADDER:
        lvl = "A0" if pref is None else "T3"
        status, payload = _try_attempt(proj, row, protected, parsed_named,
                                       blocked, pref)
        _log(lvl, {"layer_pref": pref, "status": status,
                   "reason": payload.get("reason"),
                   "precheck": payload.get("precheck",
                                           {}).get("verdict")
                   if isinstance(payload.get("precheck"), dict) else None})
        if status == "accept":
            return {"status": "committed_candidate", "accepted": payload,
                    "trail": trail}
    # ---- T5 走廊重分配 ----
    for side in ("north", "south"):
        wp = corridor_waypoints(proj, row, side)
        status, payload = _try_attempt(proj, row, protected, parsed_named,
                                       blocked, None, waypoints_cells=[wp])
        _log("T5", {"side": side, "wp_cells": list(wp), "status": status,
                    "reason": payload.get("reason")})
        if status == "accept":
            return {"status": "committed_candidate", "accepted": payload,
                    "trail": trail}
    # ---- T4 局部 rip-up ----
    nets = blocking_nets(proj, row)
    _log("T4", {"trigger": "A0/T3/T5 穷尽仍 fail", "blocking_nets": nets})
    for rn in nets:
        chains = _net_chains_2terminal(proj, rn)
        if not chains:
            _log("T4", {"net": rn, "result": "skip_no_2terminal_chain"})
            continue
        rip_blocked = proj.blocked_for(net, protected=protected,
                                       extra_nets=[rn])
        status, payload = _try_attempt(proj, row, protected, parsed_named,
                                       rip_blocked, None)
        if status != "accept":
            _log("T4", {"net": rn, "result": "row_still_fail",
                        "reason": payload.get("reason")})
            continue
        # 恢复重布：被撕网各链在（行新铜已阻挡）的图上重路由
        extra = _ops_cells(proj, payload["ops"])
        restore_ops = []
        ok_all = True
        parsed_minus = {
            "copper_layers": proj.parsed["copper_layers"],
            "segments": [s for s in parsed_named["segments"]
                         if s["net"] != rn],
            "vias": [v for v in parsed_named["vias"] if v["net"] != rn],
            "pads": parsed_named["pads"],
            "unsupported_items": proj.parsed["unsupported_items"],
            "stats": {},
            "parser": proj.parsed["parser"],
        }
        for (ta, tb) in chains:
            frow = {"net": rn,
                    "a": {"kind": "track", "layer": ta[2], "ref": None,
                          "x": ta[0], "y": ta[1], "desc": "ripup-restore"},
                    "b": {"kind": "track", "layer": tb[2], "ref": None,
                          "x": tb[0], "y": tb[1], "desc": "ripup-restore"}}
            rb = proj.blocked_for(rn, protected=protected,
                                  extra_nets=[rn])
            for li in rb:
                rb[li] |= extra.get(li, set())
            st2, pay2 = _try_attempt(proj, frow, protected, parsed_minus,
                                     rb, None)
            if st2 != "accept":
                ok_all = False
                _log("T4", {"net": rn, "result": "restore_fail",
                            "chain": [list(ta), list(tb)],
                            "reason": pay2.get("reason")})
                break
            restore_ops.extend(pay2["ops"])
        if not ok_all:
            continue
        combined_ops = payload["ops"] + restore_ops
        pc = precheck_ops(parsed_minus, proj.net_table, combined_ops,
                          protected=protected)
        if pc["verdict"] not in ("clean", "band"):
            _log("T4", {"net": rn, "result": "combined_precheck_reject",
                        "verdict": pc["verdict"]})
            continue
        removed_seg_uuids = [s["uuid"] for s in parsed_named["segments"]
                             if s["net"] == rn]
        removed_via_uuids = [v["uuid"] for v in parsed_named["vias"]
                             if v["net"] == rn]
        _log("T4", {"net": rn, "result": "accept",
                    "restore_chains": len(chains),
                    "removed_segments": len(removed_seg_uuids),
                    "removed_vias": len(removed_via_uuids)})
        payload = dict(payload)
        payload["ops"] = combined_ops
        payload["segments_n"] = sum(1 for o in combined_ops
                                    if o["op"] == "segment")
        payload["vias_n"] = sum(1 for o in combined_ops
                                if o["op"] == "via")
        payload["ripup"] = {"net": rn}
        return {"status": "committed_candidate", "accepted": payload,
                "trail": trail, "remove_segment_uuids": removed_seg_uuids,
                "remove_via_uuids": removed_via_uuids}
    if ledger is not None:
        ledger.append({"row_id": row.get("row_id"), "net": net,
                       "trail": trail})
    return {"status": "no_candidate", "accepted": None, "trail": trail}


# ================================================================ 编排 CLI

_E4_DIR_DEFAULT = "out/v4.1-engineering/e4"


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def _load_json(path):
    import json
    return json.loads(_read(path).decode("utf-8"))


def _progress_path(e4_dir):
    import pathlib
    return pathlib.Path(e4_dir) / "progress.json"


def _progress_update(e4_dir, mutate):
    """progress.json 断点状态机（读-改-写，canonical）。"""
    import json
    import pathlib
    p = _progress_path(e4_dir)
    if p.is_file():
        obj = _load_json(str(p))
    else:
        obj = {"schema": "pcbflow.v4_1.e4-progress/1",
               "declared_date": DECLARED_DATE, "ladder_level": "L1",
               "batches": {}, "rows": {}, "token_ledger": []}
    mutate(obj)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(p, obj)


def _staging_paths(e4_dir):
    import pathlib
    st = pathlib.Path(e4_dir) / "l2-batches" / "staging"
    return st, st / "revc.kicad_pcb", st / "revc.kicad_pro"


def _net_table_for(board_text, pro_path):
    pro_obj = None
    if pro_path is not None:
        try:
            pro_obj = _load_json(str(pro_path))
        except Exception:
            pro_obj = None
    return load_netclasses(board_text=board_text, kicad_pro_obj=pro_obj)


def op_stage_init(e4_dir, src_pcb, src_pro):
    """staging 快照副本建立（零 live 写：只读源，写 staging）。"""
    import pathlib
    st, pcb, pro = _staging_paths(e4_dir)
    st.mkdir(parents=True, exist_ok=True)
    data = _read(src_pcb)
    prodata = _read(src_pro)
    _write(str(pcb), data)
    _write(str(pro), prodata)
    manifest = {
        "schema": "pcbflow.v4_1.e4-staging/1",
        "declared_date": DECLARED_DATE,
        "src_pcb": str(src_pcb), "src_pro": str(src_pro),
        "board_sha256": _sha_bytes(data),
        "pro_sha256": _sha_bytes(prodata),
        "board_bytes": len(data),
        "zero_live_write": "源文件只读（本 op 只写 staging）",
    }
    write_canonical_json(st / "stage-manifest.json", manifest)
    _progress_update(e4_dir, lambda o: o.update(
        {"staging_board_sha256": manifest["board_sha256"],
         "staging_ready": True}))
    return manifest


def op_rows(e4_dir, drc_error_json, level="L2", max_nets_per_batch=10):
    """基线 DRC -> 行集+批计划（rows.json；progress 更新）。"""
    import pathlib
    drc = _load_json(drc_error_json)
    if level == "L3":
        # L3=全板只报告：GND/zone 网行一并入行集（prereg l3.scope）；
        # L2 已 committed 行剔除（防重复落铜——同内容 uuid 重复节点）
        import pathlib as _pl
        done_sigs = set()
        for cand in _pl.Path(e4_dir).glob("l2-batches/batch-*/"
                                          "candidates.json"):
            try:
                cj = _load_json(str(cand))
            except Exception:
                continue
            rec = _load_json(str(cand.parent / "batch-record.json"))                 if (cand.parent / "batch-record.json").is_file() else None
            if rec is not None and rec.get("verdict") == "commit":
                for c in cj.get("candidates", []):
                    done_sigs.add(c["row_signature"])
        rows, dropped = derive_rows(drc, exclude_nets=())
        for r in rows:
            r["class"] = "required"
        before = len(rows)
        rows = [r for r in rows if r["row_signature"] not in done_sigs]
        dropped.append({"reason": "l2_committed_excluded",
                        "count": before - len(rows)})
    else:
        rows, dropped = derive_rows(drc)
    required = [r for r in rows if r["class"] == "required"]
    excluded = [r for r in rows if r["class"] == "excluded_gnd"]
    nets = sorted({r["net"] for r in required})
    batches = []
    for i in range(0, len(nets), max_nets_per_batch):
        batches.append({"batch": "batch-%02d" % (len(batches) + 1),
                        "nets": nets[i:i + max_nets_per_batch]})
    out = {
        "schema": "pcbflow.v4_1.e4-rows/1",
        "declared_date": DECLARED_DATE,
        "level": level,
        "drc_source": str(drc_error_json),
        "required_row_count": len(required),
        "excluded_gnd_row_count": len(excluded),
        "dropped_row_count": len(dropped),
        "required_net_count": len(nets),
        "taskbook_ref": {
            "61_rows_note": "任务书 61=F3 代 residual-certs 信号行分母；"
                            "本行集=staging 基线 DRC 实测（差异登记 prereg）",
        },
        "rows": [{k: r[k] for k in ("row_id", "net", "class", "a", "b",
                                    "row_signature")} for r in rows],
        "dropped": dropped,
        "batches": batches,
    }
    p = pathlib.Path(e4_dir) / ("l3-rows.json" if level == "L3"
                                else "rows.json")
    write_canonical_json(p, out)

    def _mut(o):
        o.setdefault("levels", {})[level] = {
            "rows_total": len(rows),
            "required": len(required),
            "excluded_gnd": len(excluded),
            "batches": [b["batch"] for b in batches],
        }
    _progress_update(e4_dir, _mut)
    return out


def _batch_dir(e4_dir, batch, level="L2"):
    import pathlib
    d = pathlib.Path(e4_dir) / ("l3-batches" if level == "L3"
                                 else "l2-batches") / batch
    d.mkdir(parents=True, exist_ok=True)
    return d


def _plan_rows_for_batch(rows_obj, batch, reverse=False):
    nets = None
    for b in rows_obj["batches"]:
        if b["batch"] == batch:
            nets = list(b["nets"])
    if nets is None:
        raise E4RevcError("batch 不在 rows.json: %r" % batch)
    sel = [r for r in rows_obj["rows"]
           if r["net"] in nets and r["class"] == "required"]
    if reverse:
        nets = nets[::-1]
    order = {n: i for i, n in enumerate(nets)}
    sel.sort(key=lambda r: (order[r["net"]], r["row_id"]))
    return nets, sel


def op_batch_plan(e4_dir, batch, reverse=False, level="L2"):
    """批候选生成（A0/T3/T5/T4 梯；预检；candidates.json+梯台账）。"""
    import pathlib
    e4 = pathlib.Path(e4_dir)
    rows_obj = _load_json(str(e4 / ("l3-rows.json" if level == "L3"
                                    else "rows.json")))
    nets, sel = _plan_rows_for_batch(rows_obj, batch, reverse=reverse)
    st, pcb, pro = _staging_paths(e4_dir)
    text = _read(str(pcb)).decode("utf-8")
    name_map = net_names_from_text(text)
    table = _net_table_for(text, pro)
    try:
        proj = RevCProjection(text, net_table=table)
        projection_error = None
    except E4RevcError as e:
        # SEC-A-07 修复（REPAIR-P3S W-A）：投影不可构造（Default clearance
        # 不可解析）→ 整批按 blocked/notes 记录，不静默回退默认值。
        proj = None
        projection_error = str(e)
    parsed_named = (parsed_with_names(proj.parsed, name_map)
                    if proj is not None else None)
    protected = set(nets)
    candidates = []
    fails = []
    ladder_rows = []
    for row in sel:
        if proj is None:
            lr = {"status": "blocked",
                  "trail": [{"level": "A0", "detail": {
                      "status": "blocked",
                      "reason": projection_error,
                      "notes": ["SEC-A-07 修复口径：Default clearance 不可"
                                "解析，整批 blocked（不回退 0.2mm）"]}}]}
        else:
            lr = row_ladder_route(proj, row, protected=protected,
                                  parsed_named=parsed_named)
        rec = {"row_id": row["row_id"], "net": row["net"],
               "row_signature": row["row_signature"],
               "status": lr["status"]}
        if lr["status"] == "committed_candidate":
            acc = lr["accepted"]
            rec.update({
                "ops": acc["ops"], "segments_n": acc["segments_n"],
                "vias_n": acc["vias_n"], "length_mm": acc["length_mm"],
                "width": acc["width"], "precheck": acc["precheck"],
                "remove_segment_uuids": lr.get("remove_segment_uuids", []),
                "remove_via_uuids": lr.get("remove_via_uuids", []),
                "ripup": acc.get("ripup"),
            })
            candidates.append(rec)
        else:
            rec["trail_summary"] = [
                {"level": t["level"],
                 "status": t["detail"].get("status")}
                for t in lr["trail"]]
            if proj is None:
                rec["blocked_reason"] = projection_error
            fails.append(rec)
        ladder_rows.append({"row_id": row["row_id"], "net": row["net"],
                            "trail": lr["trail"]})
    out = {
        "schema": "pcbflow.v4_1.e4-batch-plan/1",
        "declared_date": DECLARED_DATE,
        "batch": batch, "nets": nets, "row_count": len(sel),
        "level": level, "reverse_order": reverse,
        "candidate_rows": len(candidates), "fail_rows": len(fails),
        "candidates": candidates, "fails": fails,
        "ladder_trail": ladder_rows,
    }
    bd = _batch_dir(e4_dir, batch, level=level)
    write_canonical_json(bd / "candidates.json", out)

    def _append_ledger():
        lp = e4 / "ripup-ledger.json"
        if lp.is_file():
            led = _load_json(str(lp))
        else:
            led = {"schema": "pcbflow.v4_1.e4-ripup-ledger/1",
                   "declared_date": DECLARED_DATE, "entries": []}
        for lr in ladder_rows:
            levels_hit = []
            for t in lr["trail"]:
                if t["level"] not in levels_hit:
                    levels_hit.append(t["level"])
            if set(levels_hit) - {"A0"}:
                led["entries"].append({
                    "batch": batch, "row_id": lr["row_id"],
                    "net": lr["net"], "levels_triggered": levels_hit,
                    "trail": lr["trail"]})
        write_canonical_json(lp, led)
    _append_ledger()

    def _mut(o):
        o.setdefault("batches", {})[batch] = {
            "stage": "planned", "nets": nets,
            "candidate_rows": len(candidates), "fail_rows": len(fails),
            "reverse": reverse}
    _progress_update(e4_dir, _mut)
    return out


def op_batch_apply(e4_dir, batch, level="L2"):
    """候选 ops 应用 -> challenger 板（批目录）+ hash 链。"""
    import pathlib
    e4 = pathlib.Path(e4_dir)
    bd = _batch_dir(e4_dir, batch, level=level)
    plan = _load_json(str(bd / "candidates.json"))
    st, pcb, pro = _staging_paths(e4_dir)
    pre_bytes = _read(str(pcb))
    text = pre_bytes.decode("utf-8")
    remove_segs, remove_vias = [], []
    ops = []
    for c in plan["candidates"]:
        ops.extend(c["ops"])
        remove_segs.extend(c.get("remove_segment_uuids") or [])
        remove_vias.extend(c.get("remove_via_uuids") or [])
    new_text = apply_ops_to_text(text, ops, remove_segs, remove_vias)
    post_bytes = new_text.encode("utf-8")
    _write(str(bd / "challenger.kicad_pcb"), post_bytes)
    _write(str(bd / "challenger.kicad_pro"), _read(str(pro)))
    _write(str(bd / "pre-board.kicad_pcb"), pre_bytes)
    from .prl_hygiene import inventory as _inv
    rec = {
        "schema": "pcbflow.v4_1.e4-batch-apply/1",
        "declared_date": DECLARED_DATE,
        "batch": batch,
        "pre_hash_sha256": _sha_bytes(pre_bytes),
        "post_hash_sha256": _sha_bytes(post_bytes),
        "ops_count": len(ops),
        "candidate_rows": plan["candidate_rows"],
        "prl_inventory_before": _inv(str(bd)),
    }
    write_canonical_json(bd / "apply-record.json", rec)

    def _mut(o):
        o["batches"][batch].update({"stage": "applied",
                                    "pre_hash": rec["pre_hash_sha256"],
                                    "post_hash": rec["post_hash_sha256"]})
    _progress_update(e4_dir, _mut)
    return rec


def _drc_counts(obj):
    vs = obj.get("violations", [])
    errs = [v for v in vs if v.get("severity") == "error"]
    return {"violations_total": len(vs), "severity_error": len(errs),
            "unconnected_items": len(obj.get("unconnected_items") or [])}


def _drc_error_keys(obj):
    """severity-error 行身份键（added 归因用：type+items 描述+位置）。"""
    out = []
    for v in obj.get("violations", []):
        if v.get("severity") != "error":
            continue
        items = tuple(sorted(
            (it.get("description", ""),
             round(float(it.get("pos", {}).get("x", 0)), 4),
             round(float(it.get("pos", {}).get("y", 0)), 4))
            for it in v.get("items", [])))
        out.append((v.get("type", ""), items))
    return sorted(out)


def op_batch_record(e4_dir, batch, level="L2", gate_enabled=True):
    """批 DRC 判定 + commit/rollback（硬门=零新增 severity-error）。"""
    import pathlib
    e4 = pathlib.Path(e4_dir)
    bd = _batch_dir(e4_dir, batch, level=level)
    plan = _load_json(str(bd / "candidates.json"))
    apply_rec = _load_json(str(bd / "apply-record.json"))
    drc_err = _load_json(str(bd / "drc-error.json"))
    drc_all = _load_json(str(bd / "drc-all.json"))
    st, pcb, pro = _staging_paths(e4_dir)
    base_err = _load_json(str(bd / "baseline-drc-error.json"))
    base_counts = _drc_counts(base_err)
    chal = _drc_counts(drc_err)
    added = sorted(set(_drc_error_keys(drc_err))
                   - set(_drc_error_keys(base_err)))
    removed = sorted(set(_drc_error_keys(base_err))
                     - set(_drc_error_keys(drc_err)))
    no_change = apply_rec.get("ops_count", 1) == 0
    checks = {
        "pre_hash_matches_staging": _sha_bytes(
            _read(str(pcb))) == apply_rec["pre_hash_sha256"],
        "post_hash_differs": no_change or (
            apply_rec["post_hash_sha256"]
            != apply_rec["pre_hash_sha256"]),
        "severity_error_equal": chal["severity_error"]
        == base_counts["severity_error"],
        "unconnected_not_worse": chal["unconnected_items"]
        <= base_counts["unconnected_items"],
        "added_error_empty": not added,
    }
    verdict = "commit" if all(checks.values()) else "rollback"
    if verdict == "commit":
        _write(str(pcb), _read(str(bd / "challenger.kicad_pcb")))
    from .prl_hygiene import check_and_restore as _car
    prl_rec = _car(str(bd), apply_rec["prl_inventory_before"])
    rec = {
        "schema": "pcbflow.v4_1.e4-batch-record/1",
        "declared_date": DECLARED_DATE,
        "batch": batch, "level": level, "gate_enabled": gate_enabled,
        "hash_chain": {
            "pre_hash_sha256": apply_rec["pre_hash_sha256"],
            "post_hash_sha256": apply_rec["post_hash_sha256"],
            "staging_after_verdict_sha256": _sha_bytes(_read(str(pcb))),
        },
        "drc_baseline": base_counts,
        "drc_challenger": chal,
        "drc_challenger_all": _drc_counts(drc_all),
        "added_error_keys": [list(a) for a in added][:40],
        "removed_error_keys": [list(a) for a in removed][:40],
        "checks": checks,
        "no_change_batch": no_change,
        "verdict": verdict,
        "committed_rows": (0 if no_change else
                           (plan["candidate_rows"]
                            if verdict == "commit" else 0)),
        "unconnected_delta": chal["unconnected_items"]
        - base_counts["unconnected_items"],
        "prl_hygiene": prl_rec,
    }
    write_canonical_json(bd / "batch-record.json", rec)

    def _mut(o):
        o["batches"][batch].update({
            "stage": "committed" if verdict == "commit" else "rolled_back",
            "verdict": verdict,
            "committed_rows": rec["committed_rows"],
            "unconnected_delta": rec["unconnected_delta"],
            "severity_error": chal["severity_error"],
            "unconnected": chal["unconnected_items"]})
        if verdict == "rollback":
            o.setdefault("rollbacks", []).append(
                {"batch": batch, "checks": checks})
    _progress_update(e4_dir, _mut)
    if verdict == "rollback":
        lp = e4 / "ripup-ledger.json"
        led = _load_json(str(lp)) if lp.is_file() else {
            "schema": "pcbflow.v4_1.e4-ripup-ledger/1",
            "declared_date": DECLARED_DATE, "entries": []}
        led["entries"].append({
            "batch": batch, "level": "T1",
            "trigger": "批 DRC 硬门不满足（零新增 severity-error 破）",
            "checks": checks, "result": "rolled_back"})
        write_canonical_json(lp, led)
    return rec


def op_g43(e4_dir, headless_drc_json, final_drc_json, committed_rows):
    """G4.3 配对对比+预注册判读带（prereg bands 冻结）。"""
    import pathlib
    base = _load_json(headless_drc_json)
    fin = _load_json(final_drc_json)
    b, f = _drc_counts(base), _drc_counts(fin)
    improvement = round(100.0 * committed_rows / b["unconnected_items"], 6)
    if improvement >= 30.0:
        band = "supported"
    elif improvement >= 10.0:
        band = "marginal"
    else:
        band = "not_viable_candidate"
    out = {
        "schema": "pcbflow.v4_1.e4-g43/1",
        "declared_date": DECLARED_DATE,
        "pairing": {
            "headless_baseline": {"drc": str(headless_drc_json), **b},
            "e4_final": {"drc": str(final_drc_json), **f},
        },
        "improvement_definition":
            "E4_committed_rows / headless_unconnected(%d) x 100"
            % b["unconnected_items"],
        "committed_rows": committed_rows,
        "improvement_pct": improvement,
        "bands_pct": {"supported": ">=30", "marginal": "[10,30)",
                      "not_viable_candidate": "<10"},
        "band": band,
        "s2_submission": (band == "not_viable_candidate"),
        "s2_note": "not_viable 候选=提交 §9 S2 停机判定材料（登记 "
                   "not_viable_for_full_board 由主审/用户裁决；执行侧不"
                   "自行宣布收缩）",
    }
    write_canonical_json(pathlib.Path(e4_dir) / "g43-comparison.json", out)
    return out


def main(argv=None):
    import argparse
    import json
    import pathlib
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e4revc")
    ap.add_argument("op", choices=["stage-init", "rows", "batch-plan",
                                   "batch-apply", "batch-record", "g43"])
    ap.add_argument("--e4-dir", default=_E4_DIR_DEFAULT)
    ap.add_argument("--src-pcb"), ap.add_argument("--src-pro")
    ap.add_argument("--drc"), ap.add_argument("--batch")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--level", default="L2",
                    choices=["L2", "L3"])
    ap.add_argument("--headless-drc"), ap.add_argument("--final-drc")
    ap.add_argument("--committed-rows", type=int, default=0)
    ns = ap.parse_args(argv)
    e4 = pathlib.Path(ns.e4_dir)
    e4.mkdir(parents=True, exist_ok=True)
    if ns.op == "stage-init":
        rec = op_stage_init(e4, ns.src_pcb, ns.src_pro)
    elif ns.op == "rows":
        rec = op_rows(e4, ns.drc, level=ns.level)
    elif ns.op == "batch-plan":
        rec = op_batch_plan(e4, ns.batch, reverse=ns.reverse,
                            level=ns.level)
    elif ns.op == "batch-apply":
        rec = op_batch_apply(e4, ns.batch, level=ns.level)
    elif ns.op == "batch-record":
        rec = op_batch_record(e4, ns.batch, level=ns.level)
    else:
        rec = op_g43(e4, ns.headless_drc, ns.final_drc, ns.committed_rows)
    summary = {k: v for k, v in rec.items()
               if isinstance(v, (int, float, str, bool))}
    print("ok:", ns.op, json.dumps(summary, ensure_ascii=False)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
