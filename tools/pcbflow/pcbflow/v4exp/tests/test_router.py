"""Self-tests for the pcbflow.v4exp sequential A* router."""

import json
import os
import sys
import tempfile
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_TESTS_DIR)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pcbflow.v4exp import grid, router  # noqa: E402


def _fixture(name):
    path = os.path.join(_TESTS_DIR, "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestStraightBoard(unittest.TestCase):
    """f1-style point-to-point: A* must find the shortest Manhattan path."""

    def test_shortest_path_and_hand_computed_objective(self):
        board = _fixture("fixture_straight.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        self.assertEqual(run["schema"], "pcbflow.v4exp.solver-run/1")
        self.assertEqual(run["solver_version"], "v4exp-router-1")
        self.assertEqual(run["status"], "sat")
        m = run["metrics"]
        self.assertEqual(m["total_length_mm"], 10.0)   # (15-5) mm
        self.assertEqual(m["via_count"], 0)
        self.assertEqual(m["bend_count"], 0)
        self.assertEqual(m["objective"], 10.0)         # 1.0*10 + 8*0 + 0.5*0
        self.assertTrue(m["all_connected"])
        self.assertEqual(m["unconnected"], 0)
        self.assertEqual(m["shorts"], 0)
        self.assertEqual(m["violations"],
                         {"clearance": 0, "width": 0, "layer": 0, "keepout": 0})
        self.assertGreater(m["search_nodes"], 0)
        self.assertEqual(m["ripup_count"], 0)
        self.assertEqual(len(run["routes"]), 1)
        r = run["routes"][0]
        self.assertEqual(r["route_id"], "n1-S01")
        self.assertEqual(r["endpoint_ids"], ["PA-1", "PB-1"])
        self.assertEqual(r["state"], "candidate")
        self.assertEqual(r["source"], "solver")
        self.assertEqual(r["width_mm"], 0.3)
        self.assertEqual(r["polyline_mm"][0], [5.0, 6.0])
        self.assertEqual(r["polyline_mm"][-1], [15.0, 6.0])
        self.assertEqual(run["vias"], [])

    def test_result_file_roundtrip(self):
        # PC-01（REPAIR-P1 W-4）：selftest 输出写临时目录，冻结域
        # out/v4-experiment/selftest-c1/ 复跑零回写。
        board = _fixture("fixture_straight.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        with tempfile.TemporaryDirectory(
                prefix="pcbflow-v4exp-selftest-c1-") as tmp_dir:
            out_path = os.path.join(tmp_dir, "run-straight.json")
            router.write_result(run, out_path)
            with open(out_path, "r", encoding="utf-8") as f:
                self.assertEqual(json.load(f), run)

    def test_manifest_digest_is_sha_of_routes_and_vias(self):
        board = _fixture("fixture_straight.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        import hashlib
        expected = hashlib.sha256(grid.canonical_json(
            {"routes": run["routes"], "vias": run["vias"]}).encode("utf-8")
        ).hexdigest()
        self.assertEqual(run["route_manifest_sha256_at_run"], expected)

    def test_corridor_waypoints_force_detour(self):
        board = _fixture("fixture_straight.json")
        req = {"route_order": ["n1"],
               "corridor_preferences": [{"net_id": "n1",
                                         "waypoints_mm": [[5.0, 10.0]]}]}
        run = router.solve_board(board, req)
        self.assertEqual(run["status"], "sat")
        # 4 mm up + 10 mm across + 4 mm down = 18 mm, 2 bends
        self.assertEqual(run["metrics"]["total_length_mm"], 18.0)
        self.assertEqual(run["metrics"]["bend_count"], 2)
        self.assertEqual(run["metrics"]["objective"], 19.0)  # 18 + 0.5*2
        pts = [tuple(p) for p in run["routes"][0]["polyline_mm"]]
        self.assertIn((5.0, 10.0), pts)


class TestViaBoard(unittest.TestCase):
    """Endpoint pads on different layers: exactly one via is required."""

    def test_single_via_with_hand_computed_objective(self):
        board = _fixture("fixture_via.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        self.assertEqual(run["status"], "sat")
        m = run["metrics"]
        self.assertEqual(m["via_count"], 1)
        self.assertEqual(m["total_length_mm"], 10.0)
        self.assertEqual(m["objective"], 18.0)  # 10 + 8*1
        self.assertTrue(m["all_connected"])
        self.assertEqual(m["violations"]["layer"], 0)
        for r in run["routes"]:
            self.assertIn(r["layer"], ("F.Cu", "B.Cu"))
        self.assertEqual(len(run["vias"]), 1)
        v = run["vias"][0]
        self.assertEqual(v["via_id"], "n1-V01")
        self.assertEqual(v["parent_id"], "n1-S01")
        self.assertEqual(v["net_id"], "n1")
        self.assertEqual(v["drill_mm"], 0.3)
        self.assertEqual(v["annular_ring_mm"], 0.15)
        self.assertEqual(v["state"], "candidate")
        self.assertEqual(v["source"], "solver")

    def test_layer_preference_that_forbids_the_pad_layer_fails(self):
        board = _fixture("fixture_via.json")
        req = {"route_order": ["n1"],
               "layer_preferences": [{"net_id": "n1", "layers": ["B.Cu"]}]}
        run = router.solve_board(board, req)
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run.get("failed_at"), "n1")
        self.assertEqual(run["routes"], [])


class TestClockLayerPermission(unittest.TestCase):
    """clock class may only use F.Cu: when F.Cu is fully blocked the net
    must fail, never sneak onto B.Cu."""

    def test_blocked_f_cu_clock_net_fails(self):
        board = _fixture("fixture_clock_blocked.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run.get("failed_at"), "n1")
        self.assertEqual(run["routes"], [])
        self.assertEqual(run["vias"], [])
        self.assertEqual(run["metrics"]["unconnected"], 1)
        self.assertFalse(run["metrics"]["all_connected"])
        for r in run["routes"]:  # nothing emitted, in particular no B.Cu
            self.assertNotEqual(r["layer"], "B.Cu")


class TestEnclosedBoard(unittest.TestCase):
    """f5-style: keepout ring on both layers seals one endpoint away."""

    def test_enclosed_net_fails(self):
        board = _fixture("fixture_enclosed.json")
        run = router.solve_board(board, {"route_order": ["n1"]})
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run.get("failed_at"), "n1")
        self.assertEqual(run["routes"], [])
        self.assertFalse(run["metrics"]["all_connected"])


class TestAlleyOrderSensitivity(unittest.TestCase):
    """Narrow-alley fixture: n1 first -> n2 failed; n2 first -> both sat.

    This asymmetry (the F.Cu-only clock net needs the crossing the greedy
    default net steals) is the physical basis of the E1 planning value.
    """

    def test_n1_first_fails_and_n2_first_succeeds(self):
        board = _fixture("fixture_alley.json")
        bad = router.solve_board(board, {"route_order": ["n1", "n2"]})
        self.assertEqual(bad["status"], "failed")
        self.assertEqual(bad.get("failed_at"), "n2")
        self.assertEqual(len(bad["routes"]), 1)  # n1 done, n2 stopped
        self.assertEqual(bad["metrics"]["unconnected"], 1)

        good = router.solve_board(board, {"route_order": ["n2", "n1"]})
        self.assertEqual(good["status"], "sat")
        # n1 must hop over the routed clock net on B.Cu: exactly 2 vias
        self.assertEqual(good["metrics"]["via_count"], 2)
        self.assertEqual(good["metrics"]["shorts"], 0)
        # hand computed: n2 = 19 mm straight, n1 = 11 mm + 2 vias
        self.assertEqual(good["metrics"]["total_length_mm"], 30.0)
        self.assertEqual(good["metrics"]["objective"], 46.0)
        self.assertNotEqual(bad["status"], good["status"])

    def test_two_routed_nets_keep_two_cell_separation(self):
        board = _fixture("fixture_alley.json")
        run = router.solve_board(board, {"route_order": ["n2", "n1"]})
        self.assertEqual(run["status"], "sat")
        self.assertEqual(run["metrics"]["shorts"], 0)
        world = grid.GridWorld(board)
        geom = grid.geometry_from_routes(world, run["routes"], run["vias"])
        # per-layer check: crossing on different layers is legal
        for li in (0, 1):
            cells_a = geom["n1"].get(li, set())
            cells_b = geom["n2"].get(li, set())
            if not cells_a or not cells_b:
                continue
            self.assertFalse(grid.separation_violation(cells_a, cells_b))
            min_dist = min(max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                           for a in cells_a for b in cells_b)
            self.assertGreaterEqual(min_dist, grid.MIN_CENTER_SEPARATION_CELLS)

    def test_determinism_byte_identical_runs(self):
        board = _fixture("fixture_alley.json")
        req = {"route_order": ["n2", "n1"]}
        a = router.solve_board(board, dict(req))
        b = router.solve_board(board, dict(req))
        self.assertEqual(grid.canonical_json(a), grid.canonical_json(b))
        self.assertEqual(a["actions_digest"], b["actions_digest"])
        self.assertEqual(a["route_manifest_sha256_at_run"],
                         b["route_manifest_sha256_at_run"])


class TestContractGuards(unittest.TestCase):
    def test_incomplete_route_order_rejected(self):
        board = _fixture("fixture_straight.json")
        with self.assertRaises(grid.V4ExpError):
            router.solve_board(board, {"route_order": []})

    def test_protected_net_must_come_first(self):
        board = _fixture("fixture_alley.json")
        with self.assertRaises(grid.V4ExpError):
            router.solve_board(board, {"route_order": ["n2", "n1"],
                                       "protected_net_ids": ["n1"]})


if __name__ == "__main__":
    unittest.main()
