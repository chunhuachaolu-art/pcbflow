# -*- coding: utf-8 -*-
"""D-ORACLE-1 回归（V6-ANCHOR-R1 批内发现）: _actual_gap pad×polyline 分支
的 R1 性能剪枝原漏减 pad 半径——bbox 距 ∈ [best, best+r) 的更近段被误剪,
min 高估最多 r（违例漏判）。修复后剪枝须与逐段暴力逐位一致（性质测试）。"""
import random

from v5 import drc
from v5.drc import Copper
from v5.metrics import clearance as _cl


def _brute_pad_polyline(center, r, pts):
    return min(_cl.pad_segment_distance(center, r, tuple(a), tuple(b))
               for a, b in zip(pts[:-1], pts[1:]))


def test_oracle_prune_reproducer_d_oracle_1():
    """实锤复现形: leg1 真距 0.6 先立 best, near 腿 ps 距 1.0（真距 0.2）但
    bbox 距 1.0 ∈ [best, best+r) 被旧实现误剪（修复后须报 0.2）。"""
    pad = Copper("N1", "pad", "F.Cu", pad=((10.0, 10.0), 0.8))
    pts = [[0.0, 11.4], [12.0, 11.4], [12.0, 11.0], [0.0, 11.0]]
    seg = Copper("N2", "seg", "F.Cu", polyline=pts, half_width=0.15)
    got = drc._actual_gap(pad, seg)
    want = _brute_pad_polyline((10.0, 10.0), 0.8, pts)
    assert abs(got - want) <= 1e-12
    assert abs(want - 0.2) < 1e-9           # 真最近距（旧实现误剪后报 0.6）


def test_oracle_prune_property_random():
    """随机 500 组: 剪枝 min 与逐段暴力逐位一致（含 r 大/折线长诱导剪枝）。"""
    rng = random.Random(20261004)
    for _ in range(500):
        n = rng.randint(3, 40)
        pts = [[round(rng.uniform(0, 50), 3), round(rng.uniform(0, 50), 3)]
               for _ in range(n)]
        for k in range(1, n):
            if rng.random() < 0.6:
                pts[k][0] = pts[k - 1][0]
            elif rng.random() < 0.6:
                pts[k][1] = pts[k - 1][1]
        center = (round(rng.uniform(0, 50), 3), round(rng.uniform(0, 50), 3))
        r = round(rng.uniform(0.1, 1.5), 3)
        pad = Copper("N1", "p", "F.Cu", pad=(center, r))
        seg = Copper("N2", "q", "F.Cu", polyline=pts, half_width=0.15)
        got = drc._actual_gap(pad, seg)
        want = _brute_pad_polyline(center, r, pts)
        assert abs(got - want) <= 1e-12, (center, r, pts[:6], got, want)
