"""R16 执行包测试：reader 判读迭代第十六轮收口（CAL-R16-CLOSE 包 B）——
同指引重复轮（零变更轮：observation-guidance-r15.md d5babc93 字节复用零
写入+渲染零变更 renders-r14b 四图字节复用+GT/阈值/协议零变更；唯一操纵
因子=reader 实例群重抽 12 派次）+ run-r16 主记录复算+预注册假设
（r15-dev-record-candidate-0-same-guidance-repeat）三分判据裁决：
(a) top ≤0.75（run-r14 双侧复算 18/24）不成立、(b) top ≥0.862（run-r15
双侧复算 25/29）不成立、(c) 0.75<top 27/35=0.771429<0.862 命中⇒字母=
inconclusive（(α) 跨轮实例群漂移与 (β) §5A 全局弃权致敏两候选解释均不
排斥、归因悬置）+ 机制观察单列：top 弃权构成分型（存在性 15>接触性 11>
层归属其他 1=黑点类存在性弃权为主导而非接触性）/黑点类 12 旗全弃权连续
第 4 轮主导（r13 8→r14 14→r15 7→r16 12）+2 派次判正常/绿区语义化 6/6
派次空隙语义化+6/6 §5A 显式援引/bottom 维持性（12/14=0.857143 vs r15
11/13=0.846154 轻微恶化方向如实单列+非弃权 courtyard 0/0/0 维持但
courtyard 类旗标 2 条重现[黑点-轮廓接触族，r14 同族现象部分再现]——r15
「零 courtyard 旗」本身呈实例群敏感）+ GT 逐实例命中 r12 以来首次 0→1
（R16T-001×GT-REVC-AP-6-R2LED2，containment 1.0、面积比 7.289285 门内；
union 1/13=0.076923、agreement 0/13 维持）+ 守门 rebound 维持 0
（guard_ok=True）+ 通道归因（几何门 0→0、类别门 0→1）+ development 域
dev-record（s59 生成）。

结构照 test_r15_calibration_round15.py 先例，仅输入与轮次常量不同
（R16=同指引重复轮：r10 零变更重复轮先例再现；预注册于 r16-prep-record
json（46fbd15b），链=round15-dev-record（e981897c）→用户「继续迭代到收
敛」既定指令（2026-09-08）→r16-prep-record→r15 指引字节复用零写入→
12 次盲读（实例群全部重抽）；判据=三分（≤0.75、≥0.862、两值之间=
inconclusive），分列不合并；APR-0011 门与主通道判据各自独立、互不凌驾；
r16 实测 flag_id 两板各自从头编号=读者实例输出行为差异如实登记）。

覆盖：
- 盲读原文（reader-raw-r16-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  R16T/R16B 前缀（派发指令层覆盖）、实例旗数 9/14/12/5/5/4 与弃权
  6/13/8/5/4/3、逐派次旗数（prep1-top-i2 11 旗=轮内最高弃权格）、哈希
  与 run-r16 登记一致、拒收清单为空；
- r16-prep-record.json（预注册件）：三分判据逐字（(a) ≤0.75 →
  letter_supported/(b) ≥0.862 → letter_reject/(c) 两值之间 →
  letter_inconclusive）、changed_variables=[]、no_instrument_change、
  guidance_reuse byte_reuse_zero_change 声明（edit_list=[] +
  zero_write_declaration + base_sha256=d5babc93 全值）、no_loosening_
  note 反放宽条款逐字、measurement_design 五条、round15 授权链锚；
- guidance-r15 零写入哈希锚（d5babc93 全值）+r13 基座（c28806e1）+
  协议 v1（22dc7337）+framing/witness（7004b017/b63771f9）+renders-r14b
  四 PNG sha 逐一实测；
- calibration-run-r16.json：盘上 canonical byte 一致；字母=inconclusive
  +27/35=0.771429 带内（整数交叉相乘复核）；双基线 live 值在案（r14
  18/24=0.75、r15 25/29=0.862069）且从内嵌输入重放复算一致；视角层聚
  合复算；GT 双口径 union 1/13=0.076923（r12 以来首次命中：R16T-001×
  GT-REVC-AP-6-R2LED2，containment/面积比过门）+agreement 0/13；代表
  配置（top-i3 唯一+bottom-i1 tie）joint not_met、连续=0；机制观察
  （top 分型 11/15/1+黑点 12 旗全弃权+2 派次判正常+绿区 6/6 §5A+
  bottom 维持性 worse 方向+courtyard 0/0/0 与旗 2 条）；通道归因（几何
  门 0→0+类别门 0→1+重放对拍）+courtyard 追踪链 r8..r16；输入哈希
  （冻结工件逐件实测=登记）；
- round16-dev-record.json（s59 生成）：canonical、kind、round_label=
  r16、域声明、run_record_ref 实测 sha（2c1f8265）、hypothesis_test_i
  与 run-r16 逐字一致（verdict=inconclusive）、诊断结果与代表配置口径
  一致、R15→R16 方向性观察（带内回落/轻微恶化方向/首命中/守门 0/联合
  not_met 连续=0）、联合评价趋势（r5→r16 逐轮表、连续计数 0→0）、
  preregistration_chain 与 run-r16 冻结工件一致、next_iteration_targets
  五条（零盲读度量侧分解包/dpi 640→1280 分辨率倍增/黑点类专项/留出集
  时机须用户/GT 关闭延续+首命中非新 GT）、is_gate=False、
  in_calibrated_range 恒 False；
- s59 重跑：build_dev_record 同参重建 byte-exact 一致+防覆写护栏语义
  （字节等同→幂等跳过零覆写、不同→fail-closed）+s58 零 dev-record
  写入分包边界（round16-dev-record 不在 s58 写集）；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；R16T/R16B 前缀派发层覆盖入
  naming_constraints；受保护三文件 sha256 前 8 断言；s58 脚本锚
  （0677643d）+零阈值改动断言（calibration.py=dac80b7e）。

只读 out/（生成器模式）：零子进程/零写盘/零网络（s59 幂等重跑例外=
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

ROUND_ID = "2026-09-08-r16"
ROUND_LABEL = "r16"
DECLARED_DATE = "2026-09-08"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r16-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r16-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r16-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r16-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r16-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r16-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r16-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r16-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r16-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r16-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r16-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r16-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "9a202a63", "prep1-top-i1": "5e500770",
    "applied-top-i2": "36b57ce2", "prep1-top-i2": "a0212c71",
    "applied-top-i3": "e4e47dfe", "prep1-top-i3": "5dc6a040",
    "applied-bottom-i1": "67119c5d", "prep1-bottom-i1": "1e133ff4",
    "applied-bottom-i2": "534fc376", "prep1-bottom-i2": "6a90d491",
    "applied-bottom-i3": "8f4d9d75", "prep1-bottom-i3": "0e729a85",
}
READER_IDS = {
    "applied-top-i1": "reader-r16-top-i1",
    "prep1-top-i1": "reader-r16-top-i1",
    "applied-top-i2": "reader-r16-top-i2",
    "prep1-top-i2": "reader-r16-top-i2",
    "applied-top-i3": "reader-r16-top-i3",
    "prep1-top-i3": "reader-r16-top-i3",
    "applied-bottom-i1": "reader-r16-bottom-i1",
    "prep1-bottom-i1": "reader-r16-bottom-i1",
    "applied-bottom-i2": "reader-r16-bottom-i2",
    "prep1-bottom-i2": "reader-r16-bottom-i2",
    "applied-bottom-i3": "reader-r16-bottom-i3",
    "prep1-bottom-i3": "reader-r16-bottom-i3",
}
#: 逐派次旗数（盘面实测口径；prep1-top-i2 11 旗=轮内最高弃权格）
EXPECT_PART_COUNTS = {
    "applied-top-i1": 3, "prep1-top-i1": 6,
    "applied-top-i2": 3, "prep1-top-i2": 11,
    "applied-top-i3": 5, "prep1-top-i3": 7,
    "applied-bottom-i1": 2, "prep1-bottom-i1": 3,
    "applied-bottom-i2": 2, "prep1-bottom-i2": 3,
    "applied-bottom-i3": 3, "prep1-bottom-i3": 1,
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
#: 逐实例旗数/弃权数/弃权率（盘面实测口径；与 run-r16 聚合一致）
EXPECT_COUNTS = {"top-i1": 9, "top-i2": 14, "top-i3": 12,
                 "bottom-i1": 5, "bottom-i2": 5, "bottom-i3": 4}
EXPECT_ABSTAIN = {"top-i1": 6, "top-i2": 13, "top-i3": 8,
                  "bottom-i1": 5, "bottom-i2": 4, "bottom-i3": 3}
EXPECT_RATES = {"top-i1": 0.666667, "top-i2": 0.928571, "top-i3": 0.666667,
                "bottom-i1": 1.0, "bottom-i2": 0.8, "bottom-i3": 0.75}
EXPECT_R15_RATES = {"top-i1": 0.909091, "top-i2": 0.8, "top-i3": 0.875,
                    "bottom-i1": 0.75, "bottom-i2": 0.75, "bottom-i3": 1.0}
#: 主通道三分判据描述性边界锚（(a) 基线=run-r14 双侧复算、(b)=run-r15）
TOP_R14_BASELINE_LIVE = "18/24"
TOP_R15_BASELINE_LIVE = "25/29"
BOTTOM_R15_BASELINE_LIVE = "11/13"
#: 黑点类判正常摘录锚（同现象跨实例处置分化；reading_notes 逐字）
BLACK_DOT_NORMAL_ANCHORS = [
    ("prep1-top-i2", "右上两处黑色实心钻孔点（疑似安装孔）"),
    ("prep1-top-i3", "右上元件区域内两个黑色实心圆点（符合连接器安装孔/定位孔的常规解释）"),
]
#: 绿区语义化 §5A 显式援引摘录锚（6/6 派次；reading_notes 逐字）
GREEN_5A_ANCHORS = [
    ("applied-bottom-i1", "按 §5A 仪器注记，绿色区域为板内空隙白重着色（非丝印/阻焊/courtyard 图元）"),
    ("applied-bottom-i2", "仪器注记（§5A：橙色=原白墨图元重着色、绿色=板内空隙透白重着色且非图元）仅作为仪器事实知悉，未用作任何判据"),
]
#: 受保护文件（R16-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: s58/s59 脚本锚（R16 比对生成器/dev-record 生成器；冻结）
S58_SHA256_FIRST8 = "0677643d"
CALIBRATION_SHA256_FIRST8 = "dac80b7e"
#: r15 指引（本轮唯一判读依据、字节复用零写入；d5babc93 全值）与 r13 基座
GUIDANCE_R15_SHA256 = ("d5babc9338e4d063652d5b217b85b1fb731ce53d76f16b2a5d"
                       "79e8267c4ee267")
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r15.md": "d5babc93",
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
    "out/v3-tl2/calibration/r16-prep-record.json": "46fbd15b",
    "out/v3-tl2/calibration/round15-dev-record.json": "e981897c",
    "out/v3-tl2/calibration/r15-prep-record.json": "4c6cd919",
    "out/v3-tl2/calibration/r14-prep-record.json": "93440a3d",
    "out/v3-tl2/calibration/round14-dev-record.json": "e6354d5c",
    "out/v3-tl2/calibration/render-framing-r14b.json": "7004b017",
    "out/v3-tl2/calibration/render-witness-r14b.json": "b63771f9",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r16.json": "2c1f8265",
    "out/v3-tl2/calibration/calibration-run-r15.json": "0c37c1cb",
    "out/v3-tl2/calibration/calibration-run-r14.json": "eb8e3521",
    "out/v3-tl2/calibration/ground-truth-v1.json": "828b6b5f",
    "out/v3-tl2/calibration/ground-truth-v2.json": "e1cb63d5",
}
#: renders-r14b 四图字节复用（渲染零变更=r14/r15 轮盲读同一批文件）
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
#: r16 GT 首命中（r12 以来首次逐实例命中 0→1）
FIRST_HIT = {"flag": "R16T-001", "gt": "GT-REVC-AP-6-R2LED2",
             "instance": "top-i2", "state": "applied",
             "containment": 1.0, "area_ratio": 7.289285}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s58():
    spec = importlib.util.spec_from_file_location(
        "s58_calibration_r16_compare",
        os.path.join(REPO, "scripts", "s58_calibration_r16_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _s59():
    spec = importlib.util.spec_from_file_location(
        "s59_calibration_r16_devrecord",
        os.path.join(REPO, "scripts", "s59_calibration_r16_devrecord.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r16.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round16-dev-record.json")
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

def test_reader_raw_r16_files_valid_structure_and_prefixes():
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
            expected = "R16T" if view == "top" else "R16B"
            assert prefix == expected, (key, f["flag_id"])
    # 逐派次旗数（12/12；prep1-top-i2 11 旗=轮内最高弃权格）
    for key, n in EXPECT_PART_COUNTS.items():
        d = _load(RAW_FILES[key])
        assert len(d["per_image"][0]["flags"]) == n, key
    # 拒收清单固化（49 旗全过 calibration fail-closed 校验，0 拒收）
    run, _ = _run_record()
    assert run["parse_rejections"] == []
    assert sum(EXPECT_PART_COUNTS.values()) == run["reader"]["flag_count"][
        "total"] == 49


# ---------------------------------------------------------------------------
# 预注册件（r16-prep-record）三分判据与零变更声明
# ---------------------------------------------------------------------------

def test_r16_prep_record_three_branch_criteria_and_zero_change():
    prep = _load("r16-prep-record.json")
    assert prep["kind"] == "tl2_calibration_r16_prep_record"
    assert prep["round_id_constant"] == ROUND_ID
    assert prep["round_label"] == ROUND_LABEL
    assert prep["declared_date"] == DECLARED_DATE
    assert prep["schema_version"] == "3.0"
    assert prep["evaluation_domain"]["declared"] == "development"
    assert prep["evaluation_domain"]["in_calibrated_range"] is False
    # 三分判据逐字（r16-prep-record hypothesis_test.adjudication 原文）
    adj = prep["hypothesis_test"]["adjudication"]
    assert prep["hypothesis_test"]["hypothesis_id"] == \
        "r15-dev-record-candidate-0-same-guidance-repeat"
    assert "(α)" in prep["hypothesis_test"]["hypothesis"] and \
        "(β)" in prep["hypothesis_test"]["hypothesis"]
    assert adj["letter_supported"].startswith(
        "(a) top 全旗聚合弃权率 ≤ 0.75")
    assert adj["letter_reject"].startswith(
        "(b) top 全旗聚合弃权率 ≥ 0.862")
    assert adj["letter_inconclusive"].startswith("(c) 0.75 < top < 0.862")
    assert "两候选解释均不排斥" in adj["letter_inconclusive"]
    assert "不得以连续 inconclusive 反复消耗盲读" in \
        adj["metric_lesson_separate"]
    assert "0.846" in adj["side_observation_separate"] and \
        "0/0/0" in adj["side_observation_separate"]
    # 零变更轮声明：changed_variables=[]、instrument_change.changed=false
    assert prep["changed_variables"] == []
    assert prep["no_instrument_change"] is True
    assert prep["instrument_change"]["changed"] is False
    assert prep["manipulated_factor"] == "reader 实例群（12 派次全部重抽）"
    # 指引字节复用声明（零新建指引文件）
    gr = prep["guidance_reuse"]
    assert gr["mode"] == "byte_reuse_zero_change"
    assert gr["edit_list"] == []
    assert gr["base"] == "observation-guidance-r15.md"
    assert gr["base_sha256"] == GUIDANCE_R15_SHA256
    assert gr["derived"] is None and gr["derived_sha256"] is None
    assert "零字节不动" in gr["zero_write_declaration"] and \
        "不新建指引文件" in gr["zero_write_declaration"]
    # 授权链锚：round15-dev-record 候选原文+实测 sha
    auth = gr["chain_anchors"]["round15_dev_record_authorization"]
    assert auth["candidate_quote"].startswith("R16 第一候选=同指引重复轮")
    assert auth["sha256_measured"] == _sha(
        "out/v3-tl2/calibration/round15-dev-record.json")
    anchor = gr["chain_anchors"]["run_r15_criterion_anchor"]
    assert anchor["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r15.json")
    assert "25/29=0.862069" in anchor["frozen_values"] and \
        "18/24=0.75" in anchor["frozen_values"]
    # 反放宽条款逐字保留+无放宽语义
    assert "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由" \
        in prep["no_loosening_note"]
    assert "不构成任何阈值反向放宽" in prep["no_loosening_note"]
    # 度量设计五条先于盲读冻结+盲读纪律
    assert [it["item"] for it in prep["measurement_design"]["items"]] == \
        [1, 2, 3, 4, 5]
    assert prep["no_visual_reading"] is True
    assert prep["read_prohibition_compliance"] is True
    assert prep["pre_round_review"]["status"] == \
        "not_required_zero_change_round"
    # s57 脚本锚（R16 预注册生成器；盘上实测）
    assert _sha("out/v3-tl2/calibration/r16-prep-record.json").startswith(
        "46fbd15b")


def test_guidance_r15_zero_write_and_frozen_anchors():
    # r15 指引=本轮唯一判读依据：字节复用零写入（d5babc93 全值实测）
    assert _sha("out/v3-tl2/calibration/observation-guidance-r15.md") == \
        GUIDANCE_R15_SHA256
    text = open(os.path.join(CAL_DIR, "observation-guidance-r15.md"),
                encoding="utf-8").read()
    assert "§5A" in text
    assert "仅因形态不熟悉、不确定其设计含义" in text
    # r13 基座（机械变换基座）零字节不动+协议 v1+framing/witness
    for rel, first8 in PREREG_ANCHORS.items():
        if rel.endswith("observation-guidance-r15.md"):
            continue                                 # 已全值断言
        assert _sha(rel).startswith(first8), rel
    # renders-r14b 四图字节复用（渲染零变更=与 witness 登记值逐一相等）
    for name, want in R14B_PNG_SHA256.items():
        assert _sha("out/v3-tl2/calibration/renders-r14b/" + name) == want
    witness = _load("render-witness-r14b.json")
    assert witness["renders"]["applied"]["sha256"] == \
        R14B_PNG_SHA256["applied-bottom.png"]
    assert witness["renders"]["prep1"]["sha256"] == \
        R14B_PNG_SHA256["prep1-bottom.png"]
    # 受保护三文件（R16-CLOSE 红线：零改动）
    for rel, first8 in PROTECTED_SHA256_FIRST8.items():
        assert _sha(rel).startswith(first8), rel


# ---------------------------------------------------------------------------
# run-r16 主记录：常量、字母裁决、聚合复算、GT 首命中、门、机制观察
# ---------------------------------------------------------------------------

def test_run_r16_canonical_constants_letter_inconclusive_band():
    run, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(run)    # canonical JSON
    assert run["kind"] == "tl2_calibration_run_r16"
    assert run["round_id"] == ROUND_ID
    assert run["round_label"] == ROUND_LABEL
    assert run["declared_date"] == DECLARED_DATE
    assert run["evaluation_domain"] == "development"
    assert run["schema_version"] == "3.0"
    ht = run["hypothesis_test"]
    # 字母裁决=inconclusive：落支=(c) 0.75<top<0.862（唯一正式裁决）
    assert ht["verdict"] == "inconclusive"
    assert ht["hypothesis_id"] == \
        "r15-dev-record-candidate-0-same-guidance-repeat"
    m = ht["measurement"]
    assert m["verdict"] == "inconclusive"
    assert m["letter_branch"].startswith("(c) 0.75 < top < 0.862")
    assert m["crit_a_top_le_r14_baseline"] is False
    assert m["crit_b_top_ge_r15_baseline"] is False
    # 27/35=0.771429 落在带内（整数交叉相乘复核，避免浮点）
    assert (m["top_abstain_count_r16"], m["top_abstain_flags_r16"]) == \
        (27, 35)
    assert m["top_abstain_rate_r16"] == 0.771429
    assert 27 * 24 > 18 * 35                            # > 0.75（(a) 否）
    assert 27 * 29 < 25 * 35                            # < 0.862（(b) 否）
    assert "整数交叉相乘" in ht["verdict_text"]
    # 双基线 live 值在案（fail-closed 登记）
    assert m["top_abstain_rate_r14_baseline_live"] == TOP_R14_BASELINE_LIVE
    assert m["top_abstain_rate_r14_baseline_value"] == 0.75
    assert m["top_abstain_rate_r15_baseline_live"] == TOP_R15_BASELINE_LIVE
    assert m["top_abstain_rate_r15_baseline_value"] == 0.862069
    assert m["baseline_cross_check"]["r14_top_live"] == "18/24"
    assert m["baseline_cross_check"]["r15_top_live"] == "25/29"
    # 守门通道独立单列（rebound 维持 0）
    assert m["guard_channel"]["guard_ok"] is True
    # 判据原文引用=r16-prep-record adjudication（逐字）
    prep = _load("r16-prep-record.json")
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "letter_inconclusive",
              "letter_reject", "letter_supported",
              "metric_lesson_separate", "side_observation_separate"):
        assert q[k] == adj[k], k
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r16-prep-record.json")


def test_run_r16_view_aggregates_recomputed_live():
    run, _ = _run_record()
    run15 = _load("calibration-run-r15.json")
    run14 = _load("calibration-run-r14.json")
    # 本轮聚合复算（top 27/35、bottom 12/14）
    assert _view_aggregate(run, "top") == (35, 27)
    assert _view_aggregate(run, "bottom") == (14, 12)
    # 基线 live 重放复算（run-r14/run-r15 内嵌输入；不手工抄数）
    assert _view_aggregate(run14, "top") == (24, 18)
    assert _view_aggregate(run15, "top") == (29, 25)
    assert _view_aggregate(run15, "bottom") == (13, 11)
    # 逐实例旗数/弃权数/弃权率（与 r15 对照）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    assert counts == EXPECT_COUNTS
    assert abstains == EXPECT_ABSTAIN
    assert rates == EXPECT_RATES
    r15rates = {n: run15["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER}
    assert r15rates == EXPECT_R15_RATES
    # 视角层三分列（measurement_design item 2）
    assert run["view_layer"]["top"]["abstain_rate_range"] == 0.261904
    assert run["view_layer"]["bottom"]["abstain_rate_range"] == 0.25
    assert run["hypothesis_test"]["stratified_observation"]["top"][
        "r16_range"] == 0.261904
    # bottom 侧观察单列（12/14=0.857143 vs r15 11/13=0.846154）
    bso = run["hypothesis_test"]["measurement"]["bottom_side_observation"]
    assert (bso["bottom_abstain_flags_r16"],
            bso["bottom_abstain_count_r16"]) == (14, 12)
    assert bso["bottom_abstain_rate_r16"] == 0.857143
    assert bso["bottom_abstain_rate_r15_baseline_value"] == 0.846154
    assert bso["bottom_abstain_rate_r15_baseline_live"] == "11/13"


def test_run_r16_gt_first_hit_union_agreement():
    run, _ = _run_record()
    dual = run["gt_match_dual"]
    # GT 条目层双口径：union 1/13（r12 以来首次 0→1）、agreement 0/13
    assert dual["denominator"] == 13
    assert dual["union"]["count"] == 1
    assert dual["union"]["gt_ids"] == ["GT-REVC-AP-6-R2LED2"]
    assert dual["union"]["gt_recall_union"] == 0.076923
    assert dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_ids"] == []
    # 首命中明细：R16T-001×AP-6（top-i2 applied；containment/面积比过门）
    hit = [g for g in dual["per_gt"]
           if g["gt_id"] == "GT-REVC-AP-6-R2LED2"][0]
    assert hit["matched_by_count"] == 1
    h0 = hit["hits"][0]
    assert (h0["flag_id"], h0["instance"], h0["state"]) == \
        (FIRST_HIT["flag"], FIRST_HIT["instance"], FIRST_HIT["state"])
    assert h0["containment"] == FIRST_HIT["containment"]
    assert h0["area_ratio"] == FIRST_HIT["area_ratio"]
    assert h0["containment"] >= cal.CONTAINMENT_MIN
    assert h0["area_ratio"] <= cal.AREA_RATIO_MAX
    # 逐实例侧：top-i2 combined matches_detail 同一对（代表配置不含
    # top-i2，门与逐实例命中分列如实）
    comb = run["instances"]["top-i2"]["combined"]
    assert comb["matches_total"] == 1 and comb["gt_matched_union"] == 1
    assert comb["matches_detail"][0]["gt_id"] == FIRST_HIT["gt"]
    # bottom 零匹配属结构性（GT 13 条全部 side=top；gt-audit-r1 bottom
    # GT=无源已关闭）
    assert all(g["side"] == "top" for g in dual["per_gt"])
    assert run["gt_audit_reference"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")
    # 阈值常量零改动（声明常量；只作口径引用）
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0


def test_run_r16_representative_joint_and_metric_ranges():
    run, _ = _run_record()
    # 代表配置=top-i3（中位 12 唯一）+bottom-i1（中位 5 tie 按先序）
    rep = run["representative_configuration"]
    assert rep["members"] == {"top": "top-i3", "bottom": "bottom-i1"}
    assert rep["selection"]["top"]["tie"] is False
    assert rep["selection"]["bottom"]["tie"] is True
    # 代表配置聚合（measurement_design item 4）
    agg = run["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"]) == (17, 13, 0.764706)
    assert (agg["gt_recall_total"], agg["seed_match_rate_total"],
            agg["matches_total"]) == (0.0, 0.0, 0)
    assert agg["abstain_rate_by_view"] == {
        "top": 0.666667, "top_fraction": "8/12",
        "bottom": 1.0, "bottom_fraction": "5/5"}
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
    assert mr["top"]["flag_count"] == {"max": 14, "min": 9}
    assert mr["top"]["abstain_rate"] == {"max": 0.928571, "min": 0.666667}
    assert mr["bottom"]["matches_total"] == {"max": 0, "min": 0}


def test_run_r16_mechanism_observation_typology_blackdot_green():
    run, _ = _run_record()
    mo = run["hypothesis_test"]["mechanism_observation"]
    # top 弃权构成分型：存在性 15>接触性 11>层归属其他 1（黑点类存在性
    # 弃权为主导而非接触性）
    ty = mo["top_abstain_typology"]
    assert ty["type_counts"] == {"contact": 11, "existence": 15,
                                 "other_layer": 1}
    assert ty["top_abstain_flags_total"] == 27
    assert len(ty["rows"]) == 27
    assert ty["top_abstain_rates_by_instance"] == {
        "top-i1": 0.666667, "top-i2": 0.928571, "top-i3": 0.666667}
    # 黑点类 12 旗全弃权（连续第 4 轮主导）+2 派次判正常
    bdt = mo["black_dot_tracking"]
    assert bdt["all_abstain"] is True
    assert bdt["by_instance"] == {"bottom-i1": 3, "bottom-i2": 4,
                                  "bottom-i3": 3, "top-i1": 1,
                                  "top-i2": 1, "top-i3": 0}
    assert len(bdt["black_dot_flags"]) == 12
    assert all(f["abstain"] is True for f in bdt["black_dot_flags"])
    assert "2 派次判正常" in bdt["notes_normal_dispositions"]
    # 判正常摘录逐字在案（substring fail-closed）
    for key, excerpt in BLACK_DOT_NORMAL_ANCHORS:
        assert excerpt in _raw_text(key), key
    # 绿区语义化：6/6 派次空隙语义化+6/6 显式援引 §5A（r15 收敛保持）
    gs = mo["green_semantics_by_instance"]
    assert len(gs["evidence"]) == 6
    assert all(e["cites_5A"] is True for e in gs["evidence"])
    assert all(gs["green_semantics_by_instance"][n]["§5A_cited"] is True
               for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert "6/6" in gs["status"] or "6 派次" in gs["observation"]
    for key, excerpt in GREEN_5A_ANCHORS:
        assert excerpt in _raw_text(key), key
    # bottom 维持性：非弃权 courtyard 0/0/0 维持但旗 2 条重现（实例群
    # 敏感）；聚合 12/14=0.857143 vs 11/13=0.846154 恶化方向
    bsm = mo["bottom_side_observation_maintenance"]
    assert bsm["counts"]["bottom_rate_vs_r15_direction"] == "worse"
    assert bsm["counts"]["r16_bottom_courtyard_non_abstain_by_instance"] \
        == {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert bsm["counts"]["r16_bottom_courtyard_flags_total"] == 2
    assert bsm["counts"]["bottom_abstain_rate_r16"] == 0.857143
    assert bsm["counts"]["bottom_abstain_rate_r15_baseline"] == 0.846154
    assert "实例群敏感" in bsm["observation"]
    assert "零旗标路径" in bsm["observation"]


def test_run_r16_channel_attribution_and_courtyard_tracking():
    run, _ = _run_record()
    ca = run["channel_attribution"]
    # 几何门 0→0（r14=1 回升未延续）；guard_ok=True 独立单列
    g1 = ca["channel_1_geometry_gate"]
    assert len(g1["r16_area_ratio_rejected_entries"]) == 0
    assert len(g1["r15_area_ratio_rejected_entries"]) == 0
    assert len(g1["r14_area_ratio_rejected_entries"]) == 1
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guard_ok"] is True
    # 类别门 0→1（r12–r15 连续零条目后本轮计数；R16T-006 出局条目在案）
    g2 = ca["channel_2_category_gate"]
    assert len(g2["r16_category_mismatch_entries"]) == 1
    e = g2["r16_category_mismatch_entries"][0]
    assert (e["flag_id"], e["gt_id"], e["instance"]) == \
        ("R16T-006", "GT-REVC-P1-R4J3", "top-i1")
    assert (e["containment"], e["area_ratio"]) == (0.848147, 1.529072)
    # 通道链自 r6 含 r16；视角门 0 条
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"]["r16"] == 0
    assert chain["category_gate_category_mismatch_by_round"]["r16"] == 1
    assert ca["view_gate_observations"]["r16_entries"] == []
    # 重放对拍一致（R16 十二件重放全部复现；候选对=首命中对）
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] \
        is True
    assert ca["method"]["replay_cross_check"]["r16_candidate_pairs_by_part"][
        "applied-top-i2"] == [["R16T-001", "GT-REVC-AP-6-R2LED2"]]
    # courtyard 被动追踪：命中链 r8..r16（r16=1 非弃权 courtyard 命中）
    ct = run["courtyard_tracking"]
    assert ct["courtyard_matches_r16"] == 1
    assert [ct[f"courtyard_matches_r{r}"] for r in
            (8, 9, 10, 11, 12, 13, 14, 15, 16)] == [1, 0, 1, 3, 0, 0, 0, 0, 1]
    assert len(ct["r16_courtyard_flags"]["abstain"]) == 14
    na = ct["r16_courtyard_flags"]["non_abstain"]
    assert len(na) == 1
    assert na[0]["matched_detail"]["gt_id"] == "GT-REVC-AP-6-R2LED2"
    assert na[0]["matched_detail"]["containment"] == 1.0
    # 阈值零改动声明（零期望、不为提高命中调阈值）
    assert "零改动" in ct["threshold_note"]
    # reroute 被动追踪（产量链 r15=4→r16=2；滥用型 r16=0）
    rc = run["hypothesis_test"]["reroute_continuation_r16"]
    assert rc["reroute_total_r16"] == 2
    assert rc["production_chain"]["r16"] == 2
    assert rc["misuse_chain_note"].endswith("r16=0（R16T-004 两旗「等长|蛇"
                                            "形」子串零命中、均为存在性弃"
                                            "权）——不构成 r16 判据输入（两"
                                            "判据分列互不凌驾）") or \
        "r16=0" in rc["misuse_chain_note"]


def test_run_r16_input_hashes_and_frozen_chain():
    run, _ = _run_record()
    # 预注册冻结工件：逐件实测 sha 与登记一致（37+ 件含链锚与渲染复用）
    arts = run["preregistration"]["frozen_artifacts"]
    assert len(arts) >= 30
    for item in arts:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {a["role"] for a in arts}
    assert "r16_prep_record_preregistration" in roles
    assert "r15_dev_record_preregistration_source" in roles
    assert "observation_guidance_r15_active_byte_reuse" in roles
    assert "render_witness_r14b_byte_reuse_witness" in roles
    # 十二件盲读原文哈希与登记一致（fail-closed）
    for key, info in run["reader"]["raw_files"].items():
        assert _sha(info["path_rel"]) == info["sha256"], key
        assert key in RAW_FILES
    # 12 件直读（零改动直读、非盲读违规）、零拒收
    assert all(v["direct_json_parse"] is True and v["repair"] == "no_repair"
               for v in run["reader"]["parse"].values())
    assert run["parse_rejections"] == []
    # 参考轮链锚：run-r15/run-r14 实测与登记一致
    rr = run["reference_rounds"]
    assert rr["r15_run"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r15.json")
    assert rr["r14_run"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r14.json")
    # instrument_change：零变更轮（renders-r14b 字节复用四 PNG 逐一对拍）
    ic = run["instrument_change"]
    assert ic["changed"] is False and ic["changed_variables_registered"] == []
    pngs = ic["unchanged_components"][0]["pngs"]
    assert all(p["match"] is True for p in pngs) and len(pngs) == 4


# ---------------------------------------------------------------------------
# round16-dev-record.json（s59 生成）
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round16_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["is_gate"] is False
    # 本轮性质=同指引重复轮（零变更轮）+字节复用双锚
    assert "同指引重复轮" in dev["round_nature"]
    assert "d5babc93" in dev["round_nature"]
    assert "renders-r14b" in dev["round_nature"] and "字节复用" in \
        dev["round_nature"]
    assert "changed=false" in dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "第十六轮" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert "第 16 轮" in dev["domain_basis_quote"]
    # run_record_ref=run-r16 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r16.json"
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r16.json")
    assert dev["run_record_ref"]["sha256"].startswith("2c1f8265")
    # 假设裁决节与 run-r16 逐字一致（verdict=inconclusive；(a)(b) 双否）
    run, _ = _run_record()
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "inconclusive"
    assert dev["hypothesis_test_i"]["measurement"][
        "crit_a_top_le_r14_baseline"] is False
    assert dev["hypothesis_test_i"]["measurement"][
        "crit_b_top_ge_r15_baseline"] is False
    assert dev["hypothesis_test_i"]["measurement"][
        "top_abstain_rate_r16"] == 0.771429
    assert dev["hypothesis_test_i"]["measurement"]["guard_channel"][
        "guard_ok"] is True
    # 诊断结果与 run-r16 一致（代表配置口径：top-i3 唯一+bottom-i1 tie）
    assert "top-i3" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.764706
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    assert dev["diagnostic_result"]["gt_match_dual"]["union"]["count"] == 1
    # instrument_change 镜像 run（零变更轮）+链与 GT 审计引用
    assert dev["instrument_change"] == run["instrument_change"]
    assert dev["instrument_change"]["changed"] is False
    assert dev["gt_audit_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")
    # 预注册链=run-r16 冻结工件逐件实测（与 run 登记一致）+链注锚
    chain = dev["preregistration_chain"]
    for item in run["preregistration"]["frozen_artifacts"]:
        assert chain[item["role"]] == {"path_rel": item["path_rel"],
                                       "sha256": item["sha256"]}
    note = dev["preregistration_chain_note"]
    for anchor in ("e981897c", "46fbd15b", "d5babc93", "b63771f9",
                   "2c1f8265", "62343380", "1f20554a", "继续迭代到收敛"):
        assert anchor in note, anchor


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：R15/R14 基线数值独立复算（top 25/29、
    18/24；bottom 11/13；run-r15/run-r14 内嵌输入）；next_iteration_
    targets 覆盖 R17 零盲读度量侧分解包/dpi 640→1280 分辨率倍增/黑点类
    专项/留出集运行时机（须用户）/GT 关闭延续（首命中非新 GT）；不写
    「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r15"])
    # R15/R14 基线独立复算（内嵌输入）
    run15 = _load("calibration-run-r15.json")
    run14 = _load("calibration-run-r14.json")
    assert _view_aggregate(run15, "top") == (29, 25)
    assert _view_aggregate(run14, "top") == (24, 18)
    assert _view_aggregate(run15, "bottom") == (13, 11)
    # R15→R16 分层/聚合数字在观察中如实引用
    for need in ("12→12", "42→49", "11/10/8→9/14/12", "4/4/5→5/5/4",
                 "6→10", "36→39", "0.857143", "0.795918",
                 "18/24=0.75", "25/29=0.862069", "27/35=0.771429",
                 "带内回落", "11/13=0.846154", "12/14=0.857143", "恶化方向",
                 "0.909091/0.8/0.875", "0.666667/0.928571/0.666667",
                 "0.109091", "0.261904", "0.75/0.75/1.0", "1.0/0.8/0.75",
                 "R16T-001", "GT-REVC-AP-6-R2LED2", "containment 1.0",
                 "7.289285", "1/13=0.076923", "r12 以来首次",
                 "R16T-006", "几何门", "类别门", "guard_ok=True",
                 "接触性 11", "存在性 15", "黑点类 12 旗", "2 派次判正常",
                 "6/6", "§5A", "courtyard", "0/0/0", "实例群敏感",
                 "r8=1→r9=0→r10=1→r11=3→r12=0→r13=0→r14=0→r15=0→r16=1",
                 "inconclusive", "归因悬置", "未读取盘上任何其他文件",
                 "措辞差异", "各自从头编号", "gt-audit-r1", "不凌驾",
                 "唯一正式裁决"):
        assert need in obs, need
    # 联合评价趋势：r5→r16 逐轮表；连续达标计数 0（R15 后）→0（本轮）
    trend = dev["joint_evaluation_trend"]
    assert [r["round"] for r in trend["by_round"]] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16"]
    assert trend["by_round"][-1]["abstain_rate_total"] == 0.764706
    assert trend["by_round"][-1]["source"]["sha256"].startswith("2c1f8265")
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "39/49=0.795918" in trend["aggregation_scope_note"]
    # next_iteration_targets 五条（R17 候选覆盖）
    nxt = "\n".join(dev["next_iteration_targets"])
    assert len(dev["next_iteration_targets"]) == 5
    assert "R17 第一候选" in nxt and "零盲读度量侧分解包" in nxt
    assert "r13–r16" in nxt and "家族分型" in nxt
    assert "不回写既往轮次字母" in nxt and "不触 GT" in nxt
    assert "不触阈值" in nxt
    assert "dpi 640→1280" in nxt and "单变量" in nxt
    assert "预注册" in nxt and "探针先验证" in nxt
    assert "分辨率依赖" in nxt
    assert "黑点类专项候选" in nxt and "连续 4 轮" in nxt
    assert "机械孔正常形态" in nxt and "反放宽条款逐字保留" in nxt
    assert "留出集运行时机" in nxt and "须用户拍板" in nxt
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    assert "收敛未宣告" in nxt and "in_calibrated_range 恒 False" in nxt
    assert "人工批准" in nxt
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选全部关闭" in nxt
    assert "非新 GT" in nxt and "GT-REVC-AP-6-R2LED2" in nxt
    # honest_conclusion：inconclusive 如实（归因悬置、未决；bottom 轻微
    # 恶化如实；黑点类存在性弃权主导=机制发现）
    hc = dev["honest_conclusion"]
    for need in ("inconclusive", "归因悬置", "未决", "27/35=0.771429",
                 "18/24=0.75", "25/29=0.862069", "0.764706", "not_met",
                 "0.857143", "0.846154", "0/0/0", "实例群敏感",
                 "存在性 15>接触性 11", "连续第 4 轮", "2 派次判正常",
                 "6/6", "r12 以来首次", "guard_ok=True", "分列不合并",
                 "不得冒充留出", "in_calibrated_range 恒 False",
                 "precision/FPR"):
        assert need in hc, need
    # r16 域声明与门语义（in_calibrated_range 恒 False）
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r16-prep-record.json")
    assert dev["is_gate"] is False


def test_s59_rerun_idempotent_and_overwrite_guard():
    """s59 重跑语义：build_dev_record 同参重建 byte-exact 一致；防覆写
    护栏（字节等同→幂等跳过零覆写、不同→fail-closed）；s58 零
    dev-record 写入分包边界（round16-dev-record 不在 s58 写集）。"""
    s59 = _s59()
    dev, disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(s59.build_dev_record()) == disk
    # 声明常量（无 wall-clock）
    assert s59.DECLARED_DATE == "2026-09-08"
    assert s59.ROUND_ID == "2026-09-08-r16"
    assert s59.ROUND_LABEL == "r16"
    assert s59.KIND == "tl2_calibration_round16_dev_record"
    # 三分判据实测锚常量（操作化定义）
    assert (s59.EXPECT_TOP_ABSTAIN_R16, s59.EXPECT_TOP_FLAGS_R16) == (27, 35)
    assert s59.EXPECT_TOP_RATE_R16 == 0.771429
    assert (s59.EXPECT_TOP_R14_BASELINE_LIVE,
            s59.EXPECT_TOP_R14_BASELINE_VALUE) == ("18/24", 0.75)
    assert (s59.EXPECT_TOP_R15_BASELINE_LIVE,
            s59.EXPECT_TOP_R15_BASELINE_VALUE) == ("25/29", 0.862069)
    assert (s59.EXPECT_BOTTOM_ABSTAIN_R16,
            s59.EXPECT_BOTTOM_FLAGS_R16) == (12, 14)
    assert s59.EXPECT_BOTTOM_R15_BASELINE_LIVE == "11/13"
    assert s59.EXPECT_TYPE_COUNTS == {"contact": 11, "existence": 15,
                                      "other_layer": 1}
    assert s59.EXPECT_COURTYARD_NON_ABSTAIN == {"bottom-i1": 0,
                                                "bottom-i2": 0,
                                                "bottom-i3": 0}
    # 防覆写护栏纯函数语义
    assert s59.overwrite_guard(None, b"x") == "write"
    assert s59.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s59.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：round16-dev-record 已存在且字节等同 → main 正常完成
    # （零覆写）
    path = os.path.join(CAL_DIR, "round16-dev-record.json")
    before = open(path, "rb").read()
    s59.main()                                          # 不抛异常=幂等路径
    after = open(path, "rb").read()
    assert before == after                       # 字节零改动
    # 分包边界：s58 零 dev-record 写入（round16-dev-record 由 s59 落盘；
    # s58 只产 run-r16），幂等重跑后该件字节零改动
    s58 = _s58()
    assert not hasattr(s58, "build_dev_record")
    assert hasattr(s58, "build_run")                    # s58 只产 run-r16
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r16.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    """命名约束与门语义：seed_match_rate 注记、递归无越界命名键、
    R16T/R16B 前缀派发层覆盖在案、阈值常量与比较器零改动、s58 脚本锚、
    字母裁决与门分列。"""
    run, _ = _run_record()
    dev, _ = _run_dev_record()
    nc = run["naming_constraints"]
    assert "R16T/R16B" in nc and "派发指令层覆盖" in nc
    assert "禁称 precision/FPR" in nc
    # 递归无越界命名键（run 与 dev 全树）
    for doc in (run, dev):
        _assert_no_banned_keys(doc)
    # seed_match_rate 注记常量一致（禁称 precision/FPR）
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 阈值常量零覆盖（声明常量）+比较器脚本锚（冻结）
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert _sha("pcbflow/calibration.py").startswith(CALIBRATION_SHA256_FIRST8)
    assert _sha("scripts/s58_calibration_r16_compare.py").startswith(
        S58_SHA256_FIRST8)
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；零旗标格为空
    # +拒收清单为空
    assert run["hypothesis_test"]["verdict"] == "inconclusive"
    assert run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分开如实记录" in run["hypothesis_test"]["verdict_text"] and \
        "不合并" in run["hypothesis_test"]["verdict_text"]
    assert run["hypothesis_test"]["measurement"][
        "crit_a_top_le_r14_baseline"] is False
    assert run["hypothesis_test"]["measurement"]["guard_channel"][
        "guard_ok"] is True
    assert run["reader"]["zero_flag_parts"]["parts"] == []
    assert run["parse_rejections"] == []
    # 度量教训单列在 dev-record notes（(c) 带非空分辨力有限；不追溯适用）
    assert "分辨力有限" in dev["notes"][-1]
    assert "不追溯适用" in dev["notes"][-1]
    assert "不得以连续 inconclusive 反复消耗盲读" in dev["notes"][-1]


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
