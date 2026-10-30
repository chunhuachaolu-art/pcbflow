"""cmp_patch 单测：独立指标口径、fail-closed 拦截、apply/rollback、响应校验。"""

import copy
import unittest

from pcbflow.v4exp import cmp_patch, cmp_scenarios, router
from pcbflow.v4exp.grid import GridWorld


def solve(scenario_id, order=None):
    board = cmp_scenarios.generate_scenario(scenario_id)
    if order is None:
        order = sorted(n["net_id"] for n in board["nets"])
    run = router.solve_board(board, {"route_order": order, "group": "A"})
    return board, run


def make_patch(board, geom, route, action="move_vertex", **over):
    ident = cmp_patch.route_identity(board, route)
    p = {
        "schema_version": cmp_patch.PATCH_SCHEMA,
        "action_type": action,
        "base_candidate_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(geom),
        "scenario_id": board["scenario_id"],
        "route_id": route["route_id"],
        "net_id": route["net_id"],
        "relation_id": ident["relation_ids"][0] if ident["relation_ids"] else None,
        "parent_id": None,
        "fixed_endpoint_ids": list(route["endpoint_ids"]),
        "reason": "test patch",
        "source": "program",
    }
    p.update(over)
    return p


class TestMetricsEquivalence(unittest.TestCase):
    """cmp_metrics 必须与 router._compute_metrics 对无后缀候选逐字段一致。"""

    def test_matches_router_on_real_runs(self):
        for sid in ("dev-f1-01", "dev-f3-02", "dev-f4-03"):
            board, run = solve(sid)
            world = GridWorld(board)
            mine = cmp_patch.cmp_metrics(world, run["routes"], run["vias"])
            theirs = run["metrics"]
            for k in ("all_connected", "shorts", "unconnected",
                      "violations", "total_length_mm", "via_count",
                      "bend_count", "max_congestion_overlap_cells",
                      "objective"):
                if k in ("total_length_mm", "objective"):
                    self.assertAlmostEqual(mine[k], theirs[k], 6,
                                           "%s/%s" % (sid, k))
                else:
                    self.assertEqual(mine[k], theirs[k], "%s/%s" % (sid, k))

    def test_malformed_input_fails_closed(self):
        board, run = solve("dev-f1-01")
        world = GridWorld(board)
        bad = copy.deepcopy(run["routes"])
        bad[0]["polyline_mm"] = [[float("nan"), 1.0], [2.0, 2.0]]
        out = cmp_patch.cmp_metrics(world, bad, run["vias"])
        self.assertFalse(out["all_connected"])
        self.assertGreater(sum(out["violations"].values()), 0)


class TestStructureAndIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.solver_run = solve("dev-f1-01")
        cls.geom = {"routes": copy.deepcopy(cls.solver_run["routes"]),
                    "vias": copy.deepcopy(cls.solver_run["vias"])}
        cls.world = GridWorld(cls.board)
        cls.route = cls.geom["routes"][0]

    def v(self, patch):
        return cmp_patch.validate_patch(self.world, self.board, patch,
                                        self.geom)

    def test_stale_base_hash_rejected(self):
        p = make_patch(self.board, self.geom, self.route)
        p["base_candidate_geometry_sha256"] = "0" * 64
        self.assertFalse(self.v(p)["legal"])

    def test_unknown_route_rejected(self):
        p = make_patch(self.board, self.geom, self.route, route_id="n9-S99")
        self.assertFalse(self.v(p)["legal"])

    def test_unknown_key_rejected(self):
        p = make_patch(self.board, self.geom, self.route, evil_field=1)
        self.assertFalse(self.v(p)["legal"])

    def test_missing_identity_key_rejected(self):
        p = make_patch(self.board, self.geom, self.route)
        del p["relation_id"]
        self.assertFalse(self.v(p)["legal"])

    def test_endpoint_move_rejected(self):
        base = self.route["polyline_mm"]
        poly = [list(p) for p in base]
        poly[0] = [poly[0][0] + 0.25, poly[0][1]]
        p = make_patch(self.board, self.geom, self.route,
                       polyline_mm=poly, layer=self.route["layer"],
                       width_mm=self.route["width_mm"])
        self.assertFalse(self.v(p)["legal"])

    def test_wrong_layer_rejected(self):
        p = make_patch(self.board, self.geom, self.route,
                       polyline_mm=self.route["polyline_mm"],
                       layer="B.Cu", width_mm=self.route["width_mm"])
        self.assertFalse(self.v(p)["legal"])

    def test_wrong_width_rejected(self):
        p = make_patch(self.board, self.geom, self.route,
                       polyline_mm=self.route["polyline_mm"],
                       layer=self.route["layer"], width_mm=0.5)
        self.assertFalse(self.v(p)["legal"])

    def test_off_grid_rejected(self):
        base = self.route["polyline_mm"]
        poly = [list(p) for p in base]
        poly[1] = [poly[1][0] + 0.1, poly[1][1]]
        p = make_patch(self.board, self.geom, self.route,
                       polyline_mm=poly, layer=self.route["layer"],
                       width_mm=self.route["width_mm"])
        self.assertFalse(self.v(p)["legal"])

    def test_nan_rejected_without_crash(self):
        p = make_patch(self.board, self.geom, self.route,
                       polyline_mm=[[float("nan"), 1.0], [2.0, 2.0]],
                       layer=self.route["layer"],
                       width_mm=self.route["width_mm"])
        out = self.v(p)
        self.assertFalse(out["legal"])

    def test_reject_requires_bound_identity(self):
        ok = make_patch(self.board, self.geom, self.route,
                        action="reject_route_patch")
        self.assertTrue(self.v(ok)["legal"])
        stale = dict(ok)
        stale["base_candidate_geometry_sha256"] = "0" * 64
        self.assertFalse(self.v(stale)["legal"])


class TestApplyRollbackAndUndeclared(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.solver_run = solve("dev-f2-05")
        cls.geom = {"routes": copy.deepcopy(cls.solver_run["routes"]),
                    "vias": copy.deepcopy(cls.solver_run["vias"])}
        cls.world = GridWorld(cls.board)

    def _scan_legal_move(self):
        """八方向扫描：返回第一个合法 move_vertex patch 或 None。"""
        routes = sorted(self.geom["routes"], key=lambda r: str(r["route_id"]))
        for route in routes:
            poly = route["polyline_mm"]
            for i in range(1, len(poly) - 1):
                for k in (1, 2, 3):
                    for dx, dy in ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                                   (0, 1), (1, -1), (1, 0), (1, 1)):
                        newpoly = [list(p) for p in poly]
                        newpoly[i] = [round(newpoly[i][0] + 0.25 * k * dx, 3),
                                      round(newpoly[i][1] + 0.25 * k * dy, 3)]
                        if newpoly[i] == list(poly[i]):
                            continue
                        p = make_patch(self.board, self.geom, route,
                                       polyline_mm=newpoly,
                                       layer=route["layer"],
                                       width_mm=route["width_mm"])
                        out = cmp_patch.validate_patch(self.world, self.board,
                                                       p, self.geom)
                        if out["legal"]:
                            return p, out
        return None, None

    def test_legal_patch_applies_rolls_back_and_preserves_undeclared(self):
        patch, res = self._scan_legal_move()
        self.assertIsNotNone(patch, "八方向扫描应至少找到一个合法 move_vertex")
        applied = cmp_patch.apply_and_check(self.world, self.board, patch,
                                            self.geom)
        self.assertTrue(applied["legal"])
        new_geom = applied["geometry"]
        # 未声明对象逐字节不变
        base_by_id = {str(r["route_id"]): r for r in self.geom["routes"]}
        for r in new_geom["routes"]:
            rid = str(r["route_id"])
            if rid == str(patch["route_id"]):
                continue
            self.assertEqual(r, base_by_id[rid], rid)
        self.assertEqual(new_geom["vias"], self.geom["vias"])
        # rollback 恢复逐字节一致
        restored = cmp_patch.rollback_patch(new_geom, applied["rollback"])
        self.assertEqual(cmp_patch.candidate_geometry_sha256(restored),
                         cmp_patch.candidate_geometry_sha256(self.geom))
        # 新几何 metrics 合法
        m = cmp_patch.cmp_metrics(self.world, new_geom["routes"],
                                  new_geom["vias"])
        self.assertEqual(sum(m["violations"].values()), 0)
        self.assertTrue(m["all_connected"])

    def test_apply_rejects_illegal_patch(self):
        bad = make_patch(self.board, self.geom, self.geom["routes"][0],
                         polyline_mm=[[0.0, 0.0], [1.0, 1.0]],
                         layer="F.Cu", width_mm=0.3)
        with self.assertRaises(ValueError):
            cmp_patch.apply_patch(self.world, self.board, bad, self.geom)

    def test_validation_deterministic(self):
        patch, _ = self._scan_legal_move()
        self.assertIsNotNone(patch)
        r1 = cmp_patch.validate_patch(self.world, self.board, patch, self.geom)
        r2 = cmp_patch.validate_patch(self.world, self.board, patch, self.geom)
        self.assertEqual(r1["legal"], r2["legal"])
        self.assertEqual(r1["reasons"], r2["reasons"])


class TestResponseValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board, cls.solver_run = solve("dev-f1-01")

    def resp(self, **over):
        r = {"schema": cmp_patch.RESPONSE_SCHEMA,
             "scenario_id": self.board["scenario_id"],
             "board_snapshot_sha256":
                 __import__("pcbflow.v4exp.model", fromlist=["model"])
                 .sha256_of(self.board),
             "arm": "C1", "round": 1, "patches": [], "notes": "",
             "uncertainty": "low"}
        r.update(over)
        return r

    def test_valid_empty_response(self):
        out = cmp_patch.validate_response(self.resp(), self.board, "C1", 1)
        self.assertFalse(out["blocked"])

    def test_wrong_arm_blocked(self):
        out = cmp_patch.validate_response(self.resp(arm="B1"), self.board,
                                          "C1", 1)
        self.assertTrue(out["blocked"])

    def test_unknown_root_key_blocked(self):
        out = cmp_patch.validate_response(self.resp(extra=1), self.board,
                                          "C1", 1)
        self.assertTrue(out["blocked"])

    def test_excess_patches_truncated_with_rejection(self):
        patches = [make_patch(self.board,
                              {"routes": self.solver_run["routes"],
                               "vias": self.solver_run["vias"]},
                              self.solver_run["routes"][0]) for _ in range(6)]
        out = cmp_patch.validate_response(self.resp(patches=patches),
                                          self.board, "C1", 1)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["accepted_patches"]),
                         cmp_patch.MAX_PATCHES_PER_CALL)
        self.assertEqual(len(out["rejections"]), 2)


if __name__ == "__main__":
    unittest.main()
