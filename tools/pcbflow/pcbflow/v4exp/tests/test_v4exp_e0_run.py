"""E0 编排器测试：单场景 tmp 全流程 + 双跑字节一致 + 门判定咬合。"""

import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unittest

from pcbflow.v4exp import model, run_e0
from pcbflow.v4exp.tests.test_v4exp_e0_fixture import (FIXTURE_SID,
                                                       copy_real_fixture)

ISO_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T")


def _results_text(results: dict) -> str:
    return json.dumps(results, ensure_ascii=False, indent=2) + "\n"


class TestRunE0SingleScenario(unittest.TestCase):
    """dev-f1-01 真实产物副本上的端到端编排（含 f1 突变全组）。"""

    def test_double_run_byte_identical_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_real_fixture(tmp, FIXTURE_SID)
            r1 = run_e0.compute_results({"source_dir": tmp})
            r2 = run_e0.compute_results({"source_dir": tmp})
            t1 = _results_text(r1)
            t2 = _results_text(r2)
            self.assertEqual(t1, t2, "同输入两遍结果必须逐字节一致")
            self.assertEqual(r1["schema"], "pcbflow.v4exp.e0-results/1")
            s = r1["summary"]
            self.assertEqual(s["scenarios"], 1)
            self.assertEqual(s["checks_run"], len(run_e0.ALL_CHECK_NAMES))
            self.assertEqual(s["checks_failed"], 0)
            self.assertEqual(s["mutations_run"], 8)
            self.assertEqual(s["mutations_blocked"], 8)
            self.assertEqual(s["positive_controls_passed"], 1)
            self.assertEqual(s["overall"], "pass")
            entry = r1["per_scenario"][0]
            self.assertEqual(entry["scenario_id"], FIXTURE_SID)
            self.assertEqual(set(entry["checks"]),
                             set(run_e0.ALL_CHECK_NAMES))
            self.assertEqual(len(entry["mutations"]), 9)
            # 结果文本不含主机绝对路径 / wall-clock
            self.assertNotIn(tmp, t1)
            self.assertIsNone(ISO_TS_RE.search(t1),
                              "结果不得含 ISO 时间戳")

    def test_gate_bites_on_tampered_manifest(self):
        # 篡改 manifest（width +0.1）后 overall 必须 fail 且一致性检查咬合
        with tempfile.TemporaryDirectory() as tmp:
            copy_real_fixture(tmp, FIXTURE_SID)
            mpath = os.path.join(tmp, f"route-manifest-{FIXTURE_SID}.json")
            man = model.read_json(mpath)
            man["routes"][0]["width_mm"] += 0.1
            model.write_json(mpath, man)
            r = run_e0.compute_results({"source_dir": tmp})
            self.assertEqual(r["summary"]["overall"], "fail")
            self.assertGreater(r["summary"]["checks_failed"], 0)
            entry = r["per_scenario"][0]
            self.assertFalse(
                entry["checks"]["manifest_svg_consistency"]["pass"])

    def test_gate_bites_on_missing_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_real_fixture(tmp, FIXTURE_SID)
            os.remove(os.path.join(
                tmp, f"route-preview-{FIXTURE_SID}-2400x1350.png"))
            r = run_e0.compute_results({"source_dir": tmp})
            self.assertEqual(r["summary"]["overall"], "fail")
            entry = r["per_scenario"][0]
            self.assertFalse(
                entry["checks"]["resolution_invariance"]["pass"])


class TestGateLogic(unittest.TestCase):
    """门判定硬编码逻辑的单体验证（构造最小 per_scenario）。"""

    @staticmethod
    def _ok_scenario(sid="s1", with_mutations=True):
        checks = {name: {"check": name, "pass": True, "reason": ""}
                  for name in run_e0.ALL_CHECK_NAMES}
        muts = []
        if with_mutations:
            for name in run_e0.e0_mutate.ALL_MUTATIONS:
                muts.append({
                    "mutation": name,
                    "expected": "pass" if name == run_e0.POSITIVE
                    else "blocked",
                    "observed": "pass" if name == run_e0.POSITIVE
                    else "blocked",
                    "pass": True})
        return {"scenario_id": sid, "checks": checks, "mutations": muts}

    def test_all_pass_with_mutations_is_pass(self):
        per = [self._ok_scenario("a"), self._ok_scenario("b",
                                                         with_mutations=False)]
        self.assertEqual(run_e0.overall_from(per), "pass")

    def test_failing_check_is_fail(self):
        per = [self._ok_scenario()]
        per[0]["checks"]["roundtrip_mm"]["pass"] = False
        self.assertEqual(run_e0.overall_from(per), "fail")

    def test_unblocked_negative_mutation_is_fail(self):
        per = [self._ok_scenario()]
        for row in per[0]["mutations"]:
            if row["mutation"] == "width_mismatch":
                row["observed"] = "pass"
                row["pass"] = False
        self.assertEqual(run_e0.overall_from(per), "fail")

    def test_failed_positive_control_is_fail(self):
        per = [self._ok_scenario()]
        for row in per[0]["mutations"]:
            if row["mutation"] == run_e0.POSITIVE:
                row["observed"] = "blocked"
                row["pass"] = False
        self.assertEqual(run_e0.overall_from(per), "fail")

    def test_no_mutations_at_all_is_fail(self):
        per = [self._ok_scenario(with_mutations=False)]
        self.assertEqual(run_e0.overall_from(per), "fail")

    def test_missing_check_entry_is_fail(self):
        per = [self._ok_scenario()]
        del per[0]["checks"]["identity_recovery"]
        self.assertEqual(run_e0.overall_from(per), "fail")


class TestMainEntry(unittest.TestCase):
    def test_main_read_writes_results_and_replay(self):
        with tempfile.TemporaryDirectory() as src, \
                tempfile.TemporaryDirectory() as out:
            copy_real_fixture(src, FIXTURE_SID)
            buf = io.StringIO()
            stdout_backup = sys.stdout
            sys.stdout = buf
            try:
                info = run_e0.main_read({"out_dir": out, "source_dir": src})
            finally:
                sys.stdout = stdout_backup
            results_path = os.path.join(out, "e0-results.json")
            replay_path = os.path.join(out, "replay-check-e0.json")
            self.assertTrue(os.path.exists(results_path))
            self.assertTrue(os.path.exists(replay_path))
            self.assertTrue(info["double_run_identical"])
            self.assertEqual(info["summary"]["overall"], "pass")
            with open(results_path, "r", encoding="utf-8") as f:
                text1 = f.read()
            replay = model.read_json(replay_path)
            self.assertEqual(replay["schema"],
                             "pcbflow.v4exp.e0-replay-check/1")
            self.assertTrue(replay["double_run_identical"])
            self.assertEqual(replay["overall_run1"], "pass")
            self.assertEqual(replay["overall_run2"], "pass")
            self.assertEqual(replay["results_sha256_run1"],
                             replay["results_sha256_run2"])
            self.assertEqual(replay["results_sha256_run1"],
                             hashlib.sha256(
                                 text1.encode("utf-8")).hexdigest())
            # 重放产物不含时间戳与绝对路径
            replay_text = json.dumps(replay)
            self.assertIsNone(ISO_TS_RE.search(replay_text))
            self.assertNotIn(src, replay_text)
            self.assertNotIn(out, replay_text)
            self.assertNotIn(tempfile.gettempdir(), replay_text)
            # 再跑一遍 main_read，results 逐字节一致（端到端重放）
            sys.stdout = io.StringIO()
            try:
                run_e0.main_read({"out_dir": out, "source_dir": src})
            finally:
                sys.stdout = stdout_backup
            with open(results_path, "r", encoding="utf-8") as f:
                text2 = f.read()
            self.assertEqual(text1, text2)


if __name__ == "__main__":
    unittest.main()
