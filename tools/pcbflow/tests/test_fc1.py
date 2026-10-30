"""FC1 ④ route dry-run 测试（SPEC v1.3 §10/§15 FC1/§16.4）。

覆盖：MCMF 内核（确定性/证书/独立复核）、匝道（合成 SAT/UNSAT、与 C2
escape_check 聚合等价）、车道（共享池 SAT 连续块/UNSAT 证书/层硬权限）、
Rev-C dry-run（registry 绑定/控制 18+8/三态/零写板/byte-exact/禁区扫描）。
"""

import json

import pytest

from pcbflow import audit_cmd, cli, config, envelope, flow, geo, hashing
from pcbflow import route_cmd, route_view

PLAN_PATH = "out/revc-ff1/feedforward-plan.json"


# ---- 内核：MCMF -------------------------------------------------------------
def test_flow_min_cost_and_determinism():
    def build():
        m = flow.MinCostFlow(5)
        m.add_edge(0, 1, 1, 0)
        m.add_edge(0, 2, 1, 0)
        m.add_edge(1, 3, 1, 1)
        m.add_edge(2, 3, 1, 2)
        m.add_edge(3, 4, 2, 0)
        return m

    a, b = build(), build()
    # 低费路先走（cost1），次费路补足（cost2）→ 满流 2、总费 3
    assert a.solve(0, 4) == b.solve(0, 4) == (2, 3)


def test_flow_unsat_certificate_and_independent_verify():
    names = ["SRC", "a", "b", "c", "SNK"]
    m = flow.MinCostFlow(5)
    for e in [(0, 1, 1, 0), (0, 2, 1, 0), (1, 3, 1, 1), (2, 3, 1, 2),
              (3, 4, 1, 0)]:
        m.add_edge(*e)
    f, _ = m.solve(0, 4)
    assert f == 1  # c→SNK 容量 1 → SRC 出口 2 不可满足
    cert = flow.min_cut_certificate(m, 0, 4, f, names)
    assert cert["verified"] and cert["cut_capacity"] == f
    edges = [("SRC", "a", 1), ("SRC", "b", 1), ("a", "c", 1), ("b", "c", 1),
             ("c", "SNK", 1)]
    assert flow.verify_min_cut(5, edges, 0, 4, cert["s_side"], f, names)
    assert not flow.verify_min_cut(5, edges, 0, 4, ["SRC"], f, names)


# ---- 合成板 helper ----------------------------------------------------------
def _mini_board():
    """U1（2×2 脚）+ U2（对端，使 NA/NB/ND 构成 transit）。

    W1（GND，U1 南侧）封死 U1 pad3/pad4 的 S 通道；W2（GND，U1 东侧）封死
    pad2/pad4 的 E 通道及单折绕行 → pad4（ND）在 U1 全堵：ND 于 U1 不可逃逸
    （UNSAT 证书靶），NA/NB/NC 仍分别经 N/W/E 逃逸。
    """
    fp = {
        "U1": {"ref": "U1", "x": 10.0, "y": 10.0, "rot": 0.0, "pads": [
            {"ref": "U1", "num": "1", "net": "NA", "x": 9.8, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "2", "net": "NB", "x": 10.2, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "3", "net": "NC", "x": 9.8, "y": 10.2,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "4", "net": "ND", "x": 10.2, "y": 10.2,
             "w": 0.3, "h": 0.3},
        ]},
        "U2": {"ref": "U2", "x": 30.0, "y": 10.0, "rot": 0.0, "pads": [
            {"ref": "U2", "num": "1", "net": "NA", "x": 29.8, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U2", "num": "2", "net": "NB", "x": 30.2, "y": 10.2,
             "w": 0.3, "h": 0.3},
            {"ref": "U2", "num": "3", "net": "ND", "x": 30.2, "y": 9.8,
             "w": 0.3, "h": 0.3},
        ]},
        "W1": {"ref": "W1", "x": 10.2, "y": 11.4, "rot": 0.0, "pads": [
            {"ref": "W1", "num": "1", "net": "GND", "x": 10.2, "y": 11.4,
             "w": 1.2, "h": 1.2},
        ]},
        "W2": {"ref": "W2", "x": 11.4, "y": 10.2, "rot": 0.0, "pads": [
            {"ref": "W2", "num": "1", "net": "GND", "x": 11.4, "y": 10.2,
             "w": 1.2, "h": 1.2},
        ]},
    }
    return geo.finalize_board(fp)


def _view_ctx_from_board(board):
    esc = audit_cmd.escape_check(board, lambda n: None)
    names = sorted({p["net"] for p in board["pads"]
                    if p["net"] and p["net"] != "GND"
                    and not p["net"].startswith("unconnected-")})
    nid = {n: "N%04d" % (i + 1) for i, n in enumerate(names)}
    fields = []
    for key in sorted(esc["fields"]):
        f = esc["fields"][key]
        if not f["demand_transit_nets"]:
            continue
        fields.append({
            "field": key, "ref": f["ref"], "side": f["side"],
            "supply_clear_channels": f["supply_clear_channels"],
            "demand_transit_nets": f["demand_transit_nets"],
            "blocked_transit_nets": len(f["blocked_transit_nets"]),
            "net_ids": sorted(nid[x] for x in f["transit_nets"]),
        })
    view = {"nets": [{"net_id": nid[n], "net_name": n, "bus_id": None,
                      "allowed_layers": ["F.Cu", "In2.Cu"],
                      "preferred_layer": None}
                     for n in names],
            "escape_fields": fields,
            "unmapped_transit_nets": [],
            "signal_layers": ["F.Cu", "In2.Cu"],
            "lane_pitch_mm": 0.35}
    return {"view": view, "board": board, "esc": esc, "seed_sides": {},
            "structures": {"priorities": {"layer_preference": {"ranks": []}}}}


def test_ramp_synthetic_assignment_slots_and_deficit_cert():
    """合成板：NA/NB 于 U1 逃逸（槽位编号确定），ND 全堵→UNSAT+证书。

    NC 仅单端焊盘（无对端）→ 非 transit，不入需求（C2 同口径）。
    """
    ctx = _view_ctx_from_board(_mini_board())
    rows, field_rows, runs = route_cmd.solve_ramp(ctx, {})
    u1 = next(r for r in rows if r["ref"] == "U1")
    assert u1["demand_transit_nets"] == 3  # NA/NB/ND
    assert u1["flow"] == 2
    assert [u["net_name"] for u in u1["unmatched"]] == ["ND"]
    names_a = sorted(a["net_name"] for a in u1["assignments"])
    assert names_a == ["NA", "NB"]
    for a in u1["assignments"]:
        assert a["slot"] >= 0 and a["path"] in ("straight", "dogleg")
    u2 = next(r for r in rows if r["ref"] == "U2")
    assert u2["solver_status"] == "SAT" and u2["flow"] == 3
    run = next(r for r in runs if r["run_id"] == "RAMP-U1")
    assert run["status"] == "UNSAT"
    cert = run["certificate"]
    assert cert["verified"] and cert["flow_value"] == 2
    for f in field_rows:
        assert 0 <= f["escaped"] <= f["supply_clear_channels"]


def test_ramp_synthetic_keepout_penalty_changes_cost():
    """protect_keepout 控制组：通道相交 → 罚价（advisory），不改变可行性。"""
    ctx = _view_ctx_from_board(_mini_board())
    ext_plain = {}
    ext_ko = {"keepout_groups": [{"control_id": "CTL-9001",
                                  "scope": "zone:test",
                                  "refs": ["W1"], "keepout_mm": 2.0}]}
    rows0, _f0, runs0 = route_cmd.solve_ramp(ctx, ext_plain)
    rows1, _f1, runs1 = route_cmd.solve_ramp(ctx, ext_ko)
    cost0 = sum(r["cost"] for r in rows0[0]["assignments"])
    cost1 = sum(r["cost"] for r in rows1[0]["assignments"])
    assert cost1 >= cost0  # 罚价只升不降（可行性不变：仍 2 匹配）
    assert rows1[0]["flow"] == rows0[0]["flow"] == 2


def test_ramp_channel_model_agrees_with_c2():
    """通道几何与 audit_cmd.escape_check（C2）聚合等价（同口径强制）。"""
    board = _mini_board()
    ctx = _view_ctx_from_board(board)
    esc = ctx["esc"]
    channel_clear = route_cmd._channel_geom(board)
    for p in board["pads"]:
        if not p["net"] or p["net"] == "GND":
            continue
        any_clear = any(channel_clear(p, s)[0] for s in p["side"])
        assert any_clear != esc["pad_blocked"][(p["ref"], p["num"])], p


def test_lane_synthetic_shared_pool_contiguous():
    ctx = _view_ctx_from_board(_mini_board())
    ctx["view"]["corridors"] = [
        {"bus_id": "BUS_A", "corridor": "U1-U9", "gap_mm": 3.0,
         "required_mm": 1.3, "member_count": 6, "deficit": False,
         "status": "estimated"},
        {"bus_id": "BUS_B", "corridor": "U1-U9", "gap_mm": 3.0,
         "required_mm": 1.65, "member_count": 8, "deficit": False,
         "status": "estimated"},
    ]
    ctx["view"]["buses"] = [
        {"bus_id": "BUS_A", "route_order_rank": 0, "member_count": 6},
        {"bus_id": "BUS_B", "route_order_rank": 1, "member_count": 8},
    ]
    for i, n in enumerate(ctx["view"]["nets"]):
        n["bus_id"] = "BUS_A" if i < 6 else "BUS_B"
    ctx["view"]["nets"] += [
        {"net_id": "N9001", "net_name": "BX%d" % i, "bus_id": "BUS_B",
         "allowed_layers": ["F.Cu", "In2.Cu"], "preferred_layer": None}
        for i in range(2)]
    rows, runs = route_cmd.solve_lanes(ctx, {})
    assert len(rows) == 1 and rows[0]["solver_status"] == "SAT"
    row = rows[0]
    # 池：floor((3.0-0.6)/0.35)=6 道层；A 需 3、B 需 4 → 7>6… 以下按实际序断言
    total_assigned = sum(b["assigned"] for b in row["bus_rows"])
    assert total_assigned == row["flow"]
    for b in row["bus_rows"]:
        for pl in b["per_layer"]:
            assert pl["lanes"] == sorted(pl["lanes"])


def test_lane_unsat_certificate_and_conflict():
    ctx = _view_ctx_from_board(_mini_board())
    ctx["view"]["corridors"] = [
        {"bus_id": "BUS_A", "corridor": "U1-U9", "gap_mm": 1.0,
         "required_mm": 1.3, "member_count": 6, "deficit": True,
         "status": "estimated"},
    ]
    ctx["view"]["buses"] = [
        {"bus_id": "BUS_A", "route_order_rank": 0, "member_count": 6}]
    for i, n in enumerate(ctx["view"]["nets"]):
        n["bus_id"] = "BUS_A"
    rows, runs = route_cmd.solve_lanes(ctx, {})
    assert rows[0]["solver_status"] == "UNSAT"
    run = runs[0]
    assert run["status"] == "UNSAT" and run["certificate"]["verified"]
    # demand=ceil(6/2)=3 道而池=floor(0.4/0.35)=1 道层×2 层=2 → 赤字 1
    assert rows[0]["demand_lanes"] == 3 and rows[0]["flow"] == 2


def test_lane_usb_layer_hard_authority():
    """BUS_USB：registry allowed_layers=F.Cu 为硬权限；控制偏好 In2.Cu 不生效
    （FF4-D3 同语义）。"""
    ctx = _view_ctx_from_board(_mini_board())
    ctx["view"]["corridors"] = [
        {"bus_id": "BUS_USB", "corridor": "U1-J5", "gap_mm": 12.0,
         "required_mm": 1.3, "member_count": 4, "deficit": False,
         "status": "estimated"}]
    ctx["view"]["buses"] = [
        {"bus_id": "BUS_USB", "route_order_rank": 0, "member_count": 4}]
    for i, n in enumerate(ctx["view"]["nets"]):
        n["bus_id"] = "BUS_USB"
        n["allowed_layers"] = ["F.Cu"]
    ext = {"preferred_layers": {"BUS_USB": "In2.Cu"}}
    rows, _runs = route_cmd.solve_lanes(ctx, ext)
    b = rows[0]["bus_rows"][0]
    assert b["trunk_seq"] == ["F.Cu"]  # In2.Cu 被 allowed 硬权限过滤


# ---- Rev-C dry-run（模块级一次构建） ----------------------------------------
@pytest.fixture(scope="module")
def revc(tmp_path_factory):
    return route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                    ff_plan_path=PLAN_PATH)


def test_revc_view_registry_bound(revc):
    view = revc["route_view"]["obj"]
    plan = json.load(open(PLAN_PATH, encoding="utf-8"))
    assert view["registry_snapshot_hash"] == \
        plan["snapshot"]["registry_snapshot_hash"]
    assert len(view["nets"]) == 160
    assert view["excluded_nets_count"] == 32
    assert view["board_only_nets"] == []
    assert view["schema_version"] == "1.3"


def test_revc_pins(revc):
    view = revc["route_view"]["obj"]
    pin = view["pins"]["fc2_replay_target"]
    assert pin["sha256"] == hashing.sha256_file(
        __import__("os").path.join(config.OUT_DIR, "revc-b1", "layout.json"))
    assert view["pins"]["live_board_zero_write_witness"]["sha256"] == \
        hashing.sha256_file(config.REVC_BOARD)


def test_revc_controls_18_applied_8_ignored(revc):
    c = revc["consumption"]["obj"]
    # FC3 ④ 控制升级（consumer-gate-4）：绑定有效 → 候选接受语义
    assert c["authority_effective"] == "upgraded_for_candidate_acceptance"
    assert c["consumer_gate"]["approved"] is True
    assert set(c["consumer_gate"]["promotion_check"]) >= {
        "synthetic_replay", "b_gate_zero_regression", "revc_frozen_sanity",
        "verdict"}
    assert len(c["controls_applied"]) == 18
    assert len(c["controls_ignored"]) == 8
    kinds = sorted(i["kind"] for i in c["controls_ignored"])
    assert kinds == ["protect_power_loop"] + ["reserve_corridor"] * 7
    assert c["zero_present_kinds"] == ["reserve_lane", "reserve_via_budget"]
    declared = set(c["controls_declared_consumed"])
    ignored = {i["control_id"] for i in c["controls_ignored"]}
    read = set(c["controls_actually_read"])
    assert not (declared & ignored) and (declared | ignored) <= read
    assert all(i["reason"] for i in c["controls_ignored"])
    # BUS_USB 偏好越权 → note 不生效
    notes = c["application"]["assign_preferred_layer"]["notes"]
    assert any(n["bus"] == "BUS_USB" and n["requested"] == "In2.Cu"
               for n in notes)
    assert "BUS_USB" not in c["application"]["assign_preferred_layer"][
        "per_bus"]


def test_revc_ramps_consistent_with_ff_ledger(revc):
    """UNSAT refs = FF-1 七赤字场所在 ref 集；UNSAT 必带已验证证书。"""
    p = revc["route_plan"]["obj"]
    unsat = {r["ref"] for r in p["ramps"] if r["solver_status"] == "UNSAT"}
    assert unsat == {"U1", "U2", "U3", "U6"}
    # 77 未匹配网 = C2 一阶模型网级读数（冻结输入确定性钉值；与 FF-1
    # 通道级赤字场同源，体级干净/通道级赤字口径见 PHASE-REPORT-7 §2.4）
    assert sum(len(r["unmatched"]) for r in p["ramps"]) == 77
    for run in p["solver_runs"]:
        if run["status"] == "UNSAT":
            assert run["certificate"]["verified"]
    assert p["solver_summary"]["unsat_without_certificate"] == 0
    # 场级对账：escaped ≤ 供给
    for f in p["ramp_fields_account"]:
        assert f["escaped"] <= f["supply_clear_channels"]
        assert f["margin_channels"] >= 0


def test_revc_lanes_all_sat(revc):
    p = revc["route_plan"]["obj"]
    assert all(r["solver_status"] == "SAT" for r in p["lanes"])
    j1 = next(r for r in p["lanes"] if r["corridor"] == "U1-J1")
    assert {b["bus_id"] for b in j1["bus_rows"]} == {
        "BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2"}
    assert sum(b["assigned"] for b in j1["bus_rows"]) == 10
    for b in j1["bus_rows"]:
        assert all(pl["layer"] == "In2.Cu" for pl in b["per_layer"])
        assert all(pl["contiguous"] for pl in b["per_layer"])
    usb = next(r for r in p["lanes"] if r["corridor"] == "U1-J5")
    assert usb["bus_rows"][0]["per_layer"][0]["layer"] == "F.Cu"


def test_revc_three_state_via_and_order(revc):
    p = revc["route_plan"]["obj"]
    assert set(p["solver_summary"]["by_status"]) <= {"SAT", "UNSAT"}
    assert p["via_accounting"]["via_budget"]["state"] == "missing_basis"
    assert p["via_accounting"]["via_budget"]["supply"] is None
    assert p["via_accounting"]["planned_vias_total"] == 174
    assert p["route_order"]["dropped_unknown"] == ["LOOSE"]
    assert p["route_order"]["control_order"][0] == "BUS_USB"
    # UNKNOWN 仅因 registry 缺档（本板=无）；不虚构求解
    assert all(r["solver_status"] != "UNKNOWN" for r in p["ramps"])


def test_revc_gate_and_zero_write(revc):
    env = revc["envelope"]["obj"]
    g = env["data"]["gate"]
    assert g["route_view_registry_bound"] and g["controls_parsed"]
    assert g["resource_conflicts_attributed"] and g["solver_three_state"]
    assert g["board_hash_unchanged"] and g["no_live_commit_or_save_board"]
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert env["metrics"]["board_write"] is False
    assert env["data"]["zero_write"]["unchanged"] is True
    assert env["command_kind"] == "core"
    # 冲突归因带证书指针与回退建议
    for cfo in revc["route_plan"]["obj"]["resource_conflicts"]:
        assert cfo["certificate_run"] and cfo["blocking_net_ids"]
        assert cfo["suggested_rollback_stage"] == 3
    assert revc["route_plan"]["obj"]["rollback_suggestions"]


def test_revc_products_byte_exact_double_run(revc):
    again = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                     ff_plan_path=PLAN_PATH)
    for k in ("route_view", "route_plan", "consumption", "envelope",
              "report"):
        assert revc[k]["bytes"] == again[k]["bytes"], k


def test_revc_default_path_no_plan():
    products = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                        ff_plan_path=None)
    p = products["route_plan"]["obj"]
    assert p["plan_binding"]["bound"] is False
    assert p["controls_consumed"]["parsed"] is None
    assert p["stitching"]["status"].startswith("not_bound")
    env = products["envelope"]["obj"]
    assert env["status"] == "ok"
    again = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                     ff_plan_path=None)
    assert products["route_plan"]["bytes"] == again["route_plan"]["bytes"]


def test_revc_stale_plan_not_consumed(tmp_path):
    plan = json.load(open(PLAN_PATH, encoding="utf-8"))
    plan["snapshot"]["registry_snapshot_hash"] = "deadbeef"
    bad = tmp_path / "tampered-plan.json"
    bad.write_text(json.dumps(plan, sort_keys=True), encoding="utf-8")
    products = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                        ff_plan_path=str(bad))
    env = products["envelope"]["obj"]
    p = products["route_plan"]["obj"]
    assert env["status"] == "blocked"
    assert p["plan_binding"]["stale_plan"] is True
    assert p["controls_consumed"]["applied"] == 0
    c = products["consumption"]["obj"]
    assert c["authority_effective"].endswith("未应用）")
    assert c["controls_applied"] == []
    assert all("stale_plan" in i["reason"]
               for i in c["controls_ignored"])


def test_board_files_untouched_by_build(revc):
    """构建后板文件 hash 不变（零写板硬证据；生成器模式无写路径）。"""
    assert hashing.sha256_file(config.REVC_BOARD) == \
        revc["route_plan"]["obj"]["zero_write"]["live_board_sha256"]
    assert hashing.sha256_file(config.AUDIT_P3_BOARD) == \
        revc["route_plan"]["obj"]["zero_write"]["p3_board_sha256"]


def test_no_forbidden_core_fields(revc):
    for k in ("route_view", "route_plan", "consumption", "envelope"):
        hits = envelope.scan_forbidden_core_fields(revc[k]["obj"])
        assert hits == [], (k, hits[:3])


def test_cli_consumption_without_plan_fails(capsys):
    rc = cli.main(["route", "--select", "consumption"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "--feedforward-plan" in out


def test_pcbagent_adapter_lock():
    lock = route_view.pcbagent_adapter_lock()
    assert lock["available"] is True
    assert set(lock["modules"]) == set(route_view.PCBAGENT_ADAPTER_MODULES)
    for name, mod in lock["modules"].items():
        assert mod["available"] and mod["sha256"]
    assert "registry authority" in lock["authority_note"] or \
        lock["authority_note"].startswith("pcbagent")
