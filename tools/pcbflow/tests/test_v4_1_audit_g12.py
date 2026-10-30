"""pcbflow.v4_1 G1.2 构造对拍集审计测试（漏报率=0 + 误报台账 + 交叉一致）。"""

from __future__ import annotations

import pytest

from pcbflow.v4_1 import CONSERVATIVE_BAND_MM
from pcbflow.v4_1.audit import construct_cases, run_audit


@pytest.fixture(scope="module")
def audit():
    return run_audit()


def test_constructed_set_shape(audit):
    a = audit
    assert a["case_count"] >= 25
    assert a["truth_counts"]["violation"] >= 10
    assert a["truth_counts"]["legal"] >= 8
    assert a["truth_counts"]["conservative_band"] >= 3
    # 三类形状覆盖
    shapes = set()
    for case in construct_cases():
        for p in case["pads"]:
            shapes.add(p["shape"])
    assert {"circle", "oval", "rect", "roundrect"} <= shapes


def test_gate_false_negative_zero(audit):
    a = audit["false_negatives"]
    assert a["precheck"]["count"] == 0
    assert a["precheck"]["rate"] == 0.0
    assert a["checker"]["count"] == 0
    assert a["checker"]["rate"] == 0.0


def test_gate_cross_disagreement_zero(audit):
    assert audit["cross_disagreements"] == []


def test_false_positive_ledger_registered(audit):
    """带内边界例=设计内保守行为 -> 误报台账逐条登记（G1.3，不设门）。"""
    fp = audit["false_positives"]
    band_ids = {"round_track_edge_band", "oval_track_edge_band",
                "roundrect_track_edge_band"}
    for eng in ("precheck", "checker"):
        ids = {e["case_id"] for e in fp[eng]}
        assert band_ids <= ids, "%s 台账缺带内例: %r" % (eng, ids)
        for e in fp[eng]:
            if e["case_id"] in band_ids:
                assert e["kind"] == "conservative_band_by_design"
                assert e["expected_clearance_mm"] >= 0.2
                assert e["expected_clearance_mm"] < 0.2 + \
                    CONSERVATIVE_BAND_MM


def test_pred_matches_expected_within_bounds(audit):
    """非重叠例：预检=精确引擎（<=0.002mm 数值容差）；checker=外切超集
    （pred 系统性略低，上界=双方最大半径 x (1/cos(pi/32)-1) x 2 ~ 0.003mm
    ——pad 半径 0.5 与走线半宽的外切多边形凸出之和）。"""
    for row in audit["cases"]:
        exp = row["expected_clearance_mm"]
        pv = row["precheck"]["min_foreign_clearance_mm"]
        cv = row["checker"]["min_foreign_clearance_mm"]
        assert pv is not None and cv is not None
        if exp > 0.0:
            assert abs(pv - exp) <= 0.002, row["case_id"]
            assert exp - 0.004 <= cv <= exp + 1e-9, \
                "%s checker pred %r vs exp %r" % (row["case_id"], cv, exp)
        else:
            # 重叠例：预检为负（核距下界），checker 为 0.0 哨兵（overlap 旗标）
            assert pv <= 0.0
            assert cv == 0.0


def test_truth_classification_consistency(audit):
    for row in audit["cases"]:
        exp = row["expected_clearance_mm"]
        truth = row["truth"]
        if exp < 0.2:
            assert truth == "violation"
        elif exp < 0.2 + CONSERVATIVE_BAND_MM:
            assert truth == "conservative_band"
        else:
            assert truth == "legal"


def test_old_model_blindspot_case_present(audit):
    rows = {r["case_id"]: r for r in audit["cases"]}
    assert "old_model_blindspot_oval" in rows
    r = rows["old_model_blindspot_oval"]
    assert r["truth"] == "violation"
    assert r["precheck"]["verdict"] == "violation"
    assert r["checker"]["verdict"] == "violation"
    assert r["expected_clearance_mm"] == pytest.approx(0.125)
