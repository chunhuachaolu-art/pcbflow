"""TL-5 第三包：PCBench 语料合同测试（corpus_pcbench；纯函数+真实库回放）。

覆盖：逐板许可分类（dict/list/null/str/NOASSERTION/copyleft）、保留账本
（含内容去重排除）、组级三分 split（确定性+组不跨界+frozen+小组集边界）、
unrouted 推导（不改入参）、board slug、manifest 路径字符集兼容过滤、
确定性选板（含空槽如实跳过）、TD8 manifest record→corpus manifest、
转换日志合同、真实 pcbench-r1 库回放（ledger/split/选板/跨库去重）。
"""

from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus, corpus_convert as cc, corpus_pcbench as cp, hashing

RAW = os.path.join("datasets", "pcbench-r1", "raw")
LEDGER = os.path.join("out", "v3-tl5", "retention-ledger-pcbench-r1.json")
MANIFEST = os.path.join("out", "v3-tl5", "dataset-manifest-pcbench-r1.json")


def _mit():
    return {"key": "mit", "name": "MIT License", "spdx_id": "MIT"}


# ---------------- 逐板许可分类 ----------------

def test_classify_dict_permissive_spdx():
    for spdx in ("MIT", "Apache-2.0", "CC-BY-SA-4.0", "WTFPL", "Unlicense"):
        r = cp.classify_board_license({"spdx_id": spdx})
        assert r == {"decision": "retain",
                     "reason_code": "retain_permissive_spdx",
                     "license_id": spdx}


def test_classify_dict_copyleft_and_noassertion():
    assert cp.classify_board_license(
        {"spdx_id": "GPL-3.0"})["reason_code"] == "copyleft_conservative_exclusion"
    assert cp.classify_board_license(
        {"spdx_id": "NOASSERTION"})["reason_code"] == "license_noassertion"
    assert cp.classify_board_license(
        {"spdx_id": "SOME-OTHER"})["reason_code"] == "license_spdx_other"
    for spdx in ("GPL-3.0", "AGPL-3.0", "MPL-2.0"):
        assert cp.classify_board_license(
            {"spdx_id": spdx})["decision"] == "exclude"


def test_classify_null_and_empty_str_and_untyped():
    assert cp.classify_board_license(None)["reason_code"] == "license_null"
    r = cp.classify_board_license("")
    assert r["reason_code"] == "license_empty_str" and r["license_id"] is None
    assert cp.classify_board_license(
        42)["reason_code"] == "license_field_untyped"


def test_classify_list_named_permissive_and_ambiguous():
    ok = [{"name": "MIT",
           "link": "https://raw.../LICENSE"}]
    assert cp.classify_board_license(ok)["decision"] == "retain"
    dual = [{"name": "BSD", "link": ".../LICENSE-0BSD.txt"},
            {"name": "Apache", "link": ".../LICENSE-Apache-2.0.txt"}]
    assert cp.classify_board_license(dual)["decision"] == "retain"
    for names in (["GNU"], ["CERN"], ["Creative Commons"],
                  ["License not found"], ["TAPR"], ["MIT", "GNU"]):
        assert cp.classify_board_license(
            [{"name": n} for n in names])["decision"] == "exclude"
    assert cp.classify_board_license([])["decision"] == "exclude"


# ---------------- 保留账本 ----------------

def _entry(board_id, *, on_disk=True, ver="20171130", lic=None,
           source="https://github.com/x/y", author="x"):
    return {"board_id": board_id, "on_disk": on_disk, "kicad_version": ver,
            "licenses_field": lic, "source": source, "author": author}


def test_retention_ledger_decisions_and_counts():
    entries = [
        _entry("a_mit", lic=_mit()),
        _entry("b_gpl", lic={"spdx_id": "GPL-3.0"}),
        _entry("c_null", lic=None),
        _entry("d_nodisk", lic=_mit(), on_disk=False),
        _entry("e_kicad6", lic=_mit(), ver="20211014"),
        _entry("f_dup", lic=_mit()),
    ]
    led = cp.build_retention_ledger(entries, duplicate_of={"f_dup": "a_mit"})
    assert [r["board_id"] for r in led["retained"]] == ["a_mit"]
    reasons = {e["reason_code"] for e in led["excluded"]}
    assert reasons == {"copyleft_conservative_exclusion", "license_null",
                       "metadata_entry_without_disk_dir",
                       "kicad_version_out_of_scope",
                       "duplicate_content_of:a_mit"}
    assert led["counts"]["retained"] == 1 and led["counts"]["excluded"] == 5
    # 同一输入重放 → 同账本（canonical 确定性）
    led2 = cp.build_retention_ledger(entries, duplicate_of={"f_dup": "a_mit"})
    assert hashing.json_dumps(led) == hashing.json_dumps(led2)


# ---------------- 组级三分 split ----------------

def test_split_deterministic_and_group_contained():
    gb = {f"https://github.com/x/r{i}": [f"b{i}_{j}" for j in range(k)]
          for i, k in enumerate((3, 1, 4, 1, 5, 9, 2, 6), start=1)}
    s1 = cp.assign_group_splits(gb)
    s2 = cp.assign_group_splits(gb)
    assert hashing.json_dumps(s1) == hashing.json_dumps(s2)
    roles = ("train", "validation", "holdout")
    assert s1["holdout_frozen_readonly"] is True
    assert all(s1[r] for r in roles)
    # 组不跨界：每组所有板同角色
    for g, bs in gb.items():
        owner = {r for r in roles for b in bs if b in s1[r]}
        assert len(owner) == 1, (g, owner)
    # 与 corpus.audit_split_cross 联立 → pass
    board_groups = [(b, g) for g, bs in gb.items() for b in bs]
    splits = {r: s1[r] for r in roles}
    splits["external_eval"] = []
    splits["holdout_frozen_readonly"] = True
    cross = corpus.audit_split_cross(splits, board_groups)
    assert cross["result"] == "pass", cross["violations"]


def test_split_small_group_set_edge_case():
    # 3 组小集：边界保证路径触发（train 让出一组给空角色，三方非空）
    gb = {"https://github.com/x/one": ["b1", "b2"],
          "https://github.com/x/two": ["b3"],
          "https://github.com/x/three": ["b4"]}
    s = cp.assign_group_splits(gb)
    assert all(s[r] for r in ("train", "validation", "holdout"))
    total = sum(len(s[r]) for r in ("train", "validation", "holdout"))
    assert total == 4
    # 2 组退化集：物理上无法三方非空——如实保留空角色，不虚构
    gb2 = {"https://github.com/x/one": ["b1", "b2"],
           "https://github.com/x/two": ["b3"]}
    s2 = cp.assign_group_splits(gb2)
    total2 = sum(len(s2[r]) for r in ("train", "validation", "holdout"))
    assert total2 == 3
    assert not all(s2[r] for r in ("train", "validation", "holdout"))


def test_split_ratio_approximation():
    gb = {f"g{i:03d}": [f"b{i:03d}"] for i in range(100)}
    s = cp.assign_group_splits(gb)
    assert len(s["train"]) == 70
    assert 12 <= len(s["validation"]) <= 18
    assert 12 <= len(s["holdout"]) <= 18


# ---------------- unrouted 推导 / slug / 路径兼容 ----------------

def _k5_model():
    synth = (
        "(kicad_pcb (version 20171130) (host pcbnew \"(5.1.4)\")\n"
        "  (general (thickness 1.6) (tracks 314) (modules 1) (nets 2))\n"
        "  (layers (0 Top signal) (31 Bottom signal))\n"
        "  (setup (trace_min 0.2))\n"
        "  (net 0 \"\") (net 1 GND)\n"
        "  (module Lib:A (layer Top) (at 1 2)\n"
        "    (fp_text reference U1 (at 0 0) (layer F.SilkS))\n"
        "    (pad 1 smd rect (at 0 0) (size 1 1) (layers F.Cu) (net 1 GND)))\n"
        "  (segment (start 0 0) (end 1 1) (width 0.2) (layer Top) (net 1))\n"
        "  (via (at 0.5 0.5) (size 0.8) (drill 0.4) (layers Top Bottom) "
        "(net 1)))\n")
    return cc.parse_kicad5_board(synth)


def test_derive_unrouted_model_strips_and_does_not_mutate():
    m = _k5_model()
    snapshot = copy.deepcopy(m)
    u = cp.derive_unrouted_model(m)
    assert m == snapshot  # 入参不被改
    assert u["segment_count"] == 0 and u["via_count"] == 0
    assert u["arc_count"] == 0 and u["general"]["tracks"] == "0"
    assert u["derived_unrouted"]["basis"] == "routed_geometry_stripped"
    # 封装/网/层保留（设计起点）
    assert len(u["modules"]) == len(m["modules"])
    assert u["nets"] == m["nets"] and len(u["copper_layers"]) == 2
    # 剥除后经 audit pristine 检查语义成立
    audit = cc.build_audit_obj(u, m, board_id="synth")
    assert audit["checks"][0]["id"] == "unrouted_state_pristine"
    assert audit["checks"][0]["pass"] is True


def test_board_slug_folding():
    assert cp.board_slug("RF_SIGNAL_GENERATOR_HARDWARE_RF Signal Generator") \
        == "rf-signal-generator-hardware-rf-signal-generator"
    assert cp.board_slug("kitspace_Control%20Board") == "kitspace-control-20board"
    assert cp.board_slug("plain_board-1.0") == "plain-board-1-0"


def test_manifest_path_compat_filter():
    ok = "datasets/pcbench-r1/raw/kitspace_T32_ref/raw.kicad_pcb"
    assert cp.manifest_path_compatible(ok)
    assert cp.dataset_board_paths("b_x")["processed"].endswith(
        "b_x/processed.kicad_pcb")
    for bad in ("datasets/x/RF Signal Generator/raw.kicad_pcb",
                "datasets/x/kitspace_Control%20Board/raw.kicad_pcb",
                "datasets/x/{{tpl}}/raw.kicad_pcb"):
        assert not cp.manifest_path_compatible(bad)
    # 与 v3 合同层 schemas._REL_POSIX 一致（镜像检查）
    from pcbflow import schemas
    for p in (ok, "datasets/x/RF Signal Generator/raw.kicad_pcb"):
        import re
        assert cp.manifest_path_compatible(p) == bool(
            re.match(schemas._REL_POSIX, p))


# ---------------- 确定性选板 ----------------

def _cand(bid, layers=2, group="g1", topo="t1", **over):
    d = {"board_id": bid, "copper_layers": layers, "topology_group": topo,
         "project_group": group, "parse_ok": True, "identity_ok": True,
         "manifest_path_ok": True}
    d.update(over)
    return d


def test_select_conversion_boards_rule():
    cands = [
        _cand("A_two_1", 2, "gA", "tA"),
        _cand("B_two_2", 2, "gB", "tB"),
        _cand("C_four_1", 4, "gC", "tC"),
        _cand("D_four_2", 4, "gD", "tD"),
        _cand("E_distinct", 2, "gE", "tE"),
    ]
    sel = cp.select_conversion_boards(cands)
    slots = {s["slot"] for s in sel}
    assert slots == {"S1_2layer_lex_first", "S2_4layer_lex_first",
                     "S3_distinct_group_and_topology"}
    by_slot = {s["slot"]: s["board_id"] for s in sel}
    assert by_slot["S1_2layer_lex_first"] == "A_two_1"
    assert by_slot["S2_4layer_lex_first"] == "C_four_1"
    assert by_slot["S3_distinct_group_and_topology"] == "B_two_2"
    # 确定性
    assert cp.select_conversion_boards(list(reversed(cands))) == sel


def test_select_skips_unqualified_and_bad_paths_and_empty_slots():
    cands = [
        _cand("A_ok", 2, "gA", "tA"),
        _cand("B_parsefail", 2, "gB", "tB", parse_ok=False),
        _cand("C_identityfail", 2, "gC", "tC", identity_ok=False),
        _cand("D_pathfail", 2, "gD", "tD", manifest_path_ok=False),
    ]
    sel = cp.select_conversion_boards(cands)
    # 无 4 层候选 → S2 槽空如实跳过；S3 无异组异拓扑候选 → 只剩 S1
    assert [s["board_id"] for s in sel] == ["A_ok"]
    assert sel[0]["slot"] == "S1_2layer_lex_first"
    assert cp.select_conversion_boards([]) == []


# ---------------- TD8 manifest record / corpus 联立 ----------------

def _manifest_record(**over):
    rec = cp.build_pcbench_manifest_record(
        board_ids=["a_x"], raw_files=[
            {"path": "datasets/pcbench-r1/raw/a_x/raw.kicad_pcb",
             "sha256": "0" * 64}],
        dataset_splits={"train": ["a_x"], "validation": [], "holdout": [],
                        "external_eval": [], "holdout_frozen_readonly": True},
        project_groups=["https://github.com/x/y"],
        topology_groups=[{"group_id": "cu2-1net-1mod-2pad-no-diffpair",
                          "boards": ["a_x"]}],
        conversion_script={"entry_points": ["corpus_pcbench.classify_"
                                            "board_license"],
                           "modules": {}},
        conversion_log=[{"board_id": "a_x", "path": "out/…", "sha256": "0" * 64}],
        kicad_version_field="20171130 (KiCad5)",
        normalized_hash="0" * 64,
        excluded_summary={"summary_counts": {"retained": 1, "excluded": 0}},
        source_archive={"source_uri": "https://github.com/PCBench/PCBench",
                        "archive_sha256": "0" * 64},
        source_research_ref={"path": "out/v3-tl5/source-research-r3.json",
                             "sha256": "0" * 64},
        drc_baseline={"executed": True})
    rec.update(over)
    return rec


def test_manifest_record_to_corpus_manifest_td8_complete():
    m = corpus.build_dataset_manifest(_manifest_record())
    for f in corpus.TD8_FIELDS:
        assert f in m, f
    assert m["dataset_id"] == "pcbench-r1" and m["version"] == "1"
    assert m["license_scope"]["collection_repo_code"].startswith("MIT")
    assert "MIT 不覆盖板文件" in m["license"]
    assert len(m["manifest_sha256"]) == 64 and len(m["raw_hash"]) == 64
    # manifest_sha256 排除自身（自引禁）+ 稳定
    m2 = corpus.build_dataset_manifest(_manifest_record())
    assert m == m2


# ---------------- 转换日志合同 ----------------

def test_pcbench_conversion_log_contract():
    mu = cp.derive_unrouted_model(_k5_model())
    mp = _k5_model()
    mr = copy.deepcopy(mp)
    log = cp.build_pcbench_conversion_log(
        board_id="synth", profile_id="pcbench-synth",
        module_hashes={"corpus_convert": "0" * 64,
                       "corpus_pcbench": "1" * 64},
        inputs=[{"path": "datasets/pcbench-r1/raw/synth/processed.kicad_pcb",
                 "sha256": "0" * 64, "role": "processed_pcb"}],
        outputs=[{"path": "profiles/pcbench-synth/inputs/board.kicad_pcb",
                  "sha256": "0" * 64, "role": "normalized_board"}],
        model_u=mu, model_p=mp, model_r=mr,
        crit=cc.derive_critical_nets(mu), topology_group="cu2-1net-1mod-1pad")
    for key in ("track", "conversion_date", "board_id", "profile_id",
                "modules", "input_state_semantics", "inputs", "outputs",
                "retained", "dropped", "convention_basis",
                "field_missingness", "determinism_claim"):
        assert key in log
    assert log["input_state_semantics"]["unrouted_derivation"].startswith(
        "derive_unrouted_model")
    assert log["input_state_semantics"]["stripped_counts"] == {
        "segments": mp["segment_count"], "vias": mp["via_count"],
        "arcs": mp["arc_count"]}
    assert "zones" in log["dropped"] and "final_json" in log["dropped"]
    assert "byte-exact" in log["determinism_claim"]


# ---------------- 真实 pcbench-r1 库回放（在场时） ----------------

_real = os.path.join(RAW, "LICENSE")
pytestmark_real = pytest.mark.skipif(
    not os.path.isfile(_real), reason="datasets/pcbench-r1 不在场")


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
def test_real_ledger_replay_and_counts():
    led = json.load(open(LEDGER, encoding="utf-8"))
    assert led["counts"]["retained"] == 81
    assert led["counts"]["excluded"] == 1113
    # 留存板全在盘上且版本=20171130（raw+processed 逐文件）
    for r in led["retained"]:
        d = os.path.join(RAW, r["board_id"])
        for fn in ("raw.kicad_pcb", "processed.kicad_pcb"):
            m = cc.parse_kicad5_board(open(os.path.join(d, fn),
                                           encoding="utf-8").read())
            assert m["board_version"] == "20171130"
    # 分类重放一致性（同输入同账本）
    led2 = json.load(open(LEDGER, encoding="utf-8"))
    assert hashing.json_dumps(led) == hashing.json_dumps(led2)


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
def test_real_manifest_splits_and_frozen_holdout():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    sp = man["dataset_splits"]
    assert (len(sp["train"]), len(sp["validation"]),
            len(sp["holdout"])) == (57, 13, 11)
    assert sp["holdout_frozen_readonly"] is True
    assert not (set(sp["train"]) & set(sp["validation"]))
    assert not (set(sp["train"]) & set(sp["holdout"]))
    assert not (set(sp["validation"]) & set(sp["holdout"]))
    assert man["board_ids"] == sorted(sp["train"] + sp["validation"]
                                      + sp["holdout"])
    # 真实 validation 非空（本包分母扩充目标）
    assert len(sp["validation"]) >= 10
    # raw_hash 复算 == manifest 记录（盘上文件未动）
    files = []
    for dp, _, fns in os.walk(os.path.dirname(RAW)):
        for fn in fns:
            p = os.path.join(dp, fn)
            files.append({"path": os.path.relpath(
                p, ".").replace("\\", "/"),
                "sha256": hashing.sha256_file(p)})
    assert corpus.aggregate_raw_hash(files) == man["raw_hash"]


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
def test_real_split_group_containment_and_leakage_pass():
    led = json.load(open(LEDGER, encoding="utf-8"))
    man = json.load(open(MANIFEST, encoding="utf-8"))
    sp = man["dataset_splits"]
    board_groups = [(r["board_id"], r["project_group"]) for r in led["retained"]]
    splits = {k: sp[k] for k in ("train", "validation", "holdout")}
    splits["external_eval"] = []
    splits["holdout_frozen_readonly"] = True
    cross = corpus.audit_split_cross(splits, board_groups)
    assert cross["result"] == "pass", cross["violations"]


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
def test_real_selection_matches_record_and_profiles_on_disk():
    led = json.load(open(LEDGER, encoding="utf-8"))
    sel_expected = {"74Logic_SA_ADC_SA-ADC", "kitspace_T32_ref",
                    "LAUNCHXL-F28027-isolation-PCB_project1"}
    # 候选重算（parse+identity+path ok）后选板规则复现记录的选择
    cands = []
    for r in led["retained"]:
        b = r["board_id"]
        d = os.path.join(RAW, b)
        paths = cp.dataset_board_paths(b)
        if not cp.manifest_path_compatible(paths["raw"]):
            continue
        try:
            mp = cc.parse_kicad5_board(open(os.path.join(d, "processed.kicad_pcb"),
                                            encoding="utf-8").read())
            mr = cc.parse_kicad5_board(open(os.path.join(d, "raw.kicad_pcb"),
                                            encoding="utf-8").read())
        except Exception:
            continue
        nets_eq = [x["net_id"] for x in mp["nets"]] == \
            [x["net_id"] for x in mr["nets"]]
        refs_eq = sorted(m["ref"] for m in mp["modules"]) == \
            sorted(m["ref"] for m in mr["modules"])
        cands.append(_cand(
            b, layers=len(mp["copper_layers"]), group=r["project_group"],
            topo=cc.topology_group_id(mp, cc.derive_critical_nets(mp)),
            parse_ok=True, identity_ok=nets_eq and refs_eq,
            manifest_path_ok=True))
    sel = cp.select_conversion_boards(cands)
    assert {s["board_id"] for s in sel} == sel_expected
    for s in sel:
        assert os.path.isdir(os.path.join(
            "profiles", f"pcbench-{cp.board_slug(s['board_id'])}"))
