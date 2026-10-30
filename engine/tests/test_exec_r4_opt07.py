# -*- coding: utf-8 -*-
"""EXEC-R4-B OPT-07 失败/候选双契约回归（正负向；GATE-G1 R4B-03/04/05/08）。

覆盖面：
- fail-event.v1/candidate-event.v1 schema 严格性（required/additionalProperties:
  false/enum；正例过、负例拒）；
- event_id 语义重算（canonical payload − {event_id, runtime}）与 tamper 拒绝；
- 容量证书算术独立复核（terms 复算 occupancy；cert_sha256 绑定）；
- e2e：迷你走廊容量板 opt-in 失败事件（net_exhausted+candidate_failed、
  容量证书 verified、blocker 已计算选择集）→ 准入门正向（有证书候选真正获准
  并实跑核操纵）→ 负向（无证书/错绑/无变化/父缺失/父损坏全拒）；
- baseline 登记=registered_not_extension（不算证书扩展）；
- opt-in 开/关 canonical bytes 零回退（健康板同输入双态对比）；
- sealed/fixed-shape/终检发射器单元（payload/verifier/schema）。

合成夹具登记：本文件 _build_mini_corridor_board（capacity 档参数化）/
_build_mini_healthy_board——builder=本测试文件，产出 board hash 由
compute_board_sha256 程序化计算入断言（R4B-07 合成 fixture 口径）。
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
from v5.executor import execute_candidate               # noqa: E402
from v5 import failure_events as fev                    # noqa: E402
from v5 import candidate_events as cev                  # noqa: E402

import jsonschema                                        # noqa: E402

SCHEMA_DIR = os.path.join(ROOT, "schemas")
FAIL_SCHEMA = json.load(open(
    os.path.join(SCHEMA_DIR, "fail-event.v1.schema.json"), encoding="utf-8"))
CAND_SCHEMA = json.load(open(
    os.path.join(SCHEMA_DIR, "candidate-event.v1.schema.json"),
    encoding="utf-8"))

TEST_WORLD_ID = "r4b-test-world"


# ---------------------------------------------------------------- 合成夹具

def _mini_corridor_board(capacity_mm):
    """迷你走廊容量板：两水平网全高穿越唯一 corridor；capacity<0.9 时第二网
    capacity-locked 耗尽（0.2+0.5+0.2>capacity），首网已提交在账。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "r4b-mini-corridor",
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
                       "source_uri": "tests/test_exec_r4_opt07.py",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def _mini_candidate(board):
    return {"candidate_id": "C-R4B-MINI", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": sorted(p["partition_id"]
                                  for p in board["partitions"]),
            "layer_assignment": {p["partition_id"]: "F.Cu"
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


def _run_with_events(board, cand, tmp_path, tag, world=TEST_WORLD_ID):
    """开 opt-in 跑一次；返回 (result, events[dict 列表])。"""
    journal = os.path.join(str(tmp_path), "fail-events-%s.jsonl" % tag)
    os.environ[fev.ENV_FAIL_EVENTS] = journal
    os.environ["V5_OPT09_WORLD_ID"] = world
    try:
        result = execute_candidate(copy.deepcopy(board),
                                   copy.deepcopy(cand))
    finally:
        os.environ.pop(fev.ENV_FAIL_EVENTS, None)
        os.environ.pop("V5_OPT09_WORLD_ID", None)
    events = []
    if os.path.exists(journal):
        with open(journal, encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()
                      and not line.strip().startswith('{"note"')]
    return result, events


def _result_semantic_core(result):
    """完整语义核心（routes/result/per_net/negotiation_log canonical 面）。"""
    return canonical_sha256({
        k: result[k] for k in ("verdict", "routes", "per_net",
                               "negotiation_log") if k in result})


# ---------------------------------------------------------------- schema 严格性

def _example_fail_event():
    return fev.build_fail_event(
        fail_kind="net_exhausted", scope="net", stage="attempt_ladder_ripup",
        attempts=7, cause="capacity-locked（测试例）",
        geom_secondary="open",
        blocker_nets=fev.build_blocker_not_available("测试例：未测量"),
        available_layers={"kind": "stackup_signal_available",
                          "layers": ["F.Cu"], "source": "测试例"},
        tried_layers=fev.build_tried_layers_not_available(),
        topology=fev.build_topology([[1.0, 2.0], [9.0, 2.0]], [], False,
                                    "not_computed_candidate_scope",
                                    partition_id="PT-A", net_id="N1"),
        capacity_cert={"status": "not_available", "authority": "测试例",
                       "scope": "测试例", "units": "mm", "corridors": [],
                       "cert_sha256": None, "cross_check": "not_available",
                       "reason": "测试例：无 corridor"},
        bindings={"executor_version": "v5.executor/test",
                  "board_id": "b", "board_sha256": None,
                  "routes_schema_version": "v5.routes.v1",
                  "candidate_sha256": None, "geometry_semantics": {},
                  "world_id": TEST_WORLD_ID, "state_sha256": None,
                  "parent_fail_event_id": None, "routes_sha256": None},
        event_seq=1)


def test_fail_event_schema_strict():
    ev = _example_fail_event()
    jsonschema.Draft7Validator(FAIL_SCHEMA).validate(ev)
    bad = copy.deepcopy(ev)
    del bad["cause"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(FAIL_SCHEMA).validate(bad)
    bad = copy.deepcopy(ev)
    bad["extra_key"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(FAIL_SCHEMA).validate(bad)
    bad = copy.deepcopy(ev)
    bad["fail_kind"] = "bogus"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(FAIL_SCHEMA).validate(bad)


def test_candidate_event_schema_strict():
    ev = cev.build_candidate_event(
        candidate_id="C-1", candidate_reason="baseline", affected_nets=[],
        expected_cert_change={"kind": "not_applicable"},
        source_fail_event=None,
        admission={"decision": "registered_not_extension",
                   "reason": "baseline_registered_not_extension",
                   "cert_status": "not_applicable",
                   "checks": {"parent_event_present": True,
                              "parent_event_verified": True,
                              "board_binding_match": True,
                              "world_binding_match": True,
                              "cert_verified": False,
                              "expected_change_actionable": False}},
        bindings={"board_sha256": None, "world_id": TEST_WORLD_ID,
                  "candidate_sha256": None},
        event_seq=1)
    jsonschema.Draft7Validator(CAND_SCHEMA).validate(ev)
    bad = copy.deepcopy(ev)
    bad["candidate_reason"] = "bogus"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(bad)
    bad = copy.deepcopy(ev)
    bad["extra"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(bad)


# ---------------------------------------------------------------- event_id/verifier

def test_event_id_recompute_and_tamper():
    ev = _example_fail_event()
    ok, errors = fev.verify_fail_event(
        ev, expected_bindings={"world_id": TEST_WORLD_ID})
    assert ok, errors
    tampered = copy.deepcopy(ev)
    tampered["attempts"] = 99
    ok, errors = fev.verify_fail_event(tampered)
    assert not ok and any("event_id" in e for e in errors)
    # runtime 字段不入 event_id：加 runtime 不影响重算
    with_runtime = copy.deepcopy(ev)
    with_runtime["runtime"] = {"wall_t": "t", "mono_t": 0.1, "pid": 1,
                               "process_identity": {}, "event_seq_written": 1}
    ok, errors = fev.verify_fail_event(with_runtime)
    assert ok, errors


def test_capacity_cert_arithmetic_verified_and_tampered():
    cert = {"status": "verified", "authority": "t", "scope": "t",
            "units": "mm",
            "corridors": [{"corridor_layer_id": "COR/F.Cu",
                           "capacity_mm": 0.65, "terms": [0.2],
                           "occupancy_mm": 0.2, "spacing_mm": 0.5,
                           "arithmetic": "t", "entries_count": 1}],
            "cert_sha256": None, "cross_check": "agree"}
    cert["cert_sha256"] = canonical_sha256(cert["corridors"])
    ev = _example_fail_event()
    ev2 = copy.deepcopy(ev)
    ev2["capacity_cert"] = cert
    ev2["event_id"] = canonical_sha256(
        {k: v for k, v in ev2.items() if k not in ("event_id", "runtime")})
    ok, errors = fev.verify_fail_event(ev2)
    assert ok, errors
    tampered = copy.deepcopy(ev2)
    tampered["capacity_cert"]["corridors"][0]["terms"] = [0.2, 0.2]
    ok, errors = fev.verify_fail_event(tampered)
    assert not ok  # 算术复核或 event_id 复算至少一项拒


# ---------------------------------------------------------------- e2e 正负向

def test_e2e_net_exhausted_cert_and_gate_positive(tmp_path):
    board = _mini_corridor_board(0.65)
    cand = _mini_candidate(board)
    result, events = _run_with_events(board, cand, tmp_path, "base")
    assert result["verdict"] == "FAILED"
    kinds = [e["fail_kind"] for e in events]
    assert "net_exhausted" in kinds and "candidate_failed" in kinds
    net_ev = next(e for e in events if e["fail_kind"] == "net_exhausted")
    close_ev = next(e for e in events if e["fail_kind"] == "candidate_failed")
    # 全事件过 schema+verifier+绑定核对
    board_sha = net_ev["bindings"]["board_sha256"]
    for e in events:
        jsonschema.Draft7Validator(FAIL_SCHEMA).validate(e)
        ok, errors = fev.verify_fail_event(
            e, expected_bindings={"board_sha256": board_sha,
                                  "world_id": TEST_WORLD_ID})
        assert ok, errors
    # 收口事件 parent=网级事件
    assert close_ev["bindings"]["parent_fail_event_id"] == \
        net_ev["event_id"]
    # 容量证书 verified：走廊×层容量+占用+算术+hash
    cert = net_ev["capacity_cert"]
    assert cert["status"] == "verified"
    assert cert["corridors"] and cert["cert_sha256"]
    assert cert["corridors"][0]["corridor_layer_id"] == "COR/F.Cu"
    # blocker=已计算选择集（measured=true；本夹具首网在走廊内→非空）
    blk = net_ev["blocker_nets"]
    assert blk["kind"] == "computed_selection" and blk["measured"] is True
    assert blk["net_ids"]  # PT-A 铜在失败走廊带/逃逸盘内
    # available_layers=真实 stackup；不取失败条目 layers=[]
    assert net_ev["available_layers"]["layers"] == ["F.Cu"]
    assert net_ev["tried_layers"]["kind"] == "not_available"
    assert net_ev["topology"]["edges_computed"] is True

    # ---- 准入门：baseline 登记 + 正向获准 + 实跑核操纵 ----
    journal = cev.CandidateEventJournal(
        os.path.join(str(tmp_path), "cand-events.jsonl"),
        bindings={"board_sha256": board_sha, "world_id": TEST_WORLD_ID})
    base_cand = copy.deepcopy(cand)
    keys_before = sorted(base_cand)
    ev_base, adm_base = journal.register(
        candidate=base_cand, candidate_reason="baseline",
        affected_nets=[], expected_cert_change={"kind": "not_applicable"},
        fail_event=None, board_sha256=board_sha)
    assert adm_base["decision"] == "registered_not_extension"
    assert sorted(base_cand) == keys_before  # 不给原候选载荷强塞键

    swapped = copy.deepcopy(cand)
    swapped["route_order"] = list(reversed(cand["route_order"]))
    ev_ext, adm_ext = journal.register(
        candidate=swapped, candidate_reason="cert_extension_route_order",
        affected_nets=["N1", "N2"],
        expected_cert_change={
            "kind": "cert_field_change", "cert_kind": "blocker_selection",
            "cert_field": "blocker_nets.net_ids",
            "current_value": list(blk["net_ids"]),
            "proposed_change": {
                "freedom": "route_order_permutation",
                "discrete_value": ["N2"],
                "prediction_basis": "route_order 逆转改变提交序→先布网换为"
                                    "N2、失败网换为 N1，blocker 选择集随之"
                                    "改变（同板同候选字段仅序异的确定性复跑"
                                    "可核）",
                "cert_sha256_parent": net_ev["event_id"]}},
        fail_event=net_ev, board_sha256=board_sha)
    assert adm_ext["decision"] == "admitted", adm_ext
    journal.close()
    for e in (ev_base, ev_ext):
        jsonschema.Draft7Validator(CAND_SCHEMA).validate(e)
        ok, errors = cev.verify_candidate_event(
            e, expected_bindings={"world_id": TEST_WORLD_ID})
        assert ok, errors
    # 实跑核操纵：置换候选真实执行，blocker/证书状态实测变化
    res2, events2 = _run_with_events(board, swapped, tmp_path, "swap")
    net_ev2 = next(e for e in events2 if e["fail_kind"] == "net_exhausted")
    assert res2["verdict"] == "FAILED"   # 容量不变：仍一进一拒
    assert net_ev2["blocker_nets"]["net_ids"] != blk["net_ids"]
    assert net_ev2["capacity_cert"]["corridors"][0]["terms"] == \
        cert["corridors"][0]["terms"]   # 容量事实不变（同前证一致）
    # 汇总：1 登记 baseline、1 准入
    counts = cev.summarize(os.path.join(str(tmp_path), "cand-events.jsonl"))
    assert counts["registered"] == 2
    assert counts["admitted"] == 1
    assert counts["registered_not_extension"] == 1


def test_gate_negative_fixtures(tmp_path):
    board = _mini_corridor_board(0.65)
    cand = _mini_candidate(board)
    result, events = _run_with_events(board, cand, tmp_path, "neg")
    net_ev = next(e for e in events if e["fail_kind"] == "net_exhausted")
    board_sha = net_ev["bindings"]["board_sha256"]

    def ext(change=None, fail_event="pass", board="pass", reason=None):
        ecc = {"kind": "cert_field_change", "cert_kind": "blocker_selection",
               "cert_field": "blocker_nets.net_ids",
               "current_value": list(net_ev["blocker_nets"]["net_ids"]),
               "proposed_change": {
                   "freedom": "route_order_permutation",
                   "discrete_value": list(
                       reversed(net_ev["blocker_nets"]["net_ids"])),
                   "prediction_basis": "同板仅序异复跑可核",
                   "cert_sha256_parent": net_ev["event_id"]}}
        if change:
            ecc.update(change)
        adm = cev.evaluate_admission(
            fail_event=(net_ev if fail_event == "pass" else fail_event),
            candidate_reason=reason or "cert_extension_route_order",
            expected_cert_change=ecc,
            board_sha256=(board_sha if board == "pass" else board),
            world_id=TEST_WORLD_ID)
        return adm

    assert ext(fail_event=None)["reason"] == "parent_missing"
    tampered = copy.deepcopy(net_ev)
    tampered["attempts"] = tampered["attempts"] + 1
    assert ext(fail_event=tampered)["reason"] == "parent_unverified"
    assert ext(board="deadbeef" * 8)["reason"] == "board_mismatch"
    # 错世界：换 world_id 的事件
    other_world = copy.deepcopy(net_ev)
    other_world["bindings"]["world_id"] = "other-world"
    other_world.pop("event_id", None)
    other_world["event_id"] = canonical_sha256(
        {k: v for k, v in other_world.items()
         if k not in ("event_id", "runtime")})
    assert ext(fail_event=other_world)["reason"] == "world_mismatch"
    # 无变化：discrete_value == current_value
    assert ext(change={
        "proposed_change": {"freedom": "route_order_permutation",
                            "discrete_value": list(
                                net_ev["blocker_nets"]["net_ids"]),
                            "prediction_basis": "无变化负例",
                            "cert_sha256_parent": net_ev["event_id"]}}
    )["reason"] == "no_change"
    # 自由度不可证明：prediction_basis 缺失
    assert ext(change={
        "proposed_change": {"freedom": "route_order_permutation",
                            "discrete_value": [],
                            "prediction_basis": "",
                            "cert_sha256_parent": net_ev["event_id"]}}
    )["reason"] == "unprovable_freedom"
    # 无证书：not_available 容量+not_available blocker 的失败事件
    no_cert = _example_fail_event()
    no_cert["bindings"]["board_sha256"] = board_sha
    no_cert["bindings"]["world_id"] = TEST_WORLD_ID
    no_cert.pop("event_id", None)
    no_cert["event_id"] = canonical_sha256(
        {k: v for k, v in no_cert.items()
         if k not in ("event_id", "runtime")})
    adm = cev.evaluate_admission(
        fail_event=no_cert,
        candidate_reason="cert_extension_route_order",
        expected_cert_change={
            "kind": "cert_field_change", "cert_kind": "capacity_ledger",
            "cert_field": "corridor_occupancy",
            "current_value": 0,
            "proposed_change": {
                "freedom": "layer_assignment", "discrete_value": "B.Cu",
                "prediction_basis": "负例", "cert_sha256_parent": "0" * 64}},
        board_sha256=board_sha, world_id=TEST_WORLD_ID)
    assert adm["reason"] == "cert_not_available"


def test_optin_on_off_canonical_zero_regression(tmp_path):
    board = _mini_corridor_board(1.2)   # 健康档：两网均布通
    cand = _mini_candidate(board)
    os.environ.pop(fev.ENV_FAIL_EVENTS, None)
    off = execute_candidate(copy.deepcopy(board), copy.deepcopy(cand))
    journal = os.path.join(str(tmp_path), "fail-events-healthy.jsonl")
    os.environ[fev.ENV_FAIL_EVENTS] = journal
    os.environ["V5_OPT09_WORLD_ID"] = TEST_WORLD_ID
    try:
        on = execute_candidate(copy.deepcopy(board), copy.deepcopy(cand))
    finally:
        os.environ.pop(fev.ENV_FAIL_EVENTS, None)
        os.environ.pop("V5_OPT09_WORLD_ID", None)
    assert off["verdict"] == on["verdict"] == "ROUTED"
    assert _result_semantic_core(off) == _result_semantic_core(on)
    # 健康板零失败事件
    lines = []
    if os.path.exists(journal):
        with open(journal, encoding="utf-8") as f:
            lines = [l for l in f.read().splitlines() if l.strip()]
    assert lines == []


# ---------------------------------------------------------------- 发射器单元

def test_sealed_fixedshape_finalcheck_emitters(tmp_path):
    board = _mini_corridor_board(0.65)
    from v5.executor import _Context
    ctx = _Context(board)
    journal = fev.FailEventJournal(
        os.path.join(str(tmp_path), "fail-events-unit.jsonl"),
        bindings={"executor_version": "v5.executor/test",
                  "board_id": board["board_id"],
                  "board_sha256": compute_board_sha256(board),
                  "routes_schema_version": "v5.routes.v1",
                  "candidate_sha256": "0" * 64, "geometry_semantics": {}})
    try:
        journal.emit_sealed_short_circuit(
            ctx, "PT-A", "N1", 0.2, 0, ["fixed:PT-C"], 8, 8)
        journal.emit_fixed_shape_failed(ctx, "PT-A", "N1", "ribbon")
        journal.emit_final_check_infeasible(
            ctx, 5, "final route_check infeasible: 1 项归责违例（测试）",
            {"COR/F.Cu": {"terms": [0.2, 0.2], "capacity_mm": 0.65}},
            {"schema_version": "v5.routes.v1", "routes": []})
        journal.emit_candidate_failed_close(ctx, "final-check-infeasible", 5)
    finally:
        journal.close()
    events = []
    with open(journal.path, encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]
    kinds = [e["fail_kind"] for e in events]
    assert kinds == ["sealed_short_circuit", "fixed_shape_failed",
                     "final_check_infeasible", "candidate_failed"]
    sealed = events[0]
    assert sealed["blocker_nets"]["kind"] == "geometric_blocking_evidence"
    assert sealed["topology"]["edge_order_source"] == "not_computed_preflight"
    final = events[2]
    assert final["capacity_cert"]["status"] == "verified"
    assert final["capacity_cert"]["authority"].startswith("v5.route_check")
    assert final["bindings"]["routes_sha256"] is not None
    assert events[3]["bindings"]["parent_fail_event_id"] == \
        events[2]["event_id"]
    for e in events:
        jsonschema.Draft7Validator(FAIL_SCHEMA).validate(e)
        ok, errors = fev.verify_fail_event(e)
        assert ok, errors
    # 空容量证书（无 corridor 板）=not_available：不作扩展凭证
    cert = fev.build_capacity_cert_from_ctx(_Context(
        _mini_corridor_board(0.65) if False else board))
    # 上面的 ctx 有 corridor；直接构造无 corridor 板验证 not_available 分支
    no_zone = _mini_corridor_board(1.2)
    no_zone["zones"] = []
    cert2 = fev.build_capacity_cert_from_ctx(_Context(no_zone))
    assert cert2["status"] == "not_available" and cert2["reason"]


def test_summarize_counts(tmp_path):
    p = os.path.join(str(tmp_path), "sum.jsonl")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        adm_rej = {"decision": "rejected", "reason": "cert_not_available",
                   "cert_status": "not_available"}
        adm_ok = {"decision": "admitted", "reason": "all_checks_passed",
                  "cert_status": "verified", "cert_kind": "blocker_selection"}
        for a in (adm_rej, adm_ok, adm_rej):
            ev = {"admission": a}
            f.write(json.dumps(ev, sort_keys=True) + "\n")
    counts = cev.summarize(p)
    assert counts == {"registered": 3, "admitted": 1, "rejected": 2,
                      "registered_not_extension": 0,
                      "rejected_by_reason": {"cert_not_available": 2},
                      "admitted_cert_kinds": {"blocker_selection": 1}}
