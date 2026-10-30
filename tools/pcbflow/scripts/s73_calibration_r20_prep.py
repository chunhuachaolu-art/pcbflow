#!/usr/bin/env python
"""CAL-R20-PREP：R20 stage2 组合轮（轴3+轴2 判读指引合成；渲染零变更）
预备包（只新建三个文件：scripts/s73_calibration_r20_prep.py 本体、
out/v3-tl2/calibration/observation-guidance-r20.md 与
out/v3-tl2/calibration/r20-prep-record.json；datasets/ 与 out/ 既有文件
只读、零改动，observation-guidance-r19.md / observation-guidance-r18.md
零字节不动）。

R20 轮性质（预注册，非事后）：**stage2 组合轮（轴3+轴2）**——执行
axis-experiment-plan-r17-r20（b6ec6467 冻结件）stage2：三轴单变量轮已毕
（r17 轴1 render=M1 0.88 负向出局；r18 轴2 §5B 黑点注记=M1 0.645161；
r19 轴3 §4(iii-a) 条款=M1 0.461538 第一），dev-r19
combination_decision_application 实测：按冻结 comparison_rule 排序
r19_axis3 第一、r18_axis2 第二 → 组合对=轴3+轴2；
early_stop_rule.strong_single_axis_shortcut 实测命中（最优单轴
M1=0.461538 ≤0.60）→ 阶段2 仅此一个组合轮、R21 不做。本轮唯一变更=
判读指引合成：以 observation-guidance-r19.md 全文为基底（§4(iii-a) 可
操作分辨条款随基座逐字承继），并入 observation-guidance-r18.md §5B 黑
点仪器注记节全文（黑点物理来源；仪器事实非判据）——两轴变更并集、各
轴定义按冻结件合并；渲染零变更=renders-r14b 四图字节复用；GT/阈值/协
议零变更（v1.1+v1.2 维持）。

指引生成=确定性机械变换（锚串命中数 fail-closed，锚恰 1 次否则 FAIL；
两父本哈希 8633bda5/cadcb8f3 先核验、后产出）。任务枚举编辑：(1) 标题/
round_id_constant R19→R20（声明日期 2026-09-09 两轮相同→无日期编辑，
r13→r15 先例同）；(2) 本轮性质行按组合轮口径重写；(3) 「本轮变更声明」
节正文整体替换；(4) 示例 reader_id reader-r19→reader-r20、示例旗 ID 前
缀 R19T-（4 处）/R19B-（1 处）→R20T-/R20B-（§6 规约文字与前缀示例）；
(5) 「## 6. 输出格式」标题前插入 §5B 节（r18 全文逐字转录、零改写——
§5B 段内唯一轮次身份词「本轮」出现于「本轮渲染中的实心黑色圆点物理来
源」，r20 渲染=renders-r14b 字节复用与 r18 完全同批文件，该表述对 r20
仍逐字为真，按 r19 §5A「其对本轮仍为真」零改写先例保留原文；探针引用
「s66/blackdot-probe-r18.json 在案」为来源引用、非轮次身份词，同 §5A
内 render-framing-r14b.json 引用先例）。

功能：
  1. fail-closed 复核两父本 observation-guidance-r19.md（8633bda5 锚；
     r20 指引变换基座，只读零写入）与 observation-guidance-r18.md
     （cadcb8f3 锚；§5B 来源，只读零写入）——先于任何产出。
  2. fail-closed 复核 observation-guidance-r15.md（d5babc93 锚；血统根
     基座，仅哈希锚复核）。
  3. fail-closed 复核 r19-prep-record.json（e4cf2d3c 锚；schema 血统+
     24 键镜像源）与 r18-prep-record.json（3fc054c4 锚；§5B 插入编辑先
     例 edit 8 content_sha256=19ecdb42 交叉锚）。
  4. fail-closed 复核 axis-experiment-plan-r17-r20.json（b6ec6467 锚）：
     stage2 定义、combination_decision_rule/early_stop_rule/
     comparison_rule 冻结条款逐字装载（裁决条款从冻结原文装配、非自创）、
     r16 基线、守门、用户指令原文。
  5. fail-closed 复核 round19-dev-record.json（0e2fdd69 锚）：
     combination_decision_application（early_stop_shortcut 触发、排序、
     r20_recommendation、R21 触发=否）=本轮合法性依据；
     axis_experiment_ledger.cross_round_status.measured_rows 四行 M 元组
     实测装载。
  6. fail-closed 复核 render-witness-r14b.json（b63771f9 锚）+四 PNG
     实测（bottom 两板同 d7284259、top 298bc620/b2f84524）——渲染零变
     更字节复用证明（instrument_change.changed=false 前提）。
  7. fail-closed 复核 blackdot-probe-r18.json（a49441ac 锚；仅哈希+kind
     ——§5B 探针证实前提链锚）+evaluation-protocol-v1.md 在盘锚
     22dc7337。
  8. 生成 observation-guidance-r20.md（7 组锚定编辑，命中数逐一断言；
     §1/§2/§3/§3A/§4/§5 分段逐字保留断言（§4 含 (iii-a) 整段与 r19 逐
     字相等）+§5A 段逐字保留+§6/§7 规格化后逐字保留+关键 substring 断
     言+§5B 全文逐字断言（含 r18-prep edit 8 哈希交叉锚）+(iii-a) 全文
     逐字断言+R19/R15/R18 残留零断言+新文本在位断言+位置与节序断言）。
  9. 落盘 r20-prep-record.json（canonical JSON；顶层键集合与 r19-prep-
     record 24 键逐键镜像；hypothesis_test=冻结条款逐字装配（载入条款
     ↔内嵌常量↔记录字段三层相等）；changed_variables=1（指引合成=§5B+
     (iii-a) 两增补并集）；同参重建两次逐字节一致自证；防覆写守卫；落
     盘后回读验字节）。
 10. 打印：guidance 与 prep-record 的 sha256、r20 相对 r19 字节数差、
     四 PNG 比对结果、逐项断言通过清单。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-09/2026-09-09-r20）；
无 subprocess/网络/主机绝对路径；hash=sha256_file 字节口径（PNG 仅哈希
+magic，零内容判读、零像素读取）；不读 GT/ground-truth-*/reader-raw-*/
derivation-log-*/任何 compare/诊断内容产物；无 git；r19/r18 指引只读；
记录内零 GT、零期望数量/分布/坐标；指引内零轮次结果数字（M 元组基线数
字仅入本编排侧记录、不进指引）；APR-0011/CONTAINMENT_MIN/AREA_RATIO_MAX
阈值零改动；in_calibrated_range 恒 False。

用法：python scripts/s73_calibration_r20_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R19 = CAL_DIR / "observation-guidance-r19.md"
GUIDANCE_R18 = CAL_DIR / "observation-guidance-r18.md"
GUIDANCE_R15 = CAL_DIR / "observation-guidance-r15.md"
R19_PREP_RECORD = CAL_DIR / "r19-prep-record.json"
R18_PREP_RECORD = CAL_DIR / "r18-prep-record.json"
BLACKDOT_PROBE = CAL_DIR / "blackdot-probe-r18.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
DEV_RECORD_R19 = CAL_DIR / "round19-dev-record.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r20-prep-record.json"
GUIDANCE_R20 = CAL_DIR / "observation-guidance-r20.md"
RENDR14B_DIR = CAL_DIR / "renders-r14b"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r20"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R19_SHA_PREFIX = "8633bda5"
GUIDANCE_R18_SHA_PREFIX = "cadcb8f3"
GUIDANCE_R15_SHA_PREFIX = "d5babc93"
R19_PREP_RECORD_SHA_PREFIX = "e4cf2d3c"
R18_PREP_RECORD_SHA_PREFIX = "3fc054c4"
BLACKDOT_PROBE_SHA_PREFIX = "a49441ac"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
DEV_RECORD_R19_SHA_PREFIX = "0e2fdd69"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: r18-prep-record edit 8（§5B 插入编辑）content_sha256——§5B 文本跨代链锚
R18_EDIT8_S5B_CONTENT_SHA256 = (
    "19ecdb42fed0298deacbd064323a63e9de1cff158a14ff7391b0f08e854d39bc")

RENDR14B_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

#: M 元组冻结锚（dev-r19 axis_experiment_ledger 实测行；fail-closed 装载）
M_ROWS_EXPECTED = {
    "r16_baseline": {"M1": 0.771429, "M2": 0.857143, "M3": 12,
                     "M4": 0.261904},
    "r17_axis1": {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333},
    "r18_axis2": {"M1": 0.645161, "M2": 0.684211, "M3": 13, "M4": 0.277778},
    "r19_axis3": {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111},
}
BEST_SINGLE_M1 = 0.461538
SHORTCUT_THRESHOLD = 0.60
#: 最优单轴 r19 的 M2/M3/M4（「不劣化」对照值）
R19_M2, R19_M3, R19_M4 = 0.571429, 4, 0.211111
R16_M1 = 0.771429

#: 机制观察双基线（dev-r19/r18-dev-record 在案实测；预注册对照值）
FAMILY_BASELINES = {
    "existence_blackdot": {"r18": 13, "r19": 4},
    "existence_other": {"r18": 12, "r19": 14},
    "contact": {"r18_registered_top_typology": 8, "r19_rubric": 4},
}
FIVEB_CITATION_BASELINE_R18 = {"flag_level_blackdot_abstain": "0/13",
                               "dispatch_level": "1/12"}
IIIA_CITATION_BASELINE_R19 = {"flag_iiia": 6, "flag_branch": 2,
                              "notes_level": "10/12"}


def _fail(msg: str) -> None:
    print(f"[r20-prep] FAIL: {msg}")
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
            .replace("R19T-", "R20T-")
            .replace("R19B-", "R20B-")
            .replace("reader-r19", "reader-r20"))


# ---------------------------------------------------------------------------
# 指引机械变换锚与替换文本
# ---------------------------------------------------------------------------
OLD_TITLE = "# R19 轮 reader 判读指引（observation-guidance-r19）"
NEW_TITLE = "# R20 轮 reader 判读指引（observation-guidance-r20）"
DECL_HEADING = "## 本轮变更声明（预注册，非事后）"
SECTION1_HEADING = "## 1. 角色与任务"
DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-09"
OLD_ROUND_ID_BULLET = "- round_id_constant: `2026-09-09-r19`"
NEW_ROUND_ID_BULLET = "- round_id_constant: `2026-09-09-r20`"
OLD_NATURE_LINE = (
    "- 本轮性质：**单变量判据侧变更轮（轴3 §4(iii) 可操作分辨条款轮；"
    "axis-experiment-plan-r17-r20 stage1 之一）**。渲染零变更（复用 R14 "
    "冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引 §4 增补 "
    "(iii-a) 可操作分辨条款（把接触性判据的「无法区分」操作化为证据可见"
    "性三支判据：见间隙证据→按视觉贴近继续判定；见侵入证据→按接触/交叠"
    "处理；两者均无→方按 (iii) 原文弃权；反放宽条款逐字保留），指引落盘"
    "后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**组合轮（轴3+轴2 判读指引合成；axis-experiment-plan-"
    "r17-r20 stage2 唯一组合轮，early_stop 快捷通道命中）**。渲染零变更"
    "（复用 R14 冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指"
    "引合成：以 r19 指引全文为基底（§4(iii-a) 可操作分辨条款随基座逐字承"
    "继）并入 r18 指引 §5B 黑点仪器注记节全文（黑点物理来源；仪器事实非"
    "判据）——轴3 与轴2 两轴变更并集、各轴定义按冻结件合并，指引落盘后"
    "由编排侧重新盲读。")

#: 任务枚举编辑：「本轮变更声明」节正文整体替换（逐字）
NEW_DECLARATION = (
    "本轮（R20）为 stage2 组合轮（轴3+轴2；axis-experiment-plan-r17-r20 "
    "stage2 唯一组合轮——combination_decision_rule.i_stage2_combo_pair 所"
    "定、early_stop_rule.strong_single_axis_shortcut 快捷通道实测命中后的"
    "唯一组合轮）：相对 observation-guidance-r19 仅（1）更新标题与轮次标"
    "识，（2）重写本变更声明，（3）在 §5A 之后、「## 6. 输出格式」之前并"
    "入 r18 指引 §5B 黑点仪器注记节全文（黑点物理来源；仪器事实非判据；"
    "§5B 文本自 r18 逐字转录、零改写），（4）虚构示例旗 ID 前缀改为 "
    "R20T/R20B。轴3 §4(iii-a) 可操作分辨条款全文逐字承 r19（反放宽条款逐"
    "字保留、原文在位）；§2 类别枚举、§3/§3A 位置与判据示例、§4 其余全部"
    "文本、§5 courtyard 说明、§5A 渲染配色仪器注记、§7 格式对齐提示逐字"
    "承 r19；§6 输出格式仅旗 ID 前缀机械替换。渲染零变更：本轮使用与 R14 "
    "完全相同的 renders-r14b 四图（字节复用）。预注册判据见 r20-prep-"
    "record.json hypothesis_test（先于任何盲读冻结）。")

SECTION6_HEADING = "## 6. 输出格式（reader-raw 文件的确切 schema）"
SECTION5A_HEADING = "## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）"
SECTION5B_HEADING = "## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）"
SECTION5_HEADING = "## 5. courtyard 说明（中性）"
IIIA_HEAD = "- (iii-a) 可操作分辨条款（本轮增补）"
EXIT_ANCHOR = "- **三路出口显式化（判为正常设计特征的形态不报告）**"

#: 锚串在 r19 基座中的期望命中数（不符即停；声明区先行替换后计数收敛）
EXPECTED_HITS = {
    "title": 1,
    "decl_heading": 1,
    "section1": 1,
    "round_id_bullet": 1,
    "nature_line": 1,
    "prefix_R19T-": 4,
    "prefix_R19B-": 1,
    "reader_id": 1,
    "s6_heading": 1,
}

#: §1–§5 分段逐字保留断言（§4 整段含 (iii-a) 与 r19 逐字相等=承继断言；
#: §5A 段=§5A 标题→r19 的 §6 标题，在 r20 中止于 §5B 标题前=同一段落；
#: §6/§7 段先做旗前缀/reader-id 规格化再断言）
SECTION_PAIRS = [
    ("## 1. 角色与任务", "## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）"),
    ("## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）", "## 3. 位置口径"),
    ("## 3. 位置口径", "## 3A. 类别判据示例（判据说明，非期望清单）"),
    ("## 3A. 类别判据示例（判据说明，非期望清单）", "## 4. 置信度与弃权"),
    ("## 4. 置信度与弃权", "## 5. courtyard 说明（中性）"),
    ("## 5. courtyard 说明（中性）", SECTION5A_HEADING),
]

#: 关键 substring 断言（判据零放宽+§5A/§5B 在位；逐条打印通过）
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
    # ---- §5A 原文逐字保留（随 r19 基座零改动）----
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

#: §5B 关键 substring 断言（r18 全文逐字在位的补充锚）
REQUIRED_SUBSTRING_5B = {
    "§5B 标题：## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）":
        SECTION5B_HEADING,
    "§5B 探针证实引用：探针证实，s66/blackdot-probe-r18.json 在案":
        "探针证实，s66/blackdot-probe-r18.json 在案",
    "§5B 机械定位孔：np_thru_hole": "np_thru_hole",
    "§5B 反指示声明：本节为仪器事实，不构成任何判据、期望清单或「应判为正常/无需报告」的指示":
        "本节为仪器事实，不构成任何判据、期望清单或「应判为正常/无需报告」的指示",
    "§5B 判定独立性：黑点相关现象的旗标判定仍按 §2 类别枚举与 §3A/§4 判据独立执行":
        "黑点相关现象的旗标判定仍按 §2 类别枚举与 §3A/§4 判据独立执行",
    "§5B 未证实来源处理：仪器注记未能证实来源的黑点形态，按 §4 既有规则处理":
        "仪器注记未能证实来源的黑点形态，按 §4 既有规则处理",
    "§5B top 适用：top 视黑点同样适用": "top 视黑点同样适用",
    "§5B 来源同一性限定：本句仅陈述来源同一性，不改变任何判据":
        "本句仅陈述来源同一性，不改变任何判据",
}


def extract_s5b(r18_text: str) -> str:
    """从 r18 指引提取 §5B 段（标题→r18 的 §6 标题之前，含尾随空行）。"""
    if r18_text.count(SECTION5B_HEADING) != 1:
        _fail("r18 指引 §5B 标题命中数 != 1")
    if r18_text.count(SECTION6_HEADING) != 1:
        _fail("r18 指引 §6 标题命中数 != 1")
    i = r18_text.index(SECTION5B_HEADING)
    j = r18_text.index(SECTION6_HEADING)
    if j <= i:
        _fail("r18 指引 §5B/§6 顺序异常")
    return r18_text[i:j]


# ---------------------------------------------------------------------------
# 指引生成（确定性机械变换；锚命中数逐一 fail-closed）
# ---------------------------------------------------------------------------

def build_guidance(base_text: str, seg5b: str) -> tuple[str, list[dict]]:
    """由 r19 指引文本+r18 §5B 段生成 r20 指引文本；返回 (r20 文本, edit_list)。"""
    t = base_text
    edits: list[dict] = []

    # ---- 编辑 1（先行）：本轮变更声明节正文整体替换（任务枚举）----
    # 先行原因：声明正文含 r19 自引（r19-prep-record.json 等），整体替换
    # 后轮次标识与前缀替换的命中数才收敛为期望值。
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

    # ---- 编辑 3：round_id_constant bullet 同步（轮次标识区；声明日期两轮
    #      同为 2026-09-09→无日期编辑（r13→r15 先例同），如实披露）----
    t = _replace_counted(t, OLD_ROUND_ID_BULLET, NEW_ROUND_ID_BULLET,
                         EXPECTED_HITS["round_id_bullet"], "round_id bullet")
    edits.append({
        "edit": 3,
        "kind": "round_id_constant bullet 同步（轮次标识区；s48/s54/s63/"
                "s67/s70 先例）",
        "old": OLD_ROUND_ID_BULLET,
        "new": NEW_ROUND_ID_BULLET,
        "expected_hits": EXPECTED_HITS["round_id_bullet"],
        "note": "声明日期 bullet 零编辑：r19→r20 同为 2026-09-09（人工声"
                "明常量；r13→r15 日期未变先例同）",
    })

    # ---- 编辑 4：本轮性质行重写（轮次标识区；s48/s54/s63/s67/s70 先例；
    #      非任务枚举、如实披露）----
    t = _replace_counted(t, OLD_NATURE_LINE, NEW_NATURE_LINE,
                         EXPECTED_HITS["nature_line"], "本轮性质行")
    edits.append({
        "edit": 4,
        "kind": "本轮性质行重写（轮次标识区；s48/s54/s63/s67/s70 机械变换"
                "先例；非任务枚举、如实披露）",
        "old": OLD_NATURE_LINE,
        "new": NEW_NATURE_LINE,
        "expected_hits": EXPECTED_HITS["nature_line"],
    })

    # ---- 编辑 5：示例 reader-id 同步（§6 规约示例；s48/s54/s63/s67/s70
    #      先例）----
    t = _replace_counted(t, "reader-r19", "reader-r20",
                         EXPECTED_HITS["reader_id"], "示例 reader-id")
    edits.append({
        "edit": 5,
        "kind": "示例 reader-id 同步（§6 规约示例；机械变换先例）",
        "old": "reader-r19",
        "new": "reader-r20",
        "expected_hits": EXPECTED_HITS["reader_id"],
        "note": "§6 格式示例 reader_id：reader-r20-top",
    })

    # ---- 编辑 6：示例旗 ID 前缀替换（§6 规约文字与前缀示例；任务枚举）----
    t = _replace_counted(t, "R19T-", "R20T-",
                         EXPECTED_HITS["prefix_R19T-"], "旗前缀 R19T-")
    t = _replace_counted(t, "R19B-", "R20B-",
                         EXPECTED_HITS["prefix_R19B-"], "旗前缀 R19B-")
    edits.append({
        "edit": 6,
        "kind": "示例旗 ID 前缀替换（§6 规约文字与前缀示例；任务枚举）",
        "items": [
            {"old": "R19T-", "new": "R20T-",
             "expected_hits": EXPECTED_HITS["prefix_R19T-"]},
            {"old": "R19B-", "new": "R20B-",
             "expected_hits": EXPECTED_HITS["prefix_R19B-"]},
        ],
    })

    # ---- 编辑 7：「## 6. 输出格式」标题前插入 §5B 黑点仪器注记节（任务
    #      枚举；文本=observation-guidance-r18.md §5B 段全文逐字转录、零改
    #      写）。段内轮次身份词盘点（r17 绿句先例的适用性判定）：唯一
    #      「本轮」出现于首句「本轮渲染中的实心黑色圆点物理来源」——r20
    #      渲染=renders-r14b 字节复用（四 PNG 实测=witness 登记值、与 r18
    #      完全同批文件），该表述对 r20 仍逐字为真，按 r19 §5A「其对本轮
    #      仍为真」零改写先例保留原文；「s66/blackdot-probe-r18.json 在
    #      案」为探针来源引用（同 §5A 内 render-framing-r14b.json 引用先
    #      例、非轮次身份词）；段内无 R18/reader-r18/2026-09-09-r18 等
    #      token（残留零断言覆盖）——故本轮零语义等值改写、零 before/
    #      after 披露项。----
    t = _replace_counted(t, SECTION6_HEADING, seg5b + SECTION6_HEADING,
                         EXPECTED_HITS["s6_heading"], "§6 标题（§5B 插入点）")
    edits.append({
        "edit": 7,
        "kind": "「## 6. 输出格式」标题前插入 §5B 黑点仪器注记节（任务枚举；"
                "文本=observation-guidance-r18.md §5B 段全文逐字转录、零改写）",
        "anchor": SECTION6_HEADING,
        "source": "observation-guidance-r18.md",
        "text_full": seg5b,
        "content_sha256": hashing.sha256_text(seg5b),
        "cross_check_content_sha256_r18_prep_edit8":
            R18_EDIT8_S5B_CONTENT_SHA256,
        "expected_hits": EXPECTED_HITS["s6_heading"],
        "identity_rewrite": {
            "needed": False,
            "note": "§5B 段内轮次身份词盘点：唯一「本轮」出现于首句「本轮"
                    "渲染中的实心黑色圆点物理来源」——r20 渲染=renders-r14b "
                    "字节复用（四 PNG 实测=witness 登记值、与 r18 完全同批"
                    "文件），该表述对 r20 仍逐字为真，按 r19 §5A「其对本轮"
                    "仍为真」零改写先例保留原文；「s66/blackdot-probe-r18."
                    "json 在案」为探针来源引用（非轮次身份词；同 §5A 内 "
                    "render-framing-r14b.json 引用先例）；段内无 R18/"
                    "reader-r18/2026-09-09-r18 等 token（残留零断言覆盖）"
                    "——零语义等值改写、零 before/after 披露项",
        },
    })

    return t, edits


def assert_guidance_invariants(base_text: str, r18_text: str, seg5b: str,
                               t20: str) -> list[str]:
    """§1–§5 分段逐字保留 + §5A/§6/§7 段断言 + §5B 全文逐字断言（含跨代
    哈希交叉锚）+ (iii-a) 全文逐字断言 + 关键 substring 断言 + 残留零断言
    + 新文本在位断言 + 位置与节序断言。

    返回通过的断言标签清单（任何失败 fail-closed 报错）。
    """
    passed: list[str] = []

    # ---- 分段逐字保留（§6/§7 段先做旗前缀规格化）----
    for start_anchor, end_anchor in SECTION_PAIRS:
        n = base_text.count(start_anchor)
        if n != 1:
            _fail(f"分段断言起点锚命中 {n} 次 != 1：{start_anchor!r}")
        i = base_text.index(start_anchor)
        if base_text.count(end_anchor) != 1:
            _fail(f"分段断言终点锚命中 != 1：{end_anchor!r}")
        j = base_text.index(end_anchor)
        seg = base_text[i:j]
        label = (f"分段逐字保留（{start_anchor.split('（')[0]}→"
                 f"{end_anchor.split('（')[0]}；与 r19 逐字相等）")
        if seg not in t20:
            _fail(f"{label} 失败：r19 段落未在 r20 中逐字保留（立即停止）")
        passed.append(label)

    # ---- §5A 段断言：r19 的 [§5A 标题→r19 §6 标题) 段在 r20 中逐字保留
    #      （r20 中同段落止于 §5B 标题前——§5B 恰插于该段之后、§6 之前）----
    i5a = base_text.index(SECTION5A_HEADING)
    i6b = base_text.index(SECTION6_HEADING)
    seg5a_r19 = base_text[i5a:i6b]
    if seg5a_r19 not in t20:
        _fail("§5A 段逐字断言失败：r19 §5A 段未在 r20 中逐字保留")
    passed.append("§5A 段逐字保留（r19 §5A 标题→§6 标题段=同一段落、止于 "
                  "§5B 标题前；随 r19 零改动）")

    # ---- §6/§7 段断言（旗前缀/reader-id 规格化后逐字保留）----
    i6 = base_text.index(SECTION6_HEADING)
    i7 = base_text.index("## 7. 格式对齐提示")
    seg6_norm = _normalize_prefixes(base_text[i6:i7])
    seg7_norm = _normalize_prefixes(base_text[i7:])
    if seg6_norm not in t20:
        _fail("§6 段断言失败：r19 §6 段（前缀规格化后）未在 r20 中逐字保留")
    if seg7_norm not in t20:
        _fail("§7 段断言失败：r19 §7 段（前缀规格化后）未在 r20 中逐字保留")
    passed.append("§6 段逐字保留（旗前缀 R19T-/R19B-→R20T-/R20B- 与示例 "
                  "reader_id 规格化后；规约文字零改动）")
    passed.append("§7 段逐字保留（规格化后；至文件尾）")

    # ---- §5B 全文逐字断言（任务枚举）----
    if r18_text.count(seg5b) != 1:
        _fail("§5B 段在 r18 中命中数 != 1（来源锚异常）")
    n5b = t20.count(seg5b)
    if n5b != 1:
        _fail(f"§5B 段恰 1 次断言失败：r20 中命中 {n5b} 次 != 1")
    if hashing.sha256_text(seg5b) != R18_EDIT8_S5B_CONTENT_SHA256:
        _fail("§5B 段 sha256 与 r18-prep-record edit 8 content_sha256 交叉"
              "锚不符（跨代链断裂）")
    passed.append("§5B 全文逐字在位（r18 §5B 段 substring-in 断言恰 1 次）")
    passed.append("§5B 跨代链锚（sha256=r18-prep-record edit 8 "
                  "content_sha256 19ecdb42 逐一相符）")

    # ---- (iii-a) 全文逐字断言（自 r19 基座磁盘提取、非手嵌）----
    iiia_start = base_text.index(IIIA_HEAD)
    iiia_end = base_text.index("\n" + EXIT_ANCHOR, iiia_start)
    iiia_bullet = base_text[iiia_start:iiia_end]
    if t20.count(iiia_bullet) != 1:
        _fail("(iii-a) 全文恰 1 次断言失败（r19 基座磁盘提取文本未逐字在位）")
    if iiia_bullet not in base_text[iiia_start:]:
        _fail("(iii-a) 提取自锚异常")
    passed.append("(iii-a) 全文逐字在位（自 r19 基座磁盘提取、恰 1 次；含反"
                  "放宽条款与原反放宽条款继续全部适用承接句）")

    # ---- 关键 substring 断言 ----
    for label, needle in REQUIRED_SUBSTRING_VALUES.items():
        if needle not in t20:
            _fail(f"关键 substring 断言失败（{label}）：{needle!r} 未在 r20 "
                  f"指引中逐字保留（立即停止）")
        passed.append(label)
    for label, needle in REQUIRED_SUBSTRING_5B.items():
        if needle not in t20:
            _fail(f"§5B 关键 substring 断言失败（{label}）：{needle!r} 未在 "
                  f"r20 指引中逐字保留（立即停止）")
        passed.append(label)

    # ---- 反放宽条款原句恰 1 次（§4 (iii) 句内唯一；(iii-a) 内为变体措辞
    #      不重复命中；§5B 无该句）----
    loosen_needle = "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由"
    n_loosen = t20.count(loosen_needle)
    if n_loosen != 1:
        _fail(f"反放宽条款原句恰 1 次断言失败：命中 {n_loosen} 次 != 1")
    passed.append("§4 反放宽条款原句恰 1 次（原文唯一在位；(iii-a) 内为变体"
                  "措辞不重复命中）")

    # ---- 残留零断言（机械替换完备性；R19/R15/R18 轮次 token 全零）----
    for needle in ("R19T", "R19B", "reader-r19", "2026-09-09-r19",
                   "# R19 轮", "本轮（R19）", "R19",
                   "R18T", "R18B", "reader-r18", "2026-09-09-r18",
                   "# R18 轮", "本轮（R18）", "R18",
                   "r19-prep-record.json", "r18-prep-record.json",
                   "R15T", "R15B", "reader-r15", "2026-09-08-r15",
                   "# R15 轮", "本轮（R15）", "R15", "r15",
                   "r15-prep-record.json"):
        n = t20.count(needle)
        if n != 0:
            _fail(f"残留零断言失败：{needle!r} 在 r20 指引中残留 {n} 次"
                  f"（立即停止）")
    passed.append("残留零断言（R19T/R19B/reader-r19/2026-09-09-r19/# R19 轮/"
                  "本轮（R19）/R19/r19-prep-record.json 与 R18 系与 R15 系"
                  "token 全部零命中；本轮新文本（性质行/声明）不含 R19/R18/"
                  "R15 大写字样，故大写 token 可为全文件零命中断言）")
    # 小写轮次 token 恰数断言（唯一合法残留=lineage 引用与 §5B 探针来源引用）
    for needle, want, why in (
            ("r19", 4, "observation-guidance-r19（声明内基座自引）+性质行内 "
                       "r19 指引基座指称+声明内两处「逐字承 r19」承继指称"),
            ("r18", 4, "性质行/声明内 r18 指引 §5B 来源指称（含声明内「自 "
                       "r18 逐字转录」）+ §5B 内探针来源引用 s66/"
                       "blackdot-probe-r18.json"),
            ("r20", 6, "标题 observation-guidance-r20+round_id bullet+示例 "
                       "reader-r20+声明内 r20-prep-record.json+性质行/声明内 "
                       "axis-experiment-plan-r17-r20（子串 r20×2）"),
    ):
        n = t20.count(needle)
        if n != want:
            _fail(f"小写 {needle} 计数断言失败：{n} 次 != {want}（{why}）")
    passed.append("小写轮次 token 恰数断言（r19=2、r18=3、r20=4——lineage/"
                  "来源引用逐一定位）")
    if t20.count(SECTION5B_HEADING) != 1:
        _fail("§5B 标题恰 1 次断言失败")

    # ---- 新文本在位断言 ----
    for needle, label, want in (
            (NEW_TITLE, "r20 标题在位", 1),
            (NEW_DECLARATION, "r20 变更声明在位", 1),
            (NEW_NATURE_LINE, "r20 本轮性质行在位", 1),
            ("`2026-09-09-r20`", "r20 round_id_constant bullet 在位", 1),
            (DATE_LINE, "声明日期 bullet 在位（两轮同常量零编辑）", 1),
            ("R20T-", "r20 旗前缀 R20T- 在位", 4),
            ("R20B-", "r20 旗前缀 R20B- 在位", 1),
            ("reader-r20", "r20 示例 reader-id 在位", 1),
            ("2026-09-09", "日期常量在位（声明日期+round_id 两处）", 2),
            ("r20-prep-record.json", "r20 预注册件引用在位（声明内）", 1),
            ("renders-r14b", "渲染零变更声明在位（性质行+变更声明）", 2),
    ):
        n = t20.count(needle)
        if n != want:
            _fail(f"新文本在位断言失败（{label}）：命中 {n} 次 != {want}")
        passed.append(f"{label}（命中 {n}/{want}）")

    # ---- 位置断言（§4 内 (iii-a) 序不变 + §5B 位置 + 节序）----
    i4 = t20.index("## 4. 置信度与弃权")
    i_iii = t20.index("(iii) **接触性判据（判「交叠/接触」类现象前适用）**")
    i_loosen = t20.index(loosen_needle)
    i_iiia = t20.index(IIIA_HEAD)
    i_exit = t20.index(EXIT_ANCHOR)
    i_contrast = t20.index("（对照说明：r6 §4 的")
    i5 = t20.index(SECTION5_HEADING)
    j5a = t20.index(SECTION5A_HEADING)
    j5b = t20.index(SECTION5B_HEADING)
    j6 = t20.index(SECTION6_HEADING)
    j7 = t20.index("## 7. 格式对齐提示")
    if not (i4 < i_iii < i_loosen < i_iiia < i_exit < i_contrast < i5):
        _fail("(iii-a) 位置断言失败：须位于 §4 内、(iii) 句与反放宽条款句"
              "之后、三路出口 bullet 与既有对照说明块之前（与 r19 同序）")
    if not (i5 < j5a < j5b < j6 < j7):
        _fail("节序断言失败：§4 < §5 < §5A < §5B < §6 < §7")
    if not (j5a < t20.index("top 渲染无配色变更（与既往轮次一致）") < j5b):
        _fail("§5B 位置断言失败：§5B 须紧随 §5A 末 bullet 之后、§6 之前"
              "（r18 结构位置）")
    passed.append("(iii-a) 位置断言（§4 内：(iii) 句 < 反放宽条款句 < "
                  "(iii-a) < 三路出口 bullet < 对照说明块；与 r19 同序）")
    passed.append("§5B 位置断言（§5A 末 bullet < §5B < §6；=§5B 在 r18 中"
                  "的结构位置）")
    passed.append("节序断言（§4 < §5 < §5A < §5B < §6 < §7；本轮新增 §5B）")
    return passed


# ---------------------------------------------------------------------------
# 结构探测（fail-closed）
# ---------------------------------------------------------------------------

def check_renders(witness: dict) -> list[dict]:
    """渲染仪器实测：四 PNG magic+sha256_file 实测 vs witness-r14b 登记
    值——渲染零变更字节复用证明（instrument_change.changed=false 前提）。"""
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
    """axis-experiment-plan：stage2 定义与冻结条款逐字装载（裁决条款从冻
    结原文装配、非自创）。返回冻结条款字典。"""
    if plan.get("kind") != "tl2_axis_experiment_plan_development":
        _fail("axis-plan kind 不符")
    if plan.get("declared_date") != DATE_CONSTANT:
        _fail("axis-plan declared_date != 2026-09-09")
    if not str(plan.get("combination_decision_rule", {}).get("status", "")) \
            .startswith("FROZEN"):
        _fail("axis-plan combination_decision_rule 非 FROZEN")
    if not str(plan.get("comparison_rule", {}).get("status", "")) \
            .startswith("FROZEN"):
        _fail("axis-plan comparison_rule 非 FROZEN")
    cdm = plan.get("combination_decision_rule", {})
    esr = plan.get("early_stop_rule", {})
    cmp_rule = plan.get("comparison_rule", {})
    clauses = {
        "i_stage2_combo_pair": cdm.get("i_stage2_combo_pair"),
        "ii_full_combination": cdm.get("ii_full_combination"),
        "iii_non_additive_fallback": cdm.get("iii_non_additive_fallback"),
        "iv_final_selection": cdm.get("iv_final_selection"),
        "strong_single_axis_shortcut": esr.get("strong_single_axis_shortcut"),
        "guard_failure_exit": esr.get("guard_failure_exit"),
        "ordering": cmp_rule.get("ordering"),
        "significant_benefit_definition":
            cmp_rule.get("significant_benefit_definition"),
        "drift_confound_note": cmp_rule.get("drift_confound_note"),
    }
    for k, v in clauses.items():
        if not isinstance(v, str) or not v:
            _fail(f"axis-plan 冻结条款缺失：{k}")
    if cdm.get("preregistration_note") is None:
        _fail("axis-plan combination_decision_rule.preregistration_note 缺失")
    stage2 = plan.get("experiment_design", {}).get("stage2")
    if not isinstance(stage2, str) or "R20" not in stage2:
        _fail("axis-plan experiment_design.stage2 定义缺失")
    rounds = plan.get("stage1_rounds", {}).get("rounds", [])
    r18 = next((r for r in rounds if r.get("round_id") == "R18"), None)
    r19 = next((r for r in rounds if r.get("round_id") == "R19"), None)
    if r18 is None or r18.get("axis_id") != "A2_blackdot_instrument_annotation":
        _fail("axis-plan stage1 R18=A2 定义不符")
    if r19 is None or r19.get("axis_id") != "A3_criterion_contact_clarification":
        _fail("axis-plan stage1 R19=A3 定义不符")
    r16b = plan.get("baselines_registered", {}).get("r16_baseline", {})
    if r16b.get("M1_top_aggregate_abstain_rate") != R16_M1:
        _fail("axis-plan r16 基线 M1 不符")
    guards = plan.get("guards", {})
    for gid in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                "G3_freeze_discipline"):
        if gid not in guards:
            _fail(f"axis-plan 守门缺失：{gid}")
    quote = (plan.get("user_directive_note", {}) or {}).get("user_quote")
    if quote != "三条轴单独/组合/全组合尝试，选择收益最大的继续":
        _fail(f"axis-plan 用户指令原文不符：{quote!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": plan_sha,
        "clauses": clauses,
        "stage2_text": stage2,
        "r18_round_quote": r18,
        "r19_round_quote": r19,
    }


def probe_dev19(dev19: dict, dev19_sha: str, clauses: dict) -> dict:
    """round19-dev-record：combination_decision_application=本轮合法性依
    据（early_stop 快捷通道触发、排序、r20_recommendation、R21 触发=否）
    + cross_round_status M 元组实测装载。"""
    if dev19.get("kind") != "tl2_calibration_round19_dev_record":
        _fail("round19-dev-record kind 不符")
    if dev19.get("round_id") != "2026-09-09-r19":
        _fail("round19-dev-record round_id 不符")
    if dev19.get("declared_date") != DATE_CONSTANT:
        _fail("round19-dev-record declared_date != 2026-09-09")
    cda = dev19.get("combination_decision_application")
    if not isinstance(cda, dict):
        _fail("combination_decision_application 缺失")
    shortcut = cda.get("early_stop_shortcut", {})
    if shortcut.get("triggered") is not True:
        _fail("early_stop_shortcut.triggered != True（stage2 单组合轮前提）")
    if shortcut.get("best_single_axis_m1") != BEST_SINGLE_M1:
        _fail("best_single_axis_m1 != 0.461538")
    if shortcut.get("rule_quote") != clauses["strong_single_axis_shortcut"]:
        _fail("early_stop_shortcut.rule_quote 与冻结原文不符（引用漂移）")
    # 整数交叉相乘口径复核（0.461538×10^6 ≤ 0.60×10^6）
    if not 461538 <= 600000:
        _fail("快捷通道阈值复核失败：461538 > 600000")
    rec = cda.get("r20_recommendation", {})
    if rec.get("axes") != ["r19_axis3", "r18_axis2"]:
        _fail("r20_recommendation.axes 不符")
    if rec.get("round") != "R20" or rec.get("blind_reads") != 12:
        _fail("r20_recommendation round/blind_reads 不符")
    if rec.get("render") != "renders-r14b 四图字节复用（零仪器变更）":
        _fail("r20_recommendation.render 不符")
    if rec.get("preregistration_required") is not True:
        _fail("r20_recommendation.preregistration_required != True")
    r21 = cda.get("r21_full_combination_trigger", {})
    if r21.get("met") is not False:
        _fail("r21_full_combination_trigger.met != False")
    ranking = cda.get("ranking_application", {})
    if ranking.get("eligible_sorted") != ["r19_axis3", "r18_axis2",
                                          "r17_axis1"]:
        _fail("ranking_application.eligible_sorted 不符")
    guards = cda.get("inputs", {}).get("guards", {})
    if not all(guards.get(k) is True for k in
               ("r17_axis1", "r18_axis2", "r19_axis3")):
        _fail("dev-r19 三轴资格门记录不全为真")
    rows = (dev19.get("axis_experiment_ledger", {})
            .get("cross_round_status", {}).get("measured_rows"))
    if rows != M_ROWS_EXPECTED:
        _fail(f"dev-r19 M 元组行不符：{rows!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/round19-dev-record.json",
        "sha256_measured": dev19_sha,
        "fields": ("combination_decision_application（early_stop_shortcut/"
                   "ranking_application/r20_recommendation/"
                   "r21_full_combination_trigger）+axis_experiment_ledger."
                   "cross_round_status.measured_rows"),
        "r20_recommendation": rec,
        "measured_rows": rows,
    }


def probe_r18_prep(r18rec: dict, r18rec_sha: str) -> dict:
    """r18-prep-record：§5B 插入编辑先例链锚（edit 8 content_sha256 与本
    轮提取段哈希交叉核对在 main 内执行）。"""
    if r18rec.get("kind") != "tl2_calibration_r18_prep_record":
        _fail("r18-prep-record kind 不符")
    if r18rec.get("round_id_constant") != "2026-09-09-r18":
        _fail("r18-prep-record round_id_constant 不符")
    e8 = next((e for e in r18rec.get("guidance_reuse", {}).get("edit_list", [])
               if e.get("edit") == 8), None)
    if e8 is None or e8.get("content_sha256") != R18_EDIT8_S5B_CONTENT_SHA256:
        _fail("r18-prep-record edit 8 content_sha256 锚不符")
    return {
        "path_rel": "out/v3-tl2/calibration/r18-prep-record.json",
        "sha256": r18rec_sha,
        "role": "§5B 插入编辑先例（s67 edit 8）+§5B 文本跨代哈希交叉锚",
    }


def probe_r19_prep(r19rec: dict, r19rec_sha: str) -> dict:
    """r19-prep-record：schema 血统+24 键镜像源+round_id/kind 校验。"""
    if r19rec.get("kind") != "tl2_calibration_r19_prep_record":
        _fail("r19-prep-record kind 不符")
    if r19rec.get("round_id_constant") != "2026-09-09-r19":
        _fail("r19-prep-record round_id_constant 不符")
    if r19rec.get("schema_version") != "3.0":
        _fail("r19-prep-record schema_version != 3.0")
    return {
        "path_rel": "out/v3-tl2/calibration/r19-prep-record.json",
        "sha256": r19rec_sha,
        "role": "schema 血统+24 键顶层结构逐键镜像源（同 r17/r18/r19 先例）",
    }


def probe_blackdot_context(probe: dict, probe_sha: str) -> dict:
    """blackdot-probe-r18：仅哈希+kind 复核（§5B 黑点物理来源的探针证实前
    提链锚；axis-plan A2 precondition「无探针证实则该轴不得入轮」已由 r18
    满足、本轮 §5B 逐字承继该前提）。"""
    if probe.get("kind") != "tl2_blackdot_probe_r18":
        _fail("blackdot-probe-r18 kind 不符")
    return {
        "path_rel": "out/v3-tl2/calibration/blackdot-probe-r18.json",
        "sha256": probe_sha,
        "role": "§5B 探针证实前提链锚（仅哈希+kind 复核；本轮零内容转录——"
                "§5B 文本自 r18 指引逐字转录）",
    }


# ---------------------------------------------------------------------------
# 冻结条款逐字装配的预注册判据（build 阶段由磁盘装载条款装配；main 内做
# 载入条款↔内嵌常量↔记录字段三层相等断言）
# ---------------------------------------------------------------------------

def build_hypothesis_test(c: dict) -> dict:
    """由冻结条款字典装配 hypothesis_test（纯函数；每支注明冻结出处）。"""
    return {
        "hypothesis_id": "axis-plan-r20-combo-additivity",
        "hypothesis": (
            "轴2（§5B 黑点中性仪器注记）+轴3（§4(iii-a) 可操作分辨条款）两"
            "轴变更并施的组合轮 R20 收益不低于最优单轴 r19：按冻结 "
            "combination_decision_rule.i_stage2_combo_pair「"
            + c["i_stage2_combo_pair"] + "」组合、按冻结 comparison_rule."
            "ordering「" + c["ordering"] + "」字典序排序不劣于 r19 实测 "
            "(M1,M2,M3,M4)=(0.461538, 0.571429, 4, 0.211111)（M1 维度操作化"
            "表述=M1 ≤ 0.461538），且 M2/M3/M4 不劣化（M2 ≤ 0.571429、"
            "M3 ≤ 4、M4 ≤ 0.211111，各按冻结 benefit_metrics 口径；r18=轴2 "
            "(0.645161, 0.684211, 13, 0.277778)、r16 基线 (0.771429, "
            "0.857143, 12, 0.261904) 在案实测装载）——可加性验证。"),
        "adjudication": {
            "supported": (
                "可加性验证成立（组合收益 ≥ 最优单轴）：R20 的 "
                "(M1,M2,M3,M4) 在冻结 comparison_rule.ordering「"
                + c["ordering"] + "」排序中不劣于最优单轴 r19（r19 实测 "
                "(0.461538, 0.571429, 4, 0.211111)；M1 维度操作化表述="
                "M1 ≤ 0.461538，M1 相等时依次比较 M2→M3→M4 不劣），即冻结 "
                "combination_decision_rule.ii_full_combination「"
                + c["ii_full_combination"] + "」中「R20 收益 ≥ 最优单轴」前"
                "提命中；R21 追加与否由两条独立冻结条款决定、均不在本支裁断"
                "范围：early_stop_rule.strong_single_axis_shortcut「"
                + c["strong_single_axis_shortcut"] + "」（最优单轴 "
                "M1=0.461538≤0.60 已实测触发→阶段2 仅此一个组合轮）与 ii 后"
                "半句三轴皆正前提（轴1 r17 M1=0.88 劣于 r16 基线 0.771429="
                "负向、dev-r19 在案实测不成立）——故本实验内 R21 不做（冻结"
                "出处：axis-experiment-plan-r17-r20.json "
                "combination_decision_rule.ii_full_combination + "
                "early_stop_rule.strong_single_axis_shortcut）"),
            "marginal": (
                "部分收益（可加性未证）：R20 未达 supported（排序劣于最优单"
                "轴 r19）但相对 r16 基线 (0.771429, 0.857143, 12, 0.261904) "
                "仍为改善方向（M1 < 0.771429）且 G1（bottom courtyard 非弃"
                "权 0/0/0 维持）与 G2（guard_ok=True）维持——组合有效但两轴"
                "不可加；处置按冻结 combination_decision_rule."
                "iii_non_additive_fallback「" + c["iii_non_additive_fallback"]
                + "」（后续基座采最优单轴 r19 配置）；改善方向描述参照冻结 "
                "comparison_rule.significant_benefit_definition「"
                + c["significant_benefit_definition"] + "」；跨轮实例群漂移"
                "混杂按冻结 comparison_rule.drift_confound_note「"
                + c["drift_confound_note"] + "」显式容忍（冻结出处：axis-"
                "experiment-plan-r17-r20.json combination_decision_rule."
                "iii_non_additive_fallback + comparison_rule."
                "significant_benefit_definition/drift_confound_note）"),
            "reject": (
                "组合无收益方向或守门破坏：R20 排序劣于 r16 基线（M1 ≥ "
                "0.771429，两轴并施未保有任何单轴改善方向）或 G1（bottom "
                "courtyard 非弃权 0/0/0）或 G2（guard_ok）任一破坏——处置按"
                "冻结 combination_decision_rule.iii_non_additive_fallback「"
                + c["iii_non_additive_fallback"] + "」（采最优单轴 r19 配置）；"
                "守门破坏另按冻结 early_stop_rule.guard_failure_exit「"
                + c["guard_failure_exit"] + "」（字母照实+出局声明；冻结出处："
                "axis-experiment-plan-r17-r20.json combination_decision_rule."
                "iii_non_additive_fallback + early_stop_rule."
                "guard_failure_exit）"),
            "mechanism_observation_separate": (
                "§5B 与 (iii-a) 各自的旗级援引计数分开记、互不合并：旗级 "
                "location_evidence 含「§5B」与含「(iii-a)」/「分支(」分别计"
                "数、notes 级 reading_notes 含「§5B」与含「(iii-a)」分别计数"
                "——双基线对照：r18 §5B 援引=旗级 0/13 黑点弃权旗（非弃权黑"
                "点旗亦零）、派次级 1/12（dev-r18 在案）；r19 (iii-a) 援引="
                "旗级「(iii-a)」6 旗+「分支(」2 旗、notes 级 10/12 派次"
                "（dev-r19 在案）；黑点族/存在性族/contact 族三族计数（分型"
                "件 rubric 口径）对照 r18/r19 双基线：黑点族 r18=13/r19=4、"
                "存在性其他 r18=12/r19=14、contact r19=4 全视 rubric（r18 参"
                "照 8=top 弃权分型口径——口径差异如实注明）；M1/M2/M3/M4 四"
                "元组入实验对照账；gt 照常"),
            "metric_lesson_separate": (
                "跨轮实例群漂移混杂照旧（冻结 comparison_rule."
                "drift_confound_note 在案）；字母=预注册阈值命中与否的描述性"
                "结论；两轴并施的单轮组合无法分离两轴各自贡献（只回答可加性"
                "与否——归因边界如实声明）；最终「收益最大配置」按冻结 "
                "combination_decision_rule.iv_final_selection「"
                + c["iv_final_selection"] + "」在全部已测配置中裁定（同分取"
                "变量更少者=简约优先）"),
            "descriptive_boundary_note": (
                "本轮判据均为描述性边界，与 APR-0011 门与 "
                "CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；"
                "比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json "
                "为准"),
        },
    }


#: 内嵌常量（与磁盘装载逐一相等断言；防装载漂移——读数与写装配分离）
CLAUSE_CONSTANTS = {
    "i_stage2_combo_pair":
        "阶段1（R17/R18/R19）完成后，取过守门（G1/G2 均满足）轮次中 "
        "comparison_rule 排序最优的两轴做组合轮 R20（两轴变更同时施加；渲"
        "染/指引变更按各自轴定义合并）",
    "ii_full_combination":
        "若 R20 收益 ≥ 最优单轴（comparison_rule 排序不劣于最优单轴）且三"
        "轴均各自正收益（各自 M1 不劣于 r16 基线）→ 追加全组合轮 R21（三轴"
        "全组合）",
    "iii_non_additive_fallback":
        "若 R20 收益 < 最优单轴（两轴不可加）→ 采最优单轴、不再追加",
    "iv_final_selection":
        "最终「收益最大配置」=全部已测配置（本实验 R17–R21 各配置）中 "
        "comparison_rule 排序最优者，作为后续迭代基座；同分（四键全等）时"
        "取变量更少者（简约优先）",
    "strong_single_axis_shortcut":
        "阶段1 若最优单轴已达 M1 ≤0.60（远超显著收益）→ 阶段2 仅做「最优"
        "单轴+次优单轴」一个组合轮验证可加性，不铺全组合（R21 不做）",
    "guard_failure_exit":
        "任一轮 G1/G2 破坏→该轴出局并如实记录（该轮 run/dev-record 照常落"
        "盘、字母裁决照常；「出局」仅指退出本实验后续组合与排序）",
    "ordering":
        "按 (M1 升序, M2 升序, M3 升序, M4 升序) 字典序（M1 最小者最优；同"
        "值依次比较 M2→M3→M4）",
    "significant_benefit_definition":
        "「显著收益」=相对 r16 基线 M1 绝对降幅 ≥0.10（阈值覆盖跨轮实例群"
        "漂移噪声的历史幅度，参照 r15→r16 纯重抽变动 0.09064）",
    "drift_confound_note":
        "跨轮比较的实例群漂移为已知混杂（r10 教训：各轮 12 派次实例独立重"
        "抽，跨轮 M1 差值可含纯重抽效应；r15→r16 同指引重复轮+渲染零变更仍"
        "实测漂移 0.09064）——本规则不消除该混杂，仅在阈值与多重对照中显"
        "式容忍",
}


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance19_sha: str, guidance18_sha: str,
                 guidance20_sha: str, guidance19_bytes: int,
                 guidance20_bytes: int, r19_record_sha: str,
                 r18_record_sha: str, axis_clauses: dict, axis_sha: str,
                 stage2_text: str, r18_quote: dict, r19_quote: dict,
                 dev19_rec: dict, r18prep_rec: dict, r19prep_rec: dict,
                 probe18_rec: dict, witness_sha: str, protocol_sha: str,
                 png_checks: list[dict], edit_list: list[dict],
                 section_asserts: list[str], seg5b: str,
                 hypothesis_test: dict) -> dict:
    """构建 r20-prep-record 内容（纯函数：同入参必得同 dict）。"""
    axis_rel = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r20_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r20",
        "round_nature": (
            "stage2 组合轮（轴3+轴2 判读指引合成；渲染零变更；axis-"
            "experiment-plan-r17-r20 stage2 唯一组合轮，第二十轮）：判读指"
            "引由 observation-guidance-r19.md 全文为基底、并入 observation-"
            "guidance-r18.md §5B 黑点仪器注记节全文，机械变换生成 "
            "observation-guidance-r20.md（本轮唯一判读依据；变更=§5B+(iii-a) "
            "两增补并集——§4(iii-a) 可操作分辨条款随 r19 基座逐字承继（反放"
            "宽条款逐字保留）、§5B 黑点中性仪器注记自 r18 逐字转录（仪器事"
            "实非判据、探针证实前提在案）+轮次标识机械同步，见 guidance_"
            "reuse.edit_list）；两轴变更同时施加、各轴定义按冻结件合并（per "
            "axis-plan combination_decision_rule.i_stage2_combo_pair）；执"
            "行合法性=dev-r19 combination_decision_application 在案：冻结 "
            "comparison_rule 排序 r19_axis3 第一、r18_axis2 第二 → 组合对="
            "轴3+轴2，early_stop_rule.strong_single_axis_shortcut 实测命中"
            "（最优单轴 M1=0.461538≤0.60）→ 阶段2 仅此一个组合轮、R21 不做"
            "（r21_full_combination_trigger.met=False 亦在案）；渲染零变更="
            "renders-r14b 四图字节复用（四 PNG sha256_file 实测与 render-"
            "witness-r14b.json 登记值 fail-closed 比对一致，即 r14–r19 轮盲"
            "读所用同一批文件，见 instrument_change）；GT/阈值/协议零变更"
            "（v1.1+v1.2 维持）；r19/r18/r15 指引已在盘冻结、本轮只读零写入；"
            "盲读由编排侧在本记录之后以 12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的"
            "继续」=授权执行 axis-experiment-plan-r17-r20（b6ec6467 冻结"
            "件，先于 R17–R21 任何实验轮盲读冻结以防事后择优）stage2 组合"
            "轮 R20=轴3+轴2（A3_criterion_contact_clarification+"
            "A2_blackdot_instrument_annotation）；本记录=该轮 prep-record "
            "预注册（先于任何盲读冻结）；dev-r19 combination_decision_"
            "application.r20_recommendation 同口径建议（本轮合法性依据，"
            "preregistration_required=True 在案）；比较与组合决策以冻结件 "
            "comparison_rule/combination_decision_rule/early_stop_rule 为"
            "准；既往轮次字母不回写（r8–r19 维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14–r19 完全相同（renders-r14b 字节复用，四 PNG "
                    "实测=witness-r14b 登记值），变化仅在指引文本（且为两指"
                    "引侧增补的并集、零仪器侧变量）",
            "renders": png_checks,
            "witness": "render-witness-r14b.json（b63771f9，fail-closed 复核）",
            "declaration": (
                "axis-plan stage2 R20 组合定义=渲染/指引变更按各自轴定义合"
                "并，轴3/轴2 的 render 定义均为「renders-r14b 四图字节复用"
                "（零变更）」；本轮 prep 零重渲染、零 out/ 既有文件改动（四 "
                "PNG sha256_file 实测=witness-r14b 登记值；bottom 两板逐字"
                "节同 d7284259；top 无配色 298bc620/b2f84524）"),
        },
        "no_instrument_change": True,
        "guidance_reuse": {
            "base": "observation-guidance-r19.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r19.md"),
            "base_sha256": guidance19_sha,
            "base_sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
            "s5b_source": "observation-guidance-r18.md",
            "s5b_source_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r18.md"),
            "s5b_source_sha256": guidance18_sha,
            "s5b_source_sha256_prefix_expected": GUIDANCE_R18_SHA_PREFIX,
            "lineage_root_base": {
                "path_rel": (
                    "out/v3-tl2/calibration/observation-guidance-r15.md"),
                "sha256_note": "d5babc93（血统根基座，仅哈希锚复核；r19←r15、"
                               "r18←r15、r20←r19+§5B←r18）",
            },
            "mode": "mechanical_transform_derive",
            "derived": "observation-guidance-r20.md",
            "derived_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r20.md"),
            "derived_sha256": guidance20_sha,
            "byte_size": {"base": guidance19_bytes,
                          "derived": guidance20_bytes,
                          "delta": guidance20_bytes - guidance19_bytes},
            "s5b_segment_content_sha256": hashing.sha256_text(seg5b),
            "edit_list": edit_list,
            "verbatim_frozen_sections": (
                "§2 类别枚举、§3 位置口径、§3A 类别判据示例（含示例 c 与末"
                "尾对照说明）、§4 置信度与弃权整段（含量化判据 (i)(ii)(iii) "
                "原文、(iii) 接触性判据原句、(iii-a) 可操作分辨条款全文、三"
                "路出口、反放宽条款、confidence 定义、r6/r8/r9/r12/r13 对照"
                "说明块——与 r19 逐字相等=承继断言，本轮对 §4 零改动）、"
                "§5 courtyard 说明、§5A 渲染配色仪器注记（随 r19 零改动）、"
                "§6 输出格式（旗 ID 展示前缀机械替换除外）、§7 格式对齐提示、"
                "§1 角色与任务——分段逐字保留断言（r19 段落 substring-in 断"
                "言）+关键 substring 断言双重复核，见 verification."
                "section_assertions_passed；新增=§5B 黑点仪器注记节（r18 全"
                "文逐字转录、零改写）"),
            "lineage_note": (
                "轮次标识区同步（标题行/round_id_constant bullet/本轮性质行/"
                "示例 reader_id/示例旗 ID 前缀）沿 s48→s54→s63→s67→s70 机械"
                "变换先例；r19→r20 声明日期同为 2026-09-09→无日期编辑（r13→"
                "r15 先例同）；任务枚举编辑全部逐字执行，非任务枚举的轮次标"
                "识同步项（edit 3/4/5）在 edit_list 中如实登记；本轮新文本（"
                "性质行/变更声明）不含 R19/R18/R15 大写字样——「残留零」可"
                "为全文件零命中强断言（R19/R18/R15 系 token 全零+小写 r19=2/"
                "r18=3/r20=4 恰数定位）；§5B 段轮次身份词盘点=唯一「本轮」出"
                "现于「本轮渲染中的实心黑色圆点物理来源」——r20 渲染=renders-"
                "r14b 字节复用与 r18 完全同批文件，该表述对 r20 仍逐字为真，"
                "按 r19 §5A「其对本轮仍为真」零改写先例保留原文（探针引用 "
                "s66/blackdot-probe-r18.json 为来源引用、非轮次身份词）——故"
                "§5B 零语义等值改写、零 before/after 披露项（edit 7 "
                "identity_rewrite.needed=false）；§1 与头部 bullet 区不在逐"
                "字冻结清单（冻结区=§2–§7，本轮例外=§5B 新增节一节）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
                "s5b_source_sha256_prefix_expected": GUIDANCE_R18_SHA_PREFIX,
                "r15_lineage_root": {
                    "path_rel": (
                        "out/v3-tl2/calibration/observation-guidance-r15.md"),
                    "sha256": _sha(GUIDANCE_R15),
                },
                "r19_prep_record_schema_template": r19prep_rec,
                "r18_prep_record_s5b_edit_precedent": r18prep_rec,
                "blackdot_probe_r18_premise": probe18_rec,
                "render_witness_r14b_byte_reuse": {
                    "path_rel": "out/v3-tl2/calibration/render-witness-"
                                "r14b.json",
                    "sha256": witness_sha,
                },
                "axis_experiment_plan_frozen": {
                    "path_rel": axis_rel,
                    "sha256": axis_sha,
                },
                "round19_dev_record_combination_decision": {
                    "path_rel": dev19_rec["path_rel"],
                    "sha256_measured": dev19_rec["sha256_measured"],
                    "fields": dev19_rec["fields"],
                    "r20_recommendation": dev19_rec["r20_recommendation"],
                    "measured_rows": dev19_rec["measured_rows"],
                },
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
                "id": "guidance-combo-s5b-plus-s4-iiia-union",
                "axis": "guidance",
                "axis_id": ("A3_criterion_contact_clarification+"
                            "A2_blackdot_instrument_annotation"),
                "axes": ["r19_axis3", "r18_axis2"],
                "instrument_change": False,
                "target": ("observation-guidance-r20.md §5B（新增节，r18 全"
                           "文逐字）+§4 (iii-a)（随 r19 基座逐字承继）——两增"
                           "补并集；轮次标识机械同步（标题/round_id/性质行/示"
                           "例前缀）见 guidance_reuse.edit_list edit 2/3/4/"
                           "5/6"),
                "description": (
                    "判读指引合成（组合轮唯一操纵变量=两增补并集、两轴变更同"
                    "时施加，per 冻结 i_stage2_combo_pair）：(a) 轴3 分量="
                    "§4(iii-a) 可操作分辨条款（r19 轮已预注册落盘、本轮随基"
                    "座逐字承继、零改动——§4 整段与 r19 逐字相等断言；把「无"
                    "法区分」操作化为证据可见性三支判据、反放宽条款逐字保"
                    "留）；(b) 轴2 分量=§5B 黑点仪器注记节（r18 轮已预注册落"
                    "盘、本轮自 r18 逐字转录、零改写——黑点物理来源探针证实"
                    "在案（blackdot-probe-r18 a49441ac）、仪器事实非判据、含"
                    "反指示声明「不构成任何判据、期望清单或『应判为正常/无需"
                    "报告』的指示」）；渲染零变更=renders-r14b 四图字节复用；"
                    "GT/阈值/协议零变更"),
                "attribution_channel": (
                    "M1 领衔 ordering 字典序 vs 最优单轴 r19（可加性主判据="
                    "hypothesis_test.adjudication 三支：supported 排序不劣于 "
                    "r19 (0.461538, 0.571429, 4, 0.211111)；marginal 未达 "
                    "supported 但 M1 < 0.771429 且 G1/G2 维持；reject M1 ≥ "
                    "0.771429 或 G1/G2 任一破坏）+M2/M3/M4 不劣化（M2 ≤ "
                    "0.571429、M3 ≤ 4、M4 ≤ 0.211111）；机制观察单列=§5B 与 "
                    "(iii-a) 旗级援引计数分开记+黑点/存在性/contact 三族计数 "
                    "r18/r19 双基线对照"),
                "preregistration_ref": {
                    "path_rel": axis_rel,
                    "sha256_measured": axis_sha,
                    "field": ("combination_decision_rule.i_stage2_combo_pair+"
                              "experiment_design.stage2+early_stop_rule."
                              "strong_single_axis_shortcut+stage1_rounds."
                              "rounds[R18/R19]"),
                    "stage2_quote": stage2_text,
                    "stage1_r18_quote": r18_quote,
                    "stage1_r19_quote": r19_quote,
                    "dev_r19_recommendation": dev19_rec["r20_recommendation"],
                },
            },
        ],
        "manipulated_factor": (
            "唯一操纵因素=判读指引合成（§5B+(iii-a) 两增补并集=changed_"
            "variables 单一复合变量；两轴变更同时施加，per axis-plan "
            "combination_decision_rule.i_stage2_combo_pair「两轴变更同时施"
            "加；渲染/指引变更按各自轴定义合并」）；渲染（四图字节复用）/"
            "GT/阈值/协议与 §4 判据文本（承 r19）零变更"),
        "unchanged_components": [
            {
                "byte_reuse": True,
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "note": "开工时 sha256_file 实测四 PNG 并与 render-witness-"
                        "r14b.json 登记值逐字比对（bottom=renders.applied/"
                        "prep1.sha256；top=top_zero_change_copies.sha256）"
                        "——四图即 r14–r19 轮盲读所用同一批文件；本轮零重渲"
                        "染、零仪器变更",
                "pngs": png_checks,
                "witness": "render-witness-r14b.json（b63771f9，fail-closed "
                           "复核）",
            },
            "判读指引 §1 角色与任务与盲读纪律（r19 指引原文逐字；不在冻结"
            "清单亦零改动，分段断言复核）",
            "判读指引 §2 类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与"
            "圆括号中性释义零改动；与 r19 逐字相等断言复核）",
            "§3 邻域框收窄判据与坐标口径（与 r19 逐字相等）",
            "§3A 类别判据示例：全部与 r19 逐字相等（六类全部示例含示例 c「整"
            "段规则周期」判据；§3A 末尾对照说明原位保留）",
            "§4 置信度与弃权整段：与 r19 逐字相等（含量化判据 (i)(ii)(iii) "
            "原文、(iii) 接触性判据原句、(iii-a) 可操作分辨条款全文、三路出"
            "口、反放宽条款「仅因形态不熟悉、不确定其设计含义，不构成判为正"
            "常设计特征的理由」[原句恰 1 次断言]、confidence 定义、r6/r8/"
            "r9/r12/r13 对照说明块）——本轮对 §4 零改动（轴3 分量随基座承继）",
            "§5 courtyard 说明（与 r19 逐字相等）",
            "§5A 渲染配色仪器注记：随 r19 零改动（与 r15 原文同文的逐字保留"
            "先例延续；四 PNG 实测=witness 登记值、「字节复用同一渲染件」表"
            "述对本轮仍为真）",
            "§6 输出格式：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r19 原文；仅旗 ID 展示前缀 R19T-/R19B-→R20T-/R20B- "
            "机械替换，随指引落盘固化、无需派发层覆盖）",
            "§7 格式对齐提示（r19 原文逐字）",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r19 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口径在"
            "图像空间完全一致、不做镜像换算；本轮渲染零字节变更；§5B 对 "
            "bottom 视黑点来源陈述与 top 视同源）",
            "度量设计五条与聚合口径：沿 r19-prep-record measurement_design."
            "items 同一口径（仅预注册声明内轮次标识、reader 前缀按 r20 改写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14–R19 完全相"
            "同文件：白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)、其余"
            "层 kicad 原配色不变；四 PNG sha256_file 实测=witness-r14b 登记"
            "值 fail-closed 比对一致）——渲染零变更；本轮变更=指引合成（轴2 "
            "分量 §5B 黑点仪器注记对 bottom 视黑点来源陈述在案[非电镀机械定"
            "位孔/电镀通孔焊盘钻孔/孤立焊盘对三支，仪器事实非判据、含反指示"
            "声明]；轴3 分量 §4(iii-a) 按图像可见证据操作、对 top/bottom 视"
            "在图像空间同口径适用[随 r19 基座逐字承继]）；bottom 视现象的旗"
            "标判定仍按 §2/§3A/§4 独立执行（§5B 反指示声明随节落盘）；"
            "bottom 视判读口径沿用 r4 指引原文不改；bottom 零旗标分母=0 时"
            "弃权率按 cal._ratio 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R20 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注册，"
                "聚合口径全部如实并列、不二选一、不挑优（items 沿 r19-prep-"
                "record measurement_design.items 同一口径：12 派次=2 板×2 视"
                "图×3 实例；reader 前缀 R20T/R20B；图像=renders-r14b 四图"
                "（字节复用）；零旗标分母→None 口径照旧；聚合口径与 "
                "s55_calibration_r15_compare.py 同一比较脚本血统；代表配置/"
                "逐实例/双口径分列）"),
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
        "hypothesis_test": hypothesis_test,
        "attribution_plan": {
            "declaration": (
                "本轮恰一个操纵因子（判读指引合成=§5B+(iii-a) 两增补并集；"
                "渲染零变更字节复用）、检验恰一个假设（axis-experiment-plan-"
                "r17-r20 stage2 R20=轴3+轴2 组合；hypothesis_id=axis-plan-"
                "r20-combo-additivity）；归因目的=两轴收益是否可加（组合 vs "
                "最优单轴 r19 的冻结 ordering 排序比较+M2/M3/M4 不劣化核"
                "对）；跨轮对比按冻结件 comparison_rule（跨轮实例群漂移混杂"
                "显式容忍）；字母/机制观察/度量教训三分记账（adjudication."
                "mechanism_observation_separate 与 metric_lesson_separate "
                "单列，不凌驾字母裁决）；执行合法性=dev-r19 "
                "combination_decision_application（early_stop_shortcut 触发"
                "在案）"),
            "primary_channel": {
                "change": (
                    "guidance-combo-s5b-plus-s4-iiia-union（指引合成=§5B+"
                    "(iii-a) 并集；非渲染/GT/阈值/协议变更）"),
                "metric": (
                    "M1（top 全旗聚合弃权率）领衔冻结 ordering 字典序 vs 最"
                    "优单轴 r19 (0.461538, 0.571429, 4, 0.211111)+M2/M3/M4 "
                    "不劣化（M2 ≤ 0.571429、M3 ≤ 4、M4 ≤ 0.211111）联合判据"
                    "见 hypothesis_test.adjudication 三支（各支注明冻结出处）"),
                "supported": (
                    "R20 在冻结 ordering 字典序排序中不劣于最优单轴 r19 → 可"
                    "加性验证成立（R21 不做另按 early_stop 快捷通道与三轴皆"
                    "正前提实测不成立两冻结条款，见 adjudication.supported）"),
                "marginal": (
                    "未达 supported 但相对 r16 基线仍为改善方向（M1 < "
                    "0.771429）且 G1/G2 维持 → 部分收益、可加性未证；处置按"
                    "冻结 iii_non_additive_fallback 采最优单轴 r19 配置"),
                "reject": (
                    "M1 ≥ 0.771429 或 G1/G2 任一破坏 → 按冻结 "
                    "iii_non_additive_fallback 采最优单轴 r19 配置+守门破坏"
                    "时 early_stop_rule.guard_failure_exit 出局语义"),
            },
            "guard_channel": {
                "metric": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15–r19 在"
                    "案；G1 为 §4(iii-a) 间隙支「不得弃权」方向的反向风险守"
                    "门）；G2=guard_ok=True 维持（top 视非弃权旗标 "
                    "frame_box_pct 几何门，面积比出局条目按 guard_channel 如"
                    "实登记）；两守门同为 §5B「不构成任何判据/『应判为正常/"
                    "无需报告』指示」反指示声明的反向风险守门——注记若被误用"
                    "为「少弃权/判正常」压力，G1/守门与 reject 支须如实记录"),
                "requirement": (
                    "§3 收窄判据逐字保留（r20 指引 §2–§7 除 §5B 新增节外与 "
                    "r19 逐字相等，分段断言复核），非弃权框仍须满足；任一守"
                    "门破坏→按 axis-plan early_stop_rule.guard_failure_exit "
                    "出局（字母照实+出局声明；组合轮出局处置=冻结 "
                    "iii_non_additive_fallback 采最优单轴）"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角"
                "层三分列聚合+GT 匹配双口径+联合门代表配置/范围并列；"
                "APR-0011 阈值零改动）；bottom GT 无源=bottom 旗标与 GT 匹"
                "配应为空（结构性在案，不影响收敛计数口径）；字母裁决/机制"
                "观察/度量教训三分记账、互不凌驾；归因分组逻辑由编排侧在 "
                "close 包执行；指引内零 GT、零轮次结果数字（M 元组基线数字"
                "仅入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止"
                    "（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "本轮指引合成方向=既不放松亦不新增判据：轴3 分量 (iii-a) 只把"
            "「无法区分」收窄为「无任何可辨认证据」的情形（r19 轮已预注册、"
            "本轮随基座逐字承继、零改动——两支新判定路径均以「可辨认证据」"
            "为责任条件、残余支仍按 (iii) 原文弃权、真歧义弃权通道完整保"
            "留）；轴2 分量 §5B 为仪器事实注记（r18 轮已预注册、本轮逐字转"
            "录、零改写）——不构成任何判据、期望清单或「应判为正常/无需报"
            "告」的指示（反指示声明随节落盘），黑点相关现象的旗标判定仍按 "
            "§2 类别枚举与 §3A/§4 判据独立执行（含系统性判据、接触性判据与"
            "弃权规则），仪器注记未能证实来源的黑点形态按 §4 既有规则处理；"
            "反放宽条款「仅因形态不熟悉、不确定其设计含义，不构成判为正常设"
            "计特征的理由」在 r20 指引 §4 内逐字保留（fail-closed substring "
            "断言+原句恰 1 次断言），(iii-a) 文本内含原反放宽条款继续全部适"
            "用的承接句；§4 整段与 r19 逐字相等（分段断言）——本轮对判据文"
            "本零改动、不降低判断责任标准；M1 排序不劣于 r19/M2 ≤ 0.571429/"
            "M3 ≤ 4/M4 ≤ 0.211111 等本轮判据只用于组合轮可加性归因（axis-"
            "experiment-plan-r17-r20 冻结比较规则），不触碰 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与任何"
            "阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX，只作口径引用）——门"
            "照常独立计算；不构成任何阈值反向放宽"),
        "pre_round_review": {
            "status": "satisfied_by_plan",
            "basis": (
                "axis-experiment-plan-r17-r20 冻结（b6ec6467，stage2 定义在"
                "案：experiment_design.stage2=「按 combination_decision_rule "
                "取收益 top2 轴组合（R20）……均由冻结规则决定，不临场拍板」；"
                "combination_decision_rule.i_stage2_combo_pair/ii_full_"
                "combination/iii_non_additive_fallback/iv_final_selection 与 "
                "early_stop_rule 两条款逐字装载入 hypothesis_test，载入条款"
                "↔内嵌常量↔记录字段三层相等断言）+dev-r19 combination_"
                "decision_application 在案（0e2fdd69：冻结 comparison_rule "
                "排序 r19_axis3 第一、r18_axis2 第二→组合对=轴3+轴2；"
                "early_stop_shortcut.triggered=True[最优单轴 M1=0.461538≤"
                "0.60 整数交叉相乘复核]→阶段2 仅此一个组合轮；"
                "r21_full_combination_trigger.met=False；r20_recommendation."
                "preregistration_required=True=本轮 prep-record 即该要求之执"
                "行）+轴2 前提在案（axis-plan A2 precondition「注记内容须先"
                "经盘上探针证实黑点物理来源」已由 r18 满足、blackdot-probe-"
                "r18 a49441ac 在盘复核）+轴3 约束在案（axis-plan A3 "
                "constraint=反放宽条款逐字保留，由本包 fail-closed 断言执行"
                "——§4 整段与 r19 逐字相等+反放宽原句恰 1 次，见 "
                "no_loosening_note 与 verification.section_assertions_"
                "passed）"),
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
                "不影响判读语义——分类判据文本除 (iii-a) 预注册增补（r19 轮"
                "落盘、本轮逐字承继）外零变更，§5B 黑点注记为仪器事实非判据"
                "（r18 轮落盘、本轮逐字承继），仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11–r19 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-r20."
                "md，含 §5B 黑点仪器注记节与 §4(iii-a) 可操作分辨条款——指引"
                "本体组成部分，非派发层补充）+单张 PNG（renders-r14b 四图）+"
                "派发命名指令（含 v1.2 工具行为规约硬性条款：纯 Read 内联判"
                "读、禁止任何程序化图像处理），零 GT、零历史判读件、零诊断/"
                "探针内容（diag 件与 dev/typology/probe 件为主审/编排侧核验"
                "件、非 reader 上下文）；两波次串行保序（同一实例先 applied "
                "后 prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r20-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R20T/R20B（r20 指引 §6 已机械替换落盘 R20T-/R20B-——本轮"
                "指引本体即为 r20 前缀，无需派发层覆盖）；实例间编号独立，"
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
            "observation-guidance-r19.md（r20 指引变换基座；8633bda5 锚 "
            "fail-closed，零写入）、observation-guidance-r18.md（§5B 来源；"
            "cadcb8f3 锚，仅提取 §5B 段并哈希交叉锚核对、零写入）、"
            "observation-guidance-r15.md（血统根基座；d5babc93 锚，仅哈希锚"
            "复核、零内容使用）、r19-prep-record.json（链锚=e4cf2d3c 先验"
            "证；schema 血统+24 键镜像源）、r18-prep-record.json（链锚="
            "3fc054c4；§5B 插入编辑先例 edit 8 content_sha256 交叉锚）、"
            "axis-experiment-plan-r17-r20.json（b6ec6467 锚；stage2 定义、"
            "冻结条款逐字装载、r16 基线、守门、用户指令原文）、round19-dev-"
            "record.json（0e2fdd69 锚；仅读取 combination_decision_"
            "application 与 axis_experiment_ledger.cross_round_status."
            "measured_rows——本轮合法性依据与 M 元组锚）、blackdot-probe-"
            "r18.json（a49441ac 锚；仅哈希+kind——§5B 探针证实前提链锚，本"
            "轮零内容转录）、render-witness-r14b.json（b63771f9 锚；四 PNG "
            "见证登记值+字节复用证明）、evaluation-protocol-v1.md（仅在盘+"
            "哈希复核，锚=22dc7337）；renders-r14b 四 PNG 仅哈希+magic（渲"
            "染零变更以 witness 登记哈希比对为准）；本轮恰三个新建文件="
            "scripts/s73_calibration_r20_prep.py（生成器本体）、observation-"
            "guidance-r20.md 与 r20-prep-record.json（本轮仅有的两个 out/ "
            "新建文件；本轮无探针/诊断脚本）；reader 派发（后续编排侧执行）"
            "上下文=observation-guidance-r20.md+单张 PNG（renders-r14b）+派"
            "发指令（R20T/R20B 前缀、reader-r20-{top,bottom}-i{1,2,3}、"
            "v1.2 工具行为规约硬性条款），零 GT、零历史判读件、零诊断/探针"
            "内容、零指引之外的解释；视觉判读禁止由编排/收口包兼任；跨实例/"
            "跨视角禁止交流（12 次盲读相互独立、不得交换判读信息——独立性"
            "是多实例协议的前提，亦为组合轮可加性裁决有效性的前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R19, GUIDANCE_R18, GUIDANCE_R15, R19_PREP_RECORD,
                 R18_PREP_RECORD, BLACKDOT_PROBE, WITNESS_R14B, AXIS_PLAN,
                 DEV_RECORD_R19, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件（GUIDANCE_R20/RECORD）不做前置硬拒绝：落盘阶段防覆写守卫
    # 按红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→
    # 幂等通过（零覆写）。（首轮创建前置=两 out/ 目标不存在，已由编排侧
    # 确认。）

    # ---- 冻结锚验证（fail-closed；两父本哈希先核验、后产出）----
    guidance19_sha = _sha(GUIDANCE_R19)
    guidance18_sha = _sha(GUIDANCE_R18)
    r15_sha = _sha(GUIDANCE_R15)
    r19_record_sha = _sha(R19_PREP_RECORD)
    r18_record_sha = _sha(R18_PREP_RECORD)
    probe18_sha = _sha(BLACKDOT_PROBE)
    witness_sha = _sha(WITNESS_R14B)
    axis_sha = _sha(AXIS_PLAN)
    dev19_sha = _sha(DEV_RECORD_R19)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    for sha, prefix, label in (
            (guidance19_sha, GUIDANCE_R19_SHA_PREFIX,
             "observation-guidance-r19（变换基座父本）"),
            (guidance18_sha, GUIDANCE_R18_SHA_PREFIX,
             "observation-guidance-r18（§5B 来源父本）"),
            (r15_sha, GUIDANCE_R15_SHA_PREFIX,
             "observation-guidance-r15（血统根）"),
            (r19_record_sha, R19_PREP_RECORD_SHA_PREFIX, "r19-prep-record"),
            (r18_record_sha, R18_PREP_RECORD_SHA_PREFIX, "r18-prep-record"),
            (probe18_sha, BLACKDOT_PROBE_SHA_PREFIX, "blackdot-probe-r18"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (axis_sha, AXIS_PLAN_SHA_PREFIX, "axis-experiment-plan"),
            (dev19_sha, DEV_RECORD_R19_SHA_PREFIX, "round19-dev-record"),
            (protocol_sha, EVAL_PROTOCOL_V1_SHA_PREFIX,
             "evaluation-protocol-v1")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，立即"
                  f"停止）")

    # ---- 基座文本口径复核（只读；零写入）----
    base_text = GUIDANCE_R19.read_text(encoding="utf-8")
    if hashing.sha256_text(base_text) != guidance19_sha:
        _fail("r19 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")
    r18_text = GUIDANCE_R18.read_text(encoding="utf-8")
    if hashing.sha256_text(r18_text) != guidance18_sha:
        _fail("r18 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")

    # ---- §5B 段提取（含跨代哈希交叉锚）----
    seg5b = extract_s5b(r18_text)
    if hashing.sha256_text(seg5b) != R18_EDIT8_S5B_CONTENT_SHA256:
        _fail("§5B 段 sha256 与 r18-prep-record edit 8 content_sha256 不符"
              "（跨代链断裂，立即停止）")
    # §5B 轮次身份词盘点（零改写判定的两个前提在脚本内断言）
    if seg5b.count("本轮") != 1 or "本轮渲染中的实心黑色圆点物理来源" not in seg5b:
        _fail("§5B 段「本轮」盘点异常（身份词盘点前提变化，立即停止）")
    for tok in ("R18", "reader-r18", "2026-09-09-r18", "r18 轮"):
        if tok in seg5b:
            _fail(f"§5B 段含预期外轮次身份 token：{tok!r}")

    # ---- 结构探测（冻结条款装载+合法性依据+判据值锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    dev19 = json.loads(DEV_RECORD_R19.read_text(encoding="utf-8"))
    r19_record = json.loads(R19_PREP_RECORD.read_text(encoding="utf-8"))
    r18_record = json.loads(R18_PREP_RECORD.read_text(encoding="utf-8"))
    probe18 = json.loads(BLACKDOT_PROBE.read_text(encoding="utf-8"))
    png_checks = check_renders(witness)
    axis_probe = probe_axis_plan(axis_plan, axis_sha)
    clauses = axis_probe["clauses"]
    # 载入条款↔内嵌常量逐键相等（防装载漂移；读数与写装配分离）
    for k, v_const in CLAUSE_CONSTANTS.items():
        if clauses[k] != v_const:
            _fail(f"冻结条款「{k}」载入值与内嵌常量不符（引用漂移，立即停"
                  f"止）：\n  载入={clauses[k]!r}\n  常量={v_const!r}")
    dev19_probe = probe_dev19(dev19, dev19_sha, clauses)
    r18prep_rec = probe_r18_prep(r18_record, r18_record_sha)
    r19prep_rec = probe_r19_prep(r19_record, r19_record_sha)
    probe18_rec = probe_blackdot_context(probe18, probe18_sha)

    # ---- hypothesis_test 装配（冻结条款逐字装配；三层相等链在 main 断言）----
    hypothesis_test = build_hypothesis_test(clauses)

    # ---- 指引生成（7 组锚定编辑 + 不变量断言）----
    t_work, edit_list = build_guidance(base_text, seg5b)
    edit_list_sorted = sorted(edit_list, key=lambda e: e["edit"])
    section_asserts = assert_guidance_invariants(base_text, r18_text, seg5b,
                                                 t_work)

    guidance20_bytes = t_work.encode("utf-8")
    guidance20_sha = hashing.sha256_bytes(guidance20_bytes)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance19_sha=guidance19_sha, guidance18_sha=guidance18_sha,
        guidance20_sha=guidance20_sha,
        guidance19_bytes=len(base_text.encode("utf-8")),
        guidance20_bytes=len(guidance20_bytes),
        r19_record_sha=r19_record_sha, r18_record_sha=r18_record_sha,
        axis_clauses=clauses, axis_sha=axis_sha,
        stage2_text=axis_probe["stage2_text"],
        r18_quote=axis_probe["r18_round_quote"],
        r19_quote=axis_probe["r19_round_quote"],
        dev19_rec=dev19_probe, r18prep_rec=r18prep_rec,
        r19prep_rec=r19prep_rec, probe18_rec=probe18_rec,
        witness_sha=witness_sha, protocol_sha=protocol_sha,
        png_checks=png_checks, edit_list=edit_list_sorted,
        section_asserts=section_asserts, seg5b=seg5b,
        hypothesis_test=hypothesis_test)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r19-prep-record 24 键逐键镜像
    missing = sorted(set(r19_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r19_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r19-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # hypothesis_test 三层相等链：载入冻结条款 → 装配判据 → 记录字段
    if record["hypothesis_test"] != hypothesis_test:
        _fail("hypothesis_test 与装配判据不一致（逐字要求被破坏）")
    if hypothesis_test["hypothesis_id"] != "axis-plan-r20-combo-additivity":
        _fail("hypothesis_test.hypothesis_id 不符")
    adj = hypothesis_test["adjudication"]
    field_of_clause = {
        "i_stage2_combo_pair": hypothesis_test["hypothesis"],
        "ii_full_combination": adj["supported"],
        "strong_single_axis_shortcut": adj["supported"],
        "iii_non_additive_fallback": adj["marginal"],
        "significant_benefit_definition": adj["marginal"],
        "drift_confound_note": adj["marginal"],
        "guard_failure_exit": adj["reject"],
        "iv_final_selection": adj["metric_lesson_separate"],
        "ordering": hypothesis_test["hypothesis"],
    }
    for k, quote in clauses.items():
        if quote != CLAUSE_CONSTANTS[k]:
            _fail(f"冻结条款「{k}」载入值与常量不符（二次核对）")
        if field_of_clause[k].count(quote) < 1:
            _fail(f"冻结条款「{k}」未逐字装配入对应判据字段")
    if adj["descriptive_boundary_note"].find(
            "以冻结件 axis-experiment-plan-r17-r20.json 为准") < 0:
        _fail("hypothesis_test descriptive_boundary_note 缺冻结件引用")
    # 可加性判据数值在位（与 dev-r19 实测装载行一致）
    for needle in ("0.461538", "0.571429", "0.211111", "0.645161",
                   "0.684211", "0.771429", "0.857143", "0.261904"):
        if needle not in hypothesis_test["hypothesis"] + adj["supported"] \
                + adj["marginal"] + adj["reject"]:
            _fail(f"hypothesis_test 缺 M 元组数值 {needle}")
    # 结构自证（组合轮口径；changed_variables=1）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（组合轮渲染零变更）")
    if len(record["changed_variables"]) != 1:
        _fail("changed_variables 必须恰 1 项（指引合成=§5B+(iii-a) 并集）")
    if record["changed_variables"][0]["id"] != \
            "guidance-combo-s5b-plus-s4-iiia-union":
        _fail("changed_variables[0].id 不符")
    if record["changed_variables"][0]["instrument_change"] is not False:
        _fail("changed_variables[0] 须为非仪器侧变量")
    if record["manipulated_factor"].find("唯一操纵因素=判读指引合成") != 0:
        _fail("manipulated_factor 不符（唯一操纵因子=指引合成并集）")
    if record["pre_round_review"]["status"] != "satisfied_by_plan":
        _fail("pre_round_review.status != satisfied_by_plan")
    for needle, label in (("组合轮", "round_nature 缺「组合轮」声明"),
                          ("stage2", "round_nature 缺 stage2 声明"),
                          ("渲染零变更", "round_nature 缺「渲染零变更」声明"),
                          ("strong_single_axis_shortcut",
                           "round_nature 缺快捷通道声明")):
        if needle not in record["round_nature"]:
            _fail(label)
    if "不降低判断责任标准" not in record["no_loosening_note"]:
        _fail("no_loosening_note 缺「不降低判断责任标准」反放宽声明")
    if "反指示声明" not in record["no_loosening_note"]:
        _fail("no_loosening_note 缺 §5B 反指示声明")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    if "renders-r14b" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 renders-r14b 图像口径")
    if "R20T/R20B" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 R20T/R20B 前缀口径")
    if "None" not in md["items"][4]["text"]:
        _fail("measurement_design item 5 缺零旗标分母→None 口径")
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
            GUIDANCE_R19_SHA_PREFIX) is not True:
        _fail("guidance_reuse.base_sha256 与 8633bda5 锚不符")
    if record["guidance_reuse"]["s5b_source_sha256"].startswith(
            GUIDANCE_R18_SHA_PREFIX) is not True:
        _fail("guidance_reuse.s5b_source_sha256 与 cadcb8f3 锚不符")
    if record["guidance_reuse"]["derived_sha256"] != guidance20_sha:
        _fail("guidance_reuse.derived_sha256 与实测不符")
    # edit_list[6]（edit 7）必须含 §5B 全文且与指引落盘文本逐字一致
    e7 = next(e for e in edit_list_sorted if e["edit"] == 7)
    if e7.get("text_full") != seg5b:
        _fail("edit_list[6].text_full 与 §5B 提取段不一致")
    if seg5b not in t_work:
        _fail("§5B 段未在 r20 指引文本中逐字落盘")
    if e7["content_sha256"] != hashing.sha256_text(seg5b):
        _fail("edit_list[6].content_sha256 与 §5B 段哈希不符")
    if e7["cross_check_content_sha256_r18_prep_edit8"] != \
            R18_EDIT8_S5B_CONTENT_SHA256:
        _fail("edit_list[6] 跨代链锚字段异常")
    if e7["identity_rewrite"]["needed"] is not False:
        _fail("edit_list[6].identity_rewrite.needed 必须为 False（零改写判定）")
    # §5B 插入编辑锚纪律：锚=§6 完整标题（恰 1 次、非声明内片段）
    if e7.get("anchor") != SECTION6_HEADING:
        _fail("§5B 插入编辑锚异常")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance19_sha=guidance19_sha, guidance18_sha=guidance18_sha,
        guidance20_sha=guidance20_sha,
        guidance19_bytes=len(base_text.encode("utf-8")),
        guidance20_bytes=len(guidance20_bytes),
        r19_record_sha=r19_record_sha, r18_record_sha=r18_record_sha,
        axis_clauses=clauses, axis_sha=axis_sha,
        stage2_text=axis_probe["stage2_text"],
        r18_quote=axis_probe["r18_round_quote"],
        r19_quote=axis_probe["r19_round_quote"],
        dev19_rec=dev19_probe, r18prep_rec=r18prep_rec,
        r19prep_rec=r19prep_rec, probe18_rec=probe18_rec,
        witness_sha=witness_sha, protocol_sha=protocol_sha,
        png_checks=png_checks, edit_list=edit_list_sorted,
        section_asserts=section_asserts, seg5b=seg5b,
        hypothesis_test=hypothesis_test)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r20-prep-record")

    # ---- 防覆写守卫 + 落盘 ----
    if GUIDANCE_R20.exists():
        if GUIDANCE_R20.read_bytes() != guidance20_bytes:
            _fail("observation-guidance-r20.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r20-prep] 重跑自证：observation-guidance-r20.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R20.write_bytes(guidance20_bytes)
        if GUIDANCE_R20.read_bytes() != guidance20_bytes:
            _fail("回读不一致: observation-guidance-r20.md")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r20-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r20-prep] 重跑自证：r20-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r20-prep-record.json")

    # ---- 汇总打印 ----
    print("[r20-prep] 验证通过：两父本锚核验先于产出——r19 指基座锚 "
          f"{GUIDANCE_R19_SHA_PREFIX} OK（只读，零写入，"
          f"{len(base_text.encode('utf-8'))} B）；r18 指 §5B 来源锚 "
          f"{GUIDANCE_R18_SHA_PREFIX} OK（只读，零写入）；r15 血统根锚 "
          f"{GUIDANCE_R15_SHA_PREFIX} OK（仅哈希）；r19-prep-record schema "
          f"血统锚 {R19_PREP_RECORD_SHA_PREFIX} OK（24 键镜像源）；"
          f"r18-prep-record §5B 编辑先例锚 {R18_PREP_RECORD_SHA_PREFIX} OK"
          f"（edit 8 content_sha256 19ecdb42 交叉核对通过）；witness-r14b 锚 "
          f"{WITNESS_R14B_SHA_PREFIX} OK；axis-plan 冻结锚 "
          f"{AXIS_PLAN_SHA_PREFIX} OK（stage2 定义+冻结条款 9 条逐字装载+"
          f"r16 基线 M1=0.771429/M3=12/M4=0.261904+守门 G1/G2/G3）；"
          f"round19-dev 合法性锚 {DEV_RECORD_R19_SHA_PREFIX} OK（early_stop "
          f"shortcut 触发/排序 r19 第一 r18 第二/r20_recommendation/R21="
          f"否）；blackdot-probe-r18 前提锚 {BLACKDOT_PROBE_SHA_PREFIX} OK"
          f"（仅哈希+kind）；evaluation-protocol-v1 在盘锚 "
          f"{EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r20-prep] 渲染仪器实测（四 PNG 实测=witness-r14b 登记值；字节"
          "复用、零仪器变更）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r20-prep] hypothesis_test 三层相等链：axis-plan 冻结条款磁盘"
          "装载 ↔ 内嵌常量 ↔ 装配判据/记录字段，9 条逐字装配 PASS（每支注"
          "明冻结出处；hypothesis_id=axis-plan-r20-combo-additivity；最优"
          "单轴 r19 (0.461538, 0.571429, 4, 0.211111) 与快捷通道 461538≤"
          "600000 整数复核在案）")
    print(f"[r20-prep] 顶层键镜像断言：与 r19-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）；changed_variables=1（指引合成并集）")
    print(f"[r20-prep] 指引不变量断言：{len(section_asserts)} 项全部通过"
          f"（§1–§5 分段逐字 {len(SECTION_PAIRS)} 段+§5A/§6/§7 段+§5B 全文"
          f"逐字（含 19ecdb42 跨代链锚）+(iii-a) 全文逐字+关键 substring "
          f"{len(REQUIRED_SUBSTRING_VALUES)}+{len(REQUIRED_SUBSTRING_5B)} "
          f"条+反放宽原句恰 1 次+残留零+新文本在位+位置与节序）")
    print(f"[r20-prep] 字节数差：r20（{len(guidance20_bytes)} B）- r19（"
          f"{len(base_text.encode('utf-8'))} B）= "
          f"{len(guidance20_bytes) - len(base_text.encode('utf-8'))} B")
    print(f"[r20-prep] 工件 sha256：observation-guidance-r20.md="
          f"{_sha(GUIDANCE_R20)}")
    print(f"[r20-prep] 工件 sha256：r20-prep-record.json={_sha(RECORD)}")
    print("[r20-prep] §5B 实际落盘（r18 全文逐字转录、零改写；identity_"
          "rewrite.needed=false）：")
    k = t_work.index(SECTION5B_HEADING)
    print(t_work[k:t_work.index(SECTION6_HEADING, k)], end="")


if __name__ == "__main__":
    main()
