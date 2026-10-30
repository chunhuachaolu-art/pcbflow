#!/usr/bin/env python
"""CAL-R11-PREP：R11 协议侧单变量变更轮预备见证包（只写
out/v3-tl2/calibration/r11-prep-record.json；不写任何指引文件、不写
任何协议版本文件）。

R11 轮性质（预注册，非事后）：**协议侧单变量变更轮（每视角 reader 实
例 1→3；指引/渲染/GT/阈值零变更）**——判读指引零字节复用 observation-
guidance-r9.md（本轮唯一判读依据，零文本变更、无新指引文件），渲染零字
节复用 R5 冻结件（零仪器变更、零重渲染），判读实质判据的变更变量恰零
个；唯一实验操纵=协议侧多实例修订（evaluation-protocol-v1→v1.1，追加
式：v1 语义=每视角 1 实例；v1.1=每视角 3 独立实例+聚合口径），对同指
引+同渲染每视角以 3 个独立 reader 实例盲读。执行 round10-dev-record
next_iteration_targets[0]（度量稳定性协议侧候选）方案 (a)（每格多实
例重复读，本轮取 n=3；用户 2026-09-07 拍板），目的=检验 r8→r9→r10 三
轮弃权率摆动是否主要由实例级因素贡献（轮内实例方差可观测性）。本脚本
只做 PREP，不做盲读、不做任何视觉判读、不写轮测试。

检验假设（hypothesis_id=r10-dev-record-candidate-0-i-multi-instance）：
同日同指引同渲染下，同视角实例之间的弃权率/旗标产量存在实质离散（轮内
实例方差可观测），即 r10 观测到的摆动主要由实例级因素贡献。预注册描述
性边界（非 APR-0011 门）：任一视角实例间弃权率极差（max−min）≥0.2=支
持；全部视角 <0.2=拒绝；全部视角 <0.1=强 reject 分层标注。结果无论方
向均如实入账；单轮 n=3=小样本方向性证据非统计证明（development 域只
描述不断言）。基线数字（r8=0.222222=4/18、r9=0.727273=8/11、
r10=0.285714=4/14）只作为已落盘 run-record 的引用记入本编排侧
prep-record，不进任何指引文件（指引零轮次结果数字）。

度量设计（measurement_design，预注册先于盲读冻结）五条：主记录单位=
实例；视角层聚合（中位数+最小+最大三分列）；GT 匹配 union/agreement
双口径并列（逐 GT 条目 matched_by_count 0..3）；联合门评价（APR-0011）
代表配置+per-metric 实例间范围+逐实例原始记录三者并列，不合并不挑优；
bottom 零旗标沿用库侧 cal._ratio 先例（pcbflow/calibration.py _ratio：
零分母→None+说明，r10 run-record bottom=0/0→None 同口径在案）。

功能（out/ 仅新建一个文件：r11-prep-record.json；既有产物零改动，
observation-guidance-r9.md 与 evaluation-protocol-v1.md 必须零字节不
动）：

  1. fail-closed 复核 observation-guidance-r9.md：sha256 前 8=a0c10154
     （不符即停=本轮唯一判读依据被改动）；并与 r10-prep-record.json
     guidance_reuse.sha256_measured 登记值交叉核对（链自洽）。
  2. fail-closed 复核 evaluation-protocol-v1.md 在盘且 sha256 前
     8=22dc7337（不符即停=v1.1 追加式修订的原文保留载体被改动）；修订
     声明只记于本 prep-record（协议自身状态行：后续修订=新版本文件，
     不回写；本轮不新建协议文件）。
  3. fail-closed 复核 r10-prep-record.json：sha256 前 8=3791edb1、
     schema_version=3.0、kind=tl2_calibration_r10_prep_record、
     round_id_constant=2026-09-07-r10（不符即停）；探测
     renders_reuse.png_witness 结构取见证常量并要求登记自洽
     （sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）；framing_reference.
     sha256 与盘上实测交叉核对（链自洽）。
  4. fail-closed 复核 round10-dev-record.json：sha256 前 8=da4e85f9、
     round_id=2026-09-07-r10（不符即停）；从 next_iteration_targets 按
     内容标记唯一定位度量稳定性协议侧候选项（「度量稳定性候选（协议
     侧」），实测索引回填并要求=[0]；原文逐字摘录作预注册引用。
  5. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全
     match 才继续）；并复核 frozen_inputs 无 renders-r5 输出 PNG 哈希
     登记字段（r5 前缀键不存在、r4_frozen_png_sha256_reference 在场，
     不符即停）。
  6. fail-closed 复核 renders-r5 四件 PNG：magic + sha256 实测 vs 上
     述见证常量（全 match 才继续；防改动冻结渲染）。
  7. 落盘 r11-prep-record.json（canonical JSON=
     hashing.canonical_json_bytes：ensure_ascii=False / sort_keys /
     indent=1 / LF；顶层键集合与 r10-prep-record 逐键镜像断言，文档化
     差异=新增三键「protocol_amendment」「user_directive_note」
     「measurement_design」（协议侧修订声明/用户拍板排程/预注册度量设
     计需显式键；r10 的 guidance_reuse/manipulated_factor 语义沿用）；
     hypothesis_test 键集合与 r10 逐键镜像零差异）；同参重建两次逐字节
     一致自证；防覆写守卫——目标文件已存在且重建字节非逐字节等同→
     FAIL，等同→允许幂等重跑（零覆写）；落盘后重读盘面字节回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r11）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读）；
无 subprocess / 无网络 / 无主机绝对路径；不读 GT / reader-raw-* /
calibration-run-* / derivation-log-* / compare 产物（round10-dev-record
仅读 next_iteration_targets/round_id/schema_version 字段取预注册原文；
r10-prep-record 仅用于取 PNG 见证常量与链交叉核对）；无 git；本脚本对
observation-guidance-r9.md 与 evaluation-protocol-v1.md 只读（仅哈
希），零写入。记录内零 GT（无期望数量/分布/坐标/类别侧重提示）；基线
数字仅入本编排侧记录。

用法：python scripts/s44_calibration_r11_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R10_PREP_RECORD = CAL_DIR / "r10-prep-record.json"
R10_DEV_RECORD = CAL_DIR / "round10-dev-record.json"
GUIDANCE_R9 = CAL_DIR / "observation-guidance-r9.md"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r11-prep-record.json"

DATE_CONSTANT = "2026-09-07"
ROUND_ID = "2026-09-07-r11"

#: 冻结基线锚（开工实测给定；不符即停）。GUIDANCE_R9=本轮唯一判读依据，
#: EVAL_PROTOCOL_V1=v1.1 追加式修订的原文保留载体；开工/收工由编排侧
#: 另验；本脚本内亦 fail-closed 复核。
GUIDANCE_R9_SHA_PREFIX = "a0c10154"
R10_PREP_RECORD_SHA_PREFIX = "3791edb1"
R10_DEV_RECORD_SHA_PREFIX = "da4e85f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"

#: round10-dev-record next_iteration_targets 度量稳定性协议侧候选项的
#: 内容定位标记（按标记唯一定位、实际索引实测回填并要求=[0]，不符即停）
MARK_CANDIDATE_PROTO = "度量稳定性候选（协议侧"
MARK_CANDIDATE_PLAN_A = "每格多实例重复读（n≥3"
MARK_CANDIDATE_PREREG = "两案均须先预注册再执行"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；见证常量从 r10-prep-record
#: renders_reuse.png_witness 登记探测取得，不在此硬编码）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 顶层键集合相对 r10-prep-record 的文档化差异（协议侧单变量轮的结构语
#: 义：新增 protocol_amendment=evaluation-protocol-v1→v1.1 追加式修订
#: 声明；user_directive_note=用户拍板与单变量排程；measurement_design=
#: 预注册度量设计五条。零移除——r10 的 guidance_reuse/
#: manipulated_factor 语义沿用）
TOP_LEVEL_KEY_DELTA_REMOVE = ()
TOP_LEVEL_KEY_DELTA_ADD = ("protocol_amendment", "user_directive_note",
                           "measurement_design")

#: hypothesis_test 键集合相对 r10-prep-record 零差异（13 键逐键镜像）
HT_KEY_DELTA_REMOVE = ()
HT_KEY_DELTA_ADD = ()


def _fail(msg: str) -> None:
    print(f"[r11-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s42 模式；零写入）
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r10_record: dict) -> dict:
    """探测 r10-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r10_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r10-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
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
    """复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段（与 r10 记录
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


def _extract_candidate_target(dev_record: dict) -> dict:
    """从 round10-dev-record next_iteration_targets 取度量稳定性候选原文。

    按内容标记唯一定位（「度量稳定性候选（协议侧」），实测索引回填并要
    求=[0]（用户拍板所引条目）；定位不到或歧义即停。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round10-dev-record next_iteration_targets 结构不符")
    idx = [i for i, t in enumerate(targets)
           if isinstance(t, str) and MARK_CANDIDATE_PROTO in t]
    if len(idx) != 1:
        _fail(f"next_iteration_targets 标记「{MARK_CANDIDATE_PROTO}」定位歧义：{idx}")
    if idx[0] != 0:
        _fail(f"度量稳定性候选实测索引={idx[0]} != 预注册给定 [0]")
    text = targets[idx[0]]
    if MARK_CANDIDATE_PLAN_A not in text:
        _fail("候选项缺「每格多实例重复读（n≥3」标记（方案 (a) 缺失）")
    if MARK_CANDIDATE_PREREG not in text:
        _fail("候选项缺预注册前置声明标记")
    return {
        "index_zero_based": idx[0],
        "candidate_target": text,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r10_record_sha: str, dev_record_sha: str,
                 protocol_sha: str, guidance_r9_sha: str, pdf_results: list,
                 png_results: list, quote: dict) -> dict:
    """构建 r11-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r11_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r11",
        "round_nature": (
            "协议侧单变量变更轮（每视角 reader 实例 1→3；指引/渲染/GT/阈值"
            "零变更）：判读指引零字节复用 observation-guidance-r9.md（本轮"
            "唯一判读依据，零文本变更、无新指引文件），渲染零字节复用 R5 冻"
            "结件（零仪器变更、零重渲染），判读实质判据的变更变量恰零个；唯"
            "一实验操纵=协议侧多实例修订（evaluation-protocol-v1→v1.1，追"
            "加式，见 protocol_amendment）——每视角以 3 个独立 reader 实例"
            "（i1/i2/i3）对同指引+同渲染盲读（执行 round10-dev-record "
            "next_iteration_targets[0] 方案 (a) 每格多实例重复读，本轮取 "
            "n=3，用户 2026-09-07 拍板，见 user_directive_note 与 "
            "hypothesis_test.preregistration_ref）；度量设计五条预注册先于"
            "盲读冻结（见 measurement_design）；observation-guidance-r9.md "
            "已在案冻结、本轮零指引作者动作；盲读由编排侧在本记录之后以 "
            "12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-07 拍板两项：(1) 度量稳定性候选（round10-dev-"
            "record next_iteration_targets[0]）采纳方案 (a) 每格多实例重复"
            "读，本轮取 n=3——即本轮执行的协议侧单变量；(2) §3A 示例 c 措辞"
            "修改（next_iteration_targets[1]，指引侧）排程至 R12、本轮不做"
            "。编排侧单变量排程声明：先协议后指引，两轮各自单变量（R11=协"
            "议侧每视角实例数 1→3；R12=指引侧示例 c 措辞，届时另行预注册）"),
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "amendment_version": "v1.1",
            "amendment_mode": "追加式（additive）：不改动 v1 任何既有条款语义，只追加盲读执行与聚合口径",
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视角"
                "层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径并"
                "列、联合门代表配置+实例间范围并列（全部见 measurement_"
                "design，预注册先于盲读冻结）"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（本脚本 fail-closed 在盘+哈希复核）；"
                    "v1.1 修订声明只记于本 prep-record，不回写 v1 文件（协议"
                    "自身状态行：后续修订=新版本文件，不回写）；正式 v1.1 版"
                    "本文件若需落盘属后续动作，本轮不新建协议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实例"
                "（i1/i2/i3）；实例上下文=指引+单张 PNG+派发命名指令，零 GT；"
                "两波次串行保序（同一实例先 applied 后 prep1，flag_id 编号"
                "跨板连续）"),
            "naming": (
                "reader_id=reader-r11-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R11T/R11B（由 r9 指引 §6 的 R9T/R9B 机械替换，派发指令给"
                "出）；实例间编号独立，同实例跨板连续"),
            "scope_note": (
                "本修订只改盲读执行与聚合口径，不改指引判据/渲染/GT/阈值任何"
                "实质；若 v1.1 后被正式采纳，其对门的评价含义须另行声明，本"
                "轮 in_calibrated_range 恒 False"),
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
                "path_rel": "out/v3-tl2/calibration/r10-prep-record.json",
                "sha256": r10_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量照抄 r10-prep-record.json "
                    "renders_reuse.png_witness 登记（来源链：r10-prep-record "
                    "取自 r9-prep-record，r9-prep-record 取自 r8-prep-record，"
                    "r8-prep-record 取自 r7-prep-record，源头=2026-09-06 "
                    "s35/s33 首跑实测；本脚本探测该结构取常量并要求登记自"
                    "洽，另对来源文件以 3791edb1 锚 fail-closed 复核），非"
                    "本脚本新测——R11 零仪器变更、零重渲染，不产生新见证"),
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
                    "故 renders-r5 PNG 见证常量以 r10-prep-record.json 登记"
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
                "为 R5 渲染实测事实（沿用 r10-prep-record 登记，本脚本实测仍"
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
                "在本轮由编排侧派发指令机械替换为 R11T/R11B 与 reader-r11-"
                "{top,bottom}-i{1,2,3}（命名属编排侧机械替换，非判据变更；"
                "判读实质判据零变更；实例间编号独立、同实例跨板连续，见 "
                "protocol_amendment.naming）；此覆盖如实入 run-record "
                "naming_constraints"),
        },
        "changed_variables": [],
        "manipulated_factor": (
            "唯一操纵因素=每视角独立 reader 实例数 1→3（协议侧单变量："
            "evaluation-protocol-v1→v1.1 追加式修订，见 protocol_amendment）；"
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
            "§3A 类别判据示例：6 类全部逐字原文（含示例 c 与 §3A 末尾对照说"
            "明零改动——示例 c 措辞修改已排程 R12，本轮零指引变更，见 "
            "user_directive_note）",
            "§4 全文：弃权判据（总原则「宁可 abstain 不硬标」、两条显式判"
            "据、存在性判断一般判据、三路出口显式化、confidence 定义与弃权 "
            "flag 输出细节、既有对照说明含 r8/r9 增补块）逐字原文（r9 指引 "
            "§4，零改动）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r9 指引 §6 原文；仅命名前缀编排侧机械替换，见 "
            "guidance_reuse.mechanical_naming_override）",
            "GT 集：照 s41（r9 close）口径零改动（gt-audit-r1 三候选全部关"
            "闭在案；GT 侧不再有候选，round10-dev-record next_iteration_"
            "targets[4] 在案）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作"
            "口径引用）",
            "格式对齐提示（r9 指引 §7）与 bottom 视口径（沿用 r4 指引："
            "top/bottom 判读口径在图像空间完全一致、不做镜像换算；未为 "
            "bottom 单独定图层清单——该属渲染侧变更，不在本轮）",
            "评估协议文件：evaluation-protocol-v1.md 零字节保留（v1.1 追加"
            "式修订只记于本记录，不回写 v1 文件，见 protocol_amendment）",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；本轮 bottom 每视角 3 实例使 bottom "
            "零旗标现象首次获得实例间重复观测（零期望；r10 bottom 两格零旗"
            "标在案、bottom=0/0→None 同口径）；渲染侧 bottom 图层清单属渲"
            "染侧变更，仍为后续轮候选（round10-dev-record next_iteration_"
            "targets[2] 在案），不在本轮"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R11 盲读冻结（本记录=预注册件；evaluation-"
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
            "hypothesis_id": "r10-dev-record-candidate-0-i-multi-instance",
            "hypothesis": (
                "同日同指引同渲染下，同视角实例之间的弃权率/旗标产量存在实质"
                "离散（轮内实例方差可观测），即 r10 观测到的摆动主要由实例级"
                "因素贡献。"),
            "test_design": (
                "协议侧单变量变更轮：指引 r9 零字节复用+R5 冻结渲染复用+GT/"
                "阈值零变更；唯一操纵=每视角独立实例数 1→3（evaluation-"
                "protocol-v1→v1.1 追加式修订）；12 次盲读=4 视角格×3 实例，"
                "两波次串行保序；度量设计五条预注册（measurement_design）先"
                "于盲读冻结。"),
            "baseline_reference": {
                "rounds": {
                    "r8": 0.222222,
                    "r8_fraction": "4/18",
                    "r9": 0.727273,
                    "r9_fraction": "8/11",
                    "r10": 0.285714,
                    "r10_fraction": "4/14",
                },
                "note": (
                    "R8/R9/R10 三轮实测基线（编排侧记录；引用已落盘 run-"
                    "record 在案值；数字仅入 prep-record，不进指引文件——指"
                    "引零轮次结果数字）。既有局限=跨轮 reader 实例群全更替"
                    "+轮内每格 n=1，三轮各为单点读数、轮内实例方差不可观测"
                    "——本轮即补该缺口"),
            },
            "support_condition": (
                "≥1 个视角的实例间弃权率极差（max−min）≥0.2 → 证实 n=1 单点"
                "读数不可靠、多实例协议必要（r10 观测到的跨轮摆动主要由实例"
                "级因素贡献获方向性支持）。"),
            "reject_condition": (
                "全部视角实例间弃权率极差 <0.2 → r10 跨轮摆动主要归于跨轮因"
                "素（如工具行为代际漂移）而非轮内实例采样，n=1 稳定性优于预"
                "判；补充分层：全视角极差 <0.1 记「强 reject」并如实标注。"),
            "null_result_note": (
                "结果无论方向均如实入账；单轮 n=3 仍是小样本方向性证据非统计"
                "证明（development 域只描述不断言）；「正确测出无效同样是有"
                "效证据」；0.2/0.1 为本轮预注册描述性边界，非 APR-0011 门 "
                "evaluation 本身（门三指标照常独立如实计算，互不凌驾）；度量"
                "与聚合口径执行由编排侧在 close 包执行；本记录零 GT（无期望"
                "数量/分布/坐标/类别侧重提示）。"),
            "declaration": (
                "实例级弃权率与实例间弃权率极差（本轮假设主通道）按预注册度量"
                "设计如实计算；视角层中位数/最小/最大聚合与 GT 匹配 union/"
                "agreement 双口径照常如实记录（APR-0011 阈值零改动、门照常"
                "独立计算）；跨实例=本轮被操纵因素、每视角 n=3；「正确测出无"
                "效同样是有效证据」。"),
            "preregistered_criteria_quote": {
                "candidate_0_target": quote["candidate_target"],
                "user_directive_2026_09_07": (
                    "用户拍板：(1) 采纳方案 (a) 每格多实例重复读（本轮 n=3）；"
                    "(2) 示例 c 措辞修改排程 R12（指引侧，本轮不做）"),
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round10-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R10_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": [quote["index_zero_based"]],
                "note": (
                    "引用原文逐字摘录（措辞按文件原文，未改写）：索引 [0]=度"
                    "量稳定性候选（协议侧；方案 (a)=每格多实例重复读，本轮执"
                    "行；跨轮中位数门控=同条目另一案，未在本轮执行，留作后"
                    "续候选）。该方案先于 R11 盲读落盘预注册（本记录=预注册"
                    "件）。"),
            },
            "primary_channel_metric": (
                "实例间弃权率极差（每视角分列：top 3 实例 max−min、bottom 3 "
                "实例 max−min）——度量稳定性表征轮的主度量；实例间旗标产量极"
                "差与 GT 匹配双口径并列如实附录。"),
            "metric_lesson_application": (
                "r9/r10 教训（产量计数与弃权率互补记录；round10-dev-record "
                "next_iteration_targets[0] 单实例/轮设计的弃权率度量不稳定证"
                "据）延续记账；本轮聚合口径设计（union/agreement 并列、代表"
                "配置+范围并列）即度量设计演进的第一步，全部预注册于本记录、"
                "先于盲读冻结，不追溯往轮（r8/r9/r10 字母裁决维持不变）；跨"
                "轮中位数门控候选（同条目另一案）未在本轮执行，须另行预注册"
                "后采用。"),
            "secondary_observation": (
                "reroute 类逐实例产量对照（示例 c 词汇效应在 n=3 下的监测："
                "示例 c 判据在三个独立实例下各自的弃权/非弃权选择如实记录，"
                "零期望；指引措辞修改已排程 R12、本轮零指引变更）；courtyard "
                "密集旗被动追踪延续（零阈值改动零期望；round10-dev-record "
                "next_iteration_targets[3] 在案）；非弃权旗与同态 GT 的匹配"
                "表现照常如实计算（GT/阈值零改动、不得为提高命中调阈值）。"),
        },
        "attribution_plan": {
            "declaration": (
                "本轮恰一个协议侧操纵变量（每视角独立实例数 1→3）、检验恰一"
                "个假设（round10-dev-record next_iteration_targets[0] 方案 "
                "(a)；唯一操纵=实例数 1→3）；轮后按每视角实例间弃权率极差相"
                "对预注册描述性边界 0.2/0.1 的方向归因"),
            "primary_channel": {
                "change": "per-view-instance-count-1-to-3（协议侧唯一操纵；非指引/渲染/GT/阈值变更）",
                "metric": (
                    "实例间弃权率极差（每视角分列；预注册描述性边界：任一视"
                    "角 ≥0.2 支持、全部视角 <0.2 拒绝、全部视角 <0.1 强 "
                    "reject 分层标注）；实例间旗标产量极差与 GT 匹配双口径附"
                    "录"),
                "support": (
                    "任一视角实例间弃权率极差 ≥0.2 → n=1 单点读数不可靠、多"
                    "实例协议必要获方向性支持"),
                "reject": (
                    "全部视角实例间弃权率极差 <0.2 → r10 摆动主要归于跨轮因"
                    "素（如工具行为代际漂移）而非轮内实例采样"),
            },
            "guard_channel": {
                "metric": (
                    "其余类别非弃权旗 frame_box_pct 几何门（面积比出局条"
                    "目）"),
                "requirement": (
                    "§3 收窄判据零变更（指引零字节复用），非弃权框仍须满足；"
                    "几何门面积比出局条目无回升"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角层三"
                "分列聚合+GT 匹配双口径+联合门代表配置/范围并列；APR-0011 阈"
                "值零改动）；实例=本轮被操纵因素、每视角 n=3；归因分组逻辑由"
                "编排侧在 close 包执行；本指引零 GT、零轮次结果数字（基线数"
                "字仅入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "协议侧单变量轮无判据文本变更（指引零字节复用、无新指引文件）；"
            "0.2/0.1 描述性边界只用于本轮假设检验方向归因，不触碰 APR-0011 "
            "门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与任"
            "何阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX）；§3/§3A/§4 判据文"
            "本零变更，不降低任何存在性、归类、定位或报告的责任门槛；多实例"
            "聚合口径（union/agreement 并列、代表配置+范围并列）不构成任何"
            "门的放宽或收紧——门照常独立计算"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "derivation-log-*、任何 compare/评估产物；盲读纪律=指引 §1 原文"
            "（r9 指引零字节复用）；reader 实例上下文=指引文件"
            "（observation-guidance-r9.md）+单张 PNG+派发命名指令（R11T/"
            "R11B 前缀、reader-r11-{top,bottom}-i{1,2,3}），零 GT、零其他盘"
            "上文件；跨实例/跨视角禁止交流（12 次盲读相互独立、不得交换判读"
            "信息——独立性是多实例协议的前提）；本 prep 脚本自身输入="
            "r10-prep-record.json（仅取 renders-r5 PNG 见证常量与链交叉核"
            "对，hash 锚=3791edb1 先验证）、render-framing-r5.json（仅输入"
            "链复核）、round10-dev-record.json（仅读取 next_iteration_"
            "targets 字段取候选原文摘录，hash 锚=da4e85f9 先验证）、"
            "evaluation-protocol-v1.md（仅在盘+哈希复核，锚=22dc7337）；"
            "observation-guidance-r9.md 本脚本只读（仅哈希，a0c10154 锚 "
            "fail-closed），零写入。"),
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (FRAMING_R5, R10_PREP_RECORD, R10_DEV_RECORD, GUIDANCE_R9,
                 EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r10_record = json.loads(R10_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    dev_record = json.loads(R10_DEV_RECORD.read_text(encoding="utf-8"))
    r10_record_sha = _sha(R10_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)
    dev_record_sha = _sha(R10_DEV_RECORD)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    if not r10_record_sha.startswith(R10_PREP_RECORD_SHA_PREFIX):
        _fail(f"r10-prep-record sha 前 8={r10_record_sha[:8]} != 预期 "
              f"{R10_PREP_RECORD_SHA_PREFIX}（见证来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R10_DEV_RECORD_SHA_PREFIX):
        _fail(f"round10-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R10_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if not protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX):
        _fail(f"evaluation-protocol-v1.md sha 前 8={protocol_sha[:8]} != 预期 "
              f"{EVAL_PROTOCOL_V1_SHA_PREFIX}（v1.1 修订原文保留载体疑被改"
              f"动，立即停止）")
    if r10_record.get("schema_version") != "3.0":
        _fail("r10-prep-record schema_version != 3.0（结构漂移）")
    if r10_record.get("kind") != "tl2_calibration_r10_prep_record":
        _fail("r10-prep-record kind 不符（结构漂移）")
    if r10_record.get("round_id_constant") != "2026-09-07-r10":
        _fail("r10-prep-record round_id_constant != 2026-09-07-r10（结构漂移）")
    if dev_record.get("round_id") != "2026-09-07-r10":
        _fail("round10-dev-record round_id != 2026-09-07-r10（结构漂移）")

    # ---- r9 指引零字节复核（本轮唯一判读依据；只读）----
    guidance_r9_sha = _sha(GUIDANCE_R9)
    if not guidance_r9_sha.startswith(GUIDANCE_R9_SHA_PREFIX):
        _fail(f"r9 指引 sha 前 8={guidance_r9_sha[:8]} != 预期 "
              f"{GUIDANCE_R9_SHA_PREFIX}（本轮唯一判读依据疑被改动，立即停止）")
    registered_guidance_sha = (r10_record.get("guidance_reuse") or {}).get("sha256_measured")
    if registered_guidance_sha != guidance_r9_sha:
        _fail("r10-prep-record guidance_reuse.sha256_measured 登记值与盘上"
              "实测不符（链自洽破坏，立即停止）")

    # ---- framing 链自洽（与 r10-prep-record 登记交叉核对）----
    registered_framing_sha = (r10_record.get("renders_reuse") or {}).get(
        "framing_reference", {}).get("sha256")
    if registered_framing_sha != framing_sha:
        _fail("r10-prep-record renders_reuse.framing_reference.sha256 登记"
              "值与盘上实测不符（链自洽破坏，立即停止）")

    png_constants = _load_png_witness_constants(r10_record)
    _check_framing_raster_field(framing)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)
    quote = _extract_candidate_target(dev_record)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(framing_sha=framing_sha,
                          r10_record_sha=r10_record_sha,
                          dev_record_sha=dev_record_sha,
                          protocol_sha=protocol_sha,
                          guidance_r9_sha=guidance_r9_sha,
                          pdf_results=pdf_results,
                          png_results=png_results,
                          quote=quote)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r10_record_sha=r10_record_sha,
                           dev_record_sha=dev_record_sha,
                           protocol_sha=protocol_sha,
                           guidance_r9_sha=guidance_r9_sha,
                           pdf_results=pdf_results,
                           png_results=png_results,
                           quote=quote)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r11-prep-record")

    # ---- 顶层键集合与 r10-prep-record 镜像断言（文档化差异：新增三键）----
    expected_keys = (set(r10_record.keys())
                     - set(TOP_LEVEL_KEY_DELTA_REMOVE)
                     | set(TOP_LEVEL_KEY_DELTA_ADD))
    if set(record.keys()) != expected_keys:
        _fail(f"r11-prep-record 顶层键集合与 r10-prep-record 镜像（文档化差"
              f"异：-{TOP_LEVEL_KEY_DELTA_REMOVE} +{TOP_LEVEL_KEY_DELTA_ADD}）"
              f"不符：多={sorted(set(record.keys()) - expected_keys)}，"
              f"少={sorted(expected_keys - set(record.keys()))}")
    ht_expected = (set(r10_record["hypothesis_test"].keys())
                   - set(HT_KEY_DELTA_REMOVE)
                   | set(HT_KEY_DELTA_ADD))
    if set(record["hypothesis_test"].keys()) != ht_expected:
        _fail(f"hypothesis_test 键集合镜像（文档化差异："
              f"-{HT_KEY_DELTA_REMOVE} +{HT_KEY_DELTA_ADD}）不符："
              f"多={sorted(set(record['hypothesis_test'].keys()) - ht_expected)}，"
              f"少={sorted(ht_expected - set(record['hypothesis_test'].keys()))}")

    # ---- 结构自证：changed_variables 恰空、度量设计五条预注册 ----
    if record["changed_variables"] != []:
        _fail("r11 指引/渲染/GT/阈值零变更：changed_variables 必须为空列表")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5（预注册度量设计）")
    if record["protocol_amendment"]["v1_file_preserved"]["zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved 必须为真")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r11-prep] 重跑自证：r11-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r11-prep] 工件 sha256：r11-prep-record.json="
                  f"{hashing.sha256_bytes(existing)}")
            print(f"[r11-prep] r9 指引零字节复核（收工侧随编排另验）："
                  f"observation-guidance-r9.md={guidance_r9_sha}")
            return
        _fail("r11-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r11-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r11-prep] 验证通过：r9 指引零字节锚 {GUIDANCE_R9_SHA_PREFIX} OK"
          f"（只读，零写入）；r10-prep-record 见证来源锚 "
          f"{R10_PREP_RECORD_SHA_PREFIX} OK；dev-record 锚 "
          f"{R10_DEV_RECORD_SHA_PREFIX} OK（度量稳定性候选=索引 "
          f"[{quote['index_zero_based']}] 原文摘录在案）；evaluation-"
          f"protocol-v1 在盘锚 {EVAL_PROTOCOL_V1_SHA_PREFIX} OK（v1 原文零"
          f"字节保留）；renders-r5 四件 PNG 实测=在案见证常量（magic OK）；"
          f"R5 冻结输入 PDF {len(pdf_results)} 件全 match")
    print(f"[r11-prep] 协议侧单变量自证：changed_variables=[]；唯一操纵="
          f"每视角独立实例数 1→3（v1→v1.1 追加式）；顶层键镜像 r10（文档化"
          f"差异：+protocol_amendment、+user_directive_note、"
          f"+measurement_design）；hypothesis_test 键镜像 r10 零差异；度量"
          f"设计五条预注册先于盲读冻结")
    print(f"[r11-prep] 写出：r11-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
