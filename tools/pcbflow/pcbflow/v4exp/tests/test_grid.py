"""Unit tests for pcbflow.v4exp.grid (lattice world)."""

import json
import os
import sys
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_TESTS_DIR)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pcbflow.v4exp import grid  # noqa: E402


def _fixture(name):
    path = os.path.join(_TESTS_DIR, "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestFrozenConstants(unittest.TestCase):
    def test_grid_and_separation_constants(self):
        self.assertEqual(grid.GRID_MM, 0.25)
        self.assertEqual(grid.MIN_CENTER_SEPARATION_CELLS, 2)
        self.assertEqual(grid.DILATION_RADIUS_CELLS,
                         grid.MIN_CENTER_SEPARATION_CELLS - 1)
        self.assertEqual(grid.VIA_FOOTPRINT_RADIUS_CELLS, 1)


class TestWorkspace(unittest.TestCase):
    def test_dimensions_and_walls(self):
        world = grid.GridWorld(_fixture("fixture_straight.json"))
        # board 20x12 mm + 2 mm margin all around -> 24x16 mm -> 97x65 cells
        self.assertEqual((world.nx, world.ny), (97, 65))
        self.assertEqual(world.cell_x(-2.0), 0)
        self.assertEqual(world.cell_y(-2.0), 0)
        self.assertEqual(world.cell_x(22.0), world.nx - 1)
        self.assertEqual(world.cell_y(14.0), world.ny - 1)
        self.assertFalse(world.in_bounds(-1, 0))
        self.assertFalse(world.in_bounds(0, -1))
        self.assertFalse(world.in_bounds(world.nx, 0))
        self.assertFalse(world.in_bounds(0, world.ny))

    def test_mm_cell_roundtrip_on_grid_points(self):
        world = grid.GridWorld(_fixture("fixture_straight.json"))
        for mm in (0.0, 5.0, 6.25, 15.0, 20.0):
            self.assertAlmostEqual(world.center_mm_x(world.cell_x(mm)), mm)
            self.assertAlmostEqual(world.center_mm_y(world.cell_y(mm)), mm)


class TestObstacles(unittest.TestCase):
    def test_own_pads_are_not_obstacles(self):
        world = grid.GridWorld(_fixture("fixture_straight.json"))
        blocked = world.static_blocked_for_net("n1")
        self.assertEqual(blocked[0], set())  # no other pads, no keepouts
        self.assertEqual(blocked[1], set())

    def test_keepout_blocks_per_layer(self):
        world = grid.GridWorld(_fixture("fixture_enclosed.json"))
        blocked = world.static_blocked_for_net("n1")
        inside = (world.cell_x(6.0), world.cell_y(6.0))    # inside the ring
        ring = (world.cell_x(4.5), world.cell_y(6.0))      # on the west ring
        outside = (world.cell_x(15.0), world.cell_y(6.0))  # pad side
        self.assertNotIn(inside, blocked[0])
        self.assertNotIn(outside, blocked[0])
        self.assertIn(ring, blocked[0])
        self.assertIn(ring, blocked[1])  # ring keepout is on both layers

    def test_keepout_can_block_everything_on_one_layer(self):
        world = grid.GridWorld(_fixture("fixture_clock_blocked.json"))
        blocked = world.static_blocked_for_net("n1")
        self.assertEqual(len(blocked[0]), world.nx * world.ny)  # F.Cu sealed
        self.assertEqual(blocked[1], set())                     # B.Cu untouched

    def test_other_net_pad_blocks_but_own_does_not(self):
        board = _fixture("fixture_alley.json")
        world = grid.GridWorld(board)
        blocked_for_n2 = world.static_blocked_for_net("n2")
        pad_n1_cell = (world.cell_x(10.0), world.cell_y(0.5))
        self.assertIn(pad_n1_cell, blocked_for_n2[0])
        blocked_for_n1 = world.static_blocked_for_net("n1")
        self.assertNotIn(pad_n1_cell, blocked_for_n1[0])


class TestSeparationRule(unittest.TestCase):
    def test_two_cells_distance_two_is_legal(self):
        self.assertFalse(grid.separation_violation({(0, 0)}, {(2, 0)}))
        self.assertFalse(grid.separation_violation({(0, 0)}, {(0, 2)}))
        self.assertFalse(grid.separation_violation({(5, 5)}, {(7, 6)}))

    def test_distance_one_is_violation(self):
        self.assertTrue(grid.separation_violation({(0, 0)}, {(1, 0)}))
        self.assertTrue(grid.separation_violation({(0, 0)}, {(1, 1)}))
        self.assertTrue(grid.separation_violation({(0, 0)}, {(0, 0)}))

    def test_empty_geometry_never_violates(self):
        self.assertFalse(grid.separation_violation(set(), {(1, 0)}))
        self.assertFalse(grid.separation_violation({(1, 0)}, set()))


class TestRoutedState(unittest.TestCase):
    def test_blocked_from_others_excludes_self(self):
        state = grid.RoutedState()
        state.add_net("a", {0: {(10, 10)}})
        state.add_net("b", {1: {(0, 0)}})
        blocked_for_a = state.blocked_from_others("a")
        self.assertIn((1, 1), blocked_for_a[1])    # dilated b geometry
        self.assertNotIn((1, 1), blocked_for_a.get(0, set()))
        self.assertNotIn((10, 10), blocked_for_a.get(0, set()))
        blocked_for_b = state.blocked_from_others("b")
        self.assertIn((10, 10), blocked_for_b[0])  # dilated a geometry
        self.assertNotIn((10, 10), blocked_for_b.get(1, set()))
        self.assertNotIn((0, 0), blocked_for_b.get(1, set()))


if __name__ == "__main__":
    unittest.main()
