"""FF-4 ③ 前馈计划消费（SPEC v1.3 §9.1-§9.2/§15 FF-4/§16.2-9/10/11/14）。

覆盖：默认路径 byte-exact 回归锚（不绑计划=FF1 收官态，layout sha 钉死）；
§9.1 证据字段齐全；六 hash 绑定与 stale/conflict 负例（stale→controls 不应用）；
controls 经 consumer gate（NEXT.md #6 已批）进入候选接受——escape 预留合成板
红→绿、走廊侵入启用、首选层前置、keepout 组电气邻件豁免、功率环路预算对账；
清单外 kind/未解析 target/同 target 冲突不静默；declared≠actually_read 分列；
核心产物禁区扫描；FF 模式双跑 byte-exact；CLI 退出码契约。
"""

import json

import pytest

from pcbflow import cli, config, coplace_cmd, envelope, ff_consume, geo, hashing

PLAN_PATH = "out/revc-ff1/feedforward-plan.json"
# FF1 收官态 layout（out/revc-ff1/layout.json）sha 锚：FF-4 不绑计划时不得漂移
LAYOUT_FF1_SHA = "28928d9b24a474b1db657e1985697d35611c5780ab696eb299be3bf19d47d7d9"


@pytest.fixture(scope="module")
def revc_ff():
    """Rev-C 全量 FF-4 消费跑（模块级一次）。"""
    return coplace_cmd.build_products("out/revc-ff2", ff_plan_path=PLAN_PATH)


# ---- 回归锚：默认路径 byte-exact（不绑计划=FF1 收官态） -------------------------
def test_default_layout_pinned_byte_exact():
    products = coplace_cmd.build_products()
    assert products["layout"]["sha256"] == LAYOUT_FF1_SHA
    assert "feedforward_consumption" not in products["layout"]["obj"]
    assert "ff_gate_details" not in products["layout"]["obj"]["evidence"]
    assert "ff_preferred_layers_applied" not in products["layer_plan"]["obj"]


# ---- §9.1 证据与六 hash 绑定 ---------------------------------------------------
def test_consumption_evidence_s91_fields(revc_ff):
    ev = revc_ff["layout"]["obj"]["feedforward_consumption"]
    for name in ("feedforward_plan_hash", "feedforward_registry_snapshot_hash",
                 "controls_declared_consumed", "controls_actually_read",
                 "controls_derived", "controls_ignored", "stale_plan_reason"):
        assert name in ev, name
    assert ev["plan_id"] == "FF-REVC-0001"
    assert ev["snapshot_check"]["all_match"] is True
    assert ev["stale_plan_reason"] is None and ev["conflict"] is None
    assert ev["application"]["applied"] is True
    assert ev["authority_effective"] == "upgraded_for_candidate_acceptance"
    assert ev["consumer_gate"]["approved"] is True
    assert len(ev["snapshot_check"]["checks"]) == 6  # §7.4 六 hash 逐键


def test_controls_24_consumed_2_ignored(revc_ff):
    ev = revc_ff["layout"]["obj"]["feedforward_consumption"]
    assert len(ev["controls_declared_consumed"]) == 24
    assert [i["control_id"] for i in ev["controls_ignored"]] == ["CTL-0022",
                                                                "CTL-0024"]
    assert all("§9.2" in i["reason"] for i in ev["controls_ignored"])
    assert ev["control_conflicts"] == []
    # 批注「逐条消费证据，禁静默全量吞」：24 条生效逐行（id/kind/target/applied_as）
    applied = ev["controls_applied"]
    assert len(applied) == 24
    assert {a["control_id"] for a in applied} == set(
        ev["controls_declared_consumed"])
    assert all(a["applied_as"] for a in applied)
    by_kind = {}
    for a in applied:
        by_kind[a["kind"]] = by_kind.get(a["kind"], 0) + 1
    assert by_kind == {"reserve_corridor": 7, "reserve_escape_slots": 7,
                       "assign_preferred_layer": 7, "protect_keepout": 2,
                       "protect_power_loop": 1}
    # consumer gate 三要素指针化（批注：过 gate 才生效）
    pc = ev["consumer_gate"]["promotion_check"]
    assert set(pc) >= {"synthetic_replay", "b_gate_zero_regression",
                       "revc_frozen_sanity", "verdict"}
    assert pc["verdict"].startswith("pass")


def test_d7_declared_actually_read_distinct(revc_ff):
    """§16.2-14：declared/actually_read/ignored 不混淆（实读⊇声明∪忽略且互斥）。"""
    ev = revc_ff["layout"]["obj"]["feedforward_consumption"]
    declared = set(ev["controls_declared_consumed"])
    ignored = {i["control_id"] for i in ev["controls_ignored"]}
    read = set(ev["controls_actually_read"])
    assert declared & ignored == set()
    assert (declared | ignored) == read == {
        c["control_id"]
        for c in json.load(open(PLAN_PATH, encoding=config.ENCODING))["controls"]}
    # D7：实读面带字段级登记（非静态照抄）
    assert all("field" in r for r in ev["consumption_contract"]["actually_read"])


def test_standalone_evidence_same_source(revc_ff):
    assert (revc_ff["ff_consumption"]["obj"]
            == revc_ff["layout"]["obj"]["feedforward_consumption"])


def test_no_forbidden_core_fields(revc_ff):
    assert envelope.scan_forbidden_core_fields(
        revc_ff["layout"]["obj"]) == []
    assert envelope.scan_forbidden_core_fields(
        revc_ff["ff_consumption"]["obj"]) == []


def test_ff_mode_double_run_byte_exact():
    a = coplace_cmd.build_products("out/revc-ff2", ff_plan_path=PLAN_PATH)
    b = coplace_cmd.build_products("out/revc-ff2", ff_plan_path=PLAN_PATH)
    assert a["layout"]["bytes"] == b["layout"]["bytes"]
    assert a["ff_consumption"]["bytes"] == b["ff_consumption"]["bytes"]


# ---- Rev-C 消费效果：门证据/层计划/envelope ------------------------------------
def test_revc_ff_gate_evidence(revc_ff):
    lay = revc_ff["layout"]["obj"]
    assert "escape_slot_reservation" in lay["evidence"]["hard_gates"]
    assert lay["evidence"]["verdict"] == "red"  # 冻结基线证据（非布局修改请求）
    det = lay["evidence"]["ff_gate_details"]
    assert len(det["escape_slot_reservation"]["rows"]) == 7  # 七个赤字逃逸场
    enforced = {r["bus_id"]: r for r in det["channel_intruders"]}
    assert all(r["intruder_check"] == "enforced"
               for r in det["channel_intruders"])  # 7 走廊预留全部启用
    assert any(r["intruders"] for r in det["channel_intruders"])  # 冻结板有侵入
    assert "power_loop_budget" in det
    assert det["power_loop_budget"]["limit_matches_config"] is True


def test_revc_layer_plan_pref_override(revc_ff):
    lp = revc_ff["layer_plan"]["obj"]
    applied = lp["ff_preferred_layers_applied"]
    assert len(applied) == 7 and set(applied.values()) == {"In2.Cu"}
    by_bus = {b["bus_id"]: b for b in lp["buses"]}
    assert by_bus["BUS_FMC"]["segments"][0]["layer"] == "In2.Cu"  # 原 F.Cu 首选
    # registry allowed_layers 权威不受计划偏好覆盖（BUS_USB 仍按允许层）
    assert by_bus["BUS_USB"]["segments"][0]["layer"] in \
        by_bus["BUS_USB"]["allowed_layers"]


def test_revc_envelope_ff_fields(revc_ff):
    env = revc_ff["envelope"]["obj"]
    assert env["status"] == "ok"
    m = env["metrics"]
    assert m["ff_plan_consumed"] is True and m["ff_stale_plan"] is False
    assert m["ff_controls_applied"] == 24 and m["ff_controls_ignored"] == 2
    assert m["optimization_applied"] is False  # 优化仍待确认点 #4
    assert any(d["id"] == "ff4_consumer_gate" for d in env["diagnostics"])


# ---- stale / conflict 负例（纯函数级） ------------------------------------------
def _snap(**over):
    base = {k: "H_" + k for k in
            ("registry_snapshot_hash", "structures_sha256", "constraints_sha256",
             "placement_snapshot_sha256", "board_snapshot_sha256",
             "feedforward_config_sha256")}
    base.update(over)
    return base


def test_snapshot_binding_stale_and_conflict():
    plan = {"snapshot": _snap(board_snapshot_sha256="H_other")}
    cur = _snap()
    b = ff_consume.snapshot_binding(plan, cur)
    assert b["stale_plan"] is True
    assert b["stale_plan_reason"] == ["snapshot_hash_mismatch:"
                                      "board_snapshot_sha256"]
    assert b["conflict_keys"] == ["board_snapshot_sha256"]  # §9.4 报告不择一
    assert b["conflict"]["resolution"].startswith("报告不择一")
    ok = ff_consume.snapshot_binding({"snapshot": _snap()}, _snap())
    assert ok["all_match"] is True and ok["stale_plan"] is False


def test_interpret_conflicts_not_silent():
    plan = {"controls": [
        {"control_id": "CTL-A", "kind": "reserve_corridor", "target": "bus:B1",
         "action": {"reserve_width_mm": 1.0}},
        {"control_id": "CTL-B", "kind": "reserve_corridor", "target": "bus:B1",
         "action": {"reserve_width_mm": 2.0}},  # 同 target 同 kind 动作不同
        {"control_id": "CTL-C", "kind": "set_route_order", "target": "board:x",
         "action": {"route_order": []}},
    ]}
    ext, _applied, ignored, conflicts = ff_consume.interpret_controls(
        plan, shape_refs=set(), corridor_bus_ids=["B1"], reads=[])
    assert len(conflicts) == 1
    ids = {i["control_id"] for i in ignored}
    assert ids == {"CTL-A", "CTL-B", "CTL-C"}  # 冲突双方不静默择一
    assert ext["reserve_corridor_buses"] == []


def test_interpret_unresolved_and_unconsumable():
    plan = {"controls": [
        {"control_id": "CTL-U1", "kind": "reserve_corridor",
         "target": "bus:BUS_NOPE", "action": {}},
        {"control_id": "CTL-U2", "kind": "reserve_escape_slots",
         "target": "field:ZZ|N", "action": {}},
        {"control_id": "CTL-U3", "kind": "protect_keepout",
         "target": "zone:zz", "action": {"refs": ["NOPE"], "keepout_mm": 3.0}},
        {"control_id": "CTL-U4", "kind": "assign_preferred_layer",
         "target": "bus:B1", "action": {"preferred_layer": "In1.Cu"}},
        {"control_id": "CTL-U5", "kind": "reserve_return_stitching",
         "target": "board:x", "action": {}},
    ]}
    ext, applied, ignored, _ = ff_consume.interpret_controls(
        plan, shape_refs={"U1"}, corridor_bus_ids=["B1"], reads=[])
    assert {i["control_id"] for i in ignored} == {
        "CTL-U1", "CTL-U2", "CTL-U3", "CTL-U4", "CTL-U5"}
    assert ext["escape_fields"] == [] and ext["keepout_groups"] == []
    assert applied == []  # 全部未生效逐条可见（禁静默全量吞）


# ---- 合成板：控制进入候选接受（红→绿） ------------------------------------------
def _mk(ref, lib, pads):
    return {"ref": ref, "lib": lib, "x": 0.0, "y": 0.0, "rot": 0.0,
            "pads": [{"ref": ref, "num": n, "net": net, "x": x, "y": y,
                      "w": w, "h": h} for (n, net, x, y, w, h) in pads]}


def _place(fp, x, y, rot=0.0):
    import math
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    for p in fp["pads"]:
        dx, dy = p["x"], p["y"]
        p["x"] = x + dx * c + dy * s
        p["y"] = y + dy * c - dx * s
    fp["x"], fp["y"], fp["rot"] = x, y, rot
    return fp


def _icap(ref, net, x, y):
    return _place(_mk(ref, "C_0402", [
        ("1", net, -0.5, 0.0, 0.5, 0.6), ("2", "GND", 0.5, 0.0, 0.5, 0.6)]), x, y)


def _ires(ref, x, y):
    return _place(_mk(ref, "R_0603", [
        ("1", "NETX", -0.5, 0.0, 0.5, 0.6), ("2", "NETY", 0.5, 0.0, 0.5, 0.6)]),
        x, y)


def _finalize(fp):
    board = geo.finalize_board(dict(fp))
    for f in board["footprints"].values():
        f["lib"] = next(x["lib"] for x in fp.values() if x["ref"] == f["ref"])
    return board


def _escape_board():
    """U1（锚件，北排双 3V3 引脚）+ 去耦 C1（同网=豁免，就近绿）+ 无关件 R9
    （侵入北逃逸带 1.1mm）。红种子只有 escape 门：C1 双 3V3 距 ≤0.7mm（proximity
    绿）、C1/U1/R9 互不重叠（spacing 绿）；R9 北移 2mm 即出带（一阶可解）。"""
    fp = {"U1": _place(_mk("U1", "IC8", [
        ("1", "3V3", -1.0, -2.0, 0.6, 0.4), ("2", "3V3", 1.0, -2.0, 0.6, 0.4),
        ("3", "F0", -1.0, 2.0, 0.6, 0.4), ("4", "F1", 1.0, 2.0, 0.6, 0.4),
        ("5", "GND", -1.0, 0.0, 0.6, 0.4), ("6", "GND", 1.0, 0.0, 0.6, 0.4),
        ("7", "GND", 0.0, -1.0, 0.6, 0.4), ("8", "GND", 0.0, 1.0, 0.6, 0.4)]),
        20.0, 20.0)}
    fp["C1"] = _icap("C1", "3V3", 20.0, 16.8)   # 带 14.8..17.8 内；同 3V3 → 豁免
    fp["R9"] = _ires("R9", 20.0, 15.6)          # 带 14.8..17.8 内；非邻件 → 侵入
    structures = {"anchors": [{"ref": "U1"}],
                  "power_tree": {"rails": []}, "buses": []}
    ff = {"escape_fields": [{"control_id": "CTL-T0001", "ref": "U1", "side": "N",
                             "reserve_channels": 9, "deficit_channels": 2}]}
    return _finalize(fp), structures, ff


def _ctx_of(board, structures, ff, **kw):
    return coplace_cmd.build_context(
        board, structures, None, {}, "synthetic-reg-hash",
        board_rect=(0.0, 0.0, 40.0, 40.0), ff_controls=ff, **kw)


def test_escape_reservation_gate_and_optimizer_clears():
    board, structures, ff = _escape_board()
    ctx = _ctx_of(board, structures, ff)
    st = coplace_cmd.state_from_board(board)
    ev = coplace_cmd.evaluate(ctx, st)
    assert "escape_slot_reservation" in ev["hard_fail_gates"]
    rows = {r["field"]: r for r in
            ev["hard"]["escape_slot_reservation"]["rows"]}
    assert [i["ref"] for i in rows["U1|N"]["intruders"]] == ["R9"]  # C1 豁免
    assert ev["hard"]["escape_slot_reservation"]["magnitude_mm"] > 0
    # controls 进入候选接受：爬山把非锚件清出预留带（红→绿）
    st2, _sk, trace = coplace_cmd.optimize(ctx, st, max_sweeps=20)
    ev2 = coplace_cmd.evaluate(ctx, st2)
    assert ev2["hard"]["escape_slot_reservation"]["pass"] is True
    assert trace["final_verdict"] == "pass"
    assert st2["U1"] == st["U1"]  # 锚件零移动


def test_escape_gate_absent_without_plan():
    board, structures, _ff = _escape_board()
    ctx = _ctx_of(board, structures, None)
    ev = coplace_cmd.evaluate(ctx, coplace_cmd.state_from_board(board))
    assert "escape_slot_reservation" not in ev["hard"]


def _corridor_board():
    """U1/U2 锚件上下排（x 重叠）+ BUS_T 走廊带内无关侵入件 R8。"""
    def ic(ref, y, nets):
        pads = []
        for i, net in enumerate(nets):
            pads.append((str(i + 1), net, -1.6 + (i % 4) * 1.0,
                         -0.6 + (i // 4) * 1.2, 0.6, 0.4))
        return _place(_mk(ref, "IC8", pads), 20.0, y)
    fp = {"U1": ic("U1", 20.0, ["T0", "T1", "3V3", "GND", "GND", "GND", "GND",
                                "GND"]),
          "U2": ic("U2", 40.0, ["T0", "T1", "GND", "GND", "GND", "GND", "GND",
                                "GND"]),
          "R8": _ires("R8", 20.0, 30.0)}
    structures = {"anchors": [{"ref": "U1"}, {"ref": "U2"}],
                  "power_tree": {"rails": []},
                  "buses": [{"bus_id": "BUS_T", "members": ["T0", "T1"],
                             "member_count": 2, "endpoint_refs": ["U1", "U2"],
                             "symmetry_class": None}]}
    seed = {"buses": [
        {"bus_id": "BUS_T",
         "endpoints": [{"ref": "U1", "dominant_exit_side": "S"},
                       {"ref": "U2", "dominant_exit_side": "N"}],
         "corridor": {"object": "U1-U2", "demand_width_mm": 2.0,
                      "formula": "C-0053"}}],
        "registry_snapshot_hash": "synthetic-seed-hash"}
    return _finalize(fp), structures, seed


def test_reserve_corridor_enables_intruder_enforcement():
    board, structures, seed = _corridor_board()
    st = coplace_cmd.state_from_board(board)
    plain = coplace_cmd.build_context(
        board, structures, seed, {"T0": "N01", "T1": "N02"}, "h",
        board_rect=(0.0, 0.0, 40.0, 40.0))
    row = coplace_cmd.channel_check(plain, st)["rows"][0]
    assert row["intruder_check"].startswith("not_enforced")
    assert row["ok"] is True
    ff_ctx = coplace_cmd.build_context(
        board, structures, seed, {"T0": "N01", "T1": "N02"}, "h",
        board_rect=(0.0, 0.0, 40.0, 40.0),
        ff_controls={"reserve_corridor_buses": ["BUS_T"]})
    row2 = coplace_cmd.channel_check(ff_ctx, st)["rows"][0]
    assert row2["intruder_check"] == "enforced"
    assert row2["intruders"] == ["R8"] and row2["ok"] is False
    assert row2["intruder_magnitude_mm"] > 0


def test_preferred_layer_override_per_bus():
    board, structures, seed = _corridor_board()
    kw = dict(zip(("board", "structures", "seed"), (board, structures, seed)))
    ranks = ["F.Cu=逃逸≤3mm+关键短距（软）", "In2.Cu=主干",
             "B.Cu=批准电源短跳", "In1.Cu=GND 禁信号"]  # 全局 rank：F.Cu 首选
    plain = coplace_cmd.build_context(
        net_ids={"T0": "N01", "T1": "N02"}, registry_snapshot_hash="h",
        layer_preference_ranks=ranks, board_rect=(0.0, 0.0, 40.0, 40.0), **kw)
    assert coplace_cmd.layer_plan_of(plain)["buses"][0]["segments"][0][
        "layer"] == "F.Cu"  # 全局 rank 首选
    assert "ff_preferred_layers_applied" not in coplace_cmd.layer_plan_of(plain)
    ff_ctx = coplace_cmd.build_context(
        net_ids={"T0": "N01", "T1": "N02"}, registry_snapshot_hash="h",
        layer_preference_ranks=ranks, board_rect=(0.0, 0.0, 40.0, 40.0),
        ff_controls={"preferred_layers": {"BUS_T": "In2.Cu"}}, **kw)
    lp = coplace_cmd.layer_plan_of(ff_ctx)
    assert all(s["layer"] == "In2.Cu"
               for s in lp["buses"][0]["segments"])
    assert lp["ff_preferred_layers_applied"] == {"BUS_T": "In2.Cu"}


def test_keepout_group_exempts_members_and_bonded():
    board, structures, _ = _corridor_board()
    ctx = coplace_cmd.build_context(
        board, structures, None, {}, "h", board_rect=(0.0, 0.0, 40.0, 40.0),
        ff_controls={"keepout_groups": [
            {"control_id": "CTL-T0002", "scope": "power_SW", "refs": ["U2"],
             "keepout_mm": 3.0}]})
    st = coplace_cmd.state_from_board(board)
    st["R8"]["y"] = coplace_cmd.q(37.0)  # 挪进 U2 3mm 净空（35.95..44.05）
    ko = coplace_cmd.keepout_check(ctx, st)
    ff_hits = [i for i in ko["intrusions"]
               if i["kind"] == "ff_keepout:power_SW"]
    assert any(i["ref"] == "R8" for i in ff_hits)      # 无关件计入
    assert all(i["ref"] == "R8" for i in ff_hits)      # U1=组员电气邻件豁免


def test_power_loop_budget_reconciliation():
    board, structures, seed = _corridor_board()
    ctx = coplace_cmd.build_context(
        board, structures, seed, {}, "h", board_rect=(0.0, 0.0, 40.0, 40.0),
        power_chain={"buck": "U1", "inductor": "U2"},
        ff_controls={"power_loop": {"control_id": "CTL-T0003",
                                    "refs": ["U1", "U2"],
                                    "budget_mm": [15, 10], "limit_mm": [20, 12],
                                    "keep_refs_adjacent": True}})
    row = coplace_cmd.buck_loop_check(
        ctx, coplace_cmd.state_from_board(board))
    att = row["ff_budget_attainment"]
    assert att["control_id"] == "CTL-T0003"
    assert att["limit_matches_config"] is True  # 计划限值=config（不静默覆盖）
    assert att["budget_mm"] == [15, 10]


# ---- CLI 退出码契约 -------------------------------------------------------------
def test_cli_ff_consumption_requires_plan(capsys):
    rc = cli.main(["co-place", "--select", "ff_consumption"])
    out = capsys.readouterr().out
    assert rc == config.EXIT_FAILED
    assert '"status": "failed"' in out and "--feedforward-plan" in out


def test_cli_ff_mode_exit_ok(capsys):
    rc = cli.main(["co-place", "--select", "ff_consumption",
                   "--feedforward-plan", PLAN_PATH,
                   "--out-dir", "out/revc-ff2"])
    out = capsys.readouterr().out
    assert rc == config.EXIT_OK
    assert '"FF-REVC-0001"' in out
    assert '"upgraded_for_candidate_acceptance"' in out
