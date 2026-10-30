"""TD7 外部执行 backend qualification 执行器测试（全合成数据）。

覆盖面：选板规则/工具链登记+ASM-8 对账/锁提案（不执行）/allowlist+
argv 构造（负向：遍历、非白名单、shell 拼接）/SES 解析与确定性归一
（fail-closed）/L1 层纯净（plane 越层、via 跨度、线宽）/板度量
（KiCad5 与 KiCad10 双形态）+参考对比/DRC 双 severity delta/五 stage
装配（not_executed、内容性 fail）/run record（超时、非零退出、hash
不符、截断→blocked+隔离；argv 归档只存 basename）/资格报告四轴谓词
（registry blocked、零样本、policy 违例、stage 序列篡改、
nondeterminism 如实记录不虚 claim）。
"""

import pytest

from pcbflow import backend_qualification as bq
from pcbflow import external_backend, hashing, schemas

_SHA_A = "ab" * 32
_SHA_B = "cd" * 32
_LOCK_SHA = "ef" * 32

_JAVA = r"C:\jre\bin\java.exe"
_JAR = r"C:\tools\freerouting.jar"
_DSN = r"C:\stg\board.dsn"
_SES = r"C:\stg\run1.ses"

_PROFILE_2L = {"layers": [{"name": "F.Cu", "role": "signal"},
                          {"name": "B.Cu", "role": "signal"}]}
_PROFILE_4L = {"layers": [{"name": "F.Cu", "role": "signal"},
                          {"name": "In1.Cu", "role": "power"},
                          {"name": "In2.Cu", "role": "signal"},
                          {"name": "B.Cu", "role": "plane"}]}


# ---------------------------------------------------------------------------
# 合成数据工厂
# ---------------------------------------------------------------------------

def _argv(**overrides):
    argv = bq.build_freerouting_argv(java_abs=_JAVA, jar_abs=_JAR,
                                     dsn_abs=_DSN, ses_abs=_SES)
    for i, v in overrides.items():
        argv[int(i)] = v
    return argv


def _ses_text(net_lines="", session_name="run1",
              offband_net=False) -> str:
    extra = ""
    if offband_net:
        extra = ('(net "OFFBAND" (wire (path In9.Cu 2000 1000 1000 '
                 '2000 1000)))\n')
    return f"""(session {session_name}
  (base_design {session_name})
  (placement (resolution um 10))
  (network_out
    (net GND
      (wire
        (path F.Cu 2000
          1000 -90500
          145000 -65000
        )
        (type protect)
      )
      (via "Via[0-1]_600:300_um" 151500 -508000
        (type protect)
      )
    )
    (net SIG1
      (wire
        (path B.Cu 2540
          1000 1000
          21000 1000
        )
      )
    )
{extra}  )
)
"""


def _entry(pid, nets, role="train", **kw):
    base = {"profile_id": pid, "named_net_count": nets,
            "unrouted": True, "reference_available": True,
            "dataset_role": role}
    base.update(kw)
    return base


def _registry(**overrides):
    def item(sha=_SHA_A, version="v2.3.0 (build 2026-08-07)", exists=True):
        return {"rel_path": "../../tools/x.bin",
                "abs_path_exists": exists, "sha256": sha,
                "version": version}
    kw = dict(jar=item(), java=item(version="25.0.4+7"),
              kicad_cli=item(version="10.0.5"))
    kw.update(overrides)
    return bq.build_toolchain_registry(**kw)


def _ses_ok():
    return {"present": True, "size_bytes": 128, "size_bound":
            bq.MAX_SES_BYTES, "truncated": False, "parsed": True,
            "hash_matches": True}


def _l1_ok():
    return {"checks": [{"id": "ses_layer_purity", "pass": True,
                        "evidence": "ok"},
                       {"id": "ses_via_span_within_stackup",
                        "pass": True, "evidence": "ok"},
                       {"id": "ses_width_sanity", "pass": True,
                        "evidence": "ok"},
                       {"id": "ses_network_out_nonempty", "pass": True,
                        "evidence": "ok"}],
            "all_pass": True, "layer_purity_pass": True}


def _drc_zero_new():
    return {"executed": True,
            "severity_error": {"new_violation_types": {},
                               "new_count": 0, "removed_count": 5},
            "severity_all": {"new_violation_types": {}, "new_count": 0,
                             "new_error_count": 0, "new_warning_count": 0,
                             "removed_count": 30,
                             "removed_error_count": 24,
                             "removed_warning_count": 6},
            "unconnected_items": {"baseline_unrouted": 24,
                                  "after_freerouting": 0}}


def _run_record(**overrides):
    kw = dict(
        execution_id="TD7-S11-SMALL", project_id="proj-synth",
        profile_id="profile-synth",
        source_snapshot_sha256=_SHA_A, staging_path_sha256=_SHA_B,
        tool_version="freerouting-2.3.0_2026-08-07",
        toolchain_lock_sha256=_LOCK_SHA, request_sha256=_SHA_A,
        response_sha256=_SHA_B, argv=_argv(), timeout_s=600,
        exit_status=0, ses_observed=_ses_ok(), l1_result=_l1_ok(),
        drc_result=_drc_zero_new(),
        finalization={"evidence_complete": True, "detail": "ok"},
        quality={"connectivity": {"baseline_unrouted": 24,
                                  "after_freerouting": 0}})
    kw.update(overrides)
    return bq.build_run_record(**kw)


# ---------------------------------------------------------------------------
# 1) 选板规则
# ---------------------------------------------------------------------------

def test_selection_rule_small_mid_large_deterministic():
    entries = [
        _entry("smoke-2l", 4),                       # 排除：smoke
        _entry("p-degenerate", 5),                   # 排除：band 外小板
        _entry("p-holdout", 12, role="holdout"),     # 排除：holdout
        _entry("p-a", 12),                           # small（band 内最小）
        _entry("p-b", 13),
        _entry("p-mid", 41), _entry("p-mid2", 43),
        _entry("p-large", 99), _entry("p-large2", 103)]
    sel = bq.select_qualification_boards(entries)
    assert sel["slots"]["small"]["profile_id"] == "p-a"
    assert sel["slots"]["mid"]["profile_id"] == "p-mid"
    assert sel["slots"]["large"]["profile_id"] == "p-large"
    assert sel["selected_profile_ids"] == ["p-a", "p-large", "p-mid"]
    assert sel["candidate_count"] == 7  # 9 − smoke − holdout − degenerate


def test_selection_train_only_and_validation_fallback():
    only_validation = [_entry("p-v1", 12, role="validation"),
                       _entry("p-vm", 50, role="validation"),
                       _entry("p-v2", 99, role="validation")]
    sel = bq.select_qualification_boards(only_validation)
    assert sel["slots"]["small"]["profile_id"] == "p-v1"
    assert sel["slots"]["mid"]["profile_id"] == "p-vm"
    assert sel["slots"]["large"]["profile_id"] == "p-v2"
    with_holdout = only_validation + [_entry("p-h", 41, role="holdout")]
    sel2 = bq.select_qualification_boards(with_holdout)
    assert sel2["slots"]["mid"]["profile_id"] == "p-vm"  # holdout 恒禁


def test_selection_missing_slot_and_invalid_count():
    sel = bq.select_qualification_boards(
        [_entry("p-mid", 41), _entry("p-b", 99)])
    assert sel["slots"]["small"]["status"] == "no_candidate_in_range"
    assert sel["slots"]["mid"]["profile_id"] == "p-mid"
    assert sel["slots"]["large"]["profile_id"] == "p-b"
    with pytest.raises(ValueError):
        bq.select_qualification_boards(
            [_entry("p-bad", 0, role="train")])


# ---------------------------------------------------------------------------
# 2) 工具链登记 + ASM-8 对账 + 锁提案
# ---------------------------------------------------------------------------

def test_registry_pass_and_asm8_match():
    reg = _registry()
    assert reg["registry_verdict"] == "pass"
    rec = reg["asm8_reconciliation"]["freerouting_jar"]
    assert rec["sha256_matches_asm8"] is False  # _SHA_A 非 3cf18d60 前缀
    assert rec["version_matches_asm8"] is True
    assert reg["asm8_reconciliation"]["java_runtime"][
        "version_matches_asm8"] is True
    assert reg["asm8_reconciliation"]["kicad_cli"][
        "version_matches_lock"] is True


def test_registry_blocked_on_missing_sha_or_path_or_version():
    good_jar = {"rel_path": "../../tools/x.bin", "abs_path_exists": True,
                "sha256": _SHA_A,
                "version": "v2.3.0 (build 2026-08-07)"}
    for override, key in (({"sha256": None}, "sha256"),
                          ({"abs_path_exists": False}, "abs_path_exists"),
                          ({"version": None}, "version")):
        jar = dict(good_jar, **override)
        reg = bq.build_toolchain_registry(
            jar=jar,
            java={"rel_path": "../../jre", "abs_path_exists": True,
                  "sha256": _SHA_B, "version": "25.0.4+7"},
            kicad_cli={"rel_path": "../../kc.exe", "abs_path_exists": True,
                       "sha256": _SHA_A, "version": "10.0.5"})
        assert reg["registry_verdict"] == "blocked"
        assert any(key in e for e in reg["errors"])


def test_registry_asm8_exact_sha_prefix_matches():
    reg = _registry(jar={"rel_path": "../../fr.jar",
                         "abs_path_exists": True,
                         "sha256": "3cf18d60" + "f" * 56,
                         "version": "v2.3.0 (build 2026-08-07)"})
    assert reg["asm8_reconciliation"]["freerouting_jar"][
        "sha256_matches_asm8"] is True


def test_lock_proposal_not_executed_and_gated_on_registry():
    prop = bq.build_toolchain_lock_proposal(_registry())
    assert prop["status"] == "proposed_not_executed"
    assert prop["lockable"] is True
    assert prop["proposed_entries"]["freerouting"]["sha256"] == _SHA_A
    blocked = bq.build_toolchain_lock_proposal(
        _registry(jar={"rel_path": "../../fr.jar",
                       "abs_path_exists": False, "sha256": None,
                       "version": None}))
    assert blocked["lockable"] is False
    assert blocked["proposed_entries"] is None
    assert "不改 toolchain_lock" in blocked["red_line_note"]


# ---------------------------------------------------------------------------
# 3) allowlist + argv
# ---------------------------------------------------------------------------

def test_argv_fixed_tail_and_determinism_params():
    argv = bq.build_freerouting_argv(java_abs=_JAVA, jar_abs=_JAR,
                                     dsn_abs=_DSN, ses_abs=_SES)
    assert argv[:7] == [_JAVA, "-jar", _JAR, "-de", _DSN, "-do", _SES]
    assert argv[7:] == ["-mt", "1", "-is", "sequential", "-mp", "3"]


def test_argv_rejects_bad_passes_traversal_relative():
    with pytest.raises(ValueError):
        bq.build_freerouting_argv(java_abs=_JAVA, jar_abs=_JAR,
                                  dsn_abs=_DSN, ses_abs=_SES,
                                  max_passes=0)
    with pytest.raises(ValueError):
        bq.build_freerouting_argv(java_abs=_JAVA, jar_abs=_JAR,
                                  dsn_abs=r"C:\stg\..\x.dsn",
                                  ses_abs=_SES)
    with pytest.raises(ValueError):
        bq.build_freerouting_argv(java_abs="java.exe", jar_abs=_JAR,
                                  dsn_abs=_DSN, ses_abs=_SES)


def test_declaration_and_policy_validate_pass():
    argv = _argv()
    decl = bq.external_backend_validate_target(argv=argv)
    assert decl["executable_allowlist"] == [_JAVA]
    assert _JAR in decl["path_allowlist"]
    assert decl["network_policy"] == "deny"
    record = {**external_backend.build_execution_record(
        execution_id="x-1", project_id="p", profile_id="q",
        source_snapshot_sha256=_SHA_A, staging_path_sha256=_SHA_B,
        backend="freerouting-cli-jar", protocol="cli-argv",
        tool_version="v", toolchain_lock_sha256=_LOCK_SHA,
        started_by="t", timeout_s=60), "argv_or_rpc": argv}
    assert external_backend.validate_policy(record, decl) == []


def test_declaration_rejects_traversal_and_offallowlist():
    decl = bq.external_backend_validate_target(argv=_argv())
    base = {"backend": "freerouting-cli-jar", "protocol": "cli-argv",
            "network_policy": "deny", "write_scope": "staging_only",
            "live_board_touched": False}
    bad = dict(base, argv_or_rpc=_argv(**{"4": r"C:\stg\..\etc\board.dsn"}))
    errs = external_backend.validate_policy(bad, decl)
    assert any(".." in e for e in errs)
    off = dict(base, argv_or_rpc=_argv(**{"6": r"C:\other\run1.ses"}))
    assert any("非 allowlist" in e
               for e in external_backend.validate_policy(off, decl))
    other_exe = dict(base, argv_or_rpc=_argv(
        **{"0": r"C:\Windows\System32\cmd.exe"}))
    assert any("executable_allowlist" in e for e in
               external_backend.validate_policy(other_exe, decl))
    shell = dict(base, argv_or_rpc=f"{_JAVA} -jar {_JAR}")
    assert any("shell" in e for e in
               external_backend.validate_policy(shell, decl))


# ---------------------------------------------------------------------------
# 4) SES 解析 + 确定性归一
# ---------------------------------------------------------------------------

def test_parse_ses_network_out_counts_and_length():
    g = bq.parse_ses_network_out(_ses_text())
    assert g["header"] == {"session": "run1", "base_design": "run1"}
    assert g["resolution"] == "um 10"
    assert g["net_count_in_network_out"] == 2
    assert g["totals"]["wires"] == 2 and g["totals"]["vias"] == 1
    assert g["layer_histogram"] == {"B.Cu": 1, "F.Cu": 1}
    # GND: (1000,-90500)→(145000,-65000) + SIG1: 20000 长（0.1um 单位）
    expect_gnd = ((145000 - 1000) ** 2 + (-65000 + 90500) ** 2) ** 0.5
    assert abs(g["totals"]["wire_length_mm"]
               - (expect_gnd + 20000) / 10000.0) < 1e-3
    assert g["nets"]["GND"]["protected_items"] == 2


def test_parse_ses_fail_closed():
    with pytest.raises(ValueError):
        bq.parse_ses_network_out("(session x\n (placement\n)\n)")
    with pytest.raises(ValueError):
        bq.parse_ses_network_out(
            "(session x\n (network_out\n (net N\n (wire (path F.Cu 0\n"
            " 1 2 3\n))))))\n")


def test_determinism_normalization_quoted_and_bare():
    t1 = _ses_text(session_name="run1")
    t2 = _ses_text(session_name="run2")
    n1 = bq.normalize_ses_for_determinism(t1)
    n2 = bq.normalize_ses_for_determinism(t2)
    assert n1["header_line_replacements"] == 2
    assert n1["normalized_sha256"] == n2["normalized_sha256"]
    quoted = t1.replace("(session run1", '(session "run1"').replace(
        "(base_design run1", '(base_design "run1"')
    assert bq.normalize_ses_for_determinism(quoted)[
        "normalized_sha256"] == n1["normalized_sha256"]


def test_assess_determinism_honest_paths():
    under = bq.assess_determinism(
        [{"run_id": "r1", "ses_sha256": _SHA_A,
          "normalized_sha256": _SHA_A}])
    assert under["assessed"] is False and under["deterministic"] is None
    same_norm = bq.assess_determinism([
        {"run_id": "r1", "ses_sha256": _SHA_A,
         "normalized_sha256": _SHA_B},
        {"run_id": "r2", "ses_sha256": _SHA_A,
         "normalized_sha256": _SHA_B}])
    assert same_norm["byte_exact"] is True
    assert same_norm["deterministic"] is True
    diff_geom = bq.assess_determinism([
        {"run_id": "r1", "ses_sha256": _SHA_A,
         "normalized_sha256": _SHA_A},
        {"run_id": "r2", "ses_sha256": _SHA_B,
         "normalized_sha256": _SHA_B},
        {"run_id": "r3", "ses_sha256": _LOCK_SHA,
         "normalized_sha256": _LOCK_SHA}])
    assert diff_geom["deterministic"] is False
    assert "NONDETERMINISTIC" in diff_geom["claim"]
    assert diff_geom["run_count"] == 3


# ---------------------------------------------------------------------------
# 5) L1 几何 + 层纯净
# ---------------------------------------------------------------------------

def test_l1_layer_purity_pass_and_plane_reject():
    ok = bq.ses_l1_geometry_check(
        bq.parse_ses_network_out(_ses_text()), _PROFILE_2L)
    assert ok["all_pass"] is True and ok["layer_purity_pass"] is True
    rej = bq.ses_l1_geometry_check(
        bq.parse_ses_network_out(_ses_text(offband_net=True)),
        _PROFILE_2L)
    assert rej["layer_purity_pass"] is False
    assert any(c["id"] == "ses_layer_purity" and not c["pass"]
               for c in rej["checks"])


def test_l1_via_span_and_width_fail_closed():
    bad_span = _ses_text().replace("Via[0-1]_600:300_um",
                                   "Via[0-5]_600:300_um")
    r = bq.ses_l1_geometry_check(
        bq.parse_ses_network_out(bad_span), _PROFILE_2L)
    assert any(c["id"] == "ses_via_span_within_stackup"
               and not c["pass"] for c in r["checks"])
    bad_width = _ses_text().replace("(path F.Cu 2000", "(path F.Cu 0")
    r2 = bq.ses_l1_geometry_check(
        bq.parse_ses_network_out(bad_width), _PROFILE_2L)
    assert any(c["id"] == "ses_width_sanity" and not c["pass"]
               for c in r2["checks"])
    empty = bq.ses_l1_geometry_check(
        {"nets": {}, "layer_histogram": {}}, _PROFILE_2L)
    assert empty["all_pass"] is False


def test_l1_four_layer_signal_on_power_rejected():
    ses = bq.parse_ses_network_out(_ses_text())
    r = bq.ses_l1_geometry_check(ses, _PROFILE_4L)
    assert r["layer_purity_pass"] is False  # SIG1 段在 B.Cu=plane


# ---------------------------------------------------------------------------
# 6) 板度量（KiCad5/KiCad10 双形态）+ 参考对比
# ---------------------------------------------------------------------------

_KICAD5_BOARD = """(kicad_pcb (version 20171130)
  (net 1 "GND") (net 2 "SIG1")
  (segment (start 0 0) (end 10 0) (width 0.254) (layer F.Cu) (net 1))
  (segment (start 10 0) (end 10 10) (width 0.254) (layer B.Cu) (net 2))
  (via (at 5 5) (size 0.8) (drill 0.4) (layers F.Cu B.Cu) (net 1))
)
"""

_KICAD10_BOARD = """(kicad_pcb (version 20260206)
  (segment (start 0 0) (end 10 0) (width 0.2) (layer "F.Cu") (net "GND"))
  (via (at 5 5) (size 0.6) (drill 0.3) (net "GND"))
)
"""


def test_board_metrics_kicad5_and_kicad10_forms():
    m5 = bq.board_route_metrics(_KICAD5_BOARD)
    assert m5["geometry_counts"] == {"segments": 2, "arcs": 0,
                                     "vias": 1, "zones": 0}
    assert m5["layer_histogram"] == {"B.Cu": 1, "F.Cu": 1}
    assert abs(m5["total_segment_length_mm"] - 20.0) < 1e-9
    assert m5["actual_min"]["track_width_mm"] == 0.254
    assert m5["named_net_count"] == 2
    m10 = bq.board_route_metrics(_KICAD10_BOARD)
    assert m10["geometry_counts"]["segments"] == 1
    assert m10["geometry_counts"]["vias"] == 1
    assert m10["named_net_count"] == 1
    assert abs(m10["total_segment_length_mm"] - 10.0) < 1e-9
    with pytest.raises(ValueError):
        bq.board_route_metrics("(not_a_board 1)")


def test_compare_to_reference_deltas():
    a = bq.board_route_metrics(_KICAD5_BOARD)
    b = bq.board_route_metrics(_KICAD10_BOARD)
    cmp_ = bq.compare_to_reference(a, b)
    assert cmp_["segments"]["delta"] == 1
    assert cmp_["vias"]["delta"] == 0
    assert cmp_["total_segment_length_mm"]["delta"] == 10.0
    assert "不是布线质量 authority" in cmp_["authority_note"]


# ---------------------------------------------------------------------------
# 7) DRC 双 severity delta
# ---------------------------------------------------------------------------

def _drc_json(items):
    return {"violations": [
        {"severity": s, "type": t} for s, t in items],
        "unconnected_items": []}


def test_drc_dual_severity_delta_new_and_removed():
    base_err = _drc_json([("error", "track_width")] * 2)
    act_err = _drc_json([("error", "track_width")] * 2,
                        )
    act_err["violations"].append({"severity": "error",
                                  "type": "clearance"})
    base_all = _drc_json([("error", "track_width")] * 2
                         + [("warning", "silk_overlap")] * 3)
    act_all = _drc_json([("error", "track_width")] * 2
                        + [("error", "clearance"),
                           ("warning", "silk_overlap")])
    act_all["unconnected_items"] = [{"x": 1}]
    d = bq.drc_dual_severity_delta(
        baseline_error=base_err, actual_error=act_err,
        baseline_all=base_all, actual_all=act_all)
    assert d["severity_error"]["new_count"] == 1
    assert d["severity_error"]["new_violation_types"] == {
        "error:clearance": 1}
    assert d["severity_all"]["new_count"] == 1
    assert d["severity_all"]["new_error_count"] == 1
    assert d["severity_all"]["removed_warning_count"] == 2
    assert d["unconnected_items"] == {"baseline_unrouted": 0,
                                      "after_freerouting": 1,
                                      "authority":
                                      "kicad_cli_drc_unconnected_items"}


# ---------------------------------------------------------------------------
# 8) stage 装配 + run record（blocked 负向四路径）
# ---------------------------------------------------------------------------

def test_stage_assembly_happy_and_not_executed():
    stages = bq.build_stage_statuses(
        ses_observed=_ses_ok(), l1_result=_l1_ok(),
        drc_result=_drc_zero_new(),
        finalization={"evidence_complete": True, "detail": "ok"})
    assert [s["stage"] for s in stages] == list(
        external_backend.STAGE_ORDER)
    assert all(s["status"] == "pass" for s in stages)
    none_drc = bq.build_stage_statuses(
        ses_observed=_ses_ok(), l1_result=_l1_ok(),
        drc_result=None, finalization=None)
    assert [s["status"] for s in none_drc][2:] == [
        "not_executed", "not_executed", "not_executed"]


def test_stage_assembly_drc_new_errors_fail():
    bad = _drc_zero_new()
    bad["severity_error"]["new_count"] = 18
    bad["severity_all"]["new_count"] = 18
    stages = bq.build_stage_statuses(
        ses_observed=_ses_ok(), l1_result=_l1_ok(), drc_result=bad,
        finalization={"evidence_complete": True})
    by = {s["stage"]: s["status"] for s in stages}
    assert by["drc_batch_severity_error"] == "fail"
    assert by["drc_final_severity_all"] == "fail"


def test_run_record_happy_path_verified_candidate():
    rec = _run_record()
    assert rec["policy_validation"]["pass"] is True
    assert rec["pipeline"]["pipeline_status"] == "verified_candidate"
    assert rec["pipeline"]["quarantine_staging"] is False
    assert schemas.validate("external_execution_record",
                            rec["execution_record"]) == []
    assert all(p not in a for a in rec["argv_baseline_names"]["argv"]
               for p in (":\\", "/"))   # 归档无主机绝对路径


def test_run_record_nonzero_exit_timeout_truncation_hashmismatch_blocked():
    nonzero = _run_record(exit_status=3)
    assert nonzero["pipeline"]["pipeline_status"] == "blocked"
    assert nonzero["pipeline"]["quarantine_staging"] is True
    timeout = _run_record(exit_status=None)
    assert timeout["pipeline"]["exit_classification"]["kind"] == \
        "crash_or_unknown"
    assert timeout["pipeline"]["pipeline_status"] == "blocked"
    truncated = _run_record(ses_observed={**_ses_ok(),
                                          "truncated": True})
    assert truncated["stages"][0]["status"] == "fail"
    assert truncated["pipeline"]["pipeline_status"] == "blocked"
    hash_bad = _run_record(ses_observed={**_ses_ok(),
                                         "hash_matches": False})
    assert hash_bad["stages"][0]["status"] == "fail"
    assert hash_bad["pipeline"]["pipeline_status"] == "blocked"


def test_run_record_l1_fail_blocks_pipeline():
    bad_l1 = {"checks": [{"id": "ses_layer_purity", "pass": False,
                          "evidence": "plane"}], "all_pass": False,
              "layer_purity_pass": False}
    rec = _run_record(l1_result=bad_l1)
    assert rec["stages"][1]["status"] == "fail"
    assert rec["pipeline"]["pipeline_status"] == "blocked"


# ---------------------------------------------------------------------------
# 9) 资格报告（四轴谓词 + 如实裁决）
# ---------------------------------------------------------------------------

def _report(runs=None, registry=None, det=None):
    return bq.build_qualification_report(
        toolchain_registry=registry or _registry(),
        selection={"selected_profile_ids": ["p-a"], "slots": {},
                   "rule": {}, "candidate_count": 1},
        run_records=runs if runs is not None else [_run_record()],
        determinism_runs=det if det is not None else [
            {"run_id": "r1", "ses_sha256": _SHA_A,
             "normalized_sha256": _SHA_B},
            {"run_id": "r2", "ses_sha256": _SHA_A,
             "normalized_sha256": _SHA_B}])


def test_report_pass_on_full_contract_axes():
    rep = _report()
    assert rep["verdict"] == "pass"
    assert all(rep["axis_results"][a]["pass"]
               for a in bq.QUALIFICATION_AXES)
    assert rep["engine_determinism"]["deterministic"] is True
    assert rep["quality_facts"][0]["quality"]


def test_report_blocked_on_registry_and_zero_runs():
    blocked_reg = _registry(jar={"rel_path": "../../fr.jar",
                                 "abs_path_exists": False,
                                 "sha256": None, "version": None})
    assert _report(registry=blocked_reg)["verdict"] == "blocked"
    assert _report(runs=[])["verdict"] == "blocked"


def test_report_fail_on_policy_violation():
    bad = _run_record()
    bad["policy_validation"] = {"errors": ["argv[0] 越权"], "pass": False}
    rep = _report(runs=[bad])
    assert rep["verdict"] == "fail"
    assert rep["axis_results"]["security_discipline"]["pass"] is False


def test_report_fail_on_stage_sequence_tamper_and_missing_hash():
    tampered = _run_record()
    tampered["stages"] = tampered["stages"][:4]  # 缺 rollback stage
    assert _report(runs=[tampered])["verdict"] == "fail"
    no_hash = _run_record()
    no_hash["execution_record"]["response_sha256"] = None
    rep2 = _report(runs=[no_hash])
    assert rep2["axis_results"]["record_completeness"]["pass"] is False


def test_report_nondeterminism_recorded_not_claimed():
    rep = _report(det=[
        {"run_id": "r1", "ses_sha256": _SHA_A,
         "normalized_sha256": _SHA_A},
        {"run_id": "r2", "ses_sha256": _SHA_B,
         "normalized_sha256": _SHA_B},
        {"run_id": "r3", "ses_sha256": _LOCK_SHA,
         "normalized_sha256": _LOCK_SHA}])
    assert rep["engine_determinism"]["deterministic"] is False
    assert "NONDETERMINISTIC" in rep["engine_determinism"]["claim"]
    # 测量纪律轴仍 pass（如实测+记实况），但 TL-4 噪声后果在 notes
    assert rep["axis_results"]["reproducibility"]["pass"] is True
    assert any("TL-4" in n for n in rep["notes"])
    # 但未测（<2 次）时轴 fail（不虚评）
    unmeasured = _report(det=[{"run_id": "r1", "ses_sha256": _SHA_A,
                               "normalized_sha256": _SHA_A}])
    assert unmeasured["axis_results"]["reproducibility"]["pass"] is False
    assert unmeasured["verdict"] == "fail"


def test_report_quality_not_predicated_and_gate_predicates():
    rep = _report()
    assert rep["quality_facts"][0]["pipeline_status"] == \
        "verified_candidate"
    preds = bq.qualification_gate_predicates(rep)
    ids = [p["id"] for p in preds]
    assert ids == ["td7_toolchain_registry_available",
                   "td7_qualification_sample_present",
                   "td7_security_discipline",
                   "td7_record_completeness",
                   "td7_verification_chain_executed",
                   "td7_backend_reproducibility",
                   "td7_quality_facts_recorded_not_predicated"]
    assert all(p["value"] for p in preds)
    failed = _report(registry=blocked_registry())
    assert [p["value"] for p in
            bq.qualification_gate_predicates(failed)][0] is False


def blocked_registry():
    return _registry(jar={"rel_path": "../../fr.jar",
                          "abs_path_exists": False, "sha256": None,
                          "version": None})


# ---------------------------------------------------------------------------
# 10) 合同常量
# ---------------------------------------------------------------------------

def test_contract_constants_pinned():
    assert bq.FREEROUTING_FIXED_TAIL == ("-mt", "1", "-is",
                                         "sequential")
    assert list(external_backend.STAGE_ORDER) == [
        "schema_size_validation", "l1_layer_purity",
        "drc_batch_severity_error", "drc_final_severity_all",
        "rollback_ledger_graph"]
    assert bq.BACKEND == "freerouting-cli-jar"
    assert bq.PROTOCOL == "cli-argv"
    assert bq.MODULE_NAME == "pcbflow.backend_qualification"
    assert "qualification pass 不等于布线质量好" in bq.QUALIFICATION_NOTE


# ---------------------------------------------------------------------------
# 11) A/B 统计口径（D20②：N 次重跑+分布+中位数对中位数）
# ---------------------------------------------------------------------------

def test_metric_median_odd_even_and_fail_closed():
    assert bq.metric_median([3, 1, 2]) == 2.0
    assert bq.metric_median([4, 1, 3, 2]) == 2.5
    assert bq.metric_median([7]) == 7.0
    assert bq.metric_median([2.5, 2.5, 2.5]) == 2.5
    # 输入次序无关（确定性）
    assert bq.metric_median([5, 1, 9, 3]) == bq.metric_median(
        [9, 3, 1, 5])
    with pytest.raises(ValueError):
        bq.metric_median([])
    with pytest.raises(ValueError):
        bq.metric_median([1, "x", 3])
    with pytest.raises(ValueError):
        bq.metric_median([1, float("nan"), 3])
    with pytest.raises(ValueError):
        bq.metric_median(None)


def test_summarize_metric_reports_distribution_not_cherry_pick():
    s = bq.summarize_metric([10, 30, 20])
    assert s["n"] == 3 and s["median"] == 20
    assert s["min"] == 10 and s["max"] == 30
    assert s["distinct_values"] == 3
    s2 = bq.summarize_metric([20, 20, 20])
    assert s2["distinct_values"] == 1 and s2["median"] == 20
    with pytest.raises(ValueError):
        bq.summarize_metric([])
    with pytest.raises(ValueError):
        bq.summarize_metric([1, None])


def test_compare_arm_medians_insufficient_runs():
    # n < min_runs（默认 3）⇒ 不足以判优劣（不挑单次充数）
    c = bq.compare_arm_medians(arm_a=[10], arm_b=[20, 25, 22])
    assert c["verdict"] == bq.AB_VERDICT_INSUFFICIENT
    assert c["delta_median"] is None
    assert c["distributions_separated"] is None
    c2 = bq.compare_arm_medians(arm_a=[10, 11], arm_b=[20, 21],
                                min_runs=2)
    assert c2["verdict"] == bq.AB_VERDICT_A_BETTER
    with pytest.raises(ValueError):
        bq.compare_arm_medians(arm_a=[1, 2, 3], arm_b=[1, 2, 3],
                               min_runs=1)
    with pytest.raises(ValueError):
        bq.compare_arm_medians(arm_a=[1, 2, 3], arm_b=[1, 2, 3],
                               min_runs=True)


def test_compare_arm_medians_direction_semantics():
    # lower_is_better=True（违规计数语义）：median 小=好
    c = bq.compare_arm_medians(arm_a=[10, 12, 11],
                               arm_b=[20, 25, 22])
    assert c["verdict"] == bq.AB_VERDICT_A_BETTER
    assert c["median_a"] == 11 and c["median_b"] == 22
    # delta 语义=median_a - median_b（a 更小 ⇒ 负）
    assert c["delta_median"] == -11.0
    assert c["relative_delta"] == round(-11.0 / 22, 6)
    assert c["distributions_separated"] is True
    # 方向反转：同数据 higher_is_better ⇒ b 好
    c2 = bq.compare_arm_medians(arm_a=[10, 12, 11], arm_b=[20, 25, 22],
                                lower_is_better=False)
    assert c2["verdict"] == bq.AB_VERDICT_B_BETTER
    # 分布交叠 ⇒ separated=False（如实，不升格）
    c3 = bq.compare_arm_medians(arm_a=[10, 20, 15],
                                arm_b=[12, 25, 18])
    assert c3["verdict"] == bq.AB_VERDICT_A_BETTER
    assert c3["distributions_separated"] is False


def test_compare_arm_medians_equal_and_zero_baseline():
    c = bq.compare_arm_medians(arm_a=[5, 6, 5], arm_b=[5, 5, 6])
    assert c["verdict"] == bq.AB_VERDICT_EQUAL
    assert c["delta_median"] == 0.0
    # median 相等（0 vs 0）即便分布不同 ⇒ equal（中位数口径）
    c1 = bq.compare_arm_medians(arm_a=[0, 1, 0], arm_b=[0, 0, 0])
    assert c1["verdict"] == bq.AB_VERDICT_EQUAL
    # b median=0：相对比无定义（None），不抛异常、不虚构
    c2 = bq.compare_arm_medians(arm_a=[1, 1, 1], arm_b=[0, 0, 0])
    assert c2["verdict"] == bq.AB_VERDICT_B_BETTER
    assert c2["relative_delta"] is None


def test_build_ab_report_shape_and_fail_closed():
    r = bq.build_ab_report(
        arm_labels={"a": "challenger", "b": "baseline"},
        metrics=[
            {"metric_id": "new_error_count", "lower_is_better": True,
             "values_a": [10, 12, 11], "values_b": [20, 25, 22]},
            {"metric_id": "unconnected", "lower_is_better": True,
             "values_a": [1, 2, 2], "values_b": [1, 2, 2]}],
        arm_runs={"a": 3, "b": 3})
    assert r["artifact_kind"] == "ab_statistical_report"
    assert r["overall_verdict"] == bq.AB_VERDICT_A_BETTER
    assert r["metric_count"] == 2
    assert {c["metric_id"] for c in r["comparisons"]} == {
        "new_error_count", "unconnected"}
    # arm_runs 与 values 长度不符 ⇒ fail-closed
    with pytest.raises(ValueError):
        bq.build_ab_report(
            arm_labels={"a": "x", "b": "y"},
            metrics=[{"metric_id": "m", "values_a": [1, 2],
                      "values_b": [1, 2, 3]}],
            arm_runs={"a": 3, "b": 3})
    with pytest.raises(ValueError):
        bq.build_ab_report(arm_labels={"a": "x"}, metrics=[],
                           arm_runs={"a": 1, "b": 1})
    with pytest.raises(ValueError):
        bq.build_ab_report(arm_labels={"a": "x", "b": "y"},
                           metrics=[{"metric_id": None}],
                           arm_runs={"a": 1, "b": 1})


def test_build_ab_report_verdict_aggregation():
    def mk(va, vb):
        return {"metric_id": "m", "values_a": va, "values_b": vb}

    # 任一 insufficient ⇒ overall insufficient（b 臂 n=2 < min_runs=3）
    r = bq.build_ab_report(
        arm_labels={"a": "a", "b": "b"},
        metrics=[mk([1, 2, 3], [4, 5]), mk([3, 2, 1], [5, 4])],
        arm_runs={"a": 3, "b": 2})
    assert r["overall_verdict"] == bq.AB_VERDICT_INSUFFICIENT
    # 全 equal ⇒ equal
    r2 = bq.build_ab_report(
        arm_labels={"a": "a", "b": "b"},
        metrics=[mk([1, 2, 3], [1, 2, 3]), mk([4, 5, 6], [5, 5, 5])],
        arm_runs={"a": 3, "b": 3})
    assert r2["overall_verdict"] == bq.AB_VERDICT_EQUAL
    # 方向冲突（一好一坏）⇒ inconclusive 如实
    r3 = bq.build_ab_report(
        arm_labels={"a": "a", "b": "b"},
        metrics=[mk([1, 1, 1], [2, 2, 2]), mk([2, 2, 2], [1, 1, 1])],
        arm_runs={"a": 3, "b": 3})
    assert r3["overall_verdict"] == bq.AB_VERDICT_INCONCLUSIVE
    # equal + b 好 ⇒ b_better
    r4 = bq.build_ab_report(
        arm_labels={"a": "a", "b": "b"},
        metrics=[mk([1, 1, 1], [1, 1, 1]), mk([2, 2, 2], [1, 1, 1])],
        arm_runs={"a": 3, "b": 3})
    assert r4["overall_verdict"] == bq.AB_VERDICT_B_BETTER
    # 空度量 ⇒ insufficient（不虚评）
    r5 = bq.build_ab_report(arm_labels={"a": "a", "b": "b"},
                            metrics=[], arm_runs={"a": 3, "b": 3})
    assert r5["overall_verdict"] == bq.AB_VERDICT_INSUFFICIENT


# ---------------------------------------------------------------------------
# 12) DSN 逐 net 显式规则注入（D20(d) 证伪实验仪器）
# ---------------------------------------------------------------------------

_DSN_TMPL = """(pcb "x.dsn"
  (resolution um 10)
  (structure
    (layer Top (type signal))
  )
  (network
    (net GND
      (pins U1-1 U2-2)
    )
    (net "V+ 3V3"
      (pins U1-3
        U2-4)
    )
    (net KEEP
      (rule
        (width 9)
      )
      (pins U3-1)
    )
  )
)
"""


def test_inject_net_width_rules_basic_and_quoted_names():
    r = bq.inject_net_width_rules(_DSN_TMPL,
                                  {"GND": 250, "V+ 3V3": 304.8})
    assert r["injected_nets"] == {"GND": 250, "V+ 3V3": 304.8}
    assert r["skipped_existing"] == []
    assert r["missing_nets"] == []
    assert "(width 250)" in r["dsn_text"]
    assert "(width 304.8)" in r["dsn_text"]
    # 注入位置在 net 块内、pins 之后、块收括号之前
    gnd_block = r["dsn_text"].split("(net GND")[1].split("(net")[0]
    assert gnd_block.strip().endswith(")")
    assert "(pins U1-1 U2-2)" in gnd_block
    assert gnd_block.index("(pins") < gnd_block.index("(rule")
    # 注入后仍是可解析 s-expr（往返 parse 不炸）
    from pcbflow import sexpr_min
    parsed = sexpr_min.parse(r["dsn_text"])
    assert any(isinstance(n, list) and n and n[0] == "pcb"
               for n in parsed)


def test_inject_net_width_rules_existing_rule_skipped_missing():
    r = bq.inject_net_width_rules(_DSN_TMPL,
                                  {"KEEP": 500, "NOPE": 123})
    assert r["injected_nets"] == {}
    assert r["skipped_existing"] == ["KEEP"]
    assert r["missing_nets"] == ["NOPE"]
    # KEEP 块保持原宽度 9（不重复注入、不改写既有规则）
    keep_block = r["dsn_text"].split("(net KEEP")[1].split("(net")[0]
    assert "(width 9)" in keep_block
    assert "(width 500)" not in keep_block


def test_inject_net_width_rules_fail_closed():
    with pytest.raises(ValueError):
        bq.inject_net_width_rules("", {"GND": 250})
    with pytest.raises(ValueError):
        bq.inject_net_width_rules(_DSN_TMPL, {})
    with pytest.raises(ValueError):
        bq.inject_net_width_rules(_DSN_TMPL, {"GND": -1})
    with pytest.raises(ValueError):
        bq.inject_net_width_rules(_DSN_TMPL, {"GND": 0})
    with pytest.raises(ValueError):
        bq.inject_net_width_rules(_DSN_TMPL, {"": 250})
    with pytest.raises(ValueError):
        bq.inject_net_width_rules(_DSN_TMPL, {"GND": float("nan")})


