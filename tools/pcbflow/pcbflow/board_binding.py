"""PCBFlow 铜箔闭环 P1a —— 第三腿：板铜箔 ↔ manifest 绑定核对。

依据：铜箔闭环 P1a 任务书（接口契约由主审冻结，签名与字段名不可改）。
`svg_route_package.verify_consistency` 只管 manifest↔SVG 两条腿；本模块
补上板侧事实腿：用 `copper_model.parse_copper` 重解析真实铜箔，把
`manifest["routes"]` 按 `route_id`、`manifest["vias"]` 按 `via_id`、
`manifest["zones"]` 按 `zone_id`（合同 v2）与铜箔按 `key` 逐一配对核对。

fail-closed 纪律：
- 只存在于 manifest 或只存在于板（配对失败）、字段/几何不一致、
  manifest 结构非法、`net_map` 缺键、板文本不可解析 —— 一律产出违规项；
- 配对按 `copper_model` 的 `key` **1:1** 进行。该 key 现在是**全局唯一**
  寻址键：uuid 被同一条 route 的多个铜箔对象共享（真实 Rev-C 板的路由级
  uuid）时取 `"<uuid>@<digest>"`，digest 只含该对象自身几何。故 manifest
  的 id 集合与板侧 key 集合只要可完全配对，就**不会**再产生配对歧义违规；
  `route_paired_ambiguous` / `via_paired_ambiguous` 仅作为**防御性残留
  检查**保留 —— 只有"同一 key 在板上仍匹配到多个对象"（消歧后摘要亦相同：
  板上真有一对几何全同的同 uuid 对象）这种理论残留才触发，正常板必须为 0；
- 本函数内部任何异常都按违规处理，绝不返回假阳性空列表。

net 口径（本模块的关键语义）：
- `net_map=None` → **raw 口径**：manifest 的 `net_id` 字符串直接与板上
  net 名逐字比较（KiCad10 板的 `(net "GND")` 即名字；KiCad5 板 segment
  只有 `(net 1)` 序号，raw 口径下与 manifest 的 net_id 一般不相等，
  这是如实结果而非缺陷）；
- `net_map` 为 dict → 按 `net_map[net_id]` 解析成板侧 net 名再比；
  `net_map` 中缺键 → 违规 `net_map_key_missing`；`net_map` 非 dict →
  违规且跳过 net 比较（不猜测）。
  当前口径以 `net_basis=raw` / `net_basis=net_map` 记入 `binding_report`
  的 `pending`（返回值只放违规字符串，不放说明项）。

zone 核对（合同 v2 收口；本模块原先把 zone 登记为
`pending: ["zone_contract_v2"]` —— 该口径已过时，此处清理）：
- 配对与 route/via 同规：`manifest["zones"]` 按 `zone_id` ↔ 板 zone 的
  `key`（1:1；板侧 zone_id 即 `copper_model` 的 key，见
  `board_svg_adapter` 的 zone 一节）。只在一侧 = 违规
  （`zone_only_in_manifest` / `zone_only_in_board`）；同一 key 命中多个板侧
  zone = 防御性残留违规（`zone_paired_ambiguous`）。
- 逐项核对（零容差，量化口径与 `svg_route_package` 一致，坐标 6 位）：
  `net_id`（经 `net_map` 解析，口径同 route/via）、`layers`（**稳定排序后
  逐项比**：zone 的层声明顺序无语义，成员与重数仍零容差）、
  `outline_mm`（**轮廓事实**：点数与逐点坐标零容差）、`fill_state`
  （`svg_route_package.ZONE_FILL_STATES` 枚举；板侧无"是否已重填"事实，
  故只核 manifest 声明值合法性，`fresh` 不因板侧无填充数据而判违规）。
  另核 `outline_kind`：板侧 zone 轮廓只以多边形表达（`copper_model` 只认
  polygon/pts），manifest 声明非 polygon 即与板侧事实不符。
- **派生数据不构成违规依据**：`fill_sha256` / `fill_points` 是 KiCad
  `filled_polygon` 派生数据（改轮廓必然过期），本模块**不**据此报违规；
  只在 `binding_report["info"]["zones"]` 作信息项登记。故有 zone 时
  `pending` 记 `"zone_fill_derived_not_a_violation_basis"`（显式声明派生
  数据未参与违规判定，防止把"未核对"误读成"已核对且一致"）。
- v1 形状的 manifest（无 `zones` 键）对**有 zone 的板**必然产出
  `zone_only_in_board`：v1 合同未表达 zone，不得假装核对过（fail-closed）。

合同边界（未纳入核对的板侧事实，只登记不违规）：
- via 的 `(size)` 已解析但不在本阶段核对清单（只核对 from/to_layer、
  center、drill）→ `pending` 记 `"via_size_mm"`；`annular_ring_mm` 是
  由 size/drill 派生的 manifest 侧字段，本阶段不从板反推比对；
- 无法表达的板上铜箔（arc 走线、无轮廓 zone、结构非法节点、未识别的
  铜类顶层节点）→ `pending` 记 `"unrepresentable:<kind>"`；唯
  `board_parse_error`（板文本本身不可用）升格为违规。
- 被消歧的身份（uuid 是路由级内容派生值、被同一条 route 的多个对象共享）
  **不是**"不可表示"：它不进 `pending`、不产生违规，条数记在
  `binding_report["counts"]["board_identity_disambiguated"]`（信息性）。
- route 的 state/source/relation_ids/constraint_refs/endpoint_ids 与 via
  的 parent_id 是 manifest 侧/两腿内部的字段，板上无对应事实，不在本
  阶段板侧核对范围。

生成器模式：只读纯函数，不落盘、零子进程、零 wall-clock、零随机。
"""

from __future__ import annotations

import re

from . import copper_model
from .svg_route_package import ZONE_FILL_STATES, ZONE_OUTLINE_KINDS

__all__ = ["verify_board_binding", "binding_report"]

_ROUTE_ONLY_MANIFEST = "route_only_in_manifest"
_ROUTE_ONLY_BOARD = "route_only_in_board"
_VIA_ONLY_MANIFEST = "via_only_in_manifest"
_VIA_ONLY_BOARD = "via_only_in_board"
_ZONE_ONLY_MANIFEST = "zone_only_in_manifest"
_ZONE_ONLY_BOARD = "zone_only_in_board"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


# ----------------------------------------------------------------- 小工具

def _isnum(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _q6(v) -> float:
    return round(float(v), 6)


def _q3(v) -> float:
    return round(float(v), 3)


def _pt(v) -> "list | None":
    """[x, y] 数值对 → [q6, q6]；非法返回 None。"""
    if isinstance(v, (list, tuple)) and len(v) == 2 and _isnum(v[0]) \
            and _isnum(v[1]):
        return [_q6(v[0]), _q6(v[1])]
    return None


def _index_manifest(entries, key, violations, what):
    """manifest 对象列表 → {id: entry}（非法项报违规、不并入）。"""
    out = {}
    if entries is None:
        return out
    if not isinstance(entries, list):
        violations.append("manifest.%s: 不是列表" % what)
        return out
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            violations.append("manifest.%s[%d]: 不是对象" % (what, i))
            continue
        v = e.get(key)
        if not isinstance(v, str) or v == "":
            violations.append("manifest.%s[%d]: 缺 %s" % (what, i, key))
            continue
        if v in out:
            violations.append("manifest.%s: %s 重复: %r" % (what, key, v))
            continue
        out[v] = e
    return out


def _multimap(items):
    """铜箔列表 → {key: [对象...]}（重复 key 保序保留）。"""
    out = {}
    for it in items:
        out.setdefault(it["key"], []).append(it)
    return out


def _net_basis(net_map):
    """(basis_str, usable) —— None=raw；dict=解析；其余=不可用。"""
    if net_map is None:
        return "raw", True
    if isinstance(net_map, dict):
        return "net_map", True
    return "invalid", False


def _check_net(kind, obj_id, m_net, board_net, net_map, basis, violations):
    """net 比对（raw 或 net_map 解析口径）；缺失/不匹配均报违规。

    basis 非 raw/net_map（net_map 形状非法）时跳过 net 比较 —— 已在主流程
    报 `net_map: 不是字典...` 违规，此处不再叠噪声、也不猜。"""
    if basis not in ("raw", "net_map"):
        return
    if basis == "raw":
        if m_net != board_net:
            violations.append("%s_net_mismatch: %s: manifest=%r board=%r"
                              % (kind, obj_id, m_net, board_net))
        return
    if not isinstance(m_net, str) or m_net not in net_map:
        violations.append("net_map_key_missing: %s: net_id=%r" % (obj_id, m_net))
        return
    want = net_map[m_net]
    if want != board_net:
        violations.append("%s_net_mismatch: %s: net_map[%r]=%r board=%r"
                          % (kind, obj_id, m_net, want, board_net))


# --------------------------------------------------------------- 单项核对

def _check_route(rid, mr, seg, net_map, basis, violations):
    """manifest route 与单个板 segment 的字段/几何核对（零容差）。"""
    layer = mr.get("layer")
    if not isinstance(layer, str) or layer == "":
        violations.append("route_layer_invalid: %s: %r" % (rid, layer))
    elif layer != seg["layer"]:
        violations.append("route_layer_mismatch: %s: manifest=%r board=%r"
                          % (rid, layer, seg["layer"]))

    width = mr.get("width_mm")
    if not _isnum(width):
        violations.append("route_width_invalid: %s: %r" % (rid, width))
    elif _q3(width) != _q3(seg["width"]):
        violations.append("route_width_mismatch: %s: manifest=%.3f board=%.3f"
                          % (rid, _q3(width), _q3(seg["width"])))

    poly = mr.get("polyline_mm")
    if not isinstance(poly, list):
        violations.append("route_polyline_invalid: %s: 不是列表" % rid)
    elif len(poly) < 2:
        violations.append("route_polyline_invalid: %s: 少于 2 点" % rid)
    else:
        pts = [_pt(p) for p in poly]
        if any(p is None for p in pts):
            violations.append("route_polyline_invalid: %s: 存在非法顶点" % rid)
        else:
            if len(pts) > 2:
                violations.append(
                    "route_polyline_extra_vertices: %s: %d 点（P1a 合同"
                    " 一个 route_id ↔ 一个 segment，应为 2 点）"
                    % (rid, len(pts)))
            head, tail = pts[0], pts[-1]
            if head != [_q6(seg["start"][0]), _q6(seg["start"][1])]:
                violations.append(
                    "route_polyline_mismatch: %s: 首点 manifest=%r "
                    "board.start=%r（零容差）" % (rid, head, seg["start"]))
            if tail != [_q6(seg["end"][0]), _q6(seg["end"][1])]:
                violations.append(
                    "route_polyline_mismatch: %s: 末点 manifest=%r "
                    "board.end=%r（零容差）" % (rid, tail, seg["end"]))

    _check_net("route", rid, mr.get("net_id"), seg["net"], net_map, basis,
               violations)


def _check_via(vid, mv, via, net_map, basis, violations):
    """manifest via 与单个板 via 的字段核对（from/to/center/drill/net）。"""
    layers = via["layers"]
    for field, idx in (("from_layer", 0), ("to_layer", 1)):
        v = mv.get(field)
        if not isinstance(v, str) or v == "":
            violations.append("via_%s_invalid: %s: %r" % (field, vid, v))
        elif v != layers[idx]:
            violations.append("via_%s_mismatch: %s: manifest=%r board=%r"
                              % (field, vid, v, layers[idx]))

    c = _pt(mv.get("center_mm"))
    if c is None:
        violations.append("via_center_invalid: %s: %r"
                          % (vid, mv.get("center_mm")))
    elif c != [_q6(via["at"][0]), _q6(via["at"][1])]:
        violations.append("via_center_mismatch: %s: manifest=%r board=%r"
                          % (vid, c, via["at"]))

    drill = mv.get("drill_mm")
    if not _isnum(drill):
        violations.append("via_drill_invalid: %s: %r" % (vid, drill))
    elif _q3(drill) != _q3(via["drill"]):
        violations.append("via_drill_mismatch: %s: manifest=%.3f board=%.3f"
                          % (vid, _q3(drill), _q3(via["drill"])))

    _check_net("via", vid, mv.get("net_id"), via["net"], net_map, basis,
               violations)


def _check_zone(zid, mz, zone, net_map, basis, violations, info):
    """manifest zone 与单个板 zone 的字段/几何核对（零容差；见模块 docstring）。

    `info`：派生填充数据（fill_sha256/fill_points）只作信息项登记 —— 它们
    是 KiCad `filled_polygon` 派生数据，**不得**作为违规依据。
    """
    # layers：zone 的 `(layers ...)` 是**层集合**，声明顺序无语义（与 via 的
    # from/to 有序语义不同）→ 稳定排序后逐项比；成员与重数仍零容差
    # （少一层 / 换一层 / 重复一层都必须报违规）。
    ml = mz.get("layers")
    board_decl = [str(v) for v in zone["layers"]]
    if not isinstance(ml, list) or not ml or not all(
            isinstance(v, str) and v != "" for v in ml):
        violations.append("zone_layers_invalid: %s: %r" % (zid, ml))
    elif sorted(str(v) for v in ml) != sorted(board_decl):
        violations.append("zone_layers_mismatch: %s: manifest=%r board=%r"
                          "（稳定排序后逐项比：声明顺序无语义，成员/重数"
                          "零容差）" % (zid, ml, board_decl))

    # outline_mm：轮廓事实（非填充），点数与逐点坐标 6 位零容差
    outline = mz.get("outline_mm")
    board_outline = [[_q6(p[0]), _q6(p[1])] for p in zone["outline_mm"]]
    if not isinstance(outline, list) or len(outline) < 3:
        violations.append("zone_outline_invalid: %s: 必须 >=3 点（实得 %s 点）"
                          % (zid, len(outline)
                             if isinstance(outline, list) else outline))
    else:
        pts = [_pt(p) for p in outline]
        if any(p is None for p in pts):
            violations.append("zone_outline_invalid: %s: 存在非法顶点" % zid)
        elif len(pts) != len(board_outline):
            violations.append(
                "zone_outline_mismatch: %s: 点数 manifest=%d board=%d"
                "（零容差）" % (zid, len(pts), len(board_outline)))
        else:
            diff = [i for i, (a, b) in enumerate(zip(pts, board_outline))
                    if a != b]
            if diff:
                i = diff[0]
                violations.append(
                    "zone_outline_mismatch: %s: 顶点不一致 %d/%d 处；"
                    "首个 manifest[%d]=%r board=%r（零容差）"
                    % (zid, len(diff), len(pts), i, pts[i], board_outline[i]))

    # outline_kind：板侧只用多边形表达轮廓（copper_model 只认 polygon/pts）
    kind = mz.get("outline_kind", ZONE_OUTLINE_KINDS[0])
    if kind not in ZONE_OUTLINE_KINDS:
        violations.append("zone_outline_kind_mismatch: %s: manifest=%r 非法"
                          "（板侧 zone 轮廓只以 %s 表达）"
                          % (zid, kind, list(ZONE_OUTLINE_KINDS)))
    elif kind != "polygon":
        violations.append("zone_outline_kind_mismatch: %s: manifest=%r "
                          "board=%r" % (zid, kind, "polygon"))

    # fill_state：板侧无重填证据 → 只核 manifest 声明值合法性（不猜、不升格）
    fs = mz.get("fill_state")
    if fs not in ZONE_FILL_STATES:
        violations.append("zone_fill_state_invalid: %s: %r 不在 %s"
                          % (zid, fs, list(ZONE_FILL_STATES)))
    else:
        info["fill_state_counts"][fs] += 1

    # 派生填充数据：仅信息项（不得作为违规依据）
    fill = mz.get("fill")
    sha = fill.get("fill_sha256") if isinstance(fill, dict) else None
    pts_n = fill.get("fill_points") if isinstance(fill, dict) else None
    if not isinstance(sha, str) or not _SHA256_RE.match(sha):
        info["fill_fingerprint_missing"].append(zid)
    if pts_n is not None and not isinstance(pts_n, int):
        info["fill_points_unusable"].append(zid)

    _check_net("zone", zid, mz.get("net_id"), zone["net"], net_map, basis,
               violations)


# ----------------------------------------------------------------- 主流程

def _bind(board_text, manifest, net_map):
    """板↔manifest 三族绑定对账（segments/vias/zones；net_map 消歧）。

    三族各自配对计数（paired/manifest_only/board_only）+zones 的
    fill 状态/指纹缺失/不可用点信息项；board_unrepresentable 单列
    （板侧无法进 manifest 的对象如实计数，不静默吞）。violations 为
    差集结论（对账失败面），counts/info 供上层 envelope 记账。
    """
    violations = []
    pending = []
    counts = {
        "manifest_segments": 0, "board_segments": 0, "board_segment_keys": 0,
        "paired_segments": 0, "manifest_only_segments": 0,
        "board_only_segments": 0,
        "manifest_vias": 0, "board_vias": 0, "board_via_keys": 0,
        "paired_vias": 0, "manifest_only_vias": 0, "board_only_vias": 0,
        "manifest_zones": 0, "board_zones": 0, "board_zone_keys": 0,
        "paired_zones": 0, "manifest_only_zones": 0, "board_only_zones": 0,
        "board_unrepresentable": 0,
        "board_identity_disambiguated": 0,
    }
    info = {
        "zones": {
            "fill_state_counts": {s: 0 for s in ZONE_FILL_STATES},
            "fill_fingerprint_missing": [],   # 派生数据缺/非法（信息项）
            "fill_points_unusable": [],
            "fill_derived_is_not_a_violation_basis": True,
            "fill_state_is_caller_declared": True,
            "note": "fill_sha256/fill_points 是 KiCad filled_polygon 派生数据："
                    "本模块只作信息项登记，绝不据此报违规（改派生数据不得"
                    "改变核对结论）；fill_state 由 manifest 侧调用方声明，"
                    "板侧无『是否已重填』事实，故只核声明值合法性",
        },
    }
    if not isinstance(manifest, dict):
        return ["manifest: 不是对象"], pending, counts, None, info
    if not isinstance(board_text, str):
        return ["board_text: 不是字符串"], pending, counts, None, info
    if "(" not in board_text:
        # 防假阳性空列表：路径/空文本不是板文本，绝不能当成"板上没有铜箔"
        return (["board_text: 不含任何 s-expr 节点（疑似把路径或空文本当板"
                 "文本传入，拒绝按'空板'处理）"], pending, counts, None, info)

    copper = copper_model.parse_copper(board_text)
    unrep = copper["unrepresentable"]
    kinds = sorted({u["kind"] for u in unrep})
    counts["board_unrepresentable"] = len(unrep)
    counts["board_identity_disambiguated"] = len(
        copper["identity_disambiguated"])
    counts["board_segments"] = copper["counts"]["segments"]
    counts["board_vias"] = copper["counts"]["vias"]
    counts["board_zones"] = copper["counts"]["zones"]
    for u in unrep:
        if u["kind"] == "board_parse_error":
            violations.append("board_parse_error: %s" % u["reason"])

    seg_by_key = _multimap(copper["segments"])
    via_by_key = _multimap(copper["vias"])
    zone_by_key = _multimap(copper["zones"])
    counts["board_segment_keys"] = len(seg_by_key)
    counts["board_via_keys"] = len(via_by_key)
    counts["board_zone_keys"] = len(zone_by_key)

    m_routes = _index_manifest(manifest.get("routes"), "route_id", violations,
                              "routes")
    m_vias = _index_manifest(manifest.get("vias"), "via_id", violations,
                            "vias")
    m_zones = _index_manifest(manifest.get("zones"), "zone_id", violations,
                              "zones")
    counts["manifest_segments"] = len(m_routes)
    counts["manifest_vias"] = len(m_vias)
    counts["manifest_zones"] = len(m_zones)

    basis, usable = _net_basis(net_map)
    if not usable:
        violations.append("net_map: 不是字典或 None（无法解析 net_id → "
                          "板侧 net 名），该 net_map 不可用")

    for rid in sorted(set(m_routes) | set(seg_by_key)):
        cands = seg_by_key.get(rid)
        mr = m_routes.get(rid)
        if mr is None:
            violations.append("%s: %s" % (_ROUTE_ONLY_BOARD, rid))
            counts["board_only_segments"] += 1
            continue
        if not cands:
            violations.append("%s: %s" % (_ROUTE_ONLY_MANIFEST, rid))
            counts["manifest_only_segments"] += 1
            continue
        if len(cands) > 1:
            # 防御性残留：key 已全局唯一，只有"同 uuid 且几何全同"才可能
            # 让同一 key 命中多个节点（此时 copper_model 已报
            # identity_key_collision）—— 不猜、不并合，拒绝任取其一核对。
            violations.append(
                "route_paired_ambiguous: %s: 板上 %d 个 segment 共享同一 key"
                "（身份无法唯一化，拒绝任取其一核对）" % (rid, len(cands)))
            continue
        counts["paired_segments"] += 1
        _check_route(rid, mr, cands[0], net_map if usable else None,
                     basis if usable else "invalid", violations)

    for vid in sorted(set(m_vias) | set(via_by_key)):
        cands = via_by_key.get(vid)
        mv = m_vias.get(vid)
        if mv is None:
            violations.append("%s: %s" % (_VIA_ONLY_BOARD, vid))
            counts["board_only_vias"] += 1
            continue
        if not cands:
            violations.append("%s: %s" % (_VIA_ONLY_MANIFEST, vid))
            counts["manifest_only_vias"] += 1
            continue
        if len(cands) > 1:
            # 同上：防御性残留检查（见 route 配对处）
            violations.append(
                "via_paired_ambiguous: %s: 板上 %d 个 via 共享同一 key"
                "（身份无法唯一化，拒绝任取其一核对）" % (vid, len(cands)))
            continue
        counts["paired_vias"] += 1
        _check_via(vid, mv, cands[0], net_map if usable else None,
                   basis if usable else "invalid", violations)

    # zone 配对（合同 v2）：1:1 按 zone_id ↔ 板 zone.key；同规 fail-closed
    for zid in sorted(set(m_zones) | set(zone_by_key)):
        cands = zone_by_key.get(zid)
        mz = m_zones.get(zid)
        if mz is None:
            violations.append("%s: %s" % (_ZONE_ONLY_BOARD, zid))
            counts["board_only_zones"] += 1
            continue
        if not cands:
            violations.append("%s: %s" % (_ZONE_ONLY_MANIFEST, zid))
            counts["manifest_only_zones"] += 1
            continue
        if len(cands) > 1:
            # 同 route/via：防御性残留检查（消歧后 key 已全局唯一）
            violations.append(
                "zone_paired_ambiguous: %s: 板上 %d 个 zone 共享同一 key"
                "（身份无法唯一化，拒绝任取其一核对）" % (zid, len(cands)))
            continue
        counts["paired_zones"] += 1
        _check_zone(zid, mz, cands[0], net_map if usable else None,
                    basis if usable else "invalid", violations,
                    info["zones"])

    # pending：显式登记"已解析但未纳入本阶段合同核对"的板侧事实
    if copper["counts"]["zones"]:
        # zone 已按 v2 合同核对（net/layers/outline_mm/fill_state）；仅派生
        # 填充数据（fill_sha256/fill_points）不参与违规判定，显式登记。
        pending.append("zone_fill_derived_not_a_violation_basis")
    for k in kinds:
        pending.append("unrepresentable:" + k)
    if copper["counts"]["vias"]:
        pending.append("via_size_mm")
    pending.append("net_basis=" + basis)
    return violations, pending, counts, copper, info


def verify_board_binding(board_text: str, manifest: dict,
                         net_map: "dict | None" = None) -> list:
    """第三腿核对：板铜箔 ↔ manifest，返回违规原因列表（空列表 = 一致）。

    逐项核对（全部零容差，量化口径与 svg_route_package 一致）：
    - 配对：manifest.route_id ↔ 板 segment.key、manifest.via_id ↔ 板
      via.key、manifest.zone_id ↔ 板 zone.key（1:1，key 全局唯一）；仅存在于
      一侧 = 违规（`*_only_in_manifest` / `*_only_in_board`）；
      同一 key 在板上仍匹配到多个节点 = 违规（`*_paired_ambiguous`，防御性
      残留检查：消歧后 key 已全局唯一，正常板为 0）。
    - route：`layer`、`width_mm`（3 位量化）、`polyline_mm` 与 segment
      起终点（6 位量化零容差）、net（见下）。
    - via：`from_layer`/`to_layer`（有序逐位）、`center_mm`（6 位零容差）、
      `drill_mm`（3 位量化）、net。
    - zone（合同 v2）：net、`layers`（**稳定排序后逐项比**：层声明顺序无
      语义；成员与重数零容差）、`outline_mm`（轮廓事实，点数与逐点坐标
      6 位零容差）、`fill_state`（枚举合法性）、
      `outline_kind`（板侧只以 polygon 表达）。派生填充数据
      （fill_sha256/fill_points）**不**作为违规依据。

    net 口径：`net_map=None` → raw（manifest net_id 与板上 net 名逐字比）；
    `net_map` 为 dict → 按 `net_map[net_id]` 解析成板侧 net 名再比，缺键报
    `net_map_key_missing`。当前口径记在 `binding_report["pending"]` 的
    `net_basis=raw`/`net_basis=net_map`（本函数只返回违规字符串）。

    zone 已按 v2 合同纳入核对（配对 + net/layers/outline_mm/fill_state）；
    派生填充数据不参与违规判定，登记在 `binding_report["info"]["zones"]`
    与 `pending["zone_fill_derived_not_a_violation_basis"]`。

    fail-closed：输入形状非法（manifest 非对象、board_text 非字符串、
    板文本不含任何 s-expr 节点 —— 例如误把文件路径当文本传入）、
    板文本不可解析（`board_parse_error`）、内部异常一律计入违规；
    绝不返回假阳性空列表，绝不以"看起来对"为准。
    """
    try:
        violations = _bind(board_text, manifest, net_map)[0]
    except Exception as exc:  # 任何内部异常都按违规处理（fail-closed）
        return ["verify: 内部异常按违规处理: %s: %s"
                % (exc.__class__.__name__, exc)]
    return sorted(violations)


def binding_report(board_text: str, manifest: dict,
                   net_map: "dict | None" = None) -> dict:
    """第三腿核对报告：{"violations", "pending", "counts", "identity_basis",
    "copper_sha256", "info"}。

    - `violations`：同 `verify_board_binding`（已排序，空列表 = 一致）；
    - `pending`：显式登记"已解析但未纳入合同核对"的板侧事实，形如
      `"zone_fill_derived_not_a_violation_basis"`（有 zone 时必含）、
      `"via_size_mm"`、`"unrepresentable:<kind>"`、`"net_basis=raw|net_map"`；
      有未核对项时它非空 —— 防止把"未核对"误读成"已核对且一致"；
    - `counts`：manifest 侧与板侧对象数对账（segment/via/zone 的
      `paired_*` 与 `*_only_*`；`board_identity_disambiguated` = 被消歧
      （路由级 uuid 共享）的板侧对象数，信息性，不是违规也不是"不可表示"）；
    - `info`：**不构成违规依据**的信息项。`info["zones"]` 记 zone 派生填充
      数据（fill_sha256/fill_points）的缺失/非法清单与 fill_state 计数 ——
      派生数据改不动核对结论，故只登记不判违规；
    - `identity_basis` / `copper_sha256`：铜箔事实模型的同名字段
      （输入形状非法时为 None）。
    """
    try:
        violations, pending, counts, copper, info = _bind(board_text, manifest,
                                                          net_map)
    except Exception as exc:  # fail-closed：异常按违规 + 无事实可报
        return {"violations": ["verify: 内部异常按违规处理: %s: %s"
                               % (exc.__class__.__name__, exc)],
                "pending": [], "counts": {}, "identity_basis": None,
                "copper_sha256": None, "info": {}}
    return {
        "violations": sorted(violations),
        "pending": pending,
        "counts": counts,
        "identity_basis": None if copper is None else copper["identity_basis"],
        "copper_sha256": None if copper is None else copper["copper_sha256"],
        "info": info,
    }
