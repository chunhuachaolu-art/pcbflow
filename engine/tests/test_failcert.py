# -*- coding: utf-8 -*-
"""failcert.v1：三态合同、跨字段互斥、独立复核器。"""
import copy

import pytest

from fixtures_v2 import build_v2_board
from v5 import failcert
from v5.failcert import CertError, build_unsat_cert, build_unknown_cert, verify
from v5.schema_loader import SchemaViolation


@pytest.fixture()
def prov():
    return build_v2_board()["provenance"]


def test_unsat_cert_builds_and_verifies(prov):
    cert = build_unsat_cert(
        prov, ["P3"],
        [{"constraint": "capacity",
          "data": {"occupancy_terms": [3.3, 0.2, 0.2], "capacity_mm": 4.3},
          "arithmetic": "3.3+0.5+0.2+0.5=4.7 > 4.3"}])
    result = verify(cert)
    assert result["recheck"] == "PASS"
    assert cert["check"]["recheck"] == "PASS"


def test_unsat_requires_core(prov):
    cert = {
        "cert_version": "v5.failcert.v1",
        "board_provenance": prov,
        "status": "UNSAT",
        "scope": {"nets": ["P3"]},
        "unsat_core": [],
        "check": {"procedure": "v5.failcert.verify"},
    }
    with pytest.raises(CertError):
        failcert.validate(cert)


def test_unsat_forbids_unknown_boundary(prov):
    cert = build_unsat_cert(
        prov, ["P3"],
        [{"constraint": "width", "data": {"planned_mm": 0.5, "required_min_mm": 0.8},
          "arithmetic": "0.5<0.8"}])
    cert["unknown_boundary"] = {"achieved": {"nets_connected": 0, "nets_total": 1},
                                "blocked_at": {"description": "x"},
                                "budget": {"consumed": {}, "limit": {}}}
    with pytest.raises(CertError) as ei:
        failcert.validate(cert)
    assert "unknown_boundary" in str(ei.value)


def test_unknown_forbids_unsat_core(prov):
    cert = build_unknown_cert(
        prov, ["P3", "P5"],
        achieved={"nets_connected": 1, "nets_total": 2, "cost": 12.5},
        blocked_at={"description": "C1 走廊协商未收敛"},
        budget={"consumed": {"search_nodes": 1000}, "limit": {"search_nodes": "none"}})
    cert["unsat_core"] = []
    with pytest.raises(CertError) as ei:
        failcert.validate(cert)
    assert "证书欺诈" in str(ei.value) or "unsat_core" in str(ei.value)


def test_unknown_requires_full_boundary(prov):
    cert = build_unknown_cert(prov, ["P5"], achieved={"nets_connected": 0, "nets_total": 1},
                              blocked_at={"description": "x"}, budget={"consumed": {}, "limit": {}})
    del cert["unknown_boundary"]["blocked_at"]
    with pytest.raises((CertError, SchemaViolation)):
        failcert.validate(cert)


def test_verifier_rejects_false_unsat(prov):
    """复核器驳回：声称溢出但重算不成立。"""
    cert = build_unsat_cert(
        prov, ["P3"],
        [{"constraint": "capacity",
          "data": {"occupancy_terms": [0.2, 0.2], "capacity_mm": 4.3},
          "arithmetic": "0.2+0.5+0.2=0.9 > 4.3"}])
    with pytest.raises(CertError) as ei:
        verify(cert)
    assert "复算不成立" in str(ei.value)


def test_verifier_recomputes_width_entry(prov):
    cert = build_unsat_cert(
        prov, ["P8"],
        [{"constraint": "width", "data": {"planned_mm": 0.5, "required_min_mm": 0.8},
          "arithmetic": "0.5 < 0.8"}])
    assert verify(cert)["recheck"] == "PASS"


def test_verifier_rejects_unknown_constraint(prov):
    cert = build_unsat_cert(prov, ["P3"],
                            [{"constraint": "magic", "data": {}, "arithmetic": "?"}])
    with pytest.raises(CertError):
        verify(cert)


def test_unknown_achieved_gt_total_rejected(prov):
    cert = build_unknown_cert(prov, ["P3"],
                              achieved={"nets_connected": 5, "nets_total": 3},
                              blocked_at={"description": "x"}, budget={"consumed": {}, "limit": {}})
    with pytest.raises(CertError):
        verify(cert)


def test_capacity_entry_formula_matches_module(prov):
    terms = [3.3, 0.2, 0.2]
    expected = 3.3 + 0.2 + 0.2 + 0.5 * 2
    assert expected == pytest.approx(4.7)
    cert = build_unsat_cert(
        prov, ["P3", "P5"],
        [{"constraint": "capacity",
          "data": {"occupancy_terms": terms, "capacity_mm": 4.3},
          "arithmetic": "3.3+0.2+0.2+0.5×2=4.7 > 4.3"}])
    assert verify(cert)["recheck"] == "PASS"


def test_cert_bytes_deterministic(prov):
    cert = build_unsat_cert(
        prov, ["P3"],
        [{"constraint": "width", "data": {"planned_mm": 0.5, "required_min_mm": 0.8},
          "arithmetic": "0.5 < 0.8"}])
    assert failcert.cert_bytes(cert) == failcert.cert_bytes(copy.deepcopy(cert))


def test_cert_schema_rejects_unknown_status(prov):
    cert = build_unknown_cert(prov, ["P3"], achieved={"nets_connected": 0, "nets_total": 1},
                              blocked_at={"description": "x"}, budget={"consumed": {}, "limit": {}})
    cert["status"] = "SAT"  # 失败证书不允许 SAT 态
    with pytest.raises(Exception):
        failcert.validate(cert)
