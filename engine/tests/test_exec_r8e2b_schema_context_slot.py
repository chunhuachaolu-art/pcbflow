# -*- coding: utf-8 -*-
"""EXEC-R8-E2B candidate-event.v1 死信槽位修复钉值（context 槽位解锁）。

覆盖面（任务书 §1 R8E2B-0；判据 SF-1..SF-6）：
- 旧合法件仍过：baseline/not_applicable 出口形态与 cert_field_change 全字
  段扩展形态（无 context）修复后 schema 照过（SF-1）；
- 带 candidate_reason_context 新件过：not_applicable 与 cert_field_change
  两形态（SF-2）——原 schema 外层 additionalProperties:false 封死该槽位
  （allOf[1].then 声明而 properties 不含）＝R8-B §3 死信面，本批解锁=
  expected_cert_change.properties 增一行 additive 声明；
- fail-closed：context 非法类型（非 string）必须拒（SF-4）；未知键仍拒
  （additionalProperties:false 面未放宽）；
- 透传零改动：CandidateEventJournal.register 不改 expected_cert_change 原
  字节，event_id 重算含 context 过（SF-5；candidate_events.py 本批零改动）；
- 9 类 typed 拒绝词表静态保留（SF-6）。

自包含夹具（不依赖沙箱）；schema=活树 schemas/candidate-event.v1。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5.canonical import canonical_sha256               # noqa: E402
from v5 import candidate_events as cev                  # noqa: E402

import jsonschema                                        # noqa: E402
import pytest                                            # noqa: E402

SCHEMA = json.load(open(
    os.path.join(ROOT, "schemas", "candidate-event.v1.schema.json"),
    encoding="utf-8"))

REJECTION_9 = (
    "parent_missing", "parent_unverified", "board_mismatch",
    "world_mismatch", "cert_not_available", "cert_unknown", "no_change",
    "unprovable_freedom", "baseline_not_extension",
)


def _validate(event):
    v = jsonschema.Draft7Validator(SCHEMA)
    errs = sorted(v.iter_errors(event), key=lambda e: list(e.path))
    return (not errs), errs


def _admission_baseline():
    return {"decision": "registered_not_extension",
            "reason": "baseline_registered_not_extension",
            "cert_status": "not_applicable",
            "checks": {"parent_event_present": False,
                       "parent_event_verified": False,
                       "board_binding_match": True,
                       "world_binding_match": True,
                       "cert_verified": False,
                       "expected_change_actionable": False}}


def _admission_admitted():
    return {"decision": "admitted", "reason": "all_checks_passed",
            "cert_status": "verified",
            "checks": {"parent_event_present": True,
                       "parent_event_verified": True,
                       "board_binding_match": True,
                       "world_binding_match": True,
                       "cert_verified": True,
                       "expected_change_actionable": True},
            "cert_kind": "blocker_selection", "cert_sha256": "1" * 64}


def _event(reason, ecc, admission, seq=1):
    semantic = {
        "schema_version": "candidate-event.v1",
        "candidate_id": "C-001",
        "candidate_reason": reason,
        "affected_nets": ["N1"],
        "expected_cert_change": ecc,
        "source_fail_event": None,
        "admission": admission,
        "bindings": {"board_sha256": "0" * 64, "world_id": "t-world",
                     "candidate_sha256": "2" * 64},
        "event_seq": seq,
    }
    ev = dict(semantic)
    ev["event_id"] = canonical_sha256(semantic)
    return ev


def _ecc_not_applicable(context=None):
    ecc = {"kind": "not_applicable"}
    if context is not None:
        ecc["candidate_reason_context"] = context
    return ecc


def _ecc_cert_field_change(context=None):
    ecc = {"kind": "cert_field_change", "cert_kind": "blocker_selection",
           "cert_field": "blocker_nets.net_ids",
           "current_value": ["N06", "N07"],
           "proposed_change": {
               "freedom": "route_order_permutation",
               "discrete_value": ["PT-N07", "PT-N06"],
               "prediction_basis": "route_order 前移改变提交序（可复核）",
               "cert_sha256_parent": "1" * 64}}
    if context is not None:
        ecc["candidate_reason_context"] = context
    return ecc


# ------------------------------------------------ SF-1 旧合法件仍过

def test_old_legal_baseline_event_still_valid():
    ev = _event("baseline", _ecc_not_applicable(), _admission_baseline())
    ok, errs = _validate(ev)
    assert ok, errs


def test_old_legal_cert_field_change_event_still_valid():
    ev = _event("cert_extension_route_order", _ecc_cert_field_change(),
                _admission_admitted())
    ok, errs = _validate(ev)
    assert ok, errs


# ------------------------------------------------ SF-2 带 context 新件过

def test_context_slot_valid_not_applicable():
    ev = _event("baseline",
                _ecc_not_applicable(
                    context="engine-exit baseline 登记（context 槽位解锁）"),
                _admission_baseline())
    ok, errs = _validate(ev)
    assert ok, errs


def test_context_slot_valid_cert_field_change():
    ev = _event(
        "cert_extension_route_order",
        _ecc_cert_field_change(
            context="beam depth-1 route_order 域；父证书=blocker_selection"),
        _admission_admitted())
    ok, errs = _validate(ev)
    assert ok, errs


# ------------------------------------------------ SF-4 fail-closed 面

def test_context_wrong_type_rejected():
    ev = _event("baseline", _ecc_not_applicable(context=7),
                _admission_baseline())
    ev["event_id"] = "0" * 64
    ok, _errs = _validate(ev)
    assert not ok


def test_unknown_key_still_rejected():
    ecc = _ecc_not_applicable()
    ecc["mystery_slot"] = "x"
    ev = _event("baseline", ecc, _admission_baseline())
    ev["event_id"] = "0" * 64
    ok, _errs = _validate(ev)
    assert not ok


# ------------------------------------------------ SF-5 透传零改动

def test_journal_register_passes_context_verbatim(tmp_path):
    cand = {"candidate_id": "CB-TEST", "arm": "cert-beam",
            "route_order": ["PT-A", "PT-B"],
            "layer_assignment": {"PT-A": "F.Cu", "PT-B": "F.Cu"},
            "polylines": {}, "generation_trace": []}
    ctx = "beam 注入侧 context 透传钉值"
    j = cev.CandidateEventJournal(
        str(tmp_path / "cand-events.jsonl"),
        bindings={"board_sha256": "0" * 64, "world_id": "t-world"})
    ev, adm = j.register(
        candidate=cand, candidate_reason="baseline",
        affected_nets=["N1"],
        expected_cert_change=_ecc_not_applicable(context=ctx),
        fail_event=None, board_sha256="0" * 64)
    j.close()
    assert adm["decision"] == "registered_not_extension"
    assert ev["expected_cert_change"]["candidate_reason_context"] == ctx
    # event_id 重算含 context（canonical 面覆盖新槽位）
    assert cev.verify_candidate_event(ev)[0]
    ok, errs = _validate(ev)
    assert ok, errs


def test_build_candidate_event_accepts_context_payload():
    ev = cev.build_candidate_event(
        candidate_id="CB-TEST", candidate_reason="cert_extension_edge_order",
        affected_nets=["N1"],
        expected_cert_change={
            "kind": "cert_field_change", "cert_kind": "blocker_selection",
            "cert_field": "blocker_nets.net_ids", "current_value": ["N1"],
            "proposed_change": {
                "freedom": "edge_order_permutation",
                "discrete_value": ["e1", "e0"],
                "prediction_basis": "边序重排（可复核）",
                "cert_sha256_parent": "1" * 64},
            "candidate_reason_context": "edge_order 域注入侧 context"},
        source_fail_event="3" * 64, admission=_admission_admitted(),
        bindings={"board_sha256": "0" * 64, "world_id": "t-world",
                  "candidate_sha256": "2" * 64},
        event_seq=2)
    assert cev.verify_candidate_event(ev)[0]
    ok, errs = _validate(ev)
    assert ok, errs


# ------------------------------------------------ SF-6 九类拒绝词表

def test_rejection_reasons_nine_words_unchanged():
    assert tuple(cev.REJECTION_REASONS) == REJECTION_9
    assert len(cev.REJECTION_REASONS) == 9


def test_freedom_enum_unchanged():
    assert cev.FREEDOMS == ("route_order_permutation",
                            "edge_order_permutation", "layer_assignment")
