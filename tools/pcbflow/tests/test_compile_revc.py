"""Rev-C 集成测试（输入缺失时跳过）+ 确定性 byte-exact 验证。

核心产物含中文 → 本文件显式 UTF-8（模块级声明仅提示，Python3 默认 UTF-8）。
"""

import os

import pytest

from pcbflow import compile_cmd, config, envelope

INPUTS_OK = all(os.path.exists(p) for p in (
    config.ROUTING_SPEC, config.PLACEMENT_SPEC,
    config.REVC_NETLIST, config.LENGTH_REPORT_PY))

pytestmark = pytest.mark.skipif(not INPUTS_OK, reason="Rev-C inputs not present")


@pytest.fixture(scope="module")
def products():
    return compile_cmd.build_products()


def test_gate_constraint_count(products):
    m = products["envelope"]["obj"]["metrics"]
    lo, hi = config.GATE_CONSTRAINT_COUNT
    assert lo <= m["constraint_count"] <= hi
    assert m["constraint_count_gate"]["pass"] is True


def test_nine_groups_all_bound(products):
    gate = products["envelope"]["obj"]["data"]["gate"]
    assert gate["nine_groups"]["bound"] == 9
    # 三个已知差异组已按 2026-08-29 裁决 resolved_with_diff（diff 保留不隐藏）；其余 match
    assert gate["nine_groups"]["ambiguous"] == []
    assert sorted(gate["nine_groups"]["resolved_with_diff"]) == \
        ["G_FMC_A", "G_LTDC", "G_USB"]
    assert len(gate["nine_groups"]["match"]) == 6


def test_known_ambiguities_registered(products):
    cov = products["coverage"]["obj"]
    amb = {a["id"]: a for a in cov["ambiguous_selectors"]}
    assert {"AMB-1", "AMB-2", "AMB-3", "AMB-4"} == set(amb)
    for a in amb.values():  # FA2 消费裁决：全部 resolved + 批准记录
        assert a["status"] == "resolved"
        assert a["approver"] and a["decided_on"] == "2026-08-29" and a["review"]
    g = {e["group"]: e for e in cov["nine_group_comparison"]}
    assert g["G_FMC_A"]["diff"]["script_only"] == ["FMC_A12"]
    assert g["G_LTDC"]["diff"]["spec_claimed_count"] == 23
    assert g["G_LTDC"]["diff"]["script_count"] == 19
    assert g["G_USB"]["diff"]["spec_only"] == ["USB_DM_C", "USB_DP_C"]
    # canonical 成员按裁决落地（diff 仍在，canonical 与 diff 并存）
    assert g["G_FMC_A"]["canonical_members"] is not None
    assert "FMC_A12" in g["G_FMC_A"]["canonical_members"]
    assert len(g["G_LTDC"]["canonical_members"]) == 19
    assert g["G_USB"]["canonical_members"] == \
        ["USB_DM", "USB_DM_C", "USB_DP", "USB_DP_C"]
    assert all(g[k]["status"] == "resolved_with_diff"
               for k in ("G_FMC_A", "G_LTDC", "G_USB"))


def test_ruling_amb1_applied_to_binding(products):
    """AMB-1：FMC_A12 归 FMC_ADDR，退出兜底单列。"""
    cov = products["coverage"]["obj"]
    assert "FMC_A12" in cov["net_class_binding"]["FMC_ADDR"]["members"]
    assert cov["net_class_binding"]["FMC_ADDR"]["count"] == 15
    assert "FMC_A12" not in cov["catch_all_only_nets"]
    assert cov["totals"]["net_classes"] == 18


def test_ruling_amb3_usb_segments_in_seed(products):
    """AMB-3：C-0019 带两段测量约定；C-0028 scope 注记更新。"""
    cons = products["constraints"]["obj"]["constraints"]
    c19 = next(c for c in cons if c["id"] == "C-0019")
    seg = c19["params"]["segments"]
    assert seg["mcu_side"]["nets"] == ["USB_DP", "USB_DM"]
    assert seg["connector_side"]["nets"] == ["USB_DP_C", "USB_DM_C"]
    c28 = next(c for c in cons if c["id"] == "C-0028")
    assert "已批" in c28["scope"]["note"]


def test_status_blocked_by_missing_sources(products):
    """歧义已全部裁决闭环；剩余 blocked 原因=缺失源（阻签核不阻建造，SPEC §0.2）。"""
    env = products["envelope"]["obj"]
    assert env["status"] == "blocked"
    assert env["verdict"] in ("yellow", "red")
    assert env["determinism_claim"] == "byte_exact"
    assert env["metrics"]["ambiguous_open"] == []
    assert env["metrics"]["rulings_applied"] == ["AMB-1", "AMB-2", "AMB-3", "AMB-4"]
    assert env["data"]["gate"]["blocking"].startswith("missing_sources")


def test_no_unclassified(products):
    cov = products["coverage"]["obj"]
    assert cov["unmapped_nets"] == []
    assert cov["uncovered_groups"] == []
    assert cov["uncovered_layers"] == []
    assert cov["totals"]["named_nets"] >= 150  # spec 声称 160


def test_all_checkers_declared_unimplemented(products):
    cov = products["coverage"]["obj"]
    assert cov["unimplemented_checkers"]
    for entry in cov["unimplemented_checkers"]:
        assert entry["implementation_status"] == "specified"


def test_core_products_free_of_forbidden_fields(products):
    for name in ("constraints", "coverage", "impedance_targets"):
        hits = envelope.scan_forbidden_core_fields(products[name]["obj"])
        assert hits == [], (name, hits[:3])


def test_fallback_declared(products):
    fb = products["coverage"]["obj"]["fallback"]
    assert fb["backend"] == "pcbflow.sexpr_min"
    assert fb["fidelity"] and fb["fallback_reason"]


def test_determinism_byte_exact(products):
    """同输入两次构建 → 核心产物 byte 相等（determinism_claim 的证据）。"""
    again = compile_cmd.build_products()
    for name in ("constraints", "coverage", "impedance_targets"):
        assert products[name]["bytes"] == again[name]["bytes"], name


def test_group_constraint_ids_align(products):
    cov = products["coverage"]["obj"]
    for e in cov["nine_group_comparison"]:
        assert e["constraint_id"].startswith("C-")
