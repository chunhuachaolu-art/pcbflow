"""C2 包 actions.py 单元测试：planner-response 合同 + fail-closed validator。

负向分支全覆盖（stale hash、未知 net、未知键、越界 waypoint、keepout 命中、
层越权、重复 order、缺 actions、group 错配等）+ 合法响应通过 + 语义不被改写。
校验用合成板（本文件内构造、经 model.validate_board 确认合法），不碰 holdout。
"""

import os
import sys
import tempfile
import unittest

from pcbflow.v4exp import actions, model

BOARD_SCHEMA = "pcbflow.v4exp.board/1"


def make_board():
    """合成三 net 板：n1/n2 default 双层，n3 clock 仅 F.Cu；一块双层 keepout
    k1 与一块仅 B.Cu 的 keepout k2。"""
    return {
        "schema": BOARD_SCHEMA,
        "scenario_id": "dev-f1-01", "split": "development",
        "family": "f1", "seed": 7,
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                  "width_mm": {"default": 0.3, "clock": 0.4},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                     "clock": ["F.Cu"]}},
        "pads": [
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 2.0, "y_mm": 3.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U1-2", "net_id": "n1", "x_mm": 38.0, "y_mm": 3.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-1", "net_id": "n2", "x_mm": 2.0, "y_mm": 27.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-2", "net_id": "n2", "x_mm": 38.0, "y_mm": 27.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-1", "net_id": "n3", "x_mm": 6.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-2", "net_id": "n3", "x_mm": 34.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
        ],
        "nets": [
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U1-2"]},
            {"net_id": "n2", "net_class": "default",
             "endpoints": ["U2-1", "U2-2"]},
            {"net_id": "n3", "net_class": "clock",
             "endpoints": ["U3-1", "U3-2"]},
        ],
        "keepouts": [
            {"keepout_id": "k1", "rect_mm": [16.0, 12.0, 24.0, 18.0],
             "layers": ["F.Cu", "B.Cu"]},
            {"keepout_id": "k2", "rect_mm": [30.0, 20.0, 36.0, 26.0],
             "layers": ["B.Cu"]},
        ],
        "relations": [
            {"relation_id": "r1", "relation_type": "clock_group",
             "members": ["n3"], "parent_id": None},
        ],
        "label": "satisfiable"}


def make_response(board, group="B"):
    """一份完全合法的基线响应（每个测试拿它再做单点变异）。"""
    return {
        "schema": actions.RESPONSE_SCHEMA,
        "scenario_id": board["scenario_id"],
        "board_snapshot_sha256": model.sha256_of(board),
        "group": group,
        "actions": {
            "route_order": ["n1", "n2", "n3"],
            "corridor_preferences": [],
            "layer_preferences": [],
            "protect": [],
            "notes": "baseline",
            "uncertainty": "low",
        },
    }


class TestValidatorNegative(unittest.TestCase):
    """任一全局违例 => 整体 blocked；accepted 为 null。"""

    @classmethod
    def setUpClass(cls):
        cls.board = make_board()

    def test_synth_board_is_valid(self):
        self.assertEqual([], model.validate_board(self.board))

    def v(self, response, group="B"):
        return actions.validate_response(response, self.board, group)

    def assertBlocked(self, validated, fragment=None):
        self.assertTrue(validated["blocked"])
        self.assertIsNone(validated["accepted"])
        self.assertEqual(validated["rejections"], [])
        if fragment is not None:
            self.assertIn(fragment, validated["reason"])

    def test_stale_hash_blocked(self):
        resp = make_response(self.board)
        h = resp["board_snapshot_sha256"]
        resp["board_snapshot_sha256"] = ("0" if h[0] != "0" else "1") + h[1:]
        self.assertBlocked(self.v(resp), "board_snapshot_sha256")

    def test_missing_hash_blocked(self):
        resp = make_response(self.board)
        del resp["board_snapshot_sha256"]
        self.assertBlocked(self.v(resp), "board_snapshot_sha256")

    def test_non_string_hash_blocked(self):
        resp = make_response(self.board)
        resp["board_snapshot_sha256"] = 12345
        self.assertBlocked(self.v(resp), "board_snapshot_sha256")

    def test_wrong_schema_blocked(self):
        resp = make_response(self.board)
        resp["schema"] = "pcbflow.v4exp.planner-response/2"
        self.assertBlocked(self.v(resp), "schema")

    def test_scenario_mismatch_blocked(self):
        resp = make_response(self.board)
        resp["scenario_id"] = "dev-f2-03"
        self.assertBlocked(self.v(resp), "scenario_id")

    def test_group_mismatch_blocked(self):
        # 响应自报 group="C"，但按 B 组校验 => blocked。
        resp = make_response(self.board, group="C")
        self.assertBlocked(self.v(resp), "group")

    def test_group_unknown_value_blocked(self):
        resp = make_response(self.board)
        resp["group"] = "A"
        self.assertBlocked(self.v(resp), "group")

    def test_missing_actions_blocked(self):
        resp = make_response(self.board)
        del resp["actions"]
        self.assertBlocked(self.v(resp), "actions")

    def test_route_order_missing_blocked(self):
        resp = make_response(self.board)
        del resp["actions"]["route_order"]
        self.assertBlocked(self.v(resp), "route_order")

    def test_route_order_empty_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["route_order"] = []
        self.assertBlocked(self.v(resp), "route_order")

    def test_route_order_unknown_net_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["route_order"] = ["n1", "n2", "n9"]
        self.assertBlocked(self.v(resp), "n9")

    def test_route_order_duplicate_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["route_order"] = ["n1", "n1", "n2", "n3"]
        self.assertBlocked(self.v(resp), "重复")

    def test_route_order_incomplete_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["route_order"] = ["n1", "n2"]
        self.assertBlocked(self.v(resp), "完整排列")

    def test_root_unknown_key_blocked(self):
        resp = make_response(self.board)
        resp["write_board"] = {"routes": []}
        self.assertBlocked(self.v(resp), "未知键")

    def test_actions_unknown_key_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["route_geometry"] = [[[0.0, 0.0]]]
        self.assertBlocked(self.v(resp), "未知键")

    def test_corridor_item_unknown_key_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": [], "via_hint": 0.6}]
        self.assertBlocked(self.v(resp), "via_hint")

    def test_layerpref_item_unknown_key_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["layer_preferences"] = [
            {"net_id": "n1", "layers": ["F.Cu"], "width_mm": 0.3}]
        self.assertBlocked(self.v(resp), "width_mm")

    def test_protect_unknown_net_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["protect"] = ["n7"]
        self.assertBlocked(self.v(resp), "n7")

    def test_protect_non_string_list_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["protect"] = [3]
        self.assertBlocked(self.v(resp), "protect")

    def test_notes_non_string_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["notes"] = {"text": "hi"}
        self.assertBlocked(self.v(resp), "notes")

    def test_non_object_response_blocked(self):
        self.assertBlocked(self.v([1, 2, 3]))


class TestValidatorItemRejections(unittest.TestCase):
    """逐项可拒绝：记 rejection、剔除该项，不整体 blocked。"""

    @classmethod
    def setUpClass(cls):
        cls.board = make_board()

    def v(self, response, group="B"):
        return actions.validate_response(response, self.board, group)

    def test_legal_baseline_passes(self):
        out = self.v(make_response(self.board))
        self.assertFalse(out["blocked"])
        self.assertEqual(out["rejections"], [])
        self.assertEqual(out["accepted"]["route_order"], ["n1", "n2", "n3"])
        self.assertEqual(out["accepted"]["corridor_preferences"], [])
        self.assertEqual(out["accepted"]["layer_preferences"], [])
        self.assertEqual(out["accepted"]["protect"], [])

    def test_corridor_unknown_net_rejected_only(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "nX", "waypoints_mm": [[20.0, 15.0]]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["rejections"]), 1)
        self.assertIn("未知 net", out["rejections"][0]["reason"])
        self.assertEqual(out["accepted"]["corridor_preferences"], [])

    def test_waypoint_out_of_bbox_rejected(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": [[45.0, 15.0]]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("bbox", out["rejections"][0]["reason"])

    def test_waypoint_in_keepout_rejected(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": [[20.0, 15.0]]}]  # k1 内
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("keepout", out["rejections"][0]["reason"])

    def test_keepout_judged_per_layer(self):
        # k2 仅 B.Cu：clock net n3 只允许 F.Cu => 不算命中；default net n1
        # 允许 B.Cu => 命中剔除。
        wps = [[33.0, 23.0]]
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n3", "waypoints_mm": wps}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(out["accepted"]["corridor_preferences"],
                         [{"net_id": "n3", "waypoints_mm": wps}])
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": wps}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("keepout", out["rejections"][0]["reason"])
        self.assertEqual(out["accepted"]["corridor_preferences"], [])

    def test_more_than_three_waypoints_rejected(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1",
             "waypoints_mm": [[10.0, 10.0], [12.0, 10.0], [14.0, 10.0],
                              [16.0, 10.0]]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("3", out["rejections"][0]["reason"])

    def test_malformed_waypoints_rejected_not_blocked(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": [["a", "b"]]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("畸形", out["rejections"][0]["reason"])

    def test_duplicate_corridor_net_rejected_second(self):
        resp = make_response(self.board)
        item = {"net_id": "n1", "waypoints_mm": [[10.0, 10.0]]}
        resp["actions"]["corridor_preferences"] = [item, dict(item)]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["rejections"]), 1)
        self.assertEqual(len(out["accepted"]["corridor_preferences"]), 1)

    def test_layer_not_allowed_rejected(self):
        resp = make_response(self.board)
        resp["actions"]["layer_preferences"] = [
            {"net_id": "n3", "layers": ["F.Cu", "B.Cu"]}]  # clock 仅 F.Cu
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertIn("allowed_layers", out["rejections"][0]["reason"])
        self.assertEqual(out["accepted"]["layer_preferences"], [])

    def test_layer_preference_accepted_when_legal(self):
        resp = make_response(self.board)
        resp["actions"]["layer_preferences"] = [
            {"net_id": "n3", "layers": ["F.Cu"]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(out["accepted"]["layer_preferences"],
                         [{"net_id": "n3", "layers": ["F.Cu"]}])

    def test_layerpref_unknown_net_rejected(self):
        resp = make_response(self.board)
        resp["actions"]["layer_preferences"] = [
            {"net_id": "n42", "layers": ["F.Cu"]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["rejections"]), 1)

    def test_bad_uncertainty_rejected_only(self):
        resp = make_response(self.board)
        resp["actions"]["uncertainty"] = "certain"
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["rejections"]), 1)
        self.assertEqual(out["rejections"][0]["item"], "uncertainty")

    def test_mixed_rejections_keep_valid_items(self):
        resp = make_response(self.board)
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": [[45.0, 15.0]]},
            {"net_id": "n2", "waypoints_mm": [[10.0, 22.0]]},
        ]
        resp["actions"]["layer_preferences"] = [
            {"net_id": "n3", "layers": ["B.Cu"]}]
        out = self.v(resp)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["rejections"]), 2)
        self.assertEqual(out["accepted"]["corridor_preferences"],
                         [{"net_id": "n2", "waypoints_mm": [[10.0, 22.0]]}])
        self.assertEqual(out["accepted"]["layer_preferences"], [])


class TestValidatorSemanticsPreserved(unittest.TestCase):
    """validator 决不改写 planner 语义：坐标/顺序原样透传。"""

    @classmethod
    def setUpClass(cls):
        cls.board = make_board()

    def test_coordinates_passed_through_verbatim(self):
        resp = make_response(self.board)
        raw = [[20.0, 4.5], [37.75, 4.5]]
        resp["actions"]["corridor_preferences"] = [
            {"net_id": "n1", "waypoints_mm": raw}]
        out = actions.validate_response(resp, self.board, "B")
        self.assertFalse(out["blocked"])
        got = out["accepted"]["corridor_preferences"][0]["waypoints_mm"]
        self.assertEqual(got, raw)  # 不吸附、不取整、不重排

    def test_order_and_protect_passed_through(self):
        resp = make_response(self.board)
        resp["actions"]["route_order"] = ["n3", "n1", "n2"]
        resp["actions"]["protect"] = ["n3"]
        out = actions.validate_response(resp, self.board, "B")
        self.assertFalse(out["blocked"])
        self.assertEqual(out["accepted"]["route_order"], ["n3", "n1", "n2"])
        self.assertEqual(out["accepted"]["protect"], ["n3"])

    def test_write_validated_round_trip(self):
        tmp = tempfile.mkdtemp(prefix="v4exp-e1-actions-")
        try:
            path = os.path.join(tmp, "validated-actions-x-B.json")
            validated = actions.validate_response(
                make_response(self.board), self.board, "B")
            actions.write_validated(path, validated)
            again = actions.validate_response(
                make_response(self.board), self.board, "B")
            actions.write_validated(path, again)
            with open(path, "rb") as f:
                first = f.read()
            self.assertEqual(
                model.read_json(path), validated)
            # 同输入重写逐字节一致
            actions.write_validated(path, validated)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), first)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
