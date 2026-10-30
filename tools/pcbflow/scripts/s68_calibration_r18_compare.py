#!/usr/bin/env python
"""CAL-R18-CLOSE：reader 判读迭代第十八轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s64_calibration_r17_compare.py 同构，仅输入与轮次
常量不同；R18=development 域轴2 指引侧单变量轮（axis-experiment-plan-
r17-r20 stage1 R18=A2_blackdot_instrument_annotation：渲染零变更=
renders-r14b 四图字节复用（与 r14/r15/r16/r17 盲读同一批文件、四 PNG
sha=witness-r14b 登记值 fail-closed 比对一致）；判读指引=
observation-guidance-r18.md（cadcb8f3，由 r15 指引机械变换生成、
本轮唯一判读依据；§2–§7 判据逐字承 r15（含 §5A 原文逐字保留）、
唯一实质变更=新增 §5B 黑点仪器注记节（blackdot-probe-r18.json
section_5b_text 探针证实事实的中性转录、仪器事实非判据））；
GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed=false
已预注册）——唯一操纵因子=指引侧 §5B 黑点中性仪器注记；检验
r18-prep-record.json 预注册假设（hypothesis_id=axis-plan-r18-blackdot-
note，判据=r18-prep-record.json hypothesis_test.adjudication 三分判据
预注册原文，脚本从 prep-record 文件加载判据文本、基线数字 live 重放
不手工抄数）：「黑点族弃权（连续 4 轮主导）的主因=黑点物理性质不明
导致的存在性弃权；§5B 中性仪器注记使读者能按既有判据负责任判定黑点
相关现象，黑点族弃权显著回落，且不引起其他族弃权上升」：

  T1  解析 12 个 reader-raw-r18-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r18-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r16/r17 同一比较脚本血统；聚合口径零
      改动）：(1) 实例主记录=六实例各自两板合计 flag_count/abstain_
      count/abstain_rate（6 位小数；零旗标分母=None）/非弃权清单
      （r18 实测 flag_id 两板各自从头编号——非弃权/弃权清单按
      (state, flag_id) 限定，跨板重号如实登记；与 prep-record naming
      「同实例跨板连续」声明不同=读者实例输出行为差异、如实入账不作
      废，与 r15/r16/r17 实测同形态）/逐旗 containment+area_ratio 匹配
      明细；(2) 视角层=每视角 3 实例 flag_count/abstain_rate/matches 各
      中位数+min+max 三分列不取整（本轮 12 格全部≥1 旗、实例层与
      派次层弃权率全部有定义）；(3) GT 匹配双口径=union（≥1 实例命中）
      与 agreement（≥2/3）并列+逐 GT 条目 matched_by_count（0..3；召回
      分母=GT 13 条）；(4) 联合门（APR-0011 阈值零改动）=代表配置（每
      视角 flag_count 中位数实例）算一轮 joint+per-metric 实例间范围+
      逐实例原始记录三者并列不挑优；(5) bottom 零旗标分母=按库侧
      cal._ratio 先例 None+文字说明（本轮零旗标格=0、口径在案备用）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且本轮渲染零变更
      （renders-r14b 字节复用=GT 重投影输入未变），frame_box_pct_r5
      =GT 框在渲染图像空间的归一化坐标口径、随 r14 顶层更换先例沿用
      （r14 先例：renders-r5→r14b 顶层更换时重投影台账沿用不重派生），
      本轮零新派生；bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（三分判据，r18-prep-record.json hypothesis_test.
      adjudication 原文）逐支执行：主度量=M3（黑点族弃权旗数，分型件
      rubric 口径；脚本从 abstain-typology-r13-r16.json 装载 rubric
      五类定义+关键词表+优先级（blackdot 对象判定先于 contact 组合），
      先对 r13–r16 四轮 132 条弃权旗做机械重放对拍（逐旗 family 与
      分型件在案记录逐一相等=口径忠实性证明），再同法套用 r18 全部
      弃权旗逐旗分类入账）——supported=(s) M3 ≤6（=r16 基线 12 的一
      半；基线=分型件 r16 实测装载交叉核对）且 G1/G2 维持且 M1
      ≤0.85（M1=top 全旗聚合弃权率 12 派次全口径；r16 基线 27/35=
      0.771429 双侧复算 live 重放交叉核对一致）；reject=(r) M3 ≥10
      （注记未使黑点族回落）或 G1/G2 任一破坏→按 axis-plan
      early_stop_rule 出局、转向轴3/组合轮；marginal=(m) M3 7–9
      （回落未过半）或 M1 0.85–0.862（带上缘=r15 在案 0.862069，
      记录为部分收益）。判据比较用 6 位定点整数交叉相乘（避免浮点）；
      支序=reject→supported→marginal（判据字面互斥性由脚本自检，
      未覆盖组合即中止）。letter 裁决唯一正式；守门 G1/G2 独立单列
      （G1=bottom courtyard 非弃权 0/0/0 维持、G2=guard_ok=True 维持；
      任一破坏→reject 支成立+轴2 按 plan early_stop_rule 出局）；机制
      观察单列（mechanism_observation_separate 原文口径）：黑点旗逐条
      理由对照注记援引情况（location_evidence/reading_notes 是否援引
      §5B——逐旗逐件摘录）；黑点判正常派次计数（notes 判正常不入旗，
      按分型件 blackdot_dispatch 口径计数，对照 r15=3/r16=2）；黑点转
      非弃权旗计数（逐条摘录：applied-bottom-i2 2 条 other_advisory
      非弃权黑点旗+prep1-top-i3 1 条）；M2=bottom 全旗聚合弃权率
      （对照 r16 基线 12/14=0.857143 live 复算）；M4=top 逐实例弃权率
      极差；(M1,M2,M3,M4) 四元组入实验对照账字段（照 axis-plan
      benefit_metrics 口径，四元组随 run 在案、由 dev-record 包转记）；
      top 弃权分型照常；bottom courtyard 非弃权 0/0/0 与 courtyard 旗
      计数（对照 r17 的 5 非弃权+7 弃权）。
      → calibration-run-r18.json。
  T3  development 域记录（R17→R18 方向性对照/假设裁决/联合评价趋势/
      下一迭代目标=轴3/组合轮转向）由后续 dev-record 包落盘（round18-
      dev-record，另包执行）；本包仅产出 run-r18、零 dev-record 写入。

通道归因纪律（vs R17；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/
s55/s58/s64 deviation_note 口径）：本轮对 R15/R16/R17 均以内嵌输入
（reader_flags/gt_entries/flag_views，run sha 在案）+ compare_v3 同源
几何原语（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R18 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「未读取盘上任何其他文件」（12/12 在案）；
prep1-top-i1 另自述「判据仅来自 observation-guidance-r18.md」、
applied-bottom-i3 另自述「bottom 视不做镜像换算」（与指引口径一致的
坐标自述）；§5B 显式援引 1/12 派次（applied-top-i1 notes「§5B 为仪器
事实注记，本判读仍按 §4 判据独立执行，结论与注记来源一致」=判正常
路径援引、非旗标路径援引）；跨轮实例全重抽+轮内实例差异=混杂因素
照旧声明——本轮唯一操纵因子=指引 §5B 注记（渲染零变更=renders-r14b
字节复用，仪器侧零变动；实例群重抽为轮际比较的固有混杂、per
axis-plan comparison_rule.drift_confound_note 显式容忍）。
输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件
=缩进格式冻结原始判读件、本轮零改动直读（direct JSON 解析、12 件
parse 校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round18-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量 2026-09-09
/ 2026-09-09-r18）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s68_calibration_r18_compare.py   （仓库根执行）
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"

DECLARED_DATE = "2026-09-09"
ROUND_ID = "2026-09-09-r18"
ROUND_LABEL = "r18"
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
REL_PREP_R18 = "out/v3-tl2/calibration/r18-prep-record.json"
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
REL_DEV_R17 = "out/v3-tl2/calibration/round17-dev-record.json"
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
REL_RUN_R17 = "out/v3-tl2/calibration/calibration-run-r17.json"
REL_FRAMING_R14B = "out/v3-tl2/calibration/render-framing-r14b.json"
REL_WITNESS_R14B = "out/v3-tl2/calibration/render-witness-r14b.json"
REL_PROBE_R18 = "out/v3-tl2/calibration/blackdot-probe-r18.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_GUIDANCE_R18 = "out/v3-tl2/calibration/observation-guidance-r18.md"
#: 本包唯一新建输出（防覆写护栏语义照 s64；不在 FROZEN_SHA256 锚集）。
REL_RUN_R18 = "out/v3-tl2/calibration/calibration-run-r18.json"

#: 12 份盲读原始件（6 实例×2 板；r18 实测 flag_id 两板各自从头编号，
#: 全部 12 格≥1 旗、零旗标格=0）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r18-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r18-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r18-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r18-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r18-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r18-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r18-prep1-bottom-i3.txt",
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

#: R18 渲染：图像来源=renders-r14b 四图字节复用（渲染零变更；与
#: r14/r15/r16/r17 盲读同一批文件；四 PNG 盘上 sha=witness-r14b
#: 登记值=prep-record instrument_change.renders 登记值，bottom 两板
#: 逐字节同 d7284259；top 两图=renders-r5 逐字节复用 298bc620/
#: b2f84524）。
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
#: 四 PNG 锚=renders-r14b 四图（字节复用；盘上 sha=witness-r14b 登记
#: 值=prep-record instrument_change.renders 登记值，脚本 fail-closed
#: 三方比对）；四 PDF 锚=r5 在案锚沿用（输入侧 PDF 未变）；
#: guidance-r18 锚=本轮唯一判读依据（r15 指引机械变换产物；
#: guidance-r15 锚=其变换基座 d5babc93；两条锚均在案）；
#: prep-r18 锚=本轮预注册件（其 chain_anchors 内嵌 axis-plan/witness-
#: r14b/dev-r16/dev-r17/run-r16/probe/typology 锚，脚本加载后与盘上
#: 实测逐一交叉核对）；run-r16 锚=M1 基线（27/35=0.771429）与 G1/G2
#: 守门基线的双侧复算输入（run sha 在案）；run-r17 锚=通道归因对照轮
#: 输入（r17 重放与在案登记交叉核对）；probe 锚=§5B 文本唯一转录源；
#: typology 锚=rubric/黑点族基线唯一装载源；其余沿用 s64 在案锚。
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
    REL_GUIDANCE_R18:
        "cadcb8f33afd0e8d12a022aa34d164de466b66ad37bd836659c2e78523315fc0",
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
    REL_PREP_R18:
        "3fc054c4d30ce770688440a4b7c465583e2ed34b76fbf53f3b3c59a43f2f5b4a",
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
    REL_DEV_R17:
        "e526093fe33ab28cc18ec45c0b1d0c7f671030fe0d70f1622519eac0c11bd5b7",
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
    REL_RUN_R17:
        "d444c4a53dbff6c2cc3b2a882a0e39024f9d38672144b919dfbd6d58957667fe",
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    REL_PROBE_R18:
        "a49441acacd7ac492960b7e604d1e31a37174e9d9a97b4a24ebddc2e3551111d",
    REL_TYPOLOGY:
        "6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b53283681bc80",
    RAW_FILES["applied-top-i1"]:
        "a7e0f20f02a064df955cce14ef760d0f956332ff101fd2d9c793b0bb68aa160a",
    RAW_FILES["prep1-top-i1"]:
        "c92ca022ebd38392fce5f5c9d015ac5d49618135fc6c937498c6aac7394c2584",
    RAW_FILES["applied-top-i2"]:
        "bc1fea5d2da07a67136f8cf4d029638f97232d53739919adc806de6f1cda41c2",
    RAW_FILES["prep1-top-i2"]:
        "427fa57efa8255217f2a70d9c2b576f8c7cc098fda5099d3b27e48847d9e098e",
    RAW_FILES["applied-top-i3"]:
        "7a0c6e4055b912e255f05a215107da006fef9c5c6e13d6d1b1bf06903f0fef02",
    RAW_FILES["prep1-top-i3"]:
        "9abe655581e10cd7ef759fc08a3968959ce55f6b5381d3a62e48ba76ea3d4e49",
    RAW_FILES["applied-bottom-i1"]:
        "b8ab3f38738377eeecb83eda94d9fa38d2a56b9789db16846fdd11abeaa60903",
    RAW_FILES["prep1-bottom-i1"]:
        "691d1c06fd5d5128e7ee0f428732274c1178b2ec01073b1beff5fa6bb45cc95a",
    RAW_FILES["applied-bottom-i2"]:
        "dbb9c946406d9a9dcda238a6d59515c370fa47b46c957bde38623f128189f916",
    RAW_FILES["prep1-bottom-i2"]:
        "590ca377b6e456db0aab6761a0341170d788be38f800177667c1660deb5fc43b",
    RAW_FILES["applied-bottom-i3"]:
        "36d2824c44245a8b53ec1b179a84b1f45bcad858299b1ac4334155752634cda2",
    RAW_FILES["prep1-bottom-i3"]:
        "351b1a264cccf5d441241972da4baf7ecc13567ae39232956093e09266f13225",
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
    "盲读词只含图像路径（renders-r14b 四张字节复用=渲染零变更、与 "
    "r14/r15/r16/r17 盲读同一批文件）+observation-guidance-r18.md"
    "（cadcb8f3，r15 指引机械变换产物+§5B 黑点仪器注记新节、本轮唯一"
    "判读依据；旗 ID 前缀 "
    "R18T-/R18B- 随指引 §6 落盘固化——本轮指引本体即为 r18 前缀、"
    "无需派发层覆盖，per r18-prep-record protocol_amendment.naming；"
    "reader-r18-{top,bottom}-i{1,2,3} 为派发指令命名）+起始序号+v1.2 "
    "工具行为规约"
    "硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/衍生图像"
    "生成等）；判读只允许以 Read 工具查看原图（同一原图可重复查看））；"
    "无任何 GT 坐标/类别提示/期望缺陷描述、零诊断报告内容（黑点探针链"
    "（blackdot-probe-r18.json）与 framing/witness 记录不进任何 reader "
    "上下文）、"
    "零 legend/零其他解释"
    "（判读输入=指引+单张 PNG+派发指令，与既往轮同构，仅指引件更换）；"
    "读图者不接触 GT/派生台账/任何校准"
    "产物路径；跨实例/跨视角禁止交流（12 次盲读相互独立——独立性是"
    "多实例协议的前提，亦为轴2 收益裁决有效性的前提，per r18-prep-"
    "record read_prohibition_note）")

#: 派发模式结构化记录（R18=轴2 指引侧单变量轮：每格 3 实例、两波次
#: 串行保序；派发结构与 r17 同构，协议侧零新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R18T-001..007；prep1 R18T-001..007",
        "top-i2": "applied R18T-001..006；prep1 R18T-001..002",
        "top-i3": "applied R18T-001..005；prep1 R18T-001..004",
        "bottom-i1": "applied R18B-001..003；prep1 R18B-001..003",
        "bottom-i2": "applied R18B-001..004；prep1 R18B-001..002",
        "bottom-i3": "applied R18B-001..003；prep1 R18B-001..004",
    },
    "flag_id_continuity_note": (
        "r18 实测=flag_id 两板各自从头编号（同一实例 applied 与 prep1 "
        "派次内各自独立起编；跨板同号如实登记）——与 r15/r16/r17 实测同"
        "形态；与 r18-prep-record protocol_amendment.naming「同实例"
        "跨板连续」的声明不同，属读者实例输出行为差异、如实入账不作废"
        "（非盲读违规、不作废任何产物）；编排"
        "侧因此把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R17→R18 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮单变量="
                  "指引侧 §5B 黑点中性仪器注记（渲染零变更=renders-r14b "
                  "四图字节复用；指引=observation-guidance-r18.md"
                  " 机械变换产物、§2–§7 判据逐字承 r15（含 §5A 原文逐字"
                  "保留），仅轮次标识同步+本轮变更声明重写+§5B 新节插入"
                  "）；实例群"
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
    "读者实例披露（如实入账，不作废）：R18 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何其他文件」"
    "（12/12 逐字摘录在案 reader_tool_evidence）；prep1-top-i1 另自述"
    "「判据仅来自 observation-guidance-r18.md」、applied-bottom-i3 另"
    "自述「坐标按整幅图像空间给出（bottom 视不做镜像换算）」（与指引 "
    "bottom 判读口径一致的自述）；§5B 显式援引=1/12 派次（applied-top-i1 "
    "notes「§5B 为仪器事实注记，本判读仍按 §4 判据独立执行，结论与注记"
    "来源一致」=判正常路径援引、非弃权旗路径援引，见 "
    "black_dot_tracking.fiveb_citation_observation 逐件摘录）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/零探针"
    "件/零 legend/零其他文件接触=非盲读违规；本轮唯一操纵因子=指引 §5B "
    "黑点中性仪器注记（渲染零变更=renders-r14b 四图字节复用、仪器侧"
    "零变动；实例群全部重抽为轮际比较固有混杂，per axis-plan "
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
    "本轮指引=observation-guidance-r18.md（cadcb8f3，由 r15 指引 "
    "d5babc93 机械变换生成、本轮唯一判读依据，per r18-prep-record "
    "guidance_reuse：mode=mechanical_transform_derive、edit_list 8 项"
    "逐字登记、§2–§7 分段逐字保留断言复核在案）：§2 类别枚举/§3 位置"
    "口径/§3A 示例（含示例 c）/§4 置信度与弃权（含量化判据 (i)(ii)(iii)、"
    "接触性判据、三路出口、反放宽条款）/§5/§5A（r15 原文整体逐字保留）"
    "/§6/§7 判据文本逐字承 r15；变更=轮次标识机械同步（标题/声明日期 "
    "2026-09-09/round_id_constant "
    "2026-09-09-r18/本轮性质行/示例 reader_id/示例旗 ID 前缀）+本轮变更"
    "声明节重写+§5B 黑点仪器注记新节插入（「## 6. 输出格式」标题前；"
    "文本=blackdot-probe-r18.json section_5b_text 逐字转录、探针证实"
    "事实的中性转录）；§5B=仪器事实注记、"
    "非判据——不构成任何「应判正常/无需报告」的指示，不降低任何存在性、"
    "归类、定位或报告的责任门槛（per r18-prep-record no_loosening_note；"
    "反指示声明/判定独立性/未证实形态按 §4 既有规则处理/top 适用句随 "
    "§5B 落盘；反放宽条款与三路出口随指引本体原样生效）——仪器事实补充、"
    "判断责任标准一字未松；§6 示例旗 ID 前缀 R18T-/R18B- 随指引落盘"
    "固化（r13→r15「随指引落盘固化」路径回归，无需派发层覆盖）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 18 轮迭代"
    "（development 域轴2 指引侧单变量轮（黑点中性仪器注记，渲染零变更"
    "字节复用）：迭代轮不得冒充留出证据；执行 axis-experiment-plan-"
    "r17-r20（b6ec6467 冻结件）stage1 R18，用户 2026-09-09「三条轴"
    "单独/组合/全组合尝试，选择收益最大的继续」（user_directive_note "
    "在案））。")

INSTRUMENT_NATURE = (
    "轴2 指引侧单变量轮（渲染零变更轮）：仪器变更=无（renders-r14b 四图"
    "字节复用=与 r14/r15/r16/r17 盲读同一批文件；四 PNG 盘上 sha="
    "witness-r14b 登记值=prep-record instrument_change.renders 登记值 "
    "fail-closed 三方一致；instrument_change.changed=false 已预注册，"
    "no_instrument_change=true）+判读指引=observation-guidance-r18.md"
    "（cadcb8f3，r15 指引机械变换产物、§2–§7 判据逐字承 r15（含 §5A "
    "原文逐字保留），唯一实质变更=新增 §5B 黑点仪器注记节（探针证实"
    "事实的中性转录、仪器事实非判据））+GT/阈值零变更（13 条冻结；"
    "APR-0011 与 CONTAINMENT_MIN/AREA_RATIO_MAX 只作口径引用）+协议零"
    "变更（v1.1+v1.2 维持）：唯一实验变量=指引 §5B 注记（per r18-prep-"
    "record manipulated_factor；axis_id=A2_blackdot_instrument_annotation；"
    "changed_variables 两条 instrument_change 均=false）")

#: 预注册主通道三分判据所用基线（零覆盖；per r18-prep-record
#: hypothesis_test.adjudication 原文：supported=M3 ≤6（r16 基线 12 的
#: 一半）且 G1/G2 维持且 M1 ≤0.85；reject=M3 ≥10 或 G1/G2 任一破坏；
#: marginal=M3 7–9 或 M1 0.85–0.862（带上缘=r15 在案 0.862069））。
#: 基线数字 live 重放/装载（M1/M2=同一聚合逻辑对 run-r16 内嵌实例记录
#: 双侧复算、不手工抄数；M3=分型件 r16 实测装载交叉核对）并与下列在案
#: 登记值交叉核对（fail-closed，不符即中止）：
#: (27,35)=0.771429（r18-prep-record chain_anchors.run_r16_baseline_
#: anchor.frozen_values 与 axis-plan baselines_registered.r16_baseline
#: 双锚在案）。
BASE16_TOP_AGGREGATE_REGISTERED = {"abstain": 27, "flags": 35}
#: M1 侧阈值（6 位定点整数交叉相乘比较，避免浮点）：supported 门
#: M1 ≤0.85；marginal 带 M1 0.85–0.862（带上缘=r15_reference 在案
#: 0.862069 的三位小数引用 0.862；判据原文措辞「0.85–0.862」）。
SUPPORTED_M1_THRESHOLD_6DP = 850000
MARGINAL_M1_UPPER_6DP = 862000
#: M3 侧阈值（主度量；黑点族弃权旗数，分型件 rubric 口径）：
#: supported ≤6、marginal 7–9、reject ≥10。
SUPPORTED_M3_MAX = 6
MARGINAL_M3_MIN = 7
MARGINAL_M3_MAX = 9
REJECT_M3_MIN = 10
#: bottom 侧观察基线（M2；per axis-plan baselines_registered.r16_baseline
#: .M2_bottom_aggregate_abstain_rate=0.857143；live 重放交叉核对
#: 12/14）。
BASE16_BOTTOM_AGGREGATE_REGISTERED = {"abstain": 12, "flags": 14}
#: M3/M4 基线登记值（axis-plan baselines_registered.r16_baseline 在案；
#: M3=分型件 rubric 口径黑点族弃权旗数（分型件 r16 实测装载交叉核对
#: 见 rubric 重放节）、M4=top 逐实例弃权率极差；
#: 脚本对 axis-plan 原文 fail-closed 装载核对，另对 run-r16 live 重放
#: 交叉核对 M4 的逐实例构成）。
AXIS_R16_M3_BLACKDOT_RUBRIC = 12
AXIS_R16_M4_TOP_RANGE = 0.261904
R16_TOP_INSTANCE_RATES_REGISTERED = {"top-i1": 0.666667,
                                     "top-i2": 0.928571,
                                     "top-i3": 0.666667}
R16_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}
#: 黑点族链基线（分型件 rubric 口径在案：r13=9、r14=14、r15=8、r16=12；
#: r18-prep-record chain_anchors.typology_blackdot_baseline 与分型件
#: matrix/round_totals 双向核对；本件只登记基线与 r18 实测对照）。
BLACKDOT_CHAIN_PRIOR = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
#: 黑点判正常派次链基线（分型件 blackdot_dispatch.judged_normal_
#: dispatches 口径：r15=3、r16=2；黑点判正常派次=notes 判正常不入旗
#: 的派次）。
BLACKDOT_JUDGED_NORMAL_PRIOR = {"r15": 3, "r16": 2}

#: bottom 侧观察（G1 守门）逐实例登记表（bottom courtyard 类非弃权
#: 旗；程序实测与登记一致性 fail-closed：实测值须与本表 expected 逐一
#: 相等；per r18-prep-record guard_channel「G1=bottom courtyard 非弃权
#: 0/0/0 维持（对照 r15/r16 在案 0/0/0）」；守门独立单列、不影响字母）。
SIDE_OBS_REGISTERED = [
    {"instance": "bottom-i1", "expected": 0,
     "note": ("r16/r17 零非弃权 courtyard→r18 实测 0：本轮 bottom-i1 "
              "零 courtyard 类旗标（6 旗=other_advisory 4（黑点 4）+"
              "placement 2；弃权 5；applied 3 旗+prep1 3 旗）——零 "
              "courtyard 类路径")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r16/r17 零非弃权 courtyard→r18 实测 0：本轮 bottom-i2 "
              "零 courtyard 类旗标（6 旗=other_advisory 4（黑点 4）+"
              "placement 2；弃权 2；applied 4 旗+prep1 2 旗）——零 "
              "courtyard 类路径")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r16 零非弃权 courtyard、r17 零非弃权（1 弃权）→r18 "
              "实测 0：本轮 bottom-i3 零 courtyard 类旗标（7 旗="
              "other_advisory 6（黑点 4+双椭圆焊盘对 2）+placement 1；"
              "弃权 6；applied 3 旗+prep1 4 旗）——r17 的 prep1-bottom-i3 "
              "R17B-001 courtyard 弃权旗在本轮未再现")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。prep1-top-i1 另自述判据来源、
#: applied-bottom-i3 另自述坐标口径，如实登记。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据给定 PNG（prep1-top.png）可见内容逐区域独立判读，未读取盘上任何其他文件；判据仅来自 observation-guidance-r18.md"},
    {"source": "applied-top-i2",
     "excerpt": "仅依据给定 PNG（applied-top.png，top 视）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i2",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据给定PNG可见内容逐区域独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG 的可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG 的可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG（prep1-bottom.png）可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件；坐标按整幅图像空间给出（bottom 视不做镜像换算）"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——绿色翼瓣/
#: 空隙形态在 r18 指引（§2–§7 逐字承 r15）下延续 §4(i) 判读路径的
#: 机制观察证据（5/6 bottom 派次；applied-bottom-i3 为 §5A 非图元
#: 路径、无 §4(i) 自述，如实分列）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "边缘阵列间绿色连接状图形、阵列端头方形焊盘及阵列内焊盘密集近邻均沿多条边/阵列系统性重复且形态一致，按 §4 系统性判据判为正常设计特征未报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "四边焊盘阵列间与焊盘周围的绿色翼瓣空隙、间隙环及板框退让带呈系统性重复（多处、沿同一阵列、跨多条边、形态一致），按 §4 量化判据 (i) 判为正常设计特征，三路出口路径（1）不予报告"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "以下可见形态按 §4 系统性正常特征判据判为正常设计特征、未报告：周边四边焊盘阵列的等节距近邻排布、焊盘间绿色空隙翼瓣的周期性出现及相邻贯通、四边阵列端部的方形键焊盘（4 处、跨多边、形态一致）、四边阵列相对板框呈一致性切向偏移（四面偏移方向构成一致的旋转式格局、形态逐处一致）"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "以下系统性特征按 §4(i) 量化判据与三路出口判为正常设计特征、未报告：阵列端部的方形焊盘（≥3 处、跨多条边、形态尺寸一致，合极性/1 脚标记类常规解释）、部分焊盘旁成周期分布且形态一致的绿色翼瓣形空隙、左上角两组彼此一致的「椭圆焊盘+小椭圆槽+黑点」组件图形、板内孤立的圆+方焊盘对"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "周边四侧双排焊盘阵列的间距、尺寸与样式系统性一致（满足 §4(i) 量化判据），相邻单元轮廓贴近属单元接近的联合外观，判为正常设计特征，按三路出口第(1)路不报告"},
]

#: top 弃权理由构成分型（机制观察：20 条 top 弃权旗逐旗按
#: location_evidence 关键词分类——contact=接触性「真实接触 vs 视觉
#: 贴近不可分辨/是否接触不可确认」（含读者自述「按接触性判据弃权」
#: 主出口）；existence=存在性「性质不明/是否存在不可确认」；
#: other_layer=层归属等其他出口；为 M1 未过 supported 门（0.645161
#: 已 ≤0.85）与 M3 reject 支的归因分解提供分型。逐旗 excerpt 逐字
#: substring fail-closed 校验+覆盖完整性校验；本分型（s64 口径）与
#: rubric 逐旗族分类（existence_blackdot 先行+文本主因抑制 contact）
#: 为两套登记口径、分别如实入账）。
TOP_ABSTAIN_TYPOLOGY = [
    {"source": "applied-top-i1", "flag_id": "R18T-002", "type": "existence",
     "excerpt": "无法确认其是否超出常规换向折弯的可疑形态，存在性无法负责任确认"},
    {"source": "applied-top-i1", "flag_id": "R18T-003", "type": "existence",
     "excerpt": "但分辨率下无法确认其真实形态，存在性不确定"},
    {"source": "applied-top-i1", "flag_id": "R18T-004", "type": "contact",
     "excerpt": "按接触性判据无法区分真实接触与视觉贴近，存在性不确定"},
    {"source": "applied-top-i1", "flag_id": "R18T-005", "type": "contact",
     "excerpt": "courtyard 轮廓线不可分辨，无法区分重叠、接触与合规近邻"},
    {"source": "applied-top-i1", "flag_id": "R18T-006", "type": "contact",
     "excerpt": "无法负责任确认是否重叠或接触"},
    {"source": "applied-top-i1", "flag_id": "R18T-007", "type": "existence",
     "excerpt": "疑有文字压焊盘，但分辨率下无法确认文字笔画确被图形覆盖致不可辨读"},
    {"source": "prep1-top-i1", "flag_id": "R18T-002", "type": "contact",
     "excerpt": "当前分辨率无法区分真实接触与视觉贴近，按接触性判据弃权"},
    {"source": "prep1-top-i1", "flag_id": "R18T-003", "type": "existence",
     "excerpt": "无法负责任判定其是否构成关注现象，故弃权",
     "note": "黑点对象旗（存在性出口；rubric 族=existence_blackdot）"},
    {"source": "prep1-top-i1", "flag_id": "R18T-005", "type": "existence",
     "excerpt": "当前分辨率无法确认该叠压形态是否真实存在"},
    {"source": "applied-top-i2", "flag_id": "R18T-004", "type": "existence",
     "excerpt": "未达系统性正常特征判据，而该形态又不与任何可见图形冲突、无法负责任确认其构成何种关注现象，存在性判断不定",
     "note": "黑点对象旗（存在性出口；rubric 族=existence_blackdot）"},
    {"source": "applied-top-i2", "flag_id": "R18T-005", "type": "existence",
     "excerpt": "当前分辨率下无法确认叠压是否真实存在、文字是否达到无法辨读的程度"},
    {"source": "prep1-top-i2", "flag_id": "R18T-001", "type": "contact",
     "excerpt": "当前分辨率下无法区分真实连印（笔画相接）与小于分辨率的极小间距，字形内容也无法完全确认，按接触性判据弃权",
     "note": "文本域连印接触性表述、读者自述主出口=接触性判据；rubric 族分类因文本主因抑制 contact 归 existence_other（两口径分列如实）"},
    {"source": "prep1-top-i2", "flag_id": "R18T-002", "type": "existence",
     "excerpt": "当前分辨率下无法确认具体遮挡程度与被遮挡文字内容"},
    {"source": "applied-top-i3", "flag_id": "R18T-001", "type": "existence",
     "excerpt": "按存在性量化判据不满足系统性正常特征，又无法负责任归入六类中任一关注类（归属哪类不能负责任确定）",
     "note": "黑点对象旗（存在性出口；rubric 族=existence_blackdot）"},
    {"source": "applied-top-i3", "flag_id": "R18T-003", "type": "contact",
     "excerpt": "当前分辨率下依接触性判据无法区分真实接触与视觉贴近"},
    {"source": "applied-top-i3", "flag_id": "R18T-004", "type": "existence",
     "excerpt": "当前分辨率无法确认文字笔画确实相互叠压或截断到无法辨读"},
    {"source": "applied-top-i3", "flag_id": "R18T-005", "type": "existence",
     "excerpt": "当前分辨率无法负责任确认文字相互叠压致无法辨读"},
    {"source": "prep1-top-i3", "flag_id": "R18T-002", "type": "contact",
     "excerpt": "当前分辨率下无法区分真实交叠与视觉贴近，按接触性判据属存在性不确定"},
    {"source": "prep1-top-i3", "flag_id": "R18T-003", "type": "existence",
     "excerpt": "无法负责任确认该填充是覆盖焊盘的关注现象还是有意的封装图形（如极性/方向标记类），归属不明"},
    {"source": "prep1-top-i3", "flag_id": "R18T-004", "type": "contact",
     "excerpt": "当前分辨率下无法确认该横带是否真实接触引脚（也可能为细间距引脚并排的视觉合并），按接触性判据弃权"},
]

#: 绿色区域语义化方式证据（r17 机制观察延续：bottom 派次 notes 逐字
#: 摘录；substring fail-closed 校验；对照 r16 六派次全部空隙语义化+
#: 6 派次 §5A 显式援引、r17 的 6/6 语义化+2/6 援引——r18 实测 5/6
#: 派次仍以「空隙/翼瓣」语义化绿色（§4(i) 判读路径延续；
#: prep1-bottom-i3 notes 无绿色语义化自述、如实空缺），§5A 显式援引
#: =1/6（applied-bottom-i3 notes），如实分列）。
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "边缘阵列间绿色连接状图形、阵列端头方形焊盘及阵列内焊盘密集近邻均沿多条边/阵列系统性重复且形态一致，按 §4 系统性判据判为正常设计特征未报告",
     "cites_5A": False},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "四边焊盘阵列间与焊盘周围的绿色翼瓣空隙、间隙环及板框退让带呈系统性重复（多处、沿同一阵列、跨多条边、形态一致）",
     "cites_5A": False},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "焊盘间绿色空隙翼瓣的周期性出现及相邻贯通",
     "cites_5A": False},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "部分焊盘旁成周期分布且形态一致的绿色翼瓣形空隙",
     "cites_5A": False},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "全部绿色区域按 §5A 仪器注记视为非图元（非丝印/阻焊开窗/courtyard 图形），未据此报旗",
     "cites_5A": True},
]

#: 黑点族现象证据（r18 黑点族弃权旗 13 条全弃权+2 派次 notes 判正常
#: 未报告+3 条黑点转非弃权报告旗的代表摘录；kind=reading_notes 或
#: location_evidence；substring fail-closed 校验；延续 r14–r17 黑点族
#: 追踪——r18 黑点族=13 旗（分型件 rubric 口径）vs r16=12/r17=8，
#: 数量回升、方向性描述）。
BLACK_DOT_EVIDENCE = [
    {"source": "prep1-top-i1", "kind": "location_evidence",
     "flag_id": "R18T-003", "instance": "top-i1", "disposition": "弃权",
     "excerpt": "右上块内一对孤立实心黑点（仅 2 处、单一位置）"},
    {"source": "applied-top-i2", "kind": "location_evidence",
     "flag_id": "R18T-004", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上连接器块内可见两个上下相邻的孤立实心黑点"},
    {"source": "applied-top-i3", "kind": "location_evidence",
     "flag_id": "R18T-001", "instance": "top-i3", "disposition": "弃权",
     "excerpt": "右上模块封装内部见两个孤立实心黑圆点"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "一颗孤立实心黑点紧邻胶囊形焊盘下缘"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "一颗孤立实心黑点紧邻胶囊形焊盘上缘"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "小型双焊盘脚印正下方见一个孤立实心黑点"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i1", "disposition": "弃权",
     "excerpt": "另一小型双焊盘脚印正上方见第二个孤立实心黑点"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "带绿框椭圆焊盘的右下方有一处孤立实心黑点"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "另一带绿框椭圆焊盘的上方有一处孤立实心黑点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "左上第一组横排椭圆焊盘的下缘处有一孤立实心黑点"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "左上第二组横排椭圆焊盘的上缘处有一孤立实心黑点"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "长圆形焊盘下缘与一实心黑点邻接"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "实心黑点与其下方长圆形焊盘上缘邻接"},
    {"source": "applied-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "disposition": "判正常不报告",
     "excerpt": "右上连接器内成对、同尺寸、成列对齐的两处实心黑点，形态为无铜环的小钻孔样式，结合通用 PCB 域知识判为机械定位/安装孔类正常设计特征，不报告"},
    {"source": "prep1-top-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i2", "disposition": "判正常不报告",
     "excerpt": "右上成对实心黑点形态一致、成对对齐且不与任何布线/焊盘图形相互作用，结合一般 PCB 域知识判为常规机械定位孔类正常设计特征，按三路出口不报告"},
    {"source": "prep1-top-i3", "kind": "location_evidence",
     "flag_id": "R18T-001", "instance": "top-i3",
     "disposition": "非弃权报告",
     "excerpt": "右上连接器封装区内可见两个孤立实心黑色圆点（上下成对，位于该封装焊盘列左侧）"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-001", "instance": "bottom-i2",
     "disposition": "非弃权报告",
     "excerpt": "左上角上方椭圆焊盘的下缘处有一个孤立的实心黑色圆点"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-002", "instance": "bottom-i2",
     "disposition": "非弃权报告",
     "excerpt": "左上角下方椭圆焊盘的上缘处有一个孤立的实心黑色圆点"},
]

#: 黑点族弃权旗登记表（13 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定——r18 两板各自
#: 从头编号；top 3 条（i1 prep1+i2/i3 applied）+bottom 10 条
#: （i1 2+2、i2 2、i3 2+2）；分型件 rubric 口径=r18 13 vs r16 12
#: （axis-plan baselines_registered 在案 M3 基线）。
BLACK_DOT_FLAGS = [
    ("top-i1", "prep1", "R18T-003", "other_advisory"),
    ("top-i2", "applied", "R18T-004", "other_advisory"),
    ("top-i3", "applied", "R18T-001", "other_advisory"),
    ("bottom-i1", "applied", "R18B-001", "other_advisory"),
    ("bottom-i1", "applied", "R18B-002", "other_advisory"),
    ("bottom-i1", "prep1", "R18B-001", "other_advisory"),
    ("bottom-i1", "prep1", "R18B-002", "other_advisory"),
    ("bottom-i2", "prep1", "R18B-001", "other_advisory"),
    ("bottom-i2", "prep1", "R18B-002", "other_advisory"),
    ("bottom-i3", "applied", "R18B-001", "other_advisory"),
    ("bottom-i3", "applied", "R18B-002", "other_advisory"),
    ("bottom-i3", "prep1", "R18B-001", "other_advisory"),
    ("bottom-i3", "prep1", "R18B-002", "other_advisory"),
]

#: 黑点转非弃权旗登记表（3 条；rubric unit=弃权旗、非弃权旗不分型，
#: 本表为机制观察「黑点转非弃权旗计数」的登记口径（对象含黑点词的
#: 非弃权旗、逐条摘录）；applied-bottom-i2 2 条 other_advisory
#: （r14–r17 同位黑点旗全部弃权路径在本实例转为非弃权报告）+
#: prep1-top-i3 1 条（孤立+样式不一致→按关注现象归兜底类报告）。
BLACK_DOT_NON_ABSTAIN_FLAGS = [
    ("top-i3", "prep1", "R18T-001", "other_advisory"),
    ("bottom-i2", "applied", "R18B-001", "other_advisory"),
    ("bottom-i2", "applied", "R18B-002", "other_advisory"),
]

#: §5B 援引观察证据（黑点旗逐条理由对照注记援引情况；applied-top-i1
#: notes 为全 12 派次唯一显式 §5B 援引（判正常路径援引、非旗标路径
#: 援引）；substring fail-closed 校验；旗级（location_evidence 含
#: 「§5B」）预期零命中由程序实测核验）。
FIVEB_CITATION_EVIDENCE = [
    {"source": "applied-top-i1", "kind": "reading_notes",
     "context": "黑点判正常路径援引（该派次零黑点旗标）",
     "excerpt": "（§5B 为仪器事实注记，本判读仍按 §4 判据独立执行，结论与注记来源一致）"},
]

#: placement/孤立图形类旗标处置证据（逐字摘录；substring fail-closed
#: 校验）——r18 板内孤立焊盘组跨实例/跨板处置分化延续且加剧
#: （bottom-i1 applied 非弃权报告+prep1 弃权；bottom-i2 applied 双
#: 非弃权报告（含椭圆焊盘组）+prep1 notes 判正常不报告；bottom-i3
#: applied 非弃权报告+prep1 notes 判正常不报告），如实单列。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-003", "instance": "bottom-i1", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（圆焊盘带绿色瓣状轮廓+方焊盘）",
     "excerpt": "完全脱离四周边缘双排/双列阵列的规整贴边排布模式，孤立置于周边空旷的板内区域，与全板排布组织不协调"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R18B-003", "instance": "bottom-i1", "verdict": "弃权",
     "phenomenon": "板内孤立焊盘对（同位现象、跨板出口不同）",
     "excerpt": "无法负责任地确认其构成『与周边同类图形间距规律明显被打破』的放置异常，还是仅属板内常规元件脚印"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-003", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "左上角孤立椭圆焊盘组（上下两组同型）",
     "excerpt": "其椭圆形态与全板周边阵列的圆形焊盘形态明显不同，且周边无任何同类图形"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R18B-004", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘对（绿色翼瓣圆形焊盘+方形焊盘）",
     "excerpt": "与全板焊盘沿四边成阵排列的规整模式明显不协调"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R18B-003", "instance": "bottom-i3", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘对（同位现象）",
     "excerpt": "该对游离于全部行列排布体系之外，位置关系与周边规整模式明显不协调"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i2", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘对（同位现象）",
     "excerpt": "板内孤立的圆+方焊盘对——以上均为连贯封装图形，周边无受扰、无叠越、无断裂等疑似缺陷形态，未进入弃权路径"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘对（同位现象）",
     "excerpt": "板内孤立的圆形+方形焊盘对形态完好、与周边无规律冲突，无可疑形态，不报告"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed）。
REROUTE_ADJUDICATION = [
    {"source": "applied-top-i1", "flag_id": "R18T-001", "abstain": False,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("见一段水平走向的短迹线呈多次连续小幅来回"
                           "折叠的波状形态，与周边统一的 45 度直线走线"
                           "明显不协调"),
     "adjudication": "non_abstain_report",
     "note": ("非弃权报告旗（r13 以来 reroute 类首条非弃权报告）："
              "「等长|蛇形」子串零命中；location_evidence 明写「折叠"
              "仅为局部段落而非整段规则周期形态」=按 §3A 示例 c 收窄"
              "判据排除整段规则周期后按可疑改道报告")},
    {"source": "applied-top-i1", "flag_id": "R18T-002", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("板中部偏左疑似见一段多弯折短迹线，但当前"
                           "分辨率下无法确认其是否超出常规换向折弯的"
                           "可疑形态"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「存在性无法负责任确认」，按 §4 "
              "弃权")},
    {"source": "applied-top-i1", "flag_id": "R18T-003", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("右侧竖向走线带（中部 QFP 右侧与右排插之间）"
                           "疑似见一处带紧凑折弯的迹线"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法确认其真实形态，存在性"
              "不确定」，按 §4 弃权")},
]

#: reroute 类旗标产量链基线（r8–r17 在案；本轮 r18 实测=3；
#: r16=2/r17=1 经 run-reader.flag_count 在案字段 live 核对）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4, "r16": 2, "r17": 1}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1, "r16": 0, "r17": 0}


def _fail(msg: str) -> None:
    print(f"[s68-cal-r18] FAIL: {msg}")
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
    # 本轮 12 格全部≥1 旗：有旗格 view_check 必须 full（零旗格
    # view_check=not_applicable 库侧口径备用，本轮不触发）。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    # 渲染 provenance 按视角分列：本轮渲染零变更=renders-r14b 四图
    # 字节复用（与 r14/r15/r16/r17 盲读同一批文件；framing-r14b
    # single_variable_change 在案、witness-r14b 成图见证实测在案；
    # prep 零重渲染、zero-write）。top=无配色（renders-r5 逐字节
    # 复用）；bottom=r14b 配色语义。
    if "-top-" in raw_key:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "top 渲染=渲染零变更（renders-r14b/applied-top.png 298bc620 "
            "与 prep1-top.png b2f84524=renders-r5 逐字节复用、top 无配色"
            "，与既往轮次一致）；framing-r14b=7004b017 "
            "single_variable_change 在案；本轮 zero-write 零重渲染")
    else:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "bottom 渲染=渲染零变更（renders-r14b 四图字节复用、两板 "
            "bottom 成图逐字节同 d7284259；白墨图元→橙 (255,165,0)、"
            "板内空隙白→绿 (0,128,0)；成图实测橙 81672 px/绿 206632 px"
            "/板内白 0（witness-r14b palette_assertion_summary，脚本 "
            "live 装载核对）；framing-r14b=7004b017 预注册件在案；"
            "r18-prep-record bottom_view_note 在案）")
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
                     " frame_box_pct_r5（R5 仪器像素界重投影口径；r18 "
                     "渲染零变更=renders-r14b 字节复用，重投影输入未变"
                     "、随 r14 顶层更换先例沿用不重派生，本轮零新派生）；"
                     "board_box_mm/side 等其余字段与 GT 文件逐字段原样；"
                     "13 条全部 side=top"),
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
                "r18 实测 flag_id 两板各自从头编号（跨板同号如实登记；"
                "与 prep-record naming「同实例跨板连续」声明不同=读者"
                "实例输出行为差异、如实入账不作废，与 r15/r16/r17 实测同"
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
                 "三分判据（supported=M3 ≤6 且 G1/G2 维持且 M1 ≤0.85 / "
                 "marginal=M3 7–9 或 M1 0.85–0.862 / reject=M3 ≥10 或 "
                 "G 破坏）"
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
                       "r17": "not_met（在案）",
                       "r18": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
                              run_r16: dict, run_r17: dict,
                              inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R17；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R15/R16/R17 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r15_replays = replay_round_instances(run_r15)
    r16_replays = replay_round_instances(run_r16)
    r17_replays = replay_round_instances(run_r17)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R18 {key} 通道重放与 compare_v3 对拍不一致")

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
    # r15/r16/r17=fresh 重放并与在案登记逐一交叉核对，r18=本轮 fresh 重放）
    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", r16_replays, None)
    geo_r17 = pick("area_ratio_rejected", r17_replays, None)
    geo_r18 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", r16_replays, None)
    cat_r17 = pick("category_mismatch", r17_replays, None)
    cat_r18 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", r16_replays, None)
    view_r17 = pick("view_gate", r17_replays, None)
    view_r18 = pick("view_gate", inst_replays, inst_blocks)
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
    if geo_r17 != run_r17["channel_attribution"]["channel_1_geometry_gate"][
            "r17_area_ratio_rejected_entries"]:
        _fail("R17 几何门重放与 run-r17 在案登记不一致")
    if cat_r17 != run_r17["channel_attribution"]["channel_2_category_gate"][
            "r17_category_mismatch_entries"]:
        _fail("R17 类别门重放与 run-r17 在案登记不一致")
    if view_r17 != run_r17["channel_attribution"][
            "view_gate_observations"]["r17_entries"]:
        _fail("R17 视角门重放与 run-r17 在案登记不一致")

    geo_change = (
        "几何门通道（R17→R18）：面积比出局条目 %d→%d（渲染零变更轮内"
        "top 非弃权旗与同态 GT ≥0.5 containment 交叠条目的几何门计数"
        "如实登记；本轮 top 非弃权旗 11 条、几何门=%d 条；跨轮实例群漂移"
        "混杂照旧声明，只描述不断言。"
        % (len(geo_r17), len(geo_r18), len(geo_r18)))
    cat_change = (
        "类别门通道（R17→R18）：类别不符出局条目 %d→%d（r16 在案 1 条="
        "prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3（containment "
        "0.848147、面积比 1.529072），r17 重放=0 条，r18 重放=%d 条；"
        "r11 唯一原发条目 R11T-012↔GT-REVC-AP-8-R1Q2 语境下逐轮计数如实"
        "登记；跨轮实例群漂移混杂照旧声明，只描述不断言。"
        % (len(cat_r17), len(cat_r18), len(cat_r18)))

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
            "r18": len(geo_r18),
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
            "r18": len(cat_r18),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=0→r17=0→r18=%d（r14 回升未延续、r15–r18 "
                 "维持低位：top 非弃权旗与同态 GT ≥0.5 containment 交叠"
                 "条目如实计数）；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→"
                 "r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=%d"
                 "（r11 唯一条目 R11T-012↔AP-8 无再现；r16 1 条=r16 在案、"
                 "r17/r18 逐轮如实计数）"
                 % (len(geo_r18), len(cat_r18))),
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
            "ref": {"path_rel": REL_PREP_R18, "sha256": _sha(REL_PREP_R18)},
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
            "source_of_r15_r16_r17_detail": (
                "calibration-run-r15.json / calibration-run-r16.json / "
                "calibration-run-r17.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/s55/s58/"
                "s64 deviation_note 口径：本轮对 R15/R16/R17/R18 均以内嵌"
                "输入+compare_v3 同源几何原语（calibration._containment/_"
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
                "r17_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r17_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r18_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R15/R16/R17 十二件"
                         "复算与在案 run 登记一致：R15/R16 候选对=空集、"
                         "R17 候选对=空集（run-r17 在案）；R18 十二件"
                         "重放全部复现，见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R15T/R15B、R16T/R16B、R17T/"
            "R17B 与 R18T/R18B 来自不同 reader 实例、不同判读实例；轮内"
            "实例行为差异见 reader.reader_instance_note=混杂因素；r18 "
            "两板各自从头编号亦属实例输出行为差异、如实登记）；下列分组"
            "是通道级归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "r17_area_ratio_rejected_entries": geo_r17,
            "r18_area_ratio_rejected_entries": geo_r18,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r15_category_mismatch_entries": cat_r15,
            "r16_category_mismatch_entries": cat_r16,
            "r17_category_mismatch_entries": cat_r17,
            "r18_category_mismatch_entries": cat_r18,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r15_entries": view_r15,
            "r16_entries": view_r16,
            "r17_entries": view_r17,
            "r18_entries": view_r18,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r18 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；r15/r16/r17 重放亦零视角门条目（在案延续）。"
                     % len(view_r18)),
        },
        "gate_chain_since_r6": chain,
        "r18_specific_observations": [
            "R18 六实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条；GT 条目层 union/agreement 与"
            "代表配置口径见 gt_match_dual/aggregation_representative"
            "（如实分列）；bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
            "side=top，bottom GT 无源在案 gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R18 courtyard 类旗标 %d 条（top %d+bottom %d）：top 非弃权 "
            "courtyard 5 条（applied-top-i2 R18T-001/002/003 三条近邻"
            "报告+applied-top-i3 R18T-002+prep1-top-i1 R18T-001 轮廓互"
            "越报告）、弃权 5 条；bottom courtyard 0 条——G1 守门（"
            "bottom 非弃权 courtyard 0/0/0）维持；top 弃权构成分型="
            "接触性 8+存在性 12+层归属其他 0"
            "（hypothesis_test.mechanism_observation."
            "top_abstain_typology 逐旗摘录在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R18 几何门 %d 条（r17=0 延续与否如实计数）；类别门 %d 条"
            "（r16=1 后的 r17/r18 逐轮计数如实登记）；视角门条目数"
            "见 view_gate_observations（如实单列）。"
            % (len(geo_r18), len(cat_r18)),
            "R18 suspicious_reroute 旗标 3 条（非弃权报告 1+弃权 2，全部 "
            "applied-top-i1，(state, flag_id) 限定）；产量链 r8=1→r9=0→"
            "r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→r17=1→r18=3；"
            "「等长|蛇形」子串旗级零命中（prep1-top-i2 notes 有「蛇形」"
            "一词=判刻意图形的正常判定援引、非旗标）——r18 滥用型通道"
            "被动追踪=0（见 hypothesis_test.reroute_continuation_r18，"
            "非本轮判据输入）。",
            "courtyard 被动追踪（r11–r17 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r18 "
            "courtyard_tracking 节）。",
        ],
    }


def _prep_doc() -> dict:
    """r18-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R18)


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
    弃权旗数；per r18-prep-record guard_channel「G1=bottom courtyard
    非弃权 0/0/0 维持（对照 r15/r16 在案 0/0/0）」原文；守门独立单列、
    不影响字母。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r18 两板各自从头编号、明细行已按 (state, flag_id) 限定）；
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


# ---------------------------------------------------------------------------
# 分型件 rubric 机械口径（M3 计数唯一口径；装载→r13–r16 重放对拍→r18
# 套用；关键词表/优先级全部从 abstain-typology-r13-r16.json 装载，
# 不另嵌一套词表）
# ---------------------------------------------------------------------------

R18_FAMILY_COUNTS_REGISTERED = {
    "contact": 8, "existence_blackdot": 13, "existence_other": 12,
    "semantic_confusion": 0, "other": 0}


def load_typology_rubric() -> dict:
    """分型件 rubric 装载（fail-closed：五类定义+关键词表+优先级在件）。"""
    doc = _json_load(REL_TYPOLOGY)
    rub = doc["rubric"]
    kt = rub["keyword_tables"]
    for key in ("blackdot_terms", "uncertainty_terms", "contact_terms",
                "contact_doubt_patterns", "text_primary_terms",
                "text_primary_pattern", "explicit_existence_terms",
                "semantic_terms", "generic_existence_patterns",
                "uncertainty_terms"):
        if key not in kt:
            _fail(f"typology rubric 关键词表缺失: {key}")
    if "existence_blackdot" not in rub["families"] \
            or "先于 contact" not in rub["priority_adjudication_note"]:
        _fail("typology rubric 五类定义/优先级与预期不符")
    if sorted(rub["priority_as_registered"]) != sorted(
            ("contact", "existence_blackdot", "existence_other",
             "semantic_confusion", "other")):
        _fail("typology rubric priority_as_registered 与预期不符")
    if rub["unit"] != "abstain=true 旗标（逐旗；非弃权旗不分型、仅入分母对照）":
        _fail("typology rubric unit 与预期不符")
    return doc


def rubric_classify(text: str, kt: dict) -> tuple:
    """rubric 机械互斥分型（s60 classify 同法；词表=分型件装载）。

    优先级（priority_adjudication_note）：existence_blackdot（黑点族
    对象+不确定性）→ contact（接触词+怀疑模式组合、文本主因抑制）→
    existence_other（显式）→ semantic_confusion → existence_other
    （泛化兜底）→ other。
    """
    bd = [k for k in kt["blackdot_terms"] if k in text]
    unc = [k for k in kt["uncertainty_terms"] if k in text]
    ct = [k for k in kt["contact_terms"] if k in text]
    cd = [name for name, pat in kt["contact_doubt_patterns"].items()
          if re.search(pat, text)]
    tp = [k for k in kt["text_primary_terms"] if k in text]
    if re.search(kt["text_primary_pattern"], text):
        tp.append("位号(主语)")
    ee = [k for k in kt["explicit_existence_terms"] if k in text]
    sm = [k for k in kt["semantic_terms"] if k in text]
    ge = [name for name, pat in kt["generic_existence_patterns"].items()
          if re.search(pat, text)]
    hits = {}
    for key, val in (("blackdot_terms", bd), ("uncertainty_terms", unc),
                     ("contact_terms", ct), ("contact_doubt_patterns", cd),
                     ("text_primary", tp), ("explicit_existence", ee),
                     ("semantic_terms", sm), ("generic_existence", ge)):
        if val:
            hits[key] = val
    if bd and unc:
        return "existence_blackdot", hits
    if ct and cd and not tp:
        return "contact", hits
    if ee:
        return "existence_other", hits
    if sm:
        return "semantic_confusion", hits
    if ge:
        return "existence_other", hits
    return "other", hits


def replay_typology_families(typology_doc: dict, kt: dict) -> dict:
    """r13–r16 132 条弃权旗 rubric 机械重放对拍（口径忠实性证明）。

    对分型件 per_flag 每条记录：从其 source_file 原文定位该旗的
    location_evidence，同法 classify，family 须与在案记录逐一相等
    （fail-closed）；并核对黑点族逐轮计数（r13=9/r14=14/r15=8/r16=12）
    与判正常派次计数（r15=3/r16=2）。
    """
    mism = []
    counts = {}
    for e in typology_doc["per_flag"]:
        raw_rel = "out/v3-tl2/calibration/" + e["source_file"]
        doc = json.loads(_rel(raw_rel).read_text(encoding="utf-8"))
        loc = None
        for img in doc["per_image"]:
            for f in img["flags"]:
                if f["flag_id"] == e["flag_id"]:
                    loc = f["location_evidence"]
        if loc is None:
            _fail(f"typology per_flag 源旗缺失: {e['source_file']} "
                  f"{e['flag_id']}")
        family, _ = rubric_classify(loc, kt)
        key = (e["round"], e["family"])
        counts[key] = counts.get(key, 0) + 1
        if family != e["family"]:
            mism.append((e["source_file"], e["flag_id"], e["family"],
                         family))
    if mism:
        _fail(f"rubric 重放与分型件 per_flag 不一致 {len(mism)} 条: "
              f"{mism[:5]}")
    if len(typology_doc["per_flag"]) != 132:
        _fail("分型件 per_flag 应 132 条")
    bd_counts = {r: counts.get((r, "existence_blackdot"), 0)
                 for r in ("r13", "r14", "r15", "r16")}
    if bd_counts != BLACKDOT_CHAIN_PRIOR:
        _fail(f"r13–r16 黑点族 rubric 计数与登记不符: {bd_counts}")
    disp = typology_doc["blackdot_dispatch"]
    for r in ("r15", "r16"):
        if len(disp[r]["judged_normal_dispatches"]) \
                != BLACKDOT_JUDGED_NORMAL_PRIOR[r]:
            _fail(f"分型件 {r} 判正常派次计数与登记不符")
    return {"per_flag_total": len(typology_doc["per_flag"]),
            "blackdot_counts": bd_counts}


def build_rubric_rows_r18(instances: dict, kt: dict) -> list:
    """r18 全部旗标逐旗 rubric 套用（弃权旗=互斥族分类；非弃权旗不分型
    （rubric unit 口径）、仅记录黑点对象词命中供「黑点转非弃权旗」
    机制观察计数）。"""
    rows = []
    for name in INSTANCE_ORDER:
        parts = INSTANCES[name]["parts"]
        for d in instances[name]["per_flag_gt_detail"]:
            raw_rel = RAW_FILES[parts[0] if d["state"] == "applied"
                                else parts[1]]
            doc = json.loads(_rel(raw_rel).read_text(encoding="utf-8"))
            loc = None
            for img in doc["per_image"]:
                for f in img["flags"]:
                    if f["flag_id"] == d["flag_id"]:
                        loc = f["location_evidence"]
            if loc is None:
                _fail(f"r18 旗 location_evidence 缺失: {d['flag_id']} "
                      f"({name}/{d['state']})")
            family = None
            hits = {}
            if d["abstain"]:
                family, hits = rubric_classify(loc, kt)
            else:
                hits = {"blackdot_terms":
                        [k for k in kt["blackdot_terms"] if k in loc]}
            rows.append({"instance": name, "state": d["state"],
                         "flag_id": d["flag_id"],
                         "category": d["category"], "abstain": d["abstain"],
                         "family": family,
                         "matched_blackdot_terms":
                             hits.get("blackdot_terms", [])})
    rows.sort(key=lambda r: (r["instance"], r["state"], r["flag_id"]))
    return rows


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          run_r11: dict, run_r12: dict, run_r13: dict,
                          run_r14: dict, run_r15: dict, run_r16: dict,
                          run_r17: dict, axis_plan: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（axis-plan-r18-blackdot-note，轴2 黑点中性仪器注记）裁决节
    （预注册三分判据执行；字母裁决唯一正式+守门 G1/G2 独立单列+机制
    观察单列）。

    字母裁决（唯一正式裁决）=判据 r18-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：主度量=M3（黑点族弃权旗数，分型件 rubric 口径；基线=r16
    12）三分判据——
    (r) reject：M3 ≥ 10（注记未使黑点族回落）或 G1/G2 任一破坏（按
    axis-plan early_stop 出局；转向轴3/组合轮）；
    (s) supported：M3 ≤ 6（r16 基线 12 的一半）且 G1（bottom courtyard
    非弃权 0/0/0）与 G2（guard_ok）维持且 M1（top 全旗聚合弃权率）
    ≤ 0.85（不劣于 r15/r16 带上缘 0.862 的漂移容差内）→轴2 supported；
    (m) marginal：M3 7–9（回落未过半）或 M1 0.85–0.862——记录为部分
    收益。
    M1 基线=27/35=0.771429（run-r16 内嵌实例记录双侧复算 live 重放交
    叉核对一致）；M3 基线=分型件 r16 实测装载交叉核对（rubric 机械
    重放 r13–r16 逐旗 family 对拍在案）。M3 为整数、M1 阈值比较用
    6 位定点整数交叉相乘（×10^6，避免浮点）；支序=reject→supported→
    marginal（判据字面：reject 与 supported 在 G 维持下经 M3 阈值互斥、
    supported 与 marginal 经 M3≤6∧M1≤0.85 与带内定义互斥；未覆盖组合
    即自洽性破坏、中止）。守门 G1 与 G2 独立单列——任一破坏→reject
    支成立且轴2 按 axis-plan early_stop_rule 出局（字母照实+出局声明）；
    机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R18)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（axis-plan/probe/typology/witness-r14b/dev-r16/
    # dev-r17/run-r16 锚已在 FROZEN_SHA256 校验；prep-record chain_anchors
    # 内嵌登记值与盘上实测逐一核对，fail-closed）
    anchors = prep_doc["guidance_reuse"]["chain_anchors"]
    if anchors["axis_experiment_plan_frozen"]["path_rel"] != REL_AXIS_PLAN \
            or anchors["axis_experiment_plan_frozen"]["sha256"] \
            != _sha(REL_AXIS_PLAN):
        _fail("prep-record 链锚（axis-plan）与盘上实测不符")
    probe_anchor = anchors["blackdot_probe_transcription_source"]
    if probe_anchor["path_rel"] != REL_PROBE_R18 \
            or probe_anchor["sha256"] != _sha(REL_PROBE_R18):
        _fail("prep-record 链锚（blackdot-probe-r18）与盘上实测不符")
    typ_anchor = anchors["typology_blackdot_baseline"]
    if typ_anchor["path_rel"] != REL_TYPOLOGY \
            or typ_anchor["sha256_measured"] != _sha(REL_TYPOLOGY):
        _fail("prep-record 链锚（abstain-typology）与盘上实测不符")
    if typ_anchor["blackdot_abstain_flags_rubric"] != BLACKDOT_CHAIN_PRIOR:
        _fail("prep-record typology 黑点族基线与脚本登记不符")
    if typ_anchor["blackdot_judged_normal_dispatches"] \
            != BLACKDOT_JUDGED_NORMAL_PRIOR:
        _fail("prep-record typology 黑点判正常派次基线与脚本登记不符")
    dev16_anchor = anchors["round16_dev_record_g1_anchor"]
    if dev16_anchor["path_rel"] != REL_DEV_R16 \
            or dev16_anchor["sha256_measured"] != _sha(REL_DEV_R16):
        _fail("prep-record 链锚（round16-dev-record G1）与盘上实测不符")
    dev17_anchor = anchors["round17_dev_record_chain"]
    if dev17_anchor["path_rel"] != REL_DEV_R17 \
            or dev17_anchor["sha256_measured"] != _sha(REL_DEV_R17)[:8]:
        _fail("prep-record 链锚（round17-dev-record）与盘上实测不符")
    run16_anchor = anchors["run_r16_baseline_anchor"]
    if run16_anchor["path_rel"] != REL_RUN_R16 \
            or run16_anchor["sha256_measured"] != _sha(REL_RUN_R16):
        _fail("prep-record 链锚（run-r16 基线）与盘上实测不符")
    if "27/35" not in run16_anchor["frozen_values"] \
            or "0.771429" not in run16_anchor["frozen_values"] \
            or "guard_ok=True" not in run16_anchor["frozen_values"]:
        _fail("prep-record run-r16 基线冻结值文本与预期不符")
    witness_anchor = anchors["render_witness_r14b_byte_reuse"]
    if witness_anchor["path_rel"] != REL_WITNESS_R14B \
            or witness_anchor["sha256"] != _sha(REL_WITNESS_R14B):
        _fail("prep-record 链锚（witness-r14b 字节复用）与盘上实测不符")
    if anchors["evaluation_protocol_v1_preserved"]["sha256"] \
            != _sha(REL_PROTOCOL):
        _fail("prep-record 链锚（evaluation-protocol-v1）与盘上实测不符")
    if anchors["r15_prep_record_schema_template"]["sha256"] \
            != _sha(REL_PREP_R15):
        _fail("prep-record 链锚（r15-prep-record 模板）与盘上实测不符")
    if anchors["r16_prep_record_mirror_source"]["sha256"] \
            != _sha(REL_PREP_R16):
        _fail("prep-record 链锚（r16-prep-record 镜像源）与盘上实测不符")
    gr = prep_doc["guidance_reuse"]
    if gr["derived_path_rel"] != REL_GUIDANCE_R18 \
            or gr["derived_sha256"] != _sha(REL_GUIDANCE_R18) \
            or gr["base_path_rel"] != REL_GUIDANCE_R15 \
            or gr["base_sha256"] != _sha(REL_GUIDANCE_R15):
        _fail("prep-record guidance_reuse 指引锚与盘上实测不符")
    if prep_doc["round_id_constant"] != ROUND_ID \
            or prep_doc["round_label"] != ROUND_LABEL \
            or prep_doc["declared_date"] != DECLARED_DATE \
            or prep_doc["instrument_change"]["changed"] is not False \
            or prep_doc["no_instrument_change"] is not True:
        _fail("prep-record 轮次标识/instrument_change.changed 与预期不符")
    # 四 PNG sha 三方核对（FROZEN 锚=witness-r14b 登记=prep-record 登记；
    # witness_key 按 prep-record 登记路径解析）
    witness_doc = _json_load(REL_WITNESS_R14B)

    def _witness_value(witness_key: str):
        node = witness_doc
        for part in witness_key.split("."):
            node = node[part]
        return node

    for entry in prep_doc["instrument_change"]["renders"]:
        part = entry["state_side"]
        if PNG_FILES[part] != entry["path_rel"] \
                or entry["sha256_measured"] != _sha(PNG_FILES[part]) \
                or entry["sha256_witness_registered"] \
                != _witness_value(entry["witness_key"]) \
                or entry["sha256_witness_registered"] \
                != entry["sha256_measured"] or entry["match"] is not True:
            _fail(f"prep-record instrument_change.renders 与实测不符: "
                  f"{part}")
    # probe 件关键事实核对（§5B 转录源；kind/round/overall_status 与
    # F2 证书点差值在件）
    probe_doc = _json_load(REL_PROBE_R18)
    if probe_doc["kind"] != "tl2_blackdot_probe_r18" \
            or probe_doc["round_id_constant"] != ROUND_ID \
            or "F1/F2 confirmed" not in probe_doc["overall_status"] \
            or "F3 identity_confirmed_blackdot_indeterminate" \
            not in probe_doc["overall_status"]:
        _fail("probe 件 kind/round_id/overall_status 与预期不符")
    if probe_anchor.get("f2_certificate_delta_px") is not None:
        fam_statuses = sorted(str(f.get("status")) for f in
                              probe_doc["families"])
        if json.dumps(probe_doc["families"], ensure_ascii=False).count(
                str(probe_anchor["f2_certificate_delta_px"])) < 1 \
                or fam_statuses != sorted(["confirmed", "confirmed",
                    "identity_confirmed_blackdot_indeterminate"]):
            _fail("probe 件 F2 证书差值/族状态与 prep-record 登记不符")
    if probe_doc["section_5b_text"] not in \
            _rel(REL_GUIDANCE_R18).read_text(encoding="utf-8"):
        _fail("指引 §5B 与 probe section_5b_text 逐字不符")
    # axis-plan 基线登记值 fail-closed 装载核对（非手抄）
    rb = axis_plan["baselines_registered"]["r16_baseline"]
    if rb["round_id"] != "r16" \
            or rb["M1_top_aggregate_abstain_rate"] != 0.771429 \
            or rb["M2_bottom_aggregate_abstain_rate"] != 0.857143 \
            or rb["M3_blackdot_abstain_flags_rubric"] \
            != AXIS_R16_M3_BLACKDOT_RUBRIC \
            or rb["M4_top_per_instance_rate_range"] != AXIS_R16_M4_TOP_RANGE:
        _fail("axis-plan r16 基线登记值与预期不符")
    r15ref = axis_plan["baselines_registered"]["r15_reference"]
    if r15ref["M1_top_aggregate_abstain_rate"] != 0.862069 \
            or r15ref["M3_blackdot_abstain_flags_rubric"] != 8:
        _fail("axis-plan r15 参照轮登记值与预期不符")
    if "0.09064" not in axis_plan["baselines_registered"][
            "drift_reference_note"]:
        _fail("axis-plan 漂移参照值与预期不符")
    if "≥0.10" not in axis_plan["comparison_rule"][
            "significant_benefit_definition"]:
        _fail("axis-plan 显著收益定义与预期不符")
    for gkey in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                 "G3_freeze_discipline"):
        if gkey not in axis_plan["guards"]:
            _fail(f"axis-plan 守门定义缺失: {gkey}")
    if ht["hypothesis_id"] != "axis-plan-r18-blackdot-note":
        _fail("prep-record hypothesis_id 与预期不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "≤ 6" not in adj["supported"] or "0.85" not in adj["supported"] \
            or "G1" not in adj["supported"] or "G2" not in adj["supported"]:
        _fail("prep-record supported 判据文本与预期不符")
    if "7–9" not in adj["marginal"] or "0.85–0.862" not in adj["marginal"]:
        _fail("prep-record marginal 判据文本与预期不符")
    if "≥ 10" not in adj["reject"] or "G1/G2" not in adj["reject"]:
        _fail("prep-record reject 判据文本与预期不符")
    # 阈值常数自检（6 位定点）：M1 支持门 0.85 ≤ marginal 带上缘 0.862；
    # M3 三支区间衔接（supported ≤6 < marginal 7–9 < reject ≥10）
    if not (SUPPORTED_M1_THRESHOLD_6DP < MARGINAL_M1_UPPER_6DP):
        _fail("M1 阈值常数序破坏")
    if not (SUPPORTED_M3_MAX < MARGINAL_M3_MIN
            and MARGINAL_M3_MAX < REJECT_M3_MIN):
        _fail("M3 三支阈值衔接破坏")
    # M3 基线与 rubric 机械口径装载（分型件 r16 实测装载交叉核对；
    # 不手工抄数：r13–r16 132 条弃权旗先按同一 classify 重放对拍）
    typology_doc = load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    replay_proof = replay_typology_families(typology_doc, kt)
    if replay_proof["blackdot_counts"]["r16"] \
            != AXIS_R16_M3_BLACKDOT_RUBRIC \
            or rb["M3_blackdot_abstain_flags_rubric"] \
            != replay_proof["blackdot_counts"]["r16"]:
        _fail("M3 基线（r16=12）三方装载不一致")
    rubric_rows = build_rubric_rows_r18(instances, kt)
    m3 = sum(1 for r in rubric_rows
             if r["abstain"] and r["family"] == "existence_blackdot")
    family_counts = {fam: sum(1 for r in rubric_rows
                              if r["abstain"] and r["family"] == fam)
                     for fam in ("contact", "existence_blackdot",
                                 "existence_other", "semantic_confusion",
                                 "other")}
    if m3 != len(BLACK_DOT_FLAGS) \
            or family_counts != R18_FAMILY_COUNTS_REGISTERED:
        _fail(f"M3/家族计数与登记不符: m3={m3} {family_counts}")
    rubric_bd = {(r["instance"], r["state"], r["flag_id"]) for r in
                 rubric_rows
                 if r["abstain"] and r["family"] == "existence_blackdot"}
    if rubric_bd != {(i, s, f) for i, s, f, _ in BLACK_DOT_FLAGS}:
        _fail("rubric 黑点族旗集合与登记表不一致")
    # 黑点转非弃权旗（机制观察计数）：非弃权旗中黑点对象词命中集合须与
    # 登记表逐一相等（覆盖完整性 fail-closed）
    nonabstain_bd = {(r["instance"], r["state"], r["flag_id"]) for r in
                     rubric_rows
                     if not r["abstain"] and r["matched_blackdot_terms"]}
    if nonabstain_bd != {(i, s, f) for i, s, f, _
                         in BLACK_DOT_NON_ABSTAIN_FLAGS}:
        _fail(f"黑点转非弃权旗集合与登记不符: {sorted(nonabstain_bd)}")
    # 黑点判正常派次计数（分型件 blackdot_dispatch 口径：notes 判黑点
    # 正常且该派次零黑点旗标）——程序实测 vs 登记表
    bd_disp_rows = []
    judged_normal = []
    for key in RAW_FILES:
        notes = parsed_notes[key]
        doc = json.loads(_rel(RAW_FILES[key]).read_text(encoding="utf-8"))
        has_bd_flag = any(
            [k for k in kt["blackdot_terms"] if k in f["location_evidence"]]
            for img in doc["per_image"] for f in img["flags"])
        notes_bd = [k for k in kt["blackdot_terms"] if k in notes]
        if notes_bd:
            bd_disp_rows.append({"source": key,
                                 "abstain_flag": bool(has_bd_flag),
                                 "notes_hit_terms": notes_bd})
        if notes_bd and not has_bd_flag:
            judged_normal.append(key)
    if sorted(judged_normal) != ["applied-top-i1", "prep1-top-i2"]:
        _fail(f"黑点判正常派次与登记不符: {sorted(judged_normal)}")
    # §5B 援引实测（旗级=黑点旗 location_evidence 含「§5B」预期零；
    # 派次级=notes 含「§5B」=applied-top-i1 恰 1）
    fiveb_flag_hits = []
    fiveb_notes_hits = []
    for key in RAW_FILES:
        doc = json.loads(_rel(RAW_FILES[key]).read_text(encoding="utf-8"))
        for img in doc["per_image"]:
            for f in img["flags"]:
                if "§5B" in f["location_evidence"]:
                    fiveb_flag_hits.append((key, f["flag_id"]))
        if "§5B" in parsed_notes[key]:
            fiveb_notes_hits.append(key)
    if fiveb_flag_hits:
        _fail(f"黑点旗 location_evidence 出现 §5B 援引（预期零）: "
              f"{fiveb_flag_hits}")
    if fiveb_notes_hits != ["applied-top-i1"]:
        _fail(f"§5B 派次级援引与登记不符: {fiveb_notes_hits}")
    for ev in FIVEB_CITATION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"§5B 援引摘录与 reader 原文不符: {ev['source']}")
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
    # reroute 产量链基线交叉核对（r8–r17 在案）
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
            or run_r17["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r17"]:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（M3=黑点族弃权旗数为主度量、M1=top 全旗聚合弃权率为
    # supported 附加门，12 派次全口径；三分判据逐支）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    top_rate_6dp = cal._round6(top_rate) if top_rate is not None else None
    # (r) reject：M3 ≥10 或 G1/G2 任一破坏（守门在下方实测后合成）
    crit_reject_m3 = m3 >= REJECT_M3_MIN
    # (s) supported：M3 ≤6 且 G1/G2 维持且 M1 ≤0.85（6 位定点交叉相乘）
    crit_supported_m3 = m3 <= SUPPORTED_M3_MAX
    m1_gate_ok = abst_top * 1000000 <= SUPPORTED_M1_THRESHOLD_6DP * flags_top
    # (m) marginal：M3 7–9 或 M1 0.85–0.862（带上缘=r15 在案 0.862069
    # 的判据引用 0.862；6 位定点）
    crit_marginal_m3 = MARGINAL_M3_MIN <= m3 <= MARGINAL_M3_MAX
    crit_marginal_m1 = SUPPORTED_M1_THRESHOLD_6DP * flags_top \
        < abst_top * 1000000 <= MARGINAL_M1_UPPER_6DP * flags_top
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
    geo_r18 = attribution["channel_1_geometry_gate"][
        "r18_area_ratio_rejected_entries"]
    geo_r17 = attribution["channel_1_geometry_gate"][
        "r17_area_ratio_rejected_entries"]
    guard_ok = len(geo_r18) <= len(geo_r17)
    g2_ok = guard_ok is True
    guards_ok = bool(g1_ok and g2_ok)
    axis_out = not guards_ok
    # 三支合成（判据字面；支序=reject→supported→marginal）
    crit_reject_guards = not guards_ok
    crit_reject_ok = crit_reject_m3 or crit_reject_guards
    crit_supported_ok = crit_supported_m3 and guards_ok and m1_gate_ok
    crit_marginal_ok = crit_marginal_m3 or crit_marginal_m1
    if crit_reject_ok and crit_supported_ok:
        _fail("主通道判定自洽性破坏（reject 与 supported 两支互斥）")
    # 字母裁决（三分判据，per r18-prep-record adjudication 原文）
    if crit_reject_ok:
        verdict = "reject"
        if crit_reject_guards:
            letter_branch = ("(r) G1/G2 任一破坏（per axis-plan "
                             "early_stop_rule）——轴2 出局（字母照实+出局"
                             "声明）；转向轴3/组合轮")
        else:
            letter_branch = ("(r) M3 ≥ 10（注记未使黑点族回落）——轴2 "
                             "reject：§5B 中性仪器注记未使黑点族负责任"
                             "判定成立；转向轴3/组合轮")
    elif crit_supported_ok:
        verdict = "supported"
        letter_branch = ("(s) M3 ≤ 6（r16 基线 12 的一半）且 G1/G2 维持"
                         "且 M1 ≤0.85——注记使黑点族负责任判定成立（轴2 "
                         "supported）")
    elif crit_marginal_ok:
        verdict = "marginal"
        letter_branch = ("(m) M3 7–9（回落未过半）或 M1 0.85–0.862——"
                         "记录为部分收益（轴2 不判定为胜出）")
    else:
        _fail("主通道判定未覆盖（M3/M1/G 组合未落入任一预注册支）")
    verdict_text = (
        "按预注册判据（r18-prep-record.json hypothesis_test.adjudication "
        "原文，三分判据）=%s（字母口径，唯一正式裁决）：落支=%s。实测："
        "M3（黑点族弃权旗数，分型件 rubric 口径）=%d（rubric 机械套用："
        "关键词表/优先级从 abstain-typology-r13-r16.json 装载，r13–r16 "
        "132 条弃权旗重放对拍逐一相等后套用 r18；基线=r16 12，分型件 "
        "r16 实测装载交叉核对一致）；(r) 支阈值 M3 ≥10（注记未使黑点族"
        "回落）→crit_reject_m3=%s；(s) 支 M3 ≤6 且 G1/G2 维持且 M1 "
        "≤0.85：M3 门=%s、M1（top 全旗聚合弃权率，12 派次全口径）=%d/%d"
        "=%s→M1 门=%s（r16 基线=同一聚合逻辑对 calibration-run-r16.json "
        "内嵌实例记录双侧复算=%d/%d=%s，与在案登记 27/35 及 axis-plan "
        "r16_baseline.M1 交叉核对一致，不手工抄数）；(m) 支 M3 7–9=%s、"
        "M1 0.85–0.862=%s（带上缘=r15 在案 0.862069 的判据引用 0.862）。"
        "轴2 指引侧单变量轮（§5B 黑点中性仪器注记；渲染零变更=renders-"
        "r14b 字节复用）下唯一实验变量=指引注记；字母裁决只回答「§5B "
        "注记是否使黑点族弃权显著回落」的计划件判据命中方向；三项判据"
        "文本分开如实记录、不合并；本轮判据均为描述性边界、非 APR-0011 "
        "门（门照常独立计算，互不凌驾、run-record 内分开表述）。守门 "
        "G1（bottom courtyard 非弃权 0/0/0 维持）=%s、G2（guard_ok=True "
        "维持，top 几何门面积比出局条目 R17=%d→R18=%d）=%s——均独立"
        "单列，%s（per axis-plan early_stop_rule%s）。注意：跨轮实例群"
        "漂移混杂照旧声明（r15→r16 纯重抽漂移 0.09064 在案参照）；单轮 "
        "n=3、development 域只描述不断言；机制观察单列（黑点旗 §5B 援引"
        "/黑点判正常派次/黑点转非弃权旗/M2/M4/top 弃权分型/courtyard "
        "计数），不凌驾、不改写字母裁决。"
        % (verdict, letter_branch,
           m3, crit_reject_m3,
           crit_supported_m3,
           abst_top, flags_top, top_rate,
           "成立" if m1_gate_ok else "不成立",
           base16_ab, base16_fl, cal._ratio(base16_ab, base16_fl),
           crit_marginal_m3, crit_marginal_m1,
           "维持（0/0/0）" if g1_ok else "破坏",
           len(geo_r17), len(geo_r18),
           "维持（True）" if g2_ok else "破坏",
           "守门均维持、不触发出局" if guards_ok
           else "守门破坏→reject 支成立+轴2 按 plan early_stop_rule "
                "出局（字母照实+出局声明）",
           "：guard_failure_exit=任一轮 G1/G2 破坏→该轴出局并如实记录"
           "（该轮 run/dev-record 照常落盘、字母裁决照常；「出局」仅指"
           "退出本实验后续组合与排序）" if axis_out else ""))
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 量化判据应用
    # + top 弃权分型逐旗 + 黑点族 + placement 处置 + 绿区语义化
    # + §5B 援引）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in QUANT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
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
    for ev in PLACEMENT_DISPOSITION_EVIDENCE:
        src_text = (parsed_notes[ev["source"]]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"placement 处置摘录与 reader 原文不符: {ev.get('flag_id')}")
    # 黑点族旗标登记校验（13 条全部存在、abstain=True、category=登记值、
    # rubric 族=existence_blackdot；附 matched 词与 §5B 旗级援引实测）
    black_rows = []
    rubric_row_by_key = {(r["instance"], r["state"], r["flag_id"]): r
                         for r in rubric_rows}
    for inst, st, fid, cat in BLACK_DOT_FLAGS:
        d = next(x for x in instances[inst]["per_flag_gt_detail"]
                 if x["flag_id"] == fid and x["state"] == st)
        if not d["abstain"] or d["category"] != cat:
            _fail(f"黑点族旗标登记与实测不符: {fid}")
        rr = rubric_row_by_key[(inst, st, fid)]
        if rr["family"] != "existence_blackdot":
            _fail(f"黑点族旗标 rubric 族与登记不符: {fid}")
        doc = json.loads(_rel(RAW_FILES[
            INSTANCES[inst]["parts"][0] if st == "applied"
            else INSTANCES[inst]["parts"][1]]).read_text(encoding="utf-8"))
        loc = next(f["location_evidence"] for img in doc["per_image"]
                   for f in img["flags"] if f["flag_id"] == fid)
        black_rows.append({"flag_id": fid, "instance": inst, "state": st,
                           "category": d["category"], "abstain": True,
                           "family": rr["family"],
                           "matched_blackdot_terms":
                               rr["matched_blackdot_terms"],
                           "cites_5B_location_evidence": "§5B" in loc})
    # 黑点转非弃权旗逐条摘录行（3 条；机制观察登记口径）
    nonabstain_black_rows = []
    for inst, st, fid, cat in BLACK_DOT_NON_ABSTAIN_FLAGS:
        rr = rubric_row_by_key[(inst, st, fid)]
        doc = json.loads(_rel(RAW_FILES[
            INSTANCES[inst]["parts"][0] if st == "applied"
            else INSTANCES[inst]["parts"][1]]).read_text(encoding="utf-8"))
        f = next(f for img in doc["per_image"] for f in img["flags"]
                 if f["flag_id"] == fid)
        nonabstain_black_rows.append({
            "flag_id": fid, "instance": inst, "state": st,
            "category": cat, "confidence": f["confidence"],
            "matched_blackdot_terms": rr["matched_blackdot_terms"],
            "location_evidence_excerpt": f["location_evidence"]})
    # 绿色区域语义化观察（r16/r17 side_observation 先例延续：按实例
    # 分布；程序实测 substring 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、
    # 不构成判据输入；r18 实测 §5A 显式援引=1/6 派次（applied-bottom-i3
    # notes），prep1-bottom-i3 notes 无绿色语义化自述、如实空缺）
    green_semantics = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        rec = INSTANCES[name]
        texts = [parsed_notes[p] for p in rec["parts"]]
        cites = [bool(r.get("cites_5A"))
                 for r in GREEN_SEMANTICS_EVIDENCE
                 if r["instance"] == name]
        has_green = any(t.count("绿") + t.count("翼瓣") + t.count("空隙")
                        for t in texts)
        if any(cites):
            mode = "§5A 仪器注记显式提及（绿色=非图元）"
        elif has_green:
            mode = "空隙/翼瓣几何语义化（无 §5A 显式援引）"
        else:
            mode = "无绿色语义化自述（如实空缺）"
        green_semantics[name] = {
            "绿_hits_by_part": [t.count("绿") for t in texts],
            "翼瓣_hits_by_part": [t.count("翼瓣") for t in texts],
            "空隙_hits_by_part": [t.count("空隙") for t in texts],
            "§5A_cited": any(cites),
            "semantic_mode": mode,
        }
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    black_by_instance = {n: sum(1 for row in black_rows
                                if row["instance"] == n)
                         for n in INSTANCE_ORDER}
    r18_m4 = cal._round6(max(top_rates.values()) - min(top_rates.values()))
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决不因本观察"
                 "改写；per r18-prep-record adjudication."
                 "mechanism_observation_separate 原文：黑点旗逐条理由"
                 "对照注记援引情况（是否引用 §5B）；黑点判正常派次计数"
                 "（对照 r15=3/r16=2）；M1/M2/M4 照常入实验对照账"
                 "（(M1,M2,M3,M4) 四元组入 dev-record）；top 弃权分型"
                 "照常）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道三分判据分开实测（机制 (a)：主度量=M3）：M3（黑点"
                "族弃权旗数，分型件 rubric 口径）=%d（r13–r16 链 "
                "9/14/8/12 在案、r16 基线 12 分型件实测装载交叉核对）——"
                "(r) 支 M3 ≥10=%s（注记未使黑点族回落）；(s) 支 M3 ≤6"
                "=%s 且 M1（top 全旗聚合弃权率）=%d/%d=%s→M1 门 ≤0.85"
                "=%s 且 G1/G2 维持（见 guards_g1_g2）；(m) 支 M3 7–9=%s、"
                "M1 0.85–0.862=%s。⇒ verdict=%s（%s）。M3 为整数直接"
                "比较；M1 用 6 位定点整数交叉相乘（避免浮点）。判据均为"
                "r18-prep-record hypothesis_test.adjudication 原文，"
                "轮后如实执行。"
                % (m3, crit_reject_m3, crit_supported_m3,
                   abst_top, flags_top, top_rate,
                   "成立" if m1_gate_ok else "不成立",
                   crit_marginal_m3, crit_marginal_m1, verdict,
                   letter_branch)),
            "counts": {
                "m3_blackdot_abstain_flags_rubric_r18": m3,
                "m3_r16_baseline_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
                "m3_r13_r16_chain_live_replay":
                    replay_proof["blackdot_counts"],
                "supported_threshold_m3_le": SUPPORTED_M3_MAX,
                "marginal_m3_range": [MARGINAL_M3_MIN, MARGINAL_M3_MAX],
                "reject_threshold_m3_ge": REJECT_M3_MIN,
                "m1_supported_threshold_6dp": SUPPORTED_M1_THRESHOLD_6DP,
                "m1_marginal_upper_6dp": MARGINAL_M1_UPPER_6DP,
                "r16_top_baseline_registered":
                    BASE16_TOP_AGGREGATE_REGISTERED,
                "r16_top_baseline_live": f"{base16_ab}/{base16_fl}",
                "r16_top_baseline_value": cal._ratio(base16_ab, base16_fl),
                "top_flags_r18": flags_top,
                "top_abstain_r18": abst_top,
                "top_abstain_rate_r18": top_rate,
                "crit_reject_m3_ge_10": crit_reject_m3,
                "crit_supported_m3_le_6": crit_supported_m3,
                "crit_supported_m1_le_0_85": m1_gate_ok,
                "crit_marginal_m3_7_9": crit_marginal_m3,
                "crit_marginal_m1_0_85_0_862": crit_marginal_m1,
                "crit_reject_guards_broken": crit_reject_guards,
                "verdict": verdict,
            },
            "status": (
                "轴2 指引侧单变量轮（§5B 黑点中性仪器注记；渲染零变更="
                "renders-r14b 字节复用）下 M3 落点=%d→%s 支（如实单列）；"
                "判据命中与否的描述性结论，非因果证明" % (m3, verdict)),
        },
        "guards_g1_g2": {
            "role": ("守门通道独立单列（per r18-prep-record "
                     "attribution_plan.guard_channel 与 axis-plan guards "
                     "原文；任一破坏→reject 支成立+轴2 按 plan "
                     "early_stop_rule 出局）"),
            "observation": (
                "G1=bottom courtyard 非弃权 0/0/0 维持：r18 实测=%s"
                "（对照 r16 基线 0/0/0 live 重放交叉核对一致；bottom "
                "courtyard 类旗标本身=%d 条）→G1=%s。G2="
                "guard_ok=True 维持：top 几何门面积比出局条目 R17=%d→"
                "R18=%d（不升）→guard_ok=%s→G2=%s。守门结论=%s。"
                % (list(by_instance.values()), bot_courtyard_flags,
                   "维持" if g1_ok else "破坏",
                   len(geo_r17), len(geo_r18), guard_ok,
                   "维持" if g2_ok else "破坏",
                   "G1/G2 均满足、不触发出局" if guards_ok
                   else "守门破坏→reject 支成立+轴2 出局（字母照实+出局"
                        "声明）")),
            "counts": {
                "g1_bottom_courtyard_non_abstain_r18": by_instance,
                "g1_bottom_courtyard_flags_total_r18": bot_courtyard_flags,
                "g1_r16_baseline_live": r16_courtyard_base,
                "g1_ok": g1_ok,
                "g2_geometry_gate_r17": len(geo_r17),
                "g2_geometry_gate_r18": len(geo_r18),
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
                "%s，live 重放交叉核对一致）——方向=%s（改善方向：轴2 "
                "注记轮 bottom 弃权 13/19 vs r16 12/14；轮际比较含实例群"
                "漂移混杂、照 axis-plan comparison_rule 显式容忍）。bottom "
                "侧三件实测：(1) 零旗标派次=%d 个（12 格全部≥1 旗、"
                "对照 r17 的 2 格零旗标）；(2) 黑点族弃权旗（M3，分型件 "
                "rubric 口径）=%d 条 vs r16=12（数量回升 1 条、方向性"
                "描述；bottom 侧 10 条+top 侧 3 条）；(3) bottom "
                "courtyard 类旗=%d 条（r17 的 prep1-bottom-i3 R17B-001 "
                "courtyard 弃权旗在本轮未再现）——非弃权 courtyard 维持 "
                "0/0/0（G1）。"
                % (abst_bot, flags_bot, bot_rate,
                   cal._ratio(base16_bot_ab, base16_bot_fl),
                   ("低于 r16 基线（改善方向）" if bot_below_r16
                    else "不低于 r16 基线（维持/恶化）"),
                   0, m3, bot_courtyard_flags)),
            "counts": {
                "r16_bottom_aggregate_registered":
                    BASE16_BOTTOM_AGGREGATE_REGISTERED,
                "r16_bottom_aggregate_live":
                    f"{base16_bot_ab}/{base16_bot_fl}",
                "bottom_flags_r18": flags_bot,
                "bottom_abstain_r18": abst_bot,
                "bottom_abstain_rate_r18": bot_rate,
                "bottom_abstain_rate_r16_baseline":
                    cal._round6(base16_bot_ab / base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
                "zero_flag_dispatch_count": 0,
                "m3_blackdot_abstain_flags_rubric_r18": m3,
                "m3_blackdot_rubric_r16_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": (
                "5/6 派次摘录逐字来自对应 reading_notes（substring "
                "fail-closed 校验通过）——bottom 派次仍按 §4(i) 量化"
                "判据把绿色翼瓣/空隙形态判入「系统性正常→不报告」（判读"
                "路径延续；applied-bottom-i3 为 §5A 非图元路径、无 §4(i) "
                "自述，如实分列）"),
            "status": (
                "M2 改善方向+M3 回升 1 条+零旗派次归零如实单列（不影响"
                "字母裁决；development 域只描述不断言）"),
        },
        "experiment_comparison_ledger": {
            "role": ("实验对照账（per axis-experiment-plan-r17-r20 "
                     "benefit_metrics 口径；(M1,M2,M3,M4) 四元组如实入账"
                     "——四元组由后续 dev-record 包转记入 round18-dev-"
                     "record；全部=12 派次全口径（非代表配置子集）、与"
                     "分型件同法；单位=旗标条数（M3）或 6 位小数率）"),
            "metric_definitions": {
                k: axis_plan["benefit_metrics"][k]
                for k in ("M1_top_aggregate_abstain_rate",
                          "M2_bottom_aggregate_abstain_rate",
                          "M3_blackdot_abstain_flags_rubric",
                          "M4_top_per_instance_rate_range")},
            "r16_baseline_registered": {
                "M1": rb["M1_top_aggregate_abstain_rate"],
                "M2": rb["M2_bottom_aggregate_abstain_rate"],
                "M3": rb["M3_blackdot_abstain_flags_rubric"],
                "M4": rb["M4_top_per_instance_rate_range"],
                "live_replay_cross_check": {
                    "M1": f"{base16_ab}/{base16_fl}",
                    "M2": f"{base16_bot_ab}/{base16_bot_fl}",
                    "M3": replay_proof["blackdot_counts"]["r16"],
                    "M4_top_instance_rates": r16_top_rates},
            },
            "r18_measured": {
                "M1": top_rate,
                "M1_arithmetic": f"{abst_top}/{flags_top}",
                "M2": bot_rate,
                "M2_arithmetic": f"{abst_bot}/{flags_bot}",
                "M3": m3,
                "M4": r18_m4,
                "M4_top_instance_rates": top_rates,
            },
            "direction_vs_r16": {
                "M1": ("down（%s→%s，改善方向）"
                       % (rb["M1_top_aggregate_abstain_rate"], top_rate)),
                "M2": ("down（%s→%s，改善方向）"
                       % (rb["M2_bottom_aggregate_abstain_rate"],
                          bot_rate)),
                "M3": ("up（%d→%d，黑点族未回落——reject 支驱动）"
                       % (rb["M3_blackdot_abstain_flags_rubric"], m3)),
                "M4": ("%s→%s（同量级；轮内实例差异照旧）"
                       % (rb["M4_top_per_instance_rate_range"], r18_m4)),
            },
            "confounder_note": axis_plan["baselines_registered"][
                "drift_reference_note"],
            "status": ("四元组如实并列（M1/M2 降、M3 升——主度量 M3 落 "
                       "reject 支、M1 仅作 supported 附加门；development "
                       "域只描述不断言）"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r16/r17 side_observation "
                "先例延续观察）：r18 bottom 6 派次中 5 派次 notes 以"
                "「空隙/翼瓣」语义化绿色并按 §4(i) 判入系统性正常路径"
                "（判据轴延续）、prep1-bottom-i3 notes 无绿色语义化自述"
                "（如实空缺）；§5A 仪器注记显式援引=%d/6 派次"
                "（applied-bottom-i3 notes「全部绿色区域按 §5A 仪器注记"
                "视为非图元」）——对照 r16 的 6/6、r17 的 2/6 显式援引"
                "如实分列（指引 §5A 原文逐字保留、判据文本零变更，援引"
                "波动属实例自述异质性、如实登记不作废）。逐实例 substring "
                "计数「绿|翼瓣|空隙|§5A」+摘录如实登记（无期望、不构成"
                "判据输入）。"
                % sum(1 for v in green_semantics.values()
                      if v["§5A_cited"])),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("绿区语义化「空隙非图元」读法在实例群重抽下延续"
                       "（5/6 §4(i) 路径；§5A 显式援引 1/6 如实分列；"
                       "如实单列、不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点族现象追踪（机制观察 M3，分型件 rubric 口径；rubric "
                "机械套用证明见 rubric_families 节）：r18 黑点族弃权旗 %d "
                "条全部弃权——top 视 3 旗（prep1-top-i1 R18T-003 弃权+"
                "applied-top-i2 R18T-004+applied-top-i3 R18T-001，右上"
                "连接器黑点现象延续）+bottom 左上黑点 10 旗（i1 2+2、"
                "i2 0+2、i3 2+2）——vs r16 黑点族 12 旗（分型件 rubric "
                "口径在案）/r15=8：数量回升 1 条、方向性描述（§5B 中性"
                "仪器注记未使黑点族弃权回落=reject 支驱动）。另实测黑点"
                "转非弃权旗 %d 条（applied-bottom-i2 2 条 other_advisory "
                "非弃权报告+prep1-top-i3 1 条按关注现象归兜底类报告——"
                "r14–r17 同位黑点旗全部弃权/判正常路径中首次出现非弃权"
                "报告路径）+黑点判正常派次 %d 个（对照 r15=3/r16=2）。"
                % (len(black_rows), len(nonabstain_black_rows),
                   len(judged_normal))),
            "black_dot_flags": black_rows,
            "black_dot_non_abstain_flags": nonabstain_black_rows,
            "blackdot_to_non_abstain_count": len(nonabstain_black_rows),
            "by_instance": black_by_instance,
            "all_abstain": all(r["abstain"] for r in black_rows),
            "fiveb_citation_observation": {
                "role": ("黑点旗逐条理由对照注记援引情况（per "
                         "mechanism_observation_separate 原文「是否引用 "
                         "§5B」）"),
                "observation": (
                    "旗级（location_evidence 含「§5B」）实测=%d/%d 条黑点"
                    "弃权旗、非弃权黑点旗亦零——13+3 条黑点旗的弃权/报告"
                    "理由全部按 §2/§3A/§4 独立表述（系统性量化判据/接触"
                    "性判据/归类判据），零旗援引 §5B 注记文本（与 §5B "
                    "「不构成任何判据」的反指示声明一致，注记未被用作"
                    "判正常或判异常的依据）。派次级（reading_notes 含"
                    "「§5B」）实测=%d/12=applied-top-i1 恰 1（黑点判正常"
                    "路径援引：「§5B 为仪器事实注记，本判读仍按 §4 判据"
                    "独立执行，结论与注记来源一致」——援引同时声明按 §4 "
                    "独立执行）。"
                    % (len(fiveb_flag_hits), len(black_rows),
                       len(fiveb_notes_hits))),
                "flag_level_cite_count": len(fiveb_flag_hits),
                "notes_level_cite_count": len(fiveb_notes_hits),
                "notes_level_cite_sources": fiveb_notes_hits,
                "evidence": FIVEB_CITATION_EVIDENCE,
                "evidence_check": ("摘录逐字来自对应 reading_notes"
                                   "（substring fail-closed 校验通过）"),
            },
            "judged_normal_dispatches": {
                "observation": (
                    "黑点判正常派次计数（分型件 blackdot_dispatch 口径："
                    "notes 判黑点正常且该派次零黑点旗标）=%d/12——"
                    "applied-top-i1（判机械定位/安装孔类正常、含全轮唯一 "
                    "§5B 援引）+prep1-top-i2（判常规机械定位孔类正常）；"
                    "对照 r15=3/r16=2（分型件在案、live 装载核对一致）。"
                    "注意 prep1-bottom-i2 notes 虽有「椭圆焊盘+小椭圆槽+"
                    "黑点」组件判正常表述，但该派次同时就两处黑点落了 "
                    "2 条弃权旗（R18B-001/002）——按 blackdot_dispatch "
                    "口径归入 abstain_flag_dispatches、不计入判正常派次"
                    "（如实分列）。"
                    % len(judged_normal)),
                "count": len(judged_normal),
                "sources": judged_normal,
                "r15_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r15"],
                "r16_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r16"],
                "notes_hit_rows": bd_disp_rows,
            },
            "rubric_families": {
                "role": ("M3 计数口径（分型件 rubric 机械套用；关键词表/"
                         "五类定义/优先级从 abstain-typology-r13-r16.json "
                         "装载，脚本不另嵌词表；blackdot 对象判定先于 "
                         "contact 组合）"),
                "counts": family_counts,
                "rows": [
                    {k: r[k] for k in ("instance", "state", "flag_id",
                                       "category", "family",
                                       "matched_blackdot_terms")}
                    for r in rubric_rows if r["abstain"]],
                "replay_proof": replay_proof,
                "replay_proof_note": (
                    "口径忠实性证明：同一 classify 先对 r13–r16 全部 %d 条"
                    "弃权旗重放，逐旗 family 与分型件在案记录逐一相等；"
                    "r16 黑点族计数=%d=M3 基线（axis-plan 登记值交叉核对"
                    "一致）"
                    % (replay_proof["per_flag_total"],
                       replay_proof["blackdot_counts"]["r16"])),
                "note": ("r18 全部 33 条弃权旗逐旗分类入账（rows）——"
                         "existence_blackdot %d/contact %d/existence_other "
                         "%d/semantic_confusion %d/other %d；本分型"
                         "（rubric 族）与 top_abstain_typology（contact/"
                         "existence/other_layer 主出口分型）为两套登记"
                         "口径、分别如实入账（例：prep1-top-i2 R18T-001 "
                         "读者自述主出口=接触性判据→top 分型计 contact；"
                         "rubric 族因文本主因抑制 contact→existence_other）"
                         % (family_counts["existence_blackdot"],
                            family_counts["contact"],
                            family_counts["existence_other"],
                            family_counts["semantic_confusion"],
                            family_counts["other"])),
            },
            "notes_normal_dispositions": (
                "2 派次判正常：applied-top-i1「右上连接器内成对、同尺寸、"
                "成列对齐的两处实心黑点，形态为无铜环的小钻孔样式，结合"
                "通用 PCB 域知识判为机械定位/安装孔类正常设计特征，不报告"
                "」+prep1-top-i2「右上成对实心黑点形态一致、成对对齐且不"
                "与任何布线/焊盘图形相互作用，结合一般 PCB 域知识判为常规"
                "机械定位孔类正常设计特征，按三路出口不报告」（摘录见 "
                "evidence 表 disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点族弃权路径延续+数量回升 1 条（13 vs r16 12）+"
                       "非弃权报告路径首现 3 条+判正常派次 2（如实单列、"
                       "不凌驾字母裁决）"),
        },
        "top_abstain_typology": {
            "observation": (
                "top 弃权理由构成分型（机制观察，per mechanism_observation_"
                "separate「top 弃权分型照常」；为 M1=%s 未过/过 supported "
                "门的构成提供分解）：本轮 top 弃权旗 %d 条逐旗按 "
                "location_evidence 关键词分类——接触性（真实接触 vs 视觉"
                "贴近不可分辨/是否接触不可确认，含读者自述「按接触性判据"
                "弃权」主出口）=%d 条、存在性（性质不明/是否存在不可确认）"
                "=%d 条、层归属等其他出口=%d 条。构成解读（如实单列）："
                "接触性弃权集中于 courtyard 类旗标与丝印-焊盘/连印近邻"
                "（§4(iii) 判据路径延续），存在性弃权横跨 silk/other/"
                "reroute 各类（黑点性质、疑似叠印、弯折迹线存在性等）——"
                "top 弃权非单一机制驱动；对照 r16（接触性 11+存在性 15+"
                "层归属其他 1，27 条）与 r17（接触性 8+存在性 14+其他 0，"
                "22 条）：r18 绝对数 27→22→20 续降、构成比稳定（接触性 "
                "主通道+存在性多通道分散）；弃权旗数下降但弃权率 M1="
                "%s（分母同步降 35→31）。逐旗摘录与分类在案（rows）。"
                % (top_rate, len(typology_rows), typology_counts["contact"],
                   typology_counts["existence"],
                   typology_counts["other_layer"], top_rate)),
            "type_counts": typology_counts,
            "top_abstain_flags_total": len(typology_rows),
            "r16_reference_counts": {"contact": 11, "existence": 15,
                                     "other_layer": 1},
            "r17_reference_counts": {"contact": 8, "existence": 14,
                                     "other_layer": 0},
            "rows": typology_rows,
            "evidence_check": (
                "%d/%d 条摘录逐字来自对应 location_evidence 且 (source, "
                "flag_id) 集合与实测 top 弃权旗集合逐一相等（substring+"
                "覆盖 fail-closed 校验通过）"
                % (len(typology_rows), len(typology_rows))),
            "top_abstain_rates_by_instance": top_rates,
            "top_abstain_rate_range": top_range,
            "status": ("top 弃权构成=接触性主通道+存在性多通道分散（"
                       "如实单列、不凌驾字母裁决）"),
        },
        "residual_instance_differences": {
            "observation": (
                "残余实例差异（如实单列）：(1) top 弃权率 %s/%s/%s（极差 "
                "%s）——top-i3 最高（7/9=0.777778）、top-i2 最低（4/8=0.5，"
                "该实例贡献 4 条非弃权旗）；(2) bottom 弃权率 %s/%s/%s"
                "（极差 %s）——bottom-i2 最低（2/6=0.333333，黑点双非弃权"
                "报告实例）；(3) placement/孤立图形处置实例/跨板分化延续"
                "且加剧：板内孤立焊盘对 bottom-i1 applied 非弃权报告/"
                "prep1 弃权、bottom-i2 applied 非弃权报告（含左上椭圆"
                "焊盘组）+prep1 notes 判正常不报告、bottom-i3 applied "
                "非弃权报告+prep1 notes 判正常不报告——同现象跨实例/跨板"
                "出口不同=判读语义歧义未穷尽；「正确测出无效同样是有效"
                "证据」的同构：测出残余差异同样是有效证据。"
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
                 "适用；per r18-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r18 三分判据以主度量 M3（整数）+附加门 M1（6 位定点整数交叉"
            "相乘，阈值=冻结件 0.85/0.862 原文）执行；M3 计数口径=分型件 "
            "rubric 机械套用（关键词表/优先级 fail-closed 装载+对 r13–r16 "
            "132 条弃权旗重放对拍逐一相等后套用 r18）——口径可复算性="
            "本轮度量设计要点（计数口径跨轮漂移是历史教训：r15 dev-record "
            "prose 口径 7 vs 分型件 rubric 口径 8 在案，axis-plan "
            "M3_caveat 已声明一律采用 rubric 口径）；跨轮实例群漂移混杂"
            "照旧声明（r15→r16 纯重抽漂移 0.09064 在案、axis-plan "
            "comparison_rule 显式容忍且不消除）；M1 分母（top 旗数）"
            "本身随轮变化（35→31），弃权率比较含分母效应、构成分解"
            "（top 弃权构成分型+黑点转非弃权旗）单列补足。"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一轮候选方向（如实登记，不构成本轮判据"
                   "输入）：reject 支内嵌「转向轴3/组合轮」（axis-plan "
                   "stage1 rounds R19=§4(iii) 接触性可操作分辨条款/组合"
                   "轮，均须各自 prep-record 预注册后执行）；"
                   "不得回溯改判既往轮次（r8–r17 字母裁决维持不变）"),
    }
    # r16/r17 分层基线（逐实例弃权率，live 重放；不手工抄数）
    r16_top_rates_live = r16_top_rates
    r16_bottom_rates = {}
    for n in ("bottom-i1", "bottom-i2", "bottom-i3"):
        r16_bottom_rates[n] = run_r16["instances"][n]["combined"][
            "abstain_rate"]
    r16_bottom_range = cal._round6(
        max(r16_bottom_rates.values()) - min(r16_bottom_rates.values()))
    run_r17_top_rates = {n: run_r17["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R18,
                                "sha256": _sha(REL_PREP_R18)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "supported": adj["supported"],
            "reject": adj["reject"],
            "marginal": adj["marginal"],
            "primary_channel_change": prep_doc["attribution_plan"][
                "primary_channel"]["change"],
            "primary_channel_metric": prep_doc["attribution_plan"][
                "primary_channel"]["metric"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "mechanism_observation_separate":
                adj["mechanism_observation_separate"],
            "guards_registered_in_axis_plan": {
                k: axis_plan["guards"][k]["rule"]
                for k in ("G1_bottom_courtyard_nonabstain_zero",
                          "G2_guard_ok")},
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel_metric": prep_doc["attribution_plan"][
            "primary_channel"]["metric"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r18-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮轴2 收益方向归因"
            "（axis-experiment-plan-r17-r20 冻结比较规则），与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "m3_blackdot_abstain_flags_rubric_r18": m3,
            "m3_arithmetic_note": (
                "M3 = 黑点族弃权旗数（分型件 rubric 口径）= %d（r18 全部 "
                "33 条弃权旗逐旗 rubric 分类中 existence_blackdot 计数；"
                "关键词表/优先级=abstain-typology-r13-r16.json 装载；"
                "r13–r16 132 条弃权旗重放对拍逐一相等=口径忠实性证明）"
                % m3),
            "top_abstain_flags_r18": flags_top,
            "top_abstain_count_r18": abst_top,
            "top_abstain_rate_r18": top_rate,
            "top_abstain_rate_r18_arithmetic":
                f"M1 = top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（supported 附加门度量；12 派次全口径）",
            "crit_reject_m3_ge_10": crit_reject_m3,
            "crit_supported_m3_le_6": crit_supported_m3,
            "crit_supported_m1_le_0_85": m1_gate_ok,
            "crit_marginal_m3_7_9": crit_marginal_m3,
            "crit_marginal_m1_0_85_0_862": crit_marginal_m1,
            "m1_supported_threshold_6dp": SUPPORTED_M1_THRESHOLD_6DP,
            "m1_marginal_upper_6dp": MARGINAL_M1_UPPER_6DP,
            "top_abstain_rate_r16_baseline_live":
                f"{base16_ab}/{base16_fl}",
            "top_abstain_rate_r16_baseline_value":
                cal._ratio(base16_ab, base16_fl),
            "m3_r16_baseline_registered": AXIS_R16_M3_BLACKDOT_RUBRIC,
            "m3_r16_baseline_live_replay":
                replay_proof["blackdot_counts"],
            "baseline_replay_note": (
                "M1 基线=同一聚合逻辑对 calibration-run-r16.json 内嵌实例"
                "记录（states 层 reader_flags+compare_v3.abstain）双侧"
                "复算，不手工抄数；M3 基线=分型件 r16 实测装载（rubric "
                "重放对拍）；均与在案登记值（r18-prep-record "
                "chain_anchors.run_r16_baseline_anchor.frozen_values："
                "top 27/35=0.771429、guard_ok=True；typology_blackdot_"
                "baseline.r16=12；axis-plan baselines_registered."
                "r16_baseline.M1=0.771429/M3=12）交叉核对（fail-closed，"
                "见 baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r18":
                    by_instance,
                "bottom_courtyard_flags_total_r18": bot_courtyard_flags,
                "bottom_abstain_flags_r18": flags_bot,
                "bottom_abstain_count_r18": abst_bot,
                "bottom_abstain_rate_r18": bot_rate,
                "bottom_abstain_rate_r18_arithmetic":
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
            "bottom_courtyard_detail_r18": [
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
                "r16_m3_registered": AXIS_R16_M3_BLACKDOT_RUBRIC,
                "r16_m3_live_replay": replay_proof["blackdot_counts"],
                "axis_plan_r16_baseline_M1_M2_M3_M4": [
                    rb["M1_top_aggregate_abstain_rate"],
                    rb["M2_bottom_aggregate_abstain_rate"],
                    rb["M3_blackdot_abstain_flags_rubric"],
                    rb["M4_top_per_instance_rate_range"]],
                "note": ("基线数字与 run-r16 内嵌输入重放/分型件实测装载"
                         "交叉核对一致（fail-closed：live 与登记不符即 "
                         "FAIL）；registered=r18-prep-record/axis-plan "
                         "在案登记/判据原文冻结值，live=本轮从 run-doc/"
                         "分型件重放装载实测"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（实测 %s，"
                    "r16 基线 live 重放 0/0/0）=%s；G2=guard_ok=True "
                    "维持（top 几何门面积比出局条目 R17=%d→R18=%d）"
                    "=%s；任一破坏→reject 支成立+轴2 按 plan "
                    "early_stop_rule 出局"
                    % (list(by_instance.values()),
                       "满足" if g1_ok else "破坏",
                       len(geo_r17), len(geo_r18),
                       "满足" if g2_ok else "破坏")),
                "g1_ok": g1_ok,
                "g2_geometry_gate_r17": len(geo_r17),
                "g2_geometry_gate_r18": len(geo_r18),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "note": ("守门通道按 r18-prep-record attribution_plan."
                         "guard_channel 与 axis-plan guards 独立复核；"
                         "不构成 r18 字母裁决独立输入（G 破坏经 reject "
                         "支字面并入字母裁决）"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r17 run-record courtyard_tracking 在案先例延续）——"
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
                "abstain_rate_r17_representative":
                    run_r17["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r18_representative_note": (
                    "代表配置聚合弃权率见 aggregation_representative."
                    "abstain_rate_total（本轮聚合口径按 measurement_design "
                    "五条预注册执行，代表配置/逐实例/双口径分列）"),
                "note": (
                    "跨轮聚合弃权率（口径分列如实）：r9 0.727273（8/11，"
                    "全旗标）→r10 0.285714（4/14，全旗标）→r11 0.133333"
                    "（2/15，代表配置）→r12 0.9（9/10，代表配置）→r13 "
                    "0.909091（10/11，代表配置）→r14 0.833333（10/12，"
                    "代表配置）→r15 0.785714（11/14，代表配置）→r16 "
                    "0.764706（13/17，代表配置）→r17 0.916667（11/12，"
                    "代表配置）→r18 见代表配置分列；主通道三分判据与门"
                    "各自独立计算、互不凌驾（prep-record "
                    "descriptive_boundary_note 原文语义）——门联合评价与"
                    "字母裁决分列不合并"),
            },
            "r18_total_flags_note": (
                "六实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；M3=黑点族弃权旗数 "
                "%d 为三分判据主度量、M1=top 全旗聚合弃权率 %d/%d=%s 为 "
                "supported 附加门、M2=bottom 全旗聚合弃权率 %d/%d=%s 为"
                "侧观察度量、各自单列）"
                % (n_total_all,
                   (flags_top - abst_top) + (flags_bot - abst_bot),
                   abst_top + abst_bot,
                   cal._ratio(abst_top + abst_bot, n_total_all),
                   m3,
                   abst_top, flags_top, top_rate,
                   abst_bot, flags_bot, bot_rate)),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"supported=「{adj['supported'][:80]}…」；"
            f"reject=「{adj['reject'][:80]}…」；"
            f"marginal=「{adj['marginal'][:80]}…」"
            "（r18-prep-record.json hypothesis_test.adjudication 判据原文"
            "全文见 preregistered_criteria_quote，轮后如实执行；结果无论"
            "方向均如实入账"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r18": {
            "role": ("r12 假设通道被动追踪（round13–round17-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r18": reroute_rows,
            "reroute_total_r18": len(reroute_rows),
            "reroute_by_instance_r18": {
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
                                 "r17": REROUTE_CHAIN_PRIOR["r17"],
                                 "r18": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径，旗级 location_evidence "
                "子串命中）：r10=2→r11=1→r12=0→r13 被动追踪=1（R13T-009 "
                "在案）→r14=0（R14T-004 子串零命中）→r15 机械命中=1"
                "（R15T-001 非弃权旗含「蛇形」子串——否定式援引、非滥用"
                "型引用，run-r15 在案）→r16=0（在案）→r17=0（R17T-002 "
                "子串零命中、存在性弃权）→r18=0（3 条 reroute 旗级子串"
                "零命中；prep1-top-i2 notes 有「蛇形」一词=「判为刻意"
                "图形（天线/蛇形类常规设计形态）」的正常判定援引、非旗"
                "标、非滥用型引用，如实登记）——不构成 r18 判据输入"
                "（两判据分列互不凌驾）"),
        },
        "stratified_observation": {
            "top": {"r16_by_instance_live": r16_top_rates_live,
                    "r16_range_live": AXIS_R16_M4_TOP_RANGE,
                    "r17_by_instance": run_r17_top_rates,
                    "r18_by_instance": top_rates,
                    "r18_range": top_range,
                    "direction": ("r16 三实例 %s（轮内极差 %s）→r17 %s/"
                                  "%s/%s→r18 三实例 %s/%s/%s（轮内极差 "
                                  "%s）——轴2 注记轮、实例群重抽混杂照旧"
                                  "下实例层的方向性对照（聚合 M1 %d/%d=%s"
                                  " vs r16 基线 27/35=0.771429、r17 的 "
                                  "22/25=0.88；轮内实例差异照旧）"
                                  % (f"{r16_top_rates_live['top-i1']}/"
                                     f"{r16_top_rates_live['top-i2']}/"
                                     f"{r16_top_rates_live['top-i3']}",
                                     AXIS_R16_M4_TOP_RANGE,
                                     run_r17_top_rates["top-i1"],
                                     run_r17_top_rates["top-i2"],
                                     run_r17_top_rates["top-i3"],
                                     top_rates["top-i1"],
                                     top_rates["top-i2"],
                                     top_rates["top-i3"], top_range,
                                     abst_top, flags_top, top_rate))},
            "bottom": {"r16_by_instance_live": r16_bottom_rates,
                       "r16_range_live": r16_bottom_range,
                       "r18_by_instance": bottom_rates,
                       "r18_range": bottom_range,
                       "direction": ("r16 三实例 %s（极差 %s）→r18 三"
                                     "实例 %s/%s/%s（极差 %s）——bottom "
                                     "聚合 M2 %d/%d=%s vs r16 的 12/14="
                                     "0.857143（侧观察如实单列；改善方向"
                                     "并记）"
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
                             run_r16: dict, run_r17: dict) -> dict:
    """courtyard 被动追踪（r11–r17 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r18 courtyard 类旗标与命中如实入账
    ——top 非弃权 5 条（applied-top-i2 R18T-001/002/003+applied-top-i3
    R18T-002+prep1-top-i1 R18T-001）+top 弃权 5 条+bottom 0 条。"""
    note_source = {
        "path_rel": REL_PREP_R18, "sha256": _sha(REL_PREP_R18),
        "quote": None,
        "note": ("r18-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r17 "
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
    prior = run_r17["courtyard_tracking"]
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
        "r18_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（bottom 零 courtyard 类旗标；对照 r17 的 "
                             "top 6+bottom 1 全弃权、r16 的 top 12+"
                             "bottom 2 全弃权，如实登记）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r18": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r17": prior["courtyard_matches_r17"],
        "courtyard_matches_r17_detail": (
            "R17 非弃权 courtyard 1 条（top-i3 R17T-001，containment 无 "
            "≥0.5 交叠）零命中（run-r17 在案）；courtyard 类弃权旗=top 6+"
            "bottom 1（run-r17 在案）"),
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
            "r16 回升 1 条（R16T-001↔AP-6）、r17 零命中；r18 非弃权 "
            "courtyard=%d 条（命中=%d，如实登记）；GT/阈值零改动"
            % (len(non_abstain_rows),
               sum(r["matches"] for r in non_abstain_rows))),
        "bottom_observation": {
            "fact": ("R18 bottom %d 旗（bottom-i1 6+bottom-i2 6+"
                     "bottom-i3 7）=非弃权 %d（placement/孤立图形类 4+"
                     "other_advisory 黑点 2）+弃权 %d："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=0（r14 弃权 4 条/r15 零旗"
                     "标/r16 弃权 2 条/r17 弃权 1 条/r18 零旗标，逐轮"
                     "构成如实分列）；弃权构成见 reader.flag_count."
                     "by_category；本轮零旗标格=0（实例/派次层弃权率全部"
                     "有定义，measurement_design item 5 口径在案：遇零"
                     "分母→None 不编造数值）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
            "evidence": QUANT_CRITERION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）——bottom 派次"
                               "仍按 §4(i) 把绿色翼瓣/空隙形态判入系统性"
                               "正常路径（不进 flags；applied-bottom-i3 "
                               "为 §5A 非图元路径）"),
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r18 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    run_r17 = _json_load(REL_RUN_R17)
    axis_plan = _json_load(REL_AXIS_PLAN)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, run_r16, run_r17, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, run_r15, run_r16,
                                run_r17, axis_plan, instances,
                                view_layer, attribution, raw_texts,
                                parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9,
                                         run_r10, run_r11, run_r12,
                                         run_r13, run_r14, run_r15,
                                         run_r16, run_r17)

    prep_r18 = _json_load(REL_PREP_R18)
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
            "五键投影（process-v1 §2 步骤3）；R18 reroute 类三旗 "
            "location_evidence 逐字在案（R18T-001 非弃权报告+R18T-002/"
            "003 存在性弃权，「等长|蛇形」子串旗级零命中——"
            "reroute_continuation_r18 逐旗判定在案）；"
            "R18 top 弃权旗 20 条逐旗分型摘录在案（top_abstain_typology："
            "接触性 8+存在性 12+层归属其他 0）；"
            "R18 全部 33 条弃权旗逐旗 rubric 族分类在案（black_dot_"
            "tracking.rubric_families）；bottom 黑点族/placement 处置"
            "弃权旗摘录在案（black_dot_tracking/"
            "residual_instance_differences）；§5B 援引观察逐件摘录在案"
            "（black_dot_tracking.fiveb_citation_observation）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "zero_flag_parts": {
            "parts": zero_flag_parts,
            "note": ("本轮 12 格全部≥1 旗（零旗格=0；对照 r17 的 2 格"
                     "零旗标 prep1-bottom-i1/i2）——实例层与派次层弃权率"
                     "全部有定义；measurement_design item 5 口径在案"
                     "（遇零旗标分母→按库侧 cal._ratio 先例=None+文字"
                     "说明，不编造数值；本轮不触发）"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R18, "role": "r18_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R18)},
        {"path_rel": REL_AXIS_PLAN,
         "role": "axis_experiment_plan_r17_r20_frozen",
         "sha256": _sha(REL_AXIS_PLAN)},
        {"path_rel": REL_DEV_R17,
         "role": "r17_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R17)},
        {"path_rel": REL_DEV_R16,
         "role": "r16_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R16)},
        {"path_rel": REL_PREP_R16, "role": "r16_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R16)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R18,
         "role": "observation_guidance_r18_active",
         "sha256": _sha(REL_GUIDANCE_R18)},
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
        {"path_rel": REL_PROBE_R18,
         "role": "blackdot_probe_r18_section_5b_transcription_source",
         "sha256": _sha(REL_PROBE_R18)},
        {"path_rel": REL_TYPOLOGY,
         "role": "abstain_typology_r13_r16_rubric_and_baseline_source",
         "sha256": _sha(REL_TYPOLOGY)},
        {"path_rel": REL_FRAMING_R14B,
         "role": "render_framing_r14b_lineage",
         "sha256": _sha(REL_FRAMING_R14B)},
        {"path_rel": REL_WITNESS_R14B,
         "role": "render_witness_r14b_byte_reuse",
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
         "role": "render_png_applied_top_r14b_byte_reuse",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r14b_byte_reuse",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"],
         "role": "render_png_prep1_top_r14b_byte_reuse",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r14b_byte_reuse",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r18",
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
            "axis_id": "A2_blackdot_instrument_annotation",
            "nature": INSTRUMENT_NATURE,
            "note": prep_r18["instrument_change"]["note"],
            "declaration": prep_r18["instrument_change"]["declaration"],
            "renders_registered": [
                {"state_side": e["state_side"], "path_rel": e["path_rel"],
                 "sha256_measured": e["sha256_measured"],
                 "sha256_witness_registered":
                     e["sha256_witness_registered"],
                 "witness_record": e["witness_record"],
                 "match": e["match"]}
                for e in prep_r18["instrument_change"]["renders"]],
            "components": [
                "渲染零变更=renders-r14b 四图字节复用（与 r14/r15/r16/"
                "r17 盲读同一批文件；no_instrument_change=true）"],
            "unchanged_components": list(prep_r18["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v.get("attribution_channel"),
                 "instrument_change": v["instrument_change"]}
                for v in prep_r18["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r18["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r18["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r18["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R18, "sha256": _sha(REL_PREP_R18)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；r18 指引 §6 示例旗 ID 前缀 R18T-/R18B- 随指引"
            "落盘固化（r13→r15「随指引落盘固化」路径回归，无需派发层"
            "覆盖，per r18-prep-record protocol_amendment.naming）；"
            "实例间编号独立；"
            "同实例两板各自从头编号=r18 实测输出行为、与 prep-record "
            "naming「同实例跨板连续」声明不同（与 r15/r16/r17 实测同"
            "形态），见 dispatch_mode.flag_id_continuity_note"),
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
                    "r13 指引 §4（经 r18 指引逐字承 r15 原文适用，本轮指引"
                    "=observation-guidance-r18.md，§2–§7 分段逐字保留断言"
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
                    "地判断；abstain 单列不参与匹配；§5B 黑点仪器注记="
                    "仪器事实非判据（不构成任何「应判正常/无需报告」的"
                    "指示，旗标判定仍按 §2/§3A/§4 独立执行）"),
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
                                      "（blackdot-probe-r18.json 与 "
                                      "framing/witness 记录不进任何 "
                                      "reader 上下文）、零 legend/零其他"
                                      "解释（判读输入=指引+单张 PNG+派发"
                                      "指令）；每图独立判读；跨实例/跨视角"
                                      "禁止交流（独立性亦为轴2 收益裁决"
                                      "有效性的前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R18,
                                 "sha256": _sha(REL_GUIDANCE_R18),
                                 "frozen_before_read": True,
                                 "transform_mode":
                                     "mechanical_transform_derive",
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R15,
                                     "sha256": _sha(REL_GUIDANCE_R15),
                                     "role": ("r18 指引的机械变换基座"
                                              "（§2–§7 判据逐字承 r15；"
                                              "r15 指引=r15 轮落盘产物）")},
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：axis-experiment-plan-r17-r20.json"
                 "（b6ec6467…，stage1 R18=轴2 黑点中性仪器注记轮定义+"
                 "「无探针证实则该轴不得入轮」探针先决+comparison_rule+"
                 "守门+early_stop_rule，先于 R17–R21 任何实验轮盲读冻结；"
                 "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益"
                 "最大的继续」user_directive_note 在案）→s66 探针证实"
                 "（blackdot-probe-r18.json，a49441ac…，F1/F2 confirmed、"
                 "F3 indeterminate 如实登记）→r18-prep-record.json"
                 "（3fc054c4…，本轮预注册件，measurement_design 五条"
                 "聚合口径与 hypothesis_test.adjudication 三分判据"
                 "（supported M3 ≤6 且 G1/G2 且 M1 ≤0.85/marginal M3 7–9 "
                 "或 M1 0.85–0.862/reject M3 ≥10 或 G 破坏）"
                 "先于盲读冻结；instrument_change.changed=false；"
                 "guidance=机械变换；渲染=renders-r14b 字节复用）先于本轮"
                 "盲读落盘（零 GT 暴露声明在案 no_visual_reading=true；"
                 "pre_round_review=satisfied_by_probe——s66 探针证实+"
                 "axis-plan 探针先决条款在案）→判读指引="
                 "observation-guidance-r18.md（cadcb8f3…，r15 指引机械"
                 "变换产物+§5B 新节，本轮唯一判读依据）"
                 "→渲染零变更（renders-r14b 四图字节复用，四 PNG sha="
                 "witness-r14b 登记值=prep-record 登记值三方一致）→"
                 "12 次盲读→比对记录（读者产物零改动）。GT 重"
                 "投影（derivation-log-r5.json，13 条 frame_box_pct_r5）"
                 "已在案沿用（渲染零变更=重投影输入未变，口径随 r14 顶层"
                 "更换先例沿用；bottom GT 无源在案 gt-audit-r1）；GT 冻结"
                 "纪律：轮后未增删改；gt-audit-r1 结论维持 GT 零改动"
                 "（三候选关闭，gt_audit_reference 在案）。"),
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
            "r17_run": {"path_rel": REL_RUN_R17, "sha256": _sha(REL_RUN_R17)},
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
                     "重抽，verdict=inconclusive）与 R17（轴1 仪器轮："
                     "渲染侧单变量 renders-r17 四图 640→1280dpi 全新"
                     "渲染，verdict=reject）run 在案；R18=轴2 指引侧"
                     "单变量轮（§5B 黑点中性仪器注记；渲染零变更="
                     "renders-r14b 四图字节复用；执行 axis-plan stage1 "
                     "R18=A2_blackdot_instrument_annotation、探针先决"
                     "已满足；与 R15 同为「指引侧单变量轮」血统）；轮间"
                     "对比由后续 round18-dev-record（另包落盘）与 "
                     "channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取/通道重放/rubric "
            "机械分型为纯函数（六实例旗数 14/8/9/6/6/7→代表配置 top-i3+"
            "bottom-i1（top 中位实例 9 唯一=top-i3；bottom 中位 6 为 "
            "i1/i2 tie、按先序取 bottom-i1 并如实注明）唯一可复算），"
            "无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-09-r18（事件序="
            "axis-experiment-plan-r17-r20（b6ec6467…，冻结件在案）→"
            "s66 探针证实（blackdot-probe-r18.json，a49441ac…）→"
            "r18-prep-record"
            "（3fc054c4…，本轮预注册件，先于盲读冻结）→r18 指引机械"
            "变换落盘（cadcb8f3…，本轮唯一判读依据）→渲染零变更"
            "（renders-r14b 四图字节复用、zero-write，witness-r14b 在案）"
            "→12 次盲读→比对记录；在案延续=gt-"
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
                                run_r16: dict, run_r17: dict,
                                parsed: dict, raw_texts: dict) -> None:
    """run-r18 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 14, "top-i2": 8, "top-i3": 9, "bottom-i1": 6,
                  "bottom-i2": 6, "bottom-i3": 7}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 9, "top-i2": 4, "top-i3": 7, "bottom-i1": 5,
                "bottom-i2": 2, "bottom-i3": 6}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 50:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.8 \
            or agg["flag_count_total"] != 15 \
            or agg["abstain_count_total"] != 12:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "reject":
        _fail("假设字母裁决与预注册判据复算不符")
    if hyp["hypothesis_id"] != "axis-plan-r18-blackdot-note":
        _fail("hypothesis_id 与预登记不符")
    m = hyp["measurement"]
    if m["m3_blackdot_abstain_flags_rubric_r18"] != 13 \
            or m["m3_r16_baseline_registered"] != 12:
        _fail("主通道 M3 计数与实测不一致")
    if m["top_abstain_flags_r18"] != 31 or m["top_abstain_count_r18"] != 20 \
            or m["top_abstain_rate_r18"] != 0.645161:
        _fail("附加门 M1 计数与实测不一致")
    if m["crit_reject_m3_ge_10"] is not True \
            or m["crit_supported_m3_le_6"] is not False \
            or m["crit_supported_m1_le_0_85"] is not True \
            or m["crit_marginal_m3_7_9"] is not False \
            or m["crit_marginal_m1_0_85_0_862"] is not False:
        _fail("三分判据布尔与实测不一致（M3=13 应落 reject 支）")
    if m["top_abstain_rate_r16_baseline_value"] != 0.771429:
        _fail("r16 基线值与在案登记不一致")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r18"] != 0 \
            or bso["bottom_abstain_flags_r18"] != 19 \
            or bso["bottom_abstain_count_r18"] != 13 \
            or bso["bottom_abstain_rate_r18"] != 0.684211 \
            or bso["bottom_courtyard_non_abstain_by_instance_r18"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0} \
            or bso["bottom_rate_direction_vs_r16"] != "improved":
        _fail("bottom 侧观察计数与实测不一致")
    g = m["guard_channel"]
    if g["g1_ok"] is not True or g["g2_guard_ok"] is not True \
            or g["guards_ok"] is not True \
            or g["g2_geometry_gate_r17"] != 0 \
            or g["g2_geometry_gate_r18"] != 0:
        _fail("守门 G1/G2 计数与实测不一致")
    mo = hyp["mechanism_observation"]
    tt = mo["top_abstain_typology"]
    if tt["type_counts"] != {"contact": 8, "existence": 12,
                             "other_layer": 0} \
            or tt["top_abstain_flags_total"] != 20:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 13 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 1, "top-i2": 1, "top-i3": 1,
                                     "bottom-i1": 4, "bottom-i2": 2,
                                     "bottom-i3": 4} \
            or bd["blackdot_to_non_abstain_count"] != 3 \
            or len(bd["black_dot_non_abstain_flags"]) != 3 \
            or bd["judged_normal_dispatches"]["count"] != 2 \
            or bd["fiveb_citation_observation"]["flag_level_cite_count"] \
            != 0 \
            or bd["fiveb_citation_observation"][
                "notes_level_cite_count"] != 1:
        _fail("黑点族计数与实测不一致")
    if bd["rubric_families"]["counts"] != R18_FAMILY_COUNTS_REGISTERED \
            or bd["rubric_families"]["replay_proof"]["per_flag_total"] \
            != 132:
        _fail("rubric 族计数/重放证明与实测不一致")
    if mo["bottom_side_observation_maintenance"]["counts"][
            "m3_blackdot_abstain_flags_rubric_r18"] != 13 \
            or mo["bottom_side_observation_maintenance"]["counts"][
                "zero_flag_dispatch_count"] != 0:
        _fail("bottom 侧观察 M3/零旗计数与实测不一致")
    ledger = mo["experiment_comparison_ledger"]
    if ledger["r18_measured"]["M1"] != 0.645161 \
            or ledger["r18_measured"]["M2"] != 0.684211 \
            or ledger["r18_measured"]["M3"] != 13 \
            or ledger["r18_measured"]["M4"] != 0.277778:
        _fail("实验对照账四元组与实测不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if sum(1 for v in gs.values() if v["§5A_cited"]) != 1:
        _fail("绿区语义化 §5A 引用与实测不一致（应为 1/6 实例）")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.277778 \
            or vl["bottom"]["abstain_rate_range"] != 0.52381:
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
        _fail("matches 明细与实测不一致（r18 应零命中：top 非弃权旗与同"
              "态 GT containment 无 ≥0.5 交叠或类别不符；bottom 非弃权旗"
              "结构性无匹配）")
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
            or run_r17["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r17"] \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 3:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R17 0→R18 0；类别 R17 0→R18 0）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r18_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r18_category_mismatch_entries"]) != 0:
        _fail("通道条目数与实测声明不一致")
    # courtyard 追踪与实测一致（r18 非弃权 courtyard=5、弃权=5、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r18"] != 0 or len(
            ct["r18_courtyard_flags"]["non_abstain"]) != 5:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r18_courtyard_flags"]["abstain"]) != 5:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 零旗标派次=0（12 格全部≥1 旗）
    if run_doc["reader"]["zero_flag_parts"]["parts"] != []:
        _fail("零旗标派次与实测不一致（应为空）")
    # 逐旗判定/工具规约/量化判据/分型/黑点/placement/绿区/§5B 援引
    # 摘录逐字在案
    for r in hyp["reroute_continuation_r18"]["reroute_flag_detail_r18"]:
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
    for ev in mo["black_dot_tracking"]["fiveb_citation_observation"][
            "evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"§5B 援引摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["residual_instance_differences"]["evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev.get("kind") == "reading_notes"
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r18")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), _json_load(REL_RUN_R15),
        _json_load(REL_RUN_R16), _json_load(REL_RUN_R17),
        parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R18), run_bytes,
                         "calibration-run-r18.json")
    run_sha = _sha(REL_RUN_R18)
    # round18-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s68-cal-r18] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 17、弃权 33）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s68-cal-r18] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s68-cal-r18] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s68-cal-r18] zero_flag_parts: "
          f"{[(z['instance'], z['state']) for z in run['reader']['zero_flag_parts']['parts']]}"
          f"（12 格全部≥1 旗、零旗格=0）")
    print(f"[s68-cal-r18] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}")
    print(f"[s68-cal-r18] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s68-cal-r18] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    m = hyp["measurement"]
    print(f"[s68-cal-r18] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；三分判据=主度量 M3 黑点族弃权旗数 "
          f"（分型件 rubric 口径）={m['m3_blackdot_abstain_flags_rubric_r18']}"
          f"（r16 基线 12 分型件实测装载交叉核对）；(r) 支 M3 ≥10→"
          f"crit_reject_m3={m['crit_reject_m3_ge_10']}；(s) 支 M3 ≤6→"
          f"crit_supported_m3={m['crit_supported_m3_le_6']} 且 M1 top 全旗"
          f"聚合弃权率 {m['top_abstain_count_r18']}/{m['top_abstain_flags_r18']}"
          f"={m['top_abstain_rate_r18']}→M1 门 ≤0.85="
          f"{m['crit_supported_m1_le_0_85']}（r16 基线双侧复算 "
          f"{m['top_abstain_rate_r16_baseline_live']}"
          f"={m['top_abstain_rate_r16_baseline_value']}）；(m) 支 M3 7–9="
          f"{m['crit_marginal_m3_7_9']}/M1 0.85–0.862="
          f"{m['crit_marginal_m1_0_85_0_862']}；落支={m['letter_branch']}"
          f"；守门 G1={m['guard_channel']['g1_ok']}/G2="
          f"{m['guard_channel']['g2_guard_ok']}（early_stop 触发="
          f"{m['guard_channel']['guards_ok'] is not True}）；机制观察单列）")
    print(f"[s68-cal-r18] 侧观察（M2 bottom 维持性，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r18']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r18']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r18']}"
          f" vs r16 基线 12/14=0.857143（{m['bottom_side_observation']['bottom_rate_direction_vs_r16']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r18']}"
          f"/courtyard 旗总数={m['bottom_side_observation']['bottom_courtyard_flags_total_r18']}")
    mo = hyp["mechanism_observation"]
    print(f"[s68-cal-r18] 机制观察要点：M3 rubric 族计数="
          f"{mo['black_dot_tracking']['rubric_families']['counts']}"
          f"（r13–r16 132 条重放对拍逐一相等）；黑点旗 13 条全弃权 "
          f"{mo['black_dot_tracking']['by_instance']}（vs r16=12）；"
          f"§5B 援引=旗级 "
          f"{mo['black_dot_tracking']['fiveb_citation_observation']['flag_level_cite_count']}"
          f"/13+派次级 "
          f"{mo['black_dot_tracking']['fiveb_citation_observation']['notes_level_cite_count']}"
          f"/12（applied-top-i1 判正常路径）；黑点判正常派次 "
          f"{mo['black_dot_tracking']['judged_normal_dispatches']['count']}/12"
          f"（对照 r15=3/r16=2）；黑点转非弃权旗 "
          f"{mo['black_dot_tracking']['blackdot_to_non_abstain_count']} 条"
          f"（applied-bottom-i2 2+prep1-top-i3 1）；四元组账 "
          f"(M1,M2,M3,M4)=(0.645161,0.684211,13,0.277778) vs r16 "
          f"(0.771429,0.857143,12,0.261904)；top 弃权分型="
          f"{mo['top_abstain_typology']['type_counts']}；reroute 3 旗"
          f"（非弃权报告 1+弃权 2、子串零命中）")
    print(f"[s68-cal-r18] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s68-cal-r18] channel_attribution: "
          f"geo R17={len(ca['channel_1_geometry_gate']['r17_area_ratio_rejected_entries'])}"
          f"→R18={len(ca['channel_1_geometry_gate']['r18_area_ratio_rejected_entries'])}, "
          f"cat R17={len(ca['channel_2_category_gate']['r17_category_mismatch_entries'])}"
          f"→R18={len(ca['channel_2_category_gate']['r18_category_mismatch_entries'])}")
    print(f"[s68-cal-r18] commit: run={run_status}（round18-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s68-cal-r18] sha256[:8] calibration-run-r18.json = "
          f"{run_sha[:8]}")
    print("[s68-cal-r18] R18 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
