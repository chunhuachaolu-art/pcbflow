"""CAS1 会话测试（确认点 #4 已批：IT 布局采纳级联收口；SPEC §7.4/§9.4/§15）。

覆盖：
- 转换：it-layout→placement.csv 确定性（双跑 byte-exact）+ 采纳快照/转换
  证明一致性（moved=13、锚件零移动、CSV sha 与 conversion.json 相符）；
- FF 级联计划：plan_id=FF-REVC-0004、placement 六 hash 绑定=采纳快照、
  基线 p3 绑定沿留 baseline_placement_sha256、resources/controls 与 fd3
  逐字节一致（fd3 口径沿留）、comparison place_match/stale、禁区扫描；
- ④ 级联：mode=it_adoption_cascade、§9.4 转换证明闭环（cascade_binding
  matched）、viol=70 与 IT dry-run ramps/lanes 逐字节一致、缺覆盖/错布局
  →stale 如实（不静默消费）；
- ⑤ 绑定闭环：placement_basis_closure matched + 负例（绑定篡改→stale）；
- ⑥ 重放：cas1 六件（FF 4+route 2）byte-exact、waiver 台账=fd3（输入
  未变）、包 known_open=3、探针电池=fd3；
- 默认路径零扰动：fd3 口径重生成 byte-exact；fd3 的 adopt extras 无
  placement 参数（历史口径不漂移）。
"""

import copy
import json
import os

import pytest

from pcbflow import check_cmd, config, coplace_cmd, envelope, feedforward, \
    hashing, route_cmd, signoff_cmd

IT_LAYOUT = "out/revc-it/it-layout.json"
CAS_DIR = "out/revc-cas1"
FD3_DIR = "out/revc-fd3"
CAS_PLAN = CAS_DIR + "/feedforward-plan.json"
FD3_PLAN = FD3_DIR + "/feedforward-plan.json"
IT_ROUTE_PLAN = "out/revc-it/route-plan.json"
B1_LAYOUT = "out/revc-b1/layout.json"

CAS_VIOL = 70  # IT 实测（详报 15）；级联 ④ 必须保持

# ---- R28 板锚参数化（铜环案 R4 三步法；2026-09-12 重设计批） ---------------------
# 真实板 2026-09-11 被并行工作流 ripup1 改写（8029f5ff→dbfea089，铜环案裁定书
# 事实 C）；route_cmd 把实测板 sha 嵌进 route_plan 的 pins/zero_write（锚）。
# 冻结件 byte-exact 活比较改锚期望参数化（R4 三步法②）：夹具板=仓库在案冻结
# 快照（裁定书 §3：三份快照逐字节相同），只读引用、零复制、零写入。
FROZEN_BOARD_SHA = \
    "8029f5ff6948f4abeda9cd04f78b6eaf481a462e97d3ce85ecbc024573111849"
FROZEN_BOARD_SNAPSHOT = os.path.join(
    config.PCBFLOW_ROOT, os.pardir, os.pardir, "design/coreboard/kicad/"
    "stm32h743-coreboard-revc/snapshots/live-ripup1-pre/"
    "stm32h743-coreboard-revc.kicad_pcb")
PINS_ANCHOR_LEAF = "live_board_zero_write_witness.sha256"


def _frozen_board_abs():
    """冻结夹具板绝对路径（fail-closed：sha 必须=登记锚=冻结 IT 件所记锚）。"""
    p = os.path.normpath(FROZEN_BOARD_SNAPSHOT)
    assert hashing.sha256_file(p) == FROZEN_BOARD_SHA, "冻结夹具板自身漂移"
    it_anchor = _load(IT_ROUTE_PLAN)["pins"]["live_board_zero_write_witness"][
        "sha256"]
    assert it_anchor == FROZEN_BOARD_SHA, "冻结 IT 件板锚与登记锚不符"
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


def _mask_pins_anchor(pins):
    """锚期望参数化：pins 板锚叶置哨兵后比较（语义等价对照）。"""
    obj = copy.deepcopy(pins)
    obj["live_board_zero_write_witness"]["sha256"] = "<board-anchor>"
    return obj


def _load(rel):
    with open(rel, encoding=config.ENCODING) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cas_plan():
    return _load(CAS_PLAN)


# ---- 转换执行（确认点 #4 已批部分） -------------------------------------------
def test_conversion_deterministic_and_matches_snapshot():
    lay = _load(IT_LAYOUT)
    b1 = coplace_cmd.to_placement_csv(lay)
    b2 = coplace_cmd.to_placement_csv(lay)
    assert b1 == b2
    with open(CAS_DIR + "/placement.csv", "rb") as f:
        assert f.read() == b1
    conv = _load(CAS_DIR + "/conversion.json")
    assert conv["output"]["sha256"] == hashing.sha256_bytes(b1)
    assert conv["input"]["sha256"] == hashing.sha256_file(IT_LAYOUT)
    assert conv["moved_refs"] == sorted(
        p["ref"] for p in lay["placements"] if p.get("moved"))
    assert len(conv["moved_refs"]) == 13
    assert conv["roles"] == {"anchor_locked": 10, "baseline_unchanged": 49,
                             "it_optimized": 13}
    assert conv["execution"].startswith("approved_no_board_write")


# ---- FF 级联计划（FF-REVC-0004） ----------------------------------------------
@pytest.fixture(scope="module")
def cas_ff():
    return feedforward.build_products(
        out_dir_rel=CAS_DIR, adopt_override=True, consume_bom=True,
        placement_csv=CAS_DIR + "/placement.csv",
        placement_layout=IT_LAYOUT)


def test_cas_plan_id_and_binding(cas_ff, cas_plan):
    plan = cas_ff["plan"]["obj"]
    assert plan["plan_id"] == "FF-REVC-0004"
    assert plan["plan_id"] == cas_plan["plan_id"]
    snap = plan["snapshot"]
    assert snap["placement_basis"] == "it_adopted_cascade"
    assert snap["placement_snapshot_sha256"] == \
        hashing.sha256_file(CAS_DIR + "/placement.csv")
    assert snap["placement_snapshot_sha256"] == \
        hashing.sha256_file(CAS_DIR + "/placement.csv")
    assert snap["baseline_placement_sha256"] == \
        hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV)
    assert snap["adopted_layout_sha256"] == hashing.sha256_file(IT_LAYOUT)
    # 落盘计划与重生成逐字节一致（双发）
    assert hashing.canonical_json_bytes(plan) == \
        hashing.canonical_json_bytes(cas_plan)


def test_cas_plan_fd3_caliber_preserved(cas_ff):
    """fd3 口径沿留：resources/controls 与 fd3 计划逐字节一致（placement
    绑定切换不触碰账本/控制面）。"""
    fd3 = _load(FD3_PLAN)
    plan = cas_ff["plan"]["obj"]
    for key in ("resources", "controls", "control_conflicts",
                "escape_fields_meta"):
        assert hashing.canonical_json_bytes(plan[key]) == \
            hashing.canonical_json_bytes(fd3[key])


def test_cas_comparison_and_envelope(cas_ff):
    comp = cas_ff["comparison"]["obj"]
    env = cas_ff["envelope"]["obj"]
    assert comp["placement_snapshot_match"] is True
    assert comp["stale_plan_check"]["stale_plan"] is False
    pa = comp["placement_adoption"]
    assert pa["placement_basis"] == "it_adopted_cascade"
    assert "确认点 #4 已批" in pa["confirmation"]
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert not envelope.scan_forbidden_core_fields(cas_ff["plan"]["obj"])
    assert any(i["role"] == "placement_adopted" for i in env["inputs"])


def test_cas_plan_guards():
    with pytest.raises(ValueError):
        feedforward.build_plan(adopt_override=False, consume_bom=True)
    with pytest.raises(ValueError):
        feedforward.build_plan(adopt_override=False,
                               placement_csv=CAS_DIR + "/placement.csv")


# ---- ④ 级联重发 ---------------------------------------------------------------
@pytest.fixture(scope="module")
def cas_route():
    """R28 板锚参数化：route 链的板输入钉冻结夹具板（8029f5ff=冻结 IT 件的
    构建输入板）→ 含板锚的 pins 键恢复与冻结件 byte-exact（断言原强度保持）。"""
    live = config.REVC_BOARD
    config.REVC_BOARD = _frozen_board_abs()
    try:
        return route_cmd.build_products(
            out_dir_rel=CAS_DIR + "/equivalence",
            ff_plan_path=CAS_PLAN, placement_layout_path=IT_LAYOUT)
    finally:
        config.REVC_BOARD = live


def test_route_cascade_mode_and_closure(cas_route):
    plan = cas_route["route_plan"]["obj"]
    assert plan["mode"] == "it_adoption_cascade"
    pb = plan["plan_binding"]
    assert pb["plan_id"] == "FF-REVC-0004"
    assert pb["stale_plan"] is False
    assert pb["authority_effective"].startswith("upgraded")
    cb = plan["placement_override"]["cascade_binding"]
    assert cb["status"] == "matched"
    assert cb["layout_sha_match"] and cb["converted_csv_sha_match"]
    assert cb["converted_csv_sha256"] == \
        hashing.sha256_file(CAS_DIR + "/placement.csv")
    assert plan["zero_write"]["unchanged"]
    env = cas_route["envelope"]["obj"]
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert env["metrics"]["keepout_control_violations"] == CAS_VIOL


def test_route_cascade_solving_identical_to_it_dry_run(cas_route):
    """级联 ④ 求解面与 IT dry-run 逐字节一致（差异仅 mode/覆盖/绑定三键）。

    R28 板锚参数化：cas_route 夹具已把板输入钉冻结夹具板（=IT 冻结件的构建
    输入板 8029f5ff），故含板锚的 pins 键也恢复 byte-exact——断言体原样保留。
    live 板行为由 test_route_cascade_live_board_pins_diff_exactly_anchor
    另行登记（差异恰=板锚 1 叶）。"""
    plan = cas_route["route_plan"]["obj"]
    it = _load(IT_ROUTE_PLAN)
    for key in ("ramps", "lanes", "solver_runs", "solver_summary",
                "resource_conflicts", "via_accounting", "pins"):
        assert hashing.canonical_json_bytes(plan[key]) == \
            hashing.canonical_json_bytes(it[key])
    assert plan["plan_binding"]["plan_id"] != it["plan_binding"]["plan_id"]


def test_route_cascade_live_board_pins_diff_exactly_anchor():
    """R4 三步法③ live 板集成用例 + 历史差异登记（R28）。

    live 板（≠冻结锚）下重建级联 route：pins 与冻结 IT 件的差异必须恰=板锚
    1 叶（旧值=冻结锚 8029f5ff、新值=live 板实测 sha）；掩码锚叶后 canonical
    byte-exact（语义等价对照）。板回锚（live==冻结锚）时必须全等（fail-closed，
    豁免不固化为永久通道）。"""
    it = _load(IT_ROUTE_PLAN)
    frozen_anchor = it["pins"]["live_board_zero_write_witness"]["sha256"]
    live_sha = hashing.sha256_file(config.REVC_BOARD)
    prods = route_cmd.build_products(
        out_dir_rel=CAS_DIR + "/equivalence", ff_plan_path=CAS_PLAN,
        placement_layout_path=IT_LAYOUT)
    pins = prods["route_plan"]["obj"]["pins"]
    diff = _leaf_diff(it["pins"], pins)
    if live_sha == frozen_anchor:
        assert diff == {}
        return
    assert set(diff) == {PINS_ANCHOR_LEAF}
    assert diff[PINS_ANCHOR_LEAF] == (frozen_anchor, live_sha)
    assert hashing.canonical_json_bytes(_mask_pins_anchor(it["pins"])) == \
        hashing.canonical_json_bytes(_mask_pins_anchor(pins))


def test_negative_control_non_anchor_tamper_detected():
    """负对照（R28 硬约束：不得弱化回归检测）：注入非锚差异必须仍被检出。

    ① 篡改求解面键（lanes 几何）→ 七键 byte-exact 断言必须 fire；
    ② 篡改 pins 非锚字段（snapshot_copy_protocol 文本）→ 掩码等价必须 False；
    ③ 删除 pins 字段（fc2_replay_target）→ 叶级 diff 必须超出锚叶集。"""
    it = _load(IT_ROUTE_PLAN)
    tampered_lanes = copy.deepcopy(it)
    tampered_lanes["lanes"][0]["bus_rows"][0]["assigned"] += 1
    with pytest.raises(AssertionError):
        assert hashing.canonical_json_bytes(tampered_lanes["lanes"]) == \
            hashing.canonical_json_bytes(it["lanes"])
    tampered_pins = copy.deepcopy(it["pins"])
    tampered_pins["snapshot_copy_protocol"] += "（篡改）"
    assert hashing.canonical_json_bytes(_mask_pins_anchor(tampered_pins)) != \
        hashing.canonical_json_bytes(_mask_pins_anchor(it["pins"]))
    deleted = copy.deepcopy(it["pins"])
    del deleted["fc2_replay_target"]
    assert set(_leaf_diff(it["pins"], deleted)) != {PINS_ANCHOR_LEAF}


@pytest.mark.xfail(strict=True, reason="负对照：非锚差异（lanes 几何篡改）必须"
                                       "使 byte-exact 断言 fail（R28）")
def test_negative_control_lane_tamper_breaks_byte_exact():
    """以原始断言形态直证「注入非锚差异→仍然 fail」（红即预期，xfail）。"""
    it = _load(IT_ROUTE_PLAN)
    tampered = copy.deepcopy(it)
    tampered["lanes"][0]["bus_rows"][0]["assigned"] += 1
    assert hashing.canonical_json_bytes(tampered["lanes"]) == \
        hashing.canonical_json_bytes(it["lanes"])


def test_route_cascade_without_override_is_stale():
    prods = route_cmd.build_products(
        out_dir_rel=CAS_DIR + "/equivalence-novr", ff_plan_path=CAS_PLAN)
    plan = prods["route_plan"]["obj"]
    assert plan["plan_binding"]["stale_plan"] is True
    assert plan["plan_binding"]["authority_effective"].startswith(
        "planning_advisory")


def test_route_cascade_wrong_layout_is_unverified():
    prods = route_cmd.build_products(
        out_dir_rel=CAS_DIR + "/equivalence-wrong",
        ff_plan_path=CAS_PLAN, placement_layout_path=B1_LAYOUT)
    plan = prods["route_plan"]["obj"]
    assert plan["mode"] == "it_adoption_cascade_unverified"
    assert plan["plan_binding"]["stale_plan"] is True
    assert plan["placement_override"]["cascade_binding"]["status"] == \
        "mismatch"


# ---- ⑤ 绑定闭环 ----------------------------------------------------------------
def test_check_binding_closure_matched():
    plan = _load(CAS_PLAN)
    reads = []
    binding = check_cmd._binding(plan, reads)
    assert binding["all_match"] is True
    assert binding["stale_plan_reason"] is None
    assert binding["placement_basis_closure"]["status"] == "matched"
    assert any(r["role"] == "binding" and "it-layout" in r["artifact"]
               for r in reads)


def test_check_binding_closure_stale_on_tamper():
    plan = _load(CAS_PLAN)
    plan["snapshot"]["placement_snapshot_sha256"] = "0" * 64
    binding = check_cmd._binding(plan, [])
    assert binding["all_match"] is False
    assert "placement_snapshot_sha256" in binding["stale_plan_reason"]
    assert binding["placement_basis_closure"]["status"] == "mismatch"


def test_check_report_on_disk_binding():
    rep = _load(CAS_DIR + "/check-report.json")
    assert rep["snapshot_check"]["all_match"] is True
    assert rep["snapshot_check"]["placement_basis_closure"]["status"] == \
        "matched"


# ---- ⑥ 重放与包 ----------------------------------------------------------------
def test_signoff_replay_cascade_rows():
    rep = _load(CAS_DIR + "/signoff-replay.json")
    assert rep["all_byte_exact"] is True
    cas = [r for r in rep["regenerated"] if "revc-cas1" in r["product"]]
    assert len(cas) == 6  # FF 4 件 + route 2 件
    assert all(r["byte_exact"] for r in cas)


def test_signoff_waiver_ledger_unchanged():
    with open(CAS_DIR + "/waiver-ledger.json", "rb") as f1, \
            open(FD3_DIR + "/waiver-ledger.json", "rb") as f2:
        assert f1.read() == f2.read()


def test_signoff_package_known_open():
    pkg = _load(CAS_DIR + "/signoff-package.json")
    assert len(pkg["known_open"]) == 3
    cas1 = [e for row in pkg["sections"] for e in row["entries"]
            if e.get("role") == "consumer_4_route_cas1"]
    assert cas1 and cas1[0]["path"] == CAS_DIR + "/route-consumption.json"


def test_probe_battery_and_envelopes():
    with open(CAS_DIR + "/probe-battery.json", "rb") as f1, \
            open(FD3_DIR + "/probe-battery.json", "rb") as f2:
        assert f1.read() == f2.read()
    for name in ("feedforward-envelope.json", "envelope-route.json",
                 "envelope-check.json", "envelope-signoff.json"):
        env = _load(CAS_DIR + "/" + name)
        assert env["status"] == "ok" and env["verdict"] == "pass", name


# ---- 默认路径零扰动 --------------------------------------------------------------
def test_fd3_default_regeneration_byte_exact():
    prods = feedforward.build_products(
        out_dir_rel=FD3_DIR, adopt_override=True, consume_bom=True)
    assert prods["plan"]["sha256"] == hashing.sha256_file(FD3_PLAN)
    assert prods["plan"]["obj"]["plan_id"] == "FF-REVC-0003"
    assert "placement_basis" not in prods["plan"]["obj"]["snapshot"]


def test_fd3_replay_extras_have_no_placement_keys():
    extras = signoff_cmd._adopt_replay_extras(FD3_DIR, consume_bom=True)
    assert len(extras) == 4
    assert all("placement_csv_path" not in e for e in extras)
    assert all("placement_layout_path" not in e for e in extras)
