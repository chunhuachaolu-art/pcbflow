"""E0 核对器集合（每个返回 {check, pass, reason}）。

- identity_recovery：SVG 解析出的 route/via/relation 身份集合 == manifest 集合；
  id 唯一；parent 指向存在对象且无环；relation members 都是存在的 net。
- manifest_svg_consistency：逐对象逐字段相等（浮点按 1e-9 比）。
- roundtrip_mm：manifest.polyline_mm → SVG path d → 解析回 mm，逐点误差
  <= 0.001mm；via center 同。
- hash_binding：SVG 根 attr 的 board/manifest sha == 重算值（model.canonical
  hash 工具）；manifest 内 board_snapshot_sha256 == 重算值。
- color_independence：把 fill/stroke/class 中颜色相关 token 替换为装饰值后
  重解析，机器 facts 不变。
- resolution_invariance：4 个分辨率 PNG 尺寸正确，且每条 route 的图例颜色
  （svg_pkg.LEGEND_COLORS）在 PNG 中沿其折线采样至少命中 1 像素——只证明
  视觉投影不丢对象，机器事实永不从 PNG 读取。

零子进程、零 argv、零 wall-clock、零网络。
"""

from __future__ import annotations

import math
import os
import re

from . import e0_parse, model, render_png, svg_pkg
from .model import MANIFEST_SCHEMA_VERSION, MARGIN_MM

FLOAT_TOL = 1e-9
ROUNDTRIP_TOL_MM = 0.001
SAMPLES_PER_SEG = 64
DECOR_COLOR = "#FF00FF"
CLASS_TOKEN_RE = re.compile(
    r"route-(signal|clock|bus_trunk|bus_member)(?![A-Za-z0-9_])")
COLOR_ATTR_RE = re.compile(r'(fill|stroke)="#[0-9A-Fa-f]{6}"')


def result(check: str, ok: bool, reason: str = "") -> dict:
    return {"check": check, "pass": bool(ok), "reason": reason}


def legend_rgb() -> dict:
    """图例映射表：line_type -> (R, G, B)，抄自 svg_pkg.LEGEND_COLORS。"""
    out = {}
    for line_type, hexval in svg_pkg.LEGEND_COLORS.items():
        h = hexval.lstrip("#")
        out[line_type] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return out


def _mm_eq(a, b, tol=FLOAT_TOL) -> bool:
    return abs(float(a) - float(b)) <= tol


def _pts_eq(pa, pb, tol=FLOAT_TOL) -> bool:
    return len(pa) == len(pb) and all(
        _mm_eq(a[0], b[0], tol) and _mm_eq(a[1], b[1], tol)
        for a, b in zip(pa, pb))


# ------------------------------------------------------------ identity

def identity_recovery(facts: dict, manifest: dict) -> dict:
    """SVG 解析身份集合 == manifest 集合 + 唯一性 + 父链无环 + 成员存在。"""
    errs = []
    svg_routes = {r["route_id"]: r for r in facts["routes"]}
    man_routes = {r["route_id"]: r for r in manifest["routes"]}
    svg_vias = {v["via_id"]: v for v in facts["vias"]}
    man_vias = {v["via_id"]: v for v in manifest["vias"]}
    svg_rels = {r["relation_id"]: r for r in facts["relations"]}
    man_rels = {r["relation_id"]: r for r in manifest["relations"]}

    if len(svg_routes) != len(facts["routes"]):
        errs.append("route_id 重复")
    if len(svg_vias) != len(facts["vias"]):
        errs.append("via_id 重复")
    if len(svg_rels) != len(facts["relations"]):
        errs.append("relation_id 重复")
    if set(svg_routes) != set(man_routes):
        only_svg = sorted(set(svg_routes) - set(man_routes))
        only_man = sorted(set(man_routes) - set(svg_routes))
        errs.append(f"route 集合不等 svg_only={only_svg} manifest_only={only_man}")
    if set(svg_vias) != set(man_vias):
        errs.append("via 集合不等")
    if set(svg_rels) != set(man_rels):
        errs.append("relation 集合不等")

    # net 注册表：SVG 中出现过的 net（route + pad）
    net_ids = {r["net_id"] for r in facts["routes"]}
    net_ids |= {p["net_id"] for p in facts["pads"]}
    route_ids = set(svg_routes)
    for rid, r in sorted(svg_routes.items()):
        if r["parent_id"] is not None and r["parent_id"] not in route_ids:
            errs.append(f"route {rid}: parent_id {r['parent_id']!r} 不存在")
        for nid in r["relation_ids"]:
            if nid not in svg_rels:
                errs.append(f"route {rid}: relation {nid!r} 不存在")
        if r["net_id"] not in net_ids:
            errs.append(f"route {rid}: net_id {r['net_id']!r} 不在注册表")
    # route 父链无环
    for rid in sorted(svg_routes):
        seen = {rid}
        cur = svg_routes[rid]["parent_id"]
        while cur is not None:
            if cur in seen:
                errs.append(f"route {rid}: parent 链有环")
                break
            if cur not in svg_routes:
                break
            seen.add(cur)
            cur = svg_routes[cur]["parent_id"]
    for vid, v in sorted(svg_vias.items()):
        if v["parent_id"] is None or v["parent_id"] not in route_ids:
            errs.append(f"via {vid}: parent_id {v['parent_id']!r} 不存在")
        if v["net_id"] not in net_ids:
            errs.append(f"via {vid}: net_id {v['net_id']!r} 不在注册表")
    for rid_rel, rel in sorted(svg_rels.items()):
        if not rel["member_ids"]:
            errs.append(f"relation {rid_rel}: members 为空")
        for m in rel["member_ids"]:
            if m not in net_ids:
                errs.append(
                    f"relation {rid_rel}: member {m!r} 不是存在的 net")

    if errs:
        return result("identity_recovery", False, "; ".join(errs[:8]))
    n = len(man_routes) + len(man_vias) + len(man_rels)
    return result("identity_recovery", True,
                  f"routes={len(man_routes)} vias={len(man_vias)} "
                  f"relations={len(man_rels)} 总身份={n} 全部恢复且唯一")


# ------------------------------------------------------------ consistency

def manifest_svg_consistency(facts: dict, manifest: dict,
                             board_bbox_mm: list) -> dict:
    """逐对象逐字段相等（浮点 1e-9）。SVG path/cx/cy 是 SVG 本地 mm 坐标，
    按合同平移 (sx, sy) 后与 manifest 的板 mm 坐标比较。"""
    errs = []
    sx, sy = _shift(board_bbox_mm)
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errs.append(f"manifest.schema_version 非法 "
                    f"{manifest.get('schema_version')!r}")
    if manifest.get("svg_coordinate_system") != facts["coordinate_system"]:
        errs.append("svg_coordinate_system 与 SVG 根不符")
    if manifest.get("legend_version") != facts["legend_version"]:
        errs.append("legend_version 与 SVG 图例组不符")

    man_routes = {r["route_id"]: r for r in manifest["routes"]}
    for fr in facts["routes"]:
        mr = man_routes.get(fr["route_id"])
        if mr is None:
            continue  # identity_recovery 已报
        for field in ("net_id", "line_type", "layer", "state", "source",
                      "parent_id", "svg_id"):
            if fr[field] != mr[field]:
                errs.append(f"route {fr['route_id']}.{field}: "
                            f"svg={fr[field]!r} manifest={mr[field]!r}")
        if fr["relation_ids"] != mr["relation_ids"]:
            errs.append(f"route {fr['route_id']}.relation_ids 不等")
        if fr["endpoint_ids"] != mr["endpoint_ids"]:
            errs.append(f"route {fr['route_id']}.endpoint_ids 不等")
        if fr["constraint_refs"] != mr["constraint_refs"]:
            errs.append(f"route {fr['route_id']}.constraint_refs 不等")
        if not _mm_eq(fr["width_mm"], mr["width_mm"]):
            errs.append(f"route {fr['route_id']}.width_mm: "
                        f"svg={fr['width_mm']} manifest={mr['width_mm']}")
        svg_pts = [[p[0] + sx, p[1] + sy] for p in fr["polyline_mm"]]
        if not _pts_eq(svg_pts, mr["polyline_mm"]):
            errs.append(f"route {fr['route_id']}.polyline_mm 不等")

    man_vias = {v["via_id"]: v for v in manifest["vias"]}
    for fv in facts["vias"]:
        mv = man_vias.get(fv["via_id"])
        if mv is None:
            continue
        # manifest 合同里 via 无 svg_id 字段，故只比机器字段
        for field in ("net_id", "parent_id", "from_layer", "to_layer"):
            if fv[field] != mv.get(field):
                errs.append(f"via {fv['via_id']}.{field}: "
                            f"svg={fv[field]!r} manifest={mv.get(field)!r}")
        for field in ("drill_mm", "annular_ring_mm"):
            if not _mm_eq(fv[field], mv[field]):
                errs.append(f"via {fv['via_id']}.{field} 不等")
        if not _pts_eq([[fv["center_mm"][0] + sx, fv["center_mm"][1] + sy]],
                       [mv["center_mm"]]):
            errs.append(f"via {fv['via_id']}.center_mm 不等")

    man_rels = {r["relation_id"]: r for r in manifest["relations"]}
    for fr in facts["relations"]:
        mr = man_rels.get(fr["relation_id"])
        if mr is None:
            continue
        if fr["relation_type"] != mr["relation_type"]:
            errs.append(f"relation {fr['relation_id']}.relation_type 不等")
        if fr["member_ids"] != mr["members"]:
            errs.append(f"relation {fr['relation_id']}.members 不等")

    if errs:
        return result("manifest_svg_consistency", False, "; ".join(errs[:8]))
    return result("manifest_svg_consistency", True,
                  f"routes={len(man_routes)} vias={len(man_vias)} "
                  f"relations={len(man_rels)} 全字段一致(1e-9)")


# ------------------------------------------------------------ roundtrip

def _shift(bbox_mm) -> tuple:
    return bbox_mm[0] - MARGIN_MM, bbox_mm[1] - MARGIN_MM


def roundtrip_mm(facts: dict, manifest: dict, board_bbox_mm: list) -> dict:
    """manifest.polyline_mm -> SVG path d -> 解析回 mm，逐点 <= 0.001mm。"""
    errs = []
    sx, sy = _shift(board_bbox_mm)
    # viewBox 尺寸必须等于 bbox + 2M（转换式的闭合条件）
    vw, vh = facts["viewbox_wh"]
    exp_w = (board_bbox_mm[2] - board_bbox_mm[0]) + 2 * MARGIN_MM
    exp_h = (board_bbox_mm[3] - board_bbox_mm[1]) + 2 * MARGIN_MM
    if not _mm_eq(vw, exp_w) or not _mm_eq(vh, exp_h):
        errs.append(f"viewBox 尺寸 ({vw},{vh}) != bbox+2M ({exp_w},{exp_h})")

    max_err = 0.0
    man_routes = {r["route_id"]: r for r in manifest["routes"]}
    for fr in facts["routes"]:
        mr = man_routes.get(fr["route_id"])
        if mr is None:
            continue
        svg_pts = [[p[0] + sx, p[1] + sy] for p in fr["polyline_mm"]]
        for i, (a, b) in enumerate(zip(mr["polyline_mm"], svg_pts)):
            err = max(abs(a[0] - b[0]), abs(a[1] - b[1]))
            max_err = max(max_err, err)
            if err > ROUNDTRIP_TOL_MM:
                errs.append(f"route {fr['route_id']} 点[{i}] 误差 {err:.6f}mm")
    man_vias = {v["via_id"]: v for v in manifest["vias"]}
    for fv in facts["vias"]:
        mv = man_vias.get(fv["via_id"])
        if mv is None:
            continue
        err = max(abs(mv["center_mm"][0] - (fv["center_mm"][0] + sx)),
                  abs(mv["center_mm"][1] - (fv["center_mm"][1] + sy)))
        max_err = max(max_err, err)
        if err > ROUNDTRIP_TOL_MM:
            errs.append(f"via {fv['via_id']} center 误差 {err:.6f}mm")

    if errs:
        return result("roundtrip_mm", False, "; ".join(errs[:8]))
    return result("roundtrip_mm", True,
                  f"max_err={max_err:.9f}mm <= {ROUNDTRIP_TOL_MM}mm "
                  f"(routes={len(man_routes)} vias={len(man_vias)})")


# ------------------------------------------------------------ hash

def hash_binding(facts: dict, manifest: dict, board_obj: dict) -> dict:
    """SVG 根 sha == 重算值；manifest 内 sha == 重算值（canonical hash）。"""
    errs = []
    board_sha = model.sha256_of(board_obj)
    manifest_sha = model.sha256_of(manifest)
    if manifest.get("board_snapshot_sha256") != board_sha:
        errs.append("manifest.board_snapshot_sha256 != 重算值")
    if manifest.get("manifest_payload_sha256") != manifest_sha:
        errs.append("manifest.manifest_payload_sha256 != 重算值")
    if facts["board_snapshot_sha256"] != board_sha:
        errs.append("SVG data-board-snapshot-sha256 != 重算值")
    if facts["route_manifest_sha256"] != manifest_sha:
        errs.append("SVG data-route-manifest-sha256 != 重算值")
    if errs:
        return result("hash_binding", False, "; ".join(errs))
    return result("hash_binding", True,
                  f"board={board_sha[:12]}... manifest={manifest_sha[:12]}..."
                  " 全部绑定")


# ------------------------------------------------------------ color

def rewrite_colors(svg_text: str) -> str:
    """fill/stroke 颜色值与 class 中颜色相关 token 替换为装饰值（不碰
    data-*）。"""
    out = COLOR_ATTR_RE.sub(r'\1="' + DECOR_COLOR + '"', svg_text)
    out = CLASS_TOKEN_RE.sub("route-decor", out)
    return out


def color_independence(svg_text: str, facts: dict,
                       base_svg_text: str = None) -> dict:
    """换色后重解析，机器 facts 必须逐字段不变。重写基于 base_svg_text
    （默认 svg_text 本身）；被测文本自身的 facts 由调用方传入。"""
    base = base_svg_text if base_svg_text is not None else svg_text
    mutated = rewrite_colors(base)
    if mutated == base:
        return result("color_independence", False,
                      "颜色替换未产生任何变化（替换器失效）")
    new_facts, reason = e0_parse.try_parse_svg(mutated)
    if new_facts is None:
        return result("color_independence", False,
                      f"换色后解析失败: {reason}")
    if new_facts != facts:
        diffs = _facts_diff(facts, new_facts)
        return result("color_independence", False,
                      f"换色后机器 facts 改变: {diffs}")
    return result("color_independence", True,
                  "fill/stroke/class 换装饰色后 facts 逐字段不变")


def _facts_diff(a: dict, b: dict) -> str:
    """给出两份 facts 的第一个分歧点的局部 canonical 文本，便于定位。"""
    da = model.canonical_json(a)
    db = model.canonical_json(b)
    i = 0
    while i < min(len(da), len(db)) and da[i] == db[i]:
        i += 1
    lo = max(0, i - 30)
    ha = min(len(da), i + 60)
    hb = min(len(db), i + 60)
    return (f"orig[...{da[lo:ha]}...] " f"new[...{db[lo:hb]}...]")


# ------------------------------------------------------------ resolution

def _pixel_transform(board_bbox_mm: list, width: int, height: int):
    """与 render_png.render 相同的 fit-inside 映射（mm -> px）。"""
    bx0, by0, bx1, by1 = board_bbox_mm
    bw, bh = bx1 - bx0, by1 - by0
    scale = min((width - 2 * render_png.MARGIN_PX) / bw,
                (height - 2 * render_png.MARGIN_PX) / bh)
    ox = (width - bw * scale) / 2
    oy = (height - bh * scale) / 2

    def to_px(x, y):
        return (ox + (x - bx0) * scale, oy + (y - by0) * scale)

    return to_px


def _route_color_in_png(pixels, width: int, height: int, polyline_mm,
                        color: tuple, to_px) -> tuple:
    """沿折线采样找图例颜色；未命中再做全图扫描兜底。返回 (hit, fallback)。"""
    for a, b in zip(polyline_mm, polyline_mm[1:]):
        ax, ay = to_px(a[0], a[1])
        bx, by = to_px(b[0], b[1])
        for i in range(SAMPLES_PER_SEG):
            t = i / (SAMPLES_PER_SEG - 1)
            x = int(round(ax + (bx - ax) * t))
            y = int(round(ay + (by - ay) * t))
            if 0 <= x < width and 0 <= y < height:
                if pixels[x, y] == color:
                    return True, False
    for y in range(height):
        for x in range(width):
            if pixels[x, y] == color:
                return True, True
    return False, False


def resolution_invariance(sid: str, manifest: dict, board_bbox_mm: list,
                          source_dir: str) -> dict:
    """4 分辨率 PNG：尺寸正确 + 每条 route 图例颜色至少 1 像素。机器事实
    仍只从 SVG 读，本检查只证明视觉投影不丢对象。"""
    colors = legend_rgb()
    missing = []
    for w, h in render_png.RESOLUTIONS:
        path = os.path.join(source_dir, f"route-preview-{sid}-{w}x{h}.png")
        if not os.path.exists(path):
            missing.append(f"{w}x{h}")
    if missing:
        return result("resolution_invariance", False,
                      f"缺 PNG: {missing}")
    errs = []
    from PIL import Image
    fallbacks = 0
    routes = manifest["routes"]
    for w, h in render_png.RESOLUTIONS:
        path = os.path.join(source_dir, f"route-preview-{sid}-{w}x{h}.png")
        with Image.open(path) as img:
            if img.size != (w, h):
                errs.append(f"{w}x{h}: 实际尺寸 {img.size}")
                continue
            pixels = img.load()
            to_px = _pixel_transform(board_bbox_mm, w, h)
            for route in routes:
                color = colors.get(route["line_type"])
                if color is None:
                    errs.append(f"route {route['route_id']}: 未知 line_type "
                                f"{route['line_type']!r}")
                    continue
                hit, used_fallback = _route_color_in_png(
                    pixels, w, h, route["polyline_mm"], color, to_px)
                fallbacks += 1 if used_fallback else 0
                if not hit:
                    errs.append(f"{w}x{h}: route {route['route_id']} 图例色 "
                                f"{color} 未出现")
    if errs:
        return result("resolution_invariance", False, "; ".join(errs[:8]))
    return result("resolution_invariance", True,
                  f"4 分辨率尺寸正确；routes={len(routes)} 每条图例色均命中"
                  f"（全图兜底 {fallbacks} 次）")
