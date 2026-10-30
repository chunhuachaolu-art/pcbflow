#!/usr/bin/env python
"""CAL-R20-CLOSE：reader 判读迭代第二十轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s71_calibration_r19_compare.py 同构，仅输入与轮次
常量不同；R20=development 域 stage2 组合轮（axis-experiment-plan-
r17-r20 stage2 唯一组合轮=轴3+轴2 两轴变更并施：渲染零变更=
renders-r14b 四图字节复用（与 r14–r19 盲读同一批文件、四
PNG sha=witness-r14b 登记值 fail-closed 比对一致）；判读指引=
observation-guidance-r20.md（9cdac9ed，由 r19 指引机械变换生成、
§4(iii-a) 随基座逐字承继+并入 r18 §5B 黑点仪器注记节全文（cadcb8f3
跨代哈希交叉锚），本轮唯一判读依据）；GT/阈值/协议零变更（v1.1+v1.2
维持）；instrument_change.changed=false 已预注册）——唯一操纵因子=
判读指引合成（§5B+(iii-a) 两增补并集）；检验 r20-prep-record.json
预注册假设（hypothesis_id=axis-plan-r20-combo-additivity，判据=
r20-prep-record.json hypothesis_test.adjudication 三分判据预注册
原文，脚本从 prep-record 文件加载判据文本、基线数字 live 重放不
手工抄数）：「轴2（§5B 黑点中性仪器注记）+轴3（§4(iii-a) 可操作
分辨条款）两轴变更并施的组合轮 R20 收益不低于最优单轴 r19（可加性
验证）」：

  T1  解析 12 个 reader-raw-r20-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
      12 件哈希前缀逐字钉死（盲读亲测在案：applied-top-i1=044486bb、
      prep1-top-i1=d2c1b7da、applied-bottom-i1=1aa66143、
      prep1-bottom-i1=e5e6a5d9、applied-top-i2=11edbc4d、
      prep1-top-i2=42d7c2e8、applied-bottom-i2=c95f1620、
      prep1-bottom-i2=3ecf232c、applied-top-i3=80961e4e、
      prep1-top-i3=1765d865、applied-bottom-i3=a852215f、
      prep1-bottom-i3=1691b7aa，全量哈希入 FROZEN_SHA256）。
  T2  按 r20-prep-record.json measurement_design 五条预注册聚合口径
      执行（与 calibration-run-r16–r19 同一比较脚本血统；聚合口径零
      改动）：(1) 实例主记录=六实例各自两板合计 flag_count/abstain_
      count/abstain_rate（6 位小数；零旗标分母=None）/非弃权清单
      （r20 实测编号行为=6 实例全部同实例跨板连续（与 prep-record
      naming「同实例跨板连续」声明全部相符；与 r19 实测混合行为对照
      如实登记）；清单按 (state, flag_id) 限定，跨板同号不混淆）/
      逐旗 containment+area_ratio 匹配明细；(2) 视角层=每视角 3 实例
      flag_count/abstain_rate/matches 各中位数+min+max 三分列不取整
      （本轮 12 格全部≥1 旗：bottom 三实例弃权率全部可计算、中位数
      直接取排序第 2；item 5 零分母口径未触发）；(3) GT 匹配双口径=
      union（≥1 实例命中）与 agreement（≥2/3）并列+逐 GT 条目
      matched_by_count（0..3；召回分母=GT 13 条）；(4) 联合门
      （APR-0011 阈值零改动）=代表配置（每视角 flag_count 中位数
      实例）算一轮 joint+per-metric 实例间范围+逐实例原始记录三者
      并列不挑优；(5) bottom 零旗标分母=按库侧 cal._ratio 先例
      None+文字说明（本轮无零旗标派次、先例保留在案）。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——GT 13 条全部 side=top 且本轮渲染零变更
      （renders-r14b 字节复用=GT 重投影输入未变），frame_box_pct_r5
      =GT 框在渲染图像空间的归一化坐标口径、随 r14 顶层更换先例沿用，
      本轮零新派生；bottom GT 无源在案 gt-audit-r1）
      +达标线=APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册主通道（三分判据，r20-prep-record.json hypothesis_test.
      adjudication 原文）逐支执行：判据=可加性比较（冻结 comparison_
      rule.ordering (M1 升序,M2 升序,M3 升序,M4 升序) 字典序）——
      supported=(s) R20 四元组在冻结 ordering 排序中不劣于最优单轴
      r19（r19 实测 (0.461538,0.571429,4,0.211111)=dev-r19 measured_
      rows 装载+run-r19 内嵌实例记录 live 复算交叉核对）；reject=
      (r) M1 ≥0.771429（r16 基线 27/35 双侧复算 live 重放交叉核对）、
      或 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）任一
      破坏→按 axis-plan early_stop_rule.guard_failure_exit 出局、
      处置按冻结 combination_decision_rule.iii_non_additive_fallback
      采最优单轴；marginal=(m) 未达 supported 但 M1 <0.771429 且
      G1/G2 维持——记录为部分收益（可加性未证、不可加采最优单轴
      r19）。判据比较用 6 位定点整数交叉相乘（避免浮点）；支序=
      reject→supported→marginal（判据字面互斥性由脚本自检，未覆盖
      组合即中止）。letter 裁决唯一正式；守门 G1/G2 独立单列（G1=
      bottom courtyard 非弃权 0/0/0 维持、G2=guard_ok=True 维持
      ——top 视非弃权旗标 frame_box_pct 几何门面积比出局条目 R19=0→
      R20 实测不升；任一破坏→reject 支成立+按 plan early_stop_rule
      出局）；机制观察单列（mechanism_observation_separate 原文
      口径）：§5B 与 (iii-a) 援引计数分开记（旗级 location_evidence
      含「§5B」/「(iii-a)」/「分支(」实测+notes 级含「§5B」/「(iii-a)」
      实测；双基线对照：r18 §5B 援引=旗级 0/13 黑点弃权旗、派次级
      1/12（dev-r18 在案）；r19 (iii-a) 援引=旗级「(iii-a)」6 旗+
      「分支(」2 旗、notes 级 10/12 派次（dev-r19 在案））+ (iii-a)
      逐旗理由落支分布（间隙支/侵入支/残余弃权支——逐旗摘录关键词；
      旗级落支+notes 级落支分列）；contact 族逐旗 rubric 分类入账+
      黑点族/存在性其他族计数（三族对照 r18（黑点 13/存在性 12）与
      r19（黑点 4/存在性 14）双基线——若显著上升=弃权转移如实记录）；
      黑点转非弃权旗计数（逐条摘录）+黑点判正常派次计数；M2=bottom
      全旗聚合弃权率（对照 r16 基线 12/14=0.857143、r18 13/19=
      0.684211、r19 4/7=0.571429 live 复算）；M4=top 逐实例弃权率
      极差（对照 r16 基线 0.261904）；(M1,M2,M3,M4) 四元组入实验
      对照账字段（照 axis-plan benefit_metrics 口径定义、四元组随
      run 在案、由 dev-record 包转记；r16 基线/r17 轴1/r18 轴2/
      r19 轴3/r20 组合五行并列；r17 行=round18-dev-record cross_
      round_status 实测装载、r18 行=run-r18 内嵌实例记录 live 复算、
      r19 行=dev-r19 measured_rows 装载+run-r19 内嵌实例记录 live
      复算交叉核对、与各自在案登记交叉核对）；axis-plan comparison_
      rule（(M1 升序,M2 升序,M3 升序,M4 升序) 字典序、资格门=G1/G2
      均满足）下的当前排序如实登记（资格门破坏轮不入排序）；显著
      收益定义（M1 绝对降幅 ≥0.10）逐轮对照；阶段2 结论位（supported
      →组合胜出；marginal→不可加采最优单轴 r19；reject→劣化+采
      最优单轴 r19+守门破坏出局）；top 弃权分型照常；bottom courtyard
      非弃权与 courtyard 旗计数（对照 r19 的 0 非弃权+4 弃权）。
      → calibration-run-r20.json。
  T3  development 域记录（R19→R20 方向性对照/假设裁决/联合评价趋势/
      下一迭代目标=最优单轴 r19 基座收口）由后续 dev-record 包落盘
      （round20-dev-record，另包执行）；本包仅产出 run-r20、零
      dev-record 写入。

通道归因纪律（vs R19；方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/
s55/s58/s64/s68/s71 deviation_note 口径）：本轮对 R15/R16/R17/R18/
R19 均以内嵌输入（reader_flags/gt_entries/flag_views，run sha 在案）+
compare_v3 同源几何原语（calibration._containment/_area_ratio/
CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放通道分类，并与
各态 compare_v3 的 matches∪duplicate_reports 对拍复核。跨轮 flag_id
不构成同旗配对（不同 reader 实例），归因是通道级不是旗级。

读者实例披露（如实入账，不作废）：R20 十二派次全部以 Read 工具直读、
逐派次 reading_notes 自述「未读取盘上任何其他文件」（12/12 在案）；
applied/prep1-top-i1 另自述「未与任何其他图像做跨图比对推断」、
applied/prep1-bottom-i3 另自述「不跨图合并、不跨图推断」（两板同图
同判自述）；§5B 措辞 notes 级援引 4/12 派次、§4(iii-a) 措辞 notes
级援引 4/12 派次（两计数分开记，逐件摘录见 hypothesis_test.
mechanism_observation.criterion_citation_observation）；
applied/prep1-top-i1 notes 自述黑点弃权时明写「仪器注记 §5B 不作为
判据」（§5B 反指示声明被读侧自觉遵守的在案实例）；跨轮实例全重抽+
轮内实例差异=混杂因素照旧声明——本轮唯一操纵因子=判读指引合成
（§5B+(iii-a) 并集；渲染零变更=renders-r14b 字节复用，仪器侧零
变动；实例群重抽为轮际比较的固有混杂、per axis-plan comparison_
rule.drift_confound_note 显式容忍）。
输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件=缩进
格式冻结原始判读件、本轮零改动直读（direct JSON 解析、12 件 parse
校验全部通过）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅一新 JSON；round20-dev-
record 由后续包落盘、本包零写入）；域声明=development（协议 v1 §1/§4：
迭代轮不得冒充留出证据）；无 wall-clock（日期/轮次=声明常量
2026-09-09 / 2026-09-09-r20）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；输入先验锚不符即中止；同参重建逐字节一致
（byte-exact 可重跑）；零子进程/零网络；datasets/ 零写入；不 git
commit/push。

用法：python scripts/s74_calibration_r20_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-09-r20"
ROUND_LABEL = "r20"
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
#: 本包唯一新建输出（防覆写护栏语义照 s68/s71；不在 FROZEN_SHA256 锚集）。
REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"

#: 12 份盲读原始件（6 实例×2 板；r20 实测编号行为=6 实例全部同实例
#: 跨板连续、与 prep-record naming「同实例跨板连续」声明全部相符，
#: 见 DISPATCH_MODE；12 格全部≥1 旗、无零旗标实例）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r20-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r20-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r20-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r20-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r20-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r20-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r20-prep1-bottom-i3.txt",
}

#: 六实例=本轮主记录单位（measurement_design item 1）；每实例=同视角
#: 两板（applied+prep1）两派次，实例间编号独立（r20 实测：6 实例全部
#: 同实例跨板连续）。
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
#: 渲染的输入侧冻结矢量 PDF（r20-prep-record no_loosening_note：本轮
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
    REL_FRAMING_R14B:
        "7004b01704ab3d06f2175b2075f7aa724d6c1bf9b02f46ce24da9f487125f69e",
    REL_WITNESS_R14B:
        "b63771f9f04d2e048c0692dec1edf6a20c48d40703ed620a3574ccde6b295a99",
    REL_PROBE_R18:
        "a49441acacd7ac492960b7e604d1e31a37174e9d9a97b4a24ebddc2e3551111d",
    REL_TYPOLOGY:
        "6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b53283681bc80",
    RAW_FILES["applied-top-i1"]:
        "044486bb2003d3e5b5ec2fb9a31c19f6d71c814aaab480041edaa88765eba0ef",
    RAW_FILES["prep1-top-i1"]:
        "d2c1b7dafac3a24984eeac07a0b682edd2d6f38f757078f9590ae8094c070f24",
    RAW_FILES["applied-top-i2"]:
        "11edbc4d575cbd65f59af81cc54e0360b6b40c41b4ae947b93253628939f6639",
    RAW_FILES["prep1-top-i2"]:
        "42d7c2e8f2cccf62f4d33627f4890cb6e118b9529aef0a96df82a1060502588b",
    RAW_FILES["applied-top-i3"]:
        "80961e4e0c5cccddeaa4cbb3a1fb4805e74a7093a87ce1fd866f60233a094cd4",
    RAW_FILES["prep1-top-i3"]:
        "1765d865ba6a1f3e319f8a0af948211dbe8aacea7bc3f333b6dd37eaa5423e44",
    RAW_FILES["applied-bottom-i1"]:
        "1aa661431fac5c78202963c79087b68b4fc41de9c74cc3a103997d3962b12f47",
    RAW_FILES["prep1-bottom-i1"]:
        "e5e6a5d975475c9a1f41f388ddfda5d47341e0423477e1294df8ad414f130c36",
    RAW_FILES["applied-bottom-i2"]:
        "c95f16200f4863fdc5eb989124403b8db0c3db81b400b714fb04062628d9f4b7",
    RAW_FILES["prep1-bottom-i2"]:
        "3ecf232c0d1d165991c4e572d2d380a07478188e08339c2d6290e24ee36bda43",
    RAW_FILES["applied-bottom-i3"]:
        "a852215f38babfaf5cada9a3d3087d05cb6cd0ef596bc673ed71671af4e17df8",
    RAW_FILES["prep1-bottom-i3"]:
        "1691b7aa58cc22e33aeb6388133d64b5cf5a9a06258db0e98e5bc54aaba3a783",
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
    "applied-top-i1": "044486bb",
    "prep1-top-i1": "d2c1b7da",
    "applied-bottom-i1": "1aa66143",
    "prep1-bottom-i1": "e5e6a5d9",
    "applied-top-i2": "11edbc4d",
    "prep1-top-i2": "42d7c2e8",
    "applied-bottom-i2": "c95f1620",
    "prep1-bottom-i2": "3ecf232c",
    "applied-top-i3": "80961e4e",
    "prep1-top-i3": "1765d865",
    "applied-bottom-i3": "a852215f",
    "prep1-bottom-i3": "1691b7aa",
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
    "r14–r19 盲读同一批文件）+observation-guidance-r20.md"
    "（9cdac9ed，r19 指引基座+§4 (iii-a) 逐字承继+r18 §5B 黑点仪器"
    "注记节全文转录的合成产物、"
    "本轮唯一判读依据；旗 ID 前缀 "
    "R20T-/R20B- 随指引 §6 落盘固化——本轮指引本体即为 r20 前缀、"
    "无需派发层覆盖，per r20-prep-record protocol_amendment.naming；"
    "reader-r20-{top,bottom}-i{1,2,3} 为派发指令命名）+起始序号+v1.2 "
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
    "多实例协议的前提，亦为组合轮可加性裁决有效性的前提，per r20-prep-"
    "record read_prohibition_note）")

#: 派发模式结构化记录（R20=stage2 组合轮（轴3+轴2 指引合成）：每格
#: 3 实例、两波次串行保序；派发结构与 r17–r19 同构，协议侧零新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1",
    "flag_id_continuity": {
        "top-i1": "applied R20T-001..003；prep1 R20T-004..008（跨板连续）",
        "top-i2": "applied R20T-001..003；prep1 R20T-004..008（跨板连续）",
        "top-i3": "applied R20T-001..003；prep1 R20T-004..006（跨板连续）",
        "bottom-i1": "applied R20B-001..003；prep1 R20B-004..006（跨板连续）",
        "bottom-i2": "applied R20B-001..002；prep1 R20B-003..004（跨板连续）",
        "bottom-i3": "applied R20B-001..002；prep1 R20B-003..004（跨板连续）",
    },
    "flag_id_continuity_note": (
        "r20 实测=6 实例全部同实例跨板连续（与 r20-prep-record "
        "protocol_amendment.naming「同实例跨板连续」声明全部相符——"
        "本轮 6 智能体各包两板、编号跨板连续；与 r19 实测的混合行为"
        "（仅 top-i3 连续、其余各自从头编号）对照如实登记）——编排侧"
        "仍把实例非弃权/弃权清单与逐旗明细按 (state, flag_id) 限定，"
        "跨板同号不混淆"),
    "diff_note": ("R19→R20 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮单变量="
                  "判读指引合成（§5B+(iii-a) 两增补并集：§5B 自 r18 指引"
                  "逐字转录+§4(iii-a) 随 r19 基座逐字承继；渲染零变更="
                  "renders-r14b "
                  "四图字节复用；指引=observation-guidance-r20.md"
                  " 机械变换产物、§2–§7 除 §5B 新增节外与 r19 逐字相等"
                  "（分段断言复核），轮次标识同步+本轮变更声明重写+§6 "
                  "示例前缀机械替换；判据文本零改动"
                  "）；实例群"
                  "重抽为轮际比较固有混杂（per axis-plan "
                  "comparison_rule.drift_confound_note 显式容忍）；协议"
                  "侧零新增条款"
                  "（v1.2 沿用：派发指令继续含纯 Read 直读硬性条款，"
                  "12/12 派次自述「未读取盘上任何其他文件」，见 "
                  "reader_tool_evidence；指引 §2–§7 实质判据通道除 "
                  "§5B+(iii-a) 预注册并集外零变更；"
                  "GT/阈值零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R20 十二派次全部以 Read 工具"
    "直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何其他文件」"
    "（12/12 逐字摘录在案 reader_tool_evidence）；applied/prep1-top-i1 "
    "另自述「未与任何其他图像做跨图比对推断」、prep1-top-i3/"
    "prep1-bottom-i2 另自述「不跨图合并、不跨图推断」、applied/"
    "prep1-bottom-i3 另自述「不跨图合并、不跨图推断」（两板同图同判"
    "自述）；§5B 措辞 notes 级援引=4/12 派次、§4(iii-a) 措辞 notes 级"
    "援引=4/12 派次（两计数分开记、互不合并；逐件摘录见 hypothesis_"
    "test.mechanism_observation.criterion_citation_observation；"
    "applied/prep1-top-i1 黑点弃权自述明写「仪器注记 §5B 不作为判据」"
    "=§5B 反指示声明遵守实例，如实分列）；全部判读"
    "输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零诊断/零探针"
    "件/零 legend/零其他文件接触=非盲读违规；本轮唯一操纵因子=判读"
    "指引合成（§5B+(iii-a) 并集；渲染零变更=renders-r14b 四图字节"
    "复用、仪器侧零变动；实例群全部重抽为轮际比较固有混杂，per "
    "axis-plan comparison_rule.drift_confound_note 显式容忍）；跨轮"
    "实例不同+轮内实例差异=混杂因素照旧声明（本轮每视角 n=3 给出轮内"
    "实例间范围，轮内样本仍小、development 域只描述不断言）。输出格式"
    "实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件=缩进格式"
    "冻结原始判读件、本轮零改动直读（direct JSON 解析；围栏剥离本先例"
    "不适用——12 件均为裸 JSON 文本；12 件 parse 校验全部通过、均非"
    "盲读违规）")

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
    "本轮指引=observation-guidance-r20.md（9cdac9ed，由 r19 指引 "
    "8633bda5 机械变换生成、本轮唯一判读依据，per r20-prep-record "
    "guidance_reuse：mode=mechanical_transform_derive、edit_list 7 项"
    "逐字登记、§2–§7 分段逐字保留断言复核在案）：§2 类别枚举/§3 位置"
    "口径/§3A 示例（含示例 c）/§4 置信度与弃权整段（含量化判据 "
    "(i)(ii)(iii) 原文、(iii) 接触性判据原句、(iii-a) 可操作分辨条款"
    "全文、三路出口、反放宽条款、confidence 定义、对照说明块）/§5/§5A/"
    "§6/§7 判据文本逐字承 r19（§4(iii-a) 随基座承继、零改动）；变更="
    "轮次标识机械同步（标题/"
    "声明日期 2026-09-09/round_id_constant "
    "2026-09-09-r20/本轮性质行/示例 reader_id/示例旗 ID 前缀）+本轮变更"
    "声明节重写+「## 6. 输出格式」标题前插入 §5B 黑点仪器注记节"
    "（文本=observation-guidance-r18.md §5B 段全文逐字转录、零改写、"
    "content_sha256=19ecdb42 与 r18-prep-record s67 edit 8 跨代交叉锚"
    "一致——黑点物理来源仪器事实注记：成对孤立黑点=非电镀机械定位孔"
    "渲染、焊盘中心圆盘=通孔钻孔渲染；含反指示声明「不构成任何判据、"
    "期望清单或『应判为正常/无需报告』的指示」；黑点相关现象的旗标"
    "判定仍按 §2/§3A/§4 独立执行）；§6 示例旗 ID 前缀 "
    "R20T-/R20B- 随指引落盘固化（机械替换，"
    "无需派发层覆盖）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 20 轮迭代"
    "（development 域 stage2 组合轮（轴3+轴2 判读指引合成，渲染"
    "零变更字节复用）：迭代轮不得冒充留出证据；执行 axis-experiment-plan-"
    "r17-r20（b6ec6467 冻结件）stage2 R20，用户 2026-09-09「三条轴"
    "单独/组合/全组合尝试，选择收益最大的继续」（user_directive_note "
    "在案）；执行合法性=dev-r19 combination_decision_application 在案"
    "（early_stop_shortcut 触发+排序 r19_axis3 第一/r18_axis2 第二））。")

INSTRUMENT_NATURE = (
    "stage2 组合轮（轴3+轴2 判读指引合成；渲染零变更轮）：仪器变更=无"
    "（renders-r14b 四图"
    "字节复用=与 r14–r19 盲读同一批文件；四 PNG 盘上 sha="
    "witness-r14b 登记值=prep-record instrument_change.renders 登记值 "
    "fail-closed 三方一致；instrument_change.changed=false 已预注册，"
    "no_instrument_change=true）+判读指引=observation-guidance-r20.md"
    "（9cdac9ed，r19 指引基座+§5B 自 r18 逐字转录的合成产物、§2–§7 "
    "除 §5B 新增节外与 r19 逐字相等（§4(iii-a) 随基座承继、判据文本"
    "零改动），唯一实质变更=§5B+(iii-a) 两增补并集"
    "（判读指引侧合成、两轴变更同时施加））+GT/阈值零"
    "变更（13 条冻结；APR-0011 与 CONTAINMENT_MIN/AREA_RATIO_MAX 只作"
    "口径引用）+协议零变更（v1.1+v1.2 维持）：唯一实验变量=指引合成 "
    "guidance-combo-s5b-plus-s4-iiia-union（per r20-prep-record "
    "manipulated_factor；axis_id="
    "A3_criterion_contact_clarification+A2_blackdot_instrument_annotation；"
    "changed_variables 单一复合变量、instrument_change=false）")

#: 预注册主通道三分判据所用基线（零覆盖；per r20-prep-record
#: hypothesis_test.adjudication 原文：supported=R20 四元组在冻结
#: comparison_rule.ordering 字典序下不劣于最优单轴 r19 实测
#: (0.461538,0.571429,4,0.211111)；reject=M1 ≥0.771429 或 G1/G2 任一
#: 破坏；marginal=未达 supported 但 M1 <0.771429 且 G1/G2 维持）。
#: 基线数字 live 重放/装载（M1/M2=同一聚合逻辑对 run-r16 内嵌实例记录
#: 双侧复算、不手工抄数；r19 四元组=dev-r19 measured_rows 装载+
#: run-r19 内嵌实例记录 live 复算交叉核对）并与下列在案登记值交叉
#: 核对（fail-closed，不符即中止）：(27,35)=0.771429（axis-plan
#: baselines_registered.r16_baseline 在案）。
BASE16_TOP_AGGREGATE_REGISTERED = {"abstain": 27, "flags": 35}
#: M1 侧阈值（6 位定点整数交叉相乘比较，避免浮点）：reject 门
#: M1 ≥0.771429（r16 基线）；marginal 带 M1 <0.771429。
REJECT_M1_MIN_6DP = 771429
#: r19 最优单轴四元组登记值（supported 门基准；M1/M2/M4=6 位小数、
#: M3=整数；dev-r19 measured_rows 装载+run-r19 live 复算双重交叉核对）。
R19_ROW_REGISTERED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                      "M4": 0.211111}
#: bottom 侧观察基线（M2；per axis-plan baselines_registered.r16_baseline
#: .M2_bottom_aggregate_abstain_rate=0.857143；live 重放交叉核对
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
#: r16=10；r20-prep-record 经 typology 链锚在分型件 matrix.round_totals
#: 双向核对；r16=10 全 top
#: （r16_contact_by_view 在案）；本件登记基线与 r20 实测对照）。
CONTACT_CHAIN_PRIOR = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
R16_CONTACT_BY_VIEW_REGISTERED = {"top": 10, "bottom": 0}
#: 黑点族链基线（分型件 rubric 口径在案：r13=9、r14=14、r15=8、r16=12；
#: r18=13（run-r18 实测+dev-r18 登记装载交叉核对）；r19=4（run-r19
#: 实测+dev-r19 measured_rows 装载交叉核对）；黑点判正常派次链
#: （分型件 blackdot_dispatch 口径）：r15=3、r16=2；r18=2、r19=3
#: （各自 run 实测装载交叉核对）。
BLACKDOT_CHAIN_PRIOR = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
BLACKDOT_JUDGED_NORMAL_PRIOR = {"r15": 3, "r16": 2}
#: r18 对照登记值（存在性其他族 12；黑点转非弃权旗 3；dev-r18/
#: run-r18 实测装载交叉核对——机制观察「三族计数 r18/r19 双基线」
#: 的 r18 侧对照行）。
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
#: r19 对照行/参照计数（run-r19 在案实测：dev-r19 measured_rows 装载
#: +run-r19 内嵌实例记录/分型计数 live 复算交叉核对——机制观察
#: 「三族计数 r18/r19 双基线」的 r19 侧对照行与 supported 门基准）。
R19_REFERENCE_REGISTERED = {
    "M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111,
    "contact": 4, "existence_blackdot": 4, "existence_other": 14,
    "judged_normal_dispatches": 3,
    "top_typology": {"contact": 5, "existence": 13, "other_layer": 0},
}

#: bottom 侧 G1 守门逐实例登记表（bottom courtyard 类非弃权旗；
#: 程序实测与本表 expected 逐一相等 fail-closed；per r20-prep-record
#: guard_channel「G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15–r19
#: 在案）」原文——r20 实测 2/0/0=G1 字面破坏（reject_guards 支），
#: 机制=(iii-a) 间隙支把 bottom-i1 孤立焊盘对占位框线极近近邻引导到
#: 「间隙带可辨认→视觉贴近→以 courtyard_crowding 负责任报告」的
#: 非弃权路径（r14–r19 该形态在 bottom 侧从未产生过非弃权 courtyard
#: 旗；守门字面破坏与机制方向并存=如实分列，不影响字母）。
SIDE_OBS_REGISTERED = [
    {"instance": "bottom-i1", "expected": 2,
     "note": ("r15–r19 零非弃权 courtyard→r20 实测 2：applied R20B-003+"
              "prep1 R20B-006 各 1 条（同实例跨板同现象：孤立焊盘对占位"
              "框线极近近邻、「中间仅剩一条细窄但可辨认的背景色间隙带」"
              "→按视觉贴近近邻形态负责任报告=(iii-a) 间隙支路径）——"
              "G1 字面破坏的直接构成")},
    {"instance": "bottom-i2", "expected": 0,
     "note": ("r15–r19 零非弃权 courtyard→r20 实测 0：本轮 bottom-i2 "
              "零 courtyard 类旗标（4 旗=other_advisory 黑点报告 2+"
              "placement_pattern_anomaly 2，两板零弃权）")},
    {"instance": "bottom-i3", "expected": 0,
     "note": ("r15–r19 零非弃权 courtyard→r20 实测 0：本轮 bottom-i3 "
              "4 旗全部=黑点-焊盘接触存在性弃权（(iii)+(iii-a) 残余"
              "弃权支、rubric 族=existence_blackdot）——零 courtyard "
              "类路径")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。applied-top-i2 另自述判据来源、
#: prep1-bottom-i1 另自述零接触 GT、prep1-bottom-i3 另自述同图同判，
#: 如实登记。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅依据给定 PNG 可见内容对 applied-top.png 独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i1",
     "excerpt": "仅依据给定 PNG 可见内容对 prep1-top.png 独立判读，未读取盘上任何其他文件，未与任何其他图像做跨图比对推断"},
    {"source": "applied-top-i2",
     "excerpt": "仅依据给定PNG可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-top-i2",
     "excerpt": "仅依据给定PNG可见内容逐图独立判读，未读取盘上任何其他文件；本图判读不引用、不依赖另一张图的观察"},
    {"source": "applied-top-i3",
     "excerpt": "仅依据 applied-top.png 可见内容独立判读，未读取盘上任何其他文件，未做任何程序化图像处理"},
    {"source": "prep1-top-i3",
     "excerpt": "仅依据 prep1-top.png 可见内容独立判读，未读取盘上任何其他文件，未做任何程序化图像处理，不跨图合并、不跨图推断"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅依据给定 PNG 可见内容独立判读（与前一张图分开独立执行，未做跨图合并推断），未读取盘上任何其他文件"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件，不跨图合并、不跨图推断"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅依据给定 PNG 可见内容逐图独立判读，未读取盘上任何其他文件（指引与图像除外）"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅依据本张 PNG 可见内容独立判读，不跨图合并、不跨图推断；未读取盘上任何其他文件（指引与图像除外）"},
]

#: §4(i) 量化判据「系统性正常→不报告」路径使用证据（bottom 派次
#: reading_notes 逐字摘录；substring fail-closed 校验）——r20 bottom
#: 6 派次均实际使用 §4(i) 量化判据（bottom-i1/i2 黑点=孤立出现+未达
#: 系统性量化判据→报告；bottom-i2 绿色瓣状桥接=满足量化判据→判正常；
#: applied/prep1-bottom-i3 同文=两板逐字节同图的同判自述）。
QUANT_CRITERION_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "其孔径/样式与焊盘体系不一致，未达系统性正常特征量化判据，不判为正常设计特征"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "孤立出现且与占位框线相接，以 other_advisory 报告"},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "该形态在至少 3 条不同边上重复出现且样式一致，按系统性正常特征判据（≥3 处、≥2 条边、形态一致）判为候选常规设计特征（如缝合/热过孔类常规解释），按三路出口第 1 路不报告"},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "该形态在至少 3 条不同边上重复出现且样式一致，按系统性正常特征判据（≥3 处、≥2 条边、形态一致）判为候选常规设计特征（如缝合/热过孔类常规解释），按三路出口第 1 路不报告"},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "焊盘间绿色翼瓣状空隙形态在四条边上大量重复出现、样式与尺寸一致（满足 §4(i) 系统性判据），判为正常设计特征，按三路出口不报告"},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "焊盘间绿色翼瓣状空隙形态在四条边上大量重复出现、样式与尺寸一致（满足 §4(i) 系统性判据），判为正常设计特征，按三路出口不报告"},
]

#: top 弃权理由构成分型（机制观察：14 条 top 弃权旗逐旗按
TOP_ABSTAIN_TYPOLOGY = [
    {"source": "applied-top-i1", "flag_id": "R20T-003", "type": "existence",
     "excerpt": "无法负责任地判定其属于常规机械定位孔设计特征还是应报告的异常图形，故弃权并给出疑似区域",
     "note": "成对孤立黑点（§5B 已证实其物理来源=非电镀机械定位孔渲染、仪器事实）——读侧仍按 §4 存在性判据弃权、notes 自述「仪器注记 §5B 不作为判据」（§5B 反指示声明遵守的在案实例）；rubric 族=existence_blackdot"},
    {"source": "prep1-top-i1", "flag_id": "R20T-006", "type": "existence",
     "excerpt": "无法负责任判定其属带散热 TAB 的常规大焊盘封装图形，还是多焊盘连通的异常桥连形态，亦无法排除其为非图元的着色区域，故弃权并给出疑似区域"},
    {"source": "prep1-top-i1", "flag_id": "R20T-007", "type": "existence",
     "excerpt": "无法负责任地判定其属于常规机械定位孔设计特征还是应报告的异常图形，故弃权并给出疑似区域",
     "note": "同 applied-top-i1 R20T-003（两板同图同判）；rubric 族=existence_blackdot"},
    {"source": "prep1-top-i1", "flag_id": "R20T-008", "type": "existence",
     "excerpt": "当前分辨率下无法负责任确认叠印受阻是否真实存在，故弃权"},
    {"source": "applied-top-i2", "flag_id": "R20T-002", "type": "existence",
     "excerpt": "当前分辨率下无法确认笔画是否被遮挡致辨读受阻，故弃权"},
    {"source": "applied-top-i2", "flag_id": "R20T-003", "type": "contact",
     "excerpt": "既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认轮廓接触/交叠，故弃权",
     "note": "(iii-a) 残余弃权支语言（ courtyard 近邻接触性不可确认）；rubric 族=contact"},
    {"source": "prep1-top-i2", "flag_id": "R20T-005", "type": "existence",
     "excerpt": "当前分辨率下无法确认笔画是否被遮挡致辨读受阻，故弃权"},
    {"source": "prep1-top-i2", "flag_id": "R20T-006", "type": "contact",
     "excerpt": "既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认轮廓接触/交叠，故弃权",
     "note": "同 applied-top-i2 R20T-003（两板同图同判）；rubric 族=contact"},
    {"source": "prep1-top-i2", "flag_id": "R20T-007", "type": "contact",
     "excerpt": "疑似相互连印/接触，但当前分辨率下无法确认是两标注叠压还是相邻分立标注，故弃权",
     "note": "主出口=连印/接触不可确认（是否接触/交叠不可确认口径）；rubric 族因无 contact 怀疑组合命中归 existence_other（两口径分列如实）"},
    {"source": "prep1-top-i2", "flag_id": "R20T-008", "type": "contact",
     "excerpt": "疑有接触/交叠，但该分辨率下既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认，故弃权",
     "note": "主出口=接触性怀疑（(iii-a) 残余弃权支语言）；rubric 族=existence_other（两口径分列如实）"},
    {"source": "applied-top-i3", "flag_id": "R20T-002", "type": "existence",
     "excerpt": "无法排除其属常规引出布线，无法负责任确认可疑改道形态是否存在"},
    {"source": "applied-top-i3", "flag_id": "R20T-003", "type": "other_layer",
     "excerpt": "无法确认其是否越出板框或属正常轮廓图形，亦无法在六类封闭集中负责任归类",
     "note": "主出口=归类不可确认（类别/层归属出口，本轮 other_layer 唯一条）"},
    {"source": "prep1-top-i3", "flag_id": "R20T-005", "type": "existence",
     "excerpt": "无法确认是笔画相互叠压还是仅相邻摆放"},
    {"source": "prep1-top-i3", "flag_id": "R20T-006", "type": "existence",
     "excerpt": "无法排除其属常规引出布线，无法负责任确认可疑改道形态是否存在"},
]

#: 绿色区域语义化方式证据（r17–r19 机制观察延续：bottom 派次 notes
GREEN_SEMANTICS_EVIDENCE = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "绿色区域按仪器注记理解为空隙而非图元，未据此报告",
     "cites_5A": False, "cites_5B": False},
    {"source": "applied-bottom-i2", "instance": "bottom-i2",
     "excerpt": "橙色/绿色配色与黑点按 §5A/§5B 仪器注记仅作事实参考，判定仍按 §2/§3A/§4 独立执行",
     "cites_5A": True, "cites_5B": True},
    {"source": "applied-bottom-i3", "instance": "bottom-i3",
     "excerpt": "焊盘间绿色翼瓣状空隙形态在四条边上大量重复出现、样式与尺寸一致（满足 §4(i) 系统性判据），判为正常设计特征，按三路出口不报告",
     "cites_5A": False, "cites_5B": False},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "绿色区域按仪器注记理解为空隙而非图元，未据此报告",
     "cites_5A": False, "cites_5B": False},
    {"source": "prep1-bottom-i2", "instance": "bottom-i2",
     "excerpt": "橙色/绿色配色与黑点按 §5A/§5B 仪器注记仅作事实参考，判定仍按 §2/§3A/§4 独立执行",
     "cites_5A": True, "cites_5B": True},
    {"source": "prep1-bottom-i3", "instance": "bottom-i3",
     "excerpt": "焊盘间绿色翼瓣状空隙形态在四条边上大量重复出现、样式与尺寸一致（满足 §4(i) 系统性判据），判为正常设计特征，按三路出口不报告",
     "cites_5A": False, "cites_5B": False},
]

#: 黑点族现象证据（r20 黑点族弃权旗 6 条（top-i1 两板 2+bottom-i3
#: 两板 4）+黑点转非弃权旗 6 条（全 bottom：bottom-i1 4+bottom-i2 2）
#: +判正常派次 4 的代表摘录；kind=reading_notes 或 location_evidence；
#: substring fail-closed 校验；延续 r14–r19 黑点族追踪——r20 黑点族
#: 弃权=6（rubric 口径）vs r16=12/r18=13/r19=4 双基线对照、方向性
#: 描述）。
BLACK_DOT_EVIDENCE = [
    {"source": "applied-top-i1", "kind": "location_evidence",
     "flag_id": "R20T-003", "instance": "top-i1", "disposition": "弃权",
     "excerpt": "右上角一个连接器封装轮廓内可见两个实心黑点（全板仅见此一对），按系统性量化判据该形态仅出现 2 处、落在孤立区间",
     "note": "§5B 已证实其物理来源=非电镀机械定位孔渲染（仪器事实）——读侧仍按 §4 存在性判据弃权、notes 自述「仪器注记 §5B 不作为判据」（§5B 反指示声明遵守的在案实例）"},
    {"source": "prep1-top-i1", "kind": "location_evidence",
     "flag_id": "R20T-007", "instance": "top-i1", "disposition": "弃权",
     "excerpt": "右上角一个连接器封装轮廓内可见两个实心黑点（全板仅见此一对），按系统性量化判据该形态仅出现 2 处、落在孤立区间",
     "note": "同 applied-top-i1 R20T-003（两板同图同判）"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R20B-001", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "既辨认不出二者之间连续的间隙带，也无法确凿辨认黑点边缘侵入焊盘铜环内部，真实接触与视觉贴近无法负责任区分",
     "note": "(iii)+(iii-a) 残余弃权支（按接触性判据对存在性弃权）；rubric 族=existence_blackdot"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R20B-002", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "既无可辨认的连续间隙带、亦无可辨认的侵入证据，接触与否无法负责任区分，按接触性判据弃权",
     "note": "同上（同一封装区下方第二枚黑点）"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R20B-003", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "既辨认不出二者之间连续的间隙带，也无法确凿辨认黑点边缘侵入焊盘铜环内部，真实接触与视觉贴近无法负责任区分",
     "note": "同 applied-bottom-i3 R20B-001（两板同图同判）"},
    {"source": "prep1-bottom-i3", "kind": "location_evidence",
     "flag_id": "R20B-004", "instance": "bottom-i3", "disposition": "弃权",
     "excerpt": "既无可辨认的连续间隙带、亦无可辨认的侵入证据，接触与否无法负责任区分，按接触性判据弃权",
     "note": "同 applied-bottom-i3 R20B-002（两板同图同判）"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R20B-001", "instance": "bottom-i1", "disposition": "非弃权报告",
     "excerpt": "黑点边缘与该框线直接相接并略有侵入，周边无同类黑点组成的阵列分布",
     "note": "(iii-a) 侵入支（直接相接+侵入证据→按接触/交叠处理照常报告）+§4(ii) 孤立出现——r14–r19 同位黑点-焊盘/框线贴近形态的非弃权报告路径延续（r19 见 prep1-bottom-i2 首现）"},
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R20B-002", "instance": "bottom-i1", "disposition": "非弃权报告",
     "excerpt": "黑点边缘与该框线直接相接并略有侵入，与上方黑点形态一致但仅两处、未构成跨阵列的系统性重复",
     "note": "同上（上方第二枚黑点）"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R20B-004", "instance": "bottom-i1", "disposition": "非弃权报告",
     "excerpt": "黑点边缘与该框线直接相接并略有侵入，周边无同类黑点组成的阵列分布",
     "note": "同 applied-bottom-i1 R20B-001（两板同图同判）"},
    {"source": "prep1-bottom-i1", "kind": "location_evidence",
     "flag_id": "R20B-005", "instance": "bottom-i1", "disposition": "非弃权报告",
     "excerpt": "黑点边缘与该框线直接相接并略有侵入，与上方黑点形态一致但仅两处、未构成跨阵列的系统性重复",
     "note": "同 applied-bottom-i1 R20B-002（两板同图同判）"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R20B-001", "instance": "bottom-i2", "disposition": "非弃权报告",
     "excerpt": "两个孤立实心黑色小圆点（一在两组椭圆焊盘封装右上侧、一在其下方封装左上侧），全板仅此一处成对出现、无其他同类黑点",
     "note": "§4(ii) 孤立+样式不一致归兜底类报告（非接触路径）"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R20B-003", "instance": "bottom-i2", "disposition": "非弃权报告",
     "excerpt": "两个孤立实心黑色小圆点（一在两组椭圆焊盘封装右上侧、一在其下方封装左上侧），全板仅此一处成对出现、无其他同类黑点",
     "note": "同 applied-bottom-i2 R20B-001（两板同图同判）"},
    {"source": "applied-top-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i2", "disposition": "判正常不报告",
     "excerpt": "右上封装内两枚成对孤立实心黑点、左下大圆轮廓内一圆一方两焊盘的孤立焊盘对、以及板面散布的尺寸一致小圆过孔，按§4存在性判据与通用PCB域常规图形解释（安装孔/电池触点焊盘/过孔）判为正常设计特征，均未报告"},
    {"source": "prep1-top-i2", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i2", "disposition": "判正常不报告",
     "excerpt": "右上封装内两枚成对孤立实心黑点、左下大圆轮廓内一圆一方两焊盘的孤立焊盘对、以及板面散布的尺寸一致小圆过孔，按§4存在性判据与通用PCB域常规图形解释（安装孔/电池触点焊盘/过孔）判为正常设计特征，均未报告"},
    {"source": "applied-top-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i3", "disposition": "判正常不报告",
     "excerpt": "右上角两处成对实心黑点：成对出现、形态尺寸一致、位于连接器封装占位区内，结合通用 PCB 域知识判为安装/机械定位孔类正常设计特征，按三路出口第（1）路不报告"},
    {"source": "prep1-top-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i3", "disposition": "判正常不报告",
     "excerpt": "右上角两处成对实心黑点：成对出现、形态尺寸一致、位于连接器封装占位区内，结合通用 PCB 域知识判为安装/机械定位孔类正常设计特征，按三路出口第（1）路不报告"},
]

#: 黑点族弃权旗登记表（6 条；程序校验：存在性/abstain=True/category=
#: 登记值逐一相等，不符即中止；(state, flag_id) 限定；top-i1 两板 2+
#: bottom-i3 两板 4；分型件 rubric 口径=r20 6 vs r16 12/r18 13/r19 4
#: （axis-plan/dev-r18/dev-r19 在案 M3 链）。
BLACK_DOT_FLAGS = [
    ("top-i1", "applied", "R20T-003", "other_advisory"),
    ("top-i1", "prep1", "R20T-007", "other_advisory"),
    ("bottom-i3", "applied", "R20B-001", "other_advisory"),
    ("bottom-i3", "applied", "R20B-002", "other_advisory"),
    ("bottom-i3", "prep1", "R20B-003", "other_advisory"),
    ("bottom-i3", "prep1", "R20B-004", "other_advisory"),
]

#: 黑点转非弃权旗登记表（6 条；rubric unit=弃权旗、非弃权旗不分型，
#: 本表为机制观察「黑点转非弃权旗计数」的登记口径（对象含黑点词的
#: 非弃权旗、逐条摘录）；全 bottom（bottom-i1 两板 4=黑点-占位框线
#: 直接相接并略有侵入按 (iii-a) 侵入支接触/交叠报告+bottom-i2 两板
#: 2=孤立钻孔样异常按 §4(ii) 兜底类报告）——r19（bottom 2）的
#: 非弃权报告路径在本轮放大为 6 条，如实登记）。
BLACK_DOT_NON_ABSTAIN_FLAGS = [
    ("bottom-i1", "applied", "R20B-001", "other_advisory"),
    ("bottom-i1", "applied", "R20B-002", "other_advisory"),
    ("bottom-i1", "prep1", "R20B-004", "other_advisory"),
    ("bottom-i1", "prep1", "R20B-005", "other_advisory"),
    ("bottom-i2", "applied", "R20B-001", "other_advisory"),
    ("bottom-i2", "prep1", "R20B-003", "other_advisory"),
]

#: §4(iii-a) 逐旗落支登记表（机制观察核心：判据相关旗逐旗理由对照
#: 条款三支的落支分布——branch3=残余弃权支（既无可辨认间隙带亦无可
#: 辨认侵入证据→按 (iii) 原文弃权）、branch2=侵入支（边缘直接相连/
#: 明显侵入→按「接触/交叠」处理并照常输出旗标）、branch1=间隙支
#: （可辨认间隙带→视觉贴近→继续 (i)(ii) 与三路出口判定）；r20 实测
#: 旗级「(iii-a)」/「分支(」字面援引=0（cited 全 False=按旗级理由
#: 语言归类、如实注明；援引计数见 IIIA_*_REGISTERED）；逐旗 excerpt
#: 逐字 substring fail-closed 校验）。
IIIA_BRANCH_ROWS = [
    {"source": "applied-bottom-i1", "flag_id": "R20B-003", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "中间仅剩一条细窄但可辨认的背景色间隙带，呈明显拥挤的近邻形态",
     "note": "无字面援引；间隙支路径（可辨认间隙带→视觉贴近→按 courtyard_crowding 负责任报告）——G1 守门字面破坏的直接构成（r14–r19 bottom 侧首现非弃权 courtyard 旗）"},
    {"source": "prep1-bottom-i1", "flag_id": "R20B-006", "abstain": False,
     "branch": "branch1_gap_report", "cited": False,
     "excerpt": "中间仅剩一条细窄但可辨认的背景色间隙带，呈明显拥挤的近邻形态",
     "note": "同 applied-bottom-i1 R20B-003（两板同图同判）"},
    {"source": "applied-bottom-i1", "flag_id": "R20B-001", "abstain": False,
     "branch": "branch2_intrusion_report", "cited": False,
     "excerpt": "黑点边缘与该框线直接相接并略有侵入",
     "note": "无字面援引；侵入支（直接相接并略有侵入→按接触/交叠处理照常输出旗标）"},
    {"source": "applied-bottom-i1", "flag_id": "R20B-002", "abstain": False,
     "branch": "branch2_intrusion_report", "cited": False,
     "excerpt": "黑点边缘与该框线直接相接并略有侵入",
     "note": "同上（上方第二枚黑点）"},
    {"source": "prep1-bottom-i1", "flag_id": "R20B-004", "abstain": False,
     "branch": "branch2_intrusion_report", "cited": False,
     "excerpt": "黑点边缘与该框线直接相接并略有侵入",
     "note": "同 applied-bottom-i1 R20B-001（两板同图同判）"},
    {"source": "prep1-bottom-i1", "flag_id": "R20B-005", "abstain": False,
     "branch": "branch2_intrusion_report", "cited": False,
     "excerpt": "黑点边缘与该框线直接相接并略有侵入",
     "note": "同 applied-bottom-i1 R20B-002（两板同图同判）"},
    {"source": "applied-top-i2", "flag_id": "R20T-003", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认轮廓接触/交叠",
     "note": "无字面援引；按旗级理由语言归类（notes 级该派次有「近邻形态按§4(iii-a)可操作分辨条款执行」援引）"},
    {"source": "prep1-top-i2", "flag_id": "R20T-006", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认轮廓接触/交叠",
     "note": "同 applied-top-i2 R20T-003（两板同图同判）"},
    {"source": "prep1-top-i2", "flag_id": "R20T-008", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "该分辨率下既无可辨认的连续间隙带亦无可辨认的侵入证据，无法负责任确认",
     "note": "无字面援引；按旗级理由语言归类（同上 notes 级援引）"},
    {"source": "applied-bottom-i3", "flag_id": "R20B-001", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既辨认不出二者之间连续的间隙带，也无法确凿辨认黑点边缘侵入焊盘铜环内部",
     "note": "无字面援引；(iii)+(iii-a) 残余弃权支（按接触性判据对存在性弃权；notes 自述「按 §4(iii)/(iii-a) 弃权」）"},
    {"source": "applied-bottom-i3", "flag_id": "R20B-002", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既无可辨认的连续间隙带、亦无可辨认的侵入证据，接触与否无法负责任区分",
     "note": "同上（同一封装区下方第二枚黑点）"},
    {"source": "prep1-bottom-i3", "flag_id": "R20B-003", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既辨认不出二者之间连续的间隙带，也无法确凿辨认黑点边缘侵入焊盘铜环内部",
     "note": "同 applied-bottom-i3 R20B-001（两板同图同判）"},
    {"source": "prep1-bottom-i3", "flag_id": "R20B-004", "abstain": True,
     "branch": "branch3_residual_abstain", "cited": False,
     "excerpt": "既无可辨认的连续间隙带、亦无可辨认的侵入证据，接触与否无法负责任区分",
     "note": "同 applied-bottom-i3 R20B-002（两板同图同判）"},
]

#: §4(iii-a) 间隙支（branch1）notes 级落支证据（bottom-i1 两派次
#: notes 自述「间隙带可辨认，按视觉贴近的近邻形态以 courtyard_crowding
#: 报告」=间隙支负责任报告路径；旗级落支 2 条与之对应；substring
#: fail-closed 校验）。
IIIA_NOTES_BRANCH1_ROWS = [
    {"source": "applied-bottom-i1", "instance": "bottom-i1",
     "excerpt": "间隙带可辨认，按视觉贴近的近邻形态以 courtyard_crowding 报告"},
    {"source": "prep1-bottom-i1", "instance": "bottom-i1",
     "excerpt": "间隙带可辨认，按视觉贴近的近邻形态以 courtyard_crowding 报告"},
]

#: placement/孤立图形类旗标处置证据（逐字摘录；substring fail-closed
#: 校验）——r20 板内孤立焊盘组跨实例/跨板处置分化延续：bottom-i1
#: 两板以 courtyard_crowding 报告占位框线极近近邻（间隙支路径）、
#: bottom-i2 两板以 placement_pattern_anomaly 报告孤立焊盘组偏离
#: 周边模式（本轮 placement 类唯一非弃权报告）、bottom-i3 两板判
#: 正常（中心电镀通孔焊盘正常两焊盘图形）、top-i1 两板 notes 判
#: 正常（§5B(c) 孤立焊盘对中心小圆盘=通孔钻孔渲染），如实单列。
PLACEMENT_DISPOSITION_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "location_evidence",
     "flag_id": "R20B-003", "instance": "bottom-i1", "verdict": "非弃权",
     "phenomenon": "板内孤立焊盘对（圆焊盘+方焊盘，各带绿色占位框线）",
     "excerpt": "板内右中部一对孤立焊盘（左为圆形、右为方形，各带绿色占位框线）的框线边缘极近相对"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i1", "verdict": "非弃权",
     "phenomenon": "同上（两板同图同判）",
     "excerpt": "右中部孤立焊盘对占位框线的极近近邻形态（间隙带可辨认，按视觉贴近的近邻形态以 courtyard_crowding 报告）"},
    {"source": "applied-bottom-i2", "kind": "location_evidence",
     "flag_id": "R20B-002", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "板内孤立二焊盘组件（圆焊盘围热隔离型空隙+方焊盘）",
     "excerpt": "板内右部空旷铺铜区中央孤立放置一组两焊盘图形（一带绿色瓣状的圆形焊盘、一带瓣状的方形焊盘），而全板其余所有封装图形均沿四边边缘成排放置"},
    {"source": "prep1-bottom-i2", "kind": "location_evidence",
     "flag_id": "R20B-004", "instance": "bottom-i2", "verdict": "非弃权",
     "phenomenon": "同上（两板同图同判）",
     "excerpt": "板内右部空旷铺铜区中央孤立放置一组两焊盘图形（一带绿色瓣状的圆形焊盘、一带瓣状的方形焊盘），而全板其余所有封装图形均沿四边边缘成排放置"},
    {"source": "applied-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘对（中心电镀通孔焊盘正常图形）",
     "excerpt": "右下区内孤立的一圆一方焊盘对为中心电镀通孔焊盘的正常两焊盘图形，未见伴生异常形态"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "flag_id": None, "instance": "bottom-i3", "verdict": "判正常不报告",
     "phenomenon": "同上（两板同图同判）",
     "excerpt": "右下区内孤立的一圆一方焊盘对为中心电镀通孔焊盘的正常两焊盘图形，未见伴生异常形态"},
    {"source": "applied-top-i1", "kind": "reading_notes",
     "flag_id": None, "instance": "top-i1", "verdict": "判正常不报告",
     "phenomenon": "板内孤立焊盘对（§5B(c) 仪器注记路径）",
     "excerpt": "左下有一个圆形封装（含一圆形、一方形孤立焊盘对，按 §5B(c) 仪器注记其中心小圆盘为通孔钻孔渲染，未见异常，不报告）"},
]

#: reroute 类旗标逐旗登记表（r12 假设通道被动追踪延续，零期望；
#: 摘录与子串命中均须与 reader-raw 原文实测一致——fail-closed）。
REROUTE_ADJUDICATION = [
    {"source": "applied-top-i3", "flag_id": "R20T-002", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("似见一段走线呈窄回折/钩形绕行，但当前分辨率"
                           "下无法排除其属常规引出布线"),
     "adjudication": "abstain_existence",
     "note": ("弃权旗（存在性出口）：「等长|蛇形」子串零命中；"
              "location_evidence 明写「无法负责任确认可疑改道形态是否"
              "存在」，按 §4 存在性判据弃权")},
    {"source": "prep1-top-i3", "flag_id": "R20T-006", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("似见一段走线呈窄回折/钩形绕行，但当前分辨率"
                           "下无法排除其属常规引出布线"),
     "adjudication": "abstain_existence",
     "note": ("同 applied-top-i3 R20T-002（两板同图同判、同旗号位置"
              "R20T-006）；「等长|蛇形」子串零命中")},
]

#: reroute 类旗标产量链基线（r8–r19 在案；本轮 r20 实测=2；
#: r16=2/r17=1/r18=3/r19=3 经 run-reader.flag_count 在案字段 live 核对）。
REROUTE_CHAIN_PRIOR = {"r8": 1, "r9": 0, "r10": 2, "r11": 3, "r12": 3,
                       "r13": 2, "r14": 1, "r15": 4, "r16": 2, "r17": 1,
                       "r18": 3, "r19": 3}
MISUSE_CHAIN_PRIOR = {"r10": 2, "r11": 1, "r12": 0, "r13": 1, "r14": 0,
                      "r15": 1, "r16": 0, "r17": 0, "r18": 0, "r19": 0}


def _fail(msg: str) -> None:
    print(f"[s74-cal-r20] FAIL: {msg}")
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
            "r20-prep-record bottom_view_note 在案）")
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
                     " frame_box_pct_r5（R5 仪器像素界重投影口径；r20 "
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
                "r20 实测 flag_id 编号行为=6 实例全部同实例跨板连续"
                "（与 r20-prep-record naming「同实例跨板连续」声明全部"
                "相符；对照 r19 实测混合行为如实登记）——abstain_ids/"
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

    本轮 12 格全部≥1 旗（无零旗标实例）：top/bottom 两视角弃权率全部
    有定义、中位数=排序后第 2（item 5 零分母 None 口径本轮未触发）。
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
                 "三分判据（supported=R20 四元组在冻结 comparison_rule."
                 "ordering 字典序下不劣于最优单轴 r19 (0.461538,0.571429,"
                 "4,0.211111) / marginal=未达 supported 但 M1 <0.771429 "
                 "且 G1/G2 维持 / reject=M1 ≥0.771429 或 G1/G2 任一破坏）"
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
                       "r19": "not_met（在案）",
                       "r20": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
                              run_r19: dict, inst_blocks: list,
                              inst_replays: dict) -> dict:
    """通道归因小节（vs R19；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R15/R16/R17/R18/R19 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r15_replays = replay_round_instances(run_r15)
    r16_replays = replay_round_instances(run_r16)
    r17_replays = replay_round_instances(run_r17)
    r18_replays = replay_round_instances(run_r18)
    r19_replays = replay_round_instances(run_r19)
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R20 {key} 通道重放与 compare_v3 对拍不一致")

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
    # r15–r19=fresh 重放并与在案登记逐一交叉核对，r20=本轮 fresh 重放）
    geo_r15 = pick("area_ratio_rejected", r15_replays, None)
    geo_r16 = pick("area_ratio_rejected", r16_replays, None)
    geo_r17 = pick("area_ratio_rejected", r17_replays, None)
    geo_r18 = pick("area_ratio_rejected", r18_replays, None)
    geo_r19 = pick("area_ratio_rejected", r19_replays, None)
    geo_r20 = pick("area_ratio_rejected", inst_replays, inst_blocks)
    cat_r15 = pick("category_mismatch", r15_replays, None)
    cat_r16 = pick("category_mismatch", r16_replays, None)
    cat_r17 = pick("category_mismatch", r17_replays, None)
    cat_r18 = pick("category_mismatch", r18_replays, None)
    cat_r19 = pick("category_mismatch", r19_replays, None)
    cat_r20 = pick("category_mismatch", inst_replays, inst_blocks)
    view_r15 = pick("view_gate", r15_replays, None)
    view_r16 = pick("view_gate", r16_replays, None)
    view_r17 = pick("view_gate", r17_replays, None)
    view_r18 = pick("view_gate", r18_replays, None)
    view_r19 = pick("view_gate", r19_replays, None)
    view_r20 = pick("view_gate", inst_replays, inst_blocks)
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

    n_top_nonabstain = sum(
        1 for b in inst_blocks
        if b["_instance"].startswith("top")
        for f in b["reader_flags"] if not f["abstain"])
    geo_change = (
        "几何门通道（R19→R20）：面积比出局条目 %d→%d（渲染零变更轮内"
        "top 非弃权旗与同态 GT ≥0.5 containment 交叠条目的几何门计数"
        "如实登记；本轮 top 非弃权旗 %d 条、几何门=%d 条；跨轮实例群漂移"
        "混杂照旧声明，只描述不断言。"
        % (len(geo_r19), len(geo_r20), n_top_nonabstain, len(geo_r20)))
    cat_change = (
        "类别门通道（R19→R20）：类别不符出局条目 %d→%d（r16 在案 1 条="
        "prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3（containment "
        "0.848147、面积比 1.529072），r17/r18 重放=0 条、r19 重放=2 条"
        "（run-r19 在案：applied-top-i2 R19T-004 silk×GT-REVC-AP-6-R2LED2"
        "+prep1-top-i3 R19T-009 other_advisory×GT-REVC-P1-L1NB），r20 "
        "重放=%d 条；"
        "r11 唯一原发条目 R11T-012↔GT-REVC-AP-8-R1Q2 语境下逐轮计数如实"
        "登记；跨轮实例群漂移混杂照旧声明，只描述不断言。"
        % (len(cat_r19), len(cat_r20), len(cat_r20)))

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
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→"
                 "r14=1→r15=0→r16=0→r17=0→r18=0→r19=0→r20=%d（r14 回升未"
                 "延续、r15–r20 维持低位：top 非弃权旗与同态 GT ≥0.5 "
                 "containment 交叠条目如实计数）；类别门 r6=1→r7=0→r8=1→"
                 "r9=0→r10=0→"
                 "r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=2→"
                 "r20=%d"
                 "（r11 唯一条目 R11T-012↔AP-8 无再现；r16 1 条=r16 在案、"
                 "r17–r20 逐轮如实计数）"
                 % (len(geo_r20), len(cat_r20))),
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
            "ref": {"path_rel": REL_PREP_R20, "sha256": _sha(REL_PREP_R20)},
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
            "source_of_r15_r16_r17_r18_r19_detail": (
                "calibration-run-r15.json / calibration-run-r16.json / "
                "calibration-run-r17.json / calibration-run-r18.json / "
                "calibration-run-r19.json 内嵌 "
                "reader_flags/gt_entries/flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45/s47/s49/s53/s55/s58/"
                "s64/s68/s71 deviation_note 口径：本轮对 R15/R16/R17/R18/"
                "R19/R20 "
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
                "r20_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R15/R16 候选对=空集、"
                         "R17 候选对=空集（run-r17 在案）、R18 候选对=空集"
                         "（run-r18 在案）；R19 唯一候选对=prep1-top-i3 "
                         "R19T-009↔GT-REVC-P1-L1SHORT（run-r19 在案、本轮"
                         "重放复现）；R20 十二件重放全部复现（候选对=空集"
                         "=本轮零 GT 命中），见上表如实登记）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R15T/R15B、R16T/R16B、R17T/"
            "R17B、R18T/R18B、R19T/R19B 与 R20T/R20B 来自不同 reader 实例、"
            "不同判读"
            "实例；轮内实例行为差异见 reader.reader_instance_note=混杂"
            "因素；r20 六实例全部跨板连续=与 prep-record naming 声明相符"
            "（对照 r19 混合行为）、同属实例输出行为登记如实记录）；下列分组"
            "是通道级归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r15_area_ratio_rejected_entries": geo_r15,
            "r16_area_ratio_rejected_entries": geo_r16,
            "r17_area_ratio_rejected_entries": geo_r17,
            "r18_area_ratio_rejected_entries": geo_r18,
            "r19_area_ratio_rejected_entries": geo_r19,
            "r20_area_ratio_rejected_entries": geo_r20,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r15_category_mismatch_entries": cat_r15,
            "r16_category_mismatch_entries": cat_r16,
            "r17_category_mismatch_entries": cat_r17,
            "r18_category_mismatch_entries": cat_r18,
            "r19_category_mismatch_entries": cat_r19,
            "r20_category_mismatch_entries": cat_r20,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r15_entries": view_r15,
            "r16_entries": view_r16,
            "r17_entries": view_r17,
            "r18_entries": view_r18,
            "r19_entries": view_r19,
            "r20_entries": view_r20,
            "note": ("视角门（不入两预注册通道计数，如实单列）：r20 重放"
                     "视角门条目数=%d——top 非弃权旗与同态 GT 视角错位"
                     "交叠如实计数；bottom 非弃权旗零匹配属结构性（GT 13 "
                     "条全部 side=top；bottom 无 GT 在案 gt-audit-r1："
                     "bottom GT=无源已关闭⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；r15–r19 重放亦零视角门条目（在案延续）。"
                     % len(view_r20)),
        },
        "gate_chain_since_r6": chain,
        "r20_specific_observations": [
            "R20 六实例 %d 旗标（非弃权 %d、弃权 %d）的 matches（逐实例"
            "逐态 compare_v3）合计 %d 条（本轮全部零命中——对照 r19 唯一"
            "命中 prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT 未再现；GT "
            "条目层 union/agreement 与代表配置口径见 gt_match_dual/"
            "aggregation_representative（如实分列）；bottom 非弃权旗零"
            "匹配属结构性（GT 13 条全部 side=top，bottom GT 无源在案 "
            "gt-audit-r1）。"
            % (n_fl_total, n_fl_total - n_ab_total, n_ab_total,
               n_match_total),
            "R20 courtyard 类旗标 %d 条（top %d+bottom %d）：top 弃权 "
            "3 条（applied-top-i2 R20T-003+prep1-top-i2 R20T-006/008，"
            "(iii-a) 残余弃权支）；bottom 非弃权 2 条（bottom-i1 两板 "
            "R20B-003/006，(iii-a) 间隙支负责任报告=G1 守门字面破坏的"
            "直接构成）；top 弃权构成分型=接触性 4+存在性 9+层归属"
            "其他 1（hypothesis_test.mechanism_observation."
            "top_abstain_typology 逐旗摘录在案）。"
            % (len(courtyard_counts[0]), len(courtyard_counts[1]),
               len(courtyard_counts[2])),
            "R20 几何门 %d 条（r19=0 延续与否如实计数）；类别门 %d 条"
            "（r16=1 后的 r17–r20 逐轮计数如实登记）；视角门条目数"
            "见 view_gate_observations（如实单列）。"
            % (len(geo_r20), len(cat_r20)),
            "R20 suspicious_reroute 旗标 2 条（弃权 2[applied/prep1-top-i3 "
            "R20T-002/006 存在性出口]，(state, flag_id) 限定）；产量链 "
            "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→"
            "r17=1→r18=3→r19=3→r20=2；「等长|蛇形」子串旗级零命中——r20 "
            "滥用型通道被动追踪=0（见 hypothesis_test.reroute_continuation_"
            "r20，非本轮判据输入）。",
            "courtyard 被动追踪（r11–r19 run-record courtyard_tracking "
            "在案先例延续）：GT/阈值零改动、零期望（run-r20 "
            "courtyard_tracking 节）。",
        ],
    }


def _m_tuple_6dp(m1, m2, m3, m4) -> tuple:
    """四元组 → 6 位定点比较键（M1/M2/M4=率×10^6 取整、M3=整数直接）。"""
    return (int(round(m1 * 1000000)), int(round(m2 * 1000000)),
            int(m3), int(round(m4 * 1000000)))


def adjudicate_main_channel(abst_top: int, flags_top: int, m4: float,
                            r20_tuple: tuple, r19_tuple: tuple,
                            guards_ok: bool) -> tuple:
    """主通道三分判据合成（纯函数；判据原文=
    r20-prep-record hypothesis_test.adjudication；r19 基准元组=
    dev-r19 measured_rows 装载+run-r19 live 复算交叉核对）。

    (s) supported=R20 四元组在冻结 comparison_rule.ordering
    「(M1 升序,M2 升序,M3 升序,M4 升序) 字典序」下不劣于最优单轴 r19
    （即 r20_key ≤ r19_key 字典序；M1 维度操作化表述=M1 ≤ 0.461538，
    M1 相等时依次比较 M2→M3→M4 不劣）；
    (r) reject=M1 ≥0.771429（r16 基线；6 位定点整数交叉相乘，避免
    浮点）、或 G1/G2 任一破坏；
    (m) marginal=未达 supported 但 M1 <0.771429 且 G1/G2 维持。
    支序=reject→supported→marginal；返回 (verdict, branch_key)，
    branch_key ∈ {reject_guards, reject_m1, supported, marginal}；
    supported 与 reject_m1 互斥由判据字面保证（M1 ≤0.461538 与
    M1 ≥0.771429 不相交），若同时命中即 RuntimeError（自洽性破坏）；
    未覆盖组合（守门维持、非 reject、非 supported、非 marginal）亦
    RuntimeError。
    """
    m1_gate_reject = abst_top * 1000000 >= REJECT_M1_MIN_6DP * flags_top
    crit_reject_guards = not guards_ok
    crit_reject_m1 = m1_gate_reject
    crit_reject_ok = crit_reject_guards or crit_reject_m1
    crit_supported_ok = guards_ok and (r20_tuple <= r19_tuple)
    crit_marginal_ok = ((not crit_supported_ok) and guards_ok
                        and abst_top * 1000000
                        < REJECT_M1_MIN_6DP * flags_top)
    if crit_supported_ok and crit_reject_m1:
        raise RuntimeError("主通道判定自洽性破坏（supported 与 reject_m1 "
                           "两支互斥被同时命中）")
    if crit_reject_ok:
        return ("reject",
                "reject_guards" if crit_reject_guards else "reject_m1")
    if crit_supported_ok:
        return ("supported", "supported")
    if crit_marginal_ok:
        return ("marginal", "marginal")
    raise RuntimeError("主通道判定未覆盖（ordering/M1/G 组合未落入任一"
                       "预注册支）")


def _prep_doc() -> dict:
    """r20-prep-record 原文（预注册判据唯一事实源；脚本不另嵌常量）。"""
    return _json_load(REL_PREP_R20)


def prep_doc_attribution_declaration() -> str:
    """归因声明文本（取自 r20-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["declaration"]


def prep_doc_primary_channel_change() -> str:
    """主通道变更文本（取自 r20-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["change"]


def prep_doc_primary_channel_metric() -> str:
    """主通道度量文本（取自 r20-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["primary_channel"]["metric"]


def prep_doc_guard_channel() -> dict:
    """守门通道（取自 r20-prep-record attribution_plan）。"""
    return _prep_doc()["attribution_plan"]["guard_channel"]


# ---------------------------------------------------------------------------
# 预注册假设（axis-plan-r19-criterion-operational）裁决
# （字母裁决+主通道双条件逐实例实测+机制观察单列）
# ---------------------------------------------------------------------------

def bottom_courtyard_non_abstain(instances: dict) -> dict:
    """bottom 侧 G1 守门实测（操作化定义：bottom 三实例 courtyard 类非
    弃权旗数；per r20-prep-record guard_channel「G1=bottom courtyard
    非弃权 0/0/0 维持（对照 r15–r19 在案）」原文；守门独立单列、
    不影响字母——r20 实测 2/0/0=G1 字面破坏、经 reject_guards 支并入
    字母裁决）。

    非弃权判定=per_flag_gt_detail 的 abstain 字段（与逐旗明细一致；
    r20 清单已按 (state, flag_id) 限定）；
    逐实例计数与 SIDE_OBS_REGISTERED 的 expected（=r20 实测登记）
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
# 对拍→r20 套用；关键词表/优先级全部从 abstain-typology-r13-r16.json
# 装载，不另嵌一套词表）
# ---------------------------------------------------------------------------

#: r20 rubric 族计数登记值（程序实测须与本表逐一相等 fail-closed；
#: 双基线对照 r18（黑点 13/存在性 12）与 r19（黑点 4/存在性 14）——
#: R19_REFERENCE_REGISTERED/R18_REFERENCE_REGISTERED 装载交叉核对）。
R20_FAMILY_COUNTS_REGISTERED = {
    "contact": 2, "existence_blackdot": 6, "existence_other": 10,
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


def build_rubric_rows_r20(instances: dict, kt: dict) -> list:
    """r20 全部旗标逐旗 rubric 套用（弃权旗=互斥族分类；非弃权旗不分型
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
                _fail(f"r20 旗 location_evidence 缺失: {d['flag_id']} "
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


#: §5B 与 §4(iii-a) 援引机械实测期望集合（分开记、互不合并；per
#: r20-prep-record adjudication.mechanism_observation_separate 原文）：
#: r20 旗级 location_evidence 字面「§5B」/「(iii-a)」/「分支(」=0 旗
#: （程序实测须与空集逐一相等 fail-closed）；notes 级「§5B」=4 派次
#: （applied/prep1-top-i1 黑点弃权自述「仪器注记 §5B 不作为判据」+
#: applied/prep1-bottom-i2「§5A/§5B 仪器注记仅作事实参考」）与
#: notes 级「(iii-a)」=4 派次（applied/prep1-top-i2「近邻形态按§4(iii-a)
#: 可操作分辨条款执行」+applied/prep1-bottom-i3 两板「按 §4(iii)/(iii-a)
#: 弃权」）；双基线对照：r18 §5B 援引=旗级 0/13 黑点弃权旗（非弃权
#: 黑点旗亦零）、派次级 1/12（dev-r18 在案）；r19 (iii-a) 援引=旗级
#: 「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 派次（dev-r19 在案）。
S5B_FLAG_CITE_REGISTERED = []
S5B_NOTES_CITE_REGISTERED = sorted([
    "applied-top-i1", "prep1-top-i1",
    "applied-bottom-i2", "prep1-bottom-i2",
])
IIIA_FLAG_CITE_IIIA_REGISTERED = []
IIIA_FLAG_CITE_BRANCH_REGISTERED = []
IIIA_NOTES_CITE_REGISTERED = sorted([
    "applied-top-i2", "prep1-top-i2",
    "applied-bottom-i3", "prep1-bottom-i3",
])


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          run_r11: dict, run_r12: dict, run_r13: dict,
                          run_r14: dict, run_r15: dict, run_r16: dict,
                          run_r17: dict, run_r18: dict, run_r19: dict,
                          axis_plan: dict, instances: dict,
                          view_layer: dict, attribution: dict,
                          raw_texts: dict, parsed_notes: dict,
                          reroute_rows: list) -> dict:
    """假设（axis-plan-r20-combo-additivity，stage2 组合轮可加性）裁决节
    （预注册三分判据执行；字母裁决唯一正式+守门 G1/G2 独立单列+机制
    观察单列）。

    字母裁决（唯一正式裁决）=判据 r20-prep-record.json hypothesis_test.
    adjudication 原文（脚本从 prep-record 文件加载判据文本、不另嵌一套
    常量）：判据=可加性比较（冻结 comparison_rule.ordering 字典序）——
    (s) supported：R20 四元组在冻结 ordering 排序中不劣于最优单轴 r19
    （r19 实测 (0.461538,0.571429,4,0.211111)=dev-r19 measured_rows
    装载+run-r19 内嵌实例记录 live 复算交叉核对；M1 维度操作化表述=
    M1 ≤ 0.461538，M1 相等时依次比较 M2→M3→M4 不劣）；
    (r) reject：M1 ≥0.771429（r16 基线 27/35 双侧复算 live 重放交叉
    核对）、或 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）
    任一破坏——按 axis-plan early_stop_rule.guard_failure_exit 出局、
    处置按冻结 iii_non_additive_fallback 采最优单轴 r19；
    (m) marginal：未达 supported 但 M1 <0.771429 且 G1/G2 维持——
    记录为部分收益（可加性未证、不可加采最优单轴 r19）。
    M1 基线=27/35=0.771429（run-r16 内嵌实例记录双侧复算 live 重放交
    叉核对一致）；判据比较用 6 位定点整数交叉相乘（避免浮点）；
    支序=reject→supported→marginal（判据字面：supported 与 reject_m1
    在 M1 维度互斥；未覆盖组合即自洽性破坏、中止）。守门 G1 与 G2
    独立单列——任一破坏→reject 支成立且按 axis-plan early_stop_rule
    出局（字母照实+出局声明）；机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R20)
    ht = prep_doc["hypothesis_test"]
    adj = ht["adjudication"]
    # 预注册链交叉核对（axis-plan/probe/typology/witness-r14b/dev-r19/
    # run-r16 锚已在 FROZEN_SHA256 校验；prep-record chain_anchors
    # 内嵌登记值与盘上实测逐一核对，fail-closed）
    anchors = prep_doc["guidance_reuse"]["chain_anchors"]
    if anchors["axis_experiment_plan_frozen"]["path_rel"] != REL_AXIS_PLAN \
            or anchors["axis_experiment_plan_frozen"]["sha256"] \
            != _sha(REL_AXIS_PLAN):
        _fail("prep-record 链锚（axis-plan）与盘上实测不符")
    probe_anchor = anchors["blackdot_probe_r18_premise"]
    if probe_anchor["path_rel"] != REL_PROBE_R18 \
            or probe_anchor["sha256"] != _sha(REL_PROBE_R18):
        _fail("prep-record 链锚（blackdot-probe-r18 §5B 前提）与盘上实测不符")
    if anchors["evaluation_protocol_v1_preserved"]["sha256"] \
            != _sha(REL_PROTOCOL):
        _fail("prep-record 链锚（evaluation-protocol-v1）与盘上实测不符")
    if anchors["r15_lineage_root"]["path_rel"] != REL_GUIDANCE_R15 \
            or anchors["r15_lineage_root"]["sha256"] \
            != _sha(REL_GUIDANCE_R15):
        _fail("prep-record 链锚（r15 血统根基座）与盘上实测不符")
    if anchors["r18_prep_record_s5b_edit_precedent"]["path_rel"] \
            != REL_PREP_R18 \
            or anchors["r18_prep_record_s5b_edit_precedent"]["sha256"] \
            != _sha(REL_PREP_R18):
        _fail("prep-record 链锚（r18-prep-record §5B 编辑先例）与盘上实测不符")
    if anchors["r19_prep_record_schema_template"]["path_rel"] \
            != REL_PREP_R19 \
            or anchors["r19_prep_record_schema_template"]["sha256"] \
            != _sha(REL_PREP_R19):
        _fail("prep-record 链锚（r19-prep-record schema 模板）与盘上实测不符")
    witness_anchor = anchors["render_witness_r14b_byte_reuse"]
    if witness_anchor["path_rel"] != REL_WITNESS_R14B \
            or witness_anchor["sha256"] != _sha(REL_WITNESS_R14B):
        _fail("prep-record 链锚（witness-r14b 字节复用）与盘上实测不符")
    if anchors["base_sha256_prefix_expected"] != "8633bda5" \
            or anchors["s5b_source_sha256_prefix_expected"] != "cadcb8f3":
        _fail("prep-record 前缀期望与预期不符")
    dev19_anchor = anchors["round19_dev_record_combination_decision"]
    if dev19_anchor["path_rel"] != REL_DEV_R19 \
            or dev19_anchor["sha256_measured"] != _sha(REL_DEV_R19):
        _fail("prep-record 链锚（round19-dev-record 组合决策）与盘上实测不符")
    mrows = dev19_anchor["measured_rows"]
    if mrows["r16_baseline"] != {"M1": 0.771429, "M2": 0.857143,
                                 "M3": AXIS_R16_M3_BLACKDOT_RUBRIC,
                                 "M4": AXIS_R16_M4_TOP_RANGE}:
        _fail("prep-record dev-r19 measured_rows r16 行与登记不符")
    if mrows["r17_axis1"] != R17_ROW_REGISTERED:
        _fail("prep-record dev-r19 measured_rows r17 行与登记不符")
    if mrows["r18_axis2"] != {"M1": R18_REFERENCE_REGISTERED["M1"],
                              "M2": R18_REFERENCE_REGISTERED["M2"],
                              "M3": R18_REFERENCE_REGISTERED["M3"],
                              "M4": R18_REFERENCE_REGISTERED["M4"]}:
        _fail("prep-record dev-r19 measured_rows r18 行与登记不符")
    if mrows["r19_axis3"] != R19_ROW_REGISTERED:
        _fail("prep-record dev-r19 measured_rows r19 行与登记不符")
    if dev19_anchor["r20_recommendation"]["axes"] != ["r19_axis3",
                                                      "r18_axis2"] \
            or dev19_anchor["r20_recommendation"]["round"] != "R20" \
            or dev19_anchor["r20_recommendation"]["preregistration_required"] \
            is not True:
        _fail("prep-record dev-r19 r20_recommendation 与预期不符")
    gr = prep_doc["guidance_reuse"]
    if gr["derived_path_rel"] != REL_GUIDANCE_R20 \
            or gr["derived_sha256"] != _sha(REL_GUIDANCE_R20) \
            or gr["base_path_rel"] != REL_GUIDANCE_R19 \
            or gr["base_sha256"] != _sha(REL_GUIDANCE_R19) \
            or gr["s5b_source_path_rel"] != REL_GUIDANCE_R18 \
            or gr["s5b_source_sha256"] != _sha(REL_GUIDANCE_R18):
        _fail("prep-record guidance_reuse 指引锚（derived/base/s5b_source）"
              "与盘上实测不符")
    if prep_doc["round_id_constant"] != ROUND_ID \
            or prep_doc["round_label"] != ROUND_LABEL \
            or prep_doc["declared_date"] != DECLARED_DATE \
            or prep_doc["instrument_change"]["changed"] is not False \
            or prep_doc["no_instrument_change"] is not True:
        _fail("prep-record 轮次标识/instrument_change.changed 与预期不符")
    if prep_doc["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("prep-record in_calibrated_range 应恒 False")
    cv0 = prep_doc["changed_variables"][0]
    if cv0["axis_id"] != ("A3_criterion_contact_clarification"
                          "+A2_blackdot_instrument_annotation") \
            or cv0["id"] != "guidance-combo-s5b-plus-s4-iiia-union" \
            or cv0["preregistration_ref"]["sha256_measured"] \
            != _sha(REL_AXIS_PLAN):
        _fail("prep-record changed_variables[0] 组合轴定义/链锚不符")
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
    # probe 件上下文锚核对（仅哈希+kind+round；§5B 探针证实前提链锚、
    # 本轮零内容转录——§5B 文本自 r18 指引逐字转录）
    probe_doc = _json_load(REL_PROBE_R18)
    if probe_doc["kind"] != "tl2_blackdot_probe_r18" \
            or probe_doc["round_id_constant"] != "2026-09-09-r18":
        _fail("probe 件 kind/round_id 与预期不符")
    # §5B 节文本核对（edit_list 任务枚举 edit 7 的 text_full 逐字在
    # r20 指引内恰 1 次；content_sha256=19ecdb42 与 r18-prep-record
    # s67 edit 8 跨代交叉锚一致；位置=「## 6. 输出格式」标题之前）
    s5b_edits = [e for e in gr["edit_list"]
                 if str(e.get("kind", "")).startswith(
                     "「## 6. 输出格式」标题前插入 §5B")]
    if len(s5b_edits) != 1 or "text_full" not in s5b_edits[0]:
        _fail("prep-record edit_list 缺 §5B 条款项")
    s5b_text = s5b_edits[0]["text_full"]
    if s5b_edits[0].get("content_sha256") \
            != gr.get("s5b_segment_content_sha256") \
            or s5b_edits[0].get("content_sha256") \
            != s5b_edits[0].get("cross_check_content_sha256_r18_prep_edit8"):
        _fail("prep-record §5B 段 content_sha256 跨代交叉锚不符")
    guidance_text = _rel(REL_GUIDANCE_R20).read_text(encoding="utf-8")
    if guidance_text.count(s5b_text) != 1:
        _fail("§5B 节全文在 r20 指引应恰 1 次")
    if guidance_text.count("## 5B.") != 1:
        _fail("r20 指引 §5B 节标题应恰 1 次")
    # (iii-a) 条款承继核对（随 r19 基座逐字承继：bullet 恰 1 次+位置断言）
    if guidance_text.count("执行 (iii) 时按证据可见性三支操作") != 1:
        _fail("§4 (iii-a) bullet 在 r20 指引应恰 1 次（承继自 r19 基座）")
    if guidance_text.count("(iii-a)") < 1:
        _fail("r20 指引缺 (iii-a) 条款")
    pos_iii = guidance_text.find("(iii) **接触性判据")
    pos_iiia = guidance_text.find("执行 (iii) 时按证据可见性三支操作")
    pos_exit = guidance_text.find("**三路出口显式化")
    pos_5b = guidance_text.find("## 5B.")
    if not (0 <= pos_iii < pos_iiia < pos_exit):
        _fail("(iii-a) 条款位置断言破坏（应在 (iii) 句后、三路出口前）")
    if not (0 <= pos_5b):
        _fail("§5B 节位置断言破坏（应在正文内）")
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
    if ht["hypothesis_id"] != "axis-plan-r20-combo-additivity":
        _fail("prep-record hypothesis_id 与预期不符")
    # 判据文本加载自 prep-record（脚本不另嵌判据常量；fail-closed）
    if "不劣于最优单轴 r19" not in adj["supported"] \
            or "(0.461538, 0.571429, 4, 0.211111)" not in adj["supported"]:
        _fail("prep-record supported 判据文本与预期不符")
    if "M1 < 0.771429" not in adj["marginal"] \
            or "G1" not in adj["marginal"] or "G2" not in adj["marginal"]:
        _fail("prep-record marginal 判据文本与预期不符")
    if "M1 ≥ 0.771429" not in adj["reject"] \
            or "G1" not in adj["reject"] or "G2" not in adj["reject"]:
        _fail("prep-record reject 判据文本与预期不符")
    if "采最优单轴" not in adj["reject"] or "采最优单轴" \
            not in adj["marginal"]:
        _fail("prep-record 处置条款（iii_non_additive_fallback）与预期不符")
    # 阈值常数自检（6 位定点）：reject 门=M1 基线 0.771429
    if REJECT_M1_MIN_6DP != 771429:
        _fail("M1 阈值常数与 r16 基线不符")
    if R19_ROW_REGISTERED != {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                              "M4": 0.211111}:
        _fail("r19 基准四元组登记值与预期不符")
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
    rubric_rows = build_rubric_rows_r20(instances, kt)
    contact = sum(1 for r in rubric_rows
                  if r["abstain"] and r["family"] == "contact")
    family_counts = {fam: sum(1 for r in rubric_rows
                              if r["abstain"] and r["family"] == fam)
                     for fam in ("contact", "existence_blackdot",
                                 "existence_other", "semantic_confusion",
                                 "other")}
    if family_counts != R20_FAMILY_COUNTS_REGISTERED:
        _fail(f"家族计数与登记不符: {family_counts}")
    rubric_bd = {(r["instance"], r["state"], r["flag_id"]) for r in
                 rubric_rows
                 if r["abstain"] and r["family"] == "existence_blackdot"}
    if rubric_bd != {(i, s, f) for i, s, f, _ in BLACK_DOT_FLAGS}:
        _fail("rubric 黑点族旗集合与登记表不一致")
    # contact 族分视角计数（r20 实测；对照 r16=10 全 top、r19=4 全视）
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
    if sorted(judged_normal) != ["applied-top-i2", "applied-top-i3",
                                 "prep1-top-i2", "prep1-top-i3"]:
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
    if iiia_branch_counts != {"branch1_gap_report": 2,
                              "branch2_intrusion_report": 4,
                              "branch3_residual_abstain": 7}:
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
    # dev-r19 measured_rows/R19_REFERENCE_REGISTERED 三方交叉核对
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
    if dev19_anchor["measured_rows"]["r19_axis3"] != r19_row:
        _fail("dev-r19 measured_rows r19 行与 run-r19 live 复算不符")
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
    # reroute 产量链基线交叉核对（r8–r19 在案）
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
            != REROUTE_CHAIN_PRIOR["r19"]:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（ordering 字典序判据+M1 附加门，12 派次全口径；
    # 三分判据逐支）
    abst_top, flags_top = round_view_aggregate(
        instances, ("top-i1", "top-i2", "top-i3"))
    top_rate = cal._ratio(abst_top, flags_top)
    # (r) reject：M1 ≥0.771429、或 G1/G2 任一破坏（守门在下方实测后
    # 合成）
    m4 = view_layer["top"]["abstain_rate_range"]
    crit_reject_m1 = (abst_top * 1000000
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
    # 面积比出局条目 R19=0→R20 实测不升）——独立单列（axis-plan guards.
    # G2_guard_ok 原文）
    geo_r20 = attribution["channel_1_geometry_gate"][
        "r20_area_ratio_rejected_entries"]
    geo_r19 = attribution["channel_1_geometry_gate"][
        "r19_area_ratio_rejected_entries"]
    guard_ok = len(geo_r20) <= len(geo_r19)
    g2_ok = guard_ok is True
    guards_ok = bool(g1_ok and g2_ok)
    axis_out = not guards_ok
    # 三支合成（判据字面；支序=reject→supported→marginal；合成逻辑在
    # adjudicate_main_channel 纯函数内、测试可独立构造边界用例）
    r20_tuple = _m_tuple_6dp(top_rate, bot_rate,
                             family_counts["existence_blackdot"], m4)
    r19_tuple = _m_tuple_6dp(r19_m1, r19_m2, r19_m3, r19_m4)
    verdict, branch_key = adjudicate_main_channel(
        abst_top, flags_top, m4, r20_tuple, r19_tuple, guards_ok)
    crit_reject_ok = verdict == "reject"
    crit_supported_ok = verdict == "supported"
    crit_marginal_ok = verdict == "marginal"
    crit_reject_guards = not guards_ok
    ordering_not_worse = r20_tuple <= r19_tuple
    # 字母裁决（三分判据，per r20-prep-record adjudication 原文）
    if crit_reject_ok:
        verdict = "reject"
        if crit_reject_guards:
            letter_branch = (
                "(r) G1/G2 任一破坏（per axis-plan early_stop_rule."
                "guard_failure_exit）——组合轮出局（字母照实+出局声明）；"
                "本轮=G1 破坏（bottom courtyard 非弃权实测 %s≠0/0/0）；"
                "处置=冻结 combination_decision_rule."
                "iii_non_additive_fallback 采最优单轴 r19 配置"
                % list(by_instance.values()))
        else:
            letter_branch = (
                "(r) M1 ≥0.771429（两轴并施未保有任何单轴改善方向）——"
                "reject：处置=冻结 iii_non_additive_fallback 采最优单轴 "
                "r19 配置")
    elif crit_supported_ok:
        verdict = "supported"
        letter_branch = (
            "(s) R20 四元组在冻结 ordering 字典序下不劣于最优单轴 r19"
            "（(0.461538,0.571429,4,0.211111)）——可加性验证成立"
            "（R21 追加与否按冻结条款另定，不在本支裁断范围）")
    elif crit_marginal_ok:
        verdict = "marginal"
        letter_branch = (
            "(m) 未达 supported（排序劣于最优单轴 r19）但 M1 <0.771429"
            "（实测 %s）且 G1/G2 维持——部分收益（可加性未证）：不可加"
            "采最优单轴 r19（per 冻结 iii_non_additive_fallback）"
            % cal._ratio(abst_top, flags_top))
    else:
        _fail("主通道判定未覆盖（ordering/M1/G 组合未落入任一预注册支）")
    verdict_text = (
        "按预注册判据（r20-prep-record.json hypothesis_test.adjudication "
        "原文，三分判据）=%s（字母口径，唯一正式裁决）：落支=%s。实测："
        "R20 四元组=(%s, %s, %d, %s)（M1=top 全旗聚合弃权率 %d/%d、"
        "M2=bottom 全旗聚合弃权率 %d/%d、M3=黑点族弃权旗数（分型件 "
        "rubric 口径）=%d、M4=top 逐实例弃权率极差=%s）；r19 基准元组="
        "(%s, %s, %d, %s)（dev-r19 measured_rows 装载+run-r19 内嵌实例"
        "记录 live 复算交叉核对一致，不手工抄数）→ordering 字典序不劣于="
        "%s；(r) 支 M1 ≥0.771429→crit_reject_m1=%s（r16 基线=同一聚合"
        "逻辑对 calibration-run-r16.json 内嵌实例记录双侧复算=%d/%d=%s，"
        "与在案登记 27/35 及 axis-plan r16_baseline.M1 交叉核对一致）；"
        "G1（bottom courtyard 非弃权 0/0/0 维持）=%s（实测 %s）、"
        "G2（guard_ok=True 维持，top 几何门面积比出局条目 R19=%d→R20=%d）"
        "=%s。组合轮=轴3+轴2 判读指引合成（§5B+(iii-a) 并集；渲染零变更="
        "renders-r14b 字节复用）下唯一实验变量=指引合成；字母裁决只回答"
        "「组合收益是否不低于最优单轴 r19（可加性）」的计划件判据命中"
        "方向；三项判据文本分开如实记录、不合并；本轮判据均为描述性"
        "边界、非 APR-0011 门（门照常独立计算，互不凌驾、run-record 内"
        "分开表述）。%s（per axis-plan early_stop_rule%s）。注意："
        "跨轮实例群漂移混杂照旧声明（r15→r16 纯重抽漂移 0.09064 在案"
        "参照）；单轮 n=3、development 域只描述不断言；机制观察单列（"
        "§5B 与 (iii-a) 援引计数分开记/三族计数 r18/r19 双基线对照/"
        "contact 族逐旗分类/M2/M4/top 弃权分型/courtyard 计数），不凌驾、"
        "不改写字母裁决。"
        % (verdict, letter_branch,
           top_rate, bot_rate, family_counts["existence_blackdot"], m4,
           abst_top, flags_top, abst_bot, flags_bot,
           family_counts["existence_blackdot"], m4,
           r19_m1, r19_m2, r19_m3, r19_m4,
           "成立" if ordering_not_worse else "不成立",
           crit_reject_m1,
           base16_ab, base16_fl, cal._ratio(base16_ab, base16_fl),
           "维持（0/0/0）" if g1_ok else "破坏",
           list(by_instance.values()),
           len(geo_r19), len(geo_r20),
           "维持（True）" if g2_ok else "破坏",
           "守门均维持、不触发出局" if guards_ok
           else "守门破坏→reject 支成立+按 plan early_stop_rule 出局"
                "（字母照实+出局声明；组合出局处置=冻结 "
                "iii_non_additive_fallback 采最优单轴 r19 配置）",
           "：guard_failure_exit=任一轮 G1/G2 破坏→该轴出局并如实记录"
           "（该轮 run/dev-record 照常落盘、字母裁决照常；「出局」仅指"
           "退出本实验后续组合与排序）" if axis_out else ""))
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
    # 黑点族旗标登记校验（6 条全部存在、abstain=True、category=登记值、
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
    # 绿色区域语义化观察（r16–r19 side_observation 先例延续：按实例
    # 分布；程序实测 substring 计数「绿|翼瓣|空隙|§5A」+摘录，无期望、
    # 不构成判据输入；r20 实测 §5A 显式援引=2/6 派次、§5B 显式援引
    # （notes 级，bottom 侧）=2/6 派次）
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
    r20_m4 = cal._round6(max(top_rates.values()) - min(top_rates.values()))
    # 实验对照账：r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合五行并列+
    # 冻结排序（资格门=G1/G2 均满足）
    ledger_rows = {
        "r16_baseline": {"M1": rb["M1_top_aggregate_abstain_rate"],
                         "M2": rb["M2_bottom_aggregate_abstain_rate"],
                         "M3": rb["M3_blackdot_abstain_flags_rubric"],
                         "M4": rb["M4_top_per_instance_rate_range"]},
        "r17_axis1": dict(measured_rows["r17_axis1"]),
        "r18_axis2": dict(measured_rows["r18_axis2"]),
        "r19_axis3": dict(r19_row),
        "r20_combo": {"M1": top_rate, "M2": bot_rate, "M3": family_counts[
            "existence_blackdot"], "M4": r20_m4},
    }
    eligible_rows = {k: v for k, v in ledger_rows.items()
                     if k != "r20_combo"}
    ranking = sorted(eligible_rows.items(),
                     key=lambda kv: (kv[1]["M1"], kv[1]["M2"],
                                     kv[1]["M3"], kv[1]["M4"]))
    ranking_order = [k for k, _ in ranking]
    m1_drop_r20 = cal._round6(rb["M1_top_aggregate_abstain_rate"]
                              - top_rate)
    # 阶段2 结论位（supported→组合胜出；marginal→不可加采最优单轴 r19；
    # reject→劣化+采最优单轴 r19+守门破坏出局）
    stage2_conclusion = {
        "rule_sources": (
            "axis-experiment-plan-r17-r20 combination_decision_rule."
            "ii_full_combination/iii_non_additive_fallback/"
            "iv_final_selection + early_stop_rule.guard_failure_exit"
            "（冻结原文；supported→组合胜出；marginal→不可加采最优单轴 "
            "r19；reject→劣化+采最优单轴 r19+守门破坏出局）"),
        "verdict": verdict,
        "conclusion": (
            "阶段2 结论=组合劣化（reject）：R20 四元组 ordering 字典序"
            "劣于最优单轴 r19 且 G1 守门字面破坏（bottom courtyard 非弃权 "
            "2/0/0）——按冻结 iii_non_additive_fallback「若 R20 收益 < "
            "最优单轴（两轴不可加）→ 采最优单轴、不再追加」采最优单轴 "
            "r19 配置为后续迭代基座；按 early_stop_rule.guard_failure_exit "
            "该组合出局（退出本实验后续组合与排序；R21 不做——dev-r19 "
            "r21_full_combination_trigger.met=False 在案、本轮 G1 破坏"
            "亦排除追加）；最终「收益最大配置」按 iv_final_selection 在"
            "全部已测配置中裁定=排序（含 r19）居首的 r19_axis3"
            if verdict == "reject" else
            ("阶段2 结论=组合胜出（supported）" if verdict == "supported"
             else "阶段2 结论=不可加、采最优单轴 r19（marginal）")),
        "r21_full_combination_trigger_dev_r19": False,
    }
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决不因本观察"
                 "改写；per r20-prep-record adjudication."
                 "mechanism_observation_separate 原文：§5B 与 (iii-a) "
                 "各自的旗级援引计数分开记、互不合并；三族计数对照 r18/"
                 "r19 双基线；M1/M2/M3/M4 四元组入实验对照账；gt 照常）"),
        "main_channel_three_branches": {
            "observation": (
                "主通道三分判据分开实测（机制：可加性比较）：R20 四元组="
                "(%s, %s, %d, %s) vs 最优单轴 r19=(%s, %s, %d, %s)"
                "（dev-r19 装载+run-r19 live 复算交叉核对）→ordering "
                "字典序不劣于=%s；(r) 支 M1 ≥0.771429=%s、G1/G2 任一"
                "破坏=%s；(m) 支 M1 <0.771429=%s 且 G1/G2 维持=%s。"
                "⇒ verdict=%s（%s）。四元组比较用 6 位定点整数交叉相乘"
                "（避免浮点）。判据均为 r20-prep-record hypothesis_test."
                "adjudication 原文，轮后如实执行。"
                % (top_rate, bot_rate,
                   family_counts["existence_blackdot"], m4,
                   r19_m1, r19_m2, r19_m3, r19_m4,
                   "成立" if ordering_not_worse else "不成立",
                   crit_reject_m1, crit_reject_guards,
                   abst_top * 1000000 < REJECT_M1_MIN_6DP * flags_top,
                   guards_ok, verdict, letter_branch)),
            "counts": {
                "r20_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                    "M3": family_counts[
                                        "existence_blackdot"],
                                    "M4": m4,
                                    "M1_arithmetic": f"{abst_top}/{flags_top}",
                                    "M2_arithmetic": f"{abst_bot}/{flags_bot}"},
                "r19_reference_tuple": R19_ROW_REGISTERED,
                "r19_reference_tuple_source": (
                    "dev-r19 measured_rows 装载+run-r19 内嵌实例记录 "
                    "live 复算交叉核对一致"),
                "ordering_not_worse_than_r19": ordering_not_worse,
                "crit_reject_m1_ge_0_771429": crit_reject_m1,
                "crit_reject_guards_broken": crit_reject_guards,
                "crit_marginal_m1_lt_0_771429":
                    abst_top * 1000000 < REJECT_M1_MIN_6DP * flags_top,
                "r16_top_baseline_registered":
                    BASE16_TOP_AGGREGATE_REGISTERED,
                "r16_top_baseline_live": f"{base16_ab}/{base16_fl}",
                "r16_top_baseline_value": cal._ratio(base16_ab, base16_fl),
                "top_flags_r20": flags_top,
                "top_abstain_r20": abst_top,
                "top_abstain_rate_r20": top_rate,
                "m4_top_rate_range_r20": m4,
                "contact_family_abstain_flags_rubric_r20": contact,
                "contact_family_by_view_r20": contact_by_view,
                "contact_r16_baseline_registered": CONTACT_CHAIN_PRIOR[
                    "r16"],
                "contact_r13_r16_chain_live_replay":
                    replay_proof["contact_counts"],
                "verdict": verdict,
            },
            "status": (
                "stage2 组合轮（§5B+(iii-a) 指引合成；渲染零变更="
                "renders-r14b 字节复用）下 ordering 落点=劣于 r19（M1 "
                "%s>%s 为首要劣化维度）→%s 支（如实单列；判据命中与否"
                "的描述性结论，非因果证明"
                % (top_rate, r19_m1, verdict)),
        },
        "guards_g1_g2": {
            "role": ("守门通道独立单列（per r20-prep-record "
                     "attribution_plan.guard_channel 与 axis-plan guards "
                     "原文；任一破坏→reject 支成立+按 plan "
                     "early_stop_rule 出局）"),
            "observation": (
                "G1=bottom courtyard 非弃权 0/0/0 维持：r20 实测=%s"
                "（对照 r16 基线 0/0/0 live 重放交叉核对一致；bottom "
                "courtyard 类旗标本身=%d 条）→G1=%s。G2="
                "guard_ok=True 维持：top 几何门面积比出局条目 R19=%d→"
                "R20=%d（不升）→guard_ok=%s→G2=%s。守门结论=%s。"
                "G1 破坏机制=(iii-a) 间隙支把 bottom-i1 孤立焊盘对占位"
                "框线极近近邻（间隙带可辨认）引导到 courtyard_crowding "
                "负责任报告（r14–r19 该形态在 bottom 侧从未产生过非弃权 "
                "courtyard 旗）——反向风险守门按 guard_channel 原文"
                "「注记若被误用为『少弃权/判正常』压力，G1/守门与 reject "
                "支须如实记录」如实记录。"
                % (list(by_instance.values()), bot_courtyard_flags,
                   "维持" if g1_ok else "破坏",
                   len(geo_r19), len(geo_r20), guard_ok,
                   "维持" if g2_ok else "破坏",
                   "G1/G2 均满足、不触发出局" if guards_ok
                   else "守门破坏（G1）→reject 支成立+组合出局（字母照实"
                        "+出局声明；处置=冻结 iii_non_additive_fallback "
                        "采最优单轴 r19 配置）")),
            "counts": {
                "g1_bottom_courtyard_non_abstain_r20": by_instance,
                "g1_bottom_courtyard_flags_total_r20": bot_courtyard_flags,
                "g1_r16_baseline_live": r16_courtyard_base,
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r20": len(geo_r20),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "axis_early_stop_triggered": axis_out,
            },
            "status": ("守门与字母裁决分开记账（守门经 reject_guards 支"
                       "字面并入字母裁决；axis-plan early_stop_rule."
                       "guard_failure_exit 原文语义如实援引）"),
        },
        "criterion_citation_observation": {
            "role": ("§5B 与 (iii-a) 援引机制观察核心（单列，不进字母"
                     "裁决；per r20-prep-record attribution_plan."
                     "declaration「字母/机制观察/度量教训三分记账」原文）："
                     "两条款的旗级/notes 级援引计数分开记、互不合并+"
                     "(iii-a) 逐旗落支分布（间隙支/侵入支/残余弃权支）"),
            "observation": (
                "§5B 与 (iii-a) 措辞援引计数（分开记）：旗级 location_"
                "evidence 含「§5B」=%d 旗、含「(iii-a)」=%d 旗、含"
                "「分支(」=%d 旗（三集合均为空=本轮判读在旗级理由中零"
                "字面援引）；notes 级含「§5B」=%d/12 派次（%s）、含"
                "「(iii-a)」=%d/12 派次（%s）——两计数互不合并。双基线"
                "对照：r18 §5B 援引=旗级 0/13 黑点弃权旗（非弃权黑点旗"
                "亦零）、派次级 1/12（dev-r18 在案）；r19 (iii-a) 援引="
                "旗级「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 派次"
                "（dev-r19 在案）——r20 旗级援引零化、notes 级两条款各 "
                "4/12。§5B 反指示声明遵守实例：applied/prep1-top-i1 黑点"
                "弃权自述明写「仪器注记 §5B 不作为判据」（§5B 已证实其"
                "物理来源=非电镀机械定位孔渲染，读侧仍按 §4 存在性判据"
                "弃权——未被注记引导为判正常）。"
                "旗级落支分布（13 旗=textual 证据可归支的判据相关旗）："
                "间隙支（branch1）=%d（全部非弃权 courtyard 报告：可辨认"
                "间隙带→视觉贴近→负责任报告——G1 守门字面破坏的直接"
                "构成）、侵入支（branch2）=%d（全部非弃权黑点-框线报告："
                "直接相接并略有侵入→按接触/交叠处理）、残余弃权支"
                "（branch3）=%d（全部弃权旗）。"
                % (len(s5b_flag_hits), len(iiia_flag_hits),
                   len(iibranch_flag_hits),
                   len(s5b_notes_hits), "、".join(sorted(s5b_notes_hits)),
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
                "dual_baseline_r18_s5b": (
                    "旗级 0/13 黑点弃权旗（非弃权黑点旗亦零）、派次级 "
                    "1/12（dev-r18 在案）"),
                "dual_baseline_r19_iiia": (
                    "旗级「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 "
                    "派次（dev-r19 在案）"),
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
            "status": ("旗级落支=间隙 2+侵入 4+残余弃权 7；§5B/(iii-a) "
                       "援引计数分开记、不凌驾字母裁决"),
        },
        "bottom_side_observation_maintenance": {
            "role": ("bottom 侧观察 M2（mechanism_observation_separate："
                     "单列、不影响字母；per axis-plan benefit_metrics."
                     "M2_bottom_aggregate_abstain_rate 同法）"),
            "observation": (
                "M2=bottom 全旗聚合弃权率=%d/%d=%s（对照 r16 基线 12/14="
                "%s，live 重放交叉核对一致；对照 r18 13/19=%s、r19 4/7="
                "%s live 复算）——方向="
                "%s（改善方向：组合轮 bottom 弃权 4/14 vs r16 12/14、"
                "r18 13/19、r19 4/7；轮际比较含实例群漂移混杂、照 "
                "axis-plan comparison_rule 显式容忍）。bottom "
                "侧三件实测：(1) 零旗标派次=%d 个（12 格全部≥1 旗）；"
                "(2) 黑点族弃权旗（rubric 口径）=%d 条 vs r16=12/r18=13/"
                "r19=4（top-i1 2+bottom-i3 4；数量低于 r16/r18、高于 "
                "r19，双基线对照如实登记）；(3) bottom courtyard 类旗=%d "
                "条（全部非弃权=bottom-i1 两板 R20B-003/006，间隙支报告"
                "路径）——非弃权 courtyard 2/0/0=G1 字面破坏（见 "
                "guards_g1_g2）。"
                % (abst_bot, flags_bot, bot_rate,
                   cal._ratio(base16_bot_ab, base16_bot_fl),
                   cal._ratio(r18_bot_ab, r18_bot_fl),
                   r19_m2,
                   ("低于 r16 基线（改善方向）" if bot_below_r16
                    else "不低于 r16 基线（维持/恶化）"),
                   0, family_counts["existence_blackdot"],
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
                "bottom_flags_r20": flags_bot,
                "bottom_abstain_r20": abst_bot,
                "bottom_abstain_rate_r20": bot_rate,
                "bottom_abstain_rate_r16_baseline":
                    cal._round6(base16_bot_ab / base16_bot_fl),
                "bottom_rate_direction_vs_r16": (
                    "improved" if bot_below_r16 else "not_improved"),
                "zero_flag_dispatch_count": 0,
                "blackdot_abstain_flags_rubric_r20":
                    family_counts["existence_blackdot"],
                "blackdot_rubric_r16_registered":
                    AXIS_R16_M3_BLACKDOT_RUBRIC,
                "blackdot_rubric_r18_registered":
                    R18_REFERENCE_REGISTERED["M3"],
                "blackdot_rubric_r19_registered":
                    R19_REFERENCE_REGISTERED["M3"],
            },
            "registered_detail": SIDE_OBS_REGISTERED,
            "reader_note_evidence": QUANT_CRITERION_EVIDENCE,
            "reader_note_evidence_check": (
                "6/6 派次摘录逐字来自对应 reading_notes（substring "
                "fail-closed 校验通过）——bottom 派次全部实际使用 §4(i) "
                "量化判据（黑点=孤立出现+未达系统性量化判据→报告；绿色"
                "瓣状桥接/翼瓣空隙=满足量化判据→判正常；applied/"
                "prep1-bottom-i3 同文=两板逐字节同图的同判自述）"),
            "status": (
                "M2 改善方向+黑点族弃权 6（r18/r19 双基线间）+零旗派次 0 "
                "如实单列（不影响字母裁决；development 域只描述不断言）"),
        },
        "experiment_comparison_ledger": {
            "role": ("实验对照账（per axis-experiment-plan-r17-r20 "
                     "benefit_metrics 口径定义；(M1,M2,M3,M4) 四元组如实"
                     "入账——四元组由后续 dev-record 包转记入 round20-dev-"
                     "record；全部=12 派次全口径（非代表配置子集）、与"
                     "分型件同法；单位=旗标条数（M3）或 6 位小数率；"
                     "M3 定义按冻结件=黑点族弃权旗数，contact 族计数另列"
                     "（contact_family_abstain_flags_rubric）不占 M3 槽位；"
                     "r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合五行并列）"),
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
            "r19_row_source": ("run-r19 内嵌实例记录 live 复算+dev-r19 "
                               "measured_rows 交叉核对一致"),
            "r20_measured": {
                "M1": top_rate,
                "M1_arithmetic": f"{abst_top}/{flags_top}",
                "M2": bot_rate,
                "M2_arithmetic": f"{abst_bot}/{flags_bot}",
                "M3": family_counts["existence_blackdot"],
                "M4": r20_m4,
                "M4_top_instance_rates": top_rates,
                "contact_family_abstain_flags_rubric": contact,
                "contact_family_by_view": contact_by_view,
                "existence_other_family": family_counts["existence_other"],
            },
            "family_counts_vs_r18_r19": {
                "contact": {
                    "r18_registered":
                        R18_REFERENCE_REGISTERED["top_typology"]["contact"],
                    "r19_registered": R19_REFERENCE_REGISTERED["contact"],
                    "r20_measured": contact,
                    "note": ("r18 参照值=top 弃权分型 contact 8"
                             "（全视 top）；r19/r20=rubric 口径全视 4/2"
                             "（分型件口径）——口径差异如实注明")},
                "existence_blackdot": {
                    "r18_registered": R18_REFERENCE_REGISTERED["M3"],
                    "r19_registered": R19_REFERENCE_REGISTERED["M3"],
                    "r20_measured": family_counts["existence_blackdot"]},
                "existence_other": {
                    "r18_registered":
                        R18_REFERENCE_REGISTERED["existence_other"],
                    "r19_registered":
                        R19_REFERENCE_REGISTERED["existence_other"],
                    "r20_measured": family_counts["existence_other"],
                    "note": ("对照 r18 在案存在性其他 12、r19 14：r20 实测 "
                             "10——回落、未显著上升（弃权转移对照口径"
                             "如实登记）")},
            },
            "ranking_by_comparison_rule": {
                "rule": axis_plan["comparison_rule"]["ordering"],
                "eligibility_gate": axis_plan["comparison_rule"][
                    "eligibility_gate"],
                "rows_registered": ledger_rows,
                "eligible_rows": sorted(eligible_rows),
                "ranking_order_best_first": ranking_order,
                "r20_eligibility": False,
                "r20_exclusion_reason": (
                    "资格门=G1/G2 均满足；r20 G1 破坏（bottom courtyard "
                    "非弃权 2/0/0）→不参与排序（per eligibility_gate 原文"
                    "「G1 或 G2 破坏的轮次不参与排序」；r20 行仅如实入账"
                    "不占排序位）"),
                "note": ("资格门：r17/r18/r19 均 G1/G2 满足（r17/r18 行"
                         "资格=dev-r18 在案注记「两轮 G1/G2 均满足」装载、"
                         "r19=run-r19 guards 在案）→入排序；r16=基线"
                         "参照行（非轴配置）；r20=G1 破坏不入排序；当前"
                         "排序（不含 r20）=r19 轴3 第一——如实登记、"
                         "不预写后续决策（combination_decision_rule."
                         "preregistration_note：本规则只决定「做不做、做"
                         "哪个」，不预写结果）"),
            },
            "significant_benefit_vs_r16": {
                "definition": axis_plan["comparison_rule"][
                    "significant_benefit_definition"],
                "r20_m1_absolute_drop": m1_drop_r20,
                "met": m1_drop_r20 >= 0.10,
                "r18_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r18_m1),
                "r19_drop_reference": cal._round6(
                    rb["M1_top_aggregate_abstain_rate"] - r19_m1),
                "note": ("r20 M1 绝对降幅 %s ≥0.10=显著收益定义在描述层"
                         "命中（r18 降幅 %s、r19 降幅 %s 亦 ≥0.10）；"
                         "字母裁决与实验账分列互不改写（r18/r19 先例："
                         "reject/marginal 但排序居首；本轮 reject 但 M1 "
                         "降幅 ≥0.10——两账分列）"
                         % (m1_drop_r20,
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r18_m1),
                            cal._round6(rb["M1_top_aggregate_abstain_rate"]
                                        - r19_m1))),
            },
            "stage2_conclusion": stage2_conclusion,
            "direction_vs_r16": {
                "M1": ("down（%s→%s，改善方向）"
                       % (rb["M1_top_aggregate_abstain_rate"], top_rate)),
                "M2": ("down（%s→%s，改善方向）"
                       % (rb["M2_bottom_aggregate_abstain_rate"],
                          bot_rate)),
                "M3": ("down（%d→%d，黑点族弃权回落）"
                       % (rb["M3_blackdot_abstain_flags_rubric"],
                          family_counts["existence_blackdot"])),
                "M4": ("%s→%s（走阔）"
                       % (rb["M4_top_per_instance_rate_range"], r20_m4)),
                "contact": ("down（10→%d，主度量回落）" % contact),
            },
            "confounder_note": axis_plan["baselines_registered"][
                "drift_reference_note"],
            "status": ("五元组如实并列（M1/M2/M3 降、M4 走阔 0.261904→"
                       "0.25 内对比失真见 M4 定义=轮内极差；主判据="
                       "ordering 字典序劣于 r19+G1 破坏→reject；"
                       "development 域只描述不断言）"),
        },
        "green_semantics_by_instance": {
            "observation": (
                "绿色区域语义化方式按实例分布（r16–r19 side_observation "
                "先例延续观察）：r20 bottom 6 派次全部以「空隙/翼瓣/仪器"
                "注记」语义化绿色并按 §4(i) 判入系统性正常路径或报告路径"
                "（判据轴延续；§5A 显式援引=2/6 派次（applied/prep1-"
                "bottom-i2「§5A/§5B 仪器注记仅作事实参考」）、§5B 显式"
                "援引（bottom 侧）=2/6 派次（同句）；实例级=%d/3 实例"
                "至少一板援引 §5B。指引 §5A 随 r19 基座逐字保留、§5B 自 "
                "r18 逐字转录，判据文本零变更，援引波动属实例自述异质性、"
                "如实登记不作废）。逐实例 "
                "substring 计数「绿|翼瓣|空隙|§5A」+摘录如实登记（无期望、"
                "不构成判据输入）。"
                % sum(1 for v in green_semantics.values()
                      if v["§5B_cited"])),
            "green_semantics_by_instance": green_semantics,
            "evidence": GREEN_SEMANTICS_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("绿区语义化「空隙非图元」读法在实例群重抽下延续"
                       "（§5A 援引 2/6、§5B 援引 2/6 分列；"
                       "如实单列、不凌驾字母裁决）"),
        },
        "black_dot_tracking": {
            "observation": (
                "黑点族现象追踪（机制观察，分型件 rubric 口径；rubric "
                "机械套用证明见 rubric_families 节）：r20 黑点族弃权旗 %d "
                "条（top-i1 两板 2+bottom-i3 两板 4；top-i1 黑点=§5B 已"
                "证实物理来源（非电镀机械定位孔渲染）仍按 §4 存在性判据"
                "弃权、notes 自述「仪器注记 §5B 不作为判据」；bottom-i3 "
                "黑点=按接触性判据 (iii)+(iii-a) 残余弃权支弃权）——vs "
                "r16 黑点族 12 旗（分型件 rubric 口径在案）/r18=13（run-"
                "r18 实测装载）/r19=4（run-r19 实测装载）双基线对照："
                "数量介于两基线间、方向性描述（非因果证明）。另实测黑点"
                "转非弃权旗 %d 条（全 bottom：bottom-i1 两板 4=黑点-占位"
                "框线直接相接并略有侵入按 (iii-a) 侵入支接触/交叠报告+"
                "bottom-i2 两板 2=孤立钻孔样异常按 §4(ii) 兜底类报告）"
                "+黑点判正常派次 %d 个（applied/prep1-top-i2+i3 两板；"
                "对照 r15=3/r16=2/r18=2/r19=3）。"
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
                    "applied/prep1-top-i2（黑点+孤立焊盘对+过孔按 §4 存在"
                    "性判据与域常规解释判正常）+applied/prep1-top-i3"
                    "（右上两处成对实心黑点判安装/机械定位孔类正常设计"
                    "特征，三路出口第（1）路不报告，两板同判）；对照 "
                    "r15=3/r16=2/r18=2/r19=3。注意 applied/prep1-top-i1 "
                    "notes 虽同样判读黑点，但该两派次就黑点对落了弃权旗"
                    "（R20T-003/007）——按 blackdot_dispatch 口径归入 "
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
                "note": ("r20 全部 18 条弃权旗逐旗分类入账（rows）——"
                         "existence_blackdot %d/contact %d/existence_other "
                         "%d/semantic_confusion %d/other %d；本分型"
                         "（rubric 族）与 top_abstain_typology（contact/"
                         "existence/other_layer 主出口分型）为两套登记"
                         "口径、分别如实入账（例：prep1-top-i2 R20T-007/"
                         "R20T-008 主出口=连印/接触不可确认→top 分型计 "
                         "contact；rubric 族因无 contact 怀疑组合命中归 "
                         "existence_other）"
                         % (family_counts["existence_blackdot"],
                            family_counts["contact"],
                            family_counts["existence_other"],
                            family_counts["semantic_confusion"],
                            family_counts["other"])),
            },
            "notes_normal_dispositions": (
                "4 派次判正常：applied/prep1-top-i2「右上封装内两枚成对"
                "孤立实心黑点…按§4存在性判据与通用PCB域常规图形解释（安装"
                "孔/电池触点焊盘/过孔）判为正常设计特征，均未报告」+"
                "applied/prep1-top-i3「右上角两处成对实心黑点…判为安装/"
                "机械定位孔类正常设计特征，按三路出口第（1）路不报告」"
                "（摘录见 evidence 表 disposition=判正常不报告 行）"),
            "evidence": BLACK_DOT_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes/"
                               "location_evidence（substring fail-closed "
                               "校验通过）"),
            "status": ("黑点族弃权 6（r18=13/r19=4 双基线间）+非弃权报告"
                       "路径 6 条（全 bottom）+判正常派次 4（"
                       "如实单列、不凌驾字母裁决）"),
        },
        "top_abstain_typology": {
            "observation": (
                "top 弃权理由构成分型（机制观察，per mechanism_observation_"
                "separate「top 弃权分型照常」语义；为 M1/M4 与主通道归因"
                "提供分解）：本轮 top 弃权旗 %d 条逐旗按 location_evidence "
                "关键词分类——接触性（真实接触 vs 视觉贴近不可分辨/是否"
                "接触/交叠不可确认，含连印/接触不可确认主出口）=%d 条、"
                "存在性（性质不明/是否存在不可确认）"
                "=%d 条、层归属等其他出口=%d 条。构成解读（如实单列）："
                "接触性弃权集中于 courtyard 类旗标与丝印连印/接触"
                "（(iii-a) 残余弃权支语言），存在性弃权横跨 silk/"
                "other_advisory/reroute 各类（疑似受阻文字、黑点对性质、"
                "连印存在性、改道存在性等）——top 弃权非单一机制驱动；"
                "对照 r16（接触性 11+存在性 15+层归属其他 1，27 条）与 "
                "r17（接触性 8+存在性 14+其他 0，22 条）与 r18（接触性 8+"
                "存在性 12+其他 0，20 条）与 r19（接触性 5+存在性 13+其他 "
                "0，18 条，run-r19 live）：r20 绝对数 27→22→20→18→14 续降、"
                "构成比稳定（接触性主通道+存在性多通道分散）；弃权旗数"
                "下降且弃权率 M1=%s（分母 22 较 r19 的 39 下降）。逐旗摘录"
                "与分类在案（rows）。"
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
                "%s）——top-i2 最高（6/8=0.75）、top-i1 最低（4/8=%s）；"
                "(2) bottom 弃权率 %s/%s/%s（轮内极差 %s；本轮 12 格全部"
                "≥1 旗、无 None 实例）——bottom-i3 最高（4/4=1.0，黑点-"
                "焊盘接触全部弃权）、bottom-i1/i2 最低（0.0，全部负责任"
                "报告）；(3) placement/孤立图形处置实例/跨板分化延续："
                "bottom-i1 两板以 courtyard 报告占位框线极近近邻（间隙支）、"
                "bottom-i2 两板以 placement_pattern_anomaly 报告孤立焊盘"
                "组偏离周边模式、bottom-i3 两板判正常（中心电镀通孔焊盘"
                "正常图形）、top-i1 两板 notes 判正常（§5B(c) 路径）——"
                "同现象跨实例/跨板出口不同=判读语义歧义未穷尽；「正确测出"
                "无效同样是有效证据」的同构：测出残余差异同样是有效证据。"
                % (top_rates["top-i1"], top_rates["top-i2"],
                   top_rates["top-i3"], top_range,
                   top_rates["top-i1"],
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
                 "适用；per r20-prep-record adjudication."
                 "metric_lesson_separate）"),
        "lesson": (
            "r20 三分判据=ordering 字典序可加性比较（r19 基准四元组="
            "dev-r19 measured_rows 装载+run-r19 内嵌实例记录 live 复算"
            "交叉核对，不手工抄数）+M1 附加门（6 位定点整数交叉相乘，"
            "阈值=r16 基线 0.771429 原文）；M3 计数口径=分型件 rubric "
            "机械套用（关键词表/优先级 fail-closed 装载+对 r13–r16 132 "
            "条弃权旗重放对拍逐一相等后套用 r20）——口径可复算性=度量"
            "设计要点（计数口径跨轮漂移是历史教训：r15 dev-record prose "
            "口径 7 vs 分型件 rubric 口径 8 在案，axis-plan M3_caveat 已"
            "声明一律采用 rubric 口径）；组合轮四元组 M3 槽位定义维持"
            "冻结件黑点口径、contact 主度量另列不占槽=判据侧轮的对照账"
            "纪律；跨轮实例群漂移混杂照旧声明（r15→r16 纯重抽漂移 "
            "0.09064 在案、axis-plan comparison_rule 显式容忍且不消除）；"
            "M1 分母（top 旗数）本身随轮变化（35→31→39→22），弃权率比较"
            "含分母效应、构成分解（top 弃权构成分型+§5B/(iii-a) 援引分记+"
            "黑点转非弃权旗）单列补足；资格门（G1/G2 破坏轮不入排序）"
            "首次实测触发=排序账与字母账的衔接纪律单列。"),
        "status": ("字母裁决=预注册判据命中与否的描述性结论，非因果"
                   "证明；下一迭代候选方向（如实登记，不构成本轮判据"
                   "输入）：按冻结 iii_non_additive_fallback 采最优单轴 "
                   "r19 配置为后续基座（R21 不做在案）；不得回溯改判既往"
                   "轮次（r8–r19 字母裁决维持不变）"),
    }
    # r16/r18/r19 分层基线（逐实例弃权率，live 重放/装载；不手工抄数）
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
    n_total_all = flags_top + flags_bot
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R20,
                                "sha256": _sha(REL_PREP_R20)},
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
            "本轮判据均为描述性边界（r20-prep-record.json hypothesis_"
            "test.adjudication 原文），只用于本轮组合轮可加性归因"
            "（axis-experiment-plan-r17-r20 冻结比较规则），与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值"
            "零改动）；非门阈值、非期望清单"),
        "measurement": {
            "contact_family_abstain_flags_rubric_r20": contact,
            "contact_arithmetic_note": (
                "contact = contact 族弃权旗数（分型件 rubric 口径）= %d"
                "（r20 全部 18 条弃权旗逐旗 rubric 分类中 contact 计数；"
                "关键词表/优先级=abstain-typology-r13-r16.json 装载；"
                "r13–r16 132 条弃权旗重放对拍逐一相等=口径忠实性证明；"
                "分视角 top %d+bottom %d）"
                % (contact, contact_by_view["top"],
                   contact_by_view["bottom"])),
            "top_abstain_flags_r20": flags_top,
            "top_abstain_count_r20": abst_top,
            "top_abstain_rate_r20": top_rate,
            "top_abstain_rate_r20_arithmetic":
                f"M1 = top 全旗聚合弃权率 = {abst_top}/{flags_top} = "
                f"{top_rate}（ordering 首键；12 派次全口径）",
            "m4_top_rate_range_r20": m4,
            "m4_arithmetic_note": (
                "M4 = top 逐实例弃权率极差 = %s（top 三实例 %s/%s/%s；"
                "ordering 第 4 键；先 6 位小数取率再取差）"
                % (m4, top_rates["top-i1"], top_rates["top-i2"],
                   top_rates["top-i3"])),
            "crit_reject_m1_ge_0_771429": crit_reject_m1,
            "crit_reject_guards_broken": crit_reject_guards,
            "crit_supported_ordering_not_worse_than_r19":
                ordering_not_worse,
            "crit_marginal_m1_lt_0_771429":
                abst_top * 1000000 < REJECT_M1_MIN_6DP * flags_top,
            "r20_m_tuple_6dp": {"M1": top_rate, "M2": bot_rate,
                                "M3": family_counts["existence_blackdot"],
                                "M4": m4},
            "r19_reference_tuple": R19_ROW_REGISTERED,
            "reject_m1_threshold_6dp": REJECT_M1_MIN_6DP,
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
                "复算，不手工抄数；r19 基准四元组=run-r19 内嵌实例记录 "
                "live 复算+dev-r19 measured_rows 装载交叉核对；均与在案"
                "登记值（axis-plan baselines_registered.r16_baseline.M1="
                "0.771429、dev-r19 measured_rows.r19_axis3）交叉核对"
                "（fail-closed，见 baseline_cross_check）"),
            "bottom_side_observation": {
                "bottom_courtyard_non_abstain_by_instance_r20":
                    by_instance,
                "bottom_courtyard_flags_total_r20": bot_courtyard_flags,
                "bottom_abstain_flags_r20": flags_bot,
                "bottom_abstain_count_r20": abst_bot,
                "bottom_abstain_rate_r20": bot_rate,
                "bottom_abstain_rate_r20_arithmetic":
                    f"M2 = bottom 全旗聚合弃权率 = {abst_bot}/{flags_bot} = "
                    f"{bot_rate}"
                    f"（对照 r16 基线 12/14=0.857143、r18 13/19=0.684211、"
                    f"r19 4/7=0.571429；mechanism_observation_separate "
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
            "bottom_courtyard_detail_r20": [
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
                "axis_plan_r16_baseline_M1_M2_M3_M4": [
                    rb["M1_top_aggregate_abstain_rate"],
                    rb["M2_bottom_aggregate_abstain_rate"],
                    rb["M3_blackdot_abstain_flags_rubric"],
                    rb["M4_top_per_instance_rate_range"]],
                "note": ("基线数字与 run-r16/run-r19 内嵌输入重放/分型件"
                         "实测装载交叉核对一致（fail-closed：live 与登记"
                         "不符即 FAIL）；registered=axis-plan 在案登记/"
                         "dev-r19 measured_rows/判据原文冻结值，live=本轮"
                         "从 run-doc/分型件重放装载实测；r18 行=run-r18 "
                         "live 复算+dev-r18 登记交叉核对"),
            },
            "guard_channel": {
                "metric": prep_doc_guard_channel()["metric"],
                "requirement": prep_doc_guard_channel()["requirement"],
                "observation": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（实测 %s，"
                    "r16 基线 live 重放 0/0/0）=%s；G2=guard_ok=True "
                    "维持（top 几何门面积比出局条目 R19=%d→R20=%d）"
                    "=%s；任一破坏→reject 支成立+按 plan "
                    "early_stop_rule 出局"
                    % (list(by_instance.values()),
                       "满足" if g1_ok else "破坏",
                       len(geo_r19), len(geo_r20),
                       "满足" if g2_ok else "破坏")),
                "g1_ok": g1_ok,
                "g2_geometry_gate_r19": len(geo_r19),
                "g2_geometry_gate_r20": len(geo_r20),
                "g2_guard_ok": guard_ok,
                "guards_ok": guards_ok,
                "note": ("守门通道按 r20-prep-record attribution_plan."
                         "guard_channel 与 axis-plan guards 独立复核；"
                         "G 破坏经 reject 支字面并入字母裁决（本轮 G1 "
                         "破坏=reject_guards 支）"),
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "r11–r19 run-record courtyard_tracking 在案先例延续）——"
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
                "abstain_rate_r20_representative_note": (
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
                    "（6/14，代表配置）→r20 见代表配置"
                    "分列；主通道三分判据与门各自独立计算、互不凌驾"
                    "（prep-record descriptive_boundary_note 原文语义）"
                    "——门联合评价与字母裁决分列不合并"),
            },
            "r20_total_flags_note": (
                "六实例合计 %d 旗标（非弃权 %d、弃权 %d；全旗标合计弃权"
                "率 %s 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道；ordering 首键 M1="
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
            f"supported=「{adj['supported'][:80]}…」；"
            f"reject=「{adj['reject'][:80]}…」；"
            f"marginal=「{adj['marginal'][:80]}…」"
            "（r20-prep-record.json hypothesis_test.adjudication 判据原文"
            "全文见 preregistered_criteria_quote，轮后如实执行；结果无论"
            "方向均如实入账"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_lesson_continuation": metric_lesson_continuation,
        "reroute_continuation_r20": {
            "role": ("r12 假设通道被动追踪（round13–round19-dev-record "
                     "在案候选延续；零期望；非本轮预注册判据输入，"
                     "如实单列）"),
            "reroute_flag_detail_r20": reroute_rows,
            "reroute_total_r20": len(reroute_rows),
            "reroute_by_instance_r20": {
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
                                 "r20": len(reroute_rows)},
            "misuse_chain_note": (
                "滥用型弃权旗计数链（r12 口径，旗级 location_evidence "
                "子串命中）：r10=2→r11=1→r12=0→r13 被动追踪=1（R13T-009 "
                "在案）→r14=0（R14T-004 子串零命中）→r15 机械命中=1"
                "（R15T-001 非弃权旗含「蛇形」子串——否定式援引、非滥用"
                "型引用，run-r15 在案）→r16=0（在案）→r17=0（R17T-002 "
                "子串零命中、存在性弃权）→r18=0（在案）→r19=0（3 条 "
                "reroute 旗级子串零命中）→r20=0（2 条 reroute 旗级子串"
                "零命中）——不构成 r20 判据输入"
                "（两判据分列互不凌驾）"),
        },
        "stratified_observation": {
            "top": {"r16_by_instance_live": r16_top_rates_live,
                    "r16_range_live": AXIS_R16_M4_TOP_RANGE,
                    "r17_by_instance": run_r17_top_rates,
                    "r18_by_instance": r18_top_rates,
                    "r19_by_instance": r19_top_rates,
                    "r20_by_instance": top_rates,
                    "r20_range": top_range,
                    "direction": ("r16 三实例 %s（轮内极差 %s）→r17 %s/"
                                  "%s/%s→r18 %s/%s/%s（极差 %s）→r19 %s/"
                                  "%s/%s（极差 %s）→r20 三"
                                  "实例 %s/%s/%s（轮内极差 %s）——组合轮、"
                                  "实例群重抽混杂照旧下实例层的方向性"
                                  "对照（聚合 M1 %d/%d=%s vs r16 基线 "
                                  "27/35=0.771429、r17 的 22/25=0.88、"
                                  "r18 的 20/31=0.645161、r19 的 18/39="
                                  "0.461538；轮内实例差异照旧）"
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
                                     top_rates["top-i1"],
                                     top_rates["top-i2"],
                                     top_rates["top-i3"], top_range,
                                     abst_top, flags_top, top_rate))},
            "bottom": {"r16_by_instance_live": r16_bottom_rates,
                       "r16_range_live": r16_bottom_range,
                       "r19_by_instance_live": run_r19["view_layer"][
                           "bottom"]["abstain_rate"]["by_instance"],
                       "r20_by_instance": bottom_rates,
                       "r20_range": bottom_range,
                       "direction": ("r16 三实例 %s（极差 %s）→r19 %s/%s/"
                                     "%s→r20 三实例 %s/%s/%s（极差 %s）"
                                     "——bottom 聚合 M2 %d/%d=%s vs r16 "
                                     "的 12/14=0.857143、r18 的 13/19="
                                     "0.684211、r19 的 4/7=0.571429"
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
                             run_r16: dict, run_r17: dict, run_r18: dict,
                             run_r19: dict) -> dict:
    """courtyard 被动追踪（r11–r19 run-record courtyard_tracking 在案
    先例延续；零阈值改动、零期望；r20 courtyard 类旗标与命中如实入账
    ——top 弃权 3 条（applied-top-i2 R20T-003+prep1-top-i2 R20T-006/008，
    (iii-a) 残余弃权支）+bottom 非弃权 2 条（bottom-i1 两板 R20B-003/
    006，(iii-a) 间隙支负责任报告=G1 守门字面破坏的直接构成）。"""
    note_source = {
        "path_rel": REL_PREP_R20, "sha256": _sha(REL_PREP_R20),
        "quote": None,
        "note": ("r20-prep-record 无 secondary_observation 节——本轮"
                 "courtyard 被动追踪=run-record 链先例延续（r11–r19 "
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
        "r20_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": ("弃权旗不参与匹配（abstain 单列）；本轮 "
                             "courtyard 弃权旗=top %d 条+bottom %d 条"
                             "（top 3 条全部=(iii-a) 残余弃权支路径；"
                             "bottom 零弃权 courtyard、非弃权 2 条="
                             "bottom-i1 间隙支报告（G1 守门字面破坏的"
                             "直接构成）；对照 r19 的 top 4+bottom 0 "
                             "全弃权、r18 的 top 5+bottom 0 全弃权，"
                             "如实登记）"
                             % (top_abstain_cnt, bot_abstain_cnt)),
        },
        "courtyard_matches_r20": sum(r["matches"] for r in non_abstain_rows),
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
            "r16 回升 1 条（R16T-001↔AP-6）、r17–r19 零命中；r20 非弃权 "
            "courtyard=%d 条（命中=%d，如实登记）；GT/阈值零改动"
            % (len(non_abstain_rows),
               sum(r["matches"] for r in non_abstain_rows))),
        "bottom_observation": {
            "fact": ("R20 bottom %d 旗（bottom-i1 6+bottom-i2 4+"
                     "bottom-i3 4）=非弃权 %d（黑点接触报告 4+placement "
                     "报告 2+courtyard 间隙支报告 2）+弃权 %d（bottom-i3 "
                     "黑点-焊盘接触存在性弃权 4）："
                     "零匹配属结构性（GT 13 条全部 side=top，bottom GT "
                     "无源在案 gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，"
                     "如实）；courtyard 类旗标=2（全部非弃权，bottom-i1 "
                     "两板 R20B-003/006；r14 弃权 4 条/r15 零旗标/r16 "
                     "弃权 2 条/r17 弃权 1 条/r18 零旗标/r19 零旗标/r20 "
                     "非弃权 2 条，逐轮构成如实分列）；弃权构成见 reader."
                     "flag_count.by_category；本轮零旗标格=0"
                     "（12 格全部≥1 旗；r19 的 bottom-i3 零旗标实例未"
                     "再现）"
                     % (bot_flags_total, bot_nonabstain_total,
                        bot_abstain_total)),
            "evidence": QUANT_CRITERION_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）——bottom 派次全部"
                               "实际使用 §4(i) 量化判据（绿色翼瓣/空隙形态"
                               "判入系统性正常路径或不判正常报告路径）"),
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
    axis_plan = _json_load(REL_AXIS_PLAN)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, run_r12, run_r13,
        run_r14, run_r15, run_r16, run_r17, run_r18, run_r19,
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

    prep_r20 = _json_load(REL_PREP_R20)
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
            "五键投影（process-v1 §2 步骤3）；R20 reroute 类两旗 "
            "location_evidence 逐字在案（applied/prep1-top-i3 R20T-002/"
            "006 存在性弃权，「等长|蛇形」子串旗级零命中——"
            "reroute_continuation_r20 逐旗判定在案）；"
            "R20 top 弃权旗 14 条逐旗分型摘录在案（top_abstain_typology："
            "接触性 4+存在性 9+层归属其他 1）；"
            "R20 全部 18 条弃权旗逐旗 rubric 族分类在案（black_dot_"
            "tracking.rubric_families）；(iii-a) 逐旗落支 13 条+间隙支 "
            "notes 级 2 派次+§5B/(iii-a) 援引计数分列在案（criterion_"
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
            "note": ("本轮 12 格全部≥1 旗（零旗格=0；对照 r19 的 2 格"
                     "零旗标=bottom-i3 两板、r17 的 2 格零旗标）——"
                     "measurement_design item 5 零分母→None 口径本轮未"
                     "触发（先例保留在案）；视角层 bottom 三实例弃权率"
                     "全部可计算、中位数=排序后第 2"),
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R20, "role": "r20_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R20)},
        {"path_rel": REL_PREP_R19, "role": "r19_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R19)},
        {"path_rel": REL_AXIS_PLAN,
         "role": "axis_experiment_plan_r17_r20_frozen",
         "sha256": _sha(REL_AXIS_PLAN)},
        {"path_rel": REL_DEV_R19,
         "role": "r19_dev_record_combination_decision_and_axis_ledger",
         "sha256": _sha(REL_DEV_R19)},
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
        {"path_rel": REL_RUN_R18, "role": "r18_run_record_reference",
         "sha256": _sha(REL_RUN_R18)},
        {"path_rel": REL_PREP_R16, "role": "r16_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R16)},
        {"path_rel": REL_PREP_R15, "role": "r15_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R15)},
        {"path_rel": REL_PREP_R14, "role": "r14_prep_record_prior_chain",
         "sha256": _sha(REL_PREP_R14)},
        {"path_rel": REL_GUIDANCE_R20,
         "role": "observation_guidance_r20_active",
         "sha256": _sha(REL_GUIDANCE_R20)},
        {"path_rel": REL_GUIDANCE_R19,
         "role": "observation_guidance_r20_transform_base",
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
         "role": "blackdot_probe_r18_context_anchor_hash_and_kind_only",
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
        "kind": "tl2_calibration_run_r20",
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
            "axis_id": ("A3_criterion_contact_clarification"
                        "+A2_blackdot_instrument_annotation"),
            "nature": INSTRUMENT_NATURE,
            "note": prep_r20["instrument_change"]["note"],
            "declaration": prep_r20["instrument_change"]["declaration"],
            "renders_registered": [
                {"state_side": e["state_side"], "path_rel": e["path_rel"],
                 "sha256_measured": e["sha256_measured"],
                 "sha256_witness_registered":
                     e["sha256_witness_registered"],
                 "witness_record": e["witness_record"],
                 "match": e["match"]}
                for e in prep_r20["instrument_change"]["renders"]],
            "components": [
                "渲染零变更=renders-r14b 四图字节复用（与 r14–r19 "
                "盲读同一批文件；no_instrument_change=true）"],
            "unchanged_components": list(prep_r20["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "axis": v["axis"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v.get("attribution_channel"),
                 "instrument_change": v["instrument_change"]}
                for v in prep_r20["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r20["protocol_amendment"][
                    "version"],
                "amendment_mode": "none（协议侧零变更、无新增版本）",
                "v1_file_preserved": prep_r20["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("协议侧零变更：v1.1+v1.2 原文适用（纯 Read 直读"
                         "规约自 r12 起随派发指令生效，本轮照旧；v1.1 的 "
                         "n=3 多实例与聚合口径全部沿用）；v1 文件零字节"
                         "保留、不回写；本轮无新增协议版本文件"),
            },
            "attribution_note": prep_r20["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R19, "sha256": _sha(REL_PREP_R19)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1+v1.2 维持（沿用，无新增"
                                          "版本；v1 文件零字节保留，见 "
                                          "protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；r20 指引 §6 示例旗 ID 前缀 R20T-/R20B- 随指引"
            "落盘固化（机械替换，无需派发层"
            "覆盖，per r20-prep-record protocol_amendment.naming）；"
            "实例间编号独立；"
            "r20 实测编号行为=6 智能体各包两板、编号跨板连续（与 "
            "prep-record naming「同实例跨板连续」声明全部相符；对照 "
            "r19 混合行为如实登记），见 "
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
                    "r13 指引 §4（经 r20 指引承 r19 基座原文+(iii-a) 承继+"
                    "§5B 节并入适用，本轮指引=observation-guidance-r20.md，"
                    "§2–§7 除 §5B 新增节外分段与 r19 逐字相等断言在案）："
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
                    "视觉贴近直接计为交叠）；(iii-a) 可操作分辨条款（本轮"
                    "增补）：(1) 间隙支=可辨认连续间隙带→按「视觉贴近」"
                    "继续 (i)(ii) 与三路出口判定、不得弃权；(2) 侵入支="
                    "边缘直接相连或明显侵入→按「接触/交叠」处理并照常输出"
                    "旗标；(3) 残余弃权支=两者均无→方按 (iii) 原文弃权；"
                    "反放宽条款原文保留（「仅因形态不熟悉、不确定其设计"
                    "含义」仍不构成判为正常设计特征的理由）；量化阈值为"
                    "一般判据、非期望清单；§3A 示例 c 收窄判据原文"
                    "适用；(iii-a) 可操作分辨条款（随 r19 基座逐字承继）："
                    "(1) 间隙支=可辨认连续间隙带→按「视觉贴近」继续 "
                    "(i)(ii) 与三路出口判定、不得弃权；(2) 侵入支=边缘"
                    "直接相连或明显侵入→按「接触/交叠」处理并照常输出"
                    "旗标；(3) 残余弃权支=两者均无→方按 (iii) 原文弃权；"
                    "§5B 黑点仪器注记（自 r18 逐字转录、仪器事实非判据）："
                    "反指示声明「不构成任何判据、期望清单或『应判为正常/"
                    "无需报告』的指示」随节落盘；"
                    "abstain=true=现象是否存在或归属哪类无法负责任"
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
                                      "（blackdot-probe-r18.json 与 "
                                      "framing/witness 记录不进任何 "
                                      "reader 上下文）、零 legend/零其他"
                                      "解释（判读输入=指引+单张 PNG+派发"
                                      "指令）；每图独立判读；跨实例/跨视角"
                                      "禁止交流（独立性亦为组合轮可加性"
                                      "裁决有效性的前提）"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R20,
                                 "sha256": _sha(REL_GUIDANCE_R20),
                                 "frozen_before_read": True,
                                 "transform_mode":
                                     "mechanical_transform_derive",
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R19,
                                     "sha256": _sha(REL_GUIDANCE_R19),
                                     "role": ("r20 指引的机械变换基座"
                                              "（§2–§7 除 §5B 新增节外与 "
                                              "r19 逐字相等、§4(iii-a) 随"
                                              "基座承继；r19 指引=r19 轮"
                                              "落盘产物）")},
                                 "s5b_source_ref": {
                                     "path_rel": REL_GUIDANCE_R18,
                                     "sha256": _sha(REL_GUIDANCE_R18),
                                     "role": ("§5B 黑点仪器注记节转录源"
                                              "（r18 指引 §5B 全文逐字"
                                              "转录、content_sha256="
                                              "19ecdb42 跨代交叉锚一致）")},
                                 "change_note": GUIDANCE_NOTE},
            },
        "note": ("轮次预注册链：axis-experiment-plan-r17-r20.json"
                 "（b6ec6467…，stage2 组合定义+comparison_rule+守门+"
                 "early_stop_rule+combination_decision_rule，先于 R17–R21 "
                 "任何实验轮盲读冻结；用户 2026-09-09「三条轴单独/组合/"
                 "全组合尝试，选择收益最大的继续」user_directive_note "
                 "在案）→dev-r19 combination_decision_application"
                 "（0e2fdd69…，early_stop_shortcut 触发+排序 r19_axis3 "
                 "第一/r18_axis2 第二→r20_recommendation=轴3+轴2 组合、"
                 "preregistration_required=true 在案）→r20-prep-record.json"
                 "（e29ee2a3…，本轮预注册件，measurement_design 五条"
                 "聚合口径与 hypothesis_test.adjudication 三分判据"
                 "（supported=R20 四元组 ordering 字典序不劣于最优单轴 "
                 "r19 (0.461538,0.571429,4,0.211111)/marginal=未达 "
                 "supported 但 M1 <0.771429 且 G1/G2 维持=不可加采最优"
                 "单轴/reject=M1 ≥0.771429 或 G1/G2 任一破坏）"
                 "先于盲读冻结；instrument_change.changed=false；"
                 "guidance=机械变换（§5B+(iii-a) 并集合成）；渲染="
                 "renders-r14b 字节"
                 "复用）先于本轮盲读落盘（零 GT 暴露声明在案 "
                 "no_visual_reading=true；pre_round_review="
                 "satisfied_by_plan——axis-plan stage2 定义+dev-r19 组合"
                 "决策在案）→判读指引=observation-guidance-r20.md"
                 "（9cdac9ed…，r19 指引基座机械变换产物+§5B 自 r18 逐字"
                 "转录（cadcb8f3 跨代锚）+§4(iii-a) 随基座承继，本轮"
                 "唯一判读依据；判据文本零改动、反指示声明随 §5B 落盘）"
                 "→渲染零变更（renders-r14b 四图字节复用，四 PNG sha="
                 "witness-r14b 登记值=prep-record 登记值三方一致）→"
                 "12 次盲读（12 件哈希前缀逐字钉死：044486bb/d2c1b7da/"
                 "1aa66143/e5e6a5d9/11edbc4d/42d7c2e8/c95f1620/3ecf232c/"
                 "80961e4e/1765d865/a852215f/1691b7aa）→比对记录"
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
                     "变更=renders-r14b 字节复用，verdict=marginal）run "
                     "在案；"
                     "R20=stage2 组合轮（轴3+轴2 判读指引合成=§5B+(iii-a) "
                     "两增补并集；渲染零变更=renders-r14b 四图字节复用；"
                     "执行 axis-plan stage2 R20="
                     "A3_criterion_contact_clarification+"
                     "A2_blackdot_instrument_annotation；执行合法性="
                     "dev-r19 combination_decision_application 在案）；"
                     "轮间对比由后续 round20-dev-record（另包"
                     "落盘）与 channel_attribution、hypothesis_test 承载"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案；12 件"
            "哈希前缀 044486bb/d2c1b7da/1aa66143/e5e6a5d9/11edbc4d/"
            "42d7c2e8/c95f1620/3ecf232c/80961e4e/1765d865/a852215f/"
            "1691b7aa 盘态钉死），"
            "比较器/视角层聚合/双口径归并/代表配置选取/通道重放/rubric "
            "机械分型为纯函数（六实例旗数 8/8/6/6/4/4→代表配置 "
            "top-i1+bottom-i2（top 中位 8 不唯一=top-i1/top-i2 同值→先序 "
            "top-i1；bottom 中位 4 不唯一=bottom-i2/bottom-i3 同值→先序 "
            "bottom-i2，tie 如实注明）唯一可复算），无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-09-r20（事件序="
            "axis-experiment-plan-r17-r20（b6ec6467…，冻结件在案）→"
            "dev-r19 combination_decision_application（0e2fdd69…，组合"
            "决策在案）→"
            "r20-prep-record"
            "（e29ee2a3…，本轮预注册件，先于盲读冻结）→r20 指引机械"
            "变换落盘（9cdac9ed…，r19 基座+§5B 自 r18 转录，本轮唯一"
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
                                run_r19: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """run-r20 实测数字与预注册判据复算一致性（fail-closed）。"""
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 8, "top-i2": 8, "top-i3": 6, "bottom-i1": 6,
                  "bottom-i2": 4, "bottom-i3": 4}:
        _fail("实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 4, "top-i2": 6, "top-i3": 4, "bottom-i1": 0,
                "bottom-i2": 0, "bottom-i3": 4}:
        _fail("实例弃权记账与实测不一致")
    if run_doc["reader"]["flag_count"]["total"] != 36:
        _fail("全旗标总数与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.333333 \
            or agg["flag_count_total"] != 12 \
            or agg["abstain_count_total"] != 4:
        _fail("代表配置聚合与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "reject":
        _fail("假设字母裁决与预注册判据复算不符")
    if hyp["hypothesis_id"] != "axis-plan-r20-combo-additivity":
        _fail("hypothesis_id 与预登记不符")
    m = hyp["measurement"]
    if m["contact_family_abstain_flags_rubric_r20"] != 2 \
            or m["contact_r16_baseline_registered"] != 10:
        _fail("contact 计数与实测不一致")
    if m["top_abstain_flags_r20"] != 22 or m["top_abstain_count_r20"] != 14 \
            or m["top_abstain_rate_r20"] != 0.636364:
        _fail("ordering 首键 M1 计数与实测不一致")
    if m["m4_top_rate_range_r20"] != 0.25:
        _fail("ordering 第 4 键 M4 计数与实测不一致")
    if m["crit_reject_m1_ge_0_771429"] is not False:
        _fail("reject_m1 支布尔与实测不一致（M1=0.636364 应 <0.771429）")
    if m["crit_reject_guards_broken"] is not True:
        _fail("reject_guards 支布尔与实测不一致（G1 应破坏）")
    if m["crit_supported_ordering_not_worse_than_r19"] is not False:
        _fail("supported 支布尔与实测不一致（ordering 应劣于 r19）")
    if m["crit_marginal_m1_lt_0_771429"] is not True:
        _fail("marginal 支布尔与实测不一致")
    if m["top_abstain_rate_r16_baseline_value"] != 0.771429:
        _fail("r16 基线值与在案登记不一致")
    bso = m["bottom_side_observation"]
    if bso["bottom_courtyard_flags_total_r20"] != 2 \
            or bso["bottom_abstain_flags_r20"] != 14 \
            or bso["bottom_abstain_count_r20"] != 4 \
            or bso["bottom_abstain_rate_r20"] != 0.285714 \
            or bso["bottom_courtyard_non_abstain_by_instance_r20"] != {
                "bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0} \
            or bso["bottom_rate_direction_vs_r16"] != "improved":
        _fail("bottom 侧观察计数与实测不一致")
    g = m["guard_channel"]
    if g["g1_ok"] is not False or g["g2_guard_ok"] is not True \
            or g["guards_ok"] is not False \
            or g["g2_geometry_gate_r19"] != 0 \
            or g["g2_geometry_gate_r20"] != 0:
        _fail("守门 G1/G2 计数与实测不一致")
    mo = hyp["mechanism_observation"]
    tt = mo["top_abstain_typology"]
    if tt["type_counts"] != {"contact": 4, "existence": 9,
                             "other_layer": 1} \
            or tt["top_abstain_flags_total"] != 14:
        _fail("top 弃权分型计数与实测不一致")
    bd = mo["black_dot_tracking"]
    if len(bd["black_dot_flags"]) != 6 or bd["all_abstain"] is not True \
            or bd["by_instance"] != {"top-i1": 2, "top-i2": 0, "top-i3": 0,
                                     "bottom-i1": 0, "bottom-i2": 0,
                                     "bottom-i3": 4} \
            or bd["blackdot_to_non_abstain_count"] != 6 \
            or len(bd["black_dot_non_abstain_flags"]) != 6 \
            or bd["judged_normal_dispatches"]["count"] != 4:
        _fail("黑点族计数与实测不一致")
    if bd["rubric_families"]["counts"] != R20_FAMILY_COUNTS_REGISTERED \
            or bd["rubric_families"]["replay_proof"]["per_flag_total"] \
            != 132:
        _fail("rubric 族计数/重放证明与实测不一致")
    cco = mo["criterion_citation_observation"]
    if cco["branch_counts_flag_level"] != {
            "branch1_gap_report": 2, "branch2_intrusion_report": 4,
            "branch3_residual_abstain": 7} \
            or cco["branch1_notes_level_dispatches"] != 2 \
            or cco["citation_counts"]["flag_level_s5b_literal"] != 0 \
            or cco["citation_counts"]["flag_level_iiia_literal"] != 0 \
            or cco["citation_counts"]["flag_level_branch_literal"] != 0 \
            or cco["citation_counts"]["notes_level_s5b"] != 4 \
            or cco["citation_counts"]["notes_level_iiia"] != 4:
        _fail("§5B/(iii-a) 援引/落支计数与实测不一致")
    if mo["bottom_side_observation_maintenance"]["counts"][
            "blackdot_abstain_flags_rubric_r20"] != 6 \
            or mo["bottom_side_observation_maintenance"]["counts"][
                "zero_flag_dispatch_count"] != 0:
        _fail("bottom 侧观察黑点/零旗计数与实测不一致")
    ledger = mo["experiment_comparison_ledger"]
    if ledger["r20_measured"]["M1"] != 0.636364 \
            or ledger["r20_measured"]["M2"] != 0.285714 \
            or ledger["r20_measured"]["M3"] != 6 \
            or ledger["r20_measured"]["M4"] != 0.25 \
            or ledger["r20_measured"]["contact_family_abstain_flags_rubric"] \
            != 2:
        _fail("实验对照账四元组与实测不一致")
    if ledger["ranking_by_comparison_rule"]["r20_eligibility"] is not False \
            or ledger["ranking_by_comparison_rule"][
                "ranking_order_best_first"] != ["r19_axis3", "r18_axis2",
                                                "r16_baseline",
                                                "r17_axis1"]:
        _fail("comparison_rule 排序（资格门剔除 r20）与实测不一致")
    if ledger["significant_benefit_vs_r16"]["met"] is not True \
            or ledger["significant_benefit_vs_r16"][
                "r20_m1_absolute_drop"] != 0.135065:
        _fail("显著收益对照与实测不一致")
    if ledger["stage2_conclusion"]["verdict"] != "reject":
        _fail("阶段2 结论位与字母裁决不一致")
    gs = mo["green_semantics_by_instance"]["green_semantics_by_instance"]
    if sum(1 for v in gs.values() if v["§5A_cited"]) != 1 \
            or sum(1 for v in gs.values() if v["§5B_cited"]) != 1:
        _fail("绿区语义化 §5A/§5B 引用与实测不一致（实例级各 1/3 实例；"
              "派次级 2/6 由 evidence 表 cites 计数）")
    if sum(1 for e in mo["green_semantics_by_instance"]["evidence"]
           if e.get("cites_5A")) != 2 \
            or sum(1 for e in mo["green_semantics_by_instance"]["evidence"]
                   if e.get("cites_5B")) != 2:
        _fail("绿区语义化 §5A/§5B 派次级引用与实测不一致（应各 2/6 派次）")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.25 \
            or vl["bottom"]["abstain_rate_range"] != 1.0:
        _fail("视角层极差与实测不一致（M4 方向）")
    if vl["bottom"]["abstain_rate"]["median"] != 0.0:
        _fail("bottom 弃权率中位数应为 0.0（本轮无 None 实例）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 0 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.0:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (mm["flag_id"], mm["gt_id"]) for n in INSTANCE_ORDER
        for mm in inst[n]["combined"]["matches_detail"])
    if matches_all != []:
        _fail("matches 明细与实测不一致（r20 全部零命中）")
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
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 2:
        _fail("reroute 类产量与被动追踪登记不一致")
    # 通道条目数与实测一致（几何 R19 0→R20 0；类别 R19 0→R20 0）
    ca = run_doc["channel_attribution"]
    cat_r20_entries = ca["channel_2_category_gate"][
        "r20_category_mismatch_entries"]
    if len(ca["channel_1_geometry_gate"]["r20_area_ratio_rejected_entries"]) \
            != 0 or len(cat_r20_entries) != 0:
        _fail("通道条目数与实测声明不一致")
    # courtyard 追踪与实测一致（r20 非弃权 courtyard=2、弃权=3、命中=0）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r20"] != 0 or len(
            ct["r20_courtyard_flags"]["non_abstain"]) != 2:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r20_courtyard_flags"]["abstain"]) != 3:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 零旗标派次=0（12 格全部≥1 旗）
    if run_doc["reader"]["zero_flag_parts"]["parts"] != []:
        _fail("零旗标派次与实测不一致（应为空）")
    # 逐旗判定/工具规约/量化判据/分型/黑点/placement/绿区/间隙支摘录
    # 逐字在案
    for r in hyp["reroute_continuation_r20"]["reroute_flag_detail_r20"]:
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r20")

    # 数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11),
        _json_load(REL_RUN_R12), _json_load(REL_RUN_R13),
        _json_load(REL_RUN_R14), _json_load(REL_RUN_R15),
        _json_load(REL_RUN_R16), _json_load(REL_RUN_R17),
        _json_load(REL_RUN_R18), _json_load(REL_RUN_R19), parsed,
        raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R20), run_bytes,
                         "calibration-run-r20.json")
    run_sha = _sha(REL_RUN_R20)
    # round20-dev-record 由后续 dev-record 包落盘（本包零 dev-record 写入）

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s74-cal-r20] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 18、弃权 18）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s74-cal-r20] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s74-cal-r20] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s74-cal-r20] zero_flag_parts: "
          f"{[(z['instance'], z['state']) for z in run['reader']['zero_flag_parts']['parts']]}"
          f"（12 格全部≥1 旗、零旗标口径未触发）")
    print(f"[s74-cal-r20] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}"
          f"（bottom 中位数={vl['bottom']['abstain_rate']['median']}）")
    print(f"[s74-cal-r20] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13"
          f"（本轮全部零命中；对照 r19 唯一命中 R19T-009 未再现）")
    print(f"[s74-cal-r20] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    m = hyp["measurement"]
    print(f"[s74-cal-r20] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；三分判据=ordering 字典序可加性比较："
          f"R20 四元组=({m['r20_m_tuple_6dp']['M1']},"
          f"{m['r20_m_tuple_6dp']['M2']},{m['r20_m_tuple_6dp']['M3']},"
          f"{m['r20_m_tuple_6dp']['M4']}) vs r19 基准 "
          f"({m['r19_reference_tuple']['M1']},{m['r19_reference_tuple']['M2']},"
          f"{m['r19_reference_tuple']['M3']},{m['r19_reference_tuple']['M4']})"
          f"（dev-r19 装载+run-r19 live 复算交叉核对）→不劣于="
          f"{m['crit_supported_ordering_not_worse_than_r19']}；(r) 支 "
          f"M1 ≥0.771429→crit_reject_m1="
          f"{m['crit_reject_m1_ge_0_771429']}、G1/G2 破坏="
          f"{m['crit_reject_guards_broken']}（G1=bottom courtyard 非弃权 "
          f"实测 {m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r20']}）；"
          f"(m) 支 M1 <0.771429="
          f"{m['crit_marginal_m1_lt_0_771429']}（M1={m['top_abstain_count_r20']}/"
          f"{m['top_abstain_flags_r20']}={m['top_abstain_rate_r20']}，r16 基线双侧复算 "
          f"{m['top_abstain_rate_r16_baseline_live']}"
          f"={m['top_abstain_rate_r16_baseline_value']}）；contact 族 "
          f"{m['contact_family_abstain_flags_rubric_r20']}"
          f"（top {m['contact_family_abstain_flags_rubric_r20']} 全视）；落支={m['letter_branch']}"
          f"；守门 G1={m['guard_channel']['g1_ok']}/G2="
          f"{m['guard_channel']['g2_guard_ok']}（early_stop 触发="
          f"{m['guard_channel']['guards_ok'] is not True}）；机制观察单列）")
    print(f"[s74-cal-r20] 侧观察（M2 bottom 维持性，单列不影响字母）："
          f"bottom 全旗聚合弃权={m['bottom_side_observation']['bottom_abstain_count_r20']}"
          f"/{m['bottom_side_observation']['bottom_abstain_flags_r20']}"
          f"={m['bottom_side_observation']['bottom_abstain_rate_r20']}"
          f" vs r16 基线 12/14=0.857143、r18 13/19=0.684211、r19 4/7=0.571429"
          f"（{m['bottom_side_observation']['bottom_rate_direction_vs_r16']}）；"
          f"bottom courtyard 非弃权={m['bottom_side_observation']['bottom_courtyard_non_abstain_by_instance_r20']}"
          f"/courtyard 旗总数={m['bottom_side_observation']['bottom_courtyard_flags_total_r20']}")
    mo = hyp["mechanism_observation"]
    print(f"[s74-cal-r20] 机制观察要点：rubric 族计数="
          f"{mo['black_dot_tracking']['rubric_families']['counts']}"
          f"（r13–r16 132 条重放对拍逐一相等；contact=2 vs r16 基线"
          f" 10、黑点=6 vs r18 13/r19 4、存在性其他=10 vs r18 12/r19 14）；"
          f"援引分记：旗级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_s5b_literal']}"
          f"/(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_iiia_literal']}"
          f"/分支(="
          f"{mo['criterion_citation_observation']['citation_counts']['flag_level_branch_literal']}"
          f"；notes 级 §5B="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_s5b']}"
          f"/12、(iii-a)="
          f"{mo['criterion_citation_observation']['citation_counts']['notes_level_iiia']}"
          f"/12；(iii-a) 落支="
          f"{mo['criterion_citation_observation']['branch_counts_flag_level']}"
          f"+间隙支 notes 级 "
          f"{mo['criterion_citation_observation']['branch1_notes_level_dispatches']} "
          f"派次；黑点旗 6 条全弃权 "
          f"{mo['black_dot_tracking']['by_instance']}（vs r18=13/r19=4）；"
          f"黑点转非弃权旗 "
          f"{mo['black_dot_tracking']['blackdot_to_non_abstain_count']} 条"
          f"（全 bottom：i1 4+i2 2）；黑点判正常派次 "
          f"{mo['black_dot_tracking']['judged_normal_dispatches']['count']}/12"
          f"（对照 r15=3/r16=2/r18=2/r19=3）；四元组账 "
          f"(M1,M2,M3,M4)=(0.636364,0.285714,6,0.25) vs r16 "
          f"(0.771429,0.857143,12,0.261904)/r18 (0.645161,0.684211,13,"
          f"0.277778)/r19 (0.461538,0.571429,4,0.211111)；排序（资格门"
          f"剔除 r20）="
          f"{mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['ranking_order_best_first']}"
          f"（r20_eligibility={mo['experiment_comparison_ledger']['ranking_by_comparison_rule']['r20_eligibility']}）；"
          f"阶段2 结论位={mo['experiment_comparison_ledger']['stage2_conclusion']['conclusion'][:60]}…；"
          f"top 弃权分型="
          f"{mo['top_abstain_typology']['type_counts']}；reroute 2 旗"
          f"（弃权 2、子串零命中）")
    print(f"[s74-cal-r20] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s74-cal-r20] channel_attribution: "
          f"geo R19={len(ca['channel_1_geometry_gate']['r19_area_ratio_rejected_entries'])}"
          f"→R20={len(ca['channel_1_geometry_gate']['r20_area_ratio_rejected_entries'])}, "
          f"cat R19={len(ca['channel_2_category_gate']['r19_category_mismatch_entries'])}"
          f"→R20={len(ca['channel_2_category_gate']['r20_category_mismatch_entries'])}")
    print(f"[s74-cal-r20] commit: run={run_status}（round20-dev-record 由"
          f"后续包落盘，本包零写入）")
    print(f"[s74-cal-r20] sha256[:8] calibration-run-r20.json = "
          f"{run_sha[:8]}")
    print(f"[s74-cal-r20] sha256 calibration-run-r20.json = {run_sha}")
    print("[s74-cal-r20] R20 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")



if __name__ == "__main__":
    
    main()
