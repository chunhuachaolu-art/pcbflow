"""Self-tests for pcbflow.v4exp.optimum (exhaustive-permutation optimum)."""

import json
import os
import sys
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_TESTS_DIR)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pcbflow.v4exp import optimum  # noqa: E402


def _fixture(name):
    path = os.path.join(_TESTS_DIR, "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _five_net_board():
    """Synthetic 5-net board: exceeds the exhaustion limit."""
    pads = []
    nets = []
    for i in range(5):
        y = 1.0 + 2.0 * i
        pads.append({"pad_id": "A%d" % i, "net_id": "n%d" % i, "x_mm": 2.0,
                     "y_mm": y, "w_mm": 0.6, "h_mm": 0.6, "layer": "F.Cu"})
        pads.append({"pad_id": "B%d" % i, "net_id": "n%d" % i, "x_mm": 18.0,
                     "y_mm": y, "w_mm": 0.6, "h_mm": 0.6, "layer": "F.Cu"})
        nets.append({"net_id": "n%d" % i, "net_class": "default",
                     "endpoints": ["A%d" % i, "B%d" % i]})
    return {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": "fix-five-nets",
        "split": "development",
        "family": "synthetic",
        "seed": 0,
        "board": {"bbox_mm": [0.0, 0.0, 20.0, 20.0], "layers": ["F.Cu", "B.Cu"]},
        "rules": {
            "grid_mm": 0.25,
            "clearance_mm": 0.3,
            "width_mm": {"default": 0.3, "clock": 0.4},
            "via": {"pad_mm": 0.6, "hole_mm": 0.3},
            "allowed_layers": {"default": ["F.Cu", "B.Cu"], "clock": ["F.Cu"]}
        },
        "pads": pads,
        "nets": nets,
        "keepouts": [],
        "relations": [],
        "label": "satisfiable",
    }


class TestOptimum(unittest.TestCase):
    def test_enclosed_board_is_unsat_certified(self):
        out = optimum.run_optimum(_fixture("fixture_enclosed.json"))
        self.assertEqual(out["schema"], "pcbflow.v4exp.optimum/1")
        self.assertTrue(out["opt_eligible"])
        self.assertEqual(out["permutations_tried"], 1)
        self.assertEqual(out["sat_permutations"], 0)
        self.assertTrue(out["unsat_certified"])
        self.assertEqual(out["certificate"], "exhaustive_over_permutations_v1")
        self.assertEqual(out["best_order"], [])
        self.assertIsNone(out["best_objective"])

    def test_alley_best_order_is_n2_first(self):
        out = optimum.run_optimum(_fixture("fixture_alley.json"))
        self.assertTrue(out["opt_eligible"])
        self.assertEqual(out["permutations_tried"], 2)
        self.assertEqual(out["sat_permutations"], 1)
        self.assertEqual(out["best_order"], ["n2", "n1"])
        self.assertEqual(out["best_objective"], 46.0)
        self.assertNotIn("unsat_certified", out)

    def test_single_net_board(self):
        out = optimum.run_optimum(_fixture("fixture_via.json"))
        self.assertTrue(out["opt_eligible"])
        self.assertEqual(out["permutations_tried"], 1)
        self.assertEqual(out["sat_permutations"], 1)
        self.assertEqual(out["best_order"], ["n1"])
        self.assertEqual(out["best_objective"], 18.0)
        self.assertNotIn("unsat_certified", out)

    def test_more_than_four_nets_is_not_eligible(self):
        out = optimum.run_optimum(_five_net_board())
        self.assertFalse(out["opt_eligible"])
        self.assertEqual(out["scenario_id"], "fix-five-nets")
        self.assertNotIn("permutations_tried", out)
        self.assertNotIn("unsat_certified", out)


if __name__ == "__main__":
    unittest.main()
