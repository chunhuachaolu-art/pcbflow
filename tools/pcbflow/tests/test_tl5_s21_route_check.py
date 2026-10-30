"""TL-5 S21 批测试：k9 demo 板 17 板 route/check 参考态验证（k9-route-check-batch-r1）。

覆盖（纯函数+盘上最终态 fail-closed 校验）：
- 一致性判定函数（正向全过/计数不符带差值证据/重放不符/log 键缺失 fail-closed）；
- baseline 完整性判定（staging 逐字节/前后 hash 分记/双 severity JSON 解析/
  D19(b) 类双运行 error 稳定性/坏 JSON fail-closed）；
- 批汇总结构（分布闭合/中位数/上游实况登记/anomalies/缺记录 fail-closed）；
- 盘上产物闭合（plan 17 板=r2 manifest、逐板两记录、staging 逐字节断言、
  批汇总与逐板记录一致、核心产物零主机路径、datasets/ 只读复验）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus, corpus_convert as cc, hashing

_S21_SPEC = importlib.util.spec_from_file_location(
    "s21_route_check",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "s21_route_check.py"))
s21 = importlib.util.module_from_spec(_S21_SPEC)
_S21_SPEC.loader.exec_module(s21)

BATCH_DIR = os.path.join("out", "v3-tl5", "k9-route-check-batch-r1")
TL5 = os.path.join("out", "v3-tl5")
R2 = os.path.join(TL5, "dataset-manifest-kicad-demos-r2.json")
KICAD_DEMOS = os.path.join("datasets", "kicad-demos-r1")
EXPECT_RAW_HASH = "e8db198a114cc6e93eaa17b2ffb2c14d94c6016774e1f8112e6e196257a12c35"

SRC_SHA = "a" * 64
SRC_REL = "datasets/kicad-demos-r1/raw/demo/board.kicad_pcb"

#: 最小 KiCad 8.99–10.99（20241229，top_level net 声明）合成 routed 板
SYNTH_K9 = """(kicad_pcb (version 20241229) (generator kicad) (generator_version "9.0")

  (general (thickness 1.6) (footprints 1) (nets 3))

  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
    (4 "F.SilkS" user)
  )

  (setup (pad_to_mask_clearance 0))

  (net 0 "")
  (net 1 "GND")
  (net 2 "+5V")

  (footprint "R1" (layer "F.Cu") (at 0 0)
    (property "Reference" "R1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at -1 0) (size 1 1) (layers "F.Cu") (net 1 "GND"))
    (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu") (net 2 "+5V"))
  )

  (segment (start 0 0) (end 1 0) (width 0.2) (layer "F.Cu") (net 1))
  (via (at 2 2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1))
  (zone (net 2) (layers "F.Cu"))
)
"""


def _synth_fixture():
    model = cc.parse_kicad9_board(SYNTH_K9)
    ref = s21.reference_counts_from_model(model)
    norm_text = cc.normalized_k9_board_text(
        model, source_path=SRC_REL, source_sha256=SRC_SHA)
    norm = s21.parse_normalized_counts(norm_text)
    norm_sha = hashing.sha256_text(norm_text)
    log = {
        "inputs": [{"path": SRC_REL,
                    "role": "source_pcb (as_shipped, version 20241229)",
                    "sha256": SRC_SHA}],
        "outputs": [{"path": "profiles/kicaddemo-x/inputs/board.kicad_pcb",
                     "role": "board", "sha256": norm_sha}],
        "dropped": {
            "routed_geometry": "segments=1 vias=1 arcs=0 不进规范化板",
            "zones": "zones=1 不进规范化板（原样留存于 datasets）"},
    }
    return ref, norm, norm_text, norm_sha, log


def _consistency_args(ref, norm, norm_text, norm_sha, log, disk_text=None,
                      **over):
    """norm_text=重放文本；disk_text=盘上规范化板文本（默认与重放一致）。"""
    disk_text = norm_text if disk_text is None else disk_text
    args = dict(
        ref_counts=ref, norm_counts=norm,
        replay_text=norm_text, normalized_disk_bytes=disk_text.encode("utf-8"),
        normalized_disk_sha=norm_sha,
        log_obj=log, log_disk_sha="b" * 64,
        log_manifest_sha="b" * 64, source_rel=SRC_REL, source_sha=SRC_SHA,
        outputs_disk_shas={o["path"]: o["sha256"] for o in log["outputs"]},
        manifest_norm_sha=norm_sha)
    args.update(over)
    return args


# ---------------- 一致性判定函数 ----------------

def test_consistency_pass_reference_reproduced():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    rec = s21.evaluate_consistency(**_consistency_args(ref, norm, norm_text,
                                                       norm_sha, log))
    assert rec["result"] == "pass"
    assert rec["fail_classes"] == []
    ids = {c["id"] for c in rec["checks"]}
    assert {"net_multiset_matches_reference",
            "footprint_ref_multiset_matches_reference",
            "pad_account_matches_reference",
            "pad_net_multiset_matches_reference",
            "routed_geometry_counts_match_conversion_log",
            "normalized_board_replay_matches_disk",
            "conversion_log_outputs_disk_binding",
            "conversion_log_manifest_binding",
            "log_input_binds_dataset_source",
            "normalized_board_manifest_binding"} <= ids


def test_reference_and_normalized_counts_roundtrip():
    ref, norm, _, _, _ = _synth_fixture()
    assert norm["net_names"] == ref["net_names"]
    assert norm["footprint_refs"] == ref["footprint_refs"]
    assert norm["pad_count_by_ref"] == ref["pad_count_by_ref"]
    assert norm["pad_net_names"] == ref["pad_net_names"]
    assert norm["pads_without_net"] == ref["pads_without_net"]
    assert ref["geometry"] == {"segments": 1, "vias": 1, "arcs": 0,
                               "zones": 1}


def test_consistency_count_mismatch_fail_with_delta():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    bad = dict(ref, pad_total=ref["pad_total"] + 1,
               pad_count_by_ref=dict(ref["pad_count_by_ref"], R1=3))
    rec = s21.evaluate_consistency(**_consistency_args(bad, norm, norm_text,
                                                       norm_sha, log))
    assert rec["result"] == "fail"
    assert "pad_account_matches_reference" in rec["fail_classes"]
    ev = next(c["evidence"] for c in rec["checks"]
              if c["id"] == "pad_account_matches_reference")
    assert "R1" in ev and "3" in ev  # 差值证据（逐 ref 2 vs 3）


def test_consistency_replay_mismatch_fail():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    rec = s21.evaluate_consistency(**_consistency_args(
        ref, norm, norm_text.replace("+5V", "VDD"), norm_sha, log,
        disk_text=norm_text))
    assert rec["result"] == "fail"
    assert "normalized_board_replay_matches_disk" in rec["fail_classes"]


def test_consistency_net_multiset_diff_fail():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    bad = dict(ref, net_names=["", "+5V"], net_count=2)
    rec = s21.evaluate_consistency(**_consistency_args(bad, norm, norm_text,
                                                       norm_sha, log))
    assert "net_multiset_matches_reference" in rec["fail_classes"]
    ev = next(c["evidence"] for c in rec["checks"]
              if c["id"] == "net_multiset_matches_reference")
    assert "GND" in ev  # 缺失网名在差值证据中


def test_consistency_fail_closed_malformed_log():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    # dropped 计数文本缺失 → 对应检查 fail（不崩溃）
    bad_log = {**log, "dropped": {"zones": "zones=1 不进规范化板"}}
    rec = s21.evaluate_consistency(**_consistency_args(ref, norm, norm_text,
                                                       norm_sha, bad_log))
    assert "routed_geometry_counts_match_conversion_log" in rec["fail_classes"]
    # outputs 空 → fail-closed
    empty_log = {**log, "outputs": []}
    rec2 = s21.evaluate_consistency(**_consistency_args(
        ref, norm, norm_text, norm_sha, empty_log, outputs_disk_shas={}))
    assert "conversion_log_outputs_disk_binding" in rec2["fail_classes"]
    # inputs 缺失 → log_input 检查 fail（不崩溃）
    no_input = {k: v for k, v in log.items() if k != "inputs"}
    rec3 = s21.evaluate_consistency(**_consistency_args(ref, norm, norm_text,
                                                        norm_sha, no_input))
    assert "log_input_binds_dataset_source" in rec3["fail_classes"]


def test_consistency_geometry_count_mismatch_fail():
    ref, norm, norm_text, norm_sha, log = _synth_fixture()
    bad_log = {**log, "dropped": {**log["dropped"],
                                  "routed_geometry":
                                  "segments=2 vias=1 arcs=0 不进规范化板"}}
    rec = s21.evaluate_consistency(**_consistency_args(ref, norm, norm_text,
                                                       norm_sha, bad_log))
    assert "routed_geometry_counts_match_conversion_log" in rec["fail_classes"]


# ---------------- baseline 完整性判定 ----------------

def _drc_json(errors, warnings=0, unconnected=0):
    viols = ([{"severity": "error", "type": "clearance"}] * errors
             + [{"severity": "warning", "type": "silk_over_copper"}]
             * warnings)
    return json.dumps({"kicad_version": "10.0.5",
                       "source": "reference.kicad_pcb",
                       "included_severities": ["error", "warning",
                                               "exclusion"],
                       "violations": viols,
                       "unconnected_items": [], "schematic_parity": []})


def _baseline_args(**over):
    args = dict(source_sha_before="d" * 64, source_sha_after="d" * 64,
                staging_sha="d" * 64,
                drc_error_text=_drc_json(2),
                drc_all_text=_drc_json(2, warnings=1))
    args.update(over)
    return args


def test_baseline_integrity_pass():
    ev = s21.evaluate_baseline_integrity(**_baseline_args())
    assert ev["integrity_result"] == "pass"
    assert ev["fail_classes"] == []
    assert ev["dual_run_stable"] is True
    assert ev["error_counts"] == {"severity_error": 2, "severity_all": 2}


def test_baseline_integrity_dual_run_unstable_d19b():
    ev = s21.evaluate_baseline_integrity(**_baseline_args(
        drc_error_text=_drc_json(3), drc_all_text=_drc_json(2, warnings=1)))
    assert ev["dual_run_stable"] is False
    assert ev["integrity_result"] == "fail"
    assert "dual_run_error_count_stable" in ev["fail_classes"]


def test_baseline_integrity_malformed_drc_json_fail_closed():
    ev = s21.evaluate_baseline_integrity(**_baseline_args(
        drc_error_text="not a drc json"))
    assert ev["integrity_result"] == "fail"
    assert "drc_json_wellformed" in ev["fail_classes"]
    assert ev["parsed"]["severity_error"]["ok"] is False


def test_baseline_integrity_missing_keys_fail_closed():
    partial = json.dumps({"violations": []})
    ev = s21.evaluate_baseline_integrity(**_baseline_args(
        drc_all_text=partial))
    assert "drc_json_wellformed" in ev["fail_classes"]


def test_baseline_integrity_staging_and_pre_post_hash():
    ev = s21.evaluate_baseline_integrity(**_baseline_args(
        staging_sha="e" * 64))
    assert "staging_copy_byte_identical" in ev["fail_classes"]
    ev2 = s21.evaluate_baseline_integrity(**_baseline_args(
        source_sha_after="f" * 64))
    assert "reference_unchanged_pre_post_drc" in ev2["fail_classes"]
    assert "staging_copy_byte_identical" in ev2["fail_classes"]


# ---------------- 批汇总结构 ----------------

def _plan_entry(pid, role="train", token="20241229"):
    return {"board_id": f"demo/{pid}", "profile_id": pid, "split_role": role,
            "version_token": token, "net_declaration_source": "top_level"}


def _row(pid, *, consistency="pass", unconn=0, err_b=0, err_f=0, stable=True):
    base = {
        "integrity_result": "pass" if stable else "fail",
        "connectivity": {"unconnected_items": unconn,
                         "connectivity_type_violations": {},
                         "connectivity_type_violation_total": 0},
        "dual_run_error_stability": {"stable": stable, "error_batch": err_b,
                                     "error_final": err_f},
        "drc_baseline": {"dual_severity": {
            "severity_all_final": {"total": err_f + unconn,
                                   "violations_by_severity": {
                                       "error": err_f, "warning": 1}}}},
        "checks": [],
        "fail_classes": [] if stable else ["dual_run_error_count_stable"],
    }
    ver = {
        "result": consistency, "checks": [{"id": "x", "pass":
                                           consistency == "pass",
                                           "evidence": "e"}],
        "fail_classes": [] if consistency == "pass" else ["x"],
    }
    return {"board_id": f"demo/{pid}", "profile_id": pid,
            "split_role": "train", "version_token": "20241229",
            "baseline": base, "verify": ver}


def _plan():
    return {"boards": [_plan_entry("p1"), _plan_entry("p2"),
                       _plan_entry("p3", role="holdout")]}


def test_batch_summary_structure():
    rows = [_row("p1"), _row("p2", unconn=2, err_b=5, err_f=5),
            _row("p3", consistency="fail", err_b=1, err_f=2, stable=False)]
    s = s21.build_batch_summary(
        plan=_plan(), board_rows=rows,
        refs={"r2_manifest": {"path": "x", "sha256": "a" * 64},
              "toolchain_lock_sha256": "b" * 64, "module_sha256": {},
              "script_sha256": "c" * 64})
    assert s["artifact_kind"] == "s21_k9_route_check_batch_summary"
    assert s["denominator"]["boards"] == 3
    assert s["denominator"]["split_roles"] == {"holdout": 1, "train": 2}
    dist = s["reference_check"]["consistency_distribution"]
    assert dist == {"fail": 1, "pass": 2}
    assert s["reference_check"]["all_consistency_pass"] is False
    assert len(s["reference_check"]["boards"]) == 3
    # 中位数（error-run 计数 [0, 5, 1] → 1）
    assert s["drc_error_stats"]["median"] == 1
    assert s["drc_error_stats"]["zero_error_boards"] == 1
    # 上游实况 fail-closed 登记
    assert s["upstream_reference_state"][
        "connectivity_violation_board_count"] == 1
    assert s["upstream_reference_state"]["connectivity_violation_boards"][
        0]["profile_id"] == "p2"
    # D19(b) 类双运行不稳定登记
    assert len(s["upstream_reference_state"]
               ["dual_severity_unstable_boards"]) == 1
    assert s["upstream_reference_state"]["dual_severity_unstable_boards"][0][
        "profile_id"] == "p3"
    # anomalies 带失败检查与证据
    assert s["reference_check"]["anomalies"][0]["profile_id"] == "p3"
    assert s["reference_check"]["anomalies"][0]["failed_checks"] == ["x"]


def test_batch_summary_fail_closed():
    with pytest.raises(ValueError):
        s21.build_batch_summary(plan={"boards": []}, board_rows=[], refs={})
    rows = [_row("p1"), _row("p2")]
    with pytest.raises(ValueError):  # 缺 p3 记录
        s21.build_batch_summary(plan=_plan(), board_rows=rows, refs={})
    dup = [_row("p1"), _row("p1")]
    with pytest.raises(ValueError):  # profile_id 重复
        s21.build_batch_summary(plan={"boards": [{"profile_id": "p1"}]},
                                board_rows=dup, refs={})
    with pytest.raises(ValueError):  # 计划外记录
        s21.build_batch_summary(plan=_plan(),
                                board_rows=rows + [_row("p9")], refs={})
    with pytest.raises(ValueError):  # verify 记录缺 result 键
        bad = _row("p1")
        bad["verify"].pop("result")
        s21.build_batch_summary(plan=_plan(), board_rows=[bad], refs={})


# ---------------- 盘上最终态闭合（fail-closed 校验） ----------------

def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _plan_on_disk():
    return _load(os.path.join(BATCH_DIR, "plan.json"))


@pytest.mark.skipif(not os.path.isdir(BATCH_DIR), reason="batch 未生成")
def test_batch_plan_on_disk_matches_r2():
    plan = _plan_on_disk()
    r2 = _load(R2)
    assert plan["artifact_kind"] == "s21_batch_plan"
    assert plan["counts"]["boards"] == 17
    assert [b["board_id"] for b in plan["boards"]] == r2["board_ids"]
    assert plan["r2_manifest"]["sha256"] == hashing.sha256_file(R2)
    assert plan["counts"]["split_roles"] == {"holdout": 3, "train": 14}
    # 计划源 hash 与盘上字节一致（byte 口径）
    for b in plan["boards"]:
        assert hashing.sha256_file(b["source_rel"]) == \
            b["source_sha256_before_drc"]


@pytest.mark.skipif(not os.path.isdir(BATCH_DIR), reason="batch 未生成")
def test_batch_records_on_disk_closed():
    plan = _plan_on_disk()
    for b in plan["boards"]:
        base = _load(os.path.join(BATCH_DIR, "boards", b["profile_id"],
                                  "drc-baseline.json"))
        ver = _load(os.path.join(BATCH_DIR, "boards", b["profile_id"],
                                 "verify-record.json"))
        assert base["artifact_kind"] == "s21_drc_baseline"
        assert base["board_id"] == b["board_id"]
        # staging 逐字节断言（独立重算 hash）
        assert hashing.sha256_file(base["staging"]["path"]) == \
            base["staging"]["sha256"] == base["reference_state"][
                "sha256_after_drc"]
        assert base["staging"]["byte_identical_to_reference"] is True
        assert base["reference_state"]["unchanged"] is True
        assert base["drc_invocation"]["refill_mode"] == s21.REFILL_MODE
        assert base["drc_invocation"]["severity"] == {
            "batch": "severity-error", "final": "severity-all"}
        # 双 severity JSON：在场=可解析且含 unconnected_items；不在场=
        # drc_unavailable 如实登记（kicad-cli 加载失败板，fail-closed）
        present = base["drc_artifacts_present"]
        assert set(present) == {"severity_error", "severity_all"}
        if present["severity_all"]:
            drc_all = _load(os.path.join(BATCH_DIR, "staging",
                                         b["profile_id"], "drc-all.json"))
            assert "violations" in drc_all \
                and "unconnected_items" in drc_all
        else:
            assert "drc_json_wellformed" in base["fail_classes"]
            assert base["dual_run_error_stability"]["error_batch"] is None
        # 一致性记录：verdict 合法且重放绑定（canonical 对账+raw 字节绑定）
        assert ver["artifact_kind"] == "s21_conversion_consistency_record"
        assert ver["result"] in ("pass", "fail")
        assert ver["replay"]["replay_canonical_sha256"] == \
            ver["replay"]["disk_canonical_sha256"]
        assert ver["replay"]["disk_sha256_raw"] == b["normalized_sha256"]
        assert ver["replay"]["disk_newline_convention"] in ("crlf", "lf")


@pytest.mark.skipif(not os.path.isdir(BATCH_DIR), reason="batch 未生成")
def test_batch_summary_on_disk_consistent():
    plan = _plan_on_disk()
    summary = _load(os.path.join(BATCH_DIR, "batch-summary.json"))
    assert summary["batch_id"] == "k9-route-check-batch-r1"
    assert summary["denominator"]["boards"] == 17
    dist = summary["reference_check"]["consistency_distribution"]
    assert sum(dist.values()) == 17
    table = {r["profile_id"]: r for r in summary["reference_check"]["boards"]}
    for b in plan["boards"]:
        base = _load(os.path.join(BATCH_DIR, "boards", b["profile_id"],
                                  "drc-baseline.json"))
        ver = _load(os.path.join(BATCH_DIR, "boards", b["profile_id"],
                                 "verify-record.json"))
        row = table[b["profile_id"]]
        assert row["consistency"] == ver["result"]
        assert row["unconnected_items"] == base["connectivity"][
            "unconnected_items"]
        assert row["error_count_batch_run"] == \
            base["dual_run_error_stability"]["error_batch"]
        assert row["version_token"] == b["version_token"]
    assert summary["provenance"]["r2_manifest"]["sha256"] == \
        hashing.sha256_file(R2)
    assert summary["provenance"]["toolchain_lock"]["sha256"] == \
        hashing.sha256_file("toolchain_lock.json")


@pytest.mark.skipif(not os.path.isdir(BATCH_DIR), reason="batch 未生成")
def test_core_artifacts_no_host_paths():
    """核心产物（plan/逐板两记录/批汇总）零主机路径（生成器纪律）。"""
    host_re = re.compile(r"[A-Za-z]:[\\/]|\\\\")
    for name in ("plan.json", "batch-summary.json"):
        text = open(os.path.join(BATCH_DIR, name), encoding="utf-8").read()
        assert not host_re.search(text), name
    plan = _plan_on_disk()
    for b in plan["boards"]:
        for fname in ("drc-baseline.json", "verify-record.json"):
            p = os.path.join(BATCH_DIR, "boards", b["profile_id"], fname)
            text = open(p, encoding="utf-8").read()
            assert not host_re.search(text), p


@pytest.mark.skipif(not os.path.isdir(KICAD_DEMOS), reason="dataset 缺失")
def test_datasets_kicad_demos_readonly_unchanged():
    """datasets/ 只读收工复验：raw_hash 与 r2 manifest 记录全等。"""
    files = []
    for root, _dirs, fnames in os.walk(KICAD_DEMOS):
        for fn in sorted(fnames):
            p = os.path.join(root, fn)
            files.append({"path": p.replace("\\", "/"), "sha256":
                          hashing.sha256_file(p)})
    assert len(files) == 408
    assert corpus.aggregate_raw_hash(files) == EXPECT_RAW_HASH
