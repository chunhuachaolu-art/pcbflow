"""V4.0-B solver bridge 测试：apply_actions 确定性语义 + phase_gate 失败关闭。

覆盖：route_order/lock 首现去重、corridor/layer 偏好 last-wins 且按 net_id
稳定排序、advisory 不绑定求解语义、run record 的 board_write=False /
来源标记 untrusted / actions_source_sha256 确定性；phase_gate 对 E0/E1 放行、
E2/E3 默认 blocked、allow_real_board 只落 requires_approval_record 不伪造
批准；BOARD_WRITE/LIVE_COMMIT 常量恒为 False。
夹具为 validator 产出口径的干净动作（代码内合成），零网络零模型。
"""

import pytest

from pcbflow import hashing, v4_solver_bridge as bridge
from pcbflow.v4_planner_contract import PLANNER_ACTION_SCHEMA

BOARD = {"scenario_id": "syn-1"}


def act_order(aid, order, **extra):
    act = {"action_id": aid, "type": "set_route_order", "order": order}
    act.update(extra)
    return act


def act_lock(aid, rids):
    return {"action_id": aid, "type": "lock_route",
            "target_route_ids": rids}


def act_corridor(aid, nets, corridor_id, layers=None):
    act = {"action_id": aid, "type": "prefer_corridor",
           "target_net_ids": nets, "corridor_id": corridor_id}
    if layers is not None:
        act["preferred_layers"] = layers
    return act


def act_layer(aid, nets, layers):
    return {"action_id": aid, "type": "prefer_layer",
            "target_net_ids": nets, "preferred_layers": layers}


# ---------------------------------------------------------------- 常量红线

def test_board_write_and_live_commit_constants_are_false():
    assert bridge.BOARD_WRITE is False
    assert bridge.LIVE_COMMIT is False


# ---------------------------------------------------------------- 合并语义

def test_route_order_appends_with_first_occurrence_dedup():
    si = {}
    rec = bridge.apply_actions(
        [act_order("A-1", ["n1", "n2"], reason="r1"),
         act_order("A-2", ["n2", "n3"])],
        BOARD, si)
    assert si["route_order"] == ["n1", "n2", "n3"]
    assert rec["applied"]["set_route_order"] == 2


def test_route_order_extends_existing_solver_input():
    si = {"route_order": ["n3"]}
    bridge.apply_actions([act_order("A-1", ["n3", "n1"])], BOARD, si)
    assert si["route_order"] == ["n3", "n1"]


def test_lock_route_dedup_and_order_preserved():
    si = {}
    bridge.apply_actions(
        [act_lock("A-1", ["r-1", "r-2"]), act_lock("A-2", ["r-2", "r-3"])],
        BOARD, si)
    assert si["locked_route_ids"] == ["r-1", "r-2", "r-3"]


def test_corridor_preference_last_wins_sorted_by_net_id():
    si = {}
    bridge.apply_actions(
        [act_corridor("A-1", ["n2"], "C-1"),
         act_corridor("A-2", ["n1"], "C-2"),
         act_corridor("A-3", ["n2"], "C-2", layers=["F.Cu", "B.Cu"])],
        BOARD, si)
    prefs = si["corridor_preferences"]
    assert [p["net_id"] for p in prefs] == ["n1", "n2"]  # 稳定排序
    assert prefs[0] == {"net_id": "n1", "corridor_id": "C-2"}
    # n2 的最终偏好来自最后一个动作（last-wins），preferred_layers 保留
    assert prefs[1] == {"net_id": "n2", "corridor_id": "C-2",
                        "preferred_layers": ["F.Cu", "B.Cu"]}


def test_layer_preference_last_wins_sorted_by_net_id():
    si = {}
    bridge.apply_actions(
        [act_layer("A-1", ["n2"], ["F.Cu"]),
         act_layer("A-2", ["n1"], ["B.Cu"]),
         act_layer("A-3", ["n2"], ["B.Cu"])],
        BOARD, si)
    prefs = si["layer_preferences"]
    assert prefs == [{"net_id": "n1", "layers": ["B.Cu"]},
                     {"net_id": "n2", "layers": ["B.Cu"]}]


def test_advisory_actions_do_not_bind_solver_params():
    si = {}
    rec = bridge.apply_actions(
        [{"action_id": "A-1", "type": "flag_suspect_region",
          "region_mm": [1.0, 1.0, 2.0, 2.0], "related_net_ids": ["n1"],
          "reason": "拥挤", "confidence": 0.5},
         {"action_id": "A-2", "type": "suggest_ripup_reroute",
          "target_net_ids": ["n2"]},
         {"action_id": "A-3", "type": "rank_candidates",
          "candidate_ids": ["c1", "c2"]}],
        BOARD, si)
    assert rec["applied"]["advisory"] == 3
    for key in ("route_order", "locked_route_ids", "corridor_preferences",
                "layer_preferences"):
        assert key not in si
    adv = si["advisory"]
    assert [a["action_id"] for a in adv] == ["A-1", "A-2", "A-3"]
    assert [a["type"] for a in adv] == list(bridge.ADVISORY_TYPES)
    assert adv[0]["region_mm"] == [1.0, 1.0, 2.0, 2.0]
    assert adv[0]["reason"] == "拥挤" and adv[0]["confidence"] == 0.5


def test_advisory_appends_to_existing_list_in_order():
    si = {"advisory": [{"action_id": "A-0", "type": "rank_candidates",
                        "candidate_ids": ["c0"]}]}
    bridge.apply_actions(
        [{"action_id": "A-1", "type": "rank_candidates",
          "candidate_ids": ["c1"]}], BOARD, si)
    assert [a["action_id"] for a in si["advisory"]] == ["A-0", "A-1"]


# ---------------------------------------------------------------- run record

def _one_action():
    return [act_order("A-1", ["n1", "n2"], reason="clock-first",
                      confidence=0.9)]


def test_run_record_flags_schema_and_trust_marks():
    si = {}
    rec = bridge.apply_actions(_one_action(), BOARD, si)
    assert rec["schema"] == bridge.RUN_RECORD_SCHEMA
    assert rec["scenario_id"] == "syn-1"
    assert rec["board_write"] is False
    assert rec["live_commit"] is False
    assert rec["board_write"] == bridge.BOARD_WRITE
    assert rec["live_commit"] == bridge.LIVE_COMMIT
    assert rec["input_trust"] == "untrusted_planner_output_validated"
    assert rec["actions_source_schema"] == PLANNER_ACTION_SCHEMA
    assert rec["solver_input"] is si  # 原地更新且同一对象
    assert rec["applied"] == {"set_route_order": 1, "prefer_corridor": 0,
                              "prefer_layer": 0, "lock_route": 0,
                              "advisory": 0}


def test_actions_source_sha256_is_canonical_hash_of_consumed_actions():
    actions = _one_action()
    rec = bridge.apply_actions(actions, BOARD, {})
    expected = hashing.sha256_text(hashing.json_dumps(actions))
    assert rec["actions_source_sha256"] == expected


def test_actions_source_sha256_deterministic_same_input_same_hash():
    rec1 = bridge.apply_actions(_one_action(), BOARD, {})
    rec2 = bridge.apply_actions(_one_action(), BOARD, {})
    assert rec1["actions_source_sha256"] == rec2["actions_source_sha256"]
    # solver_input 初态不同不影响来源 hash（hash 只绑定被消费的动作列表）
    rec3 = bridge.apply_actions(_one_action(), BOARD,
                                {"route_order": ["n9"]})
    assert rec3["actions_source_sha256"] == rec1["actions_source_sha256"]


def test_actions_source_sha256_changes_with_input_actions():
    rec1 = bridge.apply_actions(_one_action(), BOARD, {})
    rec2 = bridge.apply_actions(
        [act_order("A-1", ["n2", "n1"], reason="clock-first",
                   confidence=0.9)], BOARD, {})
    assert rec1["actions_source_sha256"] != rec2["actions_source_sha256"]


def test_board_without_scenario_id_records_none():
    rec = bridge.apply_actions(_one_action(), {}, {})
    assert rec["scenario_id"] is None
    rec2 = bridge.apply_actions(_one_action(), "not-a-dict", {})
    assert rec2["scenario_id"] is None


# ---------------------------------------------------------------- 输入防线

def test_rejects_non_dict_solver_input():
    with pytest.raises(ValueError):
        bridge.apply_actions(_one_action(), BOARD, "nope")


def test_rejects_non_validator_shaped_actions():
    with pytest.raises(ValueError):
        bridge.apply_actions(["not-a-dict"], BOARD, {})
    with pytest.raises(ValueError):
        bridge.apply_actions([{"action_id": "A-1"}], BOARD, {})  # 无 type
    with pytest.raises(ValueError):
        bridge.apply_actions([{"action_id": "A-1", "type": "commit_board"}],
                             BOARD, {})


# ---------------------------------------------------------------- phase_gate

@pytest.mark.parametrize("phase", ["E0", "E1"])
def test_gate_allows_synthetic_phases(phase):
    gate = bridge.phase_gate(phase)
    assert gate["verdict"] == "allowed"
    assert gate["board_scope"] == "synthetic"
    assert gate["phase"] == phase
    assert gate["allow_real_board"] is False


@pytest.mark.parametrize("phase", ["E2", "E3"])
def test_gate_blocks_real_board_phases_by_default(phase):
    gate = bridge.phase_gate(phase)
    assert gate["verdict"] == "blocked"
    assert gate["board_scope"] == "real-board"


@pytest.mark.parametrize("phase", ["E2", "E3"])
def test_gate_real_board_with_allow_requires_approval_record(phase):
    gate = bridge.phase_gate(phase, allow_real_board=True)
    assert gate["verdict"] == "requires_approval_record"
    assert gate["board_scope"] == "real-board"
    assert gate["allow_real_board"] is True
    assert gate["approval_record_required_fields"] == \
        list(bridge.APPROVAL_RECORD_REQUIRED_FIELDS)
    assert set(bridge.APPROVAL_RECORD_REQUIRED_FIELDS) == \
        {"approver", "scope", "board_ids", "approval_record_sha256"}
    # 不伪造批准：gate 结果里没有任何一份真实批准记录
    for key in ("approver", "scope", "board_ids",
                "approval_record_sha256", "approval_record"):
        assert key not in gate


@pytest.mark.parametrize("phase", ["E9", "e0", "", "EX"])
def test_gate_blocks_unknown_phase(phase):
    gate = bridge.phase_gate(phase)
    assert gate["verdict"] == "blocked"
    assert gate["board_scope"] == "unknown"
