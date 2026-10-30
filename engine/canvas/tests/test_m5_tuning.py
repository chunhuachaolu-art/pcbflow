# -*- coding: utf-8 -*-
"""Lane-M5 单元测试: canvas.tuning 四件（宽度档表/合法档枚举/残差测量/R6 预检）。

- 宽度档表: 同叠层双跑字节等 + 层间差异>0 + 档单调 + plane/不可用层不入表 +
  stripline 窄条域越界 fail-closed + 真板叠层口径。
- 合法档枚举: 确定性排序 + 长度效应闭式（2·amp·count / 2·|offset|）+ 不可
  达面（超长/容差带外）空表。
- 残差: 无组/未知网/无基线段 fail-closed。
- R6 预检: 净空/进 zone 两面 + 无基线段 fail-closed + plane 层集口径。
"""
import pytest

from v5 import canonical
from v5 import drc

from canvas import tuning as ct
from canvas.tests.test_k1_fixtures import real_board, run_batch
from canvas.tests.test_m5_fixtures import m5_state, M5_BUDGET


def _layer(lid, kind="signal", available=True):
    return {"id": lid, "kind": kind, "preferred_direction": "any",
            "available": available}


STACK_4L = [_layer("F.Cu"), _layer("In1.Cu"), _layer("GND.Cu", kind="plane"),
            _layer("B.Cu")]


# ---------------------------------------------------------------- 宽度档表

def test_width_table_double_run_byte_equal():
    a = ct.width_table(STACK_4L)
    b = ct.width_table(STACK_4L)
    assert canonical.canonical_json(a) == canonical.canonical_json(b)


def test_width_table_layer_difference():
    """层间差异>0: 外层（微带 H=1.5）恒宽于内层（带状线 b=1.0，εr 同）——
    同目标阻抗下带状线介质全填充 εeff 更高、需更宽线。"""
    tab = ct.width_table(STACK_4L)
    assert set(tab) == {"F.Cu", "In1.Cu", "B.Cu"}
    for cls in ("min", "nom", "max"):
        assert tab["F.Cu"][cls] - tab["In1.Cu"][cls] > 0.0, cls
        assert tab["B.Cu"][cls] - tab["In1.Cu"][cls] > 0.0, cls
        assert tab["F.Cu"][cls] > 0.0 and tab["In1.Cu"][cls] > 0.0


def test_width_table_class_monotonic():
    """min(60Ω) < nom(50Ω) < max(40Ω)：目标阻抗越低线越宽（两模型同向）。"""
    tab = ct.width_table(STACK_4L)
    for lid, row in tab.items():
        assert row["min"] < row["nom"] < row["max"], lid


def test_width_table_skips_plane_and_unavailable():
    tab = ct.width_table([_layer("F.Cu"), _layer("PWR.Cu", kind="plane"),
                          _layer("B.Cu", available=False)])
    assert set(tab) == {"F.Cu"}


def test_width_table_stripline_range_fail_closed():
    """stripline 近似越窄条域（W/b ≥ 0.35 需宽条式）= 越出近似模型边界，
    fail-closed 抛错不外推（工程经验近似边界纪律）。"""
    with pytest.raises(ValueError, match="窄条域"):
        ct.width_table(STACK_4L, classes={"nom": 20.0})


def test_width_table_real_board_stackup():
    """真板叠层（badgeleds F.Cu/B.Cu 双外层）: 两层同值（同为微带模型），
    档键集 = {min,nom,max}。"""
    board, _path, _sha = real_board()
    tab = ct.width_table(board["stackup"])
    assert set(tab) == {"F.Cu", "B.Cu"}
    assert canonical.canonical_json(tab["F.Cu"]) == \
        canonical.canonical_json(tab["B.Cu"])
    assert set(tab["F.Cu"]) == {"min", "nom", "max"}


# ---------------------------------------------------------------- 合法档枚举

def test_legal_options_deterministic_order():
    """排序钉死: (added_mm 升序, kind, params)——同 added=1.0 内
    accordion 先于 detour，detour 参数序 −0.5 先于 +0.5。"""
    opts = ct.legal_options(8.0, 9.0, 0.3)
    assert [(o["kind"], o["params"]) for o in opts] == [
        ("accordion", {"amp_mm": 0.5, "count": 1}),
        ("detour", {"offset_mm": -0.5}),
        ("detour", {"offset_mm": 0.5}),
    ]
    keys = [(o["added_mm"], o["kind"]) for o in opts]
    assert keys == sorted(keys)


def test_legal_options_length_effect_closed_form():
    """长度效应闭式（tuning_polyline_mm 公式单源推导）: accordion 净增
    2·amp·count、detour 净增 2·|offset|；逐档落容差带内。"""
    opts = ct.legal_options(8.0, 9.5, 0.6)     # added ∈ [0.9, 2.1]
    seen = set()
    for o in opts:
        if o["kind"] == "accordion":
            assert abs(o["added_mm"] - 2 * o["params"]["amp_mm"]
                       * o["params"]["count"]) < 1e-12
        else:
            assert abs(o["added_mm"] - 2 * abs(o["params"]["offset_mm"])) < 1e-12
        assert abs(o["residual_after_mm"]) <= 0.6 + 1e-12
        seen.add(o["kind"])
    assert seen == {"accordion", "detour"}


def test_legal_options_empty_on_overshoot():
    """基线超目标且越容差: accordion/detour 只加长 → 无合法档（不产动作）。"""
    assert ct.legal_options(8.0, 7.0, 0.3) == []


def test_legal_options_empty_when_band_unreachable():
    """容差带内无可行量化档（需求 added∈[0.5,0.6]，量化档离散 1.0/2.0/…）→ 空表。"""
    assert ct.legal_options(8.0, 8.55, 0.05) == []


def test_legal_options_zero_tol_exact_hit():
    opts = ct.legal_options(8.0, 9.0, 0.0)
    assert opts and all(o["added_mm"] == 1.0 for o in opts)


# ---------------------------------------------------------------- 残差测量

def test_residual_unknown_group_fail_closed():
    st = m5_state()
    with pytest.raises(KeyError):
        ct.residual(st, "NO-SUCH-GROUP", M5_BUDGET["length_groups"])


def test_residual_unknown_net_fail_closed():
    st = m5_state()
    groups = {"LG-BAD": {"nets": ["NET-NOPE"], "target_mm": 9.0, "tol_mm": 0.3}}
    with pytest.raises(KeyError):
        ct.residual(st, "LG-BAD", groups)


def test_residual_no_baseline_fail_closed():
    st = m5_state()
    run_batch(st, [{"action": "ripup", "net_id": "NET-T2"}])
    with pytest.raises(ValueError, match="无基线段"):
        ct.residual(st, "LG-BOXED", M5_BUDGET["length_groups"])


def test_residual_baseline_measurement():
    st = m5_state()
    r = ct.residual(st, "LG-OPEN", M5_BUDGET["length_groups"])
    assert r["target_mm"] == 9.0
    assert r["actual_mm"] == 8.0          # 基线=8mm 直线（instantiate 几何）
    assert r["residual_mm"] == 1.0
    assert r["per_net"]["NET-T1"]["tuned"] is False


# ---------------------------------------------------------------- R6 预检

def test_r6_violations_faces():
    st = m5_state()
    assert ct.r6_violations(st, "NET-T1", "detour", {"offset_mm": -0.5}) == []
    blocked = ct.r6_violations(st, "NET-T1", "detour", {"offset_mm": 0.5})
    assert [(v["rule"], v["subjects"][1]) for v in blocked] == [("R6", "Z1")]
    acc = ct.r6_violations(st, "NET-T1", "accordion",
                           {"amp_mm": 0.5, "count": 1})
    assert acc and acc[0]["rule"] == "R6" and acc[0]["subjects"][1] == "Z1"


def test_r6_violations_no_baseline_fail_closed():
    st = m5_state()
    run_batch(st, [{"action": "ripup", "net_id": "NET-T1"}])
    with pytest.raises(ValueError, match="无基线段"):
        ct.r6_violations(st, "NET-T1", "detour", {"offset_mm": -0.5})


def test_r6_real_board_no_zones_transcription():
    """真板 zones=[]（审计事实）→ R6 keepout 预检恒净空（zone_rects 透传空
    集——validate_full 与本预检同一透传源）; plane 层亦空。"""
    from canvas import validate as cval
    board, _path, _sha = real_board()
    sensitive, keepout = cval.zone_rects(board)
    assert (sensitive, keepout) == ([], [])
    assert board["zones"] == []


def test_option_actual_len_mm_mid_leg_fold_disclosure():
    """闭式精确性披露的可执行对照: accordion 腿中折返实算长 > 闭式
    2·amp·count（回退段额外计入）; 腿起点折返（count=1 于 16×0.5 腿基线
    s=total/2 恰落腿界）实算 == 闭式; detour 恒精确。"""
    st = m5_state(zones=False)
    exact_c1 = ct.option_actual_len_mm(st, "NET-T1", "accordion",
                                       {"amp_mm": 0.5, "count": 1})
    exact_c2 = ct.option_actual_len_mm(st, "NET-T1", "accordion",
                                       {"amp_mm": 0.5, "count": 2})
    assert exact_c1 == 8.0 + 1.0            # 腿起点折返: 闭式精确
    assert exact_c2 == 11.0                 # 两腿中折返: +2·(pitch−r) 额外
    assert exact_c2 > 8.0 + 2.0
    assert ct.option_actual_len_mm(st, "NET-T1", "detour",
                                   {"offset_mm": -0.5}) == 9.0


def test_r6_same_source_binding_equivalence():
    """r6_violations ≡ 直接调 v5.drc.check_keepout（同一判定器，无第二几何/
    判定路径）: 候选铜经 instantiate.tuning_copper、zones 经
    validate.zone_rects（validate_full 同一透传）。"""
    from canvas import instantiate as inst
    from canvas import protocol as cpr
    from canvas import validate as cval
    st = m5_state()
    params = {"offset_mm": 0.5}
    fake = {"shape_id": "cand:tun:r6", "net_id": "NET-T1", "group_id": "G",
            "kind": "detour", "grid": cpr.tuning_base_grid(st, "NET-T1"),
            "params": dict(params)}
    cu = inst.tuning_copper(st, fake)
    _sens, keepout = cval.zone_rects(st.board)
    direct = [v.as_dict() for v in
              drc.check_keepout([cu], keepout, ct.plane_layers(st.board))]
    assert direct == ct.r6_violations(st, "NET-T1", "detour", params)


def test_plane_layers_vocab():
    board, _path, _sha = real_board()
    assert ct.plane_layers(board) == ()          # badgeleds 无 plane 层
    stacked = {"stackup": STACK_4L}
    assert ct.plane_layers(stacked) == ("GND.Cu",)
