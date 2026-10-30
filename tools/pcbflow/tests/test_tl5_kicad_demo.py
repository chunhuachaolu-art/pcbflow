"""TL-5 第四包：KiCad demo 语料合同测试（corpus_kicad_demo；纯函数+真实库回放）。

覆盖：逐 demo 许可分类（默认映射/目录级宽松/copyleft/NC/无板/未知）、
审计账本（真实表重放确定性+fail-closed）、留存白名单归类、板 survey 与
拓扑组 id、demo 组简分（确定性+组不跨界+frozen+audit_split_cross 复核）、
跨库去重（合成重复+无重复）、真实 kicad-demos-r1 回放（账本 hash 对账/
manifest 自洽/raw_hash 重算/泄漏审计/跨库零重复）。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus, corpus_kicad_demo as kcd, hashing

RAW = os.path.join("datasets", "kicad-demos-r1", "raw")
AUDIT = os.path.join("out", "v3-tl5", "kicad-demo-license-audit.json")
LEDGER = os.path.join("out", "v3-tl5",
                      "retention-ledger-kicad-demos-r1.json")
LEAK = os.path.join("out", "v3-tl5", "leakage-audit-kicad-demos-r1.json")
R4 = os.path.join("out", "v3-tl5", "source-research-r4.json")
MANIFEST = os.path.join("out", "v3-tl5",
                        "dataset-manifest-kicad-demos-r1.json")


# ---------------- 逐 demo 许可分类 ----------------

def test_classify_default_repo_mapping_and_no_board():
    r = kcd.classify_demo_license(None, 3)
    assert r == {"decision": "retain",
                 "reason_code": "retain_default_repo_mapping",
                 "license_id": "CC-BY-SA-4.0"}
    r0 = kcd.classify_demo_license(None, 0)
    assert r0["decision"] == "not_available"
    assert r0["reason_code"] == "no_board_files"


def test_classify_dir_license_matrix():
    for lic in ("Apache-2.0", "CC-BY-SA-4.0", "CERN-OHL-P-2.0"):
        r = kcd.classify_demo_license(lic, 1)
        assert r["decision"] == "retain"
        assert r["reason_code"] == "retain_dir_license_permissive"
    for lic in ("CERN-OHL-S-2.0", "GPL-3.0", "MPL-2.0", "CERN-OHL-W-2.0"):
        r = kcd.classify_demo_license(lic, 1)
        assert r["decision"] == "exclude"
        assert r["reason_code"] == "copyleft_conservative_exclusion"
    for lic in ("CC-BY-NC-SA-4.0", "CC-BY-NC-4.0", "CC-BY-ND-4.0"):
        r = kcd.classify_demo_license(lic, 1)
        assert r["decision"] == "blocked"
        assert r["reason_code"] == "prohibitive_noncommercial"
    r = kcd.classify_demo_license("Some-Unknown-1.0", 1)
    assert r["decision"] == "blocked"
    assert r["reason_code"] == "license_unrecognized"


# ---------------- id/revision 派生 ----------------

def test_sanitize_demo_id():
    assert kcd.sanitize_demo_id("sonde xilinx") == "sonde_xilinx"
    assert kcd.sanitize_demo_id("video") == "video"
    assert kcd.sanitize_demo_id("vme-wren") == "vme-wren"
    with pytest.raises(ValueError):
        kcd.sanitize_demo_id("   ")


def test_demo_board_id_override_and_revision():
    assert kcd.demo_board_id(
        "multichannel",
        "multichannel/multichannel_mixer.kicad_pcb") \
        == "multichannel/multichannel_mixer"
    assert kcd.demo_board_id(
        "multichannel",
        "multichannel/multichannel_mixer-unrouted.kicad_pcb") \
        == "multichannel/multichannel_mixer"
    assert kcd.demo_board_id("ecc83", "ecc83/ecc83-pp_v2.kicad_pcb") \
        == "ecc83/ecc83-pp_v2"
    assert kcd.demo_board_id("sonde_xilinx", "sonde xilinx/sonde xilinx.kicad_pcb") \
        == "sonde_xilinx/sonde_xilinx"
    assert kcd.board_revision(
        "multichannel/multichannel_mixer.kicad_pcb") == "routed"
    assert kcd.board_revision(
        "multichannel/multichannel_mixer-unrouted.kicad_pcb") == "unrouted"
    assert kcd.board_revision("video/video.kicad_pcb") == "as_shipped"


# ---------------- 审计账本（真实表重放） ----------------

def _entries_from_table():
    return [{"demo_id": d, "board_files": list(kcd.BOARD_FILES[d])}
            for d in sorted(kcd.BOARD_FILES)]


def test_ledger_real_table_replay_counts_and_determinism():
    led = kcd.build_demo_audit_ledger(_entries_from_table())
    led2 = kcd.build_demo_audit_ledger(_entries_from_table())
    assert hashing.json_dumps(led) == hashing.json_dumps(led2)
    assert led["counts"]["evaluated"] == 18
    assert led["counts"]["retained_demos"] == 15
    assert led["counts"]["retained_board_files"] == 18
    assert led["counts"]["not_available"] == 1
    assert led["counts"]["blocked"] == 1
    assert led["counts"]["copyleft_conservative_exclusion"] == 1
    retained_ids = [e["demo_id"] for e in led["retained"]]
    assert "cm5_minima" not in retained_ids
    assert "stickhub" not in retained_ids
    assert "simulation" not in retained_ids
    assert len(retained_ids) == 15
    by_id = {e["demo_id"]: e for e in led["retained"] + led["excluded"]}
    assert by_id["cm5_minima"]["license_id"] == "CERN-OHL-S-2.0"
    assert by_id["stickhub"]["decision"] == "blocked"
    assert by_id["simulation"]["decision"] == "not_available"
    assert by_id["jetson-agx-thor-baseboard"]["license_id"] == "Apache-2.0"
    assert by_id["royalblue54L_feather"]["license_id"] == "CERN-OHL-P-2.0"
    assert by_id["openair-max"]["license_id"] == "CC-BY-SA-4.0"
    # retained 条目无 decision 字段（保持与 pcbench 账本同构）
    assert all("decision" not in e for e in led["retained"])
    assert all("decision" in e for e in led["excluded"])


def test_ledger_fail_closed():
    bad = _entries_from_table()
    for e in bad:
        if e["demo_id"] == "video":
            e["board_files"] = ["video/wrong.kicad_pcb"]
    with pytest.raises(ValueError):
        kcd.build_demo_audit_ledger(bad)
    unknown = [{"demo_id": "no_such_demo", "board_files": []}]
    with pytest.raises(KeyError):
        kcd.build_demo_audit_ledger(unknown)


# ---------------- 留存白名单 ----------------

def test_retention_whitelist_categories():
    keep = ["board.kicad_pcb", "proj.kicad_pro", "sch.kicad_sch",
            "lib.kicad_sym", "fp.kicad_mod", "sheet.kicad_wks",
            "rules.kicad_dru", "LICENSE", "LICENSE.txt", "LICENSE.md",
            "README", "README.md", "COPYING", "fp-lib-table",
            "sym-lib-table"]
    for fn in keep:
        ok, cat = kcd.classify_retention_file(fn)
        assert ok, fn
        assert cat in ("board_or_project_file", "license_or_readme",
                       "project_file")
    skip = {"x.step": "3d_model", "x.stp": "3d_model", "x.wrl": "3d_model",
            "x.wings": "3d_model", "x.gbr": "fabrication",
            "x.drl": "fabrication", "x.gbrjob": "fabrication",
            "x.pos": "fabrication", "x.zip": "fabrication",
            "x.pdf": "document", "x.jpg": "image", "x.svg": "image",
            "x.bmp": "image", "x.bin": "misc_binary", "x.db":
            "misc_binary", "x.json": "plugin_config", "x.txt": "tool_data"}
    for fn, cat in skip.items():
        ok, got = kcd.classify_retention_file(fn)
        assert not ok and got == cat, fn


# ---------------- 板 survey 与拓扑组 ----------------

def test_survey_board_text_counts_and_version():
    text = ('(kicad_pcb (version 20241229) (generator "pcbnew")\n'
            ' (generator_version "9.0")\n'
            ' (net 0 "") (net 1 "GND") (net 2 "VCC")\n'
            ' (footprint "R_0402" (layer "F.Cu")\n'
            '  (pad "1" smd rect (at 0 0) (size 0.5 0.5)\n'
            '   (layers "F.Cu" "F.Mask") (net 1 "GND"))\n'
            '  (pad "2" smd rect (at 1 0) (size 0.5 0.5)\n'
            '   (layers "F.Cu" "F.Mask") (net 2 "VCC")))\n'
            ' (segment (start 0 0) (end 1 1) (width 0.2) (net 1))\n'
            ' (via (at 0 0) (size 0.6) (drill 0.3) (net 1))\n'
            ' (zone (net 1) (net_name "GND") (layers "F.Cu")))\n')
    sv = kcd.survey_board_text(text)
    assert sv["version_token"] == "20241229"
    assert sv["generator_version"] == "9.0"
    assert sv["zone_count"] == 1
    sig = sv["signature"]
    # net_count=一阶 "(net " 计数：3 网表声明+2 pad+1 zone+1 segment+1 via
    assert sig["net_count"] == 8 and sig["footprint_count"] == 1
    assert sig["pad_count"] == 2 and sig["segment_count"] == 1
    assert sig["via_count"] == 1 and sig["named_net_count"] == 4
    g1 = kcd.topology_group_id(sig)
    g2 = kcd.topology_group_id(kcd.survey_board_text(text)["signature"])
    assert g1 == g2 and g1.startswith("ktd-topo-")
    other = dict(sig, pad_count=3)
    assert kcd.topology_group_id(other) != g1


# ---------------- demo 组简分 ----------------

def test_assign_demo_splits_deterministic_and_group_contained():
    demo_boards = {d: [f"{d}/b{i}" for i in range((i * 7 + 3) % 5 + 1)]
                   for i, d in enumerate(
        ["complex_hierarchy", "constraints", "ecc83", "interf_u",
         "jetson-agx-thor-baseboard", "kit-dev-coldfire-xilinx_5213",
         "microwave", "multichannel", "openair-max", "pic_programmer",
         "royalblue54L_feather", "sonde_xilinx", "tiny_tapeout", "video",
         "vme-wren"])}
    s1 = kcd.assign_demo_splits(demo_boards)
    s2 = kcd.assign_demo_splits(demo_boards)
    assert hashing.json_dumps(s1) == hashing.json_dumps(s2)
    assert s1["holdout_frozen_readonly"] is True
    assert s1["validation"] == []
    ordered = sorted(demo_boards)
    assert s1["holdout"] == sorted(
        b for d in ordered[-kcd.HOLDOUT_DEMO_COUNT:]
        for b in demo_boards[d])
    all_boards = sorted(b for bs in demo_boards.values() for b in bs)
    assert sorted(s1["train"] + s1["holdout"]) == all_boards
    groups = [(b, d) for d, bs in demo_boards.items() for b in bs]
    check = corpus.audit_split_cross(s1, groups)
    assert check["result"] == "pass", check["violations"]
    with pytest.raises(ValueError):
        kcd.assign_demo_splits({"a": ["a/x"], "b": ["b/y"]})


# ---------------- 跨库去重 ----------------

def _it(lib, bid, text):
    return {"library": lib, "board_id": bid, "file_role": "board_file",
            "text": text}


def test_cross_library_dedup_detects_and_clears():
    a = "(kicad_pcb (version 20241229)   (net 1 \"GND\"))"
    b = '(kicad_pcb\n(version 20241229)\n(net 1 "GND"))'
    r = kcd.audit_cross_library([_it("own", "own/x", a)],
                                [_it("other", "other/y", b)])
    assert r["result"] == "cross_library_duplicates_found"
    assert r["content_duplicate_group_count"] == 1
    r2 = kcd.audit_cross_library([_it("own", "own/x", a)],
                                 [_it("other", "other/y",
                                      "(kicad_pcb (version 20171130))")])
    assert r2["result"] == "no_cross_library_duplicates"
    assert r2["content_duplicate_group_count"] == 0


# ---------------- 真实库回放（datasets/ + out/） ----------------

def test_real_ledger_on_disk_matches_module_replay():
    disk = json.load(open(LEDGER, encoding="utf-8"))
    replay = kcd.build_demo_audit_ledger(_entries_from_table())
    keys = ("demo_id", "upstream_dir", "license_id", "reason_code",
            "dir_license_file", "board_file_count", "board_files",
            "project_group")
    strip = lambda e: {k: e[k] for k in keys}
    assert [strip(e) for e in disk["retained_demos"]] == replay["retained"]
    assert disk["excluded_demos"] == replay["excluded"]
    assert disk["summary"]["retained_demos"] == 15
    assert disk["summary"]["retained_boards"] == 17
    assert disk["summary"]["retained_board_files"] == 18
    assert disk["summary"]["retained_files_total"] == 408
    assert disk["archive_sha256"] == kcd.ARCHIVE_SHA256
    assert disk["pin_commit"] == kcd.PIN_COMMIT
    # multichannel 双态 revision（上游文件名明示）
    mc = [b for e in disk["retained_demos"] if e["demo_id"] == "multichannel"
          for b in e["boards"]]
    assert sorted(b["revision"] for b in mc) == ["routed", "unrouted"]
    # 数据集级许可原文三件在账
    assert sorted(f["dataset_rel"].rsplit("/", 1)[-1]
                  for f in disk["dataset_license_files"]) \
        == ["LICENSE.APACHE-2.0", "LICENSE.CC-BY-SA-4.0", "LICENSE.README"]


def test_real_dataset_files_match_ledger_hashes():
    disk = json.load(open(LEDGER, encoding="utf-8"))
    rows = [f for e in disk["retained_demos"] for f in e["files"]] \
        + disk["dataset_license_files"]
    for row in rows:
        rel = row["dataset_rel"]
        assert os.path.isfile(rel), rel
        assert hashing.sha256_file(rel) == row["sha256"], rel
    # 全部文件都落在 raw/ 之下且路径字符集兼容
    import re
    for row in rows:
        assert re.fullmatch(r"^[A-Za-z0-9._/+-]+", row["dataset_rel"]), row
        assert row["dataset_rel"].startswith(RAW.replace("\\", "/"))


def test_real_manifest_self_consistent_and_raw_hash_recomputed():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    body = {k: v for k, v in m.items() if k != "manifest_sha256"}
    assert hashing.sha256_bytes(
        hashing.canonical_json_bytes(body)) == m["manifest_sha256"]
    disk = json.load(open(LEDGER, encoding="utf-8"))
    rows = [f for e in disk["retained_demos"] for f in e["files"]] \
        + disk["dataset_license_files"]
    raw_files = [{"path": r["dataset_rel"], "sha256": r["sha256"]}
                 for r in rows]
    assert corpus.aggregate_raw_hash(raw_files) == m["raw_hash"]
    # 盘上重算（不信任账本，直接读文件）
    on_disk = []
    for dirpath, _, files in os.walk(RAW):
        for fn in files:
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, ".").replace(os.sep, "/")
            on_disk.append({"path": rel, "sha256": hashing.sha256_file(fp)})
    assert len(on_disk) == 408
    assert corpus.aggregate_raw_hash(on_disk) == m["raw_hash"]
    assert len(m["board_ids"]) == 17
    assert m["dataset_id"] == "kicad-demos-r1" and m["version"] == "1"
    assert m["dataset_splits"]["holdout_frozen_readonly"] is True
    assert m["excluded_boards"]["summary_counts"]["evaluated"] == 18


def test_real_leakage_and_cross_library_pass():
    leak = json.load(open(LEAK, encoding="utf-8"))
    assert leak["result"] == "pass"
    assert leak["in_library"]["result"] == "pass"
    assert leak["cross_library_dedup"]["result"] \
        == "no_cross_library_duplicates"
    assert leak["cross_library_dedup"]["own_board_files"] == 18
    assert leak["cross_library_dedup"]["other_board_files"] == 166
    # 泄漏审计 split 交叉复核与 manifest splits 一致（pass 且角色齐全）
    assert leak["in_library"]["split_cross"]["result"] == "pass"
    m = json.load(open(MANIFEST, encoding="utf-8"))
    for role in ("train", "validation", "holdout"):
        assert role in m["dataset_splits"]
    assert sorted(m["dataset_splits"]["train"]
                  + m["dataset_splits"]["holdout"]) \
        == sorted(m["board_ids"])


def test_real_source_research_r4_references_match_disk():
    r4 = json.load(open(R4, encoding="utf-8"))
    ev = r4["evidence"]
    assert hashing.sha256_file(ev["license_audit"]["path"]) \
        == ev["license_audit"]["sha256"]
    assert hashing.sha256_file(ev["retention_ledger"]["path"]) \
        == ev["retention_ledger"]["sha256"]
    assert r4["r4_findings"]["audit_outcome"] \
        == "per_demo_audit_mixed_retain_15_of_18"
    outcome = r4["r4_findings"]["per_demo_outcome"]
    assert len(outcome) == 18
    assert outcome["cm5_minima"]["decision"] == "exclude"
    assert outcome["stickhub"]["decision"] == "blocked"
    assert outcome["simulation"]["decision"] == "not_available"
    assert sum(1 for v in outcome.values()
               if v["decision"] == "retain") == 15
    corr = r4["r4_findings"]["license_coverage_verdict"][
        "r2_claim_correction"]
    assert "Boost" in corr["r2_claim"]
    assert "CERN-OHL-S-2.0" in corr["actual"]
    audit = json.load(open(AUDIT, encoding="utf-8"))
    assert corr["evidence_sha256"] \
        == audit["per_demo_license_evidence"]["cm5_minima"]["sha256"]
    # r4 引用的上游链路 pin/归档与模块常量一致
    assert r4["r4_findings"]["source_id"] == "SRC-KICAD-DEMO"
    assert r4["r4_findings"]["pin_commit"] == kcd.PIN_COMMIT
    assert r4["r4_findings"]["acquisition"]["archive_sha256"] \
        == kcd.ARCHIVE_SHA256
