"""TL-5 S10 批量包测试：分母纵深（78 剩余合规板逐板判定+能转尽转+参考态验证）。

覆盖（对最终落盘状态 fail-closed 校验+纯函数回放）：
- judge 台账一致性（78 板全集、分类计数闭合、4 块路径不兼容如实、slug 零冲突）；
- 转换台账与盘上一致（converted 板 10 文件齐+schema 合法+conversion log hash 对账）；
- 抽样 byte-exact 重放（转换=纯函数：同一源文本重建=盘上逐字节一致）；
- 负向 fail-closed（identity 不匹配/路径不兼容如实跳过；manifest splits 扩展键
  违反 schema→convert 不落盘）；
- check 报告/执行记录/S10 汇总台账一致性（staging 逐字节一致、结果分布闭合）；
- dataset manifest v3 升版合同（版本链、raw_hash 不变、normalized_hash 重算、
  DRC baseline 覆盖数、v1/v2 原样）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus, corpus_convert as cc, corpus_pcbench as cp
from pcbflow import check_stage, hashing, manifest as manifest_mod

BATCH = os.path.join("out", "v3-tl5", "batch-s10")
TL5 = os.path.join("out", "v3-tl5")
V2 = os.path.join(TL5, "dataset-manifest-pcbench-r1-v2.json")
V3 = os.path.join(TL5, "dataset-manifest-pcbench-r1-v3.json")
RAW = os.path.join("datasets", "pcbench-r1", "raw")

_S10_SPEC = importlib.util.spec_from_file_location(
    "s10_batch_orchestrate",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "s10_batch_orchestrate.py"))
s10 = importlib.util.module_from_spec(_S10_SPEC)
_S10_SPEC.loader.exec_module(s10)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ledgers():
    judge = _load(os.path.join(BATCH, "judge-ledger.json"))
    conv = _load(os.path.join(BATCH, "conversion-ledger.json"))
    return judge, conv


# ---------------- judge 台账一致性 ----------------

def test_judge_covers_all_78_batch_boards():
    judge, _ = _ledgers()
    v2 = _load(V2)
    done = {"74Logic_SA_ADC_SA-ADC", "kitspace_T32_ref",
            "LAUNCHXL-F28027-isolation-PCB_project1"}
    expect = sorted(
        b for r in ("train", "validation", "holdout")
        for b in v2["dataset_splits"][r] if b not in done)
    got = sorted(e["board_id"] for e in judge["entries"])
    assert got == expect and len(got) == 78
    assert judge["counts"]["judged"] == 78


def test_judge_counts_close_and_path_incompatible_known_four():
    judge, _ = _ledgers()
    entries = judge["entries"]
    n_skip = sum(1 for e in entries if e.get("skip_reason"))
    n_ok = len(entries) - n_skip
    assert judge["counts"]["convertible"] == n_ok
    assert sum(v for k, v in judge["counts"].items()
               if k != "judged" and k != "convertible") == n_skip
    path_bad = sorted(e["board_id"] for e in entries
                      if (e.get("skip_reason") or "").startswith(
                          "manifest_path_incompatible"))
    assert path_bad == [
        "Blink-Eras_Blink Eras",
        "RF_SIGNAL_GENERATOR_HARDWARE_RF Signal Generator",
        "cookiecutter-xsproduct_{{cookiecutter.product_name}}",
        "kitspace_Control%20Board"]
    # slug 零冲突（fail-closed 保证）
    assert judge["slug_collisions"] == []


def test_judge_identity_mismatch_records_detail():
    judge, _ = _ledgers()
    mism = [e for e in judge["entries"]
            if (e.get("skip_reason") or "").startswith("identity_mismatch")]
    assert mism, "identity_mismatch 分类非空（上游实况）"
    for e in mism:
        d = e["identity_detail"]
        assert not (d["net_id_sequence_equal"]
                    and d["module_ref_multiset_equal"])
        assert d["processed_nets"] >= 0 and d["raw_nets"] >= 0


# ---------------- 转换台账与盘上一致 ----------------

def test_conversion_ledger_matches_judge_convertible():
    judge, conv = _ledgers()
    convertible = sorted(e["board_id"] for e in judge["entries"]
                         if not e.get("skip_reason"))
    converted = sorted(e["board_id"] for e in conv["converted"])
    assert converted == convertible
    assert conv["counts"] == {"converted": len(converted),
                              "skipped": 0, "batch_total": 78}


PROFILE_FILES = ("profile.json", "manifest.json", "graph.json",
                 "route-check.json", "inputs/board.kicad_pcb",
                 "inputs/stackup.json", "inputs/constraints.json",
                 "derived/net-registry.json", "derived/audit.json",
                 "derived/feedforward-plan.json")


@pytest.mark.parametrize("entry_idx", [0, 7, 15, 31])
def test_converted_profile_on_disk_complete_and_valid(entry_idx):
    _, conv = _ledgers()
    e = conv["converted"][entry_idx]
    pdir = os.path.join("profiles", e["profile_id"])
    for f in PROFILE_FILES:
        assert os.path.isfile(os.path.join(pdir, f)), (e["profile_id"], f)
    mf, _ = manifest_mod.load_manifest(os.path.join(pdir, "manifest.json"))
    assert manifest_mod.validate_manifest(mf) == []
    prof, _ = manifest_mod.load_profile(os.path.join(pdir, "profile.json"))
    assert manifest_mod.validate_profile(prof) == []
    # conversion log 存在且输入 hash 与盘上数据集一致
    log = _load(e["conversion_log"]["path"])
    raw_rel = cp.dataset_board_paths(e["board_id"])["raw"]
    got = {i["path"]: i["sha256"] for i in log["inputs"]}
    assert got[raw_rel] == hashing.sha256_file(raw_rel)


def test_conversion_log_outputs_hash_reconcile():
    _, conv = _ledgers()
    for e in conv["converted"][:6] + conv["converted"][-3:]:
        log = _load(e["conversion_log"]["path"])
        for o in log["outputs"]:
            assert o["sha256"] == hashing.sha256_file(o["path"]), o["path"]


# ---------------- 抽样 byte-exact 重放 ----------------

@pytest.mark.parametrize("board_id", ["LibreSolar_MPPT_charger_20A",
                                      "zx-sizif-xxs_sizif-xxs"])
def test_conversion_byte_exact_replay(board_id):
    _, conv = _ledgers()
    assert board_id in {e["board_id"] for e in conv["converted"]}
    art = s10.build_board_artifacts(board_id)
    pid = art["profile_id"]
    for relp, text in art["texts"].items():
        disk = open(os.path.join("profiles", pid, relp),
                    encoding="utf-8").read()
        assert disk == text, (pid, relp)


def test_converted_json_files_canonical_form():
    _, conv = _ledgers()
    for e in conv["converted"]:
        pdir = os.path.join("profiles", e["profile_id"])
        for f in ("profile.json", "manifest.json", "graph.json",
                  "route-check.json", "inputs/stackup.json",
                  "inputs/constraints.json", "derived/net-registry.json",
                  "derived/audit.json", "derived/feedforward-plan.json"):
            raw = open(os.path.join(pdir, f), encoding="utf-8").read()
            assert raw == hashing.json_dumps(json.loads(raw)), (e, f)


# ---------------- 负向 fail-closed ----------------

def test_judge_negative_path_incompatible_board():
    e = s10.judge_one("kitspace_Control%20Board")
    assert e["manifest_path_ok"] is False
    assert e["skip_reason"].startswith("manifest_path_incompatible")


def test_judge_negative_identity_mismatch_board():
    e = s10.judge_one("4N35-TTL-Serial-Optoisolator_4N35-TTL-"
                      "Serial-Optoisolator")
    assert e.get("skip_reason", "").startswith("identity_mismatch")


def test_manifest_rejects_split_extension_keys():
    # dataset_splits 携带 split_unit 等扩展键 → schema 违反（convert 据此
    # fail-closed 跳过，不落盘）——回归 S10 首轮 32 板全 skip 的根因
    v2 = _load(V2)
    obj = cc.build_manifest_obj(
        project_id="p", profile_id="p", eda_version="e",
        critical_nets=[], dataset_splits=v2["dataset_splits"],
        output_root="out/x", board_id="b",
        dataset_routed_rel="../../datasets/x/raw.kicad_pcb",
        drc_baseline_rel="../../out/v3-tl5/drc-pcbench/x/x.drc-all.json")
    assert manifest_mod.validate_manifest(obj)


def test_bad_reference_sha_fail_closed():
    with pytest.raises(ValueError):
        check_stage.build_route_check_declaration(
            profile_id="p", board_id="b", dataset_role="train",
            reference_route_path="datasets/x/raw.kicad_pcb",
            reference_route_sha256="not-hex",
            profile_threshold_keys=[], prior_state_note="x")


# ---------------- check 报告与执行记录 ----------------

def test_check_reports_present_and_consistent():
    _, conv = _ledgers()
    for e in conv["converted"]:
        cdir = os.path.join(TL5, "check", e["profile_id"])
        rep = _load(os.path.join(cdir, "check-report.json"))
        assert rep["route_scope"] == "reference_verification"
        assert rep["result"] in ("pass", "fail")
        # staging 逐字节一致检查项过（kicad-cli 输入=datasets 参考态拷贝）
        by_id = {c["id"]: c for c in rep["checks"]}
        assert by_id["staging_copy_byte_identical"]["pass"] is True
        assert by_id["route_scope_reference_verification"]["pass"] is True
        assert by_id["reference_route_hash_binding"]["pass"] is True
        # 输入 hash 绑定与盘上一致
        for key, ref in rep["inputs"].items():
            assert ref["sha256"] == hashing.sha256_file(ref["path"]), (
                e["profile_id"], key)


def test_execution_record_s10_consistency():
    rec = _load(os.path.join(BATCH, "route-check-execution-record-s10.json"))
    _, conv = _ledgers()
    assert rec["route_scope"] == "reference_verification"
    assert rec["summary"]["profile_count"] == len(conv["converted"])
    assert all(e["staging_identical_to_reference"] for e in rec["entries"])
    n_pass = sum(1 for e in rec["entries"]
                 if e["check_report"]["result"] == "pass")
    assert rec["summary"]["results"] == {
        "pass": n_pass, "fail": len(rec["entries"]) - n_pass} or \
        rec["summary"]["results"].get("pass") == n_pass
    assert rec["toolchain"]["toolchain_lock"]["sha256"] == \
        hashing.sha256_file("toolchain_lock.json")
    assert rec["toolchain"]["kicad_cli_version"] == ["10.0.5"]
    # all_pass 仅当全部 pass；fail 板=参考态上游实况（语义见 batch-summary）
    assert rec["all_pass"] == (n_pass == len(rec["entries"]))


def test_drc_error_counts_consistent_across_severities():
    # 双 severity 运行 error 计数一致性：kicad-cli 10.0.5 对个别板（上游
    # 实况：cleanhawk250）error 分类跨运行不稳定（同板 4 次新鲜双跑=
    # 590/589、587/587，历史对 586/587、587/589）——合同要求"一致或
    # 不一致被 check 报告如实暴露"（fail-closed 双路径，不得掩盖）
    _, conv = _ledgers()
    for e in conv["converted"]:
        cdir = os.path.join(TL5, "check", e["profile_id"])
        rep = _load(os.path.join(cdir, "check-report.json"))
        consistent = rep["drc"]["consistency"]["error_count_equal_across_runs"]
        err = _load(os.path.join(cdir, f"{e['profile_id']}.drc-error.json"))
        allj = _load(os.path.join(cdir, f"{e['profile_id']}.drc-all.json"))
        n_err = sum(1 for v in err["violations"]
                    if v.get("severity") == "error")
        n_err_all = sum(1 for v in allj["violations"]
                        if v.get("severity") == "error")
        if consistent:
            assert n_err == n_err_all, e["profile_id"]
        else:
            # 不一致板：报告必须如实 fail 且 dual_severity_contract 检查项
            # 记为不过（不静默接受）
            assert rep["result"] == "fail", e["profile_id"]
            failed_ids = {c["id"] for c in rep["checks"] if not c["pass"]}
            assert "dual_severity_contract" in failed_ids, e["profile_id"]


# ---------------- 主路径图与 TD8 报告 ----------------

def test_graph_spec_ten_nodes_route_check_present():
    _, conv = _ledgers()
    for e in conv["converted"]:
        spec = _load(os.path.join(TL5, "mainpath", e["profile_id"],
                                  "graph-spec.json"))
        ids = [n["artifact_id"] for n in spec["nodes"]]
        assert len(ids) == 10 and len(set(ids)) == 10
        assert "route_check_declaration" in ids and "check_report" in ids
        for n in spec["nodes"]:
            if n.get("path") and n.get("sha256"):
                assert n["sha256"] == hashing.sha256_file(
                    os.path.join(TL5, "mainpath", e["profile_id"],
                                 n["path"])), (e["profile_id"], n["path"])


def test_profile_reports_six_stages_executed():
    rep_led = _load(os.path.join(BATCH, "report-ledger.json"))
    _, conv = _ledgers()
    assert len(rep_led["reports"]) == len(conv["converted"])
    for r in rep_led["reports"]:
        assert set(r["main_path_status"].values()) == {"executed"}, r
        mdir = os.path.join(TL5, "mainpath", r["profile_id"])
        rep = _load(os.path.join(mdir, "profile-report.json"))
        # 六段齐+route_scope 收窄注记在案（D17）
        assert set(rep["main_path"]) == set(cc.MAIN_PATH_STAGES)
        assert "参考 routed 态验证" in rep["main_path"]["route_check"][
            "authority"] or "reference_verification" in rep["main_path"][
            "route_check"]["authority"]
        # denominators 与 audit 构件账本一致
        audit = _load(os.path.join("profiles", r["profile_id"], "derived",
                                   "audit.json"))
        du = audit["denominators_unrouted"]
        for k in ("net_count", "module_count", "pad_count"):
            assert rep["denominators"][k] == du[k], (r["profile_id"], k)


# ---------------- S10 汇总台账与 manifest v3 ----------------

def test_batch_summary_ledger_closure():
    summary = _load(os.path.join(BATCH, "batch-summary.json"))
    judge, conv = _ledgers()
    n_conv = len(conv["converted"])
    assert summary["conversion"]["converted_in_batch"] == n_conv
    assert summary["conversion"]["total_converted_profiles"] == 3 + n_conv
    assert summary["conversion"]["total_profile_coverage"] == f"{3 + n_conv}/81"
    n_skip_records = len(summary["conversion"]["skip_reasons_per_board"])
    assert n_skip_records == 78 - n_conv
    # 结果分布闭合
    dist = summary["reference_check"]["check_result_distribution"]
    assert sum(dist.values()) == n_conv
    # 连通性分布闭合
    cdist = summary["reference_check"]["connectivity_distribution"]
    assert sum(cdist.values()) == n_conv
    # 异常板=result!=pass 板集合一致（结果态从 check 执行记录取，
    # 非 conversion ledger）
    rec = _load(os.path.join(BATCH, "route-check-execution-record-s10.json"))
    anomalies = {a["profile_id"] for a in
                 summary["reference_check"]["anomalies"]}
    expect = {e["profile_id"] for e in rec["entries"]
              if e["check_report"]["result"] != "pass"}
    assert anomalies == expect


def test_dataset_manifest_v3_version_chain_and_hashes():
    v2 = _load(V2)
    v3 = _load(V3)
    assert v3["dataset_id"] == "pcbench-r1" and v3["version"] == "3"
    assert v2["version"] == "2"  # v2 未被覆写
    # datasets 只读：raw_hash 不变
    assert v3["raw_hash"] == v2["raw_hash"]
    # normalized_hash=全量转换 profile ×7 文件 aggregate 重算
    _, conv = _ledgers()
    files = []
    for e in conv["converted"]:
        pid = e["profile_id"]
        for r in ("inputs/board.kicad_pcb", "inputs/stackup.json",
                  "inputs/constraints.json", "derived/net-registry.json",
                  "derived/audit.json", "derived/feedforward-plan.json",
                  "route-check.json"):
            p = f"profiles/{pid}/{r}"
            files.append({"path": p, "sha256": hashing.sha256_file(p)})
    expect = hashing.sha256_bytes(
        hashing.canonical_json_bytes(sorted(files, key=lambda x: x["path"])))
    # v3 覆盖=既有 3 板（值已含）+新板；直接全量复算
    all_files = list(files)
    for pid in ("pcbench-74logic-sa-adc-sa-adc", "pcbench-kitspace-t32-ref",
                "pcbench-launchxl-f28027-isolation-pcb-project1"):
        for r in ("inputs/board.kicad_pcb", "inputs/stackup.json",
                  "inputs/constraints.json", "derived/net-registry.json",
                  "derived/audit.json", "derived/feedforward-plan.json",
                  "route-check.json"):
            p = f"profiles/{pid}/{r}"
            all_files.append({"path": p,
                              "sha256": hashing.sha256_file(p)})
    expect_all = hashing.sha256_bytes(hashing.canonical_json_bytes(
        sorted(all_files, key=lambda x: x["path"])))
    assert v3["normalized_hash"] == expect_all
    # DRC baseline 覆盖=3+N；conversion_log 全量
    assert len(v3["DRC_baseline"]["per_profile"]) == 3 + len(conv["converted"])
    assert len(v3["conversion_log"]) == 3 + len(conv["converted"])
    # 版本链：prior_version 指向 v2 实文件 hash
    pv = v3["field_missingness"]["prior_version"]
    assert pv["path"] == "out/v3-tl5/dataset-manifest-pcbench-r1-v2.json"
    assert pv["sha256"] == hashing.sha256_file(V2)
    # v1/v2 原样（manifest_sha256 自洽）
    for path in (V2, os.path.join(
            TL5, "dataset-manifest-pcbench-r1.json")):
        m = _load(path)
        body = {k: v for k, v in m.items() if k != "manifest_sha256"}
        assert m["manifest_sha256"] == hashing.sha256_bytes(
            hashing.canonical_json_bytes(body)), path
    # v3 自洽
    body3 = {k: v for k, v in v3.items() if k != "manifest_sha256"}
    assert v3["manifest_sha256"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(body3))


def test_manifest_v3_field_missingness_updated():
    v3 = _load(V3)
    fm = v3["field_missingness"]
    assert "S10" in fm["conversion.scope"]
    assert fm["normalized_hash.scope"].startswith("v3 scope=")
    assert "violations 数组顺序" in fm["DRC_baseline.reproducibility"]
    assert fm["manifest_path_incompatible_boards"].startswith("4 块保留板")


def test_batch_products_no_host_paths():
    # 核台账/manifest 禁主机路径（红线 4 抽样）
    import re
    for name in ("judge-ledger.json", "conversion-ledger.json",
                 "batch-summary.json"):
        text = open(os.path.join(BATCH, name), encoding="utf-8").read()
        for pat in (r"[A-Za-z]:\\\\", r"[A-Za-z]:/", "/c/Users/",
                    r"C:.Users"):
            assert not re.search(pat, text), (name, pat)


# ---------------- TL-5-G v4 复评（S10 数字口径变化；v3 保留） ----------------

def test_tl5_gate_v4_pass_v3_preserved_predicates_unchanged():
    v3 = _load(os.path.join(TL5, "gate-record-tl5-v3.json"))
    v4 = _load(os.path.join(TL5, "gate-record-tl5-v4.json"))
    assert v4["status"] == "ok" and v4["gate_record"]["result"] == "pass"
    assert v4["verify_errors"] == [] and v4["gate_record"]["failure_codes"] == []
    # v3 保留原样（版本递增，不覆写）
    assert v3["gate_record"]["result"] == "pass"
    assert v3["gate_record"]["snapshot_revision"] == "v3-s8"
    assert v4["gate_record"]["snapshot_revision"] == "v4-s10"
    # 谓词语义不变：同 id 集合同 value
    p3 = {p["id"]: p["value"] for p in v3["gate_record"]["required_predicates"]}
    p4 = {p["id"]: p["value"] for p in v4["gate_record"]["required_predicates"]}
    assert set(p3) == set(p4) and all(v is True for v in p4.values())
    # 数字口径更新：v4 evidence 含 37 profile/35/81 覆盖与 46 跳过
    joined = "".join(p["evidence"] for p in
                     v4["gate_record"]["required_predicates"])
    assert "37" in joined and "35/81" in joined and "42 identity_mismatch" \
        in joined.replace("\n", "")
    # 输入扩展：32 新板四件套 + manifest v3 + s10 台账在场且 hash 对盘
    ids = {i["artifact_id"] for i in v4["gate_record"]["inputs"]}
    _, conv = _ledgers()
    for e in conv["converted"][:4] + conv["converted"][-2:]:
        pid = e["profile_id"]
        for aid in (f"profile_report_{pid}", f"graph_report_{pid}",
                    f"check_report_{pid}",
                    f"route_check_declaration_{pid}"):
            assert aid in ids
    for aid in ("dataset_manifest_pcbench_r1_v3", "judge_ledger_s10",
                "batch_summary_s10", "route_check_execution_record_s10"):
        assert aid in ids
    by_id = {i["artifact_id"]: i for i in v4["gate_record"]["inputs"]}
    for pid_part, path in (
            ("dataset_manifest_pcbench_r1_v3",
             "out/v3-tl5/dataset-manifest-pcbench-r1-v3.json"),
            ("judge_ledger_s10", "out/v3-tl5/batch-s10/judge-ledger.json"),
            ("batch_summary_s10", "out/v3-tl5/batch-s10/batch-summary.json")):
        assert by_id[pid_part]["sha256"] == hashing.sha256_file(path)


def test_tl5_gate_v4_byte_exact_replay():
    from pcbflow import gate as gate_mod
    spec = _load(os.path.join(TL5, "gate-spec-tl5-v4.json"))
    record = _load(os.path.join(TL5, "gate-record-tl5-v4.json"))["gate_record"]
    replay = gate_mod.evaluate_gate(**spec)
    assert hashing.json_dumps(replay) == hashing.json_dumps(record)
    # core hash 一致（evaluate_gate 纯函数重放）
    assert gate_mod.gate_core_hash(replay) == gate_mod.gate_core_hash(record)
