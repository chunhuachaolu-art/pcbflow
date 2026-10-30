# -*- coding: utf-8 -*-
"""schema fail-closed：非法样例必须报出具体键路径（P0 门）。"""
import pytest

from v5 import schema_loader
from v5.schema_loader import SchemaViolation, validate

REG = schema_loader.default_registry()
BOARD = schema_loader.load_schema("board.v1.schema.json")
FAILCERT = schema_loader.load_schema("failcert.v1.schema.json")
PRINC = schema_loader.load_schema("principle_registry.v1.schema.json")


def valid_board():
    from fixtures_v2 import build_v2_board
    return build_v2_board()


def test_valid_board_passes():
    validate(valid_board(), BOARD, REG, "")


def test_missing_required_top_reports_path():
    board = valid_board()
    del board["workspace"]
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "workspace" in str(ei.value)


def test_bad_schema_version_reports_path():
    board = valid_board()
    board["schema_version"] = "v4.board"
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "schema_version" in str(ei.value)


def test_bad_enum_stackup_kind():
    board = valid_board()
    board["stackup"][0]["kind"] = "magic"
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "stackup[0].kind" in str(ei.value)


def test_wrong_type_partition_id():
    board = valid_board()
    board["partitions"][2]["partition_id"] = 17
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "partitions[2].partition_id" in str(ei.value)


def test_additional_property_rejected_with_path():
    board = valid_board()
    board["mystery_field"] = 1
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "mystery_field" in str(ei.value)


def test_hash_pattern_enforced():
    board = valid_board()
    board["provenance"]["source_sha256"] = "XYZ"
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "provenance.source_sha256" in str(ei.value)


def test_negative_width_rejected():
    board = valid_board()
    board["partitions"][0]["width_prior"]["w_min"] = -0.1
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "partitions[0].width_prior.w_min" in str(ei.value)


def test_endpoint_pair_cardinality():
    board = valid_board()
    board["partitions"][1]["geometry"]["endpoints"] = [[1.0, 2.0]]
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "partitions[1].geometry.endpoints" in str(ei.value)


def test_no_silent_defaults():
    """fail-closed：缺字段必须报错，绝不静默补默认值。"""
    board = valid_board()
    del board["partitions"][3]["current_a"]
    with pytest.raises(SchemaViolation) as ei:
        validate(board, BOARD, REG, "")
    assert "partitions[3].current_a" in str(ei.value)


# ------------------------------------------------------- failcert schema

def valid_unsat_cert():
    return {
        "cert_version": "v5.failcert.v1",
        "board_provenance": valid_board()["provenance"],
        "status": "UNSAT",
        "scope": {"nets": ["P3"]},
        "unsat_core": [{"constraint": "width", "data": {"planned_mm": 0.5, "required_min_mm": 0.8},
                        "arithmetic": "0.5 < 0.8"}],
        "check": {"procedure": "v5.failcert.verify"},
    }


def test_valid_failcert_passes():
    validate(valid_unsat_cert(), FAILCERT, REG, "")


def test_failcert_bad_status_enum():
    cert = valid_unsat_cert()
    cert["status"] = "MAYBE"
    with pytest.raises(SchemaViolation) as ei:
        validate(cert, FAILCERT, REG, "")
    assert "status" in str(ei.value)


def test_failcert_unknown_extra_field():
    cert = valid_unsat_cert()
    cert["bonus"] = True
    with pytest.raises(SchemaViolation) as ei:
        validate(cert, FAILCERT, REG, "")
    assert "bonus" in str(ei.value)


# ------------------------------------------------------- principle registry schema

def valid_principle():
    import hashlib
    return {
        "principle_id": "P-C1-HS-FIRST",
        "name": "高速网免孔",
        "intent": {"protects": "高速信号完整性（少过孔）", "sacrifices": "低速网的短路径"},
        "scope": "C1 走廊分配",
        "protected_resources": ["C1 走廊容量", "高速网过孔预算"],
        "target_freedom": "allocation",
        "priority": 30,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"predicate": {"ptype": "HS"}, "action": "prefer_f_cu_slot"},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": ["P-C1-LOWCOST"], "yields_to": []},
        "evidence_refs": ["V2 run-03 板底走廊观察"],
        "version": "1.0.0",
        "source_hash": hashlib.sha256(b"seed").hexdigest(),
    }


def test_valid_principle_passes():
    doc = {"principle_registry_version": "v5.principle_registry.v1",
           "principles": [valid_principle()]}
    validate(doc, PRINC, REG, "")


def test_principle_missing_seven_question_field():
    p = valid_principle()
    del p["intent"]["sacrifices"]
    doc = {"principle_registry_version": "v5.principle_registry.v1", "principles": [p]}
    with pytest.raises(SchemaViolation) as ei:
        validate(doc, PRINC, REG, "")
    assert "sacrifices" in str(ei.value)


def test_principle_bad_target_freedom():
    p = valid_principle()
    p["target_freedom"] = "route_level"
    doc = {"principle_registry_version": "v5.principle_registry.v1", "principles": [p]}
    with pytest.raises(SchemaViolation) as ei:
        validate(doc, PRINC, REG, "")
    assert "target_freedom" in str(ei.value)


def test_principle_15_fields_complete():
    p = valid_principle()
    fields = {"principle_id", "name", "intent", "scope", "protected_resources",
              "target_freedom", "priority", "hard_or_soft", "overridable",
              "compiled_rule", "enforcement", "conflict_policy", "evidence_refs",
              "version", "source_hash"}
    assert fields <= set(p.keys()) and len(fields) == 15


def test_ref_resolution_failure_is_error():
    with pytest.raises(schema_loader.SchemaResolutionError):
        validate({}, {"$ref": "no-such.schema.json#/x"}, REG, "")
