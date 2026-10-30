# -*- coding: utf-8 -*-
"""clearance 几何原语：含对抗几何（擦边、端点焊盘冲突、共线、退化）。"""
import pytest

from v5.metrics import clearance as cl


def test_point_point():
    assert cl.point_point((0, 0), (3, 4)) == pytest.approx(5.0)


def test_point_segment_interior():
    assert cl.point_segment((1, 1), (0, 0), (2, 0)) == pytest.approx(1.0)


def test_point_segment_beyond_end():
    assert cl.point_segment((3, 0), (0, 0), (2, 0)) == pytest.approx(1.0)


def test_point_segment_degenerate():
    assert cl.point_segment((0, 2), (0, 0), (0, 0)) == pytest.approx(2.0)


def test_parallel_segments_distance():
    assert cl.segment_segment((0, 0), (4, 0), (0, 1), (4, 1)) == pytest.approx(1.0)


def test_collinear_overlap_zero():
    assert cl.segment_segment((0, 0), (4, 0), (2, 0), (6, 0)) == 0.0


def test_endpoint_touch_zero():
    assert cl.segment_segment((0, 0), (2, 0), (2, 0), (2, 2)) == 0.0


def test_perpendicular_distance():
    assert cl.segment_segment((0, 5), (10, 5), (5, 0), (5, 2)) == pytest.approx(3.0)


def test_diagonal_cross_zero():
    assert cl.segment_segment((0, 0), (4, 4), (0, 4), (4, 0)) == 0.0


def test_擦边_exact_clearance_is_not_negative():
    """对抗：0.5 间距擦边——距离恰等于阈值是可判定的（判违规与否在 v5.drc）。"""
    gap = cl.segment_segment((0, 0), (10, 0), (0, 0.5), (10, 0.5))
    assert gap == pytest.approx(0.5)
    gap2 = cl.segment_segment((0, 0), (10, 0), (0, 0.4999999999), (10, 0.4999999999))
    assert gap2 < 0.5


def test_pad_pad_touching():
    assert cl.pad_pad_distance((0, 0), 0.15, (0.3, 0), 0.15) == pytest.approx(0.0)


def test_pad_pad_overlap_clamped():
    assert cl.pad_pad_distance((0, 0), 0.15, (0.1, 0), 0.15) == 0.0


def test_pad_pad_gap():
    assert cl.pad_pad_distance((0, 0), 0.15, (1.0, 0), 0.15) == pytest.approx(0.7)


def test_pad_segment_touch():
    assert cl.pad_segment_distance((0, 0.15), 0.15, (-1, 0), (1, 0)) == pytest.approx(0.0)


def test_pad_segment_endpoint_conflict_geometry():
    """对抗：端点焊盘撞既布铜带（V2 P3 上端点 vs P9 场景）。"""
    gap = cl.pad_segment_distance((16.0, 36.0), 0.15, (2.0, 36.1), (44.0, 36.1))
    assert gap == pytest.approx(0.0)  # 焊盘圆与铜带相交


def test_pad_rect_inside_zero():
    r = {"x_min": 0, "y_min": 0, "x_max": 10, "y_max": 10}
    assert cl.pad_rect_distance((5, 5), 0.15, r) == 0.0


def test_pad_rect_outside():
    r = {"x_min": 0, "y_min": 0, "x_max": 10, "y_max": 10}
    assert cl.pad_rect_distance((11.65, 5), 0.15, r) == pytest.approx(1.5)


def test_rect_rect_gap_diagonal():
    assert cl.rect_rect_gap((0, 0, 1, 1), (2, 2, 3, 3)) == pytest.approx(2 ** 0.5)


def test_rect_rect_axis_gap():
    assert cl.rect_rect_gap((0, 0, 1, 1), (1.5, 0, 2, 1)) == pytest.approx(0.5)


def test_rect_rect_overlap_zero():
    assert cl.rect_rect_gap((0, 0, 2, 2), (1, 1, 3, 3)) == 0.0


def test_segment_rect_distance():
    r = {"x_min": 0, "y_min": 10, "x_max": 10, "y_max": 12}
    assert cl.segment_rect_distance((5, 0), (5, 9), r) == pytest.approx(1.0)


def test_polyline_polyline_min():
    a = [(0, 0), (10, 0)]
    b = [(0, 2), (5, 2), (10, 3)]
    assert cl.polyline_polyline(a, b) == pytest.approx(2.0)


def test_parallel_overlap_same_axis():
    assert cl.parallel_overlap_length((0, 0), (0, 7), (0, 2), (0, 9), "y") == pytest.approx(5.0)


def test_parallel_overlap_disjoint():
    assert cl.parallel_overlap_length((0, 0), (0, 2), (0, 5), (0, 9), "y") == 0.0


def test_determinism_double_run():
    args = ((0.3, 0.7), (4.1, 4.2), (0.0, 3.0), (7.0, -1.0))
    assert cl.segment_segment(*args) == cl.segment_segment(*args)
