# -*- coding: utf-8 -*-
"""V5-R1 W-6 失败网 witness 探针钉值：形状距离口径+tmp108 A0 几何锚。

锚值来源=主审复核 LEAD-REVIEW-R1-2026-09-25.md §1-6 独立几何复算
（ep1 正交铜边隙 0.235mm、对角走廊 0.442mm；v5 R5=0.5mm 全封、
细规则 0.27mm 阈值可逃逸=(c) 类证据）——探针为其程序化重现
（D-1 立规：呈裁件引擎实测主张附可复算数据件）。
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import r1_failed_net_probe as P  # noqa: E402

BOARD = os.path.join(ROOT, "out", "v5-p5", "boards", "tmp108", "board.json")
HAVE_BOARD = os.path.isfile(BOARD)


# ------------------------------------------------ 形状距离口径（合成钉）

def test_copper_gap_circle_circle_diagonal_corridor():
    # 主审 §1-6 案例：两 ⌀0.265 圆盘、中心距 √2×0.5 → 走廊 0.4421
    a = {"shape": "circle", "size_mm": [0.265]}
    g = P.copper_gap((0.0, 0.0), a, (0.5, 0.5), a)
    assert round(g, 4) == 0.4421


def test_copper_gap_circle_circle_orthogonal():
    a = {"shape": "circle", "size_mm": [0.265]}
    g = P.copper_gap((0.0, 0.0), a, (0.5, 0.0), a)
    assert round(g, 4) == 0.235


def test_copper_gap_rect_rect_axis_and_diagonal():
    r = {"shape": "rect", "size_mm": [1.0, 0.6]}
    # 同轴分离：Δx=1.2 → 1.2-1.0=0.2
    assert round(P.copper_gap((0.0, 0.0), r, (1.2, 0.0), r), 6) == 0.2
    # 单轴搭接（y 重叠）→ 取轴向间隙 0.2
    assert round(P.copper_gap((0.0, 0.0), r, (1.2, 0.3), r), 6) == 0.2
    # 对角：dx=0.2、dy=0.3 → hypot=0.3606
    assert round(P.copper_gap((0.0, 0.0), r, (1.2, 0.9), r), 4) == 0.3606


def test_copper_gap_circle_rect():
    c = {"shape": "circle", "size_mm": [0.265]}
    r = {"shape": "rect", "size_mm": [1.0, 1.0]}
    # 圆心在盒正上方 0.5+0.1325+0.1 处 → 距离 0.1
    g = P.copper_gap((0.0, 0.5 + 0.1325 + 0.1), c, (0.0, 0.0), r)
    assert round(g, 4) == 0.1


def test_copper_gap_overlap_reports_negative():
    a = {"shape": "circle", "size_mm": [0.4]}
    g = P.copper_gap((0.0, 0.0), a, (0.1, 0.0), a)
    assert g < 0


# ------------------------------------------------ tmp108 A0 几何锚（世界在位时）

@pytest.mark.skipif(not HAVE_BOARD, reason="tmp108 board.json 缺（世界未物化）")
def test_probe_tmp108_a0_anchor():
    board = json.load(open(BOARD, encoding="utf-8"))["board"]
    doc = P.probe(board, "PT-A0", radius=1.6, trace_w=0.2)
    eps = {e["endpoint_index"]: e for e in doc["endpoints"]}
    # 4 端点全（R1 世界全 pad 质心集；旧世界 2 端抽象=本批判据一回归点）
    assert set(eps) == {0, 1, 2, 3}
    # ep0 邻域空（可达端点）
    assert eps[0]["min_copper_gap_mm"] is None
    # ep1：正交 0.235/对角走廊 0.4421（主审复核 §1-6 锚 0.442 三位有效）
    assert eps[1]["min_copper_gap_mm"] == 0.235
    assert eps[1]["max_corridor_gap_mm"] == 0.4421
    cal = eps[1]["calibers"]
    # v5 R5=0.5（+线半宽 0.1）→ 全封
    assert cal["v5_r5_plus_half_width_mm"] == 0.6
    assert cal["sealed_under_v5_rules"] is True
    # 细规则阈值 0.27 → 对角走廊可逃逸=(c) 类证据
    assert cal["fine_rule_escapable_threshold_mm"] == 0.27
    assert cal["escapable_under_fine_rules"] is True
    assert "(c) 类证据" in eps[1]["reading"]
    # 邻居=5 pad（3 正交 0.5mm 节距+2 对角 0.707mm）
    assert eps[1]["n_neighbors_within_radius_mm"] == 5
