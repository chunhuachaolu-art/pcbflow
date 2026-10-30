"""cmp_scenarios 单测：数量/命名、确定性、去重、板校验、router 冒烟。"""

import os
import shutil
import tempfile
import unittest

from pcbflow.v4exp import cmp_scenarios, model, router


class TestScenarioSet(unittest.TestCase):
    def test_counts_and_naming(self):
        ids = cmp_scenarios.all_scenario_ids()
        self.assertEqual(len(ids), 112)
        dev = [i for i in ids if i.startswith("dev-")]
        cal = [i for i in ids if i.startswith("cal-")]
        hol = [i for i in ids if i.startswith("hol-")]
        self.assertEqual(len(dev), 60)
        self.assertEqual(len(cal), 20)
        self.assertEqual(len(hol), 32)
        # 新族只出现在 holdout
        for fam in ("f6", "f7", "f8"):
            self.assertTrue(all(i.startswith("hol-") for i in ids
                                if "-%s-" % fam in i))
            self.assertEqual(sum(1 for i in hol if "-%s-" % fam in i), 4)
        # serial 与上一轮 01-10 完全错开（f1..f5）
        for fam in ("f1", "f2", "f3", "f4", "f5"):
            for i in ids:
                if "-%s-" % fam in i:
                    serial = int(i.split("-")[-1])
                    if i.startswith("dev-"):
                        self.assertTrue(1 <= serial <= 12, i)
                    elif i.startswith("cal-"):
                        self.assertTrue(13 <= serial <= 16, i)
                    else:
                        self.assertTrue(17 <= serial <= 20, i)


class TestGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="v4cmp-gen-")
        cls.d1 = os.path.join(cls.tmp, "run1")
        cls.d2 = os.path.join(cls.tmp, "run2")
        cls.s1 = cmp_scenarios.generate(cls.d1)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_generate_deterministic_and_dedup(self):
        s2 = cmp_scenarios.generate(self.d2)
        self.assertEqual(self.s1["scenarios"], 112)
        self.assertEqual(self.s1["counts"], {"development": 60,
                                             "calibration": 20,
                                             "holdout": 32})
        self.assertEqual(s2["scenarios"], 112)
        # 逐文件字节一致
        for sid in cmp_scenarios.all_scenario_ids():
            with open(os.path.join(self.d1,
                                   "board-snapshot-%s.json" % sid),
                      "rb") as f1, \
                 open(os.path.join(self.d2,
                                   "board-snapshot-%s.json" % sid),
                      "rb") as f2:
                self.assertEqual(f1.read(), f2.read(), sid)
        with open(os.path.join(self.d1, "scenario-manifest.json"),
                  "rb") as f1, \
             open(os.path.join(self.d2, "scenario-manifest.json"),
                  "rb") as f2:
            self.assertEqual(f1.read(), f2.read())
        # manifest 内 hash 全部唯一（去重门）
        man = model.read_json(
            os.path.join(self.d1, "scenario-manifest.json"))
        gh = [e["canonical_geometry_hash"] for e in man["scenarios"]]
        self.assertEqual(len(set(gh)), 112)
        bh = [e["board_snapshot_sha256"] for e in man["scenarios"]]
        self.assertEqual(len(set(bh)), 112)
        # f5 全 unsat，其余 satisfiable
        for e in man["scenarios"]:
            want = ("unsatisfiable" if "-f5-" in e["scenario_id"]
                    else "satisfiable")
            self.assertEqual(e["label"], want, e["scenario_id"])

    def test_single_generate_matches_batch(self):
        man = model.read_json(
            os.path.join(self.d1, "scenario-manifest.json"))
        attempts = {e["scenario_id"]: e["dedup_attempt"]
                    for e in man["scenarios"]}
        for sid in ("hol-f6-01", "hol-f7-03", "hol-f8-02", "dev-f1-07",
                    "cal-f5-14"):
            obj = cmp_scenarios.generate_scenario(sid, attempts[sid])
            disk = model.read_json(
                os.path.join(self.d1, "board-snapshot-%s.json" % sid))
            self.assertEqual(model.canonical_json(obj),
                             model.canonical_json(disk), sid)

    def test_router_smoke_all_holdout_new_families(self):
        """f6/f7/f8 holdout：A0 空偏好必须 sat（设计承诺可满足）。"""
        for sid in cmp_scenarios.all_scenario_ids():
            if not any("-%s-" % fam in sid for fam in ("f6", "f7", "f8")):
                continue
            board = model.read_json(
                os.path.join(self.d1, "board-snapshot-%s.json" % sid))
            order = sorted(n["net_id"] for n in board["nets"])
            run = router.solve_board(board, {"route_order": order,
                                             "group": "A"})
            self.assertEqual(run["status"], "sat",
                             "%s 未达设计承诺（应可满足）" % sid)


if __name__ == "__main__":
    unittest.main()
