# -*- coding: utf-8 -*-
"""ingest fail-closed ≥12 例（格式层整批拒收 + 语义层逐条拒收词表）。"""
import json

import pytest

from canvas_pilot import protocol


def batch(actions, round_no=1):
    return json.dumps({"round": round_no, "actions": actions})


def expect_batch_reject(text, code, round_no=1):
    with pytest.raises(protocol.BatchReject) as ei:
        protocol.parse_batch(text, round_no)
    assert ei.value.code == code, (ei.value.code, code, ei.value.detail)


def test_e_parse():
    expect_batch_reject("this is not json", protocol.E_PARSE)


def test_e_not_object():
    expect_batch_reject("[1,2,3]", protocol.E_NOT_OBJECT)


def test_e_actions_not_list():
    expect_batch_reject('{"round":1,"actions":"x"}', protocol.E_ACTIONS_NOT_LIST)


def test_e_unknown_action():
    expect_batch_reject(batch([{"action": "teleport", "net_id": "N1"}]),
                        protocol.E_UNKNOWN_ACTION)


def test_e_missing_key():
    expect_batch_reject(batch([{"action": "route", "net_id": "N1"}]),
                        protocol.E_MISSING_KEY)


def test_e_extra_key():
    expect_batch_reject(batch([{"action": "via", "net_id": "N1",
                                "grid": [1, 1], "margin": 0.5}]),
                        protocol.E_EXTRA_KEY)


def test_e_non_integer_grid():
    expect_batch_reject(batch([{"action": "via", "net_id": "N1",
                                "grid": [True, 1]}]),
                        protocol.E_NON_INTEGER_GRID)


def test_e_float_coord():
    # 毫米坐标渗透: 浮点格点 → 整批拒收（任务书钉死口径）
    expect_batch_reject(batch([{"action": "via", "net_id": "N1",
                                "grid": [12.616, 107.7]}]),
                        protocol.E_FLOAT_COORD)


def test_e_string_coord():
    expect_batch_reject(batch([{"action": "via", "net_id": "N1",
                                "grid": ["1", "2"]}, ]),
                        protocol.E_FLOAT_COORD)


def test_e_grid_out_of_bounds():
    # 越界格点（格式层: 负索引/超 i_max 都在 parse 后由 apply 语义层兜住,
    # 但 waypoints 越界同样必须拒——micro 板 21×17, [999,0] 越界）
    acts = [{"action": "route", "net_id": "N1",
             "waypoints": [[999, 0], [1, 1]], "layer": "F.Cu"},
            {"action": "submit"}]
    res = protocol.parse_batch(batch(acts), 1)
    from canvas_pilot import lattice as _lat, state as _state
    from canvas_pilot.conftest import micro_board
    board = micro_board()
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    out = protocol.apply_batch(st, res, 1)
    assert out[0]["accepted"] is False
    assert out[0]["code"] == protocol.E_GRID_OUT_OF_BOUNDS


def test_e_no_submit():
    expect_batch_reject(batch([{"action": "ripup", "net_id": "N1"}]),
                        protocol.E_NO_SUBMIT)


def test_e_trailing_action():
    expect_batch_reject(batch([{"action": "submit"},
                               {"action": "ripup", "net_id": "N1"}]),
                        protocol.E_TRAILING_ACTION)


def test_e_round_mismatch():
    expect_batch_reject(batch([{"action": "submit"}], round_no=7),
                        protocol.E_ROUND_MISMATCH, round_no=1)


def test_e_waypoints_too_few():
    expect_batch_reject(batch([{"action": "route", "net_id": "N1",
                                "waypoints": [[1, 1]], "layer": "F.Cu"},
                               {"action": "submit"}]),
                        protocol.E_WAYPOINTS_TOO_FEW)


def test_e_ripup_target():
    expect_batch_reject(batch([{"action": "ripup"}]), protocol.E_RIPUP_TARGET)
    expect_batch_reject(batch([{"action": "ripup", "net_id": "N1",
                                "shape_id": "seg:N1:0"}]),
                        protocol.E_RIPUP_TARGET)


def test_semantic_rejection_is_per_action(micro_state):
    """语义层=逐条拒收: 第一条几何违例不废第二条合法动作（fail-closed 分层）。"""
    st = micro_state
    acts = [
        # N1 端到端合法: 锚A(1,1) → 锚B(19,1)
        {"action": "route", "net_id": "N1",
         "waypoints": [[1, 1], [19, 1]], "layer": "F.Cu"},
        # N2 绕行触 N1 焊盘（pad 半径参与 R5）→ V_CLEARANCE
        {"action": "route", "net_id": "N2",
         "waypoints": [[1, 15], [1, 2], [19, 2], [19, 15]], "layer": "F.Cu"},
        {"action": "submit"},
    ]
    out = protocol.apply_batch(st, protocol.parse_batch(batch(acts), 1), 1)
    assert out[0]["accepted"] is True
    assert out[1]["accepted"] is False
    assert out[1]["code"] == protocol.V_CLEARANCE


def test_via_off_path(micro_state):
    st = micro_state
    acts = [{"action": "via", "net_id": "N1", "grid": [5, 5]},
            {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(batch(acts), 1), 1)
    assert out[0]["accepted"] is False
    assert out[0]["code"] == protocol.V_VIA_OFF_PATH


def test_endpt_not_attached(micro_state):
    st = micro_state
    acts = [{"action": "route", "net_id": "N1",
             "waypoints": [[5, 5], [7, 5]], "layer": "F.Cu"},
            {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(batch(acts), 1), 1)
    assert out[0]["accepted"] is False
    assert out[0]["code"] == protocol.V_ENDPT_NOT_ATTACHED
