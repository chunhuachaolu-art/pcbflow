"""V4.0-B planner 合同测试：parse_planner_response 严格解析 + validator 失败关闭。

负向矩阵每类违例至少一个用例（stale hash、未知 schema/net/route/corridor/层、
越权动作类型、重复 action_id、根级未知键、字段类型非法、confidence 越界、
region 出 bbox），全部断言 verdict=="blocked" 且 validated_actions==[]；
正向覆盖全部 7 个白名单动作 accepted 与 reason/confidence 透传。
夹具全部代码内合成最小字典，不访问网络、不调真实模型。
"""

import copy
import hashlib
import json

import pytest

from pcbflow import v4_action_validator as validator
from pcbflow.v4_planner_contract import (
    ALLOWED_ACTION_TYPES,
    PLANNER_ACTION_SCHEMA,
    PlannerContractError,
    canonical_planner_response,
    parse_planner_response,
    planner_response_hash,
)

BOARD_SHA = hashlib.sha256(b"synthetic board v4planner").hexdigest()
MANIFEST_SHA = hashlib.sha256(b"synthetic manifest v4planner").hexdigest()


# ---------------------------------------------------------------- 合成夹具

def base_board():
    """validator registry 口径的最小板：nets / relations(bus) / 层 / bbox。"""
    return {
        "scenario_id": "syn-1",
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "nets": [{"net_id": "n1"}, {"net_id": "n2"}, {"net_id": "n3"}],
        "relations": [{"relation_id": "BUS-SPI", "relation_type": "bus",
                       "members": ["n1", "n2"]}],
    }


def base_manifest():
    """routes 已注册 3 条；corridors 注册 2 条。"""
    return {
        "routes": [{"route_id": "r-1"}, {"route_id": "r-2"},
                   {"route_id": "r-3"}],
        "relations": [],
        "corridors": [{"corridor_id": "C-F-01"}, {"corridor_id": "C-B-01"}],
    }


def base_expected():
    return {"board_snapshot_sha256": BOARD_SHA,
            "route_manifest_sha256": MANIFEST_SHA}


def default_actions():
    """全部 7 个白名单动作各一份，完全合法。"""
    return [
        {"action_id": "A-001", "type": "set_route_order",
         "target_bus_ids": ["BUS-SPI"], "order": ["n3", "n1", "n2"],
         "reason": "clock-first", "confidence": 0.9},
        {"action_id": "A-002", "type": "prefer_corridor",
         "target_net_ids": ["n2"], "corridor_id": "C-F-01",
         "preferred_layers": ["F.Cu", "B.Cu"], "confidence": 0.72},
        {"action_id": "A-003", "type": "prefer_layer",
         "target_net_ids": ["n3"], "preferred_layers": ["F.Cu"]},
        {"action_id": "A-004", "type": "lock_route",
         "target_route_ids": ["r-1"]},
        {"action_id": "A-005", "type": "flag_suspect_region",
         "region_mm": [10.0, 10.0, 20.0, 20.0], "related_net_ids": ["n1"],
         "reason": "疑似拥挤"},
        {"action_id": "A-006", "type": "suggest_ripup_reroute",
         "target_net_ids": ["n2"]},
        {"action_id": "A-007", "type": "rank_candidates",
         "candidate_ids": ["cand-a", "cand-b"]},
    ]


def base_response(actions=None):
    resp = {
        "schema_version": PLANNER_ACTION_SCHEMA,
        "board_snapshot_sha256": BOARD_SHA,
        "route_manifest_sha256": MANIFEST_SHA,
        "actions": default_actions() if actions is None else actions,
        "uncertainties": ["C-F-01 剩余容量需 solver 确认"],
    }
    return resp


def validate(resp, board=None, manifest=None, expected=None):
    return validator.validate_actions(
        resp, base_board() if board is None else board,
        base_manifest() if manifest is None else manifest,
        base_expected() if expected is None else expected)


def assert_blocked(result):
    verdict, reasons, validated = result
    assert verdict == "blocked"
    assert validated == []
    assert reasons, "blocked 必须给出 reasons（evidence 完整收集）"


def _flip(sha):
    return ("0" if sha[0] != "0" else "1") + sha[1:]


def _mutate_action(idx, key, value):
    def _apply(resp):
        resp["actions"][idx][key] = value
    return _apply


# ---------------------------------------------------------------- parse

def test_parse_accepts_valid_json_string():
    resp = base_response()
    parsed = parse_planner_response(json.dumps(resp))
    assert isinstance(parsed, dict)
    assert parsed == resp
    assert parsed["schema_version"] == PLANNER_ACTION_SCHEMA


def test_parse_accepts_dict_and_returns_same_object():
    resp = base_response()
    assert parse_planner_response(resp) is resp


def test_parse_error_is_value_error():
    assert issubclass(PlannerContractError, ValueError)


@pytest.mark.parametrize("raw", ["{not json", "", "  ", "{",])
def test_parse_rejects_invalid_json(raw):
    with pytest.raises(PlannerContractError):
        parse_planner_response(raw)


@pytest.mark.parametrize("raw", ["[]", "42", "null", '"a string"'])
def test_parse_rejects_json_non_object(raw):
    with pytest.raises(PlannerContractError):
        parse_planner_response(raw)


@pytest.mark.parametrize("version", ["v3-planner-action-9",
                                     "v4-planner-action-2", None])
def test_parse_rejects_wrong_or_missing_schema_version(version):
    resp = base_response()
    if version is None:
        del resp["schema_version"]
    else:
        resp["schema_version"] = version
    with pytest.raises(PlannerContractError):
        parse_planner_response(resp)
    with pytest.raises(PlannerContractError):
        parse_planner_response(json.dumps(resp))


@pytest.mark.parametrize("raw", [42, None, ["x"], 3.14, object()])
def test_parse_rejects_non_string_non_dict(raw):
    with pytest.raises(PlannerContractError):
        parse_planner_response(raw)


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_parse_rejects_non_finite_json_constants(literal):
    """JSON 文本含 NaN/Infinity 字面量 => 入口即拒（parse_constant fail-closed）。"""
    raw = ('{"schema_version": "%s", "board_snapshot_sha256": "%s",'
           ' "route_manifest_sha256": "%s", "actions": [{"action_id": "A-N",'
           ' "type": "flag_suspect_region", "region_mm": [%s, 10.0, 20.0,'
           ' 20.0]}], "uncertainties": []}'
           % (PLANNER_ACTION_SCHEMA, BOARD_SHA, MANIFEST_SHA, literal))
    with pytest.raises(PlannerContractError):
        parse_planner_response(raw)


# ---------------------------------------------------------------- hash 绑定

def test_response_hash_stable_across_key_insertion_order():
    a = base_response()
    b = {k: a[k] for k in reversed(list(a.keys()))}
    assert planner_response_hash(a) == planner_response_hash(b)
    assert canonical_planner_response(a) == canonical_planner_response(b)


def test_response_hash_binds_sha_claims_and_actions():
    a = base_response()
    flipped = base_response()
    flipped["board_snapshot_sha256"] = _flip(BOARD_SHA)
    reordered = base_response()
    reordered["actions"] = list(reversed(reordered["actions"]))
    assert planner_response_hash(a) != planner_response_hash(flipped)
    assert planner_response_hash(a) != planner_response_hash(reordered)
    assert json.loads(canonical_planner_response(a)) == a


# ------------------------------------------------- validate_actions 负向矩阵

def test_blocked_stale_board_snapshot_sha256():
    resp = base_response()
    resp["board_snapshot_sha256"] = _flip(BOARD_SHA)
    assert_blocked(validate(resp))


def test_blocked_stale_route_manifest_sha256():
    resp = base_response()
    resp["route_manifest_sha256"] = _flip(MANIFEST_SHA)
    assert_blocked(validate(resp))


def test_blocked_both_hashes_swapped():
    resp = base_response()
    resp["board_snapshot_sha256"], resp["route_manifest_sha256"] = \
        resp["route_manifest_sha256"], resp["board_snapshot_sha256"]
    assert_blocked(validate(resp))


def test_blocked_unknown_schema_version():
    resp = base_response()
    resp["schema_version"] = "v4-planner-action-2"
    assert_blocked(validate(resp))


def test_blocked_unknown_net_id():
    assert_blocked(validate(_mutate_action(2, "target_net_ids", ["n9"])
                            (base_response())))


def test_blocked_unknown_route_id():
    assert_blocked(validate(_mutate_action(3, "target_route_ids", ["r-99"])
                            (base_response())))


def test_blocked_unknown_corridor_id():
    assert_blocked(validate(_mutate_action(1, "corridor_id", "C-X-99")
                            (base_response())))


def test_blocked_corridor_registry_default_deny_when_unregistered():
    """manifest 无 corridors 键 => 任何 corridor 引用都 blocked（默认拒绝）。"""
    manifest = base_manifest()
    del manifest["corridors"]
    assert_blocked(validate(base_response(), manifest=manifest))


@pytest.mark.parametrize("bad_type", [
    "commit_board", "declare_drc_pass", "write_board", "gate_pass",
    "approve_signoff",
])
def test_blocked_privileged_action_types(bad_type):
    resp = base_response()
    resp["actions"] = [{"action_id": "A-X", "type": bad_type,
                        "order": ["n1"]}]
    verdict, reasons, validated = validate(resp)
    assert verdict == "blocked" and validated == []
    assert any("越权" in r for r in reasons)


def test_blocked_non_marker_unknown_action_type():
    """白名单外但不含越权标记的类型同样 blocked（白名单口径，非标记口径）。"""
    resp = base_response()
    resp["actions"] = [{"action_id": "A-X", "type": "teleport_net",
                        "target_net_ids": ["n1"]}]
    assert_blocked(validate(resp))


def test_blocked_duplicate_action_id():
    assert_blocked(validate(_mutate_action(1, "action_id", "A-001")
                            (base_response())))


def test_blocked_root_unknown_key():
    resp = base_response()
    resp["waypoints"] = [{"route_id": "r-1", "x_mm": 5.0, "y_mm": 5.0}]
    assert_blocked(validate(resp))


ILLEGAL_FIELD_CASES = [
    (_mutate_action(0, "order", "n3,n1,n2"), "order-as-string"),
    (_mutate_action(0, "order", ["n1", "n1", "n2"]), "order-duplicates"),
    (_mutate_action(0, "order", []), "order-empty"),
    (_mutate_action(0, "confidence", "0.9"), "confidence-as-string"),
    (_mutate_action(0, "action_id", 7), "action-id-non-string"),
    (_mutate_action(0, "action_id", ""), "action-id-empty"),
    (_mutate_action(1, "corridor_id", 99), "corridor-id-non-string"),
    (_mutate_action(4, "region_mm", "10,10,20,20"), "region-as-string"),
    (_mutate_action(4, "region_mm", [10.0, 10.0, 20.0]), "region-len-3"),
    (_mutate_action(3, "target_route_ids", "r-1"), "route-ids-as-string"),
    (_mutate_action(2, "preferred_layers", ["F.Cu", "F.Cu"]),
     "layer-list-duplicates"),
]


@pytest.mark.parametrize("mutate,id_", ILLEGAL_FIELD_CASES,
                         ids=[c[1] for c in ILLEGAL_FIELD_CASES])
def test_blocked_illegal_field_types(mutate, id_):
    resp = base_response()
    mutate(resp)
    assert_blocked(validate(resp))


@pytest.mark.parametrize("bad_conf", [1.5, -0.1, 2, 100])
def test_blocked_confidence_out_of_range(bad_conf):
    assert_blocked(validate(_mutate_action(0, "confidence", bad_conf)
                            (base_response())))


def test_blocked_region_mm_all_nan_dict_form():
    """dict 形态 region_mm=[NaN]*4：NaN 使链式比较全为 False，修复前会
    被判 accepted 透传；修复后 _is_num 拒绝非有限值（fail-closed）。"""
    resp = base_response()
    resp["actions"][4]["region_mm"] = [float("nan")] * 4
    assert_blocked(validate(resp))


def test_blocked_confidence_nan_dict_form():
    resp = base_response()
    resp["actions"][0]["confidence"] = float("nan")
    assert_blocked(validate(resp))


@pytest.mark.parametrize("region", [
    [10.0, 10.0, 50.0, 20.0],    # x1 出右边界
    [-5.0, 10.0, 20.0, 20.0],    # x0 出左边界
    [10.0, 10.0, 20.0, 40.0],    # y1 出上边界
    [20.0, 10.0, 10.0, 20.0],    # 退化：x0 >= x1
])
def test_blocked_region_out_of_bbox(region):
    assert_blocked(validate(_mutate_action(4, "region_mm", region)
                            (base_response())))


def test_blocked_region_when_board_bbox_missing():
    """board 无 bbox 时无法验证区域 => fail-closed。"""
    board = base_board()
    del board["board"]["bbox_mm"]
    assert_blocked(validate(base_response(), board=board))


def test_blocked_missing_claim_hash():
    resp = base_response()
    del resp["board_snapshot_sha256"]
    assert_blocked(validate(resp))


def test_blocked_non_string_claim_hash():
    resp = base_response()
    resp["route_manifest_sha256"] = 12345
    assert_blocked(validate(resp))


def test_blocked_expected_hashes_missing_key():
    expected = {"board_snapshot_sha256": BOARD_SHA}
    assert_blocked(validate(base_response(), expected=expected))


def test_blocked_expected_hashes_not_a_dict():
    assert_blocked(validate(base_response(), expected=["nope"]))
    verdict, reasons, validated = validator.validate_actions(
        base_response(), base_board(), base_manifest(), None)
    assert verdict == "blocked"
    assert validated == []
    assert reasons


def test_blocked_response_not_an_object():
    assert_blocked(validate(["nope"]))
    assert_blocked(validate(None))


def test_blocked_actions_not_a_list():
    assert_blocked(validate(base_response(actions={"A-001": {}})))


def test_blocked_action_not_an_object():
    assert_blocked(validate(base_response(actions=["A-001"])))


def test_blocked_required_per_type_key_missing():
    resp = base_response()
    resp["actions"] = [{"action_id": "A-001", "type": "prefer_layer",
                        "target_net_ids": ["n3"]}]
    assert_blocked(validate(resp))


def test_blocked_uncertainties_not_string_list():
    resp = base_response()
    resp["uncertainties"] = "guess"
    assert_blocked(validate(resp))


# ---------------------------------------------------------------- 正向

def test_accepted_all_whitelisted_actions_with_passthrough():
    resp = base_response()
    verdict, reasons, validated = validate(resp)
    assert verdict == "accepted"
    assert reasons == []
    assert [a["action_id"] for a in validated] == \
        ["A-00%d" % i for i in range(1, 8)]
    assert {a["type"] for a in validated} == set(ALLOWED_ACTION_TYPES)
    # reason / confidence / 语义字段原样透传，不重排不改写
    assert validated[0] == {"action_id": "A-001", "type": "set_route_order",
                            "target_bus_ids": ["BUS-SPI"],
                            "order": ["n3", "n1", "n2"],
                            "reason": "clock-first", "confidence": 0.9}
    assert validated[1]["corridor_id"] == "C-F-01"
    assert validated[1]["preferred_layers"] == ["F.Cu", "B.Cu"]
    assert validated[4]["region_mm"] == [10.0, 10.0, 20.0, 20.0]
    assert validated[4]["reason"] == "疑似拥挤"
    assert validated[6]["candidate_ids"] == ["cand-a", "cand-b"]
    # 无 reason / confidence 的动作不带空字段
    assert "reason" not in validated[3]
    assert "confidence" not in validated[3]


def test_accepted_each_whitelist_type_individually():
    for act in default_actions():
        resp = base_response(actions=[copy.deepcopy(act)])
        verdict, reasons, validated = validate(resp)
        assert verdict == "accepted", (act["type"], reasons)
        assert len(validated) == 1
        assert validated[0]["type"] == act["type"]


def test_parse_then_validate_end_to_end_accepted():
    verdict, reasons, validated = validate(
        parse_planner_response(json.dumps(base_response())))
    assert verdict == "accepted"
    assert reasons == []
    assert len(validated) == 7
