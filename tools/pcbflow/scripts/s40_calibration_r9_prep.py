#!/usr/bin/env python
"""CAL-R9-PREP：R9 suspicious_reroute 等长/蛇形形态判据轮预备见证包（写
out/v3-tl2/calibration/observation-guidance-r9.md 与 r9-prep-record.json）。

R9 轮性质（预注册，非事后）：**单变量指引侧变更轮 + 协议侧度量教训前瞻
预注册**——复用 R5 冻结渲染（零仪器变更、零重渲染），唯一指引侧变更=
判读指引 §3A 类别 4 `suspicious_reroute` 增补示例 c（等长/蛇形规则周期
形态可按 §4 存在性判断一般判据推理；示例 a、b 原文保留），执行
round8-dev-record.json next_iteration_targets 的指引侧候选（蛇形/等长
判据）与协议侧度量设计教训的前瞻落地（只预注册适用本轮，不追溯改判
r8）。指引落盘后由编排侧重新盲读。本脚本只做 PREP，不做盲读、不做任
何视觉判读。

检验假设：R8T-014 以「可能等长匹配设计」弃权的该类形态，§3A 等长/蛇形
形态判据（与 §4 存在性判断一般判据衔接）后可被 reader 按三路出口负责任
地裁处（判为正常设计特征→不报告，或形态不规则→正常报告非弃权），该类
疑似形态不再停留于弃权。裁决判据（度量设计教训前瞻落地）=现象类旗标产
量计数（弃权+非弃权合计，按类别分列）——非旗标内弃权率：R9 reroute 类
旗标产量=0（基线 r8=1）且其余类别守 §3 收窄判据→假设获支持；产量≥1→
不获支持。结果无论方向均如实入账。基线数字仅入本编排侧 prep-record，
不进指引文件（指引零轮次结果数字）。

功能（out/ 仅新建两个文件：observation-guidance-r9.md、
r9-prep-record.json；既有产物零改动）：

  1. fail-closed 复核 renders-r5 四件 PNG：sha256 与 r8-prep-record.json
     renders_reuse.png_witness 登记的见证常量一致（先探测该结构取常量并
     要求登记自洽：sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）。
  2. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全 match
     才继续）；并复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段
     （r5 前缀键不存在、r4_frozen_png_sha256_reference 在场，不符即停）。
  3. 冻结锚：observation-guidance-r8.md sha256 前 8=aad43270、
     round8-dev-record.json sha256 前 8=437e149c（均不符即停）；从
     round8-dev-record next_iteration_targets 按 0 起始索引 [2]/[3] 取
     两项原文逐字摘录（蛇形/等长判据=指引侧候选、度量设计教训=协议侧
     候选；按内容标记唯一定位、索引实测回填）。
  4. 由 observation-guidance-r8.md 机械变换生成 observation-guidance-
     r9.md（§3A 类别 4 增补示例 c；§3A 末尾增补 r9 对照说明一行；头部
     标题/round_id_constant/本轮性质行/变更声明节按 r9 重写；机械替换
     仅四处：R8T/R8B→R9T/R9B、round_id_constant、reader-r8、标题轮次
     标识；其余文本逐字承 r8，含 §4 两条对照说明原位保留）。变换前后
     逐项计数断言（锚点出现次数不符即停）。
  5. 落盘 r9-prep-record.json（canonical JSON=hashing.canonical_json_
     bytes：ensure_ascii=False / sort_keys / indent=1 / LF，顶层键集合
     与 r8-prep-record 逐键镜像断言）；同参重建两次逐字节一致自证；防
     覆写守卫——目标文件已存在且重建字节非逐字节等同→FAIL，等同→允
     许幂等重跑（零覆写）；落盘后重读盘面字节回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r9）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；
无 subprocess / 无网络 / 无主机绝对路径；不读 GT / reader-raw-* /
calibration-run-* / derivation-log-* / compare 产物（round8-dev-record
仅读 next_iteration_targets 字段取预注册原文；r8-prep-record 仅用于取
PNG 见证常量）；无 git。指引文件内零 GT、零轮次结果数字。

用法：python scripts/s40_calibration_r9_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R8_PREP_RECORD = CAL_DIR / "r8-prep-record.json"
R8_DEV_RECORD = CAL_DIR / "round8-dev-record.json"
GUIDANCE_R8 = CAL_DIR / "observation-guidance-r8.md"
GUIDANCE_R9 = CAL_DIR / "observation-guidance-r9.md"
RECORD = CAL_DIR / "r9-prep-record.json"

DATE_CONSTANT = "2026-09-07"
ROUND_ID = "2026-09-07-r9"

#: 冻结基线锚（包指令给定；不符即停）
GUIDANCE_R8_SHA_PREFIX = "aad43270"
R8_DEV_RECORD_SHA_PREFIX = "437e149c"

#: round8-dev-record next_iteration_targets 两项的内容定位标记
#: （0 起始索引 [2]=蛇形/等长判据=指引侧候选；[3]=度量设计教训=协议侧
#: 候选；按标记唯一定位、实际索引实测回填进记录）
MARK_GUIDANCE_ITEM = "蛇形走线/等长匹配判据"
MARK_METRIC_ITEM = "度量设计教训"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；见证常量从 r8-prep-record
#: renders_reuse.png_witness 登记探测取得，不在此硬编码）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    print(f"[r9-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# 指引生成（纯函数：r8 全文逐字 + 唯一指引侧变更 + 机械替换）
# ---------------------------------------------------------------------------

OLD_TITLE = "# R8 轮 reader 判读指引（observation-guidance-r8）"
NEW_TITLE = "# R9 轮 reader 判读指引（observation-guidance-r9）"

OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（存在性判据补强轮）**。渲染零变更"
    "（复用 R5 冻结渲染件：零仪器变更、零重渲染）；本轮唯一变更=判读指引 "
    "§4 存在性判断一般判据增补（预注册见下），指引落盘后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（suspicious_reroute 等长/蛇形形态判"
    "据轮）**。渲染零变更（复用 R5 冻结渲染件：零仪器变更、零重渲染）；本"
    "轮唯一变更=判读指引 §3A 类别 4 增补示例 c（预注册见下），指引落盘后"
    "由编排侧重新盲读。")

#: §3A 类别 4 示例 b 原行（插入锚之一）
EXAMPLE_B_REROUTE_LINE = (
    "   - 示例 b：连线在可见上无必要的位置突然大幅改变走向，形成可疑改道形"
    "态。（示例=判据说明，非期望清单，不代表图中存在此类现象。）")

#: 增补的示例 c（包指令给定文本，一字不改；3 空格缩进与同级示例一致）
EXAMPLE_C_LINE = (
    "   - 示例 c：整段连线呈规则、周期性的来回折叠形态（蛇形/等长匹配类布"
    "线的常见样式）时，该规则周期形态本身可按第 4 节存在性判断一般判据推理"
    "——同类通用布线样式的常规设计解释是候选解释之一；形态不规则、无规律的"
    "绕行仍按关注现象处理。（示例=判据说明，非期望清单，不代表图中存在此类"
    "现象。）")

#: §3A 末尾（第 6 类示例之后、"## 4" 之前）追加的对照说明（包指令给定文
#: 本，一字不改）
CONTRAST_NOTE = (
    "（对照说明（r9 增补）：r8 §3A 的六个类别示例**原文保留**；本轮仅在类"
    "别 4 `suspicious_reroute` 增补示例 c——为「等长匹配类规则形态 vs 可疑"
    "绕行」的存在性判断提供与 §4 一般判据的显式衔接，类别封闭集、使用规则、"
    "报告义务与 §4 全部文本（含反放宽条款）一字未动。）")

SEC_START = "## 本轮变更声明（预注册，非事后）"
SEC_END_ANCHOR = "\n## 1. 角色与任务"

BULLET_CHANGE = (
    "- **变更（恰一项，指引侧）：** **§3A 类别 4 `suspicious_reroute` 增补"
    "示例 c**：在 r8 §3A 类别 4 示例 a、b **原文保留**的前提下，其后增补示"
    "例 c——「整段连线呈规则、周期性的来回折叠形态（蛇形/等长匹配类布线的"
    "常见样式）时，该规则周期形态本身可按第 4 节存在性判断一般判据推理——"
    "同类通用布线样式的常规设计解释是候选解释之一；形态不规则、无规律的绕"
    "行仍按关注现象处理。（示例=判据说明，非期望清单，不代表图中存在此类现"
    "象。）」并在 §3A 末尾（第 6 类示例之后、第 4 节之前）增补一条 r9 对照"
    "说明（说明本轮增补范围与界限）。措辞中性一般化，零具体板、位号、坐标、"
    "数量期望，零轮次结果数字。")

BULLET_NO_LOOSENING = (
    "- **非放宽声明：** 本变更=经由既有判据的**候选解释说明**，**非判据放"
    "宽**——§4 三路出口显式化与反放宽条款**原文保留**（「仅因形态不熟悉、"
    "不确定其设计含义，不构成判为正常设计特征的理由」等判断标准词原样保留"
    "于弃权适用侧），总原则「宁可 abstain 不硬标」不动；示例 c 仅是为「等"
    "长匹配类规则形态 vs 可疑绕行」的存在性判断提供与 §4 一般判据的显式衔"
    "接（同类通用布线样式的常规设计解释是**候选解释之一**，非断言、非豁"
    "免），判「正常设计特征」与判「关注现象」承担**同等**判断责任（形态不"
    "规则、无规律的绕行仍按关注现象处理）；§3 邻域框收窄判据一字未动，非"
    "弃权旗标框仍受其约束；不降低任何存在性、归类、定位或报告的责任门槛。")

BULLET_UNCHANGED = (
    "- **不变：** 渲染（复用 R5 冻结渲染件）、角色与盲读纪律（§1）、类别枚"
    "举（6 类逐字，§2）、§3 邻域框收窄判据与坐标口径、§3A 其余示例（类别 "
    "4 示例 a、b 与其余五类全部示例逐字保留）、§4 全文（总原则、两条显式判"
    "据、存在性判断一般判据、三路出口显式化、confidence 定义与弃权 flag 输"
    "出细节、既有对照说明含 r8 增补块原文原位）、courtyard 中性说明（§5）、"
    "输出 schema（单 JSON、per_image、flag 恰六键、无 side 字段，§6）、格"
    "式对齐提示（§7）、bottom 视口径（沿用 r4 指引：top/bottom 判读口径在"
    "图像空间完全一致、不做镜像换算；未为 bottom 单独定图层清单——该属渲"
    "染侧变更，不在本轮）。机械替换仅：视角前缀 R8T/R8B→R9T/R9B、"
    "round_id_constant→`2026-09-07-r9`（及示例中 reader-r8→reader-r9）。")

NEW_SECTION_BODY = (
    SEC_START + "\n\n" + BULLET_CHANGE + "\n\n" + BULLET_NO_LOOSENING +
    "\n\n" + BULLET_UNCHANGED + "\n\n")


def _replace_counted(text: str, old: str, new: str, expected: int,
                     label: str) -> str:
    """计数受控替换：old 出现次数 != expected 即停。"""
    n = text.count(old)
    if n != expected:
        _fail(f"锚点计数不符：{label} 期望 {expected} 次，实测 {n} 次")
    return text.replace(old, new)


def build_guidance(r8_text: str) -> str:
    """由 r8 指引全文生成 r9 指引（纯函数；同入参必得同输出）。

    顺序纪律：先做插入与机械替换（其锚点均不含机械替换模式），再整体
    重写标题/本轮性质行/变更声明节（新文本内含 r8→r9 箭头记法，故机械
    替换必须先行，避免自命中）。
    """
    text = r8_text

    # ---- 前置计数断言（r8 输入侧锚点）----
    for pat, n in (
            ("2026-09-07-r8", 2),   # round_id 行 + 变更声明节内记法
            ("R8T-", 4),            # §6 表行 ×2 + 格式示例 flag_id ×2
            ("R8B-", 1),            # §6 表行
            ("reader-r8", 2),       # 格式示例 reader_id + 变更声明节内记法
            (OLD_TITLE, 1),
            (OLD_NATURE_LINE, 1),
            (EXAMPLE_B_REROUTE_LINE, 1),
            (EXAMPLE_B_REROUTE_LINE + "\n5. `doc_artifact_mismatch`", 1),
            ("\n\n## 4. 置信度与弃权", 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1),
            ("（对照说明（r8 增补）", 1)):
        if text.count(pat) != n:
            _fail(f"r8 指引锚点计数不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")

    # ---- (1) §3A 类别 4 增补示例 c（示例 a、b 原文保留）----
    anchor = EXAMPLE_B_REROUTE_LINE + "\n5. `doc_artifact_mismatch`"
    text = text.replace(
        anchor,
        EXAMPLE_B_REROUTE_LINE + "\n" + EXAMPLE_C_LINE +
        "\n5. `doc_artifact_mismatch`")

    # ---- (2) §3A 末尾追加 r9 对照说明（"## 4" 之前）----
    text = text.replace("\n\n## 4. 置信度与弃权",
                        "\n\n" + CONTRAST_NOTE + "\n\n## 4. 置信度与弃权")

    # ---- (3) 机械替换（四处；变更声明节旧文本此时仍在场、随后整体重写，
    #      其内被替换的记法不影响结果）----
    text = _replace_counted(text, "2026-09-07-r8", "2026-09-07-r9", 2,
                            "round_id_constant")
    text = _replace_counted(text, "R8T-", "R9T-", 4, "flag 前缀 R8T-")
    text = _replace_counted(text, "R8B-", "R9B-", 1, "flag 前缀 R8B-")
    text = _replace_counted(text, "reader-r8", "reader-r9", 2, "reader-id")

    # ---- (4) 标题、本轮性质行 ----
    text = _replace_counted(text, OLD_TITLE, NEW_TITLE, 1, "标题")
    text = _replace_counted(text, OLD_NATURE_LINE, NEW_NATURE_LINE, 1,
                            "本轮性质行")

    # ---- (5) 变更声明节整体重写（r8 同款结构，r9 内容）----
    start = text.index(SEC_START)
    end = text.index(SEC_END_ANCHOR)
    if not start < end:
        _fail("变更声明节锚点顺序异常")
    text = text[:start] + NEW_SECTION_BODY + text[end + 1:]

    # ---- 后置计数断言（r9 输出侧）----
    for pat, n in (
            ("R8T-", 0),
            ("R8B-", 0),
            ("2026-09-07-r8", 0),
            ("2026-09-07-r9", 2),
            ("R9T-", 4),
            ("R9B-", 1),
            ("reader-r9-top", 1),
            ("reader-r8", 1),       # 仅存于新节「reader-r8→reader-r9」记法
            (EXAMPLE_C_LINE, 1),
            (CONTRAST_NOTE, 1),
            ("（对照说明（r8 增补）", 1),
            (NEW_TITLE, 1),
            (NEW_NATURE_LINE, 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1)):
        if text.count(pat) != n:
            _fail(f"r9 指引后置断言不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")
    return text


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s37 模式）
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r8_record: dict) -> dict:
    """探测 r8-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r8_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r8-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
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
    """复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段（与 r8 记录
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
    """从 round8-dev-record next_iteration_targets 取两项预注册原文。

    按内容标记唯一定位（0 起始索引 [2]=蛇形/等长判据=指引侧候选、
    [3]=度量设计教训=协议侧候选），实际索引实测回填；定位不到或歧义
    即停。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or len(targets) < 4:
        _fail("round8-dev-record next_iteration_targets 结构不符")
    g_idx = [i for i, t in enumerate(targets)
             if isinstance(t, str) and MARK_GUIDANCE_ITEM in t]
    m_idx = [i for i, t in enumerate(targets)
             if isinstance(t, str) and MARK_METRIC_ITEM in t]
    if len(g_idx) != 1 or len(m_idx) != 1:
        _fail(f"next_iteration_targets 标记定位歧义：guidance={g_idx}，"
              f"metric={m_idx}")
    g_text, m_text = targets[g_idx[0]], targets[m_idx[0]]
    if "指引侧候选" not in g_text:
        _fail("蛇形/等长判据项缺「指引侧候选」标记")
    if "协议侧候选" not in m_text:
        _fail("度量设计教训项缺「协议侧候选」标记")
    return {
        "indices_zero_based": [g_idx[0], m_idx[0]],
        "guidance_side_target": g_text,
        "metric_lesson_target": m_text,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r8_record_sha: str, dev_record_sha: str,
                 guidance_r8_sha: str, guidance_r9_sha: str,
                 pdf_results: list, png_results: list, quotes: dict) -> dict:
    """构建 r9-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r9_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r9",
        "round_nature": (
            "单变量指引侧变更轮（suspicious_reroute 等长/蛇形形态判据轮）："
            "复用 R5 冻结渲染（零仪器变更、零重渲染），仅改判读指引 §3A 类"
            "别 4 增补示例 c；并落地 round8-dev-record 度量设计教训的协议侧"
            "前瞻预注册（自本轮起适用，不追溯 r8）；observation-guidance-"
            "r9.md 先于本轮盲读落盘、落盘即冻结；盲读由编排侧在本记录之后重"
            "新执行"),
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "png_witness_source": {
                "path_rel": "out/v3-tl2/calibration/r8-prep-record.json",
                "sha256": r8_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量取自 r8-prep-record.json "
                    "renders_reuse.png_witness 登记（来源链：r8-prep-record "
                    "取自 r7-prep-record，源头=2026-09-06 s35/s33 首跑实测；"
                    "本脚本探测该结构取常量并要求登记自洽），非本脚本新测——"
                    "R9 零仪器变更、零重渲染，不产生新见证"),
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
                    "故 renders-r5 PNG 见证常量以 r8-prep-record.json 登记"
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
                "为 R5 渲染实测事实（沿用 r8-prep-record 登记，本脚本实测仍"
                "符），照实登记，不含任何 GT 含义"),
            "no_instrument_change": True,
        },
        "guidance": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r9.md",
            "sha256": guidance_r9_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r8.md",
                "sha256_prefix_expected": GUIDANCE_R8_SHA_PREFIX,
                "sha256_measured": guidance_r8_sha,
                "match": guidance_r8_sha.startswith(GUIDANCE_R8_SHA_PREFIX),
                "role": "指引作者唯一事实源（另加包指令，GT 已剥离）",
            },
            "change_summary": (
                "相对 r8 指引恰三类差异：§3A 类别 4 增补示例 c；§3A 末尾"
                "（第 6 类示例之后、§4 之前）增补一条 r9 对照说明；头部（标"
                "题、round_id_constant、本轮性质行、本轮变更声明节按 r9 同"
                "款结构重写）与 §6 视角前缀/示例 reader-id 的机械替换。其余"
                "文本逐字承 r8（含 §4 两条对照说明原位保留）。"),
        },
        "changed_variables": [
            {
                "id": "reroute-serpentine-criterion-example-c",
                "target": ("observation-guidance-r9.md §3A 类别 4（恰一项；"
                           "单变量轮）"),
                "description": (
                    "§3A 类别 4 `suspicious_reroute` 增补示例 c（示例 a、b "
                    "原文保留）：「整段连线呈规则、周期性的来回折叠形态（蛇"
                    "形/等长匹配类布线的常见样式）时，该规则周期形态本身可按"
                    "第 4 节存在性判断一般判据推理——同类通用布线样式的常规设"
                    "计解释是候选解释之一；形态不规则、无规律的绕行仍按关注"
                    "现象处理。（示例=判据说明，非期望清单，不代表图中存在此"
                    "类现象。）」另在 §3A 末尾（第 6 类示例之后、§4 之前）增"
                    "补 r9 对照说明一行（措辞一字不改地使用包指令给定文本）。"),
                "attribution_channel": (
                    "reroute 类旗标产量主通道（弃权+非弃权合计；基线 r8=1，"
                    "支持=0、拒绝=≥1）；守门=其余类别非弃权旗标仍受 §3 收窄"
                    "判据约束（几何门面积比出局条目无回升）"),
            },
        ],
        "unchanged_components": [
            "渲染：复用 R5 冻结渲染件（零仪器变更、零重渲染）",
            "角色与盲读纪律（r9 指引 §1，逐字承 r8）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r9 指引 §2）",
            "§3 邻域框收窄判据与坐标口径（r9 指引 §3，逐字承 r8）",
            "§3A 类别判据示例：6 类中除类别 4 增补示例 c 外全部逐字承 r8"
            "（类别 4 示例 a、b 原文保留；§3A 末尾另增一条 r9 对照说明）",
            "§4 全文：总原则「宁可 abstain 不硬标」、两条显式判据、存在性判"
            "断一般判据、三路出口显式化、confidence 定义与弃权 flag 输出细"
            "节、既有对照说明（含 r8 增补块）原文原位（r9 指引 §4，逐字承 "
            "r8）",
            "courtyard 中性说明（r9 指引 §5，逐字承 r8）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r9 指引 §6，仅视角前缀机械替换）",
            "格式对齐提示（r9 指引 §7；fail-closed 校验口径，逐字承 r8）",
            "bottom 视口径：沿用 r4 指引不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算；为 bottom 单独定图层清单属渲染侧变"
            "更，不在本轮）",
            "机械替换仅：视角前缀 R8T/R8B→R9T/R9B；round_id_constant "
            "2026-09-07-r8→2026-09-07-r9（及示例中 reader-r8→reader-r9）",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；为 bottom 单独定图层清单属渲染侧变更，"
            "仍为后续轮候选，不在本轮"),
        "hypothesis_test": {
            "hypothesis_id": "r8-dev-record-candidate-ii",
            "hypothesis": (
                "§3A 等长/蛇形形态判据（与 §4 存在性判断一般判据衔接）后，"
                "「疑似等长匹配设计」类形态可被 reader 按三路出口负责任地裁"
                "处（判为正常设计特征→不报告，或形态不规则→正常报告非弃"
                "权），该类疑似形态不再停留于弃权。"),
            "test_design": (
                "单变量指引侧变更：仅 §3A 类别 4 suspicious_reroute 增补示"
                "例 c（等长/蛇形规则周期形态按 §4 存在性判断一般判据推理的候"
                "选解释说明；§3A 末尾另增一条对照说明），渲染与其余指引零变"
                "更，R9 盲读复用 R5 冻结渲染件。"),
            "baseline_reference": {
                "round": "r8",
                "reroute_class_flag_production_total": 1,
                "reroute_class_detail": (
                    "恰 1 条：R8T-014（prep1-top，abstain=true，弃权理由含"
                    "「可能等长匹配设计」）；全视角非弃权 reroute=0"),
                "note": (
                    "R8 实测基线（编排侧记录；数字仅入 prep-record，不进指"
                    "引文件——指引零轮次结果数字）"),
            },
            "support_condition": (
                "R9 盲读全视角 reroute 类旗标产量（弃权+非弃权合计）=0（基"
                "线 r8=1），且其余类别非弃权旗标仍守 §3 收窄判据（几何门面"
                "积比出局条目无回升），则假设获支持。"),
            "reject_condition": (
                "R9 reroute 类旗标产量 ≥1（该类形态仍未被判据化解），则假设"
                "不获支持。"),
            "null_result_note": (
                "结果无论方向均如实入账——正确测出无效同样是有效证据；n=1 基"
                "线，跨轮 reader 实例不同=混杂因素、每格 n=1、如实入账；度"
                "量与归因分组由编排侧在 close 包执行；本记录零 GT（无期望数"
                "量/分布/坐标/类别侧重提示）。"),
            "declaration": (
                "现象类旗标产量计数（弃权+非弃权合计，按类别分列）照常如实"
                "记录；聚合弃权率/matches/recall/seed_match_rate 亦照常如实"
                "记录（联合评价口径与 APR-0011 阈值零改动）；跨轮 reader 实"
                "例不同=混杂因素、每格 n=1；「正确测出无效同样是有效证据」。"),
            "preregistered_criteria_quote": {
                "guidance_side_target": quotes["guidance_side_target"],
                "metric_lesson_target": quotes["metric_lesson_target"],
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round8-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R8_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": quotes["indices_zero_based"],
                "note": (
                    "引用两项原文逐字摘录（措辞按文件原文，未改写）：索引 "
                    "[2]=蛇形走线/等长匹配判据（指引侧候选，本轮执行的指引"
                    "侧变更）；索引 [3]=度量设计教训（协议侧候选，本轮前瞻"
                    "落地、不追溯 r8）。两项先于 R9 盲读落盘预注册（本记录="
                    "预注册件）。"),
            },
            "primary_channel_metric": (
                "现象类旗标产量计数（弃权+非弃权合计，按类别分列）——非旗标"
                "内弃权率。主通道=reroute 类旗标产量（基线 r8=1；R9 支持判"
                "据=0、拒绝判据=≥1）。"),
            "metric_lesson_application": (
                "round8-dev-record next_iteration_targets 度量设计教训（协"
                "议侧候选）自本轮起前瞻落地：R9 预注册裁决判据测量化解通道"
                "本身（reroute 类旗标产量计数），而非旗标内弃权率；仅适用于"
                "本轮及之后，不追溯改判 r8（r8 字母裁决=not_supported 维持"
                "不变）；联合门三指标（gt_recall/seed_match_rate/abstain_"
                "rate，APR-0011）口径零改动、照常如实记录，不因主通道度量替"
                "换而放松。"),
            "courtyard_tracking_note": (
                "R8 top 非弃权 courtyard 6 条中 1 条命中（R8T-004↔GT-REVC-"
                "AP-8-R1Q2）；未命中 5 条（R8T-002/006/007/012/013）与同态 "
                "GT containment<0.5=定位未及 GT 邻域（非阈值问题）。R9 "
                "close 如实追踪 courtyard 类匹配表现；GT/阈值零改动、不得为"
                "提高命中调阈值、无期望。（此段=编排侧记账，不进指引。）"),
        },
        "no_loosening_note": (
            "本变更为 §3A 类别判据示例的增补（候选解释说明），非判据放宽："
            "r8 §3A 示例 a、b 原文保留，示例 c 仅是「等长匹配类规则形态 vs "
            "可疑绕行」经 §4 存在性判断一般判据的候选解释说明；§4 三路出口"
            "与反放宽条款原文保留（「仅因形态不熟悉、不确定其设计含义，不构"
            "成判为正常设计特征的理由」原样），判「正常设计特征」与判「关注"
            "现象」承担同等判断责任（形态不规则、无规律的绕行仍按关注现象处"
            "理，示例 c 不构成任何豁免）；§3 邻域框收窄判据一字未动，非弃权"
            "旗标框仍受其约束；不降低任何存在性、归类、定位或报告的责任门槛"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "derivation-log-*、任何 compare/评估产物；指引作者唯一输入="
            "observation-guidance-r8.md + 包指令（r8-prep-record.json 仅用"
            "于取 renders-r5 PNG 见证哈希常量；round8-dev-record.json 仅读"
            "取 next_iteration_targets 字段取两项预注册原文摘录，hash 锚="
            "437e149c 先验证）。"),
        "attribution_plan": {
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（round8-dev-record "
                "next_iteration_targets[2] 指引侧候选；度量教训=[3] 协议侧"
                "前瞻落地）；轮后按 reroute 类旗标产量变化方向归因"),
            "primary_channel": {
                "change": "reroute-serpentine-criterion-example-c",
                "metric": (
                    "现象类旗标产量计数（弃权+非弃权合计，按类别分列）——"
                    "reroute 类主通道（基线 r8=1）；非旗标内弃权率"),
                "support": (
                    "R9 reroute 类旗标产量=0 且其余类别守门通过 → R9 假设获"
                    "支持"),
                "reject": (
                    "R9 reroute 类旗标产量 ≥1 → R9 假设不获支持（该类形态"
                    "未被判据化解）"),
            },
            "guard_channel": {
                "metric": (
                    "其余类别非弃权旗 frame_box_pct 几何门（面积比出局条"
                    "目）"),
                "requirement": (
                    "§3 收窄判据一字未动，非弃权框仍须满足；几何门面积比出"
                    "局条目无回升，不因本轮变更放松"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标（弃权率/matches/recall/seed_match_rate）照常如实"
                "记录（联合评价口径与 APR-0011 阈值零改动）；跨轮 reader 实"
                "例不同=混杂因素、每格 n=1；归因分组逻辑由编排侧在 close 包"
                "执行；本指引零 GT、零轮次结果数字（基线数字仅入本编排侧记"
                "录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止",
        },
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (FRAMING_R5, R8_PREP_RECORD, R8_DEV_RECORD, GUIDANCE_R8):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r8_record = json.loads(R8_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    dev_record = json.loads(R8_DEV_RECORD.read_text(encoding="utf-8"))
    r8_record_sha = _sha(R8_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)
    dev_record_sha = _sha(R8_DEV_RECORD)
    if not dev_record_sha.startswith(R8_DEV_RECORD_SHA_PREFIX):
        _fail(f"round8-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R8_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if r8_record.get("schema_version") != "3.0":
        _fail("r8-prep-record schema_version != 3.0（结构漂移）")

    png_constants = _load_png_witness_constants(r8_record)
    _check_framing_raster_field(framing)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)
    quotes = _extract_preregistration_quotes(dev_record)

    guidance_r8_sha = _sha(GUIDANCE_R8)
    if not guidance_r8_sha.startswith(GUIDANCE_R8_SHA_PREFIX):
        _fail(f"r8 指引 sha 前 8={guidance_r8_sha[:8]} != 预期 "
              f"{GUIDANCE_R8_SHA_PREFIX}（冻结基线锚不符，立即停止）")

    # ---- 指引构建 + byte-exact 自证 + 防覆写守卫 ----
    r8_text = GUIDANCE_R8.read_text(encoding="utf-8")
    guidance_text = build_guidance(r8_text)
    if build_guidance(r8_text) != guidance_text:
        _fail("同参重建不一致（byte-exact 破坏）: observation-guidance-r9.md")
    guidance_bytes = guidance_text.encode("utf-8")

    if GUIDANCE_R9.exists():
        existing = GUIDANCE_R9.read_bytes()
        if existing != guidance_bytes:
            _fail("observation-guidance-r9.md 已存在且重建字节不一致"
                  "（防覆写；拒绝覆写）")
        print("[r9-prep] 重跑自证：observation-guidance-r9.md 重建字节与既有"
              "文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。")
    else:
        GUIDANCE_R9.write_bytes(guidance_bytes)
        if GUIDANCE_R9.read_bytes() != guidance_bytes:
            _fail("回读不一致: observation-guidance-r9.md")
    guidance_r9_sha = _sha(GUIDANCE_R9)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r8_record_sha=r8_record_sha,
                          dev_record_sha=dev_record_sha,
                          guidance_r8_sha=guidance_r8_sha,
                          guidance_r9_sha=guidance_r9_sha,
                          pdf_results=pdf_results,
                          png_results=png_results,
                          quotes=quotes)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r8_record_sha=r8_record_sha,
                           dev_record_sha=dev_record_sha,
                           guidance_r8_sha=guidance_r8_sha,
                           guidance_r9_sha=guidance_r9_sha,
                           pdf_results=pdf_results,
                           png_results=png_results,
                           quotes=quotes)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r9-prep-record")

    # ---- 顶层键集合与 r8-prep-record 逐键镜像断言 ----
    if set(record.keys()) != set(r8_record.keys()):
        _fail(f"r9-prep-record 顶层键集合与 r8-prep-record 不镜像："
              f"多={sorted(set(record.keys()) - set(r8_record.keys()))}，"
              f"少={sorted(set(r8_record.keys()) - set(record.keys()))}")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r9-prep] 重跑自证：r9-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r9-prep] 工件 sha256："
                  f"observation-guidance-r9.md={guidance_r9_sha}；"
                  f"r9-prep-record.json={hashing.sha256_bytes(existing)}")
            return
        _fail("r9-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r9-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r9-prep] 验证通过：renders-r5 四件 PNG 实测=r8-prep-record 登记"
          f"见证常量（magic OK）；R5 冻结输入 PDF {len(pdf_results)} 件全 "
          f"match；r8 指引基线锚 {GUIDANCE_R8_SHA_PREFIX} OK；dev-record 锚 "
          f"{R8_DEV_RECORD_SHA_PREFIX} OK（预注册两项=索引 "
          f"{quotes['indices_zero_based']} 原文摘录在案）")
    print(f"[r9-prep] 指引变换断言全过（示例 c=§3A 类别 4、对照说明=§3A 末"
          f"尾、机械替换恰四处、r8 增补对照块原位保留）")
    print(f"[r9-prep] 写出：observation-guidance-r9.md sha256={guidance_r9_sha}")
    print(f"[r9-prep] 写出：r9-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致；顶层键镜像 r8）")


if __name__ == "__main__":
    main()
