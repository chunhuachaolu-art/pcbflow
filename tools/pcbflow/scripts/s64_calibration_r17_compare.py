#!/usr/bin/env python
"""CAL-R17-CLOSE：reader 判读迭代第十七轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s58_calibration_r16_compare.py 同构，仅输入与轮次
常量不同；R17=development 域轴1 仪器轮（axis-experiment-plan-r17-r20
stage1 R17=A1_render_resolution_x2：渲染分辨率 640→1280dpi 四图全新
渲染 renders-r17、r14b 配色规则重放、非字节复用；判读指引=
observation-guidance-r17.md（07c520be，由 r15 指引机械变换生成、
本轮唯一判读依据；§2–§7 判据逐字承 r15、§5A 两处描述性同步）；
GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed=true
已预注册）——唯一操纵因子=渲染分辨率倍增；检验 r17-prep-record.json
预注册假设（hypothesis_id=axis-plan-r17-resolution-double，判据=
r17-prep-record.json hypothesis_test.adjudication 三分判据预注册原文，
脚本从 prep-record 文件加载判据文本、基线数字 live 重放不手工抄数）：
「top（及 bottom）的 contact/存在性族弃权源于 640dpi 下细节不可负责任
分辨；分辨率倍增至 1280dpi 后弃权率显著回落」：

  T1  解析 12 个 reader-raw-r17-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r17-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r16 同一比较脚本血统；聚合口径零改动）：
      (1) 实例主记录=六实例各自两板合计 flag_count/abstain_count/
      abstain_rate（6 位小数；零旗标分母=None）/非弃权清单（r17 实测
      flag_id 两板各自从头编号——非弃权/弃权清单按 (state, flag_id)
      限定，跨板重号如实登记；与 prep-record naming「同实例跨板连续」
      声明不同=读者实例输出行为差异、如实入账不作废，与 r15/r16 实测
      同形态）/逐旗 containment+area_ratio 匹配明细；(2) 视角层=每视角
      3 实例 flag_count/abstain_rate/matches 各中位数+min+max 三分列
      不取整（实例层=两板合计全部≥3 旗、弃权率全部有定义；派次层
      2 格零旗标=prep1-bottom-i1/prep1-bottom-i2）；(3) GT 匹配
      双口径=union（≥1 实例命中）与 agreement（≥2/3）并列+逐 GT 条目
      matched_by_count（0..3；召回分母=GT 13 条）；(4) 联合门（APR-0011
      阈值零改动）=代表配置（每视角 flag_count 中位数实例）算一轮
      joint+per-metric 实例间范围+逐实例原始记录三者并列不挑优；(5)
      bottom 零旗标分母=按库侧 cal._ratio 先例 None+文字说明（本轮
      派次层 2 格零旗标按零旗格处理、实例层无 None，口径在案）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且 top 渲染本轮
      为同一板 Edge.Cuts 几何+同 40pt 组合页仅 dpi 640→1280 的原生重
      渲染（framing-r17 single_variable_change 在案），frame_box_pct_r5
      =GT 框在渲染图像空间的归一化坐标口径、随 r14→r17 顶层更换先例
      沿用（r14 先例：renders-r5→r14b 顶层更换时重投影台账沿用不重
      派生），本轮零新派生；bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（三分判据，r17-prep-record.json hypothesis_test.
      adjudication 原文）逐支执行：M1=top 全旗聚合弃权率（12 派次
      全口径）——supported=(a) M1 ≤0.671429（=r16 零变更基线 0.771429
      绝对降幅 ≥0.10 的计划件显著收益阈值；r16 基线 27/35 双侧复算
      live 重放交叉核对一致）；reject=(b) M1 ≥0.771429（=r16 零变更
      基线水平，live 重放交叉核对一致）→轴1 证伪；marginal=(c)
      0.671429<M1<0.771429（带内=与跨轮漂移噪声不可分）。letter 裁决
      唯一正式；守门 G1/G2 独立单列（G1=bottom courtyard 非弃权 0/0/0
      维持、G2=guard_ok=True 维持；任一破坏→轴1 按 plan early_stop_rule
      出局）；机制观察单列（mechanism_observation_separate）：呈现尺寸
      机制观察（本轮关键：逐件收集 reader reading_notes 关于图像呈现
      尺寸/清晰度/分辨率的自述——对照 reject 支内嵌的「视觉编码器尺寸
      上限抵消增益」解释）；M2=bottom 全旗聚合弃权率（对照 r16 基线
      12/14=0.857143 live 复算）+零旗标派次计数（prep1-bottom-i1/i2）
      +M3=黑点族弃权旗数（分型件 rubric 口径，对照 r16=12）；top 新
      现象（1280 下新可见细节引发的新旗：椭圆焊盘截断带/半填充圆形/
      QFP 焊盘条疑似间断/引脚排延伸差异——逐件摘录）与 top 弃权率
      上升构成分型；bottom courtyard 非弃权 0/0/0 与 courtyard 旗计数
      （对照 r16 的 14 弃权+1 非弃权）。
      → calibration-run-r17.json。
  T3  development 域记录（R16→R17 方向性对照/假设裁决/联合评价趋势/
      下一迭代目标=轴2/轴3 转向）由后续 dev-record 包落盘（round17-
      dev-record，另包执行）；本包仅产出 run-r17、零 dev-record 写入。

通道归因纪律（vs R16；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/
s55/s58 deviation_note 口径）：本轮对 R15/R16 均以内嵌输入（reader_flags/
gt_entries/flag_views，run sha 在案）+ compare_v3 同源几何原语
（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R17 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「未读取盘上任何其他文件」（12/12 在案；
applied-top-i2 另自述「未做任何程序化图像处理」=v1.2 规约逐字自述
在 r17 首次出现）；多派次自述图像呈现尺寸（约 1000px 宽/约 1000×1000/
约 1500px）与清晰度限制=实例自述异质性如实登记（仪器 PNG 实测
4009×4009/4010×4009、与自述呈现尺寸的差=呈现端缩放，属读者可见性
机制观察、不构成违规）；跨轮实例全重抽+轮内实例差异=混杂因素照旧
声明——本轮唯一操纵因子=渲染分辨率（实例群重抽为轮际比较的固有
混杂、per axis-plan comparison_rule.drift_confound_note 显式容忍）。
输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件
=缩进格式冻结原始判读件、本轮零改动直读（direct JSON 解析、12 件
parse 校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round17-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量 2026-09-09
/ 2026-09-09-r17）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s64_calibration_r17_compare.py   （仓库根执行）
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

DECLARED_DATE = "2026-09-09"
ROUND_ID = "2026-09-09-r17"
ROUND_LABEL = "r17"
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
REL_PREP_R17 = "out/v3-tl2/calibration/r17-prep-record.json"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DEV_R10 = "out/v3-tl2/calibration/round10-dev-record.json"
REL_DEV_R11 = "out/v3-tl2/calibration/round11-dev-record.json"
REL_DEV_R12 = "out/v3-tl2/calibration/round12-dev-record.json"
REL_DEV_R13 = "out/v3-tl2/calibration/round13-dev-record.json"
REL_DEV_R14 = "out/v3-tl2/calibration/round14-dev-record.json"
REL_DEV_R15 = "out/v3-tl2/calibration/round15-dev-record.json"
REL_DEV_R16 = "out/v3-tl2/calibration/round16-dev-record.json"
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
REL_FRAMING_R17 = "out/v3-tl2/calibration/render-framing-r17.json"
REL_WITNESS_R17 = "out/v3-tl2/calibration/render-witness-r17.json"
REL_GUIDANCE_R17 = "out/v3-tl2/calibration/observation-guidance-r17.md"
#: 本包唯一新建输出（防覆写护栏语义照 s58；不在 FROZEN_SHA256 锚集）。
REL_RUN_R17 = "out/v3-tl2/calibration/calibration-run-r17.json"

#: 12 份盲读原始件（6 实例×2 板；r17 实测 flag_id 两板各自从头编号，
#: prep1-bottom-i1/i2 两派次零旗标）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r17-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r17-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r17-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r17-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r17-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r17-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r17-prep1-bottom-i3.txt",
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

#: R17 渲染：图像来源=renders-r17 四图全新渲染（轴1 唯一仪器变量=
#: dpi 640→1280、像素数×4；r14b 配色规则逐字重放于 1280 像密度重算；
#: 非字节复用；四 PNG 盘上 sha=render-witness-r17 登记值=prep-record
#: instrument_change.renders 登记值，bottom 两板逐字节同 0c2d5c00）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r17/applied-top.png",
    "applied-bottom":
        "out/v3-tl2/calibration/renders-r17/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r17/prep1-top.png",
    "prep1-bottom":
        "out/v3-tl2/calibration/renders-r17/prep1-bottom.png",
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
#: 四 PNG 锚=renders-r17 四图（轴1 全新渲染；盘上 sha=witness-r17 登记
#: 值=prep-record instrument_change.renders 登记值，脚本 fail-closed
#: 三方比对）；四 PDF 锚=r5 在案锚沿用（输入侧 PDF 未变，framing-r17
#: render_source_same_as_r14b）；
#: guidance-r17 锚=本轮唯一判读依据（r15 指引机械变换产物；
#: guidance-r15 锚=其变换基座 d5babc93；两条锚均在案）；
#: prep-r17 锚=本轮预注册件（其 chain_anchors 内嵌 axis-plan/framing-
#: r17/witness-r17/dev-r16/run-r16 锚，脚本加载后与盘上实测逐一交叉
#: 核对）；run-r16 锚=M1 基线（27/35=0.771429）与 G1/G2 守门基线的
#: 双侧复算输入（run sha 在案）；run-r15 锚=通道归因对照轮输入；
#: 其余沿用 s58 在案锚。
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
    REL_GUIDANCE_R17:
        "07c520be528708a509e4ec3f9c869a1fbe9ec59fa985813ea20627acd0e70616",
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
    REL_PREP_R17:
        "ceba4fef181f73a1e7ecb5f1765ca7a158551ad91a48413820bbc4683688c94c",
    REL_AXIS_PLAN:
        "b6ec646791064a33912354cb02323d64b3d2886ba8e4f73b1f91d93596aa25ce",
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
    REL_DEV_R16:
        "589fe62f331d2ae0d98bf32bfcbeacad66926f8bc0c4d088ec873ad01fe39c4a",
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
    REL_RUN_R16:
        "2c1f8265e553d3df2d5fcb3c19a87363e7a977ea19d5b74a3ce7b20094e7ddb8",
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    REL_FRAMING_R17:
        "a1084c14beebeea2ddd0080cc304419ebcc51f9e3c9f247b7e1ecb41ac724af4",
    REL_WITNESS_R17:
        "e979bec2bfa2df26e16fd71ba91abfe6f04d453364f9420d2583a6dfca5cdeef",
    RAW_FILES["applied-top-i1"]:
        "c5c242e5b06e61fa0251f4037b5b4e1b22c9e5401695ccb7dc9c80c036dcf866",
    RAW_FILES["prep1-top-i1"]:
        "8185be49035ef35133558aa1659ad6b155cb6bce94e7b97bb412ac7ab40bc33e",
    RAW_FILES["applied-top-i2"]:
        "7b7e08197e1a6335b7bc056a4390a31d46f2f908414239878c0fd3cf6992881a",
    RAW_FILES["prep1-top-i2"]:
        "7b26fcbd4ddd661c291dbf29a811e5b4f238b0c04fa3f95ff04f44058027bd90",
    RAW_FILES["applied-top-i3"]:
        "434a5dafcc0ddbb739e3401d29c94952a9f0c26da030f44c445f53794f3b4429",
    RAW_FILES["prep1-top-i3"]:
        "3f08cb21c3e1f5eb3680a4c56a66bd4924c01f993162fc99a1481029183683de",
    RAW_FILES["applied-bottom-i1"]:
        "4404f838cad942dc2adbf15e5825172ca248b9862dd666323013ed922265dfe7",
    RAW_FILES["prep1-bottom-i1"]:
        "9c8c801c9421c231d06aa75635fc295bcef951b1a354b4557882c7493f3af8cf",
    RAW_FILES["applied-bottom-i2"]:
        "ad31d3ca247d5e0c3949039799af9d67c2bc31b78cd63a9622366f588de94eee",
    RAW_FILES["prep1-bottom-i2"]:
        "cc5002c6ed5f42c5083e22db2cda4a60cd521be1a0e684a8fb7d52b6cb713537",
    RAW_FILES["applied-bottom-i3"]:
        "e8c7f01b123e4406acb6d4ded9709c134e15667d2fbde2acb77eda92770b223d",
    RAW_FILES["prep1-bottom-i3"]:
        "f37ab8ca913f69c98ccadfbcdf2068c5bb727a71f08bb1d74da680271f7f0c15",
    PNG_FILES["applied-top"]:
        "b35315efc7b941404cd4d30fbcbb6159d86be0cd88e9bda1d336421c5dc7a1b5",
    PNG_FILES["applied-bottom"]:
        "0c2d5c00dd09200fc2cbf03bf5682cb9421c32f11146660189da6b285a1be4a0",
    PNG_FILES["prep1-top"]:
        "bdce8bbbb9d05ac52ee5c64c4724063662c33c591869090b6d16e4d2d90ef3b8",
    PNG_FILES["prep1-bottom"]:
        "0c2d5c00dd09200fc2cbf03bf5682cb9421c32f11146660189da6b285a1be4a0",
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
    "盲读词只含图像路径（renders-r17 四张全新渲染 1280dpi=轴1 唯一"
    "仪器变量、非字节复用）+observation-guidance-r17.md"
    "（07c520be，r15 指引机械变换产物、本轮唯一判读依据；旗 ID 前缀 "
    "R17T-/R17B- 随指引 §6 落盘固化——本轮指引本体即为 r17 前缀、"
    "无需派发层覆盖，per r17-prep-record protocol_amendment.naming；"
    "reader-r17-{top,bottom}-i{1,2,3} 为派发指令命名）+起始序号+v1.2 "
    "工具行为规约"
    "硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/衍生图像"
    "生成等）；判读只允许以 Read 工具查看原图（同一原图可重复查看））；"
    "无任何 GT 坐标/类别提示/期望缺陷描述、零诊断报告内容（渲染探针链与 "
    "framing/witness/diag-r17-render 记录不进任何 reader 上下文）、"
    "零 legend/零其他解释"
    "（判读输入=指引+单张 PNG+派发指令，与既往轮同构，仅渲染件更换）；"
    "读图者不接触 GT/派生台账/任何校准"
    "产物路径；跨实例/跨视角禁止交流（12 次盲读相互独立——独立性是"
    "多实例协议的前提，亦为轴1 收益裁决有效性的前提，per r17-prep-"
    "record read_prohibition_note）")

#: 派发模式结构化记录（R17=轴1 仪器轮：每格 3 实例、两波次串行
#: 保序；派发结构与 r16 同构，协议侧零新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R17T-001..005；prep1 R17T-001..003",
        "top-i2": "applied R17T-001..005；prep1 R17T-001..003",
        "top-i3": "applied R17T-001..005；prep1 R17T-001..004",
        "bottom-i1": "applied R17B-001..004；prep1 零旗标（0 派次旗）",
        "bottom-i2": "applied R17B-001..003；prep1 零旗标（0 派次旗）",
        "bottom-i3": "applied R17B-001..004；prep1 R17B-001",
    },
    "flag_id_continuity_note": (
        "r17 实测=flag_id 两板各自从头编号（同一实例 applied 与 prep1 "
        "派次内各自独立起编；跨板同号如实登记）——与 r15/r16 实测同"
        "形态；与 r17-prep-record protocol_amendment.naming「同实例"
        "跨板连续」的声明不同，属读者实例输出行为差异、如实入账不作废"
        "（非盲读违规、不作废任何产物）；编排"
        "侧因此把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R16→R17 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮单变量="
                  "渲染分辨率倍增（renders-r17 四图全新渲染 640→1280dpi"
                  "，r14b 配色规则重放；指引=observation-guidance-r17.md"
                  " 机械变换产物、§2–§7 判据逐字承 r15，仅轮次标识同步"
                  "+本轮变更声明重写+§5A 两处描述性 px 同步）；实例群"
                  "重抽为轮际比较固有混杂（per axis-plan "
                  "comparison_rule.drift_confound_note 显式容忍）；协议"
                  "侧零新增条款"
                  "（v1.2 沿用：派发指令继续含纯 Read 直读硬性条款，"
                  "12/12 派次自述「未读取盘上任何其他文件」，见 "
                  "reader_tool_evidence；指引 §2–§7 实质判据通道零变更；"
                  "GT/阈值零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R17 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何其他文件」"
    "（12/12 逐字摘录在案 reader_tool_evidence；applied-top-i2 另自述"
    "「未做任何程序化图像处理」=v1.2 规约逐字自述在 r17 首次出现）；"
    "多派次自述图像呈现尺寸与清晰度限制（applied-top-i2「图像以约 "
    "1000px 宽度呈现，丝印文字高度仅数像素」、applied-top-i3「呈现尺寸"
    "约 1000×1000」、prep1-top-i3「图像以约 1000px 宽度呈现」、"
    "prep1-bottom-i3「全图以约 1500px 呈现」、applied-bottom-i3「单个"
    "焊盘约占图宽 2%」——仪器 PNG 实测 4009×4009/4010×4009（witness-"
    "r17 image_wh），自述呈现尺寸<仪器像素界=呈现端缩放的读者可见性"
    "自述异质性，如实登记、不构成违规；另 7 派次以「分辨率高/清晰度"
    "良好/接近可判上限」等措辞自述清晰度，见 presentation_size_"
    "mechanism_observation 逐件摘录）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/零 "
    "legend/零其他文件接触=非盲读违规；本轮唯一操纵因子=渲染分辨率"
    "倍增（实例群全部重抽为轮际比较固有混杂，per axis-plan "
    "comparison_rule.drift_confound_note 显式容忍）；跨轮实例不同+"
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
    "本轮指引=observation-guidance-r17.md（07c520be，由 r15 指引 "
    "d5babc93 机械变换生成、本轮唯一判读依据，per r17-prep-record "
    "guidance_reuse：mode=mechanical_transform_derive、edit_list 10 项"
    "逐字登记、§2–§7 分段逐字保留断言复核在案）：§2 类别枚举/§3 位置"
    "口径/§3A 示例（含示例 c）/§4 置信度与弃权（含量化判据 (i)(ii)(iii)、"
    "接触性判据、三路出口、反放宽条款）/§5/§6/§7 判据文本逐字承 r15；"
    "变更=轮次标识机械同步（标题/声明日期 2026-09-09/round_id_constant "
    "2026-09-09-r17/本轮性质行/示例 reader_id）+本轮变更声明节重写+§5A "
    "两处描述性同步（首句渲染件语义「本轮渲染件为 1280dpi 新渲染，非"
    "字节复用」、px 数与出处句随仪器更新：橙 81672→326460、绿 "
    "206632→903366、探针句改写「640dpi 期探针值为 206632/206052 px…"
    "本轮 1280dpi 实测绿 903366 px」——px 数为仪器侧像素计数事实、非"
    "判据）；§6 示例旗 ID 前缀 R17T-/R17B- 随指引落盘固化（r13→r15 "
    "「随指引落盘固化」路径回归，无需派发层覆盖）；§5A=仪器事实注记、"
    "非判据——不构成任何「应判正常/无需报告」的指示，不降低任何存在性、"
    "归类、定位或报告的责任门槛（per r17-prep-record no_loosening_note；"
    "反放宽条款与三路出口随指引本体原样生效）——描述性同步、判断责任"
    "标准一字未松")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 17 轮迭代"
    "（development 域轴1 仪器轮（渲染分辨率倍增 640→1280dpi，四图"
    "全部）：迭代轮不得冒充留出证据；执行 axis-experiment-plan-r17-r20"
    "（b6ec6467 冻结件）stage1 R17，用户 2026-09-09「三条轴单独/组合/"
    "全组合尝试，选择收益最大的继续」（user_directive_note 在案））。")

INSTRUMENT_NATURE = (
    "轴1 仪器轮（渲染侧单变量轮）：仪器变更=renders-r17 四图全新渲染"
    "（dpi 640→1280、像素数×4、r14b 配色规则逐字重放（白墨图元→橙 "
    "(255,165,0)、板内空隙白→绿 (0,128,0)、mask 于 1280 像密度重算、"
    "z 序/混合数学不变）、margin 240px 物理等值；非字节复用；四 PNG "
    "盘上 sha=witness-r17 登记值=prep-record instrument_change.renders "
    "登记值 fail-closed 三方一致；instrument_change.changed=true 已预"
    "注册）+判读指引=observation-guidance-r17.md（07c520be，r15 指引"
    "机械变换产物、§2–§7 判据逐字承 r15，仅轮次标识同步+变更声明重写"
    "+§5A 两处描述性 px 同步）+GT/阈值零变更（13 条冻结；APR-0011 与 "
    "CONTAINMENT_MIN/AREA_RATIO_MAX 只作口径引用）+协议零变更（v1.1+"
    "v1.2 维持）：唯一实验变量=渲染分辨率（per r17-prep-record "
    "manipulated_factor；axis_id=A1_render_resolution_x2；"
    "changed_variables[0].instrument_change=true）")

#: 预注册主通道三分判据所用基线（零覆盖；per r17-prep-record
#: hypothesis_test.adjudication 原文：supported=M1 ≤0.671429（=r16
#: 零变更基线 0.771429 绝对降幅 ≥0.10 的计划件显著收益阈值）、
#: reject=M1 ≥0.771429（=r16 零变更基线水平）、marginal=0.671429<
#: M1<0.771429）。
#: 基线数字 live 重放（同一聚合逻辑对 run-r16 内嵌实例记录双侧复算、
#: 不手工抄数）并与下列在案登记值交叉核对（fail-closed，不符即中止）：
#: (27,35)=0.771429（r17-prep-record chain_anchors.run_r16_baseline_
#: anchor.frozen_values 与 axis-plan baselines_registered.r16_baseline
#: 双锚在案）。
BASE16_TOP_AGGREGATE_REGISTERED = {"abstain": 27, "flags": 35}
#: 0.671429=0.771429−0.10（axis-plan comparison_rule.
#: significant_benefit_definition「相对 r16 基线 M1 绝对降幅 ≥0.10」
#: 的派生阈值，与 prep-record adjudication.supported 原文数值一致；
#: 判据比较用 6 位定点整数交叉相乘（×10^6，避免浮点）。
SUPPORTED_THRESHOLD_6DP = 671429
REJECT_THRESHOLD_6DP = 771429
#: bottom 侧观察基线（M2；per axis-plan baselines_registered.r16_baseline
#: .M2_bottom_aggregate_abstain_rate=0.857143；live 重放交叉核对
#: 12/14）。
BASE16_BOTTOM_AGGREGATE_REGISTERED = {"abstain": 12, "flags": 14}
#: M3/M4 基线登记值（axis-plan baselines_registered.r16_baseline 在案；
#: M3=分型件 rubric 口径黑点族弃权旗数、M4=top 逐实例弃权率极差；
#: 脚本对 axis-plan 原文 fail-closed 装载核对，另对 run-r16 live 重放
#: 交叉核对 M4 的逐实例构成）。
AXIS_R16_M3_BLACKDOT_RUBRIC = 12
AXIS_R16_M4_TOP_RANGE = 0.261904
R16_TOP_INSTANCE_RATES_REGISTERED = {"top-i1": 0.666667,
                                     "top-i2": 0.928571,
                                     "top-i3": 0.666667}
R16_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}
#: 黑点族链（分型件 rubric 口径在案：r15=8、r16=12；本件只登记 r16
#: 基线与 r17 实测对照，更早轮次链不重算）。

#: bottom 侧观察（G1 守门）逐实例登记表（bottom courtyard 类非弃权
#: 旗；程序实测与登记一致性 fail-closed：实测值须与本表 expected 逐一
#: 相等；per r17-prep-record guard_channel「G1=bottom courtyard 非弃权
#: 0/0/0 维持（对照 r15/r16 在案 0/0/0）」；守门独立单列、不影响字母）。
SIDE_OBS_REGISTERED = [
    {"instance": "bottom-i1", "expected": 0,
     "note": ("r16 零非弃权 courtyard→r17 实测 0：本轮 bottom-i1 零"
              "courtyard 类旗标（4 旗=other_advisory 4，其中弃权 3；"
              "applied 4 旗+prep1 零旗标格）——零旗标路径+零 "
              "courtyard 类路径")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r16 零非弃权 courtyard→r17 实测 0：本轮 bottom-i2 零"
              "courtyard 类旗标（3 旗=placement 1（非弃权）+other 2，"
              "applied 3 旗+prep1 零旗标格）——r16 的 applied-bottom-i2 "
              "黑点-轮廓近邻 courtyard 弃权旗 2 条在本轮未再现（黑点"
              "仍被报为 other_advisory）")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r16 零非弃权 courtyard→r17 实测 0：本轮 bottom-i3 有 "
              "courtyard 类旗标 1 条（prep1 R17B-001 孤立焊盘对绿色"
              "轮廓近邻+courtyard 归属不确定弃权），全部弃权——非弃权 "
              "courtyard=0 由全弃权路径维持（与 r16 零旗标路径成因"
              "不同，如实分列）")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。applied-top-i2「未做任何程序化图像
#: 处理」逐字自述为 r17 首次出现，如实登记。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据给定 PNG（applied-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i2",
     "excerpt": "仅依据给定 PNG 的可见内容逐图独立判读，未读取盘上任何其他文件，未做任何程序化图像处理"},
    {"source": "prep1-top-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据给定 PNG（applied-top.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG（prep1-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 applied-bottom.png 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据给定 PNG（prep1-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 六派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——绿色翼瓣/
#: 空隙形态在 r17 指引（§2–§7 逐字承 r15）下延续 §4(i) 判读路径的
#: 机制观察证据（6/6 bottom 派次、判据轴延续；含 2 个零旗标派次的
#: notes 内判正常路径）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "四边周边焊盘阵列上的绿色侧翼与环状缺口按 §4(i) 量化判据（≥3 处、沿同一阵列、跨多边分布、形态一致）判为正常设计特征，未报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "按 §4(i) 量化判据核验：同一形态作为最小重复单元在四条边上均大量出现（远超 3 处）、沿同一阵列成组对齐、各处形态尺寸与样式一致，判为系统性正常设计特征"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "绿色翼瓣间隙形态一致且成体系大量出现，按存在性判据(i)判为正常设计特征未报告"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "按 §4(i) 系统性正常特征判据判为 pin-1 类标记设计特征，不报告"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "带翼瓣焊盘的翼瓣/蝶形形态在四条边的阵列中系统性重复且形态一致（≥3处、跨多条边），按 §4(i) 判为正常设计特征未报告"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "阵列间散布的小型深绿色间隙/翼瓣图形沿四条边系统性重复出现（远超 3 处、沿同一阵列成组对齐、各处形态尺寸一致），按 §4(i) 量化判据判为正常设计特征"},
]

#: top 弃权理由构成分型（机制观察：22 条 top 弃权旗逐旗按
#: location_evidence 关键词分类——contact=接触性「真实接触 vs 视觉
#: 贴近不可分辨/是否接触不可确认」；existence=存在性「性质不明/是否
#: 存在不可确认」；other_layer=层归属等其他出口；为 top 弃权率上升
#: （M1 0.88 vs r16 基线 0.771429）归因分解。逐旗 excerpt 逐字
#: substring fail-closed 校验+覆盖完整性校验）。
TOP_ABSTAIN_TYPOLOGY = [
    {"source": "applied-top-i1", "flag_id": "R17T-001", "type": "existence",
     "excerpt": "无法逐字确认哪些文字确实无法辨读，故按存在性不确定弃权"},
    {"source": "applied-top-i1", "flag_id": "R17T-002", "type": "contact",
     "excerpt": "交叠与否无法负责任确认",
     "note": "接触性主出口（疑似交叠对象可能是 1 脚标记焊盘=存在性附记，按主出口计入 contact）"},
    {"source": "applied-top-i1", "flag_id": "R17T-003", "type": "existence",
     "excerpt": "无法负责任判定其为该类封装的常规安装孔/屏蔽柱图形还是异常图元"},
    {"source": "applied-top-i1", "flag_id": "R17T-004", "type": "existence",
     "excerpt": "当前清晰度下无法确认文字确被截断或压叠，故弃权"},
    {"source": "applied-top-i1", "flag_id": "R17T-005", "type": "contact",
     "excerpt": "真实接触与视觉贴近无法区分，按接触性判据弃权"},
    {"source": "prep1-top-i1", "flag_id": "R17T-001", "type": "existence",
     "excerpt": "当前判读下无法负责任确认其构成与归类，故弃权"},
    {"source": "prep1-top-i1", "flag_id": "R17T-002", "type": "existence",
     "excerpt": "当前分辨率下无法确认是否真实叠印，故弃权"},
    {"source": "prep1-top-i1", "flag_id": "R17T-003", "type": "existence",
     "excerpt": "无法确认是焊盘确实缺失还是走线覆压造成的视觉混淆，故弃权"},
    {"source": "applied-top-i2", "flag_id": "R17T-001", "type": "existence",
     "excerpt": "无法负责任判断这是正常的机械孔/非金属化孔渲染形态还是异常现象"},
    {"source": "applied-top-i2", "flag_id": "R17T-002", "type": "contact",
     "excerpt": "按接触性判据无法区分真实接触与视觉贴近，存在性不确定，故弃权"},
    {"source": "applied-top-i2", "flag_id": "R17T-003", "type": "existence",
     "excerpt": "无法负责任确认辨读是否实际受阻，故弃权"},
    {"source": "applied-top-i2", "flag_id": "R17T-004", "type": "existence",
     "excerpt": "形态孤立出现且无法确认其设计含义"},
    {"source": "applied-top-i2", "flag_id": "R17T-005", "type": "contact",
     "excerpt": "无法负责任确认是否构成不同封装占位轮廓间的重叠/接触，故弃权"},
    {"source": "prep1-top-i2", "flag_id": "R17T-001", "type": "contact",
     "excerpt": "当前分辨率下无法区分真实接触与视觉贴近，按接触性判据弃权"},
    {"source": "prep1-top-i2", "flag_id": "R17T-002", "type": "existence",
     "excerpt": "绕行是否确属多余无法负责任确认，故弃权"},
    {"source": "prep1-top-i2", "flag_id": "R17T-003", "type": "existence",
     "excerpt": "无法确认是真实叠印还是仅排布紧密，故弃权"},
    {"source": "applied-top-i3", "flag_id": "R17T-003", "type": "contact",
     "excerpt": "在当前呈现尺度下无法区分真实叠印与视觉贴近（按接触性判据存在性不确定）"},
    {"source": "applied-top-i3", "flag_id": "R17T-004", "type": "contact",
     "excerpt": "当前分辨率无法区分真实接触与视觉贴近，无法负责任确认文字叠印是否真实存在"},
    {"source": "applied-top-i3", "flag_id": "R17T-005", "type": "existence",
     "excerpt": "无法负责任确认该延伸差异是否真实"},
    {"source": "prep1-top-i3", "flag_id": "R17T-002", "type": "existence",
     "excerpt": "无法负责任确认是多个位号相互叠压连印，还是仅因图像缩小导致模糊"},
    {"source": "prep1-top-i3", "flag_id": "R17T-003", "type": "contact",
     "excerpt": "按接触性判据无法在当前渲染下区分真实接触/交叠与小于分辨率的视觉贴近"},
    {"source": "prep1-top-i3", "flag_id": "R17T-004", "type": "existence",
     "excerpt": "无法负责任确认文字是否被板框截断或仅为标注置于板缘"},
]

#: 绿色区域语义化方式证据（r17 机制观察延续：bottom 六派次 notes/
#: location_evidence 逐字摘录；substring fail-closed 校验；对照 r16
#: 六派次全部空隙语义化+6 派次 §5A 显式援引——r17 实测 6/6 派次仍以
#: 「空隙/翼瓣」语义化绿色（§4(i) 判读路径延续），但 §5A 显式援引
#: 降至 2/6（prep1-bottom-i2 notes+prep1-bottom-i3 旗 location_
#: evidence），如实分列）。
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "四边周边焊盘阵列上的绿色侧翼与环状缺口按 §4(i) 量化判据",
     "cites_5A": False},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "四边各有一组两排/两列的均匀交错圆形焊盘阵列",
     "second_excerpt": "绿色翼瓣状空隙及其在相邻图元间的局部汇并，按 §4(i) 量化判据核验",
     "cites_5A": False},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "阵列间与焊盘间的绿色翼瓣间隙形态一致且成体系大量出现，按存在性判据(i)判为正常设计特征未报告",
     "cites_5A": False},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "焊盘之间的绿色蝶形/翼瓣空隙成体系遍布全部阵列且样式一致，结合 §5A 仪器注记判为铺铜 clearance 空隙正常特征，不报告",
     "cites_5A": True},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "带翼瓣焊盘的翼瓣/蝶形形态在四条边的阵列中系统性重复且形态一致（≥3处、跨多条边）",
     "cites_5A": False},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "按 §5A 仪器注记绿色区域为基材露白而非 courtyard 图元",
     "kind": "location_evidence",
     "cites_5A": True},
]

#: 黑点族现象证据（r17 黑点族弃权旗 8 条全弃权+4 派次 notes 判正常未
#: 报告的代表摘录；kind=reading_notes 或 location_evidence；substring
#: fail-closed 校验；延续 r14–r16 黑点族追踪——r17 黑点族=8 旗（分型
#: 件 rubric 口径）vs r16=12，数量回落、方向性描述）。
BLACK_DOT_EVIDENCE = [
    {"source": "applied-top-i1", "kind": "location_evidence",
     "flag_id": "R17T-003", "instance": "top-i1", "disposition": "弃权",
     "excerpt": "右上连接器（J2）占位区内可见两个竖直对齐、尺寸一致的黑色实心圆点"},
    {"source": "applied-top-i2", "kind": "location_evidence",
     "flag_id": "R17T-001", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上连接器 footprint 内部见两个竖直对齐的实心黑色圆点"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R17B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "左上椭圆焊盘右下缘旁见一枚极小黑色实心圆点"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R17B-003", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "上缘旁同样见一枚极小黑色实心圆点"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R17B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "下方紧邻一枚孤立黑色实心圆点"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R17B-003", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "上方紧邻一枚孤立黑色实心圆点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R17B-003", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "见一黑色圆点、无可见铜环包覆"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R17B-004", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "见一与前处形态相同的黑色无环圆点"},
    {"source": "prep1-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "disposition": "判正常不报告",
     "excerpt": "右上角两枚同尺寸纵向对齐的黑色实心圆点（与安装孔常规形态一致）"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "disposition": "判正常不报告",
     "excerpt": "左上角两个小黑圆点两处形态一致、与焊盘轮廓均可见间隙，未见冲突"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i2", "disposition": "判正常不报告",
     "excerpt": "各带一相邻黑色小孔、两组互为 180° 旋转且形态彼此一致"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "disposition": "判正常不报告",
     "excerpt": "左上两组长圆形焊盘旁的两个裸钻孔圆点形态一致"},
]

#: 黑点族旗标登记表（8 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定——r17 两板各自
#: 从头编号；r17 黑点族旗全部落在 applied 板、bottom 三实例各 2 条；
#: 分型件 rubric 口径=r17 8 vs r16 12（axis-plan baselines_registered
#: 在案 M3 基线））。
BLACK_DOT_FLAGS = [
    ("top-i1", "applied", "R17T-003", "other_advisory"),
    ("top-i2", "applied", "R17T-001", "other_advisory"),
    ("bottom-i1", "applied", "R17B-002", "other_advisory"),
    ("bottom-i1", "applied", "R17B-003", "other_advisory"),
    ("bottom-i2", "applied", "R17B-002", "other_advisory"),
    ("bottom-i2", "applied", "R17B-003", "other_advisory"),
    ("bottom-i3", "applied", "R17B-003", "other_advisory"),
    ("bottom-i3", "applied", "R17B-004", "other_advisory"),
]

#: 呈现尺寸机制观察证据（本轮关键机制观察；12 派次 reading_notes 关于
#: 图像呈现尺寸/清晰度/分辨率的自述逐件逐字摘录；substring fail-closed
#: 校验；has_px_size=自述含绝对像素尺寸、stated_px=自述值；对照仪器
#: 实测 PNG image_wh=4009×4009（top）/4010×4009（bottom）（witness-r17
#: renders 登记值，脚本 live 装载）——呈现端缩放读者可见性自述与
#: reject 支内嵌「视觉编码器尺寸上限抵消增益」解释的对照，如实单列、
#: 不凌驾字母裁决）。
PRESENTATION_SIZE_EVIDENCE = [
    {"source": "applied-top-i1", "instance": "top-i1",
     "has_px_size": False, "stated_px": None,
     "excerpt": "图像整体分辨率高，多数独立丝印文字可辨",
     "second_excerpt": "局部密集簇内极小号文字与线线贴近处的判定受当前可见清晰度限制"},
    {"source": "prep1-top-i1", "instance": "top-i1",
     "has_px_size": False, "stated_px": None,
     "excerpt": "图像整体结构（边缘排针、两处 QFP、courtyard 轮廓间距、标签簇、45 度走线形态）清晰可判",
     "second_excerpt": "小号丝印文字与密集焊盘细节在当前判读分辨率下处于可辨边缘，影响上述三处的确认"},
    {"source": "applied-top-i2", "instance": "top-i2",
     "has_px_size": True, "stated_px": "约 1000px 宽",
     "excerpt": "图像以约 1000px 宽度呈现，丝印文字高度仅数像素，多数位号勉强可辨，限制了对丝印可读性与细小间隙的判定能力"},
    {"source": "prep1-top-i2", "instance": "top-i2",
     "has_px_size": False, "stated_px": None,
     "excerpt": "图像整体分辨率下板级结构可辨",
     "second_excerpt": "细部（极小位号文字、courtyard 边缘贴合、单段走线弯折的必要性）接近可判上限，细部确认受限"},
    {"source": "applied-top-i3", "instance": "top-i3",
     "has_px_size": True, "stated_px": "约 1000×1000",
     "excerpt": "呈现尺寸约 1000×1000，位号文字处于可辨读边缘"},
    {"source": "prep1-top-i3", "instance": "top-i3",
     "has_px_size": True, "stated_px": "约 1000px 宽",
     "excerpt": "图像以约 1000px 宽度呈现，多数中号位号（SW2/LED2/Y1/R12/USB1/F1/R2/C27 等）可辨读，最小号位号簇仅可辨轮廓"},
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "has_px_size": False, "stated_px": None, "mentions_dpi": True,
     "excerpt": "1280dpi 图像整体清晰，周边焊盘行间距均匀、无可见缺焊盘或间距规律破坏",
     "second_excerpt": "小尺寸细节（黑色小圆点、左上椭圆焊盘中部浅色截断带）在本分辨率下可分辨"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "has_px_size": False, "stated_px": None,
     "excerpt": "图像清晰度良好：相邻图元轮廓间的细小间隙在该分辨率下可分辨，支持上述接触性/近邻判断"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "has_px_size": False, "stated_px": None,
     "excerpt": "图像整体清晰度良好，唯小尺寸图形（黑色圆点、封装间间隙）的判读受读图坐标估计精度限制"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "has_px_size": False, "stated_px": None, "mentions_dpi": True,
     "excerpt": "1280dpi 渲染下焊盘级图元清晰可辨，支持上述对系统性特征的正常性判断"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "has_px_size": False, "stated_px": "单个焊盘约占图宽 2%（相对自述）",
     "excerpt": "呈现尺寸下单个焊盘约占图宽 2%，焊盘与翼瓣形态清晰可辨，但行内相邻焊盘间距的细微差异不足以支持可靠的不一致判定"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "has_px_size": True, "stated_px": "约 1500px", "mentions_dpi": True,
     "excerpt": "1280dpi 渲染，焊盘、轮廓与间隙图形均清晰可辨，全图以约 1500px 呈现",
     "second_excerpt": "唯 R17B-001 处两图形间最窄间隙接近呈现分辨率极限，影响接触性判断"},
]

#: 1280 下新可见细节引发的新旗（top 新现象机制观察；逐旗逐字摘录；
#: substring fail-closed 校验；对照 r16 同位现象未见此类旗在案——
#: 属方向性对照、非配对）：半填充圆形/双色半分圆、QFP 焊盘条疑似
#: 间断、引脚排延伸差异（top 弃权旗 4 条）+椭圆焊盘截断带（bottom
#: 非弃权报告旗 1 条=1280 新细节引发的首条 bottom 非弃权 other_
#: advisory 报告）；另有 2 派次 notes 把同族半填充圆形判正常未报告。
NEW_DETAIL_EVIDENCE = [
    {"source": "applied-top-i2", "flag_id": "R17T-004", "instance": "top-i2",
     "view": "top", "disposition": "弃权", "phenomenon": "半填充圆形（右半实心半圆填充大圆轮廓）",
     "excerpt": "大的黄色圆轮廓、右半为淡黄色实心半圆填充，内含两个小焊盘"},
    {"source": "prep1-top-i1", "flag_id": "R17T-001", "instance": "top-i1",
     "view": "top", "disposition": "弃权", "phenomenon": "双色半分圆形（左浅黄/右浅粉竖直分界）",
     "excerpt": "左半呈浅黄、右半呈浅粉、分界为竖直线"},
    {"source": "prep1-top-i1", "flag_id": "R17T-003", "instance": "top-i1",
     "view": "top", "disposition": "弃权", "phenomenon": "QFP 底边焊盘条疑似间断（2-3 个焊盘位）",
     "excerpt": "疑似出现约 2-3 个焊盘位的间断"},
    {"source": "applied-top-i3", "flag_id": "R17T-005", "instance": "top-i3",
     "view": "top", "disposition": "弃权", "phenomenon": "IC 顶/底引脚排左端延伸差异",
     "excerpt": "中央大 IC 底部引脚排的左端似比其顶部引脚排更向左延伸"},
    {"source": "applied-bottom-i1", "flag_id": "R17B-001", "instance": "bottom-i1",
     "view": "bottom", "disposition": "非弃权报告", "phenomenon": "椭圆焊盘中段浅色竖向截断带（橙填充分两瓣）",
     "excerpt": "其中段被一条浅色竖向带明显截断（橙色填充分为两瓣）"},
    {"source": "applied-top-i1", "kind": "reading_notes", "flag_id": None,
     "instance": "top-i1", "view": "top", "disposition": "判正常不报告",
     "phenomenon": "带黄色填充半圆的大圆形封装图形",
     "excerpt": "左下方带黄色填充半圆的大圆形封装图形（判读为电池/极性标记类常见封装丝印形态）"},
    {"source": "prep1-top-i3", "kind": "reading_notes", "flag_id": None,
     "instance": "top-i3", "view": "top", "disposition": "判正常不报告",
     "phenomenon": "左下大圆的半幅黄色填充",
     "excerpt": "左下大圆的半幅黄色填充"},
]

#: placement/孤立图形类旗标处置证据（逐字摘录；substring fail-closed
#: 校验）——r17 板内孤立焊盘组跨实例/跨板处置分化延续（bottom-i1
#: 弃权/bottom-i2 与 bottom-i3 非弃权报告/两 prep1 派次 notes 判正常
#: 不报告），如实单列。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R17B-004", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "板内孤立焊盘组（带弧形绿色缺口的小圆盘+方焊盘）",
     "excerpt": "全图其余内部区域无同类图形可比较，仅凭图像无法确定其为正常设计特征还是异常形态"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R17B-001", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（同位现象、跨实例出口不同）",
     "excerpt": "与全板其余焊盘一律沿四边成整齐阵列排布的规整模式明显偏离"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R17B-001", "instance": "bottom-i3", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "远离四边成排焊盘阵列，打破整板焊盘沿板缘成排排布的规整放置模式"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内偏右下有一组孤立的两焊盘图元（圆焊盘+方形焊盘）"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i2", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘组（同位现象）",
     "excerpt": "板内右中孤立的一对焊盘（圆形带绿色翼瓣 + 方形）"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed）。
REROUTE_ADJUDICATION = [
    {"source": "prep1-top-i2", "flag_id": "R17T-002", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("中央大封装footprint左上内侧可见一段走线呈"
                           "下行-回折-再下行的弯折形态，与周边直线扇出"
                           "对角线不一致"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「绕行是否确属多余无法负责任"
              "确认」=可疑改道是否存在无法负责任确认，按 §4 弃权")},
]

#: reroute 类旗标产量链基线（r8–r16 在案；本轮 r17 实测=1；
#: r16=2 经 run-r16 reader.flag_count 在案字段 live 核对）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4, "r16": 2}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1, "r16": 0}


def _fail(msg: str) -> None:
    print(f"[s64-cal-r17] FAIL: {msg}")
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
    # 本轮派次层 2 格零旗标（prep1-bottom-i1/i2）：有旗格 view_check
    # 必须 full、零旗格 view_check=not_applicable（库侧口径）。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    # 渲染 provenance 按视角分列：本轮渲染=轴1 唯一仪器变量（renders-
    # r17 四图全新渲染 1280dpi、r14b 配色规则重放；framing-r17
    # single_variable_change 预注册在案、witness-r17 成图见证实测在
    # 案）。top=无配色（与既往一致）；bottom=r14b 配色语义 1280dpi
    # 重放。两视角共同声明=四图全部唯一变量为 dpi。
    if "-top-" in raw_key:
        framing_rel = REL_FRAMING_R17
        framing_note = (
            "top 渲染=轴1 仪器变更轮内同一单变量应用：renders-r17/"
            "applied-top.png（4009×4009，b35315ef）与 prep1-top.png"
            "（4009×4009，bdce8bbb）均为 1280dpi 原生重渲染、top 无配色"
            "（与既往轮次一致，§5A 保留句在案）；framing-r17=a1084c14 "
            "single_variable_change 预注册在案；非字节复用")
    else:
        framing_rel = REL_FRAMING_R17
        framing_note = (
            "bottom 渲染=轴1 仪器变更：renders-r17 四图 1280dpi 全新"
            "渲染、r14b 配色规则逐字重放（白墨图元→橙 (255,165,0)、"
            "板内空隙白→绿 (0,128,0)；mask 于 1280 像密度重算、z 序/"
            "混合数学不变）；两板 bottom 成图逐字节同（0c2d5c00）；"
            "成图实测橙 326460 px/绿 903366 px/板内白 0（witness-r17 "
            "palette_assertion_summary，脚本 live 装载核对；640dpi 期值"
            "为 81672/206632，px 数已随仪器描述性同步入 r17 指引 §5A、"
            "非判据）；framing-r17=a1084c14 预注册件在案")
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
                     " frame_box_pct_r5（R5 仪器像素界重投影口径；r17 "
                     "渲染=同一板 Edge.Cuts 几何+同 40pt 组合页仅 dpi "
                     "640→1280，重投影沿用 r14 顶层更换先例不重派生、"
                     "本轮零新派生）；board_box_mm/side 等其余字段与 GT "
                     "文件逐字段原样；13 条全部 side=top"),
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
                "r17 实测 flag_id 两板各自从头编号（跨板同号如实登记；"
                "与 prep-record naming「同实例跨板连续」声明不同=读者"
                "实例输出行为差异、如实入账不作废，与 r15/r16 实测同"
                "形态）——abstain_ids/"
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
                 "三分判据（supported ≤0.671429 / marginal 带内 / "
                 "reject ≥0.771429）"
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
                       "r15": "not_met（在案）", "r16": "not_met（在案）",
                       "r17": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
                              run_r16: dict, inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R16；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R15/R16 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r15_replays = replay_round_instances(run_r15)
    r16_replays = replay_round_instances(run_r16)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R17 {key} 通道重放与 compare_v3 对拍不一致")

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
    # r15/r16=fresh 重放并与在案登记逐一交叉核对，r17=本轮 fresh 重放）
    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", r16_replays, None)
    geo_r17 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", r16_replays, None)
    cat_r17 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", r16_replays, None)
    view_r17 = pick("view_gate", inst_replays, inst_blocks)
    # 与在案 run 登记交叉核对（fail-closed：重放结果须与在案一致）
    if geo_r15 != run_r15["channel_attribution"]["channel_1_geometry_gate"][
            "r15_area_ratio_rejected_entries"]:
        _fail("R15 几何门重放与 run-r15 在案登记不一致")
    if cat_r15 != run_r15["channel_attribution"]["channel_2_category_gate"][
            "r15_category_mismatch_entries"]:
        _fail("R15 类别门重放与 run-r15 在案登记不一致")
    if view_r15 != run_r15["channel_attribution"][
            "view_gate_observations"]["r15_entries"]:
        _fail("R15 视角门重放与 run-r15 在案登记不一致")
    if geo_r16 != run_r16["channel_attribution"]["channel_1_geometry_gate"][
            "r16_area_ratio_rejected_entries"]:
        _fail("R16 几何门重放与 run-r16 在案登记不一致")
    if cat_r16 != run_r16["channel_attribution"]["channel_2_category_gate"][
            "r16_category_mismatch_entries"]:
        _fail("R16 类别门重放与 run-r16 在案登记不一致")
    if view_r16 != run_r16["channel_attribution"][
            "view_gate_observations"]["r16_entries"]:
        _fail("R16 视角门重放与 run-r16 在案登记不一致")

    geo_change = (
        "几何门通道（R16→R17）：面积比出局条目 %d→%d（渲染分辨率倍增下"
        "top 非弃权旗与同态 GT ≥0.5 containment 交叠条目的几何门计数"
        "如实登记；本轮 top 非弃权旗 3 条、几何门=%d 条；跨轮实例群漂移"
        "混杂照旧声明，只描述不断言。"
        % (len(geo_r16), len(geo_r17), len(geo_r17)))
    cat_change = (
        "类别门通道（R16→R17）：类别不符出局条目 %d→%d（r16 在案 1 条="
        "prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3（containment "
        "0.848147、面积比 1.529072），r17 重放=%d 条；r11 唯一原发条目 "
        "R11T-012↔GT-REVC-AP-8-R1Q2 语境下逐轮计数如实登记；跨轮实例群"
        "漂移混杂照旧声明，只描述不断言。"
        % (len(cat_r16), len(cat_r17), len(cat_r17)))

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
            "r14": len(run_r15["channel_attribution"][
                "channel_1_geometry_gate"]["r14_area_ratio_rejected_entries"]),
            "r15": len(geo_r15),
            "r16": len(geo_r16),
            "r17": len(geo_r17),
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
            "r14": len(run_r15["channel_attribution"][
                "channel_2_category_gate"]["r14_category_mismatch_entries"]),
            "r15": len(cat_r15),
            "r16": len(cat_r16),
            "r17": len(cat_r17),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=0→r17=%d（r14 回升未延续、r15–r17 "
                 "维持低位：top 非弃权旗与同态 GT ≥0.5 containment 交叠"
                 "条目如实计数；本轮 3 条 top 非弃权旗全部 containment"
                 " 无交叠或 <0.5）；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→"
                 "r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17=%d（r11 唯一"
                 "条目 R11T-012↔AP-8 无再现；r16 1 条=r16 在案、r17 零"
                 "条目）"
                 % (len(geo_r17), len(cat_r17))),
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
            "ref": {"path_rel": REL_PREP_R17, "sha256": _sha(REL_PREP_R17)},
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
            "source_of_r15_r16_detail": (
                "calibration-run-r15.json / calibration-run-r16.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/s55/s58 "
                "deviation_note 口径：本轮对 R15/R16/R17 均以内嵌输入+"
                "compare_v3 同源几何原语（calibration._containment/_"
                "area_ratio、CONTAINMENT_MIN=0.5、AREA_RATIO_MAX=10.0 "
                "声明常量）对每非弃权旗标×同态 GT 确定性重放通道分类："
                "containment<0.5（含 None=无交集）无条目；近邻且视角不符"
                "=view_gate；近邻且面积比>上限=area_ratio_rejected（几何"
                "门）；近邻且面积比≤上限且类别不符=category_mismatch（"
                "类别门）；类别相符且双条件过=candidate。"),
            "replay_cross_check": {
                "r15_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r15_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r16_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r16_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r17_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R15/R16 十二件复算"
                         "与在案 run 登记一致：R15 候选对=空集、R16 候选"
                         "对={R16T-001×GT-REVC-AP-6-R2LED2}；R17 十二件"
                         "重放全部复现=空集，见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R15T/R15B、R16T/R16B 与 R17T/"
            "R17B 来自不同 reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素；r17 两板各自从头编号"
            "亦属实例输出行为差异、如实登记）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "r17_area_ratio_rejected_entries": geo_r17,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r15_category_mismatch_entries": cat_r15,
            "r16_category_mismatch_entries": cat_r16,
            "r17_category_mismatch_entries": cat_r17,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r15_entries": view_r15,
            "r16_entries": view_r16,
            "r17_entries": view_r17,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r17 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；r15/r16 重放亦零视角门条目（在案延续）。"
                     % len(view_r17)),
        },
        "gate_chain_since_r6": chain,
        "r17_specific_observations": [
            "R17 六实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条；GT 条目层 union/agreement 与"
            "代表配置口径见 gt_match_dual/aggregation_representative"
            "（如实分列）；bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
            "side=top，bottom GT 无源在案 gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R17 courtyard 类旗标 %d 条（top %d+bottom %d）：top 非弃权 "
            "courtyard 1 条（applied-top-i3 R17T-001，SW2 占位框与连接器"
            "排轮廓贴邻近邻形态、containment 无 ≥0.5 交叠=零命中）、"
            "弃权 6 条；bottom courtyard 1 条（prep1-bottom-i3 R17B-001 "
            "弃权）——G1 守门（bottom 非弃权 courtyard 0/0/0）维持；"
            "top 弃权构成分型=接触性 8+存在性 14+层归属其他 0"
            "（hypothesis_test.mechanism_observation."
            "top_abstain_typology 逐旗摘录在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R17 几何门 %d 条（r16=0 延续与否如实计数）；类别门 %d 条"
            "（r16=1 后的本轮计数如实登记）；视角门条目数"
            "见 view_gate_observations（如实单列）。"
            % (len(geo_r17), len(cat_r17)),
            "R17 suspicious_reroute 旗标 1 条（弃权、存在性出口：R17T-002 "
            "prep1-top-i2，(state, flag_id) 限定）；产量链 r8=1→r9=0→"
            "r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→r17=1；「等长|"
            "蛇形」子串零命中——r17 滥用型通道被动追踪=0（见 "
            "hypothesis_test.reroute_continuation_r17，非本轮判据输入）。",
            "courtyard 被动追踪（r11–r16 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r17 "
            "courtyard_tracking 节）。",
        ],
    }


def _prep_doc() -> dict:
    """r17-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R17)


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
    """bottom 侧 G1 守门实测（操作化定义：bottom 三实例 courtyard 类非
    弃权旗数；per r17-prep-record guard_channel「G1=bottom courtyard
    非弃权 0/0/0 维持（对照 r15/r16 在案 0/0/0）」原文；守门独立单列、
    不影响字母。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r17 两板各自从头编号、明细行已按 (state, flag_id) 限定）；
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


def r16_baseline_courtyard_live(run_r16: dict) -> dict:
    """r16 基线重放实测（G1 守门对照「r16 的 0/0/0」；run-r16 内嵌输入；
    与 R16_BOTTOM_COURTYARD_BASELINE 登记交叉核对）。"""
    out = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            blk = run_r16["instances"][name]["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in blk["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        out[name] = cnt
    if out != R16_BOTTOM_COURTYARD_BASELINE:
        _fail(f"r16 bottom courtyard 基线与 run-r16 实测不符: {out}")
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


def r16_top_abstain_aggregate_live(run_r16: dict) -> tuple:
    """r16 top 全旗聚合弃权重放实测（M1 基线=0.771429；同一聚合逻辑对
    run-r16 内嵌实例记录双侧复算、不手工抄数；与 BASE16_TOP_AGGREGATE_
    REGISTERED=(27,35) 交叉核对）。"""
    ab, fl = _view_aggregate_abstain_live(
        run_r16, ("top-i1", "top-i2", "top-i3"))
    if {"abstain": ab, "flags": fl} != BASE16_TOP_AGGREGATE_REGISTERED:
        _fail("r16 top 全旗聚合弃权基线与 run-r16 实测不符（应为 27/35）")
    return ab, fl


def r16_bottom_abstain_aggregate_live(run_r16: dict) -> tuple:
    """r16 bottom 全旗聚合弃权重放实测（M2 基线；对照 12/14=0.857143）。"""
    ab, fl = _view_aggregate_abstain_live(
        run_r16, ("bottom-i1", "bottom-i2", "bottom-i3"))
    if {"abstain": ab, "flags": fl} != BASE16_BOTTOM_AGGREGATE_REGISTERED:
        _fail("r16 bottom 全旗聚合弃权基线与 run-r16 实测不符（应为 "
              "12/14）")
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
                          run_r14: dict, run_r15: dict, run_r16: dict,
                          axis_plan: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（axis-plan-r17-resolution-double，轴1 渲染分辨率倍增）裁决节
    （预注册三分判据执行；字母裁决唯一正式+守门 G1/G2 独立单列+机制
    观察单列）。

    字母裁决（唯一正式裁决）=判据 r17-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：M1（top 全旗聚合弃权率，12 派次全口径）三分判据——
    (a) M1 ≤0.671429（=r16 零变更基线 0.771429 绝对降幅 ≥0.10 的计划件
    显著收益阈值，live 重放交叉核对 (27,35) 一致）→ supported（分辨率
    瓶颈实锤，轴1 supported）；
    (b) M1 ≥0.771429（=r16 零变更基线水平，live 重放交叉核对一致）→
    reject（轴1 证伪：分辨率非瓶颈（或视觉编码器尺寸上限抵消增益，
    机制观察须记录读者实际可见细节的自述）；转向轴2/轴3）；
    (c) 0.671429<M1<0.771429（带内小幅改善，未过显著收益阈值=与跨轮
    漂移噪声不可分）→ marginal（轴1 不判定为胜出）。
    判据比较用 6 位定点整数交叉相乘（×10^6，避免浮点；阈值=冻结件
    6 位小数原文）；(a)/(b) 两支互斥（同时成立即自洽性破坏、中止）；
    守门 G1（bottom courtyard 非弃权 0/0/0 维持）与 G2（guard_ok=True
    维持）独立单列——任一破坏→轴1 按 axis-plan early_stop_rule 出局
    （字母照实+出局声明）；机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R17)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（axis-plan/framing-r17/witness-r17/dev-r16/
    # run-r16 锚已在 FROZEN_SHA256 校验；prep-record chain_anchors 内嵌
    # 登记值与盘上实测逐一核对，fail-closed）
    anchors = prep_doc["guidance_reuse"]["chain_anchors"]
    if anchors["axis_experiment_plan_frozen"]["path_rel"] != REL_AXIS_PLAN \
            or anchors["axis_experiment_plan_frozen"]["sha256"] \
            != _sha(REL_AXIS_PLAN):
        _fail("prep-record 链锚（axis-plan）与盘上实测不符")
    dev16_anchor = anchors["round16_dev_record_chain"]
    if dev16_anchor["path_rel"] != REL_DEV_R16 \
            or dev16_anchor["sha256_measured"] != _sha(REL_DEV_R16) \
            or dev16_anchor["r16_prep_record_registered_sha256"] \
            != _sha(REL_PREP_R16):
        _fail("prep-record 链锚（round16-dev-record）与盘上实测不符")
    run16_anchor = anchors["run_r16_baseline_anchor"]
    if run16_anchor["path_rel"] != REL_RUN_R16 \
            or run16_anchor["sha256_measured"] != _sha(REL_RUN_R16):
        _fail("prep-record 链锚（run-r16 基线）与盘上实测不符")
    if "27/35" not in run16_anchor["frozen_values"] \
            or "0.771429" not in run16_anchor["frozen_values"] \
            or "guard_ok=True" not in run16_anchor["frozen_values"]:
        _fail("prep-record run-r16 基线冻结值文本与预期不符")
    if anchors["render_framing_r17_single_variable_declaration"][
            "sha256"] != _sha(REL_FRAMING_R17) \
            or anchors["render_witness_r17_px_source"]["sha256"] \
            != _sha(REL_WITNESS_R17):
        _fail("prep-record 链锚（framing/witness-r17）与盘上实测不符")
    gr = prep_doc["guidance_reuse"]
    if gr["derived_path_rel"] != REL_GUIDANCE_R17 \
            or gr["derived_sha256"] != _sha(REL_GUIDANCE_R17) \
            or gr["base_path_rel"] != REL_GUIDANCE_R15 \
            or gr["base_sha256"] != _sha(REL_GUIDANCE_R15):
        _fail("prep-record guidance_reuse 指引锚与盘上实测不符")
    if prep_doc["round_id_constant"] != ROUND_ID \
            or prep_doc["round_label"] != ROUND_LABEL \
            or prep_doc["declared_date"] != DECLARED_DATE \
            or prep_doc["instrument_change"]["changed"] is not True:
        _fail("prep-record 轮次标识/instrument_change.changed 与预期不符")
    # 四 PNG sha 三方核对（FROZEN 锚=witness-r17 登记=prep-record 登记）
    witness_doc = _json_load(REL_WITNESS_R17)
    witness_key = {"applied-top": "applied-top",
                   "applied-bottom": "applied",
                   "prep1-top": "prep1-top",
                   "prep1-bottom": "prep1"}
    for side, rel in PNG_FILES.items():
        got = _sha(rel)
        if got != witness_doc["renders"][witness_key[side]]["sha256"]:
            _fail(f"PNG sha 与 witness-r17 登记值不符: {side}")
    for entry in prep_doc["instrument_change"]["renders"]:
        part = entry["state_side"]
        if PNG_FILES[part] != entry["path_rel"] \
                or entry["sha256_measured"] != _sha(PNG_FILES[part]) \
                or entry["sha256_witness_registered"] \
                != entry["sha256_measured"] or entry["match"] is not True:
            _fail(f"prep-record instrument_change.renders 与实测不符: "
                  f"{part}")
    # axis-plan 基线登记值 fail-closed 装载核对（非手抄）
    rb = axis_plan["baselines_registered"]["r16_baseline"]
    if rb["round_id"] != "r16" \
            or rb["M1_top_aggregate_abstain_rate"] != 0.771429 \
            or rb["M2_bottom_aggregate_abstain_rate"] != 0.857143 \
            or rb["M3_blackdot_abstain_flags_rubric"] \
            != AXIS_R16_M3_BLACKDOT_RUBRIC \
            or rb["M4_top_per_instance_rate_range"] != AXIS_R16_M4_TOP_RANGE:
        _fail("axis-plan r16 基线登记值与预期不符")
    if "0.09064" not in axis_plan["baselines_registered"][
            "drift_reference_note"]:
        _fail("axis-plan 漂移参照值与预期不符")
    if "≥0.10" not in axis_plan["comparison_rule"][
            "significant_benefit_definition"]:
        _fail("axis-plan 显著收益定义与预期不符")
    for gkey in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok"):
        if gkey not in axis_plan["guards"]:
            _fail(f"axis-plan 守门定义缺失: {gkey}")
    if ht["hypothesis_id"] != "axis-plan-r17-resolution-double":
        _fail("prep-record hypothesis_id 与预期不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "0.671429" not in adj["supported"] \
            or "0.771429" not in adj["supported"]:
        _fail("prep-record supported 判据文本与预期不符")
    if "0.771429" not in adj["reject"] or "轴1 证伪" not in adj["reject"]:
        _fail("prep-record reject 判据文本与预期不符")
    if "0.671429 < M1 < 0.771429" not in adj["marginal"]:
        _fail("prep-record marginal 判据文本与预期不符")
    if "G1" not in adj["guards"] or "0/0/0" not in adj["guards"] \
            or "G2" not in adj["guards"]:
        _fail("prep-record guards 文本与预期不符")
    # supported 阈值派生交叉核对：0.771429−0.10=0.671429（6 位定点）
    if REJECT_THRESHOLD_6DP - 100000 != SUPPORTED_THRESHOLD_6DP:
        _fail("supported 阈值派生（reject−0.10）与冻结常数不符")
    # 基线数字 live 重放与在案登记交叉核对（fail-closed；不手工抄数）
    base16_ab, base16_fl = r16_top_abstain_aggregate_live(run_r16)
    if cal._ratio(base16_ab, base16_fl) != 0.771429:
        _fail("run-r16 top 基线重放率与冻结值 0.771429 不符")
    # M2 基线与 G1 基线（bottom 12/14=0.857143 与 0/0/0；live 重放核对）
    base16_bot_ab, base16_bot_fl = r16_bottom_abstain_aggregate_live(run_r16)
    r16_courtyard_base = r16_baseline_courtyard_live(run_r16)
    # M4 逐实例构成 live 核对（top 三实例弃权率先 6 位取率再取极差）
    r16_top_rates = {n: run_r16["instances"][n]["combined"]["abstain_rate"]
                     for n in ("top-i1", "top-i2", "top-i3")}
    if r16_top_rates != R16_TOP_INSTANCE_RATES_REGISTERED \
            or cal._round6(max(r16_top_rates.values())
                           - min(r16_top_rates.values())) \
            != AXIS_R16_M4_TOP_RANGE:
        _fail("r16 top 逐实例弃权率构成与 axis-plan 登记不符")
    # reroute 产量链基线交叉核对（r8–r16 在案）
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
            or run_r16["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r16"]:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（M1=top 全旗聚合弃权率，12 派次全口径；三分判据逐支）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    # (a) supported：M1 ≤0.671429（6 位定点整数交叉相乘避免浮点）
    crit_a_ok = abst_top * 1000000 <= SUPPORTED_THRESHOLD_6DP * flags_top
    # (b) reject：M1 ≥0.771429（6 位定点整数交叉相乘避免浮点）
    crit_b_ok = abst_top * 1000000 >= REJECT_THRESHOLD_6DP * flags_top
    if crit_a_ok and crit_b_ok:
        _fail("主通道判定自洽性破坏（(a) 与 (b) 两支互斥）")
    # 守门 G1（bottom courtyard 非弃权 0/0/0 维持）——独立单列
    by_instance = bottom_courtyard_non_abstain(instances)
    bot_courtyard_flags = sum(
        1 for n in ("bottom-i1", "bottom-i2", "bottom-i3")
        for d in instances[n]["per_flag_gt_detail"]
        if d["category"] == "courtyard_crowding")
    g1_ok = all(v == 0 for v in by_instance.values())
    abst_bot, flags_bot = round_view_aggregate(
        instances, ("bottom-i1", "bottom-i2", "bottom-i3"))
    bot_rate = cal._ratio(abst_bot, flags_bot)
    bot_below_r16 = abst_bot * base16_bot_fl < \
        base16_bot_ab * flags_bot
    # 守门 G2（guard_ok=True 维持；top 视非弃权旗标几何门面积比出局
    # 条目不升）——独立单列（axis-plan guards.G2_guard_ok 原文）
    geo_r17 = attribution["channel_1_geometry_gate"][
        "r17_area_ratio_rejected_entries"]
    geo_r16 = attribution["channel_1_geometry_gate"][
        "r16_area_ratio_rejected_entries"]
    guard_ok = len(geo_r17) <= len(geo_r16)
    g2_ok = guard_ok is True
    guards_ok = bool(g1_ok and g2_ok)
    axis_out = not guards_ok
    # 字母裁决（三分判据，per r17-prep-record adjudication 原文）
    if crit_a_ok:
        verdict = "supported"
        letter_branch = ("(a) M1 ≤0.671429（相对 r16 零变更基线 0.771429 "
                         "绝对降幅 ≥0.10=计划件显著收益阈值）——分辨率"
                         "瓶颈实锤（轴1 supported）")
    elif crit_b_ok:
        verdict = "reject"
        letter_branch = ("(b) M1 ≥0.771429（不优于零变更基线）——轴1 "
                         "证伪：分辨率非瓶颈（或视觉编码器尺寸上限抵消"
                         "增益，机制观察须记录读者实际可见细节的自述）；"
                         "转向轴2/轴3")
    else:
        verdict = "marginal"
        letter_branch = ("(c) 0.671429 < M1 < 0.771429——带内小幅改善，"
                         "未过显著收益阈值（与跨轮漂移噪声不可分）；轴1 "
                         "不判定为胜出")
    verdict_text = (
        "按预注册判据（r17-prep-record.json hypothesis_test.adjudication "
        "原文，三分判据）=%s（字母口径，唯一正式裁决）：落支=%s。实测："
        "M1（top 全旗聚合弃权率，12 派次全口径）=%d/%d=%s；(a) 支阈值 "
        "0.671429（=r16 零变更基线 0.771429 绝对降幅 ≥0.10 的计划件"
        "显著收益阈值；r16 基线=同一聚合逻辑对 calibration-run-r16.json "
        "内嵌实例记录双侧复算=%d/%d=%s，与在案登记 27/35 及 axis-plan "
        "r16_baseline.M1 交叉核对一致，不手工抄数）；(b) 支阈值 0.771429"
        "（=r16 零变更基线水平，双侧复算交叉核对一致）；6 位定点整数"
        "交叉相乘比较（避免浮点）：(a) 支 %d×10^6 vs %d×%d → %s；"
        "(b) 支 %d×10^6 vs %d×%d → %s。轴1 仪器轮（渲染分辨率 640→"
        "1280dpi 单变量、四图全部）下唯一实验变量=分辨率；字母裁决只"
        "回答「分辨率倍增是否显著降低 top 弃权」的计划件判据命中方向；"
        "三项判据文本分开如实记录、不合并；本轮判据均为描述性边界、"
        "非 APR-0011 门（门照常独立计算，互不凌驾、run-record 内分开"
        "表述）。守门 G1（bottom courtyard 非弃权 0/0/0 维持）=%s、"
        "G2（guard_ok=True 维持，top 几何门面积比出局条目 R16=%d→"
        "R17=%d）=%s——均独立单列，%s（per axis-plan early_stop_rule"
        "%s）。注意：跨轮实例群漂移混杂照旧声明（r15→r16 纯重抽漂移 "
        "0.09064 在案参照）；单轮 n=3、development 域只描述不断言；"
        "机制观察单列（呈现尺寸自述/M2 bottom/M3 黑点族/top 新现象/"
        "courtyard 计数），不凌驾、不改写字母裁决。"
        % (verdict, letter_branch,
           abst_top, flags_top, top_rate,
           base16_ab, base16_fl, cal._ratio(base16_ab, base16_fl),
           abst_top, SUPPORTED_THRESHOLD_6DP, flags_top,
           "≤ 成立" if crit_a_ok else "> 不成立",
           abst_top, REJECT_THRESHOLD_6DP, flags_top,
           "≥ 成立" if crit_b_ok else "< 不成立",
           "维持（0/0/0）" if g1_ok else "破坏",
           len(geo_r16), len(geo_r17),
           "维持（True）" if g2_ok else "破坏",
           "守门均维持、不触发出局" if guards_ok
           else "守门破坏→轴1 按 plan early_stop_rule 出局（字母照实+"
                "出局声明）",
           "：guard_failure_exit=任一轮 G1/G2 破坏→该轴出局并如实记录"
           "（该轮 run/dev-record 照常落盘、字母裁决照常；「出局」仅指"
           "退出本实验后续组合与排序）" if axis_out else ""))
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 量化判据应用
    # + top 弃权分型逐旗 + 黑点族 + placement 处置 + 绿区语义化
    # + 呈现尺寸自述逐件 + 1280 新细节新旗）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in QUANT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in PRESENTATION_SIZE_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"呈现尺寸自述摘录与 reader 原文不符: {ev['source']}")
        if "second_excerpt" in ev and \
                ev["second_excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"呈现尺寸自述第二摘录与 reader 原文不符: {ev['source']}")
    # top 弃权理由构成分型（机制观察）：覆盖完整性 fail-closed——
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
        src_text = (raw_texts[ev["source"]]
                    if ev.get("kind") == "location_evidence"
                    else parsed_notes[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"绿区语义化摘录与 reader 原文不符: {ev['source']}")
        if "second_excerpt" in ev and \
                ev["second_excerpt"] not in src_text:
            _fail(f"绿区语义化第二摘录与 reader 原文不符: {ev['source']}")
    for ev in BLACK_DOT_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"黑点族证据摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in NEW_DETAIL_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev.get("kind") == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"1280 新细节摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in PLACEMENT_DISPOSITION_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"placement 处置摘录与 reader 原文不符: {ev.get('flag_id')}")
    # 黑点族旗标登记校验（8 条全部存在、abstain=True、category=登记值）
    black_rows = []
    for inst, st, fid, cat in BLACK_DOT_FLAGS:
        d = next(x for x in instances[inst]["per_flag_gt_detail"]
                 if x["flag_id"] == fid and x["state"] == st)
        if not d["abstain"] or d["category"] != cat:
            _fail(f"黑点族旗标登记与实测不符: {fid}")
        black_rows.append({"flag_id": fid, "instance": inst, "state": st,
                           "category": d["category"], "abstain": True})
    # 绿色区域语义化观察（r16 side_observation 先例延续：按实例分布；
    # 程序实测 substring 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、不构成
    # 判据输入；r17 实测 §5A 显式援引=2/6 派次，对照 r16 的 6/6 如实
    # 分列）
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
    # 呈现尺寸机制观察实测（本轮关键）：逐件摘录+统计
    px_rows = [ev for ev in PRESENTATION_SIZE_EVIDENCE if ev["has_px_size"]]
    dpi_rows = [ev for ev in PRESENTATION_SIZE_EVIDENCE
                if ev.get("mentions_dpi")]
    witness_dims = {side: witness_doc["renders"][witness_key[side]]["image_wh"]
                    for side in PNG_FILES}
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    black_by_instance = {n: sum(1 for row in black_rows
                                if row["instance"] == n)
                         for n in INSTANCE_ORDER}
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决不因本观察"
                 "改写；per r17-prep-record adjudication."
                 "mechanism_observation_separate：bottom 侧观察（M2/黑点"
                 "族 M3）；读者对细节可见性的自述摘录；courtyard 旗与黑点"
                 "族分布对照 r15/r16；gt 匹配照常）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道三分判据分开实测（机制 (a)）：M1=top 全旗聚合弃权率"
                "=%d/%d=%s；(a) 支 ≤0.671429（r16 零变更基线 0.771429 "
                "绝对降幅 ≥0.10 的计划件显著收益阈值；r16 基线 27/35 "
                "live 重放与在案登记/axis-plan 双锚交叉核对一致）→"
                "crit_a=%s；(b) 支 ≥0.771429（r16 零变更基线水平，双侧"
                "复算一致）→crit_b=%s；⇒ verdict=%s（%s）。两支分开如实"
                "记录、不合并；(a)(b) 同真被自洽性检查排除（6 位定点整数"
                "交叉相乘比较）。"
                % (abst_top, flags_top, top_rate,
                   crit_a_ok, crit_b_ok, verdict, letter_branch)),
            "counts": {
                "r16_top_baseline_registered":
                    BASE16_TOP_AGGREGATE_REGISTERED,
                "r16_top_baseline_live": f"{base16_ab}/{base16_fl}",
                "r16_top_baseline_value": cal._ratio(base16_ab, base16_fl),
                "supported_threshold_6dp": SUPPORTED_THRESHOLD_6DP,
                "reject_threshold_6dp": REJECT_THRESHOLD_6DP,
                "top_flags_r17": flags_top,
                "top_abstain_r17": abst_top,
                "top_abstain_rate_r17": top_rate,
                "crit_a_supported_le_0.671429": crit_a_ok,
                "crit_b_reject_ge_0.771429": crit_b_ok,
                "verdict": verdict,
            },
            "status": (
                "轴1 仪器轮（渲染 640→1280dpi 单变量）下 M1 落点=%s 支"
                "（如实单列）；判据命中与否的描述性结论，非因果证明"
                % verdict),
        },
        "guards_g1_g2": {
            "role": ("守门通道独立单列（per r17-prep-record "
                     "attribution_plan.guard_channel 与 axis-plan guards "
                     "原文；任一破坏→轴1 按 plan early_stop_rule 出局）"),
            "observation": (
                "G1=bottom courtyard 非弃权 0/0/0 维持：r17 实测=%s"
                "（对照 r16 基线 0/0/0 live 重放交叉核对一致；bottom "
                "courtyard 类旗标本身=%d 条、全部弃权）→G1=%s。G2="
                "guard_ok=True 维持：top 几何门面积比出局条目 R16=%d→"
                "R17=%d（不升）→guard_ok=%s→G2=%s。守门结论=%s。"
                % (list(by_instance.values()), bot_courtyard_flags,
                   "维持" if g1_ok else "破坏",
                   len(geo_r16), len(geo_r17), guard_ok,
                   "维持" if g2_ok else "破坏",
                   "G1/G2 均满足、不触发出局" if guards_ok
                   else "守门破坏→轴1 出局（字母照实+出局声明）")),
            "counts": {
                "g1_bottom_courtyard_non_abstain_r17": by_instance,
                "g1_bottom_courtyard_flags_total_r17": bot_courtyard_flags,
                "g1_r16_baseline_live": r16_courtyard_base,
                "g1_ok": g1_ok,
                "g2_geometry_gate_r16": len(geo_r16),
                "g2_geometry_gate_r17": len(geo_r17),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "axis_early_stop_triggered": axis_out,
            },
            "status": ("守门与字母裁决分开记账（守门不改变字母；"
                       "axis-plan early_stop_rule.guard_failure_exit 原文"
                       "语义如实援引）"),
        },
        "bottom_side_observation_maintenance": {
            "role": ("bottom 侧观察 M2（mechanism_observation_separate："
                     "单列、不影响字母；per axis-plan benefit_metrics."
                     "M2_bottom_aggregate_abstain_rate 同法）"),
            "observation": (
                "M2=bottom 全旗聚合弃权率=%d/%d=%s（对照 r16 基线 12/14="
                "%s，live 重放交叉核对一致）——方向=%s（改善方向：分辨率"
                "倍增轮 bottom 弃权 9/12 vs r16 12/14；轮际比较含实例群"
                "漂移混杂、照 axis-plan comparison_rule 显式容忍）。bottom "
                "改善通道三件实测：(1) 零旗标派次=%d 个（prep1-bottom-i1/"
                "prep1-bottom-i2 两派次零旗——逐件核实 flags=[]，r13–r16 "
                "无先例的零旗格在本轮出现；零旗格 view_check=not_"
                "applicable、不进弃权率分母，measurement_design item 5 "
                "口径在案）；(2) 黑点族弃权旗（M3，分型件 rubric 口径）"
                "=%d 条 vs r16=12（数量回落、方向性描述）；(3) bottom "
                "courtyard 类旗=%d 条（prep1-bottom-i3 R17B-001 孤立焊盘"
                "对近邻+courtyard 归属不确定弃权）全部弃权——非弃权 "
                "courtyard 维持 0/0/0（G1）。"
                % (abst_bot, flags_bot, bot_rate,
                   cal._ratio(base16_bot_ab, base16_bot_fl),
                   ("低于 r16 基线（改善方向）" if bot_below_r16
                    else "不低于 r16 基线（维持/恶化）"),
                   2, len(black_rows), bot_courtyard_flags)),
            "counts": {
                "r16_bottom_aggregate_registered":
                    BASE16_BOTTOM_AGGREGATE_REGISTERED,
                "r16_bottom_aggregate_live": f"{base16_bot_ab}/{base16_bot_fl}",
                "bottom_flags_r17": flags_bot,
                "bottom_abstain_r17": abst_bot,
                "bottom_abstain_rate_r17": bot_rate,
                "bottom_abstain_rate_r16_baseline":
                    cal._round6(base16_bot_ab / base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
                "zero_flag_parts": ["prep1-bottom-i1", "prep1-bottom-i2"],
                "zero_flag_dispatch_count": 2,
                "m3_blackdot_abstain_flags_rubric_r17": len(black_rows),
                "m3_blackdot_rubric_r16_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": (
                "6 派次摘录逐字来自对应 reading_notes（substring "
                "fail-closed 校验通过）——bottom 六派次仍按 §4(i) 量化"
                "判据把绿色翼瓣/空隙形态判入「系统性正常→不报告」（判读"
                "路径延续使用；含 2 个零旗标派次的 notes 内判正常路径）"),
            "status": (
                "M2 改善方向+零旗派次首现+M3 回落如实单列（不影响字母"
                "裁决；development 域只描述不断言）"),
        },
        "presentation_size_mechanism_observation": {
            "role": ("呈现尺寸机制观察（本轮关键；reject 支内嵌「视觉"
                     "编码器尺寸上限抵消增益」解释的对照材料；"
                     "mechanism_observation_separate 单列、不凌驾字母）"),
            "observation": (
                "逐件收集 12 派次 reading_notes 中关于图像呈现尺寸/清晰度/"
                "分辨率的自述（逐字摘录见 evidence，substring fail-closed "
                "校验）：(1) 自述绝对呈现尺寸者 %d 派次——applied-top-i2"
                "「图像以约 1000px 宽度呈现，丝印文字高度仅数像素，多数"
                "位号勉强可辨，限制了对丝印可读性与细小间隙的判定能力」、"
                "applied-top-i3「呈现尺寸约 1000×1000」、prep1-top-i3"
                "「图像以约 1000px 宽度呈现…最小号位号簇仅可辨轮廓」、"
                "prep1-bottom-i3「1280dpi 渲染…全图以约 1500px 呈现；唯 "
                "R17B-001 处两图形间最窄间隙接近呈现分辨率极限」；(2) "
                "相对尺寸自述 1 派次（applied-bottom-i3「单个焊盘约占图宽 "
                "2%%」）；(3) 其余 7 派次以「分辨率高/清晰度良好/接近可判"
                "上限/受清晰度限制」等措辞自述清晰度（12/12 派次均有"
                "清晰度轴自述）。仪器侧对照：本轮四 PNG 实测像素界="
                "top 4009×4009、bottom 4010×4009（witness-"
                "r17 renders.image_wh live 装载=%s）——读者自述呈现尺寸"
                "（约 1000–1500px）显著小于仪器像素界（自述值≈像素界/4"
                "～/2.7），即 1280dpi 的 4 倍像素增益在读者端被呈现端"
                "缩放截断。与字母裁决的关系（如实对照、不断言因果）："
                "本轮 M1=0.88 落入 reject 支（≥0.771429），该支内嵌解释"
                "之一即「视觉编码器尺寸上限抵消增益，机制观察须记录读者"
                "实际可见细节的自述」——上述自述（丝印文字高度仅数像素/"
                "最小间隙接近呈现分辨率极限/约 1000px 宽呈现）与该解释"
                "相容；top 通道自述呈现约 1000px 的三个派次恰为弃权最"
                "密集区（top-i1/top-i2 实例弃权率 1.0），bottom 自述"
                "「1280dpi 清晰/间隙可分辨」的派次则多把同族现象判正常"
                "或给出非弃权报告——方向性观察、development 域只描述"
                "不断言。"
                % (len(px_rows), json.dumps(witness_dims, ensure_ascii=False))),
            "counts": {
                "dispatches_with_px_size_self_report": len(px_rows),
                "px_size_sources": [ev["source"] for ev in px_rows],
                "stated_px_values": [ev["stated_px"] for ev in px_rows],
                "dispatches_mentioning_dpi": len(dpi_rows),
                "dispatches_with_clarity_self_report": 12,
                "instrument_png_image_wh": witness_dims,
            },
            "evidence": PRESENTATION_SIZE_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）"),
            "status": ("呈现尺寸自述与仪器像素界的差=呈现端缩放的机制"
                       "观察（如实单列、不凌驾字母裁决；为轴2/轴3 转向"
                       "与后续「呈现尺寸钉住」候选处置提供读者侧证据）"),
        },
        "top_new_detail_flags_1280": {
            "observation": (
                "1280 下新可见细节引发的新旗（机制观察；对照 r16 同位"
                "现象未见此类旗在案=方向性对照、非旗级配对）：top 弃权旗 "
                "4 条——半填充圆形 2 条（applied-top-i2 R17T-004「右半为"
                "淡黄色实心半圆填充」+prep1-top-i1 R17T-001「左半呈浅黄、"
                "右半呈浅粉、分界为竖直线」）、QFP 底边焊盘条疑似间断 "
                "1 条（prep1-top-i1 R17T-003「疑似出现约 2-3 个焊盘位的"
                "间断」）、IC 顶/底引脚排左端延伸差异 1 条（applied-top-i3 "
                "R17T-005）；bottom 非弃权报告旗 1 条=椭圆焊盘中段浅色"
                "竖向截断带（applied-bottom-i1 R17B-001「橙填充分为两瓣」"
                "——1280 新细节引发的首条 bottom 非弃权 other_advisory "
                "报告）。同族现象处置分化：半填充圆形另有 2 派次 notes "
                "判正常未报告（applied-top-i1 电池/极性标记、prep1-top-i3 "
                "§4(i) 最小重复单元路径，逐字摘录在案）。构成解读（如实"
                "单列）：高分辨率下新可见细节既触发新弃权（细节可见但仍"
                "不可负责任归类）也触发新报告（细节可见且可负责任描述）"
                "——与 M1 未回落并存。"),
            "counts": {
                "new_detail_flags_total": 5,
                "new_detail_top_abstain": 4,
                "new_detail_bottom_non_abstain": 1,
                "notes_normal_counterparts": 2,
            },
            "evidence": NEW_DETAIL_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 location_evidence/"
                               "reading_notes（substring fail-closed 校验"
                               "通过）"),
            "status": ("新细节旗=弃权与报告双向分化（如实单列、不凌驾"
                       "字母裁决）"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r16 side_observation 先例"
                "延续观察）：r17 bottom 六派次 notes 全部以「空隙/翼瓣」"
                "语义化绿色并按 §4(i) 判入系统性正常路径（6/6，判据轴"
                "延续）；但 §5A 仪器注记显式援引=%d/6 派次（prep1-bottom-i2 "
                "notes「结合 §5A 仪器注记判为铺铜 clearance 空隙」+"
                "prep1-bottom-i3 旗 location_evidence「按 §5A 仪器注记"
                "绿色区域为基材露白而非 courtyard 图元」）——对照 r16 的 "
                "6/6 显式援引如实分列（r17 指引 §5A 仅两处描述性 px 同步、"
                "判据文本逐字承 r15，援引下降属实例自述异质性、如实登记"
                "不作废）。逐实例 substring 计数「绿|翼瓣|空隙|§5A」+摘录"
                "如实登记（无期望、不构成判据输入）。"
                % sum(1 for v in green_semantics.values()
                      if v["§5A_cited"])),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("绿区语义化「空隙非图元」读法在实例群重抽下延续"
                       "（6/6 §4(i) 路径；§5A 显式援引 2/6 如实分列；"
                       "如实单列、不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点族现象追踪（机制观察 M3，分型件 rubric 口径）：r17 "
                "黑点族弃权旗 %d 条全部弃权——top 视右上连接器黑点 2 旗"
                "（applied-top-i1 R17T-003+applied-top-i2 R17T-001，"
                "r14–r16 首现现象延续）+bottom 左上黑点 6 旗（i1 2+i2 2+"
                "i3 2，全部 applied 板；r14–r16 同形态延续）——vs r16 "
                "黑点族 12 旗（分型件 rubric 口径在案）/r15=8：数量回落、"
                "方向性描述；r16 的「黑点-椭圆 courtyard 轮廓相切/近邻」"
                "归类（courtyard 通道 2 条）在本轮未再现（黑点全部按 "
                "other_advisory 报告）；全部存在性/接触性弃权出口；另有 "
                "4 派次 notes 把黑点判为安装孔/钻孔类正常特征未报告"
                "（prep1-top-i1/prep1-bottom-i1/prep1-bottom-i2/"
                "prep1-bottom-i3，逐字摘录在案）=同现象跨实例处置分化，"
                "如实登记。"),
            "black_dot_flags": black_rows,
            "by_instance": black_by_instance,
            "all_abstain": all(r["abstain"] for r in black_rows),
            "notes_normal_dispositions": (
                "4 派次判正常：prep1-top-i1「右上角两枚同尺寸纵向对齐的"
                "黑色实心圆点（与安装孔常规形态一致）」+prep1-bottom-i1"
                "「左上角两个小黑圆点两处形态一致、与焊盘轮廓均可见间隙，"
                "未见冲突」+prep1-bottom-i2「各带一相邻黑色小孔、两组互为 "
                "180° 旋转且形态彼此一致」+prep1-bottom-i3「左上两组长"
                "圆形焊盘旁的两个裸钻孔圆点形态一致」（摘录见 evidence 表 "
                "disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点族弃权路径延续+数量回落（8 vs r16 12）+处置"
                       "实例分化（如实单列、不凌驾字母裁决）"),
        },
        "top_abstain_typology": {
            "observation": (
                "top 弃权理由构成分型（机制观察，为 M1=0.88 未回落的归因"
                "提供分解）：本轮 top 弃权旗 %d 条逐旗按 location_evidence "
                "关键词分类——接触性（真实接触 vs 视觉贴近不可分辨/是否"
                "接触不可确认）=%d 条、存在性（性质不明/是否存在不可"
                "确认）=%d 条、层归属等其他出口=%d 条。构成解读（如实"
                "单列）：接触性弃权集中于 courtyard 类旗标与丝印-焊盘"
                "近邻（§4(iii) 判据路径延续），存在性弃权横跨 silk/other/"
                "reroute/placement 各类（黑点性质、半填充圆形含义、QFP "
                "间断、绕行是否存在等）——top 弃权非单一机制驱动；"
                "对照 r16（接触性 11+存在性 15+层归属其他 1，27 条）："
                "接触性 11→8、存在性 15→14、其他 1→0，弃权绝对数 "
                "27→22 但弃权率因旗数分母同降（35→25）而上升至 0.88"
                "——「分辨率倍增下弃权旗数减少但非弃权报告未同步增加」"
                "的构成如实分列（top 非弃权旗仅 3 条，其中 2 条为 1280 "
                "新细节形态相关）。逐旗摘录与分类在案（rows）。"
                % (len(typology_rows), typology_counts["contact"],
                   typology_counts["existence"],
                   typology_counts["other_layer"])),
            "type_counts": typology_counts,
            "top_abstain_flags_total": len(typology_rows),
            "r16_reference_counts": {"contact": 11, "existence": 15,
                                     "other_layer": 1},
            "rows": typology_rows,
            "evidence_check": (
                "%d/%d 条摘录逐字来自对应 location_evidence 且 (source, "
                "flag_id) 集合与实测 top 弃权旗集合逐一相等（substring+"
                "覆盖 fail-closed 校验通过）"
                % (len(typology_rows), len(typology_rows))),
            "top_abstain_rates_by_instance": top_rates,
            "top_abstain_rate_range": top_range,
            "status": ("top 弃权构成=接触性主通道+存在性多通道分散（"
                       "如实单列、不凌驾字母裁决；为轴2/轴3 转向提供"
                       "分型依据）"),
        },
        "residual_instance_differences": {
            "observation": (
                "残余实例差异（如实单列）：(1) top 弃权率 %s/%s/%s（极差 "
                "%s）——top-i1/top-i2 双实例全弃权（8/8=1.0）、top-i3 "
                "6/9=0.666667（该实例贡献本轮全部 3 条 top 非弃权旗）；"
                "(2) bottom 弃权率 %s/%s/%s（极差 %s）——bottom-i2 最低 "
                "（2/3，含 1 个零旗派次）；(3) placement/孤立图形处置"
                "实例分化延续：板内孤立焊盘组 bottom-i1 弃权（applied）/"
                "bottom-i2、bottom-i3 非弃权报告（applied）/两个 prep1 "
                "派次 notes 判正常不报告——同现象跨实例/跨板出口不同="
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
                       "关系（实例群重抽为轮际混杂、轮内样本极小）"),
        },
    }
    metric_lesson_continuation = {
        "role": ("度量设计教训延续（如实，供未来预注册参考；本轮不追溯"
                 "适用；per r17-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r17 三分判据以 6 位定点整数交叉相乘执行（阈值=冻结件 "
            "0.671429/0.771429 原文），拒绝支阈值恰=r16 基线水平、"
            "supported 支阈值=基线−0.10 的派生关系经脚本核验（"
            "REJECT−100000=SUPPORTED，6 位定点）——阈值派生关系的机械"
            "可验性=本轮度量设计可复算要点；跨轮实例群漂移混杂照旧声明"
            "（r15→r16 纯重抽漂移 0.09064 在案、axis-plan "
            "comparison_rule 显式容忍且不消除）；M1 分母（top 旗数）"
            "本身随仪器变化（35→25），弃权率比较含分母效应、构成分解"
            "（top 弃权构成分型+新细节旗双向分化）单列补足；呈现尺寸"
            "自述（约 1000–1500px vs 仪器 4009/4010px）提示「仪器像素"
            "增益≠读者可见增益」，后续仪器轴候选处置可考虑呈现尺寸钉住"
            "（如实登记、不构成本轮判据输入）。"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一轮候选方向（如实登记，不构成本轮判据"
                   "输入）：reject 支内嵌「转向轴2/轴3」（axis-plan "
                   "stage1 rounds R18=黑点仪器注记/R19=§4(iii) 接触性"
                   "可操作分辨条款，均须各自 prep-record 预注册后执行）；"
                   "不得回溯改判既往轮次（r8–r16 字母裁决维持不变）"),
    }
    # r16 分层基线（逐实例弃权率，live 重放；不手工抄数）
    r16_top_rates_live = r16_top_rates
    r16_bottom_rates = {}
    for n in ("bottom-i1", "bottom-i2", "bottom-i3"):
        r16_bottom_rates[n] = run_r16["instances"][n]["combined"][
            "abstain_rate"]
    r16_bottom_range = cal._round6(
        max(r16_bottom_rates.values()) - min(r16_bottom_rates.values()))
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R17,
                                "sha256": _sha(REL_PREP_R17)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "supported": adj["supported"],
            "reject": adj["reject"],
            "marginal": adj["marginal"],
            "guards": adj["guards"],
            "primary_channel_change": prep_doc["attribution_plan"][
                "primary_channel"]["change"],
            "primary_channel_metric": prep_doc["attribution_plan"][
                "primary_channel"]["metric"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "mechanism_observation_separate":
                adj["mechanism_observation_separate"],
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel_metric": prep_doc["attribution_plan"][
            "primary_channel"]["metric"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r17-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮轴1 收益方向归因"
            "（axis-experiment-plan-r17-r20 冻结比较规则），与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "top_abstain_flags_r17": flags_top,
            "top_abstain_count_r17": abst_top,
            "top_abstain_rate_r17": top_rate,
            "top_abstain_rate_r17_arithmetic":
                f"M1 = top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（三分判据度量；12 派次全口径）",
            "crit_a_supported_le_0.671429": crit_a_ok,
            "crit_b_reject_ge_0.771429": crit_b_ok,
            "top_abstain_rate_r16_baseline_live":
                f"{base16_ab}/{base16_fl}",
            "top_abstain_rate_r16_baseline_value":
                cal._ratio(base16_ab, base16_fl),
            "baseline_replay_note": (
                "基线=同一聚合逻辑对 calibration-run-r16.json 内嵌实例"
                "记录（states 层 reader_flags+compare_v3.abstain）双侧"
                "复算，不手工抄数；且与在案登记值（r17-prep-record "
                "chain_anchors.run_r16_baseline_anchor.frozen_values："
                "top 27/35=0.771429、guard_ok=True；axis-plan "
                "baselines_registered.r16_baseline.M1=0.771429）交叉"
                "核对（fail-closed，见 baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r17":
                    by_instance,
                "bottom_courtyard_flags_total_r17": bot_courtyard_flags,
                "bottom_abstain_flags_r17": flags_bot,
                "bottom_abstain_count_r17": abst_bot,
                "bottom_abstain_rate_r17": bot_rate,
                "bottom_abstain_rate_r17_arithmetic":
                    f"M2 = bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                    f"{bot_rate}"
                    f"（对照 r16 基线 12/14=0.857143；"
                    f"mechanism_observation_separate 单列、不影响字母）",
                "bottom_abstain_rate_r16_baseline_live":
                    f"{base16_bot_ab}/{base16_bot_fl}",
                "bottom_abstain_rate_r16_baseline_value":
                    cal._ratio(base16_bot_ab, base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
            },
            "verdict": verdict,
            "letter_branch": letter_branch,
            "bottom_courtyard_detail_r17": [
                {"instance": r["instance"],
                 "courtyard_non_abstain_count": by_instance[r["instance"]],
                 "note": r["note"]}
                for r in SIDE_OBS_REGISTERED],
            "baseline_cross_check": {
                "r16_top_registered": BASE16_TOP_AGGREGATE_REGISTERED,
                "r16_top_live": f"{base16_ab}/{base16_fl}",
                "r16_bottom_registered":
                    BASE16_BOTTOM_AGGREGATE_REGISTERED,
                "r16_bottom_live": f"{base16_bot_ab}/{base16_bot_fl}",
                "r16_bottom_courtyard_registered":
                    R16_BOTTOM_COURTYARD_BASELINE,
                "r16_bottom_courtyard_live": r16_courtyard_base,
                "r16_top_instance_rates_registered":
                    R16_TOP_INSTANCE_RATES_REGISTERED,
                "r16_top_instance_rates_live": r16_top_rates,
                "axis_plan_r16_baseline_M1_M2_M3_M4": [
                    rb["M1_top_aggregate_abstain_rate"],
                    rb["M2_bottom_aggregate_abstain_rate"],
                    rb["M3_blackdot_abstain_flags_rubric"],
                    rb["M4_top_per_instance_rate_range"]],
                "note": ("基线数字与 run-r16 内嵌输入重放实测交叉核对一致"
                         "（fail-closed：live 重放与登记不符即 FAIL）；"
                         "registered=r17-prep-record/axis-plan 在案登记/"
                         "判据原文冻结值，live=本轮从 run-doc 内嵌输入"
                         "重放实测"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（实测 %s，"
                    "r16 基线 live 重放 0/0/0）=%s；G2=guard_ok=True "
                    "维持（top 几何门面积比出局条目 R16=%d→R17=%d）"
                    "=%s；任一破坏→轴1 按 plan early_stop_rule 出局"
                    % (list(by_instance.values()),
                       "满足" if g1_ok else "破坏",
                       len(geo_r16), len(geo_r17),
                       "满足" if g2_ok else "破坏")),
                "g1_ok": g1_ok,
                "g2_geometry_gate_r16": len(geo_r16),
                "g2_geometry_gate_r17": len(geo_r17),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "note": ("守门通道按 r17-prep-record attribution_plan."
                         "guard_channel 与 axis-plan guards 独立复核；"
                         "不构成 r17 字母裁决输入"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r16 run-record courtyard_tracking 在案先例延续）——"
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
                "abstain_rate_r16_representative":
                    run_r16["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r17_representative_note": (
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
                    "代表配置）→r15 0.785714（11/14，代表配置）→r16 "
                    "0.764706（13/17，代表配置）→r17 见代表配置分列；"
                    "主通道三分判据与门各自独立计算、互不凌驾（prep-record "
                    "descriptive_boundary_note 原文语义）——门联合评价与"
                    "字母裁决分列不合并"),
            },
            "r17_total_flags_note": (
                "六实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；M1=top 全旗聚合"
                "弃权率 %d/%d=%s 为三分判据度量、M2=bottom 全旗聚合弃权"
                "率 %d/%d=%s 为侧观察度量、各自单列）"
                % (n_total_all,
                   (flags_top - abst_top) + (flags_bot - abst_bot),
                   abst_top + abst_bot,
                   cal._ratio(abst_top + abst_bot, n_total_all),
                   abst_top, flags_top, top_rate,
                   abst_bot, flags_bot, bot_rate)),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"supported=「{adj['supported'][:80]}…」；"
            f"reject=「{adj['reject'][:80]}…」；"
            f"marginal=「{adj['marginal'][:80]}…」"
            "（r17-prep-record.json hypothesis_test.adjudication 判据原文"
            "全文见 preregistered_criteria_quote，轮后如实执行；结果无论"
            "方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r17": {
            "role": ("r12 假设通道被动追踪（round13–round16-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r17": reroute_rows,
            "reroute_total_r17": len(reroute_rows),
            "reroute_by_instance_r17": {
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
                                 "r16": REROUTE_CHAIN_PRIOR["r16"],
                                 "r17": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径）：r10=2→r11=1→r12=0→"
                "r13 被动追踪=1（R13T-009 在案）→r14=0（R14T-004 子串零"
                "命中）→r15 机械命中=1（R15T-001 非弃权旗含「蛇形」"
                "子串——否定式援引、非滥用型引用，run-r15 在案）→r16=0"
                "（在案）→r17=0（R17T-002「等长|蛇形」子串零命中、"
                "存在性弃权）——不构成 r17 判据输入（两判据分列互不"
                "凌驾）"),
        },
        "stratified_observation": {
            "top": {"r16_by_instance_live": r16_top_rates_live,
                    "r16_range_live": AXIS_R16_M4_TOP_RANGE,
                    "r17_by_instance": top_rates,
                    "r17_range": top_range,
                    "direction": ("r16 三实例 %s（轮内极差 %s）→r17 三"
                                  "实例 %s/%s/%s（轮内极差 %s）——渲染"
                                  "分辨率倍增、实例群重抽混杂照旧下实例"
                                  "层的方向性对照（聚合 M1 %d/%d=%s vs "
                                  "r16 基线 27/35=0.771429；reject 支"
                                  "构成；轮内实例差异照旧）"
                                  % (f"{r16_top_rates_live['top-i1']}/"
                                     f"{r16_top_rates_live['top-i2']}/"
                                     f"{r16_top_rates_live['top-i3']}",
                                     AXIS_R16_M4_TOP_RANGE,
                                     top_rates["top-i1"],
                                     top_rates["top-i2"],
                                     top_rates["top-i3"], top_range,
                                     abst_top, flags_top, top_rate))},
            "bottom": {"r16_by_instance_live": r16_bottom_rates,
                       "r16_range_live": r16_bottom_range,
                       "r17_by_instance": bottom_rates,
                       "r17_range": bottom_range,
                       "direction": ("r16 三实例 %s（极差 %s）→r17 三"
                                     "实例 %s/%s/%s（极差 %s）——bottom "
                                     "聚合 M2 %d/%d=%s vs r16 的 12/14="
                                     "0.857143（侧观察如实单列；改善方向"
                                     "与零旗派次首现并记）"
                                     % (f"{r16_bottom_rates['bottom-i1']}/"
                                        f"{r16_bottom_rates['bottom-i2']}/"
                                        f"{r16_bottom_rates['bottom-i3']}",
                                        r16_bottom_range,
                                        bottom_rates["bottom-i1"],
                                        bottom_rates["bottom-i2"],
                                        bottom_rates["bottom-i3"],
                                        bottom_range,
                                        abst_bot, flags_bot, bot_rate))},
            "confounder_note": (
                "跨轮 reader 实例不同（轮际比较固有混杂，per axis-plan "
                "comparison_rule.drift_confound_note 显式容忍：r15→r16 "
                "纯重抽漂移 0.09064 在案）+轮内实例差异=混杂因素照旧"
                "声明；v1.2 工具规约把工具行为钉住（12/12 自述「未读取"
                "盘上任何其他文件」）但判读实例仍为不同实例；每视角 n=3 "
                "仍为小样本；development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r10: dict, run_r11: dict, run_r12: dict,
                             run_r13: dict, run_r14: dict, run_r15: dict,
                             run_r16: dict) -> dict:
    """courtyard 被动追踪（r11–r16 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r17 courtyard 类旗标与命中如实入账
    ——top 非弃权 1 条（applied-top-i3 R17T-001，containment 无 ≥0.5
    交叠=零命中）+top 弃权 6 条+bottom 弃权 1 条（prep1-bottom-i3
    R17B-001）。"""
    note_source = {
        "path_rel": REL_PREP_R17, "sha256": _sha(REL_PREP_R17),
        "quote": None,
        "note": ("r17-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r16 "
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
    prior = run_r16["courtyard_tracking"]
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
        "r17_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（bottom=prep1-bottom-i3 R17B-001 孤立焊盘"
                             "对绿色轮廓近邻+courtyard 归属不确定弃权 "
                             "1 条；对照 r16 的 top 12+bottom 2 全弃权，"
                             "如实登记）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r17": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r16": prior["courtyard_matches_r16"],
        "courtyard_matches_r16_detail": (
            "R16 非弃权 courtyard 1 条（top-i2 R16T-001↔GT-REVC-AP-6-"
            "R2LED2）命中 1（run-r16 在案）；courtyard 类弃权旗=top 12+"
            "bottom 2（run-r16 在案）"),
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
            "（Y1/R4J3 类 courtyard 密集区）——r12–r15 连续零再现、"
            "r16 回升 1 条（R16T-001↔AP-6）；r17 非弃权 courtyard=%d 条"
            "（命中=%d，containment 无 ≥0.5 交叠，如实登记）；GT/阈值"
            "零改动"
            % (len(non_abstain_rows),
               sum(r["matches"] for r in non_abstain_rows))),
        "bottom_observation": {
            "fact": ("R17 bottom %d 旗（bottom-i1 4+bottom-i2 3+"
                     "bottom-i3 5，含 2 个零旗标派次 prep1-bottom-i1/"
                     "prep1-bottom-i2）=非弃权 %d（placement/孤立图形类 "
                     "2+other_advisory 椭圆截断带 1）+弃权 %d："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=1（prep1-bottom-i3 孤立"
                     "焊盘对近邻弃权——r14 弃权 4 条/r15 零旗标/r16 弃权 "
                     "2 条/r17 弃权 1 条，逐轮构成如实分列）；弃权"
                     "构成见 reader.flag_count.by_category；本轮派次层 "
                     "2 格零旗标（实例层无零分母，measurement_design "
                     "item 5 口径在案：遇零分母→None 不编造数值）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
            "evidence": QUANT_CRITERION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）——bottom 六派次"
                               "仍按 §4(i) 把绿色翼瓣/空隙形态判入系统性"
                               "正常路径（不进 flags；含 2 个零旗派次的 "
                               "notes 内判正常路径）"),
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
    run_r16 = _json_load(REL_RUN_R16)
    axis_plan = _json_load(REL_AXIS_PLAN)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, run_r16, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, run_r15, run_r16,
                                axis_plan, instances,
                                view_layer, attribution, raw_texts,
                                parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9,
                                         run_r10, run_r11, run_r12,
                                         run_r13, run_r14, run_r15,
                                         run_r16)

    prep_r17 = _json_load(REL_PREP_R17)
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
            "五键投影（process-v1 §2 步骤3）；R17 reroute 类一旗 "
            "location_evidence 逐字在案（R17T-002 prep1-top-i2，存在性"
            "弃权、「等长|蛇形」子串零命中——reroute_continuation_r17 "
            "逐旗判定在案）；"
            "R17 top 弃权旗 22 条逐旗分型摘录在案（top_abstain_typology："
            "接触性 8+存在性 14+层归属其他 0）；"
            "bottom 黑点族/placement 处置弃权旗摘录在案（black_dot_"
            "tracking/residual_instance_differences）；呈现尺寸自述逐件"
            "摘录在案（presentation_size_mechanism_observation）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "zero_flag_parts": {
            "parts": zero_flag_parts,
            "note": ("本轮 12 格中 10 格≥1 旗、2 格零旗标（prep1-"
                     "bottom-i1/prep1-bottom-i2，flags=[] 逐件核实；"
                     "r13–r16 无零旗格先例下首现）——实例层=两板合计"
                     "全部≥3 旗、弃权率全部有定义；零旗格 view_check="
                     "not_applicable、不进弃权率分母；"
                     "measurement_design item 5 口径在案（遇零旗标"
                     "分母→按库侧 cal._ratio 先例=None+文字说明，不编造"
                     "数值）"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R17, "role": "r17_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R17)},
        {"path_rel": REL_AXIS_PLAN,
         "role": "axis_experiment_plan_r17_r20_frozen",
         "sha256": _sha(REL_AXIS_PLAN)},
        {"path_rel": REL_DEV_R16,
         "role": "r16_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R16)},
        {"path_rel": REL_PREP_R16, "role": "r16_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R16)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R17,
         "role": "observation_guidance_r17_active",
         "sha256": _sha(REL_GUIDANCE_R17)},
        {"path_rel": REL_GUIDANCE_R15,
         "role": "observation_guidance_r15_transform_base",
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
        {"path_rel": REL_FRAMING_R17,
         "role": "render_framing_r17_single_variable_declaration",
         "sha256": _sha(REL_FRAMING_R17)},
        {"path_rel": REL_WITNESS_R17,
         "role": "render_witness_r17_px_witness",
         "sha256": _sha(REL_WITNESS_R17)},
        {"path_rel": REL_FRAMING_R14B,
         "role": "render_framing_r14b_lineage",
         "sha256": _sha(REL_FRAMING_R14B)},
        {"path_rel": REL_WITNESS_R14B,
         "role": "render_witness_r14b_lineage",
         "sha256": _sha(REL_WITNESS_R14B)},
        {"path_rel": REL_DEV_R15,
         "role": "r15_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R15)},
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
         "role": "render_png_applied_top_r17_new_render_1280dpi",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r17_new_render_1280dpi",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"],
         "role": "render_png_prep1_top_r17_new_render_1280dpi",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r17_new_render_1280dpi",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r17",
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
            "changed": True,
            "axis_id": "A1_render_resolution_x2",
            "nature": INSTRUMENT_NATURE,
            "note": prep_r17["instrument_change"]["note"],
            "declaration": prep_r17["instrument_change"]["declaration"],
            "renders_registered": [
                {"state_side": e["state_side"], "path_rel": e["path_rel"],
                 "sha256_measured": e["sha256_measured"],
                 "sha256_witness_registered":
                     e["sha256_witness_registered"],
                 "witness_record": e["witness_record"],
                 "match": e["match"]}
                for e in prep_r17["instrument_change"]["renders"]],
            "components": [
                "renders-r17 四图（1280dpi 全新渲染、r14b 配色规则重放；"
                "dpi=唯一仪器变量）"],
            "unchanged_components": list(prep_r17["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v.get("attribution_channel"),
                 "instrument_change": v["instrument_change"]}
                for v in prep_r17["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r17["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r17["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r17["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R17, "sha256": _sha(REL_PREP_R17)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；r17 指引 §6 示例旗 ID 前缀 R17T-/R17B- 随指引"
            "落盘固化（r13→r15「随指引落盘固化」路径回归，无需派发层"
            "覆盖，per r17-prep-record protocol_amendment.naming）；"
            "实例间编号独立；"
            "同实例两板各自从头编号=r17 实测输出行为、与 prep-record "
            "naming「同实例跨板连续」声明不同（与 r15/r16 实测同形态），"
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
                    "r13 指引 §4（经 r17 指引逐字承 r15 原文适用，本轮指引"
                    "=observation-guidance-r17.md，§2–§7 分段逐字保留断言"
                    "在案）："
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
                                      "（渲染探针链与 framing/witness/"
                                      "diag-r17-render 记录不进任何 "
                                      "reader 上下文）、零 legend/零其他"
                                      "解释（判读输入=指引+单张 PNG+派发"
                                      "指令）；每图独立判读；跨实例/跨视角"
                                      "禁止交流（独立性亦为轴1 收益裁决"
                                      "有效性的前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R17,
                                 "sha256": _sha(REL_GUIDANCE_R17),
                                 "frozen_before_read": True,
                                 "transform_mode":
                                     "mechanical_transform_derive",
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R15,
                                     "sha256": _sha(REL_GUIDANCE_R15),
                                     "role": ("r17 指引的机械变换基座"
                                              "（§2–§7 判据逐字承 r15；"
                                              "r15 指引=r15 轮落盘产物）")},
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：axis-experiment-plan-r17-r20.json"
                 "（b6ec6467…，stage1 R17=轴1 渲染分辨率倍增轮定义+"
                 "comparison_rule 显著收益定义+守门+early_stop_rule，"
                 "先于 R17–R21 任何实验轮盲读冻结；用户 2026-09-09"
                 "「三条轴单独/组合/全组合尝试，选择收益最大的继续」"
                 "user_directive_note 在案）→r17-prep-record.json"
                 "（ceba4fef…，本轮预注册件，measurement_design 五条"
                 "聚合口径与 hypothesis_test.adjudication 三分判据"
                 "（supported ≤0.671429/marginal 带内/reject ≥0.771429）"
                 "先于盲读冻结；instrument_change.changed=true；"
                 "guidance=机械变换；渲染件=renders-r17）先于本轮盲读"
                 "落盘（零 GT 暴露声明在案 no_visual_reading=true；"
                 "pre_round_review=satisfied_by_probe_and_plan——s62 "
                 "探针 PASS+diag-r17-render 对照裁片主审核验+axis-plan "
                 "冻结）→判读指引=observation-guidance-r17.md"
                 "（07c520be…，r15 指引机械变换产物，本轮唯一判读依据）"
                 "→渲染=renders-r17 四图全新渲染（1280dpi，四 PNG sha="
                 "witness-r17 登记值=prep-record 登记值三方一致）→"
                 "12 次盲读→比对记录（读者产物零改动）。GT 重"
                 "投影（derivation-log-r5.json，13 条 frame_box_pct_r5）"
                 "已在案沿用（同一板 Edge.Cuts 几何+同 40pt 组合页仅 "
                 "dpi 变更，重投影口径随 r14 顶层更换先例沿用；bottom "
                 "渲染变更不触及；GT 全部 side=top 且 bottom GT 无源在"
                 "案 gt-audit-r1）；GT 冻结纪律：轮后未增删改；gt-audit-r1 "
                 "结论维持 GT 零改动（三候选关闭，gt_audit_reference 在案）。"),
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
            "r16_run": {"path_rel": REL_RUN_R16, "sha256": _sha(REL_RUN_R16)},
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
                     "轮：§5A 渲染配色仪器注记配套，verdict=reject）与 "
                     "R16（同指引重复轮/零变更轮：唯一操纵因子=实例群"
                     "重抽，verdict=inconclusive）run 在案；R17=轴1 仪器"
                     "轮（渲染侧单变量：renders-r17 四图 640→1280dpi "
                     "全新渲染，r14b 配色规则重放；执行 axis-plan stage1 "
                     "R17=A1_render_resolution_x2；与 R5 的「有效分辨率"
                     "单变量轮」同为渲染侧单变量轮血统）；轮间对比"
                     "由后续 round17-dev-record（另包落盘）与 "
                     "channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取与通道重放为纯函数"
            "（六实例旗数 8/8/9/4/3/5→代表配置 top-i1+bottom-i1（top "
            "中位实例 8 为 i1/i2 tie、按先序取 top-i1 并如实注明；bottom "
            "中位 4 唯一=bottom-i1）唯一可复算），无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-09-r17（事件序="
            "axis-experiment-plan-r17-r20（b6ec6467…，冻结件在案）→"
            "r17-prep-record"
            "（ceba4fef…，本轮预注册件，先于盲读冻结）→r17 指引机械"
            "变换落盘（07c520be…，本轮唯一判读依据）→renders-r17 四图"
            "全新渲染冻结（s62 仪器包在案）→12 次盲读→比对"
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
                                run_r16: dict,
                                parsed: dict, raw_texts: dict) -> None:
    """run-r17 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 8, "top-i2": 8, "top-i3": 9, "bottom-i1": 4,
                  "bottom-i2": 3, "bottom-i3": 5}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 8, "top-i2": 8, "top-i3": 6, "bottom-i1": 3,
                "bottom-i2": 2, "bottom-i3": 4}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 37:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.916667 \
            or agg["flag_count_total"] != 12 \
            or agg["abstain_count_total"] != 11:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "reject":
        _fail("假设字母裁决与预注册判据复算不符")
    m = hyp["measurement"]
    if m["top_abstain_flags_r17"] != 25 or m["top_abstain_count_r17"] != 22 \
            or m["top_abstain_rate_r17"] != 0.88:
        _fail("主通道 M1 计数与实测不一致")
    if m["crit_a_supported_le_0.671429"] is not False \
            or m["crit_b_reject_ge_0.771429"] is not True:
        _fail("三分判据布尔与实测不一致（22/25=0.88 应落 reject 支）")
    if m["top_abstain_rate_r16_baseline_value"] != 0.771429:
        _fail("r16 基线值与在案登记不一致")
    if hyp["hypothesis_id"] != "axis-plan-r17-resolution-double":
        _fail("hypothesis_id 与预登记不符")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r17"] != 1 \
            or bso["bottom_abstain_flags_r17"] != 12 \
            or bso["bottom_abstain_count_r17"] != 9 \
            or bso["bottom_abstain_rate_r17"] != 0.75 \
            or bso["bottom_courtyard_non_abstain_by_instance_r17"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0} \
            or bso["bottom_rate_direction_vs_r16"] != "improved":
        _fail("bottom 侧观察计数与实测不一致")
    g = m["guard_channel"]
    if g["g1_ok"] is not True or g["g2_guard_ok"] is not True \
            or g["guards_ok"] is not True \
            or g["g2_geometry_gate_r16"] != 0 \
            or g["g2_geometry_gate_r17"] != 0:
        _fail("守门 G1/G2 计数与实测不一致")
    mo = hyp["mechanism_observation"]
    tt = mo["top_abstain_typology"]
    if tt["type_counts"] != {"contact": 8, "existence": 14,
                             "other_layer": 0} \
            or tt["top_abstain_flags_total"] != 22:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 8 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 1, "top-i2": 1, "top-i3": 0,
                                     "bottom-i1": 2, "bottom-i2": 2,
                                     "bottom-i3": 2} \
            or mo["bottom_side_observation_maintenance"]["counts"][
                "m3_blackdot_abstain_flags_rubric_r17"] != 8:
        _fail("黑点族计数与实测不一致")
    ps = mo["presentation_size_mechanism_observation"]
    if ps["counts"]["dispatches_with_px_size_self_report"] != 4 \
            or ps["counts"]["dispatches_mentioning_dpi"] != 3 \
            or len(ps["evidence"]) != 12 \
            or ps["counts"]["instrument_png_image_wh"]["applied-top"] \
            != [4009, 4009] \
            or ps["counts"]["instrument_png_image_wh"]["applied-bottom"] \
            != [4010, 4009]:
        _fail("呈现尺寸机制观察计数与实测不一致")
    nd = mo["top_new_detail_flags_1280"]
    if nd["counts"]["new_detail_flags_total"] != 5 \
            or nd["counts"]["new_detail_top_abstain"] != 4 \
            or nd["counts"]["new_detail_bottom_non_abstain"] != 1:
        _fail("1280 新细节旗计数与实测不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if sum(1 for v in gs.values() if v["§5A_cited"]) != 2:
        _fail("绿区语义化 §5A 引用与实测不一致（应为 2/6 实例）")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.333333 \
            or vl["bottom"]["abstain_rate_range"] != 0.133333:
        _fail("视角层极差与实测不一致（M4 方向）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 0 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.0:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != []:
        _fail("matches 明细与实测不一致（r17 应零命中：top 3 条非弃权旗"
              "与同态 GT containment 无 ≥0.5 交叠、bottom 非弃权旗结构性"
              "无匹配）")
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
            or run_r16["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r16"] \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 1:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R16 0→R17 0；类别 R16 1→R17 0）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r17_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r17_category_mismatch_entries"]) != 0:
        _fail("通道条目数与实测声明不一致")
    # courtyard 追踪与实测一致（r17 非弃权 courtyard=1、弃权=7、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r17"] != 0 or len(
            ct["r17_courtyard_flags"]["non_abstain"]) != 1:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r17_courtyard_flags"]["abstain"]) != 7:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 零旗标派次与实测一致（prep1-bottom-i1/i2 两格）
    if [(z["instance"], z["state"]) for z in
            run_doc["reader"]["zero_flag_parts"]["parts"]] != \
            [("bottom-i1", "prep1"), ("bottom-i2", "prep1")]:
        _fail("零旗标派次与实测不一致")
    # 逐旗判定/工具规约/量化判据/分型/黑点/placement/绿区/呈现尺寸/
    # 新细节摘录逐字在案
    for r in hyp["reroute_continuation_r17"]["reroute_flag_detail_r17"]:
        if r["form_desc_excerpt"] not in raw_texts[r["source"]]:
            _fail(f"逐旗判定摘录与 reader 原文不符: {r['flag_id']}")
    for ev in mo["bottom_side_observation_maintenance"][
            "reader_note_evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["green_semantics_by_instance"]["evidence"]:
        src_text = (raw_texts[ev["source"]]
                    if ev.get("kind") == "location_evidence"
                    else parsed[ev["source"]]["reading_notes"])
        if ev["excerpt"] not in src_text:
            _fail(f"绿区语义化摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["top_abstain_typology"]["rows"]:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"top 弃权分型摘录与 reader 原文不符: {ev['flag_id']}")
    for ev in mo["black_dot_tracking"]["evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"黑点族摘录与 reader 原文不符: {ev.get('flag_id')}")
    for ev in mo["presentation_size_mechanism_observation"]["evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"呈现尺寸自述摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["top_new_detail_flags_1280"]["evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev.get("kind") == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"1280 新细节摘录与 reader 原文不符: {ev.get('flag_id')}")
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r17")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), _json_load(REL_RUN_R15),
        _json_load(REL_RUN_R16),
        parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R17), run_bytes,
                         "calibration-run-r17.json")
    run_sha = _sha(REL_RUN_R17)
    # round17-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s64-cal-r17] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 6、弃权 31）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s64-cal-r17] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s64-cal-r17] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s64-cal-r17] zero_flag_parts: "
          f"{[(z['instance'], z['state']) for z in run['reader']['zero_flag_parts']['parts']]}"
          f"（prep1-bottom-i1/i2 两派次零旗）")
    print(f"[s64-cal-r17] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}")
    print(f"[s64-cal-r17] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s64-cal-r17] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    m = hyp["measurement"]
    print(f"[s64-cal-r17] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；三分判据=M1 top 全旗聚合弃权率 "
          f"{m['top_abstain_count_r17']}/{m['top_abstain_flags_r17']}"
          f"={m['top_abstain_rate_r17']}；(a) 支 supported ≤0.671429（r16 "
          f"零变更基线双侧复算 {m['top_abstain_rate_r16_baseline_live']}"
          f"={m['top_abstain_rate_r16_baseline_value']}，绝对降幅 ≥0.10）"
          f"→crit_a={m['crit_a_supported_le_0.671429']}；(b) 支 reject "
          f"≥0.771429（=r16 基线水平）→crit_b="
          f"{m['crit_b_reject_ge_0.771429']}；落支={m['letter_branch']}"
          f"；守门 G1={m['guard_channel']['g1_ok']}/G2="
          f"{m['guard_channel']['g2_guard_ok']}（early_stop 触发="
          f"{m['guard_channel']['guards_ok'] is not True}）；机制观察单列）")
    print(f"[s64-cal-r17] 侧观察（M2 bottom 维持性，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r17']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r17']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r17']}"
          f" vs r16 基线 12/14=0.857143（{m['bottom_side_observation']['bottom_rate_direction_vs_r16']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r17']}"
          f"/courtyard 旗总数={m['bottom_side_observation']['bottom_courtyard_flags_total_r17']}")
    mo = hyp["mechanism_observation"]
    print(f"[s64-cal-r17] 机制观察要点：呈现尺寸自述 px 计数="
          f"{mo['presentation_size_mechanism_observation']['counts']['dispatches_with_px_size_self_report']}/12"
          f"（约 1000px×3+1500px×1，仪器像素界 4009/4010）＋清晰度自述 "
          f"12/12；top 弃权分型="
          f"{mo['top_abstain_typology']['type_counts']}；黑点族 M3 "
          f"{mo['black_dot_tracking']['by_instance']}（8 旗全弃权 vs "
          f"r16=12）；1280 新细节旗 {mo['top_new_detail_flags_1280']['counts']}"
          f"（椭圆截断带非弃权+半填充圆形/QFP 间断/引脚排差异）；"
          f"reroute 1 旗全弃权（子串零命中）")
    print(f"[s64-cal-r17] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s64-cal-r17] channel_attribution: "
          f"geo R16={len(ca['channel_1_geometry_gate']['r16_area_ratio_rejected_entries'])}"
          f"→R17={len(ca['channel_1_geometry_gate']['r17_area_ratio_rejected_entries'])}, "
          f"cat R16={len(ca['channel_2_category_gate']['r16_category_mismatch_entries'])}"
          f"→R17={len(ca['channel_2_category_gate']['r17_category_mismatch_entries'])}")
    print(f"[s64-cal-r17] commit: run={run_status}（round17-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s64-cal-r17] sha256[:8] calibration-run-r17.json = "
          f"{run_sha[:8]}")
    print("[s64-cal-r17] R17 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
