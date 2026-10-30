"""E0 核对器测试：六项 check 正例 + 各自负例 + roundtrip 阈值边界。"""

import json
import os
import tempfile
import unittest

from pcbflow.v4exp import e0_checks, e0_parse, model, render_png
from pcbflow.v4exp.tests.test_v4exp_e0_fixture import (build_memory_fixture,
                                                       copy_real_fixture)


def _deep_copy(obj):
    return json.loads(json.dumps(obj))


class TestChecksPositive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.ref, cls.manifest, cls.svg = build_memory_fixture()
        cls.board_obj = cls.board.to_obj()
        cls.facts = e0_parse.parse_svg(cls.svg)
        cls.bbox = cls.board_obj["board"]["bbox_mm"]

    def test_identity_recovery_pass(self):
        r = e0_checks.identity_recovery(self.facts, self.manifest)
        self.assertTrue(r["pass"], r["reason"])

    def test_consistency_pass(self):
        r = e0_checks.manifest_svg_consistency(self.facts, self.manifest,
                                               self.bbox)
        self.assertTrue(r["pass"], r["reason"])

    def test_roundtrip_pass(self):
        r = e0_checks.roundtrip_mm(self.facts, self.manifest, self.bbox)
        self.assertTrue(r["pass"], r["reason"])
        self.assertIn("max_err=", r["reason"])

    def test_hash_binding_pass(self):
        r = e0_checks.hash_binding(self.facts, self.manifest, self.board_obj)
        self.assertTrue(r["pass"], r["reason"])

    def test_color_independence_pass(self):
        r = e0_checks.color_independence(self.svg, self.facts)
        self.assertTrue(r["pass"], r["reason"])

    def test_resolution_invariance_pass_real_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_real_fixture(tmp, with_scenario_manifest=False)
            r = e0_checks.resolution_invariance(
                "dev-f1-01", self.manifest_of(tmp), self.bbox, tmp)
        self.assertTrue(r["pass"], r["reason"])

    def manifest_of(self, source_dir):
        return model.read_json(os.path.join(source_dir,
                                            "route-manifest-dev-f1-01.json"))

    def test_resolution_invariance_pass_rendered_pngs(self):
        # 用内存夹具现渲染 4 分辨率 PNG（与 A 包渲染器同源）验证检查器
        with tempfile.TemporaryDirectory() as tmp:
            for w, h in render_png.RESOLUTIONS:
                img = render_png.render(self.board, self.ref, self.manifest,
                                        w, h)
                img.save(os.path.join(
                    tmp, f"route-preview-dev-f3-01-{w}x{h}.png"),
                    format="PNG")
            r = e0_checks.resolution_invariance(
                "dev-f3-01", self.manifest, self.bbox, tmp)
        self.assertTrue(r["pass"], r["reason"])


class TestChecksNegative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.ref, cls.manifest, cls.svg = build_memory_fixture()
        cls.board_obj = cls.board.to_obj()
        cls.facts = e0_parse.parse_svg(cls.svg)
        cls.bbox = cls.board_obj["board"]["bbox_mm"]

    def _facts_with(self, **overrides):
        facts = _deep_copy(self.facts)
        facts.update(overrides)
        return facts

    def test_identity_missing_route(self):
        facts = _deep_copy(self.facts)
        facts["routes"] = facts["routes"][1:]
        r = e0_checks.identity_recovery(facts, self.manifest)
        self.assertFalse(r["pass"])
        self.assertIn("route 集合不等", r["reason"])

    def test_identity_duplicate_route_id(self):
        facts = _deep_copy(self.facts)
        facts["routes"].append(_deep_copy(facts["routes"][0]))
        r = e0_checks.identity_recovery(facts, self.manifest)
        self.assertFalse(r["pass"])
        self.assertIn("route_id 重复", r["reason"])

    def test_identity_via_parent_missing(self):
        facts = _deep_copy(self.facts)
        man = _deep_copy(self.manifest)
        ghost = {"via_id": "nX-V99", "net_id": "n1", "parent_id": "ghost",
                 "from_layer": "F.Cu", "to_layer": "B.Cu",
                 "center_mm": [1.0, 1.0], "drill_mm": 0.3,
                 "annular_ring_mm": 0.15}
        facts["vias"].append(_deep_copy(ghost))
        man["vias"].append(_deep_copy(ghost))
        r = e0_checks.identity_recovery(facts, man)
        self.assertFalse(r["pass"])
        self.assertIn("parent_id", r["reason"])

    def test_identity_relation_member_unknown_net(self):
        # identity 只比对集合：同 id 改 members 后 identity 仍过；
        # 未知 net 的 members 由 consistency 咬合
        man = _deep_copy(self.manifest)
        man["relations"][0]["members"] = ["nZ"]
        r = e0_checks.identity_recovery(self.facts, man)
        self.assertTrue(r["pass"], r["reason"])
        r2 = e0_checks.manifest_svg_consistency(self.facts, man, self.bbox)
        self.assertFalse(r2["pass"])
        self.assertIn("members", r2["reason"])

    def test_identity_relation_member_unknown_net_in_svg(self):
        # SVG 侧 relation 出现注册表外的 net -> identity 直接咬合
        facts = _deep_copy(self.facts)
        facts["relations"][0]["member_ids"] = ["nZ"]
        r = e0_checks.identity_recovery(facts, self.manifest)
        self.assertFalse(r["pass"])
        self.assertIn("不是存在的 net", r["reason"])

    def test_identity_parent_cycle(self):
        facts = _deep_copy(self.facts)
        if len(facts["routes"]) < 2:
            self.skipTest("夹具 route 不足")
        facts["routes"][0]["parent_id"] = facts["routes"][1]["route_id"]
        facts["routes"][1]["parent_id"] = facts["routes"][0]["route_id"]
        r = e0_checks.identity_recovery(facts, self.manifest)
        self.assertFalse(r["pass"])
        self.assertIn("环", r["reason"])

    def test_consistency_width_mismatch(self):
        facts = _deep_copy(self.facts)
        facts["routes"][0]["width_mm"] = facts["routes"][0]["width_mm"] + 0.1
        r = e0_checks.manifest_svg_consistency(facts, self.manifest,
                                               self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("width_mm", r["reason"])

    def test_consistency_polyline_mismatch(self):
        facts = _deep_copy(self.facts)
        facts["routes"][0]["polyline_mm"][0][0] += 0.004
        r = e0_checks.manifest_svg_consistency(facts, self.manifest,
                                               self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("polyline_mm", r["reason"])

    def test_consistency_layer_mismatch(self):
        facts = _deep_copy(self.facts)
        facts["routes"][0]["layer"] = \
            "B.Cu" if facts["routes"][0]["layer"] == "F.Cu" else "F.Cu"
        r = e0_checks.manifest_svg_consistency(facts, self.manifest,
                                               self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("layer", r["reason"])

    def test_consistency_net_mismatch(self):
        facts = _deep_copy(self.facts)
        facts["routes"][0]["net_id"] = "nX"
        r = e0_checks.manifest_svg_consistency(facts, self.manifest,
                                               self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("net_id", r["reason"])

    def test_roundtrip_threshold_beyond(self):
        man = _deep_copy(self.manifest)
        man["routes"][0]["polyline_mm"][0][0] += 0.002
        r = e0_checks.roundtrip_mm(self.facts, man, self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("误差", r["reason"])

    def test_roundtrip_threshold_within(self):
        man = _deep_copy(self.manifest)
        man["routes"][0]["polyline_mm"][0][0] += 0.0005
        r = e0_checks.roundtrip_mm(self.facts, man, self.bbox)
        self.assertTrue(r["pass"], r["reason"])

    def test_roundtrip_via_center_beyond(self):
        facts = _deep_copy(self.facts)
        man = _deep_copy(self.manifest)
        # manifest 是板 mm 坐标；facts.center_mm 是 SVG 本地坐标（差 sx/sy）
        sx = self.bbox[0] - model.MARGIN_MM
        sy = self.bbox[1] - model.MARGIN_MM
        via = {"via_id": "nX-V99", "net_id": "n1", "parent_id": None,
               "from_layer": "F.Cu", "to_layer": "B.Cu",
               "center_mm": [1.0 - sx, 1.0 - sy], "drill_mm": 0.3,
               "annular_ring_mm": 0.15, "svg_id": "via-nX-V99"}
        facts["vias"] = [_deep_copy(via)]
        man["vias"] = [{"via_id": "nX-V99", "net_id": "n1",
                        "parent_id": None, "from_layer": "F.Cu",
                        "to_layer": "B.Cu", "center_mm": [1.0, 1.0],
                        "drill_mm": 0.3, "annular_ring_mm": 0.15}]
        r = e0_checks.roundtrip_mm(facts, man, self.bbox)
        self.assertTrue(r["pass"], r["reason"])
        man["vias"][0]["center_mm"][1] += 0.002
        r = e0_checks.roundtrip_mm(facts, man, self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("center 误差", r["reason"])

    def test_roundtrip_viewbox_mismatch(self):
        facts = self._facts_with(viewbox_wh=[10.0, 10.0])
        r = e0_checks.roundtrip_mm(facts, self.manifest, self.bbox)
        self.assertFalse(r["pass"])
        self.assertIn("viewBox", r["reason"])

    def test_hash_tampered_manifest(self):
        man = _deep_copy(self.manifest)
        man["routes"].pop(0)
        r = e0_checks.hash_binding(self.facts, man, self.board_obj)
        self.assertFalse(r["pass"])
        self.assertIn("manifest_payload_sha256", r["reason"])

    def test_hash_tampered_board(self):
        board_obj = _deep_copy(self.board_obj)
        board_obj["seed"] += 1
        r = e0_checks.hash_binding(self.facts, self.manifest, board_obj)
        self.assertFalse(r["pass"])
        self.assertIn("board_snapshot_sha256", r["reason"])

    def test_hash_tampered_svg_root(self):
        facts = self._facts_with(route_manifest_sha256="0" * 64)
        r = e0_checks.hash_binding(facts, self.manifest, self.board_obj)
        self.assertFalse(r["pass"])
        self.assertIn("data-route-manifest-sha256", r["reason"])

    def test_color_rewriter_broken_detected(self):
        # 无颜色 token 的文本上，重写器失效必须被发现而不是静默通过
        plain = '<svg xmlns="http://www.w3.org/2000/svg"/>'
        r = e0_checks.color_independence(plain, self.facts,
                                         base_svg_text=plain)
        self.assertFalse(r["pass"])
        self.assertIn("替换器失效", r["reason"])

    def test_color_facts_changed_detected(self):
        other_facts = _deep_copy(self.facts)
        other_facts["routes"][0]["net_id"] = "nX"
        r = e0_checks.color_independence(self.svg, other_facts)
        self.assertFalse(r["pass"])
        self.assertIn("facts 改变", r["reason"])

    def test_resolution_missing_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = e0_checks.resolution_invariance(
                "dev-f1-01", self.manifest, self.bbox, tmp)
        self.assertFalse(r["pass"])
        self.assertIn("缺 PNG", r["reason"])

    def test_resolution_wrong_size_detected(self):
        # 四个分辨率名下的文件尺寸全错 -> 必须发现
        with tempfile.TemporaryDirectory() as tmp:
            for w, h in render_png.RESOLUTIONS:
                img = render_png.render(self.board, self.ref, self.manifest,
                                        800, 600)
                img.save(os.path.join(
                    tmp, f"route-preview-dev-f3-01-{w}x{h}.png"),
                    format="PNG")
            r = e0_checks.resolution_invariance(
                "dev-f3-01", self.manifest, self.bbox, tmp)
        self.assertFalse(r["pass"])
        self.assertIn("实际尺寸", r["reason"])

    def test_resolution_route_color_absent_detected(self):
        # 缺一条 route 的颜色投影：从 manifest 去掉某 route 的折线颜色不可行，
        # 直接构造空白 PNG 验证检查器能发现"图例色未出现"
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            for w, h in render_png.RESOLUTIONS:
                Image.new("RGB", (w, h), (255, 255, 255)).save(
                    os.path.join(
                        tmp, f"route-preview-dev-f3-01-{w}x{h}.png"),
                    format="PNG")
            r = e0_checks.resolution_invariance(
                "dev-f3-01", self.manifest, self.bbox, tmp)
        self.assertFalse(r["pass"])
        self.assertIn("图例色", r["reason"])


if __name__ == "__main__":
    unittest.main()
