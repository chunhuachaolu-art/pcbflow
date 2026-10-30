"""V4-EXEC-P09 复查发射管线测试（D-7；protocol-r4-review-v1）。

覆盖派发词 §4 要求的四类断言：
- baseline 零覆写守证（输入 baseline_pkg 逐字节不动；复查包为全新对象）；
- hash 链三绑（三个具名 hash + 自引 sha256 重算；与 cmp_patch 口径等值）；
- critic 输出 fail-closed（未知键/自封状态/hash 漂移/未获批 → invalid →
  人工队列）；
- disposition 追加链（human/untrusted、只写处置不写 gate、链校验过）。
"""

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing, ledger, queue  # noqa: E402
from pcbflow import svg_route_package as srp  # noqa: E402
from pcbflow import v4_review_dispatch as vrd  # noqa: E402


# ---------------------------------------------------------------------------
# 最小合成板与几何（零 out/ 依赖）
# ---------------------------------------------------------------------------

def _board():
    return {
        "scenario_id": "cal-f1-13",
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 20.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"clearance_mm": 0.2, "grid_mm": 0.25, "width_mm": 0.3,
                  "allowed_layers": ["F.Cu", "B.Cu"],
                  "via": {"drill_mm": 0.3, "annular_ring_mm": 0.15}},
        "pads": [
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 5.0, "y_mm": 5.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "U2-1", "net_id": "n1", "x_mm": 35.0, "y_mm": 5.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "J1-1", "net_id": "n2", "x_mm": 5.0, "y_mm": 15.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "J2-1", "net_id": "n2", "x_mm": 35.0, "y_mm": 15.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
        ],
        "nets": [
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U2-1"]},
            {"net_id": "n2", "net_class": "default",
             "endpoints": ["J1-1", "J2-1"]},
        ],
        "keepouts": [{"keepout_id": "k1",
                      "rect_mm": [18.0, 8.0, 22.0, 12.0],
                      "layers": ["F.Cu", "B.Cu"]}],
        "relations": [{"relation_id": "rel-001", "relation_type": "bus",
                       "members": ["n1", "n2"]}],
        "label": "fixture",
    }


def _geom_base():
    return {
        "routes": [
            {"route_id": "r1", "net_id": "n1", "layer": "F.Cu",
             "width_mm": 0.3, "state": "candidate", "source": "solver",
             "endpoint_ids": ["U1-1", "U2-1"],
             "polyline_mm": [[5.0, 5.0], [20.0, 5.0], [35.0, 5.0]]},
            {"route_id": "r2", "net_id": "n2", "layer": "F.Cu",
             "width_mm": 0.3, "state": "candidate", "source": "solver",
             "endpoint_ids": ["J1-1", "J2-1"],
             "polyline_mm": [[5.0, 15.0], [20.0, 15.0], [35.0, 15.0]]},
        ],
        "vias": [],
    }


def _geom_candidate():
    geom = copy.deepcopy(_geom_base())
    # r1 改线（末端直角改斜接）；r2 不动；r3 新增；v1 新增过孔
    for r in geom["routes"]:
        if r["route_id"] == "r1":
            r["polyline_mm"] = [[5.0, 5.0], [20.0, 5.0], [34.0, 4.0],
                                [35.0, 5.0]]
    geom["routes"].append(
        {"route_id": "r3", "net_id": "n2", "layer": "B.Cu", "width_mm": 0.3,
         "state": "candidate", "source": "solver",
         "endpoint_ids": ["J1-1", "J2-1"],
         "polyline_mm": [[5.0, 15.0], [20.0, 17.0], [35.0, 15.0]]})
    geom["vias"].append(
        {"via_id": "v1", "net_id": "n2", "parent_id": "r3",
         "from_layer": "F.Cu", "to_layer": "B.Cu",
         "center_mm": [20.0, 17.0], "drill_mm": 0.3,
         "annular_ring_mm": 0.15, "state": "candidate", "source": "solver"})
    return geom


def _baseline_pkg(board, geom=None):
    ref = vrd.enrich_geometry(board, geom if geom is not None
                              else _geom_base(),
                              state=vrd.STATE_UNCHANGED[0],
                              source=vrd.STATE_UNCHANGED[1])
    svg, man = srp.build(board, ref)
    return {"svg_text": svg, "manifest": man}


_REJECTIONS = [
    {"route_id": "r1", "reason_class": "endpoint_moved",
     "reasons": ["endpoint U1-1 moved"]},
    {"route_id": "r3", "reason_class": "keepout_or_collision",
     "reasons": ["keepout k1 collision"]},
]


def _pkg(**kw):
    board = kw.get("board") or _board()
    return vrd.build_review_package(
        board, kw.get("baseline_pkg") or _baseline_pkg(board),
        kw.get("candidate_geom") or _geom_candidate(),
        case_id=kw.get("case_id", "RC-CAL-F1-13"),
        validator_rejections=kw.get("validator_rejections", _REJECTIONS))


# ---------------------------------------------------------------------------
# 复查包生成器：确定性 + 三绑 + diff 内核 + 零覆写
# ---------------------------------------------------------------------------

def test_build_double_run_byte_exact():
    a = _pkg()
    b = _pkg()
    assert a == b  # 全包 canonical 相等（SVG/manifest/summary/PNG hash 绑定）
    board = _board()
    pa = vrd.render_review_package_pngs(board, a)
    pb = vrd.render_review_package_pngs(board, b)
    assert pa["diff_view"] == pb["diff_view"]  # PNG 字节逐字节一致
    assert pa["baseline_view"] == pb["baseline_view"]


def test_three_bind_and_self_hash_roundtrip():
    pkg = _pkg()
    board = _board()
    assert sorted(pkg["three_bind"]) == sorted(vrd.THREE_BIND_KEYS)
    assert pkg["three_bind"]["board_snapshot_sha256"] \
        == pkg["baseline_view"]["manifest"]["board_snapshot_sha256"]
    assert pkg["three_bind"]["parent_manifest_payload_sha256"] \
        == pkg["baseline_view"]["manifest"]["manifest_payload_sha256"]
    assert pkg["three_bind"]["candidate_geometry_sha256"] \
        == vrd.candidate_geometry_sha256(_geom_candidate())
    assert len(pkg["review_package_sha256"]) == 64
    assert vrd.verify_review_package(pkg) == []
    assert vrd.review_package_sha256(pkg) == pkg["review_package_sha256"]


def test_candidate_hash_matches_cmp_patch_contract():
    from pcbflow.v4exp import cmp_patch
    geom = _geom_candidate()
    assert vrd.candidate_geometry_sha256(geom) \
        == cmp_patch.candidate_geometry_sha256(geom)
    # strip_sha 自引键不参与 hash（P0 合同）
    g2 = copy.deepcopy(geom)
    assert vrd.candidate_geometry_sha256(g2) \
        == vrd.candidate_geometry_sha256(geom)


def test_baseline_pkg_not_mutated_append_only():
    board = _board()
    bp = _baseline_pkg(board)
    before = copy.deepcopy(bp)
    _pkg(board=board, baseline_pkg=bp)
    assert bp == before  # 输入零覆写（R7 的纯函数面）
    # 复查包内 baseline 视图与输入逐字节一致（只读引用）
    pkg = _pkg(board=board, baseline_pkg=bp)
    assert pkg["baseline_view"]["svg_text"] == bp["svg_text"]
    assert pkg["baseline_view"]["manifest"] == bp["manifest"]


def test_diff_kernel_counts_and_annotations():
    pkg = _pkg()
    s = pkg["summary"]
    assert s["diff"]["route_changed"] == ["r1"]
    assert s["diff"]["route_added"] == ["r3"]
    assert s["diff"]["route_removed"] == []
    assert s["diff"]["route_unchanged"] == ["r2"]
    assert s["diff"]["via_added"] == ["v1"]
    assert s["counts"]["route_changed"] == 1
    changed = s["changed_objects"][0]
    assert changed["object_id"] == "r1"
    assert changed["old_polyline_mm"] != changed["new_polyline_mm"]
    # diff 视图逐对象标注：changed→candidate/solver、unchanged→baseline、
    # removed→rejected；route_id 恒为真实身份
    man = pkg["diff_view"]["manifest"]
    states = {str(r["route_id"]): (r["state"], r["source"])
              for r in man["routes"]}
    assert states["r1"] == vrd.STATE_CHANGED
    assert states["r2"] == vrd.STATE_UNCHANGED
    assert states["r3"] == vrd.STATE_CHANGED
    # via 的 state/source 不入 manifest（srp._norm_via 合同如此），
    # via 级 diff 三态以 summary 为准
    assert pkg["summary"]["diff"]["via_added"] == ["v1"]
    # 复查摘要含 carrier 段（validator 拒绝记录）
    assert [r["reason_class"] for r in s["validator_rejections"]] \
        == ["endpoint_moved", "keepout_or_collision"]


def test_removed_route_annotated_rejected():
    board = _board()
    cand = _geom_candidate()
    cand["routes"] = [r for r in cand["routes"] if r["route_id"] != "r2"]
    pkg = vrd.build_review_package(
        board, _baseline_pkg(board), cand, case_id="RC-X",
        validator_rejections=None)
    assert pkg["summary"]["diff"]["route_removed"] == ["r2"]
    man = pkg["diff_view"]["manifest"]
    r2 = next(r for r in man["routes"] if str(r["route_id"]) == "r2")
    assert (r2["state"], r2["source"]) == vrd.STATE_REMOVED


def test_validator_rejections_fail_closed():
    bad = [{"route_id": "r1", "reason_class": "made_up_class",
            "reasons": ["x"]}]
    with pytest.raises(ValueError, match="reason_class"):
        _pkg(validator_rejections=bad)
    with pytest.raises(ValueError, match="route_id"):
        _pkg(validator_rejections=[{"reason_class": "other",
                                    "reasons": ["x"]}])
    assert _pkg(validator_rejections=None)["summary"][
        "validator_rejections"] == []


def test_verify_review_package_tamper_detected():
    pkg = _pkg()
    tampered = copy.deepcopy(pkg)
    tampered["summary"]["counts"]["route_changed"] = 99
    errs = vrd.verify_review_package(tampered)
    assert any("review_package_sha256" in e for e in errs)
    stale = copy.deepcopy(pkg)
    errs2 = vrd.verify_review_package(
        stale, expected_three_bind={"board_snapshot_sha256": "0" * 64,
                                    "candidate_geometry_sha256":
                                        pkg["three_bind"][
                                            "candidate_geometry_sha256"],
                                    "parent_manifest_payload_sha256":
                                        pkg["three_bind"][
                                            "parent_manifest_payload_sha256"]})
    assert any("board_snapshot_sha256" in e and "期望不符" in e
               for e in errs2)


# ---------------------------------------------------------------------------
# critic 桥：bundle / raw flags fail-closed / ingest / 定位可回查
# ---------------------------------------------------------------------------

_SHA = "a" * 64


def _files():
    return {role: {"file_rel": f"review-packages/RC/{role}", "sha256": _SHA}
            for role in vrd._BUNDLE_FILE_ROLES}


def _case():
    return {"case_id": "RC-CAL-F1-13", "review_package_sha256": _SHA,
            "three_bind": {k: _SHA for k in vrd.THREE_BIND_KEYS},
            "files": _files()}


def _bundle():
    return vrd.build_review_bundle(run_id="r4-run-1", cases=[_case()],
                                   approval_sha256=_SHA)


_RAW_OK = {
    "reader_id": "blind-reader-r4",
    "per_case": [{
        "case_id": "RC-CAL-F1-13",
        "flags": [{
            "category": "detour_route", "confidence": 0.6,
            "location_evidence": "route r1 末端 45° 斜接段疑似绕远",
            "description": "斜接前后的走向对比", "abstain": False,
        }],
    }],
    "reading_notes": "",
}


def test_bundle_deterministic_and_valid():
    a, b = _bundle(), _bundle()
    assert a == b
    assert vrd.review_bundle_sha256(a) == vrd.review_bundle_sha256(b)
    vrd.validate_review_bundle(a)  # 不抛即合法


def test_raw_flags_contract():
    assert vrd.validate_review_raw_flags(
        _RAW_OK, expected_case_ids=["RC-CAL-F1-13"]) == []
    raw = copy.deepcopy(_RAW_OK)
    raw["critic_status"] = "executed"  # 读者自封状态 → invalid
    errs = vrd.validate_review_raw_flags(raw,
                                         expected_case_ids=["RC-CAL-F1-13"])
    assert any("未知顶层键" in e for e in errs)
    raw2 = copy.deepcopy(_RAW_OK)
    raw2["per_case"][0]["flags"][0]["category"] = "silk_readability"
    errs2 = vrd.validate_review_raw_flags(raw2,
                                          expected_case_ids=["RC-CAL-F1-13"])
    assert any("category" in e for e in errs2)
    raw3 = copy.deepcopy(_RAW_OK)
    raw3["per_case"][0]["flags"][0]["confidence"] = True
    assert vrd.validate_review_raw_flags(raw3,
                                         expected_case_ids=["RC-CAL-F1-13"])
    raw4 = copy.deepcopy(_RAW_OK)
    del raw4["per_case"][0]
    errs4 = vrd.validate_review_raw_flags(raw4,
                                          expected_case_ids=["RC-CAL-F1-13"])
    assert any("缺例" in e for e in errs4)
    raw5 = copy.deepcopy(_RAW_OK)
    raw5["per_case"][0]["flags"][0]["location_evidence"] = ""
    assert vrd.validate_review_raw_flags(raw5,
                                         expected_case_ids=["RC-CAL-F1-13"])


def test_ingest_executed_and_fail_closed():
    bundle = _bundle()
    bsha = vrd.review_bundle_sha256(bundle)
    actual = {"RC-CAL-F1-13:review_package_sha256": _SHA}
    actual.update({f"RC-CAL-F1-13:{role}": _SHA
                   for role in vrd._BUNDLE_FILE_ROLES})
    raw_text = json.dumps(_RAW_OK, ensure_ascii=False)
    out = vrd.ingest_review_run(
        run_id="r4-run-1", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=bsha, actual_hashes=actual, approval_ok=True)
    assert out["critic_status"] == "executed"
    assert out["queue_events"] == []
    assert out["record"]["advisory_only"] is True
    assert out["record"]["flags"][0]["category"] == "detour_route"
    assert out["abstain_count"] == 0
    assert out["raw_flags_sha256"] == hashing.sha256_bytes(
        raw_text.encode("utf-8"))
    # fail-closed：实测 hash 漂移 → invalid → enqueue 人工队列
    actual_bad = dict(actual)
    actual_bad["RC-CAL-F1-13:diff_svg"] = "b" * 64
    out2 = vrd.ingest_review_run(
        run_id="r4-run-1", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=bsha, actual_hashes=actual_bad,
        approval_ok=True)
    assert out2["critic_status"] == "invalid"
    assert out2["queue_events"]
    assert out2["queue_events"][0]["event"] == "enqueue"
    # fail-closed：模型未获批
    out3 = vrd.ingest_review_run(
        run_id="r4-run-1", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=bsha, actual_hashes=actual, approval_ok=False)
    assert out3["critic_status"] == "invalid"
    # fail-closed：sidecar 声明漂移 → ValueError（可信侧）
    with pytest.raises(ValueError, match="sidecar"):
        vrd.ingest_review_run(
            run_id="r4-run-1", bundle=bundle, raw_flags_text=raw_text,
            expected_bundle_sha256="c" * 64, actual_hashes=actual,
            approval_ok=True)
    # fail-closed：raw 文本与盘上不一致
    actual_raw = dict(actual)
    actual_raw["raw_flags"] = "d" * 64
    out4 = vrd.ingest_review_run(
        run_id="r4-run-1", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=bsha, actual_hashes=actual_raw,
        approval_ok=True)
    assert out4["critic_status"] == "invalid"


def test_flag_object_traceability():
    raw = copy.deepcopy(_RAW_OK)
    errs = vrd.flags_object_traceability(
        raw, object_ids_by_case={"RC-CAL-F1-13": {"r1", "r2", "r3", "v1"}})
    assert errs == []
    raw2 = copy.deepcopy(_RAW_OK)
    raw2["per_case"][0]["flags"][0]["location_evidence"] = "图右上角附近"
    errs2 = vrd.flags_object_traceability(
        raw2, object_ids_by_case={"RC-CAL-F1-13": {"r1", "r2"}})
    assert errs2


# ---------------------------------------------------------------------------
# disposition 挂钩：L6（human/untrusted、只写处置、追加链）
# ---------------------------------------------------------------------------

def _disposition(kind, **kw):
    return vrd.build_review_disposition(
        disposition_id=kw.get("disposition_id", "DIS-RC-1"),
        case_id="RC-CAL-F1-13", review_package_sha256=_SHA, kind=kind,
        rationale_code=kw.get("rationale_code", "review-drill"),
        approver=kw.get("approver", "chief-reviewer"),
        approver_role=kw.get("approver_role", "chief_reviewer_drill"),
        rationale_text=kw.get("rationale_text"), flag_refs=["flag:1"])


def test_disposition_kinds_and_gate_write_scan():
    for kind in vrd.REVIEW_DISPOSITION_KINDS:
        rec = _disposition(kind)
        assert rec["kind"] == kind
        assert rec["scope"] == "candidate"
    with pytest.raises(ValueError, match="kind"):
        _disposition("waive")
    # fact_refs 绑定 case + 具名 hash 引用 + 旗标 refs
    rec = _disposition("accept")
    assert "RC-CAL-F1-13" in rec["fact_refs"]
    assert "review-package:" + _SHA in rec["fact_refs"]
    assert "flag:1" in rec["fact_refs"]


def test_disposition_append_chain_auditable():
    pkg = _pkg()
    entries = []
    drills = [("accept", "DIS-RC-A"), ("reject", "DIS-RC-B"),
              ("known_open", "DIS-RC-C")]
    for kind, did in drills:
        rec = vrd.build_review_disposition(
            disposition_id=did, case_id="RC-CAL-F1-13",
            review_package_sha256=pkg["review_package_sha256"], kind=kind,
            rationale_code="review-drill", approver="chief-reviewer",
            approver_role="chief_reviewer_drill", flag_refs=["flag:1"])
        entries, entry = vrd.append_review_disposition(
            entries, disposition=rec, case_id="RC-CAL-F1-13",
            three_bind=pkg["three_bind"])
        assert entry["authority"] == "human"
        assert entry["trust_level"] == "untrusted"
        assert entry["entry_kind"] == "disposition"
    assert ledger.verify_chain(entries) == []  # G5：追加链可审计
    # human authority 只允许 disposition 类 entry（TRUST_POLICY 强制）
    bad = dict(entries[-1])
    bad["entry_kind"] = "gate"
    bad.pop("entry_sha256", None)
    bad.pop("ledger_head_sha256", None)
    from pcbflow.ledger import make_entry
    tampered = make_entry(entries[:-1], entry_kind="gate", entry_id="X",
                          schema_validation=ledger.make_schema_validation(
                              "disposition_record"),
                          authority="human", trust_level="observed",
                          candidate_id="RC")
    errs = ledger.verify_chain(entries[:-1] + [tampered])
    assert any("trust_level" in e or "human" in e for e in errs)


def test_disposition_no_gate_write_and_critic_hash_binding():
    pkg = _pkg()
    rec = vrd.build_review_disposition(
        disposition_id="DIS-RC-D", case_id="RC-CAL-F1-13",
        review_package_sha256=pkg["review_package_sha256"],
        kind="reject", rationale_code="flag-backed",
        approver="chief-reviewer", approver_role="chief_reviewer_drill")
    entries, entry = vrd.append_review_disposition(
        [], disposition=rec, case_id="RC-CAL-F1-13",
        three_bind=pkg["three_bind"], critic_record_sha256="e" * 64)
    assert ledger.verify_chain(entries) == []
    assert entry["critic_run_hash"] == "e" * 64
    assert entry["artifact_hashes"] == pkg["three_bind"]
    with pytest.raises(ValueError, match="64-hex"):
        vrd.append_review_disposition([], disposition=rec,
                                      case_id="RC", three_bind=pkg[
                                          "three_bind"],
                                      critic_record_sha256="nope")
