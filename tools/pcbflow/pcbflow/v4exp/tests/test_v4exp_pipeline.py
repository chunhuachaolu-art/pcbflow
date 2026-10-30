"""A 包管线测试：生成器 -> 参考布线 -> SVG/manifest/PNG 全链（临时目录）。"""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from pcbflow.v4exp import emit_all, gen_scenarios, model

SVG_NS = "http://www.w3.org/2000/svg"


class TestPipeline(unittest.TestCase):
    """only_dev 全链冒烟 + f5 不可满足语义 + 确定性重放。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="v4exp-a-pkg-")
        cls.out_dir = os.path.join(cls._tmp, "v4-experiment")
        gen_scenarios.generate(cls.out_dir, only_dev=True)
        cls.summary = emit_all.run(cls.out_dir, ["development"])

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_dev_scenarios_generated(self):
        sm = model.read_json(os.path.join(self.out_dir,
                                          "scenario-manifest.json"))
        self.assertEqual(len(sm["scenarios"]), 30)
        for e in sm["scenarios"]:
            self.assertEqual(e["split"], "development")
            self.assertTrue(os.path.exists(os.path.join(
                self.out_dir,
                f"board-snapshot-{e['scenario_id']}.json")))
        # family -> split 隔离：每族 dev 6
        for fam, groups in sm["families"].items():
            self.assertEqual(len(groups["development"]), 6, fam)
            self.assertEqual(groups["calibration"], [])
            self.assertEqual(groups["holdout"], [])

    def test_emit_covers_all_dev(self):
        self.assertEqual(self.summary["scenarios"], 30)
        self.assertEqual(self.summary["splits"], ["development"])
        for r in self.summary["results"]:
            for p in r["files"]:
                self.assertTrue(os.path.exists(p), p)

    def test_f5_unrouted_but_has_svg(self):
        f5 = [r for r in self.summary["results"]
              if r["scenario_id"].startswith("dev-f5")]
        self.assertEqual(len(f5), 6)
        for r in f5:
            self.assertTrue(r["reference_unrouted"],
                            r["scenario_id"])
            # 被环形围死的是 n1；其余 net 玩具布线器正常连通
            self.assertIn("n1", r["unrouted_net_ids"])
            svg_path = os.path.join(self.out_dir,
                                    f"route-preview-{r['scenario_id']}.svg")
            root = ET.parse(svg_path).getroot()
            self.assertEqual(root.get("data-pcbflow-schema"),
                             "v4-svg-route-1")
            mpath = os.path.join(
                self.out_dir, f"route-manifest-{r['scenario_id']}.json")
            m = model.read_json(mpath)
            route_nets = {rt["net_id"] for rt in m["routes"]}
            self.assertNotIn("n1", route_nets)
            self.assertEqual(len(m["routes"]), r["routes"])
            self.assertEqual(
                len(m["vias"]),
                len(model.read_json(os.path.join(
                    self.out_dir,
                    f"ref-routes-{r['scenario_id']}.json"))["vias"]))
            # unrouted net 的 endpoint pad 仍在图上
            self.assertTrue(root.findall(
                f"{{{SVG_NS}}}rect[@data-object-kind='pad']"))

    def test_fully_unrouted_edge_case_still_emits_svg(self):
        """全部 net 失败的退化场景：routes 为空，SVG/manifest 照常产出。"""
        from pcbflow.v4exp import ref_route as rr, svg_pkg as sp
        # n2 的一个 endpoint 被双层环形 keepout 围死（环心 (20,15)），
        # 且该 net 无替代路径 —— 唯一 net 失败 => routes 为空。
        obj = {
            "schema": "pcbflow.v4exp.board/1",
            "scenario_id": "dev-f5-99", "split": "development",
            "family": "f5", "seed": 1,
            "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                      "layers": ["F.Cu", "B.Cu"]},
            "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                      "width_mm": {"default": 0.3, "clock": 0.4},
                      "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                      "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                         "clock": ["F.Cu"]}},
            "pads": [
                {"pad_id": "U2-1", "net_id": "n2", "x_mm": 20.0, "y_mm": 15.0,
                 "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
                {"pad_id": "U2-2", "net_id": "n2", "x_mm": 5.0, "y_mm": 5.0,
                 "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"}],
            "nets": [
                {"net_id": "n2", "net_class": "default",
                 "endpoints": ["U2-2", "U2-1"]}],
            "keepouts": [
                {"keepout_id": "k1", "rect_mm": [17.0, 12.0, 23.0, 14.0],
                 "layers": ["F.Cu", "B.Cu"]},
                {"keepout_id": "k2", "rect_mm": [17.0, 16.0, 23.0, 18.0],
                 "layers": ["F.Cu", "B.Cu"]},
                {"keepout_id": "k3", "rect_mm": [17.0, 14.0, 19.0, 16.0],
                 "layers": ["F.Cu", "B.Cu"]},
                {"keepout_id": "k4", "rect_mm": [21.0, 14.0, 23.0, 16.0],
                 "layers": ["F.Cu", "B.Cu"]}],
            "relations": [],
            "label": "unsatisfiable"}
        board = model.board_from_obj(obj)
        ref = rr.route_board(board)
        self.assertEqual(ref["routes"], [])
        self.assertEqual(ref["vias"], [])
        self.assertTrue(ref["reference_unrouted"])
        manifest, svg = sp.build(board, ref)
        self.assertEqual(manifest["routes"], [])
        root = ET.fromstring(svg)
        self.assertEqual(root.get("data-pcbflow-schema"), "v4-svg-route-1")
        self.assertTrue(root.findall(
            f"{{{SVG_NS}}}rect[@data-object-kind='board_edge']"))
        self.assertTrue(root.findall(
            f"{{{SVG_NS}}}rect[@data-object-kind='keepout']"))
        self.assertIsNotNone(root.find(f"{{{SVG_NS}}}g[@id='legend']"))

    def test_non_f5_mostly_routed(self):
        bad = [r for r in self.summary["results"]
               if not r["scenario_id"].startswith("dev-f5")
               and r["reference_unrouted"]]
        # f1/f3 必须全布；f2/f4 允许玩具布线器容量性失败，但不允许全灭
        for r in self.summary["results"]:
            if r["scenario_id"].startswith(("dev-f1", "dev-f3")):
                self.assertFalse(r["reference_unrouted"], r["scenario_id"])
            if r["scenario_id"].startswith(("dev-f2", "dev-f4")):
                self.assertGreater(r["routes"], 0, r["scenario_id"])
        # 记录性断言：f2/f4 失败数有界（<= 每场景 2）
        for r in bad:
            self.assertLessEqual(len(r["unrouted_net_ids"]), 2)

    def test_seed_replay_deterministic(self):
        sid = "dev-f1-01"
        p1 = os.path.join(self.out_dir, f"board-snapshot-{sid}.json")
        obj1 = model.read_json(p1)
        gen_scenarios.generate(os.path.join(self._tmp, "replay"),
                               only_dev=False)
        p2 = os.path.join(self._tmp, "replay",
                          f"board-snapshot-{sid}.json")
        obj2 = model.read_json(p2)
        self.assertEqual(model.sha256_of(obj1), model.sha256_of(obj2))
        self.assertEqual(obj1, obj2)

    def test_products_have_no_absolute_paths(self):
        root_markers = (":\\", "C:/", "/home/", "/Users/")
        for name in os.listdir(self.out_dir):
            path = os.path.join(self.out_dir, name)
            if not name.endswith(".json"):
                continue
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for marker in root_markers:
                self.assertNotIn(marker, text,
                                 f"{name} 含主机绝对路径痕迹 {marker}")


if __name__ == "__main__":
    unittest.main()
