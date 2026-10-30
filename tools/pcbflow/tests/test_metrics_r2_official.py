"""metrics-r2 正式指标批测试（E-3 负向断言 + 主件不变量钉）。

覆盖：
- E-3 负向断言：rows-r2/align/lc_demand_fit 37 件内嵌 convention 字符串
  零变化（==canonical 去句末「。」的合规变体，冻结件零重生成）；
  align 全部 74 件 sha256 与 align manifest inventory 逐件相等；
  库常量 canonical 形态（LC 含句末「。」、escape 常量零改动）。
- metrics-r2 主件不变量：canonical 形态、preregistered 声明、r2 冻结件
  sha 锚、P-RC-6 自检 all_match、跨进程 replay byte_exact=true、
  装配期望、M4/not_available 台账形态、关键指标数值钉。

只读（零写入/零网络/零 wall-clock/零子进程）。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import hashing
from pcbflow import observation_align_ext as oae

ROOT = os.path.join(os.path.dirname(__file__), "..")
R2 = os.path.join(ROOT, "out", "v3-obs", "rows-r2")
LC_DIR = os.path.join(R2, "align", "lc-demand-fit")
ESC_DIR = os.path.join(R2, "align", "escape-agreement")
MR2 = os.path.join(ROOT, "out", "v3-obs", "metrics-r2")

# E-3 合规变体：冻结 sidecar 内嵌 LC convention（=canonical 去句末「。」）
E3_SIDECAR_VARIANT = oae.CONVENTION_VERBATIM_LAYER_CAPACITY[:-1]

# 官方指标数值钉（resource-calibration-metrics-r2.json；同输入重算逐位同值）


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def align_manifest():
    return _load(os.path.join(R2, "align", "manifest.json"))


@pytest.fixture(scope="module")
def metrics_r2():
    return _load(os.path.join(MR2, "resource-calibration-metrics-r2.json"))


# ---- E-3：库常量 canonical 形态 ------------------------------------------------


def test_e3_lc_constant_canonical():
    assert oae.CONVENTION_VERBATIM_LAYER_CAPACITY.endswith("一致 mm²。")
    assert len(oae.CONVENTION_VERBATIM_LAYER_CAPACITY) == 129


def test_e3_pad_escape_constant_untouched():
    assert oae.CONVENTION_VERBATIM_PAD_ESCAPE.endswith("附属先例）")


def test_e3_lc_sidecars_compliance_variant_zero_regeneration(align_manifest):
    """rows-r2/align/lc_demand_fit 各件字符串零变化（合规变体，不重生成）。"""
    for pid in sorted(os.listdir(LC_DIR)):
        with open(os.path.join(LC_DIR, pid), encoding="utf-8") as f:
            sc = json.load(f)
        conv = ((sc.get("result") or {}).get("convention_verbatim")
                if sc["status"] == "ok" else sc.get("convention_verbatim"))
        assert conv == E3_SIDECAR_VARIANT, pid


def test_e3_align_sidecars_hash_match_manifest(align_manifest):
    """align 全部 74 件 sha256 与 manifest inventory 逐件相等（零触碰）。"""
    for kind_dir in ("lc_demand_fit", "pad_escape_agreement"):
        for pid, inv in align_manifest["inventory"][kind_dir].items():
            fp = os.path.join(ROOT, inv["path"])
            assert hashing.sha256_file(fp) == inv["sha256"], (kind_dir, pid)


# ---- metrics-r2 主件不变量 ------------------------------------------------------


def test_main_artifact_canonical_and_header(metrics_r2):
    path = os.path.join(MR2, "resource-calibration-metrics-r2.json")
    with open(path, "rb") as f:
        blob = f.read()
    assert blob == hashing.canonical_json_bytes(metrics_r2)
    assert metrics_r2["artifact_kind"] == "resource_calibration_metrics_r2"
    assert metrics_r2["prereg_id"] == "resource-calibration-r2"
    assert metrics_r2["result_level"] == "preregistered"
    assert metrics_r2["declared_date"] == "2026-09-13"
    assert metrics_r2["prereg"]["status"] == "frozen"
    assert metrics_r2["prereg"]["declared_date"] == "2026-09-13"


def test_main_artifact_prereg_anchor_matches_frozen_file(metrics_r2):
    frozen = os.path.join(
        ROOT, "out", "v3-obs-proposal",
        "PREREG-RESOURCE-CALIBRATION-R2-frozen.md")
    assert metrics_r2["prereg"]["sha256"] == hashing.sha256_file(frozen)
    assert metrics_r2["prereg"]["supersedes"]["sha256"] == \
        metrics_r2["inputs"]["anchors"]["prereg_frozen_r1"]["sha256"]


def test_selfcheck_all_match():
    sc = _load(os.path.join(MR2, "selfcheck-p-rc-6-r2.json"))
    assert sc["all_match"] is True
    assert sc["n_checks"] == len(sc["checks"]) >= 40


def test_replay_byte_exact_two_processes():
    rp = _load(os.path.join(MR2, "replay-check-r2.json"))
    assert rp["byte_exact"] is True
    for rec in rp["files"].values():
        assert rec["byte_exact"] is True
        assert rec["sha256_expected"] == rec["sha256_on_disk_before"]


def test_assembly_expectations(metrics_r2):
    a = metrics_r2["assembly"]
    assert a["invariants"]["rows_grand_total"] == 34901
    assert a["invariants"]["smoke_rows"] == 0
    pools = a["pools"]
    assert pools["train"]["rows_total"] == 15225
    assert pools["train"]["boards_total"] == 62
    assert pools["train"]["rows_by_source"] == {
        "r1_real_train": 5907, "r1_real_validation": 1255, "r2_train": 8063}
    assert pools["demo"]["rows_total"] == 12371
    assert pools["demo"]["boards_total"] == 17
    assert pools["holdout"]["rows_total"] == 7305
    assert pools["holdout"]["boards_total"] == 12


# ---- 官方指标数值钉（行级主口径 B-1 / LC A-1 / M5） -----------------------------


def test_aux_rails_train_row_primary(metrics_r2):
    mm = metrics_r2["pools"]["train"]["auxiliary"]["rails"]["metrics"]
    assert mm["m1_row_pool"] == {
        "p50": 0.0, "p90": 0.0, "p95": 0.07425438596491223}
    assert mm["m2_row_pool"]["p95"] == 0.0041353383458646404
    assert mm["m2b"] == {"n_underprediction": 7, "n_measurable": 130,
                         "rate": 0.05384615384615385}
    assert mm["m3_worst_board"] == {"board_id": "bm1",
                                    "board_median_abs_e": 0.0, "n_rows": 6}


def test_aux_rails_demo_not_enough_data_n2(metrics_r2):
    rails = metrics_r2["pools"]["demo"]["auxiliary"]["rails"]
    assert rails["n_measurable"] == 2
    assert rails["m4_status"] == "not_enough_data"
    assert "metrics" not in rails
    assert rails["ledger_counts"]["actual_zero"] == 27


def test_aux_all_zero_elsewhere(metrics_r2):
    for pool, short in (("train", "padload"), ("demo", "padload"),
                        ("holdout", "rails"), ("holdout", "padload")):
        mm = metrics_r2["pools"][pool]["auxiliary"][short]["metrics"]
        assert mm["m1_row_pool"]["p95"] == 0.0
        assert mm["m2_row_pool"]["p95"] == 0.0
        assert mm["m2b"]["rate"] == 0.0


def test_sixkind_all_not_available(metrics_r2):
    for pool in ("train", "demo", "holdout"):
        for kind in ("escape_slots", "corridor", "layer_capacity",
                     "bus_lane", "via_budget", "power_return_space"):
            sk = metrics_r2["pools"][pool]["sixkind"][kind]
            assert sk["m4_status"] == "not_available"
            assert sk["n_measurable"] == 0
            assert "metrics" not in sk


def test_lc_official_a1(metrics_r2):
    lc = metrics_r2["layer_capacity_official"]
    assert lc["n_ok"] == {"train": 27, "holdout": 5, "demo": 0, "total": 32}
    assert lc["n_fail_closed"] == {"train": 4, "holdout": 1, "total": 5}
    tr = lc["pools"]["train"]
    assert tr["m4_status"] == "ok" and tr["n_measurable"] == 27
    assert tr["metrics"]["m1_row_pool"]["p95"] == 0.5177501666544915
    assert tr["metrics"]["m2_row_pool"]["p95"] == 0.3603413569095238
    assert tr["metrics"]["m2b"] == {
        "n_underprediction": 25, "n_measurable": 27,
        "rate": 0.9259259259259259}
    assert tr["metrics"]["m1_board_pool"]["status"] == "not_enough_data"
    assert tr["metrics"]["m3_worst_board"] is None
    ho = lc["pools"]["holdout"]
    assert ho["m4_status"] == "ok" and ho["n_measurable"] == 5
    assert ho["metrics"]["m1_row_pool"]["p95"] == 0.29106683305606856
    assert ho["metrics"]["m2b"]["rate"] == 1.0
    dm = lc["pools"]["demo"]
    assert dm["m4_status"] == "not_available" and dm["n_measurable"] == 0
    assert len(lc["fail_closed"]) == 5
    assert all(r["m4_status"] == "not_available" and r["error_verbatim"]
               for r in lc["fail_closed"])


def test_m5_escape_descriptive_face(metrics_r2):
    
    m5 = metrics_r2["m5_escape_agreement"]
    assert m5["rc_binding"] == "none（M5 不参与 RC-1..6 任何判据；r2 §1 M5 行明文）"
    assert m5["n_ok"] == {"train": 28, "holdout": 5, "total": 33}
    assert m5["n_fail_closed"] == {"train": 3, "holdout": 1, "total": 4}
    pt = m5["pool_totals"]
    assert pt["train"]["m5_pooled_rate_agree_over_both"] == \
        0.8341269841269842
    assert pt["holdout"]["m5_pooled_rate_agree_over_both"] == \
        0.6515523788251061
    assert pt["all"]["m5_pooled_rate_agree_over_both"] == \
        0.7582815254709103
    assert pt["demo"]["m4_board_count_status"] == "not_available"
    assert pt["train"]["m4_board_count_status"] == "ok"
    assert pt["holdout"]["m4_board_count_status"] == "ok"
    for r in m5["fail_closed"]:
        assert r["m4_status"] == "not_available" and r["error_verbatim"]


def test_e3_negative_assertion_recorded(metrics_r2):
    ea = metrics_r2["reconciliation"]["e3_negative_assertion"]
    assert ea["lc_sidecar_convention_compliance_variant_all"] is True
    assert ea["align_sidecar_sha256_vs_manifest_all"] is True


def test_errata_register_anchored(metrics_r2):
    # P-RC-7 追加式：登记件锚定后可合法追加（E-4/E-5）。主件锚定值=
    # 追加前 sha（钉死）；盘上 md 头部必须记载追加链（含追加前 sha），
    # 使断言在后续合法追加下仍可复验延续性。
    reg_md = os.path.join(ROOT, "out", "v3-obs-proposal",
                          "ERRATA-REGISTER-R1-R2.md")
    anchored = metrics_r2["inputs"]["anchors"]["errata_register_json"]["sha256"]
    assert anchored == ("9e7c20b262d8ceba7b711593cab86771c7dc8dbb4bc2571"
                        "9bf3a5236753477fc")
    md_text = open(reg_md, encoding="utf-8").read()
    assert anchored in md_text
    assert "E-4" in md_text


def test_in_process_double_build_all_exact(metrics_r2):
    for rec in metrics_r2["determinism"]["in_process_double_build"]:
        assert rec["byte_exact"] is True


@pytest.mark.parametrize("rel,expect", [
    ("pcbflow/cli.py",
     "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8"),  # R-24 known_open retire (2026-09-25): 0a738047->3bfc9407 programmatic from baseline.json protected_files_sha256; out/repair-g1plus-r1/known-open-r17-registration.md appendix
    ("pcbflow/config.py",
     "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82"),  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); R-24 retire (2026-09-25): acdfac49->cbe90c4d via G1+ 7b4974d8, programmatic from baseline.json, registration appendix as above; align-r1 (2026-09-25): cbe90c4d->8ad12b3f O-1/D-3 None-input structured reject, programmatic on-disk sha, registration out/align-r1/anchor-hashes-post-align.json
    ("toolchain_lock.json",
     "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d"),
])
def test_protected_three_files_unchanged(rel, expect):
    assert hashing.sha256_file(os.path.join(ROOT, rel)) == expect


def test_rows_r2_frozen_anchors_unchanged():
    """rows-r2 冻结零触碰旁证：batch-summary/split-registry/align manifest
    sha256 与 metrics-r2 主件锚定值相等（主件生成时实测）。"""
    m = _load(os.path.join(MR2, "resource-calibration-metrics-r2.json"))
    anchors = m["inputs"]["anchors"]
    for key, rel in (
            ("rows_r2_batch_summary",
             "out/v3-obs/rows-r2/batch-summary.json"),
            ("split_registry_r2",
             "out/v3-obs/rows-r2/split-registry-r2.json"),
            ("align_manifest", "out/v3-obs/rows-r2/align/manifest.json"),
            ("rows_r1_batch_summary",
             "out/v3-obs/rows-r1/batch-summary.json")):
        assert anchors[key]["sha256"] == hashing.sha256_file(
            os.path.join(ROOT, rel)), key
