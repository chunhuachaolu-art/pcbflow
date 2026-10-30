# -*- coding: utf-8 -*-
"""V5-R1 W-1 单测：v5.steiner（FLUTE 查表形态自研复现）。

验收门 1 对位（任务书 §3.1）：合成多端网（3/5/8 端钉值）树质量对照——
B1S 总长 ≤ MST 总长逐件；精确解对照（DW 双实现互证=GeoSteiner 角色替代，
用户八裁①附款披露）；拓扑合同（连通无环/端点覆盖/确定性）。
"""
import math
import random

import pytest

from v5 import steiner


# ---------------------------------------------------------------- DW 正确性

def test_exact_rsmt_classic_values():
    # 经典钉值：L3 三点 (0,0),(2,0),(1,1) → RSMT=3（Steiner 点 (1,0)）
    total, nodes, edges = steiner.exact_rsmt([(0, 0), (2, 0), (1, 1)])
    assert total == pytest.approx(3.0)
    assert (1.0, 0.0) in {(round(n[0], 9), round(n[1], 9)) for n in nodes}
    # 正方形 4 点边长 2 → RSMT=6（H 形；=MST 平手）
    assert steiner.exact_rsmt([(0, 0), (2, 0), (0, 2), (2, 2)])[0] \
        == pytest.approx(6.0)


def test_exact_rsmt_brute_cross_check():
    """DW vs 暴力枚举（Hanan 子集+MST）小实例交叉验证（n=3..5）。"""
    import itertools

    def brute(pts):
        xs = sorted({p[0] for p in pts})
        ys = sorted({p[1] for p in pts})
        grid = [(x, y) for x in xs for y in ys]
        best = float("inf")
        for extra in itertools.combinations(grid, len(pts) - 2):
            allp = list(pts) + list(extra)
            cands = []
            for i in range(len(allp)):
                for j in range(i + 1, len(allp)):
                    d = (abs(allp[i][0] - allp[j][0])
                         + abs(allp[i][1] - allp[j][1]))
                    cands.append((d, i, j))
            cands.sort()
            parent = list(range(len(allp)))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            tot = cnt = 0
            for d, i, j in cands:
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
                    tot += d
                    cnt += 1
            if cnt == len(allp) - 1:
                best = min(best, tot)
        return best

    rng = random.Random(20260925)
    for _ in range(25):
        n = rng.randrange(3, 6)
        pts = sorted({(rng.randrange(10), rng.randrange(10))
                      for _ in range(n)})
        if len(pts) < 3:
            continue
        dw = steiner.exact_rsmt(pts)[0]
        bf = brute(pts)
        assert dw == pytest.approx(bf), pts


# ---------------------------------------------------------------- 查表段

def test_pot_table_degree3_5_vs_exact():
    """查表段（3-4 端）与 DW 精确解逐件对账（双实现互证；独立 seed）；
    5 端=表段收口后走 DW 在线精确段（method 断言+最优性同账）。"""
    rng = random.Random(99001)
    for n in (3, 4, 5):
        for _ in range(30):
            pts = sorted({(rng.randrange(60), rng.randrange(60))
                          for _ in range(n)})
            if len(pts) != n:
                continue
            topo = steiner.steiner_topology(pts)
            if n <= steiner.FLUTE_TABLE_MAX_DEGREE:
                assert topo["method"] in ("pot-table", "pot-miss-exact-dw")
            else:
                assert topo["method"] == "exact-dw"
            dw = steiner.exact_rsmt(pts)[0]
            assert topo["total_mm"] == pytest.approx(dw, abs=1e-9), pts


def test_exact_dw_segment_6_to_9():
    """DW 在线精确段（6-9 端）method 分派与最优性抽样。"""
    rng = random.Random(99002)
    for n in (6, 7, 8, 9):
        pts = sorted({(rng.randrange(70), rng.randrange(70))
                      for _ in range(n)})
        if len(pts) != n:
            continue
        topo = steiner.steiner_topology(pts)
        assert topo["method"] == "exact-dw"
        dw = steiner.exact_rsmt(pts)[0]
        assert topo["total_mm"] == pytest.approx(dw, abs=1e-9)


def test_decomposed_segment_above_9():
    """>9 端分解段：连通树+端点覆盖+B1S≤MST（分解近似界=不劣于 MST。"""
    rng = random.Random(99003)
    pts = sorted({(rng.randrange(100), rng.randrange(100))
                  for _ in range(14)})
    topo = steiner.steiner_topology(pts)
    assert topo["method"] == "decomposed"
    mst = sum(abs(pts[a][0] - pts[b][0]) + abs(pts[a][1] - pts[b][1])
              for a, b in steiner._mst_edges(pts))
    assert topo["total_mm"] <= mst + 1e-9


# ---------------------------------------------------------------- B1S≤MST

@pytest.mark.parametrize("n,seed", [(3, 1), (5, 2), (8, 3), (9, 4)])
def test_b1s_not_worse_than_mst(n, seed):
    """验收门 1：合成多端网 B1S 总长 ≤ MST 总长（逐件）。"""
    rng = random.Random(seed)
    for _ in range(20):
        pts = sorted({(rng.randrange(50), rng.randrange(50))
                      for _ in range(n)})
        if len(pts) != n:
            continue
        topo = steiner.steiner_topology(pts)
        mst = sum(abs(pts[a][0] - pts[b][0]) + abs(pts[a][1] - pts[b][1])
                  for a, b in steiner._mst_edges(pts))
        assert topo["total_mm"] <= mst + 1e-9, pts


# ---------------------------------------------------------------- 拓扑合同

def test_topology_shape_contract():
    rng = random.Random(99005)
    for n in (3, 5, 8, 11):
        pts = sorted({(rng.randrange(60), rng.randrange(60))
                      for _ in range(n)})
        if len(pts) != n:
            continue
        topo = steiner.steiner_topology(pts)
        nodes = [tuple(p) for p in topo["nodes"]]
        assert topo["terminal_count"] == n
        assert [nodes[k] for k in range(n)] == [tuple(p) for p in pts] \
            if len(pts) == n else True
        # 连通无环
        adj = {i: set() for i in range(len(nodes))}
        for u, v in topo["edges"]:
            adj[u].add(v)
            adj[v].add(u)
        assert len(topo["edges"]) == len(nodes) - 1
        seen = {0}
        stack = [0]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        assert len(seen) == len(nodes)
        # 分支点=度 ≥3 非端点
        for k in range(n, len(nodes)):
            assert len(adj[k]) >= 3


def test_determinism_double_run():
    pts = [(3, 1), (17, 5), (2, 28), (40, 40), (25, 9), (60, 33), (5, 60),
           (44, 61), (31, 55), (70, 70)]
    a = steiner.steiner_topology(pts)
    b = steiner.steiner_topology(pts)
    assert a == b


def test_trivial_and_degenerate():
    assert steiner.steiner_topology([])["edges"] == []
    one = steiner.steiner_topology([(1.5, 2.5)])
    assert one["terminal_count"] == 1 and one["edges"] == []
    two = steiner.steiner_topology([(0, 0), (3, 4)])
    assert two["total_mm"] == pytest.approx(7.0)
    assert two["edges"] == [[0, 1]]


def test_shape_key_order_invariant():
    pts = [(0, 0), (10, 3), (4, 9)]
    assert steiner._shape_key(pts) == steiner._shape_key(list(reversed(pts)))
