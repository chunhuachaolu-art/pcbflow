#!/usr/bin/env python
"""CAL-R19-PREP：R19 轴3 判据侧单变量轮（§4(iii) 可操作分辨条款；渲染零变更）
预备包（只新建三个文件：scripts/s70_calibration_r19_prep.py 本体、
out/v3-tl2/calibration/observation-guidance-r19.md 与
out/v3-tl2/calibration/r19-prep-record.json；datasets/ 与 out/ 既有文件
只读、零改动，observation-guidance-r15.md 零字节不动）。

R19 轮性质（预注册，非事后）：**轴3 判据侧单变量轮（§4(iii) 可操作分
辨条款；axis-experiment-plan-r17-r20 stage1 之一）**——渲染零变更=
renders-r14b 四图字节复用（四 PNG 实测=witness-r14b 登记值）；本轮唯
一判读变更=判读指引 §4 增补 (iii-a) 可操作分辨条款：在 (iii) 接触性判
据句之后、既有对照说明块之前插入，把「无法区分」操作化为证据可见性三
支判据（见间隙证据→按视觉贴近继续判定；见侵入证据→按接触/交叠处理；
两者均无→方按 (iii) 原文弃权）。**本实验线首次触碰判据节——反放宽是
最高约束**：条款只收窄「真歧义弃权」的适用面（把有证据可判的情形引导
到负责任判定），不降低判断责任标准；反放宽条款与三路出口逐字保留；
§4 其余部分（量化判据 (i)(ii) 原文、总原则、confidence 定义、对照说明
块）逐字不动。执行 axis-experiment-plan-r17-r20（b6ec6467 冻结件）
stage1 R19=轴3（A3_criterion_contact_clarification，guidance 原文=
「r15 指引+§4(iii) 接触性判据补可操作分辨条款（方向=判定一致性，反放
宽条款逐字保留）」）；round18-dev-record next_iteration_targets[0] 同
口径指令；用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的
继续」。

指引生成=确定性机械变换（锚串命中数 fail-closed，锚恰 1 次否则 FAIL）。
任务枚举编辑：(1) 标题/round_id_constant R15→R19（含声明日期 bullet
2026-09-08→2026-09-09、本轮性质行按轴3 口径重写、示例 reader_id
reader-r15→reader-r19、示例旗 ID 前缀 R15T-（4 处）/R15B-（1 处）→
R19T-/R19B-）；(2) 「本轮变更声明」节正文整体替换（任务给定文本逐字）；
(3) §4 (iii) 接触性判据句之后、既有对照说明块之前增补 (iii-a) 条款
bullet（逐字）。另沿 s48/s54/s67（r13/r15/r18 指引侧机械变换）先例同
步轮次标识区（如实登记）——§1 与头部 bullet 区不在逐字冻结清单（冻结
区=§2–§7；本轮冻结区唯一例外=§4 内增补 (iii-a) 一条）。

功能：
  1. fail-closed 复核 observation-guidance-r15.md（d5babc93 锚；r19
     指引唯一变换基座，只读零写入）。
  2. fail-closed 复核 r15-prep-record.json（4c6cd919 锚；schema 血统）
     与 r18-prep-record.json（3fc054c4 锚；24 键结构镜像源）。
  3. fail-closed 复核 render-witness-r14b.json（b63771f9 锚）+四 PNG
     实测（bottom 两板同 d7284259、top 298bc620/b2f84524）——渲染零
     变更字节复用证明。
  4. fail-closed 复核 axis-experiment-plan-r17-r20.json（b6ec6467 锚）：
     stage1 R19=轴3 定义、r16 基线（M1=0.771429、M3=12、M4=0.261904）、
     守门 G1/G2/G3、用户指令原文。
  5. fail-closed 复核 round18-dev-record.json（a0c1f97c 锚）：
     next_iteration_targets[0] R19=轴3 指令；r18 参照计数（黑点 13/
     top 弃权分型 接触性 8+存在性 12）。
  6. fail-closed 复核 calibration-run-r16.json（2c1f8265 锚；M1 冻结值
     +guard_ok）；abstain-typology-r13-r16.json（6dadac8d 锚；contact
     族 r13–r16=8/15/5/10、r16=10 全 top、grand 38——预注册判据基线
     锚）；blackdot-probe-r18.json（a49441ac 锚；仅哈希+kind 复核，
     本轮零内容转录）。
  7. evaluation-protocol-v1.md 在盘且锚=22dc7337。
  8. 生成 observation-guidance-r19.md（8 组锚定编辑，命中数逐一断言；
     §1/§2/§3/§3A/§5/§5A/§6/§7 分段逐字保留断言+§4 前段/后段分段断言
     +关键 substring 断言+R15 残留零断言+新文本在位断言+(iii-a) 位置
     断言+§5A 原文逐字保留断言）。
  9. 落盘 r19-prep-record.json（canonical JSON；顶层键集合与 r18-prep-
     record 24 键逐键镜像；hypothesis_test=任务预注册判据逐字（文本→
     json.loads→常量→记录字段三层相等）；同参重建两次逐字节一致自证；
     防覆写守卫；落盘后回读验字节）。
 10. 打印：三文件 sha256、r19 相对 r15 字节数差、§4(iii-a) 实际落盘全
     文、四 PNG 比对结果、逐项断言通过清单。

判据数值自洽断言：contact supported 阈值 5=r16 基线 10 的一半（任务判
据文本原文）；M4 marginal 0.26 与 r16 基线 0.261904 相差 0.001904
≤0.005（「附近」语义）；contact 族基线序列 8/15/5/10 与 r16=10 全 top
（round_view r16|top=10、r16|bottom=0）为分型件实测装载——任务判据文
本数值与在案锚逐一相符（不符即停——防预注册文本与在案事实漂移）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-09/2026-09-09-r19）；
无 subprocess/网络/主机绝对路径；hash=sha256_file 字节口径（PNG 仅哈希
+magic，零内容判读、零像素读取）；不读 GT/ground-truth-*/reader-raw-*/
derivation-log-*/任何 compare/诊断内容产物；run-r16 仅读 hypothesis_test
顶层判据值字段做冻结值锚；无 git；r15 指引只读；记录内零 GT、零期望数
量/分布/坐标；指引内零轮次结果数字（基线数字仅入本编排侧记录）。

用法：python scripts/s70_calibration_r19_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R15 = CAL_DIR / "observation-guidance-r15.md"
GUIDANCE_R19 = CAL_DIR / "observation-guidance-r19.md"
R15_PREP_RECORD = CAL_DIR / "r15-prep-record.json"
R18_PREP_RECORD = CAL_DIR / "r18-prep-record.json"
BLACKDOT_PROBE = CAL_DIR / "blackdot-probe-r18.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
DEV_RECORD_R18 = CAL_DIR / "round18-dev-record.json"
RUN_R16 = CAL_DIR / "calibration-run-r16.json"
TYPOLOGY = CAL_DIR / "abstain-typology-r13-r16.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r19-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r19"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R15_SHA_PREFIX = "d5babc93"
R15_PREP_RECORD_SHA_PREFIX = "4c6cd919"
R18_PREP_RECORD_SHA_PREFIX = "3fc054c4"
BLACKDOT_PROBE_SHA_PREFIX = "a49441ac"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
DEV_RECORD_R18_SHA_PREFIX = "a0c1f97c"
RUN_R16_SHA_PREFIX = "2c1f8265"
TYPOLOGY_SHA_PREFIX = "6dadac8d"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

RENDR14B_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

#: 判据冻结值锚（r16 基线；axis-plan/run-r16/typology 实测装载）
CONTACT_R16_BASELINE = 10
CONTACT_ABSTAIN_BASELINE = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
CONTACT_SUPPORTED_THRESHOLD = 5
CONTACT_MARGINAL_THRESHOLD = 7
CONTACT_REJECT_THRESHOLD = 8
M4_R16_BASELINE = 0.261904
M4_SUPPORTED_THRESHOLD = 0.20
M4_MARGINAL_THRESHOLD = 0.26
M1_SUPPORTED_THRESHOLD = 0.85
GRAND_CONTACT_FLAGS = 38

# ---------------------------------------------------------------------------
# 预注册判据（逐字，先于任何盲读冻结；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "axis-plan-r19-criterion-operational",
  "hypothesis": "contact 族弃权（r16=10 全 top）与判定分歧的主因=§4(iii)「无法区分」无差别适用。可操作分辨条款把有证据可判的情形引导到负责任判定后，contact 族弃权显著回落、top 逐实例一致性改善，且不引起其他族弃权上升。",
  "adjudication": {
    "supported": "contact 族弃权旗数（全视，分型件 rubric 口径，r13–r16 链重放对拍后套用本轮）≤ 5（r16 基线 10 的一半）且 M4（top 逐实例弃权率极差）≤ 0.20 且 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）维持且 M1（top 全旗聚合弃权率）≤ 0.85",
    "marginal": "未达 supported 且（contact 族 ≤ 7 或 M4 ≤ 0.26（r16 基线 0.261904 附近））且 G1/G2 维持",
    "reject": "contact 族 ≥ 8 且 M4 > 0.26，或 G1/G2 任一破坏（按 axis-plan early_stop 出局）",
    "mechanism_observation_separate": "contact 族逐旗理由对照条款三支的落支分布（间隙支/侵入支/残余弃权——逐旗摘录）；(iii-a) 措辞在旗级/notes 级的援引计数；黑点族/存在性族计数（对照 r18：黑点 13/存在性其他 12——若显著上升=弃权转移如实记录）；M1/M2/M3/M4 四元组入实验对照账；gt 照常",
    "metric_lesson_separate": "跨轮实例群漂移混杂照旧；字母=预注册阈值命中与否的描述性结论；判据节首次变更的先例意义（后续判据侧迭代的模板纪律=增补式+反放宽逐字+锚断言）单列",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

# ---------------------------------------------------------------------------
# 指引机械变换锚与替换文本
# ---------------------------------------------------------------------------
OLD_TITLE = "# R15 轮 reader 判读指引（observation-guidance-r15）"
NEW_TITLE = "# R19 轮 reader 判读指引（observation-guidance-r19）"
DECL_HEADING = "## 本轮变更声明（预注册，非事后）"
SECTION1_HEADING = "## 1. 角色与任务"
OLD_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-08"
NEW_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-09"
OLD_ROUND_ID_BULLET = "- round_id_constant: `2026-09-08-r15`"
NEW_ROUND_ID_BULLET = "- round_id_constant: `2026-09-09-r19`"
OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（bottom 配色语义仪器注记配套"
    "轮）**。渲染零变更（复用 R14 冻结渲染件 renders-r14b）；本轮唯一"
    "变更=判读指引增补 §5A 渲染配色仪器注记节（颜色→来源映射显式化；"
    "预注册见下），指引落盘后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量判据侧变更轮（轴3 §4(iii) 可操作分辨条款轮；"
    "axis-experiment-plan-r17-r20 stage1 之一）**。渲染零变更（复用 R14 "
    "冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引 §4 增补 "
    "(iii-a) 可操作分辨条款（把接触性判据的「无法区分」操作化为证据可见"
    "性三支判据：见间隙证据→按视觉贴近继续判定；见侵入证据→按接触/交叠"
    "处理；两者均无→方按 (iii) 原文弃权；反放宽条款逐字保留），指引落盘"
    "后由编排侧重新盲读。")

#: 任务枚举编辑：「本轮变更声明」节正文整体替换（逐字，任务给定文本）
NEW_DECLARATION = (
    "本轮（R19）为轴3 判据侧单变量轮：相对 observation-guidance-r15 仅"
    "（1）更新标题与轮次标识，（2）重写本变更声明，（3）§4 增补 (iii-a) "
    "可操作分辨条款（在 (iii) 接触性判据句之后、既有对照说明块之前插入；"
    "把「无法区分」操作化为证据可见性三支判据——见间隙证据→按视觉贴近"
    "继续判定；见侵入证据→按接触/交叠处理；两者均无→方按 (iii) 原文弃"
    "权；条款为判定路径的澄清而非判断责任的放松；§4 其余全部文本含量化"
    "判据 (i)(ii)(iii) 原文、三路出口与反放宽条款逐字不变），（4）虚构示"
    "例旗 ID 前缀改为 R19T/R19B。渲染零变更：本轮使用与 R14 完全相同的 "
    "renders-r14b 四图（字节复用）。§2 类别枚举、§3/§3A 位置与判据示例、"
    "§5 courtyard 说明、§5A 渲染配色仪器注记（原文逐字保留）、§6 输出格"
    "式、§7 格式对齐提示全部逐字不变。预注册判据见 r19-prep-record.json "
    "hypothesis_test（先于任何盲读冻结）。")

#: §4(iii-a) 条款 bullet（任务给定逐字文本；作为 §4 内列表项插入）
BULLET_III_A = (
    "- (iii-a) 可操作分辨条款（本轮增补）：执行 (iii) 时按证据可见性三支"
    "操作——(1) 若两图形边缘之间能在本渲染中辨认出连续的间隙带（背景或底"
    "层颜色贯通），按「视觉贴近」处理并继续按 (i)(ii) 与三路出口判定，不"
    "得弃权；(2) 若两图形边缘直接相连或一图形边缘明显侵入另一图形内部，"
    "按「接触/交叠」处理并照常输出旗标；(3) 仅当两图形边缘看似相接、且既"
    "无可辨认的间隙带亦无可辨认的侵入证据时，方属「无法区分」，按 (iii) "
    "原文弃权。本条款只把「无法区分」收窄为「无任何可辨认证据」的情形，"
    "是判定路径的澄清而非判断责任的放松；「仅因形态不熟悉、不确定其设计"
    "含义」仍不构成判为正常设计特征的理由（原反放宽条款继续全部适用）。")

#: §4 内插入点锚=三路出口 bullet 行首（§4 内、既有对照说明块之前）
EXIT_ANCHOR = "- **三路出口显式化（判为正常设计特征的形态不报告）**"
SECTION5_HEADING = "## 5. courtyard 说明（中性）"
SECTION6_HEADING = "## 6. 输出格式（reader-raw 文件的确切 schema）"

#: 锚串在 r15 基座中的期望命中数（不符即停；声明区先行替换后计数收敛）
EXPECTED_HITS = {
    "title": 1,
    "decl_heading": 1,
    "section1": 1,
    "date_line": 1,
    "round_id_bullet": 1,
    "nature_line": 1,
    "prefix_R15T-": 4,
    "prefix_R15B-": 1,
    "reader_id": 1,
    "exit_anchor": 1,
}

#: §1/§2/§3/§3A/§5/§5A/§6/§7 分段逐字保留断言（§4 特殊处理：本轮唯一
#: 冻结区例外=§4 内增补 (iii-a) 一条，故 §4 拆前段/后段分别做逐字断言；
#: §6/§7 段先做旗前缀/reader-id 规格化再断言）
SECTION_PAIRS = [
    ("## 1. 角色与任务", "## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）"),
    ("## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）", "## 3. 位置口径"),
    ("## 3. 位置口径", "## 3A. 类别判据示例（判据说明，非期望清单）"),
    ("## 3A. 类别判据示例（判据说明，非期望清单）", "## 4. 置信度与弃权"),
    ("## 5. courtyard 说明（中性）",
     "## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）"),
    ("## 6. 输出格式（reader-raw 文件的确切 schema）",
     "## 7. 格式对齐提示"),
    ("## 7. 格式对齐提示", None),  # 至文件尾
]

#: 关键 substring 断言（判据零放宽（(iii-a) 增补外）+§5A 原文逐字+(iii-a)
#: 在位；逐条打印通过）
REQUIRED_SUBSTRING_VALUES = {
    "§2 类别封闭集：1. `silk_readability`": "1. `silk_readability`",
    "§2 类别封闭集末类：6. `other_advisory`": "6. `other_advisory`",
    "§3 收窄判据：邻域框收窄判据": "邻域框收窄判据",
    "§3A 示例 c：**「整段规则周期」判据**": "**「整段规则周期」判据**",
    "§4 confidence 定义：`confidence` ∈ [0,1]：你对「该现象存在且归类正确」的自信程度":
        "`confidence` ∈ [0,1]：你对「该现象存在且归类正确」的自信程度",
    "§4 总原则：**宁可 abstain 不硬标**": "**宁可 abstain 不硬标**",
    "§4 弃权适用于条：**弃权适用于：「是否存在 / 归属哪类」不确定**":
        "**弃权适用于：「是否存在 / 归属哪类」不确定**",
    "§4 弃权不适用于条：**弃权不适用于：仅「精确范围 / 边界 / 尺寸」不确定**":
        "**弃权不适用于：仅「精确范围 / 边界 / 尺寸」不确定**",
    "§4 量化判据 (i)：(i) **系统性正常特征判据（量化）**":
        "(i) **系统性正常特征判据（量化）**",
    "§4 量化判据 (ii)：(ii) **关注现象判据**": "(ii) **关注现象判据**",
    "§4 接触性判据 (iii) 头：(iii) **接触性判据（判「交叠/接触」类现象前适用）**":
        "(iii) **接触性判据（判「交叠/接触」类现象前适用）**",
    "§4 (iii) 原句全句逐字在位":
        "(iii) **接触性判据（判「交叠/接触」类现象前适用）**——须先分辨"
        "**真实接触**（图形材料连通）与**视觉贴近**（存在小于当前分辨率的"
        "间隙）：能负责任区分时按事实处理；无法区分时，接触与否按存在性不"
        "确定处理（按「弃权适用于」条输出弃权旗），不得将视觉贴近直接计为"
        "交叠。",
    "§4 反放宽条款：仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由":
        "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由",
    "§4 三路出口：**三路出口显式化（判为正常设计特征的形态不报告）**":
        "**三路出口显式化（判为正常设计特征的形态不报告）**",
    "§4 同等判断责任：判「正常设计特征」与判「关注现象」承担**同等判断责任**":
        "判「正常设计特征」与判「关注现象」承担**同等判断责任**",
    "§4 (iii-a) 条款头：(iii-a) 可操作分辨条款（本轮增补）：执行 (iii) 时按证据可见性三支操作":
        "(iii-a) 可操作分辨条款（本轮增补）：执行 (iii) 时按证据可见性三支操作",
    "§4 (iii-a) 间隙支：按「视觉贴近」处理并继续按 (i)(ii) 与三路出口判定，不得弃权":
        "按「视觉贴近」处理并继续按 (i)(ii) 与三路出口判定，不得弃权",
    "§4 (iii-a) 侵入支：按「接触/交叠」处理并照常输出旗标":
        "按「接触/交叠」处理并照常输出旗标",
    "§4 (iii-a) 残余弃权支：方属「无法区分」，按 (iii) 原文弃权":
        "方属「无法区分」，按 (iii) 原文弃权",
    "§4 (iii-a) 收窄声明：本条款只把「无法区分」收窄为「无任何可辨认证据」的情形":
        "本条款只把「无法区分」收窄为「无任何可辨认证据」的情形",
    "§4 (iii-a) 澄清非放松：是判定路径的澄清而非判断责任的放松":
        "是判定路径的澄清而非判断责任的放松",
    "§4 (iii-a) 原反放宽条款继续适用：原反放宽条款继续全部适用":
        "原反放宽条款继续全部适用",
    "§5 courtyard 中性说明：本渲染含 courtyard 轮廓层（封装占位框线）":
        "本渲染含 courtyard 轮廓层（封装占位框线）",
    "§6 schema：每个 flag 对象**恰含以下 6 键**": "每个 flag 对象**恰含以下 6 键**",
    "§6 无 side 字段：**注意：flag 对象没有 side 字段**":
        "**注意：flag 对象没有 side 字段**",
    "§7 比较器：比较器（`pcbflow/calibration.py`）对 flag 做 fail-closed 校验":
        "比较器（`pcbflow/calibration.py`）对 flag 做 fail-closed 校验",
    # ---- §5A 原文逐字保留（本轮零改动；r15 指引 §5A 关键句）----
    "§5A 原文-首句：本轮 bottom 渲染采用 R14b 配色（与 R14 相同，字节复用同一渲染件）":
        "本轮 bottom 渲染采用 R14b 配色（与 R14 相同，字节复用同一渲染件）",
    "§5A 原文-橙 px：成图实测橙 81672 px（render-witness-r14b.json palette_assertion_summary，两板相同）":
        "成图实测橙 81672 px（render-witness-r14b.json palette_assertion_summary，两板相同）",
    "§5A 原文-绿句：探针板内空隙白 206632 px（final 口径）/ 206052 px（严格口径）":
        "探针板内空隙白 206632 px（final 口径）/ 206052 px（严格口径）",
    "§5A 原文-非图元声明：**绿色区域不是图元**": "**绿色区域不是图元**",
    "§5A 原文-非判据声明：本节为仪器事实（渲染生成语义）":
        "本节为仪器事实（渲染生成语义）",
    "§5A 原文-top 无配色：top 渲染无配色变更（与既往轮次一致）":
        "top 渲染无配色变更（与既往轮次一致）",
    "§5A 原文-白墨计数：162 fill + 4 stroke": "162 fill + 4 stroke",
    "§5A 原文-转录源计数：combined_white_fill_count=162、combined_white_stroke_count=4":
        "combined_white_fill_count=162、combined_white_stroke_count=4",
}


def _fail(msg: str) -> None:
    print(f"[r19-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _replace_counted(text: str, old: str, new: str, expected: int,
                     label: str) -> str:
    """锚串替换：命中数必须恰等于 expected，否则 fail-closed 报错。"""
    n = text.count(old)
    if n != expected:
        _fail(f"锚串命中数不符（{label}）：{old!r} 命中 {n} 次 != 预期 "
              f"{expected} 次（立即停止）")
    return text.replace(old, new)


def _normalize_prefixes(text: str) -> str:
    """机械替换规格化（§6/§7 分段断言用：合法触及冻结段的机械替换——旗
    ID 前缀与示例 reader_id——之后的期望文本）。"""
    return (text
            .replace("R15T-", "R19T-")
            .replace("R15B-", "R19B-")
            .replace("reader-r15", "reader-r19"))


# ---------------------------------------------------------------------------
# 指引生成（确定性机械变换；锚命中数逐一 fail-closed，锚恰 1 次否则 FAIL）
# ---------------------------------------------------------------------------

def build_guidance(base_text: str) -> tuple[str, list[dict]]:
    """由 r15 指引文本生成 r19 指引文本；返回 (r19 文本, edit_list)。"""
    t = base_text
    edits: list[dict] = []

    # ---- 编辑 1（先行）：本轮变更声明节正文整体替换（任务枚举）----
    # 先行原因：声明正文含 r15 自引（r19-prep-record.json / R19T/R19B /
    # 本轮（R19）），整体替换后轮次标识与旗前缀替换的命中数才收敛为期望值。
    for label, expected in (("decl_heading", EXPECTED_HITS["decl_heading"]),
                            ("section1", EXPECTED_HITS["section1"])):
        anchor = DECL_HEADING if label == "decl_heading" else SECTION1_HEADING
        n = t.count(anchor)
        if n != expected:
            _fail(f"锚串命中数不符（{label}）：{anchor!r} 命中 {n} 次 != "
                  f"预期 {expected} 次（立即停止）")
    i = t.index(DECL_HEADING)
    start = i + len(DECL_HEADING)
    j = t.index("\n" + SECTION1_HEADING, start)
    t = t[:start] + "\n\n" + NEW_DECLARATION + "\n" + t[j:]
    edits.append({
        "edit": 1,
        "kind": "本轮变更声明节正文整体替换（任务枚举，逐字）",
        "region": "「## 本轮变更声明（预注册，非事后）」标题行之后至"
                  "「## 1. 角色与任务」之前的正文整体",
        "expected_hits_decl_heading": 1,
        "expected_hits_next_section_anchor": 1,
        "content_sha256": hashing.sha256_text(NEW_DECLARATION),
    })

    # ---- 编辑 2：标题行替换（任务枚举）----
    t = _replace_counted(t, OLD_TITLE, NEW_TITLE,
                         EXPECTED_HITS["title"], "标题行")
    edits.append({
        "edit": 2,
        "kind": "标题行替换（任务枚举）",
        "old": OLD_TITLE,
        "new": NEW_TITLE,
        "expected_hits": EXPECTED_HITS["title"],
    })

    # ---- 编辑 3：声明日期 bullet 同步（轮次标识区；s48/s54/s67 先例）----
    t = _replace_counted(t, OLD_DATE_LINE, NEW_DATE_LINE,
                         EXPECTED_HITS["date_line"], "声明日期 bullet")
    edits.append({
        "edit": 3,
        "kind": "声明日期 bullet 同步（轮次标识区；s48/s54/s67 机械变换"
                "先例；非任务枚举、如实披露）",
        "old": OLD_DATE_LINE,
        "new": NEW_DATE_LINE,
        "expected_hits": EXPECTED_HITS["date_line"],
    })

    # ---- 编辑 4：round_id_constant bullet 同步（轮次标识区）----
    t = _replace_counted(t, OLD_ROUND_ID_BULLET, NEW_ROUND_ID_BULLET,
                         EXPECTED_HITS["round_id_bullet"], "round_id bullet")
    edits.append({
        "edit": 4,
        "kind": "round_id_constant bullet 同步（轮次标识区；s48/s54/s67 "
                "先例）",
        "old": OLD_ROUND_ID_BULLET,
        "new": NEW_ROUND_ID_BULLET,
        "expected_hits": EXPECTED_HITS["round_id_bullet"],
    })

    # ---- 编辑 5：本轮性质行重写（轮次标识区；s48/s54/s67 先例）----
    t = _replace_counted(t, OLD_NATURE_LINE, NEW_NATURE_LINE,
                         EXPECTED_HITS["nature_line"], "本轮性质行")
    edits.append({
        "edit": 5,
        "kind": "本轮性质行重写（轮次标识区；s48/s54/s67 机械变换先例；"
                "非任务枚举、如实披露）",
        "old": OLD_NATURE_LINE,
        "new": NEW_NATURE_LINE,
        "expected_hits": EXPECTED_HITS["nature_line"],
    })

    # ---- 编辑 6：示例 reader-id 同步（轮次标识区；s48/s54/s67 先例）----
    t = _replace_counted(t, "reader-r15", "reader-r19",
                         EXPECTED_HITS["reader_id"], "示例 reader-id")
    edits.append({
        "edit": 6,
        "kind": "示例 reader-id 同步（轮次标识区；s48/s54/s67 机械变换"
                "先例）",
        "old": "reader-r15",
        "new": "reader-r19",
        "expected_hits": EXPECTED_HITS["reader_id"],
        "note": "§6 格式示例 reader_id：reader-r19-top",
    })

    # ---- 编辑 7：示例旗 ID 前缀替换（任务枚举）----
    t = _replace_counted(t, "R15T-", "R19T-",
                         EXPECTED_HITS["prefix_R15T-"], "旗前缀 R15T-")
    t = _replace_counted(t, "R15B-", "R19B-",
                         EXPECTED_HITS["prefix_R15B-"], "旗前缀 R15B-")
    edits.append({
        "edit": 7,
        "kind": "示例旗 ID 前缀替换（任务枚举）",
        "items": [
            {"old": "R15T-", "new": "R19T-",
             "expected_hits": EXPECTED_HITS["prefix_R15T-"]},
            {"old": "R15B-", "new": "R19B-",
             "expected_hits": EXPECTED_HITS["prefix_R15B-"]},
        ],
    })

    # ---- 编辑 8：§4 内 (iii) 接触性判据句之后、既有对照说明块之前增补
    #      (iii-a) 可操作分辨条款 bullet（任务枚举；文本=任务给定逐字）。
    #      插入点锚=三路出口 bullet 行首（恰 1 次）：该锚之前恰为存在性
    #      判断一般判据 bullet（含 (iii) 句与反放宽条款句），之后为三路
    #      出口 bullet 本体与对照说明块——插入即满足「(iii) 句后、对照说
    #      明块前」。----
    t = _replace_counted(t, EXIT_ANCHOR, BULLET_III_A + "\n" + EXIT_ANCHOR,
                         EXPECTED_HITS["exit_anchor"],
                         "§4 三路出口 bullet（(iii-a) 插入点）")
    edits.append({
        "edit": 8,
        "kind": "§4 增补 (iii-a) 可操作分辨条款 bullet（任务枚举；判据侧"
                "唯一变更=§4 内、(iii) 接触性判据句之后、既有对照说明块之"
                "前插入；条款方向=把「无法区分」收窄为「无任何可辨认证据」"
                "的情形，反放宽条款与三路出口逐字保留）",
        "anchor": EXIT_ANCHOR,
        "text_full": BULLET_III_A,
        "content_sha256": hashing.sha256_text(BULLET_III_A),
        "expected_hits": EXPECTED_HITS["exit_anchor"],
    })

    return t, edits


def assert_guidance_invariants(base_text: str, t19: str) -> list[str]:
    """§1/§2/§3/§3A/§5/§5A/§6/§7 分段逐字保留断言 + §4 前段/后段分段断言
    + §5A 原文整体逐字断言 + 关键 substring 断言 + R15 残留零断言 + 新文本
    在位断言 + (iii-a) 位置断言。

    返回通过的断言标签清单（任何失败 fail-closed 报错）。
    """
    passed: list[str] = []

    # ---- 分段逐字保留（§6/§7 段先做旗前缀规格化）----
    for start_anchor, end_anchor in SECTION_PAIRS:
        n = base_text.count(start_anchor)
        if n != 1:
            _fail(f"分段断言起点锚命中 {n} 次 != 1：{start_anchor!r}")
        i = base_text.index(start_anchor)
        if end_anchor is None:
            seg = base_text[i:]
            label = f"分段逐字保留（{start_anchor.split('（')[0]}…至文件尾）"
        else:
            if base_text.count(end_anchor) != 1:
                _fail(f"分段断言终点锚命中 != 1：{end_anchor!r}")
            j = base_text.index(end_anchor)
            seg = base_text[i:j]
            label = (f"分段逐字保留（{start_anchor.split('（')[0]}→"
                     f"{end_anchor.split('（')[0]}）")
        norm = _normalize_prefixes(seg)
        if norm not in t19:
            _fail(f"{label} 失败：r15 段落（旗前缀规格化后）未在 r19 中逐"
                  f"字保留（立即停止）")
        passed.append(label)

    # ---- §4 前段/后段分段逐字断言（本轮冻结区唯一例外=§4 内增补 (iii-a)
    #      一条：前段=§4 标题→三路出口 bullet 行首（含 (i)(ii)(iii) 原文与
    #      反放宽条款），后段=三路出口 bullet 行首→§5 标题（含三路出口、
    #      location_evidence 条与 r6/r8/r13 对照说明块）——两段均须逐字为
    #      r19 子串，中间恰夹 (iii-a) bullet）----
    i4 = base_text.index("## 4. 置信度与弃权")
    i_exit_base = base_text.index(EXIT_ANCHOR)
    i5_base = base_text.index(SECTION5_HEADING)
    seg4a = base_text[i4:i_exit_base]
    seg4b = base_text[i_exit_base:i5_base]
    if seg4a not in t19:
        _fail("§4 前段逐字断言失败：§4 标题→三路出口 bullet 行首段（含"
              "(i)(ii)(iii) 原文与反放宽条款）未在 r19 中逐字保留")
    if seg4b not in t19:
        _fail("§4 后段逐字断言失败：三路出口 bullet 行首→§5 标题段（含三"
              "路出口、location_evidence 条与对照说明块）未在 r19 中逐字保"
              "留")
    if t19.count(BULLET_III_A) != 1:
        _fail("(iii-a) bullet 恰 1 次断言失败")
    joined = seg4a + BULLET_III_A + "\n" + seg4b
    if joined not in t19:
        _fail("§4 结构断言失败：§4 在 r19 中应为 前段+(iii-a)+后段 的连"
              "续拼接（增补唯一、位置唯一）")
    passed.append("§4 前段逐字保留（## 4. 置信度与弃权→三路出口 bullet 行"
                  "首；含 (i)(ii)(iii) 原文与反放宽条款）")
    passed.append("§4 后段逐字保留（三路出口 bullet 行首→## 5. courtyard "
                  "说明；含三路出口与 r6/r8/r13 对照说明块）")
    passed.append("§4 结构断言（前段+(iii-a)+后段连续拼接；(iii-a) bullet "
                  "恰 1 次）")

    # ---- §5A 原文整体逐字断言（r15 §5A 段 = §5A 标题→§6 标题，原样为
    #      r19 子串；本轮零改动）----
    i5a = base_text.index("## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）")
    i6 = base_text.index(SECTION6_HEADING)
    seg5a = base_text[i5a:i6]
    if seg5a not in t19:
        _fail("§5A 原文整体逐字断言失败：r15 指引 §5A 段未在 r19 中逐字保"
              "留（立即停止）")
    passed.append("§5A 原文整体逐字保留（r15 §5A 段 substring-in 断言；本轮"
                  "零改动）")

    # ---- 关键 substring 断言 ----
    for label, needle in REQUIRED_SUBSTRING_VALUES.items():
        if needle not in t19:
            _fail(f"关键 substring 断言失败（{label}）：{needle!r} 未在 r19 "
                  f"指引中逐字保留（立即停止）")
        passed.append(label)
    # 反放宽条款原句恰 1 次（(iii-a) 内为「……」仍不构成……变体措辞，不
    # 重复命中原文全句）
    loosen_needle = "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由"
    n_loosen = t19.count(loosen_needle)
    if n_loosen != 1:
        _fail(f"反放宽条款原句恰 1 次断言失败：命中 {n_loosen} 次 != 1")
    passed.append("§4 反放宽条款原句恰 1 次（原文唯一在位；(iii-a) 内为变体"
                  "措辞不重复命中）")

    # ---- R15 残留零断言（机械替换完备性；声明内 lineage 基座引用
    #      observation-guidance-r15 有意保留恰 1 次、不在零断言之列）----
    for needle in ("R15T", "R15B", "reader-r15", "2026-09-08-r15",
                   "2026-09-08", "# R15 轮", "本轮（R15）",
                   "R15）为指引侧单变量轮", "r15-prep-record.json", "R15"):
        n = t19.count(needle)
        if n != 0:
            _fail(f"残留零断言失败：{needle!r} 在 r19 指引中残留 {n} 次"
                  f"（立即停止）")
    passed.append("R15 残留零断言（R15T/R15B/reader-r15/2026-09-08-r15/"
                  "2026-09-08/# R15 轮/本轮（R15）/R15）为指引侧单变量轮/"
                  "r15-prep-record.json/大写 R15 全部零命中；本轮新文本（性"
                  "质行/声明）不含 R15 字样，故大写 R15 可为全文件零命中"
                  "断言——强于 r18 先例的特定 token 枚举）")
    n = t19.count("observation-guidance-r15")
    if n != 1:
        _fail(f"lineage 基座引用断言失败：observation-guidance-r15 命中 {n} "
              f"次 != 1（应为声明内基座引用恰 1 次）")
    if t19.count("r15") != 1:
        _fail(f"小写 r15 计数断言失败：{t19.count('r15')} 次 != 1（唯一合"
              f"法残留=声明内 lineage 基座自引）")
    passed.append("lineage 基座引用恰 1 次（observation-guidance-r15，声明内"
                  " derivation 基座自引；小写 r15 全文件恰 1 次）")

    # ---- 新文本在位断言 ----
    for needle, label, want in (
            (NEW_TITLE, "r19 标题在位", 1),
            (NEW_DECLARATION, "r19 变更声明在位", 1),
            (NEW_NATURE_LINE, "r19 本轮性质行在位", 1),
            ("`2026-09-09-r19`", "r19 round_id_constant bullet 在位", 1),
            (NEW_DATE_LINE, "r19 声明日期 bullet 在位", 1),
            ("R19T-", "r19 旗前缀 R19T- 在位", 4),
            ("R19B-", "r19 旗前缀 R19B- 在位", 1),
            ("reader-r19", "r19 示例 reader-id 在位", 1),
            ("2026-09-09", "r19 日期常量在位（声明日期+round_id 两处）", 2),
            ("r19-prep-record.json", "r19 预注册件引用在位（声明内）", 1),
            ("(iii-a) 可操作分辨条款（本轮增补）", "(iii-a) 条款头在位", 1),
            ("原反放宽条款继续全部适用", "(iii-a) 反放宽承接句在位", 1),
            ("renders-r14b", "渲染零变更声明在位（性质行+变更声明）", 2),
    ):
        n = t19.count(needle)
        if n != want:
            _fail(f"新文本在位断言失败（{label}）：命中 {n} 次 != {want}")
        passed.append(f"{label}（命中 {n}/{want}）")

    # ---- (iii-a) 位置断言（§4 内：(iii) 句与反放宽条款句之后、三路出口
    #      bullet 之前、既有对照说明块之前；§ 节序不变）----
    i_iii = t19.index("(iii) **接触性判据（判「交叠/接触」类现象前适用）**")
    i_loosen = t19.index("仅因形态不熟悉、不确定其设计含义，不构成判为正常"
                         "设计特征的理由")
    i_iiia = t19.index("(iii-a) 可操作分辨条款（本轮增补）")
    i_exit = t19.index(EXIT_ANCHOR)
    i_contrast = t19.index("（对照说明：r6 §4 的")
    if not (i4 < i_iii < i_loosen < i_iiia < i_exit < i_contrast < i5_base):
        _fail("(iii-a) 位置断言失败：须位于 §4 内、(iii) 句与反放宽条款句"
              "之后、三路出口 bullet 与既有对照说明块之前")
    j5 = t19.index(SECTION5_HEADING)
    j5a = t19.index("## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）")
    j6 = t19.index("## 6. 输出格式")
    j7 = t19.index("## 7. 格式对齐提示")
    if not (i4 < j5 < j5a < j6 < j7):
        _fail("节序断言失败：§4 < §5 < §5A < §6 < §7")
    passed.append("(iii-a) 位置断言（§4 内：(iii) 句 < 反放宽条款句 < "
                  "(iii-a) < 三路出口 bullet < 对照说明块）")
    passed.append("节序断言（§4 < §5 < §5A < §6 < §7；本轮无 §5B，基座"
                  "结构保持）")
    return passed


# ---------------------------------------------------------------------------
# 结构探测（fail-closed）
# ---------------------------------------------------------------------------

def check_renders(witness: dict) -> list[dict]:
    """渲染仪器实测：四 PNG magic+sha256_file 实测 vs witness-r14b 登记
    值（bottom=renders.{applied,prep1}.sha256 两板同；top=top_zero_change_
    copies）——渲染零变更字节复用证明。"""
    rendered = witness.get("renders", {})
    tops = witness.get("top_zero_change_copies", {})
    registered = {
        "applied-bottom": (rendered.get("applied", {}) or {}).get("sha256"),
        "prep1-bottom": (rendered.get("prep1", {}) or {}).get("sha256"),
        "applied-top": (tops.get("applied-top", {}) or {}).get("sha256"),
        "prep1-top": (tops.get("prep1-top", {}) or {}).get("sha256"),
    }
    results = []
    for side in RENDR14B_SIDES:
        sha = registered[side]
        if not isinstance(sha, str) or len(sha) != 64:
            _fail(f"witness-r14b {side} 登记值缺失或非 64 位 sha256：{sha!r}")
        path = RENDR14B_DIR / f"{side}.png"
        if not path.exists():
            _fail(f"PNG 缺失：{path}")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        if measured != sha:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与 witness 登记值不"
                  f"符（字节复用前提破坏）：measured={measured} "
                  f"registered={sha}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "sha256_witness_registered": sha,
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "top_zero_change_copies." + side + ".sha256"),
            "witness_record": "out/v3-tl2/calibration/render-witness-r14b.json",
            "match": True,
        })
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（字节复用口径不符）")
    return results


def probe_axis_plan(plan: dict, plan_sha: str) -> dict:
    """axis-experiment-plan-r17-r20：stage1 R19 定义与判据数值锚。"""
    if plan.get("kind") != "tl2_axis_experiment_plan_development":
        _fail("axis-plan kind 不符")
    if plan.get("declared_date") != DATE_CONSTANT:
        _fail("axis-plan declared_date != 2026-09-09")
    rounds = plan.get("stage1_rounds", {}).get("rounds", [])
    r19 = next((r for r in rounds if r.get("round_id") == "R19"), None)
    if r19 is None or r19.get("axis_id") != "A3_criterion_contact_clarification":
        _fail("axis-plan stage1 R19=A3_criterion_contact_clarification 不符")
    g = r19.get("guidance") or ""
    if "可操作分辨条款" not in g or "反放宽条款逐字保留" not in g:
        _fail(f"axis-plan R19 guidance 缺「可操作分辨条款/反放宽条款逐字保"
              f"留」条款：{g!r}")
    if r19.get("render") != "renders-r14b 四图字节复用（零变更）":
        _fail("axis-plan R19 render 定义不符")
    if "渲染零变更" not in (r19.get("round_nature") or ""):
        _fail("axis-plan R19 round_nature 缺「渲染零变更」")
    bases = plan.get("baselines_registered", {})
    r16b = bases.get("r16_baseline", {})
    if r16b.get("M1_top_aggregate_abstain_rate") != 0.771429:
        _fail(f"axis-plan r16 基线 M1 不符："
              f"{r16b.get('M1_top_aggregate_abstain_rate')}")
    if r16b.get("M3_blackdot_abstain_flags_rubric") != 12:
        _fail(f"axis-plan r16 基线 M3 不符："
              f"{r16b.get('M3_blackdot_abstain_flags_rubric')} != 12")
    if r16b.get("M4_top_per_instance_rate_range") != M4_R16_BASELINE:
        _fail(f"axis-plan r16 基线 M4 不符："
              f"{r16b.get('M4_top_per_instance_rate_range')} != "
              f"{M4_R16_BASELINE}")
    guards = plan.get("guards", {})
    for gid in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                "G3_freeze_discipline"):
        if gid not in guards:
            _fail(f"axis-plan 守门缺失：{gid}")
    quote = (plan.get("user_directive_note", {}) or {}).get("user_quote")
    if quote != "三条轴单独/组合/全组合尝试，选择收益最大的继续":
        _fail(f"axis-plan 用户指令原文不符：{quote!r}")
    # 判据数值自洽：supported contact 阈值 5 = r16 基线 10 的一半；
    # M4 marginal 0.26 与基线 0.261904 相差 0.001904 ≤ 0.005（「附近」）
    if CONTACT_SUPPORTED_THRESHOLD != CONTACT_R16_BASELINE // 2:
        _fail("判据数值自洽断言失败：5 != 10/2")
    if abs(M4_R16_BASELINE - M4_MARGINAL_THRESHOLD) > 0.005:
        _fail("判据数值自洽断言失败：|0.261904-0.26| > 0.005")
    for needle in ("≤ 5", "r16 基线 10 的一半", "≤ 0.20", "0.261904",
                   "≤ 7", "≥ 8", "early_stop", "全 top",
                   "M1（top 全旗聚合弃权率）≤ 0.85"):
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值 {needle}（逐字要求破坏）")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": plan_sha,
        "field": "stage1_rounds.rounds[R19]",
        "round_quote": r19,
    }


def probe_run_r16(run: dict, run_sha: str) -> dict:
    """calibration-run-r16：M1 冻结值与 guard_ok 锚（仅读判据值字段）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r16 hypothesis_test 结构不符")
    m = ht.get("measurement", {})
    if m.get("top_abstain_rate_r16") != 0.771429:
        _fail(f"run-r16 top_abstain_rate_r16 不符："
              f"{m.get('top_abstain_rate_r16')}")
    if m.get("guard_channel", {}).get("guard_ok") is not True:
        _fail("run-r16 guard_ok 不为真（G2 基线证据不符）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r16.json",
        "sha256_measured": run_sha,
        "frozen_values": ("top 27/35=0.771429（r16 零变更基线 M1）；"
                          "guard_ok=True——hypothesis_test 判据文本数值的"
                          "在案锚（GT 匹配与逐旗明细不读取）"),
    }


def probe_typology(typology: dict, typ_sha: str) -> dict:
    """abstain-typology：contact 族 r13–r16 基线（预注册判据基线锚），
    r16=10 全 top 证据（round_view 实测装载）与 grand 38 复核。"""
    bl: dict[str, int] = {}
    for f in typology.get("per_flag", []):
        if f.get("family") == "contact":
            bl[f["round"]] = bl.get(f["round"], 0) + 1
    if bl != CONTACT_ABSTAIN_BASELINE:
        _fail(f"分型件 contact 计数 {bl} != {CONTACT_ABSTAIN_BASELINE}")
    rv = typology.get("matrix", {}).get("round_view", {})
    top16 = (rv.get("r16|top", {}) or {}).get("families", {}).get("contact")
    bot16 = (rv.get("r16|bottom", {}) or {}).get("families", {}).get("contact")
    if top16 != 10 or bot16 != 0:
        _fail(f"分型件 r16 contact 视分布不符：top={top16}、bottom={bot16}"
              f"（预期 10/0=r16 基线 10 全 top）")
    grand = ((typology.get("matrix", {}).get("grand", {}) or {})
             .get("families", {}).get("contact"))
    if grand != GRAND_CONTACT_FLAGS:
        _fail(f"分型件 grand contact={grand} != {GRAND_CONTACT_FLAGS}")
    return {
        "path_rel": "out/v3-tl2/calibration/abstain-typology-r13-r16.json",
        "sha256_measured": typ_sha,
        "contact_abstain_flags_rubric": bl,
        "r16_contact_by_view": {"top": top16, "bottom": bot16},
        "grand_contact_flags": grand,
        "note": "r16 基线 10 全 top（round_view 实测装载）——预注册判据文"
                "本「r16=10 全 top」的在案锚",
    }


def probe_dev18(dev18: dict, dev18_sha: str) -> dict:
    """round18-dev-record：next_iteration_targets[0] R19=轴3 指令链锚与
    r18 参照计数（黑点 13/top 弃权分型 接触性 8+存在性 12）。"""
    if dev18.get("kind") != "tl2_calibration_round18_dev_record":
        _fail("round18-dev-record kind 不符")
    if dev18.get("round_id") != "2026-09-09-r18":
        _fail("round18-dev-record round_id 不符")
    if dev18.get("declared_date") != DATE_CONSTANT:
        _fail("round18-dev-record declared_date != 2026-09-09")
    targets = dev18.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round18-dev-record next_iteration_targets 缺失")
    nt0 = targets[0]
    for needle in ("R19=轴3", "可操作分辨条款", "反放宽条款逐字保留",
                   "r14b 字节复用"):
        if needle not in nt0:
            _fail(f"round18-dev-record next_iteration_targets[0] 缺关键语："
                  f"{needle!r}")
    mech = (dev18.get("hypothesis_test_i", {}).get("mechanism_observation", {}))
    ledger = (mech.get("experiment_comparison_ledger", {})
              .get("direction_vs_r16", {}).get("M3"))
    if not isinstance(ledger, str) or "12→13" not in ledger:
        _fail(f"round18-dev-record M3 方向锚不符：{ledger!r}（预期含 12→13）")
    tat = mech.get("top_abstain_typology", {})
    counts: dict[str, int] = {}
    for row in tat.get("rows", []):
        counts[row.get("type")] = counts.get(row.get("type"), 0) + 1
    if counts != {"existence": 12, "contact": 8}:
        _fail(f"round18-dev-record top 弃权分型行计数不符：{counts}"
              f"（预期 contact=8/existence=12）")
    return {
        "path_rel": "out/v3-tl2/calibration/round18-dev-record.json",
        "sha256_measured": dev18_sha,
        "field": "next_iteration_targets[0]",
        "r18_reference_counts": {
            "blackdot_abstain_flags_rubric": 13,
            "top_abstain_typology_contact": counts.get("contact"),
            "top_abstain_typology_existence": counts.get("existence"),
        },
    }


def probe_blackdot_context(probe: dict, probe_sha: str) -> dict:
    """blackdot-probe-r18：仅哈希+kind 复核（r18 §5B 上下文链锚；本轮零
    内容转录——r19 指引不含 §5B，基座=r15）。"""
    if probe.get("kind") != "tl2_blackdot_probe_r18":
        _fail("blackdot-probe-r18 kind 不符")
    return {
        "path_rel": "out/v3-tl2/calibration/blackdot-probe-r18.json",
        "sha256": probe_sha,
        "role": "r18 §5B 上下文链锚（仅哈希+kind 复核；r19 基座=r15、本轮"
                "零内容转录）",
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance15_sha: str, guidance19_sha: str,
                 guidance15_bytes: int, guidance19_bytes: int,
                 r15_record_sha: str, r18_record_sha: str,
                 axis_probe: dict, run_probe: dict, typ_probe: dict,
                 dev18_probe: dict, probe18_rec: dict, witness_sha: str,
                 protocol_sha: str, png_checks: list[dict],
                 edit_list: list[dict], section_asserts: list[str]) -> dict:
    """构建 r19-prep-record 内容（纯函数：同入参必得同 dict）。"""
    axis_rel = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r19_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r19",
        "round_nature": (
            "轴3 判据侧单变量轮（§4(iii) 可操作分辨条款；渲染零变更；"
            "axis-experiment-plan-r17-r20 stage1 之一，第十九轮）：判读指"
            "引由 observation-guidance-r15.md 机械变换生成 observation-"
            "guidance-r19.md（本轮唯一判读依据；判据侧变更=§4 内 (iii) 接"
            "触性判据句之后、既有对照说明块之前增补 (iii-a) 可操作分辨条款"
            "（把「无法区分」操作化为证据可见性三支判据——见间隙证据→按视"
            "觉贴近继续判定；见侵入证据→按接触/交叠处理；两者均无→方按 "
            "(iii) 原文弃权）+轮次标识机械同步，见 guidance_reuse.edit_"
            "list）；本实验线首次触碰判据节——反放宽为最高约束：条款只收"
            "窄「真歧义弃权」的适用面（把有证据可判的情形引导到负责任判"
            "定），不降低判断责任标准；反放宽条款与三路出口逐字保留（"
            "fail-closed 断言）、§4 其余全部文本（总原则、两条显式判据、量"
            "化判据 (i)(ii)(iii) 原文、confidence 定义、对照说明块）与 §1/"
            "§2/§3/§3A/§5/§5A/§6/§7 逐字承 r15（分段+substring 双重断言复"
            "核）；渲染零变更=renders-r14b 四图字节复用（四 PNG sha256_"
            "file 实测与 render-witness-r14b.json 登记值 fail-closed 比对一"
            "致，即 r14/r15/r16/r18 轮盲读所用同一批文件，见 instrument_"
            "change）；GT/阈值/协议零变更（v1.1+v1.2 维持）；执行 axis-"
            "experiment-plan-r17-r20（b6ec6467 冻结件）stage1 R19=轴3"
            "（A3_criterion_contact_clarification，其 guidance 原文=「r15 "
            "指引+§4(iii) 接触性判据补可操作分辨条款（方向=判定一致性，反"
            "放宽条款逐字保留）」，实测链见 changed_variables[0]."
            "preregistration_ref）；round18-dev-record next_iteration_"
            "targets[0] 同口径指令；用户 2026-09-09「三条轴单独/组合/全组"
            "合尝试，选择收益最大的继续」（见 user_directive_note）；r15 "
            "指引已在盘冻结、本轮只读零写入；盲读由编排侧在本记录之后以 "
            "12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的"
            "继续」=授权执行 axis-experiment-plan-r17-r20（b6ec6467 冻结"
            "件，先于 R17–R21 任何实验轮盲读冻结以防事后择优）stage1 "
            "R19=轴3 判据侧可操作分辨条款轮（A3_criterion_contact_"
            "clarification）；本记录=该轮 prep-record 预注册（先于任何盲读"
            "冻结）；round18-dev-record next_iteration_targets[0] 同口径指"
            "令（guidance-r19=r15 基座+§4(iii) 可操作分辨条款[方向=判定一"
            "致性；反放宽条款逐字保留]；渲染=r14b 字节复用——判据侧单变"
            "量轮，实测链见 changed_variables[0].preregistration_ref）；比"
            "较与组合决策以冻结件 comparison_rule/combination_decision_"
            "rule 为准；既往轮次字母不回写（r8–r18 维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14/r15/r16/r18 完全相同（renders-r14b 字节复"
                    "用，四 PNG 实测=witness-r14b 登记值），变化仅在指引文"
                    "本（且为判据侧单点增补）",
            "renders": png_checks,
            "witness": "render-witness-r14b.json（b63771f9，fail-closed 复核）",
            "declaration": (
                "axis-plan stage1 R19 render 原文=「renders-r14b 四图字节复"
                "用（零变更）」；本轮 prep 零重渲染、零 out/ 既有文件改动（四 "
                "PNG sha256_file 实测=witness-r14b 登记值；bottom 两板逐字"
                "节同 d7284259；top 无配色 298bc620/b2f84524）"),
        },
        "no_instrument_change": True,
        "guidance_reuse": {
            "base": "observation-guidance-r15.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r15.md"),
            "base_sha256": guidance15_sha,
            "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
            "mode": "mechanical_transform_derive",
            "derived": "observation-guidance-r19.md",
            "derived_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r19.md"),
            "derived_sha256": guidance19_sha,
            "byte_size": {"base": guidance15_bytes,
                          "derived": guidance19_bytes,
                          "delta": guidance19_bytes - guidance15_bytes},
            "edit_list": edit_list,
            "verbatim_frozen_sections": (
                "§2 类别枚举、§3 位置口径、§3A 类别判据示例（含示例 c 与末"
                "尾对照说明）、§4 置信度与弃权其余全部文本（含量化判据 "
                "(i)(ii)(iii) 原文、(iii) 接触性判据原句、三路出口、反放宽"
                "条款、confidence 定义、r6/r8/r9/r12/r13 对照说明块——本轮"
                "冻结区唯一例外=§4 内增补 (iii-a) 一条，前段/后段分别逐字"
                "断言）、§5 courtyard 说明、§5A 渲染配色仪器注记（r15 原文"
                "整体逐字保留、本轮零改动）、§6 输出格式（旗 ID 展示前缀机"
                "械替换除外）、§7 格式对齐提示、§1 角色与任务——分段逐字"
                "保留断言（r15 段落 substring-in 断言）+关键 substring 断言"
                "双重复核，见 verification.section_assertions_passed"),
            "lineage_note": (
                "轮次标识区同步（标题行/声明日期 bullet/round_id_constant "
                "bullet/本轮性质行/示例 reader_id/示例旗 ID 前缀）沿 "
                "s48_calibration_r13_prep.py→s54_calibration_r15_prep.py→"
                "s63_calibration_r17_prep.py→s67_calibration_r18_prep.py"
                "（指引侧/仪器轮机械变换）先例；任务枚举编辑全部逐字执行，"
                "非任务枚举的轮次标识同步项（edit 3/5/6）在 edit_list 中如"
                "实登记；本轮新文本（性质行/变更声明）不含 R15 字样、渲染"
                "件表述沿 r15 原文「复用 R14 冻结渲染件 renders-r14b」口径"
                "——故「R15 残留零」可做强断言（大写 R15 全文件零命中+小写"
                " r15 恰 1 次=声明内 lineage 基座自引），强于 r18 先例的特"
                "定 token 枚举断言；§1 与头部 bullet 区不在逐字冻结清单"
                "（冻结区=§2–§7，本轮唯一例外=§4 内增补 (iii-a) 一条）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
                "r15_prep_record_schema_template": {
                    "path_rel": "out/v3-tl2/calibration/r15-prep-record.json",
                    "sha256": r15_record_sha,
                },
                "r18_prep_record_mirror_source": {
                    "path_rel": "out/v3-tl2/calibration/r18-prep-record.json",
                    "sha256": r18_record_sha,
                    "cross_check": "24 键顶层结构逐键镜像（同 r17/r18 先例）",
                },
                "render_witness_r14b_byte_reuse": {
                    "path_rel": "out/v3-tl2/calibration/render-witness-"
                                "r14b.json",
                    "sha256": witness_sha,
                },
                "axis_experiment_plan_frozen": {
                    "path_rel": axis_rel,
                    "sha256": axis_probe["sha256_measured"],
                },
                "round18_dev_record_chain": {
                    "path_rel": ("out/v3-tl2/calibration/round18-dev-record"
                                 ".json"),
                    "sha256_measured": dev18_probe["sha256_measured"],
                    "field": "next_iteration_targets[0]",
                    "r18_reference_counts":
                        dev18_probe["r18_reference_counts"],
                },
                "run_r16_baseline_anchor": run_probe,
                "typology_contact_baseline": typ_probe,
                "blackdot_probe_r18_context": probe18_rec,
                "evaluation_protocol_v1_preserved": {
                    "path_rel": (
                        "out/v3-tl2/calibration/evaluation-protocol-v1.md"),
                    "sha256": protocol_sha,
                },
            },
            "verification": {
                "section_assertions_passed": section_asserts,
            },
        },
        "changed_variables": [
            {
                "id": "guidance-s4-iii-a-contact-operational-clause",
                "axis": "guidance",
                "axis_id": "A3_criterion_contact_clarification",
                "instrument_change": False,
                "target": ("observation-guidance-r19.md §4 (iii-a)（新增 "
                           "bullet：§4 内、(iii) 接触性判据句之后、既有对照"
                           "说明块之前；全文逐字见 guidance_reuse.edit_list"
                           "[7].text_full）"),
                "description": (
                    "判读指引 §4 增补 (iii-a) 可操作分辨条款（判据侧单点增"
                    "补；本实验线首次触碰判据节）：在 (iii) 接触性判据原句"
                    "之后、既有对照说明块之前插入 bullet，把「无法区分真接"
                    "触与视觉贴近」操作化为证据可见性三支判据——(1) 间隙支"
                    "：能辨认连续间隙带（背景或底层颜色贯通）→按「视觉贴"
                    "近」处理并继续按 (i)(ii) 与三路出口判定、不得弃权；"
                    "(2) 侵入支：边缘直接相连或明显侵入→按「接触/交叠」处"
                    "理并照常输出旗标；(3) 残余弃权支：既无可辨认间隙带亦"
                    "无可辨认侵入证据→方属「无法区分」、按 (iii) 原文弃权。"
                    "条款只收窄「真歧义弃权」的适用面（把有证据可判的情形"
                    "引导到负责任判定），是判定路径的澄清而非判断责任的放"
                    "松；两支新判定路径均以「可辨认证据」为责任条件；「仅"
                    "因形态不熟悉、不确定其设计含义」仍不构成判为正常设计"
                    "特征的理由（原反放宽条款继续全部适用）；§4 其余全部文"
                    "本（总原则、两条显式判据、量化判据 (i)(ii)(iii) 原文、"
                    "三路出口、confidence 定义、对照说明块）逐字不变（分段"
                    "+substring 双重断言复核）"),
                "attribution_channel": (
                    "contact 族弃权旗数（全视，分型件 rubric 口径；r16 基线 "
                    "10、r13–r16 序列 8/15/5/10 在案、r16=10 全 top）主判据"
                    "=hypothesis_test.adjudication 三支（supported contact "
                    "≤5 且 M4 ≤0.20 且 G1/G2 维持且 M1 ≤0.85；marginal 未"
                    "达 supported 且 contact ≤7 或 M4 ≤0.26 且 G1/G2 维持；"
                    "reject contact ≥8 且 M4 >0.26、或 G1/G2 任一破坏→"
                    "early_stop 出局）；判读须同时看 M4（top 逐实例弃权率极"
                    "差，r16 基线 0.261904）如实登记，不得仅以 M1 排序否定"
                    "轴3（round18-dev-record next_iteration_targets[0] 已接"
                    "受该操作化取舍）"),
                "preregistration_ref": {
                    "path_rel": axis_rel,
                    "sha256_measured": axis_probe["sha256_measured"],
                    "field": axis_probe["field"],
                    "round_quote": axis_probe["round_quote"],
                },
            },
            {
                "id": "round-identity-sync",
                "axis": "guidance",
                "instrument_change": False,
                "target": "observation-guidance-r19.md 头部与 §6 示例",
                "description": (
                    "标题行 R15→R19、声明日期 bullet 2026-09-08→2026-09-09、"
                    "round_id_constant bullet 2026-09-08-r15→2026-09-09-r19、"
                    "本轮性质行按轴3 判据侧单变量轮口径重写、示例 reader_id "
                    "reader-r15→reader-r19、示例旗 ID 前缀 R15T-（4 处）/"
                    "R15B-（1 处）→R19T-/R19B-——s48/s54/s63/s67 机械变换"
                    "先例轮次标识区同步，如实登记"),
            },
        ],
        "manipulated_factor": (
            "唯一操纵因素=判读指引 §4 增补 (iii-a) 可操作分辨条款（判据侧"
            "单点增补，per axis-plan stage1 R19=A3_criterion_contact_"
            "clarification「r15 指引+§4(iii) 接触性判据补可操作分辨条款（方"
            "向=判定一致性，反放宽条款逐字保留）」）；渲染（四图字节复用）/"
            "GT/阈值/协议与 §4 其余判据文本零变更"),
        "unchanged_components": [
            {
                "byte_reuse": True,
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "note": "开工时 sha256_file 实测四 PNG 并与 render-witness-"
                        "r14b.json 登记值逐字比对（bottom=renders.applied/"
                        "prep1.sha256；top=top_zero_change_copies.sha256）"
                        "——四图即 r14/r15/r16/r18 轮盲读所用同一批文件；本"
                        "轮零重渲染、零仪器变更",
                "pngs": png_checks,
                "witness": "render-witness-r14b.json（b63771f9，fail-closed "
                           "复核）",
            },
            "判读指引 §2 类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序"
            "与圆括号中性释义零改动；r15 指引 §2 原文，分段+substring 断"
            "言复核）",
            "§3 邻域框收窄判据与坐标口径（r15 指引 §3 原文逐字）",
            "§3A 类别判据示例：全部逐字承 r15 指引（六类全部示例含示例 c"
            "「整段规则周期」判据；§3A 末尾对照说明原位保留）",
            "§4 其余全部文本：总原则、两条显式判据、量化版存在性判断一般"
            "判据 (i)(ii)(iii) 原文、(iii) 接触性判据原句、三路出口、"
            "confidence 定义、对照说明（r6/r8/r9/r12/r13 增补块）——逐字"
            "承 r15 指引（本轮唯一例外=§4 内增补 (iii-a) 一条；§4 前段/"
            "后段分别分段逐字断言+substring 断言复核）；反放宽条款「仅因"
            "形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」"
            "逐字保留（原句恰 1 次断言）",
            "§5 courtyard 说明（r15 指引原文逐字）",
            "§5A 渲染配色仪器注记：r15 指引 §5A 原文整体逐字保留（本轮零"
            "改动——含首句「字节复用同一渲染件」表述，其对本轮仍为真：四 "
            "PNG 实测=witness 登记值；分段+substring 断言复核）",
            "§6 输出格式：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r15 指引原文；仅旗 ID 展示前缀 R15T-/R15B-→R19T-/"
            "R19B- 机械替换，随指引落盘固化、无需派发层覆盖）",
            "§7 格式对齐提示（r15 指引原文逐字）",
            "§1 角色与任务与盲读纪律（r15 指引原文逐字；不在冻结清单亦零"
            "改动，分段断言复核）",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r18 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "度量设计五条与聚合口径：沿 r16-prep-record measurement_design"
            ".items 同一口径（仅轮次标识、reader 前缀与渲染件名按 r19 改"
            "写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16/"
            "R18 完全相同文件：白墨图元→橙 (255,165,0)、板内空隙白→绿 "
            "(0,128,0)、其余层 kicad 原配色不变；四 PNG sha256_file 实测="
            "witness-r14b 登记值 fail-closed 比对一致）——渲染零变更；本"
            "轮唯一变更=判据侧 §4(iii-a) 可操作分辨条款（非仪器注记、非任"
            "何「应判正常/无需报告」的指示；不降低任何责任门槛——两支新"
            "判定路径均以「可辨认证据」为责任条件、残余支仍按 (iii) 原文"
            "弃权；bottom 视现象的旗标判定同样按 §2/§3A/§4 独立执行，条款"
            "按图像可见证据操作、对 top/bottom 视在图像空间同口径适用）；"
            "bottom 视判读口径沿用 r4 指引原文不改（top/bottom 判读口径在"
            "图像空间完全一致、不做镜像换算）；bottom 零旗标分母=0 时弃权"
            "率按 cal._ratio 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R19 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r16-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R19T/R19B；"
                "图像=renders-r14b 四图（字节复用）；聚合口径与 "
                "s55_calibration_r15_compare.py 同一比较脚本血统；代表配"
                "置/逐实例/双口径分列）"),
            "items": [
                {
                    "item": 1,
                    "name": "主记录单位=实例",
                    "text": (
                        "每实例给出其视角两板合计的 flag_count、abstain_"
                        "count、abstain_rate（分母=该实例该视角全部旗标，"
                        "跨两板合计）、非弃权旗标清单、逐旗与 GT 的 "
                        "containment/area_ratio 匹配明细（比较器 fail-closed"
                        " 校验照旧）"),
                },
                {
                    "item": 2,
                    "name": "视角层聚合",
                    "text": (
                        "每视角 3 实例的 flag_count/abstain_rate/matches 各"
                        "给中位数+最小值+最大值，如实三分列、不取整"),
                },
                {
                    "item": 3,
                    "name": "GT 匹配聚合双口径",
                    "text": (
                        "union（≥1 实例命中即计）与 agreement（≥2/3 实例命"
                        "中才计）两口径并列报告，均如实、不二选一；逐 GT 条"
                        "目给出 matched_by_count（0..3）"),
                },
                {
                    "item": 4,
                    "name": "联合门评价（APR-0011）",
                    "text": (
                        "代表配置=每视角取 flag_count 中位数实例组成代表配"
                        "置，计算一轮 joint 结果；同时如实给出 per-metric 实"
                        "例间范围（min..max）；代表配置 joint 结果、"
                        "per-metric 实例间范围、逐实例原始记录（item 1）三"
                        "者并列如实呈现，不合并、不挑优；APR-0011 阈值零改"
                        "动"),
                },
                {
                    "item": 5,
                    "name": "bottom 零旗标处理",
                    "text": (
                        "沿用库侧 cal._ratio 先例（pcbflow/calibration.py "
                        "_ratio：零分母→None）——实例/视角层遇零旗标分母"
                        "时弃权率=None+文字说明，不编造数值（r10 run-record "
                        "bottom=0/0→None 同口径在案）"),
                },
            ],
        },
        "hypothesis_test": HYPOTHESIS_TEST,
        "attribution_plan": {
            "declaration": (
                "本轮恰一个操纵因子（判读指引 §4 增补 (iii-a) 可操作分辨条"
                "款；渲染零变更字节复用）、检验恰一个假设（axis-experiment-"
                "plan-r17-r20 stage1 R19=轴3；hypothesis_id=axis-plan-r19-"
                "criterion-operational）；归因目的=contact 族弃权与判定分歧"
                "主因是否为「§4(iii)『无法区分』无差别适用」的判据侧首验；"
                "跨轮对比（vs r16 基线 contact=10、M4=0.261904）按冻结件 "
                "comparison_rule（显著收益参照；跨轮实例群漂移混杂显式容"
                "忍、参照 r15→r16 纯重抽变动 0.09064 在案量级）；字母/机制"
                "观察/度量教训三分记账（adjudication.mechanism_observation_"
                "separate 与 metric_lesson_separate 单列，不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "guidance-s4-iii-a-contact-operational-clause（判据侧唯"
                    "一操纵；非渲染/GT/阈值/协议变更）"),
                "metric": (
                    "contact 族弃权旗数（全视，分型件 rubric 口径；r16 基线 "
                    "10、r13–r16 序列 8/15/5/10 在案）+M4（top 逐实例弃权率"
                    "极差，r16 基线 0.261904）联合判据见 hypothesis_test."
                    "adjudication：supported contact ≤5 且 M4 ≤0.20 且 G1/"
                    "G2 维持且 M1 ≤0.85；marginal 未达 supported 且（contact "
                    "≤7 或 M4 ≤0.26）且 G1/G2 维持；reject contact ≥8 且 "
                    "M4 >0.26、或 G1/G2 任一破坏（early_stop 出局）"),
                "supported": (
                    "contact ≤5 且 M4 ≤0.20 且 G1/G2 维持且 M1 ≤0.85 → 可操"
                    "作分辨条款使 contact 族负责任判定成立（轴3 supported）"),
                "marginal": (
                    "未达 supported 且（contact ≤7 或 M4 ≤0.26）且 G1/G2 维"
                    "持 → 记录为部分收益"),
                "reject": (
                    "contact ≥8 且 M4 >0.26、或 G1/G2 任一破坏 → 按退出规则"
                    "出局（early_stop）"),
            },
            "guard_channel": {
                "metric": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15/r16 "
                    "在案 0/0/0；G1 为本轮 (iii-a) 间隙支「不得弃权」方向的"
                    "反向风险守门——条款若被误用为「少弃权」压力，G1/守门与"
                    "reject 支须如实记录）；G2=guard_ok=True 维持（top 视非"
                    "弃权旗标 frame_box_pct 几何门，面积比出局条目按 "
                    "guard_channel 如实登记）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r19 指引 §2–§7 除 (iii-a) 增补外"
                    "逐字承 r15，分段断言复核），非弃权框仍须满足；任一守门"
                    "破坏→按 axis-plan early_stop_rule 出局（字母照实+出局"
                    "声明）"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角"
                "层三分列聚合+GT 匹配双口径+联合门代表配置/范围并列；"
                "APR-0011 阈值零改动）；bottom GT 无源=bottom 旗标与 GT 匹"
                "配应为空（结构性在案，不影响收敛计数口径）；字母裁决/机"
                "制观察/度量教训三分记账、互不凌驾；归因分组逻辑由编排侧"
                "在 close 包执行；指引内零 GT、零轮次结果数字（基线数字仅"
                "入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止"
                    "（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "本轮判据侧变更方向=收窄而非放松：(iii-a) 只把「无法区分」收窄"
            "为「无任何可辨认证据」的情形——把有证据可判的情形引导到负责任"
            "判定；两支新判定路径均以「可辨认证据」为责任条件（间隙支仍须"
            "按 (i)(ii) 与三路出口判定、不得以条款为由直接放行；侵入支照常"
            "输出旗标并承担同等判断责任）；残余支仍按 (iii) 原文弃权——真"
            "歧义弃权通道完整保留、不降低判断责任标准（责任标准一字未降）；"
            "反放宽条款「仅因"
            "形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」"
            "与三路出口显式化在 r19 指引 §4 内逐字保留（fail-closed sub-"
            "string 断言+原句恰 1 次断言），(iii-a) 文本内含原反放宽条款继"
            "续全部适用的承接句；§4 量化判据 (i)(ii) 原文、总原则、"
            "confidence 定义、对照说明块逐字不动（分段断言）；存在性判断仍"
            "按 §4 (i)(ii)(iii) 全部要件执行、(iii-a) 仅为 (iii) 的判定路径"
            "澄清；contact ≤5/M4 ≤0.20/M1 ≤0.85 等本轮判据只用于轴3 收益方"
            "向归因（axis-experiment-plan-r17-r20 冻结比较规则），不触碰 "
            "APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与任何阈值常量（CONTAINMENT_MIN/"
            "AREA_RATIO_MAX，只作口径引用）——门照常独立计算；不构成任何"
            "阈值反向放宽"),
        "pre_round_review": {
            "status": "satisfied_by_plan",
            "basis": (
                "axis-experiment-plan-r17-r20 冻结（b6ec6467，stage1 "
                "R19=A3_criterion_contact_clarification 定义在案：guidance="
                "「r15 指引+§4(iii) 接触性判据补可操作分辨条款（方向=判定一"
                "致性，反放宽条款逐字保留）」、render=「renders-r14b 四图字"
                "节复用（零变更）」、round_nature=指引侧单变量轮渲染零变"
                "更）+abstain-typology-r13-r16 分型件 contact 族证据"
                "（6dadac8d；contact 族 r13–r16=8/15/5/10、r16=10 全 top"
                "[round_view r16|top=10、r16|bottom=0 实测装载复核]、四轮 "
                "38 旗 grand 复核；q3 事实基础 (a)(c) 在案=contact 族集中"
                "于 top 视四轮持续存在+三族 97.7% 弃权理由均为 §4 存在性/"
                "接触性判据下的「不可负责任确认」）+round18-dev-record "
                "next_iteration_targets[0]「按冻结计划推进 R19=轴3」指令在"
                "案（a0c1f97c）；判据侧首变的反放宽约束（条款只收窄「无法"
                "区分」适用面、不降低判断责任标准、反放宽条款与三路出口逐"
                "字保留）由本包 fail-closed 断言执行（见 no_loosening_note "
                "与 verification.section_assertions_passed）"),
        },
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "version": "v1.1+v1.2 维持",
            "changes": [],
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口"
                            "径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视"
                "角层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径"
                "并列、联合门代表配置+实例间范围并列（measurement_design "
                "五条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派"
                "发指令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/"
                "放大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查"
                "看原图（同一原图可重复查看）」——仪器行为钉住；属派发层，"
                "读者上下文=指引+单张 PNG+派发指令（含规约条款），零 GT；"
                "不影响判读语义——分类判据文本除 (iii-a) 预注册增补外零变"
                "更，仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11–r18 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-"
                "r19.md，含 §4(iii-a) 可操作分辨条款——指引本体组成部分，"
                "非派发层补充）+单张 PNG（renders-r14b 四图）+派发命名指令"
                "（含 v1.2 工具行为规约硬性条款：纯 Read 内联判读、禁止任"
                "何程序化图像处理），零 GT、零历史判读件、零诊断/探针内容"
                "（diag 件与 dev/typology/probe 件为主审/编排侧核验件、非 "
                "reader 上下文）；两波次串行保序（同一实例先 applied 后 "
                "prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r19-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R19T/R19B（r19 指引 §6 已机械替换落盘 R19T-/R19B-——本轮"
                "指引本体即为 r19 前缀，无需派发层覆盖）；实例间编号独立，"
                "同实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic，零内容判读、零像素读取）、ground-truth-*、reader-raw-*、"
            "derivation-log-*、任何 compare/评估产物、diag-r13-review 与 "
            "diag-r17-render 内容（零读取）；本脚本只读输入="
            "observation-guidance-r15.md（r19 指引的唯一变换基座；d5babc93 "
            "锚 fail-closed，零写入）、r15-prep-record.json（链锚=4c6cd919 "
            "先验证；schema 血统）、r18-prep-record.json（链锚=3fc054c4；"
            "24 键结构镜像来源+§5B 轮先例）、axis-experiment-plan-r17-r20."
            "json（b6ec6467 锚；stage1 R19=A3 定义、r16 基线 M1/M3/M4、守"
            "门、用户指令原文）、round18-dev-record.json（a0c1f97c 锚；仅"
            "读取 next_iteration_targets[0] 指令、kind/round_id 与 top 弃"
            "权分型 r18 参照计数——黑点 13/接触性 8/存在性其他 12）、"
            "calibration-run-r16.json（2c1f8265 锚；仅读取 hypothesis_test "
            "顶层判据冻结值字段——M1=0.771429、guard_ok=True；其 GT 匹配"
            "与逐旗明细内容不读取、不入记录）、abstain-typology-r13-r16."
            "json（6dadac8d 锚；仅读取 per_flag/matrix 家族计数做 contact "
            "族基线锚——r13–r16=8/15/5/10、r16|top=10、r16|bottom=0、"
            "grand 38）、blackdot-probe-r18.json（a49441ac 锚；仅哈希+kind "
            "复核——r18 §5B 上下文链锚，本轮零内容转录）、render-witness-"
            "r14b.json（b63771f9 锚；四 PNG 见证登记值+字节复用证明）、"
            "evaluation-protocol-v1.md（仅在盘+哈希复核，锚=22dc7337）；"
            "renders-r14b 四 PNG 仅哈希+magic（渲染零变更以 witness 登记"
            "哈希比对为准）；本轮恰三个新建文件=scripts/s70_calibration_"
            "r19_prep.py（生成器本体）、observation-guidance-r19.md 与 "
            "r19-prep-record.json（本轮仅有的两个 out/ 新建文件；本轮无探"
            "针/诊断脚本）；reader 派发（后续编排侧执行）上下文=observation-"
            "guidance-r19.md+单张 PNG（renders-r14b）+派发指令（R19T/R19B "
            "前缀、reader-r19-{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬"
            "性条款），零 GT、零历史判读件、零诊断/探针内容、零指引之外的"
            "解释；视觉判读禁止由编排/收口包兼任；跨实例/跨视角禁止交流"
            "（12 次盲读相互独立、不得交换判读信息——独立性是多实例协议的"
            "前提，亦为轴3 收益裁决有效性的前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R15, R15_PREP_RECORD, R18_PREP_RECORD,
                 BLACKDOT_PROBE, WITNESS_R14B, AXIS_PLAN, DEV_RECORD_R18,
                 RUN_R16, TYPOLOGY, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件（GUIDANCE_R19/RECORD）不做前置硬拒绝：落盘阶段防覆写守卫
    # 按红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→
    # 幂等通过（零覆写）。（首轮创建前置=两 out/ 目标不存在，已由编排侧
    # 确认。）

    # ---- 冻结锚验证（fail-closed）----
    r15_record_sha = _sha(R15_PREP_RECORD)
    r18_record_sha = _sha(R18_PREP_RECORD)
    probe18_sha = _sha(BLACKDOT_PROBE)
    witness_sha = _sha(WITNESS_R14B)
    axis_sha = _sha(AXIS_PLAN)
    dev18_sha = _sha(DEV_RECORD_R18)
    run_r16_sha = _sha(RUN_R16)
    typ_sha = _sha(TYPOLOGY)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    for sha, prefix, label in (
            (r15_record_sha, R15_PREP_RECORD_SHA_PREFIX, "r15-prep-record"),
            (r18_record_sha, R18_PREP_RECORD_SHA_PREFIX, "r18-prep-record"),
            (probe18_sha, BLACKDOT_PROBE_SHA_PREFIX, "blackdot-probe-r18"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (axis_sha, AXIS_PLAN_SHA_PREFIX, "axis-experiment-plan"),
            (dev18_sha, DEV_RECORD_R18_SHA_PREFIX, "round18-dev-record"),
            (run_r16_sha, RUN_R16_SHA_PREFIX, "calibration-run-r16"),
            (typ_sha, TYPOLOGY_SHA_PREFIX, "abstain-typology-r13-r16"),
            (protocol_sha, EVAL_PROTOCOL_V1_SHA_PREFIX,
             "evaluation-protocol-v1")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，立即"
                  f"停止）")

    r15_record = json.loads(R15_PREP_RECORD.read_text(encoding="utf-8"))
    r18_record = json.loads(R18_PREP_RECORD.read_text(encoding="utf-8"))
    for rec, label, rid, kind in (
            (r15_record, "r15-prep-record", "2026-09-08-r15",
             "tl2_calibration_r15_prep_record"),
            (r18_record, "r18-prep-record", "2026-09-09-r18",
             "tl2_calibration_r18_prep_record")):
        if rec.get("schema_version") != "3.0":
            _fail(f"{label} schema_version != 3.0（结构漂移）")
        if rec.get("kind") != kind:
            _fail(f"{label} kind 不符（结构漂移）")
        if rec.get("round_id_constant") != rid:
            _fail(f"{label} round_id_constant != {rid}（结构漂移）")

    # ---- r15 指引零字节复核（本轮唯一变换基座；只读）----
    guidance15_sha = _sha(GUIDANCE_R15)
    if not guidance15_sha.startswith(GUIDANCE_R15_SHA_PREFIX):
        _fail(f"r15 指引 sha 前 8={guidance15_sha[:8]} != 预期 "
              f"{GUIDANCE_R15_SHA_PREFIX}（变换基座疑被改动，立即停止）")
    base_text = GUIDANCE_R15.read_text(encoding="utf-8")
    if hashing.sha256_text(base_text) != guidance15_sha:
        _fail("r15 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")

    # ---- 结构探测（判据冻结值锚与指令链锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    run_r16 = json.loads(RUN_R16.read_text(encoding="utf-8"))
    typology = json.loads(TYPOLOGY.read_text(encoding="utf-8"))
    dev18 = json.loads(DEV_RECORD_R18.read_text(encoding="utf-8"))
    probe18 = json.loads(BLACKDOT_PROBE.read_text(encoding="utf-8"))
    png_checks = check_renders(witness)
    axis_probe = probe_axis_plan(axis_plan, axis_sha)
    run_probe = probe_run_r16(run_r16, run_r16_sha)
    typ_probe = probe_typology(typology, typ_sha)
    dev18_probe = probe_dev18(dev18, dev18_sha)
    probe18_rec = probe_blackdot_context(probe18, probe18_sha)

    # ---- 指引生成（8 组锚定编辑 + 不变量断言）----
    t_work, edit_list = build_guidance(base_text)
    edit_list_sorted = sorted(edit_list, key=lambda e: e["edit"])
    section_asserts = assert_guidance_invariants(base_text, t_work)

    guidance19_bytes = t_work.encode("utf-8")
    guidance19_sha = hashing.sha256_bytes(guidance19_bytes)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance15_sha=guidance15_sha, guidance19_sha=guidance19_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance19_bytes=len(guidance19_bytes),
        r15_record_sha=r15_record_sha, r18_record_sha=r18_record_sha,
        axis_probe=axis_probe, run_probe=run_probe, typ_probe=typ_probe,
        dev18_probe=dev18_probe, probe18_rec=probe18_rec,
        witness_sha=witness_sha, protocol_sha=protocol_sha,
        png_checks=png_checks, edit_list=edit_list_sorted,
        section_asserts=section_asserts)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r18-prep-record 24 键逐键镜像
    missing = sorted(set(r18_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r18_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r18-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # hypothesis_test 逐字断言链：任务给定文本→json.loads→常量→记录字段
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if record["hypothesis_test"] != HYPOTHESIS_TEST:
        _fail("hypothesis_test 与预注册判据常量不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != "axis-plan-r19-criterion-operational":
        _fail("hypothesis_test.hypothesis_id 不符")
    if HYPOTHESIS_TEST["adjudication"]["descriptive_boundary_note"].find(
            "以冻结件 axis-experiment-plan-r17-r20.json 为准") < 0:
        _fail("hypothesis_test descriptive_boundary_note 缺冻结件引用")
    # 结构自证（判据侧轮口径；判据节首变纪律）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（判据侧单变量轮）")
    if len(record["changed_variables"]) != 2:
        _fail("changed_variables 必须恰 2 项（(iii-a) 条款/轮次标识）")
    if [v["id"] for v in record["changed_variables"]] != [
            "guidance-s4-iii-a-contact-operational-clause",
            "round-identity-sync"]:
        _fail("changed_variables 顺序/标识不符")
    if any(v["instrument_change"] is not False
           for v in record["changed_variables"]):
        _fail("changed_variables 全部须为非仪器侧变量")
    if record["manipulated_factor"].find(
            "唯一操纵因素=判读指引 §4 增补 (iii-a)") != 0:
        _fail("manipulated_factor 不符（唯一操纵因子=§4(iii-a) 条款增补）")
    if record["pre_round_review"]["status"] != "satisfied_by_plan":
        _fail("pre_round_review.status != satisfied_by_plan")
    if "轴3 判据侧单变量轮" not in record["round_nature"]:
        _fail("round_nature 缺「轴3 判据侧单变量轮」声明")
    if "渲染零变更" not in record["round_nature"]:
        _fail("round_nature 缺「渲染零变更」声明")
    if "stage1" not in record["round_nature"]:
        _fail("round_nature 缺 stage1 声明")
    if "首次触碰判据节" not in record["round_nature"]:
        _fail("round_nature 缺「首次触碰判据节」首变声明")
    if "不降低判断责任标准" not in record["no_loosening_note"]:
        _fail("no_loosening_note 缺「不降低判断责任标准」反放宽声明")
    if "可辨认证据" not in record["no_loosening_note"]:
        _fail("no_loosening_note 缺「可辨认证据」责任条件声明")
    if "原反放宽条款继续全部适用" not in record["no_loosening_note"]:
        _fail("no_loosening_note 缺反放宽承接声明")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    if "renders-r14b" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 renders-r14b 图像口径")
    if "R19T/R19B" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 R19T/R19B 前缀口径")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"][
            "zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved "
              "必须为真")
    if len({p["sha256_measured"] for p in png_checks}) != 3:
        _fail("四 PNG sha 集合应为 3 个不同值（两 bottom 同哈希）")
    if record["guidance_reuse"]["mode"] != "mechanical_transform_derive":
        _fail("guidance_reuse.mode 不符")
    if not record["guidance_reuse"]["edit_list"]:
        _fail("guidance_reuse.edit_list 不得为空（本轮有指引变换）")
    if record["guidance_reuse"]["base_sha256"].startswith(
            GUIDANCE_R15_SHA_PREFIX) is not True:
        _fail("guidance_reuse.base_sha256 与 d5babc93 锚不符")
    if record["guidance_reuse"]["derived_sha256"] != guidance19_sha:
        _fail("guidance_reuse.derived_sha256 与实测不符")
    # edit_list[7]（edit 8）必须含 (iii-a) 全文且与指引落盘文本逐字一致
    e8 = next(e for e in edit_list_sorted if e["edit"] == 8)
    if e8.get("text_full") != BULLET_III_A:
        _fail("edit_list[7].text_full 与 BULLET_III_A 常量不一致")
    if BULLET_III_A not in t_work:
        _fail("(iii-a) bullet 未在 r19 指引文本中逐字落盘")
    if e8["content_sha256"] != hashing.sha256_text(BULLET_III_A):
        _fail("edit_list[7].content_sha256 与 (iii-a) 全文哈希不符")
    # (iii-a) 插入编辑锚纪律：锚不得引用冻结节标题（插入点=三路出口行首）
    if e8.get("anchor") != EXIT_ANCHOR or "§" in e8.get("anchor", ""):
        _fail("(iii-a) 插入编辑锚异常")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance15_sha=guidance15_sha, guidance19_sha=guidance19_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance19_bytes=len(guidance19_bytes),
        r15_record_sha=r15_record_sha, r18_record_sha=r18_record_sha,
        axis_probe=axis_probe, run_probe=run_probe, typ_probe=typ_probe,
        dev18_probe=dev18_probe, probe18_rec=probe18_rec,
        witness_sha=witness_sha, protocol_sha=protocol_sha,
        png_checks=png_checks, edit_list=edit_list_sorted,
        section_asserts=section_asserts)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r19-prep-record")

    # ---- 防覆写守卫 + 落盘 ----
    if GUIDANCE_R19.exists():
        if GUIDANCE_R19.read_bytes() != guidance19_bytes:
            _fail("observation-guidance-r19.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r19-prep] 重跑自证：observation-guidance-r19.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R19.write_bytes(guidance19_bytes)
        if GUIDANCE_R19.read_bytes() != guidance19_bytes:
            _fail("回读不一致: observation-guidance-r19.md")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r19-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r19-prep] 重跑自证：r19-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r19-prep-record.json")

    # ---- 汇总打印 ----
    print("[r19-prep] 验证通过：r15 指引基座锚 "
          f"{GUIDANCE_R15_SHA_PREFIX} OK（只读，零写入，"
          f"{len(base_text.encode('utf-8'))} B）；r15-prep-record schema 血"
          f"统锚 {R15_PREP_RECORD_SHA_PREFIX} OK；r18-prep-record 24 键镜像"
          f"源锚 {R18_PREP_RECORD_SHA_PREFIX} OK；witness-r14b 锚 "
          f"{WITNESS_R14B_SHA_PREFIX} OK；axis-plan 冻结锚 {AXIS_PLAN_SHA_PREFIX} "
          f"OK（stage1 R19=A3_criterion_contact_clarification、r16 基线 "
          f"M1=0.771429/M3=12/M4=0.261904、守门 G1/G2/G3）；round18-dev 锚 "
          f"{DEV_RECORD_R18_SHA_PREFIX} OK（next_iteration_targets[0] R19="
          f"轴3 指令在案；r18 参照 黑点 13/接触性 8/存在性其他 12）；"
          f"run-r16 判据锚 {RUN_R16_SHA_PREFIX} OK（M1=0.771429、"
          f"guard_ok=True）；typology 锚 {TYPOLOGY_SHA_PREFIX} OK（contact "
          f"族 r13–r16=8/15/5/10、r16=10 全 top、grand 38）；"
          f"blackdot-probe-r18 上下文锚 {BLACKDOT_PROBE_SHA_PREFIX} OK（仅"
          f"哈希+kind）；evaluation-protocol-v1 在盘锚 "
          f"{EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r19-prep] 渲染仪器实测（四 PNG 实测=witness-r14b 登记值；字节"
          "复用、零仪器变更）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r19-prep] hypothesis_test 逐字断言链：预注册判据原文文本 → "
          "json.loads → 常量 → 记录字段，三层相等 PASS（数值/口径零改动；"
          "hypothesis_id=axis-plan-r19-criterion-operational；5=10/2、"
          "|0.261904-0.26|=0.001904≤0.005、contact 基线 8/15/5/10 与 "
          "r16=10 全 top 与 axis-plan/typology/run-r16 在案锚逐一相符）")
    print(f"[r19-prep] 顶层键镜像断言：与 r18-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）")
    print(f"[r19-prep] 指引不变量断言：{len(section_asserts)} 项全部通过"
          f"（§1/§2/§3/§3A/§5/§5A/§6/§7 分段逐字 {len(SECTION_PAIRS)} 段+"
          f"§4 前段/后段+§4 结构+§5A 原文整体 + 关键 substring "
          f"{len(REQUIRED_SUBSTRING_VALUES)} 条+反放宽原句恰 1 次 + 残留零"
          f"+新文本在位+(iii-a) 位置+节序）")
    print(f"[r19-prep] 字节数差：r19（{len(guidance19_bytes)} B）- r15（"
          f"{len(base_text.encode('utf-8'))} B）= "
          f"{len(guidance19_bytes) - len(base_text.encode('utf-8'))} B")
    print(f"[r19-prep] 工件 sha256：observation-guidance-r19.md="
          f"{_sha(GUIDANCE_R19)}")
    print(f"[r19-prep] 工件 sha256：r19-prep-record.json={_sha(RECORD)}")
    print("[r19-prep] §4(iii-a) 实际落盘全文：")
    k = t_work.index(BULLET_III_A)
    print(t_work[k:t_work.index(EXIT_ANCHOR, k)], end="")


if __name__ == "__main__":
    main()
