"""pcbflow.v4_1 E2 多层合成场景族全链测试（f9/f10；任务书 §3 E2 G2.1）。"""

from __future__ import annotations

import pytest

from pcbflow.v4_1.canonical import dumps_canonical
from pcbflow.v4_1.mlchain import (check_ml_solution, mlboard_to_v4exp_board,
                                  solve_ml)
from pcbflow.v4_1.mlfamily import (ML_LAYERS, ML_RULES, generate_all_ml,
                                   generate_ml_scenario, scenario_ids_ml,
                                   validate_mlboard)

_SAT_IDS = ("dev-f9-01", "dev-f10-01")
_UNSAT_IDS = ("hol-f10-09", "hol-f10-10")


# ---------------------------------------------------------------- 生成

def test_family_shape_deterministic():
    ids = scenario_ids_ml()
    assert len(ids) == 20
    assert sorted({fam for _, fam, _, _ in ids}) == ["f10", "f9"]
    splits = {sid.split("-")[0] for sid, _, _, _ in ids}
    assert splits == {"dev", "cal", "hol"}
    for sid, fam, split, serial in ids:
        ml = generate_ml_scenario(sid)
        assert ml["scenario_id"] == sid
        assert ml["family"] == fam
        assert ml["split"] == split
        assert ml["board"]["layers"] == ML_LAYERS          # 4 层
        assert ml["rules"] == ML_RULES
        assert validate_mlboard(ml) == []


def test_generation_determinism_same_bytes():
    a = generate_ml_scenario("dev-f9-01")
    b = generate_ml_scenario("dev-f9-01")
    assert dumps_canonical(a) == dumps_canonical(b)
    all_a = dumps_canonical(generate_all_ml())
    all_b = dumps_canonical(generate_all_ml())
    assert all_a == all_b


def test_f9_cross_layer_endpoints_and_inner_walls():
    ml = generate_ml_scenario("dev-f9-01")
    by_id = {p["pad_id"]: p for p in ml["pads"]}
    for n in ml["nets"]:
        a, b = (by_id[e] for e in n["endpoints"])
        assert {a["layer"], b["layer"]} == {"F.Cu", "B.Cu"}  # 跨外层端点
    for k in ml["keepouts"]:
        assert set(k["layers"]) == {"In1.Cu", "In2.Cu"}      # 内层墙


def test_f10_unsat_ring_on_all_layers():
    ml = generate_ml_scenario("hol-f10-09")
    assert ml["label"] == "unsatisfiable"
    for k in ml["keepouts"]:
        assert set(k["layers"]) == set(ML_LAYERS)            # 全层围死


def test_validator_fail_closed():
    ml = generate_ml_scenario("dev-f9-01")

    def bad(**kw):
        obj = dict(ml)
        obj.update(kw)
        return validate_mlboard(obj)

    assert bad(family="f1")                                  # 非多层族
    assert bad(split="train")
    assert bad(label="maybe")
    b2 = dict(ml)
    b2["board"] = dict(ml["board"])
    b2["board"]["layers"] = ["F.Cu", "B.Cu"]
    assert validate_mlboard(b2)                              # 2 层非法
    b3 = dict(ml)
    b3["rules"] = dict(ML_RULES, clearance_mm=0.3)
    assert validate_mlboard(b3)                              # 规则冻结
    b4 = dict(ml)
    b4["pads"] = [dict(p, layer="In9.Cu") for p in ml["pads"]]
    assert validate_mlboard(b4)                              # pad 层非法
    b5 = dict(ml)
    b5["keepouts"] = [dict(k, layers=["In9.Cu"]) for k in ml["keepouts"]]
    assert validate_mlboard(b5)
    b6 = dict(ml)
    b6["nets"] = [dict(n, net_class="power") for n in ml["nets"]]
    assert validate_mlboard(b6)


# ---------------------------------------------------------------- 求解适配

def test_mlboard_to_v4exp_board_projection():
    ml = generate_ml_scenario("dev-f9-01")
    board = mlboard_to_v4exp_board(ml)
    assert board["schema"] == "pcbflow.v4exp.board/1"
    assert "ml_meta" not in board
    assert board["board"]["layers"] == ML_LAYERS
    assert board["scenario_id"] == ml["scenario_id"]
    assert board["pads"] == ml["pads"]
    assert board["rules"]["allowed_layers"]["clock"] == ["F.Cu", "B.Cu"]


@pytest.mark.parametrize("sid", _SAT_IDS)
def test_solve_sat_with_layer_transitions(sid):
    ml = generate_ml_scenario(sid)
    run = solve_ml(ml)
    assert run["status"] == "sat"
    assert run["metrics"]["all_connected"] is True
    assert sum(run["metrics"]["violations"].values()) == 0
    assert len(run["vias"]) > 0                              # 换层必经 via
    for v in run["vias"]:
        # via 跨度层均在 4 层栈内（贯通孔 F..B）
        assert {v["from_layer"], v["to_layer"]} <= set(ML_LAYERS)


@pytest.mark.parametrize("sid", _UNSAT_IDS)
def test_solve_unsat_reported_honestly(sid):
    ml = generate_ml_scenario(sid)
    run = solve_ml(ml)
    assert run["status"] == "failed"                         # 不渲染 sat
    assert run["metrics"]["unconnected"] >= 1


# ---------------------------------------------------------------- 检查腿

@pytest.mark.parametrize("sid", _SAT_IDS + _UNSAT_IDS)
def test_check_ml_solution_gate(sid):
    ml = generate_ml_scenario(sid)
    run = solve_ml(ml)
    rec = check_ml_solution(ml, run)
    assert rec["gate_pass"] is True
    chk = rec["check"]
    assert chk["via_span_illegal"] == []
    assert chk["layer_illegal"] == []
    assert chk["width_illegal"] == []
    assert chk["clearance_hard_violations"] == []
    assert chk["cross_engine_disagreements"] == []           # 双引擎同判
    assert "pair_stats" in chk                               # 剪枝登记不静默
    if ml["label"] == "satisfiable":
        assert rec["solver"]["status"] == "sat"
    else:
        assert rec["solver"]["status"] == "failed"


def test_check_detects_injected_violation():
    """检查腿有牙齿：注入跨网间距违例必须被查出（防恒绿）。"""
    ml = generate_ml_scenario("dev-f9-01")
    run = solve_ml(ml)
    # 注入：把第一条 route 复制为异网 route，同层贴近（0.1mm 间距）
    src = run["routes"][0]
    clone = dict(src)
    clone["route_id"] = "nX-S01"
    clone["polyline_mm"] = [[p[0], p[1] + 0.3] for p in src["polyline_mm"]]
    run2 = dict(run)
    run2["routes"] = run["routes"] + [clone]
    rec = check_ml_solution(ml, run2)
    assert rec["check"]["clearance_hard_violations"], "注入违例未被查出"
    hard = rec["check"]["clearance_hard_violations"][0]
    assert hard["pred_clearance_mm"] == pytest.approx(0.1, abs=0.01)
    assert rec["gate_pass"] is False


def test_check_layer_illegal_detection():
    """检查腿牙齿 2：clock 网跑到内层必须被查出（allowed_layers 语义）。"""
    ml = generate_ml_scenario("dev-f9-01")
    run = solve_ml(ml)
    clock_nets = {n["net_id"] for n in ml["nets"]
                  if n["net_class"] == "clock"}
    if not clock_nets:
        pytest.skip("本场景无 clock 网")
    run2 = dict(run)
    run2["routes"] = []
    for r in run["routes"]:
        r2 = dict(r)
        if str(r["route_id"]).rsplit("-S", 1)[0] in clock_nets:
            r2["layer"] = "In1.Cu"        # clock 限 [F.Cu, B.Cu]
        run2["routes"].append(r2)
    rec = check_ml_solution(ml, run2)
    assert rec["check"]["layer_illegal"]
    assert rec["gate_pass"] is False
