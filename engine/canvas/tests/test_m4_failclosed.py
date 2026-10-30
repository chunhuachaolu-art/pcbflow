# -*- coding: utf-8 -*-
"""Lane-M4 fail-closed 矩阵（≥10）: placecheck 拒收路径全谱 + set_placement
越界后的 validator 兜底 + runner 永不落非法放置。

口径标注: placecheck 是**新 validator，非 v5.drc 移植**——本族拒收码是
placecheck 命名空间（E_UNKNOWN_PARTITION/V_PLACEMENT_EDGE 新码; 其余借
protocol 既有码同名同义）。"""
import json

import pytest

from canvas import placecheck as pc
from canvas.runners import m4
from canvas.tests.test_k1_fixtures import real_state, synth_state
from canvas.tests.test_m4_fixtures import blocked_state


# ------------------------------------------------- check_placement 拒收谱

def test_fc_unknown_partition():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "NOPE", {"move": [10, 10]})
    assert not ok and code == "E_UNKNOWN_PARTITION"


def test_fc_move_float_coord():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PA", {"move": [1.5, 4]})
    assert not ok and code == "E_NON_INTEGER_GRID"


def test_fc_move_bool_coord():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PA", {"move": [True, 4]})
    assert not ok and code == "E_NON_INTEGER_GRID"


def test_fc_move_wrong_arity():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PA", {"move": [4, 4, 4]})
    assert not ok and code == "E_NON_INTEGER_GRID"


def test_fc_move_out_of_lattice_domain():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PA", {"move": [900, 4]})
    assert not ok and code == "E_GRID_OUT_OF_BOUNDS"


def test_fc_rotate_out_of_domain():
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PA", {"rotate": 9})
    assert not ok and code == "E_GRID_OUT_OF_BOUNDS"


def test_fc_out_of_frame():
    st = synth_state()
    # PA 场宽 9mm: 中心移到 (1.5,1) → 场 (-3,0.5)-(6,1.5) x 越框
    ok, code, detail = pc.check_placement(st.board, st.lattice,
                                          st.placements, "PA",
                                          {"move": [3, 2]})
    assert not ok and code == "V_PLACEMENT_EDGE" and "越框" in detail


def test_fc_collision_synth():
    st = synth_state()
    # PA 移到 PB 排: 中心 (6,8) → 场 (1.5,7.5)-(10.5,8.5) 与 PB 场重叠
    ok, code, detail = pc.check_placement(st.board, st.lattice,
                                          st.placements, "PA",
                                          {"move": [12, 16]})
    assert not ok and code == "V_PLACEMENT_COLLISION" and "gap=" in detail


def test_fc_real_board_envelope_disclosure():
    """真板包络披露: 真板分区 pad 场外接矩形基线互相重叠（36 对中 28 对
    gap<0.5，实测见 lane REPORT）→ 一切候选结构性拒收
    V_PLACEMENT_COLLISION（fail-closed: 宁拒不放）。"""
    st = real_state()
    viol = pc.check_all_placements(st.board, st.lattice, st.placements)
    assert len(viol) == 28
    assert all(v["code"] == "V_PLACEMENT_COLLISION" for v in viol)
    for pid in ("PT-VCC", "PT-Earth"):
        ok, code, _d = pc.check_placement(
            st.board, st.lattice, st.placements, pid, {"move": [44, 42]})
        assert not ok and code == "V_PLACEMENT_COLLISION"


def test_fc_candidate_shape_misuse_raises():
    st = synth_state()
    with pytest.raises(ValueError):
        pc.check_placement(st.board, st.lattice, st.placements, "PA", "x")
    with pytest.raises(ValueError):
        pc.check_placement(st.board, st.lattice, st.placements, "PA",
                           {"move": [1, 2], "extra": 0})


# ------------------------------------------------- set_placement 越界兜底

def test_fc_set_placement_out_of_domain_caught_by_check_all():
    """set_placement 是哑存（不校验）——越界覆盖由 placecheck 兜底:
    E_GRID_OUT_OF_BOUNDS 且该分区退出后续几何判定。"""
    st = synth_state()
    st.set_placement("PA", move=[999, 4])
    v = pc.check_all_placements(st.board, st.lattice, st.placements)
    assert [x["code"] for x in v] == ["E_GRID_OUT_OF_BOUNDS"]
    assert v[0]["partition_id"] == "PA"
    # 候选判同样拦（值域在 check_placement 单点判）
    ok, code, _d = pc.check_placement(st.board, st.lattice, st.placements,
                                      "PB", {"move": [999, 4]})
    assert not ok and code == "E_GRID_OUT_OF_BOUNDS"


def test_fc_set_placement_float_move_caught():
    st = synth_state()
    st.placements["PA"] = {"move": [3.5, 4], "rotate": 0, "flip": False}
    v = pc.check_all_placements(st.board, st.lattice, st.placements)
    assert [x["code"] for x in v] == ["E_NON_INTEGER_GRID"]


def test_fc_set_placement_bad_rotate_caught():
    st = synth_state()
    st.placements["PA"] = {"move": [10, 4], "rotate": 9, "flip": False}
    v = pc.check_all_placements(st.board, st.lattice, st.placements)
    assert [x["code"] for x in v] == ["E_GRID_OUT_OF_BOUNDS"]


def test_fc_set_placement_out_of_frame_caught():
    st = synth_state()
    st.set_placement("PA", move=[3, 2])          # 域内但场越框（见上）
    v = pc.check_all_placements(st.board, st.lattice, st.placements)
    assert [x["code"] for x in v] == ["V_PLACEMENT_EDGE"]


# ------------------------------------------------- runner fail-closed 不变量

def test_fc_runner_never_lands_illegal_placement():
    """run_m4 接受的每个放置都经 placecheck——收工态全场检查零违例
    （合成板基线净空）。"""
    for st in (synth_state(), blocked_state()):
        m4.run_m4(st, 200)
        assert pc.check_all_placements(st.board, st.lattice,
                                       st.placements) == []


def test_fc_real_board_runner_accepts_nothing():
    """真板包络语义下 runner 全拒——零接受、placements 不变（fail-closed
    不误放行）。"""
    st = real_state()
    sha0 = st.sha256()
    s = m4.run_m4(st, 600)
    assert s["accepted_moves"] == 0 and s["placements_final"] == {}
    assert s["evals"] == 144          # 9 分区 × 16 候选，1 轮无改善止
    assert st.sha256() == sha0


def test_fc_plan_mode_rejects_and_records_illegal():
    """plan 注入含非法动作: 拒收记录在案、状态不落。"""
    st = blocked_state()
    plan = [
        {"action": "move", "partition_id": "PZ", "target": [10, 10]},
        {"action": "move", "partition_id": "PA", "target": [3, 2]},   # 越框
        {"action": "rotate", "partition_id": "PB", "turns": 9},       # 值域
        {"action": "move", "partition_id": "PA", "target": [16, 4]},  # 合法
        {"action": "route", "net_id": "NET-A", "waypoints": [[1, 1], [2, 2]],
         "layer": "F.Cu"},                                            # 非布局面
    ]
    s = m4.run_m4(st, 100, plan=plan)
    assert s["accepted_moves"] == 1
    codes = [r["code"] for r in s["rejected"]]
    assert codes == ["E_UNKNOWN_PARTITION", "V_PLACEMENT_EDGE",
                     "E_GRID_OUT_OF_BOUNDS", "E_UNKNOWN_ACTION"]
    assert list(st.placements) == ["PA"]      # 只落了合法 move


def test_fc_budget_is_hard_cap():
    st = blocked_state()
    s = m4.run_m4(st, 10)
    assert s["evals"] == 10


def test_fc_plan_actions_leaves_state_untouched():
    st = blocked_state()
    sha0 = st.sha256()
    plan = m4.plan_actions(st, 200)
    assert st.sha256() == sha0
    assert all(a["action"] in ("move", "rotate", "flip") for a in plan)
    assert json.dumps(plan)                   # JSON 可落（台账面）
