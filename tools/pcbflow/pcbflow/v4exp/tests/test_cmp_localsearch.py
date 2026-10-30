"""cmp_localsearch 单测：确定性、预算封顶、base 不变、贪心改善、重放一致。"""

import copy
import unittest

from pcbflow.v4exp import cmp_localsearch, cmp_patch, cmp_scenarios, router
from pcbflow.v4exp.grid import GridWorld

SIDS = ("dev-f1-01", "dev-f1-03", "dev-f3-02")


def setup(sid):
    board = cmp_scenarios.generate_scenario(sid)
    run = router.solve_board(board,
                             {"route_order": sorted(n["net_id"]
                                                    for n in board["nets"]),
                              "group": "A"})
    geom = {"routes": copy.deepcopy(run["routes"]),
            "vias": copy.deepcopy(run["vias"])}
    return board, run, geom, GridWorld(board)


class TestLocalSearch(unittest.TestCase):
    def test_budget_capped_and_base_unchanged(self):
        for sid in SIDS:
            board, run, geom, world = setup(sid)
            snapshot = copy.deepcopy(geom)
            res = cmp_localsearch.run_local_search(world, board, geom,
                                                   max_proposals=8)
            self.assertLessEqual(res["evaluations"], 8)
            self.assertEqual(len(res["proposals"]), res["evaluations"])
            # 输入几何不得被就地修改
            self.assertEqual(cmp_patch.candidate_geometry_sha256(geom),
                             cmp_patch.candidate_geometry_sha256(snapshot))

    def test_deterministic_double_run(self):
        for sid in SIDS:
            board, run, geom, world = setup(sid)
            r1 = cmp_localsearch.run_local_search(world, board, geom, 8)
            r2 = cmp_localsearch.run_local_search(world, board, geom, 8)
            self.assertEqual(r1["final_geometry_sha256"],
                             r2["final_geometry_sha256"])
            self.assertEqual(r1["proposals"], r2["proposals"])

    def test_accepted_only_when_strictly_improved(self):
        for sid in SIDS:
            board, run, geom, world = setup(sid)
            res = cmp_localsearch.run_local_search(world, board, geom, 8)
            if res["accepted_count"] == 0:
                self.assertAlmostEqual(res["final_metrics"]["objective"],
                                       res["base_metrics"]["objective"], 9)
            else:
                self.assertLess(res["final_metrics"]["objective"],
                                res["base_metrics"]["objective"])
            for p in res["proposals"]:
                if p["accepted"]:
                    self.assertLess(p["candidate_objective"],
                                    res["base_metrics"]["objective"])
                self.assertFalse(p["corrected_by_solver"])

    def test_final_geometry_is_legal(self):
        for sid in SIDS:
            board, run, geom, world = setup(sid)
            res = cmp_localsearch.run_local_search(world, board, geom, 8)
            m = res["final_metrics"]
            if m["objective"] > 0 or run["status"] == "sat":
                self.assertEqual(sum(m["violations"].values()), 0, sid)
                self.assertEqual(m["unconnected"], 0, sid)

    def test_proposals_are_patch_schema(self):
        board, run, geom, world = setup("dev-f1-01")
        n = 0
        for patch in cmp_localsearch.proposal_stream(world, board, geom):
            self.assertEqual(patch["schema_version"],
                             cmp_patch.PATCH_SCHEMA)
            self.assertEqual(patch["source"], "deterministic-search")
            self.assertEqual(patch["base_candidate_geometry_sha256"],
                             cmp_patch.candidate_geometry_sha256(geom))
            self.assertIn(patch["action_type"], cmp_patch.ACTION_TYPES)
            n += 1
            if n >= 200:
                break
        self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
