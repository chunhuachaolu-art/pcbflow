"""V4.0-A 坐标 round-trip 与 canonical 确定性测试。

被测生产模块：pcbflow/svg_route_package.py。
覆盖：
- parse_svg_polyline(svg, svg_id) 与 manifest.polyline_mm 量化 6 位后
  逐点零容差相等（实现约定：path d 直接用板 mm 世界坐标，不做 "0 0"
  平移，因此可零容差 round-trip）；
- path d 非法结构（首命令非 M / 中途命令非 L / token 数不合法 /
  坐标非 6 位定点小数 / 找不到或重复 id / 非 route 组）抛 ValueError
  （_ContractError 是 ValueError 子类，fail-closed）；
- 多次 build 同输入逐字节一致（canonical：无 wall-clock、无主机路径、
  稳定排序、固定小数位）。
"""

import copy
import json
import xml.etree.ElementTree as ET

import pytest

from pcbflow import svg_route_package as s4


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


def q6(pt):
    return [round(float(pt[0]), 6), round(float(pt[1]), 6)]


@pytest.fixture(scope="module")
def package():
    board, ref = make_board(), make_ref()
    svg, manifest = s4.build(board, ref)
    return board, ref, svg, manifest


MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">'
    '<g id="route-R1" data-object-kind="route_segment">'
    '<path id="geom-R1" d="{d}"/>'
    "</g></svg>"
)


# -------------------------------------------------------- 零容差 round-trip

class TestCoordinateRoundTrip:
    def test_parsed_polyline_equals_manifest_zero_tolerance(self, package):
        """每个 route：解析 SVG path d 与 manifest.polyline_mm
        各自量化 6 位后逐点相等（零容差，无近似比较）。"""
        _, _, svg, manifest = package
        for mr in manifest["routes"]:
            parsed = s4.parse_svg_polyline(svg, mr["svg_id"])
            expected = [q6(p) for p in mr["polyline_mm"]]
            assert [q6(p) for p in parsed] == expected
            assert parsed == expected  # 量化前也已精确相等

    def test_parsed_point_count_matches_manifest(self, package):
        _, _, svg, manifest = package
        for mr in manifest["routes"]:
            parsed = s4.parse_svg_polyline(svg, mr["svg_id"])
            assert len(parsed) == len(mr["polyline_mm"]) >= 2

    def test_ref_input_quantized_into_roundtrip(self, package):
        """ref 原始坐标经量化（6 位）进入 SVG 与 manifest，两侧仍一致。"""
        board, ref = make_board(), make_ref()
        ref["routes"][0]["polyline_mm"] = [[1.2345675, 2.3456785],
                                           [3.0, 4.0]]
        svg, manifest = s4.build(board, ref)
        mr = next(r for r in manifest["routes"]
                  if r["route_id"] == "R-SIG")
        parsed = s4.parse_svg_polyline(svg, "route-R-SIG")
        assert [q6(p) for p in parsed] == [q6(p) for p in mr["polyline_mm"]]
        # 量化语义：7 位小数输入被收敛到 6 位
        assert q6(parsed[0]) == [1.234568, 2.345678] or \
            q6(parsed[0]) == [round(1.2345675, 6), round(2.3456785, 6)]


# ------------------------------------------------ 非法 path d 结构 → ValueError

class TestIllegalPathD:
    def test_first_command_not_m_raises(self):
        svg = MINIMAL_SVG.format(
            d="C 0.000000 0.000000 L 1.000000 2.000000")
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_middle_command_not_l_raises(self):
        svg = MINIMAL_SVG.format(
            d="M 0.000000 0.000000 X 1.000000 2.000000")
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_odd_token_count_raises(self):
        svg = MINIMAL_SVG.format(d="M 0.000000 0.000000 L 1.000000")
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_too_few_tokens_raises(self):
        svg = MINIMAL_SVG.format(d="M 0.000000 0.000000")
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_coordinate_not_fixed_point_6_raises(self):
        """坐标不是 6 位定点小数（合同格式）→ ValueError。"""
        for bad in ("M 0.0 0.000000 L 1.000000 2.000000",
                    "M 0.000000 0 L 1.000000 2.000000",
                    "M 1e0 0.000000 L 1.000000 2.000000",
                    "M 0.0000000 0.000000 L 1.000000 2.000000"):
            svg = MINIMAL_SVG.format(d=bad)
            with pytest.raises(ValueError):
                s4.parse_svg_polyline(svg, "route-R1")

    def test_missing_svg_id_raises(self, package):
        _, _, svg, _ = package
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-NOPE")

    def test_non_group_or_non_route_element_raises(self, package):
        _, _, svg, _ = package
        # geom-* 是 path 不是 route 组
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "geom-R-SIG")
        # legend 组不是 route_segment
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "legend")

    def test_duplicate_svg_id_raises(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg">'
               '<g id="route-R1" data-object-kind="route_segment">'
               '<path id="geom-R1" d="M 0.000000 0.000000'
               ' L 1.000000 2.000000"/></g>'
               '<g id="route-R1" data-object-kind="route_segment">'
               '<path id="geom-R1" d="M 0.000000 0.000000'
               ' L 1.000000 2.000000"/></g></svg>')
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_route_group_with_extra_child_raises(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg">'
               '<g id="route-R1" data-object-kind="route_segment">'
               '<path id="geom-R1" d="M 0.000000 0.000000'
               ' L 1.000000 2.000000"/>'
               '<path id="geom-extra" d="M 0.000000 0.000000'
               ' L 1.000000 2.000000"/></g></svg>')
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, "route-R1")

    def test_malformed_xml_raises(self):
        with pytest.raises(ValueError):
            s4.parse_svg_polyline("<svg", "route-R1")


# ------------------------------------------------- canonical 逐字节确定性

class TestCanonicalDeterminism:
    def test_double_build_svg_byte_identical(self, package):
        board, ref = make_board(), make_ref()
        svg_a, _ = s4.build(board, ref)
        svg_b, _ = s4.build(board, ref)
        assert svg_a.encode("utf-8") == svg_b.encode("utf-8")
        assert svg_a == svg_b

    def test_double_build_manifest_identical(self, package):
        board, ref = make_board(), make_ref()
        _, man_a = s4.build(board, ref)
        _, man_b = s4.build(board, ref)
        assert man_a == man_b
        assert json.dumps(man_a, sort_keys=True,
                          separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8") \
            == json.dumps(man_b, sort_keys=True,
                          separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")

    def test_rebuild_svg_from_manifest_reproducible(self, package):
        board, _, svg, manifest = package
        assert s4.build_svg(board, manifest) == svg

    def test_no_wall_clock_or_host_paths_in_artifacts(self, package):
        board, _, svg, manifest = package
        text = svg + json.dumps(manifest, sort_keys=True,
                                ensure_ascii=False)
        for forbidden in ("C:\\", "/home/", "/Users/", "started_at",
                          "elapsed", "timestamp"):
            assert forbidden not in text

    def test_input_not_mutated_by_build(self, package):
        board, ref = make_board(), make_ref()
        board_snap = copy.deepcopy(board)
        ref_snap = copy.deepcopy(ref)
        s4.build(board, ref)
        assert board == board_snap and ref == ref_snap
