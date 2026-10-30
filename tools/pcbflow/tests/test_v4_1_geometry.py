"""pcbflow.v4_1.geometry 单元测试（精确几何基元 + Minkowski 核距离引擎）。

手推闭式对照（非循环验证）：全部期望值由测试内独立公式/数值给出。
"""

from __future__ import annotations

import math

import pytest

from pcbflow.v4_1.geometry import (GeomError, GeomItem, PadGeom,
                                   clearance_between_items, point_seg_dist,
                                   seg_seg_dist)


# ---------------------------------------------------------------- 基础距离

def test_point_seg_dist_axis_and_oblique():
    assert point_seg_dist(0.5, 0.0, 0.0, 0.0, 1.0, 0.0) == pytest.approx(0.0)
    assert point_seg_dist(0.5, 0.3, 0.0, 0.0, 1.0, 0.0) == pytest.approx(0.3)
    # 投影在跨外 -> 端点距
    assert point_seg_dist(2.0, 0.0, 0.0, 0.0, 1.0, 0.0) == pytest.approx(1.0)
    assert point_seg_dist(-1.0, 0.0, 0.0, 0.0, 1.0, 0.0) == pytest.approx(1.0)


def test_seg_seg_dist_parallel_and_crossing():
    assert seg_seg_dist(0, 0, 1, 0, 0, 0.5, 1, 0.5) == pytest.approx(0.5)
    assert seg_seg_dist(0, 0, 1, 1, 0, 1, 1, 0) == pytest.approx(0.0)  # 相交
    assert seg_seg_dist(0, 0, 1, 0, 2, 0, 3, 0) == pytest.approx(1.0)


# ---------------------------------------------------------------- 焊盘基元

def test_circle_pad_point_distance():
    pad = PadGeom("circle", 10.0, 10.0, 1.0, 1.0, 0.0)
    assert pad.distance_to_point(11.0, 10.0) == pytest.approx(0.5)
    assert pad.distance_to_point(10.0, 11.0) == pytest.approx(0.5)
    assert pad.distance_to_point(10.6, 10.0) == pytest.approx(0.1)


def test_circle_pad_w_ne_h_conservative_max_axis():
    """畸形圆（w!=h）取 max 轴直径=保守超集。"""
    pad = PadGeom("circle", 0.0, 0.0, 1.0, 0.4, 0.0)
    # max 轴=1.0 -> r=0.5：点 (0.6,0) 距边界 0.1（若按 min 轴 r=0.2 则 0.4）
    assert pad.distance_to_point(0.6, 0.0) == pytest.approx(0.1)


def test_oval_pad_long_axis_exact():
    """oval 1.6x0.6 @ (10,20)：长轴端距=dx-0.8；短轴侧距=dy-0.3。"""
    pad = PadGeom("oval", 10.0, 20.0, 1.6, 0.6, 0.0)
    assert pad.distance_to_point(11.2, 20.0) == pytest.approx(0.4)
    assert pad.distance_to_point(10.0, 20.9) == pytest.approx(0.6)


def test_oval_vertical():
    pad = PadGeom("oval", 0.0, 0.0, 0.6, 1.6, 0.0)
    assert pad.distance_to_point(0.0, 1.2) == pytest.approx(0.4)
    assert pad.distance_to_point(1.0, 0.0) == pytest.approx(0.7)


def test_rect_pad_corner_distance():
    pad = PadGeom("rect", 10.0, 10.0, 1.0, 0.6, 0.0)
    # 角点 (10.5,10.3) 在边界上
    assert pad.distance_to_point(10.5, 10.3) == pytest.approx(0.0)
    # 右侧边缘法向：x=10.5 边界
    assert pad.distance_to_point(11.5, 10.3) == pytest.approx(1.0)
    # 角外斜向：hypot(1.0, 1.0)
    assert pad.distance_to_point(11.5, 11.3) == pytest.approx(
        math.hypot(1.0, 1.0))


def test_roundrect_pad_corner_arc():
    """roundrect 1.5x0.3 r=0.075：角弧心 (±0.675, ±0.075)。"""
    pad = PadGeom("roundrect", 10.0, 10.0, 1.5, 0.3, 0.0, radius=0.075)
    # 直边上方（投影在直边跨内）
    assert pad.distance_to_point(10.0, 10.4) == pytest.approx(0.25)
    # 角弧外侧斜向：到弧心 (10.675, 10.075) 距 d -> d-0.075
    d = math.hypot(10.9 - 10.675, 10.4 - 10.075)
    assert pad.distance_to_point(10.9, 10.4) == pytest.approx(d - 0.075)


def test_rotation_invariance_and_transform():
    """旋转 90° 的 0.4x1.6 rect 板上等效 1.6 宽 x 0.4 高（轴互换）。"""
    p0 = PadGeom("rect", 10.0, 10.0, 1.6, 0.4, 0.0)
    p90 = PadGeom("rect", 10.0, 10.0, 0.4, 1.6, 90.0)
    assert p0.distance_to_point(11.0, 10.0) == pytest.approx(0.2)
    assert p90.distance_to_point(11.0, 10.0) == pytest.approx(0.2)
    assert p0.distance_to_point(10.0, 11.0) == pytest.approx(0.8)
    assert p90.distance_to_point(10.0, 11.0) == pytest.approx(0.8)
    # 30° 旋转：闭式对照（局部系夹取到核角 (0.8,0.2)）
    p30 = PadGeom("rect", 10.0, 10.0, 1.6, 0.4, 30.0)
    # 查询点偏移 (1,0) -> 局部 (cos30, sin30)=(0.866025, 0.5)
    d = p30.distance_to_point(11.0, 10.0)
    assert d == pytest.approx(math.hypot(0.866025 - 0.8, 0.5 - 0.2),
                              abs=1e-6)


def test_custom_pad_vertex_bbox_conservative():
    pts = [(1.0, -1.17), (0.435, 0.575), (-0.125, -1.945), (1.015, -1.945)]
    pad = PadGeom("custom", 0.0, 0.0, 0.87, 2.79, 90.0,
                  primitive_pts=pts)
    assert pad.conservative_approximation is not None
    x0, y0, x1, y1 = pad.bbox()
    # 旋转 90°（x'=y, y'=-x）：板面 x 跨度=局部 y 跨度 2.52，y 跨度=局部
    # x 跨度 1.14——基元顶点全在包围盒内（保守超集）
    assert (x1 - x0) == pytest.approx(2.52, abs=1e-6)
    assert (y1 - y0) == pytest.approx(1.14, abs=1e-6)


# ---------------------------------------------------------------- 物项

def test_track_pad_clearance_exact_g11_anchor():
    """G1.1 锚几何：0.157043（kicad-cli 实测 0.1571，容差 0.01 内）。"""
    pad = PadGeom("roundrect", 47.675, 23.65, 1.5, 0.3, 0.0, radius=0.075)
    pad_item = GeomItem.from_pad(pad, {"F.Cu"})
    track = GeomItem.from_track("LTDC_R7", "F.Cu", 0.15,
                                48.1263, 23.15, 48.638432, 23.362132)
    res = clearance_between_items(track, pad_item)
    assert res is not None and not res["overlap"]
    assert res["clearance_mm"] == pytest.approx(0.157043, abs=1e-6)


def test_clearance_layer_rule_and_tht_all_layers():
    pad = GeomItem.from_pad(
        PadGeom("circle", 0.0, 0.0, 0.9, 0.9, 0.0),
        {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"})
    track_in1 = GeomItem.from_track("N1", "In1.Cu", 0.15, -1, 0.62, 1, 0.62)
    res = clearance_between_items(track_in1, pad)
    assert res is not None
    assert res["clearance_mm"] == pytest.approx(0.095)  # 0.62-0.45-0.075
    track_mask = GeomItem.from_track("N2", "F.Mask", 0.15, -1, 0.62, 1, 0.62)
    assert clearance_between_items(track_mask, pad) is None


def test_via_pad_overlap_negative():
    via = GeomItem.from_via("V", 0.6, {"F.Cu"}, 10.35, 70.0)
    pad = GeomItem.from_pad(PadGeom("circle", 10.0, 70.0, 1.0, 1.0, 0.0),
                            {"F.Cu"})
    res = clearance_between_items(via, pad)
    # 铜皮重叠（中心距 0.35 < 半径和 0.8）-> clearance 负（重叠旗标只在
    # 核相交时置位；负 clearance 同样触发硬违例）
    assert res is not None
    assert res["clearance_mm"] < 0.0
    assert res["clearance_mm"] == pytest.approx(-0.45)


# ---------------------------------------------------------------- fail-closed

@pytest.mark.parametrize("kwargs", [
    dict(shape="hexagon", x=0, y=0, w=1, h=1, rotation_deg=0),
    dict(shape="circle", x=0, y=0, w=0, h=1, rotation_deg=0),
    dict(shape="circle", x=0, y=0, w=-1, h=1, rotation_deg=0),
    dict(shape="roundrect", x=0, y=0, w=1, h=1, rotation_deg=0, radius=0.6),
    dict(shape="roundrect", x=0, y=0, w=1, h=1, rotation_deg=0, radius=-0.1),
    dict(shape="roundrect", x=0, y=0, w=1, h=1, rotation_deg=0, radius=None),
    dict(shape="circle", x=float("nan"), y=0, w=1, h=1, rotation_deg=0),
    dict(shape="circle", x=0, y=float("inf"), w=1, h=1, rotation_deg=0),
    dict(shape="circle", x=0, y=0, w=True, h=1, rotation_deg=0),
])
def test_pad_geom_fail_closed(kwargs):
    with pytest.raises(GeomError):
        PadGeom(**kwargs)


def test_geom_item_fail_closed():
    with pytest.raises(GeomError):
        GeomItem.from_track("N", "F.Cu", 0.0, 0, 0, 1, 0)      # 零宽
    with pytest.raises(GeomError):
        GeomItem.from_track("N", "F.Cu", -0.2, 0, 0, 1, 0)     # 负宽
    with pytest.raises(GeomError):
        GeomItem.from_track("N", "F.Cu", 0.2, float("nan"), 0, 1, 0)
    with pytest.raises(GeomError):
        GeomItem.from_via("N", 0.0, {"F.Cu"}, 0, 0)            # 零尺寸
    with pytest.raises(GeomError):
        GeomItem("weird", "N", {"F.Cu"}, [(0, 0), (1, 1)], 0.1)


def test_minkowski_identity_vs_bruteforce():
    """距离恒等式数值抽查：clearance(段, pad) == min_t dist(P(t)) - hw。"""
    pad = PadGeom("oval", 5.0, 5.0, 1.8, 0.8, 30.0)  # 旋转 oval
    ax, ay, bx, by = 7.2, 4.4, 8.1, 5.1
    hw = 0.075
    got = pad.distance_to_segment(ax, ay, bx, by) - hw
    best = min(pad.distance_to_segment(
        ax + t * (bx - ax), ay + t * (by - ay), ax + t * (bx - ax),
        ay + t * (by - ay)) for t in [i / 9999.0 for i in range(10000)])
    # 采样最小只能 >= 连续最小；闭式引擎应等于（数值密度内）连续最小
    assert got == pytest.approx(best - hw, abs=1e-6)
