#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s75_calibration_r20_devrecord.py — R20 CLOSE 包 B：
round20-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律；
底稿=s72_calibration_r19_devrecord.py 同构重建）。

R20=development 域 stage2 组合轮（axis-experiment-plan-r17-r20 stage2
唯一组合轮=轴3+轴2 两轴变更并施，用户 2026-09-09「三条轴单独/组合/全
组合尝试，选择收益最大的继续」指令操作化冻结件在案；变更=判读指引合成
observation-guidance-r20.md 9cdac9ed=r19 基座 8633bda5 机械变换派生：
r19 基底+§5B 黑点仪器注记节自 r18 指引 cadcb8f3 逐字转录整节插入
[content_sha256 19ecdb42 跨代哈希交叉锚]+§6 前缀轮次标识机械同步；
§4(iii-a) 随 r19 基座逐字承继零改动=两增补并集（§5B+(iii-a)）；渲染零
变更=renders-r14b 四图字节复用；GT/阈值/协议零变更；instrument_change.
changed=false 已预注册）。预注册假设（axis-plan-r20-combo-additivity）
ordering 三分判据轮后裁决=reject（唯一正式裁决）：
- (s) 支 R20 四元组 (0.636364, 0.285714, 6, 0.25) 在冻结
  comparison_rule.ordering「(M1 升序, M2 升序, M3 升序, M4 升序) 字典序」
  下劣于最优单轴 r19 (0.461538, 0.571429, 4, 0.211111)（M1 首键即分胜负）
  ⇒supported 未成立；(r) 支 G1 破坏命中（bottom courtyard 非弃权实测
  2/0/0≠0/0/0 维持；bottom-i1 两板 R20B-003/R20B-006 经 (iii-a) 间隙支
  负责任报告路径产生=r14–r19 bottom 侧首现非弃权 courtyard 旗）⇒
  reject_guards 支（支序最高；G2 维持 R19=0→R20=0）；(r) M1 ≥0.771429
  未命中；(m) M1 <0.771429 虽真但支序 reject 在前——字母=reject——
  组合出局（early_stop_rule.guard_failure_exit；处置=冻结
  combination_decision_rule.iii_non_additive_fallback 采最优单轴 r19 配
  置）；描述性结论、非因果证明。
G1 分岔记录（关键机制观察，如实单列不凌驾字母）：G1 字面破坏与机制方向
并存的分岔——守门设计针对的是 courtyard 混淆弃权（G1=bottom courtyard
非弃权 0/0/0 维持=「不得把 courtyard 近邻形态改判为非弃权」的反向风险
守门），而本轮触发源=负责任报告（(iii-a) 间隙支把弃权引导为有据报告：
可辨认间隙带→视觉贴近→按 courtyard_crowding 报告）——条款按设计工作
（把不可分辨弃权引导到有据判定=判据改良方向命中）但按预注册字母仍=
reject（守门字面 0/0/0 破坏）；此张力单列为判据设计的机制教训（守门
条件与判据改良的方向冲突）；如需区分「混淆弃权」与「有据报告」两类
bottom courtyard 非弃权旗，须后续轮次 prep-record 预注册修订守门操作化
定义、不得事后改判本轮。
机制观察/度量教训单列：援引分记（旗级 location_evidence 含「§5B」=0 旗、
含「(iii-a)」=0 旗、含「分支(」=0 旗=旗级零字面援引；notes 级含「§5B」
=4/12 派次、含「(iii-a)」=4/12 派次=援引习惯集中在 notes 层；双基线
对照 r18 §5B 派次级 1/12、r19 (iii-a) notes 级 10/12 在案）；(iii-a)
逐旗落支=间隙支 2+侵入支 4+残余弃权 7（间隙支 notes 级判正常路径 2 派
次）；rubric 族计数 contact 2/existence_blackdot 6/existence_other 10
（r13–r16 132 条弃权旗重放对拍逐一相等；contact 链 8/15/5/10；黑点
6=r18 13 与 r19 4 双基线间；存在性其他 10 vs r18 12/r19 14）+黑点转非
弃权旗 6 条（全 bottom）+黑点判正常派次 4+top 弃权构成分型=接触性 4+
存在性 9+层归属其他 1。实验对照账（axis-plan benefit_metrics 口径）：
(M1,M2,M3,M4)=(0.636364, 0.285714, 6, 0.25)——五轮并列（r16 基线
0.771429/0.857143/12/0.261904、r17 轴1 0.88/0.75/8/0.333333、r18 轴2
0.645161/0.684211/13/0.277778、r19 轴3 0.461538/0.571429/4/0.211111、
r20 组合 0.636364/0.285714/6/0.25）；r20=G1 破坏不入排序（资格门剔除）；
按冻结 comparison_rule 排序（不含 r20）=r19 轴3 第一、r18 第二、r16 参
照行第三、r17 末位；显著收益定义描述层命中（M1 绝对降幅 0.135065≥0.10）。
阶段2 收束：combination_decision_rule 执行完毕（supported 未落、
marginal 未落、reject 落）⇒三轴实验最终结论=收益最大配置=轴3 单变量
（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4，
按 iv_final_selection 全部已测配置中排序最优者）；R21 不做（early_stop
strong_single_axis_shortcut 命中→组合轮仅一个+三轴不全正（轴1 r17
M1=0.88 劣于基线）+本轮 G1 破坏排除追加）。下一候选建议（如实单列，
供主审/用户决策）：r19 配置的 M4=0.211111 差 0.011111 未过 supported
门 0.20——可选后续=同指引重复轮（r16 先例）收敛归因，或接受 marginal
收益收束训练环转入收敛评估；由用户拍板。GT 双口径全轮零命中
（union=agreement=0/13，candidate 对空集；r19 唯一命中 R19T-009 未再现
=单实例命中不稳定如实）；联合门 joint not_met、连续=0；
in_calibrated_range 恒 False；12 格全部≥1 旗（零旗标口径未触发）。

生成器纪律（s69/s72 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-09"；
- 防覆写护栏：round20-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round20-dev-record.json 一件（s74 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s75_calibration_r20_devrecord.py   （仓库根执行）
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

DECLARED_DATE = "2026-09-09"
ROUND_ID = "2026-09-09-r20"
ROUND_LABEL = "r20"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round20_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_PREP_R20 = "out/v3-tl2/calibration/r20-prep-record.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_GUIDANCE_R20 = "out/v3-tl2/calibration/observation-guidance-r20.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_OUT = "out/v3-tl2/calibration/round20-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 引用件哈希清单（简报在案锚；逐件 live 实测比对，fail-closed）
REFERENCE_HASH_EXPECTED = {
    "run_r20": (REL_RUN_R20, "6573a59a"),
    "guidance_r20": (REL_GUIDANCE_R20, "9cdac9ed"),
    "prep_r20": (REL_PREP_R20, "e29ee2a3"),
    "axis_experiment_plan": (REL_AXIS_PLAN, "b6ec6467"),
    "run_r19": (REL_RUN_R19, "e5755a11"),
    "dev_r19": (REL_DEV_R19, "0e2fdd69"),
}

# 主通道 ordering 三分判据实测锚（写盘前 fail-closed 与 run-r20 盘上值
# 逐一核对）
EXPECT_TOP_ABSTAIN_R20 = 14
EXPECT_TOP_FLAGS_R20 = 22
EXPECT_TOP_RATE_R20 = 0.636364
EXPECT_BOTTOM_ABSTAIN_R20 = 4
EXPECT_BOTTOM_FLAGS_R20 = 14
EXPECT_BOTTOM_RATE_R20 = 0.285714
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_CONTACT_R20 = 2
EXPECT_CONTACT_R16_BASELINE = 10
EXPECT_CONTACT_CHAIN_R13_R16 = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
# 实验对照账（axis-experiment-plan benefit_metrics 口径；M3 槽位=冻结件
# 黑点族 rubric 口径、本轮实测 6；contact=2 另列不占 M3 槽位）
EXPECT_M1 = 0.636364
EXPECT_M2 = 0.285714
EXPECT_M3 = 6
EXPECT_M4 = 0.25
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17/r18/r19 已测行（dev-r19 在案行装载；排序现状对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
EXPECT_R18_MEASURED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                       "M4": 0.277778}
EXPECT_R19_MEASURED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                       "M4": 0.211111}
EXPECT_M1_ABSOLUTE_DROP = 0.135065
EXPECT_R19_DROP_REFERENCE = 0.309891
EXPECT_R18_DROP_REFERENCE = 0.126268
# 判据 (r) 支 M1 阈值（r16 基线 6 位定点；与 s74 REJECT_M1_MIN_6DP 同锚）
REJECT_M1_MIN_6DP = 771_429
# early_stop.strong_single_axis_shortcut 阈值（冻结件原文 0.60；6 位定点）
STRONG_SHORTCUT_M1_MAX_6DP = 600_000
EXPECT_COUNTS = {"top-i1": 8, "top-i2": 8, "top-i3": 6,
                 "bottom-i1": 6, "bottom-i2": 4, "bottom-i3": 4}
EXPECT_ABSTAIN = {"top-i1": 4, "top-i2": 6, "top-i3": 4,
                  "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 4}
EXPECT_RATES = {"top-i1": 0.5, "top-i2": 0.75, "top-i3": 0.666667,
                "bottom-i1": 0.0, "bottom-i2": 0.0, "bottom-i3": 1.0}
EXPECT_TYPE_COUNTS = {"contact": 4, "existence": 9, "other_layer": 1}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 0, "bottom-i2": 0,
                                "bottom-i3": 4, "top-i1": 2,
                                "top-i2": 0, "top-i3": 0}
EXPECT_RUBRIC_COUNTS = {"contact": 2, "existence_blackdot": 6,
                        "existence_other": 10, "other": 0,
                        "semantic_confusion": 0}
EXPECT_BRANCH_COUNTS = {"branch1_gap_report": 2,
                        "branch2_intrusion_report": 4,
                        "branch3_residual_abstain": 7}
EXPECT_ZERO_FLAG_PARTS = []
EXPECT_G1_R20 = {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_G1_BASELINE = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_GUIDANCE_BYTE_SIZE = {"base": 21435, "delta": 1458, "derived": 22893}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s75-cal-r20-devrecord] FAIL: {msg}")


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
# 阶段2 收束冻结规则操作化（纯函数；构造可测，轴序变更时结论跟随变化）
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


def stage2_final_selection(axis_rows: dict, guards: dict,
                           var_counts: dict) -> dict:
    """阶段2 最终结论（纯函数；冻结 combination_decision_rule.
    iv_final_selection 原文操作化）：全部已测配置中「过资格门（G1/G2
    均满足）」者按 comparison_rule 字典序排序，排序最优者为收益最大配
    置；同分（四键全等）时取变量更少者（简约优先）。

    axis_rows={config_key: {M1,M2,M3,M4} 或四元组}；guards={config_key:
    bool}（G1/G2 破坏轮=False→不入排序，per eligibility_gate）；var_counts=
    {config_key: 变量数}（简约优先 tie-break）。过守门配置为空→
    ValueError。返回 {"eligible_sorted": [...], "tied_best": [...],
    "final_config": key, "final_row": {...}}。"""
    eligible = [k for k in axis_rows if guards.get(k) is True]
    if not eligible:
        raise ValueError("过资格门（G1/G2 均满足）配置为空——最终选择前提"
                         "不成立（fail-closed）")
    ranked = sorted(eligible, key=lambda k: comparison_sort_key(axis_rows[k]))
    best_key = comparison_sort_key(axis_rows[ranked[0]])
    tied = [k for k in ranked
            if comparison_sort_key(axis_rows[k]) == best_key]
    final = min(tied, key=lambda k: var_counts[k])
    return {"eligible_sorted": ranked, "tied_best": tied,
            "final_config": final, "final_row": _row4(axis_rows[final])}


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


def _verify_facts(run: dict, run16: dict, prep: dict, dev19: dict,
                  typology: dict, guidance_sha: str, axis_sha: str,
                  typology_sha: str) -> None:
    # ---- run-r20 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r20":
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
    if ht["hypothesis_id"] != "axis-plan-r20-combo-additivity":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "reject":
        _fail("verdict != reject")
    if "唯一正式裁决" not in ht["verdict_text"] or \
            "只描述不断言" not in ht["verdict_text"]:
        _fail("verdict_text 应含「唯一正式裁决/只描述不断言」")
    m = ht["measurement"]
    if (m["crit_supported_ordering_not_worse_than_r19"] is not False
            or m["crit_reject_m1_ge_0_771429"] is not False
            or m["crit_reject_guards_broken"] is not True
            or m["crit_marginal_m1_lt_0_771429"] is not True):
        _fail("三分判据布尔不符（ordering 不劣于=False；M1 ≥0.771429="
              "False；G 破坏=True；M1 <0.771429=True）")
    if not m["letter_branch"].startswith("(r)"):
        _fail("落支应为 (r) 支")
    if "G1/G2 任一破坏" not in m["letter_branch"] or \
            "采最优单轴 r19" not in m["letter_branch"]:
        _fail("落支文本应含 G1/G2 破坏+采最优单轴 r19 处置")
    if m["verdict"] != "reject":
        _fail("measurement.verdict != reject")
    # 本轮实测（top 14/22、bottom 4/14）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R20, EXPECT_TOP_ABSTAIN_R20):
        _fail("top 聚合不符（14/22）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R20, EXPECT_BOTTOM_ABSTAIN_R20):
        _fail("bottom 聚合不符（4/14）")
    if m["top_abstain_rate_r20"] != EXPECT_TOP_RATE_R20 or \
            m["bottom_side_observation"]["bottom_abstain_rate_r20"] != \
            EXPECT_BOTTOM_RATE_R20:
        _fail("聚合弃权率不符")
    if "14/22" not in m["top_abstain_rate_r20_arithmetic"] or \
            "4/14" not in m["bottom_side_observation"][
                "bottom_abstain_rate_r20_arithmetic"]:
        _fail("聚合算式文本不符")
    if m["bottom_side_observation"]["bottom_rate_direction_vs_r16"] != \
            "improved":
        _fail("bottom 侧观察方向应为 improved")
    # 整数交叉相乘复核（避免浮点）：ordering 不劣于=False（M1 首键
    # 636364>461538）；(r) M1 门 14×10^6 < 771429×22（未中）；G1 破坏
    # （2/0/0）；显著收益 (27/35−14/22)≥0.10 描述层命中
    if (636_364, 285_714, 6, 250_000) <= (461_538, 571_429, 4, 211_111):
        _fail("ordering 复核不符（r20 应劣于 r19）")
    if at * 1_000_000 >= REJECT_M1_MIN_6DP * ft:
        _fail("(r) M1 门复核不符（应 14×10^6<771429×22=未中）")
    if (27 * 22 - 14 * 35) * 1_000_000 < 100_000 * 35 * 22:
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
    # contact 族（另列主度量对照）：实测 2、基线 10、链重放 8/15/5/10
    if m["contact_family_abstain_flags_rubric_r20"] != EXPECT_CONTACT_R20 \
            or m["contact_r16_baseline_registered"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            m["contact_r16_baseline_live_replay"] != \
            EXPECT_CONTACT_CHAIN_R13_R16:
        _fail("contact 实测/基线/链重放不符（2、10、8/15/5/10）")
    if "top 2+bottom 0" not in m["contact_arithmetic_note"]:
        _fail("contact 分视角算式不符（top 2+bottom 0）")
    # M4 与 axis-plan 登记基线四键交叉核对
    if m["m4_top_rate_range_r20"] != EXPECT_M4 or \
            run["view_layer"]["top"]["abstain_rate_range"] != EXPECT_M4:
        _fail("M4=top 极差不符（0.25）")
    if m["baseline_cross_check"]["axis_plan_r16_baseline_M1_M2_M3_M4"] != \
            EXPECT_R16_BASELINE_M1_M2_M3_M4:
        _fail("axis-plan r16 基线四键不符")
    # 守门通道（G1 破坏=reject_guards 支；G2 维持；early_stop 触发）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not False or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not False or \
            gc["g2_geometry_gate_r19"] != 0 or \
            gc["g2_geometry_gate_r20"] != 0:
        _fail("守门通道不符（G1 破坏、G2 0→0 维持）")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["guards_ok"] is not False or \
            g12["axis_early_stop_triggered"] is not True or \
            g12["g1_bottom_courtyard_non_abstain_r20"] != EXPECT_G1_R20 or \
            g12["g1_r16_baseline_live"] != EXPECT_G1_BASELINE:
        _fail("守门 G1 实测不符（2/0/0 vs 基线 0/0/0；early_stop 触发）")
    # GT 双口径全轮零命中：union 0/13、agreement 0/13、分母 13
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (0, 0, 13):
        _fail("双口径不符（union=agreement=0/13）")
    if dual["union"]["gt_ids"] != [] or \
            dual["union"]["gt_recall_union"] != 0.0:
        _fail("union 零命中不符（candidate 对空集）")
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
    # 零旗标派次=0（12 格全部≥1 旗；item 5 口径未触发）
    if run["reader"]["zero_flag_parts"]["parts"] != EXPECT_ZERO_FLAG_PARTS:
        _fail("零旗标派次不符（应为空）")
    # 代表配置与门（top-i1+bottom-i2，双 tie=旗数中位并列如实）
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (12, 4, 0.333333, 0.0, 0.0):
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
            "tie"] is not True or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not True:
        _fail("代表配置 tie 记录不符（双 tie）")
    # instrument_change.changed=false（预注册）与 prep 一致
    if run["instrument_change"]["changed"] is not False or \
            prep["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 应为 false")
    if prep["no_instrument_change"] is not True:
        _fail("prep no_instrument_change 应为 true")
    if len(run["instrument_change"]["changed_variables_registered"]) != 1 or \
            len(prep["changed_variables"]) != 1:
        _fail("变更变量登记不符（run 1 件、prep 1 件=单一复合变量）")
    if run["instrument_change"]["changed_variables_registered"][0][
            "id"] != "guidance-combo-s5b-plus-s4-iiia-union":
        _fail("变更变量 id 不符（§5B+§4(iii-a) 并集单一复合变量）")
    if run["instrument_change"]["axis_id"] != \
            "A3_criterion_contact_clarification+" \
            "A2_blackdot_instrument_annotation":
        _fail("组合轮轴声明不符（轴3+轴2）")
    # 机制观察：援引分记、落支、黑点族、top 分型、rubric 族
    mo = ht["mechanism_observation"]
    cc = mo["criterion_citation_observation"]
    ccounts = cc["citation_counts"]
    if ccounts["flag_level_s5b_literal"] != 0 or \
            ccounts["flag_level_iiia_literal"] != 0 or \
            ccounts["flag_level_branch_literal"] != 0:
        _fail("旗级援引应为全零（§5B/(iii-a)/分支( 三集合全空）")
    if ccounts["notes_level_s5b"] != 4 or ccounts["notes_level_iiia"] != 4:
        _fail("notes 级援引不符（§5B=4/12、(iii-a)=4/12）")
    if cc["branch_counts_flag_level"] != EXPECT_BRANCH_COUNTS or \
            cc["branch1_notes_level_dispatches"] != 2:
        _fail("(iii-a) 落支不符（间隙 2+侵入 4+残余弃权 7；notes 级 2）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 6:
        _fail("黑点族 6 旗全弃权不符")
    if bdt["blackdot_to_non_abstain_count"] != 6 or \
            len(bdt["black_dot_non_abstain_flags"]) != 6:
        _fail("黑点转非弃权旗 6 条不符")
    if bdt["judged_normal_dispatches"]["count"] != 4:
        _fail("黑点判正常派次 4 不符")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS:
        _fail("rubric 族计数不符（2/6/10/0/0）")
    ty = mo["top_abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            ty["top_abstain_flags_total"] != 14 or len(ty["rows"]) != 14 or \
            ty["top_abstain_rate_range"] != EXPECT_M4:
        _fail("top 弃权构成分型不符（4/9/1、14 旗、极差 0.25）")
    if ty["r16_reference_counts"] != {"contact": 11, "existence": 15,
                                      "other_layer": 1} or \
            ty["r19_reference_counts_live"] != {"contact": 5,
                                                "existence": 13,
                                                "other_layer": 0}:
        _fail("r16/r19 分型参照不符")
    # 实验对照账：五元组/五轮并列/排序（资格门剔除 r20）/显著收益/阶段2
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r20_measured"]["M1"] != EXPECT_M1 or \
            ecl["r20_measured"]["M2"] != EXPECT_M2 or \
            ecl["r20_measured"]["M3"] != EXPECT_M3 or \
            ecl["r20_measured"]["M4"] != EXPECT_M4 or \
            ecl["r20_measured"]["M1_arithmetic"] != "14/22" or \
            ecl["r20_measured"]["M2_arithmetic"] != "4/14" or \
            ecl["r20_measured"]["contact_family_abstain_flags_rubric"] != 2 \
            or ecl["r20_measured"]["contact_family_by_view"] != \
            {"bottom": 0, "top": 2} or \
            ecl["r20_measured"]["existence_other_family"] != 10:
        _fail("实验对照账四元组/另列键不符")
    if ecl["r17_axis1_row"] != EXPECT_R17_MEASURED or \
            ecl["r18_axis2_row"] != EXPECT_R18_MEASURED or \
            ecl["r19_axis3_row"] != EXPECT_R19_MEASURED:
        _fail("r17/r18/r19 对照行不符")
    if ecl["r16_baseline_registered"]["M1"] != 0.771429 or \
            ecl["r16_baseline_registered"]["M4"] != 0.261904:
        _fail("r16 基线行不符")
    rk = ecl["ranking_by_comparison_rule"]
    if rk["ranking_order_best_first"] != ["r19_axis3", "r18_axis2",
                                          "r16_baseline", "r17_axis1"] or \
            rk["r20_eligibility"] is not False or \
            rk["rows_registered"]["r20_combo"] != \
            {"M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25} or \
            rk["rows_registered"]["r19_axis3"] != EXPECT_R19_MEASURED:
        _fail("comparison_rule 排序不符（r20 资格门剔除；r19 第一）")
    sb = ecl["significant_benefit_vs_r16"]
    if sb["met"] is not True or \
            sb["r20_m1_absolute_drop"] != EXPECT_M1_ABSOLUTE_DROP or \
            sb["r19_drop_reference"] != EXPECT_R19_DROP_REFERENCE or \
            sb["r18_drop_reference"] != EXPECT_R18_DROP_REFERENCE:
        _fail("显著收益不符（0.135065≥0.10；r19 参照 0.309891）")
    sc = ecl["stage2_conclusion"]
    if sc["verdict"] != "reject" or \
            sc["r21_full_combination_trigger_dev_r19"] is not False or \
            "采最优单轴" not in sc["conclusion"] or \
            "R21 不做" not in sc["conclusion"] or \
            "r19_axis3" not in sc["conclusion"]:
        _fail("阶段2 结论不符（组合劣化采最优单轴 r19、R21 不做）")
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
    # 指引机械变换派生锚（9cdac9ed 实测=r19 基座 8633bda5+§5B 自 r18
    # cadcb8f3 逐字转录插入）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "mechanical_transform_derive" or \
            gr["derived"] != "observation-guidance-r20.md":
        _fail("guidance_reuse 机械变换派生声明不符")
    if gr["base_sha256"][:8] != "8633bda5":
        _fail("r19 基座锚不符")
    if gr["s5b_source_sha256"][:8] != "cadcb8f3" or \
            gr["s5b_segment_content_sha256"][:8] != "19ecdb42":
        _fail("§5B 转录源/内容跨代哈希锚不符")
    if gr["derived_sha256"] != guidance_sha or \
            guidance_sha != _sha(REL_GUIDANCE_R20):
        _fail("r20 指引实测 sha 与 9cdac9ed 锚不符")
    if gr["byte_size"] != EXPECT_GUIDANCE_BYTE_SIZE:
        _fail(f"指引 byte_size 不符（{EXPECT_GUIDANCE_BYTE_SIZE}）")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R20):
        _fail("prep-record sha 实测与登记不符")
    if gr["chain_anchors"]["axis_experiment_plan_frozen"]["sha256"] != \
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
    if "两轴变更同时施加" not in cdr["i_stage2_combo_pair"] or \
            "三轴均各自正收益" not in cdr["ii_full_combination"] or \
            "采最优单轴、不再追加" not in cdr["iii_non_additive_fallback"] \
            or "简约优先" not in cdr["iv_final_selection"] or \
            "不预写结果" not in cdr["preregistration_note"]:
        _fail("combination_decision_rule 冻结原文锚不符")
    if "0.60" not in plan["early_stop_rule"]["strong_single_axis_shortcut"]:
        _fail("early_stop strong_single_axis_shortcut 锚不符")
    if "出局" not in plan["early_stop_rule"]["guard_failure_exit"]:
        _fail("early_stop guard_failure_exit 锚不符")
    if typology["matrix"]["round_totals"]["r16"]["families"]["contact"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            typology_sha != _sha(REL_TYPOLOGY):
        _fail("typology contact 基线/实测 sha 不符（r16=10）")
    # dev-r19 先验链锚（实测）与 r16–r19 已测行+组合决策建议核对
    if dev19["round_id"] != "2026-09-09-r19" or \
            dev19["hypothesis_test_i"]["verdict"] != "marginal":
        _fail("r19 dev-record 先验件常量不符")
    rows19 = dev19["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    if rows19["r16_baseline"] != {"M1": 0.771429, "M2": 0.857143, "M3": 12,
                                  "M4": 0.261904} or \
            rows19["r17_axis1"] != EXPECT_R17_MEASURED or \
            rows19["r18_axis2"] != EXPECT_R18_MEASURED or \
            rows19["r19_axis3"] != EXPECT_R19_MEASURED:
        _fail("r16–r19 已测行（dev-r19 装载）不符")
    cda19 = dev19["combination_decision_application"]
    if cda19["r20_recommendation"]["axes"] != ["r19_axis3", "r18_axis2"] or \
            cda19["r21_full_combination_trigger"]["met"] is not False or \
            cda19["early_stop_shortcut"]["triggered"] is not True:
        _fail("dev-r19 组合决策应用与在案核对不符")
    trend_rows_prior = dev19["joint_evaluation_trend"]["by_round"]
    if [r["round"] for r in trend_rows_prior] != [
            "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "r16", "r17", "r18", "r19"]:
        _fail("趋势历史行（dev-r19）不符")


def build_dev_record() -> dict:
    """构建 round20-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R20)
    run16 = _json_load(REL_RUN_R16)
    prep = _json_load(REL_PREP_R20)
    dev19 = _json_load(REL_DEV_R19)
    typology = _json_load(REL_TYPOLOGY)
    guidance_sha = _sha(REL_GUIDANCE_R20)
    axis_sha = _sha(REL_AXIS_PLAN)
    typology_sha = _sha(REL_TYPOLOGY)
    _verify_facts(run, run16, prep, dev19, typology, guidance_sha,
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

    run20_sha = _sha(REL_RUN_R20)

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

    # 联合评价趋势：r5–r19 行=round19-dev-record 在案行（冻结转录）；
    # r20 行=本轮 run 实测
    trend_rows = list(dev19["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17",
                                            "r18", "r19"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r20",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R20, "sha256": run20_sha},
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
            "全旗标合计口径仅作附记（18/36=0.5，非弃权 18+弃权 18）；"
            "本轮预注册主通道=ordering 三分判据（(r) G1 破坏→reject——"
            "(s) ordering 不劣于 r19=False、(r) M1 ≥0.771429 未中；"
            "bottom 全旗聚合弃权率 4/14=0.285714 为侧观察度量[M2，improved "
            "方向]）；实例层/视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 1.0=1.0−0.0（bottom-i1/i2/i3=0.0/0.0/"
                     "1.0；12 格全部≥1 旗、中位数=0.0=排序后第 2）；top "
                     "极差 0.25=0.75−0.5（top-i1/i2/i3=0.5/0.75/0.666667"
                     "）；本轮零旗标派次=0（对照 r19 的 2 格 bottom-i3 两"
                     "板、r18 的 0 格）——零旗格 view_check=not_applicable"
                     " 口径本轮未触发、top/bottom 弃权率全部有定义"),
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
                 "（4 格×3 实例，instance_serial_two_wave 两波次串行保"
                 "序）；R20T/R20B 前缀随 r20 指引 §6 落盘固化（机械替换"
                 "无需派发层覆盖）；flag_id 编号行为=6 实例全部同实例跨板"
                 "连续（与 prep-record naming「同实例跨板连续」声明全部相"
                 "符；对照 r19 混合行为如实登记）=读者实例输出行为差异如"
                 "实登记（编排侧按 (state, flag_id) 限定，跨板同号不混"
                 "淆）；本轮无派发操作事故（对照 r19 wave-3 重派事故如实"
                 "单列先例）；v1.2 工具规约沿用 12/12 派次自述合规与输出"
                 "格式披露（12 件缩进格式冻结原始判读件、零改动直读）如"
                 "实登记为混杂因素披露，不作废"),
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
            "measurement_design item 4；top 旗数中位 8 由 top-i1/top-i2 "
            "并列、bottom 旗数中位 4 由 bottom-i2/bottom-i3 并列——双 "
            "tie、按先序规则取 top-i1/bottom-i2 如实登记）"),
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

    # 阶段2 收束（冻结 combination_decision_rule + early_stop_rule
    # 操作化；纯函数可构造复算；不预写结果）
    axis_rows = {
        "r16_baseline": {"M1": 0.771429, "M2": 0.857143, "M3": 12,
                         "M4": 0.261904},
        "r17_axis1": dict(EXPECT_R17_MEASURED),
        "r18_axis2": dict(EXPECT_R18_MEASURED),
        "r19_axis3": dict(EXPECT_R19_MEASURED),
        "r20_combo": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                      "M3": EXPECT_M3, "M4": EXPECT_M4},
    }
    guards = {"r16_baseline": True, "r17_axis1": True, "r18_axis2": True,
              "r19_axis3": True, "r20_combo": False}
    var_counts = {"r16_baseline": 0, "r17_axis1": 1, "r18_axis2": 1,
                  "r19_axis3": 1, "r20_combo": 2}
    sel = stage2_final_selection(axis_rows, guards, var_counts)
    if sel["final_config"] != "r19_axis3" or \
            sel["eligible_sorted"] != ["r19_axis3", "r18_axis2",
                                       "r16_baseline", "r17_axis1"]:
        _fail("最终选择不符（应为 r19_axis3；r20 资格门剔除不入排序）")
    r21_met = full_combination_trigger({k: axis_rows[k] for k in
                                        ("r17_axis1", "r18_axis2",
                                         "r19_axis3")}, 0.771429)
    if r21_met is not False:
        _fail("R21 全组合触发核对不符（轴1 M1=0.88 负向→不触发）")
    if strong_single_axis_shortcut(EXPECT_R19_MEASURED["M1"]) is not True:
        _fail("strong_single_axis_shortcut 核对不符（0.461538≤0.60→命中）")
    stage2_closure = {
        "combination_decision_rule_execution": (
            "执行完毕（阶段2 唯一组合轮 R20 裁决落定：supported 未落"
            "（ordering 不劣于 r19=False）→marginal 未落（支序 reject "
            "在前：G1 破坏）→reject 落（reject_guards 支）——三分判据全支"
            "走毕；per ii_full_combination 前提「R20 收益 ≥ 最优单轴」未"
            "命中→不追加全组合；per iii_non_additive_fallback 采最优单轴"
            "；per iv_final_selection 全部已测配置中裁定收益最大配置）"),
        "early_stop": {
            "guard_failure_exit_triggered": True,
            "note": ("本轮 G1 破坏→r20 组合出局（退出本实验后续组合与排"
                     "序；「出局」仅指退出本实验后续组合与排序，run/"
                     "dev-record 照常落盘、字母裁决照常）"),
            "rule_quote": plan["early_stop_rule"]["guard_failure_exit"],
            "strong_single_axis_shortcut_triggered": True,
        },
        "final_conclusion": (
            "三轴实验最终结论=收益最大配置=轴3 单变量（guidance-r19："
            "M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4；按冻结 "
            "iv_final_selection「最终「收益最大配置」=全部已测配置（本实"
            "验 R17–R21 各配置）中 comparison_rule 排序最优者，作为后续"
            "迭代基座；同分（四键全等）时取变量更少者（简约优先）」在全"
            "部已测配置中裁定=r19_axis3——r20 组合=G1 破坏经资格门剔除"
            "不入排序、ordering 字典序亦劣于 r19（M1 首键 0.636364>"
            "0.461538）"),
        "final_selection_application": {
            "eligible_sorted": sel["eligible_sorted"],
            "final_config": sel["final_config"],
            "final_row": sel["final_row"],
            "note": ("stage2_final_selection 纯函数应用（axis_rows 五行"
                     "装载=run-r20 对照账+dev-r19 measured_rows 交叉核对；"
                     "guards r20=False=G1 破坏资格门剔除；与 run-r20 "
                     "ranking_by_comparison_rule 逐一相等 fail-closed）"),
            "tied_best": sel["tied_best"],
            "var_counts": dict(var_counts),
        },
        "r21": ("R21 不做（early_stop strong_single_axis_shortcut 命中→"
                "阶段2 仅一个组合轮+三轴不全正（轴1 r17 M1=0.88 劣于基线 "
                "0.771429=负向，per_axis_positive.r17_axis1=False）+本轮 "
                "G1 破坏排除追加——三重独立依据）"),
        "role": ("阶段2 收束应用（development 域描述性边界工具、非门、无"
                 "字母语义、不凌驾 APR-0011 与阈值；纯函数操作化、构造可"
                 "测；规则文本引用冻结原文）"),
        "rule_sources": ("axis-experiment-plan-r17-r20.json"
                         " combination_decision_rule.ii_full_combination/"
                         "iii_non_additive_fallback/iv_final_selection + "
                         "early_stop_rule.guard_failure_exit/strong_single_"
                         "axis_shortcut（冻结原文；FROZEN=先于 R17–R21 任何"
                         "实验轮盲读冻结）"),
        "verdict_chain": {
            "marginal": "未落（支序 reject 在前）",
            "reject": "落（reject_guards：G1 破坏）",
            "supported": "未落（ordering 不劣于 r19=False）",
        },
    }

    combination_decision_application = {
        "final_selection_application":
            stage2_closure["final_selection_application"],
        "inputs": {
            "axis_rows": {k: dict(v) for k, v in axis_rows.items()},
            "guards": dict(guards),
            "guards_note": ("r16=基线参照行（非轴配置、guards 恒 True 仅"
                            "入排序对照）；r17/r18=dev-r18 在案注记「两轮 "
                            "G1/G2 均满足」装载；r19=run-r19 guards 在案；"
                            "r20=本轮 G1 破坏→False（资格门剔除）"),
            "ranking_rule": plan["comparison_rule"]["ordering"],
            "r16_baseline_m1": 0.771429,
            "var_counts_note": ("变量数（简约优先 tie-break 用）：基线行 "
                                "0、单轴轮各 1、组合轮 2——本轮无同分、"
                                "tie-break 未触发（登记备查）"),
        },
        "next_candidate_suggestion": {
            "context": ("阶段2 已收束（收益最大配置=轴3 单变量 guidance-"
                        "r19）；r19 配置的 M4=0.211111 差 0.011111 未过 "
                        "supported 门 0.20（(s) 支唯一未达项；字母="
                        "marginal=部分收益在案）——如实单列、供主审/用户"
                        "决策；本包不预写决策"),
            "decision_authority": "由用户拍板（本包只列选项、不预写决策）",
            "options": [
                {
                    "motivation": ("r19 M4=0.211111 与 supported 门 0.20 "
                                   "差 0.011111；单轮 n=3、跨轮实例群漂移"
                                   "混杂 0.09064（r15→r16 纯重抽在案参照）"
                                   "——重复轮可区分真实收益与漂移、收敛归"
                                   "因（部分重复≠独立重复、验证力度如实）"),
                    "option": ("同指引重复轮（r16 先例）：对 r19 配置"
                               "（guidance-r19）做同指引重复轮收敛归因"
                               "——r15→r16 同指引重复轮为在案先例（渲染"
                               "零变更、指引零变更、仅实例重抽）"),
                    "preregistration_required": True,
                },
                {
                    "motivation": ("轴3 marginal（部分收益）如实登记、轴3 "
                                   "不判定为胜出在案；三轴实验已收束（收益"
                                   "最大配置=r19_axis3）；开发线收敛（连续 "
                                   "达标=0、正式采纳门槛未达）——转入收敛"
                                   "评估（含留出集时机=须用户拍板在案）"),
                    "option": ("接受 marginal 收益收束训练环、转入收敛评估"
                               "（不再追加迭代轮）"),
                    "preregistration_required": False,
                },
            ],
            "status": ("下一候选建议（非冻结规则输出——combination_decision_"
                       "rule 已执行完毕、阶段2 收束后无预注册的下一轮规则"
                       "位；本节为 dev-record 如实登记的选项清单）"),
        },
        "role": ("冻结 combination_decision_rule/early_stop_rule 的 R20 后"
                 "应用+阶段2 收束记录（development 域描述性边界工具、非门、"
                 "无字母语义、不凌驾 APR-0011 与阈值）"),
        "r21_full_combination_trigger": {
            "check": ("三轴均各自正收益（各自 M1 不劣于 r16 基线 0.771429）"
                      "=否：轴1 r17 M1=0.88 劣于基线（负向）——触发条件不"
                      "成立；轴2/轴3 M1 优于基线；与 dev-r19 在案核对一致"
                      "（r21_full_combination_trigger.met=False）"),
            "met": False,
            "per_axis_positive": {"r17_axis1": False,
                                  "r18_axis2": True,
                                  "r19_axis3": True},
            "rule_quote": plan["combination_decision_rule"][
                "ii_full_combination"],
        },
        "stage2_closure": stage2_closure,
        "status": ("阶段2 收束=combination_decision_rule 执行完毕（"
                   "supported/marginal/reject 全支走毕、reject 落）；收益"
                   "最大配置=轴3 单变量 r19_axis3；R21 不做；下一候选选项"
                   "如实单列供用户拍板、不预写结论"),
    }

    # G1 分岔记录（关键机制观察，如实单列不凌驾字母裁决）
    g1_bifurcation_record = {
        "bifurcation": (
            "条款按设计工作（把不可分辨弃权引导到有据判定=判据改良方向命"
            "中）但按预注册字母仍=reject（守门字面 0/0/0 破坏经 "
            "reject_guards 支）——守门条件与判据改良的方向冲突在单轮数据"
            "中同时显形"),
        "counts": {
            "bottom_courtyard_flags_total_r20": 2,
            "bottom_courtyard_non_abstain_r20": dict(EXPECT_G1_R20),
            "g1_baseline_r16_live": dict(EXPECT_G1_BASELINE),
            "non_abstain_courtyard_flag_ids": ["R20B-003", "R20B-006"],
            "trigger_flags": ("bottom-i1 两板（applied R20B-003+prep1 "
                              "R20B-006）经 (iii-a) 间隙支（branch1_gap_"
                              "report）负责任报告路径产生"),
        },
        "declared_date": DECLARED_DATE,
        "mechanism_lesson": (
            "判据设计的机制教训（单列）：守门 G1 预注册于判据改良之前，操"
            "作化定义=「bottom courtyard 非弃权 0/0/0 维持」不区分「混淆"
            "弃权转非弃权」（守门设计目标）与「有据报告转非弃权」（判据改"
            "良方向）；当两者指向相反方向时，预注册字母裁决优先"
            "（reject_guards）、改良方向只入机制观察——后续轮次如要区分两"
            "类 bottom courtyard 非弃权旗，须先走 prep-record 预注册修订"
            "守门操作化定义（先于该轮盲读冻结）、不得事后改判本轮"),
        "observation": (
            "G1 字面破坏与机制方向并存的分岔：守门 G1 的设计针对的是 "
            "courtyard 混淆弃权（G1=bottom courtyard 非弃权 0/0/0 维持"
            "=「不得把 courtyard 近邻形态改判为非弃权」的反向风险守门，"
            "对照 r15–r19 全部 0/0/0）；而本轮触发源=负责任报告——(iii-a) "
            "间隙支把弃权引导为有据报告（可辨认间隙带→视觉贴近→按 "
            "courtyard_crowding 负责任报告，bottom-i1 两板 R20B-003/"
            "R20B-006=r14–r19 bottom 侧首现非弃权 courtyard 旗）"),
        "role": ("机制教训单列：不凌驾、不改写字母裁决（reject 维持唯一"
                 "正式裁决）；不进任何度量；描述性记录、非因果证明"),
        "trigger_source": ("负责任报告（(iii-a) 把弃权引导为有据报告）——"
                           "非 yard 混淆弃权被错误改判"),
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 6 派次全部旗标中弃权旗占比"
                "（6 位小数；本轮实测 14/22）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 4/14）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径=分型件 round_totals "
                "{r}.families.existence_blackdot；本轮实测 6、全弃权；M3 "
                "槽位定义维持冻结件黑点口径——contact=2 另列不占槽=判据侧"
                "对照账纪律延续）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差=max−min（本轮实测 0.75−0.5=0.25）",
            "contact_family_abstain_flags_rubric":
                "contact 族弃权旗数（全视，分型件 rubric 口径；本轮实测 2"
                "[top 2+bottom 0]、r16 基线 10、r13–r16 链 8/15/5/10 在"
                "案——对照账另列、不占 M3 槽位）",
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
                "r19_axis3": dict(EXPECT_R19_MEASURED),
                "r20_combo": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                              "M3": EXPECT_M3, "M4": EXPECT_M4},
            },
            "note": ("五轮并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合）；"
                     "按冻结 comparison_rule=(M1 升序, M2 升序, M3 升序, "
                     "M4 升序) 字典序：r20=G1 破坏经资格门剔除不入排序；"
                     "排序（不含 r20）=r19 轴3 第一、r18 轴2 第二、r16 基"
                     "线参照行第三、r17 轴1 末位（M1=0.88 劣于基线=负向）；"
                     "阶段2 已收束（combination_decision_rule 执行完毕）——"
                     "不预写后续决策"),
            "role": ("组合轮 M 元组五轮并列登记（comparison_rule 冻结规则"
                     "的已测行并列；r16–r19 行=dev-r19 在案行实测装载、"
                     "r20 行=本轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r20.json（6573a59a…）盘上值"
            "装载（M1=14/22=0.636364 与 m.top_abstain_rate_r20、M2=4/14="
            "0.285714 与 bottom_side_observation、M3=6 与 black_dot_"
            "tracking（rubric 口径 existence_blackdot、r13–r16 132 条弃权"
            "旗重放对拍逐一相等）、M4=0.25 与 view_layer.top."
            "abstain_rate_range、contact=2 与 contact_family_abstain_"
            "flags_rubric_r20 逐一相等，fail-closed），非手抄；axis-plan "
            "在案 r16 基线四键 [0.771429, 0.857143, 12, 0.261904] 与 "
            "run-r20 baseline_cross_check 交叉核对一致；M1 绝对降幅 "
            "0.771429−0.636364=0.135065 超显著收益阈值 0.10（描述层命中、"
            "与字母裁决分列互不改写——r18/r19 先例延续；跨轮实例群漂移混"
            "杂照旧声明、本轮为组合轮=两轴并施无法分离各自贡献；主判据="
            "ordering 字典序劣于 r19+G1 破坏→reject）"),
        "next_candidate_r20": (
            "无下一轮建议键（对照 s72 血统的 next_candidate_r20 结构位：阶段2 "
            "已收束——R21 不做、收益最大配置=r19_axis3 在案；下一候选选项见 "
            "combination_decision_application.next_candidate_suggestion，由"
            "用户拍板）"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "R20 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "stage2_closure": stage2_closure,
        "status": ("R20 实测 (M1,M2,M3,M4)=(0.636364, 0.285714, 6, 0.25)"
                   "（contact=2 另列）；r20 资格门剔除不入排序（G1 破坏）；"
                   "阶段2 收束=收益最大配置=轴3 单变量 r19_axis3（如实记"
                   "录）；字母与实验账分列互不改写（本轮 reject 但 M1 降幅 "
                   "≥0.10 描述层命中——两账分列，r18/r19 先例延续）；"
                   "R21 不做"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4},
    }

    directional_observation_vs_r16 = [
        ("R16→R20 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 沿用"
         "无新增版本：12/12 派次自述「未读取盘上任何其他文件」；R20T/R20B "
         "前缀随 r20 指引 §6 落盘固化=机械替换无需派发层覆盖）；旗标 "
         "49→50→46→36（六实例旗数 top 27/35 基线轮 14/8/9→r18 14/8/9→"
         "r19 11/18/10→r20 8/8/6、bottom 4/3/5→6/6/7→4/3/0→6/4/4；非弃权 "
         "18+弃权 18）；全旗标合计弃权率 0.66（33/50，附记口径）→0.478261"
         "（22/46，附记口径）→0.5（18/36，附记口径）；预注册主通道 ordering "
         "三分判据：(s) R20 四元组 (0.636364, 0.285714, 6, 0.25) ordering "
         "字典序劣于最优单轴 r19 (0.461538, 0.571429, 4, 0.211111)（M1 首"
         "键即分胜负）⇒supported 未成立；(r) G1 破坏命中⇒reject_guards 支"
         "（支序最高）⇒字母裁决=reject（组合出局；处置=冻结 "
         "iii_non_additive_fallback 采最优单轴 r19 配置）；代表配置"
         "（top=top-i1、bottom=bottom-i2 双 tie 如实）弃权率 0.428571"
         "（6/14，r19）→0.333333（4/12）。"),
        ("视角层三分列（measurement_design item 2）：top 弃权率 0.666667/"
         "0.928571/0.666667（r16，极差 0.261904）→0.454545/0.388889/0.6"
         "（r19，极差 0.211111）→0.5/0.75/0.666667（r20，极差 0.25=M4 较 "
         "r19 走阔、较 r16 收窄）——组合轮（渲染零变更=renders-r14b 字节复"
         "用）下聚合落点 27/35=0.771429→18/39=0.461538→14/22=0.636364（较 "
         "r19 回升、较 r16 基线仍降 0.135065=显著收益定义描述层命中，与字"
         "母裁决分列互不改写；跨轮实例群漂移混杂照旧声明[r15→r16 纯重抽漂"
         "移 0.09064 在案参照]、本轮为两轴并施组合轮=无法分离轴2/轴3 各自"
         "贡献）；bottom 1.0/0.8/0.75（r16，极差 0.25）→0.75/0.333333/"
         "None（r19，极差 0.416667 按可计算实例）→0.0/0.0/1.0（r20，极差 "
         "1.0；12 格全部≥1 旗、bottom 中位数=0.0=排序后第 2）——bottom 全"
         "旗聚合弃权率 12/14=0.857143→4/7=0.571429→4/14=0.285714（improved "
         "改善方向如实单列）；本轮零旗标派次=0（r19 的 2 格→r20 的 0 格；"
         "bottom-i3 两板 4 旗全弃权=bottom 唯一弃权实例）。"),
        ("matches 与 GT 双口径（measurement_design item 3）：r19 唯一命中"
         "（union 1/13=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT）本轮未再"
         "现——union=agreement=0/13 全轮零命中（六实例 36 旗 matches 合计 "
         "0 条、candidate 对空集；单实例命中不稳定如实登记）；代表配置 "
         "gt_recall_total 0.0（0/13）、seed_match_rate 0.0（0/8，诊断口"
         "径，禁称 precision/FPR）；bottom 非弃权旗零匹配属结构性：GT 13 "
         "条全部 side=top、bottom 无 GT 在案（gt-audit-r1：bottom GT=无源"
         "已关闭）⇒ bottom 旗标与 GT 匹配应为空，如实。"),
        ("通道归因（vs R19，预注册重放方法）：几何门面积比出局 0→0"
         "（R19=0→R20=0 不升→guard_ok=True→G2 维持）；类别门 2→0（r19 的 "
         "2 条近失 R19T-004×AP-6-R2LED2、R19T-009×P1-L1NB 本轮零再现；逐"
         "轮计数如实）；视角门 0（top 非弃权旗与同态 GT 零视角错位交叠；"
         "bottom 非弃权旗零匹配属结构性）。通道链自 r6：几何门 r6=1→r7=0→"
         "r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→r15=0→r16=0→r17=0→r18=0"
         "→r19=0→r20=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→r12=0→"
         "r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=2→r20=0。重放与 "
         "compare_v3 对拍一致。"),
        ("预注册假设（axis-plan-r20-combo-additivity）字母裁决=reject"
         "（落支=(r) G1/G2 任一破坏（per axis-plan early_stop_rule."
         "guard_failure_exit）——组合轮出局（字母照实+出局声明）；本轮="
         "G1 破坏（bottom courtyard 非弃权实测 [2, 0, 0]≠0/0/0 维持）；"
         "处置=冻结 combination_decision_rule.iii_non_additive_fallback "
         "采最优单轴 r19 配置；r20-prep-record hypothesis_test."
         "adjudication 判据原文执行；唯一正式裁决）。实测：R20 四元组="
         "(0.636364, 0.285714, 6, 0.25)（M1=top 全旗聚合弃权率 14/22、"
         "M2=bottom 4/14、M3=黑点族弃权旗数 6、M4=top 逐实例极差 0.25）；"
         "r19 基准元组=(0.461538, 0.571429, 4, 0.211111)（dev-r19 "
         "measured_rows 装载+run-r19 内嵌实例记录 live 复算交叉核对一致，"
         "不手工抄数）→ordering 字典序不劣于=不成立；(r) 支 M1 ≥0.771429"
         "→crit_reject_m1=False（r16 基线=同一聚合逻辑对 run-r16 内嵌输入"
         "双侧复算 27/35=0.771429，live 重放与在案登记/axis-plan 锚交叉核"
         "对一致）；G1=破坏（2/0/0；bottom-i1 两板 R20B-003/R20B-006 经 "
         "(iii-a) 间隙支负责任报告路径产生）、G2=维持（几何门 R19=0→R20=0）；"
         "(m) 支 M1 <0.771429=True 但支序 reject 在前——marginal 未落。"),
        ("机制观察单列（不凌驾）：(a) G1 分岔（关键，如实单列）——守门设计"
         "针对 courtyard 混淆弃权、本轮触发源=负责任报告（(iii-a) 间隙支"
         "把弃权引导为有据报告）；条款按设计工作但按预注册字母仍=reject；"
         "守门条件与判据改良的方向冲突=判据设计的机制教训（g1_bifurcation_"
         "record 单列）；(b) 援引分记（两条款分开记、互不合并）：旗级 "
         "location_evidence 含「§5B」=0 旗、含「(iii-a)」=0 旗、含「分支"
         "(」=0 旗（三集合全空=本轮判读在旗级理由中零字面援引，对照 r19 "
         "旗级 (iii-a) 6 旗+分支( 2 旗）；notes 级含「§5B」=4/12 派次"
         "（applied/prep1-top-i1 黑点弃权自述「仪器注记 §5B 不作为判据」+"
         "applied/prep1-bottom-i2「§5A/§5B 仪器注记仅作事实参考」）、含"
         "「(iii-a)」=4/12 派次（applied/prep1-top-i2「近邻形态按§4(iii-a) "
         "可操作分辨条款执行」+applied/prep1-bottom-i3 两板「按 "
         "§4(iii)/(iii-a) 弃权」）——援引习惯集中在 notes 层；双基线对照："
         "r18 §5B 派次级 1/12（dev-r18 在案）、r19 (iii-a) notes 级 10/12"
         "（dev-r19 在案）；(c) (iii-a) 逐旗落支=间隙支（branch1_gap_"
         "report）2（全部非弃权 courtyard 报告旗=G1 破坏直接构成；间隙支 "
         "notes 级判正常路径 2 派次=bottom-i1 两板「间隙带可辨认→视觉贴近"
         "→报告」自述）+侵入支（branch2_intrusion_report）4+残余弃权支"
         "（branch3_residual_abstain）7；(d) rubric 族计数 contact 2/"
         "existence_blackdot 6/existence_other 10（r13–r16 132 条弃权旗"
         "重放对拍逐一相等后套用 r20，链值 8/15/5/10 在案）——黑点 6 条"
         "全弃权（top-i1 两板 2+bottom-i3 两板 4；top-i1 黑点=§5B 已证实"
         "物理来源仍按 §4 存在性判据弃权=§5B 反指示声明遵守的在案实例）vs "
         "r16=12/r18=13/r19=4 双基线间+黑点转非弃权旗 6 条（全 bottom）+"
         "黑点判正常派次 4（对照 r15=3/r16=2/r18=2/r19=3）+存在性其他 10 "
         "vs r18=12/r19=14（回落、未显著上升=弃权转移对照口径如实登记）；"
         "(e) top 弃权构成分型=接触性 5（r19）→4、存在性 13（r19）→9、"
         "其他 0（r19）→1（14 条逐旗摘录在案；r16 对照 11/15/1）；(f) 绿区"
         "语义化：bottom 派次 §4(i) 空隙/翼瓣语义化路径与 §5A/§5B 显式援引"
         "逐派次如实分列（bottom-i2 两板双援引、其余派次按 §4(i) 独立执"
         "行）。"),
        ("bottom 改善通道单列（M2=4/14=0.285714 vs r16 基线 12/14=0.857143"
         " vs r18 13/19=0.684211 vs r19 4/7=0.571429，improved 方向；不影"
         "响字母）：(1) 弃权实例收缩=bottom 三实例中仅 bottom-i3 弃权"
         "（4 旗全弃权）、bottom-i1/i2 弃权=0（r19 为 bottom-i1 3+bottom-i2 "
         "1）；(2) 黑点族弃权旗（rubric 口径）=6 条（bottom-i3 两板 4+"
         "top-i1 两板 2）；(3) 黑点转非弃权旗 6 条全 bottom（bottom-i1 "
         "courtyard 报告 2+bottom 孤立焊盘对/组件非弃权报告 4）；(4) bottom "
         "courtyard 类旗=2 条（全非弃权——G1 字面破坏的直接构成，分岔记"
         "录单列）。"),
        ("工具行为与派发操作（协议侧 v1.2 沿用第九轮，如实入账）：R20 十二"
         "派次全部以 Read 工具直读内嵌图像、逐派次 reading_notes 自述「未读"
         "取盘上任何其他文件」（12/12 逐字摘录在案 reader_tool_evidence/"
         "dispatch_discipline）；全部判读输入严格限于（指引+该 PNG），零 "
         "GT/零诊断/零 legend=非盲读违规；flag_id 编号行为=6 实例全部同实"
         "例跨板连续（与 prep-record naming 声明全部相符；对照 r19 混合行"
         "为如实登记）=读者实例输出行为差异如实登记、编排侧按 (state, "
         "flag_id) 限定；本轮无派发操作事故（对照 r19 wave-3 重派事故先例"
         "如实单列）；跨轮实例不同+轮内实例差异=混杂因素照旧声明"
         "（reader_instance_note）。"),
        ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延续，零"
         "阈值改动零期望）：courtyard 类旗标 5 条（top 3+bottom 2）：top 弃"
         "权 3（(iii-a) 残余弃权支）+bottom 非弃权 2（R20B-003/R20B-006，"
         "间隙支负责任报告=G1 守门字面破坏的直接构成）——非弃权 courtyard 2 "
         "条零命中（命中链 r8=1→r9=0→r10=1→r11=3→r12=0→r13=0→r14=0→r15=0"
         "→r16=1→r17=0→r18=0→r19=0→r20=0 延续）。reroute 类 2 条（弃权 2、"
         "top-i2 两板；子串「等长|蛇形」零命中）；产量链 r8=1→r9=0→r10=2→"
         "r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→r17=1→r18=3→r19=3→r20=2；"
         "滥用型通道被动追踪=0。"),
    ]

    honest_conclusion = (
        "本轮（development 域 stage2 组合轮=轴3+轴2 两轴变更并施（变更="
        "判读指引合成 observation-guidance-r20.md 9cdac9ed[r19 基座 "
        "8633bda5 机械变换派生 mechanical_transform_derive：r19 基底+§5B "
        "黑点仪器注记节自 r18 指引 cadcb8f3 逐字转录整节插入[§5B 文本跨代"
        "哈希交叉锚 content_sha256 19ecdb42]+§6 前缀轮次标识机械同步；"
        "§4(iii-a) 随基座逐字承继零改动=两增补并集（§5B+§4(iii-a)）=组合"
        "轮唯一操纵因子]+渲染零变更=renders-r14b 四图字节复用+GT/阈值/协议"
        "零变更（13 条冻结、v1.1+v1.2 维持）；instrument_change.changed="
        "false 已预注册；per axis-experiment-plan-r17-r20 冻结件[用户 "
        "2026-09-09 指令操作化] stage2 唯一组合轮）12 派次 36 旗标中 18 "
        "弃权、18 非弃权：代表配置（top-i1+bottom-i2 双 tie 如实）gt_recall"
        "=0.0（0/13）、seed_match_rate=0.0（0/8，诊断口径，禁称 precision/"
        "FPR）、abstain_rate=0.333333（4/12），联合评价 not_met（gt_recall、"
        "seed_match_rate 两项未达 APR-0011 暂行线；gt_count 13≥12 与 "
        "abstain_rate 0.333333≤0.5 单分项入线；诊断对照，非采纳门；连续达"
        "标计数 0→0；GT 条目层 union=agreement=0/13 双口径并列——全轮零命"
        "中、r19 唯一命中未再现=单实例命中不稳定如实）。预注册假设"
        "（axis-plan-r20-combo-additivity）裁决（按 r20-prep-record "
        "hypothesis_test.adjudication ordering 三分判据）=reject（字母口"
        "径，唯一正式裁决）：落支=(r) G1/G2 任一破坏（per axis-plan "
        "early_stop_rule.guard_failure_exit）——组合轮出局（字母照实+出局"
        "声明）；本轮=G1 破坏（bottom courtyard 非弃权实测 [2, 0, 0]≠0/0/0 "
        "维持；bottom-i1 两板 R20B-003/R20B-006 经 (iii-a) 间隙支负责任报"
        "告路径产生）+R20 四元组 (0.636364, 0.285714, 6, 0.25) ordering "
        "字典序劣于最优单轴 r19 (0.461538, 0.571429, 4, 0.211111) 双重；"
        "处置=冻结 combination_decision_rule.iii_non_additive_fallback 采"
        "最优单轴 r19 配置；(r) 支 M1 ≥0.771429 未命中（r16 基线 27/35="
        "0.771429 双侧复算一致）；(m) 支 M1 <0.771429 虽真但支序 reject 在"
        "前。守门 G1=破坏（2/0/0；r16 基线 0/0/0 live 重放对照）、G2=维持"
        "（几何门 R19=0→R20=0）——early_stop 触发（axis_early_stop_"
        "triggered=True）。G1 分岔记录（关键机制观察，如实单列不凌驾字"
        "母）：守门设计针对 courtyard 混淆弃权、本轮触发源=负责任报告"
        "（(iii-a) 把弃权引导为有据报告）——条款按设计工作但按预注册字母仍="
        "reject；守门条件与判据改良的方向冲突=判据设计的机制教训（后续如"
        "需区分两类非弃权 courtyard 旗须 prep-record 预注册修订守门操作化"
        "定义、不得事后改判本轮）。机制观察单列（不影响字母）：援引分记="
        "旗级 §5B/(iii-a)/分支( 全 0 旗+notes 级 §5B=4/12、(iii-a)=4/12"
        "（援引习惯集中在 notes 层）；(iii-a) 落支=间隙 2+侵入 4+残余弃权 "
        "7（间隙支 notes 级判正常 2 派次）；rubric 族=contact 2/existence_"
        "blackdot 6/existence_other 10（r13–r16 132 条重放对拍逐一相等；"
        "黑点 6=r18 13 与 r19 4 双基线间；存在性其他 10 vs r18 12/r19 14）"
        "+黑点转非弃权旗 6（全 bottom）+黑点判正常派次 4；top 弃权构成分"
        "型=接触性 4+存在性 9+其他 1。实验对照账：本轮 (M1,M2,M3,M4)="
        "(0.636364, 0.285714, 6, 0.25)（M3 槽位=冻结件黑点族口径、contact=2 "
        "另列不占槽；axis-plan benefit_metrics 口径实测装载），五轮并列"
        "（r16 0.771429/0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、"
        "r18 0.645161/0.684211/13/0.277778、r19 0.461538/0.571429/4/"
        "0.211111、r20 0.636364/0.285714/6/0.25）——r20=G1 破坏经资格门剔"
        "除不入排序；排序（不含 r20）=r19 第一、r18 第二、r16 参照、r17 末"
        "位；显著收益定义描述层命中（M1 绝对降幅 0.135065≥0.10；r18 "
        "0.126268、r19 0.309891 亦 ≥0.10）——与字母裁决分列互不改写（r18/"
        "r19 先例：reject/marginal 但排序居首；本轮 reject 但降幅命中）。"
        "阶段2 收束：combination_decision_rule 执行完毕（supported 未落、"
        "marginal 未落、reject 落）⇒三轴实验最终结论=收益最大配置=轴3 单"
        "变量（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、黑点"
        "族 13→4；按冻结 iv_final_selection 全部已测配置中排序最优者）；"
        "R21 不做（early_stop strong_single_axis_shortcut 命中→组合轮仅一"
        "个+三轴不全正（轴1 r17 M1=0.88 劣于基线）+本轮 G1 破坏排除追加"
        "——三重独立依据）。下一候选建议（如实单列，供主审/用户决策）："
        "r19 配置的 M4=0.211111 差 0.011111 未过 supported 门 0.20——可选"
        "后续=同指引重复轮（r16 先例）收敛归因，或接受 marginal 收益收束"
        "训练环转入收敛评估；由用户拍板、本包不预写决策。reject=预注册阈值"
        "命中方向的描述性结论、非因果证明——「正确测出不可加+守门破坏同样"
        "是有效证据」；单轮 n=3、development 域只描述不断言；字母裁决只回"
        "答「两轴并施收益是否不低于最优单轴 r19（可加性）且守门维持」的计"
        "划件判据命中方向；机制观察/度量教训单列、不凌驾不改写字母裁决；"
        "APR-0011 门（代表配置）与字母裁决分列不合并；本轮判据均为描述性边"
        "界、非门阈值（门零改动）。残余实例差异仍存（top 弃权率 0.5/0.75/"
        "0.666667 极差 0.25、bottom 0.0/0.0/1.0 极差 1.0=bottom-i3 全弃权"
        "对 bottom-i1/i2 零弃权的实例两极分化=判读语义歧义未穷尽）。bottom "
        "14 旗（4 弃权+10 非弃权）零匹配属结构性（GT 13 条全部 side=top，"
        "bottom GT 无源在案 gt-audit-r1）；本轮 12 格零旗标派次=0（对照 "
        "r19 的 2 格）。类别门 r19 的 2 条近失本轮零再现（通道链 r19=2→"
        "r20=0）。GT 侧三候选经 gt-audit-r1 全部关闭（延续零改动，GT 侧不"
        "再有候选；r20 全轮零命中与 bottom GT 无源结构相容、top 零命中=r19 "
        "唯一命中未再现）。不做「能力已修复/已达成」类断言；in_calibrated_"
        "range 恒 False。本批证据按协议 v1 §4 属 development 域，不得冒充"
        "留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r20-prep-record 判据=ordering 可加性比较、"
         "阈值零改动；两轴并施的单轮组合无法分离两轴各自贡献——只回答可加性"
         "与否，归因边界如实声明）。"),
        ("R16 对照基线=calibration-run-r16.json（同一聚合逻辑对内嵌实例记录"
         "双侧复算 top 27/35=0.771429、bottom 12/14=0.857143，与在案登记/"
         "axis-plan 锚交叉核对一致，不手工抄数）；contact 对照基线=分型件 "
         "rubric 口径 10（r13–r16 链 8/15/5/10 重放对拍逐一相等后套用，不手"
         "工抄数）；M1 绝对降幅 ≥0.10=计划件显著收益阈值（r15→r16 纯重抽漂"
         "移 0.09064 为历史幅度参照；本轮 0.135065 描述层命中与字母裁决分列"
         "互不改写）；轮间对比只做方向性描述（跨轮实例群混杂照旧，per "
         "axis-plan comparison_rule.drift_confound_note 显式容忍；本轮为组"
         "合轮=两轴并施归因边界声明）；M1 分母（top 旗数 35→39→22）本身随"
         "轮变化、弃权率比较含分母效应，构成分解（top 弃权构成分型+(iii-a) "
         "落支+黑点转非弃权旗）单列补足。"),
        ("通道归因方法：照抄 run-r15–run-r20 channel_attribution 的重放口径"
         "（deviation_note 承接），R15/R16/R17/R18/R19/R20 均以内嵌输入确定"
         "性重放并与 compare_v3 对拍（run-r20 channel_attribution.method）；"
         "重放复现与在案登记一致（fail-closed）；类别门 r19=2→r20=0 如实计"
         "数、不构成字母裁决输入。"),
        ("读者实例行为与派发操作披露如实记录：R20 十二派次 v1.2 规约自述合规"
         "（纯 Read 直读、12/12 派次自述「未读取盘上任何其他文件」，逐派次 "
         "reading_notes 原文在案）；输出格式披露（12 件缩进格式冻结原始判读"
         "件、零改动直读）parse 校验全部通过；flag_id 编号行为=6 实例全部同"
         "实例跨板连续（与 prep-record naming 声明全部相符；对照 r19 混合行"
         "为）=实例输出行为差异如实登记、编排侧按 (state, flag_id) 限定；本"
         "轮无派发操作事故（对照 r19 wave-3 重派事故单列先例）。跨轮 reader "
         "实例不同+轮内实例差异=混杂因素，每视角 n=3；本轮轮前评审=pre_"
         "round_review 在案（r20-prep-record）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=reject 维持不"
         "变（reject=组合劣化/守门破坏的描述性边界结论、非因果证明；单轮 n=3 "
         "小样本方向性证据；主通道三分判据（ordering/M1/G 四件组）与 APR-0011 "
         "门分开表述、互不凌驾：门联合评价（代表配置）=not_met 如实分列）；"
         "不得回溯改判既往轮次（r8–r19 字母裁决维持不变）；早期轴轮字母与实"
         "验账分列先例（r18：reject 但排序居首；r19：marginal 但排序居首）延"
         "续——本轮 reject 且 M1 降幅描述层命中=两账分列不合并。"),
        ("G1 分岔=判据设计的机制教训（单列，供后续预注册参考、本轮不追溯适"
         "用）：守门 G1 操作化定义「bottom courtyard 非弃权 0/0/0 维持」预"
         "注册于 (iii-a) 判据改良之前、不区分「混淆弃权转非弃权」与「有据报"
         "告转非弃权」两类形态——本轮 (iii-a) 间隙支负责任报告（R20B-003/"
         "R20B-006）按改良方向工作却触发守门字面；预注册字母优先（reject_"
         "guards）=预注册纪律的正确执行；后续如需区分两类形态，修订守门操作"
         "化定义须走 prep-record 预注册（先于该轮盲读冻结）、不得事后改判本"
         "轮或既往轮次。"),
        ("度量教训在案（供后续预注册参考、本轮不追溯适用）：M3 槽位定义维持"
         "冻结件黑点族口径、contact=2 另列不占槽=对照账纪律延续；contact 计"
         "数口径=分型件 rubric 机械套用（计数口径跨轮漂移是历史教训：r15 "
         "prose 口径 7 vs 分型件 rubric 口径 8 在案，axis-plan M3_caveat 已"
         "声明一律采用 rubric 口径）；组合轮与单轴轮的四元组并列遵守同一 "
         "benefit_metrics 口径（五轮并列在案）；实验对照账与字母裁决分列互"
         "不改写（r18/r19 先例延续、本轮 reject+降幅命中=两账分列）。"),
    ]

    next_iteration_targets = [
        ("阶段2 收束登记：combination_decision_rule 执行完毕（supported 未"
         "落、marginal 未落、reject 落）⇒三轴实验最终结论=收益最大配置=轴3 "
         "单变量（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、黑"
         "点族 13→4；按冻结 iv_final_selection 全部已测配置中排序最优者="
         "stage2_final_selection 纯函数应用、构造可测）；R21 不做（early_"
         "stop strong_single_axis_shortcut 命中+三轴不全正（轴1 r17 M1=0.88 "
         "劣于基线 0.771429）+本轮 G1 破坏排除追加——三重独立依据；引用冻"
         "结原文在案）。"),
        ("下一候选建议（如实单列，供主审/用户决策）：r19 配置的 M4=0.211111 "
         "差 0.011111 未过 supported 门 0.20（(s) 支唯一未达项）——可选后续"
         "=同指引重复轮（r16 先例：r15→r16 同指引重复轮、渲染零变更、仅实"
         "例重抽）收敛归因（区分真实收益与实例群漂移 0.09064 参照），或接受 "
         "marginal 收益收束训练环转入收敛评估（不再追加迭代轮）；两选项均须"
         "预注册纪律核对（重复轮=prep-record 预注册先于盲读冻结）；由用户拍"
         "板、本包不预写决策。"),
        ("G1 分岔后续（判据设计机制教训，单列）：守门 G1 操作化定义与判据改"
         "良的方向冲突在案（负责任报告触发守门字面）——后续如需区分「混淆弃"
         "权」与「有据报告」两类 bottom courtyard 非弃权旗，须先走 prep-"
         "record 预注册修订守门操作化定义（先于该轮盲读冻结）；不得事后改判 "
         "r20 或既往轮次；本轮 reject 维持不变。"),
        ("留出集时机=开发线收敛（须用户拍板）：r20 字母=reject（组合出局）"
         "→收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未达成，"
         "不得写成已达成）；收益最大配置 r19_axis3 的字母=marginal（部分收"
         "益）在案、轴3 不判定为胜出；GT 侧维持全关闭声明延续（gt-audit-r1["
         "1f20554a…]三候选全部关闭，r9–r20 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r20 全轮零命中[union=agreement=0/13]、"
         "r19 唯一命中未再现=单实例命中不稳定如实、非新 GT）；in_calibrated_"
         "range 恒 False 直到正式采纳（须人工批准）；达标证据仍须留出集"
         "（out/v3-tl2/holdout/HOLDOUT-PLAN.md a4b80193… 与 datasets/"
         "holdout-candidates-r1 在案）。"),
        ("判读侧残余问题登记：bottom-i3 两板 4 旗全弃权（黑点族）对 "
         "bottom-i1/i2 零弃权=实例两极分化（板内孤立焊盘对跨实例/跨板出口"
         "不同=判读语义歧义未穷尽，r19 在案先例延续）；top-i1 黑点=§5B 已证"
         "实物理来源仍按 §4 存在性判据弃权（notes 自述「仪器注记 §5B 不作为"
         "判据」=§5B 反指示声明遵守的在案实例）；reroute 类 2 旗弃权、子串"
         "「等长|蛇形」零命中=滥用型通道被动追踪=0 延续；类别门 r19 的 2 条"
         "近失本轮零再现（通道链 r19=2→r20=0）。"),
    ]

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "combination_decision_application": combination_decision_application,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": directional_observation_vs_r16,
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本件=R20 收口包 B（dev-record 分包）：development 域第 20 轮迭代"
        "（stage2 组合轮=轴3+轴2 判读指引合成）的轮次开发记录；迭代轮不得"
        "冒充留出证据。",
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "g1_bifurcation_record": g1_bifurcation_record,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev19["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r20 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r20 全旗标合计 18/36=0.5 仅作附记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R19 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 两项未达暂行线；gt_count 13≥12 "
                         "与 abstain_rate 0.333333≤0.5 单分项入线）——GT 条"
                         "目层 union=agreement=0/13 亦未达 0.75（全轮零命"
                         "中、candidate 对空集；r19 唯一命中未再现；双口径"
                         "与门分列如实）"),
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
            "读冻结防事后择优；stage2 R20=唯一组合轮=轴3+轴2）→"
            "r20-prep-record.json（e29ee2a3…，本轮预注册件，measurement_"
            "design 聚合口径与 hypothesis_test.adjudication ordering 三分"
            "判据（supported=R20 四元组 ordering 字典序不劣于最优单轴 r19/"
            "marginal=未达 supported 但 M1 <0.771429 且 G1/G2 维持/reject="
            "M1 ≥0.771429 或 G1/G2 任一破坏）先于盲读冻结；instrument_"
            "change.changed=false；changed_variables=[判读指引合成（§5B+"
            "§4(iii-a) 并集=guidance-combo-s5b-plus-s4-iiia-union，单一复合"
            "变量）一件登记]；manipulated_factor=指引合成[唯一操纵因素]；"
            "no_instrument_change=true）→判读指引=observation-guidance-"
            "r20.md（9cdac9ed…，r19 基座 8633bda5…机械变换派生 mechanical_"
            "transform_derive：r19 基底+§5B 黑点仪器注记节自 r18 指引 "
            "cadcb8f3…逐字转录整节插入[§5B 文本跨代哈希交叉锚 content_"
            "sha256 19ecdb42…；§5B 插入编辑先例=r18-prep-record 3fc054c4 在"
            "案]+§6 前缀轮次标识机械同步[R20T-/R20B-]；§4 整段与 r19 逐字相"
            "等=承继断言、(iii-a) 随基座零改动；byte_size 21435→22893="
            "delta 1458）→渲染零变更（renders-r14b 四图字节复用、与 r14/"
            "r15/r16/r17/r18/r19 盲读同一批文件[applied-top 298bc620/"
            "applied-bottom d7284259/prep1-top b2f84524/prep1-bottom "
            "d7284259，bottom 两图字节同；witness-r14b b63771f9 在案]）→"
            "12 次盲读[6 实例全部同实例跨板连续、零旗标派次=0、无派发事"
            "故]→run-r20（6573a59a…，本链执行落盘；r19_run_record_reference"
            "=e5755a11 在案=M 元组基准行 live 复算输入）；GT 重投影沿用 "
            "derivation-log-r5.json（62343380…）零新派生（GT 全部 side=top；"
            "渲染零变更=GT 重投影输入未变）；GT 冻结纪律：轮后未增删改；"
            "gt-audit-r1（1f20554a…）结论维持 GT 零改动（三候选关闭，"
            "gt_audit_reference 在案）"),
        "reference_hash_manifest": reference_hash_manifest,
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域 stage2 组合轮（第二十轮）=轴3+轴2 两轴变更并施"
            "（axis-experiment-plan-r17-r20 stage2 唯一组合轮）：变更=判读"
            "指引合成 observation-guidance-r20.md（9cdac9ed 实测锚，r19 基"
            "座 8633bda5 机械变换派生 mechanical_transform_derive：r19 基"
            "底+§5B 黑点仪器注记节自 r18 指引 cadcb8f3 逐字转录整节插入[两"
            "轴变更同时施加=§5B+(iii-a) 两增补并集；(iii-a) 随 r19 基座逐"
            "字承继零改动=§4 整段逐字相等断言]+§6 前缀轮次标识机械同步"
            "[R20T-/R20B-]）+渲染零变更=renders-r14b 四图字节复用（与 "
            "r14–r19 盲读同一批文件；no_instrument_change=true）+GT 集/协"
            "议阈值与度量版本/比较器常量零改动（GT 重投影沿用 derivation-"
            "log-r5——零新派生；gt-audit-r1 三候选关闭结论延续）；协议 "
            "v1.1+v1.2 维持无新增版本；instrument_change.changed=false 已"
            "预注册（changed_variables=[guidance-combo-s5b-plus-s4-iiia-"
            "union 单一复合变量]；轴=A3_criterion_contact_clarification+"
            "A2_blackdot_instrument_annotation）；检验假设 axis-plan-r20-"
            "combo-additivity（判据=r20-prep-record.json hypothesis_test."
            "adjudication ordering 三分判据：supported=R20 四元组在冻结 "
            "comparison_rule.ordering 字典序下不劣于最优单轴 r19/marginal="
            "未达 supported 但 M1 <0.771429 且 G1/G2 维持/reject=M1 "
            "≥0.771429 或 G1/G2 任一破坏，轮后如实执行：字母裁决唯一正式+"
            "机制观察/度量教训单列+G1 分岔记录单列；守门 G1/G2 独立单列，"
            "任一破坏→r20 组合按 plan early_stop_rule 出局）；主通道三分判"
            "据与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自"
            "独立计算、互不凌驾、分开表述；measurement_design 聚合口径先于"
            "盲读冻结；跨轮收益比较按 axis-plan 冻结规则（R20 行见 "
            "axis_experiment_ledger 五轮并列：r20 资格门剔除不入排序、阶段2 "
            "收束=收益最大配置=轴3 单变量 r19_axis3、R21 不做）；按协议 v1 "
            "§4，迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "run_record_ref": {"path_rel": REL_RUN_R20, "sha256": run20_sha},
        "schema_version": SCHEMA_VERSION,
        "stage2_closure": stage2_closure,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s75-cal-r20-devrecord] round20-dev-record: {status}")
    print(f"[s75-cal-r20-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch={dev['hypothesis_test_i']['measurement'][
              'letter_branch']}")
    print(f"[s75-cal-r20-devrecord] 三分判据: (s) ordering 不劣于 r19="
          f"False（R20 四元组 (0.636364, 0.285714, 6, 0.25) M1 首键劣于 "
          f"r19 (0.461538, 0.571429, 4, 0.211111)）；(r) G1 破坏=True（"
          f"bottom courtyard 非弃权 2/0/0≠0/0/0；G2 维持 0→0）⇒ "
          f"reject_guards 支（支序最高）；(r) M1 ≥0.771429 未中；(m) 未落"
          f"（支序 reject 在前）⇒ reject（组合出局；处置=采最优单轴 r19）")
    print(f"[s75-cal-r20-devrecord] G1 分岔（单列）: 守门设计针对 courtyard "
          f"混淆弃权、本轮触发源=负责任报告（(iii-a) 间隙支把弃权引导为有据"
          f"报告 R20B-003/R20B-006）——条款按设计工作但按预注册字母仍=reject；"
          f"守门条件与判据改良的方向冲突=机制教训")
    print(f"[s75-cal-r20-devrecord] 机制观察: 援引分记=旗级 §5B/(iii-a)/分支"
          f"( 全 0+notes 级 §5B=4/12、(iii-a)=4/12（集中在 notes 层）；落支="
          f"间隙 2+侵入 4+残余弃权 7；rubric 族 contact 2/黑点 6/存在性其他 "
          f"10；黑点转非弃权 6+判正常派次 4；top 分型 4/9/1")
    print(f"[s75-cal-r20-devrecord] 实验对照账: 五轮并列 r16 "
          f"(0.771429, 0.857143, 12, 0.261904)/r17 (0.88, 0.75, 8, "
          f"0.333333)/r18 (0.645161, 0.684211, 13, 0.277778)/r19 "
          f"(0.461538, 0.571429, 4, 0.211111)/r20 (0.636364, 0.285714, 6, "
          f"0.25)；r20 资格门剔除不入排序；显著收益 0.135065≥0.10 描述层命"
          f"中（与字母分列互不改写）")
    print(f"[s75-cal-r20-devrecord] 阶段2 收束: combination_decision_rule 执"
          f"行完毕（supported 未落、marginal 未落、reject 落）⇒ 收益最大配置"
          f"=轴3 单变量（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、"
          f"黑点族 13→4）；R21 不做（early_stop+三轴不全正+G1 破坏三重依据）；"
          f"下一候选建议=同指引重复轮（r16 先例）或收束转入收敛评估——由用户"
          f"拍板")
    print(f"[s75-cal-r20-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s75-cal-r20-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0 in_calibrated_range=恒 False")
    print(f"[s75-cal-r20-devrecord] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print(f"[s75-cal-r20-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s75-cal-r20-devrecord] R20 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=reject 唯一正式（组合出局、采最优单轴 r19）；"
          "机制观察/G1 分岔/度量教训单列不凌驾；in_calibrated_range 恒 "
          "False）")


if __name__ == "__main__":
    main()
