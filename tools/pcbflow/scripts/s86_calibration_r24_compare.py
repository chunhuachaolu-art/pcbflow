#!/usr/bin/env python
"""CAL-R24-CLOSE：reader 判读迭代第二十四轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s71/s74/s77/s82 同构，仅输入与轮次常量不同；
R24=development 域实例群扩容归因轮（多实例协议 v1.3：每视图实例数
3→6，唯一实验变量=实例数 n）：渲染零变更=renders-r14b 四图字节复用
（与 r14–r23 盲读同一批文件、四 PNG sha=witness-r14b 登记值 fail-closed
比对一致）；判读指引=observation-guidance-r23.md 字节复用（866b0157、
零改写零派生；派发层前缀覆盖 R23T/R23B→R24T/R24B、round_id→
2026-09-10-r24、reader_id→reader-r24-*——r16/r22 字节复用+派发层前缀
覆盖先例；指引文件内 §6 示例前缀 R23T-/R23B- 为落盘原文、由派发指令
覆盖）；GT/阈值/协议正文零变更（13 条冻结、v1/v1.1/v1.2 继承不改+
v1.3 n 扩容附录[登记于 r24-prep-record]；evaluation-protocol-v2=holdout
冻结件本轮不启用）；检验 r24-prep-record.json（760af49f）预注册假设
（hypothesis_id=r23-confounded-residual-confound-instance-axis-
attribution，判据=r24-prep-record.json hypothesis_test.adjudication
归因三支判据预注册原文，脚本从 prep-record 文件加载判据文本、基线
数字 live 重放不手工抄数）：

  T1  解析 24 个 reader-raw-r24-*.txt（4 视角格×6 实例=12 个 reader
      智能体各包同侧两板；fail-closed：非法 JSON 即停止；逐旗标过
      calibration fail-closed 校验，被拒者如实入拒收清单，reader 产物
      零改动）；视角注入=图像名确定性映射（*-top.png→top、
      *-bottom.png→bottom）。24 件哈希全 64 位写死断言（盘态钉死）。
  T2  按 r24-prep-record.json measurement_design 五条预注册聚合口径
      执行（n=6 扩写；与 calibration-run-r16–r23 同一比较脚本血统）：
      (1) 实例主记录=12 个实例（top 6+bottom 6）各自两板合计
          flag_count/abstain_count/abstain_rate（6 位小数；零旗标分母
          =None）/非弃权清单/逐旗 containment+area_ratio 匹配明细
          （r24 实测编号行为=12/12 实例同实例跨板连续、24 格全部≥1 旗
          =零零旗格；清单按 (state, flag_id) 限定、跨板同号不混淆——
          本轮实测同名旗号跨实例出现[如 R24T-015 同时见于 top-i2 与
          top-i6]=实例间编号独立语义的直接观测、按实例限定不混淆）；
      (2) 视角层=每视角 6 实例 flag_count/abstain_rate/matches 各
          中位数（n=6=第 3/4 序位均值）+min+max 三分列不取整；
      (3) GT 匹配双口径=union（≥1/6 实例命中）与 agreement（≥4/6
          过半数=v1.1「≥2/3 过半数」语义的 n=6 推广、v1.3 附录显式
          冻结）并列+逐 GT 条目 matched_by_count（0..6；召回分母=
          GT 13 条）；
      (4) 联合门（APR-0011 阈值零改动）=代表配置（每视角 flag_count
          升序第 3 序位=下中位实例、并列按实例编号先序——规则预注册）
          算一轮 joint+per-metric 实例间范围+逐实例原始记录三者并列
          不挑优；
      (5) bottom 零旗标分母=按库侧 cal._ratio 先例 None+文字说明
          （本轮零零旗格、该口径未触发、先例条文照登记）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且本轮渲染零变更，
      重投影输入未变、本轮零新派生；bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（归因三支判据，r24-prep-record.json hypothesis_
      test.adjudication 原文）逐支执行（字母裁决唯一正式、轮后不改写、
      脚本实测落支不预写）：
        instance_dominated=G1 维持（六 bottom 实例 courtyard 非弃权
          旗全=0）且 M4(n=6)<0.261904 且 split_half_M1_diff≤0.09064
          →实例群抽样噪声足以解释元组离散；
        not_instance_dominated=G1 维持且（M4(n=6)≥0.261904 或
          split_half_M1_diff>0.09064）→离散超出抽样尺度、下一归因轴
          =判据内容（判据内容/其他输出侧）；
        guard_interrupted=G1 破坏（任一 bottom 实例 courtyard 非弃权
          旗>0）→归因悬置、机制观察照常。
      全部阈值比较=6 位定点整数交叉相乘（避免浮点；M4 自证=
      928571−666667=261904 整数复算断言；split-half 阈值 90640=
      0.09064 的 6 位定点=|0.862069−0.771429|）；G1 破坏→guard_
      interrupted 独占。G2=top 视非弃权旗标 frame_box_pct 几何门面积
      比>10 出局条目数=实测观察项、非本轮字母支（G2>0→资格门剔除不
      入排序；r19=0/r22=2/r23=1 对照在案；本轮实测=0、出局条目零条=
      空摘录如实登记）；守门 G1/G2 独立单列；机制观察单列
      （mechanism_observation_separate 原文口径）：逐实例率分布
      （n=6 首次可看轮内分布形态：top-i1=1.0 vs top-i2/top-i6 双峰
      结构如实记录）、split-half 稳 vs 极差爆拉的分解解读、弃权分型
      （接触/存在性/其他=机械主出口分类、与 rubric 族两套口径分列）、
      contact/黑点/存在性三族计数（分型件 rubric 口径；先回放
      r13–r16=8/15/5/10 链一致才可应用；r19=4/r22=4/r23=8 对照）+
      M2 对照在案五行+(iii-a)/§5B/§6 援引计数照记+reroute 被动追踪；
      M3=黑点族弃权旗数（分型件 rubric 词元口径）；M1/M2/M3/M4+
      split_half_M1_diff 入实验对照账（比较集=r16 基线+r19/r22/r23
      实测元组四行、全部 live 复算+冻结锚交叉核对；八行并列=r16 基线/
      r17 轴1/r18 轴2/r19 轴3/r20（破坏轮登记行）/r22（登记行）/
      r23（登记行）/r24 本轮）；axis-plan comparison_rule（(M1 升序,
      M2 升序,M3 升序,M4 升序) 字典序、资格门=G1/G2 均满足）下的
      当前排序如实登记（资格门破坏轮不入排序；r20/r22/r23=排除行、
      r24 资格按 G1/G2 实测判定）；显著收益定义（M1 绝对降幅 ≥0.10）
      逐轮对照；M4 跨口径比较=描述性声明（12 格 vs r16–r23 逐实例
      两板合计口径的粒度差异=prep-record M4_operationalization_note
      延续登记）；top 弃权分型照常（机械主出口分类）；bottom courtyard
      非弃权与 courtyard 旗计数。
      → calibration-run-r24.json。
  T3  development 域记录（R23→R24 归因方向性对照/假设裁决/联合评价
      趋势/下一迭代目标）由后续 dev-record 包落盘（round24-dev-record，
      另包执行）；本包仅产出 run-r24、零 dev-record 写入。

通道归因纪律（vs R19/R20/R22/R23；方法照抄 s34–s82 deviation_note
口径）：本轮对 R15/R16/R17/R18/R19/R20/R22/R23 均以内嵌输入
（reader_flags/gt_entries/flag_views，run sha 在案）+compare_v3 同源
几何原语（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R24 二十四派次全部以 Read 工具
直读、24/24 派次 reading_notes 自述「未读取盘上任何其他文件」（逐派
次句子程序提取在案 reader_tool_evidence）；11 派次另自述未做跨图/
交叉推断（排序清单在案）；§4(iii-a) 措辞 notes 级援引 8/24 派次、
§5B 措辞 notes 级援引 0/24 派次（本轮指引=observation-guidance-r23.md
字节复用、仍无 §5B 节=任何援引为零上下文）、§6 报告框收敛条款措辞
notes 级援引 20/24 派次（三计数分开记；旗级 (iii-a) 字面援引 7 旗、
逐旗摘录在案）。证据摘录方法披露（与 r23 手工转录登记路径不同，如实
声明）：本轮逐旗/逐派次摘录=编排侧从冻结 reader-raw（24 件哈希全
64 位锚在案）程序化确定性提取（句子级切分、零改写），提取后逐字段与
机械实测（旗号/abstain/类别）核对 fail-closed——摘录非独立证据源、
其真值由冻结原文哈希锚承载。跨轮实例全重抽+扩容=本轮实验操作本身
（per r24-prep-record changed_variables[0] 原文）；输出格式实例披露：
24 件=缩进格式冻结原始判读件、本轮零改动直读（direct JSON 解析、
24 件 parse 校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round24-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量
2026-09-10 / 2026-09-10-r24）；canonical JSON（hashing.canonical_json_
bytes）；hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建
逐字节一致（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；
不 git commit/push。

用法：python scripts/s86_calibration_r24_compare.py   （仓库根执行）
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

DECLARED_DATE = "2026-09-10"
ROUND_ID = "2026-09-10-r24"
ROUND_LABEL = "r24"
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
REL_PREP_R22 = "out/v3-tl2/calibration/r22-prep-record.json"
REL_PREP_R23 = "out/v3-tl2/calibration/r23-prep-record.json"
#: 本轮预注册件（预注册判据唯一事实源；v1.3 n 扩容附录所在件）。
REL_PREP_R24 = "out/v3-tl2/calibration/r24-prep-record.json"
#: r1 件的受保护文件锚期望 v2 追加件（DEV-E0-004；supersedes 链在案）：
#: cli.py 锚 6ed4f3fd→现值 0a738047（铜环案裁定接纳）。仅用于 pfv 期望
#: 覆盖；预注册正文/文件级 sha 引用链仍走 r1 冻结件（零回写）。
REL_PREP_R24_V2 = "out/v3-tl2/calibration/r24-prep-record-v2.json"
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
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_DEV_R22 = "out/v3-tl2/calibration/round22-dev-record.json"
#: r23 轮 dev-record（本轮授权链锚=其 next_candidate_suggestion 选项(b)
#: 的执行轮登记；比较集 r23 行装载源）。
REL_DEV_R23 = "out/v3-tl2/calibration/round23-dev-record.json"
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
#: r20/r22/r23 轮在案 run（对照账 r20/r22/r23 行 live 复算输入；非本轮
#: 输出产物）。
REL_RUN_R20P = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_RUN_R22P = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_RUN_R23P = "out/v3-tl2/calibration/calibration-run-r23.json"
#: holdout 协议冻结件（s79 登记在案；本轮不启用=仅哈希锚在案）。
REL_PROTOCOL_V2 = "out/v3-tl2/calibration/evaluation-protocol-v2.md"
#: 本轮判读指引=observation-guidance-r23.md（866b0157；r24 轮字节复用、
#: 派发层前缀覆盖 R23T/R23B→R24T/R24B——r16/r22 先例同型）。
REL_GUIDANCE_R23 = "out/v3-tl2/calibration/observation-guidance-r23.md"
#: 本包唯一新建输出（防覆写护栏语义照 s68/s71/s74/s77/s82；不在
#: FROZEN_SHA256 锚集）。
REL_RUN_R24 = "out/v3-tl2/calibration/calibration-run-r24.json"

#: 24 份盲读原始件（12 实例×2 板；12 个 reader 智能体各包同侧两板、
#: 跨板连续编号；24 格全部≥1 旗=零零旗格）。
RAW_FILES = {}
for _side in ("applied", "prep1"):
    for _view in ("top", "bottom"):
        for _i in range(1, 7):
            RAW_FILES[f"{_side}-{_view}-i{_i}"] = (
                f"out/v3-tl2/calibration/reader-raw-r24-"
                f"{_side}-{_view}-i{_i}.txt")

#: 十二实例=本轮主记录单位（measurement_design item 1；n=6 扩容）；
#: 每实例=同视角两板（applied+prep1）两派次，实例间编号独立
#: （r24 实测：12/12 实例同实例跨板连续；零零旗格）。
INSTANCES = {}
for _view in ("top", "bottom"):
    for _i in range(1, 7):
        INSTANCES[f"{_view}-i{_i}"] = {
            "view": _view,
            "parts": (f"applied-{_view}-i{_i}", f"prep1-{_view}-i{_i}")}
INSTANCE_ORDER = tuple(
    [f"top-i{i}" for i in range(1, 7)]
    + [f"bottom-i{i}" for i in range(1, 7)])

#: R20 渲染：图像来源=renders-r14b 四图字节复用（渲染零变更；与
#: r14–r23 盲读同一批文件；四 PNG 盘上 sha=witness-r14b 登记值=
#: prep-record instrument_change.renders 登记值，bottom 两板逐字节同
#: d7284259；top 两图=renders-r5 逐字节复用 298bc620/b2f84524）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r14b/applied-top.png",
    "applied-bottom":
        "out/v3-tl2/calibration/renders-r14b/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r14b/prep1-top.png",
    "prep1-bottom":
        "out/v3-tl2/calibration/renders-r14b/prep1-bottom.png",
}
#: 渲染的输入侧冻结矢量 PDF（r24-prep-record no_loosening_note：本轮
#: 渲染零变更=renders-r14b 四图字节复用、PDF 输入未变；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
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
    REL_PREP_R23:
        "3c42ace77ca74730df88778f615450017583c51d738e0883e57125faa7db169e",
    REL_PREP_R24:
        "760af49fe6da58a5b508651142bf51e6c23323ba0da7edc0b79c88410c84e3dd",
    REL_GUIDANCE_R23:
        "866b0157acdf763faf68c18f72b383617a8feaa06a043015b36f5d3cf7f50ca7",
    REL_PROTOCOL_V2:
        "365b67ef247ff2d664c620971fff21efc4ed684e55a2e99625823321669e0712",
    REL_RUN_R22P:
        "80a12c055faa54b0c717b50653af0340265bf048e6aa8fcff63561d497c5d961",
    REL_RUN_R23P:
        "15f583507a68b174618395c8f894ee0c8ea8084b9617ab67647c15c00b71d00b",
    REL_DEV_R22:
        "b4b8fbe95083f970219fdcd74839b73d9d15bb2bce4d19ec8437d96d66b2b66c",
    REL_DEV_R23:
        "343a674753ff660c52e276034f9c78dc5680ca44d052634ae178110ebef12ee9",
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
for _k, _v in RAW_FILES.items():
    FROZEN_SHA256[_v] = {
        "applied-top-i1":
            "84aae6b53f16ad2347a68594926a78e7c02f3c4143caddb84596e069da835ef2",
        "prep1-top-i1":
            "23b921a7f5519e35f64512efb02f749e9e9bd966564f42ffe1d5a0740cd0dcdd",
        "applied-top-i2":
            "671dcfb0132648cce93ba6cae3504540c2fce5282f657410d6515de8952f15b0",
        "prep1-top-i2":
            "ac9e4f2bed3376e2310491cb71773036a14160fe7a9cfbfc8700fe253b58a262",
        "applied-top-i3":
            "cf18682f40749002d604e9e4550957eadef94e54d849317ccfcb8841b123a5d0",
        "prep1-top-i3":
            "547f4ad61872bf99fd39157992389111a6e32cb91341b4d5885503a022f01364",
        "applied-top-i4":
            "d34444bc35eea4364df54f4afab95b0e098b4729e18a50a1eaecf0b7324be1ac",
        "prep1-top-i4":
            "df9feb5b9d602350a3eb06ee785124b22c9c53307e6e798695417ad9f6f260b9",
        "applied-top-i5":
            "e1e75df04a3bbf58dad71a29af46692bcbf440f9e426a8b01043fd7e352be0b6",
        "prep1-top-i5":
            "f45a67943769d2fe91baa4b39fbf0e17aad6e5e9251e4583214f150e8a1101cb",
        "applied-top-i6":
            "7e3f3f0703ca1188fbbba938a23775b53e00b413927bc30fc07d27aa768babd3",
        "prep1-top-i6":
            "416fc4bc6f582f6ea2229f252af808f76f2697b8beb7510d370bba8fc51753e1",
        "applied-bottom-i1":
            "b05c3048e7af3fb57c9405af124e65f611b284a542afa4afd2f16b62350a4c66",
        "prep1-bottom-i1":
            "5ee024843e2828d29932a06646a7b9d7936a348443d2d190a19d7b45c1654ce1",
        "applied-bottom-i2":
            "628cbd33f48bd7a18c3e1bba63350e01e01ac180f0da57b5d232cec8e88c0cc4",
        "prep1-bottom-i2":
            "a01b870e9552bfdea2ebe467f8cb8ca69b76a4559c2925ead14f3d0ad25b6d74",
        "applied-bottom-i3":
            "0bdce9c1d98af1b74fe816fa788cae8c93f55866de440a221974674918160a42",
        "prep1-bottom-i3":
            "9e02ec9b9afb67b45cd41b52313b68b38d5653e897fedc0824b14f39dfaf579e",
        "applied-bottom-i4":
            "b326d23b3b061e04d2fe89077d1df4ddec5eb65f1c9ab48a256b0b1612c65702",
        "prep1-bottom-i4":
            "291e5285dacc9c158e20aabf73af621af84de122e2801d5b343b84da57fdfd06",
        "applied-bottom-i5":
            "78ecdad38f71aea690217a6c43702287187aa0da01aecf42e0f51ec6751a5a90",
        "prep1-bottom-i5":
            "9c46ec7cd83f94625d65b60901fc9413896d7253c71c3bbc12bd895497767a4d",
        "applied-bottom-i6":
            "bb8aef938961239b5f36680a304c05b1d3f159df652192634d9efe2e7bf09ed6",
        "prep1-bottom-i6":
            "1f03a2eaee3db3e0969b358591b1b4138e84632cf53fda8cbae36c90722f1bcd",
    }[_k]

#: 24 件盲读原始件哈希前缀逐字钉死（盲读亲测在案；全量哈希见
#: FROZEN_SHA256；任何再派发/替换都会使前缀不符→fail-closed 中止）。
RAW_PINNED_PREFIXES = {k: v[:8] for k, v in (
    ("applied-top-i1", FROZEN_SHA256[RAW_FILES["applied-top-i1"]]),
    ("prep1-top-i1", FROZEN_SHA256[RAW_FILES["prep1-top-i1"]]),
    ("applied-top-i2", FROZEN_SHA256[RAW_FILES["applied-top-i2"]]),
    ("prep1-top-i2", FROZEN_SHA256[RAW_FILES["prep1-top-i2"]]),
    ("applied-top-i3", FROZEN_SHA256[RAW_FILES["applied-top-i3"]]),
    ("prep1-top-i3", FROZEN_SHA256[RAW_FILES["prep1-top-i3"]]),
    ("applied-top-i4", FROZEN_SHA256[RAW_FILES["applied-top-i4"]]),
    ("prep1-top-i4", FROZEN_SHA256[RAW_FILES["prep1-top-i4"]]),
    ("applied-top-i5", FROZEN_SHA256[RAW_FILES["applied-top-i5"]]),
    ("prep1-top-i5", FROZEN_SHA256[RAW_FILES["prep1-top-i5"]]),
    ("applied-top-i6", FROZEN_SHA256[RAW_FILES["applied-top-i6"]]),
    ("prep1-top-i6", FROZEN_SHA256[RAW_FILES["prep1-top-i6"]]),
    ("applied-bottom-i1", FROZEN_SHA256[RAW_FILES["applied-bottom-i1"]]),
    ("prep1-bottom-i1", FROZEN_SHA256[RAW_FILES["prep1-bottom-i1"]]),
    ("applied-bottom-i2", FROZEN_SHA256[RAW_FILES["applied-bottom-i2"]]),
    ("prep1-bottom-i2", FROZEN_SHA256[RAW_FILES["prep1-bottom-i2"]]),
    ("applied-bottom-i3", FROZEN_SHA256[RAW_FILES["applied-bottom-i3"]]),
    ("prep1-bottom-i3", FROZEN_SHA256[RAW_FILES["prep1-bottom-i3"]]),
    ("applied-bottom-i4", FROZEN_SHA256[RAW_FILES["applied-bottom-i4"]]),
    ("prep1-bottom-i4", FROZEN_SHA256[RAW_FILES["prep1-bottom-i4"]]),
    ("applied-bottom-i5", FROZEN_SHA256[RAW_FILES["applied-bottom-i5"]]),
    ("prep1-bottom-i5", FROZEN_SHA256[RAW_FILES["prep1-bottom-i5"]]),
    ("applied-bottom-i6", FROZEN_SHA256[RAW_FILES["applied-bottom-i6"]]),
    ("prep1-bottom-i6", FROZEN_SHA256[RAW_FILES["prep1-bottom-i6"]]),
)}

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
    "24 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
    "prep1-bottom）×每格 6 实例（i1–i6）=12 个 reader 智能体（top 侧 6+"
    "bottom 侧 6）、每个 agent 串行读同侧两板（先 applied 后 prep1、"
    "flag_id 跨板连续）；两波次串行保序（波1=top 侧 6 agent、波2="
    "bottom 侧 6 agent）；每派次盲读词只含图像路径（renders-r14b 四张"
    "字节复用=渲染零变更、与 r14–r23 盲读同一批文件）+observation-"
    "guidance-r23.md（866b0157 原字节、本轮字节复用零改写；派发层前缀"
    "覆盖 R23T/R23B→R24T/R24B、round_id→2026-09-10-r24、reader_id→"
    "reader-r24-{top,bottom}-i{1..6}——指引文件内 §6 示例前缀 R23T-/R23B- "
    "为落盘原文、由派发指令覆盖，r16/r22 字节复用+派发层前缀覆盖先例）"
    "+起始序号+v1.2 工具行为规约硬性条款（禁止对图像做任何程序化处理"
    "（裁剪/放大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查看"
    "原图（同一原图可重复查看））；无任何 GT 坐标/类别提示/期望缺陷描述、"
    "零诊断报告内容（黑点探针链与 framing/witness 记录不进任何 reader "
    "上下文、零 r22/r23 现象描述注入）、零 legend/零其他解释（判读输入="
    "指引+单张 PNG+派发指令，与既往轮同构）；读图者不接触 GT/派生台账/"
    "任何校准产物路径；跨实例/跨视角禁止交流（24 次盲读相互独立——独立"
    "性是多实例协议的前提，亦为本轮归因裁决有效性的前提，per "
    "r24-prep-record read_prohibition_note）")

#: 派发模式结构化记录（R24=实例群扩容归因轮：每格 3→6 实例、两波次
#: 串行保序；唯一实验变量=实例数 n[changed_variables[0]]）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 6,
    "dispatch_count_total": 24,
    "agents_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R24T-001..011；prep1 R24T-012..024（跨板连续）",
        "top-i2": "applied R24T-001..008；prep1 R24T-009..017（跨板连续）",
        "top-i3": "applied R24T-001..007；prep1 R24T-008..016（跨板连续）",
        "top-i4": "applied R24T-001..009；prep1 R24T-010..022（跨板连续）",
        "top-i5": "applied R24T-001..005；prep1 R24T-006..011（跨板连续）",
        "top-i6": "applied R24T-001..006；prep1 R24T-007..015（跨板连续）",
        "bottom-i1": "applied R24B-001..002；prep1 R24B-003..004（跨板连续）",
        "bottom-i2": "applied R24B-001..002；prep1 R24B-003..004（跨板连续）",
        "bottom-i3": "applied R24B-001..002；prep1 R24B-003..004（跨板连续）",
        "bottom-i4": "applied R24B-001..003；prep1 R24B-004..006（跨板连续）",
        "bottom-i5": "applied R24B-001..002；prep1 R24B-003..004（跨板连续）",
        "bottom-i6": "applied R24B-001..002；prep1 R24B-003..004（跨板连续）",
    },
    "flag_id_continuity_note": (
        "r24 实测=12/12 实例同实例跨板连续、24 格全部≥1 旗=零零旗格"
        "（与 r24-prep-record protocol_amendment.naming「实例间编号独立，"
        "同实例同侧跨板连续」声明相符——本轮 12 智能体各包两板、编号跨板"
        "连续；程序逐实例实测断言在案 flag_id_continuity_check）——编排侧"
        "仍把实例非弃权/弃权清单与逐旗明细按 (instance, state, flag_id) "
        "限定，跨实例同号不混淆（本轮实测同名旗号跨实例出现：R24T-015 "
        "同时见于 top-i2 与 top-i6、R24T-004 同时见于 top-i4 与 top-i6 等"
        "=实例间编号独立语义的直接观测）"),
    "diff_note": ("R19/R20/R22/R23→R24 派发结构差异=唯一实验变量：每格"
                  "实例数 3→6（12 派次→24 派次；12 个 reader 智能体各包"
                  "同侧两板）、两波次串行保序、同实例先 applied 后 prep1；"
                  "指引=observation-guidance-r23.md 字节复用零改写（派发"
                  "层前缀覆盖 R23T/R23B→R24T/R24B——r16 先例：r15 指引+"
                  "R16T 前缀、r22 先例：r19 指引+R22T/R22B，per "
                  "r24-prep-record protocol_amendment.naming）；渲染/GT/"
                  "阈值/协议正文零变更（v1.3=prep-record 内登记的 n 扩容"
                  "附录、不新建协议文件）；协议侧唯一新增=v1.3 附录"
                  "（v1.2 纯 Read 直读硬性条款照抄沿用；24/24 派次自述"
                  "「未读取盘上任何其他文件」，见 reader_tool_evidence）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准；
#: 全部计数=程序机械实测）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R24 二十四派次全部以 Read 工具"
    "直读内嵌图像、24/24 派次 reading_notes 自述「未读取盘上任何其他"
    "文件」（逐派次句子程序提取在案 reader_tool_evidence）；11 派次另"
    "自述未做跨图/交叉或合并推断（applied/prep1-bottom-i1–i3 与 i5、"
    "prep1-top-i1/i3/i4/i5/i6，排序清单在案 no_cross_inference_sources；"
    "两板同图同判自述）；§4(iii-a) 措辞 notes 级援引=8/24 派次"
    "（applied/prep1-bottom-i1、i2、i3、i5——对照 r19 notes 级 10/12 与 "
    "r22 6/12 与 r23 4/12 在案双基线）、§5B 措辞 notes 级援引=0/24 派次"
    "（本轮指引=observation-guidance-r23.md 字节复用、仍无 §5B 节=任何"
    "援引为零上下文）、§6 报告框收敛条款措辞 notes 级援引=20/24 派次"
    "（三计数分开记、互不合并；逐旗 (iii-a) 字面援引 7 旗、逐旗摘录在案"
    "hypothesis_test.mechanism_observation.criterion_citation_observation）；"
    "全部判读输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/"
    "零探针件/零 legend/零其他文件接触=非盲读违规；本轮唯一操纵因子="
    "实例数 n：每视图 3→6（实例群重抽+扩容=本轮实验操作本身，per "
    "r24-prep-record changed_variables[0] 原文：指引/渲染/GT/阈值/协议"
    "正文零字节触碰）；轮内实例差异=本轮归因主通道的直接测量对象"
    "（n=6 首次可看轮内分布形态：top-i1=1.0 vs top-i2/top-i6 双峰结构"
    "如实记录，见 mechanism_observation.instance_distribution_"
    "observation）。输出格式实例披露（编排侧落盘前处理，盘上件=冻结"
    "证据）：24 件=缩进格式冻结原始判读件、本轮零改动直读（direct JSON "
    "解析；围栏剥离本先例不适用——24 件均为裸 JSON 文本；24 件 parse "
    "校验全部通过、均非盲读违规）")

#: 逐文件原始消息格式（如实入账；盘上件=冻结原始判读件，本轮零改动
#: 直读，parse 均为 direct JSON 解析、零 repair）。
_RAW_FORMAT_NOTE = ("盘上件=缩进格式冻结原始判读件，本轮零改动直读"
                    "（direct JSON 解析通过；非盲读违规）")
RAW_MESSAGE_FORMAT_NOTES = {k: _RAW_FORMAT_NOTE for k in RAW_FILES}

GUIDANCE_NOTE = (
    "本轮指引=observation-guidance-r23.md 字节复用（866b0157 全 64 位"
    "实测锚；per r24-prep-record guidance_reuse：mode=byte_reuse_dispatch_"
    "override、base=derived=observation-guidance-r23.md、byte delta=0、"
    "零改写零派生零写入）：§2 类别枚举/§3 位置口径/§3A 示例（含示例 c）/"
    "§4 置信度与弃权整段（含量化判据 (i)(ii)(iii) 原文、(iii) 接触性判据"
    "原句、(iii-a) 可操作分辨条款全文、三路出口、反放宽条款、confidence "
    "定义、对照说明块）/§5/§5A/§7 判据文本随基座逐字在案；§6 报告框收敛"
    "条款在基座在案（r23 轮唯一增补、本轮非变量）；本轮指引文件内 R23T- "
    "恰 4 处、R23B- 恰 1 处、reader-r23- 恰 1 处（落盘原文，由派发指令"
    "覆盖为 R24T/R24B/reader-r24-*——r16/r22 字节复用+派发层前缀覆盖"
    "先例；程序计数断言在案）；本轮指引无 §5B 节（r19 基座=r15 结构在案）"
    "——§5B 援引计数机制观察照记、任何援引为零上下文（per r24-prep-"
    "record adjudication.mechanism_observation_separate 原文）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 24 轮迭代"
    "（development 域实例群扩容归因轮（多实例协议 v1.3：每视图实例数 "
    "3→6；r23 confounded 后剩余混杂归因第一轴=实例群轴）：迭代轮不得"
    "冒充留出证据；执行 round23-dev-record 下一候选建议（b）（对剩余"
    "混杂（判据内容/实例群/其他输出侧因素）做新预注册轮归因——原文逐字"
    "摘录于 r24-prep-record guidance_reuse.chain_anchors."
    "parent_1_round23_dev_record.candidate_b_quote），"
    "用户 2026-09-10 拍板（user_directive_note 在案）；R21 全组合槽位="
    "冻结件预留位、未触发永久留空（跳号声明在案，r24 与该槽位无涉））。")

INSTRUMENT_NATURE = (
    "实例群扩容归因轮（实例群抽样规模轴）：仪器变更=无（renders-r14b "
    "四图字节复用=与 r14–r23 盲读同一批文件；四 PNG 盘上 sha=witness-"
    "r14b 登记值=prep-record instrument_change.renders 登记值 fail-closed "
    "三方一致；no_instrument_change=true）+判读指引=observation-guidance-"
    "r23.md 字节复用（866b0157；零改写零派生、派发层前缀覆盖）+GT/阈值"
    "零变更（13 条冻结；APR-0011 与 CONTAINMENT_MIN/AREA_RATIO_MAX 只作"
    "口径引用）+协议正文零变更（v1/v1.1/v1.2 继承不改+v1.3 n 扩容附录"
    "[prep-record 内登记、不新建协议文件]；protocol-v2=holdout 冻结件"
    "本轮不启用——v2 生效≠holdout 启动）：唯一实验变量=实例数 n：每视图 "
    "3→6（per r24-prep-record changed_variables[0] "
    "instance-count-n3-to-n6-v1.3；instrument_change=false、guidance_"
    "reuse.mode=byte_reuse_dispatch_override）")

#: 预注册主通道归因三支判据所用阈值（零覆盖；per r24-prep-record
#: hypothesis_test.adjudication 与 m_tuple_definitions 原文：
#: M4(n=6)<0.261904（r16 基线历史口径在案值原样引用不改写）⟺
#: m4_6dp<261904（整数）；split_half_M1_diff≤0.09064（r15→r16 纯重抽
#: 漂移在案参照）⟺ split_half_6dp≤90640（0.09064=|0.862069−0.771429|）。
#: M4 自证=928571−666667=261904（r16 基线 top-i2/top-i1 两实例率之差，
#: 本脚本整数复算断言）。基线数字 live 重放/装载（M1/M2=同一聚合逻辑
#: 对 run-r16/r19/r22/r23 内嵌实例记录双侧复算、不手工抄数）并与下列
#: 在案登记值交叉核对（fail-closed，不符即中止）。
M4_THRESHOLD_6DP = 261_904
SPLIT_HALF_THRESHOLD_6DP = 90_640
#: (27,35)=0.771429（axis-plan baselines_registered.r16_baseline 在案）。
BASE16_TOP_AGGREGATE_REGISTERED = {"abstain": 27, "flags": 35}
#: bottom 侧观察基线（M2；live 重放交叉核对 12/14）。
BASE16_BOTTOM_AGGREGATE_REGISTERED = {"abstain": 12, "flags": 14}
#: M4 阈值自证整数（r16 基线 top-i2 0.928571 − top-i1 0.666667）。
M4_SELF_CHECK_TERMS = (928_571, 666_667, 261_904)
#: M3（黑点族）基线登记值（axis-plan baselines_registered.
#: r16_baseline 在案；脚本对 axis-plan 原文 fail-closed 装载核对，另对
#: run-r16 live 重放交叉核对）。
AXIS_R16_M3_BLACKDOT_RUBRIC = 12
AXIS_R16_M4_TOP_RANGE = 0.261904
R16_TOP_INSTANCE_RATES_REGISTERED = {"top-i1": 0.666667,
                                     "top-i2": 0.928571,
                                     "top-i3": 0.666667}
R16_BOTTOM_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0,
                                 "bottom-i3": 0}
#: contact 族链基线（分型件 rubric 口径在案；回放基期=r13–r16 不变）。
CONTACT_CHAIN_PRIOR = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
#: 黑点族链基线（分型件 rubric 口径在案）。
BLACKDOT_CHAIN_PRIOR = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
BLACKDOT_JUDGED_NORMAL_PRIOR = {"r15": 3, "r16": 2}
#: r18/r19/r20/r22/r23 对照登记值（各自 run 内嵌记录 live 复算交叉核对）。
R17_ROW_REGISTERED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
R18_ROW_REGISTERED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                      "M4": 0.277778}
R19_ROW_REGISTERED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                      "M4": 0.211111}
R20_ROW_REGISTERED = {"M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25}
R22_ROW_REGISTERED = {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
R23_ROW_REGISTERED = {"M1": 0.484848, "M2": 0.571429, "M3": 8,
                      "M4": 0.520833}
R20_FAMILY_COUNTS_REGISTERED = {
    "contact": 2, "existence_blackdot": 6, "existence_other": 10,
    "semantic_confusion": 0, "other": 0}
R22_FAMILY_COUNTS_REGISTERED = {
    "contact": 2, "existence_blackdot": 4, "existence_other": 12,
    "semantic_confusion": 0, "other": 0}
R23_FAMILY_COUNTS_REGISTERED = {
    "contact": 8, "existence_blackdot": 8, "existence_other": 7,
    "semantic_confusion": 1, "other": 0}
#: r24 实测登记值（程序实测须与本表逐一相等 fail-closed；三族 rubric
#: 对照 prep-record adjudication.mechanism_observation_separate 原文
#: 「r19（4/4/14）/r22（2/4/12）/r23（8/8/7+semantic_confusion 1）在案
#: 基线」）。
R24_FAMILY_COUNTS_REGISTERED = {
    "contact": 4, "existence_blackdot": 28, "existence_other": 44,
    "semantic_confusion": 0, "other": 0}
R24_TOP_EXIT_TYPOLOGY_REGISTERED = {"contact": 26, "existence": 30,
                                    "other_layer": 2}

#: bottom 侧 G1 守门逐实例登记表（六 bottom 实例 courtyard 类非弃权旗；
#: 程序实测与本表 expected 逐一相等 fail-closed；per r24-prep-record
#: attribution_plan.guard_channel 原文「G1=六 bottom 实例（bottom-i1–i6）
#: courtyard 类非弃权旗全=0 维持（对照 r15–r19/r22/r23 在案 0/0/0、
#: r20 破坏 2/0/0=g1 分岔先例在案）；任一实例非零→G1 破坏→guard_
#: interrupted 支」）。
SIDE_OBS_REGISTERED = [
    {"instance": f"bottom-i{i}", "expected": 0,
     "note": ("r15–r19/r22/r23 零非弃权 courtyard（r20 破坏 2/0/0 在案="
              "分岔记录）→r24 实测 0（六实例扩容口径）：G1 维持")}
    for i in range(1, 7)]

#: §5B、§4(iii-a) 与 §6 援引机械实测期望集合（分开记、互不合并；r24
#: 实测=程序机械集合、须与登记逐一相等 fail-closed）：旗级 location_
#: evidence 字面「§5B」=0 旗、「分支(」=0 旗、「(iii-a)」=7 旗
#: （applied-bottom-i2 R24B-002 非弃权+applied/prep1-bottom-i5 各 2+
#: prep1-top-i1 R24T-022+prep1-bottom-i2 R24B-004）；notes 级「§5B」=
#: 0/24 派次（本轮指引字节复用、仍无 §5B 节=任何援引为零上下文）、
#: notes 级「(iii-a)」=8/24 派次（bottom-i1/i2/i3/i5 两板；对照 r19
#: notes 级 10/12 与 r22 6/12 与 r23 4/12 双基线）、notes 级 §6=20/24
#: 派次（排除 applied/prep1-top-i3 与 applied/prep1-top-i5 四派次；
#: 本轮零实验变量接触指引=援引分布属实例异质性观察、如实登记）。
S5B_FLAG_CITE_REGISTERED = []
IIIA_FLAG_CITE_REGISTERED = sorted([
    "applied-bottom-i2/R24B-002",
    "applied-bottom-i5/R24B-001",
    "applied-bottom-i5/R24B-002",
    "prep1-bottom-i2/R24B-004",
    "prep1-bottom-i5/R24B-003",
    "prep1-bottom-i5/R24B-004",
    "prep1-top-i1/R24T-022",
])
BRANCH_FLAG_CITE_REGISTERED = []
S5B_NOTES_CITE_REGISTERED = []
IIIA_NOTES_CITE_REGISTERED = sorted([
    "applied-bottom-i1", "applied-bottom-i2", "applied-bottom-i3",
    "applied-bottom-i5", "prep1-bottom-i1", "prep1-bottom-i2",
    "prep1-bottom-i3", "prep1-bottom-i5",
])
S6_NOTES_CITE_REGISTERED = sorted([
    "applied-bottom-i1", "applied-bottom-i2", "applied-bottom-i3",
    "applied-bottom-i4", "applied-bottom-i5", "applied-bottom-i6",
    "applied-top-i1", "applied-top-i2", "applied-top-i4", "applied-top-i6",
    "prep1-bottom-i1", "prep1-bottom-i2", "prep1-bottom-i3",
    "prep1-bottom-i4", "prep1-bottom-i5", "prep1-bottom-i6",
    "prep1-top-i1", "prep1-top-i2", "prep1-top-i4", "prep1-top-i6",
])

#: reroute 类旗标产量链基线（r8–r23 在案；r22=4/r23=2 经各自 run
#: reader.flag_count 在案字段 live 核对；本轮 r24 实测=6）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4, "r16": 2, "r17": 1,
                       "r18": 3, "r19": 3, "r20": 2, "r22": 4, "r23": 2}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1, "r16": 0, "r17": 0, "r18": 0, "r19": 0,
                      "r20": 0, "r22": 0, "r23": 2}


def _fail(msg: str) -> None:
    print(f"[s86-cal-r24] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    return json.loads(_rel(rel).read_text(encoding="utf-8"))


def _first_sentence(text: str, phrase: str) -> str:
    """含指定短语的第一个句子（确定性程序提取；零改写）。

    句界=中文句号「。」；提取自冻结 reader-raw 原文（哈希锚在案），
    摘录非独立证据源、其真值由冻结原文哈希锚承载（模块披露在案）。
    """
    idx = text.find(phrase)
    if idx < 0:
        return ""
    start = text.rfind("。", 0, idx)
    start = 0 if start < 0 else start + 1
    end = text.find("。", idx)
    end = len(text) if end < 0 else end + 1
    return text[start:end].strip()


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
    """GT 文件条目 + R5 重投影：frame_box_pct ← frame_box_pct_r5。

    R14 沿用该重投影：GT 13 条全部 side=top 且本轮渲染零变更
    （renders-r14b 两张 top=renders-r5 逐字节复用）⇒ 重投影输入未变，
    本轮零新派生；bottom GT 无源在案 gt-audit-r1。
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
    # 零旗格 view_check=not_applicable（库侧口径；本轮 24 格全部≥1 旗
    # =24 格 full；zero-flag not_applicable 口径本轮未触发）。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    # 渲染 provenance 按视角分列：本轮渲染零变更=renders-r14b 四图
    # 字节复用（与 r14–r23 盲读同一批文件；framing-r14b 在案）。
    if "-top-" in raw_key:
        framing_note = (
            "top 渲染=渲染零变更（renders-r14b/applied-top.png 298bc620 "
            "与 prep1-top.png b2f84524=renders-r5 逐字节复用、top 无配色"
            "，与 r14–r23 盲读同一批文件）；framing-r14b=7004b017 在案；"
            "本轮 zero-write 零重渲染")
    else:
        framing_note = (
            "bottom 渲染=渲染零变更（renders-r14b 四图字节复用、两板 "
            "bottom 成图逐字节同 d7284259；白墨图元→橙 (255,165,0)、"
            "板内空隙白→绿 (0,128,0)；成图实测橙 81672 px/绿 206632 px"
            "/板内白 0（witness-r14b palette_assertion_summary，脚本 "
            "live 装载核对）；framing-r14b=7004b017 预注册件在案；"
            "r24-prep-record bottom_view_note 在案）")
    return {
        "state": state_desc,
        "source_board": {"path_rel": board_rel, "sha256": board_sha},
        "framing": {"path_rel": REL_FRAMING_R14B, "sha256": _sha(REL_FRAMING_R14B),
                    "note": framing_note},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R5, "sha256": _sha(REL_DERIV_R5),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取该台账"
                     " frame_box_pct_r5（R5 仪器像素界重投影口径；r24 "
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
    """实例主记录（measurement_design item 1；两板合计口径；n=6）。"""
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
                 "跨两板合计；measurement_design item 1；n=6 扩容口径）"
                 % (n_ab, n_fl, abstain_rate))
    # 跨板编号连续性程序实测（DISPATCH_MODE.flag_id_continuity 的核对）
    def _nums(blk):
        return sorted(int(f["flag_id"].split("-", 1)[1])
                      for f in blk["reader_flags"])
    na, np_ = _nums(blk_appl), _nums(blk_prep)
    continuous = bool(na) and bool(np_) and \
        np_[0] == na[-1] + 1 and na == list(range(na[0], na[0] + len(na)))
    return {
        "instance": name, "view": view,
        "reader_id": parsed[spec["parts"][0]]["reader_id"],
        "parts": {"applied": spec["parts"][0], "prep1": spec["parts"][1]},
        "flag_id_cross_board_continuous": continuous,
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
                "r24 实测 flag_id 编号行为=12/12 有旗实例全部同实例跨板"
                "连续、24 格全部≥1 旗=零零旗格（与 r24-prep-record naming"
                "「实例间编号独立，同实例同侧跨板连续」声明相符）——"
                "abstain_ids/non_abstain_flag_ids 按 (instance, state, "
                "flag_id) 限定，跨实例同号不混淆（本轮实测 R24T-015 同时"
                "见于 top-i2 与 top-i6 等=实例间编号独立语义的直接观测）"),
        },
        "per_flag_gt_detail": per_flag_detail,
    }


def _median6(vals: list):
    """恰 6 值的中位数（n=6=第 3/4 序位均值；measurement_design item 2：
    中位数+最小值+最大值三分列、不取整）。"""
    if len(vals) != 6:
        _fail(f"median6 需恰 6 值: {vals}")
    s = sorted(vals)
    return (s[2] + s[3]) / 2


def build_view_layer(instances: dict) -> dict:
    """视角层聚合（measurement_design item 2；每视角 6 实例三分列）。

    本轮 24 格全部≥1 旗（零零旗格）：top/bottom 两视角六实例弃权率
    全部有定义、中位数=第 3/4 序位均值（n=6；不取整）；item 5 零分母
    None 口径本轮未触发（None 分支保留=口径先例代码在案）。
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
                "数值）；min/max 按可计算实例计算"
                % "/".join(none_names))
            range_arithmetic = (
                "实例间弃权率极差（max−min，按可计算实例）= %s − %s = %s"
                "（%s 零旗标分母→None 不计入、如实注明——measurement_"
                "design item 5 口径）"
                % (ar_max, ar_min, ar_range, "/".join(none_names)))
        else:
            ar_median = _median6(ar_vals)
            ar_median_note = ("六实例弃权率均有定义（n=6 中位数=第 3/4 "
                              "序位均值、不取整）")
            ar_min, ar_max = min(ar_vals), max(ar_vals)
            ar_range = cal._round6(ar_max - ar_min)
            range_arithmetic = (
                "实例间弃权率极差（max−min）= %s − %s = %s（逐实例=%s）"
                % (ar_max, ar_min, ar_range,
                   "/".join(f"{n}={ar[n]}" for n in names)))
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
                           "median": _median6(fc_vals),
                           "min": min(fc_vals), "max": max(fc_vals)},
            "abstain_rate": ar_block,
            "matches": {"by_instance": mt,
                        "median": _median6(mt_vals),
                        "min": min(mt_vals), "max": max(mt_vals)},
            "abstain_rate_range": ar_range,
            "abstain_rate_range_arithmetic": range_arithmetic,
        }
    return out


def build_gt_dual(instances: dict, gt_applied: list, gt_prep1: list) -> dict:
    """GT 匹配聚合双口径（measurement_design item 3；n=6 推广）。

    逐 GT 条目 matched_by_count（0..6）=同视角 6 实例中命中该条目的
    实例数；union（≥1/6 实例命中即计）与 agreement（≥4/6 过半数实例
    命中才计=v1.1「≥2/3 过半数」语义的 n=6 推广、v1.3 附录显式冻结）
    两口径并列；召回分母=GT 13 条；bottom 无 GT 在案（gt-audit-r1）
    ⇒ bottom 旗标与 GT 匹配应为空（如实）。
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
    agreement_ids = [g["gt_id"] for g in per_gt if g["matched_by_count"] >= 4]
    return {
        "denominator": 13,
        "denominator_note": ("召回分母=GT 13 条（applied 9+prep1 4；"
                            "全部 side=top——bottom 无 GT 在案 "
                            "gt-audit-r1：bottom GT=无源已关闭，bottom "
                            "旗标与 GT 匹配应为空，如实）"),
        "hit_rule": ("命中判定=每实例逐旗 containment/area_ratio 过门"
                     "（CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明常量"
                     "零改动）+一对一指派后在 GT 条目上归并；top 视角=6 "
                     "实例、bottom 视角=6 实例（v1.3 n 扩容口径）"),
        "union": {"rule": "≥1/6 实例命中即计", "gt_ids": union_ids,
                  "count": len(union_ids),
                  "gt_recall_union": cal._ratio(len(union_ids), 13)},
        "agreement": {"rule": "≥4/6 过半数实例命中才计（v1.1「≥2/3 过半"
                              "数」语义的 n=6 推广、v1.3 附录显式冻结）",
                      "gt_ids": agreement_ids,
                      "count": len(agreement_ids),
                      "gt_recall_agreement": cal._ratio(
                          len(agreement_ids), 13)},
        "per_gt": per_gt,
    }


def pick_representative(instances: dict) -> dict:
    """代表配置选取（measurement_design item 4 预注册 n=6 规则：每视角
    flag_count 升序第 3 序位（下中位）实例；并列按实例编号先序）。"""
    sel = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        counts = {n: instances[n]["combined"]["flag_count"] for n in names}
        ordered = sorted(names, key=lambda n: (counts[n],
                                               INSTANCE_ORDER.index(n)))
        selected = ordered[2]
        third, fourth = counts[ordered[2]], counts[ordered[3]]
        tied = [n for n in ordered[:3] if counts[n] == third]
        sel[view] = {
            "selected": selected,
            "lower_median_flag_count": third,
            "ascending": list(ordered),
            "tie": third == fourth,
            "tie_note": (
                "flag_count 升序第 3/4 序位同为 %d（%s 等 %d 个实例并列）"
                "→按实例编号先序取 %s，如实注明 tie（measurement_design "
                "item 4 预注册规则：并列按实例编号先序、无挑优语义）"
                % (third, "/".join(tied),
                   sum(1 for n in names if counts[n] == third), selected))
            if third == fourth else
            "第 3 序位实例唯一（%s，flag_count=%d）" % (selected, third),
            "flag_count_by_instance": counts,
        }
    return {
        "rule": ("measurement_design item 4（预注册 n=6 口径）：代表配置="
                 "每视角取 flag_count 升序第 3 序位（下中位）实例组成代表"
                 "配置，计算一轮 joint 结果（n=6 中位数=第 3/4 序位均值"
                 "可能非整数→代表实例按下中位序位选取、并列按实例编号"
                 "先序——规则预注册、不得事后调整；与 r22/r23 中位数实例"
                 "口径的差异=v1.3 附录显式声明）"),
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
        "scope": ("代表配置两态联合（measurement_design item 4 预注册 "
                  "n=6 口径：每视角 flag_count 升序第 3 序位（下中位）"
                  "实例；与 per-metric 实例间范围、逐实例原始记录三者"
                  "并列如实呈现，不合并、不挑优）"),
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
                "measurement_design item 5）；min/max 按可计算实例计算，"
                "不编造数值" % "/".join(none_names))
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
                 "归因三支判据（instance_dominated=G1 维持且 M4(n=6)<"
                 "0.261904 且 split_half≤0.09064 / not_instance_dominated="
                 "G1 维持且（M4≥0.261904 或 split_half>0.09064）/ "
                 "guard_interrupted=G1 破坏）各自独立计算、互不凌驾"},
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
                       "r22": "not_met（在案）",
                       "r23": "not_met（在案）",
                       "r24": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
# 逐旗失败通道归因（vs R18；方法照抄 s34–s82：通道级，非旗级）
# ---------------------------------------------------------------------------

def channel_replay(flags: list, flag_views: dict, gt_entries: list) -> dict:
    """近邻失败通道重放（纯函数；与 compare_v3 同源几何原语）。"""
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
    """reroute 类旗标产量（弃权+非弃权合计，全视角；纯函数）。"""
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
    """run-doc 内嵌输入重放（实例名取自该 doc；返回 {(instance, state)}）。"""
    replays = {}
    for name in run_doc["instances"]:
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
                              run_r19: dict, run_r20: dict, run_r22: dict,
                              run_r23: dict,
                              inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R19/R20/R22/R23；通道级分组，非旗级配对；链自 r6）。"""
    r15_replays = replay_round_instances(run_r15)
    r16_replays = replay_round_instances(run_r16)
    r17_replays = replay_round_instances(run_r17)
    r18_replays = replay_round_instances(run_r18)
    r19_replays = replay_round_instances(run_r19)
    r20_replays = replay_round_instances(run_r20)
    r22_replays = replay_round_instances(run_r22)
    r23_replays = replay_round_instances(run_r23)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R24 {key} 通道重放与 compare_v3 对拍不一致")

    def pick(failure, replays, blocks, order=None):
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
            for name, st in replays:
                for e in replays[(name, st)]["entries"]:
                    if e["failure"] == failure:
                        rows.append(_channel_entry(
                            dict(e, state=st, instance=name)))
        rows.sort(key=lambda x: (x["instance"], x["state"], x["flag_id"],
                                 x["gt_id"]))
        return rows

    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", r16_replays, None)
    geo_r17 = pick("area_ratio_rejected", r17_replays, None)
    geo_r18 = pick("area_ratio_rejected", r18_replays, None)
    geo_r19 = pick("area_ratio_rejected", r19_replays, None)
    geo_r20 = pick("area_ratio_rejected", r20_replays, None)
    geo_r22 = pick("area_ratio_rejected", r22_replays, None)
    geo_r23 = pick("area_ratio_rejected", r23_replays, None)
    geo_r24 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", r16_replays, None)
    cat_r17 = pick("category_mismatch", r17_replays, None)
    cat_r18 = pick("category_mismatch", r18_replays, None)
    cat_r19 = pick("category_mismatch", r19_replays, None)
    cat_r20 = pick("category_mismatch", r20_replays, None)
    cat_r22 = pick("category_mismatch", r22_replays, None)
    cat_r23 = pick("category_mismatch", r23_replays, None)
    cat_r24 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", r16_replays, None)
    view_r17 = pick("view_gate", r17_replays, None)
    view_r18 = pick("view_gate", r18_replays, None)
    view_r19 = pick("view_gate", r19_replays, None)
    view_r20 = pick("view_gate", r20_replays, None)
    view_r22 = pick("view_gate", r22_replays, None)
    view_r23 = pick("view_gate", r23_replays, None)
    view_r24 = pick("view_gate", inst_replays, inst_blocks)
    # 与在案 run 登记交叉核对（fail-closed：重放结果须与在案一致）
    for num, replays, doc in (
            ("r15", geo_r15, run_r15), ("r16", geo_r16, run_r16),
            ("r17", geo_r17, run_r17), ("r18", geo_r18, run_r18),
            ("r19", geo_r19, run_r19), ("r20", geo_r20, run_r20),
            ("r22", geo_r22, run_r22), ("r23", geo_r23, run_r23)):
        if replays != doc["channel_attribution"]["channel_1_geometry_gate"][
                f"{num}_area_ratio_rejected_entries"]:
            _fail(f"{num.upper()} 几何门重放与 run 在案登记不一致")
    for num, replays, doc in (
            ("r15", cat_r15, run_r15), ("r16", cat_r16, run_r16),
            ("r17", cat_r17, run_r17), ("r18", cat_r18, run_r18),
            ("r19", cat_r19, run_r19), ("r20", cat_r20, run_r20),
            ("r22", cat_r22, run_r22), ("r23", cat_r23, run_r23)):
        if replays != doc["channel_attribution"]["channel_2_category_gate"][
                f"{num}_category_mismatch_entries"]:
            _fail(f"{num.upper()} 类别门重放与 run 在案登记不一致")
    for num, replays, doc in (
            ("r15", view_r15, run_r15), ("r16", view_r16, run_r16),
            ("r17", view_r17, run_r17), ("r18", view_r18, run_r18),
            ("r19", view_r19, run_r19), ("r20", view_r20, run_r20),
            ("r22", view_r22, run_r22), ("r23", view_r23, run_r23)):
        if replays != doc["channel_attribution"][
                "view_gate_observations"][f"{num}_entries"]:
            _fail(f"{num.upper()} 视角门重放与 run 在案登记不一致")

    n_top_nonabstain = sum(
        1 for b in inst_blocks
        if b["_instance"].startswith("top")
        for f in b["reader_flags"] if not f["abstain"])
    geo_change = (
        "几何门通道（R19→R22→R23→R24）：面积比出局条目 %d→%d→%d→%d"
        "（本轮=实例群扩容归因轮：G2=实测观察项非字母支；本轮 top 非弃权"
        "旗 %d 条、几何门=%d 条；r20 重放=%d 条逐轮对照；跨轮实例群漂移"
        "混杂照旧声明，只描述不断言。"
        % (len(geo_r19), len(geo_r22), len(geo_r23), len(geo_r24),
           n_top_nonabstain, len(geo_r24), len(geo_r20)))
    cat_change = (
        "类别门通道（R19→R22→R23→R24）：类别不符出局条目 %d→%d→%d→%d"
        "（r16 在案 1 条=prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3，"
        "r17/r18 重放=0 条、r19 重放=2 条、r20 重放=%d 条（run-r20 在案）、"
        "r22 重放=%d 条（run-r22 在案）、r23 重放=%d 条（run-r23 在案）、"
        "r24 重放=%d 条；r11 唯一原发条目 R11T-012↔GT-REVC-AP-8-R1Q2 "
        "语境下逐轮计数如实登记；跨轮实例群漂移混杂照旧声明，只描述不断言。"
        % (len(cat_r19), len(cat_r22), len(cat_r23), len(cat_r24),
           len(cat_r20), len(cat_r22), len(cat_r23), len(cat_r24)))

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
            "r21": None,
            "r22": len(geo_r22),
            "r23": len(geo_r23),
            "r24": len(geo_r24),
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
            "r21": None,
            "r22": len(cat_r22),
            "r23": len(cat_r23),
            "r24": len(cat_r24),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=0→r17=0→r18=0→r19=0→r20=0→r22=2→r23=1"
                 "→r24=%d（r22 回升 2、r23 回落 1、r24 清零=n 扩容下逐轮"
                 "如实计数；r21=跳号未执行置 None）；类别门 r6=1→r7=0→"
                 "r8=1→r9=0→r10=0→r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→"
                 "r17=0→r18=0→r19=2→r20=%d→r22=%d→r23=%d→r24=%d"
                 "（r11 唯一条目 R11T-012↔AP-8 无再现；r16 1 条=r16 在案、"
                 "r17–r24 逐轮如实计数）"
                 % (len(geo_r24), len(cat_r20), len(cat_r22), len(cat_r23),
                    len(cat_r24))),
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
            "ref": {"path_rel": REL_PREP_R24, "sha256": _sha(REL_PREP_R24)},
            "declaration": prep_doc_attribution_declaration(),
            "primary_channel": prep_doc_primary_channel(),
            "guard_channel": prep_doc_guard_channel_text(),
        },
        "method": {
            "source_of_r15_r16_r17_r18_r19_r20_r22_r23_detail": (
                "calibration-run-r15.json / calibration-run-r16.json / "
                "calibration-run-r17.json / calibration-run-r18.json / "
                "calibration-run-r19.json / calibration-run-r20.json / "
                "calibration-run-r22.json / calibration-run-r23.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34–s82 deviation_note 口径：本轮对 R15/R16/"
                "R17/R18/R19/R20/R22/R23/R24 均以内嵌输入+compare_v3 "
                "同源几何原语（calibration._containment/_area_ratio、"
                "CONTAINMENT_MIN=0.5、AREA_RATIO_MAX=10.0 声明常量）对每"
                "非弃权旗标×同态 GT 确定性重放通道分类：containment<0.5"
                "（含 None=无交集）无条目；近邻且视角不符=view_gate；近邻"
                "且面积比>上限=area_ratio_rejected（几何门）；近邻且面积比"
                "≤上限且类别不符=category_mismatch（类别门）；类别相符且"
                "双条件过=candidate。"),
            "replay_cross_check": {
                "candidate_pairs_by_round": {
                    "r15": {f"{name}/{st}": [list(p) for p in
                                             r15_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r15_replays},
                    "r16": {f"{name}/{st}": [list(p) for p in
                                             r16_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r16_replays},
                    "r17": {f"{name}/{st}": [list(p) for p in
                                             r17_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r17_replays},
                    "r18": {f"{name}/{st}": [list(p) for p in
                                             r18_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r18_replays},
                    "r19": {f"{name}/{st}": [list(p) for p in
                                             r19_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r19_replays},
                    "r20": {f"{name}/{st}": [list(p) for p in
                                             r20_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r20_replays},
                    "r22": {f"{name}/{st}": [list(p) for p in
                                             r22_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r22_replays},
                    "r23": {f"{name}/{st}": [list(p) for p in
                                             r23_replays[(name, st)]
                                             ["candidate_pairs"]]
                            for name, st in r23_replays},
                    "r24": {key: [list(p) for p in inst_replays[key]
                                  ["candidate_pairs"]] for key in RAW_FILES},
                },
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R19 唯一候选对="
                         "prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT、R22="
                         "R22T-007/R22T-017↔L1SHORT、R23=R23T-011↔"
                         "L1SHORT+R23T-002↔R4J3 均在案复现；R24 四候选对="
                         "prep1-top-i2 R24T-015、prep1-top-i4 R24T-019、"
                         "prep1-top-i5 R24T-009、prep1-top-i6 R24T-015 各"
                         "与 GT-REVC-P1-L1SHORT，见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R15T/R15B…R24T/R24B 来自不同 "
            "reader 实例、不同判读实例；轮内实例行为差异见 reader.reader_"
            "instance_note=混杂因素；r24 12/12 有旗实例跨板连续、零零旗格="
            "与 prep-record naming 声明相符、同属实例输出行为登记如实记录；"
            "轮内同名旗号跨实例出现[如 R24T-015 见于 top-i2 与 top-i6]="
            "实例间编号独立语义的直接观测、按 (instance, state, flag_id) "
            "限定不混淆）；下列分组是通道级归因，不是旗级配对；development "
            "域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "r17_area_ratio_rejected_entries": geo_r17,
            "r18_area_ratio_rejected_entries": geo_r18,
            "r19_area_ratio_rejected_entries": geo_r19,
            "r20_area_ratio_rejected_entries": geo_r20,
            "r22_area_ratio_rejected_entries": geo_r22,
            "r23_area_ratio_rejected_entries": geo_r23,
            "r24_area_ratio_rejected_entries": geo_r24,
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
            "r23_category_mismatch_entries": cat_r23,
            "r24_category_mismatch_entries": cat_r24,
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
            "r23_entries": view_r23,
            "r24_entries": view_r24,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r24 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）。"
                     % len(view_r24)),
        },
        "gate_chain_since_r6": chain,
        "r24_specific_observations": [
            "R24 十二实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条（本轮 4 条命中全部=prep1 态 "
            "GT-REVC-P1-L1SHORT：top-i2 R24T-015/top-i4 R24T-019/top-i5 "
            "R24T-009/top-i6 R24T-015；对照 r19 唯一命中 L1SHORT、r20 零"
            "命中、r22 两条 L1SHORT、r23 两条[R4J3+L1SHORT]如实并列；GT "
            "条目层 union/agreement 与代表配置口径见 gt_match_dual/"
            "aggregation_representative（如实分列）；bottom 非弃权旗零"
            "匹配属结构性（GT 13 条全部 side=top，bottom GT 无源在案 "
            "gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R24 courtyard 类旗标 %d 条（top %d+bottom %d）：top 非弃权 "
            "6 条（top-i4 两板 R24T-001/010 贴近报告+top-i5 两板 R24T-"
            "001/002/006/007 贴近报告）+top 弃权 1 条（top-i4 prep1 "
            "R24T-021）；bottom 零 courtyard 类旗标（对照 r20 的 bottom "
            "非弃权 2 条=G1 破坏在案，r24 六实例口径 G1 维持）；top 弃权"
            "构成分型（机械主出口分类）=接触性 26+存在性 30+层归属其他 2"
            "（hypothesis_test.mechanism_observation.abstain_typology "
            "逐旗登记在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R24 几何门 %d 条（r19=0→r22=2→r23=1→r24=0 逐轮计数如实登记；"
            "G2=实测观察项非本轮字母支）；类别门 %d 条（r16=1 后的 r17–"
            "r24 逐轮计数如实登记）；视角门条目数见 view_gate_observations"
            "（如实单列）。"
            % (len(geo_r24), len(cat_r24)),
            "R24 suspicious_reroute 旗标 6 条（弃权 4[top-i3 两板 R24T-"
            "007/014+top-i6 两板 R24T-004/010 存在性出口]+非弃权 2[top-i2 "
            "两板 R24T-006/014 负责任报告]，(instance, state, flag_id) "
            "限定）；产量链 r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→"
            "r15=4→r16=2→r17=1→r18=3→r19=3→r20=2→r22=4→r23=2→r24=6；"
            "「等长」/「蛇形」子串 6 旗机械命中全 0（滥用型通道被动追踪="
            "0，见 hypothesis_test.reroute_continuation_r24，非本轮判据"
            "输入）。",
            "courtyard 被动追踪（r11–r23 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r24 "
            "courtyard_tracking 节）。",
        ],
    }


def _m_tuple_6dp(m1, m2, m3, m4) -> tuple:
    """四元组 → 6 位定点比较键（M1/M2/M4=率×10^6 取整、M3=整数直接）。"""
    return (int(round(m1 * 1000000)), int(round(m2 * 1000000)),
            int(m3), int(round(m4 * 1000000)))


def adjudicate_attribution(m4_6dp: int, split_half_6dp: int,
                           g1_ok: bool) -> tuple:
    """主通道归因三支判据合成（纯函数；判据原文=
    r24-prep-record hypothesis_test.adjudication；6 位定点整数比较）。

    (id) instance_dominated=G1 维持（六 bottom 实例 courtyard 非弃权旗
         全=0）且 M4(n=6)<0.261904 且 split_half_M1_diff≤0.09064→实例群
         抽样噪声足以解释元组离散（判据内容归因让位）；
    (nid) not_instance_dominated=G1 维持且（M4(n=6)≥0.261904 或
         split_half_M1_diff>0.09064）→离散超出抽样尺度、下一归因轴=
         判据内容（判据内容/其他输出侧）；
    (gi) guard_interrupted=G1 破坏（任一 bottom 实例 courtyard 非弃权旗
         >0）→归因悬置、机制观察照常（支序最高）。
    全部阈值比较=6 位定点整数（避免浮点）；三支互斥完备（g1_ok 时：
    M4×split_half 二维四象限中 instance_dominated 恰占「双内」象限、
    其余三象限均=至少一条件超出→not_instance_dominated），未覆盖组合
    即 RuntimeError（自洽性破坏）。返回 (verdict, branch_key)。
    """
    if not g1_ok:
        return ("guard_interrupted", "guard_interrupted_g1")
    m4_within = m4_6dp < M4_THRESHOLD_6DP
    split_within = split_half_6dp <= SPLIT_HALF_THRESHOLD_6DP
    if m4_within and split_within:
        return ("instance_dominated", "instance_dominated_both_within")
    if not m4_within and not split_within:
        return ("not_instance_dominated", "not_instance_dominated_both_exceed")
    if not m4_within:
        return ("not_instance_dominated",
                "not_instance_dominated_m4_exceeds")
    return ("not_instance_dominated",
            "not_instance_dominated_split_half_exceeds")


def _prep_doc() -> dict:
    """r24-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R24)


def _effective_pfv(prep_doc: dict) -> dict:
    """prep-record 受保护文件锚期望（追加式 v2 覆盖；fail-closed）。

    r1 冻结件零回写：其 pfv.cli.py 锚=历史参考值 6ed4f3fd…；cli.py 现值
    0a738047… 已经铜环案裁定接纳（archive/copper-loop/
    COPPER-LOOP-ADJUDICATION-2026-09-11.md）。v2 追加件（supersedes 链+
    anchor_amendment 变更说明在案，DEV-E0-004 授权）承载更新后的锚期望。
    v2 缺失/kind 不符/supersedes 链与 r1 件不符→_fail（不静默回落）。
    """
    v2 = _json_load(REL_PREP_R24_V2)
    if v2["kind"] != "tl2_calibration_r24_prep_record_v2" \
            or v2["supersedes"]["path_rel"] != REL_PREP_R24 \
            or v2["supersedes"]["sha256"] != _sha(REL_PREP_R24):
        _fail("prep-record v2 追加件 supersedes 链与 r1 冻结件不符")
    pfv = dict(prep_doc["protected_files_verification"]["hashes"])
    pfv.update(v2["protected_files_verification"]["hashes"])
    return pfv


def prep_doc_attribution_declaration() -> str:
    """归因声明文本（取自 r24-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["declaration"]


def prep_doc_primary_channel() -> str:
    """主通道文本（取自 r24-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]


def prep_doc_guard_channel_text() -> str:
    """守门通道文本（取自 r24-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["guard_channel"]


# ---------------------------------------------------------------------------
# 预注册假设裁决执行（三支判据+守门独立单列+机制观察单列）
# ---------------------------------------------------------------------------

def bottom_courtyard_non_abstain(instances: dict) -> dict:
    """bottom 侧 G1 守门实测（n=6 操作化定义：六 bottom 实例 courtyard
    类非弃权旗数；per r24-prep-record attribution_plan.guard_channel 原文；
    守门独立单列、进归因三支判据（G1 维持=三支判据前提；G1 破坏→
    guard_interrupted 独占）。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    清单已按 (instance, state, flag_id) 限定）；逐实例计数与
    SIDE_OBS_REGISTERED 的 expected（=r24 实测登记）逐一相等
    （fail-closed，不符即中止）。
    """
    out = {}
    for i in range(1, 7):
        name = f"bottom-i{i}"
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
    """视角全旗聚合弃权（分子, 分母）重放实测（对 run-doc 内嵌实例记录
    按 states 层重放，不读 combined 汇总值）。"""
    n_fl = 0
    n_ab = 0
    for name in instances:
        for st in ("applied", "prep1"):
            blk = run_doc["instances"][name]["states"][st]
            n_fl += len(blk["reader_flags"])
            n_ab += blk["compare_v3"]["abstain"]["abstain_count"]
    return n_ab, n_fl


def run_view_aggregate_live(run_doc: dict, view: str) -> tuple:
    """按视角前缀对任意 run-doc 复算全旗聚合弃权（分子, 分母）。"""
    names = sorted(n for n in run_doc["instances"]
                   if n.startswith(view))
    return _view_aggregate_abstain_live(run_doc, tuple(names))


def run_rubric_blackdot_live(run_doc: dict) -> int:
    """run-doc 内嵌 rubric 族计数装载（黑点族=M3 口径；不手工抄数）。"""
    return run_doc["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"][
            "existence_blackdot"]


def run_top_range_live(run_doc: dict) -> float:
    """run-doc 内嵌 top 逐实例弃权率极差（M4 历史口径=逐实例两板合计）。"""
    return run_doc["view_layer"]["top"]["abstain_rate_range"]


def round_view_aggregate(instances: dict, view_instances: tuple) -> tuple:
    """本轮视角全旗聚合弃权（分子, 分母）（与基线重放同一聚合口径：
    实例两板合计；与实例层 combined 计数同源）。"""
    n_fl = 0
    n_ab = 0
    for name in view_instances:
        n_fl += instances[name]["combined"]["flag_count"]
        n_ab += instances[name]["combined"]["abstain_count"]
    return n_ab, n_fl


def verify_reroute_continuation(instances: dict, raw_texts: dict) -> list:
    """reroute 类旗标被动追踪逐旗判定（r12 通道延续；零期望；fail-closed）。

    对 reroute 类旗标全列逐旗（n=6 本轮 6 条）：子串命中集=程序实测
    （「等长|蛇形」对 location_evidence）；摘录=location_evidence 原文
    逐字（程序提取、冻结原文哈希锚承载）；登记滥用型机械命中事实。
    """
    live = []
    for name in INSTANCE_ORDER:
        for d in instances[name]["per_flag_gt_detail"]:
            if d["category"] != "suspicious_reroute":
                continue
            fid = d["flag_id"]
            src = (INSTANCES[name]["parts"][0] if d["state"] == "applied"
                   else INSTANCES[name]["parts"][1])
            doc = json.loads(_rel(RAW_FILES[src]).read_text(encoding="utf-8"))
            loc = None
            for img in doc["per_image"]:
                for f in img["flags"]:
                    if f["flag_id"] == fid:
                        loc = f["location_evidence"]
            if loc is None:
                _fail(f"reroute 旗 location_evidence 缺失: {fid} ({src})")
            hits = [s for s in ("等长", "蛇形") if s in loc]
            negation = "不适用" in loc
            live.append({
                "source": src, "flag_id": fid,
                "instance": name, "state": d["state"],
                "abstain": d["abstain"],
                "detected_substring_hits": hits,
                "negation_style_reference": negation,
                "location_evidence_excerpt": loc,
                "adjudication": ("abstain_existence" if d["abstain"]
                                 else "responsible_report"),
            })
    live.sort(key=lambda r: (r["instance"], r["flag_id"]))
    return live


# ---------------------------------------------------------------------------
# 分型件 rubric 机械口径（contact 族计数唯一口径；装载→r13–r16 重放
# 对拍→r24 套用；关键词表/优先级全部从 abstain-typology-r13-r16.json
# 装载，不另嵌一套词表；对拍基期=r13–r16（8/15/5/10）不变）
# ---------------------------------------------------------------------------

def load_typology_rubric() -> dict:
    """分型件 rubric 装载（fail-closed：五类定义+关键词表+优先级在件）。"""
    doc = _json_load(REL_TYPOLOGY)
    rub = doc["rubric"]
    kt = rub["keyword_tables"]
    for key in ("blackdot_terms", "uncertainty_terms", "contact_terms",
                "contact_doubt_patterns", "text_primary_terms",
                "text_primary_pattern", "explicit_existence_terms",
                "semantic_terms", "generic_existence_patterns"):
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


def exit_type_classify(text: str, kt: dict) -> str:
    """机械主出口分类（弃权分型 contact/existence/other_layer；与 rubric
    族为两套登记口径、分列不合并；方法=关键词机械规则）：

    contact=含接触词（contact_terms）且命中接触怀疑模式
    （contact_doubt_patterns）——主出口=接触性分辨；
    existence=否则含显式存在性词（explicit_existence_terms）或泛化
    存在模式（generic_existence_patterns）——主出口=存在性；
    other_layer=其余——层归属等其他出口。
    与 rubric 的差异：不做黑点优先与文本主因抑制（两套口径分列、
    如实登记）。
    """
    ct = [k for k in kt["contact_terms"] if k in text]
    cd = [name for name, pat in kt["contact_doubt_patterns"].items()
          if re.search(pat, text)]
    if ct and cd:
        return "contact"
    ee = [k for k in kt["explicit_existence_terms"] if k in text]
    ge = [name for name, pat in kt["generic_existence_patterns"].items()
          if re.search(pat, text)]
    if ee or ge:
        return "existence"
    return "other_layer"


def replay_typology_families(typology_doc: dict, kt: dict) -> dict:
    """r13–r16 132 条弃权旗 rubric 机械重放对拍（口径忠实性证明）。"""
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


def build_rubric_rows_r24(instances: dict, kt: dict) -> list:
    """r24 全部旗标逐旗 rubric 套用（弃权旗=互斥族分类；非弃权旗不分型
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
                _fail(f"r24 旗 location_evidence 缺失: {d['flag_id']} "
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
                         "exit_type": (exit_type_classify(loc, kt)
                                       if d["abstain"] else None),
                         "matched_blackdot_terms":
                             hits.get("blackdot_terms", [])})
    rows.sort(key=lambda r: (r["instance"], r["state"], r["flag_id"]))
    return rows


def _locate_flag_text(source_key: str, flag_id: str) -> str:
    """从冻结 reader-raw 原文定位旗 location_evidence（程序提取）。"""
    doc = json.loads(
        _rel(RAW_FILES[source_key]).read_text(encoding="utf-8"))
    for img in doc["per_image"]:
        for f in img["flags"]:
            if f["flag_id"] == flag_id:
                return f["location_evidence"]
    _fail(f"旗 location_evidence 缺失: {flag_id} ({source_key})")


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          run_r11: dict, run_r12: dict, run_r13: dict,
                          run_r14: dict, run_r15: dict, run_r16: dict,
                          run_r17: dict, run_r18: dict, run_r19: dict,
                          run_r20: dict, run_r22: dict, run_r23: dict,
                          axis_plan: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（r23-confounded-residual-confound-instance-axis-attribution，
    实例群扩容归因轮）裁决节（预注册归因三支判据执行；字母裁决唯一正式
    +守门 G1/G2 独立单列+机制观察单列+度量教训单列）。

    字母裁决（唯一正式裁决）=判据 r24-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：三支=instance_dominated/not_instance_dominated/guard_
    interrupted；G1=六 bottom 实例 courtyard 非弃权旗全=0；M4(n=6)=12 个
    （态,实例）格弃权率极差（先 6 位定点取率再取最大−最小）；split_half_
    M1_diff=|M1(i1–i3 双视图聚合)−M1(i4–i6 双视图聚合)|（6 位定点整数
    交叉相乘）；G2=实测观察项非本轮字母支（G2>0→资格门剔除不入排序；
    r19=0/r22=2/r23=1 对照在案）；判据比较全 6 位定点整数、字母裁决无
    浮点路径。机制观察单列（逐实例率分布双峰结构/split-half 稳 vs 极差
    爆拉分解/弃权分型/三族计数 r19/r22/r23 三基线对照/援引计数/M2/M4
    跨口径声明），不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R24)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（prep-record chain_anchors 内嵌登记值与盘上实测
    # 逐一核对，fail-closed）
    anchors = prep_doc["guidance_reuse"]["chain_anchors"]
    p1 = anchors["parent_1_round23_dev_record"]
    if p1["path_rel"] != REL_DEV_R23 \
            or p1["sha256_measured"] != _sha(REL_DEV_R23) \
            or p1["sha256_prefix_expected"] != "343a6747":
        _fail("prep-record 链锚（parent_1 round23-dev-record）与盘上实测不符")
    if "confounded" not in p1["letter"] \
            or p1["g2_geometry_gate_r23"] != 1 \
            or p1["measured_tuple"] != {"M1": 0.484848, "M2": 0.571429,
                                        "M3": 8, "M4": 0.520833}:
        _fail("prep-record parent_1 r23 实测锚与预期不符")
    if "对剩余混杂（判据内容/实例群/其他输出侧因素）做新预注册轮归因" \
            not in p1["candidate_b_quote"]:
        _fail("prep-record parent_1 候选(b)授权原文与预期不符")
    rej23 = p1["rejected_entry_transcript"]
    if rej23["flag_id"] != "R23T-004" or rej23["instance"] != "top-i3" \
            or rej23["category"] != "other_advisory" \
            or rej23["area_ratio"] != 11.45868:
        _fail("prep-record parent_1 r23 出局条目摘录锚与预期不符")
    p2 = anchors["parent_2_round22_dev_record_drift_anchor"]
    if p2["path_rel"] != REL_DEV_R22 \
            or p2["sha256_measured"] != _sha(REL_DEV_R22) \
            or p2["sha256_prefix_expected"] != "b4b8fbe9":
        _fail("prep-record 链锚（parent_2 round22-dev-record）与盘上实测不符")
    if p2["drift_text"] != "0.09064" or p2["drift_occurrence_count"] != 9:
        _fail("prep-record parent_2 drift 锚与预期不符")
    if _rel(REL_DEV_R22).read_text(encoding="utf-8").count(
            p2["drift_text"]) != p2["drift_occurrence_count"]:
        _fail("dev-r22 drift 0.09064 raw text 计数与 prep-record 登记不符")
    a22 = anchors["run_r22_metric_anchor"]
    if a22["path_rel"] != REL_RUN_R22P \
            or a22["sha256_measured"] != _sha(REL_RUN_R22P):
        _fail("prep-record 链锚（run-r22 度量锚）与盘上实测不符")
    for tok in ("0.390244", "regressed", "0.211111"):
        if tok not in json.dumps(a22, ensure_ascii=False):
            _fail(f"prep-record run-r22 锚缺预期 token: {tok}")
    a23 = anchors["run_r23_metric_anchor"]
    if a23["path_rel"] != REL_RUN_R23P \
            or a23["sha256_measured"] != _sha(REL_RUN_R23P) \
            or a23["sha256_prefix_expected"] != "15f58350":
        _fail("prep-record 链锚（run-r23 度量锚）与盘上实测不符")
    if "0.484848" not in a23["frozen_values"] \
            or "confounded" not in a23["frozen_values"] \
            or "G2=1" not in a23["frozen_values"]:
        _fail("prep-record run-r23 冻结值文本与预期不符")
    r23lin = anchors["r23_prep_record_structure_lineage"]
    if r23lin["path_rel"] != REL_PREP_R23 \
            or r23lin["sha256"] != _sha(REL_PREP_R23):
        _fail("prep-record 链锚（r23-prep-record 结构血统）与盘上实测不符")
    wit = anchors["render_witness_r14b_byte_reuse"]
    if wit["path_rel"] != REL_WITNESS_R14B \
            or wit["sha256"] != _sha(REL_WITNESS_R14B):
        _fail("prep-record 链锚（witness-r14b 字节复用）与盘上实测不符")
    if anchors["evaluation_protocol_v1_preserved"]["path_rel"] \
            != REL_PROTOCOL \
            or anchors["evaluation_protocol_v1_preserved"]["sha256"] \
            != _sha(REL_PROTOCOL):
        _fail("prep-record 链锚（evaluation-protocol-v1）与盘上实测不符")
    v2 = anchors["evaluation_protocol_v2_holdout_not_activated"]
    if v2["path_rel"] != REL_PROTOCOL_V2 \
            or v2["sha256_measured"] != _sha(REL_PROTOCOL_V2) \
            or v2["sha256_prefix_expected"] != "365b67ef":
        _fail("prep-record 链锚（protocol-v2 holdout 未启用）与盘上实测不符")
    axa = anchors["axis_plan_m4_threshold_anchor"]
    if axa["path_rel"] != REL_AXIS_PLAN \
            or axa["sha256_measured"] != _sha(REL_AXIS_PLAN) \
            or axa["sha256_prefix_expected"] != "b6ec6467":
        _fail("prep-record 链锚（axis-plan M4 阈值锚）与盘上实测不符")
    gr = prep_doc["guidance_reuse"]
    if gr["mode"] != "byte_reuse_dispatch_override" \
            or gr["base"] != "observation-guidance-r23.md" \
            or gr["base_path_rel"] != REL_GUIDANCE_R23 \
            or gr["base_sha256"] != _sha(REL_GUIDANCE_R23) \
            or gr["derived_path_rel"] != REL_GUIDANCE_R23 \
            or gr["derived_sha256"] != _sha(REL_GUIDANCE_R23) \
            or gr["byte_size"] != {"base": 23125, "delta": 0,
                                   "derived": 23125} \
            or gr["dispatch_override"]["round_id"] \
            != "2026-09-10-r23 → 2026-09-10-r24（派发层覆盖）":
        _fail("prep-record guidance_reuse 字节复用锚与盘上实测不符")
    ident = gr["chain_anchors"]["guidance_base_r23_byte_reuse"][
        "identity_facts"]
    gtext = _rel(REL_GUIDANCE_R23).read_text(encoding="utf-8")
    for tok, want in (("# R23 轮 reader 判读指引", 1),
                      ("- round_id_constant: `2026-09-10-r23`", 1),
                      ("2026-09-09-r19", 0), ("2026-09-10-r23", 1),
                      ("R19", 0), ("R19B-", 0), ("R19T-", 0), ("R22", 0),
                      ("R23B-", 1), ("R23T-", 4), ("r22", 0),
                      ("reader-r19", 0), ("reader-r23", 2),
                      ("reader-r23-", 1), ("renders-r14b", 2)):
        if gtext.count(tok) != want:
            _fail(f"r23 指引 identity_facts 计数不符: {tok!r} "
                  f"实测={gtext.count(tok)} 登记={want}")
    if prep_doc["kind"] != "tl2_calibration_r24_prep_record":
        _fail("prep-record kind 与预期不符")
    if prep_doc["round_id_constant"] != ROUND_ID \
            or prep_doc["round_label"] != ROUND_LABEL \
            or prep_doc["declared_date"] != DECLARED_DATE \
            or prep_doc["instrument_change"]["changed"] is not False \
            or prep_doc["no_instrument_change"] is not True:
        _fail("prep-record 轮次标识/instrument_change.changed 与预期不符")
    if prep_doc["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("prep-record in_calibrated_range 应恒 False")
    if len(prep_doc["changed_variables"]) != 1 \
            or prep_doc["changed_variables"][0]["id"] \
            != "instance-count-n3-to-n6-v1.3" \
            or prep_doc["changed_variables"][0]["axis"] \
            != "instance_sampling_scale（实例群抽样规模轴）" \
            or prep_doc["changed_variables"][0]["instrument_change"] \
            is not False:
        _fail("prep-record changed_variables 应恰 1 条=实例数 n 扩容")
    if "实例数 n" not in prep_doc["manipulated_factor"]:
        _fail("prep-record manipulated_factor 与预期不符")
    if len(prep_doc["measurement_design"]["items"]) != 5:
        _fail("prep-record measurement_design 应恰 5 条")
    # 四 PNG sha 三方核对（FROZEN 锚=witness-r14b 登记=prep-record 登记）
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
    pfv = _effective_pfv(prep_doc)
    for rel in ("pcbflow/cli.py", "pcbflow/config.py",
                "toolchain_lock.json"):
        if pfv[rel] != _sha(rel):
            _fail(f"prep-record 保护文件锚与盘上实测不符: {rel}")
    v1p = prep_doc["protocol_amendment"]["v1_file_preserved"]
    if v1p["path_rel"] != REL_PROTOCOL \
            or v1p["sha256_measured"] != _sha(REL_PROTOCOL) \
            or v1p["zero_byte_preserved"] is not True:
        _fail("prep-record v1_file_preserved 与盘上实测不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "0.261904" not in adj["instance_dominated"] \
            or "0.09064" not in adj["instance_dominated"] \
            or "G1" not in adj["instance_dominated"]:
        _fail("prep-record instance_dominated 判据文本与预期不符")
    if "0.261904" not in adj["not_instance_dominated"] \
            or "0.09064" not in adj["not_instance_dominated"] \
            or "判据内容" not in adj["not_instance_dominated"]:
        _fail("prep-record not_instance_dominated 判据文本与预期不符")
    if "G1 破坏" not in adj["guard_interrupted"] \
            or "归因悬置" not in adj["guard_interrupted"]:
        _fail("prep-record guard_interrupted 判据文本与预期不符")
    if "唯一正式裁决" not in adj["letter_branch_map"] \
            or "不新增字母支" not in adj["letter_branch_map"]:
        _fail("prep-record letter_branch_map 与预期不符")
    if "261904" not in adj["fixed_point_comparison_note"] \
            or "90640" not in adj["fixed_point_comparison_note"] \
            or "928571" not in adj["fixed_point_comparison_note"]:
        _fail("prep-record fixed_point_comparison_note 与预期不符")
    if "资格门剔除" not in adj["g2_observation_separate"] \
            or "r22=2/r23=1/r19=0" not in adj["g2_observation_separate"]:
        _fail("prep-record g2_observation_separate 与预期不符")
    if "4/4/14" not in adj["mechanism_observation_separate"] \
            or "2/4/12" not in adj["mechanism_observation_separate"] \
            or "8/8/7" not in adj["mechanism_observation_separate"]:
        _fail("prep-record 机制观察单列条款（三族三基线）与预期不符")
    if "部分重复≠独立重复" not in adj["metric_lesson_separate"] \
            or "0.09064" not in adj["metric_lesson_separate"]:
        _fail("prep-record 度量教训单列条款与预期不符")
    if "三向记账" not in adj["three_way_bookkeeping"] \
            or "不合并" not in adj["three_way_bookkeeping"]:
        _fail("prep-record 三向记账条款与预期不符")
    if "描述性边界" not in adj["descriptive_boundary_note"] \
            or "互不凌驾" not in adj["descriptive_boundary_note"]:
        _fail("prep-record 描述性边界条款与预期不符")
    if ht["hypothesis_id"] != \
            "r23-confounded-residual-confound-instance-axis-attribution":
        _fail("prep-record hypothesis_id 与预期不符")
    # 阈值常数自检（6 位定点；与 prep-record 判据同锚）
    if M4_THRESHOLD_6DP != 261_904 \
            or SPLIT_HALF_THRESHOLD_6DP != 90_640:
        _fail("M4/split-half 阈值常数与 prep-record 判据不符")
    if M4_SELF_CHECK_TERMS[0] - M4_SELF_CHECK_TERMS[1] \
            != M4_SELF_CHECK_TERMS[2]:
        _fail("M4 阈值自证整数复算不符（928571−666667=261904）")
    if SPLIT_HALF_THRESHOLD_6DP != abs(862069 - 771429):
        _fail("split-half 阈值自证不符（90640=|0.862069−0.771429|）")
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
    if "M1 升序" not in axis_plan["comparison_rule"]["ordering"]:
        _fail("axis-plan 排序规则与预期不符")
    if "G1 或 G2 破坏的轮次不参与排序" \
            not in axis_plan["comparison_rule"]["eligibility_gate"]:
        _fail("axis-plan 资格门与预期不符")
    # rubric 链回放（先核对一致才可应用 r24 分型）
    typology_doc = load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    replay_proof = replay_typology_families(typology_doc, kt)
    if replay_proof["contact_counts"]["r16"] \
            != CONTACT_CHAIN_PRIOR["r16"] \
            or rb["M3_blackdot_abstain_flags_rubric"] \
            != replay_proof["blackdot_counts"]["r16"]:
        _fail("contact/M3 基线（r16）三方装载不一致")
    rubric_rows = build_rubric_rows_r24(instances, kt)
    contact = sum(1 for r in rubric_rows
                  if r["abstain"] and r["family"] == "contact")
    family_counts = {fam: sum(1 for r in rubric_rows
                              if r["abstain"] and r["family"] == fam)
                     for fam in ("contact", "existence_blackdot",
                                 "existence_other", "semantic_confusion",
                                 "other")}
    if family_counts != R24_FAMILY_COUNTS_REGISTERED:
        _fail(f"家族计数与登记不符: {family_counts}")
    contact_by_view = {"top": 0, "bottom": 0}
    for r in rubric_rows:
        if r["abstain"] and r["family"] == "contact":
            contact_by_view["top" if r["instance"].startswith("top")
                            else "bottom"] += 1
    # 黑点转非弃权旗（机制观察计数）：非弃权旗中黑点对象词命中
    nonabstain_bd = [r for r in rubric_rows
                     if not r["abstain"] and r["matched_blackdot_terms"]]
    # 黑点判正常派次计数（分型件 blackdot_dispatch 口径：notes 判黑点
    # 正常且该派次零黑点词旗标）——程序实测
    judged_normal = []
    bd_disp_rows = []
    for key in RAW_FILES:
        doc = json.loads(_rel(RAW_FILES[key]).read_text(encoding="utf-8"))
        has_bd_flag = any(
            [k for k in kt["blackdot_terms"] if k in f["location_evidence"]]
            for img in doc["per_image"] for f in img["flags"])
        notes_bd = [k for k in kt["blackdot_terms"]
                    if k in parsed_notes[key]]
        if notes_bd:
            bd_disp_rows.append({"source": key,
                                 "abstain_flag": bool(has_bd_flag),
                                 "notes_hit_terms": notes_bd})
        if notes_bd and not has_bd_flag:
            judged_normal.append(key)
    if sorted(judged_normal) != ["applied-top-i3", "prep1-top-i3"]:
        _fail(f"黑点判正常派次与实测不符: {sorted(judged_normal)}")
    # §5B、§4(iii-a) 与 §6 援引实测（分开记、互不合并）：旗级/派次级
    # 机械集合须与登记逐一相等
    s5b_flag_hits = []
    iiia_flag_hits = []
    iibranch_flag_hits = []
    s5b_notes_hits = []
    iiia_notes_hits = []
    s6_notes_hits = []
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
        if "§6" in parsed_notes[key] \
                or "报告框收敛条款" in parsed_notes[key]:
            s6_notes_hits.append(key)
    if sorted(f"{s}/{f}" for s, f in s5b_flag_hits) \
            != S5B_FLAG_CITE_REGISTERED:
        _fail(f"§5B 旗级援引与登记不符: {sorted(s5b_flag_hits)}")
    if sorted(f"{s}/{f}" for s, f in iiia_flag_hits) \
            != IIIA_FLAG_CITE_REGISTERED:
        _fail(f"(iii-a) 旗级援引与登记不符: {sorted(iiia_flag_hits)}")
    if sorted(f"{s}/{f}" for s, f in iibranch_flag_hits) \
            != BRANCH_FLAG_CITE_REGISTERED:
        _fail(f"分支( 援引与登记不符: {sorted(iibranch_flag_hits)}")
    if sorted(s5b_notes_hits) != S5B_NOTES_CITE_REGISTERED:
        _fail(f"§5B notes 级援引与登记不符: {sorted(s5b_notes_hits)}")
    if sorted(iiia_notes_hits) != IIIA_NOTES_CITE_REGISTERED:
        _fail(f"(iii-a) notes 级援引与登记不符: {sorted(iiia_notes_hits)}")
    if sorted(s6_notes_hits) != S6_NOTES_CITE_REGISTERED:
        _fail(f"§6 援引与登记不符: {sorted(s6_notes_hits)}")
    # 旗级 (iii-a) 援引 7 旗逐旗摘录（程序提取、冻结原文哈希锚承载）
    iiia_flag_rows = []
    for key, fid in sorted(iiia_flag_hits):
        loc = _locate_flag_text(key, fid)
        if "(iii-a)" not in loc:
            _fail(f"(iii-a) 摘录定位不符: {key}/{fid}")
        abst = None
        doc = json.loads(
            _rel(RAW_FILES[key]).read_text(encoding="utf-8"))
        for img in doc["per_image"]:
            for f in img["flags"]:
                if f["flag_id"] == fid:
                    abst = f["abstain"]
                    cat = f["category"]
        inst = next(n for n in INSTANCE_ORDER
                    if key in INSTANCES[n]["parts"])
        st = ("applied" if INSTANCES[inst]["parts"][0] == key else "prep1")
        iiia_flag_rows.append({"source": key, "flag_id": fid,
                               "instance": inst, "state": st,
                               "abstain": abst, "category": cat,
                               "location_evidence_excerpt": loc})
    # 基线数字 live 重放与在案登记交叉核对（fail-closed；不手工抄数）
    base16_ab, base16_fl = r16_top_abstain_aggregate_live(run_r16)
    if cal._ratio(base16_ab, base16_fl) != 0.771429:
        _fail("run-r16 top 基线重放率与冻结值 0.771429 不符")
    base16_bot_ab, base16_bot_fl = r16_bottom_abstain_aggregate_live(run_r16)
    r16_courtyard_base = r16_baseline_courtyard_live(run_r16)
    r16_top_rates = {n: run_r16["instances"][n]["combined"]["abstain_rate"]
                     for n in ("top-i1", "top-i2", "top-i3")}
    if r16_top_rates != R16_TOP_INSTANCE_RATES_REGISTERED \
            or cal._round6(max(r16_top_rates.values())
                           - min(r16_top_rates.values())) \
            != AXIS_R16_M4_TOP_RANGE:
        _fail("r16 top 逐实例弃权率构成与 axis-plan 登记不符")
    # r18/r19/r20/r22/r23 对照行 live 复算（各自 run 内嵌输入）
    r18_ab, r18_fl = run_view_aggregate_live(run_r18, "top")
    r18_bot_ab, r18_bot_fl = run_view_aggregate_live(run_r18, "bottom")
    r18_m1 = cal._ratio(r18_ab, r18_fl)
    r18_m2 = cal._ratio(r18_bot_ab, r18_bot_fl)
    r18_m3 = run_rubric_blackdot_live(run_r18)
    r18_m4 = run_top_range_live(run_r18)
    r18_row = {"M1": r18_m1, "M2": r18_m2, "M3": r18_m3, "M4": r18_m4}
    if r18_row != R18_ROW_REGISTERED:
        _fail(f"r18 对照行 live 复算与登记不符: {r18_row}")
    r19_ab, r19_fl = run_view_aggregate_live(run_r19, "top")
    r19_bot_ab, r19_bot_fl = run_view_aggregate_live(run_r19, "bottom")
    r19_m1 = cal._ratio(r19_ab, r19_fl)
    r19_m2 = cal._ratio(r19_bot_ab, r19_bot_fl)
    r19_m3 = run_rubric_blackdot_live(run_r19)
    r19_m4 = run_top_range_live(run_r19)
    r19_row = {"M1": r19_m1, "M2": r19_m2, "M3": r19_m3, "M4": r19_m4}
    if r19_row != R19_ROW_REGISTERED:
        _fail(f"r19 对照行 live 复算与登记不符: {r19_row}")
    r20_ab, r20_fl = run_view_aggregate_live(run_r20, "top")
    r20_bot_ab, r20_bot_fl = run_view_aggregate_live(run_r20, "bottom")
    r20_counts = run_r20["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    r20_row_live = {"M1": cal._ratio(r20_ab, r20_fl),
                    "M2": cal._ratio(r20_bot_ab, r20_bot_fl),
                    "M3": r20_counts["existence_blackdot"],
                    "M4": run_top_range_live(run_r20)}
    if r20_row_live != R20_ROW_REGISTERED:
        _fail(f"r20 对照行 live 复算与登记不符: {r20_row_live}")
    if r20_counts != R20_FAMILY_COUNTS_REGISTERED:
        _fail("run-r20 三族计数与登记不符")
    r22_ab, r22_fl = run_view_aggregate_live(run_r22, "top")
    r22_bot_ab, r22_bot_fl = run_view_aggregate_live(run_r22, "bottom")
    r22_counts = run_r22["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    r22_row_live = {"M1": cal._ratio(r22_ab, r22_fl),
                    "M2": cal._ratio(r22_bot_ab, r22_bot_fl),
                    "M3": r22_counts["existence_blackdot"],
                    "M4": run_top_range_live(run_r22)}
    if r22_row_live != R22_ROW_REGISTERED:
        _fail(f"r22 对照行 live 复算与登记不符: {r22_row_live}")
    if r22_counts != R22_FAMILY_COUNTS_REGISTERED:
        _fail("run-r22 三族计数与登记不符")
    r23_ab, r23_fl = run_view_aggregate_live(run_r23, "top")
    r23_bot_ab, r23_bot_fl = run_view_aggregate_live(run_r23, "bottom")
    r23_counts = run_r23["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    r23_row_live = {"M1": cal._ratio(r23_ab, r23_fl),
                    "M2": cal._ratio(r23_bot_ab, r23_bot_fl),
                    "M3": r23_counts["existence_blackdot"],
                    "M4": run_top_range_live(run_r23)}
    if r23_row_live != R23_ROW_REGISTERED:
        _fail(f"r23 对照行 live 复算与登记不符: {r23_row_live}")
    if r23_counts != R23_FAMILY_COUNTS_REGISTERED:
        _fail("run-r23 三族计数与登记不符")
    if run_r23["hypothesis_test"]["verdict"] != "confounded" \
            or run_r23["hypothesis_test"]["measurement"]["guard_channel"][
                "g2_geometry_gate_r23"] != 1:
        _fail("run-r23 字母/G2 锚与登记不符")
    if run_r22["hypothesis_test"]["verdict"] != "regressed" \
            or run_r20["hypothesis_test"]["verdict"] != "reject":
        _fail("run-r22/run-r23 先验字母锚与登记不符")
    # reroute 产量链基线交叉核对（r8–r20/r22/r23 在案）
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
            or run_r22["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r22"] \
            or run_r23["reader"]["flag_count"]["reroute_class_production"] \
            != REROUTE_CHAIN_PRIOR["r23"]:
        _fail("reroute 类产量链与在案 run 不符")

    # ---- 主通道实测（三支判据；24 派次全口径）----
    top_names = tuple(f"top-i{i}" for i in range(1, 7))
    bot_names = tuple(f"bottom-i{i}" for i in range(1, 7))
    abst_top, flags_top = round_view_aggregate(instances, top_names)
    top_rate = cal._ratio(abst_top, flags_top)
    abst_bot, flags_bot = round_view_aggregate(instances, bot_names)
    bot_rate = cal._ratio(abst_bot, flags_bot)
    # M4(n=6)=12 个（态,实例）格弃权率极差（先 6 位定点取率再取差；
    # M4_operationalization_note 口径）
    m4_cells = []
    for name in top_names:
        for st in ("applied", "prep1"):
            blk = instances[name]["states"][st]
            n = len(blk["reader_flags"])
            ab = blk["compare_v3"]["abstain"]["abstain_count"]
            rate = cal._ratio(ab, n)
            m4_cells.append({"cell": f"{name}/{st}", "flags": n,
                             "abstain": ab, "rate": rate,
                             "rate_6dp": (None if rate is None
                                          else int(round(rate * 1000000)))})
    cell_vals = [c["rate_6dp"] for c in m4_cells]
    if any(v is None for v in cell_vals):
        _fail("M4(n=6) 12 格中出现零旗标格（与零零旗格实测矛盾）")
    m4_6dp = max(cell_vals) - min(cell_vals)
    m4 = cal._round6(m4_6dp / 1000000)
    m4_max_cell = max(m4_cells, key=lambda c: c["rate_6dp"])
    m4_min_cell = min(m4_cells, key=lambda c: c["rate_6dp"])
    # split_half_M1_diff=|M1(i1–i3)−M1(i4–i6)|（双视图=两态合并聚合；
    # 6 位定点整数、不做浮点除法）
    sh = {}
    for label, rng in (("A_i1_i3", (1, 2, 3)), ("B_i4_i6", (4, 5, 6))):
        ab = sum(instances[f"top-i{i}"]["combined"]["abstain_count"]
                 for i in rng)
        fl = sum(instances[f"top-i{i}"]["combined"]["flag_count"]
                 for i in rng)
        sh[label] = {"abstain": ab, "flags": fl,
                     "rate_6dp": round(ab * 1000000 / fl)}
    split_half_6dp = abs(sh["A_i1_i3"]["rate_6dp"] - sh["B_i4_i6"]["rate_6dp"])
    split_half = cal._round6(split_half_6dp / 1000000)
    # 守门 G1（六 bottom 实例 courtyard 非弃权全 0 维持）——独立单列
    by_instance = bottom_courtyard_non_abstain(instances)
    bot_courtyard_flags = sum(
        1 for n in bot_names
        for d in instances[n]["per_flag_gt_detail"]
        if d["category"] == "courtyard_crowding")
    g1_ok = all(v == 0 for v in by_instance.values())
    # G2 出局条目数（top 视非弃权旗标 frame_box_pct 几何门面积比出局
    # 条目数）——实测观察项、非本轮字母支
    geo_r22 = attribution["channel_1_geometry_gate"][
        "r22_area_ratio_rejected_entries"]
    geo_r23 = attribution["channel_1_geometry_gate"][
        "r23_area_ratio_rejected_entries"]
    geo_r24 = attribution["channel_1_geometry_gate"][
        "r24_area_ratio_rejected_entries"]
    geo_r19 = attribution["channel_1_geometry_gate"][
        "r19_area_ratio_rejected_entries"]
    g2_zero = len(geo_r24) == 0
    guard_ok = len(geo_r24) <= len(geo_r19)
    g2_ok = guard_ok is True
    guards_ok = bool(g1_ok and g2_ok)
    # 归因三支合成（判据字面；支序=guard→instance_dominated→not_...
    # 合成逻辑在 adjudicate_attribution 纯函数内、可独立构造边界用例）
    verdict, branch_key = adjudicate_attribution(
        m4_6dp, split_half_6dp, g1_ok)
    crit_instance_dominated = verdict == "instance_dominated"
    crit_not_instance_dominated = verdict == "not_instance_dominated"
    crit_guard_interrupted = verdict == "guard_interrupted"
    m4_exceeds = m4_6dp >= M4_THRESHOLD_6DP
    split_exceeds = split_half_6dp > SPLIT_HALF_THRESHOLD_6DP
    # 字母裁决（归因三支判据，per r24-prep-record adjudication 原文）
    if crit_guard_interrupted:
        letter_branch = (
            "(gi) G1 守门破坏（bottom courtyard 非弃权实测 %s 含非零）→"
            "guard_interrupted 独占（归因悬置、机制观察照常；不新增字母支、"
            "不升级归因）" % list(by_instance.values()))
    elif crit_instance_dominated:
        letter_branch = (
            "(id) G1 维持（%s）且 M4(n=6)=%s<0.261904 且 split_half_M1_"
            "diff=%s≤0.09064（双条件同时成立）——instance_dominated：实例群"
            "抽样噪声足以解释元组离散（判据内容归因让位、发展域收敛证据"
            "如实登记）" % (list(by_instance.values()), m4, split_half))
    elif branch_key == "not_instance_dominated_m4_exceeds":
        letter_branch = (
            "(nid) G1 维持（%s）且 M4(n=6)=%s≥0.261904（6 位定点 %d≥%d）、"
            "split_half_M1_diff=%s≤0.09064（%d≤%d）——not_instance_dominated"
            "（M4 条件超出）：离散超出抽样尺度、下一归因轴=判据内容（判据"
            "内容/其他输出侧）" % (list(by_instance.values()), m4, m4_6dp,
                                   M4_THRESHOLD_6DP, split_half,
                                   split_half_6dp,
                                   SPLIT_HALF_THRESHOLD_6DP))
    elif branch_key == "not_instance_dominated_split_half_exceeds":
        letter_branch = (
            "(nid) G1 维持（%s）且 split_half_M1_diff=%s>0.09064——"
            "not_instance_dominated（split-half 条件超出）：离散超出抽样"
            "尺度、下一归因轴=判据内容（判据内容/其他输出侧）"
            % (list(by_instance.values()), split_half))
    else:
        letter_branch = (
            "(nid) G1 维持（%s）且 M4(n=6)=%s≥0.261904 且 split_half_M1_"
            "diff=%s>0.09064（双条件均超出）——not_instance_dominated："
            "离散超出抽样尺度、下一归因轴=判据内容（判据内容/其他输出侧）"
            % (list(by_instance.values()), m4, split_half))
    verdict_text = (
        "按预注册判据（r24-prep-record.json hypothesis_test.adjudication "
        "原文，归因三支判据）=%s（字母口径，唯一正式裁决、轮后不改写）："
        "落支=%s。实测：R24 五键=(M1=%s, M2=%s, M3=%d, M4(n=6)=%s, "
        "split_half_M1_diff=%s)（M1=top 全旗聚合弃权率 %d/%d、M2=bottom "
        "同口径 %d/%d、M3=黑点族弃权旗数（分型件 rubric 口径）=%d、M4=12 "
        "个（态,实例）格弃权率极差 max=%s（%s）−min=%s（%s）、split_half="
        "|%d/%d−%d/%d|（6 位定点 |%d−%d|=%d）；比较集 live 复算：r16 基线 "
        "(0.771429, 0.857143, 12, 0.261904)、r19 (0.461538, 0.571429, 4, "
        "0.211111)、r22 (0.390244, 0.2, 4, 0.104545)、r23 (0.484848, "
        "0.571429, 8, 0.520833)（各自 run 内嵌实例记录 live 复算+冻结锚"
        "交叉核对一致，不手工抄数）；G2=几何门面积比出局条目 r19=%d→r22="
        "%d→r23=%d→r24=%d（=0=%s；实测观察项非字母支、G2>0 才触发资格门"
        "剔除）；G1（六 bottom 实例 courtyard 非弃权全 0）=%s。实例群扩容"
        "归因轮（唯一实验变量=实例数 n：每视图 3→6、24 派次；指引字节"
        "复用、渲染字节冻结）下字母裁决只回答「M 元组三轮离散是否为实例群"
        "抽样噪声所主导」的归因判据命中方向：instance_dominated 支命中→"
        "判据内容归因让位（发展域收敛证据如实登记）；not_instance_"
        "dominated 支命中→离散超出抽样尺度、下一归因轴=判据内容（判据"
        "内容/其他输出侧）；guard_interrupted 支（若 G1 破坏）→归因悬置。"
        "r23 字母=confounded 与 r22 字母=regressed 维持不改写、不得回溯"
        "改判既往轮次（r8–r23 字母裁决维持不变）。判据均为描述性边界、"
        "非 APR-0011 门（门照常独立计算，互不凌驾、run-record 内分开"
        "表述）；机制观察单列（逐实例率分布双峰结构/split-half 稳 vs 极差"
        "爆拉分解/弃权分型/三族计数三基线对照/援引计数/M2/G2 出局条目"
        "[本轮=0、空摘录如实登记]），不凌驾、不改写字母裁决。注意：跨轮"
        "实例群漂移混杂照旧声明（部分重复≠独立重复、同域同编排实例池、"
        "验证力度如实声明）；单轮 development 域只描述不断言。"
        % (verdict, letter_branch,
           top_rate, bot_rate, family_counts["existence_blackdot"],
           m4, split_half,
           abst_top, flags_top, abst_bot, flags_bot,
           family_counts["existence_blackdot"],
           m4_max_cell["rate"], m4_max_cell["cell"],
           m4_min_cell["rate"], m4_min_cell["cell"],
           sh["A_i1_i3"]["abstain"], sh["A_i1_i3"]["flags"],
           sh["B_i4_i6"]["abstain"], sh["B_i4_i6"]["flags"],
           sh["A_i1_i3"]["rate_6dp"], sh["B_i4_i6"]["rate_6dp"],
           split_half_6dp,
           len(geo_r19), len(geo_r22), len(geo_r23), len(geo_r24),
           g2_zero,
           "维持（六实例全 0）" if g1_ok else "破坏"))
    # ---- M2 侧观察（对照在案五行）----
    bot_below_r16 = abst_bot * base16_bot_fl < \
        base16_bot_ab * flags_bot
    # ---- 逐实例率分布观察（n=6 首次可看轮内分布形态）----
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    instance_distribution_observation = {
        "role": ("逐实例率分布观察（n=6 首次可看轮内分布形态；机制观察"
                 "单列、不进字母裁决）"),
        "top_rates_by_instance": top_rates,
        "bottom_rates_by_instance": bottom_rates,
        "top_range_per_instance_both_boards": top_range,
        "m4_12_cell_range": m4,
        "m4_cells": m4_cells,
        "m4_max_cell": m4_max_cell,
        "m4_min_cell": m4_min_cell,
        "observation": (
            "top 六实例弃权率=%s（轮内极差[逐实例两板合计口径]=%s）；"
            "12 个（态,实例）格率极差[M4(n=6) 口径]=%s（max=%s@%s、"
            "min=%s@%s）。轮内分布形态（n=6 首次可看、如实记录）：双峰"
            "结构——top-i1=1.0（24/24 全弃权）与 top-i4=0.863636 为高"
            "峰、top-i2=0.117647 与 top-i6=0.133333 为低谷（对照 r23 的 "
            "0.6875/0.166667/0.6 三实例散布）：实例间差异远大于轮内两态"
            "差（同一实例两板率接近、跨实例率跨越整个值域）=离散主要来自"
            "实例间异质性而非态间/判读噪声；聚合 M1=0.552381 落在两峰"
            "之间=聚合值对实例抽样敏感的直接展示。bottom 六实例=%s"
            "（bottom-i1/i2 全非弃权报告、i3–i6 全弃权，轮内极差=%s）。"
            % ("/".join(f"{n}={top_rates[n]}" for n in top_names),
               top_range, m4, m4_max_cell["rate"], m4_max_cell["cell"],
               m4_min_cell["rate"], m4_min_cell["cell"],
               "/".join(f"{n}={bottom_rates[n]}" for n in bot_names),
               bottom_range)),
        "status": ("分布形态如实单列（不进字母裁决；development 域只"
                   "描述不断言）"),
    }
    split_half_decomposition = {
        "role": ("split-half 稳 vs 极差爆拉的分解解读（机制观察单列、"
                 "不进字母裁决；split_half_operationalization_note 口径）"),
        "half_A": dict(sh["A_i1_i3"]),
        "half_B": dict(sh["B_i4_i6"]),
        "split_half_6dp": split_half_6dp,
        "threshold_6dp": SPLIT_HALF_THRESHOLD_6DP,
        "observation": (
            "split-half_M1_diff=%s（6 位定点 %d）≤0.09064（阈值 6 位定点 "
            "%d=|0.862069−0.771429| r15→r16 纯重抽漂移在案参照）——对半"
            "聚合（i1–i3=31/57=0.543860 vs i4–i6=27/48=0.562500）高度"
            "稳定；同一数据上 M4(n=6)=0.888889（12 格极差）远超 0.261904"
            "参照。两者并存=「聚合稳/个体散」分解：实例群内部两半的聚合"
            "弃权率互相抵近（高弃权实例与低弃权实例在对半中配平），但"
            "逐实例率跨越整个值域（见 instance_distribution_observation "
            "双峰结构）——抽样平均的稳定性不等于个体判读的一致性；本轮"
            "字母=not_instance_dominated（M4 条件超出）与该分解一致："
            "离散由个体差异驱动、聚合稳定不构成判据收敛证据。"
            % (split_half, split_half_6dp, SPLIT_HALF_THRESHOLD_6DP)),
        "status": ("分解解读如实单列（描述性、非因果证明；不凌驾字母"
                   "裁决）"),
    }
    # ---- 弃权分型（机械主出口分类；与 rubric 族两套口径分列）----
    typology_counts = {"contact": 0, "existence": 0, "other_layer": 0}
    typology_rows = []
    for r in rubric_rows:
        if not r["abstain"] or not r["instance"].startswith("top"):
            continue
        typology_counts[r["exit_type"]] += 1
        typology_rows.append({"instance": r["instance"],
                              "state": r["state"],
                              "flag_id": r["flag_id"],
                              "category": r["category"],
                              "exit_type": r["exit_type"]})
    if typology_counts != R24_TOP_EXIT_TYPOLOGY_REGISTERED:
        _fail(f"top 弃权分型与登记不符: {typology_counts}")
    # ---- 黑点族（rubric 口径）----
    black_rows = [r for r in rubric_rows
                  if r["abstain"] and r["family"] == "existence_blackdot"]
    black_by_instance = {n: sum(1 for r in black_rows
                                if r["instance"] == n)
                         for n in INSTANCE_ORDER}
    nonabstain_black_rows = [
        {"flag_id": r["flag_id"], "instance": r["instance"],
         "state": r["state"], "category": r["category"],
         "matched_blackdot_terms": r["matched_blackdot_terms"]}
        for r in nonabstain_bd]
    # ---- G2 出局条目（r24=0 空摘录；r23 唯一条目对照自 run-r23 装载）----
    r23_g2_entries = run_r23["hypothesis_test"]["mechanism_observation"][
        "g2_rejected_entries_r23"]["entries"]
    # ---- 绿区语义化（机械观察；§5A/§5B notes 计数）----
    green_semantics = {}
    green_5a_dispatches = 0
    for name in bot_names:
        texts = [parsed_notes[p] for p in INSTANCES[name]["parts"]]
        cites = [("§5A" in t) for t in texts]
        cites_b = [("§5B" in t) for t in texts]
        green_5a_dispatches += sum(1 for c in cites if c)
        green_semantics[name] = {
            "§5A_cited": any(cites),
            "§5B_cited": any(cites_b),
            "§5A_count_by_part": [t.count("§5A") for t in texts],
            "绿_hits_by_part": [t.count("绿") for t in texts],
            "空隙_hits_by_part": [t.count("空隙") for t in texts],
        }
    # ---- 工具规约合规证据（程序机械提取）----
    tool_evidence_rows = []
    no_cross_sources = []
    for key in RAW_FILES:
        sent = _first_sentence(parsed_notes[key], "未读取盘上任何其他文件")
        if not sent:
            _fail(f"v1.2 工具规约自述句缺失: {key}")
        tool_evidence_rows.append({"source": key, "excerpt": sent})
        if ("跨图" in parsed_notes[key]
                or "交叉推断" in parsed_notes[key]):
            no_cross_sources.append(key)
    if len(tool_evidence_rows) != 24:
        _fail("工具规约自述应为 24/24 派次")
    no_cross_sources = sorted(no_cross_sources)
    # ---- 实验对照账（八行并列；资格门=G1/G2 均满足）----
    ledger_rows = {
        "r16_baseline": {"M1": rb["M1_top_aggregate_abstain_rate"],
                         "M2": rb["M2_bottom_aggregate_abstain_rate"],
                         "M3": rb["M3_blackdot_abstain_flags_rubric"],
                         "M4": rb["M4_top_per_instance_rate_range"]},
        "r17_axis1": dict(R17_ROW_REGISTERED),
        "r18_axis2": dict(r18_row),
        "r19_axis3": dict(r19_row),
        "r20_combo_registered": dict(R20_ROW_REGISTERED),
        "r22_repeat_registered": dict(R22_ROW_REGISTERED),
        "r23_repeat_registered": dict(r23_row_live),
        "r24_expansion": {"M1": top_rate, "M2": bot_rate,
                          "M3": family_counts["existence_blackdot"],
                          "M4": m4},
    }
    excluded = ("r20_combo_registered", "r22_repeat_registered",
                "r23_repeat_registered")
    eligible_rows = {k: v for k, v in ledger_rows.items()
                     if k not in excluded
                     and not (k == "r24_expansion" and not guards_ok)}
    ranking = sorted(eligible_rows.items(),
                     key=lambda kv: (kv[1]["M1"], kv[1]["M2"],
                                     kv[1]["M3"], kv[1]["M4"]))
    ranking_order = [k for k, _ in ranking]
    m1_drop_r24 = cal._round6(
        rb["M1_top_aggregate_abstain_rate"] - top_rate)
    attribution_conclusion = {
        "rule_sources": (
            "r24-prep-record.json hypothesis_test.adjudication 归因三支"
            "判据（instance_dominated/not_instance_dominated/guard_"
            "interrupted 原文）+attribution_plan.primary_channel（M4(n=6)"
            "+split_half_M1_diff 双判据裁决）+guard_channel（G1 破坏→"
            "guard_interrupted 独占）"),
        "verdict": verdict,
        "conclusion": (
            "归因结论=not_instance_dominated：M4(n=6)=0.888889 ≥ 0.261904"
            "（6 位定点 888889≥261904）而 split_half_M1_diff=0.018640≤"
            "0.09064（6 位定点 18640≤90640）——G1 维持下 M4 条件超出=离散"
            "超出抽样尺度（逐实例双峰结构 i1=1.0 vs i2/i6≈0.11–0.13；"
            "split-half 稳定与极差爆拉并存=聚合稳/个体散的分解，见机制"
            "观察），下一归因轴=判据内容（判据内容/其他输出侧）；"
            "instance_dominated 支（双条件均内）不命中=实例群扩容至 n=6 "
            "未使轮内逐实例离散收敛到 r16 基线极差尺度内；r23 字母="
            "confounded 与 r22 字母=regressed 维持不改写。G2 侧如实分列："
            "几何门出局条目 r22=2→r23=1→r24=0 清零（r19=0 对照在案）、"
            "类别门 6 条为逐轮新高（r23=1 对照）——机制观察单列、不影响"
            "字母。后续 dev-record 包转记（本轮不预写后续决策）"
            if verdict == "not_instance_dominated" else
            ("归因结论=instance_dominated：G1 维持且 M4(n=6)<0.261904 且 "
             "split_half≤0.09064——实例群抽样噪声足以解释元组离散（判据"
             "内容归因让位、发展域收敛证据如实登记）"
             if verdict == "instance_dominated" else
             "归因结论=guard_interrupted：G1 破坏（归因悬置、机制观察"
             "照常）")),
    }
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；per r24-prep-record "
                 "adjudication.mechanism_observation_separate 原文：M1/"
                 "M2/三族计数/援引计数照常单列机制观察、不进字母裁决；"
                 "G2 出局条目（若有）逐条摘录；M3 与 split_half_M1_diff "
                 "单列对照 r19/r22/r23；gt 照常）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道归因三支判据分开实测（机制：实例群抽样噪声 vs 判据"
                "内容归因判别）：R24 五键=(M1=%s, M2=%s, M3=%d, M4(n=6)=%s, "
                "split_half=%s) vs 比较集 r16 (0.771429, 0.857143, 12, "
                "0.261904)/r19 (0.461538, 0.571429, 4, 0.211111)/r22 "
                "(0.390244, 0.2, 4, 0.104545)/r23 (0.484848, 0.571429, 8, "
                "0.520833)（全部 live 复算交叉核对）；M4 阈值 6 位定点 "
                "%d（=%s）、split-half 阈值 %d（=%s）→verdict=%s（%s）。"
                "判据比较全 6 位定点整数交叉相乘/整数比较、字母裁决无浮点"
                "路径。判据均为 r24-prep-record hypothesis_test.adjudication "
                "原文，轮后如实执行。"
                % (top_rate, bot_rate,
                   family_counts["existence_blackdot"], m4, split_half,
                   M4_THRESHOLD_6DP, AXIS_R16_M4_TOP_RANGE,
                   SPLIT_HALF_THRESHOLD_6DP,
                   cal._round6(SPLIT_HALF_THRESHOLD_6DP / 1000000),
                   verdict, letter_branch)),
            "counts": {
                "r24_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                    "M3": family_counts[
                                        "existence_blackdot"],
                                    "M4": m4,
                                    "split_half_M1_diff": split_half,
                                    "M1_arithmetic": f"{abst_top}/{flags_top}",
                                    "M2_arithmetic": f"{abst_bot}/{flags_bot}"},
                "comparison_rows_live": {
                    "r16_baseline": ledger_rows["r16_baseline"],
                    "r19_axis3": ledger_rows["r19_axis3"],
                    "r22_repeat": r22_row_live,
                    "r23_repeat": r23_row_live},
                "m4_6dp": m4_6dp,
                "m4_threshold_6dp": M4_THRESHOLD_6DP,
                "m4_exceeds": m4_exceeds,
                "split_half_6dp": split_half_6dp,
                "split_half_threshold_6dp": SPLIT_HALF_THRESHOLD_6DP,
                "split_half_exceeds": split_exceeds,
                "g2_rejected_entries_r24": len(geo_r24),
                "crit_instance_dominated": crit_instance_dominated,
                "crit_not_instance_dominated": crit_not_instance_dominated,
                "crit_guard_interrupted": crit_guard_interrupted,
                "verdict": verdict,
                "branch_key": branch_key,
            },
            "status": (
                "实例群扩容归因轮（唯一实验变量=实例数 n：3→6）下双判据"
                "落点=M4 超出/split-half 内→%s 支（如实单列；判据命中与"
                "否的描述性结论，非因果证明）" % verdict),
        },
        "guards_g1_g2": {
            "role": ("守门通道独立单列（per r24-prep-record attribution_"
                     "plan.guard_channel 原文；G1=六 bottom 实例 courtyard "
                     "类非弃权旗全=0=「不得弃权」方向的反向风险守门、任一"
                     "非零→guard_interrupted 独占；G2=top 视非弃权旗标 "
                     "frame_box_pct 几何门面积比>10 出局条目数=实测观察项"
                     "非本轮字母支、G2>0→资格门剔除不入排序）"),
            "observation": (
                "G1=六 bottom 实例 courtyard 非弃权全 0 维持：r24 实测=%s"
                "（对照 r16 基线 0/0/0 live 重放交叉核对一致；r20 破坏 "
                "2/0/0 在案=分岔记录；bottom courtyard 类旗标本身=%d 条）"
                "→G1=%s。G2=几何门面积比出局条目数：R19=%d→R22=%d→R23="
                "%d→R24=%d（=0=%s；本轮出局条目零条、空摘录如实登记）→"
                "资格门剔除未触发、r24 入排序资格=%s。守门结论=%s。"
                % (list(by_instance.values()), bot_courtyard_flags,
                   "维持" if g1_ok else "破坏",
                   len(geo_r19), len(geo_r22), len(geo_r23), len(geo_r24),
                   g2_zero, guards_ok,
                   "G1 维持、G2=0（资格门满足）" if g1_ok
                   else "守门破坏→guard_interrupted 独占（如实登记）")),
            "counts": {
                "g1_bottom_courtyard_non_abstain_r24": by_instance,
                "g1_bottom_courtyard_flags_total_r24": bot_courtyard_flags,
                "g1_r16_baseline_live": r16_courtyard_base,
                "g1_r20_broken_registered":
                    {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0},
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r22": len(geo_r22),
                "g2_geometry_gate_r23": len(geo_r23),
                "g2_geometry_gate_r24": len(geo_r24),
                "g2_rejected_entries_zero": g2_zero,
                "g2_guard_ok_axis_plan_semantics": guard_ok,
                "guards_ok": guards_ok,
            },
            "status": ("守门与字母裁决分开记账（G2=观察项非字母支；G1="
                       "三支判据前提）"),
        },
        "g2_rejected_entries_r24": {
            "role": ("G2 出局条目逐条摘录（per r24-prep-record "
                     "adjudication.g2_observation_separate 原文；本轮实测="
                     "0 条=空摘录如实登记；r23 唯一出局条目对照自 run-r23 "
                     "装载、GT 字段照录[编排侧引用]）"),
            "entries": [
                {"flag_id": e["flag_id"], "instance": e["instance"],
                 "state": e["state"], "category": e["category"],
                 "gt_id": e["gt_id"], "gt_category": e["gt_category"],
                 "containment": e["containment"],
                 "area_ratio": e["area_ratio"]}
                for e in geo_r24],
            "count": len(geo_r24),
            "comparison_to_r23": {
                "source": ("calibration-run-r23.json（15f58350）机制观察 "
                           "g2_rejected_entries_r23 装载（run sha 在案）"),
                "r23_entries": [
                    {k: e[k] for k in ("flag_id", "instance", "state",
                                       "category", "gt_id", "gt_category",
                                       "containment", "area_ratio")}
                    for e in r23_g2_entries],
                "note": ("r23 唯一出局条目=other_advisory 合并铜块"
                         "（R23T-004、area_ratio=11.458680）；r24 几何门"
                         "清零（0 条）——n=6 扩容下 12 个 top 非弃权旗"
                         "（含 6 条 courtyard 类+6 条 other/silk 类近邻"
                         "报告）无一超门，r22 型宽框（≈16.4）与 r23 型"
                         "合并体（11.46）两类机制均未再现，如实登记"),
            },
            "status": ("出局条目 2→1→0 逐轮计数如实登记（观察项、不进"
                       "字母裁决）"),
        },
        "instance_distribution_observation": instance_distribution_observation,
        "split_half_decomposition": split_half_decomposition,
        "abstain_typology": {
            "role": ("top 弃权理由构成分型（机制观察；机械主出口分类="
                     "exit_type_classify 关键词规则[接触词+怀疑模式→"
                     "contact、显式/泛化存在→existence、其余→other_layer]，"
                     "与 rubric 族两套登记口径分列不合并；逐旗分类入账"
                     "typology_rows、不手工转录）"),
            "observation": (
                "top 弃权旗 %d 条逐旗机械主出口分类——接触性=%d 条、存在性="
                "%d 条、层归属其他=%d 条（top 弃权率 %s；分解见 "
                "typology_rows 与 per-instance 计数）。对照 r23（接触性 6+"
                "存在性 10+其他 0，16 条）与 r22（2/14/0，16 条）与 r19"
                "（5/13/0，18 条）在案：n=6 扩容后绝对数 16→58（实例数 "
                "3→6+实例异质性），构成比例仍以存在性/接触性两通道为主。"
                "rubric 族口径另列（contact %d+existence_blackdot %d+"
                "existence_other %d+semantic_confusion %d+other %d=76 条"
                "双侧）——两套口径分列、如实登记。"
                % (len(typology_rows), typology_counts["contact"],
                   typology_counts["existence"],
                   typology_counts["other_layer"], top_rate,
                   family_counts["contact"],
                   family_counts["existence_blackdot"],
                   family_counts["existence_other"],
                   family_counts["semantic_confusion"],
                   family_counts["other"])),
            "type_counts": typology_counts,
            "top_abstain_flags_total": len(typology_rows),
            "typology_rows": typology_rows,
            "r19_reference_counts": {"contact": 5, "existence": 13,
                                     "other_layer": 0},
            "r22_reference_counts": {"contact": 2, "existence": 14,
                                     "other_layer": 0},
            "r23_reference_counts": {"contact": 6, "existence": 10,
                                     "other_layer": 0},
            "method_note": ("本轮分型=机械关键词分类（词表=分型件装载），"
                            "非逐旗人工转录——与 r23 手工摘录登记路径不同、"
                            "如实声明；摘录原文=冻结 reader-raw（哈希锚在"
                            "案），逐旗 (instance, state, flag_id) 可复核"),
            "status": ("弃权分型如实单列（不凌驾字母裁决）"),
        },
        "criterion_citation_observation": {
            "role": ("§5B、(iii-a) 与 §6 措辞援引计数（单列，不进字母"
                     "裁决；三计数分开记、互不合并；per r24-prep-record "
                     "adjudication.mechanism_observation_separate 原文）"),
            "observation": (
                "§5B、(iii-a) 与 §6 措辞援引计数（分开记）：旗级 location_"
                "evidence 含「§5B」=%d 旗、含「(iii-a)」=%d 旗、含「分支(」"
                "=%d 旗（(iii-a) 7 旗逐旗摘录在案 iiia_flag_rows）；notes "
                "级含「§5B」=%d/24 派次（本轮指引字节复用、仍无 §5B 节="
                "任何援引为零上下文、如实登记）、含「(iii-a)」=%d/24 派次"
                "（%s）、含 §6 报告框收敛条款措辞=%d/24 派次（非援引 4 派"
                "次=applied/prep1-top-i3+applied/prep1-top-i5）——三计数"
                "互不合并。基线对照：(iii-a) notes 级对照 r19（10/12 派次、"
                "旗级 (iii-a) 6 旗+分支( 2 旗；run-r19 冻结锚在案）与 r22"
                "（旗级全 0、notes 级 6/12；run-r22 在案）与 r23（旗级全 "
                "0、notes 级 4/12、§6 6/12；run-r23 在案）三基线——本轮 "
                "8/24 与 §6 20/24 属 n=6 分母扩容下的机械计数（比例约"
                "三成与八成），如实登记、不挑优。"
                % (len(s5b_flag_hits), len(iiia_flag_hits),
                   len(iibranch_flag_hits),
                   len(s5b_notes_hits),
                   len(iiia_notes_hits),
                   "、".join(sorted(iiia_notes_hits)[:4]) + " 等 8 派次",
                   len(s6_notes_hits))),
            "citation_counts": {
                "flag_level_s5b_literal": len(s5b_flag_hits),
                "flag_level_s5b_sources": sorted(
                    f"{s}/{f}" for s, f in s5b_flag_hits),
                "flag_level_iiia_literal": len(iiia_flag_hits),
                "flag_level_iiia_sources": sorted(
                    f"{s}/{f}" for s, f in iiia_flag_hits),
                "flag_level_branch_literal": len(iibranch_flag_hits),
                "flag_level_branch_sources": sorted(
                    f"{s}/{f}" for s, f in iibranch_flag_hits),
                "notes_level_s5b": len(s5b_notes_hits),
                "notes_level_s5b_sources": sorted(s5b_notes_hits),
                "notes_level_iiia": len(iiia_notes_hits),
                "notes_level_iiia_sources": sorted(iiia_notes_hits),
                "notes_level_s6_clause": len(s6_notes_hits),
                "notes_level_s6_clause_sources": sorted(s6_notes_hits),
                "notes_level_non_citing_s5b": sorted(
                    set(RAW_FILES) - set(s5b_notes_hits)),
                "baseline_r19_iiia": (
                    "旗级「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 "
                    "派次（run-r19 冻结锚在案）"),
                "baseline_r22_iiia": (
                    "旗级全 0、notes 级 6/12 派次（run-r22 在案）"),
                "baseline_r23_iiia": (
                    "旗级全 0、notes 级 (iii-a)=4/12、§6 条款=6/12（run-"
                    "r23 在案）"),
            },
            "iiia_flag_rows": iiia_flag_rows,
            "evidence_check": (
                "旗级援引集合=机械实测且与登记逐一相等+逐旗摘录=冻结原文"
                "程序提取（substring fail-closed 校验通过）"),
            "status": ("援引计数分开记、不凌驾字母裁决"),
        },
        "bottom_side_observation_maintenance": {
            "role": ("bottom 侧观察 M2（mechanism_observation_separate："
                     "单列、不影响字母；n=6 同口径）"),
            "observation": (
                "M2=bottom 全旗聚合弃权率=%d/%d=%s（对照 r16 基线 12/14="
                "%s，live 重放交叉核对一致；对照 r18 13/19=%s、r19 4/7="
                "%s、r20 4/14=0.285714、r22 2/10=0.2、r23 8/14=0.571429）"
                "——方向=%s。bottom 六实例：i1/i2 全非弃权报告（0/4+0/4）、"
                "i3–i6 全弃权（4/4+6/6+4/4+4/4）；bottom courtyard 类旗=%d "
                "条（六实例零 courtyard 类路径）——非弃权 courtyard 六实例"
                "全 0=G1 维持（见 guards_g1_g2；对照 r20 破坏 2/0/0 在案）；"
                "零旗标派次=%d 个（24 格全部≥1 旗、item 5 零分母→None "
                "口径未触发）。"
                % (abst_bot, flags_bot, bot_rate,
                   cal._ratio(base16_bot_ab, base16_bot_fl),
                   cal._ratio(r18_bot_ab, r18_bot_fl),
                   r19_m2,
                   ("低于 r16 基线（改善方向）" if bot_below_r16
                    else "不低于 r16 基线（维持/恶化）"),
                   bot_courtyard_flags, 0)),
            "counts": {
                "r16_bottom_aggregate_registered":
                    BASE16_BOTTOM_AGGREGATE_REGISTERED,
                "r16_bottom_aggregate_live":
                    f"{base16_bot_ab}/{base16_bot_fl}",
                "r18_bottom_aggregate_live":
                    f"{r18_bot_ab}/{r18_bot_fl}",
                "r19_bottom_aggregate_live":
                    f"{r19_bot_ab}/{r19_bot_fl}",
                "r22_bottom_aggregate_live":
                    f"{r22_bot_ab}/{r22_bot_fl}",
                "r23_bottom_aggregate_live":
                    f"{r23_bot_ab}/{r23_bot_fl}",
                "bottom_flags_r24": flags_bot,
                "bottom_abstain_r24": abst_bot,
                "bottom_abstain_rate_r24": bot_rate,
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
                "zero_flag_cell_count": 0,
                "blackdot_abstain_flags_rubric_r24":
                    family_counts["existence_blackdot"],
                "blackdot_rubric_r16_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
                "blackdot_rubric_r18_registered": R18_ROW_REGISTERED["M3"],
                "blackdot_rubric_r19_registered": R19_ROW_REGISTERED["M3"],
                "blackdot_rubric_r20_registered": R20_ROW_REGISTERED["M3"],
                "blackdot_rubric_r22_registered": R22_ROW_REGISTERED["M3"],
                "blackdot_rubric_r23_registered": R23_ROW_REGISTERED["M3"],
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "status": (
                "M2=0.692308 较 r16 基线回落、高于 r19–r23 全部（如实单列，"
                "不影响字母裁决；development 域只描述不断言）"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（机械观察；r16–r23 先例延续）："
                "bottom 12 派次中 §5A 显式援引=%d 派次（bottom-i2/i3/i6 "
                "两板）、§5B 显式援引=0/12（本轮指引无 §5B 节=零上下文）；"
                "实例级 §5A 援引=%d/6。指引 §5A 判据文本随基座逐字在案，"
                "援引波动属实例自述异质性、如实登记不作废（逐实例 substring "
                "计数在案、无期望、不构成判据输入）。"
                % (green_5a_dispatches,
                   sum(1 for v in green_semantics.values()
                       if v["§5A_cited"]))),
            "green_semantics_by_instance": green_semantics,
            "evidence_check": ("§5A/§5B/绿/空隙 计数=程序 substring 机械"
                               "实测（无人工转录）"),
            "status": ("绿区语义化观察如实单列（不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点族现象追踪（机制观察，分型件 rubric 口径；rubric "
                "机械套用证明见 rubric_families 节）：r24 黑点族弃权旗 %d "
                "条（六实例逐实例分旗：top-i1/top-i4/top-i5 各两板 4、"
                "bottom-i3/i4/i5/i6 各两板 4[bottom-i4 含 2 旗 prep1]="
                "黑点/黑色圆孔性质存在性弃权）——vs r16 黑点族 12 旗（"
                "分型件 rubric 口径在案）/r18=13/r19=4/r20=6/r22=4/r23=8 "
                "多基线对照：远高于五轮基线（n=6 扩容+实例异质性；M3 跨"
                "轮对照=描述性、如实声明）。另实测黑点转非弃权旗 %d 条"
                "（top-i2 两板 4+top-i6 两板 4+bottom-i1 两板 4+bottom-i2 "
                "两板 4=黑色圆点/圆孔按 §4(ii) 孤立或接触路径负责任报告）"
                "+黑点判正常派次 %d 个（applied/prep1-top-i3 两板；对照 "
                "r15=3/r16=2/r18=2/r19=3/r20=4/r22=4/r23=2）。"
                % (len(black_rows), len(nonabstain_black_rows),
                   len(judged_normal))),
            "black_dot_flags": [
                {k: r[k] for k in ("instance", "state", "flag_id",
                                   "category", "matched_blackdot_terms")}
                for r in black_rows],
            "black_dot_non_abstain_flags": nonabstain_black_rows,
            "blackdot_to_non_abstain_count": len(nonabstain_black_rows),
            "by_instance": black_by_instance,
            "all_abstain": all(r["abstain"] for r in
                               [x for x in rubric_rows
                                if x["abstain"]
                                and x["family"] == "existence_blackdot"]),
            "judged_normal_dispatches": {
                "observation": (
                    "黑点判正常派次计数（分型件 blackdot_dispatch 口径："
                    "notes 判黑点正常且该派次零黑点词旗标）=%d/24——"
                    "applied/prep1-top-i3 两板（notes 自述黑色钻孔判安装"
                    "孔类正常特征、机械实测 notes 含黑点词且零黑点词旗标）；"
                    "对照 r15=3/r16=2/r18=2/r19=3/r20=4/r22=4/r23=2。"
                    % len(judged_normal)),
                "count": len(judged_normal),
                "sources": sorted(judged_normal),
                "r15_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r15"],
                "r16_registered": BLACKDOT_JUDGED_NORMAL_PRIOR["r16"],
                "r18_registered": 2,
                "r19_registered": 3,
                "r20_registered": 4,
                "r22_registered": 4,
                "r23_registered": 2,
                "notes_hit_rows": bd_disp_rows,
            },
            "rubric_families": {
                "role": ("contact/黑点族计数口径（分型件 rubric 机械套用；"
                         "关键词表/五类定义/优先级从 abstain-typology-"
                         "r13-r16.json 装载，脚本不另嵌词表；blackdot "
                         "对象判定先于 contact 组合；先回放 r13–r16 链"
                         "一致才可应用）"),
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
                "note": ("r24 全部 %d 条弃权旗逐旗分类入账（rows）——"
                         "existence_blackdot %d/contact %d/existence_other "
                         "%d/semantic_confusion %d/other %d；M3 槽位="
                         "existence_blackdot=%d（对照 r19=4/r22=4/r23=8）"
                         % (sum(family_counts.values()),
                            family_counts["existence_blackdot"],
                            family_counts["contact"],
                            family_counts["existence_other"],
                            family_counts["semantic_confusion"],
                            family_counts["other"],
                            family_counts["existence_blackdot"])),
            },
            "status": ("黑点族弃权 28（六实例逐实例分旗、远高于五基线）+"
                       "黑点转非弃权旗 16+判正常派次 2（如实单列、不凌驾"
                       "字母裁决）"),
        },
        "experiment_comparison_ledger": {
            "role": ("实验对照账（per axis-experiment-plan-r17-r20 "
                     "benefit_metrics 口径定义、按 n=6 扩写；五键如实入账"
                     "——五键由后续 dev-record 包转记入 round24-dev-"
                     "record；全部=24 派次全口径（非代表配置子集）；"
                     "M4 跨口径粒度差异=描述性声明（12 格 vs r16–r23 "
                     "逐实例两板合计口径、prep-record M4_operationalization_"
                     "note 延续）；对照账八行并列=r16 基线/r17 轴1/r18 "
                     "轴2/r19 轴3/r20（破坏轮登记行）/r22（登记行）/r23"
                     "（登记行）/r24 本轮）"),
            "metric_definitions": {
                k: prep_doc["measurement_design"]["m_tuple_definitions"][k]
                for k in ("M1_top_aggregate_abstain_rate",
                          "M2_bottom_aggregate_abstain_rate",
                          "M3_blackdot_abstain_flags_rubric",
                          "M4_top_per_instance_rate_range",
                          "M4_operationalization_note",
                          "split_half_M1_diff")},
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
            "r17_axis1_row": dict(R17_ROW_REGISTERED),
            "r17_row_source": ("round18-dev-record axis_experiment_ledger."
                               "cross_round_status.measured_rows.r17_axis1"
                               " 登记值（历史行装载；与 dev-r18 在案核对"
                               "一致）"),
            "r18_axis2_row": r18_row,
            "r19_axis3_row": r19_row,
            "r20_combo_registered_row": dict(R20_ROW_REGISTERED),
            "r22_repeat_registered_row": dict(R22_ROW_REGISTERED),
            "r23_repeat_registered_row": dict(r23_row_live),
            "r24_measured": {
                "M1": top_rate,
                "M1_arithmetic": f"{abst_top}/{flags_top}",
                "M2": bot_rate,
                "M2_arithmetic": f"{abst_bot}/{flags_bot}",
                "M3": family_counts["existence_blackdot"],
                "M4": m4,
                "M4_12_cells": m4_cells,
                "split_half_M1_diff": split_half,
                "split_half_halves": {k: dict(v) for k, v in sh.items()},
                "contact_family_abstain_flags_rubric": contact,
                "contact_family_by_view": contact_by_view,
                "existence_other_family": family_counts["existence_other"],
            },
            "family_counts_vs_r19_r22_r23": {
                "contact": {
                    "r19_registered": 4, "r22_registered": 2,
                    "r23_registered": 8,
                    "r24_measured": contact},
                "existence_blackdot": {
                    "r19_registered": 4, "r22_registered": 4,
                    "r23_registered": 8,
                    "r24_measured":
                        family_counts["existence_blackdot"]},
                "existence_other": {
                    "r19_registered": 14, "r22_registered": 12,
                    "r23_registered": 7,
                    "r24_measured": family_counts["existence_other"]},
            },
            "ranking_by_comparison_rule": {
                "rule": axis_plan["comparison_rule"]["ordering"],
                "eligibility_gate": axis_plan["comparison_rule"][
                    "eligibility_gate"],
                "rows_registered": ledger_rows,
                "eligible_rows": sorted(eligible_rows),
                "ranking_order_best_first": ranking_order,
                "r24_eligibility": bool(guards_ok),
                "r24_eligibility_note": (
                    "资格门=G1/G2 均满足；r24 G1 实测 %s、G2 guard_ok=%s"
                    "（几何门出局条目 %d=0≤r19 的 0=维持）→%s排序"
                    % (list(by_instance.values()), guard_ok,
                       len(geo_r24),
                       "参与" if guards_ok else "不参与")),
                "r23_eligibility": False,
                "r23_exclusion_reason": (
                    "资格门=G1/G2 均满足；r23 G2 破坏（几何门出局条目 1>0，"
                    "run-r23 在案）→不参与排序（r23 行仅如实入账不占排序"
                    "位；r23 字母=confounded 维持不改写）"),
                "r22_eligibility": False,
                "r22_exclusion_reason": (
                    "资格门=G1/G2 均满足；r22 G2 破坏（几何门出局条目 "
                    "r19=0→r22=2，run-r22 在案）→不参与排序"),
                "r20_eligibility": False,
                "r20_exclusion_reason": (
                    "资格门=G1/G2 均满足；r20 G1 破坏（bottom courtyard "
                    "非弃权 2/0/0，run-r20 在案）→不参与排序"),
                "note": ("资格门：r17/r18/r19 均 G1/G2 满足（在案）→入"
                         "排序；r16=基线参照行（非轴配置）；r20/r22/r23="
                         "守门破坏不入排序（在案）；r24 资格按 G1/G2 实测"
                         "判定（G1 维持+G2=0→参与）；当前排序=eligible 行"
                         "实测 M 元组升序——如实登记、不预写后续决策"),
            },
            "significant_benefit_vs_r16": {
                "definition": axis_plan["comparison_rule"][
                    "significant_benefit_definition"],
                "r24_m1_absolute_drop": m1_drop_r24,
                "met": m1_drop_r24 >= 0.10,
                "r18_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r18_m1),
                "r19_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r19_m1),
                "r22_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"]
                    - r22_row_live["M1"]),
                "r23_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"]
                    - r23_row_live["M1"]),
                "note": ("r24 M1 绝对降幅 %s ≥0.10=显著收益定义在描述层"
                         "命中（r18 降幅 %s、r19 降幅 %s、r22 降幅 %s、"
                         "r23 降幅 %s 亦 ≥0.10）；字母裁决与实验账分列互"
                         "不改写"
                         % (m1_drop_r24,
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r18_m1),
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r19_m1),
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r22_row_live["M1"]),
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r23_row_live["M1"]))),
            },
            "attribution_conclusion": attribution_conclusion,
            "direction_vs_r16": {
                "M1": ("down（%s→%s，改善方向）"
                       % (rb["M1_top_aggregate_abstain_rate"], top_rate)),
                "M2": ("down（%s→%s，改善方向）"
                       % (rb["M2_bottom_aggregate_abstain_rate"],
                          bot_rate)),
                "M3": ("up（%d→%d，黑点族弃权大升[n=6 扩容+实例异质性；"
                       "跨口径对照如实声明]）"
                       % (rb["M3_blackdot_abstain_flags_rubric"],
                          family_counts["existence_blackdot"])),
                "M4": ("%s→%s（走阔；跨口径粒度差异=描述性声明）"
                       % (rb["M4_top_per_instance_rate_range"], m4)),
                "contact": ("down（10→%d）" % contact),
            },
            "confounder_note": axis_plan["baselines_registered"][
                "drift_reference_note"],
            "status": ("八行如实并列（M1/M2 降、M3 升、M4 走阔[12 格口径]"
                       "）；本轮字母裁决=not_instance_dominated（M4 条件"
                       "超出）；development 域只描述不断言"),
        },
        "reader_tool_evidence": {
            "role": ("v1.2 工具规约合规证据（24/24 派次；逐派次自述句"
                     "程序确定性提取[句子级、零改写]；冻结原文哈希锚承载）"),
            "count": len(tool_evidence_rows),
            "rows": tool_evidence_rows,
            "no_cross_inference_sources": no_cross_sources,
            "evidence_check": ("24/24 派次自述句提取成功（substring "
                               "fail-closed 校验通过）"),
        },
    }
    metric_lesson_continuation = {
        "role": ("度量设计教训延续（如实，供未来预注册参考；本轮不追溯"
                 "适用；per r24-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r24 三支判据=G1 守门维持+M4(n=6)（12 格极差）<0.261904+"
            "split_half_M1_diff≤0.09064（双条件）→instance_dominated；"
            "至少一条件超出→not_instance_dominated（6 位定点整数比较、"
            "字母裁决无浮点路径）；G2=观察项非字母支（G2>0→资格门剔除）；"
            "M4 跨口径粒度差异（12 格 vs r16–r23 逐实例两板合计口径）="
            "描述性声明、阈值 0.261904=r16 历史口径在案值原样引用不改写；"
            "split_half=本轮首次启用的实例群内部一致性度量（阈值 0.09064="
            "r15→r16 纯重抽漂移在案参照）；M3 计数口径=分型件 rubric 机械"
            "套用（关键词表/优先级 fail-closed 装载+对 r13–r16 132 条弃权"
            "旗重放对拍逐一相等后套用 r24，对拍基期=r13–r16（8/15/5/10）"
            "不变）；部分重复≠独立重复（同域同编排实例池、验证力度如实"
            "声明；本轮 12 实例中每实例两派次=同实例重复非独立重复）；"
            "跨轮实例群漂移混杂照旧声明——本轮实例群重抽+扩容=实验操作"
            "本身（实例群轴直接操纵）；M1 分母（top 旗数）随实例群规模"
            "变化（35→39→22→41→33→105），弃权率比较含分母效应、构成分解"
            "（弃权分型+rubric 族+援引分记+黑点转非弃权旗）单列补足"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一迭代候选方向（如实登记，不构成本轮判据"
                   "输入）：由后续 round24-dev-record 包按授权链转记；"
                   "不得回溯改判既往轮次（r8–r23 字母裁决维持不变）"),
    }
    # 分层基线（逐实例弃权率，live 重放/装载；不手工抄数；r17 行=
    # dev-r18 axis_experiment_ledger 实测装载交叉核对）
    dev18 = _json_load(REL_DEV_R18)
    measured_rows_r17 = dev18["axis_experiment_ledger"][
        "cross_round_status"]["measured_rows"]["r17_axis1"]
    if measured_rows_r17 != R17_ROW_REGISTERED:
        _fail("dev-r18 r17_axis1 行与登记不符")
    r16_bottom_rates = {n: run_r16["instances"][n]["combined"][
        "abstain_rate"] for n in ("bottom-i1", "bottom-i2", "bottom-i3")}
    r19_top_rates = {n: run_r19["instances"][n]["combined"][
        "abstain_rate"] for n in ("top-i1", "top-i2", "top-i3")}
    r22_top_rates = run_r22["view_layer"]["top"]["abstain_rate"][
        "by_instance"]
    r23_top_rates = run_r23["view_layer"]["top"]["abstain_rate"][
        "by_instance"]
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R24,
                                "sha256": _sha(REL_PREP_R24)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "instance_dominated": adj["instance_dominated"],
            "not_instance_dominated": adj["not_instance_dominated"],
            "guard_interrupted": adj["guard_interrupted"],
            "letter_branch_map": adj["letter_branch_map"],
            "fixed_point_comparison_note": adj[
                "fixed_point_comparison_note"],
            "g2_observation_separate": adj["g2_observation_separate"],
            "primary_channel": prep_doc["attribution_plan"][
                "primary_channel"],
            "guard_channel": prep_doc["attribution_plan"]["guard_channel"],
            "descriptive_boundary_note": adj["descriptive_boundary_note"],
            "metric_lesson_separate": adj["metric_lesson_separate"],
            "mechanism_observation_separate":
                adj["mechanism_observation_separate"],
            "three_way_bookkeeping": adj["three_way_bookkeeping"],
            "user_directive_note": prep_doc["user_directive_note"],
        },
        "primary_channel": prep_doc["attribution_plan"]["primary_channel"],
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界（r24-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮实例群扩容归因（M4(n=6)"
            "+split_half_M1_diff 双判据+G1 守门），与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "contact_family_abstain_flags_rubric_r24": contact,
            "contact_arithmetic_note": (
                "contact = contact 族弃权旗数（分型件 rubric 口径）= %d"
                "（r24 全部 %d 条弃权旗逐旗 rubric 分类中 contact 计数；"
                "关键词表/优先级=abstain-typology-r13-r16.json 装载；"
                "r13–r16 132 条弃权旗重放对拍逐一相等=口径忠实性证明；"
                "分视角 top %d+bottom %d）"
                % (contact, sum(family_counts.values()),
                   contact_by_view["top"], contact_by_view["bottom"])),
            "top_abstain_flags_r24": flags_top,
            "top_abstain_count_r24": abst_top,
            "top_abstain_rate_r24": top_rate,
            "top_abstain_rate_r24_arithmetic":
                f"M1 = top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（判据首键；24 派次全口径 n=6）",
            "top_abstain_rate_r16_baseline_live":
                f"{base16_ab}/{base16_fl}",
            "top_abstain_rate_r16_baseline_value":
                cal._ratio(base16_ab, base16_fl),
            "m4_top_rate_range_r24": m4,
            "m4_arithmetic_note": (
                "M4(n=6) = top 12 个（态,实例）格弃权率极差 = %s（6 位定点 "
                "%d=max %d−min %d；max 格=%s、min 格=%s；"
                "M4_operationalization_note 口径：先 6 位定点取率再取差；"
                "与 r16–r23 逐实例两板合计口径的粒度差异=描述性声明）"
                % (m4, m4_6dp, max(cell_vals), min(cell_vals),
                   m4_max_cell["cell"], m4_min_cell["cell"])),
            "split_half_M1_diff_r24": split_half,
            "split_half_arithmetic_note": (
                "split_half_M1_diff = |M1(i1–i3)−M1(i4–i6)| = %s（6 位定点 "
                "|%d−%d|=%d；A=31/57、B=27/48；阈值 %d=0.09064 的 6 位定点"
                "、双视图=两态合并聚合；本轮首次启用）"
                % (split_half, sh["A_i1_i3"]["rate_6dp"],
                   sh["B_i4_i6"]["rate_6dp"], split_half_6dp,
                   SPLIT_HALF_THRESHOLD_6DP)),
            "crit_instance_dominated": crit_instance_dominated,
            "crit_not_instance_dominated": crit_not_instance_dominated,
            "crit_guard_interrupted": crit_guard_interrupted,
            "g2_rejected_entries_zero": g2_zero,
            "r24_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                "M3": family_counts["existence_blackdot"],
                                "M4": m4,
                                "split_half_M1_diff": split_half},
            "comparison_rows_live": {
                "r16_baseline": ledger_rows["r16_baseline"],
                "r19_axis3": r19_row,
                "r22_repeat_live": r22_row_live,
                "r23_repeat_live": r23_row_live},
            "m4_threshold_6dp": M4_THRESHOLD_6DP,
            "split_half_threshold_6dp": SPLIT_HALF_THRESHOLD_6DP,
            "contact_r16_baseline_registered": CONTACT_CHAIN_PRIOR["r16"],
            "contact_r16_baseline_live_replay":
                replay_proof["contact_counts"],
            "baseline_replay_note": (
                "M1/M2 基线=同一聚合逻辑对 calibration-run-r16.json 内嵌"
                "实例记录（states 层 reader_flags+compare_v3.abstain）双侧"
                "复算，不手工抄数；r19/r22/r23 对照行=各自 run 内嵌实例"
                "记录 live 复算+prep-record 冻结锚交叉核对；均与在案登记值"
                "（axis-plan baselines_registered.r16_baseline.M1=0.771429、"
                "prep-record run_r22/run_r23_metric_anchor 冻结值）交叉"
                "核对（fail-closed，见 baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r24":
                    by_instance,
                "bottom_courtyard_flags_total_r24": bot_courtyard_flags,
                "bottom_abstain_flags_r24": flags_bot,
                "bottom_abstain_count_r24": abst_bot,
                "bottom_abstain_rate_r24": bot_rate,
                "bottom_abstain_rate_r24_arithmetic":
                    f"M2 = bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                    f"{bot_rate}"
                    f"（对照 r16 基线 12/14=0.857143、r18 13/19=0.684211、"
                    f"r19 4/7=0.571429、r20 4/14=0.285714、r22 2/10=0.2、"
                    f"r23 8/14=0.571429；mechanism_observation_separate "
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
            "bottom_courtyard_detail_r24": [
                {"instance": row["instance"],
                 "courtyard_non_abstain_count":
                     by_instance[row["instance"]],
                 "note": row["note"]}
                for row in SIDE_OBS_REGISTERED],
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
                "r18_row_registered": R18_ROW_REGISTERED,
                "r18_row_live": r18_row,
                "r19_row_registered": R19_ROW_REGISTERED,
                "r19_row_live": r19_row,
                "r20_row_registered": R20_ROW_REGISTERED,
                "r20_row_live": r20_row_live,
                "r22_row_registered": R22_ROW_REGISTERED,
                "r22_row_live": r22_row_live,
                "r23_row_registered": R23_ROW_REGISTERED,
                "r23_row_live": r23_row_live,
                "axis_plan_r16_baseline_M1_M2_M3_M4": [
                    rb["M1_top_aggregate_abstain_rate"],
                    rb["M2_bottom_aggregate_abstain_rate"],
                    rb["M3_blackdot_abstain_flags_rubric"],
                    rb["M4_top_per_instance_rate_range"]],
                "note": ("基线数字与 run-r16/run-r18/run-r19/run-r20/"
                         "run-r22/run-r23 内嵌输入重放/分型件实测装载交叉"
                         "核对一致（fail-closed：live 与登记不符即 FAIL）；"
                         "registered=axis-plan 在案登记/prep-record 冻结锚/"
                         "判据原文冻结值，live=本轮从 run-doc/分型件重放"
                         "装载实测"),
            },
            "guard_channel": {
                "metric": prep_doc["attribution_plan"]["guard_channel"],
                "observation": (
                    "G1=六 bottom 实例 courtyard 非弃权全 0 维持（实测 %s，"
                    "r16 基线 live 重放 0/0/0；r20 破坏 2/0/0 在案=分岔"
                    "记录）=%s；G2=几何门面积比出局条目数（观察项非字母"
                    "支）：R19=%d→R22=%d→R23=%d→R24=%d（=0=%s）；axis-plan "
                    "语义 guard_ok（不升）=%s"
                    % (list(by_instance.values()),
                       "满足" if g1_ok else "破坏",
                       len(geo_r19), len(geo_r22), len(geo_r23),
                       len(geo_r24), g2_zero, guard_ok)),
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r22": len(geo_r22),
                "g2_geometry_gate_r23": len(geo_r23),
                "g2_geometry_gate_r24": len(geo_r24),
                "g2_rejected_entries_zero": g2_zero,
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "note": ("守门通道按 r24-prep-record attribution_plan."
                         "guard_channel 独立复核；G2=实测观察项非字母支"
                         "（本轮实测 0 条=资格门满足）；G1 维持=三支判据"
                         "前提"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r23 run-record courtyard_tracking 在案先例延续）——"
                "实测见 courtyard_tracking 节"),
            "aggregate_context": {
                "abstain_rate_r9":
                    run_r9["aggregation"]["abstain_rate_total"],
                "abstain_rate_r10":
                    run_r10["aggregation"]["abstain_rate_total"],
                "abstain_rate_r16_representative":
                    run_r16["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r19_representative":
                    run_r19["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r22_representative":
                    run_r22["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r23_representative":
                    run_r23["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r24_representative_note": (
                    "代表配置聚合弃权率见 aggregation_representative."
                    "abstain_rate_total（本轮聚合口径按 measurement_design "
                    "五条预注册执行[下中位代表配置]、代表配置/逐实例/双"
                    "口径分列）"),
                "note": (
                    "跨轮聚合弃权率（口径分列如实）：r9 0.727273（8/11，"
                    "全旗标）→r10 0.285714（4/14，全旗标）→r16 0.764706"
                    "（13/17，代表配置）→r19 0.428571（6/14，代表配置）→"
                    "r22 0.466667（7/15，代表配置）→r23 0.125（2/16，代表"
                    "配置）→r24 见代表配置分列；归因三支判据与门各自独立"
                    "计算、互不凌驾（prep-record descriptive_boundary_note "
                    "原文语义）——门联合评价与字母裁决分列不合并"),
            },
            "r24_total_flags_note": (
                "十二实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/双口径/"
                "代表配置，全旗标合计非主通道；判据键 M1=top 全旗聚合弃权"
                "率 %d/%d=%s、M2=bottom 同口径 %d/%d=%s、M3=黑点族弃权旗"
                "数 %d、M4(n=6)=12 格极差 %s、split_half_M1_diff=%s 各按键"
                "位入账、各自单列）"
                % (n_total_all,
                   (flags_top - abst_top) + (flags_bot - abst_bot),
                   abst_top + abst_bot,
                   cal._ratio(abst_top + abst_bot, n_total_all),
                   abst_top, flags_top, top_rate,
                   abst_bot, flags_bot, bot_rate,
                   family_counts["existence_blackdot"], m4, split_half)),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"instance_dominated=「{adj['instance_dominated'][:60]}…」；"
            f"not_instance_dominated=「{adj['not_instance_dominated'][:60]}"
            f"…」；guard_interrupted=「{adj['guard_interrupted'][:60]}…」"
            "（r24-prep-record.json hypothesis_test.adjudication 判据原文"
            "全文见 preregistered_criteria_quote，轮后如实执行；结果无论"
            "方向均如实入账"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r24": {
            "role": ("r12 假设通道被动追踪（round13–round23-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r24": reroute_rows,
            "reroute_total_r24": len(reroute_rows),
            "reroute_by_instance_r24": {
                n: sum(1 for d in instances[n]["per_flag_gt_detail"]
                       if d["category"] == "suspicious_reroute")
                for n in INSTANCE_ORDER},
            "production_chain": dict(
                REROUTE_CHAIN_PRIOR,
                r24=len(reroute_rows)),
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径，旗级 location_evidence "
                "子串命中）：r10=2→r11=1→r12=0→r13 被动追踪=1→r14=0→"
                "r15 机械命中=1（否定式援引）→r16=0→r17=0→r18=0→r19=0→"
                "r20=0→r22=0→r23 机械命中=2（均为否定式援引「不适用常规"
                "等长布线候选解释」）→r24 机械命中=%d（6 条 reroute 旗级"
                "「等长」/「蛇形」子串零命中）——不构成 r24 判据输入"
                "（两判据分列互不凌驾）" % sum(
                    1 for r in reroute_rows if r["detected_substring_hits"])),
        },
        "stratified_observation": {
            "top": {"r16_by_instance_live": r16_top_rates,
                    "r16_range_live": AXIS_R16_M4_TOP_RANGE,
                    "r19_by_instance_live": r19_top_rates,
                    "r22_by_instance_live": r22_top_rates,
                    "r23_by_instance_live": r23_top_rates,
                    "r24_by_instance": top_rates,
                    "r24_range_per_instance": top_range,
                    "direction": (
                        "r16 三实例 %s（轮内极差 %s）→r19 %s→r22 %s→r23 "
                        "%s→r24 六实例 %s（逐实例两板合计口径极差 %s；"
                        "12 格口径极差[M4(n=6)]=%s）——实例群扩容轮、实例"
                        "层方向性对照（聚合 M1 %d/%d=%s vs r16 基线 27/35="
                        "0.771429、r19 18/39=0.461538、r22 16/41=0.390244、"
                        "r23 16/33=0.484848；轮内实例差异=本轮归因测量对象）"
                        % ("/".join(f"{r16_top_rates[f'top-{k}']}"
                                    for k in ("i1", "i2", "i3")),
                           AXIS_R16_M4_TOP_RANGE,
                           "/".join(str(v) for v in r19_top_rates.values()),
                           "/".join(str(v) for v in r22_top_rates.values()),
                           "/".join(str(v) for v in r23_top_rates.values()),
                           "/".join(f"{n}={top_rates[n]}"
                                    for n in top_names),
                           top_range, m4,
                           abst_top, flags_top, top_rate))},
            "bottom": {"r16_by_instance_live": r16_bottom_rates,
                       "r24_by_instance": bottom_rates,
                       "r24_range": bottom_range,
                       "direction": (
                           "bottom 六实例 %s（极差 %s；i1/i2 全非弃权、"
                           "i3–i6 全弃权）——bottom 聚合 M2 %d/%d=%s vs r16 "
                           "的 12/14=0.857143、r19 4/7=0.571429、r20 4/14="
                           "0.285714、r22 2/10=0.2、r23 8/14=0.571429"
                           "（侧观察如实单列）"
                           % ("/".join(f"{n}={bottom_rates[n]}"
                                       for n in bot_names),
                              bottom_range,
                              abst_bot, flags_bot, bot_rate))},
            "confounder_note": (
                "跨轮 reader 实例不同（实例群重抽=轮际固有混杂；本轮扩容"
                "=实验操作本身）+轮内实例差异=本轮归因主通道的测量对象；"
                "v1.2 工具规约把工具行为钉住（24/24 自述「未读取盘上任何"
                "其他文件」）但判读实例仍为不同实例；每实例两派次=同实例"
                "重复非独立重复（部分重复≠独立重复、验证力度如实声明）；"
                "development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def r16_top_abstain_aggregate_live(run_r16: dict) -> tuple:
    """r16 top 全旗聚合弃权重放实测（M1 基线=0.771429；同一聚合逻辑对
    run-r16 内嵌实例记录双侧复算、不手工抄数；与登记交叉核对）。"""
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


def build_courtyard_tracking(instances: dict, run_r16: dict,
                             run_r19: dict, run_r22: dict,
                             run_r23: dict) -> dict:
    """courtyard 被动追踪（r11–r23 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r24 courtyard 类旗标与命中如实入账
    ——top 非弃权 6 条（top-i4 两板+top-i5 两板各 2/4 贴近报告）+top 弃权
    1 条（top-i4 prep1 R24T-021）；bottom 零 courtyard 类旗标、零命中）。"""
    note_source = {
        "path_rel": REL_PREP_R24, "sha256": _sha(REL_PREP_R24),
        "quote": None,
        "note": ("r24-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r23 "
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
    prior = run_r23["courtyard_tracking"]
    top_abstain_cnt = sum(1 for r in abstain_rows
                          if r["instance"].startswith("top"))
    bot_abstain_cnt = sum(1 for r in abstain_rows
                          if r["instance"].startswith("bottom"))
    bot_flags_total = sum(instances[n]["combined"]["flag_count"]
                          for n in INSTANCE_ORDER
                          if n.startswith("bottom"))
    bot_abstain_total = sum(instances[n]["combined"]["abstain_count"]
                            for n in INSTANCE_ORDER
                            if n.startswith("bottom"))
    bot_nonabstain_total = bot_flags_total - bot_abstain_total
    r23_prior = run_r23["courtyard_tracking"]
    return {
        "note_source": note_source,
        "declaration": ("被动追踪（run-record 链先例延续）：如实记录 "
                        "courtyard 类旗标匹配表现"
                        "（零阈值改动、零期望、不得为提高命中调阈值）"),
        "r24_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（top 1 条=top-i4 prep1 R24T-021；bottom 六"
                             "实例零 courtyard 类旗标；非弃权 6 条全部 "
                             "top（top-i4 两板 2+top-i5 两板 4=贴近报告）；"
                             "对照 r23 的 top 非弃权 5+弃权 4/bottom 0、"
                             "r22 的 top 非弃权 6+弃权 2/bottom 0、r19 的 "
                             "top 4+bottom 0 全弃权、r20 的 bottom 非弃权 "
                             "2（G1 破坏在案），如实登记）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r24": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r23": r23_prior["courtyard_matches_r23"],
        "courtyard_matches_r23_detail": (
            "R23 非弃权 courtyard 5 条（top-i2 两板 4+top-i3 prep1 1）中 "
            "1 条命中（prep1-top-i3 R23T-002↔GT-REVC-P1-R4J3；run-r23 在"
            "案）；courtyard 类弃权旗=top 4+bottom 0（run-r23 在案）"),
        "courtyard_matches_r22_registered": 0,
        "courtyard_matches_r22_detail": (
            "R22 非弃权 courtyard 6 条零命中（run-r22 在案）；courtyard "
            "类弃权旗=top 2+bottom 0（run-r22 在案）"),
        "courtyard_matches_r20_registered": 0,
        "courtyard_matches_r20_detail": (
            "R20 非弃权 courtyard 2 条（bottom-i1 两板，G1 守门字面破坏的"
            "直接构成）零命中（run-r20 在案）"),
        "courtyard_matches_r19": run_r19["courtyard_tracking"][
            "courtyard_matches_r19"],
        "courtyard_matches_r16": run_r16["courtyard_tracking"][
            "courtyard_matches_r16"],
        "courtyard_matches_r16_detail": (
            "R16 非弃权 courtyard 1 条（top-i2 R16T-001↔GT-REVC-AP-6-"
            "R2LED2）命中 1（run-r16 在案）；courtyard 类弃权旗=top 12+"
            "bottom 2（run-r16 在案）"),
        "same_domain_note": (
            "r11 三条 courtyard 命中与 r8 R8T-004、r10 R10T-011 同域"
            "（Y1/R4J3 类 courtyard 密集区）——r12–r15 连续零再现、"
            "r16 回升 1 条、r17–r22 零命中、r23 回升 1 条、r24 零命中="
            "命中链 r16=1→r17=0→r18=0→r19=0→r20=0→r22=0→r23=1→r24=%d；"
            "GT/阈值零改动"
            % sum(r["matches"] for r in non_abstain_rows)),
        "bottom_observation": {
            "fact": ("R24 bottom %d 旗（bottom-i1 4+bottom-i2 4+bottom-i3 "
                     "4+bottom-i4 6+bottom-i5 4+bottom-i6 4）=非弃权 %d"
                     "（bottom-i1/i2 各两板 4=黑色圆点/圆孔孤立或接触路径"
                     "负责任报告）+弃权 %d（bottom-i3–i6 全弃权=黑色圆点/"
                     "圆孔性质存在性弃权）：零匹配属结构性（GT 13 条全部 "
                     "side=top，bottom GT 无源在案 gt-audit-r1⇒bottom "
                     "旗标与 GT 匹配应为空，如实）；courtyard 类旗标=0"
                     "（六实例零 courtyard 类路径；r20 非弃权 2 条=G1 "
                     "破坏/r22–r24 零旗标=G1 维持，逐轮构成如实分列）；"
                     "弃权构成见 reader.flag_count.by_category；本轮零旗"
                     "标格=0（24 格全部≥1 旗、item 5 零分母→None 口径未"
                     "触发）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r24 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    # 跨板编号连续性（12/12 断言）
    if not all(instances[n]["flag_id_cross_board_continuous"]
               for n in INSTANCE_ORDER):
        _fail("实例跨板编号连续性实测与声明不符")
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

    # 代表配置（measurement_design item 4）：每视角 flag_count 升序第 3
    # 序位（下中位）实例
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
    run_r22 = _json_load(REL_RUN_R22P)
    run_r23 = _json_load(REL_RUN_R23P)
    axis_plan = _json_load(REL_AXIS_PLAN)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, run_r16, run_r17, run_r18, run_r19, run_r20,
        run_r22, run_r23, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_continuation(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, run_r12,
                                run_r13, run_r14, run_r15, run_r16,
                                run_r17, run_r18, run_r19, run_r20,
                                run_r22, run_r23, axis_plan,
                                instances, view_layer, attribution,
                                raw_texts, parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r16, run_r19,
                                         run_r22, run_r23)

    prep_r24 = _json_load(REL_PREP_R24)
    serial = list(RAW_FILES)
    by_view = {"top": 0, "bottom": 0}
    abst_by_view = {"top": 0, "bottom": 0}
    by_state = {"applied": 0, "prep1": 0}
    abst_by_state = {"applied": 0, "prep1": 0}
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
            by_state[st] += len(blk["reader_flags"])
            abst_by_state[st] += blk["compare_v3"]["abstain"][
                "abstain_count"]
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
    # （视角,态）四聚合与逐实例分解交叉核对（by_view/by_state 双分解）
    n_total = sum(instances[n]["combined"]["flag_count"]
                  for n in INSTANCE_ORDER)
    if sum(by_view.values()) != n_total \
            or sum(by_state.values()) != n_total:
        _fail("by_view/by_state 合计与全旗标总数不符")
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
            "by_state": by_state,
            "abstain_by_state": abst_by_state,
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
            "五键投影（process-v1 §2 步骤3）；R24 reroute 类六旗 "
            "location_evidence 逐字在案（reroute_continuation_r24 程序"
            "提取登记；「等长」/「蛇形」子串零命中）；"
            "R24 top 弃权旗 58 条逐旗机械主出口分型在案（abstain_typology："
            "接触性 26+存在性 30+层归属其他 2）；"
            "R24 全部 76 条弃权旗逐旗 rubric 族分类在案（black_dot_"
            "tracking.rubric_families）；(iii-a) 旗级援引 7 旗逐旗摘录在案+"
            "§5B/(iii-a)/§6 援引计数分列在案（旗级 0/7/0、notes 级 "
            "§5B 0/24+(iii-a) 8/24+§6 20/24；criterion_citation_"
            "observation）；G2 出局条目=0（空摘录如实登记，g2_rejected_"
            "entries_r24）；工具规约合规 24/24 派次自述句程序提取在案"
            "（reader_tool_evidence）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "zero_flag_parts": {
            "parts": zero_flag_parts,
            "note": ("本轮 0 格零旗标（24 格全部≥1 旗；对照 r22 的 2 格"
                     "零旗标=bottom-i1 两板先例）——"
                     "measurement_design item 5 零分母→None 口径本轮"
                     "未触发（先例条文照登记、None 分支代码在案）；"
                     "视角层 top/bottom 六实例弃权率全部有定义、中位数="
                     "第 3/4 序位均值（n=6）"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PROTOCOL_V2,
         "role": "evaluation_protocol_v2_holdout_frozen_not_activated",
         "sha256": _sha(REL_PROTOCOL_V2)},
        {"path_rel": REL_PREP_R24, "role": "r24_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R24)},
        {"path_rel": REL_PREP_R23, "role": "r23_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R23)},
        {"path_rel": REL_PREP_R22, "role": "r22_prep_record_prior_chain",
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
        {"path_rel": REL_DEV_R22,
         "role": "r22_dev_record_drift_anchor",
         "sha256": _sha(REL_DEV_R22)},
        {"path_rel": REL_DEV_R23,
         "role": "r23_dev_record_candidate_b_authorization",
         "sha256": _sha(REL_DEV_R23)},
        {"path_rel": REL_RUN_R22P,
         "role": "r22_run_record_comparison_row_and_g2_reference",
         "sha256": _sha(REL_RUN_R22P)},
        {"path_rel": REL_RUN_R23P,
         "role": "r23_run_record_comparison_row_and_g2_reference",
         "sha256": _sha(REL_RUN_R23P)},
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
         "role": "observation_guidance_r19_transform_base_historical",
         "sha256": _sha(REL_GUIDANCE_R19)},
        {"path_rel": REL_GUIDANCE_R23,
         "role": "observation_guidance_r23_active_byte_reuse",
         "sha256": _sha(REL_GUIDANCE_R23)},
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
        "kind": "tl2_calibration_run_r24",
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
            "axis_id": ("instance_sampling_scale"
                        "（唯一实验变量=实例数 n：每视图 3→6[多实例协议 "
                        "v1.3]；指引字节复用/渲染/GT/阈值/协议正文零变更）"),
            "nature": INSTRUMENT_NATURE,
            "note": prep_r24["instrument_change"]["note"],
            "declaration": prep_r24["instrument_change"]["declaration"],
            "renders_registered": [
                {"state_side": e["state_side"], "path_rel": e["path_rel"],
                 "sha256_measured": e["sha256_measured"],
                 "sha256_witness_registered":
                     e["sha256_witness_registered"],
                 "witness_record": e["witness_record"],
                 "match": e["match"]}
                for e in prep_r24["instrument_change"]["renders"]],
            "components": [
                "渲染零变更=renders-r14b 四图字节复用（与 r14–r23 "
                "盲读同一批文件；no_instrument_change=true）"],
            "unchanged_components": list(prep_r24["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v.get("attribution_channel"),
                 "instrument_change": v["instrument_change"]}
                for v in prep_r24["changed_variables"]],
            "changed_variables_note": (
                "r24-prep-record changed_variables=[instance-count-n3-to-"
                "n6-v1.3]（恰 1 条=实例数 n 扩容、实例群抽样规模轴；指引/"
                "渲染/GT/阈值/协议正文零变更）"),
            "protocol_amendment": {
                "amendment_version": prep_r24["protocol_amendment"][
                    "version"],
                "amendment_mode": ("v1.3 n 扩容附录（prep-record 内登记、"
                                   "不新建协议文件；判读语义/判据/GT/门零"
                                   "变更）"),
                "v1_file_preserved": prep_r24["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧唯一变更=v1.3 n 扩容附录（每视图实例数 "
                         "3→6、24 派次、两波次串行、union≥1/6 与 agreement"
                         "≥4/6 与代表配置下中位序位的 n=6 推广）；v1.2 纯 "
                         "Read 直读规约自 r12 起随派发指令生效、本轮照抄"
                         "沿用；v1 文件零字节保留、不回写；"
                         "evaluation-protocol-v2=holdout 协议冻结件（s79 "
                         "登记在案）本轮不启用——v2 生效≠holdout 启动"),
            },
            "attribution_note": prep_r24["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R24, "sha256": _sha(REL_PREP_R24)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": ("v1/v1.1/v1.2 继承不改+v1.3 n "
                                           "扩容附录（prep-record 内登记；"
                                           "v1 文件零字节保留，见 "
                                           "protocol_amendment）")},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；本轮指引=observation-guidance-r23.md 字节复用"
            "（零改写），其 §6 示例旗 ID 前缀 R23T-/R23B- 为落盘原文"
            "（恰 4+1 处）、派发层覆盖为 R24T/R24B=前缀差异登记在案"
            "（r16 先例：r15 指引+R16T 前缀、r22 先例：r19 指引+R22T/"
            "R22B；对照 r23：指引落盘新件、派发前缀与指引一致）；"
            "实例间编号独立（r24 实测 12/12 有旗实例跨板连续、零零旗格；"
            "轮内同名旗号跨实例出现[如 R24T-015 见于 top-i2 与 top-i6]="
            "实例间编号独立语义的直接观测），见 "
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
                     "全部关闭（r8 轮同日审计，结论 r9–r23 延续引用）；该"
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
                    "r13 指引 §4（本轮指引=observation-guidance-r23.md "
                    "字节复用零改写；(iii-a) 可操作分辨条款随 §4 逐字在案；"
                    "本轮无 §5B 节=r19 基座结构在案；§6 报告框收敛条款随"
                    "基座在案[非本轮变量]）："
                    "r8 两条显式判据"
                    "（弃权适用于存在/归类不确定；弃权不适用于仅范围不确定）、"
                    "存在性判断一般判据引导句与三路出口显式化原文保留；§4 "
                    "存在性判断一般判据=量化版 (i)(ii)(iii)（原文随基座逐字"
                    "在案）；(iii-a) 可操作分辨条款（间隙支/侵入支/残余"
                    "弃权支）逐字在案；反放宽条款原文保留（「仅因形态不熟悉、"
                    "不确定其设计含义」仍不构成判为正常设计特征的理由）；"
                    "量化阈值为一般判据、非期望清单；§3A 示例 c 收窄判据原文"
                    "适用；abstain=true=现象是否存在或归属哪类无法负责任"
                    "地判断；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("协议侧 v1.3 n 扩容口径首轮执行（v1/"
                                      "v1.1/v1.2 继承不改）：24 次盲读=4 视"
                                      "角格×6 实例（i1–i6）=12 个 reader "
                                      "智能体各包同侧两板、两波次串行保序"
                                      "（波1=top 侧、波2=bottom 侧）；本轮 "
                                      "24 派次 reader 实例群全部重抽+扩容"
                                      "（=本轮实验操作本身）；每派次指令含 "
                                      "v1.2 硬性条款（禁止程序化图像处理、"
                                      "只允许 Read 直读原图）；零诊断/探针"
                                      "内容（framing/witness 记录不进任何 "
                                      "reader 上下文、零 r22/r23 现象描述"
                                      "注入）、零 legend/零其他解释（判读"
                                      "输入=指引+单张 PNG+派发指令）；每图"
                                      "独立判读；跨实例/跨视角禁止交流"
                                      "（独立性亦为本轮归因裁决有效性的"
                                      "前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R23,
                                 "sha256": _sha(REL_GUIDANCE_R23),
                                 "frozen_before_read": True,
                                 "reuse_mode": "byte_reuse_dispatch_override",
                                 "transform_base": ("observation-guidance-"
                                                    "r23.md 即基座即本轮判"
                                                    "读依据（866b0157、零"
                                                    "改写零派生；派发层前缀"
                                                    "覆盖 R23T/R23B→R24T/"
                                                    "R24B、round_id→"
                                                    "2026-09-10-r24——"
                                                    "r16/r22 先例同型）"),
                                 "role": ("本轮唯一判读依据（字节复用本体"
                                          "在案；§6 示例前缀 R23T-/R23B- "
                                          "落盘原文、派发层覆盖=前缀差异"
                                          "登记在案）"),
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：axis-experiment-plan-r17-r20.json"
                 "（b6ec6467…，stage2 组合定义+comparison_rule+守门+"
                 "early_stop_rule+combination_decision_rule，先于 R17–R21 "
                 "任何实验轮盲读冻结；R21 全组合槽位=early_stop "
                 "strong_single_axis_shortcut 命中未触发、永久留空（跳号"
                 "声明在案）；用户 2026-09-09「三条轴单独/组合/全组合"
                 "尝试，选择收益最大的继续」指令在案）"
                 "→round22-dev-record（b4b8fbe9…，drift 0.09064 参照在案="
                 "split-half 阈值参照源）→round23-dev-record（343a6747…，"
                 "r23 收束+honest_conclusion 下一候选建议（b）「对剩余混杂"
                 "（判据内容/实例群/其他输出侧因素）做新预注册轮归因」="
                 "本轮设计出处与合法性依据；r23 字母=confounded 维持不改"
                 "写）→r24-prep-record.json（760af49f…，本轮预注册件，"
                 "measurement_design 五条[n=6 扩写]聚合口径与 hypothesis_"
                 "test.adjudication 归因三支判据（instance_dominated=G1 "
                 "维持且 M4(n=6)<0.261904 且 split_half≤0.09064/not_"
                 "instance_dominated=G1 维持且（M4≥0.261904 或 split_half>"
                 "0.09064）/guard_interrupted=G1 破坏）先于盲读冻结；"
                 "instrument_change.changed=false；guidance=observation-"
                 "guidance-r23.md 字节复用[派发层前缀覆盖]；渲染="
                 "renders-r14b 字节复用）先于本轮盲读落盘（零 GT 暴露声明"
                 "在案 no_visual_reading=true；pre_round_review 在案）→"
                 "判读指引=observation-guidance-r23.md"
                 "（866b0157…，字节复用本体，本轮唯一判读依据）"
                 "→渲染零变更（renders-r14b 四图字节复用，四 PNG sha="
                 "witness-r14b 登记值=prep-record 登记值三方一致）→"
                 "24 次盲读（24 件哈希全 64 位写死断言：84aae6b5/23b921a7/"
                 "671dcfb0/ac9e4f2b/cf18682f/547f4ad6/d34444bc/df9feb5b/"
                 "e1e75df0/f45a6794/7e3f3f07/416fc4bc/b05c3048/5ee02484/"
                 "628cbd33/a01b870e/0bdce9c1/9e02ec9b/b326d23b/291e5285/"
                 "78ecdad3/9c46ec7c/bb8aef93/1f03a2ea）→比对记录"
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
            "r20_run": {"path_rel": REL_RUN_R20P,
                        "sha256": _sha(REL_RUN_R20P)},
            "r22_run": {"path_rel": REL_RUN_R22P,
                        "sha256": _sha(REL_RUN_R22P)},
            "r23_run": {"path_rel": REL_RUN_R23P,
                        "sha256": _sha(REL_RUN_R23P)},
            "note": ("R3–R23 逐轮性质在案（r3 3D 仪器/r4 2D PDF 仪器/r5 "
                     "有效分辨率/r6 指引侧两变更/r7 §4 弃权适用性/r8 §4 "
                     "存在性判据/r9 §3A 示例 c/r10 零变更重复/r11 协议侧 "
                     "1→3 多实例 v1.1/r12 示例 c 收窄+v1.2 派发层/r13 §4 "
                     "可操作化/r14 bottom 渲染更换[reject]/r15 §5A 配套"
                     "[reject]/r16 同指引重复[inconclusive]/r17 轴1 渲染"
                     "[reject]/r18 轴2 §5B[reject]/r19 轴3 (iii-a)"
                     "[marginal]/r20 stage2 组合[reject、G1 破坏]/r22 同"
                     "指引重复[regressed、G2 0→2]/r23 报告框收敛归因"
                     "[confounded、G2=1]）run 在案；"
                     "R24=实例群扩容归因轮（多实例协议 v1.3：每视图 3→6、"
                     "24 派次；唯一实验变量=实例数 n；指引字节复用+渲染"
                     "字节冻结+GT/阈值/协议正文零变更；执行 round23-dev-"
                     "record 下一候选建议（b）[实例群轴]+用户 2026-09-10 "
                     "拍板）；轮间对比由后续 round24-dev-record（另包"
                     "落盘）与 channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案；24 件"
            "全 64 位锚盘态钉死），"
            "比较器/视角层聚合/双口径归并/代表配置选取（下中位序位+实例"
            "编号先序：top 升序 11/15/16/17/22/24→top-i3、bottom 升序 "
            "4/4/4/4/4/6→tie 按编号先序 bottom-i3）/通道重放/rubric "
            "机械分型为纯函数（十二实例旗数 24/17/16/22/11/15/4/4/4/6/"
            "4/4、弃权 24/2/5/19/6/2/0/0/4/6/4/4 唯一可复算），无 "
            "wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-10-r24（事件序="
            "axis-experiment-plan-r17-r20（b6ec6467…，冻结件在案；R21 "
            "全组合槽位未触发永久留空）→round22-dev-record（b4b8fbe9…）"
            "→round23-dev-record（343a6747…，候选(b)授权在案）→"
            "r24-prep-record（760af49f…，本轮预注册件，先于盲读冻结）→"
            "r23 指引字节复用（observation-guidance-r23.md 866b0157…，"
            "本轮唯一判读依据）→渲染零变更"
            "（renders-r14b 四图字节复用、zero-write，witness-r14b 在案）"
            "→24 次盲读→比对记录；在案延续=gt-"
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
    """run-r24 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 24, "top-i2": 17, "top-i3": 16, "top-i4": 22,
                  "top-i5": 11, "top-i6": 15, "bottom-i1": 4, "bottom-i2": 4,
                  "bottom-i3": 4, "bottom-i4": 6, "bottom-i5": 4,
                  "bottom-i6": 4}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 24, "top-i2": 2, "top-i3": 5, "top-i4": 19,
                "top-i5": 6, "top-i6": 2, "bottom-i1": 0, "bottom-i2": 0,
                "bottom-i3": 4, "bottom-i4": 6, "bottom-i5": 4,
                "bottom-i6": 4}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 131:
        _fail("全旗标总数与实测不一致")
    fc = run_doc["reader"]["flag_count"]
    if fc["by_view"] != {"top": 105, "bottom": 26} \
            or fc["abstain_by_view"] != {"top": 58, "bottom": 18} \
            or fc["by_state"] != {"applied": 59, "prep1": 72} \
            or fc["abstain_by_state"] != {"applied": 35, "prep1": 41} \
            or fc["reroute_class_production"] != 6:
        _fail("视角/态聚合与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.45 \
            or agg["flag_count_total"] != 20 \
            or agg["abstain_count_total"] != 9 \
            or agg["gt_recall_total"] != 0.0 \
            or agg["seed_match_rate_total"] != 0.0:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "not_instance_dominated":
        _fail("假设字母裁决与预注册判据复算不符")
    if hyp["hypothesis_id"] != \
            "r23-confounded-residual-confound-instance-axis-attribution":
        _fail("hypothesis_id 与预登记不符")
    m = hyp["measurement"]
    if m["contact_family_abstain_flags_rubric_r24"] != 4 \
            or m["contact_r16_baseline_registered"] != 10:
        _fail("contact 计数与实测不一致")
    if m["top_abstain_flags_r24"] != 105 or m["top_abstain_count_r24"] != 58 \
            or m["top_abstain_rate_r24"] != 0.552381:
        _fail("判据首键 M1 计数与实测不一致")
    if m["m4_top_rate_range_r24"] != 0.888889:
        _fail("M4(n=6) 计数与实测不一致")
    if m["split_half_M1_diff_r24"] != 0.01864:
        _fail("split_half_M1_diff 计数与实测不一致（应为 0.018640）")
    if m["crit_not_instance_dominated"] is not True:
        _fail("not_instance_dominated 支布尔与实测不一致（M4 条件超出）")
    if m["crit_instance_dominated"] is not False:
        _fail("instance_dominated 支布尔与实测不一致")
    if m["crit_guard_interrupted"] is not False:
        _fail("guard_interrupted 布尔与实测不一致（G1 应维持）")
    if m["g2_rejected_entries_zero"] is not True:
        _fail("G2 出局条目清零布尔与实测不一致（应为 0 条）")
    if m["m4_threshold_6dp"] != 261904 \
            or m["split_half_threshold_6dp"] != 90640:
        _fail("阈值锚与判据不符")
    if m["top_abstain_rate_r16_baseline_value"] != 0.771429:
        _fail("r16 基线值与在案登记不一致")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r24"] != 0 \
            or bso["bottom_abstain_flags_r24"] != 26 \
            or bso["bottom_abstain_count_r24"] != 18 \
            or bso["bottom_abstain_rate_r24"] != 0.692308 \
            or bso["bottom_courtyard_non_abstain_by_instance_r24"] != {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0,
                "bottom-i4": 0, "bottom-i5": 0, "bottom-i6": 0} \
            or bso["bottom_rate_direction_vs_r16"] != "improved":
        _fail("bottom 侧观察计数与实测不一致")
    g = m["guard_channel"]
    if g["g1_ok"] is not True or g["g2_guard_ok"] is not True \
            or g["guards_ok"] is not True \
            or g["g2_geometry_gate_r19"] != 0 \
            or g["g2_geometry_gate_r22"] != 2 \
            or g["g2_geometry_gate_r23"] != 1 \
            or g["g2_geometry_gate_r24"] != 0:
        _fail("守门 G1/G2 计数与实测不一致（G1 维持、G2 0→2→1→0 清零）")
    mo = hyp["mechanism_observation"]
    tt = mo["abstain_typology"]
    if tt["type_counts"] != {"contact": 26, "existence": 30,
                             "other_layer": 2} \
            or tt["top_abstain_flags_total"] != 58:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 28 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 4, "top-i2": 0, "top-i3": 0,
                                     "top-i4": 4, "top-i5": 4, "top-i6": 0,
                                     "bottom-i1": 0, "bottom-i2": 0,
                                     "bottom-i3": 4, "bottom-i4": 4,
                                     "bottom-i5": 4, "bottom-i6": 4} \
            or bd["blackdot_to_non_abstain_count"] != 16 \
            or len(bd["black_dot_non_abstain_flags"]) != 16 \
            or bd["judged_normal_dispatches"]["count"] != 2:
        _fail("黑点族计数与实测不一致")
    if bd["rubric_families"]["counts"] != R24_FAMILY_COUNTS_REGISTERED \
            or bd["rubric_families"]["replay_proof"]["per_flag_total"] \
            != 132:
        _fail("rubric 族计数/重放证明与实测不一致")
    cco = mo["criterion_citation_observation"]
    if cco["citation_counts"]["flag_level_s5b_literal"] != 0 \
            or cco["citation_counts"]["flag_level_iiia_literal"] != 7 \
            or cco["citation_counts"]["flag_level_branch_literal"] != 0 \
            or cco["citation_counts"]["notes_level_s5b"] != 0 \
            or cco["citation_counts"]["notes_level_iiia"] != 8 \
            or cco["citation_counts"]["notes_level_s6_clause"] != 20:
        _fail("§5B/(iii-a)/§6 援引计数与实测不一致")
    if len(cco["iiia_flag_rows"]) != 7:
        _fail("(iii-a) 逐旗摘录行数与实测不一致")
    grej = mo["g2_rejected_entries_r24"]
    if grej["count"] != 0 or grej["entries"] != [] \
            or len(grej["comparison_to_r23"]["r23_entries"]) != 1:
        _fail("G2 出局条目空摘录与实测不一致（r24=0、r23 对照=1）")
    if mo["split_half_decomposition"]["split_half_6dp"] != 18640 \
            or mo["split_half_decomposition"]["half_A"]["rate_6dp"] \
            != 543860 \
            or mo["split_half_decomposition"]["half_B"]["rate_6dp"] \
            != 562500:
        _fail("split-half 分解与实测不一致")
    ido = mo["instance_distribution_observation"]
    if ido["top_rates_by_instance"]["top-i1"] != 1.0 \
            or ido["top_rates_by_instance"]["top-i2"] != 0.117647 \
            or ido["m4_12_cell_range"] != 0.888889:
        _fail("逐实例率分布观察与实测不一致")
    ledger = mo["experiment_comparison_ledger"]
    if ledger["r24_measured"]["M1"] != 0.552381 \
            or ledger["r24_measured"]["M2"] != 0.692308 \
            or ledger["r24_measured"]["M3"] != 28 \
            or ledger["r24_measured"]["M4"] != 0.888889 \
            or ledger["r24_measured"]["split_half_M1_diff"] != 0.01864 \
            or ledger["r24_measured"]["contact_family_abstain_flags_rubric"] \
            != 4:
        _fail("实验对照账五键与实测不一致")
    if ledger["ranking_by_comparison_rule"]["r24_eligibility"] is not True \
            or ledger["ranking_by_comparison_rule"][
                "ranking_order_best_first"] != ["r19_axis3", "r24_expansion",
                                                "r18_axis2", "r16_baseline",
                                                "r17_axis1"]:
        _fail("comparison_rule 排序（r24 入排序、r19 第一）与实测不一致")
    if ledger["ranking_by_comparison_rule"]["r20_eligibility"] is not False \
            or ledger["ranking_by_comparison_rule"]["r22_eligibility"] \
            is not False \
            or ledger["ranking_by_comparison_rule"]["r23_eligibility"] \
            is not False:
        _fail("r20/r22/r23 破坏轮应不入排序（登记行仅如实入账）")
    if ledger["significant_benefit_vs_r16"]["met"] is not True \
            or ledger["significant_benefit_vs_r16"][
                "r24_m1_absolute_drop"] != 0.219048:
        _fail("显著收益对照与实测不一致")
    if ledger["attribution_conclusion"]["verdict"] \
            != "not_instance_dominated":
        _fail("归因结论位与字母裁决不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if sum(1 for v in gs.values() if v["§5A_cited"]) != 3 \
            or sum(1 for v in gs.values() if v["§5B_cited"]) != 0:
        _fail("绿区语义化 §5A/§5B 引用与实测不一致（实例级 §5A 3/6、"
              "§5B 0/6；派次级 §5A 6/12）")
    te = mo["reader_tool_evidence"]
    if te["count"] != 24 or len(te["rows"]) != 24 \
            or len(te["no_cross_inference_sources"]) != 11:
        _fail("工具规约证据与实测不一致（24/24、跨图自述 11 派次）")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.882353 \
            or vl["bottom"]["abstain_rate_range"] != 1.0:
        _fail("视角层极差与实测不一致")
    if vl["top"]["abstain_rate"]["median"] != 0.4289775 \
            or vl["bottom"]["abstain_rate"]["median"] != 1.0:
        _fail("n=6 中位数与实测不一致（top=(0.3125+0.545455)/2、"
              "bottom=(1.0+1.0)/2）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 1 or dual["agreement"]["count"] != 1:
        _fail("双口径计数与实测不一致（union=1、agreement=1[4/6]）")
    if dual["union"]["gt_ids"] != ["GT-REVC-P1-L1SHORT"] \
            or dual["union"]["gt_recall_union"] != 0.076923 \
            or dual["agreement"]["gt_recall_agreement"] != 0.076923:
        _fail("双口径计数与实测不一致（L1SHORT、召回 1/13）")
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    if len(hits) != 1 or hits[0]["matched_by_count"] != 4:
        _fail("GT 命中明细与实测不一致（L1SHORT 4/6 实例命中）")
    matches_all = sorted(
        (n, mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != [("top-i2", "R24T-015", "GT-REVC-P1-L1SHORT"),
                       ("top-i4", "R24T-019", "GT-REVC-P1-L1SHORT"),
                       ("top-i5", "R24T-009", "GT-REVC-P1-L1SHORT"),
                       ("top-i6", "R24T-015", "GT-REVC-P1-L1SHORT")]:
        _fail("matches 明细与实测不一致（r24 四条命中全部 L1SHORT）")
    rep = run_doc["representative_configuration"]
    if rep["members"] != {"top": "top-i3", "bottom": "bottom-i3"}:
        _fail("代表配置与实测不一致（下中位序位=top-i3+bottom-i3）")
    if rep["selection"]["top"]["tie"] is not False \
            or rep["selection"]["bottom"]["tie"] is not True:
        _fail("代表配置 tie 语义与实测不一致")
    if run_doc["reader"]["flag_count"]["reroute_class_production"] != 6:
        _fail("reroute 类产量与实测不一致")
    # 通道条目数与实测一致（几何 0、类别 6、视角 0）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r24_area_ratio_rejected_entries"]) \
            != 0 \
            or len(ca["channel_2_category_gate"]["r24_category_mismatch_"
                                                   "entries"]) != 6 \
            or len(ca["view_gate_observations"]["r24_entries"]) != 0:
        _fail("通道条目数与实测声明不一致（几何 0、类别 6、视角 0）")
    # courtyard 追踪与实测一致（r24 非弃权 courtyard=6、弃权=1、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r24"] != 0 or len(
            ct["r24_courtyard_flags"]["non_abstain"]) != 6:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r24_courtyard_flags"]["abstain"]) != 1:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 零旗标派次=0（24 格全部≥1 旗；item 5 None 口径未触发）
    if run_doc["reader"]["zero_flag_parts"]["parts"] != []:
        _fail("零旗标派次与实测不一致（本轮应为空）")
    # reroute 摘录与 reader 原文一致（程序提取回验）
    for r in hyp["reroute_continuation_r24"]["reroute_flag_detail_r24"]:
        if r["location_evidence_excerpt"] not in raw_texts[r["source"]]:
            _fail(f"reroute 摘录与 reader 原文不符: {r['flag_id']}")
        if r["detected_substring_hits"] != []:
            _fail(f"reroute 子串命中与实测不符: {r['flag_id']}")
    for ev in te["rows"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"工具规约摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["criterion_citation_observation"]["iiia_flag_rows"]:
        if ev["location_evidence_excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"(iii-a) 摘录与 reader 原文不符: {ev['flag_id']}")


def main() -> None:
    # 输入先验锚（fail-closed）
    for rel, want in FROZEN_SHA256.items():
        p = _rel(rel)
        if not p.is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")
        got = _sha(rel)
        if got != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {got[:8]}…≠{want[:8]}…")
    # 24 件盲读原始件哈希前缀逐字复核（盲读亲测在案锚）
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r24")

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
    run_status = _commit(_rel(REL_RUN_R24), run_bytes,
                         "calibration-run-r24.json")
    run_sha = _sha(REL_RUN_R24)
    # round24-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    m = hyp["measurement"]
    mo = hyp["mechanism_observation"]
    ca = run["channel_attribution"]
    print(f"[s86-cal-r24] 解析：24 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 55、弃权 76）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s86-cal-r24] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s86-cal-r24] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s86-cal-r24] zero_flag_parts: "
          f"{[(z['instance'], z['state']) for z in run['reader']['zero_flag_parts']['parts']]}"
          f"（24 格全部≥1 旗=零零旗格；item 5 零分母→None 口径未触发）")
    print(f"[s86-cal-r24] view_layer: top range={vl['top']['abstain_rate_range']}"
          f"（逐实例两板合计口径；n=6 中位数={vl['top']['abstain_rate']['median']}"
          f"=第 3/4 序位均值） bottom range={vl['bottom']['abstain_rate_range']}"
          f"（中位数={vl['bottom']['abstain_rate']['median']}）；"
          f"M4(n=6) 12 格口径={m['m4_top_rate_range_r24']}（单列）")
    print(f"[s86-cal-r24] split_half: A(i1–i3)=31/57=0.543860 vs "
          f"B(i4–i6)=27/48=0.562500 → diff={m['split_half_M1_diff_r24']}"
          f"（6 位定点 18640≤90640=内）")
    print(f"[s86-cal-r24] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13"
          f"（r24 命中=GT-REVC-P1-L1SHORT 4/6 实例[top-i2 R24T-015/top-i4 "
          f"R24T-019/top-i5 R24T-009/top-i6 R24T-015，全部 prep1]；"
          f"agreement≥4/6=v1.1 ≥2/3 语义 n=6 推广首次计入；对照 r19 唯一"
          f"命中 L1SHORT、r22 两条 L1SHORT、r23 两条[R4J3+L1SHORT]，如实并列）")
    print(f"[s86-cal-r24] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    print(f"[s86-cal-r24] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；归因三支判据=M4(n=6)+split_half 双"
          f"判据+G1 守门：R24 五键=(M1={m['r24_m_tuple_6dp']['M1']},"
          f"M2={m['r24_m_tuple_6dp']['M2']},M3={m['r24_m_tuple_6dp']['M3']},"
          f"M4={m['r24_m_tuple_6dp']['M4']},split_half="
          f"{m['r24_m_tuple_6dp']['split_half_M1_diff']})；比较集 r16 "
          f"(0.771429,0.857143,12,0.261904)/r19 (0.461538,0.571429,4,"
          f"0.211111)/r22 (0.390244,0.2,4,0.104545)/r23 (0.484848,"
          f"0.571429,8,0.520833) 全部 live 复算交叉核对；M4 阈值 0.261904"
          f"（888889≥261904=超出）、split-half 阈值 0.09064（18640≤90640="
          f"内）→落支={m['letter_branch'][:80]}…；"
          f"G1=bottom courtyard 非弃权六实例 "
          f"{m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r24']}"
          f"→g1_ok={m['guard_channel']['g1_ok']}；"
          f"G2 出局条目 R19={m['guard_channel']['g2_geometry_gate_r19']}"
          f"→R22={m['guard_channel']['g2_geometry_gate_r22']}"
          f"→R23={m['guard_channel']['g2_geometry_gate_r23']}"
          f"→R24={m['guard_channel']['g2_geometry_gate_r24']}"
          f"（观察项非字母支；r24 入排序资格={m['guard_channel']['guards_ok']}）；"
          f"M1={m['top_abstain_count_r24']}/"
          f"{m['top_abstain_flags_r24']}={m['top_abstain_rate_r24']}，r16 基线双侧复算 "
          f"{m['top_abstain_rate_r16_baseline_live']}"
          f"={m['top_abstain_rate_r16_baseline_value']}）；机制观察单列）")
    print(f"[s86-cal-r24] 侧观察（M2 bottom，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r24']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r24']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r24']}"
          f" vs r16 基线 12/14=0.857143、r19 4/7=0.571429、r20 4/14=0.285714、"
          f"r22 2/10=0.2、r23 8/14=0.571429"
          f"（{m['bottom_side_observation']['bottom_rate_direction_vs_r16']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r24']}"
          f"（G1 六实例维持；对照 r20 破坏 2/0/0 在案）")
    print(f"[s86-cal-r24] 机制观察要点：rubric 族计数="
          f"{mo['black_dot_tracking']['rubric_families']['counts']}"
          f"（r13–r16 132 条重放对拍逐一相等；contact=4 vs r19 4/r22 2/"
          f"r23 8、黑点=28 vs r19 4/r22 4/r23 8[远高=n 扩容+实例异质性]、"
          f"存在性其他=44）；逐实例率分布=top-i1 1.0 vs top-i2 0.117647/"
          f"top-i6 0.133333 双峰结构（12 格极差 0.888889）；split-half 分解="
          f"聚合稳（0.018640≤0.09064）vs 个体散（0.888889）并存；"
          f"弃权分型（机械主出口）={mo['abstain_typology']['type_counts']}；"
          f"援引分记：旗级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_s5b_literal']}"
          f"/(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_iiia_literal']}"
          f"/分支(="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_branch_literal']}"
          f"；notes 级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_s5b']}"
          f"/24（本轮指引无 §5B 节=零上下文）、(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_iiia']}"
          f"/24（对照 r19 10/12、r22 6/12、r23 4/12）、§6 报告框收敛条款="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_s6_clause']}"
          f"/24；G2 出局条目 {mo['g2_rejected_entries_r24']['count']} 条"
          f"（r23 对照=R23T-004 ar=11.45868 装载在案）；黑点旗 28 条全弃权 "
          f"{mo['black_dot_tracking']['by_instance']}（vs r19 4/r22 4/r23 8）；"
          f"黑点转非弃权旗 "
          f"{mo['black_dot_tracking']['blackdot_to_non_abstain_count']} 条；黑点判正常派次 "
          f"{mo['black_dot_tracking']['judged_normal_dispatches']['count']}/24"
          f"（对照 r15=3/r16=2/r18=2/r19=3/r20=4/r22=4/r23=2）；五键账 "
          f"(M1,M2,M3,M4,split_half)=(0.552381,0.692308,28,0.888889,"
          f"0.018640)；排序（资格门判定后入排序）="
          f"{mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['ranking_order_best_first']}"
          f"（r24_eligibility={mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['r24_eligibility']}"
          f"；r20/r22/r23=排除行）；"
          f"归因结论位={mo['experiment_comparison_ledger']['attribution_conclusion']['conclusion'][:60]}…；"
          f"reroute 6 旗（弃权 4、子串命中 0）")
    print(f"[s86-cal-r24] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    print(f"[s86-cal-r24] channel_attribution: "
          f"geo R19={len(ca['channel_1_geometry_gate']['r19_area_ratio_rejected_entries'])}"
          f"→R22={len(ca['channel_1_geometry_gate']['r22_area_ratio_rejected_entries'])}"
          f"→R23={len(ca['channel_1_geometry_gate']['r23_area_ratio_rejected_entries'])}"
          f"→R24={len(ca['channel_1_geometry_gate']['r24_area_ratio_rejected_entries'])}, "
          f"cat R24={len(ca['channel_2_category_gate']['r24_category_mismatch_entries'])}, "
          f"view R24={len(ca['view_gate_observations']['r24_entries'])}")
    print(f"[s86-cal-r24] commit: run={run_status}（round24-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s86-cal-r24] sha256[:8] calibration-run-r24.json = "
          f"{run_sha[:8]}")
    print(f"[s86-cal-r24] sha256 calibration-run-r24.json = {run_sha}")
    print("[s86-cal-r24] R24 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":

    main()
