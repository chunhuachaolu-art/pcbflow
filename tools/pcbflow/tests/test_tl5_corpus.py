"""TL-5 corpus 合同+审计测试（纯函数；TD8/S5）。"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus, hashing


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------- source 调研记录 ----------------

def test_source_research_records_complete():
    for s in corpus.SOURCE_RESEARCH:
        for key in ("source_id", "name", "uri", "content_form",
                    "claimed_scale", "license", "license_scope",
                    "acquisition", "hash_availability", "reachability",
                    "outcome", "outcome_detail"):
            assert key in s, (s.get("source_id"), key)
        assert s["outcome"] in ("get", "not_available", "blocked")


def test_source_research_names_spec_candidates():
    ids = {s["source_id"] for s in corpus.SOURCE_RESEARCH}
    assert {"SRC-PCBWORLD", "SRC-OMNIEDA", "SRC-PCB-BENCH-DIGILAB",
            "SRC-PCBBENCHMARKS"} <= ids


def test_claimed_numbers_not_denominators():
    """规格警告：679/1681/170+ 只能出现在 claimed_scale 字段。"""
    blob = json.dumps(corpus.SOURCE_RESEARCH)
    for s in corpus.SOURCE_RESEARCH:
        assert "denominator" not in json.dumps(s).lower()
    for s in corpus.SOURCE_RESEARCH:
        for num in ("679", "1,681", "1681"):
            if num in json.dumps(s):
                assert num in s["claimed_scale"].replace("1681", "1,681") \
                    or num in s["claimed_scale"]


# ---------------- raw_hash ----------------

def test_aggregate_raw_hash_deterministic_and_order_insensitive():
    files = [{"path": "datasets/x/b.kicad_pcb", "sha256": _sha("b")},
             {"path": "datasets/x/a.kicad_pcb", "sha256": _sha("a")}]
    h1 = corpus.aggregate_raw_hash(files)
    h2 = corpus.aggregate_raw_hash(list(reversed(files)))
    assert h1 == h2 and len(h1) == 64


def test_aggregate_raw_hash_rejects_host_path():
    with pytest.raises(ValueError):
        corpus.aggregate_raw_hash(
            [{"path": r"C:\host\b.kicad_pcb", "sha256": _sha("b")}])


def test_aggregate_raw_hash_rejects_bad_sha_and_dupes():
    with pytest.raises(ValueError):
        corpus.aggregate_raw_hash([{"path": "a", "sha256": "zz"}])
    with pytest.raises(ValueError):
        corpus.aggregate_raw_hash(
            [{"path": "a", "sha256": _sha("1")},
             {"path": "a", "sha256": _sha("2")}])


# ---------------- manifest ----------------

def _record():
    return {
        "dataset_id": "ds-r1", "version": "1",
        "source_uri_or_archive_sha256": _sha("archive"),
        "license": "CC-BY-SA-3.0+/4.0 (per-board)",
        "license_scope": {"redistribution": "allowed_share_alike"},
        "redistribution_allowed": True, "derivative_allowed": True,
        "attribution": True,
        "collection_date": corpus.COLLECTION_DATE,
        "board_ids": ["bm1", "bm11"],
        "revision_ids": ["bm1.unrouted", "bm1.routed"],
        "project_groups": ["g-arduino", "g-adafruit"],
        "consent_or_provenance": "public repo + per-board license.txt",
        "kicad_version": "20171130",
        "dataset_splits": {"train": ["bm1"], "validation": [],
                           "holdout": ["bm11"],
                           "holdout_frozen_readonly": True},
        "raw_files": [
            {"path": "datasets/ds-r1/raw/bm1/f", "sha256": _sha("1")},
            {"path": "datasets/ds-r1/raw/bm11/f", "sha256": _sha("2")}],
        "excluded_boards": [{"board_id": "bm2", "reason": "license_unknown"}],
    }


def test_build_manifest_covers_all_td8_fields():
    m = corpus.build_dataset_manifest(_record())
    assert list(m.keys()) == list(corpus.TD8_FIELDS)
    for k in corpus.TD8_FIELDS:
        assert m[k] != ""  # 无字段静默缺失


def test_build_manifest_hash_excludes_self_and_is_stable():
    m1 = corpus.build_dataset_manifest(_record())
    m2 = corpus.build_dataset_manifest(_record())
    assert m1["manifest_sha256"] == m2["manifest_sha256"]
    body = {k: v for k, v in m1.items() if k != "manifest_sha256"}
    assert m1["manifest_sha256"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(body))


def test_build_manifest_missing_fields_become_not_available():
    m = corpus.build_dataset_manifest(_record())  # 未传 DRC_baseline 等
    assert m["DRC_baseline"] == corpus.NA
    assert m["normalized_hash"] == corpus.NA
    assert m["conversion_script"] == corpus.NA
    assert m["topology_groups"] == corpus.NA


def test_build_manifest_requires_core_keys():
    rec = _record()
    del rec["dataset_splits"]
    with pytest.raises(ValueError):
        corpus.build_dataset_manifest(rec)


def test_build_manifest_rejects_uppercase_dataset_id():
    rec = _record()
    rec["dataset_id"] = "DS-R1"
    with pytest.raises(ValueError):
        corpus.build_dataset_manifest(rec)


# ---------------- 指纹/拓扑 ----------------

def test_content_fingerprint_whitespace_insensitive():
    a = corpus.content_fingerprint("(kicad_pcb\n  (a 1)\n)")
    b = corpus.content_fingerprint("(kicad_pcb (a 1))")
    assert a == b
    assert a != corpus.content_fingerprint("(kicad_pcb (a 2))")


def test_topology_signature_counts_and_net_multiset():
    txt = ('(kicad_pcb (net 0 "") (net 1 "GND") (net 2 "VCC") '
           '(footprint f1 (pad 1 smd)) (segment ...) (via ...))')
    sig = corpus.topology_signature(txt)
    assert sig["net_count"] == 3
    assert sig["footprint_count"] == 1
    assert sig["pad_count"] == 1
    assert sig["via_count"] == 1
    assert sig["segment_count"] == 1
    assert sig["named_net_count"] == 2
    assert sig["net_name_multiset_sha256"] == hashing.sha256_text(
        "GND\nVCC")


def test_topology_signature_distinguishes_multisets():
    s1 = corpus.topology_signature('(net 1 "GND") (net 2 "VCC")')
    s2 = corpus.topology_signature('(net 1 "GND") (net 2 "SIG")')
    assert (s1["net_name_multiset_sha256"]
            != s2["net_name_multiset_sha256"])


# ---------------- 审计 ----------------

def _splits():
    return {"train": ["bm1"], "validation": [], "holdout": ["bm11"],
            "holdout_frozen_readonly": True}


def _groups():
    return [["bm1", "g-arduino"], ["bm11", "g-adafruit"]]


def test_split_cross_pass_and_holdout_frozen():
    r = corpus.audit_split_cross(_splits(), _groups())
    assert r["result"] == "pass"
    assert r["frozen_flags"]["holdout"] is True


def test_split_cross_detects_board_in_two_roles():
    s = _splits()
    s["validation"] = ["bm1"]
    r = corpus.audit_split_cross(s, _groups())
    assert any(v["kind"] == "board_in_multiple_roles" for v in r["violations"])
    assert r["result"] == "fail"


def test_split_cross_detects_group_crossing_holdout():
    groups = [["bm1", "g-x"], ["bm11", "g-x"]]
    r = corpus.audit_split_cross(_splits(), groups)
    assert any(v["kind"] == "group_crosses_holdout_boundary"
               for v in r["violations"])


def test_split_cross_detects_unfrozen_holdout_and_unassigned():
    s = {"train": ["bm1"], "holdout": ["bm11"]}  # 缺 frozen 标志
    r = corpus.audit_split_cross(s, _groups())
    kinds = {v["kind"] for v in r["violations"]}
    assert "holdout_not_frozen" in kinds
    s2 = _splits()
    s2["train"] = []  # bm1 未分配
    r2 = corpus.audit_split_cross(s2, _groups())
    assert any(v["kind"] == "board_unassigned" for v in r2["violations"])


def test_split_cross_rejects_board_without_group():
    s = _splits()
    s["validation"] = ["ghost"]
    r = corpus.audit_split_cross(s, _groups())
    assert any(v["kind"] == "board_without_group" for v in r["violations"])


def test_content_dedup_finds_cross_board_duplicate():
    items = [{"board_id": "bm1", "file_role": "unrouted",
              "content_sha256": "aa" * 32},
             {"board_id": "bm11", "file_role": "unrouted",
              "content_sha256": "aa" * 32},
             {"board_id": "bm7", "file_role": "routed",
              "content_sha256": "bb" * 32}]
    r = corpus.audit_content_dedup(items)
    assert r["duplicate_group_count"] == 1
    assert {m["board_id"] for m in r["duplicate_groups"][0]["members"]} == {
        "bm1", "bm11"}


def test_same_source_variants_flags_cross_board_group():
    items = [{"project_group": "g-adafruit", "board_id": "bm11",
              "revision_id": "r1"},
             {"project_group": "g-adafruit", "board_id": "bm12",
              "revision_id": "r1"}]
    r = corpus.audit_same_source_variants(items)
    assert r["same_group_cross_board"] == {"g-adafruit": ["bm11", "bm12"]}


def test_same_board_multi_revision_recorded_not_hidden():
    items = [{"project_group": "g-a", "board_id": "bm1",
              "revision_id": "unrouted"},
             {"project_group": "g-a", "board_id": "bm1",
              "revision_id": "routed"}]
    r = corpus.audit_same_source_variants(items)
    assert r["same_board_multi_revision"] == {"g-a/bm1":
                                              ["routed", "unrouted"]}
    assert r["same_group_cross_board"] == {}


def test_topology_dedup_groups_identical_topology():
    sig = {"net_count": 3, "footprint_count": 1, "pad_count": 2,
           "net_name_multiset_sha256": _sha("n")}
    r = corpus.audit_topology_dedup(
        [{"board_id": "a", **sig}, {"board_id": "b", **sig},
         {"board_id": "c", **{**sig, "pad_count": 9}}])
    assert r["topology_duplicate_group_count"] == 1
    assert r["topology_duplicate_groups"][0]["board_ids"] == ["a", "b"]


def test_audit_leakage_pass_path():
    r = corpus.audit_leakage(
        _splits(), _groups(),
        content_items=[{"board_id": "bm1", "file_role": "unrouted",
                        "content_sha256": _sha("1")},
                       {"board_id": "bm11", "file_role": "unrouted",
                        "content_sha256": _sha("2")}],
        variant_items=[{"project_group": "g-arduino", "board_id": "bm1",
                        "revision_id": "unrouted"},
                       {"project_group": "g-arduino", "board_id": "bm1",
                        "revision_id": "routed"},
                       {"project_group": "g-adafruit", "board_id": "bm11",
                        "revision_id": "unrouted"}],
        topology_signatures=[
            {"board_id": "bm1", "net_count": 10, "footprint_count": 5,
             "pad_count": 50, "net_name_multiset_sha256": _sha("n1")},
            {"board_id": "bm11", "net_count": 9, "footprint_count": 4,
             "pad_count": 40, "net_name_multiset_sha256": _sha("n2")}])
    assert r["result"] == "pass"
    assert r["split_cross"]["result"] == "pass"
    assert r["same_source_variants"]["variant_flag_count"] == 1  # 同板双 rev


def test_audit_leakage_fail_on_split_violation():
    s = _splits()
    s["holdout_frozen_readonly"] = False
    r = corpus.audit_leakage(s, _groups(), [], [], [])
    assert r["result"] == "fail"


def test_audit_leakage_fail_on_duplicate_content():
    r = corpus.audit_leakage(
        _splits(), _groups(),
        content_items=[{"board_id": "bm1", "file_role": "unrouted",
                        "content_sha256": _sha("x")},
                       {"board_id": "bm11", "file_role": "unrouted",
                        "content_sha256": _sha("x")}],
        variant_items=[], topology_signatures=[])
    assert r["result"] == "fail"


def test_tl5_gate_status_honest_partial():
    assert corpus.TL5_GATE_STATUS == "partial"
    assert corpus.TL5_GATE_BLOCKERS
