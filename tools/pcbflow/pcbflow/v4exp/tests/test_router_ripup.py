"""Self-tests for the pcbflow.v4exp router ripup-and-reroute (V4-RIPUP-R1 v1).

prereg-v4-ripup-r1.md §1.3 (rev1): the run JSON carries actions only as an
actions_digest, so run-level assertions use metrics.ripup_count / status /
failed_at; the audit structure (candidates_tried / ripped / attempts) is
asserted directly on router._ripup_attempt return values.
"""

import json
import os
import sys
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


class TestRipupAlley(unittest.TestCase):
    """fixture_alley: order [n1, n2] fails; ripup must tear up n1, route n2,
    re-route n1 over B.Cu -- matching the good order's metrics exactly."""

    def test_t1_ripup_recovers_alley(self):
        board = _fixture("fixture_alley.json")
        bad = router.solve_board(board, {"route_order": ["n1", "n2"]})
        self.assertEqual(bad["status"], "failed")
        self.assertEqual(bad["metrics"]["ripup_count"], 0)

        rip = router.solve_board(board, {"route_order": ["n1", "n2"],
                                         "ripup": True})
        good = router.solve_board(board, {"route_order": ["n2", "n1"]})
        self.assertEqual(rip["status"], "sat")
        self.assertEqual(rip["metrics"]["ripup_count"], 1)
        self.assertEqual(rip["metrics"]["via_count"], 2)
        self.assertEqual(rip["metrics"]["total_length_mm"], 30.0)
        self.assertEqual(rip["metrics"]["objective"], 46.0)
        self.assertEqual(rip["metrics"]["objective"], good["metrics"]["objective"])
        self.assertEqual(rip["metrics"]["via_count"], good["metrics"]["via_count"])
        self.assertEqual(rip["metrics"]["total_length_mm"],
                         good["metrics"]["total_length_mm"])
        self.assertEqual(rip["metrics"]["shorts"], 0)

    def test_t1_audit_structure_on_attempt(self):
        board = _fixture("fixture_alley.json")
        world = grid.GridWorld(board)
        state = router.RoutedState()
        res = router._route_single_net(world, state, "n1", None, None)
        self.assertTrue(res["ok"])
        state.add_net("n1", res["cells"])
        att = router._ripup_attempt(world, state, ["n1", "n2"], 1, "n2",
                                    {}, {}, set(), res["routes"], res["vias"])
        self.assertTrue(att["ok"])
        self.assertEqual(att["ripped"], ["n1"])
        self.assertEqual(att["actions"][0]["status"], "ok")
        self.assertEqual(att["actions"][0]["op"], "ripup")
        self.assertEqual(att["actions"][0]["net_id"], "n2")
        self.assertEqual(att["actions"][0]["candidates_tried"], ["n1"])
        self.assertEqual(att["actions"][0]["attempts"], 1)
        # state keeps both nets afterwards
        self.assertIn("n1", state.cells)
        self.assertIn("n2", state.cells)

    def test_t2_default_equals_explicit_false(self):
        board = _fixture("fixture_alley.json")
        a = router.solve_board(board, {"route_order": ["n1", "n2"]})
        b = router.solve_board(board, {"route_order": ["n1", "n2"],
                                       "ripup": False})
        self.assertEqual(router.canonical_json(a), router.canonical_json(b))

    def test_t3_sat_world_untouched_by_ripup(self):
        board = _fixture("fixture_alley.json")
        a = router.solve_board(board, {"route_order": ["n2", "n1"]})
        b = router.solve_board(board, {"route_order": ["n2", "n1"],
                                       "ripup": True})
        self.assertEqual(router.canonical_json(a), router.canonical_json(b))

    def test_t4_protected_nets_excluded(self):
        board = _fixture("fixture_alley.json")
        rip = router.solve_board(board, {"route_order": ["n1", "n2"],
                                         "ripup": True,
                                         "protected_net_ids": ["n1"]})
        self.assertEqual(rip["status"], "failed")
        self.assertEqual(rip.get("failed_at"), "n2")
        self.assertEqual(rip["metrics"]["ripup_count"], 0)
        world = grid.GridWorld(board)
        state = router.RoutedState()
        res = router._route_single_net(world, state, "n1", None, None)
        state.add_net("n1", res["cells"])
        att = router._ripup_attempt(world, state, ["n1", "n2"], 1, "n2",
                                    {}, {}, {"n1"}, res["routes"], res["vias"])
        self.assertFalse(att["ok"])
        self.assertEqual(att["actions"][0]["status"], "failed")
        self.assertEqual(att["actions"][0]["candidates_tried"], [])
        self.assertEqual(att["actions"][0]["attempts"], 0)

    def test_t6_ripup_deterministic_double_run(self):
        board = _fixture("fixture_alley.json")
        a = router.solve_board(board, {"route_order": ["n1", "n2"],
                                       "ripup": True})
        b = router.solve_board(board, {"route_order": ["n1", "n2"],
                                       "ripup": True})
        self.assertEqual(router.canonical_json(a), router.canonical_json(b))

    def test_non_bool_ripup_fails_closed(self):
        board = _fixture("fixture_alley.json")
        with self.assertRaises(router.V4ExpError):
            router.solve_board(board, {"route_order": ["n2", "n1"],
                                       "ripup": "yes"})


class TestRipupStaticAndRollback(unittest.TestCase):
    """No-candidate and rollback paths keep the failed shape intact."""

    def test_t5_enclosed_first_net_no_candidates(self):
        board = _fixture("fixture_enclosed.json")
        base = router.solve_board(board, {"route_order": ["n1"]})
        rip = router.solve_board(board, {"route_order": ["n1"], "ripup": True})
        self.assertEqual(rip["status"], "failed")
        self.assertEqual(rip.get("failed_at"), "n1")
        self.assertEqual(rip["metrics"]["ripup_count"], 0)
        m_base = dict(base["metrics"])
        m_rip = dict(rip["metrics"])
        m_base.pop("search_nodes")
        m_rip.pop("search_nodes")
        self.assertEqual(m_base, m_rip)
        world = grid.GridWorld(board)
        att = router._ripup_attempt(world, router.RoutedState(),
                                    ["n1"], 0, "n1", {}, {}, set(), [], [])
        self.assertFalse(att["ok"])
        self.assertEqual(att["actions"][0]["status"], "failed")
        self.assertEqual(att["actions"][0]["candidates_tried"], [])

    def test_t7_rollback_leaves_no_trace(self):
        board = _fixture("fixture_ripup_rollback.json")
        base = router.solve_board(board, {"route_order": ["n1", "n2"]})
        self.assertEqual(base["status"], "failed")
        self.assertEqual(base.get("failed_at"), "n2")
        rip = router.solve_board(board, {"route_order": ["n1", "n2"],
                                         "ripup": True})
        # rollback: identical emitted geometry and metrics (search_nodes
        # legitimately grows: the scans and the aborted attempt expanded).
        self.assertEqual(rip["status"], "failed")
        self.assertEqual(rip.get("failed_at"), base.get("failed_at"))
        self.assertEqual(rip["routes"], base["routes"])
        self.assertEqual(rip["vias"], base["vias"])
        self.assertEqual(rip["metrics"]["ripup_count"], 0)
        m_base = dict(base["metrics"])
        m_rip = dict(rip["metrics"])
        m_base.pop("search_nodes")
        m_rip.pop("search_nodes")
        self.assertEqual(m_base, m_rip)
        # audit: the only true blocker was tried, the re-route step failed,
        # everything was rolled back.
        world = grid.GridWorld(board)
        state = router.RoutedState()
        res = router._route_single_net(world, state, "n1", None, None)
        self.assertTrue(res["ok"])
        state.add_net("n1", res["cells"])
        att = router._ripup_attempt(world, state, ["n1", "n2"], 1, "n2",
                                    {}, {}, set(), res["routes"], res["vias"])
        self.assertFalse(att["ok"])
        self.assertEqual(att["actions"][0]["status"], "failed")
        self.assertEqual(att["actions"][0]["ripped"], [])
        self.assertEqual(att["actions"][0]["candidates_tried"], ["n1"])
        self.assertEqual(att["actions"][0]["attempts"], 1)
        # state rolled back to exactly the pre-attempt geometry
        self.assertEqual(sorted(state.cells), ["n1"])


if __name__ == "__main__":
    unittest.main()
