# -*- coding: utf-8 -*-
"""test_geometry_properties —— 几何性质/暴力 oracle/D-ORACLE-1 反例常驻测试
（OPT-04 第一刀，EXEC-R2）。

底座：PCBFLOW-OPTIMAP S5-02 oracle 脚本（sha16=00c9d980f7eb42eb，8 族 779 例）
pytest 化移植——打击面=v5.drc._actual_gap 全 6 几何分支 + check_clearance
违例路径 + drc.hole_track_blocked + drc.check_edge_clearance（几何核正身）。

六族验收映射（任务书 OPT-04 判据）：交换顺序（arg-swap + copper-order-
permutation + vertex-reversal）/ 平移 / 镜像 / 共线切分合并 / 半径单调性 /
阈值邻域（S5-02 仅 39 例偏薄 → 本件加厚为 6 面 × 27 offset = 162 例，例数
如实记录）。附 D-ORACLE-1 实锤反例（A1/A2/A3）+ 三剪枝分支随机 vs 暴力
oracle（各 300）+ 旧缺陷形态复原普查（判别力对照，test-only 副本防回退）。

确定性：固定 seed 逐族独立（与 S5-02 同 seed 族保持同序列）；容差=1e-9
（=clearance.EPS 量级），arg-swap 用精确 1e-12。
"""
import copy
import random

import pytest

from v5 import drc
from v5.drc import Copper, check_clearance, check_edge_clearance
from v5.metrics import clearance as cl

TOL = 1e-9            # 变换不变量容差（与 clearance.EPS 同量级；S5-02 同值）
EXACT = 1e-12         # 参数交换精确口径（S5-02 同值）


# ---------------------------------------------------------------- 生成器
def _gen_polyline(rng, n_min=3, n_max=40, span=50.0):
    n = rng.randint(n_min, n_max)
    pts = [[round(rng.uniform(0, span), 3), round(rng.uniform(0, span), 3)]
           for _ in range(n)]
    for k in range(1, n):
        if rng.random() < 0.6:
            pts[k][0] = pts[k - 1][0]
        elif rng.random() < 0.6:
            pts[k][1] = pts[k - 1][1]
    return pts


def _g_pad(rng, span=20.0):
    return {"type": "pad",
            "c": [round(rng.uniform(0, span), 3), round(rng.uniform(0, span), 3)],
            "r": round(rng.uniform(0.1, 1.0), 3)}


def _g_poly(rng):
    return {"type": "poly", "pts": _gen_polyline(rng, 2, 14, 20.0)}


def _g_band(rng):
    x0 = round(rng.uniform(0, 12), 3)
    y0 = round(rng.uniform(0, 12), 3)
    return {"type": "band", "x0": x0, "y0": y0,
            "x1": x0 + round(rng.uniform(0.5, 6.0), 3),
            "y1": y0 + round(rng.uniform(0.5, 5.0), 3)}


_GEN = {"pad": _g_pad, "poly": _g_poly, "band": _g_band}
_KINDS = [("pad", "pad"), ("pad", "poly"), ("pad", "band"),
          ("poly", "poly"), ("poly", "band"), ("band", "band")]


def _rand_geom(rng, kind):
    return _GEN[kind](rng)


def _mk(g, net_id, cid, layer="F.Cu", hw=0.1):
    if g["type"] == "pad":
        return Copper(net_id, cid, layer,
                      pad=((g["c"][0], g["c"][1]), g["r"]), half_width=hw)
    if g["type"] == "poly":
        return Copper(net_id, cid, layer,
                      polyline=[list(p) for p in g["pts"]], half_width=hw)
    return Copper(net_id, cid, layer,
                  band=(g["x0"], g["y0"], g["x1"], g["y1"]), half_width=hw)


def _gap(ga, gb):
    return drc._actual_gap(_mk(ga, "N1", "a"), _mk(gb, "N2", "b"))


def _t_translate(g, dx, dy):
    h = copy.deepcopy(g)
    if h["type"] == "pad":
        h["c"] = [h["c"][0] + dx, h["c"][1] + dy]
    elif h["type"] == "poly":
        h["pts"] = [[p[0] + dx, p[1] + dy] for p in h["pts"]]
    else:
        h["x0"], h["x1"] = h["x0"] + dx, h["x1"] + dx
        h["y0"], h["y1"] = h["y0"] + dy, h["y1"] + dy
    return h


def _t_mirror(g, axis, c):
    h = copy.deepcopy(g)
    if h["type"] == "pad":
        h["c"] = [c - h["c"][0], h["c"][1]] if axis == "x" \
            else [h["c"][0], c - h["c"][1]]
    elif h["type"] == "poly":
        h["pts"] = [[c - p[0], p[1]] for p in h["pts"]] if axis == "x" \
            else [[p[0], c - p[1]] for p in h["pts"]]
    else:
        if axis == "x":
            x0, x1 = c - h["x0"], c - h["x1"]
            h["x0"], h["x1"] = min(x0, x1), max(x0, x1)
        else:
            y0, y1 = c - h["y0"], c - h["y1"]
            h["y0"], h["y1"] = min(y0, y1), max(y0, y1)
    return h


def _rev_poly(g):
    h = copy.deepcopy(g)
    h["pts"] = list(reversed(h["pts"]))
    return h


def _viol_set(coppers, req=0.5):
    viol, checked = check_clearance(coppers, req)
    return {(v.rule, tuple(sorted([v.subject_a, v.subject_b])),
             v.data.get("gap_mm")) for v in viol}, checked


# ------------------------------------------------ 判据①：D-ORACLE-1 反例
FIX_PTS = [[0.0, 11.4], [12.0, 11.4], [12.0, 11.0], [0.0, 11.0]]
FIX_CENTER, FIX_R = (10.0, 10.0), 0.8


def _brute_pad_poly(center, r, pts):
    """暴力 oracle：逐段取 min（无剪枝路径；与被测共用距离原语=路径外唯一事实）。"""
    return min(cl.pad_segment_distance(center, r, tuple(a), tuple(b))
               for a, b in zip(pts[:-1], pts[1:]))


def _old_gap_pad_polyline(center, r, pts):
    """D-ORACLE-1 修复前形态复原（test-only 副本，判别力对照防回退）：
    剪枝下界 rect_rect_gap 漏减 pad 半径 r（v5/drc.py 修复注释所述原实现）。"""
    best, thresh = float("inf"), None
    bb = (center[0], center[1], center[0], center[1])
    segbbs = [(min(a[0], b[0]), min(a[1], b[1]),
               max(a[0], b[0]), max(a[1], b[1]))
              for a, b in zip(pts[:-1], pts[1:])]
    for (a, b), sb in zip(cl.polyline(pts), segbbs):
        if thresh is not None and cl.rect_rect_gap(bb, sb) >= thresh:
            continue                                   # ← 漏减 r 的旧条件
        d = cl.pad_segment_distance(center, r, a, b)
        if d < best:
            best = d
            thresh = best + drc._PRUNE_SLACK
    return best


def test_d_oracle_1_reproducer():
    """实锤反例（仓内回归件 L17-26 原值）：修复码=暴力=0.2；旧形态报 0.6；
    check_clearance 层修复码捕获违例、旧形态漏判。"""
    pad = Copper("N1", "p", "F.Cu", pad=(FIX_CENTER, FIX_R))
    seg = Copper("N2", "s", "F.Cu", polyline=[list(p) for p in FIX_PTS],
                 half_width=0.15)
    fix_gap = drc._actual_gap(pad, seg)
    brute = _brute_pad_poly(FIX_CENTER, FIX_R, FIX_PTS)
    old_gap = _old_gap_pad_polyline(FIX_CENTER, FIX_R, FIX_PTS)
    assert abs(fix_gap - brute) <= 1e-12
    assert abs(brute - 0.2) < 1e-9          # 真最近距（旧形态误剪后报 0.6）
    assert abs(old_gap - 0.6) < 1e-9        # 旧缺陷形态判别力在场
    viol, _ = check_clearance([pad, seg], 0.5)
    assert len(viol) == 1 and round(viol[0].data["gap_mm"], 10) == 0.2
    assert not (old_gap < 0.5 - cl.EPS)     # 旧形态漏判演示（负例锚）


@pytest.mark.parametrize("branch", ["pad_polyline", "polyline_band",
                                    "polyline_polyline"])
def test_prune_vs_brute_oracle_all_branches(branch):
    """三剪枝分支随机 300 组 vs 暴力 oracle 逐位一致（seed=20261007，S5-02
    同 seed 复测口径；mismatch 须为 0）+ 旧式误剪普查 ≥1（判别力非退化）。"""
    rng = random.Random(20261007)
    n_per = 300
    mismatch, max_diff = 0, 0.0
    mispruned = 0
    for _ in range(n_per):
        pts = _gen_polyline(rng)
        if branch == "pad_polyline":
            pad_cu = Copper("N1", "p", "F.Cu",
                            pad=((round(rng.uniform(0, 50), 3),
                                  round(rng.uniform(0, 50), 3)),
                                 round(rng.uniform(0.1, 1.5), 3)))
            poly_cu = Copper("N2", "q", "F.Cu", polyline=pts, half_width=0.15)
            got = drc._actual_gap(pad_cu, poly_cu)
            want = _brute_pad_poly(pad_cu.pad[0], pad_cu.pad[1], pts)
            og = _old_gap_pad_polyline(pad_cu.pad[0], pad_cu.pad[1], pts)
            if abs(og - want) > 1e-12:
                mispruned += 1
        elif branch == "polyline_band":
            bx, by = round(rng.uniform(0, 10), 3), round(rng.uniform(0, 10), 3)
            b = (bx, by, round(bx + rng.uniform(0.5, 6.0), 3),
                 round(by + rng.uniform(0.5, 4.0), 3))
            poly_cu = Copper("N1", "q", "F.Cu", polyline=pts, half_width=0.15)
            band_cu = Copper("N2", "b", "F.Cu", band=b)
            bd = dict(x_min=b[0], y_min=b[1], x_max=b[2], y_max=b[3])
            got = drc._actual_gap(poly_cu, band_cu)
            want = min(cl.segment_rect_distance(a, c, bd)
                       for a, c in cl.polyline(pts))
            og = None
        else:
            pts2 = _gen_polyline(rng)
            poly_cu = Copper("N1", "r", "F.Cu", polyline=pts, half_width=0.15)
            poly2 = Copper("N2", "r2", "F.Cu", polyline=pts2, half_width=0.15)
            got = drc._actual_gap(poly_cu, poly2)
            want = cl.polyline_polyline(pts, pts2)
            og = None
        d = abs(got - want)
        max_diff = max(max_diff, d)
        if d > 1e-12:
            mismatch += 1
    assert mismatch == 0, "branch %s mismatch=%d max_diff=%g" % (
        branch, mismatch, max_diff)
    if branch == "pad_polyline":
        assert mispruned >= 1     # 旧缺陷形态在本 seed 普查内确有误剪（判别力）


# ------------------------------------------------ 判据②：六族 property test
def test_family_translation_invariance():
    """平移不变（120 例，seed=101；S5-02 同族同 seed）。"""
    rng = random.Random(101)
    for _ in range(120):
        ka, kb = _KINDS[rng.randrange(6)]
        ga, gb = _rand_geom(rng, ka), _rand_geom(rng, kb)
        dx, dy = rng.randint(-64, 64) / 8.0, rng.randint(-64, 64) / 8.0
        g0 = _gap(ga, gb)
        g1 = _gap(_t_translate(ga, dx, dy), _t_translate(gb, dx, dy))
        assert abs(g1 - g0) <= TOL, (ka, kb, dx, dy, g0, g1)


def test_family_mirror_invariance():
    """镜像不变（120 例，seed=102；镜面常数 32.0 精确二进值）。"""
    rng = random.Random(102)
    for k in range(120):
        ka, kb = _KINDS[rng.randrange(6)]
        ga, gb = _rand_geom(rng, ka), _rand_geom(rng, kb)
        axis = "x" if k % 2 == 0 else "y"
        g0 = _gap(ga, gb)
        g1 = _gap(_t_mirror(ga, axis, 32.0), _t_mirror(gb, axis, 32.0))
        assert abs(g1 - g0) <= TOL, (ka, kb, axis, g0, g1)


def test_family_arg_swap_exact():
    """参数顺序交换（120 例，seed=103；_actual_gap(a,b)==(b,a) 精确 1e-12）。"""
    rng = random.Random(103)
    for _ in range(120):
        ka, kb = _KINDS[rng.randrange(6)]
        ga, gb = _rand_geom(rng, ka), _rand_geom(rng, kb)
        g0 = drc._actual_gap(_mk(ga, "N1", "a"), _mk(gb, "N2", "b"))
        g1 = drc._actual_gap(_mk(gb, "N2", "b"), _mk(ga, "N1", "a"))
        assert abs(g1 - g0) <= EXACT, (ka, kb, g0, g1)


def test_family_polyline_vertex_reversal():
    """折线顶点反序（100 例，seed=104）。"""
    rng = random.Random(104)
    for k in range(100):
        ka, kb = ("poly", "poly") if k % 3 == 0 else \
            (("pad", "poly") if k % 3 == 1 else ("poly", "band"))
        ga, gb = _rand_geom(rng, ka), _rand_geom(rng, kb)
        ga2 = _rev_poly(ga) if ga["type"] == "poly" else ga
        gb2 = _rev_poly(gb) if gb["type"] == "poly" else gb
        g0, g1 = _gap(ga, gb), _gap(ga2, gb2)
        assert abs(g1 - g0) <= TOL, (ka, kb, g0, g1)


def test_family_copper_order_permutation():
    """check_clearance 铜序交换：违例集+checked 计数不变（80 例，seed=105）。"""
    rng = random.Random(105)
    for _ in range(80):
        coppers = []
        for j in range(5):
            g = _rand_geom(rng, rng.choice(["pad", "poly", "band"]))
            coppers.append(_mk(g, "N1" if j % 2 == 0 else "N2", "c%d" % j))
        s0, c0 = _viol_set(coppers)
        s1, c1 = _viol_set(coppers[2:] + coppers[:2])
        assert s0 == s1 and c0 == c1


def test_family_collinear_split_merge():
    """共线切分/合并（120 例，seed=106；中点逐次折半=精确共线，合并逐位还原）。"""
    def _split(pts, i):
        a, b = pts[i], pts[i + 1]
        m = [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0]
        return pts[:i + 1] + [m] + pts[i + 1:]

    def _split4(pts, i):
        a, b = pts[i], pts[i + 1]
        m2 = [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0]
        m1 = [(a[0] + m2[0]) / 2.0, (a[1] + m2[1]) / 2.0]
        m3 = [(m2[0] + b[0]) / 2.0, (m2[1] + b[1]) / 2.0]
        return pts[:i + 1] + [m1, m2, m3] + pts[i + 1:]

    rng = random.Random(106)
    for k in range(120):
        ka, kb = ("pad", "poly") if k % 2 == 0 else ("poly", "poly")
        ga, gb = _rand_geom(rng, ka), _rand_geom(rng, kb)
        i_a = rng.randrange(len(ga["pts"]) - 1) if ga["type"] == "poly" else None
        i_b = rng.randrange(len(gb["pts"]) - 1) if gb["type"] == "poly" else None
        sp = copy.deepcopy(ga)
        if i_a is not None:
            sp["pts"] = _split(ga["pts"], i_a)
        sq = copy.deepcopy(gb)
        if i_b is not None:
            sq["pts"] = _split4(gb["pts"], i_b)
        g0, g1 = _gap(ga, gb), _gap(sp, sq)
        assert abs(g1 - g0) <= TOL, (ka, kb, g0, g1)
        # 合并方向：去所插点=逐位还原原输入 → gap 精确相等
        mg, mq = copy.deepcopy(sp), copy.deepcopy(sq)
        restored = True
        if i_a is not None:
            if mg["pts"][:i_a + 1] + mg["pts"][i_a + 2:] != ga["pts"]:
                restored = False
            mg["pts"] = ga["pts"]
        if i_b is not None:
            if mq["pts"][:i_b + 1] + mq["pts"][i_b + 4:] != gb["pts"]:
                restored = False
            mq["pts"] = gb["pts"]
        gm = _gap(mg, mq)
        assert restored and abs(gm - g0) == 0.0


def test_family_radius_monotonicity():
    """半径单调性（80 例，seed=107）：gap(r) 非增；=max(0,中心距−r[−r_other])；
    违例旗标随 r 单调不减。"""
    rng = random.Random(107)
    radii = [round(0.05 * (t + 1), 3) for t in range(15)]
    for k in range(80):
        if k % 2 == 0:
            g = _g_pad(rng)
            pts = _gen_polyline(rng, 2, 10, 20.0)
            center = tuple(g["c"])
            brute_c = min(cl.point_segment(center, a, b)
                          for a, b in cl.polyline(pts))
            other = {"type": "poly", "pts": pts}

            def get(r):
                return drc._actual_gap(
                    Copper("N1", "p", "F.Cu", pad=(center, r)),
                    _mk(other, "N2", "o", hw=0.15))
            other_r_term = 0.0
        else:
            g = _g_pad(rng)
            c2 = (round(rng.uniform(0, 20), 3), round(rng.uniform(0, 20), 3))
            brute_c = cl.point_point(tuple(g["c"]), c2)
            other = {"type": "pad", "c": list(c2),
                     "r": round(rng.uniform(0.1, 0.8), 3)}

            def get(r):
                return drc._actual_gap(
                    Copper("N1", "p", "F.Cu", pad=(tuple(g["c"]), r)),
                    _mk(other, "N2", "o"))
            other_r_term = other["r"]
        prev = None
        flags = {req: [] for req in (0.4, 0.5, 0.8)}
        for r in radii:
            gr = get(r)
            if prev is not None:
                assert gr <= prev + 1e-12, (k, r, prev, gr)
            prev = gr
            want = max(0.0, brute_c - r - other_r_term)
            assert abs(gr - want) <= TOL, (k, r, gr, want)
            for req in flags:
                flags[req].append(gr < req - cl.EPS)
        for req, v in flags.items():
            assert all(v[i] <= v[i + 1] for i in range(len(v) - 1)), (k, req)


# ---------------------------------------- 判据②：阈值邻域（S5-02 39 例→加厚 150 例）
# 25 个 offset（0 + ±[1e-12..1e-3] 对数布点）；6 个判定面（R5 走廊×4 判定器
# + 孔带 + 板边带）。每例断言：判定器输出 ⟺ 距离原语谓词（oracle 交叉），
# 且 |offset|≥1e-6 的稳健侧符号正确（1e-12..1e-6 之间=数值敏感区只验一致性）。
OFFSETS = [0.0] + [s * m for s in (1, -1) for m in
                  (1e-12, 1e-11, 1e-10, 5e-10, 1e-9, 5e-9, 1e-8, 1e-7, 5e-7,
                   1e-6, 1e-5, 1e-4, 1e-3)]
assert len(OFFSETS) == 27
NEAR = 1e-6       # 稳健侧判定界（S5-02 同值）


def _thr_case(family, o):
    """单例两面读数：(判定器实际输出, 距离原语谓词期望)。返回 (actual,
    expected, robust)；robust=None 表示 offset 在数值敏感区内不设稳健侧。"""
    robust = (True if o <= -NEAR else (False if o >= NEAR else None))
    if family == "pad_pad":
        d = 1.0 + o
        p1 = Copper("N1", "a", "F.Cu", pad=((2.0, 3.0), 0.2))
        p2 = Copper("N2", "b", "F.Cu", pad=((2.0 + d, 3.0), 0.3))
        viol, _ = check_clearance([p1, p2], 0.5)
        prim = cl.pad_pad_distance((2.0, 3.0), 0.2, (2.0 + d, 3.0), 0.3)
        return len(viol) > 0, prim < 0.5 - cl.EPS, robust
    if family == "track_track":
        dd = 0.5 + o
        cand = Copper("N1", "c", "F.Cu", polyline=[[4.5, dd], [5.5, dd]])
        fore = Copper("N2", "f", "F.Cu",
                      polyline=[[0.0, 0.0], [10.0, 0.0]])
        g = drc._actual_gap(cand, fore)
        prim = cl.segment_segment((4.5, dd), (5.5, dd), (0.0, 0.0), (10.0, 0.0))
        return g < 0.5 - cl.EPS, prim < 0.5 - cl.EPS, robust
    if family == "pad_poly":
        dd = 0.8 + o
        p = Copper("N1", "a", "F.Cu", pad=((2.0, 0.0), 0.3))
        q = Copper("N2", "b", "F.Cu", polyline=[[0.0, dd], [10.0, dd]])
        viol, _ = check_clearance([p, q], 0.5)
        prim = cl.pad_segment_distance((2.0, 0.0), 0.3, (0.0, dd), (10.0, dd))
        return len(viol) > 0, prim < 0.5 - cl.EPS, robust
    if family == "poly_poly":
        dd = 0.5 + o
        c1 = Copper("N1", "c", "F.Cu", polyline=[[0.0, dd], [10.0, dd]])
        c2 = Copper("N2", "f", "F.Cu", polyline=[[0.0, 0.0], [10.0, 0.0]])
        viol, _ = check_clearance([c1, c2], 0.5)
        prim = cl.segment_segment((0.0, dd), (10.0, dd), (0.0, 0.0), (10.0, 0.0))
        return len(viol) > 0, prim < 0.5 - cl.EPS, robust
    if family == "hole_band":
        dd = 0.55 + o                       # 阈值=hr+HOLE_TO_HOLE+half=0.55
        got = drc.hole_track_blocked((5.0, 0.0), 0.15, (4.5, dd), (5.5, dd),
                                     0.15)
        prim = cl.point_segment((5.0, 0.0), (4.5, dd), (5.5, dd))
        want = prim < 0.15 + drc.HOLE_TO_HOLE_MM + 0.15 - cl.EPS
        return got, want, robust
    # edge_band：判定点距边=0.2+o vs 带 0.2（擦边合规）
    dd = 0.2 + o
    cand = Copper("N1", "c", "F.Cu", polyline=[[4.5, dd], [5.5, dd]])
    viol = check_edge_clearance([cand], (0.0, 0.0, 20.0, 12.0))
    return len(viol) > 0, dd < 0.2 - cl.EPS, robust


@pytest.mark.parametrize("family", ["pad_pad", "track_track", "pad_poly",
                                    "poly_poly", "hole_band", "edge_band"])
@pytest.mark.parametrize("offset", OFFSETS)
def test_threshold_neighborhood(family, offset):
    """阈值邻域（6 面 × 27 offset=162 例）：判定器 ⟺ 距离原语（oracle 交叉）
    + 稳健侧。S5-02 底座仅 39 例（3 面×13），本件加厚至 162 例（例数如实
    登记入批报告）。"""
    actual, expected, robust = _thr_case(family, offset)
    assert actual == expected, (family, offset, actual, expected)
    if robust is not None:
        assert actual == robust, (family, offset, actual, robust)


def test_threshold_neighborhood_case_count_disclosure():
    """例数披露钉（防回退）：27 offset × 6 面 = 162 例。"""
    assert len(OFFSETS) * 6 == 162
