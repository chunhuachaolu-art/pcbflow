# -*- coding: utf-8 -*-
"""宽度先验度量（P0 四模块之一；任务书 §3.3 用户原始规格落地）。

- 保守最小值 = max(载流下限 f(电流, 铜厚, 温升), 厂商工艺最小线宽)
- 无显著提升最大值 = 增量收益（压降/温升改善）< 5% 处封顶
- 区间内调整 0 罚
判定语义（R1 违例等）在 v5.drc。
"""
DEFAULT_K_PER_AMP = 0.4
DEFAULT_FLOOR_MM = 0.3
SIGNIFICANT_IMPROVEMENT = 0.05


def current_min_width(current_a, k_per_amp=DEFAULT_K_PER_AMP, floor_mm=DEFAULT_FLOOR_MM):
    """载流下限：R1 口径 max(k×电流, 地板)。current_a<0 非法。"""
    if current_a < 0:
        raise ValueError("电流不能为负: %r" % current_a)
    return max(k_per_amp * current_a, floor_mm)


def conservative_min_width(current_a, fab_min_mm, k_per_amp=DEFAULT_K_PER_AMP,
                           floor_mm=DEFAULT_FLOOR_MM):
    """保守最小值 = max(载流下限, 工艺最小)。"""
    return max(current_min_width(current_a, k_per_amp, floor_mm), fab_min_mm)


def improvement_curve(w, w_ref, r_ref):
    """简单压降改善模型：压降 ∝ 1/宽度。返回相对 w_ref 的压降降幅比例。

    r_ref = w_ref 下的单位电阻基准（Ω/mm 任意标度）。纯确定性。
    """
    if w <= 0:
        raise ValueError("宽度必须为正")
    r = r_ref * w_ref / w
    return (r_ref - r) / r_ref


def significant_max_width(w_ref, r_ref, threshold=SIGNIFICANT_IMPROVEMENT):
    """增量收益 < threshold 处封顶：解 1 − w_ref/w = threshold ⇒ w = w_ref/(1−threshold)。"""
    if not (0.0 <= threshold < 1.0):
        raise ValueError("threshold 须在 [0,1)")
    return w_ref / (1.0 - threshold)


def in_interval(w, w_min, w_max, tol=1e-9):
    """宽度是否在允许区间（含边界擦边）。区间内调整 0 罚。"""
    return (w_min - tol) <= w <= (w_max + tol)


def adjustment_penalty(w, w_min, w_max, tol=1e-9):
    """区间内调整 0 罚；区间外 = 无穷（不可行的宽度选择）。"""
    return 0.0 if in_interval(w, w_min, w_max, tol) else float("inf")


def bottleneck_verdict(planned_width, usable_width, w_min):
    """瓶颈段核算事实：可用宽是否容得下计划宽；计划宽最窄可收到 w_min。

    返回 dict；"必须收窄"的处置语义由上层（J 项生成/裁决）作出。
    """
    narrow_floor = max(w_min, 0.0)
    return {
        "planned_width": planned_width,
        "usable_width": usable_width,
        "fits_as_planned": planned_width <= usable_width + 1e-9,
        "narrow_floor": narrow_floor,
        "narrowable": narrow_floor <= usable_width + 1e-9,
    }
