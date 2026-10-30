# -*- coding: utf-8 -*-
"""E5 plannerseat harness 测试：token 计数与硬停（G5.3，超限=blocked 不出数
实测）、排序响应结构校验、评估腿确定性、patch wrapper 校验、拒绝原因回流。"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow.v4_1 import plannerseat  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")

ORDER_SIDS = ["cal-f4-07", "cal-f5-07"]  # 1 sat gap 场景 + 1 unsat 证书场景


def _board(sid):
    return plannerseat.read_board(
        os.path.join(ROOT, "out", "v4-experiment"), sid)


class TestTokenLedgerG53(unittest.TestCase):
    """G5.3 预算纪律：计数口径 + 双层硬停（session/suite）实测。"""

    def test_estimate_tokens_ceil(self):
        self.assertEqual(plannerseat.estimate_tokens(800), 200)
        self.assertEqual(plannerseat.estimate_tokens(801), 201)
        self.assertEqual(plannerseat.estimate_tokens(0), 0)

    def _tmp_files(self, specs):
        d = tempfile.mkdtemp()
        paths = []
        for name, text in specs:
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            paths.append(p)
        return d, paths

    def test_session_ceiling_blocked(self):
        # 注入超限 session：800_001 chars → 200_001 tokens > 200k ceiling
        d, paths = self._tmp_files([("big.json", "x" * 800001)])
        ledger = plannerseat.build_ledger(
            [{"session_id": "ord-x-M", "scenario_id": "x", "arm": "M",
              "files": paths}], None)
        e = ledger["sessions"][0]
        self.assertTrue(e["blocked"])
        self.assertEqual(e["blocked_reason"], "session_ceiling_exceeded")
        self.assertEqual(e["est_tokens"], 200001)

    def test_session_at_ceiling_not_blocked(self):
        d, paths = self._tmp_files([("ok.json", "x" * 800000)])
        ledger = plannerseat.build_ledger(
            [{"session_id": "ord-x-M", "scenario_id": "x", "arm": "M",
              "files": paths}], None)
        self.assertFalse(ledger["sessions"][0]["blocked"])
        self.assertEqual(ledger["sessions"][0]["est_tokens"], 200000)

    def test_suite_ceiling_blocks_remaining(self):
        # 4 个 200k sessions = 800k < 7M 不触发；构造 36×200k=7.2M > 7M：
        # 第 36 个 session 起必须 blocked（suite_ceiling_exceeded）
        d, _ = self._tmp_files([("p.json", "x" * 800000)])
        sessions = [{"session_id": "s%02d" % i, "scenario_id": "x%02d" % i,
                     "arm": "M", "files": [os.path.join(d, "p.json")]}
                    for i in range(36)]
        ledger = plannerseat.build_ledger(sessions, None)
        blocked = [e for e in ledger["sessions"] if e["blocked"]]
        self.assertTrue(blocked)
        self.assertTrue(all(e["blocked_reason"] == "suite_ceiling_exceeded"
                            for e in blocked))
        # 未超限的前置 session 不 blocked
        first_blocked = next(i for i, e in enumerate(ledger["sessions"])
                             if e["blocked"])
        self.assertEqual(first_blocked, 35)  # 35×200k=7.0M 未超；第 36 个=7.2M 超
        self.assertFalse(ledger["sessions"][34]["blocked"])

    def test_scenario_blocked_lookup(self):
        d, paths = self._tmp_files([("big.json", "x" * 800001)])
        ledger = plannerseat.build_ledger(
            [{"session_id": "ord-cal-f4-07-M", "scenario_id": "cal-f4-07",
              "arm": "M", "files": paths}], None)
        self.assertEqual(len(plannerseat.scenario_blocked(ledger, "cal-f4-07")),
                         1)
        self.assertEqual(len(plannerseat.scenario_blocked(ledger, "other")), 0)


class TestOrderingResponseValidation(unittest.TestCase):

    def test_valid_permutation(self):
        board = _board("cal-f4-07")
        nets = sorted(n["net_id"] for n in board["nets"])
        resp = {"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                "scenario_id": "cal-f4-07", "route_order": nets,
                "notes": "ok", "uncertainty": "low"}
        vr = plannerseat.validate_ordering_response(resp, board)
        self.assertFalse(vr["blocked"])
        self.assertEqual(vr["route_order"], nets)

    def test_missing_net_blocked(self):
        board = _board("cal-f4-07")
        resp = {"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                "scenario_id": "cal-f4-07",
                "route_order": ["n1", "n2", "n3"],
                "notes": "", "uncertainty": "low"}
        self.assertTrue(
            plannerseat.validate_ordering_response(resp, board)["blocked"])

    def test_duplicate_blocked(self):
        board = _board("cal-f4-07")
        resp = {"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                "scenario_id": "cal-f4-07",
                "route_order": ["n1", "n1", "n3", "n2"],
                "notes": "", "uncertainty": "low"}
        self.assertTrue(
            plannerseat.validate_ordering_response(resp, board)["blocked"])

    def test_wrong_schema_and_sid_blocked(self):
        board = _board("cal-f4-07")
        nets = sorted(n["net_id"] for n in board["nets"])
        bad1 = {"schema": "other/1", "scenario_id": "cal-f4-07",
                "route_order": nets, "notes": "", "uncertainty": "low"}
        bad2 = {"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                "scenario_id": "zzz", "route_order": nets,
                "notes": "", "uncertainty": "low"}
        bad3 = {"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                "scenario_id": "cal-f4-07", "route_order": nets,
                "notes": "", "uncertainty": "maybe"}
        for bad in (bad1, bad2, bad3):
            self.assertTrue(
                plannerseat.validate_ordering_response(bad, board)["blocked"])


class TestOrderingEvalLeg(unittest.TestCase):
    """评估腿对冻结锚场景的确定性读数（read-only out/v4-experiment）。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.root = os.path.join(ROOT, "out", "v4-experiment")
        io_dir = os.path.join(cls.tmp, "io")
        os.makedirs(io_dir, exist_ok=True)
        # M 臂响应：cal-f4-07 用稳定序（已知 S=188.0/opt=171.5）；
        # cal-f5-07（unsat 证书）任意合法排列。
        with open(os.path.join(io_dir, "planner-response-cal-f4-07-M.json"),
                  "w", encoding="utf-8", newline="\n") as f:
            json.dump({"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                       "scenario_id": "cal-f4-07",
                       "route_order": ["n1", "n2", "n3", "n4"],
                       "notes": "test stable order", "uncertainty": "low"}, f)
        with open(os.path.join(io_dir, "planner-response-cal-f5-07-M.json"),
                  "w", encoding="utf-8", newline="\n") as f:
            json.dump({"schema": plannerseat.ORDERING_RESPONSE_SCHEMA,
                       "scenario_id": "cal-f5-07",
                       "route_order": ["n1", "n2"],
                       "notes": "test unsat", "uncertainty": "low"}, f)
        # 空台账（无 blocked）
        ledger = {"schema": plannerseat.LEDGER_SCHEMA, "sessions": []}
        with open(os.path.join(cls.tmp, "ledger.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump(ledger, f)
        cls.io_dir = io_dir
        cls.ledger_path = os.path.join(cls.tmp, "ledger.json")

    def test_capture_formula_on_f4_07(self):
        res = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, self.io_dir,
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            self.ledger_path, None)
        row = next(r for r in res["rows"] if r["scenario_id"] == "cal-f4-07")
        self.assertTrue(row["applicable_for_capture"])
        # 冻结件 router 口径 171.5 + 重解复现校验通过
        self.assertEqual(row["optimum"]["objective_router"], 171.5)
        self.assertTrue(row["optimum"]["router_reproduced"])
        # cmp 统一度量空间（DEV-E5-001）：S=188.0（探盘口径一致）
        self.assertEqual(row["arms"]["S"]["objective"], 188.0)
        self.assertEqual(row["gap_S"],
                         round(188.0 - row["optimum"]["objective"], 6))
        opt_cmp = row["optimum"]["objective"]
        self.assertEqual(row["capture"]["S"], 0.0)
        self.assertEqual(row["capture"]["M"], 0.0)  # M=稳定序
        self.assertAlmostEqual(row["arms"]["A1"]["objective"], 187.828,
                               places=3)
        self.assertAlmostEqual(row["capture"]["A1"],
                               1 - (187.828 - opt_cmp) / (188.0 - opt_cmp),
                               places=3)

    def test_unsat_scenario_not_applicable(self):
        res = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, self.io_dir,
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            self.ledger_path, None)
        row = next(r for r in res["rows"] if r["scenario_id"] == "cal-f5-07")
        self.assertTrue(row["unsat_certified"])
        self.assertFalse(row["applicable_for_capture"])
        self.assertNotIn("capture", row)

    def test_blocked_session_produces_no_numbers(self):
        """G5.3 核心行为：token 超限 session → 该场景 M 臂 blocked 不出数。"""
        big = os.path.join(self.tmp, "big.txt")
        with open(big, "w", encoding="utf-8", newline="\n") as f:
            f.write("x" * 800001)
        ledger = plannerseat.build_ledger(
            [{"session_id": "ord-cal-f4-07-M", "scenario_id": "cal-f4-07",
              "arm": "M", "files": [big]}],
            os.path.join(self.tmp, "ledger-blocked.json"))
        res = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, self.io_dir,
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            os.path.join(self.tmp, "ledger-blocked.json"), None)
        row = next(r for r in res["rows"] if r["scenario_id"] == "cal-f4-07")
        self.assertTrue(row["arms"]["M"]["blocked"])
        self.assertIsNone(row["arms"]["M"]["objective"])
        self.assertEqual(row["capture"]["M"], "blocked")  # 不出数
        # S/A1 确定性臂照常出数（blocked 只作用于模型臂）
        self.assertEqual(row["arms"]["S"]["objective"], 188.0)
        self.assertIsNotNone(row["arms"]["A1"]["objective"])

    def test_missing_response_blocked(self):
        res = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, os.path.join(self.tmp, "empty-io"),
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            self.ledger_path, None)
        for r in res["rows"]:
            self.assertTrue(r["arms"]["M"]["blocked"])

    def test_optimum_anchor_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            fake_prereg = os.path.join(td, "prereg-e5.json")
            with open(fake_prereg, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"scenario_sets": {"ordering_seat_g52": {
                    "board_snapshot_sha256": {
                        "out/v4-experiment/board-snapshot-cal-f4-07.json":
                            "0" * 64}}}}, f)
            # 锚不匹配 → fail-closed（baseline 校验在 prereg 之后仍需通过；
            # 此处构造 board hash 失配即触发）
            with self.assertRaises(Exception):
                plannerseat.run_ordering_eval(
                    self.root, ["cal-f4-07"], self.io_dir, fake_prereg,
                    self.ledger_path, None)

    def test_eval_deterministic(self):
        a = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, self.io_dir,
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            self.ledger_path, None)
        b = plannerseat.run_ordering_eval(
            self.root, ORDER_SIDS, self.io_dir,
            os.path.join(ROOT, "out", "v4.1-engineering", "e5",
                         "prereg-e5.json"),
            self.ledger_path, None)
        from pcbflow.v4_1.canonical import dumps_canonical
        self.assertEqual(dumps_canonical(a), dumps_canonical(b))


class TestPatchResponseAndFeedback(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = os.path.join(ROOT, "out", "v4-experiment")
        cls.board = plannerseat.read_board(cls.root, "cal-f4-07")

    def _resp(self, arm="E5-PROJ", rnd=1, patches=None):
        from pcbflow.v4exp import model
        return {"schema": plannerseat.RESPONSE_SCHEMA,
                "scenario_id": "cal-f4-07",
                "board_snapshot_sha256": model.sha256_of(self.board),
                "arm": arm, "round": rnd,
                "patches": patches if patches is not None else [],
                "notes": "", "uncertainty": "low"}

    def test_wrapper_valid(self):
        vr = plannerseat.validate_patch_response(
            self._resp(), self.board, "E5-PROJ", 1)
        self.assertFalse(vr["blocked"])

    def test_wrapper_wrong_arm(self):
        vr = plannerseat.validate_patch_response(
            self._resp(arm="E5-SVG"), self.board, "E5-PROJ", 1)
        self.assertTrue(vr["blocked"])

    def test_wrapper_unknown_keys(self):
        r = self._resp()
        r["extra"] = 1
        self.assertTrue(plannerseat.validate_patch_response(
            r, self.board, "E5-PROJ", 1)["blocked"])

    def test_wrapper_too_many_patches(self):
        r = self._resp(patches=[{}, {}, {}, {}, {}])
        self.assertTrue(plannerseat.validate_patch_response(
            r, self.board, "E5-PROJ", 1)["blocked"])

    def test_reject_reasons_flow_into_feedback(self):
        """拒绝原因结构化回流：stale hash patch 的 reasons 进入反馈文件。"""
        from pcbflow.v4exp import cmp_patch
        from pcbflow.v4exp.grid import GridWorld
        world = GridWorld(self.board)
        run = plannerseat.baseline_run(self.board)
        geom = cmp_patch.geom_from_run(run)
        route = geom["routes"][0]
        bad_patch = {
            "schema_version": cmp_patch.PATCH_SCHEMA,
            "action_type": "replace_subpath",
            "base_candidate_geometry_sha256": "0" * 64,  # stale → 拒绝
            "scenario_id": "cal-f4-07",
            "route_id": route["route_id"], "net_id": route["net_id"],
            "relation_id": None, "parent_id": None,
            "fixed_endpoint_ids": list(route["endpoint_ids"]),
            "reason": "test", "source": "planner",
            "layer": route["layer"], "width_mm": route["width_mm"],
            "polyline_mm": [list(p) for p in route["polyline_mm"]],
        }
        ev = plannerseat.evaluate_patches(world, self.board, [bad_patch], geom)
        self.assertFalse(ev["records"][0]["legal"])
        self.assertTrue(ev["records"][0]["reasons"])
        fb = plannerseat.build_feedback("cal-f4-07", "E5-PROJ", 1, ev)
        self.assertEqual(fb["patch_results"][0]["reasons"],
                         ev["records"][0]["reasons"])
        self.assertIn("updated_base_candidate_geometry_sha256", fb)

    def test_corrected_by_solver_always_false(self):
        from pcbflow.v4exp import cmp_patch
        from pcbflow.v4exp.grid import GridWorld
        world = GridWorld(self.board)
        run = plannerseat.baseline_run(self.board)
        geom = cmp_patch.geom_from_run(run)
        ev = plannerseat.evaluate_patches(world, self.board, [], geom)
        for rec in ev["records"]:
            self.assertFalse(rec["corrected_by_solver"])


if __name__ == "__main__":
    unittest.main()
