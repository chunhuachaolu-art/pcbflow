"""FC3 ④ 控制升级测试（consumer-gate-4；SPEC v1.3 §9.2/§10.2/§15 FF-4 表）。

覆盖 promotion_check 三要素：
- 合成重放：keepout=lex 首位（净通道存在→零控制违例；全通道命中→仍 SAT，
  违例=flow，UNSAT 三态不被控制违例制造/污染）；组员豁免。
- B 门零回归：默认（未绑计划）route_plan/envelope/report sha pin 零漂移 +
  双跑 byte-exact。
- Rev-C 冻结 sanity：fc3=fd2 计划（FF-REVC-0002）绑定 approved_override 基准
  全 match、authority=upgraded、18+8 控制不变、UNSAT 集/77 未匹配不变、
  79 违例 run↔assignment 对账一致、envelope ok/pass、fc1 冻结 pin 吻合；
  ③ 重跑证据（fd2 绑定）applied 24/位姿与默认全等；stale 负例不消费。
"""

import json
import os

import pytest

import revc_board_fixture
from pcbflow import audit_cmd, cli, config, coplace_cmd, envelope, geo
from pcbflow import hashing, route_cmd, route_view, signoff_cmd

FD2_PLAN = "out/revc-fd2/feedforward-plan.json"

# 默认（未绑计划）④ 产物 sha 锚：④ 升级只作用于绑定路径，默认路径零漂移
# M1 刷新：APPLY-1 落线后 dbfea089 板默认路径三产物实测重锚，2026-09-11
# （REPAIR-P1 W-5：构建输入钉仓内冻结夹具板，三 sha 原样保留，仅与 live
# 板演进解耦；板 sha 经 route_cmd 零写见证进入产物，见 live 不变量用例）
DEFAULT_ROUTE_PLAN_SHA = (
    "20be2753b89b911a7405354459ac6789ffa42f9d4008d37c3801ace33eb6fff5")
DEFAULT_ROUTE_ENVELOPE_SHA = (
    "c5abf52724e518c3d7696e27fa6e83c3dbb19252dbba4eebd7662de645ea86c7")
DEFAULT_ROUTE_REPORT_SHA = (
    "408a2f0f1311d69a1b7b0ee879564cf94b4ef28c90ba0d7438266ec35506d33c")


# ---- 合成板 helpers（test_fc1 mini board 同源；keepout 靶件可增） --------------
def _mini_board(extra=None):
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
    if extra:
        fp.update(extra)
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


def _ko(refs, mm, scope="zone:test"):
    return {"keepout_groups": [{"control_id": "CTL-9001", "scope": scope,
                                "refs": refs, "keepout_mm": mm}]}


# ---- 要素 1：合成重放（keepout=lex 候选接受） ----------------------------------
def test_keepout_lex_prefers_clean_channel():
    """净通道存在 → lex 首位把控制违例清零（重路由到净通道；物理流不变）。

    单 transit 网 NA 专用板：U1 pad1 只有 N/W 两向；W3（GND，(10.9,7.8)）
    本体与 NA 全部通道矩形不相交（物理零堵），keepout 1.4mm 覆盖窗
    （9.5,6.4,12.3,9.2）罩住 N 全路径（直通+双折），W 侧全净。无控制 →
    NA 走 N（cost 平手取 side 序）；有控制 → N 带违例 M 系数、lex 让位 →
    NA 改走净 W，违例清零、流不变。
    """
    fp = {
        "U1": {"ref": "U1", "x": 10.0, "y": 10.0, "rot": 0.0, "pads": [
            {"ref": "U1", "num": "1", "net": "NA", "x": 9.8, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "2", "net": "GND", "x": 10.2, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "3", "net": "GND", "x": 9.8, "y": 10.2,
             "w": 0.3, "h": 0.3},
            {"ref": "U1", "num": "4", "net": "GND", "x": 10.2, "y": 10.2,
             "w": 0.3, "h": 0.3},
        ]},
        "U2": {"ref": "U2", "x": 30.0, "y": 10.0, "rot": 0.0, "pads": [
            {"ref": "U2", "num": "1", "net": "NA", "x": 29.8, "y": 9.8,
             "w": 0.3, "h": 0.3},
            {"ref": "U2", "num": "2", "net": "GND", "x": 30.2, "y": 10.2,
             "w": 0.3, "h": 0.3},
            {"ref": "U2", "num": "3", "net": "GND", "x": 30.2, "y": 9.8,
             "w": 0.3, "h": 0.3},
        ]},
        "W3": {"ref": "W3", "x": 10.9, "y": 7.8, "rot": 0.0, "pads": [
            {"ref": "W3", "num": "1", "net": "GND", "x": 10.9, "y": 7.8,
             "w": 0.2, "h": 0.2}]},
    }
    board = geo.finalize_board(fp)
    plain_ctx = _view_ctx_from_board(board)
    rows0, _f0, runs0 = route_cmd.solve_ramp(plain_ctx, {})
    rows1, _f1, runs1 = route_cmd.solve_ramp(
        plain_ctx, _ko(["W3"], 1.4, scope="zone:north"))
    u1_0 = next(r for r in rows0 if r["ref"] == "U1")
    u1_1 = next(r for r in rows1 if r["ref"] == "U1")
    assert u1_1["flow"] == u1_0["flow"] == 1  # 物理可行性不变
    assert u1_0["assignments"][0]["side"] == "N"
    assert u1_1["assignments"][0]["side"] == "W"
    assert u1_1["assignments"][0]["keepout_control"] is None
    run1 = next(r for r in runs1 if r["run_id"] == "RAMP-U1")
    run0 = next(r for r in runs0 if r["run_id"] == "RAMP-U1")
    assert run1["keepout_control_violations"] == 0
    assert run1["control_violation_cost"] == 0
    assert run1["keepout_penalized"] == 1  # N 通道命中在账（清零=重路由非无视）
    assert run0["keepout_penalized"] == 0
    # 无控制组时 m_factor=0：违例恒 0（FC1 口径不变）
    assert run0["keepout_control_violations"] == 0
    assert run0["control_violation_cost"] == 0


def test_keepout_violation_never_flips_sat_to_unsat():
    """全通道命中 → 仍 SAT（物理可行），违例=flow 逐项单列；UNSAT 不被制造。

    W3（0.2²，GND）放在 U2 西北侧远处：keepout 6mm 覆盖 U2 全部通道矩形，
    但本体不与任何通道矩形相交（物理堵零）；U2 保持 SAT flow 3、违例=3。
    """
    board = _mini_board(extra={
        "W3": {"ref": "W3", "x": 26.8, "y": 6.8, "rot": 0.0, "pads": [
            {"ref": "W3", "num": "1", "net": "GND", "x": 26.8, "y": 6.8,
             "w": 0.2, "h": 0.2}]}})
    ctx = _view_ctx_from_board(board)
    rows0, _f0, _runs0 = route_cmd.solve_ramp(ctx, {})
    rows1, _f1, runs1 = route_cmd.solve_ramp(ctx, _ko(["W3"], 6.0))
    u2_0 = next(r for r in rows0 if r["ref"] == "U2")
    u2_1 = next(r for r in rows1 if r["ref"] == "U2")
    assert u2_0["solver_status"] == u2_1["solver_status"] == "SAT"
    assert u2_1["flow"] == u2_0["flow"] == 3
    assert u2_0["assignments"], "sanity：无控制时 U2 全匹配"
    assert all(a["keepout_control"] == "CTL-9001"
               for a in u2_1["assignments"])
    run1 = next(r for r in runs1 if r["run_id"] == "RAMP-U2")
    assert run1["status"] == "SAT"
    assert run1["keepout_control_violations"] == 3  # = flow（全命中）
    assert "certificate" not in run1  # 控制违例≠UNSAT：无证书可言


def test_keepout_member_ref_exempt():
    """组员 ref 自身通道豁免（与 ③ keepout 豁免语义同源）。"""
    ctx = _view_ctx_from_board(_mini_board())
    rows, _f, runs = route_cmd.solve_ramp(ctx, _ko(["U1"], 3.0,
                                                   scope="zone:member"))
    u1 = next(r for r in rows if r["ref"] == "U1")
    assert all(a["keepout_control"] is None for a in u1["assignments"])
    run = next(r for r in runs if r["run_id"] == "RAMP-U1")
    assert run["keepout_control_violations"] == 0


# ---- 要素 2：B 门零回归（默认路径 sha pin） ------------------------------------
def test_default_route_pinned_byte_exact(monkeypatch):
    """未绑计划=FC1 收官态：route_plan/envelope/report sha 钉死零漂移。

    REPAIR-P1 W-5（铜环案 R4 三步法②）：构建输入钉冻结夹具板（与
    2026-09-11 live 板 dbfea089 逐字节同）——三产物内嵌的零写板锚随
    夹具板冻结，sha 期望原样保留，与 live 板演进解耦。
    """
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    products = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                        ff_plan_path=None)
    assert products["route_plan"]["sha256"] == DEFAULT_ROUTE_PLAN_SHA
    assert products["envelope"]["sha256"] == DEFAULT_ROUTE_ENVELOPE_SHA
    assert products["report"]["sha256"] == DEFAULT_ROUTE_REPORT_SHA
    assert products["route_plan"]["obj"]["plan_binding"]["bound"] is False
    assert products["envelope"]["obj"]["data"]["gate"].get(
        "controls_consumer_gate_approved") is None  # 条件键不进默认路径
    assert "keepout_control_violations" not in products["envelope"]["obj"][
        "metrics"]


@pytest.mark.skipif(not os.path.isfile(str(config.REVC_BOARD)),
                    reason="真实板不存在")
def test_default_route_live_board_invariants():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进仍可构建且合同成立。

    只断板无关不变量——零写见证=live 板实测 sha（身份无漂移，证明板字节
    确实进入产物=钉板 sha 锚的真实性来源）、三产物齐备、默认路径不绑
    计划；不带三产物 sha 精确值（那些由钉夹具板用例守护）。全构建内存
    零落盘（route_cmd 零写见证，redesign-report P6 先例）。
    """
    products = route_cmd.build_products(out_dir_rel="out/revc-fc1",
                                        ff_plan_path=None)
    live_sha = hashing.sha256_file(config.REVC_BOARD)
    plan = products["route_plan"]["obj"]
    witnesses = [
        plan["zero_write"]["live_board_sha256"],
        plan["zero_write"]["live_board_sha256_after_build"],
        plan["pins"]["live_board_zero_write_witness"]["sha256"],
    ]
    for w in witnesses:
        assert w == live_sha
    assert plan["plan_binding"]["bound"] is False
    assert all(products[k]["sha256"] for k in
               ("route_plan", "envelope", "report"))
    assert os.path.isfile(str(config.REVC_BOARD))


# ---- 要素 3：Rev-C 冻结 sanity（fc3=fd2 计划绑定） -----------------------------
@pytest.fixture(scope="module")
def fc3():
    return route_cmd.build_products(out_dir_rel="out/revc-fc3",
                                    ff_plan_path=FD2_PLAN)


def test_fc3_binding_approved_override_basis(fc3):
    """fd2 计划=批准视图 hash 基准（fc3-D3）：六 hash 全 match，basis 落键。"""
    c = fc3["consumption"]["obj"]
    assert c["plan_id"] == "FF-REVC-0002"
    assert c["snapshot_check"]["all_match"] is True
    assert c["snapshot_check"]["structures_basis"] == "approved_override"
    st = next(x for x in c["snapshot_check"]["checks"]
              if x["key"] == "structures_sha256")
    assert st["match"] is True and st["current"] and st["plan"] == \
        st["current"]
    assert c["authority_effective"] == "upgraded_for_candidate_acceptance"
    assert c["consumer_gate"]["approved"] is True
    pc = c["consumer_gate"]["promotion_check"]
    assert set(pc) >= {"synthetic_replay", "b_gate_zero_regression",
                       "revc_frozen_sanity", "verdict"}
    assert pc["verdict"].startswith("pass")
    assert "consumer-gate-4.json" in c["note"]
    # 控制集与 FF1 口径一致（26 条全解析，禁静默全量吞）
    assert len(c["controls_applied"]) == 18
    assert len(c["controls_ignored"]) == 8
    declared = set(c["controls_declared_consumed"])
    ignored = {i["control_id"] for i in c["controls_ignored"]}
    read = set(c["controls_actually_read"])
    assert not (declared & ignored) and (declared | ignored) <= read


def test_fc3_three_state_and_violation_ledger(fc3):
    """三态红线不变 + keepout 违例逐 run↔逐赋值对账一致。"""
    p = fc3["route_plan"]["obj"]
    unsat = {r["ref"] for r in p["ramps"] if r["solver_status"] == "UNSAT"}
    assert unsat == {"U1", "U2", "U3", "U6"}  # 物理赤字场不因控制改变
    assert sum(len(r["unmatched"]) for r in p["ramps"]) == 77
    for run in p["solver_runs"]:
        if run["status"] == "UNSAT":
            assert run["certificate"]["verified"]
    assert p["solver_summary"]["unsat_without_certificate"] == 0
    assert all(r["solver_status"] == "SAT" for r in p["lanes"])
    # 违例对账：run 计数 = 命中赋值行数（同一账本两视角）
    viol = sum(r["keepout_control_violations"] for r in p["solver_runs"]
               if r["kind"] == "ramp")
    hits = sum(1 for r in p["ramps"] for a in r["assignments"]
               if a["keepout_control"])
    assert viol == hits == 79  # Rev-C 冻结基线的控制违例面（control-attributed）
    env = fc3["envelope"]["obj"]
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert env["data"]["gate"]["controls_consumer_gate_approved"] is True
    assert env["metrics"]["keepout_control_violations"] == 79
    assert any(d["id"] == "fc3_controls_upgraded" for d in env["diagnostics"])
    assert env["data"]["zero_write"]["unchanged"] is True
    # keepout 控制组生效证据（CTL-0025/0026 → lex 候选接受语义）
    app = fc3["consumption"]["obj"]["application"]["protect_keepout"]
    assert app["effect"].startswith("匝道通道 keepout 进入候选接受")
    assert {g["scope"] for g in app["groups"]} == {"power_SW", "crystal_NE"}


def test_fc3_double_run_byte_exact(fc3):
    again = route_cmd.build_products(out_dir_rel="out/revc-fc3",
                                     ff_plan_path=FD2_PLAN)
    for k in ("route_view", "route_plan", "consumption", "envelope",
              "report"):
        assert fc3[k]["bytes"] == again[k]["bytes"], k


def test_fc3_stale_fd2_not_consumed(tmp_path):
    plan = json.load(open(FD2_PLAN, encoding="utf-8"))
    plan["snapshot"]["registry_snapshot_hash"] = "deadbeef"
    bad = tmp_path / "tampered-plan.json"
    bad.write_text(json.dumps(plan, sort_keys=True), encoding="utf-8")
    products = route_cmd.build_products(out_dir_rel="out/revc-fc3",
                                        ff_plan_path=str(bad))
    env = products["envelope"]["obj"]
    assert env["status"] == "blocked"
    c = products["consumption"]["obj"]
    assert c["authority_effective"].endswith("未应用）")
    assert c["controls_applied"] == []
    assert products["route_plan"]["obj"]["controls_consumed"]["applied"] == 0


def test_fc1_frozen_pin_intact():
    """fc1 route-plan 冻结 pin（④ 升级后历史证据；只读核对，禁重生成）。"""
    import os
    pin = signoff_cmd.FC1_FROZEN_PINS["route-plan.json"]
    rel = os.path.join("out", "revc-fc1", "route-plan.json")
    assert hashing.sha256_file(rel) == pin["sha256"]


# ---- ③ 重跑证据（fd2 计划绑定；NEXT.md「重跑 ③ 消费证据」） ---------------------
@pytest.fixture(scope="module")
def coplace_fc3():
    return coplace_cmd.build_products("out/revc-fc3", ff_plan_path=FD2_PLAN)


def test_coplace_fd2_consumption(coplace_fc3):
    ev = coplace_fc3["ff_consumption"]["obj"]
    assert ev["plan_id"] == "FF-REVC-0002"
    assert ev["snapshot_check"]["all_match"] is True
    assert ev["snapshot_check"]["structures_basis"] == "approved_override"
    assert ev["authority_effective"] == "upgraded_for_candidate_acceptance"
    assert len(ev["controls_declared_consumed"]) == 24
    assert [i["control_id"] for i in ev["controls_ignored"]] == ["CTL-0022",
                                                                 "CTL-0024"]


def test_coplace_fd2_poses_equal_default(coplace_fc3):
    """控制集与 FF1 语义一致 → 位姿与默认跑全等（③ 升级同款冻结 sanity）。"""
    default = coplace_cmd.build_products()
    poses = lambda l: json.dumps(l["layout"]["obj"]["placements"],
                                 sort_keys=True)
    assert poses(coplace_fc3) == poses(default)


# ---- CLI 契约 -------------------------------------------------------------------
def test_cli_route_summary_reports_upgraded_authority(capsys):
    rc = cli.main(["route", "--select", "summary",
                   "--feedforward-plan", FD2_PLAN,
                   "--out-dir", "out/revc-fc3"])
    out = capsys.readouterr().out
    assert rc == config.EXIT_OK
    assert "upgraded_for_candidate_acceptance" in out
    assert '"verdict": "pass"' in out


def test_no_forbidden_core_fields(fc3, coplace_fc3):
    for k in ("route_view", "route_plan", "consumption", "envelope"):
        assert envelope.scan_forbidden_core_fields(fc3[k]["obj"]) == [], k
    assert envelope.scan_forbidden_core_fields(
        coplace_fc3["ff_consumption"]["obj"]) == []
