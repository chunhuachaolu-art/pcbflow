#!/usr/bin/env python
"""CAL-R14-PREP：R14 纯仪器变更轮预备见证包（只写
out/v3-tl2/calibration/r14-prep-record.json；不写任何指引文件、不写
任何渲染/协议文件）。

R14 轮性质（预注册，非事后）：**纯仪器变更轮（bottom 视白色内容显式
化配色；指引零字节复用 r13）**——本轮恰零个指引侧变量：判读指引零字
节复用 observation-guidance-r13.md（本轮唯一判读依据，零文本变更、无
新指引文件），仪器侧单变量=bottom 渲染件更换（r5 白压平版→r14b 显式
配色版：白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)），top 两张
渲染自 renders-r5 逐字节复用（零变更）。此为 r5→r14b 首次渲染变更，
属「零仪器变更」纪律的显式例外声明（渲染侧单变量轮，预注册=
render-framing-r14b.json 7004b017 先于成图落盘）。执行 round13-dev-
record next_iteration_targets[0]（渲染侧消歧，6b34c442 先验证），用户
2026-09-08 拍板路线 A（指引零字节复用+不给颜色图例——无图例条件即本
轮检验设计的一部分）。仪器变更史：首试 framing-r14（918672b4）预制色
B.SilkS/B.CrtYd 被探针证伪（两板 bottom 该两层自有图元=0；成图与 r5
逐字节相同=零变更）如实作废保留；二试 framing-r14b（7004b017）基于
白色双来源探针（白墨矢量 162+4 图元 / 板内空隙白=墨缺失）落地。本脚
本只做 PREP，不做盲读、不做任何视觉判读、不写轮测试。

检验假设（hypothesis_id=r13-dev-record-candidate-0-render-disambiguate）：
bottom 白色内容显式化（橙=墨图元、绿=空隙）在无图例条件下不破坏 r13
的收敛——三实例对蝶形/空隙形态仍一致判入系统性正常路径（其周期几何
不因配色改变），且新配色被 reader 语义化利用（reading_notes 出现对
橙/绿的颜色-语义归属表述）。预注册描述性边界（非 APR-0011 门）：支
持=bottom courtyard 非弃权旗数极差 ≤5 且 bottom 聚合弃权率 ≤ r13 水
平（≤10/11）；拒绝=极差 >5（裁决重新发散）或聚合弃权率 >10/11（无
图例配色引发混淆）。基线数字（r13 bottom courtyard 非弃权 0/0/0 极差
0；bottom 旗数 3/4/4、弃权率 1.0/1.0/0.75、聚合 10/11 弃权；top 弃权
率 0.7/0.857143/0.285714）只作为已落盘 run-record 的引用记入本编排侧
prep-record，不进任何指引文件（指引零轮次结果数字）。

度量设计（measurement_design，预注册先于盲读冻结）五条照抄 r13-prep-
record（实例主记录/视角层三分列/union+agreement 双口径/代表配置+范围
+逐实例并列/零旗标 None 口径），仅声明行轮次编号更新。

功能（out/ 仅新建一个文件：r14-prep-record.json；datasets/ 与 out/
既有文件只读、零改动，observation-guidance-r13.md 必须零字节不动）：

  1. fail-closed 复核 observation-guidance-r13.md：sha256 前 8=c28806e1
     （不符即停=本轮唯一判读依据被改动）；并与 r13-prep-record.json
     guidance.sha256 登记值交叉核对（链自洽）。
  2. fail-closed 复核 r13-prep-record.json：sha256 前 8=b1c0d8b5、
     schema_version=3.0、kind=tl2_calibration_r13_prep_record、
     round_id_constant=2026-09-08-r13（不符即停）；探测
     renders_reuse.png_witness 结构取 renders-r5 四件 PNG 见证常量并
     要求登记自洽（sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）。
  3. fail-closed 复核 round13-dev-record.json：sha256 前 8=6b34c442、
     round_id=2026-09-08-r13（不符即停）；从 next_iteration_targets 按
     内容标记唯一定位渲染侧消歧候选项（「渲染侧消歧」），实测索引回
     填并要求=[0]；原文逐字摘录作预注册引用。
  4. fail-closed 复核 render-framing-r14b.json：sha256 前 8=7004b017、
     round_id_constant=2026-09-08-r14b、date_constant=2026-09-08（不
     符即停）；两板板界断言（expected_from_r5_derivation_log.
     board_px_bounds_full）须逐字=[6074,355,7839,2119]（与 r5 逐字同
     口径在案）；首试证伪登记（framing_r14=918672b4 /
     witness_r14=13fd1cab）在案复核。
  5. fail-closed 复核 render-witness-r14b.json：sha256 前 8=b63771f9、
     kind=tl2_calibration_render_witness_r14b（不符即停）；链自洽=
     witness.framing.sha256 与盘上 framing 实测逐字相同且
     unchanged_during_render 为真；配色语义=白墨图元→橙 [255,165,0]、
     板内空隙白→绿 [0,128,0]（color_mapping 结构探测）；两板
     palette_assertion_summary.assertions_pass 须为真且计数两板相同
     （橙 81672/绿 206632/白降 280886，结构探测取值）；conclusion 白
     墨矢量标记（「白墨矢量图元162 fill+4 stroke」）在案复核；
     r5_references.renders_r5_png_sha256 与 r13-prep-record 见证常量
     逐侧交叉核对（双链自洽）；top_zero_change_copies 登记值=见证常量；
     首试证伪登记与 framing 侧一致。
  6. fail-closed 复核渲染件字节事实：renders-r5 四件 PNG magic+实测
     sha=见证常量；renders-r14b 四件 PNG magic+实测——两张 top 与
     renders-r5 原件逐字节相同（sha 相同+bytes 相同双重判定=逐字节复
     用）、两张 bottom 实测均=d7284259 前缀且两板相同（与 r5 既有事实
     一致）且 != r5 bottom（仪器变更实测成立）；另与 witness 登记
     r14b bottom sha 交叉核对。
  7. fail-closed 复核 evaluation-protocol-v1.md 在盘且 sha256 前
     8=22dc7337（不符即停）。
  8. 落盘 r14-prep-record.json（canonical JSON=
     hashing.canonical_json_bytes：ensure_ascii=False / sort_keys /
     indent=1 / LF；顶层键集合与 r13-prep-record 逐键镜像断言，文档化
     差异=「guidance」→「guidance_reuse」（指引从新写变零字节复用）与
     「renders_reuse」→「instrument_change」（渲染从零变更变单变量变
     更，renders 见证结构内嵌其中）；hypothesis_test 键集合与 r13 逐键
     镜像零差异）；同参重建两次逐字节一致自证；防覆写守卫——目标文件
     已存在且重建字节非逐字节等同→FAIL，等同→允许幂等重跑（零覆写）；
     落盘后重读盘面字节回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-08 / 2026-09-08-r14）；
hash=sha256_file 字节口径（PNG 仅做哈希+magic+逐字节比对，零内容判
读、零像素读取）；无 subprocess / 无网络 / 无主机绝对路径；不读 GT /
reader-raw-* / calibration-run-* / derivation-log-* / 任何 compare 产
物（round13-dev-record 仅读 round_id/next_iteration_targets 字段取预
注册原文；r13-prep-record 仅用于取 renders-r5 PNG 见证常量与链交叉核
对）；无 git；本脚本对 observation-guidance-r13.md 只读（仅哈希），
零写入。记录内零 GT（无期望数量/分布/坐标/类别侧重提示；板界/调色板
计数为仪器侧几何与配色事实，非板面内容断言）；基线数字仅入本编排侧
记录。

用法：python scripts/s52_calibration_r14_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R13 = CAL_DIR / "observation-guidance-r13.md"
R13_PREP_RECORD = CAL_DIR / "r13-prep-record.json"
R13_DEV_RECORD = CAL_DIR / "round13-dev-record.json"
FRAMING_R14B = CAL_DIR / "render-framing-r14b.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r14-prep-record.json"

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r14"

#: 冻结基线锚（开工实测给定；不符即停）。GUIDANCE_R13=本轮唯一判读依据；
#: FRAMING/WITNESS_R14B=本轮仪器变更的预注册与见证件；开工/收工由编排侧
#: 另验；本脚本内亦 fail-closed 复核。
GUIDANCE_R13_SHA_PREFIX = "c28806e1"
R13_PREP_RECORD_SHA_PREFIX = "b1c0d8b5"
R13_DEV_RECORD_SHA_PREFIX = "6b34c442"
FRAMING_R14B_SHA_PREFIX = "7004b017"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
R14B_BOTTOM_SHA_PREFIX = "d7284259"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
FALSIFIED_FRAMING_R14_SHA_PREFIX = "918672b4"
FALSIFIED_WITNESS_R14_SHA_PREFIX = "13fd1cab"

#: r13 run-record（基线引用源）——编排侧 prep 时实测引用常量；本脚本零
#: 接触该文件（不读 calibration-run-*，纪律同 s44/s48）
RUN_RECORD_R13_SHA_CONSTANT = (
    "787c4589e1f85d4cdefc62fb36ffacd62eff5b195eed62baee99388bf7241136")

#: round13-dev-record next_iteration_targets 渲染侧消歧候选项的内容定位
#: 标记（按标记唯一定位、实际索引实测回填并要求=[0]，不符即停）
MARK_CANDIDATE_RENDER = "渲染侧消歧"
MARK_CANDIDATE_PREREG = "须预注册"
MARK_CANDIDATE_EXCEPTION = "零仪器变更纪律例外"

#: renders-r5 / renders-r14b 四件 PNG 的固定遍历顺序（确定性；见证常量
#: 从 r13-prep-record renders_reuse.png_witness 登记探测取得，不在此硬
#: 编码）
RENDERS_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 板界断言（与 r5 逐字同口径在案；render-framing-r14b.json
#: compose_and_crop_same_as_r5.expected_from_r5_derivation_log 两板
#: board_px_bounds_full 须逐字等于此值，不符即停）
EXPECTED_BOARD_BOUNDS = [6074, 355, 7839, 2119]

#: 白色双来源配色语义（render-witness-r14b.json color_mapping 结构探测
#: 目标值；不符即停）
ORANGE_TARGET_RGB = [255, 165, 0]
GREEN_TARGET_RGB = [0, 128, 0]
CONCLUSION_VECTOR_MARKER = "白墨矢量图元162 fill+4 stroke"

#: 顶层键集合相对 r13-prep-record 的文档化差异（纯仪器变更轮的结构语
#: 义：「guidance」→「guidance_reuse」=指引从新写落盘变零字节复用；
#: 「renders_reuse」→「instrument_change」=渲染从零字节复用变单变量
#: 仪器变更（renders 见证结构内嵌其中）。零移除其余键——r13 的
#: pre_round_review 等键全部保留镜像）
TOP_LEVEL_KEY_DELTA_REMOVE = ("guidance", "renders_reuse")
TOP_LEVEL_KEY_DELTA_ADD = ("guidance_reuse", "instrument_change")

#: hypothesis_test 键集合相对 r13-prep-record 零差异（13 键逐键镜像）
HT_KEY_DELTA_REMOVE = ()
HT_KEY_DELTA_ADD = ()


def _fail(msg: str) -> None:
    print(f"[r14-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s44 模式；零写入）
# ---------------------------------------------------------------------------

def _load_r5_png_witness_constants(r13_record: dict) -> dict:
    """探测 r13-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r13_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r13-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
    by_side = {}
    for item in witness:
        for key in ("state_side", "path_rel", "sha256_witness_constant",
                    "sha256_measured", "match_to_witness_constant"):
            if key not in item:
                _fail(f"png_witness 项缺键 {key}（结构探测失败）")
        by_side[item["state_side"]] = item
    if sorted(by_side) != sorted(RENDERS_SIDES):
        _fail(f"png_witness state_side 集不符：{sorted(by_side)}")
    constants = {}
    for side in RENDERS_SIDES:
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


def _check_png(path: Path, expected_sha: str, path_rel: str) -> dict:
    """PNG magic 检查 + 实测 sha256 vs 给定期望值。"""
    if not path.exists():
        _fail(f"PNG 缺失：{path}")
    with path.open("rb") as f:
        magic = f.read(8)
    if magic != PNG_MAGIC:
        _fail(f"{path.name}: 不是 PNG（magic 不符）")
    measured = _sha(path)
    return {
        "path_rel": path_rel,
        "sha256_measured": measured,
        "sha256_expected": expected_sha,
        "match": measured == expected_sha,
    }


def _check_r5_renders(constants: dict) -> dict:
    """renders-r5 四件 PNG：magic + 实测 sha vs r13-prep-record 见证常量。"""
    results = {}
    for side in RENDERS_SIDES:
        r = _check_png(CAL_DIR / "renders-r5" / f"{side}.png",
                       constants[side],
                       f"out/v3-tl2/calibration/renders-r5/{side}.png")
        if not r["match"]:
            _fail(f"renders-r5/{side}.png 实测与登记见证常量不符"
                  f"（R5 冻结渲染疑被改动）：{r}")
        results[side] = r
    return results


def _check_r14b_renders(r5_constants: dict, witness: dict) -> dict:
    """renders-r14b 四件 PNG 字节事实：
    - 两张 top 与 renders-r5 原件逐字节相同（sha 相同+bytes 相同双判定）；
    - 两张 bottom 实测均=d7284259 前缀、两板相同、!= r5 bottom（变更成立）；
    - 与 witness 登记 r14b bottom sha 交叉核对。
    """
    rendered = witness.get("renders", {})
    out = {"top_reuse": [], "bottom_new": []}
    for side in ("applied-top", "prep1-top"):
        path = CAL_DIR / "renders-r14b" / f"{side}.png"
        r = _check_png(path, r5_constants[side],
                       f"out/v3-tl2/calibration/renders-r14b/{side}.png")
        if not r["match"]:
            _fail(f"renders-r14b/{side}.png 实测 != renders-r5 原件见证常量"
                  f"（top 零变更声明被破坏）：{r}")
        if path.read_bytes() != (CAL_DIR / "renders-r5" / f"{side}.png").read_bytes():
            _fail(f"renders-r14b/{side}.png 与 renders-r5 原件逐字节比对不符"
                  f"（top 逐字节复用声明被破坏）")
        out["top_reuse"].append({
            "state_side": side,
            "path_rel": r["path_rel"],
            "source_rel": f"out/v3-tl2/calibration/renders-r5/{side}.png",
            "sha256_measured": r["sha256_measured"],
            "sha256_r5_source_witness": r5_constants[side],
            "byte_identical_reuse": True,
        })
    bottom_shas = []
    for side in ("applied-bottom", "prep1-bottom"):
        path = CAL_DIR / "renders-r14b" / f"{side}.png"
        measured = _sha(path)
        if not measured.startswith(R14B_BOTTOM_SHA_PREFIX):
            _fail(f"renders-r14b/{side}.png sha 前 8={measured[:8]} != 预期 "
                  f"{R14B_BOTTOM_SHA_PREFIX}（r14b bottom 见证锚不符，立即停止）")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        registered = (rendered.get(side.replace("-bottom", ""), {})
                      .get("sha256"))
        if registered != measured:
            _fail(f"render-witness-r14b.json renders.{side.replace('-bottom', '')}"
                  f".sha256 登记值与盘上实测不符（链自洽破坏，立即停止）")
        bottom_shas.append(measured)
        out["bottom_new"].append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "sha256_prefix_expected": R14B_BOTTOM_SHA_PREFIX,
            "sha256_witness_registered": registered,
            "witness_chain_match": True,
        })
    if len(set(bottom_shas)) != 1:
        _fail(f"r14b 两张 bottom 实测 sha 不相同（与 r5 既有两板相同事实口径"
              f"不一致）：{bottom_shas}")
    if bottom_shas[0] == r5_constants["applied-bottom"]:
        _fail("r14b bottom 实测 == r5 bottom（仪器变更未成立，与 round_nature "
              "矛盾，立即停止）")
    out["bottom_two_boards_identical"] = True
    out["bottom_differs_from_r5"] = True
    return out


def _check_framing_r14b(framing: dict, r5_constants: dict) -> dict:
    """render-framing-r14b 结构复核：轮次常量/板界断言/首试证伪登记/top 零变更声明。"""
    if framing.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-framing-r14b round_id_constant 不符："
              f"{framing.get('round_id_constant')}")
    if framing.get("date_constant") != DATE_CONSTANT:
        _fail("render-framing-r14b date_constant != 2026-09-08")
    if framing.get("kind") != "tl2_calibration_render_framing_r14b_preregistration":
        _fail("render-framing-r14b kind 不符")
    compose = framing.get("compose_and_crop_same_as_r5", {})
    expected = compose.get("expected_from_r5_derivation_log", {})
    bounds = {}
    for state in ("applied", "prep1"):
        got = expected.get(state, {}).get("board_px_bounds_full")
        if got != EXPECTED_BOARD_BOUNDS:
            _fail(f"framing-r14b {state} 板界断言 {got} != 逐字同口径期望 "
                  f"{EXPECTED_BOARD_BOUNDS}（与 r5 板界不一致，立即停止）")
        bounds[state] = list(got)
    falsified = framing.get("falsified_first_attempt_reference", {})
    if not str(falsified.get("framing_r14_sha256", "")).startswith(
            FALSIFIED_FRAMING_R14_SHA_PREFIX):
        _fail("framing-r14b 首试证伪登记 framing_r14_sha256 锚不符")
    if not str(falsified.get("witness_r14_sha256", "")).startswith(
            FALSIFIED_WITNESS_R14_SHA_PREFIX):
        _fail("framing-r14b 首试证伪登记 witness_r14_sha256 锚不符")
    top_decl = framing.get("top_zero_change", {})
    declared_top = top_decl.get("source_sha256", {})
    # top 零变更声明 vs r13-prep-record 见证常量（r5 top 原件）交叉核对；
    # 注：expected_from_r5_derivation_log 的 output_png_sha256_r5 为 r5
    # bottom 输出登记（bottom=本轮重渲染对象），不作 top 交叉源
    for side in ("applied-top", "prep1-top"):
        if declared_top.get(side) != r5_constants[side]:
            _fail(f"framing-r14b top 零变更声明 {side} 与 r5 见证常量不符："
                  f"{declared_top.get(side)}")
    return {
        "board_px_bounds_full": bounds,
        "round_id_constant": framing.get("round_id_constant"),
        "falsified_framing_r14_sha256": falsified.get("framing_r14_sha256"),
        "falsified_witness_r14_sha256": falsified.get("witness_r14_sha256"),
    }


def _check_witness_r14b(witness: dict, framing_sha: str,
                        r5_constants: dict) -> dict:
    """render-witness-r14b 结构复核：链自洽/配色语义/调色板断言/双链交叉。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")
    if witness.get("date_constant") != DATE_CONSTANT:
        _fail("render-witness-r14b date_constant != 2026-09-08")
    framing_ref = witness.get("framing", {})
    if framing_ref.get("sha256") != framing_sha:
        _fail("render-witness-r14b.framing.sha256 与盘上 framing 实测不符"
              "（链自洽破坏，立即停止）")
    if framing_ref.get("unchanged_during_render") is not True:
        _fail("render-witness-r14b.framing.unchanged_during_render 不为真")
    mapping = witness.get("color_mapping", {})
    ink = mapping.get("white_ink_drawings", {}).get("target_rgb")
    void = mapping.get("board_void_white", {}).get("target_rgb")
    if ink != ORANGE_TARGET_RGB:
        _fail(f"witness 白墨图元配色语义不符：{ink} != {ORANGE_TARGET_RGB}")
    if void != GREEN_TARGET_RGB:
        _fail(f"witness 板内空隙白配色语义不符：{void} != {GREEN_TARGET_RGB}")
    if CONCLUSION_VECTOR_MARKER not in str(witness.get("conclusion", "")):
        _fail("witness conclusion 缺白墨矢量标记（162 fill+4 stroke）")
    summary = witness.get("palette_assertion_summary", {})
    palette = {}
    for state in ("applied", "prep1"):
        item = summary.get(state, {})
        if item.get("assertions_pass") is not True:
            _fail(f"witness {state} palette_assertions_pass 不为真")
        palette[state] = {
            "orange_exact_count": item.get("orange_exact_count"),
            "green_exact_count": item.get("green_exact_count"),
            "white_reduction": item.get("white_reduction"),
            "white_pixel_count_r5": item.get("white_pixel_count_r5"),
            "white_pixel_count_r14b": item.get("white_pixel_count_r14b"),
        }
    if (palette["applied"] != palette["prep1"]
            or palette["applied"]["orange_exact_count"] is None):
        _fail(f"witness 两板调色板实测不一致或缺值：{palette}")
    r5_refs = (witness.get("r5_references", {})
               .get("renders_r5_png_sha256", {}))
    for side in RENDERS_SIDES:
        if r5_refs.get(side) != r5_constants[side]:
            _fail(f"witness r5_references.{side} 与 r13-prep-record 见证常量"
                  f"不符（双链交叉失败）：{r5_refs.get(side)}")
    copies = witness.get("top_zero_change_copies", {})
    for side in ("applied-top", "prep1-top"):
        item = copies.get(side, {})
        if (item.get("sha256") != r5_constants[side]
                or item.get("source_rel")
                != f"out/v3-tl2/calibration/renders-r5/{side}.png"):
            _fail(f"witness top_zero_change_copies.{side} 登记不符：{item}")
    falsified = witness.get("falsified_first_attempt_reference", {})
    if not str(falsified.get("framing_r14_sha256", "")).startswith(
            FALSIFIED_FRAMING_R14_SHA_PREFIX):
        _fail("witness 首试证伪登记 framing_r14_sha256 锚不符")
    det = witness.get("determinism_rerun_byte_identical", {})
    if det.get("applied") is not True or det.get("prep1") is not True:
        _fail("witness determinism_rerun_byte_identical 不为全真")
    return {
        "orange_target_rgb": list(ink),
        "green_target_rgb": list(void),
        "conclusion_vector_marker": CONCLUSION_VECTOR_MARKER,
        "palette": palette["applied"],
        "determinism_rerun_byte_identical": {"applied": True, "prep1": True},
    }


def _extract_candidate_target(dev_record: dict) -> dict:
    """从 round13-dev-record next_iteration_targets 取渲染侧消歧候选原文。

    按内容标记唯一定位（「渲染侧消歧」），实测索引回填并要求=[0]（用户
    拍板所引条目）；定位不到或歧义即停。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round13-dev-record next_iteration_targets 结构不符")
    idx = [i for i, t in enumerate(targets)
           if isinstance(t, str) and MARK_CANDIDATE_RENDER in t]
    if len(idx) != 1:
        _fail(f"next_iteration_targets 标记「{MARK_CANDIDATE_RENDER}」定位歧义：{idx}")
    if idx[0] != 0:
        _fail(f"渲染侧消歧候选实测索引={idx[0]} != 预注册给定 [0]")
    text = targets[idx[0]]
    if MARK_CANDIDATE_PREREG not in text:
        _fail("候选项缺预注册前置声明标记")
    if MARK_CANDIDATE_EXCEPTION not in text:
        _fail("候选项缺零仪器变更纪律例外声明标记")
    return {
        "index_zero_based": idx[0],
        "candidate_target": text,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance_sha: str, r13_record_sha: str, dev_record_sha: str,
                 protocol_sha: str, framing_sha: str, witness_sha: str,
                 r5_constants: dict, r14b_renders: dict, framing_probe: dict,
                 witness_probe: dict, quote: dict) -> dict:
    """构建 r14-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r14_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r14",
        "round_nature": (
            "纯仪器变更轮（bottom 视白色内容显式化配色；指引零字节复用 "
            "r13）：判读指引零字节复用 observation-guidance-r13.md（本轮"
            "唯一判读依据，零文本变更、无新指引文件——本轮恰零个指引侧变"
            "量），仪器侧单变量=bottom 渲染件更换（r5 白压平版→r14b 显式"
            "配色版：白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)，见"
            " instrument_change）；top 两张渲染自 renders-r5 逐字节复用（"
            "零变更）。此为 r5→r14b 首次渲染变更、零仪器变更纪律的显式例"
            "外声明（渲染侧单变量轮；预注册=render-framing-r14b.json "
            "7004b017 先于成图落盘，见 instrument_change.framing_witness）；"
            "执行 round13-dev-record next_iteration_targets[0]（渲染侧消"
            "歧，6b34c442 先验证），用户 2026-09-08 拍板路线 A（见 "
            "user_directive_note 与 hypothesis_test.preregistration_ref）；"
            "仪器变更史如实保留（首试 framing-r14 918672b4 预配色探针证伪"
            "作废、二试 framing-r14b 落地，见 instrument_change."
            "attempt_history）；GT/阈值/协议零变更（v1.2 沿用无新增版本）；"
            "r13 指引已在盘冻结、本轮零指引作者动作；盲读由编排侧在本记录"
            "之后以 12 次独立实例盲读执行"),
        "user_directive_note": (
            "用户 2026-09-08 拍板路线 A（渲染侧消歧的执行路线，本记录=首"
            "次落盘登记）：纯仪器侧单变量——bottom 视白色内容显式化配色"
            "（白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)），指引零"
            "字节复用 r13、不配发颜色图例（无图例条件即本轮检验设计的一部"
            "分；图例/指引侧配套留作混淆风险显现时的后续候选，见 "
            "hypothesis_test.reject_condition）；指引侧与协议侧零变更"),
        "instrument_change": {
            "declared": True,
            "exception_declaration": (
                "r5→r14b 首次渲染变更，属「零仪器变更」纪律的显式例外（渲"
                "染侧单变量轮）：变更范围=bottom 两张渲染件的白色内容显式"
                "化配色，仅此一项；层清单/dpi/裁剪/页几何与 r5 逐字同口径"
                "（板界断言逐字相同在案，本脚本 fail-closed 复核）；预注册"
                "=render-framing-r14b.json 先于成图落盘（7004b017）"),
            "renders": {
                "top_reuse": r14b_renders["top_reuse"],
                "bottom_new": r14b_renders["bottom_new"],
                "bottom_two_boards_identical": True,
                "bottom_two_boards_identical_note": (
                    "两板 bottom 实测 sha 相同（d7284259…）——与 r5 既有"
                    "两板 bottom 逐字节相同事实口径一致，照实登记，不含任"
                    "何 GT 含义"),
                "bottom_differs_from_r5": True,
                "bottom_differs_note": (
                    "r14b bottom（d7284259…）!= r5 bottom（f87f8fec…）——"
                    "仪器变更实测成立（本脚本 fail-closed 断言，不符即停）"),
                "top_reuse_note": (
                    "两张 top 自 renders-r5 逐字节复用（sha 相同+bytes 相"
                    "同双重判定，本脚本 fail-closed 实测；见证=与 r5 原件"
                    "哈希相同）——top 视零仪器变更"),
            },
            "change_declaration": (
                "bottom 视白色内容显式化：白墨图元（162 钻孔圆盘+4 椭圆轮"
                "廓，跨 B.Cu/B.Mask 焊盘绘制族）→橙 (255,165,0)；板内空隙"
                "白（铺铜 clearance 透出页底，非图元）→绿 (0,128,0)；其余"
                "层保持 kicad 原配色（B.Cu/B.Mask/Edge.Cuts 原配色；"
                "B.Silkscreen/B.Courtyard 自有图元=0，首试探针实证）；层清"
                "单/dpi/裁剪/页几何与 r5 逐字同口径（板界断言 [6074,355,"
                "7839,2119] 逐字相同在案，本脚本 fail-closed 复核）"),
            "white_dual_source_probe": {
                "white_ink_drawings": {
                    "target_rgb": witness_probe["orange_target_rgb"],
                    "semantics": (
                        "焊盘钻孔圆盘+椭圆焊盘轮廓白填充（B.Cu∪B.Mask 双族"
                        "共享绘制）"),
                    "count_note": (
                        "白墨矢量图元 162 fill+4 stroke（render-witness-"
                        "r14b.json conclusion 在案；本脚本 conclusion 标记"
                        " fail-closed 复核）"),
                },
                "board_void_white": {
                    "target_rgb": witness_probe["green_target_rgb"],
                    "semantics": (
                        "板界内空隙白（铺铜 clearance/翼瓣空隙/板框退让带/"
                        "基准环缝的基材露白；非图元、墨缺失）"),
                },
                "measured_palette": {
                    "orange_exact_count":
                        witness_probe["palette"]["orange_exact_count"],
                    "green_exact_count":
                        witness_probe["palette"]["green_exact_count"],
                    "white_reduction":
                        witness_probe["palette"]["white_reduction"],
                    "white_pixel_count_r5":
                        witness_probe["palette"]["white_pixel_count_r5"],
                    "white_pixel_count_r14b":
                        witness_probe["palette"]["white_pixel_count_r14b"],
                    "boards": "两板相同（结构探测实测登记）",
                    "source": (
                        "render-witness-r14b.json palette_assertion_summary"
                        "（本脚本结构探测取值，两板 assertions_pass 为真）"),
                },
            },
            "attempt_history": {
                "first_attempt_falsified": {
                    "framing": {
                        "path_rel":
                            "out/v3-tl2/calibration/render-framing-r14.json",
                        "sha256_prefix_expected":
                            FALSIFIED_FRAMING_R14_SHA_PREFIX,
                        "sha256_registered":
                            framing_probe["falsified_framing_r14_sha256"],
                    },
                    "witness": {
                        "path_rel":
                            "out/v3-tl2/calibration/render-witness-r14.json",
                        "sha256_prefix_expected":
                            FALSIFIED_WITNESS_R14_SHA_PREFIX,
                        "sha256_registered":
                            framing_probe["falsified_witness_r14_sha256"],
                    },
                    "falsification": (
                        "首试（framing-r14，918672b4）预配色 B.SilkS/B.CrtYd"
                        "被探针证伪：两板 bottom 该两层自有图元=0（单层导出"
                        "逐字节相同、板文件普查图元=0），overlay 应用 0 像素"
                        "，成图与 renders-r5 逐字节相同=零变更，如实作废保"
                        "留（作废件在盘未动，锚 918672b4/13fd1cab）"),
                },
                "second_attempt_landed": {
                    "basis": (
                        "二试 framing-r14b（7004b017）基于白色双来源探针（像"
                        "素+矢量双通道）：白墨矢量 162+4 图元（B.Cu∪B.Mask "
                        "双族共享）/板内空隙白=墨缺失（铺铜 clearance 透出"
                        "页底）——据此重定向配色：白墨图元→橙、板内空隙白"
                        "→绿"),
                    "framing_witness": {
                        "framing": {
                            "path_rel": (
                                "out/v3-tl2/calibration/"
                                "render-framing-r14b.json"),
                            "sha256_prefix_expected":
                                FRAMING_R14B_SHA_PREFIX,
                            "sha256_measured": framing_sha,
                            "match":
                                framing_sha.startswith(FRAMING_R14B_SHA_PREFIX),
                        },
                        "witness": {
                            "path_rel": (
                                "out/v3-tl2/calibration/"
                                "render-witness-r14b.json"),
                            "sha256_prefix_expected":
                                WITNESS_R14B_SHA_PREFIX,
                            "sha256_measured": witness_sha,
                            "match": witness_sha.startswith(
                                WITNESS_R14B_SHA_PREFIX),
                        },
                        "chain_note": (
                            "witness.framing.sha256 与盘上 framing 实测逐字"
                            "相同、unchanged_during_render 为真（本脚本"
                            " fail-closed 复核）"),
                    },
                },
            },
            "framing_probe": framing_probe,
            "witness_probe": witness_probe,
            "color_semantics_note": (
                "编排侧事实记录，不进指引：橙=钻孔/焊盘开窗墨；绿=板内空隙"
                "（墨缺失）；读者无图例（指引零变更）——本轮即检验「无图例"
                "下的新配色能否被 reader 语义化利用」，混淆风险如实预注册"
                "（见 hypothesis_test.reject_condition）"),
            "no_instrument_change": False,
        },
        "guidance_reuse": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r13.md",
            "sha256_prefix_expected": GUIDANCE_R13_SHA_PREFIX,
            "sha256_measured": guidance_sha,
            "match": guidance_sha.startswith(GUIDANCE_R13_SHA_PREFIX),
            "zero_byte_reuse": True,
            "role": (
                "本轮唯一判读依据，零字节复用（r13 指引落盘即冻结；本轮零"
                "指引作者动作、零文本变更、无新指引文件——本轮恰零个指引侧"
                "变量）"),
            "cross_check": (
                "r13-prep-record.json guidance.sha256 登记值与本脚本盘上实"
                "测逐字相符（链自洽，不符即停）"),
            "mechanical_naming_override": (
                "指引 §6 的 flag_id 前缀 R13T/R13B 与 reader_id reader-r13-*"
                " 在本轮由编排侧派发指令机械替换为 R14T/R14B 与 reader-r14-"
                "{top,bottom}-i{1,2,3}（命名属编排侧机械替换、派发层，非判"
                "据变更；判读实质判据零变更；指引本体零字节复用）；此覆盖如"
                "实入 run-record naming_constraints"),
        },
        "changed_variables": [
            {
                "id": "bottom-render-white-content-explicit-coloring",
                "target": (
                    "bottom 视渲染件（applied-bottom/prep1-bottom 两张；"
                    "renders-r5 白压平版→renders-r14b 显式配色版）"),
                "description": (
                    "bottom 视白色内容显式化配色：白墨图元（162 钻孔圆盘+4 "
                    "椭圆轮廓，跨 B.Cu/B.Mask 焊盘绘制族）→橙 (255,165,0)；"
                    "板内空隙白（铺铜 clearance 透出页底，非图元）→绿 "
                    "(0,128,0)；其余层保持 kicad 原配色；层清单/dpi/裁剪/"
                    "页几何与 r5 逐字同口径（板界断言 [6074,355,7839,2119] "
                    "逐字相同在案）"),
                "instrument_change": True,
                "attribution_channel": (
                    "bottom courtyard 收敛维持主通道（bottom courtyard 非"
                    "弃权旗数极差：基线 r13=0；支持=极差 ≤5 且 bottom 聚合"
                    "弃权率 ≤ r13 水平 10/11；拒绝=极差 >5 或聚合弃权率 "
                    ">10/11）；守门=top 渲染零变更下的方向性稳定记录"),
            }
        ],
        "manipulated_factor": (
            "唯一操纵因素=bottom 渲染件更换（r5 白压平版→r14b 显式配色版，"
            "见 instrument_change；r5→r14b 首次渲染变更、零仪器变更纪律例"
            "外已预注册）；指引/顶层（top）渲染/GT/阈值零变更"),
        "unchanged_components": [
            "判读指引：observation-guidance-r13.md 零字节复用（本轮唯一判"
            "读依据；无新指引文件，零文本变更，sha256 前 8=c28806e1 本脚本"
            " fail-closed 复核；本轮恰零个指引侧变量——§1 角色/§2 六类/§3 "
            "收窄判据/§3A 示例/§4 判据（含量化版 (i)(ii)(iii) 与对照说明）"
            "/§5 courtyard 说明/§6 输出 schema/§7 格式提示全部原文适用）",
            "top 渲染：renders-r14b 两张 top PNG 自 renders-r5 逐字节复用"
            "（applied-top=298bc620…、prep1-top=b2f84524…，实测=renders-r5"
            " 原件 sha 相同+bytes 相同，零重渲染）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r13 指引 §2 原文）",
            "§3 邻域框收窄判据与坐标口径（r13 指引 §3 原文）",
            "§3A 类别判据示例：全部逐字承 r13 指引（六类全部示例含示例 c；"
            "§3A 末尾对照说明原位保留）",
            "§4 全文：总原则、两条显式判据、量化版存在性判断一般判据 "
            "(i)(ii)(iii)、接触性判据、三路出口、confidence 定义、对照说明"
            "（r6/r8/r9/r12/r13 增补块）——r13 指引零字节复用，全部原文原位",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r13 指引 §6 原文；仅命名前缀编排侧机械替换，见 "
            "guidance_reuse.mechanical_naming_override）",
            "GT 集：零改动（gt-audit-r1 三候选全部关闭在案；GT 侧不再有候"
            "选，r9–r13 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作"
            "口径引用）",
            "评估协议：v1.2 沿用无新增版本（evaluation-protocol-v1.md 零字"
            "节保留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口径"
            "在图像空间完全一致、不做镜像换算；图像侧唯一变更=bottom 渲染"
            "件配色，见 instrument_change）",
            "机械替换仅：视角前缀 R13T/R13B→R14T/R14B；示例 reader-id "
            "reader-r13→reader-r14（派发层，非判据）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件即被操纵仪器（renders-r5 白压平版→"
            "renders-r14b 显式配色版）：白墨图元→橙、板内空隙白→绿、其余"
            "层 kicad 原配色不变（见 instrument_change）；bottom 视判读口"
            "径沿用 r4 指引原文不改（top/bottom 判读口径在图像空间完全一致"
            "、不做镜像换算——r13 指引零字节复用）；bottom 零旗标分母=0 时"
            "弃权率按 cal._ratio 先例=None 口径照旧；读者侧无颜色图例（指"
            "引零变更）——无图例下的新配色语义化利用即本轮检验设计"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R14 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注册"
                "，聚合口径全部如实并列、不二选一、不挑优（五条 items 照抄 "
                "r13-prep-record measurement_design.items 原文，仅本声明行"
                "轮次编号更新）"),
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
            "hypothesis_id": "r13-dev-record-candidate-0-render-disambiguate",
            "hypothesis": (
                "bottom 白色内容显式化（橙=墨图元、绿=空隙）在无图例条件下"
                "不破坏 r13 的收敛——三实例对蝶形/空隙形态仍一致判入系统性"
                "正常路径（其周期几何不因配色改变），且新配色被 reader 语义"
                "化利用（reading_notes 出现对橙/绿的颜色-语义归属表述）。"),
            "test_design": (
                "纯仪器变更轮：指引 r13 零字节复用（恰零个指引侧变量）+top "
                "渲染逐字节复用+GT/阈值零变更；唯一操纵=bottom 渲染件更换（"
                "r5 白压平版→r14b 显式配色版，r5→r14b 首次渲染变更、零仪器"
                "变更纪律例外已预注册）；协议 v1.2 沿用无新增版本；12 次盲"
                "读=4 视角格×3 实例；度量设计五条预注册（measurement_"
                "design）先于盲读冻结。"),
            "baseline_reference": {
                "round": "r13",
                "bottom_courtyard_non_abstain_by_instance": {
                    "bottom-i1": 0,
                    "bottom-i2": 0,
                    "bottom-i3": 0,
                },
                "bottom_courtyard_non_abstain_range": 0,
                "bottom_flags_by_instance": {
                    "bottom-i1": 3,
                    "bottom-i2": 4,
                    "bottom-i3": 4,
                },
                "bottom_abstain_rate_by_instance": {
                    "bottom-i1": 1.0,
                    "bottom-i2": 1.0,
                    "bottom-i3": 0.75,
                },
                "bottom_abstain_aggregate": "10/11 弃权（聚合）",
                "top_abstain_rate_by_instance": {
                    "top-i1": 0.7,
                    "top-i2": 0.857143,
                    "top-i3": 0.285714,
                },
                "note": (
                    "r13 bottom 实测基线（编排侧在案值；引用已落盘 run-"
                    "record 引用，数字仅入本编排侧 prep-record，不进指引文"
                    "件——指引零轮次结果数字）。r13 收敛实测：bottom "
                    "courtyard 非弃权 0/0/0（极差 0）=三实例一致走系统性正"
                    "常路径（r12 三发散裁决 18/0/0 经 §4 量化判据后归零在"
                    "案）；bottom 旗数 3/4/4、弃权率 1.0/1.0/0.75（聚合 "
                    "10/11 弃权）——弃权为主、非弃权零；top 弃权率 "
                    "0.7/0.857143/0.285714 供 top 方向性对照（top 渲染本轮"
                    "零变更）"),
                "sources": {
                    "r13_dev_record": {
                        "path_rel": (
                            "out/v3-tl2/calibration/round13-dev-record.json"),
                        "sha256": dev_record_sha,
                    },
                    "r13_run_record": {
                        "path_rel": (
                            "out/v3-tl2/calibration/calibration-run-r13.json"),
                        "sha256": RUN_RECORD_R13_SHA_CONSTANT,
                        "note": (
                            "编排侧 prep 时实测引用常量（本脚本零接触该文"
                            "件，不读 calibration-run-*）"),
                    },
                },
            },
            "support_condition": (
                "bottom courtyard 非弃权旗数极差 ≤5（收敛维持）且 bottom "
                "聚合弃权率 ≤ r13 水平（≤10/11，即配色未引发混淆性弃权上"
                "升），则仪器变更无副作用获支持。"),
            "reject_condition": (
                "bottom courtyard 非弃权旗数极差 >5（裁决重新发散）或 "
                "bottom 聚合弃权率 > r13（10/11，配色引发混淆），则如实记"
                "录：前者=操作化判据对新配色不稳健；后者=无图例配色引发混"
                "淆，指向图例/指引侧配套候选。"),
            "null_result_note": (
                "结果无论方向如实；描述性边界（≤5 / ≤10-11）为本轮预注册描"
                "述性边界、非 APR-0011 门（门照常独立计算，互不凌驾）；跨"
                "轮实例群混杂照旧；「正确测出无效同样是有效证据」；bottom "
                "零旗标分母=0 时弃权率=None 口径照旧（cal._ratio 先例）。"),
            "declaration": (
                "bottom 视角层 courtyard 类非弃权旗数极差（本轮假设主通道）"
                "按逐实例如实计数（bottom-i1/i2/i3 三分列）；bottom 聚合弃"
                "权率并列如实（对照 r13=10/11）；top 视角全类照常如实记录"
                "（top 渲染零变更、方向性对照）；跨实例=同轮同指引（v1.2 规"
                "约沿用），跨轮对比=方向性（实例群混杂照旧）；「正确测出无"
                "效同样是有效证据」。"),
            "preregistered_criteria_quote": {
                "candidate_0_target": quote["candidate_target"],
                "user_directive_2026_09_08": (
                    "用户拍板路线 A（2026-09-08）：渲染侧消歧执行纯仪器侧单"
                    "变量——bottom 视白色内容显式化配色（白墨图元→橙、板内"
                    "空隙白→绿），指引零字节复用 r13、不配发颜色图例（无图"
                    "例条件即本轮检验设计；图例/指引侧配套为混淆显现时的后"
                    "续候选）"),
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round13-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R13_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": [quote["index_zero_based"]],
                "note": (
                    "引用原文逐字摘录（措辞按文件原文，未改写）：索引 [0]="
                    "top 视接触性弃权高企的后续候选（渲染侧消歧…）——本轮"
                    "按用户路线 A 执行其渲染侧单变量（bottom 白色内容显式化"
                    "；候选项原文所述图例配套本轮不执行，留作后续候选）。先"
                    "于 R14 盲读落盘预注册（本记录=预注册件）。"),
            },
            "primary_channel_metric": (
                "bottom 视角层 courtyard 类非弃权旗数极差（收敛维持性；基线"
                " r13=0）；bottom 聚合弃权率对照 r13=10/11 并列（混淆通道要"
                "件）；执行由编排侧在 close 包执行。"),
            "metric_lesson_application": (
                "r9–r13 教训链延续（产量计数+弃权率互补、逐实例如实分列不聚"
                "合掩盖、r13 §4 量化判据使 bottom 三裁决 18/0/0→0/0/0 收敛"
                "在案）；本轮=仪器侧处置首验（区别于 r13 指引侧、r10 采样"
                "侧、r11–r12 工具侧处置）；全部预注册于本记录、先于盲读冻"
                "结，不追溯改判既往轮次（r8–r13 字母裁决维持不变）。"),
            "secondary_observation": (
                "颜色语义化利用（≥2/3 bottom 实例 reading_notes 出现对橙/"
                "绿的颜色-语义归属表述=新配色可用性证据；逐实例 substring "
                "检索「橙|绿|颜色」如实登记，无期望）；黑点类弃权是否延续"
                "（r13 一致弃权的形态在新配色下走向，如实记录零期望）；top "
                "视方向性稳定记录（top 渲染零变更）；courtyard 密集旗被动"
                "追踪延续（GT/阈值零改动；不得为提高命中调阈值；无期望）。"),
        },
        "attribution_plan": {
            "declaration": (
                "本轮恰一个仪器侧操纵变量（bottom 渲染件更换）、检验恰一个"
                "假设（round13-dev-record next_iteration_targets[0] 渲染侧"
                "消歧；hypothesis_id=r13-dev-record-candidate-0-render-"
                "disambiguate）；归因分层：本轮检验「bottom 白色内容歧义」"
                "病根的仪器侧处置首验（区别于 r13 指引侧、r10 采样侧处置）；"
                "跨轮对比（vs r12–r13）为方向性（实例群混杂照旧）"),
            "primary_channel": {
                "change": (
                    "bottom-render-white-content-explicit-coloring（仪器侧"
                    "唯一操纵；非指引/GT/阈值/top 渲染变更）"),
                "metric": (
                    "bottom 视角层 courtyard 类非弃权旗数极差（收敛维持性；"
                    "预注册描述性边界：≤5 支持、>5 拒绝）；bottom 聚合弃权"
                    "率对照 r13=10/11 并列（>10/11=混淆拒绝通道）"),
                "support": (
                    "极差 ≤5 且 bottom 聚合弃权率 ≤10/11 → 仪器变更无副作"
                    "用（收敛维持）获支持"),
                "reject": (
                    "极差 >5（裁决重新发散）或聚合弃权率 >10/11（无图例配"
                    "色引发混淆）→ 如实记录；后者指向图例/指引侧配套候选"),
            },
            "guard_channel": {
                "metric": (
                    "top 视角非弃权旗标 frame_box_pct 几何门（面积比出局条"
                    "目；top 渲染零变更）"),
                "requirement": (
                    "§3 收窄判据零变更（r13 指引零字节复用），非弃权框仍须"
                    "满足；几何门面积比出局条目无回升"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角层"
                "三分列聚合+GT 匹配双口径+联合门代表配置/范围并列；APR-0011 "
                "阈值零改动）；bottom GT 无源=bottom 旗标与 GT 匹配应为空"
                "（结构性在案，不影响收敛计数口径）；归因分组逻辑由编排侧在"
                " close 包执行；本指引零 GT、零轮次结果数字（基线数字仅入本"
                "编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "本轮纯仪器变更轮无任何判据文本变更（指引 r13 零字节复用、无新"
            "指引文件）：§1–§7 全部原文适用，不降低任何存在性、归类、定位"
            "或报告的责任门槛；≤5 / ≤10-11 描述性边界只用于本轮假设检验方"
            "向归因，不触碰 APR-0011 门（gt_recall≥0.75/seed_match_rate"
            "≥0.5/abstain_rate≤0.5）与任何阈值常量（CONTAINMENT_MIN/"
            "AREA_RATIO_MAX，只作口径引用）；渲染配色变更只作用于图像可读"
            "性（白墨图元/空隙白的颜色区分），不改变任何图元几何、层清单/"
            "dpi/裁剪/页几何（板界断言逐字同口径）、不改 GT、不构成任何门"
            "的放宽或收紧——门照常独立计算"),
        "no_instrument_change": False,
        "pre_round_review": {
            "declaration": (
                "本轮无用户拍板的额外评审（区别于 r13 轮的 D1/D2/D3 诊断评"
                "审）；本轮轮前诊断=渲染探针链（首试 framing-r14 预配色探"
                "针证伪+白色双来源探针），全部为仪器侧事实、已入 "
                "instrument_change.attempt_history 与 render-framing-r14b."
                "json/render-witness-r14b.json（7004b017/b63771f9，本脚本"
                " fail-closed 复核）；探针事实仅入本记录、不进指引、不进任"
                "何 reader 上下文"),
        },
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "amendment_version": "v1.2（沿用，无新增版本）",
            "amendment_mode": (
                "无新增修订：v1.2 原文适用（纯 Read 直读规约自 r12 起随派发"
                "指令生效，本轮照旧）；v1.1 的 n=3 多实例与聚合口径全部沿"
                "用；本轮单变量=仪器侧恰一项，协议侧零变更"),
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视角"
                "层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径并"
                "列、联合门代表配置+实例间范围并列（measurement_design 五"
                "条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派发"
                "指令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/放"
                "大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查看原"
                "图（同一原图可重复查看）」——仪器行为钉住；属派发层，读者"
                "上下文=指引+单张 PNG+派发指令（含规约条款），零 GT；不影"
                "响判读语义——分类判据零变更，仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11/r12/r13 轮同口径在案登记，本脚"
                    "本 fail-closed 在盘+哈希复核）；本轮无新增版本、不新建"
                    "协议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；实例上下文=指引（observation-guidance-r13."
                "md 零字节复用）+单张 PNG+派发命名指令（含 v1.2 工具行为规"
                "约硬性条款），零 GT、零颜色图例（无图例条件即本轮检验设"
                "计）、零诊断/探针内容；两波次串行保序（同一实例先 applied "
                "后 prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r14-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R14T/R14B（由 r13 指引 §6 的 R13T/R13B 机械替换，派发指令"
                "给出——指引本体零字节复用，替换属派发层覆盖，非判据变更）；"
                "实例间编号独立，同实例跨板连续"),
            "motivation_note": (
                "沿用声明（无新增动机条目）：v1.2 于 r12 轮以追加式落定（工"
                "具异质性已由规约钉住）；本轮无新增协议条款"),
            "scope_note": (
                "本轮协议侧零变更（v1.2 沿用声明，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic+逐字节比对，零内容判读、零像素读取）、ground-truth-*、"
            "reader-raw-*、calibration-run-*、derivation-log-*、任何 "
            "compare/评估产物；本脚本只读输入=observation-guidance-r13.md"
            "（本轮唯一判读依据；c28806e1 锚 fail-closed，零写入）、r13-"
            "prep-record.json（取 renders-r5 PNG 见证常量与链交叉核对，"
            "hash 锚=b1c0d8b5 先验证）、round13-dev-record.json（仅读取 "
            "round_id、next_iteration_targets（标记定位 [0]）字段取预注册"
            "原文摘录，hash 锚=6b34c442 先验证）、render-framing-r14b.json"
            "（7004b017 锚 fail-closed；板界/首试证伪/top 零变更登记复核）、"
            "render-witness-r14b.json（b63771f9 锚 fail-closed；配色语义/"
            "调色板断言/双链交叉复核）、evaluation-protocol-v1.md（仅在盘+"
            "哈希复核，锚=22dc7337）；renders-r5/renders-r14b PNG 仅哈希+"
            "magic+逐字节比对；observation-guidance-r13.md 本脚本只读（仅"
            "哈希），零写入；reader 派发（后续编排侧执行）上下文=observation-"
            "guidance-r13.md+单张 PNG+派发指令（R14T/R14B 前缀、reader-r14-"
            "{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬性条款），零 GT、零"
            "颜色图例（无图例条件即本轮检验设计）、零其他盘上文件；跨实例/"
            "跨视角禁止交流（12 次盲读相互独立、不得交换判读信息——独立性"
            "是多实例协议的前提）。"),
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R13, R13_PREP_RECORD, R13_DEV_RECORD, FRAMING_R14B,
                 WITNESS_R14B, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r13_record = json.loads(R13_PREP_RECORD.read_text(encoding="utf-8"))
    dev_record = json.loads(R13_DEV_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R14B.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    r13_record_sha = _sha(R13_PREP_RECORD)
    dev_record_sha = _sha(R13_DEV_RECORD)
    framing_sha = _sha(FRAMING_R14B)
    witness_sha = _sha(WITNESS_R14B)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    if not r13_record_sha.startswith(R13_PREP_RECORD_SHA_PREFIX):
        _fail(f"r13-prep-record sha 前 8={r13_record_sha[:8]} != 预期 "
              f"{R13_PREP_RECORD_SHA_PREFIX}（见证来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R13_DEV_RECORD_SHA_PREFIX):
        _fail(f"round13-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R13_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if not framing_sha.startswith(FRAMING_R14B_SHA_PREFIX):
        _fail(f"render-framing-r14b sha 前 8={framing_sha[:8]} != 预期 "
              f"{FRAMING_R14B_SHA_PREFIX}（仪器预注册锚不符，立即停止）")
    if not witness_sha.startswith(WITNESS_R14B_SHA_PREFIX):
        _fail(f"render-witness-r14b sha 前 8={witness_sha[:8]} != 预期 "
              f"{WITNESS_R14B_SHA_PREFIX}（仪器见证锚不符，立即停止）")
    if not protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX):
        _fail(f"evaluation-protocol-v1.md sha 前 8={protocol_sha[:8]} != 预期 "
              f"{EVAL_PROTOCOL_V1_SHA_PREFIX}（协议原文保留载体疑被改动，立"
              f"即停止）")
    if r13_record.get("schema_version") != "3.0":
        _fail("r13-prep-record schema_version != 3.0（结构漂移）")
    if r13_record.get("kind") != "tl2_calibration_r13_prep_record":
        _fail("r13-prep-record kind 不符（结构漂移）")
    if r13_record.get("round_id_constant") != "2026-09-08-r13":
        _fail("r13-prep-record round_id_constant != 2026-09-08-r13（结构漂移）")
    if dev_record.get("round_id") != "2026-09-08-r13":
        _fail("round13-dev-record round_id != 2026-09-08-r13（结构漂移）")

    # ---- r13 指引零字节复核（本轮唯一判读依据；只读）----
    guidance_sha = _sha(GUIDANCE_R13)
    if not guidance_sha.startswith(GUIDANCE_R13_SHA_PREFIX):
        _fail(f"r13 指引 sha 前 8={guidance_sha[:8]} != 预期 "
              f"{GUIDANCE_R13_SHA_PREFIX}（本轮唯一判读依据疑被改动，立即停"
              f"止）")
    registered_guidance_sha = (r13_record.get("guidance") or {}).get("sha256")
    if registered_guidance_sha != guidance_sha:
        _fail("r13-prep-record guidance.sha256 登记值与盘上实测不符（链自洽"
              "破坏，立即停止）")

    # ---- 见证常量与仪器链复核 ----
    r5_constants = _load_r5_png_witness_constants(r13_record)
    _check_r5_renders(r5_constants)
    r14b_renders = _check_r14b_renders(r5_constants, witness)
    framing_probe = _check_framing_r14b(framing, r5_constants)
    witness_probe = _check_witness_r14b(witness, framing_sha, r5_constants)
    quote = _extract_candidate_target(dev_record)

    # ---- 记录构建 + byte-exact 自证 ----
    record = build_record(guidance_sha=guidance_sha,
                          r13_record_sha=r13_record_sha,
                          dev_record_sha=dev_record_sha,
                          protocol_sha=protocol_sha,
                          framing_sha=framing_sha,
                          witness_sha=witness_sha,
                          r5_constants=r5_constants,
                          r14b_renders=r14b_renders,
                          framing_probe=framing_probe,
                          witness_probe=witness_probe,
                          quote=quote)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(guidance_sha=guidance_sha,
                           r13_record_sha=r13_record_sha,
                           dev_record_sha=dev_record_sha,
                           protocol_sha=protocol_sha,
                           framing_sha=framing_sha,
                           witness_sha=witness_sha,
                           r5_constants=r5_constants,
                           r14b_renders=r14b_renders,
                           framing_probe=framing_probe,
                           witness_probe=witness_probe,
                           quote=quote)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r14-prep-record")

    # ---- 顶层键集合与 r13-prep-record 镜像断言（文档化差异：两换零移除余）----
    expected_keys = (set(r13_record.keys())
                     - set(TOP_LEVEL_KEY_DELTA_REMOVE)
                     | set(TOP_LEVEL_KEY_DELTA_ADD))
    if set(record.keys()) != expected_keys:
        _fail(f"r14-prep-record 顶层键集合与 r13-prep-record 镜像（文档化差"
              f"异：-{TOP_LEVEL_KEY_DELTA_REMOVE} +{TOP_LEVEL_KEY_DELTA_ADD}）"
              f"不符：多={sorted(set(record.keys()) - expected_keys)}，"
              f"少={sorted(expected_keys - set(record.keys()))}")
    ht_expected = (set(r13_record["hypothesis_test"].keys())
                   - set(HT_KEY_DELTA_REMOVE)
                   | set(HT_KEY_DELTA_ADD))
    if set(record["hypothesis_test"].keys()) != ht_expected:
        _fail(f"hypothesis_test 键集合镜像（文档化差异："
              f"-{HT_KEY_DELTA_REMOVE} +{HT_KEY_DELTA_ADD}）不符："
              f"多={sorted(set(record['hypothesis_test'].keys()) - ht_expected)}，"
              f"少={sorted(ht_expected - set(record['hypothesis_test'].keys()))}")

    # ---- 结构自证：changed_variables 恰一项、度量设计五条、恒 False 位 ----
    if len(record["changed_variables"]) != 1:
        _fail("r14 恰一项变更变量：changed_variables 必须恰 1 项")
    if record["instrument_change"]["declared"] is not True:
        _fail("instrument_change.declared 必须为真（仪器变更轮）")
    if record["instrument_change"]["no_instrument_change"] is not False:
        _fail("instrument_change.no_instrument_change 必须为 False")
    if record["no_instrument_change"] is not False:
        _fail("顶层 no_instrument_change 必须为 False（本轮=仪器变更轮，如"
              "实登记）")
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
            print(f"[r14-prep] 重跑自证：r14-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r14-prep] 工件 sha256：r14-prep-record.json="
                  f"{hashing.sha256_bytes(existing)}")
            print(f"[r14-prep] r13 指引零字节复核（收工侧随编排另验）："
                  f"observation-guidance-r13.md={guidance_sha}")
            return
        _fail("r14-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r14-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r14-prep] 验证通过：r13 指引零字节锚 {GUIDANCE_R13_SHA_PREFIX} OK"
          f"（只读，零写入）；r13-prep-record 见证来源锚 "
          f"{R13_PREP_RECORD_SHA_PREFIX} OK；dev-record 锚 "
          f"{R13_DEV_RECORD_SHA_PREFIX} OK（渲染侧消歧候选=索引 "
          f"[{quote['index_zero_based']}] 原文摘录在案）；framing-r14b 锚 "
          f"{FRAMING_R14B_SHA_PREFIX} OK（板界断言两板逐字=[6074,355,7839,"
          f"2119]；首试证伪登记 {FALSIFIED_FRAMING_R14_SHA_PREFIX} 在案）；"
          f"witness-r14b 锚 {WITNESS_R14B_SHA_PREFIX} OK（橙/绿配色语义+两"
          f"板 assertions_pass+链自洽+双链交叉）；evaluation-protocol-v1 在"
          f"盘锚 {EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print(f"[r14-prep] 仪器变更自证：top 两张自 renders-r5 逐字节复用（sha+"
          f"bytes 双判定）；bottom 两张实测={r14b_renders['bottom_new'][0]['sha256_measured'][:8]}"
          f"（两板相同、!= r5 bottom=变更成立）；首试 framing-r14 "
          f"{FALSIFIED_FRAMING_R14_SHA_PREFIX} 证伪史如实保留")
    print(f"[r14-prep] 纯仪器变更轮自证：changed_variables 恰 1 项（bottom "
          f"渲染件）；指引侧变量=0；顶层键镜像 r13（文档化差异：-guidance "
          f"+guidance_reuse、-renders_reuse +instrument_change）；"
          f"hypothesis_test 键镜像 r13 零差异（13 键）；度量设计五条照抄预"
          f"注册先于盲读冻结")
    print(f"[r14-prep] 写出：r14-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致）")


if __name__ == "__main__":
    main()
