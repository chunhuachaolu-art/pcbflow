#!/usr/bin/env python
"""CAL-R15-PREP：R15 指引侧单变量轮预备包（只新建两个文件：
out/v3-tl2/calibration/observation-guidance-r15.md 与
out/v3-tl2/calibration/r15-prep-record.json；datasets/ 与 out/ 既有
文件只读、零改动，observation-guidance-r13.md 零字节不动）。

R15 轮性质（预注册，非事后）：**指引侧单变量轮（bottom 配色语义仪器
注记配套轮）**——渲染零变更（renders-r14b 四图字节复用，四 PNG 实测
sha256 与 render-witness-r14b.json 登记值 fail-closed 比对）；本轮唯一
指引侧变量=新增 §5A 渲染配色仪器注记节（颜色→来源映射显式化：橙=
白墨图元重着色、绿=板内空隙白重着色非图元；数值事实自 render-framing-
r14b.json/render-witness-r14b.json 结构探测转录，不凭记忆写）。执行
round14-dev-record next_iteration_targets[0]（r14 reject 预注册拒绝支第
二支「无图例配色引发混淆性弃权上升」所指向的指引侧配套），用户
2026-09-08「请继续」批准。§2–§7 判据文本逐字承 r13（分段+substring
双重断言）；反放宽条款与三路出口逐字保留。

指引生成=确定性机械变换（锚串命中数 fail-closed）。任务枚举 4 处编辑：
(1) 标题行替换；(2) 本轮变更声明节正文整体替换；(3) §6 标题前插入
§5A 节；(4) 示例旗 ID 前缀 R13T-（4 处）/R13B-（1 处）→R15T-/R15B-。
另沿 s48_calibration_r13_prep.py（r12→r13 指引侧轮）机械变换先例同步
轮次标识区（非任务枚举 4 处、如实登记）：round_id_constant bullet
2026-09-08-r13→2026-09-08-r15、「本轮性质」行按 r15 口径重写、示例
reader-id reader-r13→reader-r15——声明的「更新标题与轮次标识」因此
成立，指引内无 r13 失实头部陈述。§1 与头部 bullet 区不在逐字冻结清单
（冻结区=§2–§7）。

功能：
  1. fail-closed 复核 observation-guidance-r13.md（c28806e1 锚；r15
     指引唯一变换基座，只读零写入）。
  2. fail-closed 复核 r14-prep-record.json（93440a3d 锚、
     schema_version=3.0、kind、round_id_constant）。
  3. fail-closed 复核 round14-dev-record.json（round_id=2026-09-08-r14；
     next_iteration_targets 按「指引侧颜色-图层映射配套」标记唯一定位
     并要求实测索引=[0]；原文逐字摘录；实测 sha 入记录）。
  4. fail-closed 复核 render-framing-r14b.json（7004b017 锚、
     round_id_constant=2026-09-08-r14b）：vector_attribution 白墨图元
     162 fill+4 stroke（applied/prep1 同值）、board_white_coverage 板内
     空隙白 final=206632/strict=206052（两板同值）——§5A 转录源。
  5. fail-closed 复核 render-witness-r14b.json（b63771f9 锚、kind、
     round_id_constant）：配色语义（白墨图元→橙 [255,165,0]、板内空隙
     白→绿 [0,128,0]）、两板 palette_assertion_summary.assertions_pass
     为真且橙 81672/绿 206632 两板相同；四 PNG 见证登记值提取。
  6. 渲染零变更实测：renders-r14b 四 PNG magic+sha256_file 实测并与
     witness 登记值逐字比对（applied-bottom/prep1-bottom=
     renders.applied/prep1.sha256=d7284259…；applied-top/prep1-top=
     top_zero_change_copies.sha256=298bc620…/b2f84524…）——四图即
     r14 轮盲读所用同一批文件，字节复用成立。
  7. fail-closed 复核 evaluation-protocol-v1.md 在盘且锚=22dc7337。
  8. 生成 observation-guidance-r15.md（7 组锚定编辑，命中数逐一断言；
     §2–§7 分段逐字保留断言+关键 substring 断言+R13 残留零断言）。
  9. 落盘 r15-prep-record.json（canonical JSON=hashing.canonical_json_
     bytes：ensure_ascii=False/sort_keys/indent=1/LF；顶层键集合与
     r14-prep-record 逐键镜像；hypothesis_test=预注册判据逐字；同参
     重建两次逐字节一致自证；防覆写守卫——目标已存在且重建字节非逐
     字节等同→FAIL，等同→幂等通过（零覆写）；落盘后回读验字节）。
 10. 打印：两文件 sha256（sha256_file）、r15 相对 r13 字节数差、§5A
     节全文回显、四 PNG 比对结果、逐项断言通过清单。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-08 / 2026-09-08-r15）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / reader-raw-* /
calibration-run-* / derivation-log-* / 任何 compare 产物；无 git；
r13 指引只读；记录内零 GT、零期望数量/分布/坐标（162/4/206632/206052/
81672 为仪器侧配色与像素计数事实，非板面内容断言）；指引内零轮次
结果数字。

用法：python scripts/s54_calibration_r15_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R13 = CAL_DIR / "observation-guidance-r13.md"
GUIDANCE_R15 = CAL_DIR / "observation-guidance-r15.md"
R14_PREP_RECORD = CAL_DIR / "r14-prep-record.json"
R14_DEV_RECORD = CAL_DIR / "round14-dev-record.json"
FRAMING_R14B = CAL_DIR / "render-framing-r14b.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r15-prep-record.json"

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r15"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R13_SHA_PREFIX = "c28806e1"
R14_PREP_RECORD_SHA_PREFIX = "93440a3d"
FRAMING_R14B_SHA_PREFIX = "7004b017"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 渲染零变更见证（render-witness-r14b.json 登记值；四 PNG 实测逐一
#: fail-closed 比对。bottom=renders.{applied,prep1}.sha256；
#: top=top_zero_change_copies.{applied-top,prep1-top}.sha256）
RENDERS_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
R14B_BOTTOM_SHA_PREFIX = "d7284259"

#: §5A 数值事实（仪器侧转录目标值；结构探测不符即停，转录不凭记忆）
EXPECTED_WHITE_FILL_COUNT = 162
EXPECTED_WHITE_STROKE_COUNT = 4
EXPECTED_VOID_FINAL = 206632
EXPECTED_VOID_STRICT = 206052
EXPECTED_ORANGE_RGB = [255, 165, 0]
EXPECTED_GREEN_RGB = [0, 128, 0]
EXPECTED_ORANGE_PX = 81672
EXPECTED_GREEN_PX = 206632

#: round14-dev-record next_iteration_targets 候选项内容定位标记
MARK_CANDIDATE = "指引侧颜色-图层映射配套"

# ---------------------------------------------------------------------------
# 指引机械变换锚与替换文本
# ---------------------------------------------------------------------------
OLD_TITLE = "# R13 轮 reader 判读指引（observation-guidance-r13）"
NEW_TITLE = "# R15 轮 reader 判读指引（observation-guidance-r15）"
DECL_HEADING = "## 本轮变更声明（预注册，非事后）"
SECTION1_HEADING = "## 1. 角色与任务"
SECTION6_ANCHOR = "## 6. 输出格式"
OLD_ROUND_ID = "2026-09-08-r13"
NEW_ROUND_ID = "2026-09-08-r15"
OLD_READER_ID = "reader-r13"
NEW_READER_ID = "reader-r15"
OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（§4 存在性判断一般判据可操作化"
    "轮）**。渲染零变更（复用 R5 冻结渲染件）；本轮唯一变更=判读指引 "
    "§4 存在性判断一般判据可操作化替换（预注册见下），指引落盘后由编"
    "排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（bottom 配色语义仪器注记配套"
    "轮）**。渲染零变更（复用 R14 冻结渲染件 renders-r14b）；本轮唯一"
    "变更=判读指引增补 §5A 渲染配色仪器注记节（颜色→来源映射显式化；"
    "预注册见下），指引落盘后由编排侧重新盲读。")

#: 任务枚举编辑 2：本轮变更声明正文（逐字）
NEW_DECLARATION = (
    "本轮（R15）为指引侧单变量轮：相对 observation-guidance-r13 仅（1）"
    "更新标题与轮次标识，（2）重写本变更声明，（3）新增 §5A 渲染配色仪"
    "器注记节，（4）虚构示例旗 ID 前缀改为 R15T/R15B。§2 类别枚举、§3/"
    "§3A 位置与判据示例、§4 置信度与弃权（含量化判据 (i)(ii)(iii) 与接"
    "触性判据）、§5 courtyard 说明、§6 输出格式、§7 格式对齐提示全部逐"
    "字不变。渲染零变更：本轮使用与 R14 完全相同的 renders-r14b 四图"
    "（字节复用）。预注册判据见 r15-prep-record.json hypothesis_test"
    "（先于任何盲读冻结）。")

#: §5A 标题（任务枚举编辑 3 的节标题，逐字）
SECTION_5A_HEADING = "## 5A. 渲染配色仪器注记（bottom 配色语义；仪器事实，非判据）"

#: 锚串在 r13 基座中的期望命中数（不符即停；edit 5/7 的命中数以编辑 2
#: （声明正文整体替换）执行之后剩余的 r13 自引为口径）
EXPECTED_HITS = {
    "title": 1,
    "decl_heading": 1,
    "section1": 1,
    "section6_anchor": 1,
    "nature_line": 1,
    "prefix_R13T-": 4,
    "prefix_R13B-": 1,
    "round_id_after_decl": 1,
    "reader_id_after_decl": 1,
}

#: §2–§7 分段逐字保留断言（起点标题锚, 终点标题锚；§5 段以 §6 锚截尾，
#: 其后紧接新插入的 §5A——substring 断言不受影响；§6/§7 段先做旗前缀
#: 规格化（R13T-/R13B-→R15T-/R15B-）再断言）
SECTION_PAIRS = [
    ("## 1. 角色与任务", "## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）"),
    ("## 2. 类别枚举（封闭集；逐字取自代码常量，禁止发明类别）", "## 3. 位置口径"),
    ("## 3. 位置口径", "## 3A. 类别判据示例（判据说明，非期望清单）"),
    ("## 3A. 类别判据示例（判据说明，非期望清单）", "## 4. 置信度与弃权"),
    ("## 4. 置信度与弃权", "## 5. courtyard 说明（中性）"),
    ("## 5. courtyard 说明（中性）", "## 6. 输出格式"),
    ("## 6. 输出格式（reader-raw 文件的确切 schema）",
     "## 7. 格式对齐提示"),
    ("## 7. 格式对齐提示", None),  # 至文件尾
]

#: 关键 substring 断言（判据零放宽；逐条打印通过情况）
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
}

#: hypothesis_test=预注册判据（逐字，先于任何盲读冻结；不得改写数值或口径）
HYPOTHESIS_TEST = {
    "hypothesis_id": "r14-dev-record-candidate-0-guidance-color-legend",
    "hypothesis": (
        "r14 字母=reject 的机制=无图例配色引发混淆性弃权（bottom 全旗聚"
        "合弃权 14/14=1.0>10/11，同一绿色被三实例三种语义化）。若在指引"
        "仪器注记节显式化 bottom 配色语义（橙=白墨图元重着色；绿=板内空"
        "隙白重着色、非图元），则判读者对非图元色的语义化分歧收敛、混淆"
        "性弃权回落，且 r13 量化判据达成的 bottom courtyard 收敛（全实例"
        "非弃权=0）不回退。"),
    "adjudication": {
        "supported_requires_all": [
            "(i) courtyard 收敛维持：bottom courtyard 类旗标非弃权计数按"
            "实例 bottom-i1/i2/i3 全为 0（各实例含 applied+prep1 两派次；"
            "对照 r13/r14 的 0/0/0）",
            "(ii) 混淆回落：bottom 全旗聚合弃权率 ≤ 10/11（=0.909091，冻"
            "结基线=calibration-run-r13.json 同口径；bottom 零旗标时条件"
            "自动满足并记入机制观察）",
            "(iii) top 不回退：top 全旗聚合弃权率 ≤ run-r14 同口径聚合弃"
            "权率（冻结基线=calibration-run-r14.json，由比较脚本同一逻辑"
            "对基线与本轮双侧复算，不手工赋值）",
        ],
        "reject_if": (
            "(i) 不满足（图例引入新混淆或收敛不稳健），或 (ii)(iii) 任一"
            "不满足（图例不足以消除混淆/其他轴回退）"),
        "mechanism_observation_separate": (
            "绿色区域语义化方式按实例分布（对照 r14 三实例三种语义化：轮"
            "廓/连接形态/courtyard 矩形）；黑点类旗标延续观察；bottom 零"
            "旗标情形的构成如实记录"),
        "metric_lesson_separate": (
            "跨轮实例群漂移为已知混杂（r10 实证）；字母裁决=预注册判据命"
            "中与否的描述性结论，非因果证明；聚合与分层观察分开记账"),
        "descriptive_boundary_note": (
            "本轮判据均为描述性边界，与 APR-0011 门（gt_recall≥0.75/"
            "seed_match_rate≥0.5/abstain_rate≤0.5）与 CONTAINMENT_MIN/"
            "AREA_RATIO_MAX 常量分列、互不凌驾（门阈值零改动）；非门阈"
            "值、非期望清单"),
    },
}


def _fail(msg: str) -> None:
    print(f"[r15-prep] FAIL: {msg}")
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
    """机械替换规格化（§2–§7 分段断言用：r13 段落经 edit_list 所列、合法
    触及冻结段的机械替换——旗 ID 前缀与示例 reader_id——之后的期望文本）。"""
    return (text
            .replace("R13T-", "R15T-")
            .replace("R13B-", "R15B-")
            .replace("reader-r13", "reader-r15"))


# ---------------------------------------------------------------------------
# 指引生成（确定性机械变换；锚命中数逐一 fail-closed）
# ---------------------------------------------------------------------------

def build_guidance(base_text: str) -> tuple[str, list[dict]]:
    """由 r13 指引文本生成 r15 指引文本；返回 (r15 文本, edit_list)。"""
    t = base_text
    edits: list[dict] = []

    # ---- 编辑 2（先行）：本轮变更声明节正文整体替换（任务枚举编辑 2）----
    # 先行原因：声明正文含 r13 自引（2026-09-08-r13 / reader-r13 / R13T
    # 箭头记法），整体替换后轮次标识同步替换的命中数才收敛为头部唯一。
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
        "edit": 2,
        "kind": "本轮变更声明节正文整体替换（任务枚举编辑 2，逐字）",
        "region": "「## 本轮变更声明（预注册，非事后）」标题行之后至"
                  "「## 1. 角色与任务」之前的正文整体",
        "expected_hits_decl_heading": 1,
        "expected_hits_next_section_anchor": 1,
    })

    # ---- 编辑 1：标题行替换（任务枚举编辑 1）----
    t = _replace_counted(t, OLD_TITLE, NEW_TITLE,
                         EXPECTED_HITS["title"], "标题行")
    edits.append({
        "edit": 1,
        "kind": "标题行替换（任务枚举编辑 1）",
        "old": OLD_TITLE,
        "new": NEW_TITLE,
        "expected_hits": EXPECTED_HITS["title"],
    })

    # ---- 编辑 6：轮次标识同步（s48 先例；非任务枚举 4 处，如实披露）----
    t = _replace_counted(t, OLD_ROUND_ID, NEW_ROUND_ID,
                         EXPECTED_HITS["round_id_after_decl"],
                         "round_id_constant bullet")
    edits.append({
        "edit": 6,
        "kind": "轮次标识同步（s48_calibration_r13_prep r12→r13 机械变换"
                "先例；非任务枚举 4 处，如实披露）",
        "old": OLD_ROUND_ID,
        "new": NEW_ROUND_ID,
        "expected_hits_after_edit_2": EXPECTED_HITS["round_id_after_decl"],
        "note": "头部 bullet：- round_id_constant: `2026-09-08-r15`",
    })

    # ---- 编辑 7：本轮性质行重写（s48 先例；非任务枚举 4 处，如实披露）----
    t = _replace_counted(t, OLD_NATURE_LINE, NEW_NATURE_LINE,
                         EXPECTED_HITS["nature_line"], "本轮性质行")
    edits.append({
        "edit": 7,
        "kind": "本轮性质行重写（s48 先例；非任务枚举 4 处，如实披露）",
        "old": OLD_NATURE_LINE,
        "new": NEW_NATURE_LINE,
        "expected_hits": EXPECTED_HITS["nature_line"],
    })

    # ---- 编辑 8：示例 reader-id 同步（s48 先例；非任务枚举 4 处）----
    t = _replace_counted(t, OLD_READER_ID, NEW_READER_ID,
                         EXPECTED_HITS["reader_id_after_decl"],
                         "示例 reader-id")
    edits.append({
        "edit": 8,
        "kind": "示例 reader-id 同步（s48 先例；非任务枚举 4 处，如实披"
                "露）",
        "old": OLD_READER_ID,
        "new": NEW_READER_ID,
        "expected_hits_after_edit_2": EXPECTED_HITS["reader_id_after_decl"],
        "note": "§6 格式示例 reader_id：reader-r15-top",
    })

    # ---- 编辑 3：§6 标题前插入 §5A 节（任务枚举编辑 3；数值事实由调用
    #      方以结构探测值传入语义——本函数只负责锚定位置，§5A 文本经
    #      format 参数注入）----
    # （在 build_guidance_5a 中与数值事实绑定后另行拼接；此处先做前缀
    #   替换，§5A 插入放在 main 流程内以保证纯函数无隐藏依赖。）

    # ---- 编辑 4：示例旗 ID 前缀替换（任务枚举编辑 4）----
    t = _replace_counted(t, "R13T-", "R15T-",
                         EXPECTED_HITS["prefix_R13T-"], "旗前缀 R13T-")
    t = _replace_counted(t, "R13B-", "R15B-",
                         EXPECTED_HITS["prefix_R13B-"], "旗前缀 R13B-")
    edits.append({
        "edit": 4,
        "kind": "示例旗 ID 前缀替换（任务枚举编辑 4）",
        "items": [
            {"old": "R13T-", "new": "R15T-",
             "expected_hits": EXPECTED_HITS["prefix_R13T-"]},
            {"old": "R13B-", "new": "R15B-",
             "expected_hits": EXPECTED_HITS["prefix_R13B-"]},
        ],
    })

    return t, edits


def insert_section_5a(text_r15: str, section_5a_text: str) -> str:
    """在「## 6. 输出格式」标题前插入 §5A 节（任务枚举编辑 3）。"""
    n = text_r15.count(SECTION6_ANCHOR)
    if n != EXPECTED_HITS["section6_anchor"]:
        _fail(f"锚串命中数不符（§6 标题锚）：{SECTION6_ANCHOR!r} 命中 {n} "
              f"次 != 预期 {EXPECTED_HITS['section6_anchor']} 次（立即停止）")
    k = text_r15.index(SECTION6_ANCHOR)
    return text_r15[:k] + section_5a_text + text_r15[k:]


def build_section_5a(*, white_fill: int, white_stroke: int, void_final: int,
                     void_strict: int, orange_px: int, green_px: int) -> str:
    """§5A 节全文（数值事实由结构探测值注入；不凭记忆写）。"""
    return (
        SECTION_5A_HEADING + "\n"
        "\n"
        "- 本轮 bottom 渲染采用 R14b 配色（与 R14 相同，字节复用同一渲染"
        "件）。**橙色 (255,165,0)=原白色墨迹图元重着色**：白墨矢量图元 "
        f"{white_fill} fill + {white_stroke} stroke（焊盘钻孔圆盘+椭圆焊盘"
        "轮廓的白色填充，B.Cu∪B.Mask 双族共享绘制；B.Silkscreen/"
        "B.Courtyard/Edge.Cuts 族零白图元）——数量与层归属转录自编排侧 "
        "render-framing-r14b.json（vector_attribution："
        f"combined_white_fill_count={white_fill}、"
        f"combined_white_stroke_count={white_stroke}）；成图实测橙 "
        f"{orange_px} px（render-witness-r14b.json palette_assertion_"
        "summary，两板相同）。\n"
        "- **绿色 (0,128,0)=板内空隙白重着色**：墨缺失处页底背景透出的基"
        "材露白（铺铜 clearance/翼瓣空隙/板框退让带/基准环缝）——探针板"
        f"内空隙白 {void_final} px（final 口径）/ {void_strict} px（严格口"
        "径），转录自 render-framing-r14b.json（probe_block.board_white_"
        f"coverage）；成图实测绿 {green_px} px（render-witness-r14b.json，"
        "两板相同）。**绿色区域不是图元**：不是丝印、不是阻焊开窗图形、"
        "不是 courtyard 图形。\n"
        "- 本节为仪器事实（渲染生成语义），不构成任何判据、期望清单或"
        "「应判为正常/无需报告」的指示；旗标判定仍按 §2 类别枚举、§3A/"
        "§4 判据独立执行。对任意区域无法负责任判定时，按 §4 弃权规则弃"
        "权（理由照实写）。\n"
        "- top 渲染无配色变更（与既往轮次一致）。\n"
        "\n")


def assert_guidance_invariants(base_text: str, t15: str) -> list[str]:
    """§2–§7 分段逐字保留断言 + 关键 substring 断言 + R13 残留零断言。

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
        if norm not in t15:
            _fail(f"{label} 失败：r13 段落（旗前缀规格化后）未在 r15 中逐"
                  f"字保留（立即停止）")
        passed.append(label)

    # ---- 关键 substring 断言 ----
    for label, needle in REQUIRED_SUBSTRING_VALUES.items():
        if needle not in t15:
            _fail(f"关键 substring 断言失败（{label}）：{needle!r} 未在 r15 "
                  f"指引中逐字保留（立即停止）")
        passed.append(label)

    # ---- R13 残留零断言（机械替换完备性）----
    for needle in ("R13T-", "R13B-", "R13T", "R13B", "R13 轮",
                   "2026-09-08-r13", "reader-r13"):
        n = t15.count(needle)
        if n != 0:
            _fail(f"R13 残留断言失败：{needle!r} 在 r15 指引中残留 {n} 次"
                  f"（立即停止）")
    passed.append("R13 残留零断言（R13T-/R13B-/R13T/R13B/R13 轮/"
                  "2026-09-08-r13/reader-r13 全部零命中）")

    # ---- 新文本在位断言 ----
    for needle, label in (
            (NEW_TITLE, "r15 标题在位"),
            (NEW_DECLARATION, "r15 变更声明在位"),
            (NEW_NATURE_LINE, "r15 本轮性质行在位"),
            (SECTION_5A_HEADING, "§5A 节标题在位"),
            ("`2026-09-08-r15`", "r15 round_id_constant bullet 在位"),
            ("reader-r15", "r15 示例 reader-id 在位"),
    ):
        n = t15.count(needle)
        if n != 1:
            _fail(f"新文本在位断言失败（{label}）：命中 {n} 次 != 1")
        passed.append(label)

    # ---- §5A 位置断言（§5 之后、§6 之前，恰一节）----
    i5 = t15.index("## 5. courtyard 说明（中性）")
    i5a = t15.index(SECTION_5A_HEADING)
    i6 = t15.index("## 6. 输出格式")
    if not (i5 < i5a < i6):
        _fail("§5A 位置断言失败：须位于 §5 之后、§6 之前")
    passed.append("§5A 位置断言（§5 < §5A < §6）")
    return passed


# ---------------------------------------------------------------------------
# 结构探测（fail-closed；§5A 数值事实转录源）
# ---------------------------------------------------------------------------

def probe_framing(framing: dict) -> dict:
    """render-framing-r14b：白墨图元计数与板内空隙白面积（两板同值断言）。"""
    if framing.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-framing-r14b round_id_constant 不符："
              f"{framing.get('round_id_constant')}")
    if framing.get("date_constant") != DATE_CONSTANT:
        _fail("render-framing-r14b date_constant != 2026-09-08")
    table = (framing.get("probe_block", {})
             .get("vector_attribution", {})
             .get("attribution_table", {}))
    coverage = framing.get("probe_block", {}).get("board_white_coverage", {})
    out = {}
    for state in ("applied", "prep1"):
        item = table.get(state, {})
        fill = item.get("combined_white_fill_count")
        stroke = item.get("combined_white_stroke_count")
        cov = coverage.get(state, {})
        vf = cov.get("board_white_on_void_final")
        vs = cov.get("board_white_on_void_strict")
        if (fill != EXPECTED_WHITE_FILL_COUNT
                or stroke != EXPECTED_WHITE_STROKE_COUNT):
            _fail(f"framing {state} 白墨图元计数不符：fill={fill} "
                  f"stroke={stroke}（预期 {EXPECTED_WHITE_FILL_COUNT}/"
                  f"{EXPECTED_WHITE_STROKE_COUNT}）")
        if vf != EXPECTED_VOID_FINAL or vs != EXPECTED_VOID_STRICT:
            _fail(f"framing {state} 板内空隙白不符：final={vf} strict={vs}"
                  f"（预期 {EXPECTED_VOID_FINAL}/{EXPECTED_VOID_STRICT}）")
        out[state] = {"white_fill": fill, "white_stroke": stroke,
                      "void_final": vf, "void_strict": vs}
    if out["applied"] != out["prep1"]:
        _fail("framing 两板探针值不一致（白墨图元/空隙白面积）")
    return out["applied"]


def probe_witness(witness: dict) -> dict:
    """render-witness-r14b：配色语义/成图实测调色板/四 PNG 见证登记值。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")
    if witness.get("date_constant") != DATE_CONSTANT:
        _fail("render-witness-r14b date_constant != 2026-09-08")
    mapping = witness.get("color_mapping", {})
    ink = mapping.get("white_ink_drawings", {}).get("target_rgb")
    void = mapping.get("board_void_white", {}).get("target_rgb")
    if ink != EXPECTED_ORANGE_RGB:
        _fail(f"witness 白墨图元配色语义不符：{ink} != {EXPECTED_ORANGE_RGB}")
    if void != EXPECTED_GREEN_RGB:
        _fail(f"witness 板内空隙白配色语义不符：{void} != {EXPECTED_GREEN_RGB}")
    summary = witness.get("palette_assertion_summary", {})
    palette = {}
    for state in ("applied", "prep1"):
        item = summary.get(state, {})
        if item.get("assertions_pass") is not True:
            _fail(f"witness {state} palette_assertions_pass 不为真")
        palette[state] = {
            "orange_exact_count": item.get("orange_exact_count"),
            "green_exact_count": item.get("green_exact_count"),
        }
    if palette["applied"] != palette["prep1"]:
        _fail(f"witness 两板成图实测调色板不一致：{palette}")
    if palette["applied"]["orange_exact_count"] != EXPECTED_ORANGE_PX:
        _fail(f"witness 橙像素计数不符：{palette['applied']['orange_exact_count']}"
              f" != {EXPECTED_ORANGE_PX}")
    if palette["applied"]["green_exact_count"] != EXPECTED_GREEN_PX:
        _fail(f"witness 绿像素计数不符：{palette['applied']['green_exact_count']}"
              f" != {EXPECTED_GREEN_PX}")
    rendered = witness.get("renders", {})
    copies = witness.get("top_zero_change_copies", {})
    registered = {
        "applied-bottom": (rendered.get("applied", {}) or {}).get("sha256"),
        "prep1-bottom": (rendered.get("prep1", {}) or {}).get("sha256"),
        "applied-top": (copies.get("applied-top", {}) or {}).get("sha256"),
        "prep1-top": (copies.get("prep1-top", {}) or {}).get("sha256"),
    }
    for side, sha in registered.items():
        if not isinstance(sha, str) or len(sha) != 64:
            _fail(f"witness {side} 见证登记值缺失或非 64 位 sha256：{sha!r}")
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（与 r5→r14b 既有两板"
              "相同事实口径不一致）")
    return {
        "orange_target_rgb": list(ink),
        "green_target_rgb": list(void),
        "orange_px": palette["applied"]["orange_exact_count"],
        "green_px": palette["applied"]["green_exact_count"],
        "registered": registered,
    }


def check_renders_byte_reuse(registered: dict) -> list[dict]:
    """渲染零变更实测：四 PNG magic+sha256_file 实测 vs witness 登记值。"""
    results = []
    for side in RENDERS_SIDES:
        path = CAL_DIR / "renders-r14b" / f"{side}.png"
        if not path.exists():
            _fail(f"PNG 缺失：{path}")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        expect = registered[side]
        if measured != expect:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与 witness 登记值不"
                  f"符（渲染零变更声明被破坏）：measured={measured} "
                  f"registered={expect}")
        if side.endswith("-bottom") and not measured.startswith(
                R14B_BOTTOM_SHA_PREFIX):
            _fail(f"renders-r14b/{side}.png sha 前 8={measured[:8]} != 预期 "
                  f"{R14B_BOTTOM_SHA_PREFIX}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "witness_record": "out/v3-tl2/calibration/render-witness-r14b.json",
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "top_zero_change_copies." + side + ".sha256"),
            "sha256_witness_registered": expect,
            "match": True,
        })
    return results


def extract_candidate(dev_record: dict, dev_record_sha: str) -> dict:
    """round14-dev-record next_iteration_targets：按标记唯一定位并要求=[0]。"""
    if dev_record.get("round_id") != "2026-09-08-r14":
        _fail(f"round14-dev-record round_id 不符：{dev_record.get('round_id')}")
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round14-dev-record next_iteration_targets 结构不符")
    idx = [i for i, t in enumerate(targets)
           if isinstance(t, str) and MARK_CANDIDATE in t]
    if len(idx) != 1:
        _fail(f"next_iteration_targets 标记「{MARK_CANDIDATE}」定位歧义："
              f"{idx}")
    if idx[0] != 0:
        _fail(f"指引侧配套候选实测索引={idx[0]} != 授权给定 [0]")
    return {
        "path_rel": "out/v3-tl2/calibration/round14-dev-record.json",
        "sha256_measured": dev_record_sha,
        "field": "next_iteration_targets",
        "item_indices_zero_based": [idx[0]],
        "candidate_quote": targets[idx[0]],
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance13_sha: str, guidance15_sha: str,
                 guidance13_bytes: int, guidance15_bytes: int,
                 r14_record_sha: str, dev_ref: dict, framing_sha: str,
                 witness_sha: str, protocol_sha: str,
                 png_checks: list[dict], edit_list: list[dict],
                 section_asserts: list[str]) -> dict:
    """构建 r15-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r15_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r15",
        "round_nature": (
            "指引侧单变量轮（指引侧颜色-图层映射配套轮，第十五轮；r14 "
            "reject 预注册拒绝支第二支「无图例配色引发混淆性弃权上升」所"
            "指向的配套）：判读指引由 observation-guidance-r13.md 机械变"
            "换生成 observation-guidance-r15.md（本轮唯一判读依据；单变"
            "量=新增 §5A 渲染配色仪器注记节（颜色→来源映射显式化：橙=白"
            "墨图元重着色、绿=板内空隙白重着色非图元；r14 编排侧 "
            "color_semantics_note 在案事实转录指引侧）+轮次标识机械同步，"
            "见 guidance_reuse.edit_list）；渲染零变更=renders-r14b 四图字"
            "节复用（四 PNG sha256_file 实测与 render-witness-r14b.json 登"
            "记值 fail-closed 比对一致，即 r14 轮盲读所用同一批文件，见 "
            "instrument_change）；§2–§7 判据文本逐字承 r13（分段+substring"
            " 双重断言复核）、反放宽条款与三路出口逐字保留；GT/阈值/协议"
            "零变更（v1.1+v1.2 维持）；执行 round14-dev-record "
            "next_iteration_targets[0]（指引侧颜色-图层映射配套，实测链见 "
            "changed_variables[0].preregistration_ref），用户 2026-09-08「"
            "请继续」批准（见 user_directive_note）；r13 指引已在盘冻结、"
            "本轮只读零写入；盲读由编排侧在本记录之后以 12 次独立实例盲"
            "读执行"),
        "user_directive_note": (
            "用户 2026-09-08「请继续」=批准执行 round14-dev-record "
            "next_iteration_targets[0]（r15 指引侧颜色-图层映射配套，授权"
            "原文逐字摘录于 changed_variables[0].preregistration_ref."
            "candidate_quote；round14-dev-record.json 实测 sha256="
            f"{dev_ref['sha256_measured']}）：候选方案=仪器注记节增补 "
            "bottom 配色语义说明（橙=孔/开窗墨、绿=空隙非图元；r14 编排侧"
            " color_semantics_note 在案事实转录指引侧）；属指引侧变更、须"
            "预注册+单变量纪律（指引与仪器分轮单变量：本轮渲染零变更）；"
            "反放宽条款（「仅因形态不熟悉、不确定其设计含义，不构成判为"
            "正常设计特征的理由」）与三路出口一字保留；不得回溯改判既往"
            "轮次（r8–r14 字母裁决维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14 完全相同（字节复用），变化仅在指引文本",
        },
        "guidance_reuse": {
            "base": "observation-guidance-r13.md",
            "base_path_rel": "out/v3-tl2/calibration/observation-guidance-r13.md",
            "base_sha256": guidance13_sha,
            "derived": "observation-guidance-r15.md",
            "derived_path_rel": "out/v3-tl2/calibration/observation-guidance-r15.md",
            "derived_sha256": guidance15_sha,
            "byte_size": {"base": guidance13_bytes, "derived": guidance15_bytes,
                          "delta": guidance15_bytes - guidance13_bytes},
            "edit_list": edit_list,
            "verbatim_frozen_sections": (
                "§2 类别枚举、§3 位置口径、§3A 类别判据示例（含示例 c 与末"
                "尾对照说明）、§4 置信度与弃权（含量化判据 (i)(ii)(iii)、接"
                "触性判据、三路出口、反放宽条款、r6/r8/r13 对照说明块）、"
                "§5 courtyard 说明、§6 输出格式（旗 ID 展示前缀机械替换除"
                "外）、§7 格式对齐提示——分段逐字保留断言（r13 段落 substring"
                "-in 断言）+关键 substring 断言双重复核，见 "
                "verification.section_assertions_passed"),
            "lineage_note": (
                "轮次标识区同步（标题行/round_id_constant bullet/本轮性质"
                "行/示例 reader_id）沿 s48_calibration_r13_prep.py（r12→"
                "r13 指引侧轮）机械变换先例；任务枚举 4 处编辑全部逐字执"
                "行，非任务枚举的轮次标识同步项在 edit_list 中如实登记（"
                "edit 6/7/8）——变更声明文本「仅（1）更新标题与轮次标识」"
                "因此与产物自洽；§1 与头部 bullet 区不在逐字冻结清单（冻"
                "结区=§2–§7）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R13_SHA_PREFIX,
                "r14_prep_record_mirror_source": {
                    "path_rel": "out/v3-tl2/calibration/r14-prep-record.json",
                    "sha256": r14_record_sha,
                },
                "render_framing_r14b_transcription_source": {
                    "path_rel": "out/v3-tl2/calibration/render-framing-r14b.json",
                    "sha256": framing_sha,
                },
                "render_witness_r14b": {
                    "path_rel": "out/v3-tl2/calibration/render-witness-r14b.json",
                    "sha256": witness_sha,
                },
                "evaluation_protocol_v1_preserved": {
                    "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                    "sha256": protocol_sha,
                },
            },
            "verification": {
                "section_assertions_passed": section_asserts,
            },
        },
        "changed_variables": [
            {
                "id": "guidance-color-legend-instrument-note",
                "axis": "guidance",
                "instrument_change": False,
                "target": (
                    "observation-guidance-r15.md（新落盘；由 observation-"
                    "guidance-r13.md 机械变换生成，见 guidance_reuse."
                    "edit_list）"),
                "description": (
                    "指引增补 §5A 渲染配色仪器注记节（bottom 配色语义显式"
                    "化：橙 (255,165,0)=白墨图元重着色（162 fill+4 stroke，"
                    "B.Cu∪B.Mask 双族共享绘制）；绿 (0,128,0)=板内空隙白重"
                    "着色（墨缺失处基材露白，非图元：非丝印、非阻焊开窗图"
                    "形、非 courtyard 图形）——数值事实自 render-framing-"
                    "r14b.json/render-witness-r14b.json 结构探测转录）；配"
                    "套机械变换=标题与轮次标识（标题行/round_id_constant/"
                    "本轮性质行/示例 reader_id）、本变更声明重写、示例旗 ID"
                    " 前缀 R13T-（4 处）/R13B-（1 处）→R15T-/R15B-；§2–§7 "
                    "判据文本零变更"),
                "attribution_channel": (
                    "bottom 混淆性弃权回落主通道（三分判据 hypothesis_test."
                    "adjudication：(i) bottom courtyard 非弃权 0/0/0 收敛"
                    "维持；(ii) bottom 全旗聚合弃权率 ≤10/11；(iii) top 全"
                    "旗聚合弃权率 ≤ run-r14 同口径）；守门=top 渲染零变更"
                    "下的方向性稳定记录"),
                "preregistration_ref": dev_ref,
            }
        ],
        "manipulated_factor": (
            "唯一操纵因素=指引增补 §5A 渲染配色仪器注记节（颜色→来源映射"
            "显式化：橙=白墨图元重着色、绿=板内空隙白重着色非图元；r14 编"
            "排侧 color_semantics_note 在案事实转录指引侧，per "
            "round14-dev-record next_iteration_targets[0]）；渲染（四图字"
            "节复用）/GT/阈值/协议零变更"),
        "unchanged_components": [
            {
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "witness": ("render-witness-r14b.json（b63771f9，fail-closed"
                            " 复核）"),
                "pngs": png_checks,
                "byte_reuse": True,
                "note": ("开工时 sha256_file 实测四 PNG 并与 "
                         "render-witness-r14b.json 登记值逐字比对（bottom="
                         "renders.applied/prep1.sha256；top=top_zero_change_"
                         "copies.sha256）——四图即 r14 轮盲读所用同一批文"
                         "件；本轮零重渲染、零仪器变更"),
            },
            "判读指引 §2 类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序"
            "与圆括号中性释义零改动；r13 指引 §2 原文，分段+substring 断"
            "言复核）",
            "§3 邻域框收窄判据与坐标口径（r13 指引 §3 原文逐字）",
            "§3A 类别判据示例：全部逐字承 r13 指引（六类全部示例含示例 c"
            "「整段规则周期」判据；§3A 末尾对照说明原位保留）",
            "§4 全文：总原则、两条显式判据、量化版存在性判断一般判据 "
            "(i)(ii)(iii)、接触性判据、三路出口、confidence 定义、对照说"
            "明（r6/r8/r9/r12/r13 增补块）——逐字承 r13 指引（分段+"
            "substring 断言复核）；反放宽条款「仅因形态不熟悉、不确定其设"
            "计含义，不构成判为正常设计特征的理由」逐字保留",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r13 指引 §6 原文；仅旗 ID 展示前缀 R13T-/R13B-→"
            "R15T-/R15B- 机械替换，随指引落盘固化、无需派发层覆盖）",
            "GT 集：零改动（gt-audit-r1 三候选全部关闭在案；GT 侧不再有"
            "候选，r9–r14 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "机械替换仅：标题与轮次标识（标题行/round_id_constant/本轮性"
            "质行/示例 reader_id，沿 s48 先例）、示例旗 ID 前缀 R13T-→"
            "R15T-（4 处）/R13B-→R15B-（1 处）——§2–§7 判据文本零变更",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 显式配色版字节复用（与 R14 "
            "完全相同：白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)、"
            "其余层 kicad 原配色不变；四 PNG sha256 与 render-witness-"
            "r14b.json 登记值 fail-closed 比对一致）；top 渲染无配色变更"
            "（与 R14/R5 逐字节相同）；bottom 视判读口径沿用 r4 指引原文"
            "不改（top/bottom 判读口径在图像空间完全一致、不做镜像换算）；"
            "本轮变化仅在指引侧（§5A 颜色-图层映射仪器注记）——r14 实测的"
            "无图例混淆由指引注记消解，注记不构成任何「应判正常/无需报"
            "告」的指示；bottom 零旗标分母=0 时弃权率按 cal._ratio 先例="
            "None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R15 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r14-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R15T/R15B；"
                "聚合口径与 calibration-run-r14 同一比较脚本血统；代表配"
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
                "本轮恰一个指引侧操纵变量（指引增补 §5A 仪器注记节）、检验"
                "恰一个假设（round14-dev-record next_iteration_targets[0] "
                "指引侧颜色-图层映射配套；hypothesis_id=r14-dev-record-"
                "candidate-0-guidance-color-legend）；归因分层：r14 reject"
                "（预注册拒绝支第二支：无图例配色引发混淆性弃权上升）所指"
                "向的指引侧配套首验（区别于 r14 仪器侧处置）；跨轮对比"
                "（vs r13–r14）为方向性（实例群混杂照旧）；bottom 主通道="
                "top 方向性附录；字母/机制观察/度量教训三分记账（adjudication"
                ".mechanism_observation_separate 与 metric_lesson_separate "
                "单列，不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "guidance-color-legend-instrument-note（指引侧唯一操纵；"
                    "非渲染/GT/阈值/协议变更）"),
                "metric": (
                    "三分判据见 hypothesis_test.adjudication.supported_"
                    "requires_all：(i) bottom courtyard 类非弃权计数按实例 "
                    "bottom-i1/i2/i3 全为 0（收敛维持）；(ii) bottom 全旗聚"
                    "合弃权率 ≤10/11（混淆回落；bottom 零旗标时条件自动满"
                    "足并记入机制观察）；(iii) top 全旗聚合弃权率 ≤ run-r14"
                    " 同口径（不回退；比较脚本同一逻辑对基线与本轮双侧复"
                    "算，不手工赋值）"),
                "support": "(i)(ii)(iii) 全部满足 → supported",
                "reject": (
                    "(i) 不满足（图例引入新混淆或收敛不稳健），或 (ii)(iii)"
                    " 任一不满足（图例不足以消除混淆/其他轴回退）→ 如实记"
                    "录 reject"),
            },
            "guard_channel": {
                "metric": (
                    "top 视角非弃权旗标 frame_box_pct 几何门（面积比出局条"
                    "目；top 渲染字节复用零变更）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r15 指引 §2–§7 逐字承 r13，分段"
                    "断言复核），非弃权框仍须满足；几何门面积比出局条目变"
                    "化如实记录"),
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
            "本轮指引侧变更不触碰任何判据文本：§2–§7 逐字承 r13（分段+"
            "substring 双重断言复核），§5A 为仪器事实注记、非判据——不构"
            "成任何「应判正常/无需报告」的指示，不降低任何存在性、归类、"
            "定位或报告的责任门槛；反放宽条款「仅因形态不熟悉、不确定其"
            "设计含义，不构成判为正常设计特征的理由」与三路出口显式化在 "
            "r15 指引 §4 内逐字保留（fail-closed substring 断言）；仅因形"
            "态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由；"
            "≤10/11 等本轮判据只用于假设检验方向归因，不触碰 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与任"
            "何阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX，只作口径引用）—"
            "—门照常独立计算"),
        "no_instrument_change": True,
        "pre_round_review": {
            "status": "satisfied_by_prior_evidence",
            "basis": (
                "r14 预注册拒绝支第二支机制证据在案（render-framing-r14b "
                "白色双来源+三实例对同一绿色三种语义化），本轮为其指引侧配"
                "套，无需新增视觉评审"),
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
                    "v1 原文零字节保留（r11–r14 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-"
                "r15.md）+单张 PNG+派发命名指令（含 v1.2 工具行为规约硬性"
                "条款：纯 Read 内联判读、禁止任何程序化图像处理），零 GT、"
                "零历史判读件、零 legend（指引 §5A 仪器注记）之外的解释、"
                "零诊断/探针内容；两波次串行保序（同一实例先 applied 后 "
                "prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r15-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R15T/R15B（r15 指引 §6 已机械替换落盘 R15T-/R15B-——本轮"
                "指引本体即为 r15 前缀，无需派发层覆盖）；实例间编号独立，"
                "同实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic，零内容判读、零像素读取）、ground-truth-*、reader-raw-"
            "*、calibration-run-*、derivation-log-*、任何 compare/评估产物"
            "；本脚本只读输入=observation-guidance-r13.md（r15 指引的唯一"
            "变换基座；c28806e1 锚 fail-closed，零写入）、r14-prep-record."
            "json（链锚=93440a3d 先验证；字段结构镜像来源）、round14-dev-"
            "record.json（仅读取 round_id、next_iteration_targets（标记定"
            "位 [0]）字段取授权原文，实测 sha 入记录）、render-framing-"
            "r14b.json（7004b017 锚 fail-closed；§5A 数值事实转录源："
            "vector_attribution 162 fill+4 stroke、board_white_coverage "
            "206632/206052）、render-witness-r14b.json（b63771f9 锚 "
            "fail-closed；四 PNG 见证登记+配色语义+成图实测调色板）、"
            "evaluation-protocol-v1.md（仅在盘+哈希复核，锚=22dc7337）；"
            "renders-r14b 四 PNG 仅哈希+magic（渲染零变更以 witness 登记哈"
            "希比对为准）；observation-guidance-r15.md 与 r15-prep-record."
            "json 为本轮仅有的两个新建文件；reader 派发（后续编排侧执行）"
            "上下文=observation-guidance-r15.md+单张 PNG+派发指令（R15T/"
            "R15B 前缀、reader-r15-{top,bottom}-i{1,2,3}、v1.2 工具行为规"
            "约硬性条款），零 GT、零历史判读件、零 legend 之外的解释、零其"
            "他盘上文件；视觉判读禁止由编排/收口包兼任；跨实例/跨视角禁止"
            "交流（12 次盲读相互独立、不得交换判读信息——独立性是多实例"
            "协议的前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R13, R14_PREP_RECORD, R14_DEV_RECORD, FRAMING_R14B,
                 WITNESS_R14B, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    # 目标文件（GUIDANCE_R15/RECORD）不做前置硬拒绝：落盘阶段防覆写守卫
    # 按红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→
    # 幂等通过（零覆写）。（首轮创建前置=两目标不存在，已由编排侧确认。）

    import json

    # ---- 冻结锚验证（fail-closed）----
    r14_record = json.loads(R14_PREP_RECORD.read_text(encoding="utf-8"))
    dev_record = json.loads(R14_DEV_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R14B.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    r14_record_sha = _sha(R14_PREP_RECORD)
    dev_record_sha = _sha(R14_DEV_RECORD)
    framing_sha = _sha(FRAMING_R14B)
    witness_sha = _sha(WITNESS_R14B)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    if not r14_record_sha.startswith(R14_PREP_RECORD_SHA_PREFIX):
        _fail(f"r14-prep-record sha 前 8={r14_record_sha[:8]} != 预期 "
              f"{R14_PREP_RECORD_SHA_PREFIX}（结构镜像来源锚不符，立即停止）")
    if not framing_sha.startswith(FRAMING_R14B_SHA_PREFIX):
        _fail(f"render-framing-r14b sha 前 8={framing_sha[:8]} != 预期 "
              f"{FRAMING_R14B_SHA_PREFIX}（仪器预注册锚不符，立即停止）")
    if not witness_sha.startswith(WITNESS_R14B_SHA_PREFIX):
        _fail(f"render-witness-r14b sha 前 8={witness_sha[:8]} != 预期 "
              f"{WITNESS_R14B_SHA_PREFIX}（仪器见证锚不符，立即停止）")
    if not protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX):
        _fail(f"evaluation-protocol-v1.md sha 前 8={protocol_sha[:8]} != 预"
              f"期 {EVAL_PROTOCOL_V1_SHA_PREFIX}（协议原文保留载体疑被改动，"
              f"立即停止）")
    if r14_record.get("schema_version") != "3.0":
        _fail("r14-prep-record schema_version != 3.0（结构漂移）")
    if r14_record.get("kind") != "tl2_calibration_r14_prep_record":
        _fail("r14-prep-record kind 不符（结构漂移）")
    if r14_record.get("round_id_constant") != "2026-09-08-r14":
        _fail("r14-prep-record round_id_constant != 2026-09-08-r14（结构漂移）")

    # ---- r13 指引零字节复核（本轮唯一变换基座；只读）----
    guidance13_sha = _sha(GUIDANCE_R13)
    if not guidance13_sha.startswith(GUIDANCE_R13_SHA_PREFIX):
        _fail(f"r13 指引 sha 前 8={guidance13_sha[:8]} != 预期 "
              f"{GUIDANCE_R13_SHA_PREFIX}（变换基座疑被改动，立即停止）")
    base_text = GUIDANCE_R13.read_text(encoding="utf-8")
    if hashing.sha256_text(base_text) != guidance13_sha:
        _fail("r13 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")

    # ---- 结构探测（§5A 数值事实转录源）----
    probe_f = probe_framing(framing)
    witness_probe = probe_witness(witness)
    if (probe_f["white_fill"], probe_f["white_stroke"],
            probe_f["void_final"], probe_f["void_strict"]) != (
            EXPECTED_WHITE_FILL_COUNT, EXPECTED_WHITE_STROKE_COUNT,
            EXPECTED_VOID_FINAL, EXPECTED_VOID_STRICT):
        _fail("§5A 转录值与冻结常量不符（立即停止）")
    if (witness_probe["orange_px"], witness_probe["green_px"]) != (
            EXPECTED_ORANGE_PX, EXPECTED_GREEN_PX):
        _fail("witness 成图实测值与冻结常量不符（立即停止）")

    # ---- 渲染零变更实测（四 PNG vs witness 登记值）----
    png_checks = check_renders_byte_reuse(witness_probe["registered"])

    # ---- 授权候选提取（round14-dev-record next_iteration_targets[0]）----
    dev_ref = extract_candidate(dev_record, dev_record_sha)

    # ---- 指引生成（7 组锚定编辑 + §5A 插入 + 不变量断言）----
    t_work, edit_list = build_guidance(base_text)
    section_5a = build_section_5a(
        white_fill=probe_f["white_fill"], white_stroke=probe_f["white_stroke"],
        void_final=probe_f["void_final"], void_strict=probe_f["void_strict"],
        orange_px=witness_probe["orange_px"], green_px=witness_probe["green_px"])
    t15 = insert_section_5a(t_work, section_5a)
    edit_list.append({
        "edit": 3,
        "kind": "「## 6. 输出格式」标题前插入 §5A 渲染配色仪器注记节（任务"
                "枚举编辑 3）",
        "anchor": SECTION6_ANCHOR,
        "expected_hits": EXPECTED_HITS["section6_anchor"],
        "content_sha256": hashing.sha256_text(section_5a),
        "numeric_facts_transcribed": {
            "white_fill_count": probe_f["white_fill"],
            "white_stroke_count": probe_f["white_stroke"],
            "board_void_white_final_px": probe_f["void_final"],
            "board_void_white_strict_px": probe_f["void_strict"],
            "orange_measured_px": witness_probe["orange_px"],
            "green_measured_px": witness_probe["green_px"],
            "sources": ["render-framing-r14b.json（7004b017）",
                        "render-witness-r14b.json（b63771f9）"],
        },
    })
    edit_list_sorted = sorted(edit_list, key=lambda e: e["edit"])
    section_asserts = assert_guidance_invariants(base_text, t15)

    guidance15_bytes = t15.encode("utf-8")
    guidance15_sha = hashing.sha256_bytes(guidance15_bytes)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(
        guidance13_sha=guidance13_sha, guidance15_sha=guidance15_sha,
        guidance13_bytes=len(base_text.encode("utf-8")),
        guidance15_bytes=len(guidance15_bytes),
        r14_record_sha=r14_record_sha, dev_ref=dev_ref,
        framing_sha=framing_sha, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks,
        edit_list=edit_list_sorted, section_asserts=section_asserts)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r14-prep-record 逐键镜像
    missing = sorted(set(r14_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r14_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r14-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # 结构自证
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更轮）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（渲染零变更轮）")
    if record["hypothesis_test"] != HYPOTHESIS_TEST:
        _fail("hypothesis_test 与预注册判据常量不一致（逐字要求被破坏）")
    if len(record["changed_variables"]) != 1:
        _fail("r15 恰一项变更变量：changed_variables 必须恰 1 项")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"][
            "zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved "
              "必须为真")
    if len({p["sha256_measured"] for p in png_checks}) != 3:
        _fail("四 PNG sha 集合应为 3 个不同值（两 bottom 同哈希）")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance13_sha=guidance13_sha, guidance15_sha=guidance15_sha,
        guidance13_bytes=len(base_text.encode("utf-8")),
        guidance15_bytes=len(guidance15_bytes),
        r14_record_sha=r14_record_sha, dev_ref=dev_ref,
        framing_sha=framing_sha, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks,
        edit_list=edit_list_sorted, section_asserts=section_asserts)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r15-prep-record")

    # ---- 防覆写守卫 + 落盘 ----
    if GUIDANCE_R15.exists():
        if GUIDANCE_R15.read_bytes() != guidance15_bytes:
            _fail("observation-guidance-r15.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r15-prep] 重跑自证：observation-guidance-r15.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R15.write_bytes(guidance15_bytes)
        if GUIDANCE_R15.read_bytes() != guidance15_bytes:
            _fail("回读不一致: observation-guidance-r15.md")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r15-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r15-prep] 重跑自证：r15-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r15-prep-record.json")

    # ---- 汇总打印 ----
    print("[r15-prep] 验证通过：r13 指引基座锚 "
          f"{GUIDANCE_R13_SHA_PREFIX} OK（只读，零写入）；r14-prep-record "
          f"镜像锚 {R14_PREP_RECORD_SHA_PREFIX} OK；round14-dev-record 实测 "
          f"{dev_record_sha[:8]}（候选=next_iteration_targets["
          f"{dev_ref['item_indices_zero_based'][0]}] 原文摘录在案）；"
          f"framing-r14b 锚 {FRAMING_R14B_SHA_PREFIX} OK（§5A 转录源：白墨 "
          f"{probe_f['white_fill']} fill+{probe_f['white_stroke']} stroke、"
          f"空隙白 final {probe_f['void_final']}/strict "
          f"{probe_f['void_strict']}）；witness-r14b 锚 "
          f"{WITNESS_R14B_SHA_PREFIX} OK（橙 {witness_probe['orange_px']} px"
          f"/绿 {witness_probe['green_px']} px 两板相同、assertions_pass 双"
          f"真）；evaluation-protocol-v1 在盘锚 "
          f"{EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r15-prep] 渲染零变更自证（四 PNG 实测=witness 登记值）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print(f"[r15-prep] 指引不变量断言：{len(section_asserts)} 项全部通过"
          f"（§2–§7 分段逐字 {len(SECTION_PAIRS)} 段 + 关键 substring "
          f"{len(REQUIRED_SUBSTRING_VALUES)} 条 + R13 残留零 + 新文本在位 + "
          f"§5A 位置）")
    print(f"[r15-prep] 字节数差：r15（{len(guidance15_bytes)} B）- r13（"
          f"{len(base_text.encode('utf-8'))} B）= "
          f"{len(guidance15_bytes) - len(base_text.encode('utf-8'))} B")
    print(f"[r15-prep] 工件 sha256：observation-guidance-r15.md="
          f"{_sha(GUIDANCE_R15)}")
    print(f"[r15-prep] 工件 sha256：r15-prep-record.json={_sha(RECORD)}")
    print("[r15-prep] §5A 节实际落盘全文：")
    print(section_5a, end="")


if __name__ == "__main__":
    main()
