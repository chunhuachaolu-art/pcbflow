#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s65_calibration_r17_devrecord.py — R17 CLOSE 包 B：
round17-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律）。

R17=轴1 仪器轮（渲染分辨率倍增，axis-experiment-plan-r17-r20 stage1
R17=A1_render_resolution_x2；用户 2026-09-09「三条轴单独/组合/全组合
尝试，选择收益最大的继续」指令操作化冻结件在案）：仪器变更=renders-r17
四图全新渲染（dpi 640→1280、像素数×4；framing 预注册 a1084c14→witness
见证 e979bec2）；判读指引=observation-guidance-r17.md（07c520be，r15
基座 d5babc93 机械变换派生：§2–§7 判据逐字保留、§5A 描述性同步[橙
326460/绿 903366 px 仪器事实]、R17T/R17B 前缀随指引落盘固化）；GT/
阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed=true 已
预注册。预注册假设（axis-plan-r17-resolution-double）三分判据轮后裁
决=reject（唯一正式裁决）：
- (a) 支 M1=top 全旗聚合弃权率 ≤0.671429（r16 零变更基线 0.771429
  绝对降幅 ≥0.10=计划件显著收益阈值）→ crit_a=False；
- (b) 支 M1 ≥0.771429（不优于零变更基线）→ crit_b=True ⇒ 字母=
  reject——轴1 证伪：分辨率非瓶颈（或视觉编码器尺寸上限抵消增益，
  机制观察须记录读者实际可见细节的自述）；转向轴2/轴3。
机制观察/度量教训单列不凌驾字母裁决：呈现尺寸自述 4/12 派次（约
1000px×3+约 1500px×1）vs 仪器像素界 4009/4010 px——呈现端缩放截断
像素增益的机制候选（如实单列、不断言）；1280 新细节旗 5 条（top 弃权
4+bottom 非弃权 1+判正常对照 2）；M2=bottom 9/12=0.75 vs r16 基线
12/14=0.857143（improved 方向单列；零旗标派次 2[prep1-bottom-i1/i2，
r13–r16 无先例]+黑点族 8 vs r16 12+bottom courtyard 旗 1 全弃权）；M3=
黑点族 8 旗全弃权；M4=top 逐实例弃权率极差 0.333333。实验对照账
（axis-plan benefit_metrics 口径）：(M1,M2,M3,M4)=(0.88,0.75,8,
0.333333)，R17 在三单轴中的排序位置待 R18/R19 后按冻结规则比较——
不预写结论。守门 G1/G2 均 True 维持、不触发出局；GT 双口径 union
0/13（r16 的 1/13 未复现=单实例命中不稳定如实）、agreement 0/13；代
表配置（top-i1 tie 按先序+bottom-i1 唯一）joint not_met、连续=0。

生成器纪律：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-09"；
- 防覆写护栏：round17-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round17-dev-record.json 一件（s64 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s65_calibration_r17_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-09-r17"
ROUND_LABEL = "r17"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round17_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R17 = "out/v3-tl2/calibration/calibration-run-r17.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_PREP_R17 = "out/v3-tl2/calibration/r17-prep-record.json"
REL_DEV_R16 = "out/v3-tl2/calibration/round16-dev-record.json"
REL_GUIDANCE_R17 = "out/v3-tl2/calibration/observation-guidance-r17.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_OUT = "out/v3-tl2/calibration/round17-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 主通道三分判据实测锚（写盘前 fail-closed 与 run-r17 盘上值逐一核对）
EXPECT_TOP_ABSTAIN_R17 = 22
EXPECT_TOP_FLAGS_R17 = 25
EXPECT_TOP_RATE_R17 = 0.88
EXPECT_BOTTOM_ABSTAIN_R17 = 9
EXPECT_BOTTOM_FLAGS_R17 = 12
EXPECT_BOTTOM_RATE_R17 = 0.75
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_COURTYARD_NON_ABSTAIN = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_COUNTS = {"top-i1": 8, "top-i2": 8, "top-i3": 9,
                 "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 5}
EXPECT_ABSTAIN = {"top-i1": 8, "top-i2": 8, "top-i3": 6,
                  "bottom-i1": 3, "bottom-i2": 2, "bottom-i3": 4}
EXPECT_RATES = {"top-i1": 1.0, "top-i2": 1.0, "top-i3": 0.666667,
                "bottom-i1": 0.75, "bottom-i2": 0.666667, "bottom-i3": 0.8}
EXPECT_R16_RATES = {"top-i1": 0.666667, "top-i2": 0.928571,
                    "top-i3": 0.666667, "bottom-i1": 1.0,
                    "bottom-i2": 0.8, "bottom-i3": 0.75}
EXPECT_TYPE_COUNTS = {"contact": 8, "existence": 14, "other_layer": 0}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 2, "bottom-i2": 2, "bottom-i3": 2,
                                "top-i1": 1, "top-i2": 1, "top-i3": 0}
# 实验对照账（axis-experiment-plan benefit_metrics 口径；M3 单位=旗标条数）
EXPECT_M1 = 0.88
EXPECT_M2 = 0.75
EXPECT_M3 = 8
EXPECT_M4 = 0.333333
# axis-plan 在案 r16 基线四键（baselines_registered/benefit_metrics 口径）
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]


def _fail(msg: str) -> None:
    raise SystemExit(f"[s65-cal-r17-devrecord] FAIL: {msg}")


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


def _verify_facts(run: dict, run16: dict, prep: dict, dev16: dict,
                  guidance_sha: str, axis_sha: str) -> None:
    # ---- run-r17 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r17":
        _fail("run kind 不符")
    if (run["round_id"], run["round_label"], run["declared_date"],
            run["evaluation_domain"]) != (ROUND_ID, ROUND_LABEL,
                                          DECLARED_DATE, "development"):
        _fail("run 声明常量不符")
    ht = run["hypothesis_test"]
    if ht["hypothesis_id"] != "axis-plan-r17-resolution-double":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "reject":
        _fail("verdict != reject")
    m = ht["measurement"]
    if (m["crit_a_supported_le_0.671429"] is not False
            or m["crit_b_reject_ge_0.771429"] is not True):
        _fail("三分判据布尔不符（(a) 否、(b) 是）")
    if not m["letter_branch"].startswith("(b)"):
        _fail("落支应为 (b) 支")
    if m["verdict"] != "reject":
        _fail("measurement.verdict != reject")
    # 本轮实测（top 22/25、bottom 9/12）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R17, EXPECT_TOP_ABSTAIN_R17):
        _fail("top 聚合不符（22/25）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R17, EXPECT_BOTTOM_ABSTAIN_R17):
        _fail("bottom 聚合不符（9/12）")
    if m["top_abstain_rate_r17"] != EXPECT_TOP_RATE_R17 or \
            m["bottom_side_observation"]["bottom_abstain_rate_r17"] != \
            EXPECT_BOTTOM_RATE_R17:
        _fail("聚合弃权率不符")
    if "22/25" not in m["top_abstain_rate_r17_arithmetic"] or \
            "9/12" not in m["bottom_side_observation"][
                "bottom_abstain_rate_r17_arithmetic"]:
        _fail("聚合算式文本不符")
    # (a) 否/(b) 是的整数交叉相乘复核（避免浮点）：22/25<0.671429 不成立
    # 且 22/25≥0.771429 成立
    if (at * 1_000_000 <= 671429 * ft) or (at * 1_000_000 < 771429 * ft):
        _fail("整数交叉相乘复核不符（应 22×10^6>671429×25 且 "
              "22×10^6≥771429×25）")
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
        _fail("M4=top 极差不符（0.333333）")
    if m["baseline_cross_check"]["axis_plan_r16_baseline_M1_M2_M3_M4"] != \
            EXPECT_R16_BASELINE_M1_M2_M3_M4:
        _fail("axis-plan r16 基线四键不符")
    # bottom 侧观察（improved 方向如实单列）与 courtyard 0/0/0
    bso = m["bottom_side_observation"]
    if (bso["bottom_abstain_flags_r17"], bso["bottom_abstain_count_r17"]) != \
            (12, 9) or bso["bottom_rate_direction_vs_r16"] != "improved" or \
            bso["bottom_courtyard_flags_total_r17"] != 1 or \
            bso["bottom_courtyard_non_abstain_by_instance_r17"] != \
            EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("bottom 侧观察不符（9/12、improved、courtyard 旗 1、非弃权 "
              "0/0/0）")
    cy17 = _courtyard_non_abstain_by_instance(run)
    cy16 = _courtyard_non_abstain_by_instance(run16)
    if cy17 != EXPECT_COURTYARD_NON_ABSTAIN or \
            cy16 != EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("courtyard 非弃权复算不符（r17/r16 均 0/0/0）")
    if _courtyard_flags_total(run) != 1 or _courtyard_flags_total(run16) != 2:
        _fail("bottom courtyard 旗总数不符（r17=1、r16=2）")
    # 守门通道（G1/G2 均维持；独立单列；early_stop 未触发）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not True:
        _fail("守门 G1/G2 应均维持 True")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["guards_ok"] is not True or \
            g12["axis_early_stop_triggered"] is not False or \
            g12["g2_geometry_gate_r16"] != 0 or \
            g12["g2_geometry_gate_r17"] != 0:
        _fail("守门通道不符（G2 0→0、early_stop 未触发）")
    ca = run["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r17_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_1_geometry_gate"][
                "r16_area_ratio_rejected_entries"]) != 0:
        _fail("几何门 0→0 复核不符")
    if len(ca["channel_2_category_gate"]["r17_category_mismatch_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r16_category_mismatch_entries"]) != 1:
        _fail("类别门 1→0 复核不符")
    if len(ca["view_gate_observations"]["r17_entries"]) != 0:
        _fail("视角门 r17=0 复核不符")
    # GT 双口径：union 0/13（r16 的 1/13 未复现）、agreement 0/13
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (0, 0, 13):
        _fail("双口径不符（union 0/13、agreement 0/13）")
    if dual["union"]["gt_ids"] != [] or dual["union"]["gt_recall_union"] != 0.0:
        _fail("union 应为零命中")
    if run["courtyard_tracking"]["courtyard_matches_r17"] != 0:
        _fail("courtyard 追踪 r17=0 不符")
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
    # 零旗标派次 2（r13–r16 无先例）
    zfp = [(p["state"] + "-" + p["instance"])
           for p in run["reader"]["zero_flag_parts"]["parts"]]
    if zfp != ["prep1-bottom-i1", "prep1-bottom-i2"]:
        _fail("零旗标派次不符（prep1-bottom-i1/prep1-bottom-i2）")
    # 代表配置与门
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (12, 11, 0.916667, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0:
        _fail("联合门/连续计数不符")
    rep = run["representative_configuration"]["members"]
    if rep != {"top": "top-i1", "bottom": "bottom-i1"}:
        _fail("代表配置成员不符（top-i1+bottom-i1）")
    if run["representative_configuration"]["selection"]["top"][
            "tie"] is not True or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not False:
        _fail("代表配置 tie 记录不符（top tie 按先序、bottom 唯一）")
    # instrument_change.changed=true（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not True or \
            prep["instrument_change"]["changed"] is not True:
        _fail("instrument_change.changed 应为 true")
    if prep["no_instrument_change"] is not False:
        _fail("prep no_instrument_change 应为 false")
    if len(run["instrument_change"]["changed_variables_registered"]) != 3 or \
            len(prep["changed_variables"]) != 3:
        _fail("变更变量登记不符（run 3 件、prep 3 件）")
    if prep["changed_variables"][0]["id"] != "render-resolution-x2-r17" or \
            prep["changed_variables"][1]["id"] != \
            "guidance-5a-descriptive-px-sync" or \
            prep["changed_variables"][2]["id"] != "round-identity-sync":
        _fail("变更变量 id 不符（主变量+§5A px 同步+轮次标识机械同步）")
    if prep["instrument_change"]["axis_id"] != "A1_render_resolution_x2" or \
            prep["instrument_change"]["renders"][0]["match"] is not True:
        _fail("轴1 声明/renders-r17 见证 match 不符")
    # 机制观察：top 分型/黑点分布/呈现尺寸/新细节旗
    mo = ht["mechanism_observation"]
    ty = mo["top_abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            ty["top_abstain_flags_total"] != 22 or len(ty["rows"]) != 22:
        _fail("top 弃权构成分型不符（8/14/0、22 旗）")
    if ty["r16_reference_counts"] != {"contact": 11, "existence": 15,
                                      "other_layer": 1}:
        _fail("r16 分型参照不符（11/15/1）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 8:
        _fail("黑点族 8 旗全弃权不符")
    if "4 派次判正常" not in bdt["notes_normal_dispositions"]:
        _fail("黑点族 4 派次判正常不符")
    psm = mo["presentation_size_mechanism_observation"]
    if psm["counts"]["dispatches_with_px_size_self_report"] != 4 or \
            psm["counts"]["instrument_png_image_wh"] != {
                "applied-top": [4009, 4009], "applied-bottom": [4010, 4009],
                "prep1-top": [4009, 4009], "prep1-bottom": [4010, 4009]}:
        _fail("呈现尺寸机制观察不符（4/12 自述、仪器 4009/4010）")
    ndf = mo["top_new_detail_flags_1280"]["counts"]
    if (ndf["new_detail_flags_total"], ndf["new_detail_top_abstain"],
            ndf["new_detail_bottom_non_abstain"],
            ndf["notes_normal_counterparts"]) != (5, 4, 1, 2):
        _fail("1280 新细节旗不符（5=4+1+2 对照）")
    # 判据引用=prep-record 原文（逐字一致，共键比对）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "guards", "marginal",
              "mechanism_observation_separate", "metric_lesson_separate",
              "reject", "supported"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引机械变换派生锚（07c520be 实测=r15 基座 d5babc93 派生）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "mechanical_transform_derive" or \
            gr["derived"] != "observation-guidance-r17.md":
        _fail("guidance_reuse 机械变换派生声明不符")
    if gr["base_sha256"] != gr["chain_anchors"][
            "base_sha256_prefix_expected"] and \
            gr["base_sha256"][:8] != "d5babc93":
        _fail("r15 基座锚不符")
    if gr["derived_sha256"] != guidance_sha or \
            guidance_sha != _sha(REL_GUIDANCE_R17):
        _fail("r17 指引实测 sha 与 07c520be 锚不符")
    if gr["byte_size"] != {"base": 19878, "derived": 19959, "delta": 81}:
        _fail("指引 byte_size 不符（19878→19959，delta 81）")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R17):
        _fail("prep-record sha 实测与登记不符")
    if gr["chain_anchors"]["axis_experiment_plan_frozen"]["sha256"] != \
            axis_sha or axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    # 轴计划比较规则（冻结）与 r16 基线锚
    plan = _json_load(REL_AXIS_PLAN)
    if "M1 升序" not in plan["comparison_rule"]["ordering"]:
        _fail("axis-plan 排序规则不符（M1 升序字典序）")
    if "G1/G2" not in plan["comparison_rule"]["eligibility_gate"]:
        _fail("axis-plan 资格门不符（G1/G2）")
    if "0.10" not in plan["comparison_rule"]["significant_benefit_definition"]:
        _fail("axis-plan 显著收益定义不符（绝对降幅 ≥0.10）")
    # r16 dev-record 先验链锚（实测）
    prior = [a for a in run["preregistration"]["frozen_artifacts"]
             if a["role"] == "r16_dev_record_prior_chain"]
    if len(prior) != 1 or prior[0]["sha256"] != _sha(REL_DEV_R16):
        _fail("round16-dev-record 先验链锚不符")
    if dev16["round_id"] != "2026-09-08-r16" or \
            dev16["hypothesis_test_i"]["verdict"] != "inconclusive":
        _fail("r16 dev-record 先验件常量不符")


def build_dev_record() -> dict:
    """构建 round17-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R17)
    run16 = _json_load(REL_RUN_R16)
    prep = _json_load(REL_PREP_R17)
    dev16 = _json_load(REL_DEV_R16)
    guidance_sha = _sha(REL_GUIDANCE_R17)
    axis_sha = _sha(REL_AXIS_PLAN)
    _verify_facts(run, run16, prep, dev16, guidance_sha, axis_sha)

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

    run17_sha = _sha(REL_RUN_R17)

    # 联合评价趋势：r5–r16 行=round16-dev-record 在案行（冻结转录）；
    # r17 行=本轮 run 实测
    trend_rows = list(dev16["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r17",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R17, "sha256": run17_sha},
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
            "全旗标合计口径仅作附记（31/37=0.837838，非弃权 6+弃权 31）；"
            "本轮预注册主通道=三分判据（(a) M1=top ≤0.671429（r16 零变更"
            "基线 27/35=0.771429 绝对降幅 ≥0.10）不成立；(b) M1 ≥0.771429"
            "（不优于零变更基线）成立⇒reject）；bottom 全旗聚合弃权率 "
            "9/12=0.75 为侧观察度量（M2，improved 方向）；实例层/视角层"
            "分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 0.133333=0.8−0.666667（bottom-i1/i2/i3 "
                     "= 0.75/0.666667/0.8）；top 极差 0.333333=1.0−"
                     "0.666667（top-i1/i2 双实例全弃权 8/8、top-i3 6/9="
                     "0.666667 独扛全部 3 条 top 非弃权旗）；本轮首现 2 个"
                     "零旗标派次（prep1-bottom-i1/prep1-bottom-i2，逐件核"
                     "实 flags=[]，r13–r16 无先例）——零旗格 view_check="
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
                 "（4 格×3 实例，两波次串行保序）；R17T/R17B 前缀随 r17 "
                 "指引 §6 落盘固化（r13→r15「随指引落盘固化」路径回归、"
                 "无需派发指令层覆盖，per r17-prep-record protocol_"
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
            "representative_configuration（top-i1+bottom-i1，"
            "measurement_design item 4；top 中位 8 为 top-i1/top-i2 tie "
            "（8/8/9）按先序取 top-i1 并如实注明；bottom 中位 4 由 "
            "bottom-i1 唯一持有（4/3/5）无 tie）"),
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
                "（6 位小数；本轮实测 22/25）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 9/12）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径；本轮实测 8、全弃权）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差=max−min（本轮实测 1.0−0.666667="
                "0.333333）",
            "scope": "跨轮统一口径：全部=12 派次全口径（非代表配置子集）、"
                     "与分型件同法；单位=旗标条数",
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r17.json（d444c4a5…）盘上值"
            "装载（M1=22/25=0.88 与 m.top_abstain_rate_r17、M2=9/12=0.75 "
            "与 bottom_side_observation、M3=8 与 black_dot_tracking、M4="
            "0.333333 与 view_layer.top.abstain_rate_range 逐一相等，"
            "fail-closed），非手抄；axis-plan 在案 r16 基线四键 [0.771429, "
            "0.857143, 12, 0.261904] 与 run-r17 baseline_cross_check 交叉"
            "核对一致"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "R17 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "status": ("R17 实测 (M1,M2,M3,M4)=(0.88, 0.75, 8, 0.333333)；资格"
                   "门=G1/G2 均满足→进入排序；R17 在三单轴中的位置待 R18/"
                   "R19 后按冻结规则比较——不预写结论（combination_decision_"
                   "rule.preregistration_note：本规则只决定「做不做、做哪"
                   "个」，不预写结果）"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4},
    }

    directional_observation_vs_r16 = [
        ("R16→R17 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 沿用"
         "无新增版本：12/12 派次自述「未读取盘上任何其他文件」；R17T/R17B "
         "前缀随 r17 指引 §6 落盘固化=r13→r15 路径回归、无需派发层覆盖）；"
         "旗标 49→37（六实例旗数 top 9/14/12→8/8/9、bottom 5/5/4→4/3/5；"
         "非弃权 10→6、弃权 39→31）；全旗标合计弃权率 0.795918（39/49，附"
         "记口径）→0.837838（31/37，附记口径）；预注册主通道三分判据：(a) "
         "M1 ≤0.671429（r16 零变更基线 27/35=0.771429 绝对降幅 ≥0.10）不成"
         "立（crit_a=False）；(b) M1 ≥0.771429 成立（crit_b=True）⇒字母裁"
         "决=reject（轴1 证伪：分辨率非瓶颈[或视觉编码器尺寸上限抵消增益]"
         "；转向轴2/轴3）；代表配置（top=top-i1：中位 8 tie（8/8/9）按先序"
         "取、如实注明；bottom=bottom-i1：中位 4 唯一）弃权率 0.764706"
         "（13/17）→0.916667（11/12）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.666667/"
         "0.928571/0.666667（r16，极差 0.261904）→1.0/1.0/0.666667（r17，"
         "极差 0.333333）——top 渲染分辨率倍增（renders-r17 四图全新渲染 "
         "640→1280dpi、像素数×4、r14b 配色规则逐字重放）下聚合落点 27/35="
         "0.771429→22/25=0.88（不降反升=劣于零变更基线、落 reject 支；弃权"
         "旗数 27→22 有限回落但非弃权旗未同步增加[10→3]、分母 35→25 同降"
         "推高弃权率；跨轮实例群不同=混杂照旧、方向性描述）；bottom 1.0/0.8"
         "/0.75（r16，极差 0.25）→0.75/0.666667/0.8（r17，极差 0.133333）"
         "——bottom 全旗聚合弃权率 12/14=0.857143→9/12=0.75（improved 改"
         "善方向如实单列）；本轮首现 2 个零旗标派次（prep1-bottom-i1/"
         "prep1-bottom-i2，r13–r16 无先例；view_check=not_applicable 不进"
         "弃权率分母）。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r16 的 r12 以"
         "来首次逐实例命中（union 1/13=0.076923，R16T-001×GT-REVC-AP-6-"
         "R2LED2）在本轮未复现——GT 条目层 union=1/13→0/13（0.0）、"
         "agreement=0/13（0.0）维持：单实例命中不稳定如实登记（r16 命中属 "
         "top-i2 单实例，本轮同族 top 派次零命中）；代表配置 gt_recall_"
         "total 0.0（0/13）、seed_match_rate 0.0（0/1，诊断口径，禁称 "
         "precision/FPR）。bottom 12 旗（9 弃权+3 非弃权）零匹配属结构性："
         "GT 13 条全部 side=top、bottom 无 GT 在案（gt-audit-r1：bottom "
         "GT=无源已关闭）⇒ bottom 旗标与 GT 匹配应为空，如实；top 非弃权旗 "
         "3 条（其中 2 条为 1280 新细节形态相关）与同态 GT 零 ≥0.5 "
         "containment 交叠或类别/视角门内零命中。"),
        ("通道归因（vs R16，预注册重放方法）：几何门面积比出局 0→0"
         "（guard_ok=True 独立单列、不构成 r17 字母裁决输入）；类别门 1→0"
         "（r16 在案 1 条=prep1/top-i1 R16T-006 silk×GT-REVC-P1-R4J3 类别"
         "不符出局在本轮未再现、r17 零条目）；视角门 0→0（top 非弃权旗与同"
         "态 GT 零视角错位交叠；bottom 非弃权旗零匹配属结构性）。通道链自 "
         "r6：几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→"
         "r15=0→r16=0→r17=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→r12="
         "0→r13=0→r14=0→r15=0→r16=1→r17=0。重放与 compare_v3 对拍一致。"),
        ("预注册假设（axis-plan-r17-resolution-double）字母裁决=reject（落"
         "支=(b) M1 ≥0.771429（不优于零变更基线）——轴1 证伪：分辨率非瓶颈"
         "（或视觉编码器尺寸上限抵消增益，机制观察须记录读者实际可见细节的"
         "自述）；转向轴2/轴3；r17-prep-record hypothesis_test.adjudication "
         "判据原文执行；唯一正式裁决）。实测：M1=22/25=0.88 vs r16 零变更基"
         "线 27/35=0.771429（live 重放双侧复算与在案登记/axis-plan 锚交叉核"
         "对一致，不手工抄数）；(a) 支阈值 0.671429=基线绝对降幅 ≥0.10 的计"
         "划件显著收益阈值（r15→r16 纯重抽漂移 0.09064 为历史幅度参照）不成"
         "立；6 位定点整数交叉相乘比较：(a) 22×10^6>671429×25、(b) 22×"
         "10^6≥771429×25。守门 G1（bottom courtyard 非弃权 0/0/0 维持）=维"
         "持、G2（guard_ok=True 维持，几何门 R16=0→R17=0）=维持——均独立单"
         "列，守门均维持、不触发出局（per axis-plan early_stop_rule）。"),
        ("机制观察单列（不凌驾）：(a) 呈现尺寸自述 4/12 派次（applied-top-i2"
         "「约 1000px 宽度呈现」+applied-top-i3「约 1000×1000」+prep1-top-i3"
         "「约 1000px 宽度呈现」+prep1-bottom-i3「约 1500px 呈现」）vs 仪器"
         "像素界 top 4009×4009/bottom 4010×4009（witness-r17 live 装载）——"
         "读者自述呈现尺寸（≈像素界/4～/2.7）表明 1280dpi 的 4 倍像素增益在"
         "读者端被呈现端缩放截断；reject 支内嵌「视觉编码器尺寸上限抵消增益"
         "」解释与该自述相容（top 自述约 1000px 的三派次恰为弃权最密区 "
         "[top-i1/top-i2 弃权率 1.0]、bottom 自述「1280dpi 清晰/间隙可分辨"
         "」的派次多判正常或非弃权报告——方向性观察、development 域只描述"
         "不断言）；(b) 1280 新可见细节旗 5 条（top 弃权 4[半填充圆形 2+QFP "
         "疑似间断 1+IC 引脚排延伸差异 1]+bottom 非弃权报告 1[applied-"
         "bottom-i1 R17B-001 椭圆焊盘中段浅色竖向截断带]）+同族判正常对照 2"
         "——新细节既触发新弃权也触发新报告、双向分化；与 M1 未回落并存；"
         "(c) top 弃权构成分型=接触性 11→8、存在性 15→14、其他 1→0（22 条"
         "逐旗摘录在案）；(d) 绿区语义化：bottom-i2/bottom-i3 §5A 显式援引"
         "+bottom-i1 无援引的空隙/翼瓣几何语义化（与 r16 的 6/6 全援引不同、"
         "实例分化如实登记）。"),
        ("bottom 改善通道单列（M2=9/12=0.75 vs r16 基线 12/14=0.857143，"
         "improved 方向；不影响字母）：(1) 零旗标派次 2 个（prep1-bottom-i1/"
         "prep1-bottom-i2 两派次零旗，r13–r16 无先例；零旗格不进弃权率分"
         "母）；(2) 黑点族弃权旗（M3，分型件 rubric 口径）=8 条 vs r16=12"
         "（数量回落、方向性描述；top 2+bottom 6，全部弃权；另有 4 派次 "
         "notes 把黑点判为安装孔/钻孔类正常特征未报告=同现象跨实例处置分"
         "化）；(3) bottom courtyard 类旗 1 条（prep1-bottom-i3 R17B-001 "
         "孤立焊盘对近邻+courtyard 归属不确定弃权）全部弃权——非弃权 "
         "courtyard 0/0/0 维持（G1）。「top 细节密度 vs bottom 粗特征对呈现"
         "缩放的 differential」记入机制观察候选（bottom 1280dpi 自述清晰派"
         "次多判正常/非弃权 vs top 自述约 1000px 呈现派次弃权最密——不断"
         "言、development 域只描述）。"),
        ("工具行为（协议侧 v1.2 沿用第六轮，如实入账）：R17 十二派次全部以 "
         "Read 工具直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何"
         "其他文件」（12/12 逐字摘录在案 reader_tool_evidence）；全部判读"
         "输入严格限于（指引+该 PNG），零 GT/零诊断/零 legend（含 diag-"
         "r17-render 对照裁片不进 reader 上下文）=非盲读违规；flag_id 两板"
         "各自从头编号=实例输出行为差异如实登记、编排侧按 (state, flag_id) "
         "限定；跨轮实例不同+轮内实例差异=混杂因素照旧声明"
         "（reader_instance_note）。"),
        ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延续，零"
         "阈值改动零期望）：courtyard 类旗标 8 条（top 7+bottom 1）、弃权 "
         "7+非弃权 1——非弃权 courtyard 1 条（applied-top-i3 R17T-001）零"
         "命中（9 条同态 GT checked）；命中链 r8=1→r9=0→r10=1→r11=3→r12=0→"
         "r13=0→r14=0→r15=0→r16=1→r17=0（r16 的 R16T-001 命中未再现）；"
         "bottom courtyard 弃权 1 条=r16 的 2 条（黑点-椭圆轮廓相切/近邻）"
         "未再现、黑点本轮全按 other_advisory 报告（归类如实分列）。reroute "
         "类 1 条全部弃权（存在性出口；R17T-002「等长|蛇形」子串零命中——"
         "滥用型通道被动追踪=0，r15 机械命中=1 的否定式援引未再现）；产量链 "
         "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→r17=1。"),
    ]

    honest_conclusion = (
        "本轮（development 域，轴1 仪器轮（渲染侧单变量：renders-r17 四图"
        "全新渲染 dpi 640→1280[framing 预注册 a1084c14→witness 见证 "
        "e979bec2、bottom 两图字节同 0c2d5c00]+判读指引=observation-"
        "guidance-r17.md 07c520be[r15 基座 d5babc93 机械变换派生：§2–§7 判"
        "据逐字保留、§5A 描述性仪器同步、R17T/R17B 前缀随指引落盘固化]+"
        "GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed="
        "true 已预注册；唯一实验变量=渲染分辨率；per axis-experiment-plan-"
        "r17-r20 冻结件[用户 2026-09-09 指令操作化]））12 派次 37 旗标中 "
        "31 弃权、6 非弃权：代表配置（top-i1+bottom-i1：top 中位 8 为 i1/i2 "
        "tie 按先序取并如实注明、bottom 中位 4 唯一）gt_recall=0.0（0/13）、"
        "seed_match_rate=0.0（0/1，诊断口径，禁称 precision/FPR）、"
        "abstain_rate=0.916667（11/12），联合评价 not_met（gt_recall、"
        "seed_match_rate 与 abstain_rate 三项未达 APR-0011 暂行线；诊断对"
        "照，非采纳门；连续达标计数 0→0；GT 条目层 union=0/13、agreement="
        "0/13 双口径并列——r16 的 1/13 首命中未复现=单实例命中不稳定如"
        "实）。预注册假设（axis-plan-r17-resolution-double）裁决（按 "
        "r17-prep-record hypothesis_test.adjudication 三分判据）=reject（字"
        "母口径，唯一正式裁决）：M1（top 全旗聚合弃权率，12 派次全口径）实"
        "测=22/25=0.88，落支=(b) M1 ≥0.771429（不优于零变更基线）——轴1 证"
        "伪：分辨率非瓶颈（或视觉编码器尺寸上限抵消增益，机制观察须记录读"
        "者实际可见细节的自述）；转向轴2/轴3。(a) 支基线=同一聚合逻辑对 "
        "run-r16 内嵌实例记录双侧复算 27/35=0.771429（live 重放与在案登记/"
        "axis-plan 锚交叉核对一致，不手工抄数），阈值 0.671429=绝对降幅 "
        "≥0.10 的计划件显著收益阈值不成立；marginal 带 0.671429<M1<"
        "0.771429 亦未落。守门 G1（bottom courtyard 非弃权 0/0/0 维持）与 "
        "G2（guard_ok=True，几何门 0→0）均维持、不触发出局（axis-plan "
        "early_stop_rule）。bottom 改善通道如实单列（不影响字母）：M2=9/12="
        "0.75 vs r16 基线 12/14=0.857143（improved 方向）；三件实测=零旗标"
        "派次 2（prep1-bottom-i1/prep1-bottom-i2，r13–r16 无先例）+黑点族 "
        "8 旗全弃权 vs r16 12（数量回落）+bottom courtyard 旗 1 条全弃权"
        "（非弃权 0/0/0 维持）。机制发现（比 M1 数字更值钱）：呈现尺寸自述 "
        "4/12 派次（约 1000px×3+约 1500px×1）vs 仪器像素界 4009/4010 px——"
        "读者端呈现尺寸（≈像素界/4～/2.7）与 reject 支内嵌「视觉编码器尺寸"
        "上限抵消增益」解释相容（呈现端缩放截断像素增益的机制候选；如实单"
        "列、不断言）；1280 新可见细节旗 5 条（top 弃权 4+bottom 非弃权报"
        "告 1[applied-bottom-i1 R17B-001 椭圆截断带]）+判正常对照 2——高分"
        "辨率下新可见细节既触发新弃权也触发新报告、双向分化，与 M1 未回落"
        "并存；top 弃权构成分型=接触性 8+存在性 14+其他 0（r16 对照 11/15/"
        "1）；「top 细节密度 vs bottom 粗特征对呈现缩放的 differential」记"
        "入机制观察候选（bottom 自述清晰派次多判正常/非弃权 vs top 自述约 "
        "1000px 呈现派次弃权最密——方向性观察、development 域只描述不断"
        "言）。实验对照账：本轮 (M1,M2,M3,M4)=(0.88, 0.75, 8, 0.333333)"
        "（axis-plan benefit_metrics 口径实测装载），R17 在三单轴中的排序"
        "位置待 R18/R19 后按冻结规则比较——不预写结论。注意：reject=预注册"
        "阈值命中方向的描述性结论、非因果证明——「正确测出无效同样是有效证"
        "据」；单轮 n=3、development 域只描述不断言；机制观察/度量教训单列"
        "、不凌驾不改写字母裁决；APR-0011 门（代表配置）与字母裁决分列不合"
        "并；本轮判据均为描述性边界、非门阈值（门零改动）。残余实例差异仍"
        "存（top 弃权率 1.0/1.0/0.666667 极差 0.333333、top-i1/top-i2 双实"
        "例全弃权、top-i3 独扛全部 3 条 top 非弃权旗；bottom 0.75/0.666667/"
        "0.8；板内孤立焊盘组三实例三出口=判读语义歧义未穷尽）。bottom 12 旗"
        "（9 弃权+3 非弃权）零匹配属结构性（GT 13 条全部 side=top，bottom "
        "GT 无源在案 gt-audit-r1）；本轮 12 格中 2 格零旗标（首现；item 5 "
        "口径：零旗格不进弃权率分母、view_check=not_applicable）。「系统性"
        "正常→不报告」通道 bottom 六派次一致使用（§4(i) 判读路径延续，摘录"
        "在案）。工具行为混杂如实入账（12/12 派次自述「未读取盘上任何其他"
        "文件」；R17T/R17B 前缀随指引落盘固化；flag_id 两板各自从头编号=实"
        "例输出行为差异如实登记、编排侧按 (state, flag_id) 限定）；输出格式"
        "披露（12 件缩进格式冻结原始判读件、零改动直读）如实登记、均非盲读"
        "违规。GT 侧三候选经 gt-audit-r1 全部关闭（延续零改动，GT 侧不再有"
        "候选；r17 union 0/13 与 bottom GT 无源结构相容）。不做「能力已修复"
        "/已达成」类断言；in_calibrated_range 恒 False。本批证据按协议 v1 "
        "§4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r17-prep-record no_loosening_note：判据文"
         "本零改动、§2–§7 逐字承 r15[分段+substring 双重断言复核]；§5A 两处"
         "为描述性仪器事实同步[px 数=仪器侧像素计数事实、非判据，不构成任何"
         "「应判正常/无需报告」的指示，不降低任何责任门槛]——反放宽条款「仅"
         "因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」与"
         "三路出口显式化在 r17 指引 §4 内逐字保留；三分判据描述性边界与门分"
         "列）。"),
        ("R16 对照基线=calibration-run-r16.json（2c1f8265…，在案）；判据 (b) "
         "支基线=同一聚合逻辑对 run-r16 内嵌实例记录双侧复算（27/35="
         "0.771429）、(a) 支阈值 0.671429=计划件显著收益阈值（绝对降幅 ≥0.10；"
         "r15→r16 纯重抽漂移 0.09064 为历史幅度参照），不手工抄数；轮间对比"
         "只做方向性描述（跨轮实例群混杂照旧，per axis-plan "
         "comparison_rule.drift_confound_note 显式容忍）。"),
        ("通道归因方法：照抄 run-r15/run-r16 channel_attribution 的重放口径"
         "（deviation_note 承接），R15/R16/R17 均以内嵌输入确定性重放并与 "
         "compare_v3 对拍（run-r17 channel_attribution.method）；重放复现与"
         "在案登记一致（fail-closed）。"),
        ("读者实例行为披露如实记录：R17 十二派次 v1.2 规约自述合规（纯 Read "
         "直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 reading_"
         "notes 原文在案）；输出格式披露（12 件缩进格式冻结原始判读件、零改"
         "动直读）parse 校验全部通过。跨轮 reader 实例不同+轮内实例差异=混杂"
         "因素，每视角 n=3；本轮轮前评审=pre_round_review[satisfied_by_"
         "probe_and_plan：s62 探针 PASS[framing feasible]+诊断裁片主审核验+"
         "axis-plan 冻结]——与 r16 零变更轮的 not_required 路径不同、如实分"
         "列；轮前诊断=渲染探针链[framing a1084c14→witness e979bec2→diag 对"
         "照裁片]，r14 首试探针证伪教训已被本轮先探针后成图流程吸收。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=reject 维持不"
         "变（reject=轴1 证伪的描述性边界结论、非因果证明——预注册描述性边界"
         "下的方向性记录；单轮 n=3 小样本方向性证据；主通道三分判据"
         "（≤0.671429、带内、≥0.771429）与 APR-0011 门分开表述、互不凌驾：门"
         "联合评价（代表配置）=not_met 如实分列）；不得回溯改判既往轮次（r8–"
         "r16 字母裁决维持不变）。"),
        ("度量教训在案（供 R18 预注册参考、本轮不追溯适用）：跨轮实例群漂移混"
         "杂照旧声明（r15→r16 纯重抽漂移 0.09064 在案）；字母=预注册阈值命中"
         "与否的描述性结论（per r17-prep-record metric_lesson_separate）；实"
         "验对照账（axis_experiment_ledger）=axis-plan 冻结比较规则的 R17 行"
         "登记[(M1,M2,M3,M4)=(0.88, 0.75, 8, 0.333333)]，排序与组合决策待 "
         "R18/R19 后按冻结规则执行、不预写结论（axis1 现 M1=0.88 劣势位，但"
         "bottom 改善通道与呈现尺寸机制候选已如实入账备查）。"),
    ]

    next_iteration_targets = [
        ("按冻结计划推进 R18=轴2（黑点类专项[连续 5 轮主导：r13 8→r14 14→"
         "r15 7→r16 12→r17 8 旗全弃权+判正常派次分化]）：先经盘上探针证实黑"
         "点物理来源→guidance-r18=r15 基座+黑点中性仪器注记[注记须探针证实"
         "、非判据，不降低任何责任门槛，反放宽条款逐字保留、防放宽审查；无探"
         "针证实则该轴不得入轮，per axis-plan stage1 A2 原文]；渲染="
         "renders-r14b 字节复用（四图、零变更）——指引侧单变量轮。"),
        ("继而 R19=轴3（判据侧：§4(iii) 接触性判据补可操作分辨条款，方向=判"
         "定一致性，反放宽条款逐字保留；渲染=r14b 字节复用零变更）——指引侧"
         "单变量轮（axis-plan stage1 A3 原文；收益本在 M4[弃权判定一致性]、"
         "排序规则 M1 领衔对其不利属已接受的操作化取舍，判读须同时看 M4 如"
         "实登记，不得仅以排序否定轴3）。"),
        ("阶段2 组合轮按 axis-plan 冻结规则执行（combination_decision_rule："
         "R20=过守门轮次中 comparison_rule 排序最优两轴组合、必要时 R21 全组"
         "合；R17 现处 M1 劣势位[0.88 为三单轴中已知最高]——若 R18/R19 任一 "
         "M1 优于 0.771429 则 R20=该两轴组合；轴1 的 bottom 改善通道[M2="
         "0.75 improved+零旗派次 2+黑点族 8 回落]可作 R20 组合候选的记录在"
         "案事实，但排序规则 M1 优先照冻结执行、不临场调整）。"),
        ("呈现端缩放机制候选（若后续需要）：renders-r17 的 bottom 改善[top 自"
         "述约 1000px 呈现=像素界/4 vs bottom 自述约 1500px≈像素界/2.7、且 "
         "bottom M2 改善]提示「中庸分辨率（或呈现在 ~1500px 的超采样）可能"
         "优于原生 2×」——作为轴1 后续变体候选登记（如 960dpi 单变量，须预注"
         "册+framing 先冻结+探针先验证），本轮不做（axis-plan stage1 无此轴、"
         "登记备查不改变冻结排序规则）。"),
        ("留出集运行时机=开发线收敛判断（须用户拍板）：r17 字母=reject→轴1 "
         "证伪、收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未达"
         "成，不得写成已达成）；GT 侧维持全关闭声明延续（gt-audit-r1["
         "1f20554a…]三候选全部关闭，r9–r17 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r17 union 0/13[r16 的 1/13 未复现=单实"
         "例命中不稳定如实]、非新 GT）；in_calibrated_range 恒 False 直到正"
         "式采纳（须人工批准）；达标证据仍须留出集（out/v3-tl2/holdout/"
         "HOLDOUT-PLAN.md a4b80193… 与 datasets/holdout-candidates-r1 在"
         "案）。"),
    ]

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": directional_observation_vs_r16,
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本轮为同域第 17 轮迭代（development 域轴1 仪器轮（渲染分辨率 "
        "640→1280dpi 单变量）：迭代轮不得冒充留出证据）。",
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev16["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r17 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r17 全旗标合计 31/37=0.837838 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R16 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 与 abstain_rate 0.916667>0.5 "
                         "三项未达暂行线；gt_count 13≥12 单分项入线）——GT 条"
                         "目层 union 口径 0/13=0.0 亦未达 0.75（r16 的 1/13 "
                         "未复现=单实例命中不稳定如实；双口径与门分列如实）"),
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
            "stage1 R17=轴1 渲染分辨率倍增）→r17-prep-record.json"
            "（ceba4fef…，本轮预注册件，measurement_design 五条聚合口径与 "
            "hypothesis_test.adjudication 三分判据（≤0.671429/带内/≥"
            "0.771429）先于盲读冻结；instrument_change.changed=true；"
            "changed_variables=[渲染分辨率 640→1280dpi 四图全部（主变量 "
            "render-resolution-x2-r17）+§5A px 描述性同步+轮次标识机械同"
            "步，三件登记]；manipulated_factor=渲染分辨率[唯一仪器实验变"
            "量]）→判读指引="
            "observation-guidance-r17.md（07c520be…，r15 基座 d5babc93…机械"
            "变换派生 mechanical_transform_derive：§2–§7 判据逐字保留[分段+"
            "substring 双重断言]、§5A 描述性同步[橙 326460/绿 903366 px 仪器"
            "事实、非判据]+机械变换 edit_list 十件逐件登记[任务枚举+轮次标"
            "识同步+§5A 描述性同步]；byte_size 19878→19959="
            "delta 81）→renders-r17 四图全新渲染（1280dpi；framing 预注册 "
            "a1084c14→成图→witness 见证 e979bec2[像素界 top 4009×4009/"
            "bottom 4010×4009]；四 PNG sha256_file 实测=witness 登记值["
            "applied-top b35315ef/applied-bottom 0c2d5c00/prep1-top bdce8bbb"
            "/prep1-bottom 0c2d5c00，bottom 两图字节同]）→12 次盲读→run-r17"
            "（d444c4a5…，本链执行落盘）；GT 重投影沿用 derivation-log-r5."
            "json（62343380…）零新派生（GT 全部 side=top；渲染变更不改 GT 冻"
            "结纪律）；GT 冻结纪律：轮后未增删改；gt-audit-r1（1f20554a…）结"
            "论维持 GT 零改动（三候选关闭，gt_audit_reference 在案）"),
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域轴1 仪器轮（渲染侧单变量，第十七轮）：渲染变更="
            "renders-r17 四图全新渲染（dpi 640→1280、像素数×4；r14b 配色规"
            "则逐字重放[白墨图元→橙 (255,165,0)、板内空隙白→绿 (0,128,0)、"
            "二值 mask 全量替换不做 alpha 混合、z 序 base→橙→绿]；margin "
            "240px 物理等值；层清单/组合页/裁剪公式同口径、dpi=唯一仪器变量；"
            "framing 预注册 a1084c14→witness 见证 e979bec2——renders-r17 新"
            "渲染、非字节复用）+判读指引=observation-guidance-r17.md "
            "（07c520be 实测锚，r15 基座 d5babc93 机械变换派生 mechanical_"
            "transform_derive：§2–§7 判据逐字保留[分段+substring 双重断言复"
            "核]、§5A 渲染配色仪器注记描述性同步[橙 326460/绿 903366 px=仪"
            "器侧像素计数事实、非判据，不降低任何责任门槛]；R17T/R17B 前缀随"
            "指引 §6 落盘固化）+GT 集/协议阈值与度量版本/比较器常量零改动"
            "（GT 重投影沿用 derivation-log-r5——零新派生；gt-audit-r1 三候"
            "选关闭结论延续）；协议 v1.1+v1.2 维持无新增版本；instrument_"
            "change.changed=true 已预注册（changed_variables=[渲染分辨率 "
            "640→1280dpi 四图全部]；轴=axis-plan stage1 R17="
            "A1_render_resolution_x2）；检验假设 axis-plan-r17-resolution-"
            "double（判据=r17-prep-record.json hypothesis_test.adjudication "
            "三分判据 (a)≤0.671429/[marginal 带内]/(b)≥0.771429，轮后如实执"
            "行：字母裁决唯一正式+机制观察/度量教训单列；守门 G1/G2 独立单"
            "列，任一破坏→轴1 按 plan early_stop_rule 出局）；主通道三分判"
            "据与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独"
            "立计算、互不凌驾、分开表述；measurement_design 五条聚合口径先于"
            "盲读冻结；跨轮收益比较按 axis-plan 冻结规则（R17 行见 axis_"
            "experiment_ledger：排序待 R18/R19 后比较、不预写结论）；按协议 "
            "v1 §4，迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R17, "sha256": run17_sha},
        "schema_version": SCHEMA_VERSION,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s65-cal-r17-devrecord] round17-dev-record: {status}")
    print(f"[s65-cal-r17-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch={dev['hypothesis_test_i']['measurement'][
              'letter_branch']}")
    print(f"[s65-cal-r17-devrecord] 三分判据: (a) M1 22/25=0.88≤0.671429 不成"
          f"立（run-r16 双侧复算 27/35=0.771429；降幅 ≥0.10 显著收益阈值）；"
          f"(b) M1 ≥0.771429 成立 ⇒ reject（轴1 证伪，转向轴2/轴3）")
    print(f"[s65-cal-r17-devrecord] 守门: G1=维持（bottom courtyard 非弃权 "
          f"0/0/0）、G2=维持（几何门 0→0，guard_ok=True）→不触发出局")
    print(f"[s65-cal-r17-devrecord] 机制观察: 呈现尺寸自述 4/12 派次[约 1000px"
          f"×3+约 1500px×1] vs 仪器 4009/4010 px（呈现端缩放候选，不断言）；"
          f"M2=9/12=0.75 improved[零旗派次 2+黑点族 8 vs 12]；M4=0.333333；"
          f"1280 新细节旗 5[top 4+bottom 1]")
    print(f"[s65-cal-r17-devrecord] 实验对照账: (M1,M2,M3,M4)=(0.88, 0.75, 8, "
          f"0.333333)；R17 排序位置待 R18/R19 后按 axis-plan 冻结规则比较")
    print(f"[s65-cal-r17-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s65-cal-r17-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0")
    print(f"[s65-cal-r17-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s65-cal-r17-devrecord] R17 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=reject 唯一正式；机制观察/度量教训单列不凌驾；"
          "in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
