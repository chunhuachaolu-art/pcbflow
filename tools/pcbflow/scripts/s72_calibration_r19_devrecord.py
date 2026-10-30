#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s72_calibration_r19_devrecord.py — R19 CLOSE 包 B：
round19-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律；
底稿=s69_calibration_r18_devrecord.py 同构重建）。

R19=轴3 判据侧单变量轮（§4(iii-a) 可操作分辨条款增补，axis-experiment-
plan-r17-r20 stage1 R19=A3_criterion_contact_clarification；用户
2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的继续」指令操作
化冻结件在案）：渲染零变更=renders-r14b 四图字节复用（与 r14/r15/r16/
r17/r18 盲读同一批文件）；判读指引=observation-guidance-r19.md
（8633bda5，r15 基座 d5babc93 机械变换派生+§4 增补 (iii-a) bullet=判据
节首次变更先例：增补式+反放宽条款逐字保留+锚断言[content_sha256=
97bb4c0f…、anchor/expected_hits 机械插入断言]；§2–§7 其余逐字承 r15、
§5A 原文逐字保留、无 §5B）；GT/阈值/协议零变更（13 条冻结、v1.1+v1.2
维持）；instrument_change.changed=false。预注册假设（axis-plan-r19-
criterion-operational）三分判据轮后裁决=marginal（唯一正式裁决）：
- (s) 支 contact ≤5（实测 4 ✓）且 M1=18/39=0.461538≤0.85 ✓ 且 G1/G2
  维持 ✓，唯 M4=top 逐实例弃权率极差 0.211111>0.20 未过⇒supported 未
  成立；(r) 支 contact ≥8 且 M4 >0.26=False；(m) 支未达 supported 且
  （contact ≤7 或 M4 ≤0.26）且 G1/G2 维持——两途径均满足（contact
  4≤7、M4 0.211111≤0.26）⇒字母=marginal——记录为部分收益（轴3 不判
  定为胜出）；描述性结论、非因果证明。
机制观察/度量教训单列不凌驾字母裁决：(iii-a) 逐旗落支分布（旗级 14 旗
=textual 证据可归支者：残余弃权支 8[全弃权旗]+侵入支 6[全非弃权报告
旗]+间隙支旗级 0——间隙支全部在 notes 级判正常路径消化（4 派次自述
「可辨认间隙带→视觉贴近→继续判定→判正常不报告」））；援引计数（旗级
location_evidence 含「(iii-a)」=6 旗[全弃权旗]、含「分支(」=2 旗[全非
弃权黑点-焊盘接触报告旗]、notes 级含「(iii-a)」=10/12 派次、未援引 2
派次=applied-bottom-i1/applied-top-i3 如实分列）；黑点族（rubric 口径
existence_blackdot）=4 vs r18=13 显著回落+黑点转非弃权旗 6 条+黑点判
正常派次 3；存在性其他=14 vs r18=12（+2 如实记录、未显著上升=弃权转
移对照口径）；top 弃权构成分型=接触性 5+存在性 13+层归属其他 0（r18
对照 8/12/0、r16 对照 11/15/1）。实验对照账（axis-plan benefit_metrics
口径）：(M1,M2,M3,M4)=(0.461538, 0.571429, 4, 0.211111)（M3 槽位=冻
结件黑点族口径；contact=4 另列不占槽）——四轮并列（r16 基线 0.771429/
0.857143/12/0.261904、r17 轴1 0.88/0.75/8/0.333333、r18 轴2 0.645161/
0.684211/13/0.277778、r19 轴3 0.461538/0.571429/4/0.211111）；按冻结
comparison_rule=(M1 升序, M2 升序, M3 升序, M4 升序) 字典序：r19 轴3
第一、r18 轴2 第二、r16 基线参照行第三、r17 轴1 末位（M1=0.88 劣于基
线=负向，不进组合；非守门出局——r17 G1/G2 满足）；显著收益定义命中
（M1 绝对降幅 0.309891≥0.10）；按冻结 combination_decision_rule.
i_stage2_combo_pair：下一候选=R20=轴3+轴2 组合轮（guidance=§5B+§4
(iii-a) 合成、renders-r14b 零仪器变更、12 派次；须各自 prep-record 预
注册后执行、不预写结果）；R21 全组合触发条件核对=否（三轴皆正不成立：
轴1 M1=0.88 负向）+early_stop strong_single_axis_shortcut 实测命中
（最优单轴 M1=0.461538≤0.60→阶段2 仅一个组合轮、R21 不做）。GT 双口
径 union 1/13（唯一命中=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT
[other_advisory、containment 1.0、(iii-a) 侵入支产物旗]、r16 的 1/13
后 r17/r18 连续零命中、r19 再现=单实例命中不稳定如实）、agreement
0/13（≥2/3 规则）；类别门 2 条近失如实（R19T-004×GT-REVC-AP-6-R2LED2
[silk×courtyard]、R19T-009×GT-REVC-P1-L1NB[other_advisory×courtyard]
近邻交叠类别不符出局）；代表配置（top-i1+bottom-i2 双唯一）joint
not_met、连续=0；零旗标派次=2（bottom-i3 两板，item 5 None 口径）。
派发事故记录（如实、单列）：wave-3 重派时主审误派重复智能体（2×top-i3
+2×bottom-i3 并发同实例 ID）；后完成者在未读取旧文件内容前提下删除重
写；盘上最终=一套完整自洽 i3 输出（top 跨板连续 R19T-001..010；bottom
0 旗标），4 个 i3 文件哈希已钉死（7941cb00/5591ce98/f4069303/
fcc69fb5）；先完成者的重复输出废弃；教训=重派前必须核对目标实例唯一
性。

生成器纪律（s69/s71 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-09"；
- 防覆写护栏：round19-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round19-dev-record.json 一件（s71 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s72_calibration_r19_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-09-r19"
ROUND_LABEL = "r19"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round19_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_PREP_R19 = "out/v3-tl2/calibration/r19-prep-record.json"
REL_DEV_R18 = "out/v3-tl2/calibration/round18-dev-record.json"
REL_GUIDANCE_R19 = "out/v3-tl2/calibration/observation-guidance-r19.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_OUT = "out/v3-tl2/calibration/round19-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 派发事故后盘态钉死（与 s71 I3_PINNED_PREFIXES 同锚；live 实测复核）。
REL_RAW_I3 = {
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r19-applied-top-i3.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r19-applied-bottom-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r19-prep1-top-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r19-prep1-bottom-i3.txt",
}
I3_PINNED_PREFIXES = {
    "applied-top-i3": "7941cb00",
    "applied-bottom-i3": "5591ce98",
    "prep1-top-i3": "f4069303",
    "prep1-bottom-i3": "fcc69fb5",
}

# 引用件哈希清单（简报在案锚；逐件 live 实测比对，fail-closed）
REFERENCE_HASH_EXPECTED = {
    "run_r19": (REL_RUN_R19, "e5755a11"),
    "guidance_r19": (REL_GUIDANCE_R19, "8633bda5"),
    "prep_r19": (REL_PREP_R19, "e4cf2d3c"),
    "axis_experiment_plan": (REL_AXIS_PLAN, "b6ec6467"),
    "abstain_typology_r13_r16": (REL_TYPOLOGY, "6dadac8d"),
}

# 主通道三分判据实测锚（写盘前 fail-closed 与 run-r19 盘上值逐一核对）
EXPECT_TOP_ABSTAIN_R19 = 18
EXPECT_TOP_FLAGS_R19 = 39
EXPECT_TOP_RATE_R19 = 0.461538
EXPECT_BOTTOM_ABSTAIN_R19 = 4
EXPECT_BOTTOM_FLAGS_R19 = 7
EXPECT_BOTTOM_RATE_R19 = 0.571429
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_CONTACT_R19 = 4
EXPECT_CONTACT_R16_BASELINE = 10
EXPECT_CONTACT_CHAIN_R13_R16 = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
EXPECT_M4_R19 = 0.211111
# 实验对照账（axis-experiment-plan benefit_metrics 口径；M3 槽位=冻结件
# 黑点族 rubric 口径、本轮实测 4；contact=4 另列不占 M3 槽位）
EXPECT_M1 = 0.461538
EXPECT_M2 = 0.571429
EXPECT_M3 = 4
EXPECT_M4 = 0.211111
# axis-plan 在案 r16 基线四键（baselines_registered/benefit_metrics 口径）
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17/r18 已测行（dev-r18 在案行装载；排序现状对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
EXPECT_R18_MEASURED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                       "M4": 0.277778}
EXPECT_M1_ABSOLUTE_DROP = 0.309891
EXPECT_R18_DROP_REFERENCE = 0.126268
# early_stop.strong_single_axis_shortcut 阈值（冻结件原文 0.60；6 位定点）
STRONG_SHORTCUT_M1_MAX_6DP = 600_000
EXPECT_COUNTS = {"top-i1": 11, "top-i2": 18, "top-i3": 10,
                 "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 0}
EXPECT_ABSTAIN = {"top-i1": 5, "top-i2": 7, "top-i3": 6,
                  "bottom-i1": 3, "bottom-i2": 1, "bottom-i3": 0}
EXPECT_RATES = {"top-i1": 0.454545, "top-i2": 0.388889, "top-i3": 0.6,
                "bottom-i1": 0.75, "bottom-i2": 0.333333,
                "bottom-i3": None}
EXPECT_R16_RATES = {"top-i1": 0.666667, "top-i2": 0.928571,
                    "top-i3": 0.666667, "bottom-i1": 1.0,
                    "bottom-i2": 0.8, "bottom-i3": 0.75}
EXPECT_TYPE_COUNTS = {"contact": 5, "existence": 13, "other_layer": 0}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 3, "bottom-i2": 1,
                                "bottom-i3": 0, "top-i1": 0,
                                "top-i2": 0, "top-i3": 0}
EXPECT_RUBRIC_COUNTS = {"contact": 4, "existence_blackdot": 4,
                        "existence_other": 14, "other": 0,
                        "semantic_confusion": 0}
EXPECT_BRANCH_COUNTS = {"branch1_gap_report": 0,
                        "branch2_intrusion_report": 6,
                        "branch3_residual_abstain": 8}
EXPECT_ZERO_FLAG_PARTS = [{"flag_count": 0, "instance": "bottom-i3",
                           "state": "applied"},
                          {"flag_count": 0, "instance": "bottom-i3",
                           "state": "prep1"}]
EXPECT_GUIDANCE_BYTE_SIZE = {"base": 19878, "delta": 1557, "derived": 21435}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s72-cal-r19-devrecord] FAIL: {msg}")


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
# 冻结组合决策规则操作化（纯函数；构造可测，轴序变更时建议跟随变化）
# ---------------------------------------------------------------------------

def _row4(row) -> dict:
    """行归一：dict{M1..M4} 或四元组 → dict。"""
    if isinstance(row, dict):
        return {"M1": row["M1"], "M2": row["M2"],
                "M3": row["M3"], "M4": row["M4"]}
    return {"M1": row[0], "M2": row[1], "M3": row[2], "M4": row[3]}


def comparison_sort_key(row) -> tuple:
    """冻结 comparison_rule 排序键：(M1 升序, M2 升序, M3 升序,
    M4 升序) 字典序（M1 最小者最优；同值依次比较 M2→M3→M4）。"""
    m = _row4(row)
    return (m["M1"], m["M2"], m["M3"], m["M4"])


def next_stage2_candidate(axis_rows: dict, guards: dict) -> dict:
    """阶段2 组合轮候选（纯函数；冻结 combination_decision_rule.
    i_stage2_combo_pair 原文操作化）：仅 G1/G2 均满足的轴进入排序，
    按 comparison_rule 字典序取最优两轴=R20。

    axis_rows={axis_key: {M1,M2,M3,M4} 或四元组}；guards={axis_key:
    bool}。过守门轴不足两轴→ValueError（组合轮前提不成立，调用方
    fail-closed）。返回 {"eligible_sorted": [...], "r20_axes": [...]}
    （best-first）。"""
    eligible = sorted((k for k in axis_rows if guards.get(k) is True),
                      key=lambda k: comparison_sort_key(axis_rows[k]))
    if len(eligible) < 2:
        raise ValueError("过守门（G1/G2 均满足）轴不足两轴——组合轮前提"
                         "不成立（fail-closed）")
    return {"eligible_sorted": eligible, "r20_axes": eligible[:2]}


def full_combination_trigger(axis_rows: dict, baseline_m1: float) -> bool:
    """轴2 ii_full_combination 触发条件核对（纯函数）：三轴均各自正
    收益（升序口径：各自 M1 不劣于 r16 基线 ⇔ M1×10^6 ≤ 基线×10^6，
    避免浮点）。"""
    return all(_row4(row)["M1"] * 1_000_000 <= baseline_m1 * 1_000_000
               for row in axis_rows.values())


def strong_single_axis_shortcut(best_single_axis_m1: float) -> bool:
    """early_stop_rule.strong_single_axis_shortcut 触发核对（纯函数）：
    最优单轴 M1 ≤0.60（M1×10^6 ≤ 600000，避免浮点）→阶段2 仅做最优
    单轴+次优单轴一个组合轮（R21 不做）。"""
    return best_single_axis_m1 * 1_000_000 <= STRONG_SHORTCUT_M1_MAX_6DP


# ---------------------------------------------------------------------------
# fail-closed 事实核对（所有入文数字先与盘上值对账）
# ---------------------------------------------------------------------------

def _view_abstain_aggregate(run: dict, view: str):
    names = [n for n in INSTANCE_ORDER if n.startswith(view)]
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run16: dict, prep: dict, dev18: dict,
                  typology: dict, guidance_sha: str, axis_sha: str,
                  typology_sha: str) -> None:
    # ---- run-r19 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r19":
        _fail("run kind 不符")
    if (run["round_id"], run["round_label"], run["declared_date"],
            run["evaluation_domain"]) != (ROUND_ID, ROUND_LABEL,
                                          DECLARED_DATE, "development"):
        _fail("run 声明常量不符")
    if run["evaluation_domain_note"]["in_calibrated_range"] is not False:
        _fail("in_calibrated_range 应恒 False")
    if run["parse_rejections"] != []:
        _fail("拒收清单应为空")
    ht = run["hypothesis_test"]
    if ht["hypothesis_id"] != "axis-plan-r19-criterion-operational":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "marginal":
        _fail("verdict != marginal")
    if "记录为部分收益" not in ht["verdict_text"] or \
            "不判定为胜出" not in ht["verdict_text"]:
        _fail("verdict_text 应含「记录为部分收益/不判定为胜出」")
    m = ht["measurement"]
    if (m["crit_supported_contact_le_5"] is not True
            or m["crit_supported_m1_le_0_85"] is not True
            or m["crit_supported_m4_le_0_20"] is not False
            or m["crit_reject_contact_ge_8_and_m4_above_0_26"] is not False
            or m["crit_marginal_contact_le_7"] is not True
            or m["crit_marginal_m4_le_0_26"] is not True):
        _fail("三分判据布尔不符（(s) contact/M1 真而 M4 假；(r) 假；"
              "(m) 两途径真）")
    if not m["letter_branch"].startswith("(m)"):
        _fail("落支应为 (m) 支")
    if m["verdict"] != "marginal":
        _fail("measurement.verdict != marginal")
    # 本轮实测（top 18/39、bottom 4/7）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R19, EXPECT_TOP_ABSTAIN_R19):
        _fail("top 聚合不符（18/39）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R19, EXPECT_BOTTOM_ABSTAIN_R19):
        _fail("bottom 聚合不符（4/7）")
    if m["top_abstain_rate_r19"] != EXPECT_TOP_RATE_R19 or \
            m["bottom_side_observation"]["bottom_abstain_rate_r19"] != \
            EXPECT_BOTTOM_RATE_R19:
        _fail("聚合弃权率不符")
    if "18/39" not in m["top_abstain_rate_r19_arithmetic"] or \
            "4/7" not in m["bottom_side_observation"][
                "bottom_abstain_rate_r19_arithmetic"]:
        _fail("聚合算式文本不符")
    if m["bottom_side_observation"]["bottom_rate_direction_vs_r16"] != \
            "improved":
        _fail("bottom 侧观察方向应为 improved")
    # 整数交叉相乘复核（避免浮点）：(s) contact=4≤5 ✓、M1 门 18×10^6≤
    # 850000×39 ✓、M4 门 211111>200000 未过；(r) 需 contact≥8 ✗；(m)
    # contact 4≤7 ✓、211111≤260000 ✓；显著收益 (27/35−18/39)≥0.10 ✓
    if not (EXPECT_CONTACT_R19 <= 5):
        _fail("(s) contact ≤5 复核不符")
    if at * 1_000_000 > 850_000 * ft:
        _fail("M1 ≤0.85 门复核不符（应 18×10^6≤850000×39）")
    if not (211_111 > 200_000):
        _fail("M4 门未过复核不符（0.211111>0.20）")
    if not (EXPECT_CONTACT_R19 <= 7 and 211_111 <= 260_000):
        _fail("(m) 两途径复核不符")
    if (27 * 39 - 18 * 35) * 1_000_000 < 100_000 * 35 * 39:
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
    # contact 族（主度量）：实测 4、基线 10、链重放 8/15/5/10、分视角
    if m["contact_family_abstain_flags_rubric_r19"] != EXPECT_CONTACT_R19 \
            or m["contact_r16_baseline_registered"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            m["contact_r16_baseline_live_replay"] != \
            EXPECT_CONTACT_CHAIN_R13_R16:
        _fail("contact 实测/基线/链重放不符（4、10、8/15/5/10）")
    if "top 4+bottom 0" not in m["contact_arithmetic_note"]:
        _fail("contact 分视角算式不符（top 4+bottom 0）")
    # M4 与 axis-plan 登记基线四键交叉核对
    if m["m4_top_rate_range_r19"] != EXPECT_M4_R19 or \
            run["view_layer"]["top"]["abstain_rate_range"] != EXPECT_M4:
        _fail("M4=top 极差不符（0.211111）")
    if m["baseline_cross_check"]["axis_plan_r16_baseline_M1_M2_M3_M4"] != \
            EXPECT_R16_BASELINE_M1_M2_M3_M4:
        _fail("axis-plan r16 基线四键不符")
    # 守门通道（G1/G2 均维持；独立单列；early_stop 未触发）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not True:
        _fail("守门 G1/G2 应均维持 True")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["guards_ok"] is not True or \
            g12["axis_early_stop_triggered"] is not False or \
            g12["g2_geometry_gate_r18"] != 0 or \
            g12["g2_geometry_gate_r19"] != 0 or \
            g12["g1_bottom_courtyard_non_abstain_r19"] != \
            {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0} or \
            g12["g1_bottom_courtyard_flags_total_r19"] != 0:
        _fail("守门通道不符（G1 0/0/0、G2 0→0、early_stop 未触发）")
    ca = run["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r19_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_1_geometry_gate"][
                "r18_area_ratio_rejected_entries"]) != 0:
        _fail("几何门 0→0 复核不符")
    c2 = ca["channel_2_category_gate"]
    near = c2["r19_category_mismatch_entries"]
    if len(near) != 2:
        _fail("类别门 r19 应 2 条近失")
    near_keys = {(e["flag_id"], e["instance"], e["state"], e["gt_id"])
                 for e in near}
    if near_keys != {("R19T-004", "top-i2", "applied",
                      "GT-REVC-AP-6-R2LED2"),
                     ("R19T-009", "top-i3", "prep1",
                      "GT-REVC-P1-L1NB")}:
        _fail("类别门近失条目不符（R19T-004×AP-6、R19T-009×P1-L1NB）")
    if len(ca["view_gate_observations"]["r19_entries"]) != 0:
        _fail("视角门 r19=0 复核不符")
    # GT 双口径：union 1/13（唯一命中）、agreement 0/13、分母 13
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (1, 0, 13):
        _fail("双口径不符（union 1/13、agreement 0/13）")
    if dual["union"]["gt_ids"] != ["GT-REVC-P1-L1SHORT"] or \
            dual["union"]["gt_recall_union"] != 0.076923:
        _fail("union 唯一命中不符（GT-REVC-P1-L1SHORT）")
    hit_gt = [p for p in dual["per_gt"]
              if p["gt_id"] == "GT-REVC-P1-L1SHORT"][0]
    hit = hit_gt["hits"][0]
    if (hit["flag_id"], hit["instance"], hit["state"],
            hit["containment"]) != ("R19T-009", "top-i3", "prep1", 1.0):
        _fail("唯一命中明细不符（prep1-top-i3 R19T-009 containment 1.0）")
    if run["courtyard_tracking"]["courtyard_matches_r19"] != 0:
        _fail("courtyard 追踪 r19=0 不符")
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
    # 零旗标派次=2（bottom-i3 两板；top 12 格全部≥1 旗）
    if run["reader"]["zero_flag_parts"]["parts"] != EXPECT_ZERO_FLAG_PARTS:
        _fail("零旗标派次不符（bottom-i3 两板）")
    # 代表配置与门（top-i1+bottom-i2 双唯一）
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (14, 6, 0.428571, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0 or \
            run["compliance_representative"][
                "critic_calibration_in_range"] is not False:
        _fail("联合门/连续计数/in_calibrated_range 不符")
    rep = run["representative_configuration"]["members"]
    if rep != {"top": "top-i1", "bottom": "bottom-i2"}:
        _fail("代表配置成员不符（top-i1+bottom-i2）")
    if run["representative_configuration"]["selection"]["top"][
            "tie"] is not False or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not False:
        _fail("代表配置 tie 记录不符（双唯一）")
    # instrument_change.changed=false（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not False or \
            prep["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 应为 false")
    if prep["no_instrument_change"] is not True:
        _fail("prep no_instrument_change 应为 true")
    if len(run["instrument_change"]["changed_variables_registered"]) != 2 or \
            len(prep["changed_variables"]) != 2:
        _fail("变更变量登记不符（run 2 件、prep 2 件）")
    if run["instrument_change"]["changed_variables_registered"][0][
            "id"] != "guidance-s4-iii-a-contact-operational-clause" or \
            run["instrument_change"]["changed_variables_registered"][1][
                "id"] != "round-identity-sync":
        _fail("变更变量 id 不符（§4(iii-a) 条款+轮次标识机械同步）")
    if run["instrument_change"]["axis_id"] != \
            "A3_criterion_contact_clarification":
        _fail("轴3 声明不符")
    # 机制观察：(iii-a) 落支/援引、黑点族、top 分型、rubric 族
    mo = ht["mechanism_observation"]
    iiia = mo["iiia_branch_observation"]
    if iiia["branch_counts_flag_level"] != EXPECT_BRANCH_COUNTS or \
            iiia["branch1_notes_level_dispatches"] != 4:
        _fail("(iii-a) 落支不符（残余 8+侵入 6+间隙 0；notes 级判正常 "
              "4 派次）")
    cc = iiia["citation_counts"]
    if cc["flag_level_iiia_literal"] != 6 or \
            cc["flag_level_branch_literal"] != 2 or \
            cc["notes_level_iiia"] != 10 or \
            len(cc["notes_level_iiia_sources"]) != 10 or \
            cc["notes_level_non_citing"] != ["applied-bottom-i1",
                                             "applied-top-i3"]:
        _fail("援引计数不符（旗级 (iii-a) 6、分支( 2、notes 级 10/12）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 4:
        _fail("黑点族 4 旗全弃权不符")
    if bdt["blackdot_to_non_abstain_count"] != 6 or \
            len(bdt["black_dot_non_abstain_flags"]) != 6:
        _fail("黑点转非弃权旗 6 条不符")
    if bdt["judged_normal_dispatches"]["count"] != 3:
        _fail("黑点判正常派次 3 不符")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS:
        _fail("rubric 族计数不符（4/4/14/0/0）")
    ty = mo["top_abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            ty["top_abstain_flags_total"] != 18 or len(ty["rows"]) != 18 or \
            ty["top_abstain_rate_range"] != EXPECT_M4:
        _fail("top 弃权构成分型不符（5/13/0、18 旗、极差 0.211111）")
    if ty["r16_reference_counts"] != {"contact": 11, "existence": 15,
                                      "other_layer": 1} or \
            ty["r17_reference_counts"] != {"contact": 8, "existence": 14,
                                           "other_layer": 0} or \
            ty["r18_reference_counts_live"] != {"contact": 8,
                                                "existence": 12,
                                                "other_layer": 0}:
        _fail("r16/r17/r18 分型参照不符")
    # 实验对照账：四元组/四轮并列/排序/显著收益/快捷通道观察
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r19_measured"]["M1"] != EXPECT_M1 or \
            ecl["r19_measured"]["M2"] != EXPECT_M2 or \
            ecl["r19_measured"]["M3"] != EXPECT_M3 or \
            ecl["r19_measured"]["M4"] != EXPECT_M4 or \
            ecl["r19_measured"]["M1_arithmetic"] != "18/39" or \
            ecl["r19_measured"]["M2_arithmetic"] != "4/7" or \
            ecl["r19_measured"]["contact_family_abstain_flags_rubric"] != 4 \
            or ecl["r19_measured"]["contact_family_by_view"] != \
            {"bottom": 0, "top": 4} or \
            ecl["r19_measured"]["existence_other_family"] != 14:
        _fail("实验对照账四元组/另列键不符")
    if ecl["r17_axis1_row"] != EXPECT_R17_MEASURED or \
            ecl["r18_axis2_row"] != EXPECT_R18_MEASURED:
        _fail("r17/r18 对照行不符")
    if ecl["r16_baseline_registered"]["M1"] != 0.771429 or \
            ecl["r16_baseline_registered"]["M4"] != 0.261904 or \
            ecl["r16_baseline_registered"]["live_replay_cross_check"][
                "M1"] != "27/35":
        _fail("r16 基线行/复算交叉核对不符")
    rk = ecl["ranking_by_comparison_rule"]
    if rk["ranking_order_best_first"] != ["r19_axis3", "r18_axis2",
                                          "r16_baseline", "r17_axis1"] or \
            rk["r19_rank"] != 1 or rk["rows_registered"]["r19_axis3"] != \
            {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}:
        _fail("comparison_rule 排序不符（r19 第一、r18 第二、r17 末位）")
    sb = ecl["significant_benefit_vs_r16"]
    if sb["met"] is not True or \
            sb["r19_m1_absolute_drop"] != EXPECT_M1_ABSOLUTE_DROP or \
            sb["r18_drop_reference"] != EXPECT_R18_DROP_REFERENCE:
        _fail("显著收益不符（0.309891≥0.10；r18 参照 0.126268）")
    if "0.60" not in ecl["strong_single_axis_shortcut_observation"]:
        _fail("strong_single_axis_shortcut 观察锚不符")
    # 判据引用=prep-record 原文（逐字一致，共键比对；adjudication 6 键）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "marginal",
              "mechanism_observation_separate", "metric_lesson_separate",
              "reject", "supported"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引机械变换派生锚（8633bda5 实测=r15 基座 d5babc93 派生+(iii-a) 增补）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "mechanical_transform_derive" or \
            gr["derived"] != "observation-guidance-r19.md":
        _fail("guidance_reuse 机械变换派生声明不符")
    if gr["base_sha256"][:8] != "d5babc93":
        _fail("r15 基座锚不符")
    if gr["derived_sha256"] != guidance_sha or \
            guidance_sha != _sha(REL_GUIDANCE_R19):
        _fail("r19 指引实测 sha 与 8633bda5 锚不符")
    if gr["byte_size"] != EXPECT_GUIDANCE_BYTE_SIZE:
        _fail(f"指引 byte_size 不符（{EXPECT_GUIDANCE_BYTE_SIZE}）")
    iii_a = [e for e in gr["edit_list"]
             if e.get("kind", "").startswith("§4 增补 (iii-a)")]
    if len(iii_a) != 1 or iii_a[0]["content_sha256"][:8] != "97bb4c0f":
        _fail("(iii-a) 增补 bullet 锚断言不符（content_sha256 97bb4c0f）")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R19):
        _fail("prep-record sha 实测与登记不符")
    anchors = gr["chain_anchors"]
    if anchors["axis_experiment_plan_frozen"]["sha256"] != \
            axis_sha or axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    # 轴计划比较/组合/early_stop 规则（冻结）与 typology 基线锚
    plan = _json_load(REL_AXIS_PLAN)
    if "M1 升序" not in plan["comparison_rule"]["ordering"]:
        _fail("axis-plan 排序规则不符（M1 升序字典序）")
    if "G1/G2" not in plan["comparison_rule"]["eligibility_gate"]:
        _fail("axis-plan 资格门不符（G1/G2）")
    if "0.10" not in plan["comparison_rule"]["significant_benefit_definition"]:
        _fail("axis-plan 显著收益定义不符（绝对降幅 ≥0.10）")
    cdr = plan["combination_decision_rule"]
    if "最优的两轴做组合轮 R20" not in cdr["i_stage2_combo_pair"] or \
            "三轴均各自正收益" not in cdr["ii_full_combination"] or \
            "不预写结果" not in cdr["preregistration_note"]:
        _fail("combination_decision_rule 冻结原文锚不符")
    if "0.60" not in plan["early_stop_rule"]["strong_single_axis_shortcut"]:
        _fail("early_stop strong_single_axis_shortcut 锚不符")
    if typology["matrix"]["round_totals"]["r16"]["families"]["contact"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            typology_sha != _sha(REL_TYPOLOGY):
        _fail("typology contact 基线/实测 sha 不符（r16=10）")
    # i3 件盘态钉死（派发事故后终态；与 s71 同锚 live 复核）
    for key, prefix in I3_PINNED_PREFIXES.items():
        got = _sha(REL_RAW_I3[key])
        if not got.startswith(prefix):
            _fail(f"i3 件盘态前缀不符: {key}（{got[:8]} ≠ {prefix}）")
        if not run["reader"]["raw_files"][key]["sha256"].startswith(prefix):
            _fail(f"run raw_files 登记前缀不符: {key}")
    cont = run["reader"]["dispatch_mode"]["flag_id_continuity"]
    if "R19T-001..004" not in cont["top-i3"] or \
            "R19T-005..010" not in cont["top-i3"] or \
            "跨板连续" not in cont["top-i3"]:
        _fail("top-i3 跨板连续编号锚不符（R19T-001..010）")
    # r18 dev-record 先验链锚（实测）与 r17/r18 已测行
    prior = [a for a in run["preregistration"]["frozen_artifacts"]
             if a["role"] == "r18_dev_record_prior_chain_and_axis_ledger"]
    if len(prior) != 1 or prior[0]["sha256"] != _sha(REL_DEV_R18):
        _fail("round18-dev-record 先验链锚不符")
    if dev18["round_id"] != "2026-09-09-r18" or \
            dev18["hypothesis_test_i"]["verdict"] != "reject":
        _fail("r18 dev-record 先验件常量不符")
    if dev18["axis_experiment_ledger"]["this_round_measured"] != \
            EXPECT_R18_MEASURED:
        _fail("r18 dev-record 已测行四元组不符")
    if dev18["axis_experiment_ledger"]["cross_round_status"][
            "measured_rows"]["r17_axis1"] != EXPECT_R17_MEASURED:
        _fail("r17 已测行（dev-r18 装载）不符")
    trend_rows_prior = dev18["joint_evaluation_trend"]["by_round"]
    if [r["round"] for r in trend_rows_prior] != [
            "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "r16", "r17", "r18"]:
        _fail("趋势历史行（dev-r18）不符")


def build_dev_record() -> dict:
    """构建 round19-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R19)
    run16 = _json_load(REL_RUN_R16)
    prep = _json_load(REL_PREP_R19)
    dev18 = _json_load(REL_DEV_R18)
    typology = _json_load(REL_TYPOLOGY)
    guidance_sha = _sha(REL_GUIDANCE_R19)
    axis_sha = _sha(REL_AXIS_PLAN)
    typology_sha = _sha(REL_TYPOLOGY)
    _verify_facts(run, run16, prep, dev18, typology, guidance_sha,
                  axis_sha, typology_sha)

    ht = run["hypothesis_test"]
    m = ht["measurement"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    plan = _json_load(REL_AXIS_PLAN)

    # 预注册链（逐件实测 sha，fail-closed 与 run 登记值交叉核对）
    chain = {}
    for item in run["preregistration"]["frozen_artifacts"]:
        got = _sha(item["path_rel"])
        if got != item["sha256"]:
            _fail(f"冻结工件实测 sha 与登记不符: {item['role']}")
        chain[item["role"]] = {"path_rel": item["path_rel"],
                               "sha256": got}

    run19_sha = _sha(REL_RUN_R19)

    # 引用件哈希清单（简报在案锚逐一 live 实测）
    reference_hash_manifest = {
        "entries": {},
        "role": ("引用件哈希清单（全部 live sha256_file 实测、与在案前缀"
                 "逐一比对；fail-closed）"),
    }
    for name, (rel, prefix) in REFERENCE_HASH_EXPECTED.items():
        got = _sha(rel)
        if not got.startswith(prefix):
            _fail(f"引用件实测 sha 前缀不符: {name}（{got[:8]} ≠ {prefix}）")
        reference_hash_manifest["entries"][name] = {
            "path_rel": rel,
            "sha256": got,
            "sha256_prefix_expected": prefix,
        }

    # 联合评价趋势：r5–r18 行=round18-dev-record 在案行（冻结转录）；
    # r19 行=本轮 run 实测
    trend_rows = list(dev18["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17",
                                            "r18"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r19",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R19, "sha256": run19_sha},
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
            "全旗标合计口径仅作附记（22/46=0.478261，非弃权 24+弃权 22）；"
            "本轮预注册主通道=三分判据（(m) 未达 supported 且（contact ≤7 "
            "或 M4 ≤0.26）且 G1/G2 维持⇒marginal——(s) contact=4≤5 与 "
            "M1=18/39=0.461538≤0.85 成立、唯 M4=0.211111>0.20 未过；"
            "bottom 全旗聚合弃权率 4/7=0.571429 为侧观察度量[M2，improved "
            "方向]）；实例层/视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 0.416667=0.75−0.333333（bottom-i1/i2/i3 "
                     "= 0.75/0.333333/None，按可计算实例；bottom-i3 两板"
                     "零旗标分母→None、measurement_design item 5 口径不编"
                     "造数值）；top 极差 0.211111=0.6−0.388889（top-i1/i2"
                     "/i3=0.454545/0.388889/0.6）；本轮零旗标派次=2"
                     "（bottom-i3 两板，对照 r18 的 12 格全部≥1 旗、r17 的 "
                     "2 格）——零旗格 view_check=not_applicable、不进弃权"
                     "率分母（measurement_design item 5 口径在案），top 弃"
                     "权率全部有定义、bottom 中位数含 None"),
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
                 "（4 格×3 实例，两波次串行保序）；R19T/R19B 前缀随 r19 "
                 "指引 §6 落盘固化；flag_id 编号行为混合（top-i3 两板跨板"
                 "连续 R19T-001..010、其余实例两板各自从头编号）=读者实例"
                 "输出行为差异如实登记（编排侧按 (state, flag_id) 限定，"
                 "跨板同号不混淆）；wave-3 派发事故（重派重复智能体）如实"
                 "单列 dispatch_incident_record——盘上终态=一套完整自洽 "
                 "i3 输出、4 件哈希钉死，先完成者重复输出废弃；v1.2 工具"
                 "规约沿用 12/12 派次自述合规与输出格式披露（12 件缩进格"
                 "式冻结原始判读件、零改动直读）如实登记为混杂因素披露，"
                 "不作废"),
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
            "representative_configuration（top-i1+bottom-i2，"
            "measurement_design item 4；top 中位 11 由 top-i1 唯一持有"
            "（11/18/10）无 tie；bottom 中位 3 由 bottom-i2 唯一持有"
            "（4/3/0）无 tie——双唯一、按先序规则本轮未触发）"),
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

    # 组合决策应用（冻结 combination_decision_rule + early_stop_rule
    # 操作化；纯函数可构造复算；不预写结果）
    axis_rows = {
        "r17_axis1": dict(EXPECT_R17_MEASURED),
        "r18_axis2": dict(EXPECT_R18_MEASURED),
        "r19_axis3": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                      "M3": EXPECT_M3, "M4": EXPECT_M4},
    }
    guards = {"r17_axis1": True, "r18_axis2": True, "r19_axis3": True}
    cand = next_stage2_candidate(axis_rows, guards)
    if cand["r20_axes"] != ["r19_axis3", "r18_axis2"]:
        _fail("R20 候选不符（应为轴3+轴2）")
    r21_met = full_combination_trigger(axis_rows, 0.771429)
    if r21_met is not False:
        _fail("R21 全组合触发核对不符（轴1 M1=0.88 负向→不触发）")
    shortcut_met = strong_single_axis_shortcut(EXPECT_M1)
    if shortcut_met is not True:
        _fail("strong_single_axis_shortcut 核对不符（0.461538≤0.60→命中）")
    combination_decision_application = {
        "early_stop_shortcut": {
            "check": ("最优单轴 M1=0.461538 ≤0.60（0.461538×10^6≤"
                      "600000 整数交叉相乘）→阶段2 仅做最优单轴+次优单轴"
                      "一个组合轮（R21 不做）——early_stop_rule."
                      "strong_single_axis_shortcut 冻结原文引用"),
            "best_single_axis_m1": EXPECT_M1,
            "rule_quote": plan["early_stop_rule"][
                "strong_single_axis_shortcut"],
            "triggered": True,
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "inputs": {
            "axis_rows": {k: dict(v) for k, v in axis_rows.items()},
            "guards": dict(guards),
            "guards_note": ("r17/r18 行资格=dev-r18 在案注记「两轮 G1/G2 "
                            "均满足」装载；r19=本轮 guards 实测"
                            "（g1_ok/g2_guard_ok 均 True）"),
            "ranking_rule": plan["comparison_rule"]["ordering"],
            "r16_baseline_m1": 0.771429,
        },
        "r20_recommendation": {
            "axes": cand["r20_axes"],
            "blind_reads": 12,
            "combination": "轴3+轴2 组合轮（A3_criterion_contact_"
                           "clarification+A2_blackdot_instrument_annotation）",
            "guidance": "§5B+§4(iii-a) 合成（两轴变更同时施加：r18 §5B "
                        "黑点中性仪器注记+r19 §4(iii-a) 可操作分辨条款；"
                        "各轴定义按冻结件合并）",
            "note": ("本轮=建议（dev-record 分包如实转记 run-r19 对照账排"
                     "序与冻结规则应用）；R20 执行须编排侧后续包按冻结件走"
                     "prep-record 预注册（先于该轮盲读冻结）；本建议只决定"
                     "「做不做、做哪个」，不预写结果"
                     "（combination_decision_rule.preregistration_note "
                     "原文）"),
            "preregistration_required": True,
            "render": "renders-r14b 四图字节复用（零仪器变更）",
            "round": "R20",
        },
        "r21_full_combination_trigger": {
            "check": ("三轴均各自正收益（各自 M1 不劣于 r16 基线 0.771429）"
                      "=否：轴1 r17 M1=0.88 劣于基线（负向）——触发条件不"
                      "成立；轴2/轴3 M1 优于基线"),
            "met": False,
            "per_axis_positive": {"r17_axis1": False,
                                  "r18_axis2": True,
                                  "r19_axis3": True},
            "rule_quote": plan["combination_decision_rule"][
                "ii_full_combination"],
        },
        "ranking_application": {
            "eligible_sorted": cand["eligible_sorted"],
            "note": ("按冻结 comparison_rule=(M1 升序, M2 升序, M3 升序, "
                     "M4 升序) 字典序：r19 轴3 第一（M1=0.461538 为已测配"
                     "置最低）、r18 轴2 第二、r16 基线参照行第三、r17 轴1 "
                     "末位（M1=0.88 劣于基线=负向、不进最优两轴组合——收"
                     "益方向描述、非守门出局：r17 G1/G2 满足）；与 run-r19 "
                     "ranking_by_comparison_rule 逐一相等（fail-closed）"),
            "r17_last_note": ("轴1 不进 R20 组合=实测结果（M1 负向）如实"
                              "登记，非惩罚性操作；早期轴轮字母与实验账分"
                              "列先例（r18：reject 但排序居首）延续"),
            "rows": {k: dict(v) for k, v in axis_rows.items()},
        },
        "role": ("冻结 combination_decision_rule/early_stop_rule 的 R19 后"
                 "应用（development 域描述性边界工具、非门、无字母语义、"
                 "不凌驾 APR-0011 与阈值；纯函数操作化、构造可测）"),
        "status": ("R20 候选=轴3+轴2 组合轮；R21 全组合触发=否（三轴皆正"
                   "不成立）+strong_single_axis_shortcut 实测命中（组合轮"
                   "仅一个、R21 不做）——两核对引用冻结原文，最终由编排侧"
                   "后续包执行、不预写结论"),
    }

    dispatch_incident_record = {
        "declared_date": DECLARED_DATE,
        "event": ("wave-3 重派时主审误派重复智能体：2×top-i3+2×bottom-i3 "
                  "并发同实例 ID（重派前未核对目标实例唯一性）"),
        "final_disk_state": ("盘上最终=一套完整自洽 i3 输出（top 跨板连续 "
                             "R19T-001..010；bottom 0 旗标）；12 件盲读原"
                             "文合法性/编号行为/旗数弃权记账已由 run-r19 "
                             "fail-closed 校验在案"),
        "lesson": ("重派前必须核对目标实例唯一性（编排侧纪律；后续轮次"
                   "重派/替换操作须先核对该实例无并发任务）"),
        "pinned_i3_full_sha256": {k: _sha(rel)
                                  for k, rel in REL_RAW_I3.items()},
        "pinned_i3_prefixes": dict(I3_PINNED_PREFIXES),
        "pinned_verification": ("live sha256_file 前缀逐一复核（本脚本 "
                                "fail-closed；与 s71 I3_PINNED_PREFIXES "
                                "同锚）"),
        "resolution": ("后完成者在未读取旧文件内容前提下删除重写；先完成"
                       "者的重复输出废弃"),
        "role": ("派发操作事故记录（如实、单列）：操作层事件，不改判读产"
                 "物完整性核验结论、不改字母裁决、不进任何度量；链完整性"
                 "由盘上哈希钉死在案"),
        "scope": ("单列如实记录：不构成判读/度量/裁决输入；先完成者重复"
                  "输出零残留（盘上=后完成者一套自洽输出、4 件 i3 哈希钉"
                  "死）；top-i3 跨板连续编号（R19T-001..004 applied + "
                  "R19T-005..010 prep1）与 bottom-i3 两板 0 旗标即该终态"
                  "的实测指纹"),
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 6 派次全部旗标中弃权旗占比"
                "（6 位小数；本轮实测 18/39）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 4/7）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径=分型件 round_totals "
                "{r}.families.existence_blackdot；本轮实测 4、全弃权；M3 "
                "槽位定义维持冻结件黑点口径——主度量已切换为 contact、"
                "contact=4 另列不占槽=判据侧轮的对照账纪律）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差=max−min（本轮实测 0.6−0.388889="
                "0.211111）",
            "contact_family_abstain_flags_rubric":
                "contact 族弃权旗数（全视，分型件 rubric 口径；本轮实测 4"
                "[top 4+bottom 0]、r16 基线 10、r13–r16 链 8/15/5/10 在"
                "案——本轮主通道度量、另列不占 M3 槽位）",
            "scope": "跨轮统一口径：全部=12 派次全口径（非代表配置子集）、"
                     "与分型件同法；单位=旗标条数（M3/contact）或 6 位小"
                     "数率（M1/M2/M4）",
        },
        "cross_round_status": {
            "measured_rows": {
                "r16_baseline": {"M1": 0.771429, "M2": 0.857143,
                                 "M3": 12, "M4": 0.261904},
                "r17_axis1": dict(EXPECT_R17_MEASURED),
                "r18_axis2": dict(EXPECT_R18_MEASURED),
                "r19_axis3": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                              "M3": EXPECT_M3, "M4": EXPECT_M4},
            },
            "note": ("轴3 现居已测配置第一（按冻结 comparison_rule=(M1 升"
                     "序, M2 升序, M3 升序, M4 升序) 字典序：R19 M1=0.461"
                     "538 为已测配置最低、R18 0.645161 次之、R17 M1=0.88 "
                     "劣于基线=负向居末；三轮 G1/G2 均满足=过资格门、基线"
                     "行非轴配置）——如实记录、不预写阶段2 结论"
                     "（combination_decision_rule.preregistration_note："
                     "本规则只决定「做不做、做哪个」，不预写结果）"),
            "role": ("轴3 单变量轮 M 元组四轮并列（r16 基线/r17 轴1/r18 轴"
                     "2/r19 轴3）登记（comparison_rule 冻结规则的已测行并"
                     "列；r17/r18 行=round18-dev-record 在案行实测装载、"
                     "r19 行=本轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r19.json（e5755a11…）盘上值"
            "装载（M1=18/39=0.461538 与 m.top_abstain_rate_r19、M2=4/7="
            "0.571429 与 bottom_side_observation、M3=4 与 black_dot_"
            "tracking（rubric 口径 existence_blackdot、r13–r16 132 条弃权"
            "旗重放对拍逐一相等）、M4=0.211111 与 view_layer.top."
            "abstain_rate_range、contact=4 与 contact_family_abstain_"
            "flags_rubric_r19 逐一相等，fail-closed），非手抄；axis-plan "
            "在案 r16 基线四键 [0.771429, 0.857143, 12, 0.261904] 与 "
            "run-r19 baseline_cross_check 交叉核对一致；M1 绝对降幅 "
            "0.771429−0.461538=0.309891 超显著收益阈值 0.10（跨轮实例群漂"
            "移混杂照旧声明、本轮为判据变更轮、改善不能归因于单变量以外因"
            "素；主度量 contact=4 落 marginal 支=M4 门 0.20 未达）"),
        "next_candidate_r20": combination_decision_application[
            "r20_recommendation"],
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "R19 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "status": ("R19 实测 (M1,M2,M3,M4)=(0.461538, 0.571429, 4, "
                   "0.211111)（contact=4 另列）；资格门=G1/G2 均满足→进入"
                   "排序；轴3 现居已测配置第一（如实记录）；字母与实验账分"
                   "列互不改写（本轮 marginal 且排序居首/显著收益命中——记"
                   "录为部分收益、轴3 不判定为胜出；按冻结规则写下一候选="
                   "R20=轴3+轴2 组合轮，见 combination_decision_application"
                   "）；不预写阶段2 结论"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4},
    }

    directional_observation_vs_r16 = [
        ("R16→R19 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 沿用"
         "无新增版本：12/12 派次自述「未读取盘上任何其他文件」；R19T/R19B "
         "前缀随 r19 指引 §6 落盘固化）；旗标 49→50→46（六实例旗数 top "
         "27/35 基线轮 14/8/9→r18 14/8/9→r19 11/18/10、bottom 4/3/5→6/6"
         "/7→4/3/0；非弃权 17→24、弃权 33→22）；全旗标合计弃权率 0.66"
         "（33/50，附记口径）→0.478261（22/46，附记口径）；预注册主通道三"
         "分判据：(s) contact=4≤5 ✓ 且 M1=18/39=0.461538≤0.85 ✓ 且 G1/G2 "
         "维持 ✓、唯 M4=0.211111>0.20 未过⇒supported 未成立；(m) 未达 "
         "supported 且（contact ≤7 或 M4 ≤0.26）且 G1/G2 维持——两途径均"
         "满足⇒字母裁决=marginal（记录为部分收益、轴3 不判定为胜出）；代表"
         "配置（top=top-i1：中位 11 唯一；bottom=bottom-i2：中位 3 唯一）"
         "弃权率 0.8（12/15，r18）→0.428571（6/14）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.666667/"
         "0.928571/0.666667（r16，极差 0.261904）→0.642857/0.5/0.777778"
         "（r18，极差 0.277778）→0.454545/0.388889/0.6（r19，极差 "
         "0.211111=M4 收窄）——轴3 条款轮（渲染零变更=renders-r14b 字节复"
         "用）下聚合落点 27/35=0.771429→20/31=0.645161→18/39=0.461538（绝"
         "对降幅 0.309891 超计划件显著收益阈值 0.10=显著收益定义命中；跨轮"
         "实例群漂移混杂照旧声明[r15→r16 纯重抽漂移 0.09064 在案参照]、本"
         "轮为判据变更轮；M1 为 supported 附加门、M4 门未过不改字母）；"
         "bottom 1.0/0.8/0.75（r16，极差 0.25）→0.833333/0.333333/"
         "0.857143（r18，极差 0.52381）→0.75/0.333333/None（r19，按可计"
         "算实例极差 0.416667；bottom-i3 两板零旗标=None）——bottom 全旗"
         "聚合弃权率 12/14=0.857143→13/19=0.684211→4/7=0.571429（improved "
         "改善方向如实单列）；本轮零旗标派次=2（bottom-i3 两板；r17 的 2 "
         "格→r18 的 0 格→r19 的 2 格；零旗格 view_check=not_applicable 不"
         "进弃权率分母）。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r16 的 r12 以"
         "来首次逐实例命中（union 1/13=R16T-001×GT-REVC-AP-6-R2LED2）在 "
         "r17/r18 连续零命中后、r19 再现 union 1/13（0.076923）——唯一命中"
         "=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT（other_advisory、"
         "containment 1.0、面积比 8.227698、(iii-a) 侵入支产物旗，机制观察"
         "在案）；GT 条目层 agreement=0/13（0.0，≥2/3 规则：单实例命中不"
         "计）——单实例命中不稳定如实登记；代表配置 gt_recall_total 0.0"
         "（0/13）、seed_match_rate 0.0（0/8，诊断口径，禁称 precision/"
         "FPR）。类别门 2 条近失如实（几何门 0→0 延续）：R19T-004×GT-"
         "REVC-AP-6-R2LED2（silk_readability×courtyard_crowding、"
         "containment 0.853766）与 R19T-009×GT-REVC-P1-L1NB（other_"
         "advisory×courtyard_crowding、containment 0.924945）近邻交叠类别"
         "不符出局；bottom 7 旗（4 弃权+3 非弃权）零匹配属结构性：GT 13 条"
         "全部 side=top、bottom 无 GT 在案（gt-audit-r1：bottom GT=无源已"
         "关闭）⇒ bottom 旗标与 GT 匹配应为空，如实。"),
        ("通道归因（vs R18，预注册重放方法）：几何门面积比出局 0→0"
         "（guard_ok=True 独立单列、不构成 r19 字母裁决输入）；类别门 0→2"
         "（近失条目如上、r16 在案 1 条 R16T-006 之后 r17/r18 连续零、r19 "
         "回升 2 条逐轮计数如实）；视角门 0→0（top 非弃权旗与同态 GT 零视"
         "角错位交叠；bottom 非弃权旗零匹配属结构性）。通道链自 r6：几何门 "
         "r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→r15=0→r16=0"
         "→r17=0→r18=0→r19=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→"
         "r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=2。重放与 "
         "compare_v3 对拍一致。"),
        ("预注册假设（axis-plan-r19-criterion-operational）字母裁决="
         "marginal（落支=(m) 未达 supported 且（contact ≤7 或 M4 ≤0.26）"
         "且 G1/G2 维持——记录为部分收益（轴3 不判定为胜出）；命中途径="
         "contact ≤7（实测 4）；M4 ≤0.26（实测 0.211111）——两途径均满足；"
         "r19-prep-record hypothesis_test.adjudication 判据原文执行；唯一"
         "正式裁决）。实测：contact（contact 族弃权旗数，分型件 rubric 口"
         "径）=4 vs r16 基线 10（rubric 机械套用：关键词表/优先级从 "
         "abstain-typology-r13-r16.json 装载，r13–r16 132 条弃权旗重放对拍"
         "逐一相等后套用 r19，链值 8/15/5/10 在案；基线=分型件 r16 实测装"
         "载交叉核对一致，不手工抄数；分视角 top 4+bottom 0，对照 r16=10 "
         "全 top）；(s) 支 contact ≤5=True 且 M1=top 全旗聚合弃权率 18/39="
         "0.461538≤0.85 成立（r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧"
         "复算 27/35=0.771429，live 重放与在案登记/axis-plan 锚交叉核对一"
         "致，不手工抄数）且 G1/G2 维持，唯 M4（top 逐实例弃权率极差）="
         "0.211111→M4 门 ≤0.20 不成立⇒supported 未成立；(r) 支 contact "
         "≥8 且 M4 >0.26=False。守门 G1（bottom courtyard 非弃权 0/0/0 维"
         "持）=维持、G2（guard_ok=True 维持，几何门 R18=0→R19=0）=维持——"
         "均独立单列，守门均维持、不触发出局（per axis-plan early_stop_"
         "rule.guard_failure_exit）。"),
        ("机制观察单列（不凌驾）：(a) (iii-a) 逐旗落支分布（旗级 14 旗="
         "textual 证据可归支者）：残余弃权支（第三支）=8（全部弃权旗：字面"
         "援引 6+语言归类 2）、侵入支（分支(2)）=6（全部非弃权报告旗：字面"
         "援引「分支(2)」2+语言归类 4）、间隙支（分支(1)）旗级=0——间隙支"
         "路径全部在判正常路径消化（notes 级 4 派次自述「可辨认间隙带→视觉"
         "贴近→继续判定→判正常不报告」，top-i3/bottom-i3 两实例四板）；"
         "(b) (iii-a) 措辞援引计数：旗级 location_evidence 含「(iii-a)」="
         "6 旗（全部弃权旗）、含「分支(」=2 旗（全部非弃权黑点-焊盘接触报"
         "告旗=prep1-bottom-i2 R19B-001/002）、notes 级含「(iii-a)」=10/12"
         " 派次（未援引 2 派次=applied-bottom-i1/applied-top-i3，如实分"
         "列）；(c) 机制方向（描述性）：条款把部分原属「无法区分」弃权域的"
         "黑点-焊盘贴近距离引导到侵入支负责任报告（prep1-bottom-i2 2 条）"
         "并产出本轮唯一 GT 命中旗（prep1-top-i3 R19T-009↔GT-REVC-P1-"
         "L1SHORT，侵入支合并证据报告）；残余弃权支仍按 (iii) 原文保留 8 "
         "旗；黑点族（rubric 口径）=4 vs r18=13 显著回落（全部 bottom："
         "bottom-i1 3+bottom-i2 1；其中 applied-bottom-i2 R19B-001 为"
         "rubric「圆点」词命中组件内部圆点、非黑点现象如实注明）+黑点转非"
         "弃权旗 6 条（top 4：i2/i3 两板按 §4(ii) 孤立+样式不一致归兜底类"
         "报告；bottom 2：prep1-bottom-i2 分支(2) 侵入证据判接触/交叠报"
         "告=非弃权报告路径首现）+黑点判正常派次 3（prep1-top-i1+applied/"
         "prep1-bottom-i3）；(d) 存在性其他=14 vs r18=12（+2 如实记录、未"
         "显著上升=弃权转移对照口径如实登记）；top 弃权构成分型=接触性 "
         "11→8（r17）→8（r18）→5、存在性 15→14（r17）→12（r18）→13、"
         "其他 1→0→0→0（18 条逐旗摘录在案）；(e) 绿区语义化：bottom 6 派"
         "次全部按 §4(i) 空隙/翼瓣语义化路径（6/6 对照 r18 的 5/6）、§5A "
         "显式援引 4/6 派次（指引 §5A 原文逐字保留、援引波动属实例自述异质"
         "性、如实登记不作废）。"),
        ("bottom 改善通道单列（M2=4/7=0.571429 vs r16 基线 12/14=0.857143"
         " vs r18 13/19=0.684211，improved 方向；不影响字母）：(1) 零旗标"
         "派次=2 个（bottom-i3 两板零旗标=零旗标实例；top 侧 12 格全部≥1 "
         "旗）；(2) 黑点族弃权旗（rubric 口径）=4 条 vs r16=12/r18=13（数"
         "量回落；全部 bottom 侧）；(3) 黑点-焊盘接触分支(2) 非弃权报告 2 "
         "条（prep1-bottom-i2，bottom-i2 弃权率 1/3 为 bottom 最低）；"
         "(4) bottom courtyard 类旗=0 条——非弃权 courtyard 0/0/0 维持"
         "（G1，零旗标路径；bottom-i1 4 旗=placement 1 非弃权+other_"
         "advisory 3 弃权[黑点 3]、bottom-i2 3 旗=other_advisory 3）。"),
        ("工具行为与派发操作（协议侧 v1.2 沿用第八轮，如实入账）：R19 十二"
         "派次全部以 Read 工具直读内嵌图像、逐派次 reading_notes 自述「未读"
         "取盘上任何其他文件」（12/12 逐字摘录在案 reader_tool_evidence）；"
         "全部判读输入严格限于（指引+该 PNG），零 GT/零诊断/零 legend=非盲"
         "读违规；flag_id 编号行为混合（top-i3 两板跨板连续、其余实例两板各"
         "自从头编号）=实例输出行为差异如实登记、编排侧按 (state, flag_id) "
         "限定；wave-3 派发事故（重派重复智能体：2×top-i3+2×bottom-i3 并发"
         "同实例 ID；后完成者未读取旧文件内容前提下删除重写、先完成者重复输"
         "出废弃；盘上终态=一套自洽 i3 输出、4 件哈希钉死 7941cb00/"
         "5591ce98/f4069303/fcc69fb5）如实单列 dispatch_incident_record"
         "（教训=重派前必须核对目标实例唯一性）；跨轮实例不同+轮内实例差异"
         "=混杂因素照旧声明（reader_instance_note）。"),
        ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延续，零"
         "阈值改动零期望）：courtyard 类旗标 6 条（top 6+bottom 0）：非弃权 "
         "2（prep1-top-i1 R19T-001/002 贴邻/共边报告）+弃权 4（(iii-a) 残"
         "余弃权支）——非弃权 courtyard 2 条零命中；命中链 r8=1→r9=0→r10=1"
         "→r11=3→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=0（r16 的 "
         "R16T-001 之后零命中延续）。reroute 类 3 条（非弃权报告 2[applied-"
         "top-i2 R19T-007+prep1-top-i2 R19T-002]+弃权 1[applied-top-i1 "
         "R19T-005 存在性出口]）；产量链 r8=1→r9=0→r10=2→r11=3→r12=3→r13=2"
         "→r14=1→r15=4→r16=2→r17=1→r18=3→r19=3；「等长|蛇形」旗级子串零命"
         "中——滥用型通道被动追踪=0。"),
    ]

    honest_conclusion = (
        "本轮（development 域，轴3 判据侧单变量轮（§4(iii-a) 可操作分辨条"
        "款增补：判读指引=observation-guidance-r19.md 8633bda5[r15 基座 "
        "d5babc93 机械变换派生+§4 增补 (iii-a) bullet——判据节首次变更先例："
        "增补式[§4 内、(iii) 接触性判据句之后、对照说明块之前插入 bullet]+"
        "反放宽条款逐字保留[「仅因形态不熟悉、不确定其设计含义，不构成判为"
        "正常设计特征的理由」原文一字不松]+锚断言[content_sha256 97bb4c0f、"
        "anchor/expected_hits 机械插入断言]；§2–§7 其余逐字承 r15、§5A 原"
        "文逐字保留、无 §5B]+渲染零变更=renders-r14b 四图字节复用+GT/阈值"
        "/协议零变更（13 条冻结、v1.1+v1.2 维持）；instrument_change."
        "changed=false 已预注册；唯一实验变量=判据 §4(iii-a) 条款；per "
        "axis-experiment-plan-r17-r20 冻结件[用户 2026-09-09 指令操作化]）"
        "）12 派次 46 旗标中 22 弃权、24 非弃权：代表配置（top-i1+bottom-i2 "
        "双唯一）gt_recall=0.0（0/13）、seed_match_rate=0.0（0/8，诊断口"
        "径，禁称 precision/FPR）、abstain_rate=0.428571（6/14），联合评价 "
        "not_met（gt_recall、seed_match_rate 两项未达 APR-0011 暂行线；"
        "gt_count 13≥12 与 abstain_rate 0.428571≤0.5 单分项入线；诊断对照"
        "，非采纳门；连续达标计数 0→0；GT 条目层 union=1/13、agreement="
        "0/13 双口径并列——唯一命中=prep1-top-i3 R19T-009↔GT-REVC-P1-"
        "L1SHORT（containment 1.0、(iii-a) 侵入支产物旗），r16 的 1/13 后 "
        "r17/r18 连续零、r19 再现=单实例命中不稳定如实）。预注册假设"
        "（axis-plan-r19-criterion-operational）裁决（按 r19-prep-record "
        "hypothesis_test.adjudication 三分判据）=marginal（字母口径，唯一"
        "正式裁决）：落支=(m) 未达 supported 且（contact ≤7 或 M4 ≤0.26）"
        "且 G1/G2 维持——记录为部分收益（轴3 不判定为胜出）；命中途径="
        "contact ≤7（实测 4）与 M4 ≤0.26（实测 0.211111）两途径均满足。"
        "实测：contact（主度量，分型件 rubric 口径）=4 vs r16 基线 10（"
        "rubric 机械套用：r13–r16 132 条弃权旗重放对拍逐一相等后套用 r19，"
        "口径忠实性证明；分视角 top 4+bottom 0）；(s) 支 contact ≤5 ✓ 且 "
        "M1=top 全旗聚合弃权率 18/39=0.461538≤0.85 ✓（r16 基线=同一聚合逻"
        "辑对 run-r16 内嵌实例记录双侧复算 27/35=0.771429，live 重放与在案"
        "登记/axis-plan 锚交叉核对一致，不手工抄数）且 G1/G2 维持 ✓，唯 "
        "M4（top 逐实例弃权率极差）=0.211111>0.20 未过——supported 未成立"
        "的关键=M4 门；(r) 支 contact ≥8 且 M4 >0.26=False；(m) 支两途径"
        "均满足。守门 G1（bottom courtyard 非弃权 0/0/0 维持）与 G2"
        "（guard_ok=True，几何门 0→0）均维持、不触发出局（axis-plan "
        "early_stop_rule）。机制观察单列（不影响字母）：(iii-a) 逐旗落支分"
        "布=残余弃权 8+侵入 6+间隙 0（间隙支全部在 notes 级判正常路径消化、"
        "4 派次）；援引计数=旗级 (iii-a) 6 旗+分支( 2 旗+notes 级 10/12 "
        "派次（未援引 2 派次如实分列）；黑点族=4 vs r18=13 显著回落+黑点转"
        "非弃权旗 6 条+黑点判正常派次 3；存在性其他=14 vs r18=12（+2 如实"
        "记录、未显著上升=弃权转移对照口径）；top 弃权构成分型=接触性 5+存"
        "在性 13+其他 0（r18 对照 8/12/0、r16 对照 11/15/1）。实验对照账："
        "本轮 (M1,M2,M3,M4)=(0.461538, 0.571429, 4, 0.211111)（M3 槽位=冻"
        "结件黑点族口径、contact=4 另列不占槽；axis-plan benefit_metrics "
        "口径实测装载），轴3 现居已测配置第一（R19 M1=0.461538 < R18 "
        "0.645161 < R16 基线 0.771429 < R17 0.88，按冻结 comparison_rule "
        "M1 升序字典序；三轮均过 G1/G2 资格门）——显著收益定义命中（M1 绝"
        "对降幅 0.309891≥0.10；r18 降幅 0.126268 亦 ≥0.10）；按冻结 "
        "combination_decision_rule 写下一候选=R20=轴3+轴2 组合轮"
        "（guidance=§5B+§4(iii-a) 合成、renders-r14b 零仪器变更、12 派次；"
        "须各自 prep-record 预注册后执行）；R21 全组合触发条件核对=否（三"
        "轴皆正不成立：轴1 M1=0.88 负向）+early_stop strong_single_axis_"
        "shortcut 实测命中（最优单轴 M1=0.461538≤0.60→阶段2 仅一个组合轮、"
        "R21 不做）——两核对引用冻结原文、不预写结论。marginal=预注册阈值"
        "命中方向的描述性结论、非因果证明——「正确测出部分有效同样是有效证"
        "据」；单轮 n=3、development 域只描述不断言；字母裁决只回答「(iii-a) "
        "条款是否使 contact 族弃权显著回落且判定一致性改善」的计划件判据命"
        "中方向；机制观察/度量教训单列、不凌驾不改写字母裁决；APR-0011 门"
        "（代表配置）与字母裁决分列不合并；本轮判据均为描述性边界、非门阈"
        "值（门零改动）。残余实例差异仍存（top 弃权率 0.454545/0.388889/0.6 "
        "极差 0.211111、bottom 0.75/0.333333/None 按可计算实例极差 "
        "0.416667；板内孤立焊盘对跨实例/跨板出口不同[非弃权报告/弃权/判正"
        "常不报告三出口]=判读语义歧义未穷尽）。bottom 7 旗（4 弃权+3 非弃"
        "权）零匹配属结构性（GT 13 条全部 side=top，bottom GT 无源在案 "
        "gt-audit-r1）；本轮 12 格零旗标派次=2（bottom-i3 两板、item 5 None "
        "口径触发；top 全部有定义）。「系统性正常→不报告」通道 bottom 六派"
        "次使用（§4(i) 判读路径延续，摘录在案）。类别门 2 条近失如实（"
        "R19T-004×AP-6-R2LED2、R19T-009×P1-L1NB 近邻交叠类别不符出局）。"
        "工具行为混杂如实入账（12/12 派次自述「未读取盘上任何其他文件」；"
        "R19T/R19B 前缀随指引落盘固化；flag_id 编号行为混合=实例输出行为差"
        "异如实登记）；wave-3 派发事故如实单列（盘上终态哈希钉死、判读产物"
        "完整性不受影响）。GT 侧三候选经 gt-audit-r1 全部关闭（延续零改动，"
        "GT 侧不再有候选；r19 union 1/13 与 bottom GT 无源结构相容）。不做"
        "「能力已修复/已达成」类断言；in_calibrated_range 恒 False。本批证"
        "据按协议 v1 §4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r19-prep-record no_loosening_note：本轮判"
         "据侧变更方向=收窄而非放松——(iii-a) 只把「无法区分」收窄为「无任"
         "何可辨认证据」的情形，把有证据可判的情形引导到负责任判定；两支新"
         "判定路径均以「可辨认证据」为责任条件（间隙支仍须按 (i)(ii) 与三路"
         "出口判定、不得以条款为由直接放行；侵入支照常输出旗标并承担同等判"
         "断责任）；「仅因形态不熟悉、不确定其设计含义，不构成判为正常设计"
         "特征的理由」反放宽条款原文一字不松、三路出口显式化逐字保留；三分"
         "判据描述性边界与门分列）。"),
        ("R16 对照基线=calibration-run-r16.json（同一聚合逻辑对内嵌实例记录"
         "双侧复算 top 27/35=0.771429、bottom 12/14=0.857143，与在案登记/"
         "axis-plan 锚交叉核对一致，不手工抄数）；主度量 contact 基线=分型"
         "件 rubric 口径 10（r13–r16 链 8/15/5/10 重放对拍逐一相等后套用，"
         "不手工抄数）；M1 绝对降幅 ≥0.10=计划件显著收益阈值（r15→r16 纯重"
         "抽漂移 0.09064 为历史幅度参照）；轮间对比只做方向性描述（跨轮实例"
         "群混杂照旧，per axis-plan comparison_rule.drift_confound_note 显"
         "式容忍；本轮为判据变更轮）；M1 分母（top 旗数 35→31→39）本身随轮"
         "变化、弃权率比较含分母效应，构成分解（top 弃权构成分型+(iii-a) 落"
         "支+黑点转非弃权旗）单列补足。"),
        ("通道归因方法：照抄 run-r15–run-r19 channel_attribution 的重放口径"
         "（deviation_note 承接），R15/R16/R17/R18/R19 均以内嵌输入确定性重"
         "放并与 compare_v3 对拍（run-r19 channel_attribution.method）；重放"
         "复现与在案登记一致（fail-closed）；类别门 r19=2 条近失（几何门 "
         "0→0 延续）如实计数、不构成字母裁决输入。"),
        ("读者实例行为与派发操作披露如实记录：R19 十二派次 v1.2 规约自述合规"
         "（纯 Read 直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 "
         "reading_notes 原文在案）；输出格式披露（12 件缩进格式冻结原始判读"
         "件、零改动直读）parse 校验全部通过；flag_id 编号行为混合（top-i3 "
         "两板跨板连续 R19T-001..010、其余实例两板各自从头编号）=实例输出行"
         "为差异如实登记、编排侧按 (state, flag_id) 限定；wave-3 派发事故"
         "（重派重复智能体、后完成者未读取旧文件内容前提下删除重写、先完成"
         "者重复输出废弃、盘上终态=一套自洽 i3 输出）如实单列 "
         "dispatch_incident_record（4 件 i3 哈希钉死 7941cb00/5591ce98/"
         "f4069303/fcc69fb5；教训=重派前必须核对目标实例唯一性）——操作层"
         "事件、不改判读产物完整性核验结论、不改字母裁决、不进任何度量。跨"
         "轮 reader 实例不同+轮内实例差异=混杂因素，每视角 n=3；本轮轮前评"
         "审=pre_round_review 在案（r19-prep-record）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=marginal 维持"
         "不变（marginal=部分收益的描述性边界结论、非因果证明——「轴3 不判"
         "定为胜出」如实登记；单轮 n=3 小样本方向性证据；主通道三分判据"
         "（contact/M4/M1/G 四件组）与 APR-0011 门分开表述、互不凌驾：门联"
         "合评价（代表配置）=not_met 如实分列）；不得回溯改判既往轮次"
         "（r8–r18 字母裁决维持不变）。"),
        ("度量教训在案（供 R20 预注册参考、本轮不追溯适用）：主度量切换（轴2 "
         "黑点 M3→轴3 contact）时四元组 M3 槽位定义维持冻结件黑点口径、新主"
         "度量另列不占槽=判据侧轮的对照账纪律；contact 计数口径=分型件 "
         "rubric 机械套用（计数口径跨轮漂移是历史教训：r15 dev-record prose "
         "口径 7 vs 分型件 rubric 口径 8 在案，axis-plan M3_caveat 已声明一"
         "律采用 rubric 口径）；判据节首次变更的先例意义（后续判据侧迭代的"
         "模板纪律=增补式+反放宽逐字保留+锚断言，per r19-prep-record "
         "metric_lesson_separate）单列；实验对照账四轮并列如实（轴3 排序居"
         "首但 marginal——字母与实验账分列互不改写的在案先例延续）。"),
    ]

    next_iteration_targets = [
        ("按冻结 combination_decision_rule.i_stage2_combo_pair 写下一候选="
         "R20=轴3+轴2 组合轮（r19_axis3+r18_axis2 过守门轮次中排序最优两"
         "轴）：guidance=§5B+§4(iii-a) 合成（两轴变更同时施加、各轴定义按"
         "冻结件合并）、renders-r14b 四图字节复用（零仪器变更）、12 派次——"
         "R20 执行须编排侧后续包各自 prep-record 预注册后执行（先于该轮盲"
         "读冻结）、不预写结论；组合轮=轴1 M1 改善归因的部分重复验证机会"
         "（r19 M1 降幅 0.309891 与 r18 0.126268 均超阈值 0.10；部分重复"
         "≠独立重复、如实登记验证力度）。"),
        ("R21 全组合触发条件核对=否（如实引用冻结件 ii_full_combination："
         "三轴均各自正收益不成立——轴1 r17 M1=0.88 劣于 r16 基线 0.771429"
         "=负向；轴2/轴3 优于基线）+early_stop strong_single_axis_shortcut "
         "实测命中（最优单轴 M1=0.461538≤0.60→阶段2 仅做最优单轴+次优单轴"
         "一个组合轮、R21 不做）——两核对引用冻结原文在案；最终做不做/做哪"
         "个由编排侧后续包按冻结规则执行、本包不预写决策。"),
        ("轴1 结果登记：r17 轴1（渲染分辨率倍增）M1=0.88 劣于基线=负向、"
         "comparison_rule 排序末位、不进 R20 组合——收益方向描述、非守门出"
         "局（r17 G1/G2 满足）；r17 字母=reject 维持不变（不得回溯改判）。"),
        ("判据节首次变更先例归档：增补式+反放宽条款逐字保留+锚断言（"
         "content_sha256 97bb4c0f/anchor/expected_hits 机械插入断言）=后续"
         "判据侧迭代的模板纪律（per r19-prep-record metric_lesson_separate "
         "单列）；(iii-a) 残余弃权支 8 旗=「无任何可辨认证据」情形仍按 "
         "(iii) 原文弃权——判据侧不再迭代（无新判据变更候选在案）；黑点接"
         "触性子问题的残余实例差异照旧声明（板内孤立焊盘对跨实例/跨板出口"
         "不同=判读语义歧义未穷尽）。"),
        ("留出集时机=开发线收敛（须用户拍板）：r19 字母=marginal（部分收益）"
         "→收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未达"
         "成，不得写成已达成）；GT 侧维持全关闭声明延续（gt-audit-r1["
         "1f20554a…]三候选全部关闭，r9–r19 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r19 union 1/13[唯一命中=prep1-top-i3 "
         "R19T-009↔GT-REVC-P1-L1SHORT，单实例命中不稳定如实]、非新 GT）；"
         "in_calibrated_range 恒 False 直到正式采纳（须人工批准）；达标证据"
         "仍须留出集（out/v3-tl2/holdout/HOLDOUT-PLAN.md a4b80193… 与 "
         "datasets/holdout-candidates-r1 在案）。"),
    ]

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "combination_decision_application": combination_decision_application,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": directional_observation_vs_r16,
        "dispatch_incident_record": dispatch_incident_record,
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本件=R19 收口包 B（dev-record 分包）：development 域第 19 轮迭代"
        "（轴3 判据侧单变量轮）的轮次开发记录；迭代轮不得冒充留出证据。",
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev18["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r19 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r19 全旗标合计 22/46=0.478261 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R18 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 两项未达暂行线；gt_count 13≥12 "
                         "与 abstain_rate 0.428571≤0.5 单分项入线）——GT 条"
                         "目层 union 口径 1/13=0.076923 亦未达 0.75（唯一命"
                         "中=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT；"
                         "agreement=0/13[≥2/3 规则]；双口径与门分列如实）"),
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
            "rule]+组合决策规则+early_stop_rule，先于 R17–R21 任何实验轮盲"
            "读冻结防事后择优；stage1 R19=轴3 判据侧可操作分辨条款轮）→"
            "r19-prep-record.json（e4cf2d3c…，本轮预注册件，measurement_"
            "design 五条聚合口径与 hypothesis_test.adjudication 三分判据"
            "（supported contact ≤5 且 M4 ≤0.20 且 G1/G2 维持且 M1 ≤0.85/"
            "marginal 未达 supported 且 contact ≤7 或 M4 ≤0.26 且 G1/G2 维"
            "持/reject contact ≥8 且 M4 >0.26 或 G 破坏）先于盲读冻结；"
            "instrument_change.changed=false；changed_variables=[§4(iii-a) "
            "可操作分辨条款（guidance-s4-iii-a-contact-operational-clause）"
            "+轮次标识机械同步（round-identity-sync），两件登记]；"
            "manipulated_factor=指引增补 §4(iii-a)[唯一操纵因素]；no_"
            "loosening_note=判据侧变更方向=收窄而非放松、反放宽条款原文一"
            "字不松）→判读指引=observation-guidance-r19.md（8633bda5…，"
            "r15 基座 d5babc93…机械变换派生 mechanical_transform_derive："
            "§2–§7 除 (iii-a) 增补外逐字承 r15[分段+substring 双重断言]、"
            "§5A 原文逐字保留、机械变换 edit_list 八件逐件登记[任务枚举+轮"
            "次标识同步+§4 (iii-a) 条款增补 bullet、content_sha256 97bb4c0f"
            " 锚断言]；byte_size 19878→21435=delta 1557）→渲染零变更"
            "（renders-r14b 四图字节复用、与 r14/r15/r16/r17/r18 盲读同一批"
            "文件[applied-top 298bc620/applied-bottom d7284259/prep1-top "
            "b2f84524/prep1-bottom d7284259，bottom 两图字节同；witness-r14b "
            "b63771f9 在案]）→12 次盲读[wave-3 派发事故如实单列：重派重复"
            "智能体、盘上终态=一套自洽 i3 输出、4 件哈希钉死 7941cb00/"
            "5591ce98/f4069303/fcc69fb5；top-i3 跨板连续 R19T-001..010]→"
            "run-r19（e5755a11…，本链执行落盘）；GT 重投影沿用 derivation-"
            "log-r5.json（62343380…）零新派生（GT 全部 side=top；判据变更"
            "不改 GT 冻结纪律）；GT 冻结纪律：轮后未增删改；gt-audit-r1"
            "（1f20554a…）结论维持 GT 零改动（三候选关闭，gt_audit_reference "
            "在案）"),
        "reference_hash_manifest": reference_hash_manifest,
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域轴3 判据侧单变量轮（第十九轮）：渲染零变更="
            "renders-r14b 四图字节复用（与 r14/r15/r16/r17/r18 盲读同一批文"
            "件；no_instrument_change=true）+判读指引=observation-guidance-"
            "r19.md（8633bda5 实测锚，r15 基座 d5babc93 机械变换派生 "
            "mechanical_transform_derive：§2–§7 除 (iii-a) 外逐字保留[分段"
            "+substring 双重断言复核]、§5A 原文逐字保留、§4 增补 (iii-a) 可"
            "操作分辨条款=判据节首次变更先例[增补式+反放宽条款逐字保留+锚"
            "断言；条款把「无法区分」收窄为「无任何可辨认证据」的情形、是"
            "判定路径的澄清而非判断责任的放松]）+GT 集/协议阈值与度量版本/"
            "比较器常量零改动（GT 重投影沿用 derivation-log-r5——零新派生；"
            "gt-audit-r1 三候选关闭结论延续）；协议 v1.1+v1.2 维持无新增版"
            "本；instrument_change.changed=false 已预注册（changed_variables="
            "[§4(iii-a) 条款+轮次标识机械同步]；轴=axis-plan stage1 R19="
            "A3_criterion_contact_clarification）；检验假设 axis-plan-r19-"
            "criterion-operational（判据=r19-prep-record.json hypothesis_"
            "test.adjudication 三分判据：supported=contact ≤5 且 M4 ≤0.20 "
            "且 G1/G2 维持且 M1 ≤0.85/marginal=未达 supported 且 contact "
            "≤7 或 M4 ≤0.26 且 G1/G2 维持/reject=contact ≥8 且 M4 >0.26 或 "
            "G 破坏，轮后如实执行：字母裁决唯一正式+机制观察/度量教训单列；"
            "守门 G1/G2 独立单列，任一破坏→轴3 按 plan early_stop_rule 出"
            "局）；主通道三分判据与 APR-0011 门（gt_recall≥0.75/"
            "seed_match_rate≥0.5/abstain_rate≤0.5）与 CONTAINMENT_MIN/"
            "AREA_RATIO_MAX 常量各自独立计算、互不凌驾、分开表述；"
            "measurement_design 五条聚合口径先于盲读冻结；跨轮收益比较按 "
            "axis-plan 冻结规则（R19 行见 axis_experiment_ledger：轴3 现居"
            "已测配置第一、下一候选=R20=轴3+轴2 组合轮、如实记录、不预写阶"
            "段2 结论）；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R19, "sha256": run19_sha},
        "schema_version": SCHEMA_VERSION,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s72-cal-r19-devrecord] round19-dev-record: {status}")
    print(f"[s72-cal-r19-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch={dev['hypothesis_test_i']['measurement'][
              'letter_branch']}")
    print(f"[s72-cal-r19-devrecord] 三分判据: (s) contact=4≤5 ✓+M1 18/39="
          f"0.461538≤0.85 ✓+G1/G2 ✓、唯 M4=0.211111>0.20 未过；(r) 未落；"
          f"(m) 两途径均满足（contact ≤7 ✓、M4 ≤0.26 ✓）⇒ marginal（记录"
          f"为部分收益、轴3 不判定为胜出）")
    print(f"[s72-cal-r19-devrecord] 守门: G1=维持（bottom courtyard 非弃权 "
          f"0/0/0，零旗标路径）、G2=维持（几何门 0→0，guard_ok=True）→不触"
          f"发出局")
    print(f"[s72-cal-r19-devrecord] 机制观察: (iii-a) 落支=残余弃权 8+侵入 6+"
          f"间隙 0[间隙支 notes 级判正常 4 派次]；援引=旗级 (iii-a) 6+分支( 2+"
          f"notes 级 10/12；黑点族 4 vs r18=13+转非弃权 6+判正常 3；存在性其"
          f"他 14 vs r18=12（+2 未显著）")
    print(f"[s72-cal-r19-devrecord] 实验对照账: (M1,M2,M3,M4)=(0.461538, "
          f"0.571429, 4, 0.211111)（contact=4 另列）；排序 r19 第一、r18 第"
          f"二、r17 M1=0.88 负向居末；显著收益 0.309891≥0.10 命中；下一候选"
          f"=R20=轴3+轴2 组合轮（R21 触发=否、early_stop 快捷通道命中→组合"
          f"轮仅一个）")
    print(f"[s72-cal-r19-devrecord] 派发事故: wave-3 重派重复智能体（2×top-i3+"
          f"2×bottom-i3 并发同实例 ID）如实单列；盘上终态=一套自洽 i3 输出、"
          f"4 件哈希钉死 7941cb00/5591ce98/f4069303/fcc69fb5；教训=重派前必"
          f"须核对目标实例唯一性")
    print(f"[s72-cal-r19-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s72-cal-r19-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0 in_calibrated_range=恒 False")
    print(f"[s72-cal-r19-devrecord] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print(f"[s72-cal-r19-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s72-cal-r19-devrecord] R19 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=marginal 唯一正式（部分收益、不判胜出）；机制观"
          "察/度量教训单列不凌驾；in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
