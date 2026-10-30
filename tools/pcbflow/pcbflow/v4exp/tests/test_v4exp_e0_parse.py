"""E0 严格 SVG 解析器测试：正例 + 负例（fail-closed 全覆盖）。"""

import json
import re
import unittest

from pcbflow.v4exp import e0_parse
from pcbflow.v4exp.e0_parse import E0ParseError, parse_svg, try_parse_svg
from pcbflow.v4exp.tests.test_v4exp_e0_fixture import build_memory_fixture


class TestParsePositive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.ref, cls.manifest, cls.svg = build_memory_fixture()

    def test_valid_svg_parses(self):
        facts = parse_svg(self.svg)
        self.assertEqual(facts["schema"], "v4-svg-route-1")
        self.assertEqual(facts["coordinate_system"], "pcbflow-internal-mm")
        self.assertEqual(facts["y_axis"], "down-positive")
        self.assertEqual(facts["legend_version"], "v4exp-legend-1")
        self.assertEqual(facts["board_snapshot_sha256"],
                         self.manifest["board_snapshot_sha256"])
        self.assertEqual(facts["route_manifest_sha256"],
                         self.manifest["manifest_payload_sha256"])

    def test_route_identity_and_fields(self):
        facts = parse_svg(self.svg)
        man_routes = {r["route_id"]: r for r in self.manifest["routes"]}
        self.assertEqual({r["route_id"] for r in facts["routes"]},
                         set(man_routes))
        for fr in facts["routes"]:
            mr = man_routes[fr["route_id"]]
            self.assertEqual(fr["net_id"], mr["net_id"])
            self.assertEqual(fr["line_type"], mr["line_type"])
            self.assertEqual(fr["layer"], mr["layer"])
            self.assertEqual(fr["width_mm"], mr["width_mm"])
            self.assertEqual(fr["relation_ids"], mr["relation_ids"])
            self.assertEqual(fr["constraint_refs"], mr["constraint_refs"])
            self.assertEqual(fr["endpoint_ids"], mr["endpoint_ids"])
            self.assertEqual(fr["svg_id"], mr["svg_id"])

    def test_via_fields(self):
        facts = parse_svg(self.svg)
        man_vias = {v["via_id"]: v for v in self.manifest["vias"]}
        self.assertEqual({v["via_id"] for v in facts["vias"]}, set(man_vias))
        for fv in facts["vias"]:
            mv = man_vias[fv["via_id"]]
            self.assertEqual(fv["parent_id"], mv["parent_id"])
            self.assertEqual(fv["drill_mm"], mv["drill_mm"])
            self.assertEqual(fv["annular_ring_mm"], mv["annular_ring_mm"])

    def test_relations_pads_keepouts(self):
        facts = parse_svg(self.svg)
        self.assertEqual(
            {r["relation_id"] for r in facts["relations"]},
            {r["relation_id"] for r in self.manifest["relations"]})
        self.assertEqual(
            {p["pad_id"] for p in facts["pads"]},
            {p.pad_id for p in self.board.pads})
        self.assertEqual(
            {k["keepout_id"] for k in facts["keepouts"]},
            {k.keepout_id for k in self.board.keepouts})
        self.assertEqual(len(facts["board_edge"]), 1)

    def test_json_serializable_and_deterministic(self):
        f1 = parse_svg(self.svg)
        f2 = parse_svg(self.svg)
        self.assertEqual(json.dumps(f1), json.dumps(f2))
        self.assertEqual(f1, f2)

    def test_try_parse_ok_shape(self):
        facts, reason = try_parse_svg(self.svg)
        self.assertIsNone(reason)
        self.assertIsNotNone(facts)


class _NegativeMixin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svg = build_memory_fixture()[3]

    def _reject(self, mutate, frag):
        svg = mutate(self.svg)
        facts, reason = try_parse_svg(svg)
        self.assertIsNone(facts, "期望解析失败")
        self.assertIn(frag, reason, f"reason 应含 {frag!r}，实际 {reason!r}")


class TestParseNegativeRoot(_NegativeMixin, unittest.TestCase):
    def test_wrong_schema(self):
        self._reject(
            lambda s: s.replace('data-pcbflow-schema="v4-svg-route-1"',
                                'data-pcbflow-schema="v4-svg-route-2"'),
            "data-pcbflow-schema")

    def test_wrong_coordinate_system(self):
        self._reject(
            lambda s: s.replace('data-coordinate-system="pcbflow-internal-mm"',
                                'data-coordinate-system="kicad-mm"'),
            "data-coordinate-system")

    def test_wrong_y_axis(self):
        self._reject(
            lambda s: s.replace('data-y-axis="down-positive"',
                                'data-y-axis="up-positive"'),
            "data-y-axis")

    def test_wrong_preserve_aspect_ratio(self):
        self._reject(
            lambda s: s.replace('preserveAspectRatio="xMidYMid meet"',
                                'preserveAspectRatio="xMinYMin slice"'),
            "preserveAspectRatio")

    def test_bad_board_sha(self):
        def mutate(s):
            key = 'data-board-snapshot-sha256="'
            i = s.find(key) + len(key)
            return s[:i] + "XYZ" + s[i + 64:]
        self._reject(mutate, "64 位小写 hex")

    def test_manifest_sha_zeroed_still_hex_but_checked_by_hash(self):
        # 64 个 '0' 是合法 hex 形状：解析器放行，hash_binding 负责拦截
        svg = self.svg
        i = svg.find('data-route-manifest-sha256="') + len(
            'data-route-manifest-sha256="')
        svg = svg[:i] + "0" * 64 + svg[i + 64:]
        facts, reason = try_parse_svg(svg)
        self.assertIsNone(reason)

    def test_bad_viewbox_tokens(self):
        self._reject(
            lambda s: s.replace('viewBox="0 0 44.000000 34.000000"',
                                'viewBox="0 0 44.000000"'), "viewBox")

    def test_nonzero_viewbox_origin(self):
        self._reject(
            lambda s: s.replace('viewBox="0 0 44.000000 34.000000"',
                                'viewBox="1 0 44.000000 34.000000"'),
            "viewBox")


class TestParseNegativeObjects(_NegativeMixin, unittest.TestCase):
    def _route_block(self, svg):
        start = svg.find('<g id="route-')
        end = svg.find("</g>", start) + 4
        return start, end

    def test_unknown_object_kind(self):
        self._reject(
            lambda s: s.replace('data-object-kind="route_segment"',
                                'data-object-kind="mystery"', 1),
            "未知 data-object-kind")

    def test_route_missing_required_attr(self):
        def mutate(s):
            a, b = self._route_block(s)
            block = s[a:b].replace(' data-state="baseline"', "", 1)
            return s[:a] + block + s[b:]
        self._reject(mutate, "缺必填属性 data-state")

    def test_route_unknown_line_type(self):
        self._reject(
            lambda s: s.replace('data-line-type="bus_member"',
                                'data-line-type="mystery"', 1),
            "未知 data-line-type")

    def test_duplicate_element_id(self):
        def mutate(s):
            a, b = self._route_block(s)
            return s[:b] + "\n  " + s[a:b] + s[b:]
        self._reject(mutate, "id 重复")

    def test_path_d_unknown_command(self):
        self._reject(
            lambda s: s.replace("M ", "C ", 1), "首命令必须是 M")

    def test_path_d_relative_command(self):
        self._reject(
            lambda s: s.replace(" L ", " l ", 1), "必须是 L")

    def test_path_d_five_decimals(self):
        def mutate(s):
            i = s.find('d="M ')
            j = s.find(" ", i + 5)
            return s[:i + 5] + s[i + 5:j - 1] + s[j:]
        self._reject(mutate, "6 位定点小数")

    def test_path_d_single_point(self):
        def mutate(s):
            m = re.search(r'd="M (-?\d+\.\d{6}) (-?\d+\.\d{6})'
                          r'( L -?\d+\.\d{6} -?\d+\.\d{6})+"', s)
            self.assertIsNotNone(m, "夹具应含多点 path d")
            return s[:m.start()] + \
                f'd="M {m.group(1)} {m.group(2)}"' + s[m.end():]
        self._reject(mutate, "至少 2 个点")

    def test_width_two_decimals(self):
        self._reject(
            lambda s: s.replace('data-width-mm="0.400"',
                                'data-width-mm="0.4"', 1),
            "3 位定点小数")

    def test_bad_constraint_ref_shape(self):
        self._reject(
            lambda s: s.replace("C-width-040", "WIDTH-040", 1),
            "形状不符")

    def test_relation_unknown_type(self):
        self._reject(
            lambda s: s.replace('data-relation-type="clock_group"',
                                'data-relation-type="mystery"', 1),
            "未知 data-relation-type")

    def test_relation_missing_member_attr(self):
        def mutate(s):
            a = s.find('data-object-kind="route_relation"')
            a = s.rfind("<g", 0, a + 30)
            b = s.find("</g>", a) + 4
            block = s[a:b].replace(' data-member-ids="n1 n2"', "", 1)
            return s[:a] + block + s[b:]
        self._reject(mutate, "缺必填属性 data-member-ids")

    def test_legend_missing(self):
        def mutate(s):
            a = s.find('<g id="legend"')
            b = s.find("</svg>")
            self.assertNotEqual(a, -1)
            return s[:a] + s[b:]
        self._reject(mutate, "图例组")

    def test_unknown_tag(self):
        self._reject(
            lambda s: s.replace("</style>", "</style>\n  <foo/>", 1),
            "白名单外标签")

    def test_unknown_attribute(self):
        self._reject(
            lambda s: s.replace('<rect id="board-edge"',
                                '<rect data-secret="1" id="board-edge"', 1),
            "白名单外属性")

    def test_not_xml(self):
        self._reject(lambda s: s[10:], "XML 语法错误")


if __name__ == "__main__":
    unittest.main()
