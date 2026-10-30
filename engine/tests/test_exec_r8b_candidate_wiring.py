# -*- coding: utf-8 -*-
"""EXEC-R8-B OPT-07 候选出口事件接线回归（executor 级 CandidateEventJournal）。

覆盖面（任务书 §1 R8B-A/R8B-B；判据 JB-5/JB-6/JB-8）：
- env 未设（V5_R4B_CANDIDATE_EVENTS 缺）→ 零侧车文件+双跑 canonical 零差
  （字节级零行为变化的单板同构门）；
- env 已设+FAILED 候选（走廊容量板）→ 恰 1 条出口事件：Draft7 schema 过、
  verify_candidate_event 过、event_id 重算过、baseline 通道
  registered_not_extension、source_fail_event==同跑 fail-event 收口事件 id；
- env 已设+ROUTED 候选（容量放开同板）→ 恰 1 条出口事件、
  source_fail_event=None（健康收口零失败事件）；
- env 开/关同板 canonical 五字段逐对相等（接线零泄漏）；
- schema fail-closed：未知键/非法 candidate_reason 事件必须被 Draft7 拒；
- register_engine_exit(journal=None) → (None, None)（缺 env 常量面）；
- 9 类 typed 拒绝词表静态保留+parent_missing 语义冒烟（准入语义零改动）；
- 原候选载荷不被强塞键。

合成夹具：builder 复制自 tests/test_exec_r4_opt07.py _mini_corridor_board/
_mini_candidate（同口径：capacity<0.9=FAILED、≥0.9=ROUTED）。
板只读；落盘只进 pytest tmp_path。
"""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5.board import load_board, compute_board_sha256   # noqa: E402
from v5.canonical import canonical_sha256               # noqa: E402
from v5.executor import (EXECUTOR_VERSION,               # noqa: E402
                         execute_candidate)
from v5 import failure_events as fev                    # noqa: E402
from v5 import candidate_events as cev                  # noqa: E402

import jsonschema                                        # noqa: E402

SCHEMA_DIR = os.path.join(ROOT, "schemas")
CAND_SCHEMA = json.load(open(
    os.path.join(SCHEMA_DIR, "candidate-event.v1.schema.json"),
    encoding="utf-8"))

TEST_WORLD_ID = "r8b-test-world"


# ---------------------------------------------------------------- 合成夹具
# （复制自 tests/test_exec_r4_opt07.py 同口径；板只读）

def _mini_corridor_board(capacity_mm):
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "r8b-mini-corridor",
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0, "y_max": 6.0},
        "zones": [{"zone_id": "COR", "kind": "corridor",
                   "layers": "signal",
                   "rect": {"x_min": 4.0, "y_min": 0.0,
                            "x_max": 6.0, "y_max": 6.0},
                   "capacity": float(capacity_mm)}],
        "partitions": [
            {"partition_id": "PT-A", "ptype": "MISC", "layer_policy": "F.Cu",
             "planned_width": 0.2, "current_a": 0,
             "geometry": {"endpoints": [[1.0, 2.0], [9.0, 2.0]]},
             "speed_class": "low_speed",
             "width_prior": {"w_min": 0.2, "w_max": 0.4}},
            {"partition_id": "PT-B", "ptype": "MISC", "layer_policy": "F.Cu",
             "planned_width": 0.2, "current_a": 0,
             "geometry": {"endpoints": [[1.0, 3.0], [9.0, 3.0]]},
             "speed_class": "low_speed",
             "width_prior": {"w_min": 0.2, "w_max": 0.4}},
        ],
        "nets": [
            {"net_id": "N1", "net_class": "MISC", "partitions": ["PT-A"]},
            {"net_id": "N2", "net_class": "MISC", "partitions": ["PT-B"]},
        ],
        "hard_rules": {"R1": {"floor_mm": 0.3, "k_a": 0.4},
                       "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
                       "R3": {"unsplittable": True},
                       "R4": {"max_distance_mm": 2.0,
                              "return_via_required": True},
                       "R5": {"min_clearance_mm": 0.5},
                       "R6": {"keepout_zones_forbidden": True,
                              "plane_forbidden": True}},
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_exec_r8b_candidate_wiring.py",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def _mini_candidate(board):
    return {"candidate_id": "C-R8B-MINI", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": sorted(p["partition_id"]
                                  for p in board["partitions"]),
            "layer_assignment": {p["partition_id"]: "F.Cu"
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


def _read_events(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('{"note"'):
                out.append(json.loads(line))
    return out


def _five_fields(out):
    per_net = out.get("per_net", [])
    return {"verdict": out.get("verdict"),
            "ok_nets": sum(1 for pn in per_net
                           if pn.get("status") != "failed"),
            "result_full": canonical_sha256(out),
            "routes_doc": (canonical_sha256(out.get("routes"))
                           if out.get("routes") is not None else None),
            "negotiation_log": canonical_sha256(
                out.get("negotiation_log", []))}


def _run(board, cand, env_pairs):
    saved = {k: os.environ.get(k) for k, _ in env_pairs}
    for k, _ in env_pairs:
        os.environ.pop(k, None)
    for k, v in env_pairs:
        if v is not None:
            os.environ[k] = v
    try:
        return execute_candidate(copy.deepcopy(board),
                                 copy.deepcopy(cand))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---------------------------------------------------------------- env 未设

def test_env_unset_zero_sidecar_and_double_run_canonical_equal(tmp_path):
    board = _mini_corridor_board(0.65)
    cand = _mini_candidate(board)
    for k in (cev.ENV_CANDIDATE_EVENTS, fev.ENV_FAIL_EVENTS,
              "V5_OPT09_WORLD_ID"):
        os.environ.pop(k, None)
    out1 = _run(board, cand, [])
    out2 = _run(board, cand, [])
    assert _five_fields(out1) == _five_fields(out2)   # 双跑字节等
    assert out1["verdict"] == "FAILED"
    # 零侧车文件：candidate/fail 事件面零建盘
    assert not os.path.exists(str(tmp_path / "cand-events.jsonl"))
    assert not os.path.exists(str(tmp_path / "cand-events.jsonl.manifest.json"))


def test_env_unset_journal_from_env_none_and_helper_none_safe(tmp_path):
    for k in (cev.ENV_CANDIDATE_EVENTS, fev.ENV_FAIL_EVENTS):
        os.environ.pop(k, None)
    assert cev.CandidateEventJournal.from_env() is None
    ev, adm = cev.register_engine_exit(
        None, candidate={"candidate_id": "C-X"}, affected_nets=["N1"])
    assert ev is None and adm is None


# ---------------------------------------------------------------- env 已设

def test_env_on_failed_exit_event_full_contract(tmp_path):
    board = _mini_corridor_board(0.65)   # FAILED（capacity 0.65）
    cand = _mini_candidate(board)
    keys_before = sorted(cand)
    cpath = str(tmp_path / "cand-events.jsonl")
    fpath = str(tmp_path / "fail-events.jsonl")
    out = _run(board, cand, [(cev.ENV_CANDIDATE_EVENTS, cpath),
                             (fev.ENV_FAIL_EVENTS, fpath),
                             ("V5_OPT09_WORLD_ID", TEST_WORLD_ID)])
    assert out["verdict"] == "FAILED"
    assert sorted(cand) == keys_before          # 不给原候选强塞键
    events = _read_events(cpath)
    assert len(events) == 1                     # 恰一条出口事件
    ev = events[0]
    jsonschema.Draft7Validator(CAND_SCHEMA).validate(ev)
    ok, errors = cev.verify_candidate_event(
        ev, expected_bindings={"world_id": TEST_WORLD_ID})
    assert ok, errors
    # event_id 语义重算（payload−{event_id,runtime}）
    semantic = {k: v for k, v in ev.items()
                if k not in ("event_id", "runtime")}
    assert canonical_sha256(semantic) == ev["event_id"]
    # baseline 通道（不算证书扩展）+ 新版本戳 + 候选 hash 绑定
    assert ev["candidate_reason"] == "baseline"
    assert ev["admission"]["decision"] == "registered_not_extension"
    assert ev["expected_cert_change"] == {"kind": "not_applicable"}
    assert ev["bindings"]["executor_version"] == EXECUTOR_VERSION
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）
    assert ev["bindings"]["candidate_sha256"] == canonical_sha256(cand)
    assert ev["candidate_id"] == "C-R8B-MINI"
    assert sorted(ev["affected_nets"]) == ["N1", "N2"]
    # 父 fail-event 关联=同跑 fail JSONL 的收口事件 id
    fevents = _read_events(fpath)
    assert fevents, "FAILED 跑 fail-event 面应有事件"
    assert fevents[-1]["fail_kind"] == "candidate_failed"
    assert ev["source_fail_event"] == fevents[-1]["event_id"]
    assert ev["admission"]["checks"]["parent_event_present"] is True
    assert ev["admission"]["checks"]["parent_event_verified"] is False


def test_env_on_routed_exit_event_no_parent(tmp_path):
    board = _mini_corridor_board(0.95)   # ROUTED（capacity ≥0.9）
    cand = _mini_candidate(board)
    cpath = str(tmp_path / "cand-events.jsonl")
    fpath = str(tmp_path / "fail-events.jsonl")
    out = _run(board, cand, [(cev.ENV_CANDIDATE_EVENTS, cpath),
                             (fev.ENV_FAIL_EVENTS, fpath),
                             ("V5_OPT09_WORLD_ID", TEST_WORLD_ID)])
    assert out["verdict"] == "ROUTED"
    events = _read_events(cpath)
    assert len(events) == 1
    ev = events[0]
    jsonschema.Draft7Validator(CAND_SCHEMA).validate(ev)
    ok, errors = cev.verify_candidate_event(ev)
    assert ok, errors
    assert ev["source_fail_event"] is None   # 健康收口零失败事件
    assert ev["admission"]["checks"]["parent_event_present"] is False
    assert _read_events(fpath) == []


def test_env_on_off_canonical_five_fields_equal(tmp_path):
    board = _mini_corridor_board(0.65)
    cand = _mini_candidate(board)
    cpath = str(tmp_path / "cand-events.jsonl")
    off = _run(board, cand, [])
    on = _run(board, cand, [(cev.ENV_CANDIDATE_EVENTS, cpath),
                            ("V5_OPT09_WORLD_ID", TEST_WORLD_ID)])
    assert _five_fields(off) == _five_fields(on)   # 接线零泄漏


# ---------------------------------------------------------------- fail-closed

def test_exit_event_schema_fail_closed(tmp_path):
    board = _mini_corridor_board(0.65)
    cand = _mini_candidate(board)
    cpath = str(tmp_path / "cand-events.jsonl")
    _run(board, cand, [(cev.ENV_CANDIDATE_EVENTS, cpath),
                       ("V5_OPT09_WORLD_ID", TEST_WORLD_ID)])
    ev = _read_events(cpath)[0]
    bad = copy.deepcopy(ev)
    bad["extra_unknown_key"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(bad)
    bad = copy.deepcopy(ev)
    bad["candidate_reason"] = "engine_exit"   # 不在受控词表
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(bad)
    bad = copy.deepcopy(ev)
    bad["bindings"]["geometry_semantics"] = {"v": 1}   # bindings 白名单外
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(bad)


# ---------------------------------------------------------------- 准入语义保留

def test_nine_typed_rejections_static_and_gate_smoke():
    assert cev.REJECTION_REASONS == (
        "parent_missing", "parent_unverified", "board_mismatch",
        "world_mismatch", "cert_not_available", "cert_unknown", "no_change",
        "unprovable_freedom", "baseline_not_extension")
    assert len(cev.REJECTION_REASONS) == 9
    # 冒烟：父缺失仍拒（evaluate_admission 语义零改动）
    adm = cev.evaluate_admission(
        fail_event=None, candidate_reason="cert_extension_route_order",
        expected_cert_change={"kind": "cert_field_change"},
        board_sha256="0" * 64, world_id=TEST_WORLD_ID)
    assert adm["decision"] == "rejected"
    assert adm["reason"] == "parent_missing"
