# -*- coding: utf-8 -*-
"""P0 黄金门：四度量模块对 V2 场景复算 = V2 判分键数值（34.85/37.25/38.05/42.4）。

判分键权威：partition-judge-v2/MANIFEST.md（先于被试会话预冻结）。
组合槽位为判分键原手算值转录（fixtures_v2.py 头注），度量算术全部由引擎通用函数完成。
"""
import pytest

import fixtures_v2 as fx
from v5.board import load_board
from v5.measure import measure_assignment
from v5.metrics import capacity as cap
from v5.metrics import width_prior as wp

EXPECTED_ORDER = ["A_P3B_P5F", "B_P3F_P5B", "C_P3F_P5I", "D_P3I_P5F"]


@pytest.fixture(scope="module")
def loaded_board():
    return load_board(fx.build_v2_board())


def test_source_template_still_frozen():
    assert fx.verify_source_frozen(), "V2 模板文件哈希漂移，夹具转录失效"


def test_golden_board_loads_with_hash_chain(loaded_board):
    assert loaded_board["provenance"]["source_sha256"] == fx.SOURCE_SHA256


@pytest.mark.parametrize("combo", EXPECTED_ORDER)
def test_golden_combo_cost_exact(combo):
    """判分键逐值复现：引擎通用度量算术 = 冻结判分键数值。"""
    combo_def = fx.GOLDEN_COMBOS[combo]
    m = measure_assignment(combo_def["routes"], fx.LAYER_DIRECTIONS)
    assert m["total_cost"] == pytest.approx(fx.GOLDEN[combo], abs=1e-9)


def test_golden_ordinal_matches_key():
    """判分键序：A(34.85) < B(37.25) < C(38.05) < D(42.4)。"""
    totals = {name: measure_assignment(d["routes"], fx.LAYER_DIRECTIONS)["total_cost"]
              for name, d in fx.GOLDEN_COMBOS.items()}
    ordered = sorted(totals, key=lambda k: totals[k])
    assert ordered == EXPECTED_ORDER


def test_golden_gap_B_minus_C_is_in1_penalty():
    """C−B = 0.8 = 0.2×4.0（P5 在 In1 的水平逆向罚；判分键内差一致）。"""
    t = {n: measure_assignment(d["routes"], fx.LAYER_DIRECTIONS)["total_cost"]
         for n, d in fx.GOLDEN_COMBOS.items()}
    assert t["C_P3F_P5I"] - t["B_P3F_P5B"] == pytest.approx(0.8)


def test_golden_gap_D_minus_A_is_p3_in1_penalty():
    """D−A = 7.55（P3 在 In1 的水平逆向罚；判分键内差一致）。"""
    t = {n: measure_assignment(d["routes"], fx.LAYER_DIRECTIONS)["total_cost"]
         for n, d in fx.GOLDEN_COMBOS.items()}
    assert t["D_P3I_P5F"] - t["A_P3B_P5F"] == pytest.approx(7.55)


def test_double_f_cu_capacity_infeasible():
    """双留F.Cu 判分键判不可行：占用 4.7 > 4.3（capacity 模块）。"""
    verdict = cap.check_fits(fx.c1_fcu_entries(p3_on_f=True, p5_on_f=True), fx.C1_CAPACITY)
    assert verdict["occupancy_mm"] == pytest.approx(4.7)
    assert not verdict["fits"]


def test_single_f_cu_occupancies_feasible():
    """A/B/C/D 四组合中任一留 F.Cu 的占用 4.0 ≤ 4.3。"""
    for p3f, p5f in ((True, False), (False, True)):
        verdict = cap.check_fits(fx.c1_fcu_entries(p3_on_f=p3f, p5_on_f=p5f), fx.C1_CAPACITY)
        assert verdict["fits"] and verdict["occupancy_mm"] == pytest.approx(4.0)


def test_per_net_breakdown_golden_anchor():
    """逐网拆解对锚：P3_F=25.25 / P5_F=6.15 / P5_B=12.0 / P5_I=12.8 / P3_B=28.7 / P3_I=36.25。"""
    anchors = {
        ("B_P3F_P5B", "P3"): 25.25,
        ("B_P3F_P5B", "P5"): 12.0,
        ("C_P3F_P5I", "P5"): 12.8,
        ("A_P3B_P5F", "P3"): 28.7,
        ("A_P3B_P5F", "P5"): 6.15,
        ("D_P3I_P5F", "P3"): 36.25,
    }
    for (combo, net), expect in anchors.items():
        m = measure_assignment(fx.GOLDEN_COMBOS[combo]["routes"], fx.LAYER_DIRECTIONS)
        got = next(r["cost"] for r in m["per_net"] if r["net_id"] == net)
        assert got == pytest.approx(expect), (combo, net)


def test_golden_measurement_bytes_double_run_equal():
    routes = fx.GOLDEN_COMBOS["A_P3B_P5F"]["routes"]
    from v5.measure import measure_assignment_bytes
    assert (measure_assignment_bytes(routes, fx.LAYER_DIRECTIONS)
            == measure_assignment_bytes(routes, fx.LAYER_DIRECTIONS))


def test_width_prior_on_v2_data(loaded_board):
    """width-prior 模块对 V2 板数据复算：P1 瓶颈收窄、P8 R1 违例事实。"""
    parts = {p["partition_id"]: p for p in loaded_board["partitions"]}
    p1 = wp.bottleneck_verdict(parts["P1"]["planned_width"],
                               parts["P1"]["bottleneck"]["usable_width"],
                               parts["P1"]["width_prior"]["w_min"])
    assert not p1["fits_as_planned"] and p1["narrowable"]
    r1 = loaded_board["hard_rules"]["R1"]
    p8_min = wp.conservative_min_width(parts["P8"]["current_a"],
                                       fab_min_mm=0.0,
                                       k_per_amp=r1["k_a"],
                                       floor_mm=r1["floor_mm"])
    assert p8_min == pytest.approx(0.8)
    assert not wp.in_interval(parts["P8"]["planned_width"],
                              parts["P8"]["width_prior"]["w_min"],
                              parts["P8"]["width_prior"]["w_max"])


def test_golden_p3_slot_r2_ana_all_clean():
    """转录槽位对 ANA 的 R2 距离全部 ≥3（夹具自洽性）。"""
    for combo in fx.GOLDEN_COMBOS:
        for route in fx.GOLDEN_COMBOS[combo]["routes"]:
            xs = [pt[0] for pt in route["polyline"]]
            assert max(xs) - fx.ANA_RECT["x_max"] >= 3.0 - 1e-9
