# -*- coding: utf-8 -*-
"""width_prior 宽度先验：载流下限、工艺下限、5% 封顶、区间零罚、瓶颈。"""
import pytest

from v5.metrics import width_prior as wp


def test_current_min_floor_dominates():
    assert wp.current_min_width(0.5) == pytest.approx(0.3)  # 0.4×0.5=0.2 < 0.3


def test_current_min_k_dominates():
    assert wp.current_min_width(2.0) == pytest.approx(0.8)  # 0.4×2=0.8


def test_current_min_zero_current():
    assert wp.current_min_width(0.0) == pytest.approx(0.3)


def test_current_min_negative_rejected():
    with pytest.raises(ValueError):
        wp.current_min_width(-1.0)


def test_conservative_min_fab_dominates():
    assert wp.conservative_min_width(0.5, fab_min_mm=0.5) == pytest.approx(0.5)


def test_conservative_min_current_dominates():
    assert wp.conservative_min_width(3.0, fab_min_mm=0.2) == pytest.approx(1.2)


def test_v2_p8_r1_min():
    """V2 播种缺陷 D1：P8 2.0A → R1 下限 0.8，计划 0.5 违例。"""
    assert wp.conservative_min_width(2.0, 0.0) == pytest.approx(0.8)
    assert wp.in_interval(0.5, 0.8, 1.6) is False


def test_v2_p1_interval():
    assert wp.in_interval(1.2, 0.6, 1.4)
    assert wp.in_interval(0.6, 0.6, 1.4)  # 擦边含边界
    assert not wp.in_interval(1.5, 0.6, 1.4)


def test_adjustment_penalty_zero_inside():
    assert wp.adjustment_penalty(1.0, 0.6, 1.4) == 0.0


def test_adjustment_penalty_inf_outside():
    assert wp.adjustment_penalty(0.1, 0.6, 1.4) == float("inf")


def test_improvement_curve_monotonic():
    small = wp.improvement_curve(0.6, 0.6, 1.0)
    big = wp.improvement_curve(1.4, 0.6, 1.0)
    assert big > small >= 0.0


def test_improvement_curve_exact_5pct():
    w = wp.significant_max_width(0.6, 1.0, threshold=0.05)
    assert wp.improvement_curve(w, 0.6, 1.0) == pytest.approx(0.05)


def test_significant_max_width_formula():
    assert wp.significant_max_width(1.0, 1.0) == pytest.approx(1.0 / 0.95)


def test_significant_max_invalid_threshold():
    with pytest.raises(ValueError):
        wp.significant_max_width(1.0, 1.0, threshold=1.0)


def test_bottleneck_v2_p1():
    """V2 J4：P1 计划 1.2、瓶颈可用 1.0 → 放不下但可收窄至 [0.6,1.0]。"""
    v = wp.bottleneck_verdict(1.2, 1.0, 0.6)
    assert not v["fits_as_planned"]
    assert v["narrowable"]
    assert v["narrow_floor"] == pytest.approx(0.6)


def test_bottleneck_not_narrowable():
    v = wp.bottleneck_verdict(1.2, 0.5, 0.6)
    assert not v["narrowable"]


def test_bottleneck_fits_as_planned():
    v = wp.bottleneck_verdict(0.9, 1.0, 0.6)
    assert v["fits_as_planned"]
