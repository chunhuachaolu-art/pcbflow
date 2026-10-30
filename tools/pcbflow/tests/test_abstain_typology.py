"""s60 弃权理由家族分型包测试（development 域事后分析件）——
abstain-typology-r13-r16.json（s60 生成）对 48 件 reader-raw-r13..16
冻结输入的逐旗分型 fail-closed 校验：

- 产物在位+声明常量（declared_date=2026-09-08、disclaimer 事后分析
  四要点）+ anchors 与盘上 48 raw+4 run sha256 逐件实测相等；
- matrix 与 per_flag 独立重算一致（轮×视角×家族、轮合计、grand；
  分母=abstain+non_abstain；cross_check_vs_runs 24 格全等）；
- rubric 五家族+关键词表+优先级裁定说明+disclaimer 在位；逐旗记录
  字段完备（family 五值闭合、matched 命中依据、evidence_excerpt）；
- 输入锚：48 件 raw 文件名全在 anchors；per_flag=132、r16 黑点 12 旗
  全部落 existence_blackdot 且逐实例分布=run-r16 登记格、判正常不入
  r16=2 派次。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing

CAL = os.path.join("out", "v3-tl2", "calibration")
PRODUCT = os.path.join(CAL, "abstain-typology-r13-r16.json")
FAMILIES = ("contact", "existence_blackdot", "existence_other",
            "semantic_confusion", "other")
ROUNDS = ("r13", "r14", "r15", "r16")
VIEWS = ("top", "bottom")

DISCLAIMER_KEY_PHRASES = (
    "development 域事后分析",
    "非校准轮",
    "无字母裁决",
    "不得回写 r13–r16 任何 run/dev-record",
    "判据/阈值/GT 零改动",
)


def _load_product() -> dict:
    with open(PRODUCT, encoding="utf-8") as f:
        return json.load(f)


def test_product_anchors_and_disclaimer():
    doc = _load_product()
    assert doc["kind"] == "abstain_typology_posthoc_r13_r16"
    assert doc["declared_date"] == "2026-09-08"
    assert doc["evaluation_domain"] == "development"
    for phrase in DISCLAIMER_KEY_PHRASES:
        assert phrase in doc["disclaimer"]
    anchors = doc["anchors"]
    assert anchors["raw_count"] == 48 and anchors["run_count"] == 4
    raw_files = sorted(
        f for f in os.listdir(CAL)
        if f.startswith("reader-raw-r1") and f[12:14] in ("13", "14", "15", "16")
        and f.endswith(".txt")
    )
    assert len(raw_files) == 48
    for name in raw_files:
        live = hashing.sha256_file(os.path.join(CAL, name))
        assert anchors["raw_sha256"][name] == live
    for r in ROUNDS:
        name = f"calibration-run-{r}.json"
        live = hashing.sha256_file(os.path.join(CAL, name))
        assert anchors["runs_sha256"][name] == live


def test_matrix_consistent_with_per_flag_recount():
    doc = _load_product()
    per_flag = doc["per_flag"]
    rv = doc["matrix"]["round_view"]
    for rnd in ROUNDS:
        for view in VIEWS:
            key = f"{rnd}|{view}"
            recount = {f: 0 for f in FAMILIES}
            abst = 0
            for pf in per_flag:
                if pf["round"] == rnd and pf["view"] == view:
                    recount[pf["family"]] += 1
                    abst += 1
            e = rv[key]
            assert e["abstain"] == abst
            assert e["families"] == recount
            assert e["flags"] == abst + e["non_abstain"]
            assert abs(e["abstain_rate"] - abst / e["flags"]) < 5e-7
        rt = doc["matrix"]["round_totals"][rnd]
        assert rt["abstain"] == rv[f"{rnd}|top"]["abstain"] + rv[f"{rnd}|bottom"]["abstain"]
        for f in FAMILIES:
            assert rt["families"][f] == (rv[f"{rnd}|top"]["families"][f]
                                         + rv[f"{rnd}|bottom"]["families"][f])
    grand = doc["matrix"]["grand"]
    assert grand["abstain"] == len(per_flag) == 132
    assert grand["flags"] == grand["abstain"] + grand["non_abstain"]
    for f in FAMILIES:
        assert grand["families"][f] == sum(
            doc["matrix"]["round_totals"][r]["families"][f] for r in ROUNDS)
    cc = doc["cross_check_vs_runs"]
    assert len(cc) == 24
    assert all(entry["equal"] is True for entry in cc.values())


def test_rubric_disclaimer_and_per_flag_wellformed():
    doc = _load_product()
    rubric = doc["rubric"]
    assert set(rubric["families"]) == set(FAMILIES)
    assert rubric["priority_as_registered"] == list(FAMILIES)
    assert "r16 已知 12 黑点旗" in rubric["priority_adjudication_note"]
    kt = rubric["keyword_tables"]
    for key in ("blackdot_terms", "uncertainty_terms", "contact_terms",
                "contact_doubt_patterns", "text_primary_terms",
                "explicit_existence_terms", "semantic_terms",
                "generic_existence_patterns"):
        assert kt[key], f"keyword table {key} 不得为空"
    assert rubric["unit"].startswith("abstain=true")
    assert rubric["basis"].startswith("location_evidence")
    for pf in doc["per_flag"]:
        for key in ("round", "view", "board", "instance", "source_file",
                    "flag_id", "category", "family", "matched",
                    "evidence_excerpt"):
            assert key in pf, f"per_flag 缺字段 {key}"
        assert pf["family"] in FAMILIES
        assert pf["matched"], "每旗必须附命中依据"
        assert pf["evidence_excerpt"].strip()
        assert pf["round"] in ROUNDS and pf["view"] in VIEWS
    assert doc["findings"]["q3_contact_vs_existence_axis_evidence"].count("不替用户拍板") >= 1


def test_inputs_anchored_and_r16_blackdot_expectation():
    doc = _load_product()
    assert set(doc["anchors"]["raw_sha256"]) == set(
        f for f in os.listdir(CAL)
        if f.startswith("reader-raw-r1") and f[12:14] in ("13", "14", "15", "16")
        and f.endswith(".txt"))
    per_flag = doc["per_flag"]
    assert len(per_flag) == 132
    r16_bd = [pf for pf in per_flag
              if pf["round"] == "r16" and pf["family"] == "existence_blackdot"]
    assert len(r16_bd) == 12
    dist = {}
    for pf in r16_bd:
        key = f"{pf['view']}-{pf['instance']}"
        dist[key] = dist.get(key, 0) + 1
    expected = {"bottom-i1": 3, "bottom-i2": 4, "bottom-i3": 3,
                "top-i1": 1, "top-i2": 1, "top-i3": 0}
    assert all(dist.get(k, 0) == v for k, v in expected.items())
    assert sum(dist.values()) == 12
    bdd = doc["blackdot_dispatch"]
    assert len(bdd["r16"]["judged_normal_dispatches"]) == 2
    assert len(bdd["r16"]["abstain_flag_dispatches"]) == 8
    assert bdd["r15"]["judged_normal_dispatches"] and not bdd["r13"]["judged_normal_dispatches"]
