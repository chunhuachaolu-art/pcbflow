"""C2 包 run_e1 / prepare_inputs 集成测试（stdlib unittest，临时目录）。

覆盖：A 组用 dev-f1-01 真实板跑通；blocked 响应进 solver-run 为 unknown；
同输入双跑逐字节一致；replay 模式逐文件比对（含篡改检出）；planner 输入
不给 label（答案）；产物无主机绝对路径。禁改 holdout 场景，只用 development。
"""

import json
import os
import shutil
import tempfile
import unittest

from pcbflow.v4exp import actions, model, prepare_inputs, run_e1

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO_ROOT, "out", "v4-experiment")
SID = "dev-f1-01"

ABS_MARKERS = (":\\", "C:/", "c:/", "/home/", "/Users/")


def legal_response(board, group="B"):
    """针对 dev-f1-01 的合法响应：稳定序 + n1 绕行 corridor（偏离 A 组
    直连基线），保证 B 组几何一定区别于 A 组。"""
    return {
        "schema": actions.RESPONSE_SCHEMA,
        "scenario_id": board["scenario_id"],
        "board_snapshot_sha256": model.sha256_of(board),
        "group": group,
        "actions": {
            "route_order": ["n1", "n2", "n3"],
            "corridor_preferences": [
                {"net_id": "n1", "waypoints_mm": [[20.0, 8.0]]}],
            "layer_preferences": [
                {"net_id": "n2", "layers": ["F.Cu"]}],
            "protect": [],
            "notes": "unit-test",
            "uncertainty": "low",
        },
    }


def write_validated(actions_dir, sid, group, validated):
    os.makedirs(actions_dir, exist_ok=True)
    path = os.path.join(actions_dir,
                        "validated-actions-%s-%s.json" % (sid, group))
    actions.write_validated(path, validated)
    return path


class TestRunner(unittest.TestCase):
    """runner 语义：A 组基线、blocked/missing -> UNKNOWN、router 拒绝可见。"""

    @classmethod
    def setUpClass(cls):
        cls.board = model.read_json(
            os.path.join(SRC, "board-snapshot-%s.json" % SID))
        cls._tmp = tempfile.mkdtemp(prefix="v4exp-e1-runner-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _out(self, name):
        path = os.path.join(self._tmp, name)
        os.makedirs(path, exist_ok=True)
        return path

    def test_a_group_real_board_runs_sat(self):
        out_dir = self._out("a-run")
        summary = run_e1.run([SID], ["A"], SRC, self._out("a-actions"),
                             out_dir)
        run_file = os.path.join(out_dir, "solver-run-%s-A.json" % SID)
        run_dict = model.read_json(run_file)
        self.assertEqual(run_dict["status"], "sat")
        self.assertEqual(run_dict["group"], "A")
        self.assertTrue(run_dict["metrics"]["all_connected"])
        self.assertEqual(run_dict["metrics"]["violations"],
                         {"clearance": 0, "width": 0, "layer": 0,
                          "keepout": 0})
        gs = summary["groups_summary"]["A"]
        self.assertEqual(gs["sat_rate"], 1.0)
        self.assertEqual(gs["unknown_count"], 0)
        self.assertEqual(gs["blocked_count"], 0)

    def test_blocked_response_becomes_unknown(self):
        actions_dir = self._out("blk-actions")
        write_validated(actions_dir, SID, "B", {
            "schema": actions.VALIDATED_SCHEMA, "scenario_id": SID,
            "group": "B", "blocked": True,
            "reason": "board_snapshot_sha256 与重算值不一致（stale/错误 hash）",
            "rejections": [], "accepted": None})
        out_dir = self._out("blk-run")
        summary = run_e1.run([SID], ["B"], SRC, actions_dir, out_dir)
        run_dict = model.read_json(
            os.path.join(out_dir, "solver-run-%s-B.json" % SID))
        self.assertEqual(run_dict["status"], "unknown")
        self.assertEqual(run_dict["blocked_from"], "validator")
        self.assertIn("stale", run_dict["blocked_reason"])
        self.assertEqual(run_dict["routes"], [])
        self.assertEqual(run_dict["vias"], [])
        self.assertEqual(run_dict["metrics"], {})
        gs = summary["groups_summary"]["B"]
        self.assertEqual(gs["unknown_count"], 1)
        self.assertEqual(gs["blocked_count"], 1)
        self.assertEqual(gs["sat_rate"], 0.0)
        self.assertIsNone(gs["mean_objective_sat"])

    def test_missing_validated_file_is_unknown(self):
        out_dir = self._out("miss-run")
        summary = run_e1.run([SID], ["C"], SRC, self._out("miss-actions"),
                             out_dir)
        run_dict = model.read_json(
            os.path.join(out_dir, "solver-run-%s-C.json" % SID))
        self.assertEqual(run_dict["status"], "unknown")
        self.assertEqual(run_dict["blocked_from"], "validator")
        gs = summary["groups_summary"]["C"]
        self.assertEqual(gs["blocked_count"], 1)

    def test_full_pipe_legal_response_reaches_solver(self):
        actions_dir = self._out("pipe-actions")
        validated = actions.validate_response(
            legal_response(self.board), self.board, "B")
        self.assertFalse(validated["blocked"])
        write_validated(actions_dir, SID, "B", validated)
        out_dir = self._out("pipe-run")
        run_e1.run([SID], ["A", "B"], SRC, actions_dir, out_dir)
        run_dict = model.read_json(
            os.path.join(out_dir, "solver-run-%s-B.json" % SID))
        self.assertIn(run_dict["status"], ("sat", "failed"))
        self.assertNotIn("blocked_from", run_dict)
        # corridor 偏好必须真的进入求解：n1 被迫绕行，几何与 A 组不同
        # （actions_digest 只哈希动作清单，区分不了几何，故比对路线本体）。
        a_run = model.read_json(
            os.path.join(out_dir, "solver-run-%s-A.json" % SID))
        self.assertNotEqual(run_dict["routes"], a_run["routes"])

    def test_router_rejected_actions_visible_as_unknown(self):
        """validator 放行但 router 拒绝（protect 未排最前）=> unknown，
        不得崩溃、不得静默。"""
        resp = legal_response(self.board)
        resp["actions"]["protect"] = ["n3"]  # route_order 中 n3 排最后
        validated = actions.validate_response(resp, self.board, "B")
        self.assertFalse(validated["blocked"])  # 合同只 block 未知 net
        actions_dir = self._out("rej-actions")
        write_validated(actions_dir, SID, "B", validated)
        out_dir = self._out("rej-run")
        summary = run_e1.run([SID], ["B"], SRC, actions_dir, out_dir)
        run_dict = model.read_json(
            os.path.join(out_dir, "solver-run-%s-B.json" % SID))
        self.assertEqual(run_dict["status"], "unknown")
        self.assertEqual(run_dict["blocked_from"], "router")
        gs = summary["groups_summary"]["B"]
        self.assertEqual(gs["unknown_count"], 1)
        self.assertEqual(gs["blocked_count"], 0)


class TestDeterminism(unittest.TestCase):
    """同输入双跑逐字节一致；replay 比对与篡改检出。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="v4exp-e1-det-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _actions_dir(self):
        d = os.path.join(self._tmp, "actions")
        os.makedirs(d, exist_ok=True)
        return d

    def test_double_run_byte_exact(self):
        out1 = os.path.join(self._tmp, "run1")
        out2 = os.path.join(self._tmp, "run2")
        kwargs = dict(scenario_ids=[SID], groups=["A", "B"],
                      source_dir=SRC, actions_dir=self._actions_dir())
        s1 = run_e1.run(replay=False, out_dir=out1, **kwargs)
        s2 = run_e1.run(replay=False, out_dir=out2, **kwargs)
        self.assertEqual(s1, s2)
        names = sorted(os.listdir(out1))
        self.assertEqual(names, sorted(os.listdir(out2)))
        for name in names:
            with open(os.path.join(out1, name), "rb") as f:
                b1 = f.read()
            with open(os.path.join(out2, name), "rb") as f:
                b2 = f.read()
            self.assertEqual(b1, b2, name)
        # run 文件无 wall-clock / 主机绝对路径痕迹
        for name in names:
            with open(os.path.join(out1, name), "r",
                      encoding="utf-8") as f:
                text = f.read()
            for marker in ABS_MARKERS:
                self.assertNotIn(marker, text, "%s 含 %r" % (name, marker))

    def test_replay_all_same_and_detects_tampering(self):
        out_dir = os.path.join(self._tmp, "replay-run")
        run_e1.run([SID], ["A"], SRC, self._actions_dir(), out_dir)
        check = run_e1.run([SID], ["A"], SRC, self._actions_dir(), out_dir,
                           replay=True)
        self.assertTrue(check["all_same"])
        self.assertEqual(len(check["files"]), 1)
        self.assertTrue(check["files"][0]["same"])
        self.assertNotIn("timestamp", json.dumps(check))
        # 篡改一个 run 文件后 replay 必须报 diff（canonical JSON 无空格分隔）
        target = os.path.join(out_dir, "solver-run-%s-A.json" % SID)
        with open(target, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn('"sat"', text)
        with open(target, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace('"sat"', '"xxx"', 1))
        check2 = run_e1.run([SID], ["A"], SRC, self._actions_dir(), out_dir,
                            replay=True)
        self.assertFalse(check2["all_same"])
        self.assertFalse(check2["files"][0]["same"])
        # replay 模式不覆盖磁盘上的 run 文件
        with open(target, "r", encoding="utf-8") as f:
            self.assertIn('"xxx"', f.read())


class TestPrepareInputs(unittest.TestCase):
    """B/C/D 三组 planner 输入的内容边界。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="v4exp-e1-inputs-")
        cls.inputs_dir = os.path.join(cls._tmp, "inputs")
        cls.summary = prepare_inputs.run(["development"], ["B", "C", "D"],
                                         cls.inputs_dir, source_dir=SRC)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_all_dev_scenarios_x_groups_written(self):
        self.assertEqual(len(self.summary["scenario_ids"]), 30)
        self.assertEqual(len(self.summary["files_written"]), 90)
        for sid in self.summary["scenario_ids"]:
            self.assertTrue(sid.startswith("dev-"), sid)
            for g in ("B", "C", "D"):
                path = os.path.join(self.inputs_dir,
                                    "planner-input-%s-%s.json" % (sid, g))
                self.assertTrue(os.path.exists(path), path)

    def _load(self, sid, group):
        return model.read_json(os.path.join(
            self.inputs_dir, "planner-input-%s-%s.json" % (sid, group)))

    def test_group_b_summary_without_label(self):
        board = model.read_json(os.path.join(SRC,
                                             "board-snapshot-%s.json" % SID))
        obj = self._load(SID, "B")
        self.assertNotIn("label", obj)
        self.assertNotIn("label", obj["board_summary"])
        self.assertNotIn("seed", obj["board_summary"])
        bs = obj["board_summary"]
        self.assertEqual(set(bs), {"bbox_mm", "layers", "rules", "pads",
                                   "nets", "keepouts", "relations"})
        self.assertEqual(bs["rules"], board["rules"])
        self.assertEqual(bs["bbox_mm"], board["board"]["bbox_mm"])
        self.assertEqual(obj["board_snapshot_sha256"],
                         model.sha256_of(board))
        self.assertIn("planner-response/1", obj["contract_text"])
        self.assertEqual(prepare_inputs.CONTRACT_TEXT, obj["contract_text"])

    def test_group_c_has_svg_and_png_pointer(self):
        obj = self._load(SID, "C")
        self.assertTrue(obj["svg_source"].startswith("<?xml"))
        self.assertIn('data-board-snapshot-sha256="%s"'
                      % obj["board_snapshot_sha256"], obj["svg_source"])
        self.assertEqual(
            obj["png_path"],
            "out/v4-experiment/route-preview-%s-1200x675.png" % SID)
        self.assertNotIn("label", obj)
        self.assertNotIn("label", obj["board_summary"])
        for marker in ABS_MARKERS:
            self.assertNotIn(marker, obj["png_path"])

    def test_group_d_pointer_only(self):
        # D 组：规划信息只有 PNG 指针；但必须带 board_snapshot_sha256
        # （内容寻址串，不泄露板几何），否则 D 响应会被协议必然拦截，
        # §5.4 条件 6 的"像素复原"诊断就退化为平凡结论。
        board = model.read_json(os.path.join(SRC,
                                             "board-snapshot-%s.json" % SID))
        obj = self._load(SID, "D")
        self.assertEqual(
            set(obj),
            {"schema", "scenario_id", "group", "inputs", "contract_text",
             "board_snapshot_sha256"})
        self.assertEqual(obj["board_snapshot_sha256"],
                         model.sha256_of(board))
        self.assertEqual(
            obj["inputs"],
            ["out/v4-experiment/route-preview-%s-1200x675.png" % SID])
        self.assertNotIn("board_summary", obj)
        self.assertNotIn("svg_source", obj)

    def test_group_calibration_generation(self):
        """calibration 10 场景 x B/C/D 同一冻结代码可生成（holdout 留给
        主智能体，测试不碰）。"""
        cal_dir = os.path.join(self._tmp, "inputs-cal")
        summary = prepare_inputs.run(["calibration"], ["B", "C", "D"],
                                     cal_dir, source_dir=SRC)
        self.assertEqual(len(summary["scenario_ids"]), 10)
        self.assertEqual(len(summary["files_written"]), 30)
        for sid in summary["scenario_ids"]:
            self.assertTrue(sid.startswith("cal-"), sid)
        obj = model.read_json(os.path.join(
            self._tmp, "inputs-cal",
            "planner-input-cal-f1-07-D.json"))
        self.assertIn("board_snapshot_sha256", obj)
        self.assertNotIn("board_summary", obj)

    def test_frozen_contract_identical_across_groups(self):
        texts = set()
        for g in ("B", "C", "D"):
            texts.add(self._load(SID, g)["contract_text"])
        self.assertEqual(len(texts), 1)

    def test_prepare_inputs_deterministic(self):
        other = os.path.join(self._tmp, "inputs-again")
        summary2 = prepare_inputs.run(["development"], ["B", "C", "D"],
                                      other, source_dir=SRC)
        self.assertEqual(self.summary["files_written"],
                         summary2["files_written"])
        for name in self.summary["files_written"]:
            with open(os.path.join(self.inputs_dir, name), "rb") as f:
                b1 = f.read()
            with open(os.path.join(other, name), "rb") as f:
                b2 = f.read()
            self.assertEqual(b1, b2, name)


if __name__ == "__main__":
    unittest.main()
