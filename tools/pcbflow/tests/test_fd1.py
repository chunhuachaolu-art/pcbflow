"""FD1 单测（⑤ 检查器族/残差/探针电池 + ⑥ waiver 红线/签核包）。

变异电池=§16.5 正向/负向变异（deterministic_screening 子集，自包含合成路由）；
残差/stale/waiver 用 tmp 合成树（monkeypatch 模块常量为绝对路径，os.path.join
绝对分量丢弃前缀）；signoff 重放为 Rev-C 冻结基线轨（同 test_*_revc 先例）。
"""

from __future__ import annotations

import copy
import json
import os

import pytest

from pcbflow import check_cmd, cli, config, hashing, route_cmd, signoff_cmd
from pcbflow.envelope import scan_forbidden_core_fields

# ---- R28 板锚参数化（铜环案 R4 三步法；2026-09-12 重设计批） ---------------------
# 真实板 2026-09-11 被并行工作流 ripup1 改写（8029f5ff→dbfea089，铜环案裁定书
# 事实 C）；route_cmd 把实测板 sha 嵌进 route_plan 的 zero_write/pins（锚），
# 冻结 out/revc-fc3 件记旧板锚 → 重放门 byte-exact 失败。冻结口径参数化（R4
# 三步法②）：板输入钉仓库在案冻结快照板（裁定书 §3），只读引用、零复制。
FROZEN_BOARD_SHA = \
    "8029f5ff6948f4abeda9cd04f78b6eaf481a462e97d3ce85ecbc024573111849"
FROZEN_BOARD_SNAPSHOT = os.path.join(
    config.PCBFLOW_ROOT, os.pardir, os.pardir, "design/coreboard/kicad/"
    "stm32h743-coreboard-revc/snapshots/live-ripup1-pre/"
    "stm32h743-coreboard-revc.kicad_pcb")
FC3_ROUTE_PLAN = "out/revc-fc3/route-plan.json"
FC3_REGEN_KW = dict(out_dir_rel="out/revc-fc3",
                    ff_plan_path="out/revc-fd2/feedforward-plan.json")
# 板锚叶全集（route_plan 内嵌实测板 sha 的仅有三处；live 板下实测枚举）
ANCHOR_LEAVES = ("pins.live_board_zero_write_witness.sha256",
                 "zero_write.live_board_sha256",
                 "zero_write.live_board_sha256_after_build")


def _fc3_disk_plan():
    with open(os.path.join(config.PCBFLOW_ROOT, FC3_ROUTE_PLAN),
              encoding="utf-8") as f:
        return json.load(f)


def _frozen_board_abs():
    """冻结夹具板绝对路径（fail-closed：sha 必须=登记锚=冻结 fc3 件所记锚）。"""
    p = os.path.normpath(FROZEN_BOARD_SNAPSHOT)
    assert hashing.sha256_file(p) == FROZEN_BOARD_SHA, "冻结夹具板自身漂移"
    assert _fc3_disk_plan()["zero_write"]["live_board_sha256"] == \
        FROZEN_BOARD_SHA, "冻结 fc3 件板锚与登记锚不符"
    return p


def _leaf_diff(a, b, path="", out=None):
    """结构化叶级 diff：{叶路径: (旧值, 新值)}——历史差异登记的比较核。"""
    if out is None:
        out = {}
    if type(a) is not type(b):
        out[path or "<root>"] = (a, b)
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            _leaf_diff(a.get(k, "<MISSING>"), b.get(k, "<MISSING>"),
                       "%s.%s" % (path, k) if path else k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out["%s[len]" % path] = (len(a), len(b))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _leaf_diff(x, y, "%s[%d]" % (path, i), out)
    elif a != b:
        out[path] = (a, b)
    return out


def _set_leaf(obj, dotted, value):
    keys = dotted.split(".")
    cur = obj
    for k in keys[:-1]:
        cur = cur[k]
    cur[keys[-1]] = value


def _mask_anchor_leaves(plan):
    """锚期望参数化：三锚叶置哨兵后比较（语义等价对照）。"""
    obj = copy.deepcopy(plan)
    for leaf in ANCHOR_LEAVES:
        _set_leaf(obj, leaf, "<board-anchor>")
    return obj


def _patch_replay_fc3_product(monkeypatch, product_path):
    """负对照注入通道：重放集 fc3 行指向 tmp 副本（冻结件本体零接触）。"""
    newset = tuple(
        dict(r, product=product_path) if r["product"] == FC3_ROUTE_PLAN else r
        for r in signoff_cmd.REPLAY_SET)
    monkeypatch.setattr(signoff_cmd, "REPLAY_SET", newset)

# ---- 合成路由/数据 --------------------------------------------------------------
def _route(net_id, segs, vias=()):
    return {"net_id": net_id, "segments": segs, "vias": list(vias)}


STRAIGHT = _route("N1", [[0, 0.0, 0.0, 10.0, 0.0]])


# ---- 变异电池：CHK-CORNER（正向 2 + 负向 1） ------------------------------------
def test_mutation_corner():
    rows = check_cmd.run_deterministic_screening([STRAIGHT])
    corner = rows[0]
    assert corner["checker_id"] == "CHK-CORNER" and corner["verdict"] == "pass"
    # 正向变异：注入零长段 → 必须 fire
    mutated = _route("N1", [[0, 0.0, 0.0, 10.0, 0.0],
                            [0, 10.0, 0.0, 10.0, 0.0]])
    assert check_cmd.run_deterministic_screening(
        [mutated])[0]["verdict"] == "fail"
    # 正向变异：相邻重复段 → 必须 fire
    dup = _route("N1", [[0, 0.0, 0.0, 10.0, 0.0],
                        [0, 0.0, 0.0, 10.0, 0.0]])
    row = check_cmd.run_deterministic_screening([dup])[0]
    assert row["verdict"] == "fail"
    assert any(v["kind"] == "duplicate_consecutive_segment"
               for v in row["violations"])


# ---- 变异电池：CHK-LEN ------------------------------------------------------------
def test_mutation_len():
    assert check_cmd.run_deterministic_screening([STRAIGHT])[1][
        "verdict"] == "pass"
    # 正向变异：绕行比 2.0（>1.5 阈值）→ fire
    detour = _route("N1", [[0, 0.0, 0.0, 5.0, 0.0],
                           [0, 5.0, 0.0, 5.0, 10.0],
                           [0, 5.0, 10.0, 10.0, 10.0],
                           [0, 10.0, 10.0, 10.0, 0.0]])
    row = check_cmd.run_deterministic_screening([detour])[1]
    assert row["checker_id"] == "CHK-LEN" and row["verdict"] == "fail"
    assert row["violations"][0]["kind"] == "detour_ratio_over"


# ---- 变异电池：CHK-SYMM（有声明执行；无声明 not_executed 不伪造） -----------------
def test_mutation_symm():
    sym = {"class_id": "SYM-1",
           "members": [["RA", "1"], ["RB", "1"]]}
    routes = [{"net_id": "N1", "ref_pad": ("RA", "1"),
               "segments": [[0, 10.0, 10.0, 10.0, 10.0]]},
              {"net_id": "N2", "ref_pad": ("RB", "1"),
               "segments": [[0, 10.0, 10.5, 10.0, 10.5]]}]
    rows = check_cmd.run_deterministic_screening(routes, sym_classes=[sym])
    assert rows[2]["checker_id"] == "CHK-SYMM" and rows[2]["verdict"] == "pass"
    # 正向变异：成员大幅偏移 → fire
    routes2 = [dict(routes[0]),
               {"net_id": "N2", "ref_pad": ("RB", "1"),
                "segments": [[0, 10.0, 20.0, 10.0, 20.0]]}]
    row = check_cmd.run_deterministic_screening(routes2, sym_classes=[sym])[2]
    assert row["verdict"] == "fail"
    # 无已批声明 → not_executed（不伪造测量）
    row = check_cmd.run_deterministic_screening(routes)[2]
    assert row["checker_status"] == "not_executed" and row["verdict"] is None


# ---- 变异电池：CHK-DIFF（差分连续性） ---------------------------------------------
DIFF_REL = {"relation_id": "RDP-X", "kind": "differential_pair",
            "members": ["N1", "N2"],
            "segments": {"mcu_side": ["N1"], "connector_side": ["N2"]}}


def test_mutation_diff():
    routes = [_route("N1", [[0, 0.0, 0.0, 10.0, 0.0]]),
              _route("N2", [[0, 0.0, 1.0, 10.2, 1.0]])]  # 失配 2%
    rows = check_cmd.run_deterministic_screening(routes,
                                                 diff_relations=[DIFF_REL])
    assert rows[3]["verdict"] == "pass"
    # 正向变异 1：一侧成员整体缺失 → side_incomplete fail
    row = check_cmd.run_deterministic_screening(
        [routes[0]], diff_relations=[DIFF_REL])[3]
    assert row["verdict"] == "fail"
    assert any(v["kind"] == "side_incomplete" for v in row["violations"])
    # 正向变异 2：长度失配 >10% → fail
    bad = _route("N2", [[0, 0.0, 1.0, 15.0, 1.0]])
    row = check_cmd.run_deterministic_screening(
        [routes[0], bad], diff_relations=[DIFF_REL])[3]
    assert row["verdict"] == "fail"
    # 成员不在数据集 → not_available（信息级，不入 violations）
    row = check_cmd.run_deterministic_screening(
        [_route("N9", [[0, 0, 0, 1, 0]])],
        diff_relations=[DIFF_REL])[3]
    assert row["checker_status"] == "not_executed"
    assert row["violations"] == []
    assert row["not_available"][0]["kind"] == "members_not_in_dataset"


# ---- checker 注册表（§11.1 authority 分档 + 禁区扫描） ----------------------------
def test_checker_registry_authority_and_scan():
    reg = check_cmd._checker_registry("out/revc-fd1")
    checkers = reg["checkers"]
    assert len(checkers) == 18
    by_auth = {}
    for c in checkers:
        by_auth.setdefault(c["authority"], []).append(c["checker_id"])
    assert len(by_auth["kicad_authoritative"]) == 5
    assert len(by_auth["deterministic_screening"]) == 4
    assert len(by_auth["screening_or_external_required"]) == 6
    assert len(by_auth["external_required"]) == 3
    assert all(c["source"] == "spec_built_in" for c in checkers)
    assert reg["vision_candidates"] == 0
    assert scan_forbidden_core_fields(reg) == []
    assert reg["consumption"]["stale_plan_reason"] is None


# ---- §11.2 残差：合成树（E 计算/not_available 三态/stale 降级） -------------------
def _make_fd_tree(tmp_path, tamper_snapshot=False):
    a3 = tmp_path / "a3"
    ff1 = tmp_path / "ff1"
    fc2 = tmp_path / "fc2"
    for d in (a3, ff1, fc2):
        d.mkdir()
    (a3 / "net-registry.json").write_text(
        json.dumps({"registry_snapshot_hash": "REG-X"}), encoding="utf-8")
    (a3 / "constraints.json").write_text("{}", encoding="utf-8")
    (a3 / "structures.json").write_text("{}", encoding="utf-8")

    def fsha(p):
        import hashlib
        return hashlib.sha256(p.read_bytes()).hexdigest()

    snap = {
        "registry_snapshot_hash": "REG-X",
        "constraints_sha256": fsha(a3 / "constraints.json"),
        "structures_sha256": fsha(a3 / "structures.json"),
        "placement_snapshot_sha256": fsha(
            __import__("pathlib").Path(
                __import__("pcbflow.config", fromlist=["x"])
                .AUDIT_P3_PLACEMENT_CSV)),
        "board_snapshot_sha256": fsha(
            __import__("pathlib").Path(
                __import__("pcbflow.config", fromlist=["x"])
                .AUDIT_P3_BOARD)),
    }
    if tamper_snapshot:
        snap["constraints_sha256"] = "0" * 64
    plan = {
        "plan_id": "FF-T-0001", "authority": "planning_advisory",
        "snapshot": snap,
        "controls": [{"kind": "reserve_corridor", "control_id": "CTL-1"}],
        "resources": [
            {"resource_id": "layer_capacity:board", "kind": "layer_capacity",
             "state": "available", "net_ids": [], "relation_ids": [],
             "demand": {"value": 100.0, "unit": "mm2", "basis": ["t"]},
             "supply": {"value": 300.0, "unit": "mm2"},
             "reserve": {"value": 0.0, "unit": "mm2"},
             "margin": {"value": 200.0, "unit": "mm2"}},
            {"resource_id": "via_budget:board", "kind": "via_budget",
             "state": "missing_basis", "net_ids": [], "relation_ids": [],
             "demand": {"value": 0, "unit": "vias",
                        "basis": ["missing_basis:fab_capability_table"]},
             "margin": {"value": None, "unit": "vias"}},
            {"resource_id": "corridor:t", "kind": "corridor",
             "state": "available", "net_ids": ["N1"],
             "demand": {"value": 1.0, "unit": "mm"}},
            {"resource_id": "escape:t", "kind": "escape_slots",
             "state": "low_margin", "net_ids": [],
             "demand": {"value": 1, "unit": "channels"}},
            {"resource_id": "power:t", "kind": "power_return_space",
             "state": "resource_deficit", "net_ids": [],
             "demand": {"value": 10, "unit": "mm2"}},
        ],
        "residuals": [], "residuals_note": "n/a",
    }
    (ff1 / "feedforward-plan.json").write_text(
        json.dumps(plan), encoding="utf-8")
    replay = {
        "definition": {"denominator": 10, "committed": 8, "planned_sat": 9},
        "executed_routes": [_route("N1", [[0, 0.0, 0.0, 10.0, 0.0]],
                                   vias=[1, 2])],
    }
    (fc2 / "replay-plan.json").write_text(json.dumps(replay),
                                          encoding="utf-8")
    (fc2 / "residual-certs.json").write_text(json.dumps(
        {"counts": {"SAT": 1, "UNSAT": 2, "UNKNOWN": 3},
         "unsat_without_certificate": 0}), encoding="utf-8")
    return a3, ff1, fc2


def test_residuals_math_and_not_available(tmp_path, monkeypatch):
    a3, ff1, fc2 = _make_fd_tree(tmp_path)
    monkeypatch.setattr(check_cmd, "A3_DIR", str(a3))
    monkeypatch.setattr(check_cmd, "FF1_DIR", str(ff1))
    out = check_cmd.build_ff_residuals(out_dir_rel=str(fc2))
    assert out["stale_plan_reason"] is None
    rows = {r["residual_id"]: r for r in out["rows"]}
    # RES-LC-1：actual=10mm×0.35=3.5，E=3.5-100=-96.5
    assert rows["RES-LC-1"]["actual"]["value"] == pytest.approx(3.5, abs=1e-6)
    assert rows["RES-LC-1"]["E"]["value"] == pytest.approx(-96.5, abs=1e-6)
    # RES-LC-2：final margin=300-3.5=296.5，E=296.5-200=96.5
    assert rows["RES-LC-2"]["actual"]["value"] == pytest.approx(296.5,
                                                                abs=1e-6)
    # RES-UNRES-1/2：三态 5；未落板 2
    assert rows["RES-UNRES-1"]["actual"]["value"] == 5
    assert rows["RES-UNRES-2"]["actual"]["value"] == 2
    # via_budget missing_basis → not_available（实际观测列账 2，不成 residual）
    na = {e.get("residual_id"): e for e in out["not_available"]
          if e.get("residual_id")}
    assert "RES-VIA-1" in na
    assert na["RES-VIA-1"]["actual_observed"]["value"] == 2
    assert "missing_basis" in na["RES-VIA-1"]["reason"]
    # 四资源族 + reserve → not_available 有因
    kinds = [e for e in out["not_available"]
             if e.get("dimension") == "demand_vs_consumption"
             and e.get("residual_id") is None]
    assert len(kinds) >= 4
    assert any(e["dimension"] == "reserve_vs_actual_reserve"
               for e in out["not_available"])
    # §9.1 同构消费面
    cons = out["consumption"]
    assert cons["feedforward_plan_hash"]
    assert cons["plan_id"] == "FF-T-0001"
    assert cons["controls_declared_consumed"] == []
    assert cons["controls_ignored"]
    assert cons["declared_consumed"] and cons["consumption_contract"][
        "actually_read"]
    assert scan_forbidden_core_fields(out) == []


def test_residuals_stale_degrades_to_not_available(tmp_path, monkeypatch):
    a3, ff1, fc2 = _make_fd_tree(tmp_path, tamper_snapshot=True)
    monkeypatch.setattr(check_cmd, "A3_DIR", str(a3))
    monkeypatch.setattr(check_cmd, "FF1_DIR", str(ff1))
    out = check_cmd.build_ff_residuals(out_dir_rel=str(fc2))
    assert out["stale_plan_reason"]
    assert "snapshot_mismatch" in out["stale_plan_reason"]
    assert out["rows"] == []
    assert any("stale_plan" in e["reason"] for e in out["not_available"])


# ---- kicad_authoritative 档：DRC ledger 消费（hash 输入） -------------------------
def test_kicad_authoritative_from_ledger(tmp_path, monkeypatch):
    fc2 = tmp_path / "fc2"
    (fc2 / "drc").mkdir(parents=True)
    (fc2 / "drc" / "final-all.json").write_text(json.dumps(
        {"violations": [{"type": "track_width", "severity": "error"},
                        {"type": "silk_over_copper", "severity": "warning"}],
         "unconnected_items": [{}, {}, {}]}), encoding="utf-8")
    (fc2 / "drc" / "baseline-all.json").write_text(json.dumps(
        {"violations": [], "unconnected_items": [{}, {}, {}, {}, {}]}),
        encoding="utf-8")
    reads = []
    rows = check_cmd.run_kicad_authoritative(reads, str(fc2))
    by_id = {r["checker_id"]: r for r in rows}
    assert by_id["CHK-WIDTH"]["verdict"] == "fail"
    assert by_id["CHK-WIDTH"]["violation_counts"] == {"track_width": 1}
    assert by_id["CHK-SHORT"]["verdict"] == "pass"
    assert by_id["CHK-CONN"]["unconnected_items"] == 3
    assert by_id["CHK-CONN"]["unconnected_new_vs_baseline"] == -2
    # 未映射类型列账（silk_over_copper），不静默丢弃
    assert by_id["CHK-LEDGER-UNMAPPED"]["violation_counts"] == {
        "silk_over_copper": 1}
    assert all(r["evidence"]["sha256"] for r in rows)


# ---- 探针电池判定（合成 DRC JSON；板文本确定性） -----------------------------------
def test_probe_board_deterministic_and_guards(tmp_path):
    t1 = check_cmd.build_probe_board("probe-width")
    t2 = check_cmd.build_probe_board("probe-width")
    assert t1 == t2 and "(segment" in t1 and '(net "N1")' in t1
    proj = json.loads(check_cmd.build_probe_project("probe-width"))
    assert proj["board"]["design_settings"]["rules"]["min_track_width"] == 0.2
    with pytest.raises(ValueError):
        check_cmd.build_probe_board("nope")
    assert cli.main(["check", "--select", "probe_board"]) == \
        cli.config.EXIT_FAILED
    assert cli.main(["check", "--select", "probe_battery"]) == \
        cli.config.EXIT_FAILED


def test_probe_battery_detection(tmp_path):
    drc_root = tmp_path / "probes"
    for p in check_cmd.PROBES:
        d = drc_root / p["probe"] / "drc"
        d.mkdir(parents=True)
        if p["checker_id"] == "CHK-CONN":
            payload = {"violations": [], "unconnected_items": [{}]}
        else:
            payload = {"violations": [{"type": p["expected_types"][0],
                                       "severity": "error"}],
                       "unconnected_items": []}
        (d / "probe-drc.json").write_text(json.dumps(payload),
                                          encoding="utf-8")
    clean = drc_root / check_cmd.PROBE_CLEAN / "drc"
    clean.mkdir(parents=True)
    (clean / "probe-drc.json").write_text(json.dumps(
        {"violations": [], "unconnected_items": []}), encoding="utf-8")
    bat = check_cmd.build_probe_battery(str(drc_root))
    assert bat["gate"] == {"expected": 5, "detected": 5,
                           "clean_control_ok": True, "battery_100": True}
    # 阴性对照失败（注入 error 违规）→ battery_100 False
    (clean / "probe-drc.json").write_text(json.dumps(
        {"violations": [{"type": "clearance", "severity": "error"}],
         "unconnected_items": []}), encoding="utf-8")
    bat = check_cmd.build_probe_battery(str(drc_root))
    assert bat["gate"]["battery_100"] is False
    assert bat["gate"]["detected"] == 5
    # DRC 缺失 → detected=None（不伪造）
    bat = check_cmd.build_probe_battery(str(tmp_path / "absent"))
    assert all(r["detected"] is None for r in bat["results"]
               if "checker_id" in r)


# ---- ⑤ envelope 门语义（探针缺失=yellow，不误报 pass） ----------------------------
def test_check_envelope_unknown_without_probe(tmp_path, monkeypatch):
    a3, ff1, fc2 = _make_fd_tree(tmp_path)
    monkeypatch.setattr(check_cmd, "A3_DIR", str(a3))
    monkeypatch.setattr(check_cmd, "FF1_DIR", str(ff1))
    out_dir = tmp_path / "fd1"
    out_dir.mkdir()
    env = check_cmd.build_envelope(out_dir_rel=str(out_dir),
                                   fc2_dir=str(fc2))
    assert env["status"] == "unknown" and env["verdict"] == "yellow"
    assert env["data"]["gate"]["checker_validation"][
        "probe_battery_100"] is None


# ---- ⑥ waiver 红线：approved 恒空 + 候选待批 + 赤字不入候选 -----------------------
def test_waiver_ledger_red_lines(tmp_path):
    led = signoff_cmd.build_waiver_ledger(str(tmp_path))
    assert led["approved"] == []
    for c in led["candidates"]:
        assert c["approver"] is None
        # created_at 属 §12.1 批准字段，人工批准时才落值（禁区键禁入核心产物）
        assert "created_at" not in c
        assert "pending_approval" in c["status"]
        assert c["expiry"]
    assert scan_forbidden_core_fields(led) == []
    # FC2 真实台账接入（dangling×3 + 基线 silk/courtyard 聚合）
    fc2 = tmp_path / "fc2"
    (fc2 / "drc").mkdir(parents=True)
    (fc2 / "replay-plan.json").write_text(json.dumps(
        {"execution_ledger": {"final_all": {
            "new_warning_detail": ["track_dangling:x", "via_dangling:y",
                                   "track_dangling:z"]}}}), encoding="utf-8")
    (fc2 / "drc" / "baseline-all.json").write_text(json.dumps(
        {"violations": [{"type": "silk_over_copper", "severity": "warning"},
                        {"type": "courtyards_overlap",
                         "severity": "warning"}]}), encoding="utf-8")
    led = signoff_cmd.build_waiver_ledger(str(fc2))
    assert len(led["candidates"]) == 4  # 3 dangling + 1 基线聚合
    assert all("constraint_id" in c for c in led["candidates"])
    # 前馈资源赤字绝不入候选（§12.1 红线）
    assert all("resource_deficit" not in c["reason"]
               for c in led["candidates"])


# ---- ⑥ 重放（Rev-C 冻结基线轨） + 签核包结构 --------------------------------------
def test_signoff_replay_and_package(monkeypatch):
    """R28 板锚参数化：重放链的板输入钉冻结夹具板（8029f5ff=冻结 fc3 件的
    构建输入板）→ 原全部 byte-exact 断言零改动、原强度成立；live 板差异登记
    见 test_signoff_replay_live_board_diff_exactly_anchor。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    replay = signoff_cmd.build_replay()
    assert replay["all_byte_exact"] is True
    assert len(replay["regenerated"]) == 6
    # FC3 ④ 升级：fc1 route-plan 转冻结 pin（不重生成），pin 2→3
    assert len(replay["double_send_pins"]) == 3
    fc1_pin = next(p for p in replay["double_send_pins"]
                   if p["product"].startswith("out/revc-fc1/"))
    assert fc1_pin["matches_pin"] is True and fc1_pin["rerun"] is None
    assert scan_forbidden_core_fields(replay) == []
    pkg = signoff_cmd.build_package()
    items = {s["item"]: s for s in pkg["sections"]}
    assert len(pkg["sections"]) == 13
    assert items["structures snapshot"]["status"] == "present_unapproved"
    assert items["advisory appendix"]["status"] == "empty_by_design"
    assert pkg["signoff_body"]["external_signoff"] is False
    assert pkg["signoff_body"]["human_approval"] is False
    assert pkg["known_open"]
    env = signoff_cmd.build_envelope()
    assert env["data"]["gate"]["dry_run_package_ok"] is True
    assert env["data"]["gate"]["production_signoff_ready"] is False
    # 批准计数随仓库 approvals 输入状态（确认点 #5 消费后=已批条数）
    import os
    from pcbflow import config as cfg
    ap = os.path.join(cfg.PCBFLOW_ROOT, "out/revc-fd1/approvals/"
                                         "waiver-approvals.json")
    expected = 4 if os.path.exists(ap) else 0
    assert env["data"]["gate"]["waiver_approved_count"] == expected
    assert scan_forbidden_core_fields(env) == []


def test_signoff_replay_live_board_diff_exactly_anchor():
    """R4 三步法③ live 板集成用例 + 历史差异登记（R28 规范资产）。

    live 板（≠冻结锚）下：唯一非 byte-exact 重放行恰=fc3 route-plan；其磁盘/
    重建**全计划**叶级 diff 恰=板锚 3 叶（旧值=冻结锚 8029f5ff、新值=live 板
    实测 sha）；掩码 3 叶后全计划 canonical byte-exact（语义等价对照）。
    板回锚 → all_byte_exact=True（fail-closed，豁免不固化为永久通道）。"""
    anchor = _fc3_disk_plan()["zero_write"]["live_board_sha256"]
    live = hashing.sha256_file(config.REVC_BOARD)
    replay = signoff_cmd.build_replay()
    bad = {r["product"] for r in replay["regenerated"]
           if not r["byte_exact"]}
    if live == anchor:
        assert replay["all_byte_exact"] is True
        return
    assert bad == {FC3_ROUTE_PLAN}
    assert all(p["matches_pin"] for p in replay["double_send_pins"])
    regen = route_cmd.build_products(**FC3_REGEN_KW)["route_plan"]["obj"]
    diff = _leaf_diff(_fc3_disk_plan(), regen)
    assert set(diff) == set(ANCHOR_LEAVES)
    for leaf in ANCHOR_LEAVES:
        assert diff[leaf] == (anchor, live)
    assert hashing.canonical_json_bytes(
        _mask_anchor_leaves(_fc3_disk_plan())) == \
        hashing.canonical_json_bytes(_mask_anchor_leaves(regen))


def test_negative_control_non_anchor_replay_tamper_detected(
        monkeypatch, tmp_path):
    """负对照（R28 硬约束）：钉板全 byte-exact 前提下注入差异必须仍被检出。

    对照组：tmp 逐字节副本 → all_byte_exact=True（钉板口径自证）；
    注入①（非锚，删字段）：副本删 via_accounting → False 且失败行恰=该副本；
    注入②（非锚，重建侧）：重建件删一条 lane → 叶级 diff 超出锚叶集=检出；
    注入③（锚值篡改，非登记配对）：锚叶改伪值 → 同样 False。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "route-plan.json"
    with open(os.path.join(config.PCBFLOW_ROOT, FC3_ROUTE_PLAN), "rb") as f:
        copy_path.write_bytes(f.read())
    _patch_replay_fc3_product(monkeypatch, str(copy_path))
    assert signoff_cmd.build_replay()["all_byte_exact"] is True
    obj = json.loads(copy_path.read_text(encoding="utf-8"))
    del obj["via_accounting"]  # 注入①：非锚（删 route_plan 字段）
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    replay = signoff_cmd.build_replay()
    assert replay["all_byte_exact"] is False
    assert {r["product"] for r in replay["regenerated"]
            if not r["byte_exact"]} == {str(copy_path)}
    # 注入②：非锚（重建侧候选几何篡改——删一条 lane）
    regen = route_cmd.build_products(**FC3_REGEN_KW)["route_plan"]["obj"]
    del regen["lanes"][0]
    assert set(_leaf_diff(_fc3_disk_plan(), regen)) != set(ANCHOR_LEAVES)
    # 注入③：锚值篡改（非「冻结锚→live 锚」登记配对）同样必须检出
    pristine = _fc3_disk_plan()
    pristine["zero_write"]["live_board_sha256"] = "ff" * 32
    copy_path.write_text(json.dumps(pristine), encoding="utf-8")
    assert signoff_cmd.build_replay()["all_byte_exact"] is False


@pytest.mark.xfail(strict=True, reason="负对照：非锚差异（删 via_accounting）"
                                       "必须使重放门 fail（R28）")
def test_negative_control_replay_green_must_fire_on_tamper(
        monkeypatch, tmp_path):
    """以原始断言形态直证「注入非锚差异→仍然 fail」（红即预期，xfail）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "route-plan.json"
    obj = _fc3_disk_plan()
    del obj["via_accounting"]
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    _patch_replay_fc3_product(monkeypatch, str(copy_path))
    assert signoff_cmd.build_replay()["all_byte_exact"] is True


# ---- ⑥ 批准消费（approvals 输入 → approved 侧 + 漂移检测） -------------------------
def test_waiver_approval_consumption(tmp_path):
    fc2 = tmp_path / "fc2"
    (fc2 / "drc").mkdir(parents=True)
    (fc2 / "replay-plan.json").write_text(json.dumps(
        {"execution_ledger": {"final_all": {
            "new_warning_detail": ["track_dangling:x", "track_dangling:y"]}}}),
        encoding="utf-8")
    (fc2 / "drc" / "baseline-all.json").write_text("{}", encoding="utf-8")
    out_dir = tmp_path / "fd1"
    (out_dir / "approvals").mkdir(parents=True)
    ledger = signoff_cmd.build_waiver_ledger(out_dir_rel=str(out_dir),
                                             fc2_dir=str(fc2))
    assert len(ledger["candidates"]) == 2 and ledger["approved"] == []
    # 批准第 1 条（reason 须与候选精确一致）
    reason1 = ledger["candidates"][0]["reason"]
    (out_dir / "approvals" / "waiver-approvals.json").write_text(
        json.dumps({"approvals": [{"candidate_index": 1,
                                   "decision": "approved",
                                   "reason": reason1,
                                   "approver": "用户",
                                   "approved_via": "测试批注",
                                   "expiry": "下一 rev"}]}), encoding="utf-8")
    ledger = signoff_cmd.build_waiver_ledger(out_dir_rel=str(out_dir),
                                             fc2_dir=str(fc2))
    assert len(ledger["approved"]) == 1
    assert ledger["approved"][0]["waiver_id"] == "WV-0001"
    assert ledger["approved"][0]["approver"] == "用户"
    assert len(ledger["candidates"]) == 1
    assert ledger["approval_drift"] == []
    assert scan_forbidden_core_fields(ledger) == []
    # reason 不一致 → 漂移不合并
    (out_dir / "approvals" / "waiver-approvals.json").write_text(
        json.dumps({"approvals": [{"candidate_index": 2,
                                   "decision": "approved",
                                   "reason": "被篡改的理由",
                                   "approver": "x",
                                   "approved_via": "y"}]}), encoding="utf-8")
    ledger = signoff_cmd.build_waiver_ledger(out_dir_rel=str(out_dir),
                                             fc2_dir=str(fc2))
    assert ledger["approved"] == []
    assert len(ledger["approval_drift"]) == 1
    assert len(ledger["candidates"]) == 2


# ---- CLI：check/signoff 出 stub（db stub 保留） ------------------------------------
def test_cli_check_signoff_wired():
    from pcbflow import config
    out = signoff_cmd.build_products(select="summary")
    assert out["payload"]["obj"]["command"] == "signoff"
    obj = check_cmd.build_products(select="checker_registry")["payload"]["obj"]
    assert obj["artifact_kind"] == "checker_registry"
    # db 仍为 specified stub（未建造如实报）
    import io
    from unittest import mock

    class _Buf:
        def __init__(self):
            self.buffer = io.BytesIO()

    with mock.patch("sys.stdout", _Buf()):
        rc = cli.main(["db"])
    assert rc == config.EXIT_NOT_IMPLEMENTED
