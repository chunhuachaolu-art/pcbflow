"""TL-5 第四包：check_stage（参考 routed 态验证口径，偏差 D17）测试。

覆盖：routed 板几何解析（逐网铜几何/实际最小几何/drill 字面量缺失）、
DRC 双 severity 摘要（一致性/fail-closed）、route/check 声明装配（D17
route_scope+holdout 注记+路径/hash fail-closed）、check 报告 verdict
（正向全过+负向：未连通/DRC 超声明上限/staging 不一致/阈值不符/
setup 漂移/口径冒用——advisory 零几何不计 verdict）、执行汇总记录、
真实 bm1 板与既有 DRC baseline 的回放（byte-exact 复算）。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import check_stage as cs
from pcbflow import hashing

#: 最小 KiCad5 routed 合成板：net1 +5V（2 焊盘+1 segment）、net2 GND
#: （3 焊盘+1 segment+1 via+1 zone）、net3 N$1（2 焊盘+零铜几何——
#: advisory 靶）、net4 SIG（单焊盘命名网——advisory 不应flag）
SYNTH_ROUTED = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.4-0-10_14)")

  (general (thickness 1.6) (tracks 3) (zones 1) (modules 2) (nets 5))

  (layers
    (0 Top signal)
    (31 Bottom signal)
  )

  (setup
    (trace_clearance 0.1)
    (trace_min 0.2)
    (via_size 0.8)
    (via_drill 0.4)
    (via_min_size 0.4)
    (via_min_drill 0.3)
  )

  (net 0 "")
  (net 1 +5V)
  (net 2 GND)
  (net 3 N$1)
  (net 4 SIG)

  (module Lib:A (layer Top) (tedit 5DD86010)
    (at 10.0 20.0 90)
    (fp_text reference U1 (at 0 -2.54 90) (layer F.SilkS))
    (pad 1 thru_hole circle (at 1.0 -5.25 90) (size 1.458 1.458) (drill 0.95) (layers *.Cu *.Mask)
      (net 2 GND))
    (pad 2 smd rect (at -1.0 -5.25) (size 0.3 0.6) (layers F.Cu)
      (net 1 +5V))
    (pad 3 smd rect (at 0.0 -7.25) (size 0.3 0.6) (layers F.Cu)
      (net 3 N$1))
  )

  (module Lib:B (layer Bottom) (tedit 5DD86011)
    (at 30.5 40.25)
    (fp_text reference U2 (at 0 0) (layer B.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.3 0.6) (layers B.Cu)
      (net 1 +5V))
    (pad 2 thru_hole circle (at 2.5 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 2 GND))
    (pad 3 thru_hole circle (at 5.0 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 3 N$1))
    (pad 4 smd rect (at 7.5 0.0) (size 0.3 0.6) (layers B.Cu)
      (net 4 SIG))
  )

  (segment (start 10.0 15.0) (end 12.0 15.0) (width 0.2032) (layer Top) (net 1))
  (segment (start 30.5 40.25) (end 33.0 41.0) (width 0.25) (layer Bottom) (net 2))
  (arc (start 1.0 1.0) (end 2.0 2.0) (width 0.3) (layer Top) (net 2))
  (via (at 31.0 40.5) (size 0.8) (drill 0.4) (layers Top Bottom) (net 2))
  (zone (net 2) (net_name GND) (layer Bottom) (polygon (pts (xy 0 0) (xy 5 5))))
)
"""

#: 无 drill 字面量的 via（上游实况靶）
SYNTH_VIA_NO_DRILL = """(kicad_pcb (version 20171130) (host pcbnew "x")
  (general (tracks 1) (zones 0) (modules 1) (nets 2))
  (layers (0 Top signal) (31 Bottom signal))
  (setup (trace_min 0.2) (trace_clearance 0.1) (via_min_size 0.4) (via_min_drill 0.3))
  (net 0 "")
  (net 1 GND)
  (module Lib:A (layer Top)
    (at 1.0 1.0)
    (fp_text reference U1 (at 0 0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.3 0.6) (layers F.Cu) (net 1 GND))
    (pad 2 smd rect (at 2.0 0.0) (size 0.3 0.6) (layers F.Cu) (net 1 GND))
  )
  (segment (start 1.0 1.0) (end 2.0 1.0) (width 0.25) (layer Top) (net 1))
  (via (at 1.5 1.0) (size 1.0) (layers Top Bottom) (net 1))
)
"""

DRC_ALL = {
    "$schema": "https://schemas.kicad.org/drc.v1.json",
    "kicad_version": "10.0.5", "coordinate_units": "mm",
    "date": "2026-09-03T00:00:00", "source": "staged.kicad_pcb",
    "included_severities": ["error", "warning", "exclusion"],
    "schematic_parity": [],
    "unconnected_items": [],
    "violations": [
        {"type": "solder_mask_bridge", "severity": "error", "items": []},
        {"type": "silk_over_copper", "severity": "warning", "items": []},
    ],
}
DRC_ERROR = {
    "$schema": "https://schemas.kicad.org/drc.v1.json",
    "kicad_version": "10.0.5", "coordinate_units": "mm",
    "date": "2026-09-03T00:00:00", "source": "staged.kicad_pcb",
    "included_severities": ["error"],
    "schematic_parity": [],
    "unconnected_items": [],
    "violations": [
        {"type": "solder_mask_bridge", "severity": "error", "items": []},
    ],
}

THRESHOLDS = {"min_track_width_mm": 0.2, "min_clearance_mm": 0.1,
              "via_min_size_mm": 0.4, "via_min_drill_mm": 0.3}
SHA = "a" * 64
SHA2 = "b" * 64


def _geometry():
    return cs.parse_routed_geometry(SYNTH_ROUTED)


def _drc_summary():
    return cs.summarize_drc(DRC_ALL, DRC_ERROR)


def _declaration(**over):
    kw = dict(profile_id="synth-1", board_id="synth", dataset_role="train",
              reference_route_path="datasets/x/raw/synth.kicad_pcb",
              reference_route_sha256=SHA,
              profile_threshold_keys=sorted(THRESHOLDS),
              prior_state_note="测试：此前=not_executed")
    kw.update(over)
    return cs.build_route_check_declaration(**kw)


def _refs(**over):
    refs = {
        "reference_route": {"path": "datasets/x/raw/synth.kicad_pcb",
                            "sha256": SHA},
        "staged_board": {"path": "out/staging/synth.kicad_pcb",
                         "sha256": SHA},
        "route_check_declaration": {
            "path": "profiles/synth-1/route-check.json", "sha256": SHA2},
        "profile": {"path": "profiles/synth-1/profile.json", "sha256": SHA2},
        "drc_severity_error": {
            "path": "out/check/synth/synth.drc-error.json", "sha256": SHA2},
        "drc_severity_all": {
            "path": "out/check/synth/synth.drc-all.json", "sha256": SHA2},
    }
    refs.update(over)
    return refs


def _report(**over):
    kw = dict(profile_id="synth-1", board_id="synth",
              dataset_role="train",
              declaration=_declaration(),
              geometry=_geometry(), drc_summary=_drc_summary(),
              profile_thresholds=THRESHOLDS, input_refs=_refs())
    kw.update(over)
    return cs.build_check_report(**kw)


# ---------------------------------------------------------------------------
# 1. routed 板几何解析
# ---------------------------------------------------------------------------

def test_parse_routed_geometry_counts_and_mins():
    g = _geometry()
    by = {n["name"]: n for n in g["per_net"]}
    assert by["+5V"]["segment_count"] == 1 and by["+5V"]["pad_count"] == 2
    assert by["GND"]["via_count"] == 1 and by["GND"]["zone_count"] == 1
    assert by["GND"]["arc_count"] == 1
    assert by["N$1"]["copper_item_count"] == 0 and by["N$1"]["pad_count"] == 2
    assert by["SIG"]["pad_count"] == 1  # 单焊盘命名网
    assert g["actual_min"] == {"track_width_mm": 0.2032,
                               "via_size_mm": 0.8, "via_drill_mm": 0.4}
    assert g["vias_without_drill_token"] == 0
    assert g["setup"]["trace_min"] == "0.2"
    assert g["items_bound_outside_declared_nets"] == 0


def test_parse_via_without_drill_token():
    g = cs.parse_routed_geometry(SYNTH_VIA_NO_DRILL)
    assert g["vias_without_drill_token"] == 1
    assert g["actual_min"]["via_drill_mm"] is None
    assert g["actual_min"]["via_size_mm"] == 1.0


def test_advisory_zero_geometry_flags_multi_pad_named_only():
    flagged = cs.advisory_zero_geometry_nets(_geometry())
    assert [f["name"] for f in flagged] == ["N$1"]


def test_parse_fail_closed_on_non_board():
    with pytest.raises(ValueError):
        cs.parse_routed_geometry("(not_a_board)")


# ---------------------------------------------------------------------------
# 2. DRC 双 severity 摘要
# ---------------------------------------------------------------------------

def test_summarize_drc_counts_and_consistency():
    s = _drc_summary()
    ds = s["dual_severity"]
    assert ds["severity_error_batch"]["violations_by_severity"] == {
        "error": 1}
    assert ds["severity_all_final"]["violations_by_severity"] == {
        "error": 1, "warning": 1}
    assert s["consistency"]["error_count_equal_across_runs"] is True
    assert s["connectivity_authority_input"]["unconnected_items"] == 0
    assert s["connectivity_authority_input"][
        "connectivity_type_violations"] == {}


def test_summarize_drc_flags_connectivity_types():
    all_d = json.loads(json.dumps(DRC_ALL))
    all_d["unconnected_items"] = [{"description": "x", "pos": {}}]
    all_d["violations"].append({"type": "unconnected_wire",
                                "severity": "error", "items": []})
    s = cs.summarize_drc(all_d, DRC_ERROR)
    assert s["connectivity_authority_input"]["unconnected_items"] == 1
    assert s["connectivity_authority_input"][
        "connectivity_type_violations"] == {"unconnected_wire": {"error": 1}}
    assert s["connectivity_authority_input"][
        "connectivity_type_violation_total"] == 1


def test_summarize_drc_fail_closed_on_non_drc_json():
    with pytest.raises(ValueError):
        cs.summarize_drc({"violations": []}, DRC_ERROR)


# ---------------------------------------------------------------------------
# 3. route/check 声明（D17 口径）
# ---------------------------------------------------------------------------

def test_declaration_content_and_holdout_note():
    d = _declaration(dataset_role="holdout")
    assert d["route_scope"] == cs.ROUTE_SCOPE
    assert "不生成布线" in d["route_scope_note"]
    assert "holdout" in d["holdout_note"]
    assert d["drc_max_error_severity"] is None
    assert d["reference_route"] == {
        "path": "datasets/x/raw/synth.kicad_pcb", "sha256": SHA}


def test_declaration_fail_closed_on_host_path_and_bad_sha():
    with pytest.raises(ValueError):
        _declaration(reference_route_path=r"F:\host\board.kicad_pcb")
    with pytest.raises(ValueError):
        _declaration(reference_route_sha256="zz")
    with pytest.raises(ValueError):
        _declaration(dataset_role="other")


# ---------------------------------------------------------------------------
# 4. check 报告 verdict（正向+负向）
# ---------------------------------------------------------------------------

def test_check_report_pass_path_full_checks():
    r = _report()
    assert r["result"] == "pass"
    assert all(c["pass"] for c in r["checks"])
    ids = {c["id"] for c in r["checks"]}
    assert "connectivity_kicad_cli" in ids
    assert "staging_copy_byte_identical" in ids
    assert "threshold_identity_with_reference_setup" in ids
    assert "actual_geometry_meets_thresholds" in ids
    assert r["route_scope"] == "reference_verification"
    assert r["authority"]["connectivity"] == "kicad_cli_drc_unconnected_items"
    assert "非布线生成" in r["authority"]["execution"]
    # 红线 4：不得出现肯定语气的布线能力/生成已执行声明（否定语境除外）
    text = json.dumps(r, ensure_ascii=False)
    assert "已具备布线能力" not in text
    assert "route generation executed" not in text.replace(
        "非 route generation executed", "")
    # advisory 零几何网如实flag但不进 verdict
    adv = r["advisory_checks"][0]
    assert adv["flagged_net_count"] == 1 and adv["advisory"] is True
    assert r["result"] == "pass"


def test_check_report_negative_unconnected_fails():
    all_d = json.loads(json.dumps(DRC_ALL))
    all_d["unconnected_items"] = [{"description": "x", "pos": {}}]
    r = _report(drc_summary=cs.summarize_drc(all_d, DRC_ERROR))
    conn = [c for c in r["checks"] if c["id"] == "connectivity_kicad_cli"][0]
    assert conn["pass"] is False and r["result"] == "fail"


def test_check_report_negative_drc_limit_exceeded_fails():
    all_d = json.loads(json.dumps(DRC_ALL))
    err_d = json.loads(json.dumps(DRC_ERROR))
    for d in (all_d, err_d):
        d["violations"].append({"type": "clearance", "severity": "error",
                                "items": []})
    decl = _declaration()
    decl["drc_max_error_severity"] = 1  # 实际 error=2 → 超限
    r = _report(declaration=decl, drc_summary=cs.summarize_drc(all_d, err_d))
    lim = [c for c in r["checks"]
           if c["id"] == "drc_error_count_within_declared_limit"][0]
    assert lim["pass"] is False and r["result"] == "fail"


def test_check_report_negative_staging_mismatch_fails():
    refs = _refs(staged_board={"path": "out/staging/synth.kicad_pcb",
                               "sha256": SHA2})
    r = _report(input_refs=refs)
    st = [c for c in r["checks"]
          if c["id"] == "staging_copy_byte_identical"][0]
    assert st["pass"] is False and r["result"] == "fail"


def test_check_report_negative_threshold_and_setup_drift_fail():
    th = dict(THRESHOLDS, min_track_width_mm=0.3)  # 实际 0.2032 < 0.3
    r = _report(profile_thresholds=th)
    geo = [c for c in r["checks"]
           if c["id"] == "actual_geometry_meets_thresholds"][0]
    assert geo["pass"] is False and r["result"] == "fail"
    g = _geometry()
    g["setup"]["trace_min"] = "0.25"  # setup 漂移 → identity 不符
    r2 = _report(geometry=g)
    ident = [c for c in r2["checks"]
             if c["id"] == "threshold_identity_with_reference_setup"][0]
    assert ident["pass"] is False and r2["result"] == "fail"


def test_check_report_skips_drill_check_when_no_literal():
    g = cs.parse_routed_geometry(SYNTH_VIA_NO_DRILL)
    r = _report(geometry=g)
    entries = r["threshold_reconciliation"]["actual_geometry"]["entries"]
    drill = [e for e in entries if e["check"] == "via_min_drill_mm"][0]
    assert drill["status"] == "skipped"
    assert r["field_missingness"]["via_drill_token"].startswith("1 个")
    assert r["result"] == "pass"  # 跳过≠失败（如实记录）


def test_check_report_fail_closed_paths():
    decl = _declaration()
    decl["route_scope"] = "route_generation"  # 口径冒用 → fail-closed
    with pytest.raises(ValueError):
        _report(declaration=decl)
    with pytest.raises(ValueError):
        _report(input_refs=_refs(profile={"path": "p", "sha256": "short"}))
    with pytest.raises(ValueError):
        _report(input_refs=_refs(staged_board={"path": r"C:\x",
                                               "sha256": SHA}))


def test_check_report_no_wall_clock_no_host_path():
    text = json.dumps(_report(), ensure_ascii=False)
    assert "evaluated_at" not in text and "elapsed_s" not in text
    assert "\\" not in text and ":/" not in text.replace("https://", "")


# ---------------------------------------------------------------------------
# 5. 执行汇总记录
# ---------------------------------------------------------------------------

def test_execution_record_summary_and_fail_closed():
    entry = {
        "profile_id": "synth-1", "board_id": "synth", "dataset_role": "train",
        "reference_route": {"path": "datasets/x/raw/synth.kicad_pcb",
                            "sha256": SHA},
        "staged_board_sha256": SHA,
        "declaration": {"path": "profiles/synth-1/route-check.json",
                        "sha256": SHA2},
        "check_report": {"path": "out/check/synth/check-report.json",
                         "sha256": SHA2, "result": "pass"},
        "drc": {"severity_error": {"path": "p1", "exit": 0, "violations": 1},
                "severity_all": {"path": "p2", "exit": 0, "violations": 2}},
        "kicad_cli_version": "10.0.5",
    }
    rec = cs.build_execution_record(entries=[entry],
                                    toolchain_lock_sha256=SHA)
    assert rec["all_pass"] is True
    assert rec["summary"]["results"] == {"pass": 1}
    assert rec["route_scope"] == "reference_verification"
    assert "布线生成未发生" in rec["stage_semantics"]
    with pytest.raises(ValueError):
        cs.build_execution_record(entries=[], toolchain_lock_sha256=SHA)
    with pytest.raises(ValueError):
        cs.build_execution_record(entries=[entry],
                                  toolchain_lock_sha256="bad")
    bad = dict(entry, staged_board_sha256=SHA2)
    rec2 = cs.build_execution_record(entries=[bad],
                                     toolchain_lock_sha256=SHA)
    assert rec2["all_pass"] is False


# ---------------------------------------------------------------------------
# 6. 真实 bm1 回放（routed 参考态 + S6 DRC baseline + S8 check 报告）
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.isfile(os.path.join(
        "datasets", "pcbbenchmarks-r1", "raw", "bm1",
        "bm1.routed.kicad_pcb")), reason="bm1 数据集不在场")
def test_real_bm1_geometry_and_check_report_replay():
    g = cs.parse_routed_geometry(open(os.path.join(
        "datasets", "pcbbenchmarks-r1", "raw", "bm1", "bm1.routed.kicad_pcb"),
        encoding="utf-8").read())
    assert g["actual_min"]["track_width_mm"] == 0.2032
    assert g["vias_without_drill_token"] == 0
    assert cs.advisory_zero_geometry_nets(g) == []
    assert g["setup"]["trace_min"] == "0.2"
    s = cs.summarize_drc(
        json.load(open(os.path.join("out", "v3-tl5", "drc", "bm1",
                                    "bm1.routed.drc-all.json"),
                       encoding="utf-8")),
        json.load(open(os.path.join("out", "v3-tl5", "drc", "bm1",
                                    "bm1.routed.drc-error.json"),
                       encoding="utf-8")))
    assert s["dual_severity"]["severity_error_batch"][
        "violations_by_severity"] == {"error": 126}
    assert s["dual_severity"]["severity_all_final"][
        "violations_by_severity"] == {"error": 126, "warning": 132}
    assert s["connectivity_authority_input"]["unconnected_items"] == 0
    # S8 落盘 check 报告 = 纯函数重放（byte-exact）
    path = os.path.join("out", "v3-tl5", "check", "pcbbm-bm1",
                        "check-report.json")
    if os.path.isfile(path):
        on_disk = json.load(open(path, encoding="utf-8"))
        assert on_disk["result"] == "pass"
        assert on_disk["route_scope"] == "reference_verification"
        assert hashing.sha256_text(
            cs.dumps_canonical(on_disk)) == hashing.sha256_file(path)
