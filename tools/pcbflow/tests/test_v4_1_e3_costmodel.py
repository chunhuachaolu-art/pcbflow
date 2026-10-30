"""tests/test_v4_1_e3_costmodel -- E3 via 分层成本模型单元/合同测试（G3.3 支撑）。

依据：exec/V4.1-ROUTER-ENGINEERING-TASKBOOK-2026-09-12.md §3 E3；
prereg-e3.json → cost_model_defaults（tolerance/默认参数依据）。
"""

from __future__ import annotations

import pytest

from pcbflow.v4_1.costmodel import (DEFAULT_COST_PARAMS, FLAT_VIA_MM,
                                    CostModelError, ViaCostModel,
                                    via_span_class)
from pcbflow.v4_1.layerstack import LayerStackError

STACK4 = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
STACK2 = ["F.Cu", "B.Cu"]


def test_defaults_match_prereg():
    m = ViaCostModel(STACK4)
    assert m.params["through_mm"] == DEFAULT_COST_PARAMS["through_mm"] == 8.0
    assert m.params["adjacent_blind_mm"] == 4.0
    assert m.params["per_extra_gap_mm"] == 1.5
    assert m.params["clamp_partial_to_through"] is True


def test_4layer_cost_table():
    m = ViaCostModel(STACK4)
    assert m.cost_mm("F.Cu", "B.Cu") == 8.0          # 贯通锚
    assert m.cost_mm("B.Cu", "F.Cu") == 8.0          # 写出顺序无关
    assert m.cost_mm("F.Cu", "In1.Cu") == 4.0        # 相邻盲
    assert m.cost_mm("In1.Cu", "In2.Cu") == 4.0      # 埋（相邻）
    assert m.cost_mm("F.Cu", "In2.Cu") == 5.5        # 4+1.5*1 深盲
    assert m.cost_mm("In1.Cu", "B.Cu") == 5.5
    # 单深盲 < 贯通 < ... 且单深盲(5.5) < 两相邻盲(8.0) → In2 单跳可达
    assert m.cost_mm("F.Cu", "In2.Cu") < ViaCostModel(STACK4).cost_mm("F.Cu", "B.Cu")


def test_two_layer_degeneracy_is_v1_anchor():
    """2 层栈唯一跨度=贯通 → 分层默认退化为 v1 常数 8.0（G3.2 连续性根）。"""
    m = ViaCostModel(STACK2)
    assert m.cost_mm("F.Cu", "B.Cu") == FLAT_VIA_MM == 8.0
    f = ViaCostModel(STACK2, flat=True)
    assert f.cost_mm("F.Cu", "B.Cu") == 8.0


def test_flat_model_is_v1_equivalent():
    f = ViaCostModel(STACK4, flat=True)
    for a in STACK4:
        for b in STACK4:
            if a != b:
                assert f.cost_mm(a, b) == 8.0


def test_cost_cells_integral_and_conversions():
    m = ViaCostModel(STACK4)
    assert m.cost_cells("F.Cu", "B.Cu", 0.25) == 32   # v1 VIA_COST_CELLS
    assert m.cost_cells("F.Cu", "In1.Cu", 0.25) == 16
    assert m.cost_cells("F.Cu", "In2.Cu", 0.25) == 22
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": 8.0001,
                                     "adjacent_blind_mm": 4.0,
                                     "per_extra_gap_mm": 1.5}).cost_cells(
            "F.Cu", "B.Cu")


def test_partial_clamped_to_through_on_deep_stacks():
    stack6 = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
    m = ViaCostModel(stack6)
    # gap5 部分跨度：4+1.5*4=10 > 8 → 截断到 through
    assert m.gaps("F.Cu", "B.Cu") == 5
    assert m.cost_mm("F.Cu", "In4.Cu") == 8.0  # 4+6=10 → clamp
    assert m.cost_mm("F.Cu", "In1.Cu") == 4.0
    # 全部部分跨度 <= 贯通（单调可替代）
    for i in range(1, 5):
        assert m.cost_mm("F.Cu", stack6[i]) <= 8.0


def test_fail_closed_params():
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": -1.0,
                                     "adjacent_blind_mm": 4.0})
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": 4.0,
                                     "adjacent_blind_mm": 9.0})  # 单调性破坏
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": float("nan"),
                                     "adjacent_blind_mm": 4.0})
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": True,
                                     "adjacent_blind_mm": 4.0})
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, flat=False, params={"flat_via_mm": 8.0})
    with pytest.raises(CostModelError):
        ViaCostModel(STACK4, params={"through_mm": 8.0,
                                     "adjacent_blind_mm": 4.0,
                                     "per_extra_gap_mm": -0.5})


def test_fail_closed_layers():
    with pytest.raises(LayerStackError):
        ViaCostModel(["F.Cu", "F.Silk"])   # 非铜层名
    with pytest.raises(LayerStackError):
        ViaCostModel(["F.Cu", "F.Cu"])     # 重复
    with pytest.raises(LayerStackError):
        ViaCostModel([])                   # 空栈
    m = ViaCostModel(STACK4)
    with pytest.raises(LayerStackError):
        m.cost_mm("F.Cu", "Silk")   # 非栈内层 fail-closed
    with pytest.raises(LayerStackError):
        ViaCostModel(STACK4, flat=True).cost_mm("F.Cu", "Edge.Cuts")


def test_span_class_classification():
    assert via_span_class("F.Cu", "B.Cu", STACK4) == "through"
    assert via_span_class("B.Cu", "F.Cu", STACK4) == "through"
    assert via_span_class("F.Cu", "In1.Cu", STACK4) == "blind_adjacent"
    assert via_span_class("B.Cu", "In2.Cu", STACK4) == "blind_adjacent"
    assert via_span_class("F.Cu", "In2.Cu", STACK4) == "blind_deep"
    assert via_span_class("In1.Cu", "B.Cu", STACK4) == "blind_deep"
    assert via_span_class("In1.Cu", "In2.Cu", STACK4) == "buried"
    # 2 层栈唯一跨度即贯通
    assert via_span_class("F.Cu", "B.Cu", STACK2) == "through"


def test_as_dict_and_table_deterministic():
    m = ViaCostModel(STACK4)
    t1 = m.via_costs_table_cells()
    t2 = ViaCostModel(STACK4).via_costs_table_cells()
    assert t1 == t2
    assert t1["F.Cu|B.Cu"] == 32 and t1["F.Cu|In1.Cu"] == 16
    assert m.as_dict()["copper_layers"] == STACK4


def test_objective_via_cost_diagnostic():
    m = ViaCostModel(STACK4)
    via = {"from_layer": "F.Cu", "to_layer": "In2.Cu"}
    assert m.objective_via_cost_mm(via) == 5.5
