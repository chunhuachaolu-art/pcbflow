#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s79_protocol_v2_freeze.py — 评估协议 v2 冻结入账包：
protocol-v2-registration.json 生成器（纯函数+防覆写；登记件分包纪律，
结构血统=s78_calibration_r22_devrecord.py 同构）。

任务血统：R20 close 已完成（calibration-run-r20.json=6573a59a、
round20-dev-record.json=80e3e9e2 在盘）；per V3-RECOMMENDATIONS-
2026-09-09.md §6 交付顺序「R20 close → 冻结 holdout 协议」与 §7 最终
建议「完成 R20 close，随后冻结评估协议并准备独立 holdout」，本包执行
冻结评估协议 v2（独立 holdout 评估协议）并入账登记件。批准依据=用户
2026-09-10 指令「按 V3-RECOMMENDATIONS-2026-09-09.md 继续之后的工
作」。

本包边界（如实声明）：
- evaluation-protocol-v2.md（冻结件）由人工 Write 落盘，本脚本**只读
  实测+结构锚校验（fail-closed）**，不生成、不改写该 md；
- 本脚本只写 protocol-v2-registration.json 一件（canonical JSON）；
- evaluation-protocol-v1.md 零字节不动（22dc7337 锚）；HOLDOUT-PLAN.md
  零改动（a4b80193 锚）；datasets/ 严格只读；out/ 既有文件只读；
- APR-0011 阈值零改动；in_calibrated_range 恒 False；自动分流恒
  blocked；v2 生效≠holdout 启动（启动=用户判断的独立人工点）。

P2 九条款装配事实（如实登记）：V3-RECOMMENDATIONS §3 P2 原列八条
（三集按板隔离/reader 盲读/一对一匹配/重复旗标单列/unmatched·
unadjudicated·真实 false positive 三分/六指标分列/逐旗标人工裁定/
阈值不晋升）；第九条（缺 hash/stale/配对不完整候选 blocked）来自
§5 治理红线，经协议并入九条款清单——from 字段逐条如实标注。

现状登记（全部盘上实测装载，fail-closed）：
- r19 marginal（dev-r19=0e2fdd69）M 四元组=(0.461538, 0.571429, 4,
  0.211111)；
- r20 reject（run-r20=6573a59a、dev-r20=80e3e9e2）M1=0.636364，G1
  守门字面破坏（2/0/0）经 reject_guards——g1_bifurcation_record 在案；
  per §3 P1 表 reject→停止同一调参轴+保留负向证据；R21 不做；
- r22 regressed（run-r22=80a12c05、dev-r22=b4b8fbe9）M 四元组=
  (0.390244, 0.2, 4, 0.104545)，M1 落复制带 [0.361538, 0.561538]
  =带内复现；G2 几何门 R19=0→R22=2 破坏经 regressed_guards——
  g2_bifurcation_record 在案；G2 出局条目 R22T-002（16.406371）/
  R22T-013（16.369542）指针登记；
- 胜出配置=guidance-r19（8633bda5）双账定性：收益最大配置（描述性）
  与守门字面降级两账并列、不合并、不改写。

生成器纪律（s69/s72/s75/s78 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-10"；
- 防覆写护栏：protocol-v2-registration.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 末尾打印两件（v2 md + registration）sha256；重跑幂等。

用法：python scripts/s79_protocol_v2_freeze.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

# ---------------------------------------------------------------------------
# 声明常量（无 wall-clock）
# ---------------------------------------------------------------------------

DECLARED_DATE = "2026-09-10"
SCHEMA_VERSION = "3.0"
KIND = "protocol_v2_registration"

REL_PROTOCOL_V2 = "out/v3-tl2/calibration/evaluation-protocol-v2.md"
REL_PROTOCOL_V1 = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_HOLDOUT_PLAN = "out/v3-tl2/holdout/HOLDOUT-PLAN.md"
REL_RECOMMENDATIONS = "V3-RECOMMENDATIONS-2026-09-09.md"
REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_DEV_R22 = "out/v3-tl2/calibration/round22-dev-record.json"
REL_OUT = "out/v3-tl2/calibration/protocol-v2-registration.json"

# 引用件哈希锚（在案前缀；逐件 live 实测比对，fail-closed）。
# protocol_v2 不设前缀锚：冻结件由人工 Write 落盘，本脚本实测其哈希
# 登记并做结构锚校验（§v2_structural_anchors），防「锚追文件」循环。
REFERENCE_HASH_EXPECTED = {
    "protocol_v1": (REL_PROTOCOL_V1, "22dc7337"),
    "holdout_plan": (REL_HOLDOUT_PLAN, "a4b80193"),
    "recommendations": (REL_RECOMMENDATIONS, "ef94cffe"),
    "run_r20": (REL_RUN_R20, "6573a59a"),
    "run_r22": (REL_RUN_R22, "80a12c05"),
    "dev_r19": (REL_DEV_R19, "0e2fdd69"),
    "dev_r20": (REL_DEV_R20, "80e3e9e2"),
    "dev_r22": (REL_DEV_R22, "b4b8fbe9"),
}

# P2 九条款（id, from, text 摘要）——与 evaluation-protocol-v2.md §1
# 逐条一致；from 如实标注（1–8=§3 P2 原列；9=§5 红线并入）。
P2_CLAUSES = (
    ("P2-1", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "development/calibration/frozen holdout 按板或项目组隔离"),
    ("P2-2", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "reader 只看渲染输入，不看 GT"),
    ("P2-3", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "reader-to-GT 一对一匹配"),
    ("P2-4", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "重复旗标单列，不重复计入 precision"),
    ("P2-5", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "unmatched/unadjudicated/真实 false positive 三分"),
    ("P2-6", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "precision/recall/FPR/FNR/abstain/confidence calibration 分列"),
    ("P2-7", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "至少一部分结果有逐旗标人工裁定"),
    ("P2-8", "V3-RECOMMENDATIONS-2026-09-09.md §3 P2",
     "暂定阈值达标不自动晋升模型"),
    ("P2-9", "V3-RECOMMENDATIONS-2026-09-09.md §5（治理红线并入条款）",
     "任何缺 hash/stale/配对不完整候选 blocked"),
)

# evaluation-protocol-v2.md 结构锚（子串清单，fail-closed）——冻结件
# 结构断言（九条款齐/边界声明齐/supersedes 在位）。
V2_STRUCTURAL_ANCHORS = (
    "protocol_id: evaluation-protocol-v2",
    "version: v2",
    "status: frozen",
    "declared_date",
    DECLARED_DATE,
    "承继与取代关系（supersedes）",
    "v2 只治理未来的独立 holdout 评估",
    "v1 原文零字节保留",
    "v1.1 多实例聚合口径与 v1.2 工具行为规约被 v2 继承",
    "批准依据: 用户 2026-09-10 指令",
    "P2-1", "P2-2", "P2-3", "P2-4",
    "P2-5", "P2-6", "P2-7", "P2-8", "P2-9",
    "HOLDOUT-PLAN.md",
    "任何盲读、任何指引/协议迭代不得接触其渲染件",
    "运行时机=用户判断的独立人工点",
    "r19（marginal）",
    "r20（reject，G1 分岔）",
    "r22（regressed，G2 分岔，M1 带内复现）",
    "R21 全组合",
    "R22T-002", "R22T-013",
    "guidance-r19",
    "两账并列、不合并、不改写",
    "TL 门零改动",
    "APR-0011 零改动",
    "in_calibrated_range 恒 False",
    "自动分流恒 blocked",
    "v2 生效≠holdout 启动",
    "V4-SVG 属独立路线",
    "v4exp",
    "与 §5 治理红线的对齐声明",
)

# 现状登记数字锚（盘上实测装载后逐项比对，fail-closed）
R19_TUPLE = (0.461538, 0.571429, 4, 0.211111)
R20_M1 = 0.636364
R22_TUPLE = (0.390244, 0.2, 4, 0.104545)
R19_M1 = 0.461538
REPL_BAND = ("0.361538", "0.561538")
G2_OUTLIER_AREA_RATIOS = (16.406371, 16.369542)


# ---------------------------------------------------------------------------
# 基础助手（s78 同构）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    raise SystemExit(f"[s79-protocol-v2-freeze] FAIL: {msg}")


def _rel(rel: str) -> Path:
    return REPO / rel


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    with open(_rel(rel), encoding="utf-8") as f:
        return json.load(f)


def _read_text(rel: str) -> str:
    with open(_rel(rel), encoding="utf-8") as f:
        return f.read()


def overwrite_guard(existing: "bytes | None", new: bytes) -> str:
    """防覆写护栏（纯函数）：无既有→write；字节等同→idempotent_skip；
    既有且不同→fail（fail-closed，绝不覆写）。"""
    if existing is None:
        return "write"
    return "idempotent_skip" if existing == new else "fail"


def _commit(path: Path, new_bytes: bytes, label: str) -> str:
    """落盘（护栏语义）：已存在且字节等同→幂等跳过（零覆写）；
    已存在且不同→FAIL；否则写入并回读自证。"""
    if path.exists():
        if overwrite_guard(path.read_bytes(), new_bytes) == "fail":
            _fail(f"{label} 已存在且与重建字节不同（防覆写护栏，"
                  "fail-closed；发布产物不可覆写）")
        return "idempotent_skip"
    path.write_bytes(new_bytes)
    if path.read_bytes() != new_bytes:
        _fail(f"回读不一致: {label}")
    return "written"


def verify_reference_hashes(measured: "dict[str, str]",
                            expected: "dict[str, tuple]" = None) -> None:
    """引用件哈希清单校验（纯函数）：任一件实测前缀≠锚→SystemExit
    （fail-closed；篡改任一引用哈希→拒算）。"""
    expected = REFERENCE_HASH_EXPECTED if expected is None else expected
    for role, (rel, anchor) in sorted(expected.items()):
        got = measured.get(role)
        if got is None:
            _fail(f"引用件 {role}（{rel}）缺实测哈希")
        if not got.startswith(anchor):
            _fail(f"引用件 {role}（{rel}）实测 sha256={got} 与在案锚 "
                  f"{anchor} 不符（fail-closed）")


def measure_reference_hashes(
        expected: "dict[str, tuple]" = None) -> "dict[str, str]":
    """逐件实测引用件哈希（只读）。"""
    expected = REFERENCE_HASH_EXPECTED if expected is None else expected
    return {role: _sha(rel) for role, (rel, _a) in sorted(expected.items())}


def verify_v2_structural_anchors(text: str,
                                 anchors: "tuple[str, ...]" = None) -> None:
    """v2 冻结件结构锚校验（纯函数）：任一子串缺失→SystemExit。"""
    anchors = V2_STRUCTURAL_ANCHORS if anchors is None else anchors
    missing = [a for a in anchors if a not in text]
    if missing:
        _fail(f"evaluation-protocol-v2.md 结构锚缺失: {missing}")


# ---------------------------------------------------------------------------
# P1 表处置逻辑（纯函数；构造可测）
# ---------------------------------------------------------------------------

def axis_stop_action(r20_outcome: str) -> dict:
    """per V3-RECOMMENDATIONS §3 P1 表（纯函数）：按 R20 结果返回处置。
    四支齐全（supported/marginal/reject/inconclusive）；未知结果→
    fail-closed。"""
    table = {
        "supported": (
            "冻结当前组合指引和 metric，进入独立 holdout",
            "freeze current combined guidance and metric, enter "
            "independent holdout"),
        "marginal": (
            "仅在预注册规则允许时进入 holdout，不称为胜出",
            "enter holdout only if preregistered rules allow, do not "
            "call it a win"),
        "reject": (
            "停止同一调参轴，保留负向证据",
            "stop the same tuning axis, retain negative evidence"),
        "inconclusive": (
            "不强行选优，重新设计可区分原因的实验或直接进入冻结 holdout",
            "do not force a pick; redesign a discriminating experiment "
            "or enter frozen holdout"),
    }
    if r20_outcome not in table:
        _fail(f"axis_stop_action: 未知 R20 结果 {r20_outcome!r}（P1 表 "
              "四支之外，fail-closed）")
    action_zh, action_en = table[r20_outcome]
    return {
        "r20_outcome": r20_outcome,
        "action_zh": action_zh,
        "action_en": action_en,
        "source": "V3-RECOMMENDATIONS-2026-09-09.md §3 P1 表",
    }


# ---------------------------------------------------------------------------
# 现状数字装载（fail-closed）
# ---------------------------------------------------------------------------

def _load_r20(run_r20: dict) -> dict:
    ht = run_r20.get("hypothesis_test", {})
    m = ht.get("measurement", {})
    gc = m.get("guard_channel", {})
    verdict = ht.get("verdict")
    if verdict != "reject":
        _fail(f"run-r20 verdict={verdict!r}≠'reject'（fail-closed）")
    if m.get("top_abstain_rate_r20") != R20_M1:
        _fail(f"run-r20 top_abstain_rate_r20={m.get('top_abstain_rate_r20')}"
              f"≠{R20_M1}（fail-closed）")
    if gc.get("g1_ok") is not False:
        _fail("run-r20 guard_channel.g1_ok 应为 False（G1 破坏，"
              "fail-closed）")
    return {"verdict": verdict, "m1": m["top_abstain_rate_r20"],
            "g1_ok": gc["g1_ok"]}


def _load_r22(run_r22: dict) -> dict:
    ht = run_r22.get("hypothesis_test", {})
    m = ht.get("measurement", {})
    gc = m.get("guard_channel", {})
    verdict = ht.get("verdict")
    if verdict != "regressed":
        _fail(f"run-r22 verdict={verdict!r}≠'regressed'（fail-closed）")
    if m.get("top_abstain_rate_r22") != R22_TUPLE[0]:
        _fail(f"run-r22 top_abstain_rate_r22={m.get('top_abstain_rate_r22')}"
              f"≠{R22_TUPLE[0]}（fail-closed）")
    if (gc.get("g2_geometry_gate_r19"), gc.get("g2_geometry_gate_r22")) != \
            (0, 2):
        _fail("run-r22 G2 几何门应为 0→2（fail-closed）")
    if gc.get("guards_ok") is not False:
        _fail("run-r22 guard_channel.guards_ok 应为 False（fail-closed）")
    return {"verdict": verdict, "m1": m["top_abstain_rate_r22"],
            "g2_r19": gc["g2_geometry_gate_r19"],
            "g2_r22": gc["g2_geometry_gate_r22"]}


def _load_dev_r19(dev_r19: dict) -> dict:
    ht = dev_r19.get("hypothesis_test_i", {})
    trm = dev_r19.get("axis_experiment_ledger", {}).get(
        "this_round_measured", {})
    verdict = ht.get("verdict")
    if verdict != "marginal":
        _fail(f"dev-r19 verdict={verdict!r}≠'marginal'（fail-closed）")
    tuple19 = (trm.get("M1"), trm.get("M2"), trm.get("M3"), trm.get("M4"))
    if tuple19 != R19_TUPLE:
        _fail(f"dev-r19 M 四元组={tuple19}≠{R19_TUPLE}（fail-closed）")
    return {"verdict": verdict, "tuple": tuple19}


def _load_dev_r20(dev_r20: dict) -> dict:
    ht = dev_r20.get("hypothesis_test_i", {})
    verdict = ht.get("verdict")
    if verdict != "reject":
        _fail(f"dev-r20 verdict={verdict!r}≠'reject'（fail-closed）")
    if "g1_bifurcation_record" not in dev_r20:
        _fail("dev-r20 缺 g1_bifurcation_record（fail-closed）")
    return {"verdict": verdict,
            "g1_bifurcation": "g1_bifurcation_record 在案"}


def _load_dev_r22(dev_r22: dict) -> dict:
    ht = dev_r22.get("hypothesis_test_i", {})
    led = dev_r22.get("axis_experiment_ledger", {})
    trm = led.get("this_round_measured", {})
    sug = dev_r22.get("next_candidate_suggestion", {})
    verdict = ht.get("verdict")
    if verdict != "regressed":
        _fail(f"dev-r22 verdict={verdict!r}≠'regressed'（fail-closed）")
    tuple22 = (trm.get("M1"), trm.get("M2"), trm.get("M3"), trm.get("M4"))
    if tuple22 != R22_TUPLE:
        _fail(f"dev-r22 M 四元组={tuple22}≠{R22_TUPLE}（fail-closed）")
    if "g2_bifurcation_record" not in dev_r22:
        _fail("dev-r22 缺 g2_bifurcation_record（fail-closed）")
    options = sug.get("options", [])
    if len(options) != 3:
        _fail(f"dev-r22 next_candidate_suggestion 选项数={len(options)}≠3"
              "（fail-closed）")
    rows = led.get("cross_round_status", {}).get("measured_rows", {})
    for row, m1 in (("r19_axis3", R19_M1), ("r20_combo", R20_M1),
                    ("r22_repeat", R22_TUPLE[0])):
        if rows.get(row, {}).get("M1") != m1:
            _fail(f"dev-r22 轴账行 {row}.M1={rows.get(row, {}).get('M1')}"
                  f"≠{m1}（fail-closed）")
    return {"verdict": verdict, "tuple": tuple22,
            "options": [o.get("option", "")[:40] for o in options]}


# ---------------------------------------------------------------------------
# registration 构建（纯函数：输入全部为已装载的实测值/常量）
# ---------------------------------------------------------------------------

def build_registration(measured_hashes: "dict[str, str]",
                       protocol_v2_sha256: str,
                       protocol_v2_bytes_len: int,
                       r20_fact: dict, r22_fact: dict,
                       dev19_fact: dict, dev20_fact: dict,
                       dev22_fact: dict) -> dict:
    """登记件构建（纯函数）。哈希与现状数字均由调用方实测装载，
    本函数不做 IO。"""
    reg = {
        "approved_via": {
            "directive": "用户 2026-09-10 指令「按 "
                         "V3-RECOMMENDATIONS-2026-09-09.md 继续之后的"
                         "工作」",
            "doc_quote": "§7 最终建议：完成 R20 close，随后冻结评估协议"
                         "并准备独立 holdout",
            "doc_ref": {
                "path_rel": REL_RECOMMENDATIONS,
                "sha256": measured_hashes["recommendations"],
            },
            "prerequisite_status": "R20 close 已完成（run-r20=6573a59a、"
                                   "dev-r20=80e3e9e2 在盘）——本包执行其"
                                   "后续项（§6：R20 close → 冻结 holdout "
                                   "协议）",
        },
        "axis_stop_decision": {
            "decision": axis_stop_action("reject"),
            "g1_scope_note": "r20 的 G1 破坏源=组合指引 (iii-a) 间隙支——"
                             "同属「同一调参轴（组合指引轴）」停止范围",
            "r21_full_combination": "not_run（round20-dev-record 已登记"
                                    "「R21 不做」；axis-plan 冻结件预留"
                                    "槽位因 early_stop 未触发永久留空；"
                                    "r22 跳号与其无涉）",
            "negative_evidence_retained": "r20 reject 与 G1 分岔记录"
                                          "（dev-r20 g1_bifurcation_"
                                          "record）在案保留",
        },
        "boundary_declaration": {
            "apr_0011_thresholds": "unchanged（provisional_supersedable "
                                   "原文零改动）",
            "auto_routing": "blocked（恒；BL-4+TD5 合取约束在位；P2-8 "
                            "阈值不晋升条款同向）",
            "development_line_retained": "「GT≥12、覆盖≥3 类、连续两轮"
                                         "达标」保留为 development 评估"
                                         "线，非翻转正式谓词的充分条件",
            "in_calibrated_range": False,
            "tl_gates": "unchanged（TL-0–TL-6 门定义零改动）",
            "v2_activation_is_not_holdout_start":
                "v2 冻结只建立评估规则；holdout 启动=用户判断的独立人"
                "工点（HOLDOUT-PLAN 运行时机条款）",
            "v4_svg_separate_route":
                "per RECOMMENDATIONS §3 P4：V4-SVG 以新版本/新 schema/"
                "新实验目录进入开发（v4exp 外部工作流在盘登记：pcbflow/"
                "v4exp 模块与 out/v4-experiment 产物在案），不改 V3 门、"
                "不入 V3 历史产物、非本协议对象",
        },
        "declared_date": DECLARED_DATE,
        "governance_alignment":
            "与 V3-RECOMMENDATIONS §5 治理红线对齐：不覆盖历史 JSON/"
            "校准轮/状态摘要/冻结 render manifest（v1 零字节保留即其执"
            "行）；不改 schema/TL 门/waiver/生产条件换 pass；缺 hash/"
            "stale/配对不完整候选 blocked（P2-9）；本登记件=纯函数+"
            "canonical JSON+声明常量日期（无 wall-clock/主机路径）",
        "holdout_plan_ref": {
            "one_time_discipline":
                "候选板 designation=holdout-candidate；正式运行前任何盲"
                "读、任何指引/协议迭代不得接触其渲染件；渲染只在正式运"
                "行时做（冻结渲染管线）",
            "path_rel": REL_HOLDOUT_PLAN,
            "sha256": measured_hashes["holdout_plan"],
            "started": False,
            "timing": "用户判断的独立人工点（v2 冻结不构成启动指令）",
            "zero_gt_claim":
                "外部语料只评弃权率/旗标产量稳定性；零 GT 主张；报告不"
                "得出现 GT recall 字样（N/A+纪律引用）",
        },
        "kind": KIND,
        "next_steps": {
            "decision_authority": "用户拍板（dev-r22 与本件均不预写决策）",
            "options_pointer": {
                "source": "round22-dev-record.json "
                          "next_candidate_suggestion.options（三选项如实"
                          "单列）",
                "option_a": "接受发展域现状收束训练环（不再追加迭代轮）；"
                            "留出集时机由用户判断（preregistration_"
                            "required=False）",
                "option_b": "对 G2 的 2 条出局条目做机制归因（报告框 "
                            "hygiene 核实→派发层框收敛指引；须新预注册"
                            "轮）",
                "option_c": "再一轮同指引重复轮（三样本；r16 先例同型；"
                            "须预注册）",
            },
        },
        "non_round_artifact_note":
            "本件为协议冻结登记件（非轮次件）：无 round 字段；round_"
            "id/round_label 语义属轮次件（dev-record/run-record 链），"
            "本件不占用轮次号段",
        "p2_clauses": [
            {"from": src, "id": cid, "text": text}
            for cid, src, text in P2_CLAUSES
        ],
        "p2_clauses_assembly_note":
            "装配事实：§3 P2 原列八条（P2-1…P2-8）；P2-9=§5 治理红线并"
            "入条款——from 字段逐条如实标注，九条合计为协议冻结口径",
        "protocol_v2": {
            "bytes": protocol_v2_bytes_len,
            "declared_date": DECLARED_DATE,
            "path_rel": REL_PROTOCOL_V2,
            "sha256": protocol_v2_sha256,
            "status": "frozen",
            "structural_anchor_count": len(V2_STRUCTURAL_ANCHORS),
            "version": "v2",
        },
        "references": {
            role: {"path_rel": rel, "sha256": measured_hashes[role]}
            for role, (rel, _a) in sorted(REFERENCE_HASH_EXPECTED.items())
        },
        "status_registration": {
            "axis_ledger_rows": {
                "r16_baseline": {"M1": 0.771429},
                "r17_axis1": {"M1": 0.88},
                "r18_axis2": {"M1": 0.645161},
                "r19_axis3": {"M1": dev19_fact["tuple"][0]},
                "r20_combo": {"M1": r20_fact["m1"]},
                "r22_repeat": {"M1": r22_fact["m1"]},
            },
            "r19": {
                "dev_record": "round19-dev-record.json（0e2fdd69）",
                "m_tuple_6dp": list(dev19_fact["tuple"]),
                "verdict": dev19_fact["verdict"],
            },
            "r20": {
                "g1_bifurcation":
                    "G1（bottom courtyard 非弃权 0/0/0 维持）字面破坏"
                    "（实测 2/0/0，触发旗 R20B-003/R20B-006）经 "
                    "reject_guards 支命中；触发源=负责任报告（(iii-a) "
                    "间隙支）——两账分列（dev-r20 g1_bifurcation_record "
                    "在案，字母不改写）",
                "m1_6dp": r20_fact["m1"],
                "run_record": "calibration-run-r20.json（6573a59a）",
                "verdict": r20_fact["verdict"],
            },
            "r21": {
                "status": "not_run（跳号；R21 全组合槽位永久留空；r22 与"
                          "该位无涉）",
            },
            "r22": {
                "g2_bifurcation":
                    f"G2 几何门 R19=0→R22=2 破坏经 regressed_guards 支"
                    f"命中；M1={r22_fact['m1']}/1 落复制带 "
                    f"[{REPL_BAND[0]}, {REPL_BAND[1]}]（r19±0.10）内="
                    f"带内复现——字母=regressed（唯一正式裁决）与 M1 带"
                    f"内复制事实两账分列（dev-r22 g2_bifurcation_record "
                    f"在案，字母不改写）",
                "g2_outlier_entries_pointer": {
                    "R22T-002": {"area_ratio": G2_OUTLIER_AREA_RATIOS[0],
                                 "excerpt_source":
                                     "round22-dev-record.json "
                                     "g2_bifurcation_record."
                                     "rejected_entries_excerpt"},
                    "R22T-013": {"area_ratio": G2_OUTLIER_AREA_RATIOS[1],
                                 "excerpt_source":
                                     "round22-dev-record.json "
                                     "g2_bifurcation_record."
                                     "rejected_entries_excerpt"},
                },
                "m_tuple_6dp": list(dev22_fact["tuple"]),
                "run_record": "calibration-run-r22.json（80a12c05）",
                "verdict": dev22_fact["verdict"],
            },
            "supersession_scope":
                "v2 只治理未来独立 holdout 评估；v1 原文零字节保留继续承"
                "载 R1–R22 历史口径；v1.1 多实例聚合口径与 v1.2 工具行为"
                "规约被 v2 继承（原样、不另立版本）",
            "winning_config_dual_account":
                "胜出配置=guidance-r19（observation-guidance-r19.md="
                "8633bda5）：收益最大配置=轴3 单变量（M1=0.461538 历史"
                "最佳）——归因状态=「M1 量级在新鲜实例群复现（r22 带内，"
                "机制方向支持）但守门字面降级（r22 字母=regressed）」两"
                "账并列、不合并、不改写；「胜出」仅描述性定性，不构成采"
                "纳、不构成晋升",
        },
        "supersedes": {
            "inherited": ["v1.1 多实例聚合口径（r11 确立 n=3 实例协议、"
                          "实例主记录+视角层三分列）",
                          "v1.2 工具行为规约（判读只允许以 Read 工具查看"
                          "原图、禁止程序化处理）"],
            "retention": "v1 原文零字节保留（evaluation-protocol-v1.md，"
                         "sha256 前缀 22dc7337 实测在盘），继续承载 "
                         "R1–R22 历史口径；对 v1 冻结产物零回写",
            "scope": "v2 只治理未来的独立 holdout 评估；development/"
                     "calibration 域轮次评估继续按 v1 口径在案执行",
            "target_path_rel": REL_PROTOCOL_V1,
            "target_sha256": measured_hashes["protocol_v1"],
        },
        "schema_version": SCHEMA_VERSION,
    }
    return reg


# ---------------------------------------------------------------------------
# 主流程（实测装载→校验→构建→落盘→打印）
# ---------------------------------------------------------------------------

def main() -> None:
    # 1) 引用件哈希实测+fail-closed 校验
    measured = measure_reference_hashes()
    verify_reference_hashes(measured)

    # 2) v2 冻结件：只读实测+结构锚校验（不生成、不改写）
    v2_text = _read_text(REL_PROTOCOL_V2)
    verify_v2_structural_anchors(v2_text)
    v2_sha = _sha(REL_PROTOCOL_V2)
    v2_bytes_len = _rel(REL_PROTOCOL_V2).stat().st_size
    if v2_bytes_len == 0:
        _fail("evaluation-protocol-v2.md 为零字节（冻结件不得为空）")

    # 3) v1 零字节不动锚：实测字节>0 且哈希锚已由 step 1 校验
    v1_size = _rel(REL_PROTOCOL_V1).stat().st_size
    if v1_size == 0:
        _fail("evaluation-protocol-v1.md 零字节=被清空（零字节不动锚破坏）")

    # 4) 现状数字 fail-closed 装载
    r20_fact = _load_r20(_json_load(REL_RUN_R20))
    r22_fact = _load_r22(_json_load(REL_RUN_R22))
    dev19_fact = _load_dev_r19(_json_load(REL_DEV_R19))
    dev20_fact = _load_dev_r20(_json_load(REL_DEV_R20))
    dev22_fact = _load_dev_r22(_json_load(REL_DEV_R22))

    # 5) 构建+落盘（防覆写护栏）
    reg = build_registration(measured, v2_sha, v2_bytes_len,
                             r20_fact, r22_fact, dev19_fact, dev20_fact,
                             dev22_fact)
    reg_bytes = hashing.canonical_json_bytes(reg)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, reg_bytes, REL_OUT)
    print(f"[s79-protocol-v2-freeze] protocol-v2-registration: {status}")
    print(f"[s79-protocol-v2-freeze] supersedes: "
          f"{reg['supersedes']['target_path_rel']} "
          f"sha256[:8]={reg['supersedes']['target_sha256'][:8]}（零字节"
          f"保留，{v1_size} bytes）→ v2 "
          f"sha256[:8]={v2_sha[:8]}（{v2_bytes_len} bytes，status=frozen）")
    print(f"[s79-protocol-v2-freeze] P2 九条款: 1–8=RECOMMENDATIONS §3 P2 "
          f"原列；9=§5 红线并入——逐条 from 标注（装配事实如实登记）")
    print(f"[s79-protocol-v2-freeze] 现状登记: r19=marginal "
          f"M1={dev19_fact['tuple'][0]}；r20=reject（G1 破坏 2/0/0，"
          f"M1={r20_fact['m1']}）→per P1 表=停止同一调参轴+保留负向证据+"
          f"R21 不做；r22=regressed（G2 0→2，M1={r22_fact['m1']} 带内复现"
          f"[{REPL_BAND[0]}, {REPL_BAND[1]}]）；胜出配置 guidance-r19 双"
          f"账定性（收益最大 vs 守门降级，两账并列不改写）")
    print(f"[s79-protocol-v2-freeze] 边界声明: TL 门/APR-0011 零改动；"
          f"in_calibrated_range=False；自动分流=blocked；v2 生效≠holdout "
          f"启动（启动=用户判断的独立人工点）；V4-SVG 独立路线（v4exp 在"
          f"盘登记、非本协议对象）")
    print(f"[s79-protocol-v2-freeze] 下一候选三选项指针（dev-r22、用户拍"
          f"板）: (a) 收束训练环+留出时机用户判断；(b) G2 出局条目机制归"
          f"因（须新预注册轮）；(c) 同指引重复轮三样本（须预注册）")
    print(f"[s79-protocol-v2-freeze] sha256 {Path(REL_PROTOCOL_V2).name} = "
          f"{v2_sha}")
    print(f"[s79-protocol-v2-freeze] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print("[s79-protocol-v2-freeze] 协议 v2 冻结入账完成（v2 只治理未来"
          "独立 holdout 评估；v1 零字节保留；in_calibrated_range 恒 "
          "False；自动分流恒 blocked；holdout 未启动）")


if __name__ == "__main__":
    main()
