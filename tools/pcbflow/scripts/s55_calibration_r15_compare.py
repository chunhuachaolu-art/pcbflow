#!/usr/bin/env python
"""CAL-R15-CLOSE：reader 判读迭代第十五轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s53_calibration_r14_compare.py 同构，仅输入与轮次
常量不同；R15=development 域指引侧单变量轮（指引侧颜色-图层映射配套
轮：判读指引由 observation-guidance-r13.md 机械变换生成 observation-
guidance-r15.md——本轮唯一判读依据；单变量=新增 §5A 渲染配色仪器注记
节（颜色→来源映射显式化：橙 (255,165,0)=白墨图元重着色（162 fill+4
stroke）、绿 (0,128,0)=板内空隙白重着色非图元；仪器事实注记、非判据）
+轮次标识机械同步；§2–§7 判据文本零变更（分段+substring 双重断言
复核，per r15-prep-record guidance_reuse.verification）；渲染零变更=
renders-r14b 四图字节复用（四 PNG sha 与 r14 轮盲读所用同一批文件
逐一相等）；instrument_change.changed=false 已预注册）+GT/阈值零
变更）；检验 r14 预注册候选假设（r14-dev-record-candidate-0-guidance-
color-legend，判据=r15-prep-record.json hypothesis_test.adjudication
三分判据预注册原文，脚本从 prep-record 文件加载判据文本、基线数字
live 重放不手工抄数）：

  T1  解析 12 个 reader-raw-r15-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r15-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r14 同一比较脚本血统）：(1) 实例主记录
      =六实例各自两板合计 flag_count/abstain_count/abstain_rate（6 位
      小数；零旗标分母=None）/非弃权清单（r15 flag_id 两板各自从头
      编号——非弃权/弃权清单按 (state, flag_id) 限定，跨板重号如实
      登记）/逐旗 containment+area_ratio 匹配明细；(2) 视角层=每视角
      3 实例 flag_count/abstain_rate/matches 各中位数+min+max 三分列
      不取整（本轮 12 格全部≥1 旗、弃权率全部有定义）；(3) GT 匹配
      双口径=union（≥1 实例命中）与 agreement（≥2/3）并列+逐 GT 条目
      matched_by_count（0..3；召回分母=GT 13 条）；(4) 联合门（APR-0011
      阈值零改动）=代表配置（每视角 flag_count 中位数实例；本轮 top
      中位实例唯一、bottom 中位 tie 取先序如实注明）算一轮 joint+
      per-metric 实例间范围+逐实例原始记录三者并列不挑优；(5) bottom
      零旗标分母=按库侧 cal._ratio 先例 None+文字说明（本轮 12 格
      全部≥1 旗、无 None 实例，口径保留备用）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且 top 渲染零
      变更（r15 top=renders-r14b 路径、字节内容=renders-r5、r14 已
      在案）故重投影输入未变；bottom 渲染字节复用 r14b 不触及 GT 重
      投影——bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（三分判据，r15-prep-record.json hypothesis_test.
      adjudication.supported_requires_all 原文）逐项执行：
      supported=(i)∧(ii)∧(iii) 全部满足；reject_if=(i) 不满足或
      (ii)(iii) 任一不满足。实测：(i) bottom courtyard 类旗标非弃权
      计数 0/0/0——r15 bottom 零 courtyard 类旗标（旗标全部为
      placement_pattern_anomaly/other_advisory），条件自动满足、分类
      通道转移如实记入机制观察（对照 r13/r14 的 0/0/0=全弃权路径，
      本轮=零旗标路径，成因三分如实分列）；(ii) bottom 全旗聚合弃权率
      =11/13=0.846154≤10/11（基线=calibration-run-r13.json 内嵌记录
      重放实测 10/11 交叉核对一致）满足；(iii) top 全旗聚合弃权率
      =25/29=0.862069>run-r14 同口径聚合弃权率（同一聚合逻辑对
      run-r14 内嵌实例记录双侧复算=18/24=0.75，不手工抄数）违约
      ⇒ verdict=reject（拒绝支=第三支 top 回退；r14→r15 top 弃权率
      0.75→0.862069 回升如实记录）。letter 裁决唯一正式；机制观察
      单列（绿区语义化按实例分布：r15 bottom 三实例 notes 均以
      「空隙/翼瓣」语义化绿色且 bottom-i2 两派次+bottom-i3 prep1
      显式援引 §5A 仪器注记、对照 r14 三实例三种语义化；黑点类 7 旗
      全弃权+3 派次 notes 判正常；bottom 零 courtyard 旗=分类通道
      转移；placement 类 6 旗两非弃权四弃权）；度量教训单列（prep-
      record metric_lesson_separate）。
      → calibration-run-r15.json。
  T3  development 域记录（R14→R15 方向性对照/假设裁决/联合评价趋势
      （r5→r15）/下一迭代目标）由后续 dev-record 包落盘（round15-dev-
      record，另包执行）；本包仅产出 run-r15、零 dev-record 写入。

通道归因纪律（vs R14；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53
deviation_note 口径）：本轮对 R13/R14 均以内嵌输入（reader_flags/
gt_entries/flag_views，run sha 在案）+ compare_v3 同源几何原语
（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R15 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「仅依据给定 PNG 可见内容独立判读，未读取盘
上任何其他文件」（12/12 在案）；r15 notes 无「未做任何裁剪/放大/像素
分析」逐字语句（与 r14 措辞差异如实登记；工具轴=派发指令 v1.2 硬性
条款照旧钉住）；跨轮实例不同+轮内实例差异=混杂因素照旧声明。输出格
式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件=缩进格式冻结
原始判读件、本轮零改动直读（direct JSON 解析、12 件 parse 校验全部
通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round15-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量 2026-09-08
/ 2026-09-08-r15）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s55_calibration_r15_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-08-r15"
ROUND_LABEL = "r15"
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
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DEV_R10 = "out/v3-tl2/calibration/round10-dev-record.json"
REL_DEV_R11 = "out/v3-tl2/calibration/round11-dev-record.json"
REL_DEV_R12 = "out/v3-tl2/calibration/round12-dev-record.json"
REL_DEV_R13 = "out/v3-tl2/calibration/round13-dev-record.json"
REL_DEV_R14 = "out/v3-tl2/calibration/round14-dev-record.json"
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
REL_FRAMING_R14B = "out/v3-tl2/calibration/render-framing-r14b.json"
REL_WITNESS_R14B = "out/v3-tl2/calibration/render-witness-r14b.json"

#: 12 份盲读原始件（6 实例×2 板；r15 flag_id 两板各自从头编号）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r15-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r15-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r15-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r15-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r15-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r15-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r15-prep1-bottom-i3.txt",
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
#: 四 PNG 锚=renders-r14b 四图（r15 字节复用=与 s53 在案锚同一批文件）；
#: 四 PDF 锚=r5 在案锚沿用（输入侧 PDF 未变）；
#: guidance-r15 锚=r15-prep-record.json guidance_reuse.derived_sha256
#: 全长（本轮新落盘冻结、本轮唯一判读依据）、guidance-r13 锚=其生成
#: 基座（c28806e1）、guidance-r12 锚=其 r12 在案锚；
#: prep-r15 锚=任务给定先验（盘上实测一致）=round14-dev-record 锚=
#: run-r14 锚（本轮 top 基线双侧复算的输入，run sha 在案）=framing-
#: r14b 锚=witness-r14b 锚；其余沿用 s53 在案锚。
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
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    RAW_FILES["applied-top-i1"]:
        "8514380684673c1aaa21a44ae409d8bd806c13152e07fa7baa82a15440c8450d",
    RAW_FILES["prep1-top-i1"]:
        "578fab5f33075d7e897ee388ab66f20e388a081b8b0d6b1d4a3ab67cf67deea9",
    RAW_FILES["applied-top-i2"]:
        "65905c7781ded3e05e8a7daf85998aa1a3ccf912fc846626fcf1004255b6bb3e",
    RAW_FILES["prep1-top-i2"]:
        "6f460dcfdde16c5b31cbbc064e59b3703a356fb911c2f4b13e5952000f3046a8",
    RAW_FILES["applied-top-i3"]:
        "b6b881a009546fde5600b58f3c20d12a470314a778c7ab9622cf2750a73ac0bc",
    RAW_FILES["prep1-top-i3"]:
        "1f50bda29def5a5177f409fde15a706527522be508fc569357030d49acfea9d7",
    RAW_FILES["applied-bottom-i1"]:
        "092c67f06848ce3d04891bb567090b58dc2f013bcb403552a0f400e6cac2369b",
    RAW_FILES["prep1-bottom-i1"]:
        "8188b79880cb4f0a828e5f8dbc17d54441764f4a32b3a22855c1c81c9238fbb9",
    RAW_FILES["applied-bottom-i2"]:
        "0e380ede661d2424d6a33757e615a3dfdb0fe658a5d6604c7255cf300e2708ff",
    RAW_FILES["prep1-bottom-i2"]:
        "6e2e2e6a314777e036052af2b213ae1dff9aa1de7e225d0480d50f156deba1df",
    RAW_FILES["applied-bottom-i3"]:
        "112fe7c9d752e3fabd7fabe0c8fb6fbccaaf1a255d6be017f36bf5095bddb740",
    RAW_FILES["prep1-bottom-i3"]:
        "89254b872bf3be09ee6a7b09edf26544a1dbfaf53e21d0a53d927d49d7488352",
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
    "盲读词只含图像路径（renders-r14b 四张字节复用=r14 轮盲读所用同一"
    "批文件、本轮渲染零变更）+observation-guidance-r15.md"
    "（d5babc93，本轮新落盘冻结、本轮唯一判读依据）路径+视角前缀与实例 "
    "reader_id（R15T/R15B 前缀已随 r15 指引 §6 落盘固化、无需派发层"
    "覆盖，per r15-prep-record protocol_amendment.naming；reader-r15-"
    "{top,bottom}-i{1,2,3} 为派发指令命名）+起始序号+v1.2 工具行为规约"
    "硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/衍生图像"
    "生成等）；判读只允许以 Read 工具查看原图（同一原图可重复查看））；"
    "无任何 GT 坐标/类别提示/期望缺陷描述、零诊断报告内容（渲染探针链与 "
    "framing/witness 记录不进任何 reader 上下文）、除指引 §5A 仪器注记"
    "外零 legend/零其他解释（§5A=颜色→来源映射仪器事实注记即本轮唯一"
    "检验变量，per r15-prep-record）；读图者不接触 GT/派生台账/任何校准"
    "产物路径；跨实例/跨视角禁止交流（12 次盲读相互独立——独立性是"
    "多实例协议的前提，per r15-prep-record read_prohibition_note）")

#: 派发模式结构化记录（R15=指引侧单变量轮：每格 3 实例、两波次串行
#: 保序；派发结构与 r14 同构，协议侧零新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R15T-001..007；prep1 R15T-001..004",
        "top-i2": "applied R15T-001..004；prep1 R15T-001..006",
        "top-i3": "applied R15T-001..004；prep1 R15T-001..004",
        "bottom-i1": "applied R15B-001..003；prep1 R15B-001",
        "bottom-i2": "applied R15B-001..002；prep1 R15B-001..002",
        "bottom-i3": "applied R15B-001..003；prep1 R15B-001..002",
    },
    "flag_id_continuity_note": (
        "r15 实测=flag_id 两板各自从头编号（同一实例 applied 与 prep1 "
        "派次内各自独立起编；跨板同号如实登记）——与 r13/r14 的「同实例"
        "跨板连续」不同，属读者实例输出行为差异、如实入账不作废；编排"
        "侧因此把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R14→R15 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮变更="
                  "指引侧单变量（observation-guidance-r15.md 新落盘："
                  "§5A 渲染配色仪器注记节+轮次标识机械同步；§2–§7 判据"
                  "文本零变更）+渲染零变更（renders-r14b 四图字节复用）；"
                  "协议侧零新增条款"
                  "（v1.2 沿用：派发指令继续含纯 Read 直读硬性条款，"
                  "12/12 派次自述「未读取盘上任何其他文件」，见 "
                  "reader_instance_note；指引 §2–§7 实质判据通道零变更；"
                  "GT/阈值零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R15 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「仅依据给定 PNG 可见内容"
    "独立判读，未读取盘上任何其他文件」（12/12 逐字摘录在案 "
    "reader_tool_evidence）；r15 notes 无「未做任何裁剪/放大/像素分析"
    "等程序化处理」逐字语句——与 r14 十二派次措辞不同，属自述措辞"
    "差异、如实登记（工具行为轴=派发指令 v1.2 硬性条款照旧钉住，"
    "r10/r11 实测 8/12 派次自选 PIL 局部裁剪放大的自选异质性自 r12 "
    "规约生效起持续为零）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/除指引 "
    "§5A 仪器注记外零 legend/零其他文件接触=非盲读违规；跨轮实例不同+"
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
    "本轮指引=observation-guidance-r15.md（d5babc93，本轮新落盘冻结、"
    "本轮唯一判读依据）：该文件由 r13 指引（observation-guidance-r13.md，"
    "c28806e1，指引作者唯一事实源）机械变换生成并在本轮落盘冻结"
    "（per r15-prep-record guidance_reuse.edit_list：8 处编辑=标题行/"
    "本轮变更声明节正文/新增 §5A 渲染配色仪器注记节/示例旗 ID 前缀 "
    "R13T-→R15T-×4+R13B-→R15B-×1/round_id_constant/本轮性质行/示例 "
    "reader-id；§2–§7 判据文本零变更=分段逐字保留断言+关键 substring "
    "断言双重复核通过、per guidance_reuse.verification."
    "section_assertions_passed）；§5A=仪器事实注记、非判据——不构成任何"
    "「应判正常/无需报告」的指示，不降低任何存在性、归类、定位或报告"
    "的责任门槛（per r15-prep-record no_loosening_note；反放宽条款与"
    "三路出口在 §4 内逐字保留）——本轮恰一个指引侧变量（§5A 仪器注记"
    "节）、判断责任标准一字未松")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 15 轮迭代"
    "（development 域指引侧单变量轮（§5A 仪器注记配套）：迭代轮不得"
    "冒充留出证据）。")

INSTRUMENT_NATURE = (
    "单变量指引侧变更轮（判读指引增补 §5A 渲染配色仪器注记节：颜色→"
    "来源映射显式化——橙 (255,165,0)=白墨图元重着色（162 fill+4 stroke，"
    "B.Cu∪B.Mask 双族共享绘制）、绿 (0,128,0)=板内空隙白重着色（墨缺失"
    "处基材露白，非图元：非丝印、非阻焊开窗图形、非 courtyard 图形）；"
    "数值事实自 render-framing-r14b.json/render-witness-r14b.json 结构"
    "探测转录，per r15-prep-record changed_variables[0].description）"
    "+渲染零变更（renders-r14b 四图字节复用=r14 轮盲读所用同一批文件，"
    "四 PNG 盘上 sha 与 witness 登记值逐一相等）+GT/阈值零变更"
    "（instrument_change.changed=false 已预注册；§5A 为仪器事实注记、"
    "非判据）：判读语义"
    "通道的变更变量恰一项（指引侧 §5A）")

#: 预注册主通道三分判据所用声明常量（零覆盖；per r15-prep-record
#: hypothesis_test.adjudication.supported_requires_all 原文）。
#: supported=(i)∧(ii)∧(iii) 全部满足；reject_if=(i) 不满足或 (ii)(iii)
#: 任一不满足。(i) bottom courtyard 类非弃权计数按实例全为 0；
#: (ii) bottom 全旗聚合弃权率 ≤10/11（基线=run-r13 同口径重放交叉
#: 核对）；(iii) top 全旗聚合弃权率 ≤ run-r14 同口径聚合弃权率——
#: (iii) 无预注册常量，基线=同一聚合逻辑对 run-r14 内嵌实例记录双侧
#: 复算（不手工抄数）。
MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES = {
    "support_bottom_courtyard_non_abstain_max": 0,
    "support_max_aggregate_abstain_num": 10,
    "support_max_aggregate_abstain_den": 11,
}

#: 主通道逐实例登记表（bottom courtyard 类非弃权旗；程序实测与登记
#: 一致性 fail-closed：实测值须与本表 expected 逐一相等）。
MAIN_CHANNEL_REGISTERED = [
    {"instance": "bottom-i1", "expected": 0,
     "note": ("r13/r14 基线 0→r15 实测 0：本轮 bottom 零 courtyard 类"
              "旗标（4 旗=placement_pattern_anomaly 2+other_advisory 2，"
              "其中 1 非弃权 3 弃权）——非弃权 courtyard=0 系零旗标"
              "路径所致（条件 (i) 自动满足；与 r13 判正常收敛路径/r14 "
              "全弃权路径成因三分、如实分列不合并）")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r13/r14 基线 0→r15 实测 0：本轮 bottom 零 courtyard 类"
              "旗标（4 旗=placement_pattern_anomaly 2+other_advisory 2，"
              "r14 的黑点骑跨 courtyard 轮廓 2 条弃权旗本轮未再现）"
              "——零旗标路径")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r13/r14 基线 0→r15 实测 0：本轮 bottom 零 courtyard 类"
              "旗标（5 旗全部弃权=other_advisory 3+placement_pattern_"
              "anomaly 2；r14 的阵列顶端疑似接触 courtyard 弃权 2 条"
              "本轮未再现）——零旗标路径")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。r15 自述措辞=「仅依据给定 PNG…未读取
#: 盘上任何其他文件」（与 r14「未做任何裁剪/放大/像素分析」措辞不同，
#: 差异如实登记，见 READER_INSTANCE_NOTE）。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据给定 PNG（prep1-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i2",
     "excerpt": "仅依据给定 PNG（applied-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i2",
     "excerpt": "仅依据给定 prep1-top.png 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据给定 PNG（applied-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据给定 prep1-top.png 的可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG（applied-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG（renders-r14b/prep1-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG（applied-bottom.png，bottom 视）可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 applied-bottom.png 的可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 六派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——绿色翼瓣/
#: 空隙形态在 r15 指引 §5A 注记下延续 §4(i) 判读路径的机制观察证据
#: （3/3 bottom 实例、判据轴延续）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "按 §4(i) 系统性正常特征判据不报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "按 §4(i) 系统性正常设计特征判为正常，不报告"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "按 §4(i) 判为正常设计特征，未进入 flags"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "≥3 处、分布于 ≥2 条边、形态尺寸一致"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "均满足 §4(i) 量化判据（最小重复单元≥3 处、沿同一阵列对齐、跨≥2 条阵列/边、形态尺寸样式一致）"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "按§4(i)量化判据判为正常设计特征未报告"},
]

#: §4(iii) 接触性判据延续使用证据（r15 top 视角 6 条 courtyard 弃权旗
#: 中明写接触性不可区分的 5 条，逐旗 location_evidence 逐字摘录；
#: substring fail-closed 校验；第 6 条=存在性出口、另行如实登记）。
CONTACT_CRITERION_EVIDENCE = [
    {"source": "applied-top-i1", "flag_id": "R15T-003",
     "excerpt": "无法区分真实接触与视觉贴近"},
    {"source": "applied-top-i2", "flag_id": "R15T-001",
     "excerpt": "当前分辨率下无法负责任区分真实接触/交叠与视觉贴近"},
    {"source": "prep1-top-i2", "flag_id": "R15T-005",
     "excerpt": "在当前分辨率下均无法负责任区分"},
    {"source": "applied-top-i3", "flag_id": "R15T-002",
     "excerpt": "当前分辨率下无法分辨是真实接触还是小于分辨率的视觉贴近"},
    {"source": "prep1-top-i3", "flag_id": "R15T-001",
     "excerpt": "当前分辨率无法区分真实接触与视觉贴近"},
]

#: 绿色区域语义化方式证据（r15-prep-record adjudication.
#: mechanism_observation_separate 预注册：按实例分布；bottom 六派次
#: reading_notes 逐字摘录；substring fail-closed 校验；对照 r14 三实例
#: 三种语义化=轮廓/连接形态/courtyard 矩形——r15 三实例均以「空隙/
#: 翼瓣」语义化、其中 3 派次显式援引 §5A 仪器注记）。
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "多数焊盘间夹有绿色清空隙翼瓣状空隙"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "沿阵列周期性出现的月牙/翼瓣状绿色空隙特征"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "板缘内侧绿色带与焊盘间绿色翼瓣按指引 §5A 仪器注记理解为空隙着色、未作为图元判读",
     "cites_5A": True},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "左右两边焊盘列上各出现的大尺寸绿色热隔离翼瓣形态",
     "second_excerpt": "其绿色分段环与 §5A 基准环缝描述相符",
     "cites_5A": True},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "部分焊盘所带的绿色翼瓣状间隙形态"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "规律分布的花瓣状绿色空隙与个别方形端焊盘",
     "second_excerpt": "§5A 亦注明绿色区域非图元",
     "cites_5A": True},
]

#: 黑点类现象证据（r15 黑点类旗标 7 条全弃权+3 派次 notes 判正常未
#: 报告的代表摘录；kind=reading_notes 或 location_evidence；substring
#: fail-closed 校验；延续 r14 黑点类追踪）。
BLACK_DOT_EVIDENCE = [
    {"source": "applied-top-i2", "kind": "location_evidence",
     "flag_id": "R15T-002", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上连接器区块内有两处实心黑色圆点"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R15B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "图像左上角有两组小椭圆焊盘组，各伴有一枚实心黑点"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R15B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "旁各见一枚实心黑色小圆点"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "图上部偏左区域见两个孤立的实心小黑圆点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "图像左上角有一个孤立黑色圆点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R15B-002", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "有第二个孤立黑色圆点"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "有一小黑色圆点（钻孔/基准点样）"},
    {"source": "prep1-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "disposition": "判正常不报告",
     "excerpt": "右上两黑色实心圆点判为基准点/连接器定位类正常特征，未报告"},
    {"source": "applied-top-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i3", "disposition": "判正常不报告",
     "excerpt": "两枚实心黑点疑似基准点/安装孔且不与任何图形构成可见冲突，未作为疑似形态报告"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "disposition": "判正常不报告",
     "excerpt": "两处位于左上小型焊盘群旁的黑色钻孔点（两组镜像成对、与焊盘间可见明显间隙，未见可疑接触形态，不构成怀疑对象）"},
]

#: 黑点类旗标登记表（7 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定——r15 两板各自
#: 从头编号）。
BLACK_DOT_FLAGS = [
    ("top-i2", "applied", "R15T-002", "other_advisory"),
    ("bottom-i1", "applied", "R15B-002", "other_advisory"),
    ("bottom-i2", "applied", "R15B-002", "other_advisory"),
    ("bottom-i2", "prep1", "R15B-001", "other_advisory"),
    ("bottom-i3", "applied", "R15B-001", "other_advisory"),
    ("bottom-i3", "applied", "R15B-002", "other_advisory"),
    ("bottom-i3", "prep1", "R15B-001", "other_advisory"),
]

#: placement 类旗标（板内孤立焊盘组+边缘节距空档）处置证据（逐字摘录；
#: substring fail-closed 校验）——r15 六旗两非弃权四弃权+notes 判正常
#: 未报告三种处置如实单列（区别于 r14 板内孤立组「两判正常一弃权」）。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i1", "verdict": "非弃权",
     "phenomenon": "边缘节距空档（上边缘内排右端）",
     "excerpt": "该排的间距规律在此处被明显打破"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "边缘节距空档（同位现象、跨板出口不同）",
     "excerpt": "位置估计精度不足以负责任地确认间距规律被明显打破"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R15B-001", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（「圆形焊盘（四周带绿色空隙翼瓣）+方形焊盘」）",
     "excerpt": "与其余全部沿板缘成行成列紧贴排列的焊盘图形相距甚远、不属任何行列阵列，与周边规整贴边放置模式明显不协调"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R15B-003", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内空白区孤悬一组焊盘"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R15B-003", "instance": "bottom-i3", "verdict": "弃权",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "位置明显脱离四边外围焊盘阵列的规整模式"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R15B-002", "instance": "bottom-i2", "verdict": "弃权",
     "phenomenon": "左上两组图元簇镜像排布",
     "excerpt": "仅两处样本且无同类第三参照，无法确认是设计意图的镜像摆置还是个别成员取向偏离"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R15B-002", "instance": "bottom-i3", "verdict": "弃权",
     "phenomenon": "右侧阵列焊盘形态疑似不一致",
     "excerpt": "当前分辨率无法确认该差异是真实形态异常还是相邻绿色空隙并合造成的渲染观感"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i2", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘对（右下区域）",
     "excerpt": "板内孤立小焊盘对（右下区域，其绿色分段环与 §5A 基准环缝描述相符）"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内孤立两焊盘形态完整、与周边无接触，无可疑形态，未报告"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（可见内容列举、未旗标）",
     "excerpt": "中部偏右一组圆盘+方形焊盘"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed）。
REROUTE_ADJUDICATION = [
    {"source": "applied-top-i1", "flag_id": "R15T-005", "abstain": False,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("板中央偏左处一段铜箔走线围出近似圆角矩形的"
                           "环形/回折形态，孤立出现且与周边简捷的 45 度"
                           "走向明显不协调"),
     "adjudication": "non_abstain_boundary_report",
     "note": ("非弃权旗：「等长|蛇形」子串零命中（fail-closed 实测=登记"
              "一致）=未援引候选解释；reading_notes 明写「按判据 (ii) "
              "孤立不一致形态报告为 suspicious_reroute」——边界报告方向"
              "保留（r11 R11T-018/020、r12 R12T-001、r13 R13T-001、"
              "r14 R14T-004 同向先例延续；滥用型被动追踪=0）")},
    {"source": "prep1-top-i1", "flag_id": "R15T-002", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("可见一段呈矩形C形回折的红色走线"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法确认它是连接两个邻近端点的"
              "多余绕行（可疑改道）还是两条正常折线引出」=可疑改道"
              "是否存在无法负责任确认，按 §4 弃权")},
    {"source": "applied-top-i3", "flag_id": "R15T-001", "abstain": False,
     "declared_substring_hits": ["蛇形"],
     "form_desc_excerpt": ("一段红色连线形成狭窄的回折/环形形态（两段"
                           "近似平行的短竖线顶端相连，并斜向引出）"),
     "adjudication": "non_abstain_boundary_report_negation_citation",
     "note": ("非弃权旗：「蛇形」子串命中=1（fail-closed 实测=登记"
              "一致）——但语义=否定式援引：location_evidence 明写"
              "「属孤立的明显多余弯折，非整段规则周期蛇形」=按 §3A "
              "示例 c 收窄判据正确排除整段规则周期候选解释后按 §4(ii) "
              "孤立不一致报告；机械命中如实登记、非滥用型被动追踪"
              "（与 r14 R14T-004 零命中边界报告同向、多一处否定式"
              "收窄判据援引，如实分记）")},
    {"source": "prep1-top-i3", "flag_id": "R15T-004", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("疑见一段连线呈回折/钩形（先向左延伸后折返"
                           "回向右）"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "「该形态亦可能是两条相互独立的连线在当前分辨率下被误读"
              "为连贯回折，无法负责任确认可疑改道是否存在」按 §4 弃权")},
]

#: reroute 类旗标产量链基线（r8–r14 在案；本轮 r15 实测=4）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0}

#: bottom courtyard 非弃权旗 r13/r14 基线（prep-record 判据 (i) 对照值
#: 「对照 r13/r14 的 0/0/0」；与 run-r13/run-r14 内嵌记录重放实测交叉
#: 核对，fail-closed）。
R13_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}
R14_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}


def _fail(msg: str) -> None:
    print(f"[s55-cal-r15] FAIL: {msg}")
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
    # 渲染 provenance 按视角分列：本轮渲染零变更（renders-r14b 四图
    # 字节复用=r14 轮盲读所用同一批文件）；top=字节内容与 renders-r5
    # 一致（framing-r5 在案先例），bottom=r14b 显式配色版（framing-r14b
    # 预注册在案）。两视角共同声明=本轮零重渲染、唯一变量=指引 §5A。
    if "-top-" in raw_key:
        framing_rel = REL_FRAMING_R5
        framing_note = (
            "top 渲染零变更（跨 r14→r15 双轮零变更）：r15 top=renders-"
            "r14b 路径、字节内容=renders-r5（r14 轮已逐字节复用在案；"
            "framing-r5 预注册件在案；本轮唯一变量=指引侧 §5A 仪器"
            "注记）")
    else:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "bottom 渲染零变更：r15 bottom=renders-r14b 四图字节复用"
            "（与 R14 完全相同：白墨图元→橙 (255,165,0)、板内空隙白→"
            "绿 (0,128,0)；四 PNG sha 与 render-witness-r14b.json 登记"
            "值 fail-closed 比对一致=r14 轮盲读所用同一批文件；framing-"
            "r14b=7004b017 预注册件在案；本轮零重渲染）")
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
                "r15 flag_id 两板各自从头编号（跨板同号如实登记）——"
                "abstain_ids/non_abstain_flag_ids 按 (state, flag_id) "
                "限定，跨板同号不混淆"),
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
                 "三分判据（0/0/0、≤10/11、≤run-r14 同口径）各自独立"
                 "计算、互不凌驾"},
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
                       "r15": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
                              run_r13: dict, run_r14: dict,
                              inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R14；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R13/R14 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r13_replays = replay_round_instances(run_r13)
    r14_replays = replay_round_instances(run_r14)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R15 {key} 通道重放与 compare_v3 对拍不一致")

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
    # r13/r14=本轮 fresh 重放并与在案登记逐一交叉核对）
    geo_r13 = pick("area_ratio_rejected", r13_replays, None)
    geo_r14 = pick("area_ratio_rejected", r14_replays, None)
    geo_r15 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r13 = pick("category_mismatch", r13_replays, None)
    cat_r14 = pick("category_mismatch", r14_replays, None)
    cat_r15 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r13 = pick("view_gate", r13_replays, None)
    view_r14 = pick("view_gate", r14_replays, None)
    view_r15 = pick("view_gate", inst_replays, inst_blocks)
    # 与在案 run 登记交叉核对（fail-closed：重放结果须与在案一致）
    if geo_r13 != run_r13["channel_attribution"]["channel_1_geometry_gate"][
            "r13_area_ratio_rejected_entries"]:
        _fail("R13 几何门重放与 run-r13 在案登记不一致")
    if cat_r13 != run_r13["channel_attribution"]["channel_2_category_gate"][
            "r13_category_mismatch_entries"]:
        _fail("R13 类别门重放与 run-r13 在案登记不一致")
    if view_r13 != run_r13["channel_attribution"][
            "view_gate_observations"]["r13_entries"]:
        _fail("R13 视角门重放与 run-r13 在案登记不一致")
    if geo_r14 != run_r14["channel_attribution"]["channel_1_geometry_gate"][
            "r14_area_ratio_rejected_entries"]:
        _fail("R14 几何门重放与 run-r14 在案登记不一致")
    if cat_r14 != run_r14["channel_attribution"]["channel_2_category_gate"][
            "r14_category_mismatch_entries"]:
        _fail("R14 类别门重放与 run-r14 在案登记不一致")
    if view_r14 != run_r14["channel_attribution"][
            "view_gate_observations"]["r14_entries"]:
        _fail("R14 视角门重放与 run-r14 在案登记不一致")

    geo_change = (
        "几何门通道（R14→R15）：面积比出局条目 1→0（r15 重放零几何门"
        "条目；r14 唯一条目=R14T-002×GT-REVC-AP-7-C31U4 宽泛丝印框未"
        "再现——r15 top 非弃权旗 4 条（i1 1 reroute+i2 2 silk+i3 1 "
        "reroute）与同态 GT 零 ≥0.5 containment 交叠；§3 收窄判据守门"
        "回落如实单列（r15 预注册 support 条件不含守门要件、几何门条目"
        "变化按 guard_channel 要求如实记录）。")
    cat_change = (
        "类别门通道（R14→R15）：类别不符出局条目 0→0（r15 重放零类别门"
        "条目；R11T-012↔GT-REVC-AP-8-R1Q2 仍为 r11 唯一条目、r12–r15 "
        "均无再现）；多实例样本量极小，只描述不断言。")

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
            "r13": len(geo_r13),
            "r14": len(geo_r14),
            "r15": len(geo_r15),
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
            "r13": len(cat_r13),
            "r14": len(cat_r14),
            "r15": len(cat_r15),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0（r14 回升未延续、r15 回落：r15 top 非弃权"
                 "旗与同态 GT 零 ≥0.5 containment 交叠）；类别门 r6=1→"
                 "r7=0→r8=1→r9=0→r10=0→r11=1→r12=0→r13=0→r14=0→r15=0"
                 "（R15 零条目；r11 唯一条目 R11T-012↔AP-8 连续四轮无"
                 "再现）"),
    }
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R15, "sha256": _sha(REL_PREP_R15)},
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
            "source_of_r13_r14_detail": (
                "calibration-run-r13.json / calibration-run-r14.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53 deviation_"
                "note 口径：本轮对 R13/R14/R15 均以内嵌输入+compare_v3 "
                "同源几何原语（calibration._containment/_area_ratio、"
                "CONTAINMENT_MIN=0.5、AREA_RATIO_MAX=10.0 声明常量）对每"
                "非弃权旗标×同态 GT 确定性重放通道分类：containment<0.5"
                "（含 None=无交集）无条目；近邻且视角不符=view_gate；近邻"
                "且面积比>上限=area_ratio_rejected（几何门）；近邻且面积"
                "比≤上限且类别不符=category_mismatch（类别门）；类别相符"
                "且双条件过=candidate。"),
            "replay_cross_check": {
                "r13_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r13_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r14_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r14_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r15_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R13/R14 十二件复算"
                         "与在案 run 登记一致：R13/R14 候选对=空集；R15 "
                         "十二件重放全部复现：候选对=空集，matches=0）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R13T/R13B、R14T/R14B 与 R15T/"
            "R15B 来自不同 reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素；r15 两板各自从头编号"
            "亦属实例输出行为差异、如实登记）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r13_area_ratio_rejected_entries": geo_r13,
            "r14_area_ratio_rejected_entries": geo_r14,
            "r15_area_ratio_rejected_entries": geo_r15,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r13_category_mismatch_entries": cat_r13,
            "r14_category_mismatch_entries": cat_r14,
            "r15_category_mismatch_entries": cat_r15,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r13_entries": view_r13,
            "r14_entries": view_r14,
            "r15_entries": view_r15,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r15 重放"
                     "零视角门条目——r15 top 非弃权旗 4 条与同态 GT 零"
                     "视角错位交叠、bottom 非弃权旗 2 条（GT 13 条全部 "
                     "side=top；bottom 无 GT 在案 gt-audit-r1：bottom "
                     "GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，如实）；"
                     "r13/r14 重放亦零视角门条目（在案延续）。"),
        },
        "gate_chain_since_r6": chain,
        "r15_specific_observations": [
            "R15 六实例 42 旗标（非弃权 6、弃权 36）中，matches（逐实例"
            "逐态 compare_v3）合计 0 条：GT 条目层 union=0/13（0.0）、"
            "agreement=0/13（0.0）、代表配置 gt_recall_total=0/13（0.0）"
            "——r11 的 4 条逐实例命中连续第四轮零再现；top 非弃权旗 4 条"
            "（i1 1 reroute+i2 2 silk+i3 1 reroute）与同态 GT 零 ≥0.5 "
            "containment 交叠（零几何门条目）；bottom 非弃权旗 2 条"
            "（placement 类）零匹配属结构性（GT 13 条全部 side=top，"
            "bottom GT 无源在案 gt-audit-r1）。",
            "R15 courtyard 类旗标 6 条全部弃权且全部位于 top（top-i1 ×1"
            "+top-i2 ×2+top-i3 ×3；bottom 零 courtyard 类旗标——区别于 "
            "r14 的 bottom 4 条 courtyard 弃权：黑点骑跨轮廓 2+阵列顶端"
            "疑似接触 2 本轮未再现，分类通道转移如实记录）；top 弃权 "
            "courtyard 6 条中 5 条带接触性判据「真实接触 vs 视觉贴近"
            "不可区分」理由（逐旗摘录在案 hypothesis_test."
            "mechanism_observation.contact_criterion_continuation）、"
            "1 条（prep1-top-i3 R15T-003）为存在性出口（第二条轮廓"
            "存在性/归属层不可确认）——出口构成如实分列。",
            "R15 几何门 0 条（r14 的 1 条回落）；类别门 0 条（r12–r15 "
            "连续零条目）；视角门四轮（r12–r15）均空。",
            "R15 suspicious_reroute 旗标 4 条：非弃权 2（R15T-005 "
            "applied-top-i1+R15T-001 applied-top-i3）+弃权 2（R15T-002 "
            "prep1-top-i1+R15T-004 prep1-top-i3，存在性出口）；逐实例"
            "产量 top-i1=2、top-i3=2；r8=1→r9=0→r10=2→r11=3→r12=3→"
            "r13=2→r14=1→r15=4；非弃权 R15T-001 含「蛇形」子串但为"
            "否定式援引（明写「非整段规则周期蛇形」=收窄判据排除候选"
            "解释）——r15 滥用型通道被动追踪见 hypothesis_test."
            "reroute_continuation_r15（非本轮判据输入）。",
            "courtyard 被动追踪（r11–r14 run-record courtyard_tracking "
            "在案先例延续）：r15 非弃权 "
            "courtyard 旗 0 条（r11 14 条 3 命中→r12 20 条 0 命中→r13 "
            "0 条→r14 0 条→r15 0 条）、弃权 6 条（全部 top；bottom 零 "
            "courtyard 旗）；courtyard 匹配 r8=1→r9=0→r10=1→r11=3→"
            "r12=0→r13=0→r14=0→r15=0；GT/阈值零改动、零期望（run-r15 "
            "courtyard_tracking 节）。",
        ],
    }


def _prep_doc() -> dict:
    """r15-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R15)


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
    """主通道判据 (i) 实测（操作化定义：bottom 三实例 courtyard 类非
    弃权旗数；per r15-prep-record supported_requires_all[0] 原文）。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r15 两板各自从头编号、明细行已按 (state, flag_id) 限定）；
    逐实例计数与 MAIN_CHANNEL_REGISTERED 的 expected 逐一相等
    （fail-closed，不符即中止）。
    """
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        rec = instances[name]
        cnt = sum(1 for d in rec["per_flag_gt_detail"]
                  if d["category"] == "courtyard_crowding"
                  and not d["abstain"])
        out[name] = cnt
    for row in MAIN_CHANNEL_REGISTERED:
        if out[row["instance"]] != row["expected"]:
            _fail(f"主通道实测与登记表不符: {row['instance']} "
                  f"实测={out[row['instance']]} 登记={row['expected']}")
    return out


def r13_baseline_courtyard_live(run_r13: dict) -> dict:
    """r13 基线重放实测（判据 (i) 对照「r13 的 0/0/0」；run-r13 内嵌
    输入；与 R13_BOTTOM_COURTYARD_BASELINE 登记交叉核对）。"""
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            blk = run_r13["instances"][name]["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in blk["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        out[name] = cnt
    if out != R13_BOTTOM_COURTYARD_BASELINE:
        _fail(f"r13 bottom courtyard 基线与 run-r13 实测不符: {out}")
    return out


def r14_baseline_courtyard_live(run_r14: dict) -> dict:
    """r14 基线重放实测（判据 (i) 对照「r14 的 0/0/0」；run-r14 内嵌
    输入；与 R14_BOTTOM_COURTYARD_BASELINE 登记交叉核对）。"""
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            blk = run_r14["instances"][name]["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in blk["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        out[name] = cnt
    if out != R14_BOTTOM_COURTYARD_BASELINE:
        _fail(f"r14 bottom courtyard 基线与 run-r14 实测不符: {out}")
    return out


def _view_aggregate_abstain_live(run_doc: dict, instances: tuple) -> tuple:
    """视角全旗聚合弃权（分子, 分母）重放实测（判据 (ii)/(iii) 同一口
    径：对 run-doc 内嵌实例记录按 states 层重放，不读 combined 汇总值）。"""
    n_fl = 0
    n_ab = 0
    for name in instances:
        for st in ("applied", "prep1"):
            blk = run_doc["instances"][name]["states"][st]
            n_fl += len(blk["reader_flags"])
            n_ab += blk["compare_v3"]["abstain"]["abstain_count"]
    return n_ab, n_fl


def r13_bottom_abstain_aggregate_live(run_r13: dict) -> tuple:
    """r13 bottom 全旗聚合弃权重放实测（判据 (ii) 基线；对照 10/11）。"""
    return _view_aggregate_abstain_live(
        run_r13, ("bottom-i1", "bottom-i2", "bottom-i3"))


def r14_top_abstain_aggregate_live(run_r14: dict) -> tuple:
    """r14 top 全旗聚合弃权重放实测（判据 (iii) 基线；同一聚合逻辑对
    run-r14 内嵌实例记录双侧复算、不手工抄数）。"""
    return _view_aggregate_abstain_live(
        run_r14, ("top-i1", "top-i2", "top-i3"))


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
                          run_r14: dict, instances: dict, view_layer: dict,
                          attribution: dict, raw_texts: dict,
                          parsed_notes: dict, reroute_rows: list) -> dict:
    """假设（r14-dev-record-candidate-0-guidance-color-legend）裁决节
    （预注册三分判据执行；字母裁决唯一正式+机制观察单列）。

    字母裁决（唯一正式裁决）=判据 r15-prep-record.json hypothesis_test.
    adjudication 原文（supported_requires_all 三项；脚本从 prep-record
    文件加载判据文本、不另嵌一套常量）：support=(i)∧(ii)∧(iii) 全部
    满足；reject_if=(i) 不满足或 (ii)(iii) 任一不满足。实测：
    (i) bottom courtyard 类非弃权旗数 0/0/0——r15 bottom 零 courtyard
    类旗标（与 r13 判正常收敛路径/r14 全弃权路径成因三分、如实分列）；
    (ii) bottom 全旗聚合弃权率 11/13=0.846154≤10/11（基线=run-r13 内嵌
    记录重放实测 10/11 交叉核对一致）满足；(iii) top 全旗聚合弃权率
    25/29=0.862069>run-r14 同口径聚合弃权率（同一聚合逻辑对 run-r14
    内嵌实例记录双侧复算=18/24=0.75，不手工抄数）违约 ⇒ verdict=reject
    （拒绝支=第三支 top 回退）。三项分开如实记录、不合并；本轮判据均
    为描述性边界、非 APR-0011 门（门照常独立计算，互不凌驾、run-record
    内分开表述）。守门通道（top 几何门）=r15-prep-record
    attribution_plan.guard_channel 独立单列：R14=1→R15=0 回落如实记录。
    机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R15)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（round14-dev-record 锚已在 FROZEN_SHA256 校验；
    # 其 next_iteration_targets[0] 候选原文被本 prep-record 逐字摘录
    # 预注册；sha256_measured 与盘上实测须一致）
    dev14 = _json_load(REL_DEV_R14)
    preref = prep_doc["changed_variables"][0]["preregistration_ref"]
    if preref["path_rel"] != REL_DEV_R14 or \
            preref["sha256_measured"] != _sha(REL_DEV_R14) or \
            dev14["next_iteration_targets"][
                preref["item_indices_zero_based"][0]] \
            != preref["candidate_quote"]:
        _fail("prep-record 预注册摘录（candidate_0）与 round14-dev-record "
              "原文/锚不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    requires_all = adj["supported_requires_all"]
    if len(requires_all) != 3:
        _fail("prep-record supported_requires_all 应恰三项")
    # 基线数字与在案 run 交叉核对（fail-closed；live 重放与登记不符即 FAIL）
    if "对照 r13/r14 的 0/0/0" not in requires_all[0]:
        _fail("prep-record 判据 (i) 文本与预期不符")
    r13_base_live = r13_baseline_courtyard_live(run_r13)
    r14_base_live = r14_baseline_courtyard_live(run_r14)
    if "10/11" not in requires_all[1] or "0.909091" not in requires_all[1] \
            or "calibration-run-r13.json" not in requires_all[1]:
        _fail("prep-record 判据 (ii) 文本与预期不符")
    base_ab, base_fl = r13_bottom_abstain_aggregate_live(run_r13)
    if (base_ab, base_fl) != (10, 11):
        _fail("r13 bottom 全旗聚合弃权基线与 run-r13 实测不符（应为 10/11）")
    if "calibration-run-r14.json" not in requires_all[2] or \
            "不手工赋值" not in requires_all[2] or \
            "双侧复算" not in requires_all[2]:
        _fail("prep-record 判据 (iii) 文本与预期不符")
    base_top_ab, base_top_fl = r14_top_abstain_aggregate_live(run_r14)
    # r14 bottom 全旗聚合（机制观察对照值；live 重放、不手工抄数）
    r14_bot_ab, r14_bot_fl = _view_aggregate_abstain_live(
        run_r14, ("bottom-i1", "bottom-i2", "bottom-i3"))
    if (r14_bot_ab, r14_bot_fl) != (14, 14):
        _fail("r14 bottom 全旗聚合弃权与 run-r14 实测不符（应为 14/14）")
    # reroute 产量链基线交叉核对（r8–r14 在案）
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
            != REROUTE_CHAIN_PRIOR["r14"]:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（三分判据逐项）
    by_instance = bottom_courtyard_non_abstain(instances)
    vals = [by_instance[n] for n in ("bottom-i1", "bottom-i2", "bottom-i3")]
    bot_courtyard_flags = sum(
        1 for n in ("bottom-i1", "bottom-i2", "bottom-i3")
        for d in instances[n]["per_flag_gt_detail"]
        if d["category"] == "courtyard_crowding")
    # (i) bottom courtyard 类非弃权计数按实例全为 0
    i_max = MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES[
        "support_bottom_courtyard_non_abstain_max"]
    crit1_ok = all(v <= i_max for v in vals)
    # (ii) bottom 全旗聚合弃权率 ≤10/11（基线 live=10/11 交叉核对一致）
    abst_bot, flags_bot = round_view_aggregate(
        instances, ("bottom-i1", "bottom-i2", "bottom-i3"))
    bot_rate = cal._ratio(abst_bot, flags_bot)
    b_num = MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES[
        "support_max_aggregate_abstain_num"]
    b_den = MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES[
        "support_max_aggregate_abstain_den"]
    crit2_ok = abst_bot * b_den <= b_num * flags_bot
    bottom_zero_flag = flags_bot == 0
    # (iii) top 全旗聚合弃权率 ≤ run-r14 同口径聚合弃权率（双侧复算）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    crit3_ok = abst_top * base_top_fl <= base_top_ab * flags_top
    top_base_rate = cal._ratio(base_top_ab, base_top_fl)
    # 守门通道（top 几何门）——独立单列（r15 support 条件不含此件）
    geo_r15 = attribution["channel_1_geometry_gate"][
        "r15_area_ratio_rejected_entries"]
    geo_r14 = attribution["channel_1_geometry_gate"][
        "r14_area_ratio_rejected_entries"]
    guard_ok = len(geo_r15) == 0 and len(geo_r15) <= len(geo_r14)
    # 字母裁决（三分判据，per r15-prep-record supported_requires_all/
    # reject_if 原文；整数交叉相乘避免浮点比较）
    supported = crit1_ok and crit2_ok and crit3_ok
    rejected = (not crit1_ok) or (not crit2_ok) or (not crit3_ok)
    if supported and rejected:
        _fail("主通道判定自洽性破坏（support 与 reject 互斥）")
    verdict = "supported" if supported else "reject"
    reject_branch = None
    if rejected:
        branches = []
        if not crit1_ok:
            branches.append("第 (i) 项（图例引入新混淆或收敛不稳健）")
        if not crit2_ok:
            branches.append("第 (ii) 项（图例不足以消除 bottom 混淆性"
                            "弃权）")
        if not crit3_ok:
            branches.append("第 (iii) 项（top 全旗聚合弃权率回退："
                            "其他轴回退）")
        reject_branch = "；".join(branches)
    verdict_text = (
        "按预注册判据（r15-prep-record.json hypothesis_test.adjudication "
        "原文，三分判据）=reject（字母口径，唯一正式裁决）：条件 (i) "
        "bottom 三实例 courtyard 类非弃权旗数实测=0/0/0（对照 r13/r14 "
        "的 0/0/0，live 重放交叉核对一致）满足——但成因与 r13/r14 均不"
        "同：r15 bottom 零 courtyard 类旗标（旗标全部为 placement/"
        "other 类），非弃权 courtyard=0 系零旗标路径、条件自动满足"
        "（分类通道转移如实记入机制观察）；条件 (ii) bottom 全旗聚合"
        f"弃权率实测={abst_bot}/{flags_bot}={bot_rate}≤{b_num}/{b_den}"
        "（r13 基线 10/11=0.909091，run-r13 内嵌记录重放交叉核对一致）"
        "满足——bottom 混淆性弃权较 r14 全弃权（14/14=1.0）回落；条件 "
        f"(iii) top 全旗聚合弃权率实测={abst_top}/{flags_top}={top_rate}>"
        f"run-r14 同口径聚合弃权率（同一聚合逻辑对 run-r14 内嵌实例记录"
        f"双侧复算={base_top_ab}/{base_top_fl}={top_base_rate}，不手工"
        "抄数）违约 ⇒ 拒绝支=" + f"{reject_branch}——top 轴回退（r14→"
        "r15 top 聚合弃权率 0.75→0.862069 回升），图例/指引侧配套未"
        "消除 top 轴弃权水平。三项判据分开如实记录、不合并；守门通道"
        "（top 几何门）R14=1→R15=0 回落独立单列（r15 support 条件不含"
        "守门要件）。注意：reject=预注册描述性边界下的方向性归因、非"
        "统计证明——「正确测出无效同样是有效证据」；单轮 n=3、跨轮实例"
        "群混杂照旧（development 域只描述不断言）；机制观察单列（绿区"
        "语义化按实例分布/黑点类延续/bottom 零 courtyard 旗=分类通道"
        "转移/placement 类处置分化），不凌驾、不改写字母裁决；APR-0011 "
        "门（代表配置）与裁决=reject 分列不合并；本轮判据均为描述性"
        "边界、非门阈值（门零改动）。")
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 量化判据应用
    # + 接触性判据逐旗 + 黑点类 + placement 处置 + 绿区语义化）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in QUANT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in CONTACT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"接触性判据摘录与 reader 原文不符: {ev['flag_id']}")
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
    # 黑点类旗标登记校验（7 条全部存在、abstain=True、category=登记值）
    black_rows = []
    for inst, st, fid, cat in BLACK_DOT_FLAGS:
        d = next(x for x in instances[inst]["per_flag_gt_detail"]
                 if x["flag_id"] == fid and x["state"] == st)
        if not d["abstain"] or d["category"] != cat:
            _fail(f"黑点类旗标登记与实测不符: {fid}")
        black_rows.append({"flag_id": fid, "instance": inst, "state": st,
                           "category": d["category"], "abstain": True})
    # 接触性判据旗标登记校验（5 条全部 courtyard_crowding+abstain+top 视角）
    contact_rows = []
    for ev in CONTACT_CRITERION_EVIDENCE:
        inst = None
        st = None
        for name in INSTANCE_ORDER:
            for s, part in (("applied", INSTANCES[name]["parts"][0]),
                            ("prep1", INSTANCES[name]["parts"][1])):
                if part == ev["source"]:
                    inst, st = name, s
        if inst is None or not inst.startswith("top"):
            _fail(f"接触性判据登记 source 非 top 视角: {ev['source']}")
        d = next(x for x in instances[inst]["per_flag_gt_detail"]
                 if x["flag_id"] == ev["flag_id"] and x["state"] == st)
        if d["category"] != "courtyard_crowding" or not d["abstain"]:
            _fail(f"接触性判据旗标登记与实测不符: {ev['flag_id']}")
        contact_rows.append({"flag_id": ev["flag_id"], "instance": inst,
                             "state": st, "category": d["category"],
                             "abstain": True})
    # 绿色区域语义化观察（r15-prep-record adjudication.
    # mechanism_observation_separate 预注册：按实例分布；程序实测
    # substring 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、不构成判据输入）
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
            "semantic_mode": ("§5A 仪器注记显式援引+空隙/翼瓣语义化"
                              if any(cites)
                              else "空隙/翼瓣几何语义化（无 §5A 显式"
                                   "援引）"),
        }
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=reject "
                 "不因本观察改写；per r15-prep-record adjudication."
                 "mechanism_observation_separate）"),
        "main_channel_three_criteria": {
            "observation": (
                "主通道三分判据分开实测（机制 (i)）：条件 (i) bottom 三"
                "实例 courtyard 类非弃权旗数 0/0/0 满足——但成因与 r13/"
                "r14 均不同：r15 bottom 零 courtyard 类旗标（r15 bottom "
                "13 旗=placement_pattern_anomaly 6+other_advisory 7，"
                "courtyard=0），非弃权 courtyard=0 系零旗标路径、条件"
                "自动满足（r13=§4(i) 判正常收敛路径、r14=全弃权路径、"
                "r15=零旗标路径，成因三分如实分列不合并）；条件 (ii) "
                "bottom 全旗聚合弃权率 11/13=0.846154≤10/11 满足——"
                "bottom 混淆性弃权较 r14 全弃权（14/14=1.0）回落（§5A "
                "注记下 bottom 三实例弃权率 0.75/0.75/1.0、且出现 2 条"
                "非弃权 placement 旗=弃权出口不再垄断）；条件 (iii) top "
                "全旗聚合弃权率 25/29=0.862069>run-r14 同口径 18/24="
                "0.75（双侧复算）违约——top 轴回退（top 渲染零变更下 "
                "r14→r15 弃权水平回升、跨轮实例群混杂照旧）；⇒ verdict="
                "reject（拒绝支=第 (iii) 项）。三项分开如实记录、不合并。"),
            "counts": {
                "r13_courtyard_by_instance": R13_BOTTOM_COURTYARD_BASELINE,
                "r14_courtyard_by_instance": R14_BOTTOM_COURTYARD_BASELINE,
                "r15_courtyard_by_instance": by_instance,
                "r15_bottom_courtyard_flags_total": bot_courtyard_flags,
                "bottom_flags_r15": flags_bot,
                "bottom_abstain_r15": abst_bot,
                "bottom_abstain_rate_r15": bot_rate,
                "bottom_abstain_rate_r13_baseline":
                    cal._round6(base_ab / base_fl),
                "bottom_abstain_rate_r14":
                    cal._round6(r14_bot_ab / r14_bot_fl),
                "top_flags_r15": flags_top,
                "top_abstain_r15": abst_top,
                "top_abstain_rate_r15": top_rate,
                "top_abstain_rate_r14_baseline":
                    top_base_rate,
            },
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": ("6 派次摘录逐字来自对应 "
                                           "reading_notes（substring "
                                           "fail-closed 校验通过）——"
                                           "bottom 六派次仍按 §4(i) 量化"
                                           "判据把绿色翼瓣/空隙形态判入"
                                           "「系统性正常→不报告」（判读"
                                           "路径延续使用）"),
            "status": ("条件 (i) 满足（零旗标路径）+条件 (ii) 满足"
                       "（bottom 混淆回落）+条件 (iii) 违约（top 回退）"
                       "⇒ verdict=reject；development 域只描述不断言"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r15-prep-record 预注册"
                "机制观察；对照 r14 三实例三种语义化=轮廓/连接形态/"
                "courtyard 矩形）：r15 bottom 三实例 notes 均以「空隙/"
                "翼瓣」几何语义化绿色（清空隙翼瓣/月牙翼瓣状空隙/花瓣状"
                "空隙/热隔离翼瓣），其中 bottom-i2 两派次+bottom-i3 "
                "prep1 共 3 派次显式援引 §5A 仪器注记（「按指引 §5A "
                "仪器注记理解为空隙着色、未作为图元判读」「其绿色分段环"
                "与 §5A 基准环缝描述相符」「§5A 亦注明绿色区域非图元」）"
                "——§5A 颜色→来源映射在 2/3 实例被显式用作判读参照；"
                "r14 的三实例语义化分歧（把绿色读作轮廓/连接形态/"
                "courtyard 矩形三种图元化误读）在 r15 未再现。逐实例 "
                "substring 计数「绿|翼瓣|空隙|§5A」+摘录如实登记（无"
                "期望、不构成判据输入）。"),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）"),
            "status": ("绿区语义化收敛于「空隙非图元」读法、§5A 注记在 "
                       "2/3 实例被显式援引（如实单列、不凌驾字母裁决；"
                       "与条件 (iii) top 回退并存=bottom 侧配套见效/"
                       "top 轴另有构成，两观察分列不合并）"),
        },
        "contact_criterion_continuation": {
            "observation": (
                "接触性判据延续（机制 (b)）：§4(iii)「真实接触 vs 视觉"
                "贴近不可区分→按存在性弃权」路径在本轮 top 视角 6 条 "
                "courtyard 弃权旗中的 5 条上延续生效（逐旗摘录 substring "
                "fail-closed 校验在案）；第 6 条（prep1-top-i3 R15T-003）"
                "为存在性出口（第二条轮廓存在性/归属层不可确认）——出口"
                "构成 5 接触性+1 存在性如实分列（区别于 r14 的 13/13 "
                "全接触性）；top 弃权率 0.909091/0.8/0.875（极差 "
                "0.109091，较 r14 的 0.833333/0.75/0.7 极差 0.133333 "
                "相近、整体水平回升=条件 (iii) 违约的构成）；top 弃权"
                "构成=courtyard 6+silk 15（13 弃权 2 非弃权）+黑点类 1"
                "+疑似焊盘连条/板边条带等其他类 3（逐类计数见 reader."
                "flag_count.by_category）。"),
            "contact_flag_count": len(contact_rows),
            "contact_flags": contact_rows,
            "contact_evidence": CONTACT_CRITERION_EVIDENCE,
            "contact_evidence_check": ("5/5 条摘录逐字来自对应 "
                                       "location_evidence（substring "
                                       "fail-closed 校验通过）"),
            "top_abstain_rates_by_instance": top_rates,
            "top_abstain_rate_range": top_range,
            "status": ("接触性弃权路径语义在 top 视角延续（r13 8/8→"
                       "r14 13/13→r15 5/6）；top 渲染零变更=方向性对照"
                       "如实单列、不凌驾 bottom 主通道字母裁决"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点类现象追踪（机制 (c)）：r15 黑点类旗标 7 条全部弃权"
                "——top 视右上黑点 1 旗（R15T-002 applied-top-i2，r14 "
                "首现现象延续）+bottom 左上黑点 6 旗（i1 1+i2 2+i3 3，"
                "r14 同形态延续）；全部 other_advisory 存在性/接触性"
                "弃权出口；vs r14 黑点类 14 旗全弃权——弃权路径方向"
                "延续、数量下降；另有 3 派次 notes 把黑点判为基准点/"
                "定位类正常特征未报告（prep1-top-i1/applied-top-i3/"
                "prep1-bottom-i1，逐字摘录在案）=同现象跨实例处置分化"
                "（7 弃权+3 判正常+2 派次未提及），如实登记。"),
            "black_dot_flags": black_rows,
            "by_instance": {"top-i1": 0, "top-i2": 1, "top-i3": 0,
                            "bottom-i1": 1, "bottom-i2": 2, "bottom-i3": 3},
            "all_abstain": True,
            "notes_normal_dispositions": (
                "3 派次判正常：prep1-top-i1「右上两黑色实心圆点判为基准"
                "点/连接器定位类正常特征」+applied-top-i3「两枚实心黑点"
                "疑似基准点/安装孔…未作为疑似形态报告」+prep1-bottom-i1"
                "「黑色钻孔点…不构成怀疑对象」（摘录见 evidence 表 "
                "disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点类弃权路径延续+处置实例分化（如实单列、"
                       "不凌驾字母裁决）"),
        },
        "bottom_zero_courtyard_category_shift": {
            "observation": (
                "bottom 零 courtyard 旗=分类通道转移（r15-prep-record "
                "预注册机制观察项）：r14 bottom 14 旗全弃权中含 courtyard "
                "类 4 条（黑点骑跨轮廓 2+阵列顶端疑似接触 2），r15 bottom "
                "13 旗中 courtyard 类=0（旗标全部为 placement "
                "pattern_anomaly 6+other_advisory 7）——r14 的两类 "
                "courtyard 弃权成因现象本轮未再现，bottom 旗标构成整体"
                "转移到 placement/other 通道；r14 的 14 旗全弃权 vs r15 "
                "的 13 旗 11 弃权+2 非弃权（placement 类）——弃权出口"
                "不再垄断 bottom。判据 (i) 在零旗标路径下自动满足（"
                "per supported_requires_all[1] bottom 零旗标同类语义、"
                "如实记入机制观察）。"),
            "bottom_flags_by_category_r15": {
                "placement_pattern_anomaly": {"total": 6, "non_abstain": 2,
                                              "abstain": 4},
                "other_advisory": {"total": 7, "non_abstain": 0,
                                   "abstain": 7},
            },
            "r14_contrast": ("r14 bottom=14 旗全弃权（courtyard 4+other "
                             "10）；r15 bottom=13 旗（弃权 11+非弃权 2，"
                             "courtyard 0）"),
            "status": ("分类通道转移如实记录（单列、不凌驾字母裁决；"
                       "非因果归因——实例群混杂照旧）"),
        },
        "residual_instance_differences": {
            "observation": (
                "残余实例差异（如实单列）：(1) top 弃权率 0.909091/0.8/"
                "0.875（极差 0.109091）——整体水平较 r14 回升（条件 (iii) "
                "违约的构成）；(2) bottom 弃权率 0.75/0.75/1.0（极差 "
                "0.25）——bottom-i3 全弃权（5 旗）、i1/i2 各 3/4；"
                "(3) placement 类处置实例分化：板内孤立焊盘组 bottom-i1 "
                "弃权/bottom-i2 非弃权报告/bottom-i3 弃权+prep1 两实例"
                "判正常不报告（r14=两判正常一弃权）；边缘节距空档 "
                "bottom-i1 跨板出口分化（applied 非弃权报告/prep1 弃权）"
                "——同现象跨板出口不同=判读语义歧义未穷尽；「正确测出"
                "无效同样是有效证据」的同构：测出残余差异同样是有效证据。"),
            "evidence": PLACEMENT_DISPOSITION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("残余差异不凌驾主通道字母裁决；不构成已证因果"
                       "关系（实例群混杂照旧、样本量极小）"),
        },
    }
    metric_lesson_continuation = {
        "role": ("度量设计教训延续（如实，供未来预注册参考；本轮不追溯"
                 "适用；per r15-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r15 三分判据的 (iii) 支（top 全旗聚合弃权率 ≤ run-r14 同"
            "口径）在 top 渲染零变更下触发 reject——「不回退」判据把"
            "配套变更对其他轴的外溢纳入方向归因（bottom 混淆回落 (ii) "
            "满足与 top 回退 (iii) 违约并存：单轴读数不足以定位变更的"
            "全幅效果，per-instance+per-view 分列聚合是必要口径）；"
            "(i) 支在 bottom 零 courtyard 旗路径下自动满足——计数型"
            "判据对「通道转移」（courtyard→placement/other）不敏感，"
            "须配机制观察（分类通道转移单列）补足；跨轮实例群漂移为"
            "已知混杂（r10 实证）、聚合与分层观察分开记账的度量设计"
            "教训链（r9–r14）在 r15 延续。"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一轮候选方向（如实登记，不构成本轮判据"
                   "输入）：top 轴弃权构成（silk 类 15 旗/13 弃权）与"
                   "实例群漂移的分离须更大样本或同实例跨轮设计；不得"
                   "回溯改判既往轮次（r8–r14 字母裁决维持不变）"),
    }
    # r14 分层基线（逐实例弃权率，live 重放；不手工抄数）
    r14_top_rates = {}
    r14_bottom_rates = {}
    for n in INSTANCE_ORDER:
        blk_a = run_r14["instances"][n]["states"]["applied"]
        blk_p = run_r14["instances"][n]["states"]["prep1"]
        fl_n = len(blk_a["reader_flags"]) + len(blk_p["reader_flags"])
        ab_n = (blk_a["compare_v3"]["abstain"]["abstain_count"]
                + blk_p["compare_v3"]["abstain"]["abstain_count"])
        rate_n = cal._ratio(ab_n, fl_n)
        if n.startswith("top"):
            r14_top_rates[n] = rate_n
        else:
            r14_bottom_rates[n] = rate_n
    r14_top_range = cal._round6(
        max(r14_top_rates.values()) - min(r14_top_rates.values()))
    r14_bottom_range = cal._round6(
        max(r14_bottom_rates.values()) - min(r14_bottom_rates.values()))
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R15,
                                "sha256": _sha(REL_PREP_R15)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "supported_requires_all": adj["supported_requires_all"],
            "reject_if": adj["reject_if"],
            "support": prep_doc["attribution_plan"]["primary_channel"][
                "support"],
            "reject": prep_doc["attribution_plan"]["primary_channel"][
                "reject"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "mechanism_observation_separate":
                adj["mechanism_observation_separate"],
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel_metric": prep_doc["attribution_plan"][
            "primary_channel"]["metric"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r15-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮假设检验、与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "bottom_courtyard_non_abstain_by_instance_r15": by_instance,
            "bottom_courtyard_flags_total_r15": bot_courtyard_flags,
            "bottom_abstain_flags_r15": flags_bot,
            "bottom_abstain_count_r15": abst_bot,
            "bottom_abstain_rate_r15": bot_rate,
            "bottom_abstain_rate_r15_arithmetic":
                f"bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                f"{bot_rate}"
                f"（对照 r13 基线 10/11=0.909091；条件 (ii) 阈值 "
                f"{b_num}/{b_den}；bottom 零旗标自动满足条款本轮未触发"
                f"（分母 {flags_bot}>0，bottom_zero_flag={bottom_zero_flag}））",
            "crit1_bottom_courtyard_non_abstain_all_zero": crit1_ok,
            "crit2_bottom_abstain_le_10_11": crit2_ok,
            "top_abstain_flags_r15": flags_top,
            "top_abstain_count_r15": abst_top,
            "top_abstain_rate_r15": top_rate,
            "top_abstain_rate_r15_arithmetic":
                f"top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（条件 (iii) 实测）",
            "crit3_top_abstain_le_r14_baseline": crit3_ok,
            "top_abstain_rate_r14_baseline_live":
                f"{base_top_ab}/{base_top_fl}",
            "top_abstain_rate_r14_baseline_value": top_base_rate,
            "top_baseline_replay_note": (
                "判据 (iii) 基线=同一聚合逻辑对 calibration-run-r14.json "
                "内嵌实例记录（states 层 reader_flags+compare_v3.abstain）"
                "双侧复算，不手工抄数；且与 run-r14 各实例 combined 记账"
                "逐实例交叉核对（fail-closed，见 baseline_cross_check）"),
            "reject_condition_met": rejected,
            "support_condition_met": supported,
            "reject_branch": reject_branch,
            "bottom_courtyard_detail_r15": [
                {"instance": r["instance"],
                 "courtyard_non_abstain_count": by_instance[r["instance"]],
                 "note": r["note"]}
                for r in MAIN_CHANNEL_REGISTERED],
            "baseline_cross_check": {
                "r13_courtyard_by_instance_registered":
                    R13_BOTTOM_COURTYARD_BASELINE,
                "r13_courtyard_by_instance_live": r13_base_live,
                "r14_courtyard_by_instance_registered":
                    R14_BOTTOM_COURTYARD_BASELINE,
                "r14_courtyard_by_instance_live": r14_base_live,
                "r13_bottom_abstain_aggregate_registered":
                    "10/11",
                "r13_bottom_abstain_live": f"{base_ab}/{base_fl}",
                "r14_top_abstain_aggregate_live":
                    f"{base_top_ab}/{base_top_fl}",
                "note": ("基线数字与 run-r13/run-r14 内嵌输入重放实测交叉"
                         "核对一致（fail-closed：live 重放与登记不符即 "
                         "FAIL）；registered=r15-prep-record 登记/判据"
                         "原文，live=本轮从 run-doc 内嵌输入重放实测；"
                         "top 基线无数值登记=按判据 (iii) 「不手工赋值」"
                         "由脚本双侧复算"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "top 视角非弃权旗标面积比出局条目 R14=1→R15=0（回落"
                    "如实记录：r14 唯一条目 R14T-002×GT-REVC-AP-7-C31U4 "
                    "本轮未再现；r15 top 非弃权旗 4 条与同态 GT 零 ≥0.5 "
                    "containment 交叠）——guard_ok=True 如实记录；r15 "
                    "预注册 support 条件不含守门要件（guard_channel 独立"
                    "单列，与三分判据分开、不合并）"),
                "guard_ok": guard_ok,
                "note": ("守门通道按 r15-prep-record attribution_plan."
                         "guard_channel 独立复核（几何门面积比出局条目"
                         "变化如实记录）；不构成 r15 字母裁决输入"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r14 run-record courtyard_tracking 在案先例延续，"
                "r15-prep-record 未另设 secondary_observation 节）——"
                "实测见 courtyard_tracking 节（非弃权 0 条、弃权 6 条"
                "（全部 top）、命中 0；bottom 零 courtyard 旗）"),
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
                "abstain_rate_r15_representative_note": (
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
                    "代表配置）→r15 见代表配置分列；主通道三分判据与门"
                    "各自独立计算、互不凌驾（prep-record "
                    "descriptive_boundary_note 原文语义）——门联合评价 "
                    "与裁决=reject 分列不合并"),
            },
            "r15_total_flags_note": (
                "六实例合计 42 旗标（非弃权 6、弃权 36；全旗标合计弃权率 "
                "0.857143 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；bottom 全旗标聚合"
                "弃权率 11/13=0.846154 为条件 (ii) 度量、top 全旗标聚合"
                "弃权率 25/29=0.862069 为条件 (iii) 度量、各自单列）"),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"support=「{prep_doc['attribution_plan']['primary_channel']['support']}」；"
            f"reject_if=「{adj['reject_if']}」"
            "（r15-prep-record.json hypothesis_test.adjudication 判据原文"
            "，轮后如实执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r15": {
            "role": ("r12 假设通道被动追踪（round13/round14-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，如实"
                     "单列）"),
            "reroute_flag_detail_r15": reroute_rows,
            "reroute_total_r15": len(reroute_rows),
            "reroute_by_instance_r15": {
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
                                 "r15": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径）：r10=2→r11=1→r12=0→"
                "r13 被动追踪=1（R13T-009 在案）→r14=0（R14T-004 子串零"
                "命中）→r15 机械命中=1（R15T-001 非弃权旗含「蛇形」"
                "子串——但为否定式援引：location_evidence 明写「非整段"
                "规则周期蛇形」=§3A 示例 c 收窄判据正确排除候选解释，"
                "非滥用型引用；机械命中与语义裁定如实分记）——不构成 "
                "r15 判据输入（两判据分列互不凌驾）"),
        },
        "stratified_observation": {
            "top": {"r14_by_instance_live": r14_top_rates,
                    "r14_range_live": r14_top_range,
                    "r15_by_instance": top_rates,
                    "r15_range": top_range,
                    "direction": ("r14 三实例 0.833333/0.75/0.7（轮内"
                                  "极差 0.133333）→r15 三实例 0.909091/"
                                  "0.8/0.875（轮内极差 0.109091）——top "
                                  "渲染零变更（r15=renders-r14b 路径字节"
                                  "复用）下弃权率整体水平回升（0.75→"
                                  "0.862069=条件 (iii) 违约的构成；跨轮"
                                  "实例群不同=混杂照旧、方向性描述）；"
                                  "构成=silk 类 15 旗（13 弃权 2 非弃权）"
                                  "+courtyard 6 弃权+黑点类 1+其他 3")},
            "bottom": {"r14_by_instance_live": r14_bottom_rates,
                       "r14_range_live": r14_bottom_range,
                       "r15_by_instance": bottom_rates,
                       "r15_range": bottom_range,
                       "direction": ("r14 三实例 1.0/1.0/1.0（极差 0.0="
                                     "全弃权）→r15 三实例 0.75/0.75/1.0"
                                     "（极差 0.25）——bottom 混淆性弃权"
                                     "整体回落（聚合 1.0→0.846154，条件 "
                                     "(ii) 满足）、且出现 2 条非弃权 "
                                     "placement 旗（弃权出口不再垄断）；"
                                     "bottom-i3 仍全弃权（5 旗）")},
            "confounder_note": (
                "跨轮 reader 实例不同+轮内实例差异=混杂因素照旧声明；"
                "v1.2 工具规约把工具行为钉住（12/12 自述「未读取盘上"
                "任何其他文件」）但判读实例仍为不同实例（r15 notes 措辞"
                "与 r14 不同亦属实例差异、如实登记）；每视角 n=3 仍为"
                "小样本；development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r11: dict, run_r12: dict, run_r13: dict,
                             run_r14: dict) -> dict:
    """courtyard 被动追踪（r11–r14 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r15 非弃权 courtyard 0 条、弃权 6 条
    （全部 top）、bottom 零 courtyard 旗如实入账）。"""
    note_source = {
        "path_rel": REL_PREP_R15, "sha256": _sha(REL_PREP_R15),
        "quote": None,
        "note": ("r15-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r14 "
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
    prior = run_r14["courtyard_tracking"]
    return {
        "note_source": note_source,
        "declaration": ("被动追踪（run-record 链先例延续）：如实记录 "
                        "courtyard 类旗标匹配表现"
                        "（零阈值改动、零期望、不得为提高命中调阈值）"),
        "r15_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "6 条全部 top（按实例 i1×1/i2×2/i3×3）"
                             "+bottom 零 courtyard 类"
                             "旗标（r14 bottom 4 条 courtyard 弃权旗本"
                             "轮未再现——分类通道转移，见 hypothesis_"
                             "test.mechanism_observation."
                             "bottom_zero_courtyard_category_shift）"),
        },
        "courtyard_matches_r15": sum(r["matches"] for r in non_abstain_rows),
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
            "（r15 非弃权 courtyard=0 条：6 条 courtyard 类旗标全部"
            "弃权且全部 top；GT/阈值零改动"),
        "bottom_observation": {
            "fact": ("R15 bottom 13 旗（bottom-i1 4+bottom-i2 4+"
                     "bottom-i3 5）=非弃权 2（placement 类）+弃权 11："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=0（r12 非弃权 20 条→"
                     "r13 0 条→r14 弃权 4 条/非弃权 0→r15 零旗标——"
                     "r14 的黑点骑跨轮廓+阵列顶端疑似接触两类 courtyard "
                     "弃权现象本轮未再现）；弃权构成=other_advisory 7"
                     "（黑点类 6+左上镜像排布 1）+placement 类 4；非弃权"
                     "构成=placement 类 2（边缘节距空档 1+板内孤立焊盘"
                     "组 1）——本轮 12 格全部≥1 旗、无零旗标分母实例"
                     "（measurement_design item 5 口径保留备用：遇零"
                     "分母→None 不编造数值）"),
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
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, instances, view_layer,
                                attribution, raw_texts, parsed_notes,
                                reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9,
                                         run_r11, run_r12, run_r13,
                                         run_r14)

    prep_r15 = _json_load(REL_PREP_R15)
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
            "五键投影（process-v1 §2 步骤3）；R15 reroute 类四旗 "
            "location_evidence 逐字在案（R15T-005/R15T-001 非弃权边界"
            "报告+R15T-002/R15T-004 存在性弃权；R15T-001 含「蛇形」"
            "子串=否定式收窄判据援引——reroute_continuation_r15 逐旗"
            "判定在案）；"
            "R15 top courtyard 弃权旗 6 条中 5 条接触性判据理由逐旗摘录"
            "在案（contact_criterion_continuation；1 条存在性出口分列）；"
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
                     "bottom-i1 单旗）——实例层/视角层弃权率全部有定义；"
                     "measurement_design item 5 口径保留备用（遇零旗标"
                     "分母→按库侧 cal._ratio 先例=None+文字说明，不编造"
                     "数值）"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R15,
         "role": "observation_guidance_r15_active",
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
         "role": "r14_dev_record_preregistration_source",
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
         "role": "render_png_applied_top_r15_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r15_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"],
         "role": "render_png_prep1_top_r15_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r15_byte_reuse_r14b",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r15",
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
            "note": prep_r15["instrument_change"]["note"],
            "components": [],
            "unchanged_components": list(prep_r15["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v["attribution_channel"],
                 "instrument_change": v["instrument_change"]}
                for v in prep_r15["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r15["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r15["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r15["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R15, "sha256": _sha(REL_PREP_R15)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；R15T/R15B 示例旗 ID 前缀已随 r15 指引 §6 落盘"
            "固化、无需派发层覆盖（per r15-prep-record protocol_"
            "amendment.naming：指引本体即为 r15 前缀；实例间编号独立、"
            "同实例两板各自从头编号=r15 实测输出行为、与 r13/r14 跨板"
            "连续不同，见 dispatch_mode.flag_id_continuity_note）"),
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
                    "r13 指引 §4（经 r15 指引 §2–§7 逐字保留、原文适用）："
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
                                      "不进任何 reader 上下文）、除指引 "
                                      "§5A 仪器注记外零 legend/零其他解释；"
                                      "每图独立判读；跨实例/跨视角禁止交流"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R15,
                                 "sha256": _sha(REL_GUIDANCE_R15),
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R13,
                                     "sha256": _sha(REL_GUIDANCE_R13),
                                     "role": ("r15 指引的机械变换基座"
                                              "（§2–§7 判据文本逐字承 "
                                              "r13；r13 指引=r13 轮落盘"
                                              "产物）")},
                                 "change_note": GUIDANCE_NOTE},
            },
            "note": ("轮次预注册链：round14-dev-record.json（e6354d5c…，"
                     "next_iteration_targets[0] 指引侧颜色-图层映射配套"
                     "候选原文被 r15-prep-record 逐字摘录预注册+用户 "
                     "2026-09-08「请继续」批准执行（user_directive_note "
                     "在案））→r15-prep-record.json（4c6cd919…，本轮预"
                     "注册件，measurement_design 五条聚合口径与 "
                     "hypothesis_test.adjudication 三分判据先于盲读冻结；"
                     "instrument_change.changed=false）先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；"
                     "pre_round_review=satisfied_by_prior_evidence——r14 "
                     "拒绝支第二支机制证据在案、无需新增视觉评审）→"
                     "observation-guidance-r15.md（d5babc93…）由 r13 指引"
                     "机械变换生成落盘冻结（本轮唯一判读依据；§2–§7 判据"
                     "文本零变更=分段+substring 双重断言复核；§5A=仪器"
                     "事实注记、非判据）→渲染零变更（renders-r14b 四图"
                     "字节复用=四 PNG sha 与 witness 登记值逐一相等，即 "
                     "r14 轮盲读所用同一批文件）→12 次盲读→比对记录（"
                     "读者产物零改动）。GT 重投影（derivation-log-r5."
                     "json，13 条 frame_box_pct_r5）已在案沿用（GT 全部 "
                     "side=top 且 top 渲染零变更=重投影输入未变；bottom "
                     "渲染字节复用不触及）；GT 冻结纪律：轮后未增删改；"
                     "gt-audit-r1 结论维持 GT 零改动（三候选关闭，"
                     "gt_audit_reference 在案）。"),
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
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）与 R9"
                     "（§3A 示例 c 增补轮）与 R10（零变更重复轮）与 R11"
                     "（协议侧单变量轮：每视角实例 1→3，v1.1 追加式）与 "
                     "R12（单变量指引侧变更轮：示例 c 收窄+协议侧派发层 "
                     "v1.2 首轮）与 R13（单变量指引侧变更轮：§4 存在性"
                     "判据可操作化+pre_round_review 评审前置）与 R14"
                     "（纯仪器变更轮：bottom 渲染件更换 renders-r5→"
                     "renders-r14b，verdict=reject）run 在案；"
                     "R15=指引侧单变量轮（§5A 渲染配色仪器注记配套："
                     "r14 reject 拒绝支第二支所指向的配套；指引 r13 机械"
                     "变换生成 r15、渲染零变更 renders-r14b 字节复用）；"
                     "轮间对比"
                     "由后续 round15-dev-record（另包落盘）与 "
                     "channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取与通道重放为纯函数"
            "（六实例旗数 11/10/8/4/4/5→代表配置 top-i2+bottom-i1（top "
            "中位实例唯一；bottom 中位 4 为 i1/i2 tie、按先序取 bottom-i1 "
            "并如实注明）唯一可复算），无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-08-r15（事件序="
            "round14-dev-record（e6354d5c…，在案）→r15-prep-record"
            "（4c6cd919…，本轮预注册件，先于盲读冻结）→r15 指引机械"
            "变换落盘（d5babc93…，本轮唯一判读依据）→renders-r14b 四图"
            "字节复用（渲染零变更）→12 次盲读→比对记录；在案延续=gt-"
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
                                run_r13: dict, run_r14: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """run-r15 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 11, "top-i2": 10, "top-i3": 8, "bottom-i1": 4,
                  "bottom-i2": 4, "bottom-i3": 5}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 10, "top-i2": 8, "top-i3": 7, "bottom-i1": 3,
                "bottom-i2": 3, "bottom-i3": 5}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 42:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.785714 \
            or agg["flag_count_total"] != 14 \
            or agg["abstain_count_total"] != 11:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "reject":
        _fail("假设字母裁决与预注册判据复算不符")
    m = hyp["measurement"]
    if m["bottom_courtyard_flags_total_r15"] != 0 \
            or m["bottom_abstain_flags_r15"] != 13 \
            or m["bottom_abstain_count_r15"] != 11 \
            or m["bottom_abstain_rate_r15"] != 0.846154 \
            or m["bottom_courtyard_non_abstain_by_instance_r15"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail("主通道 (i)(ii) 计数与实测不一致")
    if m["top_abstain_flags_r15"] != 29 or m["top_abstain_count_r15"] != 25 \
            or m["top_abstain_rate_r15"] != 0.862069 \
            or m["top_abstain_rate_r14_baseline_value"] != 0.75:
        _fail("主通道 (iii) 计数与实测不一致")
    if m["crit1_bottom_courtyard_non_abstain_all_zero"] is not True \
            or m["crit2_bottom_abstain_le_10_11"] is not True \
            or m["crit3_top_abstain_le_r14_baseline"] is not False:
        _fail("三分判据布尔与实测不一致")
    if m["reject_condition_met"] is not True \
            or m["support_condition_met"] is not False:
        _fail("判定布尔与实测不一致")
    if "(iii)" not in (m["reject_branch"] or ""):
        _fail("拒绝支归属与实测不一致")
    if m["guard_channel"]["guard_ok"] is not True:
        _fail("守门通道布尔与实测不一致")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.109091 \
            or vl["bottom"]["abstain_rate_range"] != 0.25:
        _fail("视角层极差与实测不一致")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 0 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.0:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != []:
        _fail("matches 明细与实测不一致（r15 应零匹配）")
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
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 4:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R14 1→R15 0；类别 R14 0→R15 0）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r15_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r15_category_mismatch_entries"]) != 0:
        _fail("通道条目数与实测声明不一致")
    # courtyard 追踪与实测一致（r15 非弃权 courtyard=0、弃权=6、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r15"] != 0 or len(
            ct["r15_courtyard_flags"]["non_abstain"]) != 0:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r15_courtyard_flags"]["abstain"]) != 6:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 逐旗判定/工具规约/量化判据/接触性/黑点/placement/绿区摘录逐字在案
    mo = hyp["mechanism_observation"]
    for r in hyp["reroute_continuation_r15"]["reroute_flag_detail_r15"]:
        if r["form_desc_excerpt"] not in raw_texts[r["source"]]:
            _fail(f"逐旗判定摘录与 reader 原文不符: {r['flag_id']}")
    for ev in mo["main_channel_three_criteria"]["reader_note_evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["green_semantics_by_instance"]["evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"绿区语义化摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["contact_criterion_continuation"]["contact_evidence"]:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"接触性判据摘录与 reader 原文不符: {ev['flag_id']}")
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r15")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R15), run_bytes,
                         "calibration-run-r15.json")
    run_sha = _sha(REL_RUN_R15)
    # round15-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s55-cal-r15] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 6、弃权 36）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s55-cal-r15] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s55-cal-r15] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s55-cal-r15] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}")
    print(f"[s55-cal-r15] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s55-cal-r15] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    m = hyp["measurement"]
    print(f"[s55-cal-r15] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；判据 (i) bottom courtyard 非弃权="
          f"{m['bottom_courtyard_non_abstain_by_instance_r15']}"
          f"/bottom 零 courtyard 旗={m['bottom_courtyard_flags_total_r15']}"
          f"/crit1={m['crit1_bottom_courtyard_non_abstain_all_zero']}"
          f"；判据 (ii) bottom 全旗聚合弃权={m['bottom_abstain_count_r15']}"
          f"/{m['bottom_abstain_flags_r15']}={m['bottom_abstain_rate_r15']}"
          f"≤10/11/crit2={m['crit2_bottom_abstain_le_10_11']}"
          f"；判据 (iii) top 全旗聚合弃权={m['top_abstain_count_r15']}"
          f"/{m['top_abstain_flags_r15']}={m['top_abstain_rate_r15']}"
          f" vs run-r14 基线（双侧复算）={m['top_abstain_rate_r14_baseline_live']}"
          f"={m['top_abstain_rate_r14_baseline_value']}"
          f"/crit3={m['crit3_top_abstain_le_r14_baseline']}"
          f"/拒绝支={m['reject_branch']}"
          f"/guard_ok={m['guard_channel']['guard_ok']}；机制观察单列）")
    mo = hyp["mechanism_observation"]
    print(f"[s55-cal-r15] 机制观察要点：绿区语义化（"
          f"{ {k: v['semantic_mode'] for k, v in mo['green_semantics_by_instance']['green_semantics_by_instance'].items()} }）；"
          f"黑点类 7 旗全弃权+3 派次 notes 判正常；bottom 零 courtyard 旗"
          f"=分类通道转移（r14 bottom 4 条 courtyard 弃权未再现）；"
          f"placement 类 6 旗（2 非弃权+4 弃权）")
    print(f"[s55-cal-r15] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s55-cal-r15] channel_attribution: "
          f"geo R14={len(ca['channel_1_geometry_gate']['r14_area_ratio_rejected_entries'])}"
          f"→R15={len(ca['channel_1_geometry_gate']['r15_area_ratio_rejected_entries'])}, "
          f"cat R14={len(ca['channel_2_category_gate']['r14_category_mismatch_entries'])}"
          f"→R15={len(ca['channel_2_category_gate']['r15_category_mismatch_entries'])}")
    print(f"[s55-cal-r15] commit: run={run_status}（round15-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s55-cal-r15] sha256[:8] {Path(REL_RUN_R15).name} = "
          f"{run_sha[:8]}")
    print("[s55-cal-r15] R15 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
