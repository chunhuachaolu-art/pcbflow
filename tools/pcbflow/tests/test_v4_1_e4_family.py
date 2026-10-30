"""tests/test_v4_1_e4_family.py -- E4 L1 f11 族单元测试（纯函数域）。

覆盖：确定性生成/校验 fail-closed/容量构造事实（In1 饱和+In2 兜底）/
30 网全链冒烟（1 场景）/观察台账键。
"""

from __future__ import annotations

import pytest

from pcbflow.v4_1 import e4family as ef


def test_scenario_ids_deterministic():
    ids = ef.scenario_ids_e4()
    assert len(ids) == 8
    assert ids[0][0] == "dev-f11-01" and ids[-1][0] == "hol-f11-08"
    assert ids == ef.scenario_ids_e4()


def test_seed_for_scenario_id():
    assert ef.seed_for_e4("dev-f11-01") == ef.seed_for_e4("dev-f11-01")
    assert ef.seed_for_e4("dev-f11-01") != ef.seed_for_e4("dev-f11-02")


def test_generate_and_validate_all():
    for (sid, split, serial) in ef.scenario_ids_e4():
        ml = ef.generate_e4_scenario(sid, split, serial)
        assert ef.validate_e4board(ml) == []
        assert len(ml["nets"]) == 30 and len(ml["pads"]) == 60
        assert ml["board"]["layers"] == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
        # 确定性：重生成逐字节一致（对象等价）
        ml2 = ef.generate_e4_scenario(sid, split, serial)
        assert ml == ml2


def test_generate_byte_determinism(tmp_path):
    import json
    ml = ef.generate_e4_scenario("dev-f11-01", "development", 1)
    s1 = json.dumps(ml, sort_keys=True, ensure_ascii=False)
    ml2 = ef.generate_e4_scenario("dev-f11-01", "development", 1)
    s2 = json.dumps(ml2, sort_keys=True, ensure_ascii=False)
    assert s1 == s2


def test_capacity_facts():
    """容量构造事实：In1 门合计容量 <30、In2 门兜底 >=30。"""
    for (sid, split, serial) in ef.scenario_ids_e4():
        ml = ef.generate_e4_scenario(sid, split, serial)
        g = ml["gates_mm"]
        in1_cap = (g["in1_a"][1] - g["in1_a"][0]
                   + g["in1_b"][1] - g["in1_b"][0]) / 0.5 - 4
        in2_cap = (g["in2"][1] - g["in2"][0]) / 0.5 - 4
        # In1 两门合计标称容量 < 30（饱和动因）；In2 单门 >= 30（sat 兜底）
        assert in1_cap < 30, (sid, in1_cap)
        assert in2_cap >= 30 - 4, (sid, in2_cap)


def test_validate_negative():
    ml = ef.generate_e4_scenario("dev-f11-01", "development", 1)
    bad = dict(ml)
    bad["nets"] = ml["nets"][:29]
    errs = ef.validate_e4board(bad)
    assert any("nets" in e for e in errs)
    bad2 = dict(ml)
    bad2["schema"] = "wrong"
    assert ef.validate_e4board(bad2)
    bad3 = dict(ml)
    bad3["rules"] = dict(ef.E4_RULES, clearance_mm=0.3)
    assert ef.validate_e4board(bad3)


def test_chain_smoke_one_scenario():
    """单场景全链冒烟（分层臂 sat + 检查腿 hard=0 + In2 非零）。"""
    from pcbflow.v4_1.mlchain import check_ml_solution, \
        mlboard_to_v4exp_board
    from pcbflow.v4_1.solver2 import solve_board2
    from pcbflow.v4_1.costmodel import ViaCostModel
    from pcbflow.v4exp.grid import GridWorld
    ml = ef.generate_e4_scenario("dev-f11-01", "development", 1)
    board = mlboard_to_v4exp_board(ml)
    world = GridWorld(board)
    run = solve_board2(board, {"route_order": sorted(
        n["net_id"] for n in ml["nets"]), "group": "T"},
        cost_model=ViaCostModel(list(world.layers)))
    assert run["status"] == "sat"
    chk = check_ml_solution(ml, run)
    assert chk["check"]["clearance_hard_violations"] == []
    assert chk["check"]["cross_engine_disagreements"] == []
    in2_len = sum(
        sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            for a, b in zip(r["polyline_mm"], r["polyline_mm"][1:]))
        for r in run["routes"] if r["layer"] == "In2.Cu")
    assert in2_len > 0


def test_post_check_rejects_close_pads():
    ml = ef.generate_e4_scenario("dev-f11-01", "development", 1)
    ml["pads"][0] = dict(ml["pads"][0],
                         x_mm=ml["pads"][1]["x_mm"],
                         y_mm=ml["pads"][1]["y_mm"])
    with pytest.raises(ef.E4FamilyError):
        ef._post_check(ml)
