"""E0 严格 SVG 解析器（fail-closed，合同 data-pcbflow-schema="v4-svg-route-1"）。

只认白名单标签/属性（递归校验整棵树）；机器事实只从 data-* 属性提取
（routes/vias/relations/pads/keepouts/board_edge），数值按定点小数
（decimal.Decimal）解析。以下任一情况直接解析失败并给出 reason：
- 白名单外的标签或属性、命名空间不符；
- 未知 data-object-kind；
- route 对象缺任一必填 data-* 属性；
- path d 出现 M/L 以外命令、首命令非 M、点数 < 2；
- 坐标（path d、via cx/cy/r）不是 6 位定点小数；width/drill/ring 不是 3 位；
- sha256 属性不是 64 位小写 hex、根合同属性值不符、viewBox 形状不符；
- 元素 id 重复；
- line_type / relation_type 不在合同枚举内。

零子进程、零 argv、零 wall-clock、零网络。输出 facts dict 可直接 json 化。
颜色/stroke/fill/class 是纯视觉，解析器不据其产生机器事实。
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from decimal import Decimal

from .model import LINE_TYPES, RELATION_TYPES

SVG_NS = "http://www.w3.org/2000/svg"
SVG_SCHEMA = "v4-svg-route-1"
SVG_COORD_SYSTEM = "pcbflow-internal-mm"
SVG_Y_AXIS = "down-positive"
PRESERVE_AR = "xMidYMid meet"

DEC6_RE = re.compile(r"^-?\d+\.\d{6}$")
DEC3_RE = re.compile(r"^-?\d+\.\d{3}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONSTRAINT_REF_RE = re.compile(r"^C-[a-z][a-z-]*-\d{3}$")

OBJECT_KINDS = ("route_segment", "via", "route_relation",
                "board_edge", "pad", "keepout")

ROUTE_REQUIRED_ATTRS = (
    "data-route-id", "data-net-id", "data-relation-id", "data-line-type",
    "data-parent-id", "data-layer", "data-width-mm", "data-state",
    "data-source", "data-endpoint-start", "data-endpoint-end",
    "data-constraint-refs")
VIA_REQUIRED_ATTRS = (
    "data-via-id", "data-net-id", "data-parent-id", "data-from-layer",
    "data-to-layer", "data-drill-mm", "data-annular-ring-mm")
RELATION_REQUIRED_ATTRS = ("data-relation-id", "data-relation-type",
                           "data-member-ids")

# 白名单：标签 -> 属性集合（SVG 命名空间由标签本身的 {ns} 前缀强制）
TAGS = ("svg", "title", "style", "g", "rect", "circle", "path", "line",
        "text")
ATTR_WHITELIST = {
    "svg": {"version", "data-pcbflow-schema",
            "data-board-snapshot-sha256", "data-route-manifest-sha256",
            "data-coordinate-system", "data-y-axis", "viewBox",
            "preserveAspectRatio"},
    "title": {"id"},
    "style": set(),
    "g": {"id", "data-object-kind", "data-legend-version",
          "data-relation-id", "data-relation-type", "data-member-ids",
          "data-route-id", "data-net-id", "data-line-type",
          "data-parent-id", "data-layer", "data-width-mm", "data-state",
          "data-source", "data-endpoint-start", "data-endpoint-end",
          "data-constraint-refs"},
    "rect": {"id", "data-object-kind", "data-keepout-id", "data-layers",
             "data-pad-id", "data-net-id", "data-layer", "x", "y",
             "width", "height", "class", "fill", "fill-opacity", "stroke",
             "stroke-width", "stroke-dasharray"},
    "circle": {"id", "data-object-kind", "data-via-id", "data-net-id",
               "data-parent-id", "data-from-layer", "data-to-layer",
               "data-drill-mm", "data-annular-ring-mm", "cx", "cy", "r",
               "class", "fill", "stroke", "stroke-width",
               "stroke-dasharray"},
    "path": {"id", "d", "class"},
    "line": {"x1", "y1", "x2", "y2", "stroke", "stroke-width",
             "stroke-dasharray"},
    "text": {"x", "y", "class"},
}


class E0ParseError(ValueError):
    """严格解析失败（fail-closed）。"""


def _dec(text: str, pattern: re.Pattern, decimals: int, where: str) -> float:
    if not pattern.match(text):
        raise E0ParseError(
            f"{where}: 数值 {text!r} 不是 {decimals} 位定点小数")
    return float(Decimal(text))


def _dec6(text: str, where: str) -> float:
    return _dec(text, DEC6_RE, 6, where)


def _dec3(text: str, where: str) -> float:
    return _dec(text, DEC3_RE, 3, where)


def _local(tag: str, where: str) -> str:
    if not tag.startswith("{" + SVG_NS + "}"):
        raise E0ParseError(
            f"{where}: 标签 {tag!r} 不在 SVG 命名空间 {{{SVG_NS}}}")
    return tag[len(SVG_NS) + 2:]


def _split_ids(text: str, where: str) -> list:
    if text == "":
        return []
    ids = text.split(" ")
    for i in ids:
        if i == "":
            raise E0ParseError(f"{where}: id 列表 {text!r} 含空 token")
    return ids


def _split_csv(text: str, where: str) -> list:
    if text == "":
        return []
    ids = text.split(",")
    for i in ids:
        if i == "":
            raise E0ParseError(f"{where}: csv 列表 {text!r} 含空 token")
    return ids


def parse_path_d(d: str, where: str) -> list:
    """合同 path d：'M x y' 后跟若干 'L x y'，坐标一律 6 位定点小数。"""
    tokens = d.split(" ")
    if len(tokens) < 3 or len(tokens) % 3 != 0:
        raise E0ParseError(f"{where}: d 串 token 数不合法: {d!r}")
    pts = []
    for i in range(0, len(tokens), 3):
        cmd = tokens[i]
        if i == 0:
            if cmd != "M":
                raise E0ParseError(f"{where}: d 首命令必须是 M，实际 {cmd!r}")
        elif cmd != "L":
            raise E0ParseError(
                f"{where}: d 第 {i // 3 + 1} 命令必须是 L，实际 {cmd!r}")
        x = _dec6(tokens[i + 1], f"{where}.x[{i // 3}]")
        y = _dec6(tokens[i + 2], f"{where}.y[{i // 3}]")
        pts.append([x, y])
    if len(pts) < 2:
        raise E0ParseError(f"{where}: 折线至少 2 个点")
    return pts


def _parse_viewbox(text: str) -> list:
    parts = text.split(" ")
    if len(parts) != 4:
        raise E0ParseError(f"viewBox: 必须 4 个 token，实际 {text!r}")
    # 原点允许 '0' 或 '0.000000'（生产器写 '0 0'），但必须是零
    for i, name in ((0, "x"), (1, "y")):
        if not re.match(r"^-?0(\.\d+)?$", parts[i]) \
                or float(Decimal(parts[i])) != 0.0:
            raise E0ParseError(
                f"viewBox: {name} 必须为 0，实际 {parts[i]!r}")
    w = _dec6(parts[2], "viewBox.w")
    h = _dec6(parts[3], "viewBox.h")
    if w <= 0 or h <= 0:
        raise E0ParseError(f"viewBox: 宽高必须为正，实际 {text!r}")
    return [w, h]


def _require(attrs: dict, names, where: str) -> None:
    for n in names:
        if n not in attrs:
            raise E0ParseError(f"{where}: 缺必填属性 {n}")


def _whitelist_walk(el, seen_ids: set) -> None:
    """递归校验整棵树：命名空间、标签白名单、属性白名单、id 唯一。"""
    where = "root" if el.tag.endswith("svg") else "tree"
    tag = _local(el.tag, where)
    if tag not in TAGS:
        raise E0ParseError(f"白名单外标签 {tag!r}")
    unknown = set(el.attrib) - ATTR_WHITELIST[tag]
    if unknown:
        raise E0ParseError(f"{tag}: 白名单外属性 {sorted(unknown)}")
    eid = el.attrib.get("id")
    if eid is not None:
        if eid in seen_ids:
            raise E0ParseError(f"{tag}: 元素 id 重复 {eid!r}")
        seen_ids.add(eid)
    for child in el:
        _whitelist_walk(child, seen_ids)


def parse_svg(svg_text: str) -> dict:
    """严格解析 SVG 文本，返回机器 facts dict（可 json 化）。失败抛
    E0ParseError。"""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise E0ParseError(f"XML 语法错误: {exc}") from exc

    tag = _local(root.tag, "root")
    if tag != "svg":
        raise E0ParseError(f"根标签必须是 svg，实际 {tag!r}")
    attrs = dict(root.attrib)

    if attrs.get("version") != "1.1":
        raise E0ParseError(
            f"svg: version 期望 '1.1'，实际 {attrs.get('version')!r}")
    if attrs.get("data-pcbflow-schema") != SVG_SCHEMA:
        raise E0ParseError(
            f"svg: data-pcbflow-schema 期望 {SVG_SCHEMA}，"
            f"实际 {attrs.get('data-pcbflow-schema')!r}")
    for sha_attr in ("data-board-snapshot-sha256",
                     "data-route-manifest-sha256"):
        v = attrs.get(sha_attr, "")
        if not SHA256_RE.match(v):
            raise E0ParseError(f"svg: {sha_attr} 不是 64 位小写 hex: {v!r}")
    if attrs.get("data-coordinate-system") != SVG_COORD_SYSTEM:
        raise E0ParseError(
            f"svg: data-coordinate-system 期望 {SVG_COORD_SYSTEM}，"
            f"实际 {attrs.get('data-coordinate-system')!r}")
    if attrs.get("data-y-axis") != SVG_Y_AXIS:
        raise E0ParseError(
            f"svg: data-y-axis 期望 {SVG_Y_AXIS}，"
            f"实际 {attrs.get('data-y-axis')!r}")
    if attrs.get("preserveAspectRatio") != PRESERVE_AR:
        raise E0ParseError(
            f"svg: preserveAspectRatio 期望 {PRESERVE_AR}，"
            f"实际 {attrs.get('preserveAspectRatio')!r}")
    viewbox_wh = _parse_viewbox(attrs.get("viewBox", ""))

    seen_ids = set()
    _whitelist_walk(root, seen_ids)

    facts = {
        "schema": SVG_SCHEMA,
        "board_snapshot_sha256": attrs["data-board-snapshot-sha256"],
        "route_manifest_sha256": attrs["data-route-manifest-sha256"],
        "coordinate_system": SVG_COORD_SYSTEM,
        "y_axis": SVG_Y_AXIS,
        "viewbox_wh": viewbox_wh,
        "preserve_aspect_ratio": PRESERVE_AR,
        "legend_version": None,
        "board_edge": [],
        "routes": [],
        "vias": [],
        "relations": [],
        "pads": [],
        "keepouts": [],
    }

    for el in root:
        tag = _local(el.tag, "root-child")
        e_attrs = dict(el.attrib)
        where = f"{tag}#{e_attrs.get('id')}" if e_attrs.get("id") else tag
        kind = e_attrs.get("data-object-kind")
        if kind is not None and kind not in OBJECT_KINDS:
            raise E0ParseError(f"{where}: 未知 data-object-kind {kind!r}")

        if tag in ("style", "title"):
            continue
        if kind == "route_segment":
            facts["routes"].append(_parse_route_g(el, e_attrs, where))
        elif kind == "route_relation":
            facts["relations"].append(_parse_relation_g(e_attrs, where))
        elif kind == "via":
            facts["vias"].append(_parse_via_circle(e_attrs, where))
        elif kind == "pad":
            _require(e_attrs, ("data-pad-id", "data-net-id", "data-layer"),
                     where)
            facts["pads"].append({
                "pad_id": e_attrs["data-pad-id"],
                "net_id": e_attrs["data-net-id"],
                "layer": e_attrs["data-layer"]})
        elif kind == "keepout":
            _require(e_attrs, ("data-keepout-id", "data-layers"), where)
            facts["keepouts"].append({
                "keepout_id": e_attrs["data-keepout-id"],
                "layers": _split_ids(e_attrs["data-layers"],
                                     f"{where}.data-layers")})
        elif kind == "board_edge":
            facts["board_edge"].append({"object_kind": kind})
        elif e_attrs.get("data-legend-version") is not None:
            facts["legend_version"] = e_attrs["data-legend-version"]

    if facts["legend_version"] is None:
        raise E0ParseError("缺图例组 <g id=... data-legend-version=...>")
    if not facts["board_edge"]:
        raise E0ParseError("缺 board_edge 对象")

    facts["routes"].sort(key=lambda r: r["route_id"])
    facts["vias"].sort(key=lambda v: v["via_id"])
    facts["relations"].sort(key=lambda r: r["relation_id"])
    facts["pads"].sort(key=lambda p: p["pad_id"])
    facts["keepouts"].sort(key=lambda k: k["keepout_id"])
    return facts


def _parse_route_g(el, attrs: dict, where: str) -> dict:
    _require(attrs, ROUTE_REQUIRED_ATTRS, where)
    route_id = attrs["data-route-id"]
    if route_id == "":
        raise E0ParseError(f"{where}: data-route-id 不能为空")
    line_type = attrs["data-line-type"]
    if line_type not in LINE_TYPES:
        raise E0ParseError(f"{where}: 未知 data-line-type {line_type!r}")
    constraint_refs = _split_csv(attrs["data-constraint-refs"],
                                 f"{where}.data-constraint-refs")
    for ref in constraint_refs:
        if not CONSTRAINT_REF_RE.match(ref):
            raise E0ParseError(f"{where}: constraint ref {ref!r} 形状不符")
    width = _dec3(attrs["data-width-mm"], f"{where}.data-width-mm")
    if width <= 0:
        raise E0ParseError(f"{where}: data-width-mm 必须为正")

    kids = list(el)
    paths = [c for c in kids if _local(c.tag, where) == "path"]
    if len(kids) != 1 or len(paths) != 1:
        raise E0ParseError(
            f"{where}: route 组必须恰含 1 个 path 子元素")
    p_attrs = dict(paths[0].attrib)
    path_id = p_attrs.get("id", "")
    if path_id != f"geom-{route_id}":
        raise E0ParseError(
            f"{where}: path id 期望 'geom-{route_id}'，实际 {path_id!r}")
    polyline = parse_path_d(p_attrs.get("d", ""), f"{where}.path.d")

    endpoint_start = attrs["data-endpoint-start"]
    endpoint_end = attrs["data-endpoint-end"]
    if endpoint_start == "" or endpoint_end == "":
        raise E0ParseError(f"{where}: endpoint 不能为空")
    return {
        "route_id": route_id,
        "svg_id": attrs.get("id", ""),
        "path_id": path_id,
        "net_id": attrs["data-net-id"],
        "relation_ids": _split_ids(attrs["data-relation-id"],
                                   f"{where}.data-relation-id"),
        "line_type": line_type,
        "parent_id": attrs["data-parent-id"] or None,
        "layer": attrs["data-layer"],
        "width_mm": width,
        "state": attrs["data-state"],
        "source": attrs["data-source"],
        "endpoint_ids": [endpoint_start, endpoint_end],
        "constraint_refs": constraint_refs,
        "polyline_mm": polyline,
    }


def _parse_via_circle(attrs: dict, where: str) -> dict:
    _require(attrs, VIA_REQUIRED_ATTRS, where)
    via_id = attrs["data-via-id"]
    if via_id == "":
        raise E0ParseError(f"{where}: data-via-id 不能为空")
    drill = _dec3(attrs["data-drill-mm"], f"{where}.data-drill-mm")
    ring = _dec3(attrs["data-annular-ring-mm"],
                 f"{where}.data-annular-ring-mm")
    if drill <= 0 or ring < 0:
        raise E0ParseError(f"{where}: drill/ring 数值非法")
    cx = _dec6(attrs.get("cx", ""), f"{where}.cx")
    cy = _dec6(attrs.get("cy", ""), f"{where}.cy")
    _dec6(attrs.get("r", ""), f"{where}.r")  # r 是派生视觉量，仅校验格式
    return {
        "via_id": via_id,
        "svg_id": attrs.get("id", ""),
        "net_id": attrs["data-net-id"],
        "parent_id": attrs["data-parent-id"] or None,
        "from_layer": attrs["data-from-layer"],
        "to_layer": attrs["data-to-layer"],
        "drill_mm": drill,
        "annular_ring_mm": ring,
        "center_mm": [cx, cy],
    }


def _parse_relation_g(attrs: dict, where: str) -> dict:
    _require(attrs, RELATION_REQUIRED_ATTRS, where)
    rel_id = attrs["data-relation-id"]
    if rel_id == "":
        raise E0ParseError(f"{where}: data-relation-id 不能为空")
    rel_type = attrs["data-relation-type"]
    if rel_type not in RELATION_TYPES:
        raise E0ParseError(f"{where}: 未知 data-relation-type {rel_type!r}")
    members = _split_ids(attrs["data-member-ids"],
                         f"{where}.data-member-ids")
    if not members:
        raise E0ParseError(f"{where}: relation 成员不能为空")
    return {
        "relation_id": rel_id,
        "svg_id": attrs.get("id", ""),
        "relation_type": rel_type,
        "member_ids": members,
    }


def try_parse_svg(svg_text: str) -> tuple:
    """返回 (facts, None) 或 (None, reason)，便于负向判定。"""
    try:
        return parse_svg(svg_text), None
    except E0ParseError as exc:
        return None, str(exc)
