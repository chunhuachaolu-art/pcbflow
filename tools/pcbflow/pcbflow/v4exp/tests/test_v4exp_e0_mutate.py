"""E0 突变引擎测试：8 种负向突变每种至少 1 例 + 8a 正向对照 + 确定性。

夹具：A 包 dev-f1-01 真实产物副本（tmp 目录）；A 包缺失则整类 Skip。
"""

import os
import tempfile
import unittest

from pcbflow.v4exp import e0_mutate, e0_parse, model
from pcbflow.v4exp.e0_mutate import (ALL_MUTATIONS, NEGATIVE_MUTATIONS,
                                     POSITIVE_MUTATION)
from pcbflow.v4exp.tests.test_v4exp_e0_fixture import (FIXTURE_SID,
                                                       copy_real_fixture,
                                                       read_text)


class TestMutationsOnRealFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        copy_real_fixture(cls.tmp.name, FIXTURE_SID)
        cls.svg = read_text(os.path.join(
            cls.tmp.name, f"route-preview-{FIXTURE_SID}.svg"))
        cls.manifest = model.read_json(os.path.join(
            cls.tmp.name, f"route-manifest-{FIXTURE_SID}.json"))
        cls.board_obj = model.read_json(os.path.join(
            cls.tmp.name, f"board-snapshot-{FIXTURE_SID}.json"))
        cls.original_facts = e0_parse.parse_svg(cls.svg)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _evaluate(self, name):
        mutated = e0_mutate.apply_mutation(name, self.svg, self.manifest)
        if name == POSITIVE_MUTATION:
            return e0_mutate.evaluate_mutation(
                mutated, self.manifest, self.board_obj,
                original_facts=self.original_facts, original_svg=self.svg)
        return e0_mutate.evaluate_mutation(
            mutated, self.manifest, self.board_obj)

    def test_base_fixture_parses_clean(self):
        facts, reason = e0_parse.try_parse_svg(self.svg)
        self.assertIsNone(reason)
        self.assertTrue(facts["routes"])

    def test_all_mutations_covered(self):
        self.assertEqual(len(ALL_MUTATIONS), 9)
        self.assertEqual(len(NEGATIVE_MUTATIONS), 8)

    def test_mutation_deterministic(self):
        for name in ALL_MUTATIONS:
            m1 = e0_mutate.apply_mutation(name, self.svg, self.manifest)
            m2 = e0_mutate.apply_mutation(name, self.svg, self.manifest)
            self.assertEqual(m1, m2, f"{name} 两次突变不一致")
            self.assertIsInstance(m1, str)

    def test_mutations_actually_change_bytes(self):
        for name in ALL_MUTATIONS:
            mutated = e0_mutate.apply_mutation(name, self.svg, self.manifest)
            self.assertNotEqual(mutated, self.svg,
                                f"{name} 未改变 SVG 字节")

    def test_01_net_id_unknown_blocked(self):
        verdict = self._evaluate("net_id_unknown")
        self.assertTrue(verdict["blocked"], verdict)

    def test_02_layer_mismatch_blocked(self):
        verdict = self._evaluate("layer_mismatch")
        self.assertTrue(verdict["blocked"], verdict)

    def test_03_width_mismatch_blocked(self):
        verdict = self._evaluate("width_mismatch")
        self.assertTrue(verdict["blocked"], verdict)

    def test_04_path_coord_shift_blocked(self):
        verdict = self._evaluate("path_coord_shift")
        self.assertTrue(verdict["blocked"], verdict)

    def test_05_duplicate_route_id_blocked(self):
        verdict = self._evaluate("duplicate_route_id")
        self.assertTrue(verdict["blocked"], verdict)

    def test_06_route_deleted_blocked(self):
        verdict = self._evaluate("route_deleted")
        self.assertTrue(verdict["blocked"], verdict)

    def test_07_manifest_hash_zeroed_blocked(self):
        verdict = self._evaluate("manifest_hash_zeroed")
        self.assertTrue(verdict["blocked"], verdict)

    def test_08a_color_only_positive_control_passes(self):
        mutated = e0_mutate.apply_mutation(POSITIVE_MUTATION, self.svg,
                                           self.manifest)
        facts2, reason = e0_parse.try_parse_svg(mutated)
        self.assertIsNone(reason)
        self.assertEqual(facts2, self.original_facts,
                         "8a 正向对照 facts 必须与原版逐字段相等")
        verdict = e0_mutate.evaluate_mutation(
            mutated, self.manifest, self.board_obj,
            original_facts=self.original_facts, original_svg=self.svg)
        self.assertFalse(verdict["blocked"], verdict)

    def test_08a_colors_actually_changed_but_data_intact(self):
        mutated = e0_mutate.apply_mutation(POSITIVE_MUTATION, self.svg,
                                           self.manifest)
        self.assertNotEqual(mutated, self.svg)
        for data_attr in ("data-route-id=", "data-net-id=",
                          "data-width-mm=", "data-line-type="):
            self.assertEqual(mutated.count(data_attr),
                             self.svg.count(data_attr),
                             f"8a 不得触碰 {data_attr}")

    def test_08b_line_type_unknown_blocked(self):
        verdict = self._evaluate("line_type_unknown")
        self.assertTrue(verdict["blocked"], verdict)

    def test_blocked_detail_reports_parse_or_check(self):
        for name in NEGATIVE_MUTATIONS:
            verdict = self._evaluate(name)
            self.assertTrue(verdict["blocked"], name)
            self.assertTrue(verdict["detail"], name)


if __name__ == "__main__":
    unittest.main()
