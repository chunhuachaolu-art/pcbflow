"""G0 profile 声明装载守卫（REPAIR-P4 W-1 常驻套件）。

守卫三面：
1. 快照纪律：config / feedforward_config 大写属性集 canonical sha 钉值——
   profile 装载不得增删大写常量或改值（config_sha256 / ff_config_sha256
   是历史产物 envelope 的嵌入值，漂移=历史台账 byte-exact 破坏）。
2. 装载钉值：Rev-C 项目事实经 profile 装载后的代表值与 G0 冻结时点逐项相等
   （profile 内容漂移=测试红，改 profile 须过等价门并重钉本文件）。
3. fail-closed：profile 缺失 / 坏 JSON / 缺节 / 版本不符 → ProfileError 硬失败，
   无静默回落。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import config, hashing, profile_loader
from pcbflow import compile_cmd, enum_cmd, net_registry
from pcbflow import feedforward_config as ffc
from pcbflow import check_cmd, signoff_cmd


def _upper_snapshot(module):
    return {k: v for k, v in vars(module).items() if k.isupper()}


# ---- 1. 快照纪律（等价门机制级守卫） ----------------------------------------

def test_config_snapshot_sha_pinned():
    """vars(config) 大写属性集 canonical sha=G0 冻结值（914180f9…）。

    漂移来源=装载行为变化或大写常量增删；任一发生都破坏历史产物 envelope
    byte-exact，须重过 W-1 等价门并重钉。
    """
    sha = hashing.sha256_text(hashing.json_dumps(_upper_snapshot(config)))
    assert sha == "914180f951f66c887979d72d4348a479b8b2025c77d1365f1967b9ec2ffa7a29"


def test_ffc_snapshot_sha_pinned():
    sha = hashing.sha256_text(hashing.json_dumps(_upper_snapshot(ffc)))
    assert sha == "e34febf55364beea9aa8a3cf6943569951c1e95400d3dc2bde8cebfa0653292e"


def test_upper_key_counts_pinned():
    assert len(_upper_snapshot(config)) == 81
    assert len(_upper_snapshot(ffc)) == 24


# ---- 2. 装载钉值（G0 冻结时点代表值） ----------------------------------------

def test_paths_and_gate_values_pinned():
    assert config.ROUTING_SPEC.endswith(
        os.path.join("design", "coreboard", "reports", "routing-spec-v1.md"))
    assert config.REVC_NETLIST.endswith("revc.netlist")
    assert config.REVC_BOARD.endswith("stm32h743-coreboard-revc.kicad_pcb")
    assert config.AUDIT_P3_BOARD.endswith(os.path.join(
        "snapshots", "p3-placement-gates-pass",
        "stm32h743-coreboard-revc.kicad_pcb"))
    assert config.GATE_CONSTRAINT_COUNT == (40, 60)
    assert config.NINE_GROUPS == [
        "G_USB", "G_FMC_D", "G_FMC_C", "G_FMC_A",
        "G_EMMC", "G_SD", "G_QSPI", "G_ETH", "G_LTDC"]
    assert config.AUDIT_SIGNAL_LAYERS == ["F.Cu", "In2.Cu"]
    assert config.AUDIT_GRID_CELL_MM == 0.5
    assert config.AUDIT_FATAL_MIN_BLOCKED_PADS == 4
    assert config.GATE_AUDIT_RECALL_MIN == 0.70
    assert config.GATE_AUDIT_3V3_MIN == 15
    assert config.GATE_AUDIT_FP_MAX == 0.10
    assert config.CPLACE_STEPS_MM == (0.5, 1.0, 2.0)
    assert config.CPLACE_QUANT == 0.05
    assert config.CPLACE_BODY_INFLATE_MM == config.AUDIT_BODY_INFLATE_MM == 0.25
    assert config.SEED_PATH.endswith(os.path.join("revc-a3", "skeleton-seed.json"))


def test_module_pins_pinned():
    assert compile_cmd.PROJECT_ID == "stm32h743-coreboard-revc"
    assert compile_cmd.NET_TOTAL_SPEC_CLAIM == 160
    assert check_cmd.A3_DIR == "out/revc-a3"
    assert check_cmd.FC2_DIR == "out/revc-fc2"
    assert signoff_cmd.FD1_OUT_DEFAULT == "out/revc-fd1"
    assert signoff_cmd.FC2_DIR == "out/revc-fc2"
    assert ffc.PLAN_ID == "FF-REVC-0001"
    assert ffc.FREEZE_ID == "FF0-REVC-0001"
    assert ffc.FF_OUT_DIR_REL == "out/revc-ff1"
    assert ffc.A3_FROZEN_PRODUCTS[0] == "audit.json"
    assert ffc.B1_FROZEN_PRODUCTS[-1] == "skeletons.geojson"


def test_enum_tables_shape_pinned():
    assert [b["bus_id"] for b in enum_cmd._BUS_RULES] == [
        "BUS_USB", "BUS_FMC", "BUS_SDMMC2", "BUS_SDMMC1",
        "BUS_QSPI", "BUS_ETH", "BUS_LTDC"]
    assert enum_cmd._BUS_RULES[0]["pattern"] == "^USB_"
    assert enum_cmd._BUS_RULES[1]["symmetry_constraint"] == "C-0029"
    assert len(enum_cmd._POWER_EDGES) == 8
    assert enum_cmd._POWER_EDGES[0]["from"] == "VBUS_RAW"
    assert [a[0] for a in enum_cmd._ANCHORS] == [
        "J1", "J2", "J3", "J4", "J5", "U1", "U2", "Y1", "Y2", "U6"]
    assert set(enum_cmd._PRIORITIES) == {
        "stage_order", "bus_order", "net_order", "objective_order",
        "layer_preference", "commit_batch_order", "rollback_escalation",
        "anchor_lock"}
    assert enum_cmd._CLASS_OF_GROUP["G_USB"] == ["USB_DIFF"]
    assert enum_cmd._GROUP_TOPOLOGY["G_EMMC"] == "C-0031 CK 先行锁定"


# ---- 3. 角色规则声明化等价（每原子至少一钉值） --------------------------------

@pytest.mark.parametrize("net,cls,role,rule", [
    ("GNDA", "GND_CLASS", "ground_return_analog", "rule:gnda_exact(C-0042)"),
    ("GND", "GND_CLASS", "ground_return", "rule:gnd_exact"),
    ("SW_NODE", "PWR_SW_raw", "power_switch_node", "rule:sw_node_exact(C-0033)"),
    ("FB_NODE", "PWR_SW_raw", "power_feedback", "rule:fb_node_exact(PWR_SW_raw)"),
    ("EMMC_VSEL", "PWR_SW_raw", "power_enable", "rule:emmc_vsel(C-0045)"),
    ("VDDA", "SIG_DEFAULT", "power_rail", "rule:pwr_class(C-0042)"),
    ("PWR_MAIN", "PWR_MAIN_CLASS", "power_rail", "rule:pwr_class(C-0042)"),
    ("HSE_IN", "SIG_DEFAULT", "crystal_node", "rule:xo_prefix(C-0032)"),
    ("X_ANLG", "ANLG", "analog_sensitive", "rule:anlg_class"),
    ("FOO_DM", "SIG_DEFAULT", "differential_negative", "rule:dm_suffix"),
    ("USB_DM", "SIG_DEFAULT", "differential_negative", "rule:dm_suffix"),
    ("USB_DP", "SIG_DEFAULT", "differential_positive", "rule:dp_suffix"),
    ("QSPI_CLK", "SIG_DEFAULT", "clock", "rule:clk_suffix"),
    ("FMC_SDCLK", "SIG_DEFAULT", "clock", "rule:clk_suffix"),
    ("LTDC_PCLK", "SIG_DEFAULT", "clock", "rule:clk_suffix"),
    ("NRST", "SIG_DEFAULT", "reset", "rule:nrst_exact"),
    ("SWDIO", "SIG_DEFAULT", "test_or_configuration", "rule:dbg_prefix"),
    ("BTN_USER", "SIG_DEFAULT", "test_or_configuration", "rule:dbg_prefix"),
    ("LED_STATUS", "SIG_DEFAULT", "test_or_configuration", "rule:dbg_prefix"),
    ("GPIO_PA0", "SIG_DEFAULT", "ordinary_gpio", "rule:gpio_prefix"),
    ("FMC_D5", "SIG_DEFAULT", "ordinary_control", "rule:sig_default_residual"),
    ("ANY_OTHER", "OTHER_CLASS", "ordinary_signal", "rule:default"),
])
def test_electrical_role_rules_equivalence(net, cls, role, rule):
    got_role, got_rule = net_registry.electrical_role_of(net, cls)
    assert (got_role, got_rule) == (role, rule)


@pytest.mark.parametrize("net,role", [
    ("FMC_SDCLK", "clock"), ("SDMMC2_CK", "clock"), ("LTDC_PCLK", "clock"),
    ("FMC_A11", "address"), ("FMC_A0", "address"), ("FMC_BA1", "address"),
    ("FMC_D15", "data"), ("FMC_NBL0", "data"), ("SDMMC1_D3", "data"),
    ("QSPI_IO2", "data"), ("LTDC_R3", "data"), ("ETH_RXD0", "data"),
    ("ETH_CRS_DV", "data"),
    ("LTDC_HSYNC", "control"), ("SDMMC2_CMD", "control"), ("SD_CD", "control"),
    ("ETH_MDIO", "control"),
    ("VREF_PLUS", "signal"), ("SW_NODE", "signal"),
])
def test_bus_role_rules_equivalence(net, role):
    assert net_registry.bus_role_of(net) == role


# ---- 4. fail-closed 装载 ------------------------------------------------------

def _write_profile(tmp_path, payload_bytes):
    d = tmp_path / "profiles" / "revc-coreboard"
    d.mkdir(parents=True)
    (d / "profile.json").write_bytes(payload_bytes)
    return str(tmp_path)


def test_load_profile_ok_and_cached(tmp_path):
    src = profile_loader.profile_path(config.PCBFLOW_ROOT)
    root = _write_profile(tmp_path, open(src, "rb").read())
    pf = profile_loader.load_profile(root)
    assert pf["profile_id"] == "revc-coreboard"
    assert pf["_sha256"] == hashing.sha256_file(src)
    again = profile_loader.load_profile(root)
    assert again is pf  # lru_cache 共享（只读语义）


def test_load_profile_missing_fails_closed(tmp_path):
    with pytest.raises(profile_loader.ProfileError, match="profile_missing"):
        profile_loader.load_profile(str(tmp_path))


def test_load_profile_bad_json_fails_closed(tmp_path):
    root = _write_profile(tmp_path, b"{not json")
    with pytest.raises(profile_loader.ProfileError, match="profile_bad_json"):
        profile_loader.load_profile(root)


def test_load_profile_missing_section_fails_closed(tmp_path):
    src = json.loads(open(profile_loader.profile_path(
        config.PCBFLOW_ROOT), encoding="utf-8").read())
    del src["net_registry"]
    root = _write_profile(
        tmp_path, json.dumps(src, ensure_ascii=False).encode("utf-8"))
    with pytest.raises(profile_loader.ProfileError,
                       match="profile_missing_sections"):
        profile_loader.load_profile(root)


def test_load_profile_schema_version_mismatch_fails_closed(tmp_path):
    src = json.loads(open(profile_loader.profile_path(
        config.PCBFLOW_ROOT), encoding="utf-8").read())
    src["schema_version"] = "pcbflow-g0-profile/9.9"
    root = _write_profile(
        tmp_path, json.dumps(src, ensure_ascii=False).encode("utf-8"))
    with pytest.raises(profile_loader.ProfileError,
                       match="profile_schema_version_mismatch"):
        profile_loader.load_profile(root)


def test_load_profile_key_missing_fails_closed():
    with pytest.raises(profile_loader.ProfileError,
                       match="profile_key_missing"):
        profile_loader.require({"enum": {}}, "enum", "bus_rules")


def test_unknown_rule_atom_fails_closed():
    with pytest.raises(profile_loader.ProfileError,
                       match="role_rule_atom_unknown"):
        net_registry._nr_atom_ok({"net_bogus": "X"}, "N", "C")
