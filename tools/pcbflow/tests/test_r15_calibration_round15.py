"""R15 执行包测试：reader 判读迭代第十五轮收口（CAL-R15-CLOSE 包 B）——
盲读原文与视角注入（12 派次=4 视角格×3 实例，v1.2 规约沿用第四轮）+
run-r15 主记录复算+预注册假设（r14-dev-record-candidate-0-guidance-
color-legend）三分判据裁决（条件 (i) bottom courtyard 非弃权 0/0/0=
零旗标路径维持+条件 (ii) bottom 全旗聚合弃权率 11/13=0.846154≤10/11
满足+条件 (iii) top 全旗聚合弃权率 25/29=0.862069>run-r14 同口径双侧
复算 18/24=0.75 违约⇒字母=reject 拒绝支=第 (iii) 项（top 全旗聚合弃
权率回退：其他轴回退）+机制观察单列：图例对 bottom 主通道生效（混淆
回落+绿区语义化三实例收敛为空隙/翼瓣几何（2/3 实例显式援引 §5A）+
r14 的 4 条 bottom courtyard 弃权未再现）/接触性判据 5/6/黑点类 7 旗
全弃权+3 派次判正常/残余实例差异；度量教训单列：判据 (iii) 对跨轮实
例群漂移敏感（r10 教训在新轴复现））+ 通道归因（vs R14：几何门 1→0
回落）+ courtyard 被动追踪 + development 域 dev-record（s56 生成）。

结构照 test_r14_calibration_round14.py 先例，仅输入与轮次常量不同
（R15=单变量指引侧变更轮：observation-guidance-r15.md=d5babc93 由
r13 指引 c28806e1 机械变换生成（新增 §5A 渲染配色仪器注记节=仪器事
实注记、非判据；示例旗 ID 前缀 R13T-/R13B-→R15T-/R15B- 随指引落盘
固化）；渲染零变更（renders-r14b 四图字节复用=r14 轮盲读所用同一批
文件）；GT/阈值零变更；instrument_change.changed=false 已预注册；预
注册于 r15-prep-record.json（4c6cd919），链=round14-dev-record
（e6354d5c）→用户「请继续」批准（2026-09-08）→r15-prep-record→
r15 指引落盘→12 次盲读；判据=三分（0/0/0、≤10/11、≤run-r14 同口
径 18/24），分列不合并；APR-0011 门与主通道判据各自独立、互不凌驾；
r15 实测 flag_id 两板各自从头编号=读者实例输出行为差异如实登记）。

覆盖：
- 盲读原文（reader-raw-r15-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  两板各自从头编号（同实例 applied/prep1 各自起编=与 r13/r14 跨板连
  续不同的实例输出行为差异）、实例旗数 11/10/8/4/4/5 与弃权
  10/8/7/3/3/5、reroute 恰 4 条（2 非弃权边界报告+2 存在性弃权；其中
  R15T-001「蛇形」子串=否定式收窄判据援引）、拒收清单固化（42 旗全过
  calibration fail-closed 校验，0 拒收）、哈希与 run-r15 登记一致；
- 视角注入确定性+派发模式（12 派次两波次串行保序）+读者实例披露
  （12/12 派次自述「未读取盘上任何其他文件」=v1.2 沿用合规；输出格
  式披露：12 件缩进格式冻结原始判读件、零改动直读；本轮无零旗标格）；
- calibration-run-r15.json：盘上 canonical byte 一致；逐实例逐态
  compare_v3 用内嵌输入重算 byte-exact 一致（12 格全部有旗、view_check
  全 full、零 matches）；内嵌 gt_entries=源 GT 文件条目+
  derivation-log-r5 重投影零新派生；六实例聚合复算（弃权率
  0.909091/0.8/0.875/0.75/0.75/1.0）；视角层三分列（top 极差
  0.109091/bottom 极差 0.25）；双口径（union 0/13、agreement 0/13）；
  代表配置（top-i2 唯一+bottom-i1 tie 按先序）joint 复算（14 旗 11 弃
  权=0.785714；APR-0011 联合 not_met）+per-metric 范围；
- 预注册假设三分判据裁决：判据引用=r15-prep-record adjudication 原文
  （supported_requires_all/reject_if 逐字）；实测 (i) 0/0/0（零旗标路
  径、成因与 r13 判正常/r14 全弃权三分）；(ii) 11/13=0.846154≤10/11
  （r13 基线重放交叉核对）；(iii) 25/29=0.862069>18/24=0.75（双侧复
  算）违约⇒verdict=reject；守门通道 R14=1→R15=0 回落独立单列
  （guard_ok=True；r15 support 条件不含守门要件）；机制观察单列（主
  通道三分实测/分类通道转移/绿区语义化收敛+§5A 援引摘录校验/接触性
  5/6/黑点类 7 旗+3 派次判正常/残余实例差异）；reroute 被动追踪（产
  量链 r14=1→r15=4；滥用型机械命中=1 但语义=否定式正确排除）；
- 通道归因（vs R14）：重放对拍 R13/R14 十二件（复算=在案登记）与
  R15 十二件全部复现（候选对=空集）；几何门 1→0（R14T-002 条目未再
  现）、类别门 0→0、视角门 0→0；链自 r6 含 r15；courtyard 追踪：非弃
  权 0 条、弃权 6 条全部 top、命中 r8..r15 链；
- 预注册链：37 件冻结工件逐件实测 sha 与登记一致（r14-dev→
  r15-prep→r15 指引 d5babc93→渲染零变更 witness b63771f9→run-r15
  0c37c1cb）；guidance-r15 §5A 节在位+§4 量化判据 substring 逐字保
  留+R13 前缀零残留；阈值常量零覆盖（containment 0.5/area_ratio_max
  10.0；calibration.py=dac80b7e）；gt-audit-r1（1f20554a）；
- round15-dev-record.json（s56 生成）：canonical、kind、round_label=
  r15、域声明、run_record_ref 实测 sha、hypothesis_test_i 与 run-r15
  逐字一致（verdict=reject）、诊断结果与代表配置口径一致、R14→R15 方
  向性观察（旗标 38→42、bottom 14/14→11/13、top 18/24→25/29、守门
  1→0、双口径 0/13 维持、连续 not_met 维持）、联合评价趋势（r5→r15
  逐轮表、连续计数 0→0）、flag_production 记账、preregistration_chain
  与 run-r15 冻结工件一致、next_iteration_targets 六条（同指引重复轮/
  绿区语义化维持观察/top 弃权构成细分/黑点类延续/留出集时机须用户/
  GT 关闭延续）、is_gate=False、in_calibrated_range 恒 False；
- s56 重跑：build_dev_record 同参重建 byte-exact 一致+防覆写护栏语
  义（字节等同→幂等跳过零覆写、不同→fail-closed）+s55 零 dev-record
  写入分包边界（round15-dev-record 不在 s55 写集）；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；R15T/R15B 前缀随指引 §6 落盘固化入
  naming_constraints；受保护三文件 sha256 前 8 断言；s55 脚本锚
  （bc58afc6）+零阈值改动断言。

只读 out/（生成器模式）：零子进程/零写盘/零网络（s56 幂等重跑例外=
字节等同零覆写路径）。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import critic                       # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-08-r15"
ROUND_LABEL = "r15"
DECLARED_DATE = "2026-09-08"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r15-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r15-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r15-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r15-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r15-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r15-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r15-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r15-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r15-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r15-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r15-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r15-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "85143806", "prep1-top-i1": "578fab5f",
    "applied-top-i2": "65905c77", "prep1-top-i2": "6f460dcf",
    "applied-top-i3": "b6b881a0", "prep1-top-i3": "1f50bda2",
    "applied-bottom-i1": "092c67f0", "prep1-bottom-i1": "8188b798",
    "applied-bottom-i2": "0e380ede", "prep1-bottom-i2": "6e2e2e6a",
    "applied-bottom-i3": "112fe7c9", "prep1-bottom-i3": "89254b87",
}
READER_IDS = {
    "applied-top-i1": "reader-r15-top-i1",
    "prep1-top-i1": "reader-r15-top-i1",
    "applied-top-i2": "reader-r15-top-i2",
    "prep1-top-i2": "reader-r15-top-i2",
    "applied-top-i3": "reader-r15-top-i3",
    "prep1-top-i3": "reader-r15-top-i3",
    "applied-bottom-i1": "reader-r15-bottom-i1",
    "prep1-bottom-i1": "reader-r15-bottom-i1",
    "applied-bottom-i2": "reader-r15-bottom-i2",
    "prep1-bottom-i2": "reader-r15-bottom-i2",
    "applied-bottom-i3": "reader-r15-bottom-i3",
    "prep1-bottom-i3": "reader-r15-bottom-i3",
}
VIEW_OF_KEY = {
    "applied-top-i1": "top", "prep1-top-i1": "top",
    "applied-top-i2": "top", "prep1-top-i2": "top",
    "applied-top-i3": "top", "prep1-top-i3": "top",
    "applied-bottom-i1": "bottom", "prep1-bottom-i1": "bottom",
    "applied-bottom-i2": "bottom", "prep1-bottom-i2": "bottom",
    "applied-bottom-i3": "bottom", "prep1-bottom-i3": "bottom",
}
STATE_OF_KEY = {
    "applied-top-i1": "applied", "prep1-top-i1": "prep1",
    "applied-top-i2": "applied", "prep1-top-i2": "prep1",
    "applied-top-i3": "applied", "prep1-top-i3": "prep1",
    "applied-bottom-i1": "applied", "prep1-bottom-i1": "prep1",
    "applied-bottom-i2": "applied", "prep1-bottom-i2": "prep1",
    "applied-bottom-i3": "applied", "prep1-bottom-i3": "prep1",
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
#: 逐实例旗数/弃权数（盘面实测口径；与 run-r15 聚合一致）
EXPECT_COUNTS = {"top-i1": 11, "top-i2": 10, "top-i3": 8,
                 "bottom-i1": 4, "bottom-i2": 4, "bottom-i3": 5}
EXPECT_ABSTAIN = {"top-i1": 10, "top-i2": 8, "top-i3": 7,
                  "bottom-i1": 3, "bottom-i2": 3, "bottom-i3": 5}
EXPECT_PART_COUNTS = {
    "applied-top-i1": 7, "prep1-top-i1": 4,
    "applied-top-i2": 4, "prep1-top-i2": 6,
    "applied-top-i3": 4, "prep1-top-i3": 4,
    "applied-bottom-i1": 3, "prep1-bottom-i1": 1,
    "applied-bottom-i2": 2, "prep1-bottom-i2": 2,
    "applied-bottom-i3": 3, "prep1-bottom-i3": 2,
}
#: 本轮无零旗标格（12 格全部≥1 旗；最小格=prep1-bottom-i1 单旗）
ZERO_FLAG_PARTS = []
#: 原始件键 → 实例键（"{state}-{view}-i{n}" → "{view}-i{n}"）
INSTANCE_OF_KEY = {k: k.split("-", 1)[1] for k in RAW_FILES}
GT_V1_IDS = ["GT-REVC-P1-R4J3", "GT-REVC-P1-F1J2", "GT-REVC-P1-L1NB",
             "GT-REVC-P1-L1SHORT"]
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
#: R15 reroute 恰 4 条（2 非弃权边界报告+2 存在性弃权；r14 的 1 条→
#: r15 产量链回升；R15T-001 含「蛇形」子串=否定式收窄判据援引）
EXPECT_R15_REROUTE = sorted([
    ("top-i1", "R15T-002", "prep1", True),
    ("top-i1", "R15T-005", "applied", False),
    ("top-i3", "R15T-001", "applied", False),
    ("top-i3", "R15T-004", "prep1", True),
])
#: 受保护文件（R15-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: s55 脚本锚（R15 比对生成器；冻结）
S55_SHA256_FIRST8 = "bc58afc6"
#: r15 指引（本轮唯一判读依据；d5babc93）与 r13 基座（c28806e1 零字节
#: 不动=机械变换基座）
GUIDANCE_SHA256_FIRST8 = {
    "out/v3-tl2/calibration/observation-guidance-r15.md": "d5babc93",
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r15.md": "d5babc93",
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
    "out/v3-tl2/calibration/r15-prep-record.json": "4c6cd919",
    "out/v3-tl2/calibration/r14-prep-record.json": "93440a3d",
    "out/v3-tl2/calibration/r13-prep-record.json": "b1c0d8b5",
    "out/v3-tl2/calibration/round14-dev-record.json": "e6354d5c",
    "out/v3-tl2/calibration/round13-dev-record.json": "6b34c442",
    "out/v3-tl2/calibration/round12-dev-record.json": "1411dab6",
    "out/v3-tl2/calibration/r12-prep-record.json": "d393cf27",
    "out/v3-tl2/calibration/round11-dev-record.json": "66e41bbf",
    "out/v3-tl2/calibration/r11-prep-record.json": "9074df2d",
    "out/v3-tl2/calibration/round10-dev-record.json": "da4e85f9",
    "out/v3-tl2/calibration/r10-prep-record.json": "3791edb1",
    "out/v3-tl2/calibration/round9-dev-record.json": "5ee18d61",
    "out/v3-tl2/calibration/r9-prep-record.json": "dd979632",
    "out/v3-tl2/calibration/round8-dev-record.json": "437e149c",
    "out/v3-tl2/calibration/r8-prep-record.json": "237920a5",
    "out/v3-tl2/calibration/r7-prep-record.json": "e48c37fe",
    "out/v3-tl2/calibration/render-framing-r14.json": "918672b4",
    "out/v3-tl2/calibration/render-framing-r14b.json": "7004b017",
    "out/v3-tl2/calibration/render-witness-r14b.json": "b63771f9",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r14.json": "eb8e3521",
    "out/v3-tl2/calibration/calibration-run-r13.json": "787c4589",
    "out/v3-tl2/calibration/calibration-run-r12.json": "2ec2fb04",
    "out/v3-tl2/calibration/calibration-run-r11.json": "ec05e472",
    "out/v3-tl2/calibration/calibration-run-r10.json": "622c9099",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
    "out/v3-tl2/holdout/HOLDOUT-PLAN.md": "a4b80193",
}
#: renders-r14b 四图字节复用（渲染零变更=r14 轮盲读同一批文件）
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
#: 六实例弃权率（盘面实测口径；本轮无零旗标实例、全部有定义）
EXPECT_RATES = {"top-i1": 0.909091, "top-i2": 0.8, "top-i3": 0.875,
                "bottom-i1": 0.75, "bottom-i2": 0.75, "bottom-i3": 1.0}
#: 主通道三分判据描述性边界锚（(iii) 基线=run-r14 双侧复算）
TOP_BASELINE_LIVE = "18/24"
BOTTOM_R13_BASELINE = "10/11"
#: 绿区语义化 §5A 显式援引摘录锚（2/3 实例；原始件 reading_notes）
GREEN_5A_ANCHORS = [
    ("applied-bottom-i2", "按指引 §5A 仪器注记理解为空隙着色、未作为图元判读"),
    ("prep1-bottom-i2", "其绿色分段环与 §5A 基准环缝描述相符"),
    ("prep1-bottom-i3", "§5A 亦注明绿色区域非图元"),
]
#: 黑点类判正常摘录锚（同现象跨实例处置分化；reading_notes 逐字）
BLACK_DOT_NORMAL_ANCHORS = [
    ("prep1-top-i1", "右上两黑色实心圆点判为基准点/连接器定位类正常特征"),
]


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s55():
    spec = importlib.util.spec_from_file_location(
        "s55_calibration_r15_compare",
        os.path.join(REPO, "scripts", "s55_calibration_r15_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _s56():
    spec = importlib.util.spec_from_file_location(
        "s56_calibration_r15_devrecord",
        os.path.join(REPO, "scripts", "s56_calibration_r15_devrecord.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r15.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round15-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _raw_text(key):
    return open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                             RAW_FILES[key]), encoding="utf-8").read()


def _raw_loc(key, flag_id):
    d = _load(RAW_FILES[key])
    for img in d["per_image"]:
        for f in img["flags"]:
            if f["flag_id"] == flag_id:
                return f["location_evidence"]
    raise AssertionError((key, flag_id))


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r15_files_valid_structure_and_prefixes():
    seen = {}
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == READER_IDS[key]
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key.rsplit("-", 1)[0]
        assert len(img["flags"]) == EXPECT_PART_COUNTS[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R15T-", "bottom": "R15B-"}[view]
        for f in img["flags"]:
            assert set(f) == READER_FLAG_KEYS           # 六键（含位置证据）
            assert f["flag_id"].startswith(prefix)      # 视图前缀一致
            assert f["category"] in critic.FLAG_CATEGORIES
            assert isinstance(f["abstain"], bool)
            assert 0.0 <= float(f["confidence"]) <= 1.0
            box = f["frame_box_pct"]
            assert len(box) == 4 and all(0.0 <= v <= 1.0 for v in box)
            assert box[0] < box[2] and box[1] < box[3]
            assert f["location_evidence"].strip()
        # r15 实测=两板各自从头编号（同实例 applied/prep1 各自 001 起编）
        state = STATE_OF_KEY[key]
        ids = sorted(f["flag_id"] for f in img["flags"])
        want = [prefix + "%03d" % i for i in range(1, len(ids) + 1)]
        assert ids == want, (key, ids)
        seen.setdefault(INSTANCE_OF_KEY[key], {})[state] = ids
        assert d["reading_notes"].strip()
    # 每实例两板均从 001 起编（与 r13/r14 跨板连续不同=实例输出行为差异）
    for inst, boards in seen.items():
        assert boards["applied"][0].endswith("001") and \
            boards["prep1"][0].endswith("001"), inst
        assert len(boards["applied"]) + len(boards["prep1"]) == \
            EXPECT_COUNTS[inst]
    # reroute 类旗标恰 4 条（2 非弃权边界报告+2 存在性弃权）
    reroute = sorted((INSTANCE_OF_KEY[key], f["flag_id"],
                      key.split("-", 1)[0], f["abstain"])
                     for key, name in RAW_FILES.items()
                     for f in _load(name)["per_image"][0]["flags"]
                     if f["category"] == "suspicious_reroute")
    assert reroute == EXPECT_R15_REROUTE
    # 合计 42 旗=6 非弃权+36 弃权（盘面口径与聚合一致）
    total = sum(EXPECT_COUNTS.values())
    abstain = sum(EXPECT_ABSTAIN.values())
    assert total == 42 and abstain == 36 and total - abstain == 6
    # 本轮无零旗标格（12 格全部≥1 旗）
    assert all(v >= 1 for v in EXPECT_PART_COUNTS.values())
    assert ZERO_FLAG_PARTS == []
    # §5A 显式援引摘录锚（2/3 实例；逐字 substring）+黑点类判正常摘录
    for key, excerpt in GREEN_5A_ANCHORS:
        assert excerpt in _raw_text(key), key
    for key, excerpt in BLACK_DOT_NORMAL_ANCHORS:
        assert excerpt in _raw_text(key), key


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s55 = _s55()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s55.RAW_FILES.items():
        parsed = s55.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s55.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则（作用于派发图像名，非盘上件键）
    assert s55.view_for_image("applied-top.png") == "top"
    assert s55.view_for_image("prep1-bottom.png") == "bottom"
    assert s55.view_for_image("applied-top.png") == s55.view_for_image(
        "applied-top.png")
    try:
        s55.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want == {("%s.png" % key.rsplit("-", 1)[0]):
                               VIEW_OF_KEY[key]}
        replay_ids = [f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]]
        inst = INSTANCE_OF_KEY[key]
        block = run["instances"][inst]["states"][STATE_OF_KEY[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == VIEW_OF_KEY[key]
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）
    # 旗标计数（按实例/板/视角/类别分层；总 42）
    fc = run["reader"]["flag_count"]
    assert fc["by_instance"] == EXPECT_COUNTS
    assert fc["abstain_by_instance"] == EXPECT_ABSTAIN
    assert fc["by_state"] == {"applied": 23, "prep1": 19}
    assert fc["by_view"] == {"top": 29, "bottom": 13}
    assert fc["abstain_by_view"] == {"top": 25, "bottom": 11}
    assert fc["by_category"] == {
        "silk_readability": {"total": 15, "non_abstain": 2, "abstain": 13},
        "courtyard_crowding": {"total": 6, "non_abstain": 0, "abstain": 6},
        "other_advisory": {"total": 11, "non_abstain": 0, "abstain": 11},
        "suspicious_reroute": {"total": 4, "non_abstain": 2, "abstain": 2},
        "placement_pattern_anomaly": {"total": 6, "non_abstain": 2,
                                      "abstain": 4},
    }
    assert fc["reroute_by_instance"] == {"top-i1": 2, "top-i2": 0,
                                         "top-i3": 2, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fc["reroute_class_production"] == 4
    assert fc["total"] == 42
    # 派发模式（12 派次=4 格×3 实例，两波次串行保序；v1.2 沿用条款）
    dm = run["reader"]["dispatch_mode"]
    assert dm["mode"] == "instance_serial_two_wave"
    assert dm["instances_per_cell"] == 3 and dm["dispatch_count_total"] == 12
    assert "同一实例先 applied 后 prep1" in dm["within_instance_serial_order"]
    assert "R15B-001..003" in dm["flag_id_continuity"]["bottom-i1"]
    assert "指引侧单变量" in dm["diff_note"] and "v1.2" in dm["diff_note"]
    assert "渲染零变更" in dm["diff_note"]
    assert "各自从头编号" in dm["flag_id_continuity_note"]
    assert "12 次盲读" in run["reader"]["dispatch_discipline"]
    assert "禁止交流" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r15.md" in \
        run["reader"]["dispatch_discipline"]
    assert "禁止对图像做任何程序化处理" in \
        run["reader"]["dispatch_discipline"]            # v1.2 沿用条款
    assert "零诊断报告内容" in run["reader"]["dispatch_discipline"]
    assert "§5A 仪器注记外零 legend" in run["reader"]["dispatch_discipline"]
    # 读者实例披露（R15：12/12 未读取盘上任何其他文件+措辞差异如实登记）
    note = run["reader"]["reader_instance_note"]
    assert "12/12" in note and "Read 工具" in note
    assert "未读取盘上任何其他文件" in note
    assert "措辞差异" in note and "如实登记" in note
    assert "非盲读违规" in note and "混杂因素照旧声明" in note
    assert "缩进格式冻结原始判读件" in note
    # 逐文件格式披露登记（编排侧落盘前处理；盘上件=冻结证据；12 件均
    # 零改动直读）
    fm = run["reader"]["parse"]
    for key in RAW_FILES:
        assert fm[key]["direct_json_parse"] is True, key
        assert fm[key]["repair"] == "no_repair", key
        assert "缩进格式冻结原始判读件" in fm[key][
            "raw_message_format_note"], key
    # 零旗标格（本轮无；item 5 口径保留备用）
    zp = run["reader"]["zero_flag_parts"]
    assert zp["parts"] == []
    assert "无零旗标格" in zp["note"] and "None" in zp["note"] \
        and "不编造数值" in zp["note"]


# ---------------------------------------------------------------------------
# run-r15：canonical、常量、域声明、单变更轮、受保护文件、courtyard
# ---------------------------------------------------------------------------

def test_run_r15_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r15"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == ROUND_LABEL
    assert rec["declared_date"] == DECLARED_DATE
    assert rec["metric_version"] == "calibration-metric-v3"
    assert rec["preregistration"]["round_id_constant"] == ROUND_ID
    for key in rec:                                     # 无机器时间戳键
        assert key in ("declared_date",) or (
            "time" not in key.lower() and "date" not in key.lower())
    # development 域声明（协议 v1 §1/§4：迭代轮不得冒充留出证据）
    assert rec["evaluation_domain"] == "development"
    note = rec["evaluation_domain_note"]
    assert note["declared"] == "development"
    assert note["in_calibrated_range"] is False
    assert "不得冒充未见留出" in note["basis_quote"]
    assert "第 15 轮" in note["basis_quote"]
    assert note["protocol_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/evaluation-protocol-v1.md")
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    # 单变更声明（指引侧单变量=§5A 仪器注记；渲染零变更；协议侧零新增）
    ic = rec["instrument_change"]
    assert ic["changed"] is False                       # 预注册零仪器变更
    assert ic["nature"].startswith("单变量指引侧变更轮")
    assert "§5A" in ic["nature"] and "渲染零变更" in ic["nature"]
    assert "instrument_change.changed=false" in ic["nature"]
    assert ic["note"] == "渲染与 r14 完全相同（字节复用），变化仅在指引文本"
    assert ic["components"] == []
    # changed_variables 登记与 r15-prep-record.json 一致（恰一项，锚
    # 4c6cd919；no_instrument_change=true 指本轮恰零仪器侧变更）
    prep = _load("r15-prep-record.json")
    assert prep["no_instrument_change"] is True
    assert prep["instrument_change"]["changed"] is False
    assert prep["read_prohibition_compliance"] is True
    assert prep["no_visual_reading"] is True
    assert [v["id"] for v in prep["changed_variables"]] == [
        "guidance-color-legend-instrument-note"]
    assert [v["id"] for v in ic["changed_variables_registered"]] == \
        [v["id"] for v in prep["changed_variables"]]
    reg = ic["changed_variables_registered"][0]
    assert reg["axis"] == "guidance" and reg["instrument_change"] is False
    assert "observation-guidance-r15.md" in reg["target"]
    # unchanged：渲染四图字节复用（witness 链）+判据文本零变更声明
    byt = [u for u in ic["unchanged_components"] if isinstance(u, dict)]
    assert len(byt) == 1 and byt[0]["byte_reuse"] is True
    for png in byt[0]["pngs"]:
        assert png["match"] is True
        assert _sha(png["path_rel"]) == png["sha256_measured"] == \
            png["sha256_witness_registered"]
    texts = "\n".join(u for u in ic["unchanged_components"]
                      if isinstance(u, str))
    assert "§4 全文" in texts and "反放宽条款" in texts
    assert "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由" \
        in texts
    assert "机械替换仅" in texts and "§2–§7 判据文本零变更" in texts
    pa = ic["protocol_amendment"]
    assert pa["amendment_version"] == "v1.1+v1.2 维持"
    assert "零变更" in pa["note"] or "零新增" in pa["note"]
    v1p = pa["v1_file_preserved"]
    assert v1p["zero_byte_preserved"] is True
    assert _sha(v1p["path_rel"]) == v1p["sha256_measured"]
    assert "恰一个指引侧操纵变量" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r15-prep-record.json")
    assert rec["protocol"]["amendment_version"].startswith("v1.1+v1.2")
    # 指引=r15 新落盘（d5babc93；由 r13 指引 c28806e1 机械变换生成）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r15.md")
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r13.md")
    assert "机械变换生成" in gp["change_note"]
    assert "落盘冻结" in gp["change_note"]
    assert "§2–§7 判据文本零变更" in gp["change_note"]
    # 同日只读 GT 审计引用（1f20554a；结论=GT 侧已全部关闭，本轮延续）
    ref = rec["gt_audit_reference"]
    assert ref["sha256"] == _sha("out/v3-tl2/calibration/gt-audit-r1.json")
    assert ref["sha256"].startswith("1f20554a")
    assert "bottom GT=无源已关闭" in ref["note"]
    assert "reroute GT=无源已关闭" in ref["note"]
    assert "L1NB 框径=合理维持现框" in ref["note"]
    assert "全部关闭" in ref["note"]                    # GT 侧候选关闭声明
    assert "应为空" in ref["note"]                      # bottom 零匹配结构性
    # 受保护三文件零改动（sha256 前 8）+ r15/r13 指引锚
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])
    for rel, want in GUIDANCE_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])
    # 三者并列声明（measurement_design item 4：不合并、不挑优）
    prn = rec["parallel_record_note"]
    assert "三者并列" in prn and "不挑优" in prn
    assert "aggregation_representative" in prn
    assert "metric_ranges_instance" in prn and "instances" in prn
    # measurement_design 五条预注册在 prep-record（先于盲读冻结）
    md = prep["measurement_design"]
    assert [it["item"] for it in md["items"]] == [1, 2, 3, 4, 5]
    assert "先于 R15 盲读冻结" in md["preregistration_declaration"]
    # pre_round_review 键（satisfied_by_prior_evidence：r14 拒绝支机制证据
    # 在案、无需新增视觉评审）
    prr = prep["pre_round_review"]
    assert prr["status"] == "satisfied_by_prior_evidence"
    assert "无需新增视觉评审" in prr["basis"]
    # courtyard 被动追踪键（run-record 链先例延续；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r15-prep-record.json")
    assert "零期望" in ct["declaration"] and "零阈值" in ct["declaration"]
    assert "零改动" in ct["threshold_note"]
    assert "r15-prep-record 无 secondary_observation 节" in \
        ct["note_source"]["note"]
    # bottom 观察（零 courtyard 旗+零匹配结构性+本轮无零旗标格）
    bz = ct["bottom_observation"]
    assert "13 旗" in bz["fact"] and "应为空" in bz["fact"]
    assert "courtyard 类旗标=0" in bz["fact"] and "无零旗标" in bz["fact"]
    for ev in bz["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz["evidence_check"]


def test_run_r15_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            block = rec["instances"][inst]["states"][st]
            rep = cal.compare_v3(block["reader_flags"], block["gt_entries"],
                                 flag_views=block["flag_views"])
            assert hashing.canonical_json_bytes(rep) == \
                hashing.canonical_json_bytes(block["compare_v3"])
            n_flags = len(block["reader_flags"])
            assert n_flags >= 1                          # 本轮无零旗标格
            assert block["view_check"] == rep["view_check"] == "full"
            r = block["compare_v3"]
            # 阈值常量零覆盖（与 r12 相同的声明常量）
            assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
            assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
            assert r["metric_version"] == "calibration-metric-v3"
            assert r["matches"] == []                    # R15 零匹配
            assert r["duplicate_reports"] == []
    # R15 零匹配（全部实例/全部态）：逐实例 matches_detail 复算为空
    for inst in INSTANCE_ORDER:
        assert rec["instances"][inst]["combined"]["matches_total"] == 0
        assert rec["instances"][inst]["combined"]["matches_detail"] == []
        assert rec["instances"][inst]["combined"]["gt_matched_union"] == 0
    # 全部实例/态 view_mismatch=0（top 旗与同态 GT 视角相符；bottom 无 GT）
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            r = rec["instances"][inst]["states"][st]["compare_v3"]
            assert r["view_mismatch"] == []
    # top 非弃权旗 4 条（i1 1 reroute+i2 2 silk+i3 1 reroute）；与同态 GT
    # 零 ≥0.5 containment 交叠（r14 的 R14T-002 几何门出局条目未再现）
    rows = [d for n in ("top-i1", "top-i2", "top-i3")
            for d in rec["instances"][n]["per_flag_gt_detail"]
            if not d["abstain"]]
    assert len(rows) == 4
    assert sorted((d["flag_id"], d["category"]) for d in rows) == [
        ("R15T-001", "silk_readability"),
        ("R15T-001", "suspicious_reroute"),
        ("R15T-003", "silk_readability"),
        ("R15T-005", "suspicious_reroute"),
    ]
    assert all(d["gt_overlaps"] == [] and d["containment_all_none"] is True
               and d["matched"] is False for d in rows)
    # bottom 非弃权旗 2 条（placement 类：i1 边缘节距空档+i2 板内孤立焊盘
    # 组；弃权出口不再垄断 bottom）；bottom-i3 仍全弃权（5 旗）
    brows = [d for n in ("bottom-i1", "bottom-i2", "bottom-i3")
             for d in rec["instances"][n]["per_flag_gt_detail"]
             if not d["abstain"]]
    assert len(brows) == 2
    assert all(d["category"] == "placement_pattern_anomaly" for d in brows)
    assert rec["instances"]["bottom-i3"]["combined"]["abstain_rate"] == 1.0
    assert rec["instances"]["bottom-i3"]["combined"]["flag_count"] == \
        rec["instances"]["bottom-i3"]["combined"]["abstain_count"] == 5


def test_run_r15_gt_entries_source_plus_reprojection():
    rec, _ = _run_record()
    sources = {"prep1": ("ground-truth-v1.json", GT_V1_IDS),
               "applied": ("ground-truth-v2.json", GT_V2_IDS)}
    for st, (gt_name, ids) in sources.items():
        gt = _load(gt_name)
        by_id = {e["gt_id"]: e for e in gt["gt_entries"]}
        block = rec["instances"]["top-i1"]["states"][st]
        assert [e["gt_id"] for e in block["gt_entries"]] == ids
        for e in block["gt_entries"]:
            src = by_id[e["gt_id"]]
            for k in src:                               # 除 frame_box_pct 外
                if k == "frame_box_pct":                # 逐字段原样
                    continue
                assert e[k] == src[k], (st, e["gt_id"], k)
    # frame_box_pct 恰为 derivation-log-r5 的 frame_box_pct_r5（按 gt_id；
    # top 渲染零变更=重投影输入未变，本轮零新派生、沿用 r5 台账）
    deriv = {e["gt_id"]: e["frame_box_pct_r5"]
             for e in _load("derivation-log-r5.json")["entries"]}
    for st in ("prep1", "applied"):
        assert "零新派生" in rec["instances"]["top-i1"]["states"][st][
            "gt_reprojection"]["note"]
        for e in rec["instances"]["top-i1"]["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0
            assert e["side"] == "top"                   # 13 条全部 top


# ---------------------------------------------------------------------------
# 实例聚合、视角层三分列、GT 匹配双口径（measurement_design items 1-3）
# ---------------------------------------------------------------------------

def test_run_r15_instance_view_layer_and_dual_gt_aggregation():
    rec, _ = _run_record()
    # item 1：实例主记录两板合计复算（abstain_rate 保留 6 位小数）
    for inst in INSTANCE_ORDER:
        c = rec["instances"][inst]["combined"]
        assert c["flag_count"] == EXPECT_COUNTS[inst]
        assert c["abstain_count"] == EXPECT_ABSTAIN[inst]
        assert c["abstain_rate"] == EXPECT_RATES[inst]
        assert c["abstain_rate"] == round(
            EXPECT_ABSTAIN[inst] / EXPECT_COUNTS[inst], 6)
        assert f"{EXPECT_ABSTAIN[inst]}/{EXPECT_COUNTS[inst]}" in \
            c["abstain_rate_arithmetic"]
        n_detail = sum(1 for d in rec["instances"][inst]["per_flag_gt_detail"]
                       if not d["abstain"])
        assert n_detail == EXPECT_COUNTS[inst] - EXPECT_ABSTAIN[inst]
        for d in rec["instances"][inst]["per_flag_gt_detail"]:
            for o in d["gt_overlaps"]:
                assert set(o) == {"gt_id", "gt_category", "containment",
                                  "area_ratio", "channel"}
    # item 2：视角层三分列（中位数+min+max，不取整）复算；本轮无 None
    vl = rec["view_layer"]
    for view, names in (("top", ("top-i1", "top-i2", "top-i3")),
                        ("bottom", ("bottom-i1", "bottom-i2",
                                    "bottom-i3"))):
        v = vl[view]
        assert v["instances"] == list(names)
        fc = [EXPECT_COUNTS[n] for n in names]
        ar = [EXPECT_RATES[n] for n in names]
        mt = [rec["instances"][n]["combined"]["matches_total"]
              for n in names]
        assert v["flag_count"]["median"] == sorted(fc)[1]
        assert (v["flag_count"]["min"], v["flag_count"]["max"]) == \
            (min(fc), max(fc))
        assert v["matches"]["median"] == sorted(mt)[1]
        assert (v["matches"]["min"], v["matches"]["max"]) == (min(mt),
                                                              max(mt))
        assert v["abstain_rate"]["median"] == sorted(ar)[1]
        assert (v["abstain_rate"]["min"], v["abstain_rate"]["max"]) == \
            (min(ar), max(ar))
        assert v["abstain_rate_range"] == round(max(ar) - min(ar), 6)
        assert "均有定义" in v["abstain_rate"]["median_note"]
    assert vl["top"]["abstain_rate_range"] == 0.109091
    assert vl["bottom"]["abstain_rate_range"] == 0.25
    assert vl["top"]["abstain_rate"]["median"] == 0.875
    assert vl["bottom"]["abstain_rate"]["median"] == 0.75
    assert "0.109091" in vl["top"]["abstain_rate_range_arithmetic"]
    assert "0.25" in vl["bottom"]["abstain_rate_range_arithmetic"]
    # item 3：GT 匹配双口径复算（union ≥1 / agreement ≥2/3；分母 13）
    dual = rec["gt_match_dual"]
    assert dual["denominator"] == 13
    per_gt = {g["gt_id"]: g for g in dual["per_gt"]}
    assert len(per_gt) == 13
    recount = {gid: 0 for gid in per_gt}
    for inst in INSTANCE_ORDER:
        for m in rec["instances"][inst]["combined"]["matches_detail"]:
            recount[m["gt_id"]] += 1
    for gid, g in per_gt.items():
        assert g["matched_by_count"] == recount[gid] == 0, gid
        assert g["hits"] == []
    assert dual["union"]["rule"] == "≥1 实例命中即计"
    assert dual["agreement"]["rule"] == "≥2/3 实例命中才计"
    assert dual["union"]["gt_ids"] == []
    assert dual["union"]["count"] == 0
    assert dual["union"]["gt_recall_union"] == 0.0
    assert dual["agreement"]["gt_ids"] == [] and \
        dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_recall_agreement"] == 0.0
    assert "应为空" in dual["denominator_note"]         # bottom 无 GT 在案


# ---------------------------------------------------------------------------
# 代表配置 joint + per-metric 范围（item 4；bottom 中位 tie 如实注明）
# ---------------------------------------------------------------------------

def _rep_state_report(rec, st):
    """代表配置合并态块 compare_v3 独立重算（测试内复算用）。"""
    rep = rec["representative_configuration"]["members"]
    flags, views = [], {}
    for inst in (rep["top"], rep["bottom"]):
        blk = rec["instances"][inst]["states"][st]
        flags.extend(blk["reader_flags"])
        views.update(blk["flag_views"])
    gt = rec["instances"]["top-i1"]["states"][st]["gt_entries"]
    return cal.compare_v3(flags, gt, flag_views=views)


def test_run_r15_representative_joint_and_metric_ranges():
    rec, _ = _run_record()
    rep = rec["representative_configuration"]
    # 代表配置选取复算：top 中位 10 唯一（top-i2）；bottom 中位 4 为 i1/i2
    # tie、按先序取 bottom-i1 并如实注明
    assert rep["rule"].startswith("measurement_design item 4")
    assert rep["members"] == {"top": "top-i2", "bottom": "bottom-i1"}
    sel = rep["selection"]
    assert sel["top"]["median_flag_count"] == 10
    assert sel["top"]["tie"] is False and "唯一" in sel["top"]["tie_note"]
    assert sel["top"]["flag_count_by_instance"] == {"top-i1": 11,
                                                    "top-i2": 10,
                                                    "top-i3": 8}
    assert sel["bottom"]["median_flag_count"] == 4
    assert sel["bottom"]["tie"] is True
    assert sel["bottom"]["selected"] == "bottom-i1"
    assert "tie" in sel["bottom"]["tie_note"] or "先序" in \
        sel["bottom"]["tie_note"]
    assert sel["bottom"]["flag_count_by_instance"] == {"bottom-i1": 4,
                                                       "bottom-i2": 4,
                                                       "bottom-i3": 5}
    # 代表配置合并态块 compare_v3 独立重算（由成员实例内嵌输入重建）
    agg = rec["aggregation_representative"]
    p = _rep_state_report(rec, "prep1")
    a = _rep_state_report(rec, "applied")
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    assert agg["flag_count_total"] == n_fl == 14       # 10（top-i2）+4
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 0
    assert agg["gt_matched_total"] == n_gm == 0
    assert agg["scored_total"] == n_sc == 3
    assert agg["abstain_count_total"] == n_ab == 11
    assert agg["gt_recall_total"] == round(0 / 13, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(0 / 3, 6) == 0.0
    assert agg["abstain_rate_total"] == round(11 / 14, 6) == 0.785714
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "11/14" in agg["abstain_rate_arithmetic"]
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert "代表配置" in agg["scope"] and "不挑优" in agg["scope"]
    # 两态弃权率分列（prep1 5/7、applied 6/7）
    assert agg["abstain_rate_by_state"]["prep1"] == round(5 / 7, 6)
    assert agg["abstain_rate_by_state"]["applied"] == round(6 / 7, 6)
    assert agg["abstain_rate_by_view"]["top"] == round(8 / 10, 6)
    assert agg["abstain_rate_by_view"]["bottom"] == round(3 / 4, 6)
    # APR-0011 达标评估逐项复算（阈值零改动；联合 not_met，三项未达线）
    comp = rec["compliance_representative"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    assert criteria["gt_count_ge_12"]["actual"] == 13
    assert criteria["gt_count_ge_12"]["met"] is True
    assert criteria["gt_recall_ge_0.75"]["actual"] == 0.0
    assert criteria["gt_recall_ge_0.75"]["met"] is False
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == 0.0
    assert criteria["seed_match_rate_ge_0.5"]["met"] is False
    assert criteria["abstain_rate_le_0.5"]["actual"] == 0.785714
    assert criteria["abstain_rate_le_0.5"]["met"] is False
    assert "阈值零改动" in criteria["abstain_rate_le_0.5"]["note"]
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    assert "互不凌驾" in criteria["abstain_rate_le_0.5"]["note"] and \
        "三分判据" in criteria["abstain_rate_le_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8", "r9", "r10", "r11",
                                     "r12", "r13", "r14", "r15"}
    assert consec["rounds"]["r14"] == "not_met（在案）"
    assert consec["rounds"]["r15"] == "not_met（本轮）"
    assert comp["joint_evaluation"] == "not_met"
    assert "代表配置" in comp["scope_note"] and "不挑优" in comp["scope_note"]
    # per-metric 实例间范围（item 4 三并列之二）复算
    mr = rec["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"min": 8, "max": 11}
    assert mr["top"]["abstain_rate"] == {"min": 0.8, "max": 0.909091}
    assert mr["top"]["abstain_count"] == {"min": 7, "max": 10}
    assert mr["top"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["top"]["scored"] == {"min": 1, "max": 2}
    assert mr["bottom"]["flag_count"] == {"min": 4, "max": 5}
    assert mr["bottom"]["abstain_rate"] == {"min": 0.75, "max": 1.0}
    assert mr["bottom"]["abstain_count"] == {"min": 3, "max": 5}
    assert mr["bottom"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["bottom"]["scored"] == {"min": 0, "max": 1}
    assert "note" not in mr["bottom"]["abstain_rate"]   # 本轮无 None 实例


# ---------------------------------------------------------------------------
# 预注册假设三分判据裁决（(i)(ii) 满足+(iii) 违约⇒字母=reject+机制观察）
# ---------------------------------------------------------------------------

def test_run_r15_hypothesis_reject_verdict_and_mechanism():
    rec, _ = _run_record()
    prep = _load("r15-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == \
        "r14-dev-record-candidate-0-guidance-color-legend"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r15-prep-record.json")
    # 判据引用=r15-prep-record.json adjudication 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    adj = prep["hypothesis_test"]["adjudication"]
    for k in ("supported_requires_all", "reject_if",
              "descriptive_boundary_note", "mechanism_observation_separate",
              "metric_lesson_separate"):
        assert quote[k] == adj[k], k
    assert quote["hypothesis"] == prep["hypothesis_test"]["hypothesis"]
    assert len(quote["supported_requires_all"]) == 3
    assert "bottom-i1/i2/i3 全为 0" in quote["supported_requires_all"][0]
    assert "≤ 10/11" in quote["supported_requires_all"][1]
    assert "run-r14 同口径" in quote["supported_requires_all"][2] and \
        "不手工赋值" in quote["supported_requires_all"][2]
    assert "(iii) 任一不满足" in quote["reject_if"]
    assert "请继续" in quote["user_directive_note"]
    # 主通道度量=prep-record 登记（三分判据）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    assert "10/11" in ht["primary_channel_metric"]
    # 描述性边界与门分列声明（非门阈值）
    assert "描述性边界" in ht["descriptive_boundary_note"] and \
        "门阈值零改动" in ht["descriptive_boundary_note"]
    # 主通道实测：(i) 0/0/0（零旗标路径）；(ii) 11/13≤10/11；
    # (iii) 25/29>18/24 违约
    m = ht["measurement"]
    assert m["crit1_bottom_courtyard_non_abstain_all_zero"] is True
    assert m["crit2_bottom_abstain_le_10_11"] is True
    assert m["crit3_top_abstain_le_r14_baseline"] is False
    assert m["bottom_courtyard_non_abstain_by_instance_r15"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert m["bottom_courtyard_flags_total_r15"] == 0
    assert m["bottom_abstain_count_r15"] == 11
    assert m["bottom_abstain_flags_r15"] == 13
    assert m["bottom_abstain_rate_r15"] == 0.846154
    assert "11/13" in m["bottom_abstain_rate_r15_arithmetic"] and \
        "10/11" in m["bottom_abstain_rate_r15_arithmetic"]
    assert m["top_abstain_count_r15"] == 25
    assert m["top_abstain_flags_r15"] == 29
    assert m["top_abstain_rate_r15"] == 0.862069
    assert "25/29" in m["top_abstain_rate_r15_arithmetic"]
    assert m["top_abstain_rate_r14_baseline_live"] == "18/24"
    assert m["top_abstain_rate_r14_baseline_value"] == 0.75
    assert m["reject_condition_met"] is True
    assert m["support_condition_met"] is False
    assert "第 (iii) 项" in m["reject_branch"] and "回退" in m["reject_branch"]
    assert "bottom 零旗标=False" in m["bottom_abstain_rate_r15_arithmetic"] \
        or "分母 13>0" in m["bottom_abstain_rate_r15_arithmetic"]
    # 基线交叉核对（r13 10/11、r13/r14 courtyard 0/0/0、r14 top 18/24）
    bc = m["baseline_cross_check"]
    assert bc["r13_bottom_abstain_aggregate_registered"] == \
        bc["r13_bottom_abstain_live"] == "10/11"
    assert bc["r13_courtyard_by_instance_registered"] == \
        bc["r13_courtyard_by_instance_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert bc["r14_courtyard_by_instance_registered"] == \
        bc["r14_courtyard_by_instance_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert bc["r14_top_abstain_aggregate_live"] == "18/24"
    assert "不手工抄数" in bc["note"] or "双侧复算" in bc["note"]
    # (i) 三实例逐例明细（零旗标路径；r14 courtyard 弃权现象未再现）
    assert len(m["bottom_courtyard_detail_r15"]) == 3
    assert all(d["courtyard_non_abstain_count"] == 0
               for d in m["bottom_courtyard_detail_r15"])
    assert all("零旗标路径" in d["note"]
               for d in m["bottom_courtyard_detail_r15"])
    # 守门通道：top 几何门 R14=1→R15=0 回落（独立单列；guard_ok=True；
    # r15 support 条件不含守门要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "R14=1→R15=0" in g["observation"]
    assert "R14T-002" in g["observation"] and \
        "GT-REVC-AP-7-C31U4" in g["observation"]
    assert "不构成 r15 字母裁决输入" in g["note"]
    # 全旗标合计附记（非主通道）如实
    assert "42" in m["r15_total_flags_note"] and "0.857143" in \
        m["r15_total_flags_note"] and "非主通道" in m["r15_total_flags_note"]
    # 字母裁决=reject（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "reject"
    assert adj["reject_if"] in ht["verdict_rule"]
    assert "(i)(ii)(iii) 全部满足" in ht["verdict_rule"]
    assert "reject" in ht["verdict_text"] and "唯一正式裁决" in ht[
        "verdict_text"]
    assert "第 (iii) 项" in ht["verdict_text"] and "25/29" in \
        ht["verdict_text"]
    assert "18/24" in ht["verdict_text"] and "0.75" in ht["verdict_text"]
    assert "0/0/0" in ht["verdict_text"] and "10/11" in ht["verdict_text"]
    assert "11/13" in ht["verdict_text"] and "0.846154" in ht["verdict_text"]
    assert "统计证明" in ht["verdict_text"] and "n=3" in ht["verdict_text"]
    assert "分列不合并" in ht["verdict_text"]
    assert "描述性边界" in ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）
    mo = ht["mechanism_observation"]
    assert "不凌驾" in mo["role"]
    # (a) 主通道三分判据分开实测（成因三分：判正常/全弃权/零旗标路径）
    mc = mo["main_channel_three_criteria"]
    assert "条件 (i)" in mc["observation"] and "条件 (ii)" in \
        mc["observation"] and "条件 (iii)" in mc["observation"]
    assert "零旗标路径" in mc["observation"]
    counts = mc["counts"]
    assert counts["r15_courtyard_by_instance"] == {"bottom-i1": 0,
                                                   "bottom-i2": 0,
                                                   "bottom-i3": 0}
    assert counts["r15_bottom_courtyard_flags_total"] == 0
    assert counts["bottom_abstain_r15"] == 11 and \
        counts["bottom_flags_r15"] == 13
    assert counts["bottom_abstain_rate_r15"] == 0.846154
    assert counts["bottom_abstain_rate_r14"] == 1.0
    assert counts["top_abstain_r15"] == 25 and counts["top_flags_r15"] == 29
    assert counts["top_abstain_rate_r15"] == 0.862069
    assert counts["top_abstain_rate_r14_baseline"] == 0.75
    # (b) bottom 零 courtyard 旗=分类通道转移（placement/other 构成）
    shift = mo["bottom_zero_courtyard_category_shift"]
    assert "courtyard" not in shift["bottom_flags_by_category_r15"]
    assert shift["bottom_flags_by_category_r15"] == {
        "other_advisory": {"abstain": 7, "non_abstain": 0, "total": 7},
        "placement_pattern_anomaly": {"abstain": 4, "non_abstain": 2,
                                      "total": 6},
    }
    assert "分类通道转移" in shift["observation"]
    assert "未再现" in shift["observation"]
    assert "r14 bottom=14 旗全弃权" in shift["r14_contrast"] and \
        "courtyard 0" in shift["r14_contrast"]
    assert "不凌驾字母裁决" in shift["status"] or "不凌驾" in shift["status"]
    # (c) 绿区语义化：三实例收敛空隙/翼瓣几何；2/3 实例显式援引 §5A
    gs = mo["green_semantics_by_instance"]
    gsm = gs["green_semantics_by_instance"]
    assert gsm["bottom-i1"]["§5A_cited"] is False
    assert gsm["bottom-i2"]["§5A_cited"] is True
    assert gsm["bottom-i3"]["§5A_cited"] is True
    assert "空隙" in gsm["bottom-i1"]["semantic_mode"] and \
        "翼瓣" in gsm["bottom-i1"]["semantic_mode"]
    assert "2/3 实例" in gs["observation"] and "§5A" in gs["observation"]
    assert "未再现" in gs["observation"]                # r14 分歧未再现
    assert "substring" in gs["evidence_check"]
    for ev in gs["evidence"]:
        src = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in src, ev["source"]
        if ev.get("second_excerpt"):
            assert ev["second_excerpt"] in src, ev["source"]
    # (d) 接触性判据延续：top courtyard 弃权 6 条中 5 条接触性+1 存在性
    cc = mo["contact_criterion_continuation"]
    assert cc["contact_flag_count"] == 5
    assert "5/6" in cc["status"] and "视觉贴近" in cc["observation"]
    assert "r13 8/8→r14 13/13→r15 5/6" in cc["status"]
    assert cc["top_abstain_rate_range"] == 0.109091
    assert cc["top_abstain_rates_by_instance"] == {
        "top-i1": 0.909091, "top-i2": 0.8, "top-i3": 0.875}
    assert "substring" in cc["contact_evidence_check"]
    assert len(cc["contact_evidence"]) == 5
    for ev in cc["contact_evidence"]:
        assert ev["excerpt"] in _raw_loc(ev["source"], ev["flag_id"]), \
            (ev["source"], ev["flag_id"])
    assert all(row["abstain"] is True and
               row["category"] == "courtyard_crowding"
               for row in cc["contact_flags"])
    assert "存在性出口" in cc["observation"]            # 第 6 条分列
    # (e) 黑点类追踪：7 旗全弃权+3 派次判正常（跨实例处置分化）
    bd = mo["black_dot_tracking"]
    assert bd["all_abstain"] is True
    assert sum(bd["by_instance"].values()) == 7
    assert bd["by_instance"] == {"bottom-i1": 1, "bottom-i2": 2,
                                 "bottom-i3": 3, "top-i1": 0, "top-i2": 1,
                                 "top-i3": 0}
    assert "7 条全部弃权" in bd["observation"]
    assert "3 判正常" in bd["observation"]
    assert "3 派次判正常" in bd["notes_normal_dispositions"]
    assert len(bd["black_dot_flags"]) == 7
    assert all(row["abstain"] is True for row in bd["black_dot_flags"])
    assert "处置实例分化" in bd["status"] or "不凌驾" in bd["status"]
    assert "substring" in bd["evidence_check"]
    for ev in bd["evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_loc(ev["source"], ev["flag_id"]))
        assert ev["excerpt"] in src, (ev["source"], ev.get("flag_id"))
    # (f) 残余实例差异（top 回升+bottom-i3 全弃权+同现象不同出口）
    rd = mo["residual_instance_differences"]
    assert "0.109091" in rd["observation"]
    assert "substring" in rd["evidence_check"]
    for ev in rd["evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_loc(ev["source"], ev["flag_id"]))
        assert ev["excerpt"] in src, ev.get("flag_id")
    assert "不凌驾" in rd["status"] or "不凌驾" in rd["observation"]
    # 度量教训延续：(iii) 对跨轮实例群漂移敏感（r10 教训新轴复现）
    ml = ht["metric_lesson_continuation"]
    assert "(iii) 支" in ml["lesson"] or "实例群漂移" in ml["lesson"]
    assert "reject" in ml["lesson"] and "r10" in ml["lesson"]
    assert "不追溯适用" in ml["role"]
    assert "不得回溯改判" in ml["status"]
    # reroute 类被动追踪（产量链回升 4；滥用型机械命中=1 但语义=正确排除）
    rc = ht["reroute_continuation_r15"]
    assert rc["reroute_total_r15"] == 4
    assert rc["reroute_by_instance_r15"] == {"top-i1": 2, "top-i2": 0,
                                             "top-i3": 2, "bottom-i1": 0,
                                             "bottom-i2": 0, "bottom-i3": 0}
    detail = sorted(rc["reroute_flag_detail_r15"],
                    key=lambda r: (r["instance"], r["flag_id"], r["state"]))
    assert [(r["instance"], r["flag_id"], r["state"], r["abstain"],
             r["detected_substring_hits"], r["adjudication"])
            for r in detail] == [
        ("top-i1", "R15T-002", "prep1", True, [], "abstain_existence"),
        ("top-i1", "R15T-005", "applied", False, [],
         "non_abstain_boundary_report"),
        ("top-i3", "R15T-001", "applied", False, ["蛇形"],
         "non_abstain_boundary_report_negation_citation"),
        ("top-i3", "R15T-004", "prep1", True, [], "abstain_existence"),
    ]
    for r in rc["reroute_flag_detail_r15"]:
        assert r["form_desc_excerpt"] in _raw_text(r["source"])
    assert "否定式援引" in rc["misuse_chain_note"] and \
        "机械命中与语义裁定如实分记" in rc["misuse_chain_note"]
    assert rc["production_chain"] == {"r8": 1, "r9": 0, "r10": 2, "r11": 3,
                                      "r12": 3, "r13": 2, "r14": 1,
                                      "r15": 4}
    assert "被动追踪" in rc["role"] or "非本轮预注册判据输入" in rc["role"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r14_range_live"] == 0.133333
    assert st_["top"]["r15_range"] == 0.109091
    assert st_["top"]["r15_by_instance"] == {"top-i1": 0.909091,
                                             "top-i2": 0.8,
                                             "top-i3": 0.875}
    assert st_["bottom"]["r14_range_live"] == 0.0
    assert st_["bottom"]["r15_range"] == 0.25
    assert st_["bottom"]["r15_by_instance"] == {"bottom-i1": 0.75,
                                                "bottom-i2": 0.75,
                                                "bottom-i3": 1.0}
    assert "混杂因素" in st_["confounder_note"] and "n=3" in \
        st_["confounder_note"]
    assert "不得凌驾字母裁决" in st_["precedence_note"]
    assert "已证因果关系" in st_["precedence_note"]
    # 跨轮聚合弃权率语境（口径分列如实）
    ac = m["aggregate_context"]
    assert ac["abstain_rate_r9"] == 0.727273
    assert ac["abstain_rate_r10"] == 0.285714
    assert ac["abstain_rate_r11_representative"] == 0.133333
    assert ac["abstain_rate_r12_representative"] == 0.9
    assert ac["abstain_rate_r13_representative"] == 0.909091
    assert ac["abstain_rate_r14_representative"] == 0.833333


# ---------------------------------------------------------------------------
# 通道归因（vs R14；重放可复核；链自 r6 衔接）+ courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r15_channel_attribution_and_courtyard_reproducible():
    s55 = _s55()
    rec, _ = _run_record()
    run13 = _load("calibration-run-r13.json")
    run14 = _load("calibration-run-r14.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r13/r14 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r13.json" in ca["method"][
        "source_of_r13_r14_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] is True
    # 重放复算（R13/R14/R15 均用内嵌输入）与登记一致 + 对拍 compare_v3
    pairs13 = ca["method"]["replay_cross_check"][
        "r13_candidate_pairs_by_instance_state"]
    pairs14 = ca["method"]["replay_cross_check"][
        "r14_candidate_pairs_by_instance_state"]
    assert set(pairs13) == {f"{n}/{st}" for n in INSTANCE_ORDER
                            for st in ("applied", "prep1")}
    assert set(pairs14) == set(pairs13)
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            for run_x, pairs in ((run13, pairs13), (run14, pairs14)):
                blk = run_x["instances"][name]["states"][st]
                rp = s55.channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        blk["gt_entries"])
                assert s55.replay_matches_agree(rp, blk["compare_v3"])
                assert pairs[f"{name}/{st}"] == [list(p) for p in
                                                 rp["candidate_pairs"]]
    # R13/R14 十二件重放候选对=空集（与在案一致）
    assert all(v == [] for v in pairs13.values())
    assert all(v == [] for v in pairs14.values())
    # R15 十二件重放对拍 compare_v3 全部一致（候选对=空集）
    pairs15 = ca["method"]["replay_cross_check"]["r15_candidate_pairs_by_part"]
    assert set(pairs15) == set(RAW_FILES)
    for key in RAW_FILES:
        blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
            STATE_OF_KEY[key]]
        rp = s55.channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
        assert pairs15[key] == [list(p) for p in rp["candidate_pairs"]]
        assert pairs15[key] == []                       # R15 零候选对
    # 通道分组条目（几何门 R14 1→R15 0 回落；类别门 R14 0→R15 0）
    rej14 = ca["channel_1_geometry_gate"]["r14_area_ratio_rejected_entries"]
    assert len(rej14) == 1 and rej14[0]["flag_id"] == "R14T-002" \
        and rej14[0]["gt_id"] == "GT-REVC-AP-7-C31U4"
    assert ca["channel_1_geometry_gate"]["r15_area_ratio_rejected_entries"] \
        == []
    assert "1→0" in ca["channel_1_geometry_gate"]["change"]
    cat15 = ca["channel_2_category_gate"]["r15_category_mismatch_entries"]
    assert cat15 == []
    assert "0→0" in ca["channel_2_category_gate"]["change"]
    # 视角门：三轮重放均空（bottom 无 GT；top 非弃权旗与同态 GT 视角相符）
    assert ca["view_gate_observations"]["r13_entries"] == []
    assert ca["view_gate_observations"]["r14_entries"] == []
    assert ca["view_gate_observations"]["r15_entries"] == []
    assert "应为空" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 …r14=1→r15=0；类别 …r14=0→r15=0）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0, "r11": 0, "r12": 0,
         "r13": 0, "r14": 1, "r15": 0}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0, "r11": 1, "r12": 0,
         "r13": 0, "r14": 0, "r15": 0}
    assert "通道级归因" in chain["scope"]
    # R15 特有观察：零 matches、top 构成、reroute 链
    spec = "\n".join(ca["r15_specific_observations"])
    assert "union=0/13" in spec or "matches=0" in spec
    assert "R14T-002" in spec and "r15" in spec.lower() or \
        "R15T" in spec
    assert "r14=1→r15=4" in spec or "r15=4" in spec
    # courtyard 被动追踪（run-record 链先例延续）：非弃权 0、弃权 6 全
    # top、命中 0
    ct = rec["courtyard_tracking"]
    na = ct["r15_courtyard_flags"]["non_abstain"]
    ab = ct["r15_courtyard_flags"]["abstain"]
    assert len(na) == 0 and len(ab) == 6
    assert ct["courtyard_matches_r15"] == 0
    assert all(r["view"] == "top" for r in ab)
    assert ct["courtyard_matches_r14"] == 0
    assert ct["courtyard_matches_r13"] == 0
    assert ct["courtyard_matches_r12"] == 0
    assert ct["courtyard_matches_r11"] == 3
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "零再现" in ct["same_domain_note"]
    # bottom 观察：零 courtyard 旗（r14 弃权 4 条未再现）+零匹配结构性
    bz = ct["bottom_observation"]
    assert "courtyard 类旗标=0" in bz["fact"] and "应为空" in bz["fact"]
    assert "无零旗标" in bz["fact"]
    for ev in bz["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw
    assert "pairing_caveat" in ca and "通道级" in ca["pairing_caveat"]
    # 主通道独立复算：bottom 三实例 courtyard 非弃权=0（逐实例重放；
    # 本轮成因=零旗标路径）
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        n_courtyard = 0
        for st in ("applied", "prep1"):
            b = rec["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            for f in b["reader_flags"]:
                if f["category"] == "courtyard_crowding":
                    n_courtyard += 1
                    if f["flag_id"] not in abst:
                        cnt += 1
        assert (cnt, n_courtyard) == (0, 0), name
    # 判据 (iii) 基线独立复算：top 全旗聚合 18/24=0.75（run-r14 内嵌输入）
    run14 = _load("calibration-run-r14.json")
    f14 = sum(run14["instances"][n]["combined"]["flag_count"]
              for n in ("top-i1", "top-i2", "top-i3"))
    a14 = sum(run14["instances"][n]["combined"]["abstain_count"]
              for n in ("top-i1", "top-i2", "top-i3"))
    assert (f14, a14) == (24, 18)


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖、指引文本锚
# ---------------------------------------------------------------------------

def test_run_r15_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r15_prep_record_preregistration",
            "r14_prep_record_prior_chain",
            "observation_guidance_r15_active",
            "observation_guidance_r13_lineage_base",
            "observation_guidance_r12_baseline",
            "observation_guidance_r9_chain", "observation_guidance_r8_chain",
            "render_framing_r14b_byte_reuse_provenance",
            "render_witness_r14b_byte_reuse_witness",
            "r14_dev_record_preregistration_source",
            "r13_dev_record_prior_chain", "r12_dev_record_prior_chain",
            "r13_prep_record_prior_chain", "r12_prep_record_witness_source",
            "r11_dev_record_witness_chain", "r11_prep_record_witness_chain",
            "r10_dev_record_witness_chain", "r10_prep_record_witness_chain",
            "r9_dev_record_witness_chain", "r9_prep_record_witness_chain",
            "r8_dev_record_witness_chain", "r8_prep_record_witness_chain",
            "r7_prep_record_witness_chain",
            "render_framing_r5_top_pixel_provenance",
            "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied", "gt_audit_r1_closed",
            "source_image_pdf_applied_top_r4",
            "source_image_pdf_applied_bottom_r4",
            "source_image_pdf_prep1_top_r4",
            "source_image_pdf_prep1_bottom_r4",
            "render_png_applied_top_r15_byte_reuse_r14b",
            "render_png_prep1_top_r15_byte_reuse_r14b",
            "render_png_applied_bottom_r15_byte_reuse_r14b",
            "render_png_prep1_bottom_r15_byte_reuse_r14b"} <= roles
    for key, blk in rec["reader"]["raw_files"].items():
        assert blk["sha256"] == _sha(blk["path_rel"])
        assert blk["sha256"].startswith(RAW_SHA256_FIRST8[key])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    # 预注册件哈希锚（先验给定的前 8；含 r14-dev→r15-prep→r15 指引链）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r12 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "零覆盖" in rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 命名固化入 naming_constraints（per r15-prep-record
    # protocol_amendment.naming：指引本体即为 r15 前缀，无需派发层覆盖）
    assert "R15T/R15B" in rec["naming_constraints"]
    assert "落盘固化" in rec["naming_constraints"] or "无需派发层覆盖" in \
        rec["naming_constraints"]
    assert "实例间编号独立" in rec["naming_constraints"]
    assert "各自从头编号" in rec["naming_constraints"]
    # 指引锚：本轮=r15 新落盘（d5babc93），机械变换基座=r13 指引
    # （c28806e1）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"].startswith("d5babc93")
    assert gp["baseline_ref"]["sha256"].startswith("c28806e1")
    # 指引内容锚：r15 指引（本轮唯一判读依据）§5A 节在位+§4 量化判据
    # substring 逐字保留+R13 前缀零残留+轮次常量
    g15 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                            "observation-guidance-r15.md"),
               encoding="utf-8").read()
    assert "## 5A. 渲染配色仪器注记" in g15          # §5A 节在位
    assert "仪器事实，非判据" in g15
    assert "255,165,0" in g15 and "0,128,0" in g15   # 橙/绿数值事实
    assert "接触性判据" in g15 and "至少出现 3 处" in g15 \
        and "三路出口" in g15 and "最小重复单元" in g15   # §4 量化判据
    assert "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由" \
        in g15                                        # 反放宽条款逐字
    assert "整段规则周期" in g15 and "示例 c" in g15   # §3A 收窄判据
    assert "2026-09-08-r15" in g15 and "R15T-001" in g15
    assert "R13T" not in g15 and "R13B" not in g15    # R13 前缀零残留
    # 基座 r13 指引零字节不动（R13 前缀在基座在案）
    g13 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                            "observation-guidance-r13.md"),
               encoding="utf-8").read()
    assert "R13T-001" in g13 and "2026-09-08-r13" in g13
    # 预注册链声明（r14-dev→用户批准→r15-prep→r15 指引先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "e6354d5c" in rec["preregistration"]["note"]
    assert "4c6cd919" in rec["preregistration"]["note"]
    assert "d5babc93" in rec["preregistration"]["note"]
    assert "请继续" in rec["preregistration"]["note"]
    assert "instrument_change.changed=false" in rec["preregistration"]["note"]
    assert "r15-prep-record.json" in rec["preregistration"]["note"]
    assert "measurement_design" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r14=上一轮基线；r15 前 run 不含本轮）
    ref14 = rec["reference_rounds"]["r14_run"]
    assert ref14["sha256"] == _sha(ref14["path_rel"])
    assert ref14["sha256"].startswith("eb8e3521")
    assert "r15_run" not in rec["reference_rounds"]
    # 渲染零变更实测：四 PNG=renders-r14b 原件逐字节（witness 登记值）
    import hashlib
    for name, want in R14B_PNG_SHA256.items():
        got = open(os.path.join(CAL_DIR, "renders-r14b", name),
                   "rb").read()
        assert hashlib.sha256(got).hexdigest() == want
    bot_a = open(os.path.join(CAL_DIR, "renders-r14b",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r14b",
                              "prep1-bottom.png"), "rb").read()
    assert bot_a == bot_p                              # 两板同图=仪器事实


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round15_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["is_gate"] is False
    # 本轮性质=单变量指引侧变更轮（§5A 仪器注记）+渲染零变更
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert "§5A" in dev["round_nature"] and "仪器注记" in dev["round_nature"]
    assert "渲染零变更" in dev["round_nature"]
    assert "d5babc93" in dev["round_nature"] and "c28806e1" in \
        dev["round_nature"]
    assert "机械变换生成" in dev["round_nature"]
    assert "changed=false" in dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert "第 15 轮" in dev["domain_basis_quote"]
    # 诊断结果与 run-r15 一致（代表配置口径：top-i2 唯一+bottom-i1 tie）
    run, _ = _run_record()
    assert "top-i2" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.785714
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is False
    # 假设裁决节与 run-r15 逐字一致（verdict=reject；三分判据分列）
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "reject"
    assert dev["hypothesis_test_i"]["measurement"][
        "crit3_top_abstain_le_r14_baseline"] is False
    assert dev["hypothesis_test_i"]["measurement"][
        "bottom_abstain_rate_r15"] == 0.846154
    assert dev["hypothesis_test_i"]["measurement"][
        "top_abstain_rate_r15"] == 0.862069
    assert dev["hypothesis_test_i"]["measurement"]["reject_condition_met"] \
        is True
    assert dev["hypothesis_test_i"]["measurement"]["support_condition_met"] \
        is False
    assert dev["hypothesis_test_i"]["measurement"]["guard_channel"][
        "guard_ok"] is True
    # 联合评价趋势：连续达标计数 0（R14 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "代表配置" in trend["aggregation_scope_note"]
    assert "0.857143" in trend["aggregation_scope_note"]  # 全旗标附记口径
    # r5→r15 逐轮走势表（数值取各轮 run-record；r11–r15 行=代表配置口径）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
         "r15"]
    by_r = {row["round"]: row for row in trend["by_round"]}
    assert by_r["r8"]["abstain_rate_total"] == 0.222222
    assert by_r["r8"]["matches_total"] == 1
    assert by_r["r10"]["abstain_rate_total"] == 0.285714
    assert by_r["r14"]["abstain_rate_total"] == 0.833333
    assert by_r["r14"]["flag_count_total"] == 12
    assert by_r["r14"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r15"]["abstain_rate_total"] == 0.785714
    assert by_r["r15"]["flag_count_total"] == 14
    assert by_r["r15"]["matches_total"] == 0
    assert by_r["r15"]["gt_recall_total"] == 0.0
    assert by_r["r15"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r15"]["round_id"] == ROUND_ID
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r15 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r15.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    assert dev["run_record_ref"]["sha256"].startswith("0c37c1cb")
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 旗标产量记账（42=6+36；实例/视角分列）
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 36 and fp["non_abstain_count"] == 6
    assert fp["abstain_rate_all_flags"] == 0.857143
    assert fp["abstain_rate_by_instance"] == EXPECT_RATES
    assert fp["abstain_rate_range_by_view"]["top"] == 0.109091
    assert fp["abstain_rate_range_by_view"]["bottom"] == 0.25
    assert "无零旗标" in fp["abstain_rate_range_by_view"]["note"]
    assert fp["flag_count_by_instance"] == EXPECT_COUNTS
    assert sum(fp["flag_count_by_file"].values()) == 42
    assert fp["reroute_by_instance"] == {"top-i1": 2, "top-i2": 0,
                                         "top-i3": 2, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fp["reroute_class_production"] == 4
    assert fp["parse_rejections"] == []
    assert fp["reader_ids"] == READER_IDS
    assert fp["raw_files"] == run["reader"]["raw_files"]
    assert "冻结证据" in fp["note"] and "12 派次" in fp["note"]
    assert "R15T/R15B" in fp["note"] and "落盘固化" in fp["note"]
    assert "各自从头编号" in fp["note"]
    # instrument_change 与 run 一致（changed=false 预注册）
    assert dev["instrument_change"] == run["instrument_change"]
    assert dev["instrument_change"]["changed"] is False
    # 诚实结论：字母裁决=reject；四条机制结论如实单列
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.785714" in hc and "development 域" in hc
    assert "0.0（0/13）" in hc and "union=0/13" in hc and "agreement=0/13" \
        in hc
    assert "reject" in hc and "唯一正式裁决" in hc
    assert "0/0/0" in hc and "10/11" in hc and "11/13" in hc
    assert "0.846154" in hc and "25/29" in hc and "0.862069" in hc
    assert "18/24" in hc and "第 (iii) 项" in hc
    assert "统计证明" in hc and "n=3" in hc
    assert "5/6" in hc and "接触性" in hc
    assert "黑点" in hc and "3 派次判正常" in hc
    assert "未穷尽" in hc
    assert "正确测出无效" in hc
    assert "无零旗标格" in hc and "不编造数值" in hc
    assert "12/12 派次" in hc and "措辞差异" in hc
    assert "机制结论如实单列" in hc
    assert "混杂" in hc
    assert "gt-audit-r1" in hc and "全部关闭" in hc
    assert "in_calibrated_range" in hc and "不得冒充留出" in hc
    assert "空隙/翼瓣几何" in hc                        # 机制结论 ①（图例生效）
    assert "2/3 实例" in hc and "§5A" in hc
    assert "未再现" in hc
    assert "跨轮实例群漂移敏感" in hc                   # 机制结论 ③（度量教训）
    assert "同指引重复轮消解" in hc
    assert "门在工作" in hc                             # 机制结论 ④
    # preregistration_chain 与 run-r15 冻结工件一致（逐件实测 sha）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert {k: v["path_rel"] for k, v in chain.items()} == \
        {i["role"]: i["path_rel"]
         for i in run["preregistration"]["frozen_artifacts"]}
    assert chain["r14_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round14-dev-record.json")
    assert chain["r15_prep_record_preregistration"]["sha256"].startswith(
        "4c6cd919")
    assert chain["observation_guidance_r15_active"]["sha256"].startswith(
        "d5babc93")
    assert chain["render_witness_r14b_byte_reuse_witness"][
        "sha256"].startswith("b63771f9")
    assert "e6354d5c" in dev["preregistration_chain_note"]
    assert "4c6cd919" in dev["preregistration_chain_note"]
    assert "d5babc93" in dev["preregistration_chain_note"]
    assert "c28806e1" in dev["preregistration_chain_note"]
    assert "0c37c1cb" in dev["preregistration_chain_note"]
    assert "请继续" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：R14 基线数值独立复算（bottom 14/14、
    top 18/24；run-r14 内嵌输入）；next_iteration_targets 覆盖 R16 同指
    引重复轮（判据 (iii) 实例群漂移消解）/绿区语义化维持观察/top 弃权
    构成细分/黑点类延续观察/留出集运行时机（须用户）/GT 关闭延续；
    不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r14"])
    # R14 基线独立复算（run-r14 内嵌输入）：bottom 14/14 全弃权、
    # top 18/24、courtyard bottom 4 条弃权
    run14 = _load("calibration-run-r14.json")
    fb = sum(run14["instances"][n]["combined"]["flag_count"]
             for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    ab = sum(run14["instances"][n]["combined"]["abstain_count"]
             for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (fb, ab) == (14, 14)                         # r14 bottom 全弃权
    ft = sum(run14["instances"][n]["combined"]["flag_count"]
             for n in ("top-i1", "top-i2", "top-i3"))
    at = sum(run14["instances"][n]["combined"]["abstain_count"]
             for n in ("top-i1", "top-i2", "top-i3"))
    assert (ft, at) == (24, 18)                         # r14 top 基线 18/24
    # R14→R15 分层/聚合数字在观察中如实引用
    for need in ("12→12", "38→42", "6/8/10→11/10/8", "4/3/7→4/4/5",
                 "32→36", "0.842105", "0.857143", "0/0/0", "14/14=1.0",
                 "11/13", "0.846154", "10/11", "25/29", "0.862069",
                 "18/24=0.75", "第 (iii) 项", "reject",
                 "0.833333/0.75/0.7", "0.909091/0.8/0.875",
                 "0.109091", "0.133333", "1.0/1.0/1.0", "0.75/0.75/1.0",
                 "0.25", "0.833333（10/12）", "0.785714（11/14）",
                 "0/13", "连续第四轮零匹配", "R14T-002",
                 "GT-REVC-AP-7-C31U4", "R11T-012", "几何门", "类别门",
                 "候选对=空集", "guard_ok=True", "分类通道转移",
                 "空隙/翼瓣", "§5A", "2/3 实例", "courtyard 类旗标 0",
                 "5 接触性+1 存在性", "黑点类 7 旗全弃权", "3 派次判正常",
                 "r8=1→r9=0→r10=1→r11=3→r12=0→r13=0→r14=0→r15=0",
                 "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4",
                 "否定式收窄判据", "未读取盘上任何其他文件", "措辞差异",
                 "各自从头编号", "gt-audit-r1", "pairing_caveat",
                 "不凌驾", "唯一正式裁决"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # R16 第一候选=同指引重复轮（实例群漂移消解；r10 先例）
    assert "同指引重复轮" in nxt and "R16 第一候选" in nxt
    assert "r10" in nxt and "实例群漂移" in nxt
    assert "≤0.75" in nxt and "≥0.862" in nxt
    assert "预注册" in nxt and "不得回溯改判" in nxt
    # 绿区语义化收敛维持观察（零期望）
    assert "绿区语义化收敛维持观察" in nxt and "零期望" in nxt
    assert "courtyard 矩形类图元化误读" in nxt and "如实记录" in nxt
    # top 弃权构成细分候选
    assert "top 弃权构成细分" in nxt and "接触性" in nxt and "丝印叠压" in nxt
    assert "存在性" in nxt and "预注册" in nxt
    # 黑点类一致弃权延续观察（14 旗→7 旗+3 派次判正常）
    assert "黑点类一致弃权延续观察" in nxt and "14 旗" in nxt and \
        "7 旗" in nxt and "3 派次判正常" in nxt
    # 留出集运行时机=开发线收敛判断（须用户；收敛未宣告、连续=0）
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    assert "留出集运行时机" in nxt and "须用户" in nxt
    assert "收敛未宣告" in nxt and "维持 0" in nxt
    assert "in_calibrated_range 恒 False" in nxt
    assert "人工批准" in nxt
    # GT 侧维持全关闭声明延续（matches=0 与 bottom GT 无源结构相容）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选全部关闭" in nxt
    assert "matches=0" in nxt and "结构相容" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r15-prep-record.json")
    assert dev["is_gate"] is False


def test_s56_rerun_idempotent_and_overwrite_guard():
    """s56 重跑语义：build_dev_record 同参重建 byte-exact 一致；防覆写
    护栏（字节等同→幂等跳过零覆写、不同→fail-closed）；s55 零
    dev-record 写入分包边界（round15-dev-record 不在 s55 写集）。"""
    s56 = _s56()
    dev, disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(s56.build_dev_record()) == disk
    # 声明常量（无 wall-clock）
    assert s56.DECLARED_DATE == "2026-09-08"
    assert s56.ROUND_ID == "2026-09-08-r15"
    assert s56.ROUND_LABEL == "r15"
    # 三分判据实测锚常量（操作化定义）
    assert (s56.EXPECT_TOP_ABSTAIN_R15, s56.EXPECT_TOP_FLAGS_R15) == (25, 29)
    assert s56.EXPECT_TOP_BASELINE_LIVE == "18/24"
    assert s56.EXPECT_TOP_BASELINE_VALUE == 0.75
    assert (s56.EXPECT_BOTTOM_ABSTAIN_R15,
            s56.EXPECT_BOTTOM_FLAGS_R15) == (11, 13)
    assert s56.EXPECT_COURTYARD_BASELINE == {"bottom-i1": 0, "bottom-i2": 0,
                                             "bottom-i3": 0}
    # 防覆写护栏纯函数语义
    assert s56.overwrite_guard(None, b"x") == "write"
    assert s56.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s56.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：round15-dev-record 已存在且字节等同 → main 正常完成
    # （零覆写）
    before = open(os.path.join(CAL_DIR, "round15-dev-record.json"),
                  "rb").read()
    s56.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "round15-dev-record.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    # 分包边界：s55 零 dev-record 写入（round15-dev-record 由 s56 落盘；
    # s55 无 dev-record 生成函数），幂等重跑后该件字节零改动
    s55 = _s55()
    assert not hasattr(s55, "build_dev_record")
    assert hasattr(s55, "build_run")                    # s55 只产 run-r15
    # run_record_ref 仍指向 run-r15 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r15.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "接触性判据" in rp["abstain_semantics"]
    assert "最小重复单元" in rp["abstain_semantics"]
    assert "反放宽条款" in rp["abstain_semantics"]
    assert "§5A" in rp["discipline"] and "零 legend" in rp["discipline"]
    assert "禁止交流" in rp["per_view_dispatch"] or "12 次盲读" in \
        rp["discipline"]
    assert "v1.2" in rp["discipline"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r15-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "11/10/8/4/4/5" in rec["deterministic_recompute_note"]
    assert "2026-09-08-r15" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 命名固化（指引本体即为 r15 前缀）如实入账
    assert "R15T/R15B" in rec["naming_constraints"]
    assert "无需派发层覆盖" in rec["naming_constraints"]
    prep = _load("r15-prep-record.json")
    assert "无需派发层覆盖" in prep["protocol_amendment"]["naming"] or \
        "指引本体即为 r15 前缀" in prep["protocol_amendment"]["naming"]
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写；reject≠统计
    # 证明；主通道判据与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-2]
    assert "reject 维持不变" in dev["notes"][-2]
    assert "分开表述" in dev["notes"][-2]
    assert "小样本方向性证据" in dev["notes"][-2]
    # 指引侧变更轮：无任何判据文本变更（§2–§7 逐字承 r13；§5A=仪器事实
    # 注记、非判据），不降低任何责任门槛
    assert "no_loosening_note" in prep
    assert "不触碰任何判据文本" in prep["no_loosening_note"]
    assert "责任门槛" in prep["no_loosening_note"]
    assert "放宽或收紧" in dev["notes"][1]
    # s55 脚本锚（R15 比对生成器冻结）+零阈值改动断言
    assert _sha("scripts/s55_calibration_r15_compare.py").startswith(
        S55_SHA256_FIRST8)
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；描述性边界
    # 与门分列
    assert rec["hypothesis_test"]["verdict"] == "reject"
    assert rec["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分列不合并" in rec["hypothesis_test"]["verdict_text"]
    assert rec["hypothesis_test"]["measurement"][
        "crit3_top_abstain_le_r14_baseline"] is False
    assert rec["hypothesis_test"]["measurement"]["guard_channel"][
        "guard_ok"] is True
    # 度量教训单列在 dev-record notes（(iii) 实例群漂移敏感；不追溯适用）
    assert "实例群漂移敏感" in dev["notes"][-1]
    assert "不追溯适用" in dev["notes"][-1]


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
