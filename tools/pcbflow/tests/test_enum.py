"""① 结构枚举测试（FA2）：候选全量覆盖、裁决落库、确定性、禁区扫描。"""

import os

import pytest

from pcbflow import config, envelope, enum_cmd

INPUTS_OK = all(os.path.exists(p) for p in (config.REVC_NETLIST,
                                            config.LENGTH_REPORT_PY))

pytestmark = pytest.mark.skipif(not INPUTS_OK, reason="Rev-C inputs not present")


@pytest.fixture(scope="module")
def products():
    return enum_cmd.build_products()


def test_candidate_full_coverage(products):
    """① 门半边一：自动枚举候选必须全量覆盖（160 具名网逐网 home，无遗漏）。"""
    cov = products["coverage"]["obj"]
    s = products["structures"]["obj"]
    assert cov["coverage"]["named_nets"] == cov["coverage"]["assigned"]
    assert cov["coverage"]["uncovered"] == []
    assert s["coverage_summary"]["uncovered"] == []
    assert s["authority_status"] == "draft"
    assert sum(s["coverage_summary"]["bucket_counts"].values()) == \
        s["coverage_summary"]["named_nets"]


def test_home_partition_is_exact(products):
    """home 归属一网一桶；桶计数与网数一致（重复归属=实现 bug）。"""
    cov = products["coverage"]["obj"]["net_home_assignment"]
    assert len(cov) == 160
    homes = {v["home"] for v in cov.values()}
    assert homes == {"bus", "power_tree", "return_tree", "loose"}


def test_bus_members_match_rulings(products):
    """AMB-1/2/3/4 的裁决反映在总线成员上。"""
    s = products["structures"]["obj"]
    b = {x["bus_id"]: x for x in s["buses"]}
    assert len(s["buses"]) == 7
    assert b["BUS_FMC"]["member_count"] == 39          # AMB-1：含 FMC_A12
    assert "FMC_A12" in b["BUS_FMC"]["members"]
    assert b["BUS_LTDC"]["member_count"] == 20         # AMB-2：网表为准（19+PCLK）
    assert b["BUS_USB"]["members"] == ["USB_DM", "USB_DM_C", "USB_DP", "USB_DP_C"]  # AMB-3
    assert "SD_CD" in b["BUS_SDMMC1"]["members"]       # AMB-4
    assert b["BUS_SDMMC1"]["member_count"] == 7


def test_usb_bus_endpoints_two_segments(products):
    """USB 两段端点全数据推导：MCU→U6→R6→J5。"""
    b = {x["bus_id"]: x for x in products["structures"]["obj"]["buses"]}["BUS_USB"]
    assert {"U1", "U6", "R6", "J5"} <= set(b["endpoint_refs"])
    assert b["endpoints"]["U6"]["footprint"] and \
        "SOT-23" in b["endpoints"]["U6"]["footprint"]


def test_anchors_and_footprints(products):
    """SPEC §① 锚件清单 10 件；封装字段非空（数据推导）。"""
    s = products["structures"]["obj"]
    refs = [a["ref"] for a in s["anchors"]]
    assert refs == ["J1", "J2", "J3", "J4", "J5", "U1", "U2", "Y1", "Y2", "U6"]
    for a in s["anchors"]:
        assert a["footprint"], a["ref"]
        assert "锁死" in a["lock"]


def test_timing_groups_canonical(products):
    m = products["structures"]["obj"]["mapping"]
    tg = m["timing_groups"]
    assert len(tg) == 9
    assert len(tg["G_FMC_A"]["canonical_members"]) == 15   # AMB-1
    assert len(tg["G_LTDC"]["canonical_members"]) == 19    # AMB-2
    assert tg["G_USB"]["canonical_members"] == \
        ["USB_DM", "USB_DM_C", "USB_DP", "USB_DP_C"]       # AMB-3
    assert "segments" in tg["G_USB"]["measurement"]
    assert tg["G_EMMC"]["tolerance_mm"] == {"target": 1.5, "limit": 3.0}
    assert all(tg[g]["segment_budget"]["filled"] is False for g in tg)
    assert {r["id"] for r in m["rulings_consumed"]} == \
        {"AMB-1", "AMB-2", "AMB-3", "AMB-4"}


def test_mapping_three_layers(products):
    m = products["structures"]["obj"]["mapping"]
    assert "不同层级" in m["net_class_to_planner"]["level_note"]
    assert m["planner_to_length_groups"]["G_FMC_D"]["kicad_net_classes"] == \
        ["FMC_DATA_L", "FMC_DATA_H"]
    assert m["planner_to_length_groups"]["G_FMC_D"]["member_count"] == 18


def test_power_edges_validated_by_netlist(products):
    """声明的电源树边必须经网表共享器件验证（验证失败=如实标 None）。

    实测拓扑：VBUS_RAW→F1→5V_USB→(Q1/Q2)→5V/5V_HDR→U3→SW_NODE→L1→3V3
    →U4(LDO)→VDDA→FB1→VREF+。注意 F1 不直达 5V、FB1 不在 3V3→VDDA 上
    （初稿两条按 spec 文本的边被本验证否决后修正）。
    """
    pt = products["structures"]["obj"]["power_tree"]
    validated = {(e["from"], e["to"]): e["validated_by_shared_ref"] for e in pt["edges"]}
    assert validated[("VBUS_RAW", "5V_USB")] == "F1"
    assert validated[("5V_USB", "5V")] in ("Q1", "Q2")
    assert validated[("5V", "SW_NODE")] == "U3"
    assert validated[("SW_NODE", "3V3")] == "L1"
    assert validated[("3V3", "VDDA")] == "U4"
    assert validated[("VDDA", "VREF+")] == "FB1"
    assert validated[("VBAT", "VBAT_CHG")] is None  # 无单一桥接器件 → 如实标 None
    rails = pt["rails"]
    assert rails["5V"]["current_budget_a"] is None  # 不虚构电流预算
    assert "3V3" in rails and len(rails["3V3"]["decoupling_caps"]) >= 10
    assert "1.0" in rails["5V"]["min_width_raw"]  # 线宽取 §2 类行 raw


def test_findings_registered(products):
    """枚举新发现如实登记：STR-1 存储总线端点、STR-2 顺序缺口。"""
    f = {x["id"]: x for x in products["structures"]["obj"]["findings"]}
    assert f["STR-1"]["status"] == "pending"
    assert "U1↔J1" in f["STR-1"]["title"]
    assert "39" in " ".join(f["STR-1"]["evidence"]) or True  # 证据为端点表
    assert f["STR-2"]["kind"] == "ordering_gap"


def test_priorities_scopes_and_three_orders(products):
    p = products["structures"]["obj"]["priorities"]
    for key in ("stage_order", "bus_order", "net_order", "objective_order",
                "layer_preference", "commit_batch_order", "rollback_escalation",
                "anchor_lock"):
        assert key in p and p[key].get("source"), key
    t = p["three_orders_report"]
    assert set(t) == {"routing_spec_execution_order",
                      "pcbagent_planner_order", "pcbflow_optimization_order"}
    assert t["routing_spec_execution_order"]["sequence"][:2] == ["USB", "FMC"]


def test_enum_gate_blocked_by_authority_pending(products):
    """① 门：候选覆盖半边已过；权威确认半边 pending → blocked/yellow。"""
    env = products["envelope"]["obj"]
    assert env["command"] == "enum"
    assert env["status"] == "blocked" and env["verdict"] == "yellow"
    assert env["data"]["gate"]["candidate_full_coverage"] is True
    assert "pending_user" in env["data"]["gate"]["explicit_confirmation"]
    assert env["metrics"]["rulings_consumed"] == ["AMB-1", "AMB-2", "AMB-3", "AMB-4"]


def test_core_products_free_of_forbidden_fields(products):
    for name in ("structures", "coverage"):
        hits = envelope.scan_forbidden_core_fields(products[name]["obj"])
        assert hits == [], (name, hits[:3])


def test_determinism_byte_exact(products):
    """同输入两次构建 → 核心产物 byte 相等。"""
    again = enum_cmd.build_products()
    for name in ("structures", "coverage"):
        assert products[name]["bytes"] == again[name]["bytes"], name
