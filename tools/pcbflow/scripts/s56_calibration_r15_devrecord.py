#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s56_calibration_r15_devrecord.py — R15 CLOSE 包 B：
round15-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律）。

R15=指引侧颜色-图层映射配套轮（单变量指引侧变更轮：判读指引增补 §5A
渲染配色仪器注记节——颜色→来源映射显式化（橙 (255,165,0)=白墨图元
重着色、绿 (0,128,0)=板内空隙白重着色非图元；数值事实自
render-framing-r14b/render-witness-r14b 结构探测转录）；observation-
guidance-r15.md（d5babc93）由 r13 指引（c28806e1）机械变换生成、
§2–§7 判据文本零变更；渲染零变更（renders-r14b 四图字节复用=r14 轮
盲读所用同一批文件）；GT/阈值零变更；instrument_change.changed=false
已预注册）。预注册假设（r14-dev-record-candidate-0-guidance-color-
legend）三分判据轮后裁决=reject（唯一正式裁决）：
- 条件 (i) bottom courtyard 非弃权 0/0/0 满足（本轮=零旗标路径——
  bottom 零 courtyard 类旗标=分类通道转移，与 r13 判正常收敛路径/
  r14 全弃权路径成因三分）；
- 条件 (ii) bottom 全旗聚合弃权率 11/13=0.846154≤10/11 满足（混淆
  性弃权回落；r14 全弃权 14/14=1.0）；
- 条件 (iii) top 全旗聚合弃权率 25/29=0.862069>run-r14 同口径双侧
  复算基线 18/24=0.75 违约 ⇒ 拒绝支=第 (iii) 项（top 全旗聚合弃权
  率回退：其他轴回退）。
机制观察/度量教训单列不凌驾字母裁决；机制观察=图例对 bottom 主通道
生效（混淆回落+绿区语义化三实例收敛为空隙/翼瓣几何（2/3 实例显式援
引 §5A）+r14 的 4 条 bottom courtyard 弃权未再现）；度量教训=关系式
跨轮守门判据 (iii) 对跨轮实例群漂移敏感（r10 教训在新轴复现：top
0.75→0.862 无法区分「§5A 全局弃权致敏」与「实例群噪声」，须同指引
重复轮消解）。

生成器纪律：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-08"；
- 防覆写护栏：round15-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round15-dev-record.json 一件（s55 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s56_calibration_r15_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-08-r15"
ROUND_LABEL = "r15"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round15_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R15 = "out/v3-tl2/calibration/calibration-run-r15.json"
REL_RUN_R14 = "out/v3-tl2/calibration/calibration-run-r14.json"
REL_RUN_R13 = "out/v3-tl2/calibration/calibration-run-r13.json"
REL_PREP_R15 = "out/v3-tl2/calibration/r15-prep-record.json"
REL_DEV_R14 = "out/v3-tl2/calibration/round14-dev-record.json"
REL_OUT = "out/v3-tl2/calibration/round15-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 主通道三分判据实测锚（写盘前 fail-closed 与 run-r15 盘上值逐一核对）
EXPECT_TOP_ABSTAIN_R15 = 25
EXPECT_TOP_FLAGS_R15 = 29
EXPECT_TOP_RATE_R15 = 0.862069
EXPECT_TOP_BASELINE_LIVE = "18/24"
EXPECT_TOP_BASELINE_VALUE = 0.75
EXPECT_BOTTOM_ABSTAIN_R15 = 11
EXPECT_BOTTOM_FLAGS_R15 = 13
EXPECT_BOTTOM_RATE_R15 = 0.846154
EXPECT_COURTYARD_BASELINE = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_COUNTS = {"top-i1": 11, "top-i2": 10, "top-i3": 8,
                 "bottom-i1": 4, "bottom-i2": 4, "bottom-i3": 5}
EXPECT_ABSTAIN = {"top-i1": 10, "top-i2": 8, "top-i3": 7,
                  "bottom-i1": 3, "bottom-i2": 3, "bottom-i3": 5}
EXPECT_RATES = {"top-i1": 0.909091, "top-i2": 0.8, "top-i3": 0.875,
                "bottom-i1": 0.75, "bottom-i2": 0.75, "bottom-i3": 1.0}
EXPECT_R14_RATES = {"top-i1": 0.833333, "top-i2": 0.75, "top-i3": 0.7,
                    "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 1.0}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s56-cal-r15-devrecord] FAIL: {msg}")


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


def _view_abstain_aggregate(run: dict, view: str):
    names = [n for n in INSTANCE_ORDER if n.startswith(view)]
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run14: dict, run13: dict, prep: dict,
                  dev14: dict) -> None:
    # ---- run-r15 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r15":
        _fail("run kind 不符")
    if (run["round_id"], run["round_label"], run["declared_date"],
            run["evaluation_domain"]) != (ROUND_ID, ROUND_LABEL,
                                          DECLARED_DATE, "development"):
        _fail("run 声明常量不符")
    ht = run["hypothesis_test"]
    if ht["hypothesis_id"] != "r14-dev-record-candidate-0-guidance-color-legend":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "reject":
        _fail("verdict != reject")
    m = ht["measurement"]
    if (m["crit1_bottom_courtyard_non_abstain_all_zero"] is not True
            or m["crit2_bottom_abstain_le_10_11"] is not True
            or m["crit3_top_abstain_le_r14_baseline"] is not False):
        _fail("三分判据布尔不符")
    if "第 (iii) 项" not in m["reject_branch"]:
        _fail("拒绝支不符")
    # (iii) 基线双侧复算（同一聚合逻辑对 run-r14 内嵌输入重算）
    f14, a14 = _view_abstain_aggregate(run14, "top")
    if (f14, a14) != (24, 18) or m["top_abstain_rate_r14_baseline_live"] != \
            EXPECT_TOP_BASELINE_LIVE or \
            m["top_abstain_rate_r14_baseline_value"] != \
            EXPECT_TOP_BASELINE_VALUE:
        _fail("top r14 基线复算不符（18/24）")
    fb14, ab14 = _view_abstain_aggregate(run14, "bottom")
    if (fb14, ab14) != (14, 14):
        _fail("bottom r14 全弃权复算不符（14/14）")
    # 本轮实测
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R15, EXPECT_TOP_ABSTAIN_R15):
        _fail("top 聚合不符（25/29）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R15, EXPECT_BOTTOM_ABSTAIN_R15):
        _fail("bottom 聚合不符（11/13）")
    if m["top_abstain_rate_r15"] != EXPECT_TOP_RATE_R15 or \
            m["bottom_abstain_rate_r15"] != EXPECT_BOTTOM_RATE_R15:
        _fail("聚合弃权率不符")
    if "25/29" not in m["top_abstain_rate_r15_arithmetic"] or \
            "11/13" not in m["bottom_abstain_rate_r15_arithmetic"]:
        _fail("聚合算式文本不符")
    cy15 = _courtyard_non_abstain_by_instance(run)
    if cy15 != EXPECT_COURTYARD_BASELINE or \
            m["bottom_courtyard_non_abstain_by_instance_r15"] != \
            EXPECT_COURTYARD_BASELINE or \
            m["bottom_courtyard_flags_total_r15"] != 0:
        _fail("courtyard 基线复算不符（0/0/0）")
    cy13 = _courtyard_non_abstain_by_instance(run13)
    cy14 = _courtyard_non_abstain_by_instance(run14)
    if cy13 != EXPECT_COURTYARD_BASELINE or cy14 != \
            EXPECT_COURTYARD_BASELINE:
        _fail("r13/r14 courtyard 基线复算不符")
    b13f = sum(run13["instances"][n]["combined"]["flag_count"]
               for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    b13a = sum(run13["instances"][n]["combined"]["abstain_count"]
               for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    if (b13f, b13a) != (11, 10):
        _fail("r13 bottom 聚合复算不符（10/11）")
    # 判据引用=prep-record 原文（逐字一致）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("supported_requires_all", "reject_if",
              "descriptive_boundary_note", "mechanism_observation_separate",
              "metric_lesson_separate"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 守门通道（回落 1→0；独立单列）
    if m["guard_channel"]["guard_ok"] is not True:
        _fail("guard_channel 应为回落 True")
    if len(run["channel_attribution"]["channel_1_geometry_gate"][
            "r15_area_ratio_rejected_entries"]) != 0 or \
            len(run14["channel_attribution"]["channel_1_geometry_gate"][
                "r14_area_ratio_rejected_entries"]) != 1:
        _fail("几何门 1→0 复核不符")
    # 旗数/弃权率（逐实例）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN or \
            rates != EXPECT_RATES:
        _fail("逐实例旗数/弃权率不符")
    r14rates = {n: run14["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER}
    if r14rates != EXPECT_R14_RATES:
        _fail("r14 逐实例弃权率不符")
    # 代表配置与门
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (14, 11, 0.785714, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0:
        _fail("联合门/连续计数不符")
    dual = run["gt_match_dual"]
    if dual["union"]["count"] != 0 or dual["agreement"]["count"] != 0 or \
            dual["denominator"] != 13:
        _fail("双口径不符（0/13）")
    # instrument_change.changed=false（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not False or \
            prep["instrument_change"]["changed"] is not False or \
            prep["no_instrument_change"] is not True:
        _fail("instrument_change.changed 应为 false")
    ids = [v["id"] for v in run["instrument_change"][
        "changed_variables_registered"]]
    if ids != [v["id"] for v in prep["changed_variables"]] or ids != [
            "guidance-color-legend-instrument-note"]:
        _fail("变更变量登记不符（恰一项指引侧）")
    # 黑点类（r14 14 旗→r15 7 旗全弃权+3 派次判正常）
    bdt = ht["mechanism_observation"]["black_dot_tracking"]
    if bdt["all_abstain"] is not True or sum(bdt["by_instance"].values()) \
            != 7 or len(bdt["black_dot_flags"]) != 7:
        _fail("黑点类 7 旗不符")
    if "3 派次判正常" not in bdt["notes_normal_dispositions"]:
        _fail("黑点类 3 派次判正常不符")
    bdt14 = dev14["hypothesis_test_i"]["mechanism_observation"][
        "black_dot_tracking"]
    if sum(bdt14["by_instance"].values()) != 14:
        _fail("r14 黑点类 14 旗不符")
    # 绿区语义化（三实例空隙/翼瓣收敛；2/3 实例显式援引 §5A）
    gs = ht["mechanism_observation"]["green_semantics_by_instance"]
    cited = [n for n in ("bottom-i1", "bottom-i2", "bottom-i3")
             if gs["green_semantics_by_instance"][n]["§5A_cited"]]
    if sorted(cited) != ["bottom-i2", "bottom-i3"] or \
            gs["green_semantics_by_instance"]["bottom-i1"]["§5A_cited"]:
        _fail("§5A 显式援引 2/3 实例不符")
    # run_record_ref 实测=登记
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R15):
        _fail("prep-record sha 实测与登记不符")
    if dev14["hypothesis_test_i"]["verdict"] != "reject":
        _fail("r14 dev-record verdict 不符")


def build_dev_record() -> dict:
    """构建 round15-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R15)
    run14 = _json_load(REL_RUN_R14)
    run13 = _json_load(REL_RUN_R13)
    prep = _json_load(REL_PREP_R15)
    dev14 = _json_load(REL_DEV_R14)
    _verify_facts(run, run14, run13, prep, dev14)

    ht = run["hypothesis_test"]
    m = ht["measurement"]
    mo = ht["mechanism_observation"]
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

    run14_sha = _sha(REL_RUN_R14)
    run15_sha = _sha(REL_RUN_R15)

    # 联合评价趋势：r5–r14 行=round14-dev-record 在案行（冻结转录）；
    # r15 行=本轮 run 实测
    trend_rows = list(dev14["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r15",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R15, "sha256": run15_sha},
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
            "全旗标合计口径仅作附记（36/42=0.857143，非弃权 6+弃权 36）；"
            "本轮预注册主通道=三分判据（(i) bottom courtyard 非弃权 0/0/0；"
            "(ii) bottom 全旗聚合弃权率 11/13=0.846154≤10/11；(iii) top "
            "全旗聚合弃权率 25/29=0.862069 对照 run-r14 双侧复算 18/24="
            "0.75），实例层/视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": dict(fc["by_instance"]) and {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("本轮无零旗标实例、两视角弃权率全部有定义（bottom 极差 "
                     "0.25=1.0−0.75=bottom-i3 全弃权与 i1/i2 回落并存；top "
                     "极差 0.109091 较 r14 的 0.133333 相近、整体水平回升="
                     "条件 (iii) 违约的构成）"),
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
                 "实例，两波次串行保序）；R15T/R15B 前缀已随 r15 指引 §6 落盘"
                 "固化、无需派发层覆盖（per r15-prep-record "
                 "protocol_amendment.naming）；flag_id 两板各自从头编号=读者"
                 "实例输出行为差异如实登记（编排侧按 (state, flag_id) 限定，"
                 "跨板同号不混淆）；v1.2 工具规约沿用 12/12 派次自述合规与"
                 "输出格式披露（12 件缩进格式冻结原始判读件、零改动直读；围栏"
                 "剥离先例不适用）如实登记为混杂因素披露，不作废"),
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
            "representative_configuration（top-i2+bottom-i1，"
            "measurement_design item 4；top 中位 10 由 top-i2 唯一持有"
            "（11/10/8）无 tie；bottom 中位 4 为 bottom-i1/bottom-i2 tie、"
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

    directional_observation_vs_r14 = [
        ("R14→R15 派发与旗标量对照：盲读派次 12→12（协议侧 v1.2 沿用无新增"
         "版本：12/12 派次自述「未读取盘上任何其他文件」；r15 notes 无 r14 "
         "的「未做任何程序化处理」逐字语句=自述措辞差异如实登记）；旗标 "
         "38→42（六实例旗数 top 6/8/10→11/10/8、bottom 4/3/7→4/4/5；非弃权 "
         "6→6、弃权 32→36）；全旗标合计弃权率 0.842105（32/38，附记口径）→"
         "0.857143（36/42，附记口径）；预注册主通道三分判据：条件 (i) bottom "
         "courtyard 非弃权 0/0/0 维持（本轮=零旗标路径，bottom 零 courtyard "
         "类旗标=分类通道转移）；条件 (ii) bottom 全旗聚合弃权率 11/13="
         "0.846154≤10/11 满足（r14 全弃权 14/14=1.0 回落）；条件 (iii) top "
         "全旗聚合弃权率 25/29=0.862069>run-r14 同口径双侧复算 18/24=0.75 "
         "违约⇒字母裁决=reject（拒绝支=第 (iii) 项：top 全旗聚合弃权率回退"
         "——其他轴回退）；代表配置（top=top-i2：中位 10 唯一（11/10/8）无 "
         "tie；bottom=bottom-i1：中位 4 tie（4/4/5）按先序取、如实注明）"
         "弃权率 0.833333（10/12）→0.785714（11/14）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.833333/0.75/"
         "0.7（r14，极差 0.133333）→0.909091/0.8/0.875（r15，极差 0.109091）"
         "——top 渲染零变更（r15=renders-r14b 四图字节复用）下弃权率整体水平"
         "回升（条件 (iii) 违约构成；跨轮实例群不同=混杂照旧、方向性描述）；"
         "bottom 1.0/1.0/1.0（r14，极差 0.0=全弃权）→0.75/0.75/1.0（r15，"
         "极差 0.25）——bottom 混淆性弃权回落、出现 2 条非弃权 placement 旗"
         "（弃权出口不再垄断 bottom；bottom-i3 仍全弃权 5 旗）；旗数 top "
         "6/8/10→11/10/8、bottom 4/3/7→4/4/5；本轮无零旗标实例、弃权率全部"
         "有定义。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r14 零匹配→r15 "
         "连续第四轮零匹配（六实例全部 matches=0）：GT 条目层 union=0/13"
         "（0.0）、agreement=0/13（0.0，连续四轮均 0）；代表配置 gt_recall_"
         "total 0.0（0/13）、seed_match_rate 0.0（0/3，诊断口径，禁称 "
         "precision/FPR）。bottom 13 旗（11 弃权+2 非弃权）零匹配属结构性："
         "GT 13 条全部 side=top、bottom 无 GT 在案（gt-audit-r1：bottom GT="
         "无源已关闭）⇒ bottom 旗标与 GT 匹配应为空，如实；top 非弃权旗 4 条"
         "（i1 1 reroute+i2 2 silk+i3 1 reroute）与同态 GT 零 ≥0.5 "
         "containment 交叠（r14 的 R14T-002 几何门出局条目未再现）。"),
        ("通道归因（vs R14，预注册重放方法）：几何门面积比出局 1→0（r14 回升"
         "未延续：r14 唯一条目 R14T-002×GT-REVC-AP-7-C31U4 宽泛丝印框未再现；"
         "guard_ok=True 独立单列、不构成 r15 字母裁决输入——r15 预注册 "
         "support 条件不含守门要件）；类别门 0→0（R11T-012↔GT-REVC-AP-8-"
         "R1Q2 仍为 r11 唯一条目、r12–r15 无再现）；视角门 0→0（r15 top 非弃"
         "权旗 4 条/bottom 非弃权旗 2 条与同态 GT 零视角错位交叠；bottom 无 "
         "GT 在案）。通道链自 r6：几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→"
         "r12=0→r13=0→r14=1→r15=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→"
         "r12=0→r13=0→r14=0→r15=0。重放与 compare_v3 对拍一致（R13/R14 十二"
         "件复算与在案登记一致、R15 十二件全部复现：候选对=空集）。"),
        ("预注册假设（r14-dev-record-candidate-0-guidance-color-legend）字母"
         "裁决=reject（预注册拒绝支=第 (iii) 项：top 全旗聚合弃权率回退——"
         "其他轴回退；r15-prep-record hypothesis_test.adjudication 判据原文"
         "执行；唯一正式裁决）。机制观察单列（不凌驾）：(a) 条件 (i) 满足但"
         "成因与 r13/r14 三分（r13=§4(i) 判正常收敛路径、r14=全弃权路径、"
         "r15=零旗标路径——bottom 13 旗=courtyard 0+placement 6+other 7，"
         "分类通道转移如实分列）；(b) 图例对 bottom 主通道生效：bottom 混淆"
         "性弃权回落（11/13=0.846154≤10/11、三实例 0.75/0.75/1.0、出现 2 条"
         "非弃权 placement 旗=弃权出口不再垄断）+绿区语义化三实例收敛为"
         "「空隙/翼瓣几何」读法（r14 的三实例三种图元化误读=轮廓/连接形态/"
         "courtyard 矩形未再现；其中 bottom-i2 两派次+bottom-i3 prep1 共 3 "
         "派次显式援引 §5A 仪器注记=2/3 实例）+r14 的 4 条 bottom courtyard "
         "弃权（黑点骑跨轮廓 2+阵列顶端疑似接触 2）未再现（bottom courtyard "
         "类旗标 0）；(c) top 轴回退独立构成：top 弃权 25/29=courtyard 6"
         "（5 接触性+1 存在性出口）+silk 15（13 弃权 2 非弃权）+黑点类 1+"
         "其他 3——top 渲染零变更下 0.75→0.862069 回升与图例的 bottom 效应"
         "并存=两轴分列不合并；(d) 守门通道回落 R14=1→R15=0（guard_ok=True "
         "独立单列）。"),
        ("工具行为（协议侧 v1.2 沿用第四轮，如实入账）：R15 十二派次全部以 "
         "Read 工具直读内嵌图像、逐派次 reading_notes 自述「仅依据给定 PNG "
         "可见内容独立判读，未读取盘上任何其他文件」（12/12 逐字摘录在案 "
         "reader_tool_evidence）；r15 notes 无「未做任何裁剪/放大/像素分析等"
         "程序化处理」逐字语句——与 r14 十二派次措辞不同，属自述措辞差异、"
         "如实登记（工具行为轴=派发指令 v1.2 硬性条款照旧钉住，r10/r11 实测 "
         "8/12 派次自选 PIL 局部裁剪放大的自选异质性自 r12 规约生效起持续为"
         "零）；全部判读输入仍严格限于（指引+该 PNG），零外部信息、零 GT/零"
         "诊断/除指引 §5A 仪器注记外零 legend=非盲读违规；跨轮实例不同+轮内"
         "实例差异=混杂因素照旧声明（reader_instance_note）。"),
        ("输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件=缩进"
         "格式冻结原始判读件、本轮零改动直读（direct JSON 解析；围栏剥离本"
         "先例不适用——12 件均为裸 JSON 文本）；12 件 parse 校验全部通过、均"
         "非盲读违规、拒收清单为空。flag_id 编号行为差异如实登记：r15 实测="
         "两板各自从头编号（同一实例 applied 与 prep1 各自独立起编、跨板同号"
         "如实登记）——与 r13/r14 的「同实例跨板连续」不同，属读者实例输出"
         "行为差异、如实入账不作废。"),
        ("courtyard 被动追踪（run-record 链先例延续，零阈值改动零期望）：R15 "
         "courtyard 类旗标 6 条全部弃权且全部 top（非弃权 0）零命中（r8=1→"
         "r9=0→r10=1→r11=3→r12=0→r13=0→r14=0→r15=0）；bottom 零 courtyard "
         "类旗标（r12 非弃权 20 条→r13 0 条→r14 弃权 4 条→r15 零旗标）；"
         "黑点类 7 旗全弃权+3 派次判正常（prep1-top-i1/applied-top-i3/"
         "prep1-bottom-i1 判基准点/定位类正常未报告=同现象跨实例处置分化）；"
         "reroute 类 4 条（2 非弃权边界报告+2 存在性弃权；R15T-001 含「蛇形」"
         "子串=否定式收窄判据援引、机械命中与语义裁定分记；产量链 r8=1→r9=0"
         "→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4；滥用型链 r10=2→r11=1→r12="
         "0→r13 被动追踪=1→r14=0→r15 机械命中=1 但语义=正确排除候选解释）。"),
        ("跨轮 flag_id 不构成同旗配对（R13T/R13B、R14T/R14B 与 R15T/R15B 来"
         "自不同 reader 实例、不同判读实例）；通道归因是通道级不是旗级"
         "（run-r15 channel_attribution.pairing_caveat；r15 两板各自从头编号"
         "亦属实例输出行为差异、如实登记）。"),
    ]

    honest_conclusion = (
        "本轮（development 域，单变量指引侧变更轮（判读指引增补 §5A 渲染配色"
        "仪器注记节：颜色→来源映射显式化——橙 (255,165,0)=白墨图元重着色、绿 "
        "(0,128,0)=板内空隙白重着色（非图元）；§5A=仪器事实注记、非判据；"
        "observation-guidance-r15.md=d5babc93 由 r13 指引 c28806e1 机械变换"
        "生成、§2–§7 判据文本零变更+渲染零变更（renders-r14b 四图字节复用=r14 "
        "轮盲读所用同一批文件）+GT/阈值零变更；instrument_change.changed=false "
        "已预注册））12 派次 42 旗标中 36 弃权、6 非弃权：代表配置（top-i2+"
        "bottom-i1：top 中位 10 唯一、bottom 中位 4 为 i1/i2 tie 按先序取并"
        "如实注明）gt_recall=0.0（0/13）、seed_match_rate=0.0（0/3，诊断口"
        "径，禁称 precision/FPR）、abstain_rate=0.785714（11/14），联合评价 "
        "not_met（gt_recall、seed_match_rate 与 abstain_rate 三项未达 "
        "APR-0011 暂行线；诊断对照，非采纳门；连续达标计数 0→0；GT 条目层 "
        "union=0/13、agreement=0/13 双口径并列）。预注册假设"
        "（r14-dev-record-candidate-0-guidance-color-legend）裁决（按 "
        "r15-prep-record hypothesis_test.adjudication 三分判据）=reject（字"
        "母口径，唯一正式裁决）：条件 (i) bottom 三实例 courtyard 类非弃权旗"
        "数实测=0/0/0（对照 r13/r14 的 0/0/0，live 重放交叉核对一致）满足——"
        "但成因与 r13/r14 三分：r15 bottom 零 courtyard 类旗标（13 旗="
        "placement 6+other 7），非弃权 courtyard=0 系零旗标路径、条件自动满"
        "足（分类通道转移如实记入机制观察）；条件 (ii) bottom 全旗聚合弃权率"
        "实测=11/13=0.846154≤10/11（r13 基线 10/11=0.909091，run-r13 内嵌记"
        "录重放交叉核对一致）满足——bottom 混淆性弃权较 r14 全弃权（14/14="
        "1.0）回落；条件 (iii) top 全旗聚合弃权率实测=25/29=0.862069>run-r14 "
        "同口径聚合弃权率（同一聚合逻辑对 run-r14 内嵌实例记录双侧复算=18/24="
        "0.75，不手工抄数）违约 ⇒ 拒绝支=第 (iii) 项（top 全旗聚合弃权率回"
        "退：其他轴回退）——top 轴回退（top 渲染零变更下 r14→r15 弃权水平 "
        "0.75→0.862069 回升），图例/指引侧配套未消除 top 轴弃权水平。三项判"
        "据分开如实记录、不合并；守门通道（top 几何门）R14=1→R15=0 回落独立"
        "单列（guard_ok=True；r15 support 条件不含守门要件）。注意：reject="
        "预注册描述性边界下的方向性归因、非统计证明——「正确测出无效同样是"
        "有效证据」；单轮 n=3、跨轮实例群混杂照旧（development 域只描述不断"
        "言）；机制观察/度量教训单列、不凌驾不改写字母裁决；APR-0011 门（代"
        "表配置）与裁决=reject 分列不合并；本轮判据均为描述性边界、非门阈值"
        "（门零改动）。四条机制结论如实单列：①图例对 bottom 主通道生效——混"
        "淆性弃权回落（11/13=0.846154≤10/11；三实例 0.75/0.75/1.0；出现 2 条"
        "非弃权 placement 旗=弃权出口不再垄断 bottom）+绿区语义化三实例收敛"
        "为「空隙/翼瓣几何」读法（r14 的三实例三种图元化误读=轮廓/连接形态/"
        "courtyard 矩形未再现；其中 2/3 实例（bottom-i2 两派次+bottom-i3 "
        "prep1 共 3 派次）显式援引 §5A 仪器注记）+r14 的 4 条 bottom "
        "courtyard 弃权（黑点骑跨轮廓 2+阵列顶端疑似接触 2）未再现（bottom "
        "courtyard 类旗标 0）；②top 轴回退独立构成——top 弃权 25/29："
        "courtyard 6（5 接触性+1 存在性出口；r13 8/8→r14 13/13→r15 5/6）+"
        "silk 15（13 弃权 2 非弃权）+黑点类 1+其他 3；③度量教训——关系式跨"
        "轮守门判据 (iii) 对跨轮实例群漂移敏感（r10 教训在新轴复现）：top "
        "0.75→0.862 无法区分「§5A 全局弃权致敏」与「实例群噪声」，须同指引重"
        "复轮消解（next_iteration_targets[0]；R16 第一候选）；④守门通道 "
        "R14=1→R15=0 回落（r14 唯一条目 R14T-002×GT-REVC-AP-7-C31U4 未再现；"
        "r15 top 非弃权旗 4 条与同态 GT 零 ≥0.5 containment 交叠）=门在工作"
        "的方向性记录。残余实例差异仍存（top 弃权率 0.909091/0.8/0.875 极差 "
        "0.109091；bottom-i3 仍全弃权 5 旗；黑点类 7 旗全弃权+3 派次判正常="
        "同现象跨实例处置分化；板内孤立焊盘组/边缘节距空档多派次不同出口），"
        "判读语义歧义未穷尽。bottom 13 旗零匹配属结构性（GT 13 条全部 side="
        "top，bottom GT 无源在案 gt-audit-r1）；本轮无零旗标格（12 格全部≥1 "
        "旗，最小格=prep1-bottom-i1 单旗；item 5 口径保留备用：遇零分母→"
        "None 不编造数值）。「系统性正常→不报告」通道 bottom 六派次一致使用"
        "（§4(i) 判读路径延续，摘录在案）。工具行为混杂如实入账（12/12 派次 "
        "v1.2 合规自述在案：自述「未读取盘上任何其他文件」；无 r14 的「未做"
        "任何程序化处理」逐字语句=自述措辞差异如实登记；flag_id 两板各自从头"
        "编号=实例输出行为差异如实登记、编排侧按 (state, flag_id) 限定）；输"
        "出格式披露（12 件缩进格式冻结原始判读件、零改动直读；围栏剥离先例不"
        "适用）如实登记、均非盲读违规。GT 侧三候选经 gt-audit-r1 全部关闭（延"
        "续零改动，GT 侧不再有候选；r15 matches=0 与 bottom GT 无源结构相"
        "容）。不做「能力已修复/已达成」类断言；in_calibrated_range 恒 "
        "False。本批证据按协议 v1 §4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r15-prep-record no_loosening_note：本轮指"
         "引侧变更不触碰任何判据文本（§2–§7 逐字承 r13，§5A 为仪器事实注记、"
         "非判据）；三分判据描述性边界与门分列）。"),
        ("R14 对照基线=calibration-run-r14.json（eb8e3521…，在案）；R13 对照"
         "基线=calibration-run-r13.json（787c4589…，在案）；R8–R12 对照基线"
         "=calibration-run-r8.json（3c580eb3…）/r9（e16420e5…）/r10"
         "（622c9099…）/r11（ec05e472…）/r12（2ec2fb04…，在案）；判据 (iii) "
         "基线=同一聚合逻辑对 run-r14 内嵌实例记录双侧复算（18/24=0.75），不"
         "手工抄数；轮间对比只做方向性描述（跨轮实例群混杂照旧）。"),
        ("通道归因方法：照抄 run-r14 channel_attribution 的重放口径"
         "（deviation_note 承接），R13/R14/R15 均以内嵌输入确定性重放并与 "
         "compare_v3 对拍（run-r15 channel_attribution.method）；R13/R14 十"
         "二件复算与在案登记一致、R15 十二件全部复现（fail-closed）。"),
        ("读者实例行为披露如实记录：R15 十二派次 v1.2 规约自述合规（纯 Read "
         "直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 reading_"
         "notes 原文在案；无「未做任何程序化处理」逐字语句=自述措辞差异如实"
         "登记）；输出格式披露（12 件缩进格式冻结原始判读件、零改动直读；围"
         "栏剥离先例不适用）parse 校验全部通过。跨轮 reader 实例不同+轮内实"
         "例差异=混杂因素，每视角 n=3；本轮无用户拍板的额外评审"
         "（pre_round_review=satisfied_by_prior_evidence：r14 拒绝支第二支机"
         "制证据在案、无需新增视觉评审）——轮前诊断无新增（渲染零变更、零探"
         "针）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=reject 维持不"
         "变（reject=预注册描述性边界下的方向性归因、非统计证明——单轮 n=3 "
         "小样本方向性证据；主通道三分判据（0/0/0、≤10/11、≤run-r14 同口径 "
         "18/24 描述性边界）与 APR-0011 门分开表述、互不凌驾：门联合评价（代"
         "表配置）=not_met 如实分列）；不得回溯改判既往轮次（r8–r14 字母裁决"
         "维持不变）。"),
        ("度量教训在案（供 R16 预注册参考、本轮不追溯适用）：关系式跨轮守门"
         "判据 (iii) 对跨轮实例群漂移敏感（r10 教训在新轴复现）——top 0.75→"
         "0.862 无法区分「§5A 全局弃权致敏」与「实例群噪声」，须同指引重复轮"
         "消解（见 next_iteration_targets[0]）；计数型判据 (i) 对「通道转移」"
         "（courtyard→placement/other）不敏感，须配机制观察补足。"),
    ]

    next_iteration_targets = [
        ("R16 第一候选=同指引重复轮（指引侧零变更、渲染零变更，仅换 12 派次"
         "实例群；r10 零变更重复轮先例）：检验三分判据 (iii) top 回退是否=跨"
         "轮实例群漂移——r15 指引零变更（observation-guidance-r15.md "
         "d5babc93 零字节复用）、渲染零变更（renders-r14b 四图字节复用）、GT/"
         "阈值零变更；若 top 全旗聚合弃权率回落至 ≤0.75 水平（run-r14 双侧复"
         "算基线 18/24）则 r15 (iii) 违约=实例噪声、图例的 bottom 效应（混淆"
         "回落 11/13≤10/11+绿区语义化收敛）得以确认保留；若 top 持续 ≥0.862"
         "（25/29）则「§5A 全局弃权致敏」假设升级，须指引侧再处置（预注册后"
         "执行；不得回溯改判既往轮次）。"),
        ("绿区语义化收敛维持观察（R16 零变更轮顺带覆盖，零期望）：r15 bottom "
         "三实例 notes 收敛为「空隙/翼瓣几何」读法（r14 三实例三种图元化误读"
         "未再现；2/3 实例显式援引 §5A）——若再现 courtyard 矩形类图元化误读"
         "=图例效果不稳，如实记录；继续被动追踪绿/翼瓣/空隙 substring 计数"
         "（无期望、不构成判据输入）。"),
        ("top 弃权构成细分候选（若 R16 同指引重复轮 top 仍高：接触性（r15 5/"
         "6）/丝印叠压（silk 15 旗 13 弃权 2 非弃权）/存在性出口（1）分层记"
         "账后再定处置轴；渲染侧候选=底/顶层归属可辨+图例，属渲染侧变更、须"
         "预注册+声明零仪器变更纪律例外）。"),
        ("黑点类一致弃权延续观察（零变更零期望）：r14 黑点类 14 旗全弃权→r15 "
         "7 旗全弃权+3 派次判正常（prep1-top-i1/applied-top-i3/prep1-bottom-"
         "i1 判基准点/定位类正常未报告）=同现象跨实例处置分化；继续被动追踪"
         "（GT/阈值零改动；若走向变化如实记录）。"),
        ("留出集运行时机=开发线收敛判断（须用户拍板）：r15 字母=reject→收敛"
         "未宣告，连续达标轮次维持 0（正式采纳门槛=连续 2 轮达标+人工批准未"
         "达成，不得写成已达成）；in_calibrated_range 恒 False 直到正式采纳"
         "（须人工批准）；达标证据仍须留出集（out/v3-tl2/holdout/"
         "HOLDOUT-PLAN.md a4b80193… 与 datasets/holdout-candidates-r1 在"
         "案）。"),
        ("GT 侧维持全关闭声明延续：r8 轮同日只读审计 gt-audit-r1（1f20554a…）"
         "三候选全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、L1NB "
         "框径=合理维持现框），r9–r15 延续零改动——GT 侧已全部关闭；r15 "
         "matches=0（union/agreement 0/13）与 bottom GT 无源结构相容（GT 13 "
         "条全部 side=top），后续迭代回归指引侧/渲染侧/协议侧；bottom 零匹配"
         "的结构性原因在案。"),
    ]

    return {
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r14": directional_observation_vs_r14,
        "domain_basis_quote": (
            "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每"
            "轮盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开"
            "始后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级"
            "为 development 证据，不得冒充未见留出。本轮为同域第 15 轮迭代"
            "（development 域指引侧单变量变更轮（§5A 仪器注记配套）：迭代轮"
            "不得冒充留出证据）。"),
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev14["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r15 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r15 全旗标合计 36/42=0.857143 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R14 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 与 abstain_rate 0.785714>0.5 "
                         "三项未达暂行线；gt_count 13≥12 单分项入线）——GT 条"
                         "目层 union 口径 0/13=0.0 亦未达 0.75（双口径与门分"
                         "列如实）"),
            },
        },
        "kind": KIND,
        "next_iteration_targets": next_iteration_targets,
        "notes": notes,
        "preregistration_chain": chain,
        "preregistration_chain_note": (
            "预注册链（含哈希）：round14-dev-record.json（e6354d5c…，"
            "next_iteration_targets[0] 指引侧颜色-图层映射配套候选原文被 "
            "r15-prep-record 逐字摘录预注册+用户 2026-09-08「请继续」批准执"
            "行，user_directive_note 在案）→r15-prep-record.json（4c6cd919…，"
            "本轮预注册件，measurement_design 五条聚合口径与 hypothesis_test."
            "adjudication 三分判据先于盲读冻结；instrument_change.changed="
            "false）→observation-guidance-r15.md（d5babc93…）由 r13 指引"
            "（c28806e1…）机械变换生成落盘冻结（本轮唯一判读依据；§2–§7 判据"
            "文本零变更=分段+substring 双重断言复核；§5A=仪器事实注记、非判"
            "据）→渲染零变更（renders-r14b 四图字节复用=四 PNG sha 与 "
            "render-witness-r14b.json b63771f9 登记值逐一相等，即 r14 轮盲读"
            "所用同一批文件）→12 次盲读→run-r15（0c37c1cb…，本链执行落盘）；"
            "GT 重投影沿用 derivation-log-r5.json（62343380…）零新派生（top "
            "渲染零变更=重投影输入未变；bottom 渲染字节复用不触及）；GT 冻结"
            "纪律：轮后未增删改；gt-audit-r1（1f20554a…）结论维持 GT 零改动"
            "（三候选关闭，gt_audit_reference 在案）"),
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域单变量指引侧变更轮（指引侧颜色-图层映射配套轮，第"
            "十五轮）：判读指引增补 §5A 渲染配色仪器注记节（颜色→来源映射显"
            "式化：橙 (255,165,0)=白墨图元重着色（162 fill+4 stroke，"
            "B.Cu∪B.Mask 双族共享绘制）、绿 (0,128,0)=板内空隙白重着色（墨缺"
            "失处基材露白，非图元：非丝印、非阻焊开窗图形、非 courtyard 图"
            "形）；数值事实自 render-framing-r14b.json/render-witness-r14b."
            "json 结构探测转录；§5A=仪器事实注记、非判据——不降低任何责任门"
            "槛）+渲染零变更（renders-r14b 四图字节复用=r14 轮盲读所用同一批"
            "文件，四 PNG sha 与 witness 登记值逐一相等）+指引 observation-"
            "guidance-r15.md（d5babc93）由 r13 指引（c28806e1）机械变换生成"
            "落盘冻结（§2–§7 判据文本零变更；示例旗 ID 前缀 R13T-/R13B-→"
            "R15T-/R15B- 随指引落盘固化）；GT 集/协议阈值与度量版本/比较器常"
            "量零改动（GT 重投影沿用 derivation-log-r5——top 渲染未变=零新派"
            "生；gt-audit-r1 三候选关闭结论延续）；协议 v1.1+v1.2 维持无新增"
            "版本；instrument_change.changed=false 已预注册；检验 "
            "round14-dev-record next_iteration_targets[0] 候选假设 "
            "r14-dev-record-candidate-0-guidance-color-legend（判据="
            "r15-prep-record.json hypothesis_test.adjudication 三分判据，轮后"
            "如实执行：字母裁决唯一正式+机制观察/度量教训单列）；主通道三分判"
            "据与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独"
            "立计算、互不凌驾、分开表述；measurement_design 五条聚合口径先于"
            "盲读冻结；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R15, "sha256": run15_sha},
        "schema_version": SCHEMA_VERSION,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s56-cal-r15-devrecord] round15-dev-record: {status}")
    print(f"[s56-cal-r15-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"reject_branch={dev['hypothesis_test_i']['measurement'][
              'reject_branch']}")
    print(f"[s56-cal-r15-devrecord] 三分判据: (i) 0/0/0 满足（零旗标路径）；"
          f"(ii) 11/13=0.846154≤10/11 满足；(iii) 25/29=0.862069>18/24=0.75 "
          f"违约 ⇒ reject")
    print(f"[s56-cal-r15-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s56-cal-r15-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0")
    print(f"[s56-cal-r15-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s56-cal-r15-devrecord] R15 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=reject 唯一正式；机制观察/度量教训单列不凌驾；"
          "in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
