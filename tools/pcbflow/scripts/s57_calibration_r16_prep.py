#!/usr/bin/env python
"""CAL-R16-PREP：R16 同指引重复轮预备包（只新建一个文件：
out/v3-tl2/calibration/r16-prep-record.json；scripts/s57_calibration_r16_
prep.py 为生成器本体。datasets/ 与 out/ 既有文件只读、零改动；
observation-guidance-r15.md 零字节不动——本轮**不新建指引文件**）。

R16 轮性质（预注册，非事后）：**同指引重复轮（r10 先例）**——唯一操纵
因子=reader 实例群抽样（12 派次全部重抽）。执行 round15-dev-record
next_iteration_targets[0]（R16 第一候选=同指引重复轮），用户 2026-09-08
「继续迭代到收敛」既定指令批准。归因目的：消解 r15 判据 (iii) 违约
（top 全旗聚合弃权 25/29=0.862 > run-r14 双侧复算基线 18/24=0.75）的
两候选解释——(α) 跨轮实例群漂移（r10 实证的主因通道）vs (β) §5A 仪
器注记的全局弃权致敏（指引侧遗留效应）。

零变更声明（三条通道全在案锚定，fail-closed）：
  - 指引零变更：observation-guidance-r15.md 字节复用（d5babc93 实测
    锚；本脚本无任何指引写路径、零编辑、零机械变换）。
  - 渲染零变更：renders-r14b 四 PNG sha256_file 实测与
    render-witness-r14b.json（b63771f9）登记值逐字比对（即 r14/r15
    轮盲读所用同一批文件）。
  - 协议/GT/阈值冻结：evaluation-protocol-v1.md（22dc7337）在盘复核；
    APR-0011 与 CONTAINMENT_MIN/AREA_RATIO_MAX 零改动（只作口径引用）。

判据冻结值锚定（calibration-run-r15.json hypothesis_test.measurement，
0c37c1cb 锚 fail-closed）：top 25/29=0.862069、bottom 11/13=0.846154、
基线 18/24=0.75（run-r14 内嵌实例记录双侧复算在案值）、crit1/crit2=
True、crit3=False——hypothesis_test 预注册判据文本中的数值与在案实测
逐一对应，防预注册文本漂移。

hypothesis_test=任务预注册归因判据**逐字**（脚本内以 HYPOTHESIS_TEST_
TEXT 原文常量嵌入；断言链=文本→json.loads→HYPOTHESIS_TEST→record 字
段，三层相等，不得改数值或口径）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-08 / 2026-09-08-r16）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-* /
reader-raw-* / derivation-log-* / 任何 compare 产物；run-r15 仅读
hypothesis_test.measurement 数值字段做冻结值锚（不读其 GT 匹配与逐旗
明细内容入记录）；无 git；r15 指引只读零写入；记录内零 GT、零期望数
量/分布/坐标；指引内零轮次结果数字（基线数字仅入本编排侧记录）；
r16-prep-record.json 落盘=canonical JSON（hashing.canonical_json_bytes）
+同参重建两次逐字节一致自证+防覆写守卫（已存在且重建字节不同→FAIL，
相同→幂等零覆写）+落盘后回读验字节。

用法：python scripts/s57_calibration_r16_prep.py
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
R15_PREP_RECORD = CAL_DIR / "r15-prep-record.json"
R15_DEV_RECORD = CAL_DIR / "round15-dev-record.json"
RUN_R15 = CAL_DIR / "calibration-run-r15.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r16-prep-record.json"

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r16"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R15_SHA_PREFIX = "d5babc93"
R15_PREP_RECORD_SHA_PREFIX = "4c6cd919"
R15_DEV_RECORD_SHA_PREFIX = "e981897c"
RUN_R15_SHA_PREFIX = "0c37c1cb"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 渲染零变更见证（render-witness-r14b.json 登记值；四 PNG 实测逐一
#: fail-closed 比对。bottom=renders.{applied,prep1}.sha256；
#: top=top_zero_change_copies.{applied-top,prep1-top}.sha256）
RENDERS_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
R14B_BOTTOM_SHA_PREFIX = "d7284259"

#: round15-dev-record next_iteration_targets 候选项内容定位标记
#: （「同指引重复轮」在 targets[0]/[2] 双命中、定位歧义；「R16 第一候
#:  选」为 targets[0] 专属措辞，唯一命中）
MARK_CANDIDATE = "R16 第一候选"

# ---------------------------------------------------------------------------
# 预注册归因判据（逐字；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "r15-dev-record-candidate-0-same-guidance-repeat",
  "hypothesis": "r15 判据 (iii) 违约（top 全旗聚合弃权 25/29=0.862>run-r14 基线 18/24=0.75）存在两候选解释：(α) 跨轮实例群漂移（r10 实证的主因通道）——同指引重抽实例群后 top 应回到历史水平附近；(β) §5A 仪器注记的全局弃权致敏（指引侧遗留效应）——同指引下 top 应持续高位。R16=零变更重复轮（唯一操纵因子=实例群抽样），以 top 聚合弃权率落点做归因裁决。",
  "adjudication": {
    "letter_supported": "(a) top 全旗聚合弃权率 ≤ 0.75（=run-r14 双侧复算基线，冻结值）——漂移解释 (α) 成立，r15 (iii) 违约记为实例群噪声，r15 图例的 bottom 主通道效应（(i)(ii)）得以保留确认",
    "letter_reject": "(b) top 全旗聚合弃权率 ≥ 0.862（=r15 实测水平，冻结值）——致敏解释 (β) 升级，§5A 指引侧遗留效应成立，后续须指引侧再处置（预注册后执行）",
    "letter_inconclusive": "(c) 0.75 < top < 0.862（两轮值之间=两候选解释均不排斥）——字母=inconclusive（development 域如实记录），归因悬置，机制观察加权",
    "side_observation_separate": "bottom 主通道维持性单列（不影响字母）：bottom courtyard 旗与非弃权计数、bottom 全旗聚合弃权率对照 r15 的 11/13=0.846 与 0/0/0——若 bottom 恶化=图例效应本身实例群敏感，如实记录；黑点类与绿区语义化方式延续观察",
    "metric_lesson_separate": "两轮制归因的分辨力有限（(c) 带非空）；若 inconclusive，第三点须靠分层（同实例群双跑）或判据侧处置，不得以连续 inconclusive 反复消耗盲读",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量分列、互不凌驾（门阈值零改动）；非门阈值、非期望清单"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

#: 判据冻结值锚（=calibration-run-r15.json hypothesis_test.measurement
#: 在案实测；不符即停——防预注册文本与在案事实漂移）
CRITERION_ANCHOR_TOP_COUNT = 25
CRITERION_ANCHOR_TOP_FLAGS = 29
CRITERION_ANCHOR_TOP_RATE = 0.862069
CRITERION_ANCHOR_BOTTOM_COUNT = 11
CRITERION_ANCHOR_BOTTOM_FLAGS = 13
CRITERION_ANCHOR_BOTTOM_RATE = 0.846154
CRITERION_ANCHOR_BASELINE_LIVE = "18/24"
CRITERION_ANCHOR_BASELINE_VALUE = 0.75


def _fail(msg: str) -> None:
    print(f"[r16-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def check_guidance_zero_write() -> dict:
    """指引基座复核：只读哈希+字节数，零写入（本函数无写路径）。"""
    if not GUIDANCE_R15.exists():
        _fail(f"缺失：{GUIDANCE_R15}")
    sha = _sha(GUIDANCE_R15)
    if not sha.startswith(GUIDANCE_R15_SHA_PREFIX):
        _fail(f"observation-guidance-r15.md sha 前 8={sha[:8]} != 预期 "
              f"{GUIDANCE_R15_SHA_PREFIX}（判读指引基座疑被改动，立即停止）")
    return {
        "path_rel": "out/v3-tl2/calibration/observation-guidance-r15.md",
        "sha256_measured": sha,
        "byte_size": GUIDANCE_R15.stat().st_size,
        "zero_write": True,
    }


def check_renders_byte_reuse(witness: dict) -> list[dict]:
    """渲染零变更实测：四 PNG magic+sha256_file 实测 vs witness 登记值。"""
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


def probe_witness(witness: dict) -> None:
    """render-witness-r14b 结构最小校验（kind/轮次/日期锚）。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")
    if witness.get("date_constant") != DATE_CONSTANT:
        _fail("render-witness-r14b date_constant != 2026-09-08")


def extract_candidate(dev_record: dict, dev_record_sha: str) -> dict:
    """round15-dev-record next_iteration_targets：按标记唯一定位并要求=[0]。"""
    if dev_record.get("round_id") != "2026-09-08-r15":
        _fail(f"round15-dev-record round_id 不符：{dev_record.get('round_id')}")
    if dev_record.get("schema_version") != "3.0":
        _fail("round15-dev-record schema_version != 3.0（结构漂移）")
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or not targets:
        _fail("round15-dev-record next_iteration_targets 结构不符")
    idx = [i for i, t in enumerate(targets)
           if isinstance(t, str) and MARK_CANDIDATE in t]
    if len(idx) != 1:
        _fail(f"next_iteration_targets 标记「{MARK_CANDIDATE}」定位歧义："
              f"{idx}")
    if idx[0] != 0:
        _fail(f"同指引重复轮候选实测索引={idx[0]} != 授权给定 [0]")
    return {
        "path_rel": "out/v3-tl2/calibration/round15-dev-record.json",
        "sha256_measured": dev_record_sha,
        "field": "next_iteration_targets",
        "item_indices_zero_based": [idx[0]],
        "candidate_quote": targets[idx[0]],
    }


def anchor_run15_criterion(run15: dict) -> dict:
    """calibration-run-r15 hypothesis_test.measurement 数值锚定（fail-closed）。

    只读取判据冻结值字段（零 GT 匹配/逐旗明细内容入记录）。
    """
    ht = run15.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r15 hypothesis_test 结构不符")
    if ht.get("hypothesis_id") != "r14-dev-record-candidate-0-guidance-color-legend":
        _fail("calibration-run-r15 hypothesis_test.hypothesis_id 不符")
    m = ht.get("measurement")
    if not isinstance(m, dict):
        _fail("calibration-run-r15 hypothesis_test.measurement 结构不符")
    expect = {
        "top_abstain_count_r15": CRITERION_ANCHOR_TOP_COUNT,
        "top_abstain_flags_r15": CRITERION_ANCHOR_TOP_FLAGS,
        "top_abstain_rate_r15": CRITERION_ANCHOR_TOP_RATE,
        "bottom_abstain_count_r15": CRITERION_ANCHOR_BOTTOM_COUNT,
        "bottom_abstain_flags_r15": CRITERION_ANCHOR_BOTTOM_FLAGS,
        "bottom_abstain_rate_r15": CRITERION_ANCHOR_BOTTOM_RATE,
        "top_abstain_rate_r14_baseline_value": CRITERION_ANCHOR_BASELINE_VALUE,
    }
    for key, want in expect.items():
        got = m.get(key)
        if got != want:
            _fail(f"判据冻结值锚不符：{key}={got!r} != {want!r}（立即停止）")
    live = (m.get("baseline_cross_check", {}) or {}).get(
        "r14_top_abstain_aggregate_live")
    if live != CRITERION_ANCHOR_BASELINE_LIVE:
        _fail(f"基线在案值不符：r14_top_abstain_aggregate_live={live!r} != "
              f"{CRITERION_ANCHOR_BASELINE_LIVE!r}（立即停止）")
    for key, want in (("crit1_bottom_courtyard_non_abstain_all_zero", True),
                      ("crit2_bottom_abstain_le_10_11", True),
                      ("crit3_top_abstain_le_r14_baseline", False)):
        if m.get(key) is not want:
            _fail(f"三分判据布尔锚不符：{key}={m.get(key)!r} != {want!r}")
    return {
        "top_abstain_r15": (f"{CRITERION_ANCHOR_TOP_COUNT}/"
                            f"{CRITERION_ANCHOR_TOP_FLAGS}="
                            f"{CRITERION_ANCHOR_TOP_RATE}"),
        "bottom_abstain_r15": (f"{CRITERION_ANCHOR_BOTTOM_COUNT}/"
                               f"{CRITERION_ANCHOR_BOTTOM_FLAGS}="
                               f"{CRITERION_ANCHOR_BOTTOM_RATE}"),
        "r14_top_baseline": (f"{CRITERION_ANCHOR_BASELINE_LIVE}="
                             f"{CRITERION_ANCHOR_BASELINE_VALUE}"),
        "crit1": True, "crit2": True, "crit3": False,
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance15_sha: str, guidance15_bytes_n: int,
                 r15_record_sha: str, dev_ref: dict, run15_sha: str,
                 witness_sha: str, protocol_sha: str,
                 png_checks: list[dict]) -> dict:
    """构建 r16-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r16_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r16",
        "round_nature": (
            "同指引重复轮（r10 先例，第十六轮）：唯一操纵因子=reader 实例"
            "群抽样（12 派次全部重抽）；判读指引=observation-guidance-r15."
            "md 字节复用（d5babc93 实测锚；本脚本零写入、零编辑、零机械变"
            "换——本轮不新建指引文件）；渲染零变更=renders-r14b 四图字节"
            "复用（四 PNG sha256_file 实测与 render-witness-r14b.json 登记值"
            " fail-closed 比对一致，即 r14/r15 轮盲读所用同一批文件，见 "
            "instrument_change）；GT/阈值/协议零变更（v1.1+v1.2 维持）；执"
            "行 round15-dev-record next_iteration_targets[0]（R16 第一候选="
            "同指引重复轮，实测链见 guidance_reuse.chain_anchors."
            "round15_dev_record_authorization），用户 2026-09-08「继续迭代到"
            "收敛」既定指令（见 user_directive_note）；r15 指引已在盘冻结、"
            "本轮只读零写入；盲读由编排侧在本记录之后以 12 次独立实例盲读"
            "执行（12 派次 reader 实例群全部重抽）"),
        "user_directive_note": (
            "用户 2026-09-08「继续迭代到收敛」既定指令=授权执行 "
            "round15-dev-record next_iteration_targets[0]（R16 第一候选=同指"
            "引重复轮，授权原文逐字摘录于 guidance_reuse.chain_anchors."
            "round15_dev_record_authorization.candidate_quote；"
            "round15-dev-record.json 实测 sha256="
            f"{dev_ref['sha256_measured']}）：r15 指引/渲染零变更，仅换 12 "
            "派次 reader 实例群，用于消解「top 回退=跨轮实例群漂移」vs「"
            "§5A 全局弃权致敏」的归因歧义；预注册后执行；不得回溯改判既往"
            "轮次（r8–r15 字母裁决维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14/r15 完全相同（renders-r14b 字节复用）",
        },
        "guidance_reuse": {
            "base": "observation-guidance-r15.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r15.md"),
            "base_sha256": guidance15_sha,
            "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
            "mode": "byte_reuse_zero_change",
            "derived": None,
            "derived_path_rel": None,
            "derived_sha256": None,
            "byte_size": {"base": guidance15_bytes_n, "delta": 0},
            "edit_list": [],
            "zero_write_declaration": (
                "本轮不新建指引文件：observation-guidance-r15.md 零字节不动"
                "（本脚本无任何指引写路径；实测哈希在 guidance_reuse."
                "base_sha256，与开工实测 d5babc93 锚 fail-closed 一致）"),
            "verbatim_scope_note": (
                "§2–§7 判据文本、反放宽条款（「仅因形态不熟悉、不确定其设"
                "计含义，不构成判为正常设计特征的理由」）、三路出口、§5A "
                "渲染配色仪器注记随 r15 指引本体原样生效（字节复用=零措辞"
                "调整空间）；§6 示例旗 ID 前缀保持 R15T-/R15B-（r15 落盘原"
                "文），R16 派次 flag_id 前缀由派发指令层覆盖（见 "
                "protocol_amendment.naming）"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R15_SHA_PREFIX,
                "r15_prep_record_mirror_source": {
                    "path_rel": "out/v3-tl2/calibration/r15-prep-record.json",
                    "sha256": r15_record_sha,
                },
                "round15_dev_record_authorization": dev_ref,
                "run_r15_criterion_anchor": {
                    "path_rel": "out/v3-tl2/calibration/calibration-run-r15.json",
                    "sha256": run15_sha,
                    "frozen_values": (
                        "top 25/29=0.862069、bottom 11/13=0.846154、基线 "
                        "18/24=0.75（run-r14 内嵌实例记录双侧复算在案值）；"
                        "crit1/crit2=True、crit3=False——本记录 "
                        "hypothesis_test 预注册判据文本数值的在案锚"),
                },
                "render_witness_r14b": {
                    "path_rel": (
                        "out/v3-tl2/calibration/render-witness-r14b.json"),
                    "sha256": witness_sha,
                },
                "evaluation_protocol_v1_preserved": {
                    "path_rel": (
                        "out/v3-tl2/calibration/evaluation-protocol-v1.md"),
                    "sha256": protocol_sha,
                },
            },
        },
        "changed_variables": [],
        "manipulated_factor": "reader 实例群（12 派次全部重抽）",
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
                         "copies.sha256）——四图即 r14/r15 轮盲读所用同一"
                         "批文件；本轮零重渲染、零仪器变更"),
            },
            "判读指引 observation-guidance-r15.md 字节复用（d5babc93 实测"
            "锚）：§2 类别枚举、§3 收窄判据、§3A 判据示例、§4 全文（含量"
            "化判据 (i)(ii)(iii)、接触性判据、三路出口、反放宽条款「仅因形"
            "态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」）、"
            "§5 courtyard 说明、§5A 渲染配色仪器注记、§6 输出格式、§7 格式"
            "对齐提示——零字节不动（本轮不新建指引文件）",
            "GT 集：零改动（gt-audit-r1 三候选全部关闭在案；GT 侧不再有"
            "候选，r9–r15 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "度量设计五条与聚合口径：沿 r15-prep-record measurement_design"
            ".items 同一口径（仅轮次标识按 r16 改写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 显式配色版字节复用（与 "
            "R14/R15 完全相同：白墨图元→橙 (255,165,0)、板内空隙白→绿 "
            "(0,128,0)、其余层 kicad 原配色不变；四 PNG sha256 与 "
            "render-witness-r14b.json 登记值 fail-closed 比对一致）；top 渲"
            "染无配色变更（与 R14/R5 逐字节相同）；bottom 视判读口径沿用 "
            "r4 指引原文不改（top/bottom 判读口径在图像空间完全一致、不做"
            "镜像换算）；本轮零变更重复轮（指引/渲染字节复用）——唯一变"
            "化=reader 实例群重抽；bottom 零旗标分母=0 时弃权率按 cal._ratio"
            " 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R16 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r15-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R16T/R16B；"
                "聚合口径与 s55_calibration_r15_compare.py 同一比较脚本血"
                "统；代表配置/逐实例/双口径分列）"),
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
                "本轮恰一个操纵因子（reader 实例群抽样：12 派次全部重抽）、"
                "检验恰一个假设（round15-dev-record next_iteration_targets"
                "[0] 同指引重复轮；hypothesis_id=r15-dev-record-candidate-0-"
                "same-guidance-repeat）；归因目的=r15 判据 (iii) 违约（top "
                "25/29=0.862>18/24=0.75）的两候选解释消解：(α) 跨轮实例群"
                "漂移 vs (β) §5A 全局弃权致敏；跨轮对比（vs r14–r15）为方"
                "向性，实例群混杂在本轮=唯一操纵因子、恰是裁决变量；bottom"
                " 主通道维持性观察单列（side_observation_separate，不影响字"
                "母）；字母/机制观察/度量教训三分记账（adjudication."
                "side_observation_separate 与 metric_lesson_separate 单列，"
                "不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "reader-instance-group-resample（实例群抽样；非指引/渲"
                    "染/GT/阈值/协议变更）"),
                "metric": (
                    "top 全旗聚合弃权率归因裁决（三支）：(a) ≤0.75 → (α) "
                    "漂移成立；(b) ≥0.862 → (β) 致敏升级；(c) 两值之间 → "
                    "inconclusive（归因悬置）——详见 hypothesis_test."
                    "adjudication"),
                "support": (
                    "(a) top 全旗聚合弃权率 ≤ 0.75（冻结值）→ letter_"
                    "supported"),
                "reject": (
                    "(b) top 全旗聚合弃权率 ≥ 0.862（冻结值）→ letter_"
                    "reject（(β) 升级，指引侧再处置预注册后执行）"),
                "inconclusive": (
                    "(c) 0.75 < top < 0.862 → 字母=inconclusive"
                    "（development 域如实记录）"),
            },
            "side_observation": {
                "metric": (
                    "bottom 主通道维持性单列（不影响字母）：bottom courtyard"
                    " 旗与非弃权计数、bottom 全旗聚合弃权率对照 r15 的 "
                    "11/13=0.846 与 0/0/0"),
                "note": (
                    "若 bottom 恶化=图例效应本身实例群敏感，如实记录；黑点"
                    "类与绿区语义化方式延续观察"),
            },
            "guard_channel": {
                "metric": (
                    "top 视角非弃权旗标 frame_box_pct 几何门（面积比出局条"
                    "目；top 渲染字节复用零变更）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r15 指引字节复用），非弃权框仍须"
                    "满足；几何门面积比出局条目变化如实记录"),
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
            "零变更重复轮：判读指引=observation-guidance-r15.md 字节复用（"
            "d5babc93 实测锚）——反放宽条款「仅因形态不熟悉、不确定其设计"
            "含义，不构成判为正常设计特征的理由」与三路出口随指引本体原样"
            "生效，零变更轮无任何措辞调整空间（本脚本无任何指引写路径）；"
            "本轮三支判据（≤0.75 / ≥0.862 / 两值之间）只用于归因裁决方向，"
            "不触碰 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与任何阈值常量（CONTAINMENT_MIN/AREA_RATIO_"
            "MAX，只作口径引用）——门照常独立计算；不构成任何阈值反向放宽"),
        "no_instrument_change": True,
        "pre_round_review": {
            "status": "not_required_zero_change_round",
            "basis": "同指引重复轮先例 r10；无新干预引入",
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
                    "v1 原文零字节保留（r11–r15 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；本轮 12 派次 reader 实例群全部重抽（与 r15"
                " 无实例身份延续——同指引重复轮的唯一操纵因子）；实例上下"
                "文=指引（observation-guidance-r15.md 字节复用）+单张 PNG+"
                "派发命名指令（含 v1.2 工具行为规约硬性条款：纯 Read 内联"
                "判读、禁止任何程序化图像处理），零 GT、零历史判读件、零诊"
                "断/探针内容；两波次串行保序（同一实例先 applied 后 prep1，"
                "flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r16-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R16T/R16B（r15 指引 §6 示例前缀为 R15T-/R15B- 落盘原文、"
                "字节复用不改——R16 派次前缀由派发指令层覆盖，与 r13→r15"
                "「随指引落盘固化」路径不同，如实登记）；实例间编号独立，"
                "同实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 ground-truth-*、datasets/ 下任"
            "何文件、reader-raw-*、derivation-log-*、任何 compare/评估产物；"
            "未读取任何 PNG/PDF 内容（renders-r14b 四 PNG 仅哈希+magic，零"
            "内容判读、零像素读取）；本脚本只读输入=observation-guidance-"
            "r15.md（判读指引基座；d5babc93 锚 fail-closed，零写入——本轮"
            "零编辑零变换）、r15-prep-record.json（链锚=4c6cd919 先验证；字"
            "段结构镜像来源）、round15-dev-record.json（仅读取 round_id、"
            "next_iteration_targets（标记「R16 第一候选」定位 [0]）字段取授"
            "权原文，实测 sha 入记录）、calibration-run-r15.json（链锚="
            "0c37c1cb；仅读取 hypothesis_test.measurement 判据冻结值字段做"
            " fail-closed 锚定——top 25/29/0.862069、bottom 11/13/0.846154、"
            "基线 18/24/0.75、crit1/crit2/crit3 布尔；其 GT 匹配与逐旗明细"
            "内容不读取、不入记录）、render-witness-r14b.json（b63771f9 锚 "
            "fail-closed；四 PNG 见证登记值）、evaluation-protocol-v1.md（"
            "仅在盘+哈希复核，锚=22dc7337）；r16-prep-record.json 为本轮唯"
            "一新建产物（scripts/s57_calibration_r16_prep.py 为生成器本体，"
            "亦即本轮第二个新文件）；reader 派发（后续编排侧执行）上下文="
            "observation-guidance-r15.md+单张 PNG+派发指令（R16T/R16B 前缀、"
            "reader-r16-{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬性条款），"
            "零 GT、零历史判读件、零 r15 判读结果注入；视觉判读禁止由编排/"
            "收口包兼任；跨实例/跨视角禁止交流（12 次盲读相互独立、不得交"
            "换判读信息——独立性是多实例协议的前提，亦为实例群重抽归因的"
            "前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R15, R15_PREP_RECORD, R15_DEV_RECORD, RUN_R15,
                 WITNESS_R14B, EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    # 目标文件 RECORD 不做前置硬拒绝：落盘阶段防覆写守卫按红线口径执行
    # ——已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等通过（零覆
    # 写）。（首轮创建前置=目标不存在，已由编排侧开工确认。）

    # ---- 冻结锚验证（fail-closed）----
    r15_record_sha = _sha(R15_PREP_RECORD)
    dev_record_sha = _sha(R15_DEV_RECORD)
    run15_sha = _sha(RUN_R15)
    witness_sha = _sha(WITNESS_R14B)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    if not r15_record_sha.startswith(R15_PREP_RECORD_SHA_PREFIX):
        _fail(f"r15-prep-record sha 前 8={r15_record_sha[:8]} != 预期 "
              f"{R15_PREP_RECORD_SHA_PREFIX}（结构镜像来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R15_DEV_RECORD_SHA_PREFIX):
        _fail(f"round15-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R15_DEV_RECORD_SHA_PREFIX}（授权依据锚不符，立即停止）")
    if not run15_sha.startswith(RUN_R15_SHA_PREFIX):
        _fail(f"calibration-run-r15 sha 前 8={run15_sha[:8]} != 预期 "
              f"{RUN_R15_SHA_PREFIX}（判据实测值在案处锚不符，立即停止）")
    if not witness_sha.startswith(WITNESS_R14B_SHA_PREFIX):
        _fail(f"render-witness-r14b sha 前 8={witness_sha[:8]} != 预期 "
              f"{WITNESS_R14B_SHA_PREFIX}（仪器见证锚不符，立即停止）")
    if not protocol_sha.startswith(EVAL_PROTOCOL_V1_SHA_PREFIX):
        _fail(f"evaluation-protocol-v1.md sha 前 8={protocol_sha[:8]} != 预"
              f"期 {EVAL_PROTOCOL_V1_SHA_PREFIX}（协议原文保留载体疑被改动，"
              f"立即停止）")

    r15_record = json.loads(R15_PREP_RECORD.read_text(encoding="utf-8"))
    if r15_record.get("schema_version") != "3.0":
        _fail("r15-prep-record schema_version != 3.0（结构漂移）")
    if r15_record.get("kind") != "tl2_calibration_r15_prep_record":
        _fail("r15-prep-record kind 不符（结构漂移）")
    if r15_record.get("round_id_constant") != "2026-09-08-r15":
        _fail("r15-prep-record round_id_constant != 2026-09-08-r15（结构漂移）")

    # ---- 指引零写入复核（只读哈希；本脚本全程无指引写路径）----
    guidance = check_guidance_zero_write()
    guidance15_sha = guidance["sha256_measured"]

    # ---- 授权候选提取（round15-dev-record next_iteration_targets[0]）----
    dev_record = json.loads(R15_DEV_RECORD.read_text(encoding="utf-8"))
    dev_ref = extract_candidate(dev_record, dev_record_sha)

    # ---- 判据冻结值锚定（calibration-run-r15 在案实测）----
    run15 = json.loads(RUN_R15.read_text(encoding="utf-8"))
    crit_anchor = anchor_run15_criterion(run15)

    # ---- witness 结构校验 + 渲染零变更实测（四 PNG vs 登记值）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    probe_witness(witness)
    png_checks = check_renders_byte_reuse(witness)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance15_sha=guidance15_sha,
        guidance15_bytes_n=guidance["byte_size"],
        r15_record_sha=r15_record_sha, dev_ref=dev_ref,
        run15_sha=run15_sha, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r15-prep-record 逐键镜像
    missing = sorted(set(r15_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r15_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r15-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # hypothesis_test 逐字断言链：任务给定文本→json.loads→常量→记录字段
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if record["hypothesis_test"] != HYPOTHESIS_TEST:
        _fail("hypothesis_test 与预注册判据常量不一致（逐字要求被破坏）")
    # 结构自证
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（零变更重复轮）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（零变更重复轮）")
    if record["changed_variables"] != []:
        _fail("零变更重复轮：changed_variables 必须为空列表")
    if record["guidance_reuse"]["mode"] != "byte_reuse_zero_change":
        _fail("guidance_reuse.mode 必须为 byte_reuse_zero_change")
    if record["guidance_reuse"]["edit_list"] != []:
        _fail("guidance_reuse.edit_list 必须为空（零编辑）")
    if record["guidance_reuse"]["base_sha256"].startswith(
            GUIDANCE_R15_SHA_PREFIX) is not True:
        _fail("guidance_reuse.base_sha256 与 d5babc93 锚不符")
    if record["manipulated_factor"] != "reader 实例群（12 派次全部重抽）":
        _fail("manipulated_factor 不符（唯一操纵因子=实例群重抽）")
    if record["pre_round_review"]["status"] != "not_required_zero_change_round":
        _fail("pre_round_review.status 不符")
    if "同指引重复轮" not in record["round_nature"]:
        _fail("round_nature 缺「同指引重复轮」声明")
    if "r10 先例" not in record["round_nature"]:
        _fail("round_nature 缺「r10 先例」声明")
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
        guidance15_sha=guidance15_sha,
        guidance15_bytes_n=guidance["byte_size"],
        r15_record_sha=r15_record_sha, dev_ref=dev_ref,
        run15_sha=run15_sha, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r16-prep-record")

    # ---- 防覆写守卫 + 落盘（唯一写入目标=RECORD；指引零写入）----
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r16-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r16-prep] 重跑自证：r16-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r16-prep-record.json")

    # ---- 汇总打印 ----
    print("[r16-prep] 验证通过：observation-guidance-r15.md 基座锚 "
          f"{GUIDANCE_R15_SHA_PREFIX} OK（sha256={guidance15_sha}，只读零写"
          f"入，{guidance['byte_size']} B）；r15-prep-record 镜像锚 "
          f"{R15_PREP_RECORD_SHA_PREFIX} OK；round15-dev-record 实测 "
          f"{dev_record_sha[:8]}（候选=next_iteration_targets["
          f"{dev_ref['item_indices_zero_based'][0]}]「{MARK_CANDIDATE}」原文"
          f"摘录在案）；calibration-run-r15 判据锚 {RUN_R15_SHA_PREFIX} OK"
          f"（top {crit_anchor['top_abstain_r15']}、bottom "
          f"{crit_anchor['bottom_abstain_r15']}、基线 "
          f"{crit_anchor['r14_top_baseline']}、crit1={crit_anchor['crit1']}/"
          f"crit2={crit_anchor['crit2']}/crit3={crit_anchor['crit3']}）；"
          f"witness-r14b 锚 {WITNESS_R14B_SHA_PREFIX} OK；"
          f"evaluation-protocol-v1 在盘锚 {EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r16-prep] 渲染零变更自证（四 PNG 实测=witness 登记值）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r16-prep] hypothesis_test 逐字断言链：预注册判据原文文本 → "
          "json.loads → 常量 → 记录字段，三层相等 PASS（数值/口径零改动）")
    print(f"[r16-prep] 顶层键镜像断言：与 r15-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）")
    print(f"[r16-prep] 工件 sha256：observation-guidance-r15.md（零写入复"
          f"核）={_sha(GUIDANCE_R15)}")
    print(f"[r16-prep] 工件 sha256：r16-prep-record.json={_sha(RECORD)}")


if __name__ == "__main__":
    main()
