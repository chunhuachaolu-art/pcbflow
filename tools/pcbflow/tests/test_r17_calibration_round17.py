"""R17 执行包测试：reader 判读迭代第十七轮收口（CAL-R17-CLOSE 包 B）——
轴1 仪器轮（渲染分辨率倍增，axis-experiment-plan-r17-r20 stage1
R17=A1_render_resolution_x2；renders-r17 四图全新渲染 dpi 640→1280、
framing 预注册 a1084c14→witness 见证 e979bec2；判读指引=
observation-guidance-r17.md 07c520be=r15 基座 d5babc93 机械变换派生：
§2–§7 判据逐字保留+§5A 描述性同步[橙 326460/绿 903366 px 仪器事实]、
R17T/R17B 前缀随指引落盘固化；GT/阈值/协议零变更）+ run-r17 主记录
复算+预注册假设（axis-plan-r17-resolution-double）三分判据裁决：
(a) M1=top 全旗聚合弃权率 ≤0.671429（r16 零变更基线 27/35=0.771429
绝对降幅 ≥0.10=计划件显著收益阈值）不成立、(b) M1 ≥0.771429 成立⇒
字母=reject（轴1 证伪：分辨率非瓶颈[或视觉编码器尺寸上限抵消增益]；
转向轴2/轴3）+ 机制观察单列：呈现尺寸自述 4/12 派次[约 1000px×3+约
1500px×1] vs 仪器像素界 4009/4010 px（呈现端缩放截断像素增益的机制候
选，如实单列不断言）/1280 新可见细节旗 5 条（top 弃权 4+bottom 非弃权
1+判正常对照 2=双向分化）/M2=bottom 9/12=0.75 vs r16 基线 12/14=
0.857143（improved 改善方向如实单列：零旗标派次 2[prep1-bottom-i1/i2，
r13–r16 无先例]+黑点族 8 旗全弃权 vs r16 12+bottom courtyard 旗 1 全
弃权）/M3=黑点族 8/M4=top 逐实例弃权率极差 0.333333 + 实验对照账
（axis_experiment_ledger：(M1,M2,M3,M4)=(0.88, 0.75, 8, 0.333333)；
R17 排序位置待 R18/R19 后按冻结规则比较、不预写结论）+ 守门 G1/G2 均
True 维持、不触发出局 + GT 双口径 union 0/13（r16 的 1/13 未复现=单实
例命中不稳定如实）、agreement 0/13 + 代表配置（top-i1 tie 按先序+
bottom-i1 唯一）joint not_met、连续=0 + development 域 dev-record
（s65 生成）。

结构照 test_r16_calibration_round16.py 先例，仅输入与轮次常量不同
（R17=轴1 仪器轮：预注册于 r17-prep-record json（ceba4fef），链=
axis-experiment-plan-r17-r20（b6ec6467，用户 2026-09-09「三条轴单独/
组合/全组合尝试，选择收益最大的继续」指令操作化冻结件）→r17-prep-
record→r15 指引机械变换派生 r17 指引（07c520be）→renders-r17 新渲染
（非字节复用）→12 次盲读；判据=三分（≤0.671429、带内、≥0.771429=
reject），分列不合并；APR-0011 门与主通道判据各自独立、互不凌驾；
R17T/R17B 前缀随指引 §6 落盘固化=r13→r15 路径回归、无需派发层覆盖）。

覆盖：
- 盲读原文（reader-raw-r17-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  R17T/R17B 前缀（随指引落盘固化）、实例旗数 8/8/9/4/3/5 与弃权
  8/8/6/3/2/4、逐派次旗数（prep1-bottom-i1/i2 两格零旗=r13–r16 无先
  例首现）、哈希与 run-r17 登记一致、拒收清单为空；
- r17-prep-record.json（预注册件）：三分判据逐字（(a) ≤0.671429 →
  supported/(b) ≥0.771429 → reject/带内 → marginal）、guards、
  changed_variables 三件（render-resolution-x2-r17 主变量+§5A px 描
  述性同步+轮次标识机械同步）、no_instrument_change=false、
  instrument_change.changed=true、guidance_reuse
  mechanical_transform_derive（edit_list 三处+derived_sha256=07c520be
  全值+byte_size 19878→19959=delta 81）、no_loosening_note 反放宽条款
  逐字、measurement_design 五条、pre_round_review
  satisfied_by_probe_and_plan；
- guidance-r17 派生哈希锚（07c520be 全值）+§5A px 同步句在位（橙
  326460/绿 903366）+§4 逐字保留（反放宽条款）+r15 基座（d5babc93）+
  协议 v1（22dc7337）+framing/witness（a1084c14/e979bec2）+axis-plan
  冻结件（b6ec6467）+renders-r17 四 PNG sha 逐一实测[bottom 两图字节
  同 0c2d5c00]；
- calibration-run-r17.json：盘上 canonical byte 一致；字母=reject
  +22/25=0.88 落 (b) 支（整数交叉相乘复核）；r16 基线 live 值在案
  （top 27/35=0.771429、bottom 12/14=0.857143）且从内嵌输入重放复算
  一致；视角层聚合复算（top 极差 0.333333、bottom 0.133333）；GT 双
  口径 union 0/13+agreement 0/13（r16 的 1/13 未复现）；代表配置
  （top-i1 tie 按先序+bottom-i1 唯一）joint not_met、连续=0；机制观
  察（呈现尺寸 4/12 自述 vs 仪器 4009/4010+1280 新细节旗 5+top 分型
  8/14/0+黑点 8 旗全弃权+4 派次判正常）；守门 G1/G2+early_stop 未触
  发；通道归因（几何门 0→0、类别门 1→0、视角门 0）+courtyard 追踪链
  r8..r17+reroute 追踪（产量链 r17=1、滥用型 0）；输入哈希（冻结工
  件逐件实测=登记）；
- round17-dev-record.json（s65 生成）：canonical、kind、round_label=
  r17、域声明、run_record_ref 实测 sha（d444c4a5）、hypothesis_test_i
  与 run-r17 逐字一致（verdict=reject）、诊断结果与代表配置口径一致、
  实验对照账 axis_experiment_ledger（M1..M4 四键实测+axis-plan 冻结
  规则+不预写结论）、R16→R17 方向性观察（reject/呈现尺寸机制/improved
  /union 未复现/守门/联合 not_met 连续=0）、联合评价趋势（r5→r17 逐
  轮表、连续计数 0→0）、preregistration_chain 与 run-r17 冻结工件一
  致、next_iteration_targets 五条（R18=轴2 黑点类专项探针先证/R19=
  轴3 判据侧/阶段2 组合按冻结规则/呈现端缩放机制候选 960dpi 登记[本
  轮不做]/留出集时机须用户+GT 关闭延续）、is_gate=False、
  in_calibrated_range 恒 False；
- s65 重跑：build_dev_record 同参重建 byte-exact 一致+防覆写护栏语义
  （字节等同→幂等跳过零覆写、不同→fail-closed）+s64 零 dev-record
  写入分包边界（round17-dev-record 不在 s64 写集）；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；R17T/R17B 前缀随指引落盘固化入
  naming_constraints；受保护三文件 sha256 前 8 断言；s64 脚本锚
  （80ef579c）+零阈值改动断言（calibration.py=dac80b7e）。

只读 out/（生成器模式）：零子进程/零写盘/零网络（s65 幂等重跑例外=
字节等同零覆写路径）。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-09-r17"
ROUND_LABEL = "r17"
DECLARED_DATE = "2026-09-09"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r17-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r17-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r17-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r17-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r17-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r17-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r17-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r17-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r17-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r17-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r17-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r17-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "c5c242e5", "prep1-top-i1": "8185be49",
    "applied-top-i2": "7b7e0819", "prep1-top-i2": "7b26fcbd",
    "applied-top-i3": "434a5daf", "prep1-top-i3": "3f08cb21",
    "applied-bottom-i1": "4404f838", "prep1-bottom-i1": "9c8c801c",
    "applied-bottom-i2": "ad31d3ca", "prep1-bottom-i2": "cc5002c6",
    "applied-bottom-i3": "e8c7f01b", "prep1-bottom-i3": "f37ab8ca",
}
READER_IDS = {
    "applied-top-i1": "reader-r17-top-i1",
    "prep1-top-i1": "reader-r17-top-i1",
    "applied-top-i2": "reader-r17-top-i2",
    "prep1-top-i2": "reader-r17-top-i2",
    "applied-top-i3": "reader-r17-top-i3",
    "prep1-top-i3": "reader-r17-top-i3",
    "applied-bottom-i1": "reader-r17-bottom-i1",
    "prep1-bottom-i1": "reader-r17-bottom-i1",
    "applied-bottom-i2": "reader-r17-bottom-i2",
    "prep1-bottom-i2": "reader-r17-bottom-i2",
    "applied-bottom-i3": "reader-r17-bottom-i3",
    "prep1-bottom-i3": "reader-r17-bottom-i3",
}
#: 逐派次旗数（盘面实测口径；prep1-bottom-i1/i2 两格零旗=r13–r16 无先例）
EXPECT_PART_COUNTS = {
    "applied-top-i1": 5, "prep1-top-i1": 3,
    "applied-top-i2": 5, "prep1-top-i2": 3,
    "applied-top-i3": 5, "prep1-top-i3": 4,
    "applied-bottom-i1": 4, "prep1-bottom-i1": 0,
    "applied-bottom-i2": 3, "prep1-bottom-i2": 0,
    "applied-bottom-i3": 4, "prep1-bottom-i3": 1,
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
#: 逐实例旗数/弃权数/弃权率（盘面实测口径；与 run-r17 聚合一致）
EXPECT_COUNTS = {"top-i1": 8, "top-i2": 8, "top-i3": 9,
                 "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 5}
EXPECT_ABSTAIN = {"top-i1": 8, "top-i2": 8, "top-i3": 6,
                  "bottom-i1": 3, "bottom-i2": 2, "bottom-i3": 4}
EXPECT_RATES = {"top-i1": 1.0, "top-i2": 1.0, "top-i3": 0.666667,
                "bottom-i1": 0.75, "bottom-i2": 0.666667, "bottom-i3": 0.8}
EXPECT_R16_RATES = {"top-i1": 0.666667, "top-i2": 0.928571,
                    "top-i3": 0.666667, "bottom-i1": 1.0,
                    "bottom-i2": 0.8, "bottom-i3": 0.75}
#: 主通道三分判据描述性边界锚（(a)/(b) 基线=run-r16 双侧复算 27/35）
TOP_R16_BASELINE_LIVE = "27/35"
BOTTOM_R16_BASELINE_LIVE = "12/14"
#: 黑点族判正常摘录锚（4 派次判正常中 2 例逐字；reading_notes）
BLACK_DOT_NORMAL_ANCHORS = [
    ("prep1-top-i1", "右上角两枚同尺寸纵向对齐的黑色实心圆点（与安装孔常规形态一致）"),
    ("prep1-bottom-i1", "左上角两个小黑圆点两处形态一致、与焊盘轮廓均可见间隙，未见冲突"),
]
#: 受保护文件（R17-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: s64/s65 脚本锚（R17 比对生成器/dev-record 生成器；冻结）
S64_SHA256_FIRST8 = "80ef579c"
CALIBRATION_SHA256_FIRST8 = "dac80b7e"
#: r17 指引（本轮唯一判读依据、r15 基座机械变换派生；07c520be 全值）
GUIDANCE_R17_SHA256 = ("07c520be528708a509e4ec3f9c869a1fbe9ec59fa985813ea2"
                       "0627acd0e70616")
GUIDANCE_R15_BASE_SHA256 = ("d5babc9338e4d063652d5b217b85b1fb731ce53d76f16b"
                            "2a5d79e8267c4ee267")
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r17.md": "07c520be",
    "out/v3-tl2/calibration/observation-guidance-r15.md": "d5babc93",
    "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json": "b6ec6467",
    "out/v3-tl2/calibration/r17-prep-record.json": "ceba4fef",
    "out/v3-tl2/calibration/round16-dev-record.json": "589fe62f",
    "out/v3-tl2/calibration/r16-prep-record.json": "46fbd15b",
    "out/v3-tl2/calibration/r15-prep-record.json": "4c6cd919",
    "out/v3-tl2/calibration/round15-dev-record.json": "e981897c",
    "out/v3-tl2/calibration/render-framing-r17.json": "a1084c14",
    "out/v3-tl2/calibration/render-witness-r17.json": "e979bec2",
    "out/v3-tl2/calibration/render-framing-r14b.json": "7004b017",
    "out/v3-tl2/calibration/render-witness-r14b.json": "b63771f9",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r17.json": "d444c4a5",
    "out/v3-tl2/calibration/calibration-run-r16.json": "2c1f8265",
    "out/v3-tl2/calibration/ground-truth-v1.json": "828b6b5f",
    "out/v3-tl2/calibration/ground-truth-v2.json": "e1cb63d5",
}
#: renders-r17 四图全新渲染（1280dpi；bottom 两图字节同=0c2d5c00）
R17_PNG_SHA256 = {
    "applied-top.png":
        "b35315efc7b941404cd4d30fbcbb6159d86be0cd88e9bda1d336421c5dc7a1b5",
    "prep1-top.png":
        "bdce8bbbb9d05ac52ee5c64c4724063662c33c591869090b6d16e4d2d90ef3b8",
    "applied-bottom.png":
        "0c2d5c00dd09200fc2cbf03bf5682cb9421c32f11146660189da6b285a1be4a0",
    "prep1-bottom.png":
        "0c2d5c00dd09200fc2cbf03bf5682cb9421c32f11146660189da6b285a1be4a0",
}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s64():
    spec = importlib.util.spec_from_file_location(
        "s64_calibration_r17_compare",
        os.path.join(REPO, "scripts", "s64_calibration_r17_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _s65():
    spec = importlib.util.spec_from_file_location(
        "s65_calibration_r17_devrecord",
        os.path.join(REPO, "scripts", "s65_calibration_r17_devrecord.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r17.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round17-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _raw_text(key):
    return open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                             RAW_FILES[key]), encoding="utf-8").read()


def _view_aggregate(run, view):
    names = [n for n in INSTANCE_ORDER if n.startswith(view)]
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r17_files_valid_structure_and_prefixes():
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == READER_IDS[key]
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] in ("applied-top.png", "prep1-top.png",
                                "applied-bottom.png", "prep1-bottom.png")
        assert isinstance(d["reading_notes"], str) and d["reading_notes"]
        for f in img["flags"]:
            assert READER_FLAG_KEYS <= set(f)           # 六键投影齐备
            assert f["abstain"] in (True, False)
            assert 0.0 <= f["confidence"] <= 1.0
            assert len(f["frame_box_pct"]) == 4
            assert f["location_evidence"]
            prefix, view = f["flag_id"][:4], key.split("-", 1)[1].split(
                "-i", 1)[0]
            expected = "R17T" if view == "top" else "R17B"
            assert prefix == expected, (key, f["flag_id"])
    # 逐派次旗数（12/12；prep1-bottom-i1/i2 两格零旗=r13–r16 无先例首现）
    for key, n in EXPECT_PART_COUNTS.items():
        d = _load(RAW_FILES[key])
        assert len(d["per_image"][0]["flags"]) == n, key
    # 拒收清单固化（37 旗全过 calibration fail-closed 校验，0 拒收）
    run, _ = _run_record()
    assert run["parse_rejections"] == []
    assert sum(EXPECT_PART_COUNTS.values()) == run["reader"]["flag_count"][
        "total"] == 37


# ---------------------------------------------------------------------------
# 预注册件（r17-prep-record）三分判据与轴1 仪器变更声明
# ---------------------------------------------------------------------------

def test_r17_prep_record_three_branch_criteria_and_instrument_change():
    prep = _load("r17-prep-record.json")
    assert prep["kind"] == "tl2_calibration_r17_prep_record"
    assert prep["round_id_constant"] == ROUND_ID
    assert prep["round_label"] == ROUND_LABEL
    assert prep["declared_date"] == DECLARED_DATE
    assert prep["schema_version"] == "3.0"
    assert prep["evaluation_domain"]["declared"] == "development"
    assert prep["evaluation_domain"]["in_calibrated_range"] is False
    # 三分判据逐字（r17-prep-record hypothesis_test.adjudication 原文）
    adj = prep["hypothesis_test"]["adjudication"]
    assert prep["hypothesis_test"]["hypothesis_id"] == \
        "axis-plan-r17-resolution-double"
    assert "1280dpi" in prep["hypothesis_test"]["hypothesis"]
    assert adj["supported"].startswith(
        "M1（top 全旗聚合弃权率，12 派次全口径）≤ 0.671429")
    assert adj["reject"].startswith("M1 ≥ 0.771429")
    assert adj["marginal"].startswith("0.671429 < M1 < 0.771429")
    assert "轴1 证伪" in adj["reject"] and "分辨率非瓶颈" in adj["reject"]
    run0, _ = _run_record()
    assert "转向轴2/轴3" in run0["hypothesis_test"]["measurement"][
        "letter_branch"]
    assert "G1=bottom courtyard 非弃权 0/0/0 维持" in adj["guards"] and \
        "G2=guard_ok=True" in adj["guards"]
    assert "bottom 侧观察（M2/黑点族 M3）" in \
        adj["mechanism_observation_separate"]
    assert "0.09064" in adj["metric_lesson_separate"]
    # 轴1 仪器轮声明：changed_variables 三件、instrument_change.changed=true
    cvs = prep["changed_variables"]
    assert [v["id"] for v in cvs] == ["render-resolution-x2-r17",
                                      "guidance-5a-descriptive-px-sync",
                                      "round-identity-sync"]
    assert cvs[0]["axis_id"] == "A1_render_resolution_x2"
    assert prep["no_instrument_change"] is False
    assert prep["instrument_change"]["changed"] is True
    assert "640→1280" in prep["manipulated_factor"] and \
        "唯一仪器实验变量" in prep["manipulated_factor"]
    # 指引机械变换派生声明（非字节复用：§2–§7 逐字保留+§5A 描述性同步）
    gr = prep["guidance_reuse"]
    assert gr["mode"] == "mechanical_transform_derive"
    assert gr["base"] == "observation-guidance-r15.md"
    assert gr["base_sha256"] == GUIDANCE_R15_BASE_SHA256
    assert gr["derived"] == "observation-guidance-r17.md"
    assert gr["derived_sha256"] == GUIDANCE_R17_SHA256
    assert gr["byte_size"] == {"base": 19878, "derived": 19959, "delta": 81}
    assert len(gr["edit_list"]) == 10
    assert "本轮变更声明节正文整体替换" in gr["edit_list"][0]["kind"]
    # 轴计划冻结锚+见证锚
    anchors = gr["chain_anchors"]
    assert anchors["axis_experiment_plan_frozen"]["sha256"] == _sha(
        "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json")
    assert anchors["render_witness_r17_px_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/render-witness-r17.json")
    # 反放宽条款逐字保留+无放宽语义（§5A px 数=仪器事实、非判据）
    assert "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由" \
        in prep["no_loosening_note"]
    assert "不构成任何阈值反向放宽" in prep["no_loosening_note"]
    assert "903366" in prep["no_loosening_note"]
    # 度量设计五条先于盲读冻结+盲读纪律+轮前评审（探针+计划）
    assert [it["item"] for it in prep["measurement_design"]["items"]] == \
        [1, 2, 3, 4, 5]
    assert prep["no_visual_reading"] is True
    assert prep["read_prohibition_compliance"] is True
    assert prep["pre_round_review"]["status"] == "satisfied_by_probe_and_plan"
    # s63 脚本产物锚（R17 预注册件；盘上实测）
    assert _sha("out/v3-tl2/calibration/r17-prep-record.json").startswith(
        "ceba4fef")


def test_guidance_r17_derived_and_frozen_anchors():
    # r17 指引=本轮唯一判读依据：r15 基座机械变换派生（07c520be 全值实测）
    assert _sha("out/v3-tl2/calibration/observation-guidance-r17.md") == \
        GUIDANCE_R17_SHA256
    text = open(os.path.join(CAL_DIR, "observation-guidance-r17.md"),
                encoding="utf-8").read()
    assert "§5A" in text
    assert "仅因形态不熟悉、不确定其设计含义" in text
    # §5A px 同步句在位（仪器事实：橙 326460/绿 903366 px；640 期探针值可考）
    assert "326460" in text and "903366" in text
    assert "640dpi 期探针值为 206632/206052 px" in text
    assert "本轮 1280dpi 实测绿 903366 px" in text
    # R17T/R17B 前缀随指引落盘固化（r13→r15 路径回归；§6 示例前缀即 R17）
    assert "R17T-001" in text and "R17B-001" in text
    # r15 基座（d5babc93）零字节不动+协议 v1+framing/witness+axis-plan
    for rel, first8 in PREREG_ANCHORS.items():
        if rel.endswith("observation-guidance-r17.md"):
            continue                                 # 已全值断言
        assert _sha(rel).startswith(first8), rel
    # renders-r17 四图全新渲染（非字节复用；bottom 两图字节同 0c2d5c00）
    for name, want in R17_PNG_SHA256.items():
        assert _sha("out/v3-tl2/calibration/renders-r17/" + name) == want
    witness = _load("render-witness-r17.json")
    assert witness["renders"]["applied-top"]["sha256"] == \
        R17_PNG_SHA256["applied-top.png"]
    assert witness["renders"]["prep1-top"]["sha256"] == \
        R17_PNG_SHA256["prep1-top.png"]
    assert witness["renders"]["applied"]["sha256"] == \
        R17_PNG_SHA256["applied-bottom.png"]
    assert witness["renders"]["prep1"]["sha256"] == \
        R17_PNG_SHA256["prep1-bottom.png"]
    assert witness["renders"]["applied-top"]["image_wh"] == [4009, 4009]
    assert witness["renders"]["applied"]["image_wh"] == [4010, 4009]
    # 受保护三文件（R17-CLOSE 红线：零改动）
    for rel, first8 in PROTECTED_SHA256_FIRST8.items():
        assert _sha(rel).startswith(first8), rel


# ---------------------------------------------------------------------------
# run-r17 主记录：常量、字母裁决、聚合复算、GT 零命中、门、机制观察
# ---------------------------------------------------------------------------

def test_run_r17_canonical_constants_letter_reject_branch_b():
    run, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(run)    # canonical JSON
    assert run["kind"] == "tl2_calibration_run_r17"
    assert run["round_id"] == ROUND_ID
    assert run["round_label"] == ROUND_LABEL
    assert run["declared_date"] == DECLARED_DATE
    assert run["evaluation_domain"] == "development"
    assert run["schema_version"] == "3.0"
    ht = run["hypothesis_test"]
    # 字母裁决=reject：落支=(b) M1 ≥0.771429（唯一正式裁决）
    assert ht["verdict"] == "reject"
    assert ht["hypothesis_id"] == "axis-plan-r17-resolution-double"
    m = ht["measurement"]
    assert m["verdict"] == "reject"
    assert m["letter_branch"].startswith("(b) M1 ≥0.771429")
    assert m["crit_a_supported_le_0.671429"] is False
    assert m["crit_b_reject_ge_0.771429"] is True
    # 22/25=0.88 落 (b) 支（整数交叉相乘复核，避免浮点）
    assert (m["top_abstain_count_r17"], m["top_abstain_flags_r17"]) == \
        (22, 25)
    assert m["top_abstain_rate_r17"] == 0.88
    assert 22 * 1_000_000 > 671429 * 25                 # > 0.671429（(a) 否）
    assert 22 * 1_000_000 >= 771429 * 25                # ≥ 0.771429（(b) 是）
    assert "整数交叉相乘" in ht["verdict_text"]
    # r16 基线 live 值在案（fail-closed 登记；双侧复算）
    assert m["top_abstain_rate_r16_baseline_live"] == TOP_R16_BASELINE_LIVE
    assert m["top_abstain_rate_r16_baseline_value"] == 0.771429
    assert m["baseline_cross_check"]["r16_top_live"] == "27/35"
    assert m["baseline_cross_check"]["r16_top_registered"] == \
        {"abstain": 27, "flags": 35}
    assert m["baseline_cross_check"]["r16_bottom_live"] == \
        BOTTOM_R16_BASELINE_LIVE
    # 守门通道独立单列（G1/G2 均维持；early_stop 未触发）
    assert m["guard_channel"]["guards_ok"] is True
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    assert g12["g1_ok"] is True and g12["g2_guard_ok"] is True
    assert g12["axis_early_stop_triggered"] is False
    assert g12["g2_geometry_gate_r16"] == 0 and \
        g12["g2_geometry_gate_r17"] == 0
    # 判据原文引用=r17-prep-record adjudication（逐字，共键）
    prep = _load("r17-prep-record.json")
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "guards", "marginal",
              "mechanism_observation_separate", "metric_lesson_separate",
              "reject", "supported"):
        assert q[k] == adj[k], k
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r17-prep-record.json")


def test_run_r17_view_aggregates_recomputed_live():
    run, _ = _run_record()
    run16 = _load("calibration-run-r16.json")
    # 本轮聚合复算（top 22/25、bottom 9/12）
    assert _view_aggregate(run, "top") == (25, 22)
    assert _view_aggregate(run, "bottom") == (12, 9)
    # 基线 live 重放复算（run-r16 内嵌输入；不手工抄数）
    assert _view_aggregate(run16, "top") == (35, 27)
    assert _view_aggregate(run16, "bottom") == (14, 12)
    # 逐实例旗数/弃权数/弃权率（与 r16 对照）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    assert counts == EXPECT_COUNTS
    assert abstains == EXPECT_ABSTAIN
    assert rates == EXPECT_RATES
    r16rates = {n: run16["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER}
    assert r16rates == EXPECT_R16_RATES
    # 视角层三分列（measurement_design item 2）：M4=top 极差 0.333333
    assert run["view_layer"]["top"]["abstain_rate_range"] == 0.333333
    assert run["view_layer"]["bottom"]["abstain_rate_range"] == 0.133333
    assert run["hypothesis_test"]["stratified_observation"]["top"][
        "r17_range"] == 0.333333
    # bottom 侧观察单列（9/12=0.75 vs r16 12/14=0.857143，improved 方向）
    bso = run["hypothesis_test"]["measurement"]["bottom_side_observation"]
    assert (bso["bottom_abstain_flags_r17"],
            bso["bottom_abstain_count_r17"]) == (12, 9)
    assert bso["bottom_abstain_rate_r17"] == 0.75
    assert bso["bottom_abstain_rate_r16_baseline_value"] == 0.857143
    assert bso["bottom_abstain_rate_r16_baseline_live"] == "12/14"
    assert bso["bottom_rate_direction_vs_r16"] == "improved"


def test_run_r17_gt_zero_match_union_agreement():
    run, _ = _run_record()
    dual = run["gt_match_dual"]
    # GT 条目层双口径：union 0/13（r16 的 1/13 未复现）、agreement 0/13
    assert dual["denominator"] == 13
    assert dual["union"]["count"] == 0
    assert dual["union"]["gt_ids"] == []
    assert dual["union"]["gt_recall_union"] == 0.0
    assert dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_ids"] == []
    assert all(g["matched_by_count"] == 0 for g in dual["per_gt"])
    # r16 的首命中对（R16T-001×AP-6）在本轮零命中=单实例命中不稳定
    hit16 = [g for g in _load("calibration-run-r16.json")["gt_match_dual"]
             ["per_gt"] if g["gt_id"] == "GT-REVC-AP-6-R2LED2"][0]
    assert hit16["matched_by_count"] == 1
    # bottom 零匹配属结构性（GT 13 条全部 side=top；gt-audit-r1 bottom
    # GT=无源已关闭）
    assert all(g["side"] == "top" for g in dual["per_gt"])
    assert run["gt_audit_reference"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")
    # 阈值常量零改动（声明常量；只作口径引用）
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0


def test_run_r17_representative_joint_and_metric_ranges():
    run, _ = _run_record()
    # 代表配置=top-i1（中位 8 tie 按先序）+bottom-i1（中位 4 唯一）
    rep = run["representative_configuration"]
    assert rep["members"] == {"top": "top-i1", "bottom": "bottom-i1"}
    assert rep["selection"]["top"]["tie"] is True
    assert rep["selection"]["bottom"]["tie"] is False
    # 代表配置聚合（measurement_design item 4）
    agg = run["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"]) == (12, 11, 0.916667)
    assert (agg["gt_recall_total"], agg["seed_match_rate_total"],
            agg["matches_total"]) == (0.0, 0.0, 0)
    assert agg["abstain_rate_by_view"] == {
        "top": 1.0, "top_fraction": "8/8",
        "bottom": 0.75, "bottom_fraction": "3/4"}
    # APR-0011 门（代表配置）：not_met、连续=0；分列不合并
    comp = run["compliance_representative"]
    assert comp["joint_evaluation"] == "not_met"
    assert comp["consecutive_rounds"]["consecutive_met_count"] == 0
    crit = {c["id"]: c for c in comp["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is False
    # per-metric 实例间范围（measurement_design item 4 三并列）
    mr = run["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"max": 9, "min": 8}
    assert mr["top"]["abstain_rate"] == {"max": 1.0, "min": 0.666667}
    assert mr["bottom"]["flag_count"] == {"max": 5, "min": 3}
    assert mr["bottom"]["matches_total"] == {"max": 0, "min": 0}


def test_run_r17_mechanism_observation_presentation_blackdot_newdetail():
    run, _ = _run_record()
    mo = run["hypothesis_test"]["mechanism_observation"]
    # top 弃权构成分型：接触性 8+存在性 14+其他 0（r16 对照 11/15/1）
    ty = mo["top_abstain_typology"]
    assert ty["type_counts"] == {"contact": 8, "existence": 14,
                                 "other_layer": 0}
    assert ty["top_abstain_flags_total"] == 22
    assert len(ty["rows"]) == 22
    assert ty["r16_reference_counts"] == {"contact": 11, "existence": 15,
                                          "other_layer": 1}
    assert ty["top_abstain_rates_by_instance"] == {
        "top-i1": 1.0, "top-i2": 1.0, "top-i3": 0.666667}
    # 呈现尺寸机制观察：自述绝对呈现尺寸 4 派次 vs 仪器像素界 4009/4010
    psm = mo["presentation_size_mechanism_observation"]
    pc = psm["counts"]
    assert pc["dispatches_with_px_size_self_report"] == 4
    assert pc["dispatches_with_clarity_self_report"] == 12
    assert pc["stated_px_values"] == ["约 1000px 宽", "约 1000×1000",
                                      "约 1000px 宽", "约 1500px"]
    assert pc["instrument_png_image_wh"] == {
        "applied-top": [4009, 4009], "applied-bottom": [4010, 4009],
        "prep1-top": [4009, 4009], "prep1-bottom": [4010, 4009]}
    assert "呈现端缩放" in psm["status"]
    # 1280 新可见细节旗：5 条=top 弃权 4+bottom 非弃权 1+判正常对照 2
    ndf = mo["top_new_detail_flags_1280"]["counts"]
    assert (ndf["new_detail_flags_total"], ndf["new_detail_top_abstain"],
            ndf["new_detail_bottom_non_abstain"],
            ndf["notes_normal_counterparts"]) == (5, 4, 1, 2)
    assert "双向分化" in mo["top_new_detail_flags_1280"]["status"]
    # 黑点族 8 旗全弃权（vs r16 12；连续主导第 5 轮）+4 派次判正常
    bdt = mo["black_dot_tracking"]
    assert bdt["all_abstain"] is True
    assert bdt["by_instance"] == {"bottom-i1": 2, "bottom-i2": 2,
                                  "bottom-i3": 2, "top-i1": 1,
                                  "top-i2": 1, "top-i3": 0}
    assert len(bdt["black_dot_flags"]) == 8
    assert all(f["abstain"] is True for f in bdt["black_dot_flags"])
    assert "4 派次判正常" in bdt["notes_normal_dispositions"]
    # 判正常摘录逐字在案（substring fail-closed）
    for key, excerpt in BLACK_DOT_NORMAL_ANCHORS:
        assert excerpt in _raw_text(key), key
    # bottom 改善通道单列：M2=9/12=0.75 improved（零旗派次 2+黑点 8+旗 1）
    bsm = mo["bottom_side_observation_maintenance"]
    assert bsm["counts"]["bottom_rate_direction_vs_r16"] == "improved"
    assert bsm["counts"]["bottom_abstain_rate_r17"] == 0.75
    assert bsm["counts"]["bottom_abstain_rate_r16_baseline"] == 0.857143
    assert bsm["counts"]["zero_flag_dispatch_count"] == 2
    assert bsm["counts"]["zero_flag_parts"] == ["prep1-bottom-i1",
                                                "prep1-bottom-i2"]
    assert bsm["counts"]["m3_blackdot_abstain_flags_rubric_r17"] == 8
    assert bsm["counts"]["m3_blackdot_rubric_r16_registered"] == 12
    assert "改善方向" in bsm["observation"]
    assert "零旗标派次" in bsm["observation"]
    # 零旗标派次固化（run 件；r13–r16 无先例首现）
    zfp = run["reader"]["zero_flag_parts"]
    assert [p["state"] + "-" + p["instance"]
            for p in zfp["parts"]] == ["prep1-bottom-i1", "prep1-bottom-i2"]


def test_run_r17_channel_attribution_and_courtyard_tracking():
    run, _ = _run_record()
    ca = run["channel_attribution"]
    # 几何门 0→0；guard_ok=True 独立单列
    g1 = ca["channel_1_geometry_gate"]
    assert len(g1["r17_area_ratio_rejected_entries"]) == 0
    assert len(g1["r16_area_ratio_rejected_entries"]) == 0
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    # 类别门 1→0（r16 的 R16T-006 出局条目在本轮未再现）
    g2 = ca["channel_2_category_gate"]
    assert len(g2["r17_category_mismatch_entries"]) == 0
    assert len(g2["r16_category_mismatch_entries"]) == 1
    assert g2["r16_category_mismatch_entries"][0]["flag_id"] == "R16T-006"
    # 通道链自 r6 含 r17；视角门 0 条
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"]["r17"] == 0
    assert chain["category_gate_category_mismatch_by_round"]["r17"] == 0
    assert ca["view_gate_observations"]["r17_entries"] == []
    # courtyard 被动追踪：命中链 r8..r17（r17=0；r16 的 1 未复现）
    ct = run["courtyard_tracking"]
    assert ct["courtyard_matches_r17"] == 0
    assert [ct[f"courtyard_matches_r{r}"] for r in
            (8, 9, 10, 11, 12, 13, 14, 15, 16, 17)] == \
        [1, 0, 1, 3, 0, 0, 0, 0, 1, 0]
    assert len(ct["r17_courtyard_flags"]["abstain"]) == 7
    na = ct["r17_courtyard_flags"]["non_abstain"]
    assert len(na) == 1
    assert (na[0]["flag_id"], na[0]["instance"], na[0]["matches"]) == \
        ("R17T-001", "top-i3", 0)
    # 阈值零改动声明（零期望、不为提高命中调阈值）
    assert "零改动" in ct["threshold_note"]
    # reroute 被动追踪（产量链 r16=2→r17=1；滥用型 r17=0）
    rc = run["hypothesis_test"]["reroute_continuation_r17"]
    assert rc["reroute_total_r17"] == 1
    assert rc["production_chain"]["r17"] == 1
    assert rc["production_chain"]["r16"] == 2
    assert "r17=0" in rc["misuse_chain_note"]


def test_run_r17_input_hashes_and_frozen_chain():
    run, _ = _run_record()
    # 预注册冻结工件：逐件实测 sha 与登记一致（45 件含链锚与新渲染见证）
    arts = run["preregistration"]["frozen_artifacts"]
    assert len(arts) >= 40
    for item in arts:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {a["role"] for a in arts}
    assert "r17_prep_record_preregistration" in roles
    assert "axis_experiment_plan_r17_r20_frozen" in roles
    assert "r16_dev_record_prior_chain" in roles
    assert "observation_guidance_r17_active" in roles
    assert "render_witness_r17_px_witness" in roles
    # 十二件盲读原文哈希与登记一致（fail-closed）
    for key, info in run["reader"]["raw_files"].items():
        assert _sha(info["path_rel"]) == info["sha256"], key
        assert key in RAW_FILES
    # 12 件直读（零改动直读、非盲读违规）、零拒收
    assert all(v["direct_json_parse"] is True and v["repair"] == "no_repair"
               for v in run["reader"]["parse"].values())
    assert run["parse_rejections"] == []
    # 参考轮链锚：run-r16 实测与登记一致
    rr = run["reference_rounds"]
    assert rr["r16_run"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r16.json")
    # instrument_change：轴1 仪器轮（renders-r17 四 PNG 见证逐一对拍）
    ic = run["instrument_change"]
    assert ic["changed"] is True
    assert ic["axis_id"] == "A1_render_resolution_x2"
    assert len(ic["changed_variables_registered"]) == 3
    assert len(ic["renders_registered"]) == 4
    assert all(p["match"] is True for p in ic["renders_registered"])
    assert ic["renders_registered"][0]["sha256_measured"] == \
        ic["renders_registered"][0]["sha256_witness_registered"]
    assert len(ic["unchanged_components"]) == 15


# ---------------------------------------------------------------------------
# round17-dev-record.json（s65 生成）
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round17_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["is_gate"] is False
    # 本轮性质=轴1 仪器轮+新渲染双锚
    assert "轴1 仪器轮" in dev["round_nature"]
    assert "07c520be" in dev["round_nature"]
    assert "renders-r17" in dev["round_nature"] and "非字节复用" in \
        dev["round_nature"]
    assert "changed=true" in dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "第十七轮" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert "第 17 轮" in dev["domain_basis_quote"]
    # run_record_ref=run-r17 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r17.json"
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r17.json")
    assert dev["run_record_ref"]["sha256"].startswith("d444c4a5")
    # 假设裁决节与 run-r17 逐字一致（verdict=reject；(a) 否/(b) 是）
    run, _ = _run_record()
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "reject"
    assert dev["hypothesis_test_i"]["measurement"][
        "crit_a_supported_le_0.671429"] is False
    assert dev["hypothesis_test_i"]["measurement"][
        "crit_b_reject_ge_0.771429"] is True
    assert dev["hypothesis_test_i"]["measurement"][
        "top_abstain_rate_r17"] == 0.88
    assert dev["hypothesis_test_i"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    # 呈现尺寸机制观察字段在案（镜像 run-r17 hypothesis_test）
    assert dev["hypothesis_test_i"]["mechanism_observation"][
        "presentation_size_mechanism_observation"]["counts"][
            "dispatches_with_px_size_self_report"] == 4
    # 诊断结果与 run-r17 一致（代表配置口径：top-i1 tie+bottom-i1 唯一）
    assert "top-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.916667
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    assert dev["diagnostic_result"]["gt_match_dual"]["union"]["count"] == 0
    # instrument_change 镜像 run（轴1 仪器轮）+链与 GT 审计引用
    assert dev["instrument_change"] == run["instrument_change"]
    assert dev["instrument_change"]["changed"] is True
    assert dev["gt_audit_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")
    # 实验对照账：M1..M4 四键实测+冻结规则引用+不预写结论
    ledger = dev["axis_experiment_ledger"]
    assert ledger["this_round_measured"] == {"M1": 0.88, "M2": 0.75,
                                             "M3": 8, "M4": 0.333333}
    assert ledger["frozen_plan_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json")
    assert ledger["frozen_plan_ref"]["sha256"].startswith("b6ec6467")
    assert "不预写结论" in ledger["status"]
    assert "0.771429" in ledger["measured_note"]
    # 预注册链=run-r17 冻结工件逐件实测（与 run 登记一致）+链注锚
    chain = dev["preregistration_chain"]
    for item in run["preregistration"]["frozen_artifacts"]:
        assert chain[item["role"]] == {"path_rel": item["path_rel"],
                                       "sha256": item["sha256"]}
    note = dev["preregistration_chain_note"]
    for anchor in ("b6ec6467", "ceba4fef", "07c520be", "d5babc93",
                   "a1084c14", "e979bec2", "d444c4a5", "62343380",
                   "1f20554a", "0c2d5c00", "选择收益最大的继续"):
        assert anchor in note, anchor


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：R16 基线数值独立复算（top 27/35、
    bottom 12/14；run-r16 内嵌输入）；next_iteration_targets 覆盖 R18=
    轴2 黑点类专项（探针先证）/R19=轴3 判据侧/阶段2 组合按冻结规则/
    呈现端缩放机制候选登记（本轮不做）/留出集运行时机（须用户）+GT 关
    闭延续；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r16"])
    # R16 基线独立复算（内嵌输入）
    run16 = _load("calibration-run-r16.json")
    assert _view_aggregate(run16, "top") == (35, 27)
    assert _view_aggregate(run16, "bottom") == (14, 12)
    # R16→R17 分层/聚合数字在观察中如实引用
    for need in ("12→12", "49→37", "9/14/12→8/8/9", "5/5/4→4/3/5",
                 "10→6", "39→31", "0.795918", "0.837838",
                 "0.671429", "27/35=0.771429", "22/25=0.88", "reject",
                 "12/14=0.857143", "9/12=0.75", "improved",
                 "1.0/1.0/0.666667", "0.666667/0.928571/0.666667",
                 "0.333333", "0.261904", "1.0/0.8/0.75",
                 "0.75/0.666667/0.8", "0/13", "1/13", "未复现",
                 "单实例命中不稳定", "R16T-001", "GT-REVC-AP-6-R2LED2",
                 "R16T-006", "几何门", "类别门", "guard_ok=True",
                 "early_stop_rule", "接触性 11→8", "存在性 15→14",
                 "黑点族", "零旗标派次", "prep1-bottom-i1",
                 "约 1000px", "约 1500px", "4009", "4010", "呈现端缩放",
                 "视觉编码器尺寸上限抵消增益", "1280 新可见细节旗 5 条",
                 "R17B-001", "R17T-001", "0/0/0", "r16=1→r17=0",
                 "轴1 证伪", "转向轴2/轴3", "未读取盘上任何其他文件",
                 "R17T/R17B 前缀随 r17 指引 §6 落盘固化",
                 "各自从头编号", "gt-audit-r1", "不凌驾",
                 "唯一正式裁决"):
        assert need in obs, need
    # 联合评价趋势：r5→r17 逐轮表；连续达标计数 0（R16 后）→0（本轮）
    trend = dev["joint_evaluation_trend"]
    assert [r["round"] for r in trend["by_round"]] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16", "r17"]
    assert trend["by_round"][-1]["abstain_rate_total"] == 0.916667
    assert trend["by_round"][-1]["source"]["sha256"].startswith("d444c4a5")
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "31/37=0.837838" in trend["aggregation_scope_note"]
    # next_iteration_targets 五条（R18/R19/组合/呈现端机制候选/留出+GT）
    nxt = "\n".join(dev["next_iteration_targets"])
    assert len(dev["next_iteration_targets"]) == 5
    assert "R18=轴2" in nxt and "黑点类专项" in nxt
    assert "探针证实" in nxt and "黑点物理来源" in nxt
    assert "guidance-r18=r15 基座+黑点中性仪器注记" in nxt
    assert "非判据" in nxt and "反放宽条款逐字保留" in nxt
    assert "renders-r14b 字节复用" in nxt
    assert "R19=轴3" in nxt and "§4(iii)" in nxt
    assert "判定一致性" in nxt
    assert "阶段2 组合轮按 axis-plan 冻结规则执行" in nxt
    assert "M1 优于 0.771429" in nxt and "R20=该两轴组合" in nxt
    assert "M1 优先照冻结执行" in nxt
    assert "呈现端缩放机制候选" in nxt and "中庸分辨率" in nxt
    assert "~1500px" in nxt and "960dpi" in nxt and "本轮不做" in nxt
    assert "留出集运行时机" in nxt and "须用户拍板" in nxt
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    assert "收敛未宣告" in nxt and "in_calibrated_range 恒 False" in nxt
    assert "人工批准" in nxt
    assert "GT 侧维持全关闭" in nxt and "gt-audit-r1" in nxt
    assert "1f20554a" in nxt and "单实例命中不稳定" in nxt
    # honest_conclusion：reject 如实（轴1 证伪；呈现尺寸机制候选；M2
    # improved 如实；实验对照账四键）
    hc = dev["honest_conclusion"]
    for need in ("reject", "轴1 证伪", "22/25=0.88", "0.771429",
                 "0.671429", "0.916667", "not_met", "0.75", "0.857143",
                 "improved", "零旗标", "4009/4010", "呈现端缩放", "双向分化",
                 "0.333333", "接触性 8+存在性 14", "(0.88, 0.75, 8, 0.333333)",
                 "不预写结论", "非因果证明", "单实例命中不稳定",
                 "分列不合并", "不得冒充留出", "in_calibrated_range 恒 False",
                 "precision/FPR"):
        assert need in hc, need
    # r17 域声明与门语义（in_calibrated_range 恒 False）
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r17-prep-record.json")
    assert dev["is_gate"] is False


def test_s65_rerun_idempotent_and_overwrite_guard():
    """s65 重跑语义：build_dev_record 同参重建 byte-exact 一致；防覆写
    护栏（字节等同→幂等跳过零覆写、不同→fail-closed）；s64 零
    dev-record 写入分包边界（round17-dev-record 不在 s64 写集）。"""
    s65 = _s65()
    dev, disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(s65.build_dev_record()) == disk
    # 声明常量（无 wall-clock）
    assert s65.DECLARED_DATE == "2026-09-09"
    assert s65.ROUND_ID == "2026-09-09-r17"
    assert s65.ROUND_LABEL == "r17"
    assert s65.KIND == "tl2_calibration_round17_dev_record"
    # 三分判据实测锚常量（操作化定义）
    assert (s65.EXPECT_TOP_ABSTAIN_R17, s65.EXPECT_TOP_FLAGS_R17) == (22, 25)
    assert s65.EXPECT_TOP_RATE_R17 == 0.88
    assert (s65.EXPECT_TOP_R16_BASELINE_LIVE,
            s65.EXPECT_TOP_R16_BASELINE_VALUE) == ("27/35", 0.771429)
    assert (s65.EXPECT_BOTTOM_ABSTAIN_R17,
            s65.EXPECT_BOTTOM_FLAGS_R17) == (9, 12)
    assert s65.EXPECT_BOTTOM_RATE_R17 == 0.75
    assert s65.EXPECT_BOTTOM_R16_BASELINE_LIVE == "12/14"
    assert s65.EXPECT_TYPE_COUNTS == {"contact": 8, "existence": 14,
                                      "other_layer": 0}
    assert s65.EXPECT_COURTYARD_NON_ABSTAIN == {"bottom-i1": 0,
                                                "bottom-i2": 0,
                                                "bottom-i3": 0}
    # 实验对照账四键锚（axis-plan benefit_metrics 口径）
    assert (s65.EXPECT_M1, s65.EXPECT_M2, s65.EXPECT_M3, s65.EXPECT_M4) == \
        (0.88, 0.75, 8, 0.333333)
    assert s65.EXPECT_R16_BASELINE_M1_M2_M3_M4 == \
        [0.771429, 0.857143, 12, 0.261904]
    # 防覆写护栏纯函数语义
    assert s65.overwrite_guard(None, b"x") == "write"
    assert s65.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s65.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：round17-dev-record 已存在且字节等同 → main 正常完成
    # （零覆写）
    path = os.path.join(CAL_DIR, "round17-dev-record.json")
    before = open(path, "rb").read()
    s65.main()                                          # 不抛异常=幂等路径
    after = open(path, "rb").read()
    assert before == after                       # 字节零改动
    # 分包边界：s64 零 dev-record 写入（round17-dev-record 由 s65 落盘；
    # s64 只产 run-r17），幂等重跑后该件字节零改动
    s64 = _s64()
    assert not hasattr(s64, "build_dev_record")
    assert hasattr(s64, "build_run")                    # s64 只产 run-r17
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r17.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    """命名约束与门语义：seed_match_rate 注记、递归无越界命名键、
    R17T/R17B 前缀随指引落盘固化在案、阈值常量与比较器零改动、s64 脚本
    锚、字母裁决与门分列。"""
    run, _ = _run_record()
    dev, _ = _run_dev_record()
    nc = run["naming_constraints"]
    assert "R17T-/R17B-" in nc and "随指引落盘固化" in nc
    assert "禁称 precision/FPR" in nc
    # 递归无越界命名键（run 与 dev 全树）
    for doc in (run, dev):
        _assert_no_banned_keys(doc)
    # seed_match_rate 注记常量一致（禁称 precision/FPR）
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 阈值常量零覆盖（声明常量）+比较器脚本锚（冻结）
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert _sha("pcbflow/calibration.py").startswith(CALIBRATION_SHA256_FIRST8)
    assert _sha("scripts/s64_calibration_r17_compare.py").startswith(
        S64_SHA256_FIRST8)
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；零旗标格=2
    # +拒收清单为空
    assert run["hypothesis_test"]["verdict"] == "reject"
    assert run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分开如实记录" in run["hypothesis_test"]["verdict_text"] and \
        "不合并" in run["hypothesis_test"]["verdict_text"]
    assert run["hypothesis_test"]["measurement"][
        "crit_a_supported_le_0.671429"] is False
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    assert [p["state"] + "-" + p["instance"]
            for p in run["reader"]["zero_flag_parts"]["parts"]] == \
        ["prep1-bottom-i1", "prep1-bottom-i2"]
    assert run["parse_rejections"] == []
    # 度量教训单列在 dev-record notes（漂移混杂；不追溯适用；对照账不预写）
    assert "0.09064" in dev["notes"][-1]
    assert "不追溯适用" in dev["notes"][-1]
    assert "不预写结论" in dev["notes"][-1]


def _assert_no_banned_keys(obj, path="doc"):
    if isinstance(obj, dict):
        for banned in ("reader_false_positive_ids",
                       "reader_precision_vs_seed_gt"):
            assert banned not in obj, (path, banned)
        for k, v in obj.items():
            _assert_no_banned_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_banned_keys(v, f"{path}[{i}]")
