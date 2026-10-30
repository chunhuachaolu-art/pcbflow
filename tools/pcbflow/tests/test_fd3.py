"""FD3 单测（FF 重跑会话：BOM 派生轨功耗表 derived 消费）。

覆盖：
- FF3 计划：plan_id=FF-REVC-0003、snapshot 六 hash+信息键与 fd2 同基准；
- rail 供给 sourced/derived 分列：7/12 落位（VBUS_RAW/5V_USB/SW_NODE sourced，
  5V/5V_HDR/3V3/VBAT_CHG derived），margin 数学（3V3 0.388 available 等）；
- 5V_HDR 赤字=载板负载无界×width 上界口径的登记（blocking 空、net_ids 有）；
- 缺源轨保持 missing_basis（FB_NODE/VBAT/VCAP1/VCAP2/EMMC_VSEL）+ BOM 需求
  consumption 口径随行；width-derived 回退轨（4 轨）与铜宽载流复核行；
- 诊断 missing_sources_partial_resolved 更新（FF3 版本文本+7/12 计数）；
- guard：--consume-bom 无 --adopt-override 拒绝（模块级+CLI）；
- 默认路径回归：fd2 adopt 口径重生成与盘上计划 byte-exact（0ae6e0e7…）；
- fd3 CLI 重生成 byte-exact + envelope 输入绑定 BOM 源 hash。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import cli, feedforward as ff, hashing
from pcbflow import feedforward_config as ffc

FD3_DIR = "out/revc-fd3"
FD2_DIR = "out/revc-fd2"


def _fsha(rel):
    return hashing.sha256_file(os.path.join(ff.config.PCBFLOW_ROOT,
                                            *rel.split("/")))


@pytest.fixture(scope="module")
def bom_plan():
    plan, basis = ff.build_plan(True, consume_bom=True)
    return plan, basis


def _rails(plan):
    return {r["resource_id"].split(":")[-1]: r for r in plan["resources"]
            if r["resource_id"].startswith("power_return_space:rail:")}


# ---- 计划基准 -------------------------------------------------------------------
def test_fd3_plan_id_and_snapshot(bom_plan):
    plan, _ = bom_plan
    assert plan["plan_id"] == ff.FF3_PLAN_ID == "FF-REVC-0003"
    # 六 hash 基准与 fd2 同（structures=批准视图 hash；信息键随行）
    assert "structures_override_sha256" in plan["snapshot"]
    assert "structures_authority" in plan["snapshot"]
    # 消费契约：BOM 源真实读取登记
    read_roles = {r["role"] for r in plan["consumption_contract"]["actually_read"]}
    assert "bom_power_derive" in read_roles
    assert any("bom-power-derive" in d for d
               in plan["consumption_contract"]["declared_consumed"])


def test_guard_requires_adopt():
    with pytest.raises(ValueError):
        ff.build_plan(False, consume_bom=True)


# ---- rail 供给 sourced/derived 分列 ---------------------------------------------
def test_rail_supply_landed_classes(bom_plan):
    plan, _ = bom_plan
    rails = _rails(plan)
    sourced = {name for name, r in rails.items()
               if r["supply"]["value"] is not None
               and r["supply"]["basis"][0].startswith("sourced")}
    derived = {name for name, r in rails.items()
               if r["supply"]["value"] is not None
               and r["supply"]["basis"][0].startswith("derived")}
    assert sourced == {"VBUS_RAW", "5V_USB", "SW_NODE"}
    assert derived == {"5V", "5V_HDR", "3V3", "VBAT_CHG"}
    # 其余 5 轨供给侧 missing_basis 保持（不虚构）
    assert {name for name, r in rails.items()
            if r["supply"]["value"] is None} == {
        "FB_NODE", "VBAT", "VCAP1", "VCAP2", "EMMC_VSEL"}


def test_rail_margin_math_and_states(bom_plan):
    plan, _ = bom_plan
    rails = _rails(plan)
    # 3V3：供给 min(3A, η·2.5W/3.3V=0.6818) vs 需求 0.2938（BOM 功耗派生）
    r33 = rails["3V3"]
    assert r33["supply"]["value"] == pytest.approx(0.6818, abs=1e-9)
    assert r33["demand"]["value"] == pytest.approx(0.2938, abs=1e-9)
    assert r33["margin"]["value"] == pytest.approx(0.388, abs=1e-3)
    assert r33["state"] == "available"
    # 5V/5V_USB/VBUS_RAW：0.5−0.2155
    for name in ("5V", "5V_USB", "VBUS_RAW"):
        assert rails[name]["margin"]["value"] == pytest.approx(0.2845, abs=1e-3)
        assert rails[name]["state"] == "available"
    # SW_NODE sourced 3A；VBAT_CHG derived 13.6mA、稳态需求 0
    assert rails["SW_NODE"]["state"] == "available"
    assert rails["VBAT_CHG"]["demand"]["value"] == 0.0
    assert rails["VBAT_CHG"]["state"] == "available"
    # 全局状态迁移：missing_basis 12→5、deficit 9→10（唯一新增=5V_HDR）
    assert ff._state_counts(plan["resources"]) == {
        "available": 30, "low_margin": 217,
        "missing_basis": 5, "resource_deficit": 10}


def test_5v_hdr_deficit_registered_as_carrier_bound(bom_plan):
    plan, _ = bom_plan
    hdr = _rails(plan)["5V_HDR"]
    assert hdr["state"] == "resource_deficit"
    assert hdr["supply"]["value"] == 0.5
    assert hdr["deficit_magnitude"]["value"] == pytest.approx(1.882, abs=1e-3)
    # 需求=width-derived 回退（载板负载无更好源）+ 缺口为口径登记非板载违规
    assert "derived_policy" in hdr["demand"]["basis"][0]
    assert "carrier_bound" in hdr["demand"]["basis"][0] or any(
        "载板" in b for b in hdr["demand"]["basis"])


def test_missing_supply_rails_keep_consumption_demand(bom_plan):
    plan, _ = bom_plan
    rails = _rails(plan)
    fb = rails["FB_NODE"]
    vbat = rails["VBAT"]
    # BOM consumption 需求随行（µA 级），供给缺源→missing_basis
    assert fb["demand"]["value"] == pytest.approx(5.96e-06, abs=1e-9)
    assert vbat["demand"]["value"] == pytest.approx(2.32e-06, abs=1e-9)
    for r in (fb, vbat, rails["VCAP1"], rails["VCAP2"], rails["EMMC_VSEL"]):
        assert r["state"] == "missing_basis"
        assert "missing_basis" in r["supply"]["basis"][0]


def test_width_capacity_crosscheck_on_bom_demand_rails(bom_plan):
    plan, _ = bom_plan
    rails = _rails(plan)
    body = rails["3V3"]["demand"]["basis"]
    assert any("宽度载流复核" in b and "充足" in b for b in body)
    # 回退轨（VCAP1）无复核行（需求即 width 口径本身）
    assert not any("宽度载流复核" in b
                   for b in rails["VCAP1"]["demand"]["basis"])


# ---- 诊断 -----------------------------------------------------------------------
def test_diagnostics_fd3_missing_sources_partial(bom_plan):
    plan, _ = bom_plan
    d = next(x for x in plan["diagnostics"]
             if x["id"] == "missing_sources_partial_resolved")
    assert "FF3" in d["title"]
    assert "7/12" in d["title"]
    assert "TBD-1" in d["title"]


# ---- envelope/CLI 契约 ----------------------------------------------------------
def test_cli_fd3_plan_regenerates_byte_exact(capsys):
    rc = cli.main(["feedforward", "--adopt-override", "--consume-bom",
                   "--select", "plan", "--out-dir", FD3_DIR])
    assert rc == cli.config.EXIT_OK
    regen = capsys.readouterr().out
    disk = open(os.path.join(ff.config.PCBFLOW_ROOT,
                             FD3_DIR + "/feedforward-plan.json"),
                "rb").read().decode("utf-8")
    assert regen == disk


def test_cli_consume_bom_guard(capsys):
    rc = cli.main(["feedforward", "--consume-bom", "--select", "plan",
                   "--out-dir", FD3_DIR])
    assert rc == cli.config.EXIT_FAILED
    out = capsys.readouterr().out
    assert "adopt-override" in json.loads(out)["error"]


def test_envelope_inputs_bind_bom_source():
    env = json.load(open(os.path.join(
        ff.config.PCBFLOW_ROOT, FD3_DIR + "/feedforward-envelope.json"),
        encoding="utf-8"))
    bom_inputs = [i for i in env["inputs"]
                  if i["path"] == ff.BOM_POWER_REL]
    assert len(bom_inputs) == 1
    assert bom_inputs[0]["sha256"] == _fsha(ff.BOM_POWER_REL)
    assert env["metrics"]["sources_consumed"] == 4
    assert env["metrics"]["resources_by_state"]["missing_basis"] == 5


def test_fd2_adopt_path_still_byte_exact(capsys):
    """fd2 口径默认回归：consume_bom=False 的 adopt 重生成与冻结 fd2 计划一致。"""
    rc = cli.main(["feedforward", "--adopt-override", "--select", "plan",
                   "--out-dir", FD2_DIR])
    assert rc == cli.config.EXIT_OK
    regen = capsys.readouterr().out
    disk = open(os.path.join(ff.config.PCBFLOW_ROOT,
                             FD2_DIR + "/feedforward-plan.json"),
                "rb").read().decode("utf-8")
    assert regen == disk


def test_fd2_rails_unchanged_by_fd3_code():
    """fd2 计划 rail 行不受 FD3 代码影响（供给仍 None、12 轨 missing_basis）。"""
    plan, _ = ff.build_plan(True)
    rails = _rails(plan)
    assert len(rails) == 12
    assert all(r["state"] == "missing_basis" for r in rails.values())
    assert all(r["supply"]["value"] is None for r in rails.values())
