#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s78_calibration_r22_devrecord.py — R22 CLOSE 包 B：
round22-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律；
结构血统=s75_calibration_r20_devrecord.py 同构重建）。

R22=development 域同指引重复轮（收敛归因；r16 先例：r15→r16 同指引
重复、渲染零变更、仅实例重抽；本轮=第二十二轮；执行 round20-dev-record
next_iteration_targets[1] 同指引重复轮候选，用户 2026-09-09「三条轴单
独/组合/全组合尝试，选择收益最大的继续」=授权指令在案；hypothesis_id=
r20-dev-record-candidate-r19-config-same-guidance-repeat）。变更=零
（判读指引=observation-guidance-r19.md 字节复用[8633bda5 实测锚；零新
建指引文件；§6 示例旗 ID 前缀保持 R19T-/R19B- 落盘原文、R22 派次前缀
R22T/R22B 由派发指令层覆盖=前缀差异登记、r16 先例在案]+渲染零变更=
renders-r14b 四图字节复用+GT/阈值/协议零变更；changed_variables=0；
唯一实验操作=reader 实例群重抽 12 派次）；【跳号声明】r21 号段=axis-
experiment-plan-r17-r20（b6ec6467 冻结件）combination_decision_rule.
ii_full_combination 预留的 R21 全组合条件位——per early_stop_rule.
strong_single_axis_shortcut「……不铺全组合（R21 不做）」未触发、该槽
位永久留空；round20-dev-record next_iteration_targets[0] 已登记「R21
不做」；r22 为该登记之后的时序下一轮、与该 R21 全组合位无涉——轮次号
跳号以免台账歧义。
预注册假设复制性三分判据轮后裁决=regressed（字母口径，唯一正式裁决，
轮后不改写）：(g) 支命中=regressed_guards（G2=top 视非弃权旗标几何门
面积比出局条目 R19=0→R22=2 破坏；支序先行）——而 M1=0.390244（16/41）
实际落在复制带 [0.361538, 0.561538]（r19±0.10）内（甚至优于 r19 的
0.461538 带中心）、contact 族=2≤7、G1=bottom courtyard 非弃权 0/0/0
维持——分岔如实登记（g2_bifurcation_record 单列，照 r20 的
g1_bifurcation_record 先例）：冻结支文把 G1/G2 破坏与「r19 量级不可
复制、轴3 收益判定降级为单轮现象」捆绑为同一结论文本，而本轮 M1 分量
与该解释相悖（量级在新鲜实例群复现）——两账分列：字母=regressed（唯一
正式裁决）与 M1 复制事实=机制观察单列，不合并、不改写；(g) 支 M1
≥0.771429 未命中（r16 基线 27/35 live 复算交叉核对一致）；(d) 支 M1
<0.771429 真但守门破坏→不落。R22 四元组=(0.390244, 0.2, 4, 0.104545)
（M1=top 全旗聚合弃权率 16/41、M2=bottom 2/10、M3=黑点族 rubric 口径
4、M4=top 逐实例弃权率极差 0.104545）。机制观察单列：M4 双样本（r19=
0.211111 未过 0.20 门[差 0.011111 在案] vs r22=0.104545 过门=第二次
样本过门；不进字母、不合并分布、不挑优）；三族计数 contact 2/existence_blackdot
4/existence_other 12 对照 r19（4/4/14）与 r20（2/6/10）——黑点 4=与
r19 持平（guidance-r19 无 §5B 节，bottom 黑点仍存在性弃权——bottom-i2
两板 2 条）；援引计数对照 r19 基线（r19=旗级「(iii-a)」6 旗+「分支(」
2 旗、notes 级 10/12 派次在案；r22=旗级全 0、notes 级 §5B=0/12[指引
字节复用无 §5B 节=任何援引为零上下文]、(iii-a)=6/12 派次）；(iii-a)
逐旗落支=间隙 6+侵入 1+残余弃权 2。GT：条目层双口径 union=agreement=
1/13（GT-REVC-P1-L1SHORT，prep1-top-i2 R22T-007+prep1-top-i3 R22T-017
双实例命中=agreement 口径（≥2/3 实例命中才计）自 r12 引入以来首次计入
——r12 以来第二次逐实例命中、且首次两实例一致命中，如实登记）；通道
归因：几何门 2、类别门 4、视角门 1 对照 r19（0/2/0）与 r20（0/0/0）。
联合门：joint not_met、连续=0、in_calibrated_range 恒 False 照常。
三轴实验总收束位：comparison_rule 排序不变（r19_axis3 第一、r18 第二、
r16 参照行第三、r17 末位）；r22 不入排序（G2 破坏=资格门剔除、行仅如
实入账）；轴3 收益的归因状态=「M1 量级在新鲜实例群复现（机制方向支
持）但守门字面降级（预注册字母=regressed）」——两账并列、不合并、不改
写；发展域证据不得冒充留出。下一候选建议（如实单列、由用户拍板、本包
不预写决策）三选项：(a) 接受发展域现状收束训练环、留出集时机由用户判
断（HOLDOUT-PLAN a4b80193 Tier 1/2 候选清单零接触在案）；(b) 对 G2 的
2 条出局条目做机制归因（如 reader 负责任报告的报告框 frame_box_pct 过
大触发 area_ratio>10——属报告框 hygiene 而非判据问题的话，处置轴=派
发层框收敛指引，须新预注册轮）；(c) 再一轮同指引重复轮（三样本）。

生成器纪律（s69/s72/s75 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对）；
- 日期只用常量 DECLARED_DATE="2026-09-09"；
- 防覆写护栏：round22-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round22-dev-record.json 一件（s77 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s78_calibration_r22_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-09-r22"
ROUND_LABEL = "r22"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round22_dev_record"
EVALUATION_DOMAIN = "development"

REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_PREP_R22 = "out/v3-tl2/calibration/r22-prep-record.json"
REL_GUIDANCE_R19 = "out/v3-tl2/calibration/observation-guidance-r19.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_OUT = "out/v3-tl2/calibration/round22-dev-record.json"

INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

# 引用件哈希清单（简报在案锚；逐件 live 实测比对，fail-closed）
REFERENCE_HASH_EXPECTED = {
    "run_r22": (REL_RUN_R22, "80a12c05"),
    "prep_r22": (REL_PREP_R22, "63346ee6"),
    "guidance_r19": (REL_GUIDANCE_R19, "8633bda5"),
    "run_r19": (REL_RUN_R19, "e5755a11"),
    "dev_r19": (REL_DEV_R19, "0e2fdd69"),
    "dev_r20": (REL_DEV_R20, "80e3e9e2"),
    "run_r20": (REL_RUN_R20, "6573a59a"),
}

# 主通道复制性三分判据实测锚（写盘前 fail-closed 与 run-r22 盘上值
# 逐一核对；6 位定点整数交叉相乘，与 s77 REJECT_M1_MIN_6DP/
# REPL_BAND_LO_6DP/REPL_BAND_HI_6DP/CONTACT_MAX_REPL 同锚）
EXPECT_TOP_ABSTAIN_R22 = 16
EXPECT_TOP_FLAGS_R22 = 41
EXPECT_TOP_RATE_R22 = 0.390244
EXPECT_BOTTOM_ABSTAIN_R22 = 2
EXPECT_BOTTOM_FLAGS_R22 = 10
EXPECT_BOTTOM_RATE_R22 = 0.2
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_CONTACT_R22 = 2
EXPECT_CONTACT_R16_BASELINE = 10
EXPECT_CONTACT_CHAIN_R13_R16 = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
# 实验对照账（axis-experiment-plan benefit_metrics 口径；M3 槽位=冻结件
# 黑点族 rubric 口径、本轮实测 4；contact=2 另列不占 M3 槽位）
EXPECT_M1 = 0.390244
EXPECT_M2 = 0.2
EXPECT_M3 = 4
EXPECT_M4 = 0.104545
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17/r18/r19/r20 已测行（dev-r19/run 在案行装载；排序现状对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
EXPECT_R18_MEASURED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                       "M4": 0.277778}
EXPECT_R19_MEASURED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                       "M4": 0.211111}
EXPECT_R20_MEASURED = {"M1": 0.636364, "M2": 0.285714, "M3": 6,
                       "M4": 0.25}
EXPECT_R19_DROP_REFERENCE = 0.309891
EXPECT_R18_DROP_REFERENCE = 0.126268
EXPECT_R22_M1_ABSOLUTE_DROP = 0.381185
# 判据 (g) 支 M1 阈值与 (p) 支带宽（6 位定点；与 s77 同锚）
REJECT_M1_MIN_6DP = 771_429
REPL_BAND_LO_6DP = 361_538
REPL_BAND_HI_6DP = 561_538
CONTACT_MAX_REPL = 7
# r19 supported 门 0.20（M4 双样本对照用；6 位定点）
SUPPORTED_M4_MAX_6DP = 200_000
EXPECT_COUNTS = {"top-i1": 11, "top-i2": 10, "top-i3": 20,
                 "bottom-i1": 0, "bottom-i2": 4, "bottom-i3": 6}
EXPECT_ABSTAIN = {"top-i1": 5, "top-i2": 4, "top-i3": 7,
                  "bottom-i1": 0, "bottom-i2": 2, "bottom-i3": 0}
EXPECT_RATES = {"top-i1": 0.454545, "top-i2": 0.4, "top-i3": 0.35,
                "bottom-i1": None, "bottom-i2": 0.5, "bottom-i3": 0.0}
EXPECT_TOP_INSTANCE_RATES = {"top-i1": 0.454545, "top-i2": 0.4,
                             "top-i3": 0.35}
EXPECT_TYPE_COUNTS = {"contact": 2, "existence": 14, "other_layer": 0}
EXPECT_BLACK_DOT_BY_INSTANCE = {"bottom-i1": 0, "bottom-i2": 2,
                                "bottom-i3": 0, "top-i1": 0,
                                "top-i2": 2, "top-i3": 0}
EXPECT_RUBRIC_COUNTS = {"contact": 2, "existence_blackdot": 4,
                        "existence_other": 12, "other": 0,
                        "semantic_confusion": 0}
EXPECT_BRANCH_COUNTS = {"branch1_gap_report": 6,
                        "branch2_intrusion_report": 1,
                        "branch3_residual_abstain": 2}
# G2 破坏 2 条出局条目（run-r22 channel_1_geometry_gate 实测装载交叉
# 核对；现象摘录=对应 reader-raw 件 location_evidence 原文逐字）
EXPECT_G2_REJECTED_ENTRIES = [
    {"flag_id": "R22T-002", "instance": "top-i3", "state": "applied",
     "category": "silk_readability",
     "gt_id": "GT-REVC-AP-7-C31U4", "gt_category": "courtyard_crowding",
     "area_ratio": 16.406371, "containment": 0.804462,
     "phenomenon": ("左中被动件密集区内多枚位号小字相互叠压并压在焊盘与"
                    "走线上（C74/C32 一带），难以逐字辨读。")},
    {"flag_id": "R22T-013", "instance": "top-i3", "state": "prep1",
     "category": "silk_readability",
     "gt_id": "GT-REVC-P1-L1SHORT", "gt_category": "other_advisory",
     "area_ratio": 16.369542, "containment": 1.0,
     "phenomenon": ("右下区域竖排/横排位号小字（C28、L17、C36 一带）压在"
                    "焊盘与走线上，辨读受阻。")},
]
EXPECT_G1_R22 = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_G1_BASELINE = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_G1_R20_BROKEN = {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
# GT 命中明细（union=agreement=1/13；双实例命中）
EXPECT_GT_HIT_GT_ID = "GT-REVC-P1-L1SHORT"
EXPECT_GT_HIT_FLAGS = {("R22T-007", "top-i2", "prep1"),
                       ("R22T-017", "top-i3", "prep1")}
# 通道门计数（几何门/类别门/视角门，r22 vs r19 vs r20）
EXPECT_GATES_R22 = {"geometry": 2, "category": 4, "view": 1}
EXPECT_GATES_R19 = {"geometry": 0, "category": 2, "view": 0}
EXPECT_GATES_R20 = {"geometry": 0, "category": 0, "view": 0}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s78-cal-r22-devrecord] FAIL: {msg}")


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
# 复制性结论逻辑（纯函数；供本件登记值复算与构造用例复用）
# ---------------------------------------------------------------------------

def replication_verdict_fixed_point(abst_top: int, flags_top: int,
                                    contact: int, guards_ok: bool) -> tuple:
    """主通道复制性三分判据（纯函数；布尔合成与 s77.
    adjudicate_replication 同判据同锚——判据原文=r22-prep-record
    hypothesis_test.adjudication；6 位定点整数交叉相乘避免浮点）。

    (p) replicated=M1 带内 [361538, 561538] 且 contact≤7 且守门维持；
    (g) regressed=M1 ≥771429（r16 基线）或 G1/G2 任一破坏（支序最高，
    regressed_guards 先于 regressed_m1）；
    (d) drifted=未达 replicated 且 M1 <771429 且守门维持。
    返回 (verdict, branch_key)；本函数与 run-r22 盘上裁决互为交叉核对。
    """
    m1_ge_reject = abst_top * 1_000_000 >= REJECT_M1_MIN_6DP * flags_top
    m1_in_band = (abst_top * 1_000_000 >= REPL_BAND_LO_6DP * flags_top
                  and abst_top * 1_000_000 <= REPL_BAND_HI_6DP * flags_top)
    crit_regressed_guards = not guards_ok
    crit_regressed_ok = crit_regressed_guards or m1_ge_reject
    crit_replicated_ok = (guards_ok and m1_in_band
                          and contact <= CONTACT_MAX_REPL)
    crit_drifted_ok = (guards_ok and not crit_replicated_ok
                       and not m1_ge_reject)
    if crit_regressed_ok:
        return ("regressed",
                "regressed_guards" if crit_regressed_guards
                else "regressed_m1")
    if crit_replicated_ok:
        return ("replicated", "replicated")
    if crit_drifted_ok:
        return ("drifted", "drifted")
    raise RuntimeError("复制性判定未覆盖（带宽/M1/G/contact 组合未落入"
                       "任一预注册支）")


def _view_abstain_aggregate(run: dict, view: str):
    names = [n for n in INSTANCE_ORDER if n.startswith(view)]
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run16: dict, run19: dict, run20: dict,
                  prep: dict, dev19: dict, dev20: dict, typology: dict,
                  guidance_sha: str, axis_sha: str, typology_sha: str,
                  run22_sha: str) -> None:
    # ---- run-r22 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r22":
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
    if ht["hypothesis_id"] != \
            "r20-dev-record-candidate-r19-config-same-guidance-repeat":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "regressed":
        _fail("verdict != regressed")
    if "唯一正式裁决" not in ht["verdict_text"]:
        _fail("verdict_text 应含「唯一正式裁决」")
    m = ht["measurement"]
    if (m["crit_regressed_guards_broken"] is not True
            or m["crit_regressed_m1_ge_0_771429"] is not False
            or m["crit_replicated_m1_in_band"] is not True
            or m["crit_replicated_contact_le_7"] is not True
            or m["crit_drifted_m1_lt_0_771429"] is not True):
        _fail("复制性判据布尔不符（G 破坏=True；M1 ≥0.771429=False；"
              "M1 带内=True；contact≤7=True；M1<0.771429=True）")
    if not m["letter_branch"].startswith("(g)"):
        _fail("落支应为 (g) 支")
    if "G1/G2 任一破坏" not in m["letter_branch"] or \
            "不可复制" not in m["letter_branch"]:
        _fail("落支文本应含 G1/G2 破坏+量级不可复制结论")
    if m["verdict"] != "regressed":
        _fail("measurement.verdict != regressed")
    # 复制性结论纯函数交叉核对（实际输入=G2 破坏→regressed_guards；
    # 构造反事实 G2 维持→replicated=分岔两侧可复算）
    if replication_verdict_fixed_point(16, 41, 2, False) != \
            ("regressed", "regressed_guards"):
        _fail("复制性纯函数实际输入复算不符（G2 破坏→regressed_guards）")
    if replication_verdict_fixed_point(16, 41, 2, True) != \
            ("replicated", "replicated"):
        _fail("复制性纯函数反事实复算不符（G2 维持→replicated）")
    # 本轮实测（top 16/41、bottom 2/10）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R22, EXPECT_TOP_ABSTAIN_R22):
        _fail("top 聚合不符（16/41）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R22, EXPECT_BOTTOM_ABSTAIN_R22):
        _fail("bottom 聚合不符（2/10）")
    if m["top_abstain_rate_r22"] != EXPECT_TOP_RATE_R22 or \
            m["r22_m_tuple_6dp"]["M1"] != EXPECT_TOP_RATE_R22:
        _fail("M1 不符（16/41=0.390244）")
    if m["r22_m_tuple_6dp"] != {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4}:
        _fail("M 元组不符（0.390244/0.2/4/0.104545）")
    if "16/41" not in m["top_abstain_rate_r22_arithmetic"]:
        _fail("M1 算式文本不符")
    if m["m4_top_rate_range_r22"] != EXPECT_M4 or \
            run["view_layer"]["top"]["abstain_rate_range"] != EXPECT_M4:
        _fail("M4=top 极差不符（0.104545）")
    # M4 双样本（r19=0.211111 未过 0.20 门[差 0.011111=在案]；r22=
    # 0.104545 过门=第二次样本过门；如实并列、不改 r19 字母）
    if 104_545 > SUPPORTED_M4_MAX_6DP:
        _fail("M4 双样本对照不符（r22=0.104545 应 ≤0.20=第二次样本过门）")
    if 211_111 <= SUPPORTED_M4_MAX_6DP:
        _fail("M4 r19 参照不符（0.211111>0.20 差 0.011111=在案事实）")
    # 整数交叉相乘复核（避免浮点）：(g) 支 M1 门 16×10^6 < 771429×41
    # （未中）；(p) 带内 361538×41 ≤ 16×10^6 ≤ 561538×41；contact 2≤7
    if 16 * 1_000_000 >= REJECT_M1_MIN_6DP * 41:
        _fail("(g) M1 门复核不符（应 16×10^6<771429×41=未中）")
    if not (REPL_BAND_LO_6DP * 41 <= 16 * 1_000_000
            <= REPL_BAND_HI_6DP * 41):
        _fail("(p) M1 带内复核不符（361538×41≤16×10^6≤561538×41）")
    if not 2 <= CONTACT_MAX_REPL:
        _fail("contact 门复核不符（2≤7）")
    # 基线双侧复算（同一聚合逻辑对 run-r16 内嵌输入重算）
    f16, a16 = _view_abstain_aggregate(run16, "top")
    if (f16, a16) != (35, 27) or \
            m["top_abstain_rate_r16_baseline_live"] != \
            EXPECT_TOP_R16_BASELINE_LIVE or \
            m["top_abstain_rate_r16_baseline_value"] != \
            EXPECT_TOP_R16_BASELINE_VALUE:
        _fail("top r16 基线复算不符（27/35）")
    fb16, ab16 = _view_abstain_aggregate(run16, "bottom")
    if (fb16, ab16) != (14, 12):
        _fail("bottom r16 基线复算不符（12/14）")
    # r19 参照元组=run-r19 内嵌实例记录 live 复算+登记交叉核对
    f19, a19 = _view_abstain_aggregate(run19, "top")
    fb19, ab19 = _view_abstain_aggregate(run19, "bottom")
    if (a19, f19) != (18, 39) or (ab19, fb19) != (4, 7):
        _fail("r19 live 复算不符（18/39、4/7）")
    if m["r19_reference_tuple"] != EXPECT_R19_MEASURED:
        _fail("r19 参照元组登记不符")
    # r20 对照行=run-r20 live 复算+登记交叉核对
    f20, a20 = _view_abstain_aggregate(run20, "top")
    fb20, ab20 = _view_abstain_aggregate(run20, "bottom")
    if (a20, f20) != (14, 22) or (ab20, fb20) != (4, 14):
        _fail("r20 live 复算不符（14/22、4/14）")
    # contact 族（另列主度量对照）：实测 2、基线 10、链重放 8/15/5/10
    if m["contact_family_abstain_flags_rubric_r22"] != EXPECT_CONTACT_R22 \
            or m["contact_r16_baseline_registered"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            m["contact_r16_baseline_live_replay"] != \
            EXPECT_CONTACT_CHAIN_R13_R16:
        _fail("contact 实测/基线/链重放不符（2、10、8/15/5/10）")
    # 逐实例旗数/弃权率与 r22 对照（bottom-i1 零旗=None 口径触发）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN or \
            rates != EXPECT_RATES:
        _fail("逐实例旗数/弃权率不符")
    # 零旗标派次=2（bottom-i1 两板；item 5 零分母→None 口径触发）
    parts = run["reader"]["zero_flag_parts"]["parts"]
    if [(p["instance"], p["state"]) for p in parts] != \
            [("bottom-i1", "applied"), ("bottom-i1", "prep1")]:
        _fail("零旗标派次不符（bottom-i1 两板）")
    # 代表配置与门（top-i1+bottom-i2；双双非 tie）
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (15, 7, 0.466667, 0.0, 0.0):
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
    # 守门通道（G1 维持=0/0/0；G2 破坏=0→2；guards_ok=False）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not False or \
            gc["guards_ok"] is not False or \
            gc["g2_geometry_gate_r19"] != 0 or \
            gc["g2_geometry_gate_r22"] != 2:
        _fail("守门通道不符（G1 维持、G2 0→2 破坏）")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["g1_bottom_courtyard_non_abstain_r22"] != EXPECT_G1_R22 or \
            g12["g1_r16_baseline_live"] != EXPECT_G1_BASELINE or \
            g12["g1_r20_broken_registered"] != EXPECT_G1_R20_BROKEN:
        _fail("守门 G1 实测不符（0/0/0 维持；基线/r20 对照）")
    # GT 双口径：union=agreement=1/13（GT-REVC-P1-L1SHORT 双实例命中）
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (1, 1, 13):
        _fail("双口径不符（union=agreement=1/13）")
    if dual["union"]["gt_ids"] != [EXPECT_GT_HIT_GT_ID] or \
            dual["agreement"]["gt_ids"] != [EXPECT_GT_HIT_GT_ID] or \
            dual["union"]["gt_recall_union"] != 0.076923:
        _fail("GT 命中登记不符（GT-REVC-P1-L1SHORT、1/13=0.076923）")
    hit = [pg for pg in dual["per_gt"] if pg.get("hits")]
    if len(hit) != 1 or hit[0]["matched_by_count"] != 2 or \
            {(h["flag_id"], h["instance"], h["state"])
             for h in hit[0]["hits"]} != EXPECT_GT_HIT_FLAGS:
        _fail("GT 双实例命中明细不符（R22T-007+R22T-017，均 prep1）")
    # G2 出局条目 2 条（逐条与 run 通道归因实测逐一相等，fail-closed）
    gate_entries = run["channel_attribution"]["channel_1_geometry_gate"][
        "r22_area_ratio_rejected_entries"]
    if len(gate_entries) != 2:
        _fail("G2 出局条目数不符（应为 2）")
    for want, got in zip(EXPECT_G2_REJECTED_ENTRIES, gate_entries):
        for k in ("flag_id", "instance", "state", "category", "gt_id",
                  "gt_category", "area_ratio", "containment"):
            if want[k] != got.get(k):
                _fail(f"G2 出局条目 {want['flag_id']} 字段 {k} 不符")
    # 通道门计数（几何/类别/视角；r22 vs r19 vs r20）
    ca = run["channel_attribution"]
    n_cat_r22 = len(ca["channel_2_category_gate"]["r22_category_mismatch_"
                                             "entries"])
    n_cat_r19 = len(ca["channel_2_category_gate"]["r19_category_mismatch_"
                                             "entries"])
    n_cat_r20 = len(ca["channel_2_category_gate"]["r20_category_mismatch_"
                                             "entries"])
    n_view_r22 = len(ca["view_gate_observations"]["r22_entries"])
    n_view_r19 = len(ca["view_gate_observations"]["r19_entries"])
    n_view_r20 = len(ca["view_gate_observations"]["r20_entries"])
    n_geom_r19 = ca["gate_chain_since_r6"][
        "geometry_gate_area_ratio_rejected_by_round"]["r19"]
    n_geom_r20 = ca["gate_chain_since_r6"][
        "geometry_gate_area_ratio_rejected_by_round"]["r20"]
    if (2, n_cat_r22, n_view_r22) != (EXPECT_GATES_R22["geometry"],
                                      EXPECT_GATES_R22["category"],
                                      EXPECT_GATES_R22["view"]):
        _fail("r22 通道门计数不符（2/4/1）")
    if (n_geom_r19, n_cat_r19, n_view_r19) != \
            (EXPECT_GATES_R19["geometry"], EXPECT_GATES_R19["category"],
             EXPECT_GATES_R19["view"]):
        _fail("r19 通道门计数不符（0/2/0）")
    if (n_geom_r20, n_cat_r20, n_view_r20) != \
            (EXPECT_GATES_R20["geometry"], EXPECT_GATES_R20["category"],
             EXPECT_GATES_R20["view"]):
        _fail("r20 通道门计数不符（0/0/0）")
    # 机制观察：援引分记、落支、黑点族、top 分型、rubric 族
    mo = ht["mechanism_observation"]
    cc = mo["criterion_citation_observation"]
    ccounts = cc["citation_counts"]
    if ccounts["flag_level_s5b_literal"] != 0 or \
            ccounts["flag_level_iiia_literal"] != 0 or \
            ccounts["flag_level_branch_literal"] != 0:
        _fail("旗级援引应为全零（§5B/(iii-a)/分支( 三集合全空）")
    if ccounts["notes_level_s5b"] != 0 or ccounts["notes_level_iiia"] != 6:
        _fail("notes 级援引不符（§5B=0/12、(iii-a)=6/12）")
    if "旗级「(iii-a)」6 旗" not in ccounts["baseline_r19_iiia"] or \
            "10/12" not in ccounts["baseline_r19_iiia"]:
        _fail("r19 援引基线对照不符（旗级 6+2、notes 10/12 在案）")
    if cc["branch_counts_flag_level"] != EXPECT_BRANCH_COUNTS or \
            cc["branch1_notes_level_dispatches"] != 2:
        _fail("(iii-a) 落支不符（间隙 6+侵入 1+残余弃权 2；notes 级 2）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 4:
        _fail("黑点族 4 旗全弃权不符（bottom-i2 2+top-i2 2）")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS:
        _fail("rubric 族计数不符（2/4/12/0/0）")
    if rf["replay_proof"]["per_flag_total"] != 132:
        _fail("rubric 重放对拍不符（132 条）")
    ty = mo["top_abstain_typology"]
    if ty["observation"] and "接触性" in ty["observation"]:
        # top 分型登记=接触性 2+存在性 14+其他 0（16 条；观察文本+rows）
        pass
    if len(ty["rows"]) != 16:
        _fail("top 弃权构成分型 16 条不符")
    # 实验对照账：六元组/六行并列/排序（r20、r22 资格门剔除）/复制结论
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r22_measured"]["M1"] != EXPECT_M1 or \
            ecl["r22_measured"]["M2"] != EXPECT_M2 or \
            ecl["r22_measured"]["M3"] != EXPECT_M3 or \
            ecl["r22_measured"]["M4"] != EXPECT_M4 or \
            ecl["r22_measured"]["M1_arithmetic"] != "16/41" or \
            ecl["r22_measured"]["M2_arithmetic"] != "2/10" or \
            ecl["r22_measured"]["contact_family_abstain_flags_rubric"] != \
            2 or ecl["r22_measured"]["existence_other_family"] != 12:
        _fail("实验对照账四元组/另列键不符")
    if ecl["r17_axis1_row"] != EXPECT_R17_MEASURED or \
            ecl["r18_axis2_row"] != EXPECT_R18_MEASURED or \
            ecl["r19_axis3_row"] != EXPECT_R19_MEASURED or \
            ecl["r20_combo_registered_row"] != EXPECT_R20_MEASURED:
        _fail("r17/r18/r19/r20 对照行不符")
    if ecl["r16_baseline_registered"]["M1"] != 0.771429 or \
            ecl["r16_baseline_registered"]["M4"] != 0.261904:
        _fail("r16 基线行不符")
    rk = ecl["ranking_by_comparison_rule"]
    if rk["ranking_order_best_first"] != ["r19_axis3", "r18_axis2",
                                          "r16_baseline", "r17_axis1"] or \
            rk["r20_eligibility"] is not False or \
            rk["r22_eligibility"] is not False:
        _fail("comparison_rule 排序不符（r20/r22 资格门剔除；r19 第一）")
    if "G2" not in rk["r22_eligibility_note"] and \
            "几何门" not in rk["r22_eligibility_note"]:
        _fail("r22 资格门剔除理由应含 G2/几何门")
    rc = ecl["replication_conclusion"]
    if rc["verdict"] != "regressed" or \
            "不可复制" not in rc["conclusion"] or \
            "0.211111" not in rc["m4_second_sample_note"]:
        _fail("复制性结论/M4 双样本单列不符")
    sb = ecl["significant_benefit_vs_r16"]
    if sb["met"] is not True or \
            sb["r22_m1_absolute_drop"] != EXPECT_R22_M1_ABSOLUTE_DROP or \
            sb["r19_drop_reference"] != EXPECT_R19_DROP_REFERENCE or \
            sb["r18_drop_reference"] != EXPECT_R18_DROP_REFERENCE:
        _fail("显著收益不符（0.381185≥0.10；r19 参照 0.309891）")
    # 判据引用=prep-record 原文（逐字一致，共键比对；adjudication 7 键）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "drifted",
              "mechanism_observation_separate", "metric_lesson_separate",
              "m4_second_sample_separate", "regressed", "replicated"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引字节复用锚（8633bda5 本体零改动；mode=byte_reuse_zero_change）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "byte_reuse_zero_change" or \
            gr["base"] != "observation-guidance-r19.md":
        _fail("guidance_reuse 字节复用声明不符")
    if gr["base_sha256"] != guidance_sha or guidance_sha != \
            _sha(REL_GUIDANCE_R19):
        _fail("r19 指引实测 sha 与 8633bda5 锚不符")
    if gr["byte_size"]["delta"] != 0:
        _fail("指引字节复用 delta 应为 0")
    if prep["changed_variables"] != [] or \
            prep["no_instrument_change"] is not True:
        _fail("changed_variables=0/no_instrument_change 不符")
    if "R22T" not in gr["verbatim_scope_note"] or \
            "派发指令层覆盖" not in gr["verbatim_scope_note"]:
        _fail("§6 前缀差异登记不符（R19T 落盘原文 vs R22T 派发层覆盖）")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R22):
        _fail("prep-record sha 实测与登记不符")
    if gr["chain_anchors"]["axis_experiment_plan_frozen_r21_slot"][
            "path_rel"] != REL_AXIS_PLAN or axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    # 跳号声明（r21=冻结预留条件位、未执行；冻结原文在 prep 链锚）
    slot = gr["chain_anchors"]["axis_experiment_plan_frozen_r21_slot"][
        "r21_slot_frozen_quotes"]
    if "R21（三轴全组合）" not in slot["combination_decision_rule."
                                       "ii_full_combination"] or \
            "R21 不做" not in slot["early_stop_rule."
                                   "strong_single_axis_shortcut"]:
        _fail("r21 槽位冻结原文锚不符")
    if "R21 不做" not in prep["round_nature"] or \
            "跳号" not in prep["round_nature"]:
        _fail("prep 跳号声明不符")
    # 执行授权链（dev-r20 next_iteration_targets[1] 同指引重复轮候选）
    cand = dev20["next_iteration_targets"][1]
    if "同指引重复轮" not in cand or "由用户拍板" not in cand:
        _fail("dev-r20 重复轮候选授权原文不符")
    if dev20["round_id"] != "2026-09-09-r20" or \
            dev20["hypothesis_test_i"]["verdict"] != "reject":
        _fail("dev-r20 先验件常量不符")
    if dev19["round_id"] != "2026-09-09-r19" or \
            dev19["hypothesis_test_i"]["verdict"] != "marginal":
        _fail("r19 dev-record 先验件常量不符")
    # 联合评价趋势历史行（dev-r20 冻结转录 r5–r20）
    trend_rows_prior = dev20["joint_evaluation_trend"]["by_round"]
    if [r["round"] for r in trend_rows_prior] != [
            "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "r16", "r17", "r18", "r19", "r20"]:
        _fail("趋势历史行（dev-r20）不符")
    # typology 基线锚
    if typology["matrix"]["round_totals"]["r16"]["families"]["contact"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            typology_sha != _sha(REL_TYPOLOGY):
        _fail("typology contact 基线/实测 sha 不符（r16=10）")
    # run-r22 盘上件哈希=简报锚（80a12c05）
    if not run22_sha.startswith("80a12c05"):
        _fail("run-r22 实测 sha 与 80a12c05 锚不符")


def build_dev_record() -> dict:
    """构建 round22-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    run = _json_load(REL_RUN_R22)
    run16 = _json_load(REL_RUN_R16)
    run19 = _json_load(REL_RUN_R19)
    run20 = _json_load(REL_RUN_R20)
    prep = _json_load(REL_PREP_R22)
    dev19 = _json_load(REL_DEV_R19)
    dev20 = _json_load(REL_DEV_R20)
    typology = _json_load(REL_TYPOLOGY)
    guidance_sha = _sha(REL_GUIDANCE_R19)
    axis_sha = _sha(REL_AXIS_PLAN)
    typology_sha = _sha(REL_TYPOLOGY)
    run22_sha = _sha(REL_RUN_R22)
    _verify_facts(run, run16, run19, run20, prep, dev19, dev20, typology,
                  guidance_sha, axis_sha, typology_sha, run22_sha)

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

    # 联合评价趋势：r5–r20 行=round20-dev-record 在案行（冻结转录）；
    # r22 行=本轮 run 实测
    trend_rows = list(dev20["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17",
                                            "r18", "r19", "r20"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r22",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R22, "sha256": run22_sha},
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
            "全旗标合计口径仅作附记（18/51=0.352941，非弃权 33+弃权 18）；"
            "本轮预注册主通道=复制性三分判据（(g) G2 破坏→regressed——"
            "M1 带内与 contact 门两判据虽命中、支序 regressed 在前；"
            "bottom 全旗聚合弃权率 2/10=0.2 为侧观察度量[M2，improved "
            "方向]）；实例层/视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 0.5=0.5−0.0（bottom-i1 两板零旗标→"
                     "弃权率=None[零分母口径]、bottom-i2/i3=0.5/0.0——"
                     "min/max 按可计算实例计算，不编造数值；bottom 中位"
                     "数=None=含 None 实例的视角层口径触发）；top 极差 "
                     "0.104545=0.454545−0.35（top-i1/i2/i3=0.454545/0.4/"
                     "0.35）——两视角极差均收窄（top 0.25→0.104545、"
                     "bottom 1.0→0.5），M4 双样本如实并列"),
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
                 "序）；R22T/R22B 前缀由派发指令层覆盖（指引=guidance-r19 "
                 "字节复用、其 §6 示例旗 ID 前缀保持 R19T-/R19B- 落盘原"
                 "文=前缀差异登记、r16 先例在案，与 r20「随指引落盘固化」"
                 "路径不同）；flag_id 编号行为=5 个有旗实例全部同实例跨板"
                 "连续+bottom-i1 两板零旗标（编号无可登记）（与 prep-"
                 "record naming「同实例跨板连续」声明相符）；本轮无派发操"
                 "作事故；v1.2 工具规约沿用 12/12 派次自述合规与输出格式"
                 "披露如实登记为混杂因素披露，不作废"),
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
            "measurement_design item 4；top 旗数中位 11=top-i1 唯一、"
            "bottom 旗数中位 4=bottom-i2 唯一——双非 tie、按先序规则选取"
            "如实登记）"),
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

    # G2 分岔记录（关键机制观察，照 r20 的 g1_bifurcation_record 先例，
    # 如实单列不凌驾字母裁决）
    g2_bifurcation_record = {
        "bifurcation": (
            "冻结支文把 G1/G2 破坏与「r19 量级不可复制、轴3 收益判定降级"
            "为单轮现象」捆绑为同一结论文本，而本轮 M1 分量与该解释相悖："
            "M1=0.390244 落复制带 [0.361538, 0.561538] 内（甚至优于 r19 "
            "的带中心 0.461538）+contact=2≤7+G1 维持——若 G2 不破坏，同"
            "一输入字面落 replicated（replication_verdict_fixed_point("
            "16, 41, 2, True)=('replicated','replicated') 构造可复算）；"
            "唯 G2 破坏（几何门出局条目 0→2）触发字母——字母=regressed "
            "（唯一正式裁决）与 M1 复制事实=机制观察，两账分列"),
        "counts": {
            "contact_family_abstain_flags_rubric_r22": 2,
            "contact_le_7": True,
            "g1_bottom_courtyard_non_abstain_r22": dict(EXPECT_G1_R22),
            "g1_baseline_r16_live": dict(EXPECT_G1_BASELINE),
            "g2_geometry_gate_r19": 0,
            "g2_geometry_gate_r22": 2,
            "m1_in_replication_band": True,
            "m1_r22": EXPECT_M1,
            "m1_r19_band_center": EXPECT_R19_MEASURED["M1"],
            "replication_band": "[0.361538, 0.561538]（r19±0.10）",
        },
        "counterfactual_check": {
            "function": "replication_verdict_fixed_point",
            "guards_ok_false": ["regressed", "regressed_guards"],
            "guards_ok_true": ["replicated", "replicated"],
            "note": ("同一 M1/contact 实测输入下守门布尔翻转即字母翻转="
                     "本轮分岔的最小构造证明；纯函数、构造可测"),
        },
        "declared_date": DECLARED_DATE,
        "letter_vs_fact": {
            "letter": ("regressed（(g) regressed_guards 支；唯一正式裁"
                       "决，轮后不改写；后续任何机制归因不得改判本轮字"
                       "母）"),
            "m1_replication_fact": ("M1 量级复制成立（0.390244∈"
                                    "[0.361538, 0.561538]、且优于 r19 带"
                                    "中心 0.461538；contact 族 2≤7；G1 "
                                    "维持 0/0/0）——机制观察单列、不进字"
                                    "母、不改写字母"),
            "status": ("两账分列、不合并、不改写（照 r20 g1_bifurcation_"
                       "record「字母/机制教训分列」先例）"),
        },
        "observation": (
            "G2 字面破坏与 M1 复制并存的分岔：守门 G2 的设计针对的是报告"
            "框质量（top 视非弃权旗标 frame_box_pct 几何门=负责任报告的"
            "报告框 hygiene 守门，出局条目不得回升，对照 r6–r20 链在"
            "案）；而本轮 M1/contact/G1 三项复制性判据全部满足——冻结支"
            "文「任一守门破坏→r19 量级不可复制」的解释在本轮 M1 分量上"
            "失去对应（量级复现与守门破坏同时发生）"),
        "rejected_entries_excerpt": [
            {
                "area_ratio": e["area_ratio"],
                "category": e["category"],
                "containment": e["containment"],
                "corresponding_phenomenon": e["phenomenon"],
                "flag_id": e["flag_id"],
                "gt_category": e["gt_category"],
                "gt_id": e["gt_id"],
                "instance": e["instance"],
                "phenomenon_source": (
                    f"reader-raw-r22-{'applied' if e['state'] == 'applied' else 'prep1'}-"
                    f"{e['instance']}.txt location_evidence 原文逐字"),
                "state": e["state"],
            }
            for e in EXPECT_G2_REJECTED_ENTRIES
        ],
        "role": ("机制教训单列：不凌驾、不改写字母裁决（regressed 维持唯"
                 "一正式裁决）；不进任何度量；描述性记录、非因果证明"),
        "trigger_source": ("守门 G2 破坏（top 几何门面积比出局条目 R19=0"
                           "→R22=2；两条均 silk_readability 类、area_ratio"
                           ">10）——非 M1 量级漂移"),
    }

    # 三轴实验总收束位（comparison_rule 排序不变；r22 不入排序；轴3
    # 收益归因状态两账并列）
    three_axis_experiment_closeout = {
        "attribution_status_axis3_benefit": (
            "轴3 收益的归因状态=「M1 量级在新鲜实例群复现（机制方向支"
            "持）但守门字面降级（预注册字母=regressed）」——两账并列、"
            "不合并、不改写：M1=0.390244 落复制带内（机制方向支持）与 "
            "G2 几何门 0→2 破坏（守门字面降级）在本轮数据中同时显形；"
            "同指引重复轮的收敛归因判据按预注册字母回答=「未获复制支"
            "持」，而 M1 分量的机制观察单列为「量级复现成立」——两账并"
            "列由 g2_bifurcation_record 承载，后续轮次不得合并改写"),
        "comparison_rule_note": (
            "比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json "
            "为准（b6ec6467；FROZEN=先于 R17–R21 任何实验轮盲读冻结）；"
            "r22 在该计划时间界之外（r21 槽位永久留空后的收束观察轮），"
            "本轮结果仅登记于对照账、不触发任何计划内规则分支"),
        "development_domain_discipline": (
            "按协议 v1 §4，本批证据属 development 域，不得冒充未见留出；"
            "in_calibrated_range 恒 False 直到正式采纳（须人工批准）；"
            "达标证据仍须留出集"),
        "final_conclusion_unchanged": (
            "三轴实验最终结论维持=收益最大配置=轴3 单变量（guidance-r19，"
            "M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4；按冻结 "
            "iv_final_selection 全部已测配置中排序最优者）——r22 同指引"
            "重复轮不改变该收束（r22 不入排序、字母=regressed），仅在机"
            "制观察层新增「M1 量级复现+G2 报告框 hygiene 问题暴露」两项"
            "事实"),
        "ranking": {
            "eligible_rows": ["r16_baseline", "r17_axis1", "r18_axis2",
                              "r19_axis3"],
            "excluded_rows": {
                "r20_combo": "G1 破坏（2/0/0，run-r20 在案）",
                "r22_repeat": "G2 破坏（几何门 0→2，本轮实测）",
            },
            "ranking_order_best_first": ["r19_axis3", "r18_axis2",
                                         "r16_baseline", "r17_axis1"],
            "status": ("comparison_rule 排序不变（r19_axis3 第一）；r22 "
                       "不入排序（G2 破坏=资格门剔除、行仅如实入账）"),
        },
        "role": ("三轴实验总收束位（development 域描述性边界工具、非门、"
                 "无字母语义、不凌驾 APR-0011 与阈值；两账并列、不合并、"
                 "不改写）"),
    }

    # 下一候选建议（如实单列、由用户拍板、本包不预写决策）
    next_candidate_suggestion = {
        "context": (
            "r22 同指引重复轮字母=regressed（G2 破坏；M1 带内复制与 G1/"
            "contact 维持在案=g2_bifurcation_record 两账分列）；三轴实验"
            "已收束（收益最大配置=r19_axis3 在案）；开发线收敛（连续达标="
            "0、正式采纳门槛未达）——下一动作如实单列、由用户拍板、本包"
            "不预写决策"),
        "decision_authority": "由用户拍板（本包只列选项、不预写决策）",
        "options": [
            {
                "motivation": ("字母=regressed 且轴3 收益归因状态已两账并"
                               "列登记；留出集时机=开发线收敛（须用户拍板"
                               "在案；HOLDOUT-PLAN.md a4b80193 Tier 1/2 "
                               "候选清单零接触在案）；in_calibrated_range "
                               "恒 False 直到正式采纳（须人工批准）"),
                "option": ("接受发展域现状收束训练环（不再追加迭代轮）；"
                           "留出集时机由用户判断"),
                "preregistration_required": False,
            },
            {
                "motivation": ("G2 破坏 2 条出局条目均为 silk_readability "
                               "负责任报告、area_ratio>10（16.406371/"
                               "16.369542；frame_box_pct 报告框过大形态）"
                               "——若机制归因确认属报告框 hygiene 而非判"
                               "据问题（对照 r6–r20 几何门链仅 r14=1），"
                               "处置轴=派发层框收敛指引（非判据修订）；须"
                               "新预注册轮（prep-record 先于盲读冻结）"),
                "option": ("对 G2 的 2 条出局条目做机制归因（reader 负责任"
                           "报告的 frame_box_pct 过大触发 area_ratio>10"
                           "核实）；属报告框 hygiene 则处置轴=派发层框收"
                           "敛指引、须新预注册轮"),
                "preregistration_required": True,
            },
            {
                "motivation": ("M1 带内复制基于 n=2 同指引重复（r19/r22）"
                               "——第三样本可进一步分离「量级复制」与「实"
                               "例群漂移」（r15→r16 纯重抽漂移 0.09064 在"
                               "案参照；部分重复≠独立重复、验证力度如实）"
                               "；M4 双样本（0.211111/0.104545）亦待第三"
                               "样本"),
                "option": ("再一轮同指引重复轮（三样本；r16 先例同型）——"
                           "配置与 r22 完全同构（指引/渲染字节复用、仅实"
                           "例重抽）"),
                "preregistration_required": True,
            },
        ],
        "status": ("下一候选建议（非冻结规则输出——三轴计划已收束、本轮"
                   "为计划外收束观察轮；本节为 dev-record 如实登记的选项"
                   "清单）"),
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 6 派次全部旗标中弃权旗占比"
                "（6 位小数；本轮实测 16/41）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 2/10）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径=分型件 round_totals "
                "{r}.families.existence_blackdot；本轮实测 4、全弃权；M3 "
                "槽位定义维持冻结件黑点口径——contact=2 另列不占槽=判据侧"
                "对照账纪律延续）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差=max−min（本轮实测 0.454545−0.35="
                "0.104545）",
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
                "r20_combo": dict(EXPECT_R20_MEASURED),
                "r22_repeat": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                               "M3": EXPECT_M3, "M4": EXPECT_M4},
            },
            "note": ("六行并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合/"
                     "r22 重复轮）；按冻结 comparison_rule=(M1 升序, M2 "
                     "升序, M3 升序, M4 升序) 字典序：r20/r22=G 守门破坏经"
                     "资格门剔除不入排序；排序（不含 r20/r22）=r19 轴3 第"
                     "一、r18 轴2 第二、r16 基线参照行第三、r17 轴1 末位"
                     "（M1=0.88 劣于基线=负向）——排序不变、如实登记、不"
                     "预写后续决策"),
            "role": ("重复轮 M 元组六行并列登记（comparison_rule 冻结规则"
                     "的已测行并列；r16–r20 行=dev-r19/dev-r20 在案行实测"
                     "装载+各自 run 内嵌记录 live 复算交叉核对、r22 行=本"
                     "轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r22.json（80a12c05…）盘上值"
            "装载（M1=16/41=0.390244 与 m.top_abstain_rate_r22、M2=2/10="
            "0.2 与 m.r22_m_tuple_6dp.M2、M3=4 与 black_dot_tracking."
            "rubric_families（rubric 口径 existence_blackdot、r13–r16 132 "
            "条弃权旗重放对拍逐一相等）、M4=0.104545 与 view_layer.top."
            "abstain_rate_range、contact=2 与 contact_family_abstain_"
            "flags_rubric_r22 逐一相等，fail-closed），非手抄；axis-plan "
            "在案 r16 基线四键 [0.771429, 0.857143, 12, 0.261904] 与 "
            "run-r22 baseline_cross_check 交叉核对一致；M1 绝对降幅 "
            "0.771429−0.390244=0.381185 超显著收益阈值 0.10（描述层命中、"
            "与字母裁决分列互不改写——r18/r19/r20 先例延续；跨轮实例群漂"
            "移混杂照旧声明、本轮恰以实例群重抽为唯一实验操作与裁决变量；"
            "主判据=复制性三分判据、G2 破坏→regressed）"),
        "next_candidate_r22": (
            "见 next_candidate_suggestion（三选项如实单列、由用户拍板、"
            "本包不预写决策）"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "r22 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "significant_benefit_vs_r16": {
            "definition": "「显著收益」=相对 r16 基线 M1 绝对降幅 ≥0.10（"
                          "阈值覆盖跨轮实例群漂移噪声的历史幅度，参照 "
                          "r15→r16 纯重抽变动 0.09064）",
            "met": True,
            "note": ("r22 M1 绝对降幅 0.381185 ≥0.10=显著收益定义在描述层"
                     "命中（r18 降幅 0.126268、r19 降幅 0.309891 亦 ≥0.10）"
                     "；字母裁决与实验账分列互不改写"),
            "r18_drop_reference": EXPECT_R18_DROP_REFERENCE,
            "r19_drop_reference": EXPECT_R19_DROP_REFERENCE,
            "r22_m1_absolute_drop": EXPECT_R22_M1_ABSOLUTE_DROP,
        },
        "status": ("R22 实测 (M1,M2,M3,M4)=(0.390244, 0.2, 4, 0.104545)"
                   "（contact=2 另列）；r22 资格门剔除不入排序（G2 破坏）；"
                   "排序不变=r19_axis3 第一（如实记录）；字母与实验账分列"
                   "互不改写（本轮 regressed 但 M1 带内复制成立——两账分"
                   "列由 g2_bifurcation_record 承载）；三轴实验已收束"
                   "（收益最大配置=r19_axis3 维持）"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4},
    }

    # 机制观察单列（M4 双样本/三族对照/黑点/援引）
    mechanism_observation_r22 = {
        "citation_counts_vs_r19": {
            "r22_measured": {
                "branch_counts_flag_level": dict(EXPECT_BRANCH_COUNTS),
                "flag_level_branch_literal": 0,
                "flag_level_iiia_literal": 0,
                "flag_level_s5b_literal": 0,
                "notes_level_iiia": "6/12 派次",
                "notes_level_s5b": "0/12 派次（指引字节复用无 §5B 节=任何"
                                   "援引为零上下文）",
            },
            "r19_baseline_registered": {
                "flag_level": "旗级「(iii-a)」6 旗+「分支(」2 旗",
                "notes_level": "notes 级 10/12 派次",
                "source": "run-r19/r22-prep-record run_r19_metric_anchor "
                          "在案",
            },
            "status": ("§5B 与 (iii-a) 援引计数分开记、对照 r19 基线如"
                       "实；不进字母裁决"),
        },
        "m4_second_sample": {
            "note": ("M4 双样本单列（per adjudication.m4_second_sample_"
                     "separate 原文）：r19=0.211111 vs r22=0.104545——r22 "
                     "过 ≤0.20 supported 门=第二次样本过门（r19 的 supported "
                     "门 0.20 差 0.011111 在案、字母=marginal 维持不变）；"
                     "两样本分布如实并列、不进字母裁决、不因双样本改门、不"
                     "挑优、不合并分布"),
            "r19": 0.211111,
            "r19_pass_gate": False,
            "r22": EXPECT_M4,
            "r22_pass_gate": True,
            "supported_gate": 0.2,
        },
        "rubric_families_vs_baselines": {
            "r19_registered": {"contact": 4, "existence_blackdot": 4,
                               "existence_other": 14},
            "r20_registered": {"contact": 2, "existence_blackdot": 6,
                               "existence_other": 10},
            "r22_measured": {"contact": 2, "existence_blackdot": 4,
                             "existence_other": 12},
            "status": ("三族计数（分型件 rubric 口径）对照 r19（4/4/14）"
                       "与 r20（2/6/10）：contact 2=与 r20 持平、低于 "
                       "r19；黑点 4=与 r19 持平；存在性其他 12=介于两基"
                       "线间——如实登记"),
        },
        "black_dot_observation": {
            "bottom_blackdot_still_existence_abstain": (
                "bottom 黑点仍存在性弃权（bottom-i2 两板 2 条：R22B-002/"
                "R22B-004 黑点-焊盘贴近存在性弃权）——guidance-r19 无 §5B "
                "节、黑点仪器注记不在本轮指引中=黑点弃权构成与 r19 同构如"
                "实"),
            "by_instance": dict(EXPECT_BLACK_DOT_BY_INSTANCE),
            "counts": "黑点族弃权旗 4 条（全弃权；top-i2 2+bottom-i2 2）",
        },
        "role": ("机制观察单列（per r22-prep-record adjudication."
                 "mechanism_observation_separate 原文）：不进字母裁决、"
                 "不凌驾、不改写字母"),
        "top_abstain_typology_r22": {
            "counts": dict(EXPECT_TYPE_COUNTS),
            "note": ("top 弃权 16 条逐旗分型：接触性 2+存在性 14+层归属其"
                     "他 0（对照 r19 5/13/0、r20 4/9/1——存在性占比上升、"
                     "接触性收敛，如实单列）"),
        },
    }

    # GT 命中里程碑（agreement 口径首次计入）
    gt_agreement_milestone = {
        "agreement_first_counted": (
            "GT 条目层 agreement 口径（≥2/3 实例命中才计）自 r12 引入以来"
            "首次计入：union=agreement=1/13（GT-REVC-P1-L1SHORT，"
            "prep1-top-i2 R22T-007+prep1-top-i3 R22T-017 双实例命中）——"
            "r12 以来第二次逐实例命中（r19 R19T-009 单实例命中=仅 union "
            "计入）、且首次两实例一致命中，如实登记（单实例命中不稳定→双"
            "实例一致的改善方向如实描述，非因果证明、非能力断言）"),
        "gt_id": EXPECT_GT_HIT_GT_ID,
        "hit_flags": sorted(f"{i}:{f}:{s}" for f, i, s
                            in EXPECT_GT_HIT_FLAGS),
        "recall": {"agreement": 0.076923, "union": 0.076923},
        "structural_note": ("bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
                            "side=top、bottom GT 无源在案 gt-audit-r1）；"
                            "GT 侧维持全关闭声明延续（gt-audit-r1 三候选"
                            "全部关闭、r9–r22 延续零改动、非新 GT）"),
    }

    honest_conclusion = (
        "本轮（development 域同指引重复轮=收敛归因轮[第二十二轮；r16 先"
        "例：r15→r16 同指引重复、渲染零变更、仅实例重抽]；变更=零（判读"
        "指引=observation-guidance-r19.md 字节复用[8633bda5 本体零改动、"
        "零新建指引文件；§6 示例旗 ID 前缀保持 R19T-/R19B- 落盘原文、"
        "R22 派次前缀 R22T/R22B 由派发指令层覆盖=前缀差异登记、r16 先例"
        "在案]+渲染零变更=renders-r14b 四图字节复用[与 r14–r20 盲读同一"
        "批文件]+GT/阈值/协议零变更（13 条冻结、v1.1+v1.2 维持）；"
        "changed_variables=0；唯一实验操作=reader 实例群重抽 12 派次；"
        "【跳号声明】r21=axis-plan 冻结件预留的 R21 全组合条件位——per "
        "early_stop_rule.strong_single_axis_shortcut 未触发、槽位永久留"
        "空，r22 与该位无涉）12 派次 51 旗标中 18 弃权、33 非弃权：代表"
        "配置（top-i1+bottom-i2 双非 tie 如实）gt_recall=0.0（0/13）、"
        "seed_match_rate=0.0（0/8，诊断口径，禁称 precision/FPR）、"
        "abstain_rate=0.466667（7/15），联合评价 not_met（gt_recall、"
        "seed_match_rate 两项未达 APR-0011 暂行线；gt_count 13≥12 与 "
        "abstain_rate 0.466667≤0.5 单分项入线；诊断对照，非采纳门；连续"
        "达标计数 0→0；GT 条目层 union=agreement=1/13 双口径并列——"
        "GT-REVC-P1-L1SHORT 双实例命中=agreement 口径自 r12 引入以来首次"
        "计入、r12 以来第二次逐实例命中、首次两实例一致命中，如实登记）。"
        "预注册假设（r20-dev-record-candidate-r19-config-same-guidance-"
        "repeat）复制性三分判据裁决（按 r22-prep-record hypothesis_test."
        "adjudication 原文）=regressed（字母口径，唯一正式裁决，轮后不改"
        "写）：落支=(g) regressed_guards（任一守门破坏；支序先行）——本"
        "轮=G2 破坏（top 几何门面积比出局条目 R19=0→R22=2；R22T-002 "
        "16.406371/R22T-013 16.369542 均 silk_readability 负责任报告、"
        "逐条摘录入 g2_bifurcation_record）；而 M1=0.390244（16/41）落复"
        "制带 [0.361538, 0.561538] 内（甚至优于 r19 的 0.461538）、"
        "contact=2≤7、G1=bottom courtyard 非弃权 0/0/0 维持（r16 基线 "
        "live 重放对照；r20 破坏 2/0/0 在案=分岔记录）——三项复制性判据"
        "全部满足、唯 G2 破坏触发字母；冻结支文把 G1/G2 破坏与「r19 量级"
        "不可复制」捆绑为同一结论文本、本轮 M1 分量与该解释相悖——分岔如"
        "实登记（g2_bifurcation_record 单列）：字母=regressed 与 M1 复制"
        "事实=机制观察两账分列、不合并、不改写（同一输入守门布尔翻转即字"
        "母翻转：replication_verdict_fixed_point(16,41,2,True)=replicated "
        "构造可复算）。(g) 支 M1 ≥0.771429 未命中（r16 基线 27/35 双侧复"
        "算一致）；(d) 支 M1 <0.771429 真但守门破坏→不落。机制观察单列"
        "（不影响字母）：M4 双样本=r19 0.211111（未过 0.20 门、差 0.011111 "
        "在案）vs r22 0.104545（过门=第二次样本过门；不进字母、不合并分"
        "布、不挑优）；rubric 三族 contact 2/existence_blackdot 4/existence_other "
        "12 对照 r19（4/4/14）与 r20（2/6/10）——黑点 4=与 r19 持平"
        "（guidance-r19 无 §5B 节、bottom 黑点仍存在性弃权[bottom-i2 两"
        "板]）；援引计数对照 r19 基线（r19=旗级 6+2、notes 10/12 在案；"
        "r22=旗级全 0、notes 级 §5B=0/12、(iii-a)=6/12）；(iii-a) 落支="
        "间隙 6+侵入 1+残余弃权 2；GT 双口径 union=agreement=1/13=双实例"
        "一致命中（agreement 口径首次计入）；通道归因几何门 2/类别门 4/"
        "视角门 1 对照 r19（0/2/0）与 r20（0/0/0）。实验对照账：本轮 "
        "(M1,M2,M3,M4)=(0.390244, 0.2, 4, 0.104545)（M3 槽位=冻结件黑点"
        "族口径、contact=2 另列不占槽），六行并列（r16 "
        "0.771429/0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、r18 "
        "0.645161/0.684211/13/0.277778、r19 0.461538/0.571429/4/0.211111、"
        "r20 0.636364/0.285714/6/0.25、r22 0.390244/0.2/4/0.104545）——"
        "r22 与 r20 均 G 守门破坏经资格门剔除不入排序；comparison_rule "
        "排序不变=r19_axis3 第一、r18 第二、r16 参照、r17 末位；显著收益"
        "定义描述层命中（M1 绝对降幅 0.381185≥0.10；r18 0.126268、r19 "
        "0.309891 亦 ≥0.10）——与字母裁决分列互不改写。三轴实验总收束"
        "位：最终结论维持=收益最大配置=轴3 单变量（guidance-r19）；r22 "
        "不入排序、不改变收束；轴3 收益的归因状态=「M1 量级在新鲜实例群"
        "复现（机制方向支持）但守门字面降级（预注册字母=regressed）」——"
        "两账并列、不合并、不改写；发展域证据不得冒充留出。下一候选建议"
        "（如实单列、由用户拍板、本包不预写决策）：(a) 接受发展域现状收"
        "束训练环、留出集时机由用户判断；(b) 对 G2 的 2 条出局条目做机制"
        "归因（报告框 hygiene 核实，处置轴=派发层框收敛指引、须新预注册"
        "轮）；(c) 再一轮同指引重复轮（三样本）。regressed=预注册阈值命"
        "中方向的描述性结论、非因果证明——「同指引重复轮如实测得守门破"
        "坏同样是有效证据」；单轮 n=3、development 域只描述不断言；字母"
        "裁决只回答「r19 单轮收益是否在新鲜实例群复现（真实收益 vs 实例"
        "群漂移）且守门维持」的判据命中方向；部分重复≠独立重复（同域同编"
        "排实例池、验证力度如实声明）；机制观察/度量教训单列、不凌驾不改"
        "写字母裁决；APR-0011 门（代表配置）与字母裁决分列不合并；本轮判"
        "据均为描述性边界、非门阈值（门零改动）。残余实例差异仍存（top "
        "弃权率 0.454545/0.4/0.35 极差 0.104545、bottom None/0.5/0.0 极"
        "差 0.5 按可计算实例——M4 双样本极差收窄如实）；bottom-i1 两板零"
        "旗标=零分母→None 口径触发（r17/r19 先例复现）。不做「能力已修"
        "复/已达成」类断言；in_calibrated_range 恒 False。本批证据按协议 "
        "v1 §4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r22-prep-record 判据=复制性三分判据、"
         "阈值零改动）。"),
        ("R16 对照基线=calibration-run-r16.json（同一聚合逻辑对内嵌实例记录"
         "双侧复算 top 27/35=0.771429、bottom 12/14=0.857143，与在案登记/"
         "axis-plan 锚交叉核对一致，不手工抄数）；r19 参照元组=run-r19 内嵌"
         "实例记录 live 复算（18/39、4/7）+prep-record run_r19_metric_anchor "
         "冻结值交叉核对一致；contact 对照基线=分型件 rubric 口径 10（r13–"
         "r16 链 8/15/5/10 重放对拍逐一相等后套用，不手工抄数）；轮间对比只"
         "做方向性描述（跨轮实例群混杂照旧；本轮恰以实例群重抽为唯一实验操"
         "作与裁决变量=收敛归因设计本身）；M1 分母（top 旗数 35→39→22→41）"
         "本身随轮变化、弃权率比较含分母效应，构成分解（top 弃权构成分型+"
         "(iii-a) 落支+黑点/援引计数）单列补足。"),
        ("复制性判据的描述性边界纪律：M1 带宽 [0.361538, 0.561538]（r19±"
         "0.10）与截断值 0.771429（r16 基线 6 位定点）均为预注册描述性边界、"
         "不得事后收放；部分重复≠独立重复（同域同编排实例池、验证力度如实声"
         "明）；同指引重复轮的字母裁决只回答「量级是否复制+守门是否维持」、"
         "不回答「判据条款是否有效」——后者属机制观察与后续预注册轮的范畴。"),
        ("G2 分岔=判据设计的机制教训（单列，供后续预注册参考、本轮不追溯适"
         "用）：守门 G2 操作化定义「top 几何门面积比出局条目不得回升」与复制"
         "性结论在冻结支文中捆绑（任一破坏→量级不可复制），本轮 M1 带内复制"
         "与 G2 破坏同时显形=该捆绑解释的反例在案；预注册字母优先（"
         "regressed_guards）=预注册纪律的正确执行；后续如需把「报告框 "
         "hygiene」与「判据量级复制」分开裁决，修订须走 prep-record 预注册"
         "（先于该轮盲读冻结）、不得事后改判本轮或既往轮次（r8–r20 字母裁"
         "决维持不变）。"),
        ("度量教训在案（供后续预注册参考、本轮不追溯适用）：M3 槽位定义维持"
         "冻结件黑点族口径、contact=2 另列不占槽=对照账纪律延续；contact 计"
         "数口径=分型件 rubric 机械套用（计数口径跨轮漂移是历史教训：r15 "
         "prose 口径 7 vs 分型件 rubric 口径 8 在案，axis-plan M3_caveat 已"
         "声明一律采用 rubric 口径）；零旗标格=2（bottom-i1 两板）→视角层 "
         "bottom 中位数=None、极差按可计算实例口径触发（r17/r19 先例复现）"
         "；重复轮与单轴轮的四元组并列遵守同一 benefit_metrics 口径（六行并"
         "列在案）；实验对照账与字母裁决分列互不改写（r18/r19/r20 先例延续、"
         "本轮 regressed+降幅命中+带内复制=三账事实分列）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=regressed 维持"
         "不变（regressed=守门破坏/量级不可复制的描述性边界结论、非因果证"
         "明；单轮 n=3 小样本方向性证据；主通道复制性三分判据与 APR-0011 门"
         "分开表述、互不凌驾：门联合评价（代表配置）=not_met 如实分列）；不"
         "得回溯改判既往轮次（r8–r20 字母裁决维持不变）；早期轮字母与实验账"
         "分列先例（r18：reject 但排序居首；r19：marginal 但排序居首；r20："
         "reject 但降幅命中）延续——本轮 regressed 且 M1 带内复制+降幅命中="
         "两账分列不合并（g2_bifurcation_record 承载）。"),
        ("通道归因方法：照抄 run-r15–run-r22 channel_attribution 的重放口径"
         "（deviation_note 承接），R16/R19/R20/R22 均以内嵌输入确定性重放并"
         "与 compare_v3 对拍（run-r22 channel_attribution.method）；重放复现"
         "与在案登记一致（fail-closed）；几何门 r22=2/类别门 r22=4/视角门 "
         "r22=1 如实计数、不构成字母裁决输入以外的门。"),
        ("读者实例行为与派发操作披露如实记录：R22 十二派次 v1.2 规约自述合规"
         "（纯 Read 直读、12/12 派次自述「未读取盘上任何其他文件」）；输出格"
         "式披露（12 件缩进格式冻结原始判读件、零改动直读）parse 校验全部通"
         "过；flag_id 编号行为=5 个有旗实例全部同实例跨板连续+bottom-i1 两板"
         "零旗标（与 prep-record naming 声明相符）；R22T/R22B 前缀由派发指"
         "令层覆盖（指引字节复用、§6 落盘原文 R19T-/R19B- 保持=前缀差异登"
         "记、r16 先例在案）；本轮无派发操作事故。跨轮 reader 实例不同+轮内"
         "实例差异=混杂因素，每视角 n=3；本轮轮前评审=pre_round_review 在案"
         "（r22-prep-record）。"),
    ]

    next_iteration_targets = [
        ("三轴实验总收束位登记：comparison_rule 排序不变（r19_axis3 第一、"
         "r18 第二、r16 参照行第三、r17 末位）；r22 不入排序（G2 破坏=资格"
         "门剔除、行仅如实入账）；三轴实验最终结论维持=收益最大配置=轴3 单"
         "变量（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、黑点"
         "族 13→4；按冻结 iv_final_selection 全部已测配置中排序最优者）；"
         "轴3 收益的归因状态=「M1 量级在新鲜实例群复现（机制方向支持）但守"
         "门字面降级（预注册字母=regressed）」——两账并列、不合并、不改写。"),
        ("下一候选建议（如实单列，供主审/用户决策；本包不预写决策）："
         "(a) 接受发展域现状收束训练环（不再追加迭代轮），留出集时机由用户"
         "判断（HOLDOUT-PLAN.md a4b80193 Tier 1/2 候选清单零接触在案；正式"
         "采纳门槛=连续 2 轮达标+人工批准未达成、不得写成已达成）；"
         "(b) 对 G2 的 2 条出局条目做机制归因（reader 负责任报告的 "
         "frame_box_pct 过大触发 area_ratio>10 核实——属报告框 hygiene 而"
         "非判据问题的话，处置轴=派发层框收敛指引，须新预注册轮[prep-"
         "record 先于盲读冻结]）；(c) 再一轮同指引重复轮（三样本；r16 先例"
         "同型、配置与 r22 完全同构）；三选项均由用户拍板。"),
        ("G2 分岔后续（判据设计机制教训，单列）：守门 G2 与复制性结论的捆绑"
         "解释在本轮 M1 分量上失去对应（量级复现与守门破坏同时显形）——后续"
         "如需把「报告框 hygiene」与「判据量级复制」分开裁决，须先走 "
         "prep-record 预注册修订守门操作化定义（先于该轮盲读冻结）；不得事"
         "后改判 r22 或既往轮次；本轮 regressed 维持不变。"),
        ("留出集时机=开发线收敛（须用户拍板）：r22 字母=regressed→收敛未宣"
         "告、连续=0（正式采纳门槛=连续 2 轮达标+人工批准未达成，不得写成已"
         "达成）；GT 侧维持全关闭声明延续（gt-audit-r1[1f20554a…]三候选全部"
         "关闭，r9–r22 延续零改动；GT 13 条全部 side=top、bottom 零匹配属"
         "结构性；r22 union=agreement=1/13=GT-REVC-P1-L1SHORT 双实例命中、"
         "agreement 口径自 r12 引入以来首次计入=机制方向事实、非新 GT）；"
         "in_calibrated_range 恒 False 直到正式采纳（须人工批准）；达标证据"
         "仍须留出集（out/v3-tl2/holdout/HOLDOUT-PLAN.md a4b80193… 与 "
         "datasets/holdout-candidates-r1 在案）。"),
        ("判读侧残余问题登记：top 弃权 16 条存在性占比上升（14/16；对照 r19 "
         "13/18、r20 9/14）；bottom-i1 两板零旗标（零分母→None 口径触发，"
         "r17/r19 先例复现）；bottom 黑点仍存在性弃权（bottom-i2 两板，指引"
         "无 §5B 节同构 r19）；reroute 类 4 旗全弃权、子串「等长|蛇形」零命"
         "中=滥用型通道被动追踪=0 延续；类别门 r22=4 条（对照 r19=2、r20="
         "0，逐轮计数如实）。"),
    ]

    round_identity_declaration = {
        "changed_variables": 0,
        "changed_variables_note": ("指引/渲染字节复用+GT/阈值/协议零变更="
                                   "changed_variables=0（prep-record."
                                   "changed_variables=[] 实测核对一致）；唯"
                                   "一操作=实例群重抽（12 派次全部重抽、与 "
                                   "r19/r20 实例群无身份延续）"),
        "guidance_reuse": {
            "base": "observation-guidance-r19.md",
            "base_sha256_prefix": "8633bda5",
            "byte_delta": 0,
            "mode": "byte_reuse_zero_change",
            "zero_new_guidance_file": True,
        },
        "precedent": "r16 先例（r15→r16 同指引重复、渲染零变更、仅实例重抽）",
        "round_nature": "同指引重复轮（收敛归因；第二十二轮）",
        "section6_prefix_difference": (
            "§6 前缀差异登记：指引 §6 示例旗 ID 前缀保持 R19T-/R19B- 落盘"
            "原文（字节复用不改），R22 派次实际前缀=R22T/R22B 由派发指令层"
            "覆盖（r16 先例在案：r15 指引+R16T 前缀执行先例，与 r20「随指"
            "引落盘固化」路径不同）"),
        "sole_operation": "reader 实例群重抽（12 派次）",
    }

    r21_skip_declaration = {
        "declaration": (
            "【跳号声明】r21 号段=axis-experiment-plan-r17-r20（b6ec6467 "
            "冻结件）combination_decision_rule.ii_full_combination 预留的 "
            "R21 全组合条件位——per early_stop_rule.strong_single_axis_"
            "shortcut「……不铺全组合（R21 不做）」未触发、该槽位永久留"
            "空；round20-dev-record next_iteration_targets[0] 已登记「R21 "
            "不做」；r22 为该登记之后的时序下一轮、与该 R21 全组合位无涉"
            "（非其执行、非其替代）——轮次号跳号以免台账歧义"),
        "frozen_quotes": prep["guidance_reuse"]["chain_anchors"][
            "axis_experiment_plan_frozen_r21_slot"]["r21_slot_frozen_quotes"],
        "r21_status": "冻结计划未执行位（槽位永久留空）",
        "role": ("轮次身份声明（如实登记；防台账歧义；冻结原文引用）"),
    }

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": [
            ("R16→R22 派发与旗标量对照：盲读派次 12→12（协议侧 v1.1+v1.2 "
             "沿用无新增版本）；旗标 36（r19）→36（r20）→51（六实例旗数 "
             "top 11/10/20、bottom 0/4/6；非弃权 33+弃权 18）；全旗标合计 "
             "弃权率 0.5（18/36，附记口径）→0.352941（18/51，附记口径）；"
             "预注册主通道复制性三分判据：(g) G2 破坏命中⇒regressed_guards "
             "支（支序最高）⇒字母裁决=regressed（唯一正式裁决）；M1 带内+"
             "contact 门两判据命中如实分列（g2_bifurcation_record）；代表"
             "配置（top-i1+bottom-i2 双非 tie）弃权率 0.428571（6/14，"
             "r19）→0.333333（4/12，r20）→0.466667（7/15，r22）。"),
            ("视角层三分列（measurement_design item 2）：top 弃权率 "
             "0.454545/0.4/0.35（r22，极差 0.104545=M4）——聚合落点 "
             "27/35=0.771429（r16 基线）→18/39=0.461538（r19）→14/22="
             "0.636364（r20）→16/41=0.390244（r22，复制带内、优于 r19 带"
             "中心；较 r16 基线降 0.381185=显著收益定义描述层命中，与字母"
             "裁决分列互不改写；本轮恰以实例群重抽为唯一实验操作与裁决变"
             "量=收敛归因设计本身）；bottom None/0.5/0.0（r22，极差 0.5 "
             "按可计算实例；bottom-i1 两板零旗标→零分母 None 口径触发）——"
             "bottom 全旗聚合弃权率 12/14=0.857143（r16）→4/7=0.571429"
             "（r19）→4/14=0.285714（r20）→2/10=0.2（r22，improved 改善"
             "方向如实单列）；M4 双样本（r19 0.211111 vs r22 0.104545——"
             "r22 过 0.20 门=第二次样本过门、r19 差 0.011111 未过在案）"
             "单列不进字母。"),
            ("matches 与 GT 双口径（measurement_design item 3）：r19 唯一"
             "命中（union 1/13=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT）"
             "→r22 union=agreement=1/13（GT-REVC-P1-L1SHORT，prep1-top-i2 "
             "R22T-007+prep1-top-i3 R22T-017 双实例命中）——r12 以来第二"
             "次逐实例命中、且首次两实例一致命中=agreement 口径（≥2/3 实"
             "例命中才计）首次计入，如实登记；代表配置 gt_recall_total 0.0"
             "（0/13）、seed_match_rate 0.0（0/8，诊断口径，禁称 precision/"
             "FPR）；bottom 非弃权旗零匹配属结构性（GT 13 条全部 side=top、"
             "bottom 无 GT 在案 gt-audit-r1）。"),
            ("通道归因（vs R19/R20，预注册重放方法）：几何门面积比出局 "
             "0→0→2（R19=0→R20=0→R22=2 回升=守门 G2 破坏；R22T-002 "
             "16.406371+R22T-013 16.369542 逐条摘录入 g2_bifurcation_"
             "record）；类别门 2（r19）→0（r20）→4（r22，逐条在案）；视"
             "角门 0→0→1（r22 单条在案）。通道链自 r6：几何门 r6=1→r7=0→"
             "r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→r15=0→r16=0→r17=0→"
             "r18=0→r19=0→r20=0→r22=2；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→"
             "r11=1→r12=0→r13=0→r14=0→r15=0→r16=1→r17=0→r18=0→r19=2→r20=0"
             "→r22=4。重放与 compare_v3 对拍一致。"),
            ("预注册假设（r20-dev-record-candidate-r19-config-same-guidance-"
             "repeat）复制性三分判据字母裁决=regressed（唯一正式裁决）：落"
             "支=(g) regressed_guards（per r22-prep-record guard_channel."
             "requirement 原文：任一守门破坏→regressed 支命中——描述性边"
             "界，本实验已收束、收敛归因轮出局语义不适用、破坏照实记录）；"
             "实测：R22 四元组=(0.390244, 0.2, 4, 0.104545)（M1=top 全旗聚"
             "合弃权率 16/41、M2=bottom 2/10、M3=黑点族弃权旗数 4、M4=top "
             "逐实例极差 0.104545）；r19 参照元组=(0.461538, 0.571429, 4, "
             "0.211111)（run-r19 内嵌实例记录 live 复算+冻结锚交叉核对一"
             "致，不手工抄数）→M1 带 [0.361538, 0.561538] 内=True、"
             "contact 族 2≤7=True、G1=0/0/0 维持——三项复制性判据全部满"
             "足；(g) 支 M1 ≥0.771429→crit_regressed_m1=False（r16 基线="
             "同一聚合逻辑对 run-r16 内嵌输入双侧复算 27/35=0.771429）；"
             "G2=破坏（几何门 R19=0→R22=2）——支序 regressed 在 replicated "
             "之前、字母=regressed；分岔（M1 复制与守门破坏同时显形）如实"
             "分列（g2_bifurcation_record）。"),
            ("机制观察单列（不凌驾）：(a) G2 分岔（关键，如实单列）——守门"
             "设计针对报告框质量（frame_box_pct 几何门），本轮触发源=silk_"
             "readability 负责任报告 2 条（area_ratio>10）；M1 带内复制与"
             "守门破坏同时显形=冻结支文捆绑解释的反例在案（g2_bifurcation_"
             "record 单列、字母不改写）；(b) M4 双样本=r19 0.211111（未过 "
             "0.20 门、差 0.011111 在案）vs r22 0.104545（过门=第二次样本"
             "过门；不进字母、不合并分布、不挑优）；(c) 援引分记（两条款分开记、互不合并）："
             "旗级 §5B/(iii-a)/分支( 全 0 旗（对照 r19 旗级 (iii-a) 6 旗+"
             "分支( 2 旗）；notes 级 §5B=0/12 派次（指引字节复用无 §5B 节"
             "=任何援引为零上下文）、(iii-a)=6/12 派次（对照 r19 notes 级 "
             "10/12）；(d) (iii-a) 逐旗落支=间隙支 6+侵入支 1+残余弃权支 2"
             "（间隙支 notes 级判正常路径 2 派次）；(e) rubric 族计数 "
             "contact 2/existence_blackdot 4/existence_other 12（r13–r16 "
             "132 条弃权旗重放对拍逐一相等后套用 r22，链值 8/15/5/10 在"
             "案）——黑点 4=与 r19 持平（guidance-r19 无 §5B 节、bottom "
             "黑点仍存在性弃权[bottom-i2 两板]）vs r16=12/r18=13/r20=6；"
             "存在性其他 12 vs r19=14/r20=10（介于两基线间）；(f) top 弃"
             "权构成分型=接触性 2+存在性 14+其他 0（16 条逐旗摘录在案；"
             "对照 r19 5/13/0、r20 4/9/1——存在性占比上升、接触性收敛）。"),
            ("bottom 改善通道单列（M2=2/10=0.2 vs r16 基线 12/14=0.857143 "
             "vs r19 4/7=0.571429 vs r20 4/14=0.285714，improved 方向；不"
             "影响字母）：bottom 弃权旗仅 bottom-i2 两板 2 条（黑点-焊盘贴"
             "近存在性弃权）；bottom 非弃权 8 条（黑点/深色小圆点报告 4+"
             "placement 报告 4）；bottom courtyard 类旗标=0（G1 维持的直"
             "接构成）；bottom-i1 两板零旗标（r19 先例格复现）。"),
            ("工具行为与派发操作（协议侧 v1.2 沿用第十轮，如实入账）：R22 "
             "十二派次全部以 Read 工具直读内嵌图像、逐派次 reading_notes "
             "自述「未读取盘上任何其他文件」；全部判读输入严格限于（指引+"
             "该 PNG），零 GT/零诊断/零 legend=非盲读违规；flag_id 编号行"
             "为=5 个有旗实例全部同实例跨板连续+bottom-i1 两板零旗标（与 "
             "prep-record naming 声明相符）；R22T/R22B 前缀由派发指令层覆"
             "盖（指引字节复用、§6 落盘原文 R19T-/R19B- 保持=前缀差异登"
             "记、r16 先例在案）；本轮无派发操作事故；跨轮实例不同+轮内实"
             "例差异=混杂因素照旧声明（reader_instance_note）。"),
            ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延"
             "续，零阈值改动零期望）：courtyard 类旗标 8 条（top 弃权 2+"
             "top 非弃权 6；bottom 0）——非弃权 courtyard 命中链 r16=1→"
             "r17=0→r18=0→r19=0→r20=0→r22=0；reroute 类 4 条（全弃权；"
             "top-i1 2+top-i3 2；子串「等长|蛇形」零命中）；产量链 r8=1→"
             "r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2→r17=1→r18=3"
             "→r19=3→r20=2→r22=4；滥用型通道被动追踪=0。"),
        ],
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本件=R22 收口包 B（dev-record 分包）：development 域第 22 轮迭代"
        "（同指引重复轮=收敛归因）的轮次开发记录；迭代轮不得冒充留出证据。",
        "evaluation_domain": EVALUATION_DOMAIN,
        "flag_production": flag_production,
        "g2_bifurcation_record": g2_bifurcation_record,
        "gt_agreement_milestone": gt_agreement_milestone,
        "gt_audit_ref": dict(run["gt_audit_reference"]),
        "honest_conclusion": honest_conclusion,
        "hypothesis_test_i": ht,
        "instrument_change": run["instrument_change"],
        "is_gate": False,
        "joint_evaluation_trend": {
            "after_r12": dict(dev20["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r22 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r22 全旗标合计 18/51=0.352941 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R20 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 与 "
                         "seed_match_rate 0.0 两项未达暂行线；gt_count 13≥12 "
                         "与 abstain_rate 0.466667≤0.5 单分项入线）——GT 条"
                         "目层 union=agreement=1/13 亦未达 0.75（双口径与门"
                         "分列如实；agreement 口径首次计入=机制方向事实，不"
                         "构成门判定改善）"),
            },
        },
        "kind": KIND,
        "mechanism_observation_r22": mechanism_observation_r22,
        "next_candidate_suggestion": next_candidate_suggestion,
        "next_iteration_targets": next_iteration_targets,
        "notes": notes,
        "preregistration_chain": chain,
        "preregistration_chain_note": (
            "预注册链（含哈希）：axis-experiment-plan-r17-r20.json"
            "（b6ec6467…，用户 2026-09-09「三条轴单独/组合/全组合尝试，选择"
            "收益最大的继续」指令操作化=冻结比较规则[comparison_rule]+组合"
            "决策规则+early_stop_rule，先于 R17–R21 任何实验轮盲读冻结；r21 "
            "全组合槽位=条件位未触发、永久留空）→r20-prep-record.json（"
            "e29ee2a3…，阶段2 组合轮预注册件在案）→round20-dev-record.json"
            "（80e3e9e2…，阶段2 收束+next_iteration_targets[1] 同指引重复"
            "轮候选=本轮设计出处与合法性依据）→r22-prep-record.json（"
            "63346ee6…，本轮预注册件，measurement_design 聚合口径与 "
            "hypothesis_test.adjudication 复制性三分判据（replicated=M1 带"
            "内+contact≤7+守门维持/drifted=未达 replicated 且 M1 <0.771429 "
            "且守门维持/regressed=M1 ≥0.771429 或 G1/G2 任一破坏）先于盲读"
            "冻结；changed_variables=[]；no_instrument_change=true）→判读指"
            "引=observation-guidance-r19.md 字节复用（8633bda5…，本体零字节"
            "不动、零新建指引文件；§6 前缀差异=R19T-/R19B- 落盘原文 vs "
            "R22T/R22B 派发层覆盖、r16 先例在案）→渲染零变更（renders-r14b "
            "四图字节复用、与 r14–r20 盲读同一批文件[applied-top 298bc620/"
            "applied-bottom d7284259/prep1-top b2f84524/prep1-bottom "
            "d7284259；witness-r14b b63771f9 在案]）→12 次盲读[5 个有旗实"
            "例全部同实例跨板连续、bottom-i1 两板零旗标、无派发事故]→"
            "run-r22（80a12c05…，本链执行落盘；r19_run_record_reference="
            "e5755a11 在案=M 元组参照行 live 复算输入）；GT 重投影沿用 "
            "derivation-log-r5.json（62343380…）零新派生（GT 全部 side=top；"
            "渲染零变更=GT 重投影输入未变）；GT 冻结纪律：轮后未增删改；"
            "gt-audit-r1（1f20554a…）结论维持 GT 零改动（三候选关闭，"
            "gt_audit_reference 在案）"),
        "reference_hash_manifest": reference_hash_manifest,
        "round_id": ROUND_ID,
        "round_identity_declaration": round_identity_declaration,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域同指引重复轮（第二十二轮；收敛归因；r16 先例）："
            "变更=零（判读指引=observation-guidance-r19.md 字节复用["
            "8633bda5 实测锚；零新建指引文件；§6 前缀差异=R19T-/R19B- 落盘"
            "原文 vs R22T/R22B 派发层覆盖、r16 先例在案]+渲染零变更="
            "renders-r14b 四图字节复用（与 r14–r20 盲读同一批文件；"
            "no_instrument_change=true）+GT 集/协议阈值与度量版本/比较器常"
            "量零改动（GT 重投影沿用 derivation-log-r5——零新派生；gt-audit-"
            "r1 三候选关闭结论延续）；协议 v1.1+v1.2 维持无新增版本；"
            "changed_variables=0）；唯一实验操作=reader 实例群重抽（12 派"
            "次全部重抽、与 r19/r20 实例群无身份延续）；【跳号声明】r21 号"
            "段=axis-experiment-plan-r17-r20（b6ec6467 冻结件）预留的 R21 "
            "全组合条件位（early_stop_rule.strong_single_axis_shortcut 未"
            "触发、槽位永久留空；dev-r20 已登记「R21 不做」；r22 与该位无"
            "涉）；检验假设 r20-dev-record-candidate-r19-config-same-"
            "guidance-repeat（判据=r22-prep-record.json hypothesis_test."
            "adjudication 复制性三分判据，轮后如实执行：字母裁决唯一正式+"
            "机制观察/度量教训单列+G2 分岔记录单列；主通道复制性三分判据与 "
            "APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate"
            "≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独立计算、互"
            "不凌驾、分开表述；measurement_design 聚合口径先于盲读冻结）；"
            "跨轮收益比较按 axis-plan 冻结规则（r22 行见 axis_experiment_"
            "ledger 六行并列：r22 资格门剔除不入排序、排序不变=r19_axis3 "
            "第一、三轴实验总收束位两账并列）；按协议 v1 §4，迭代轮证据不"
            "冒充未见留出，in_calibrated_range 恒 False"),
        "r21_skip_declaration": r21_skip_declaration,
        "run_record_ref": {"path_rel": REL_RUN_R22, "sha256": run22_sha},
        "schema_version": SCHEMA_VERSION,
        "three_axis_experiment_closeout": three_axis_experiment_closeout,
    }


def main() -> None:
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s78-cal-r22-devrecord] round22-dev-record: {status}")
    print(f"[s78-cal-r22-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch=(g) regressed_guards（G2 几何门 0→2 破坏）")
    print(f"[s78-cal-r22-devrecord] 复制性三分判据: (p) M1 带内=True（"
          f"0.390244∈[0.361538, 0.561538]、优于 r19 带中心 0.461538）+"
          f"contact=2≤7=True+G1 维持=0/0/0——三项复制性判据全满足；(g) G2 "
          f"破坏=True（R19=0→R22=2；支序先行）⇒ regressed（唯一正式裁决）；"
          f"(g) M1 ≥0.771429 未中；(d) 不落（守门破坏）")
    print(f"[s78-cal-r22-devrecord] G2 分岔（单列）: M1 带内复制+contact 门+"
          f"G1 维持与守门字面降级同时显形——冻结支文把 G1/G2 破坏与「量级"
          f"不可复制」捆绑、本轮 M1 分量与该解释相悖；两账分列不合并不改写"
          f"（反事实构造：守门维持⇒replicated）；出局条目 R22T-002 "
          f"16.406371+R22T-013 16.369542 逐条摘录在案")
    print(f"[s78-cal-r22-devrecord] 机制观察: M4 双样本 r19=0.211111（未过 "
          f"0.20 门、差 0.011111 在案）vs r22=0.104545（过门=第二次样本过"
          f"门）；rubric 族 contact 2/黑点 4（与 r19 "
          f"持平）/存在性其他 12（对照 r19 4/4/14、r20 2/6/10）；援引 r22="
          f"旗级全 0+notes §5B 0/12+(iii-a) 6/12（对照 r19 旗级 6+2/notes "
          f"10/12）；落支 间隙 6+侵入 1+残余弃权 2")
    print(f"[s78-cal-r22-devrecord] GT: union=agreement=1/13（"
          f"GT-REVC-P1-L1SHORT；prep1-top-i2 R22T-007+prep1-top-i3 R22T-017 "
          f"双实例命中=agreement 口径自 r12 引入以来首次计入）；通道门 几何 "
          f"2/类别 4/视角 1（对照 r19 0/2/0、r20 0/0/0）")
    print(f"[s78-cal-r22-devrecord] 三轴总收束: comparison_rule 排序不变"
          f"（r19_axis3 第一）；r22 不入排序（G2 破坏）；轴3 收益归因状态="
          f"「M1 量级在新鲜实例群复现（机制方向支持）但守门字面降级（字母="
          f"regressed）」两账并列不合并不改写")
    print(f"[s78-cal-r22-devrecord] 下一候选建议（三选项、由用户拍板）: "
          f"(a) 接受发展域现状收束训练环+留出集时机用户判断；(b) G2 两条出"
          f"局条目机制归因（报告框 hygiene 核实→派发层框收敛指引、须新预注"
          f"册轮）；(c) 再一轮同指引重复轮（三样本）")
    print(f"[s78-cal-r22-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s78-cal-r22-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0 in_calibrated_range=恒 False")
    print(f"[s78-cal-r22-devrecord] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print(f"[s78-cal-r22-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    print("[s78-cal-r22-devrecord] R22 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=regressed 唯一正式（regressed_guards 支=G2 破"
          "坏）；M1 带内复制事实/G2 分岔/M4 双样本/度量教训单列不凌驾；"
          "in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
