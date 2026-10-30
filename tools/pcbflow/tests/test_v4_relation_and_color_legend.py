"""V4.0-A 关系对象、via、keepout、board edge、图例与颜色编码测试。

被测生产模块：pcbflow/svg_route_package.py。
覆盖（方案 §3.3/§3.4/§2.2/§2.3）：
- 关系对象显式表达：differential_pair 与 bus 的 data-member-ids 与
  manifest.relations members 一致，成员 route 仍带独立
  route_id/net_id/constraint-refs（parent/关系不替代网络身份）；
- via 对象：via_id/from-layer/to-layer/drill/annular-ring 全套 data-*；
- keepout 与 board edge 的 data-* 表达；
- 图例：legend_record() 带版本 + sha256（独立重算核验），manifest 与
  SVG 内图例组绑定一致；篡改图例 hash 必检出；
- 颜色/线型仅是 class 编码：改 class 不影响 data-* 字段解析，
  verify_consistency 仍为清白（机器事实只来自 data-* 属性）。
"""

import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import pytest

from pcbflow import svg_route_package as s4

SVG_NS = "http://www.w3.org/2000/svg"


# ---------------------------------------------------------- 合成最小夹具

def make_board():
    return {
        "scenario_id": "SC-V4A-SVG",
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0]},
        "rules": {"min_clearance_mm": 0.2},
        "pads": [
            {"pad_id": "U1.1", "net_id": "N1", "x_mm": 12.4, "y_mm": 8.2,
             "w_mm": 0.6, "h_mm": 0.4, "layer": "F.Cu"},
            {"pad_id": "J3.2", "net_id": "N1", "x_mm": 18.7, "y_mm": 8.2,
             "w_mm": 0.6, "h_mm": 0.4, "layer": "F.Cu"},
            {"pad_id": "U1.3", "net_id": "USB_DP", "x_mm": 6.0, "y_mm": 12.0,
             "w_mm": 0.6, "h_mm": 0.4, "layer": "F.Cu"},
            {"pad_id": "U1.4", "net_id": "USB_DN", "x_mm": 7.4, "y_mm": 12.0,
             "w_mm": 0.6, "h_mm": 0.4, "layer": "F.Cu"},
        ],
        "keepouts": [
            {"keepout_id": "K1", "rect_mm": [20.0, 14.0, 30.0, 22.0],
             "layers": ["F.Cu", "B.Cu"]},
        ],
        "relations": [
            {"relation_id": "DP1", "relation_type": "differential_pair",
             "members": ["USB_DP", "USB_DN"], "parent_id": None},
            {"relation_id": "BUS1", "relation_type": "bus",
             "members": ["N1"], "parent_id": None},
        ],
    }


def make_ref():
    return {
        "scenario_id": "SC-V4A-SVG",
        "routes": [
            {"route_id": "R-SIG", "net_id": "N1",
             "relation_ids": ["R-N1-U1.1-J3.2"], "line_type": "signal",
             "parent_id": None, "layer": "F.Cu", "width_mm": 0.25,
             "polyline_mm": [[12.4, 8.2], [18.7, 8.2]],
             "endpoint_ids": ["U1.1", "J3.2"],
             "constraint_refs": ["C-clearance-020", "C-width-025"],
             "state": "candidate", "source": "solver"},
            {"route_id": "R-DP", "net_id": "USB_DP",
             "relation_ids": ["R-DP1-P"], "line_type": "diff_p",
             "parent_id": None, "layer": "F.Cu", "width_mm": 0.25,
             "polyline_mm": [[6.0, 12.0], [6.0, 18.0], [14.0, 18.0]],
             "endpoint_ids": ["U1.3", "J5.1"],
             "constraint_refs": ["C-diff-gap-015"],
             "state": "baseline", "source": "baseline"},
            {"route_id": "R-DN", "net_id": "USB_DN",
             "relation_ids": ["R-DP1-N"], "line_type": "diff_n",
             "parent_id": None, "layer": "B.Cu", "width_mm": 0.25,
             "polyline_mm": [[7.4, 12.0], [7.4, 19.2], [14.0, 19.2]],
             "endpoint_ids": ["U1.4", "J5.2"],
             "constraint_refs": ["C-diff-gap-015"],
             "state": "locked", "source": "baseline"},
        ],
        "vias": [
            {"via_id": "V1", "net_id": "N1", "parent_id": "R-SIG",
             "from_layer": "F.Cu", "to_layer": "B.Cu",
             "center_mm": [18.7, 8.2], "drill_mm": 0.3,
             "annular_ring_mm": 0.15},
        ],
    }


@pytest.fixture(scope="module")
def package():
    board, ref = make_board(), make_ref()
    svg, manifest = s4.build(board, ref)
    return board, ref, svg, manifest


def find_by_id(root, el_id):
    for el in root.iter():
        if isinstance(el.tag, str) and el.attrib.get("id") == el_id:
            return el
    raise AssertionError(f"SVG 中找不到 id={el_id!r} 的元素")


def strip_sha(obj):
    if isinstance(obj, dict):
        return {k: strip_sha(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [strip_sha(v) for v in obj]
    return obj


def canon_sha256(obj):
    text = json.dumps(strip_sha(obj), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------- 关系对象

class TestRelationObjects:
    def test_diff_pair_relation_group_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        g = find_by_id(root, "relation-DP1")
        assert g.tag == f"{{{SVG_NS}}}g"
        assert g.get("data-object-kind") == "route_relation"
        assert g.get("data-relation-id") == "DP1"
        assert g.get("data-relation-type") == "differential_pair"
        mr = next(r for r in manifest["relations"]
                  if r["relation_id"] == "DP1")
        assert g.get("data-member-ids") == " ".join(mr["members"])
        assert mr["members"] == ["USB_DP", "USB_DN"]

    def test_bus_relation_group_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        g = find_by_id(root, "relation-BUS1")
        assert g.get("data-relation-type") == "bus"
        mr = next(r for r in manifest["relations"]
                  if r["relation_id"] == "BUS1")
        assert g.get("data-member-ids") == " ".join(mr["members"]) == "N1"

    def test_relation_types_are_enumerated_in_manifest(self, package):
        _, _, _, manifest = package
        for mr in manifest["relations"]:
            assert mr["relation_type"] in s4.RELATION_TYPES

    def test_members_keep_independent_identity_and_constraint_refs(self,
                                                                   package):
        """差分对成员仍是独立 route：独立 route_id/net_id 与
        data-constraint-refs（关系不吞并成员身份）。"""
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        by_net = {r["net_id"]: r for r in manifest["routes"]}
        for net in ("USB_DP", "USB_DN"):
            assert net in by_net
        g_dp = find_by_id(root, "route-R-DP")
        g_dn = find_by_id(root, "route-R-DN")
        assert g_dp.get("data-net-id") == "USB_DP"
        assert g_dn.get("data-net-id") == "USB_DN"
        for g in (g_dp, g_dn):
            assert g.get("data-constraint-refs") == "C-diff-gap-015"
        assert g_dp.get("data-line-type") == "diff_p"
        assert g_dn.get("data-line-type") == "diff_n"


# ----------------------------------------------------------------- via

class TestViaObject:
    def test_via_full_data_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        el = find_by_id(root, "via-V1")
        assert el.tag == f"{{{SVG_NS}}}circle"
        assert el.get("data-object-kind") == "via"
        for name in s4.SVG_VIA_ATTRS:
            assert name in el.attrib, f"via 缺属性 {name}"
        mv = manifest["vias"][0]
        assert mv["via_id"] == "V1"
        assert el.get("data-via-id") == "V1"
        assert el.get("data-net-id") == mv["net_id"]
        assert el.get("data-parent-id") == mv["parent_id"] == "R-SIG"
        assert el.get("data-from-layer") == mv["from_layer"] == "F.Cu"
        assert el.get("data-to-layer") == mv["to_layer"] == "B.Cu"
        assert el.get("data-drill-mm") == f"{mv['drill_mm']:.3f}" == "0.300"
        assert el.get("data-annular-ring-mm") == \
            f"{mv['annular_ring_mm']:.3f}" == "0.150"

    def test_via_geometry_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        el = find_by_id(root, "via-V1")
        cx, cy = manifest["vias"][0]["center_mm"]
        assert el.get("cx") == f"{cx:.6f}"
        assert el.get("cy") == f"{cy:.6f}"
        r = manifest["vias"][0]["drill_mm"] / 2 \
            + manifest["vias"][0]["annular_ring_mm"]
        assert el.get("r") == f"{r:.6f}"


# ----------------------------------------------------- keepout 与 board edge

class TestKeepoutAndBoardEdge:
    def test_keepout_rect_attributes(self, package):
        _, _, svg, _ = package
        root = ET.fromstring(svg)
        el = find_by_id(root, "keepout-K1")
        assert el.get("data-object-kind") == "keepout"
        assert el.get("data-keepout-id") == "K1"
        assert el.get("data-layers") == "F.Cu B.Cu"
        x0, y0, x1, y1 = (20.0, 14.0, 30.0, 22.0)
        assert el.get("x") == f"{x0:.6f}"
        assert el.get("y") == f"{y0:.6f}"
        assert el.get("width") == f"{x1 - x0:.6f}"
        assert el.get("height") == f"{y1 - y0:.6f}"

    def test_board_edge_rect_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        el = find_by_id(root, "board-edge")
        assert el.get("data-object-kind") == "board_edge"
        x0, y0, x1, y1 = manifest["board_bbox_mm"]
        assert el.get("x") == f"{x0:.6f}"
        assert el.get("y") == f"{y0:.6f}"
        assert el.get("width") == f"{x1 - x0:.6f}"
        assert el.get("height") == f"{y1 - y0:.6f}"


# ----------------------------------------------------------------- 图例

class TestLegend:
    def test_legend_record_has_version_and_sha256(self):
        rec = s4.legend_record()
        assert rec["legend_version"] == "pcbflow-v4-legend-1"
        assert re.fullmatch(r"[0-9a-f]{64}", rec["legend_sha256"])
        assert rec["color_is_visual_only"] is True

    def test_legend_sha256_recomputable_independently(self):
        """legend_sha256 对剔除 *_sha256 后 canonical 形式可独立重算。"""
        rec = s4.legend_record()
        assert rec["legend_sha256"] == canon_sha256(rec)

    def test_legend_entries_cover_all_line_types_with_machine_facts(self):
        rec = s4.legend_record()
        line_entries = {e["value"]: e for e in rec["entries"]
                        if e["item"] == "line_type"}
        assert set(line_entries) == set(s4.LINE_TYPES)
        for lt, e in line_entries.items():
            assert e["color"] == s4.LEGEND_COLORS[lt]
            assert e["machine_fact"] == f"data-line-type={lt}"
        states = {e["value"] for e in rec["entries"] if e["item"] == "state"}
        assert {"candidate", "conflict"} <= states

    def test_legend_record_deterministic(self):
        assert s4.legend_record() == s4.legend_record()

    def test_manifest_and_svg_legend_binding_consistent(self, package):
        _, _, svg, manifest = package
        rec = s4.legend_record()
        assert manifest["legend_version"] == rec["legend_version"]
        assert manifest["legend_sha256"] == rec["legend_sha256"]
        root = ET.fromstring(svg)
        g = find_by_id(root, "legend")
        assert g.get("data-legend-version") == rec["legend_version"]
        assert g.get("data-legend-sha256") == rec["legend_sha256"]

    def test_tampered_svg_legend_sha_detected(self, package):
        _, _, svg, manifest = package
        svg_mut = svg.replace(
            f'data-legend-sha256="{s4.legend_record()["legend_sha256"]}"',
            'data-legend-sha256="' + "0" * 64 + '"', 1)
        assert svg_mut != svg
        out = s4.verify_consistency(svg_mut, manifest)
        assert isinstance(out, list) and out
        assert any("图例" in v for v in out)


# -------------------------------------- 颜色/线型仅是 class 编码（§2.2）

class TestColorIsVisualOnly:
    def test_style_block_defines_visual_classes(self, package):
        _, _, svg, manifest = package
        for mr in manifest["routes"]:
            assert f".route-{mr['line_type']}{{" in svg

    def test_changing_class_does_not_affect_data_parsing(self, package):
        """改 class（颜色/线型/层虚饰）后：
        data-* 字段解析结果不变，一致性核对仍清白。"""
        _, _, svg, manifest = package
        old_class = "route route-signal route-candidate layer-FCu"
        new_class = "route route-power route-conflict layer-BCu"
        assert f'class="{old_class}"' in svg
        svg_mut = svg.replace(f'class="{old_class}"',
                              f'class="{new_class}"', 1)
        root0, root1 = ET.fromstring(svg), ET.fromstring(svg_mut)
        g0, g1 = find_by_id(root0, "route-R-SIG"), \
            find_by_id(root1, "route-R-SIG")
        for name in s4.SVG_ROUTE_ATTRS:
            assert g0.get(name) == g1.get(name), name
        assert s4.parse_svg_polyline(svg_mut, "route-R-SIG") == \
            s4.parse_svg_polyline(svg, "route-R-SIG")
        assert s4.verify_consistency(svg_mut, manifest) == []

    def test_machine_facts_live_in_data_attrs_not_class(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            path = list(g)[0]
            # class 只是可视化编码
            assert "route" in path.get("class")
            # 机器事实在 data-* 属性
            assert g.get("data-line-type") == mr["line_type"]
            assert g.get("data-state") == mr["state"]
            assert g.get("data-layer") == mr["layer"]
