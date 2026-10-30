"""资源校准指标计算器（PREREG-RESOURCE-CALIBRATION-R1 冻结版 §1）测试。

覆盖：type-7 分位/中位数与手算样例对账（P-RC-6）、残差 E/e 公式与
actual=0 不入分母（§0.3）、单位护栏剔除登记（§0.4）、M4 三档门控
（n=0 → not_available / 0<n<5 → not_enough_data / n≥5 出数，Q7）、
M1/M2 行级池与板级池双口径手算（Q2）、M2b、M3 worst-board 并列
board_id 字典序取首、输入顺序不敏感 + byte-exact 重放（确定性）、
describe_pool 混类 fail-closed。冻结口径常量（M4_MIN_ROWS=5、type-7）
零回退测试（P-RC-2 纪律）。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import hashing, resource_calibration_metrics as rcm


# ---------------------------------------------------------------------------
# 行构造 helpers（observation-row-v1 最小投影；仅指标计算所需字段）
# ---------------------------------------------------------------------------

_OBS = [0]


def _row(kind, obj, board_id, predicted, actual, p_unit="count", a_unit="count",
         p_reason=None, a_reason=None):
    _OBS[0] += 1
    pred = None
    if predicted is not None or p_reason is not None:
        pred = {"value": predicted, "unit": p_unit, "model": "m", "basis": []}
        if p_reason is not None:
            pred["not_available_reason"] = p_reason
    act = None
    if actual is not None or a_reason is not None:
        act = {"value": actual, "unit": a_unit}
        if a_reason is not None:
            act["not_available_reason"] = a_reason
    return {
        "row_id": "%s:%s" % (kind, obj),
        "observation_id": "obs-test-%04d" % _OBS[0],
        "split": {"board_id": board_id, "role": "train"},
        "prediction": pred,
        "actual": act,
    }


def _e_rows(board_id, es, kind="escape_slots", actual=100.0):
    """构造给定相对残差 e 的行集（actual=100，predicted=100·(1−e)）。"""
    return [_row(kind, "%s#%d" % (board_id, i), board_id,
                 predicted=actual * (1.0 - e), actual=actual)
            for i, e in enumerate(es)]


# ---------------------------------------------------------------------------
# type-7 分位/中位数：手算样例对账（P-RC-6 最小数值自检核心样例）
# ---------------------------------------------------------------------------


class TestQuantileType7:
    def test_hand_examples_odd_n(self):
        # [1..5]：P50 → h=(5−1)·0.5=2.0 → x[2]=3.0
        #         P90 → h=3.6 → 4+0.6·(5−4)=4.6；P95 → h=3.8 → 4.8
        assert rcm.quantile_type7([5, 1, 4, 2, 3], 0.50) == 3.0
        assert abs(rcm.quantile_type7([1, 2, 3, 4, 5], 0.90) - 4.6) < 1e-12
        assert abs(rcm.quantile_type7([1, 2, 3, 4, 5], 0.95) - 4.8) < 1e-12

    def test_hand_examples_even_n(self):
        # [1..4]：P50 → h=1.5 → 2+0.5·1=2.5；P90 → h=2.7 → 3.7；P95 → 3.85
        assert rcm.quantile_type7([4, 2, 1, 3], 0.50) == 2.5
        assert abs(rcm.quantile_type7([1, 2, 3, 4], 0.90) - 3.7) < 1e-12
        assert abs(rcm.quantile_type7([1, 2, 3, 4], 0.95) - 3.85) < 1e-12

    def test_median_and_edges(self):
        assert rcm.median_type7([10.0, 30.0, 20.0]) == 20.0
        assert rcm.median_type7([10.0, 30.0, 20.0, 40.0]) == 25.0
        assert rcm.quantile_type7([7.0], 0.5) == 7.0  # n=1
        assert rcm.quantile_type7([1.0, 2.0], 0.0) == 1.0  # q=0 → min
        assert rcm.quantile_type7([1.0, 2.0], 1.0) == 2.0  # q=1 → max

    def test_matches_numpy_linear_reference(self):
        # numpy 1.x/2.x percentile linear 同式参考实现（手工展开两处）：
        # [0.1,0.2,0.3,0.4,0.5] P90 → h=3.6 → 0.4+0.6·0.1=0.46
        # [0.1,0.2,0.3,0.4,0.5] P95 → h=3.8 → 0.4+0.8·0.1=0.48
        v = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert abs(rcm.quantile_type7(v, 0.90) - 0.46) < 1e-12
        assert abs(rcm.quantile_type7(v, 0.95) - 0.48) < 1e-12

    def test_fail_closed(self):
        with pytest.raises(ValueError):
            rcm.quantile_type7([], 0.5)
        with pytest.raises(ValueError):
            rcm.quantile_type7([1.0, float("nan")], 0.5)


# ---------------------------------------------------------------------------
# 行分类与护栏（§0.3/§0.4）
# ---------------------------------------------------------------------------


class TestClassifyRow:
    def test_residual_formula(self):
        status, d = rcm.classify_row(
            _row("rails", "GND", "b/x", predicted=6, actual=8))
        assert status == "measurable"
        assert d["residual"] == 2.0  # E = actual − predicted
        assert abs(d["relative_residual"] - 0.25) < 1e-15

    def test_actual_zero_excluded(self):
        # actual=0（非 null）：E=−7 有定义但 e 分母=0 → actual_zero 台账（§0.3）
        status, d = rcm.classify_row(_row("rails", "GND", "b/x", predicted=7, actual=0))
        assert status == "actual_zero"
        assert d["reason"].startswith("actual=0")

    def test_prediction_null_and_actual_null(self):
        status, _ = rcm.classify_row(
            _row("via_budget", "board", "b/x", predicted=None, actual=6,
                 p_reason="not_modelled 原文"))
        assert status == "prediction_null"
        status, d = rcm.classify_row(
            _row("escape_slots", "P1|E", "b/x", predicted=1, actual=None,
                 a_reason="粒度不齐"))
        assert status == "actual_null"
        assert d["reason"] == "粒度不齐"

    def test_unit_guard(self):
        status, _ = rcm.classify_row(
            _row("layer_capacity", "board", "b/x", predicted=60.9, actual=12.0,
                 p_unit="mm2", a_unit="mm"))
        assert status == "unit_mismatch"
        status, _ = rcm.classify_row(
            _row("layer_capacity", "board", "b/x", predicted=60.9, actual=12.0,
                 a_unit=None))
        assert status == "unit_mismatch"

    def test_zero_positive_and_minus_zero_normalization(self):
        # e=0 规范化 +0.0；E=actual−predicted=float 相减零 → 无 −0.0 泄入
        _, d = rcm.classify_row(_row("rails", "N", "b/x", predicted=33, actual=33))
        assert d["relative_residual"] == 0.0
        assert math_copysign_positive(d["relative_residual"])


def math_copysign_positive(v):
    import math
    return math.copysign(1.0, v) > 0


class TestClassifyRows:
    def test_order_insensitive_and_sorted(self):
        rows_a = _e_rows("b/one", [0.1, 0.3])
        rows_b = _e_rows("a/two", [0.2])
        m1, x1 = rcm.classify_rows(rows_a + rows_b)
        m2, x2 = rcm.classify_rows(list(reversed(rows_a + rows_b)))
        assert x1 == [] and x2 == []
        assert m1 == m2  # 输入顺序不敏感（同输入 byte-exact 前提）
        assert [r["board_id"] for r in m1] == ["a/two", "b/one", "b/one"]

    def test_mixed_outcomes_counted(self):
        rows = [
            _row("rails", "A", "b/1", predicted=1, actual=2),      # measurable
            _row("rails", "B", "b/1", predicted=5, actual=0),      # actual_zero
            _row("rails", "C", "b/1", predicted=1, actual=None, a_reason="r"),
            _row("rails", "D", "b/1", predicted=None, actual=3, p_reason="r"),
            _row("rails", "E", "b/1", predicted=1, actual=2, a_unit="mm"),
        ]
        m, x = rcm.classify_rows(rows)
        assert len(m) == 1
        assert sorted(rec["status"] for rec in x) == [
            "actual_null", "actual_zero", "prediction_null", "unit_mismatch"]


# ---------------------------------------------------------------------------
# M4 门控（Q7：门槛=5 固定）
# ---------------------------------------------------------------------------


class TestM4:
    def test_status_boundaries(self):
        assert rcm.m4_status(0) == "not_available"
        assert rcm.m4_status(1) == "not_enough_data"
        assert rcm.m4_status(4) == "not_enough_data"
        assert rcm.m4_status(5) == "ok"

    def test_gate_frozen_constant(self):
        # 冻结口径零回退（P-RC-2）：门槛=5、type-7 分位点
        assert rcm.M4_MIN_ROWS == 5
        assert rcm.MIN_BOARD_ROWS == 5
        assert rcm.QUANTILES_M1 == (0.50, 0.90, 0.95)
        assert rcm.QUANTILE_M2 == 0.95
        assert rcm.SIX_KINDS == ("escape_slots", "corridor", "layer_capacity",
                                 "bus_lane", "via_budget", "power_return_space")


# ---------------------------------------------------------------------------
# M1/M2 双口径 + M2b + M3：手算对账
# ---------------------------------------------------------------------------


def _two_board_setup():
    """板 alpha e=[0.1,0.3,0.5,0.7,0.9]；板 beta e=[0.05,0.2,0.4,0.9,1.0]。

    行级 |e| 排序 = [0.05,0.1,0.2,0.3,0.4,0.5,0.7,0.9,0.9,1.0]。
    """
    rows = _e_rows("b/alpha", [0.1, 0.3, 0.5, 0.7, 0.9])
    rows += _e_rows("b/beta", [0.05, 0.2, 0.4, 0.9, 1.0])
    return rows


class TestM1M2BothPools:
    def test_m1_row_pool_hand(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        out = rcm.m1_row_pool(m)
        assert abs(out["p50"] - 0.45) < 1e-12   # h=4.5 → 0.4+0.5·0.1
        assert abs(out["p90"] - 0.91) < 1e-12   # h=8.1 → x[8]=0.9+0.1·(1.0−0.9)
        assert abs(out["p95"] - 0.955) < 1e-12  # h=8.55 → 0.9+0.55·0.1

    def test_m1_board_pool_hand(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        out = rcm.m1_board_pool(m)
        assert [b["board_id"] for b in out["eligible_boards"]] == ["b/alpha", "b/beta"]
        assert out["eligible_boards"][0]["board_median_abs_e"] == 0.5
        assert out["eligible_boards"][1]["board_median_abs_e"] == 0.4
        # 板值 [0.4, 0.5]（板等权）：P50 h=0.5 → 0.45；P90 h=0.9 → 0.49；
        # P95 h=0.95 → 0.495
        assert abs(out["p50"] - 0.45) < 1e-12
        assert abs(out["p90"] - 0.49) < 1e-12
        assert abs(out["p95"] - 0.495) < 1e-12

    def test_m2_row_and_board_pool_hand(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        row = rcm.m2_row_pool(m)
        assert abs(row["p95"] - 0.955) < 1e-12  # signed 排序同 |e|（全为正）
        # 板级：alpha signed median=0.5；beta=[0.05,0.2,0.4,0.9,1.0] median=0.4
        # 板值 [0.4, 0.5] → P95 h=0.95 → 0.495
        out = rcm.m2_board_pool(m)
        assert abs(out["p95"] - 0.495) < 1e-12

    def test_m2_signed_handles_negatives(self):
        rows = _e_rows("b/alpha", [-0.9, -0.7, -0.5, 0.1, 0.3])
        m, _ = rcm.classify_rows(rows)
        out = rcm.m2_board_pool(m)
        assert out["eligible_boards"][0]["board_median_signed_e"] == -0.5
        assert abs(out["p95"] - (-0.5)) < 1e-12  # 单板：P95=板值本身
        # 行级 P95（signed 排序 [−0.9,−0.7,−0.5,0.1,0.3]，h=3.8 → 0.1+0.8·0.2）
        assert abs(rcm.m2_row_pool(m)["p95"] - 0.26) < 1e-12

    def test_m2b(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        out = rcm.m2b_rate(m)
        assert out == {"n_underprediction": 10, "n_measurable": 10, "rate": 1.0}
        rows = _e_rows("b/alpha", [0.1, -0.3, 0.5, -0.7, 0.9])
        mm, _ = rcm.classify_rows(rows)
        assert rcm.m2b_rate(mm) == {"n_underprediction": 3, "n_measurable": 5,
                                    "rate": 0.6}

    def test_m3_worst_board_argmax(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        out = rcm.m3_worst_board(m)
        assert out == {"board_id": "b/alpha", "n_rows": 5,
                       "board_median_abs_e": 0.5}

    def test_m3_tie_board_id_lexicographic(self):
        # 并列 → board_id 字典序取首（防 tie 漂移）
        rows = _e_rows("b/zzz", [0.1, 0.3, 0.5, 0.7, 0.9])   # median 0.5
        rows += _e_rows("b/aaa", [0.1, 0.2, 0.5, 0.8, 0.9])  # median 0.5
        m, _ = rcm.classify_rows(rows)
        out = rcm.m3_worst_board(m)
        assert out["board_id"] == "b/aaa"
        assert out["board_median_abs_e"] == 0.5

    def test_m3_boards_below_threshold_not_eligible(self):
        rows = _e_rows("b/big", [0.1, 0.2, 0.3, 0.4, 0.5])  # 5 行参评
        rows += _e_rows("b/tiny", [9.9, 9.9, 9.9, 9.9])     # 4 行不参评
        m, _ = rcm.classify_rows(rows)
        out = rcm.m3_worst_board(m)
        assert out["board_id"] == "b/big"

    def test_m3_empty_returns_none(self):
        assert rcm.m3_worst_board([]) is None

    def test_board_pool_no_eligible_board_not_enough_data(self):
        # Q7 执行注记：所有板板内行数 < 门槛 → 板级池无参评板 → not_enough_data
        rows = _e_rows("b/one", [0.1, 0.2, 0.3]) + _e_rows("b/two", [0.4, 0.5])
        m, _ = rcm.classify_rows(rows)
        b1 = rcm.m1_board_pool(m)
        b2 = rcm.m2_board_pool(m)
        assert b1["eligible_boards"] == [] and b1["status"] == "not_enough_data"
        assert "p50" not in b1 and "p95" not in b1
        assert b2["eligible_boards"] == [] and b2["status"] == "not_enough_data"
        assert "p95" not in b2


# ---------------------------------------------------------------------------
# describe_pool 门控与 fail-closed
# ---------------------------------------------------------------------------


class TestDescribePool:
    def test_sixkind_n_zero_not_available(self):
        rows = [
            _row("escape_slots", "P1|E", "b/1", predicted=1, actual=None,
                 a_reason="粒度不齐"),
            _row("escape_slots", "P1|W", "b/1", predicted=2, actual=None,
                 a_reason="粒度不齐"),
        ]
        out = rcm.describe_pool(rows, "escape_slots")
        assert out["m4_status"] == "not_available"
        assert out["n_measurable"] == 0
        assert out["ledger_counts"] == {"prediction_null": 0, "actual_null": 2,
                                        "actual_zero": 0, "unit_mismatch": 0}
        assert "metrics" not in out  # M4 字面：不出任何 M 数值
        assert out["excluded_summary"] == [{
            "status": "actual_null", "n": 2,
            "reason": "粒度不齐"}]

    def test_not_enough_data_reports_n(self):
        rows = _e_rows("b/1", [0.1, 0.2, 0.3], kind="rails")
        out = rcm.describe_pool(rows, "rails")
        assert out["m4_status"] == "not_enough_data"
        assert out["n_measurable"] == 3
        assert "metrics" not in out

    def test_ok_produces_metrics(self):
        rows = _e_rows("b/1", [0.1, 0.2, 0.3, 0.4, 0.5], kind="rails")
        out = rcm.describe_pool(rows, "rails")
        assert out["m4_status"] == "ok"
        assert out["metrics"]["n_measurable"] == 5
        assert abs(out["metrics"]["m1_row_pool"]["p50"] - 0.3) < 1e-12

    def test_auxiliary_note(self):
        rows = _e_rows("b/1", [0.1, 0.2, 0.3, 0.4, 0.5], kind="rails")
        out = rcm.describe_pool(rows, "rails", auxiliary=True)
        assert "纯描述性" in out["note"]

    def test_mixed_kinds_fail_closed(self):
        rows = _e_rows("b/1", [0.1, 0.2, 0.3, 0.4, 0.5])
        rows.append(_row("via_budget", "board", "b/1", predicted=None, actual=3,
                         p_reason="not_modelled"))
        with pytest.raises(ValueError):
            rcm.describe_pool(rows, "rails")

    def test_excluded_rows_never_silently_dropped(self):
        # P-RC-4：n_rows_total = measurable + excluded（禁止删行凑分母）
        rows = _e_rows("b/1", [0.1, 0.2, 0.3, 0.4, 0.5], kind="rails")
        rows.append(_row("rails", "Z", "b/1", predicted=5, actual=0))
        out = rcm.describe_pool(rows, "rails")
        assert out["n_rows_total"] == 6
        assert out["n_measurable"] + sum(out["ledger_counts"].values()) == 6


# ---------------------------------------------------------------------------
# 确定性：byte-exact 重放（P-RC-6）
# ---------------------------------------------------------------------------


class TestLedgerSummary:
    def test_aggregation_and_order(self):
        rows = [
            _row("escape_slots", "P1|E", "b/1", predicted=1, actual=None,
                 a_reason="r1"),
            _row("escape_slots", "P1|W", "b/1", predicted=2, actual=None,
                 a_reason="r1"),
            _row("escape_slots", "P2|N", "b/2", predicted=3, actual=None,
                 a_reason="r2"),
            _row("escape_slots", "P2|S", "b/2", predicted=4, actual=0),
        ]
        _, x = rcm.classify_rows(rows)
        assert rcm.ledger_summary(x) == [
            {"status": "actual_null", "reason": "r1", "n": 2},
            {"status": "actual_null", "reason": "r2", "n": 1},
            {"status": "actual_zero", "reason": rcm.classify_row(rows[3])[1]["reason"],
             "n": 1},
        ]
        assert rcm.board_null_detail(x, "escape_slots") == {"b/1": 2, "b/2": 1}
        assert rcm.board_null_detail(x, "rails") == {}

    def test_describe_pool_exclude_detail_toggle(self):
        rows = _e_rows("b/1", [0.1, 0.2], kind="rails") + [
            _row("rails", "Z", "b/1", predicted=1, actual=None, a_reason="r")]
        agg = rcm.describe_pool(rows, "rails", auxiliary=True)
        assert "excluded_detail" not in agg and agg["excluded_summary"]
        det = rcm.describe_pool(rows, "rails", auxiliary=True, exclude_detail=True)
        assert len(det["excluded_detail"]) == 1
        assert det["excluded_detail"][0]["observation_id"]


class TestDeterminism:
    def test_byte_exact_replay(self):
        rows = _two_board_setup()
        payload1 = rcm.compute_metrics(rcm.classify_rows(rows)[0])
        payload2 = rcm.compute_metrics(rcm.classify_rows(list(reversed(rows)))[0])
        b1 = hashing.canonical_json_bytes(payload1)
        b2 = hashing.canonical_json_bytes(payload2)
        assert b1 == b2  # 输入顺序不敏感，双跑 byte-exact

    def test_floats_json_stable(self):
        m, _ = rcm.classify_rows(_two_board_setup())
        text = hashing.json_dumps(rcm.m1_row_pool(m))
        assert hashing.json_dumps(rcm.m1_row_pool(rcm.classify_rows(_two_board_setup())[0])) == text
        # 数值有限性（canonical JSON 不出 NaN/Infinity）
        assert "NaN" not in text and "Infinity" not in text
