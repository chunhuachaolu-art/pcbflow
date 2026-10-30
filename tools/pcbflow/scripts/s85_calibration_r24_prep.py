#!/usr/bin/env python
"""CAL-R24-PREP：R24 实例群扩容归因轮（多实例协议 v1.3：每视图实例数
3→6）预备包（只新建两个文件：scripts/s85_calibration_r24_prep.py 本体与
out/v3-tl2/calibration/r24-prep-record.json——本轮唯一 out/ 新产物；
datasets/ 与 out/ 既有文件只读、零改动，observation-guidance-r23.md
字节复用零触碰）。

R24 轮性质（预注册，非事后）：**实例群扩容归因轮（多实例协议 v1.3：
每视图实例数 3→6）**。r23 事实锚（round23-dev-record 343a6747 在案）：
M=(0.484848, 0.571429, 8, 0.520833)、G2 几何门出局条目=1（R23T-004
other_advisory 合并铜块 area_ratio=11.458680>10）、归因三支判据字母裁
决=confounded（唯一正式裁决、轮后不改写）——G2 未清零且 M1 带内→框宽
非（唯一）主因，归因转向=剩余混杂（判据内容/实例群/其他输出侧因素）。
本轮唯一实验变量=实例数 n：每视图 3→6（top 6+bottom 6=12 个 reader 智
能体、24 次盲读=24 派次、两波次串行）；指引字节复用零改写（observation-
guidance-r23.md=866b0157 全 64 位实测锚；派发层前缀覆盖 R23T/R23B→
R24T/R24B、round_id→2026-09-10-r24、reader_id→reader-r24-*——r16/r22
字节复用+派发层前缀覆盖先例；指引文件内 §6 示例前缀 R23T/R23B 由派发
指令覆盖、非文件改写）；渲染字节冻结=renders-r14b 四图（applied-top
298bc620 / prep1-top b2f84524 / applied-bottom=prep1-bottom d7284259，
bottom 两态同图如实声明——全 64 位 hash 写入）；GT/阈值/协议正文零变
更（v1/v1.1/v1.2 继承不改+v1.3 n 扩容附录；evaluation-protocol-v2=
holdout 冻结件本轮不启用——v2 生效≠holdout 启动、holdout 暂不启动）。

归因三支判据（hypothesis_test.adjudication 原文逐字冻结，字母唯一正式
裁决；全部阈值比较=6 位定点整数交叉相乘、零浮点除法）：
  instance_dominated：G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）
    且 M4(n=6) < 0.261904 且 split_half_M1_diff ≤ 0.09064 → 实例群抽样
    噪声足以解释元组离散（判据内容归因让位；发展域收敛证据如实登记）；
  not_instance_dominated：G1 维持 且（M4(n=6) ≥ 0.261904 或
    split_half_M1_diff > 0.09064）→ 离散超出抽样尺度、下一归因轴=判据
    内容（判据内容/其他输出侧）；
  guard_interrupted：G1 破坏（任一 bottom 实例 courtyard 非弃权旗 >0）
    → 字母=guard_interrupted（归因悬置、机制观察照常、g1 分岔先例引
    用）。
G2=实测观察项（非本轮字母支）：G2>0→r24 资格门剔除不入排序（r22/r23
先例；r22=2/r23=1/r19=0 对照在案）。「正确测出无效同样是有效证据」三
向记账；结果无论方向均如实入账。

判据锚（全部实测核对，fail-closed）：
  M4 阈值锚 0.261904=r16 基线 M4（axis-experiment-plan-r17-r20.json=
  b6ec6467 在案键位 baselines_registered.r16_baseline.M4_top_per_
  instance_rate_range；字面键 baseline_cross_check 在 run-record 件=
  calibration-run-r23.json hypothesis_test.measurement.baseline_cross_
  check.axis_plan_r16_baseline_M1_M2_M3_M4 交叉核对在案）；
  drift 参照 0.09064=r15→r16 纯重抽漂移（round22/round23-dev-record
  grep 在案后才可引用；本脚本=raw text 计数断言）；
  比较集=r16 基线+r19/r22/r23 实测元组（四行全部盘上在案值双源装载交
  叉核对、非手抄）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-10 / 2026-09-10-r24）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-*
/ reader-raw-* / derivation-log-* / 任何 compare/诊断内容产物；run-r23/
run-r22 仅读 hypothesis_test 顶层判据冻结值字段（GT 匹配与逐旗明细不读
取不入记录）；dev-r23 仅读 axis_experiment_ledger 实测元组、g2 分岔记
录计数/字母/出局条目锚、hypothesis_test_i.verdict、next_candidate_
suggestion 选项(b)原文（GT 字段不转录）；无 git；r23 指引只读零字节不
动；记录内零 GT、零期望数量/分布/坐标；指引内零轮次结果数字（基线数字
仅入本编排侧记录）；r24-prep-record.json 落盘=确定性字节（构造纯函数+
同参重建两次逐字节一致自证）+防覆写守卫（已存在且重建字节不同→FAIL，
相同→幂等零覆写）+落盘后回读验字节；保护三文件（pcbflow/cli.py、
pcbflow/config.py、toolchain_lock.json）开工/收工各验一次全 64 位
sha256。

用法：python scripts/s85_calibration_r24_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R23 = CAL_DIR / "observation-guidance-r23.md"
DEV_RECORD_R22 = CAL_DIR / "round22-dev-record.json"
DEV_RECORD_R23 = CAL_DIR / "round23-dev-record.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
R23_PREP_RECORD = CAL_DIR / "r23-prep-record.json"
RUN_R22 = CAL_DIR / "calibration-run-r22.json"
RUN_R23 = CAL_DIR / "calibration-run-r23.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
EVAL_PROTOCOL_V2 = CAL_DIR / "evaluation-protocol-v2.md"
RECORD = CAL_DIR / "r24-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"
CLI_PY = REPO / "pcbflow" / "cli.py"
CONFIG_PY = REPO / "pcbflow" / "config.py"
TOOLCHAIN_LOCK = REPO / "toolchain_lock.json"

DATE_CONSTANT = "2026-09-10"
ROUND_ID = "2026-09-10-r24"
ROUND_LABEL = "r24"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）。指引/渲染/r23 实测/M4 锚/保护三文件
# =全 64 位 sha256 断言；其余链锚=前 8 位断言。
# ---------------------------------------------------------------------------
GUIDANCE_R23_SHA = ("866b0157acdf763faf68c18f72b383617a8feaa06a043"
                    "015b36f5d3cf7f50ca7")
DEV_RECORD_R23_SHA = ("343a674753ff660c52e276034f9c78dc5680ca44d052634ae"
                      "178110ebef12ee9")
AXIS_PLAN_SHA = ("b6ec646791064a33912354cb02323d64b3d2886ba8e4f73b1f91d93"
                 "596aa25ce")
PNG_APPLIED_TOP_SHA = ("298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5"
                       "ca85e0f4f12a3cd0")
PNG_PREP1_TOP_SHA = ("b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca"
                     "54c58f688d44f8")
PNG_APPLIED_BOTTOM_SHA = ("d7284259c236ba3e2e7295f11fabc119ec37d347744439"
                          "e608e35ee7574731a3")
PNG_PREP1_BOTTOM_SHA = PNG_APPLIED_BOTTOM_SHA   # bottom 两态同图（如实声明）
CLI_PY_SHA = ("6ed4f3fd7c87947562acffb90c8563dfae0d05ad82c395a45d0aad226"
              "c206e17")
CONFIG_PY_SHA = ("f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a"
                 "4c13e73baf")
TOOLCHAIN_LOCK_SHA = ("d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd"
                      "896d9301690b3d")

DEV_RECORD_R22_SHA_PREFIX = "b4b8fbe9"
R23_PREP_RECORD_SHA_PREFIX = "3c42ace7"
RUN_R22_SHA_PREFIX = "80a12c05"
RUN_R23_SHA_PREFIX = "15f58350"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
EVAL_PROTOCOL_V2_SHA_PREFIX = "365b67ef"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

RENDR14B_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
PNG_EXPECTED = {
    "applied-top": PNG_APPLIED_TOP_SHA,
    "prep1-top": PNG_PREP1_TOP_SHA,
    "applied-bottom": PNG_APPLIED_BOTTOM_SHA,
    "prep1-bottom": PNG_PREP1_BOTTOM_SHA,
}

#: observation-guidance-r23.md 身份探针（字节复用基座落盘事实；不符即停）
GUIDANCE_R23_FACTS = {
    "R23T-": 4,
    "R23B-": 1,
    "reader-r23-": 1,
    "reader-r23": 2,
    "- round_id_constant: `2026-09-10-r23`": 1,
    "2026-09-10-r23": 1,
    "# R23 轮 reader 判读指引": 1,
    "renders-r14b": 2,
    "R19": 0,
    "R19T-": 0,
    "R19B-": 0,
    "reader-r19": 0,
    "R22": 0,
    "r22": 0,
    "2026-09-09-r19": 0,
}
GUIDANCE_R23_BYTES = 23125

# ---------------------------------------------------------------------------
# 实测锚常量（=在案实测装载目标；probe 逐一断言，不符即停——防预注册
# 文本与在案事实漂移）
# ---------------------------------------------------------------------------
M_TUPLE_R16 = {"M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}
M_TUPLE_R19 = {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}
M_TUPLE_R22 = {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
M_TUPLE_R23 = {"M1": 0.484848, "M2": 0.571429, "M3": 8, "M4": 0.520833}
M4_ANCHOR = 0.261904          # r16 基线 M4（axis-plan 在案）
M4_ANCHOR_6DP = 261904        # 6 位定点整数
DRIFT_TEXT = "0.09064"        # r15→r16 纯重抽漂移（raw text 在案锚）
DRIFT_6DP = 90640             # 0.09064 的 6 位定点整数
G2_R19 = 0
G2_R22 = 2
G2_R23 = 1
AREA_RATIO_R23T004 = 11.45868  # R23T-004（dev-r23 在案）
TOP_ABSTAIN_R23 = 16
TOP_FLAGS_R23 = 33

#: round23-dev-record 定位标记（fail-closed）
CANDIDATE_B_OPTION = (
    "对剩余混杂（判据内容/实例群/其他输出侧因素）做新预注册轮归因"
    "（须新 prep-record 先于盲读冻结；方向=归因结论位登记的转向）")
CANDIDATE_B_QUOTE = (
    "(b) 对剩余混杂（判据内容/实例群/其他输出侧因素）做新预注册轮归因"
    "（须新 prep-record 先于盲读冻结；方向=归因结论位登记的转向）")

#: 归因三支判据原文（任务给定逐字冻结；json.loads 对拍断言见 main）
ADJ_INSTANCE_DOMINATED = (
    "G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）且 M4(n=6) < "
    "0.261904 且 split_half_M1_diff ≤ 0.09064 → 实例群抽样噪声足以解释"
    "元组离散（判据内容归因让位；发展域收敛证据如实登记）")
ADJ_NOT_INSTANCE_DOMINATED = (
    "G1 维持 且（M4(n=6) ≥ 0.261904 或 split_half_M1_diff > 0.09064）→ "
    "离散超出抽样尺度、下一归因轴=判据内容（判据内容/其他输出侧）")
ADJ_GUARD_INTERRUPTED = (
    "G1 破坏（任一 bottom 实例 courtyard 非弃权旗 >0）→ 字母=guard_"
    "interrupted（归因悬置、机制观察照常、g1 分岔先例引用）")
NO_LOOSENING_SENTENCE = (
    "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由")

DESCRIPTIVE_BOUNDARY_NOTE = (
    "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/"
    "AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结"
    "件 axis-experiment-plan-r17-r20.json 为准")

HYPOTHESIS_TEST_TEXT = r'''
{
 "adjudication": {
  "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准",
  "fixed_point_comparison_note": "全部阈值比较=6 位定点整数交叉相乘、零浮点除法（r22/r23 先例）：M4(n=6)<0.261904 ⟺ m4_6dp<261904（整数）；split_half_M1_diff≤0.09064 ⟺ split_half_6dp≤90640（0.09064=|0.862069−0.771429| 的 6 位定点=90640 整数）；M4 自证=928571−666667=261904（r16 基线 top-i2/top-i1 两实例率之差，本脚本整数复算断言）；字母裁决无浮点路径",
  "g2_observation_separate": "G2（top 视非弃权旗标 frame_box_pct 几何门面积比>10 出局条目数）=实测观察项、非本轮字母支：G2>0 → r24 资格门剔除不入排序（r22/r23 先例；r22=2/r23=1/r19=0 对照在案）；出局条目逐条摘录入机制观察（flag_id/category/area_ratio/containment/现象转述逐条如实、GT 字段不转录）；几何门照常独立计算、不改写三支字母、不参与 instance_dominated/not_instance_dominated 分支判定",
  "guard_interrupted": "G1 破坏（任一 bottom 实例 courtyard 非弃权旗 >0）→ 字母=guard_interrupted（归因悬置、机制观察照常、g1 分岔先例引用）",
  "instance_dominated": "G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）且 M4(n=6) < 0.261904 且 split_half_M1_diff ≤ 0.09064 → 实例群抽样噪声足以解释元组离散（判据内容归因让位；发展域收敛证据如实登记）",
  "letter_branch_map": "字母=三支之一（instance_dominated/not_instance_dominated/guard_interrupted），唯一正式裁决、轮后不改写：G1 破坏→guard_interrupted 独占（归因悬置）；G1 维持→由 M4(n=6) 与 split_half_M1_diff 双条件恰定一支（instance_dominated 需两条件同时成立、not_instance_dominated 需至少一条件超出）——三支互斥、恰一支命中、不新增字母支、不升级归因；r23 字母=confounded 与 r22 字母=regressed 维持不改写",
  "mechanism_observation_separate": "M1/M2/三族计数/援引计数照常单列机制观察、不进字母裁决：M1（top 全旗聚合弃权率，12 派次全口径）入实验对照账（比较集=r16 基线+r19/r22/r23 实测元组，axis ledger 延续登记、rubric 口径）；M2（bottom 同口径）对照在案四行；contact/黑点/存在性三族计数（分型件 rubric 口径）对照 r19（4/4/14）/r22（2/4/12）/r23（8/8/7+semantic_confusion 1）在案基线；(iii-a)/§5B/§6 援引计数照记（本轮指引=observation-guidance-r23.md 字节复用、§5B 节不存在=任何援引为零上下文）；G2 出局条目（若有）逐条摘录；M3（黑点族弃权旗数）与 split_half_M1_diff 单列对照 r19/r22/r23；gt 照常",
  "metric_lesson_separate": "跨轮实例群漂移混杂照旧声明——本轮唯一实验变量=实例数 n（实例群轴），实例群重抽由「轮际固有混杂」转变为本轮实验操作本身（n 扩容=对实例群轴的直接操纵）；M4 口径粒度差异显式登记（本轮 12 格=（applied-top|prep1-top 两态）×（i1–i6 六实例）各自实例率 vs r16–r23 的逐实例两板合计口径（3 格）——阈值 0.261904=r16 历史口径在案值原样引用不改写、跨口径比较=描述性、如实声明）；split_half_M1_diff=本轮首次启用的实例群内部一致性度量（阈值 0.09064=r15→r16 纯重抽漂移在案参照、90640=6 位定点）；部分重复≠独立重复（同域同编排实例池、验证力度如实声明）；单轮 development 域只描述不断言",
  "not_instance_dominated": "G1 维持 且（M4(n=6) ≥ 0.261904 或 split_half_M1_diff > 0.09064）→ 离散超出抽样尺度、下一归因轴=判据内容（判据内容/其他输出侧）",
  "three_way_bookkeeping": "「正确测出无效同样是有效证据」三向记账：结果无论方向均如实入账——字母（三支判据按预注册原文执行、唯一正式裁决、轮后不改写）、机制观察（M1/M2/M3 元组落点+三族计数+援引计数+G2 出局条目摘录，单列不进字母）、度量教训（M4 口径粒度登记+split_half 首次启用+实例群轴直接操纵的验证力度声明，单列）——三账分列、不合并、不改写；instance_dominated 支命中不构成「判据已收敛/能力已达成」类断言（发展域收敛证据如实登记而已）、not_instance_dominated 支命中不构成对判据内容的否定性断言（仅登记下一归因轴方向）"
 },
 "hypothesis": "r23（单变量报告框收敛归因轮）字母=confounded（唯一正式裁决、轮后不改写）：G2 出局条目 1>0 未清零（R23T-004 other_advisory 合并铜块 area_ratio=11.458680>10、r22 型 silk 宽框未再现=条款对目标起效）且 M1=0.484848（16/33）落带 [0.361538, 0.561538] 内→框宽非（唯一）主因、归因转向=剩余混杂（判据内容/实例群/其他输出侧因素）（round23-dev-record 343a6747 在案）。剩余混杂三轴中实例群轴的可分变量=实例数 n：M 元组三轮实测离散（r19=0.461538/r22=0.390244/r23=0.484848；M4 三样本 0.211111/0.104545/0.520833）的两个候选解释=(α) 判据内容/其他输出侧因素主导（离散随配置与指引变化、不随抽样规模收敛）；(β) 实例群抽样噪声主导（离散主要为小样本抽样涨落、随 n 扩容被平均——M4 极差收窄且 split-half 一致性高）。R24=实例群扩容归因轮（唯一实验变量=实例数 n：每视图 3→6、24 派次=4 视角格×6 实例；指引字节复用零改写、渲染字节冻结、GT/阈值/协议正文零变更），以 M4(n=6)+split_half_M1_diff 双判据做归因裁决（6 位定点整数比较）：instance_dominated 支命中→实例群抽样噪声足以解释元组离散（判据内容归因让位、发展域收敛证据如实登记）；not_instance_dominated 支命中→离散超出抽样尺度、下一归因轴=判据内容；guard_interrupted 支（若 G1 破坏）→归因悬置、机制观察照常。",
 "hypothesis_id": "r23-confounded-residual-confound-instance-axis-attribution"
}
'''
import json as _json  # noqa: E402  (模块级对拍用；无 IO)

HYPOTHESIS_TEST = _json.loads(HYPOTHESIS_TEST_TEXT)


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[r24-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _require_full_sha(path: Path, expected: str, label: str) -> str:
    if not path.exists():
        _fail(f"缺失：{path}")
    measured = _sha(path)
    if measured != expected:
        _fail(f"{label} 全 64 位 sha256 实测不符：measured={measured} != "
              f"expected={expected}（锚被改动，立即停止）")
    return measured


def _require_prefix_sha(path: Path, prefix: str, label: str) -> str:
    if not path.exists():
        _fail(f"缺失：{path}")
    measured = _sha(path)
    if not measured.startswith(prefix):
        _fail(f"{label} sha 前 8={measured[:8]} != 预期 {prefix}（锚不符，"
              f"立即停止）")
    return measured


# ---------------------------------------------------------------------------
# probe（实测锚装载与断言；只读判据冻结值字段，GT 匹配/逐旗明细不读取）
# ---------------------------------------------------------------------------

def check_renders_byte_freeze(witness: dict) -> list:
    """渲染字节冻结实测：四 PNG magic+sha256_file 实测 vs witness 登记
    值 vs 任务给定全 64 位预期值三重比对（bottom 两态同图如实声明）。"""
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
    for side in RENDR14B_SIDES:
        path = RENDR14B_DIR / f"{side}.png"
        if not path.exists():
            _fail(f"PNG 缺失：{path}")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        expect_full = PNG_EXPECTED[side]
        if measured != expect_full:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与任务给定全 64 位"
                  f"预期值不符：measured={measured} expected={expect_full}")
        if measured != registered[side]:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与 witness 登记值"
                  f"不符（渲染字节冻结声明被破坏）：measured={measured} "
                  f"registered={registered[side]}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "sha256_expected_full": expect_full,
            "sha256_witness_registered": registered[side],
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "top_zero_change_copies." + side + ".sha256"),
            "witness_record": "out/v3-tl2/calibration/render-witness-r14b.json",
            "match": True,
        })
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（字节冻结口径不符）")
    return results


def probe_witness(witness: dict) -> None:
    """render-witness-r14b 结构最小校验（kind/轮次/日期锚）。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")


def probe_guidance_r23(text: str, sha: str) -> dict:
    """observation-guidance-r23.md 字节复用基座身份探针（全 64 位锚+事实
    计数族；不符即停）。"""
    if sha != GUIDANCE_R23_SHA:
        _fail("指引全 64 位锚不符（probe 内部不一致）")
    if hashing.sha256_text(text) != sha:
        _fail("r23 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")
    if len(text.encode("utf-8")) != GUIDANCE_R23_BYTES:
        _fail(f"r23 指引字节数不符：{len(text.encode('utf-8'))} != "
              f"{GUIDANCE_R23_BYTES}")
    facts = {}
    for needle, want in GUIDANCE_R23_FACTS.items():
        got = text.count(needle)
        if got != want:
            _fail(f"r23 指引身份探针不符：{needle!r} 命中 {got} 次 != 预期 "
                  f"{want} 次（基座疑被改动，立即停止）")
        # 反放宽句不做记录内键名转录（「恰 1 次」纪律：全记录该句恰出
        # 现 1 次=no_loosening_note 引用处；此处以指代键登记计数）
        key = ("反放宽句（逐字原文见本记录 no_loosening_note）"
               if needle == NO_LOOSENING_SENTENCE else needle)
        facts[key] = got
    return {
        "path_rel": "out/v3-tl2/calibration/observation-guidance-r23.md",
        "sha256_measured": sha,
        "sha256_prefix_expected": GUIDANCE_R23_SHA[:8],
        "byte_size": GUIDANCE_R23_BYTES,
        "identity_facts": facts,
        "role": ("指引字节复用基座（本轮零改写零派生；派发层前缀覆盖 "
                 "R23T/R23B→R24T/R24B、round_id→2026-09-10-r24、"
                 "reader_id→reader-r24-*；§6 示例前缀 R23T/R23B 为指引落"
                 "盘原文、由派发指令覆盖——r16/r22 先例同型）"),
    }


def probe_axis_plan(plan: dict, sha: str) -> dict:
    """axis-experiment-plan-r17-r20：M4 阈值锚+r16 基线四键（fail-closed）。"""
    if plan.get("declared_date") != "2026-09-09":
        _fail(f"axis-plan declared_date 不符：{plan.get('declared_date')!r}")
    if plan.get("schema_version") != "3.0":
        _fail("axis-plan schema_version != 3.0（结构漂移）")
    base = plan.get("baselines_registered", {}).get("r16_baseline", {})
    got = {
        "M1": base.get("M1_top_aggregate_abstain_rate"),
        "M2": base.get("M2_bottom_aggregate_abstain_rate"),
        "M3": base.get("M3_blackdot_abstain_flags_rubric"),
        "M4": base.get("M4_top_per_instance_rate_range"),
    }
    if got != M_TUPLE_R16:
        _fail(f"axis-plan r16_baseline 四键不符：{got!r} != {M_TUPLE_R16!r}")
    if base.get("M4_top_per_instance_rate_range") != M4_ANCHOR:
        _fail("M4 阈值锚不符（axis-plan baselines_registered.r16_baseline."
              "M4_top_per_instance_rate_range != 0.261904）")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": AXIS_PLAN_SHA[:8],
        "role": ("M4 阈值锚+r16 基线在案件：M4=0.261904 键位=baselines_"
                 "registered.r16_baseline.M4_top_per_instance_rate_range"
                 "（盘上实测键位；字面键 baseline_cross_check 在 run-record"
                 " 件——run-r23 baseline_cross_check 与本件交叉核对在案）；"
                 "r16 基线四键=[0.771429, 0.857143, 12, 0.261904]"),
        "r16_baseline": M_TUPLE_R16,
    }


def probe_run_r23(run: dict, sha: str) -> dict:
    """calibration-run-r23 判据冻结值锚定（fail-closed；只读顶层判据值
    字段+guard_channel+verdict；GT 匹配与逐旗明细不读取不入记录）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r23 hypothesis_test 结构不符")
    if ht.get("verdict") != "confounded":
        _fail(f"run-r23 verdict 锚不符：{ht.get('verdict')!r}（预期 "
              f"confounded=r23 字母在案锚、轮后不改写）")
    if ht.get("hypothesis_id") != \
            "r22-g2-bifurcation-frame-box-hygiene-attribution":
        _fail("run-r23 hypothesis_id 不符（r23 预注册假设锚）")
    m = ht.get("measurement", {})
    if m.get("r23_m_tuple_6dp") != M_TUPLE_R23:
        _fail(f"run-r23 r23_m_tuple_6dp 不符：{m.get('r23_m_tuple_6dp')!r}")
    if m.get("top_abstain_rate_r23") != 0.484848 or \
            m.get("top_abstain_count_r23") != TOP_ABSTAIN_R23 or \
            m.get("top_abstain_flags_r23") != TOP_FLAGS_R23:
        _fail("run-r23 M1 分子分母锚不符（16/33=0.484848）")
    if m.get("r19_reference_tuple") != M_TUPLE_R19:
        _fail(f"run-r23 r19_reference_tuple 不符："
              f"{m.get('r19_reference_tuple')!r}")
    gc = m.get("guard_channel", {})
    if gc.get("g2_geometry_gate_r19") != G2_R19 or \
            gc.get("g2_geometry_gate_r22") != G2_R22 or \
            gc.get("g2_geometry_gate_r23") != G2_R23:
        _fail(f"run-r23 G2 几何门链锚不符：r19={gc.get('g2_geometry_gate_r19')!r} "
              f"r22={gc.get('g2_geometry_gate_r22')!r} "
              f"r23={gc.get('g2_geometry_gate_r23')!r}")
    bcc = m.get("baseline_cross_check", {})
    if bcc.get("axis_plan_r16_baseline_M1_M2_M3_M4") != \
            [0.771429, 0.857143, 12, 0.261904]:
        _fail("run-r23 baseline_cross_check r16 基线四键不符（M4 阈值锚"
              "交叉核对失败）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r23.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": RUN_R23_SHA_PREFIX[:8],
        "role": ("r23 实测锚（run 件）：M tuple=(0.484848, 0.571429, 8, "
                 "0.520833)（M1=16/33）；G2 几何门 r19=0→r22=2→r23=1；"
                 "verdict=confounded（轮后不改写）；baseline_cross_check."
                 "axis_plan_r16_baseline_M1_M2_M3_M4=[0.771429, 0.857143, "
                 "12, 0.261904]（M4 阈值锚交叉核对在案）"),
        "frozen_values": ("M tuple (M1,M2,M3,M4)=(0.484848, 0.571429, 8, "
                          "0.520833)（M1=16/33、M2=8/14）；verdict="
                          "confounded；G2=1"),
    }


def probe_run_r22(run: dict, sha: str) -> dict:
    """calibration-run-r22 判据冻结值锚定（r22 元组+r19 参照元组装载源）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r22 hypothesis_test 结构不符")
    if ht.get("verdict") != "regressed":
        _fail(f"run-r22 verdict 锚不符：{ht.get('verdict')!r}")
    m = ht.get("measurement", {})
    if m.get("r22_m_tuple_6dp") != M_TUPLE_R22:
        _fail(f"run-r22 r22_m_tuple_6dp 不符：{m.get('r22_m_tuple_6dp')!r}")
    if m.get("r19_reference_tuple") != M_TUPLE_R19:
        _fail(f"run-r22 r19_reference_tuple 不符："
              f"{m.get('r19_reference_tuple')!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r22.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": RUN_R22_SHA_PREFIX[:8],
        "role": ("r22 元组+r19 参照元组装载源（比较集双源之一）：r22=(0."
                 "390244, 0.2, 4, 0.104545)、r19=(0.461538, 0.571429, 4, "
                 "0.211111)；verdict=regressed"),
    }


def probe_dev_record_r23(dev: dict, sha: str) -> dict:
    """round23-dev-record：r23 实测锚（M 元组/G2/verdict/字母）+候选(b)
    授权原文+比较集台账行（GT 字段不转录）。"""
    if dev.get("kind") != "tl2_calibration_round23_dev_record":
        _fail("round23-dev-record kind 不符")
    if dev.get("round_id") != "2026-09-10-r23" or \
            dev.get("round_label") != "r23":
        _fail("round23-dev-record 轮次标识不符")
    if dev.get("declared_date") != "2026-09-10":
        _fail("round23-dev-record declared_date != 2026-09-10")
    if dev.get("schema_version") != "3.0":
        _fail("round23-dev-record schema_version != 3.0（结构漂移）")
    measured = dev.get("axis_experiment_ledger", {}).get(
        "this_round_measured", {})
    if measured != M_TUPLE_R23:
        _fail(f"round23-dev-record 实测四元组锚不符：{measured!r}")
    rows = dev.get("axis_experiment_ledger", {}).get(
        "cross_round_status", {}).get("measured_rows", {})
    for row_name, want in (("r16_baseline", M_TUPLE_R16),
                           ("r19_axis3", M_TUPLE_R19),
                           ("r22_repeat", M_TUPLE_R22),
                           ("r23_attribution", M_TUPLE_R23)):
        if rows.get(row_name) != want:
            _fail(f"round23-dev-record 台账行 {row_name} 不符："
                  f"{rows.get(row_name)!r} != {want!r}（比较集装载源锚）")
    if dev.get("hypothesis_test_i", {}).get("verdict") != "confounded":
        _fail("round23-dev-record hypothesis_test_i.verdict != confounded")
    g2 = dev.get("g2_bifurcation_record")
    if not isinstance(g2, dict):
        _fail("round23-dev-record g2_bifurcation_record 结构不符")
    counts = g2.get("counts", {})
    if counts.get("g2_geometry_gate_r19") != G2_R19 or \
            counts.get("g2_geometry_gate_r22") != G2_R22 or \
            counts.get("g2_geometry_gate_r23") != G2_R23:
        _fail("round23-dev-record G2 几何门链锚不符（r19=0/r22=2/r23=1）")
    if counts.get("g1_bottom_courtyard_non_abstain_r23") != \
            {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail("round23-dev-record G1 维持锚不符（r23 0/0/0）")
    letter = g2.get("letter_vs_fact", {}).get("letter", "")
    if not letter.startswith("confounded"):
        _fail(f"r23 字母锚不符：{letter!r}（预期 confounded、轮后不改写）")
    entries = g2.get("rejected_entries_excerpt")
    if not isinstance(entries, list) or len(entries) != 1:
        _fail("r23 出局条目摘录须恰 1 条（R23T-004）")
    entry = entries[0]
    for key, val in (("flag_id", "R23T-004"), ("category", "other_advisory"),
                     ("area_ratio", AREA_RATIO_R23T004),
                     ("state", "prep1"), ("instance", "top-i3")):
        if entry.get(key) != val:
            _fail(f"r23 出局条目锚不符：R23T-004.{key}={entry.get(key)!r} "
                  f"!= {val!r}")
    if AREA_RATIO_R23T004 <= 10:
        _fail("R23T-004 area_ratio 未过 10（语义引用锚不符）")
    opts = dev.get("next_candidate_suggestion", {}).get("options", [])
    if len(opts) != 3:
        _fail(f"round23-dev-record 下一候选选项须恰 3 项：{len(opts)}")
    if opts[1].get("option") != CANDIDATE_B_OPTION:
        _fail(f"候选(b) 原文不符：{opts[1].get('option')!r}")
    if opts[1].get("preregistration_required") is not True:
        _fail("候选(b) preregistration_required != true")
    return {
        "path_rel": "out/v3-tl2/calibration/round23-dev-record.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": DEV_RECORD_R23_SHA[:8],
        "role": ("本轮设计出处与合法性依据（两父之一）：confounded 支归因"
                 "转向登记+候选(b)授权原文+r23 实测元组/G2/字母锚+比较集"
                 "台账行装载源"),
        "letter": "confounded（唯一正式裁决、轮后不改写）",
        "measured_tuple": M_TUPLE_R23,
        "g2_geometry_gate_r23": G2_R23,
        "candidate_b_quote": CANDIDATE_B_QUOTE,
        "rejected_entry_transcript": {
            "flag_id": "R23T-004",
            "state": "prep1",
            "instance": "top-i3",
            "category": "other_advisory",
            "area_ratio": AREA_RATIO_R23T004,
            "omitted_fields_note": (
                "gt_id/gt_category 不转录（本记录内零 GT 纪律）；全文见 "
                "round23-dev-record.json g2_bifurcation_record."
                "rejected_entries_excerpt"),
        },
    }


def probe_dev_record_r22(dev: dict, sha: str, drift_counts: dict) -> dict:
    """round22-dev-record：r22 实测元组锚+drift 0.09064 raw text 在案计数。"""
    if dev.get("kind") != "tl2_calibration_round22_dev_record":
        _fail("round22-dev-record kind 不符")
    if dev.get("round_id") != "2026-09-09-r22" or \
            dev.get("round_label") != "r22":
        _fail("round22-dev-record 轮次标识不符")
    if dev.get("declared_date") != "2026-09-09":
        _fail("round22-dev-record declared_date != 2026-09-09")
    if dev.get("schema_version") != "3.0":
        _fail("round22-dev-record schema_version != 3.0（结构漂移）")
    measured = dev.get("axis_experiment_ledger", {}).get(
        "this_round_measured", {})
    if measured != M_TUPLE_R22:
        _fail(f"round22-dev-record 实测四元组锚不符：{measured!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/round22-dev-record.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": DEV_RECORD_R22_SHA_PREFIX[:8],
        "role": ("drift 参照在案件（两父之二）：r15→r16 纯重抽漂移 0.09064 "
                 "raw text 在案计数证明（先 grep 确认在案后才可引用——"
                 "fail-closed）+r22 实测元组锚（比较集装载源）"),
        "drift_text": DRIFT_TEXT,
        "drift_occurrence_count": drift_counts["round22"],
    }


def probe_drift_anchor(dev22_text: str, dev23_text: str) -> dict:
    """drift 0.09064 在案锚：raw text 计数（缺锚即 FAIL；先确认在案后才
    可引用）。"""
    c22 = dev22_text.count(DRIFT_TEXT)
    c23 = dev23_text.count(DRIFT_TEXT)
    if c22 + c23 < 1:
        _fail(f"drift 参照 {DRIFT_TEXT} 在 round22/round23-dev-record 均"
              f"未在案（引用前必须 grep 确认，fail-closed）")
    if DRIFT_6DP != 90640:
        _fail("drift 6 位定点常量自证失败")
    return {"round22": c22, "round23": c23, "drift_text": DRIFT_TEXT,
            "drift_6dp": DRIFT_6DP}


# ---------------------------------------------------------------------------
# 记录构造（纯函数）
# ---------------------------------------------------------------------------

def build_record(*, guidance_ref: dict, dev23_ref: dict, dev22_ref: dict,
                 axis_ref: dict, run23_ref: dict, run22_ref: dict,
                 r23_record_sha: str, witness_sha: str,
                 protocol_v1_sha: str, protocol_v2_sha: str,
                 png_checks: list, drift_counts: dict,
                 protected_hashes: dict) -> dict:
    """r24-prep-record 构造（25 键=r23-prep-record 24 键镜像+protected_
    files_verification；canonical JSON sort_keys 落盘）。"""
    record = {}
    record["attribution_plan"] = {
        "declaration": (
            "本轮恰一个实验变量（实例数 n：每视图 3→6=多实例协议 v1.3 扩"
            "容；指引/渲染/GT/阈值/协议正文零变更）、检验恰一个假设（"
            "hypothesis_id=r23-confounded-residual-confound-instance-axis-"
            "attribution：r23 confounded 支归因转向登记的剩余混杂=判据内"
            "容/实例群/其他输出侧因素中，「实例群抽样噪声」是否足以解释 "
            "r19/r22/r23 三轮 M 元组离散）；归因目的=实例数扩容下 M4(n=6) "
            "与 split_half_M1_diff 双判据落点裁决（三支：instance_"
            "dominated=抽样噪声足以解释、判据内容归因让位；not_instance_"
            "dominated=离散超出抽样尺度、下一归因轴=判据内容；guard_"
            "interrupted=归因悬置）；字母/机制观察/度量教训三分记账（"
            "mechanism_observation_separate 与 metric_lesson_separate 单"
            "列，不凌驾三支裁决）"),
        "grouping_note": (
            "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角层三"
            "分列聚合+GT 匹配双口径+联合门代表配置/范围并列；APR-0011 阈"
            "值零改动）；bottom GT 无源=bottom 旗标与 GT 匹配应为空（结构"
            "性在案，不影响收敛计数口径）；三支裁决/机制观察/度量教训三分"
            "记账、互不凌驾；归因分组逻辑由编排侧在 close 包执行；指引内"
            "零 GT、零轮次结果数字（基线数字仅入本编排侧记录）"),
        "guard_channel": (
            "G1=六 bottom 实例（bottom-i1–i6）courtyard 类非弃权旗全=0 维"
            "持（对照 r15–r19/r22/r23 在案 0/0/0、r20 破坏 2/0/0=g1 分岔"
            "先例在案；G1 为「不得弃权」方向的反向风险守门；任一实例非零"
            "→G1 破坏→guard_interrupted 支）；G2=top 视非弃权旗标 frame_"
            "box_pct 几何门面积比>10 出局条目数=实测观察项（非本轮字母"
            "支）：G2>0→r24 资格门剔除不入排序（r22/r23 先例；r22=2/r23="
            "1/r19=0 对照在案）；G3 冻结纪律照常"),
        "primary_channel": (
            "M4(n=6)（top 逐实例弃权率极差=12 个实例率的最大−最小）+split_"
            "half_M1_diff（|M1(i1–i3 双视图聚合)−M1(i4–i6 双视图聚合)|）"
            "双判据归因裁决（三支，6 位定点整数交叉相乘比较、零浮点除法）"
            "——详见 hypothesis_test.adjudication；M1/M2/M3 全元组照常入"
            "实验对照账（比较集=r16 基线+r19/r22/r23 实测元组）；G2=实测"
            "观察项非本轮字母支"),
        "single_variable_rationale": (
            "剩余混杂三轴（round23-dev-record confounded 支归因转向登记）："
            "(1) 判据内容轴（判据条款语义/门限）；(2) 实例群轴（reader 实"
            "例抽样噪声/实例群异质性）；(3) 其他输出侧轴（输出格式/报告纪"
            "律之外的输出侧因素）。单变量选择理由=实例群是唯一可单变量直"
            "接测量的轴：实例数 n 可机械扩容（3→6）而不触碰指引/渲染/GT/"
            "阈值/协议正文任何字节——「抽样噪声尺度随 n 的变化」由此成为"
            "可直接测量的量（M4 极差收窄+split-half 一致性升高=噪声解释力"
            "证据）；判据内容轴须指引文本变更、其他输出侧轴须输出侧操作化"
            "变更，均=多变量并施、不可与本轮同测，留待后续预注册轮（如 "
            "not_instance_dominated 支命中则下一归因轴=判据内容）"),
    }
    record["bottom_view_note"] = (
        "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16/R18/"
        "R19/R20/R22/R23 完全相同文件：白墨图元→橙 (255,165,0)、板内空隙"
        "白→绿 (0,128,0)、其余层 kicad 原配色不变；四 PNG sha256_file 实"
        "测=witness-r14b 登记值+任务给定全 64 位预期值双重 fail-closed 比"
        "对一致）——渲染零变更；本轮唯一判读变更=无（指引字节复用零改"
        "写、实例数扩容=派发层）；bottom 视判读口径沿用 r4 指引原文不改"
        "（top/bottom 判读口径在图像空间完全一致、不做镜像换算）；本轮 "
        "bottom 侧 6 实例（bottom-i1–i6）各包同侧两板（先 applied 后 "
        "prep1、flag_id 同实例跨板连续）；bottom 零旗标分母=0 时弃权率按 "
        "cal._ratio 先例=None 口径照旧")
    record["changed_variables"] = [
        {
            "attribution_channel": (
                "归因裁决=hypothesis_test.adjudication 三支（instance_"
                "dominated：G1 维持且 M4(n=6)<0.261904 且 split_half_M1_"
                "diff≤0.09064；not_instance_dominated：G1 维持且（M4(n=6)"
                "≥0.261904 或 split_half_M1_diff>0.09064）；guard_"
                "interrupted：G1 破坏）——全部阈值比较=6 位定点整数交叉相"
                "乘、零浮点除法"),
            "axis": "instance_sampling_scale（实例群抽样规模轴）",
            "axis_note": (
                "剩余混杂三轴中实例群轴的单变量直接测量（三混杂轴与单变量"
                "选择理由见 attribution_plan.single_variable_rationale）；"
                "判据内容轴与其他输出侧轴零触碰、留待后续预注册轮；三轴实"
                "验（axis-experiment-plan-r17-r20）收束决议与轴停止决议不"
                "变——本变量非三判据轴任何一支重开"),
            "description": (
                "每视图实例数 3→6：top 侧 6+bottom 侧 6=12 个 reader 智能体、"
                "24 次盲读=24 派次（4 视角格×6 实例）、两波次串行（波1="
                "top 侧 6 agent、波2=bottom 侧 6 agent）；每个 agent 串行读"
                "同侧两板（先 applied 后 prep1、flag_id 跨板连续编号）产出 "
                "2 件 reader-raw-r24-*.txt；指引字节复用零改写（派发层前缀"
                "覆盖 R23T/R23B→R24T/R24B、round_id→2026-09-10-r24、"
                "reader_id→reader-r24-*）；渲染字节冻结；实例群全量重抽+"
                "扩容（6 新实例/视角）"),
            "id": "instance-count-n3-to-n6-v1.3",
            "instrument_change": False,
            "target": (
                "盲读编排层（reader 实例群规模；多实例协议 v1.3 附录）——不"
                "触碰任何盘上判读指引/渲染/判据/GT/阈值文件"),
        },
    ]
    record["declared_date"] = DATE_CONSTANT
    record["evaluation_domain"] = {
        "declared": "development",
        "in_calibrated_range": False,
        "note": (
            "in_calibrated_range 恒 False，直到正式采纳为止（development "
            "域只描述不断言）；holdout 暂不启动=用户 2026-09-10 拍板（本"
            "轮不启动留出集评估）"),
    }
    record["guidance_reuse"] = {
        "base": "observation-guidance-r23.md",
        "base_path_rel": "out/v3-tl2/calibration/observation-guidance-r23.md",
        "base_sha256": GUIDANCE_R23_SHA,
        "base_sha256_prefix_expected": GUIDANCE_R23_SHA[:8],
        "byte_size": {
            "base": GUIDANCE_R23_BYTES,
            "delta": 0,
            "derived": GUIDANCE_R23_BYTES,
        },
        "chain_anchors": {
            "axis_plan_m4_threshold_anchor": {
                "path_rel": axis_ref["path_rel"],
                "role": axis_ref["role"],
                "sha256_measured": axis_ref["sha256_measured"],
                "sha256_prefix_expected": axis_ref["sha256_prefix_expected"],
            },
            "evaluation_protocol_v1_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256": protocol_v1_sha,
            },
            "evaluation_protocol_v2_holdout_not_activated": {
                "note": (
                    "holdout 协议冻结件（s79 登记在案）本轮不启用——v2 生"
                    "效≠holdout 启动；holdout 暂不启动=用户 2026-09-10 拍"
                    "板；本轮协议口径=v1/v1.1/v1.2 继承+v1.3 n 扩容附录"),
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v2.md",
                "sha256_measured": protocol_v2_sha,
                "sha256_prefix_expected": EVAL_PROTOCOL_V2_SHA_PREFIX,
            },
            "guidance_base_r23_byte_reuse": {
                "byte_size": GUIDANCE_R23_BYTES,
                "identity_facts": guidance_ref["identity_facts"],
                "path_rel": guidance_ref["path_rel"],
                "role": guidance_ref["role"],
                "sha256_measured": guidance_ref["sha256_measured"],
                "sha256_prefix_expected": guidance_ref["sha256_prefix_expected"],
            },
            "parent_1_round23_dev_record": {
                "candidate_b_quote": dev23_ref["candidate_b_quote"],
                "g2_geometry_gate_r23": dev23_ref["g2_geometry_gate_r23"],
                "letter": dev23_ref["letter"],
                "measured_tuple": dev23_ref["measured_tuple"],
                "path_rel": dev23_ref["path_rel"],
                "rejected_entry_transcript":
                    dev23_ref["rejected_entry_transcript"],
                "role": dev23_ref["role"],
                "sha256_measured": dev23_ref["sha256_measured"],
                "sha256_prefix_expected":
                    dev23_ref["sha256_prefix_expected"],
            },
            "parent_2_round22_dev_record_drift_anchor": {
                "drift_occurrence_count":
                    dev22_ref["drift_occurrence_count"],
                "drift_text": dev22_ref["drift_text"],
                "path_rel": dev22_ref["path_rel"],
                "role": dev22_ref["role"],
                "sha256_measured": dev22_ref["sha256_measured"],
                "sha256_prefix_expected":
                    dev22_ref["sha256_prefix_expected"],
            },
            "render_witness_r14b_byte_reuse": {
                "path_rel": "out/v3-tl2/calibration/render-witness-r14b.json",
                "sha256": witness_sha,
            },
            "r23_prep_record_structure_lineage": {
                "cross_check": (
                    "24 键顶层结构逐键镜像（本轮判据/结构血统=r23；新增 "
                    "protected_files_verification 键=r23 dev-record 同名"
                    "键位先例）"),
                "path_rel": "out/v3-tl2/calibration/r23-prep-record.json",
                "sha256": r23_record_sha,
            },
            "run_r22_metric_anchor": {
                "path_rel": run22_ref["path_rel"],
                "role": run22_ref["role"],
                "sha256_measured": run22_ref["sha256_measured"],
                "sha256_prefix_expected":
                    run22_ref["sha256_prefix_expected"],
            },
            "run_r23_metric_anchor": {
                "frozen_values": run23_ref["frozen_values"],
                "path_rel": run23_ref["path_rel"],
                "role": run23_ref["role"],
                "sha256_measured": run23_ref["sha256_measured"],
                "sha256_prefix_expected":
                    run23_ref["sha256_prefix_expected"],
            },
        },
        "derived": "observation-guidance-r23.md（同一文件、零派生）",
        "derived_path_rel":
            "out/v3-tl2/calibration/observation-guidance-r23.md",
        "derived_sha256": GUIDANCE_R23_SHA,
        "dispatch_override": {
            "flag_id_prefix": "R23T/R23B → R24T/R24B（派发层覆盖）",
            "note": (
                "指引文件内 §6 示例旗 ID 前缀 R23T/R23B 与 round_id 落盘原"
                "文（2026-09-10-r23）由派发指令覆盖、非文件改写——r16/r22 "
                "字节复用+派发层前缀覆盖先例（r16 先例：r15 指引+R16T 前"
                "缀；r22 先例：r19 指引+R22T/R22B）"),
            "reader_id": "reader-r23-* → reader-r24-*（派发层覆盖）",
            "round_id": "2026-09-10-r23 → 2026-09-10-r24（派发层覆盖）",
        },
        "mode": "byte_reuse_dispatch_override",
        "zero_write_declaration": (
            "指引文件零字节不动、零改写、零派生（本脚本对 observation-"
            "guidance-r23.md 无任何写路径；全 64 位实测哈希="
            "guidance_reuse.base_sha256，与开工实测 866b0157 锚 fail-closed "
            "一致；同参重建=N/A——无变换）——r16/r22 指引字节复用先例同型"),
    }
    record["hypothesis_test"] = HYPOTHESIS_TEST
    record["instrument_change"] = {
        "changed": False,
        "declaration": (
            "本轮 prep 零重渲染、零 out/ 既有文件改动（四 PNG sha256_file "
            "实测=witness-r14b 登记值+任务给定全 64 位预期值双重比对；"
            "bottom 两板逐字节同 d7284259=两态同图如实声明；top 无配色 "
            "298bc620/b2f84524）；指引基座=observation-guidance-r23.md 只"
            "读零写入（866b0157）；本轮恰一个 out/ 新建文件=本记录"),
        "note": (
            "渲染与 r14/r15/r16/r18/r19/r20/r22/r23 完全相同（renders-r14b "
            "字节冻结，四 PNG 实测=witness-r14b 登记值），本轮唯一变更=实"
            "例数 n（派发层实例群规模、非仪器侧）"),
        "renders": png_checks,
        "witness": f"render-witness-r14b.json（{WITNESS_R14B_SHA_PREFIX}，fail-closed 复核）",
    }
    record["kind"] = "tl2_calibration_r24_prep_record"
    record["manipulated_factor"] = (
        "唯一操纵因素=每视图实例数 n：3→6（实例群抽样规模扩容；多实例协"
        "议 v1.3 附录；12 个 reader 智能体、24 次盲读=24 派次、两波次串"
        "行）；指引（observation-guidance-r23.md 字节复用零改写+派发层前"
        "缀覆盖 R24T/R24B）/渲染（renders-r14b 四图字节冻结）/GT/阈值/协"
        "议正文零变更")
    record["measurement_design"] = {
        "comparison_set": {
            "note": (
                "比较集四行全部由盘上在案值双源装载交叉核对（fail-closed、"
                "非手抄）：r16=axis-plan baselines_registered.r16_baseline+"
                "round23-dev-record 台账 r16_baseline+run-r23 baseline_"
                "cross_check 三源一致；r19=run-r22 r19_reference_tuple+"
                "round23 台账 r19_axis3+run-r23 r19_reference_tuple 三源一"
                "致；r22=run-r22 r22_m_tuple_6dp+round22-dev-record this_"
                "round_measured+round23 台账 r22_repeat 三源一致；r23="
                "run-r23 r23_m_tuple_6dp+round23 this_round_measured+"
                "round23 台账 r23_attribution 三源一致"),
            "rows": [
                {"role": "主基线=零变更最新轮", "round": "r16_baseline",
                 "tuple": M_TUPLE_R16},
                {"role": "轴3 单变量轮（历史最佳 M1）", "round": "r19",
                 "tuple": M_TUPLE_R19},
                {"role": "同指引重复轮（r16 先例）", "round": "r22",
                 "tuple": M_TUPLE_R22},
                {"role": "报告框收敛归因轮（本轮设计出处）", "round": "r23",
                 "tuple": M_TUPLE_R23},
            ],
            "scope": (
                "M 元组比较为 development 域描述性对照（axis ledger 延续登"
                "记、rubric 口径）；跨轮实例群漂移混杂照旧声明；M4 跨口径"
                "粒度差异如实单列（见 m_tuple_definitions.M4 与 "
                "adjudication.metric_lesson_separate）"),
        },
        "items": [
            {
                "item": 1,
                "name": "主记录单位=实例",
                "text": (
                    "每实例（12 个 reader 实例=智能体：top 侧 6+bottom 侧 "
                    "6，各包同侧两板：同一实例先 applied 后 prep1）给出其"
                    "视角两板合计的 flag_count、abstain_count、abstain_"
                    "rate（分母=该实例该侧两板全部旗标，跨两板合计）、非"
                    "弃权旗标清单、逐旗与 GT 的 containment/area_ratio 匹"
                    "配明细（比较器 fail-closed 校验照旧；flag_id 编号同实"
                    "例同侧跨板连续）"),
            },
            {
                "item": 2,
                "name": "视角层聚合",
                "text": (
                    "每视角 6 实例的 flag_count/abstain_rate/matches 各给"
                    "中位数+最小值+最大值，如实三分列、不取整"),
            },
            {
                "item": 3,
                "name": "GT 匹配聚合双口径",
                "text": (
                    "union（≥1/6 实例命中即计）与 agreement（≥4/6 过半数"
                    "实例命中才计）两口径并列报告，均如实、不二选一；逐 GT "
                    "条目给出 matched_by_count（0..6）；agreement ≥4/6="
                    "v1.1「≥2/3 过半数」语义的 n=6 推广（v1.3 附录显式冻"
                    "结、不得事后收放）"),
            },
            {
                "item": 4,
                "name": "联合门评价（APR-0011）",
                "text": (
                    "代表配置=每视角取 flag_count 升序第 3 序位（下中位）实"
                    "例组成代表配置（n=6 中位数=第 3/4 序位均值可能非整数"
                    "→代表实例按下中位序位选取、并列按实例编号先序——规则"
                    "预注册、不得事后调整，与 r22/r23 中位数实例口径的差异="
                    "v1.3 附录显式声明），计算一轮 joint 结果；同时如实给"
                    "出 per-metric 实例间范围（min..max）；代表配置 joint "
                    "结果、per-metric 实例间范围、逐实例原始记录（item 1）"
                    "三者并列如实呈现，不合并、不挑优；APR-0011 阈值零改动"),
            },
            {
                "item": 5,
                "name": "bottom 零旗标处理",
                "text": (
                    "沿用库侧 cal._ratio 先例（pcbflow/calibration.py _ratio："
                    "零分母→None）——实例/视角层遇零旗标分母时弃权率=None+"
                    "文字说明，不编造数值（r10 run-record bottom=0/0→None "
                    "与 r22 bottom-i1 同口径在案）"),
            },
        ],
        "m_tuple_definitions": {
            "M1_top_aggregate_abstain_rate": (
                "top 全旗聚合弃权率 = 12 派次（applied+prep1 两态 × i1–i6 "
                "六实例）top 全部旗标中弃权占比（6 位定点）"),
            "M2_bottom_aggregate_abstain_rate": (
                "bottom 同口径（12 派次：applied+prep1 两态 × bottom-i1–i6 "
                "六实例）"),
            "M3_blackdot_abstain_flags_rubric": (
                "黑点族弃权旗数（分型件 rubric 词元口径：圆点/实心圆/黑点/"
                "黑色圆等，双侧双视图，与 run-r23 black_dot_tracking 同法）"),
            "M4_top_per_instance_rate_range": (
                "top 逐实例弃权率极差（12 个实例率的最大−最小）"),
            "M4_operationalization_note": (
                "12 个实例率=（applied-top|prep1-top 两态）×（i1–i6 六实"
                "例）共 12 个（态,实例）格各自弃权率，先 6 位定点取率再取"
                "最大−最小；与 r16–r23「逐实例两板合计」（3 格）口径的粒度"
                "差异=v1.3 扩容口径显式登记；阈值 0.261904=r16 基线历史口"
                "径在案值原样引用不改写（跨口径比较=描述性、如实声明）"),
            "split_half_M1_diff": (
                "|M1(i1–i3 双视图聚合) − M1(i4–i6 双视图聚合)|（6 位定点整"
                "数交叉相乘比较）"),
            "split_half_operationalization_note": (
                "双视图=applied+prep1 两态合并聚合：a_6dp=round(i1–i3 弃权"
                "数×1000000/i1–i3 旗数)、b_6dp 同法（i4–i6）——6 位定点整"
                "数、不做浮点除法；split_half_6dp=|a_6dp−b_6dp|；阈值="
                "0.09064 的 6 位定点=90640 整数（≤ 为 instance_dominated "
                "支条件、> 为 not_instance_dominated 支条件）；本轮首次启"
                "用的实例群内部一致性度量"),
            "scope": (
                "全部=24 派次全口径（非代表配置子集）；单位=旗标条数（M3）"
                "或 6 位定点率（M1/M2/M4/split_half_M1_diff）；与 axis-"
                "experiment-plan-r17-r20 benefit_metrics 及分型件同血统按 "
                "n=6 扩写"),
        },
        "preregistration_declaration": (
            "本节先于 R24 盲读冻结（本记录=预注册件；evaluation-protocol-v1 "
            "§4 口径：轮次开始后不得增删）；五条逐条预注册+M 元组 n=6 口径"
            "五键（M1/M2/M3/M4/split_half_M1_diff）逐字冻结，聚合口径全部"
            "如实并列、不二选一、不挑优（items 沿 r23-prep-record "
            "measurement_design.items 同一口径按本轮改写：24 派次=2 板×2 "
            "视图×6 实例、12 智能体各包同侧两板、编号同实例同侧跨板连续；"
            "reader 前缀 R24T/R24B=派发层覆盖（r16/r22 先例）；图"
            "像=renders-r14b 四图（字节冻结）；聚合口径与 s71/s74/s77/s82 "
            "比较脚本同血统；代表配置/逐实例/双口径分列）；比较集=r16 基线"
            "+r19/r22/r23 实测元组（四行全部盘上在案值三源装载交叉核对）"),
    }
    record["no_instrument_change"] = True
    record["no_loosening_note"] = (
        "实例数扩容不是判据收紧也不是放宽：旗标产出与否、类别判定标准、弃"
        "权判据与报告义务零变更（指引字节复用零改写——反放宽条款「" + NO_LOOSENING_SENTENCE + "」随基座逐字保留、本记录恰引用 1 次）；"
        "显式防止「扩容摊薄弃权率」误读：M1/M2=全旗聚合率口径、扩容只提高"
        "聚合的抽样稳定性、不改变单旗弃权判定标准（G1 守门照常独立计算）；"
        "M4(n=6)/split_half_M1_diff 双判据=归因方向判别的描述性边界、非门、"
        "不触碰 APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate"
        "≤0.5）与任何阈值常量（CONTAINMENT_MIN/AREA_RATIO_MAX，只作口径引"
        "用）——门照常独立计算；不构成任何阈值反向放宽")
    record["no_visual_reading"] = True
    record["pre_round_review"] = {
        "basis": (
            "本轮无指引无渲染变更（指引=observation-guidance-r23.md 字节复"
            "用零改写=866b0157 全 64 位实测锚、渲染=renders-r14b 四图字节"
            "冻结=全 64 位实测锚与 witness-r14b 登记值双重比对一致）——无"
            "新视觉材料引入、无新判读面；唯一新增=reader 实例数量（派发层"
            "扩容 3→6），不产生任何新图像内容；r16/r22 零变更轮免视觉评审"
            "先例同型；授权链=round23-dev-record honest_conclusion 下一候"
            "选建议（b）（原文逐字见 user_directive_note）+用户 2026-09-10 "
            "拍板（选项(b)+holdout 暂不启动）"),
        "status": "not_required_zero_change_round",
    }
    record["protected_files_verification"] = {
        "hashes": protected_hashes,
        "note": (
            "受保护文件全 64 位 sha256 实测断言（本脚本开工/收工各验一次；"
            "零改动红线；fail-closed）"),
        "role": "红线执行证据（保护文件零改动+datasets/ 只读+out/ 只读除声明新文件）",
    }
    record["protocol_amendment"] = {
        "blind_read_execution": (
            "24 次盲读 = 4 视角格（applied-top/applied-bottom/prep1-bottom/"
            "prep1-top）× 6 实例（i1–i6）= 12 个 reader 智能体（top 侧 6 + "
            "bottom 侧 6），每个 agent 串行读同侧两板（先 applied 后 "
            "prep1、flag_id 跨板连续编号）产出 2 件 reader-raw-r24-*.txt；"
            "两波次串行（波1=top 侧 6 agent、波2=bottom 侧 6 agent）。"
            "reader 上下文=指引文件（observation-guidance-r23.md 原字节）+"
            "该侧两张 PNG+派发命名指令（round 2026-09-10-r24、前缀 R24T/"
            "R24B、reader_id=reader-r24-top-iK / reader-r24-bottom-iK）；"
            "v1.2 工具行为规约硬性条款照抄（纯 Read 内联判读、禁止任何程"
            "序化图像处理）；零 GT、零历史判读件、零诊断/探针内容、零 r22/"
            "r23 现象描述注入（本记录所载 r23 出局条目转述为编排侧引用，"
            "不进任何 reader 上下文）；输出 JSON schema 同 r23（reader_id/"
            "per_image[{image,flags[{flag_id,category,confidence,abstain,"
            "frame_box_pct,location_evidence}]}]/reading_notes）；Write 工"
            "具落盘、禁长 heredoc；跨实例/跨视角禁止交流（24 次盲读相互独"
            "立、不得交换判读信息——独立性是多实例协议的前提，亦为本轮归"
            "因裁决有效性的前提）"),
        "changes": [
            {
                "id": "multi-instance-protocol-v1.3-n-expansion-appendix",
                "kind": "n_expansion_appendix（纯实例数扩容；判读语义/判"
                        "据/GT/门零变更）",
                "text": (
                    "v1.3 附录：每视图实例数 3→6——12 个 reader 智能体（top "
                    "6+bottom 6）、24 次盲读=24 派次、两波次串行（波1=top "
                    "侧 6 agent、波2=bottom 侧 6 agent）；聚合口径 n=6 推"
                    "广：GT 匹配 union=≥1/6 实例命中即计、agreement=≥4/6 "
                    "过半数（v1.1 ≥2/3 过半数语义推广）、联合门代表配置=每"
                    "视角 flag_count 升序第 3 序位（下中位）实例；v1/v1.1/"
                    "v1.2 全部继承不改（v1.2 工具行为规约硬性条款照抄）；"
                    "协议正文文件 evaluation-protocol-v1.md 零字节不动——"
                    "v1.3=本记录内登记的附录、不新建协议文件"),
            },
        ],
        "naming": (
            "reader_id=reader-r24-{top,bottom}-i{1..6}；flag_id 前缀 R24T/"
            "R24B=派发层覆盖（指引字节复用致其 §6 落盘原文为 R23T-/R23B-、"
            "round_id 落盘原文为 2026-09-10-r23——派发指令覆盖、前缀差异登"
            "记在案；r16 先例：r15 指引+R16T 前缀、r22 先例：r19 指引+"
            "R22T/R22B）；实例间编号独立，同实例同侧跨板连续"),
        "protocol_id": "evaluation-protocol-v1",
        "scope_note": (
            "本轮协议侧唯一变更=v1.3 n 扩容附录（纯实例数扩容、判读语义/"
            "判据/GT/门零变更）；in_calibrated_range 恒 False 不变"),
        "v1_1_semantics": (
            "每视角多独立实例+聚合口径：实例层主记录、视角层中位数/最小/"
            "最大聚合、GT 匹配 union/agreement 双口径并列、联合门代表配置+"
            "实例间范围并列（measurement_design 五条）；本轮 n=6 扩容执行"
            "（v1.1 原文 n=3 口径由 v1.3 附录推广、v1.1 语义不改）"),
        "v1_2_semantics": (
            "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派发指"
            "令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/放大/像"
            "素分析/衍生图像生成等）；判读只允许以 Read 工具查看原图（同一"
            "原图可重复查看）」——仪器行为钉住；属派发层，读者上下文=指引+"
            "同侧两张 PNG+派发指令（含规约条款），零 GT；不影响判读语义——"
            "分类判据零变更，仅输入手段固定"),
        "v1_3_semantics": (
            "本轮新增 n 扩容附录（见 changes[0]）：每视图实例数 3→6、24 "
            "派次、两波次串行、聚合口径 n=6 推广（union≥1/6、agreement≥4/6 "
            "过半数、代表配置=下中位序位实例）——先于盲读冻结于本记录、"
            "不得事后收放"),
        "v1_file_preserved": {
            "note": (
                "v1 原文零字节保留（r11–r23 轮同口径在案登记，本脚本 "
                "fail-closed 在盘+哈希复核）；v1.3=记录内附录、不新建协议"
                "文件；evaluation-protocol-v2.md=holdout 协议冻结件（s79 "
                "登记在案）本轮不启用——v2 生效≠holdout 启动，holdout 暂"
                "不启动=用户 2026-09-10 拍板"),
            "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
            "sha256_measured": protocol_v1_sha,
            "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
            "zero_byte_preserved": True,
        },
        "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
        "version": "v1.3（n 扩容附录；v1/v1.1/v1.2 继承不改）",
    }
    record["read_prohibition_compliance"] = True
    record["read_prohibition_note"] = (
        "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+magic，"
        "零内容判读、零像素读取）、ground-truth-*、reader-raw-*、derivation-"
        "log-*、任何 compare/评估产物、diag 内容（零读取）；本脚本只读输入="
        "observation-guidance-r23.md（字节复用基座；866b0157 全 64 位锚 "
        "fail-closed，只读零写入）、round23-dev-record.json（343a6747 两父"
        "之一；仅读 axis_experiment_ledger 实测元组/台账行、g2_bifurcation_"
        "record 计数/字母/出局条目锚（GT 字段不转录）、hypothesis_test_i."
        "verdict、next_candidate_suggestion 选项(b)原文——本轮设计出处与"
        "合法性依据）、round22-dev-record.json（b4b8fbe9 两父之二；仅读 "
        "this_round_measured 元组+drift 0.09064 raw text 计数）、axis-"
        "experiment-plan-r17-r20.json（b6ec6467；仅读 baselines_registered "
        "r16 基线四键=M4 阈值锚）、calibration-run-r23.json（15f58350；仅读 "
        "hypothesis_test 顶层判据冻结值字段+guard_channel+verdict——GT 匹"
        "配与逐旗明细不读取、不入记录）、calibration-run-r22.json（80a12c05；"
        "同上口径）、r23-prep-record.json（3c42ace7；结构血统与 24 键镜像来"
        "源+descriptive_boundary_note 照抄源）、render-witness-r14b.json"
        "（b63771f9 锚 fail-closed；四 PNG 见证登记值）、evaluation-protocol-"
        "v1.md（仅在盘+哈希复核，锚=22dc7337）、evaluation-protocol-v2.md"
        "（仅在盘+哈希复核，锚=365b67ef；holdout 冻结件本轮不启用）；保护"
        "三文件（pcbflow/cli.py/pcbflow/config.py/toolchain_lock.json）仅"
        "哈希（开工/收工各验一次）；renders-r14b 四 PNG 仅哈希+magic（渲染"
        "字节冻结以 witness 登记哈希+任务给定全 64 位预期值双重比对为准）；"
        "本轮恰两个新建文件=scripts/s85_calibration_r24_prep.py（生成器本"
        "体）与本记录 r24-prep-record.json（本轮唯一 out/ 新建产物；本轮无"
        "探针/诊断脚本）；reader 派发（后续编排侧执行）上下文=observation-"
        "guidance-r23.md 原字节+同侧两张 PNG（renders-r14b）+派发指令（"
        "round 2026-09-10-r24、前缀 R24T/R24B、reader_id=reader-r24-{top,"
        "bottom}-i{1..6}、v1.2 工具行为规约硬性条款照抄），零 GT、零历史判"
        "读件、零诊断/探针内容、零 r22/r23 现象描述注入、零指引之外的解释；"
        "视觉判读禁止由编排/收口包兼任；跨实例/跨视角禁止交流（24 次盲读相"
        "互独立、不得交换判读信息——独立性是多实例协议的前提，亦为本轮归"
        "因裁决有效性的前提）。")
    record["round_id_constant"] = ROUND_ID
    record["round_label"] = ROUND_LABEL
    record["round_nature"] = (
        "实例群扩容归因轮（多实例协议 v1.3：每视图实例数 3→6；r23 "
        "confounded 后剩余混杂归因第一轴=实例群轴；本轮=第二十四轮）：唯"
        "一实验变量=实例数 n（每视图 3→6：top 6+bottom 6=12 个 reader 智"
        "能体、24 次盲读=24 派次、两波次串行）；指引字节复用零改写"
        "（observation-guidance-r23.md=866b0157 全 64 位实测锚；派发层前"
        "缀覆盖 R23T/R23B→R24T/R24B、round_id→2026-09-10-r24、reader_id→"
        "reader-r24-*——r16/r22 字节复用+派发层前缀覆盖先例；指引文件内 "
        "§6 示例前缀 R23T/R23B 由派发指令覆盖、非文件改写）；渲染零变更="
        "renders-r14b 四图字节冻结（四 PNG sha256_file 实测与 render-"
        "witness-r14b.json 登记值+任务给定全 64 位预期值双重 fail-closed "
        "比对一致，即 r14–r23 轮盲读所用同一批文件，见 instrument_change；"
        "bottom 两态同图如实声明）；GT/阈值/协议正文零变更（13 条冻结、"
        "v1/v1.1/v1.2 继承不改+v1.3 n 扩容附录；evaluation-protocol-v2="
        "holdout 冻结件本轮不启用——v2 生效≠holdout 启动、holdout 暂不启"
        "动=用户 2026-09-10 拍板）；changed_variables=1（instance_count "
        "n:3→6，见 changed_variables[0]）；执行 round23-dev-record 下一候"
        "选建议（b）（对剩余混杂（判据内容/实例群/其他输出侧因素）做新预"
        "注册轮归因——原文逐字见 user_directive_note）+用户 2026-09-10 拍"
        "板；r23 字母裁决=confounded 维持不改写、不得回溯改判既往轮次"
        "（r8–r23 字母裁决维持不变）；r23 指引已在盘冻结、本轮只读零写入；"
        "盲读由编排侧在本记录之后以 24 次独立实例盲读执行（12 个 reader "
        "智能体各包同侧两板=24 派次）")
    record["schema_version"] = "3.0"
    record["unchanged_components"] = [
        {
            "byte_reuse": True,
            "component": "renders-r14b 四图字节复用（渲染零变更）",
            "note": (
                "开工时 sha256_file 实测四 PNG 并与 render-witness-r14b.json "
                "登记值+任务给定全 64 位预期值逐字双重比对（bottom=renders."
                "applied/prep1.sha256 两态同图 d7284259 如实声明；top="
                "top_zero_change_copies.sha256 298bc620/b2f84524）——四图"
                "即 r14–r23 轮盲读所用同一批文件；本轮零重渲染、零仪器变更"),
            "pngs": png_checks,
            "witness": (
                f"render-witness-r14b.json（{WITNESS_R14B_SHA_PREFIX}，fail-closed 复核）"),
        },
        "判读指引零改写（observation-guidance-r23.md=866b0157 字节复用；"
        "§6 示例旗 ID 前缀 R23T-/R23B- 与 round_id 落盘原文 2026-09-10-r23 "
        "由派发层覆盖为 R24T-/R24B-/2026-09-10-r24——r16/r22 先例；§2–§7 "
        "判据文本随基座逐字保留、反放宽句恰 1 次在案）",
        "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，GT 侧"
        "不再有候选，r9–r23 延续引用）",
        "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate"
        "≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作口径引"
        "用；几何门照常独立计算）；M4 阈值锚 0.261904 与 drift 参照 "
        "0.09064=在案历史值原样引用、零修改",
        "评估协议：v1/v1.1/v1.2 继承不改（evaluation-protocol-v1.md 零字"
        "节保留、本轮不新建协议文件；v1.3=本记录内登记的 n 扩容附录；"
        "evaluation-protocol-v2=holdout 冻结件本轮不启用，见 protocol_"
        "amendment）",
        "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口径在图"
        "像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
        "度量设计与聚合口径：沿 r23-prep-record measurement_design.items "
        "同一口径按 n=6 改写（轮次标识、reader 前缀与实例数按 r24 改写；"
        "union/agreement/代表配置的 n=6 推广=v1.3 附录显式声明）",
    ]
    record["user_directive_note"] = (
        "用户 2026-09-10 拍板：r23 归因轮（字母=confounded）后执行选项(b)"
        "=对剩余混杂（判据内容/实例群/其他输出侧因素）做新预注册归因轮；"
        "holdout 暂不启动（本记录=选项(b) 的第一轴执行轮[实例群轴]预注册"
        "件、先于盲读冻结）。r23 事实锚（round23-dev-record.json 343a6747 "
        "实测在案）：M=(0.484848, 0.571429, 8, 0.520833)（M1=16/33）、G2 "
        "几何门出局条目=1（R23T-004 other_advisory 合并铜块 area_ratio="
        "11.458680>10、prep1/top-i3）、归因三支判据字母裁决=confounded"
        "（唯一正式裁决、轮后不改写）——归因转向=剩余混杂（判据内容/实例"
        "群/其他输出侧因素混杂主导）；round23-dev-record next_candidate_"
        "suggestion options[1] 原文：「" + CANDIDATE_B_OPTION + "」——本"
        "轮=该候选的执行轮（实例群轴单变量直接测量；判据内容/其他输出侧轴"
        "留待后续：如 not_instance_dominated 支命中则下一归因轴=判据内"
        "容）；r23 字母裁决=confounded 维持、轮后不改写；holdout 暂不启动"
        "（evaluation-protocol-v2=holdout 冻结件本轮不启用——v2 生效≠"
        "holdout 启动）；预注册后执行")
    return record


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 开工：保护三文件全 64 位实测（第一次）----
    protected_hashes = {
        "pcbflow/cli.py": _require_full_sha(CLI_PY, CLI_PY_SHA, "pcbflow/cli.py"),
        "pcbflow/config.py": _require_full_sha(CONFIG_PY, CONFIG_PY_SHA,
                                               "pcbflow/config.py"),
        "toolchain_lock.json": _require_full_sha(
            TOOLCHAIN_LOCK, TOOLCHAIN_LOCK_SHA, "toolchain_lock.json"),
    }

    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R23, DEV_RECORD_R22, DEV_RECORD_R23, AXIS_PLAN,
                 R23_PREP_RECORD, RUN_R22, RUN_R23, WITNESS_R14B,
                 EVAL_PROTOCOL_V1, EVAL_PROTOCOL_V2):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件 RECORD 不做前置硬拒绝：落盘阶段防覆写守卫按红线口径执行——
    # 已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等零覆写。

    # ---- 全 64 位锚（任何写路径之前；fail-closed）----
    guidance_sha = _require_full_sha(GUIDANCE_R23, GUIDANCE_R23_SHA,
                                     "observation-guidance-r23.md")
    dev23_sha = _require_full_sha(DEV_RECORD_R23, DEV_RECORD_R23_SHA,
                                  "round23-dev-record.json")
    axis_sha = _require_full_sha(AXIS_PLAN, AXIS_PLAN_SHA,
                                 "axis-experiment-plan-r17-r20.json")

    # ---- 前缀锚 ----
    dev22_sha = _require_prefix_sha(DEV_RECORD_R22, DEV_RECORD_R22_SHA_PREFIX,
                                    "round22-dev-record.json")
    r23_record_sha = _require_prefix_sha(R23_PREP_RECORD,
                                         R23_PREP_RECORD_SHA_PREFIX,
                                         "r23-prep-record")
    run22_sha = _require_prefix_sha(RUN_R22, RUN_R22_SHA_PREFIX,
                                    "calibration-run-r22")
    run23_sha = _require_prefix_sha(RUN_R23, RUN_R23_SHA_PREFIX,
                                    "calibration-run-r23")
    witness_sha = _require_prefix_sha(WITNESS_R14B, WITNESS_R14B_SHA_PREFIX,
                                      "render-witness-r14b")
    protocol_v1_sha = _require_prefix_sha(EVAL_PROTOCOL_V1,
                                          EVAL_PROTOCOL_V1_SHA_PREFIX,
                                          "evaluation-protocol-v1")
    protocol_v2_sha = _require_prefix_sha(EVAL_PROTOCOL_V2,
                                          EVAL_PROTOCOL_V2_SHA_PREFIX,
                                          "evaluation-protocol-v2")

    # ---- 基座只读装载（零写入）----
    guidance_text = GUIDANCE_R23.read_text(encoding="utf-8")
    dev22_text = DEV_RECORD_R22.read_text(encoding="utf-8")
    dev23_text = DEV_RECORD_R23.read_text(encoding="utf-8")

    # ---- 结构探测（实测锚与授权链锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    run23 = json.loads(RUN_R23.read_text(encoding="utf-8"))
    run22 = json.loads(RUN_R22.read_text(encoding="utf-8"))
    dev23 = json.loads(dev23_text)
    dev22 = json.loads(dev22_text)
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    r23_record = json.loads(R23_PREP_RECORD.read_text(encoding="utf-8"))
    if r23_record.get("kind") != "tl2_calibration_r23_prep_record" or \
            r23_record.get("round_label") != "r23" or \
            r23_record.get("schema_version") != "3.0":
        _fail("r23-prep-record 先例件结构漂移")

    probe_witness(witness)
    png_checks = check_renders_byte_freeze(witness)
    guidance_ref = probe_guidance_r23(guidance_text, guidance_sha)
    axis_ref = probe_axis_plan(axis_plan, axis_sha)
    run23_ref = probe_run_r23(run23, run23_sha)
    run22_ref = probe_run_r22(run22, run22_sha)
    dev23_ref = probe_dev_record_r23(dev23, dev23_sha)
    drift_counts = probe_drift_anchor(dev22_text, dev23_text)
    dev22_ref = probe_dev_record_r22(dev22, dev22_sha, drift_counts)

    # descriptive_boundary_note 照抄血统源核对（fail-closed）
    lineage_note = (r23_record.get("hypothesis_test", {})
                    .get("adjudication", {})
                    .get("descriptive_boundary_note", ""))
    if DESCRIPTIVE_BOUNDARY_NOTE != lineage_note:
        _fail("descriptive_boundary_note 未照抄 r23-prep-record 血统原文")

    # ---- 判据逐字断言链：预注册判据原文→json.loads→常量→记录字段 ----
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != \
            "r23-confounded-residual-confound-instance-axis-attribution":
        _fail("hypothesis_test.hypothesis_id 不符")
    adj = HYPOTHESIS_TEST["adjudication"]
    if set(adj.keys()) != {"instance_dominated", "not_instance_dominated",
                           "guard_interrupted", "letter_branch_map",
                           "g2_observation_separate", "three_way_bookkeeping",
                           "mechanism_observation_separate",
                           "metric_lesson_separate",
                           "fixed_point_comparison_note",
                           "descriptive_boundary_note"}:
        _fail(f"adjudication 三支+单列结构不符：{sorted(adj.keys())}")
    if adj["instance_dominated"] != ADJ_INSTANCE_DOMINATED or \
            adj["not_instance_dominated"] != ADJ_NOT_INSTANCE_DOMINATED or \
            adj["guard_interrupted"] != ADJ_GUARD_INTERRUPTED:
        _fail("归因三支判据原文与冻结常量不一致（逐字要求被破坏）")

    # ---- 定点整数自证（零浮点路径）----
    if 928571 - 666667 != M4_ANCHOR_6DP:
        _fail("M4 阈值锚 6 位定点自证失败：928571−666667 != 261904")
    if 862069 - 771429 != DRIFT_6DP:
        _fail("drift 6 位定点自证失败：862069−771429 != 90640")
    if int(round(M4_ANCHOR * 1000000)) != M4_ANCHOR_6DP:
        _fail("M4_ANCHOR_6DP 与 0.261904 不一致")
    if G2_R23 != 1 or G2_R22 != 2 or G2_R19 != 0:
        _fail("G2 对照链常量不符（r19=0/r22=2/r23=1）")

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance_ref=guidance_ref, dev23_ref=dev23_ref, dev22_ref=dev22_ref,
        axis_ref=axis_ref, run23_ref=run23_ref, run22_ref=run22_ref,
        r23_record_sha=r23_record_sha, witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha, protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks, drift_counts=drift_counts,
        protected_hashes=protected_hashes)
    # 结构镜像断言：顶层键集合=r23-prep-record 24 键+protected_files_
    # verification（恰多 1 键、不少 1 键）
    missing = sorted(set(r23_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r23_record.keys()))
    if missing or extra != ["protected_files_verification"]:
        _fail(f"顶层键集合与 r23-prep-record 镜像不符：少={missing}，"
              f"多={extra}（预期恰多 protected_files_verification）")
    if len(record) != 25:
        _fail(f"顶层键数须恰 25：{len(record)}")
    # 结构自证（单变量轮口径）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True")
    if len(record["changed_variables"]) != 1:
        _fail(f"changed_variables 必须恰 1 项（实测 "
              f"{len(record['changed_variables'])}）")
    cv = record["changed_variables"][0]
    if cv["id"] != "instance-count-n3-to-n6-v1.3" or \
            cv["instrument_change"] is not False:
        _fail("changed_variables[0] 不符（唯一操纵因素=实例数 n）")
    if record["guidance_reuse"]["mode"] != "byte_reuse_dispatch_override":
        _fail("guidance_reuse.mode 必须为 byte_reuse_dispatch_override")
    if record["guidance_reuse"]["base_sha256"] != GUIDANCE_R23_SHA or \
            record["guidance_reuse"]["derived_sha256"] != GUIDANCE_R23_SHA:
        _fail("guidance_reuse sha 与 866b0157 锚不符")
    bs = record["guidance_reuse"]["byte_size"]
    if (bs["base"], bs["delta"], bs["derived"]) != (GUIDANCE_R23_BYTES, 0,
                                                    GUIDANCE_R23_BYTES):
        _fail("guidance_reuse.byte_size 必须为 (23125, 0, 23125)（零改写）")
    if record["round_id_constant"] != ROUND_ID or \
            record["round_label"] != ROUND_LABEL or \
            record["declared_date"] != DATE_CONSTANT:
        _fail("轮次标识不符（2026-09-10-r24 / r24 / 2026-09-10）")
    rn = record["round_nature"]
    for needle in ("实例群扩容归因轮", "v1.3", "唯一实验变量=实例数 n",
                   "字节复用", "字节冻结", "changed_variables=1",
                   "holdout 暂不启动", "r16/r22 字节复用+派发层前缀覆盖先例",
                   "24 次独立实例盲读", "非文件改写"):
        if needle not in rn:
            _fail(f"round_nature 缺「{needle}」声明")
    if record["manipulated_factor"] is None or \
            "3→6" not in record["manipulated_factor"]:
        _fail("manipulated_factor 不符（唯一操纵因素=实例数 n:3→6）")
    nl = record["no_loosening_note"]
    for needle in ("不是判据收紧也不是放宽", "扩容摊薄弃权率",
                   "CONTAINMENT_MIN/AREA_RATIO_MAX", NO_LOOSENING_SENTENCE):
        if needle not in nl:
            _fail(f"no_loosening_note 缺「{needle[:20]}…」声明")
    if record["hypothesis_test"]["adjudication"][
            "descriptive_boundary_note"] != DESCRIPTIVE_BOUNDARY_NOTE:
        _fail("记录内 descriptive_boundary_note 与血统源不一致")
    # measurement_design 五条+M 元组定义+比较集
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    mtd = md["m_tuple_definitions"]
    for key in ("M1_top_aggregate_abstain_rate",
                "M2_bottom_aggregate_abstain_rate",
                "M3_blackdot_abstain_flags_rubric",
                "M4_top_per_instance_rate_range", "split_half_M1_diff"):
        if key not in mtd:
            _fail(f"m_tuple_definitions 缺 {key}")
    if "12 派次" not in mtd["M1_top_aggregate_abstain_rate"] or \
            "12 个实例率" not in mtd["M4_top_per_instance_rate_range"] or \
            "0.09064" not in mtd["split_half_operationalization_note"] or \
            "6 位定点整数交叉相乘比较" not in mtd["split_half_M1_diff"]:
        _fail("M 元组 n=6 口径声明不完整")
    rows = md["comparison_set"]["rows"]
    if [r["round"] for r in rows] != ["r16_baseline", "r19", "r22", "r23"]:
        _fail("comparison_set 比较集行不符")
    if (rows[0]["tuple"], rows[1]["tuple"], rows[2]["tuple"],
            rows[3]["tuple"]) != (M_TUPLE_R16, M_TUPLE_R19, M_TUPLE_R22,
                                  M_TUPLE_R23):
        _fail("comparison_set 元组值不符")
    # protocol_amendment v1.3
    pa = record["protocol_amendment"]
    if "v1.3" not in pa["version"] or len(pa["changes"]) != 1:
        _fail("protocol_amendment 必须为 v1.3（n 扩容附录、恰 1 项变更）")
    if "24 次盲读" not in pa["blind_read_execution"] or \
            "R24T/R24B" not in pa["blind_read_execution"] or \
            "reader-r24-top-iK" not in pa["blind_read_execution"] or \
            "禁长 heredoc" not in pa["blind_read_execution"]:
        _fail("protocol_amendment.blind_read_execution 缺盲读执行计划口径")
    if pa["v1_file_preserved"]["zero_byte_preserved"] is not True:
        _fail("v1_file_preserved.zero_byte_preserved 必须为真")
    # pre_round_review 免评审声明
    if record["pre_round_review"]["status"] != \
            "not_required_zero_change_round":
        _fail("pre_round_review.status 不符（零变更轮免评审先例）")
    # protected hashes 与实测一致
    if record["protected_files_verification"]["hashes"] != protected_hashes:
        _fail("protected_files_verification.hashes 与实测不一致")
    # 渲染：四 PNG sha 集合=3 个不同值（两 bottom 同哈希）
    if len({p["sha256_measured"] for p in png_checks}) != 3:
        _fail("四 PNG sha 集合应为 3 个不同值（两 bottom 同哈希）")
    # 反放宽句恰 1 次（canonical bytes 口径）
    record_bytes = hashing.canonical_json_bytes(record)
    if record_bytes.decode("utf-8").count(NO_LOOSENING_SENTENCE) != 1:
        _fail("反放宽句在记录中须恰 1 次（canonical bytes 计数）")

    # 同参重建自证（纯函数）
    rebuild = build_record(
        guidance_ref=guidance_ref, dev23_ref=dev23_ref, dev22_ref=dev22_ref,
        axis_ref=axis_ref, run23_ref=run23_ref, run22_ref=run22_ref,
        r23_record_sha=r23_record_sha, witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha, protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks, drift_counts=drift_counts,
        protected_hashes=protected_hashes)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r24-prep-record")

    # ---- 防覆写守卫 + 落盘（唯一写入目标=RECORD；指引/锚文件零写入）----
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r24-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r24-prep] 重跑自证：r24-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r24-prep-record.json")

    # ---- 收工：保护三文件全 64 位实测（第二次）----
    protected_after = {
        "pcbflow/cli.py": _require_full_sha(CLI_PY, CLI_PY_SHA, "pcbflow/cli.py"),
        "pcbflow/config.py": _require_full_sha(CONFIG_PY, CONFIG_PY_SHA,
                                               "pcbflow/config.py"),
        "toolchain_lock.json": _require_full_sha(
            TOOLCHAIN_LOCK, TOOLCHAIN_LOCK_SHA, "toolchain_lock.json"),
    }
    if protected_after != protected_hashes:
        _fail("收工保护三文件 hash 与开工不一致（红线被破坏，立即停止）")
    if _sha(GUIDANCE_R23) != GUIDANCE_R23_SHA:
        _fail("收工指引 hash 与开工不一致（r23 指引零触碰红线被破坏）")

    # ---- 汇总打印 ----
    print("[r24-prep] 保护三文件开工/收工双验 PASS：pcbflow/cli.py="
          f"{CLI_PY_SHA[:8]}、pcbflow/config.py={CONFIG_PY_SHA[:8]}、"
          f"toolchain_lock.json={TOOLCHAIN_LOCK_SHA[:8]}（全 64 位实测一致）")
    print("[r24-prep] 字节复用/冻结锚 PASS：observation-guidance-r23.md="
          f"{guidance_sha}（866b0157，只读零写入，{GUIDANCE_R23_BYTES} B）；"
          f"renders-r14b 四图=applied-top {PNG_APPLIED_TOP_SHA[:8]}/"
          f"prep1-top {PNG_PREP1_TOP_SHA[:8]}/applied-bottom "
          f"{PNG_APPLIED_BOTTOM_SHA[:8]}/prep1-bottom "
          f"{PNG_PREP1_BOTTOM_SHA[:8]}（bottom 两态同图；全 64 位+witness "
          f"b63771f9 三重比对一致）")
    print("[r24-prep] 判据锚 PASS：M4 阈值锚 0.261904=axis-plan"
          f"（{axis_sha[:8]}）baselines_registered.r16_baseline 键位在案+"
          f"run-r23（{run23_sha[:8]}）baseline_cross_check 交叉核对；定点自"
          f"证 928571−666667=261904；drift 0.09064 在案计数 dev22={drift_counts['round22']}/"
          f"dev23={drift_counts['round23']}（round22-dev-record="
          f"{dev22_sha[:8]}），定点 862069−771429=90640")
    print(f"[r24-prep] r23 实测锚 PASS：round23-dev-record={dev23_sha[:8]}"
          f"（M=(0.484848, 0.571429, 8, 0.520833)、G2=1、verdict=confounded"
          f"维持不改写）；候选(b)原文逐字在案；run-r22={run22_sha[:8]}"
          f"（r22 元组+r19 参照）；比较集四行三源交叉核对一致")
    print(f"[r24-prep] 顶层键镜像断言：与 r23-prep-record 逐键一致+恰多 "
          f"protected_files_verification PASS（{len(record)} 键）；"
          f"changed_variables=1；反放宽句恰 1 次；归因三支判据原文逐字冻结"
          f"（instance_dominated/not_instance_dominated/guard_interrupted）")
    print(f"[r24-prep] 工件 sha256：r24-prep-record.json={_sha(RECORD)}")


if __name__ == "__main__":
    main()
