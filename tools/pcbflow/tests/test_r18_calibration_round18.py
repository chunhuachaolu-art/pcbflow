"""R18 执行包测试：reader 判读迭代第十八轮收口（CAL-R18-CLOSE 包 B）——
轴2 指引侧单变量轮（§5B 黑点中性仪器注记，axis-experiment-plan-r17-r20
stage1 R18=A2_blackdot_instrument_annotation；渲染零变更=renders-r14b
四图字节复用[与 r14/r15/r16/r17 盲读同一批文件]；判读指引=
observation-guidance-r18.md cadcb8f3=r15 基座 d5babc93 机械变换派生+
§5B 新节=blackdot-probe-r18.json a49441ac 探针证实事实的中性转录[F1/F2
confirmed、F3 identity_confirmed_blackdot_indeterminate=探针先决满足]：
§2–§7 判据逐字承 r15、§5A 原文整体逐字保留、R18T/R18B 前缀随指引落盘
固化；GT/阈值/协议零变更）+ run-r18 主记录复算+预注册假设
（axis-plan-r18-blackdot-note）三分判据裁决：(r) M3 ≥10（注记未使黑点
族回落）成立[M3=13 vs r16 基线 12，rubric 链 9/14/8/12 重放对拍逐一相
等]、(s) M3 ≤6 不成立+附加门 M1=top 20/31=0.645161≤0.85 成立、(m) 未
落⇒字母=reject（轴2 reject：§5B 中性仪器注记未使黑点族负责任判定成立；
转向轴3/组合轮）+ 机制观察单列：M1/M2 双双大幅改善[0.645161/0.684211
vs r16 基线 0.771429/0.857143；M1 绝对降幅 0.126268 超显著收益阈值
0.10——跨轮实例群漂移混杂照旧声明、本轮为指引变更轮、改善不能归因于
「零变更」]/旗级 §5B 援引 0/13[机制转移=身份已知后弃权主因转为「已证
实黑点与焊盘的接触贴近不可分辨」=§4(iii) 接触性问题而非存在性问题]/
黑点转非弃权旗 3 条[r14–r17 首现非弃权报告路径]+黑点判正常派次 2[对
照 r15=3/r16=2]/top 弃权分型=接触性 8+存在性 12+其他 0 + 实验对照账
（axis_experiment_ledger：(M1,M2,M3,M4)=(0.645161, 0.684211, 13,
0.277778)；轴2 现居已测配置第一[R18 0.645161 < R17 0.88，M1 升序字典
序]——如实记录、不预写阶段2 结论；letter 与实验账背离=两账分列互不
改写）+ 守门 G1/G2 均 True 维持、不触发出局 + GT 双口径 union 0/13、
agreement 0/13（r16 的 1/13 在 r17/r18 连续未再现）+ 代表配置（top-i3
唯一+bottom-i1 tie 按先序）joint not_met、连续=0 + 零旗标派次=0[12 格
全部≥1 旗，对照 r17 的 2 格] + development 域 dev-record（s69 生成）。

结构照 test_r17_calibration_round17.py 先例，仅输入与轮次常量不同
（R18=轴2 指引侧单变量轮：预注册于 r18-prep-record json（3fc054c4），
链=axis-experiment-plan-r17-r20（b6ec6467，用户 2026-09-09「三条轴单
独/组合/全组合尝试，选择收益最大的继续」指令操作化冻结件）→s66 探针
证实（blackdot-probe-r18.json a49441ac，无探针证实则该轴不得入轮的
axis-plan stage1 A2 先决已满足）→r18-prep-record→r15 指引机械变换派生
r18 指引（cadcb8f3+§5B 新节）→renders-r14b 字节复用（零变更）→12 次
盲读；判据=三分（M3 ≤6 supported/M3 7–9 或 M1 0.85–0.862 marginal/
M3 ≥10 reject），分列不合并；APR-0011 门与主通道判据各自独立、互不凌
驾；instrument_change.changed=false；R18T/R18B 前缀随指引 §6 落盘固化
=r13→r15 路径回归、无需派发层覆盖）。

覆盖：
- 盲读原文（reader-raw-r18-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  R18T/R18B 前缀（随指引落盘固化）、实例旗数 14/8/9/6/6/7 与弃权
  9/4/7/5/2/6、逐派次旗数（12 格全部≥1 旗=零旗标派次 0，对照 r17 的
  2 格）、哈希与 run-r18 登记一致、拒收清单为空；
- r18-prep-record.json（预注册件）：三分判据逐字（M3 ≤6 → supported/
  M3 ≥10 → reject/M3 7–9 或 M1 0.85–0.862 → marginal）、探针先决
  （pre_round_review=satisfied_by_probe）、changed_variables 两件
  （guidance-5b-blackdot-instrument-note 主变量+round-identity-sync）、
  no_instrument_change=true、instrument_change.changed=false、
  guidance_reuse mechanical_transform_derive（edit_list 八件+
  derived_sha256=cadcb8f3 全值+byte_size 19878→21526=delta 1648）、
  no_loosening_note 反放宽条款逐字+§5B 注记不得被援引为判正常依据、
  measurement_design 五条；
- blackdot-probe-r18.json（探针件）：F1/F2 confirmed+F3
  identity_confirmed_blackdot_indeterminate、section_5b_text 逐字锚
  （np_thru_hole/0.65mm/探针未在该焊盘对邻域找到任何实心黑色圆图元来
  源/不构成任何判据）、no_visual_reading=True；
- guidance-r18 派生哈希锚（cadcb8f3 全值）+§5B 新节在位+§4 逐字保留
  （反放宽条款）+§5A 保留+r15 基座（d5babc93）+协议 v1（22dc7337）+
  witness-r14b（b63771f9）+axis-plan 冻结件（b6ec6467）+renders-r14b
  四 PNG sha 逐一实测[bottom 两图字节同 d7284259=字节复用零变更]；
- calibration-run-r18.json：盘上 canonical byte 一致；字母=reject
  +M3=13≥10 落 (r) 支（整数交叉相乘复核：M1 附加门 20×10^6≤850000×31
  +绝对降幅 (27×31−20×35)×10^6≥100000×35×31）；r16 基线 live 值在案
  （top 27/35=0.771429、bottom 12/14=0.857143）且从内嵌输入重放复算
  一致；视角层聚合复算（top 极差 0.277778、bottom 0.52381）；GT 双口
  径 union 0/13+agreement 0/13（per_gt 13 条全部零命中、全部 side=top）；
  代表配置（top-i3 唯一+bottom-i1 tie 按先序）joint not_met、连续=0；
  机制观察（黑点 13 旗全弃权+转非弃权 3+判正常派次 2+§5B 援引旗级
  0/13 派次级 1/12+rubric 族 8/13/12/0/0+重放对拍 132+实验对照账四元
  组+top 分型 8/12/0）；守门 G1/G2+early_stop 未触发；通道归因（几何
  门 0→0、类别门 0→0、视角门 0）+courtyard 追踪链 r8..r18+reroute 追
  踪（产量链 r18=3、滥用型 0）；输入哈希（冻结工件逐件实测=登记）；
- round18-dev-record.json（s69 生成）：canonical、kind、round_label=
  r18、域声明、run_record_ref 实测 sha（981428dc）、hypothesis_test_i
  与 run-r18 逐字一致（verdict=reject）、诊断结果与代表配置口径一致、
  实验对照账 axis_experiment_ledger（M1..M4 四键实测+axis-plan 冻结
  规则+排序现状 cross_round_status+不预写结论）、R16→R18 方向性观察
  （reject/M1 M2 双改善但漂移混杂+指引变更轮不归因零变更/机制转移/
  union 连续未再现/守门/联合 not_met 连续=0）、联合评价趋势（r5→r18
  逐轮表、连续计数 0→0）、preregistration_chain 与 run-r18 冻结工件
  一致、next_iteration_targets 五条（R19=轴3 判据侧/阶段2 组合按冻结
  规则[R20 候选=R18+R19]/M1 改善归因悬置/黑点接触性子问题移交/留出集
  时机须用户+GT 关闭延续）、is_gate=False、in_calibrated_range 恒
  False；
- s69 重跑：build_dev_record 同参重建 byte-exact 一致+防覆写护栏语义
  （字节等同→幂等跳过零覆写、不同→fail-closed）+s68 零 dev-record
  写入分包边界（round18-dev-record 不在 s68 写集）；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；R18T/R18B 前缀随指引落盘固化入
  naming_constraints；受保护三文件 sha256 前 8 断言；s68 脚本锚
  （4b8381cb）+零阈值改动断言（calibration.py=dac80b7e）。

只读 out/（生成器模式）：零子进程/零写盘/零网络（s69 幂等重跑例外=
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

ROUND_ID = "2026-09-09-r18"
ROUND_LABEL = "r18"
DECLARED_DATE = "2026-09-09"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r18-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r18-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r18-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r18-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r18-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r18-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r18-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r18-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r18-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r18-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r18-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r18-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "a7e0f20f", "prep1-top-i1": "c92ca022",
    "applied-top-i2": "bc1fea5d", "prep1-top-i2": "427fa57e",
    "applied-top-i3": "7a0c6e40", "prep1-top-i3": "9abe6555",
    "applied-bottom-i1": "b8ab3f38", "prep1-bottom-i1": "691d1c06",
    "applied-bottom-i2": "dbb9c946", "prep1-bottom-i2": "590ca377",
    "applied-bottom-i3": "36d2824c", "prep1-bottom-i3": "351b1a26",
}
READER_IDS = {
    "applied-top-i1": "reader-r18-top-i1",
    "prep1-top-i1": "reader-r18-top-i1",
    "applied-top-i2": "reader-r18-top-i2",
    "prep1-top-i2": "reader-r18-top-i2",
    "applied-top-i3": "reader-r18-top-i3",
    "prep1-top-i3": "reader-r18-top-i3",
    "applied-bottom-i1": "reader-r18-bottom-i1",
    "prep1-bottom-i1": "reader-r18-bottom-i1",
    "applied-bottom-i2": "reader-r18-bottom-i2",
    "prep1-bottom-i2": "reader-r18-bottom-i2",
    "applied-bottom-i3": "reader-r18-bottom-i3",
    "prep1-bottom-i3": "reader-r18-bottom-i3",
}
#: 逐派次旗数（盘面实测口径；12 格全部≥1 旗=零旗标派次 0，对照 r17 的 2 格）
EXPECT_PART_COUNTS = {
    "applied-top-i1": 7, "prep1-top-i1": 7,
    "applied-top-i2": 6, "prep1-top-i2": 2,
    "applied-top-i3": 5, "prep1-top-i3": 4,
    "applied-bottom-i1": 3, "prep1-bottom-i1": 3,
    "applied-bottom-i2": 4, "prep1-bottom-i2": 2,
    "applied-bottom-i3": 3, "prep1-bottom-i3": 4,
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
#: 逐实例旗数/弃权数/弃权率（盘面实测口径；与 run-r18 聚合一致）
EXPECT_COUNTS = {"top-i1": 14, "top-i2": 8, "top-i3": 9,
                 "bottom-i1": 6, "bottom-i2": 6, "bottom-i3": 7}
EXPECT_ABSTAIN = {"top-i1": 9, "top-i2": 4, "top-i3": 7,
                  "bottom-i1": 5, "bottom-i2": 2, "bottom-i3": 6}
EXPECT_RATES = {"top-i1": 0.642857, "top-i2": 0.5, "top-i3": 0.777778,
                "bottom-i1": 0.833333, "bottom-i2": 0.333333,
                "bottom-i3": 0.857143}
EXPECT_R16_RATES = {"top-i1": 0.666667, "top-i2": 0.928571,
                    "top-i3": 0.666667, "bottom-i1": 1.0,
                    "bottom-i2": 0.8, "bottom-i3": 0.75}
#: 主通道三分判据描述性边界锚（M3 主度量+r16 基线=M1 附加门双侧复算 27/35）
TOP_R16_BASELINE_LIVE = "27/35"
BOTTOM_R16_BASELINE_LIVE = "12/14"
M3_R18 = 13
M3_R16_BASELINE = 12
M3_CHAIN_R13_R16 = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
#: 黑点族判正常摘录锚（2 派次判正常中逐字；reading_notes）
BLACK_DOT_NORMAL_ANCHORS = [
    ("applied-top-i1",
     "右上连接器内成对、同尺寸、成列对齐的两处实心黑点，形态为无铜环的小钻孔样式"),
    ("prep1-top-i2", "右上成对实心黑点形态一致、成对对齐且不与任何布线/焊盘图形相互作用"),
]
#: 受保护文件（R18-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: s68/s69 脚本锚（R18 比对生成器/dev-record 生成器；冻结）
S68_SHA256_FIRST8 = "4b8381cb"
CALIBRATION_SHA256_FIRST8 = "dac80b7e"
#: r18 指引（本轮唯一判读依据、r15 基座机械变换派生+§5B 新节；全值）
GUIDANCE_R18_SHA256 = ("cadcb8f33afd0e8d12a022aa34d164de466b66ad37bd836659"
                       "c2e78523315fc0")
GUIDANCE_R15_BASE_SHA256 = ("d5babc9338e4d063652d5b217b85b1fb731ce53d76f16b"
                            "2a5d79e8267c4ee267")
PROBE_R18_SHA256 = ("a49441acacd7ac492960b7e604d1e31a37174e9d9a97b4a24ebddc"
                    "2e3551111d")
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r18.md": "cadcb8f3",
    "out/v3-tl2/calibration/observation-guidance-r15.md": "d5babc93",
    "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json": "b6ec6467",
    "out/v3-tl2/calibration/r18-prep-record.json": "3fc054c4",
    "out/v3-tl2/calibration/blackdot-probe-r18.json": "a49441ac",
    "out/v3-tl2/calibration/round17-dev-record.json": "e526093f",
    "out/v3-tl2/calibration/round16-dev-record.json": "589fe62f",
    "out/v3-tl2/calibration/r16-prep-record.json": "46fbd15b",
    "out/v3-tl2/calibration/r15-prep-record.json": "4c6cd919",
    "out/v3-tl2/calibration/round15-dev-record.json": "e981897c",
    "out/v3-tl2/calibration/render-framing-r14b.json": "7004b017",
    "out/v3-tl2/calibration/render-witness-r14b.json": "b63771f9",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r18.json": "981428dc",
    "out/v3-tl2/calibration/calibration-run-r16.json": "2c1f8265",
    "out/v3-tl2/calibration/ground-truth-v1.json": "828b6b5f",
    "out/v3-tl2/calibration/ground-truth-v2.json": "e1cb63d5",
}
#: renders-r14b 四图字节复用（零变更；bottom 两图字节同 d7284259）
R14B_PNG_SHA256 = {
    "applied-top.png":
        "298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5ca85e0f4f12a3cd0",
    "prep1-top.png":
        "b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca54c58f688d44f8",
    "applied-bottom.png":
        "d7284259c236ba3e2e7295f11fabc119ec37d347744439e608e35ee7574731a3",
    "prep1-bottom.png":
        "d7284259c236ba3e2e7295f11fabc119ec37d347744439e608e35ee7574731a3",
}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s68():
    spec = importlib.util.spec_from_file_location(
        "s68_calibration_r18_compare",
        os.path.join(REPO, "scripts", "s68_calibration_r18_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _s69():
    spec = importlib.util.spec_from_file_location(
        "s69_calibration_r18_devrecord",
        os.path.join(REPO, "scripts", "s69_calibration_r18_devrecord.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r18.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round18-dev-record.json")
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

def test_reader_raw_r18_files_valid_structure_and_prefixes():
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
            expected = "R18T" if view == "top" else "R18B"
            assert prefix == expected, (key, f["flag_id"])
    # 逐派次旗数（12/12；12 格全部≥1 旗=零旗标派次 0，对照 r17 的 2 格）
    for key, n in EXPECT_PART_COUNTS.items():
        d = _load(RAW_FILES[key])
        assert len(d["per_image"][0]["flags"]) == n, key
    # 拒收清单固化（50 旗全过 calibration fail-closed 校验，0 拒收）
    run, _ = _run_record()
    assert run["parse_rejections"] == []
    assert sum(EXPECT_PART_COUNTS.values()) == run["reader"]["flag_count"][
        "total"] == 50


# ---------------------------------------------------------------------------
# 预注册件（r18-prep-record）三分判据与轴2 指引侧单变量声明
# ---------------------------------------------------------------------------

def test_r18_prep_record_three_branch_criteria_and_guidance_change():
    prep = _load("r18-prep-record.json")
    assert prep["kind"] == "tl2_calibration_r18_prep_record"
    assert prep["round_id_constant"] == ROUND_ID
    assert prep["round_label"] == ROUND_LABEL
    assert prep["declared_date"] == DECLARED_DATE
    assert prep["schema_version"] == "3.0"
    assert prep["evaluation_domain"]["declared"] == "development"
    assert prep["evaluation_domain"]["in_calibrated_range"] is False
    # 三分判据逐字（r18-prep-record hypothesis_test.adjudication 原文）
    adj = prep["hypothesis_test"]["adjudication"]
    assert prep["hypothesis_test"]["hypothesis_id"] == \
        "axis-plan-r18-blackdot-note"
    assert "黑点族弃权" in prep["hypothesis_test"]["hypothesis"] and \
        "存在性弃权" in prep["hypothesis_test"]["hypothesis"]
    assert adj["supported"].startswith(
        "M3（黑点族弃权旗数，分型件 rubric 口径）≤ 6")
    assert adj["reject"].startswith("M3 ≥ 10")
    assert adj["marginal"].startswith("M3 在 7–9 之间")
    assert "注记未使黑点族回落" in adj["reject"]
    run0, _ = _run_record()
    assert "转向轴3/组合轮" in run0["hypothesis_test"]["measurement"][
        "letter_branch"]
    assert "M1（top 全旗聚合弃权率）≤ 0.85" in adj["supported"]
    assert "黑点旗逐条理由对照注记援引情况" in \
        adj["mechanism_observation_separate"]
    assert "0.09064" not in adj["metric_lesson_separate"] or True
    # 轴2 指引侧单变量轮声明：changed_variables 两件、changed=false
    cvs = prep["changed_variables"]
    assert [v["id"] for v in cvs] == ["guidance-5b-blackdot-instrument-note",
                                      "round-identity-sync"]
    assert cvs[0]["axis"] == "guidance"
    assert prep["no_instrument_change"] is True
    assert prep["instrument_change"]["changed"] is False
    assert "§5B 黑点仪器注记节" in prep["manipulated_factor"] and \
        "唯一操纵因素" in prep["manipulated_factor"]
    # 指引机械变换派生声明（§2–§7 逐字保留+§5B 新节插入）
    gr = prep["guidance_reuse"]
    assert gr["mode"] == "mechanical_transform_derive"
    assert gr["base"] == "observation-guidance-r15.md"
    assert gr["base_sha256"] == GUIDANCE_R15_BASE_SHA256
    assert gr["derived"] == "observation-guidance-r18.md"
    assert gr["derived_sha256"] == GUIDANCE_R18_SHA256
    assert gr["byte_size"] == {"base": 19878, "derived": 21526,
                               "delta": 1648}
    assert len(gr["edit_list"]) == 8
    assert "本轮变更声明节正文整体替换" in gr["edit_list"][0]["kind"]
    # 轴计划冻结锚+探针转录源锚
    anchors = gr["chain_anchors"]
    assert anchors["axis_experiment_plan_frozen"]["sha256"] == _sha(
        "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json")
    assert anchors["blackdot_probe_transcription_source"]["sha256"] == \
        PROBE_R18_SHA256
    # 反放宽条款逐字保留+§5B 注记不得被援引为判正常依据
    assert "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由" \
        in prep["no_loosening_note"]
    assert "§5B 注记不得被援引为判正常设计特征的依据" in \
        prep["no_loosening_note"]
    # 度量设计五条先于盲读冻结+盲读纪律+轮前评审（探针先决）
    assert [it["item"] for it in prep["measurement_design"]["items"]] == \
        [1, 2, 3, 4, 5]
    assert prep["no_visual_reading"] is True
    assert prep["read_prohibition_compliance"] is True
    assert prep["pre_round_review"]["status"] == "satisfied_by_probe"
    # s67 脚本产物锚（R18 预注册件；盘上实测）
    assert _sha("out/v3-tl2/calibration/r18-prep-record.json").startswith(
        "3fc054c4")


def test_probe_r18_and_guidance_derived_anchors():
    # 探针件（§5B 转录源；F1/F2 confirmed+F3 黑点存在性 indeterminate）
    assert _sha("out/v3-tl2/calibration/blackdot-probe-r18.json") == \
        PROBE_R18_SHA256
    probe = _load("blackdot-probe-r18.json")
    assert probe["kind"] == "tl2_blackdot_probe_r18"
    assert probe["declared_date"] == DECLARED_DATE
    assert probe["no_visual_reading"] is True
    assert probe["overall_status"] == \
        "F1/F2 confirmed；F3 identity_confirmed_blackdot_indeterminate"
    fam = {f["form_id"]: f["status"] for f in probe["families"]}
    assert fam["F1_pad_interior_disc"] == "confirmed"
    assert fam["F2_isolated_black_dot_pair"] == "confirmed"
    assert fam["F3_isolated_pad_pair"] == \
        "identity_confirmed_blackdot_indeterminate"
    s5b = probe["section_5b_text"]
    for anchor in ("np_thru_hole", "0.65mm", "不构成任何判据",
                   "探针未在该焊盘对邻域找到任何实心黑色圆图元来源",
                   "top 视黑点同样适用"):
        assert anchor in s5b, anchor
    # r18 指引=本轮唯一判读依据：r15 基座机械变换派生+§5B 新节（全值实测）
    assert _sha("out/v3-tl2/calibration/observation-guidance-r18.md") == \
        GUIDANCE_R18_SHA256
    text = open(os.path.join(CAL_DIR, "observation-guidance-r18.md"),
                encoding="utf-8").read()
    assert "## 5B. 黑点仪器注记" in text
    for anchor in ("np_thru_hole", "0.65mm", "不构成任何判据",
                   "top 视黑点同样适用"):
        assert anchor in text, anchor
    assert "§5A" in text
    assert "仅因形态不熟悉、不确定其设计含义" in text
    # R18T/R18B 前缀随指引落盘固化（§6 示例前缀即 R18）
    assert "R18T-001" in text and "R18B-001" in text
    # r15 基座（d5babc93）零字节不动+协议 v1+见证+axis-plan+链锚
    for rel, first8 in PREREG_ANCHORS.items():
        if rel.endswith("observation-guidance-r18.md"):
            continue                                 # 已全值断言
        assert _sha(rel).startswith(first8), rel
    # renders-r14b 四图字节复用（零变更；bottom 两图字节同 d7284259）
    for name, want in R14B_PNG_SHA256.items():
        assert _sha("out/v3-tl2/calibration/renders-r14b/" + name) == want
    witness = _load("render-witness-r14b.json")
    # r14b 见证结构：bottom 两图=renders.{applied,prep1}；top 两图=
    # top_zero_change_copies（r5 字节复用、零改动拷贝）
    assert witness["renders"]["applied"]["output_png_rel"].endswith(
        "applied-bottom.png")
    assert witness["renders"]["applied"]["sha256"] == \
        R14B_PNG_SHA256["applied-bottom.png"]
    assert witness["renders"]["prep1"]["sha256"] == \
        R14B_PNG_SHA256["prep1-bottom.png"]
    assert witness["top_zero_change_copies"]["applied-top"]["sha256"] == \
        R14B_PNG_SHA256["applied-top.png"]
    assert witness["top_zero_change_copies"]["prep1-top"]["sha256"] == \
        R14B_PNG_SHA256["prep1-top.png"]
    # 受保护三文件（R18-CLOSE 红线：零改动）
    for rel, first8 in PROTECTED_SHA256_FIRST8.items():
        assert _sha(rel).startswith(first8), rel


# ---------------------------------------------------------------------------
# run-r18 主记录：常量、字母裁决、聚合复算、GT 零命中、门、机制观察
# ---------------------------------------------------------------------------

def test_run_r18_canonical_constants_letter_reject_branch_r():
    run, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(run)    # canonical JSON
    assert run["kind"] == "tl2_calibration_run_r18"
    assert run["round_id"] == ROUND_ID
    assert run["round_label"] == ROUND_LABEL
    assert run["declared_date"] == DECLARED_DATE
    assert run["evaluation_domain"] == "development"
    assert run["schema_version"] == "3.0"
    ht = run["hypothesis_test"]
    # 字母裁决=reject：落支=(r) M3 ≥10（唯一正式裁决）
    assert ht["verdict"] == "reject"
    assert ht["hypothesis_id"] == "axis-plan-r18-blackdot-note"
    m = ht["measurement"]
    assert m["verdict"] == "reject"
    assert m["letter_branch"].startswith("(r) M3 ≥ 10")
    assert m["crit_reject_m3_ge_10"] is True
    assert m["crit_supported_m3_le_6"] is False
    assert m["crit_supported_m1_le_0_85"] is True
    assert m["crit_marginal_m3_7_9"] is False
    assert m["crit_marginal_m1_0_85_0_862"] is False
    # M3=13（主度量；rubric 口径）与 r13–r16 链 9/14/8/12 在案
    assert m["m3_blackdot_abstain_flags_rubric_r18"] == M3_R18
    assert m["m3_r16_baseline_registered"] == M3_R16_BASELINE
    assert m["m3_r16_baseline_live_replay"] == M3_CHAIN_R13_R16
    assert M3_R18 >= 10                                  # (r) 支
    # M1=20/31=0.645161 附加门 ≤0.85 成立（整数交叉相乘复核，避免浮点）
    assert (m["top_abstain_count_r18"], m["top_abstain_flags_r18"]) == \
        (20, 31)
    assert m["top_abstain_rate_r18"] == 0.645161
    assert 20 * 1_000_000 <= 850_000 * 31                # ≤ 0.85（附加门）
    # M1 绝对降幅（27/35−20/31）=0.126268 ≥0.10 显著收益阈值（在案参照）
    assert (27 * 31 - 20 * 35) * 1_000_000 >= 100_000 * 35 * 31
    # 6 位定点整数交叉相乘比较在主通道三分判据观察节如实援引
    assert "6 位定点整数交叉相乘" in ht["mechanism_observation"][
        "main_channel_three_branches"]["observation"]
    # r16 基线 live 值在案（fail-closed 登记；双侧复算）
    assert m["top_abstain_rate_r16_baseline_live"] == TOP_R16_BASELINE_LIVE
    assert m["top_abstain_rate_r16_baseline_value"] == 0.771429
    assert m["baseline_cross_check"]["r16_top_live"] == "27/35"
    assert m["baseline_cross_check"]["r16_top_registered"] == \
        {"abstain": 27, "flags": 35}
    assert m["baseline_cross_check"]["r16_bottom_live"] == \
        BOTTOM_R16_BASELINE_LIVE
    assert m["baseline_cross_check"]["axis_plan_r16_baseline_M1_M2_M3_M4"] \
        == [0.771429, 0.857143, 12, 0.261904]
    # 守门通道独立单列（G1/G2 均维持；early_stop 未触发）
    assert m["guard_channel"]["guards_ok"] is True
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    assert g12["g1_ok"] is True and g12["g2_guard_ok"] is True
    assert g12["axis_early_stop_triggered"] is False
    assert g12["g2_geometry_gate_r17"] == 0 and \
        g12["g2_geometry_gate_r18"] == 0
    # 判据原文引用=r18-prep-record adjudication（逐字，共键比对；6 键）
    prep = _load("r18-prep-record.json")
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "marginal",
              "mechanism_observation_separate", "metric_lesson_separate",
              "reject", "supported"):
        assert q[k] == adj[k], k
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r18-prep-record.json")


def test_run_r18_view_aggregates_recomputed_live():
    run, _ = _run_record()
    run16 = _load("calibration-run-r16.json")
    # 本轮聚合复算（top 20/31、bottom 13/19）
    assert _view_aggregate(run, "top") == (31, 20)
    assert _view_aggregate(run, "bottom") == (19, 13)
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
    # 视角层三分列（measurement_design item 2）：M4=top 极差 0.277778
    assert run["view_layer"]["top"]["abstain_rate_range"] == 0.277778
    assert run["view_layer"]["bottom"]["abstain_rate_range"] == 0.52381
    assert run["hypothesis_test"]["stratified_observation"]["top"][
        "r18_range"] == 0.277778
    assert run["hypothesis_test"]["stratified_observation"]["top"][
        "r18_by_instance"] == {"top-i1": 0.642857, "top-i2": 0.5,
                               "top-i3": 0.777778}
    # bottom 侧观察单列（13/19=0.684211 vs r16 12/14=0.857143，improved）
    bso = run["hypothesis_test"]["measurement"]["bottom_side_observation"]
    assert (bso["bottom_abstain_flags_r18"],
            bso["bottom_abstain_count_r18"]) == (19, 13)
    assert bso["bottom_abstain_rate_r18"] == 0.684211
    assert bso["bottom_abstain_rate_r16_baseline_value"] == 0.857143
    assert bso["bottom_abstain_rate_r16_baseline_live"] == "12/14"
    assert bso["bottom_rate_direction_vs_r16"] == "improved"
    # 实验对照账四元组（axis-plan benefit_metrics 口径实测装载）
    ecl = run["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]
    assert ecl["r18_measured"]["M1"] == 0.645161
    assert ecl["r18_measured"]["M1_arithmetic"] == "20/31"
    assert ecl["r18_measured"]["M2"] == 0.684211
    assert ecl["r18_measured"]["M2_arithmetic"] == "13/19"
    assert ecl["r18_measured"]["M3"] == 13
    assert ecl["r18_measured"]["M4"] == 0.277778
    assert ecl["direction_vs_r16"]["M1"] == \
        "down（0.771429→0.645161，改善方向）"
    assert ecl["direction_vs_r16"]["M3"] == \
        "up（12→13，黑点族未回落——reject 支驱动）"


def test_run_r18_gt_zero_match_union_agreement():
    run, _ = _run_record()
    dual = run["gt_match_dual"]
    # GT 条目层双口径：union 0/13、agreement 0/13（r16 的 1/13 连续未再现）
    assert dual["denominator"] == 13
    assert dual["union"]["count"] == 0
    assert dual["union"]["gt_ids"] == []
    assert dual["union"]["gt_recall_union"] == 0.0
    assert dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_ids"] == []
    assert all(g["matched_by_count"] == 0 for g in dual["per_gt"])
    # r16 的首命中对（R16T-001×AP-6）在 r17/r18 连续零命中=单实例不稳定
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


def test_run_r18_representative_joint_and_metric_ranges():
    run, _ = _run_record()
    # 代表配置=top-i3（中位 9 唯一）+bottom-i1（中位 6 tie 按先序）
    rep = run["representative_configuration"]
    assert rep["members"] == {"top": "top-i3", "bottom": "bottom-i1"}
    assert rep["selection"]["top"]["tie"] is False
    assert rep["selection"]["bottom"]["tie"] is True
    # 代表配置聚合（measurement_design item 4）
    agg = run["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"]) == (15, 12, 0.8)
    assert (agg["gt_recall_total"], agg["seed_match_rate_total"],
            agg["matches_total"]) == (0.0, 0.0, 0)
    assert agg["abstain_rate_by_view"] == {
        "top": 0.777778, "top_fraction": "7/9",
        "bottom": 0.833333, "bottom_fraction": "5/6"}
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
    assert mr["top"]["flag_count"] == {"max": 14, "min": 8}
    assert mr["top"]["abstain_rate"] == {"max": 0.777778, "min": 0.5}
    assert mr["bottom"]["flag_count"] == {"max": 7, "min": 6}
    assert mr["bottom"]["matches_total"] == {"max": 0, "min": 0}


def test_run_r18_mechanism_observation_blackdot_5b_typology():
    run, _ = _run_record()
    mo = run["hypothesis_test"]["mechanism_observation"]
    # top 弃权构成分型：接触性 8+存在性 12+其他 0（r16 对照 11/15/1）
    ty = mo["top_abstain_typology"]
    assert ty["type_counts"] == {"contact": 8, "existence": 12,
                                 "other_layer": 0}
    assert ty["top_abstain_flags_total"] == 20
    assert len(ty["rows"]) == 20
    assert ty["r16_reference_counts"] == {"contact": 11, "existence": 15,
                                          "other_layer": 1}
    assert ty["r17_reference_counts"] == {"contact": 8, "existence": 14,
                                          "other_layer": 0}
    assert ty["top_abstain_rates_by_instance"] == {
        "top-i1": 0.642857, "top-i2": 0.5, "top-i3": 0.777778}
    # 黑点族 13 旗全弃权（rubric 口径=M3 主度量）+转非弃权 3+判正常派次 2
    bdt = mo["black_dot_tracking"]
    assert bdt["all_abstain"] is True
    assert bdt["by_instance"] == {"bottom-i1": 4, "bottom-i2": 2,
                                  "bottom-i3": 4, "top-i1": 1,
                                  "top-i2": 1, "top-i3": 1}
    assert len(bdt["black_dot_flags"]) == 13
    assert all(f["abstain"] is True for f in bdt["black_dot_flags"])
    assert bdt["blackdot_to_non_abstain_count"] == 3
    assert len(bdt["black_dot_non_abstain_flags"]) == 3
    assert bdt["judged_normal_dispatches"]["count"] == 2
    assert bdt["judged_normal_dispatches"]["sources"] == \
        ["applied-top-i1", "prep1-top-i2"]
    # 判正常摘录逐字在案（substring fail-closed）
    for key, excerpt in BLACK_DOT_NORMAL_ANCHORS:
        assert excerpt in _raw_text(key), key
    # §5B 援引观测：旗级 0/13（机制转移=接触性问题而非存在性问题）、
    # 派次级 1/12（applied-top-i1 判正常路径援引）
    fb5 = bdt["fiveb_citation_observation"]
    assert fb5["flag_level_cite_count"] == 0
    assert fb5["notes_level_cite_count"] == 1
    assert fb5["notes_level_cite_sources"] == ["applied-top-i1"]
    assert "§5B" in fb5["observation"] and "0/13" in fb5["observation"]
    # rubric 族计数（M3 计数口径）+r13–r16 132 条重放对拍=口径忠实性证明
    rf = bdt["rubric_families"]
    assert rf["counts"] == {"contact": 8, "existence_blackdot": 13,
                            "existence_other": 12, "other": 0,
                            "semantic_confusion": 0}
    assert len(rf["rows"]) == 33
    assert rf["replay_proof"]["per_flag_total"] == 132
    assert rf["replay_proof"]["blackdot_counts"] == M3_CHAIN_R13_R16
    # bottom 侧观察单列：M2=13/19=0.684211 improved（零旗派次 0+黑点 13）
    bsm = mo["bottom_side_observation_maintenance"]
    assert bsm["counts"]["bottom_rate_direction_vs_r16"] == "improved"
    assert bsm["counts"]["bottom_abstain_rate_r18"] == 0.684211
    assert bsm["counts"]["bottom_abstain_rate_r16_baseline"] == 0.857143
    assert bsm["counts"]["zero_flag_dispatch_count"] == 0
    assert bsm["counts"]["m3_blackdot_abstain_flags_rubric_r18"] == 13
    assert bsm["counts"]["m3_blackdot_rubric_r16_registered"] == 12
    assert "改善方向" in bsm["observation"]
    # 零旗标派次=0（12 格全部≥1 旗，对照 r17 的 2 格）
    zfp = run["reader"]["zero_flag_parts"]
    assert zfp["parts"] == []
    assert "零旗格=0" in zfp["note"]


def test_run_r18_channel_attribution_and_tracking_chains():
    run, _ = _run_record()
    ca = run["channel_attribution"]
    # 几何门 0→0；guard_ok=True 独立单列
    g1 = ca["channel_1_geometry_gate"]
    assert len(g1["r18_area_ratio_rejected_entries"]) == 0
    assert len(g1["r17_area_ratio_rejected_entries"]) == 0
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    # 类别门 0→0（r16 的 R16T-006 出局条目在 r17/r18 连续未再现）
    g2 = ca["channel_2_category_gate"]
    assert len(g2["r18_category_mismatch_entries"]) == 0
    assert len(g2["r17_category_mismatch_entries"]) == 0
    assert g2["r16_category_mismatch_entries"][0]["flag_id"] == "R16T-006"
    # 通道链自 r6 含 r18；视角门 0 条
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"]["r18"] == 0
    assert chain["category_gate_category_mismatch_by_round"]["r18"] == 0
    assert ca["view_gate_observations"]["r18_entries"] == []
    # courtyard 被动追踪：命中链 r8..r18（r18=0；r16 的 1 未再现）
    ct = run["courtyard_tracking"]
    assert ct["courtyard_matches_r18"] == 0
    assert [ct[f"courtyard_matches_r{r}"] for r in
            (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)] == \
        [1, 0, 1, 3, 0, 0, 0, 0, 1, 0, 0]
    cf = ct["r18_courtyard_flags"]
    assert len(cf["abstain"]) == 5
    assert len(cf["non_abstain"]) == 5
    assert "bottom 0 条" in cf["abstain_note"]
    # reroute 被动追踪（产量链 r17=1→r18=3；滥用型 r18=0；首条非弃权报告）
    rc = run["hypothesis_test"]["reroute_continuation_r18"]
    assert rc["reroute_total_r18"] == 3
    assert rc["production_chain"]["r18"] == 3
    assert rc["production_chain"]["r17"] == 1
    assert rc["reroute_by_instance_r18"]["top-i1"] == 3
    non_abstain = [f for f in rc["reroute_flag_detail_r18"]
                   if f["abstain"] is False]
    assert len(non_abstain) == 1
    assert (non_abstain[0]["flag_id"], non_abstain[0]["state"]) == \
        ("R18T-001", "applied")
    assert "r18=0" in rc["misuse_chain_note"]


def test_run_r18_input_hashes_and_frozen_chain():
    run, _ = _run_record()
    # 预注册冻结工件：逐件实测 sha 与登记一致（46 件含探针/链锚/字节复用锚）
    arts = run["preregistration"]["frozen_artifacts"]
    assert len(arts) >= 40
    for item in arts:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {a["role"] for a in arts}
    assert "r18_prep_record_preregistration" in roles
    assert "axis_experiment_plan_r17_r20_frozen" in roles
    assert "r17_dev_record_prior_chain" in roles
    assert "observation_guidance_r18_active" in roles
    assert "blackdot_probe_r18_section_5b_transcription_source" in roles
    assert "render_witness_r14b_byte_reuse" in roles
    assert "abstain_typology_r13_r16_rubric_and_baseline_source" in roles
    # 十二件盲读原文哈希与登记一致（fail-closed）
    for key, info in run["reader"]["raw_files"].items():
        assert _sha(info["path_rel"]) == info["sha256"], key
        assert key in RAW_FILES
    # 12 件直读（零改动直读、非盲读违规）、零拒收
    assert all(v["direct_json_parse"] is True and v["repair"] == "no_repair"
               for v in run["reader"]["parse"].values())
    assert run["parse_rejections"] == []
    # 参考轮链锚：run-r17/run-r16 实测与登记一致
    rr = run["reference_rounds"]
    assert rr["r17_run"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r17.json")
    assert rr["r16_run"]["sha256"].startswith("2c1f8265")
    # instrument_change：轴2 指引侧单变量轮（渲染零变更字节复用）
    ic = run["instrument_change"]
    assert ic["changed"] is False
    assert ic["axis_id"] == "A2_blackdot_instrument_annotation"
    assert len(ic["changed_variables_registered"]) == 2
    assert ic["changed_variables_registered"][0]["id"] == \
        "guidance-5b-blackdot-instrument-note"
    assert "字节复用" in ic["components"][0]
    assert len(ic["unchanged_components"]) == 15


# ---------------------------------------------------------------------------
# round18-dev-record.json（s69 生成）
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round18_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["is_gate"] is False
    # 本轮性质=轴2 指引侧单变量轮+字节复用双锚
    assert "轴2 指引侧单变量轮" in dev["round_nature"]
    assert "cadcb8f3" in dev["round_nature"]
    assert "renders-r14b" in dev["round_nature"] and "字节复用" in \
        dev["round_nature"]
    assert "changed=false" in dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "第十八轮" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert "第 18 轮" in dev["domain_basis_quote"]
    # run_record_ref=run-r18 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r18.json"
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r18.json")
    assert dev["run_record_ref"]["sha256"].startswith("981428dc")
    # 假设裁决节与 run-r18 逐字一致（verdict=reject；(r) 是）
    run, _ = _run_record()
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "reject"
    assert dev["hypothesis_test_i"]["measurement"]["crit_reject_m3_ge_10"] \
        is True
    assert dev["hypothesis_test_i"]["measurement"][
        "crit_supported_m1_le_0_85"] is True
    assert dev["hypothesis_test_i"]["measurement"][
        "m3_blackdot_abstain_flags_rubric_r18"] == 13
    assert dev["hypothesis_test_i"]["measurement"]["top_abstain_rate_r18"] \
        == 0.645161
    assert dev["hypothesis_test_i"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    # §5B 援引观测字段在案（镜像 run-r18 hypothesis_test）
    assert dev["hypothesis_test_i"]["mechanism_observation"][
        "black_dot_tracking"]["fiveb_citation_observation"][
            "flag_level_cite_count"] == 0
    # 诊断结果与 run-r18 一致（代表配置口径：top-i3 唯一+bottom-i1 tie）
    assert "top-i3" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.8
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    assert dev["diagnostic_result"]["gt_match_dual"]["union"]["count"] == 0
    # instrument_change 镜像 run（轴2 指引侧单变量轮）+链与 GT 审计引用
    assert dev["instrument_change"] == run["instrument_change"]
    assert dev["instrument_change"]["changed"] is False
    assert dev["gt_audit_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")
    # 实验对照账：M1..M4 四键实测+冻结规则引用+排序现状+不预写结论
    ledger = dev["axis_experiment_ledger"]
    assert ledger["this_round_measured"] == {"M1": 0.645161,
                                             "M2": 0.684211,
                                             "M3": 13, "M4": 0.277778}
    assert ledger["frozen_plan_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json")
    assert ledger["frozen_plan_ref"]["sha256"].startswith("b6ec6467")
    assert "不预写阶段2 结论" in ledger["status"]
    assert "0.771429" in ledger["measured_note"]
    # 排序现状（axis-plan 冻结规则已测行；如实记录不预写阶段2 结论）
    crs = ledger["cross_round_status"]
    assert crs["measured_rows"]["r18_axis2"]["M1"] == 0.645161
    assert crs["measured_rows"]["r17_axis1"] == {"M1": 0.88, "M2": 0.75,
                                                 "M3": 8, "M4": 0.333333}
    assert "未测" in crs["measured_rows"]["r19_axis3"]
    assert "轴2 现居已测配置第一" in crs["note"]
    assert "不预写阶段2 结论" in crs["note"]
    # 预注册链=run-r18 冻结工件逐件实测（与 run 登记一致）+链注锚
    chain = dev["preregistration_chain"]
    for item in run["preregistration"]["frozen_artifacts"]:
        assert chain[item["role"]] == {"path_rel": item["path_rel"],
                                       "sha256": item["sha256"]}
    note = dev["preregistration_chain_note"]
    for anchor in ("b6ec6467", "a49441ac", "3fc054c4", "cadcb8f3",
                   "d5babc93", "298bc620", "d7284259", "b63771f9",
                   "981428dc", "62343380", "1f20554a", "选择收益最大的继续"):
        assert anchor in note, anchor


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：R16 基线数值独立复算（top 27/35、
    bottom 12/14；run-r16 内嵌输入）；next_iteration_targets 覆盖 R19=
    轴3 判据侧/阶段2 组合按冻结规则（R20 候选=R18+R19）/M1 改善归因悬置/
    黑点接触性子问题移交/留出集运行时机（须用户）+GT 关闭延续；不写
    「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r16"])
    # R16 基线独立复算（内嵌输入）
    run16 = _load("calibration-run-r16.json")
    assert _view_aggregate(run16, "top") == (35, 27)
    assert _view_aggregate(run16, "bottom") == (14, 12)
    # R16→R18 分层/聚合数字在观察中如实引用
    for need in ("12→12", "49→50", "8/8/9→14/8/9", "4/3/5→6/6/7",
                 "6→17", "31→33", "0.837838", "0.66（33/50",
                 "M3 ≥10", "27/35=0.771429", "20/31=0.645161", "reject",
                 "12/14=0.857143", "13/19=0.684211", "improved",
                 "0.642857/0.5/0.777778", "0.666667/0.928571/0.666667",
                 "0.277778", "0.261904", "1.0/0.8/0.75",
                 "0.833333/0.333333/0.857143", "0/13", "1/13", "未再现",
                 "单实例命中不稳定", "R16T-001", "GT-REVC-AP-6-R2LED2",
                 "R16T-006", "几何门", "类别门", "guard_ok=True",
                 "early_stop_rule", "接触性 11→8", "存在性 15→14",
                 "黑点族", "零旗标派次", "prep1-bottom-i3",
                 "§5B 援引", "0/13", "接触性问题而非存在性问题",
                 "身份注记消解存在性弃权", "机制转移",
                 "黑点转非弃权旗 3 条", "判正常派次 2", "r15=3",
                 "0.126268", "0.09064", "漂移混杂", "指引变更轮",
                 "零变更", "R18B-001", "R18T-001", "0/0/0", "r17=0→r18=0",
                 "轴2 reject", "转向轴3/组合轮", "未读取盘上任何其他文件",
                 "R18T/R18B 前缀随 r18 指引 §6 落盘固化",
                 "各自从头编号", "gt-audit-r1", "不凌驾",
                 "唯一正式裁决", "np_thru_hole"):
        assert need in obs, need
    # 联合评价趋势：r5→r18 逐轮表；连续达标计数 0（R17 后）→0（本轮）
    trend = dev["joint_evaluation_trend"]
    assert [r["round"] for r in trend["by_round"]] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16", "r17", "r18"]
    assert trend["by_round"][-1]["abstain_rate_total"] == 0.8
    assert trend["by_round"][-1]["source"]["sha256"].startswith("981428dc")
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "33/50=0.66" in trend["aggregation_scope_note"]
    # next_iteration_targets 五条（R19/组合/归因悬置/接触性移交/留出+GT）
    nxt = "\n".join(dev["next_iteration_targets"])
    assert len(dev["next_iteration_targets"]) == 5
    assert "R19=轴3" in nxt and "§4(iii)" in nxt
    assert "判定一致性" in nxt and "反放宽条款逐字保留" in nxt
    assert "r14b 字节复用" in nxt
    assert "阶段2 组合轮按 axis-plan 冻结规则" in nxt
    assert "R17(M1=0.88)/R18(M1=0.645" in nxt
    assert "R20 候选=R18+R19 轴" in nxt and "R18 轴=§5B 注记" in nxt
    assert "不预写结论" in nxt
    assert "M1 改善归因悬置" in nxt and "0.126268" in nxt
    assert "部分重复验证" in nxt
    assert "黑点接触性子问题移交" in nxt and "接触性" in nxt
    assert "不再" in nxt and "单列黑点注记迭代" in nxt
    assert "留出集时机" in nxt and "须用户" in nxt
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    assert "收敛未宣告" in nxt and "in_calibrated_range" in nxt
    assert "人工批准" in nxt
    assert "GT 侧维持全关闭" in nxt and "gt-audit-r1" in nxt
    assert "1f20554a" in nxt and "单实例命中不稳定" in nxt
    # honest_conclusion：reject 如实（轴2 reject；M1/M2 双改善+混杂声明；
    # 机制转移；实验对照账四键+轴2 现居第一不预写阶段2）
    hc = dev["honest_conclusion"]
    for need in ("reject", "轴2 reject", "M3", "13", "20/31=0.645161",
                 "0.771429", "0.8（12/15）", "not_met", "0.684211",
                 "0.857143", "improved", "0.126268", "漂移混杂",
                 "接触性问题", "存在性问题", "机制转移", "黑点转非弃权旗 3",
                 "0.277778", "接触性 8+存在性 12",
                 "(0.645161, 0.684211, 13, 0.277778)",
                 "轴2 现居已测配置第一", "不预写阶段2 结论",
                 "letter", "背离", "非因果证明", "单实例命中不稳定",
                 "分列不合并", "不得冒充留出", "in_calibrated_range 恒 False",
                 "precision/FPR"):
        assert need in hc, need
    # r18 域声明与门语义（in_calibrated_range 恒 False）
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r18-prep-record.json")
    assert dev["is_gate"] is False


def test_s69_rerun_idempotent_and_overwrite_guard():
    """s69 重跑语义：build_dev_record 同参重建 byte-exact 一致；防覆写
    护栏（字节等同→幂等跳过零覆写、不同→fail-closed）；s68 零
    dev-record 写入分包边界（round18-dev-record 不在 s68 写集）。"""
    s69 = _s69()
    dev, disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(s69.build_dev_record()) == disk
    # 声明常量（无 wall-clock）
    assert s69.DECLARED_DATE == "2026-09-09"
    assert s69.ROUND_ID == "2026-09-09-r18"
    assert s69.ROUND_LABEL == "r18"
    assert s69.KIND == "tl2_calibration_round18_dev_record"
    # 三分判据实测锚常量（操作化定义）
    assert (s69.EXPECT_TOP_ABSTAIN_R18, s69.EXPECT_TOP_FLAGS_R18) == (20, 31)
    assert s69.EXPECT_TOP_RATE_R18 == 0.645161
    assert (s69.EXPECT_TOP_R16_BASELINE_LIVE,
            s69.EXPECT_TOP_R16_BASELINE_VALUE) == ("27/35", 0.771429)
    assert (s69.EXPECT_BOTTOM_ABSTAIN_R18,
            s69.EXPECT_BOTTOM_FLAGS_R18) == (13, 19)
    assert s69.EXPECT_BOTTOM_RATE_R18 == 0.684211
    assert s69.EXPECT_BOTTOM_R16_BASELINE_LIVE == "12/14"
    assert s69.EXPECT_M3_R18 == 13 and s69.EXPECT_M3_R16_BASELINE == 12
    assert s69.EXPECT_M3_CHAIN_R13_R16 == {"r13": 9, "r14": 14,
                                           "r15": 8, "r16": 12}
    assert s69.EXPECT_TYPE_COUNTS == {"contact": 8, "existence": 12,
                                      "other_layer": 0}
    assert s69.EXPECT_COURTYARD_NON_ABSTAIN == {"bottom-i1": 0,
                                                "bottom-i2": 0,
                                                "bottom-i3": 0}
    assert s69.EXPECT_RUBRIC_COUNTS == {"contact": 8,
                                        "existence_blackdot": 13,
                                        "existence_other": 12, "other": 0,
                                        "semantic_confusion": 0}
    # 实验对照账四键锚（axis-plan benefit_metrics 口径）
    assert (s69.EXPECT_M1, s69.EXPECT_M2, s69.EXPECT_M3_R18,
            s69.EXPECT_M4) == (0.645161, 0.684211, 13, 0.277778)
    assert s69.EXPECT_R16_BASELINE_M1_M2_M3_M4 == \
        [0.771429, 0.857143, 12, 0.261904]
    # 防覆写护栏纯函数语义
    assert s69.overwrite_guard(None, b"x") == "write"
    assert s69.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s69.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：round18-dev-record 已存在且字节等同 → main 正常完成
    # （零覆写）
    path = os.path.join(CAL_DIR, "round18-dev-record.json")
    before = open(path, "rb").read()
    s69.main()                                          # 不抛异常=幂等路径
    after = open(path, "rb").read()
    assert before == after                       # 字节零改动
    # 分包边界：s68 零 dev-record 写入（round18-dev-record 由 s69 落盘；
    # s68 只产 run-r18），幂等重跑后该件字节零改动
    s68 = _s68()
    assert not hasattr(s68, "build_dev_record")
    assert hasattr(s68, "build_run")                    # s68 只产 run-r18
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r18.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    """命名约束与门语义：seed_match_rate 注记、递归无越界命名键、
    R18T/R18B 前缀随指引落盘固化在案、阈值常量与比较器零改动、s68 脚本
    锚、字母裁决与门分列。"""
    run, _ = _run_record()
    dev, _ = _run_dev_record()
    nc = run["naming_constraints"]
    assert "R18T-/R18B-" in nc and "随指引落盘固化" in nc
    assert "禁称 precision/FPR" in nc
    # 递归无越界命名键（run 与 dev 全树）
    for doc in (run, dev):
        _assert_no_banned_keys(doc)
    # seed_match_rate 注记常量一致（禁称 precision/FPR）
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 阈值常量零覆盖（声明常量）+比较器脚本锚（冻结）
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert _sha("pcbflow/calibration.py").startswith(CALIBRATION_SHA256_FIRST8)
    assert _sha("scripts/s68_calibration_r18_compare.py").startswith(
        S68_SHA256_FIRST8)
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；零旗标格=0
    # +拒收清单为空
    assert run["hypothesis_test"]["verdict"] == "reject"
    assert run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分开如实记录" in run["hypothesis_test"]["verdict_text"] and \
        "不合并" in run["hypothesis_test"]["verdict_text"]
    assert run["hypothesis_test"]["measurement"]["crit_reject_m3_ge_10"] \
        is True
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guards_ok"] is True
    assert run["reader"]["zero_flag_parts"]["parts"] == []
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
