"""编译器单元测试：锚点漂移守卫、GROUPS 提取、类匹配。零落盘。"""

import pytest

from pcbflow import compile_cmd, compile_seeds


def test_seeds_unique_ids_in_range():
    ids = [s["id"] for s in compile_seeds.SEEDS]
    assert len(ids) == len(set(ids))
    lo, hi = (40, 60)
    assert lo <= len(ids) <= hi
    assert ids == [f"C-{i + 1:04d}" for i in range(len(ids))]


def test_anchor_drift_detected():
    """spec 文本漂移（锚点行被改）→ verify_anchors 必须报失败。"""
    good = ["x" * 5 for _ in range(200)]
    good[28] = "| PWR_5V | 5V, 5V_HDR, 5V_USB, VBUS_RAW | ..."  # 第 29 行
    texts = {"routing": good, "placement": ["y" * 5 for _ in range(200)]}
    # 用完整种子表会因 placement 无内容而误报，这里只验证机制：改掉一行后
    # 单种子检查失败。
    line = None
    for s in compile_seeds.SEEDS:
        if s["id"] == "C-0001":
            line = s["line"]
            break
    mutated = list(good)
    mutated[line - 1] = "| PWR_5V(漂移) | ..."
    from pcbflow.compile_cmd import verify_anchors as _v
    # 构造仅含 C-0001 的种子视图
    import pcbflow.compile_seeds as seeds_mod
    orig = seeds_mod.SEEDS
    try:
        seeds_mod.SEEDS = [s for s in orig if s["id"] == "C-0001"]
        assert _v({"routing": mutated, "placement": good}) == []
        assert _v({"routing": good, "placement": good}) == []
        hits = _v({"routing": mutated[:line - 1] + ["DRIFT"] + mutated[line:],
                   "placement": good})
        assert len(hits) == 1 and hits[0]["constraint"] == "C-0001"
    finally:
        seeds_mod.SEEDS = orig


def test_extract_script_groups_comprehensions():
    script = (
        "GROUPS = {\n"
        "  'G_X': {'ref': 'CLK', 'target': 2.5, 'limit': 5.0,\n"
        "          'nets': [f'X{i}' for i in range(3)] + ['NBL']},\n"
        "  'G_Y': {'ref': None, 'target': 1.0, 'limit': 2.5, 'nets': ['A', 'B']},\n"
        "}\n"
    )
    g = compile_cmd.extract_script_groups(script)
    assert g["G_X"]["nets"] == ["X0", "X1", "X2", "NBL"]
    assert g["G_X"]["ref"] == "CLK" and g["G_X"]["limit"] == 5.0
    assert g["G_Y"]["ref"] is None


def test_extract_rejects_unsupported():
    with pytest.raises(ValueError):
        compile_cmd.extract_script_groups("GROUPS = {'a': __import__('os')}")


def test_match_class_priority_and_catch_all():
    m = compile_cmd._match_class
    assert m("USB_DP_C") == "USB_DIFF"       # 具体类含 _C
    assert m("FMC_A12") == "FMC_ADDR"        # AMB-1 已批（2026-08-29）：A12 纳入
    assert m("FMC_A11") == "FMC_ADDR"
    assert m("FMC_D15") == "FMC_DATA_H" and m("FMC_D7") == "FMC_DATA_L"
    assert m("LTDC_R4") == "LTDC"            # 前缀通配
    assert m("VREF+") == "ANLG"              # '+' 需转义
    assert m("GPIO_PC0") == "SIG_DEFAULT"
    assert m("GND") == "GND"


def test_expected_spec_members_consistent_with_seeds():
    """转录的九组 spec 成员与种子的组覆盖对齐（防两处漂移）。"""
    groups = {s["scope"]["group"] for s in compile_seeds.SEEDS
              if s["domain"] == "LENGTH"}
    assert groups == set(compile_cmd.EXPECTED_SPEC_GROUP_MEMBERS)
