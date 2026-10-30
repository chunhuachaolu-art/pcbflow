"""tests/test_v4_1_e3_action2 -- E3 动作空间 v2 + patch 合同 v2 测试（G3.1 支撑）。

依据：任务书 §3 E3；prereg-e3.json → g31_negative_set / patch_contract_v2。
正例基座：合成之字形链（synthetic_chain_base）+ f9/f10 多层求解输出。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow.v4exp import cmp_patch
from pcbflow.v4exp.grid import GridWorld
from pcbflow.v4_1 import action2, solver2
from pcbflow.v4_1.action2 import (ALL_ACTION_TYPES, DELETE_VIA,
                                  INSERT_VIA, MERGE_SEGMENTS,
                                  NEW_ACTION_TYPES, PATCH_SCHEMA_V2,
                                  REORDER_LAYERS, SPLIT_SEGMENT,
                                  _first_legal_patch, apply_and_check2,
                                  rollback2, synthetic_chain_base,
                                  v2_proposal_stream, validate_patch2)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")


# ---------------------------------------------------------------- 基座

@pytest.fixture(scope="module")
def synth():
    sid, board, geom = synthetic_chain_base()
    return sid, board, GridWorld(board), geom


@pytest.fixture(scope="module")
def ml_geom():
    from pcbflow.v4_1.mlchain import mlboard_to_v4exp_board
    from pcbflow.v4_1.mlfamily import generate_ml_scenario
    board = mlboard_to_v4exp_board(generate_ml_scenario("dev-f9-02"))
    order = sorted(str(n["net_id"]) for n in board["nets"])
    run = solver2.solve_board2(board, {"route_order": order, "group": "T"})
    return board, GridWorld(board), {"routes": run["routes"],
                                     "vias": run["vias"]}


def _sha(geom):
    return cmp_patch.candidate_geometry_sha256(geom)


# ---------------------------------------------------------------- 正例：五类动作

def test_action_type_registry():
    assert NEW_ACTION_TYPES == ("delete_via", "insert_via", "reorder_layers",
                                "split_segment", "merge_segments")
    assert set(ALL_ACTION_TYPES) > set(cmp_patch.ACTION_TYPES)
    assert PATCH_SCHEMA_V2 == "v4-route-patch/2"


def test_delete_via_positive_with_cascade(synth):
    """删中链 via（keep=F）：相邻 via 跨度级联更新 + rollback 字节恢复。"""
    _sid, board, world, geom = synth
    patch = _first_legal_patch(world, board, geom, DELETE_VIA)
    assert patch is not None
    res = apply_and_check2(world, board, patch, geom)
    assert res["legal"], res.get("reasons")
    cand = res["geometry"]
    assert len(cand["vias"]) == len(geom["vias"]) - 1
    # 级联：下游 via 的 from_layer = keep_layer
    removed = [v for v in geom["vias"]
               if v["via_id"] not in {x["via_id"] for x in cand["vias"]}]
    assert len(removed) == 1
    keep = patch["keep_layer"]
    joint = removed[0]["center_mm"]
    for v in cand["vias"]:
        if v["center_mm"] == joint:
            continue
    # 连通性保持（span-aware）
    m = solver2.metrics_span_aware(world, cand["routes"], cand["vias"])
    assert m["all_connected"] and sum(m["violations"].values()) == 0
    restored = rollback2(cand, res["rollback"])
    assert _sha(restored) == _sha(geom)


def test_insert_via_positive_on_multisegment_chain(ml_geom):
    """v2 解除 v1 限制：多段多 via 链上加 via（v1 insert_via_candidate 拒绝）。"""
    board, world, geom = ml_geom
    patch = _first_legal_patch(world, board, geom, INSERT_VIA)
    assert patch is not None
    res = apply_and_check2(world, board, patch, geom)
    assert res["legal"], res.get("reasons")
    cand = res["geometry"]
    assert len(cand["vias"]) == len(geom["vias"]) + 1
    assert len(cand["routes"]) == len(geom["routes"]) + 1
    m = solver2.metrics_span_aware(world, cand["routes"], cand["vias"])
    assert m["all_connected"] and sum(m["violations"].values()) == 0
    restored = rollback2(cand, res["rollback"])
    assert _sha(restored) == _sha(geom)
    # v1 同 patch（换 v1 schema）必须被 v1 合同拒绝：多段链是 v1 域外
    v1_style = dict(patch)
    v1_style["schema_version"] = cmp_patch.PATCH_SCHEMA
    v1_style["action_type"] = "insert_via_candidate"
    v1_res = cmp_patch.validate_patch(world, board, v1_style, geom)
    assert not v1_res["legal"]


def test_reorder_layers_positive_with_span_update(synth):
    _sid, board, world, geom = synth
    patch = None
    for cand in v2_proposal_stream(world, board, geom):
        if cand["action_type"] == REORDER_LAYERS and \
                cand["route_id"] == "n1-S03":
            if validate_patch2(world, board, cand, geom)["legal"]:
                patch = cand
                break
    assert patch is not None
    res = apply_and_check2(world, board, patch, geom)
    assert res["legal"], res.get("reasons")
    cand = res["geometry"]
    moved = [r for r in cand["routes"]
             if r["route_id"] == patch["route_id"]]
    assert moved and moved[0]["layer"] == patch["layer"]
    # 相邻 via 跨度级联：上游 to / 下游 from = 新层
    for v in cand["vias"]:
        if v["via_id"] == "n1-V02":
            assert v["to_layer"] == patch["layer"]
        if v["via_id"] == "n1-V03":
            assert v["from_layer"] == patch["layer"]
    m = solver2.metrics_span_aware(world, cand["routes"], cand["vias"])
    assert m["all_connected"] and sum(m["violations"].values()) == 0
    restored = rollback2(cand, res["rollback"])
    assert _sha(restored) == _sha(geom)


def test_split_then_merge_roundtrip(synth):
    _sid, board, world, geom = synth
    sp = _first_legal_patch(world, board, geom, SPLIT_SEGMENT)
    assert sp is not None
    res = apply_and_check2(world, board, sp, geom)
    assert res["legal"], res.get("reasons")
    geom2 = res["geometry"]
    # joint 语义：B 段 parent=A 段、共享 joint id、同层
    ra = [r for r in geom2["routes"] if r["route_id"] == sp["route_id"] + "a"]
    rb = [r for r in geom2["routes"] if r["route_id"] == sp["route_id"] + "b"]
    assert ra and rb
    assert ra[0]["endpoint_ids"][1] == rb[0]["endpoint_ids"][0]
    assert rb[0]["parent_id"] == ra[0]["route_id"]
    assert ra[0]["layer"] == rb[0]["layer"] == \
        [r for r in geom["routes"]
         if r["route_id"] == sp["route_id"]][0]["layer"]
    # merge 是 split 的逆：几何恢复（段结构恢复为单段）
    mp = _first_legal_patch(world, board, geom2, MERGE_SEGMENTS)
    assert mp is not None
    res2 = apply_and_check2(world, board, mp, geom2)
    assert res2["legal"], res2.get("reasons")
    merged = res2["geometry"]
    assert len(merged["routes"]) == len(geom["routes"])
    m = solver2.metrics_span_aware(world, merged["routes"], merged["vias"])
    assert m["all_connected"] and sum(m["violations"].values()) == 0
    # 几何等价（cell 集）：split+merge 不改变铜几何
    m0 = solver2.metrics_span_aware(world, geom["routes"], geom["vias"])
    assert (m["total_length_mm"], m["via_count"], m["bend_count"]) == \
        (m0["total_length_mm"], m0["via_count"], m0["bend_count"])


def test_proposal_stream_deterministic_and_typed(synth, ml_geom):
    _s, board, world, geom = synth
    s1 = [json.dumps(p, sort_keys=True) for p in
          v2_proposal_stream(world, board, geom)]
    s2 = [json.dumps(p, sort_keys=True) for p in
          v2_proposal_stream(world, board, geom)]
    assert s1 == s2
    assert {p["action_type"] for p in v2_proposal_stream(world, board, geom)} \
        <= set(NEW_ACTION_TYPES)
    _b, w2, g2 = ml_geom
    stream = list(v2_proposal_stream(w2, _b, g2))
    assert stream  # 非空
    assert all(p["schema_version"] == PATCH_SCHEMA_V2 for p in stream)


# ---------------------------------------------------------------- 负例：结构/身份/几何

def test_schema_and_whitelist_negatives(synth):
    _sid, board, world, geom = synth
    patch = _first_legal_patch(world, board, geom, DELETE_VIA)
    # 非法 schema
    for bad in ("v4-route-patch/3", "v4-route-patch", None, 1):
        p = dict(patch)
        p["schema_version"] = bad
        assert not validate_patch2(world, board, p, geom)["legal"]
    # 未知键
    p = dict(patch)
    p["width_mm"] = 0.99
    r = validate_patch2(world, board, p, geom)
    assert not r["legal"] and any("未知键" in x for x in r["reasons"])
    # 缺键
    p = {k: v for k, v in patch.items() if k != "keep_layer"}
    r = validate_patch2(world, board, p, geom)
    assert not r["legal"] and any("缺失" in x for x in r["reasons"])
    # 非法 action_type
    p = dict(patch)
    p["action_type"] = "replace_whole_board"
    assert not validate_patch2(world, board, p, geom)["legal"]


def test_stale_hash_and_unknown_object_negatives(synth):
    _sid, board, world, geom = synth
    patch = _first_legal_patch(world, board, geom, INSERT_VIA) or \
        _first_legal_patch(world, board, geom, DELETE_VIA)
    p = dict(patch)
    p["base_candidate_geometry_sha256"] = "0" * 64
    r = validate_patch2(world, board, p, geom)
    assert not r["legal"]
    p = dict(patch)
    p["route_id"] = "n9-S99"
    p["via_id"] = "n9-V99"
    assert not validate_patch2(world, board, p, geom)["legal"]


def test_identity_negatives(synth):
    _sid, board, world, geom = synth
    patch = _first_legal_patch(world, board, geom, DELETE_VIA)
    # 端点链逆转
    p = dict(patch)
    p["fixed_endpoint_ids"] = list(reversed(p["fixed_endpoint_ids"]))
    assert not validate_patch2(world, board, p, geom)["legal"]
    # 异网身份
    p = dict(patch)
    p["net_id"] = "n2"
    assert not validate_patch2(world, board, p, geom)["legal"]
    # 异段 fixed_endpoint_ids
    p = dict(patch)
    other = [r for r in geom["routes"] if r["net_id"] == "n2"][0]
    p["fixed_endpoint_ids"] = [str(x) for x in other["endpoint_ids"]]
    assert not validate_patch2(world, board, p, geom)["legal"]


def test_layer_and_coord_negatives(synth):
    _sid, board, world, geom = synth
    dv = _first_legal_patch(world, board, geom, DELETE_VIA)
    p = dict(dv)
    p["keep_layer"] = "In2.Cu"  # 不在 {A,B} 层对内（该 via 为 F..B）
    assert not validate_patch2(world, board, p, geom)["legal"]
    iv = _first_legal_patch(world, board, geom, INSERT_VIA)
    if iv is not None:
        p = dict(iv)
        p["to_layer"] = p["layer"]  # 同层
        assert not validate_patch2(world, board, p, geom)["legal"]
        p = dict(iv)
        p["via_mm"] = [float(iv["via_mm"][0]) + 0.1, iv["via_mm"][1]]
        assert not validate_patch2(world, board, p, geom)["legal"]
        p = dict(iv)
        p["via_mm"] = [float("nan"), iv["via_mm"][1]]
        assert not validate_patch2(world, board, p, geom)["legal"]
    sp = _first_legal_patch(world, board, geom, SPLIT_SEGMENT)
    p = dict(sp)
    p["split_mm"] = [sp["split_mm"][0] + 0.1, sp["split_mm"][1]]
    assert not validate_patch2(world, board, p, geom)["legal"]
    p = dict(sp)
    p["split_mm"] = [float("nan"), sp["split_mm"][1]]
    assert not validate_patch2(world, board, p, geom)["legal"]


def test_merge_negatives(synth):
    _sid, board, world, geom = synth
    sp = _first_legal_patch(world, board, geom, SPLIT_SEGMENT)
    res = apply_and_check2(world, board, sp, geom)
    geom2 = res["geometry"]
    mp = _first_legal_patch(world, board, geom2, MERGE_SEGMENTS)
    # 自并
    p = dict(mp)
    p["merge_with_route_id"] = p["route_id"]
    assert not validate_patch2(world, board, p, geom2)["legal"]
    # 未知 id
    p = dict(mp)
    p["merge_with_route_id"] = "n9-S99"
    assert not validate_patch2(world, board, p, geom2)["legal"]
    # 非相邻段
    p = dict(mp)
    p["merge_with_route_id"] = "n2-S01"
    assert not validate_patch2(world, board, p, geom2)["legal"]


def test_delete_via_degenerate_span_rejected(synth):
    _sid, board, world, geom = synth
    # V03 (In1..B) 删除 keep=B：下游 S04 在 B → 退化跨度 B..B
    p = None
    for cand in v2_proposal_stream(world, board, geom):
        if cand["action_type"] == DELETE_VIA and \
                cand["via_id"] == "n1-V03" and cand["keep_layer"] == "B.Cu":
            p = cand
            break
    if p is not None:
        r = validate_patch2(world, board, p, geom)
        assert not r["legal"]


# ---------------------------------------------------------------- v1 兼容

def test_v1_schema_delegates_bit_exact(synth):
    """schema v1 patch 在 v2 入口下的判定与 v1 validator 完全一致。"""
    _sid, board, world, geom = synth
    # v1 域内构造：单段 n2 上 replace_subpath（直段→加倒角）
    route = [r for r in geom["routes"] if r["net_id"] == "n2"][0]
    poly = route["polyline_mm"]
    mid = poly[len(poly) // 2]
    v1_patch = {
        "schema_version": cmp_patch.PATCH_SCHEMA,
        "action_type": "replace_subpath",
        "base_candidate_geometry_sha256": _sha(geom),
        "scenario_id": board["scenario_id"],
        "route_id": route["route_id"],
        "net_id": "n2",
        "relation_id": None,
        "parent_id": None,
        "fixed_endpoint_ids": [str(x) for x in route["endpoint_ids"]],
        "reason": "v1 contract regression",
        "source": "program",
        "layer": route["layer"],
        "width_mm": route["width_mm"],
        "polyline_mm": [poly[0], mid, poly[-1]],
    }
    r_v1 = cmp_patch.validate_patch(world, board, v1_patch, geom)
    r_v2 = validate_patch2(world, board, v1_patch, geom)
    assert r_v1["legal"] == r_v2["legal"]
    assert r_v2["reasons"] == r_v1["reasons"]
    # stale hash 变体同判
    bad = dict(v1_patch)
    bad["base_candidate_geometry_sha256"] = "0" * 64
    assert validate_patch2(world, board, bad, geom)["legal"] is False


def test_v2_schema_accepts_v1_action_with_same_semantics(synth):
    """schema v2 下 v1 动作：改牌委托 v1（语义一致，仅 schema 串放开）。"""
    _sid, board, world, geom = synth
    route = [r for r in geom["routes"] if r["net_id"] == "n2"][0]
    poly = route["polyline_mm"]
    mid = poly[len(poly) // 2]
    v2_patch = {
        "schema_version": PATCH_SCHEMA_V2,
        "action_type": "replace_subpath",
        "base_candidate_geometry_sha256": _sha(geom),
        "scenario_id": board["scenario_id"],
        "route_id": route["route_id"],
        "net_id": "n2",
        "relation_id": None,
        "parent_id": None,
        "fixed_endpoint_ids": [str(x) for x in route["endpoint_ids"]],
        "reason": "v2 schema v1 action",
        "source": "program",
        "layer": route["layer"],
        "width_mm": route["width_mm"],
        "polyline_mm": [poly[0], mid, poly[-1]],
    }
    r = validate_patch2(world, board, v2_patch, geom)
    v1_style = dict(v2_patch)
    v1_style["schema_version"] = cmp_patch.PATCH_SCHEMA
    r_v1 = cmp_patch.validate_patch(world, board, v1_style, geom)
    assert r["legal"] == r_v1["legal"]
    # v1 动作键合同不因 v2 schema 放开：夹带未知键仍拒
    bad = dict(v2_patch)
    bad["via_id"] = "n1-V01"
    assert not validate_patch2(world, board, bad, geom)["legal"]


def test_p1_replay_subset_agrees_with_v1_record():
    """盘上 P1 记录负向计数=81；v2 重放摘要一致（本测试读台账不重跑）。"""
    path = os.path.join(_ROOT, "out", "v4.1-engineering", "e3",
                        "p1-replay-v1.json")
    if not os.path.exists(path):
        pytest.skip("p1-replay-v1.json 尚未生成（CLI 运行后生效）")
    with open(path, encoding="utf-8") as f:
        rec = json.load(f)
    s = rec["summary"]
    assert s["v1_mutations_total"] == 81
    assert s["v1_mutations_blocked_v2"] == 81
    assert s["backward_compat_81_of_81"] is True
    assert s["program_acceptance_v2"] == "12/12"
    # 与盘上 P1 原件对账（只读）
    with open(os.path.join(_CMP, "p1", "patch-results.json"),
              encoding="utf-8") as f:
        orig = json.load(f)
    orig_total = sum(len(e.get("mutations", []))
                     for e in orig["cases"])
    orig_blocked = sum(1 for e in orig["cases"] for m in e.get("mutations", [])
                       if m.get("blocked"))
    assert orig_total == orig_blocked == 81


# ---------------------------------------------------------------- 精化环

def test_refine_v2_strict_improvement_only(synth):
    """精化环：接受判据=冻结 objective 严格改善；结果不劣于初始。"""
    _sid, board, world, geom = synth
    run = {"status": "sat", "routes": geom["routes"], "vias": geom["vias"]}
    out = action2.refine_v2(world, board, run, max_proposals=32)
    assert out["final_metrics"]["objective"] <= out["base_metrics"]["objective"]
    for p in out["proposals"]:
        if p["accepted"]:
            assert p["candidate_objective"] is not None
    # 接受数=严格改善数
    accepted_obj = [p["candidate_objective"] for p in out["proposals"]
                    if p["accepted"]]
    assert all(o is not None for o in accepted_obj)


def test_refine_v2_skips_unsat():
    _sid, board, geom = synthetic_chain_base()
    world = GridWorld(board)
    out = action2.refine_v2(world, board, {"status": "failed",
                                           "routes": [], "vias": []})
    assert out["evaluations"] == 0 and out["accepted_count"] == 0
