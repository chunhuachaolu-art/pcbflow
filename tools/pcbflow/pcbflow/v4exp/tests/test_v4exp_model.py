"""A 包合同测试：板模型校验正/负例 + canonical hash 稳定性。"""

import hashlib
import unittest

from pcbflow.v4exp import model


def valid_board_obj() -> dict:
    return {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": "dev-f3-01",
        "split": "development",
        "family": "f3",
        "seed": 12345,
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                  "width_mm": {"default": 0.3, "clock": 0.4},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                     "clock": ["F.Cu"]}},
        "pads": [
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 5.0, "y_mm": 6.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-1", "net_id": "n1", "x_mm": 35.0, "y_mm": 6.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U1-2", "net_id": "n2", "x_mm": 5.0, "y_mm": 8.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-2", "net_id": "n2", "x_mm": 35.0, "y_mm": 8.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-1", "net_id": "n3", "x_mm": 5.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "J2-1", "net_id": "n3", "x_mm": 35.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"}],
        "nets": [
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U2-1"]},
            {"net_id": "n2", "net_class": "default",
             "endpoints": ["U1-2", "U2-2"]},
            {"net_id": "n3", "net_class": "clock",
             "endpoints": ["U3-1", "J2-1"]}],
        "keepouts": [{"keepout_id": "k1",
                      "rect_mm": [10.0, 10.0, 20.0, 20.0],
                      "layers": ["F.Cu"]}],
        "relations": [
            {"relation_id": "BUS-1", "relation_type": "bus",
             "members": ["n1", "n2"], "parent_id": None},
            {"relation_id": "CLK-1", "relation_type": "clock_group",
             "members": ["n3"], "parent_id": None}],
        "label": "satisfiable"}


class TestBoardValidation(unittest.TestCase):
    def test_valid_board_passes(self):
        self.assertEqual(model.validate_board(valid_board_obj()), [])
        board = model.board_from_obj(valid_board_obj())  # 不抛
        self.assertEqual(board.scenario_id, "dev-f3-01")

    def _assert_reject(self, mutate, frag):
        obj = valid_board_obj()
        mutate(obj)
        errs = model.validate_board(obj)
        self.assertTrue(any(frag in e for e in errs),
                        f"期望错误含 {frag!r}，实际 {errs}")

    def test_wrong_schema(self):
        self._assert_reject(
            lambda o: o.update(schema="pcbflow.v4exp.board/2"), "schema")

    def test_bad_pad_id(self):
        self._assert_reject(
            lambda o: o["pads"][0].update(pad_id="U1"), "pad_id")

    def test_bad_net_id(self):
        self._assert_reject(
            lambda o: o["nets"][0].update(net_id="n10"), "net_id")

    def test_one_endpoint_net(self):
        self._assert_reject(
            lambda o: o["nets"][0].update(endpoints=["U1-1"]), "endpoints")

    def test_endpoint_without_pad(self):
        self._assert_reject(
            lambda o: o["nets"][0].update(endpoints=["U1-1", "U9-9"]),
            "无对应 pad")

    def test_endpoint_net_mismatch(self):
        self._assert_reject(
            lambda o: o["nets"][0].update(endpoints=["U1-1", "U1-2"]),
            "不一致")

    def test_clock_net_without_relation(self):
        def mutate(o):
            o["relations"] = [o["relations"][0]]
        self._assert_reject(mutate, "clock 网络")

    def test_pad_center_not_half_multiple(self):
        self._assert_reject(
            lambda o: o["pads"][0].update(x_mm=5.25), "0.5 的倍数")

    def test_mm_not_005_multiple(self):
        self._assert_reject(
            lambda o: o["rules"].update(clearance_mm=0.33), "clearance")

    def test_keepout_boundary_not_half_multiple(self):
        self._assert_reject(
            lambda o: o["keepouts"][0].update(rect_mm=[10.25, 10.0, 20.0,
                                                       20.0]), "0.5 的倍数")

    def test_keepout_out_of_bbox(self):
        self._assert_reject(
            lambda o: o["keepouts"][0].update(rect_mm=[10.0, 10.0, 42.0,
                                                       20.0]), "bbox")

    def test_bad_relation_type(self):
        self._assert_reject(
            lambda o: o["relations"][0].update(relation_type="diff"),
            "relation_type")

    def test_bad_net_class(self):
        self._assert_reject(
            lambda o: o["nets"][0].update(net_class="fast"), "net_class")

    def test_bad_label(self):
        self._assert_reject(
            lambda o: o.update(label="maybe"), "label")

    def test_bad_split(self):
        self._assert_reject(
            lambda o: o.update(split="train"), "split")

    def test_pad_layer_not_in_board_layers(self):
        self._assert_reject(
            lambda o: o["pads"][0].update(layer="F.Cu2"), "板层")

    def test_via_hole_ge_pad(self):
        self._assert_reject(
            lambda o: o["rules"].update(via={"pad_mm": 0.3, "hole_mm": 0.3}),
            "hole_mm")


class TestCanonicalHash(unittest.TestCase):
    def test_canonical_form_exact_bytes(self):
        self.assertEqual(model.canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')
        self.assertEqual(
            model.sha256_of({"a": 1}),
            hashlib.sha256(b'{"a":1}').hexdigest())

    def test_key_order_independence(self):
        o1 = {"x": {"b": 1, "a": 2}, "y": [1, 2]}
        o2 = {"y": [1, 2], "x": {"a": 2, "b": 1}}
        self.assertEqual(model.sha256_of(o1), model.sha256_of(o2))

    def test_strips_sha256_keys_recursively(self):
        o1 = {"a": 1, "manifest_payload_sha256": "deadbeef"}
        o2 = {"a": 1}
        self.assertEqual(model.sha256_of(o1), model.sha256_of(o2))
        nested = {"a": 1, "sub": {"board_snapshot_sha256": "x"}}
        self.assertEqual(model.sha256_of(nested), model.sha256_of(
            {"a": 1, "sub": {}}))

    def test_unicode_escaped_not_used(self):
        self.assertEqual(model.canonical_json({"k": "总线"}),
                         '{"k":"总线"}')

    def test_constraint_ref_format(self):
        self.assertEqual(model.constraint_ref("width", 0.3), "C-width-030")
        self.assertEqual(model.constraint_ref("width", 0.4), "C-width-040")
        self.assertEqual(model.constraint_ref("clearance", 0.3),
                         "C-clearance-030")

    def test_mm_quantization(self):
        self.assertEqual(model.mm((0.6 - 0.3) / 2), 0.15)
        self.assertEqual(model.mm(14.5), 14.5)


class ScenarioIdCharsetTest(unittest.TestCase):
    """SEC-B-04 收口守卫（align-r1，2026-09-25）：scenario_id 拼入
    route-manifest-%s.json / route-preview-%s.svg 文件名，须拒路径分隔符、
    ../ 穿越与空白；合法域=[A-Za-z0-9._-] 且禁连续两点。"""

    def _errs_with_sid(self, sid):
        obj = valid_board_obj()
        obj["scenario_id"] = sid
        return model.validate_board(obj)

    def test_legal_ids_pass(self):
        for sid in ("dev-f1-01", "fix-five-nets", "a", "F5.x_9-", "unsat-f5-03"):
            self.assertNotIn(
                "scenario_id", ";".join(self._errs_with_sid(sid)), sid)

    def test_traversal_and_separators_rejected(self):
        for sid in ("../evil", "..", "a..b", "a/b", "a\b", "a b", "a	b",
                    "../" + "x" * 40, "x/y/../../z", "café", "x;y", ""):
            errs = ";".join(self._errs_with_sid(sid))
            self.assertIn("scenario_id", errs, sid)


if __name__ == "__main__":
    unittest.main()
