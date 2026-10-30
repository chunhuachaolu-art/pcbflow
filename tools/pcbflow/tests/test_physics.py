"""TD6 物理证据与 bring-up 层合同测试（全合成数据；SPEC-v3.0-PROPOSAL §TD6）。

构造真值：
  - 全绿 required 项（openems 仿真入 external_required + lab_measurement
    实测入 bring_up）→ physics_gate=pass；
  - fail-closed 逐路径：缺项/not_executed/unknown/stale/limit_fail/
    uncertainty_fail/no_approval/coverage 不全 → blocked 或 fail，绝不 pass；
  - coverage=100% 是必要非充分：coverage 完整但 limit_fail → fail；
  - revc-tbd1 语义复刻：datasheet_derived 的 102.7Ω screening 项不能
    satisfy bring_up/external_required（authority_mismatch），bring-up
    witness 缺失 → not_available；
  - openEMS 与 scikit-rf 非等价：designated 逐字匹配。
"""

import pytest

from pcbflow import hashing, physics, schemas


def _sha(tag):
    return hashing.sha256_text(tag)


def _green_booleans():
    return dict(
        required_scope_defined=True,
        coverage_complete=True,
        input_model_complete=True,
        executed=True,
        convergence_or_validity_pass=True,
        limit_pass=True,
        uncertainty_acceptable=True,
        external_approval_present=True,
    )


def _green_external(item_id="PHY-EXT-1", **over):
    fields = dict(
        status="pass",
        **_green_booleans(),
        bring_up_disposition="not_available",
        net_or_relation="USB90_DP",
        model_or_tool="openems",
        model_version="openems-0.0.35-synth",
        input_hashes={"board": _sha("board"), "stackup": _sha("stackup")},
        measurement_convention="differential_microstrip_2x",
        limits={"target_impedance_ohm": 100.0, "tolerance_pct": 10.0},
        uncertainty=2.5,
        fidelity="required_grade",
        authority="openems",
        review_ref=_sha("review-ext"),
        approval_ref=_sha("approval-ext"),
        measured_value=98.7,
        note="合成绿色 external_required 项",
    )
    fields.update(over)
    return physics.build_item(item_id, "external_required", **fields)


def _green_bring_up(item_id="PHY-BU-1", **over):
    fields = dict(
        status="pass",
        **_green_booleans(),
        bring_up_disposition="pass",
        net_or_relation="USB90_DP",
        model_or_tool="lab_bench",
        model_version="bench-synth-1",
        input_hashes={"board": _sha("board-bu")},
        measurement_convention="tdr_ohm",
        limits={"target_impedance_ohm": 100.0, "tolerance_pct": 10.0},
        uncertainty=1.5,
        fidelity="measured",
        authority="lab_measurement",
        review_ref=_sha("review-bu"),
        approval_ref=_sha("approval-bu"),
        measured_value=101.2,
        note="合成绿色 bring_up 项",
    )
    fields.update(over)
    return physics.build_item(item_id, "bring_up", **fields)


def _revc_tbd1_item(track="physics_screening", **over):
    """revc-tbd1 语义：datasheet_derived + fidelity=screening 的资料级证据。"""
    fields = dict(
        status="pass",
        **_green_booleans(),
        bring_up_disposition="not_available",
        net_or_relation="ETH_RXD0",
        model_or_tool=None,
        input_hashes={"datasheet": _sha("ds")},
        measurement_convention="datasheet_note",
        limits={"differential_impedance_ohm": 100.0, "tolerance_pct": 15.0},
        fidelity="screening",
        authority="datasheet_derived",
        measured_value="102.7 ohm",
        note="revc-tbd1 资料/推导级 screening 证据（非 bring-up pass）",
    )
    fields.update(over)
    return physics.build_item("PHY-REVC-TBD1", track, **fields)


def _witness_report(**over):
    report = {
        "schema_version": schemas.SCHEMA_V3,
        "project_id": "synth-proj",
        "profile_id": "synth-profile",
        "board_serial": "SN-SYNTH-0001",
        "board_revision": "RevC",
        "fixture": "FIX-SYNTH-01",
        "firmware_version": "fw-1.0.0-synth",
        "test_software_version": "ts-1.0.0-synth",
        "raw_measurements": [
            {"measurement_id": "M1", "quantity": "impedance", "value": 99.1,
             "unit": "ohm", "limit": 110.0, "pass": True},
        ],
        "environment": {"temperature_c": "25", "humidity_pct": "40"},
        "operator": "op-synth-01",
        "input_hash": _sha("bu-in"),
        "output_hash": _sha("bu-out"),
        "items": ["PHY-BU-1"],
        "bring_up_status": "pass",
    }
    report.update(over)
    return report


# ---------------------------------------------------------------------------
# 常量与构造
# ---------------------------------------------------------------------------

def test_tracks_constant_matches_schema_enum():
    enum = schemas.SCHEMAS["physics_report"]["properties"]["items"][
        "items"]["properties"]["track"]["enum"]
    assert physics.TRACKS == ("physics_screening", "external_required",
                              "bring_up")
    assert list(physics.TRACKS) == enum


def test_build_item_defaults_fail_closed():
    item = physics.build_item("PHY-RAW-1", "external_required")
    assert item["status"] == "not_executed"
    assert item["bring_up_disposition"] == "not_available"
    assert item["authority"] == "none"
    for field in ("required_scope_defined", "coverage_complete",
                  "input_model_complete", "executed",
                  "convergence_or_validity_pass", "limit_pass",
                  "uncertainty_acceptable", "external_approval_present"):
        assert item[field] is False
    assert not schemas.validate_spec(
        schemas.SCHEMAS["physics_report"]["properties"]["items"]["items"],
        item)


def test_build_item_rejects_unknown_track_and_bad_enum():
    with pytest.raises(ValueError):
        physics.build_item("PHY-BAD-1", "geometry")            # 非三轨
    with pytest.raises(ValueError):
        physics.build_item("PHY-BAD-2", "external_required",
                           authority="hand_waving")            # enum 外


# ---------------------------------------------------------------------------
# 全绿 → pass
# ---------------------------------------------------------------------------

def test_green_required_gate_pass():
    items = [_green_external(), _green_bring_up()]
    gate = physics.evaluate_gate(items, ["PHY-EXT-1", "PHY-BU-1"])
    assert gate["physics_gate"] == "pass"
    assert gate["failure_codes"] == []
    assert gate["evaluated_required"] == ["PHY-EXT-1", "PHY-BU-1"]
    assert gate["denominator"] == 2
    assert gate["coverage"] == {"covered": 2, "complete": True}


# ---------------------------------------------------------------------------
# fail-closed 逐路径
# ---------------------------------------------------------------------------

def test_missing_report_blocked():
    gate = physics.evaluate_gate([_green_external()],
                                 ["PHY-EXT-1", "PHY-BU-1"])
    assert gate["physics_gate"] == "blocked"
    assert "missing_report" in gate["failure_codes"]
    assert gate["coverage"] == {"covered": 1, "complete": False}


def test_not_executed_blocked():
    item = _green_external(executed=False)          # status 仍 pass、其余门绿
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "blocked"
    assert "not_executed" in gate["failure_codes"]


def test_status_unknown_blocked():
    item = _green_external(status="unknown")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "blocked"
    assert "status_unknown" in gate["failure_codes"]


def test_status_stale_blocked():
    """freshness 门：stale 证据不能过 required 门。"""
    item = _green_external(status="stale")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "blocked"
    assert "status_stale" in gate["failure_codes"]


def test_limit_fail():
    item = _green_external(limit_pass=False, status="fail")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "fail"
    assert "limit_fail" in gate["failure_codes"]


def test_uncertainty_fail():
    item = _green_external(uncertainty_acceptable=False, status="fail")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "fail"
    assert "uncertainty_fail" in gate["failure_codes"]


def test_no_approval():
    item = _green_external(external_approval_present=False, status="fail")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert gate["physics_gate"] == "fail"
    assert "no_approval" in gate["failure_codes"]


def test_coverage_complete_but_limit_fail_is_fail_not_pass():
    """coverage=100% 是必要非充分：全有报告但一项 limit_fail → fail。"""
    items = [_green_external(), _green_bring_up(limit_pass=False,
                                                status="fail")]
    gate = physics.evaluate_gate(items, ["PHY-EXT-1", "PHY-BU-1"])
    assert gate["coverage"]["complete"] is True     # 报告齐
    assert gate["physics_gate"] == "fail"           # 但结果门 fail
    assert "limit_fail" in gate["failure_codes"]


def test_empty_required_scope_not_required():
    gate = physics.evaluate_gate([_green_external()], [])
    assert gate["physics_gate"] == "not_required"
    assert gate["failure_codes"] == []


def test_check_item_gate_codes_and_bring_up_disposition():
    green = _green_bring_up()
    assert physics.check_item(green) == []
    for field, code in (
            ("required_scope_defined", "not_required_scope_defined"),
            ("coverage_complete", "coverage_incomplete"),
            ("input_model_complete", "input_model_incomplete"),
            ("executed", "not_executed"),
            ("convergence_or_validity_pass", "validity_fail"),
            ("limit_pass", "limit_fail"),
            ("uncertainty_acceptable", "uncertainty_fail"),
            ("external_approval_present", "no_approval")):
        item = _green_bring_up(**{field: False})
        assert physics.check_item(item) == [code]
    # bring_up 轨：处置缺失 → blocked 类码；fail/deferred → fail 类码
    assert "bring_up_not_available" in physics.check_item(
        _green_bring_up(bring_up_disposition="not_available"))
    assert "bring_up_disposition_fail" in physics.check_item(
        _green_bring_up(bring_up_disposition="deferred"))
    # 非 bring_up 轨不检查处置
    assert physics.check_item(
        _green_external(bring_up_disposition="deferred")) == []


# ---------------------------------------------------------------------------
# authority 兼容性与 revc-tbd1 语义
# ---------------------------------------------------------------------------

def test_authority_tier_matrix():
    ext_openems = _green_external()
    assert physics.authority_compatible(ext_openems, "physics_screening")
    assert physics.authority_compatible(ext_openems, "external_required")
    assert not physics.authority_compatible(ext_openems, "bring_up")  # 仿真非实测
    bu_lab = _green_bring_up()
    assert physics.authority_compatible(bu_lab, "bring_up")
    assert physics.authority_compatible(bu_lab, "external_required")
    none_auth = _green_external(authority="none")
    assert not physics.authority_compatible(none_auth, "external_required")
    assert not physics.authority_compatible(none_auth, "bring_up")
    assert physics.authority_compatible({}, "unknown_track") is False  # 未知轨


def test_revc_tbd1_screening_cannot_satisfy_required_tracks():
    tbd1 = _revc_tbd1_item()
    assert physics.authority_compatible(tbd1, "physics_screening") is True
    assert physics.authority_compatible(tbd1, "external_required") is False
    assert physics.authority_compatible(tbd1, "bring_up") is False
    # 同一资料级证据挂在 bring_up 轨（处置也标 pass）→ authority_mismatch
    as_bu = _revc_tbd1_item(track="bring_up", bring_up_disposition="pass",
                            status="pass", **_green_booleans())
    gate = physics.evaluate_gate([as_bu], ["PHY-REVC-TBD1"])
    assert gate["physics_gate"] == "fail"
    assert "authority_mismatch" in gate["failure_codes"]


def test_revc_tbd1_no_bring_up_witness_means_not_available():
    """无真实回板记录：即使资料级 screening 项全绿，bring-up 也只能
    not_available，不能凭推导给 pass。"""
    empty_witness = physics.bring_up_witness({})
    assert empty_witness["has_witness"] is False
    assert empty_witness["status"] == "not_available"
    assert empty_witness["missing"] == sorted(empty_witness["missing"])  # 确定性排序
    assert set(empty_witness["missing"]) == {
        "board_serial", "board_revision", "fixture", "firmware_version",
        "test_software_version", "environment", "operator", "input_hash",
        "output_hash", "raw_measurements", "items", "schema_invalid"}
    tbd1 = _revc_tbd1_item()
    gate = physics.evaluate_gate([tbd1], ["PHY-REVC-TBD1"])
    assert gate["physics_gate"] == "pass"          # screening 轨自身可过
    assert empty_witness["status"] == "not_available"  # 但 bring-up 层不因此 pass


def test_fidelity_screening_downgrades_simulation_evidence():
    item = _green_external(fidelity="screening")   # openems 但显式降级
    assert not physics.authority_compatible(item, "external_required")
    gate = physics.evaluate_gate([item], ["PHY-EXT-1"])
    assert "authority_mismatch" in gate["failure_codes"]
    assert gate["physics_gate"] == "fail"


# ---------------------------------------------------------------------------
# 指定后端（openEMS 与 scikit-rf 非等价）
# ---------------------------------------------------------------------------

def test_designated_backend_literal_match():
    openems_item = _green_external(model_or_tool="openems")
    assert physics.designated_backend_ok(openems_item, "openems") is True
    assert physics.designated_backend_ok(openems_item, "scikit_rf") is False
    skrf_item = _green_external(model_or_tool="scikit_rf",
                                authority="scikit_rf")
    assert physics.designated_backend_ok(skrf_item, "scikit_rf") is True
    assert physics.designated_backend_ok(skrf_item, "openems") is False
    assert physics.designated_backend_ok(
        _green_external(model_or_tool=None), "openems") is False
    assert physics.designated_backend_ok(openems_item, "") is False


# ---------------------------------------------------------------------------
# bring_up_witness 正负用例
# ---------------------------------------------------------------------------

def test_bring_up_witness_positive():
    result = physics.bring_up_witness(_witness_report())
    assert result == {"has_witness": True, "status": "pass"}


def test_bring_up_witness_negative_empty_raw_measurements():
    report = _witness_report(raw_measurements=[])
    result = physics.bring_up_witness(report)
    assert result["has_witness"] is False
    assert result["status"] == "not_available"
    assert "raw_measurements" in result["missing"]
    assert "schema_invalid" in result["missing"]


def test_bring_up_witness_negative_missing_board_serial():
    report = _witness_report()
    del report["board_serial"]
    result = physics.bring_up_witness(report)
    assert result["has_witness"] is False
    assert result["status"] == "not_available"
    assert "board_serial" in result["missing"]


def test_bring_up_witness_claimed_pass_without_evidence_stays_not_available():
    """报告自报 bring_up_status=pass 但缺 operator/环境 → 只能 not_available。"""
    report = _witness_report(operator="op-synth-01",
                             environment={},
                             bring_up_status="pass")
    result = physics.bring_up_witness(report)
    assert result["has_witness"] is False
    assert result["status"] == "not_available"
    assert "environment" in result["missing"]


def test_bring_up_witness_non_dict_fail_closed():
    result = physics.bring_up_witness(None)
    assert result == {"has_witness": False, "status": "not_available",
                      "missing": ["report_invalid"]}


# ---------------------------------------------------------------------------
# 产物构造（report / coverage）
# ---------------------------------------------------------------------------

def test_build_report_green_and_schema_valid():
    items = [_green_external(), _green_bring_up()]
    report = physics.build_report("synth-proj", "synth-profile", "rev-synth-1",
                                  items, ["PHY-EXT-1", "PHY-BU-1"])
    assert schemas.is_valid("physics_report", report)
    assert report["physics_gate"] == "pass"
    assert report["gate_failure_codes"] == []
    assert [it["item_id"] for it in report["items"]] == ["PHY-EXT-1",
                                                         "PHY-BU-1"]


def test_build_report_fail_path_carries_codes():
    items = [_green_external(), _green_bring_up(limit_pass=False,
                                                status="fail")]
    report = physics.build_report("synth-proj", "synth-profile", "rev-synth-1",
                                  items, ["PHY-EXT-1", "PHY-BU-1"])
    assert schemas.is_valid("physics_report", report)
    assert report["physics_gate"] == "fail"
    assert "limit_fail" in report["gate_failure_codes"]


def test_build_coverage_missing_scope_diff():
    cov = physics.build_coverage(["PHY-EXT-1", "PHY-BU-1"],
                                 [_green_external()],
                                 project_id="synth-proj",
                                 profile_id="synth-profile",
                                 snapshot_revision="rev-synth-1")
    assert schemas.is_valid("physics_coverage", cov)
    assert cov["covered_scope"] == ["PHY-EXT-1"]
    assert cov["missing_scope"] == ["PHY-BU-1"]     # 差集
    assert cov["coverage_complete"] is False


def test_build_coverage_complete():
    cov = physics.build_coverage(["PHY-EXT-1"],
                                 [_green_external(status="fail")],
                                 project_id="synth-proj",
                                 profile_id="synth-profile",
                                 snapshot_revision="rev-synth-1")
    assert schemas.is_valid("physics_coverage", cov)
    assert cov["missing_scope"] == []
    assert cov["coverage_complete"] is True         # 在场即覆盖，与结果无关


def test_build_coverage_defaults_are_schema_valid():
    cov = physics.build_coverage(["PHY-EXT-1"], [_green_external()])
    assert schemas.is_valid("physics_coverage", cov)
    assert cov["project_id"] == "unspecified"


def test_duplicate_item_ids_fail_closed():
    gate = physics.evaluate_gate([_green_external(), _green_external()],
                                 ["PHY-EXT-1"])
    assert gate["physics_gate"] == "fail"
    assert "duplicate_item" in gate["failure_codes"]
