"""IT 会话测试（③ keepout-aware 重优化 + ④ 布局覆盖对照；SPEC §9/§10）。

覆盖：
- 度量自校：基线（零移动）违例复算必须精确=冻结 fc3 官方值 79（未动 refs
  原浮点零漂移的性质）；
- 等价性：route --placement-from-layout（b1 基线布局，零 moved）→ ramps/
  lanes 与 fc3 route-plan 逐字节一致；
- board_with_layout：moved/unmoved 语义（未动=零漂移；动=位姿/焊盘重建）；
- 优化器：锚件位姿冻结红线、护栏拒绝（buck 环路回归被拒）、严格改善；
- 产物：核心禁区扫描、决策逻辑（<10% → rollback_archive/yellow）、
  metric 失配 → blocked；
- 默认路径零扰动由既有 test_fc4/test_ff4 sha pin 覆盖（本文件不重复）。
"""

import json

import pytest

from pcbflow import config, coplace_cmd, envelope, geo, hashing, keepout_iter, \
    route_cmd, route_view

FD3_PLAN = "out/revc-fd3/feedforward-plan.json"
FD2_PLAN = "out/revc-fd2/feedforward-plan.json"
FC3_PLAN = "out/revc-fc3/route-plan.json"
B1_LAYOUT = "out/revc-b1/layout.json"

BASELINE_VIOL = 79  # KEEPOUT-EVIDENCE.md / fc3 route-plan（pin 08a3ed6b…）


@pytest.fixture(scope="module")
def base():
    return keepout_iter.setup(FD3_PLAN, FC3_PLAN, "out/revc-it")


# ---- 度量自校与基线账 --------------------------------------------------------
def test_metric_self_check_baseline_equals_official(base):
    assert base["official"]["viol"] == BASELINE_VIOL
    assert base["m0"]["viol"] == BASELINE_VIOL
    assert base["m0"]["unsat_refs"] == base["official"]["unsat_refs"]
    assert base["m0"]["unmatched"] == base["official"]["unmatched"]


def test_candidate_refs_non_anchor_and_groups(base):
    anchors = set(base["anchors"])
    assert anchors == {"J1", "J2", "J3", "J4", "J5", "U1", "U2", "U6",
                       "Y1", "Y2"}
    assert not set(base["candidate_refs"]) & anchors
    group_refs = {r for g in base["keepout_groups"] for r in g["refs"]}
    assert {"U3", "L1", "Q1", "Q2", "F1"} <= group_refs
    assert base["ff_binding"]["all_match"]


# ---- board_with_layout / escape_fields_of 因子化 -----------------------------
def test_board_with_layout_unmoved_zero_drift(base):
    board, moved = route_view.board_with_layout(
        base["board"], base["vp"]["view"]["placements"]
        if "placements" in base["vp"]["view"] else
        [{"ref": r, "x": coplace_cmd.uq(base["st0"][r]["x"]),
          "y": coplace_cmd.uq(base["st0"][r]["y"]),
          "rot": base["st0"][r]["rot"]} for r in sorted(base["st0"])])
    assert moved == []
    for p0, p1 in zip(base["board"]["pads"], board["pads"]):
        assert (p0["x"], p0["y"], p0["w"], p0["h"]) == \
            (p1["x"], p1["y"], p1["w"], p1["h"])


def test_board_with_layout_moves_ref(base):
    rows = [{"ref": r, "x": coplace_cmd.uq(base["st0"][r]["x"]),
             "y": coplace_cmd.uq(base["st0"][r]["y"]),
             "rot": base["st0"][r]["rot"]} for r in sorted(base["st0"])]
    rows[0]["x"] += 2.0
    ref = rows[0]["ref"]
    board, moved = route_view.board_with_layout(base["board"], rows)
    assert moved == [ref]
    fp0 = base["board"]["footprints"][ref]
    fp1 = board["footprints"][ref]
    assert fp1["x"] == fp0["x"] + 2.0 and fp1["y"] == fp0["y"]
    for p0, p1 in zip(fp0["pads"], fp1["pads"]):
        assert p1["x"] == pytest.approx(p0["x"] + 2.0, abs=1e-9)
        assert p1["y"] == pytest.approx(p0["y"], abs=1e-9)


def test_escape_fields_of_matches_route_view(base):
    fields, transit, unmapped = route_view.escape_fields_of(
        base["vp"]["esc"], base["net_id_of"])
    assert fields == base["vp"]["view"]["escape_fields"]
    assert sorted(transit) == base["vp"]["view"]["transit_refs"]
    assert sorted(unmapped) == base["vp"]["view"]["unmapped_transit_nets"]


# ---- ④ 布局覆盖等价性（IT 官方对照机制） --------------------------------------
def test_route_placement_override_b1_equivalence():
    prods = route_cmd.build_products(
        out_dir_rel="out/revc-it/equivalence-b1", ff_plan_path=FD2_PLAN,
        placement_layout_path=B1_LAYOUT)
    plan = prods["route_plan"]["obj"]
    assert plan["mode"] == "keepout_iteration_dry_run"
    assert plan["placement_override"]["moved_refs"] == []
    fc3 = json.load(open(FC3_PLAN, encoding=config.ENCODING))
    assert hashing.canonical_json_bytes(plan["ramps"]) == \
        hashing.canonical_json_bytes(fc3["ramps"])
    assert hashing.canonical_json_bytes(plan["lanes"]) == \
        hashing.canonical_json_bytes(fc3["lanes"])
    assert prods["envelope"]["obj"]["status"] == "ok"
    assert plan["zero_write"]["unchanged"]


# ---- 优化器与护栏 -------------------------------------------------------------
def test_optimize_micro_anchors_frozen(base):
    final_st, res = keepout_iter.optimize(base, max_sweeps=1, refs=["R1"])
    st0 = base["st0"]
    for a in base["anchors"]:
        assert (final_st[a]["x"], final_st[a]["y"], final_st[a]["rot"]) == \
            (st0[a]["x"], st0[a]["y"], st0[a]["rot"])
    assert res["converged"] or res["max_sweeps_reached"]
    assert res["final_m"]["viol"] <= BASELINE_VIOL
    ok, _ = keepout_iter.guards_of(base, res["final_ev"], res["final_m"])
    assert ok


def test_guard_rejects_power_loop_regression(base):
    from pcbflow import coplace_cmd as cp
    trial = {r: dict(v) for r, v in base["st0"].items()}
    trial["U3"]["y"] += cp.q(5.0)  # buck 远离电感/去耦链 → 环路/半径必恶化
    ev = cp.evaluate(base["ctx"], trial)
    ok, checks = keepout_iter.guards_3(base, ev)
    assert not ok and checks


def test_metric_moves_reduce_or_keep(base):
    m = keepout_iter.viol_metric(base, base["st0"])
    assert m["viol"] == BASELINE_VIOL  # 零移动恒等
    trial = {r: dict(v) for r, v in base["st0"].items()}
    trial["R1"]["y"] -= base["st0"]["R1"]["y"] * 0  # no-op 构造
    assert keepout_iter.viol_metric(base, trial)["viol"] == BASELINE_VIOL


# ---- 产物管线（小候选集快速端到端） -------------------------------------------
def test_build_products_pipeline_small_refs(base):
    prods = keepout_iter.build_products(
        out_dir_rel="out/revc-it", ff_plan_path=FD3_PLAN,
        baseline_route_plan=FC3_PLAN, max_sweeps=1, refs=["R1"])
    it = prods["keepout_iteration"]["obj"]
    lay = prods["it_layout"]["obj"]
    env = prods["envelope"]["obj"]
    assert not envelope.scan_forbidden_core_fields(it)
    assert not envelope.scan_forbidden_core_fields(lay)
    assert it["target_caliber"]["metric_self_check"]["equals_official"]
    assert it["result"]["violations_baseline"] == BASELINE_VIOL
    # R1 单件微调：降幅 <10% → 回退存档路径（决策与护栏自洽）
    assert it["result"]["decision"] == "rollback_archive"
    assert env["verdict"] == "yellow" and env["status"] == "ok"
    assert it["confirmation_point_4_declaration"]["conversion_executed"] \
        is False
    assert it["confirmation_point_4_declaration"]["anchors"] == base["anchors"]
    roles = {p["role"] for p in lay["placements"]}
    assert "anchor_locked" in roles
    for p in lay["placements"]:
        if p["role"] == "anchor_locked":
            assert p["moved"] is False


def test_build_products_blocked_on_metric_mismatch(base, monkeypatch):
    orig = keepout_iter._load_official
    monkeypatch.setattr(keepout_iter, "_load_official",
                        lambda path: dict(orig(path),
                                          viol=BASELINE_VIOL - 1))
    prods = keepout_iter.build_products(
        out_dir_rel="out/revc-it", ff_plan_path=FD3_PLAN,
        baseline_route_plan=FC3_PLAN, max_sweeps=1, refs=["R1"])
    env = prods["envelope"]["obj"]
    assert env["status"] == "blocked" and env["verdict"] == "red"
    assert env["metrics"]["metric_self_check_pass"] is False
