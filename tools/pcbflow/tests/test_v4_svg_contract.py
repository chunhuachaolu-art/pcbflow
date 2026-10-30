"""V4.0-A SVG 数据合同测试（V4-SUPERVISOR-PLAN §3）。

被测生产模块：pcbflow/svg_route_package.py。
覆盖：
- 根节点合同：data-pcbflow-schema="v4-svg-route-2"、snapshot/manifest
  sha256 绑定、data-coordinate-system="pcbflow-internal-mm"、
  data-y-axis="down-positive"、mm viewBox（板 bbox 原点 - 2.0mm 边距，
  实现偏差：非 "0 0" 平移）、preserveAspectRatio="xMidYMid meet"；
- route 对象全套 data-* 属性（route_id/net_id/relation_id/line_type/
  parent_id/layer/width_mm/state/source/endpoint/constraint-refs）
  存在且与 manifest 对应 entry 一致。

夹具全部为代码内合成最小字典（3 条 route + 差分对/bus 关系 + 1 via +
1 keepout），不依赖外部文件、不访问网络。
"""

import hashlib
import json
import re
import xml.etree.ElementTree as ET

import pytest

from pcbflow import svg_route_package as s4

SVG_NS = "http://www.w3.org/2000/svg"
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


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
    """按模块合同（§9）：canonical hash 前递归剔除 *_sha256 键。"""
    if isinstance(obj, dict):
        return {k: strip_sha(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [strip_sha(v) for v in obj]
    return obj


def canon_sha256(obj):
    """独立重算 canonical sha256（sort_keys + 紧凑分隔符 + utf-8）。"""
    text = json.dumps(strip_sha(obj), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ 根节点合同

class TestRootContract:
    def test_root_is_namespaced_svg(self, package):
        _, _, svg, _ = package
        root = ET.fromstring(svg)
        assert root.tag == f"{{{SVG_NS}}}svg"

    def test_schema_version_attribute(self, package):
        _, _, svg, _ = package
        root = ET.fromstring(svg)
        assert root.get("version") == "1.1"
        assert root.get("data-pcbflow-schema") == "v4-svg-route-2"

    def test_coordinate_system_and_y_axis(self, package):
        _, _, svg, _ = package
        root = ET.fromstring(svg)
        assert root.get("data-coordinate-system") == "pcbflow-internal-mm"
        assert root.get("data-y-axis") == "down-positive"

    def test_preserve_aspect_ratio(self, package):
        _, _, svg, _ = package
        root = ET.fromstring(svg)
        assert root.get("preserveAspectRatio") == "xMidYMid meet"

    def test_viewbox_is_mm_world_coords_with_margin(self, package):
        """实现约定：viewBox 直接用板 mm 世界坐标，
        min-x/min-y = board bbox 原点 - MARGIN_MM(2.0)，非 "0 0" 平移。"""
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        x0, y0, x1, y1 = manifest["board_bbox_mm"]
        m = s4.MARGIN_MM
        expect = (f"{x0 - m:.6f} {y0 - m:.6f} "
                  f"{(x1 - x0) + 2 * m:.6f} {(y1 - y0) + 2 * m:.6f}")
        assert root.get("viewBox") == expect
        assert root.get("viewBox") == "-2.000000 -2.000000 44.000000 34.000000"

    def test_manifest_sha256_binding(self, package):
        """SVG 根节点绑定 route-manifest payload sha256（64 位小写 hex）。"""
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        bound = root.get("data-route-manifest-sha256")
        assert SHA256_HEX_RE.fullmatch(bound)
        assert bound == manifest["manifest_payload_sha256"]
        # 独立重算：canonical(manifest 剔除 *_sha256) 的 sha256
        assert manifest["manifest_payload_sha256"] == canon_sha256(manifest)

    def test_snapshot_sha256_binding(self, package):
        """SVG 根节点与 manifest 双向绑定 board snapshot sha256。"""
        board, _, svg, manifest = package
        root = ET.fromstring(svg)
        bound = root.get("data-board-snapshot-sha256")
        assert SHA256_HEX_RE.fullmatch(bound)
        assert bound == manifest["board_snapshot_sha256"]
        assert manifest["board_snapshot_sha256"] == canon_sha256(board)

    def test_manifest_coordinate_system_declared(self, package):
        _, _, _, manifest = package
        assert manifest["schema_version"] == "v4-route-manifest-2"
        assert manifest["svg_coordinate_system"] == "pcbflow-internal-mm"
        assert manifest["board_bbox_mm"] == [0.0, 0.0, 40.0, 30.0]


# ------------------------------------------------- route 对象 data-* 合同

class TestRouteObjectContract:
    def test_every_manifest_route_has_group_with_full_attrs(self, package):
        """route 全套 data-* 属性存在（以模块常量全集为准）。"""
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            assert g.tag == f"{{{SVG_NS}}}g"
            assert g.get("data-object-kind") == "route_segment"
            for name in s4.SVG_ROUTE_ATTRS:
                assert name in g.attrib, (
                    f"route {mr['route_id']}: 缺属性 {name}")

    def test_route_identity_attributes_match_manifest(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            assert g.get("id") == f"route-{mr['route_id']}"
            assert g.get("data-route-id") == mr["route_id"]
            assert g.get("data-net-id") == mr["net_id"]
            # data-relation-id 是空格连接的 relation_ids 列表
            assert g.get("data-relation-id") == " ".join(mr["relation_ids"])

    def test_route_semantic_attributes_match_manifest(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            assert g.get("data-line-type") == mr["line_type"]
            assert g.get("data-line-type") in s4.LINE_TYPES
            assert g.get("data-parent-id") == (mr["parent_id"] or "")
            assert g.get("data-layer") == mr["layer"]
            assert g.get("data-width-mm") == f"{mr['width_mm']:.3f}"
            assert g.get("data-state") == mr["state"]
            assert g.get("data-state") in s4.ROUTE_STATES
            assert g.get("data-source") == mr["source"]
            assert g.get("data-source") in s4.ROUTE_SOURCES

    def test_route_endpoint_and_constraint_attributes(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            assert g.get("data-endpoint-start") == mr["endpoint_ids"][0]
            assert g.get("data-endpoint-end") == mr["endpoint_ids"][1]
            assert g.get("data-constraint-refs") == \
                ",".join(mr["constraint_refs"])

    def test_route_group_contains_single_geometry_path(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for mr in manifest["routes"]:
            g = find_by_id(root, mr["svg_id"])
            kids = list(g)
            assert len(kids) == 1
            path = kids[0]
            assert path.tag == f"{{{SVG_NS}}}path"
            assert path.get("id") == f"geom-{mr['route_id']}"
            d = path.get("d", "")
            assert d.startswith("M ")
            # 坐标一律 6 位定点小数
            for tok in d.split(" ")[1::3]:
                assert re.fullmatch(r"-?\d+\.\d{6}", tok), tok

    def test_routes_sorted_by_route_id_in_svg(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        order = [g.get("data-route-id") for g in root.iter()
                 if g.get("data-object-kind") == "route_segment"]
        assert order == sorted(r["route_id"] for r in manifest["routes"])


# ------------------------------------------------------- 端到端一致性底线

class TestPackageConsistencyBaseline:
    def test_verify_clean_without_snapshot(self, package):
        _, _, svg, manifest = package
        assert s4.verify_consistency(svg, manifest) == []

    def test_verify_clean_with_matching_snapshot(self, package):
        board, _, svg, manifest = package
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []
