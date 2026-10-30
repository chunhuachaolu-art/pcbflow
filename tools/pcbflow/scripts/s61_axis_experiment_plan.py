#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s61_axis_experiment_plan.py — development 域实验计划件：
tl2 校准线「三轴收益比较实验」（R17–R20，条件触发 R21）——
跨轮收益比较规则与组合决策规则的预注册冻结件（先于任何实验轮盲读）。

背景：abstain-typology-r13-r16（锚 6dadac8d…）给出三条处置轴的分型证据；
用户 2026-09-09 指令：「三条轴单独/组合/全组合尝试，选择收益最大的继续」。
为防事后择优，本件在任何实验轮盲读之前冻结：
- benefit_metrics（跨轮统一口径 M1–M4，12 派次全口径、与分型件同法）；
- baselines_registered（r16 主基线 + r15 参照；数值从盘上 run-r16 与
  abstain-typology 实测装载、fail-closed，不得手抄）；
- guards（G1/G2/G3）；
- comparison_rule（字典序排序 + 显著收益定义 + 漂移混杂注记）；
- combination_decision_rule（阶段2 组合/全组合决策）；
- early_stop_rule 与 limitations_note。

本件性质（disclaimer，逐字入产物）：development 域实验计划（用户 2026-09-09
授权的三轴阶乘探索），非门、无字母语义、不凌驾 APR-0011/阈值；各实验轮仍
各自走 prep-record 预注册；本件只冻结跨轮比较规则与组合决策规则。

生成器纪律：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节只依赖
  盘上冻结输入与本文件常量；日期只用常量 DECLARED_DATE="2026-09-09"）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（4 件锚开工实测、与期望值 fail-closed
  比对，不符即 FAIL 不落盘）；
- 防覆写护栏：产物已存在且字节不同→FAIL；字节等同→幂等跳过零覆写；
- 本脚本只写 axis-experiment-plan-r17-r20.json 一件。

用法：python scripts/s61_axis_experiment_plan.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"
REL_OUT = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
OUT = REPO / REL_OUT

DECLARED_DATE = "2026-09-09"
SCHEMA_VERSION = "3.0"
KIND = "tl2_axis_experiment_plan_development"
EVALUATION_DOMAIN = "development"

ANCHOR_DIR = CAL
# 四件锚（开工实测期望值；fail-closed：不符即 FAIL 不落盘）
EXPECTED_ANCHOR_SHA = {
    "abstain-typology-r13-r16.json":
        "6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b53283681bc80",
    "calibration-run-r16.json":
        "2c1f8265e553d3df2d5fcb3c19a87363e7a977ea19d5b74a3ce7b20094e7ddb8",
    "round16-dev-record.json":
        "589fe62f331d2ae0d98bf32bfcbeacad66926f8bc0c4d088ec873ad01fe39c4a",
    "observation-guidance-r15.md":
        "d5babc9338e4d063652d5b217b85b1fb731ce53d76f16b2a5d79e8267c4ee267",
}

# 基线期望值（fail-closed 比对目标；产物内数值仍以盘上实测装载为准）
EXPECTED_BASELINES = {
    "r16": {"M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904},
    "r15": {"M1": 0.862069, "M2": 0.846154, "M3": 8},
}
# 分型证据期望值（grand 家族计数 + 视分布计数 + 占比）
EXPECTED_GRAND_FAMILIES = {
    "contact": 38, "existence_blackdot": 43, "existence_other": 48,
    "other": 0, "semantic_confusion": 3,
}
EXPECTED_VIEW_COUNTS = {
    "contact_top": 36, "contact_bottom": 2,
    "blackdot_top": 8, "blackdot_bottom": 35,
}
EXPECTED_SHARES = {"contact_top_share": 0.947368, "blackdot_bottom_share": 0.813953}

DISCLAIMER = (
    "本件=development 域实验计划（用户 2026-09-09 授权的三轴阶乘探索），非门、"
    "无字母语义、不凌驾 APR-0011 与既有阈值（gt_recall≥0.75/seed_match_rate≥0.5/"
    "abstain_rate≤0.5 与各轮预注册三分判据均原样适用）；各实验轮（R17–R21，如触发）"
    "仍各自走 prep-record 预注册（先于该轮盲读冻结），本件不替代任何轮级预注册；"
    "本件只冻结跨轮收益比较规则（comparison_rule）与组合决策规则"
    "（combination_decision_rule），不预写任何轮的结果、不预判任何轴的收益；"
    "判据/阈值/GT 零改动、既往轮次字母不回写。"
)


def _fail(msg: str):
    print(f"[s61][FAIL] {msg}")
    raise SystemExit(2)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        _fail(msg)


def _rate6(num: int, den: int) -> float:
    """分型件同法：弃权率先四舍五入 6 位小数。"""
    return round(num / den, 6)


# ---------------------------------------------------------------------------
# fail-closed 装载（只读盘上冻结输入）
# ---------------------------------------------------------------------------

def load_inputs() -> dict:
    measured: dict[str, str] = {}
    for name, expected in EXPECTED_ANCHOR_SHA.items():
        p = ANCHOR_DIR / name
        if not p.is_file():
            _fail(f"anchor missing: {name}")
        h = hashing.sha256_file(str(p))
        _require(h == expected,
                 f"anchor hash mismatch: {name} got {h} expected {expected}")
        measured[name] = h
        print(f"[s61] anchor OK: {name} = {h}")

    typ_path = ANCHOR_DIR / "abstain-typology-r13-r16.json"
    run_path = ANCHOR_DIR / "calibration-run-r16.json"
    dev_path = ANCHOR_DIR / "round16-dev-record.json"
    g15_path = ANCHOR_DIR / "observation-guidance-r15.md"

    typ = json.loads(typ_path.read_text(encoding="utf-8"))
    run16 = json.loads(run_path.read_text(encoding="utf-8"))
    dev16_raw = dev_path.read_text(encoding="utf-8")
    g15_text = g15_path.read_text(encoding="utf-8")

    # --- 分型证据装载（matrix.grand + round_view 视分布求和） ---
    grand = typ["matrix"]["grand"]["families"]
    _require(grand == EXPECTED_GRAND_FAMILIES,
             f"grand families mismatch: {grand}")
    rounds4 = ("r13", "r14", "r15", "r16")
    contact_top = sum(typ["matrix"]["round_view"][f"{r}|top"]["families"]["contact"]
                      for r in rounds4)
    contact_bottom = sum(typ["matrix"]["round_view"][f"{r}|bottom"]["families"]["contact"]
                         for r in rounds4)
    blackdot_top = sum(typ["matrix"]["round_view"][f"{r}|top"]["families"]["existence_blackdot"]
                       for r in rounds4)
    blackdot_bottom = sum(typ["matrix"]["round_view"][f"{r}|bottom"]["families"]["existence_blackdot"]
                          for r in rounds4)
    _require({"contact_top": contact_top, "contact_bottom": contact_bottom,
              "blackdot_top": blackdot_top,
              "blackdot_bottom": blackdot_bottom} == EXPECTED_VIEW_COUNTS,
             "round×view family sums mismatch")
    contact_top_share = _rate6(contact_top, grand["contact"])
    blackdot_bottom_share = _rate6(blackdot_bottom, grand["existence_blackdot"])
    _require(contact_top_share == EXPECTED_SHARES["contact_top_share"],
             f"contact top share mismatch: {contact_top_share}")
    _require(blackdot_bottom_share == EXPECTED_SHARES["blackdot_bottom_share"],
             f"blackdot bottom share mismatch: {blackdot_bottom_share}")
    blackdot_by_round = {r: typ["matrix"]["round_totals"][r]["families"]["existence_blackdot"]
                         for r in rounds4}
    _require(blackdot_by_round == {"r13": 9, "r14": 14, "r15": 8, "r16": 12},
             f"blackdot by round mismatch: {blackdot_by_round}")
    print(f"[s61] evidence loaded: contact={grand['contact']} "
          f"(top {contact_top}/bottom {contact_bottom}, top share "
          f"{contact_top_share * 100:.1f}%), blackdot={grand['existence_blackdot']} "
          f"(top {blackdot_top}/bottom {blackdot_bottom}, bottom share "
          f"{blackdot_bottom_share * 100:.1f}%), existence_other="
          f"{grand['existence_other']}, semantic={grand['semantic_confusion']}")

    # --- 基线 M1/M2/M3 装载（分型件 matrix；逐项与期望值 fail-closed） ---
    def _m123(rnd: str) -> dict:
        rt = typ["matrix"]["round_view"][f"{rnd}|top"]
        rb = typ["matrix"]["round_view"][f"{rnd}|bottom"]
        m1, m2 = rt["abstain_rate"], rb["abstain_rate"]
        m3 = typ["matrix"]["round_totals"][rnd]["families"]["existence_blackdot"]
        _require(m1 == _rate6(rt["abstain"], rt["flags"]),
                 f"{rnd} top rate recompute mismatch")
        _require(m2 == _rate6(rb["abstain"], rb["flags"]),
                 f"{rnd} bottom rate recompute mismatch")
        exp = EXPECTED_BASELINES[rnd]
        _require(m1 == exp["M1"], f"{rnd} M1 mismatch: {m1}")
        _require(m2 == exp["M2"], f"{rnd} M2 mismatch: {m2}")
        _require(m3 == exp["M3"], f"{rnd} M3 mismatch: {m3}")
        return {"M1": m1, "M2": m2, "M3": m3}

    r16_m = _m123("r16")
    r15_m = _m123("r15")

    # --- r16 M4 装载（run-r16 instances；与 run 登记率、分型件交叉核对） ---
    inst = run16["instances"]
    per_inst: dict[str, float] = {}
    for name in ("top-i1", "top-i2", "top-i3"):
        c = inst[name]["combined"]
        r = _rate6(c["abstain_count"], c["flag_count"])
        _require(r == c["abstain_rate"],
                 f"r16 {name} rate mismatch vs run registry: {r} vs {c['abstain_rate']}")
        cc = typ["cross_check_vs_runs"][f"r16|{name}"]
        _require(cc["equal"] is True
                 and cc["recomputed_abstain"] == c["abstain_count"]
                 and cc["recomputed_flags"] == c["flag_count"],
                 f"r16 {name} cross-check vs typology mismatch")
        per_inst[name] = r
    m4_16 = round(max(per_inst.values()) - min(per_inst.values()), 6)
    _require(m4_16 == EXPECTED_BASELINES["r16"]["M4"],
             f"r16 M4 mismatch: {m4_16}")
    r16_m["M4"] = m4_16
    print(f"[s61] baselines loaded: r16 M1={r16_m['M1']} M2={r16_m['M2']} "
          f"M3={r16_m['M3']} M4={r16_m['M4']} "
          f"(per-instance top rates {per_inst})")
    print(f"[s61] baselines loaded: r15 M1={r15_m['M1']} M2={r15_m['M2']} "
          f"M3={r15_m['M3']}")

    # --- 口径差异在案证据（s59 prose 口径 r15=7 vs 分型件 rubric 口径 r15=8）---
    _require("r15 7→r16 12" in dev16_raw,
             "dev-record r16 未含 s59 prose 口径 r15=7 在案证据")
    _require("非弃权 courtyard 0/0/0" in dev16_raw,
             "dev-record r16 未含 G1 基线证据（非弃权 courtyard 0/0/0 维持）")
    print("[s61] dev-record in-evidence OK: s59 prose 口径 r15=7（vs rubric 口径 8）"
          "与 G1 基线「非弃权 courtyard 0/0/0 维持」均在案")

    # --- 协议与指引装载核验 ---
    amend = run16["protocol"]["amendment_version"]
    _require("v1.1+v1.2" in amend, f"protocol amendment mismatch: {amend}")
    guard_ok = run16["hypothesis_test"]["measurement"]["guard_channel"]["guard_ok"]
    _require(guard_ok is True, "r16 guard_channel.guard_ok is not True")
    _require("接触性判据" in g15_text and "§5A" in g15_text,
             "guidance r15 缺 §4(iii) 接触性判据或 §5A 节")
    print(f"[s61] protocol OK: amendment={amend.split('（')[0]}；"
          f"r16 guard_ok=True；guidance r15 含 §4(iii) 接触性判据与 §5A")

    drift = round(abs(r15_m["M1"] - r16_m["M1"]), 6)
    return {
        "measured": measured,
        "grand": grand,
        "contact_top": contact_top, "contact_bottom": contact_bottom,
        "blackdot_top": blackdot_top, "blackdot_bottom": blackdot_bottom,
        "contact_top_share": contact_top_share,
        "blackdot_bottom_share": blackdot_bottom_share,
        "blackdot_by_round": blackdot_by_round,
        "r16": r16_m, "r15": r15_m,
        "per_inst_top_r16": per_inst,
        "drift_r15_r16": drift,
        "protocol_amendment": amend,
    }


# ---------------------------------------------------------------------------
# 计划件构建（纯函数：字节只依赖 loaded 与本文件常量）
# ---------------------------------------------------------------------------

def build_doc(x: dict) -> dict:
    g = x["grand"]
    pct_ct = f"{x['contact_top_share'] * 100:.1f}%"
    pct_bb = f"{x['blackdot_bottom_share'] * 100:.1f}%"
    bd = x["blackdot_by_round"]
    r16, r15 = x["r16"], x["r15"]

    doc = {
        "kind": KIND,
        "schema_version": SCHEMA_VERSION,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "user_directive_note": {
            "directive_date": DECLARED_DATE,
            "user_quote": "三条轴单独/组合/全组合尝试，选择收益最大的继续",
            "note": "用户 2026-09-09 原话指令：三条轴单独/组合/全组合尝试、选择收益最大的继续；"
                    "本件将该指令操作化为预注册的跨轮收益比较规则（comparison_rule）与组合决策"
                    "规则（combination_decision_rule），并先于任何实验轮盲读冻结以防事后择优",
        },
        "disclaimer": DISCLAIMER,
        "experiment_design": {
            "stage1": "三单轴轮：R17=轴1（渲染分辨率倍增）、R18=轴2（黑点类专项）、"
                      "R19=轴3（判据侧处置），各轮单变量、12 派次盲读",
            "stage2": "组合轮：按 combination_decision_rule 取收益 top2 轴组合（R20），"
                      "必要时全组合（R21）——是否触发、与谁组合均由冻结规则决定，不临场拍板",
            "why_frozen_first": "跨轮收益比较规则先于 R17–R21 任何实验轮盲读冻结"
                                "（用户 2026-09-09 指令+防事后择优）",
            "final_selection": "最终「收益最大配置」由 combination_decision_rule (iv) 决定",
        },
        "axes": [
            {
                "axis_id": "A1_render_resolution_x2",
                "name": "top/全视渲染分辨率倍增（dpi 640→1280）",
                "side": "instrument（仪器轮：渲染侧变更，轮级预注册须声明零仪器变更纪律例外）",
                "target_families": f"contact 族为主（四轮 {g['contact']} 旗、top "
                                   f"{x['contact_top']}/bottom {x['contact_bottom']}、"
                                   f"top 占 {pct_ct}），并覆盖 top 视存在性族（existence_other）",
                "evidence_refs": [
                    "abstain-typology-r13-r16.json findings."
                    "q3_contact_vs_existence_axis_evidence",
                    "abstain-typology-r13-r16.json matrix.grand.families.contact="
                    f"{g['contact']}（本件实测装载复核）",
                ],
                "mechanism_hypothesis": "contact 族=结构间 courtyard/轮廓接触不可分辨"
                                        "（真实接触 vs 视觉贴近在 dpi 640 下不可分辨），"
                                        "其解决依赖更高角点分辨率（分型件事实基础 (a)）",
            },
            {
                "axis_id": "A2_blackdot_instrument_annotation",
                "name": "黑点类专项（指引侧中性仪器注记）",
                "side": "guidance（指引侧；渲染 r14b 字节复用零变更）",
                "target_families": f"existence_blackdot 族（四轮 {g['existence_blackdot']} 旗、"
                                   f"bottom {x['blackdot_bottom']}/top {x['blackdot_top']}、"
                                   f"bottom 占 {pct_bb}；弃权连续 4 轮主导 "
                                   f"r13={bd['r13']}/r14={bd['r14']}/r15={bd['r15']}/"
                                   f"r16={bd['r16']}，rubric 口径）",
                "precondition": "注记内容须先经盘上探针证实黑点物理来源（仪器事实）；"
                                "注记=仪器事实陈述、非判据、不引导判定方向；"
                                "无探针证实则该轴不得入轮",
                "evidence_refs": [
                    "abstain-typology-r13-r16.json findings."
                    "q2_blackdot_counts_and_normal_dispatches",
                    "round16-dev-record.json 机制观察 (b)（黑点类 12 旗全弃权"
                    "连续第 4 轮主导在案）",
                ],
                "mechanism_hypothesis": "黑点族弃权与渲染配色（黑点图元无仪器注记解释）相关"
                                        "（分型件事实基础 (b)）",
            },
            {
                "axis_id": "A3_criterion_contact_clarification",
                "name": "判据侧处置（§4(iii) 接触性判据补可操作分辨条款）",
                "side": "guidance（指引侧判据语义；渲染 r14b 字节复用零变更）",
                "target": "弃权判定一致性（跨实例/跨派次处置分化的收敛）",
                "primary_metric_note": "轴3 的收益本在 M4（top 逐实例弃权率极差）而非 M1；"
                                       "comparison_rule 以 M1 领衔对其不利，属已接受的"
                                       "操作化取舍（见 limitations_note）",
                "constraint": "方向=判定一致性；反放宽条款逐字保留（同等判断责任、"
                              "「仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征"
                              "的理由」原文一字不松）",
                "evidence_refs": [
                    "abstain-typology-r13-r16.json findings."
                    "q3_contact_vs_existence_axis_evidence（判据措辞致敏=跨家族共因，"
                    "分型件事实基础 (c)）",
                    "observation-guidance-r15.md §4 量化判据 (iii) 接触性判据（在案原文）",
                ],
            },
        ],
        "stage1_rounds": {
            "common": {
                "blind_reads_per_round": 12,
                "blind_reads_composition": "2 视角(top/bottom)×2 板(applied/prep1)"
                                           "×3 实例(i1/i2/i3)，与 r13–r16 同口径",
                "protocol": f"evaluation-protocol-v1，amendment {x['protocol_amendment']}"
                            "（维持，零新增版本）",
                "preregistration": "各轮仍各自走 prep-record 预注册（先于该轮盲读冻结）；"
                                   "本件不替代轮级预注册",
                "letter_adjudication": "各轮字母裁决照常执行；本计划件无字母语义",
            },
            "rounds": [
                {
                    "round_id": "R17",
                    "axis_id": "A1_render_resolution_x2",
                    "round_nature": "仪器轮（渲染侧单变量）",
                    "render": "全新渲染 dpi 640→1280（像素密度 4 倍），r14b 配色规则重放："
                              "bottom 视白墨矢量图元 mask→橙 (255,165,0)、板界内空隙白 mask→"
                              "绿 (0,128,0)、二值 mask 全量替换不做 alpha 混合、z 序 "
                              "base→橙→绿（与 render-framing-r14b declaration 同规则于 "
                              "1280dpi 重放）；层清单/组合页/裁剪公式同口径，dpi=唯一仪器变量",
                    "guidance": "observation-guidance-r15.md 逐字复用（零变更；含 §4 量化判据 "
                                "(i)(ii)(iii) 与 §5A 渲染配色仪器注记）",
                },
                {
                    "round_id": "R18",
                    "axis_id": "A2_blackdot_instrument_annotation",
                    "round_nature": "指引侧单变量轮（渲染零变更）",
                    "render": "renders-r14b 四图字节复用（零变更）",
                    "guidance": "r15 指引+黑点中性仪器注记；注记内容须先经盘上探针证实黑点"
                                "物理来源（仪器事实非判据），无探针证实则该轴不得入轮",
                },
                {
                    "round_id": "R19",
                    "axis_id": "A3_criterion_contact_clarification",
                    "round_nature": "指引侧单变量轮（渲染零变更）",
                    "render": "renders-r14b 四图字节复用（零变更）",
                    "guidance": "r15 指引+§4(iii) 接触性判据补可操作分辨条款"
                                "（方向=判定一致性，反放宽条款逐字保留）",
                },
            ],
        },
        "benefit_metrics": {
            "scope": "跨轮统一口径：全部=12 派次全口径（非代表配置子集）、与分型件"
                     "（abstain-typology-r13-r16.json）同法；单位=旗标条数",
            "M1_top_aggregate_abstain_rate": "top 全旗聚合弃权率=该轮 top 视 6 派次全部"
                                             "旗标中弃权旗占比（分型件 round_view "
                                             "{r}|top.abstain_rate 同法，6 位小数）",
            "M2_bottom_aggregate_abstain_rate": "bottom 全旗聚合弃权率（同法，round_view "
                                                "{r}|bottom）",
            "M3_blackdot_abstain_flags_rubric": "黑点族弃权旗数（rubric 口径=分型件 "
                                                "round_totals {r}.families."
                                                "existence_blackdot）",
            "M4_top_per_instance_rate_range": "top 逐实例弃权率极差=max−min（top-i1/i2/i3 "
                                              "三实例各自 6 派次全口径弃权率先四舍五入 "
                                              "6 位小数再取差，与 run 件 instances."
                                              "combined.abstain_rate 同源）",
        },
        "baselines_registered": {
            "unified_method_note": "数值由本件从盘上 abstain-typology-r13-r16.json（matrix）"
                                   "与 calibration-run-r16.json（instances/protocol）实测装载，"
                                   "与预注册期望值 fail-closed 比对（不符即 FAIL 不落盘），"
                                   "非手抄",
            "r16_baseline": {
                "round_id": "r16",
                "role": "主基线=零变更最新轮（guidance=r15 逐字复用、渲染 renders-r14b "
                        "字节复用、实例群重抽）",
                "M1_top_aggregate_abstain_rate": r16["M1"],
                "M2_bottom_aggregate_abstain_rate": r16["M2"],
                "M3_blackdot_abstain_flags_rubric": r16["M3"],
                "M4_top_per_instance_rate_range": r16["M4"],
                "loaded_from": {
                    "M1_M2_M3": "abstain-typology-r13-r16.json matrix.round_view "
                                "r16|top / r16|bottom + round_totals.r16.families."
                                "existence_blackdot",
                    "M4": f"calibration-run-r16.json instances top-i1/i2/i3 combined"
                          f"（实测 {x['per_inst_top_r16']}，先 6 位小数取率再取极差；"
                          "与分型件 cross_check_vs_runs r16|top-i* 逐实例相等交叉核对）",
                },
            },
            "r15_reference": {
                "round_id": "r15",
                "role": "参照轮（指引侧单变量轮；非主基线）",
                "M1_top_aggregate_abstain_rate": r15["M1"],
                "M2_bottom_aggregate_abstain_rate": r15["M2"],
                "M3_blackdot_abstain_flags_rubric": r15["M3"],
                "M3_caveat": "分型件 rubric 口径 r15=8；s59 dev-record prose 口径=7"
                             "（「r13 8→r14 14→r15 7→r16 12」在案）——本实验一律采用"
                             "分型件 rubric 口径，差异如实披露",
            },
            "drift_reference_note": f"r15→r16（同指引重复轮+渲染零变更）M1 变动 "
                                    f"|{r15['M1']}−{r16['M1']}|={x['drift_r15_r16']}"
                                    "（纯实例群重抽效应的实测方向性量级），为显著收益"
                                    "阈值 0.10 的历史幅度参照",
        },
        "guards": {
            "G1_bottom_courtyard_nonabstain_zero": {
                "rule": "bottom 三实例（i1/i2/i3）courtyard 类非弃权旗 0/0/0 维持",
                "baseline_evidence": "r16 在案：非弃权 courtyard 0/0/0 维持"
                                     "（round16-dev-record 实测在案证据，本件装载校验通过）",
                "scope": "轮级守门：任一实例非零→G1 破坏",
            },
            "G2_guard_ok": {
                "rule": "guard_ok=True 维持（无宽泛框出局：top 视非弃权旗标 frame_box_pct "
                        "几何门，面积比出局条目按 guard_channel 如实登记）",
                "baseline_evidence": "r16 hypothesis_test.measurement.guard_channel."
                                     "guard_ok=True（run-r16 实测装载校验通过）",
                "scope": "轮级守门：guard_ok=False→G2 破坏",
            },
            "G3_freeze_discipline": {
                "rule": "GT/阈值零改动、既往轮次字母不回写（全局纪律，贯穿 R17–R21）",
                "scope": "全局纪律、非轮级门槛；破坏即实验整体失效并如实记录",
            },
        },
        "comparison_rule": {
            "status": "FROZEN（先于 R17–R21 任何实验轮盲读冻结；冻结件=本计划件 "
                      "canonical 落盘；防事后择优）",
            "eligibility_gate": "仅 G1/G2 均满足的轮次进入排序；G1 或 G2 破坏的轮次不参与"
                                "排序（按 early_stop_rule 该轴出局）",
            "ordering": "按 (M1 升序, M2 升序, M3 升序, M4 升序) 字典序"
                        "（M1 最小者最优；同值依次比较 M2→M3→M4）",
            "significant_benefit_definition": "「显著收益」=相对 r16 基线 M1 绝对降幅 ≥0.10"
                                              "（阈值覆盖跨轮实例群漂移噪声的历史幅度，"
                                              f"参照 r15→r16 纯重抽变动 {x['drift_r15_r16']}）",
            "drift_confound_note": "跨轮比较的实例群漂移为已知混杂（r10 教训：各轮 12 派次"
                                   "实例独立重抽，跨轮 M1 差值可含纯重抽效应；r15→r16 同指引"
                                   "重复轮+渲染零变更仍实测漂移 "
                                   f"{x['drift_r15_r16']}）——本规则不消除该混杂，仅在"
                                   "阈值与多重对照中显式容忍",
            "descriptive_boundary": "本规则=development 域描述性边界工具，仅用于本实验内"
                                    "配置排序与收益陈述；非门、无字母语义、不凌驾 APR-0011 "
                                    "与阈值",
        },
        "combination_decision_rule": {
            "status": "FROZEN（先于 R17–R21 任何实验轮盲读冻结）",
            "i_stage2_combo_pair": "阶段1（R17/R18/R19）完成后，取过守门（G1/G2 均满足）"
                                   "轮次中 comparison_rule 排序最优的两轴做组合轮 R20"
                                   "（两轴变更同时施加；渲染/指引变更按各自轴定义合并）",
            "ii_full_combination": "若 R20 收益 ≥ 最优单轴（comparison_rule 排序不劣于"
                                   "最优单轴）且三轴均各自正收益（各自 M1 不劣于 r16 基线）"
                                   "→ 追加全组合轮 R21（三轴全组合）",
            "iii_non_additive_fallback": "若 R20 收益 < 最优单轴（两轴不可加）→ 采最优单轴、"
                                         "不再追加",
            "iv_final_selection": "最终「收益最大配置」=全部已测配置（本实验 R17–R21 各配置）"
                                  "中 comparison_rule 排序最优者，作为后续迭代基座；同分"
                                  "（四键全等）时取变量更少者（简约优先）",
            "preregistration_note": "R20/R21（如触发）仍各自走 prep-record 预注册（先于该轮"
                                    "盲读冻结）；本规则只决定「做不做、做哪个」，不预写结果",
        },
        "early_stop_rule": {
            "guard_failure_exit": "任一轮 G1/G2 破坏→该轴出局并如实记录（该轮 run/"
                                  "dev-record 照常落盘、字母裁决照常；「出局」仅指退出"
                                  "本实验后续组合与排序）",
            "strong_single_axis_shortcut": "阶段1 若最优单轴已达 M1 ≤0.60（远超显著收益）→ "
                                           "阶段2 仅做「最优单轴+次优单轴」一个组合轮验证"
                                           "可加性，不铺全组合（R21 不做）",
        },
        "limitations_note": {
            "drift_confound": "跨轮实例群漂移为已知混杂：各轮 12 派次实例独立重抽，跨轮指标"
                              "差值含纯重抽效应（r15→r16 M1 漂移 "
                              f"{x['drift_r15_r16']} 为实测参照；r10 教训在案），本实验"
                              "规则显式容忍而非消除该混杂",
            "m1_lexicographic_operationalization": "M1 字典序为操作化收益定义、非全局效用："
                                                   "它优先压 top 全旗弃权率，不直接加权 "
                                                   "recall/seed 匹配/GT 匹配与 bottom 侧",
            "axis3_disadvantage_accepted": "轴3 的收益本在 M4（弃权判定一致性）而非 M1，"
                                           "排序规则（M1 领衔）对其不利属已接受的操作化"
                                           "取舍——轴3 的收益判读须同时看 M4 的如实登记，"
                                           "不得仅以排序否定轴3",
        },
        "anchors": {
            "measured_at_build": "开工实测（本件构建时逐件 sha256_file，与预注册期望值 "
                                 "fail-closed 比对，不符即 FAIL 不落盘）",
            "inputs_sha256": {
                "abstain-typology-r13-r16.json": {
                    "sha256": x["measured"]["abstain-typology-r13-r16.json"],
                    "role": "三轴分型证据与基线 M1/M2/M3 装载源（分型件）",
                },
                "calibration-run-r16.json": {
                    "sha256": x["measured"]["calibration-run-r16.json"],
                    "role": "r16 基线 M4、协议版本与 guard_ok 装载源（run 件）",
                },
                "round16-dev-record.json": {
                    "sha256": x["measured"]["round16-dev-record.json"],
                    "role": "s59 prose 口径 r15=7 在案证据与 G1 基线 0/0/0 维持在案证据"
                            "（r16 dev-record）",
                },
                "observation-guidance-r15.md": {
                    "sha256": x["measured"]["observation-guidance-r15.md"],
                    "role": "R17–R19 指引基线（r15 指引；§4 量化判据 (iii) 接触性判据与 "
                            "§5A 渲染配色仪器注记在案）",
                },
            },
            "self": {
                "path": REL_OUT,
                "note": "本计划件自证（幂等）：idempotence.canonical_bytes_sha256="
                        "不含 idempotence 节的 canonical 字节哈希；同输入⇒byte-exact "
                        "同输出，重跑零覆写",
            },
        },
    }
    return doc


def _commit(path: Path, canonical: bytes) -> str:
    if path.exists():
        old = path.read_bytes()
        if old == canonical:
            return "IDEMPOTENT-SKIP（字节等同、零覆写）"
        _fail(f"refuse to overwrite existing file with different bytes: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical)
    return "CREATED"


def main() -> int:
    x = load_inputs()
    doc = build_doc(x)
    canonical = hashing.canonical_json_bytes(doc)
    doc["idempotence"] = {
        "note": "本件由 s61 以 canonical_json_bytes 重建；同输入⇒byte-exact 同输出",
        "canonical_bytes_sha256": hashing.sha256_bytes(canonical),
        "declared_date_constant": DECLARED_DATE,
    }
    canonical = hashing.canonical_json_bytes(doc)
    status = _commit(OUT, canonical)

    print(f"[s61] kind={KIND} declared_date={DECLARED_DATE} "
          f"evaluation_domain={EVALUATION_DOMAIN}")
    print("[s61] rules frozen: comparison_rule=(G1/G2 过守门→(M1↑,M2↑,M3↑,M4↑) 字典序；"
          "显著收益=M1 绝对降幅 ≥0.10)；combination_decision_rule="
          "(i) top2 轴组合 R20 →(ii) 收益≥最优单轴且三轴均正收益→R21 全组合/"
          "(iii) 不可加→采最优单轴/(iv) 全部已测配置排序最优+同分取变量更少者")
    print(f"[s61] commit: {status} path={REL_OUT}")
    print(f"[s61] canonical_bytes_sha256(excl idempotence)="
          f"{doc['idempotence']['canonical_bytes_sha256']}")
    print(f"[s61] file_sha256={hashing.sha256_file(str(OUT))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
