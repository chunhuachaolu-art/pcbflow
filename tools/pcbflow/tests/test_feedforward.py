"""FF1 会话测试（SPEC v1.3 §16.2 FF 子集 + §16.3 Rev-C FF shadow 验收 + §15 FF-3）。

覆盖：margin 公式/四态/缺 basis 不默认 green/稳定排序/160+32 NC 列账/六 hash 自洽/
双跑 byte-exact/禁区扫描/控制冲突不静默/stale 发现/基线门与板 hash 不变/
required_mm 三态/declared≠actually_read/六资源可构造缺口归因。
冻结产物（out/revc-a3、out/revc-b1、out/revc-ff1/baseline-freeze.json）只读。
"""

import functools
import json
import os

import pytest

from pcbflow import config, coplace_cmd, envelope, feedforward
from pcbflow import feedforward_config as ffc
from pcbflow import hashing


@functools.lru_cache(maxsize=1)
def _products():
    return feedforward.build_products("out/revc-ff1")


@functools.lru_cache(maxsize=1)
def _freeze():
    return feedforward.build_baseline_freeze()


def _plan():
    return _products()["plan"]["obj"]


# ---- 1-3：公式与四态 ----------------------------------------------------------
def test_margin_formula_and_states():
    """margin=supply−demand−reserve；green/yellow/red/unknown 四态（§16.2-1/2）。"""
    assert feedforward.classify_resource(1.0, 0.5, True) == "available"
    assert feedforward.classify_resource(0.2, 0.5, True) == "low_margin"
    assert feedforward.classify_resource(0.0, 0.5, True) == "low_margin"
    assert feedforward.classify_resource(-0.001, 0.5, True) == "resource_deficit"
    assert feedforward.classify_resource(5.0, 0.5, False) == "missing_basis"
    assert feedforward.classify_resource(None, 0.5, True) == "missing_basis"
    # 公式本体：资源行 margin 与 supply−demand−reserve 数值一致
    for r in _plan()["resources"]:
        if r["state"] != "missing_basis":
            expect = round(r["supply"]["value"] - r["demand"]["value"]
                           - (r["reserve"]["value"] or 0.0), 4)
            assert r["margin"]["value"] == expect, r["resource_id"]


def test_missing_basis_not_green():
    """缺 basis → missing_basis，禁默认 green（§16.2-3；D5 电流缺源不虚构）。"""
    rails = [r for r in _plan()["resources"]
             if r["resource_id"].startswith("power_return_space:rail:")]
    assert rails, "电源轨资源应存在"
    for r in rails:
        assert r["state"] == "missing_basis"
        assert r["supply"]["value"] is None and r["demand"]["value"] is None
    via = [r for r in _plan()["resources"] if r["kind"] == "via_budget"]
    assert via and via[0]["state"] == "missing_basis"  # fab 能力表缺源


# ---- 4/7：稳定排序与双跑 byte-exact -------------------------------------------
def test_stable_sorting():
    p = _plan()
    ids = [r["resource_id"] for r in p["resources"]]
    assert ids == sorted(ids)
    cids = [(c["kind"], c["target"]) for c in p["controls"]]
    assert cids == sorted(cids)
    for r in p["resources"]:
        assert r["net_ids"] == sorted(set(r["net_ids"]))
        assert r["blocking_net_ids"] == sorted(set(r["blocking_net_ids"]))


def test_double_run_byte_exact():
    """§16.2-7：同输入双跑，plan/coverage byte-exact（comparison 含 rebuild 一致）。"""
    a = feedforward.build_products("out/revc-ff1")
    for k in ("plan", "coverage", "comparison"):
        assert a[k]["bytes"] == _products()[k]["bytes"], k


# ---- 5：160 具名 + 32 NC 列账 --------------------------------------------------
def test_named_and_nc_nets_ledgered():
    cov = _products()["coverage"]["obj"]
    assert cov["nets"]["named_total"] == 160
    assert cov["nets"]["nc_excluded_total"] == 32
    assert cov["nets"]["nc_listed_explicitly"] is True
    assert cov["nets"]["net_id_stable"] is True


# ---- 6：六 hash 自洽 ----------------------------------------------------------
def test_snapshot_six_hashes_match_files():
    snap = _plan()["snapshot"]
    a3 = ffc.A3_DIR_REL
    reg = json.load(open(os.path.join(config.PCBFLOW_ROOT, *(
        (a3 + "/net-registry.json").split("/"))), encoding=config.ENCODING))
    assert snap["registry_snapshot_hash"] == reg["registry_snapshot_hash"]
    assert snap["structures_sha256"] == hashing.sha256_file(
        os.path.join(config.PCBFLOW_ROOT, *(a3 + "/structures.json").split("/")))
    assert snap["constraints_sha256"] == hashing.sha256_file(
        os.path.join(config.PCBFLOW_ROOT, *(a3 + "/constraints.json").split("/")))
    assert snap["placement_snapshot_sha256"] == hashing.sha256_file(
        config.AUDIT_P3_PLACEMENT_CSV)
    assert snap["board_snapshot_sha256"] == hashing.sha256_file(
        config.AUDIT_P3_BOARD)
    assert snap["feedforward_config_sha256"] == feedforward.ff_config_sha256()


# ---- 8：核心产物禁区 ----------------------------------------------------------
def test_no_forbidden_fields():
    for name in ("plan", "coverage", "comparison"):
        obj = _products()[name]["obj"]
        assert envelope.scan_forbidden_core_fields(obj) == [], name
    assert envelope.scan_forbidden_core_fields(_freeze()["data"]) == []


# ---- 9：控制冲突不静默 ---------------------------------------------------------
def test_control_conflict_detection_synthetic():
    ctls = [
        {"control_id": "CTL-0001", "kind": "assign_preferred_layer",
         "target": "bus:BUS_FMC", "action": {"preferred_layer": "In2.Cu"}},
        {"control_id": "CTL-0002", "kind": "assign_preferred_layer",
         "target": "bus:BUS_FMC", "action": {"preferred_layer": "F.Cu"}},
        {"control_id": "CTL-0003", "kind": "reserve_corridor",
         "target": "bus:BUS_FMC", "action": {"reserve_width_mm": 7.6}},
    ]
    conflicts = feedforward.detect_control_conflicts(ctls)
    assert len(conflicts) == 1
    assert conflicts[0]["control_ids"] == ["CTL-0001", "CTL-0002"]
    assert "不静默" in conflicts[0]["resolution"]


def test_generated_controls_no_conflict_and_gated():
    p = _plan()
    assert p["control_conflicts"] == []
    for c in p["controls"]:
        assert c["approval_state"].startswith("pending_FF4_consumer_gate")
        assert c["status"] == "planning_advisory"
        assert c["consumer_stages"] and set(c["consumer_stages"]) <= {3, 4}


# ---- 10：stale 发现 -----------------------------------------------------------
def test_stale_plan_detected():
    snap = dict(_plan()["snapshot"])
    assert feedforward.check_stale(snap, snap)["stale_plan"] is False
    snap2 = dict(snap, structures_sha256="deadbeef")
    out = feedforward.check_stale(snap2, snap)
    assert out["stale_plan"] is True
    assert out["diff_keys"] == ["structures_sha256"]


# ---- 11/12：基线门、verdict、板与历史产物 hash 不变 ----------------------------
def test_comparison_invariants_163():
    """§16.3 Rev-C FF shadow 验收字段全到位。"""
    c = _products()["comparison"]["obj"]
    assert c["registry_snapshot_match"] is True
    assert c["structures_snapshot_match"] is True
    assert c["constraints_snapshot_match"] is True
    assert c["placement_snapshot_match"] is True
    assert c["gate_unchanged"] is True
    assert c["baseline_verdict_unchanged"] is True
    assert c["optimization_applied_unchanged"] is False  # §16.3 契约值
    assert c["optimization_applied"] is False
    assert c["board_write"] is False
    assert c["stale_plan_check"]["stale_plan"] is False
    assert c["gate_verdicts_registered"]["audit"] == {
        "G1_open_recall": True, "G2_3v3_escape": True, "G3_false_fatal": True}
    assert c["gate_verdicts_registered"]["layout_evidence"] == "red"  # 冻结基线证据


def test_ff0_freeze_matches_current_files():
    """FF-0 冻结 hash 与当前盘上文件一致（历史产物未被本会话改动）。"""
    data = _freeze()["data"]
    assert len(data["frozen_products"][ffc.A3_DIR_REL]) == 16
    assert len(data["frozen_products"][ffc.B1_DIR_REL]) == 7
    for rel in (ffc.A3_DIR_REL, ffc.B1_DIR_REL):
        for name, sha in data["frozen_products"][rel].items():
            path = os.path.join(config.PCBFLOW_ROOT, *(rel.split("/")), name)
            assert hashing.sha256_file(path) == sha, rel + "/" + name
    reg = data["historical_registration"]
    assert reg["coplace_optimization"]["applied"] is False
    assert data["registered_defects"][0]["id"] == "FF3-1"


# ---- 13：required_mm 三态（FF-3 集成面） ---------------------------------------
def test_ff3_fix_evidence_in_comparison():
    fix = _products()["comparison"]["obj"]["ff3_fix"]
    assert fix["canonical_field"] == "required_mm"
    assert fix["layout_changed_top_level_keys"] == ["sanity_vs_audit"]
    assert fix["layout_core_unchanged_outside_sanity_vs_audit"] is True
    assert fix["placement_csv_byte_equal"] is True
    assert fix["geojson_byte_equal"] is True
    assert fix["layer_plan_byte_equal"] is True
    assert all(r["demand_consistent"] == "consistent"
               and r["audit_demand_mm"] is not None
               for r in fix["sanity_rows_now"]) and len(fix["sanity_rows_now"]) == 7
    assert "空比较" in fix["historical_limitation"]


# ---- 14：declared ≠ actually_read（D7） ----------------------------------------
def test_consumption_evidence_separation():
    cc = _plan()["consumption_contract"]
    read_blob = hashing.json_dumps(cc["actually_read"])
    # D7：canonical 字段 required_mm 的消费由真实读取路径仪器化产生
    assert "required_mm" in read_blob
    # 声明面与实读面分列；三态覆盖（实读/派生/忽略），fallback 无
    assert cc["declared_consumed"] and cc["actually_read"] and cc["derived"]
    assert any("ignored" not in k for k in cc)  # 键面齐
    assert cc["ignored"]
    assert cc["fallback"] is None
    assert cc["fidelity"].startswith("full")
    # seed 的 demand_width_mm 是真实读取（skeleton-seed 语义面，非 audit 字段冒充）
    assert any("skeleton-seed.json" in r["artifact"] for r in cc["actually_read"])
    assert any("skeleton-seed" in d for d in cc["declared_consumed"])


# ---- 15/16：六类资源可构造 + 需求函数口径 --------------------------------------
def test_six_kinds_constructible_with_attribution():
    cov = _products()["coverage"]["obj"]
    assert cov["resources"]["kinds_missing"] == []
    assert set(cov["resources"]["by_kind"]) == set(ffc.RESOURCE_KINDS)
    p = _plan()
    for r in p["resources"]:
        assert r["basis"], r["resource_id"]
        assert r["demand_model"]
        assert r["yellow_margin"] is not None or r["state"] == "missing_basis"
        if r["state"] == "resource_deficit":
            assert r["blocking_net_ids"] or r["net_ids"], r["resource_id"]
            assert r["suggested_rollback_stage"] in (2, 3)
            assert r["deficit_magnitude"]["value"] > 0
    kinds_with_deficit = {r["kind"] for r in p["resources"]
                          if r["state"] == "resource_deficit"}
    assert kinds_with_deficit >= {"escape_slots", "power_return_space"}


def test_power_return_demand_functions():
    """D5：环路面积/去耦半径可算；轨道电流缺源 missing_basis；回流穿越归因。"""
    p = _plan()
    by_id = {r["resource_id"]: r for r in p["resources"]}
    loop = by_id["power_return_space:SW_loop_area"]
    assert loop["demand"]["value"] == pytest.approx(85.078, abs=0.01)
    decap = by_id["power_return_space:decap_radius"]
    assert decap["state"] == "resource_deficit"
    assert decap["supply"]["value"] == pytest.approx(3.0)
    cross = by_id["power_return_space:analog_zone_crossings"]
    assert cross["demand"]["value"] == 15 and len(cross["blocking_net_ids"]) == 15


# ---- 17：advisory 边界 ---------------------------------------------------------
def test_plan_is_planning_advisory_only():
    p = _plan()
    assert p["status"] == "planning_advisory" and p["authority"] == "planning_advisory"
    blob = hashing.json_dumps(p)
    assert "stage_status" not in blob
    assert p["residuals"] == []  # 无可比实际结果不编造 residual（§11.2）


def test_envelope_contract():
    env = _products()["envelope"]["obj"]
    assert env["command"] == "feedforward"
    assert env["command_kind"] == "core"
    assert env["schema_version"] == ffc.SCHEMA_FF_ENVELOPE
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert env["determinism_claim"] == "byte_exact"
