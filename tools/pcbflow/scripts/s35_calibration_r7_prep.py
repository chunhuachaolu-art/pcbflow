#!/usr/bin/env python
"""CAL-R7-PREP：R7 弃权判据再校准轮预备见证包（写 out/v3-tl2/calibration/
r7-prep-record.json）。

R7 轮性质：**单变量**指引侧变更轮（弃权判据再校准轮）——复用 R5 冻结
渲染（零仪器变更、零重渲染），仅改判读指引 §4 弃权适用性措辞
（observation-guidance-r7.md，先于本轮盲读落盘、落盘即冻结），盲读由
编排侧在本记录之后重新执行。本脚本只做见证记录，不做盲读、不做任何
视觉判读。

检验假设：r6 轮 dev-record 预注册候选假设 (a)——r6 邻域框收窄判据提高
了「负责任定位」责任门槛，使边界性观察从硬标转向弃权。R7 仅改 §4 措辞
（弃权适用性显式分列），若弃权率显著回落且非弃权框仍守 §3 收窄判据则
(a) 获支持；若不降则 (a) 不获支持。结果无论方向均如实入账（正确测出
无效同样是有效证据）。

功能（out/ 仅新建 r7-prep-record.json 一个文件；既有产物零改动）：

  1. fail-closed 复核 renders-r5 四件 PNG：sha256 与 r6-prep-record.json
     renders_reuse.png_witness **登记的见证常量**一致（先探测该结构取
     常量并要求登记自洽：sha256_measured == sha256_script_constant 且
     match_to_script_constant 为真；不符即停）——证明「复用 R5 冻结渲染」
     的光栅输出未变。
  2. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全 match
     才继续）。
  3. 实测基线锚：observation-guidance-r6.md sha256 前 8=1accadbd（不符
     即停）；计算 observation-guidance-r7.md 的 sha256（先有指引后有
     记录）。
  4. 落盘 r7-prep-record.json（canonical JSON=hashing.canonical_json_bytes：
     ensure_ascii=False / sort_keys / indent=1 / LF，与仓内既有校准产物
     同口径）；同参重建两次逐字节一致自证；既有文件不覆写守卫——重跑时
     重建字节与既有文件逐字节比对：一致=字节级可重跑+守卫生效（零覆写），
     不一致=FAIL。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r7）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；本
脚本不读 GT / reader-raw-* / calibration-run-* / round*-dev-record.json /
derivation-log-* / compare 产物（预注册纪律：指引作者零 GT 暴露；指引
作者唯一输入=observation-guidance-r6.md + 包指令）；无网络；无 git。

用法：python scripts/s35_calibration_r7_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R6_PREP_RECORD = CAL_DIR / "r6-prep-record.json"
GUIDANCE_R6 = CAL_DIR / "observation-guidance-r6.md"
GUIDANCE_R7 = CAL_DIR / "observation-guidance-r7.md"
RECORD = CAL_DIR / "r7-prep-record.json"

DATE_CONSTANT = "2026-09-06"
ROUND_ID = "2026-09-06-r7"

#: 冻结基线锚：r6 指引 sha256 前 8（包指令给定；不符即停）
GUIDANCE_R6_SHA_PREFIX = "1accadbd"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；实际见证常量不在此硬编码，
#: 而是从 r6-prep-record.json renders_reuse.png_witness 登记探测取得）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    print(f"[r7-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r6_record: dict) -> dict:
    """探测 r6-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_script_constant / sha256_measured / match_to_script_constant；
    登记自洽要求：sha256_measured == sha256_script_constant 且
    match_to_script_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r6_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r6-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
    by_side = {}
    for item in witness:
        for key in ("state_side", "path_rel", "sha256_script_constant",
                    "sha256_measured", "match_to_script_constant"):
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
        if item["sha256_measured"] != item["sha256_script_constant"]:
            _fail(f"{side} png_witness 登记不自洽（measured != script_constant）")
        if item["match_to_script_constant"] is not True:
            _fail(f"{side} png_witness 登记自洽位不为真")
        constants[side] = item["sha256_script_constant"]
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

def build_record(*, framing_sha: str, r6_record_sha: str,
                 guidance_r6_sha: str, guidance_r7_sha: str,
                 pdf_results: list, png_results: list) -> dict:
    """构建 r7-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r7_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r7",
        "round_nature": (
            "单变量指引侧变更轮（弃权判据再校准轮）：复用 R5 冻结渲染（零"
            "仪器变更、零重渲染），仅改判读指引 §4 弃权适用性措辞；"
            "observation-guidance-r7.md 先于本轮盲读落盘、落盘即冻结；盲读"
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
                "path_rel": "out/v3-tl2/calibration/r6-prep-record.json",
                "sha256": r6_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量取自 r6-prep-record.json "
                    "renders_reuse.png_witness 登记（来源=2026-09-06 s33 首"
                    "跑实测；本脚本探测该结构取常量并要求登记自洽），非本脚"
                    "本新测——R7 零仪器变更、零重渲染，不产生新见证"),
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
                    "故 renders-r5 PNG 见证常量以 r6-prep-record.json 登记"
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
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r7.md",
            "sha256": guidance_r7_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r6.md",
                "sha256_prefix_expected": GUIDANCE_R6_SHA_PREFIX,
                "sha256_measured": guidance_r6_sha,
                "match": guidance_r6_sha.startswith(GUIDANCE_R6_SHA_PREFIX),
                "role": "指引作者唯一事实源（另加包指令，GT 已剥离）",
            },
        },
        "changed_variables": [
            {
                "id": "abstain-applicability-recalibration",
                "target": "observation-guidance-r7.md §4（恰一项；单变量轮）",
                "description": (
                    "弃权适用性再校准：把 r6 §4「宁可 abstain 不硬标：仅模"
                    "糊怀疑、无法负责任地定位或定类时……」一条拆分为两类不"
                    "确定性的显式判据（总原则保留）——（1）弃权适用于：现象"
                    "是否存在或归属哪类无法负责任地判断；（2）弃权不适用于："
                    "现象可见且已可归类、仅精确范围/边界/尺寸难以确定，此时"
                    "正常报告并按 §3 邻域判据给框（措辞中性，零类别/位置/"
                    "数量暗示）"),
                "attribution_channel": (
                    "弃权率主通道（abstain 旗占比）；守门=非弃权旗 "
                    "frame_box_pct 仍受 §3 收窄判据约束（containment / "
                    "area_ratio 不因本轮变更放松）"),
            },
        ],
        "unchanged_components": [
            "渲染：复用 R5 冻结渲染件（零仪器变更、零重渲染）",
            "角色与盲读纪律（r7 指引 §1，逐字）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r7 指引 §2）",
            "§3 邻域框收窄判据与坐标口径（r7 指引 §3，逐字）",
            "§3A 类别判据示例（r7 指引，逐字）",
            "§4 总原则「宁可 abstain 不硬标」、confidence 定义与弃权 flag "
            "输出细节（category=当前最可能类、confidence=低值、"
            "frame_box_pct=疑似区域、弃权原因；判断标准词「仅模糊怀疑」「"
            "无法负责任地」原样保留）",
            "courtyard 中性说明（r7 指引 §5，逐字）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r7 指引 §6，仅视角前缀机械替换）",
            "格式对齐提示（r7 指引 §7；fail-closed 校验口径，逐字）",
            "bottom 视口径：沿用 r4 指引不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算；为 bottom 单独定图层清单属渲染侧变"
            "更，不在本轮）",
            "机械替换仅两处：视角前缀 R6T/R6B→R7T/R7B；round_id_constant "
            "2026-09-06-r6→2026-09-06-r7（及示例中 reader-r6→reader-r7）",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；为 bottom 单独定图层清单属渲染侧变"
            "更，仍为后续轮候选，不在本轮"),
        "hypothesis_test": {
            "hypothesis_id": "r6-dev-record-candidate-a",
            "hypothesis": (
                "r6 邻域框收窄判据提高了「负责任定位」的责任门槛，使部分边"
                "界性观察从硬标转向弃权（弃权率回升的候选解释）"),
            "test_design": (
                "单变量指引侧变更：仅 §4 弃权适用性措辞显式分列（存在/归类"
                "不确定→弃权；可见可归类但范围不确定→正常报告），渲染与其余"
                "指引零变更，R7 盲读复用 R5 冻结渲染件"),
            "support_condition": (
                "若弃权率相对 r6 显著回落、且非弃权旗标框仍守 §3 收窄判据，"
                "则假设 (a) 获支持（边界性观察回归正常报告）"),
            "reject_condition": (
                "若弃权率不降，则假设 (a) 不获支持（弃权主导因素为「存在性"
                "不确定」而非「范围不确定」，本轮措辞再校准对此无效）"),
            "null_result_note": (
                "结果无论方向均如实入账——正确测出无效同样是有效证据；度量"
                "与归因分组由编排侧在 close 包执行；本记录零 GT"),
        },
        "no_loosening_note": (
            "本变更为指引措辞再校准，非判据放宽：现象「是否存在」「归属哪"
            "类」的责任标准维持 r6 原文语义（「仅模糊怀疑」「无法负责任地"
            "」等判断标准词原样保留于弃权适用侧）；§3 邻域框收窄判据一字未"
            "动，非弃权旗标框仍受其约束；「范围不确定不构成弃权理由」是把 "
            "r6 §3 既有口径（「框仍不要求精确贴边」）在 §4 显式化，不降低"
            "定位责任门槛"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "round*-dev-record.json、derivation-log-*、任何 compare/评估产"
            "物；指引作者唯一输入=observation-guidance-r6.md + 包指令（"
            "r6-prep-record.json 仅用于取 renders-r5 PNG 见证哈希常量）"),
        "attribution_plan": {
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（r6 预注册候选 (a)）；轮后"
                "按弃权率变化方向归因"),
            "primary_channel": {
                "change": "abstain-applicability-recalibration",
                "metric": "弃权率（abstain 旗占比，相对 r6）",
                "support": "显著回落且非弃权框守 §3 收窄判据 → (a) 获支持",
                "reject": "不降 → (a) 不获支持（存在性不确定占主导）",
            },
            "guard_channel": {
                "metric": "非弃权旗 frame_box_pct 几何门（containment / "
                          "area_ratio）",
                "requirement": (
                    "§3 收窄判据一字未动，非弃权框仍须满足；几何门不因本轮"
                    "变更放松"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "归因分组逻辑由编排侧在 close 包执行；本指引与本记录零 GT"
                "（无期望数量/分布/坐标/类别侧重提示）"),
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
    for path in (FRAMING_R5, R6_PREP_RECORD, GUIDANCE_R6):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not GUIDANCE_R7.exists():
        _fail("缺失 observation-guidance-r7.md（先落盘 D1 指引，后跑本脚本）")

    # ---- 验证（fail-closed）----
    import json

    r6_record = json.loads(R6_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    r6_record_sha = _sha(R6_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)

    png_constants = _load_png_witness_constants(r6_record)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)

    guidance_r6_sha = _sha(GUIDANCE_R6)
    if not guidance_r6_sha.startswith(GUIDANCE_R6_SHA_PREFIX):
        _fail(f"r6 指引 sha 前 8={guidance_r6_sha[:8]} != 预期 "
              f"{GUIDANCE_R6_SHA_PREFIX}（冻结基线锚不符，立即停止）")
    guidance_r7_sha = _sha(GUIDANCE_R7)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r6_record_sha=r6_record_sha,
                          guidance_r6_sha=guidance_r6_sha,
                          guidance_r7_sha=guidance_r7_sha,
                          pdf_results=pdf_results,
                          png_results=png_results)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r6_record_sha=r6_record_sha,
                           guidance_r6_sha=guidance_r6_sha,
                           guidance_r7_sha=guidance_r7_sha,
                           pdf_results=pdf_results,
                           png_results=png_results)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r7-prep-record")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r7-prep] 重跑自证：r7-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。"
                  f"sha256={hashing.sha256_bytes(existing)[:16]}…")
            return
        _fail("r7-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r7-prep-record.json")
    sha = _sha(RECORD)
    print(f"[r7-prep] 验证通过：renders-r5 四件 PNG 实测=r6-prep-record 登记"
          f"见证常量（magic OK）；R5 冻结输入 PDF {len(pdf_results)} 件全 "
          f"match；r6 指引基线锚 {GUIDANCE_R6_SHA_PREFIX} OK")
    print(f"[r7-prep] guidance r7 sha256={guidance_r7_sha}")
    print(f"[r7-prep] 写出：r7-prep-record.json sha256={sha[:16]}…"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
