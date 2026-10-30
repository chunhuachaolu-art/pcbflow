# -*- coding: utf-8 -*-
"""VERIFY-1 战役测试：纯函数/账本逻辑 + 证据复核（test_verify1_ 前缀）。

证据类用例读取 out/coreboard-verify1/ 产物；产物缺失则 skipTest
（纯函数类用例无条件执行，不依赖任何产物）。"""
import json
import math
import os
import sys
import unittest

PCBFLOW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1_ROOT = os.path.join(PCBFLOW_ROOT, "out", "coreboard-verify1")
sys.path.insert(0, PCBFLOW_ROOT)
sys.path.insert(0, V1_ROOT)

import v1lib  # noqa: E402


MINI_BOARD = """(kicad_pcb
%s%s
  (segment
    (start 1.0 1.0)
    (end 2.0 1.0)
    (width 0.2)
    (layer "F.Cu")
    (net "A")
    (uuid "aaaaaaaa-1111-2222-3333-444444444444")
  )
  (segment
    (start 2.0 1.0)
    (end 3.0 1.0)
    (width 0.2)
    (layer "F.Cu")
    (net "B")
    (uuid "bbbbbbbb-1111-2222-3333-444444444444")
  )
  (via
    (at 3.5 1.0)
    (size 0.6)
    (drill 0.3)
    (layers "F.Cu" "In2.Cu")
    (net "B")
    (uuid "cccccccc-1111-2222-3333-444444444444")
  )
)
""" % ("  (layer \"F.Cu\")\n", "")


def _mini_after_drop_a():
    return MINI_BOARD.replace(
        '  (segment\n    (start 1.0 1.0)\n    (end 2.0 1.0)\n'
        '    (width 0.2)\n    (layer "F.Cu")\n    (net "A")\n'
        '    (uuid "aaaaaaaa-1111-2222-3333-444444444444")\n  )\n', "")


class TestVerify1StripBill(unittest.TestCase):
    def test_strip_bill_diff_pure(self):
        after = _mini_after_drop_a()
        bill = v1lib.strip_bill_from_diff(MINI_BOARD, after)
        self.assertEqual(len(bill["segments"]), 1)
        self.assertEqual(bill["segments"][0]["net"], "A")
        self.assertEqual(len(bill["vias"]), 0)

    def test_strip_bill_diff_identical_empty(self):
        bill = v1lib.strip_bill_from_diff(MINI_BOARD, MINI_BOARD)
        self.assertEqual(bill["segments"], [])
        self.assertEqual(bill["vias"], [])

    def test_bill_by_net_sorts_and_groups(self):
        after = _mini_after_drop_a()
        bill = v1lib.strip_bill_from_diff(MINI_BOARD, after)
        by_net = v1lib.bill_by_net(bill)
        self.assertEqual(sorted(by_net), ["A"])

    def test_protected_hit_check(self):
        bill = {"segments": [{"net": "3V3", "uuid": "x"}], "vias": []}
        hits = v1lib.protected_hit_check(bill, ("3V3", "GPIO_PE2"))
        self.assertEqual(len(hits), 1)
        self.assertEqual(v1lib.protected_hit_check(
            {"segments": [], "vias": []}, ("3V3",)), [])


class TestVerify1Anchors(unittest.TestCase):
    def test_pt_seg_dist(self):
        self.assertAlmostEqual(v1lib._pt_seg_dist(0, 1, -1, 0, 1, 0), 1.0)
        self.assertAlmostEqual(v1lib._pt_seg_dist(0, 0, -1, 0, 1, 0), 0.0)
        self.assertAlmostEqual(v1lib._pt_seg_dist(2, 0, -1, 0, 1, 0), 1.0)

    def test_endpoint_anchors_width_overlap(self):
        # 幸存端点距被剥段中心线 0.03mm < 半宽 0.1 → 命中（体接触口径）
        bill = {"segments": [{"net": "A", "x1": 0.0, "y1": 0.0,
                              "x2": 5.0, "y2": 0.0, "width": 0.2,
                              "layer_name": "F.Cu"}],
                "vias": []}
        survive = [{"net": "A", "x1": 5.03, "y1": 0.0, "x2": 6.0, "y2": 0.0,
                    "layer_name": "F.Cu", "width": 0.2}]
        out = v1lib.endpoint_anchors(bill, survive, [])
        self.assertEqual(len(out["A"]), 1)
        self.assertEqual(out["A"][0]["x"], 5.03)

    def test_endpoint_anchors_no_false_positive(self):
        bill = {"segments": [{"net": "A", "x1": 0.0, "y1": 0.0,
                              "x2": 5.0, "y2": 0.0, "width": 0.2,
                              "layer_name": "F.Cu"}],
                "vias": []}
        survive = [{"net": "A", "x1": 5.5, "y1": 0.0, "x2": 6.0, "y2": 0.0,
                    "layer_name": "F.Cu", "width": 0.2}]
        out = v1lib.endpoint_anchors(bill, survive, [])
        self.assertEqual(out["A"], [])


class TestVerify1SplitAndBatch(unittest.TestCase):
    def test_split_root_and_orphans(self):
        comps = [{"n_items": 30}, {"n_items": 1}]
        root, orphans = v1lib.split_root_and_orphans(comps)
        self.assertEqual(root, 0)
        self.assertEqual(orphans, [1])

    def test_split_empty(self):
        root, orphans = v1lib.split_root_and_orphans([])
        self.assertIsNone(root)
        self.assertEqual(orphans, [])

    def test_batch_gate(self):
        ok, n, nets = v1lib.batch_gate([["A", "B"], ["B", "C"]])
        self.assertTrue(ok)
        self.assertEqual(n, 3)
        ok, n, _ = v1lib.batch_gate([["n%d" % i for i in range(11)]])
        self.assertFalse(ok)
        self.assertEqual(n, 11)

    def test_pocket_overlap_real_pair(self):
        gnda = {"pocket": [22.325, 30.15], "radius_mm": 1.5}
        fmc = {"pocket": [22.325, 33.65], "radius_mm": 1.5}
        res = v1lib.pocket_overlap(gnda, fmc)
        self.assertAlmostEqual(res["dist_mm"], 3.5)
        self.assertFalse(res["overlap"])
        near = v1lib.pocket_overlap(gnda, {"pocket": [22.325, 31.0],
                                           "radius_mm": 1.5})
        self.assertTrue(near["overlap"])


class TestVerify1PrefixClearance(unittest.TestCase):
    def test_layer_aware_pass(self):
        # 同几何不同层：不冲突
        prefix = [(0, 0.0, 0.0, 1.0, 0.0, 0.2)]
        added = [{"net": "X", "segments": [(6, 0.0, 0.0, 1.0, 0.0)],
                  "vias": []}]
        ok, _ = v1lib.prefix_ok_with_added(prefix, [], added)
        self.assertTrue(ok)

    def test_layer_aware_fail_same_layer(self):
        prefix = [(0, 0.0, 0.0, 1.0, 0.0, 0.2)]
        added = [{"net": "X", "segments": [(0, 0.0, 0.1, 1.0, 0.1)],
                  "vias": []}]
        ok, worst = v1lib.prefix_ok_with_added(prefix, [], added)
        self.assertFalse(ok)  # 中心距 0.1 < 需 0.4
        self.assertLess(worst, 0)

    def test_via_needs_bigger_margin(self):
        prefix = [(0, 0.0, 0.0, 1.0, 0.0, 0.2)]
        added = [{"net": "X", "segments": [], "vias": [(0.5, 0.45)]}]
        ok, _ = v1lib.prefix_ok_with_added(prefix, [], added)
        self.assertFalse(ok)  # 距 0.45 < 线-孔需 0.6


class TestVerify1LayerPolicy(unittest.TestCase):
    def test_restore_first(self):
        pol = v1lib.reroute_layer_policy("GPIO_PC2C", [0], [0], False)
        self.assertEqual(sorted(pol[0][0]), [0])
        self.assertFalse(pol[0][2])
        # 尝试 2 = 双层救场
        self.assertEqual(sorted(pol[1][0]), [0, 6])
        self.assertTrue(pol[1][2])

    def test_deviation_only_new_in2_on_f_only_net(self):
        # ANLG 原链无孔而新解含 In2 → deviation
        pol = v1lib.reroute_layer_policy("VDDA", [0], [6], False)
        self.assertTrue(pol[0][2])
        # 原链带孔（恢复原状态）→ 不算新增偏离
        pol = v1lib.reroute_layer_policy("VDDA", [0], [6], True)
        self.assertFalse(pol[0][2])


class TestVerify1DrcReads(unittest.TestCase):
    def test_drc_reads_and_new_error_keys(self):
        base = {"violations": [{"severity": "error", "type": "clearance",
                                "items": [{"description": "x",
                                           "pos": {"x": 1, "y": 2}}]}],
                "unconnected_items": []}
        post = {"violations": base["violations"] +
                [{"severity": "error", "type": "shorting_items",
                  "items": [{"description": "y", "pos": {"x": 3, "y": 4}}]}],
                "unconnected_items": [{"description": "A", "pos":
                                       {"x": 0, "y": 0}}]}
        self.assertEqual(v1lib.new_error_keys(base, post), [
            "shorting_items|y|3.0000,4.0000"])
        self.assertEqual(v1lib.new_error_keys(base, base), [])
        reads = v1lib.drc_reads(post)
        self.assertEqual(reads["unconnected"], 1)
        self.assertEqual(reads["severity"]["error"], 2)


class TestVerify1LedgerEvidence(unittest.TestCase):
    def setUp(self):
        self.ledgers = {}
        for case, segs, vias in (("gnda", 7, 1), ("fmc", 22, 0)):
            p = os.path.join(V1_ROOT, "ledger",
                             "%s-strip-ledger.json" % case)
            if not os.path.isfile(p):
                self.skipTest("ledger 缺失：%s" % p)
            self.ledgers[case] = (json.load(open(p, encoding="utf-8")),
                                  segs, vias)

    def test_strip_reproduced_sha(self):
        for case, (led, _s, _v) in self.ledgers.items():
            self.assertTrue(led["reproduced"], case)
            self.assertEqual(led["rebuilt_sha256"],
                             led["design1_strip_sha256"], case)

    def test_counts_match_design1(self):
        for case, (led, segs, vias) in self.ledgers.items():
            self.assertEqual(led["counts"]["segments"], segs, case)
            self.assertEqual(led["counts"]["vias"], vias, case)

    def test_no_protected_hits(self):
        for case, (led, _s, _v) in self.ledgers.items():
            self.assertEqual(led["protected_hits"], 0, case)
            for d in led["bill"]["segments"] + led["bill"]["vias"]:
                self.assertNotIn(d["net"], ("3V3", "GPIO_PE2"), case)


class TestVerify1VerdictEvidence(unittest.TestCase):
    def _load(self, rel):
        p = os.path.join(V1_ROOT, rel)
        if not os.path.isfile(p):
            self.skipTest("产物缺失：%s" % p)
        return json.load(open(p, encoding="utf-8"))

    def test_obligations_single_break_per_net(self):
        for case, nets in (("gnda", 4), ("fmc", 7)):
            o = self._load("verdicts/%s-obligations.json" % case)
            self.assertEqual(len(o["nets"]), nets, case)
            for net, info in o["nets"].items():
                self.assertEqual(info["new_breaks"], 1, (case, net))

    def test_postcheck_truth_tables(self):
        g = self._load("verdicts/gnda-postcheck.json")
        self.assertTrue(g["nets"]["GNDA"]["truly_closed"])
        self.assertFalse(g["nets"]["VDDA"]["truly_closed"])
        self.assertEqual(g["truly_closed_count"], 4)
        f = self._load("verdicts/fmc-postcheck.json")
        self.assertTrue(f["nets"]["FMC_SDNE0"]["truly_closed"])
        self.assertEqual(f["truly_closed_count"], 5)
        self.assertFalse(f["nets"]["ETH_REF_CLK"]["truly_closed"])

    def test_witness_absent_probe_direction(self):
        for case, fails in (("gnda", ["VDDA"]), ("fmc", ["VDDA",
                                                         "QSPI_IO1"])):
            v = self._load("verdicts/%s-reroute-verdicts.json" % case)
            by = {x["net"]: x for x in v["verdicts"]}
            for net in fails:
                self.assertFalse(by[net]["ok"], (case, net))
                self.assertTrue(by[net].get("witness_absent_solvable"),
                                (case, net))


class TestVerify1MergeShortEvidence(unittest.TestCase):
    def test_two_witnesses_same_layer_crossing(self):
        d1 = os.path.join(PCBFLOW_ROOT, "out", "coreboard-design1")
        gp = os.path.join(d1, "rows",
                          "classa_RPL-039_GNDA_pocket_wall_strip_1.5_6.json")
        fp = os.path.join(d1, "rows",
                          "classa_RPL-038_FMC_SDNE0_pocket_wall_strip"
                          "_1.5_4.json")
        if not (os.path.isfile(gp) and os.path.isfile(fp)):
            self.skipTest("design1 rows 缺失")
        g = json.load(open(gp, encoding="utf-8"))["route_plan"]
        f = json.load(open(fp, encoding="utf-8"))["route_plan"]

        def inter(a, b):
            (L1, x1, y1, x2, y2), (L2, a1, b1, a2, b2) = a, b
            d = (x2 - x1) * (b2 - b1) - (y2 - y1) * (a2 - a1)
            if abs(d) < 1e-12:
                return False
            t = ((a1 - x1) * (b2 - b1) - (b1 - y1) * (a2 - a1)) / d
            u = ((a1 - x1) * (y2 - y1) - (b1 - y1) * (x2 - x1)) / d
            return 0 <= t <= 1 and 0 <= u <= 1
        hits = [1 for s in g["segments"] for t in f["segments"]
                if s[0] == t[0] and inter(s, t)]
        self.assertGreaterEqual(len(hits), 1,
                                "两 witness 同层至少 1 处相交（合并短路证据）")
        # 孔位重合（不同网同点孔=死短）
        gvia = {(v[0], v[1]) for v in g["vias"]}
        fvia = {(v[0], v[1]) for v in f["vias"]}
        self.assertTrue(gvia & fvia, "两 witness 存在同点孔")


class TestVerify1ViafixEvidence(unittest.TestCase):
    def test_in1_conflicts_are_stale_fill_class(self):
        for case in ("gnda", "fmc"):
            p = os.path.join(V1_ROOT, "verdicts", "%s-viafix.json" % case)
            if not os.path.isfile(p):
                self.skipTest("产物缺失：%s" % p)
            d = json.load(open(p, encoding="utf-8"))
            conflicted = [x for x in d["per_via"] if x["norefill_conflicts"]]
            for x in conflicted:
                self.assertEqual(x.get("refill_conflicts"), [],
                                 (case, x["via"]))


if __name__ == "__main__":
    unittest.main()
