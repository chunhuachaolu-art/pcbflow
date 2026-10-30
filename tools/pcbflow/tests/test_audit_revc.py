"""② Rev-C 回测集成测试（p3 布局时点 + opens.csv 真值；全程只读）。

三门（SPEC §② 算法回测门，预测器质量门≠交付门）：
  G1 ≥70% 断点预测；G2 3V3 逃逸缺口 ≥15/22；G3 误报 ≤10%。
固定阈值与分母钉死（61/22）；模型重调时这些断言必须被有意更新。
"""

import os

import pytest

from pcbflow import audit_cmd, config, envelope

INPUTS_OK = all(os.path.exists(p) for p in (
    config.AUDIT_P3_BOARD, config.AUDIT_OPENS_CSV, config.REVC_NETLIST))
pytestmark = pytest.mark.skipif(not INPUTS_OK, reason="Rev-C backtest inputs missing")


@pytest.fixture(scope="module")
def products():
    return audit_cmd.build_products()


def test_board_snapshot_parsed(products):
    snap = products["audit"]["obj"]["board_snapshot"]
    assert snap["footprints"] == 72 and snap["pads"] == 564
    assert snap["tracks"] == 0 and snap["vias"] == 0  # p3=纯布局时点


def test_opens_denominators(products):
    """分母必须钉死：61 非 GND 断点、22 条 3V3（dataset/mode 齐备）。"""
    a = products["audit"]["obj"]
    assert a["prediction"]["opens_total"] == 61
    g = a["gates"]
    assert g["G1_open_recall"]["denominator"] == 61
    assert g["G2_3v3_escape"]["denominator"] == 22
    for gk in g.values():
        assert gk["dataset"] and gk["mode"] and gk["definition"]


def test_three_gates_pass_with_thresholds(products):
    g = products["audit"]["obj"]["gates"]
    assert g["G1_open_recall"]["pass"] is True
    assert g["G1_open_recall"]["rate"] >= config.GATE_AUDIT_RECALL_MIN
    assert g["G2_3v3_escape"]["pass"] is True
    assert g["G2_3v3_escape"]["hits"] >= config.GATE_AUDIT_3V3_MIN
    assert g["G3_false_fatal"]["pass"] is True
    assert g["G3_false_fatal"]["rate"] <= config.GATE_AUDIT_FP_MAX


def test_fatal_marking_pinned(products):
    """当前模型 fatal 集（调参记录见 config.AUDIT_FATAL_MIN_BLOCKED_PADS）：
    网级死刑只打给多点被围死的 3V3 轨；FMC 2 端网全堵降为场级证书。"""
    fm = products["audit"]["obj"]["prediction"]["fatal_marking"]
    assert fm["fatal_nets"] == ["3V3"]
    assert fm["false_positive_nets"] == []
    assert "3V3" in fm["failed_nets_f3"]


def test_seven_checks_executed_with_verdicts(products):
    checks = {c["check_id"]: c for c in products["audit"]["obj"]["checks"]}
    assert len(checks) == 7
    for c in checks.values():
        assert c["checker_status"] == "executed"
        assert c["verdict"] in ("pass", "yellow", "red")
    # pin-swap：AF 表缺失 → 零候选 + proposal_only
    ps = products["pin_swap"]["obj"]
    assert ps["candidates"] == [] and ps["status"] == "proposal_only"
    assert ps["missing_sources"][0]["source"] == "mcu_alternate_function_table"


def test_registry_consumption_declared(products):
    """SPEC §1.2：audit.json 记录 registry_snapshot_hash/registry_consumed/字段。"""
    rc = products["audit"]["obj"]["registry_consumption"]
    assert rc["registry_consumed"] is True
    assert rc["registry_snapshot_hash"]
    assert "routing_class.value" in rc["fields_consumed"]
    enum_products = __import__("pcbflow").enum_cmd.build_products()
    assert rc["registry_snapshot_hash"] == \
        enum_products["net_registry"]["obj"]["registry_snapshot_hash"]
    seed = products["skeleton_seed"]["obj"]
    assert seed["registry_snapshot_hash"] == rc["registry_snapshot_hash"]
    assert seed["buses"], "骨架种子必须给全部总线出口侧"


def test_storage_corridors_pending_str1(products):
    """STR-1 未批 → 存储走廊照算但标 pending，不产生致命。"""
    c4 = next(c for c in products["audit"]["obj"]["checks"]
              if c["check_id"] == "C4_corridor_capacity")
    st = {c["bus_id"]: c for c in c4["metrics"]["corridor_budgets"]}
    for b in ("BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2"):
        assert st[b]["status"] == "pending_STR-1"
        assert st[b]["fatal"] is False


def test_audit_determinism_and_clean(products):
    again = audit_cmd.build_products()
    for name in ("audit", "pin_swap", "skeleton_seed"):
        assert products[name]["bytes"] == again[name]["bytes"], name
        hits = envelope.scan_forbidden_core_fields(products[name]["obj"])
        assert hits == [], (name, hits[:3])


def test_cli_audit_wiring():
    """CLI 面接线：audit --select summary 可跑，exit=0（status=ok）。"""
    from pcbflow import cli
    rc = cli.main(["audit", "--select", "summary", "--out-dir", "out/revc-a3"])
    assert rc == config.EXIT_OK
