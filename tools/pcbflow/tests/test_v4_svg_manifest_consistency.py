"""V4.0-A verify_consistency 一致性核对测试（方案 §4 解析规则 1–5）。

被测生产模块：pcbflow/svg_route_package.py。
覆盖：
- 规则 1：svg_id/route_id/net_id 与 manifest entry 一一对应
  （删除 route 组 / manifest 改名 / 改 net_id / 改 svg_id 均必检出）；
- 规则 2：SVG path 坐标篡改必检出（零容差）；
- 规则 3：layer/width/state 字段不一致必检出；
- 规则 5：snapshot hash 不符、manifest payload hash 不符、
  SVG 根节点 hash 属性与 manifest 不符必检出；
- blocked 语义：任何不一致 = 返回非空违规列表，完全一致 = 返回 []；
  语法错误/垃圾输入不抛异常、同样按违规（fail-closed，绝不以视觉为准）。
"""

import copy
import xml.etree.ElementTree as ET

import pytest

from pcbflow import svg_route_package as s4

SVG_NS = "http://www.w3.org/2000/svg"

ET.register_namespace("", SVG_NS)


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
    return board, svg, manifest


def mutate_svg(svg_text, mutator):
    """解析 → 修改 → 序列化（保持命名空间与语义，只改目标处）。"""
    root = ET.fromstring(svg_text)
    mutator(root)
    return ET.tostring(root, encoding="unicode")


def find_by_id(root, el_id):
    for el in root.iter():
        if isinstance(el.tag, str) and el.attrib.get("id") == el_id:
            return el
    raise AssertionError(f"SVG 中找不到 id={el_id!r} 的元素")


def assert_blocked(violations, needle=None):
    """blocked 语义：返回非空字符串违规列表；needle 用于确认命中点。"""
    assert isinstance(violations, list) and violations, (
        f"期望检出违规，实际返回 {violations!r}")
    assert all(isinstance(v, str) and v for v in violations)
    if needle is not None:
        assert any(needle in v for v in violations), violations


# ------------------------------------------------------------- 正向基线

class TestCleanBaseline:
    def test_pristine_package_verifies_empty(self, package):
        _, svg, manifest = package
        assert s4.verify_consistency(svg, manifest) == []

    def test_pristine_with_matching_snapshot_verifies_empty(self, package):
        board, svg, manifest = package
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []


# -------------------------------------------- 规则 1：身份一一对应（含删除/改名）

class TestRule1Identity:
    def test_deleted_svg_route_group_detected(self, package):
        """删除 SVG 中一个 route 组 → 该 route 仅在 manifest 中 → blocked。"""
        _, svg, manifest = package

        def drop(root):
            root.remove(find_by_id(root, "route-R-SIG"))

        svg_mut = mutate_svg(svg, drop)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "仅在 manifest 中")

    def test_manifest_route_rename_detected(self, package):
        """manifest 侧 route_id 改名 → route 仅在 SVG 中 → blocked。"""
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        for e in man_mut["routes"]:
            if e["route_id"] == "R-SIG":
                e["route_id"] = "R-XX"
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "仅在 SVG 中")

    def test_net_id_mismatch_detected(self, package):
        _, svg, manifest = package

        def renet(root):
            find_by_id(root, "route-R-SIG").set("data-net-id", "N9")

        svg_mut = mutate_svg(svg, renet)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, ".net_id:")

    def test_manifest_svg_id_mismatch_detected(self, package):
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        for e in man_mut["routes"]:
            if e["route_id"] == "R-SIG":
                e["svg_id"] = "route-OTHER"
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "svg_id")

    def test_via_set_mismatch_detected(self, package):
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        man_mut["vias"] = []
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "via 集合不等")

    def test_relation_set_mismatch_detected(self, package):
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        man_mut["relations"] = [
            r for r in man_mut["relations"] if r["relation_id"] != "DP1"]
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "relation 集合不等")


# -------------------------------------- 规则 2：坐标零容差（含 viewBox）

class TestRule2Geometry:
    def test_tampered_path_coordinate_detected(self, package):
        """SVG path 坐标篡改（保持 6 位定点格式）→ 与 polyline_mm 不符。"""
        _, svg, manifest = package

        def move(root):
            path = find_by_id(root, "geom-R-SIG")
            path.set("d", "M 12.450000 8.200000 L 18.700000 8.200000")

        svg_mut = mutate_svg(svg, move)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "SVG path 坐标与 polyline_mm 不一致")

    def test_tampered_via_center_detected(self, package):
        _, svg, manifest = package

        def move(root):
            find_by_id(root, "via-V1").set("cx", "18.700001")

        svg_mut = mutate_svg(svg, move)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "via V1: SVG cx/cy 与 center_mm 不一致")

    def test_tampered_viewbox_detected(self, package):
        _, svg, manifest = package

        def shrink(root):
            root.set("viewBox", "-2.000000 -2.000000 40.000000 34.000000")

        svg_mut = mutate_svg(svg, shrink)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "viewBox")


# -------------------------------- 规则 3：layer/width/state 等字段一致

class TestRule3Fields:
    def test_layer_mismatch_detected(self, package):
        _, svg, manifest = package

        def relayer(root):
            find_by_id(root, "route-R-SIG").set("data-layer", "B.Cu")

        svg_mut = mutate_svg(svg, relayer)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, ".layer:")

    def test_state_mismatch_detected(self, package):
        _, svg, manifest = package

        def restate(root):
            find_by_id(root, "route-R-SIG").set("data-state", "conflict")

        svg_mut = mutate_svg(svg, restate)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, ".state:")

    def test_width_mismatch_detected(self, package):
        _, svg, manifest = package

        def rewidth(root):
            find_by_id(root, "route-R-SIG").set("data-width-mm", "0.400")

        svg_mut = mutate_svg(svg, rewidth)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, ".width_mm:")

    def test_line_type_mismatch_detected(self, package):
        _, svg, manifest = package

        def retype(root):
            find_by_id(root, "route-R-DP").set("data-line-type", "signal")

        svg_mut = mutate_svg(svg, retype)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, ".line_type:")

    def test_via_layer_mismatch_detected(self, package):
        _, svg, manifest = package

        def relayer(root):
            find_by_id(root, "via-V1").set("data-to-layer", "F.Cu")

        svg_mut = mutate_svg(svg, relayer)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "via V1.to_layer:")

    def test_relation_member_mismatch_detected(self, package):
        _, svg, manifest = package

        def remember(root):
            find_by_id(root, "relation-DP1").set(
                "data-member-ids", "USB_DP USB_DN N1")

        svg_mut = mutate_svg(svg, remember)
        out = s4.verify_consistency(svg_mut, manifest)
        assert_blocked(out, "relation DP1.members:")


# ------------------------------------- 规则 5：hash 绑定（snapshot/payload）

class TestRule5HashBinding:
    def test_stale_snapshot_detected(self, package):
        """快照被篡改/过期（hash 不符）→ blocked。"""
        _, svg, manifest = package
        snap = copy.deepcopy(make_board())
        snap["board"]["bbox_mm"] = [0.0, 0.0, 40.0, 30.5]
        out = s4.verify_consistency(svg, manifest, snapshot=snap)
        assert_blocked(out, "snapshot sha256")

    def test_tampered_manifest_detected_by_payload_recompute(self, package):
        """manifest 内容被篡改 → payload sha256 与重算值不符 → blocked。"""
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        man_mut["routes"][0]["source"] = "human_edit"
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "manifest_payload_sha256 != 重算值")

    def test_svg_manifest_sha_attribute_vs_payload_mismatch(self, package):
        """SVG 根节点 data-route-manifest-sha256 与 manifest payload 不符。"""
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        man_mut["manifest_payload_sha256"] = "f" * 64
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "SVG data-route-manifest-sha256 !=")

    def test_svg_snapshot_sha_attribute_vs_manifest_mismatch(self, package):
        _, svg, manifest = package
        man_mut = copy.deepcopy(manifest)
        man_mut["board_snapshot_sha256"] = "e" * 64
        out = s4.verify_consistency(svg, man_mut)
        assert_blocked(out, "SVG data-board-snapshot-sha256 !=")


# ------------------------------------------------ blocked / fail-closed 语义

class TestBlockedSemantics:
    def test_any_violation_means_blocked_nonempty_list(self, package):
        """blocked 语义：一致 ⇒ []；任何不一致 ⇒ 非空列表（不抛异常）。"""
        _, svg, manifest = package
        assert s4.verify_consistency(svg, manifest) == []
        man_mut = copy.deepcopy(manifest)
        man_mut["routes"][0]["state"] = "rejected"
        out = s4.verify_consistency(svg, man_mut)
        assert isinstance(out, list) and out

    def test_xml_syntax_error_reported_not_raised(self, package):
        _, _, manifest = package
        out = s4.verify_consistency("<svg", manifest)
        assert isinstance(out, list) and out

    def test_non_object_inputs_reported_not_raised(self, package):
        _, svg, manifest = package
        assert s4.verify_consistency(svg, None) == ["manifest: 不是对象"]
        out = s4.verify_consistency(None, manifest)
        assert out == ["svg_text: 不是字符串"]
