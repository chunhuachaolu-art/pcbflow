#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s59_calibration_r16_devrecord.py — R16 CLOSE 包 B：
round16-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律）。

R16=同指引重复轮（零变更轮，r10 先例再现）：判读指引=
observation-guidance-r15.md 字节复用（d5babc93 实测锚、零新建指引
文件）；渲染零变更（renders-r14b 四图字节复用=r14/r15 轮盲读所用
同一批文件，四 PNG sha 与 render-witness-r14b.json 登记值逐一相等）；
GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed=
false 已预注册、changed_variables=[]；唯一操纵因子=reader 实例群
重抽（12 派次全部重抽）。预注册假设
（r15-dev-record-candidate-0-same-guidance-repeat）三分判据轮后
裁决=inconclusive（唯一正式裁决）：
- (a) 支 top 全旗聚合弃权率 ≤0.75（run-r14 双侧复算基线 18/24）
  → crit_a=False；
- (b) 支 top 全旗聚合弃权率 ≥0.862（run-r15 双侧复算 25/29=
  0.862069）→ crit_b=False；
- (c) 0.75 < top=27/35=0.771429 < 0.862 命中 ⇒ 字母=inconclusive
  （(α) 跨轮实例群漂移与 (β) §5A 全局弃权致敏两候选解释均不排斥、
  归因悬置）。
机制观察/度量教训单列不凌驾字母裁决：top 弃权构成分型=存在性
15>接触性 11>层归属其他 1（黑点类存在性弃权为主导而非接触性）；
黑点类 12 旗全弃权连续第 4 轮主导（r13 8→r14 14→r15 7→r16 12）
+2 派次判正常；绿区语义化 6/6 派次「空隙/翼瓣」读法+6/6 显式援引
§5A（r15 收敛在实例群重抽下完全保持）；bottom 维持性=12/14=0.857143
vs r15 的 11/13=0.846154（轻微恶化方向如实单列）+非弃权 courtyard
0/0/0 维持但 courtyard 类旗标 2 条重现（r15「零 courtyard 旗」本身
呈实例群敏感）；GT 逐实例命中 r12 以来首次 0→1（R16T-001×
GT-REVC-AP-6-R2LED2，containment 1.0、面积比 7.289285 门内；union
1/13=0.076923、agreement 0/13 维持）；守门 rebound 维持 0
（guard_ok=True）；联合 not_met、连续=0。

生成器纪律：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-08"；
- 防覆写护栏：round16-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round16-dev-record.json 一件（s58 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s59_calibration_r16_devrecord.py   （仓库根执行）
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

DECLARED_DATE = "2026-09-08"
ROUND_ID = "2026-09-08-r16"
ROUND_LABEL = "r16"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round16_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_RUN_R15 = "out/v3-tl2/calibration/calibration-run-r15.json"
REL_RUN_R14 = "out/v3-tl2/calibration/calibration-run-r14.json"
REL_PREP_R16 = "out/v3-tl2/calibration/r16-prep-record.json"
REL_DEV_R15 = "out/v3-tl2/calibration/round15-dev-record.json"
REL_GUIDANCE_R15 = "out/v3-tl2/calibration/observation-guidance-r15.md"
REL_OUT = "out/v3-tl2/calibration/round16-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 主通道三分判据实测锚（写盘前 fail-closed 与 run-r16 盘上值逐一核对）
EXPECT_TOP_ABSTAIN_R16 = 27
EXPECT_TOP_FLAGS_R16 = 35
EXPECT_TOP_RATE_R16 = 0.771429
EXPECT_BOTTOM_ABSTAIN_R16 = 12
EXPECT_BOTTOM_FLAGS_R16 = 14
EXPECT_BOTTOM_RATE_R16 = 0.857143
EXPECT_TOP_R15_BASELINE_LIVE = "25/29"
EXPECT_TOP_R15_BASELINE_VALUE = 0.862069
EXPECT_TOP_R14_BASELINE_LIVE = "18/24"
EXPECT_TOP_R14_BASELINE_VALUE = 0.75
EXPECT_BOTTOM_R15_BASELINE_LIVE = "11/13"
EXPECT_BOTTOM_R15_BASELINE_VALUE = 0.846154
EXPECT_COURTYARD_NON_ABSTAIN = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_COUNTS = {"top-i1": 9, "top-i2": 14, "top-i3": 12,
                 "bottom-i1": 5, "bottom-i2": 5, "bottom-i3": 4}
EXPECT_ABSTAIN = {"top-i1": 6, "top-i2": 13, "top-i3": 8,
                  "bottom-i1": 5, "bottom-i2": 4, "bottom-i3": 3}
EXPECT_RATES = {"top-i1": 0.666667, "top-i2": 0.928571, "top-i3": 0.666667,
                "bottom-i1": 1.0, "bottom-i2": 0.8, "bottom-i3": 0.75}
EXPECT_R15_RATES = {"top-i1": 0.909091, "top-i2": 0.8, "top-i3": 0.875,
                    "bottom-i1": 0.75, "bottom-i2": 0.75, "bottom-i3": 1.0}
EXPECT_TYPE_COUNTS = {"contact": 11, "existence": 15, "other_layer": 1}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 3, "bottom-i2": 4, "bottom-i3": 3,
                                "top-i1": 1, "top-i2": 1, "top-i3": 0}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s59-cal-r16-devrecord] FAIL: {msg}")


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


def _verify_facts(run: dict, run15: dict, run14: dict, prep: dict,
                  dev15: dict, guidance_sha: str) -> None:
    # ---- run-r16 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r16":
        _fail("run kind 不符")
    if (run["round_id"], run["round_label"], run["declared_date"],
            run["evaluation_domain"]) != (ROUND_ID, ROUND_LABEL,
                                          DECLARED_DATE, "development"):
        _fail("run 声明常量不符")
    ht = run["hypothesis_test"]
    if ht["hypothesis_id"] != "r15-dev-record-candidate-0-same-guidance-repeat":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "inconclusive":
        _fail("verdict != inconclusive")
    m = ht["measurement"]
    if (m["crit_a_top_le_r14_baseline"] is not False
            or m["crit_b_top_ge_r15_baseline"] is not False):
        _fail("三分判据布尔不符（(a)(b) 应双否）")
    if "(c)" not in m["letter_branch"] or "0.75" not in m["letter_branch"]:
        _fail("落支应为 (c) 带")
    if m["verdict"] != "inconclusive":
        _fail("measurement.verdict != inconclusive")
    # 本轮实测（top 27/35、bottom 12/14）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R16, EXPECT_TOP_ABSTAIN_R16):
        _fail("top 聚合不符（27/35）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R16, EXPECT_BOTTOM_ABSTAIN_R16):
        _fail("bottom 聚合不符（12/14）")
    if m["top_abstain_rate_r16"] != EXPECT_TOP_RATE_R16 or \
            m["bottom_side_observation"]["bottom_abstain_rate_r16"] != \
            EXPECT_BOTTOM_RATE_R16:
        _fail("聚合弃权率不符")
    if "27/35" not in m["top_abstain_rate_r16_arithmetic"] or \
            "12/14" not in m["bottom_side_observation"][
                "bottom_abstain_rate_r16_arithmetic"]:
        _fail("聚合算式文本不符")
    # (a)(b) 双否的整数交叉相乘复核（避免浮点）：27/35>18/24 且
    # 27/35<25/29
    if (at * 24 <= 18 * ft) or (at * 29 >= 25 * ft):
        _fail("整数交叉相乘复核不符（(a)(b) 双否应 27×24>18×35 且 "
              "27×29<25×35）")
    # 基线双侧复算（同一聚合逻辑对 run-r14/run-r15 内嵌输入重算）
    f14, a14 = _view_abstain_aggregate(run14, "top")
    if (f14, a14) != (24, 18) or \
            m["top_abstain_rate_r14_baseline_live"] != \
            EXPECT_TOP_R14_BASELINE_LIVE or \
            m["top_abstain_rate_r14_baseline_value"] != \
            EXPECT_TOP_R14_BASELINE_VALUE:
        _fail("top r14 基线复算不符（18/24）")
    f15, a15 = _view_abstain_aggregate(run15, "top")
    if (f15, a15) != (29, 25) or \
            m["top_abstain_rate_r15_baseline_live"] != \
            EXPECT_TOP_R15_BASELINE_LIVE or \
            m["top_abstain_rate_r15_baseline_value"] != \
            EXPECT_TOP_R15_BASELINE_VALUE:
        _fail("top r15 基线复算不符（25/29）")
    fb15, ab15 = _view_abstain_aggregate(run15, "bottom")
    if (fb15, ab15) != (13, 11) or \
            m["bottom_side_observation"]["bottom_abstain_rate_r15_baseline_live"] != \
            EXPECT_BOTTOM_R15_BASELINE_LIVE or \
            m["bottom_side_observation"]["bottom_abstain_rate_r15_baseline_value"] != \
            EXPECT_BOTTOM_R15_BASELINE_VALUE:
        _fail("bottom r15 基线复算不符（11/13）")
    # bottom 侧观察（恶化方向如实单列）与 courtyard 0/0/0
    bso = m["bottom_side_observation"]
    if (bso["bottom_abstain_flags_r16"], bso["bottom_abstain_count_r16"]) != \
            (14, 12) or bso["bottom_rate_direction_vs_r15"] == "" or \
            bso["bottom_courtyard_flags_total_r16"] != 2 or \
            bso["bottom_courtyard_non_abstain_by_instance_r16"] != \
            EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("bottom 侧观察不符（12/14、courtyard 旗 2、非弃权 0/0/0）")
    cy16 = _courtyard_non_abstain_by_instance(run)
    cy15 = _courtyard_non_abstain_by_instance(run15)
    if cy16 != EXPECT_COURTYARD_NON_ABSTAIN or \
            cy15 != EXPECT_COURTYARD_NON_ABSTAIN:
        _fail("courtyard 非弃权复算不符（r16/r15 均 0/0/0）")
    if _courtyard_flags_total(run) != 2 or _courtyard_flags_total(run15) != 0:
        _fail("bottom courtyard 旗总数不符（r16=2、r15=0）")
    # 守门通道（0→0 维持；独立单列）
    if m["guard_channel"]["guard_ok"] is not True:
        _fail("guard_channel 应维持 True")
    ca = run["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r16_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_1_geometry_gate"][
                "r15_area_ratio_rejected_entries"]) != 0 or \
            len(ca["channel_1_geometry_gate"][
                "r14_area_ratio_rejected_entries"]) != 1:
        _fail("几何门 0→0（r14=1）复核不符")
    if len(ca["channel_2_category_gate"]["r16_category_mismatch_entries"]) \
            != 1:
        _fail("类别门 r16=1 条不符")
    # GT 双口径：union 1/13（首命中）、agreement 0/13
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (1, 0, 13):
        _fail("双口径不符（union 1/13、agreement 0/13）")
    if dual["union"]["gt_ids"] != ["GT-REVC-AP-6-R2LED2"] or \
            dual["union"]["gt_recall_union"] != 0.076923:
        _fail("union 首命中条目不符（GT-REVC-AP-6-R2LED2、0.076923）")
    hit = dual["per_gt"][5]
    if hit["gt_id"] != "GT-REVC-AP-6-R2LED2" or hit["matched_by_count"] != 1:
        _fail("per_gt 首命中不符")
    h0 = hit["hits"][0]
    if (h0["flag_id"], h0["instance"], h0["state"]) != \
            ("R16T-001", "top-i2", "applied") or \
            h0["containment"] != 1.0 or h0["area_ratio"] != 7.289285:
        _fail("首命中明细不符（R16T-001×AP-6、containment 1.0、面积比 "
              "7.289285）")
    if run["courtyard_tracking"]["courtyard_matches_r16"] != 1:
        _fail("courtyard 追踪 r16=1 不符")
    # 旗数/弃权率（逐实例）与 r15 对照
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN or \
            rates != EXPECT_RATES:
        _fail("逐实例旗数/弃权率不符")
    r15rates = {n: run15["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER}
    if r15rates != EXPECT_R15_RATES:
        _fail("r15 逐实例弃权率不符")
    # 代表配置与门
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (17, 13, 0.764706, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0:
        _fail("联合门/连续计数不符")
    rep = run["representative_configuration"]["members"]
    if rep != {"top": "top-i3", "bottom": "bottom-i1"}:
        _fail("代表配置成员不符（top-i3+bottom-i1）")
    # instrument_change.changed=false（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not False or \
            prep["instrument_change"]["changed"] is not False or \
            prep["no_instrument_change"] is not True:
        _fail("instrument_change.changed 应为 false")
    if run["instrument_change"]["changed_variables_registered"] != [] or \
            prep["changed_variables"] != []:
        _fail("变更变量登记应为空（零变更轮）")
    if prep["manipulated_factor"] != "reader 实例群（12 派次全部重抽）":
        _fail("操纵因子声明不符")
    # 机制观察：top 分型/黑点分布/绿区语义化/bottom 维持性
    mo = ht["mechanism_observation"]
    ty = mo["top_abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            ty["top_abstain_flags_total"] != 27 or len(ty["rows"]) != 27:
        _fail("top 弃权构成分型不符（11/15/1、27 旗）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 12:
        _fail("黑点类 12 旗全弃权不符")
    if "2 派次判正常" not in bdt["notes_normal_dispositions"]:
        _fail("黑点类 2 派次判正常不符")
    gs = mo["green_semantics_by_instance"]
    if not all(gs["green_semantics_by_instance"][n]["§5A_cited"]
               for n in ("bottom-i1", "bottom-i2", "bottom-i3")):
        _fail("绿区语义化 6/6 派次 §5A 显式援引不符")
    bsm = mo["bottom_side_observation_maintenance"]
    if bsm["counts"]["bottom_rate_vs_r15_direction"] != "worse" or \
            bsm["counts"]["bottom_abstain_rate_r16"] != 0.857143 or \
            bsm["counts"]["r16_bottom_courtyard_non_abstain_total"] != 0:
        _fail("bottom 维持性单列不符")
    # 判据引用=prep-record 原文（逐字一致）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "letter_inconclusive",
              "letter_reject", "letter_supported",
              "metric_lesson_separate", "side_observation_separate"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引字节复用锚（d5babc93 实测）
    if prep["guidance_reuse"]["mode"] != "byte_reuse_zero_change" or \
            prep["guidance_reuse"]["edit_list"] != []:
        _fail("guidance_reuse 字节复用声明不符")
    if prep["guidance_reuse"]["base_sha256"] != guidance_sha or \
            guidance_sha != _sha(REL_GUIDANCE_R15):
        _fail("r15 指引实测 sha 与 d5babc93 锚不符（零写入承诺）")
    # 预注册引用：run→prep 实测一致；prep→dev15 授权链
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R16):
        _fail("prep-record sha 实测与登记不符")
    auth = prep["guidance_reuse"]["chain_anchors"][
        "round15_dev_record_authorization"]
    if auth["sha256_measured"] != _sha(REL_DEV_R15):
        _fail("round15-dev-record 实测 sha 与链锚不符")
    if not dev15["next_iteration_targets"][0].startswith(
            "R16 第一候选=同指引重复轮"):
        _fail("r15 dev-record 授权候选原文定位不符")
    if dev15["hypothesis_test_i"]["verdict"] != "reject":
        _fail("r15 dev-record verdict 不符")
    if dev15["round_id"] != "2026-09-08-r15":
        _fail("r15 dev-record round_id 不符")


def build_dev_record() -> dict:
    """构建 round16-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R16)
    run15 = _json_load(REL_RUN_R15)
    run14 = _json_load(REL_RUN_R14)
    prep = _json_load(REL_PREP_R16)
    dev15 = _json_load(REL_DEV_R15)
    guidance_sha = _sha(REL_GUIDANCE_R15)
    _verify_facts(run, run15, run14, prep, dev15, guidance_sha)

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

    run16_sha = _sha(REL_RUN_R16)

    # 联合评价趋势：r5–r15 行=round15-dev-record 在案行（冻结转录）；
    # r16 行=本轮 run 实测
    trend_rows = list(dev15["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r16",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R16, "sha256": run16_sha},
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
            "全旗标合计口径仅作附记（39/49=0.795918，非弃权 10+弃权 39）；"
            "本轮预注册主通道=三分判据（(a) top ≤0.75（run-r14 双侧复算 "
            "18/24）不成立；(b) top ≥0.862（run-r15 双侧复算 25/29）不成立"
            "；(c) 0.75<top 27/35=0.771429<0.862 命中⇒inconclusive）；"
            "bottom 全旗聚合弃权率 12/14=0.857143 为侧观察度量；实例层/"
            "视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("本轮无零旗标实例、两视角弃权率全部有定义（bottom 极差 "
                     "0.25=1.0−0.75（bottom-i1 全弃权与 i2/i3 并存）；top "
                     "极差 0.261904 较 r15 的 0.109091 扩大、prep1-top-i2 "
                     "单派次 11 旗全弃权=本轮最高弃权格（top-i2 13/14="
                     "0.928571 拉高轮内极差））"),
            "top": run["view_layer"]["top"]["abstain_rate_range"],
        },
        "blind_discipline": run["reader"]["dispatch_discipline"],
        "flag_count_by_category": {k: dict(v)
                                   for k, v in fc["by_category"].items()},
        "flag_count_by_file": flag_count_by_file,
        "flag_count_by_instance": dict(fc["by_instance"]),
        "non_abstain_count": fc["total"] - sum(fc["abstain_by_instance"]
                                               .values()),
        "note": ("flag 全部通过 calibration fail-closed 校验（拒收清单为空）；"
                 "读者产物为冻结证据，本包零改动；派发模式=12 派次（4 格×3 "
                 "实例，两波次串行保序）；R16T/R16B 前缀由派发指令层覆盖"
                 "（r15 指引 §6 示例前缀 R15T-/R15B- 落盘原文、字节复用不改"
                 "，per r16-prep-record protocol_amendment.naming）；flag_id "
                 "两板各自从头编号=读者实例输出行为差异如实登记（编排侧按 "
                 "(state, flag_id) 限定，跨板同号不混淆）；v1.2 工具规约沿用"
                 " 12/12 派次自述合规与输出格式披露（12 件缩进格式冻结原始"
                 "判读件、零改动直读）如实登记为混杂因素披露，不作废"),
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
            "measurement_design item 4；top 中位 12 由 top-i3 唯一持有"
            "（9/14/12）无 tie；bottom 中位 5 为 bottom-i1/bottom-i2 tie、"
            "按先序取 bottom-i1 并如实注明）"),
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

    directional_observation_vs_r15 = [
        ("R15→R16 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 沿用"
         "无新增版本：12/12 派次自述「未读取盘上任何其他文件」；r16 notes "
         "无 r14 的「未做任何程序化处理」逐字语句=自述措辞差异如实登记）；"
         "旗标 42→49（六实例旗数 top 11/10/8→9/14/12、bottom 4/4/5→5/5/4；"
         "非弃权 6→10、弃权 36→39）；全旗标合计弃权率 0.857143（36/42，附记"
         "口径）→0.795918（39/49，附记口径）；预注册主通道三分判据：(a) "
         "top ≤0.75（run-r14 双侧复算 18/24）不成立（crit_a=False）；(b) "
         "top ≥0.862（run-r15 双侧复算 25/29）不成立（crit_b=False）；(c) "
         "0.75<top 27/35=0.771429<0.862 命中⇒字母裁决=inconclusive（两候选"
         "解释均不排斥、归因悬置）；代表配置（top=top-i3：中位 12 唯一"
         "（9/14/12）无 tie；bottom=bottom-i1：中位 5 tie（5/5/4）按先序"
         "取、如实注明）弃权率 0.785714（11/14）→0.764706（13/17）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.909091/"
         "0.8/0.875（r15，极差 0.109091）→0.666667/0.928571/0.666667（r16，"
         "极差 0.261904）——top 渲染零变更（r16=renders-r14b 四图字节复用）"
         "下聚合落点 25/29=0.862069→27/35=0.771429（带内回落：落回两基线 "
         "18/24=0.75 与 25/29=0.862069 之间=判据 (c) 支的构成；跨轮实例群"
         "不同=混杂照旧、方向性描述；prep1-top-i2 单派次 11 旗全弃权=本轮"
         "最高弃权格）；bottom 0.75/0.75/1.0（r15，极差 0.25）→1.0/0.8/"
         "0.75（r16，极差 0.25）——bottom 全旗聚合弃权率 11/13=0.846154→"
         "12/14=0.857143（轻微恶化方向如实单列；bottom-i1 全弃权 5 旗）；"
         "旗数 top 11/10/8→9/14/12、bottom 4/4/5→5/5/4；本轮无零旗标实例、"
         "弃权率全部有定义。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r12–r15 连续四"
         "轮零匹配→r16 GT 逐实例命中 r12 以来首次 0→1：top-i2 applied "
         "R16T-001×GT-REVC-AP-6-R2LED2（containment 1.0、面积比 7.289285"
         "≤10 门内；CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明常量零改"
         "动）；GT 条目层 union=1/13=0.076923（≥1 实例命中即计）、"
         "agreement=0/13（0.0，≥2/3 实例命中才计）维持；代表配置 gt_recall_"
         "total 0.0（0/13）、seed_match_rate 0.0（0/4，诊断口径，禁称 "
         "precision/FPR）——代表配置=top-i3+bottom-i1 不含 top-i2，逐实例"
         "命中与门分列如实。bottom 14 旗（12 弃权+2 非弃权）零匹配属结构"
         "性：GT 13 条全部 side=top、bottom 无 GT 在案（gt-audit-r1："
         "bottom GT=无源已关闭）⇒ bottom 旗标与 GT 匹配应为空，如实；top "
         "非弃权旗 10 条中 1 条命中（其余与同态 GT 无 ≥0.5 containment 交"
         "叠或类别门出局）。"),
        ("通道归因（vs R15，预注册重放方法）：几何门面积比出局 0→0（r14 "
         "回升未延续、r15–r16 同指引重复轮维持 0；guard_ok=True 独立单列、"
         "不构成 r16 字母裁决输入——r16 预注册 guard_channel 无数值要件、"
         "「变化如实记录」）；类别门 0→1（r12–r15 连续零条目后的本轮计数"
         "如实登记：R16T-006×GT-REVC-P1-R4J3 silk_readability/courtyard_"
         "crowding 类别不符出局、containment 0.848147/面积比 1.529072；"
         "R11T-012↔GT-REVC-AP-8-R1Q2 仍为 r11 唯一在案条目、五轮无再现）；"
         "视角门 0→0（bottom 非弃权旗与同态 GT 零视角错位交叠；bottom 无 "
         "GT 在案）。通道链自 r6：几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0"
         "→r12=0→r13=0→r14=1→r15=0→r16=0；类别门 r6=1→r7=0→r8=1→r9=0→"
         "r10=0→r11=1→r12=0→r13=0→r14=0→r15=0→r16=1。重放与 compare_v3 "
         "对拍一致（R14/R15 十二件复算与在案登记一致、R16 十二件重放全部"
         "复现：候选对=applied-top-i2 [R16T-001, GT-REVC-AP-6-R2LED2]）。"),
        ("预注册假设（r15-dev-record-candidate-0-same-guidance-repeat）字"
         "母裁决=inconclusive（落支=(c) 0.75<top<0.862：两候选解释均不排"
         "斥、归因悬置；r16-prep-record hypothesis_test.adjudication 判据"
         "原文执行；唯一正式裁决）。零变更轮（唯一操纵因子=reader 实例群"
         "重抽）如实测得两轮带内落点：「r15 (iii) 违约是噪声 (α) 还是致敏 "
         "(β)」未决——两轮制归因对「两基线之间」落点分辨力有限（(c) 带非"
         "空）；度量教训单列：inconclusive 后不得再以盲目重复轮消耗盲读，"
         "第三点须靠分层（同实例群双跑）或判据侧/度量侧处置。"),
        ("机制观察单列（不凌驾）：(a) top 弃权构成分型=接触性 11+存在性 "
         "15+层归属其他 1（27 条逐旗摘录在案）——存在性/黑点类弃权为主导"
         "而非接触性；接触性弃权集中于 courtyard 类旗标（§4(iii) 判据路径"
         "延续），存在性弃权横跨 silk/other/reroute/placement 各类（黑点性"
         "质、叠压是否存在、绕行是否存在等）=top 弃权非单一机制驱动、r15 "
         "「6 条 courtyard 弃权中 5 接触+1 存在性」在实例群重抽下扩展为构"
         "成多通道化；(b) 黑点类 12 旗全弃权连续第 4 轮主导（r13 8→r14 14"
         "→r15 7→r16 12；top 2+bottom 10）+2 派次判正常（prep1-top-i2/"
         "prep1-top-i3 判安装孔/定位类正常未报告=同现象跨实例处置分化）；"
         "(c) 绿区语义化 6/6 派次「空隙/翼瓣」读法+6/6 派次显式援引 §5A 仪"
         "器注记（其中 4 派次明写「仅作仪器事实、未作为判据」）——r15 的语"
         "义化收敛在实例群重抽下完全保持；(d) bottom courtyard 类旗标 2 条"
         "重现（applied-bottom-i2 黑点-椭圆轮廓相切/近邻、r14「黑点骑跨轮"
         "廓」同族现象部分再现；非弃权 courtyard 0/0/0 维持但 r15「零 "
         "courtyard 旗」本身呈实例群敏感——r15 零旗标路径→r16 有旗全弃权"
         "路径，成因差异如实分列）。"),
        ("工具行为（协议侧 v1.2 沿用第五轮，如实入账）：R16 十二派次全部以 "
         "Read 工具直读内嵌图像、逐派次 reading_notes 自述「未读取盘上任何"
         "其他文件」（12/12 逐字摘录在案 reader_tool_evidence；prep1-"
         "bottom-i1 另自述「不掌握任何 GT 或期望信息」；prep1-top-i2 自述"
         "「做两遍独立判读」=实例自述措辞异质性如实登记）；r16 notes 无"
         "「未做任何裁剪/放大/像素分析等程序化处理」逐字语句——与 r14/r15 "
         "同为自述措辞差异、如实登记（工具行为轴=派发指令 v1.2 硬性条款照"
         "旧钉住）；全部判读输入仍严格限于（指引+该 PNG），零外部信息、零 "
         "GT/零诊断/零 legend=非盲读违规；跨轮实例不同+轮内实例差异=混杂"
         "因素照旧声明（reader_instance_note）。"),
        ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延续，零"
         "阈值改动零期望）：courtyard 类旗标 15 条（top 13+bottom 2）、弃"
         "权 14+非弃权 1——非弃权 courtyard 1 条（applied-top-i2 R16T-001）"
         "命中 GT-REVC-AP-6-R2LED2（containment 1.0、面积比 7.289285）；"
         "命中链 r8=1→r9=0→r10=1→r11=3→r12=0→r13=0→r14=0→r15=0→r16=1；"
         "bottom courtyard 弃权 2 条=黑点-椭圆轮廓相切/近邻（r14 弃权 4 条"
         "→r15 零旗标→r16 有旗全弃权 2 条，逐轮构成如实分列）。reroute 类 "
         "2 条全部弃权（存在性出口；R16T-004 prep1-top-i1+R16T-004 "
         "prep1-top-i3，「等长|蛇形」子串零命中——滥用型通道被动追踪=0，"
         "r15 机械命中=1 的否定式援引未再现）；产量链 r8=1→r9=0→r10=2→"
         "r11=3→r12=3→r13=2→r14=1→r15=4→r16=2。"),
        ("跨轮 flag_id 不构成同旗配对（R14T/R14B、R15T/R15B 与 R16T/R16B "
         "来自不同 reader 实例、不同判读实例；本轮实例群全部重抽）；通道归"
         "因是通道级不是旗级（run-r16 channel_attribution.pairing_caveat）；"
         "r16 两板各自从头编号亦属实例输出行为差异、如实登记（与 r16-prep-"
         "record protocol_amendment.naming「同实例跨板连续」声明不同，如实"
         "入账不作废）。"),
    ]

    honest_conclusion = (
        "本轮（development 域，同指引重复轮（零变更轮：判读指引="
        "observation-guidance-r15.md 字节复用 d5babc93、零新建指引文件+"
        "渲染零变更 renders-r14b 四图字节复用=r14/r15 轮盲读所用同一批文件+"
        "GT/阈值/协议零变更（v1.1+v1.2 维持）；instrument_change.changed="
        "false 已预注册、changed_variables=[]；唯一操纵因子=reader 实例群"
        "重抽 12 派次））12 派次 49 旗标中 39 弃权、10 非弃权：代表配置"
        "（top-i3+bottom-i1：top 中位 12 唯一、bottom 中位 5 为 i1/i2 tie "
        "按先序取并如实注明）gt_recall=0.0（0/13）、seed_match_rate=0.0"
        "（0/4，诊断口径，禁称 precision/FPR）、abstain_rate=0.764706"
        "（13/17），联合评价 not_met（gt_recall、seed_match_rate 与 "
        "abstain_rate 三项未达 APR-0011 暂行线；诊断对照，非采纳门；连续"
        "达标计数 0→0；GT 条目层 union=1/13=0.076923、agreement=0/13 双口"
        "径并列）。预注册假设（r15-dev-record-candidate-0-same-guidance-"
        "repeat）裁决（按 r16-prep-record hypothesis_test.adjudication 三"
        "分判据）=inconclusive（字母口径，唯一正式裁决）：top 全旗聚合弃权"
        "率实测=27/35=0.771429，落支=(c) 0.75<top<0.862——(a) 支基线="
        "run-r14 同口径双侧复算 18/24=0.75（live 重放与在案登记交叉核对一"
        "致，不手工抄数）不成立；(b) 支基线=run-r15 双侧复算 25/29=0.862069"
        " 同上不成立；(α) 跨轮实例群漂移与 (β) §5A 全局弃权致敏两候选解释"
        "均不排斥、归因悬置。零变更轮如实测得两轮带内落点：「r15 (iii) 违约"
        "是噪声还是致敏」未决——两轮制归因分辨力有限（(c) 带非空），"
        "inconclusive 后不得再以盲目重复轮消耗盲读，第三点须走分层（同实例"
        "群双跑）/判据侧/度量侧处置。bottom 图例效应方向未被推翻但轻微恶化"
        "信号如实在案：bottom 全旗聚合弃权率 12/14=0.857143 vs r15 基线 "
        "11/13=0.846154（恶化方向如实单列、不影响字母）；非弃权 courtyard "
        "0/0/0 维持但 courtyard 类旗标 2 条重现（applied-bottom-i2 黑点-椭"
        "圆轮廓相切/近邻、r14 同族现象部分再现；r15「零 courtyard 旗」本身"
        "呈实例群敏感——零旗标路径与有旗全弃权路径成因不同、如实分列）。"
        "机制发现（比 (iii) 归因更值钱）：黑点类存在性弃权跃升为两视角主导"
        "——top 弃权构成分型=存在性 15>接触性 11>层归属其他 1（黑点性质类"
        "存在性弃权横跨 silk/other/reroute/placement 各类=top 弃权非单一机"
        "制驱动、r15 的「5 接触+1 存在性」构成在实例群重抽下多通道化）；黑"
        "点类 12 旗全弃权连续第 4 轮（r13 8→r14 14→r15 7→r16 12）+2 派次"
        "判正常（同现象跨实例处置分化）；绿区语义化 6/6 派次「空隙/翼瓣」"
        "读法+6/6 显式援引 §5A（r15 收敛在实例群重抽下完全保持）。GT 侧："
        "r12 以来首次逐实例命中 0→1（R16T-001×GT-REVC-AP-6-R2LED2，"
        "containment 1.0、面积比 7.289285≤10 门内；union 1/13、agreement "
        "0/13 维持）——既有条目命中非新 GT、GT 零改动。守门通道几何门 "
        "R15=0→R16=0 维持（guard_ok=True 独立单列）；类别门 0→1（R16T-006 "
        "类别不符出局、r12–r15 连续零条目后本轮计数如实登记）。注意："
        "inconclusive=归因悬置、非无效——「正确测出无效同样是有效证据」；"
        "单轮 n=3、development 域只描述不断言；机制观察/度量教训单列、不凌"
        "驾不改写字母裁决；APR-0011 门（代表配置）与字母裁决分列不合并；本"
        "轮判据均为描述性边界、非门阈值（门零改动）。残余实例差异仍存（top "
        "弃权率 0.666667/0.928571/0.666667 极差 0.261904、prep1-top-i2 单派"
        "次 11 旗全弃权=轮内最高弃权格；bottom-i1 全弃权 5 旗；板内孤立焊"
        "盘组三实例三出口=判读语义歧义未穷尽）。bottom 14 旗（12 弃权+2 非"
        "弃权）零匹配属结构性（GT 13 条全部 side=top，bottom GT 无源在案 "
        "gt-audit-r1）；本轮无零旗标格（12 格全部≥1 旗，最小格=prep1-"
        "bottom-i3 单旗；item 5 口径保留备用：遇零分母→None 不编造数值）。"
        "「系统性正常→不报告」通道 bottom 六派次一致使用（§4(i) 判读路径延"
        "续，摘录在案）。工具行为混杂如实入账（12/12 派次自述「未读取盘上"
        "任何其他文件」；无「未做任何程序化处理」逐字语句=自述措辞差异如实"
        "登记；flag_id 两板各自从头编号=实例输出行为差异如实登记、编排侧按 "
        "(state, flag_id) 限定）；输出格式披露（12 件缩进格式冻结原始判读"
        "件、零改动直读）如实登记、均非盲读违规。GT 侧三候选经 gt-audit-r1 "
        "全部关闭（延续零改动，GT 侧不再有候选；r16 的 1 命中与 bottom GT "
        "无源结构相容）。不做「能力已修复/已达成」类断言；in_calibrated_"
        "range 恒 False。本批证据按协议 v1 §4 属 development 域，不得冒充"
        "留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r16-prep-record no_loosening_note：零变更"
         "重复轮无任何措辞调整空间——反放宽条款「仅因形态不熟悉、不确定其设"
         "计含义，不构成判为正常设计特征的理由」随指引本体原样生效；三分判"
         "据描述性边界与门分列）。"),
        ("R15 对照基线=calibration-run-r15.json（0c37c1cb…，在案）；R14 对照"
         "基线=calibration-run-r14.json（eb8e3521…，在案）；R8–R13 对照基线"
         "=calibration-run-r8.json（3c580eb3…）/r9（e16420e5…）/r10"
         "（622c9099…）/r11（ec05e472…）/r12（2ec2fb04…）/r13（787c4589…，"
         "在案）；判据 (a) 基线=同一聚合逻辑对 run-r14 内嵌实例记录双侧复算"
         "（18/24=0.75）、(b) 支基线=run-r15 双侧复算（25/29=0.862069），"
         "不手工抄数；轮间对比只做方向性描述（跨轮实例群混杂照旧）。"),
        ("通道归因方法：照抄 run-r15 channel_attribution 的重放口径"
         "（deviation_note 承接），R14/R15/R16 均以内嵌输入确定性重放并与 "
         "compare_v3 对拍（run-r16 channel_attribution.method）；R14/R15 十"
         "二件复算与在案登记一致、R16 十二件重放全部复现（fail-closed：候"
         "选对=applied-top-i2 [R16T-001, GT-REVC-AP-6-R2LED2]）。"),
        ("读者实例行为披露如实记录：R16 十二派次 v1.2 规约自述合规（纯 Read "
         "直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 reading_"
         "notes 原文在案；无「未做任何程序化处理」逐字语句=自述措辞差异如实"
         "登记）；输出格式披露（12 件缩进格式冻结原始判读件、零改动直读）"
         "parse 校验全部通过。跨轮 reader 实例不同+轮内实例差异=混杂因素，"
         "每视角 n=3；本轮无新增评审（pre_round_review=not_required_zero_"
         "change_round：同指引重复轮先例 r10、无新干预引入）——轮前诊断无新"
         "增（渲染零变更、零探针）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=inconclusive "
         "维持不变（inconclusive=归因悬置、非无效——预注册描述性边界下的方"
         "向性记录；单轮 n=3 小样本方向性证据；主通道三分判据（≤0.75、"
         "≥0.862、两值之间）与 APR-0011 门分开表述、互不凌驾：门联合评价"
         "（代表配置）=not_met 如实分列）；不得回溯改判既往轮次（r8–r15 字"
         "母裁决维持不变）。"),
        ("度量教训在案（供 R17 预注册参考、本轮不追溯适用）：两轮制归因的分"
         "辨力有限（(c) 带非空）——若 inconclusive，第三点须靠分层（同实例"
         "群双跑）或判据侧/度量侧处置，不得以连续 inconclusive 反复消耗盲读"
         "（per r16-prep-record metric_lesson_separate）；top 弃权构成分型"
         "（接触性 11+存在性 15+其他 1）已为「分辨率受限 vs 语义歧义 vs 现"
         "象本身可疑」的处置轴选择提供第一手分解（见 "
         "next_iteration_targets[0] 零盲读度量侧分解包候选）。"),
    ]

    next_iteration_targets = [
        ("R17 第一候选=零盲读度量侧分解包（development 域编排侧重分析，零新"
         "盲读、零新渲染）：对 r13–r16 既有 reader-raw 做弃权理由家族分型统"
         "计（接触性/存在性-黑点类/语义混淆类/其他），统一口径定义+四轮分布"
         "表+top 高弃权构成结论——为「分辨率受限 vs 语义歧义 vs 现象本身可"
         "疑」的处置轴选择提供证据；不回写既往轮次字母、不触 GT、不触阈值"
         "（r16 top 弃权构成分型=接触性 11+存在性 15+层归属其他 1 为该方法"
         "论的单轮先例）。"),
        ("次候选=top 渲染分辨率倍增（仪器轮：dpi 640→1280 单变量，须预注册+"
         "framing 先冻结+探针先验证[r14 首试探针证伪教训]）——检验接触性/"
         "存在性弃权的分辨率依赖（r16 top 弃权 27 条中接触性 11+存在性 15 "
         "多数含「当前分辨率」措辞；当前渲染=renders-r14b 四图字节复用、"
         "dpi 640 自 r5 起未变；渲染侧变更、须预注册+声明零仪器变更纪律例"
         "外）。"),
        ("黑点类专项候选（连续 4 轮主导：r13 8→r14 14→r15 7→r16 12 旗全弃"
         "权+判正常派次分化）：渲染侧放大观察或指引 §5 同类「机械孔正常形"
         "态」中性说明[指引侧单变量、反放宽条款逐字保留、防放宽审查]——两"
         "分支均须预注册后执行（§5A 先例=仪器事实注记、非判据，不降低任何"
         "责任门槛）。"),
        ("留出集运行时机=开发线收敛判断（须用户拍板）：r16 字母=inconclusive"
         "→top 轴收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未"
         "达成，不得写成已达成）；in_calibrated_range 恒 False 直到正式采纳"
         "（须人工批准）；达标证据仍须留出集（out/v3-tl2/holdout/"
         "HOLDOUT-PLAN.md a4b80193… 与 datasets/holdout-candidates-r1 在"
         "案）。"),
        ("GT 侧维持全关闭声明延续：r8 轮同日只读审计 gt-audit-r1（1f20554a…）"
         "三候选全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、"
         "L1NB 框径=合理维持现框），r9–r16 延续零改动——GT 侧已全部关闭；"
         "r16 的 1 命中=既有条目 GT-REVC-AP-6-R2LED2 命中（union 1/13="
         "0.076923、agreement 0/13）、非新 GT、GT 零改动；bottom 零匹配的"
         "结构性原因在案（GT 13 条全部 side=top）。"),
    ]

    return {
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r15": directional_observation_vs_r15,
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"],
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev15["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r16 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r16 全旗标合计 39/49=0.795918 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R15 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 与 abstain_rate 0.764706>0.5 "
                         "三项未达暂行线；gt_count 13≥12 单分项入线）——GT 条"
                         "目层 union 口径 1/13=0.076923 亦未达 0.75（双口径"
                         "与门分列如实；union=既有条目 AP-6 命中、非新 GT）"),
            },
        },
        "kind": KIND,
        "next_iteration_targets": next_iteration_targets,
        "notes": notes,
        "preregistration_chain": chain,
        "preregistration_chain_note": (
            "预注册链（含哈希）：round15-dev-record.json（e981897c…，"
            "next_iteration_targets[0] 同指引重复轮候选原文被 r16-prep-"
            "record 逐字摘录预注册+用户 2026-09-08「继续迭代到收敛」既定指"
            "令（user_directive_note 在案））→r16-prep-record.json"
            "（46fbd15b…，本轮预注册件，measurement_design 五条聚合口径与 "
            "hypothesis_test.adjudication 三分判据（≤0.75/≥0.862/两值之间）"
            "先于盲读冻结；instrument_change.changed=false；"
            "changed_variables=[]；manipulated_factor=reader 实例群重抽）"
            "→判读指引=observation-guidance-r15.md（d5babc93…）字节复用零"
            "写入（本轮零新建指引文件；§2–§7 判据与 §5A 仪器注记随本体原样"
            "生效）→渲染零变更（renders-r14b 四图字节复用=四 PNG sha 与 "
            "render-witness-r14b.json b63771f9 登记值逐一相等，即 r14/r15 "
            "轮盲读所用同一批文件）→12 次盲读（实例群全部重抽）→run-r16"
            "（2c1f8265…，本链执行落盘）；GT 重投影沿用 derivation-log-r5."
            "json（62343380…）零新派生（GT 全部 side=top 且 top 渲染零变更"
            "=重投影输入未变；bottom 渲染字节复用不触及）；GT 冻结纪律：轮"
            "后未增删改；gt-audit-r1（1f20554a…）结论维持 GT 零改动（三候"
            "选关闭，gt_audit_reference 在案）"),
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域同指引重复轮（零变更轮，第十六轮）：判读指引="
            "observation-guidance-r15.md 字节复用（d5babc93 实测锚、零新建"
            "指引文件；§2–§7 判据与 §5A 渲染配色仪器注记随本体原样生效——"
            "字节复用=零措辞调整空间；示例旗 ID 前缀保持 R15T-/R15B- 落盘"
            "原文，R16 派次前缀由派发指令层覆盖）+渲染零变更（renders-r14b "
            "四图字节复用=r14/r15 轮盲读所用同一批文件，四 PNG sha 与 "
            "witness 登记值逐一相等）+GT 集/协议阈值与度量版本/比较器常量零"
            "改动（GT 重投影沿用 derivation-log-r5——零新派生；gt-audit-r1 "
            "三候选关闭结论延续）；协议 v1.1+v1.2 维持无新增版本；"
            "instrument_change.changed=false 已预注册（changed_variables="
            "[]）；唯一操纵因子=reader 实例群重抽（12 派次全部重抽，r10 零"
            "变更重复轮先例再现）；检验 round15-dev-record "
            "next_iteration_targets[0] 候选假设 "
            "r15-dev-record-candidate-0-same-guidance-repeat（判据="
            "r16-prep-record.json hypothesis_test.adjudication 三分判据 "
            "(a)≤0.75/(b)≥0.862/(c) 两值之间，轮后如实执行：字母裁决唯一正"
            "式+机制观察/度量教训单列）；主通道三分判据与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独立计算、互不凌驾、分"
            "开表述；measurement_design 五条聚合口径先于盲读冻结；按协议 v1 "
            "§4，迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R16, "sha256": run16_sha},
        "schema_version": SCHEMA_VERSION,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s59-cal-r16-devrecord] round16-dev-record: {status}")
    print(f"[s59-cal-r16-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch={dev['hypothesis_test_i']['measurement'][
              'letter_branch']}")
    print(f"[s59-cal-r16-devrecord] 三分判据: (a) 27/35=0.771429≤0.75 不成立"
          f"（run-r14 双侧复算 18/24=0.75）；(b) ≥0.862（run-r15 双侧复算 "
          f"25/29=0.862069）不成立；(c) 0.75<top<0.862 命中 ⇒ inconclusive")
    print(f"[s59-cal-r16-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s59-cal-r16-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0")
    print(f"[s59-cal-r16-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s59-cal-r16-devrecord] R16 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=inconclusive 唯一正式；机制观察/度量教训单列不"
          "凌驾；in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
