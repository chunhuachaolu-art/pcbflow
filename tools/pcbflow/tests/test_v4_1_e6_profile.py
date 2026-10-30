"""tests/test_v4_1_e6_profile -- G6.3 性能画像格式冻结测试。

依据：任务书 §3 E6 G6.3 + prereg-e6.json g63（先冻结格式再产样例）：
schema 结构/类型/单位/禁 wall-clock 字段/排除核心 hash 的机器证/
采样器确定性（search_nodes 逐次相同；elapsed/memory 允许漂移）。
"""

from __future__ import annotations

import copy
import json
import os

import pytest

from pcbflow.v4_1 import e6profile
from pcbflow.v4_1.e6profile import (PROFILE_SCHEMA, ProfileSchemaError,
                                    core_facts, core_hash,
                                    demo_core_hash_exclusion, make_profile,
                                    sample_e3_solver2, validate_profile)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")
_E6 = os.path.join(_ROOT, "out", "v4.1-engineering", "e6")


def _mk(**over):
    base = {
        "subject": {"kind": "unit", "solver": "test", "scenario_id": "s1",
                    "deterministic_key": "k"},
        "search_nodes": 42, "astar_expanded": 42, "elapsed_s": 1.5,
        "peak_bytes": 1024, "outcome": {"status": "sat"},
    }
    base.update(over)
    return make_profile(**base)


# ---------------------------------------------------------------- schema 冻结

def test_make_profile_valid_and_schema_frozen():
    p = _mk()
    assert p["schema"] == PROFILE_SCHEMA == \
        "pcbflow.v4_1.e6-perf-profile/1"
    assert validate_profile(p) is True


def test_validator_rejects_wrong_schema_version():
    p = _mk()
    p["schema"] = "pcbflow.v4_1.e6-perf-profile/2"
    with pytest.raises(ProfileSchemaError, match="schema"):
        validate_profile(p)


def test_validator_rejects_wall_clock_fields():
    for field in ("timestamp", "evaluated_at", "measured_at", "now"):
        p = _mk()
        p[field] = "2026-09-12T00:00:00"
        with pytest.raises(ProfileSchemaError, match="wall-clock"):
            validate_profile(p)


def test_validator_rejects_bad_types_and_values():
    p = _mk()
    p["search_nodes"] = -1
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["search_nodes"] = 1.5
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["elapsed_s"] = -0.1
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["memory"] = {"method": "x", "peak_bytes": -3}
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["hash_policy"]["enters_core_hash"] = True
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["subject"]["scenario_id"] = ""
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)
    p = _mk()
    p["declared_date"] = "2026-09-13"
    with pytest.raises(ProfileSchemaError):
        validate_profile(p)


def test_canonical_roundtrip_deterministic():
    from pcbflow.v4_1.canonical import dumps_canonical
    p = _mk()
    assert dumps_canonical(json.loads(dumps_canonical(p))) == \
        dumps_canonical(p)


# ---------------------------------------------------------------- hash 排除

def test_core_hash_exclusion_proven():
    record = {"schema": "demo/1", "facts": {"a": 1},
              "evaluation_metadata": {"perf_profile": _mk()}}
    demo = demo_core_hash_exclusion(record)
    assert demo["exclusion_proven"] is True
    assert core_facts(record) == {"schema": "demo/1", "facts": {"a": 1}}


def test_core_hash_insensitive_to_profile_content():
    r1 = {"schema": "d/1", "facts": {"a": 1},
          "evaluation_metadata": {"perf_profile": _mk()}}
    r2 = copy.deepcopy(r1)
    r2["evaluation_metadata"]["perf_profile"]["search_nodes"] = 999999
    assert core_hash(r1) == core_hash(r2)


# ---------------------------------------------------------------- 采样器

def _board(sid):
    path = os.path.join(_CMP, "board-snapshot-%s.json" % sid)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.skipif(_board("dev-f1-01") is None,
                    reason="E3 快照板不在盘")
def test_sample_e3_solver2_deterministic_search_nodes():
    board = _board("dev-f1-01")
    p1 = sample_e3_solver2(board, "dev-f1-01", cost_arm="flat")
    p2 = sample_e3_solver2(board, "dev-f1-01", cost_arm="flat")
    assert p1["search_nodes"] == p2["search_nodes"] > 0
    assert p1["astar_expanded"] == p1["search_nodes"]
    # elapsed/memory 为测量量：只断言合理量级（>=0），不做逐次相等断言
    assert 0.0 <= p1["elapsed_s"] < 3600.0
    assert p1["memory"]["peak_bytes"] > 0
    assert p1["subject"]["kind"] == "e3_solver2_scenario"


@pytest.mark.skipif(_board("dev-f1-01") is None,
                    reason="E3 快照板不在盘")
def test_sample_e3_layered_arm_profiles():
    board = _board("dev-f1-01")
    p = sample_e3_solver2(board, "dev-f1-01", cost_arm="layered")
    assert "layered" in p["subject"]["solver"]
    assert validate_profile(p)


# ---------------------------------------------------------------- 盘上样例对账

def _samples():
    for name in ("profiles-e3.json", "profiles-e4.json"):
        p = os.path.join(_E6, "g63", name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                for prof in json.load(f)["profiles"]:
                    yield prof


@pytest.mark.skipif(not list(_samples()), reason="G6.3 样例未在盘")
def test_disk_samples_all_validate():
    n = 0
    for prof in _samples():
        validate_profile(prof)
        n += 1
    assert n >= 10  # prereg samples_target（>=7）之上的实跑集
