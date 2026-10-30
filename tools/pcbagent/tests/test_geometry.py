# -*- coding: utf-8 -*-
"""几何内核单元测试（合成数据，不依赖 Rev-C）。

覆盖 p5_ground v3 修复过的四类历史缺陷：
单位一致性（本内核纯 mm）、轴对齐粗检（旋转矩形精确判）、seg-rect 漏中段、
抖动坐标（EPS 一致的边界判定）。
运行：python tests/test_geometry.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbagent import geometry as G  # noqa: E402


def approx(a, b, tol=1e-9):
    assert abs(a - b) < tol, f"{a} != {b}"


def test_seg_pt():
    approx(G.seg_pt_dist(0, 0, 0, 5, 10, 5), 5.0)
    approx(G.seg_pt_dist(5, 0, 0, 5, 10, 5), 5.0)
    approx(G.seg_pt_dist(-3, 5, 0, 5, 10, 5), 3.0)
    approx(G.seg_pt_dist(0, 5, 0, 5, 0, 5), 0.0)


def test_seg_seg():
    # 十字交叉
    approx(G.seg_seg_dist(-1, 0, 1, 0, 0, -1, 0, 1), 0.0)
    # 平行间距
    approx(G.seg_seg_dist(0, 0, 10, 0, 0, 0.2, 10, 0.2), 0.2)
    # 端点最近
    approx(G.seg_seg_dist(0, 0, 1, 0, 3, 0, 5, 0), 2.0)
    # 共线搭接
    approx(G.seg_seg_dist(0, 0, 2, 0, 2, 0, 4, 0), 0.0)
    # 共线分离
    approx(G.seg_seg_dist(0, 0, 2, 0, 3, 0, 4, 0), 1.0)
    # 45° 斜交
    approx(G.seg_seg_dist(0, 0, 2, 2, 2, 0, 2, 2), 0.0)


def test_pt_poly_and_seg_poly():
    sq = [(0, 0), (4, 0), (4, 4), (0, 4)]
    approx(G.pt_poly_dist(2, 2, sq), 0.0)
    approx(G.pt_poly_dist(5, 2, sq), 1.0)
    approx(G.pt_poly_dist(2, -0.3, sq), 0.3)
    # 中段穿入：只查端点会漏（p5 M2 缺陷回归）
    approx(G.seg_poly_dist(-1, 2, 5, 2, sq), 0.0)
    # 段在外平行
    approx(G.seg_poly_dist(-1, -0.5, 5, -0.5, sq), 0.5)
    # 段完全在内部
    approx(G.seg_poly_dist(1, 1, 2, 2, sq), 0.0)
    # 旋转矩形（真旋转判，非轴对齐 bbox）
    dia = [G.rot_pt(x, y, 45) for (x, y) in sq]
    # 顶点: A(0,0) B(2.83,-2.83) C(5.66,0) D(2.83,2.83)，中心 (2.83,0)
    approx(G.pt_poly_dist(2.83, 0.0, dia), 0.0, tol=1e-6)      # 中心在内
    approx(G.pt_poly_dist(4.0, 4.0, dia), 1.656854, tol=1e-4)  # 对角外侧
    # 在轴对齐 bbox 内但菱形外（轴对齐粗检会误判在内——M2 缺陷回归点）
    approx(G.pt_poly_dist(0.5, 2.5, dia), math.hypot(1.0, 1.0), tol=1e-6)


def test_prim_dist():
    # 两个圆盘
    approx(G.prim_dist((("pt", 0, 0), 0.5), (("pt", 2, 0), 0.5)), 1.0)
    # 重叠 → 0
    approx(G.prim_dist((("pt", 0, 0), 0.5), (("pt", 0.8, 0), 0.5)), 0.0)
    # 段（走线）vs 圆盘（过孔）：中心距 1.0，线宽 0.2、盘 0.6 → 表面距 1.0-0.1-0.3=0.6
    approx(G.prim_dist((("seg", 0, 0, 2, 0), 0.1), (("pt", 0, 1.0), 0.3)), 0.6)
    # 矩形 vs 矩形
    r1 = (("poly", [(0, 0), (1, 0), (1, 1), (0, 1)]), 0.0)
    r2 = (("poly", [(2, 0), (3, 0), (3, 1), (2, 1)]), 0.0)
    approx(G.prim_dist(r1, r2), 1.0)
    # 矩形 vs 旋转矩形（45°，绕自身中心转后平移到 (2, 0.5)）
    sq45 = [(x - 0.5, y - 0.5) for (x, y) in [(0, 0), (1, 0), (1, 1), (0, 1)]]
    r45 = (("poly", [(x + 2.0, y + 0.5) for (x, y) in
                     [G.rot_pt(x, y, 45) for (x, y) in sq45]]), 0.0)
    d = G.prim_dist(r1, r45)
    assert 0.0 < d < 0.5, d


def test_winding_rings():
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    hole = [(4, 4), (6, 4), (6, 6), (4, 6)]
    # 外环逆时针 + 孔顺时针（绕向相反，KiCad 惯例）
    rings = [outer, list(reversed(hole))]
    assert G.pt_in_rings(2, 2, rings)          # 实体区
    assert not G.pt_in_rings(5, 5, rings)      # 孔内
    assert not G.pt_in_rings(11, 5, rings)     # 外部
    # 绕向同向的退化情形不判孔
    rings_bad = [outer, hole]
    # 同向时 nonzero 绕数孔内=2 仍非零（会误判实体）——KiCad 文件保证绕向相反
    assert G.pt_in_rings(5, 5, rings_bad)


def test_seg_angle():
    assert G.seg_angle_ok(0, 0, 10, 0)
    assert G.seg_angle_ok(0, 0, 0, 10)
    assert G.seg_angle_ok(0, 0, 5, 5)
    assert G.seg_angle_ok(0, 0, 5, -5)
    assert not G.seg_angle_ok(0, 0, 5, 1)
    assert not G.seg_angle_ok(0, 0, 3, 1)


def test_rrect_via_inset():
    from pcbagent.mirror import BoardMirror
    inst = BoardMirror.__new__(BoardMirror)  # 只用其纯函数方法
    r = 0.2
    core = G.inset_rect_poly(0, 0, 0.5, 0.4, r)
    prim = (("poly", core), r)
    # 表面到圆角矩形中心线外 1mm 处的距离 = 1 - r?（核心半宽 0.3 → 右边 0.3 + r）
    approx(G.pt_prim_dist(1.5, 0, prim), 1.5 - 0.3 - r)


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"ALL {len(fns)} GEOMETRY TESTS PASSED")


if __name__ == "__main__":
    run_all()
