"""A 包合同测试：SVG/manifest 重解析抽查 + byte-exact 双发。"""

import io
import unittest
import xml.etree.ElementTree as ET

from pcbflow.v4exp import model, ref_route, render_png, svg_pkg
from pcbflow.v4exp.tests.test_v4exp_model import valid_board_obj

SVG_NS = "http://www.w3.org/2000/svg"


def make_board_and_routes():
    board = model.board_from_obj(valid_board_obj())
    ref = ref_route.route_board(board)
    return board, ref


class TestSvgReparse(unittest.TestCase):
    def setUp(self):
        self.board, self.ref = make_board_and_routes()
        self.manifest, self.svg = svg_pkg.build(self.board, self.ref)
        self.root = ET.fromstring(self.svg)

    def test_root_data_attributes(self):
        self.assertEqual(self.root.tag, f"{{{SVG_NS}}}svg")
        # 抽查 3 个 data-* 属性（合同要求 >= 3）
        self.assertEqual(self.root.get("data-pcbflow-schema"),
                         "v4-svg-route-1")
        self.assertEqual(self.root.get("data-coordinate-system"),
                         "pcbflow-internal-mm")
        self.assertEqual(self.root.get("data-y-axis"), "down-positive")

    def test_viewbox_meets_margin_contract(self):
        x0, y0, x1, y1 = self.board.bbox_mm
        w = (x1 - x0) + 2 * model.MARGIN_MM
        h = (y1 - y0) + 2 * model.MARGIN_MM
        self.assertEqual(self.root.get("viewBox"),
                         f"0 0 {model.fmt6(w)} {model.fmt6(h)}")
        self.assertEqual(self.root.get("preserveAspectRatio"),
                         "xMidYMid meet")

    def test_route_group_attributes(self):
        routes = self.root.findall(
            f"{{{SVG_NS}}}g[@data-object-kind='route_segment']")
        self.assertTrue(routes)
        g = routes[0]
        self.assertEqual(g.get("data-net-id"), "n1")
        self.assertIn(g.get("data-layer"), ("F.Cu", "B.Cu"))
        self.assertEqual(g.get("data-state"), "baseline")
        self.assertEqual(g.get("data-source"), "generator")
        self.assertIn("C-clearance-030", g.get("data-constraint-refs"))
        path = g.find(f"{{{SVG_NS}}}path")
        self.assertTrue(path.get("d", "").startswith("M "))
        self.assertIn("layer-FCu", path.get("class"))

    def test_sha256_roundtrip(self):
        self.assertEqual(
            self.manifest["manifest_payload_sha256"],
            model.sha256_of(self.manifest))
        self.assertEqual(
            self.manifest["board_snapshot_sha256"],
            model.sha256_of(self.board.to_obj()))
        self.assertEqual(
            self.root.get("data-route-manifest-sha256"),
            self.manifest["manifest_payload_sha256"])
        self.assertEqual(
            self.root.get("data-board-snapshot-sha256"),
            self.manifest["board_snapshot_sha256"])

    def test_manifest_structure(self):
        self.assertEqual(self.manifest["schema_version"],
                         "v4-route-manifest-1")
        self.assertEqual(self.manifest["svg_coordinate_system"],
                         "pcbflow-internal-mm")
        self.assertEqual(self.manifest["legend_version"], "v4exp-legend-1")
        self.assertEqual(self.manifest["rules"],
                         self.board.rules.to_obj())
        for r in self.manifest["routes"]:
            self.assertEqual(r["svg_id"], f"route-{r['route_id']}")
            self.assertEqual(len(r["endpoint_ids"]), 2)
        # manifest 的 routes/vias 与 ref-routes 同构
        self.assertEqual(self.manifest["routes"], self.ref["routes"])
        self.assertEqual(self.manifest["vias"], self.ref["vias"])

    def test_via_parent_chain(self):
        by_id = {r["route_id"]: r for r in self.manifest["routes"]}
        for v in self.manifest["vias"]:
            self.assertIn(v["parent_id"], by_id)
            parent = by_id[v["parent_id"]]
            self.assertEqual(parent["net_id"], v["net_id"])

    def test_relation_groups_present(self):
        rels = self.root.findall(
            f"{{{SVG_NS}}}g[@data-object-kind='route_relation']")
        self.assertEqual(len(rels), 2)
        member_ids = {r.get("data-relation-id"): r.get("data-member-ids")
                      for r in rels}
        self.assertEqual(member_ids["BUS-1"], "n1 n2")
        self.assertEqual(rels[0].get("data-relation-type"), "bus")


class TestByteExact(unittest.TestCase):
    def setUp(self):
        self.board, self.ref = make_board_and_routes()

    def test_svg_manifest_double_build_identical(self):
        m1, s1 = svg_pkg.build(self.board, self.ref)
        m2, s2 = svg_pkg.build(self.board, self.ref)
        self.assertEqual(s1, s2)
        self.assertEqual(model.canonical_bytes(m1),
                         model.canonical_bytes(m2))

    def test_ref_route_double_run_identical(self):
        r1 = ref_route.route_board(self.board)
        r2 = ref_route.route_board(self.board)
        self.assertEqual(model.canonical_bytes(r1),
                         model.canonical_bytes(r2))

    def test_png_double_render_identical_bytes(self):
        m, _ = svg_pkg.build(self.board, self.ref)
        for w, h in render_png.RESOLUTIONS:
            img1 = render_png.render(self.board, self.ref, m, w, h)
            img2 = render_png.render(self.board, self.ref, m, w, h)
            b1 = io.BytesIO()
            b2 = io.BytesIO()
            img1.save(b1, format="PNG")
            img2.save(b2, format="PNG")
            self.assertEqual(b1.getvalue(), b2.getvalue(),
                             f"{w}x{h} 两张 PNG 不逐字节一致")

    def test_png_resolution_and_margin(self):
        from PIL import Image
        m, _ = svg_pkg.build(self.board, self.ref)
        w, h = render_png.RESOLUTIONS[0]
        img = render_png.render(self.board, self.ref, m, w, h)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (w, h))


if __name__ == "__main__":
    unittest.main()
