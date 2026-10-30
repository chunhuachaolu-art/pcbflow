"""schemas.py 子集验证器与 jsonschema 库交叉验证（偏差 D6 补偿）。

自研验证器是运行时唯一 authority（零依赖纪律）；jsonschema 4.26 仅在
测试侧对同一批实例做一致性对拍——两引擎结论必须一致，分歧即引擎缺陷。
jsonschema 缺席时 skip（不强加依赖）。
"""

from __future__ import annotations

import pytest

from pcbflow import schemas

jsonschema = pytest.importorskip("jsonschema")

V3 = "3.0"


def _gate_record_ok():
    return {
        "schema_version": V3, "gate_id": "TL-0-G1",
        "gate_kind": "training_loop", "project_id": "smoke-2l",
        "profile_id": "smoke-2l", "snapshot_revision": "smoke-r1",
        "predicate_version": "pv1",
        "inputs": [{"artifact_id": "constraints", "sha256": "0" * 64,
                    "status": "present"}],
        "required_predicates": [{"id": "schema_valid", "value": True,
                                 "evidence": "validator 3.0"}],
        "fact_refs": [], "disposition_refs": [],
        "cycle_check": {"acyclic": True, "topological_order": ["a", "b"]},
        "result": "pass", "failure_codes": [],
        "evaluator": {"name": "gate", "version": "1.0",
                      "code_sha256": "1" * 64},
        "evaluation_metadata": {"evaluated_at": None, "host": None,
                                "elapsed_s": None},
    }


def _ledger_entry_ok():
    return {
        "schema_version": V3, "entry_seq": 0, "entry_id": "E-0",
        "entry_kind": "proposal", "prev_entry_sha256": None,
        "entry_sha256": "2" * 64, "ledger_head_sha256": "3" * 64,
        "authority": "human", "trust_level": "untrusted",
        "schema_validation": {"schema_name": "proposal_patch",
                              "schema_sha256": "4" * 64, "valid": True},
    }


def _patch_ok():
    return {
        "schema_version": V3, "patch_id": "P-1", "base_revision": "r1",
        "base_artifact_hash": "5" * 64,
        "target_scope": "tuning", "operation_kind": "threshold_candidate",
        "changes": [{"path": "policy/thresholds.json", "op": "set",
                     "value": 3}],
        "preconditions": [], "expected_affected_nodes": ["ff_plan"],
        "rollback_plan": "revert to base revision",
        "proposer_id": "offline-search-1", "rationale": "test",
        "evidence_refs": [], "random_seed": None,
        "determinism_claim": "byte_exact", "execution_allowed": False,
    }


CORPUS = [
    ("gate_record", _gate_record_ok, [
        ("result 非法枚举", lambda o: o.update(result="人为")),
        ("gate_kind 非法", lambda o: o.update(gate_kind="human")),
        ("多余键", lambda o: o.update(approved_by="bob")),
        ("input status 非法", lambda o: o["inputs"][0].update(
            status="present!")),
        ("evaluator 缺 code_sha256",
         lambda o: o["evaluator"].pop("code_sha256")),
    ]),
    ("decision_ledger_entry", _ledger_entry_ok, [
        ("entry_kind 非法", lambda o: o.update(entry_kind="rewrite")),
        ("trust_level 非法", lambda o: o.update(trust_level="approved")),
        ("entry_sha256 非 hex",
         lambda o: o.update(entry_sha256="ZZ" * 32)),
        ("entry_seq 负数", lambda o: o.update(entry_seq=-1)),
    ]),
    ("proposal_patch", _patch_ok, [
        ("execution_allowed=true（const 违例）",
         lambda o: o.update(execution_allowed=True)),
        ("operation_kind 禁类",
         lambda o: o.update(operation_kind="board_write")),
        ("changes 空数组", lambda o: o.update(changes=[])),
        ("base_artifact_hash 短", lambda o: o.update(
            base_artifact_hash="abc")),
    ]),
]


@pytest.mark.parametrize("schema_name,maker,mutations", CORPUS,
                         ids=[c[0] for c in CORPUS])
def test_engine_agrees_with_jsonschema(schema_name, maker, mutations):
    spec = schemas.SCHEMAS[schema_name]
    # 正例：两引擎都必须判合法
    ok_obj = maker()
    assert schemas.validate(schema_name, ok_obj) == []
    assert jsonschema.validate(ok_obj, spec) is None
    # 负例：两引擎都必须判非法
    for label, mutate in mutations:
        obj = maker()
        mutate(obj)
        mine = schemas.validate(schema_name, obj)
        theirs = []
        try:
            jsonschema.validate(obj, spec)
        except jsonschema.ValidationError as exc:
            theirs = [str(exc.message)]
        assert mine, f"{label}: 自研引擎漏判"
        assert theirs, f"{label}: jsonschema 漏判（口径漂移）"


def test_schema_hash_deterministic_and_distinct():
    hs = {name: schemas.schema_hash(name) for name in schemas.SCHEMAS}
    assert len(set(hs.values())) == len(hs)  # 各 schema hash 互异
    assert all(len(h) == 64 for h in hs.values())
    # 同名重算稳定（canonical 序列化）
    assert schemas.schema_hash("gate_record") == hs["gate_record"]


def test_unknown_schema_fail_closed():
    errs = schemas.validate("nonexistent_schema", {"any": 1})
    assert errs and "未知 schema 名" in errs[0]
