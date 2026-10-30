#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s69_calibration_r18_devrecord.py — R18 CLOSE 包 B：
round18-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律）。

R18=轴2 指引侧单变量轮（§5B 黑点中性仪器注记，axis-experiment-plan-
r17-r20 stage1 R18=A2_blackdot_instrument_annotation；用户 2026-09-09
「三条轴单独/组合/全组合尝试，选择收益最大的继续」指令操作化冻结件在
案）：渲染零变更=renders-r14b 四图字节复用（与 r14/r15/r16/r17 盲读同
一批文件）；判读指引=observation-guidance-r18.md（cadcb8f3，r15 基座
d5babc93 机械变换派生+§5B 黑点仪器注记新节=blackdot-probe-r18.json
探针证实事实的中性转录[F1/F2 confirmed、F3 identity_confirmed_blackdot_
indeterminate]：§2–§7 判据逐字承 r15、§5A 原文整体逐字保留、R18T/R18B
前缀随指引落盘固化）；GT/阈值/协议零变更（v1.1+v1.2 维持）；
instrument_change.changed=false。预注册假设（axis-plan-r18-blackdot-
note）三分判据轮后裁决=reject（唯一正式裁决）：
- (r) 支 M3 ≥10（注记未使黑点族回落）→ crit_reject_m3=True：M3（黑
  点族弃权旗数，分型件 rubric 口径；r13–r16 链 9/14/8/12 重放对拍逐一
  相等=口径忠实性证明）实测=13 ≥10（vs r16 基线 12 回升 1 条）⇒ 字母=
  reject——§5B 中性仪器注记未使黑点族负责任判定成立；转向轴3/组合轮；
- (s) 支 M3 ≤6=False（但附加门 M1=top 全旗聚合弃权率 20/31=0.645161
  ≤0.85 成立、G1/G2 维持）；(m) 支 M3 7–9=False、M1 0.85–0.862=False。
机制观察/度量教训单列不凌驾字母裁决：M1/M2 双双大幅改善（0.645161 vs
r16 基线 0.771429、0.684211 vs 0.857143；M1 绝对降幅 0.126268 超显著
收益阈值 0.10——跨轮实例群漂移混杂照旧声明、本轮为指引变更轮、改善
不能归因于「零变更」）；旗级 §5B 援引 0/13（身份已知后弃权主因转为
「已证实黑点与焊盘的接触贴近不可分辨」=§4(iii) 接触性问题而非存在性
问题——机制转移如实记录）；黑点转非弃权旗 3 条（r14–r17 同位黑点旗
全部弃权/判正常路径中首次出现非弃权报告路径）+黑点判正常派次 2（对照
r15=3/r16=2）=§5B 的行为效应存在但不足以压 M3；top 弃权分型=接触性
8+存在性 12+其他 0（r16 对照 11/15/1、r17 对照 8/14/0）。实验对照账
（axis-plan benefit_metrics 口径）：(M1,M2,M3,M4)=(0.645161,0.684211,
13,0.277778)，轴2 现居已测配置第一（按冻结 comparison_rule M1 升序
字典序：R18 0.645161 < R17 0.88；R19 未测）——如实记录、不预写阶段2
结论。守门 G1/G2 均 True 维持、不触发出局；GT 双口径 union 0/13、
agreement 0/13（r16 的 1/13 未再现=连续两轮零命中）；代表配置
（top-i3 唯一+bottom-i1 tie 按先序）joint not_met、连续=0；零旗标派
次=0（12 格全部≥1 旗，对照 r17 的 2 格）。

生成器纪律（s65 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-09"；
- 防覆写护栏：round18-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round18-dev-record.json 一件（s68 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s69_calibration_r18_devrecord.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"

# ---------------------------------------------------------------------------
# 声明常量（无 wall-clock）
# ---------------------------------------------------------------------------

DECLARED_DATE = "2026-09-09"
ROUND_ID = "2026-09-09-r18"
ROUND_LABEL = "r18"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round18_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R18 = "out/v3-tl2/calibration/calibration-run-r18.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_PREP_R18 = "out/v3-tl2/calibration/r18-prep-record.json"
REL_DEV_R17 = "out/v3-tl2/calibration/round17-dev-record.json"
REL_GUIDANCE_R18 = "out/v3-tl2/calibration/observation-guidance-r18.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_PROBE_R18 = "out/v3-tl2/calibration/blackdot-probe-r18.json"
REL_OUT = "out/v3-tl2/calibration/round18-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 主通道三分判据实测锚（写盘前 fail-closed 与 run-r18 盘上值逐一核对）
EXPECT_TOP_ABSTAIN_R18 = 20
EXPECT_TOP_FLAGS_R18 = 31
EXPECT_TOP_RATE_R18 = 0.645161
EXPECT_BOTTOM_ABSTAIN_R18 = 13
EXPECT_BOTTOM_FLAGS_R18 = 19
EXPECT_BOTTOM_RATE_R18 = 0.684211
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_M3_R18 = 13
EXPECT_M3_R16_BASELINE = 12
EXPECT_M3_CHAIN_R13_R16 = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
EXPECT_COURTYARD_NON_ABSTAIN = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_COUNTS = {"top-i1": 14, "top-i2": 8, "top-i3": 9,
                 "bottom-i1": 6, "bottom-i2": 6, "bottom-i3": 7}
EXPECT_ABSTAIN = {"top-i1": 9, "top-i2": 4, "top-i3": 7,
                  "bottom-i1": 5, "bottom-i2": 2, "bottom-i3": 6}
EXPECT_RATES = {"top-i1": 0.642857, "top-i2": 0.5, "top-i3": 0.777778,
                "bottom-i1": 0.833333, "bottom-i2": 0.333333,
                "bottom-i3": 0.857143}
EXPECT_R16_RATES = {"top-i1": 0.666667, "top-i2": 0.928571,
                    "top-i3": 0.666667, "bottom-i1": 1.0,
                    "bottom-i2": 0.8, "bottom-i3": 0.75}
EXPECT_TYPE_COUNTS = {"contact": 8, "existence": 12, "other_layer": 0}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 4, "bottom-i2": 2,
                                "bottom-i3": 4, "top-i1": 1,
                                "top-i2": 1, "top-i3": 1}
EXPECT_RUBRIC_COUNTS = {"contact": 8, "existence_blackdot": 13,
                        "existence_other": 12, "other": 0,
                        "semantic_confusion": 0}
# 实验对照账（axis-experiment-plan benefit_metrics 口径；M3 单位=旗标条数）
EXPECT_M1 = 0.645161
EXPECT_M2 = 0.684211
EXPECT_M4 = 0.277778
# axis-plan 在案 r16 基线四键（baselines_registered/benefit_metrics 口径）
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17 已测行（round17-dev-record 实测装载；排序现状对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s69-cal-r18-devrecord] FAIL: {msg}")


def _rel(rel: str) -> Path:
    return REPO / rel


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    with open(_rel(rel), encoding="utf-8") as f:
        return json.load(f)


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


# ---------------------------------------------------------------------------
# fail-closed 事实核对（所有入文数字先与盘上值对账）
# ---------------------------------------------------------------------------

def _courtyard_non_abstain_by_instance(run: dict, names=("bottom-i1",
                                                         "bottom-i2",
                                                         "bottom-i3")):
    out = {}
    for name in names:
        cnt = 0
        for st in ("applied", "prep1"):
            b = run["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        out[name] = cnt
    return out


def _courtyard_flags_total(run: dict, names=("bottom-i1", "bottom-i2",
                                             "bottom-i3")) -> int:
    cnt = 0
    for name in names:
        for st in ("applied", "prep1"):
            b = run["instances"][name]["states"][st]
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding")
    return cnt


def _view_abstain_aggregate(run: dict, view: str):
    names = [n for n in INSTANCE_ORDER if n.startswith(view)]
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run16: dict, prep: dict, dev17: dict,
                  probe: dict, guidance_sha: str, axis_sha: str) -> None:
    # ---- run-r18 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r18":
        _fail("run kind 不符")
    if (run["round_id"], run["round_label"], run["declared_date"],
            run["evaluation_domain"]) != (ROUND_ID, ROUND_LABEL,
                                          DECLARED_DATE, "development"):
        _fail("run 声明常量不符")
    ht = run["hypothesis_test"]
    if ht["hypothesis_id"] != "axis-plan-r18-blackdot-note":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "reject":
        _fail("verdict != reject")
    m = ht["measurement"]
    if (m["crit_reject_m3_ge_10"] is not True
            or m["crit_supported_m3_le_6"] is not False
            or m["crit_supported_m1_le_0_85"] is not True
            or m["crit_marginal_m3_7_9"] is not False
            or m["crit_marginal_m1_0_85_0_862"] is not False):
        _fail("三分判据布尔不符（(r) 是、(s)/(m) 否、M1 附加门成立）")
    if not m["letter_branch"].startswith("(r)"):
        _fail("落支应为 (r) 支")
    if m["verdict"] != "reject":
        _fail("measurement.verdict != reject")
    # 本轮实测（top 20/31、bottom 13/19）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R18, EXPECT_TOP_ABSTAIN_R18):
        _fail("top 聚合不符（20/31）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R18, EXPECT_BOTTOM_ABSTAIN_R18):
        _fail("bottom 聚合不符（13/19）")
    if m["top_abstain_rate_r18"] != EXPECT_TOP_RATE_R18 or \
            m["bottom_side_observation"]["bottom_abstain_rate_r18"] != \
            EXPECT_BOTTOM_RATE_R18:
        _fail("聚合弃权率不符")
    if "20/31" not in m["top_abstain_rate_r18_arithmetic"] or \
            "13/19" not in m["bottom_side_observation"][
                "bottom_abstain_rate_r18_arithmetic"]:
        _fail("聚合算式文本不符")
    # 整数交叉相乘复核（避免浮点）：M3=13≥10（reject 支）；
    # M1 附加门 20/31≤0.85 成立；M1 绝对降幅（27/35−20/31）≥0.10 成立
    if not (EXPECT_M3_R18 >= 10):
        _fail("M3 ≥10 复核不符")
    if at * 1_000_000 > 850_000 * ft:
        _fail("M1 附加门复核不符（应 20×10^6≤850000×31）")
    # (27/35−20/31)≥0.10 ⇔ (27×31−20×35)×10^6 ≥ 0.10×35×31×10^6
    if (27 * 31 - 20 * 35) * 1_000_000 < 100_000 * 35 * 31:
        _fail("M1 绝对降幅复核不符（应 ≥0.10）")
    # 基线双侧复算（同一聚合逻辑对 run-r16 内嵌输入重算）
    f16, a16 = _view_abstain_aggregate(run16, "top")
    if (f16, a16) != (35, 27) or \
            m["top_abstain_rate_r16_baseline_live"] != \
            EXPECT_TOP_R16_BASELINE_LIVE or \
            m["top_abstain_rate_r16_baseline_value"] != \
            EXPECT_TOP_R16_BASELINE_VALUE:
        _fail("top r16 基线复算不符（27/35）")
    fb16, ab16 = _view_abstain_aggregate(run16, "bottom")
    if (fb16, ab16) != (14, 12) or \
            m["bottom_side_observation"][
                "bottom_abstain_rate_r16_baseline_live"] != \
            EXPECT_BOTTOM_R16_BASELINE_LIVE or \
            m["bottom_side_observation"][
                "bottom_abstain_rate_r16_baseline_value"] != \
            EXPECT_BOTTOM_R16_BASELINE_VALUE:
        _fail("bottom r16 基线复算不符（12/14）")
    # M4 与 axis-plan 登记基线四键交叉核对
    if run["view_layer"]["top"]["abstain_rate_range"] != EXPECT_M4:
        _fail("M4=top 极差不符（0.277778）")
    if m["baseline_cross_check"]["axis_plan_r16_baseline_M1_M2_M3_M4"] != \
            EXPECT_R16_BASELINE_M1_M2_M3_M4:
        _fail("axis-plan r16 基线四键不符")
    # M3（分型件 rubric 口径）与 r13–r16 链重放对拍
    if m["m3_blackdot_abstain_flags_rubric_r18"] != EXPECT_M3_R18 or \
            m["m3_r16_baseline_registered"] != EXPECT_M3_R16_BASELINE or \
            m["m3_r16_baseline_live_replay"] != EXPECT_M3_CHAIN_R13_R16:
        _fail("M3 实测/基线/链重放不符（13、12、9/14/8/12）")
    # bottom 侧观察（improved 方向如实单列）与 courtyard 0/0/0
    bso = m["bottom_side_observation"]
    if (bso["bottom_abstain_flags_r18"], bso["bottom_abstain_count_r18"]) != \
            (19, 13) or bso["bottom_rate_direction_vs_r16"] != "improved" or \
            bso["bottom_courtyard_flags_total_r18"] != 0 or \
            bso["bottom_courtyard_non_abstain_by_instance_r18"] != \
            EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("bottom 侧观察不符（13/19、improved、courtyard 旗 0、非弃权 "
              "0/0/0）")
    cy18 = _courtyard_non_abstain_by_instance(run)
    cy16 = _courtyard_non_abstain_by_instance(run16)
    if cy18 != EXPECT_COURTYARD_NON_ABSTAIN or \
            cy16 != EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("courtyard 非弃权复算不符（r18/r16 均 0/0/0）")
    if _courtyard_flags_total(run) != 0 or _courtyard_flags_total(run16) != 2:
        _fail("bottom courtyard 旗总数不符（r18=0、r16=2）")
    # 守门通道（G1/G2 均维持；独立单列；early_stop 未触发）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not True:
        _fail("守门 G1/G2 应均维持 True")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["guards_ok"] is not True or \
            g12["axis_early_stop_triggered"] is not False or \
            g12["g2_geometry_gate_r17"] != 0 or \
            g12["g2_geometry_gate_r18"] != 0:
        _fail("守门通道不符（G2 0→0、early_stop 未触发）")
    ca = run["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r18_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_1_geometry_gate"][
                "r17_area_ratio_rejected_entries"]) != 0:
        _fail("几何门 0→0 复核不符")
    if len(ca["channel_2_category_gate"]["r18_category_mismatch_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r17_category_mismatch_entries"]) != 0:
        _fail("类别门 0→0 复核不符")
    if len(ca["view_gate_observations"]["r18_entries"]) != 0:
        _fail("视角门 r18=0 复核不符")
    # GT 双口径：union 0/13（r16 的 1/13 未再现）、agreement 0/13
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (0, 0, 13):
        _fail("双口径不符（union 0/13、agreement 0/13）")
    if dual["union"]["gt_ids"] != [] or dual["union"]["gt_recall_union"] != 0.0:
        _fail("union 应为零命中")
    if run["courtyard_tracking"]["courtyard_matches_r18"] != 0:
        _fail("courtyard 追踪 r18=0 不符")
    # 旗数/弃权率（逐实例）与 r16 对照
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN or \
            rates != EXPECT_RATES:
        _fail("逐实例旗数/弃权率不符")
    r16rates = {n: run16["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER}
    if r16rates != EXPECT_R16_RATES:
        _fail("r16 逐实例弃权率不符")
    # 零旗标派次=0（12 格全部≥1 旗；对照 r17 的 2 格）
    if run["reader"]["zero_flag_parts"]["parts"] != []:
        _fail("零旗标派次应为 0")
    # 代表配置与门
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (15, 12, 0.8, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0:
        _fail("联合门/连续计数不符")
    rep = run["representative_configuration"]["members"]
    if rep != {"top": "top-i3", "bottom": "bottom-i1"}:
        _fail("代表配置成员不符（top-i3+bottom-i1）")
    if run["representative_configuration"]["selection"]["top"][
            "tie"] is not False or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not True:
        _fail("代表配置 tie 记录不符（top 唯一、bottom tie 按先序）")
    # instrument_change.changed=false（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not False or \
            prep["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 应为 false")
    if prep["no_instrument_change"] is not True:
        _fail("prep no_instrument_change 应为 true")
    if len(run["instrument_change"]["changed_variables_registered"]) != 2 or \
            len(prep["changed_variables"]) != 2:
        _fail("变更变量登记不符（run 2 件、prep 2 件）")
    if prep["changed_variables"][0]["id"] != \
            "guidance-5b-blackdot-instrument-note" or \
            prep["changed_variables"][1]["id"] != "round-identity-sync":
        _fail("变更变量 id 不符（§5B 黑点仪器注记+轮次标识机械同步）")
    if run["instrument_change"]["axis_id"] != "A2_blackdot_instrument_annotation":
        _fail("轴2 声明不符")
    # 机制观察：top 分型/黑点分布/§5B 援引/判正常派次/rubric 族
    mo = ht["mechanism_observation"]
    ty = mo["top_abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            ty["top_abstain_flags_total"] != 20 or len(ty["rows"]) != 20:
        _fail("top 弃权构成分型不符（8/12/0、20 旗）")
    if ty["r16_reference_counts"] != {"contact": 11, "existence": 15,
                                      "other_layer": 1} or \
            ty["r17_reference_counts"] != {"contact": 8, "existence": 14,
                                           "other_layer": 0}:
        _fail("r16/r17 分型参照不符")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 13:
        _fail("黑点族 13 旗全弃权不符")
    if bdt["blackdot_to_non_abstain_count"] != 3 or \
            len(bdt["black_dot_non_abstain_flags"]) != 3:
        _fail("黑点转非弃权旗 3 条不符")
    if bdt["judged_normal_dispatches"]["count"] != 2 or \
            bdt["judged_normal_dispatches"]["sources"] != \
            ["applied-top-i1", "prep1-top-i2"]:
        _fail("黑点判正常派次 2 不符")
    fb5 = bdt["fiveb_citation_observation"]
    if fb5["flag_level_cite_count"] != 0 or \
            fb5["notes_level_cite_count"] != 1:
        _fail("§5B 援引观测不符（旗级 0/13、派次级 1/12）")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS or \
            rf["replay_proof"]["per_flag_total"] != 132 or \
            rf["replay_proof"]["blackdot_counts"] != EXPECT_M3_CHAIN_R13_R16:
        _fail("rubric 族计数/重放对拍不符")
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r18_measured"]["M1"] != EXPECT_M1 or \
            ecl["r18_measured"]["M2"] != EXPECT_M2 or \
            ecl["r18_measured"]["M3"] != EXPECT_M3_R18 or \
            ecl["r18_measured"]["M4"] != EXPECT_M4 or \
            ecl["r18_measured"]["M1_arithmetic"] != "20/31":
        _fail("实验对照账四元组不符")
    # 判据引用=prep-record 原文（逐字一致，共键比对；r18 判据键=6 键）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "marginal",
              "mechanism_observation_separate", "metric_lesson_separate",
              "reject", "supported"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 探针先决（axis-plan A2：无探针证实不得入轮）
    if probe["kind"] != "tl2_blackdot_probe_r18" or \
            probe["declared_date"] != DECLARED_DATE:
        _fail("探针件常量不符")
    if probe["overall_status"] != \
            "F1/F2 confirmed；F3 identity_confirmed_blackdot_indeterminate":
        _fail("探针 overall_status 不符")
    fam = {f["form_id"]: f["status"] for f in probe["families"]}
    if fam.get("F1_pad_interior_disc") != "confirmed" or \
            fam.get("F2_isolated_black_dot_pair") != "confirmed" or \
            fam.get("F3_isolated_pad_pair") != \
            "identity_confirmed_blackdot_indeterminate":
        _fail("探针三族状态不符")
    if "np_thru_hole" not in probe["section_5b_text"] or \
            "0.65mm" not in probe["section_5b_text"]:
        _fail("§5B 转录文本锚不符")
    # 指引机械变换派生锚（cadcb8f3 实测=r15 基座 d5babc93 派生+§5B 新节）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "mechanical_transform_derive" or \
            gr["derived"] != "observation-guidance-r18.md":
        _fail("guidance_reuse 机械变换派生声明不符")
    if gr["base_sha256"][:8] != "d5babc93":
        _fail("r15 基座锚不符")
    if gr["derived_sha256"] != guidance_sha or \
            guidance_sha != _sha(REL_GUIDANCE_R18):
        _fail("r18 指引实测 sha 与 cadcb8f3 锚不符")
    if gr["byte_size"] != {"base": 19878, "delta": 1648, "derived": 21526}:
        _fail("指引 byte_size 不符（19878→21526，delta 1648）")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致；探针锚一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R18):
        _fail("prep-record sha 实测与登记不符")
    anchors = gr["chain_anchors"]
    if anchors["axis_experiment_plan_frozen"]["sha256"] != \
            axis_sha or axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    if anchors["blackdot_probe_transcription_source"]["sha256"] != \
            _sha(REL_PROBE_R18):
        _fail("探针转录源实测 sha 与登记不符")
    # 轴计划比较规则（冻结）与 r16 基线锚
    plan = _json_load(REL_AXIS_PLAN)
    if "M1 升序" not in plan["comparison_rule"]["ordering"]:
        _fail("axis-plan 排序规则不符（M1 升序字典序）")
    if "G1/G2" not in plan["comparison_rule"]["eligibility_gate"]:
        _fail("axis-plan 资格门不符（G1/G2）")
    if "0.10" not in plan["comparison_rule"]["significant_benefit_definition"]:
        _fail("axis-plan 显著收益定义不符（绝对降幅 ≥0.10）")
    # r17 dev-record 先验链锚（实测）与 r17 已测行
    prior = [a for a in run["preregistration"]["frozen_artifacts"]
             if a["role"] == "r17_dev_record_prior_chain"]
    if len(prior) != 1 or prior[0]["sha256"] != _sha(REL_DEV_R17):
        _fail("round17-dev-record 先验链锚不符")
    if dev17["round_id"] != "2026-09-09-r17" or \
            dev17["hypothesis_test_i"]["verdict"] != "reject":
        _fail("r17 dev-record 先验件常量不符")
    if dev17["axis_experiment_ledger"]["this_round_measured"] != \
            EXPECT_R17_MEASURED:
        _fail("r17 dev-record 已测行四元组不符")


def build_dev_record() -> dict:
    """构建 round18-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R18)
    run16 = _json_load(REL_RUN_R16)
    prep = _json_load(REL_PREP_R18)
    dev17 = _json_load(REL_DEV_R17)
    probe = _json_load(REL_PROBE_R18)
    guidance_sha = _sha(REL_GUIDANCE_R18)
    axis_sha = _sha(REL_AXIS_PLAN)
    _verify_facts(run, run16, prep, dev17, probe, guidance_sha, axis_sha)

    ht = run["hypothesis_test"]
    m = ht["measurement"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]

    # 预注册链（逐件实测 sha，fail-closed 与 run 登记值交叉核对）
    chain = {}
    for item in run["preregistration"]["frozen_artifacts"]:
        got = _sha(item["path_rel"])
        if got != item["sha256"]:
            _fail(f"冻结工件实测 sha 与登记不符: {item['role']}")
        chain[item["role"]] = {"path_rel": item["path_rel"],
                               "sha256": got}

    run18_sha = _sha(REL_RUN_R18)

    # 联合评价趋势：r5–r17 行=round17-dev-record 在案行（冻结转录）；
    # r18 行=本轮 run 实测
    trend_rows = list(dev17["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r18",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R18, "sha256": run18_sha},
    })

    fc = run["reader"]["flag_count"]
    flag_count_by_file = {k: run["reader"]["parse"][k]["flag_count"]
                          for k in sorted(run["reader"]["parse"])}

    flag_production = {
        "abstain_by_instance": dict(fc["abstain_by_instance"]),
        "abstain_count": sum(fc["abstain_by_instance"].values()),
        "abstain_rate_all_flags": round(
            sum(fc["abstain_by_instance"].values()) / fc["total"], 6),
        "abstain_rate_all_flags_note": (
            "全旗标合计口径仅作附记（33/50=0.66，非弃权 17+弃权 33）；"
            "本轮预注册主通道=三分判据（(r) M3=13≥10 成立⇒reject——注记"
            "未使黑点族回落；(s) 附加门 M1=top 20/31=0.645161≤0.85 成立"
            "但不改判；bottom 全旗聚合弃权率 13/19=0.684211 为侧观察度量"
            "（M2，improved 方向））；实例层/视角层分列、全旗标合计非主"
            "通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 0.52381=0.857143−0.333333（bottom-i1/i2"
                     "/i3 = 0.833333/0.333333/0.857143）；top 极差 "
                     "0.277778=0.777778−0.5（top-i1/i2/i3=0.642857/0.5/"
                     "0.777778）；本轮零旗标派次=0（12 格全部≥1 旗，对照 "
                     "r17 的 2 格零旗标）——零旗格 view_check="
                     "not_applicable、不进弃权率分母（measurement_design "
                     "item 5 口径在案），弃权率全部有定义"),
            "top": run["view_layer"]["top"]["abstain_rate_range"],
        },
        "blind_discipline": run["reader"]["dispatch_discipline"],
        "flag_count_by_category": {k: dict(v)
                                   for k, v in fc["by_category"].items()},
        "flag_count_by_file": flag_count_by_file,
        "flag_count_by_instance": dict(fc["by_instance"]),
        "non_abstain_count": fc["total"] - sum(fc["abstain_by_instance"]
                                               .values()),
        "note": ("flag 全部通过 calibration fail-closed 校验（拒收清单为"
                 "空）；读者产物为冻结证据，本包零改动；派发模式=12 派次"
                 "（4 格×3 实例，两波次串行保序）；R18T/R18B 前缀随 r18 "
                 "指引 §6 落盘固化（r13→r15「随指引落盘固化」路径回归、"
                 "无需派发指令层覆盖，per r18-prep-record protocol_"
                 "amendment.naming）；flag_id 两板各自从头编号=读者实例输"
                 "出行为差异如实登记（编排侧按 (state, flag_id) 限定，跨"
                 "板同号不混淆）；v1.2 工具规约沿用 12/12 派次自述合规与"
                 "输出格式披露（12 件缩进格式冻结原始判读件、零改动直读）"
                 "如实登记为混杂因素披露，不作废"),
        "parse_rejections": list(run["parse_rejections"]),
        "raw_files": {k: dict(v) for k, v in
                      run["reader"]["raw_files"].items()},
        "reader_ids": dict(run["reader"]["reader_ids"]),
        "reader_instance_note": run["reader"]["reader_instance_note"],
        "reroute_by_instance": dict(fc["reroute_by_instance"]),
        "reroute_class_production": fc["reroute_class_production"],
    }

    diagnostic_result = {
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": (
            "representative_configuration（top-i3+bottom-i1，"
            "measurement_design item 4；top 中位 9 由 top-i3 唯一持有"
            "（14/8/9）无 tie；bottom 中位 6 为 bottom-i1/bottom-i2 tie"
            "（6/6/7）按先序取 bottom-i1 并如实注明）"),
        "criteria": [{"actual": c["actual"], "id": c["id"],
                      "met": c["met"], "threshold": c["threshold"]}
                     for c in comp["criteria"]],
        "gt_match_dual": {"agreement": dict(run["gt_match_dual"]["agreement"]),
                          "union": dict(run["gt_match_dual"]["union"])},
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "metric_ranges_instance": run["metric_ranges_instance"],
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "seed_metric_note": agg["seed_metric_note"],
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 6 派次全部旗标中弃权旗占比"
                "（6 位小数；本轮实测 20/31）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 13/19）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径；本轮实测 13、全弃权；主度量）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差=max−min（本轮实测 0.777778−0.5="
                "0.277778）",
            "scope": "跨轮统一口径：全部=12 派次全口径（非代表配置子集）、"
                     "与分型件同法；单位=旗标条数",
        },
        "cross_round_status": {
            "measured_rows": {
                "r17_axis1": dict(
                    dev17["axis_experiment_ledger"]["this_round_measured"]),
                "r18_axis2": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                              "M3": EXPECT_M3_R18, "M4": EXPECT_M4},
                "r19_axis3": "未测（stage1 待执行）",
            },
            "note": ("轴2 现居已测配置第一（按冻结 comparison_rule=(M1 升"
                     "序, M2 升序, M3 升序, M4 升序) 字典序：R18 M1="
                     "0.645161 < R17 M1=0.88；两轮 G1/G2 均满足=过资格门；"
                     "R19 未测）——如实记录、不预写阶段2 结论"
                     "（combination_decision_rule.preregistration_note："
                     "本规则只决定「做不做、做哪个」，不预写结果）"),
            "role": ("axis-plan 排序现状如实登记（comparison_rule 冻结规则"
                     "的已测行并列；R17 行=round17-dev-record 实测装载、"
                     "R18 行=本轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r18.json（981428dc…）盘上值"
            "装载（M1=20/31=0.645161 与 m.top_abstain_rate_r18、M2=13/19="
            "0.684211 与 bottom_side_observation、M3=13 与 black_dot_"
            "tracking（rubric 重放对拍 r13–r16 132 条弃权旗逐一相等）、M4="
            "0.277778 与 view_layer.top.abstain_rate_range 逐一相等，"
            "fail-closed），非手抄；axis-plan 在案 r16 基线四键 [0.771429, "
            "0.857143, 12, 0.261904] 与 run-r18 baseline_cross_check 交叉"
            "核对一致；M1 绝对降幅 0.771429−0.645161=0.126268 超显著收益"
            "阈值 0.10（跨轮实例群漂移混杂照旧声明、本轮为指引变更轮，改"
            "善不能归因于「零变更」；主度量=M3 未达）"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "R18 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "status": ("R18 实测 (M1,M2,M3,M4)=(0.645161, 0.684211, 13, "
                   "0.277778)；资格门=G1/G2 均满足→进入排序；轴2 现居已测"
                   "配置第一（如实记录）；字母与实验账背离（reject 但 M1/M2 "
                   "最优）照 frozen comparison_rule 执行——排序按 M1 字典"
                   "序、字母按预注册三分判据，两账分列互不改写；不预写阶段"
                   "2 结论（combination_decision_rule.preregistration_"
                   "note：本规则只决定「做不做、做哪个」，不预写结果）"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3_R18, "M4": EXPECT_M4},
    }

    directional_observation_vs_r16 = [
        ("R16→R18 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 沿用"
         "无新增版本：12/12 派次自述「未读取盘上任何其他文件」；R18T/R18B "
         "前缀随 r18 指引 §6 落盘固化=r13→r15 路径回归、无需派发层覆盖）；"
         "旗标 49→50（六实例旗数 top 8/8/9→14/8/9、bottom 4/3/5→6/6/7；"
         "非弃权 6→17、弃权 31→33）；全旗标合计弃权率 0.837838（31/37，附"
         "记口径）→0.66（33/50，附记口径）；预注册主通道三分判据：(r) M3 "
         "≥10 成立（crit_reject_m3=True，M3=13 vs r16 基线 12）；(s) M3 "
         "≤6 不成立且附加门 M1=20/31=0.645161≤0.85 成立；⇒字母裁决=reject"
         "（轴2 reject：§5B 中性仪器注记未使黑点族负责任判定成立；转向轴3"
         "/组合轮）；代表配置（top=top-i3：中位 9 唯一；bottom=bottom-i1："
         "中位 6 tie（6/6/7）按先序取、如实注明）弃权率 0.764706（13/17）"
         "→0.8（12/15）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.666667/"
         "0.928571/0.666667（r16，极差 0.261904）→0.642857/0.5/0.777778"
         "（r18，极差 0.277778=M4）——§5B 注记轮（渲染零变更=renders-r14b "
         "字节复用）下聚合落点 27/35=0.771429→20/31=0.645161（绝对降幅 "
         "0.126268 超计划件显著收益阈值 0.10=M1 双双改善之一；跨轮实例群"
         "漂移混杂照旧声明[r15→r16 纯重抽漂移 0.09064 在案参照]、本轮为"
         "指引变更轮、改善不能归因于「零变更」；M1 为 supported 附加门、"
         "主度量 M3 未达不改字母）；bottom 1.0/0.8/0.75（r16，极差 0.25）"
         "→0.833333/0.333333/0.857143（r18，极差 0.52381）——bottom 全旗"
         "聚合弃权率 12/14=0.857143→13/19=0.684211（improved 改善方向如"
         "实单列）；本轮零旗标派次=0（12 格全部≥1 旗，r17 的 2 格零旗标"
         "未再现；view_check=not_applicable 不进弃权率分母）。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r16 的 r12 以"
         "来首次逐实例命中（union 1/13=0.076923，R16T-001×GT-REVC-AP-6-"
         "R2LED2）在 r17/r18 连续两轮未再现——GT 条目层 union=0/13（0.0）、"
         "agreement=0/13（0.0）：单实例命中不稳定如实登记；代表配置 "
         "gt_recall_total 0.0（0/13）、seed_match_rate 0.0（0/1，诊断口"
         "径，禁称 precision/FPR）。bottom 19 旗（13 弃权+6 非弃权）零匹"
         "配属结构性：GT 13 条全部 side=top、bottom 无 GT 在案（gt-audit-"
         "r1：bottom GT=无源已关闭）⇒ bottom 旗标与 GT 匹配应为空，如实；"
         "top 非弃权旗 11 条与同态 GT 零 ≥0.5 containment 交叠或类别/视"
         "角门内零命中。"),
        ("通道归因（vs R17，预注册重放方法）：几何门面积比出局 0→0"
         "（guard_ok=True 独立单列、不构成 r18 字母裁决输入）；类别门 0→0"
         "（r16 在案 1 条 R16T-006 出局条目 r17/r18 连续零再现）；视角门 "
         "0→0（top 非弃权旗与同态 GT 零视角错位交叠；bottom 非弃权旗零匹"
         "配属结构性）。通道链自 r6：几何门 r6=1→r7=0→r8=0→r9=0→r10=0→"
         "r11=0→r12=0→r13=0→r14=1→r15=0→r16=0→r17=0→r18=0；类别门 r6=1→"
         "r7=0→r8=1→r9=0→r10=0→r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17="
         "0→r18=0。重放与 compare_v3 对拍一致。"),
        ("预注册假设（axis-plan-r18-blackdot-note）字母裁决=reject（落支="
         "(r) M3 ≥ 10（注记未使黑点族回落）——轴2 reject：§5B 中性仪器注"
         "记未使黑点族负责任判定成立；转向轴3/组合轮；r18-prep-record "
         "hypothesis_test.adjudication 判据原文执行；唯一正式裁决）。实"
         "测：M3（黑点族弃权旗数，分型件 rubric 口径）=13 vs r16 基线 12"
         "（rubric 机械套用：关键词表/优先级从 abstain-typology-r13-r16."
         "json 装载，r13–r16 132 条弃权旗重放对拍逐一相等后套用 r18，链值"
         "9/14/8/12 在案；基线=分型件 r16 实测装载交叉核对一致，不手工抄"
         "数）；(s) 支附加门 M1=top 全旗聚合弃权率 20/31=0.645161≤0.85 成"
         "立（6 位定点整数交叉相乘：20×10^6≤850000×31）但 M3 门=False 不"
         "改判；(m) 支 M3 7–9=False、M1 0.85–0.862=False。守门 G1（"
         "bottom courtyard 非弃权 0/0/0 维持）=维持、G2（guard_ok=True 维"
         "持，几何门 R17=0→R18=0）=维持——均独立单列，守门均维持、不触发"
         "出局（per axis-plan early_stop_rule）。"),
        ("机制观察单列（不凌驾）：(a) §5B 援引观测=旗级（location_evidence "
         "含「§5B」）0/13 条黑点弃权旗（非弃权黑点旗亦零）——13+3 条黑点"
         "旗的弃权/报告理由全部按 §2/§3A/§4 独立表述（与 §5B「不构成任何"
         "判据」的反指示声明一致）；派次级=1/12（applied-top-i1 notes「"
         "§5B 为仪器事实注记，本判读仍按 §4 判据独立执行，结论与注记来源"
         "一致」=黑点判正常路径援引）；(b) 机制转移如实记录：黑点身份已被 "
         "§5B 证实（探针 F1/F2 confirmed：封装内 2 个非电镀机械定位孔 "
         "np_thru_hole 0.65mm），但 13 条黑点弃权旗的 location_evidence "
         "多为「已证实黑点与焊盘接触贴近不可分辨」（如「孤立实心黑点紧邻"
         "胶囊形焊盘下缘」类表述）=§4(iii) 接触性问题而非存在性问题——"
         "「身份注记消解存在性弃权」假设被证伪：身份已知≠可负责任判定接"
         "触性；(c) 黑点转非弃权旗 3 条（applied-bottom-i2 R18B-001/002 "
         "非弃权报告+prep1-top-i3 R18T-001 按关注现象归兜底类报告——r14–"
         "r17 同位黑点旗全部弃权/判正常路径中首次出现非弃权报告路径）+黑"
         "点判正常派次 2 个（applied-top-i1+prep1-top-i2，对照 r15=3/"
         "r16=2）=§5B 的行为效应存在但不足以压 M3；(d) top 弃权构成分型="
         "接触性 11→8（r17）→8、存在性 15→14（r17）→12、其他 1→0（r17）"
         "→0（20 条逐旗摘录在案）；(e) 绿区语义化：bottom 6 派次中 5 派次"
         "按 §4(i) 空隙/翼瓣语义化路径、§5A 显式援引 1/6 派次（r16 的 6/6、"
         "r17 的 2/6 对照，实例自述异质性如实登记）。"),
        ("bottom 改善通道单列（M2=13/19=0.684211 vs r16 基线 12/14="
         "0.857143，improved 方向；不影响字母）：(1) 零旗标派次=0 个（12 "
         "格全部≥1 旗，对照 r17 的 2 格）；(2) 黑点族弃权旗（M3，分型件 "
         "rubric 口径）=13 条 vs r16=12（数量回升 1 条、方向性描述；top 3+"
         "bottom 10）；(3) 黑点转非弃权报告 2 条（bottom 侧）+黑点判正常"
         "对照；(4) bottom courtyard 类旗=0 条（r17 的 prep1-bottom-i3 "
         "R17B-001 courtyard 弃权旗未再现）——非弃权 courtyard 0/0/0 维持"
         "（G1，零旗标路径）。"),
        ("工具行为（协议侧 v1.2 沿用第七轮，如实入账）：R18 十二派次全部以 "
         "Read 工具直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何"
         "其他文件」（12/12 逐字摘录在案 reader_tool_evidence）；全部判读"
         "输入严格限于（指引+该 PNG），零 GT/零诊断/零探针件/零 legend（黑"
         "点探针链（blackdot-probe-r18.json）不进任何 reader 上下文）=非盲"
         "读违规；flag_id 两板各自从头编号=实例输出行为差异如实登记、编排"
         "侧按 (state, flag_id) 限定；跨轮实例不同+轮内实例差异=混杂因素照"
         "旧声明（reader_instance_note）。"),
        ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延续，零"
         "阈值改动零期望）：courtyard 类旗标 10 条（top 10+bottom 0）、弃"
         "权 5+非弃权 5——非弃权 courtyard 5 条零命中；命中链 r8=1→r9=0→"
         "r10=1→r11=3→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0（r16 的 "
         "R16T-001 命中 r17/r18 未再现）。reroute 类 3 条（非弃权报告 1+"
         "弃权 2，全部 applied-top-i1；r13 以来 reroute 类首条非弃权报告="
         "「折叠仅为局部段落而非整段规则周期形态」按 §3A 示例 c 收窄判据排"
         "除后报告；「等长|蛇形」旗级子串零命中——滥用型通道被动追踪=0；"
         "prep1-top-i2 notes 有「蛇形」一词=判刻意图形的正常判定援引、非旗"
         "标）；产量链 r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→"
         "r16=2→r17=1→r18=3。"),
    ]

    honest_conclusion = (
        "本轮（development 域，轴2 指引侧单变量轮（§5B 黑点中性仪器注记："
        "判读指引=observation-guidance-r18.md cadcb8f3[r15 基座 d5babc93 "
        "机械变换派生+§5B 新节=blackdot-probe-r18.json a49441ac 探针证实"
        "事实的中性转录：F1/F2 confirmed、F3 identity_confirmed_blackdot_"
        "indeterminate，探针先决满足 per axis-plan stage1 A2；§2–§7 判据"
        "逐字承 r15、§5A 原文整体逐字保留、反指示声明随 §5B 落盘、R18T/"
        "R18B 前缀随指引落盘固化]+渲染零变更=renders-r14b 四图字节复用+"
        "GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed="
        "false 已预注册；唯一实验变量=指引 §5B 注记；per axis-experiment-"
        "plan-r17-r20 冻结件[用户 2026-09-09 指令操作化]））12 派次 50 旗"
        "标中 33 弃权、17 非弃权：代表配置（top-i3 唯一+bottom-i1 tie 按"
        "先序取并如实注明）gt_recall=0.0（0/13）、seed_match_rate=0.0"
        "（0/1，诊断口径，禁称 precision/FPR）、abstain_rate=0.8（12/15），"
        "联合评价 not_met（gt_recall、seed_match_rate 与 abstain_rate 三"
        "项未达 APR-0011 暂行线；诊断对照，非采纳门；连续达标计数 0→0；GT "
        "条目层 union=0/13、agreement=0/13 双口径并列——r16 的 1/13 首命"
        "中 r17/r18 连续未再现=单实例命中不稳定如实）。预注册假设"
        "（axis-plan-r18-blackdot-note）裁决（按 r18-prep-record "
        "hypothesis_test.adjudication 三分判据）=reject（字母口径，唯一正"
        "式裁决）：主度量 M3（黑点族弃权旗数，分型件 rubric 口径）实测=13"
        "（vs r16 基线 12 回升 1 条），落支=(r) M3 ≥ 10（注记未使黑点族回"
        "落）——轴2 reject：§5B 中性仪器注记未使黑点族负责任判定成立；转"
        "向轴3/组合轮。rubric 机械套用：r13–r16 132 条弃权旗重放对拍逐一"
        "相等后套用 r18（口径忠实性证明）；(s) 支 M3 ≤6=False 但附加门 M1="
        "top 全旗聚合弃权率 20/31=0.645161≤0.85 成立（r16 基线=同一聚合逻"
        "辑对 run-r16 内嵌实例记录双侧复算 27/35=0.771429，live 重放与在案"
        "登记/axis-plan 锚交叉核对一致，不手工抄数）、M1 绝对降幅 0.126268"
        "≥0.10——但 M1 仅 supported 附加门、主度量 M3 未达，字母不改；(m) "
        "支未落。守门 G1（bottom courtyard 非弃权 0/0/0 维持）与 G2"
        "（guard_ok=True，几何门 0→0）均维持、不触发出局（axis-plan "
        "early_stop_rule）。机制观察单列（不影响字母）：M1/M2 双双大幅改"
        "善（M1=0.645161 vs r16 基线 0.771429、M2=13/19=0.684211 vs 12/14="
        "0.857143，双双 improved 方向；M1 绝对降幅 0.126268 超显著收益阈值"
        " 0.10；跨轮实例群漂移混杂照旧声明、本轮为指引变更轮、改善不能归因"
        "于「零变更」）；"
        "旗级 §5B 援引 0/13（身份已知后弃权主因转为「已证实黑点与焊盘的接"
        "触贴近不可分辨」=§4(iii) 接触性问题而非存在性问题——机制转移如实"
        "记录：「身份注记消解存在性弃权」假设被证伪，身份已知≠可负责任判"
        "定接触性）；黑点转非弃权旗 3 条（r14–r17 首现非弃权报告路径）+黑"
        "点判正常派次 2（对照 r15=3/r16=2）=§5B 的行为效应存在但不足以压 "
        "M3；top 弃权构成分型=接触性 8+存在性 12+其他 0（r16 对照 11/15/"
        "1、r17 对照 8/14/0）。实验对照账：本轮 (M1,M2,M3,M4)=(0.645161, "
        "0.684211, 13, 0.277778)（axis-plan benefit_metrics 口径实测装"
        "载），轴2 现居已测配置第一（R18 M1=0.645161 < R17 M1=0.88，按冻"
        "结 comparison_rule M1 升序字典序；两轮均过 G1/G2 资格门；R19 未"
        "测）——如实记录、不预写阶段2 结论；轴2 的 letter 与轴2 的实验账"
        "表现背离（reject 但 M1/M2 最优）——排序按冻结 comparison_rule 执"
        "行、字母按预注册三分判据执行，两账分列互不改写。注意：reject=预"
        "注册阈值命中方向的描述性结论、非因果证明——「正确测出无效同样是"
        "有效证据」；单轮 n=3、development 域只描述不断言；机制观察/度量"
        "教训单列、不凌驾不改写字母裁决；APR-0011 门（代表配置）与字母裁"
        "决分列不合并；本轮判据均为描述性边界、非门阈值（门零改动）。残余"
        "实例差异仍存（top 弃权率 0.642857/0.5/0.777778 极差 0.277778、"
        "bottom 0.833333/0.333333/0.857143 极差 0.52381；板内孤立焊盘对跨"
        "实例/跨板出口不同[非弃权报告/弃权/判正常不报告三出口]=判读语义歧"
        "义未穷尽）。bottom 19 旗（13 弃权+6 非弃权）零匹配属结构性（GT "
        "13 条全部 side=top，bottom GT 无源在案 gt-audit-r1）；本轮 12 格"
        "零旗标派次=0（全部有定义）。「系统性正常→不报告」通道 bottom 五"
        "派次使用（§4(i) 判读路径延续，摘录在案；applied-bottom-i3 为 §5A "
        "非图元路径）。工具行为混杂如实入账（12/12 派次自述「未读取盘上"
        "任何其他文件」；R18T/R18B 前缀随指引落盘固化；flag_id 两板各自从"
        "头编号=实例输出行为差异如实登记、编排侧按 (state, flag_id) 限"
        "定）；输出格式披露（12 件缩进格式冻结原始判读件、零改动直读）如"
        "实登记、均非盲读违规。GT 侧三候选经 gt-audit-r1 全部关闭（延续零"
        "改动，GT 侧不再有候选；r18 union 0/13 与 bottom GT 无源结构相"
        "容）。不做「能力已修复/已达成」类断言；in_calibrated_range 恒 "
        "False。本批证据按协议 v1 §4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r18-prep-record no_loosening_note：判据文"
         "本零改动、§2–§7 逐字承 r15[分段+substring 双重断言复核；§5A 原文"
         "整体逐字保留]；§5B 为仪器事实注记、非判据——不构成任何「应判正常"
         "/无需报告」的指示，不降低任何存在性、归类、定位或报告的责任门槛，"
         "注记不得被援引为判正常设计特征的依据——反放宽条款「仅因形态不熟"
         "悉、不确定其设计含义，不构成判为正常设计特征的理由」与三路出口显"
         "式化在 r18 指引 §4 内逐字保留；三分判据描述性边界与门分列）。"),
        ("R16 对照基线=calibration-run-r16.json（2c1f8265…，在案）；主度量 "
         "M3 基线=分型件 rubric 口径 12（r13–r16 链 9/14/8/12 重放对拍逐一"
         "相等后套用，不手工抄数）；supported 附加门 M1 基线=同一聚合逻辑对 "
         "run-r16 内嵌实例记录双侧复算（27/35=0.771429）；M1 绝对降幅 ≥0.10"
         "=计划件显著收益阈值（r15→r16 纯重抽漂移 0.09064 为历史幅度参照）；"
         "轮间对比只做方向性描述（跨轮实例群混杂照旧，per axis-plan "
         "comparison_rule.drift_confound_note 显式容忍；本轮为指引变更轮，"
         "M1/M2 改善不能归因于「零变更」）。"),
        ("通道归因方法：照抄 run-r15/run-r16/run-r17 channel_attribution 的"
         "重放口径（deviation_note 承接），R15/R16/R17/R18 均以内嵌输入确定"
         "性重放并与 compare_v3 对拍（run-r18 channel_attribution.method）；"
         "重放复现与在案登记一致（fail-closed）。"),
        ("读者实例行为披露如实记录：R18 十二派次 v1.2 规约自述合规（纯 Read "
         "直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 reading_"
         "notes 原文在案）；输出格式披露（12 件缩进格式冻结原始判读件、零改"
         "动直读）parse 校验全部通过。跨轮 reader 实例不同+轮内实例差异=混杂"
         "因素，每视角 n=3；本轮轮前评审=pre_round_review[探针先决 satisfied_"
         "by_probe_and_plan：s66 探针 F1/F2 confirmed+axis-plan 冻结]——§5B "
         "注记内容=探针证实事实的中性转录（blackdot-probe-r18.json "
         "section_5b_text 逐字转录在案），无探针证实则该轴不得入轮（axis-"
         "plan stage1 A2 原文）已满足。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=reject 维持不"
         "变（reject=注记未使黑点族回落的描述性边界结论、非因果证明——预注"
         "册描述性边界下的方向性记录；单轮 n=3 小样本方向性证据；主通道三分"
         "判据（M3 ≤6/M3 7–9/M3 ≥10+M1 附加门）与 APR-0011 门分开表述、互不"
         "凌驾：门联合评价（代表配置）=not_met 如实分列）；不得回溯改判既往"
         "轮次（r8–r17 字母裁决维持不变）。"),
        ("度量教训在案（供 R19 预注册参考、本轮不追溯适用）：跨轮实例群漂移混"
         "杂照旧声明（r15→r16 纯重抽漂移 0.09064 在案）；字母=预注册阈值命中"
         "与否的描述性结论（per r18-prep-record metric_lesson_separate）；实"
         "验对照账（axis_experiment_ledger）=axis-plan 冻结比较规则的 R18 行"
         "登记[(M1,M2,M3,M4)=(0.645161, 0.684211, 13, 0.277778)]，轴2 现居已"
         "测配置第一（R18 M1 < R17 M1=0.88；如实记录）——排序与组合决策待 "
         "R19 后按冻结规则执行、不预写结论（轴2 的 letter 与实验账背离=两账"
         "分列互不改写的在案先例）。"),
    ]

    next_iteration_targets = [
        ("按冻结计划推进 R19=轴3（判据侧：guidance-r19=r15 基座+§4(iii) 可"
         "操作分辨条款[方向=判定一致性；反放宽条款逐字保留]；渲染=r14b 字节"
         "复用）——指引侧单变量轮（axis-plan stage1 A3 原文；收益本在 M4[弃"
         "权判定一致性]、排序规则 M1 领衔对其不利属已接受的操作化取舍，判读"
         "须同时看 M4 如实登记，不得仅以排序否定轴3；r18 的 M3=13≥10 残余黑"
         "点弃权多为接触性=§4(iii) 议题的直接在案输入）。"),
        ("阶段2 组合轮按 axis-plan 冻结规则：已测 R17(M1=0.88)/R18(M1=0.645"
         "161)——R19 后取过守门轮次中排序最优两轴组合为 R20（若 R19 M1 不劣"
         "于 r16 基线 0.771429，R20 候选=R18+R19 轴；R18 轴=§5B 注记；组合轮"
         "须各自 prep-record 预注册后执行，不预写结论）。"),
        ("M1 改善归因悬置记录：R18 的 M1=0.645161（20/31）为超阈值收益（绝"
         "对降幅 0.126268≥0.10）但单轮单测，跨轮实例群漂移混杂照旧声明、本"
         "轮为指引变更轮——改善不能归因于「零变更」；组合轮 R20（若含 §5B）"
         "可作部分重复验证（部分重复≠独立重复、如实登记验证力度）。"),
        ("黑点接触性子问题移交：黑点族残余 13 条弃权主因=接触性（身份已明、"
         "旗级 §5B 援引 0/13；「已证实黑点与焊盘接触贴近不可分辨」=§4(iii) "
         "接触性问题而非存在性问题）——归入轴1/轴3 的 contact 议题账，不再"
         "单列黑点注记迭代（机制转移如实入账，供 R19 §4(iii) 可操作分辨条款"
         "设计参考）。"),
        ("留出集时机=开发线收敛（须用户拍板）：r18 字母=reject→轴2 注记假说"
         "证伪、收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未达"
         "成，不得写成已达成）；GT 侧维持全关闭声明延续（gt-audit-r1["
         "1f20554a…]三候选全部关闭，r9–r18 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r18 union 0/13[r16 的 1/13 在 r17/r18 "
         "连续未再现=单实例命中不稳定如实]、非新 GT）；in_calibrated_range "
         "恒 False 直到正式采纳（须人工批准）；达标证据仍须留出集"
         "（out/v3-tl2/holdout/HOLDOUT-PLAN.md a4b80193… 与 datasets/"
         "holdout-candidates-r1 在案）。"),
    ]

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": directional_observation_vs_r16,
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本轮为同域第 18 轮迭代（development 域轴2 指引侧单变量轮（黑点中"
        "性仪器注记 §5B，渲染零变更字节复用）：迭代轮不得冒充留出证据）。",
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev17["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r18 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r18 全旗标合计 33/50=0.66 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R17 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 与 abstain_rate 0.8>0.5 三项"
                         "未达暂行线；gt_count 13≥12 单分项入线）——GT 条目"
                         "层 union 口径 0/13=0.0 亦未达 0.75（r16 的 1/13 "
                         "在 r17/r18 连续未再现=单实例命中不稳定如实；双口"
                         "径与门分列如实）"),
            },
        },
        "kind": KIND,
        "next_iteration_targets": next_iteration_targets,
        "notes": notes,
        "preregistration_chain": chain,
        "preregistration_chain_note": (
            "预注册链（含哈希）：axis-experiment-plan-r17-r20.json"
            "（b6ec6467…，用户 2026-09-09「三条轴单独/组合/全组合尝试，选择"
            "收益最大的继续」指令操作化=预注册跨轮收益比较规则[comparison_"
            "rule]+组合决策规则，先于 R17–R21 任何实验轮盲读冻结防事后择优；"
            "stage1 R18=轴2 黑点中性仪器注记、探针先决=无探针证实不得入轮）"
            "→s66 探针证实（blackdot-probe-r18.json a49441ac…，F1/F2 "
            "confirmed[黑点=封装内 2 个非电镀机械定位孔 np_thru_hole 0.65mm"
            "+焊盘钻孔盘族]、F3 identity_confirmed_blackdot_indeterminate "
            "如实中性表述；§5B 转录源）→r18-prep-record.json（3fc054c4…，"
            "本轮预注册件，measurement_design 五条聚合口径与 hypothesis_"
            "test.adjudication 三分判据（M3 ≤6/M3 7–9/M3 ≥10+M1 附加门 "
            "0.85/0.862）先于盲读冻结；instrument_change.changed=false；"
            "changed_variables=[§5B 黑点仪器注记新节（guidance-5b-blackdot-"
            "instrument-note）+轮次标识机械同步（round-identity-sync），两"
            "件登记]；manipulated_factor=指引增补 §5B[唯一操纵因素]）→判读"
            "指引=observation-guidance-r18.md（cadcb8f3…，r15 基座 d5babc93"
            "…机械变换派生 mechanical_transform_derive：§2–§7 判据逐字保留"
            "[分段+substring 双重断言]、§5A 原文整体逐字保留+机械变换 "
            "edit_list 八件逐件登记[任务枚举+轮次标识同步+§5B 新节插入]；"
            "byte_size 19878→21526=delta 1648）→渲染零变更（renders-r14b 四"
            "图字节复用、与 r14/r15/r16/r17 盲读同一批文件[applied-top "
            "298bc620/applied-bottom d7284259/prep1-top b2f84524/prep1-"
            "bottom d7284259，bottom 两图字节同；witness-r14b b63771f9 在"
            "案]）→12 次盲读→run-r18（981428dc…，本链执行落盘）；GT 重投影"
            "沿用 derivation-log-r5.json（62343380…）零新派生（GT 全部 "
            "side=top；指引变更不改 GT 冻结纪律）；GT 冻结纪律：轮后未增删"
            "改；gt-audit-r1（1f20554a…）结论维持 GT 零改动（三候选关闭，"
            "gt_audit_reference 在案）"),
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域轴2 指引侧单变量轮（第十八轮）：渲染零变更="
            "renders-r14b 四图字节复用（与 r14/r15/r16/r17 盲读同一批文件；"
            "no_instrument_change=true）+判读指引=observation-guidance-r18"
            ".md（cadcb8f3 实测锚，r15 基座 d5babc93 机械变换派生 "
            "mechanical_transform_derive：§2–§7 判据逐字保留[分段+substring"
            " 双重断言复核]、§5A 原文整体逐字保留、§5B 黑点中性仪器注记新节"
            "=blackdot-probe-r18.json a49441ac 探针证实事实的中性转录[F1/F2 "
            "confirmed、F3 identity_confirmed_blackdot_indeterminate；仪器"
            "事实非判据、反指示声明随节落盘、不降低任何责任门槛]；R18T/R18B "
            "前缀随指引 §6 落盘固化）+GT 集/协议阈值与度量版本/比较器常量零"
            "改动（GT 重投影沿用 derivation-log-r5——零新派生；gt-audit-r1 "
            "三候选关闭结论延续）；协议 v1.1+v1.2 维持无新增版本；instrument"
            "_change.changed=false 已预注册（changed_variables=[§5B 黑点仪"
            "器注记+轮次标识机械同步]；轴=axis-plan stage1 R18="
            "A2_blackdot_instrument_annotation）；检验假设 axis-plan-r18-"
            "blackdot-note（判据=r18-prep-record.json hypothesis_test."
            "adjudication 三分判据 M3 ≤6 supported/[M3 7–9 或 M1 0.85–0.862]"
            " marginal/M3 ≥10 reject+M1 附加门，轮后如实执行：字母裁决唯一"
            "正式+机制观察/度量教训单列；守门 G1/G2 独立单列，任一破坏→轴2 "
            "按 plan early_stop_rule 出局）；主通道三分判据与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独立计算、互不凌驾、分"
            "开表述；measurement_design 五条聚合口径先于盲读冻结；跨轮收益"
            "比较按 axis-plan 冻结规则（R18 行见 axis_experiment_ledger："
            "轴2 现居已测配置第一、如实记录、不预写阶段2 结论）；按协议 "
            "v1 §4，迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R18, "sha256": run18_sha},
        "schema_version": SCHEMA_VERSION,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s69-cal-r18-devrecord] round18-dev-record: {status}")
    print(f"[s69-cal-r18-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch={dev['hypothesis_test_i']['measurement'][
              'letter_branch']}")
    print(f"[s69-cal-r18-devrecord] 三分判据: (r) M3=13≥10 成立（vs r16 基线 "
          f"12，rubric 链 9/14/8/12 重放对拍）；(s) M3≤6 不成立+附加门 M1 "
          f"20/31=0.645161≤0.85 成立；(m) 未落 ⇒ reject（轴2 reject，转向轴"
          f"3/组合轮）")
    print(f"[s69-cal-r18-devrecord] 守门: G1=维持（bottom courtyard 非弃权 "
          f"0/0/0，零旗标路径）、G2=维持（几何门 0→0，guard_ok=True）→不触"
          f"发出局")
    print(f"[s69-cal-r18-devrecord] 机制观察: M1/M2 双改善[0.645161/0.684211 "
          f"vs 0.771429/0.857143，降幅 0.126268 超阈值 0.10；漂移混杂照旧、"
          f"指引变更轮不归因零变更]；旗级 §5B 援引 0/13[机制转移=接触性问题]；"
          f"黑点转非弃权 3+判正常派次 2；top 分型 8/12/0")
    print(f"[s69-cal-r18-devrecord] 实验对照账: (M1,M2,M3,M4)=(0.645161, "
          f"0.684211, 13, 0.277778)；轴2 现居已测配置第一（R18 0.645161 < "
          f"R17 0.88，M1 升序字典序；不预写阶段2 结论）")
    print(f"[s69-cal-r18-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s69-cal-r18-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0")
    print(f"[s69-cal-r18-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s69-cal-r18-devrecord] R18 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=reject 唯一正式；机制观察/度量教训单列不凌驾；"
          "in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
