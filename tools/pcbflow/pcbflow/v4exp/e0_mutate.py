"""E0 确定性负向突变引擎（8 种突变 + 1 个正向对照）。

突变对象：f1 场景（有 route）的 SVG 文本；目标 route 一律取
manifest["routes"][0]（确定序）。同输入同突变体字节一致。

负向突变（期望 blocked）：
  1) net_id_unknown      某 route data-net-id 改为未知 "nX"
  2) layer_mismatch      某 route data-layer 与 manifest 相反（F.Cu<->B.Cu）
  3) width_mismatch      某 route data-width-mm +0.1
  4) path_coord_shift    某 path d 首点坐标 +0.25
  5) duplicate_route_id  复制某 route <g> 节点（重复 route_id）
  6) route_deleted       删除一个 route 对象
  7) manifest_hash_zeroed 根节点 data-route-manifest-sha256 改成 64 个 '0'
  8b) line_type_unknown  某 route data-line-type 改为未知值 "mystery"

正向对照（必须仍通过全部机器检查且 facts 与原版逐字段相等）：
  8a) color_only_positive_control 仅改颜色/stroke，不碰 data-*

blocked 判定 = 严格解析失败 或 任一机器检查不过。
零子进程、零 argv、零 wall-clock、零网络。
"""

from __future__ import annotations

import re

from . import e0_checks, e0_parse, model
from .e0_checks import rewrite_colors

NEGATIVE_MUTATIONS = (
    "net_id_unknown",
    "layer_mismatch",
    "width_mismatch",
    "path_coord_shift",
    "duplicate_route_id",
    "route_deleted",
    "manifest_hash_zeroed",
    "line_type_unknown",
)
POSITIVE_MUTATION = "color_only_positive_control"
# 结果行顺序镜像合同编号 1..7、8a、8b
ALL_MUTATIONS = NEGATIVE_MUTATIONS[:7] + (POSITIVE_MUTATION,) \
    + NEGATIVE_MUTATIONS[7:]
UNKNOWN_NET = "nX"
UNKNOWN_LINE_TYPE = "mystery"


def _route_block(svg_text: str, route_id: str) -> tuple:
    """返回 route 组 <g ...> ... </g> 的文本 span [start, end)。"""
    marker = f'<g id="route-{route_id}"'
    start = svg_text.find(marker)
    if start == -1:
        raise ValueError(f"突变目标 route 组未找到: {route_id}")
    end = svg_text.find("</g>", start)
    if end == -1:
        raise ValueError(f"route 组未闭合: {route_id}")
    return start, end + len("</g>")


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"突变 {what}: 目标子串出现 {text.count(old)} 次")
    return text.replace(old, new, 1)


def _attr_swap(block: str, attr: str, new_value: str,
               what: str) -> str:
    """块内 data 属性值替换（目标子串从 SVG 块自身提取，突变自洽）。"""
    m = re.search(rf'{attr}="([^"]*)"', block)
    if not m:
        raise ValueError(f"突变 {what}: 块内未找到 {attr}")
    return _replace_once(block, m.group(0), f'{attr}="{new_value}"', what)


def _swap_layer(layer: str) -> str:
    return "B.Cu" if layer == "F.Cu" else "F.Cu"


def apply_mutation(name: str, svg_text: str, manifest: dict) -> str:
    """返回突变后的 SVG 文本（确定性；同输入同字节）。

    manifest 只用于确定目标 route（routes[0].route_id）；被替换的旧值一律
    从 SVG 文本自身提取，保证突变引擎不依赖 manifest 与 SVG 的事前一致。
    """
    rid = manifest["routes"][0]["route_id"]
    start, end = _route_block(svg_text, rid)
    block = svg_text[start:end]

    if name == "net_id_unknown":
        mutated_block = _attr_swap(block, "data-net-id", UNKNOWN_NET, name)
    elif name == "layer_mismatch":
        cur = re.search(r'data-layer="([^"]*)"', block).group(1)
        mutated_block = _attr_swap(block, "data-layer",
                                   _swap_layer(cur), name)
    elif name == "width_mismatch":
        m = re.search(r'data-width-mm="(-?\d+\.\d{3})"', block)
        if not m:
            raise ValueError("突变 width_mismatch: 未找到 data-width-mm")
        new = model.fmt3(float(m.group(1)) + 0.1)
        mutated_block = _replace_once(
            block, m.group(0), f'data-width-mm="{new}"', name)
    elif name == "path_coord_shift":
        m = re.search(r'd="M (-?\d+\.\d{6}) ', block)
        if not m:
            raise ValueError("突变 path_coord_shift: 未找到 path d 首点")
        shifted = model.fmt6(float(m.group(1)) + 0.25)
        mutated_block = _replace_once(
            block, m.group(0), f'd="M {shifted} ', name)
    elif name == "duplicate_route_id":
        return svg_text[:end] + "\n  " + block + svg_text[end:]
    elif name == "route_deleted":
        line_start = svg_text.rfind("\n", 0, start)
        line_end = svg_text.find("\n", end)
        if line_end == -1:
            line_end = len(svg_text)
        return svg_text[:line_start + 1] + svg_text[line_end + 1:]
    elif name == "manifest_hash_zeroed":
        return re.sub(
            r'data-route-manifest-sha256="[0-9a-f]{64}"',
            'data-route-manifest-sha256="' + "0" * 64 + '"',
            svg_text, count=1)
    elif name == "line_type_unknown":
        mutated_block = _attr_swap(block, "data-line-type",
                                   UNKNOWN_LINE_TYPE, name)
    elif name == POSITIVE_MUTATION:
        return rewrite_colors(svg_text)
    else:
        raise ValueError(f"未知突变: {name}")
    return svg_text[:start] + mutated_block + svg_text[end:]


def run_machine_checks(facts: dict, svg_text: str, manifest: dict,
                       board_obj: dict, base_svg_text: str = None) -> list:
    """对（可能被突变的）SVG 的机器检查集合：身份/一致/roundtrip/hash/颜色。

    base_svg_text：颜色独立性检查所用的原始（含真实颜色的）SVG 文本；
    缺省用 svg_text 本身。
    """
    bbox = board_obj["board"]["bbox_mm"]
    return [
        e0_checks.identity_recovery(facts, manifest),
        e0_checks.manifest_svg_consistency(facts, manifest, bbox),
        e0_checks.roundtrip_mm(facts, manifest, bbox),
        e0_checks.hash_binding(facts, manifest, board_obj),
        e0_checks.color_independence(svg_text, facts, base_svg_text),
    ]


def evaluate_mutation(mutated_svg: str, manifest: dict,
                      board_obj: dict, original_facts: dict = None,
                      original_svg: str = None) -> dict:
    """判定突变结果：blocked = 解析失败或任一机器检查不过。

    提供 original_facts 时（正向对照 8a），额外要求 mutated facts 与原版
    逐字段相等，否则按 blocked 处理；original_svg 供颜色检查做重写基底。
    """
    facts, reason = e0_parse.try_parse_svg(mutated_svg)
    if facts is None:
        return {"blocked": True, "detail": f"parse_failure: {reason}"}
    if original_facts is not None and facts != original_facts:
        return {"blocked": True,
                "detail": "facts 与原版不一致: "
                          + e0_checks._facts_diff(original_facts, facts)}
    checks = run_machine_checks(facts, mutated_svg, manifest, board_obj,
                                base_svg_text=original_svg)
    failed = [c for c in checks if not c["pass"]]
    if failed:
        first = failed[0]
        return {"blocked": True,
                "detail": f"{first['check']}: {first['reason'][:160]}"}
    return {"blocked": False, "detail": "全部机器检查通过（未被拦截）"}
