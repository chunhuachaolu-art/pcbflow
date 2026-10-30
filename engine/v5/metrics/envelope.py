# -*- coding: utf-8 -*-
"""保守包络度量（P0 四模块之一）。

保守包络 = 实际铜几何向外扩 margin 的矩形（V2 场景口径 0.6mm）。
包络重叠 ≠ 实际冲突（外扩伪影）：本模块提供伪影判别原语（用实际几何复核），
判定语义仍在 v5.drc。
"""
from . import clearance


DEFAULT_MARGIN = 0.6


def expand_rect(rect, margin=DEFAULT_MARGIN):
    x0, y0, x1, y1 = rect
    return (x0 - margin, y0 - margin, x1 + margin, y1 + margin)


def segment_envelope(a, b, half_width, margin=DEFAULT_MARGIN):
    """线段铜的保守包络矩形（含半线宽与外扩）。"""
    x0, x1 = sorted((a[0], b[0]))
    y0, y1 = sorted((a[1], b[1]))
    grow = half_width + margin
    return (x0 - grow, y0 - grow, x1 + grow, y1 + grow)


def pad_envelope(center, radius, margin=DEFAULT_MARGIN):
    cx, cy = center
    grow = radius + margin
    return (cx - grow, cy - grow, cx + grow, cy + grow)


def envelopes_overlap(env_a, env_b):
    return clearance.rect_rect_gap(env_a, env_b) <= 0.0


def envelope_overlap_depth(env_a, env_b):
    """重叠深度（负值=间隙）；供包络叠加视图与冲突热区用。"""
    ax0, ay0, ax1, ay1 = env_a
    bx0, by0, bx1, by1 = env_b
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    return min(ox, oy)


def artifact_check(env_a, env_b, actual_gap, min_clearance=0.5):
    """外扩伪影判别：包络响警（重叠）但实际几何间距 ≥ min_clearance（真冲突不存在）。

    返回 (is_artifact, actual_gap)。纯度量事实，不构成违例判定。
    """
    return (envelopes_overlap(env_a, env_b) and actual_gap >= min_clearance - clearance.EPS,
            actual_gap)
