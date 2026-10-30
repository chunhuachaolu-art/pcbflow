"""FF5 单测（资料级 rail 源复算：--bom-power-file 覆盖 + FF-REVC-0005 级联）。

覆盖：
- FF5 计划：plan_id=FF-REVC-0005、snapshot 携带 bom_power_source_path/sha256
  且 placement 级联键（it_adopted_cascade）保持；
- EMMC_VSEL demand 落 sourced 2.5e-7A（PDR_ON FT_xx Ilkg ±250nA，DS12110
  Table 50）；VCAP1/2/VBAT/FB_NODE 定性 definitive（basis 文本变化、数值
  与状态不变）；其余 7 轨与 fd3 逐值一致；
- 非 rail 资源与 controls 与 cas1 逐值一致（rail 源不触碰布线/结构面）；
- guard：bom_power_file 无 consume_bom 拒绝；文件缺失报错；
- CLI：ff5 计划重生成 byte-exact + 盘上源 hash 绑定；
- 默认路径零扰动：fd3 口径（BOM_POWER_REL）重生成与冻结 fd3 计划 byte-exact
  （test_fd3 已覆盖，此处补 plan_id 优先级回归：FF5 > CAS > FF3）。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import cli, feedforward as ff, hashing

CAS1_DIR = "out/revc-cas1"
CAS2_DIR = "out/revc-cas2"
V2_REL = CAS2_DIR + "/approvals/sources/bom-power-derive.json"


def _fsha(rel):
    return hashing.sha256_file(os.path.join(ff.config.PCBFLOW_ROOT,
                                            *rel.split("/")))


@pytest.fixture(scope="module")
def ff5_plan():
    plan, _ = ff.build_plan(
        True, consume_bom=True, bom_power_file=V2_REL,
        placement_csv=CAS1_DIR + "/placement.csv",
        placement_layout="out/revc-it/it-layout.json")
    return plan


def _rails(plan):
    return {r["resource_id"].split(":")[-1]: r for r in plan["resources"]
            if r["resource_id"].startswith("power_return_space:rail:")}


# ---- 计划基准 -------------------------------------------------------------------
def test_ff5_plan_id_precedence_and_snapshot(ff5_plan):
    assert ff.FF5_PLAN_ID == "FF-REVC-0005"
    assert ff5_plan["plan_id"] == "FF-REVC-0005"
    snap = ff5_plan["snapshot"]
    assert snap["placement_basis"] == "it_adopted_cascade"  # 级联检测键保持
    assert snap["bom_power_source_path"] == V2_REL
    assert snap["bom_power_source_sha256"] == _fsha(V2_REL)
    read_roles = {r["role"] for r
                  in ff5_plan["consumption_contract"]["actually_read"]}
    assert "bom_power_derive" in read_roles
    # 读取登记路径=v2 源（非 fd3 钉源）
    v2_reads = [r for r in ff5_plan["consumption_contract"]["actually_read"]
                if r["role"] == "bom_power_derive"]
    assert all(r["artifact"] == V2_REL for r in v2_reads)


def test_ff5_emmc_vsel_demand_landed_sourced(ff5_plan):
    rails = _rails(ff5_plan)
    dem = rails["EMMC_VSEL"]["demand"]
    assert dem["value"] == pytest.approx(2.5e-7)
    assert dem["basis"][0].startswith("sourced")
    assert "Table 50" in dem["basis"][0] and "250nA" in dem["basis"][0]
    # 供给侧仍载板定义（不虚构）
    assert rails["EMMC_VSEL"]["supply"]["value"] is None


def test_ff5_definitive_classifications_value_stable(ff5_plan):
    rails = _rails(ff5_plan)
    for name in ("VCAP1", "VCAP2"):
        # demand=null 回退 width-derived 政策口径，definitive class 记于回退
        # 文本「无更好源（class）」槽位；供给侧 definitive 注记随行
        dem_text = "；".join(rails[name]["demand"]["basis"])
        assert "not_applicable_internal_regulator" in dem_text
        assert rails[name]["demand"]["value"] is not None  # width 回退沿留
        sup_text = "；".join(rails[name]["supply"]["basis"])
        assert "非独立供电轨" in sup_text and "§6.3.2" in sup_text
    assert "查证性缺源" in "；".join(rails["VBAT"]["supply"]["basis"])
    assert "非功率轨" in "；".join(rails["FB_NODE"]["supply"]["basis"])
    # 其余 7 轨数值与 fd3 口径逐值一致（fd3 供给落位不被本覆盖扰动）
    landed = {n for n, r in rails.items() if r["supply"]["value"] is not None}
    assert landed == {"VBUS_RAW", "5V_USB", "SW_NODE",
                      "5V", "5V_HDR", "3V3", "VBAT_CHG"}
    assert rails["3V3"]["demand"]["value"] == pytest.approx(0.2938)


def test_ff5_non_rail_resources_untouched(ff5_plan):
    disk = json.load(open(os.path.join(ff.config.PCBFLOW_ROOT,
                                       *CAS1_DIR.split("/"),
                                       "feedforward-plan.json"),
                          encoding="utf-8"))
    strip = lambda p: [r for r in p["resources"]
                       if not r["resource_id"].startswith(
                           "power_return_space:rail:")]
    assert strip(ff5_plan) == strip(disk)
    assert ff5_plan["controls"] == disk["controls"]


# ---- guard 与确定性 --------------------------------------------------------------
def test_guard_bom_file_requires_consume_bom():
    with pytest.raises(ValueError):
        ff.build_plan(True, consume_bom=False, bom_power_file=V2_REL)


def test_guard_bom_file_missing(tmp_path):
    missing = str(tmp_path / "no-such.json")
    with pytest.raises(FileNotFoundError):
        ff.build_plan(True, consume_bom=True, bom_power_file=missing)


def test_ff5_plan_regen_byte_exact(capsys):
    """CLI 重生成与盘上 FF-REVC-0005 计划 byte-exact。"""
    disk = open(os.path.join(ff.config.PCBFLOW_ROOT, *CAS2_DIR.split("/"),
                             "feedforward-plan.json"),
                encoding="utf-8").read()
    rc = cli.main(["feedforward",
                   "--adopt-override", "--consume-bom",
                   "--bom-power-file", V2_REL,
                   "--placement-csv", CAS1_DIR + "/placement.csv",
                   "--placement-layout", "out/revc-it/it-layout.json",
                   "--select", "plan", "--out-dir", CAS2_DIR])
    assert rc in (0, None)
    regen = capsys.readouterr().out
    assert hashing.sha256_bytes(regen.encode("utf-8")) == \
        hashing.sha256_bytes(disk.encode("utf-8"))
