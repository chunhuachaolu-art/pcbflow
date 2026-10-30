# -*- coding: utf-8 -*-
"""Lane-M4 referee 测试: 三分量公式手算锚定（自有夹具矩阵，非 v5.drc
绑定——referee 是评分器不是 DRC）、权重注入与 fail-closed、无随机源
（双跑等）、真板/合成板界内 sanity。"""
import json

import pytest

from v5 import canonical

from canvas import referee as ref
from canvas.tests.test_k1_fixtures import real_state, synth_state
from canvas.tests.test_m4_fixtures import blocked_state, pc_board, pc_lattice


def _single(pad, eps=((3.0, 3.0), (5.0, 3.0))):
    b = pc_board([("PA", "NET-A", eps, [pad, pad])])
    return b, pc_lattice(b)


def test_capacity_exact_single_partition():
    """手算: 单分区 2×2 pad（场 (2,2)-(6,4)）→ 占位格点 i4..12×j4..8=45,
    域 41×25=1025 → capacity=1-45/1025。"""
    b, lat = _single((2.0, 2.0))
    s = ref.score(b, lat, {})
    assert s["capacity"] == round(1.0 - 45.0 / 1025.0, 9)
    assert s["corridor"] == 1.0          # 单分区无对
    assert s["escape"] == round(2.0 / 3.0, 9)   # 端点 d=3 → 1-3/9
    assert s["total"] == pytest.approx(
        0.4 * (2.0 / 3.0) + 0.3 * 1.0 + 0.3 * (1.0 - 45.0 / 1025.0), abs=1e-8)
    assert s["weights_used"] == {"capacity": 0.3, "corridor": 0.3,
                                 "escape": 0.4}


def test_escape_exact_thin_field():
    """手算: 1×1 pad（场 (2.5,2.5)-(5.5,3.5)）→ 端点 d=2 → escape=7/9。"""
    b, lat = _single((1.0, 1.0))
    s = ref.score(b, lat, {})
    assert s["escape"] == round(7.0 / 9.0, 9)


def test_corridor_third_party_occupancy():
    """手算: A|B 走廊被 C 占 9/33, 其余对 0 → corridor=1-1/11。"""
    b = pc_board([
        ("PA", "NET-A", ((2.0, 5.0), (2.0, 7.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PB", "NET-B", ((18.0, 5.0), (18.0, 7.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PC", "NET-C", ((10.0, 6.0), (12.0, 6.0)), [(2.0, 2.0), (2.0, 2.0)]),
    ])
    lat = pc_lattice(b)
    s = ref.score(b, lat, {})
    # A 场 (1,4)-(3,8) 中心 (4,12); B 场 (17,4)-(19,8) 中心 (36,12);
    # C 场 (9,5)-(13,7) 占 i18..26×j10..14 → A|B 走廊行 j12 i4..36 共 33
    # 格被占 9; 其余 2 对 0 → mean occ = (9/33)/3
    assert s["corridor"] == round(1.0 - (9.0 / 33.0) / 3.0, 9)


def test_placements_change_score():
    """覆盖后位置进评分: 堵塞板 PC2 让出走廊列 → corridor 0.961538→1.0。"""
    st = blocked_state()
    b, lat, pl = st.board, st.lattice, st.placements
    s0 = ref.score(b, lat, pl)
    assert s0["corridor"] == round(1.0 - (3.0 / 13.0) / 6.0, 9)
    st.set_placement("PC2", move=[8, 10])     # 中心 (4,5): 场离 i12 走廊列
    s1 = ref.score(b, lat, st.placements)
    assert s1["corridor"] == 1.0
    assert s1["total"] > s0["total"]


def test_weights_injection():
    """权重注入点: 自定权重改 total; 单分量权重=直取该分量。"""
    b, lat = _single((2.0, 2.0))
    s = ref.score(b, lat, {})
    w = {"escape": 1.0, "corridor": 0.0, "capacity": 0.0}
    s2 = ref.score(b, lat, {}, weights=w)
    assert s2["total"] == s["escape"] and s2["weights_used"] == w
    w3 = {"escape": 0.0, "corridor": 0.0, "capacity": 2.0}
    s3 = ref.score(b, lat, {}, weights=w3)
    assert s3["total"] == pytest.approx(2.0 * s["capacity"], abs=1e-9)


def test_weights_fail_closed():
    b, lat = _single((2.0, 2.0))
    for bad in ({"escape": 1.0, "corridor": 0.0},                 # 缺键
                {"escape": 1.0, "corridor": 0.0, "capacity": 0.0, "x": 1.0},
                {"escape": -0.1, "corridor": 0.0, "capacity": 0.0},
                {"escape": True, "corridor": 0.0, "capacity": 0.0}):
        with pytest.raises(ValueError):
            ref.score(b, lat, {}, weights=bad)


def test_bounds_and_determinism_all_boards():
    """三板（真/合成/堵塞）: 分量全 [0,1]; 双跑 dict 等 + canonical 字节等
    （无随机源）。"""
    for st in (real_state(), synth_state(), blocked_state()):
        s1 = ref.score(st.board, st.lattice, st.placements)
        s2 = ref.score(st.board, st.lattice, st.placements)
        for k in ("escape", "corridor", "capacity", "total"):
            assert 0.0 <= s1[k] <= 1.0 + 1e-12, (k, s1[k])
        assert s1 == s2
        assert canonical.canonical_json(s1) == canonical.canonical_json(s2)
        assert json.loads(canonical.canonical_json(s1))["total"] == \
            s1["total"]


def test_capacity_real_board_positive_free_room():
    st = real_state()
    s = ref.score(st.board, st.lattice, st.placements)
    # 真板 9 分区大包络并集占板面——空闲率仍为正且 <1（占位非空非满）
    assert 0.0 < s["capacity"] < 1.0
