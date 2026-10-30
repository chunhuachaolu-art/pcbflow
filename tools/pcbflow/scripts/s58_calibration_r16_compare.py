#!/usr/bin/env python
"""CAL-R16-CLOSE：reader 判读迭代第十六轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s55_calibration_r15_compare.py 同构，仅输入与轮次
常量不同；R16=development 域同指引重复轮（零变更轮，r10 先例再现：
判读指引=observation-guidance-r15.md 字节复用（d5babc93 零字节不动、
本轮零新建指引文件）；渲染零变更=renders-r14b 四图字节复用（四 PNG
sha 与 r14/r15 轮盲读所用同一批文件逐一相等）；GT/阈值/协议零变更
（v1.1+v1.2 维持）；instrument_change.changed=false 已预注册）——
唯一操纵因子=reader 实例群重抽（12 派次全部重抽、与 r15 无实例身份
延续）；检验 r15 预注册候选假设（r15-dev-record-candidate-0-same-
guidance-repeat，判据=r16-prep-record.json hypothesis_test.adjudication
三分判据预注册原文，脚本从 prep-record 文件加载判据文本、两侧基线
数字 live 重放不手工抄数）：r15 (iii) 违约（top 25/29=0.862069>
run-r14 基线 18/24=0.75）的两候选解释消解——(α) 跨轮实例群漂移 vs
(β) §5A 全局弃权致敏：

  T1  解析 12 个 reader-raw-r16-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r16-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r15 同一比较脚本血统；聚合口径零改动）：
      (1) 实例主记录=六实例各自两板合计 flag_count/abstain_count/
      abstain_rate（6 位小数；零旗标分母=None）/非弃权清单（r16 实测
      flag_id 两板各自从头编号——非弃权/弃权清单按 (state, flag_id)
      限定，跨板重号如实登记；与 prep-record naming「同实例跨板连续」
      声明不同=读者实例输出行为差异、如实入账不作废，与 r15 实测同
      形态）/逐旗 containment+area_ratio 匹配明细；(2) 视角层=每视角
      3 实例 flag_count/abstain_rate/matches 各中位数+min+max 三分列
      不取整（本轮 12 格全部≥1 旗、弃权率全部有定义）；(3) GT 匹配
      双口径=union（≥1 实例命中）与 agreement（≥2/3）并列+逐 GT 条目
      matched_by_count（0..3；召回分母=GT 13 条）；(4) 联合门（APR-0011
      阈值零改动）=代表配置（每视角 flag_count 中位数实例）算一轮
      joint+per-metric 实例间范围+逐实例原始记录三者并列不挑优；(5)
      bottom 零旗标分母=按库侧 cal._ratio 先例 None+文字说明（本轮
      12 格全部≥1 旗、无 None 实例，口径保留备用）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且 top 渲染零
      变更（r16 top=renders-r14b 路径、字节内容=renders-r5、r14/r15
      已在案）故重投影输入未变；bottom 渲染字节复用 r14b 不触及 GT
      重投影——bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（三分判据，r16-prep-record.json hypothesis_test.
      adjudication 原文）逐支执行：top 全旗聚合弃权率归因裁决——
      supported=(a) top ≤0.75（run-r14 双侧复算基线，live 重放交叉
      核对一致）；reject=(b) top ≥0.862（run-r15 实测水平，live 重放
      交叉核对一致）；inconclusive=(c) 0.75<top<0.862（两值之间=
      两候选解释均不排斥、归因悬置）。letter 裁决唯一正式；机制观察
      单列：bottom 主通道维持性（side_observation_separate：bottom
      courtyard 类旗标数与非弃权计数对照 r15 零旗/0-0-0——r16 实测
      bottom courtyard 类 2 条全部弃权（applied-bottom-i2 黑点-轮廓
      近邻形态、r14 现象部分再现）、非弃权计数维持 0/0/0；bottom 全旗
      聚合弃权率对照 r15 的 11/13=0.846154（live 重放交叉核对一致）；
      黑点类旗标分布（12 旗全弃权、按实例 1/1/0/3/4/3，另 2 派次
      notes 判正常未报告）；绿区语义化方式延续（bottom 六派次全部以
      空隙/翼瓣语义化且全部显式提及 §5A 仪器注记、对照 r15 三派次
      援引）；top 弃权理由构成分型（27 条弃权旗逐旗分类：接触性 11+
      存在性 15+层归属其他 1——top 高弃权归因分解）。
      → calibration-run-r16.json。
  T3  development 域记录（R15→R16 方向性对照/假设裁决/联合评价趋势
      （r5→r16）/下一迭代目标）由后续 dev-record 包落盘（round16-dev-
      record，另包执行）；本包仅产出 run-r16、零 dev-record 写入。

通道归因纪律（vs R15；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/
s55 deviation_note 口径）：本轮对 R14/R15 均以内嵌输入（reader_flags/
gt_entries/flag_views，run sha 在案）+ compare_v3 同源几何原语
（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R16 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「未读取盘上任何其他文件」（12/12 在案；
prep1-bottom-i1 另自述「不掌握任何 GT 或期望信息」）；r16 notes 无
「未做任何裁剪/放大/像素分析」逐字语句（与 r14 措辞差异同 r15，如实
登记；工具轴=派发指令 v1.2 硬性条款照旧钉住）；跨轮实例全重抽+轮内
实例差异=混杂因素照旧声明——本轮实例群重抽恰是唯一操纵因子、裁决
变量。输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件
=缩进格式冻结原始判读件、本轮零改动直读（direct JSON 解析、12 件
parse 校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round16-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量 2026-09-08
/ 2026-09-08-r16）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s58_calibration_r16_compare.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"

DECLARED_DATE = "2026-09-08"
ROUND_ID = "2026-09-08-r16"
ROUND_LABEL = "r16"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_GUIDANCE_R12 = "out/v3-tl2/calibration/observation-guidance-r12.md"
REL_GUIDANCE_R13 = "out/v3-tl2/calibration/observation-guidance-r13.md"
REL_GUIDANCE_R15 = "out/v3-tl2/calibration/observation-guidance-r15.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
REL_PREP_R9 = "out/v3-tl2/calibration/r9-prep-record.json"
REL_PREP_R10 = "out/v3-tl2/calibration/r10-prep-record.json"
REL_PREP_R11 = "out/v3-tl2/calibration/r11-prep-record.json"
REL_PREP_R12 = "out/v3-tl2/calibration/r12-prep-record.json"
REL_PREP_R13 = "out/v3-tl2/calibration/r13-prep-record.json"
REL_PREP_R14 = "out/v3-tl2/calibration/r14-prep-record.json"
REL_PREP_R15 = "out/v3-tl2/calibration/r15-prep-record.json"
REL_PREP_R16 = "out/v3-tl2/calibration/r16-prep-record.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DEV_R10 = "out/v3-tl2/calibration/round10-dev-record.json"
REL_DEV_R11 = "out/v3-tl2/calibration/round11-dev-record.json"
REL_DEV_R12 = "out/v3-tl2/calibration/round12-dev-record.json"
REL_DEV_R13 = "out/v3-tl2/calibration/round13-dev-record.json"
REL_DEV_R14 = "out/v3-tl2/calibration/round14-dev-record.json"
REL_DEV_R15 = "out/v3-tl2/calibration/round15-dev-record.json"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_GT_AUDIT = "out/v3-tl2/calibration/gt-audit-r1.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_RUN_R6 = "out/v3-tl2/calibration/calibration-run-r6.json"
REL_RUN_R7 = "out/v3-tl2/calibration/calibration-run-r7.json"
REL_RUN_R8 = "out/v3-tl2/calibration/calibration-run-r8.json"
REL_RUN_R9 = "out/v3-tl2/calibration/calibration-run-r9.json"
REL_RUN_R10 = "out/v3-tl2/calibration/calibration-run-r10.json"
REL_RUN_R11 = "out/v3-tl2/calibration/calibration-run-r11.json"
REL_RUN_R12 = "out/v3-tl2/calibration/calibration-run-r12.json"
REL_RUN_R13 = "out/v3-tl2/calibration/calibration-run-r13.json"
REL_RUN_R14 = "out/v3-tl2/calibration/calibration-run-r14.json"
REL_RUN_R15 = "out/v3-tl2/calibration/calibration-run-r15.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_FRAMING_R14B = "out/v3-tl2/calibration/render-framing-r14b.json"
REL_WITNESS_R14B = "out/v3-tl2/calibration/render-witness-r14b.json"

#: 12 份盲读原始件（6 实例×2 板；r16 实测 flag_id 两板各自从头编号）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r16-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r16-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r16-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r16-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r16-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r16-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r16-prep1-bottom-i3.txt",
}

#: 六实例=本轮主记录单位（measurement_design item 1）；每实例=同视角
#: 两板（applied+prep1）两派次，实例间编号独立、同实例跨板连续
#: （protocol_amendment.blind_read_execution/naming）。
INSTANCES = {
    "top-i1": {"view": "top",
               "parts": ("applied-top-i1", "prep1-top-i1")},
    "top-i2": {"view": "top",
               "parts": ("applied-top-i2", "prep1-top-i2")},
    "top-i3": {"view": "top",
               "parts": ("applied-top-i3", "prep1-top-i3")},
    "bottom-i1": {"view": "bottom",
                  "parts": ("applied-bottom-i1", "prep1-bottom-i1")},
    "bottom-i2": {"view": "bottom",
                  "parts": ("applied-bottom-i2", "prep1-bottom-i2")},
    "bottom-i3": {"view": "bottom",
                  "parts": ("applied-bottom-i3", "prep1-bottom-i3")},
}
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

#: R15 渲染：图像来源=renders-r14b 四图字节复用（渲染零变更；四 PNG
#: 盘上 sha 与 r15-prep-record instrument_change 的 renders 登记值=
#: render-witness-r14b 登记值逐一相等，即 r14 轮盲读所用同一批文件；
#: 本轮唯一变量=指引侧 §5A 仪器注记）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r14b/applied-top.png",
    "applied-bottom":
        "out/v3-tl2/calibration/renders-r14b/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r14b/prep1-top.png",
    "prep1-bottom":
        "out/v3-tl2/calibration/renders-r14b/prep1-bottom.png",
}
#: 渲染的输入侧冻结矢量 PDF（r15-prep-record no_loosening_note：本轮
#: 渲染零变更=renders-r14b 四图字节复用、PDF 输入未变；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=renders-r14b 四图（r16 字节复用=与 s55 在案锚同一批文件）；
#: 四 PDF 锚=r5 在案锚沿用（输入侧 PDF 未变）；
#: guidance-r15 锚=r15-prep-record.json guidance_reuse.base_sha256
#: 全长（r16 同指引重复轮=字节复用、本轮唯一判读依据，零新建指引
#: 文件）、guidance-r13 锚=其机械变换基座（c28806e1）；
#: prep-r16 锚=任务给定先验（盘上实测一致）=round15-dev-record 锚
#: （本轮预注册授权链）=run-r15 锚（本轮 (b) 支基线与 bottom 侧观察
#: 基线双侧复算的输入，run sha 在案）；run-r14 锚=本轮 (a) 支基线
#: 双侧复算的输入；其余沿用 s55 在案锚。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R8:
        "aad43270b1c88d446511737416f3cc191e0f882a925e9e03ef3af1a5ef207993",
    REL_GUIDANCE_R9:
        "a0c10154c4a4c2c7721dbd0a5f12861885e20d09ca0e3d06edc54b1b64e848a8",
    REL_GUIDANCE_R12:
        "0ac22fcd046bf9c3997c84895d4388af0d0dbbfdefd424a8887787ae2be7ea67",
    REL_GUIDANCE_R13:
        "c28806e143d7598fc78f210fb4165d259ea26c3323dedfe30bc9eded784d2a0e",
    REL_GUIDANCE_R15:
        "d5babc9338e4d063652d5b217b85b1fb731ce53d76f16b2a5d79e8267c4ee267",
    REL_PREP_R7:
        "e48c37fee217f3745662875640c3bef4dea27906d76ee07f85ed981815a7b3f2",
    REL_PREP_R8:
        "237920a54fa28d3f37e7926e744b51bb7c29cd8f69797c626ad2c9c7d6b01efa",
    REL_PREP_R9:
        "dd979632cf5ec51c870a6ab23f9f86953f2e0ce473db5866b3bd851ed6626173",
    REL_PREP_R10:
        "3791edb10f2ab677d77b73feb3adf96177699c2903b5fc8b56186f8228509f72",
    REL_PREP_R11:
        "9074df2d9a91175981379c398982e082c72293677e07a848bc4da7c81f5359a0",
    REL_PREP_R12:
        "d393cf2722f797d3f43955cd58e8e1e39846ad31b66903c188ceedefb5f006de",
    REL_PREP_R13:
        "b1c0d8b5a38a832867f01aedec323a761846e577de25c1ea681e7064cead2f51",
    REL_PREP_R14:
        "93440a3d8d99c118ab41a0b3ed7f780a40c96524bb84f3618d883c292fbe246e",
    REL_PREP_R15:
        "4c6cd9190e8b39210ce16546708dc6f641d33d435b7281673effda75b29f172c",
    REL_PREP_R16:
        "46fbd15b3cd26b0f6396fde4eb67e0ea4750d0759dd31c7805a252fab6b28319",
    REL_DEV_R8:
        "437e149c3ae4d96653111be968f7d80d86ecbca7f6bb42a31f370ec5af78515d",
    REL_DEV_R9:
        "5ee18d61fc1464a92a6e9bbe46d269245748abb836bc07e535a42cff9aa57c43",
    REL_DEV_R10:
        "da4e85f97d216527aa5fd7027392d79d7935d5a79d200695c6b22510d65d628a",
    REL_DEV_R11:
        "66e41bbff7e20208525950c9af3f802e0ddde2746833f05d6bff23f26cf56389",
    REL_DEV_R12:
        "1411dab644e9a0fadc577bc19e8c7ced63f827463e49c9cb615405829855093b",
    REL_DEV_R13:
        "6b34c44218f9b925b825ea6d0fc6031bbe9fcaede6f5531d44d62402c841100a",
    REL_DEV_R14:
        "e6354d5c936a6c7ad8014ded90d1fb8742e1d1802c2f5dadf4e17b4795111afc",
    REL_DEV_R15:
        "e981897ccfa8873bb2bd65fb05a966813770c8b5fd4ffaef0bd4ad5cf501297d",
    REL_DERIV_R5:
        "623433801e8953587b60baff7827b859887ae218fad8100fb038382afa5b8663",
    REL_GT_V1:
        "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_GT_V2:
        "e1cb63d5e05761feada0b2dd030018bc04c3d3d165f33adcda2b9b348bd4b3a9",
    REL_GT_AUDIT:
        "1f20554a833d75cdbcf7df3c8212f39fd6b818bc25f47157325b44ab9804824b",
    REL_RUN_R3:
        "0b09012e01b2d9fbd0cf6afb0d71191c657746b078a0debb0703ed999af734cd",
    REL_RUN_R4:
        "0cf8bb3127f3d6b4cde2bd34abd5e9474294c14987116371d031d66da6dc8490",
    REL_RUN_R5:
        "2ed5a12867c203b6dce044944139fa255b0ebc86dac60719a50c7dd175ece0d6",
    REL_RUN_R6:
        "6e6ffdf77eacf92f9386e0ff8a281fe155fee9c5be5f487d83b0b96544f98251",
    REL_RUN_R7:
        "62b34b7129c69bc53dde8faf15d98927e946fc96fa446e43f859b4ef2e8e37be",
    REL_RUN_R8:
        "3c580eb34f1c39d5d6705b7b5303d016327fa049bdc1bc014ebe86214006fb4b",
    REL_RUN_R9:
        "e16420e5c8efc5759a4a48ceee954bb72da6064ad6b57d577de913300e683d05",
    REL_RUN_R10:
        "622c9099e83198ddb0110300ec6b9be612e21cc19cec7f285966807a6035ef85",
    REL_RUN_R11:
        "ec05e472f97f7cdbff37ea206282fb797a765b6d9f6985b25c5603b7a255d376",
    REL_RUN_R12:
        "2ec2fb048202516909138d5ad0346413254d3b8e75193379cd4d0a01a92af9d1",
    REL_RUN_R13:
        "787c4589e1f85d4cdefc62fb36ffacd62eff5b195eed62baee99388bf7241136",
    REL_RUN_R14:
        "eb8e352171f48d19ce7f5cd7fb843a2334f73cf06df50f6c004e1cff41587795",
    REL_RUN_R15:
        "0c37c1cb12a65fcd235ab91b5a85d865569fac0dc2235555d41378005fa6162f",
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    RAW_FILES["applied-top-i1"]:
        "9a202a6387fe99a661123d15d92e00c766f0182b24b880fedf75ef4a6c1cf9d8",
    RAW_FILES["prep1-top-i1"]:
        "5e500770f4567dd0055d808c5be2fdc5498653490e103ed909ea7623eb13c78d",
    RAW_FILES["applied-top-i2"]:
        "36b57ce2290c7ab92696da00d9fca7b4072f0fe93c62e163ca06a00d3836f9c7",
    RAW_FILES["prep1-top-i2"]:
        "a0212c717ae872087e64313e1b4ae49b5f69c7f308bdc0413cbd41d1bbb3f3d1",
    RAW_FILES["applied-top-i3"]:
        "e4e47dfe7ea95db297365e752549a67dff7fd118b9b496f25bd78ba60d1a2e54",
    RAW_FILES["prep1-top-i3"]:
        "5dc6a04032eefddff07eb3995478fbfbdce09846e5126b43a9cec22d965b8fad",
    RAW_FILES["applied-bottom-i1"]:
        "67119c5d2cf190085d976793b9febef297461ee781f6a13fe815c630ff6a6409",
    RAW_FILES["prep1-bottom-i1"]:
        "1e133ff45e8ade1888c2410746f048d6839a0521c8577b34da57badd73a30554",
    RAW_FILES["applied-bottom-i2"]:
        "534fc376ca90ab912e21e35a780cfc19972091590f4725bd5e0c26aac08702da",
    RAW_FILES["prep1-bottom-i2"]:
        "6a90d491b2a46d53adeb27374cf2c238269a45320c0566ac8aef1031a9147d93",
    RAW_FILES["applied-bottom-i3"]:
        "8f4d9d7510fa623d07132a2a6a71d51432d7f879cbcde393ff5126e77d1a93f3",
    RAW_FILES["prep1-bottom-i3"]:
        "0e729a852237bfc2738081fe7339446a9e7bced0619bc8506a7a3d1fcdd40bf8",
    PNG_FILES["applied-top"]:
        "298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5ca85e0f4f12a3cd0",
    PNG_FILES["applied-bottom"]:
        "d7284259c236ba3e2e7295f11fabc119ec37d347744439e608e35ee7574731a3",
    PNG_FILES["prep1-top"]:
        "b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca54c58f688d44f8",
    PNG_FILES["prep1-bottom"]:
        "d7284259c236ba3e2e7295f11fabc119ec37d347744439e608e35ee7574731a3",
    PDF_FILES["applied-top"]:
        "0028957c5ec9477d9dbde723c2dd6bfe93f58ec075c95caee86cb915c555667d",
    PDF_FILES["applied-bottom"]:
        "95dcdb59f9ef368a7a89665c964b43b7492ac11c48c2f98d9cc19efaab30a793",
    PDF_FILES["prep1-top"]:
        "770a50bb3089cdd48505ae320e7199a8f467bcc947c22d767c78a401d81dd35b",
    PDF_FILES["prep1-bottom"]:
        "6675458e1c7fa235c6f91c55e3a9bc5789d62126b2d9cca89f8e4512d001d47a",
}

#: 视角注入规则（确定性；读者产物无 side 字段，视角由图像名决定）。
VIEW_INJECTION_RULE = (
    "图像名 basename 确定性映射：*-top.png→top、*-bottom.png→bottom"
    "（盲读派发时每图独立给定，视角=图像名后缀；由编排侧注入 "
    "compare_v3 的 flag_views，reader 产物无 side 字段、不含视角信息）")

READER_KEYS = ("flag_id", "category", "confidence", "abstain",
               "frame_box_pct")

APPLIED_SHA_FROZEN = (
    "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85")
PREP1_SHA_FROZEN = (
    "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0bc5497fc5a62c7")

DISPATCH_DISCIPLINE = (
    "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
    "prep1-bottom）×每格 3 实例（i1/i2/i3）；两波次串行保序（同一实例"
    "先 applied 后 prep1）；每派次"
    "盲读词只含图像路径（renders-r14b 四张字节复用=r14/r15 轮盲读所用"
    "同一批文件、本轮渲染零变更）+observation-guidance-r15.md"
    "（d5babc93 字节复用、本轮零新建指引文件）路径+视角前缀与实例 "
    "reader_id（R16T/R16B 前缀由派发指令层覆盖——r15 指引 §6 示例前缀"
    "保持 R15T-/R15B- 落盘原文、字节复用不改，per r16-prep-record "
    "protocol_amendment.naming；reader-r16-{top,bottom}-i{1,2,3} 为派发"
    "指令命名）+起始序号+v1.2 工具行为规约"
    "硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/衍生图像"
    "生成等）；判读只允许以 Read 工具查看原图（同一原图可重复查看））；"
    "无任何 GT 坐标/类别提示/期望缺陷描述、零诊断报告内容（渲染探针链与 "
    "framing/witness 记录不进任何 reader 上下文）、零 legend/零其他解释"
    "（同指引重复轮=判读输入与 r15 完全同构，仅 reader 实例群重抽）；"
    "读图者不接触 GT/派生台账/任何校准"
    "产物路径；跨实例/跨视角禁止交流（12 次盲读相互独立——独立性是"
    "多实例协议的前提，亦为实例群重抽归因的前提，per r16-prep-record "
    "read_prohibition_note）")

#: 派发模式结构化记录（R16=同指引重复轮：每格 3 实例、两波次串行
#: 保序；派发结构与 r15 同构，协议侧零新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R16T-001..003；prep1 R16T-001..006",
        "top-i2": "applied R16T-001..003；prep1 R16T-001..011",
        "top-i3": "applied R16T-001..005；prep1 R16T-001..007",
        "bottom-i1": "applied R16B-001..002；prep1 R16B-001..003",
        "bottom-i2": "applied R16B-001..002；prep1 R16B-001..003",
        "bottom-i3": "applied R16B-001..003；prep1 R16B-001",
    },
    "flag_id_continuity_note": (
        "r16 实测=flag_id 两板各自从头编号（同一实例 applied 与 prep1 "
        "派次内各自独立起编；跨板同号如实登记）——与 r15 实测同形态；"
        "与 r16-prep-record protocol_amendment.naming「同实例跨板连续」"
        "的声明不同，属读者实例输出行为差异、如实入账不作废（非盲读"
        "违规、不作废任何产物）；编排"
        "侧因此把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R15→R16 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮零变更="
                  "指引侧字节复用（observation-guidance-r15.md 零字节"
                  "不动）+渲染零变更（renders-r14b 四图字节复用）；唯一"
                  "操纵因子=reader 实例群重抽（12 派次全部重抽）；协议"
                  "侧零新增条款"
                  "（v1.2 沿用：派发指令继续含纯 Read 直读硬性条款，"
                  "12/12 派次自述「未读取盘上任何其他文件」，见 "
                  "reader_instance_note；指引 §2–§7 实质判据通道零变更；"
                  "GT/阈值零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R16 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何其他文件」"
    "（12/12 逐字摘录在案 reader_tool_evidence；prep1-bottom-i1 另自述"
    "「不掌握任何 GT 或期望信息」；prep1-top-i2 自述「做两遍独立判读」、"
    "多个派次自述「逐区域独立判读」=实例自述措辞异质性如实登记）；"
    "r16 notes 无「未做任何裁剪/放大/像素分析"
    "等程序化处理」逐字语句——与 r14/r15 同为自述措辞"
    "差异、如实登记（工具行为轴=派发指令 v1.2 硬性条款照旧钉住，"
    "r10/r11 实测 8/12 派次自选 PIL 局部裁剪放大的自选异质性自 r12 "
    "规约生效起持续为零）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/零 "
    "legend/零其他文件接触=非盲读违规；本轮实例群全部重抽（与 r15 无"
    "实例身份延续）=唯一操纵因子；跨轮实例不同+"
    "轮内实例差异=混杂因素照旧声明（本轮每视角 n=3 给出轮内实例间范围，"
    "轮内样本仍小、development 域只描述不断言）。输出格式实例披露（编排"
    "侧落盘前处理，盘上件=冻结证据）：12 件=缩进格式冻结原始判读件、"
    "本轮零改动直读（direct JSON 解析；围栏剥离本先例不适用——12 件"
    "均为裸 JSON 文本；12 件 parse 校验全部通过、均非盲读违规）")

#: 逐文件原始消息格式（如实入账；盘上件=冻结原始判读件，本轮零改动
#: 直读，parse 均为 direct JSON 解析、零 repair）。
_RAW_FORMAT_NOTE = ("盘上件=缩进格式冻结原始判读件，本轮零改动直读"
                    "（direct JSON 解析通过；非盲读违规）")
RAW_MESSAGE_FORMAT_NOTES = {
    "applied-top-i1": _RAW_FORMAT_NOTE,
    "applied-top-i2": _RAW_FORMAT_NOTE,
    "applied-top-i3": _RAW_FORMAT_NOTE,
    "applied-bottom-i1": _RAW_FORMAT_NOTE,
    "applied-bottom-i2": _RAW_FORMAT_NOTE,
    "applied-bottom-i3": _RAW_FORMAT_NOTE,
    "prep1-top-i1": _RAW_FORMAT_NOTE,
    "prep1-top-i2": _RAW_FORMAT_NOTE,
    "prep1-top-i3": _RAW_FORMAT_NOTE,
    "prep1-bottom-i1": _RAW_FORMAT_NOTE,
    "prep1-bottom-i2": _RAW_FORMAT_NOTE,
    "prep1-bottom-i3": _RAW_FORMAT_NOTE,
}

GUIDANCE_NOTE = (
    "本轮指引=observation-guidance-r15.md 字节复用（d5babc93，r15 轮"
    "落盘冻结、本轮零字节不动、零新建指引文件，per r16-prep-record "
    "guidance_reuse：mode=byte_reuse_zero_change、edit_list=[]、"
    "zero_write_declaration 在案）：该文件由 r13 指引（observation-"
    "guidance-r13.md，c28806e1，指引作者唯一事实源）机械变换生成；"
    "§2–§7 判据文本与 §5A 渲染配色仪器注记随本体原样生效（字节复用="
    "零措辞调整空间）；§6 示例旗 ID 前缀保持 R15T-/R15B-（r15 落盘"
    "原文），R16 派次 flag_id 前缀 R16T/R16B 由派发指令层覆盖（与 "
    "r13→r15「随指引落盘固化」路径不同，per r16-prep-record "
    "protocol_amendment.naming）；§5A=仪器事实注记、非判据——不构成任何"
    "「应判正常/无需报告」的指示，不降低任何存在性、归类、定位或报告"
    "的责任门槛（per r16-prep-record no_loosening_note；反放宽条款与"
    "三路出口随指引本体原样生效）——同指引重复轮、判断责任标准一字未松")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 16 轮迭代"
    "（development 域同指引重复轮（零变更轮：唯一操纵因子=reader 实例"
    "群重抽）：迭代轮不得"
    "冒充留出证据）。")

INSTRUMENT_NATURE = (
    "同指引重复轮（零变更轮，r10 先例再现）：判读指引=observation-"
    "guidance-r15.md 字节复用（d5babc93 实测锚、零新建指引文件）"
    "+渲染零变更（renders-r14b 四图字节复用=r14/r15 轮盲读所用同一批"
    "文件，四 PNG 盘上 sha 与 witness 登记值逐一相等）+GT/阈值零变更"
    "（instrument_change.changed=false 已预注册）+协议零变更（v1.1+"
    "v1.2 维持）：仪器与判读语义通道零变更，唯一操纵因子=reader 实例"
    "群重抽（12 派次全部重抽，per r16-prep-record "
    "manipulated_factor=「reader 实例群（12 派次全部重抽）」；"
    "changed_variables=[]）")

#: 预注册主通道三分判据所用基线（零覆盖；per r16-prep-record
#: hypothesis_test.adjudication 原文：letter_supported=(a) top ≤0.75
#: （=run-r14 双侧复算基线，冻结值）、letter_reject=(b) top ≥0.862
#: （=r15 实测水平，冻结值）、letter_inconclusive=(c) 0.75<top<0.862）。
#: 两侧基线数字均 live 重放（同一聚合逻辑对 run-r14/run-r15 内嵌实例
#: 记录双侧复算、不手工抄数）并与下列在案登记值交叉核对（fail-closed，
#: 不符即中止）：(18,24)=0.75、(25,29)=0.862069（r16-prep-record
#: chain_anchors.run_r15_criterion_anchor.frozen_values 在案锚）。
BASE14_TOP_AGGREGATE_REGISTERED = {"abstain": 18, "flags": 24}
BASE15_TOP_AGGREGATE_REGISTERED = {"abstain": 25, "flags": 29}
#: bottom 侧观察基线（per r16-prep-record side_observation：对照 r15
#: 的 11/13=0.846 与 0/0/0；live 重放交叉核对）。
BASE15_BOTTOM_AGGREGATE_REGISTERED = {"abstain": 11, "flags": 13}
R15_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}

#: bottom 主通道维持性侧观察逐实例登记表（bottom courtyard 类非弃权
#: 旗；程序实测与登记一致性 fail-closed：实测值须与本表 expected 逐一
#: 相等；per r16-prep-record side_observation「对照 r15 的…0/0/0」；
#: side_observation_separate=单列、不影响字母）。
SIDE_OBS_REGISTERED = [
    {"instance": "bottom-i1", "expected": 0,
     "note": ("r15 零旗→r16 实测 0：本轮 bottom-i1 零 courtyard 类"
              "旗标（5 旗=placement_pattern_anomaly 1+other_advisory 4，"
              "全部弃权）——非弃权 courtyard=0 系零旗标路径所致")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r15 零旗→r16 实测 0：本轮 bottom-i2 有 courtyard 类"
              "旗标 2 条（applied R16B-001/R16B-002，黑点-椭圆 courtyard "
              "轮廓相切/近邻形态、r14「黑点骑跨轮廓」现象部分再现），"
              "全部弃权——非弃权 courtyard=0 由全弃权路径维持（与 "
              "r15 零旗标路径成因不同，如实分列）")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r15 零旗→r16 实测 0：本轮 bottom-i3 零 courtyard 类"
              "旗标（4 旗=other_advisory 3+非弃权 other_advisory 1）"
              "——零旗标路径")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。r16 自述措辞异质性（「做两遍独立判读」
#: 「逐区域独立判读」等）如实登记，见 READER_INSTANCE_NOTE。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据给定 PNG（applied-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据给定 prep1-top.png 的可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i2",
     "excerpt": "仅依据给定 PNG 可见内容做两遍独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i2",
     "excerpt": "仅依据给定PNG可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据给定 applied-top.png 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据给定 PNG 可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG（applied-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG（prep1-bottom.png）的可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据给定 PNG（prep1-bottom.png，bottom 视）可见内容独立判读，未读取盘上任何其他文件"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 六派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——绿色翼瓣/
#: 空隙形态在 r15 指引字节复用下延续 §4(i) 判读路径的机制观察证据
#: （6/6 bottom 派次、判据轴延续）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "形态沿阵列系统性一致，判为正常设计特征不报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "按§4(i)量化判据（最小重复单元大量出现、沿同一阵列对齐、跨至少2条边、各处形态一致）判为系统性正常设计特征"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "按 §4(i) 量化判据核为系统性重复"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "满足 §4(i) 量化系统性判据，判为正常设计特征未报告"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "最小重复单元形态一致（≥3处、多阵列、样式一致），按§4(i)判为正常设计特征"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "按 §4(i) 判为正常设计特征不报告"},
]

#: top 弃权理由构成分型（机制观察 (d)：27 条 top 弃权旗逐旗按
#: location_evidence 关键词分类——contact=接触性「真实接触 vs 视觉
#: 贴近不可分辨/是否接触不可确认」；existence=存在性「性质不明/是否
#: 存在不可确认」；other_layer=层归属等其他出口；为 top 高弃权归因
#: 提供分解。逐旗 excerpt 逐字 substring fail-closed 校验）。
TOP_ABSTAIN_TYPOLOGY = [
    {"source": "applied-top-i1", "flag_id": "R16T-001", "type": "contact",
     "excerpt": "当前分辨率下无法区分真实接触/重叠与视觉贴近"},
    {"source": "applied-top-i1", "flag_id": "R16T-002", "type": "existence",
     "excerpt": "无法确认是真实叠印/遮挡还是仅字号过小导致的渲染模糊"},
    {"source": "applied-top-i1", "flag_id": "R16T-003", "type": "existence",
     "excerpt": "无法负责任判断其为常规标记形态（如极性半圆标记类）还是图形偏移/错位类异常"},
    {"source": "prep1-top-i1", "flag_id": "R16T-002", "type": "contact",
     "excerpt": "当前分辨率下无法分辨是真实接触还是视觉贴近，按接触性判据作存在性弃权"},
    {"source": "prep1-top-i1", "flag_id": "R16T-003", "type": "existence",
     "excerpt": "无法负责任地判定为正常设计特征（如基准点/安装孔）或关注现象"},
    {"source": "prep1-top-i1", "flag_id": "R16T-004", "type": "existence",
     "excerpt": "无法确认它是真实的可疑绕行还是普通弯折/过孔"},
    {"source": "applied-top-i2", "flag_id": "R16T-002", "type": "existence",
     "excerpt": "无法确认其为关注现象还是安装孔/基准点类常规设计特征"},
    {"source": "applied-top-i2", "flag_id": "R16T-003", "type": "existence",
     "excerpt": "当前分辨率无法确认叠压是否真实存在"},
    {"source": "prep1-top-i2", "flag_id": "R16T-001", "type": "contact",
     "excerpt": "当前分辨率下无法区分真实接触与视觉贴近，接触与否按存在性不确定弃权"},
    {"source": "prep1-top-i2", "flag_id": "R16T-002", "type": "contact",
     "excerpt": "无法在该分辨率下确认是否接触或交叠"},
    {"source": "prep1-top-i2", "flag_id": "R16T-003", "type": "contact",
     "excerpt": "无法负责任区分接触与贴近"},
    {"source": "prep1-top-i2", "flag_id": "R16T-004", "type": "contact",
     "excerpt": "无法确认是否达到接触/交叠，存在性不确定故弃权"},
    {"source": "prep1-top-i2", "flag_id": "R16T-005", "type": "contact",
     "excerpt": "极近相邻，且该大圆形属courtyard层还是丝印轮廓亦无法确认",
     "note": "接触性主出口+层归属附记（混合型，按主出口计入 contact）"},
    {"source": "prep1-top-i2", "flag_id": "R16T-006", "type": "contact",
     "excerpt": "当前分辨率无法区分接触与视觉贴近"},
    {"source": "prep1-top-i2", "flag_id": "R16T-007", "type": "contact",
     "excerpt": "是否接触无法负责任判断"},
    {"source": "prep1-top-i2", "flag_id": "R16T-008", "type": "existence",
     "excerpt": "无法确认文字是否真的无法逐字辨读"},
    {"source": "prep1-top-i2", "flag_id": "R16T-009", "type": "existence",
     "excerpt": "笔画级遮挡无法在该分辨率下确认"},
    {"source": "prep1-top-i2", "flag_id": "R16T-010", "type": "existence",
     "excerpt": "其设计含义（极性标记/标识类常规图形还是异常图形块）无法负责任判断"},
    {"source": "prep1-top-i2", "flag_id": "R16T-011", "type": "contact",
     "excerpt": "是否达到接触/交叠无法在当前分辨率负责任判断"},
    {"source": "applied-top-i3", "flag_id": "R16T-003", "type": "existence",
     "excerpt": "无法负责任确认文字是否真正叠压至不可辨读"},
    {"source": "applied-top-i3", "flag_id": "R16T-004", "type": "contact",
     "excerpt": "按接触性判据当前分辨率无法区分真实交叠/接触与视觉贴近"},
    {"source": "applied-top-i3", "flag_id": "R16T-005", "type": "existence",
     "excerpt": "无法负责任区分其是否横越焊盘铜箔还是仅从两排交错焊盘的间隙中穿过"},
    {"source": "prep1-top-i3", "flag_id": "R16T-003", "type": "existence",
     "excerpt": "无法排除其为第三个微小元件的焊盘或渲染粘连"},
    {"source": "prep1-top-i3", "flag_id": "R16T-004", "type": "existence",
     "excerpt": "无法端到端追踪确认其为真实的多余绕行还是相邻走线并行弯曲"},
    {"source": "prep1-top-i3", "flag_id": "R16T-005", "type": "other_layer",
     "excerpt": "无法确认两线各属丝印外形还是 courtyard 轮廓层",
     "note": ("层归属/构成不明出口（该旗 location_evidence 同时明写"
              "「可分辨为未接触」——非接触性主出口，计入 other_layer）")},
    {"source": "prep1-top-i3", "flag_id": "R16T-006", "type": "existence",
     "excerpt": "无法区分斜置元件与斜向走线段或焊盘桥接"},
    {"source": "prep1-top-i3", "flag_id": "R16T-007", "type": "existence",
     "excerpt": "无法确认是否真实重叠致辨读受阻"},
]

#: 绿色区域语义化方式证据（r16-prep-record side_observation 预注册：
#: 黑点类与绿区语义化方式延续观察；bottom 六派次 reading_notes 逐字
#: 摘录；substring fail-closed 校验；对照 r15 三实例「空隙/翼瓣」
#: 几何收敛+3 派次 §5A 援引——r16 六派次全部空隙语义化且全部显式
#: 提及 §5A 仪器注记（其中多派次明写「仅作仪器事实、未作为判据」））。
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "按 §5A 仪器注记，绿色区域为板内空隙白重着色（非丝印/阻焊/courtyard 图元）",
     "cites_5A": True},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "绿色蝶形/腰条连接与各焊盘外围绿色环带，按§4(i)量化判据",
     "second_excerpt": "（§5A 渲染配色仪器注记所述空隙语义与之相容，但判定仍按§2/§3A/§4独立作出，未把仪器注记当作判据）",
     "cites_5A": True},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "仪器注记（§5A：橙色=原白墨图元重着色、绿色=板内空隙透白重着色且非图元）仅作为仪器事实知悉，未用作任何判据",
     "cites_5A": True},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "绿色蝶形/翼瓣区域按 §5A 仪器注记视为基材露白空隙而非图元（仅作仪器事实，未作为判据）",
     "cites_5A": True},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "焊盘旁的绿色楔形翼瓣空隙沿多条阵列系统性重复、最小重复单元形态一致",
     "second_excerpt": "§5A配色注记仅作仪器事实参考，未作为判据使用",
     "cites_5A": True},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "其绿色（按 §5A 为铺铜间隙/翼瓣类空隙，非图元）领结形空隙相连",
     "cites_5A": True},
]

#: 黑点类现象证据（r16 黑点类旗标 12 条全弃权+2 派次 notes 判正常未
#: 报告的代表摘录；kind=reading_notes 或 location_evidence；substring
#: fail-closed 校验；延续 r14/r15 黑点类追踪——本轮黑点/钻孔点为两
#: 视角主要弃权理由之一，按实例分布见 by_instance 实测）。
BLACK_DOT_EVIDENCE = [
    {"source": "prep1-top-i1", "kind": "location_evidence",
     "flag_id": "R16T-003", "instance": "top-i1", "disposition": "弃权",
     "excerpt": "右上模块区内有两个实心黑色填充圆"},
    {"source": "applied-top-i2", "kind": "location_evidence",
     "flag_id": "R16T-002", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上 D2 区域焊盘列上有两个竖直排列的实心黑圆点"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R16B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "一个黑色圆点（疑似孔状图形）"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R16B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "形态疑似钻孔点逼近乃至接触焊盘外轮廓"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R16B-003", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "右上缘同样紧邻一个小实心黑圆点"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "一枚黑色圆孔状图形，外观与该轮廓相切或略有搭接"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R16B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "另一枚黑色圆孔状图形位于下方另一组双焊盘组件椭圆 courtyard 轮廓上缘附近"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "一枚黑色钻孔圆点紧贴宽椭圆焊盘下缘"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R16B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "一枚黑色钻孔圆点紧贴宽椭圆焊盘上缘"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "孤立黑色实心小圆点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R16B-002", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "与第一处形态一致的孤立黑色实心小圆点"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "两粒小黑点分别紧贴两组胶囊形焊盘的边缘"},
    {"source": "prep1-top-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i2", "disposition": "判正常不报告",
     "excerpt": "右上两处黑色实心钻孔点（疑似安装孔）"},
    {"source": "prep1-top-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i3", "disposition": "判正常不报告",
     "excerpt": "右上元件区域内两个黑色实心圆点（符合连接器安装孔/定位孔的常规解释）"},
]

#: 黑点类旗标登记表（12 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定——r16 两板各自
#: 从头编号；applied-bottom-i2 两条因读者按「黑点-椭圆 courtyard 轮廓
#: 相切/近邻」归类为 courtyard_crowding（黑点类旗标首次进入 courtyard
#: 通道的 bottom 记录，与 r14 bottom 4 条 courtyard 弃权现象同族））。
BLACK_DOT_FLAGS = [
    ("top-i1", "prep1", "R16T-003", "other_advisory"),
    ("top-i2", "applied", "R16T-002", "other_advisory"),
    ("bottom-i1", "applied", "R16B-002", "other_advisory"),
    ("bottom-i1", "prep1", "R16B-002", "other_advisory"),
    ("bottom-i1", "prep1", "R16B-003", "other_advisory"),
    ("bottom-i2", "applied", "R16B-001", "courtyard_crowding"),
    ("bottom-i2", "applied", "R16B-002", "courtyard_crowding"),
    ("bottom-i2", "prep1", "R16B-001", "other_advisory"),
    ("bottom-i2", "prep1", "R16B-002", "other_advisory"),
    ("bottom-i3", "applied", "R16B-001", "other_advisory"),
    ("bottom-i3", "applied", "R16B-002", "other_advisory"),
    ("bottom-i3", "prep1", "R16B-001", "other_advisory"),
]

#: placement/孤立图形类旗标处置证据（逐字摘录；substring fail-closed
#: 校验）——r16 板内孤立焊盘组跨实例/跨板处置分化（弃权/非弃权报告/
#: 判正常不报告）+孤立方形焊盘独有绿色轮廓非弃权报告+top 斜置元件
#: 存在性弃权，如实单列。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "板内孤立焊盘组（圆形+方形焊盘对）",
     "excerpt": "一组孤立的一圆形焊盘加一方形焊盘，是整板唯一不位于四边阵列上的放置"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R16B-003", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（同位现象、跨板出口不同）",
     "excerpt": "该对焊盘孤立于板内、与周边规整排布模式明显不协调"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R16B-003", "instance": "bottom-i3", "verdict": "非弃权",
     "phenomenon": "孤立方形焊盘外围独有绿色方形轮廓线",
     "excerpt": "其余四处同类方形焊盘（各焊盘阵列端部）均无此轮廓"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R16B-001", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "孤立虚线环（分段环）焊盘",
     "excerpt": "其外围的绿色环呈断开分段（虚线环）形态"},
    {"source": "prep1-top-i3", "kind": "location_evidence",
     "flag_id": "R16T-006", "instance": "top-i3", "verdict": "弃权",
     "phenomenon": "疑似 45° 斜置两焊盘小图形（top 视角）",
     "excerpt": "疑似有一个45°斜置的两焊盘小图形"},
    {"source": "applied-bottom-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i2", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内右下孤立的圆焊盘+方形焊盘一组，间距与板面其他组件间距相当、无接触无交叠，未见可归类的关注形态，不报告"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内右侧一组孤立圆形+方形 2 焊盘小封装，样式与全域设计语言一致，判为常规小封装形态不报告"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed）。
REROUTE_ADJUDICATION = [
    {"source": "prep1-top-i1", "flag_id": "R16T-004", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("见一段走线呈疑似钩状回卷形态，与周边 "
                           "45°/90° 规整走线不一致"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法确认它是真实的可疑绕行还是"
              "普通弯折/过孔」=可疑改道是否存在无法负责任确认，按 §4 "
              "弃权")},
    {"source": "prep1-top-i3", "flag_id": "R16T-004", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("有一至两条走线呈明显S弯与钩状回折形态，与"
                           "周边较直捷的走线形态不一致"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中（「S弯」"
              "非「蛇形」子串、机械判定如实）；「无法端到端追踪确认其"
              "为真实的多余绕行还是相邻走线并行弯曲」按 §4 弃权")},
]

#: reroute 类旗标产量链基线（r8–r15 在案；本轮 r16 实测=2）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1}


def _fail(msg: str) -> None:
    print(f"[s58-cal-r16] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    return json.loads(_rel(rel).read_text(encoding="utf-8"))


def view_for_image(image: str) -> str:
    """图像名 → 视角（确定性；非 top/bottom 后缀即 ValueError）。"""
    if image.endswith("-top.png"):
        return "top"
    if image.endswith("-bottom.png"):
        return "bottom"
    raise ValueError(f"view_for_image: 图像名无视角后缀 {image!r}")


def parse_reader_raw(raw_rel: str) -> dict:
    """reader-raw 文件解析（T1；fail-closed；reader 产物零改动）。

    返回 {reader_id, images:[{image, view, flags, rejected}], notes,
    direct_json_parse, repair}；flags=五键投影（READER_KEYS，顺序保持
    内容零改动），rejected=被 calibration fail-closed 校验拒收的旗标
    清单（{image, flag_id, error}；reader 原文不修改）。
    """
    text = _rel(raw_rel).read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        _fail(f"reader-raw 非法 JSON（fail-closed 停止）: {raw_rel}: {exc}")
    if not isinstance(doc, dict) or sorted(doc) != sorted(
            ("reader_id", "per_image", "reading_notes")):
        _fail(f"reader-raw 顶层键非法: {raw_rel}: {sorted(doc)}")
    images = []
    for entry in doc["per_image"]:
        if not isinstance(entry, dict) or sorted(entry) != sorted(
                ("image", "flags")):
            _fail(f"reader-raw per_image 条目键非法: {raw_rel}")
        image = entry["image"]
        view = view_for_image(image)
        flags, rejected = [], []
        for f in entry["flags"]:
            try:
                cal._normalize_reader_flags([f])
            except ValueError as exc:
                rejected.append({"image": image, "flag_id": f.get("flag_id"),
                                 "error": str(exc)})
                continue
            flags.append({k: f[k] for k in READER_KEYS})
        images.append({"image": image, "view": view, "flags": flags,
                       "rejected": rejected})
    return {"reader_id": doc["reader_id"], "images": images,
            "reading_notes": doc["reading_notes"],
            "direct_json_parse": True, "repair": "no_repair"}


def _gt_entries_with_r5_reprojection(gt_rel: str, deriv_doc: dict) -> list:
    """GT 文件条目 + R5 重投影：frame_box_pct ← frame_box_pct_r5
    （按 gt_id 对齐 derivation-log-r5；其余字段逐字段原样）。

    R14 沿用该重投影：GT 13 条全部 side=top 且 top 渲染零变更
    （renders-r14b 两张 top=renders-r5 逐字节复用）⇒ 重投影输入
    （板 Edge.Cuts bbox + renders-r5 PNG 像素界）未变，本轮零新派生；
    bottom 渲染变更不触及 GT 重投影（bottom GT 无源在案 gt-audit-r1）。
    """
    r5 = {e["gt_id"]: e["frame_box_pct_r5"] for e in deriv_doc["entries"]}
    out = []
    for e in _json_load(gt_rel)["gt_entries"]:
        if e["gt_id"] not in r5:
            _fail(f"derivation-log-r5 缺 gt_id 重投影: {e['gt_id']}")
        e2 = dict(e)
        e2["frame_box_pct"] = list(r5[e["gt_id"]])
        out.append(e2)
    cal.validate_gt_entries(out)
    return out


def _state_block(state: str, state_desc: str, board_rel: str, board_sha: str,
                 gt_rel: str, gt_sha: str, raw_key: str,
                 parsed: dict, gt_entries: list) -> dict:
    """单实例单态块：内嵌 reader_flags/gt_entries/flag_views+compare_v3。"""
    flags = []
    flag_views = {}
    for img in parsed[raw_key]["images"]:
        for f in img["flags"]:
            flags.append(f)
            flag_views[f["flag_id"]] = img["view"]
    report = cal.compare_v3(flags, gt_entries, flag_views=flag_views)
    if report["containment_min"] != cal.CONTAINMENT_MIN \
            or report["area_ratio_max"] != cal.AREA_RATIO_MAX:
        _fail("compare_v3 阈值与声明常量不符")
    # 本轮无零旗标格（12 格全部≥1 旗）：view_check 必须 full。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    # 渲染 provenance 按视角分列：本轮渲染零变更（同指引重复轮=
    # renders-r14b 四图字节复用=r14/r15 轮盲读所用同一批文件）；top=
    # 字节内容与 renders-r5 一致（framing-r5 在案先例），bottom=r14b
    # 显式配色版（framing-r14b 预注册在案）。两视角共同声明=本轮零重
    # 渲染、唯一操纵因子=reader 实例群重抽。
    if "-top-" in raw_key:
        framing_rel = REL_FRAMING_R5
        framing_note = (
            "top 渲染零变更（跨 r14→r15→r16 三轮零变更）：r16 top="
            "renders-r14b 路径、字节内容=renders-r5（r14/r15 轮已逐字节"
            "复用在案；framing-r5 预注册件在案；本轮唯一操纵因子=reader "
            "实例群重抽）")
    else:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "bottom 渲染零变更：r16 bottom=renders-r14b 四图字节复用"
            "（与 R14/R15 完全相同：白墨图元→橙 (255,165,0)、板内空隙"
            "白→绿 (0,128,0)；四 PNG sha 与 render-witness-r14b.json "
            "登记值 fail-closed 比对一致=r14/r15 轮盲读所用同一批文件；"
            "framing-r14b=7004b017 预注册件在案；本轮零重渲染）")
    return {
        "state": state_desc,
        "source_board": {"path_rel": board_rel, "sha256": board_sha},
        "framing": {"path_rel": framing_rel, "sha256": _sha(framing_rel),
                    "note": framing_note},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R5, "sha256": _sha(REL_DERIV_R5),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取该台账"
                     " frame_box_pct_r5（R5 仪器像素界重投影；本轮渲染"
                     "未变故零新派生、沿用之）；board_box_mm/side 等其余"
                     "字段与 GT 文件逐字段原样；13 条全部 side=top"),
        },
        "gt_entries": gt_entries,
        "reader_flags": flags,
        "flag_views": flag_views,
        "view_check": report["view_check"],
        "compare_v3": report,
    }


def build_flag_gt_detail(flags: list, flag_views: dict, gt_entries: list,
                         report: dict, state: str) -> list:
    """逐旗 GT 重叠明细（measurement_design item 1；纯函数）。"""
    matched_by_flag = {m["flag_id"]: m for m in report["matches"]}
    abst = set(report["abstain"]["abstain_ids"])
    rows = []
    for f in flags:
        fid = f["flag_id"]
        if fid in abst:
            rows.append({"flag_id": fid, "state": state, "abstain": True,
                         "category": f["category"],
                         "gt_overlaps": [], "containment_all_none": None,
                         "matched": False, "matched_gt_id": None,
                         "note": "弃权旗不参与匹配（abstain 单列）"})
            continue
        overlaps = []
        none_cnt = 0
        for e in gt_entries:
            c = cal._containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None:
                none_cnt += 1
                continue
            ar = cal._area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            fv = flag_views.get(fid)
            if fv is not None and fv != e["side"]:
                channel = "view_gate"
            elif ar is None or ar > cal.AREA_RATIO_MAX:
                channel = "area_ratio_rejected"
            elif e["category"] != f["category"]:
                channel = "category_mismatch"
            else:
                channel = "candidate"
            overlaps.append({
                "gt_id": e["gt_id"], "gt_category": e["category"],
                "containment": cal._round6(c),
                "area_ratio": (cal._round6(ar) if ar is not None else None),
                "channel": channel})
        overlaps.sort(key=lambda x: x["gt_id"])
        m = matched_by_flag.get(fid)
        rows.append({"flag_id": fid, "state": state, "abstain": False,
                     "category": f["category"], "gt_overlaps": overlaps,
                     "containment_all_none": none_cnt == len(gt_entries),
                     "matched": bool(m),
                     "matched_gt_id": (m["gt_id"] if m else None)})
    rows.sort(key=lambda r: r["flag_id"])
    return rows


def build_instance_record(name: str, spec: dict, parsed: dict,
                          gt_applied: list, gt_prep1: list) -> dict:
    """实例主记录（measurement_design item 1；两板合计口径）。"""
    view = spec["view"]
    blk_appl = _state_block(
        "applied", "ASM-7 终检后终态", "out/revc-asm/board/applied.kicad_pcb",
        APPLIED_SHA_FROZEN, REL_GT_V2, _sha(REL_GT_V2),
        spec["parts"][0], parsed, gt_applied)
    blk_prep = _state_block(
        "prep1", "ASM-P1 批前快照（种子域）",
        "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb", PREP1_SHA_FROZEN,
        REL_GT_V1, _sha(REL_GT_V1), spec["parts"][1], parsed, gt_prep1)
    n_fl = (len(blk_appl["reader_flags"]) +
            len(blk_prep["reader_flags"]))
    n_ab = (blk_appl["compare_v3"]["abstain"]["abstain_count"] +
            blk_prep["compare_v3"]["abstain"]["abstain_count"])
    n_sc = (blk_appl["compare_v3"]["reader_scored_count"] +
            blk_prep["compare_v3"]["reader_scored_count"])
    matches_detail = []
    gt_matched_ids = []
    for st, blk in (("applied", blk_appl), ("prep1", blk_prep)):
        for m in blk["compare_v3"]["matches"]:
            matches_detail.append(dict(
                m, state=st,
                containment=cal._round6(m["containment"]),
                area_ratio=cal._round6(m["area_ratio"])))
            gt_matched_ids.append(m["gt_id"])
    matches_detail.sort(key=lambda m: (m["state"], m["flag_id"]))
    abstain_ids = (
        [{"state": "applied", "flag_id": i}
         for i in blk_appl["compare_v3"]["abstain"]["abstain_ids"]]
        + [{"state": "prep1", "flag_id": i}
           for i in blk_prep["compare_v3"]["abstain"]["abstain_ids"]])
    abstain_ids.sort(key=lambda x: (x["state"], x["flag_id"]))
    abst_appl = set(blk_appl["compare_v3"]["abstain"]["abstain_ids"])
    abst_prep = set(blk_prep["compare_v3"]["abstain"]["abstain_ids"])
    non_abstain_ids = sorted(
        [{"state": "applied", "flag_id": f["flag_id"]}
         for f in blk_appl["reader_flags"] if f["flag_id"] not in abst_appl]
        + [{"state": "prep1", "flag_id": f["flag_id"]}
           for f in blk_prep["reader_flags"] if f["flag_id"] not in abst_prep],
        key=lambda x: (x["state"], x["flag_id"]))
    per_flag_detail = (
        build_flag_gt_detail(blk_appl["reader_flags"],
                             blk_appl["flag_views"], gt_applied,
                             blk_appl["compare_v3"], "applied")
        + build_flag_gt_detail(blk_prep["reader_flags"],
                               blk_prep["flag_views"], gt_prep1,
                               blk_prep["compare_v3"], "prep1"))
    per_flag_detail.sort(key=lambda r: r["flag_id"])
    abstain_rate = cal._ratio(n_ab, n_fl)
    if abstain_rate is None:
        arith = ("abstain_rate = %d/%d = None（零旗标分母，按库侧 "
                 "cal._ratio 先例=None，measurement_design item 5；"
                 "不编造数值）" % (n_ab, n_fl))
    else:
        arith = ("abstain_rate = %d/%d = %s（分母=该实例该视角全部旗标，"
                 "跨两板合计；measurement_design item 1）"
                 % (n_ab, n_fl, abstain_rate))
    return {
        "instance": name, "view": view,
        "reader_id": parsed[spec["parts"][0]]["reader_id"],
        "parts": {"applied": spec["parts"][0], "prep1": spec["parts"][1]},
        "states": {"applied": blk_appl, "prep1": blk_prep},
        "combined": {
            "flag_count": n_fl,
            "abstain_count": n_ab,
            "scored": n_sc,
            "abstain_rate": abstain_rate,
            "abstain_rate_arithmetic": arith,
            "matches_total": len(matches_detail),
            "matches_detail": matches_detail,
            "gt_matched_union": len(set(gt_matched_ids)),
            "gt_recall_union": cal._ratio(len(set(gt_matched_ids)), 13),
            "seed_match_rate": cal._ratio(len(matches_detail), n_sc),
            "abstain_ids": abstain_ids,
            "non_abstain_flag_ids": non_abstain_ids,
            "flag_id_scope_note": (
                "r16 实测 flag_id 两板各自从头编号（跨板同号如实登记；"
                "与 prep-record naming「同实例跨板连续」声明不同=读者"
                "实例输出行为差异、如实入账不作废）——abstain_ids/"
                "non_abstain_flag_ids 按 (state, flag_id) 限定，跨板"
                "同号不混淆"),
        },
        "per_flag_gt_detail": per_flag_detail,
    }


def _median3(vals: list):
    """恰 3 值的中位数（排序后取第 2；measurement_design item 2：
    中位数+最小值+最大值三分列、不取整）。"""
    if len(vals) != 3:
        _fail(f"median3 需恰 3 值: {vals}")
    return sorted(vals)[1]


def build_view_layer(instances: dict) -> dict:
    """视角层聚合（measurement_design item 2；每视角 3 实例三分列）。

    本轮无零旗标实例（12 格全部≥1 旗）：两视角弃权率全部有定义
    （中位数=排序后第 2）；item 5 口径（零分母→None）保留备用。
    """
    out = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        fc = {n: instances[n]["combined"]["flag_count"] for n in names}
        ar = {n: instances[n]["combined"]["abstain_rate"] for n in names}
        mt = {n: instances[n]["combined"]["matches_total"] for n in names}
        fc_vals = [fc[n] for n in names]
        ar_vals = [ar[n] for n in names]
        mt_vals = [mt[n] for n in names]
        computable = [v for v in ar_vals if v is not None]
        none_names = [n for n in names if ar[n] is None]
        if none_names:
            ar_median = None
            ar_min, ar_max = min(computable), max(computable)
            ar_range = cal._round6(ar_max - ar_min)
            ar_median_note = (
                "弃权率中位数含 None 实例（%s 零旗标分母→None，cal._ratio "
                "先例、measurement_design item 5）无法定义→None（不编造"
                "数值）；min/max 按可计算实例（%s）计算"
                % ("/".join(none_names),
                   "/".join(n for n in names if ar[n] is not None)))
            range_arithmetic = (
                "实例间弃权率极差（max−min，按可计算实例）= %s − %s = %s"
                "（%s = %s/%s/%s；%s 零旗标分母→None 不计入、如实注明——"
                "measurement_design item 5 口径）"
                % (ar_max, ar_min, ar_range,
                   "/".join(names), ar_vals[0], ar_vals[1], ar_vals[2],
                   "/".join(none_names)))
        else:
            ar_median = _median3(ar_vals)
            ar_median_note = "三实例弃权率均有定义（中位数=排序后第 2）"
            ar_min, ar_max = min(ar_vals), max(ar_vals)
            ar_range = cal._round6(ar_max - ar_min)
            range_arithmetic = (
                "实例间弃权率极差（max−min）= %s − %s = %s（%s/%s/%s = "
                "%s/%s/%s）"
                % (ar_max, ar_min, ar_range, names[0], names[1], names[2],
                   ar_vals[0], ar_vals[1], ar_vals[2]))
        ar_block = {
            "by_instance": ar,
            "median": ar_median,
            "min": ar_min,
            "max": ar_max,
            "median_note": ar_median_note,
        }
        out[view] = {
            "instances": names,
            "flag_count": {"by_instance": fc,
                           "median": _median3(fc_vals),
                           "min": min(fc_vals), "max": max(fc_vals)},
            "abstain_rate": ar_block,
            "matches": {"by_instance": mt,
                        "median": _median3(mt_vals),
                        "min": min(mt_vals), "max": max(mt_vals)},
            "abstain_rate_range": ar_range,
            "abstain_rate_range_arithmetic": range_arithmetic,
        }
    return out


def build_gt_dual(instances: dict, gt_applied: list, gt_prep1: list) -> dict:
    """GT 匹配聚合双口径（measurement_design item 3）。

    逐 GT 条目 matched_by_count（0..3）=同视角 3 实例中命中该条目的
    实例数（命中判定=该实例对应态 compare_v3 的 matches 含该 gt_id，
    即逐旗 containment/area_ratio 过门+一对一指派后在 GT 条目上归并）；
    union（≥1 实例命中即计）与 agreement（≥2/3 实例命中才计）两口径
    并列；召回分母=GT 13 条；bottom 无 GT 在案（gt-audit-r1：bottom
    GT=无源已关闭）⇒ bottom 旗标与 GT 匹配应为空（如实）。
    """
    state_of_gt = {}
    ordered = []
    for e in gt_applied:
        state_of_gt[e["gt_id"]] = "applied"
        ordered.append(e)
    for e in gt_prep1:
        state_of_gt[e["gt_id"]] = "prep1"
        ordered.append(e)
    per_gt = []
    for e in ordered:
        gid = e["gt_id"]
        st = state_of_gt[gid]
        hits = []
        for n in INSTANCE_ORDER:
            if instances[n]["view"] != e["side"]:
                continue
            for m in instances[n]["combined"]["matches_detail"]:
                if m["gt_id"] == gid:
                    hits.append({"instance": n, "flag_id": m["flag_id"],
                                 "state": m["state"],
                                 "containment": m["containment"],
                                 "area_ratio": m["area_ratio"]})
        hits.sort(key=lambda h: h["instance"])
        per_gt.append({
            "gt_id": gid, "category": e["category"], "side": e["side"],
            "state": st,
            "gt_role": ("gt_expansion（applied 态）" if st == "applied"
                        else "gt_seed（prep1 态）"),
            "matched_by_count": len(hits),
            "hits": hits})
    union_ids = [g["gt_id"] for g in per_gt if g["matched_by_count"] >= 1]
    agreement_ids = [g["gt_id"] for g in per_gt if g["matched_by_count"] >= 2]
    return {
        "denominator": 13,
        "denominator_note": ("召回分母=GT 13 条（applied 9+prep1 4；"
                            "全部 side=top——bottom 无 GT 在案 "
                            "gt-audit-r1：bottom GT=无源已关闭，bottom "
                            "旗标与 GT 匹配应为空，如实）"),
        "hit_rule": ("命中判定=每实例逐旗 containment/area_ratio 过门"
                     "（CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明常量"
                     "零改动）+一对一指派后在 GT 条目上归并；top 视角=3 "
                     "实例、bottom 视角=3 实例"),
        "union": {"rule": "≥1 实例命中即计", "gt_ids": union_ids,
                  "count": len(union_ids),
                  "gt_recall_union": cal._ratio(len(union_ids), 13)},
        "agreement": {"rule": "≥2/3 实例命中才计", "gt_ids": agreement_ids,
                      "count": len(agreement_ids),
                      "gt_recall_agreement": cal._ratio(
                          len(agreement_ids), 13)},
        "per_gt": per_gt,
    }


def pick_representative(instances: dict) -> dict:
    """代表配置选取（measurement_design item 4：每视角 flag_count
    中位数实例；中位不唯一取先序并如实注明 tie）。"""
    sel = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        counts = {n: instances[n]["combined"]["flag_count"] for n in names}
        med = _median3(list(counts.values()))
        tied = [n for n in names if counts[n] == med]
        sel[view] = {
            "selected": tied[0],
            "median_flag_count": med,
            "tie": len(tied) > 1,
            "tie_note": ("flag_count 中位 %d 不唯一（%s 同为 %d）→按先序"
                         "取 %s，如实注明 tie（measurement_design item 4 "
                         "无挑优语义；不预设、不挑优）"
                         % (med, "/".join(tied), med, tied[0]))
            if len(tied) > 1 else "中位实例唯一（%s）" % tied[0],
            "flag_count_by_instance": counts,
        }
    return {
        "rule": ("measurement_design item 4（预注册）：代表配置=每视角取 "
                 "flag_count 中位数实例组成代表配置，计算一轮 joint 结果"),
        "selection": sel,
        "members": {"top": sel["top"]["selected"],
                    "bottom": sel["bottom"]["selected"]},
    }


def _merge_state_blocks(blocks: list, state: str, state_desc: str,
                        gt_entries: list) -> dict:
    """代表配置合并态块（同态两实例旗标拼接；视角注入合并）。"""
    flags = []
    flag_views = {}
    for blk in blocks:
        flags.extend(blk["reader_flags"])
        flag_views.update(blk["flag_views"])
    report = cal.compare_v3(flags, gt_entries, flag_views=flag_views)
    if report["view_check"] != "full":
        _fail(f"代表配置 {state} 态 view_check 应为 full")
    return {
        "state": state_desc,
        "members": [b["members_note"] for b in blocks],
        "gt_file": blocks[0]["gt_file"],
        "gt_reprojection": blocks[0]["gt_reprojection"],
        "gt_entries": gt_entries,
        "reader_flags": flags,
        "flag_views": flag_views,
        "view_check": report["view_check"],
        "compare_v3": report,
    }


def _aggregate(prep: dict, appl: dict) -> dict:
    """两态联合聚合（照 s47 口径；此处置于代表配置）。"""
    p, a = prep["compare_v3"], appl["compare_v3"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    cells: dict = {v: {"abstain_count": 0, "flag_count": 0}
                   for v in ("top", "bottom")}
    for blk in (prep, appl):
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            cell = cells[view]
            cell["flag_count"] += 1
            if fid in abst:
                cell["abstain_count"] += 1
    by_view = {}
    for view, cell in cells.items():
        cell["rate"] = cal._ratio(cell["abstain_count"], cell["flag_count"])
        cell["fraction"] = f"{cell['abstain_count']}/{cell['flag_count']}"
        by_view[view] = dict(cell)
    return {
        "scope": ("代表配置两态联合（measurement_design item 4 预注册："
                  "代表配置=每视角 flag_count 中位数实例；与 per-metric "
                  "实例间范围、逐实例原始记录三者并列如实呈现，不合并、"
                  "不挑优）"),
        "flag_count_total": n_fl,
        "gt_count_total": n_gt,
        "matches_total": n_match,
        "gt_matched_total": n_gm,
        "scored_total": n_sc,
        "abstain_count_total": n_ab,
        "gt_recall_total": cal._ratio(n_gm, n_gt),
        "gt_recall_arithmetic": f"gt_recall_total = ({p['gt_matched_count']}"
                                f"+{a['gt_matched_count']})/({p['gt_count']}"
                                f"+{a['gt_count']}) = {n_gm}/{n_gt}",
        "seed_match_rate_total": cal._ratio(n_match, n_sc),
        "seed_match_rate_arithmetic":
            f"seed_match_rate_total = ({len(p['matches'])}+"
            f"{len(a['matches'])})/({p['reader_scored_count']}+"
            f"{a['reader_scored_count']}) = {n_match}/{n_sc}",
        "abstain_rate_total": cal._ratio(n_ab, n_fl),
        "abstain_rate_arithmetic": f"abstain_rate_total = "
            f"({p['abstain']['abstain_count']}+"
            f"{a['abstain']['abstain_count']})/({p['reader_flag_count']}+"
            f"{a['abstain']['reader_flag_count']}) = {n_ab}/{n_fl}",
        "abstain_rate_by_state": {
            "applied": a["abstain"]["abstain_rate"],
            "applied_fraction":
                f"{a['abstain']['abstain_count']}/"
                f"{a['abstain']['reader_flag_count']}",
            "prep1": p["abstain"]["abstain_rate"],
            "prep1_fraction":
                f"{p['abstain']['abstain_count']}/"
                f"{p['abstain']['reader_flag_count']}",
        },
        "abstain_rate_by_view": {
            "top": by_view["top"]["rate"],
            "top_fraction": by_view["top"]["fraction"],
            "bottom": by_view["bottom"]["rate"],
            "bottom_fraction": by_view["bottom"]["fraction"],
        },
        "abstain_rate_by_view_arithmetic":
            f"abstain_rate_by_view: top = {by_view['top']['fraction']} = "
            f"{by_view['top']['rate']}；bottom = "
            f"{by_view['bottom']['fraction']} = "
            f"{by_view['bottom']['rate']}",
        "abstain_rate_definition": cal.ABSTAIN_RATE_DEFINITION,
        "seed_metric_note": cal.SEED_METRIC_NOTE,
    }


def build_metric_ranges(instances: dict) -> dict:
    """per-metric 实例间范围（measurement_design item 4 三并列之二）。"""
    out = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        comb = [instances[n]["combined"] for n in names]
        rates = [c["abstain_rate"] for c in comb]
        computable = [r for r in rates if r is not None]
        none_names = [n for n, r in zip(names, rates) if r is None]
        rate_block = {
            "min": min(computable) if computable else None,
            "max": max(computable) if computable else None,
        }
        if none_names:
            rate_block["note"] = (
                "%s 零旗标分母→abstain_rate=None（cal._ratio 先例、"
                "measurement_design item 5）；min/max 按可计算实例（%s）"
                "计算，不编造数值" % ("/".join(none_names),
                                    "/".join(n for n, r in
                                             zip(names, rates)
                                             if r is not None)))
        out[view] = {
            "instances": names,
            "flag_count": {"min": min(c["flag_count"] for c in comb),
                           "max": max(c["flag_count"] for c in comb)},
            "abstain_count": {"min": min(c["abstain_count"] for c in comb),
                              "max": max(c["abstain_count"] for c in comb)},
            "abstain_rate": rate_block,
            "matches_total": {"min": min(c["matches_total"] for c in comb),
                              "max": max(c["matches_total"] for c in comb)},
            "gt_matched_union": {"min": min(c["gt_matched_union"]
                                            for c in comb),
                                 "max": max(c["gt_matched_union"]
                                            for c in comb)},
            "scored": {"min": min(c["scored"] for c in comb),
                       "max": max(c["scored"] for c in comb)},
        }
    return out


def _criteria(agg: dict) -> list:
    return [
        {"id": "gt_count_ge_12", "threshold": 12,
         "actual": agg["gt_count_total"],
         "met": agg["gt_count_total"] >= 12,
         "note": ("有效分母=v1 四条（prep1 态）+v2 九条（applied 态）"
                  "=13；全部条目在派生台账声明可见性依据（协议 §3.5 "
                  "排除口径无剔除项）")},
        {"id": "gt_recall_ge_0.75", "threshold": 0.75,
         "actual": agg["gt_recall_total"],
         "met": agg["gt_recall_total"] >= 0.75,
         "note": f"gt_recall_total={agg['gt_matched_total']}/"
                 f"{agg['gt_count_total']}（代表配置口径）"},
        {"id": "seed_match_rate_ge_0.5", "threshold": 0.5,
         "actual": agg["seed_match_rate_total"],
         "met": agg["seed_match_rate_total"] >= 0.5,
         "note": f"seed_match_rate_total={agg['matches_total']}/"
                 f"{agg['scored_total']}（诊断值，禁称 precision/FPR）"},
        {"id": "abstain_rate_le_0.5", "threshold": 0.5,
         "actual": agg["abstain_rate_total"],
         "met": agg["abstain_rate_total"] <= 0.5,
         "note": f"abstain_rate_total={agg['abstain_count_total']}/"
                 f"{agg['flag_count_total']}（单位=旗标条数；分母=代表"
                 "配置全部旗标）；APR-0011 阈值零改动，与预注册主通道"
                 "三分判据（top ≤0.75 / ≥0.862 / 两值之间=inconclusive）"
                 "各自独立计算、互不凌驾"},
    ]


def _compliance(agg: dict) -> dict:
    criteria = _criteria(agg)
    all_met = all(c["met"] for c in criteria)
    unmet = "、".join(c["id"] for c in criteria if not c["met"]) or "无"
    return {
        "baseline": "APR-0011（provisional_supersedable；"
                    "evaluation-protocol-v1 §3 联合评价；阈值零改动）",
        "scope_note": ("本轮联合评价按 measurement_design item 4 以代表"
                       "配置计算；与 per-metric 实例间范围、逐实例原始"
                       "记录三者并列如实呈现，不合并、不挑优"),
        "criteria": criteria,
        "joint_evaluation": "met" if all_met else "not_met",
        "joint_evaluation_rule": "任一不满足即未达标（协议 v1 §3）",
        "consecutive_rounds": {
            "id": "consecutive_2_rounds", "required": 2,
            "consecutive_met_count": 0,
            "met": False,
            "rounds": {"r1": "not_met（在案）", "r2": "not_met（在案）",
                       "r3": "not_met（在案）", "r4": "not_met（在案）",
                       "r5": "not_met（在案）", "r6": "not_met（在案）",
                       "r7": "not_met（在案）", "r8": "not_met（在案）",
                       "r9": "not_met（在案）", "r10": "not_met（在案）",
                       "r11": "not_met（在案）", "r12": "not_met（在案）",
                       "r13": "not_met（在案）", "r14": "not_met（在案）",
                       "r15": "not_met（在案）",
                       "r16": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": (f"本轮联合评价未达标（代表配置未达暂行线项={unmet}；"
                     "实测值见 criteria），连续计数仍"
                     "为 0" if not all_met
                     else "本轮联合评价达标，连续计数=1（development 域，"
                          "不计入正式采纳）"),
        },
        "critic_calibration_in_range": False,
        "critic_calibration_in_range_note": (
            "轮后实测值如实记录；谓词语义不变（正式采纳须人工批准），"
            "自动分流恒 blocked（BL-4+TD5 合取约束，达标≠自动分流）；"
            "正式采纳前 in_calibrated_range 恒 False"),
    }


# ---------------------------------------------------------------------------
# 逐旗失败通道归因（vs R12；方法照抄 s34/s36/s39/s41/s43/s45/s47：
# 通道级，非旗级）
# ---------------------------------------------------------------------------

def channel_replay(flags: list, flag_views: dict, gt_entries: list) -> dict:
    """近邻失败通道重放（纯函数；与 compare_v3 同源几何原语）。

    对每个非弃权旗标与同态全部 GT 条目计算 containment/area_ratio：
    containment<CONTAINMENT_MIN（含 None=无交集）→ 无条目（非近邻）；
    近邻且视角不符 → view_gate（视角门，不入两预注册通道计数）；
    近邻且面积比>AREA_RATIO_MAX → area_ratio_rejected（几何门）；
    近邻且面积比≤上限且类别不符 → category_mismatch（类别门）；
    类别相符且双条件过 → candidate（一对一指派候选）。
    返回 {entries, candidate_pairs}；candidate_pairs 与该态
    compare_v3 的 matches∪duplicate_reports 对拍复核。
    """
    entries = []
    for f in flags:
        if f["abstain"]:
            continue
        for e in gt_entries:
            c = cal._containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None or c < cal.CONTAINMENT_MIN:
                continue
            ar = cal._area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            base = {"flag_id": f["flag_id"], "category": f["category"],
                    "gt_id": e["gt_id"], "gt_category": e["category"],
                    "flag_view": flag_views.get(f["flag_id"]),
                    "gt_side": e["side"], "containment": cal._round6(c)}
            if flag_views.get(f["flag_id"]) and \
                    flag_views[f["flag_id"]] != e["side"]:
                entries.append(dict(base, failure="view_gate",
                                    area_ratio=(cal._round6(ar)
                                                if ar is not None else None)))
            elif ar is None or ar > cal.AREA_RATIO_MAX:
                entries.append(dict(base, failure="area_ratio_rejected",
                                    area_ratio=(cal._round6(ar)
                                                if ar is not None else None)))
            elif e["category"] != f["category"]:
                entries.append(dict(base, failure="category_mismatch",
                                    area_ratio=cal._round6(ar)))
            else:
                entries.append(dict(base, failure="candidate",
                                    area_ratio=cal._round6(ar)))
    entries.sort(key=lambda x: (x["flag_id"], x["gt_id"]))
    candidate_pairs = sorted((x["flag_id"], x["gt_id"]) for x in entries
                             if x["failure"] == "candidate")
    return {"entries": entries, "candidate_pairs": candidate_pairs}


def replay_matches_agree(replay: dict, report: dict) -> bool:
    """重放 candidate 对拍该态 compare_v3（matches∪duplicates）。"""
    ref = sorted([(m["flag_id"], m["gt_id"]) for m in report["matches"]]
                 + [(d["flag_id"], d["gt_id"])
                    for d in report["duplicate_reports"]])
    return replay["candidate_pairs"] == ref


def _channel_entry(e: dict) -> dict:
    keep = ("flag_id", "category", "gt_id", "gt_category", "containment",
            "area_ratio", "state", "instance")
    return {k: e[k] for k in keep if k in e}


def reroute_production_blocks(blocks: list) -> int:
    """reroute 类旗标产量（弃权+非弃权合计，全视角；纯函数）。

    入参=态块列表（实例态块或 run_doc 态块值均可）。
    """
    n = 0
    for blk in blocks:
        for f in blk["reader_flags"]:
            if f["category"] == "suspicious_reroute":
                n += 1
    return n


def reroute_production(states: dict) -> int:
    """reroute 类旗标产量（states 映射版；兼容 run_doc["states"]）。"""
    return reroute_production_blocks(list(states.values()))


def replay_round_instances(run_doc: dict) -> dict:
    """六实例 run-doc 内嵌输入重放（返回 {(instance, state): replay}）。"""
    replays = {}
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            blk = run_doc["instances"][name]["states"][st]
            rp = channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
            if not replay_matches_agree(rp, blk["compare_v3"]):
                _fail(f"内嵌输入重放与 compare_v3 对拍不一致: "
                      f"{name}/{st}")
            replays[(name, st)] = rp
    return replays


def build_channel_attribution(run_r6: dict, run_r7: dict, run_r8: dict,
                              run_r9: dict, run_r11: dict, run_r12: dict,
                              run_r13: dict, run_r14: dict, run_r15: dict,
                              inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R15；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R14/R15 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r14_replays = replay_round_instances(run_r14)
    r15_replays = replay_round_instances(run_r15)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R16 {key} 通道重放与 compare_v3 对拍不一致")

    def pick(failure, replays, blocks):
        rows = []
        if blocks is not None:
            for blk in blocks:
                rp = replays[blk["_part_key"]]
                for e in rp["entries"]:
                    if e["failure"] == failure:
                        rows.append(_channel_entry(
                            dict(e, state=blk["_state"],
                                 instance=blk["_instance"])))
        else:
            for name in INSTANCE_ORDER:
                for st in ("applied", "prep1"):
                    for e in replays[(name, st)]["entries"]:
                        if e["failure"] == failure:
                            rows.append(_channel_entry(
                                dict(e, state=st, instance=name)))
        rows.sort(key=lambda x: (x["instance"], x["state"], x["flag_id"],
                                 x["gt_id"]))
        return rows

    # r11 条目数取 run-r12 在案转录（r10 条目数取 run-r11 在案转录；
    # r14/r15=本轮 fresh 重放并与在案登记逐一交叉核对）
    geo_r14 = pick("area_ratio_rejected", r14_replays, None)
    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r14 = pick("category_mismatch", r14_replays, None)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r14 = pick("view_gate", r14_replays, None)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", inst_replays, inst_blocks)
    # 与在案 run 登记交叉核对（fail-closed：重放结果须与在案一致）
    if geo_r14 != run_r14["channel_attribution"]["channel_1_geometry_gate"][
            "r14_area_ratio_rejected_entries"]:
        _fail("R14 几何门重放与 run-r14 在案登记不一致")
    if cat_r14 != run_r14["channel_attribution"]["channel_2_category_gate"][
            "r14_category_mismatch_entries"]:
        _fail("R14 类别门重放与 run-r14 在案登记不一致")
    if view_r14 != run_r14["channel_attribution"][
            "view_gate_observations"]["r14_entries"]:
        _fail("R14 视角门重放与 run-r14 在案登记不一致")
    if geo_r15 != run_r15["channel_attribution"]["channel_1_geometry_gate"][
            "r15_area_ratio_rejected_entries"]:
        _fail("R15 几何门重放与 run-r15 在案登记不一致")
    if cat_r15 != run_r15["channel_attribution"]["channel_2_category_gate"][
            "r15_category_mismatch_entries"]:
        _fail("R15 类别门重放与 run-r15 在案登记不一致")
    if view_r15 != run_r15["channel_attribution"][
            "view_gate_observations"]["r15_entries"]:
        _fail("R15 视角门重放与 run-r15 在案登记不一致")

    geo_change = (
        "几何门通道（R15→R16）：面积比出局条目 %d→%d（r15 重放零几何门"
        "条目、r16 重放=%d 条；同指引重复轮+渲染零变更下条目变化=纯"
        "实例群重抽效果的方向性观察；多实例样本量极小，只描述不断言。"
        % (len(geo_r15), len(geo_r16), len(geo_r16)))
    cat_change = (
        "类别门通道（R15→R16）：类别不符出局条目 %d→%d（r12–r15 连续"
        "零条目，r16 重放=%d 条；R11T-012↔GT-REVC-AP-8-R1Q2 仍为 r11 "
        "唯一条目）；多实例样本量极小，只描述不断言。"
        % (len(cat_r15), len(cat_r16), len(cat_r16)))

    def _gate_count(doc, num, key):
        return len(doc["channel_attribution"][key][
            f"r{num}_{'area_ratio_rejected' if key == 'channel_1_geometry_gate' else 'category_mismatch'}_entries"])

    chain = {
        "scope": ("通道归因链自 r6 起逐轮在案（各轮 run-record "
                  "channel_attribution，run sha 锚在案）；跨轮 flag_id "
                  "不构成同旗配对，通道级归因"),
        "geometry_gate_area_ratio_rejected_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_1_geometry_gate"),
            "r7": _gate_count(run_r7, 7, "channel_1_geometry_gate"),
            "r8": _gate_count(run_r8, 8, "channel_1_geometry_gate"),
            "r9": _gate_count(run_r9, 9, "channel_1_geometry_gate"),
            "r10": len(run_r11["channel_attribution"][
                "channel_1_geometry_gate"]["r10_area_ratio_rejected_entries"]),
            "r11": len(run_r12["channel_attribution"][
                "channel_1_geometry_gate"]["r11_area_ratio_rejected_entries"]),
            "r12": len(run_r13["channel_attribution"][
                "channel_1_geometry_gate"]["r12_area_ratio_rejected_entries"]),
            "r13": len(run_r14["channel_attribution"][
                "channel_1_geometry_gate"]["r13_area_ratio_rejected_entries"]),
            "r14": len(geo_r14),
            "r15": len(geo_r15),
            "r16": len(geo_r16),
        },
        "category_gate_category_mismatch_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_2_category_gate"),
            "r7": _gate_count(run_r7, 7, "channel_2_category_gate"),
            "r8": _gate_count(run_r8, 8, "channel_2_category_gate"),
            "r9": _gate_count(run_r9, 9, "channel_2_category_gate"),
            "r10": len(run_r11["channel_attribution"][
                "channel_2_category_gate"]["r10_category_mismatch_entries"]),
            "r11": len(run_r12["channel_attribution"][
                "channel_2_category_gate"]["r11_category_mismatch_entries"]),
            "r12": len(run_r13["channel_attribution"][
                "channel_2_category_gate"]["r12_category_mismatch_entries"]),
            "r13": len(run_r14["channel_attribution"][
                "channel_2_category_gate"]["r13_category_mismatch_entries"]),
            "r14": len(cat_r14),
            "r15": len(cat_r15),
            "r16": len(cat_r16),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=%d（r14 回升未延续、r15–r16 同指引重复"
                 "轮维持低位：top 非弃权旗与同态 GT ≥0.5 containment 交叠"
                 "条目如实计数）；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→"
                 "r11=1→r12=0→r13=0→r14=0→r15=0→r16=%d（r11 唯一条目 "
                 "R11T-012↔AP-8 连续五轮无再现）"
                 % (len(geo_r16), len(cat_r16))),
    }
    n_fl_total = sum(len(b["reader_flags"]) for b in inst_blocks)
    n_ab_total = sum(b["compare_v3"]["abstain"]["abstain_count"]
                     for b in inst_blocks)
    n_match_total = sum(len(b["compare_v3"]["matches"])
                        for b in inst_blocks)
    courtyard_all = [(b["_instance"], b["_state"], f["flag_id"])
                     for b in inst_blocks
                     for f in b["reader_flags"]
                     if f["category"] == "courtyard_crowding"]
    courtyard_counts = (
        courtyard_all,
        [x for x in courtyard_all if x[0].startswith("top")],
        [x for x in courtyard_all if x[0].startswith("bottom")])
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R16, "sha256": _sha(REL_PREP_R16)},
            "declaration": prep_doc_attribution_declaration(),
            "primary_channel": {
                "change": prep_doc_primary_channel_change(),
                "metric": prep_doc_primary_channel_metric(),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
            },
        },
        "method": {
            "source_of_r14_r15_detail": (
                "calibration-run-r14.json / calibration-run-r15.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/s55 "
                "deviation_note 口径：本轮对 R14/R15/R16 均以内嵌输入+"
                "compare_v3 同源几何原语（calibration._containment/_"
                "area_ratio、CONTAINMENT_MIN=0.5、AREA_RATIO_MAX=10.0 "
                "声明常量）对每非弃权旗标×同态 GT 确定性重放通道分类："
                "containment<0.5（含 None=无交集）无条目；近邻且视角不符"
                "=view_gate；近邻且面积比>上限=area_ratio_rejected（几何"
                "门）；近邻且面积比≤上限且类别不符=category_mismatch（"
                "类别门）；类别相符且双条件过=candidate。"),
            "replay_cross_check": {
                "r14_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r14_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r15_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r15_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r16_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R14/R15 十二件复算"
                         "与在案 run 登记一致：R14/R15 候选对=空集；R16 "
                         "十二件重放全部复现，见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R14T/R14B、R15T/R15B 与 R16T/"
            "R16B 来自不同 reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素；r16 两板各自从头编号"
            "亦属实例输出行为差异、如实登记）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r14_area_ratio_rejected_entries": geo_r14,
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r14_category_mismatch_entries": cat_r14,
            "r15_category_mismatch_entries": cat_r15,
            "r16_category_mismatch_entries": cat_r16,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r14_entries": view_r14,
            "r15_entries": view_r15,
            "r16_entries": view_r16,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r16 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；r14/r15 重放亦零视角门条目（在案延续）。"
                     % len(view_r16)),
        },
        "gate_chain_since_r6": chain,
        "r16_specific_observations": [
            "R16 六实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条；GT 条目层 union/agreement 与"
            "代表配置口径见 gt_match_dual/aggregation_representative"
            "（如实分列）；bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
            "side=top，bottom GT 无源在案 gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R16 courtyard 类旗标 %d 条（top %d+bottom %d）：bottom "
            "courtyard 类旗标在 r15 零旗标后部分再现（applied-bottom-i2 "
            "两条黑点-椭圆 courtyard 轮廓相切/近邻弃权旗、r14 同族现象"
            "）；非弃权 courtyard 见 courtyard_tracking（逐旗明细在案）；"
            "top 弃权理由构成分型=接触性 11+存在性 15+层归属其他 1"
            "（hypothesis_test.mechanism_observation."
            "top_abstain_typology 逐旗摘录在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R16 几何门 %d 条（r15=0 延续与否如实计数）；类别门 %d 条"
            "（r12–r15 连续零条目后的本轮计数如实登记）；视角门条目数"
            "见 view_gate_observations（如实单列）。"
            % (len(geo_r16), len(cat_r16)),
            "R16 suspicious_reroute 旗标 2 条（全部弃权、存在性出口："
            "R16T-004 prep1-top-i1+R16T-004 prep1-top-i3，(state, "
            "flag_id) 限定）；产量链 r8=1→r9=0→r10=2→r11=3→r12=3→"
            "r13=2→r14=1→r15=4→r16=2；「等长|蛇形」子串双旗零命中"
            "——r16 滥用型通道被动追踪=0（见 hypothesis_test."
            "reroute_continuation_r16，非本轮判据输入）。",
            "courtyard 被动追踪（r11–r15 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r16 "
            "courtyard_tracking 节）。",
        ],
    }


def _prep_doc() -> dict:
    """r16-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R16)


def prep_doc_attribution_declaration() -> str:
    """归因声明文本（取自 r15-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["declaration"]


def prep_doc_primary_channel_change() -> str:
    """主通道变更文本（取自 r15-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["change"]


def prep_doc_primary_channel_metric() -> str:
    """主通道度量文本（取自 r15-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["metric"]


def prep_doc_guard_channel() -> dict:
    """守门通道（取自 r15-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["guard_channel"]


# ---------------------------------------------------------------------------
# 预注册假设（r13-dev-record-candidate-0-render-disambiguate）裁决
# （字母裁决+主通道双条件逐实例实测+机制观察单列）
# ---------------------------------------------------------------------------

def bottom_courtyard_non_abstain(instances: dict) -> dict:
    """bottom 侧观察实测（操作化定义：bottom 三实例 courtyard 类非
    弃权旗数；per r16-prep-record side_observation「bottom courtyard
    旗与非弃权计数…对照 r15 的…0/0/0」原文；side_observation_separate
    =单列、不影响字母）。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r16 两板各自从头编号、明细行已按 (state, flag_id) 限定）；
    逐实例计数与 SIDE_OBS_REGISTERED 的 expected 逐一相等
    （fail-closed，不符即中止）。
    """
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        rec = instances[name]
        cnt = sum(1 for d in rec["per_flag_gt_detail"]
                  if d["category"] == "courtyard_crowding"
                  and not d["abstain"])
        out[name] = cnt
    for row in SIDE_OBS_REGISTERED:
        if out[row["instance"]] != row["expected"]:
            _fail(f"bottom 侧观察实测与登记表不符: {row['instance']} "
                  f"实测={out[row['instance']]} 登记={row['expected']}")
    return out


def r15_baseline_courtyard_live(run_r15: dict) -> dict:
    """r15 基线重放实测（side_observation 对照「r15 的 0/0/0」；run-r15
    内嵌输入；与 R15_BOTTOM_COURTYARD_BASELINE 登记交叉核对）。"""
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            blk = run_r15["instances"][name]["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in blk["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        out[name] = cnt
    if out != R15_BOTTOM_COURTYARD_BASELINE:
        _fail(f"r15 bottom courtyard 基线与 run-r15 实测不符: {out}")
    return out


def _view_aggregate_abstain_live(run_doc: dict, instances: tuple) -> tuple:
    """视角全旗聚合弃权（分子, 分母）重放实测（判据 (a)/(b) 与 side
    observation 同一口径：对 run-doc 内嵌实例记录按 states 层重放，
    不读 combined 汇总值）。"""
    n_fl = 0
    n_ab = 0
    for name in instances:
        for st in ("applied", "prep1"):
            blk = run_doc["instances"][name]["states"][st]
            n_fl += len(blk["reader_flags"])
            n_ab += blk["compare_v3"]["abstain"]["abstain_count"]
    return n_ab, n_fl


def r14_top_abstain_aggregate_live(run_r14: dict) -> tuple:
    """r14 top 全旗聚合弃权重放实测（(a) 支基线=0.75；同一聚合逻辑对
    run-r14 内嵌实例记录双侧复算、不手工抄数；与 BASE14_TOP_AGGREGATE_
    REGISTERED=(18,24) 交叉核对）。"""
    ab, fl = _view_aggregate_abstain_live(
        run_r14, ("top-i1", "top-i2", "top-i3"))
    if {"abstain": ab, "flags": fl} != BASE14_TOP_AGGREGATE_REGISTERED:
        _fail("r14 top 全旗聚合弃权基线与 run-r14 实测不符（应为 18/24）")
    return ab, fl


def r15_top_abstain_aggregate_live(run_r15: dict) -> tuple:
    """r15 top 全旗聚合弃权重放实测（(b) 支基线=0.862069；同一聚合逻辑
    对 run-r15 内嵌实例记录双侧复算、不手工抄数；与 BASE15_TOP_AGGREGATE_
    REGISTERED=(25,29) 交叉核对）。"""
    ab, fl = _view_aggregate_abstain_live(
        run_r15, ("top-i1", "top-i2", "top-i3"))
    if {"abstain": ab, "flags": fl} != BASE15_TOP_AGGREGATE_REGISTERED:
        _fail("r15 top 全旗聚合弃权基线与 run-r15 实测不符（应为 25/29）")
    return ab, fl


def r15_bottom_abstain_aggregate_live(run_r15: dict) -> tuple:
    """r15 bottom 全旗聚合弃权重放实测（side_observation 基线；对照
    11/13=0.846154）。"""
    ab, fl = _view_aggregate_abstain_live(
        run_r15, ("bottom-i1", "bottom-i2", "bottom-i3"))
    if {"abstain": ab, "flags": fl} != BASE15_BOTTOM_AGGREGATE_REGISTERED:
        _fail("r15 bottom 全旗聚合弃权基线与 run-r15 实测不符（应为 "
              "11/13）")
    return ab, fl


def round_view_aggregate(instances: dict, view_instances: tuple) -> tuple:
    """本轮视角全旗聚合弃权（分子, 分母）（与基线重放同一聚合口径：
    三实例两板合计；与实例层 combined 计数同源）。"""
    n_fl = 0
    n_ab = 0
    for name in view_instances:
        n_fl += instances[name]["combined"]["flag_count"]
        n_ab += instances[name]["combined"]["abstain_count"]
    return n_ab, n_fl


def verify_reroute_continuation(instances: dict, raw_texts: dict) -> list:
    """reroute 类旗标被动追踪逐旗判定（r12 通道延续；fail-closed）。

    对 reroute 类旗标全列逐旗：
    - 子串命中集=程序实测（「等长|蛇形」对 location_evidence），须与
      登记表 declared_substring_hits 逐一相等（含顺序）；
    - form_desc_excerpt 逐字 substring 校验（防转述失真）；
    - abstain 属性与登记表一致。
    返回逐旗判定行（含实测子串与证据），并在不符时中止。
    """
    declared = {row["flag_id"]: row for row in REROUTE_ADJUDICATION}
    live = []
    for name in INSTANCE_ORDER:
        for d in instances[name]["per_flag_gt_detail"]:
            if d["category"] != "suspicious_reroute":
                continue
            fid = d["flag_id"]
            if fid not in declared:
                _fail(f"reroute 旗标缺逐旗判定登记: {fid}")
            row = declared[fid]
            loc = None
            for key, rel in RAW_FILES.items():
                if key != row["source"]:
                    continue
                doc = json.loads(_rel(rel).read_text(encoding="utf-8"))
                for img in doc["per_image"]:
                    for f in img["flags"]:
                        if f["flag_id"] == fid:
                            loc = f["location_evidence"]
            if loc is None:
                _fail(f"逐旗判定登记 source/flag_id 与盘上件不符: {fid}")
            hits = [s for s in ("等长", "蛇形") if s in loc]
            if hits != row["declared_substring_hits"]:
                _fail(f"子串命中实测与登记不符: {fid} "
                      f"实测={hits} 登记={row['declared_substring_hits']}")
            if row["form_desc_excerpt"] not in raw_texts[row["source"]]:
                _fail(f"形态描述摘录与 reader 原文不符: {fid}")
            if row["abstain"] is not d["abstain"]:
                _fail(f"登记 abstain 与实例明细不符: {fid}")
            live.append({
                "source": row["source"], "flag_id": fid,
                "instance": name, "state": d["state"],
                "abstain": d["abstain"],
                "detected_substring_hits": hits,
                "declared_substring_hits": row["declared_substring_hits"],
                "form_desc_excerpt": row["form_desc_excerpt"],
                "adjudication": row["adjudication"],
                "note": row["note"]})
    live.sort(key=lambda r: (r["instance"], r["flag_id"]))
    if len(live) != len(REROUTE_ADJUDICATION):
        _fail("逐旗判定登记表与实测 reroute 旗标数不符")
    return live


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          run_r11: dict, run_r12: dict, run_r13: dict,
                          run_r14: dict, run_r15: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（r15-dev-record-candidate-0-same-guidance-repeat）裁决节
    （预注册三分判据执行；字母裁决唯一正式+机制观察单列+bottom 侧观察
    单列）。

    字母裁决（唯一正式裁决）=判据 r16-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：top 全旗聚合弃权率归因裁决三支——
    (a) top ≤0.75（=run-r14 双侧复算基线，live 重放交叉核对 (18,24)
    一致）→ supported（漂移解释 (α) 成立，r15 (iii) 违约记为实例群
    噪声，r15 图例的 bottom 主通道效应（(i)(ii)）得以保留确认）；
    (b) top ≥0.862（=r15 实测水平，live 重放交叉核对 (25,29) 一致）→
    reject（§5A 全局弃权致敏解释 (β) 升级，指引侧再处置预注册后执行）；
    (c) 0.75<top<0.862（两轮值之间=两候选解释均不排斥）→ inconclusive
    （development 域如实记录，归因悬置，机制观察加权）。
    判据比较用整数交叉相乘（避免浮点比较）；(a)/(b) 两支互斥（同时
    成立即自洽性破坏、中止）；机制观察单列、不凌驾、不改写字母裁决；
    bottom 主通道维持性=side_observation_separate 单列（不影响字母）。
    """
    prep_doc = _json_load(REL_PREP_R16)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（round15-dev-record 锚已在 FROZEN_SHA256 校验；
    # 其 next_iteration_targets[0] 候选原文被本 prep-record 逐字摘录
    # 预注册；sha256_measured 与盘上实测须一致）
    dev15 = _json_load(REL_DEV_R15)
    preref = prep_doc["guidance_reuse"]["chain_anchors"][
        "round15_dev_record_authorization"]
    if preref["path_rel"] != REL_DEV_R15 or \
            preref["sha256_measured"] != _sha(REL_DEV_R15) or \
            dev15["next_iteration_targets"][
                preref["item_indices_zero_based"][0]] \
            != preref["candidate_quote"]:
        _fail("prep-record 预注册摘录（candidate_0）与 round15-dev-record "
              "原文/锚不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "0.75" not in adj["letter_supported"] or \
            "run-r14 双侧复算基线" not in adj["letter_supported"]:
        _fail("prep-record letter_supported 文本与预期不符")
    if "0.862" not in adj["letter_reject"] or \
            "r15 实测水平" not in adj["letter_reject"]:
        _fail("prep-record letter_reject 文本与预期不符")
    if "0.75 < top < 0.862" not in adj["letter_inconclusive"]:
        _fail("prep-record letter_inconclusive 文本与预期不符")
    # 两侧基线数字 live 重放与在案登记交叉核对（fail-closed；不手工抄数）
    base14_ab, base14_fl = r14_top_abstain_aggregate_live(run_r14)
    base15_ab, base15_fl = r15_top_abstain_aggregate_live(run_r15)
    if cal._ratio(base14_ab, base14_fl) != 0.75:
        _fail("run-r14 top 基线重放率与冻结值 0.75 不符")
    if cal._ratio(base15_ab, base15_fl) != 0.862069:
        _fail("run-r15 top 基线重放率与冻结值 0.862069 不符")
    # bottom 侧观察基线（r15 的 11/13=0.846154 与 0/0/0；live 重放核对）
    base15_bot_ab, base15_bot_fl = r15_bottom_abstain_aggregate_live(run_r15)
    r15_courtyard_base = r15_baseline_courtyard_live(run_r15)
    # reroute 产量链基线交叉核对（r8–r15 在案）
    if reroute_production(run_r8["states"]) != REROUTE_CHAIN_PRIOR["r8"] \
            or reroute_production(run_r9["states"]) != REROUTE_CHAIN_PRIOR["r9"] \
            or reroute_production(run_r10["states"]) != REROUTE_CHAIN_PRIOR["r10"] \
            or run_r11["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r11"] \
            or run_r12["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r12"] \
            or run_r13["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r13"] \
            or run_r14["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r14"] \
            or run_r15["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r15"]:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（top 全旗聚合弃权率；三分判据逐支）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    # (a) top ≤0.75（=run-r14 双侧复算基线 live；整数交叉相乘避免浮点）
    crit_a_ok = abst_top * base14_fl <= base14_ab * flags_top
    # (b) top ≥0.862（=run-r15 实测水平 live；整数交叉相乘避免浮点）
    crit_b_ok = abst_top * base15_fl >= base15_ab * flags_top
    if crit_a_ok and crit_b_ok:
        _fail("主通道判定自洽性破坏（(a) 与 (b) 两支互斥）")
    # bottom 侧观察（side_observation_separate：单列、不影响字母）
    by_instance = bottom_courtyard_non_abstain(instances)
    bot_courtyard_flags = sum(
        1 for n in ("bottom-i1", "bottom-i2", "bottom-i3")
        for d in instances[n]["per_flag_gt_detail"]
        if d["category"] == "courtyard_crowding")
    abst_bot, flags_bot = round_view_aggregate(
        instances, ("bottom-i1", "bottom-i2", "bottom-i3"))
    bot_rate = cal._ratio(abst_bot, flags_bot)
    bot_worse_than_r15 = abst_bot * base15_bot_fl > \
        base15_bot_ab * flags_bot
    # 守门通道（top 几何门）——独立单列（prep-record guard_channel：
    # 「几何门面积比出局条目变化如实记录」，无数值要件）
    geo_r16 = attribution["channel_1_geometry_gate"][
        "r16_area_ratio_rejected_entries"]
    geo_r15 = attribution["channel_1_geometry_gate"][
        "r15_area_ratio_rejected_entries"]
    guard_ok = len(geo_r16) <= len(geo_r15)
    # 字母裁决（三分判据，per r16-prep-record adjudication 原文）
    if crit_a_ok:
        verdict = "supported"
        letter_branch = ("(a) top 全旗聚合弃权率 ≤0.75——漂移解释 (α) "
                         "成立（r15 (iii) 违约记为实例群噪声，r15 图例"
                         "的 bottom 主通道效应得以保留确认）")
    elif crit_b_ok:
        verdict = "reject"
        letter_branch = ("(b) top 全旗聚合弃权率 ≥0.862——致敏解释 (β) "
                         "升级（§5A 指引侧遗留效应成立，后续须指引侧再"
                         "处置，预注册后执行）")
    else:
        verdict = "inconclusive"
        letter_branch = ("(c) 0.75 < top < 0.862——两候选解释均不排斥、"
                         "归因悬置（development 域如实记录；机制观察"
                         "加权）")
    verdict_text = (
        "按预注册判据（r16-prep-record.json hypothesis_test.adjudication "
        "原文，三分判据）=%s（字母口径，唯一正式裁决）：落支=%s。实测："
        "top 全旗聚合弃权率=%d/%d=%s；(a) 支基线=run-r14 同口径聚合弃权"
        "率（同一聚合逻辑对 calibration-run-r14.json 内嵌实例记录双侧"
        "复算=%d/%d=%s，与在案登记 18/24 交叉核对一致，不手工抄数）；"
        "(b) 支基线=run-r15 实测水平（同一聚合逻辑对 calibration-run-"
        "r15.json 内嵌实例记录双侧复算=%d/%d=%s，与在案登记 25/29 交叉"
        "核对一致，不手工抄数）；整数交叉相乘比较（避免浮点）：(a) 支 "
        "%d×%d vs %d×%d → %s；(b) 支 %d×%d vs %d×%d → %s。同指引重复轮"
        "（零变更：指引/渲染字节复用、GT/阈值/协议零变更）下唯一操纵"
        "因子=reader 实例群重抽——字母裁决只回答「r15 top 水平是漂移"
        "还是致敏」的归因方向；三项判据文本分开如实记录、不合并；本轮"
        "判据均为描述性边界、非 APR-0011 门（门照常独立计算，互不凌驾、"
        "run-record 内分开表述）。守门通道（top 几何门）=r16-prep-record "
        "attribution_plan.guard_channel 独立单列（R15=%d→R16=%d 条，"
        "如实记录）。注意：%s；单轮 n=3、development 域只描述不断言；"
        "机制观察单列（bottom 主通道维持性/黑点类分布/绿区语义化/top "
        "弃权构成分型），不凌驾、不改写字母裁决。"
        % (verdict, letter_branch,
           abst_top, flags_top, top_rate,
           base14_ab, base14_fl, cal._ratio(base14_ab, base14_fl),
           base15_ab, base15_fl, cal._ratio(base15_ab, base15_fl),
           abst_top, base14_fl, base14_ab, flags_top,
           "≤ 成立" if crit_a_ok else "> 不成立",
           abst_top, base15_fl, base15_ab, flags_top,
           "≥ 成立" if crit_b_ok else "< 不成立",
           len(geo_r15), len(geo_r16),
           ("inconclusive=归因悬置、非无效——两候选解释均不排斥，分辨力"
            "须靠分层（同实例群双跑）或判据侧处置补足，不得以连续 "
            "inconclusive 反复消耗盲读（per prep-record "
            "metric_lesson_separate）" if verdict == "inconclusive"
            else "字母裁决=预注册描述性边界下的方向性归因、非统计证明"
                 "——「正确测出无效同样是有效证据」")))
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 量化判据应用
    # + top 弃权分型逐旗 + 黑点类 + placement 处置 + 绿区语义化）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in QUANT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    # top 弃权理由构成分型（机制观察 (d)）：覆盖完整性 fail-closed——
    # 登记表 (source, flag_id) 集合须与实测 top 三实例全部弃权旗集合
    # 逐一相等；逐旗 excerpt 逐字 substring 校验
    typology_rows = []
    typology_counts = {"contact": 0, "existence": 0, "other_layer": 0}
    top_abstain_keys = set()
    for n in ("top-i1", "top-i2", "top-i3"):
        for d in instances[n]["per_flag_gt_detail"]:
            if d["abstain"]:
                src = (INSTANCES[n]["parts"][0] if d["state"] == "applied"
                       else INSTANCES[n]["parts"][1])
                top_abstain_keys.add((src, d["flag_id"]))
    if {(ev["source"], ev["flag_id"]) for ev in TOP_ABSTAIN_TYPOLOGY} \
            != top_abstain_keys:
        _fail("top 弃权分型登记表与实测 top 弃权旗集合不一致")
    for ev in TOP_ABSTAIN_TYPOLOGY:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"top 弃权分型摘录与 reader 原文不符: {ev['flag_id']}")
        if ev["type"] not in typology_counts:
            _fail(f"top 弃权分型未知类型: {ev['type']}")
        typology_counts[ev["type"]] += 1
        typology_rows.append({"source": ev["source"],
                              "flag_id": ev["flag_id"],
                              "type": ev["type"],
                              "excerpt": ev["excerpt"],
                              "note": ev.get("note")})
    for ev in GREEN_SEMANTICS_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"绿区语义化摘录与 reader 原文不符: {ev['source']}")
        if "second_excerpt" in ev and \
                ev["second_excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"绿区语义化第二摘录与 reader 原文不符: {ev['source']}")
    for ev in BLACK_DOT_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"黑点类证据摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in PLACEMENT_DISPOSITION_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"placement 处置摘录与 reader 原文不符: {ev.get('flag_id')}")
    # 黑点类旗标登记校验（12 条全部存在、abstain=True、category=登记值）
    black_rows = []
    for inst, st, fid, cat in BLACK_DOT_FLAGS:
        d = next(x for x in instances[inst]["per_flag_gt_detail"]
                 if x["flag_id"] == fid and x["state"] == st)
        if not d["abstain"] or d["category"] != cat:
            _fail(f"黑点类旗标登记与实测不符: {fid}")
        black_rows.append({"flag_id": fid, "instance": inst, "state": st,
                           "category": d["category"], "abstain": True})
    # 绿色区域语义化观察（r16-prep-record side_observation「黑点类与
    # 绿区语义化方式延续观察」预注册：按实例分布；程序实测 substring
    # 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、不构成判据输入）
    green_semantics = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        rec = INSTANCES[name]
        texts = [parsed_notes[p] for p in rec["parts"]]
        cites = [bool(r.get("cites_5A"))
                 for r in GREEN_SEMANTICS_EVIDENCE
                 if r["instance"] == name]
        green_semantics[name] = {
            "绿_hits_by_part": [t.count("绿") for t in texts],
            "翼瓣_hits_by_part": [t.count("翼瓣") for t in texts],
            "空隙_hits_by_part": [t.count("空隙") for t in texts],
            "§5A_cited": any(cites),
            "semantic_mode": ("§5A 仪器注记显式提及+空隙语义化"
                              if any(cites)
                              else "空隙/翼瓣几何语义化（无 §5A 显式"
                                   "援引）"),
        }
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    black_by_instance = {n: sum(1 for row in black_rows
                                if row["instance"] == n)
                         for n in INSTANCE_ORDER}
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决不因本观察"
                 "改写；per r16-prep-record adjudication."
                 "side_observation_separate/metric_lesson_separate）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道三分判据分开实测（机制 (a)）：top 全旗聚合弃权率"
                "=%d/%d=%s；(a) 支 ≤0.75（run-r14 双侧复算基线 18/24="
                "0.75，live 重放与在案登记交叉核对一致）→crit_a=%s；"
                "(b) 支 ≥0.862（run-r15 实测水平 25/29=0.862069，live "
                "重放与在案登记交叉核对一致）→crit_b=%s；⇒ verdict=%s"
                "（%s）。两支分开如实记录、不合并；(a)(b) 同真被自洽性"
                "检查排除（整数交叉相乘比较）。"
                % (abst_top, flags_top, top_rate,
                   crit_a_ok, crit_b_ok, verdict, letter_branch)),
            "counts": {
                "r14_top_baseline_registered":
                    BASE14_TOP_AGGREGATE_REGISTERED,
                "r14_top_baseline_live": f"{base14_ab}/{base14_fl}",
                "r15_top_baseline_registered":
                    BASE15_TOP_AGGREGATE_REGISTERED,
                "r15_top_baseline_live": f"{base15_ab}/{base15_fl}",
                "top_flags_r16": flags_top,
                "top_abstain_r16": abst_top,
                "top_abstain_rate_r16": top_rate,
                "crit_a_top_le_r14_baseline": crit_a_ok,
                "crit_b_top_ge_r15_baseline": crit_b_ok,
                "verdict": verdict,
            },
            "status": (
                "同指引重复轮（零变更）下 top 落点=%s 支（如实单列）；"
                "(α) 漂移与 (β) 致敏两候选解释的取舍以字母裁决为准、"
                "机制观察不凌驾" % verdict),
        },
        "bottom_side_observation_maintenance": {
            "role": ("bottom 主通道维持性（side_observation_separate："
                     "单列、不影响字母；per r16-prep-record "
                     "side_observation 原文「bottom courtyard 旗与非"
                     "弃权计数、bottom 全旗聚合弃权率对照 r15 的 11/13="
                     "0.846 与 0/0/0」）"),
            "observation": (
                "bottom 维持性两件实测：(1) courtyard 类旗标与非弃权"
                "计数——r16 实测非弃权 courtyard=0/0/0（对照 r15 的 "
                "0/0/0，live 重放交叉核对一致），但 courtyard 类旗标"
                "本身=%d 条（全部弃权；applied-bottom-i2 黑点-椭圆 "
                "courtyard 轮廓相切/近邻形态，r14「黑点骑跨轮廓」同族"
                "现象部分再现——r15 零旗标路径→r16 有旗全弃权路径，"
                "成因差异如实分列）；(2) bottom 全旗聚合弃权率=%d/%d=%s"
                "（对照 r15 的 11/13=0.846154，live 重放交叉核对一致）"
                "——方向=%s（若 bottom 恶化=图例效应本身实例群敏感的"
                "候选信号，per side_observation.note 如实记录、不影响"
                "字母）。"
                % (bot_courtyard_flags, abst_bot, flags_bot, bot_rate,
                   "高于 r15 基线（恶化方向）" if bot_worse_than_r15
                   else "不高于 r15 基线（维持）")),
            "counts": {
                "r15_bottom_courtyard_non_abstain_by_instance_live":
                    r15_courtyard_base,
                "r16_bottom_courtyard_non_abstain_by_instance":
                    by_instance,
                "r16_bottom_courtyard_flags_total": bot_courtyard_flags,
                "r16_bottom_courtyard_non_abstain_total":
                    sum(by_instance.values()),
                "r15_bottom_aggregate_registered":
                    BASE15_BOTTOM_AGGREGATE_REGISTERED,
                "r15_bottom_aggregate_live":
                    f"{base15_bot_ab}/{base15_bot_fl}",
                "bottom_flags_r16": flags_bot,
                "bottom_abstain_r16": abst_bot,
                "bottom_abstain_rate_r16": bot_rate,
                "bottom_abstain_rate_r15_baseline":
                    cal._round6(base15_bot_ab / base15_bot_fl),
                "bottom_rate_vs_r15_direction": (
                    "worse" if bot_worse_than_r15 else "not_worse"),
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": (
                "6 派次摘录逐字来自对应 reading_notes（substring "
                "fail-closed 校验通过）——bottom 六派次仍按 §4(i) 量化"
                "判据把绿色翼瓣/空隙形态判入「系统性正常→不报告」（判读"
                "路径延续使用）"),
            "status": (
                "非弃权 courtyard 计数维持 0/0/0+聚合弃权率方向如实单列"
                "（不影响字母裁决；development 域只描述不断言）"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r16-prep-record "
                "side_observation 预注册延续观察；对照 r15 三实例「空隙/"
                "翼瓣」几何收敛+3 派次 §5A 显式援引）：r16 bottom 六派次"
                " notes 全部以「空隙/翼瓣」语义化绿色（翼瓣状空隙/蝶形"
                "腰条连接/领结形空隙/楔形翼瓣空隙），且六派次全部显式"
                "提及 §5A 仪器注记——其中 4 派次明写「仅作仪器事实、未"
                "作为判据」（prep1-bottom-i1/applied-bottom-i2/"
                "prep1-bottom-i2/applied-bottom-i3）、applied-bottom-i1"
                " 直接按 §5A 语义读取图面（「据此本图未见任何丝印文字」）、"
                "prep1-bottom-i3 把 §5A 空隙语义并入 §4(i) 判读——r15 的"
                "语义化收敛在 r16 实例群重抽下完全保持（6/6）。逐实例 "
                "substring 计数「绿|翼瓣|空隙|§5A」+摘录如实登记（无"
                "期望、不构成判据输入）。"),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）"),
            "status": ("绿区语义化「空隙非图元」读法在实例群重抽下延续"
                       "（6/6 派次 §5A 提及、r15 收敛保持；如实单列、"
                       "不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点类现象追踪（机制观察 (b)）：r16 黑点类旗标 12 条"
                "全部弃权——top 视右上黑点 2 旗（prep1-top-i1 R16T-003+"
                "applied-top-i2 R16T-002，r14/r15 首现现象延续）+bottom "
                "左上黑点 10 旗（i1 3+i2 4+i3 3，r14/r15 同形态延续且"
                "本轮=bottom 弃权主要理由）；其中 applied-bottom-i2 两条"
                "被读者归类为 courtyard_crowding（黑点-椭圆 courtyard "
                "轮廓相切/近邻）——黑点类在 r16 进入 bottom courtyard "
                "通道（r14 同族现象部分再现，见 bottom 侧观察）；全部"
                "存在性/接触性弃权出口；vs r15 黑点类 7 旗全弃权——"
                "数量上升（跨轮实例群重抽下方向性描述）；另有 2 派次 "
                "notes 把黑点判为安装孔/定位类正常特征未报告（prep1-"
                "top-i2/prep1-top-i3，逐字摘录在案）=同现象跨实例处置"
                "分化，如实登记。"),
            "black_dot_flags": black_rows,
            "by_instance": black_by_instance,
            "all_abstain": all(r["abstain"] for r in black_rows),
            "notes_normal_dispositions": (
                "2 派次判正常：prep1-top-i2「右上两处黑色实心钻孔点"
                "（疑似安装孔）」+prep1-top-i3「右上元件区域内两个黑色"
                "实心圆点（符合连接器安装孔/定位孔的常规解释）」（摘录"
                "见 evidence 表 disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点类弃权路径延续+数量上升+处置实例分化（如实"
                       "单列、不凌驾字母裁决）"),
        },
        "top_abstain_typology": {
            "observation": (
                "top 弃权理由构成分型（机制观察 (d)，为 top 高弃权归因"
                "提供分解）：本轮 top 弃权旗 %d 条逐旗按 location_evidence "
                "关键词分类——接触性（真实接触 vs 视觉贴近不可分辨/是否"
                "接触不可确认）=%d 条、存在性（性质不明/是否存在不可"
                "确认）=%d 条、层归属等其他出口=%d 条。构成解读（如实"
                "单列）：接触性弃权集中于 courtyard 类旗标（§4(iii) 判据"
                "路径延续），存在性弃权横跨 silk/other/reroute/placement "
                "各类（黑点性质、叠压是否存在、绕行是否存在等）——top "
                "弃权非单一机制驱动；r15 的「6 条 courtyard 弃权中 5 接触"
                "+1 存在性」在 r16 实例群重抽下扩展为「弃权理由构成多"
                "通道化」。逐旗摘录与分类在案（rows）。"
                % (len(typology_rows), typology_counts["contact"],
                   typology_counts["existence"],
                   typology_counts["other_layer"])),
            "type_counts": typology_counts,
            "top_abstain_flags_total": len(typology_rows),
            "rows": typology_rows,
            "evidence_check": (
                "%d/%d 条摘录逐字来自对应 location_evidence 且 (source, "
                "flag_id) 集合与实测 top 弃权旗集合逐一相等（substring+"
                "覆盖 fail-closed 校验通过）"
                % (len(typology_rows), len(typology_rows))),
            "top_abstain_rates_by_instance": top_rates,
            "top_abstain_rate_range": top_range,
            "status": ("top 弃权构成=接触性主通道+存在性多通道分散（"
                       "如实单列、不凌驾字母裁决；为「漂移 vs 致敏」"
                       "归因悬置情形提供下一轮分型依据）"),
        },
        "residual_instance_differences": {
            "observation": (
                "残余实例差异（如实单列）：(1) top 弃权率 %s/%s/%s（极差 "
                "%s）——top-i2 单实例 13/14=0.928571 拉高轮内极差（"
                "prep1-top-i2 单派次 11 旗全弃权=本轮最高弃权格）；"
                "(2) bottom 弃权率 %s/%s/%s（极差 %s）——bottom-i1 全"
                "弃权（5 旗）；(3) placement/孤立图形处置实例分化：板内"
                "孤立焊盘组 bottom-i1 弃权/bottom-i2 跨板分化（applied "
                "判正常不报告、prep1 非弃权报告）/bottom-i3 判正常不报告+"
                "孤立方形焊盘独有绿色轮廓非弃权报告；孤立虚线环焊盘"
                "（prep1-bottom-i1）弃权——同现象跨实例/跨板出口不同="
                "判读语义歧义未穷尽；「正确测出无效同样是有效证据」的同"
                "构：测出残余差异同样是有效证据。"
                % (top_rates["top-i1"], top_rates["top-i2"],
                   top_rates["top-i3"], top_range,
                   bottom_rates["bottom-i1"], bottom_rates["bottom-i2"],
                   bottom_rates["bottom-i3"], bottom_range)),
            "evidence": PLACEMENT_DISPOSITION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("残余差异不凌驾字母裁决；不构成已证因果"
                       "关系（实例群重抽为本轮操纵因子、轮内样本极小）"),
        },
    }
    metric_lesson_continuation = {
        "role": ("度量设计教训延续（如实，供未来预注册参考；本轮不追溯"
                 "适用；per r16-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r16 三分判据的 (c) 支（0.75<top<0.862）命中=inconclusive"
            "——两轮制归因（漂移 (α) vs 致敏 (β)）对「两基线之间」的"
            "落点分辨力有限（per prep-record metric_lesson_separate "
            "原文：若 inconclusive，第三点须靠分层（同实例群双跑）或"
            "判据侧处置，不得以连续 inconclusive 反复消耗盲读）；(a)(b) "
            "两支冻结值=run-r14/run-r15 同口径双侧复算（live 重放+在案"
            "登记交叉核对）避免了手工抄数漂移；bottom 侧观察"
            "（side_observation_separate）单列使 bottom 效应的维持性"
            "不与 top 归因混叠；同指引重复轮恰以实例群重抽为唯一操纵"
            "因子，使「两候选解释消解」设计成立——但落点居中时归因"
            "悬置如实入账（聚合与分层观察分开记账的度量设计教训链 "
            "r9–r15 延续）。"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一轮候选方向（如实登记，不构成本轮判据"
                   "输入）：同实例群双跑分层或判据侧处置（per prep-"
                   "record metric_lesson_separate）；不得回溯改判既往"
                   "轮次（r8–r15 字母裁决维持不变）"),
    }
    # r15 分层基线（逐实例弃权率，live 重放；不手工抄数）
    r15_top_rates = {}
    r15_bottom_rates = {}
    for n in INSTANCE_ORDER:
        blk_a = run_r15["instances"][n]["states"]["applied"]
        blk_p = run_r15["instances"][n]["states"]["prep1"]
        fl_n = len(blk_a["reader_flags"]) + len(blk_p["reader_flags"])
        ab_n = (blk_a["compare_v3"]["abstain"]["abstain_count"]
                + blk_p["compare_v3"]["abstain"]["abstain_count"])
        rate_n = cal._ratio(ab_n, fl_n)
        if n.startswith("top"):
            r15_top_rates[n] = rate_n
        else:
            r15_bottom_rates[n] = rate_n
    r15_top_range = cal._round6(
        max(r15_top_rates.values()) - min(r15_top_rates.values()))
    r15_bottom_range = cal._round6(
        max(r15_bottom_rates.values()) - min(r15_bottom_rates.values()))
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R16,
                                "sha256": _sha(REL_PREP_R16)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "letter_supported": adj["letter_supported"],
            "letter_reject": adj["letter_reject"],
            "letter_inconclusive": adj["letter_inconclusive"],
            "support": prep_doc["attribution_plan"]["primary_channel"][
                "support"],
            "reject": prep_doc["attribution_plan"]["primary_channel"][
                "reject"],
            "inconclusive": prep_doc["attribution_plan"]["primary_channel"][
                "inconclusive"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "side_observation_separate": adj["side_observation_separate"],
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel_metric": prep_doc["attribution_plan"][
            "primary_channel"]["metric"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r16-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮假设检验、与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "top_abstain_flags_r16": flags_top,
            "top_abstain_count_r16": abst_top,
            "top_abstain_rate_r16": top_rate,
            "top_abstain_rate_r16_arithmetic":
                f"top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（三分判据度量）",
            "crit_a_top_le_r14_baseline": crit_a_ok,
            "crit_b_top_ge_r15_baseline": crit_b_ok,
            "top_abstain_rate_r14_baseline_live":
                f"{base14_ab}/{base14_fl}",
            "top_abstain_rate_r14_baseline_value":
                cal._ratio(base14_ab, base14_fl),
            "top_abstain_rate_r15_baseline_live":
                f"{base15_ab}/{base15_fl}",
            "top_abstain_rate_r15_baseline_value":
                cal._ratio(base15_ab, base15_fl),
            "baseline_replay_note": (
                "两侧基线=同一聚合逻辑对 calibration-run-r14.json / "
                "calibration-run-r15.json 内嵌实例记录（states 层 "
                "reader_flags+compare_v3.abstain）双侧复算，不手工抄数；"
                "且与在案登记值（r16-prep-record chain_anchors."
                "run_r15_criterion_anchor.frozen_values：top 25/29="
                "0.862069、基线 18/24=0.75）交叉核对（fail-closed，见 "
                "baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r16":
                    by_instance,
                "bottom_courtyard_flags_total_r16": bot_courtyard_flags,
                "bottom_abstain_flags_r16": flags_bot,
                "bottom_abstain_count_r16": abst_bot,
                "bottom_abstain_rate_r16": bot_rate,
                "bottom_abstain_rate_r16_arithmetic":
                    f"bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                    f"{bot_rate}"
                    f"（对照 r15 基线 11/13=0.846154；side_observation_"
                    f"separate 单列、不影响字母）",
                "bottom_abstain_rate_r15_baseline_live":
                    f"{base15_bot_ab}/{base15_bot_fl}",
                "bottom_abstain_rate_r15_baseline_value":
                    cal._ratio(base15_bot_ab, base15_bot_fl),
                "bottom_rate_direction_vs_r15": (
                    "高于 r15 基线（恶化方向，如实单列；实例群敏感候选"
                    "信号照 per side_observation.note 登记）"
                    if bot_worse_than_r15
                    else "不高于 r15 基线（维持）"),
            },
            "verdict": verdict,
            "letter_branch": letter_branch,
            "bottom_courtyard_detail_r16": [
                {"instance": r["instance"],
                 "courtyard_non_abstain_count": by_instance[r["instance"]],
                 "note": r["note"]}
                for r in SIDE_OBS_REGISTERED],
            "baseline_cross_check": {
                "r14_top_registered": BASE14_TOP_AGGREGATE_REGISTERED,
                "r14_top_live": f"{base14_ab}/{base14_fl}",
                "r15_top_registered": BASE15_TOP_AGGREGATE_REGISTERED,
                "r15_top_live": f"{base15_ab}/{base15_fl}",
                "r15_bottom_registered": BASE15_BOTTOM_AGGREGATE_REGISTERED,
                "r15_bottom_live": f"{base15_bot_ab}/{base15_bot_fl}",
                "r15_bottom_courtyard_registered":
                    R15_BOTTOM_COURTYARD_BASELINE,
                "r15_bottom_courtyard_live": r15_courtyard_base,
                "note": ("两侧基线数字与 run-r14/run-r15 内嵌输入重放实测"
                         "交叉核对一致（fail-closed：live 重放与登记不符"
                         "即 FAIL）；registered=r16-prep-record 在案登记/"
                         "判据原文冻结值，live=本轮从 run-doc 内嵌输入"
                         "重放实测"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "top 视角非弃权旗标面积比出局条目 R15=%d→R16=%d"
                    "（变化如实记录；guard_ok=%s）——r16-prep-record "
                    "guard_channel 无数值要件（「变化如实记录」）、独立"
                    "单列，与三分判据分开、不合并"
                    % (len(geo_r15), len(geo_r16), guard_ok)),
                "guard_ok": guard_ok,
                "note": ("守门通道按 r16-prep-record attribution_plan."
                         "guard_channel 独立复核（几何门面积比出局条目"
                         "变化如实记录）；不构成 r16 字母裁决输入"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r15 run-record courtyard_tracking 在案先例延续，"
                "r16-prep-record 未另设 secondary_observation 节）——"
                "实测见 courtyard_tracking 节"),
            "aggregate_context": {
                "abstain_rate_r9":
                    run_r9["aggregation"]["abstain_rate_total"],
                "abstain_rate_r10":
                    run_r10["aggregation"]["abstain_rate_total"],
                "abstain_rate_r11_representative":
                    run_r11["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r12_representative":
                    run_r12["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r13_representative":
                    run_r13["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r14_representative":
                    run_r14["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r15_representative":
                    run_r15["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r16_representative_note": (
                    "代表配置聚合弃权率见 aggregation_representative."
                    "abstain_rate_total（本轮聚合口径按 measurement_design "
                    "五条预注册执行，代表配置/逐实例/双口径分列）"),
                "apr0011_joint_evaluation_representative_note": (
                    "APR-0011 联合门按代表配置独立计算，结果见 "
                    "compliance_representative.joint_evaluation（与字母"
                    "裁决分列不合并）"),
                "note": (
                    "跨轮聚合弃权率（口径分列如实）：r9 0.727273（8/11，"
                    "全旗标）→r10 0.285714（4/14，全旗标）→r11 0.133333"
                    "（2/15，代表配置）→r12 0.9（9/10，代表配置）→r13 "
                    "0.909091（10/11，代表配置）→r14 0.833333（10/12，"
                    "代表配置）→r15 0.785714（11/14，代表配置）→r16 见"
                    "代表配置分列；主通道三分判据与门各自独立计算、互不"
                    "凌驾（prep-record descriptive_boundary_note 原文"
                    "语义）——门联合评价与字母裁决分列不合并"),
            },
            "r16_total_flags_note": (
                "六实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；top 全旗聚合弃权率"
                " %d/%d=%s 为三分判据度量、bottom 全旗聚合弃权率 %d/%d=%s"
                " 为侧观察度量、各自单列）"
                % (n_total_all,
                   (flags_top - abst_top) + (flags_bot - abst_bot),
                   abst_top + abst_bot,
                   cal._ratio(abst_top + abst_bot, n_total_all),
                   abst_top, flags_top, top_rate,
                   abst_bot, flags_bot, bot_rate)),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"support=「{prep_doc['attribution_plan']['primary_channel']['support']}」；"
            f"reject=「{prep_doc['attribution_plan']['primary_channel']['reject']}」；"
            f"inconclusive=「{prep_doc['attribution_plan']['primary_channel']['inconclusive']}」"
            "（r16-prep-record.json hypothesis_test.adjudication 判据原文"
            "，轮后如实执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r16": {
            "role": ("r12 假设通道被动追踪（round13/round14/round15-dev-"
                     "record 在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r16": reroute_rows,
            "reroute_total_r16": len(reroute_rows),
            "reroute_by_instance_r16": {
                n: sum(1 for d in instances[n]["per_flag_gt_detail"]
                       if d["category"] == "suspicious_reroute")
                for n in INSTANCE_ORDER},
            "production_chain": {"r8": REROUTE_CHAIN_PRIOR["r8"],
                                 "r9": REROUTE_CHAIN_PRIOR["r9"],
                                 "r10": REROUTE_CHAIN_PRIOR["r10"],
                                 "r11": REROUTE_CHAIN_PRIOR["r11"],
                                 "r12": REROUTE_CHAIN_PRIOR["r12"],
                                 "r13": REROUTE_CHAIN_PRIOR["r13"],
                                 "r14": REROUTE_CHAIN_PRIOR["r14"],
                                 "r15": REROUTE_CHAIN_PRIOR["r15"],
                                 "r16": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径）：r10=2→r11=1→r12=0→"
                "r13 被动追踪=1（R13T-009 在案）→r14=0（R14T-004 子串零"
                "命中）→r15 机械命中=1（R15T-001 非弃权旗含「蛇形」"
                "子串——否定式援引、非滥用型引用，run-r15 在案）→r16=0"
                "（R16T-004 两旗「等长|蛇形」子串零命中、均为存在性"
                "弃权）——不构成 r16 判据输入（两判据分列互不凌驾）"),
        },
        "stratified_observation": {
            "top": {"r15_by_instance_live": r15_top_rates,
                    "r15_range_live": r15_top_range,
                    "r16_by_instance": top_rates,
                    "r16_range": top_range,
                    "direction": ("r15 三实例 %s（轮内极差 %s）→r16 三"
                                  "实例 %s/%s/%s（轮内极差 %s）——同指引"
                                  "重复轮、top 渲染零变更下实例群重抽的"
                                  "方向性对照（聚合 %d/%d=%s vs r15 的 "
                                  "25/29=0.862069；两基线之间=三分判据 "
                                  "(c) 支的构成；轮内实例差异照旧）"
                                  % (f"{r15_top_rates['top-i1']}/"
                                     f"{r15_top_rates['top-i2']}/"
                                     f"{r15_top_rates['top-i3']}",
                                     r15_top_range,
                                     top_rates["top-i1"],
                                     top_rates["top-i2"],
                                     top_rates["top-i3"], top_range,
                                     abst_top, flags_top, top_rate))},
            "bottom": {"r15_by_instance_live": r15_bottom_rates,
                       "r15_range_live": r15_bottom_range,
                       "r16_by_instance": bottom_rates,
                       "r16_range": bottom_range,
                       "direction": ("r15 三实例 %s（极差 %s）→r16 三"
                                     "实例 %s/%s/%s（极差 %s）——bottom "
                                     "聚合 %d/%d=%s vs r15 的 11/13="
                                     "0.846154（侧观察如实单列；实例群"
                                     "重抽下方向性描述）"
                                     % (f"{r15_bottom_rates['bottom-i1']}/"
                                        f"{r15_bottom_rates['bottom-i2']}/"
                                        f"{r15_bottom_rates['bottom-i3']}",
                                        r15_bottom_range,
                                        bottom_rates["bottom-i1"],
                                        bottom_rates["bottom-i2"],
                                        bottom_rates["bottom-i3"],
                                        bottom_range,
                                        abst_bot, flags_bot, bot_rate))},
            "confounder_note": (
                "跨轮 reader 实例不同（本轮=全部重抽、恰为裁决变量）+"
                "轮内实例差异=混杂因素照旧声明；v1.2 工具规约把工具行为"
                "钉住（12/12 自述「未读取盘上任何其他文件」）但判读实例"
                "仍为不同实例；每视角 n=3 仍为小样本；development 域"
                "方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r11: dict, run_r12: dict, run_r13: dict,
                             run_r14: dict, run_r15: dict) -> dict:
    """courtyard 被动追踪（r11–r15 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r16 courtyard 类旗标与命中如实入账
    ——bottom courtyard 类 2 条（applied-bottom-i2 黑点-轮廓近邻，全部
    弃权）在 r15 零旗标后部分再现）。"""
    note_source = {
        "path_rel": REL_PREP_R16, "sha256": _sha(REL_PREP_R16),
        "quote": None,
        "note": ("r16-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r15 "
                 "在案），零期望、零阈值改动照旧，不为提高命中调阈值")}
    non_abstain_rows, abstain_rows = [], []
    for n in INSTANCE_ORDER:
        rec = instances[n]
        matched_ids = {m["flag_id"]: m
                       for m in rec["combined"]["matches_detail"]}
        for d in rec["per_flag_gt_detail"]:
            if d["category"] != "courtyard_crowding":
                continue
            if d["abstain"]:
                abstain_rows.append({"flag_id": d["flag_id"],
                                     "instance": n, "state": d["state"],
                                     "view": rec["view"]})
                continue
            overlaps = d["gt_overlaps"]
            ars = [o["area_ratio"] for o in overlaps
                   if o["area_ratio"] is not None]
            m = matched_ids.get(d["flag_id"])
            non_abstain_rows.append({
                "flag_id": d["flag_id"], "instance": n,
                "state": d["state"], "view": rec["view"],
                "gt_entries_checked": len(
                    rec["states"][d["state"]]["gt_entries"]),
                "containment_all_none": d["containment_all_none"],
                "area_ratio_min": min(ars) if ars else None,
                "area_ratio_max": max(ars) if ars else None,
                "matches": 1 if m else 0,
                "matched_detail": (
                    {"gt_id": m["gt_id"], "state": m["state"],
                     "containment": m["containment"],
                     "area_ratio": m["area_ratio"]} if m else None)})
    non_abstain_rows.sort(key=lambda r: (r["instance"], r["state"],
                                         r["flag_id"]))
    abstain_rows.sort(key=lambda r: (r["instance"], r["state"],
                                     r["flag_id"]))
    prior = run_r15["courtyard_tracking"]
    top_abstain_cnt = sum(1 for r in abstain_rows
                          if r["instance"].startswith("top"))
    bot_abstain_cnt = sum(1 for r in abstain_rows
                          if r["instance"].startswith("bottom"))
    bot_flags_total = sum(instances[n]["combined"]["flag_count"]
                          for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    bot_abstain_total = sum(instances[n]["combined"]["abstain_count"]
                            for n in ("bottom-i1", "bottom-i2",
                                      "bottom-i3"))
    bot_nonabstain_total = bot_flags_total - bot_abstain_total
    return {
        "note_source": note_source,
        "declaration": ("被动追踪（run-record 链先例延续）：如实记录 "
                        "courtyard 类旗标匹配表现"
                        "（零阈值改动、零期望、不得为提高命中调阈值）"),
        "r16_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（bottom=applied-bottom-i2 黑点-椭圆 "
                             "courtyard 轮廓相切/近邻 2 条——r14 同族"
                             "现象部分再现、r15 零旗标后未再现→部分"
                             "再现，如实登记；见 hypothesis_test."
                             "mechanism_observation."
                             "bottom_side_observation_maintenance）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r16": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r15": prior["courtyard_matches_r15"],
        "courtyard_matches_r15_detail": (
            "R15 非弃权 courtyard 0 条（6 条 courtyard 类旗标全部弃权="
            "全部 top、bottom 零 courtyard 类旗标）零命中（run-r15 在案）"),
        "courtyard_matches_r14": prior["courtyard_matches_r14"],
        "courtyard_matches_r14_detail": (
            "R14 非弃权 courtyard 0 条（17 条 courtyard 类旗标全部弃权="
            "top 13+bottom 4）零命中（run-r14 在案）"),
        "courtyard_matches_r13": prior["courtyard_matches_r13"],
        "courtyard_matches_r13_detail": (
            "R13 非弃权 courtyard 0 条（8 条弃权全部 top、bottom 零 "
            "courtyard 类旗标）零命中（run-r13 在案，run-r14 转录在案）"),
        "courtyard_matches_r12": prior["courtyard_matches_r12"],
        "courtyard_matches_r12_detail": (
            "R12 非弃权 courtyard 20 条零命中（bottom 18 条因 GT 全部 "
            "side=top 无从命中；run-r12 在案，run-r13 转录在案）"),
        "courtyard_matches_r11": prior["courtyard_matches_r11"],
        "courtyard_matches_r11_detail": (
            "R11 非弃权 courtyard 14 条中 3 条命中（top-i1 R11T-009↔"
            "GT-REVC-P1-R4J3、top-i3 R11T-010↔GT-REVC-AP-1-R5U6/R11T-003"
            "↔GT-REVC-AP-6-R2LED2；run-r11 在案，run-r13 转录在案）"),
        "courtyard_matches_r10": prior["courtyard_matches_r10"],
        "courtyard_matches_r10_detail": (
            "R10T-011↔GT-REVC-P1-R4J3（containment 0.829864、面积比 "
            "1.770688；run-r10 在案，run-r13 转录在案）"),
        "courtyard_matches_r9": prior["courtyard_matches_r9"],
        "courtyard_matches_r9_detail": (
            "R9 top 非弃权 courtyard 2 条与同态 GT 零交集、弃权 2 条；"
            "run-r9 在案，run-r13 转录在案"),
        "courtyard_matches_r8": prior["courtyard_matches_r8"],
        "courtyard_matches_r8_detail": (
            "R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、面积比 "
            "2.688288；run-r8 在案，run-r13 转录在案）"),
        "same_domain_note": (
            "r11 三条 courtyard 命中与 r8 R8T-004、r10 R10T-011 同域"
            "（Y1/R4J3 类 courtyard 密集区）——r12–r15 连续零再现"
            "（r15 非弃权 courtyard=0 条）；r16 非弃权 courtyard=%d 条"
            "（命中=%d，如实登记）；GT/阈值零改动"
            % (len(non_abstain_rows),
               sum(r["matches"] for r in non_abstain_rows))),
        "bottom_observation": {
            "fact": ("R16 bottom %d 旗（bottom-i1 5+bottom-i2 5+"
                     "bottom-i3 4）=非弃权 %d（placement/孤立图形类）+"
                     "弃权 %d："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=2（applied-bottom-i2 黑点"
                     "-轮廓近邻、全部弃权——r14 弃权 4 条/r15 零旗标/"
                     "r16 有旗全弃权 2 条，逐轮构成如实分列）；弃权"
                     "构成见 reader.flag_count.by_category；本轮 12 格"
                     "全部≥1 旗、无零旗标分母实例"
                     "（measurement_design item 5 口径保留备用：遇零"
                     "分母→None 不编造数值）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
            "evidence": QUANT_CRITERION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）——bottom 六派次"
                               "仍按 §4(i) 把绿色翼瓣/空隙形态判入系统性"
                               "正常路径（不进 flags）"),
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r14 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}

    rejections = []
    for key in RAW_FILES:
        for img in parsed[key]["images"]:
            for r in img["rejected"]:
                rejections.append({"file": key, **r})
    for key in RAW_FILES:
        if not parsed[key]["images"]:
            _fail(f"reader-raw per_image 空: {key}")

    deriv = _json_load(REL_DERIV_R5)
    gt_applied = _gt_entries_with_r5_reprojection(REL_GT_V2, deriv)
    gt_prep1 = _gt_entries_with_r5_reprojection(REL_GT_V1, deriv)
    if len(gt_applied) != 9 or len(gt_prep1) != 4:
        _fail("GT 条目数不符（applied=9、prep1=4）")

    instances = {name: build_instance_record(name, INSTANCES[name], parsed,
                                             gt_applied, gt_prep1)
                 for name in INSTANCE_ORDER}
    view_layer = build_view_layer(instances)
    gt_dual = build_gt_dual(instances, gt_applied, gt_prep1)

    # 实例态块平铺（供通道归因重放；带定位元数据）
    inst_blocks = []
    for name in INSTANCE_ORDER:
        for st, part in (("applied", INSTANCES[name]["parts"][0]),
                         ("prep1", INSTANCES[name]["parts"][1])):
            blk = dict(instances[name]["states"][st])
            blk["_part_key"] = part
            blk["_instance"] = name
            blk["_state"] = st
            inst_blocks.append(blk)
    inst_replays = {
        blk["_part_key"]: channel_replay(blk["reader_flags"],
                                         blk["flag_views"],
                                         blk["gt_entries"])
        for blk in inst_blocks}

    # 代表配置（measurement_design item 4）：每视角 flag_count 中位数实例
    rep = pick_representative(instances)
    top_name = rep["members"]["top"]
    bot_name = rep["members"]["bottom"]
    rep_appl = _merge_state_blocks(
        [dict(instances[top_name]["states"]["applied"],
              members_note=f"{top_name}/applied-top（{top_name}）"),
         dict(instances[bot_name]["states"]["applied"],
              members_note=f"{bot_name}/applied-bottom（{bot_name}）")],
        "applied", "ASM-7 终检后终态（代表配置）", gt_applied)
    rep_prep = _merge_state_blocks(
        [dict(instances[top_name]["states"]["prep1"],
              members_note=f"{top_name}/prep1-top（{top_name}）"),
         dict(instances[bot_name]["states"]["prep1"],
              members_note=f"{bot_name}/prep1-bottom（{bot_name}）")],
        "prep1", "ASM-P1 批前快照（种子域；代表配置）", gt_prep1)
    agg = _aggregate(rep_prep, rep_appl)
    comp = _compliance(agg)
    metric_ranges = build_metric_ranges(instances)

    run_r6 = _json_load(REL_RUN_R6)
    run_r7 = _json_load(REL_RUN_R7)
    run_r8 = _json_load(REL_RUN_R8)
    run_r9 = _json_load(REL_RUN_R9)
    run_r11 = _json_load(REL_RUN_R11)
    run_r12 = _json_load(REL_RUN_R12)
    run_r13 = _json_load(REL_RUN_R13)
    run_r14 = _json_load(REL_RUN_R14)
    run_r15 = _json_load(REL_RUN_R15)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, run_r15, instances,
                                view_layer, attribution, raw_texts,
                                parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9,
                                         run_r11, run_r12, run_r13,
                                         run_r14, run_r15)

    prep_r16 = _json_load(REL_PREP_R16)
    serial = list(RAW_FILES)
    by_view = {"top": 0, "bottom": 0}
    abst_by_view = {"top": 0, "bottom": 0}
    by_category: dict = {}
    abstain_by_instance = {}
    reroute_by_instance = {n: 0 for n in INSTANCE_ORDER}
    for name in INSTANCE_ORDER:
        abstain_by_instance[name] = instances[name]["combined"][
            "abstain_count"]
        reroute_by_instance[name] = sum(
            1 for d in instances[name]["per_flag_gt_detail"]
            if d["category"] == "suspicious_reroute")
        for st in ("applied", "prep1"):
            blk = instances[name]["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            for fid, view in blk["flag_views"].items():
                by_view[view] += 1
                if fid in abst:
                    abst_by_view[view] += 1
            for f in blk["reader_flags"]:
                cell = by_category.setdefault(f["category"],
                                              {"total": 0, "non_abstain": 0,
                                               "abstain": 0})
                cell["total"] += 1
                if f["flag_id"] in abst:
                    cell["abstain"] += 1
                else:
                    cell["non_abstain"] += 1
    n_total = sum(instances[n]["combined"]["flag_count"]
                  for n in INSTANCE_ORDER)
    zero_flag_parts = [
        {"instance": n, "state": st,
         "flag_count": len(instances[n]["states"][st]["reader_flags"])}
        for n in INSTANCE_ORDER for st in ("applied", "prep1")
        if not instances[n]["states"][st]["reader_flags"]]
    reader_block = {
        "dispatch_discipline": DISPATCH_DISCIPLINE,
        "dispatch_mode": DISPATCH_MODE,
        "reader_ids": {k: parsed[k]["reader_id"] for k in serial},
        "raw_files": {k: {"path_rel": RAW_FILES[k], "sha256": _sha(RAW_FILES[k])}
                      for k in serial},
        "parse": {k: {"direct_json_parse": parsed[k]["direct_json_parse"],
                      "repair": parsed[k]["repair"],
                      "raw_message_format_note": RAW_MESSAGE_FORMAT_NOTES[k],
                      "flag_count": sum(len(i["flags"])
                                        for i in parsed[k]["images"]),
                      "rejected_count": sum(len(i["rejected"])
                                            for i in parsed[k]["images"])}
                  for k in serial},
        "flag_count": {
            "by_instance": {n: instances[n]["combined"]["flag_count"]
                            for n in INSTANCE_ORDER},
            "abstain_by_instance": abstain_by_instance,
            "by_state": {"applied": sum(
                len(instances[n]["states"]["applied"]["reader_flags"])
                for n in INSTANCE_ORDER),
                "prep1": sum(len(instances[n]["states"]["prep1"][
                    "reader_flags"]) for n in INSTANCE_ORDER)},
            "by_view": {"top": by_view["top"], "bottom": by_view["bottom"]},
            "abstain_by_view": {"top": abst_by_view["top"],
                                "bottom": abst_by_view["bottom"]},
            "by_category": by_category,
            "reroute_by_instance": reroute_by_instance,
            "reroute_class_production": sum(reroute_by_instance.values()),
            "total": n_total,
        },
        "reader_instance_note": READER_INSTANCE_NOTE,
        "location_evidence_note": (
            "location_evidence 保留于 raw 原文（hash 在案），不进度量"
            "五键投影（process-v1 §2 步骤3）；R16 reroute 类两旗 "
            "location_evidence 逐字在案（R16T-004 prep1-top-i1+R16T-004 "
            "prep1-top-i3，均为存在性弃权、「等长|蛇形」子串零命中——"
            "reroute_continuation_r16 逐旗判定在案）；"
            "R16 top 弃权旗 27 条逐旗分型摘录在案（top_abstain_typology："
            "接触性 11+存在性 15+层归属其他 1）；"
            "bottom 黑点类/placement 处置弃权旗摘录在案（black_dot_"
            "tracking/residual_instance_differences）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "zero_flag_parts": {
            "parts": zero_flag_parts,
            "note": ("本轮 12 格全部≥1 旗（无零旗标格；最小格=prep1-"
                     "bottom-i3 单旗）——实例层/视角层弃权率全部有定义；"
                     "measurement_design item 5 口径保留备用（遇零旗标"
                     "分母→按库侧 cal._ratio 先例=None+文字说明，不编造"
                     "数值）"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R16, "role": "r16_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R16)},
        {"path_rel": REL_DEV_R15,
         "role": "r15_dev_record_preregistration_source",
         "sha256": _sha(REL_DEV_R15)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R15,
         "role": "observation_guidance_r15_active_byte_reuse",
         "sha256": _sha(REL_GUIDANCE_R15)},
        {"path_rel": REL_GUIDANCE_R13,
         "role": "observation_guidance_r13_lineage_base",
         "sha256": _sha(REL_GUIDANCE_R13)},
        {"path_rel": REL_GUIDANCE_R12,
         "role": "observation_guidance_r12_baseline",
         "sha256": _sha(REL_GUIDANCE_R12)},
        {"path_rel": REL_GUIDANCE_R9,
         "role": "observation_guidance_r9_chain",
         "sha256": _sha(REL_GUIDANCE_R9)},
        {"path_rel": REL_GUIDANCE_R8, "role": "observation_guidance_r8_chain",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_FRAMING_R14B,
         "role": "render_framing_r14b_byte_reuse_provenance",
         "sha256": _sha(REL_FRAMING_R14B)},
        {"path_rel": REL_WITNESS_R14B,
         "role": "render_witness_r14b_byte_reuse_witness",
         "sha256": _sha(REL_WITNESS_R14B)},
        {"path_rel": REL_DEV_R14,
         "role": "r14_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R14)},
        {"path_rel": REL_DEV_R13,
         "role": "r13_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R13)},
        {"path_rel": REL_DEV_R12,
         "role": "r12_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R12)},
        {"path_rel": REL_PREP_R13, "role": "r13_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R13)},
        {"path_rel": REL_PREP_R12, "role": "r12_prep_record_witness_source",
         "sha256": _sha(REL_PREP_R12)},
        {"path_rel": REL_DEV_R11, "role": "r11_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R11)},
        {"path_rel": REL_PREP_R11, "role": "r11_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R11)},
        {"path_rel": REL_DEV_R10, "role": "r10_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R10)},
        {"path_rel": REL_PREP_R10, "role": "r10_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R10)},
        {"path_rel": REL_DEV_R9, "role": "r9_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R9)},
        {"path_rel": REL_PREP_R9, "role": "r9_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R9)},
        {"path_rel": REL_DEV_R8, "role": "r8_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R8)},
        {"path_rel": REL_PREP_R8, "role": "r8_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R8)},
        {"path_rel": REL_PREP_R7, "role": "r7_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R7)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_top_pixel_provenance",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_GT_AUDIT, "role": "gt_audit_r1_closed",
         "sha256": _sha(REL_GT_AUDIT)},
        {"path_rel": PDF_FILES["applied-top"],
         "role": "source_image_pdf_applied_top_r4",
         "sha256": _sha(PDF_FILES["applied-top"])},
        {"path_rel": PDF_FILES["applied-bottom"],
         "role": "source_image_pdf_applied_bottom_r4",
         "sha256": _sha(PDF_FILES["applied-bottom"])},
        {"path_rel": PDF_FILES["prep1-top"],
         "role": "source_image_pdf_prep1_top_r4",
         "sha256": _sha(PDF_FILES["prep1-top"])},
        {"path_rel": PDF_FILES["prep1-bottom"],
         "role": "source_image_pdf_prep1_bottom_r4",
         "sha256": _sha(PDF_FILES["prep1-bottom"])},
        {"path_rel": PNG_FILES["applied-top"],
         "role": "render_png_applied_top_r16_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r16_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"],
         "role": "render_png_prep1_top_r16_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r16_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r16",
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "declared_date": DECLARED_DATE,
        "metric_version": cal.METRIC_VERSION_V3,
        "evaluation_domain": EVALUATION_DOMAIN,
        "evaluation_domain_note": {
            "declared": EVALUATION_DOMAIN,
            "basis_quote": DOMAIN_BASIS_QUOTE,
            "in_calibrated_range": False,
            "in_calibrated_range_note": (
                "development 域迭代轮不构成留出证据；正式采纳前 "
                "in_calibrated_range 恒 False（协议 v1 §1/§4；v1.2 规约"
                "沿用其对门的评价含义不变）"),
            "protocol_ref": {"path_rel": REL_PROTOCOL,
                             "sha256": _sha(REL_PROTOCOL)},
        },
        "instrument_change": {
            "changed": False,
            "nature": INSTRUMENT_NATURE,
            "note": prep_r16["instrument_change"]["note"],
            "components": [],
            "unchanged_components": list(prep_r16["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v["attribution_channel"],
                 "instrument_change": v["instrument_change"]}
                for v in prep_r16["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r16["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r16["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r16["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R16, "sha256": _sha(REL_PREP_R16)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；r15 指引 §6 示例旗 ID 前缀保持 R15T-/R15B-（r15 "
            "落盘原文、字节复用不改），R16 派次 R16T/R16B 前缀由派发"
            "指令层覆盖（per r16-prep-record protocol_amendment.naming："
            "与 r13→r15「随指引落盘固化」路径不同）；实例间编号独立；"
            "同实例两板各自从头编号=r16 实测输出行为、与 prep-record "
            "naming「同实例跨板连续」声明不同（与 r15 实测同形态），"
            "见 dispatch_mode.flag_id_continuity_note"),
        "coverage_caveat": cal.COVERAGE_CAVEAT_V3,
        "reader": reader_block,
        "instances": instances,
        "parse_rejections": rejections,
        "view_layer": view_layer,
        "gt_match_dual": gt_dual,
        "representative_configuration": rep,
        "aggregation_representative": agg,
        "compliance_representative": comp,
        "metric_ranges_instance": metric_ranges,
        "parallel_record_note": (
            "measurement_design item 4 三者并列如实呈现（不合并、不挑优）："
            "①代表配置 joint 结果（aggregation_representative/"
            "compliance_representative）；②per-metric 实例间范围"
            "（metric_ranges_instance）；③逐实例原始记录（instances，"
            "measurement_design item 1）——另有 GT 匹配双口径"
            "（gt_match_dual，item 3）与视角层三分列（view_layer，"
            "item 2）并列"),
        "hypothesis_test": hyp,
        "channel_attribution": attribution,
        "courtyard_tracking": courtyard,
        "gt_audit_reference": {
            "path_rel": REL_GT_AUDIT, "sha256": _sha(REL_GT_AUDIT),
            "note": ("只读 GT 源审计（gt-audit-r1，2026-09-07，"
                     "sha 1f20554a…）：bottom GT=无源已关闭、reroute GT="
                     "无源已关闭、L1NB 框径=合理维持现框——GT 侧三候选"
                     "全部关闭（r8 轮同日审计，结论 r9–r13 延续引用）；该"
                     "审计非本轮预注册件（deviations 在案），其结论维持"
                     "本轮 GT 零改动；bottom 旗标与 GT 匹配应为空"
                     "（结构性：GT 13 条全部 side=top）；round12-dev-"
                     "record gt_audit_ref/next_iteration_targets 引用其"
                     "结论（GT 侧已全部关闭）"),
        },
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r12 相同；"
                                   "只作口径引用，APR-0011 阈值零改动）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r13 指引 §4（经 r15 指引字节复用原文适用，本轮指引"
                    "=observation-guidance-r15.md 零字节不动）："
                    "r8 两条显式判据"
                    "（弃权适用于存在/归类不确定；弃权不适用于仅范围不确定）、"
                    "存在性判断一般判据引导句与三路出口显式化原文保留；§4 "
                    "存在性判断一般判据=量化版 (i)(ii)(iii)（(i) 系统性正常"
                    "特征判据（量化）：最小重复单元至少 3 处+沿同一阵列或"
                    "成组对齐+至少 2 条不同阵列/边+形态尺寸样式一致→更可能"
                    "正常设计特征；计数以最小重复单元为准、联合交叠外观不得"
                    "替代单元级计数、成对出现率不构成否定系统性的依据；"
                    "(ii) 关注现象判据：孤立出现（仅 1–2 处）或不一致或"
                    "形态明显不一致→更可能关注现象；(iii) 接触性判据："
                    "真实接触 vs 视觉贴近不可区分→按存在性弃权，不得将"
                    "视觉贴近直接计为交叠）；量化阈值为一般判据、非期望"
                    "清单；反放宽条款原文保留；§3A 示例 c 收窄判据原文"
                    "适用；abstain=true=现象是否存在或归属哪类无法负责任"
                    "地判断；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("协议侧 v1.1 多实例口径沿用+v1.2 工具"
                                      "规约沿用（无新增版本）：12 次盲读="
                                      "4 视角格×3 实例（i1/i2/i3），两波次"
                                      "串行保序（同一实例先 applied 后 "
                                      "prep1）；每派次指令含 v1.2 硬性"
                                      "条款（禁止程序化图像处理、只允许 "
                                      "Read 直读原图）；零诊断/探针内容"
                                      "（渲染探针链与 framing/witness 记录"
                                      "不进任何 reader 上下文）、零 legend/"
                                      "零其他解释（同指引重复轮=判读输入"
                                      "与 r15 完全同构）；每图独立判读；跨"
                                      "实例/跨视角禁止交流（独立性亦为"
                                      "实例群重抽归因的前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R15,
                                 "sha256": _sha(REL_GUIDANCE_R15),
                                 "frozen_before_read": True,
                                 "byte_reuse_zero_change": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R13,
                                     "sha256": _sha(REL_GUIDANCE_R13),
                                     "role": ("r15 指引的机械变换基座"
                                              "（r15 指引=r16 轮字节复用"
                                              "本体；r13 指引=r13 轮落盘"
                                              "产物）")},
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：round15-dev-record.json（e981897c…，"
                 "next_iteration_targets[0] 同指引重复轮候选原文被 "
                 "r16-prep-record 逐字摘录预注册+用户 2026-09-08「继续"
                 "迭代到收敛」既定指令（user_directive_note 在案））→"
                 "r16-prep-record.json（46fbd15b…，本轮预注册件，"
                 "measurement_design 五条聚合口径与 hypothesis_test."
                 "adjudication 三分判据（≤0.75/≥0.862/两值之间）先于盲读"
                 "冻结；instrument_change.changed=false；"
                 "changed_variables=[]；manipulated_factor=reader 实例群"
                 "重抽）先于本轮盲读落盘（零 GT 暴露声明在案 "
                 "no_visual_reading=true；pre_round_review="
                 "not_required_zero_change_round——同指引重复轮先例 r10、"
                 "无新干预引入）→判读指引=observation-guidance-r15.md"
                 "（d5babc93…）字节复用零写入（本轮零新建指引文件；§2–§7 "
                 "判据与 §5A 仪器注记随本体原样生效）→渲染零变更"
                 "（renders-r14b 四图字节复用=四 PNG sha 与 witness 登记值"
                 "逐一相等，即 r14/r15 轮盲读所用同一批文件）→12 次盲读"
                 "（实例群全部重抽）→比对记录（读者产物零改动）。GT 重"
                 "投影（derivation-log-r5.json，13 条 frame_box_pct_r5）"
                 "已在案沿用（GT 全部 side=top 且 top 渲染零变更=重投影"
                 "输入未变；bottom 渲染字节复用不触及）；GT 冻结纪律："
                 "轮后未增删改；gt-audit-r1 结论维持 GT 零改动（三候选"
                 "关闭，gt_audit_reference 在案）。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "r7_run": {"path_rel": REL_RUN_R7, "sha256": _sha(REL_RUN_R7)},
            "r8_run": {"path_rel": REL_RUN_R8, "sha256": _sha(REL_RUN_R8)},
            "r9_run": {"path_rel": REL_RUN_R9, "sha256": _sha(REL_RUN_R9)},
            "r10_run": {"path_rel": REL_RUN_R10, "sha256": _sha(REL_RUN_R10)},
            "r11_run": {"path_rel": REL_RUN_R11, "sha256": _sha(REL_RUN_R11)},
            "r12_run": {"path_rel": REL_RUN_R12, "sha256": _sha(REL_RUN_R12)},
            "r13_run": {"path_rel": REL_RUN_R13, "sha256": _sha(REL_RUN_R13)},
            "r14_run": {"path_rel": REL_RUN_R14, "sha256": _sha(REL_RUN_R14)},
            "r15_run": {"path_rel": REL_RUN_R15, "sha256": _sha(REL_RUN_R15)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）与 R9"
                     "（§3A 示例 c 增补轮）与 R10（零变更重复轮）与 R11"
                     "（协议侧单变量轮：每视角实例 1→3，v1.1 追加式）与 "
                     "R12（单变量指引侧变更轮：示例 c 收窄+协议侧派发层 "
                     "v1.2 首轮）与 R13（单变量指引侧变更轮：§4 存在性"
                     "判据可操作化+pre_round_review 评审前置）与 R14"
                     "（纯仪器变更轮：bottom 渲染件更换 renders-r5→"
                     "renders-r14b，verdict=reject）与 R15（指引侧单变量"
                     "轮：§5A 渲染配色仪器注记配套，verdict=reject）run "
                     "在案；R16=同指引重复轮（零变更：指引 r15 字节复用+"
                     "渲染 renders-r14b 字节复用+GT/阈值/协议零变更；"
                     "唯一操纵因子=reader 实例群重抽；r10 零变更重复轮"
                     "先例再现）；轮间对比"
                     "由后续 round16-dev-record（另包落盘）与 "
                     "channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取与通道重放为纯函数"
            "（六实例旗数 9/14/12/5/5/4→代表配置 top-i3+bottom-i1（top "
            "中位实例唯一；bottom 中位 5 为 i1/i2 tie、按先序取 bottom-i1 "
            "并如实注明）唯一可复算），无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-08-r16（事件序="
            "round15-dev-record（e981897c…，在案）→r16-prep-record"
            "（46fbd15b…，本轮预注册件，先于盲读冻结）→r15 指引字节"
            "复用零写入（d5babc93…，本轮唯一判读依据）→renders-r14b 四图"
            "字节复用（渲染零变更）→12 次盲读（实例群全部重抽）→比对"
            "记录；在案延续=gt-"
            "audit-r1 只读 GT 源审计（r8 轮落盘，本轮延续引用其结论，"
            "GT 零改动维持））"),
    }


def overwrite_guard(existing: "bytes | None", new: bytes) -> str:
    """防覆写护栏（纯函数）：无既有→write；字节等同→idempotent_skip；
    既有且不同→fail（fail-closed，绝不覆写）。"""
    if existing is None:
        return "write"
    return "idempotent_skip" if existing == new else "fail"


def _commit(path: Path, new_bytes: bytes, label: str) -> str:
    """落盘（护栏语义）：已存在且字节等同→幂等跳过（零覆写）；
    已存在且不同→FAIL；否则写入并回读自证。"""
    if path.exists():
        if overwrite_guard(path.read_bytes(), new_bytes) == "fail":
            _fail(f"{label} 已存在且与重建字节不同（防覆写护栏，"
                  "fail-closed；发布产物不可覆写）")
        return "idempotent_skip"
    path.write_bytes(new_bytes)
    if path.read_bytes() != new_bytes:
        _fail(f"回读不一致: {label}")
    return "written"


def _assert_observation_numbers(run_doc: dict, run_r8: dict, run_r9: dict,
                                run_r10: dict, run_r11: dict, run_r12: dict,
                                run_r13: dict, run_r14: dict, run_r15: dict,
                                parsed: dict, raw_texts: dict) -> None:
    """run-r16 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 9, "top-i2": 14, "top-i3": 12, "bottom-i1": 5,
                  "bottom-i2": 5, "bottom-i3": 4}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 6, "top-i2": 13, "top-i3": 8, "bottom-i1": 5,
                "bottom-i2": 4, "bottom-i3": 3}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 49:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.764706 \
            or agg["flag_count_total"] != 17 \
            or agg["abstain_count_total"] != 13:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "inconclusive":
        _fail("假设字母裁决与预注册判据复算不符")
    m = hyp["measurement"]
    if m["top_abstain_flags_r16"] != 35 or m["top_abstain_count_r16"] != 27 \
            or m["top_abstain_rate_r16"] != 0.771429:
        _fail("主通道 top 计数与实测不一致")
    if m["crit_a_top_le_r14_baseline"] is not False \
            or m["crit_b_top_ge_r15_baseline"] is not False:
        _fail("三分判据布尔与实测不一致（27/35=0.771429 应落 (c) 支）")
    if m["top_abstain_rate_r14_baseline_value"] != 0.75 \
            or m["top_abstain_rate_r15_baseline_value"] != 0.862069:
        _fail("两侧基线值与在案登记不一致")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r16"] != 2 \
            or bso["bottom_abstain_flags_r16"] != 14 \
            or bso["bottom_abstain_count_r16"] != 12 \
            or bso["bottom_abstain_rate_r16"] != 0.857143 \
            or bso["bottom_courtyard_non_abstain_by_instance_r16"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail("bottom 侧观察计数与实测不一致")
    mo = hyp["mechanism_observation"]
    tt = mo["top_abstain_typology"]
    if tt["type_counts"] != {"contact": 11, "existence": 15,
                             "other_layer": 1} \
            or tt["top_abstain_flags_total"] != 27:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 12 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 1, "top-i2": 1, "top-i3": 0,
                                     "bottom-i1": 3, "bottom-i2": 4,
                                     "bottom-i3": 3}:
        _fail("黑点类计数与实测不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if not all(v["§5A_cited"] for v in gs.values()):
        _fail("绿区语义化 §5A 引用与实测不一致")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.261904 \
            or vl["bottom"]["abstain_rate_range"] != 0.25:
        _fail("视角层极差与实测不一致")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 1 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.076923:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != [("R16T-001", "GT-REVC-AP-6-R2LED2")]:
        _fail("matches 明细与实测不一致（r16 应恰 1 条：top-i2 R16T-001"
              "×GT-REVC-AP-6-R2LED2）")
    if reroute_production(run_r8["states"]) != REROUTE_CHAIN_PRIOR["r8"] \
            or reroute_production(run_r9["states"]) != REROUTE_CHAIN_PRIOR["r9"] \
            or reroute_production(run_r10["states"]) != REROUTE_CHAIN_PRIOR["r10"] \
            or run_r11["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r11"] \
            or run_r12["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r12"] \
            or run_r13["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r13"] \
            or run_r14["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r14"] \
            or run_r15["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r15"] \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 2:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R15 0→R16 0；类别 R15 0→R16 1）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r16_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r16_category_mismatch_entries"]) != 1:
        _fail("通道条目数与实测声明不一致")
    # courtyard 追踪与实测一致（r16 非弃权 courtyard=1、弃权=14、命中=1）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r16"] != 1 or len(
            ct["r16_courtyard_flags"]["non_abstain"]) != 1:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r16_courtyard_flags"]["abstain"]) != 14:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 逐旗判定/工具规约/量化判据/分型/黑点/placement/绿区摘录逐字在案
    for r in hyp["reroute_continuation_r16"]["reroute_flag_detail_r16"]:
        if r["form_desc_excerpt"] not in raw_texts[r["source"]]:
            _fail(f"逐旗判定摘录与 reader 原文不符: {r['flag_id']}")
    for ev in mo["bottom_side_observation_maintenance"][
            "reader_note_evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["green_semantics_by_instance"]["evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"绿区语义化摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["top_abstain_typology"]["rows"]:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"top 弃权分型摘录与 reader 原文不符: {ev['flag_id']}")
    for ev in mo["black_dot_tracking"]["evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"黑点类摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in mo["residual_instance_differences"]["evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"placement 处置摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in run_doc["courtyard_tracking"]["bottom_observation"]["evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"bottom 量化判据摘录与 reader 原文不符: {ev['source']}")


def main() -> None:
    # 输入先验锚（fail-closed）
    for rel, want in FROZEN_SHA256.items():
        p = _rel(rel)
        if not p.is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")
        got = _sha(rel)
        if got != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {got[:8]}…≠{want[:8]}…")

    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r16")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), _json_load(REL_RUN_R15),
        parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R16), run_bytes,
                         "calibration-run-r16.json")
    run_sha = _sha(REL_RUN_R16)
    # round16-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s58-cal-r16] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 10、弃权 39）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s58-cal-r16] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s58-cal-r16] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s58-cal-r16] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}")
    print(f"[s58-cal-r16] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s58-cal-r16] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    m = hyp["measurement"]
    print(f"[s58-cal-r16] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；三分判据=top 全旗聚合弃权率 "
          f"{m['top_abstain_count_r16']}/{m['top_abstain_flags_r16']}"
          f"={m['top_abstain_rate_r16']}；(a) 支 ≤0.75（run-r14 基线双侧复算 "
          f"{m['top_abstain_rate_r14_baseline_live']}"
          f"={m['top_abstain_rate_r14_baseline_value']}）→crit_a="
          f"{m['crit_a_top_le_r14_baseline']}；(b) 支 ≥0.862（run-r15 实测"
          f"双侧复算 {m['top_abstain_rate_r15_baseline_live']}"
          f"={m['top_abstain_rate_r15_baseline_value']}）→crit_b="
          f"{m['crit_b_top_ge_r15_baseline']}；落支={m['letter_branch']}"
          f"/guard_ok={m['guard_channel']['guard_ok']}；机制观察单列）")
    print(f"[s58-cal-r16] 侧观察（bottom 维持性，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r16']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r16']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r16']}"
          f" vs r15 基线 11/13=0.846154（{m['bottom_side_observation']['bottom_rate_direction_vs_r15']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r16']}"
          f"/courtyard 旗总数={m['bottom_side_observation']['bottom_courtyard_flags_total_r16']}")
    mo = hyp["mechanism_observation"]
    print(f"[s58-cal-r16] 机制观察要点：top 弃权分型="
          f"{mo['top_abstain_typology']['type_counts']}；黑点类 "
          f"{mo['black_dot_tracking']['by_instance']}（12 旗全弃权+2 派次"
          f" notes 判正常）；绿区语义化 §5A 提及="
          f"{ {k: v['§5A_cited'] for k, v in mo['green_semantics_by_instance']['green_semantics_by_instance'].items()} }；"
          f"reroute 2 旗全弃权（子串零命中）")
    print(f"[s58-cal-r16] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s58-cal-r16] channel_attribution: "
          f"geo R15={len(ca['channel_1_geometry_gate']['r15_area_ratio_rejected_entries'])}"
          f"→R16={len(ca['channel_1_geometry_gate']['r16_area_ratio_rejected_entries'])}, "
          f"cat R15={len(ca['channel_2_category_gate']['r15_category_mismatch_entries'])}"
          f"→R16={len(ca['channel_2_category_gate']['r16_category_mismatch_entries'])}")
    print(f"[s58-cal-r16] commit: run={run_status}（round16-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s58-cal-r16] sha256[:8] {Path(REL_RUN_R16).name} = "
          f"{run_sha[:8]}")
    print("[s58-cal-r16] R16 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
