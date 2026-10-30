#!/usr/bin/env python
"""CAL-R8-PREP：R8 存在性判据补强轮预备见证包（写 out/v3-tl2/calibration/
r8-prep-record.json）。

R8 轮性质：**单变量**指引侧变更轮（存在性判据补强轮）——复用 R5 冻结
渲染（零仪器变更、零重渲染），仅改判读指引 §4 存在性判断一般判据
（observation-guidance-r8.md，先于本轮盲读落盘、落盘即冻结），盲读由
编排侧在本记录之后重新执行。本脚本只做见证记录，不做盲读、不做任何
视觉判读。

检验假设：r7 轮 dev-record 预注册候选方向 (i)——R7 弃权主导因素为
「存在性不确定」（bottom 层全弃权），其中一部分疑似形态实为 reader 未
识别的正常设计特征；R8 为 §4 增补一般性存在性判据（系统性重复=正常
特征启发 + 判为正常设计特征不报告的三路出口显式化），若 bottom 层弃权
率回落至预注册阈值 <0.5 且 top 层非弃权旗仍守 §3 收窄判据（几何门面
积比出局条目无回升）则 R8 假设获支持；若未回落至 <0.5 则不获支持
（存在性歧义非指引措辞可化解，指向需渲染侧图层信息等更强证据通道）。
结果无论方向均如实入账（正确测出无效同样是有效证据）。

功能（out/ 仅新建 r8-prep-record.json 一个文件；既有产物零改动）：

  1. fail-closed 复核 renders-r5 四件 PNG：sha256 与 r7-prep-record.json
     renders_reuse.png_witness **登记的见证常量**一致（先探测该结构取
     常量并要求登记自洽：sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）——证明「复用 R5 冻结渲染」
     的光栅输出未变。
  2. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全 match
     才继续）。
  3. 实测基线锚：observation-guidance-r7.md sha256 前 8=9e7a7b13（不符
     即停）；计算 observation-guidance-r8.md 的 sha256（先有指引后有
     记录）。
  4. 落盘 r8-prep-record.json（canonical JSON=hashing.canonical_json_bytes：
     ensure_ascii=False / sort_keys / indent=1 / LF，与仓内既有校准产物
     同口径）；同参重建两次逐字节一致自证；既有文件不覆写守卫——重跑时
     重建字节与既有文件逐字节比对：一致=字节级可重跑+守卫生效（零覆写），
     不一致=FAIL。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r8）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；本
脚本不读 GT / reader-raw-* / calibration-run-* / round*-dev-record.json /
derivation-log-* / compare 产物（预注册纪律：指引作者零 GT 暴露；指引
作者唯一输入=observation-guidance-r7.md + 包指令）；无网络；无 git。
基线数字（R7 分层弃权率等）仅入本编排侧 prep-record（reader 不可见），
不进指引文件。

用法：python scripts/s37_calibration_r8_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R7_PREP_RECORD = CAL_DIR / "r7-prep-record.json"
GUIDANCE_R7 = CAL_DIR / "observation-guidance-r7.md"
GUIDANCE_R8 = CAL_DIR / "observation-guidance-r8.md"
RECORD = CAL_DIR / "r8-prep-record.json"

DATE_CONSTANT = "2026-09-07"
ROUND_ID = "2026-09-07-r8"

#: 冻结基线锚：r7 指引 sha256 前 8（包指令给定；不符即停）
GUIDANCE_R7_SHA_PREFIX = "9e7a7b13"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；实际见证常量不在此硬编码，
#: 而是从 r7-prep-record.json renders_reuse.png_witness 登记探测取得）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    print(f"[r8-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r7_record: dict) -> dict:
    """探测 r7-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r7_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r7-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
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


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r7_record_sha: str,
                 guidance_r7_sha: str, guidance_r8_sha: str,
                 pdf_results: list, png_results: list) -> dict:
    """构建 r8-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r8_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r8",
        "round_nature": (
            "单变量指引侧变更轮（存在性判据补强轮）：复用 R5 冻结渲染（零"
            "仪器变更、零重渲染），仅改判读指引 §4 存在性判断一般判据；"
            "observation-guidance-r8.md 先于本轮盲读落盘、落盘即冻结；盲读"
            "由编排侧在本记录之后重新执行"),
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "png_witness_source": {
                "path_rel": "out/v3-tl2/calibration/r7-prep-record.json",
                "sha256": r7_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量取自 r7-prep-record.json "
                    "renders_reuse.png_witness 登记（来源=2026-09-06 s35 首"
                    "跑实测，其源又可溯至 2026-09-06 s33 首跑实测；本脚本探"
                    "测该结构取常量并要求登记自洽），非本脚本新测——R8 零仪"
                    "器变更、零重渲染，不产生新见证"),
            },
            "raster_output_hash_field_probe": {
                "field_found": False,
                "finding": (
                    "render-framing-r5.json 中不存在 renders-r5 输出 PNG "
                    "的哈希登记字段；frozen_inputs.r4_frozen_png_sha256_"
                    "reference 登记的是 R4 轮冻结 PNG 参考值（与 renders-r5 "
                    "实测不符，属预期：R5 仪器 dpi/crop 变更后 PNG 字节本不"
                    "相同）"),
                "resolution": (
                    "故 renders-r5 PNG 见证常量以 r7-prep-record.json 登记"
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
                "为 R5 渲染实测事实，照实登记，不含任何 GT 含义"),
            "no_instrument_change": True,
        },
        "guidance": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r8.md",
            "sha256": guidance_r8_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r7.md",
                "sha256_prefix_expected": GUIDANCE_R7_SHA_PREFIX,
                "sha256_measured": guidance_r7_sha,
                "match": guidance_r7_sha.startswith(GUIDANCE_R7_SHA_PREFIX),
                "role": "指引作者唯一事实源（另加包指令，GT 已剥离）",
            },
        },
        "changed_variables": [
            {
                "id": "existence-criteria-reinforcement",
                "target": "observation-guidance-r8.md §4（恰一项；单变量轮）",
                "description": (
                    "§4 存在性判断一般判据增补：在 r7 §4 两条显式判据原文"
                    "保留的前提下，为「弃权适用于」一条增补一般性存在性判"
                    "据——（1）系统性重复 vs 孤立不一致启发（同类图形间规"
                    "则成体系重复→更可能正常设计特征，通用 PCB 域知识内常"
                    "规图形可能解释如散热辐条/热隔离盘形态、安装孔、基准"
                    "点、极性标记类；孤立或不一致→更可能关注现象）；（2）"
                    "三路出口显式化（判为正常设计特征→不报告；疑似但无法"
                    "负责任确认→弃权路径；存在且可归类→正常报告路径）（措"
                    "辞中性一般化，零具体板/位号/坐标/数量期望）"),
                "attribution_channel": (
                    "bottom 视角层弃权率主通道（相对 R7 基线 12/12=1.0；预"
                    "注册阈值 bottom 层弃权率 <0.5）；守门=top 层非弃权旗 "
                    "frame_box_pct 仍受 §3 收窄判据约束（几何门面积比出局"
                    "条目无回升）"),
            },
        ],
        "unchanged_components": [
            "渲染：复用 R5 冻结渲染件（零仪器变更、零重渲染）",
            "角色与盲读纪律（r8 指引 §1，逐字承 r7）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r8 指引 §2）",
            "§3 邻域框收窄判据与坐标口径（r8 指引 §3，逐字承 r7）",
            "§3A 类别判据示例（r8 指引，逐字承 r7）",
            "§4 总原则「宁可 abstain 不硬标」与 r7 既有两条显式判据原文、"
            "confidence 定义与弃权 flag 输出细节（category=当前最可能类、"
            "confidence=低值、frame_box_pct=疑似区域、弃权原因；判断标准词"
            "「仅模糊怀疑」「无法负责任地」原样保留）",
            "courtyard 中性说明（r8 指引 §5，逐字承 r7）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r8 指引 §6，仅视角前缀机械替换）",
            "格式对齐提示（r8 指引 §7；fail-closed 校验口径，逐字承 r7）",
            "bottom 视口径：沿用 r4 指引不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算；为 bottom 单独定图层清单属渲染侧变"
            "更，不在本轮）",
            "机械替换仅：视角前缀 R7T/R7B→R8T/R8B；round_id_constant "
            "2026-09-06-r7→2026-09-07-r8（及示例中 reader-r7→reader-r8）",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；为 bottom 单独定图层清单属渲染侧变"
            "更，仍为后续轮候选，不在本轮"),
        "hypothesis_test": {
            "hypothesis_id": "r7-dev-record-candidate-i",
            "hypothesis": (
                "存在性歧义可由一般判据（系统性重复=正常特征启发）化解——"
                "R7 弃权主导因素为「存在性不确定」（bottom 层全弃权），其"
                "中一部分疑似形态实为 reader 未识别的正常设计特征，§4 一般"
                "判据可使该部分被负责任地判出（判为正常特征→不报告），从"
                "而使 bottom 层弃权率回落"),
            "test_design": (
                "单变量指引侧变更：仅 §4 增补存在性判断一般判据（系统性重"
                "复 vs 孤立不一致启发 + 判为正常设计特征不报告的三路出口显"
                "式化），渲染与其余指引零变更，R8 盲读复用 R5 冻结渲染件"),
            "baseline_reference": {
                "round": "r7",
                "aggregate_abstain_rate": 0.6,
                "bottom_layer_abstain_rate": 1.0,
                "bottom_layer_detail": "bottom 视角层 12/12 全弃权（=1.0）",
                "top_layer_abstain_rate": 0.231,
                "top_layer_detail": "top 视角层 3/13≈0.231 回落",
                "note": (
                    "R7 实测基线（编排侧记录；数字仅入 prep-record，不进指"
                    "引文件——指引零轮次结果数字）"),
            },
            "support_condition": (
                "R8 盲读 bottom 视角层弃权率相对 R7 基线（12/12=1.0）显著"
                "回落——预注册阈值：bottom 层弃权率 < 0.5——且 top 层非弃"
                "权旗标仍守 §3 收窄判据（几何门面积比出局条目无回升），则 "
                "R8 假设获支持"),
            "reject_condition": (
                "bottom 层弃权率未回落至 < 0.5（存在性歧义非指引措辞可化"
                "解，指向需渲染侧图层信息等更强证据通道），则 R8 假设不获"
                "支持"),
            "declaration": (
                "聚合弃权率/matches/recall/seed_match_rate 照常如实记录（联"
                "合评价口径与 APR-0011 阈值零改动）；分层观察如实附录、不"
                "凌驾；跨轮 reader 实例不同=混杂因素、每格 n=1；「正确测"
                "出无效同样是有效证据」"),
            "null_result_note": (
                "结果无论方向均如实入账；度量与归因分组由编排侧在 close "
                "包执行；本记录零 GT（无期望数量/分布/坐标/类别侧重提示）"),
        },
        "no_loosening_note": (
            "本变更为 §4 存在性判据的补强，非判据放宽：r7 §4 既有两条显式"
            "判据原文保留，「仅模糊怀疑」「无法负责任地」等判断标准词原样"
            "保留于弃权适用侧，总原则「宁可 abstain 不硬标」不动；新启发要"
            "求判「正常设计特征」与判「关注现象」承担同等判断责任（仅因形"
            "态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由，仍"
            "走弃权路径）；§3 邻域框收窄判据一字未动，非弃权旗标框仍受其约"
            "束；不降低任何存在性、归类、定位或报告的责任门槛"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "round*-dev-record.json、derivation-log-*、任何 compare/评估产"
            "物；指引作者唯一输入=observation-guidance-r7.md + 包指令（"
            "r7-prep-record.json 仅用于取 renders-r5 PNG 见证哈希常量）"),
        "attribution_plan": {
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（r7 dev-record 预注册候选 "
                "(i)）；轮后按 bottom 层弃权率变化方向归因"),
            "primary_channel": {
                "change": "existence-criteria-reinforcement",
                "metric": (
                    "bottom 视角层弃权率（相对 R7 基线 12/12=1.0；预注册阈"
                    "值 <0.5）"),
                "support": (
                    "bottom 层弃权率 <0.5 且 top 层守门通过 → R8 假设获支"
                    "持"),
                "reject": (
                    "bottom 层弃权率未回落至 <0.5 → R8 假设不获支持（存在"
                    "性歧义非指引措辞可化解）"),
            },
            "guard_channel": {
                "metric": (
                    "top 层非弃权旗 frame_box_pct 几何门（面积比出局条目）"),
                "requirement": (
                    "§3 收窄判据一字未动，非弃权框仍须满足；几何门面积比出"
                    "局条目无回升，不因本轮变更放松"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标（弃权率/matches/recall/seed_match_rate）照常如实"
                "记录（联合评价口径与 APR-0011 阈值零改动）；分层观察如实"
                "附录、不凌驾；跨轮 reader 实例不同=混杂因素、每格 n=1；归"
                "因分组逻辑由编排侧在 close 包执行；本指引零 GT、零轮次结"
                "果数字（基线数字仅入本编排侧记录）"),
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
    for path in (FRAMING_R5, R7_PREP_RECORD, GUIDANCE_R7):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not GUIDANCE_R8.exists():
        _fail("缺失 observation-guidance-r8.md（先落盘 D1 指引，后跑本脚本）")

    # ---- 验证（fail-closed）----
    import json

    r7_record = json.loads(R7_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    r7_record_sha = _sha(R7_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)

    png_constants = _load_png_witness_constants(r7_record)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)

    guidance_r7_sha = _sha(GUIDANCE_R7)
    if not guidance_r7_sha.startswith(GUIDANCE_R7_SHA_PREFIX):
        _fail(f"r7 指引 sha 前 8={guidance_r7_sha[:8]} != 预期 "
              f"{GUIDANCE_R7_SHA_PREFIX}（冻结基线锚不符，立即停止）")
    guidance_r8_sha = _sha(GUIDANCE_R8)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r7_record_sha=r7_record_sha,
                          guidance_r7_sha=guidance_r7_sha,
                          guidance_r8_sha=guidance_r8_sha,
                          pdf_results=pdf_results,
                          png_results=png_results)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r7_record_sha=r7_record_sha,
                           guidance_r7_sha=guidance_r7_sha,
                           guidance_r8_sha=guidance_r8_sha,
                           pdf_results=pdf_results,
                           png_results=png_results)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r8-prep-record")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r8-prep] 重跑自证：r8-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。"
                  f"sha256={hashing.sha256_bytes(existing)[:16]}…")
            return
        _fail("r8-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r8-prep-record.json")
    sha = _sha(RECORD)
    print(f"[r8-prep] 验证通过：renders-r5 四件 PNG 实测=r7-prep-record 登记"
          f"见证常量（magic OK）；R5 冻结输入 PDF {len(pdf_results)} 件全 "
          f"match；r7 指引基线锚 {GUIDANCE_R7_SHA_PREFIX} OK")
    print(f"[r8-prep] guidance r8 sha256={guidance_r8_sha}")
    print(f"[r8-prep] 写出：r8-prep-record.json sha256={sha[:16]}…"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
