"""pcbflow.v4_1.board_parse -- 解析路径 A（s-expr 树；只读复用
pcbflow.sexpr_min，零改动既有模块）。

从 kicad_pcb 文本提取 clearance 域内事实：

- segment（走线）：uuid/net/layer/width/start/end；
- via：uuid/net/size/位置/层跨度（layers l1 l2；E2 起跨度=栈序闭区间
  展开，含中间层——盲孔 (F.Cu In2.Cu) 在 4 层栈含 In1.Cu，见
  layerstack.via_span_layers）；
- footprint -> pad：焊盘号/类型/形态/局部坐标+局部旋转/尺寸/圆角比/
  铜层/网；footprint 旋转叠加（KiCad >= 6 语义：pad (at) 第三元为
  footprint 相对角，总角 = footprint 角 + pad 相对角）；
- 板铜层表（(layers ...) 内 *.Cu）；
- custom 基元：登记 unsupported_items（backlog），同时提取基元顶点供
  保守包围盒建模（geometry.PadGeom(shape="custom")）。

校验全部 fail-closed（抛 BoardParseError，不静默）：

- 节点缺必需子节点（footprint 缺 at/Reference、pad 缺 at/size/layers、
  segment/via 缺 start/end/width/layer/net/uuid…）；
- 非法形态枚举（circle/oval/rect/roundrect/custom 之外）；
- 非有限数（NaN/Inf）与非数值 token；
- 形状退化（零/负尺寸、圆角比越界 [0, 0.5]、负半径）；
- 坐标离格（KiCad 内部单位 1nm → 文本坐标小数位 > 6 不可表示）。

零 IO（输入为文本字符串）、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math
import re

from .. import sexpr_min
from . import KICAD_MAX_COORD_DECIMALS
from .layerstack import via_span_layers

__all__ = ["BoardParseError", "parse_board_text", "SUPPORTED_PAD_SHAPES"]

SUPPORTED_PAD_SHAPES = ("circle", "oval", "rect", "roundrect", "custom")

_NUM_TOKEN_RE = re.compile(r"^-?\d+(\.\d+)?$")
_COPPER_SUFFIX = ".Cu"


class BoardParseError(ValueError):
    """板解析 fail-closed。"""


def _check_num_token(tok, what, allow_six_dp=True):
    """数值 token 校验：格式/有限性/离格（>6 位小数不可表示）。

    仅适用于 mm 量纲值（坐标/尺寸——KiCad 1nm 网格）；无量纲比率
    （roundrect_rratio 等）走 _check_ratio_token（KiCad 全精度序列化）。
    """
    if not isinstance(tok, str) or not _NUM_TOKEN_RE.match(tok):
        raise BoardParseError("%s 非数值 token（fail-closed）: %r"
                              % (what, tok))
    if "." in tok:
        dp = len(tok.split(".", 1)[1])
        if dp > KICAD_MAX_COORD_DECIMALS:
            raise BoardParseError(
                "%s 坐标离格（fail-closed）：小数位 %d > KiCad 1nm 上限 %d: %r"
                % (what, dp, KICAD_MAX_COORD_DECIMALS, tok))
    v = float(tok)
    if not math.isfinite(v):
        raise BoardParseError("%s 非有限数（fail-closed）: %r" % (what, tok))
    del allow_six_dp
    return v


def _check_ratio_token(tok, what):
    """无量纲比率 token 校验（格式/有限性；无小数位限制）。"""
    if not isinstance(tok, str) or not _NUM_TOKEN_RE.match(tok):
        raise BoardParseError("%s 非数值 token（fail-closed）: %r"
                              % (what, tok))
    v = float(tok)
    if not math.isfinite(v):
        raise BoardParseError("%s 非有限数（fail-closed）: %r" % (what, tok))
    return v


def _find_first(node, tag):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == tag:
            return c
    return None


def _require(node, tags, what):
    out = []
    for t in tags:
        v = _find_first(node, t)
        if v is None:
            raise BoardParseError("%s 缺必需子节点 (fail-closed): %r"
                                  % (what, t))
        out.append(v)
    return out


def _q(v):
    return round(float(v), 6)


# ---------------------------------------------------------------- 主入口

def parse_board_text(text):
    """kicad_pcb 文本 -> 结构模型（纯函数，fail-closed）。"""
    roots = [n for n in sexpr_min.parse(text)
             if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise BoardParseError("expect exactly one kicad_pcb root, got %d"
                              % len(roots))
    root = roots[0]
    copper_layers = _parse_copper_layers(root)
    segments, vias, pads, unsupported = [], [], [], []
    for c in root[1:]:
        if not isinstance(c, list) or not c:
            continue
        tag = c[0]
        if tag == "segment":
            segments.append(_parse_segment(c))
        elif tag == "via":
            vias.append(_parse_via(c, copper_layers))
        elif tag == "footprint":
            _parse_footprint(c, copper_layers, pads, unsupported)
    return {
        "parser": "A_tree_sexpr_min",
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


def _parse_copper_layers(root):
    layers_node = _find_first(root, "layers")
    out = []
    if layers_node is None:
        raise BoardParseError("板缺 (layers) 节点（fail-closed）")
    for sub in layers_node[1:]:
        if isinstance(sub, list) and len(sub) >= 2 \
                and isinstance(sub[1], str) and sub[1].endswith(_COPPER_SUFFIX) \
                and sub[1] != "Edge.Cuts":
            out.append(sub[1])
    if not out:
        raise BoardParseError("板铜层表为空（fail-closed）")
    return out


def _parse_segment(node):
    st, en, w, ly, nt, uid = _require(
        node, ("start", "end", "width", "layer", "net", "uuid"), "segment")
    return {
        "uuid": uid[1],
        "net": nt[1],
        "layer": ly[1],
        "width": _check_num_token(w[1], "segment.width"),
        "x1": _check_num_token(st[1], "segment.start.x"),
        "y1": _check_num_token(st[2], "segment.start.y"),
        "x2": _check_num_token(en[1], "segment.end.x"),
        "y2": _check_num_token(en[2], "segment.end.y"),
    }


def _parse_via(node, copper_layers):
    at, size, lys, nt, uid = _require(
        node, ("at", "size", "layers", "net", "uuid"), "via")
    if len(lys) < 3:
        raise BoardParseError("via layers 跨度不足（fail-closed）: %r"
                              % (lys,))
    span = [lys[1], lys[2]]
    # E2 多层跨度语义（layerstack.via_span_layers）：跨度 = 栈序闭区间
    # （含中间层）。(F.Cu B.Cu) = 全部铜层（与 E1 行为一致）；盲/埋孔
    # 如 (F.Cu In2.Cu) 在 4 层栈 = {F.Cu, In1.Cu, In2.Cu}（E1 旧实现
    # 只取两端点=多层语义缺口，E2 修复）。
    layers = via_span_layers(span[0], span[1], copper_layers)
    for lv in layers:
        if lv not in copper_layers:
            raise BoardParseError("via 层 %r 不在板铜层表（fail-closed）"
                                  % (lv,))
    return {
        "uuid": uid[1],
        "net": nt[1],
        "x": _check_num_token(at[1], "via.at.x"),
        "y": _check_num_token(at[2], "via.at.y"),
        "size": _check_num_token(size[1], "via.size"),
        "layers": sorted(layers),
    }


def _footprint_reference(fp):
    for sub in fp[1:]:
        if isinstance(sub, list) and sub and sub[0] == "property" \
                and len(sub) >= 3 and sub[1] == "Reference":
            return sub[2]
    raise BoardParseError("footprint 缺 Reference property（fail-closed）")


def _footprint_at(fp, ref):
    at = _find_first(fp, "at")
    if at is None or len(at) < 3:
        raise BoardParseError("footprint %s 缺 (at)（fail-closed）" % ref)
    fx = _check_num_token(at[1], "footprint.at.x")
    fy = _check_num_token(at[2], "footprint.at.y")
    rot = 0.0
    if len(at) > 3 and at[3] != "":
        rot = _check_num_token(at[3], "footprint.at.rot")
    return fx, fy, rot


def _pad_layers(pad_node, copper_layers, pad_id):
    """焊盘铜层集合：'*.Cu'=全部铜层（THT）；否则取列出的 *.Cu 层。"""
    plys, = _require(pad_node, ("layers",), "pad %s" % pad_id)
    listed = [lv for lv in plys[1:] if isinstance(lv, str)]
    copper = [lv for lv in listed if lv.endswith(_COPPER_SUFFIX)]
    if not copper:
        return []          # 非铜层 pad（如 NPTH 标注层）不进 clearance 模型
    if "*.Cu" in copper:
        return list(copper_layers)
    out = []
    for lv in copper:
        if lv not in copper_layers:
            raise BoardParseError("pad %s 层 %r 不在板铜层表（fail-closed）"
                                  % (pad_id, lv))
        out.append(lv)
    return out


def _primitive_points(pad_node, pad_id):
    """custom 基元顶点（backlog 保守建模用）。

    基元嵌套于 (primitives (gr_poly (pts (xy ...))) ...)；gr_arc 取
    端点/中点（保守代表点）。custom 外形 backlog 未实现，解析层只取
    顶点做包围盒超集——几何近似登记在 geometry 层。
    """
    pts = []
    prims = _find_first(pad_node, "primitives")
    if prims is None:
        return pts
    for pr in prims[1:]:
        if not isinstance(pr, list) or not pr:
            continue
        if pr[0] in ("gr_poly", "gr_line", "gr_rect"):
            pts_node = _find_first(pr, "pts")
            if pts_node is not None:
                for xy in pts_node[1:]:
                    if isinstance(xy, list) and xy and xy[0] == "xy" \
                            and len(xy) >= 3:
                        pts.append((_check_num_token(xy[1], "prim.xy.x"),
                                    _check_num_token(xy[2], "prim.xy.y")))
        elif pr[0] == "gr_arc":
            for tag in ("start", "end", "mid"):
                n2 = _find_first(pr, tag)
                if n2 is not None and len(n2) >= 3:
                    pts.append((_check_num_token(n2[1], "gr_arc.%s.x" % tag),
                                _check_num_token(n2[2], "gr_arc.%s.y" % tag)))
    del pad_id
    return pts


def _parse_footprint(fp, copper_layers, pads_out, unsupported_out):
    ref = _footprint_reference(fp)
    fx, fy, frot = _footprint_at(fp, ref)
    for pad in sexpr_min.find_all(fp, "pad"):
        pid = pad[1]
        pad_id = "%s.%s" % (ref, pid)
        pat, psize = _require(pad, ("at", "size"), "pad %s" % pad_id)
        px = _check_num_token(pat[1], "pad.at.x")
        py = _check_num_token(pat[2], "pad.at.y")
        prot = 0.0
        if len(pat) > 3 and pat[3] != "":
            prot = _check_num_token(pat[3], "pad.at.rot")
        w = _check_num_token(psize[1], "pad.size.w")
        h = _check_num_token(psize[2], "pad.size.h")
        shape = pad[3] if len(pad) > 3 and isinstance(pad[3], str) else None
        ptype = pad[2] if len(pad) > 2 and isinstance(pad[2], str) else None
        if shape not in SUPPORTED_PAD_SHAPES:
            raise BoardParseError(
                "pad %s 非法/不支持形态枚举（fail-closed）: %r（支持集=%r；"
                "新形态须扩 SUPPORTED_PAD_SHAPES 后再放行）"
                % (pad_id, shape, SUPPORTED_PAD_SHAPES))
        if ptype is None:
            raise BoardParseError("pad %s 缺类型 token（fail-closed）"
                                  % pad_id)
        layers = _pad_layers(pad, copper_layers, pad_id)
        pnet = _find_first(pad, "net")
        rratio_node = _find_first(pad, "roundrect_rratio")
        radius = None
        if shape == "roundrect":
            if rratio_node is None or len(rratio_node) < 2:
                raise BoardParseError(
                    "pad %s roundrect 缺 roundrect_rratio（fail-closed）"
                    % pad_id)
            ratio = _check_ratio_token(rratio_node[1], "pad.rratio")
            if not (0.0 <= ratio <= 0.5):
                raise BoardParseError(
                    "pad %s 圆角比越界（fail-closed）: %r 限 [0,0.5]"
                    % (pad_id, ratio))
            radius = ratio * min(w, h)
        if w <= 0.0 or h <= 0.0:
            raise BoardParseError(
                "pad %s 形状退化：零/负尺寸（fail-closed）w=%r h=%r"
                % (pad_id, w, h))
        # 总旋转 = footprint 角 + pad 相对角（KiCad >= 6 文件语义）
        total_rot = frot + prot
        # 焊盘中心：局部坐标经 footprint 旋转平移（KiCad 画布 y-down 正角
        # CCW 映射，与 p3_revc_staging._footprint_pads 同口径——本模块独立
        # 实现该映射，零 import 其代码）
        rot_rad = math.radians(frot)
        cs, sn = math.cos(rot_rad), math.sin(rot_rad)
        ax = fx + px * cs + py * sn
        ay = fy - px * sn + py * cs
        prim_pts = _primitive_points(pad, pad_id) if shape == "custom" else None
        rec = {
            "pad_id": pad_id,
            "pad_type": ptype,
            "shape": shape,
            "net_id": pnet[1] if pnet is not None else "",
            "x_mm": _q(ax),
            "y_mm": _q(ay),
            "w_mm": w,
            "h_mm": h,
            "rotation_deg": _q(total_rot),
            "corner_radius_mm": None if radius is None else _q(radius),
            "layers": sorted(layers),
            "primitive_pts": [[_q(p[0]), _q(p[1])] for p in prim_pts]
            if prim_pts else None,
        }
        pads_out.append(rec)
        if shape == "custom":
            unsupported_out.append({
                "pad_id": pad_id,
                "net_id": rec["net_id"],
                "layers": rec["layers"],
                "reason": "custom 基元 backlog 未实现（任务书 §3 E1）；"
                          "geometry 层以基元顶点包围盒为保守超集建模",
                "primitive_pt_count": len(rec["primitive_pts"] or ()),
            })
