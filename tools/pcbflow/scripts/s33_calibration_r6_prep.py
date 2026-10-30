#!/usr/bin/env python
"""CAL-R6-PREP：R6 指引侧变更轮预备见证包（写 out/v3-tl2/calibration/
r6-prep-record.json）。

R6 轮性质：指引侧变更轮——复用 R5 冻结渲染（零仪器变更、零重渲染），
仅改判读指引文本（observation-guidance-r6.md，先于本轮盲读落盘、落盘
即冻结），盲读由编排侧在本记录之后重新执行。本脚本只做见证记录，不做
盲读、不做任何视觉判读。

功能（out/ 仅新建 r6-prep-record.json 一个文件；既有产物零改动）：

  1. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全 match
     才继续）——证明「复用 R5 冻结渲染」的输入侧未变。
  2. 光栅输出哈希字段探测结论（落盘如实声明）：render-framing-r5.json
     **无** renders-r5 输出 PNG 的哈希登记字段（frozen_inputs.
     r4_frozen_png_sha256_reference 登记的是 R4 轮冻结 PNG 参考值；R5
     仪器 dpi/crop 变更后与 renders-r5 实测本不相同，属预期）。按包指令
     fallback：脚本内常量记录 renders-r5 四件 PNG 盘上实测 sha256（来源
     =2026-09-06 本脚本首跑实测），重跑时 fail-closed 比对（防改动见证）。
  3. 计算 observation-guidance-r6.md 的 sha256（先有指引后有记录）；
     同时实测基线 observation-guidance-r4.md sha256 并校验其前 8=
     c0706d0f（冻结基线锚，不符即停）。
  4. 落盘 r6-prep-record.json（canonical JSON=hashing.canonical_json_bytes：
     ensure_ascii=False / sort_keys / indent=1 / LF，与仓内既有校准产物
     同口径）；同参重建两次逐字节一致自证；既有文件不覆写守卫——重跑时
     重建字节与既有文件逐字节比对：一致=字节级可重跑+守卫生效（零覆写），
     不一致=FAIL。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r6）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；本
脚本不读 GT / reader-raw-* / calibration-run-* / round*-dev-record.json /
derivation-log-* / compare 产物（预注册纪律：指引作者零 GT 暴露）；无
网络；无 git。

用法：python scripts/s33_calibration_r6_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
GUIDANCE_R4 = CAL_DIR / "observation-guidance-r4.md"
GUIDANCE_R6 = CAL_DIR / "observation-guidance-r6.md"
RECORD = CAL_DIR / "r6-prep-record.json"

DATE_CONSTANT = "2026-09-06"
ROUND_ID = "2026-09-06-r6"

#: 冻结基线锚：r4 指引 sha256 前 8（包指令给定；不符即停）
GUIDANCE_R4_SHA_PREFIX = "c0706d0f"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的见证哈希常量（fallback 分支：render-framing-r5.json
#: 无 renders-r5 输出 PNG 哈希登记字段；来源=2026-09-06 本脚本首跑实测，
#: 重跑 fail-closed 比对，防 renders-r5 被改动）
RENDERS_R5_PNG_SHA256 = {
    "applied-top":
        "298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5ca85e0f4f12a3cd0",
    "applied-bottom":
        "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9",
    "prep1-top":
        "b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca54c58f688d44f8",
    "prep1-bottom":
        "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9",
}

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    print(f"[r6-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证
# ---------------------------------------------------------------------------

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


def _check_renders_r5_pngs() -> list:
    """renders-r5 四件 PNG：magic 检查 + 实测 sha256 vs 脚本见证常量。"""
    results = []
    for state_side, expected in RENDERS_R5_PNG_SHA256.items():
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
            "sha256_script_constant": expected,
            "match_to_script_constant": measured == expected,
        })
    bad = [r for r in results if not r["match_to_script_constant"]]
    if bad:
        _fail(f"renders-r5 PNG 实测与脚本见证常量不符（R5 冻结渲染疑被改动）：{bad}")
    return results


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, guidance_r4_sha: str,
                 guidance_r6_sha: str, pdf_results: list,
                 png_results: list) -> dict:
    """构建 r6-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r6_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r6",
        "round_nature": (
            "指引侧变更轮：复用 R5 冻结渲染（零仪器变更、零重渲染），仅改"
            "判读指引文本；observation-guidance-r6.md 先于本轮盲读落盘、"
            "落盘即冻结；盲读由编排侧在本记录之后重新执行"),
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "raster_output_hash_field_probe": {
                "field_found": False,
                "finding": (
                    "render-framing-r5.json 中不存在 renders-r5 输出 PNG "
                    "的哈希登记字段；frozen_inputs.r4_frozen_png_sha256_"
                    "reference 登记的是 R4 轮冻结 PNG 参考值（与 renders-r5 "
                    "实测不符，属预期：R5 仪器 dpi/crop 变更后 PNG 字节本不"
                    "相同）"),
                "fallback": (
                    "按包指令 fallback：以脚本内常量记录 renders-r5 四件 "
                    "PNG 盘上实测 sha256（来源=2026-09-06 s33 首跑实测），"
                    "重跑 fail-closed 比对（防改动见证）"),
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
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r6.md",
            "sha256": guidance_r6_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r4.md",
                "sha256_prefix_expected": GUIDANCE_R4_SHA_PREFIX,
                "sha256_measured": guidance_r4_sha,
                "match": guidance_r4_sha.startswith(GUIDANCE_R4_SHA_PREFIX),
                "role": "指引作者唯一事实源（另加包指令抽象条目，GT 已剥离）",
            },
        },
        "changed_variables": [
            {
                "id": "neighborhood-frame-tightening",
                "target": "observation-guidance-r6.md §3",
                "description": (
                    "邻域框口径收紧：frame_box_pct 收窄至可见现象本身的邻域"
                    "（现象延展范围+最小必要余量），不得把大片未受影响区域"
                    "包进邻域框；仍是非精确贴边的邻域声明（一般规则措辞，"
                    "零类别/位置暗示）"),
                "attribution_channel": (
                    "frame_box_pct 几何门（containment / area_ratio）"),
            },
            {
                "id": "category-criteria-exemplification",
                "target": "observation-guidance-r6.md §3A（新增节）",
                "description": (
                    "类别判据示例化：6 合法类别逐类 1-2 个中性视觉判据示例"
                    "（每例注明示例=判据说明，非期望清单；零坐标、零数量、"
                    "零板面引用）"),
                "attribution_channel": "类别匹配门",
            },
        ],
        "unchanged_components": [
            "渲染：复用 R5 冻结渲染件（零仪器变更、零重渲染）",
            "角色与盲读纪律（r6 指引 §1，逐字）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与 r4 圆括号"
            "中性释义零改动；r6 指引 §2）",
            "置信度与弃权规则（r6 指引 §4，逐字）",
            "courtyard 中性说明（r6 指引 §5，逐字）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r6 指引 §6，仅视角前缀机械替换）",
            "格式对齐提示（r6 指引 §7；fail-closed 校验口径，逐字）",
            "位置口径的坐标定义与 top/bottom 图像空间一致性（r6 指引 §3 "
            "前两条，逐字）",
            "bottom 视口径：沿用 r4 指引不改（为 bottom 单独定图层清单属"
            "渲染侧变更，R7 候选，不在本轮）",
            "机械替换仅两处：视角前缀 R4T/R4B→R6T/R6B；round_id_constant "
            "2026-09-06-r4→2026-09-06-r6",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；为 bottom 单独定图层清单属渲染侧变"
            "更，为 R7 候选，不在本轮"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "round*-dev-record.json、derivation-log-*、任何 compare/评估产"
            "物；指引作者唯一输入=observation-guidance-r4.md + 包指令抽象"
            "条目（GT/flag ID 已剥离）"),
        "attribution_plan": {
            "declaration": (
                "两项变更命中不同度量通道；轮后按 R5 失败通道分组归因"),
            "channel_1": {
                "change": "neighborhood-frame-tightening",
                "gate": "frame_box_pct 几何门",
                "metrics": ["containment", "area_ratio"],
            },
            "channel_2": {
                "change": "category-criteria-exemplification",
                "gate": "类别匹配门",
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "失败通道分组归因逻辑由编排侧在 close 包执行；本指引与本记"
                "录零 GT（无期望数量/分布/坐标/类别侧重提示）"),
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
    if not FRAMING_R5.exists():
        _fail(f"缺失：{FRAMING_R5}")
    if not GUIDANCE_R4.exists():
        _fail(f"缺失：{GUIDANCE_R4}")
    if not GUIDANCE_R6.exists():
        _fail("缺失 observation-guidance-r6.md（先落盘 D1 指引，后跑本脚本）")

    # ---- 验证（fail-closed）----
    import json

    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    framing_sha = _sha(FRAMING_R5)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs()

    guidance_r4_sha = _sha(GUIDANCE_R4)
    if not guidance_r4_sha.startswith(GUIDANCE_R4_SHA_PREFIX):
        _fail(f"r4 指引 sha 前 8={guidance_r4_sha[:8]} != 预期 "
              f"{GUIDANCE_R4_SHA_PREFIX}（冻结基线锚不符，立即停止）")
    guidance_r6_sha = _sha(GUIDANCE_R6)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          guidance_r4_sha=guidance_r4_sha,
                          guidance_r6_sha=guidance_r6_sha,
                          pdf_results=pdf_results,
                          png_results=png_results)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           guidance_r4_sha=guidance_r4_sha,
                           guidance_r6_sha=guidance_r6_sha,
                           pdf_results=pdf_results,
                           png_results=png_results)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r6-prep-record")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r6-prep] 重跑自证：r6-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。"
                  f"sha256={hashing.sha256_bytes(existing)[:16]}…")
            return
        _fail("r6-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r6-prep-record.json")
    sha = _sha(RECORD)
    print(f"[r6-prep] 验证通过：R5 冻结输入 PDF {len(pdf_results)} 件全 "
          f"match；renders-r5 四件 PNG 实测=见证常量（magic OK）；r4 指引"
          f"基线锚 {GUIDANCE_R4_SHA_PREFIX} OK")
    print(f"[r6-prep] guidance r6 sha256={guidance_r6_sha}")
    print(f"[r6-prep] 写出：r6-prep-record.json sha256={sha[:16]}…"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
