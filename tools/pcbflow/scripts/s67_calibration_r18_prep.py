#!/usr/bin/env python
"""CAL-R18-PREP：R18 轴2 指引侧单变量轮（黑点中性仪器注记；渲染零变更）
预备包（只新建两个文件：out/v3-tl2/calibration/observation-guidance-
r18.md 与 out/v3-tl2/calibration/r18-prep-record.json；datasets/ 与 out/
既有文件只读、零改动，observation-guidance-r15.md 零字节不动）。

R18 轮性质（预注册，非事后）：**轴2 指引侧单变量轮（黑点中性仪器注
记；axis-experiment-plan-r17-r20 stage1 之一）**——渲染零变更=
renders-r14b 四图字节复用（四 PNG 实测=witness-r14b 登记值）；本轮唯
一判读变更=指引增补 §5B 黑点仪器注记节（黑点物理来源；仪器事实非判
据），其内容=探针证实事实的中性转录（s66_blackdot_probe_r18.py →
blackdot-probe-r18.json，fail-closed 装载）：(a) 孤立实心黑点对=封装
内 2 个非电镀机械定位孔（np_thru_hole，孔径=焊盘尺寸=0.65mm、无铜环）
的渲染表现（证书点 fiducial_disk_black 0.64px 匹配）；(b) 焊盘中心圆
盘=电镀通孔焊盘钻孔渲染（162 圆钻孔+4 椭圆槽孔=framing 白墨图元计数
恒等；r14b bottom 呈橙色，非黑色墨点）；(c) 板内孤立焊盘对=CRTC 两
电镀焊盘、其邻域无黑点图元来源（黑点存在性 indeterminate 如实登记，
注记按任务口径写中性表述、不替读者下正常结论）。判据零改动（§2–§7
逐字承 r15，§5A 原文逐字保留）。执行 axis-experiment-plan-r17-r20
（b6ec6467 冻结件）stage1 R18=轴2（A2_blackdot_instrument_annotation，
其 guidance 原文规定「注记内容须先经盘上探针证实黑点物理来源（仪器
事实非判据），无探针证实则该轴不得入轮」——本包开工前探针已证实，
见 pre_round_review），用户 2026-09-09「三条轴单独/组合/全组合尝试，
选择收益最大的继续」。

指引生成=确定性机械变换（锚串命中数 fail-closed，锚恰 1 次否则 FAIL）。
任务枚举编辑：(1) 标题/round_id_constant R15→R18（含声明日期 bullet
2026-09-08→2026-09-09、本轮性质行按轴2 口径重写、示例 reader_id
reader-r15→reader-r17 血统同款→reader-r18、示例旗 ID 前缀 R15T-（4 处）/
R15B-（1 处）→R18T-/R18B-）；(2) 「本轮变更声明」节正文整体替换（任
务给定文本逐字）；(3) §6 标题前插入 §5B 黑点仪器注记节（探针文本逐字
转录）。另沿 s48/s54（r12→r13、r13→r15 指引侧轮）机械变换先例同步轮
次标识区（如实登记）——§1 与头部 bullet 区不在逐字冻结清单（冻结区=
§2–§7，含 §5A 原文逐字保留）。

功能：
  1. fail-closed 复核 observation-guidance-r15.md（d5babc93 锚；r18
     指引唯一变换基座，只读零写入）。
  2. fail-closed 复核 r15-prep-record.json（4c6cd919 锚；schema 模板）
     与 r16-prep-record.json（46fbd15b 锚；24 键结构镜像源）。
  3. fail-closed 复核 blackdot-probe-r18.json（a49441ac 锚、kind、
     round_id_constant、overall_status、F1/F2=confirmed、F3=
     identity_confirmed_blackdot_indeterminate）：§5B 文本唯一转录源。
  4. fail-closed 复核 render-witness-r14b.json（b63771f9 锚）+四 PNG
     实测（bottom 两板同 d7284259、top 298bc620/b2f84524）——渲染零
     变更字节复用证明。
  5. fail-closed 复核 axis-experiment-plan-r17-r20.json（b6ec6467 锚）：
     stage1 R18=轴2 定义、r16 基线（M1=0.771429、M3=12）、r15 带上缘
     M1=0.862069、守门 G1/G2、用户指令原文。
  6. fail-closed 复核 round17-dev-record.json（e526093f 锚）：
     next_iteration_targets[0] 探针先决条款。
  7. fail-closed 复核 calibration-run-r16.json（2c1f8265 锚；M1 冻结值
     +guard_ok）与 round16-dev-record.json（589fe62f 锚；G1 基线
     0/0/0 在案）；abstain-typology-r13-r16.json（6dadac8d 锚；黑点族
     r13-r16 计数 9/14/8/12 与判正常派次 r15=3/r16=2——预注册判据基
     线锚，探针已复核、本包复核）。
  8. evaluation-protocol-v1.md 在盘且锚=22dc7337。
  9. 生成 observation-guidance-r18.md（8 组锚定编辑，命中数逐一断言；
     §1/§2–§5/§5A/§6/§7 分段逐字保留断言+关键 substring 断言+R15 残
     留零断言+新文本在位断言+§5A 原文逐字保留断言+§5B 位置断言）。
 10. 落盘 r18-prep-record.json（canonical JSON；顶层键集合与 r16-prep-
     record 24 键逐键镜像；hypothesis_test=任务预注册判据逐字（文本→
     json.loads→常量→记录字段三层相等）；同参重建两次逐字节一致自证；
     防覆写守卫；落盘后回读验字节）。
 11. 打印：两文件 sha256、r18 相对 r15 字节数差、§5B 节实际落盘全文、
     四 PNG 比对结果、逐项断言通过清单。

判据数值自洽断言：M3_supported 阈值 6=r16 基线 12 的一半（任务判据文
本原文）；0.85 < 0.862=r15 M1（axis-plan r15_reference 实测）——任务
判据文本数值与在案锚逐一相符（不符即停——防预注册文本与在案事实漂移）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-09/2026-09-09-r18）；
无 subprocess/网络/主机绝对路径；hash=sha256_file 字节口径（PNG 仅哈希
+magic，零内容判读、零像素读取）；不读 GT/ground-truth-*/reader-raw-*/
derivation-log-*/任何 compare/诊断内容产物；run-r16 仅读 hypothesis_test
顶层判据值字段做冻结值锚；无 git；r15 指引只读；记录内零 GT、零期望数
量/分布/坐标（§5B 内 162/4/0.65/2 为仪器侧图元计数与板卡源文件事实转
录、非期望清单）；指引内零轮次结果数字（基线数字仅入本编排侧记录）。

用法：python scripts/s67_calibration_r18_prep.py
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
GUIDANCE_R18 = CAL_DIR / "observation-guidance-r18.md"
R15_PREP_RECORD = CAL_DIR / "r15-prep-record.json"
R16_PREP_RECORD = CAL_DIR / "r16-prep-record.json"
BLACKDOT_PROBE = CAL_DIR / "blackdot-probe-r18.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
DEV_RECORD_R17 = CAL_DIR / "round17-dev-record.json"
RUN_R16 = CAL_DIR / "calibration-run-r16.json"
ROUND16_DEV_RECORD = CAL_DIR / "round16-dev-record.json"
TYPOLOGY = CAL_DIR / "abstain-typology-r13-r16.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r18-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r18"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R15_SHA_PREFIX = "d5babc93"
R15_PREP_RECORD_SHA_PREFIX = "4c6cd919"
R16_PREP_RECORD_SHA_PREFIX = "46fbd15b"
BLACKDOT_PROBE_SHA_PREFIX = "a49441ac"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
DEV_RECORD_R17_SHA_PREFIX = "e526093f"
RUN_R16_SHA_PREFIX = "2c1f8265"
ROUND16_DEV_RECORD_SHA_PREFIX = "589fe62f"
TYPOLOGY_SHA_PREFIX = "6dadac8d"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

RENDERS_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

#: 判据冻结值锚（r16 基线与带上缘；axis-plan/run-r16/typology 实测）
M3_R16_BASELINE = 12
M3_SUPPORTED_THRESHOLD = 6
BLACKDOT_ABSTAIN_BASELINE = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
BLACKDOT_JUDGED_NORMAL_BASELINE = {"r15": 3, "r16": 2}
M1_BAND_UPPER_R15 = 0.862069
M1_SUPPORTED_THRESHOLD = 0.85

# ---------------------------------------------------------------------------
# 预注册判据（逐字，先于任何盲读冻结；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "axis-plan-r18-blackdot-note",
  "hypothesis": "黑点族弃权（连续 4 轮主导，bottom 81.4%）的主因=黑点物理性质不明导致的存在性弃权。§5B 中性仪器注记（探针证实来源）使读者能按既有判据负责任判定黑点相关现象，黑点族弃权显著回落，且不引起其他族弃权上升。",
  "adjudication": {
    "supported": "M3（黑点族弃权旗数，分型件 rubric 口径）≤ 6（r16 基线 12 的一半）且 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）维持且 M1（top 全旗聚合弃权率）≤ 0.85（不劣于 r15/r16 带上缘 0.862 的漂移容差内）",
    "marginal": "M3 在 7–9 之间（回落未过半）或 M1 在 0.85–0.862——记录为部分收益",
    "reject": "M3 ≥ 10（注记未使黑点族回落）或 G1/G2 任一破坏（按 axis-plan early_stop 出局）",
    "mechanism_observation_separate": "黑点旗逐条理由对照注记援引情况（是否引用 §5B）；黑点判正常派次计数（对照 r15=3/r16=2）；M1/M2/M4 照常入实验对照账（(M1,M2,M3,M4) 四元组入 dev-record）；top 弃权分型照常",
    "metric_lesson_separate": "跨轮实例群漂移混杂照旧；字母=预注册阈值命中与否的描述性结论",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

# ---------------------------------------------------------------------------
# 指引机械变换锚与替换文本
# ---------------------------------------------------------------------------
OLD_TITLE = "# R15 轮 reader 判读指引（observation-guidance-r15）"
NEW_TITLE = "# R18 轮 reader 判读指引（observation-guidance-r18）"
DECL_HEADING = "## 本轮变更声明（预注册，非事后）"
SECTION1_HEADING = "## 1. 角色与任务"
OLD_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-08"
NEW_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-09"
OLD_ROUND_ID_BULLET = "- round_id_constant: `2026-09-08-r15`"
NEW_ROUND_ID_BULLET = "- round_id_constant: `2026-09-09-r18`"
OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（bottom 配色语义仪器注记配套"
    "轮）**。渲染零变更（复用 R14 冻结渲染件 renders-r14b）；本轮唯一"
    "变更=判读指引增补 §5A 渲染配色仪器注记节（颜色→来源映射显式化；"
    "预注册见下），指引落盘后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（轴2 黑点中性仪器注记轮；axis-"
    "experiment-plan-r17-r20 stage1 之一）**。渲染零变更（复用 R14/R15/"
    "R16 同一冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引"
    "增补 §5B 黑点仪器注记节（黑点物理来源；仪器事实非判据，内容先经盘"
    "上探针证实），指引落盘后由编排侧重新盲读。")

#: 任务枚举编辑：「本轮变更声明」节正文整体替换（逐字，任务给定文本）
NEW_DECLARATION = (
    "本轮（R18）为轴2 指引侧单变量轮：相对 observation-guidance-r15 仅"
    "（1）更新标题与轮次标识，（2）重写本变更声明，（3）新增 §5B 黑点仪"
    "器注记节（黑点物理来源；仪器事实非判据，内容先经盘上探针证实），"
    "（4）虚构示例旗 ID 前缀改为 R18T/R18B。渲染零变更：本轮使用与 R14/"
    "R15/R16 完全相同的 renders-r14b 四图（字节复用）。§2 类别枚举、§3/"
    "§3A 位置与判据示例、§4 置信度与弃权（含量化判据 (i)(ii)(iii) 与接"
    "触性判据）、§5 courtyard 说明、§5A 渲染配色仪器注记（原文逐字保留）"
    "、§6 输出格式、§7 格式对齐提示全部逐字不变。预注册判据见 r18-prep-"
    "record.json hypothesis_test（先于任何盲读冻结）。")

SECTION_6_HEADING = "## 6. 输出格式（reader-raw 文件的确切 schema）"

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
    "section6_heading": 1,
}

#: §1/§2–§5/§5A/§6/§7 分段逐字保留断言（§5A 段=「## 5A.」标题→「## 6.」
#: 标题的原文整体；§5B 插入点在其后，不破坏该段连续性；§6/§7 段先做旗
#: 前缀/reader-id 规格化再断言）
SECTION_PAIRS = [
    ("## 1. 角色与任务", "## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）"),
    ("## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）", "## 3. 位置口径"),
    ("## 3. 位置口径", "## 3A. 类别判据示例（判据说明，非期望清单）"),
    ("## 3A. 类别判据示例（判据说明，非期望清单）", "## 4. 置信度与弃权"),
    ("## 4. 置信度与弃权", "## 5. courtyard 说明（中性）"),
    ("## 5. courtyard 说明（中性）",
     "## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）"),
    ("## 6. 输出格式（reader-raw 文件的确切 schema）",
     "## 7. 格式对齐提示"),
    ("## 7. 格式对齐提示", None),  # 至文件尾
]

#: 关键 substring 断言（判据零放宽+§5A 原文逐字+§5B 在位；逐条打印通过）
REQUIRED_SUBSTRING_VALUES = {
    "§2 类别封闭集：1. `silk_readability`": "1. `silk_readability`",
    "§2 类别封闭集末类：6. `other_advisory`": "6. `other_advisory`",
    "§3 收窄判据：邻域框收窄判据": "邻域框收窄判据",
    "§3A 示例 c：**「整段规则周期」判据**": "**「整段规则周期」判据**",
    "§4 总原则：**宁可 abstain 不硬标**": "**宁可 abstain 不硬标**",
    "§4 量化判据 (i)：(i) **系统性正常特征判据（量化）**":
        "(i) **系统性正常特征判据（量化）**",
    "§4 量化判据 (ii)：(ii) **关注现象判据**": "(ii) **关注现象判据**",
    "§4 接触性判据 (iii)：(iii) **接触性判据（判「交叠/接触」类现象前适用）**":
        "(iii) **接触性判据（判「交叠/接触」类现象前适用）**",
    "§4 反放宽条款：仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由":
        "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由",
    "§4 三路出口：**三路出口显式化（判为正常设计特征的形态不报告）**":
        "**三路出口显式化（判为正常设计特征的形态不报告）**",
    "§4 同等判断责任：判「正常设计特征」与判「关注现象」承担**同等判断责任**":
        "判「正常设计特征」与判「关注现象」承担**同等判断责任**",
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
    # ---- §5B 在位（新增节关键语）----
    "§5B 节标题：## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）":
        "## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）",
    "§5B 探针证实话：物理来源（探针证实": "物理来源（探针证实",
    "§5B 非判据声明：不构成任何判据、期望清单或「应判为正常/无需报告」的指示":
        "不构成任何判据、期望清单或「应判为正常/无需报告」的指示",
    "§5B 判定独立性：旗标判定仍按 §2 类别枚举与 §3A/§4 判据独立执行":
        "旗标判定仍按 §2 类别枚举与 §3A/§4 判据独立执行",
    "§5B 未证实形态：仪器注记未能证实来源的黑点形态，按 §4 既有规则处理":
        "仪器注记未能证实来源的黑点形态，按 §4 既有规则处理",
    "§5B top 适用句：top 视黑点同样适用": "top 视黑点同样适用",
}


def _fail(msg: str) -> None:
    print(f"[r18-prep] FAIL: {msg}")
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
            .replace("R15T-", "R18T-")
            .replace("R15B-", "R18B-")
            .replace("reader-r15", "reader-r18"))


# ---------------------------------------------------------------------------
# 指引生成（确定性机械变换；锚命中数逐一 fail-closed，锚恰 1 次否则 FAIL）
# ---------------------------------------------------------------------------

def build_guidance(base_text: str, section_5b: str
                   ) -> tuple[str, list[dict]]:
    """由 r15 指引文本生成 r18 指引文本；返回 (r18 文本, edit_list)。"""
    t = base_text
    edits: list[dict] = []

    # ---- 编辑 1（先行）：本轮变更声明节正文整体替换（任务枚举）----
    # 先行原因：声明正文含 r15 自引（r15-prep-record.json / R15T/R15B /
    # 本轮（R15）），整体替换后轮次标识与旗前缀替换的命中数才收敛为期望值。
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

    # ---- 编辑 3：声明日期 bullet 同步（轮次标识区；s48/s54 先例延伸）----
    t = _replace_counted(t, OLD_DATE_LINE, NEW_DATE_LINE,
                         EXPECTED_HITS["date_line"], "声明日期 bullet")
    edits.append({
        "edit": 3,
        "kind": "声明日期 bullet 同步（轮次标识区；s48/s54 机械变换先例；"
                "非任务枚举、如实披露——r13→r15 时日期未变故先例无此项）",
        "old": OLD_DATE_LINE,
        "new": NEW_DATE_LINE,
        "expected_hits": EXPECTED_HITS["date_line"],
    })

    # ---- 编辑 4：round_id_constant bullet 同步（轮次标识区）----
    t = _replace_counted(t, OLD_ROUND_ID_BULLET, NEW_ROUND_ID_BULLET,
                         EXPECTED_HITS["round_id_bullet"], "round_id bullet")
    edits.append({
        "edit": 4,
        "kind": "round_id_constant bullet 同步（轮次标识区；s48/s54 先例）",
        "old": OLD_ROUND_ID_BULLET,
        "new": NEW_ROUND_ID_BULLET,
        "expected_hits": EXPECTED_HITS["round_id_bullet"],
    })

    # ---- 编辑 5：本轮性质行重写（轮次标识区；s48/s54 先例）----
    t = _replace_counted(t, OLD_NATURE_LINE, NEW_NATURE_LINE,
                         EXPECTED_HITS["nature_line"], "本轮性质行")
    edits.append({
        "edit": 5,
        "kind": "本轮性质行重写（轮次标识区；s48/s54 机械变换先例；非任务"
                "枚举、如实披露）",
        "old": OLD_NATURE_LINE,
        "new": NEW_NATURE_LINE,
        "expected_hits": EXPECTED_HITS["nature_line"],
    })

    # ---- 编辑 6：示例 reader-id 同步（轮次标识区；s48/s54 先例）----
    t = _replace_counted(t, "reader-r15", "reader-r18",
                         EXPECTED_HITS["reader_id"], "示例 reader-id")
    edits.append({
        "edit": 6,
        "kind": "示例 reader-id 同步（轮次标识区；s48/s54 机械变换先例）",
        "old": "reader-r15",
        "new": "reader-r18",
        "expected_hits": EXPECTED_HITS["reader_id"],
        "note": "§6 格式示例 reader_id：reader-r18-top",
    })

    # ---- 编辑 7：示例旗 ID 前缀替换（任务枚举）----
    t = _replace_counted(t, "R15T-", "R18T-",
                         EXPECTED_HITS["prefix_R15T-"], "旗前缀 R15T-")
    t = _replace_counted(t, "R15B-", "R18B-",
                         EXPECTED_HITS["prefix_R15B-"], "旗前缀 R15B-")
    edits.append({
        "edit": 7,
        "kind": "示例旗 ID 前缀替换（任务枚举）",
        "items": [
            {"old": "R15T-", "new": "R18T-",
             "expected_hits": EXPECTED_HITS["prefix_R15T-"]},
            {"old": "R15B-", "new": "R18B-",
             "expected_hits": EXPECTED_HITS["prefix_R15B-"]},
        ],
    })

    # ---- 编辑 8：§6 标题前插入 §5B 黑点仪器注记节（任务枚举；文本=
    #      探针 blackdot-probe-r18.json section_5b_text 逐字转录）----
    t = _replace_counted(t, SECTION_6_HEADING, section_5b + SECTION_6_HEADING,
                         EXPECTED_HITS["section6_heading"], "§6 标题（§5B 插入点）")
    edits.append({
        "edit": 8,
        "kind": "「## 6. 输出格式」标题前插入 §5B 黑点仪器注记节（任务枚举；"
                "文本=blackdot-probe-r18.json section_5b_text 逐字转录，探针"
                "证实事实的中性转录、非判据）",
        "anchor": "## 6. 输出格式",
        "content_sha256": hashing.sha256_text(section_5b),
        "expected_hits": EXPECTED_HITS["section6_heading"],
    })

    return t, edits


def assert_guidance_invariants(base_text: str, t18: str,
                               section_5b: str) -> list[str]:
    """§1/§2–§5/§5A/§6/§7 分段逐字保留断言 + §5A 原文整体逐字断言 + 关键
    substring 断言 + R15 残留零断言 + 新文本在位断言 + §5B 位置断言。

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
        if norm not in t18:
            _fail(f"{label} 失败：r15 段落（旗前缀规格化后）未在 r18 中逐"
                  f"字保留（立即停止）")
        passed.append(label)

    # ---- §5A 原文整体逐字断言（r15 §5A 段 = §5A 标题→§6 标题，原样为
    #      r18 子串；§5B 插入点在其后、不破坏该段）----
    i5a = base_text.index("## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）")
    i6 = base_text.index(SECTION_6_HEADING)
    seg5a = base_text[i5a:i6]
    if seg5a not in t18:
        _fail("§5A 原文整体逐字断言失败：r15 指引 §5A 段未在 r18 中逐字保"
              "留（立即停止）")
    passed.append("§5A 原文整体逐字保留（r15 §5A 段 substring-in 断言；本轮"
                  "零改动）")

    # ---- §5B 文本逐字在位（探针转录完整性）----
    if section_5b not in t18:
        _fail("§5B 文本逐字在位断言失败：探针 section_5b_text 未逐字落盘")
    passed.append("§5B 文本逐字在位（=blackdot-probe-r18.json "
                  "section_5b_text 逐字）")

    # ---- 关键 substring 断言 ----
    for label, needle in REQUIRED_SUBSTRING_VALUES.items():
        if needle not in t18:
            _fail(f"关键 substring 断言失败（{label}）：{needle!r} 未在 r18 "
                  f"指引中逐字保留（立即停止）")
        passed.append(label)

    # ---- R15 残留零断言（机械替换完备性；声明内 lineage 基座引用
    #      observation-guidance-r15 有意保留恰 1 次、不在零断言之列）----
    for needle in ("R15T", "R15B", "reader-r15", "2026-09-08-r15",
                   "2026-09-08", "# R15 轮", "本轮（R15）",
                   "R15）为指引侧单变量轮", "r15-prep-record.json"):
        n = t18.count(needle)
        if n != 0:
            _fail(f"残留零断言失败：{needle!r} 在 r18 指引中残留 {n} 次"
                  f"（立即停止）")
    passed.append("R15 残留零断言（R15T/R15B/reader-r15/2026-09-08-r15/"
                  "2026-09-08/# R15 轮/本轮（R15）/R15）为指引侧单变量轮/"
                  "r15-prep-record.json 全部零命中；声明内 lineage 基座引用 "
                  "observation-guidance-r15 有意保留恰 1 次、单列断言）")
    n = t18.count("observation-guidance-r15")
    if n != 1:
        _fail(f"lineage 基座引用断言失败：observation-guidance-r15 命中 {n} "
              f"次 != 1（应为声明内基座引用恰 1 次）")
    passed.append("lineage 基座引用恰 1 次（observation-guidance-r15，声明内"
                  " derivation 基座自引）")

    # ---- 新文本在位断言 ----
    for needle, label, want in (
            (NEW_TITLE, "r18 标题在位", 1),
            (NEW_DECLARATION, "r18 变更声明在位", 1),
            (NEW_NATURE_LINE, "r18 本轮性质行在位", 1),
            ("`2026-09-09-r18`", "r18 round_id_constant bullet 在位", 1),
            (NEW_DATE_LINE, "r18 声明日期 bullet 在位", 1),
            ("R18T-", "r18 旗前缀 R18T- 在位", 4),
            ("R18B-", "r18 旗前缀 R18B- 在位", 1),
            ("reader-r18", "r18 示例 reader-id 在位", 1),
            ("2026-09-09", "r18 日期常量在位（声明日期+round_id 两处）", 2),
            ("r18-prep-record.json", "r18 预注册件引用在位（声明内）", 1),
            ("## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）",
             "§5B 节标题在位", 1),
            ("blackdot-probe-r18.json", "§5B 探针件引用在位", 1),
            ("np_thru_hole", "§5B F2 结论在位（np_thru_hole）", 1),
            ("renders-r14b", "渲染零变更声明在位（性质行+变更声明）", 2),
    ):
        n = t18.count(needle)
        if n != want:
            _fail(f"新文本在位断言失败（{label}）：命中 {n} 次 != {want}")
        passed.append(f"{label}（命中 {n}/{want}）")

    # ---- §5B 位置断言（§5A 之后、§6 之前）----
    j5 = t18.index("## 5. courtyard 说明（中性）")
    j5a = t18.index("## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）")
    j5b = t18.index("## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）")
    j6 = t18.index("## 6. 输出格式")
    if not (j5 < j5a < j5b < j6):
        _fail("§5B 位置断言失败：须位于 §5A 之后、§6 之前")
    passed.append("§5B 位置断言（§5 < §5A < §5B < §6）")
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
    for side in RENDERS_SIDES:
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


def probe_blackdot(probe: dict, probe_sha: str) -> dict:
    """blackdot-probe-r18：探针结论与 §5B 转录源（fail-closed）。"""
    if probe.get("kind") != "tl2_blackdot_probe_r18":
        _fail("blackdot-probe-r18 kind 不符")
    if probe.get("round_id_constant") != ROUND_ID:
        _fail(f"blackdot-probe round_id_constant 不符："
              f"{probe.get('round_id_constant')}")
    if probe.get("declared_date") != DATE_CONSTANT:
        _fail("blackdot-probe declared_date != 2026-09-09")
    if "F1/F2 confirmed" not in probe.get("overall_status", ""):
        _fail(f"blackdot-probe overall_status 不符：{probe.get('overall_status')}")
    fams = {f["form_id"]: f for f in probe.get("families", [])}
    for fid in ("F1_pad_interior_disc", "F2_isolated_black_dot_pair",
                "F3_isolated_pad_pair"):
        if fid not in fams:
            _fail(f"blackdot-probe 缺探针族：{fid}")
    if fams["F1_pad_interior_disc"].get("status") != "confirmed":
        _fail("F1 status != confirmed（§5B (b) 项不可落盘）")
    if fams["F2_isolated_black_dot_pair"].get("status") != "confirmed":
        _fail("F2 status != confirmed（§5B (a) 项不可落盘）")
    if fams["F3_isolated_pad_pair"].get("status") != \
            "identity_confirmed_blackdot_indeterminate":
        _fail("F3 status != identity_confirmed_blackdot_indeterminate")
    cm = fams["F2_isolated_black_dot_pair"].get("certificate_match", {})
    if cm.get("delta_px", 999) > cm.get("tolerance_px", 0):
        _fail("F2 证书点匹配超差（黑点定位不可靠）")
    if fams["F2_isolated_black_dot_pair"].get("count") != 2:
        _fail("F2 count != 2")
    section = probe.get("section_5b_text", "")
    for needle in ("## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）",
                   "探针证实", "不构成任何判据、期望清单",
                   "按 §4 既有规则处理", "top 视黑点同样适用",
                   "np_thru_hole"):
        if needle not in section:
            _fail(f"probe section_5b_text 缺关键语：{needle!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/blackdot-probe-r18.json",
        "sha256": probe_sha,
        "overall_status": probe["overall_status"],
        "f2_certificate_delta_px": cm.get("delta_px"),
    }


def probe_axis_plan(plan: dict, plan_sha: str) -> dict:
    """axis-experiment-plan-r17-r20：stage1 R18 定义与判据数值锚。"""
    if plan.get("kind") != "tl2_axis_experiment_plan_development":
        _fail("axis-plan kind 不符")
    if plan.get("declared_date") != DATE_CONSTANT:
        _fail("axis-plan declared_date != 2026-09-09")
    rounds = plan.get("stage1_rounds", {}).get("rounds", [])
    r18 = next((r for r in rounds if r.get("round_id") == "R18"), None)
    if r18 is None or r18.get("axis_id") != "A2_blackdot_instrument_annotation":
        _fail("axis-plan stage1 R18=A2_blackdot_instrument_annotation 不符")
    if "探针证实" not in (r18.get("guidance") or ""):
        _fail("axis-plan R18 guidance 缺「探针证实」先决条款")
    if r18.get("render") != "renders-r14b 四图字节复用（零变更）":
        _fail("axis-plan R18 render 定义不符")
    if "渲染零变更" not in (r18.get("round_nature") or ""):
        _fail("axis-plan R18 round_nature 缺「渲染零变更」")
    bases = plan.get("baselines_registered", {})
    r16b = bases.get("r16_baseline", {})
    if r16b.get("M1_top_aggregate_abstain_rate") != 0.771429:
        _fail(f"axis-plan r16 基线 M1 不符："
              f"{r16b.get('M1_top_aggregate_abstain_rate')}")
    if r16b.get("M3_blackdot_abstain_flags_rubric") != M3_R16_BASELINE:
        _fail(f"axis-plan r16 基线 M3 不符："
              f"{r16b.get('M3_blackdot_abstain_flags_rubric')} != "
              f"{M3_R16_BASELINE}")
    r15b = bases.get("r15_reference", {})
    if r15b.get("M1_top_aggregate_abstain_rate") != M1_BAND_UPPER_R15:
        _fail(f"axis-plan r15 参照 M1（带上缘 0.862）不符："
              f"{r15b.get('M1_top_aggregate_abstain_rate')}")
    guards = plan.get("guards", {})
    for gid in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                "G3_freeze_discipline"):
        if gid not in guards:
            _fail(f"axis-plan 守门缺失：{gid}")
    quote = (plan.get("user_directive_note", {}) or {}).get("user_quote")
    if quote != "三条轴单独/组合/全组合尝试，选择收益最大的继续":
        _fail(f"axis-plan 用户指令原文不符：{quote!r}")
    # 判据数值自洽：supported M3 阈值 6 = r16 基线 12 的一半；0.85 < 0.862
    if M3_SUPPORTED_THRESHOLD != M3_R16_BASELINE // 2:
        _fail("判据数值自洽断言失败：6 != 12/2")
    if not (M1_SUPPORTED_THRESHOLD < M1_BAND_UPPER_R15):
        _fail("判据数值自洽断言失败：0.85 >= 0.862069")
    for needle in ("≤ 6", "r16 基线 12 的一半", "0.85", "0.862", "r15=3/r16=2"):
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值 {needle}（逐字要求破坏）")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": plan_sha,
        "field": "stage1_rounds.rounds[R18]",
        "round_quote": r18,
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


def probe_dev_records(dev16: dict, dev16_sha: str) -> dict:
    """round16-dev-record：G1 基线 0/0/0 在案（判据 G1 的在案锚）。"""
    m = (dev16.get("hypothesis_test_i", {}) or {}).get("measurement", {})
    g1 = (m.get("bottom_side_observation", {}) or {}).get(
        "bottom_courtyard_non_abstain_by_instance_r16")
    if g1 is None:
        g1 = ((dev16.get("hypothesis_test_i", {}).get("mechanism_observation",
                                                      {}) or {})
              .get("bottom_side_observation_maintenance", {})
              .get("counts", {})
              .get("r16_bottom_courtyard_non_abstain_by_instance"))
    if g1 != {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail(f"round16-dev-record G1 基线证据不符：{g1}")
    return {
        "path_rel": "out/v3-tl2/calibration/round16-dev-record.json",
        "sha256_measured": dev16_sha,
        "g1_baseline_evidence": "r16 非弃权 courtyard 0/0/0 维持在案",
    }


def probe_typology(typology: dict, typ_sha: str) -> dict:
    """abstain-typology：黑点族 r13-r16 基线（M3 与判正常派次锚）。"""
    bl: dict[str, int] = {}
    for f in typology.get("per_flag", []):
        if f.get("family") == "existence_blackdot":
            bl[f["round"]] = bl.get(f["round"], 0) + 1
    if bl != BLACKDOT_ABSTAIN_BASELINE:
        _fail(f"分型件 existence_blackdot 计数 {bl} != {BLACKDOT_ABSTAIN_BASELINE}")
    bd = typology.get("blackdot_dispatch", {})
    jn = {r: len(bd.get(r, {}).get("judged_normal_dispatches", []))
          for r in ("r15", "r16")}
    if jn != BLACKDOT_JUDGED_NORMAL_BASELINE:
        _fail(f"分型件 blackdot 判正常派次 {jn} != "
              f"{BLACKDOT_JUDGED_NORMAL_BASELINE}")
    return {
        "path_rel": "out/v3-tl2/calibration/abstain-typology-r13-r16.json",
        "sha256_measured": typ_sha,
        "blackdot_abstain_flags_rubric": bl,
        "blackdot_judged_normal_dispatches": jn,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance15_sha: str, guidance18_sha: str,
                 guidance15_bytes: int, guidance18_bytes: int,
                 r15_record_sha: str, r16_record_sha: str,
                 probe_rec: dict, axis_probe: dict, run_probe: dict,
                 dev_probe: dict, typ_probe: dict, witness_sha: str,
                 protocol_sha: str, png_checks: list[dict],
                 edit_list: list[dict], section_asserts: list[str]) -> dict:
    """构建 r18-prep-record 内容（纯函数：同入参必得同 dict）。"""
    axis_rel = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
    probe_rel = "out/v3-tl2/calibration/blackdot-probe-r18.json"
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r18_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r18",
        "round_nature": (
            "轴2 指引侧单变量轮（黑点中性仪器注记；渲染零变更；axis-"
            "experiment-plan-r17-r20 stage1 之一，第十八轮）：判读指引由 "
            "observation-guidance-r15.md 机械变换生成 observation-"
            "guidance-r18.md（本轮唯一判读依据；指引侧变更=新增 §5B 黑点"
            "仪器注记节（黑点物理来源；仪器事实非判据，内容=blackdot-"
            "probe-r18.json 探针证实事实的中性转录）+轮次标识机械同步，见 "
            "guidance_reuse.edit_list）；§2–§7 判据文本逐字承 r15（含 §5A "
            "渲染配色仪器注记原文逐字保留；分段+substring 双重断言复核）、"
            "反放宽条款与三路出口逐字保留；渲染零变更=renders-r14b 四图字"
            "节复用（四 PNG sha256_file 实测与 render-witness-r14b.json 登"
            "记值 fail-closed 比对一致，即 r14/r15/r16/r17 轮盲读所用同一"
            "批文件，见 instrument_change）；GT/阈值/协议零变更（v1.1+v1.2 "
            "维持）；执行 axis-experiment-plan-r17-r20（b6ec6467 冻结件）"
            "stage1 R18=轴2（A2_blackdot_instrument_annotation，实测链见 "
            "changed_variables[0].preregistration_ref），其 guidance 原文"
            "规定「注记内容须先经盘上探针证实黑点物理来源（仪器事实非判"
            "据），无探针证实则该轴不得入轮」——探针先决已满足（s66 证实，"
            "见 pre_round_review）；用户 2026-09-09「三条轴单独/组合/全组"
            "合尝试，选择收益最大的继续」（见 user_directive_note）；r15 "
            "指引已在盘冻结、本轮只读零写入；盲读由编排侧在本记录之后以 "
            "12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的"
            "继续」=授权执行 axis-experiment-plan-r17-r20（b6ec6467 冻结"
            "件，先于 R17–R21 任何实验轮盲读冻结以防事后择优）stage1 "
            "R18=轴2 黑点中性仪器注记轮（A2_blackdot_instrument_"
            "annotation）；本记录=该轮 prep-record 预注册（先于任何盲读冻"
            "结）；round17-dev-record next_iteration_targets[0] 同口径指"
            "令（先经盘上探针证实黑点物理来源→guidance-r18=r15 基座+黑点"
            "中性仪器注记；渲染=renders-r14b 字节复用——指引侧单变量轮，"
            "实测链见 changed_variables[0].preregistration_ref）；比较与组"
            "合决策以冻结件 comparison_rule/combination_decision_rule 为"
            "准；判据零改动、既往轮次字母不回写（r8–r17 维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14/r15/r16 完全相同（renders-r14b 字节复用，四 "
                    "PNG 实测=witness-r14b 登记值），变化仅在指引文本",
            "renders": png_checks,
            "witness": "render-witness-r14b.json（b63771f9，fail-closed 复核）",
            "declaration": (
                "axis-plan stage1 R18 render 原文=「renders-r14b 四图字节复"
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
            "derived": "observation-guidance-r18.md",
            "derived_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r18.md"),
            "derived_sha256": guidance18_sha,
            "byte_size": {"base": guidance15_bytes,
                          "derived": guidance18_bytes,
                          "delta": guidance18_bytes - guidance15_bytes},
            "edit_list": edit_list,
            "verbatim_frozen_sections": (
                "§2 类别枚举、§3 位置口径、§3A 类别判据示例（含示例 c 与末"
                "尾对照说明）、§4 置信度与弃权（含量化判据 (i)(ii)(iii)、"
                "接触性判据、三路出口、反放宽条款、r6/r8/r13 对照说明块）、"
                "§5 courtyard 说明、§5A 渲染配色仪器注记（r15 原文整体逐字"
                "保留、本轮零改动）、§6 输出格式（旗 ID 展示前缀机械替换除"
                "外）、§7 格式对齐提示、§1 角色与任务——分段逐字保留断言"
                "（r15 段落 substring-in 断言）+关键 substring 断言双重复"
                "核，见 verification.section_assertions_passed"),
            "lineage_note": (
                "轮次标识区同步（标题行/声明日期 bullet/round_id_constant "
                "bullet/本轮性质行/示例 reader_id/示例旗 ID 前缀）沿 "
                "s48_calibration_r13_prep.py→s54_calibration_r15_prep.py→"
                "s63_calibration_r17_prep.py（指引侧/仪器轮机械变换）先例；"
                "任务枚举编辑全部逐字执行，非任务枚举的轮次标识同步项（edit "
                "3/5/6）在 edit_list 中如实登记——声明日期 bullet 为本轮新"
                "增同步项（r13→r15 时日期未变故先例无此项），已如实披露；"
                "§1 与头部 bullet 区不在逐字冻结清单（冻结区=§2–§7）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
                "blackdot_probe_transcription_source": {
                    "path_rel": probe_rel,
                    "sha256": probe_rec["sha256"],
                    "f2_certificate_delta_px":
                        probe_rec["f2_certificate_delta_px"],
                },
                "r15_prep_record_schema_template": {
                    "path_rel": "out/v3-tl2/calibration/r15-prep-record.json",
                    "sha256": r15_record_sha,
                },
                "r16_prep_record_mirror_source": {
                    "path_rel": "out/v3-tl2/calibration/r16-prep-record.json",
                    "sha256": r16_record_sha,
                    "cross_check": "24 键顶层结构逐键镜像（同 r17 先例）",
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
                "round17_dev_record_chain": {
                    "path_rel": ("out/v3-tl2/calibration/round17-dev-record"
                                 ".json"),
                    "sha256_measured": DEV_RECORD_R17_SHA_PREFIX,
                    "field": "next_iteration_targets[0]",
                },
                "run_r16_baseline_anchor": run_probe,
                "round16_dev_record_g1_anchor": dev_probe,
                "typology_blackdot_baseline": typ_probe,
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
                "id": "guidance-5b-blackdot-instrument-note",
                "axis": "guidance",
                "axis_id": "A2_blackdot_instrument_annotation",
                "instrument_change": False,
                "target": "observation-guidance-r18.md §5B（新增节）",
                "description": (
                    "指引增补 §5B 黑点仪器注记节（黑点物理来源；仪器事实，非"
                    "判据）：内容=探针证实事实的中性转录（blackdot-probe-"
                    "r18.json section_5b_text 逐字转录，sha256_text 记于 "
                    "edit_list[7].content_sha256）——(a) 孤立实心黑点对=封"
                    "装内 2 个非电镀机械定位孔（np_thru_hole，孔径=焊盘尺寸="
                    "0.65mm、无铜环）的渲染表现（F2 confirmed：证书点 "
                    "fiducial_disk_black 0.64px 匹配）；(b) 焊盘中心圆盘="
                    "电镀通孔焊盘钻孔渲染（F1 confirmed：162 圆钻孔+4 椭圆槽"
                    "孔=framing-r14b 白墨图元计数恒等；r14b bottom 呈橙色、"
                    "非黑色墨点）；(c) 板内孤立焊盘对=CRTC 两电镀焊盘，探针"
                    "未在其邻域找到任何实心黑色圆图元来源——F3 黑点存在性 "
                    "indeterminate 如实登记，注记按中性表述落盘（「探针未在"
                    "该焊盘对邻域找到任何实心黑色圆图元来源」），不替读者下"
                    "正常结论；注记含反指示声明（不构成任何判据、期望清单或"
                    "「应判为正常/无需报告」的指示；旗标判定仍按 §2 类别枚举"
                    "与 §3A/§4 判据独立执行含系统性判据、接触性判据与弃权规"
                    "则；未能证实来源的黑点形态按 §4 既有规则处理）+top 视同"
                    "样适用一句；§2–§7 判据文本零变更（含 §5A 原文逐字）"),
                "attribution_channel": (
                    "M3（黑点族弃权旗数，分型件 rubric 口径）主判据="
                    "hypothesis_test.adjudication 三支（supported ≤6/marginal "
                    "7–9/reject ≥10，r16 基线 12）+附加门 M1 ≤0.85 与守门 "
                    "G1/G2；任一守门破坏→按 axis-plan early_stop_rule 出局"),
                "preregistration_ref": {
                    "path_rel": axis_rel,
                    "sha256_measured": axis_probe["sha256_measured"],
                    "field": axis_probe["field"],
                    "round_quote": axis_probe["round_quote"],
                    "probe": {
                        "path_rel": probe_rel,
                        "sha256": probe_rec["sha256"],
                        "overall_status": probe_rec["overall_status"],
                    },
                },
            },
            {
                "id": "round-identity-sync",
                "axis": "guidance",
                "instrument_change": False,
                "target": "observation-guidance-r18.md 头部与 §6 示例",
                "description": (
                    "标题行 R15→R18、声明日期 bullet 2026-09-08→2026-09-09、"
                    "round_id_constant bullet 2026-09-08-r15→2026-09-09-r18、"
                    "本轮性质行按轴2 指引侧单变量轮口径重写、示例 reader_id "
                    "reader-r15→reader-r18、示例旗 ID 前缀 R15T-（4 处）/"
                    "R15B-（1 处）→R18T-/R18B-——s48/s54/s63 机械变换先例轮"
                    "次标识区同步，如实登记"),
            },
        ],
        "manipulated_factor": (
            "唯一操纵因素=指引增补 §5B 黑点仪器注记节（黑点物理来源；仪器事"
            "实非判据；blackdot-probe-r18.json 探针证实事实的中性转录，per "
            "axis-plan stage1 R18=A2_blackdot_instrument_annotation 探针先"
            "决）；渲染（四图字节复用）/GT/阈值/协议零变更"),
        "unchanged_components": [
            {
                "byte_reuse": True,
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "note": "开工时 sha256_file 实测四 PNG 并与 render-witness-"
                        "r14b.json 登记值逐字比对（bottom=renders.applied/"
                        "prep1.sha256；top=top_zero_change_copies.sha256）"
                        "——四图即 r14/r15/r16/r17 轮盲读所用同一批文件；本"
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
            "§4 全文：总原则、两条显式判据、量化版存在性判断一般判据 "
            "(i)(ii)(iii)、接触性判据、三路出口、confidence 定义、对照说"
            "明（r6/r8/r9/r12/r13 增补块）——逐字承 r15 指引（分段+"
            "substring 断言复核）；反放宽条款「仅因形态不熟悉、不确定其设"
            "计含义，不构成判为正常设计特征的理由」逐字保留",
            "§5 courtyard 说明（r15 指引原文逐字）",
            "§5A 渲染配色仪器注记：r15 指引 §5A 原文整体逐字保留（本轮零"
            "改动——含首句「字节复用同一渲染件」表述，其对本轮仍为真：四 "
            "PNG 实测=witness 登记值；分段+substring 断言复核）",
            "§6 输出格式：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r15 指引原文；仅旗 ID 展示前缀 R15T-/R15B-→R18T-/"
            "R18B- 机械替换，随指引落盘固化、无需派发层覆盖）",
            "§7 格式对齐提示（r15 指引原文逐字）",
            "§1 角色与任务与盲读纪律（r15 指引原文逐字；不在冻结清单亦零"
            "改动，分段断言复核）",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r17 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "度量设计五条与聚合口径：沿 r16-prep-record measurement_design"
            ".items 同一口径（仅轮次标识、reader 前缀与渲染件名按 r18 改"
            "写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16 完"
            "全相同文件：白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)、"
            "其余层 kicad 原配色不变；四 PNG sha256_file 实测=witness-r14b "
            "登记值 fail-closed 比对一致）——渲染零变更；本轮唯一变更=指引"
            "侧 §5B 黑点仪器注记（黑点物理来源；仪器事实非判据，不构成任何"
            "「应判正常/无需报告」的指示，不降低任何责任门槛；黑点相关现象"
            "的旗标判定仍按 §2/§3A/§4 独立执行）；§5B 所载图元计数（162 圆"
            "钻孔+4 椭圆槽孔、2 个 np 定位孔）为板卡源文件仪器事实、非期望"
            "清单；bottom 视判读口径沿用 r4 指引原文不改（top/bottom 判读"
            "口径在图像空间完全一致、不做镜像换算）；bottom 零旗标分母=0 "
            "时弃权率按 cal._ratio 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R18 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r16-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R18T/R18B；"
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
                "本轮恰一个操纵因子（指引增补 §5B 黑点仪器注记节；渲染零变"
                "更字节复用）、检验恰一个假设（axis-experiment-plan-r17-r20 "
                "stage1 R18=轴2；hypothesis_id=axis-plan-r18-blackdot-note）；"
                "归因目的=黑点族弃权主因是否为「黑点物理性质不明导致的存在"
                "性弃权」的注记侧首验；跨轮对比（vs r16 基线 M3=12）按冻结"
                "件 comparison_rule（显著收益参照；跨轮实例群漂移混杂显式容"
                "忍、参照 r15→r16 纯重抽变动 0.09064 在案量级）；字母/机制"
                "观察/度量教训三分记账（adjudication.mechanism_observation_"
                "separate 与 metric_lesson_separate 单列，不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "guidance-5b-blackdot-instrument-note（指引侧唯一操纵；"
                    "非渲染/GT/阈值/协议变更）"),
                "metric": (
                    "M3（黑点族弃权旗数，分型件 rubric 口径；r16 基线 12、"
                    "r13–r16 序列 9/14/8/12 在案）三分判据见 hypothesis_test."
                    "adjudication：supported M3 ≤6（基线一半）且 G1/G2 维持"
                    "且 M1 ≤0.85；marginal M3 7–9 或 M1 0.85–0.862（部分收"
                    "益）；reject M3 ≥10 或 G1/G2 任一破坏（early_stop 出局）"),
                "supported": (
                    "M3 ≤6 且 G1/G2 维持且 M1 ≤0.85 → 注记使黑点族负责任判"
                    "定成立（轴2 supported）"),
                "marginal": (
                    "M3 7–9（回落未过半）或 M1 0.85–0.862 → 记录为部分收益"),
                "reject": (
                    "M3 ≥10（注记未使黑点族回落）或 G1/G2 任一破坏 → 按退"
                    "出规则出局；转向轴3/组合轮"),
            },
            "guard_channel": {
                "metric": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15/r16 "
                    "在案 0/0/0，round16-dev-record 实测装载校验通过）；"
                    "G2=guard_ok=True 维持（top 视非弃权旗标 frame_box_pct "
                    "几何门，面积比出局条目按 guard_channel 如实登记）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r18 指引 §2–§7 逐字承 r15，分段"
                    "断言复核），非弃权框仍须满足；任一守门破坏→按 "
                    "axis-plan early_stop_rule 出局（字母照实+出局声明）"),
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
            "本轮判据文本零改动：§2–§7 逐字承 r15（分段+substring 双重断"
            "言复核；§5A 原文整体逐字保留）；§5B 为仪器事实注记、非判据—"
            "—不构成任何「应判正常/无需报告」的指示，不降低任何存在性、"
            "归类、定位或报告的责任门槛（指引内反指示声明随 §5B 落盘）；"
            "反放宽条款「仅因形态不熟悉、不确定其设计含义，不构成判为正常"
            "设计特征的理由」与三路出口显式化在 r18 指引 §4 内逐字保留"
            "（fail-closed substring 断言）；§5B 注记不得被援引为判正常设"
            "计特征的依据——存在性判断仍按 §4 (i)(ii)(iii) 全部要件执行，"
            "注记仅提供图元物理来源事实；M3 ≤6/0.85 等本轮判据只用于轴2 "
            "收益方向归因（axis-experiment-plan-r17-r20 冻结比较规则），不"
            "触碰 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与任何阈值常量（CONTAINMENT_MIN/"
            "AREA_RATIO_MAX，只作口径引用）——门照常独立计算；不构成任何"
            "阈值反向放宽"),
        "pre_round_review": {
            "status": "satisfied_by_probe",
            "basis": (
                "s66 探针证实（blackdot-probe-r18.json，a49441ac，"
                "overall_status=F1/F2 confirmed；F3 identity_confirmed_"
                "blackdot_indeterminate——焊盘对身份证实、其邻域黑点存在性"
                "indeterminate 如实登记，§5B (c) 项按中性表述落盘、不替读"
                "者下正常结论；F2 证书点 fiducial_disk_black 0.64px 匹配、"
                "排除项全零）+axis-experiment-plan-r17-r20 冻结（b6ec6467，"
                "R18=A2 探针先决条款在案）；符合 axis-plan A2 原文「无探针"
                "证实则该轴不得入轮」的入轮前提"),
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
                "不影响判读语义——分类判据零变更，仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11–r17 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-"
                "r18.md，含 §5A/§5B 仪器注记节——指引本体组成部分，非派发"
                "层补充）+单张 PNG（renders-r14b 四图）+派发命名指令（含 "
                "v1.2 工具行为规约硬性条款：纯 Read 内联判读、禁止任何程"
                "序化图像处理），零 GT、零历史判读件、零诊断/探针内容"
                "（blackdot-probe-r18.json 与 diag 件为主审/编排侧核验件、"
                "非 reader 上下文）；两波次串行保序（同一实例先 applied 后 "
                "prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r18-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R18T/R18B（r18 指引 §6 已机械替换落盘 R18T-/R18B-——本轮"
                "指引本体即为 r18 前缀，无需派发层覆盖）；实例间编号独立，"
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
            "observation-guidance-r15.md（r18 指引的唯一变换基座；d5babc93 "
            "锚 fail-closed，零写入）、r15-prep-record.json（链锚=4c6cd919 "
            "先验证；schema 模板）、r16-prep-record.json（链锚=46fbd15b；"
            "24 键结构镜像来源）、blackdot-probe-r18.json（a49441ac 锚；§5B "
            "文本唯一转录源、kind/round_id/overall_status/族状态 fail-"
            "closed 复核；探针只读解析板卡源文件、零写板零 PNG 内容读取）、"
            "render-witness-r14b.json（b63771f9 锚；四 PNG 见证登记值+字节"
            "复用证明）、axis-experiment-plan-r17-r20.json（b6ec6467 锚；"
            "stage1 R18=A2 定义、r16 基线 M1/M3、r15 带上缘、守门、用户指"
            "令原文）、round17-dev-record.json（e526093f 锚；仅读取 "
            "next_iteration_targets[0] 探针先决条款）、calibration-run-r16."
            "json（2c1f8265 锚；仅读取 hypothesis_test 顶层判据冻结值字段"
            "——M1=0.771429、guard_ok=True；其 GT 匹配与逐旗明细内容不读"
            "取、不入记录）、round16-dev-record.json（589fe62f 锚；仅读取 "
            "G1 基线证据字段）、abstain-typology-r13-r16.json（6dadac8d "
            "锚；仅读取 per_flag 家族计数与 blackdot_dispatch 判正常派次"
            "计数做预注册基线锚）、evaluation-protocol-v1.md（仅在盘+哈希"
            "复核，锚=22dc7337）；renders-r14b 四 PNG 仅哈希+magic（渲染"
            "零变更以 witness 登记哈希比对为准）；observation-guidance-"
            "r18.md 与 r18-prep-record.json 为本轮仅有的两个 out/ 新建文件"
            "（scripts/s66_blackdot_probe_r18.py 与 "
            "scripts/s67_calibration_r18_prep.py 为生成器本体，亦即本轮另"
            "两个新文件；blackdot-probe-r18.json 为探针件）；reader 派发"
            "（后续编排侧执行）上下文=observation-guidance-r18.md+单张 "
            "PNG（renders-r14b）+派发指令（R18T/R18B 前缀、reader-r18-"
            "{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬性条款），零 GT、"
            "零历史判读件、零诊断/探针内容、零指引之外的解释；视觉判读禁"
            "止由编排/收口包兼任；跨实例/跨视角禁止交流（12 次盲读相互独"
            "立、不得交换判读信息——独立性是多实例协议的前提，亦为轴2 收"
            "益裁决有效性的前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R15, R15_PREP_RECORD, R16_PREP_RECORD,
                 BLACKDOT_PROBE, WITNESS_R14B, AXIS_PLAN, DEV_RECORD_R17,
                 RUN_R16, ROUND16_DEV_RECORD, TYPOLOGY, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件（GUIDANCE_R18/RECORD）不做前置硬拒绝：落盘阶段防覆写守卫
    # 按红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→
    # 幂等通过（零覆写）。（首轮创建前置=两目标不存在，已由编排侧确认。）

    # ---- 冻结锚验证（fail-closed）----
    r15_record_sha = _sha(R15_PREP_RECORD)
    r16_record_sha = _sha(R16_PREP_RECORD)
    probe_sha = _sha(BLACKDOT_PROBE)
    witness_sha = _sha(WITNESS_R14B)
    axis_sha = _sha(AXIS_PLAN)
    dev17_sha = _sha(DEV_RECORD_R17)
    run_r16_sha = _sha(RUN_R16)
    dev16_sha = _sha(ROUND16_DEV_RECORD)
    typ_sha = _sha(TYPOLOGY)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    for sha, prefix, label in (
            (r15_record_sha, R15_PREP_RECORD_SHA_PREFIX, "r15-prep-record"),
            (r16_record_sha, R16_PREP_RECORD_SHA_PREFIX, "r16-prep-record"),
            (probe_sha, BLACKDOT_PROBE_SHA_PREFIX, "blackdot-probe-r18"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (axis_sha, AXIS_PLAN_SHA_PREFIX, "axis-experiment-plan"),
            (dev17_sha, DEV_RECORD_R17_SHA_PREFIX, "round17-dev-record"),
            (run_r16_sha, RUN_R16_SHA_PREFIX, "calibration-run-r16"),
            (dev16_sha, ROUND16_DEV_RECORD_SHA_PREFIX, "round16-dev-record"),
            (typ_sha, TYPOLOGY_SHA_PREFIX, "abstain-typology-r13-r16"),
            (protocol_sha, EVAL_PROTOCOL_V1_SHA_PREFIX,
             "evaluation-protocol-v1")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，立即"
                  f"停止）")

    r15_record = json.loads(R15_PREP_RECORD.read_text(encoding="utf-8"))
    r16_record = json.loads(R16_PREP_RECORD.read_text(encoding="utf-8"))
    for rec, label, rid in ((r15_record, "r15-prep-record",
                             "2026-09-08-r15"),
                            (r16_record, "r16-prep-record",
                             "2026-09-08-r16")):
        if rec.get("schema_version") != "3.0":
            _fail(f"{label} schema_version != 3.0（结构漂移）")
        if rec.get("kind") != f"tl2_calibration_{label.replace('-prep-record', '')}_prep_record":
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

    # ---- 结构探测（§5B 转录源与判据冻结值锚）----
    probe_doc = json.loads(BLACKDOT_PROBE.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    run_r16 = json.loads(RUN_R16.read_text(encoding="utf-8"))
    dev16 = json.loads(ROUND16_DEV_RECORD.read_text(encoding="utf-8"))
    typology = json.loads(TYPOLOGY.read_text(encoding="utf-8"))
    probe_rec = probe_blackdot(probe_doc, probe_sha)
    png_checks = check_renders(witness)
    axis_probe = probe_axis_plan(axis_plan, axis_sha)
    run_probe = probe_run_r16(run_r16, run_r16_sha)
    dev_probe = probe_dev_records(dev16, dev16_sha)
    typ_probe = probe_typology(typology, typ_sha)

    # ---- 指引生成（8 组锚定编辑 + 不变量断言）----
    section_5b = probe_doc["section_5b_text"]
    t_work, edit_list = build_guidance(base_text, section_5b)
    edit_list_sorted = sorted(edit_list, key=lambda e: e["edit"])
    section_asserts = assert_guidance_invariants(base_text, t_work, section_5b)

    guidance18_bytes = t_work.encode("utf-8")
    guidance18_sha = hashing.sha256_bytes(guidance18_bytes)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance15_sha=guidance15_sha, guidance18_sha=guidance18_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance18_bytes=len(guidance18_bytes),
        r15_record_sha=r15_record_sha, r16_record_sha=r16_record_sha,
        probe_rec=probe_rec, axis_probe=axis_probe, run_probe=run_probe,
        dev_probe=dev_probe, typ_probe=typ_probe, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks,
        edit_list=edit_list_sorted, section_asserts=section_asserts)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r16-prep-record 24 键逐键镜像
    missing = sorted(set(r16_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r16_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r16-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # hypothesis_test 逐字断言链：任务给定文本→json.loads→常量→记录字段
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if record["hypothesis_test"] != HYPOTHESIS_TEST:
        _fail("hypothesis_test 与预注册判据常量不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != "axis-plan-r18-blackdot-note":
        _fail("hypothesis_test.hypothesis_id 不符")
    # 结构自证（指引侧轮口径）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（指引侧单变量轮）")
    if len(record["changed_variables"]) != 2:
        _fail("changed_variables 必须恰 2 项（§5B 注记/轮次标识）")
    if [v["id"] for v in record["changed_variables"]] != [
            "guidance-5b-blackdot-instrument-note", "round-identity-sync"]:
        _fail("changed_variables 顺序/标识不符")
    if any(v["instrument_change"] is not False
           for v in record["changed_variables"]):
        _fail("changed_variables 全部须为非仪器侧变量")
    if record["manipulated_factor"].find("唯一操纵因素=指引增补 §5B") != 0:
        _fail("manipulated_factor 不符（唯一操纵因子=§5B 注记增补）")
    if record["pre_round_review"]["status"] != "satisfied_by_probe":
        _fail("pre_round_review.status 不符")
    if "轴2 指引侧单变量轮" not in record["round_nature"]:
        _fail("round_nature 缺「轴2 指引侧单变量轮」声明")
    if "渲染零变更" not in record["round_nature"]:
        _fail("round_nature 缺「渲染零变更」声明")
    if "stage1" not in record["round_nature"]:
        _fail("round_nature 缺 stage1 声明")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    if "renders-r14b" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 renders-r14b 图像口径")
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
    if record["guidance_reuse"]["derived_sha256"] != guidance18_sha:
        _fail("guidance_reuse.derived_sha256 与实测不符")
    # §5B 非判据自证：注记编辑不得触碰 §2–§7 冻结锚关键语
    for e in edit_list_sorted:
        if e["edit"] == 8:
            for needle in ("§2", "§3", "§4 ", "§5 ", "§5A", "§6", "§7"):
                if needle in e.get("anchor", "") and needle not in ("§6",):
                    _fail("§5B 插入编辑锚异常")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance15_sha=guidance15_sha, guidance18_sha=guidance18_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance18_bytes=len(guidance18_bytes),
        r15_record_sha=r15_record_sha, r16_record_sha=r16_record_sha,
        probe_rec=probe_rec, axis_probe=axis_probe, run_probe=run_probe,
        dev_probe=dev_probe, typ_probe=typ_probe, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks,
        edit_list=edit_list_sorted, section_asserts=section_asserts)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r18-prep-record")

    # ---- 防覆写守卫 + 落盘 ----
    if GUIDANCE_R18.exists():
        if GUIDANCE_R18.read_bytes() != guidance18_bytes:
            _fail("observation-guidance-r18.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r18-prep] 重跑自证：observation-guidance-r18.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R18.write_bytes(guidance18_bytes)
        if GUIDANCE_R18.read_bytes() != guidance18_bytes:
            _fail("回读不一致: observation-guidance-r18.md")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r18-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r18-prep] 重跑自证：r18-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r18-prep-record.json")

    # ---- 汇总打印 ----
    print("[r18-prep] 验证通过：r15 指引基座锚 "
          f"{GUIDANCE_R15_SHA_PREFIX} OK（只读，零写入，"
          f"{len(base_text.encode('utf-8'))} B）；r15-prep-record schema 模"
          f"板锚 {R15_PREP_RECORD_SHA_PREFIX} OK；r16-prep-record 24 键镜像"
          f"源锚 {R16_PREP_RECORD_SHA_PREFIX} OK；blackdot-probe-r18 锚 "
          f"{BLACKDOT_PROBE_SHA_PREFIX} OK（F1/F2 confirmed、F2 证书点偏差 "
          f"{probe_rec['f2_certificate_delta_px']}px、F3 黑点存在性 "
          f"indeterminate 如实登记）；witness-r14b 锚 {WITNESS_R14B_SHA_PREFIX} "
          f"OK；axis-plan 冻结锚 {AXIS_PLAN_SHA_PREFIX} OK（stage1 R18=A2、"
          f"r16 基线 M1=0.771429/M3=12、带上缘 0.862069、守门 G1/G2）；"
          f"round17-dev 锚 {DEV_RECORD_R17_SHA_PREFIX} OK（探针先决条款在"
          f"案）；run-r16 判据锚 {RUN_R16_SHA_PREFIX} OK（M1=0.771429、"
          f"guard_ok=True）；round16-dev 链锚 {ROUND16_DEV_RECORD_SHA_PREFIX} "
          f"OK（G1 基线 0/0/0 在案）；typology 锚 {TYPOLOGY_SHA_PREFIX} OK"
          f"（黑点族 r13–r16=9/14/8/12、判正常 r15=3/r16=2）；"
          f"evaluation-protocol-v1 在盘锚 {EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r18-prep] 渲染仪器实测（四 PNG 实测=witness-r14b 登记值；字节"
          "复用、零仪器变更）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r18-prep] hypothesis_test 逐字断言链：预注册判据原文文本 → "
          "json.loads → 常量 → 记录字段，三层相等 PASS（数值/口径零改动；"
          "hypothesis_id=axis-plan-r18-blackdot-note；6=12/2、0.85<0.862069 "
          "与 axis-plan/typology/run-r16 在案锚逐一相符）")
    print(f"[r18-prep] 顶层键镜像断言：与 r16-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）")
    print(f"[r18-prep] 指引不变量断言：{len(section_asserts)} 项全部通过"
          f"（§1/§2–§5/§5A/§6/§7 分段逐字 {len(SECTION_PAIRS)} 段+§5A 原文"
          f"整体+§5B 逐字 + 关键 substring {len(REQUIRED_SUBSTRING_VALUES)} "
          f"条 + 残留零 + 新文本在位 + §5B 位置）")
    print(f"[r18-prep] 字节数差：r18（{len(guidance18_bytes)} B）- r15（"
          f"{len(base_text.encode('utf-8'))} B）= "
          f"{len(guidance18_bytes) - len(base_text.encode('utf-8'))} B")
    print(f"[r18-prep] 工件 sha256：observation-guidance-r18.md="
          f"{_sha(GUIDANCE_R18)}")
    print(f"[r18-prep] 工件 sha256：r18-prep-record.json={_sha(RECORD)}")
    print("[r18-prep] §5B 节实际落盘全文：")
    k = t_work.index("## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）")
    print(t_work[k:t_work.index("## 6. 输出格式")], end="")


if __name__ == "__main__":
    main()
