# -*- coding: utf-8 -*-
"""Lane-M4 placecheck 测试: **新 validator 自有夹具矩阵**（合成 pad 场
矩阵，非 v5.drc 绑定——本族只测 canvas.placecheck 的放置预检口径;
铜面对铜面 DRC 的 validate_full 对照在 test_m4_runner.py）。

覆盖: 接受路径/布间间距（含阈值参数化+R5 推导）/板框/非格点/值域/
未知分区/同网豁免/rotate·flip 覆盖后位置/check_all 全场/merge 语义/
circle 外接方/其它分区既有覆盖被尊重。"""
import pytest

from canvas import placecheck as pc

from canvas.tests.test_m4_fixtures import pc_board, pc_lattice


# ---------------------------------------------------------------- 夹具阵

def _far():
    """两分区相距远: A 场 (2,2)-(6,4)，B 场 (12,8)-(16,10)。"""
    b = pc_board([
        ("PA", "NET-A", ((3.0, 3.0), (5.0, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PB", "NET-B", ((13.0, 9.0), (15.0, 9.0)), [(2.0, 2.0), (2.0, 2.0)]),
    ])
    return b, pc_lattice(b)


def _row_pair(b_center_x):
    """同排两分区: A 场 (2,2)-(6,4)（中心 x=4）; B 场宽 4 中心 x=b_center_x。"""
    b = pc_board([
        ("PA", "NET-A", ((3.0, 3.0), (5.0, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PB", "NET-B", ((b_center_x - 1.0, 3.0), (b_center_x + 1.0, 3.0)),
         [(2.0, 2.0), (2.0, 2.0)]),
    ])
    return b, pc_lattice(b)


# ---------------------------------------------------------------- 矩阵

def test_accept_clear_move():
    """自有夹具: 开阔区 move 接受; 覆盖后外接矩形=期望值。"""
    b, lat = _far()
    ok, code, detail = pc.check_placement(b, lat, {}, "PA", {"move": [10, 2]})
    assert ok and code is None and detail is None
    # 中心 (5,1) → 场 (3,0)-(7,2); vs B 场 (12,8)-(16,10) 净空
    r = pc.pad_field_rect(b, lat, {"PA": {"move": [10, 2], "rotate": 0,
                                          "flip": False}}, "PA")
    assert r == (3.0, 0.0, 7.0, 2.0)


def test_reject_collision_gap():
    """自有夹具: 布间间距不足 → V_PLACEMENT_COLLISION（detail 含 gap）。"""
    b, lat = _row_pair(8.2)   # B 场 (6.2,2)-(10.2,4)
    ok, code, detail = pc.check_placement(b, lat, {}, "PA", {"move": [12, 6]})
    # A 移到中心 (6,3) → 场 (4,2)-(8,4) 与 B 场 x 重叠 → 拒
    assert not ok and code == "V_PLACEMENT_COLLISION" and "gap=" in detail


def test_reject_out_of_frame():
    """自有夹具: pad 场外接矩形越出板框 → V_PLACEMENT_EDGE。"""
    b, lat = _far()
    ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"move": [2, 2]})
    # 中心 (1,1) → 场 (-1,0)-(3,2): x 下缘越出 ws.x_min=0
    assert not ok and code == "V_PLACEMENT_EDGE"


def test_frame_boundary_inclusive_accept():
    """自有夹具: 场缘恰贴板框（FRAME_EPS 内）接受。"""
    b, lat = _far()
    ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"move": [4, 6]})
    # 中心 (2,3) → 场 (0,2)-(4,4) 恰贴左边框
    assert ok, code


def test_reject_non_grid_move():
    """自有夹具: 非格点 move（浮点/字符串/bool/长度≠2）→ E_NON_INTEGER_GRID。"""
    b, lat = _far()
    for bad in ([1.5, 2], ["a", 1], [1], [1, 2, 3], [True, 2], "12,6"):
        ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"move": bad})
        assert not ok and code == "E_NON_INTEGER_GRID", bad


def test_reject_move_out_of_lattice():
    """自有夹具: 整数格点但越出 lattice 域 → E_GRID_OUT_OF_BOUNDS。"""
    b, lat = _far()
    for bad in ([999, 2], [-5, 2], [4, 999]):
        ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"move": bad})
        assert not ok and code == "E_GRID_OUT_OF_BOUNDS", bad


def test_reject_unknown_partition():
    """自有夹具: 未知分区 → E_UNKNOWN_PARTITION（本件定名新码）。"""
    b, lat = _far()
    ok, code, detail = pc.check_placement(b, lat, {}, "PZ", {"move": [8, 6]})
    assert not ok and code == "E_UNKNOWN_PARTITION" and detail == "PZ"


def test_rotate_value_domain():
    """自有夹具: candidate rotate ∉ {0,1,2,3} → E_GRID_OUT_OF_BOUNDS。"""
    b, lat = _far()
    for bad in (4, -1, 7, "1", 1.5, True):
        ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"rotate": bad})
        assert not ok and code == "E_GRID_OUT_OF_BOUNDS", bad


def test_rotate_swings_bbox_into_collision():
    """自有夹具: rotate 覆盖后场形变化——横条转竖侵入下方分区被查出。"""
    b = pc_board([
        ("PA", "NET-A", ((2.0, 5.0), (8.0, 5.0)), [(1.0, 1.0), (1.0, 1.0)]),
        ("PB", "NET-B", ((4.0, 8.0), (6.0, 8.0)), [(1.0, 1.0), (1.0, 1.0)]),
    ])
    lat = pc_lattice(b)
    # 原位: A 场 (1.5,4.5)-(8.5,5.5) vs B 场 (3.5,7.5)-(6.5,8.5) 隙 2.0
    ok0, c0, _d0 = pc.check_placement(b, lat, {}, "PA", {"rotate": 0})
    assert ok0 and c0 is None
    # rotate 1（cw）: A 端点 (2,5)/(8,5) 绕中心 (5,5) → (5,2)/(5,8)
    #   → 场 (4.5,1.5)-(5.5,8.5) 与 B 场重叠（且仍在框内）
    ok1, c1, _d1 = pc.check_placement(b, lat, {}, "PA", {"rotate": 1})
    assert not ok1 and c1 == "V_PLACEMENT_COLLISION"


def test_flip_shifts_bbox_collision():
    """自有夹具: flip 端点镜像——非对称 pad 场翻转后大 pad 挤近邻被查出。"""
    b = pc_board([
        ("PA", "NET-A", ((4.0, 3.0), (6.0, 3.0)),
         [(4.0, 2.0), (1.0, 1.0)]),
        ("PB", "NET-B", ((8.8, 3.0), (10.8, 3.0)), [(1.0, 1.0), (1.0, 1.0)]),
    ])
    lat = pc_lattice(b)
    # 原位: A 场并 (2,2)-(6.5,4) vs B 场 (8.3,2.5)-(11.3,3.5) 隙 1.8
    ok0, _c0, _d0 = pc.check_placement(b, lat, {}, "PA", {"flip": False})
    assert ok0
    # flip: 大 pad 镜到 x=6 → A 场并 (3.5,2)-(8,4) vs B 场隙 0.3 < 0.5
    ok1, c1, _d1 = pc.check_placement(b, lat, {}, "PA", {"flip": True})
    assert not ok1 and c1 == "V_PLACEMENT_COLLISION"


def test_same_net_exempt_toggle():
    """自有夹具: 同网分区对缺省豁免; same_net_exempt=False 关豁免后拒收。"""
    b = pc_board([
        ("PA", "NET-X", ((3.0, 3.0), (5.0, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PB", "NET-X", ((5.5, 3.0), (7.5, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
    ])
    lat = pc_lattice(b)     # 两场 x 重叠（同网）
    ok, _c, _d = pc.check_placement(b, lat, {}, "PA", {"move": [9, 6]})
    assert ok                          # 同网豁免（R5 纪律镜像）
    ok2, c2, _d2 = pc.check_placement(b, lat, {}, "PA", {"move": [9, 6]},
                                      same_net_exempt=False)
    assert not ok2 and c2 == "V_PLACEMENT_COLLISION"
    # 豁免也适用于 check_all 全场
    assert pc.check_all_placements(b, lat, {}) == []
    assert len(pc.check_all_placements(b, lat, {},
                                       same_net_exempt=False)) == 1


def test_threshold_parameterization():
    """自有夹具: 阈值参数化——同 0.3 隙: 缺省 R5=0.5 拒、注入 0.2 收;
    R5=1.0 板推导拒 0.9 隙、注入 0.5 收。"""
    b, lat = _row_pair(8.2)      # A|B 基线场隙 = 6.2-6 = 0.2?否: 0.2 是
    # _row_pair(8.2): B 场 (6.2,2)-(10.2,4)，A 场 (2,2)-(6,4) → 隙 0.2
    # 候选: A move [8,10] → 中心 (4,5) → 场 (2,4)-(6,6) vs B 场: dy=0,
    # dx=0.3 → gap 0.3
    ok, code, _d = pc.check_placement(b, lat, {}, "PA", {"move": [8, 10]})
    assert not ok and code == "V_PLACEMENT_COLLISION"   # 0.3 < 0.5
    ok2, c2, _d2 = pc.check_placement(b, lat, {}, "PA", {"move": [8, 10]},
                                      min_gap_mm=0.2)
    assert ok2 and c2 is None                           # 0.3 ≥ 0.2
    # R5=1.0 推导板: 候选 0.9 隙拒、注入 0.5 收
    b10 = pc_board([
        ("PA", "NET-A", ((3.0, 3.0), (5.0, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
        ("PB", "NET-B", ((8.9, 3.0), (10.9, 3.0)), [(2.0, 2.0), (2.0, 2.0)]),
    ], r5=1.0)
    lat10 = pc_lattice(b10)     # B 场 (7.9,2)-(11.9,4)
    assert pc.default_min_gap_mm(b10) == 1.0
    ok3, c3, _d3 = pc.check_placement(b10, lat10, {}, "PA", {"move": [10, 6]})
    # A 中心 (5,3) → 场 (3,2)-(7,4) vs B 场: 隙 0.9 < 1.0 → 拒
    assert not ok3 and c3 == "V_PLACEMENT_COLLISION"
    ok4, _c4, _d4 = pc.check_placement(b10, lat10, {}, "PA",
                                       {"move": [10, 6]}, min_gap_mm=0.5)
    assert ok4


def test_check_all_clean_then_violations():
    """自有夹具: check_all 全场——净空阵 []; 越框+碰撞违例结构/检查序
    （单分区面在配对面之前）。"""
    b, lat = _far()
    assert pc.check_all_placements(b, lat, {}) == []
    # 越框
    pl = {"PA": {"move": [2, 2], "rotate": 0, "flip": False}}
    v = pc.check_all_placements(b, lat, pl)
    assert [x["code"] for x in v] == ["V_PLACEMENT_EDGE"]
    assert v[0]["partition_id"] == "PA"
    # 碰撞对: A 移 (5,3)、B 移 (8.5,3) → 场 (3,2)-(7,4) vs (6.5,2)-(10.5,4)
    #   → x 重叠 0.5 → gap=-0.5
    pl2 = {"PA": {"move": [10, 6], "rotate": 0, "flip": False},
           "PB": {"move": [17, 6], "rotate": 0, "flip": False}}
    v2 = pc.check_all_placements(b, lat, pl2)
    assert [x["code"] for x in v2] == ["V_PLACEMENT_COLLISION"]
    assert v2[0]["partitions"] == ["PA", "PB"]
    assert v2[0]["gap_mm"] == pytest.approx(-0.5, abs=1e-6)
    # 检查序: 越框（单分区面）先于配对面
    pl3 = {"PA": {"move": [2, 2], "rotate": 0, "flip": False},
           "PB": {"move": [6, 2], "rotate": 0, "flip": False}}
    v3 = pc.check_all_placements(b, lat, pl3)
    assert [x["code"] for x in v3] == \
        ["V_PLACEMENT_EDGE", "V_PLACEMENT_COLLISION"]


def test_other_partition_coverage_respected():
    """自有夹具: 候选判的是**其它分区覆盖后**位置（非原位）。"""
    b, lat = _far()
    # B 已 move 到中心 (9,6) → 覆盖后场 (7,5)-(11,7)
    pl = {"PB": {"move": [18, 12], "rotate": 0, "flip": False}}
    # A move [16,10] → 场 (6,4)-(10,6) 与 B 覆盖后场重叠 → 拒
    ok, code, _d = pc.check_placement(b, lat, pl, "PA", {"move": [16, 10]})
    assert not ok and code == "V_PLACEMENT_COLLISION"
    # 同一 move 在 B 原位（远角）时接受——证明判覆盖后位置
    ok2, _c2, _d2 = pc.check_placement(b, lat, {}, "PA", {"move": [16, 10]})
    assert ok2


def test_circle_pad_square_envelope():
    """自有夹具: circle pad（size_mm 单元素）外接方=半径方。"""
    b = pc_board([
        ("PA", "NET-A", ((4.0, 3.0), (6.0, 3.0)), [(1.6,), (1.6,)]),
        ("PB", "NET-B", ((14.0, 9.0), (16.0, 9.0)), [(2.0, 2.0), (2.0, 2.0)]),
    ])
    lat = pc_lattice(b)
    r = pc.pad_field_rect(b, lat, {}, "PA")
    assert r == (4.0 - 0.8, 3.0 - 0.8, 6.0 + 0.8, 3.0 + 0.8)


def test_merge_candidate_semantics():
    """自有夹具: merge——缺键承袭/None 清 move/无覆盖起恒等/合同外键与
    非 dict 异常 fail-closed。"""
    cur = {"PA": {"move": [10, 4], "rotate": 1, "flip": True}}
    assert pc.merge_candidate(cur, "PA", {}) == \
        {"move": [10, 4], "rotate": 1, "flip": True}
    assert pc.merge_candidate(cur, "PA", {"rotate": 3}) == \
        {"move": [10, 4], "rotate": 3, "flip": True}
    assert pc.merge_candidate(cur, "PA", {"move": None}) == \
        {"move": None, "rotate": 1, "flip": True}
    assert pc.merge_candidate({}, "PB", {"move": [4, 6]}) == \
        {"move": [4, 6], "rotate": 0, "flip": False}
    with pytest.raises(ValueError):
        pc.merge_candidate(cur, "PA", {"bogus": 1})
    with pytest.raises(ValueError):
        pc.merge_candidate(cur, "PA", None)


def test_candidate_malformed_fail_closed():
    """自有夹具: candidate 非 dict / flip 非 bool / 合同外键 → ValueError
    （API 误用面 fail-closed，无码静默）。"""
    b, lat = _far()
    with pytest.raises(ValueError):
        pc.check_placement(b, lat, {}, "PA", None)
    with pytest.raises(ValueError):
        pc.check_placement(b, lat, {}, "PA", {"flip": 1})
    with pytest.raises(ValueError):
        pc.check_placement(b, lat, {}, "PA", {"move": [1, 2], "x": 3})


def test_rect_gap_metric():
    """自有夹具: rect_gap 度量——单轴隙/角距 hypot/重叠负侵入。"""
    a = (0.0, 0.0, 2.0, 2.0)
    assert pc.rect_gap_mm(a, (3.0, 0.0, 5.0, 2.0)) == pytest.approx(1.0)
    assert pc.rect_gap_mm(a, (2.0, 4.0, 4.0, 6.0)) == pytest.approx(2.0)
    assert pc.rect_gap_mm(a, (3.0, 3.0, 5.0, 5.0)) == \
        pytest.approx(2 ** 0.5)               # 角距 hypot(1,1)
    assert pc.rect_gap_mm(a, (1.0, 1.0, 3.0, 3.0)) == \
        pytest.approx(-1.0)                   # 单轴侵入深度
    assert pc.rect_gap_mm(a, (0.0, 0.0, 2.0, 2.0)) == \
        pytest.approx(-2.0)                   # 全叠双轴深度取小
