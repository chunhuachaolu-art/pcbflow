# -*- coding: utf-8 -*-
"""L0 板镜像（BoardMirror，SPEC §1）。

- 加载：无 KiCad 实例依赖，直接解析 .kicad_pcb（s-expr）+ .kicad_pro（规则）。
- net 以名字为键（KiCad 10 文件里无编号，HANDOFF 坑 2）。
- 形状统一为 geometry.prim（core ⊕ r），pad 含旋转（真旋转矩形，非轴对齐 bbox——
  失败审计 M2 教训）。镜像只读：写路径在 L3 commit，绝不走本模块。
- zone 以 filled_polygon 为铜实体（nonzero 绕数判内）；rasterize/connectivity/opens
  为 SPEC 规定服务。
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from . import config as C
from . import geometry as G
from . import sexpr as S

COPPER_LAYER_NAMES = {"F.Cu": C.LAYER_F, "B.Cu": C.LAYER_B,
                      "In1.Cu": C.LAYER_IN1, "In2.Cu": C.LAYER_IN2}
STACK_ORDER = [C.LAYER_F, C.LAYER_IN1, C.LAYER_IN2, C.LAYER_B]  # 由表及里
STACK_ORDER_ALL = frozenset(STACK_ORDER)


class NetClass:
    __slots__ = ("name", "clearance", "via_diameter", "via_drill", "wire_width")

    def __init__(self, name, clearance, via_diameter, via_drill, wire_width):
        self.name = name
        self.clearance = clearance
        self.via_diameter = via_diameter
        self.via_drill = via_drill
        self.wire_width = wire_width


class CopperItem:
    """含铜项：prims（绝对坐标 core⊕r）、net（名字键）、层集、描述。"""
    __slots__ = ("kind", "net", "layers", "prims", "desc")

    def __init__(self, kind, net, layers, prims, desc):
        self.kind = kind      # 'pad' | 'track' | 'via'
        self.net = net        # netless 为 ""
        self.layers = layers  # frozenset(int)
        self.prims = prims
        self.desc = desc


class HoleItem:
    """钻孔：孔存在于 layers 跨层范围内（过孔 F..In2 的孔不达 B 层）。
    npth=True 的孔-铜间距要求按网络类口径（实测校准，见 config）。"""
    __slots__ = ("net", "layers", "prim", "desc", "npth")

    def __init__(self, net, layers, prim, desc, npth=False):
        self.net = net
        self.layers = layers
        self.prim = prim
        self.desc = desc
        self.npth = npth


class ZoneFill:
    __slots__ = ("net", "layer", "rings", "edges", "filled", "_edge_idx")

    def __init__(self, net, layer, rings, filled=True):
        self.net = net
        self.layer = layer
        self.rings = rings
        self.edges = [(r[i][0], r[i][1], r[(i + 1) % len(r)][0], r[(i + 1) % len(r)][1])
                      for r in rings for i in range(len(r))]
        self.filled = filled
        self._edge_idx = None

    def edges_near(self, x1, y1, x2, y2, pad=0.5):
        """bbox 附近的填充边（惰性桶索引；zone 多边形巨大，禁全量遍历）。"""
        if self._edge_idx is None:
            idx = {}
            for ei, e in enumerate(self.edges):
                bx1 = int(min(e[0], e[2]) // C.BUCKET)
                bx2 = int(max(e[0], e[2]) // C.BUCKET)
                by1 = int(min(e[1], e[3]) // C.BUCKET)
                by2 = int(max(e[1], e[3]) // C.BUCKET)
                for bx in range(bx1, bx2 + 1):
                    for by in range(by1, by2 + 1):
                        idx.setdefault((bx, by), []).append(ei)
            self._edge_idx = idx
        out = set()
        for bx in range(int((x1 - pad) // C.BUCKET), int((x2 + pad) // C.BUCKET) + 1):
            for by in range(int((y1 - pad) // C.BUCKET), int((y2 + pad) // C.BUCKET) + 1):
                lst = self._edge_idx.get((bx, by))
                if lst:
                    out.update(lst)
        return [self.edges[i] for i in out]


class Pad:
    __slots__ = ("ref", "number", "net", "layers", "x", "y", "rot", "w", "h",
                 "shape", "drill", "npth")

    def __init__(self, ref, number, net, layers, x, y, rot, w, h, shape, drill, npth):
        self.ref = ref
        self.number = number
        self.net = net
        self.layers = layers
        self.x, self.y, self.rot = x, y, rot
        self.w, self.h = w, h
        self.shape = shape
        self.drill = drill
        self.npth = npth


class Track:
    __slots__ = ("layer", "x1", "y1", "x2", "y2", "width", "net")

    def __init__(self, layer, x1, y1, x2, y2, width, net):
        self.layer, self.x1, self.y1, self.x2, self.y2 = layer, x1, y1, x2, y2
        self.width = width
        self.net = net


class Via:
    __slots__ = ("x", "y", "size", "drill", "layers", "net")

    def __init__(self, x, y, size, drill, layers, net):
        self.x, self.y, self.size, self.drill = x, y, size, drill
        self.layers = layers
        self.net = net


def _span_layers(la, lb):
    ia, ib = STACK_ORDER.index(la), STACK_ORDER.index(lb)
    lo, hi = min(ia, ib), max(ia, ib)
    return frozenset(STACK_ORDER[lo:hi + 1])


class BoardMirror:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.pcb_path = None
        self.pro_path = None
        for f in os.listdir(project_dir):
            if f.endswith(".kicad_pro"):
                self.pro_path = os.path.join(project_dir, f)
        if self.pro_path:
            # 同目录可能有历史评估板（如 expA-eval.kicad_pcb）：必须取与 .kicad_pro
            # 同名的板文件，否则会镜像到错误版本
            stem = os.path.splitext(os.path.basename(self.pro_path))[0]
            cand = os.path.join(project_dir, stem + ".kicad_pcb")
            if os.path.exists(cand):
                self.pcb_path = cand
        if not self.pcb_path:
            for f in os.listdir(project_dir):
                if f.endswith(".kicad_pcb"):
                    self.pcb_path = os.path.join(project_dir, f)
                    break
        if not self.pcb_path:
            raise FileNotFoundError(f"no .kicad_pcb in {project_dir}")
        self.net_classes: dict[str, NetClass] = {}
        self.net_class_of: dict[str, str] = {}
        self.pads: list[Pad] = []
        self.tracks: list[Track] = []
        self.vias: list[Via] = []
        self.zones: list[ZoneFill] = []
        self.edge_segs: list[tuple] = []
        self.items: list[CopperItem] = []
        self.holes: list[HoleItem] = []
        self._items_by_net: dict[str, list[int]] = {}
        self._bucket: dict[tuple, list[int]] = {}
        self._hole_bucket: dict[tuple, list[int]] = {}
        self._load_pro()
        self._load_pcb()
        self._build_index()

    # ---------- 规则（网络类感知接口）----------

    def _load_pro(self):
        if not self.pro_path:
            self.net_classes["Default"] = NetClass("Default", 0.2, 0.6, 0.3, 0.2)
            return
        pro = json.load(open(self.pro_path, encoding="utf-8"))
        for c in pro.get("net_settings", {}).get("classes", []):
            nc = NetClass(c.get("name", "Default"),
                          float(c.get("clearance", 0.2)),
                          float(c.get("via_diameter", 0.6)),
                          float(c.get("via_drill", 0.3)),
                          float(c.get("wire_width", 0.2)))
            self.net_classes[nc.name] = nc
            # net→class 指派在原理图侧；pro 无 netnames 时全部落 Default
            # （本板 18 类 clearance 一致 0.2，对 L1 判定无差异——见 PHASE-REPORT）
            for n in c.get("netnames", []):
                self.net_class_of[n] = nc.name

    def clearance_between(self, net_a: str, net_b: str) -> float:
        ca = self.net_classes.get(self.net_class_of.get(net_a, "Default"))
        cb = self.net_classes.get(self.net_class_of.get(net_b, "Default"))
        va = ca.clearance if ca else C.BOARD_MIN_CLEARANCE
        vb = cb.clearance if cb else C.BOARD_MIN_CLEARANCE
        return max(va, vb, C.BOARD_MIN_CLEARANCE)

    def via_params_of(self, net: str):
        nc = self.net_classes.get(self.net_class_of.get(net, "Default"))
        if nc:
            return nc.via_diameter, nc.via_drill
        return 0.6, 0.3

    # ---------- 解析 ----------

    def _load_pcb(self):
        with open(self.pcb_path, encoding="utf-8") as fh:
            root = S.parse(fh.read())
        for node in S.walk(root, "footprint"):
            self._load_footprint(node)
        for seg in S.walk(root, "segment"):
            st, en = S.child(seg, "start"), S.child(seg, "end")
            w = S.num(S.atoms(S.child(seg, "width"))[0])
            layer = S.atoms(S.child(seg, "layer"))[0]
            nnode = S.child(seg, "net")
            netn = S.atoms(nnode)[0] if nnode is not None else ""
            t = Track(COPPER_LAYER_NAMES[layer], S.num(st[1]), S.num(st[2]),
                      S.num(en[1]), S.num(en[2]), w, netn)
            self.tracks.append(t)
            self._add_item(CopperItem(
                "track", t.net, frozenset((t.layer,)),
                [(("seg", t.x1, t.y1, t.x2, t.y2), t.width / 2.0)],
                f"走线 [{t.net or '无网'}] ({t.x1:.4f},{t.y1:.4f})-({t.x2:.4f},{t.y2:.4f}) w={t.width}"))
        for v in S.walk(root, "via"):
            at = S.child(v, "at")
            size = S.num(S.atoms(S.child(v, "size"))[0])
            drill = S.num(S.atoms(S.child(v, "drill"))[0])
            lnode = S.child(v, "layers")
            la = COPPER_LAYER_NAMES[S.atoms(lnode)[0]]
            lb = COPPER_LAYER_NAMES[S.atoms(lnode)[1]]
            nnode = S.child(v, "net")
            netn = S.atoms(nnode)[0] if nnode is not None else ""
            x, y = S.num(at[1]), S.num(at[2])
            vv = Via(x, y, size, drill, _span_layers(la, lb), netn)
            self.vias.append(vv)
            # 存量 via 盘保持精确圆（O(1) 查询）；CLI 的多边形近似口径只对
            # "候选盘"生效（legality._via_disk_prim，B1 校准实证）
            self._add_item(CopperItem(
                "via", vv.net, vv.layers,
                [(("pt", x, y), size / 2.0)],
                f"过孔 [{vv.net or '无网'}] ({x:.4f},{y:.4f}) size={size} drill={drill}"))
            self._add_hole(HoleItem(
                vv.net, vv.layers, (("pt", x, y), drill / 2.0),
                f"过孔钻孔 [{vv.net or '无网'}] ({x:.4f},{y:.4f}) d={drill}"))
        for z in S.walk(root, "zone"):
            nnode = S.child(z, "net")
            netn = S.atoms(nnode)[0] if nnode is not None else ""
            for fp in S.children(z, "filled_polygon"):
                layer = S.atoms(S.child(fp, "layer"))[0]
                rings = []
                for pts in S.children(fp, "pts"):
                    ring = [(S.num(xy[1]), S.num(xy[2])) for xy in S.children(pts, "xy")]
                    if len(ring) >= 3:
                        rings.append(ring)
                if rings:
                    self.zones.append(ZoneFill(netn, COPPER_LAYER_NAMES[layer], rings))
        for node in S.walk(root, "gr_line"):
            ln = S.child(node, "layer")
            if ln and S.atoms(ln)[0] == "Edge.Cuts":
                st, en = S.child(node, "start"), S.child(node, "end")
                self.edge_segs.append((S.num(st[1]), S.num(st[2]),
                                       S.num(en[1]), S.num(en[2])))
        for node in S.walk(root, "gr_rect"):
            ln = S.child(node, "layer")
            if ln and S.atoms(ln)[0] == "Edge.Cuts":
                st, en = S.child(node, "start"), S.child(node, "end")
                x1, y1, x2, y2 = S.num(st[1]), S.num(st[2]), S.num(en[1]), S.num(en[2])
                self.edge_segs += [(x1, y1, x2, y1), (x2, y1, x2, y2),
                                   (x2, y2, x1, y2), (x1, y2, x1, y1)]

    def _load_footprint(self, fp):
        fpat = S.child(fp, "at")
        fx, fy = S.num(fpat[1]), S.num(fpat[2])
        frot = S.num(fpat[3]) if len(fpat) > 3 else 0.0
        ref = "?"
        for prop in S.children(fp, "property"):
            a = S.atoms(prop)
            if len(a) >= 2 and a[0] == "Reference":
                ref = a[1]
                break
        for pd in S.children(fp, "pad"):
            self._load_pad(pd, ref, fx, fy, frot)

    def _load_pad(self, pd, ref, fx, fy, frot):
        atoms = S.atoms(pd)
        number = atoms[0] if len(atoms) > 0 else ""
        ptype = atoms[1] if len(atoms) > 1 else "smd"
        shape = atoms[2] if len(atoms) > 2 else "rect"
        pat = S.child(pd, "at")
        px_local, py_local = S.num(pat[1]), S.num(pat[2])
        prot = S.num(pat[3]) if len(pat) > 3 else 0.0
        ox, oy = G.rot_pt(px_local, py_local, frot)
        ax, ay = fx + ox, fy + oy
        # KiCad 9+ 板文件格式：pad 的 (at x y rot) 角度已是绝对角（含封装旋转），
        # 位置偏移仍按封装旋转。U2/R5 双例 + pcbnew SWIG 交叉验证实证。
        trot = prot % 360.0
        szn = S.child(pd, "size")
        w, h = S.num(szn[1]), S.num(szn[2])
        nnode = S.child(pd, "net")
        netn = S.atoms(nnode)[0] if nnode is not None else ""
        layers = set()
        lnode = S.child(pd, "layers")
        if lnode:
            for tok in S.atoms(lnode):
                if tok in COPPER_LAYER_NAMES:
                    layers.add(COPPER_LAYER_NAMES[tok])
                elif tok == "*.Cu":
                    layers |= set(STACK_ORDER)
        drill = 0.0
        oval_drill = None
        dnode = S.child(pd, "drill")
        if dnode is not None:
            da = S.atoms(dnode)
            if da and da[0] == "oval":
                oval_drill = (S.num(da[1]), S.num(da[2]))
            elif da:
                drill = S.num(da[0])
        npth = ptype == "np_thru_hole"
        if npth:
            drill = drill or w
        layers = frozenset(layers)
        self.pads.append(Pad(ref, number, netn, layers, ax, ay, trot, w, h,
                             shape, drill, npth))
        if npth:
            # 非金属化孔：只有孔，无铜
            prim = self._hole_prim(oval_drill, drill, ax, ay, trot)
            self._add_hole(HoleItem("", STACK_ORDER_ALL, prim,
                                    f"NPTH 孔 ({ax:.4f},{ay:.4f}) d={drill}",
                                    npth=True))
            return
        copper_layers = STACK_ORDER_ALL if ptype == "thru_hole" else layers
        prims = self._pad_prims(shape, w, h, trot, pd, ax, ay)
        self._add_item(CopperItem(
            "pad", netn, copper_layers, prims,
            f"{ref} 焊盘 {number} [{netn or '无网'}] ({ax:.4f},{ay:.4f}) {shape} {w}x{h}"))
        if drill > 0 or oval_drill:
            prim = self._hole_prim(oval_drill, drill, ax, ay, trot)
            self._add_hole(HoleItem(netn, STACK_ORDER_ALL, prim,
                                    f"PTH 钻孔 [{netn}] ({ax:.4f},{ay:.4f}) d={drill}"))

    def _hole_prim(self, oval_drill, drill, ax, ay, trot):
        if oval_drill:
            return self._move_prim(self._capsule_prim(0, 0, oval_drill[0],
                                                      oval_drill[1], trot), ax, ay)
        return (("pt", ax, ay), drill / 2.0)

    # ---------- pad 形状 → 绝对 prim 集 ----------

    def _pad_prims(self, shape, w, h, trot, pd_node, ax, ay):
        prims = []
        if shape == "rect":
            prims.append(self._rect_prim(0, 0, w / 2.0, h / 2.0, trot))
        elif shape == "circle":
            prims.append((("pt", 0, 0), w / 2.0))
        elif shape == "oval":
            prims.append(self._capsule_prim(0, 0, w, h, trot))
        elif shape == "roundrect":
            rrn = S.child(pd_node, "roundrect_rratio")
            rratio = S.num(S.atoms(rrn)[0]) if rrn is not None else 0.25
            r = rratio * min(w, h)
            core = G.inset_rect_poly(0, 0, w / 2.0, h / 2.0, r)
            if core is None:
                prims.append(self._capsule_prim(0, 0, w, h, trot))
            else:
                prims.append((("poly", self._rot_poly(core, trot)), r))
        elif shape == "custom":
            opt = S.child(pd_node, "options")
            anchor = "rect"
            if opt is not None:
                an = S.child(opt, "anchor")
                if an is not None:
                    anchor = S.atoms(an)[0]
            if anchor == "rect":
                prims.append(self._rect_prim(0, 0, w / 2.0, h / 2.0, trot))
            elif anchor == "circle":
                prims.append((("pt", 0, 0), min(w, h) / 2.0))
            primn = S.child(pd_node, "primitives")
            if primn is not None:
                for gr in primn[1:]:
                    if not isinstance(gr, list) or not gr:
                        continue
                    if gr[0] == "gr_poly":
                        for ptsn in S.children(gr, "pts"):
                            pts = [(S.num(xy[1]), S.num(xy[2]))
                                   for xy in S.children(ptsn, "xy")]
                            if len(pts) >= 3:
                                prims.append((("poly", self._rot_poly(pts, trot)), 0.0))
                    elif gr[0] == "gr_line":
                        st, en = S.child(gr, "start"), S.child(gr, "end")
                        prims.append((("seg", S.num(st[1]), S.num(st[2]),
                                       S.num(en[1]), S.num(en[2])), 0.0))
                    elif gr[0] == "gr_rect":
                        st, en = S.child(gr, "start"), S.child(gr, "end")
                        prims.append(self._rect_prim(
                            (S.num(st[1]) + S.num(en[1])) / 2,
                            (S.num(st[2]) + S.num(en[2])) / 2,
                            abs(S.num(en[1]) - S.num(st[1])) / 2,
                            abs(S.num(en[2]) - S.num(st[2])) / 2, 0.0))
                    elif gr[0] == "gr_circle":
                        cen, en = S.child(gr, "center"), S.child(gr, "end")
                        r = math.hypot(S.num(en[1]) - S.num(cen[1]),
                                       S.num(en[2]) - S.num(cen[2]))
                        prims.append((("pt", S.num(cen[1]), S.num(cen[2])), r))
        else:
            # 未见形状保守取外接矩形（Rev-C 无 trapezoid 等，见报告偏离清单）
            prims.append(self._rect_prim(0, 0, w / 2.0, h / 2.0, trot))
        return [self._move_prim(p, ax, ay) for p in prims]

    def _rect_prim(self, cx, cy, hw, hh, rot):
        poly = [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]
        return (("poly", self._rot_poly(poly, rot)), 0.0)

    def _capsule_prim(self, cx, cy, w, h, rot):
        if w >= h:
            half, r, dx, dy = (w - h) / 2.0, h / 2.0, (w - h) / 2.0, 0.0
        else:
            half, r, dx, dy = (h - w) / 2.0, w / 2.0, 0.0, (h - w) / 2.0
        x1, y1 = G.rot_pt(cx - dx, cy - dy, rot)
        x2, y2 = G.rot_pt(cx + dx, cy + dy, rot)
        return (("seg", x1, y1, x2, y2), r)

    def _rot_poly(self, pts, rot):
        if rot % 360.0 == 0.0:
            return [(x, y) for (x, y) in pts]
        return [G.rot_pt(x, y, rot) for (x, y) in pts]

    @staticmethod
    def _move_prim(p, dx, dy):
        core, r = p
        if core[0] == "pt":
            return (("pt", core[1] + dx, core[2] + dy), r)
        if core[0] == "seg":
            return (("seg", core[1] + dx, core[2] + dy, core[3] + dx, core[4] + dy), r)
        return (("poly", [(x + dx, y + dy) for (x, y) in core[1]]), r)

    # ---------- 索引 ----------

    def _add_item(self, item: CopperItem):
        self._items_by_net.setdefault(item.net, []).append(len(self.items))
        self.items.append(item)

    def _add_hole(self, hole: HoleItem):
        self.holes.append(hole)

    def _build_index(self):
        for idx, it in enumerate(self.items):
            for prim in it.prims:
                x1, y1, x2, y2 = G.prim_bbox(prim)
                self._index_put(self._bucket, it.layers, x1, y1, x2, y2, idx)
        for idx, h in enumerate(self.holes):
            x1, y1, x2, y2 = G.prim_bbox(h.prim)
            self._index_put(self._hole_bucket, h.layers, x1, y1, x2, y2, idx)

    @staticmethod
    def _index_put(bucket, layers, x1, y1, x2, y2, idx):
        pad = C.BUCKET
        for L in layers:
            for bx in range(int((x1 - pad) // C.BUCKET), int((x2 + pad) // C.BUCKET) + 1):
                for by in range(int((y1 - pad) // C.BUCKET), int((y2 + pad) // C.BUCKET) + 1):
                    bucket.setdefault((L, bx, by), []).append(idx)

    def query_copper(self, layer, x1, y1, x2, y2, extra=0.0):
        out = set()
        for bx in range(int((x1 - extra) // C.BUCKET), int((x2 + extra) // C.BUCKET) + 1):
            for by in range(int((y1 - extra) // C.BUCKET), int((y2 + extra) // C.BUCKET) + 1):
                lst = self._bucket.get((layer, bx, by))
                if lst:
                    out.update(lst)
        return [self.items[i] for i in out]

    def query_holes(self, layer, x1, y1, x2, y2, extra=0.0):
        out = set()
        for bx in range(int((x1 - extra) // C.BUCKET), int((x2 + extra) // C.BUCKET) + 1):
            for by in range(int((y1 - extra) // C.BUCKET), int((y2 + extra) // C.BUCKET) + 1):
                lst = self._hole_bucket.get((layer, bx, by))
                if lst:
                    out.update(lst)
        return [self.holes[i] for i in out]

    def zones_on(self, layer):
        return [z for z in self.zones if z.layer == layer]

    # ---------- 服务（SPEC §1）----------

    def rasterize(self, layer, bbox, res):
        """uint16 栅格：bit12-15=类型(1 pad/2 track/3 via/4 zone)，bit0-11=net 序号(1基)。
        逐格心精确判覆盖。"""
        x0, y0, x1, y1 = bbox
        nx = max(1, int(math.ceil((x1 - x0) / res)))
        ny = max(1, int(math.ceil((y1 - y0) / res)))
        grid = np.zeros((ny, nx), dtype=np.uint16)
        net_idx = {n: i + 1 for i, n in enumerate(
            sorted(k for k in self._items_by_net if k))}
        type_bit = {"pad": 1, "track": 2, "via": 3}
        cands = self.query_copper(layer, x0 - res, y0 - res, x1 + res, y1 + res,
                                  extra=res + 1.0)
        static_prims = []
        for it in cands:
            for prim in it.prims:
                static_prims.append((prim, type_bit[it.kind], net_idx.get(it.net, 0)))
        zone_list = self.zones_on(layer)
        for iy in range(ny):
            cy = y0 + (iy + 0.5) * res
            for ix in range(nx):
                cx = x0 + (ix + 0.5) * res
                val = 0
                for (prim, tb, ni) in static_prims:
                    if G.pt_prim_dist(cx, cy, prim) <= 0.0:
                        v = (tb << 12) | (ni & 0x0FFF)
                        if v > val:
                            val = v
                if val == 0:
                    for z in zone_list:
                        if G.pt_in_rings(cx, cy, z.rings):
                            v = (4 << 12) | (net_idx.get(z.net, 0) & 0x0FFF)
                            if v > val:
                                val = v
                grid[iy, ix] = val
        return grid

    def connectivity(self, net):
        """并查集连通分量。同网已灌 zone 作为公共节点：接触 zone 的分量合并为一组
        （组内追加字符串 'ZONE' 标记）。返回 list[list[CopperItem|'ZONE']]。"""
        idxs = self._items_by_net.get(net, [])
        n = len(idxs)
        items = [self.items[i] for i in idxs]
        par = list(range(n))

        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i

        bbs = [_items_bbox(it) for it in items]
        for a in range(n):
            ia = items[a]
            ba0, ba1, ba2, ba3 = bbs[a]
            for b in range(a + 1, n):
                bb0, bb1, bb2, bb3 = bbs[b]
                if ba0 > bb2 + C.TOUCH_TOL or bb0 > ba2 + C.TOUCH_TOL or \
                   ba1 > bb3 + C.TOUCH_TOL or bb1 > ba3 + C.TOUCH_TOL:
                    continue
                if not (ia.layers & items[b].layers):
                    continue
                if _items_touch(ia, items[b]):
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        par[ra] = rb
        zl = [z for z in self.zones if z.net == net and z.filled]
        zone_roots = set()
        if zl:
            zlayers = {z.layer for z in zl}
            for a in range(n):
                ia = items[a]
                if ia.layers & zlayers:
                    for z in zl:
                        if z.layer in ia.layers and _item_touches_zone(ia, z):
                            zone_roots.add(find(a))
        groups: dict[int, list] = {}
        for a in range(n):
            groups.setdefault(find(a), []).append(items[a])
        out = []
        merged = None
        for root, g in groups.items():
            if root in zone_roots:
                if merged is None:
                    merged = list(g)
                else:
                    merged.extend(g)
            else:
                out.append(g)
        if merged is not None:
            merged.append("ZONE")
            out.insert(0, merged)
        return out

    def opens(self):
        """{net: 断点数(=分量数-1)}，只统计有焊盘的网。"""
        res = {}
        for net, idxs in self._items_by_net.items():
            if not net:
                continue
            if not any(self.items[i].kind == "pad" for i in idxs):
                continue
            res[net] = max(0, len(self.connectivity(net)) - 1)
        return res

    def sync(self):
        self._load_pro()
        self.pads.clear()
        self.tracks.clear()
        self.vias.clear()
        self.zones.clear()
        self.edge_segs.clear()
        self.items.clear()
        self.holes.clear()
        self._items_by_net.clear()
        self._load_pcb()
        self._build_index()

    def stats(self):
        return {
            "pads": len(self.pads),
            "tracks": len(self.tracks),
            "vias": len(self.vias),
            "nets": len([k for k in self._items_by_net if k]),
            "zones": len(self.zones),
            "edge_segs": len(self.edge_segs),
            "bbox": self.bbox(),
        }

    def bbox(self):
        xs, ys = [], []
        for (x1, y1, x2, y2) in self.edge_segs:
            xs += [x1, x2]
            ys += [y1, y2]
        if not xs:
            return None
        return (min(xs), min(ys), max(xs), max(ys))


def _items_bbox(it: CopperItem):
    x1 = y1 = float("inf")
    x2 = y2 = -float("inf")
    for prim in it.prims:
        a, b, c, d = G.prim_bbox(prim)
        x1, y1 = min(x1, a), min(y1, b)
        x2, y2 = max(x2, c), max(y2, d)
    return x1, y1, x2, y2


def _items_touch(a: CopperItem, b: CopperItem) -> bool:
    for pa in a.prims:
        for pb in b.prims:
            if G.prim_dist(pa, pb) <= C.TOUCH_TOL:
                return True
    return False


def _item_touches_zone(it: CopperItem, z: ZoneFill) -> bool:
    """项是否触及 zone 填充实体的铜。先做一次中心绕数判内，再用局部边
    （edges_near 桶索引）做穿越/最小距离——避免对数万填充边全量遍历。"""
    for prim in it.prims:
        core, r = prim
        k = core[0]
        if k == "pt":
            if G.pt_in_rings(core[1], core[2], z.rings):
                return True
            loc = z.edges_near(core[1] - r - 0.1, core[2] - r - 0.1,
                               core[1] + r + 0.1, core[2] + r + 0.1)
            if _pt_rings_dist(core[1], core[2], loc) <= r + C.TOUCH_TOL:
                return True
        elif k == "seg":
            x1, y1, x2, y2 = core[1], core[2], core[3], core[4]
            if G.pt_in_rings(x1, y1, z.rings) or G.pt_in_rings(x2, y2, z.rings):
                return True
            bx1, by1 = min(x1, x2) - r - 0.1, min(y1, y2) - r - 0.1
            bx2, by2 = max(x1, x2) + r + 0.1, max(y1, y2) + r + 0.1
            loc = z.edges_near(bx1, by1, bx2, by2)
            if G.seg_crosses_rings(x1, y1, x2, y2, loc):
                return True
            if _seg_rings_dist(x1, y1, x2, y2, loc) <= r + C.TOUCH_TOL:
                return True
        else:
            poly = core[1]
            if G.pt_in_rings(poly[0][0], poly[0][1], z.rings):
                return True
            xs = [p0[0] for p0 in poly]
            ys = [p0[1] for p0 in poly]
            loc = z.edges_near(min(xs) - r - 0.1, min(ys) - r - 0.1,
                               max(xs) + r + 0.1, max(ys) + r + 0.1)
            for c0, c1 in zip(poly, poly[1:] + poly[:1]):
                if G.seg_crosses_rings(c0[0], c0[1], c1[0], c1[1], loc):
                    return True
            d = min(_seg_rings_dist(c0[0], c0[1], c1[0], c1[1], loc)
                    for c0, c1 in zip(poly, poly[1:] + poly[:1]))
            if d <= r + C.TOUCH_TOL:
                return True
    return False


def _pt_rings_dist(px, py, edges) -> float:
    return min(G.seg_pt_dist(px, py, *e) for e in edges)


def _seg_rings_dist(x1, y1, x2, y2, edges) -> float:
    return min(G.seg_seg_dist(x1, y1, x2, y2, *e) for e in edges)
