"""pcbflow.v4_1.checker -- 独立几何 checker（与 precheck 结构性双实现）。

独立性（对拍用，不一致=blocked 登记）：

- 解析：路径 B（board_parse_alt，行扫描/正则；零依赖路径 A）；
- 几何引擎：外切多边形表示——圆弧用外切折线逼近（顶点半径
  r/cos(π/N)，N>=32/整圆 → 形状超集，clearance 只会低估不会高估 =
  漏报 0 方向），与 precheck 的 Minkowski 核闭式引擎无共享代码；
- 距离：自有 线段-线段 / 凸多边形对 距离与 SAT 相交判定实现。

物项建模（全部凸多边形超集）：

- track：两端帽圆外切 N 边形的凸包（胶囊超集；直边自动相切）；
- via / circle pad：外切 N 边形；
- oval pad：两帽外切 N 边形凸包（胶囊超集）；
- rect pad：精确顶点多边形（旋转由顶点变换承载）；
- roundrect pad：4 直边（按 r 缩进）+ 4 圆角外切折线（超集）；
- custom pad（backlog）：基元顶点包围盒（与 precheck 同保守方向，独立
  实现）。

保守带与违例判定逻辑与 precheck 同构（CONSERVATIVE_BAND_MM）。

零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math

from . import CONSERVATIVE_BAND_MM, DECLARED_DATE

__all__ = ["CheckerBlocked", "CheckItem", "IndependentGeometryChecker",
           "build_check_items"]

_CHECKER_SCHEMA = "pcbflow.v4_1.checker/1"
_ARC_SEGMENTS = 32          # 每整圆折线段数（外切超集）

_LIMITATIONS = [
    "zone/铺铜填充不建模（E2/E6 域，登记 limitation 非 silence）",
    "custom 基元 backlog：顶点包围盒保守超集",
    "圆弧外切折线超集：pred_clearance 系统性低估（上界 "
    "r*(1/cos(pi/N)-1)，N=%d——典型 0.075mm 半径约 0.00036mm）"
    % _ARC_SEGMENTS,
]


class CheckerBlocked(ValueError):
    """checker fail-closed。"""


# ---------------------------------------------------------------- 自有几何

def _dist_point_seg(px, py, x1, y1, x2, y2):
    """点-线段距离（自有实现：参数投影，闭式）。"""
    ex, ey = x2 - x1, y2 - y1
    dot = ex * ex + ey * ey
    if dot <= 0.0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * ex + (py - y1) * ey) / dot
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return math.hypot(px - (x1 + t * ex), py - (y1 + t * ey))


def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


def _seg_hit_seg(ax, ay, bx, by, cx, cy, dx, dy):
    d1 = _cross(cx, cy, dx, dy, ax, ay)
    d2 = _cross(cx, cy, dx, dy, bx, by)
    d3 = _cross(ax, ay, bx, by, cx, cy)
    d4 = _cross(ax, ay, bx, by, dx, dy)
    tol = 1e-12
    if ((d1 > tol and d2 < -tol) or (d1 < -tol and d2 > tol)) and \
            ((d3 > tol and d4 < -tol) or (d3 < -tol and d4 > tol)):
        return True
    def _collinear_on(ox, oy, lx1, ly1, lx2, ly2, px, py):
        return abs(_cross(ox, oy, lx1, ly1, lx2, ly2)) <= tol and \
            min(lx1, lx2) - tol <= px <= max(lx1, lx2) + tol and \
            min(ly1, ly2) - tol <= py <= max(ly1, ly2) + tol
    return (_collinear_on(ax, ay, bx, by, cx, cy)
            or _collinear_on(ax, ay, bx, by, dx, dy)
            or _collinear_on(cx, cy, dx, dy, ax, ay)
            or _collinear_on(cx, cy, dx, dy, bx, by))


def _dist_seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    if _seg_hit_seg(ax, ay, bx, by, cx, cy, dx, dy):
        return 0.0
    return min(_dist_point_seg(ax, ay, cx, cy, dx, dy),
               _dist_point_seg(bx, by, cx, cy, dx, dy),
               _dist_point_seg(cx, cy, ax, ay, bx, by),
               _dist_point_seg(dx, dy, ax, ay, bx, by))


def _point_in_poly(px, py, poly):
    """凸多边形内/边上判定（全部叉积同号；自有实现）。"""
    tol = 1e-12
    pos = neg = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = _cross(x1, y1, x2, y2, px, py)
        if c > tol:
            pos = True
        elif c < -tol:
            neg = True
    return not (pos and neg)


def _poly_hit_poly(pa, pb):
    """两凸多边形相交（含边界）：SAT（自有实现）。"""
    def _axes(poly):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            yield (-(y2 - y1), x2 - x1)
    for poly in (pa, pb):
        for (axn, ayn) in _axes(poly):
            la = [x * axn + y * ayn for (x, y) in pa]
            lb = [x * axn + y * ayn for (x, y) in pb]
            if max(la) < min(lb) - 1e-12 or max(lb) < min(la) - 1e-12:
                return False
    return True


def _poly_distance(pa, pb):
    """两凸多边形距离（相交=0；否则边对最小距离，闭式精确于多边形）。"""
    if _poly_hit_poly(pa, pb):
        return 0.0
    best = math.inf
    for poly_a, poly_b in ((pa, pb), (pb, pa)):
        n = len(poly_a)
        for i in range(n):
            x1, y1 = poly_a[i]
            x2, y2 = poly_a[(i + 1) % n]
            for (qx, qy) in poly_b:
                d = _dist_point_seg(qx, qy, x1, y1, x2, y2)
                if d < best:
                    best = d
    return best


def _circumscribed_ngon(cx, cy, r, n=_ARC_SEGMENTS):
    """圆的外切 N 边形（顶点半径 r/cos(pi/n)：形状超集，保证不漏报）。"""
    rv = r / math.cos(math.pi / n)
    return [(cx + rv * math.cos(2.0 * math.pi * k / n),
             cy + rv * math.sin(2.0 * math.pi * k / n)) for k in range(n)]


def _convex_hull(points):
    """单调链凸包（自有实现；>=2 点）。"""
    pts = sorted(set((round(x, 9), round(y, 9)) for (x, y) in points))
    if len(pts) <= 2:
        return [tuple(p) for p in pts]
    def _half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and _cross(out[-2][0], out[-2][1],
                                          out[-1][0], out[-1][1],
                                          p[0], p[1]) <= 0:
                out.pop()
            out.append(p)
        return out
    lower = _half(pts)
    upper = _half(reversed(pts))
    return lower[:-1] + upper[:-1]


def _capsule_polygon(ax, ay, bx, by, r):
    """胶囊（线段 ⊕ 圆 r）超集：两端外切 N 边形的凸包。"""
    return _convex_hull(_circumscribed_ngon(ax, ay, r)
                        + _circumscribed_ngon(bx, by, r))


def _roundrect_polygon(cx, cy, hw, hh, r, rot_deg):
    """圆角矩形外切折线超集（局部坐标生成后旋转平移，凸包整形）。

    超集论证：圆角外切链顶点半径 rv=r/cos(pi/(2Q)) > r，链弦与真弧相切
    （弦心距=rv*cos(pi/(2Q))=r）→ 链在真弧外侧；直边中点在真边界上、
    相邻外切链端点在真边线外侧 → 凸包边不切入真形状。r=0 退化为精确
    矩形（4 顶点凸包）。
    """
    if r < 0.0 or 2.0 * r > min(2.0 * hw, 2.0 * hh) + 1e-12:
        raise CheckerBlocked("圆角半径越界（fail-closed）r=%r" % (r,))
    cs, sn = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))

    def _b(lx, ly):
        return (cx + lx * cs - ly * sn, cy + lx * sn + ly * cs)
    quarter = max(4, _ARC_SEGMENTS // 4)
    rv = r / math.cos(math.pi / (2.0 * quarter))
    pts = [_b(hw, 0.0), _b(0.0, hh), _b(-hw, 0.0), _b(0.0, -hh)]  # 边中点
    # 每角外弧覆盖各自朝外象限：NE 0..90°、SE -90..0°、SW 180..270°、
    # NW 90..180°（角度相对各自圆角中心）
    corners = (((hw - r, hh - r), 0.0),
               ((hw - r, -(hh - r)), -math.pi / 2.0),
               ((-(hw - r), -(hh - r)), math.pi),
               ((-(hw - r), hh - r), math.pi / 2.0))
    for (ccx, ccy), a0 in corners:
        for k in range(quarter + 1):
            ang = a0 + (math.pi / 2.0) * k / quarter
            pts.append(_b(ccx + rv * math.cos(ang),
                          ccy + rv * math.sin(ang)))
    return _convex_hull(pts)


# ---------------------------------------------------------------- 物项

class CheckItem:
    """checker 物项（凸多边形超集表示）。"""

    __slots__ = ("kind", "net", "layers", "poly", "src",
                 "conservative_approximation")

    def __init__(self, kind, net, layers, poly, src=None,
                 conservative_approximation=None):
        if not poly:
            raise CheckerBlocked("空多边形（fail-closed）")
        for (x, y) in poly:
            if not (math.isfinite(x) and math.isfinite(y)):
                raise CheckerBlocked("多边形顶点非有限（fail-closed）")
        self.kind = kind
        self.net = net
        self.layers = frozenset(layers)
        self.poly = tuple(poly)
        self.src = src if src is not None else {}
        self.conservative_approximation = conservative_approximation


def build_check_items(parsed_alt):
    """路径 B 解析产物 -> CheckItem 列表。"""
    items = []
    copper = set(parsed_alt["copper_layers"])
    for s in parsed_alt["segments"]:
        if not (s["width"] > 0.0):
            raise CheckerBlocked("走线零/负宽度（fail-closed）")
        items.append(CheckItem(
            "track", s["net"], {s["layer"]},
            _capsule_polygon(s["x1"], s["y1"], s["x2"], s["y2"],
                             s["width"] / 2.0),
            src={"uuid": s["uuid"]}))
    for v in parsed_alt["vias"]:
        if not (v["size"] > 0.0):
            raise CheckerBlocked("via 零/负尺寸（fail-closed）")
        items.append(CheckItem(
            "via", v["net"], set(v["layers"]),
            _circumscribed_ngon(v["x"], v["y"], v["size"] / 2.0),
            src={"uuid": v["uuid"]}))
    for p in parsed_alt["pads"]:
        if not p["layers"]:
            continue
        layers = set(p["layers"]) & copper
        items.append(_pad_check_item(p, layers))
    return items


def _pad_check_item(p, layers):
    shape, w, h = p["shape"], p["w_mm"], p["h_mm"]
    cx, cy, rot = p["x_mm"], p["y_mm"], p["rotation_deg"]
    approx = None
    if shape == "circle":
        # w!=h 畸形取 max 轴（与 precheck 同保守方向；独立实现）
        poly = _circumscribed_ngon(cx, cy, max(w, h) / 2.0)
    elif shape == "oval":
        r = min(w, h) / 2.0
        if w >= h:
            half = (w - h) / 2.0
            (ax, ay), (bx, by) = (cx - half, cy), (cx + half, cy)
        else:
            half = (h - w) / 2.0
            (ax, ay), (bx, by) = (cx, cy - half), (cx, cy + half)
        poly = _capsule_polygon(ax, ay, bx, by, r)
    elif shape == "rect":
        poly = _roundrect_polygon(cx, cy, w / 2.0, h / 2.0, 0.0, rot)
    elif shape == "roundrect":
        r = p["corner_radius_mm"]
        if r is None:
            raise CheckerBlocked("roundrect 缺半径（fail-closed）")
        poly = _roundrect_polygon(cx, cy, w / 2.0, h / 2.0, r, rot)
    elif shape == "custom":
        approx = ("custom 基元 backlog 未实现：顶点(经旋转)包围盒保守超集"
                  "（checker 独立实现）")
        prim = p["primitive_pts"] or []
        if prim:
            cs, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            board = [(cx + lx * cs - ly * sn, cy + lx * sn + ly * cs)
                     for (lx, ly) in prim]
        else:
            board = [(cx + sx * w / 2.0, cy + sy * h / 2.0)
                     for (sx, sy) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        xs = [q[0] for q in board]
        ys = [q[1] for q in board]
        poly = [(max(xs), max(ys)), (max(xs), min(ys)),
                (min(xs), min(ys)), (min(xs), max(ys))]
    else:
        raise CheckerBlocked("不支持形态（fail-closed）: %r" % (shape,))
    return CheckItem("pad", p["net_id"], layers, poly,
                     src={"pad_id": p["pad_id"]},
                     conservative_approximation=approx)


class IndependentGeometryChecker:
    """独立几何 checker（路径 B + 外切多边形引擎）。"""

    def __init__(self, check_items, net_table, protected_nets=(),
                 conservative_band_mm=CONSERVATIVE_BAND_MM):
        if net_table is None:
            raise CheckerBlocked(
                "net class 表缺失（fail-closed not_available——须 blocked）")
        self.items = list(check_items)
        self.net_table = net_table
        self.protected = set(protected_nets)
        self.band = float(conservative_band_mm)

    def check_via(self, net, layers, size, x, y):
        """via 候选独立复核。"""
        for (nm, v) in (("size", size), ("x", x), ("y", y)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) \
                    or not math.isfinite(v):
                raise CheckerBlocked("via 候选参数非法（fail-closed）"
                                     "%s=%r" % (nm, v))
        if not size > 0.0:
            raise CheckerBlocked("via 零/负尺寸（fail-closed）")
        cand = CheckItem("via", net, set(layers),
                         _circumscribed_ngon(x, y, size / 2.0),
                         src={"uuid": "(candidate-via)"})
        return self._check_candidate(cand)

    def check_pad(self, pad_dict, copper_layers):
        """pad 候选独立复核（pad_dict=路径 B pad 记录）。"""
        layers = set(pad_dict["layers"]) & set(copper_layers)
        cand = _pad_check_item(pad_dict, layers)
        return self._check_candidate(cand)

    def _check_candidate(self, cand):
        violations = []
        min_clear = None
        pairs = 0
        for it in self.items:
            if it.net == cand.net or it.net in self.protected:
                continue
            if not (cand.layers & it.layers):
                continue
            pairs += 1
            d = _poly_distance(cand.poly, it.poly)
            overlap = d <= 1e-12
            pred = 0.0 if overlap else d
            if min_clear is None or pred < min_clear:
                min_clear = pred
            required = self.net_table.required_clearance(cand.net, it.net)
            hard = overlap or pred < required - 1e-12
            band = (not hard) and pred < required + self.band - 1e-12
            if hard or band:
                violations.append({
                    "item_kind": it.kind,
                    "item_ref": it.src.get("uuid") or it.src.get("pad_id"),
                    "item_net": it.net,
                    "layer": sorted(cand.layers & it.layers)[0],
                    "pred_clearance_mm": None if overlap
                    else round(pred, 6),
                    "required_mm": round(required, 6),
                    "overlap": overlap,
                    "flag_class": "hard_violation" if hard
                    else "conservative_band",
                    "conservative_approximation": it.conservative_approximation,
                })
        return {
            "schema": _CHECKER_SCHEMA,
            "declared_date": DECLARED_DATE,
            "engine": "v4_1_circumscribed_polygon",
            "parser": "B_scan_regex",
            "candidate_kind": cand.kind,
            "candidate_net": cand.net,
            "verdict": "violation" if violations else "clean",
            "violations": sorted(violations, key=lambda v: (
                v["flag_class"] != "hard_violation",
                v["pred_clearance_mm"] if v["pred_clearance_mm"] is not None
                else -1.0, v["item_ref"] or "")),
            "min_foreign_clearance_mm": None if min_clear is None
            else round(min_clear, 6),
            "checked_pairs": pairs,
            "conservative_band_mm": self.band,
            "limitations": list(_LIMITATIONS),
        }

    def check_segment(self, net, layer, width, ax, ay, bx, by):
        """单段新几何独立复核 -> 机器可读结果。"""
        for (nm, v) in (("width", width), ("ax", ax), ("ay", ay),
                        ("bx", bx), ("by", by)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) \
                    or not math.isfinite(v):
                raise CheckerBlocked("候选参数非法（fail-closed）%s=%r"
                                     % (nm, v))
        if not width > 0.0:
            raise CheckerBlocked("候选零/负宽度（fail-closed）")
        cand = CheckItem("track", net, {layer},
                         _capsule_polygon(ax, ay, bx, by, width / 2.0),
                         src={"uuid": "(candidate)"})
        return self._check_candidate(cand)
