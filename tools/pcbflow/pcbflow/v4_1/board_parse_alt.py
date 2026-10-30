"""pcbflow.v4_1.board_parse_alt -- 解析路径 B（独立行扫描；零依赖路径 A
与 pcbflow.sexpr_min——交叉对拍用第二实现，对拍不一致=blocked 登记）。

实现机制（与路径 A 的树解析结构性不同）：单趟扫描构建「括号深度图」
(每个字符的括号深度)与顶层节点 span，再在 span 内用受限正则提取字段；
字段提取一律锚定节点起始 token，避免误匹配嵌套同名节点。

产出结构与 board_parse.parse_board_text 完全同形（逐字段量化 6dp 对拍）。
校验规则与路径 A 相同（fail-closed：缺字段/非法枚举/非有限数/退化/离格
>6 位小数），实现独立。

零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math
import re

from . import KICAD_MAX_COORD_DECIMALS

__all__ = ["BoardParseAltError", "parse_board_text_alt"]

SUPPORTED_PAD_SHAPES = ("circle", "oval", "rect", "roundrect", "custom")


class BoardParseAltError(ValueError):
    """路径 B 解析 fail-closed。"""


_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _num(tok, what, is_ratio=False):
    """数值 token 校验：格式/有限性/离格。

    mm 量纲值（坐标/尺寸）限 6 位小数（KiCad 1nm 网格）；无量纲比率
    （roundrect_rratio，KiCad 全精度序列化，如 0.1923076923）不限。
    """
    if tok is None or not _NUM_RE.match(tok):
        raise BoardParseAltError("%s 非数值 token（fail-closed）: %r"
                                 % (what, tok))
    if not is_ratio and "." in tok             and len(tok.split(".", 1)[1]) > KICAD_MAX_COORD_DECIMALS:
        raise BoardParseAltError(
            "%s 坐标离格（fail-closed）：小数位 > %d: %r"
            % (what, KICAD_MAX_COORD_DECIMALS, tok))
    v = float(tok)
    if not math.isfinite(v):
        raise BoardParseAltError("%s 非有限数（fail-closed）" % what)
    return v


def _q(v):
    return round(float(v), 6)


def _depth_map(text):
    """逐字符括号深度图 + 根 span + 根直接子节点 (tag, start, end) 列表。

    depths[i] 语义：'('=开括后自身深度；')' =闭括前自身深度；其余字符
    =所在层深度。深度 k 节点 span=其 '(' 起，至闭括（含）——闭括后首
    字符深度回落至 <k。跳过字符串字面量（不改变深度）。
    """
    depths = bytearray(len(text))
    nodes = []
    roots = []
    stack = []
    i, n, depth = 0, len(text), 0

    def _mark(idx, d):
        depths[idx] = d if d < 255 else 255

    while i < n:
        c = text[i]
        if c == '"':
            _mark(i, depth)
            i += 1
            while i < n:
                _mark(i, depth)
                if text[i] == "\\":
                    _mark(i + 1, depth)
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif c == "(":
            depth += 1
            _mark(i, depth)
            stack.append(i)
        elif c == ")":
            _mark(i, depth)
            if not stack:
                raise BoardParseAltError("括号不平衡（fail-closed）offset=%d"
                                         % i)
            start = stack.pop()
            depth -= 1
            if depth <= 1:
                # depth->0 = 根自身；depth->1 = 根直接子节点
                m = re.match(r"\(([\w*-]+)", text[start:i + 1])
                if m and m.group(1) == "kicad_pcb":
                    roots.append((m.group(1), start, i + 1))
                elif m:
                    nodes.append((m.group(1), start, i + 1))
        else:
            _mark(i, depth)
        i += 1
    if stack:
        raise BoardParseAltError("括号不平衡（fail-closed）：未闭合")
    return depths, nodes, roots


def _field(block, tag, arity):
    """节点块内锚定子节点 (tag v1 .. vN) 的值 token 列表（首个匹配）。

    值 token 数可多于 arity（如 pad (at x y rot)）——返回全部 token，
    调用方按需取前 arity 个；闭括锚定防止吞嵌套。
    """
    m = re.search(r"\(" + re.escape(tag) + r"((?:\s+(?:\"(?:[^\"\\]|\\.)*\""
                  r"|[-\w.]+))+)\s*\)", block)
    if m is None:
        return None
    raw = m.group(1)
    toks = re.findall(r"\"(?:[^\"\\]|\\.)*\"|[-\w.]+", raw)
    return [t[1:-1] if t.startswith('"') else t for t in toks]


def _field_opt_sub(block, tag):
    """(tag "str") 型子节点字符串值（如 net/class）。"""
    m = re.search(r"\(" + re.escape(tag) + r"\s+\"((?:[^\"\\]|\\.)*)\"\)",
                  block)
    return m.group(1) if m else None


def _span_at_depth(text, depths, lo, hi, depth_want):
    """[lo,hi) 内开括深度==depth_want 的节点 span 列表 (tag, start, end)。

    span 终点=闭括后首字符（深度回落 <depth_want）；tag 与节点级字符
    深度==depth_want，子节点>depth_want。
    """
    out = []
    i = lo
    n = hi
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
            i += 1  # 跳过闭引号（否则闭引号被再次当作开引号吞掉后续节点）
            continue
        if c == "(" and depths[i] == depth_want:
            m = re.match(r"\(([\w*-]+)", text[i:])
            if not m:
                i += 1
                continue
            j = i + 1
            while j < n and depths[j] >= depth_want:
                j += 1
            out.append((m.group(1), i, j))
            i = j
            continue
        i += 1
    return out


def parse_board_text_alt(text):
    """kicad_pcb 文本 -> 结构模型（路径 B；fail-closed）。"""
    depths, nodes, roots = _depth_map(text)
    if len(roots) != 1:
        raise BoardParseAltError("expect exactly one kicad_pcb root, got %d"
                                 % len(roots))
    copper_layers = _parse_copper_layers(text, depths, nodes)
    segments, vias, pads, unsupported = [], [], [], []
    for (tag, s, e) in nodes:
        if tag == "segment":
            segments.append(_parse_segment(text[s:e]))
        elif tag == "via":
            vias.append(_parse_via(text[s:e], copper_layers))
        elif tag == "footprint":
            _parse_footprint(text, depths, s, e, copper_layers, pads,
                             unsupported)
    return {
        "parser": "B_scan_regex",
        "copper_layers": copper_layers,
        "segments": segments,
        "vias": vias,
        "pads": pads,
        "unsupported_items": unsupported,
        "stats": {
            "segment_count": len(segments),
            "via_count": len(vias),
            "pad_count": len(pads),
            "unsupported_count": len(unsupported),
        },
    }


def _parse_copper_layers(text, depths, nodes):
    for (tag, s, e) in nodes:
        if tag == "layers":
            names = re.findall(r"\(\d+\s+\"([^\"]+)\"", text[s:e])
            out = [nm for nm in names
                   if nm.endswith(".Cu") and nm != "Edge.Cuts"]
            if not out:
                raise BoardParseAltError("板铜层表为空（fail-closed）")
            return out
    raise BoardParseAltError("板缺 (layers) 节点（fail-closed）")


def _parse_segment(block):
    st = _field(block, "start", 2)
    en = _field(block, "end", 2)
    w = _field(block, "width", 1)
    nt = _field_opt_sub(block, "net")
    uid = _field(block, "uuid", 1)
    ly = _field(block, "layer", 1)
    if None in (st, en, w, nt, uid, ly):
        raise BoardParseAltError("segment 缺必需字段（fail-closed）")
    return {
        "uuid": uid[0],
        "net": nt,
        "layer": ly[0].strip('"'),
        "width": _num(w[0], "segment.width"),
        "x1": _num(st[0], "segment.start.x"),
        "y1": _num(st[1], "segment.start.y"),
        "x2": _num(en[0], "segment.end.x"),
        "y2": _num(en[1], "segment.end.y"),
    }


def _via_span_layers_b(span, copper_layers):
    """路径 B 独立实现的 via 跨度展开（栈序闭区间，含中间层）。

    与路径 A（board_parse 经 layerstack.via_span_layers）结构性双实现：
    本函数不 import layerstack，独立做「栈序索引 + 闭区间切片」——
    交叉对拍不一致=blocked 的独立性纪律不破。语义见 layerstack 模块
    文档（E2：(F.Cu B.Cu)=全栈；盲/埋孔含中间层）。
    """
    names = list(copper_layers)
    if len(span) != 2:
        raise BoardParseAltError("via layers 跨度非法（fail-closed）: %r"
                                 % (span,))
    for lv in span:
        if lv not in names:
            raise BoardParseAltError("via 层 %r 不在板铜层表（fail-closed）"
                                     % (lv,))
    ia, ib = names.index(span[0]), names.index(span[1])
    lo, hi = (ia, ib) if ia <= ib else (ib, ia)
    return names[lo:hi + 1]


def _parse_via(block, copper_layers):
    at = _field(block, "at", 2)
    size = _field(block, "size", 1)
    lys = _field(block, "layers", 2)
    nt = _field_opt_sub(block, "net")
    uid = _field(block, "uuid", 1)
    if None in (at, size, lys, nt, uid):
        raise BoardParseAltError("via 缺必需字段（fail-closed）")
    span = [t.strip('"') for t in lys]
    layers = _via_span_layers_b(span, copper_layers)
    for lv in layers:
        if lv not in copper_layers:
            raise BoardParseAltError("via 层 %r 不在板铜层表（fail-closed）"
                                     % (lv,))
    return {
        "uuid": uid[0],
        "net": nt,
        "x": _num(at[0], "via.at.x"),
        "y": _num(at[1], "via.at.y"),
        "size": _num(size[0], "via.size"),
        "layers": sorted(layers),
    }


def _parse_footprint(text, depths, s, e, copper_layers, pads_out,
                     unsupported_out):
    fp = text[s:e]
    m = re.search(r"\(property\s+\"Reference\"\s+\"((?:[^\"\\]|\\.)*)\"",
                  fp)
    if m is None:
        raise BoardParseAltError("footprint 缺 Reference property（fail-closed）")
    ref = m.group(1)
    fp_depth = depths[s]
    fat = None
    for (tag2, ps2, pe2) in _span_at_depth(text, depths, s, e, fp_depth + 1):
        if tag2 == "at":
            fat = _field(text[ps2:pe2], "at", 2)
            break
    if fat is None:
        raise BoardParseAltError("footprint %s 缺 (at)（fail-closed）" % ref)
    fx, fy = _num(fat[0], "footprint.at.x"), _num(fat[1], "footprint.at.y")
    # footprint 自身旋转=其直接子 (at) 第三值（property/pad 内 (at) 不算）
    frot = _num(fat[2], "footprint.at.rot") if len(fat) >= 3 else 0.0
    # footprint 子节点（pad）深度 = footprint 自身开括深度 + 1
    for (tag, ps, pe) in _span_at_depth(text, depths, s, e, fp_depth + 1):
        if tag != "pad":
            continue
        pb = text[ps:pe]
        pm = re.match(r'\(pad\s+"((?:[^"\\]|\\.)*)"\s+(\S+)\s+(\S+)', pb)
        if pm is None:
            raise BoardParseAltError(
                "pad 头部格式非法（fail-closed）: %r" % pb[:60])
        pid, ptype, shape = pm.group(1), pm.group(2), pm.group(3)
        pad_id = "%s.%s" % (ref, pid)
        if shape not in SUPPORTED_PAD_SHAPES:
            raise BoardParseAltError(
                "pad %s 非法/不支持形态枚举（fail-closed）: %r"
                % (pad_id, shape))
        pat = _field(pb, "at", 2)
        psize = _field(pb, "size", 2)
        if pat is None or psize is None:
            raise BoardParseAltError(
                "pad %s 缺 at/size（fail-closed）" % pad_id)
        px, py = _num(pat[0], "pad.at.x"), _num(pat[1], "pad.at.y")
        # pad 相对旋转=pad 块内首个 (at) 第三值（KiCad >= 6 footprint 相对角）
        prot = _num(pat[2], "pad.at.rot") if len(pat) >= 3 else 0.0
        w, h = _num(psize[0], "pad.size.w"), _num(psize[1], "pad.size.h")
        if w <= 0.0 or h <= 0.0:
            raise BoardParseAltError(
                "pad %s 形状退化：零/负尺寸（fail-closed）" % pad_id)
        net = _field_opt_sub(pb, "net") or ""
        plys = re.search(r"\(layers((?:\s+\"[^\"]*\")+)\s*\)", pb)
        layers = []
        if plys is None:
            raise BoardParseAltError(
                "pad %s 缺 (layers)（fail-closed）" % pad_id)
        listed = re.findall(r'"([^"]*)"', plys.group(1))
        copper = [lv for lv in listed if lv.endswith(".Cu")]
        if not copper:
            layers = []
        elif "*.Cu" in copper:
            layers = list(copper_layers)
        else:
            for lv in copper:
                if lv not in copper_layers:
                    raise BoardParseAltError(
                        "pad %s 层 %r 不在板铜层表（fail-closed）"
                        % (pad_id, lv))
                layers.append(lv)
        radius = None
        if shape == "roundrect":
            rr = _field(pb, "roundrect_rratio", 1)
            if rr is None:
                raise BoardParseAltError(
                    "pad %s roundrect 缺 roundrect_rratio（fail-closed）"
                    % pad_id)
            ratio = _num(rr[0], "pad.rratio", is_ratio=True)
            if not (0.0 <= ratio <= 0.5):
                raise BoardParseAltError(
                    "pad %s 圆角比越界（fail-closed）: %r" % (pad_id, ratio))
            radius = ratio * min(w, h)
        total_rot = frot + prot
        rot_rad = math.radians(frot)
        cs, sn = math.cos(rot_rad), math.sin(rot_rad)
        ax = fx + px * cs + py * sn
        ay = fy - px * sn + py * cs
        prim_pts = None
        if shape == "custom":
            pts = re.findall(
                r"\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)", pb)
            prim_pts = [[_q(float(a)), _q(float(b))] for (a, b) in pts]
        rec = {
            "pad_id": pad_id,
            "pad_type": ptype,
            "shape": shape,
            "net_id": net,
            "x_mm": _q(ax),
            "y_mm": _q(ay),
            "w_mm": w,
            "h_mm": h,
            "rotation_deg": _q(total_rot),
            "corner_radius_mm": None if radius is None else _q(radius),
            "layers": sorted(layers),
            "primitive_pts": prim_pts,
        }
        pads_out.append(rec)
        if shape == "custom":
            unsupported_out.append({
                "pad_id": pad_id,
                "net_id": net,
                "layers": rec["layers"],
                "reason": "custom 基元 backlog 未实现（任务书 §3 E1）；"
                          "geometry 层以基元顶点包围盒为保守超集建模",
                "primitive_pt_count": len(prim_pts or ()),
            })
