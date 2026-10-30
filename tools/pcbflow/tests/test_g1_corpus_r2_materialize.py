"""G1 corpus-r2 37 板 profile 物化回归测试（G 线 r2 包 G1）。

两层：
  A. 单元级（自足小夹具，不依赖批产物）——路由分派/版本门互斥 fail-closed/
     解析失败 fail-closed/小板全链转换+schema/双源回读计数/铜层按档双口径；
  B. 批产物级（读 out/v3-gline-r2/ 台账与 profiles/corpusr2-*/ 盘面，
     中间态缺产物 pytest.skip，完工后全过）——37 板计划路由计数/台账
     converted+skipped 全覆盖/七件+graph+route-check 在盘与 schema/
     H1–H6 治理携带/声明件形态（U-R2-7）/verify 全 pass/既有 profile
     前缀计数零变化。

编排脚本经 sys.path 导入（out/v3-gline-r2/g1_convert.py；模块级 REPO
定位 parents[2] 与该位置自洽）。datasets/ 只读。
"""

from __future__ import annotations

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "out", "v3-gline-r2"))

import g1_convert  # noqa: E402
from pcbflow import corpus_convert as cc  # noqa: E402
from pcbflow import corpus_convert_legacy as ccl  # noqa: E402
from pcbflow import manifest as manifest_mod  # noqa: E402

PLAN = os.path.join(REPO, "out", "v3-gline-r2", "g1-plan.json")
LEDGER = os.path.join(REPO, "out", "v3-gline-r2",
                      "g1-conversion-ledger.json")
VERIFY = os.path.join(REPO, "out", "v3-gline-r2", "g1-verify-report.json")

#: 既有 profiles/ 前缀计数基线（r1 零触碰断言；corpusr2-* 为 G1 新增）
EXISTING_PREFIX_COUNTS = {"pcbench-": 35, "pcbbm-": 2, "kicaddemo-": 17,
                          "smoke-": 2}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# A1. 路由分派与版本门（fail-closed）
# ---------------------------------------------------------------------------

def test_route_dispatch_covers_all_dataset_buckets():
    assert g1_convert.route_of("20210424") == "k9"
    assert g1_convert.route_of("20211014") == "k9"
    assert g1_convert.route_of("20221018") == "k9"
    assert g1_convert.route_of("20241030") == "k9"
    assert g1_convert.route_of("20241229") == "k9"
    assert g1_convert.route_of("20260206") == "k9"
    assert g1_convert.route_of("20260624") == "k9"
    assert g1_convert.route_of("20171130") == "k5"
    assert g1_convert.route_of("20171114") == "legacy"
    assert g1_convert.route_of("4") == "legacy"
    assert g1_convert.route_of("20230408") is None  # 未知档 → 拒
    assert g1_convert.route_of("1") is None


def test_version_gates_mutually_exclusive_reject():
    # k9 门拒 k5/legacy token（跨门不越）
    with pytest.raises(ValueError):
        cc.parse_kicad9_board("(kicad_pcb (version 20171130))")
    with pytest.raises(ValueError):
        cc.parse_kicad9_board("(kicad_pcb (version 4))")
    # k5 门拒 legacy/k9 token
    with pytest.raises(ValueError):
        cc.parse_kicad5_board("(kicad_pcb (version 20171114))")
    with pytest.raises(ValueError):
        cc.parse_kicad5_board("(kicad_pcb (version 20221018))")
    # legacy 门拒 k5/k9 token
    with pytest.raises(ValueError):
        ccl.parse_legacy_board("(kicad_pcb (version 20171130))")
    with pytest.raises(ValueError):
        ccl.parse_legacy_board("(kicad_pcb (version 20241229))")


def test_malformed_board_fails_closed():
    truncated = ("(kicad_pcb (version 20171130) (general (thickness 1.6))"
                 " (layers (0 Top signal)")  # 括号未闭合
    with pytest.raises(Exception):
        g1_convert.parse_by_route(truncated, "k5")
    with pytest.raises(ValueError):
        g1_convert.parse_by_route(
            "(kicad_pcb (version 20171130)) (kicad_pcb (version 20171130))",
            "k5")  # 顶层双根
    with pytest.raises(Exception):
        g1_convert.parse_by_route("(kicad_pcb (version 20221018)", "k9")


def test_preflight_skip_codes_fail_closed():
    base = {"board_id": "x", "profile_id": "corpusr2-x",
            "source_rel": "datasets/corpus-r2-r1/raw/d/x.kicad_pcb",
            "source_present": False, "source_sha256_measured": None,
            "source_sha256_declared": "0" * 64, "version_token": "1",
            "route": None}
    # 次序：缺文件 > sha 失锚 > 版本门 > 产物在
    r = g1_convert.preflight_skip(dict(base), pdir_exists=False)
    assert r[0] == "SOURCE_FILE_MISSING"
    e2 = dict(base, source_present=True, source_sha256_measured="f" * 64)
    r = g1_convert.preflight_skip(e2, pdir_exists=False)
    assert r[0] == "SHA_MISMATCH"
    e3 = dict(e2, source_sha256_measured="0" * 64)
    r = g1_convert.preflight_skip(e3, pdir_exists=False)
    assert r[0] == "VERSION_GATE_REJECT"
    e4 = dict(e3, route="k9", version_token="20221018")
    assert g1_convert.preflight_skip(e4, pdir_exists=False) is None
    r = g1_convert.preflight_skip(e4, pdir_exists=True)
    assert r[0] == "OUTPUT_EXISTS"
    assert all(r[0] in g1_convert.SKIP_REASONS for r in
               [g1_convert.preflight_skip(dict(base), False),
                g1_convert.preflight_skip(e2, False),
                g1_convert.preflight_skip(e3, False),
                g1_convert.preflight_skip(e4, True)])


# ---------------------------------------------------------------------------
# A2. 小夹具全链转换（三路径 × parse→构件→schema→双源回读）
# ---------------------------------------------------------------------------

K5_BOARD = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.4)")
  (general (thickness 1.6) (nets 3))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "") (net 1 GND) (net 2 VCC)
  (setup (trace_min 0.2) (trace_clearance 0.2) (via_min_size 0.6)
    (via_min_drill 0.3))
  (module "R:R_0603" (layer F.Cu) (at 0 0)
    (fp_text reference R1 (at 0 0) (layer F.SilkS))
    (pad 1 smd rect (at -0.5 0) (size 0.5 0.5) (layers F.Cu)
      (net 1 GND))
    (pad 2 smd rect (at 0.5 0) (size 0.5 0.5) (layers F.Cu)
      (net 2 VCC)))
  (segment (start 0 0) (end 1 1) (width 0.2) (net 1) (layer F.Cu))
  (via (at 1 1) (size 0.6) (drill 0.3) (net 1))
  (zone (net 1) (net_name GND) (layer F.Cu)))
"""

K9_BOARD = """(kicad_pcb (version 20221018) (generator pcbnew)
  (general (thickness 1.6))
  (layers (0 "F.Cu" mixed) (31 "B.Cu" mixed) (32 "F.SilkS" user))
  (net 0 "") (net 1 GND) (net 2 "SDA")
  (footprint "R:R_0603" (layer "F.Cu") (at 0 0)
    (fp_text reference "R1" (at 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at -0.5 0) (size 0.5 0.5) (layers "F.Cu")
      (net 1 "GND"))
    (pad "2" smd rect (at 0.5 0) (size 0.5 0.5) (layers "F.Cu")
      (net 2 "SDA")))
  (segment (start 0 0) (end 1 1) (width 0.2) (net 1) (layer "F.Cu"))
  (via (at 1 1) (size 0.6) (drill 0.3) (net 1)))
"""

LEGACY_BOARD = """(kicad_pcb (version 4) (host pcbnew 4.0.2)
  (general (thickness 1.6) (nets 2))
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (net 0 "") (net 1 +5V)
  (module "Lib:FP" (layer F.Cu) (at 0 0)
    (fp_text reference X1 (at 0 0) (layer F.SilkS))
    (pad 1 smd rect (at 0 0) (size 1 1) (layers F.Cu) (net 1 +5V)))
  (segment (start 0 0) (end 2 2) (width 0.25) (net 1) (layer F.Cu)))
"""


def _small_pipeline(text, route, board_id="small-board"):
    model = g1_convert.parse_by_route(text, route)
    crit = cc.derive_critical_nets(model)
    norm = g1_convert.normalized_text_by_route(
        model, route, source_path=f"datasets/x/{board_id}.kicad_pcb",
        source_sha256="a" * 64)
    profile = cc.build_profile_obj(model, profile_id=f"corpusr2-{board_id}",
                                   project_id=board_id, crit=crit)
    mf = cc.build_manifest_obj(
        project_id=board_id, profile_id=f"corpusr2-{board_id}",
        eda_version="test", critical_nets=crit["critical_nets"],
        dataset_splits={"train": [], "validation": [], "holdout": [],
                        "external_eval": []},
        output_root=f"profiles/corpusr2-{board_id}", board_id=board_id,
        dataset_routed_rel=f"../../datasets/x/{board_id}.kicad_pcb",
        drc_baseline_rel=None)
    return model, crit, norm, profile, mf


@pytest.mark.parametrize("text,route", [
    (K5_BOARD, "k5"), (K9_BOARD, "k9"), (LEGACY_BOARD, "legacy"),
])
def test_small_board_full_pipeline_schema_and_reparse(text, route):
    model, crit, norm, profile, mf = _small_pipeline(text, route)
    # schema 严格贴合（fail-closed 先例=s10 落盘前校验）
    assert manifest_mod.validate_profile(profile) == []
    assert manifest_mod.validate_manifest(mf) == []
    # 双源回读：规范化板 sexpr 直读 vs 源模型一阶计数
    nc = g1_convert.normalized_counts(norm)
    rc = g1_convert.reference_counts_from_model(model)
    assert nc["net_names"] == rc["net_names"]
    assert nc["footprint_refs"] == rc["footprint_refs"]
    assert nc["footprint_count"] == rc["footprint_count"]
    assert nc["pad_total"] == rc["pad_total"]
    assert nc["pad_net_names"] == rc["pad_net_names"]
    assert nc["pads_without_net"] == rc["pads_without_net"]
    assert nc["copper_layers"] == rc["copper_layers"]
    # 正则口径 vs 模型计数（PROVENANCE 门 2 风格）
    rx = g1_convert.regex_geometry_counts(text)
    assert rx["segments"] == model["segment_count"]
    assert rx["vias"] == model["via_count"]
    assert rx["zones"] == model["zone_count"]
    assert rx["footprints"] == len(model["modules"])
    # 单态板 graph：audit 节点不在场 + deviations 声明
    g = g1_convert.build_graph_generic(
        project_id="small-board", profile_id="corpusr2-small-board",
        revision="r1",
        file_hashes={"inputs/board.kicad_pcb": "b" * 64,
                     "inputs/stackup.json": "b" * 64,
                     "inputs/constraints.json": "b" * 64,
                     "derived/net-registry.json": "b" * 64,
                     "derived/feedforward-plan.json": "b" * 64},
        converter_path=g1_convert.converter_identity(route)["converter_path"])
    aids = [n["artifact_id"] for n in g["nodes"]]
    assert "audit_report" not in aids
    assert any("audit" in d for d in g["deviations"])
    assert g["converter_path"] == \
        g1_convert.converter_identity(route)["converter_path"]


def test_k9_modern_copper_whitelist_on_mixed_layers():
    """20221018 档 mixed 铜层必须入账（signal-only 判据=0 铜层虚假事实——
    K9_MODERN_COPPER_TYPES 按档白名单判据，与 4 板 fail-closed 教训同判）。"""
    model = cc.parse_kicad9_board(K9_BOARD)
    assert [(l["name"], l["type"]) for l in model["copper_layers"]] == [
        ("F.Cu", "mixed"), ("B.Cu", "mixed")]
    # 顶层声明网（< 20260206）：net 0 空名网 + GND + SDA
    assert [n["name"] for n in model["nets"]] == ["", "GND", "SDA"]


def test_k5_thresholds_setup_identity_derivation():
    model, crit, _norm, profile, _mf = _small_pipeline(K5_BOARD, "k5")
    assert profile["thresholds"] == {
        "min_track_width_mm": 0.2, "min_clearance_mm": 0.2,
        "via_min_size_mm": 0.6, "via_min_drill_mm": 0.3}
    assert model["setup"]["trace_min"] == "0.2"


# ---------------------------------------------------------------------------
# B. 批产物级（台账/盘面；中间态缺产物 skip，完工后全过）
# ---------------------------------------------------------------------------

_requires_plan = pytest.mark.skipif(not os.path.isfile(PLAN),
                                    reason="G1 plan 未落盘（中间态）")
_requires_ledger = pytest.mark.skipif(not os.path.isfile(LEDGER),
                                      reason="G1 ledger 未落盘（中间态）")


@_requires_plan
def test_plan_covers_37_boards_with_route_counts_and_sha_anchor():
    plan = _load(PLAN)
    assert plan["counts"]["planned"] == 37
    assert plan["counts"]["by_route"] == {"k9": 26, "k5": 9, "legacy": 2}
    ds = _load(os.path.join(REPO, "datasets", "corpus-r2-r1",
                            "manifest.json"))
    by_id = {b["board_id"]: b for b in ds["boards"]}
    for e in plan["boards"]:
        b = by_id[e["board_id"]]
        assert e["profile_id"] == "corpusr2-" + e["board_id"]
        assert e["source_sha256_measured"] == e["source_sha256_declared"] \
            == b["board_file_sha256"]
        assert e["version_token"] == b["kicad_version_token"]
        assert e["tier_designation"] == b["tier_designation"]
        assert e["project_group"] == b["project_group"]
    # 派生 split 快照（tier 原样派生，不重新切分）
    s = plan["derived_splits"]
    assert len(s["train"]) == 31 and len(s["holdout"]) == 6
    assert s["validation"] == [] and s["external_eval"] == []
    holdout_ids = {x.split(":", 1)[1] for x in ds["counts"]["holdout_pool"]}
    assert set(s["holdout"]) == holdout_ids


@_requires_ledger
def test_ledger_full_coverage_and_products_on_disk():
    ledger = _load(LEDGER)
    plan = _load(PLAN)
    assert ledger["counts"]["batch_total"] == 37
    assert ledger["counts"]["converted"] + ledger["counts"]["skipped"] == 37
    # skip（若有）必须显式原因码，不硬造
    for s in ledger["skipped"]:
        assert s["skip_reason"] in g1_convert.SKIP_REASONS
    # 逐 converted 板七件+graph+route-check 在盘且 schema 过
    for row in ledger["converted"]:
        pid = row["profile_id"]
        assert pid.startswith("corpusr2-")
        pdir = os.path.join(REPO, "profiles", pid)
        for f in ("inputs/board.kicad_pcb", "inputs/stackup.json",
                  "inputs/constraints.json", "derived/net-registry.json",
                  "derived/feedforward-plan.json", "profile.json",
                  "manifest.json", "graph.json", "route-check.json"):
            assert os.path.isfile(os.path.join(pdir, f)), (pid, f)
        prof = _load(os.path.join(pdir, "profile.json"))
        mf = _load(os.path.join(pdir, "manifest.json"))
        assert manifest_mod.validate_profile(prof) == []
        assert manifest_mod.validate_manifest(mf) == []
        assert mf["backtest"]["reference_route"] == \
            f"../../{row['source']['path']}"
        assert mf["dataset_splits"]["holdout"] and \
            len(mf["dataset_splits"]["train"]) == 31
        # conversion log 在台账且声明件形态锚定
        log = _load(os.path.join(REPO, "out", "v3-gline-r2",
                                 "conversion-logs", f"{pid}.json"))
        assert log["route_check"]["status"] == \
            g1_convert.ROUTE_CHECK_STATUS
        assert log["corpus_anchor"]["project_group"] == row["project_group"]


@_requires_ledger
def test_route_check_declaration_form_no_drc_fabrication():
    ledger = _load(LEDGER)
    for row in ledger["converted"]:
        rc = _load(os.path.join(REPO, "profiles", row["profile_id"],
                                "route-check.json"))
        assert rc["artifact_kind"] == "route_check_declaration"
        assert rc["route_check_status"] == g1_convert.ROUTE_CHECK_STATUS
        # 零 DRC 字段虚构：无执行结果字段（drc_max_error_severity 恒 null）
        assert rc["drc_max_error_severity"] is None
        assert "drc_errors" not in rc and "error_count" not in rc
        assert rc["reference_route"]["sha256"] == row["source"]["sha256"]
        assert rc["reference_route"]["path"].startswith(
            "datasets/corpus-r2-r1/raw/")
        # 治理携带（schema 冻结 manifest 的替代落点）
        anchor = rc["corpus_anchor"]
        assert anchor["tier_designation"] == row["tier_designation"]
        assert anchor["dataset_ref"]["path"] == \
            "datasets/corpus-r2-r1/manifest.json"
        assert len(anchor["dataset_ref"]["sha256"]) == 64


@_requires_ledger
def test_holdout_six_boards_materialized_with_pool_anchor():
    ledger = _load(LEDGER)
    by_id = {r["board_id"]: r for r in ledger["converted"]}
    pools = {}
    for bid, row in by_id.items():
        if row["tier_designation"] == "holdout-pool":
            anchor = _load(os.path.join(
                REPO, "profiles", row["profile_id"],
                "route-check.json"))["corpus_anchor"]
            pools[anchor["holdout_pool"]["pool_id"]] = bid
            rc = _load(os.path.join(REPO, "profiles", row["profile_id"],
                                    "route-check.json"))
            assert rc["dataset_role"] == "holdout"
    assert set(pools) == {"H1", "H2", "H3", "H4", "H5", "H6"}
    assert pools["H1"] == "kria-k26-devboard"
    assert pools["H6"] == "jetson-nano-baseboard"
    # H6 亲和警示逐字携带
    rc = _load(os.path.join(REPO, "profiles",
                            by_id["jetson-nano-baseboard"]["profile_id"],
                            "route-check.json"))
    assert "jetson-agx-thor" in rc["holdout_note"]


@_requires_ledger
def test_existing_profile_prefix_counts_untouched():
    """r1 既有 56 profile（35 pcbench+2 pcbbm+17 demo+2 smoke）零触碰：
    前缀计数不变且 corpusr2-* 恰为新增前缀。

    REPAIR-P4 W-1（G0，2026-09-23）：profiles/revc-coreboard/ 为项目配置
    声明 profile（非 corpus 数据域，登记=out/repair-p4/anchor-hashes-post-g0.json），
    白名单放行、不计入任何前缀计数。"""
    counts = {}
    corpusr2 = 0
    for name in sorted(os.listdir(os.path.join(REPO, "profiles"))):
        matched = False
        for pref in EXISTING_PREFIX_COUNTS:
            if name.startswith(pref):
                counts[pref] = counts.get(pref, 0) + 1
                matched = True
        if name.startswith("corpusr2-"):
            corpusr2 += 1
            matched = True
        if name == "revc-coreboard":
            matched = True  # G0 项目配置声明 profile（见 docstring）
        assert matched, f"未知前缀 profile 目录: {name}"
    assert counts == EXISTING_PREFIX_COUNTS
    ledger = _load(LEDGER)
    assert corpusr2 == ledger["counts"]["converted"]


@_requires_ledger
@pytest.mark.skipif(not os.path.isfile(VERIFY),
                    reason="G1 verify report 未落盘（中间态）")
def test_verify_report_all_pass_with_evidence():
    report = _load(VERIFY)
    ledger = _load(LEDGER)
    assert report["result"] == "pass"
    assert report["counts"]["fail"] == 0
    assert report["counts"]["verified"] == ledger["counts"]["converted"]
    by_ids = {r["board_id"] for r in ledger["converted"]}
    for row in report["boards"]:
        assert row["board_id"] in by_ids
        ids = {c["id"] for c in row["checks"]}
        # 核心证据类必须逐板在场
        assert {"source_sha_anchored", "evidence_counts_reconcile",
                "normalized_board_reparse", "net_registry_count",
                "profile_layers_equal_stackup",
                "route_check_declaration_form"} <= ids
        assert all(c["pass"] for c in row["checks"]), row["board_id"]
