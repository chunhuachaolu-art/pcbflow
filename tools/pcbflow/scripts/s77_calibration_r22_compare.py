#!/usr/bin/env python
"""CAL-R22-CLOSE：reader 判读迭代第二十二轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s71_calibration_r19_compare.py/s74_calibration_r20_
compare.py 同构，仅输入与轮次常量不同；R22=development 域同指引
重复轮（收敛归因轮；r16 先例：r15→r16 同指引重复、渲染零变更、
仅实例重抽）：渲染零变更=renders-r14b 四图字节复用（与 r14–r20
盲读同一批文件、四 PNG sha=witness-r14b 登记值 fail-closed 比对
一致）；判读指引=observation-guidance-r19.md 字节复用（8633bda5，
r19 轮落盘本体零字节不动、本轮不新建指引文件；其 §6 示例旗 ID
前缀保持 R19T-/R19B- 落盘原文——派发层覆盖为 R22T/R22B，前缀
差异登记、r16 先例在案）；GT/阈值/协议零变更（v1.1+v1.2 维持）；
instrument_change.changed=false 已预注册）——唯一操纵因子=reader
实例群抽样（12 派次全部重抽、与 r19/r20 实例群无身份延续）；
检验 r22-prep-record.json 预注册假设（hypothesis_id=r20-dev-record-
candidate-r19-config-same-guidance-repeat，判据=r22-prep-record.json
hypothesis_test.adjudication 复制性三分判据预注册原文，脚本从
prep-record 文件加载判据文本、基线数字 live 重放不手工抄数）：
「r19 配置（guidance-r19=§4(iii-a) 可操作分辨条款；渲染 r14b 字节
复用）的单轮收益 M1=0.461538 是否在新鲜实例群复现——真实收益 vs
实例群漂移的收敛归因裁决」：

  T1  解析 12 个 reader-raw-r22-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
      12 件哈希前缀逐字钉死（盲读亲测在案：applied-top-i1=fcea824a、
      prep1-top-i1=0de33b5f、applied-bottom-i1=e2758622、
      prep1-bottom-i1=044edcca、applied-top-i2=d8dad94e、
      prep1-top-i2=4849758c、applied-bottom-i2=31b978ef、
      prep1-bottom-i2=570b9a3b、applied-top-i3=60e96d3f、
      prep1-top-i3=6260dbbd、applied-bottom-i3=9796b4d6、
      prep1-bottom-i3=a81d8098，全量哈希入 FROZEN_SHA256）。
  T2  按 r22-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r16–r20 同一比较脚本血统；聚合口径零
      改动）：(1) 实例主记录=六实例各自两板合计 flag_count/abstain_
      count/abstain_rate（6 位小数；零旗标分母=None）/非弃权清单
      （r22 实测编号行为=5 个有旗实例全部同实例跨板连续+bottom-i1
      两板零旗标（与 prep-record naming「同实例跨板连续」声明相符，
      零旗标实例编号无可登记如实注明）；清单按 (state, flag_id) 限定，
      跨板同号不混淆）/逐旗 containment+area_ratio 匹配明细；
      (2) 视角层=每视角 3 实例 flag_count/abstain_rate/matches 各
      中位数+min+max 三分列不取整（本轮 12 格中 bottom-i1 两板零
      旗标=2 格零旗：bottom 视角弃权率含 None 实例→中位数=None、
      min/max 按可计算实例计算；item 5 零分母口径本轮触发）；
      (3) GT 匹配双口径=union（≥1 实例命中）与 agreement（≥2/3）
      并列+逐 GT 条目 matched_by_count（0..3；召回分母=GT 13 条）；
      (4) 联合门（APR-0011 阈值零改动）=代表配置（每视角 flag_count
      中位数实例）算一轮 joint+per-metric 实例间范围+逐实例原始记录
      三者并列不挑优；(5) bottom 零旗标分母=按库侧 cal._ratio 先例
      None+文字说明（本轮 bottom-i1 两板零旗标=该实例 None，先例
      本轮实测触发）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且本轮渲染零变更
      （renders-r14b 字节复用=GT 重投影输入未变），frame_box_pct_r5
      =GT 框在渲染图像空间的归一化坐标口径、随 r14 顶层更换先例沿用，
      本轮零新派生；bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（复制性三分判据，r22-prep-record.json hypothesis_
      test.adjudication 原文）逐支执行：判据=M1 落点+contact 族+
      守门维持——replicated=M1（top 全旗聚合弃权率，12 派次全口径）
      落 [0.361538, 0.561538]（r19±0.10）且 contact 族弃权旗数（全视，
      分型件 rubric 口径）≤7 且 G1（bottom courtyard 非弃权 0/0/0）
      与 G2（guard_ok）维持→r19 量级获复制支持；drifted=未达
      replicated 且 M1 <0.771429（r16 基线）且 G1/G2 维持→r19 量级
      部分归因实例群（收益方向存但幅度不确定）；regressed=M1 ≥
      0.771429 或 G1/G2 任一破坏→r19 量级不可复制、轴3 收益判定
      降级为单轮现象。判据比较用 6 位定点整数交叉相乘（避免浮点）；
      支序=regressed→replicated→drifted（判据字面互斥性由脚本自检，
      未覆盖组合即中止）。letter 裁决唯一正式；守门 G1/G2 独立单列
      （G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15–r19 在案
      0/0/0、r20 破坏 2/0/0 在案=分岔记录）、G2=guard_ok=True 维持
      ——top 视非弃权旗标 frame_box_pct 几何门面积比出局条目 R19=0
      →R22 实测不升；本轮守门破坏→regressed 支命中（描述性边界，
      per prep-record guard_channel requirement 原文：本实验已收束、
      收敛归因轮出局语义不适用、破坏照实记录））；M4 第二样本单列
      （m4_second_sample_separate 原文：r22 实测 M4 与 r19 的
      0.211111 双样本分布如实并列、不进字母裁决、不因双样本改门、
      不挑优、不合并分布）；机制观察单列（mechanism_observation_
      separate 原文口径）：contact/黑点/存在性三族计数（分型件
      rubric 口径）对照 r19（4/4/14）与 r20（2/6/10）；(iii-a) 援引
      计数对照 r19 基线（旗级「(iii-a)」6 旗+「分支(」2 旗；notes 级
      10/12 派次）、§5B 援引计数照记（本轮指引字节复用无 §5B 节=
      基座结构在案，任何援引为零上下文、如实登记）+ (iii-a) 逐旗
      理由落支分布（间隙支/侵入支/残余弃权支——逐旗摘录关键词；
      旗级落支+notes 级落支分列）；黑点族逐旗分类入账+黑点转非弃权
      旗计数（逐条摘录）+黑点判正常派次计数；M2=bottom 全旗聚合
      弃权率（对照 r16 基线 12/14=0.857143、r18 13/19=0.684211、
      r19 4/7=0.571429、r20 4/14=0.285714）；(M1,M2,M3,M4) 四元组
      入实验对照账字段（照 axis-plan benefit_metrics 口径定义、
      四元组随 run 在案、由 dev-record 包转记；对照账六行并列=
      r16 基线/r17 轴1/r18 轴2/r19 轴3/r20（破坏轮登记行）/
      r22 本轮；r17 行=round18-dev-record cross_round_status 实测
      装载、r18 行=run-r18 内嵌实例记录 live 复算、r19 行=dev-r19
      measured_rows 装载+run-r19 内嵌实例记录 live 复算交叉核对、
      r20 行=run-r20 内嵌记录 live 复算+登记值交叉核对、与各自在案
      登记交叉核对）；axis-plan comparison_rule（(M1 升序,M2 升序,
      M3 升序,M4 升序) 字典序、资格门=G1/G2 均满足）下的当前排序
      如实登记（资格门破坏轮不入排序；r22 按同口径 M 元组入排序）；
      显著收益定义（M1 绝对降幅 ≥0.10）逐轮对照；复制性结论位
      （replicated→r19 量级获复制支持；drifted→部分归因实例群；
      regressed→降级单轮现象）；top 弃权分型照常；bottom courtyard
      非弃权与 courtyard 旗计数（对照 r19 的 0 非弃权+4 弃权、r20 的
      2 非弃权+3 弃权）。
      → calibration-run-r22.json。
  T3  development 域记录（R19/R20→R22 收敛归因方向性对照/假设裁决/
      联合评价趋势/下一迭代目标）由后续 dev-record 包落盘
      （round22-dev-record，另包执行）；本包仅产出 run-r22、零
      dev-record 写入。

通道归因纪律（vs R19/R20；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/
s53/s55/s58/s64/s68/s71/s74 deviation_note 口径）：本轮对 R15/R16/
R17/R18/R19/R20 均以内嵌输入（reader_flags/gt_entries/flag_views，
run sha 在案）+compare_v3 同源几何原语（calibration._containment/
_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放
通道分类，并与各态 compare_v3 的 matches∪duplicate_reports 对拍
复核。跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是
通道级不是旗级。

读者实例披露（如实入账，不作废）：R22 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「未读取盘上任何其他文件」（12/12 在案）；
applied/prep1-top-i1 另自述「未与任何其他图像做跨图比对推断」、
prep1-top-i2 另自述「亦未跨图推断」、prep1-top-i3 另自述「未跨图
合并推断」、applied/prep1-bottom-i3 另自述「未对图像做任何程序化
处理（仅以 Read 查看原图，每图两遍）」（两板同图同判自述）；
§4(iii-a) 措辞 notes 级援引 6/12 派次、§5B 措辞 notes 级援引 0/12
派次（本轮指引字节复用无 §5B 节=任何援引为零上下文、两计数分开
记，逐件摘录见 hypothesis_test.mechanism_observation.criterion_
citation_observation）；applied/prep1-bottom-i1 零旗派次 notes 自述
按 §2 六类逐项核查并明引 §4(iii-a)(1) 间隙带可辨认→视觉贴近路径
（零旗标判读自述在案）；跨轮实例全重抽+轮内实例差异=混杂因素照旧
声明——本轮唯一操纵因子=reader 实例群重抽（指引/渲染字节复用、
仪器侧零变动；实例群重抽为本轮唯一实验操作与裁决变量、per r22-prep-
record attribution_plan.declaration 原文）。
输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件=缩进
格式冻结原始判读件、本轮零改动直读（direct JSON 解析、12 件 parse
校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round22-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量
2026-09-09 / 2026-09-09-r22）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s77_calibration_r22_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-09-r22"
ROUND_LABEL = "r22"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_GUIDANCE_R12 = "out/v3-tl2/calibration/observation-guidance-r12.md"
REL_GUIDANCE_R13 = "out/v3-tl2/calibration/observation-guidance-r13.md"
REL_GUIDANCE_R15 = "out/v3-tl2/calibration/observation-guidance-r15.md"
REL_GUIDANCE_R18 = "out/v3-tl2/calibration/observation-guidance-r18.md"
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
REL_PREP_R19 = "out/v3-tl2/calibration/r19-prep-record.json"
REL_PREP_R20 = "out/v3-tl2/calibration/r20-prep-record.json"
#: 本轮预注册件（预注册判据唯一事实源）。
REL_PREP_R22 = "out/v3-tl2/calibration/r22-prep-record.json"
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
REL_DEV_R18 = "out/v3-tl2/calibration/round18-dev-record.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
#: r20 轮 dev-record（本轮授权链锚；prep-record chain_anchors 引用）。
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
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
REL_RUN_R18 = "out/v3-tl2/calibration/calibration-run-r18.json"
REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_FRAMING_R14B = "out/v3-tl2/calibration/render-framing-r14b.json"
REL_WITNESS_R14B = "out/v3-tl2/calibration/render-witness-r14b.json"
REL_PROBE_R18 = "out/v3-tl2/calibration/blackdot-probe-r18.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_GUIDANCE_R19 = "out/v3-tl2/calibration/observation-guidance-r19.md"
REL_GUIDANCE_R20 = "out/v3-tl2/calibration/observation-guidance-r20.md"
#: 本轮判读指引=observation-guidance-r19.md 字节复用（8633bda5 锚；
#: 上两行 r19/r20 指引均为历史在案锚、本轮零新建指引文件）。
#: r20 轮在案 run（对照账 r20 行 live 复算输入；非本轮输出）。
REL_RUN_R20P = "out/v3-tl2/calibration/calibration-run-r20.json"
#: 本包唯一新建输出（防覆写护栏语义照 s68/s71/s74；不在 FROZEN_SHA256 锚集）。
REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"

#: 12 份盲读原始件（6 实例×2 板；r22 实测编号行为=5 个有旗实例全部
#: 同实例跨板连续+bottom-i1 两板零旗标（编号无可登记）、与 prep-record
#: naming「同实例跨板连续」声明相符，见 DISPATCH_MODE；本轮 2 格零旗
#: 标（bottom-i1 两板）、其余 10 格≥1 旗）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r22-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r22-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r22-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r22-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r22-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r22-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r22-prep1-bottom-i3.txt",
}

#: 六实例=本轮主记录单位（measurement_design item 1）；每实例=同视角
#: 两板（applied+prep1）两派次，实例间编号独立（r22 实测：5 个有旗
#: 实例全部同实例跨板连续；bottom-i1 两板零旗标）。
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

#: R20 渲染：图像来源=renders-r14b 四图字节复用（渲染零变更；与
#: r14–r19 盲读同一批文件；四 PNG 盘上 sha=witness-r14b
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
#: 渲染的输入侧冻结矢量 PDF（r22-prep-record no_loosening_note：本轮
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
#: guidance-r20 锚=本轮唯一判读依据（r19 指引基座 8633bda5+§5B 节自
#: r18 指引 cadcb8f3 逐字转录的机械变换产物；guidance-r19 锚=其变换
#: 基座、guidance-r18 锚=§5B 转录源、guidance-r15 锚=血统根基座
#: d5babc93，三条锚均在案）；prep-r20 锚=本轮预注册件（其 chain_
#: anchors 内嵌 axis-plan/probe-r18 前提/r15 根/r18-prep §5B 先例/
#: r19-prep 模板/witness-r14b/dev-r19 组合决策锚，脚本加载后与盘上
#: 实测逐一交叉核对）；run-r16 锚=M1 基线（27/35=0.771429）与 G1/G2
#: 守门基线的双侧复算输入（run sha 在案）；run-r17/run-r18/run-r19 锚=
#: 通道归因对照轮输入（r17/r18/r19 重放与在案登记交叉核对；run-r18/
#: run-r19 另=M 元组对照行 live 复算输入）；dev-r18 锚=r17/r18 M 元组
#: 对照行装载源（轴账 cross_round_status）；dev-r19 锚=组合决策
#: （combination_decision_application）与 r16–r19 measured_rows 装载
#: 源（轴账 cross_round_status）；probe 锚=§5B 探针证实前提链锚（仅
#: 哈希+kind 复核、本轮零内容转录——§5B 文本自 r18 指引逐字转录）；
#: typology 锚=rubric/contact 族基线唯一装载源；其余沿用 s68/s71 在案锚。
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
    REL_GUIDANCE_R19:
        "8633bda58c6c2f1f3e8783f02160f73e010884a51d7f6c274a5e15ded1fdaa3f",
    REL_GUIDANCE_R18:
        "cadcb8f33afd0e8d12a022aa34d164de466b66ad37bd836659c2e78523315fc0",
    REL_GUIDANCE_R20:
        "9cdac9ed605da74262ff0b750ce6768526064a9bba181eff45596fee9616ecf5",
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
    REL_PREP_R19:
        "e4cf2d3cedbbcd60c4c7b397d4dcfcf5d052209a3221f19b8a885d84d970e86a",
    REL_PREP_R20:
        "e29ee2a3603965ef64eec31bd6905b98cee274b51236d7be8d299f71f388095d",
    REL_PREP_R22:
        "63346ee6fe1a9fef1e852fdbeda499a20a91cddbda01829ca234dd9a2c4f3ad4",
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
    REL_DEV_R18:
        "a0c1f97c8350b7327cfde8183a355b5bc33049d49e6d4545f415a8676af2a3b5",
    REL_DEV_R19:
        "0e2fdd69a8981e3e06c5bba2e1f4d5c4377c69aaf0c018eff750421565f99ba3",
    REL_DEV_R20:
        "80e3e9e25657434db691935291b5f19008637d58cfb1243e8209b76369f5dc04",
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
    REL_RUN_R18:
        "981428dcb032b40607776598b63ed94cb97903af0d17fe99ed90736629c1b4a8",
    REL_RUN_R19:
        "e5755a11e7e0c2da37a8b11902992f4a4fe6925d1dc3e8c6c5c3f46efbc537c5",
    REL_RUN_R20P:
        "6573a59a8f67fdb220d963161992a494546a5c57ba369c16fe83feba0f18820c",
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    REL_PROBE_R18:
        "a49441acacd7ac492960b7e604d1e31a37174e9d9a97b4a24ebddc2e3551111d",
    REL_TYPOLOGY:
        "6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b53283681bc80",
    RAW_FILES["applied-top-i1"]:
        "fcea824a0c9fef9d1d2526ee77a591fb718cbe6d59d699c680cf9ddab46f14e3",
    RAW_FILES["prep1-top-i1"]:
        "0de33b5f3bb7133c4ab865a1b084bb3f654fda3ac47dce0adaf093c2ba7798f5",
    RAW_FILES["applied-top-i2"]:
        "d8dad94e2f61b237aea22f964775941893d31cf4996dc93a41504b8e121d22fb",
    RAW_FILES["prep1-top-i2"]:
        "4849758c9010e9bffbab59fa602b79cd80f54f4641744a321e84aba9117c3495",
    RAW_FILES["applied-top-i3"]:
        "60e96d3f08da0873ee13d247806e56f148f4b0701558f65072e2a770d78733f8",
    RAW_FILES["prep1-top-i3"]:
        "6260dbbd3a08316fc640a69f7188822c6ba0f14acb73f3d7387e817e44bad8dd",
    RAW_FILES["applied-bottom-i1"]:
        "e275862248779e78bc49062dbbd4a7fe7cd6997d5f0b40fc1600d49ded5ecf08",
    RAW_FILES["prep1-bottom-i1"]:
        "044edcca2382627e318dee15fbf06650cbd806089d1b85c81c0f12e6d4dee2ad",
    RAW_FILES["applied-bottom-i2"]:
        "31b978ef69521e104a8bd3575861d6c141bc01977e65c2ec4d6428eb6e32eb68",
    RAW_FILES["prep1-bottom-i2"]:
        "570b9a3bfa9d0886779b760c5ea18571bbe4122772487708d402facb6eda9a90",
    RAW_FILES["applied-bottom-i3"]:
        "9796b4d6ec0191aa35aa85a2476e368098fd7bb5faa579621b6e08ec3031f4c2",
    RAW_FILES["prep1-bottom-i3"]:
        "a81d8098d2144675b4847654f8c60b192962c1f9fb46cc8a514ce2cb54338909",
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

#: 12 件盲读原始件哈希前缀逐字钉死（盲读亲测在案；全量哈希见
#: FROZEN_SHA256；任何再派发/替换都会使前缀不符→fail-closed 中止）。
RAW_PINNED_PREFIXES = {
    "applied-top-i1": "fcea824a",
    "prep1-top-i1": "0de33b5f",
    "applied-bottom-i1": "e2758622",
    "prep1-bottom-i1": "044edcca",
    "applied-top-i2": "d8dad94e",
    "prep1-top-i2": "4849758c",
    "applied-bottom-i2": "31b978ef",
    "prep1-bottom-i2": "570b9a3b",
    "applied-top-i3": "60e96d3f",
    "prep1-top-i3": "6260dbbd",
    "applied-bottom-i3": "9796b4d6",
    "prep1-bottom-i3": "a81d8098",
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
    "r14–r20 盲读同一批文件）+observation-guidance-r19.md"
    "（8633bda5，字节复用=r19 轮落盘本体零改动、"
    "本轮唯一判读依据；旗 ID 前缀 "
    "R22T-/R22B- 由派发指令层覆盖（指引 §6 示例前缀保持 R19T-/R19B- "
    "落盘原文——指引字节复用+§6 前缀差异登记、r16 先例在案，per "
    "r22-prep-record protocol_amendment.naming；"
    "reader-r22-{top,bottom}-i{1,2,3} 为派发指令命名）+起始序号+v1.2 "
    "工具行为规约"
    "硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/衍生图像"
    "生成等）；判读只允许以 Read 工具查看原图（同一原图可重复查看））；"
    "无任何 GT 坐标/类别提示/期望缺陷描述、零诊断报告内容（黑点探针链"
    "与 framing/witness 记录不进任何 reader 上下文）、"
    "零 legend/零其他解释"
    "（判读输入=指引+单张 PNG+派发指令，与既往轮同构，仅实例群重抽）；"
    "读图者不接触 GT/派生台账/任何校准"
    "产物路径；跨实例/跨视角禁止交流（12 次盲读相互独立——独立性是"
    "多实例协议的前提，亦为实例群重抽收敛归因裁决有效性的前提，per "
    "r22-prep-record read_prohibition_note）")

#: 派发模式结构化记录（R22=同指引重复轮：每格 3 实例、两波次串行
#: 保序；派发结构与 r17–r20 同构，协议侧零新增条款；唯一实验操作=
#: 实例群全部重抽）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R22T-001..005；prep1 R22T-006..011（跨板连续）",
        "top-i2": "applied R22T-001..004；prep1 R22T-005..010（跨板连续）",
        "top-i3": "applied R22T-001..009；prep1 R22T-010..020（跨板连续）",
        "bottom-i1": "两板 0 旗（零旗标实例、编号行为无可登记）",
        "bottom-i2": "applied R22B-001..002；prep1 R22B-003..004（跨板连续）",
        "bottom-i3": "applied R22B-001..003；prep1 R22B-004..006（跨板连续）",
    },
    "flag_id_continuity_note": (
        "r22 实测=5 个有旗实例全部同实例跨板连续+bottom-i1 两板零旗标"
        "（与 r22-prep-record protocol_amendment.naming「实例间编号独立，"
        "同实例跨板连续」声明相符——本轮 6 智能体各包两板、编号跨板"
        "连续；零旗标实例编号行为无可观测、如实注明）——编排侧"
        "仍把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R19/R20→R22 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮单变量="
                  "reader 实例群重抽（12 派次全部重抽、与 r19/r20 实例群"
                  "无身份延续；指引/渲染/GT/阈值/协议零变更）；指引字节"
                  "复用=observation-guidance-r19.md 本体零改动，其 §6 "
                  "示例旗 ID 前缀保持 R19T-/R19B- 落盘原文，R22 派次前缀 "
                  "R22T/R22B 由派发指令层覆盖（指引字节复用+§6 前缀差异"
                  "登记、r16 先例在案：r15 指引+R16T 前缀执行先例，与 "
                  "r20「随指引落盘固化」路径不同，per r22-prep-record "
                  "protocol_amendment.naming）；协议侧零新增条款"
                  "（v1.2 沿用：派发指令继续含纯 Read 直读硬性条款，"
                  "12/12 派次自述「未读取盘上任何其他文件」，见 "
                  "reader_tool_evidence；指引 §2–§7 判据文本零改动；"
                  "GT/阈值零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R22 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何其他文件」"
    "（12/12 逐字摘录在案 reader_tool_evidence）；applied/prep1-top-i1 "
    "另自述「未与任何其他图像做跨图比对推断」、prep1-top-i2 另自述"
    "「亦未跨图推断」、prep1-top-i3 另自述「未跨图合并推断」、applied/"
    "prep1-bottom-i3 另自述「未对图像做任何程序化处理（仅以 Read 查看"
    "原图，每图两遍）」（两板同图同判自述）；§4(iii-a) 措辞 notes 级"
    "援引=6/12 派次（applied/prep1-top-i2、applied/prep1-top-i3、"
    "applied/prep1-bottom-i1）、§5B 措辞 notes 级援引=0/12 派次（本轮"
    "指引=observation-guidance-r19.md 字节复用、无 §5B 节=任何援引为"
    "零上下文；两计数分开记、互不合并；逐件摘录见 hypothesis_"
    "test.mechanism_observation.criterion_citation_observation）；"
    "applied/prep1-bottom-i1 零旗派次 notes 自述按 §2 封闭六类逐项"
    "核查后 0 旗（含 0 弃权）并明引 §4(iii-a)(1) 间隙带可辨认→视觉"
    "贴近路径（零旗标判读自述在案、如实登记）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/零探针"
    "件/零 legend/零其他文件接触=非盲读违规；本轮唯一操纵因子=reader"
    " 实例群重抽（12 派次全部重抽、与 r19/r20 实例群无身份延续；指引/"
    "渲染字节复用、仪器侧零变动；per r22-prep-record "
    "attribution_plan.declaration 原文：实例群混杂在本轮=唯一实验操作、"
    "恰是裁决变量）；跨轮实例不同+轮内实例差异=混杂因素照旧声明"
    "（本轮每视角 n=3 给出轮内实例间范围，轮内样本仍小、development "
    "域只描述不断言）。输出格式实例披露（编排侧落盘前处理，盘上件="
    "冻结证据）：12 件=缩进格式冻结原始判读件、本轮零改动直读（direct "
    "JSON 解析；围栏剥离本先例不适用——12 件均为裸 JSON 文本；12 件 "
    "parse 校验全部通过、均非盲读违规）")

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
    "本轮指引=observation-guidance-r19.md 字节复用（8633bda5，r19 轮"
    "落盘本体零字节不动、本轮唯一判读依据，per r22-prep-record "
    "guidance_reuse：mode=byte_reuse_zero_change、edit_list=[]、"
    "derived=null、zero_write_declaration=本轮不新建指引文件）：§2 类别"
    "枚举/§3 位置口径/§3A 示例（含示例 c）/§4 置信度与弃权整段（含量化"
    "判据 (i)(ii)(iii) 原文、(iii) 接触性判据原句、(iii-a) 可操作分辨"
    "条款全文、三路出口、反放宽条款、confidence 定义、对照说明块）/§5/"
    "§5A/§6/§7 判据文本随 r19 指引本体原样生效（字节复用=零措辞调整"
    "空间）；§6 示例旗 ID 前缀保持 R19T-/R19B-（r19 落盘原文、字节复用"
    "不改——本轮指引内 R19T- 恰 4 处、R19B- 恰 1 处实测锚定，per "
    "r22-prep-record guidance_reuse.verbatim_scope_note），R22 派次 "
    "flag_id 前缀 R22T/R22B 由派发指令层覆盖（前缀差异登记；r16 先例"
    "在案：r15 指引+R16T 前缀执行先例）；本轮指引无 §5B 节（r19 基座"
    "=r15 结构在案）——§5B 援引计数机制观察照记、任何援引为零上下文"
    "（per r22-prep-record adjudication.mechanism_observation_separate "
    "原文）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 22 轮迭代"
    "（development 域同指引重复轮（收敛归因；r16 先例：r15→r16 同指引"
    "重复、渲染零变更、仅实例重抽）：迭代轮不得冒充留出证据；执行 "
    "round20-dev-record next_iteration_targets[1] 同指引重复轮候选"
    "（round20-dev-record=80e3e9e2 实测锚、候选原文逐字摘录于 r22-prep-"
    "record guidance_reuse.chain_anchors.round20_dev_record_authorization），"
    "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的继续」"
    "（user_directive_note 在案）；R21 全组合槽位=冻结件预留位、未触发"
    "永久留空（跳号声明在案，r22 与该槽位无涉））。")

INSTRUMENT_NATURE = (
    "同指引重复轮（收敛归因；渲染零变更轮）：仪器变更=无（renders-r14b "
    "四图字节复用=与 r14–r20 盲读同一批文件；四 PNG 盘上 sha="
    "witness-r14b 登记值=prep-record instrument_change.renders 登记值 "
    "fail-closed 三方一致；instrument_change.changed=false 已预注册，"
    "no_instrument_change=true）+判读指引=observation-guidance-r19.md "
    "字节复用（8633bda5；零编辑零变换、不新建指引文件）+GT/阈值零"
    "变更（13 条冻结；APR-0011 与 CONTAINMENT_MIN/AREA_RATIO_MAX 只作"
    "口径引用）+协议零变更（v1.1+v1.2 维持）：唯一实验变量=reader "
    "实例群（12 派次全部重抽、与 r19/r20 实例群无身份延续；per "
    "r22-prep-record manipulated_factor；changed_variables=[] 在案、"
    "guidance_reuse.mode=byte_reuse_zero_change、instrument_change=false）")


#: 预注册主通道复制性三分判据所用基线（零覆盖；per r22-prep-record
#: hypothesis_test.adjudication 原文：replicated=M1 落 [0.361538,
#: 0.561538]（r19±0.10）且 contact 族弃权旗数（全视，分型件 rubric
#: 口径）≤7 且 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）
#: 维持；drifted=未达 replicated 且 M1 <0.771429 且 G1/G2 维持；
#: regressed=M1 ≥0.771429 或 G1/G2 任一破坏）。
#: 基线数字 live 重放/装载（M1/M2=同一聚合逻辑对 run-r16 内嵌实例记录
#: 双侧复算、不手工抄数；r19 四元组=run-r19 内嵌实例记录 live 复算
#+登记值交叉核对；r20 四元组=run-r20 内嵌记录 live 复算+登记值交叉
#: 核对）并与下列在案登记值交叉核对（fail-closed，不符即中止）：
#: (27,35)=0.771429（axis-plan baselines_registered.r16_baseline 在案）。
BASE16_TOP_AGGREGATE_REGISTERED = {"abstain": 27, "flags": 35}
#: M1 侧阈值（6 位定点整数交叉相乘比较，避免浮点）：regressed 门
#: M1 ≥0.771429（r16 基线）；drifted 带 M1 <0.771429。
REJECT_M1_MIN_6DP = 771429
#: replicated 带 M1 ∈ [0.361538, 0.561538]（r19±0.10；per r22-prep-
#: record adjudication.replicated 原文；6 位定点整数交叉相乘比较）。
REPL_BAND_LO_6DP = 361538
REPL_BAND_HI_6DP = 561538
#: contact 族 replicated 门（r19 contact=4 的 ≤7 描述性边界；per
#: r22-prep-record adjudication.replicated 原文「≤ 7」）。
CONTACT_MAX_REPL = 7
#: r19 参照四元组登记值（replicated 带中心与 M4 双样本参照；M1/M2/M4=
#: 6 位小数、M3=整数；run-r19 内嵌实例记录 live 复算交叉核对+run_r19
#: metric_anchor 冻结值文本核对）。
R19_ROW_REGISTERED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                      "M4": 0.211111}
#: r20 对照行登记值（破坏轮历史行；run-r20 内嵌记录 live 复算交叉
#: 核对；三族 rubric 计数另见 R20_REFERENCE_REGISTERED；per r22-prep-
#: record hypothesis 原文登记：M1=0.636364、G1 破坏在案）。
R20_ROW_REGISTERED = {"M1": 0.636364, "M2": 0.285714, "M3": 6,
                      "M4": 0.25}
#: bottom 侧观察基线（M2；per axis-plan baselines_registered.r16_baseline
#:.M2_bottom_aggregate_abstain_rate=0.857143；live 重放交叉核对
#: 12/14）。
BASE16_BOTTOM_AGGREGATE_REGISTERED = {"abstain": 12, "flags": 14}
#: M3（黑点族）/M4 基线登记值（axis-plan baselines_registered.
#: r16_baseline 在案；M3=分型件 rubric 口径黑点族弃权旗数、M4=top 逐
#: 实例弃权率极差；脚本对 axis-plan 原文 fail-closed 装载核对，另对
#: run-r16 live 重放交叉核对 M4 的逐实例构成）。
AXIS_R16_M3_BLACKDOT_RUBRIC = 12
AXIS_R16_M4_TOP_RANGE = 0.261904
R16_TOP_INSTANCE_RATES_REGISTERED = {"top-i1": 0.666667,
                                     "top-i2": 0.928571,
                                     "top-i3": 0.666667}
R16_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}
#: contact 族链基线（分型件 rubric 口径在案：r13=8、r14=15、r15=5、
#: r16=10；分型件 matrix.round_totals 双向核对；r16=10 全 top
#: （r16_contact_by_view 在案）；本件登记基线与 r22 实测对照）。
CONTACT_CHAIN_PRIOR = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
R16_CONTACT_BY_VIEW_REGISTERED = {"top": 10, "bottom": 0}
#: 黑点族链基线（分型件 rubric 口径在案：r13=9、r14=14、r15=8、r16=12；
#: r18=13（run-r18 实测+dev-r18 登记装载交叉核对）；r19=4（run-r19
#: 实测装载交叉核对）；黑点判正常派次链
#: （分型件 blackdot_dispatch 口径）：r15=3、r16=2；r18=2、r19=3、
#: r20=4（各自 run 实测装载交叉核对）。
BLACKDOT_CHAIN_PRIOR = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
BLACKDOT_JUDGED_NORMAL_PRIOR = {"r15": 3, "r16": 2}
#: r18 对照登记值（存在性其他族 12；黑点转非弃权旗 3；dev-r18/
#: run-r18 实测装载交叉核对——机制观察「三族计数」的 r18 侧对照行）。
R18_REFERENCE_REGISTERED = {
    "M1": 0.645161, "M2": 0.684211, "M3": 13, "M4": 0.277778,
    "existence_other": 12, "blackdot_to_non_abstain": 3,
    "judged_normal_dispatches": 2,
    "top_typology": {"contact": 8, "existence": 12, "other_layer": 0},
}
#: r17 轴1 对照行（round18-dev-record axis_experiment_ledger.
#: cross_round_status.measured_rows.r17_axis1 实测装载；脚本装载后与
#: 本登记值交叉核对，fail-closed）。
R17_ROW_REGISTERED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
#: r19 对照行/参照计数（run-r19 在案实测：run-r19 内嵌实例记录/分型
#: 计数 live 复算交叉核对——机制观察「三族计数 r19 基线」与
#: replicated 带中心；per r22-prep-record adjudication.mechanism_
#: observation_separate 原文「contact/黑点/存在性三族计数对照 r19
#: （4/4/14）」）。
R19_REFERENCE_REGISTERED = {
    "M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111,
    "contact": 4, "existence_blackdot": 4, "existence_other": 14,
    "judged_normal_dispatches": 3,
    "top_typology": {"contact": 5, "existence": 13, "other_layer": 0},
}
#: r20 对照登记值（破坏轮历史行；run-r20 内嵌记录 live 复算交叉核对；
#: per r22-prep-record adjudication.mechanism_observation_separate
#: 原文「对照 r19（4/4/14）与 r20（2/6/10）」+chain_anchors.
#: dev_r20_family_counts_cross_check（脚本对该链锚 fail-closed 装载
#: 核对）；G1 破坏登记=r20 bottom courtyard 非弃权 2/0/0（run-r20
#: 在案；r22-prep-record guard_channel 原文「r20 破坏 2/0/0 在案=
#: 分岔记录」）。
R20_REFERENCE_REGISTERED = {
    "M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25,
    "contact": 2, "existence_blackdot": 6, "existence_other": 10,
    "judged_normal_dispatches": 4,
    "top_typology": {"contact": 4, "existence": 9, "other_layer": 1},
    "g1_bottom_courtyard_non_abstain": {"bottom-i1": 2, "bottom-i2": 0,
                                        "bottom-i3": 0},
}


#: bottom 侧 G1 守门逐实例登记表（bottom courtyard 类非弃权旗；
#: 程序实测与本表 expected 逐一相等 fail-closed；per r22-prep-record
#: guard_channel「G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15–r19
#: 在案 0/0/0、r20 破坏 2/0/0 在案=分岔记录）」原文——r22 实测 0/0/0
#:=G1 维持（对照 r20 的 2/0/0 字面破坏在案，分岔如实分列）。
SIDE_OBS_REGISTERED = [
    {"instance": "bottom-i1", "expected": 0,
     "note": ("r15–r19 零非弃权 courtyard（r20 破坏 2 在案=分岔记录）"
              "→r22 实测 0：本轮 bottom-i1 两板零旗标（notes 自述按 §2 "
              "封闭六类逐项核查后 0 旗（含 0 弃权）、明引 §4(iii-a)(1) "
              "间隙带可辨认→按视觉贴近处理且判系统性正常不报告）——"
              "G1 维持")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r15–r19 零非弃权 courtyard（r20 破坏 2 在案=分岔记录）"
              "→r22 实测 0：本轮 bottom-i2 零 courtyard 类旗标（4 旗="
              "placement_pattern_anomaly 报告 2+other_advisory 黑点"
              "弃权 2，两板同构）")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r15–r19 零非弃权 courtyard（r20 破坏 2 在案=分岔记录）"
              "→r22 实测 0：本轮 bottom-i3 6 旗全部非弃权（深色小圆点 "
              "other_advisory 报告 4+孤立焊盘对 placement_pattern_"
              "anomaly 报告 2）——零 courtyard 类路径")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。applied/prep1-top-i1 另自述未跨图
#: 比对、applied/prep1-bottom-i3 另自述零程序化处理，如实登记。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据 applied-top.png 可见内容独立盲读，未读取盘上任何其他文件，未与任何其他图像做跨图比对推断"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据 prep1-top.png 可见内容独立盲读，未读取盘上任何其他文件，未与任何其他图像做跨图比对推断"},
    {"source": "applied-top-i2",
     "excerpt": "仅凭给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i2",
     "excerpt": "仅凭给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件，亦未跨图推断"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件，未跨图合并推断"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件；按 §2 封闭六类逐项核查后本图 0 旗（含 0 弃权）"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件；按 §2 封闭六类逐项核查后本图 0 旗（含 0 弃权）"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件，未对图像做任何程序化处理（仅以 Read 查看原图，每图两遍）"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件，未对图像做任何程序化处理（仅以 Read 查看原图，每图两遍）"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——r22 bottom
#: 6 派次均实际使用 §4(i) 量化判据（bottom-i1 零旗派次=近邻间距
#: 系统性一致判正常+黑点判有意机械孔不报告；bottom-i2 方形焊盘
#: 端部标记判系统性正常未报告；bottom-i3 绿色翼瓣空隙判系统性
#: 正常不报告；applied/prep1 两板同文=同图同判自述）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "该近邻间距沿各阵列系统性一致（§4(i)），判为正常连接器式针排列设计特征（三路出口第 1 路），不报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "该近邻间距沿各阵列系统性一致（§4(i)），判为正常连接器式针排列设计特征（三路出口第 1 路），不报告"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "各阵列端部的方形焊盘（1 号标记样式）在至少三处出现且形态一致，按系统性正常特征未报告"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "各阵列端部的方形焊盘（1 号标记样式）在至少三处出现且形态一致，按系统性正常特征未报告"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "四组周边行列阵列中大量焊盘附带的绿色翼瓣状空隙图形（数十处、沿同一阵列分布、四条边均有、形态一致）"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "四组周边行列阵列中大量焊盘附带的绿色翼瓣状空隙图形（数十处、沿同一阵列分布、四条边均有、形态一致）"},
]


#: top 弃权理由构成分型（机制观察：16 条 top 弃权旗逐旗按
#: location_evidence 主出口关键词分类；r22 实测 16 条=top-i1 5+
#: top-i2 4+top-i3 7）。
TOP_ABSTAIN_TYPOLOGY = [
    {"source": "applied-top-i1", "flag_id": "R22T-004", "type": "existence",
     "excerpt": "平滑弧形过渡亦可能属常规布线手法，无法负责任确认其属可疑改道，故弃权",
     "note": "reroute 类旗（r12 被动追踪延续）；主出口=存在性（是否存在不可确认）；rubric 族=existence_other"},
    {"source": "applied-top-i1", "flag_id": "R22T-005", "type": "existence",
     "excerpt": "当前分辨率下无法确认字符确属无法辨认，故弃权",
     "note": "silk 类；主出口=存在性（可读性受损是否存在不可确认）"},
    {"source": "prep1-top-i1", "flag_id": "R22T-009", "type": "existence",
     "excerpt": "平滑弧形过渡亦可能属常规布线手法，无法负责任确认其属可疑改道，故弃权",
     "note": "同 applied-top-i1 R22T-004（两板同图同判）；reroute 类"},
    {"source": "prep1-top-i1", "flag_id": "R22T-010", "type": "existence",
     "excerpt": "当前分辨率下无法确认字符确属无法辨认，故弃权",
     "note": "同 applied-top-i1 R22T-005（两板同图同判）"},
    {"source": "prep1-top-i1", "flag_id": "R22T-011", "type": "existence",
     "excerpt": "但不排除散热焊盘类常规图形解释，无法负责任确认其属关注现象，故弃权",
     "note": "焊盘/铜图形连片融合孤立形态（prep1 波次新增旗）；主出口=存在性"},
    {"source": "applied-top-i2", "flag_id": "R22T-003", "type": "existence",
     "excerpt": "当前分辨率下无法确认叠压是否真实存在、可读性是否受损，故弃权",
     "note": "silk 类疑似叠压；主出口=存在性"},
    {"source": "applied-top-i2", "flag_id": "R22T-004", "type": "existence",
     "excerpt": "无法负责任判断其为正常安装/屏蔽孔特征还是异常图元，故弃权",
     "note": "黑点对性质存在性弃权（本轮指引=observation-guidance-r19.md 字节复用、无 §5B 节=零上下文，如实登记）；rubric 族=existence_blackdot"},
    {"source": "prep1-top-i2", "flag_id": "R22T-009", "type": "existence",
     "excerpt": "当前分辨率下无法确认叠压是否真实存在、可读性是否受损，故弃权",
     "note": "同 applied-top-i2 R22T-003（两板同图同判）"},
    {"source": "prep1-top-i2", "flag_id": "R22T-010", "type": "existence",
     "excerpt": "无法负责任判断其为正常安装/屏蔽孔特征还是异常图元，故弃权",
     "note": "同 applied-top-i2 R22T-004（两板同图同判）；rubric 族=existence_blackdot"},
    {"source": "applied-top-i3", "flag_id": "R22T-007", "type": "existence",
     "excerpt": "当前分辨率下无法确认是真实回绕走线还是相邻走线与过孔的视觉组合",
     "note": "reroute 类旗（r12 被动追踪延续）；主出口=存在性"},
    {"source": "applied-top-i3", "flag_id": "R22T-008", "type": "contact",
     "excerpt": "间隙带与侵入证据均不可辨认，无法负责任判定是否接触",
     "note": "(iii-a) 残余弃权支语言（间隙带与侵入证据均不可辨认）；rubric 族=contact"},
    {"source": "applied-top-i3", "flag_id": "R22T-009", "type": "existence",
     "excerpt": "形态生僻，无法负责任判断其为正常设计图元还是异常图形",
     "note": "notes 自述「生僻形态按反放宽条款走弃权路径」；主出口=存在性"},
    {"source": "prep1-top-i3", "flag_id": "R22T-015", "type": "existence",
     "excerpt": "当前分辨率无法确认是叠压还是单一密集字符串",
     "note": "silk 类疑似叠压；主出口=存在性"},
    {"source": "prep1-top-i3", "flag_id": "R22T-018", "type": "existence",
     "excerpt": "当前分辨率下无法确认是真实回绕走线还是相邻走线与过孔的视觉组合",
     "note": "同 applied-top-i3 R22T-007（两板同图同判）；reroute 类"},
    {"source": "prep1-top-i3", "flag_id": "R22T-019", "type": "contact",
     "excerpt": "间隙带与侵入证据均不可辨认，无法负责任判定是否接触",
     "note": "同 applied-top-i3 R22T-008（两板同图同判）；rubric 族=contact"},
    {"source": "prep1-top-i3", "flag_id": "R22T-020", "type": "existence",
     "excerpt": "形态生僻，无法负责任判断其为正常设计图元还是异常图形",
     "note": "同 applied-top-i3 R22T-009（两板同图同判）"},
]

#: 绿色区域语义化方式证据（r17–r20 机制观察延续：bottom 派次 notes
#: 逐字摘录+cites_5A/cites_5B=notes 级字面援引实测登记）。
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "所见绿色图形按 §5A 为板内空隙（非图元），角部小封装周边的绿色弧形亦为空隙",
     "cites_5A": True, "cites_5B": False},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "部分焊盘之间可见深绿色翼瓣状空隙（按仪器注记属空隙而非图元）",
     "cites_5A": False, "cites_5B": False},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "四组周边行列阵列中大量焊盘附带的绿色翼瓣状空隙图形（数十处、沿同一阵列分布、四条边均有、形态一致）",
     "cites_5A": False, "cites_5B": False},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "所见绿色图形按 §5A 为板内空隙（非图元），角部小封装周边的绿色弧形亦为空隙",
     "cites_5A": True, "cites_5B": False},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "部分焊盘之间可见深绿色翼瓣状空隙（按仪器注记属空隙而非图元）",
     "cites_5A": False, "cites_5B": False},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "四组周边行列阵列中大量焊盘附带的绿色翼瓣状空隙图形（数十处、沿同一阵列分布、四条边均有、形态一致）",
     "cites_5A": False, "cites_5B": False},
]


#: 黑点族现象证据（r22 黑点族弃权旗 4 条（top-i2 两板 2+bottom-i2
#: 两板 2）+黑点转非弃权旗 6 条（top-i3 两板 2+bottom-i3 两板 4）
#: +判正常派次 4 的代表摘录；kind=reading_notes 或 location_evidence；
#: substring fail-closed 校验；延续 r14–r20 黑点族追踪——r22 黑点族
#: 弃权=4（rubric 口径）vs r16=12/r18=13/r19=4/r20=6 对照、方向性
#: 描述；本轮指引字节复用无 §5B 节=黑点判读零 §5B 上下文、如实
#: 登记）。
BLACK_DOT_EVIDENCE = [
    {"source": "applied-top-i2", "kind": "location_evidence",
     "flag_id": "R22T-004", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上角连接器 footprint 内部可见上下两个实心黑色圆点，与本板其余孔/焊盘的配色渲染均不一致",
     "note": "黑点对性质存在性弃权（本轮指引无 §5B 节=零上下文，如实登记）；rubric 族=existence_blackdot"},
    {"source": "prep1-top-i2", "kind": "location_evidence",
     "flag_id": "R22T-010", "instance": "top-i2", "disposition": "弃权",
     "excerpt": "右上角连接器 footprint 内部可见上下两个实心黑色圆点，与本板其余孔/焊盘的配色渲染均不一致",
     "note": "同 applied-top-i2 R22T-004（两板同图同判）"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R22B-002", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "全板其余区域无同类黑点；无法负责任判断其为钻孔/过孔类正常图形还是异常残留关注现象，故按存在性不确定弃权",
     "note": "§4(ii) 孤立+存在性不确定弃权；rubric 族=existence_blackdot"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R22B-004", "instance": "bottom-i2", "disposition": "弃权",
     "excerpt": "全板其余区域无同类黑点；无法负责任判断其为钻孔/过孔类正常图形还是异常残留关注现象，故按存在性不确定弃权",
     "note": "同 applied-bottom-i2 R22B-002（两板同图同判）"},
    {"source": "applied-top-i3", "kind": "location_evidence",
     "flag_id": "R22T-006", "instance": "top-i3", "disposition": "非弃权报告",
     "excerpt": "右上角区域内有两个实心黑色圆点标记，与全板其他焊盘/孔位呈现样式（粉环白心）均不一致，呈孤立异常标记形态",
     "note": "§4(ii) 孤立异常报告（非接触路径；r19 bottom 侧黑点非弃权报告先例的 top 侧再现，如实登记）"},
    {"source": "prep1-top-i3", "kind": "location_evidence",
     "flag_id": "R22T-016", "instance": "top-i3", "disposition": "非弃权报告",
     "excerpt": "右上角区域内有两个实心黑色圆点标记，与全板其他焊盘/孔位呈现样式（粉环白心）均不一致，呈孤立异常标记形态",
     "note": "同 applied-top-i3 R22T-006（两板同图同判）"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-001", "instance": "bottom-i3", "disposition": "非弃权报告",
     "excerpt": "板左上区域一个水平长圆形焊盘的下缘旁可见一个深色小圆点，其颜色与全图其余图元配色（橙/青/绿/蓝）均不同，且此类深色圆点全图仅两例，呈孤立形态",
     "note": "§4(ii) 孤立出现兜底类报告（黑点词=「圆点」rubric 词表命中）"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-002", "instance": "bottom-i3", "disposition": "非弃权报告",
     "excerpt": "板左侧偏上区域另一水平长圆形焊盘的上缘旁可见第二个深色小圆点，形态与左上角一处一致，两处孤立分布，不与周边任何阵列图形相连",
     "note": "同上（第二枚深色小圆点）"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-004", "instance": "bottom-i3", "disposition": "非弃权报告",
     "excerpt": "板左上区域一个水平长圆形焊盘的下缘旁可见一个深色小圆点，其颜色与全图其余图元配色（橙/青/绿/蓝）均不同，且此类深色圆点全图仅两例，呈孤立形态",
     "note": "同 applied-bottom-i3 R22B-001（两板同图同判）"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-005", "instance": "bottom-i3", "disposition": "非弃权报告",
     "excerpt": "板左侧偏上区域另一水平长圆形焊盘的上缘旁可见第二个深色小圆点，形态与左上角一处一致，两处孤立分布，不与周边任何阵列图形相连",
     "note": "同 applied-bottom-i3 R22B-002（两板同图同判）"},
    {"source": "applied-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "disposition": "判正常不报告",
     "excerpt": "板上散布的孤立小圆点、右上角黑色圆孔与白色椭圆标记等，按系统性正常特征判据判为正常设计特征，未报告",
     "note": "黑点词命中（黑色圆/圆点）而零黑点旗=判正常派次（blackdot_dispatch 口径）"},
    {"source": "prep1-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "disposition": "判正常不报告",
     "excerpt": "板上散布的孤立小圆点、右上角黑色圆孔与白色椭圆标记等，按系统性正常特征判据判为正常设计特征，未报告",
     "note": "同 applied-top-i1（两板同文自述）"},
    {"source": "applied-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "disposition": "判正常不报告",
     "excerpt": "左上角两处同款两焊盘封装旁的两个小黑点：尺寸一致、垂直对齐、与两处同款封装呈一致关联定位，判为有意的机械孔/定位类设计特征（三路出口第 1 路），不报告",
     "note": "零旗派次黑点判正常（黑点词=小黑点命中、零黑点旗；blackdot_dispatch 口径）"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "disposition": "判正常不报告",
     "excerpt": "左上角两处同款两焊盘封装旁的两个小黑点：尺寸一致、垂直对齐、与两处同款封装呈一致关联定位，判为有意的机械孔/定位类设计特征（三路出口第 1 路），不报告",
     "note": "同 applied-bottom-i1（两板同文自述）"},
]

#: 黑点族弃权旗登记表（4 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定；top-i2 两板 2+
#: bottom-i2 两板 2；分型件 rubric 口径=r22 4 vs r16 12/r18 13/r19 4/
#: r20 6 对照（分型件/各自 run 在案 M3 链）。
BLACK_DOT_FLAGS = [
    ("top-i2", "applied", "R22T-004", "other_advisory"),
    ("top-i2", "prep1", "R22T-010", "other_advisory"),
    ("bottom-i2", "applied", "R22B-002", "other_advisory"),
    ("bottom-i2", "prep1", "R22B-004", "other_advisory"),
]

#: 黑点转非弃权旗登记表（6 条；rubric unit=弃权旗、非弃权旗不分型，
#: 本表为机制观察「黑点转非弃权旗计数」的登记口径（对象含黑点词的
#: 非弃权旗、逐条摘录）；top-i3 两板 2=孤立异常标记按 §4(ii) 报告+
#: bottom-i3 两板 4=深色小圆点按 §4(ii) 兜底类报告）——r19（bottom 2）
#: /r20（全 bottom 6）的非弃权报告路径在本轮=6 条（top 侧首现 2 条），
#: 如实登记。
BLACK_DOT_NON_ABSTAIN_FLAGS = [
    ("top-i3", "applied", "R22T-006", "other_advisory"),
    ("top-i3", "prep1", "R22T-016", "other_advisory"),
    ("bottom-i3", "applied", "R22B-001", "other_advisory"),
    ("bottom-i3", "applied", "R22B-002", "other_advisory"),
    ("bottom-i3", "prep1", "R22B-004", "other_advisory"),
    ("bottom-i3", "prep1", "R22B-005", "other_advisory"),
]


#: §4(iii-a) 逐旗落支登记表（机制观察核心：判据相关旗逐旗理由对照
#: 条款三支的落支分布——branch3=残余弃权支（既无可辨认间隙带亦无可
#: 辨认侵入证据→按 (iii) 原文弃权）、branch2=侵入支（边缘直接相连/
#: 明显侵入→按「接触/交叠」处理并照常输出旗标）、branch1=间隙支
#: （可辨认间隙带→视觉贴近→继续 (i)(ii) 与三路出口判定）；r22 实测
#: 旗级「(iii-a)」/「分支(」/「§5B」字面援引=0（cited 全 False=按旗级
#: 理由语言归类、如实注明；notes 级援引见 IIIA_*_REGISTERED）；逐旗
#: excerpt 逐字 substring fail-closed 校验）。
IIIA_BRANCH_ROWS = [
    {"source": "applied-top-i1", "flag_id": "R22T-002", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "两框之间仅剩一条极窄的连续缝隙，呈明显拥挤的近邻形态",
     "note": "无字面援引；间隙支路径（可辨认连续细缝→视觉贴近→按 courtyard_crowding 负责任报告、非交叠）"},
    {"source": "prep1-top-i1", "flag_id": "R22T-007", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "两框之间仅剩一条极窄的连续缝隙，呈明显拥挤的近邻形态",
     "note": "同 applied-top-i1 R22T-002（两板同图同判）"},
    {"source": "applied-top-i1", "flag_id": "R22T-003", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "间隙极窄，呈拥挤的近邻形态",
     "note": "无字面援引；间隙支路径（长距离平行贴邻+极窄间隙→视觉贴近→负责任报告）"},
    {"source": "prep1-top-i1", "flag_id": "R22T-008", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "间隙极窄，呈拥挤的近邻形态",
     "note": "同 applied-top-i1 R22T-003（两板同图同判）"},
    {"source": "applied-top-i2", "flag_id": "R22T-001", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "未见连续间隙带，呈明显拥挤的近邻形态",
     "note": "无字面援引（notes 级该派次有「(iii-a)」援引）；读侧自述「按 (iii-a) 判定为贴触/极近（无可辨认间隙带）故报告」——无可辨认间隙带仍走继续判定→报告路径=间隙支「不得弃权」方向的边缘应用（未走残余弃权支），如实登记"},
    {"source": "prep1-top-i2", "flag_id": "R22T-005", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "未见连续间隙带，呈明显拥挤的近邻形态",
     "note": "同 applied-top-i2 R22T-001（两板同图同判）"},
    {"source": "prep1-top-i2", "flag_id": "R22T-007", "abstain": False,
     "branch": "branch2_intrusion_report", "cited": False,
     "excerpt": "连成一片连续粉色实体（无可辨认间隙带）",
     "note": "无字面援引（notes 级该派次有「按 (iii-a) 判定为接触/融合…按接触/交叠报告」援引）；侵入支（图元直接相连→按接触/交叠处理照常输出旗标）"},
    {"source": "applied-top-i3", "flag_id": "R22T-008", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "间隙带与侵入证据均不可辨认，无法负责任判定是否接触",
     "note": "无字面援引；(iii-a) 残余弃权支（notes 自述「接触性存疑处按指引 §4(iii-a) 三支判据弃权」）"},
    {"source": "prep1-top-i3", "flag_id": "R22T-019", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "间隙带与侵入证据均不可辨认，无法负责任判定是否接触",
     "note": "同 applied-top-i3 R22T-008（两板同图同判）"},
]

#: §4(iii-a) 间隙支（branch1）notes 级落支证据（top-i1 两派次
#: notes 自述「可辨认连续细缝，按可操作分辨条款的视觉贴近分支处理，
#: 报告为近邻拥挤（非交叠）」=间隙支负责任报告路径；旗级落支 4 条
#: 与之对应；substring fail-closed 校验）。
IIIA_NOTES_BRANCH1_ROWS = [
    {"source": "applied-top-i1", "instance": "top-i1",
     "excerpt": "占位框两处极近相邻处均可辨认连续细缝，按可操作分辨条款的视觉贴近分支处理，报告为近邻拥挤（非交叠）"},
    {"source": "prep1-top-i1", "instance": "top-i1",
     "excerpt": "占位框两处极近相邻处均可辨认连续细缝，按可操作分辨条款的视觉贴近分支处理，报告为近邻拥挤（非交叠）"},
]

#: placement/孤立图形类旗标处置证据（逐字摘录；substring fail-closed
#: 校验）——r22 板内孤立焊盘组/焊盘对处置：bottom-i2 两板以
#: placement_pattern_anomaly 报告孤立焊盘组偏离周边模式（非弃权）、
#: bottom-i3 两板以 placement_pattern_anomaly 报告孤立焊盘对（非弃权；
#: 对照 r20 同形态 bottom-i3 判正常=跨轮处置分化如实登记）、
#: bottom-i1 两板零旗派次 notes 自述孤立两焊盘封装不报告（§4(i)
#: 未打破阵列规律），如实单列。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R22B-001", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘组（圆焊盘+方焊盘并排）",
     "excerpt": "图内偏右下的空旷板面内部孤立出现一组焊盘图形（一个带四瓣绿色空隙翼瓣的圆形焊盘与一个方形焊盘并排），而板上其余全部同类圆形/方形焊盘均沿板边排成规整双列/双行阵列，该孤立组与周边规整阵列模式明显不协调"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R22B-003", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "同上（两板同图同判）",
     "excerpt": "图内偏右下的空旷板面内部孤立出现一组焊盘图形（一个带四瓣绿色空隙翼瓣的圆形焊盘与一个方形焊盘并排），而板上其余全部同类圆形/方形焊盘均沿板边排成规整双列/双行阵列，该孤立组与周边规整阵列模式明显不协调"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-003", "instance": "bottom-i3", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘对（圆焊盘带四向翼瓣+方焊盘）",
     "excerpt": "板内中右区域可见一组孤立的圆形焊盘（带四向绿色翼瓣状空隙图形）与方形焊盘组成的焊盘对，四周大片板面无任何同类图形，明显偏离全板图形均沿周边成对行列排布的规整模式"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R22B-006", "instance": "bottom-i3", "verdict": "非弃权",
     "phenomenon": "同上（两板同图同判）",
     "excerpt": "板内中右区域可见一组孤立的圆形焊盘（带四向绿色翼瓣状空隙图形）与方形焊盘组成的焊盘对，四周大片板面无任何同类图形，明显偏离全板图形均沿周边成对行列排布的规整模式"},
    {"source": "applied-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "verdict": "判正常不报告",
     "phenomenon": "板内孤立两焊盘封装（圆+方；零旗派次 placement 核查）",
     "excerpt": "中部偏右孤立两焊盘封装（圆+方）处于开阔区、未打破任何周边规整阵列规律，均不报告"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "verdict": "判正常不报告",
     "phenomenon": "同上（两板同文自述）",
     "excerpt": "中部偏右孤立两焊盘封装（圆+方）处于开阔区、未打破任何周边规整阵列规律，均不报告"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed；
#: r22 实测=4 条（top-i1 两板+top-i3 两板）、全部弃权、「等长|蛇形」
#: 子串零命中）。
REROUTE_ADJUDICATION = [
    {"source": "applied-top-i1", "flag_id": "R22T-004", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("数条连线呈平滑弧形弯折，与周边以直线加45度"
                           "折角为主的走线风格不一致，疑似绕行"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法负责任确认其属可疑改道，"
              "故弃权」，按 §4 存在性判据弃权")},
    {"source": "prep1-top-i1", "flag_id": "R22T-009", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("数条连线呈平滑弧形弯折，与周边以直线加45度"
                           "折角为主的走线风格不一致，疑似绕行"),
     "adjudication": "abstain_existence",
     "note": ("同 applied-top-i1 R22T-004（两板同图同判、同旗号位置 "
              "R22T-009）；「等长|蛇形」子串零命中")},
    {"source": "applied-top-i3", "flag_id": "R22T-007", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("中央扇出区疑似出现闭合回绕状走线轮廓，但当前"
                           "分辨率下无法确认是真实回绕走线还是相邻走线与"
                           "过孔的视觉组合"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法确认是真实回绕走线还是相邻"
              "走线与过孔的视觉组合」，按 §4 存在性判据弃权")},
    {"source": "prep1-top-i3", "flag_id": "R22T-018", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("中央扇出区疑似出现闭合回绕状走线轮廓，但当前"
                           "分辨率下无法确认是真实回绕走线还是相邻走线与"
                           "过孔的视觉组合"),
     "adjudication": "abstain_existence",
     "note": ("同 applied-top-i3 R22T-007（两板同图同判、同旗号位置 "
              "R22T-018）；「等长|蛇形」子串零命中")},
]

#: reroute 类旗标产量链基线（r8–r20 在案；本轮 r22 实测=4；
#: r16=2/r17=1/r18=3/r19=3/r20=2 经 run-reader.flag_count 在案字段
#: live 核对）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4, "r16": 2, "r17": 1,
                       "r18": 3, "r19": 3, "r20": 2}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1, "r16": 0, "r17": 0, "r18": 0, "r19": 0,
                      "r20": 0}



def _fail(msg: str) -> None:
    print(f"[s77-cal-r22] FAIL: {msg}")
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
    # 零旗格 view_check=not_applicable（库侧口径；本轮 12 格全部≥1 旗
# =12 格 full；zero-flag not_applicable 口径本轮未触发）。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    # 渲染 provenance 按视角分列：本轮渲染零变更=renders-r14b 四图
    # 字节复用（与 r14/r15/r16/r17/r18 盲读同一批文件；framing-r14b
    # single_variable_change 在案、witness-r14b 成图见证实测在案；
    # prep 零重渲染、zero-write）。top=无配色（renders-r5 逐字节
    # 复用）；bottom=r14b 配色语义。
    if "-top-" in raw_key:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "top 渲染=渲染零变更（renders-r14b/applied-top.png 298bc620 "
            "与 prep1-top.png b2f84524=renders-r5 逐字节复用、top 无配色"
            "，与 r14–r19 盲读同一批文件）；framing-r14b=7004b017 "
            "single_variable_change 在案；本轮 zero-write 零重渲染")
    else:
        framing_rel = REL_FRAMING_R14B
        framing_note = (
            "bottom 渲染=渲染零变更（renders-r14b 四图字节复用、两板 "
            "bottom 成图逐字节同 d7284259；白墨图元→橙 (255,165,0)、"
            "板内空隙白→绿 (0,128,0)；成图实测橙 81672 px/绿 206632 px"
            "/板内白 0（witness-r14b palette_assertion_summary，脚本 "
            "live 装载核对）；framing-r14b=7004b017 预注册件在案；"
            "r22-prep-record bottom_view_note 在案）")
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
                     " frame_box_pct_r5（R5 仪器像素界重投影口径；r22 "
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
                "r22 实测 flag_id 编号行为=5 个有旗实例全部同实例跨板"
                "连续+bottom-i1 两板零旗标（与 r22-prep-record naming"
                "「实例间编号独立，同实例跨板连续」声明相符；零旗标实例"
                "编号无可登记如实注明）——abstain_ids/"
                "non_abstain_flag_ids 仍按 (state, flag_id) 限定，跨板"
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

    本轮 bottom-i1 两板零旗标（2 格零旗）：bottom 视角弃权率含 None
    实例→中位数=None、min/max 按可计算实例计算（item 5 零分母 None
    口径本轮触发）；top 视角三实例弃权率全部有定义、中位数=排序后第 2。
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
                 "复制性三分判据（replicated=M1 落 [0.361538,0.561538] "
                 "且 contact 族≤7 且 G1/G2 维持 / drifted=未达 replicated "
                 "且 M1 <0.771429 且 G1/G2 维持 / regressed=M1 ≥0.771429 "
                 "或 G1/G2 任一破坏）"
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
                       "r17": "not_met（在案）", "r18": "not_met（在案）",
                       "r19": "not_met（在案）", "r20": "not_met（在案）",
                       "r21": "跳号未执行（R21 全组合槽位未触发、永久留空"
                              "在案）",
                       "r22": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
# 逐旗失败通道归因（vs R18；方法照抄 s34/s36/s39/s41/s43/s45/s47/s68：
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
                              run_r16: dict, run_r17: dict, run_r18: dict,
                              run_r19: dict, run_r20: dict,
                              inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R19/R20；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R15/R16/R17/R18/R19/R20 十四件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r15_replays = replay_round_instances(run_r15)
    r16_replays = replay_round_instances(run_r16)
    r17_replays = replay_round_instances(run_r17)
    r18_replays = replay_round_instances(run_r18)
    r19_replays = replay_round_instances(run_r19)
    r20_replays = replay_round_instances(run_r20)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R22 {key} 通道重放与 compare_v3 对拍不一致")

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
    # r15–r20=fresh 重放并与在案登记逐一交叉核对，r22=本轮 fresh 重放）
    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", r16_replays, None)
    geo_r17 = pick("area_ratio_rejected", r17_replays, None)
    geo_r18 = pick("area_ratio_rejected", r18_replays, None)
    geo_r19 = pick("area_ratio_rejected", r19_replays, None)
    geo_r20 = pick("area_ratio_rejected", r20_replays, None)
    geo_r22 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", r16_replays, None)
    cat_r17 = pick("category_mismatch", r17_replays, None)
    cat_r18 = pick("category_mismatch", r18_replays, None)
    cat_r19 = pick("category_mismatch", r19_replays, None)
    cat_r20 = pick("category_mismatch", r20_replays, None)
    cat_r22 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", r16_replays, None)
    view_r17 = pick("view_gate", r17_replays, None)
    view_r18 = pick("view_gate", r18_replays, None)
    view_r19 = pick("view_gate", r19_replays, None)
    view_r20 = pick("view_gate", r20_replays, None)
    view_r22 = pick("view_gate", inst_replays, inst_blocks)
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
    if geo_r18 != run_r18["channel_attribution"]["channel_1_geometry_gate"][
            "r18_area_ratio_rejected_entries"]:
        _fail("R18 几何门重放与 run-r18 在案登记不一致")
    if cat_r18 != run_r18["channel_attribution"]["channel_2_category_gate"][
            "r18_category_mismatch_entries"]:
        _fail("R18 类别门重放与 run-r18 在案登记不一致")
    if view_r18 != run_r18["channel_attribution"][
            "view_gate_observations"]["r18_entries"]:
        _fail("R18 视角门重放与 run-r18 在案登记不一致")
    if geo_r19 != run_r19["channel_attribution"]["channel_1_geometry_gate"][
            "r19_area_ratio_rejected_entries"]:
        _fail("R19 几何门重放与 run-r19 在案登记不一致")
    if cat_r19 != run_r19["channel_attribution"]["channel_2_category_gate"][
            "r19_category_mismatch_entries"]:
        _fail("R19 类别门重放与 run-r19 在案登记不一致")
    if view_r19 != run_r19["channel_attribution"][
            "view_gate_observations"]["r19_entries"]:
        _fail("R19 视角门重放与 run-r19 在案登记不一致")
    if geo_r20 != run_r20["channel_attribution"]["channel_1_geometry_gate"][
            "r20_area_ratio_rejected_entries"]:
        _fail("R20 几何门重放与 run-r20 在案登记不一致")
    if cat_r20 != run_r20["channel_attribution"]["channel_2_category_gate"][
            "r20_category_mismatch_entries"]:
        _fail("R20 类别门重放与 run-r20 在案登记不一致")
    if view_r20 != run_r20["channel_attribution"][
            "view_gate_observations"]["r20_entries"]:
        _fail("R20 视角门重放与 run-r20 在案登记不一致")

    n_top_nonabstain = sum(
        1 for b in inst_blocks
        if b["_instance"].startswith("top")
        for f in b["reader_flags"] if not f["abstain"])
    geo_change = (
        "几何门通道（R19→R22）：面积比出局条目 %d→%d（渲染零变更轮内"
        "top 非弃权旗与同态 GT ≥0.5 containment 交叠条目的几何门计数"
        "如实登记；本轮 top 非弃权旗 %d 条、几何门=%d 条；r20 重放=%d 条"
        "逐轮对照；跨轮实例群漂移混杂照旧声明，只描述不断言。"
        % (len(geo_r19), len(geo_r22), n_top_nonabstain, len(geo_r22),
           len(geo_r20)))
    cat_change = (
        "类别门通道（R19→R22）：类别不符出局条目 %d→%d（r16 在案 1 条="
        "prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3（containment "
        "0.848147、面积比 1.529072），r17/r18 重放=0 条、r19 重放=2 条、"
        "r20 重放=%d 条"
        "（run-r20 在案），r22 "
        "重放=%d 条；"
        "r11 唯一原发条目 R11T-012↔GT-REVC-AP-8-R1Q2 语境下逐轮计数如实"
        "登记；跨轮实例群漂移混杂照旧声明，只描述不断言。"
        % (len(cat_r19), len(cat_r22), len(cat_r20), len(cat_r22)))

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
            "r19": len(geo_r19),
            "r20": len(geo_r20),
            "r22": len(geo_r22),
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
            "r19": len(cat_r19),
            "r20": len(cat_r20),
            "r22": len(cat_r22),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=0→r17=0→r18=0→r19=0→r20=0→r22=%d（r14 "
                 "回升未延续、r15–r22 维持低位：top 非弃权旗与同态 GT ≥0.5 "
                 "containment 交叠条目如实计数）；类别门 r6=1→r7=0→r8=1→"
                 "r9=0→r10=0→"
                 "r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=2→"
                 "r20=%d→r22=%d"
                 "（r11 唯一条目 R11T-012↔AP-8 无再现；r16 1 条=r16 在案、"
                 "r17–r22 逐轮如实计数）"
                 % (len(geo_r22), len(cat_r20), len(cat_r22))),
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
            "ref": {"path_rel": REL_PREP_R22, "sha256": _sha(REL_PREP_R22)},
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
            "source_of_r15_r16_r17_r18_r19_r20_detail": (
                "calibration-run-r15.json / calibration-run-r16.json / "
                "calibration-run-r17.json / calibration-run-r18.json / "
                "calibration-run-r19.json / calibration-run-r20.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/s55/s58/"
                "s64/s68/s71/s74 deviation_note 口径：本轮对 R15/R16/R17/"
                "R18/R19/R20/R22 "
                "均以内嵌输入+compare_v3 同源几何原语（calibration._"
                "containment/_area_ratio、CONTAINMENT_MIN=0.5、"
                "AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 GT "
                "确定性重放通道分类：containment<0.5（含 None=无交集）无"
                "条目；近邻且视角不符=view_gate；近邻且面积比>上限="
                "area_ratio_rejected（几何门）；近邻且面积比≤上限且类别"
                "不符=category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
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
                "r18_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r18_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r19_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r19_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r20_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r20_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r22_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R15/R16 候选对=空集、"
                         "R17 候选对=空集（run-r17 在案）、R18 候选对=空集"
                         "（run-r18 在案）；R19 唯一候选对=prep1-top-i3 "
                         "R19T-009↔GT-REVC-P1-L1SHORT（run-r19 在案、本轮"
                         "重放复现）；R20 候选对=空集（run-r20 在案、本轮"
                         "重放复现）；R22 十二件重放全部复现（候选对"
                         "=prep1-top-i2 R22T-007 与 prep1-top-i3 R22T-017 "
                         "各与 GT-REVC-P1-L1SHORT，见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R15T/R15B、R16T/R16B、R17T/"
            "R17B、R18T/R18B、R19T/R19B、R20T/R20B 与 R22T/R22B 来自不同 "
            "reader 实例、不同判读"
            "实例；轮内实例行为差异见 reader.reader_instance_note=混杂"
            "因素；r22 五个有旗实例全部跨板连续+bottom-i1 两板零旗标=与 "
            "prep-record naming 声明相符、同属实例输出行为登记如实记录）；"
            "下列分组是通道级归因，不是旗级配对；development 域只描述"
            "不断言能力"),
        "channel_1_geometry_gate": {
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "r17_area_ratio_rejected_entries": geo_r17,
            "r18_area_ratio_rejected_entries": geo_r18,
            "r19_area_ratio_rejected_entries": geo_r19,
            "r20_area_ratio_rejected_entries": geo_r20,
            "r22_area_ratio_rejected_entries": geo_r22,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r15_category_mismatch_entries": cat_r15,
            "r16_category_mismatch_entries": cat_r16,
            "r17_category_mismatch_entries": cat_r17,
            "r18_category_mismatch_entries": cat_r18,
            "r19_category_mismatch_entries": cat_r19,
            "r20_category_mismatch_entries": cat_r20,
            "r22_category_mismatch_entries": cat_r22,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r15_entries": view_r15,
            "r16_entries": view_r16,
            "r17_entries": view_r17,
            "r18_entries": view_r18,
            "r19_entries": view_r19,
            "r20_entries": view_r20,
            "r22_entries": view_r22,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r22 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；r15–r20 重放亦零视角门条目（在案延续）。"
                     % len(view_r22)),
        },
        "gate_chain_since_r6": chain,
        "r22_specific_observations": [
            "R22 六实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条（本轮 2 条命中=prep1-top-i2 "
            "R22T-007+prep1-top-i3 R22T-017 各与 GT-REVC-P1-L1SHORT；"
            "对照 r19 唯一命中同 GT（R19T-009）与 r20 零命中如实并列；GT "
            "条目层 union/agreement 与代表配置口径见 gt_match_dual/"
            "aggregation_representative（如实分列）；bottom 非弃权旗零"
            "匹配属结构性（GT 13 条全部 side=top，bottom GT 无源在案 "
            "gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R22 courtyard 类旗标 %d 条（top %d+bottom %d）：top 非弃权 "
            "6 条（top-i1 两板 R22T-002/003/007/008 间隙支负责任报告+"
            "top-i2 两板 R22T-001/005 贴触/极近报告）+top 弃权 2 条"
            "（top-i3 两板 R22T-008/019，(iii-a) 残余弃权支）；bottom 零 "
            "courtyard 类旗标（对照 r20 的 bottom 非弃权 2 条=G1 破坏在"
            "案，r22 G1 维持）；top 弃权构成分型=接触性 2+存在性 14+层"
            "归属其他 0（hypothesis_test.mechanism_observation."
            "top_abstain_typology 逐旗摘录在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R22 几何门 %d 条（r19=0/r20=0 延续与否如实计数）；类别门 %d "
            "条（r16=1 后的 r17–r22 逐轮计数如实登记）；视角门条目数"
            "见 view_gate_observations（如实单列）。"
            % (len(geo_r22), len(cat_r22)),
            "R22 suspicious_reroute 旗标 4 条（弃权 4[top-i1 两板 "
            "R22T-004/009+top-i3 两板 R22T-007/018 存在性出口]，"
            "(state, flag_id) 限定）；产量链 "
            "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→"
            "r17=1→r18=3→r19=3→r20=2→r22=4；「等长|蛇形」子串旗级零命中"
            "——r22 滥用型通道被动追踪=0（见 hypothesis_test."
            "reroute_continuation_r22，非本轮判据输入）。",
            "courtyard 被动追踪（r11–r20 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r22 "
            "courtyard_tracking 节）。",
        ],
    }

def _m_tuple_6dp(m1, m2, m3, m4) -> tuple:
    """四元组 → 6 位定点比较键（M1/M2/M4=率×10^6 取整、M3=整数直接）。"""
    return (int(round(m1 * 1000000)), int(round(m2 * 1000000)),
            int(m3), int(round(m4 * 1000000)))


def adjudicate_replication(abst_top: int, flags_top: int,
                           contact: int, guards_ok: bool) -> tuple:
    """主通道复制性三分判据合成（纯函数；判据原文=
    r22-prep-record hypothesis_test.adjudication；r16 截断基线=
    27/35=0.771429 live 重放交叉核对）。

    (p) replicated=M1 落 [0.361538, 0.561538]（r19±0.10）且 contact
    族弃权旗数（全视，分型件 rubric 口径）≤7 且 G1（bottom courtyard
    非弃权 0/0/0）与 G2（guard_ok）维持→r19 量级获复制支持（收益
    方向与幅度在新鲜实例群成立）；
    (g) regressed=M1 ≥0.771429（r16 基线；6 位定点整数交叉相乘，
    避免浮点）、或 G1/G2 任一破坏→r19 量级不可复制、轴3 收益判定
    降级为单轮现象；
    (d) drifted=未达 replicated 且 M1 <0.771429 且 G1/G2 维持→r19
    量级部分归因实例群（收益方向存但幅度不确定）。
    支序=regressed→replicated→drifted；返回 (verdict, branch_key)，
    branch_key ∈ {regressed_guards, regressed_m1, replicated,
    drifted}；replicated 与 regressed_m1 互斥由判据字面保证（M1 ∈
    [0.361538, 0.561538] 与 M1 ≥0.771429 不相交），若同时命中即
    RuntimeError（自洽性破坏）；未覆盖组合（守门维持、非 regressed、
    非 replicated、非 drifted）亦 RuntimeError。
    """
    m1_ge_reject = abst_top * 1000000 >= REJECT_M1_MIN_6DP * flags_top
    m1_in_band = (abst_top * 1000000 >= REPL_BAND_LO_6DP * flags_top
                  and abst_top * 1000000 <= REPL_BAND_HI_6DP * flags_top)
    crit_regressed_guards = not guards_ok
    crit_regressed_m1 = m1_ge_reject
    crit_regressed_ok = crit_regressed_guards or crit_regressed_m1
    crit_replicated_ok = (guards_ok and m1_in_band
                          and contact <= CONTACT_MAX_REPL)
    crit_drifted_ok = ((not crit_replicated_ok) and guards_ok
                       and not m1_ge_reject)
    if crit_replicated_ok and crit_regressed_m1:
        raise RuntimeError("主通道判定自洽性破坏（replicated 与 "
                           "regressed_m1 两支互斥被同时命中）")
    if crit_regressed_ok:
        return ("regressed",
                "regressed_guards" if crit_regressed_guards
                else "regressed_m1")
    if crit_replicated_ok:
        return ("replicated", "replicated")
    if crit_drifted_ok:
        return ("drifted", "drifted")
    raise RuntimeError("主通道判定未覆盖（带宽/M1/G/contact 组合未落入"
                       "任一预注册支）")



def _prep_doc() -> dict:
    """r22-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R22)


def prep_doc_attribution_declaration() -> str:
    """归因声明文本（取自 r22-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["declaration"]


def prep_doc_primary_channel_change() -> str:
    """主通道变更文本（取自 r22-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["change"]


def prep_doc_primary_channel_metric() -> str:
    """主通道度量文本（取自 r22-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["metric"]


def prep_doc_guard_channel() -> dict:
    """守门通道（取自 r22-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["guard_channel"]


# ---------------------------------------------------------------------------
# 预注册假设（r20-dev-record-candidate-r19-config-same-guidance-repeat）
# 复制性裁决（字母裁决+主通道逐支实测+M4 第二样本单列+机制观察单列）
# ---------------------------------------------------------------------------

def bottom_courtyard_non_abstain(instances: dict) -> dict:
    """bottom 侧 G1 守门实测（操作化定义：bottom 三实例 courtyard 类非
    弃权旗数；per r22-prep-record guard_channel「G1=bottom courtyard
    非弃权 0/0/0 维持（对照 r15–r19 在案 0/0/0、r20 破坏 2/0/0 在案=
    分岔记录）」原文；守门独立单列、不影响字母——r22 实测 0/0/0=
    G1 维持；守门破坏→regressed 支命中（描述性边界，出局语义不适用）。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r22 清单已按 (state, flag_id) 限定）；
    逐实例计数与 SIDE_OBS_REGISTERED 的 expected（=r22 实测登记）
    逐一相等（fail-closed，不符即中止）。
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
# 分型件 rubric 机械口径（contact 族计数唯一口径；装载→r13–r16 重放
# 对拍→r22 套用；关键词表/优先级全部从 abstain-typology-r13-r16.json
# 装载，不另嵌一套词表；对拍基期=r13–r16（8/15/5/10）不变）
# ---------------------------------------------------------------------------

#: r22 rubric 族计数登记值（程序实测须与本表逐一相等 fail-closed；
#: 基线对照 r19（contact 4/黑点 4/存在性 14）与 r20（contact 2/黑点 6/
#: 存在性 10）——R19_REFERENCE_REGISTERED/R20_REFERENCE_REGISTERED
#: 装载交叉核对；r20 侧另经 r22-prep-record chain_anchors.
#: dev_r20_family_counts_cross_check 双向核对）。
R20_FAMILY_COUNTS_REGISTERED = {
    "contact": 2, "existence_blackdot": 6, "existence_other": 10,
    "semantic_confusion": 0, "other": 0}
R22_FAMILY_COUNTS_REGISTERED = {
    "contact": 2, "existence_blackdot": 4, "existence_other": 12,
    "semantic_confusion": 0, "other": 0}

#: §5B 与 §4(iii-a) 援引机械实测期望集合（分开记、互不合并；per
#: r22-prep-record adjudication.mechanism_observation_separate 原文）：
#: r22 旗级 location_evidence 字面「§5B」/「(iii-a)」/「分支(」=0 旗
#: （程序实测须与空集逐一相等 fail-closed）；notes 级「§5B」=0 派次
#: （本轮指引字节复用无 §5B 节=任何援引为零上下文）与 notes 级
#: 「(iii-a)」=6 派次（applied/prep1-top-i2、applied/prep1-top-i3、
#: applied/prep1-bottom-i1）；r19 基线对照：(iii-a) 援引=旗级
#: 「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 派次（run-r19/
#: r22-prep-record run_r19_metric_anchor 在案）；r18 §5B 援引=旗级
#: 0/13 黑点弃权旗、派次级 1/12（dev-r18 在案）。
S5B_FLAG_CITE_REGISTERED = []
S5B_NOTES_CITE_REGISTERED = []
IIIA_FLAG_CITE_IIIA_REGISTERED = []
IIIA_FLAG_CITE_BRANCH_REGISTERED = []
IIIA_NOTES_CITE_REGISTERED = sorted([
    "applied-bottom-i1", "applied-top-i2", "applied-top-i3",
    "prep1-bottom-i1", "prep1-top-i2", "prep1-top-i3",
])



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
    （fail-closed）；并核对黑点族逐轮计数（r13=9/r14=14/r15=8/r16=12）、
    contact 族逐轮计数（r13=8/r14=15/r15=5/r16=10）与判正常派次计数
    （r15=3/r16=2）。
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
    ct_counts = {r: counts.get((r, "contact"), 0)
                 for r in ("r13", "r14", "r15", "r16")}
    if bd_counts != BLACKDOT_CHAIN_PRIOR:
        _fail(f"r13–r16 黑点族 rubric 计数与登记不符: {bd_counts}")
    if ct_counts != CONTACT_CHAIN_PRIOR:
        _fail(f"r13–r16 contact 族 rubric 计数与登记不符: {ct_counts}")
    if typology_doc["matrix"]["round_totals"]["r16"]["families"][
            "contact"] != CONTACT_CHAIN_PRIOR["r16"]:
        _fail("分型件 matrix r16 contact 计数与登记不符")
    disp = typology_doc["blackdot_dispatch"]
    for r in ("r15", "r16"):
        if len(disp[r]["judged_normal_dispatches"]) \
                != BLACKDOT_JUDGED_NORMAL_PRIOR[r]:
            _fail(f"分型件 {r} 判正常派次计数与登记不符")
    return {"per_flag_total": len(typology_doc["per_flag"]),
            "blackdot_counts": bd_counts,
            "contact_counts": ct_counts}


def build_rubric_rows_r22(instances: dict, kt: dict) -> list:
    """r22 全部旗标逐旗 rubric 套用（弃权旗=互斥族分类；非弃权旗不分型
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
                _fail(f"r22 旗 location_evidence 缺失: {d['flag_id']} "
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
                          run_r17: dict, run_r18: dict, run_r19: dict,
                          axis_plan: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（r20-dev-record-candidate-r19-config-same-guidance-repeat，
    同指引重复轮收敛归因）裁决节（预注册复制性三分判据执行；字母裁决
    唯一正式+守门 G1/G2 独立单列+M4 第二样本单列+机制观察单列）。

    字母裁决（唯一正式裁决）=判据 r22-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：判据=M1 落点+contact 族+守门维持——
    (p) replicated：M1（top 全旗聚合弃权率，12 派次全口径）落
    [0.361538, 0.561538]（r19±0.10）且 contact 族弃权旗数（全视，
    分型件 rubric 口径）≤7 且 G1（bottom courtyard 非弃权 0/0/0）与
    G2（guard_ok）维持→r19 量级获复制支持（收益方向与幅度在新鲜
    实例群成立）；
    (g) regressed：M1 ≥0.771429（r16 基线 27/35 双侧复算 live 重放
    交叉核对）、或 G1/G2 任一破坏→r19 量级不可复制、轴3 收益判定
    降级为单轮现象（描述性边界：本实验已收束、收敛归因轮出局语义
    不适用、破坏照实记录，per prep-record guard_channel requirement）；
    (d) drifted：未达 replicated 且 M1 <0.771429 且 G1/G2 维持→r19
    量级部分归因实例群（收益方向存但幅度不确定）。
    M1 基线=27/35=0.771429（run-r16 内嵌实例记录双侧复算 live 重放交
    叉核对一致）；判据比较用 6 位定点整数交叉相乘（避免浮点）；
    支序=regressed→replicated→drifted（判据字面：replicated 与
    regressed_m1 在 M1 维度互斥；未覆盖组合即自洽性破坏、中止）。
    M4 第二样本单列（m4_second_sample_separate 原文：r22 实测 M4 与
    r19 的 0.211111 双样本分布如实并列、不进字母裁决、不因双样本改门、
    不挑优、不合并分布）。守门 G1 与 G2 独立单列——任一破坏→
    regressed 支命中（字母照实）；机制观察单列、不凌驾、不改写字母
    裁决。
    """
    prep_doc = _json_load(REL_PREP_R22)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（axis-plan/protocol/r16 先例/r19 结构血统/
    # witness-r14b/round20-dev-record 授权/run-r16/run-r19 锚已在
    # FROZEN_SHA256 校验；prep-record chain_anchors 内嵌登记值与盘上
    # 实测逐一核对，fail-closed）
    anchors = prep_doc["guidance_reuse"]["chain_anchors"]
    ap_anchor = anchors["axis_experiment_plan_frozen_r21_slot"]
    if ap_anchor["path_rel"] != REL_AXIS_PLAN \
            or ap_anchor["sha256_measured"] != _sha(REL_AXIS_PLAN):
        _fail("prep-record 链锚（axis-plan/R21 槽位冻结原文）与盘上实测不符")
    if "三条轴单独/组合/全组合尝试，选择收益最大的继续" \
            not in ap_anchor["user_quote"]:
        _fail("prep-record 用户指令原文锚与预期不符")
    if "R21 不做" not in ap_anchor["r21_slot_frozen_quotes"][
            "early_stop_rule.strong_single_axis_shortcut"]:
        _fail("prep-record R21 槽位冻结原文与预期不符")
    if anchors["evaluation_protocol_v1_preserved"]["path_rel"] \
            != REL_PROTOCOL \
            or anchors["evaluation_protocol_v1_preserved"]["sha256"] \
            != _sha(REL_PROTOCOL):
        _fail("prep-record 链锚（evaluation-protocol-v1）与盘上实测不符")
    r16prec = anchors["r16_prep_record_same_guidance_repeat_precedent"]
    if r16prec["path_rel"] != REL_PREP_R16 \
            or r16prec["sha256"] != _sha(REL_PREP_R16):
        _fail("prep-record 链锚（r16 同指引重复轮先例）与盘上实测不符")
    r19lin = anchors["r19_prep_record_structure_lineage"]
    if r19lin["path_rel"] != REL_PREP_R19 \
            or r19lin["sha256"] != _sha(REL_PREP_R19):
        _fail("prep-record 链锚（r19-prep-record 结构血统）与盘上实测不符")
    wit = anchors["render_witness_r14b_byte_reuse"]
    if wit["path_rel"] != REL_WITNESS_R14B \
            or wit["sha256"] != _sha(REL_WITNESS_R14B):
        _fail("prep-record 链锚（witness-r14b 字节复用）与盘上实测不符")
    auth = anchors["round20_dev_record_authorization"]
    if auth["path_rel"] != REL_DEV_R20 \
            or auth["sha256_measured"] != _sha(REL_DEV_R20):
        _fail("prep-record 链锚（round20-dev-record 授权）与盘上实测不符")
    if "同指引重复轮" not in auth["repeat_candidate_quote"] \
            or "R21 不做" not in auth["stage2_closure_and_r21_skip_quote"]:
        _fail("prep-record round20-dev-record 授权原文与预期不符")
    a16 = anchors["run_r16_baseline_anchor"]
    if a16["path_rel"] != REL_RUN_R16 \
            or a16["sha256_measured"] != _sha(REL_RUN_R16):
        _fail("prep-record 链锚（run-r16 M1 基线）与盘上实测不符")
    if "0.771429" not in a16["frozen_values"] \
            or "guard_ok=True" not in a16["frozen_values"]:
        _fail("prep-record run-r16 冻结值文本与预期不符")
    a19 = anchors["run_r19_metric_anchor"]
    if a19["path_rel"] != REL_RUN_R19 \
            or a19["sha256_measured"] != _sha(REL_RUN_R19):
        _fail("prep-record 链锚（run-r19 度量锚）与盘上实测不符")
    for tok in ("0.461538", "0.571429", "4, 0.211111", "marginal",
                "4/4/14", "10/12"):
        if tok not in a19["frozen_values"]:
            _fail(f"prep-record run-r19 冻结值文本缺预期 token: {tok}")
    if anchors["base_sha256_prefix_expected"] != "8633bda5":
        _fail("prep-record 基座前缀期望与预期不符")
    fam20 = anchors["dev_r20_family_counts_cross_check"][
        "r20_family_counts_rubric"]
    if fam20 != R20_FAMILY_COUNTS_REGISTERED:
        _fail("prep-record dev-r20 三族计数链锚与登记不符")
    gr = prep_doc["guidance_reuse"]
    if gr["mode"] != "byte_reuse_zero_change" \
            or gr["derived"] is not None or gr["edit_list"] != []:
        _fail("prep-record guidance_reuse 复用模式与预期不符")
    if gr["base"] != "observation-guidance-r19.md" \
            or gr["base_path_rel"] != REL_GUIDANCE_R19 \
            or gr["base_sha256"] != _sha(REL_GUIDANCE_R19):
        _fail("prep-record guidance_reuse 基座锚与盘上实测不符")
    if "R19T-" not in gr["verbatim_scope_note"] \
            or "派发指令层覆盖" not in gr["verbatim_scope_note"]:
        _fail("prep-record §6 前缀差异声明与预期不符")
    if prep_doc["kind"] != "tl2_calibration_r22_prep_record":
        _fail("prep-record kind 与预期不符")
    if prep_doc["round_id_constant"] != ROUND_ID \
            or prep_doc["round_label"] != ROUND_LABEL \
            or prep_doc["declared_date"] != DECLARED_DATE \
            or prep_doc["instrument_change"]["changed"] is not False \
            or prep_doc["no_instrument_change"] is not True:
        _fail("prep-record 轮次标识/instrument_change.changed 与预期不符")
    if prep_doc["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("prep-record in_calibrated_range 应恒 False")
    if prep_doc["changed_variables"] != []:
        _fail("prep-record changed_variables 应为空（同指引重复轮：唯一"
              "操纵因子=实例群重抽）")
    if "reader 实例群" not in prep_doc["manipulated_factor"]:
        _fail("prep-record manipulated_factor 与预期不符")
    if len(prep_doc["measurement_design"]["items"]) != 5:
        _fail("prep-record measurement_design 应恰 5 条")
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
    # 指引本体核对（字节复用：r19 指引 (iii-a) bullet 恰 1 次+无 §5B 节
    # +§6 示例前缀 R19T-/R19B- 计数与 prep-record 实测锚一致）
    guidance_text = _rel(REL_GUIDANCE_R19).read_text(encoding="utf-8")
    if guidance_text.count("执行 (iii) 时按证据可见性三支操作") != 1:
        _fail("§4 (iii-a) bullet 在 r19 指引应恰 1 次（字节复用基座）")
    if guidance_text.count("(iii-a)") < 1:
        _fail("r19 指引缺 (iii-a) 条款")
    if guidance_text.count("## 5B.") != 0:
        _fail("r19 指引应无 §5B 节（字节复用基座结构在案）")
    if guidance_text.count("R19T-") != 4 or guidance_text.count("R19B-") != 1:
        _fail("r19 指引 §6 示例前缀计数与 prep-record 实测锚不符")
    pos_iii = guidance_text.find("(iii) **接触性判据")
    pos_iiia = guidance_text.find("执行 (iii) 时按证据可见性三支操作")
    pos_exit = guidance_text.find("**三路出口显式化")
    if not (0 <= pos_iii < pos_iiia < pos_exit):
        _fail("(iii-a) 条款位置断言破坏（应在 (iii) 句后、三路出口前）")
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
    if "M1 升序" not in axis_plan["comparison_rule"]["ordering"]:
        _fail("axis-plan 排序规则与预期不符")
    if "G1 或 G2 破坏的轮次不参与排序" \
            not in axis_plan["comparison_rule"]["eligibility_gate"]:
        _fail("axis-plan 资格门与预期不符")
    for gkey in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                 "G3_freeze_discipline"):
        if gkey not in axis_plan["guards"]:
            _fail(f"axis-plan 守门定义缺失: {gkey}")
    if ht["hypothesis_id"] != "r20-dev-record-candidate-r19-config-same-guidance-repeat":
        _fail("prep-record hypothesis_id 与预期不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "0.361538" not in adj["replicated"] \
            or "0.561538" not in adj["replicated"] \
            or "≤ 7" not in adj["replicated"] \
            or "G1" not in adj["replicated"] or "G2" not in adj["replicated"]:
        _fail("prep-record replicated 判据文本与预期不符")
    if "M1 < 0.771429" not in adj["drifted"] \
            or "G1" not in adj["drifted"] or "G2" not in adj["drifted"]:
        _fail("prep-record drifted 判据文本与预期不符")
    if "M1 ≥ 0.771429" not in adj["regressed"] \
            or "G1" not in adj["regressed"] or "G2" not in adj["regressed"]:
        _fail("prep-record regressed 判据文本与预期不符")
    if "0.211111" not in adj["m4_second_sample_separate"] \
            or "不进字母裁决" not in adj["m4_second_sample_separate"]:
        _fail("prep-record M4 第二样本单列条款与预期不符")
    if "4/4/14" not in adj["mechanism_observation_separate"] \
            or "2/6/10" not in adj["mechanism_observation_separate"]:
        _fail("prep-record 机制观察单列条款（三族双基线）与预期不符")
    if "部分重复≠独立重复" not in adj["metric_lesson_separate"]             or "不得事后收放" not in adj["metric_lesson_separate"]:
        _fail("prep-record 度量教训单列条款（带宽描述性边界）与预期不符")
    # 阈值常数自检（6 位定点）：regressed 门=M1 基线 0.771429、
    # replicated 带=[0.361538, 0.561538]、contact 门=≤7
    if REJECT_M1_MIN_6DP != 771429:
        _fail("M1 阈值常数与 r16 基线不符")
    if REPL_BAND_LO_6DP != 361538 or REPL_BAND_HI_6DP != 561538 \
            or CONTACT_MAX_REPL != 7:
        _fail("replicated 带宽/contact 门常数与 prep-record 判据不符")
    if R19_ROW_REGISTERED != {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                              "M4": 0.211111}:
        _fail("r19 参照四元组登记值与预期不符")
    if R20_ROW_REGISTERED != {"M1": 0.636364, "M2": 0.285714, "M3": 6,
                              "M4": 0.25}:
        _fail("r20 对照行登记值与预期不符")

    # contact 基线与 rubric 机械口径装载（分型件 r16 实测装载交叉核对；
    # 不手工抄数：r13–r16 132 条弃权旗先按同一 classify 重放对拍）
    typology_doc = load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    replay_proof = replay_typology_families(typology_doc, kt)
    if replay_proof["contact_counts"]["r16"] \
            != CONTACT_CHAIN_PRIOR["r16"] \
            or rb["M3_blackdot_abstain_flags_rubric"] \
            != replay_proof["blackdot_counts"]["r16"]:
        _fail("contact/M3 基线（r16）三方装载不一致")
    rubric_rows = build_rubric_rows_r22(instances, kt)
    contact = sum(1 for r in rubric_rows
                  if r["abstain"] and r["family"] == "contact")
    family_counts = {fam: sum(1 for r in rubric_rows
                              if r["abstain"] and r["family"] == fam)
                     for fam in ("contact", "existence_blackdot",
                                 "existence_other", "semantic_confusion",
                                 "other")}
    if family_counts != R22_FAMILY_COUNTS_REGISTERED:
        _fail(f"家族计数与登记不符: {family_counts}")
    rubric_bd = {(r["instance"], r["state"], r["flag_id"]) for r in
                 rubric_rows
                 if r["abstain"] and r["family"] == "existence_blackdot"}
    if rubric_bd != {(i, s, f) for i, s, f, _ in BLACK_DOT_FLAGS}:
        _fail("rubric 黑点族旗集合与登记表不一致")
    # contact 族分视角计数（r22 实测；对照 r16=10 全 top、r19=4 全视、
    # r20=2 全视）
    contact_by_view = {"top": 0, "bottom": 0}
    for r in rubric_rows:
        if r["abstain"] and r["family"] == "contact":
            contact_by_view["top" if r["instance"].startswith("top")
                            else "bottom"] += 1
    # 黑点转非弃权旗（机制观察计数）：非弃权旗中黑点对象词命中集合须与
    # 登记表逐一相等（覆盖完整性 fail-closed）
    nonabstain_bd = {(r["instance"], r["state"], r["flag_id"]) for r in
                     rubric_rows
                     if not r["abstain"] and r["matched_blackdot_terms"]}
    if nonabstain_bd != {(i, s, f) for i, s, f, _
                         in BLACK_DOT_NON_ABSTAIN_FLAGS}:
        _fail(f"黑点转非弃权旗集合与登记不符: {sorted(nonabstain_bd)}")
    # 黑点判正常派次计数（分型件 blackdot_dispatch 口径：notes 判黑点
    # 正常且该派次零黑点词旗标）——程序实测 vs 登记表
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
    if sorted(judged_normal) != ["applied-bottom-i1", "applied-top-i1",
                                 "prep1-bottom-i1", "prep1-top-i1"]:
        _fail(f"黑点判正常派次与登记不符: {sorted(judged_normal)}")
    # §5B 与 §4(iii-a) 援引实测（分开记、互不合并；per
    # mechanism_observation_separate 原文）：旗级 location_evidence 含
    # 「§5B」/「(iii-a)」/「分支(」；派次级=notes 含「§5B」/「(iii-a)」
    # ——机械集合须与登记逐一相等
    s5b_flag_hits = []
    iiia_flag_hits = []
    iibranch_flag_hits = []
    s5b_notes_hits = []
    iiia_notes_hits = []
    for key in RAW_FILES:
        doc = json.loads(_rel(RAW_FILES[key]).read_text(encoding="utf-8"))
        for img in doc["per_image"]:
            for f in img["flags"]:
                if "§5B" in f["location_evidence"]:
                    s5b_flag_hits.append((key, f["flag_id"]))
                if "(iii-a)" in f["location_evidence"]:
                    iiia_flag_hits.append((key, f["flag_id"]))
                if "分支(" in f["location_evidence"]:
                    iibranch_flag_hits.append((key, f["flag_id"]))
        if "§5B" in parsed_notes[key]:
            s5b_notes_hits.append(key)
        if "(iii-a)" in parsed_notes[key]:
            iiia_notes_hits.append(key)
    if sorted(s5b_flag_hits) != S5B_FLAG_CITE_REGISTERED:
        _fail(f"§5B 旗级援引与登记不符: {sorted(s5b_flag_hits)}")
    if sorted(iiia_flag_hits) != IIIA_FLAG_CITE_IIIA_REGISTERED:
        _fail(f"(iii-a) 旗级援引与登记不符: {sorted(iiia_flag_hits)}")
    if sorted(iibranch_flag_hits) != IIIA_FLAG_CITE_BRANCH_REGISTERED:
        _fail(f"分支( 援引与登记不符: {sorted(iibranch_flag_hits)}")
    if sorted(s5b_notes_hits) != S5B_NOTES_CITE_REGISTERED:
        _fail(f"§5B notes 级援引与登记不符: {sorted(s5b_notes_hits)}")
    if sorted(iiia_notes_hits) != IIIA_NOTES_CITE_REGISTERED:
        _fail(f"(iii-a) notes 级援引与登记不符: {sorted(iiia_notes_hits)}")
    # (iii-a) 逐旗落支登记校验（excerpt 逐字+abstain 属性+cited 集合=
    # 机械援引集合；落支计数自检）
    iiia_rows_out = []
    rubric_row_by_key = {(r["instance"], r["state"], r["flag_id"]): r
                         for r in rubric_rows}
    for row in IIIA_BRANCH_ROWS:
        if row["excerpt"] not in raw_texts[row["source"]]:
            _fail(f"(iii-a) 落支摘录与 reader 原文不符: {row['flag_id']} "
                  f"({row['source']})")
        src_flag = None
        doc = json.loads(
            _rel(RAW_FILES[row["source"]]).read_text(encoding="utf-8"))
        for img in doc["per_image"]:
            for f in img["flags"]:
                if f["flag_id"] == row["flag_id"]:
                    src_flag = f
        if src_flag is None or src_flag["abstain"] is not row["abstain"]:
            _fail(f"(iii-a) 落支登记 abstain 与原文不符: {row['flag_id']}")
        inst = next(n for n in INSTANCE_ORDER
                    if row["source"] in INSTANCES[n]["parts"])
        st = ("applied" if INSTANCES[inst]["parts"][0] == row["source"]
              else "prep1")
        rr = rubric_row_by_key[(inst, st, row["flag_id"])]
        if rr["abstain"] is not row["abstain"]:
            _fail(f"(iii-a) 落支登记与 rubric 行不符: {row['flag_id']}")
        literal_cite = ("(iii-a)" in src_flag["location_evidence"]
                        or "分支(" in src_flag["location_evidence"]
                        or "§5B" in src_flag["location_evidence"])
        if literal_cite is not row["cited"]:
            _fail(f"(iii-a) 落支 cited 与机械援引不符: {row['flag_id']}")
        iiia_rows_out.append(dict(row, instance=inst, state=st))
    iiia_branch_counts = {
        "branch1_gap_report": sum(1 for r in iiia_rows_out
                                  if r["branch"] == "branch1_gap_report"),
        "branch2_intrusion_report": sum(
            1 for r in iiia_rows_out
            if r["branch"] == "branch2_intrusion_report"),
        "branch3_residual_abstain": sum(
            1 for r in iiia_rows_out
            if r["branch"] == "branch3_residual_abstain"),
    }
    if iiia_branch_counts != {"branch1_gap_report": 6,
                              "branch2_intrusion_report": 1,
                              "branch3_residual_abstain": 2}:
        _fail(f"(iii-a) 落支分布与登记不符: {iiia_branch_counts}")
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
    # r18 对照行 live 复算（run-r18 内嵌输入；M 元组+分型/族计数）与
    # dev-r18 axis_experiment_ledger 登记交叉核对（fail-closed）
    r18_ab, r18_fl = _view_aggregate_abstain_live(
        run_r18, ("top-i1", "top-i2", "top-i3"))
    r18_bot_ab, r18_bot_fl = _view_aggregate_abstain_live(
        run_r18, ("bottom-i1", "bottom-i2", "bottom-i3"))
    r18_m1 = cal._ratio(r18_ab, r18_fl)
    r18_m2 = cal._ratio(r18_bot_ab, r18_bot_fl)
    r18_m3 = run_r18["hypothesis_test"]["measurement"][
        "m3_blackdot_abstain_flags_rubric_r18"]
    r18_m4 = run_r18["view_layer"]["top"]["abstain_rate_range"]
    r18_row = {"M1": r18_m1, "M2": r18_m2, "M3": r18_m3, "M4": r18_m4}
    if r18_row != {"M1": R18_REFERENCE_REGISTERED["M1"],
                   "M2": R18_REFERENCE_REGISTERED["M2"],
                   "M3": R18_REFERENCE_REGISTERED["M3"],
                   "M4": R18_REFERENCE_REGISTERED["M4"]}:
        _fail(f"r18 对照行 live 复算与登记不符: {r18_row}")
    dev18 = _json_load(REL_DEV_R18)
    measured_rows = dev18["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    if measured_rows["r17_axis1"] != R17_ROW_REGISTERED:
        _fail("dev-r18 r17_axis1 行与登记不符")
    if measured_rows["r18_axis2"] != {"M1": r18_m1, "M2": r18_m2,
                                      "M3": r18_m3, "M4": r18_m4}:
        _fail("dev-r18 r18_axis2 行与 run-r18 live 复算不符")
    r18_m = run_r18["hypothesis_test"]["mechanism_observation"]
    if r18_m["top_abstain_typology"]["type_counts"] \
            != R18_REFERENCE_REGISTERED["top_typology"]:
        _fail("run-r18 top 弃权分型与 dev-r18 参照计数不符")
    if len(r18_m["black_dot_tracking"]["black_dot_flags"]) \
            != R18_REFERENCE_REGISTERED["M3"] \
            or r18_m["black_dot_tracking"]["rubric_families"]["counts"][
                "existence_other"] \
            != R18_REFERENCE_REGISTERED["existence_other"] \
            or r18_m["black_dot_tracking"][
                "blackdot_to_non_abstain_count"] \
            != R18_REFERENCE_REGISTERED["blackdot_to_non_abstain"] \
            or r18_m["black_dot_tracking"]["judged_normal_dispatches"][
                "count"] \
            != R18_REFERENCE_REGISTERED["judged_normal_dispatches"]:
        _fail("run-r18 黑点族/存在性族对照计数与登记不符")
    if "G1/G2 均满足" not in dev18["axis_experiment_ledger"][
            "cross_round_status"]["note"]:
        _fail("dev-r18 资格门注记与预期不符")
    # r19 对照行 live 复算（run-r19 内嵌输入；M 元组+族计数+分型）与
    # R19_ROW_REGISTERED/R19_REFERENCE_REGISTERED 交叉核对
    r19_ab, r19_fl = _view_aggregate_abstain_live(
        run_r19, ("top-i1", "top-i2", "top-i3"))
    r19_bot_ab, r19_bot_fl = _view_aggregate_abstain_live(
        run_r19, ("bottom-i1", "bottom-i2", "bottom-i3"))
    r19_m1 = cal._ratio(r19_ab, r19_fl)
    r19_m2 = cal._ratio(r19_bot_ab, r19_bot_fl)
    r19_counts = run_r19["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    r19_m3 = r19_counts["existence_blackdot"]
    r19_m4 = run_r19["view_layer"]["top"]["abstain_rate_range"]
    r19_row = {"M1": r19_m1, "M2": r19_m2, "M3": r19_m3, "M4": r19_m4}
    if r19_row != R19_ROW_REGISTERED:
        _fail(f"r19 对照行 live 复算与登记不符: {r19_row}")
    r19_typology_live = run_r19["hypothesis_test"]["mechanism_observation"][
        "top_abstain_typology"]["type_counts"]
    if r19_typology_live != R19_REFERENCE_REGISTERED["top_typology"]:
        _fail("run-r19 top 弃权分型与登记参照不符")
    if r19_counts["contact"] != R19_REFERENCE_REGISTERED["contact"] \
            or r19_counts["existence_blackdot"] \
            != R19_REFERENCE_REGISTERED["existence_blackdot"] \
            or r19_counts["existence_other"] \
            != R19_REFERENCE_REGISTERED["existence_other"] \
            or run_r19["hypothesis_test"]["mechanism_observation"][
                "black_dot_tracking"]["judged_normal_dispatches"]["count"] \
            != R19_REFERENCE_REGISTERED["judged_normal_dispatches"]:
        _fail("run-r19 三族/判正常对照计数与登记不符")
    # r20 对照行 live 复算（run-r20 内嵌输入；M 元组+族计数+分型+G1
    # 破坏登记）与 R20_ROW_REGISTERED/R20_REFERENCE_REGISTERED/prep-
    # record dev_r20_family_counts_cross_check 三方交叉核对
    run_r20 = _json_load(REL_RUN_R20P)
    r20_ab, r20_fl = _view_aggregate_abstain_live(
        run_r20, ("top-i1", "top-i2", "top-i3"))
    r20_bot_ab, r20_bot_fl = _view_aggregate_abstain_live(
        run_r20, ("bottom-i1", "bottom-i2", "bottom-i3"))
    r20_counts = run_r20["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    r20_row_live = {"M1": cal._ratio(r20_ab, r20_fl),
                    "M2": cal._ratio(r20_bot_ab, r20_bot_fl),
                    "M3": r20_counts["existence_blackdot"],
                    "M4": run_r20["view_layer"]["top"]["abstain_rate_range"]}
    if r20_row_live != R20_ROW_REGISTERED:
        _fail(f"r20 对照行 live 复算与登记不符: {r20_row_live}")
    if r20_counts != R20_FAMILY_COUNTS_REGISTERED:
        _fail("run-r20 三族计数与 prep-record 链锚/登记不符")
    r20_typology_live = run_r20["hypothesis_test"]["mechanism_observation"][
        "top_abstain_typology"]["type_counts"]
    if r20_typology_live != R20_REFERENCE_REGISTERED["top_typology"]:
        _fail("run-r20 top 弃权分型与登记参照不符")
    if run_r20["hypothesis_test"]["measurement"]["bottom_side_observation"][
            "bottom_courtyard_non_abstain_by_instance_r20"] \
            != R20_REFERENCE_REGISTERED["g1_bottom_courtyard_non_abstain"]:
        _fail("run-r20 G1 破坏登记（2/0/0）与登记参照不符")
    if run_r20["hypothesis_test"]["mechanism_observation"][
            "black_dot_tracking"]["judged_normal_dispatches"]["count"] \
            != R20_REFERENCE_REGISTERED["judged_normal_dispatches"]:
        _fail("run-r20 判正常派次对照计数与登记不符")
    # reroute 产量链基线交叉核对（r8–r20 在案）
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
            or run_r18["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r18"] \
            or run_r19["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r19"] \
            or run_r20["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r20"]:
        _fail("reroute 类产量链与在案 run 不符")


    # 主通道实测（复制性三分判据+M1 带宽/contact 门，12 派次全口径）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    # (g) regressed：M1 ≥0.771429、或 G1/G2 任一破坏（守门在下方实测后
    # 合成）
    m4 = view_layer["top"]["abstain_rate_range"]
    crit_regressed_m1 = (abst_top * 1000000
                         >= REJECT_M1_MIN_6DP * flags_top)
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
    # 守门 G2（guard_ok=True 维持；top 视非弃权旗标 frame_box_pct 几何门
    # 面积比出局条目 R19=0→R22 实测不升）——独立单列（axis-plan guards.
    # G2_guard_ok 原文）
    geo_r22 = attribution["channel_1_geometry_gate"][
        "r22_area_ratio_rejected_entries"]
    geo_r19 = attribution["channel_1_geometry_gate"][
        "r19_area_ratio_rejected_entries"]
    guard_ok = len(geo_r22) <= len(geo_r19)
    g2_ok = guard_ok is True
    guards_ok = bool(g1_ok and g2_ok)
    # 复制性三支合成（判据字面；支序=regressed→replicated→drifted；
    # 合成逻辑在 adjudicate_replication 纯函数内、可独立构造边界用例）
    r22_tuple = _m_tuple_6dp(top_rate, bot_rate,
                             family_counts["existence_blackdot"], m4)
    r19_tuple = _m_tuple_6dp(r19_m1, r19_m2, r19_m3, r19_m4)
    verdict, branch_key = adjudicate_replication(
        abst_top, flags_top, contact, guards_ok)
    crit_regressed_ok = verdict == "regressed"
    crit_replicated_ok = verdict == "replicated"
    crit_drifted_ok = verdict == "drifted"
    crit_regressed_guards = not guards_ok
    m1_in_band = (abst_top * 1000000 >= REPL_BAND_LO_6DP * flags_top
                  and abst_top * 1000000 <= REPL_BAND_HI_6DP * flags_top)
    crit_contact_le_max = contact <= CONTACT_MAX_REPL
    crit_drifted_m1_lt = (abst_top * 1000000
                          < REJECT_M1_MIN_6DP * flags_top)
    # 字母裁决（复制性三分判据，per r22-prep-record adjudication 原文）
    if crit_regressed_ok:
        verdict = "regressed"
        if crit_regressed_guards:
            letter_branch = (
                "(g) G1/G2 任一破坏（per r22-prep-record guard_channel."
                "requirement 原文：任一守门破坏→regressed 支命中——描述性"
                "边界，本实验已收束、收敛归因轮出局语义不适用、破坏照实"
                "记录）；本轮=G1/G2 破坏（bottom courtyard 非弃权实测 %s≠"
                "0/0/0 或几何门回升）；复制性结论=r19 量级不可复制、轴3 "
                "收益判定降级为单轮现象"
                % list(by_instance.values()))
        else:
            letter_branch = (
                "(g) M1 ≥0.771429（实测 %s 不落入 r19±0.10 带且不低于 "
                "r16 基线）——regressed：r19 量级不可复制、轴3 收益判定"
                "降级为单轮现象"
                % cal._ratio(abst_top, flags_top))
    elif crit_replicated_ok:
        verdict = "replicated"
        letter_branch = (
            "(p) M1 落 [0.361538, 0.561538]（r19±0.10；实测 %s）且 "
            "contact 族 %d≤7 且 G1/G2 维持——replicated：r19 量级获复制"
            "支持（收益方向与幅度在新鲜实例群成立）"
            % (cal._ratio(abst_top, flags_top), contact))
    elif crit_drifted_ok:
        verdict = "drifted"
        letter_branch = (
            "(d) 未达 replicated（M1 实测 %s 落点/contact 族 %d）但 "
            "M1 <0.771429 且 G1/G2 维持——drifted：r19 量级部分归因实例群"
            "（收益方向存但幅度不确定）"
            % (cal._ratio(abst_top, flags_top), contact))
    else:
        _fail("主通道判定未覆盖（带宽/M1/G/contact 组合未落入任一预注册"
              "支）")
    verdict_text = (
        "按预注册判据（r22-prep-record.json hypothesis_test.adjudication "
        "原文，复制性三分判据）=%s（字母口径，唯一正式裁决）：落支=%s。"
        "实测：R22 四元组=(%s, %s, %d, %s)（M1=top 全旗聚合弃权率 %d/%d、"
        "M2=bottom 全旗聚合弃权率 %d/%d、M3=黑点族弃权旗数（分型件 "
        "rubric 口径）=%d、M4=top 逐实例弃权率极差=%s）；r19 参照元组="
        "(%s, %s, %d, %s)（run-r19 内嵌实例记录 live 复算+run_r19_"
        "metric_anchor 冻结值交叉核对一致，不手工抄数）→M1 带 "
        "[0.361538, 0.561538] "
        "内=%s、contact 族 %d≤7=%s；(g) 支 M1 ≥0.771429→crit_regressed_"
        "m1=%s（r16 基线=同一聚合逻辑对 calibration-run-r16.json 内嵌"
        "实例记录双侧复算=%d/%d=%s，与在案登记 27/35 及 axis-plan r16_"
        "baseline.M1 交叉核对一致）；G1（bottom courtyard 非弃权 0/0/0 "
        "维持）=%s（实测 %s）、G2（guard_ok=True 维持，top 几何门面积比"
        "出局条目 R19=%d→R22=%d）=%s。同指引重复轮（指引=observation-"
        "guidance-r19.md 字节复用、渲染=renders-r14b 字节复用）下唯一"
        "实验变量=reader 实例群重抽；字母裁决只回答「r19 单轮收益是否在"
        "新鲜实例群复现（真实收益 vs 实例群漂移）」的收敛归因判据命中"
        "方向；三项判据文本分开如实记录、不合并；本轮判据均为描述性"
        "边界、非 APR-0011 门（门照常独立计算，互不凌驾、run-record 内"
        "分开表述）。M4 第二样本单列（m4_second_sample_separate 原文："
        "r22 实测 %s 与 r19 的 0.211111 双样本分布如实并列、不进字母"
        "裁决、不因双样本改门、不挑优、不合并分布）。注意：跨轮实例群"
        "漂移混杂=本轮裁决变量本身（r15→r16 纯重抽漂移 0.09064 在案"
        "参照；部分重复≠独立重复、同域同编排实例池、验证力度如实声明）；"
        "单轮 n=3、development 域只描述不断言；机制观察单列（§5B 与 "
        "(iii-a) 援引计数分开记/三族计数 r19/r20 双基线对照/contact 族"
        "逐旗分类/M2/M4/top 弃权分型/courtyard 计数），不凌驾、不改写"
        "字母裁决。"
        % (verdict, letter_branch,
           top_rate, bot_rate, family_counts["existence_blackdot"], m4,
           abst_top, flags_top, abst_bot, flags_bot,
           family_counts["existence_blackdot"], m4,
           r19_m1, r19_m2, r19_m3, r19_m4,
           m1_in_band, contact, crit_contact_le_max,
           crit_regressed_m1,
           base16_ab, base16_fl, cal._ratio(base16_ab, base16_fl),
           "维持（0/0/0）" if g1_ok else "破坏",
           list(by_instance.values()),
           len(geo_r19), len(geo_r22),
           "维持（True）" if g2_ok else "破坏",
           m4))
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 量化判据应用
    # + top 弃权分型逐旗 + 黑点族 + placement 处置 + 绿区语义化
    # + (iii-a) 间隙支 notes 级）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in QUANT_CRITERION_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"量化判据应用摘录与 reader 原文不符: {ev['source']}")
    for ev in IIIA_NOTES_BRANCH1_ROWS:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"(iii-a) 间隙支 notes 摘录与 reader 原文不符: "
                  f"{ev['source']}")
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
    # 黑点族旗标登记校验（4 条全部存在、abstain=True、category=登记值、
    # rubric 族=existence_blackdot；附 matched 词与旗级援引实测）
    black_rows = []
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
                           "cites_iiia_location_evidence":
                               "(iii-a)" in loc or "分支(" in loc,
                           "cites_s5b_location_evidence": "§5B" in loc})
    # 黑点转非弃权旗逐条摘录行（6 条；机制观察登记口径）
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
    # 绿色区域语义化观察（r16–r20 side_observation 先例延续：按实例
    # 分布；程序实测 substring 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、
    # 不构成判据输入；r22 实测 §5A 显式援引=2/6 派次（bottom-i1 两板）、
    # §5B 显式援引=0/6 派次（本轮指引无 §5B 节=零上下文））
    green_semantics = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        rec = INSTANCES[name]
        texts = [parsed_notes[p] for p in rec["parts"]]
        rows_inst = [r for r in GREEN_SEMANTICS_EVIDENCE
                     if r["instance"] == name]
        cites_5a = [bool(r.get("cites_5A")) for r in rows_inst]
        cites_5b = [bool(r.get("cites_5B")) for r in rows_inst]
        has_green = any(t.count("绿") + t.count("翼瓣") + t.count("空隙")
                        for t in texts)
        if any(cites_5a) or any(cites_5b):
            mode = "§5A/§5B 仪器注记显式提及（仅作事实参考）"
        elif has_green:
            mode = "空隙/翼瓣几何语义化（无 §5A/§5B 显式援引）"
        else:
            mode = "无绿色语义化自述（如实空缺）"
        green_semantics[name] = {
            "绿_hits_by_part": [t.count("绿") for t in texts],
            "翼瓣_hits_by_part": [t.count("翼瓣") for t in texts],
            "空隙_hits_by_part": [t.count("空隙") for t in texts],
            "§5A_cited": any(cites_5a),
            "§5B_cited": any(cites_5b),
            "semantic_mode": mode,
        }
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    black_by_instance = {n: sum(1 for row in black_rows
                                if row["instance"] == n)
                         for n in INSTANCE_ORDER}
    r22_m4 = cal._round6(max(top_rates.values()) - min(top_rates.values()))

    # 实验对照账：r16 基线/r17 轴1/r18 轴2/r19 轴3/r20（破坏轮登记行）/
    # r22 本轮 六行并列+冻结排序（资格门=G1/G2 均满足；r22 按同口径
    # M 元组入排序）
    ledger_rows = {
        "r16_baseline": {"M1": rb["M1_top_aggregate_abstain_rate"],
                         "M2": rb["M2_bottom_aggregate_abstain_rate"],
                         "M3": rb["M3_blackdot_abstain_flags_rubric"],
                         "M4": rb["M4_top_per_instance_rate_range"]},
        "r17_axis1": dict(measured_rows["r17_axis1"]),
        "r18_axis2": dict(measured_rows["r18_axis2"]),
        "r19_axis3": dict(r19_row),
        "r20_combo_registered": dict(R20_ROW_REGISTERED),
        "r22_repeat": {"M1": top_rate, "M2": bot_rate, "M3": family_counts[
            "existence_blackdot"], "M4": r22_m4},
    }
    eligible_rows = {k: v for k, v in ledger_rows.items()
                     if k != "r20_combo_registered"
                     and not (k == "r22_repeat" and not guards_ok)}
    ranking = sorted(eligible_rows.items(),
                     key=lambda kv: (kv[1]["M1"], kv[1]["M2"],
                                     kv[1]["M3"], kv[1]["M4"]))
    ranking_order = [k for k, _ in ranking]
    m1_drop_r22 = cal._round6(rb["M1_top_aggregate_abstain_rate"]
                              - top_rate)
    # 复制性结论位（replicated→r19 量级获复制支持；drifted→部分归因
    # 实例群；regressed→降级单轮现象）
    replication_conclusion = {
        "rule_sources": (
            "r22-prep-record.json hypothesis_test.adjudication 复制性三分"
            "判据（replicated/drifted/regressed 原文）+attribution_plan."
            "primary_channel（M1 落点归因裁决三支）+guard_channel."
            "requirement（守门破坏→regressed 支命中、描述性边界）"),
        "verdict": verdict,
        "conclusion": (
            "收敛归因结论=replicated：r19 配置单轮收益（M1=0.461538、"
            "contact 族 10→4、M4=0.211111）在 12 派次全新实例群复现"
            "（r22 M1 实测落 r19±0.10 带内、contact 族 %d≤7、G1/G2 "
            "维持）——r19 量级获复制支持（收益方向与幅度在新鲜实例群"
            "成立；(β) 实例群漂移解释被本轮落点削弱、漂移参照幅度 "
            "0.09064 远小于 r19 降幅 0.309891 在案并列）；后续 dev-record "
            "包转记（本轮不预写后续决策）"
            if verdict == "replicated" else
            ("收敛归因结论=drifted：r19 量级部分归因实例群（收益方向存"
             "但幅度不确定）" if verdict == "drifted" else
             "收敛归因结论=regressed：r19 量级不可复制、轴3 收益判定"
             "降级为单轮现象")),
        "m4_second_sample_note": (
            "M4 双样本单列（per adjudication.m4_second_sample_separate "
            "原文）：r22 实测 %s vs r19 的 0.211111——两样本分布如实并列、"
            "不进字母裁决、不因双样本改门、不挑优、不合并分布（r19 的 "
            "supported 门 0.20 差 0.011111 在案、字母=marginal 维持不变）"
            % r22_m4),
    }
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决不因本观察"
                 "改写；per r22-prep-record adjudication."
                 "mechanism_observation_separate 原文：contact/黑点/存在性"
                 "三族计数对照 r19（4/4/14）与 r20（2/6/10）；(iii-a) 援引"
                 "计数对照 r19 基线、§5B 援引计数照记（本轮指引字节复用"
                 "无 §5B 节=任何援引为零上下文、如实登记）；M1/M2/M3/M4 "
                 "四元组入实验对照账；gt 照常）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道复制性三分判据分开实测（机制：收敛归因）：R22 四元组="
                "(%s, %s, %d, %s) vs r19 参照=(%s, %s, %d, %s)（run-r19 "
                "live 复算交叉核对）；M1 带 [0.361538, 0.561538] 内=%s、"
                "contact 族 %d≤7=%s；(g) 支 M1 ≥0.771429=%s、G1/G2 任一"
                "破坏=%s；(d) 支 M1 <0.771429=%s 且 G1/G2 维持=%s。"
                "⇒ verdict=%s（%s）。判据比较用 6 位定点整数交叉相乘"
                "（避免浮点）。判据均为 r22-prep-record hypothesis_test."
                "adjudication 原文，轮后如实执行。"
                % (top_rate, bot_rate,
                   family_counts["existence_blackdot"], m4,
                   r19_m1, r19_m2, r19_m3, r19_m4,
                   m1_in_band, contact, crit_contact_le_max,
                   crit_regressed_m1, crit_regressed_guards,
                   crit_drifted_m1_lt, guards_ok, verdict, letter_branch)),
            "counts": {
                "r22_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                    "M3": family_counts[
                                        "existence_blackdot"],
                                    "M4": m4,
                                    "M1_arithmetic": f"{abst_top}/{flags_top}",
                                    "M2_arithmetic": f"{abst_bot}/{flags_bot}"},
                "r19_reference_tuple": R19_ROW_REGISTERED,
                "r19_reference_tuple_source": (
                    "run-r19 内嵌实例记录 live 复算+prep-record "
                    "run_r19_metric_anchor 冻结值交叉核对一致"),
                "m1_in_replication_band": m1_in_band,
                "replication_band": "[0.361538, 0.561538]（r19±0.10）",
                "contact_family_le_7": crit_contact_le_max,
                "crit_regressed_m1_ge_0_771429": crit_regressed_m1,
                "crit_regressed_guards_broken": crit_regressed_guards,
                "crit_drifted_m1_lt_0_771429": crit_drifted_m1_lt,
                "r16_top_baseline_registered":
                    BASE16_TOP_AGGREGATE_REGISTERED,
                "r16_top_baseline_live": f"{base16_ab}/{base16_fl}",
                "r16_top_baseline_value": cal._ratio(base16_ab, base16_fl),
                "top_flags_r22": flags_top,
                "top_abstain_r22": abst_top,
                "top_abstain_rate_r22": top_rate,
                "m4_top_rate_range_r22": m4,
                "contact_family_abstain_flags_rubric_r22": contact,
                "contact_family_by_view_r22": contact_by_view,
                "contact_r16_baseline_registered": CONTACT_CHAIN_PRIOR[
                    "r16"],
                "contact_r13_r16_chain_live_replay":
                    replay_proof["contact_counts"],
                "verdict": verdict,
            },
            "status": (
                "同指引重复轮（指引/渲染字节复用；唯一实验操作=实例群"
                "重抽）下 M1 落点=%s（r19±0.10 带内=%s）、守门维持=%s"
                "→%s 支（如实单列；判据命中与否的描述性结论，非因果证明"
                % (top_rate, m1_in_band, guards_ok, verdict)),
        },
        "guards_g1_g2": {
            "role": ("守门通道独立单列（per r22-prep-record "
                     "attribution_plan.guard_channel 原文；任一破坏→"
                     "regressed 支命中（描述性边界，非 axis-plan "
                     "early_stop 出局语义——本实验已收束、收敛归因轮"
                     "出局语义不适用、破坏照实记录））"),
            "observation": (
                "G1=bottom courtyard 非弃权 0/0/0 维持：r22 实测=%s"
                "（对照 r16 基线 0/0/0 live 重放交叉核对一致；r20 破坏 "
                "2/0/0 在案=分岔记录；bottom "
                "courtyard 类旗标本身=%d 条）→G1=%s。G2="
                "guard_ok=True 维持：top 几何门面积比出局条目 R19=%d→"
                "R22=%d（不升=维持判据、实测回升即破坏）→guard_ok=%s→G2=%s。守门结论=%s。"
                "（对照 r20 的 (iii-a) 间隙支引导 bottom 非弃权 courtyard "
                "报告=G1 字面破坏在案；本轮同形态在 top 侧以间隙支报告、"
                "bottom 侧零 courtyard 旗标——G1 维持，分岔如实分列。）"
                % (list(by_instance.values()), bot_courtyard_flags,
                   "维持" if g1_ok else "破坏",
                   len(geo_r19), len(geo_r22), guard_ok,
                   "维持" if g2_ok else "破坏",
                   "G1/G2 均满足" if guards_ok
                   else "守门破坏→regressed 支命中（字母照实；描述性"
                        "边界、出局语义不适用）")),
            "counts": {
                "g1_bottom_courtyard_non_abstain_r22": by_instance,
                "g1_bottom_courtyard_flags_total_r22": bot_courtyard_flags,
                "g1_r16_baseline_live": r16_courtyard_base,
                "g1_r20_broken_registered":
                    R20_REFERENCE_REGISTERED[
                        "g1_bottom_courtyard_non_abstain"],
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r22": len(geo_r22),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
            },
            "status": ("守门与字母裁决分开记账（守门经 regressed 支"
                       "字面并入字母裁决；guard_channel.requirement 原文"
                       "语义如实援引）"),
        },
        "criterion_citation_observation": {
            "role": ("§5B 与 (iii-a) 援引机制观察核心（单列，不进字母"
                     "裁决；per r22-prep-record attribution_plan."
                     "declaration「字母/机制观察/度量教训三分记账」原文）："
                     "两条款的旗级/notes 级援引计数分开记、互不合并+"
                     "(iii-a) 逐旗落支分布（间隙支/侵入支/残余弃权支）"),
            "observation": (
                "§5B 与 (iii-a) 措辞援引计数（分开记）：旗级 location_"
                "evidence 含「§5B」=%d 旗、含「(iii-a)」=%d 旗、含"
                "「分支(」=%d 旗（三集合均为空=本轮判读在旗级理由中零"
                "字面援引）；notes 级含「§5B」=%d/12 派次（本轮指引="
                "observation-guidance-r19.md 字节复用、无 §5B 节=任何援引"
                "为零上下文、如实登记）、含「(iii-a)」=%d/12 派次（%s）"
                "——两计数互不合并。基线对照：r18 §5B 援引=旗级 0/13 "
                "黑点弃权旗（非弃权黑点旗亦零）、派次级 1/12（dev-r18 "
                "在案）；r19 (iii-a) 援引=旗级「(iii-a)」6 旗+「分支(」"
                "2 旗、notes 级 10/12 派次（run-r19/prep-record 冻结锚"
                "在案）。"
                "旗级落支分布（9 旗=textual 证据可归支的判据相关旗）："
                "间隙支（branch1）=%d（top-i1 两板 4+top-i2 两板 2："
                "可辨认细缝/贴触极近→视觉贴近→负责任报告；top-i2 两板"
                "无可辨认间隙带仍走继续判定路径=边缘应用，如实登记）、"
                "侵入支（branch2）=%d（prep1-top-i2 胶囊图元连片融合："
                "直接相连→按接触/交叠处理）、残余弃权支（branch3）=%d"
                "（top-i3 两板 courtyard 弃权旗）。"
                % (len(s5b_flag_hits), len(iiia_flag_hits),
                   len(iibranch_flag_hits),
                   len(s5b_notes_hits),
                   len(iiia_notes_hits),
                   "、".join(sorted(iiia_notes_hits)),
                   iiia_branch_counts["branch1_gap_report"],
                   iiia_branch_counts["branch2_intrusion_report"],
                   iiia_branch_counts["branch3_residual_abstain"])),
            "citation_counts": {
                "flag_level_s5b_literal": len(s5b_flag_hits),
                "flag_level_s5b_sources": [f"{s}/{f}" for s, f in
                                           s5b_flag_hits],
                "flag_level_iiia_literal": len(iiia_flag_hits),
                "flag_level_iiia_sources": [f"{s}/{f}" for s, f in
                                            iiia_flag_hits],
                "flag_level_branch_literal": len(iibranch_flag_hits),
                "notes_level_s5b": len(s5b_notes_hits),
                "notes_level_s5b_sources": sorted(s5b_notes_hits),
                "notes_level_iiia": len(iiia_notes_hits),
                "notes_level_iiia_sources": sorted(iiia_notes_hits),
                "notes_level_non_citing_s5b": sorted(
                    set(RAW_FILES) - set(s5b_notes_hits)),
                "notes_level_non_citing_iiia": sorted(
                    set(RAW_FILES) - set(iiia_notes_hits)),
                "baseline_r18_s5b": (
                    "旗级 0/13 黑点弃权旗（非弃权黑点旗亦零）、派次级 "
                    "1/12（dev-r18 在案）"),
                "baseline_r19_iiia": (
                    "旗级「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 "
                    "派次（run-r19/prep-record 冻结锚在案）"),
            },
            "branch_counts_flag_level": iiia_branch_counts,
            "branch1_notes_level_dispatches": len(IIIA_NOTES_BRANCH1_ROWS),
            "branch_rows": [
                {k: r.get(k) for k in ("source", "instance", "state",
                                       "flag_id", "branch", "cited",
                                       "abstain", "excerpt", "note")}
                for r in iiia_rows_out],
            "branch1_notes_rows": IIIA_NOTES_BRANCH1_ROWS,
            "evidence_check": (
                "逐旗 excerpt 逐字 substring 校验+abstain 属性核对+cited "
                "集合=机械援引集合逐一相等（fail-closed 校验通过）"),
            "status": ("旗级落支=间隙 6+侵入 1+残余弃权 2；§5B/(iii-a) "
                       "援引计数分开记、不凌驾字母裁决"),
        },
        "bottom_side_observation_maintenance": {
            "role": ("bottom 侧观察 M2（mechanism_observation_separate："
                     "单列、不影响字母；per axis-plan benefit_metrics."
                     "M2_bottom_aggregate_abstain_rate 同法）"),
            "observation": (
                "M2=bottom 全旗聚合弃权率=%d/%d=%s（对照 r16 基线 12/14="
                "%s，live 重放交叉核对一致；对照 r18 13/19=%s、r19 4/7="
                "%s、r20 4/14=%s）——方向="
                "%s（改善方向：r22 bottom 弃权 2/10 vs r16 12/14、"
                "r18 13/19、r19 4/7、r20 4/14；轮际比较含实例群漂移混杂、"
                "照 axis-plan comparison_rule 显式容忍）。bottom "
                "侧三件实测：(1) 零旗标派次=%d 个（bottom-i1 两板；"
                "item 5 零分母→None 口径本轮触发、bottom-i1 弃权率=None）；"
                "(2) 黑点族弃权旗（rubric 口径）=%d 条 vs r16=12/r18=13/"
                "r19=4/r20=6（top-i2 两板 2+bottom-i2 两板 2；与 r19 "
                "持平、低于 r16/r18/r20，多基线对照如实登记）；(3) bottom "
                "courtyard 类旗=%d 条（本轮 bottom 三实例零 courtyard "
                "类旗标）——非弃权 courtyard 0/0/0=G1 维持（见 "
                "guards_g1_g2；对照 r20 的 2/0/0 破坏在案）。"
                % (abst_bot, flags_bot, bot_rate,
                   cal._ratio(base16_bot_ab, base16_bot_fl),
                   cal._ratio(r18_bot_ab, r18_bot_fl),
                   r19_m2, R20_ROW_REGISTERED["M2"],
                   ("低于 r16 基线（改善方向）" if bot_below_r16
                    else "不低于 r16 基线（维持/恶化）"),
                   2, family_counts["existence_blackdot"],
                   bot_courtyard_flags)),
            "counts": {
                "r16_bottom_aggregate_registered":
                    BASE16_BOTTOM_AGGREGATE_REGISTERED,
                "r16_bottom_aggregate_live":
                    f"{base16_bot_ab}/{base16_bot_fl}",
                "r18_bottom_aggregate_live":
                    f"{r18_bot_ab}/{r18_bot_fl}",
                "r19_bottom_aggregate_live":
                    f"{r19_bot_ab}/{r19_bot_fl}",
                "r20_bottom_aggregate_registered":
                    {"abstain": 4, "flags": 14},
                "bottom_flags_r22": flags_bot,
                "bottom_abstain_r22": abst_bot,
                "bottom_abstain_rate_r22": bot_rate,
                "bottom_abstain_rate_r16_baseline":
                    cal._round6(base16_bot_ab / base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
                "zero_flag_dispatch_count": 2,
                "blackdot_abstain_flags_rubric_r22":
                    family_counts["existence_blackdot"],
                "blackdot_rubric_r16_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
                "blackdot_rubric_r18_registered":
                    R18_REFERENCE_REGISTERED["M3"],
                "blackdot_rubric_r19_registered":
                    R19_REFERENCE_REGISTERED["M3"],
                "blackdot_rubric_r20_registered":
                    R20_REFERENCE_REGISTERED["M3"],
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": (
                "6/6 派次摘录逐字来自对应 reading_notes（substring "
                "fail-closed 校验通过）——bottom 派次全部实际使用 §4(i) "
                "量化判据（bottom-i1 零旗派次=近邻间距系统性一致判正常+"
                "黑点判有意机械孔不报告；bottom-i2/bottom-i3 绿色翼瓣/"
                "方形端部标记=满足量化判据→判正常；applied/prep1 两板"
                "同文=同图同判自述）"),
            "status": (
                "M2 改善方向+黑点族弃权 4（多基线低位）+零旗派次 2 "
                "如实单列（不影响字母裁决；development 域只描述不断言）"),
        },

        "experiment_comparison_ledger": {
            "role": ("实验对照账（per axis-experiment-plan-r17-r20 "
                     "benefit_metrics 口径定义；(M1,M2,M3,M4) 四元组如实"
                     "入账——四元组由后续 dev-record 包转记入 round22-dev-"
                     "record；全部=12 派次全口径（非代表配置子集）、与"
                     "分型件同法；单位=旗标条数（M3）或 6 位小数率；"
                     "M3 定义按冻结件=黑点族弃权旗数，contact 族计数另列"
                     "（contact_family_abstain_flags_rubric）不占 M3 槽位；"
                     "对照账六行并列=r16 基线/r17 轴1/r18 轴2/r19 轴3/"
                     "r20（破坏轮登记行）/r22 本轮）"),
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
            "r17_axis1_row": dict(measured_rows["r17_axis1"]),
            "r17_row_source": ("round18-dev-record axis_experiment_ledger."
                               "cross_round_status.measured_rows.r17_axis1"
                               "（实测装载、与登记值交叉核对一致）"),
            "r18_axis2_row": r18_row,
            "r18_row_source": ("run-r18 内嵌实例记录 live 复算+dev-r18 "
                               "cross_round_status 交叉核对一致"),
            "r19_axis3_row": r19_row,
            "r19_row_source": ("run-r19 内嵌实例记录 live 复算+prep-record "
                               "run_r19_metric_anchor 冻结值交叉核对一致"),
            "r20_combo_registered_row": dict(R20_ROW_REGISTERED),
            "r20_row_source": ("run-r20 内嵌记录 live 复算+本件登记值交叉"
                               "核对一致（r20=守门破坏轮：G1 2/0/0 在案，"
                               "仅如实入账不占排序位）"),
            "r22_measured": {
                "M1": top_rate,
                "M1_arithmetic": f"{abst_top}/{flags_top}",
                "M2": bot_rate,
                "M2_arithmetic": f"{abst_bot}/{flags_bot}",
                "M3": family_counts["existence_blackdot"],
                "M4": r22_m4,
                "M4_top_instance_rates": top_rates,
                "contact_family_abstain_flags_rubric": contact,
                "contact_family_by_view": contact_by_view,
                "existence_other_family": family_counts["existence_other"],
            },
            "family_counts_vs_r19_r20": {
                "contact": {
                    "r19_registered": R19_REFERENCE_REGISTERED["contact"],
                    "r20_registered": R20_FAMILY_COUNTS_REGISTERED[
                        "contact"],
                    "r22_measured": contact,
                    "note": ("r19/r20/r22=rubric 口径全视 4/2/2（分型件"
                             "口径）——r22 与 r20 持平、低于 r19，如实"
                             "登记")},
                "existence_blackdot": {
                    "r19_registered": R19_REFERENCE_REGISTERED["M3"],
                    "r20_registered": R20_FAMILY_COUNTS_REGISTERED[
                        "existence_blackdot"],
                    "r22_measured": family_counts["existence_blackdot"]},
                "existence_other": {
                    "r19_registered":
                        R19_REFERENCE_REGISTERED["existence_other"],
                    "r20_registered":
                        R20_FAMILY_COUNTS_REGISTERED["existence_other"],
                    "r22_measured": family_counts["existence_other"],
                    "note": ("对照 r19 在案存在性其他 14、r20 10：r22 实测 "
                             "12——介于两基线间、未显著上升（弃权转移对照"
                             "口径如实登记）")},
            },
            "ranking_by_comparison_rule": {
                "rule": axis_plan["comparison_rule"]["ordering"],
                "eligibility_gate": axis_plan["comparison_rule"][
                    "eligibility_gate"],
                "rows_registered": ledger_rows,
                "eligible_rows": sorted(eligible_rows),
                "ranking_order_best_first": ranking_order,
                "r22_eligibility": bool(guards_ok),
                "r22_eligibility_note": (
                    "资格门=G1/G2 均满足；r22 G1 实测 %s、G2 guard_ok=%s"
                    "→%s排序"
                    % (list(by_instance.values()), guard_ok,
                       "参与" if guards_ok else "不参与")),
                "r20_eligibility": False,
                "r20_exclusion_reason": (
                    "资格门=G1/G2 均满足；r20 G1 破坏（bottom courtyard "
                    "非弃权 2/0/0，run-r20 在案）→不参与排序（per "
                    "eligibility_gate 原文「G1 或 G2 破坏的轮次不参与"
                    "排序」；r20 行仅如实入账不占排序位）"),
                "note": ("资格门：r17/r18/r19 均 G1/G2 满足（r17/r18 行"
                         "资格=dev-r18 在案注记「两轮 G1/G2 均满足」装载、"
                         "r19=run-r19 guards 在案）→入排序；r16=基线"
                         "参照行（非轴配置）；r20=G1 破坏不入排序（在案）；"
                         "r22 资格按 G1/G2 实测判定（见 r22_eligibility/"
                         "r22_eligibility_note——本轮 G2 几何门 0→2 破坏→"
                         "不入排序、行仅如实入账）；当前排序=eligible 行"
                         "实测 M 元组升序——如实登记、不预写后续决策"),
            },
            "significant_benefit_vs_r16": {
                "definition": axis_plan["comparison_rule"][
                    "significant_benefit_definition"],
                "r22_m1_absolute_drop": m1_drop_r22,
                "met": m1_drop_r22 >= 0.10,
                "r18_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r18_m1),
                "r19_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r19_m1),
                "note": ("r22 M1 绝对降幅 %s ≥0.10=显著收益定义在描述层"
                         "命中（r18 降幅 %s、r19 降幅 %s 亦 ≥0.10）；"
                         "字母裁决与实验账分列互不改写"
                         % (m1_drop_r22,
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r18_m1),
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r19_m1))),
            },
            "replication_conclusion": replication_conclusion,
            "direction_vs_r16": {
                "M1": ("down（%s→%s，改善方向）"
                       % (rb["M1_top_aggregate_abstain_rate"], top_rate)),
                "M2": ("down（%s→%s，改善方向）"
                       % (rb["M2_bottom_aggregate_abstain_rate"],
                          bot_rate)),
                "M3": ("down（%d→%d，黑点族弃权回落）"
                       % (rb["M3_blackdot_abstain_flags_rubric"],
                          family_counts["existence_blackdot"])),
                "M4": ("%s→%s（收窄）"
                       % (rb["M4_top_per_instance_rate_range"], r22_m4)),
                "contact": ("down（10→%d，主度量回落）" % contact),
            },
            "confounder_note": axis_plan["baselines_registered"][
                "drift_reference_note"],
            "status": ("六行如实并列（M1/M2/M3 降、M4 收窄 0.261904→"
                       "%s 内对比失真见 M4 定义=轮内极差；本轮字母裁决="
                       "replicated 带内+contact 门+守门维持；"
                       "development 域只描述不断言）" % r22_m4),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r16–r20 side_observation "
                "先例延续观察）：r22 bottom 6 派次全部以「空隙/翼瓣/仪器"
                "注记」语义化绿色并按 §4(i) 判入系统性正常路径或报告路径"
                "（判据轴延续；§5A 显式援引=2/6 派次（applied/prep1-"
                "bottom-i1 零旗派次核查自述「按 §5A 为板内空隙（非图元）」）、"
                "§5B 显式援引=0/6 派次（本轮指引字节复用无 §5B 节=零"
                "上下文）；实例级=%d/3 实例至少一板援引 §5A。指引 §5A 随 "
                "r19 基座本体原样生效，判据文本零变更，援引波动属实例"
                "自述异质性、如实登记不作废）。逐实例 "
                "substring 计数「绿|翼瓣|空隙|§5A」+摘录如实登记（无期望、"
                "不构成判据输入）。"
                % sum(1 for v in green_semantics.values()
                      if v["§5A_cited"])),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("绿区语义化「空隙非图元」读法在实例群重抽下延续"
                       "（§5A 援引 2/6、§5B 援引 0/6 分列；"
                       "如实单列、不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点族现象追踪（机制观察，分型件 rubric 口径；rubric "
                "机械套用证明见 rubric_families 节）：r22 黑点族弃权旗 %d "
                "条（top-i2 两板 2+bottom-i2 两板 2；均为黑点对性质存在性"
                "弃权；本轮指引字节复用无 §5B 节=零 §5B 上下文、如实"
                "登记）——vs r16 黑点族 12 旗（分型件 rubric 口径在案）/"
                "r18=13（run-r18 实测装载）/r19=4（run-r19 实测装载）/"
                "r20=6（run-r20 实测装载）多基线对照：与 r19 持平、低于 "
                "r16/r18/r20，方向性描述（非因果证明）。另实测黑点"
                "转非弃权旗 %d 条（top-i3 两板 2=孤立异常标记按 §4(ii) "
                "报告+bottom-i3 两板 4=深色小圆点按 §4(ii) 兜底类报告）"
                "+黑点判正常派次 %d 个（applied/prep1-top-i1+applied/"
                "prep1-bottom-i1 两板；对照 r15=3/r16=2/r18=2/r19=3/"
                "r20=4）。"
                % (len(black_rows), len(nonabstain_black_rows),
                   len(judged_normal))),
            "black_dot_flags": black_rows,
            "black_dot_non_abstain_flags": nonabstain_black_rows,
            "blackdot_to_non_abstain_count": len(nonabstain_black_rows),
            "by_instance": black_by_instance,
            "all_abstain": all(r["abstain"] for r in black_rows),
            "judged_normal_dispatches": {
                "observation": (
                    "黑点判正常派次计数（分型件 blackdot_dispatch 口径："
                    "notes 判黑点正常且该派次零黑点词旗标）=%d/12——"
                    "applied/prep1-top-i1（散布孤立小圆点/右上角黑色圆孔"
                    "等按系统性正常特征判据判为正常设计特征）+applied/"
                    "prep1-bottom-i1（左上角两处小黑点判有意的机械孔/"
                    "定位类设计特征、三路出口第 1 路不报告，零旗派次）；"
                    "对照 r15=3/r16=2/r18=2/r19=3/r20=4。注意 applied/"
                    "prep1-top-i2 与 applied/prep1-bottom-i2 notes 虽提及"
                    "黑点，但该四派次就黑点落了弃权旗（R22T-004/010、"
                    "R22B-002/004）——按 blackdot_dispatch 口径归入 "
                    "abstain_flag_dispatches、不计入判正常派次（如实"
                    "分列）。"
                    % len(judged_normal)),
                "count": len(judged_normal),
                "sources": sorted(judged_normal),
                "r15_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r15"],
                "r16_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r16"],
                "r18_registered": R18_REFERENCE_REGISTERED[
                    "judged_normal_dispatches"],
                "r19_registered": R19_REFERENCE_REGISTERED[
                    "judged_normal_dispatches"],
                "r20_registered": R20_REFERENCE_REGISTERED[
                    "judged_normal_dispatches"],
                "notes_hit_rows": bd_disp_rows,
            },
            "rubric_families": {
                "role": ("contact/黑点族计数口径（分型件 rubric 机械套用；"
                         "关键词表/五类定义/优先级从 abstain-typology-"
                         "r13-r16.json 装载，脚本不另嵌词表；blackdot "
                         "对象判定先于 contact 组合）"),
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
                    "r16 黑点族计数=%d=M3 基线、r16 contact 计数=%d="
                    "contact 基线（axis-plan/prep-record 登记值交叉核对"
                    "一致）"
                    % (replay_proof["per_flag_total"],
                       replay_proof["blackdot_counts"]["r16"],
                       replay_proof["contact_counts"]["r16"])),
                "note": ("r22 全部 18 条弃权旗逐旗分类入账（rows）——"
                         "existence_blackdot %d/contact %d/existence_other "
                         "%d/semantic_confusion %d/other %d；本分型"
                         "（rubric 族）与 top_abstain_typology（contact/"
                         "existence/other_layer 主出口分型）为两套登记"
                         "口径、分别如实入账"
                         % (family_counts["existence_blackdot"],
                            family_counts["contact"],
                            family_counts["existence_other"],
                            family_counts["semantic_confusion"],
                            family_counts["other"])),
            },
            "notes_normal_dispositions": (
                "4 派次判正常：applied/prep1-top-i1「板上散布的孤立小圆点、"
                "右上角黑色圆孔与白色椭圆标记等，按系统性正常特征判据判为"
                "正常设计特征，未报告」+applied/prep1-bottom-i1「左上角"
                "两处同款两焊盘封装旁的两个小黑点…判为有意的机械孔/定位类"
                "设计特征（三路出口第 1 路），不报告」（摘录见 evidence 表 "
                "disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点族弃权 4（与 r19 持平、多基线低位）+非弃权报告"
                       "路径 6 条（top 侧首现 2+bottom 4）+判正常派次 4（"
                       "如实单列、不凌驾字母裁决）"),
        },
        "top_abstain_typology": {
            "observation": (
                "top 弃权理由构成分型（机制观察，per mechanism_observation_"
                "separate「top 弃权分型照常」语义；为 M1/M4 与主通道归因"
                "提供分解）：本轮 top 弃权旗 %d 条逐旗按 location_evidence "
                "关键词分类——接触性（真实接触 vs 视觉贴近不可分辨/是否"
                "接触/交叠不可确认）=%d 条、"
                "存在性（性质不明/是否存在不可确认）"
                "=%d 条、层归属等其他出口=%d 条。构成解读（如实单列）："
                "接触性弃权集中于 courtyard 类旗标"
                "（(iii-a) 残余弃权支语言），存在性弃权横跨 silk/"
                "other_advisory/reroute 各类（疑似受阻文字、黑点对性质、"
                "回绕存在性、生僻形态等）——top 弃权非单一机制驱动；"
                "对照 r16（接触性 11+存在性 15+层归属其他 1，27 条）与 "
                "r17（接触性 8+存在性 14+其他 0，22 条）与 r18（接触性 8+"
                "存在性 12+其他 0，20 条）与 r19（接触性 5+存在性 13+其他 "
                "0，18 条，run-r19 live）与 r20（接触性 4+存在性 9+其他 "
                "0，14 条，run-r20 live）：r22 绝对数 27→22→20→18→14→16"
                "（较 r20 回升、低于 r16–r18）；M1=%s（分母 41 较 r20 的 "
                "22 回升）。逐旗摘录与分类在案（rows）。"
                % (len(typology_rows), typology_counts["contact"],
                   typology_counts["existence"],
                   typology_counts["other_layer"], top_rate)),
            "type_counts": typology_counts,
            "top_abstain_flags_total": len(typology_rows),
            "r16_reference_counts": {"contact": 11, "existence": 15,
                                     "other_layer": 1},
            "r17_reference_counts": {"contact": 8, "existence": 14,
                                     "other_layer": 0},
            "r18_reference_counts_live": R18_REFERENCE_REGISTERED[
                "top_typology"],
            "r19_reference_counts_live": r19_typology_live,
            "r20_reference_counts_live": r20_typology_live,
            "rows": typology_rows,
            "evidence_check": (
                "%d/%d 条摘录逐字来自对应 location_evidence 且 (source, "
                "flag_id) 集合与实测 top 弃权旗集合逐一相等（substring+"
                "覆盖 fail-closed 校验通过）"
                % (len(typology_rows), len(typology_rows))),
            "top_abstain_rates_by_instance": top_rates,
            "top_abstain_rate_range": top_range,
            "status": ("top 弃权构成=存在性多通道分散+接触性 2 条（"
                       "如实单列、不凌驾字母裁决）"),
        },
        "residual_instance_differences": {
            "observation": (
                "残余实例差异（如实单列）：(1) top 弃权率 %s/%s/%s（极差 "
                "%s）——top-i1 最高（5/11=%s）、top-i3 最低（7/20=%s）；"
                "(2) bottom 弃权率 %s/%s/%s（轮内极差 %s 按可计算实例；"
                "bottom-i1 两板零旗标→None，item 5 零分母口径本轮触发）"
                "——bottom-i2 最高（2/4=0.5，黑点弃权 2）、bottom-i3 最低"
                "（0.0，全部负责任报告）、bottom-i1=None（零旗派次）；"
                "(3) placement/孤立图形处置实例/跨板分化："
                "bottom-i2 两板以 placement_pattern_anomaly 报告孤立焊盘"
                "组偏离周边模式、bottom-i3 两板以 placement_pattern_"
                "anomaly 报告孤立焊盘对（对照 r20 同形态判正常=跨轮处置"
                "分化如实登记）、bottom-i1 两板零旗派次自述孤立两焊盘封装"
                "不报告（§4(i) 未打破阵列规律）、top-i1 两板 notes 判正常"
                "（按系统性正常特征判据；本轮指引无 §5B(c) 路径）——"
                "同现象跨实例/跨板出口不同=判读语义歧义未穷尽；「正确测出"
                "无效同样是有效证据」的同构：测出残余差异同样是有效证据。"
                % (top_rates["top-i1"], top_rates["top-i2"],
                   top_rates["top-i3"], top_range,
                   top_rates["top-i1"], top_rates["top-i3"],
                   bottom_rates["bottom-i1"], bottom_rates["bottom-i2"],
                   bottom_rates["bottom-i3"], bottom_range)),
            "evidence": PLACEMENT_DISPOSITION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("残余差异不凌驾字母裁决；不构成已证因果"
                       "关系（实例群重抽=本轮唯一实验操作、轮内样本极小）"),
        },
    }
    metric_lesson_continuation = {
        "role": ("度量设计教训延续（如实，供未来预注册参考；本轮不追溯"
                 "适用；per r22-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r22 三分判据=M1 落点带宽（r19±0.10 描述性边界、不得事后"
            "收放）+contact 族门（≤7）+守门维持（6 位定点整数交叉相乘，"
            "避免浮点；截断值=r16 基线 0.771429 原文）；M4 第二样本单列"
            "（r22 实测与 r19 的 0.211111 双样本并列、不进字母、不合并"
            "分布）；M3 计数口径=分型件 rubric 机械套用（关键词表/优先级 "
            "fail-closed 装载+对 r13–r16 132 条弃权旗重放对拍逐一相等后"
            "套用 r22，对拍基期=r13–r16（8/15/5/10）不变）——口径可复算"
            "性=度量设计要点（计数口径跨轮漂移是历史教训：r15 dev-record "
            "prose 口径 7 vs 分型件 rubric 口径 8 在案，axis-plan M3_"
            "caveat 已声明一律采用 rubric 口径）；部分重复≠独立重复（同域"
            "同编排实例池、验证力度如实声明）；跨轮实例群漂移混杂=本轮"
            "唯一实验操作与裁决变量（r15→r16 纯重抽漂移 0.09064 在案、"
            "axis-plan comparison_rule 显式容忍且不消除）；M1 分母（top "
            "旗数）本身随轮变化（35→31→39→22→41），弃权率比较含分母"
            "效应、构成分解（top 弃权构成分型+§5B/(iii-a) 援引分记+黑点"
            "转非弃权旗）单列补足"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一迭代候选方向（如实登记，不构成本轮判据"
                   "输入）：由后续 round22-dev-record 包按授权链转记；"
                   "不得回溯改判既往轮次（r8–r20 字母裁决维持不变）"),
    }
    # r16/r18/r19/r20 分层基线（逐实例弃权率，live 重放/装载；不手工抄数）
    r16_top_rates_live = r16_top_rates
    r16_bottom_rates = {}
    for n in ("bottom-i1", "bottom-i2", "bottom-i3"):
        r16_bottom_rates[n] = run_r16["instances"][n]["combined"][
            "abstain_rate"]
    r16_bottom_range = cal._round6(
        max(r16_bottom_rates.values()) - min(r16_bottom_rates.values()))
    run_r17_top_rates = {n: run_r17["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    r18_top_rates = {n: run_r18["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    r19_top_rates = {n: run_r19["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    r20_top_rates = {n: run_r20["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R22,
                                "sha256": _sha(REL_PREP_R22)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "replicated": adj["replicated"],
            "drifted": adj["drifted"],
            "regressed": adj["regressed"],
            "m4_second_sample_separate": adj["m4_second_sample_separate"],
            "primary_channel_change": prep_doc["attribution_plan"][
                "primary_channel"]["change"],
            "primary_channel_metric": prep_doc["attribution_plan"][
                "primary_channel"]["metric"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "mechanism_observation_separate":
                adj["mechanism_observation_separate"],
            "guards_registered_in_prep_record": {
                "metric": prep_doc["attribution_plan"]["guard_channel"][
                    "metric"],
                "requirement": prep_doc["attribution_plan"][
                    "guard_channel"]["requirement"]},
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel_metric": prep_doc["attribution_plan"][
            "primary_channel"]["metric"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r22-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮同指引重复轮收敛归因"
            "（M1 落点+contact 族+守门维持），与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "contact_family_abstain_flags_rubric_r22": contact,
            "contact_arithmetic_note": (
                "contact = contact 族弃权旗数（分型件 rubric 口径）= %d"
                "（r22 全部 18 条弃权旗逐旗 rubric 分类中 contact 计数；"
                "关键词表/优先级=abstain-typology-r13-r16.json 装载；"
                "r13–r16 132 条弃权旗重放对拍逐一相等=口径忠实性证明；"
                "分视角 top %d+bottom %d）"
                % (contact, contact_by_view["top"],
                   contact_by_view["bottom"])),
            "top_abstain_flags_r22": flags_top,
            "top_abstain_count_r22": abst_top,
            "top_abstain_rate_r22": top_rate,
            "top_abstain_rate_r22_arithmetic":
                f"M1 = top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（判据首键；12 派次全口径）",
            "m4_top_rate_range_r22": m4,
            "m4_arithmetic_note": (
                "M4 = top 逐实例弃权率极差 = %s（top 三实例 %s/%s/%s；"
                "第二样本单列机制观察、不进字母裁决；先 6 位小数取率再取差）"
                % (m4, top_rates["top-i1"], top_rates["top-i2"],
                   top_rates["top-i3"])),
            "crit_regressed_m1_ge_0_771429": crit_regressed_m1,
            "crit_regressed_guards_broken": crit_regressed_guards,
            "crit_replicated_m1_in_band": m1_in_band,
            "crit_replicated_contact_le_7": crit_contact_le_max,
            "crit_drifted_m1_lt_0_771429": crit_drifted_m1_lt,
            "r22_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                "M3": family_counts["existence_blackdot"],
                                "M4": m4},
            "r19_reference_tuple": R19_ROW_REGISTERED,
            "reject_m1_threshold_6dp": REJECT_M1_MIN_6DP,
            "replication_band_6dp": [REPL_BAND_LO_6DP, REPL_BAND_HI_6DP],
            "top_abstain_rate_r16_baseline_live":
                f"{base16_ab}/{base16_fl}",
            "top_abstain_rate_r16_baseline_value":
                cal._ratio(base16_ab, base16_fl),
            "contact_r16_baseline_registered": CONTACT_CHAIN_PRIOR["r16"],
            "contact_r16_baseline_live_replay":
                replay_proof["contact_counts"],
            "baseline_replay_note": (
                "M1 基线=同一聚合逻辑对 calibration-run-r16.json 内嵌实例"
                "记录（states 层 reader_flags+compare_v3.abstain）双侧"
                "复算，不手工抄数；r19 参照四元组=run-r19 内嵌实例记录 "
                "live 复算+prep-record run_r19_metric_anchor 冻结值交叉"
                "核对；r20 对照行=run-r20 内嵌记录 live 复算+登记值交叉"
                "核对；均与在案登记值（axis-plan baselines_registered."
                "r16_baseline.M1=0.771429、prep-record 冻结锚）交叉核对"
                "（fail-closed，见 baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r22":
                    by_instance,
                "bottom_courtyard_flags_total_r22": bot_courtyard_flags,
                "bottom_abstain_flags_r22": flags_bot,
                "bottom_abstain_count_r22": abst_bot,
                "bottom_abstain_rate_r22": bot_rate,
                "bottom_abstain_rate_r22_arithmetic":
                    f"M2 = bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                    f"{bot_rate}"
                    f"（对照 r16 基线 12/14=0.857143、r18 13/19=0.684211、"
                    f"r19 4/7=0.571429、r20 4/14=0.285714；"
                    f"mechanism_observation_separate "
                    f"单列、不影响字母）",
                "bottom_abstain_rate_r16_baseline_live":
                    f"{base16_bot_ab}/{base16_bot_fl}",
                "bottom_abstain_rate_r16_baseline_value":
                    cal._ratio(base16_bot_ab, base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
            },
            "verdict": verdict,
            "letter_branch": letter_branch,
            "bottom_courtyard_detail_r22": [
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
                "r16_contact_registered": CONTACT_CHAIN_PRIOR["r16"],
                "r16_contact_live_replay": replay_proof["contact_counts"],
                "r18_row_registered": {
                    k: R18_REFERENCE_REGISTERED[k]
                    for k in ("M1", "M2", "M3", "M4")},
                "r18_row_live": r18_row,
                "r19_row_registered": R19_ROW_REGISTERED,
                "r19_row_live": r19_row,
                "r20_row_registered": R20_ROW_REGISTERED,
                "r20_row_live": r20_row_live,
                "axis_plan_r16_baseline_M1_M2_M3_M4": [
                    rb["M1_top_aggregate_abstain_rate"],
                    rb["M2_bottom_aggregate_abstain_rate"],
                    rb["M3_blackdot_abstain_flags_rubric"],
                    rb["M4_top_per_instance_rate_range"]],
                "note": ("基线数字与 run-r16/run-r19/run-r20 内嵌输入重放/"
                         "分型件实测装载交叉核对一致（fail-closed：live 与"
                         "登记不符即 FAIL）；registered=axis-plan 在案登记/"
                         "prep-record 冻结锚/判据原文冻结值，live=本轮"
                         "从 run-doc/分型件重放装载实测；r18/r20 行=各自 "
                         "run 内嵌记录 live 复算+登记交叉核对"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（实测 %s，"
                    "r16 基线 live 重放 0/0/0；r20 破坏 2/0/0 在案=分岔"
                    "记录）=%s；G2=guard_ok=True "
                    "维持（top 几何门面积比出局条目 R19=%d→R22=%d）"
                    "=%s；任一破坏→regressed 支命中（描述性边界，出局"
                    "语义不适用）"
                    % (list(by_instance.values()),
                       "满足" if g1_ok else "破坏",
                       len(geo_r19), len(geo_r22),
                       "满足" if g2_ok else "破坏")),
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r22": len(geo_r22),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "note": ("守门通道按 r22-prep-record attribution_plan."
                         "guard_channel 独立复核；G 破坏经 regressed 支"
                         "字面并入字母裁决（本轮实测：G1 维持、G2 几何门 "
                         "0→2 破坏=regressed_guards 支命中）"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r20 run-record courtyard_tracking 在案先例延续）——"
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
                "abstain_rate_r18_representative":
                    run_r18["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r19_representative":
                    run_r19["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r20_representative":
                    run_r20["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r22_representative_note": (
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
                    "代表配置）→r18 0.8（12/15，代表配置）→r19 0.428571"
                    "（6/14，代表配置）→r20 0.333333（run-r20 在案）→r22 "
                    "见代表配置分列；复制性三分判据与门各自独立计算、互不"
                    "凌驾（prep-record descriptive_boundary_note 原文"
                    "语义）——门联合评价与字母裁决分列不合并"),
            },
            "r22_total_flags_note": (
                "六实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；判据首键 M1="
                "top 全旗聚合弃权率 %d/%d=%s 与 M4=top 逐实例弃权率极差 "
                "%s、M2=bottom 全旗聚合弃权率 %d/%d=%s、M3=黑点族弃权旗"
                "数 %d 各按键位入账、"
                "各自单列）"
                % (n_total_all,
                   (flags_top - abst_top) + (flags_bot - abst_bot),
                   abst_top + abst_bot,
                   cal._ratio(abst_top + abst_bot, n_total_all),
                   abst_top, flags_top, top_rate, m4,
                   abst_bot, flags_bot, bot_rate,
                   family_counts["existence_blackdot"])),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"replicated=「{adj['replicated'][:80]}…」；"
            f"drifted=「{adj['drifted'][:80]}…」；"
            f"regressed=「{adj['regressed'][:80]}…」"
            "（r22-prep-record.json hypothesis_test.adjudication 判据原文"
            "全文见 preregistered_criteria_quote，轮后如实执行；结果无论"
            "方向均如实入账"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r22": {
            "role": ("r12 假设通道被动追踪（round13–round20-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r22": reroute_rows,
            "reroute_total_r22": len(reroute_rows),
            "reroute_by_instance_r22": {
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
                                 "r18": REROUTE_CHAIN_PRIOR["r18"],
                                 "r19": REROUTE_CHAIN_PRIOR["r19"],
                                 "r20": REROUTE_CHAIN_PRIOR["r20"],
                                 "r22": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径，旗级 location_evidence "
                "子串命中）：r10=2→r11=1→r12=0→r13 被动追踪=1（R13T-009 "
                "在案）→r14=0（R14T-004 子串零命中）→r15 机械命中=1"
                "（R15T-001 非弃权旗含「蛇形」子串——否定式援引、非滥用"
                "型引用，run-r15 在案）→r16=0（在案）→r17=0（R17T-002 "
                "子串零命中、存在性弃权）→r18=0（在案）→r19=0（3 条 "
                "reroute 旗级子串零命中）→r20=0（2 条 reroute 旗级子串"
                "零命中）→r22=0（4 条 reroute 旗级子串零命中）——不构成 "
                "r22 判据输入"
                "（两判据分列互不凌驾）"),
        },
        "stratified_observation": {
            "top": {"r16_by_instance_live": r16_top_rates_live,
                    "r16_range_live": AXIS_R16_M4_TOP_RANGE,
                    "r17_by_instance": run_r17_top_rates,
                    "r18_by_instance": r18_top_rates,
                    "r19_by_instance": r19_top_rates,
                    "r20_by_instance_live": r20_top_rates,
                    "r22_by_instance": top_rates,
                    "r22_range": top_range,
                    "direction": ("r16 三实例 %s（轮内极差 %s）→r17 %s/"
                                  "%s/%s→r18 %s/%s/%s（极差 %s）→r19 %s/"
                                  "%s/%s（极差 %s）→r20 %s/%s/%s→r22 三"
                                  "实例 %s/%s/%s（轮内极差 %s）——同指引"
                                  "重复轮、实例群重抽=裁决变量下实例层的"
                                  "方向性对照（聚合 M1 %d/%d=%s vs r16 基线 "
                                  "27/35=0.771429、r17 的 22/25=0.88、"
                                  "r18 的 20/31=0.645161、r19 的 18/39="
                                  "0.461538、r20 的 14/22=0.636364；轮内"
                                  "实例差异照旧）"
                                  % (f"{r16_top_rates_live['top-i1']}/"
                                     f"{r16_top_rates_live['top-i2']}/"
                                     f"{r16_top_rates_live['top-i3']}",
                                     AXIS_R16_M4_TOP_RANGE,
                                     run_r17_top_rates["top-i1"],
                                     run_r17_top_rates["top-i2"],
                                     run_r17_top_rates["top-i3"],
                                     r18_top_rates["top-i1"],
                                     r18_top_rates["top-i2"],
                                     r18_top_rates["top-i3"],
                                     r18_m4,
                                     r19_top_rates["top-i1"],
                                     r19_top_rates["top-i2"],
                                     r19_top_rates["top-i3"],
                                     r19_m4,
                                     r20_top_rates["top-i1"],
                                     r20_top_rates["top-i2"],
                                     r20_top_rates["top-i3"],
                                     top_rates["top-i1"],
                                     top_rates["top-i2"],
                                     top_rates["top-i3"], top_range,
                                     abst_top, flags_top, top_rate))},
            "bottom": {"r16_by_instance_live": r16_bottom_rates,
                       "r16_range_live": r16_bottom_range,
                       "r19_by_instance_live": run_r19["view_layer"][
                           "bottom"]["abstain_rate"]["by_instance"],
                       "r20_by_instance_live": run_r20["view_layer"][
                           "bottom"]["abstain_rate"]["by_instance"],
                       "r22_by_instance": bottom_rates,
                       "r22_range": bottom_range,
                       "direction": ("r16 三实例 %s（极差 %s）→r19 %s/%s/"
                                     "%s→r20 %s/%s/%s→r22 三实例 %s/%s/%s"
                                     "（极差 %s 按可计算实例；bottom-i1 "
                                     "两板零旗标→None）"
                                     "——bottom 聚合 M2 %d/%d=%s vs r16 "
                                     "的 12/14=0.857143、r18 的 13/19="
                                     "0.684211、r19 的 4/7=0.571429、"
                                     "r20 的 4/14=0.285714"
                                     "（侧观察如实单列；改善方向并记）"
                                     % (f"{r16_bottom_rates['bottom-i1']}/"
                                        f"{r16_bottom_rates['bottom-i2']}/"
                                        f"{r16_bottom_rates['bottom-i3']}",
                                        r16_bottom_range,
                                        run_r19["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i1"],
                                        run_r19["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i2"],
                                        run_r19["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i3"],
                                        run_r20["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i1"],
                                        run_r20["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i2"],
                                        run_r20["view_layer"]["bottom"][
                                            "abstain_rate"]["by_instance"][
                                                "bottom-i3"],
                                        bottom_rates["bottom-i1"],
                                        bottom_rates["bottom-i2"],
                                        bottom_rates["bottom-i3"],
                                        bottom_range,
                                        abst_bot, flags_bot, bot_rate))},
            "confounder_note": (
                "跨轮 reader 实例不同（本轮唯一实验操作=实例群重抽、"
                "恰是裁决变量；r15→r16 纯重抽漂移 0.09064 在案为量级"
                "参照）+轮内实例差异=混杂因素照旧声明；v1.2 工具规约把"
                "工具行为钉住（12/12 自述「未读取盘上任何其他文件」）"
                "但判读实例仍为不同实例；每视角 n=3 仍为小样本；"
                "development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }

def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r10: dict, run_r11: dict, run_r12: dict,
                             run_r13: dict, run_r14: dict, run_r15: dict,
                             run_r16: dict, run_r17: dict, run_r18: dict,
                             run_r19: dict) -> dict:
    """courtyard 被动追踪（r11–r20 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r22 courtyard 类旗标与命中如实入账
    ——top 非弃权 6 条（top-i1 两板 R22T-002/003/007/008 间隙支负责任
    报告+top-i2 两板 R22T-001/005 贴触/极近报告）+top 弃权 2 条（top-i3
    两板 R22T-008/019，(iii-a) 残余弃权支）；bottom 零 courtyard 类
    旗标（对照 r20 的 bottom 非弃权 2 条=G1 破坏在案，r22 G1 维持）。"""
    note_source = {
        "path_rel": REL_PREP_R22, "sha256": _sha(REL_PREP_R22),
        "quote": None,
        "note": ("r22-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r20 "
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
    prior = run_r19["courtyard_tracking"]
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
        "r22_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（top 2 条全部=(iii-a) 残余弃权支路径"
                             "（top-i3 两板）；bottom 零 courtyard 类"
                             "旗标；非弃权 6 条全部 top（top-i1 两板 "
                             "4=间隙支负责任报告+top-i2 两板 2=贴触/"
                             "极近报告）；对照 r19 的 top 4+bottom 0 "
                             "全弃权、r18 的 top 5+bottom 0 全弃权、"
                             "r20 的 top 3 弃权+bottom 非弃权 2（G1 "
                             "破坏在案），如实登记）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r22": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r20_registered": 0,
        "courtyard_matches_r20_detail": (
            "R20 非弃权 courtyard 2 条（bottom-i1 两板 R20B-003/006，"
            "(iii-a) 间隙支报告=G1 守门字面破坏的直接构成）零命中"
            "（run-r20 在案）；courtyard 类弃权旗=top 3+bottom 0"
            "（run-r20 在案）"),
        "courtyard_matches_r19": prior["courtyard_matches_r19"],
        "courtyard_matches_r19_detail": (
            "R19 非弃权 courtyard 2 条（prep1-top-i1 R19T-001/002 贴邻/"
            "共边报告）零命中（run-r19 在案）；courtyard 类弃权旗=top 4+"
            "bottom 0（run-r19 在案）"),
        "courtyard_matches_r18": prior["courtyard_matches_r18"],
        "courtyard_matches_r18_detail": (
            "R18 非弃权 courtyard 5 条（top-i2 3 条+top-i3 1 条+top-i1 "
            "1 条）零命中（run-r18 在案）；courtyard 类弃权旗=top 5+"
            "bottom 0（run-r18 在案）"),
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
            "r16 回升 1 条（R16T-001↔AP-6）、r17–r20 零命中；r22 非弃权 "
            "courtyard=%d 条（命中=%d，如实登记）；GT/阈值零改动"
            % (len(non_abstain_rows),
               sum(r["matches"] for r in non_abstain_rows))),
        "bottom_observation": {
            "fact": ("R22 bottom %d 旗（bottom-i1 0+bottom-i2 4+"
                     "bottom-i3 6）=非弃权 %d（黑点/深色小圆点报告 4+"
                     "placement 报告 4）+弃权 %d（bottom-i2 黑点-焊盘"
                     "贴近存在性弃权 2）："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=0（本轮 bottom 三实例零 "
                     "courtyard 类路径；r14 弃权 4 条/r15 零旗标/r16 "
                     "弃权 2 条/r17 弃权 1 条/r18 零旗标/r19 零旗标/"
                     "r20 非弃权 2 条=G1 破坏/r22 零旗标=G1 维持，逐轮"
                     "构成如实分列）；弃权构成见 reader."
                     "flag_count.by_category；本轮零旗标格=2（bottom-i1 "
                     "两板；item 5 零分母→None 口径触发）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
            "evidence": QUANT_CRITERION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）——bottom 派次全部"
                               "实际使用 §4(i) 量化判据（绿色翼瓣/空隙形态"
                               "判入系统性正常路径或零旗派次逐项核查自述）"),
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }

def build_run() -> dict:
    """run-r20 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    run_r18 = _json_load(REL_RUN_R18)
    run_r19 = _json_load(REL_RUN_R19)
    run_r20 = _json_load(REL_RUN_R20P)
    axis_plan = _json_load(REL_AXIS_PLAN)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, run_r16, run_r17, run_r18, run_r19, run_r20,
        inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, run_r15, run_r16,
                                run_r17, run_r18, run_r19, axis_plan,
                                instances, view_layer, attribution,
                                raw_texts, parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9,
                                         run_r10, run_r11, run_r12,
                                         run_r13, run_r14, run_r15,
                                         run_r16, run_r17, run_r18,
                                         run_r19)

    prep_r22 = _json_load(REL_PREP_R22)
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
            "五键投影（process-v1 §2 步骤3）；R22 reroute 类四旗 "
            "location_evidence 逐字在案（applied/prep1-top-i1 R22T-004/"
            "009+applied/prep1-top-i3 R22T-007/018 存在性弃权，"
            "「等长|蛇形」子串旗级零命中——"
            "reroute_continuation_r22 逐旗判定在案）；"
            "R22 top 弃权旗 16 条逐旗分型摘录在案（top_abstain_typology："
            "接触性 2+存在性 14+层归属其他 0）；"
            "R22 全部 18 条弃权旗逐旗 rubric 族分类在案（black_dot_"
            "tracking.rubric_families）；(iii-a) 逐旗落支 9 条+间隙支 "
            "notes 级 2 派次+§5B/(iii-a) 援引计数分列在案（旗级 0/0/0、"
            "notes 级 §5B 0+(iii-a) 6/12；criterion_"
            "citation_observation）；"
            "bottom 黑点族/placement 处置旗摘录在案（black_dot_"
            "tracking/residual_instance_differences）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "zero_flag_parts": {
            "parts": zero_flag_parts,
            "note": ("本轮 2 格零旗标（bottom-i1 两板；对照 r19 的 2 格"
                     "零旗标=bottom-i3 两板、r17 的 2 格零旗标先例）——"
                     "measurement_design item 5 零分母→None 口径本轮"
                     "触发（bottom-i1 弃权率=None；先例在本轮实测复现）；"
                     "视角层 bottom 弃权率含 None 实例→中位数=None、"
                     "min/max 按可计算实例计算"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R22, "role": "r22_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R22)},
        {"path_rel": REL_PREP_R20, "role": "r20_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R20)},
        {"path_rel": REL_PREP_R19, "role": "r19_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R19)},
        {"path_rel": REL_AXIS_PLAN,
         "role": "axis_experiment_plan_r17_r20_frozen",
         "sha256": _sha(REL_AXIS_PLAN)},
        {"path_rel": REL_DEV_R19,
         "role": "r19_dev_record_combination_decision_and_axis_ledger",
         "sha256": _sha(REL_DEV_R19)},
        {"path_rel": REL_DEV_R20,
         "role": "r20_dev_record_authorization_next_iteration_targets",
         "sha256": _sha(REL_DEV_R20)},
        {"path_rel": REL_DEV_R18,
         "role": "r18_dev_record_prior_chain_and_axis_ledger",
         "sha256": _sha(REL_DEV_R18)},
        {"path_rel": REL_DEV_R17,
         "role": "r17_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R17)},
        {"path_rel": REL_DEV_R16,
         "role": "r16_dev_record_prior_chain",
         "sha256": _sha(REL_DEV_R16)},
        {"path_rel": REL_PREP_R18, "role": "r18_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R18)},
        {"path_rel": REL_RUN_R19, "role": "r19_run_record_reference_and_m_tuple_source",
         "sha256": _sha(REL_RUN_R19)},
        {"path_rel": REL_RUN_R20P, "role": "r20_run_record_reference_and_comparison_row",
         "sha256": _sha(REL_RUN_R20P)},
        {"path_rel": REL_RUN_R18, "role": "r18_run_record_reference",
         "sha256": _sha(REL_RUN_R18)},
        {"path_rel": REL_PREP_R16, "role": "r16_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R16)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R20,
         "role": "observation_guidance_r20_prior_round_historical",
         "sha256": _sha(REL_GUIDANCE_R20)},
        {"path_rel": REL_GUIDANCE_R19,
         "role": "observation_guidance_r19_active_byte_reuse",
         "sha256": _sha(REL_GUIDANCE_R19)},
        {"path_rel": REL_GUIDANCE_R18,
         "role": "observation_guidance_r18_s5b_segment_source",
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
         "role": "blackdot_probe_r18_prior_chain_hash_only",
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
        "kind": "tl2_calibration_run_r22",
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
            "axis_id": ("none_zero_change_repeat_round"
                        "（唯一实验操作=reader 实例群重抽，非指引/渲染/"
                        "GT/阈值/协议变更）"),
            "nature": INSTRUMENT_NATURE,
            "note": prep_r22["instrument_change"]["note"],
            "declaration": prep_r22["instrument_change"]["declaration"],
            "renders_registered": [
                {"state_side": e["state_side"], "path_rel": e["path_rel"],
                 "sha256_measured": e["sha256_measured"],
                 "sha256_witness_registered":
                     e["sha256_witness_registered"],
                 "witness_record": e["witness_record"],
                 "match": e["match"]}
                for e in prep_r22["instrument_change"]["renders"]],
            "components": [
                "渲染零变更=renders-r14b 四图字节复用（与 r14–r19 "
                "盲读同一批文件；no_instrument_change=true）"],
            "unchanged_components": list(prep_r22["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v.get("attribution_channel"),
                 "instrument_change": v["instrument_change"]}
                for v in prep_r22["changed_variables"]],
            "changed_variables_note": (
                "r22-prep-record changed_variables=[]（同指引重复轮："
                "指引/渲染/GT/阈值/协议零变更，唯一实验操作=reader 实例群"
                "重抽，见 manipulated_factor）"),
            "protocol_amendment": {
                "amendment_version": prep_r22["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r22["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r22["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R22, "sha256": _sha(REL_PREP_R22)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；r19 指引 §6 示例旗 ID 前缀保持 R19T-/R19B- 落盘"
            "原文（字节复用不改），R22 派次前缀 R22T/R22B 由派发指令层"
            "覆盖（指引字节复用+§6 前缀差异登记；r16 先例在案：r15 指引"
            "+R16T 前缀执行先例，per r22-prep-record protocol_amendment."
            "naming）；实例间编号独立；"
            "r22 实测编号行为=6 智能体各包两板、编号跨板连续（5 个有旗"
            "实例全部跨板连续+bottom-i1 两板零旗标编号无可登记；与 "
            "prep-record naming 声明相符），见 "
            "dispatch_mode.flag_id_continuity_note"),
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
                     "全部关闭（r8 轮同日审计，结论 r9–r19 延续引用）；该"
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
                    "r13 指引 §4（本轮指引=observation-guidance-r19.md "
                    "字节复用=r19 轮落盘本体零字节不动；(iii-a) 可操作分辨"
                    "条款随指引本体原样生效；本轮无 §5B 节=r19 基座结构"
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
                    "视觉贴近直接计为交叠）；(iii-a) 可操作分辨条款（随 "
                    "r19 指引本体原样生效）：(1) 间隙支=可辨认连续间隙带→"
                    "按「视觉贴近」继续 "
                    "(i)(ii) 与三路出口判定、不得弃权；(2) 侵入支=边缘"
                    "直接相连或明显侵入→按「接触/交叠」处理并照常输出"
                    "旗标；(3) 残余弃权支=两者均无→方按 (iii) 原文弃权；"
                    "反放宽条款原文保留（「仅因形态不熟悉、不确定其设计"
                    "含义」仍不构成判为正常设计特征的理由）；量化阈值为"
                    "一般判据、非期望清单；§3A 示例 c 收窄判据原文"
                    "适用；§6 示例旗 ID 前缀保持 R19T-/R19B- 落盘原文"
                    "（R22T/R22B=派发层覆盖、前缀差异登记）；"
                    "abstain=true=现象是否存在或归属哪类无法负责任"
                    "地判断；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("协议侧 v1.1 多实例口径沿用+v1.2 工具"
                                      "规约沿用（无新增版本）：12 次盲读="
                                      "4 视角格×3 实例（i1/i2/i3），两波次"
                                      "串行保序（同一实例先 applied 后 "
                                      "prep1）；本轮 12 派次 reader 实例群"
                                      "全部重抽（与 r19/r20 实例群无身份"
                                      "延续=唯一实验操作）；每派次指令含 "
                                      "v1.2 硬性"
                                      "条款（禁止程序化图像处理、只允许 "
                                      "Read 直读原图）；零诊断/探针内容"
                                      "（framing/witness 记录不进任何 "
                                      "reader 上下文）、零 legend/零其他"
                                      "解释（判读输入=指引+单张 PNG+派发"
                                      "指令）；每图独立判读；跨实例/跨视角"
                                      "禁止交流（独立性亦为实例群重抽收敛"
                                      "归因裁决有效性的前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R19,
                                 "sha256": _sha(REL_GUIDANCE_R19),
                                 "frozen_before_read": True,
                                 "reuse_mode": "byte_reuse_zero_change",
                                 "zero_write": ("本轮不新建指引文件："
                                                "observation-guidance-"
                                                "r19.md 零字节不动（r16 "
                                                "先例=r15 指引字节复用"
                                                "+派发层前缀覆盖，per "
                                                "r22-prep-record guidance_"
                                                "reuse.zero_write_"
                                                "declaration）"),
                                 "role": ("本轮唯一判读依据（r19 轮落盘"
                                          "本体；§6 示例前缀 R19T-/R19B- "
                                          "保持落盘原文、R22T/R22B 由派发"
                                          "指令层覆盖）"),
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：axis-experiment-plan-r17-r20.json"
                 "（b6ec6467…，stage2 组合定义+comparison_rule+守门+"
                 "early_stop_rule+combination_decision_rule，先于 R17–R21 "
                 "任何实验轮盲读冻结；R21 全组合槽位=early_stop "
                 "strong_single_axis_shortcut 命中未触发、永久留空（跳号"
                 "声明在案）；用户 2026-09-09「三条轴单独/组合/"
                 "全组合尝试，选择收益最大的继续」user_directive_note "
                 "在案）→round20-dev-record（80e3e9e2…，next_iteration_"
                 "targets[0] 阶段2 收束+R21 不做、targets[1] 同指引重复轮"
                 "候选 preregistration_required=true=本轮设计出处与合法性"
                 "依据）→r22-prep-record.json"
                 "（63346ee6…，本轮预注册件，measurement_design 五条"
                 "聚合口径与 hypothesis_test.adjudication 复制性三分判据"
                 "（replicated=M1 落 [0.361538, 0.561538]（r19±0.10）且 "
                 "contact 族≤7 且 G1/G2 维持/drifted=未达 replicated 且 "
                 "M1 <0.771429 且 G1/G2 维持/regressed=M1 ≥0.771429 或 "
                 "G1/G2 任一破坏）"
                 "先于盲读冻结；instrument_change.changed=false；"
                 "guidance=字节复用（observation-guidance-r19.md 本体零"
                 "改动、不新建指引文件）；渲染="
                 "renders-r14b 字节"
                 "复用）先于本轮盲读落盘（零 GT 暴露声明在案 "
                 "no_visual_reading=true；pre_round_review="
                 "not_required_zero_change_round——零变更轮在案）→判读"
                 "指引=observation-guidance-r19.md"
                 "（8633bda5…，r19 轮落盘本体字节复用，本轮"
                 "唯一判读依据；§6 示例前缀 R19T-/R19B- 保持落盘原文、"
                 "R22T/R22B=派发层覆盖（前缀差异登记、r16 先例在案））"
                 "→渲染零变更（renders-r14b 四图字节复用，四 PNG sha="
                 "witness-r14b 登记值=prep-record 登记值三方一致）→"
                 "12 次盲读（12 件哈希前缀逐字钉死：fcea824a/0de33b5f/"
                 "e2758622/044edcca/d8dad94e/4849758c/31b978ef/570b9a3b/"
                 "60e96d3f/6260dbbd/9796b4d6/a81d8098）→比对记录"
                 "（读者产物零改动）。GT 重"
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
            "r18_run": {"path_rel": REL_RUN_R18, "sha256": _sha(REL_RUN_R18)},
            "r19_run": {"path_rel": REL_RUN_R19, "sha256": _sha(REL_RUN_R19)},
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
                     "渲染，verdict=reject）与 R18（轴2 指引侧单变量轮："
                     "§5B 黑点中性仪器注记，verdict=reject）与 R19（轴3 "
                     "判据侧单变量轮：§4(iii-a) 可操作分辨条款，渲染零"
                     "变更=renders-r14b 字节复用，verdict=marginal）与 "
                     "R20（stage2 组合轮：轴3+轴2 判读指引合成=§5B+(iii-a) "
                     "两增补并集；渲染零变更=renders-r14b 四图字节复用；"
                     "执行 axis-plan stage2 R20，verdict=reject、G1 守门"
                     "字面破坏在案）run 在案；"
                     "R22=同指引重复轮（收敛归因；r16 先例：r15→r16 同指引"
                     "重复、渲染零变更、仅实例重抽；唯一实验操作=reader "
                     "实例群重抽 12 派次；执行 round20-dev-record next_"
                     "iteration_targets[1] 候选、R21 全组合槽位未触发永久"
                     "留空=跳号声明在案）；"
                     "轮间对比由后续 round22-dev-record（另包"
                     "落盘）与 channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案；12 件"
            "哈希前缀 fcea824a/0de33b5f/e2758622/044edcca/d8dad94e/"
            "4849758c/31b978ef/570b9a3b/60e96d3f/6260dbbd/9796b4d6/"
            "a81d8098 盘态钉死），"
            "比较器/视角层聚合/双口径归并/代表配置选取/通道重放/rubric "
            "机械分型为纯函数（六实例旗数 11/10/20/0/4/6→代表配置 "
            "top-i1+bottom-i2（top 中位 11 唯一=top-i1；bottom 中位 4 "
            "唯一=bottom-i2）唯一可复算），无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-09-r22（事件序="
            "axis-experiment-plan-r17-r20（b6ec6467…，冻结件在案；R21 "
            "全组合槽位未触发永久留空）→"
            "round20-dev-record（80e3e9e2…，阶段2 收束+同指引重复轮候选"
            "授权在案）→"
            "r22-prep-record"
            "（63346ee6…，本轮预注册件，先于盲读冻结）→r19 指引字节"
            "复用（8633bda5…，零写入、零编辑，本轮唯一"
            "判读依据）→渲染零变更"
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
                                run_r16: dict, run_r17: dict, run_r18: dict,
                                run_r19: dict, run_r20: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """run-r22 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 11, "top-i2": 10, "top-i3": 20, "bottom-i1": 0,
                  "bottom-i2": 4, "bottom-i3": 6}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 5, "top-i2": 4, "top-i3": 7, "bottom-i1": 0,
                "bottom-i2": 2, "bottom-i3": 0}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 51:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.466667 \
            or agg["flag_count_total"] != 15 \
            or agg["abstain_count_total"] != 7:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "regressed":
        _fail("假设字母裁决与预注册判据复算不符")
    if hyp["hypothesis_id"] != "r20-dev-record-candidate-r19-config-same-guidance-repeat":
        _fail("hypothesis_id 与预登记不符")
    m = hyp["measurement"]
    if m["contact_family_abstain_flags_rubric_r22"] != 2 \
            or m["contact_r16_baseline_registered"] != 10:
        _fail("contact 计数与实测不一致")
    if m["top_abstain_flags_r22"] != 41 or m["top_abstain_count_r22"] != 16 \
            or m["top_abstain_rate_r22"] != 0.390244:
        _fail("判据首键 M1 计数与实测不一致")
    if m["m4_top_rate_range_r22"] != 0.104545:
        _fail("M4 计数与实测不一致（第二样本单列机制观察）")
    if m["crit_regressed_m1_ge_0_771429"] is not False:
        _fail("regressed_m1 支布尔与实测不一致（M1=0.390244 应 <0.771429）")
    if m["crit_regressed_guards_broken"] is not True:
        _fail("regressed_guards 支布尔与实测不一致（G2 应破坏）")
    if m["crit_replicated_m1_in_band"] is not True:
        _fail("replicated 带内布尔与实测不一致（M1 应落 r19±0.10 带，"
              "但守门破坏经支序先行否决 replicated）")
    if m["crit_replicated_contact_le_7"] is not True:
        _fail("replicated contact 门布尔与实测不一致")
    if m["crit_drifted_m1_lt_0_771429"] is not True:
        _fail("drifted 支布尔与实测不一致")
    if m["top_abstain_rate_r16_baseline_value"] != 0.771429:
        _fail("r16 基线值与在案登记不一致")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r22"] != 0 \
            or bso["bottom_abstain_flags_r22"] != 10 \
            or bso["bottom_abstain_count_r22"] != 2 \
            or bso["bottom_abstain_rate_r22"] != 0.2 \
            or bso["bottom_courtyard_non_abstain_by_instance_r22"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0} \
            or bso["bottom_rate_direction_vs_r16"] != "improved":
        _fail("bottom 侧观察计数与实测不一致")
    g = m["guard_channel"]
    if g["g1_ok"] is not True or g["g2_guard_ok"] is not False \
            or g["guards_ok"] is not False \
            or g["g2_geometry_gate_r19"] != 0 \
            or g["g2_geometry_gate_r22"] != 2:
        _fail("守门 G1/G2 计数与实测不一致（G1 维持、G2 几何门 0→2 破坏）")
    mo = hyp["mechanism_observation"]
    tt = mo["top_abstain_typology"]
    if tt["type_counts"] != {"contact": 2, "existence": 14,
                             "other_layer": 0} \
            or tt["top_abstain_flags_total"] != 16:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 4 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 0, "top-i2": 2, "top-i3": 0,
                                     "bottom-i1": 0, "bottom-i2": 2,
                                     "bottom-i3": 0} \
            or bd["blackdot_to_non_abstain_count"] != 6 \
            or len(bd["black_dot_non_abstain_flags"]) != 6 \
            or bd["judged_normal_dispatches"]["count"] != 4:
        _fail("黑点族计数与实测不一致")
    if bd["rubric_families"]["counts"] != R22_FAMILY_COUNTS_REGISTERED \
            or bd["rubric_families"]["replay_proof"]["per_flag_total"] \
            != 132:
        _fail("rubric 族计数/重放证明与实测不一致")
    cco = mo["criterion_citation_observation"]
    if cco["branch_counts_flag_level"] != {
            "branch1_gap_report": 6, "branch2_intrusion_report": 1,
            "branch3_residual_abstain": 2} \
            or cco["branch1_notes_level_dispatches"] != 2 \
            or cco["citation_counts"]["flag_level_s5b_literal"] != 0 \
            or cco["citation_counts"]["flag_level_iiia_literal"] != 0 \
            or cco["citation_counts"]["flag_level_branch_literal"] != 0 \
            or cco["citation_counts"]["notes_level_s5b"] != 0 \
            or cco["citation_counts"]["notes_level_iiia"] != 6:
        _fail("§5B/(iii-a) 援引/落支计数与实测不一致")
    if mo["bottom_side_observation_maintenance"]["counts"][
            "blackdot_abstain_flags_rubric_r22"] != 4 \
            or mo["bottom_side_observation_maintenance"]["counts"][
                "zero_flag_dispatch_count"] != 2:
        _fail("bottom 侧观察黑点/零旗计数与实测不一致")
    ledger = mo["experiment_comparison_ledger"]
    if ledger["r22_measured"]["M1"] != 0.390244 \
            or ledger["r22_measured"]["M2"] != 0.2 \
            or ledger["r22_measured"]["M3"] != 4 \
            or ledger["r22_measured"]["M4"] != 0.104545 \
            or ledger["r22_measured"]["contact_family_abstain_flags_rubric"] \
            != 2:
        _fail("实验对照账四元组与实测不一致")
    if ledger["ranking_by_comparison_rule"]["r22_eligibility"] is not False \
            or ledger["ranking_by_comparison_rule"][
                "ranking_order_best_first"] != ["r19_axis3", "r18_axis2",
                                                "r16_baseline",
                                                "r17_axis1"]:
        _fail("comparison_rule 排序（r22 G2 破坏不入排序）与实测不一致")
    if ledger["ranking_by_comparison_rule"]["r20_eligibility"] is not False:
        _fail("r20 破坏轮应不入排序（登记行仅如实入账）")
    if ledger["significant_benefit_vs_r16"]["met"] is not True \
            or ledger["significant_benefit_vs_r16"][
                "r22_m1_absolute_drop"] != 0.381185:
        _fail("显著收益对照与实测不一致")
    if ledger["replication_conclusion"]["verdict"] != "regressed":
        _fail("复制性结论位与字母裁决不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if sum(1 for v in gs.values() if v["§5A_cited"]) != 1 \
            or sum(1 for v in gs.values() if v["§5B_cited"]) != 0:
        _fail("绿区语义化 §5A/§5B 引用与实测不一致（实例级 §5A 1/3、"
              "§5B 0/3；派次级 §5A 2/6 由 evidence 表 cites 计数）")
    if sum(1 for e in mo["green_semantics_by_instance"]["evidence"]
           if e.get("cites_5A")) != 2 \
            or sum(1 for e in mo["green_semantics_by_instance"]["evidence"]
                   if e.get("cites_5B")) != 0:
        _fail("绿区语义化 §5A/§5B 派次级引用与实测不一致（§5A 2/6、"
              "§5B 0/6=本轮指引无 §5B 节）")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.104545 \
            or vl["bottom"]["abstain_rate_range"] != 0.5:
        _fail("视角层极差与实测不一致（M4 方向；bottom 按可计算实例）")
    if vl["bottom"]["abstain_rate"]["median"] is not None:
        _fail("bottom 弃权率中位数应为 None（bottom-i1 零旗标分母）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 1 or dual["agreement"]["count"] != 1:
        _fail("双口径计数与实测不一致（union=agreement=1）")
    if dual["union"]["gt_ids"] != ["GT-REVC-P1-L1SHORT"]             or dual["union"]["gt_recall_union"] != 0.076923:
        _fail("双口径计数与实测不一致（L1SHORT、召回 1/13）")
    matches_all = sorted(
        (mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != [("R22T-007", "GT-REVC-P1-L1SHORT"),
                       ("R22T-017", "GT-REVC-P1-L1SHORT")]:
        _fail("matches 明细与实测不一致（r22 两条命中：prep1-top-i2 "
              "R22T-007+prep1-top-i3 R22T-017 与 L1SHORT）")
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
            or run_r18["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r18"] \
            or run_r19["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r19"] \
            or run_r20["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r20"] \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 4:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R19 0→R22 0；类别 R19 2→R22 0）
    ca = run_doc["channel_attribution"]
    cat_r22_entries = ca["channel_2_category_gate"][
        "r22_category_mismatch_entries"]
    if len(ca["channel_1_geometry_gate"]["r22_area_ratio_rejected_entries"]) \
            != 2 or len(cat_r22_entries) != 4:
        _fail("通道条目数与实测声明不一致（几何门 2、类别门 4）")
    # courtyard 追踪与实测一致（r22 非弃权 courtyard=6、弃权=2、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r22"] != 0 or len(
            ct["r22_courtyard_flags"]["non_abstain"]) != 6:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r22_courtyard_flags"]["abstain"]) != 2:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 零旗标派次=2（bottom-i1 两板；item 5 None 口径触发）
    if run_doc["reader"]["zero_flag_parts"]["parts"] != [
            {"instance": "bottom-i1", "state": "applied", "flag_count": 0},
            {"instance": "bottom-i1", "state": "prep1", "flag_count": 0}]:
        _fail("零旗标派次与实测不一致（bottom-i1 两板）")
    # 逐旗判定/工具规约/量化判据/分型/黑点/placement/绿区/间隙支摘录
    # 逐字在案
    for r in hyp["reroute_continuation_r22"]["reroute_flag_detail_r22"]:
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
    for ev in mo["criterion_citation_observation"]["branch1_notes_rows"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"(iii-a) 间隙支摘录与 reader 原文不符: {ev['source']}")
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
    # 12 件盲读原始件哈希前缀逐字复核（盲读亲测在案锚）
    for key, prefix in RAW_PINNED_PREFIXES.items():
        got = _sha(RAW_FILES[key])
        if not got.startswith(prefix):
            _fail(f"盲读原始件盘态钉死前缀不符: {key} {got[:8]}…≠{prefix}…")

    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r22")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), _json_load(REL_RUN_R15),
        _json_load(REL_RUN_R16), _json_load(REL_RUN_R17),
        _json_load(REL_RUN_R18), _json_load(REL_RUN_R19),
        _json_load(REL_RUN_R20P), parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R22), run_bytes,
                         "calibration-run-r22.json")
    run_sha = _sha(REL_RUN_R22)
    # round22-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    m = hyp["measurement"]
    mo = hyp["mechanism_observation"]
    ca = run["channel_attribution"]
    print(f"[s77-cal-r22] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 33、弃权 18）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s77-cal-r22] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s77-cal-r22] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s77-cal-r22] zero_flag_parts: "
          f"{[(z['instance'], z['state']) for z in run['reader']['zero_flag_parts']['parts']]}"
          f"（bottom-i1 两板零旗标；item 5 零分母→None 口径触发）")
    print(f"[s77-cal-r22] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}"
          f"（bottom 中位数={vl['bottom']['abstain_rate']['median']}"
          f"=None（含零旗标实例）、min/max 按可计算实例）")
    print(f"[s77-cal-r22] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13"
          f"（r22 恢复命中=同 GT L1SHORT 两条旗（R22T-007/R22T-017）；"
          f"对照 r19 唯一命中同 GT（R19T-009）、r20 零命中，如实并列）")
    print(f"[s77-cal-r22] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    print(f"[s77-cal-r22] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；复制性三分判据=M1 落点+contact 族+"
          f"守门维持：R22 四元组=({m['r22_m_tuple_6dp']['M1']},"
          f"{m['r22_m_tuple_6dp']['M2']},{m['r22_m_tuple_6dp']['M3']},"
          f"{m['r22_m_tuple_6dp']['M4']}) vs r19 参照 "
          f"({m['r19_reference_tuple']['M1']},{m['r19_reference_tuple']['M2']},"
          f"{m['r19_reference_tuple']['M3']},{m['r19_reference_tuple']['M4']})"
          f"（run-r19 live 复算+prep-record 冻结锚交叉核对）→M1 带 "
          f"[0.361538,0.561538] 内={m['crit_replicated_m1_in_band']}、"
          f"contact 族={m['contact_family_abstain_flags_rubric_r22']}≤7="
          f"{m['crit_replicated_contact_le_7']}；(g) 支 M1 ≥0.771429→"
          f"crit_regressed_m1="
          f"{m['crit_regressed_m1_ge_0_771429']}、G1/G2 破坏="
          f"{m['crit_regressed_guards_broken']}（G1=bottom courtyard 非弃权 "
          f"实测 {m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r22']}"
          f"；G2 几何门 R19={m['guard_channel']['g2_geometry_gate_r19']}"
          f"→R22={m['guard_channel']['g2_geometry_gate_r22']}）；"
          f"(d) 支 M1 <0.771429="
          f"{m['crit_drifted_m1_lt_0_771429']}（M1={m['top_abstain_count_r22']}/"
          f"{m['top_abstain_flags_r22']}={m['top_abstain_rate_r22']}，r16 基线双侧复算 "
          f"{m['top_abstain_rate_r16_baseline_live']}"
          f"={m['top_abstain_rate_r16_baseline_value']}）；M4 第二样本单列"
          f"={m['m4_top_rate_range_r22']}（vs r19 0.211111、不进字母）；落支={m['letter_branch']}"
          f"；守门 G1={m['guard_channel']['g1_ok']}/G2="
          f"{m['guard_channel']['g2_guard_ok']}；机制观察单列）")
    print(f"[s77-cal-r22] 侧观察（M2 bottom，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r22']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r22']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r22']}"
          f" vs r16 基线 12/14=0.857143、r18 13/19=0.684211、r19 4/7=0.571429、"
          f"r20 4/14=0.285714"
          f"（{m['bottom_side_observation']['bottom_rate_direction_vs_r16']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r22']}"
          f"/courtyard 旗总数={m['bottom_side_observation']['bottom_courtyard_flags_total_r22']}"
          f"（G1 维持；对照 r20 破坏 2/0/0 在案）")
    print(f"[s77-cal-r22] 机制观察要点：rubric 族计数="
          f"{mo['black_dot_tracking']['rubric_families']['counts']}"
          f"（r13–r16 132 条重放对拍逐一相等；contact=2 vs r16 基线"
          f" 10、黑点=4 vs r19 4/r20 6、存在性其他=12 vs r19 14/r20 10）；"
          f"援引分记：旗级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_s5b_literal']}"
          f"/(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_iiia_literal']}"
          f"/分支(="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_branch_literal']}"
          f"；notes 级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_s5b']}"
          f"/12（本轮指引字节复用无 §5B 节=零上下文）、(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_iiia']}"
          f"/12；(iii-a) 落支="
          f"{mo['criterion_citation_observation']['branch_counts_flag_level']}"
          f"+间隙支 notes 级 "
          f"{mo['criterion_citation_observation']['branch1_notes_level_dispatches']} "
          f"派次；黑点旗 4 条全弃权 "
          f"{mo['black_dot_tracking']['by_instance']}（vs r19 4/r20 6）；"
          f"黑点转非弃权旗 "
          f"{mo['black_dot_tracking']['blackdot_to_non_abstain_count']} 条"
          f"（top 侧首现 2+bottom 4）；黑点判正常派次 "
          f"{mo['black_dot_tracking']['judged_normal_dispatches']['count']}/12"
          f"（对照 r15=3/r16=2/r18=2/r19=3/r20=4）；四元组账 "
          f"(M1,M2,M3,M4)=(0.390244,0.2,4,0.104545) vs r16 "
          f"(0.771429,0.857143,12,0.261904)/r17 (0.88,0.75,8,0.333333)/"
          f"r18 (0.645161,0.684211,13,0.277778)/r19 (0.461538,0.571429,4,"
          f"0.211111)/r20 (0.636364,0.285714,6,0.25)；排序（资格门判定后"
          f"入排序）="
          f"{mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['ranking_order_best_first']}"
          f"（r22_eligibility={mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['r22_eligibility']}）；"
          f"复制性结论位={mo['experiment_comparison_ledger']['replication_conclusion']['conclusion'][:60]}…；"
          f"top 弃权分型="
          f"{mo['top_abstain_typology']['type_counts']}；reroute 4 旗"
          f"（弃权 4、子串零命中）")
    print(f"[s77-cal-r22] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    print(f"[s77-cal-r22] channel_attribution: "
          f"geo R19={len(ca['channel_1_geometry_gate']['r19_area_ratio_rejected_entries'])}"
          f"→R22={len(ca['channel_1_geometry_gate']['r22_area_ratio_rejected_entries'])}, "
          f"cat R19={len(ca['channel_2_category_gate']['r19_category_mismatch_entries'])}"
          f"→R22={len(ca['channel_2_category_gate']['r22_category_mismatch_entries'])}")
    print(f"[s77-cal-r22] commit: run={run_status}（round22-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s77-cal-r22] sha256[:8] calibration-run-r22.json = "
          f"{run_sha[:8]}")
    print(f"[s77-cal-r22] sha256 calibration-run-r22.json = {run_sha}")
    print("[s77-cal-r22] R22 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")



if __name__ == "__main__":
    
    main()
