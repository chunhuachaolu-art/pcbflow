#!/usr/bin/env python
"""CAL-R10-PREP：R10 零变更重复轮预备见证包（只写
out/v3-tl2/calibration/r10-prep-record.json；不写任何指引文件）。

R10 轮性质（预注册，非事后）：**零变更重复轮（同指引+同渲染+新 reader
实例群；分离实例差异与指引效应）**——判读指引零字节复用 observation-
guidance-r9.md（本轮唯一判读依据，零文本变更、无新指引文件），渲染零字
节复用 R5 冻结件（零仪器变更、零重渲染），恰零个变更变量；唯一实验操纵
=以全新 reader 子智能体实例群（四格各一）对同指引+同渲染再盲读一轮。
执行 round9-dev-record.json next_iteration_targets[0] 候选方案 (a)（同
指引重复轮），目的=把 r9 弃权率回升中的「reader 实例差异」与「指引效
应」分离开。本脚本只做 PREP，不做盲读、不做任何视觉判读、不写轮测试。

检验假设（hypothesis_id=r9-dev-record-candidate-0a）：r9 弃权率回升主
要由 reader 实例更替驱动，而非 §3A 示例 c 指引变更或板面内容驱动——同
指引+同渲染下换新实例群，弃权率将回落向 r8 水平。预注册裁决边界=本轮
abstain_rate_total 0.5（≤0.5 支持=实例差异主导方向性成立、>0.5 拒绝=
回升更可能系统性）；该边界只用于本轮假设检验字母裁决，不触碰 APR-0011
门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与任何阈值
常量。结果无论方向均如实入账；n=1 实例群、单次重复=方向性证据非统计证
明（development 域只描述不断言）。基线数字（r9=0.727273=8/11、
r8=0.222222=4/18）只作为已落盘 run-record 的引用记入本编排侧
prep-record，不进任何指引文件（指引零轮次结果数字）。

功能（out/ 仅新建一个文件：r10-prep-record.json；既有产物零改动，
observation-guidance-r9.md 必须零字节不动）：

  1. fail-closed 复核 observation-guidance-r9.md：sha256 前 8=a0c10154
     （不符即停=本轮唯一判读依据被改动）；并与 r9-prep-record.json
     guidance.sha256 登记值交叉核对（链自洽）。
  2. fail-closed 复核 r9-prep-record.json：sha256 前 8=dd979632、
     schema_version=3.0、kind=tl2_calibration_r9_prep_record（不符即
     停）；探测 renders_reuse.png_witness 结构取见证常量并要求登记自洽
     （sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）。
  3. fail-closed 复核 round9-dev-record.json：sha256 前 8=5ee18d61、
     round_id=2026-09-07-r9（不符即停）；从 next_iteration_targets 按
     内容标记唯一定位候选方案 (a) 项（「同指引重复轮」），实测索引回填
     并要求=[0]；原文逐字摘录作预注册引用。
  4. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全
     match 才继续）；并复核 frozen_inputs 无 renders-r5 输出 PNG 哈希
     登记字段（r5 前缀键不存在、r4_frozen_png_sha256_reference 在场，
     不符即停）。
  5. fail-closed 复核 renders-r5 四件 PNG：magic + sha256 实测 vs 上
     述见证常量（全 match 才继续；防改动冻结渲染）。
  6. 落盘 r10-prep-record.json（canonical JSON=
     hashing.canonical_json_bytes：ensure_ascii=False / sort_keys /
     indent=1 / LF；顶层键集合与 r9-prep-record 逐键镜像断言，唯二文档
     化差异=「guidance」改名为「guidance_reuse」（r10 零指引作者动作，
     复用代替生成）+新增「manipulated_factor」（零变更轮的唯一实验操纵
     需显式键）；hypothesis_test 键集合镜像 r9，唯二文档化差异=
     「courtyard_tracking_note」并入「secondary_observation」）；同参
     重建两次逐字节一致自证；防覆写守卫——目标文件已存在且重建字节非
     逐字节等同→FAIL，等同→允许幂等重跑（零覆写）；落盘后重读盘面字节
     回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r10）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；
无 subprocess / 无网络 / 无主机绝对路径；不读 GT / reader-raw-* /
calibration-run-* / derivation-log-* / compare 产物（round9-dev-record
仅读 next_iteration_targets/round_id/schema_version 字段取预注册原文；
r9-prep-record 仅用于取 PNG 见证常量与链交叉核对）；无 git；本脚本对
observation-guidance-r9.md 只读（仅哈希），零写入。记录内零 GT（无期
望数量/分布/坐标/类别侧重提示）；基线数字仅入本编排侧记录。

用法：python scripts/s42_calibration_r10_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R9_PREP_RECORD = CAL_DIR / "r9-prep-record.json"
R9_DEV_RECORD = CAL_DIR / "round9-dev-record.json"
GUIDANCE_R9 = CAL_DIR / "observation-guidance-r9.md"
RECORD = CAL_DIR / "r10-prep-record.json"

DATE_CONSTANT = "2026-09-07"
ROUND_ID = "2026-09-07-r10"

#: 冻结基线锚（包指令给定；不符即停）。GUIDANCE_R9=本轮唯一判读依据，
#: 开工/收工由编排侧另验；本脚本内亦 fail-closed 复核。
GUIDANCE_R9_SHA_PREFIX = "a0c10154"
R9_PREP_RECORD_SHA_PREFIX = "dd979632"
R9_DEV_RECORD_SHA_PREFIX = "5ee18d61"

#: round9-dev-record next_iteration_targets 候选方案 (a) 项的内容定位
#: 标记（按标记唯一定位、实际索引实测回填并要求=[0]，不符即停）
MARK_CANDIDATE_0A = "同指引重复轮"
MARK_CANDIDATE_0A_PLAN = "候选方案：(a) 同指引重复轮"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；见证常量从 r9-prep-record
#: renders_reuse.png_witness 登记探测取得，不在此硬编码）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 顶层键集合相对 r9-prep-record 的文档化差异（零变更轮的结构语义：
#: guidance 改名 guidance_reuse——r10 复用代替生成；新增
#: manipulated_factor——零变更轮的唯一实验操纵需显式键）
TOP_LEVEL_KEY_DELTA_REMOVE = ("guidance",)
TOP_LEVEL_KEY_DELTA_ADD = ("guidance_reuse", "manipulated_factor")

#: hypothesis_test 键集合相对 r9-prep-record 的文档化差异
#: （courtyard_tracking_note 并入 secondary_observation）
HT_KEY_DELTA_REMOVE = ("courtyard_tracking_note",)
HT_KEY_DELTA_ADD = ("secondary_observation",)


def _fail(msg: str) -> None:
    print(f"[r10-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s40 模式；零写入）
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r9_record: dict) -> dict:
    """探测 r9-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r9_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r9-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
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
    """复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段（与 r9 记录
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


def _extract_candidate_0a_quote(dev_record: dict) -> dict:
    """从 round9-dev-record next_iteration_targets 取候选方案 (a) 项原文。

    按内容标记唯一定位（「同指引重复轮」），实测索引回填并要求=[0]（包指
    令给定第 [0] 项方案 (a)）；定位不到或歧义即停。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round9-dev-record next_iteration_targets 结构不符")
    idx = [i for i, t in enumerate(targets)
           if isinstance(t, str) and MARK_CANDIDATE_0A in t]
    if len(idx) != 1:
        _fail(f"next_iteration_targets 标记「{MARK_CANDIDATE_0A}」定位歧义：{idx}")
    if idx[0] != 0:
        _fail(f"候选方案 (a) 实测索引={idx[0]} != 预注册给定 [0]")
    text = targets[idx[0]]
    if MARK_CANDIDATE_0A_PLAN not in text:
        _fail("候选项缺「候选方案：(a) 同指引重复轮」标记")
    if "须预注册后执行" not in text or "须先预注册再执行" not in text:
        _fail("候选项缺预注册前置声明标记")
    return {
        "index_zero_based": idx[0],
        "candidate_target": text,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r9_record_sha: str, dev_record_sha: str,
                 guidance_r9_sha: str, pdf_results: list, png_results: list,
                 quote: dict) -> dict:
    """构建 r10-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r10_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r10",
        "round_nature": (
            "零变更重复轮（同指引+同渲染+新 reader 实例群；分离实例差异与指"
            "引效应）：判读指引零字节复用 observation-guidance-r9.md（本轮唯"
            "一判读依据，零文本变更、无新指引文件），渲染零字节复用 R5 冻结件"
            "（零仪器变更、零重渲染），恰零个变更变量；唯一实验操纵=以全新 "
            "reader 子智能体实例群（四格各一）对同指引+同渲染再盲读一轮——把 "
            "r9 弃权率回升中的「reader 实例差异」与「指引效应」分离开（执行 "
            "round9-dev-record next_iteration_targets[0] 候选方案 (a)，见 "
            "hypothesis_test.preregistration_ref）；observation-guidance-r9."
            "md 已在案冻结、本轮零指引作者动作；盲读由编排侧在本记录之后以全"
            "新实例群重新执行"),
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "png_witness_source": {
                "path_rel": "out/v3-tl2/calibration/r9-prep-record.json",
                "sha256": r9_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量照抄 r9-prep-record.json "
                    "renders_reuse.png_witness 登记（来源链：r9-prep-record "
                    "取自 r8-prep-record，r8-prep-record 取自 r7-prep-"
                    "record，源头=2026-09-06 s35/s33 首跑实测；本脚本探测该"
                    "结构取常量并要求登记自洽，另对来源文件以 "
                    "dd979632 锚 fail-closed 复核），非本脚本新测——R10 零"
                    "仪器变更、零重渲染，不产生新见证"),
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
                    "故 renders-r5 PNG 见证常量以 r9-prep-record.json 登记"
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
                "为 R5 渲染实测事实（沿用 r9-prep-record 登记，本脚本实测仍"
                "符），照实登记，不含任何 GT 含义"),
            "no_instrument_change": True,
        },
        "guidance_reuse": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r9.md",
            "sha256_prefix_expected": GUIDANCE_R9_SHA_PREFIX,
            "sha256_measured": guidance_r9_sha,
            "match": guidance_r9_sha.startswith(GUIDANCE_R9_SHA_PREFIX),
            "zero_byte_reuse": True,
            "role": "本轮唯一判读依据，零字节复用（r9 指引落盘即冻结；本轮零指引作者动作、零文本变更，无新指引文件）",
            "mechanical_naming_override": (
                "指引 §6 的 flag_id 前缀 R9T/R9B 与 reader_id reader-r9-* "
                "在本轮由编排侧派发指令机械替换为 R10T/R10B 与 reader-r10-*"
                "（命名属编排侧机械替换，非判据变更；判读实质判据零变更）；"
                "此覆盖如实入 run-record naming_constraints"),
        },
        "changed_variables": [],
        "manipulated_factor": (
            "唯一操纵因素=reader 实例群更替（全新子智能体实例，四格各一）；"
            "指引/渲染/GT/阈值零变更"),
        "unchanged_components": [
            "判读指引：observation-guidance-r9.md 零字节复用（本轮唯一判读"
            "依据；无新指引文件，零文本变更，sha256 前 8=a0c10154 本脚本"
            "fail-closed 复核）",
            "渲染：R5 冻结渲染件逐字节复用（零仪器变更、零重渲染；四件 PNG "
            "实测=在案见证常量）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r9 指引 §2 原文）",
            "§3 邻域框收窄判据与坐标口径（r9 指引 §3 原文）",
            "§3A 类别判据示例：6 类全部逐字原文（含 r9 增补示例 c 与 §3A "
            "末尾 r9 对照说明，零改动）",
            "§4 全文：弃权判据（总原则「宁可 abstain 不硬标」、两条显式判"
            "据、存在性判断一般判据、三路出口显式化、confidence 定义与弃权 "
            "flag 输出细节、既有对照说明含 r8/r9 增补块）逐字原文（r9 指引 "
            "§4，零改动）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r9 指引 §6 原文；仅命名前缀编排侧机械替换，见 "
            "guidance_reuse.mechanical_naming_override）",
            "GT 集：照 s41（r9 close）口径零改动（gt-audit-r1 三候选全部关"
            "闭在案；GT 侧不再有候选，round9-dev-record next_iteration_"
            "targets[4] 在案）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作"
            "口径引用）",
            "格式对齐提示（r9 指引 §7）与 bottom 视口径（沿用 r4 指引："
            "top/bottom 判读口径在图像空间完全一致、不做镜像换算；未为 "
            "bottom 单独定图层清单——该属渲染侧变更，不在本轮）",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；为 bottom 单独定图层清单属渲染侧变更，"
            "仍为后续轮候选（round9-dev-record next_iteration_targets[1] 在"
            "案），不在本轮"),
        "hypothesis_test": {
            "hypothesis_id": "r9-dev-record-candidate-0a",
            "hypothesis": (
                "r9 弃权率回升主要由 reader 实例更替驱动，而非 §3A 示例 c 指"
                "引变更或板面内容驱动——同指引+同渲染下换新实例群，弃权率将回"
                "落向 r8 水平。"),
            "test_design": (
                "零变更重复轮：指引 r9 零字节复用+R5 冻结渲染复用+全新四实例"
                "盲读；唯一操纵=实例群更替。"),
            "baseline_reference": {
                "round": "r9",
                "abstain_rate_total": 0.727273,
                "abstain_fraction": "8/11",
                "reference_round_abstain": {
                    "r8": 0.222222,
                    "r8_fraction": "4/18",
                },
                "note": (
                    "R9/R8 实测基线（编排侧记录；数字仅入 prep-record，不进"
                    "指引文件——指引零轮次结果数字）"),
            },
            "support_condition": (
                "R10 盲读 abstain_rate_total ≤ 0.5（即相对 r9 回落、靠近 r8 "
                "一侧），则「实例差异主导 r9 回升」获方向性支持（r8 的 0.222 "
                "与 r9 的 0.727 之间差异主要由实例群特异性行为贡献，指引效应"
                "在 n=1 设计下不可归因）。"),
            "reject_condition": (
                "R10 abstain_rate_total > 0.5（高位维持），则回升更可能是系"
                "统性的（指向 r9 指引增补、判读模型行为漂移或板面刺激侧因素，"
                "实例差异不足以解释）。"),
            "null_result_note": (
                "结果无论方向均如实入账；n=1 实例群、单次重复=方向性证据非统"
                "计证明（development 域只描述不断言）；「正确测出无效同样是"
                "有效证据」；0.5 为本轮预注册裁决边界，非 APR-0011 门 "
                "evaluation 本身（门三指标照常独立如实计算，互不凌驾）；度量"
                "与归因分组由编排侧在 close 包执行；本记录零 GT（无期望数量/"
                "分布/坐标/类别侧重提示）。"),
            "declaration": (
                "abstain_rate_total（本轮假设主通道）照常如实计算；聚合 "
                "matches/recall/seed_match_rate 与按类别/视角分列产量计数亦"
                "照常如实记录（联合评价口径与 APR-0011 阈值零改动）；跨轮 "
                "reader 实例不同=本轮被操纵因素、每格 n=1；「正确测出无效同"
                "样是有效证据」。"),
            "preregistered_criteria_quote": {
                "candidate_0_plan_a_target": quote["candidate_target"],
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round9-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R9_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": [quote["index_zero_based"]],
                "note": (
                    "引用原文逐字摘录（措辞按文件原文，未改写）：索引 [0]=弃"
                    "权率回升实例异质性归因追问（候选方案 (a)=同指引重复轮，"
                    "本轮执行；候选方案 (b)=多 reader 重复读，未在本轮执行，"
                    "留作后续候选）。该方案先于 R10 盲读落盘预注册（本记录="
                    "预注册件）。"),
            },
            "primary_channel_metric": (
                "abstain_rate_total（本轮假设的直接度量；照 r8 教训同时按类"
                "别/视角分列产量计数附录）。"),
            "metric_lesson_application": (
                "r9 教训（产量计数无法区分『判据化解』与『刺激缺席』，"
                "round9-dev-record next_iteration_targets[3] 协议侧候选）延"
                "续记账；本轮主通道回到弃权率本身（假设即关于弃权率的实例归"
                "因），产量计数按类别/视角分列如实附录；该教训的协议侧候选"
                "（产量计数与刺激存在性核验配对）须另行预注册后采用，不因本"
                "轮隐含采用；不追溯改判 r9（r9 字母裁决=supported 维持不"
                "变）。"),
            "secondary_observation": (
                "reroute 类产量对照——若 R10 出现 reroute 类旗标（产量≥1），"
                "则 r9「刺激缺席」机制观察需修正为实例群特异性；若仍为 0，刺"
                "激缺席证据增强。另：courtyard 密集旗被动追踪延续（零阈值改"
                "动零期望；r9 top 非弃权 courtyard 2 条与同态 GT 零交集在"
                "案，round9-dev-record next_iteration_targets[2]）；非弃权"
                "旗与同态 GT 的匹配表现照常如实计算（GT/阈值零改动、不得为"
                "提高命中调阈值）。"),
        },
        "attribution_plan": {
            "declaration": (
                "本轮恰零个变更变量、检验恰一个假设（round9-dev-record "
                "next_iteration_targets[0] 候选方案 (a)；唯一操纵=实例群更"
                "替）；轮后按 abstain_rate_total 相对预注册裁决边界 0.5 的方"
                "向归因"),
            "primary_channel": {
                "change": "reader-instance-group-swap（唯一操纵；非指引/渲染/GT/阈值变更）",
                "metric": (
                    "abstain_rate_total（预注册裁决边界=0.5：≤0.5 支持、"
                    ">0.5 拒绝）；按类别/视角分列产量计数附录"),
                "support": (
                    "R10 abstain_rate_total ≤ 0.5 → 实例差异主导 r9 回升获"
                    "方向性支持"),
                "reject": (
                    "R10 abstain_rate_total > 0.5 → 回升更可能是系统性的"
                    "（指引增补/模型行为漂移/板面刺激侧因素）"),
            },
            "guard_channel": {
                "metric": (
                    "其余类别非弃权旗 frame_box_pct 几何门（面积比出局条"
                    "目）"),
                "requirement": (
                    "§3 收窄判据零变更（零变更轮），非弃权框仍须满足；几何"
                    "门面积比出局条目无回升"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标（弃权率/matches/recall/seed_match_rate）照常如实"
                "记录（联合评价口径与 APR-0011 阈值零改动）；跨轮 reader 实"
                "例不同=本轮被操纵因素、每格 n=1；归因分组逻辑由编排侧在 "
                "close 包执行；本指引零 GT、零轮次结果数字（基线数字仅入本"
                "编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "零变更轮无判据文本变更（指引零字节复用、无新指引文件）；0.5 裁"
            "决边界只用于本轮假设检验字母裁决，不触碰 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与任何"
            "阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX）；§3/§3A/§4 判据文本"
            "零变更，不降低任何存在性、归类、定位或报告的责任门槛"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "derivation-log-*、任何 compare/评估产物；盲读纪律=指引 §1 原文"
            "（r9 指引零字节复用）；reader 实例上下文=指引文件"
            "（observation-guidance-r9.md）+单张 PNG+派发命名指令（R10T/"
            "R10B 前缀），零 GT、零其他盘上文件；本 prep 脚本自身输入="
            "r9-prep-record.json（仅取 renders-r5 PNG 见证常量与链交叉核"
            "对，hash 锚=dd979632 先验证）、render-framing-r5.json（仅输入"
            "链复核）、round9-dev-record.json（仅读取 next_iteration_"
            "targets 字段取候选方案 (a) 原文摘录，hash 锚=5ee18d61 先验"
            "证）；observation-guidance-r9.md 本脚本只读（仅哈希，a0c10154 "
            "锚 fail-closed），零写入。"),
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (FRAMING_R5, R9_PREP_RECORD, R9_DEV_RECORD, GUIDANCE_R9):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r9_record = json.loads(R9_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    dev_record = json.loads(R9_DEV_RECORD.read_text(encoding="utf-8"))
    r9_record_sha = _sha(R9_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)
    dev_record_sha = _sha(R9_DEV_RECORD)
    if not r9_record_sha.startswith(R9_PREP_RECORD_SHA_PREFIX):
        _fail(f"r9-prep-record sha 前 8={r9_record_sha[:8]} != 预期 "
              f"{R9_PREP_RECORD_SHA_PREFIX}（见证来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R9_DEV_RECORD_SHA_PREFIX):
        _fail(f"round9-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R9_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if r9_record.get("schema_version") != "3.0":
        _fail("r9-prep-record schema_version != 3.0（结构漂移）")
    if r9_record.get("kind") != "tl2_calibration_r9_prep_record":
        _fail("r9-prep-record kind 不符（结构漂移）")
    if dev_record.get("round_id") != "2026-09-07-r9":
        _fail("round9-dev-record round_id != 2026-09-07-r9（结构漂移）")

    # ---- r9 指引零字节复核（本轮唯一判读依据；只读）----
    guidance_r9_sha = _sha(GUIDANCE_R9)
    if not guidance_r9_sha.startswith(GUIDANCE_R9_SHA_PREFIX):
        _fail(f"r9 指引 sha 前 8={guidance_r9_sha[:8]} != 预期 "
              f"{GUIDANCE_R9_SHA_PREFIX}（本轮唯一判读依据疑被改动，立即停止）")
    registered_guidance_sha = (r9_record.get("guidance") or {}).get("sha256")
    if registered_guidance_sha != guidance_r9_sha:
        _fail("r9-prep-record guidance.sha256 登记值与盘上实测不符"
              "（链自洽破坏，立即停止）")

    png_constants = _load_png_witness_constants(r9_record)
    _check_framing_raster_field(framing)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)
    quote = _extract_candidate_0a_quote(dev_record)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r9_record_sha=r9_record_sha,
                          dev_record_sha=dev_record_sha,
                          guidance_r9_sha=guidance_r9_sha,
                          pdf_results=pdf_results,
                          png_results=png_results,
                          quote=quote)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r9_record_sha=r9_record_sha,
                           dev_record_sha=dev_record_sha,
                           guidance_r9_sha=guidance_r9_sha,
                           pdf_results=pdf_results,
                           png_results=png_results,
                           quote=quote)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r10-prep-record")

    # ---- 顶层键集合与 r9-prep-record 镜像断言（唯二文档化差异）----
    expected_keys = (set(r9_record.keys())
                     - set(TOP_LEVEL_KEY_DELTA_REMOVE)
                     | set(TOP_LEVEL_KEY_DELTA_ADD))
    if set(record.keys()) != expected_keys:
        _fail(f"r10-prep-record 顶层键集合与 r9-prep-record 镜像（文档化差"
              f"异：-{TOP_LEVEL_KEY_DELTA_REMOVE} +{TOP_LEVEL_KEY_DELTA_ADD}）"
              f"不符：多={sorted(set(record.keys()) - expected_keys)}，"
              f"少={sorted(expected_keys - set(record.keys()))}")
    ht_expected = (set(r9_record["hypothesis_test"].keys())
                   - set(HT_KEY_DELTA_REMOVE)
                   | set(HT_KEY_DELTA_ADD))
    if set(record["hypothesis_test"].keys()) != ht_expected:
        _fail(f"hypothesis_test 键集合镜像（文档化差异："
              f"-{HT_KEY_DELTA_REMOVE} +{HT_KEY_DELTA_ADD}）不符："
              f"多={sorted(set(record['hypothesis_test'].keys()) - ht_expected)}，"
              f"少={sorted(ht_expected - set(record['hypothesis_test'].keys()))}")

    # ---- 零变更轮自证：changed_variables 恰空 ----
    if record["changed_variables"] != []:
        _fail("零变更轮 changed_variables 必须为空列表")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r10-prep] 重跑自证：r10-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r10-prep] 工件 sha256：r10-prep-record.json="
                  f"{hashing.sha256_bytes(existing)}")
            print(f"[r10-prep] r9 指引零字节复核（收工侧随编排另验）："
                  f"observation-guidance-r9.md={guidance_r9_sha}")
            return
        _fail("r10-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r10-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r10-prep] 验证通过：r9 指引零字节锚 {GUIDANCE_R9_SHA_PREFIX} OK"
          f"（只读，零写入）；r9-prep-record 见证来源锚 "
          f"{R9_PREP_RECORD_SHA_PREFIX} OK；dev-record 锚 "
          f"{R9_DEV_RECORD_SHA_PREFIX} OK（预注册候选方案 (a)=索引 "
          f"[{quote['index_zero_based']}] 原文摘录在案）；renders-r5 四件 "
          f"PNG 实测=在案见证常量（magic OK）；R5 冻结输入 PDF "
          f"{len(pdf_results)} 件全 match")
    print(f"[r10-prep] 零变更轮自证：changed_variables=[]；唯一操纵="
          f"reader 实例群更替；顶层键镜像 r9（文档化差异："
          f"guidance→guidance_reuse、+manipulated_factor）；"
          f"hypothesis_test 键镜像 r9（courtyard_tracking_note 并入 "
          f"secondary_observation）")
    print(f"[r10-prep] 写出：r10-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
