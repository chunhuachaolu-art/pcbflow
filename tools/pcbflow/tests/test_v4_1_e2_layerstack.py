"""pcbflow.v4_1 E2 层栈/层对/贯通孔跨度语义测试（任务书 §3 E2）。"""

from __future__ import annotations

import pytest

from pcbflow.v4_1.board_parse import parse_board_text
from pcbflow.v4_1.board_parse_alt import parse_board_text_alt
from pcbflow.v4_1.geometry import GeomItem
from pcbflow.v4_1.layerstack import (DEFAULT_STACK_4, LayerStack,
                                     LayerStackError, is_copper_layer_name,
                                     via_span_layers)
from pcbflow.v4_1.netclasses import NetClass, NetClassTable
from pcbflow.v4_1.precheck import AdvisoryPrecheckV41, build_geom_items

STACK4 = list(DEFAULT_STACK_4)


# ---------------------------------------------------------------- 层栈基元

def test_stack4_via_spans():
    st = LayerStack(STACK4)
    assert st.via_span("F.Cu", "B.Cu") == STACK4           # 贯通=全栈
    assert st.via_span("F.Cu", "In2.Cu") == ["F.Cu", "In1.Cu", "In2.Cu"]
    assert st.via_span("In1.Cu", "B.Cu") == ["In1.Cu", "In2.Cu", "B.Cu"]
    assert st.via_span("In1.Cu", "In2.Cu") == ["In1.Cu", "In2.Cu"]
    assert st.via_span("B.Cu", "F.Cu") == STACK4           # 写出顺序无关
    assert st.via_span("In2.Cu", "F.Cu") == ["F.Cu", "In1.Cu", "In2.Cu"]


def test_stack4_pairs_and_roles():
    st = LayerStack(STACK4)
    assert st.adjacent_pairs() == [("F.Cu", "In1.Cu"),
                                   ("In1.Cu", "In2.Cu"),
                                   ("In2.Cu", "B.Cu")]
    assert st.is_outer("F.Cu") and st.is_outer("B.Cu")
    assert st.is_inner("In1.Cu") and st.is_inner("In2.Cu")
    assert st.layers_between("F.Cu", "B.Cu") == ["In1.Cu", "In2.Cu"]
    assert st.layers_between("In1.Cu", "In1.Cu") == []
    assert st.via_spans_all("F.Cu", "B.Cu") is True
    assert st.via_spans_all("F.Cu", "In2.Cu") is False


def test_stack_fail_closed():
    with pytest.raises(LayerStackError):
        LayerStack([])                                     # 空栈
    with pytest.raises(LayerStackError):
        LayerStack(["F.Cu", "F.Cu"])                       # 重复
    with pytest.raises(LayerStackError):
        LayerStack(["F.Cu", "Edge.Cuts"])                  # 非铜层名
    with pytest.raises(LayerStackError):
        LayerStack(STACK4).via_span("F.Cu", "In3.Cu")      # 不在栈内
    with pytest.raises(LayerStackError):
        via_span_layers("F.Cu", "B.Cu", [])                # 空栈


def test_is_copper_layer_name():
    assert is_copper_layer_name("F.Cu")
    assert is_copper_layer_name("In6.Cu")
    assert not is_copper_layer_name("*.Cu")                # 通配符非具体层
    assert not is_copper_layer_name("Edge.Cuts")
    assert not is_copper_layer_name("F.Mask")


# ---------------------------------------------------------------- 解析集成

def _board(via_layers):
    return ('(kicad_pcb (version 20260206)\n'
            '  (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) '
            '(2 "In2.Cu" signal) (31 "B.Cu" signal))\n'
            '  (via (at 10 20) (size 0.6) (drill 0.3) (layers %s) '
            '(net "N1") (uuid "v1"))\n'
            ')\n' % via_layers)


@pytest.mark.parametrize("span,expected", [
    # 解析产物 layers 为排序表（E1 语义保留；跨度集合=栈序闭区间展开）
    ('"F.Cu" "B.Cu"', ["B.Cu", "F.Cu", "In1.Cu", "In2.Cu"]),
    ('"F.Cu" "In2.Cu"', ["F.Cu", "In1.Cu", "In2.Cu"]),
    ('"In1.Cu" "B.Cu"', ["B.Cu", "In1.Cu", "In2.Cu"]),
    ('"In1.Cu" "In2.Cu"', ["In1.Cu", "In2.Cu"]),
    ('"In2.Cu" "In1.Cu"', ["In1.Cu", "In2.Cu"]),          # 反序写出
])
def test_via_span_expansion_both_paths(span, expected):
    a = parse_board_text(_board(span))
    b = parse_board_text_alt(_board(span))
    assert a["vias"][0]["layers"] == expected
    assert b["vias"][0]["layers"] == expected              # 交叉一致


def test_via_unknown_layer_fail_closed_both_paths():
    for fn in (parse_board_text, parse_board_text_alt):
        with pytest.raises(ValueError):
            fn(_board('"F.Cu" "In9.Cu"'))


def test_via_through_e1_semantics_unchanged():
    """(F.Cu B.Cu) 全栈展开=E1 既有行为（2 层板亦然）。"""
    board2 = ('(kicad_pcb (version 20260206)\n'
              '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n'
              '  (via (at 1 1) (size 0.6) (drill 0.3) '
              '(layers "F.Cu" "B.Cu") (net "N") (uuid "v"))\n)\n')
    assert parse_board_text(board2)["vias"][0]["layers"] == ["B.Cu", "F.Cu"]


# ---------------------------------------------------------------- 预检集成

def _th_board(via_layers):
    """盲/埋孔 via 作为唯一障碍 + 探针段（距 via 中心 0.5mm）。

    via size 0.6（r=0.3），探针宽 0.2（r=0.1）→ clearance=0.1 < 0.2：
    跨度内层=违例；跨度外层=clean（多层跨度语义端到端）。
    """
    return ('(kicad_pcb (version 20260206)\n'
            '  (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) '
            '(2 "In2.Cu" signal) (31 "B.Cu" signal))\n'
            '  (via (at 10 20) (size 0.6) (drill 0.3) (layers %s) '
            '(net "NV") (uuid "v1"))\n'
            ')\n' % via_layers)


def _table():
    return NetClassTable(
        {"Default": NetClass("Default", 0.2, 0.25)}, {}, [],
        "declared_for_test")


def _probe_precheck(via_layers):
    parsed = parse_board_text(_th_board(via_layers))
    items = build_geom_items(parsed)
    via = next(it for it in items if it.src.get("uuid") == "v1")
    pre = AdvisoryPrecheckV41(items, _table())
    return via, pre


def test_blind_via_intermediate_layer_obstacle_end_to_end():
    """盲孔 (F.Cu In2.Cu)：In1（中间层）与 In2（端点层）违例、B.Cu clean。"""
    via, pre = _probe_precheck('"F.Cu" "In2.Cu"')
    assert via.layers == {"F.Cu", "In1.Cu", "In2.Cu"}
    r_in1 = pre.check_segment("NX", "In1.Cu", 0.2, 5, 20.5, 15, 20.5)
    hit = [v for v in r_in1["violations"] if v["item_ref"] == "v1"]
    assert hit and hit[0]["flag_class"] == "hard_violation"
    assert hit[0]["pred_clearance_mm"] == pytest.approx(0.1)
    r_in2 = pre.check_segment("NX", "In2.Cu", 0.2, 5, 20.5, 15, 20.5)
    assert any(v["item_ref"] == "v1"
               and v["flag_class"] == "hard_violation"
               for v in r_in2["violations"])
    r_b = pre.check_segment("NX", "B.Cu", 0.2, 5, 20.5, 15, 20.5)
    assert r_b["verdict"] == "clean"                       # 跨度外无障碍


def test_buried_via_span_excludes_outer():
    """埋孔 (In1.Cu In2.Cu)：In1/In2 违例、F.Cu/B.Cu clean。"""
    via, pre = _probe_precheck('"In1.Cu" "In2.Cu"')
    assert via.layers == {"In1.Cu", "In2.Cu"}
    for layer in ("In1.Cu", "In2.Cu"):
        r = pre.check_segment("NX", layer, 0.2, 5, 20.5, 15, 20.5)
        assert any(v["item_ref"] == "v1"
                   and v["flag_class"] == "hard_violation"
                   for v in r["violations"]), layer
    for layer in ("F.Cu", "B.Cu"):
        r = pre.check_segment("NX", layer, 0.2, 5, 20.5, 15, 20.5)
        assert r["verdict"] == "clean", layer


def test_geomitem_via_span_layers_direct():
    it = GeomItem.from_via("N", 0.6, ["F.Cu", "In1.Cu", "In2.Cu"], 3, 4)
    assert it.layers == {"F.Cu", "In1.Cu", "In2.Cu"}
    assert LayerStack(STACK4).as_dict()["layer_count"] == 4
