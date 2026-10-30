"""FD2 单测（adoption 级联重跑：structures.override 权威 + 能力/叠层/电流源消费）。

覆盖：
- 批准视图（override 对读草案）：authority/STR-1/STR-2 裁决落位、hash 稳定、
  base_draft 失配拒绝消费、草案文件冻结；
- FD2 计划：plan_id/snapshot 六 hash+信息键/STR-1 合并通道行 width_basis 复核/
  via 供给 derived 上界/rail sourced+derived 分类（供给侧 missing_basis 保持）；
- 阻抗重算一阶公式数学（闭式解/二分/容差判定/TBD-1 义务保留）；
- ⑤ approved 基准绑定 + RES-VIA-1 退化口径 model_gap；
- ⑥ fd2 包：structures 已批段/known_open 收敛/批准消费/重放 byte-exact；
- 默认路径回归：build_plan() 无 adopt=FF1 口径（structures=草案文件 hash）。
"""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from pcbflow import check_cmd, cli, config, feedforward as ff, signoff_cmd
from pcbflow import feedforward_config as ffc, hashing
from pcbflow.envelope import scan_forbidden_core_fields

FD2_DIR = "out/revc-fd2"
FD1_APPROVALS = "out/revc-fd1/approvals"

# ---- R28 板锚参数化（铜环案 R4 三步法；2026-09-12 重设计批） ---------------------
# 真实板 2026-09-11 被并行工作流 ripup1 改写（8029f5ff→dbfea089，铜环案裁定书
# 事实 C）；route_cmd 把实测板 sha 嵌进 route_plan（锚），冻结 out/revc-fc3 件
# 记旧板锚 → 包重放门 byte-exact 失败。冻结口径参数化（R4 三步法②）：板输入
# 钉仓库在案冻结快照板（裁定书 §3，三份快照逐字节相同），只读引用、零复制。
FROZEN_BOARD_SHA = \
    "8029f5ff6948f4abeda9cd04f78b6eaf481a462e97d3ce85ecbc024573111849"
FROZEN_BOARD_SNAPSHOT = os.path.join(
    ff.config.PCBFLOW_ROOT, os.pardir, os.pardir, "design/coreboard/kicad/"
    "stm32h743-coreboard-revc/snapshots/live-ripup1-pre/"
    "stm32h743-coreboard-revc.kicad_pcb")
FC3_ROUTE_PLAN = "out/revc-fc3/route-plan.json"
A3_CONSTRAINTS = "out/revc-a3/constraints.json"


def _fc3_disk_anchor():
    with open(os.path.join(config.PCBFLOW_ROOT, FC3_ROUTE_PLAN),
              encoding="utf-8") as f:
        return json.load(f)["zero_write"]["live_board_sha256"]


def _frozen_board_abs():
    """冻结夹具板绝对路径（fail-closed：sha 必须=登记锚=冻结 fc3 件所记锚）。"""
    p = os.path.normpath(FROZEN_BOARD_SNAPSHOT)
    assert hashing.sha256_file(p) == FROZEN_BOARD_SHA, "冻结夹具板自身漂移"
    assert _fc3_disk_anchor() == FROZEN_BOARD_SHA, "冻结 fc3 件板锚与登记锚不符"
    return p


def _patch_replay_product(monkeypatch, product_rel, product_path):
    """负对照注入通道：重放集指定行指向 tmp 副本（冻结件本体零接触）。"""
    newset = tuple(
        dict(r, product=product_path) if r["product"] == product_rel else r
        for r in signoff_cmd.REPLAY_SET)
    monkeypatch.setattr(signoff_cmd, "REPLAY_SET", newset)


def _fsha(rel):
    return hashing.sha256_file(os.path.join(ff.config.PCBFLOW_ROOT,
                                            *rel.split("/")))


@pytest.fixture(scope="module")
def adopted():
    plan, basis = ff.build_plan(adopt_override=True)
    return plan, basis


# ---- 批准视图 -------------------------------------------------------------------
def test_approved_view_and_hash(adopted):
    plan, basis = adopted
    draft = json.loads(open(os.path.join(
        ff.config.PCBFLOW_ROOT, "out/revc-a3/structures.json"),
        encoding="utf-8").read())
    ov = json.loads(open(os.path.join(
        ff.config.PCBFLOW_ROOT, ff.OVERRIDE_REL), encoding="utf-8").read())
    view = ff.approved_structures_view(draft, ov)
    assert view["authority_status"] == "approved"
    st_by_id = {f["id"]: f["status"] for f in view["findings"]}
    assert "adopted" in st_by_id["STR-1"]
    assert "adopted" in st_by_id["STR-2"]
    # 草案本体未被改写（authority 仍 draft；STR-1 仍 pending）
    assert draft["authority_status"] == "draft"
    # 草案文件冻结 = override.base_draft.sha256
    assert _fsha("out/revc-a3/structures.json") == \
        ov["approved"]["base_draft"]["sha256"]
    # hash 确定性（重算一致）且 ≠ 草案文件 hash
    h1 = ff.approved_structures_sha256(draft, ov)
    assert h1 == ff.approved_structures_sha256(draft, ov)
    assert h1 == basis["snapshot"]["structures_sha256"]
    assert h1 != _fsha("out/revc-a3/structures.json")


def test_override_base_mismatch_rejected(tmp_path, monkeypatch):
    """base_draft.sha256 与盘上草案不符 → 拒绝消费（不静默）。"""
    reads = []
    orig = ff._read_json

    def tampered(rel, role, reads_):
        obj, sha = orig(rel, role, reads_)
        if rel == ff.OVERRIDE_REL:
            obj["approved"]["base_draft"]["sha256"] = "0" * 64
        return obj, sha

    monkeypatch.setattr(ff, "_read_json", tampered)
    with pytest.raises(ValueError):
        ff.load_override(reads)


# ---- FD2 计划 -------------------------------------------------------------------
def test_fd2_plan_snapshot_and_core(adopted):
    plan, basis = adopted
    assert plan["plan_id"] == ff.ADOPT_PLAN_ID == "FF-REVC-0002"
    for k in ffc.STALE_CHECK_KEYS:
        assert plan["snapshot"][k]
    # 信息键：批准视图绑定 + 草案冻结 + override hash
    snap = plan["snapshot"]
    assert snap["structures_authority"].startswith("approved")
    assert snap["structures_draft_sha256"] == \
        _fsha("out/revc-a3/structures.json")
    assert snap["structures_override_sha256"]
    # 六 hash 中其余五项与冻结基线一致（adoption 只动 structures 基准）
    assert snap["registry_snapshot_hash"] == \
        json.loads(open(os.path.join(
            ff.config.PCBFLOW_ROOT, "out/revc-a3/net-registry.json"),
            encoding="utf-8").read())["registry_snapshot_hash"]
    assert snap["constraints_sha256"] == _fsha("out/revc-a3/constraints.json")
    assert plan["authority"] == "planning_advisory"
    assert scan_forbidden_core_fields(plan) == []


def test_str1_combined_corridor_and_pending_resolution(adopted):
    plan, _ = adopted
    rows = {r["resource_id"]: r for r in plan["resources"]}
    comb = rows["corridor:U1-J1:storage_combined"]
    # 19 网存储通道：ceil(19/2)×0.35+0.6 = 4.1mm（override width_basis）
    assert comb["demand"]["value"] == 4.1
    assert comb["supply"]["value"] == 28.655
    assert comb["state"] == "available"
    assert comb["width_basis_check"]["consistent"] is True
    assert comb["width_basis_check"]["override_claim_mm"] == 4.1
    assert len(comb["scope"]["bus_ids"]) == 3
    # per-bus 行 pending 注记解除（audit C4 历史行不回写）
    for rid in ("corridor:U1-J1",):
        per_bus = [r for r in plan["resources"]
                   if r["resource_id"] == rid]
        assert len(per_bus) == 3
        assert all("STR-1 已批" in r["note"] for r in per_bus)
    aud = json.loads(open(os.path.join(
        ff.config.PCBFLOW_ROOT, "out/revc-a3/audit.json"),
        encoding="utf-8").read())
    c4 = next(c for c in aud["checks"] if c["check_id"] == "C4_corridor_capacity")
    assert any(r.get("status") == "pending_STR-1"
               for r in c4["metrics"]["corridor_budgets"])  # 历史冻结


def test_via_supply_and_rail_currents(adopted):
    plan, _ = adopted
    rows = {r["resource_id"]: r for r in plan["resources"]}
    vb = rows["via_budget:board"]
    # 供给=能力表 derived 密度上界：单层可用面积/(0.25+2×0.09)²
    fab = json.loads(open(os.path.join(
        ff.config.PCBFLOW_ROOT, ff.FAB_CAPABILITY_REL),
        encoding="utf-8").read())
    supply, cell = ff.via_budget_supply(2403.0, fab)  # 数值随面积缩放
    assert supply == int(2403.0 / (cell["cell_pitch_mm"] ** 2))
    assert vb["supply"]["value"] > 0 and vb["state"] == "available"
    assert "derived" in vb["supply"]["basis"][0]
    assert vb["yellow_margin"]["value"] == pytest.approx(
        ff.VIA_BUDGET_YELLOW_FRACTION * vb["supply"]["value"], abs=0.05)
    # 5V_USB sourced；其余 derived（IPC-2221A 拟合式 @ 干路线宽）
    usb = rows["power_return_space:rail:5V_USB"]
    assert usb["demand"]["value"] == ff.USB_VBUS_BUDGET_A == 0.5
    assert "sourced" in usb["demand"]["basis"][0]
    r33 = rows["power_return_space:rail:3V3"]
    assert r33["demand"]["value"] == round(ff.ipc2221_current_a(1.0), 3)
    assert "derived_policy" in r33["demand"]["basis"][0]
    vbat = rows["power_return_space:rail:VBAT"]
    assert vbat["demand"]["value"] == round(ff.ipc2221_current_a(0.3), 3)
    # rail 供给侧仍缺 → missing_basis 保持（不虚构）
    assert r33["state"] == "missing_basis"
    assert "supply" in r33["reason"]
    # 诊断：STR-1 已批 + 缺失源部分解决
    di = {d["id"] for d in plan["diagnostics"]}
    assert "str1_adopted_corridors" in di
    assert "missing_sources_partial_resolved" in di
    assert "str1_pending_corridors" not in di


# ---- 阻抗重算（一阶公式；derived 预估，TBD-1 保留） ------------------------------
def test_impedance_rerun_math(adopted):
    _, basis = adopted
    reads = []
    imp = ff.build_impedance_targets(ff.ADOPT_PLAN_ID, basis["sources"], reads)
    h, er, t = 0.2104, 4.4, 0.035
    w50 = ff.width_for_z0(50.0, h, t, er)
    assert w50 == pytest.approx(0.3498, abs=1e-3)
    zd = ff.zdiff_edge_coupled(0.2, 0.2, h, t, er)
    assert zd == pytest.approx(108.7, abs=0.5)
    rows = {r["net_class"]: r for r in imp["targets"]}
    assert rows["single_ended_critical"]["est_width_mm_for_target"] == \
        round(w50, 4)
    assert rows["single_ended_critical"]["within_tolerance"] is True
    u = rows["USB_DIFF"]
    assert u["est_zdiff_ohm_adopted_geometry"] == round(zd, 1)
    assert u["within_tolerance"] is False      # 108.7 出 90±15%
    assert u["revision_threshold_30pct_exceeded"] is False  # <30% 修订阈
    assert "pending_TBD-1" in u["status"]
    assert imp["estimate_class"].startswith("first_order_estimate")
    assert scan_forbidden_core_fields(imp) == []


# ---- ⑤ approved 基准绑定 + via 退化残差 -----------------------------------------
def test_check_binding_approved_and_via_model_gap():
    res = check_cmd.build_ff_residuals(out_dir_rel="out/revc-fc2",
                                       ff_plan_dir=FD2_DIR)
    assert res["stale_plan_reason"] is None
    assert res["snapshot_check"]["structures_basis"] == "approved_override"
    rows = {r["residual_id"]: r for r in res["rows"]}
    via = rows["RES-VIA-1"]
    assert via["predicted"]["value"] == 0
    assert via["E"]["value"] == via["actual_observed"]["value"]  # E=obs−0
    assert via["model_gap"] == "layer_plan via_count_total=0（计划级未计）"
    # ⑤ envelope 门保持 pass（检查器验证与 board_quality 分列）
    env = check_cmd.build_envelope(out_dir_rel=FD2_DIR,
                                   probe_drc_dir="out/revc-fd1/probes",
                                   fc2_dir="out/revc-fc2",
                                   ff_plan_dir=FD2_DIR)
    assert env["status"] == "ok" and env["verdict"] == "pass"


# ---- ⑥ fd2 签核包 ---------------------------------------------------------------
SO = dict(out_dir_rel=FD2_DIR, ff_plan_dir=FD2_DIR, check_dir=FD2_DIR,
          approvals_dir=FD1_APPROVALS)


def test_signoff_package_fd2(monkeypatch):
    """R28 板锚参数化：包/门/重放链的板输入钉冻结夹具板（8029f5ff=冻结 fc3
    件的构建输入板）→ 原断言（门 replay_all_byte_exact=True、十行重放全
    byte-exact）零改动、原强度成立；live 板差异登记见
    test_signoff_envelope_live_board_gate_registered。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    pkg = signoff_cmd.build_package(**SO)
    sec = {s["item"]: s for s in pkg["sections"]}
    assert sec["structures snapshot"]["status"] == "present"
    assert any(e.get("role") == "authority_approval"
               for e in sec["structures snapshot"]["entries"])
    # known_open 收敛：structures 条目随批准关闭（其余如实保留）
    assert "① structures" not in [k.get("source") for k in pkg["known_open"]]
    assert {k["source"] for k in pkg["known_open"]} == {
        "⑤ check-report", "④ FC2 靶 1", "④ FC2 靶 2"}
    # 批准消费（approvals 跨目录输入）
    ledger = signoff_cmd.build_waiver_ledger(out_dir_rel=FD2_DIR,
                                             approvals_dir=FD1_APPROVALS)
    assert len(ledger["approved"]) == 4
    assert ledger["approval_drift"] == []
    assert ledger["approvals_input"]["path"] == \
        FD1_APPROVALS + "/waiver-approvals.json"
    env = signoff_cmd.build_envelope(adopt_override=True, **SO)
    g = env["data"]["gate"]
    assert g["structures_approved"] is True
    assert g["production_signoff_ready"] is False  # 外部/生产正文仍缺（如实）
    assert g["replay_all_byte_exact"] is True
    assert env["status"] == "ok" and env["verdict"] == "pass"
    # fd2 核心 FF 产物入重放（6 历史 + 4 fd2）
    replay = signoff_cmd.build_replay(FD2_DIR, signoff_cmd._adopt_replay_extras(
        FD2_DIR))
    assert len(replay["regenerated"]) == 10
    assert all(r["byte_exact"] for r in replay["regenerated"])


def test_signoff_envelope_live_board_gate_registered():
    """R4 三步法③ live 板集成用例：fd2 包重放门随板锚状态参数化（R28）。

    漂移态（live≠冻结锚）：门 replay_all_byte_exact=False；默认重放集与
    fd2 extras 集的失败行都恰=[fc3 route-plan]（板锚行），fd2 四 extras 行
    保持 byte-exact。板回锚 → 门 True、十行全 exact（fail-closed）。"""
    anchor = _fc3_disk_anchor()
    live = hashing.sha256_file(config.REVC_BOARD)
    env = signoff_cmd.build_envelope(adopt_override=True, **SO)
    g = env["data"]["gate"]
    assert g["replay_all_byte_exact"] == (live == anchor)
    replay = signoff_cmd.build_replay(FD2_DIR, signoff_cmd._adopt_replay_extras(
        FD2_DIR))
    ok = all(r["byte_exact"] for r in replay["regenerated"])
    assert ok == (live == anchor)
    if live != anchor:
        assert [r["product"] for r in replay["regenerated"]
                if not r["byte_exact"]] == [FC3_ROUTE_PLAN]
        default = signoff_cmd.build_replay()
        assert {r["product"] for r in default["regenerated"]
                if not r["byte_exact"]} == {FC3_ROUTE_PLAN}


def test_negative_control_non_anchor_replay_tamper_detected(
        monkeypatch, tmp_path):
    """负对照（R28 硬约束）：钉板门 True 前提下注入非锚差异必须仍被检出。

    对照组：a3 constraints tmp 逐字节副本 → 门 replay_all_byte_exact=True；
    注入（非锚）：副本 constraints[0].params.class 篡改 → 门 False。
    冻结件本体零接触（tmp 副本注入，REPLAY_SET 定向改指）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "constraints.json"
    with open(os.path.join(config.PCBFLOW_ROOT, A3_CONSTRAINTS), "rb") as f:
        copy_path.write_bytes(f.read())
    _patch_replay_product(monkeypatch, A3_CONSTRAINTS, str(copy_path))
    env = signoff_cmd.build_envelope(adopt_override=True, **SO)
    assert env["data"]["gate"]["replay_all_byte_exact"] is True
    obj = json.loads(copy_path.read_text(encoding="utf-8"))
    obj["constraints"][0]["params"]["class"] = "TAMPERED-NON-ANCHOR"
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    env = signoff_cmd.build_envelope(adopt_override=True, **SO)
    assert env["data"]["gate"]["replay_all_byte_exact"] is False


@pytest.mark.xfail(strict=True, reason="负对照：非锚差异（constraints 字段篡改）"
                                       "必须使包重放门 fail（R28）")
def test_negative_control_gate_green_must_fire_on_tamper(
        monkeypatch, tmp_path):
    """以原始断言形态直证「注入非锚差异→仍然 fail」（红即预期，xfail）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "constraints.json"
    obj = json.loads(open(os.path.join(config.PCBFLOW_ROOT, A3_CONSTRAINTS),
                          encoding="utf-8").read())
    obj["constraints"][0]["params"]["class"] = "TAMPERED-NON-ANCHOR"
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    _patch_replay_product(monkeypatch, A3_CONSTRAINTS, str(copy_path))
    env = signoff_cmd.build_envelope(adopt_override=True, **SO)
    assert env["data"]["gate"]["replay_all_byte_exact"] is True


# ---- 默认路径回归（FF1 字节稳定） -----------------------------------------------
def test_default_path_unchanged():
    plan, basis = ff.build_plan()
    assert plan["plan_id"] == ffc.PLAN_ID == "FF-REVC-0001"
    assert plan["snapshot"]["structures_sha256"] == \
        _fsha("out/revc-a3/structures.json")
    assert "structures_override_sha256" not in plan["snapshot"]
    assert not any(r["resource_id"] == "corridor:U1-J1:storage_combined"
                   for r in plan["resources"])
    # fd2 盘上计划与默认重建必然不同（structures 基准变化）
    disk_fd2 = open(os.path.join(ff.config.PCBFLOW_ROOT,
                                 "out/revc-fd2/feedforward-plan.json"),
                    "rb").read()
    assert hashing.canonical_json_bytes(plan) != disk_fd2


# ---- CLI 契约 -------------------------------------------------------------------
def test_cli_impedance_targets_guard(capsys):
    rc = cli.main(["feedforward", "--select", "impedance_targets",
                   "--out-dir", FD2_DIR])
    assert rc == cli.config.EXIT_FAILED
    out = capsys.readouterr().out
    assert "adopt-override" in json.loads(out)["error"]


def test_cli_fd2_plan_regenerates_byte_exact(capsys):
    rc = cli.main(["feedforward", "--adopt-override", "--select", "plan",
                   "--out-dir", FD2_DIR])
    assert rc == cli.config.EXIT_OK
    regen = capsys.readouterr().out
    disk = open(os.path.join(ff.config.PCBFLOW_ROOT,
                             "out/revc-fd2/feedforward-plan.json"),
                "rb").read().decode("utf-8")
    assert regen == disk
