#!/usr/bin/env python
"""CAL-R12-PREP：R12 指引侧单变量变更轮（suspicious_reroute「整段规则周
期」判据收窄轮）+协议侧跨轮工具行为规约 v1.2（派发层）预备见证包（写
out/v3-tl2/calibration/observation-guidance-r12.md 与 r12-prep-record.json）。

R12 轮性质（预注册，非事后）：**单变量指引侧变更轮 + 协议侧追加式规约**
——基准指引=observation-guidance-r9.md（a0c10154；即 r11 轮零字节复用件
「r11 指引」，无独立 r11 指引文件），唯一指引侧实质变更=§3A 类别 4 示例 c
收窄替换（r9 增补示例原文删除，替换为「整段规则周期」判据）+ §3A 末尾
r9 对照说明原位保留、其后追加 r12 对照说明；执行 round11-dev-record
next_iteration_targets[1]（用户 2026-09-07 已拍板排程本轮）。协议侧
evaluation-protocol-v1→v1.2 追加式（执行 next_iteration_targets[0] 固定
reader 工具行为规约案：所有 reader 派发指令统一加入硬性条款——禁止对图
像做任何程序化处理（裁剪/放大/像素分析/衍生图像生成等），判读只允许以
Read 工具查看原图（同一原图可重复查看）；属派发层、随派发指令生效，不进
指引判读文本、不改变任何分类判据语义；v1.1 的 n=3 多实例与聚合口径全部
沿用）。渲染零字节复用 R5 冻结件（零仪器变更、零重渲染）。本脚本只做
PREP，不做盲读、不做任何视觉判读、不写轮测试。

检验假设（hypothesis_id=r11-dev-record-candidate-1-example-c-tighten）：
示例 c 收窄后，「形态非整段规则周期却援引等长/蛇形候选解释」的滥用型弃
权旗被消除（该类形态按 §4 直接走弃权或关注路径，弃权理由不再引用候选解
释），同时边界条款方向的非弃权 reroute 报告保留。支持=R12 盲读滥用型弃
权旗=0 且 reroute 类非弃权旗≥1；拒绝=滥用型弃权旗≥1；reroute 类旗标总
量=0 记「不可判」（不是支持）。基线数字（r10=2：R10T-012/013；r11=1：
R11T-006；r11 另有边界条款方向非弃权 reroute=2：R11T-018/020，属正确用
法保留）只作为已落盘 run-record 的引用记入本编排侧 prep-record，不进任
何指引文件（指引零轮次结果数字）。

功能（out/ 仅新建两个文件：observation-guidance-r12.md、
r12-prep-record.json；既有产物零改动，observation-guidance-r9.md 零字
节不动）：

  1. fail-closed 复核 observation-guidance-r9.md：sha256 前 8=a0c10154
     （不符即停=基准指引疑被改动）；并与 r11-prep-record.json
     guidance_reuse.sha256_measured 登记值交叉核对（链自洽）。
  2. fail-closed 复核 r11-prep-record.json：sha256 前 8=9074df2d、
     schema_version=3.0、kind=tl2_calibration_r11_prep_record、
     round_id_constant=2026-09-07-r11（不符即停）；探测
     renders_reuse.png_witness 结构取 renders-r5 四件 PNG 见证常量并要
     求登记自洽（sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）；framing_reference.
     sha256 与盘上实测交叉核对（链自洽）。
  3. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全
     match 才继续）；并复核 frozen_inputs 无 renders-r5 输出 PNG 哈希
     登记字段（r5 前缀键不存在、r4_frozen_png_sha256_reference 在场，
     不符即停）。
  4. fail-closed 复核 renders-r5 四件 PNG：magic + sha256 实测 vs 上述
     见证常量（全 match 才继续；防改动冻结渲染）。
  5. fail-closed 复核 round11-dev-record.json：sha256 前 8=66e41bbf、
     round_id=2026-09-07-r11（不符即停）；从 next_iteration_targets 按
     内容标记唯一定位两项（跨轮可比性协议候选=[0]、示例 c 措辞修改=
     [1]，实测索引回填并要求相符）；另取 hypothesis_test_i.
     preregistered_criteria_quote.user_directive_2026_09_07 原文（须含
     「示例 c 措辞修改排程 R12」标记，不符即停）；取 run_record_ref 与
     r10_contrast_ref 的 path_rel/sha256 作基线 sources（在案引用）。
  6. 由 observation-guidance-r9.md 机械变换生成 observation-guidance-
     r12.md（§3A 类别 4 示例 c 收窄替换；§3A 末尾 r9 对照说明原位保留、
     其后追加 r12 对照说明；头部标题/round_id_constant/本轮性质行/变更
     声明节（四 bullet：变更/非放宽/不变/归因计划）按 r9 同款结构重写；
     机械替换恰四处：2026-09-07-r9→2026-09-07-r12、R9T-→R12T-、
     R9B-→R12B-、reader-r9→reader-r12，标题轮次标识 R9→R12 一并替换。
     其余文本逐字承 r9）。变换前后逐项计数断言（锚点出现次数不符即停）
     +输出侧禁词断言（零 GT、零轮次结果数字）。
  7. 落盘 r12-prep-record.json（canonical JSON=
     hashing.canonical_json_bytes：ensure_ascii=False / sort_keys /
     indent=1 / LF；顶层键集合与 r11-prep-record 逐键镜像断言，文档化
     差异=-guidance_reuse +guidance（r11=零字节复用轮、r12=指引变更轮，
     语义对应更换，与 r9-prep-record 的 guidance 键结构对齐）；
     hypothesis_test 键集合与 r11 逐键镜像零差异）；同参重建两次逐字节
     一致自证；防覆写守卫——目标文件已存在且重建字节非逐字节等同→
     FAIL，等同→允许幂等重跑（零覆写）；落盘后重读盘面字节回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r12）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；
无 subprocess / 无网络 / 无主机绝对路径；不读 GT / reader-raw-* /
calibration-run-* / derivation-log-* / compare 产物（round11-dev-record
仅读 next_iteration_targets 与 user_directive/run_record_ref/
r10_contrast_ref 字段取预注册原文与在案引用；r11-prep-record 仅用于取
PNG 见证常量与链交叉核对）；无 git。指引文件内零 GT、零轮次结果数字
（输出侧禁词断言执行）。

用法：python scripts/s46_calibration_r12_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R11_PREP_RECORD = CAL_DIR / "r11-prep-record.json"
R11_DEV_RECORD = CAL_DIR / "round11-dev-record.json"
GUIDANCE_R9 = CAL_DIR / "observation-guidance-r9.md"
GUIDANCE_R12 = CAL_DIR / "observation-guidance-r12.md"
RECORD = CAL_DIR / "r12-prep-record.json"

DATE_CONSTANT = "2026-09-07"
ROUND_ID = "2026-09-07-r12"

#: 冻结基线锚（开工实测给定；不符即停）。GUIDANCE_R9=基准指引（=r11 轮
#: 零字节复用件，即「r11 指引」；本脚本只读、零写入）；开工/收工由编排
#: 侧另验受保护文件；本脚本内亦 fail-closed 复核。
GUIDANCE_R9_SHA_PREFIX = "a0c10154"
R11_PREP_RECORD_SHA_PREFIX = "9074df2d"
R11_DEV_RECORD_SHA_PREFIX = "66e41bbf"

#: round11-dev-record next_iteration_targets 两项的内容定位标记
#: （0 起始索引 [0]=跨轮可比性协议候选=协议侧 v1.2 来源；[1]=示例 c 措
#: 辞修改=指引侧候选=本轮执行的指引侧变更；按标记唯一定位、实际索引实
#: 测回填并要求相符，不符即停）
MARK_CANDIDATE_PROTO = "跨轮可比性协议候选（协议侧"
MARK_CANDIDATE_PROTO_PLAN = "固定 reader 工具行为规约"
MARK_CANDIDATE_GUIDANCE = "示例 c 措辞修改（指引侧"
MARK_USER_DIRECTIVE = "示例 c 措辞修改排程 R12"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；见证常量从 r11-prep-record
#: renders_reuse.png_witness 登记探测取得，不在此硬编码）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 顶层键集合相对 r11-prep-record 的文档化差异（r11=零字节复用轮用
#: guidance_reuse；r12=指引变更轮，语义对应更换为 r9-prep-record 同款
#: guidance 键结构。零其他增删）
TOP_LEVEL_KEY_DELTA_REMOVE = ("guidance_reuse",)
TOP_LEVEL_KEY_DELTA_ADD = ("guidance",)

#: hypothesis_test 键集合相对 r11-prep-record 零差异（13 键逐键镜像）
HT_KEY_DELTA_REMOVE = ()
HT_KEY_DELTA_ADD = ()

# ---------------------------------------------------------------------------
# 指引生成（纯函数：r9 全文逐字 + 唯一指引侧变更 + 机械替换）
# ---------------------------------------------------------------------------

OLD_TITLE = "# R9 轮 reader 判读指引（observation-guidance-r9）"
NEW_TITLE = "# R12 轮 reader 判读指引（observation-guidance-r12）"

OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（suspicious_reroute 等长/蛇形形态判"
    "据轮）**。渲染零变更（复用 R5 冻结渲染件：零仪器变更、零重渲染）；本"
    "轮唯一变更=判读指引 §3A 类别 4 增补示例 c（预注册见下），指引落盘后"
    "由编排侧重新盲读。")

NEW_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（suspicious_reroute「整段规则周期」"
    "判据收窄轮）+ 协议侧跨轮工具行为规约 v1.2（派发层，读者不可见，见对"
    "照说明）**。渲染零变更（复用 R5 冻结渲染件：零仪器变更、零重渲染）；"
    "本轮指引侧唯一变更=判读指引 §3A 类别 4 示例 c 收窄替换（预注册见"
    "下），指引落盘后由编排侧重新盲读。")

#: §3A 类别 4 示例 c 原行（r9 增补；替换锚）
OLD_EXAMPLE_C_LINE = (
    "   - 示例 c：整段连线呈规则、周期性的来回折叠形态（蛇形/等长匹配类布"
    "线的常见样式）时，该规则周期形态本身可按第 4 节存在性判断一般判据推理"
    "——同类通用布线样式的常规设计解释是候选解释之一；形态不规则、无规律的"
    "绕行仍按关注现象处理。（示例=判据说明，非期望清单，不代表图中存在此类"
    "现象。）")

#: 替换后的示例 c（包指令给定文本，一字不改；3 空格缩进与同级示例一致）
NEW_EXAMPLE_C_LINE = (
    "   - 示例 c：**「整段规则周期」判据**——仅当一段连线**全程**呈规则、"
    "周期性的来回折叠（蛇形/等长匹配类布线的完整样式：折叠贯穿该段连线始"
    "终、节律一致）时，才可把同类通用布线样式的常规设计解释作为第 4 节存在"
    "性判断中的候选解释之一；**仅局部出现的小幅波状/抖动段、单次的大弯折或"
    "大范围绕行，均不构成整段规则周期形态，不适用该候选解释**，仍按第 4 节"
    "一般判据处理（孤立出现或打破周边同类图形规律的不一致形态 → 更可能是"
    "关注现象）。（示例=判据说明，非期望清单，不代表图中存在此类现象。）")

#: §3A 末尾追加的 r12 对照说明（包指令给定文本，一字不改；置于 r9 对照
#: 说明之后、"## 4" 之前）
CONTRAST_NOTE_R12 = (
    "（对照说明（r12 增补）：类别 4 示例 c 自本轮起被「整段规则周期」判据"
    "**收窄替换**——原示例（r9 增补）允许把规则周期形态作为常规设计候选解"
    "释之一，本轮收窄其适用前提为『全程规则、周期、节律一致』；仅局部小幅"
    "波状/抖动、单次大弯折或大范围绕行不再适用该候选解释，仍按 §4 一般判据"
    "处理。本变更为**收紧**（候选解释可用前提收窄、判断责任标准一字未"
    "松），§4 全文（含三路出口与反放宽条款）、类别封闭集、其余示例逐字保"
    "留。）")

SEC_START = "## 本轮变更声明（预注册，非事后）"
SEC_END_ANCHOR = "\n## 1. 角色与任务"

BULLET_CHANGE = (
    "- **变更（指引侧恰一项 + 协议侧一项）：** **指引侧：§3A 类别 4 "
    "`suspicious_reroute` 示例 c 收窄替换**——r9 增补的示例 c 原文删除，替"
    "换为「整段规则周期」判据（全文见 §3A 类别 4；适用前提收窄为整段连线"
    "**全程**规则、周期、节律一致；仅局部小幅波状/抖动、单次大弯折或大范"
    "围绕行不再适用等长/蛇形候选解释）；并在 §3A 末尾（r9 对照说明之后、"
    "第 4 节之前）增补一条 r12 对照说明。**协议侧：跨轮工具行为规约 v1.2"
    "（追加式）**——自本轮起所有 reader 派发指令统一加入硬性条款：禁止对"
    "图像做任何程序化处理（裁剪/放大/像素分析/衍生图像生成等），判读只允"
    "许以 Read 工具查看原图（同一原图可重复查看）；该规约属**派发层**（派"
    "发指令文本），不进本指引判读文本、不改变任何分类判据语义。措辞中性一"
    "般化，零具体板、位号、坐标、数量期望，零轮次结果数字。")

BULLET_NO_LOOSENING = (
    "- **非放宽声明：** 本轮指引侧变更为**收紧**——候选解释可用前提收窄"
    "（「整段规则周期」判据），**判断责任标准一字未松**；§4 三路出口显式"
    "化与反放宽条款**原文保留**（「仅因形态不熟悉、不确定其设计含义，不构"
    "成判为正常设计特征的理由」等判断标准词原样保留于弃权适用侧），总原则"
    "「宁可 abstain 不硬标」不动；§3 邻域框收窄判据一字未动，非弃权旗标框"
    "仍受其约束；§3、§4 与 §3A 其余示例一字不动；判「正常设计特征」与判"
    "「关注现象」承担**同等**判断责任；不降低任何存在性、归类、定位或报告"
    "的责任门槛。协议侧工具行为规约仅固定判读输入手段（只允许 Read 直读原"
    "图），不触碰任何判据文本。")

BULLET_UNCHANGED = (
    "- **不变：** 渲染（复用 R5 冻结渲染件）、角色与盲读纪律（§1）、类别枚"
    "举（6 类逐字，§2）、§3 邻域框收窄判据与坐标口径、§3A 其余示例（类别 "
    "4 示例 a、b 与其余五类全部示例逐字保留）、§4 全文（总原则、两条显式判"
    "据、存在性判断一般判据、三路出口显式化、confidence 定义与弃权 flag 输"
    "出细节、既有对照说明含 r8/r9 增补块原文原位）、courtyard 中性说明"
    "（§5）、输出 schema（单 JSON、per_image、flag 恰六键、无 side 字段，"
    "§6）、格式对齐提示（§7）、bottom 视口径（沿用 r4 指引：top/bottom 判"
    "读口径在图像空间完全一致、不做镜像换算；未为 bottom 单独定图层清单—"
    "—该属渲染侧变更，不在本轮）。机械替换仅：视角前缀 R9T/R9B→R12T/R12B、"
    "round_id_constant→`2026-09-07-r12`（及示例中 reader-r9→reader-r12）。")

BULLET_ATTRIBUTION = (
    "- **归因计划：** 本轮归因分层由编排侧在轮后记录执行：reroute 类主通道"
    "指标主要归因于示例 c 措辞收窄（协议侧工具行为规约属派发层、不改变任何"
    "分类判据语义）；跨轮对比为方向性（reader 实例群与工具代际混杂照旧声"
    "明）；轮内多实例分布=工具规约下的新一致性基线。本指引零 GT、零轮次结"
    "果数字（判据引用与基线文字仅入编排侧记录）。")

NEW_SECTION_BODY = (
    SEC_START + "\n\n" + BULLET_CHANGE + "\n\n" + BULLET_NO_LOOSENING +
    "\n\n" + BULLET_UNCHANGED + "\n\n" + BULLET_ATTRIBUTION + "\n\n")

#: 输出侧禁词断言（指引零 GT、零轮次结果数字的清单法自动化；均为在案轮
#: 次结果分数/分数记法/盘上产物 id 前缀，r9 指引全文与本轮新增文本均不含）
FORBIDDEN_IN_GUIDANCE = (
    "GT-", "ground-truth", "ground_truth", "abstain_rate",
    "0.222222", "0.727273", "0.285714", "0.226415", "0.133333",
    "0.153846", "0.307692", "0.154", "0.076923",
    "4/14", "8/11", "4/18", "2/15", "12/53", "1/13", "2/13", "3/20",
    "R10T-", "R11T-", "R11B-", "reader-r10", "reader-r11",
)


def _fail(msg: str) -> None:
    print(f"[r12-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _replace_counted(text: str, old: str, new: str, expected: int,
                     label: str) -> str:
    """计数受控替换：old 出现次数 != expected 即停。"""
    n = text.count(old)
    if n != expected:
        _fail(f"锚点计数不符：{label} 期望 {expected} 次，实测 {n} 次")
    return text.replace(old, new)


def build_guidance(r9_text: str) -> str:
    """由 r9 指引全文生成 r12 指引（纯函数；同入参必得同输出）。

    顺序纪律：先做替换与插入（其锚点均不含机械替换模式），再整体重写
    标题/本轮性质行/变更声明节（新文本内含 r9→r12 箭头记法，故机械替换
    必须先行，避免自命中）。
    """
    text = r9_text

    # ---- 前置计数断言（r9 输入侧锚点）----
    for pat, n in (
            ("2026-09-07-r9", 2),   # round_id 行 + 变更声明节内记法
            ("R9T-", 4),            # §6 表行 ×2 + 格式示例 flag_id ×2
            ("R9B-", 1),            # §6 表行
            ("reader-r9", 2),       # 格式示例 reader_id + 变更声明节内记法
            (OLD_TITLE, 1),
            (OLD_NATURE_LINE, 1),
            (OLD_EXAMPLE_C_LINE, 1),
            ("（对照说明（r9 增补）", 1),
            ("（对照说明（r11 增补）", 0),  # r11 轮零指引变更、无 r11 增补块
            ("（对照说明（r8 增补）", 1),   # §4 既有 r8 增补块
            ("\n\n## 4. 置信度与弃权", 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1)):
        if text.count(pat) != n:
            _fail(f"r9 指引锚点计数不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")

    # ---- (1) §3A 类别 4 示例 c 收窄替换（示例 a、b 原文保留）----
    text = text.replace(OLD_EXAMPLE_C_LINE, NEW_EXAMPLE_C_LINE)

    # ---- (2) §3A 末尾追加 r12 对照说明（r9 对照说明原位、其后，"## 4" 之前）----
    text = text.replace("\n\n## 4. 置信度与弃权",
                        "\n\n" + CONTRAST_NOTE_R12 + "\n\n## 4. 置信度与弃权")

    # ---- (3) 机械替换（四处；变更声明节旧文本此时仍在场、随后整体重写，
    #      其内被替换的记法不影响结果）----
    text = _replace_counted(text, "2026-09-07-r9", "2026-09-07-r12", 2,
                            "round_id_constant")
    text = _replace_counted(text, "R9T-", "R12T-", 4, "flag 前缀 R9T-")
    text = _replace_counted(text, "R9B-", "R12B-", 1, "flag 前缀 R9B-")
    text = _replace_counted(text, "reader-r9", "reader-r12", 2, "reader-id")

    # ---- (4) 标题、本轮性质行 ----
    text = _replace_counted(text, OLD_TITLE, NEW_TITLE, 1, "标题")
    text = _replace_counted(text, OLD_NATURE_LINE, NEW_NATURE_LINE, 1,
                            "本轮性质行")

    # ---- (5) 变更声明节整体重写（r9 同款结构，r12 内容四 bullet）----
    start = text.index(SEC_START)
    end = text.index(SEC_END_ANCHOR)
    if not start < end:
        _fail("变更声明节锚点顺序异常")
    text = text[:start] + NEW_SECTION_BODY + text[end + 1:]

    # ---- 输出侧禁词断言（零 GT、零轮次结果数字）----
    for pat in FORBIDDEN_IN_GUIDANCE:
        if pat in text:
            _fail(f"r12 指引含禁词（零 GT/零轮次结果数字自检失败）：{pat}")

    # ---- 后置计数断言（r12 输出侧）----
    for pat, n in (
            ("R9T-", 0),
            ("R9B-", 0),
            ("2026-09-07-r9", 0),
            ("2026-09-07-r12", 2),
            ("R12T-", 4),
            ("R12B-", 1),
            ("reader-r12-top", 1),
            ("reader-r9", 1),       # 仅存于新节「reader-r9→reader-r12」记法
            (OLD_EXAMPLE_C_LINE, 0),
            (NEW_EXAMPLE_C_LINE, 1),
            (CONTRAST_NOTE_R12, 1),
            ("（对照说明（r9 增补）", 1),
            ("（对照说明（r8 增补）", 1),
            (NEW_TITLE, 1),
            (NEW_NATURE_LINE, 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1)):
        if text.count(pat) != n:
            _fail(f"r12 指引后置断言不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")
    return text


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s40/s44 模式；零写入）
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r11_record: dict) -> dict:
    """探测 r11-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r11_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r11-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
    by_side = {}
    for item in witness:
        for key in ("state_side", "path_rel", "sha256_witness_constant",
                    "sha256_measured", "match_to_witness_constant"):
            if key not in item:
                _fail(f"png_witness 项缺键 {key}（结构探测失败）")
        by_side[item["state_side"]] = item
    if sorted(by_side) != sorted(RENDERS_R5_SIDES):
        _fail(f"png_witness state_side 集不符：{sorted(by_side)}")
    constants = {}
    for side in RENDERS_R5_SIDES:
        item = by_side[side]
        expected_rel = f"out/v3-tl2/calibration/renders-r5/{side}.png"
        if item["path_rel"] != expected_rel:
            _fail(f"{side} png_witness path_rel 不符：{item['path_rel']}")
        if item["sha256_measured"] != item["sha256_witness_constant"]:
            _fail(f"{side} png_witness 登记不自洽（measured != witness_constant）")
        if item["match_to_witness_constant"] is not True:
            _fail(f"{side} png_witness 登记自洽位不为真")
        constants[side] = item["sha256_witness_constant"]
    return constants


def _check_frozen_input_pdfs(framing: dict) -> list:
    """R5 渲染输入链复核：frozen_inputs.r4_frozen_pdfs 登记值 vs 盘上实测。"""
    registered = {item["state_side"]: item
                  for item in framing["frozen_inputs"]["r4_frozen_pdfs"]}
    results = []
    for state_side, rel in FROZEN_PDF_RELS.items():
        item = registered.get(state_side)
        if item is None:
            _fail(f"render-framing-r5.json 缺 {state_side} 的冻结 PDF 登记")
        if item["path_rel"] != rel:
            _fail(f"{state_side} 冻结 PDF 路径不符：{item['path_rel']} != {rel}")
        measured = _sha(REPO / rel)
        results.append({
            "state_side": state_side,
            "path_rel": rel,
            "sha256_registered": item["sha256"],
            "sha256_measured": measured,
            "match": measured == item["sha256"],
        })
    bad = [r for r in results if not r["match"]]
    if bad:
        _fail(f"R5 冻结输入 PDF 复核不符（渲染输入链疑被改动）：{bad}")
    return results


def _check_framing_raster_field(framing: dict) -> None:
    """复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段（与在案记录
    raster_output_hash_field_probe 结论一致；不符即停=framing 结构漂移）。"""
    fi_keys = list(framing.get("frozen_inputs", {}).keys())
    if any("r5" in k.lower() for k in fi_keys):
        _fail(f"render-framing-r5 frozen_inputs 出现 r5 前缀键（与在案探测结"
              f"论不符，framing 结构漂移）：{fi_keys}")
    if "r4_frozen_png_sha256_reference" not in fi_keys:
        _fail("render-framing-r5 frozen_inputs 缺 r4_frozen_png_sha256_"
              "reference（与在案探测结论不符，framing 结构漂移）")


def _check_renders_r5_pngs(constants: dict) -> list:
    """renders-r5 四件 PNG：magic 检查 + 实测 sha256 vs 登记见证常量。"""
    results = []
    for state_side in RENDERS_R5_SIDES:
        expected = constants[state_side]
        path = CAL_DIR / "renders-r5" / f"{state_side}.png"
        if not path.exists():
            _fail(f"renders-r5 PNG 缺失：{path}")
        with path.open("rb") as f:
            magic = f.read(8)
        if magic != PNG_MAGIC:
            _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        results.append({
            "state_side": state_side,
            "path_rel": f"out/v3-tl2/calibration/renders-r5/{state_side}.png",
            "sha256_measured": measured,
            "sha256_witness_constant": expected,
            "match_to_witness_constant": measured == expected,
        })
    bad = [r for r in results if not r["match_to_witness_constant"]]
    if bad:
        _fail(f"renders-r5 PNG 实测与登记见证常量不符（R5 冻结渲染疑被改动）：{bad}")
    return results


def _extract_preregistration_quotes(dev_record: dict) -> dict:
    """从 round11-dev-record 取两项预注册原文与 user_directive 原文。

    按内容标记唯一定位（0 起始索引 [0]=跨轮可比性协议候选=协议侧 v1.2 来
    源、[1]=示例 c 措辞修改=指引侧候选=本轮执行的指引侧变更），实际索引
    实测回填并要求相符；定位不到或歧义即停。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or len(targets) < 2:
        _fail("round11-dev-record next_iteration_targets 结构不符")
    p_idx = [i for i, t in enumerate(targets)
             if isinstance(t, str) and MARK_CANDIDATE_PROTO in t]
    g_idx = [i for i, t in enumerate(targets)
             if isinstance(t, str) and MARK_CANDIDATE_GUIDANCE in t]
    if len(p_idx) != 1 or len(g_idx) != 1:
        _fail(f"next_iteration_targets 标记定位歧义：proto={p_idx}，"
              f"guidance={g_idx}")
    if p_idx[0] != 0:
        _fail(f"跨轮可比性协议候选实测索引={p_idx[0]} != 预注册给定 [0]")
    if g_idx[0] != 1:
        _fail(f"示例 c 措辞修改候选实测索引={g_idx[0]} != 预注册给定 [1]")
    proto_text, guidance_text = targets[p_idx[0]], targets[g_idx[0]]
    if MARK_CANDIDATE_PROTO_PLAN not in proto_text:
        _fail("协议侧候选项缺「固定 reader 工具行为规约」标记（v1.2 执行案缺失）")
    if "单变量纪律" not in guidance_text:
        _fail("示例 c 措辞修改项缺「单变量纪律」标记")

    quote_block = (dev_record.get("hypothesis_test_i", {})
                   .get("preregistered_criteria_quote", {}))
    user_directive = quote_block.get("user_directive_2026_09_07")
    if not isinstance(user_directive, str) or MARK_USER_DIRECTIVE not in user_directive:
        _fail("user_directive_2026_09_07 缺失或缺「示例 c 措辞修改排程 R12」标记")

    run_ref = dev_record.get("run_record_ref", {})
    r10_ref = (dev_record.get("hypothesis_test_i", {})
               .get("mechanism_observation", {})
               .get("example_c_bidirectional_effect", {})
               .get("r10_contrast_ref", {}))
    for ref, label in ((run_ref, "run_record_ref"), (r10_ref, "r10_contrast_ref")):
        if not isinstance(ref, dict) or "path_rel" not in ref or "sha256" not in ref:
            _fail(f"round11-dev-record {label} 缺 path_rel/sha256（在案引用结构漂移）")

    return {
        "indices_zero_based": [p_idx[0], g_idx[0]],
        "proto_candidate_target": proto_text,
        "guidance_candidate_target": guidance_text,
        "user_directive": user_directive,
        "r11_run_record_ref": {"path_rel": run_ref["path_rel"],
                               "sha256": run_ref["sha256"]},
        "r10_run_record_ref": {"path_rel": r10_ref["path_rel"],
                               "sha256": r10_ref["sha256"]},
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r11_record_sha: str, dev_record_sha: str,
                 guidance_r9_sha: str, guidance_r12_sha: str,
                 pdf_results: list, png_results: list, quotes: dict) -> dict:
    """构建 r12-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r12_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r12",
        "round_nature": (
            "单变量指引侧变更轮（suspicious_reroute「整段规则周期」判据收窄"
            "轮）+协议侧跨轮工具行为规约 v1.2（派发层，读者不可见）：判读指"
            "引由 r9 指引（r11 轮零字节复用件，a0c10154）机械变换生成 "
            "observation-guidance-r12.md（指引侧唯一实质变更=§3A 类别 4 示"
            "例 c 收窄替换+§3A 末尾 r12 对照说明；执行 round11-dev-record "
            "next_iteration_targets[1]，用户 2026-09-07 已拍板排程本轮），"
            "渲染零字节复用 R5 冻结件（零仪器变更、零重渲染）；协议侧 "
            "evaluation-protocol-v1→v1.2 追加式（执行 next_iteration_"
            "targets[0] 固定 reader 工具行为规约案：派发指令统一禁止程序化"
            "图像处理、只允许 Read 直读原图——属派发层、不改变任何分类判据"
            "语义；v1.1 的 n=3 多实例与聚合口径全部沿用，见 protocol_"
            "amendment）；指引先于本轮盲读落盘、落盘即冻结；盲读由编排侧在"
            "本记录之后以 12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-07 拍板示例 c 修改措辞排程 R12（本轮执行；r11-"
            "prep-record user_directive_note 与 round11-dev-record "
            "hypothesis_test_i.preregistered_criteria_quote."
            "user_directive_2026_09_07 原文在案）与 Tier 2 留出下载（并行"
            "包，不在本记录范围）"),
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "amendment_version": "v1.2",
            "amendment_mode": (
                "追加式（additive）：不改动 v1/v1.1 任何既有条款语义，只追"
                "加 reader 派发指令的工具行为规约（派发层）"),
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视角"
                "层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径并"
                "列、联合门代表配置+实例间范围并列（measurement_design 五"
                "条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约：自本轮起所有 reader 派发指令统一加入硬性"
                "条款——「禁止对图像做任何程序化处理（裁剪/放大/像素分析/"
                "衍生图像生成等）；判读只允许以 Read 工具查看原图（同一原图"
                "可重复查看）」——仪器行为钉住（与 r9 全纯直读口径对齐）；"
                "属派发层，读者上下文=指引+单张 PNG+派发指令（含规约条款），"
                "零 GT；不影响判读语义——分类判据零变更，仅输入手段固定"),
            "motivation_note": (
                "动机如实记：r10/r11 实测 8/12 派次自选 PIL 局部裁剪放大"
                "（round11-dev-record reader_instance_note 在案）、跨轮 "
                "0/4→8/12 摆动=轮间可比性最大混杂；规约把仪器行为钉住"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": "22dc7337",
                "sha256_measured": "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
                "zero_byte_preserved": True,
                "note": (
                    "v1 原文零字节保留（r11 轮同口径在案登记，本轮继续沿"
                    "用）；v1.2 修订声明只记于本 prep-record，不回写 v1 文"
                    "件（协议自身状态行：后续修订=新版本文件，不回写）；正"
                    "式 v1.2 版本文件若需落盘属后续动作，本轮不新建协议文"
                    "件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实例"
                "（i1/i2/i3）；实例上下文=指引（observation-guidance-r12.md）"
                "+单张 PNG+派发命名指令（含 v1.2 工具行为规约硬性条款），零 "
                "GT；两波次串行保序（同一实例先 applied 后 prep1，flag_id "
                "编号跨板连续）"),
            "naming": (
                "reader_id=reader-r12-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R12T/R12B（本轮指引生成时已由 §6 的 R9T/R9B 机械替换写入 "
                "R12T/R12B 与 reader-r12 示例——与 r11 的派发侧机械覆盖不"
                "同，本轮替换随指引落盘固化；实例后缀 i{1,2,3} 仍由派发指"
                "令机械补全）；实例间编号独立，同实例跨板连续"),
            "scope_note": (
                "本修订只追加派发指令条款，不改指引判据/渲染/GT/阈值任何实"
                "质；工具规约不改变分类判据语义（仅输入手段固定）；若 v1.2 "
                "后被正式采纳，其对门的评价含义须另行声明，本轮 "
                "in_calibrated_range 恒 False"),
        },
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "png_witness_source": {
                "path_rel": "out/v3-tl2/calibration/r11-prep-record.json",
                "sha256": r11_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量照抄 r11-prep-record.json "
                    "renders_reuse.png_witness 登记（来源链：r11-prep-record "
                    "取自 r10-prep-record，r10-prep-record 取自 r9-prep-"
                    "record，r9-prep-record 取自 r8-prep-record，r8-prep-"
                    "record 取自 r7-prep-record，源头=2026-09-06 s35/s33 "
                    "首跑实测；本脚本探测该结构取常量并要求登记自洽，另对来"
                    "源文件以 9074df2d 锚 fail-closed 复核），非本脚本新测"
                    "——R12 零仪器变更、零重渲染，不产生新见证"),
            },
            "raster_output_hash_field_probe": {
                "field_found": False,
                "finding": (
                    "render-framing-r5.json 中不存在 renders-r5 输出 PNG "
                    "的哈希登记字段；frozen_inputs.r4_frozen_png_sha256_"
                    "reference 登记的是 R4 轮冻结 PNG 参考值（与 renders-r5 "
                    "实测不符，属预期：R5 仪器 dpi/crop 变更后 PNG 字节本不"
                    "相同）；本脚本已复核该结构结论仍成立（不符即停）"),
                "resolution": (
                    "故 renders-r5 PNG 见证常量以 r11-prep-record.json 登记"
                    "值为准（见 png_witness_source），本脚本 fail-closed 实"
                    "测比对（防改动见证）"),
            },
            "frozen_input_pdfs_check": {
                "scope": ("render-framing-r5.json frozen_inputs."
                          "r4_frozen_pdfs（R5 渲染输入链）"),
                "count": len(pdf_results),
                "all_match": True,
                "results": pdf_results,
            },
            "png_witness": png_results,
            "png_witness_note": (
                "applied-bottom 与 prep1-bottom 盘上字节一致（sha256 相同）"
                "为 R5 渲染实测事实（沿用 r11-prep-record 登记，本脚本实测仍"
                "符），照实登记，不含任何 GT 含义"),
            "no_instrument_change": True,
        },
        "guidance": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r12.md",
            "sha256": guidance_r12_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r9.md",
                "sha256_prefix_expected": GUIDANCE_R9_SHA_PREFIX,
                "sha256_measured": guidance_r9_sha,
                "match": guidance_r9_sha.startswith(GUIDANCE_R9_SHA_PREFIX),
                "role": (
                    "指引作者唯一事实源（=r11 轮零字节复用件，即本轮语境的"
                    "「r11 指引」，无独立 r11 指引文件；另加包指令，GT 已剥"
                    "离）"),
            },
            "change_summary": (
                "相对 r11 指引（=observation-guidance-r9.md，r11 轮零字节复"
                "用）恰三类差异：§3A 类别 4 示例 c 收窄替换（「整段规则周"
                "期」判据，r9 增补原文删除）；§3A 末尾（r9 对照说明原位保"
                "留、其后、§4 之前）增补一条 r12 对照说明；头部（标题、"
                "round_id_constant、本轮性质行、本轮变更声明节按 r9 同款结"
                "构重写为本轮四 bullet：变更/非放宽/不变/归因计划）与 §6 视"
                "角前缀/示例 reader-id 的机械替换（恰四处：2026-09-07-r9→"
                "2026-09-07-r12、R9T-→R12T-、R9B-→R12B-、reader-r9→"
                "reader-r12，标题轮次标识 R9→R12 一并）。其余文本逐字承 r9 "
                "指引（含 §4 两条对照说明与 §3A r9 对照说明原位保留）。"),
        },
        "changed_variables": [
            {
                "id": "reroute-example-c-full-segment-periodic-tighten",
                "target": ("observation-guidance-r12.md §3A 类别 4（指引侧"
                           "恰一项；单变量轮）"),
                "description": (
                    "§3A 类别 4 `suspicious_reroute` 示例 c 收窄替换（示例 "
                    "a、b 原文保留）：r9 增补的示例 c 原文删除，替换为「整"
                    "段规则周期」判据（措辞一字不改地使用包指令给定文本）；"
                    "另在 §3A 末尾（r9 对照说明之后、§4 之前）增补 r12 对照"
                    "说明一行（措辞一字不改地使用包指令给定文本）。"),
                "old_text": OLD_EXAMPLE_C_LINE,
                "new_text": NEW_EXAMPLE_C_LINE,
                "contrast_note_added": CONTRAST_NOTE_R12,
                "attribution_channel": (
                    "reroute 类主通道（滥用型弃权旗计数：基线 r10=2、r11=1；"
                    "支持=0 且 reroute 类非弃权旗≥1、拒绝=≥1）；守门=其余"
                    "类别非弃权旗标仍受 §3 收窄判据约束（几何门面积比出局条"
                    "目无回升）"),
            },
            {
                "id": "protocol-v1-2-reader-tool-behavior-rule",
                "target": ("reader 派发指令（协议侧一项；evaluation-"
                           "protocol-v1→v1.2 追加式，派发层）"),
                "description": (
                    "自本轮起所有 reader 派发指令统一加入硬性条款：「禁止对"
                    "图像做任何程序化处理（裁剪/放大/像素分析/衍生图像生成"
                    "等）；判读只允许以 Read 工具查看原图（同一原图可重复查"
                    "看）」。不影响判读语义——分类判据零变更，仅输入手段固"
                    "定（与 r9 全纯直读口径对齐；r10/r11 实测 8/12 派次自选 "
                    "PIL 操作、跨轮 0/4→8/12 摆动=轮间可比性最大混杂，规约"
                    "把仪器行为钉住）。"),
                "attribution_channel": (
                    "非判读语义通道：不改变分类判据，reroute 类主通道指标主"
                    "要归因于指引侧措辞收窄；对轮内一致性（实例间弃权率极"
                    "差）为工具规约下的新一致性基线（首轮）"),
            },
        ],
        "manipulated_factor": (
            "恰两项变更变量（指引侧单变量=§3A 类别 4 示例 c 收窄替换，见 "
            "changed_variables[0]；协议侧派发层一项=v1.2 工具行为规约，不改"
            "判读语义，见 changed_variables[1] 与 protocol_amendment）；渲"
            "染/GT/阈值零变更"),
        "unchanged_components": [
            "渲染：R5 冻结渲染件逐字节复用（零仪器变更、零重渲染；四件 PNG "
            "实测=在案见证常量）",
            "角色与盲读纪律（r12 指引 §1，逐字承 r9 指引）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r12 指引 §2）",
            "§3 邻域框收窄判据与坐标口径（r12 指引 §3，逐字承 r9 指引）",
            "§3A 类别判据示例：6 类中除类别 4 示例 c 收窄替换外全部逐字承 "
            "r9 指引（类别 4 示例 a、b 原文保留；§3A 末尾 r9 对照说明原位保"
            "留、其后另增 r12 对照说明）",
            "§4 全文：总原则「宁可 abstain 不硬标」、两条显式判据、存在性判"
            "断一般判据、三路出口显式化、confidence 定义与弃权 flag 输出细"
            "节、既有对照说明（含 r8/r9 增补块）原文原位（r12 指引 §4，逐字"
            "承 r9 指引）",
            "courtyard 中性说明（r12 指引 §5，逐字承 r9 指引）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r12 指引 §6，仅视角前缀/示例 reader-id 机械替换）",
            "格式对齐提示（r12 指引 §7；fail-closed 校验口径，逐字承 r9 指"
            "引）",
            "bottom 视口径：沿用 r4 指引不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算；为 bottom 单独定图层清单属渲染侧变"
            "更，不在本轮）",
            "GT 集：照 s41（r9 close）口径零改动（gt-audit-r1 三候选全部关"
            "闭在案；GT 侧不再有候选，round11-dev-record next_iteration_"
            "targets[4] 在案）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作"
            "口径引用）",
            "评估协议文件：evaluation-protocol-v1.md 零字节保留（v1.2 追加"
            "式修订只记于本记录，不回写 v1 文件，见 protocol_amendment）",
            "机械替换仅：视角前缀 R9T/R9B→R12T/R12B；round_id_constant "
            "2026-09-07-r9→2026-09-07-r12（及示例中 reader-r9→reader-r12）；"
            "标题轮次标识 R9→R12",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；bottom 零旗标分母=0 时弃权率按 "
            "cal._ratio 先例=None 口径照旧（r10/r11 在案）；渲染侧 bottom "
            "图层清单属渲染侧变更，仍为后续轮候选（round11-dev-record "
            "next_iteration_targets[2] 在案），不在本轮"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R12 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注册，"
                "聚合口径全部如实并列、不二选一、不挑优"),
            "items": [
                {
                    "item": 1,
                    "name": "主记录单位=实例",
                    "text": (
                        "每实例给出其视角两板合计的 flag_count、abstain_count、"
                        "abstain_rate（分母=该实例该视角全部旗标，跨两板合"
                        "计）、非弃权旗标清单、逐旗与 GT 的 containment/"
                        "area_ratio 匹配明细（比较器 fail-closed 校验照旧）"),
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
                        "例间范围（min..max）；代表配置 joint 结果、per-metric"
                        " 实例间范围、逐实例原始记录（item 1）三者并列如实呈"
                        "现，不合并、不挑优；APR-0011 阈值零改动"),
                },
                {
                    "item": 5,
                    "name": "bottom 零旗标处理",
                    "text": (
                        "沿用库侧 cal._ratio 先例（pcbflow/calibration.py "
                        "_ratio：零分母→None）——实例/视角层遇零旗标分母时"
                        "弃权率=None+文字说明，不编造数值（r10 run-record "
                        "bottom=0/0→None 同口径在案）"),
                },
            ],
        },
        "hypothesis_test": {
            "hypothesis_id": "r11-dev-record-candidate-1-example-c-tighten",
            "hypothesis": (
                "示例 c 收窄后，「形态非整段规则周期却援引等长/蛇形候选解释」"
                "的滥用型弃权旗被消除（该类形态按 §4 直接走弃权或关注路径，"
                "弃权理由不再引用候选解释），同时边界条款方向的非弃权 reroute "
                "报告保留。"),
            "test_design": (
                "单变量指引侧变更轮（+协议侧派发层规约）：指引由 r9 指引"
                "（r11 轮零字节复用件，a0c10154）机械变换生成 observation-"
                "guidance-r12.md（§3A 类别 4 示例 c 收窄替换+§3A 末尾 r12 "
                "对照说明+头部机械替换），渲染 R5 冻结件复用、GT/阈值零变"
                "更；协议侧 evaluation-protocol-v1→v1.2 追加式（派发层工具"
                "行为规约，读者不可见，不改判读语义）；12 次盲读=4 视角格×"
                "3 实例（v1.1 多实例口径沿用）。"),
            "baseline_reference": {
                "note": (
                    "r10/r11 实测基线（编排侧记录；引用已落盘 run-record 在"
                    "案值；数字仅入 prep-record，不进指引文件——指引零轮次"
                    "结果数字）。滥用型弃权旗=reroute 类弃权旗且 "
                    "location_evidence 援引等长/蛇形候选解释、所述形态非整段"
                    "规则周期；边界条款方向的非弃权 reroute=按示例 c 边界条"
                    "款（形态不规则、无规律→按关注现象）报告，属正确用法保"
                    "留。"),
                "r10": {
                    "misuse_abstain_flag_count": 2,
                    "detail": (
                        "R10T-012/R10T-013（均弃权；location_evidence 明确"
                        "援引「按 r9 示例 c 与第 4 节判据」后仍走弃权路径）"),
                },
                "r11": {
                    "misuse_abstain_flag_count": 1,
                    "detail": (
                        "R11T-006（弃权；描述「形态规整但不呈规则周期折叠」"
                        "并援引等长/保护类候选解释）"),
                    "boundary_non_abstain_reroute_count": 2,
                    "boundary_detail": (
                        "R11T-018/R11T-020（非弃权；按示例 c 边界条款「形态"
                        "不规则、无规律，按关注现象报告」——属正确用法，收"
                        "窄后应保留）"),
                },
                "sources": {
                    "r10": quotes["r10_run_record_ref"],
                    "r11": quotes["r11_run_record_ref"],
                },
            },
            "support_condition": (
                "R12 盲读中滥用型弃权旗=0（操作化定义：close 侧对 reroute "
                "类弃权旗的 location_evidence 做「等长|蛇形」子串 fail-"
                "closed 检出后，逐条核对形态描述——凡引用候选解释且描述为局"
                "部波状/抖动/单次大弯折/大范围绕行者计滥用型）且 reroute 类"
                "非弃权旗≥1（边界报告方向保留），则收窄生效获支持。"),
            "reject_condition": (
                "滥用型弃权旗≥1，则收窄措辞未生效（reader 仍以候选解释为由"
                "对非周期形态弃权），如实记录。"),
            "null_result_note": (
                "结果无论方向如实；若 R12 盲读 reroute 类旗标总量=0（刺激/"
                "判读双重缺席），记「不可判」并如实（不是支持）；n=3、跨轮"
                "实例群混杂照旧；描述性边界非 APR-0011 门。"),
            "declaration": (
                "滥用型弃权旗计数（本轮假设主通道）按操作化定义如实计算、逐"
                "旗引用原文 substring 证据；reroute 类弃权/非弃权分列、轮内 "
                "n=3 实例分布照常如实记录（APR-0011 阈值零改动、门照常独立"
                "计算）；跨实例=同轮同指引（工具规约统一后），跨轮对比=方向"
                "性；「正确测出无效同样是有效证据」。"),
            "preregistered_criteria_quote": {
                "candidate_0_target": quotes["proto_candidate_target"],
                "candidate_1_target": quotes["guidance_candidate_target"],
                "user_directive_2026_09_07": quotes["user_directive"],
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round11-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R11_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": quotes["indices_zero_based"],
                "note": (
                    "引用两项原文逐字摘录（措辞按文件原文，未改写）：索引 "
                    "[0]=跨轮可比性协议候选（协议侧；固定 reader 工具行为规"
                    "约=本轮 v1.2 执行案；每轮固定实例混合配比=同条目另一"
                    "案，未在本轮执行）；索引 [1]=示例 c 措辞修改（指引侧候"
                    "选，本轮执行的指引侧变更，用户 2026-09-07 已拍板排程 "
                    "R12）。两项先于 R12 盲读落盘预注册（本记录=预注册件）。"),
            },
            "primary_channel_metric": (
                "滥用型弃权旗计数（操作化定义见 support_condition：close 侧"
                "对 reroute 类弃权旗 location_evidence 做「等长|蛇形」子串 "
                "fail-closed 检出后逐条核对形态描述，逐旗引用原文 substring "
                "证据；执行由编排侧在 close 包执行）。"),
            "metric_lesson_application": (
                "r9→r11 教训链延续（产量计数+构成分析互补；round11-dev-"
                "record「效果随实例而异」的实例分层记录照旧：reroute 类逐实"
                "例产量与弃权/非弃权选择逐实例如实分列，不聚合掩盖）；本轮"
                "主通道=滥用型弃权旗计数（构成分析）而非单一聚合弃权率；全"
                "部预注册于本记录、先于盲读冻结，不追溯改判既往轮次（r8/r9/"
                "r10/r11 字母裁决维持不变）。"),
            "secondary_observation": (
                "工具规约 v1.2 首轮的轮内一致性（实例间弃权率极差如实分列，"
                "预期实例间弃权率极差维持小带；r11 基线 top 0.154/bottom 0.0 "
                "在案——数字仅入本编排侧记录）；courtyard 密集旗被动追踪延"
                "续（零阈值改动零期望；round11-dev-record next_iteration_"
                "targets[3] 在案）；bottom 零旗标=None 口径照旧（pcbflow/"
                "calibration.py _ratio 先例）。"),
        },
        "attribution_plan": {
            "declaration": (
                "本轮变更变量恰两项（指引侧单变量=示例 c 收窄替换、协议侧派"
                "发层=v1.2 工具行为规约）、检验恰一个假设（round11-dev-"
                "record next_iteration_targets[1]；hypothesis_id=r11-dev-"
                "record-candidate-1-example-c-tighten）；归因分层：reroute "
                "类主通道指标主要归因于措辞收窄（工具规约不改变分类判据语"
                "义）；跨轮对比（vs r10/r11）为方向性（实例群+工具代际混杂"
                "照旧声明）；轮内 n=3 分布=工具规约下的新一致性基线"),
            "primary_channel": {
                "change": (
                    "reroute-example-c-full-segment-periodic-tighten（指引"
                    "侧单变量）"),
                "metric": (
                    "滥用型弃权旗计数（操作化定义：close 侧对 reroute 类弃"
                    "权旗 location_evidence 做「等长|蛇形」子串 fail-closed "
                    "检出后逐条核对形态描述，逐旗引用原文 substring 证据）；"
                    "reroute 类非弃权旗计数并列（边界报告方向）"),
                "support": (
                    "滥用型弃权旗=0 且 reroute 类非弃权旗≥1 → 收窄生效获支"
                    "持"),
                "reject": (
                    "滥用型弃权旗≥1 → 收窄措辞未生效，如实记录"),
            },
            "guard_channel": {
                "metric": (
                    "其余类别非弃权旗 frame_box_pct 几何门（面积比出局条"
                    "目）"),
                "requirement": (
                    "§3 收窄判据零变更（逐字承 r9 指引），非弃权框仍须满"
                    "足；几何门面积比出局条目无回升"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角层三"
                "分列聚合+GT 匹配双口径+联合门代表配置/范围并列；APR-0011 阈"
                "值零改动）；轮内 n=3 实例分布=工具规约 v1.2 下的新一致性基"
                "线（首轮）；归因分组逻辑由编排侧在 close 包执行；本指引零 "
                "GT、零轮次结果数字（基线数字仅入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "本轮指引侧变更为收紧方向（候选解释可用前提收窄）：示例 c 由「规"
            "则周期形态本身可按一般判据推理、常规设计解释是候选解释之一」收"
            "窄为「仅整段规则周期形态适用该候选解释」——不构成任何放宽；「"
            "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由"
            "」反放宽条款原样保留；§3/§4/§3A 其余示例一字不动，不降低任何存"
            "在性、归类、定位或报告的责任门槛；协议侧 v1.2 工具行为规约只固"
            "定判读输入手段、不触碰判据文本；APR-0011 门（gt_recall≥0.75/"
            "seed_match_rate≥0.5/abstain_rate≤0.5）与 CONTAINMENT_MIN/"
            "AREA_RATIO_MAX 常量零改动；度量设计五条聚合口径沿用 v1.1、不构"
            "成任何门的放宽或收紧——门照常独立计算"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "derivation-log-*、任何 compare/评估产物；指引作者唯一输入="
            "observation-guidance-r9.md（=r11 轮零字节复用件，a0c10154 锚 "
            "fail-closed，本脚本只读零写入）+包指令；r11-prep-record.json "
            "仅用于取 renders-r5 PNG 见证常量与链交叉核对（hash 锚="
            "9074df2d 先验证）；round11-dev-record.json 仅读取 "
            "next_iteration_targets 与 hypothesis_test_i.preregistered_"
            "criteria_quote.user_directive_2026_09_07、run_record_ref、"
            "r10_contrast_ref 字段取预注册原文摘录与在案引用（hash 锚="
            "66e41bbf 先验证）；render-framing-r5.json 仅输入链复核；"
            "observation-guidance-r12.md 落盘即冻结；reader 派发（后续编排"
            "侧执行）上下文=observation-guidance-r12.md+单张 PNG+派发指令"
            "（R12T/R12B 前缀、reader-r12-{top,bottom}-i{1,2,3}、v1.2 工具"
            "行为规约硬性条款），零 GT、零其他盘上文件；跨实例/跨视角禁止交"
            "流（12 次盲读相互独立、不得交换判读信息——独立性是多实例协议"
            "的前提）。"),
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (FRAMING_R5, R11_PREP_RECORD, R11_DEV_RECORD, GUIDANCE_R9):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r11_record = json.loads(R11_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    dev_record = json.loads(R11_DEV_RECORD.read_text(encoding="utf-8"))
    r11_record_sha = _sha(R11_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)
    dev_record_sha = _sha(R11_DEV_RECORD)
    if not r11_record_sha.startswith(R11_PREP_RECORD_SHA_PREFIX):
        _fail(f"r11-prep-record sha 前 8={r11_record_sha[:8]} != 预期 "
              f"{R11_PREP_RECORD_SHA_PREFIX}（见证来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R11_DEV_RECORD_SHA_PREFIX):
        _fail(f"round11-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R11_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if r11_record.get("schema_version") != "3.0":
        _fail("r11-prep-record schema_version != 3.0（结构漂移）")
    if r11_record.get("kind") != "tl2_calibration_r11_prep_record":
        _fail("r11-prep-record kind 不符（结构漂移）")
    if r11_record.get("round_id_constant") != "2026-09-07-r11":
        _fail("r11-prep-record round_id_constant != 2026-09-07-r11（结构漂移）")
    if dev_record.get("round_id") != "2026-09-07-r11":
        _fail("round11-dev-record round_id != 2026-09-07-r11（结构漂移）")

    # ---- r9 指引零字节复核（基准指引=「r11 指引」；只读）----
    guidance_r9_sha = _sha(GUIDANCE_R9)
    if not guidance_r9_sha.startswith(GUIDANCE_R9_SHA_PREFIX):
        _fail(f"r9 指引 sha 前 8={guidance_r9_sha[:8]} != 预期 "
              f"{GUIDANCE_R9_SHA_PREFIX}（基准指引疑被改动，立即停止）")
    registered_guidance_sha = (r11_record.get("guidance_reuse") or {}).get("sha256_measured")
    if registered_guidance_sha != guidance_r9_sha:
        _fail("r11-prep-record guidance_reuse.sha256_measured 登记值与盘上"
              "实测不符（链自洽破坏，立即停止）")

    # ---- framing 链自洽（与 r11-prep-record 登记交叉核对）----
    registered_framing_sha = (r11_record.get("renders_reuse") or {}).get(
        "framing_reference", {}).get("sha256")
    if registered_framing_sha != framing_sha:
        _fail("r11-prep-record renders_reuse.framing_reference.sha256 登记"
              "值与盘上实测不符（链自洽破坏，立即停止）")

    png_constants = _load_png_witness_constants(r11_record)
    _check_framing_raster_field(framing)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)
    quotes = _extract_preregistration_quotes(dev_record)

    # ---- 指引构建 + byte-exact 自证 + 防覆写守卫 ----
    r9_text = GUIDANCE_R9.read_text(encoding="utf-8")
    guidance_text = build_guidance(r9_text)
    if build_guidance(r9_text) != guidance_text:
        _fail("同参重建不一致（byte-exact 破坏）: observation-guidance-r12.md")
    guidance_bytes = guidance_text.encode("utf-8")

    if GUIDANCE_R12.exists():
        existing = GUIDANCE_R12.read_bytes()
        if existing != guidance_bytes:
            _fail("observation-guidance-r12.md 已存在且重建字节不一致"
                  "（防覆写；拒绝覆写）")
        print("[r12-prep] 重跑自证：observation-guidance-r12.md 重建字节与既有"
              "文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。")
    else:
        GUIDANCE_R12.write_bytes(guidance_bytes)
        if GUIDANCE_R12.read_bytes() != guidance_bytes:
            _fail("回读不一致: observation-guidance-r12.md")
    guidance_r12_sha = _sha(GUIDANCE_R12)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r11_record_sha=r11_record_sha,
                          dev_record_sha=dev_record_sha,
                          guidance_r9_sha=guidance_r9_sha,
                          guidance_r12_sha=guidance_r12_sha,
                          pdf_results=pdf_results,
                          png_results=png_results,
                          quotes=quotes)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r11_record_sha=r11_record_sha,
                           dev_record_sha=dev_record_sha,
                           guidance_r9_sha=guidance_r9_sha,
                           guidance_r12_sha=guidance_r12_sha,
                           pdf_results=pdf_results,
                           png_results=png_results,
                           quotes=quotes)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r12-prep-record")

    # ---- 顶层键集合与 r11-prep-record 镜像断言（文档化差异：-guidance_reuse +guidance）----
    expected_keys = (set(r11_record.keys())
                     - set(TOP_LEVEL_KEY_DELTA_REMOVE)
                     | set(TOP_LEVEL_KEY_DELTA_ADD))
    if set(record.keys()) != expected_keys:
        _fail(f"r12-prep-record 顶层键集合与 r11-prep-record 镜像（文档化差"
              f"异：-{TOP_LEVEL_KEY_DELTA_REMOVE} +{TOP_LEVEL_KEY_DELTA_ADD}）"
              f"不符：多={sorted(set(record.keys()) - expected_keys)}，"
              f"少={sorted(expected_keys - set(record.keys()))}")
    ht_expected = (set(r11_record["hypothesis_test"].keys())
                   - set(HT_KEY_DELTA_REMOVE)
                   | set(HT_KEY_DELTA_ADD))
    if set(record["hypothesis_test"].keys()) != ht_expected:
        _fail(f"hypothesis_test 键集合镜像（文档化差异："
              f"-{HT_KEY_DELTA_REMOVE} +{HT_KEY_DELTA_ADD}）不符："
              f"多={sorted(set(record['hypothesis_test'].keys()) - ht_expected)}，"
              f"少={sorted(ht_expected - set(record['hypothesis_test'].keys()))}")

    # ---- 结构自证：changed_variables 恰 2 项、度量设计五条、域声明 ----
    cv = record["changed_variables"]
    if not isinstance(cv, list) or len(cv) != 2:
        _fail("changed_variables 必须恰 2 项（指引侧单变量+协议侧派发层）")
    if cv[0]["old_text"] != OLD_EXAMPLE_C_LINE or cv[0]["new_text"] != NEW_EXAMPLE_C_LINE:
        _fail("changed_variables[0] 新旧全文对照与指引变换常量不符")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5（预注册度量设计）")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"]["zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved 必须为真")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r12-prep] 重跑自证：r12-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r12-prep] 工件 sha256："
                  f"observation-guidance-r12.md={guidance_r12_sha}；"
                  f"r12-prep-record.json={hashing.sha256_bytes(existing)}")
            print(f"[r12-prep] 基准指引零字节复核（收工侧随编排另验）："
                  f"observation-guidance-r9.md={guidance_r9_sha}")
            return
        _fail("r12-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r12-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r12-prep] 验证通过：基准指引锚 {GUIDANCE_R9_SHA_PREFIX} OK"
          f"（只读，零写入）；r11-prep-record 见证来源锚 "
          f"{R11_PREP_RECORD_SHA_PREFIX} OK；round11-dev-record 锚 "
          f"{R11_DEV_RECORD_SHA_PREFIX} OK（预注册两项=索引 "
          f"{quotes['indices_zero_based']} 原文摘录在案）；renders-r5 四件 "
          f"PNG 实测=在案见证常量（magic OK）；R5 冻结输入 PDF "
          f"{len(pdf_results)} 件全 match")
    print(f"[r12-prep] 指引变换断言全过（示例 c 收窄替换=§3A 类别 4、r12 对"
          f"照说明=r9 对照说明之后 §4 之前、r9/r8 增补块原位保留、机械替换恰"
          f"四处、输出侧禁词断言零 GT/零轮次结果数字）")
    print(f"[r12-prep] 写出：observation-guidance-r12.md sha256={guidance_r12_sha}")
    print(f"[r12-prep] 写出：r12-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致；顶层键镜像 r11，文档化"
          f"差异：-guidance_reuse +guidance）")


if __name__ == "__main__":
    main()
