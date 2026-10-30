#!/usr/bin/env python
"""CAL-R17-PREP：R17 轴1 仪器轮（渲染分辨率倍增 640→1280dpi）预备包（只
新建两个文件：out/v3-tl2/calibration/observation-guidance-r17.md 与
out/v3-tl2/calibration/r17-prep-record.json；datasets/ 与 out/ 既有文件
只读、零改动，observation-guidance-r15.md 零字节不动）。

R17 轮性质（预注册，非事后）：**轴1 仪器轮（渲染分辨率倍增；axis-
experiment-plan-r17-r20 stage1 之一）**——仪器变更=renders-r17 四图全
新渲染（dpi 640→1280，r14b 配色规则重放，margin 240px 物理等值；非字
节复用，s62 仪器包产物只读引用）；指引侧仅轮次标识机械同步与 §5A 描
述性同步（配色 px 数与出处句随仪器更新，仅描述性、非判据）；判据零改
动（§2–§7 逐字承 r15）。执行 axis-experiment-plan-r17-r20（b6ec6467
冻结件）stage1 R17=轴1（A1_render_resolution_x2），用户 2026-09-09
「三条轴单独/组合/全组合尝试，选择收益最大的继续」。

指引生成=确定性机械变换（锚串命中数 fail-closed，锚恰 1 次否则 FAIL）。
任务枚举编辑：(1) 标题/round_id_constant R15→R17（含 §6 示例旗 ID 前缀
R15T-（4 处）/R15B-（1 处）→R17T-/R17B-、示例 reader_id
reader-r15→reader-r17）；(2) 「本轮变更声明」节正文整体替换（任务给定
文本逐字）；(3) §5A 描述性同步两处（首句渲染件语义；px 数与出处句）。
另沿 s48/s54（r12→r13、r13→r15 指引侧轮）机械变换先例同步轮次标识区
（声明日期 bullet 2026-09-08→2026-09-09、本轮性质行按轴1 仪器轮口径重
写；非任务枚举、如实登记）——§1 与头部 bullet 区不在逐字冻结清单（冻
结区=§2–§7）。

§5A 同步纪律：仅两处描述性编辑（非判据）——
  (i) 首句：「本轮 bottom 渲染采用 R14b 配色（与 R14 相同，字节复用同
      一渲染件）」→「本轮 bottom 渲染采用 R14b 配色规则（与 R14/R15/
      R16 同一配色语义；本轮渲染件为 1280dpi 新渲染，非字节复用）」。
  (ii) px 数值更新：橙 81672→326460、绿 206632→903366（数字来源=
      render-witness-r17.json palette_assertion_summary 实测，脚本
      fail-closed 装载）；「探针板内空隙白 206632 px（final 口径）/
      206052 px（严格口径）」句改写为「640dpi 期探针值为 206632/206052
      px（final 口径/严格口径，转录自 render-framing-r14b.json
      probe_block.board_white_coverage，历史值保持可考），本轮 1280dpi
      实测绿 903366 px」——任务给定替换文本「640dpi 期探针值为
      206632/206052 px，本轮 1280dpi 实测绿 903366 px」以语义等价形式
      落盘（历史出处随探针值括注、实测值括注 witness-r17 出处），避免
      替换后「转录自 render-framing-r14b.json」悬置误挂到 1280dpi 实测
      值上；两条数字子串逐字在位断言。§5A 其余文字（非图元声明、非判
      据声明、top 无配色）逐字保留。

功能：
  1. fail-closed 复核 observation-guidance-r15.md（d5babc93 锚；r17
     指引唯一变换基座，只读零写入）。
  2. fail-closed 复核 r15-prep-record.json（4c6cd919 锚；schema 模板）
     与 r16-prep-record.json（46fbd15b 锚；24 键结构镜像源；实测 sha
     与 round16-dev-record 登记值交叉核对）。
  3. fail-closed 复核 render-framing-r17.json（a1084c14 锚、kind、
     round_id_constant）：单变量声明（dpi 640→1280、margin
     120px→240px 物理等值 0.1875in、r14b 配色规则重放）与探针可行性。
  4. fail-closed 复核 render-witness-r17.json（e979bec2 锚、kind）：
     配色语义（橙 [255,165,0]/绿 [0,128,0]）、两板 palette_assertion_
     summary.assertions_pass 双真且橙 326460/绿 903366/板内白 0 两板相
     同、top 橙/绿=0、两板 bottom 同哈希；640dpi 期参照值 81672/206632
     （r14b_references.palette_640_measured）——§5A px 转录源。
  5. fail-closed 复核 axis-experiment-plan-r17-r20.json（b6ec6467 锚、
     kind）：stage1 rounds[0]=R17/A1_render_resolution_x2、r16 基线
     M1=0.771429、显著收益定义（绝对降幅 ≥0.10）、守门 G1/G2、用户指
     令原文。
  6. fail-closed 复核 round16-dev-record.json（589fe62f 锚）：verdict=
     inconclusive、top 27/35=0.771429、r16 非弃权 courtyard 0/0/0 在案
     （G1 基线证据）、r16-prep-record 登记 sha 交叉核对；run-r16
     （2c1f8265 锚）hypothesis_test.measurement 判据冻结值锚定（M1=
     0.771429、guard_ok=True；GT 匹配与逐旗明细不读取）。
  7. fail-closed 复核 evaluation-protocol-v1.md 在盘且锚=22dc7337；
     diag-r17-render/ 在盘（存在性，零内容读取）。
  8. 渲染仪器实测：renders-r17 四 PNG magic+sha256_file 实测并与
     witness-r17 登记值逐字比对（bottom=0c2d5c00 两板同、applied-top=
     b35315ef、prep1-top=bdce8bbb）——本轮零重渲染、只读引用。
  9. 生成 observation-guidance-r17.md（10 组锚定编辑，命中数逐一断言；
     §1/§2–§5/§6/§7 分段逐字保留断言+关键 substring 断言+R15 残留零断
     言+新文本在位断言+§5A 位置断言）。
 10. 落盘 r17-prep-record.json（canonical JSON=hashing.canonical_json_
     bytes；顶层键集合与 r16-prep-record 24 键逐键镜像；
     hypothesis_test=任务预注册判据逐字（文本→json.loads→常量→记录字
     段三层相等）；同参重建两次逐字节一致自证；防覆写守卫——目标已存
     在且重建字节非逐字节等同→FAIL，等同→幂等通过（零覆写）；落盘后
     回读验字节）。
 11. 打印：两文件 sha256（sha256_file）、r17 相对 r15 字节数差、§5A 节
     实际落盘全文、四 PNG 比对结果、逐项断言通过清单。

判据数值自洽断言：M1_supported 阈值 0.671429=r16 基线 0.771429−0.10
（axis-plan 显著收益定义），HYPOTHESIS_TEST_TEXT 内数值与在案锚逐一相符
（不符即停——防预注册文本与在案事实漂移）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-09 / 2026-09-09-r17）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-* /
reader-raw-* / derivation-log-* / 任何 compare 产物；run-r16 仅读
hypothesis_test 顶层判据值字段做冻结值锚（不读其 GT 匹配与逐旗明细内容
入记录）；无 git；r15 指引只读；记录内零 GT、零期望数量/分布/坐标
（326460/903366/81672/206632/206052/162/4 为仪器侧配色与像素计数事实，
非板面内容断言）；指引内零轮次结果数字（基线数字仅入本编排侧记录）。

用法：python scripts/s63_calibration_r17_prep.py
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
GUIDANCE_R17 = CAL_DIR / "observation-guidance-r17.md"
R15_PREP_RECORD = CAL_DIR / "r15-prep-record.json"
R16_PREP_RECORD = CAL_DIR / "r16-prep-record.json"
ROUND16_DEV_RECORD = CAL_DIR / "round16-dev-record.json"
RUN_R16 = CAL_DIR / "calibration-run-r16.json"
FRAMING_R17 = CAL_DIR / "render-framing-r17.json"
WITNESS_R17 = CAL_DIR / "render-witness-r17.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
DIAG_R17_DIR = CAL_DIR / "diag-r17-render"
RECORD = CAL_DIR / "r17-prep-record.json"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r17"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R15_SHA_PREFIX = "d5babc93"
R15_PREP_RECORD_SHA_PREFIX = "4c6cd919"
R16_PREP_RECORD_SHA_PREFIX = "46fbd15b"
ROUND16_DEV_RECORD_SHA_PREFIX = "589fe62f"
RUN_R16_SHA_PREFIX = "2c1f8265"
FRAMING_R17_SHA_PREFIX = "a1084c14"
WITNESS_R17_SHA_PREFIX = "e979bec2"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 渲染仪器见证（render-witness-r17.json 登记值；四 PNG 实测逐一
#: fail-closed 比对。bottom=renders.{applied,prep1}.sha256（两板同哈希）；
#: top=renders.{applied-top,prep1-top}.sha256）
RENDERS_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
R17_BOTTOM_SHA_PREFIX = "0c2d5c00"
R17_APPLIED_TOP_SHA_PREFIX = "b35315ef"
R17_PREP1_TOP_SHA_PREFIX = "bdce8bbb"

#: §5A px 数值事实（仪器侧转录目标值；结构探测不符即停，转录不凭记忆）
EXPECTED_ORANGE_PX_R17 = 326460
EXPECTED_GREEN_PX_R17 = 903366
EXPECTED_ORANGE_PX_640 = 81672
EXPECTED_GREEN_PX_640 = 206632
EXPECTED_VOID_FINAL_640 = 206632
EXPECTED_VOID_STRICT_640 = 206052
EXPECTED_WHITE_FILL_COUNT = 162
EXPECTED_WHITE_STROKE_COUNT = 4
EXPECTED_WHITE_IN_BOARD = 0
EXPECTED_ORANGE_RGB = [255, 165, 0]
EXPECTED_GREEN_RGB = [0, 128, 0]

#: 判据冻结值锚（r16 零变更基线与显著收益阈值；axis-plan/run-r16 实测）
M1_R16_BASELINE = 0.771429
M1_R16_TOP_COUNT = 27
M1_R16_TOP_FLAGS = 35
SIGNIFICANT_BENEFIT_DELTA = 0.10
M1_SUPPORTED_THRESHOLD = 0.671429

# ---------------------------------------------------------------------------
# 预注册判据（逐字，先于任何盲读冻结；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "axis-plan-r17-resolution-double",
  "hypothesis": "top（及 bottom）的 contact/存在性族弃权源于 640dpi 下细节不可负责任分辨（分型件：97.7% 弃权=§4 诚实弃权）。分辨率倍增至 1280dpi 后，此前亚感知的间隙与细节变为可辨，读者可负责任地判定，弃权率显著回落——若成立则 top 通道的瓶颈=分辨率；若不成立则分辨率非瓶颈（轴1 证伪，转向轴2/轴3）。",
  "adjudication": {
    "supported": "M1（top 全旗聚合弃权率，12 派次全口径）≤ 0.671429（相对 r16 零变更基线 0.771429 绝对降幅 ≥0.10=计划件『显著收益』阈值）——分辨率瓶颈实锤",
    "marginal": "0.671429 < M1 < 0.771429——带内小幅改善，未过显著收益阈值（与跨轮漂移噪声不可分）；记 marginal，轴1 不判定为胜出",
    "reject": "M1 ≥ 0.771429（不优于零变更基线）——轴1 证伪：分辨率非瓶颈（或视觉编码器尺寸上限抵消增益，机制观察须记录读者实际可见细节的自述）",
    "guards": "G1=bottom courtyard 非弃权 0/0/0 维持；G2=guard_ok=True；任一破坏→轴1 按 plan early_stop_rule 出局（字母照实+出局声明）",
    "mechanism_observation_separate": "bottom 侧观察（M2/黑点族 M3）；读者对细节可见性的自述摘录（reading_notes 中提及清晰度/分辨率者）；courtyard 旗与黑点族分布对照 r15/r16；gt 匹配照常",
    "metric_lesson_separate": "跨轮实例群漂移混杂照旧声明（r15→r16 纯重抽漂移 0.09064 在案）；字母=预注册阈值命中与否的描述性结论",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

# ---------------------------------------------------------------------------
# 指引机械变换锚与替换文本
# ---------------------------------------------------------------------------
OLD_TITLE = "# R15 轮 reader 判读指引（observation-guidance-r15）"
NEW_TITLE = "# R17 轮 reader 判读指引（observation-guidance-r17）"
DECL_HEADING = "## 本轮变更声明（预注册，非事后）"
SECTION1_HEADING = "## 1. 角色与任务"
OLD_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-08"
NEW_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-09"
OLD_ROUND_ID_BULLET = "- round_id_constant: `2026-09-08-r15`"
NEW_ROUND_ID_BULLET = "- round_id_constant: `2026-09-09-r17`"
OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（bottom 配色语义仪器注记配套"
    "轮）**。渲染零变更（复用 R14 冻结渲染件 renders-r14b）；本轮唯一"
    "变更=判读指引增补 §5A 渲染配色仪器注记节（颜色→来源映射显式化；"
    "预注册见下），指引落盘后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量仪器侧变更轮（轴1 渲染分辨率倍增轮；axis-"
    "experiment-plan-r17-r20 stage1 之一）**。仪器变更为本轮唯一实验变"
    "量（renders-r17 四图全新渲染 dpi 640→1280，r14b 配色规则重放；详见 "
    "render-framing-r17），判据零改动；指引侧仅轮次标识同步与 §5A 描述"
    "性同步（配色 px 数与出处句随仪器更新），指引落盘后由编排侧重新盲"
    "读。")

#: 任务枚举编辑：「本轮变更声明」节正文整体替换（逐字，任务给定文本）
NEW_DECLARATION = (
    "本轮（R17）为轴1 仪器轮：渲染分辨率 640→1280dpi（四图全部，margin "
    "240px 物理等值，r14b 配色规则重放；详见 render-framing-r17）。指引"
    "侧仅 §5A 描述性同步（配色 px 数与出处句随仪器更新，见下）；§2 类别"
    "枚举、§3/§3A、§4 置信度与弃权（含量化判据 (i)(ii)(iii) 与接触性判"
    "据）、§5 courtyard 说明、§6 输出格式、§7 格式对齐提示全部逐字不变"
    "。预注册判据见 r17-prep-record.json hypothesis_test（先于任何盲读"
    "冻结）。")

#: §5A 描述性同步（两处，仅描述性、非判据）
SECTION_5A_HEADING = "## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）"
E1_OLD = "本轮 bottom 渲染采用 R14b 配色（与 R14 相同，字节复用同一渲染件）。"
E1_NEW = ("本轮 bottom 渲染采用 R14b 配色规则（与 R14/R15/R16 同一配色"
          "语义；本轮渲染件为 1280dpi 新渲染，非字节复用）。")
E2_OLD = "成图实测橙 81672 px（render-witness-r14b.json palette_assertion_summary，两板相同）"
E2_NEW = "成图实测橙 326460 px（render-witness-r17.json palette_assertion_summary，两板相同）"
E3_OLD = ("探针板内空隙白 206632 px（final 口径）/ 206052 px（严格口"
          "径），转录自 render-framing-r14b.json（probe_block.board_"
          "white_coverage）；成图实测绿 206632 px（render-witness-r14b"
          ".json，两板相同）。")
E3_NEW = ("640dpi 期探针值为 206632/206052 px（final 口径/严格口径，转"
          "录自 render-framing-r14b.json probe_block.board_white_"
          "coverage，历史值保持可考），本轮 1280dpi 实测绿 903366 px"
          "（render-witness-r17.json，两板相同）。")

#: 锚串在 r15 基座中的期望命中数（不符即停；声明区先行替换后计数收敛）
EXPECTED_HITS = {
    "title": 1,
    "decl_heading": 1,
    "section1": 1,
    "date_line": 1,
    "round_id_bullet": 1,
    "nature_line": 1,
    "e1_old": 1,
    "e2_old": 1,
    "e3_old": 1,
    "prefix_R15T-": 4,
    "prefix_R15B-": 1,
    "reader_id": 1,
}

#: §1/§2–§5/§6/§7 分段逐字保留断言（起点标题锚, 终点标题锚；§5 段以 §5A
#: 标题锚截尾——§5A 本身本轮有描述性同步、不在此列，另行 substring 断言；
#: §6/§7 段先做旗前缀/reader-id 规格化（R15T-/R15B-/reader-r15→R17）再
#: 断言）
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

#: 关键 substring 断言（判据零放宽+§5A 同步在位；逐条打印通过情况）
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
    # ---- §5A 描述性同步在位（两处；仅描述性、非判据）----
    "§5A 同步(i) 首句：本轮渲染件为 1280dpi 新渲染，非字节复用":
        "本轮渲染件为 1280dpi 新渲染，非字节复用",
    "§5A 同步(ii) 橙 px（witness-r17）：成图实测橙 326460 px（render-witness-r17.json":
        "成图实测橙 326460 px（render-witness-r17.json",
    "§5A 同步(ii) 绿 px（witness-r17）：本轮 1280dpi 实测绿 903366 px":
        "本轮 1280dpi 实测绿 903366 px",
    "§5A 同步(ii) 历史可考：640dpi 期探针值为 206632/206052 px":
        "640dpi 期探针值为 206632/206052 px",
    "§5A 保留-非图元声明：**绿色区域不是图元**": "**绿色区域不是图元**",
    "§5A 保留-非判据声明：本节为仪器事实（渲染生成语义）":
        "本节为仪器事实（渲染生成语义）",
    "§5A 保留-top 无配色：top 渲染无配色变更（与既往轮次一致）":
        "top 渲染无配色变更（与既往轮次一致）",
    "§5A 保留-白墨图元计数：162 fill + 4 stroke": "162 fill + 4 stroke",
    "§5A 保留-转录源计数：combined_white_fill_count=162、combined_white_stroke_count=4":
        "combined_white_fill_count=162、combined_white_stroke_count=4",
}


def _fail(msg: str) -> None:
    print(f"[r17-prep] FAIL: {msg}")
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
            .replace("R15T-", "R17T-")
            .replace("R15B-", "R17B-")
            .replace("reader-r15", "reader-r17"))


# ---------------------------------------------------------------------------
# 指引生成（确定性机械变换；锚命中数逐一 fail-closed，锚恰 1 次否则 FAIL）
# ---------------------------------------------------------------------------

def build_guidance(base_text: str, *, orange_px: int, green_px: int,
                   void_final_640: int, void_strict_640: int
                   ) -> tuple[str, list[dict]]:
    """由 r15 指引文本生成 r17 指引文本；返回 (r17 文本, edit_list)。"""
    t = base_text
    edits: list[dict] = []

    # ---- 编辑 1（先行）：本轮变更声明节正文整体替换（任务枚举）----
    # 先行原因：声明正文含 r15 自引（r15-prep-record.json / R15T/R15B），
    # 整体替换后轮次标识与旗前缀替换的命中数才收敛为期望值。
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

    # ---- 编辑 3：声明日期 bullet 同步（轮次标识区；s48/s54 先例延伸：
    #      本轮日期常量 2026-09-08→2026-09-09 变动，故显式列出）----
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
    t = _replace_counted(t, "reader-r15", "reader-r17",
                         EXPECTED_HITS["reader_id"], "示例 reader-id")
    edits.append({
        "edit": 6,
        "kind": "示例 reader-id 同步（轮次标识区；s48/s54 机械变换先例）",
        "old": "reader-r15",
        "new": "reader-r17",
        "expected_hits_after_edit_1": EXPECTED_HITS["reader_id"],
        "note": "§6 格式示例 reader_id：reader-r17-top",
    })

    # ---- 编辑 7：示例旗 ID 前缀替换（任务枚举）----
    t = _replace_counted(t, "R15T-", "R17T-",
                         EXPECTED_HITS["prefix_R15T-"], "旗前缀 R15T-")
    t = _replace_counted(t, "R15B-", "R17B-",
                         EXPECTED_HITS["prefix_R15B-"], "旗前缀 R15B-")
    edits.append({
        "edit": 7,
        "kind": "示例旗 ID 前缀替换（任务枚举）",
        "items": [
            {"old": "R15T-", "new": "R17T-",
             "expected_hits": EXPECTED_HITS["prefix_R15T-"]},
            {"old": "R15B-", "new": "R17B-",
             "expected_hits": EXPECTED_HITS["prefix_R15B-"]},
        ],
    })

    # ---- 编辑 8/9/10：§5A 描述性同步（任务枚举；两处=首句+px/出处句；
    #      px 值由 witness-r17 结构探测值经常量复核后注入，不凭记忆写）--
    if (orange_px, green_px) != (EXPECTED_ORANGE_PX_R17, EXPECTED_GREEN_PX_R17):
        _fail(f"witness-r17 成图实测值与冻结常量不符：橙={orange_px}/"
              f"绿={green_px}（立即停止）")
    if (void_final_640, void_strict_640) != (EXPECTED_VOID_FINAL_640,
                                             EXPECTED_VOID_STRICT_640):
        _fail(f"640dpi 期探针参照值与冻结常量不符：{void_final_640}/"
              f"{void_strict_640}（立即停止）")
    t = _replace_counted(t, E1_OLD, E1_NEW, EXPECTED_HITS["e1_old"],
                         "§5A 首句（同步 i）")
    edits.append({
        "edit": 8,
        "kind": "§5A 描述性同步 (i)：首句渲染件语义（任务枚举；仅描述性、"
                "非判据）",
        "old": E1_OLD,
        "new": E1_NEW,
        "expected_hits": EXPECTED_HITS["e1_old"],
    })
    t = _replace_counted(t, E2_OLD, E2_NEW, EXPECTED_HITS["e2_old"],
                         "§5A 橙 px 与出处（同步 ii）")
    edits.append({
        "edit": 9,
        "kind": "§5A 描述性同步 (ii) 之一：橙 px 数值与出处句随仪器更新"
                "（81672→326460；来源 render-witness-r17.json 实测；任务"
                "枚举；仅描述性、非判据）",
        "old": E2_OLD,
        "new": E2_NEW,
        "expected_hits": EXPECTED_HITS["e2_old"],
        "numeric_facts_transcribed": {
            "orange_measured_px_1280": orange_px,
            "orange_measured_px_640_history": EXPECTED_ORANGE_PX_640,
            "source": "render-witness-r17.json palette_assertion_summary",
        },
    })
    t = _replace_counted(t, E3_OLD, E3_NEW, EXPECTED_HITS["e3_old"],
                         "§5A 绿句（同步 ii）")
    edits.append({
        "edit": 10,
        "kind": "§5A 描述性同步 (ii) 之二：绿 px 数值与出处句随仪器更新、"
                "探针句改写（任务枚举；仅描述性、非判据）。任务给定替换文"
                "本「640dpi 期探针值为 206632/206052 px，本轮 1280dpi 实"
                "测绿 903366 px」以语义等价形式落盘——历史出处（转录自 "
                "render-framing-r14b.json probe_block.board_white_coverage）"
                "随探针值括注、实测值括注 render-witness-r17.json 出处，"
                "避免悬置误挂；两条数字子串逐字在位断言（见 "
                "verification.section_assertions_passed）",
        "old": E3_OLD,
        "new": E3_NEW,
        "expected_hits": EXPECTED_HITS["e3_old"],
        "numeric_facts_transcribed": {
            "green_measured_px_1280": green_px,
            "board_void_white_640_final_px": void_final_640,
            "board_void_white_640_strict_px": void_strict_640,
            "sources": ["render-witness-r17.json（e979bec2）",
                        "render-framing-r14b.json（7004b017，历史探针值出处）"],
        },
    })

    return t, edits


def assert_guidance_invariants(base_text: str, t17: str) -> list[str]:
    """§1/§2–§5/§6/§7 分段逐字保留断言 + 关键 substring 断言 + R15/640px
    残留零断言 + 新文本在位断言 + §5A 位置断言。

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
        if norm not in t17:
            _fail(f"{label} 失败：r15 段落（旗前缀规格化后）未在 r17 中逐"
                  f"字保留（立即停止）")
        passed.append(label)

    # ---- 关键 substring 断言 ----
    for label, needle in REQUIRED_SUBSTRING_VALUES.items():
        if needle not in t17:
            _fail(f"关键 substring 断言失败（{label}）：{needle!r} 未在 r17 "
                  f"指引中逐字保留（立即停止）")
        passed.append(label)

    # ---- R15/640dpi px 残留零断言（机械替换完备性；§5A 历史探针值
    #      206632/206052 有意保留可考、不在零断言之列）----
    for needle in ("R15T", "R15B", "reader-r15", "2026-09-08-r15",
                   "2026-09-08", "# R15 轮", "observation-guidance-r15",
                   "81672", "探针板内空隙白 206632", "成图实测绿 206632",
                   "render-witness-r14b.json", "R14b 配色（与 R14 相同",
                   "字节复用同一渲染件"):
        n = t17.count(needle)
        if n != 0:
            _fail(f"残留零断言失败：{needle!r} 在 r17 指引中残留 {n} 次"
                  f"（立即停止）")
    passed.append("R15/640px 残留零断言（R15T/R15B/reader-r15/2026-09-08-r15/"
                  "2026-09-08/# R15 轮/observation-guidance-r15/81672/探针板"
                  "内空隙白 206632/成图实测绿 206632/render-witness-r14b.json/"
                  "R14b 配色（与 R14 相同/字节复用同一渲染件 全部零命中；"
                  "640dpi 期探针历史值 206632/206052 有意保留可考）")

    # ---- 新文本在位断言 ----
    for needle, label, want in (
            (NEW_TITLE, "r17 标题在位", 1),
            (NEW_DECLARATION, "r17 变更声明在位", 1),
            (NEW_NATURE_LINE, "r17 本轮性质行在位", 1),
            ("`2026-09-09-r17`", "r17 round_id_constant bullet 在位", 1),
            (NEW_DATE_LINE, "r17 声明日期 bullet 在位", 1),
            ("R17T-", "r17 旗前缀 R17T- 在位", 4),
            ("R17B-", "r17 旗前缀 R17B- 在位", 1),
            ("reader-r17", "r17 示例 reader-id 在位", 1),
            ("2026-09-09", "r17 日期常量在位（声明日期+round_id 两处）", 2),
            (E1_NEW, "§5A 同步(i) 首句在位", 1),
            (E2_NEW, "§5A 同步(ii) 橙 px 句在位", 1),
            (E3_NEW, "§5A 同步(ii) 绿句在位", 1),
            ("render-witness-r17.json", "witness-r17 出处在位（橙/绿两处）", 2),
            ("render-framing-r14b.json",
             "r14b 历史出处保留（橙 bullet 转录源+绿 bullet 历史探针出处）", 2),
    ):
        n = t17.count(needle)
        if n != want:
            _fail(f"新文本在位断言失败（{label}）：命中 {n} 次 != {want}")
        passed.append(f"{label}（命中 {n}/{want}）")

    # ---- §5A 位置断言（§5 之后、§6 之前）----
    i5 = t17.index("## 5. courtyard 说明（中性）")
    i5a = t17.index(SECTION_5A_HEADING)
    i6 = t17.index("## 6. 输出格式")
    if not (i5 < i5a < i6):
        _fail("§5A 位置断言失败：须位于 §5 之后、§6 之前")
    passed.append("§5A 位置断言（§5 < §5A < §6）")
    return passed


# ---------------------------------------------------------------------------
# 结构探测（fail-closed；仪器事实转录源与判据冻结值锚）
# ---------------------------------------------------------------------------

def probe_framing(framing: dict) -> dict:
    """render-framing-r17：单变量声明与探针可行性（fail-closed）。"""
    if framing.get("kind") != "tl2_calibration_render_framing_r17_preregistration":
        _fail("render-framing-r17 kind 不符")
    if framing.get("round_id_constant") != ROUND_ID:
        _fail(f"render-framing-r17 round_id_constant 不符："
              f"{framing.get('round_id_constant')}")
    if framing.get("date_constant") != DATE_CONSTANT:
        _fail("render-framing-r17 date_constant != 2026-09-09")
    if framing.get("axis_reference", {}).get("expected_prefix") != AXIS_PLAN_SHA_PREFIX:
        _fail("render-framing-r17 axis_reference 期望前缀 != b6ec6467")
    cc = framing.get("compose_and_crop", {})
    if cc.get("dpi") != 1280 or cc.get("dpi_previous") != 640:
        _fail(f"framing dpi 不符：{cc.get('dpi_previous')}→{cc.get('dpi')}")
    if cc.get("crop_margin_px") != 240 or cc.get("crop_margin_px_previous") != 120:
        _fail(f"framing 裁剪边距不符：{cc.get('crop_margin_px_previous')}→"
              f"{cc.get('crop_margin_px')}")
    mc = framing.get("single_variable_change", {}).get("margin_conversion", {})
    if (mc.get("px_1280"), mc.get("px_640"), mc.get("physical_inch")) != \
            (240, 120, 0.1875):
        _fail(f"framing margin_conversion 物理等值不符：{mc}")
    svc = framing.get("single_variable_change", {}).get("declaration", "")
    if "只改变一个仪器变量" not in svc or "1280" not in svc:
        _fail("framing single_variable_change.declaration 缺单变量声明关键语")
    if framing.get("probe_conclusion", {}).get("feasible") is not True:
        _fail("framing probe_conclusion.feasible 不为真（s62 探针未 PASS）")
    if framing.get("freeze_order", {}).get("declaration") is None:
        _fail("framing freeze_order.declaration 缺失")
    return {"dpi": cc.get("dpi"), "dpi_previous": cc.get("dpi_previous")}


def probe_witness(witness: dict, *, framing_sha: str, axis_sha: str) -> dict:
    """render-witness-r17：配色语义/成图实测调色板/640 参照值/登记 sha。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r17":
        _fail("render-witness-r17 kind 不符")
    if witness.get("round_id_constant") != ROUND_ID:
        _fail(f"render-witness-r17 round_id_constant 不符："
              f"{witness.get('round_id_constant')}")
    if witness.get("date_constant") != DATE_CONSTANT:
        _fail("render-witness-r17 date_constant != 2026-09-09")
    if witness.get("framing", {}).get("sha256") != framing_sha:
        _fail("witness.r17 framing 登记 sha 与实测不符（framing 链破坏）")
    if witness.get("framing", {}).get("unchanged_during_render") is not True:
        _fail("witness framing.unchanged_during_render 不为真")
    if witness.get("axis_reference", {}).get("sha256") != axis_sha:
        _fail("witness axis_reference 登记 sha 与 axis-plan 实测不符")
    mapping = witness.get("r14b_references", {}).get("color_mapping_r14b", {})
    if mapping.get("orange_rgb") != EXPECTED_ORANGE_RGB:
        _fail(f"witness r14b 橙配色语义不符：{mapping.get('orange_rgb')}")
    if mapping.get("green_rgb") != EXPECTED_GREEN_RGB:
        _fail(f"witness r14b 绿配色语义不符：{mapping.get('green_rgb')}")
    summary = witness.get("palette_assertion_summary", {})
    palette = {}
    for state in ("applied", "prep1"):
        item = summary.get(state, {})
        if item.get("assertions_pass") is not True:
            _fail(f"witness {state} palette_assertions_pass 不为真")
        if item.get("white_in_board_after") != EXPECTED_WHITE_IN_BOARD:
            _fail(f"witness {state} 板内白清零断言不符："
                  f"{item.get('white_in_board_after')}")
        if item.get("orange_green_mix_count") != 0:
            _fail(f"witness {state} 橙绿零交集断言不符")
        palette[state] = {
            "orange_exact_count": item.get("orange_exact_count"),
            "green_exact_count": item.get("green_exact_count"),
        }
    if palette["applied"] != palette["prep1"]:
        _fail(f"witness 两板成图实测调色板不一致：{palette}")
    if palette["applied"]["orange_exact_count"] != EXPECTED_ORANGE_PX_R17:
        _fail(f"witness 橙像素计数不符："
              f"{palette['applied']['orange_exact_count']} != "
              f"{EXPECTED_ORANGE_PX_R17}")
    if palette["applied"]["green_exact_count"] != EXPECTED_GREEN_PX_R17:
        _fail(f"witness 绿像素计数不符："
              f"{palette['applied']['green_exact_count']} != "
              f"{EXPECTED_GREEN_PX_R17}")
    for state in ("applied-top", "prep1-top"):
        item = summary.get(state, {})
        if item.get("orange_exact_count") != 0 or item.get("green_exact_count") != 0:
            _fail(f"witness {state} top 无配色断言不符（橙/绿应=0）")
    p640 = witness.get("r14b_references", {}).get("palette_640_measured", {})
    if p640.get("orange_exact_count") != EXPECTED_ORANGE_PX_640:
        _fail(f"witness 640 期橙参照值不符：{p640.get('orange_exact_count')}")
    if p640.get("green_exact_count") != EXPECTED_GREEN_PX_640:
        _fail(f"witness 640 期绿参照值不符：{p640.get('green_exact_count')}")
    if p640.get("white_in_board_after") != EXPECTED_WHITE_IN_BOARD:
        _fail("witness 640 期板内白参照值不符（应为 0）")
    rendered = witness.get("renders", {})
    registered = {
        "applied-bottom": (rendered.get("applied", {}) or {}).get("sha256"),
        "prep1-bottom": (rendered.get("prep1", {}) or {}).get("sha256"),
        "applied-top": (rendered.get("applied-top", {}) or {}).get("sha256"),
        "prep1-top": (rendered.get("prep1-top", {}) or {}).get("sha256"),
    }
    for side, sha in registered.items():
        if not isinstance(sha, str) or len(sha) != 64:
            _fail(f"witness {side} 见证登记值缺失或非 64 位 sha256：{sha!r}")
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（两板 bottom 逐字节同"
              "事实口径不一致）")
    mask = (rendered.get("applied", {}) or {}).get("mask_rebuild", {})
    if (mask.get("rebuilt_white_fill_drawings"),
            mask.get("rebuilt_white_stroke_drawings")) != (
            EXPECTED_WHITE_FILL_COUNT, EXPECTED_WHITE_STROKE_COUNT):
        _fail(f"witness 1280 白墨矢量重建计数不符：fill="
              f"{mask.get('rebuilt_white_fill_drawings')}/stroke="
              f"{mask.get('rebuilt_white_stroke_drawings')}")
    return {
        "orange_px": palette["applied"]["orange_exact_count"],
        "green_px": palette["applied"]["green_exact_count"],
        "void_final_640": p640.get("green_exact_count"),
        "void_strict_640": EXPECTED_VOID_STRICT_640,
        "registered": registered,
    }


def check_renders(registered: dict) -> list[dict]:
    """渲染仪器实测：四 PNG magic+sha256_file 实测 vs witness 登记值。"""
    expect_prefix = {
        "applied-bottom": R17_BOTTOM_SHA_PREFIX,
        "prep1-bottom": R17_BOTTOM_SHA_PREFIX,
        "applied-top": R17_APPLIED_TOP_SHA_PREFIX,
        "prep1-top": R17_PREP1_TOP_SHA_PREFIX,
    }
    results = []
    for side in RENDERS_SIDES:
        path = CAL_DIR / "renders-r17" / f"{side}.png"
        if not path.exists():
            _fail(f"PNG 缺失：{path}")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        expect = registered[side]
        if measured != expect:
            _fail(f"renders-r17/{side}.png 实测 sha256 与 witness 登记值不"
                  f"符（仪器见证链破坏）：measured={measured} "
                  f"registered={expect}")
        if not measured.startswith(expect_prefix[side]):
            _fail(f"renders-r17/{side}.png sha 前 8={measured[:8]} != 预期 "
                  f"{expect_prefix[side]}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r17/{side}.png",
            "sha256_measured": measured,
            "witness_record": "out/v3-tl2/calibration/render-witness-r17.json",
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "renders." + side + ".sha256"),
            "sha256_witness_registered": expect,
            "match": True,
        })
    return results


def probe_axis_plan(plan: dict, plan_sha: str) -> dict:
    """axis-experiment-plan-r17-r20：stage1 R17 定义与判据数值锚。"""
    if plan.get("kind") != "tl2_axis_experiment_plan_development":
        _fail("axis-plan kind 不符")
    if plan.get("declared_date") != DATE_CONSTANT:
        _fail("axis-plan declared_date != 2026-09-09")
    if plan.get("idempotence", {}).get("canonical_bytes_sha256") is None:
        _fail("axis-plan idempotence 节缺失")
    axes = plan.get("axes", [])
    if not axes or axes[0].get("axis_id") != "A1_render_resolution_x2":
        _fail("axis-plan axes[0].axis_id != A1_render_resolution_x2")
    rounds = plan.get("stage1_rounds", {}).get("rounds", [])
    if not rounds or rounds[0].get("round_id") != "R17":
        _fail("axis-plan stage1 rounds[0].round_id != R17")
    if rounds[0].get("axis_id") != "A1_render_resolution_x2":
        _fail("axis-plan R17 axis_id 不符")
    if "仪器轮" not in (rounds[0].get("round_nature") or ""):
        _fail("axis-plan R17 round_nature 缺「仪器轮」")
    r16_base = plan.get("baselines_registered", {}).get("r16_baseline", {})
    if r16_base.get("M1_top_aggregate_abstain_rate") != M1_R16_BASELINE:
        _fail(f"axis-plan r16 基线 M1 不符："
              f"{r16_base.get('M1_top_aggregate_abstain_rate')} != "
              f"{M1_R16_BASELINE}")
    sig = plan.get("comparison_rule", {}).get(
        "significant_benefit_definition", "")
    if "≥0.10" not in sig:
        _fail(f"axis-plan 显著收益定义缺 ≥0.10：{sig!r}")
    guards = plan.get("guards", {})
    for gid in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                "G3_freeze_discipline"):
        if gid not in guards:
            _fail(f"axis-plan 守门缺失：{gid}")
    if plan.get("early_stop_rule", {}).get("guard_failure_exit") is None:
        _fail("axis-plan early_stop_rule.guard_failure_exit 缺失")
    quote = (plan.get("user_directive_note", {}) or {}).get("user_quote")
    if quote != "三条轴单独/组合/全组合尝试，选择收益最大的继续":
        _fail(f"axis-plan 用户指令原文不符：{quote!r}")
    # 判据数值自洽：supported 阈值 = r16 基线 − 显著收益阈值
    if round(M1_R16_BASELINE - SIGNIFICANT_BENEFIT_DELTA, 6) != \
            M1_SUPPORTED_THRESHOLD:
        _fail("判据数值自洽断言失败：0.771429-0.10 != 0.671429")
    for needle in ("0.671429", "0.771429", "≥0.10"):
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值 {needle}（逐字要求破坏）")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": plan_sha,
        "field": "stage1_rounds.rounds[0]",
        "round_quote": rounds[0],
    }


def probe_run_r16(run: dict, run_sha: str) -> dict:
    """calibration-run-r16：M1 冻结值与 guard_ok 锚（仅读判据值字段）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r16 hypothesis_test 结构不符")
    if ht.get("hypothesis_id") != "r15-dev-record-candidate-0-same-guidance-repeat":
        _fail("calibration-run-r16 hypothesis_test.hypothesis_id 不符")
    if ht.get("verdict") != "inconclusive":
        _fail("calibration-run-r16 verdict 不符（应为 inconclusive）")
    m = ht.get("measurement", {})
    if m.get("top_abstain_rate_r16") != M1_R16_BASELINE:
        _fail(f"run-r16 top_abstain_rate_r16 不符："
              f"{m.get('top_abstain_rate_r16')} != {M1_R16_BASELINE}")
    if (m.get("top_abstain_count_r16"), m.get("top_abstain_flags_r16")) != \
            (M1_R16_TOP_COUNT, M1_R16_TOP_FLAGS):
        _fail(f"run-r16 top 旗数不符：{m.get('top_abstain_count_r16')}/"
              f"{m.get('top_abstain_flags_r16')} != "
              f"{M1_R16_TOP_COUNT}/{M1_R16_TOP_FLAGS}")
    gc = m.get("guard_channel", {})
    if gc.get("guard_ok") is not True:
        _fail("run-r16 guard_ok 不为真（G2 基线证据不符）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r16.json",
        "sha256_measured": run_sha,
        "frozen_values": (f"top {M1_R16_TOP_COUNT}/{M1_R16_TOP_FLAGS}="
                          f"{M1_R16_BASELINE}（r16 零变更基线 M1）；"
                          "guard_ok=True——hypothesis_test 判据文本数值的"
                          "在案锚（GT 匹配与逐旗明细不读取）"),
    }


def probe_dev_record(dev: dict, dev_sha: str, r16_record_sha: str) -> dict:
    """round16-dev-record：链证据与 r16-prep-record 登记 sha 交叉核对。"""
    hti = dev.get("hypothesis_test_i", {})
    if hti.get("verdict") != "inconclusive":
        _fail("round16-dev-record verdict 不符")
    m = hti.get("measurement", {})
    if m.get("top_abstain_rate_r16") != M1_R16_BASELINE:
        _fail("round16-dev-record top_abstain_rate_r16 不符")
    g1 = (m.get("bottom_side_observation", {}) or {}).get(
        "bottom_courtyard_non_abstain_by_instance_r16")
    if g1 is None:
        g1 = ((hti.get("mechanism_observation", {}) or {})
              .get("bottom_side_observation_maintenance", {})
              .get("counts", {})
              .get("r16_bottom_courtyard_non_abstain_by_instance"))
    if g1 != {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail(f"round16-dev-record G1 基线证据不符：{g1}")
    preref = hti.get("preregistration_ref", {})
    if preref.get("sha256") != r16_record_sha:
        _fail(f"r16-prep-record 实测 sha 与 round16-dev-record 登记值不符："
              f"measured={r16_record_sha} registered={preref.get('sha256')}")
    return {
        "path_rel": "out/v3-tl2/calibration/round16-dev-record.json",
        "sha256_measured": dev_sha,
        "g1_baseline_evidence": "r16 非弃权 courtyard 0/0/0 维持在案；"
                                "verdict=inconclusive（带内落点）",
        "r16_prep_record_registered_sha256": preref.get("sha256"),
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance15_sha: str, guidance17_sha: str,
                 guidance15_bytes: int, guidance17_bytes: int,
                 r15_record_sha: str, r16_record_sha: str,
                 dev_probe: dict, run_probe: dict, axis_probe: dict,
                 framing_sha: str, witness_sha: str, protocol_sha: str,
                 png_checks: list[dict], edit_list: list[dict],
                 section_asserts: list[str]) -> dict:
    """构建 r17-prep-record 内容（纯函数：同入参必得同 dict）。"""
    axis_rel = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r17_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r17",
        "round_nature": (
            "轴1 仪器轮（渲染分辨率倍增 640→1280dpi，四图全部；axis-"
            "experiment-plan-r17-r20 stage1 之一，第十七轮）：判读指引由 "
            "observation-guidance-r15.md 机械变换生成 observation-"
            "guidance-r17.md（本轮唯一判读依据；指引侧变更=轮次标识机械同"
            "步+本轮变更声明重写+§5A 描述性同步（配色 px 数与出处句随仪器"
            "更新，两处、仅描述性非判据），见 guidance_reuse.edit_list）；"
            "§2–§7 判据文本逐字承 r15（分段+substring 双重断言复核）、反"
            "放宽条款与三路出口逐字保留；仪器变更=renders-r17 四图全新渲"
            "染（dpi 640→1280、r14b 配色规则重放、margin 240px 物理等值；"
            "非字节复用；s62 仪器包产物只读引用，四 PNG sha256_file 实测"
            "与 render-witness-r17.json 登记值 fail-closed 比对一致，见 "
            "instrument_change）；GT/阈值/协议零变更（v1.1+v1.2 维持）；"
            "执行 axis-experiment-plan-r17-r20（b6ec6467 冻结件）stage1 "
            "R17=轴1（A1_render_resolution_x2，实测链见 "
            "changed_variables[0].preregistration_ref），用户 2026-09-09"
            "「三条轴单独/组合/全组合尝试，选择收益最大的继续」（见 "
            "user_directive_note）；r15 指引已在盘冻结、本轮只读零写入；"
            "盲读由编排侧在本记录之后以 12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的"
            "继续」=授权执行 axis-experiment-plan-r17-r20（b6ec6467 冻结"
            "件，先于 R17–R21 任何实验轮盲读冻结以防事后择优）stage1 "
            "R17=轴1 渲染分辨率倍增轮；本记录=该轮 prep-record 预注册（先"
            "于任何盲读冻结）；比较与组合决策以冻结件 comparison_rule/"
            "combination_decision_rule 为准（显著收益=相对 r16 基线 M1 绝"
            "对降幅 ≥0.10）；判据零改动、既往轮次字母不回写（r8–r16 维持"
            "不变）"),
        "instrument_change": {
            "changed": True,
            "note": "renders-r17 新渲染（1280dpi）；非字节复用",
            "axis_id": "A1_render_resolution_x2",
            "renders": png_checks,
            "witness": ("render-witness-r17.json（e979bec2，fail-closed "
                        "复核）"),
            "declaration": (
                "四 PNG 由 s62 仪器包生成并冻结（framing 预注册 a1084c14→"
                "成图→witness 见证 e979bec2→diag 对照裁片）；本轮 prep 零"
                "重渲染、零 out/ 既有文件改动（四 PNG sha256_file 实测="
                "witness 登记值；bottom 两板逐字节同 0c2d5c00；top 无配色）"),
        },
        "no_instrument_change": False,
        "guidance_reuse": {
            "base": "observation-guidance-r15.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r15.md"),
            "base_sha256": guidance15_sha,
            "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
            "mode": "mechanical_transform_derive",
            "derived": "observation-guidance-r17.md",
            "derived_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r17.md"),
            "derived_sha256": guidance17_sha,
            "byte_size": {"base": guidance15_bytes,
                          "derived": guidance17_bytes,
                          "delta": guidance17_bytes - guidance15_bytes},
            "edit_list": edit_list,
            "verbatim_frozen_sections": (
                "§2 类别枚举、§3 位置口径、§3A 类别判据示例（含示例 c 与末"
                "尾对照说明）、§4 置信度与弃权（含量化判据 (i)(ii)(iii)、"
                "接触性判据、三路出口、反放宽条款、r6/r8/r13 对照说明块）、"
                "§5 courtyard 说明、§6 输出格式（旗 ID 展示前缀机械替换除"
                "外）、§7 格式对齐提示、§1 角色与任务——分段逐字保留断言"
                "（r15 段落 substring-in 断言）+关键 substring 断言双重复"
                "核，见 verification.section_assertions_passed；§5A 渲染配"
                "色仪器注记除两处描述性同步（edit 8/9/10）外逐字承 r15（非"
                "图元声明、非判据声明、top 无配色句零改动，substring 断言"
                "复核）"),
            "lineage_note": (
                "轮次标识区同步（标题行/声明日期 bullet/round_id_constant "
                "bullet/本轮性质行/示例 reader_id/示例旗 ID 前缀）沿 "
                "s48_calibration_r13_prep.py→s54_calibration_r15_prep.py"
                "（指引侧轮机械变换）先例；任务枚举编辑全部逐字执行，非任"
                "务枚举的轮次标识同步项（edit 3/5/6）在 edit_list 中如实登"
                "记——声明日期 bullet 为本轮新增同步项（r13→r15 时日期未"
                "变故先例无此项），已如实披露；§1 与头部 bullet 区不在逐字"
                "冻结清单（冻结区=§2–§7）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
                "r15_prep_record_schema_template": {
                    "path_rel": "out/v3-tl2/calibration/r15-prep-record.json",
                    "sha256": r15_record_sha,
                },
                "r16_prep_record_mirror_source": {
                    "path_rel": "out/v3-tl2/calibration/r16-prep-record.json",
                    "sha256": r16_record_sha,
                    "cross_check": "实测 sha 与 round16-dev-record "
                                   "hypothesis_test_i.preregistration_ref."
                                   "sha256 登记值逐字相等",
                },
                "render_framing_r17_single_variable_declaration": {
                    "path_rel": "out/v3-tl2/calibration/render-framing-r17.json",
                    "sha256": framing_sha,
                },
                "render_witness_r17_px_source": {
                    "path_rel": "out/v3-tl2/calibration/render-witness-r17.json",
                    "sha256": witness_sha,
                },
                "axis_experiment_plan_frozen": {
                    "path_rel": axis_rel,
                    "sha256": axis_probe["sha256_measured"],
                },
                "round16_dev_record_chain": dev_probe,
                "run_r16_baseline_anchor": run_probe,
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
                "id": "render-resolution-x2-r17",
                "axis": "instrument",
                "axis_id": "A1_render_resolution_x2",
                "instrument_change": True,
                "target": (
                    "renders-r17 四图（out/v3-tl2/calibration/renders-r17/"
                    "；1280dpi 全新渲染，r14b 配色规则重放；非字节复用）"),
                "description": (
                    "渲染分辨率倍增（640→1280dpi，四图全部；线度×2、像素"
                    "数×4；margin 240px 物理等值=120px×2=0.1875in；r14b 配"
                    "色规则逐字重放：白墨矢量图元 mask→橙 (255,165,0)、板"
                    "内空隙白 mask→绿 (0,128,0)，mask 于 1280 像密度重算，"
                    "z 序/混合数学不变；单变量声明=render-framing-r17.json "
                    "single_variable_change）；成图实测橙 326460/绿 903366/"
                    "板内白 0（render-witness-r17.json，两板相同）"),
                "attribution_channel": (
                    "M1（top 全旗聚合弃权率，12 派次全口径）主判据="
                    "hypothesis_test.adjudication 三支（supported ≤0.671429"
                    "/marginal 带内/reject ≥0.771429）；守门=G1（bottom "
                    "courtyard 非弃权 0/0/0 维持）+G2（guard_ok=True），任"
                    "一破坏→轴1 按 plan early_stop_rule 出局（字母照实+出"
                    "局声明）"),
                "preregistration_ref": {
                    "path_rel": axis_rel,
                    "sha256_measured": axis_probe["sha256_measured"],
                    "field": axis_probe["field"],
                    "round_quote": axis_probe["round_quote"],
                },
            },
            {
                "id": "guidance-5a-descriptive-px-sync",
                "axis": "guidance",
                "instrument_change": False,
                "target": "observation-guidance-r17.md §5A（两处描述性同步）",
                "description": (
                    "(i) 首句：「本轮 bottom 渲染采用 R14b 配色（与 R14 相"
                    "同，字节复用同一渲染件）」→「本轮 bottom 渲染采用 "
                    "R14b 配色规则（与 R14/R15/R16 同一配色语义；本轮渲染"
                    "件为 1280dpi 新渲染，非字节复用）」；(ii) px 数与出处"
                    "句随仪器更新：橙 81672→326460、绿 206632→903366（数字"
                    "来源=render-witness-r17.json palette_assertion_summary "
                    "实测，脚本 fail-closed 装载）；「探针板内空隙白 206632 "
                    "px（final 口径）/ 206052 px（严格口径）」句改写为「"
                    "640dpi 期探针值为 206632/206052 px（final 口径/严格口"
                    "径，转录自 render-framing-r14b.json probe_block.board_"
                    "white_coverage，历史值保持可考），本轮 1280dpi 实测绿 "
                    "903366 px」——仅描述性仪器事实同步、非判据；§5A 其余"
                    "文字（非图元声明、非判据声明、top 无配色）逐字保留"),
            },
            {
                "id": "round-identity-sync",
                "axis": "guidance",
                "instrument_change": False,
                "target": "observation-guidance-r17.md 头部与 §6 示例",
                "description": (
                    "标题行 R15→R17、声明日期 bullet 2026-09-08→2026-09-09、"
                    "round_id_constant bullet 2026-09-08-r15→2026-09-09-r17、"
                    "本轮性质行按轴1 仪器轮口径重写、示例 reader_id "
                    "reader-r15→reader-r17、示例旗 ID 前缀 R15T-（4 处）/"
                    "R15B-（1 处）→R17T-/R17B-——s48/s54 机械变换先例轮次"
                    "标识区同步，如实登记"),
            },
        ],
        "manipulated_factor": (
            "渲染分辨率（640→1280dpi，四图全部；唯一仪器实验变量，axis-plan "
            "stage1 R17=A1_render_resolution_x2）；判据文本/GT/阈值/协议零"
            "变更（指引侧仅描述性同步与轮次标识机械同步）"),
        "unchanged_components": [
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
            "§6 输出格式：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r15 指引原文；仅旗 ID 展示前缀 R15T-/R15B-→R17T-/"
            "R17B- 机械替换，随指引落盘固化、无需派发层覆盖）",
            "§7 格式对齐提示（r15 指引原文逐字）",
            "§5A 渲染配色仪器注记：除两处描述性同步（首句渲染件语义、px "
            "数与出处句）外逐字承 r15（非图元声明、非判据声明、top 无配色"
            "句零改动）——描述性同步不触碰任何判据语义",
            "§1 角色与任务与盲读纪律（r15 指引原文逐字；不在冻结清单亦零"
            "改动，分段断言复核）",
            "渲染产物 renders-r17 四图+render-framing-r17/render-witness-"
            "r17/diag-r17-render：s62 仪器包在盘冻结，本轮 prep 零重渲染、"
            "零改动（四 PNG sha256_file 实测=witness 登记值，见 "
            "instrument_change.renders）",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r16 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染侧唯一变量=分辨"
            "率，配色语义与 r14b 相同）",
            "度量设计五条与聚合口径：沿 r16-prep-record measurement_design"
            ".items 同一口径（仅轮次标识、reader 前缀与渲染件名按 r17 改"
            "写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r17（1280dpi 全新渲染；非字节复"
            "用）：r14b 配色规则逐字重放（白墨图元→橙 (255,165,0)、板内空"
            "隙白→绿 (0,128,0)、其余层 kicad 原配色不变；mask 在 1280 像密"
            "度重算（白墨矢量重建 fill 162+stroke 4 不变），z 序/混合数学"
            "不变，per render-framing-r17 single_variable_change）；成图实"
            "测橙 326460 px/绿 903366 px/板内白 0（render-witness-r17.json "
            "palette_assertion_summary，两板相同；640dpi 期值为 81672/"
            "206632）——§5A px 数已随仪器更新（指引侧描述性同步、非判据）"
            "；两板 bottom 成图逐字节同（0c2d5c00）；top 渲染无配色（本轮 "
            "top 亦为 1280dpi 原生重渲染，属同一单变量「分辨率」在 top 的"
            "应用）；bottom 视判读口径沿用 r4 指引原文不改（top/bottom 判"
            "读口径在图像空间完全一致、不做镜像换算）；bottom 零旗标分母="
            "0 时弃权率按 cal._ratio 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R17 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r16-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R17T/R17B；"
                "图像=renders-r17 四图；聚合口径与 s55_calibration_r15_"
                "compare.py 同一比较脚本血统；代表配置/逐实例/双口径分列）"),
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
                "本轮恰一个操纵因子（渲染分辨率 640→1280dpi 四图全部）、检"
                "验恰一个假设（axis-experiment-plan-r17-r20 stage1 R17=轴"
                "1；hypothesis_id=axis-plan-r17-resolution-double）；归因"
                "目的=top（及 bottom）contact/存在性族弃权是否源于 640dpi "
                "分辨率瓶颈的分型件假设首验；跨轮对比（vs r16 零变更基线 "
                "M1=0.771429）按冻结件 comparison_rule（显著收益=绝对降幅 "
                "≥0.10，跨轮实例群漂移混杂显式容忍、参照 r15→r16 纯重抽变"
                "动 0.09064）；bottom 侧观察单列（mechanism_observation_"
                "separate，不影响字母）；字母/机制观察/度量教训三分记账"
                "（adjudication.mechanism_observation_separate 与 metric_"
                "lesson_separate 单列，不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "render-resolution-2x（仪器侧唯一操纵；非指引判据/GT/"
                    "阈值/协议变更）"),
                "metric": (
                    "M1（top 全旗聚合弃权率，12 派次全口径）三分判据见 "
                    "hypothesis_test.adjudication：supported ≤0.671429（相"
                    "对 r16 零变更基线 0.771429 绝对降幅 ≥0.10=计划件显著"
                    "收益阈值）；marginal 0.671429<M1<0.771429；reject "
                    "M1≥0.771429（轴1 证伪）"),
                "supported": (
                    "M1 ≤ 0.671429 → 分辨率瓶颈实锤（轴1 supported）"),
                "marginal": (
                    "0.671429 < M1 < 0.771429 → 记 marginal，轴1 不判定为"
                    "胜出（与跨轮漂移噪声不可分）"),
                "reject": (
                    "M1 ≥ 0.771429 → 轴1 证伪：分辨率非瓶颈（或视觉编码器"
                    "尺寸上限抵消增益，机制观察须记录读者实际可见细节的自"
                    "述）；转向轴2/轴3"),
            },
            "guard_channel": {
                "metric": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15/r16 "
                    "在案 0/0/0，round16-dev-record 实测装载校验通过）；"
                    "G2=guard_ok=True 维持（top 视非弃权旗标 frame_box_pct "
                    "几何门，面积比出局条目按 guard_channel 如实登记）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r17 指引 §2–§7 逐字承 r15，分段"
                    "断言复核），非弃权框仍须满足；任一守门破坏→轴1 按 "
                    "plan early_stop_rule 出局（字母照实+出局声明）"),
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
            "言复核）；§5A 两处为描述性仪器事实同步（配色 px 数与出处句随"
            "渲染仪器 640→1280dpi 更新：橙 81672→326460、绿 206632→"
            "903366、探针句改「640dpi 期探针值为 206632/206052 px+本轮 "
            "1280dpi 实测绿 903366 px」——px 数为仪器侧像素计数事实、非判"
            "据，不构成任何「应判正常/无需报告」的指示，不降低任何存在性、"
            "归类、定位或报告的责任门槛；反放宽条款「仅因形态不熟悉、不确"
            "定其设计含义，不构成判为正常设计特征的理由」与三路出口显式化"
            "在 r17 指引 §4 内逐字保留（fail-closed substring 断言）；M1 "
            "阈值 0.671429/0.771429 等本轮判据只用于轴1 收益方向归因"
            "（axis-experiment-plan-r17-r20 冻结比较规则），不触碰 APR-"
            "0011 门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤"
            "0.5）与任何阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX，只作口"
            "径引用）——门照常独立计算；不构成任何阈值反向放宽"),
        "pre_round_review": {
            "status": "satisfied_by_probe_and_plan",
            "basis": (
                "s62 探针 PASS（render-framing-r17 probe_conclusion."
                "feasible=true；板界 ×2±2px/裁剪白边 240px/配色 4× 带内/"
                "板内白清零断言全过）+诊断裁片主审亲自核验（diag-r17-render/"
                "：bottom 基准黑点-焊盘邻域与 top 相邻 courtyard 对，"
                "640(2× 最近邻放大)/1280 并排对照）+axis-experiment-plan-"
                "r17-r20 冻结（b6ec6467）"),
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
                    "v1 原文零字节保留（r11–r16 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-"
                "r17.md）+单张 PNG（renders-r17 四图）+派发命名指令（含 "
                "v1.2 工具行为规约硬性条款：纯 Read 内联判读、禁止任何程"
                "序化图像处理），零 GT、零历史判读件、零诊断/探针内容（含 "
                "diag-r17-render 对照裁片——其为主审核验件、非 reader 上"
                "下文）；两波次串行保序（同一实例先 applied 后 prep1，"
                "flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r17-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R17T/R17B（r17 指引 §6 已机械替换落盘 R17T-/R17B-——本轮"
                "指引本体即为 r17 前缀，无需派发层覆盖）；实例间编号独立，"
                "同实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic，零内容判读、零像素读取；diag-r17-render 对照裁片仅存"
            "在性核验、零内容读取）、ground-truth-*、reader-raw-*、"
            "derivation-log-*、任何 compare/评估产物；本脚本只读输入="
            "observation-guidance-r15.md（r17 指引的唯一变换基座；d5babc93 "
            "锚 fail-closed，零写入）、r15-prep-record.json（链锚=4c6cd919 "
            "先验证；schema 模板）、r16-prep-record.json（链锚=46fbd15b，"
            "与 round16-dev-record 登记值交叉核对；24 键结构镜像来源）、"
            "round16-dev-record.json（589fe62f 锚；仅读取 hypothesis_test_i "
            "verdict/M1/守门基线证据/preregistration_ref 登记 sha 字段）、"
            "calibration-run-r16.json（2c1f8265 锚；仅读取 hypothesis_test "
            "顶层判据冻结值字段做 fail-closed 锚定——M1=0.771429、top "
            "27/35、guard_ok=True；其 GT 匹配与逐旗明细内容不读取、不入记"
            "录）、render-framing-r17.json（a1084c14 锚；单变量声明与探针"
            "可行性）、render-witness-r17.json（e979bec2 锚；§5A px 数值"
            "事实转录源：橙 326460/绿 903366/板内白 0、640 期参照 81672/"
            "206632）、axis-experiment-plan-r17-r20.json（b6ec6467 锚；"
            "stage1 R17 定义、r16 基线、显著收益定义、守门、用户指令原文）、"
            "evaluation-protocol-v1.md（仅在盘+哈希复核，锚=22dc7337）；"
            "renders-r17 四 PNG 仅哈希+magic（仪器见证以 witness 登记哈希"
            "比对为准）；observation-guidance-r17.md 与 r17-prep-record."
            "json 为本轮仅有的两个 out/ 新建文件（scripts/s63_calibration_"
            "r17_prep.py 为生成器本体，亦即本轮第三个新文件）；reader 派发"
            "（后续编排侧执行）上下文=observation-guidance-r17.md+单张 "
            "PNG（renders-r17）+派发指令（R17T/R17B 前缀、reader-r17-"
            "{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬性条款），零 GT、"
            "零历史判读件、零诊断/探针内容、零 legend 之外的解释；视觉判"
            "读禁止由编排/收口包兼任；跨实例/跨视角禁止交流（12 次盲读相"
            "互独立、不得交换判读信息——独立性是多实例协议的前提，亦为轴"
            "1 收益裁决有效性的前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R15, R15_PREP_RECORD, R16_PREP_RECORD,
                 ROUND16_DEV_RECORD, RUN_R16, FRAMING_R17, WITNESS_R17,
                 AXIS_PLAN, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not DIAG_R17_DIR.is_dir():
        _fail(f"缺失诊断裁片目录：{DIAG_R17_DIR}")
    if not (DIAG_R17_DIR / "manifest.json").exists():
        _fail("diag-r17-render/manifest.json 缺失（主审核验件在案性不符）")
    # 目标文件（GUIDANCE_R17/RECORD）不做前置硬拒绝：落盘阶段防覆写守卫
    # 按红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→
    # 幂等通过（零覆写）。（首轮创建前置=两目标不存在，已由编排侧确认。）

    # ---- 冻结锚验证（fail-closed）----
    r15_record_sha = _sha(R15_PREP_RECORD)
    r16_record_sha = _sha(R16_PREP_RECORD)
    dev_record_sha = _sha(ROUND16_DEV_RECORD)
    run_r16_sha = _sha(RUN_R16)
    framing_sha = _sha(FRAMING_R17)
    witness_sha = _sha(WITNESS_R17)
    axis_sha = _sha(AXIS_PLAN)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    if not r15_record_sha.startswith(R15_PREP_RECORD_SHA_PREFIX):
        _fail(f"r15-prep-record sha 前 8={r15_record_sha[:8]} != 预期 "
              f"{R15_PREP_RECORD_SHA_PREFIX}（schema 模板锚不符，立即停止）")
    if not r16_record_sha.startswith(R16_PREP_RECORD_SHA_PREFIX):
        _fail(f"r16-prep-record sha 前 8={r16_record_sha[:8]} != 预期 "
              f"{R16_PREP_RECORD_SHA_PREFIX}（24 键镜像源锚不符，立即停止）")
    if not dev_record_sha.startswith(ROUND16_DEV_RECORD_SHA_PREFIX):
        _fail(f"round16-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{ROUND16_DEV_RECORD_SHA_PREFIX}（链锚不符，立即停止）")
    if not run_r16_sha.startswith(RUN_R16_SHA_PREFIX):
        _fail(f"calibration-run-r16 sha 前 8={run_r16_sha[:8]} != 预期 "
              f"{RUN_R16_SHA_PREFIX}（判据实测值在案处锚不符，立即停止）")
    if not framing_sha.startswith(FRAMING_R17_SHA_PREFIX):
        _fail(f"render-framing-r17 sha 前 8={framing_sha[:8]} != 预期 "
              f"{FRAMING_R17_SHA_PREFIX}（仪器预注册锚不符，立即停止）")
    if not witness_sha.startswith(WITNESS_R17_SHA_PREFIX):
        _fail(f"render-witness-r17 sha 前 8={witness_sha[:8]} != 预期 "
              f"{WITNESS_R17_SHA_PREFIX}（仪器见证锚不符，立即停止）")
    if not axis_sha.startswith(AXIS_PLAN_SHA_PREFIX):
        _fail(f"axis-experiment-plan sha 前 8={axis_sha[:8]} != 预期 "
              f"{AXIS_PLAN_SHA_PREFIX}（实验计划冻结锚不符，立即停止）")
    if not protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX):
        _fail(f"evaluation-protocol-v1.md sha 前 8={protocol_sha[:8]} != 预"
              f"期 {EVAL_PROTOCOL_V1_SHA_PREFIX}（协议原文保留载体疑被改动，"
              f"立即停止）")

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

    # ---- 结构探测（仪器事实转录源与判据冻结值锚）----
    framing = json.loads(FRAMING_R17.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS_R17.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    run_r16 = json.loads(RUN_R16.read_text(encoding="utf-8"))
    dev_record = json.loads(ROUND16_DEV_RECORD.read_text(encoding="utf-8"))
    probe_framing(framing)
    wp = probe_witness(witness, framing_sha=framing_sha, axis_sha=axis_sha)
    axis_probe = probe_axis_plan(axis_plan, axis_sha)
    run_probe = probe_run_r16(run_r16, run_r16_sha)
    dev_probe = probe_dev_record(dev_record, dev_record_sha, r16_record_sha)

    # ---- 渲染仪器实测（四 PNG vs witness-r17 登记值）----
    png_checks = check_renders(wp["registered"])

    # ---- 指引生成（10 组锚定编辑 + 不变量断言）----
    t_work, edit_list = build_guidance(
        base_text, orange_px=wp["orange_px"], green_px=wp["green_px"],
        void_final_640=wp["void_final_640"],
        void_strict_640=wp["void_strict_640"])
    edit_list_sorted = sorted(edit_list, key=lambda e: e["edit"])
    section_asserts = assert_guidance_invariants(base_text, t_work)

    guidance17_bytes = t_work.encode("utf-8")
    guidance17_sha = hashing.sha256_bytes(guidance17_bytes)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance15_sha=guidance15_sha, guidance17_sha=guidance17_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance17_bytes=len(guidance17_bytes),
        r15_record_sha=r15_record_sha, r16_record_sha=r16_record_sha,
        dev_probe=dev_probe, run_probe=run_probe, axis_probe=axis_probe,
        framing_sha=framing_sha, witness_sha=witness_sha,
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
    if HYPOTHESIS_TEST["hypothesis_id"] != "axis-plan-r17-resolution-double":
        _fail("hypothesis_test.hypothesis_id 不符")
    # 结构自证（仪器轮口径）
    if record["instrument_change"]["changed"] is not True:
        _fail("instrument_change.changed 必须为 True（轴1 仪器轮）")
    if record["no_instrument_change"] is not False:
        _fail("顶层 no_instrument_change 必须为 False（轴1 仪器轮）")
    if len(record["changed_variables"]) != 3:
        _fail("changed_variables 必须恰 3 项（渲染/§5A 同步/轮次标识）")
    if [v["id"] for v in record["changed_variables"]] != [
            "render-resolution-x2-r17", "guidance-5a-descriptive-px-sync",
            "round-identity-sync"]:
        _fail("changed_variables 顺序/标识不符")
    if record["changed_variables"][0]["instrument_change"] is not True:
        _fail("changed_variables[0] 须为仪器侧变量")
    if record["manipulated_factor"].find("渲染分辨率") != 0:
        _fail("manipulated_factor 不符（唯一操纵因子=渲染分辨率）")
    if record["pre_round_review"]["status"] != "satisfied_by_probe_and_plan":
        _fail("pre_round_review.status 不符")
    if "轴1 仪器轮" not in record["round_nature"]:
        _fail("round_nature 缺「轴1 仪器轮」声明")
    if "stage1" not in record["round_nature"]:
        _fail("round_nature 缺 stage1 声明")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    if "renders-r17" not in md["preregistration_declaration"]:
        _fail("measurement_design 预注册声明缺 renders-r17 图像口径")
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
    if record["guidance_reuse"]["derived_sha256"] != guidance17_sha:
        _fail("guidance_reuse.derived_sha256 与实测不符")
    # §5A 同步非判据自证：两条同步编辑须不触碰 §2–§7 冻结锚字符串
    for e in edit_list_sorted:
        if e["edit"] in (8, 9, 10):
            for needle in ("§2", "§3", "§4 ", "§5 ", "§6", "§7"):
                if needle in e["new"]:
                    _fail(f"§5A 同步编辑 {e['edit']} 误触冻结节关键语")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance15_sha=guidance15_sha, guidance17_sha=guidance17_sha,
        guidance15_bytes=len(base_text.encode("utf-8")),
        guidance17_bytes=len(guidance17_bytes),
        r15_record_sha=r15_record_sha, r16_record_sha=r16_record_sha,
        dev_probe=dev_probe, run_probe=run_probe, axis_probe=axis_probe,
        framing_sha=framing_sha, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks,
        edit_list=edit_list_sorted, section_asserts=section_asserts)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r17-prep-record")

    # ---- 防覆写守卫 + 落盘 ----
    if GUIDANCE_R17.exists():
        if GUIDANCE_R17.read_bytes() != guidance17_bytes:
            _fail("observation-guidance-r17.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r17-prep] 重跑自证：observation-guidance-r17.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R17.write_bytes(guidance17_bytes)
        if GUIDANCE_R17.read_bytes() != guidance17_bytes:
            _fail("回读不一致: observation-guidance-r17.md")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r17-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r17-prep] 重跑自证：r17-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r17-prep-record.json")

    # ---- 汇总打印 ----
    print("[r17-prep] 验证通过：r15 指引基座锚 "
          f"{GUIDANCE_R15_SHA_PREFIX} OK（只读，零写入，"
          f"{len(base_text.encode('utf-8'))} B）；r15-prep-record schema 模"
          f"板锚 {R15_PREP_RECORD_SHA_PREFIX} OK；r16-prep-record 24 键镜像"
          f"源锚 {R16_PREP_RECORD_SHA_PREFIX} OK（与 round16-dev-record 登"
          f"记 sha 交叉核对一致）；round16-dev-record 链锚 "
          f"{ROUND16_DEV_RECORD_SHA_PREFIX} OK（verdict=inconclusive、G1 基"
          f"线 0/0/0 在案）；run-r16 判据锚 {RUN_R16_SHA_PREFIX} OK（M1="
          f"{run_probe['frozen_values'].split('（')[0]}、guard_ok=True）；"
          f"framing-r17 单变量锚 {FRAMING_R17_SHA_PREFIX} OK（dpi "
          f"640→1280、margin 120px→240px 物理等值 0.1875in、探针 "
          f"feasible=true）；witness-r17 锚 {WITNESS_R17_SHA_PREFIX} OK"
          f"（橙 {wp['orange_px']} px/绿 {wp['green_px']} px/板内白 0，两板"
          f"相同；640 期参照 {EXPECTED_ORANGE_PX_640}/"
          f"{EXPECTED_GREEN_PX_640}）；axis-plan 冻结锚 "
          f"{AXIS_PLAN_SHA_PREFIX} OK（stage1 R17=A1、显著收益 ≥0.10、守门 "
          f"G1/G2）；"
          f"evaluation-protocol-v1 在盘锚 {EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r17-prep] 渲染仪器实测（四 PNG 实测=witness-r17 登记值；非字节"
          "复用、只读引用）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r17-prep] hypothesis_test 逐字断言链：预注册判据原文文本 → "
          "json.loads → 常量 → 记录字段，三层相等 PASS（数值/口径零改动；"
          "hypothesis_id=axis-plan-r17-resolution-double；0.671429="
          "0.771429-0.10 与 axis-plan/run-r16 在案锚逐一相符）")
    print(f"[r17-prep] 顶层键镜像断言：与 r16-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）")
    print(f"[r17-prep] 指引不变量断言：{len(section_asserts)} 项全部通过"
          f"（§1/§2–§5/§6/§7 分段逐字 {len(SECTION_PAIRS)} 段 + 关键 "
          f"substring {len(REQUIRED_SUBSTRING_VALUES)} 条 + 残留零 + 新文"
          f"本在位 + §5A 位置）")
    print(f"[r17-prep] 字节数差：r17（{len(guidance17_bytes)} B）- r15（"
          f"{len(base_text.encode('utf-8'))} B）= "
          f"{len(guidance17_bytes) - len(base_text.encode('utf-8'))} B")
    print(f"[r17-prep] 工件 sha256：observation-guidance-r17.md="
          f"{_sha(GUIDANCE_R17)}")
    print(f"[r17-prep] 工件 sha256：r17-prep-record.json={_sha(RECORD)}")
    print("[r17-prep] §5A 节实际落盘全文：")
    k = t_work.index(SECTION_5A_HEADING)
    print(t_work[k:t_work.index("## 6. 输出格式")], end="")


if __name__ == "__main__":
    main()
