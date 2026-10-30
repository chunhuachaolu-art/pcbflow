# -*- coding: utf-8 -*-
"""E5 投影模块测试：确定性（同输入同输出字节）、零换算坐标帧、零泄露字段、
候选几何投影、fail-closed。"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow.v4_1 import projection  # noqa: E402


def _board():
    return {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": "t-f1-01", "split": "development", "family": "f1",
        "seed": 7, "label": "satisfiable",
        "board": {"bbox_mm": [0.0, 0.0, 20.0, 15.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                  "width_mm": {"default": 0.3, "clock": 0.4},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                     "clock": ["F.Cu"]}},
        "pads": [
            {"pad_id": "U2-1", "net_id": "n2", "x_mm": 18.0, "y_mm": 13.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 2.0, "y_mm": 2.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U1-2", "net_id": "n1", "x_mm": 18.0, "y_mm": 2.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-2", "net_id": "n2", "x_mm": 2.0, "y_mm": 13.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
        ],
        "nets": [
            {"net_id": "n2", "net_class": "default",
             "endpoints": ["U2-2", "U2-1"]},
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U1-2"]},
        ],
        "keepouts": [
            {"keepout_id": "k2", "rect_mm": [10.0, 3.0, 11.0, 12.0],
             "layers": ["F.Cu"]},
            {"keepout_id": "k1", "rect_mm": [5.0, 3.0, 6.0, 12.0],
             "layers": ["F.Cu"]},
        ],
        "relations": [],
    }


class TestProjectionDeterminism(unittest.TestCase):

    def test_same_input_same_output_bytes(self):
        b = _board()
        a = projection.projection_canonical_bytes(projection.build_projection(b))
        d = projection.projection_canonical_bytes(projection.build_projection(b))
        self.assertEqual(a, d)

    def test_deterministic_across_key_order_and_list_shuffle(self):
        b1 = _board()
        b2 = copy.deepcopy(b1)
        b2["pads"].reverse()
        b2["nets"].reverse()
        b2["keepouts"].reverse()
        # manifest 内容相同、列表序不同 → 投影排序后仍逐字节一致
        self.assertEqual(
            projection.projection_canonical_bytes(
                projection.build_projection(b1)),
            projection.projection_canonical_bytes(
                projection.build_projection(b2)))


class TestProjectionContent(unittest.TestCase):

    def test_coordinate_frame_zero_conversion(self):
        p = projection.build_projection(_board())
        self.assertEqual(p["coordinate_frame"]["system"], "board_mm")
        # pads 坐标与 manifest 原值逐字节一致（零换算、零 +2.0 边距）
        by_id = {x["pad_id"]: x for x in p["pads"]}
        self.assertEqual(by_id["U1-1"]["x_mm"], 2.0)
        self.assertEqual(by_id["U1-1"]["y_mm"], 2.0)
        self.assertEqual(by_id["U2-1"]["x_mm"], 18.0)
        self.assertEqual(by_id["U2-1"]["y_mm"], 13.0)

    def test_sorted_object_table(self):
        p = projection.build_projection(_board())
        self.assertEqual([x["pad_id"] for x in p["pads"]],
                         ["U1-1", "U1-2", "U2-1", "U2-2"])
        self.assertEqual([n["net_id"] for n in p["nets"]], ["n1", "n2"])
        self.assertEqual([k["keepout_id"] for k in p["keepouts"]],
                         ["k1", "k2"])

    def test_no_label_leak(self):
        p = projection.build_projection(_board())
        text = repr(p)
        for leak in ("satisfiable", "unsatisfiable", "development",
                     "calibration", "holdout"):
            self.assertNotIn(leak, text)
        self.assertNotIn("label", p)
        self.assertNotIn("family", p)
        self.assertNotIn("split", p)
        self.assertNotIn("seed", p)

    def test_span_summary_derived(self):
        p = projection.build_projection(_board())
        n1 = p["nets"][0]
        self.assertEqual(n1["span_summary"]["dx_mm"], 16.0)
        self.assertEqual(n1["span_summary"]["dy_mm"], 0.0)
        self.assertEqual(n1["span_summary"]["straight_line_mm"], 16.0)
        self.assertEqual(n1["span_summary"]["endpoint_objects"][0]["pad_id"],
                         "U1-1")

    def test_candidate_geometry_projection(self):
        b = _board()
        geom = {
            "routes": [{
                "route_id": "n1-S01", "net_id": "n1", "layer": "F.Cu",
                "width_mm": 0.3, "polyline_mm": [[2.0, 2.0], [18.0, 2.0]],
                "endpoint_ids": ["U1-1", "U1-2"],
            }],
            "vias": [],
        }
        p = projection.build_projection(b, geom)
        routes = p["candidate_geometry"]["routes"]
        self.assertEqual(len(routes), 1)
        r = routes[0]
        # manifest 原字段 + 先例身份补齐（relation_ids/line_type/state/source）
        self.assertEqual(r["route_id"], "n1-S01")
        self.assertEqual(r["polyline_mm"], [[2.0, 2.0], [18.0, 2.0]])
        self.assertEqual(r["relation_ids"], [])
        self.assertEqual(r["line_type"], "signal")
        # 坐标零换算：直接是板 mm
        self.assertEqual(r["polyline_mm"][0], [2.0, 2.0])

    def test_candidate_geometry_sorted(self):
        b = _board()
        geom = {
            "routes": [
                {"route_id": "n2-S01", "net_id": "n2", "layer": "F.Cu",
                 "width_mm": 0.3, "polyline_mm": [[2.0, 13.0], [18.0, 13.0]],
                 "endpoint_ids": ["U2-2", "U2-1"]},
                {"route_id": "n1-S01", "net_id": "n1", "layer": "F.Cu",
                 "width_mm": 0.3, "polyline_mm": [[2.0, 2.0], [18.0, 2.0]],
                 "endpoint_ids": ["U1-1", "U1-2"]},
            ],
            "vias": [],
        }
        p = projection.build_projection(b, geom)
        self.assertEqual([r["route_id"] for r in p["candidate_geometry"]["routes"]],
                         ["n1-S01", "n2-S01"])

    def test_no_svg_in_projection(self):
        b = _board()
        p = projection.build_projection(b)
        self.assertNotIn("svg_source", p)
        self.assertNotIn("viewBox", repr(p))


class TestProjectionFailClosed(unittest.TestCase):

    def test_missing_board(self):
        with self.assertRaises(ValueError):
            projection.build_projection({"nets": []})

    def test_none_board(self):
        with self.assertRaises(ValueError):
            projection.build_projection(None)


if __name__ == "__main__":
    unittest.main()
