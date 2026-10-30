#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s87_calibration_r24_devrecord.py — R24 CLOSE 包 B：
round24-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律；
结构血统=s78/s83 同构重建）。

R24=development 域实例群扩容归因轮（多实例协议 v1.3：每视图实例数 3→6；
本轮=第二十四轮；执行 round23-dev-record 下一候选建议 (b)（对剩余混杂
（判据内容/实例群/其他输出侧因素）做新预注册轮归因——原文逐字在案）+
用户 2026-09-10 拍板=授权指令在案；hypothesis_id=r23-confounded-residual-
confound-instance-axis-attribution）。唯一实验变量=实例数 n（每视图 3→6：
12 个 reader 智能体、24 派次=4 视角格×6 实例、两波次串行；指引字节复用
observation-guidance-r23.md[866b0157 实测锚、零改写零派生；派发层前缀
覆盖 R23T/R23B→R24T/R24B——r16/r22 先例]+渲染零变更=renders-r14b 四图
字节复用+GT/阈值/协议正文零变更[v1/v1.1/v1.2 继承不改+v1.3 n 扩容附录
（登记于 r24-prep-record=760af49f 预注册件）；protocol-v2=holdout 冻结
件本轮不启用]）。
【跳号声明延续】r21 号段=axis-experiment-plan-r17-r20（b6ec6467 冻结件）
预留的 R21 全组合条件位——未触发、槽位永久留空（round20-dev-record
next_iteration_targets[0] 已登记「R21 不做」、r22 跳号声明在案
round22-dev-record=b4b8fbe9 r21_skip_declaration 冻结原文引用）；r24 为
r23 之后的时序下一轮、与该 R21 全组合位无涉。
预注册假设归因三支判据轮后裁决（按 r24-prep-record hypothesis_test.
adjudication 原文、脚本实测落支、不预写）=not_instance_dominated（字母
口径，唯一正式裁决，轮后不改写）：G1 维持（六 bottom 实例 courtyard 非
弃权旗全=0）且 M4(n=6)=0.888889≥0.261904（6 位定点 888889≥261904；
M4 阈值=r16 基线历史口径在案值原样引用）、split_half_M1_diff=0.018640
（6 位定点 18640）≤0.09064（6 位定点 90640=|0.862069−0.771429| r15→r16
纯重抽漂移在案参照）——M4 条件超出→离散超出抽样尺度、下一归因轴=判据
内容（判据内容/其他输出侧）。归因结论槽=按实测落支登记：逐实例离散超出
抽样尺度（n=6 首次可看轮内分布形态：top-i1=1.0 vs top-i2=0.117647/
top-i6=0.133333 双峰结构）；split-half 稳定（0.018640≤0.09064）与极差
爆拉（0.888889）并存=聚合稳/个体散的分解结论如实登记——对半聚合互相
抵近而逐实例率跨越整个值域，抽样平均的稳定性不构成判据收敛证据。
「正确测出无效同样是有效证据」三向记账：字母（三支判据按预注册原文执
行）、机制观察（五键落点+三族计数+援引计数+G2 出局条目[本轮=0 空摘录]
+逐实例率分布+split-half 分解，单列不进字母）、度量教训（M4 跨口径粒度
差异=描述性声明[12 格 vs r16–r23 逐实例两板合计口径]+split_half 首次
启用+实例群轴直接操纵的验证力度声明[部分重复≠独立重复]，单列）——三账
分列、不合并、不改写。R24 五键=(M1, M2, M3, M4, split_half_M1_diff)=
(0.552381, 0.692308, 28, 0.888889, 0.018640)（M1=top 全旗聚合弃权率
58/105、M2=bottom 18/26、M3=黑点族 rubric 口径 28、M4=12 个（态,实例）
格弃权率极差 1.0−0.111111）。机制观察单列：三族计数 contact 4/
existence_blackdot 28/existence_other 44（r13–r16 132 条重放对拍逐一
相等后套用）对照 r19（4/4/14）与 r22（2/4/12）与 r23（8/8/7+semantic_
confusion 1）三基线——黑点 28 远高于三基线（n=6 扩容+实例异质性、跨轮
对照=描述性）；援引计数（旗级 §5B=0/(iii-a)=7/分支(=0；notes 级 §5B=
0/24、(iii-a)=8/24、§6=20/24）对照 r19/r22/r23 在案基线；G2 几何门
r19=0→r22=2→r23=1→r24=0 清零=资格门满足（r24 入排序——r20/r22/r23
后首个资格轮）。GT：条目层双口径 union=agreement=1/13=0.076923
（GT-REVC-P1-L1SHORT 由 top-i2 R24T-015/top-i4 R24T-019/top-i5 R24T-
009/top-i6 R24T-015 四实例命中=agreement≥4/6=v1.1「≥2/3 过半数」语义
的 n=6 推广首次计入；r22 首次 agreement 计入的 2/3 里程碑维持不改写）；
通道归因：几何门 0、类别门 6、视角门 0 对照 r19（0/2/0）与 r20（0/0/0）
与 r22（2/4/1）与 r23（1/1/0）。联合门：joint not_met、连续=0、
in_calibrated_range 恒 False 照常。台账八行并列（r16 基线/r17 轴1/
r18 轴2/r19 轴3/r20/r22/r23/r24；前七行=round23-dev-record 台账在案行
逐值继承+本轮 live 复算交叉核对）；排序=r19_axis3 第一、r24 第二（G1/G2
满足=入排序）、r18/r16 参照/r17 末位；显著收益 0.219048≥0.10 描述层
命中（r18 0.126268/r19 0.309891/r22 0.381185/r23 0.286581 亦命中）。
下一候选建议（如实单列、由用户拍板、本包不预写决策）三选项：(a) 接受
发展域现状收束训练环、留出集时机由用户判断（HOLDOUT-PLAN a4b80193
Tier 1/2 候选清单零接触在案）；(b) 判据内容轴归因轮（not_instance_
dominated 支登记的下一归因轴=判据内容[判据内容/其他输出侧]；须新
prep-record 先于盲读冻结）；(c) 同指引重复轮（第三样本分离实例群漂移；
或对输出侧其他因素操作化）。

生成器纪律（s69/s72/s75/s78/s83 血统）：
- 受保护文件锚（开工/收工各验一次）：pcbflow/cli.py/pcbflow/config.py/
  toolchain_lock.json 全 64 位 sha256 实测断言（fail-closed）；
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对；
  24 份 reader-raw 全 64 位锚逐一实测）；
- 日期只用常量 DECLARED_DATE="2026-09-10"；
- 防覆写护栏：round24-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round24-dev-record.json 一件（s86 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s87_calibration_r24_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-10-r24"
ROUND_LABEL = "r24"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round24_dev_record"
EVALUATION_DOMAIN = "development"

# 受保护文件（红线 1：开工/收工各验一次；全 64 位实测锚，fail-closed）
PROTECTED_FILES = {
    "pcbflow/cli.py":
        "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e",
    "pcbflow/config.py":
        "f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a4c13e73baf",
    "toolchain_lock.json":
        "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
}

REL_RUN_R24 = "out/v3-tl2/calibration/calibration-run-r24.json"
REL_RUN_R23 = "out/v3-tl2/calibration/calibration-run-r23.json"
REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_PREP_R24 = "out/v3-tl2/calibration/r24-prep-record.json"
REL_GUIDANCE_R23 = "out/v3-tl2/calibration/observation-guidance-r23.md"
REL_GUIDANCE_R19 = "out/v3-tl2/calibration/observation-guidance-r19.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_DEV_R22 = "out/v3-tl2/calibration/round22-dev-record.json"
REL_DEV_R23 = "out/v3-tl2/calibration/round23-dev-record.json"
REL_OUT = "out/v3-tl2/calibration/round24-dev-record-v2.json"
#: v2 追加件（DEV-E0-004）：与 r1 冻结件差异恰=protected_files_
#: verification 的 cli.py 锚两处（6ed4f3fd→0a738047，铜环案接纳）；r1 零回写。

INSTANCE_ORDER = tuple(
    [f"top-i{i}" for i in range(1, 7)]
    + [f"bottom-i{i}" for i in range(1, 7)])

# 引用件哈希清单（简报在案锚；逐件 live 实测比对，fail-closed）
REFERENCE_HASH_EXPECTED = {
    "run_r24": (REL_RUN_R24, "8a9bdb7d"),
    "prep_r24": (REL_PREP_R24, "760af49f"),
    "guidance_r23": (REL_GUIDANCE_R23, "866b0157"),
    "guidance_r19_base": (REL_GUIDANCE_R19, "8633bda5"),
    "run_r16": (REL_RUN_R16, "2c1f8265"),
    "run_r19": (REL_RUN_R19, "e5755a11"),
    "run_r20": (REL_RUN_R20, "6573a59a"),
    "run_r22": (REL_RUN_R22, "80a12c05"),
    "run_r23": (REL_RUN_R23, "15f58350"),
    "dev_r19": (REL_DEV_R19, "0e2fdd69"),
    "dev_r20": (REL_DEV_R20, "80e3e9e2"),
    "dev_r22": (REL_DEV_R22, "b4b8fbe9"),
    "dev_r23": (REL_DEV_R23, "343a6747"),
    "axis_plan": (REL_AXIS_PLAN, "b6ec6467"),
    "typology": (REL_TYPOLOGY, "6dadac8d"),
}

# 归因三支判据实测锚（写盘前 fail-closed 与 run-r24 盘上值逐一核对；
# 6 位定点整数比较，与 s86 M4_THRESHOLD_6DP/SPLIT_HALF_THRESHOLD_6DP
# 同锚）
M4_THRESHOLD_6DP = 261_904
SPLIT_HALF_THRESHOLD_6DP = 90_640
EXPECT_TOP_ABSTAIN_R24 = 58
EXPECT_TOP_FLAGS_R24 = 105
EXPECT_TOP_RATE_R24 = 0.552381
EXPECT_BOTTOM_ABSTAIN_R24 = 18
EXPECT_BOTTOM_FLAGS_R24 = 26
EXPECT_BOTTOM_RATE_R24 = 0.692308
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_CONTACT_R24 = 4
EXPECT_CONTACT_R16_BASELINE = 10
EXPECT_CONTACT_CHAIN_R13_R16 = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
# 实验对照账五键（axis-experiment-plan benefit_metrics 口径按 n=6 扩写；
# M3 槽位=冻结件黑点族 rubric 口径、本轮实测 28）
EXPECT_M1 = 0.552381
EXPECT_M2 = 0.692308
EXPECT_M3 = 28
EXPECT_M4 = 0.888889
EXPECT_M4_6DP = 888_889
EXPECT_SPLIT_HALF = 0.01864
EXPECT_SPLIT_HALF_6DP = 18_640
EXPECT_SPLIT_HALVES = {"A_i1_i3": {"abstain": 31, "flags": 57,
                                   "rate_6dp": 543_860},
                       "B_i4_i6": {"abstain": 27, "flags": 48,
                                   "rate_6dp": 562_500}}
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17/r18/r19/r20/r22/r23 已测行（dev-r23/run 在案行装载；排序现状对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
EXPECT_R18_MEASURED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                       "M4": 0.277778}
EXPECT_R19_MEASURED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                       "M4": 0.211111}
EXPECT_R20_MEASURED = {"M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25}
EXPECT_R22_MEASURED = {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
EXPECT_R23_MEASURED = {"M1": 0.484848, "M2": 0.571429, "M3": 8,
                       "M4": 0.520833}
EXPECT_R19_DROP_REFERENCE = 0.309891
EXPECT_R18_DROP_REFERENCE = 0.126268
EXPECT_R22_DROP_REFERENCE = 0.381185
EXPECT_R23_DROP_REFERENCE = 0.286581
EXPECT_R24_M1_ABSOLUTE_DROP = 0.219048
# 逐实例旗数/弃权记账（r24 实测；12 实例）
EXPECT_COUNTS = {"top-i1": 24, "top-i2": 17, "top-i3": 16, "top-i4": 22,
                 "top-i5": 11, "top-i6": 15, "bottom-i1": 4, "bottom-i2": 4,
                 "bottom-i3": 4, "bottom-i4": 6, "bottom-i5": 4,
                 "bottom-i6": 4}
EXPECT_ABSTAIN = {"top-i1": 24, "top-i2": 2, "top-i3": 5, "top-i4": 19,
                  "top-i5": 6, "top-i6": 2, "bottom-i1": 0, "bottom-i2": 0,
                  "bottom-i3": 4, "bottom-i4": 6, "bottom-i5": 4,
                  "bottom-i6": 4}
EXPECT_TOP_INSTANCE_RATES = {"top-i1": 1.0, "top-i2": 0.117647,
                             "top-i3": 0.3125, "top-i4": 0.863636,
                             "top-i5": 0.545455, "top-i6": 0.133333}
# 三支判据布尔（not_instance_dominated 命中=M4 条件超出）
EXPECT_TYPE_COUNTS = {"contact": 26, "existence": 30, "other_layer": 2}
EXPECT_BLACK_DOT_BY_INSTANCE = {"top-i1": 4, "top-i2": 0, "top-i3": 0,
                                "top-i4": 4, "top-i5": 4, "top-i6": 0,
                                "bottom-i1": 0, "bottom-i2": 0,
                                "bottom-i3": 4, "bottom-i4": 4,
                                "bottom-i5": 4, "bottom-i6": 4}
EXPECT_RUBRIC_COUNTS = {"contact": 4, "existence_blackdot": 28,
                        "existence_other": 44, "other": 0,
                        "semantic_confusion": 0}
# 援引期望（与 run-r24 实测逐一相等，fail-closed；三计数分开记）
EXPECT_FLAG_IIIA = 7
EXPECT_NOTES_IIIA_SOURCES = sorted([
    "applied-bottom-i1", "applied-bottom-i2", "applied-bottom-i3",
    "applied-bottom-i5", "prep1-bottom-i1", "prep1-bottom-i2",
    "prep1-bottom-i3", "prep1-bottom-i5",
])
EXPECT_NOTES_S6_COUNT = 20
# 守门（G1 六实例全 0 维持；G2 r19=0→r22=2→r23=1→r24=0 清零=资格门满足）
EXPECT_G1_R24 = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0,
                 "bottom-i4": 0, "bottom-i5": 0, "bottom-i6": 0}
EXPECT_G1_BASELINE = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_G1_R20_BROKEN = {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_GATES_R24 = {"geometry": 0, "category": 6, "view": 0}
EXPECT_GATES_R19 = {"geometry": 0, "category": 2, "view": 0}
EXPECT_GATES_R20 = {"geometry": 0, "category": 0, "view": 0}
EXPECT_GATES_R22 = {"geometry": 2, "category": 4, "view": 1}
EXPECT_GATES_R23 = {"geometry": 1, "category": 1, "view": 0}
# GT 命中明细（union=agreement=1/13；L1SHORT 4/6 实例命中=agreement
# ≥4/6 首次计入）
EXPECT_GT_GT_IDS = ["GT-REVC-P1-L1SHORT"]
EXPECT_GT_HIT_FLAGS = {("R24T-015", "top-i2", "prep1"),
                       ("R24T-019", "top-i4", "prep1"),
                       ("R24T-009", "top-i5", "prep1"),
                       ("R24T-015", "top-i6", "prep1")}
# 代表配置（下中位序位=top-i3+bottom-i3；bottom tie=编号先序）
EXPECT_REPRESENTATIVE = {"top": "top-i3", "bottom": "bottom-i3"}
# 24 份 reader-raw 全 64 位锚（与 run-r24 reader.raw_files 逐一实测核对）
READER_RAW_PREFIXES = {
    "applied-top-i1": "84aae6b5", "prep1-top-i1": "23b921a7",
    "applied-top-i2": "671dcfb0", "prep1-top-i2": "ac9e4f2b",
    "applied-top-i3": "cf18682f", "prep1-top-i3": "547f4ad6",
    "applied-top-i4": "d34444bc", "prep1-top-i4": "df9feb5b",
    "applied-top-i5": "e1e75df0", "prep1-top-i5": "f45a6794",
    "applied-top-i6": "7e3f3f07", "prep1-top-i6": "416fc4bc",
    "applied-bottom-i1": "b05c3048", "prep1-bottom-i1": "5ee02484",
    "applied-bottom-i2": "628cbd33", "prep1-bottom-i2": "a01b870e",
    "applied-bottom-i3": "0bdce9c1", "prep1-bottom-i3": "9e02ec9b",
    "applied-bottom-i4": "b326d23b", "prep1-bottom-i4": "291e5285",
    "applied-bottom-i5": "78ecdad3", "prep1-bottom-i5": "9c46ec7c",
    "applied-bottom-i6": "bb8aef93", "prep1-bottom-i6": "1f03a2ea",
}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s87-cal-r24-devrecord] FAIL: {msg}")


def _rel(rel: str) -> Path:
    return REPO / rel


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    with open(_rel(rel), encoding="utf-8") as f:
        return json.load(f)


def verify_protected_files() -> dict:
    """受保护文件全 64 位 sha256 实测断言（开工/收工各验一次；fail-closed，
    有变即 FAIL——红线 1 的脚本侧执行）。"""
    got = {}
    for rel, want in PROTECTED_FILES.items():
        h = _sha(rel)
        if h != want:
            _fail(f"受保护文件实测 sha 与锚不符（零改动红线破坏）: {rel}"
                  f"（{h} ≠ {want}）")
        got[rel] = h
    return got


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
# 归因三支判据逻辑（纯函数；供本件登记值复算与构造用例复用）
# ---------------------------------------------------------------------------

def attribution_verdict_fixed_point(m4_6dp: int, split_half_6dp: int,
                                    g1_ok: bool) -> tuple:
    """主通道归因三支判据（纯函数；与 s86.adjudicate_attribution 同判据
    同锚——判据原文=r24-prep-record hypothesis_test.adjudication；全部
    6 位定点整数比较、字母裁决无浮点路径）。

    (id)  instance_dominated=G1 维持且 M4(n=6)<261904 且 split_half≤90640
          （双条件同时成立）→实例群抽样噪声足以解释元组离散；
    (nid) not_instance_dominated=G1 维持且（M4≥261904 或 split_half>
          90640）（至少一条件超出）→离散超出抽样尺度、下一归因轴=判据
          内容（判据内容/其他输出侧）；
    (gi)  guard_interrupted=G1 破坏（任一 bottom 实例 courtyard 非弃权
          旗>0）→归因悬置、机制观察照常（支序最高）。
    返回 (verdict, branch_key)；本函数与 run-r24 盘上裁决互为交叉核对。
    """
    if not g1_ok:
        return ("guard_interrupted", "guard_interrupted_g1")
    m4_within = m4_6dp < M4_THRESHOLD_6DP
    split_within = split_half_6dp <= SPLIT_HALF_THRESHOLD_6DP
    if m4_within and split_within:
        return ("instance_dominated", "instance_dominated_both_within")
    if not m4_within and not split_within:
        return ("not_instance_dominated",
                "not_instance_dominated_both_exceed")
    if not m4_within:
        return ("not_instance_dominated",
                "not_instance_dominated_m4_exceeds")
    return ("not_instance_dominated",
            "not_instance_dominated_split_half_exceeds")


def _view_abstain_aggregate(run: dict, view: str):
    names = sorted(n for n in run["instances"] if n.startswith(view))
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run16: dict, run19: dict, run20: dict,
                  run22: dict, run23: dict, prep: dict, dev19: dict,
                  dev20: dict, dev22: dict, dev23: dict, typology: dict,
                  guidance23_sha: str, axis_sha: str, typology_sha: str,
                  run24_sha: str, raw_files: dict) -> None:
    # ---- 受保护文件（开工锚；全 64 位） ----
    verify_protected_files()
    # ---- run-r24 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r24":
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
            "r23-confounded-residual-confound-instance-axis-attribution":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "not_instance_dominated":
        _fail("verdict != not_instance_dominated")
    if "唯一正式裁决" not in ht["verdict_text"]:
        _fail("verdict_text 应含「唯一正式裁决」")
    m = ht["measurement"]
    if (m["crit_not_instance_dominated"] is not True
            or m["crit_guard_interrupted"] is not False
            or m["crit_instance_dominated"] is not False):
        _fail("归因三支判据布尔不符（not_instance_dominated=True；"
              "guard_interrupted=False；instance_dominated=False）")
    if not m["letter_branch"].startswith("(nid)"):
        _fail("落支应为 (nid) 支")
    if "0.261904" not in m["letter_branch"] or \
            "下一归因轴=判据内容" not in m["letter_branch"]:
        _fail("落支文本应含 M4 条件超出+下一归因轴=判据内容")
    if m["verdict"] != "not_instance_dominated":
        _fail("measurement.verdict != not_instance_dominated")
    # 归因三支纯函数交叉核对（实际输入=M4=888889 超出、split=18640 内、
    # G1 维持→not_instance_dominated_m4_exceeds；构造反事实：双条件内→
    # instance_dominated、双超出→both_exceed、仅 split 超出→split_half_
    # exceeds、G1 破坏→guard_interrupted=四态可复算）
    if attribution_verdict_fixed_point(888_889, 18_640, True) != \
            ("not_instance_dominated", "not_instance_dominated_m4_exceeds"):
        _fail("归因纯函数实际输入复算不符（M4 超出+split 内→nid_m4）")
    if attribution_verdict_fixed_point(261_903, 90_640, True) != \
            ("instance_dominated", "instance_dominated_both_within"):
        _fail("归因纯函数反事实复算不符（双条件内→instance_dominated）")
    if attribution_verdict_fixed_point(261_904, 90_640, True) != \
            ("not_instance_dominated", "not_instance_dominated_m4_exceeds"):
        _fail("归因纯函数边界复算不符（M4 恰=261904=超出）")
    if attribution_verdict_fixed_point(888_889, 90_641, True) != \
            ("not_instance_dominated",
             "not_instance_dominated_both_exceed"):
        _fail("归因纯函数反事实复算不符（双超出→both_exceed）")
    if attribution_verdict_fixed_point(200_000, 90_641, True) != \
            ("not_instance_dominated",
             "not_instance_dominated_split_half_exceeds"):
        _fail("归因纯函数反事实复算不符（仅 split 超出）")
    if attribution_verdict_fixed_point(888_889, 18_640, False) != \
            ("guard_interrupted", "guard_interrupted_g1"):
        _fail("归因纯函数反事实复算不符（G1 破坏→guard_interrupted）")
    # 本轮实测（top 58/105、bottom 18/26）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R24, EXPECT_TOP_ABSTAIN_R24):
        _fail("top 聚合不符（105/58）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R24, EXPECT_BOTTOM_ABSTAIN_R24):
        _fail("bottom 聚合不符（26/18）")
    if m["top_abstain_rate_r24"] != EXPECT_TOP_RATE_R24 or \
            m["r24_m_tuple_6dp"]["M1"] != EXPECT_TOP_RATE_R24:
        _fail("M1 不符（58/105=0.552381）")
    if m["r24_m_tuple_6dp"] != {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4,
                                "split_half_M1_diff": EXPECT_SPLIT_HALF}:
        _fail("M 五键不符（0.552381/0.692308/28/0.888889/0.01864）")
    if "58/105" not in m["top_abstain_rate_r24_arithmetic"]:
        _fail("M1 算式文本不符")
    if m["m4_top_rate_range_r24"] != EXPECT_M4:
        _fail("M4(n=6) 不符（0.888889）")
    if m["split_half_M1_diff_r24"] != EXPECT_SPLIT_HALF \
            or m["split_half_M1_diff_r24"] * 1000000 != \
            round(EXPECT_SPLIT_HALF * 1000000):
        _fail("split_half 不符（0.018640）")
    # 双判据定点整数复核（避免浮点）：888889≥261904=超出、18640≤90640=内
    if not (EXPECT_M4_6DP >= M4_THRESHOLD_6DP):
        _fail("(nid) M4 条件超出复核不符（888889≥261904）")
    if not (EXPECT_SPLIT_HALF_6DP <= SPLIT_HALF_THRESHOLD_6DP):
        _fail("(nid) split-half 条件内复核不符（18640≤90640）")
    if m["m4_threshold_6dp"] != M4_THRESHOLD_6DP \
            or m["split_half_threshold_6dp"] != SPLIT_HALF_THRESHOLD_6DP:
        _fail("阈值锚登记不符")
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
    # r19/r20/r22/r23 对照行=各自 run live 复算+登记交叉核对
    for doc, want, top_pair, bot_pair in (
            (run19, EXPECT_R19_MEASURED, (39, 18), (7, 4)),
            (run20, EXPECT_R20_MEASURED, (22, 14), (14, 4)),
            (run22, EXPECT_R22_MEASURED, (41, 16), (10, 2)),
            (run23, EXPECT_R23_MEASURED, (33, 16), (14, 8))):
        f_x, a_x = _view_abstain_aggregate(doc, "top")
        fb_x, ab_x = _view_abstain_aggregate(doc, "bottom")
        if (f_x, a_x) != top_pair or (fb_x, ab_x) != bot_pair:
            _fail(f"{want} live 复算不符（{top_pair}、{bot_pair}）")
    rows_live = ht["measurement"]["comparison_rows_live"]
    if rows_live["r19_axis3"] != EXPECT_R19_MEASURED \
            or rows_live["r22_repeat_live"] != EXPECT_R22_MEASURED \
            or rows_live["r23_repeat_live"] != EXPECT_R23_MEASURED \
            or rows_live["r16_baseline"] != {
                "M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}:
        _fail("比较集 live 复算装载不符")
    # contact 族（另列主度量对照）：实测 4、基线 10、链重放 8/15/5/10
    if m["contact_family_abstain_flags_rubric_r24"] != EXPECT_CONTACT_R24 \
            or m["contact_r16_baseline_registered"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            m["contact_r16_baseline_live_replay"] != \
            EXPECT_CONTACT_CHAIN_R13_R16:
        _fail("contact 实测/基线/链重放不符（4、10、8/15/5/10）")
    # 逐实例旗数/弃权率与 r24 对照（本轮无零旗格）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN:
        _fail("逐实例旗数/弃权率不符")
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER if n.startswith("top")}
    if rates != EXPECT_TOP_INSTANCE_RATES:
        _fail("top 逐实例弃权率不符（双峰结构实测锚）")
    # 零旗标派次=0（24 格全部≥1 旗）
    if run["reader"]["zero_flag_parts"]["parts"] != []:
        _fail("零旗标派次应为空（24 格全部≥1 旗）")
    # 代表配置与门（top-i3+bottom-i3；下中位序位、bottom tie=编号先序）
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (20, 9, 0.45, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0 or \
            run["compliance_representative"][
                "critic_calibration_in_range"] is not False:
        _fail("联合门/连续计数/in_calibrated_range 不符")
    if run["representative_configuration"]["members"] != \
            EXPECT_REPRESENTATIVE:
        _fail("代表配置成员不符（top-i3+bottom-i3）")
    if run["representative_configuration"]["selection"]["top"][
            "tie"] is not False or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not True:
        _fail("代表配置 tie 语义不符（top 第 3 序位唯一、bottom tie 按"
              "实例编号先序）")
    # 守门通道（G1 六实例全 0 维持；G2 0→2→1→0 清零=资格门满足）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not True or \
            gc["g2_geometry_gate_r19"] != 0 or \
            gc["g2_geometry_gate_r22"] != 2 or \
            gc["g2_geometry_gate_r23"] != 1 or \
            gc["g2_geometry_gate_r24"] != 0:
        _fail("守门通道不符（G1 维持、G2 0→2→1→0 清零）")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["g1_bottom_courtyard_non_abstain_r24"] != EXPECT_G1_R24 or \
            g12["g1_r16_baseline_live"] != EXPECT_G1_BASELINE or \
            g12["g1_r20_broken_registered"] != EXPECT_G1_R20_BROKEN:
        _fail("守门 G1 实测不符（六实例全 0 维持；基线/r20 对照）")
    # GT 双口径：union=agreement=1/13（L1SHORT 4/6 实例命中）
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (1, 1, 13):
        _fail("双口径不符（union=1/13、agreement=1/13）")
    if dual["union"]["gt_ids"] != EXPECT_GT_GT_IDS or \
            dual["agreement"]["gt_ids"] != EXPECT_GT_GT_IDS or \
            dual["union"]["gt_recall_union"] != 0.076923 or \
            dual["agreement"]["gt_recall_agreement"] != 0.076923:
        _fail("GT 命中登记不符（L1SHORT、1/13=0.076923）")
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    if len(hits) != 1 or hits[0]["matched_by_count"] != 4:
        _fail("GT 命中明细不符（L1SHORT 4/6 实例命中）")
    if {(h["flag_id"], h["instance"], h["state"])
            for h in hits[0]["hits"]} != EXPECT_GT_HIT_FLAGS:
        _fail("GT 命中旗明细不符（R24T-015/019/009/015，全部 prep1）")
    # 通道门计数（几何/类别/视角；r24 vs r19 vs r20 vs r22 vs r23）
    ca = run["channel_attribution"]
    n_geom_r24 = len(ca["channel_1_geometry_gate"][
        "r24_area_ratio_rejected_entries"])
    n_cat_r24 = len(ca["channel_2_category_gate"][
        "r24_category_mismatch_entries"])
    n_view_r24 = len(ca["view_gate_observations"]["r24_entries"])
    n_geom_r23 = ca["gate_chain_since_r6"][
        "geometry_gate_area_ratio_rejected_by_round"]["r23"]
    n_cat_r19 = len(ca["channel_2_category_gate"][
        "r19_category_mismatch_entries"])
    n_cat_r20 = len(ca["channel_2_category_gate"][
        "r20_category_mismatch_entries"])
    n_cat_r22 = len(ca["channel_2_category_gate"][
        "r22_category_mismatch_entries"])
    if (n_geom_r24, n_cat_r24, n_view_r24) != \
            (EXPECT_GATES_R24["geometry"], EXPECT_GATES_R24["category"],
             EXPECT_GATES_R24["view"]):
        _fail("r24 通道门计数不符（0/6/0）")
    if (n_geom_r19 := ca["gate_chain_since_r6"][
            "geometry_gate_area_ratio_rejected_by_round"]["r19"]) != \
            EXPECT_GATES_R19["geometry"]:
        _fail("r19 几何门计数不符")
    if (n_cat_r19, n_cat_r20, n_cat_r22) != \
            (EXPECT_GATES_R19["category"], EXPECT_GATES_R20["category"],
             EXPECT_GATES_R22["category"]) or n_geom_r23 != \
            EXPECT_GATES_R23["geometry"]:
        _fail("r19/r20/r22/r23 通道门计数不符")
    # 机制观察：援引分记、黑点族、top 分型、rubric 族、split-half 分解
    mo = ht["mechanism_observation"]
    cc = mo["criterion_citation_observation"]
    ccounts = cc["citation_counts"]
    if ccounts["flag_level_s5b_literal"] != 0 or \
            ccounts["flag_level_iiia_literal"] != EXPECT_FLAG_IIIA or \
            ccounts["flag_level_branch_literal"] != 0:
        _fail("旗级援引不符（§5B=0、(iii-a)=7、分支(=0）")
    if ccounts["notes_level_s5b"] != 0 or \
            ccounts["notes_level_iiia"] != 8 or \
            ccounts["notes_level_s6_clause"] != EXPECT_NOTES_S6_COUNT:
        _fail("notes 级援引不符（§5B=0/24、(iii-a)=8/24、§6=20/24）")
    if ccounts["notes_level_iiia_sources"] != EXPECT_NOTES_IIIA_SOURCES:
        _fail("notes 级援引来源清单不符（三计数分开记）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 28:
        _fail("黑点族弃权 28 旗全弃权不符")
    if bdt["blackdot_to_non_abstain_count"] != 16:
        _fail("黑点转非弃权旗计数不符（16 条）")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS:
        _fail("rubric 族计数不符（4/28/44/0/0）")
    if rf["replay_proof"]["per_flag_total"] != 132:
        _fail("rubric 重放对拍不符（132 条）")
    ty = mo["abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            len(ty["typology_rows"]) != 58:
        _fail("top 弃权构成分型不符（接触性 26+存在性 30+其他 2；58 条）")
    sh = mo["split_half_decomposition"]
    if sh["split_half_6dp"] != EXPECT_SPLIT_HALF_6DP or \
            sh["half_A"] != EXPECT_SPLIT_HALVES["A_i1_i3"] or \
            sh["half_B"] != EXPECT_SPLIT_HALVES["B_i4_i6"]:
        _fail("split-half 分解不符（543860/562500、18640）")
    # 实验对照账：八行并列/排序（r24 入排序、r20/r22/r23 剔除）/归因结论位
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r24_measured"]["M1"] != EXPECT_M1 or \
            ecl["r24_measured"]["M2"] != EXPECT_M2 or \
            ecl["r24_measured"]["M3"] != EXPECT_M3 or \
            ecl["r24_measured"]["M4"] != EXPECT_M4 or \
            ecl["r24_measured"]["M1_arithmetic"] != "58/105" or \
            ecl["r24_measured"]["M2_arithmetic"] != "18/26" or \
            ecl["r24_measured"]["split_half_M1_diff"] != \
            EXPECT_SPLIT_HALF or \
            ecl["r24_measured"]["contact_family_abstain_flags_rubric"] != \
            4 or ecl["r24_measured"]["existence_other_family"] != 44:
        _fail("实验对照账五键/另列键不符")
    if ecl["r17_axis1_row"] != EXPECT_R17_MEASURED or \
            ecl["r18_axis2_row"] != EXPECT_R18_MEASURED or \
            ecl["r19_axis3_row"] != EXPECT_R19_MEASURED or \
            ecl["r20_combo_registered_row"] != EXPECT_R20_MEASURED or \
            ecl["r22_repeat_registered_row"] != EXPECT_R22_MEASURED or \
            ecl["r23_repeat_registered_row"] != EXPECT_R23_MEASURED:
        _fail("r17/r18/r19/r20/r22/r23 对照行不符")
    if ecl["r16_baseline_registered"]["M1"] != 0.771429 or \
            ecl["r16_baseline_registered"]["M4"] != 0.261904:
        _fail("r16 基线行不符")
    # 台账前七行=round23-dev-record 台账在案行逐值继承（live 交叉核对）
    rows23 = dev23["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    if rows23["r16_baseline"] != ecl["r16_baseline_registered"] and \
            {k: rows23["r16_baseline"][k]
             for k in ("M1", "M2", "M3", "M4")} != \
            {k: ecl["r16_baseline_registered"][k]
             for k in ("M1", "M2", "M3", "M4")}:
        _fail("台账 r16 行与 dev-r23 继承不符")
    if rows23["r17_axis1"] != ecl["r17_axis1_row"] \
            or {k: rows23["r18_axis2"][k]
                for k in ("M1", "M2", "M3", "M4")} != ecl["r18_axis2_row"] \
            or rows23["r19_axis3"] != ecl["r19_axis3_row"] \
            or {k: rows23["r20_combo"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r20_combo_registered_row"] \
            or {k: rows23["r22_repeat"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r22_repeat_registered_row"] \
            or {k: rows23["r23_attribution"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r23_repeat_registered_row"]:
        _fail("台账 r17–r23 行与 dev-r23 在案行继承不符")
    rk = ecl["ranking_by_comparison_rule"]
    if rk["ranking_order_best_first"] != ["r19_axis3", "r24_expansion",
                                          "r18_axis2", "r16_baseline",
                                          "r17_axis1"] or \
            rk["r24_eligibility"] is not True or \
            rk["r20_eligibility"] is not False or \
            rk["r22_eligibility"] is not False or \
            rk["r23_eligibility"] is not False:
        _fail("comparison_rule 排序不符（r19 第一、r24 入排序；"
              "r20/r22/r23 资格门剔除）")
    att = ecl["attribution_conclusion"]["conclusion"]
    if "not_instance_dominated" not in att or "0.261904" not in att or \
            "判据内容" not in att:
        _fail("归因结论位不符（not_instance_dominated/0.261904/判据内容）")
    sb = ecl["significant_benefit_vs_r16"]
    if sb["met"] is not True or \
            sb["r24_m1_absolute_drop"] != EXPECT_R24_M1_ABSOLUTE_DROP or \
            sb["r19_drop_reference"] != EXPECT_R19_DROP_REFERENCE or \
            sb["r18_drop_reference"] != EXPECT_R18_DROP_REFERENCE or \
            sb["r22_drop_reference"] != EXPECT_R22_DROP_REFERENCE or \
            sb["r23_drop_reference"] != EXPECT_R23_DROP_REFERENCE:
        _fail("显著收益不符（0.219048≥0.10；r19 参照 0.309891）")
    # 判据引用=prep-record 原文（逐字一致，共键比对）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("instance_dominated", "not_instance_dominated",
              "guard_interrupted", "letter_branch_map",
              "fixed_point_comparison_note", "g2_observation_separate",
              "descriptive_boundary_note", "mechanism_observation_separate",
              "metric_lesson_separate", "three_way_bookkeeping"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引字节复用锚（byte_reuse_dispatch_override；零改写零派生）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "byte_reuse_dispatch_override" or \
            gr["base"] != "observation-guidance-r23.md" or \
            gr["base_path_rel"] != gr["derived_path_rel"]:
        _fail("guidance_reuse 字节复用声明不符")
    if gr["base_sha256"] != guidance23_sha or guidance23_sha != \
            _sha(REL_GUIDANCE_R23):
        _fail("r23 指引实测 sha 与 866b0157 锚不符")
    if gr["byte_size"] != {"base": 23125, "delta": 0, "derived": 23125}:
        _fail("指引字节账不符（23125+0=23125）")
    if len(prep["changed_variables"]) != 1 or \
            prep["no_instrument_change"] is not True:
        _fail("changed_variables=1/n 扩容单变量、no_instrument_change 不符")
    if "instance-count-n3-to-n6-v1.3" \
            not in json.dumps(prep["changed_variables"], ensure_ascii=False):
        _fail("changed_variables 应为实例数 n 扩容单变量")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R24):
        _fail("prep-record sha 实测与登记不符")
    if axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    # 执行授权链（dev23 下一候选建议 (b)+用户 2026-09-10 拍板；r23 字母
    # =confounded、r22 字母=regressed 维持不改写）
    cand = dev23["next_candidate_suggestion"]["options"][1]
    if "剩余混杂" not in cand["option"] or "预注册" not in cand["option"]:
        _fail("dev-r23 选项 (b) 剩余混杂归因授权原文不符")
    if dev23["round_id"] != "2026-09-10-r23" or \
            dev23["hypothesis_test_i"]["verdict"] != "confounded":
        _fail("dev-r23 先验件常量不符")
    if dev22["round_id"] != "2026-09-09-r22" or \
            dev22["hypothesis_test_i"]["verdict"] != "regressed":
        _fail("dev-r22 先验件常量不符")
    if "g2_bifurcation_record" not in dev22 or \
            "g2_bifurcation_record" not in dev23:
        _fail("dev-r22/dev-r23 g2_bifurcation_record 延续引用源缺失")
    if dev20["round_id"] != "2026-09-09-r20" or \
            dev20["hypothesis_test_i"]["verdict"] != "reject":
        _fail("dev-r20 先验件常量不符")
    if dev19["round_id"] != "2026-09-09-r19" or \
            dev19["hypothesis_test_i"]["verdict"] != "marginal":
        _fail("r19 dev-record 先验件常量不符")
    # 联合评价趋势历史行（dev-r23 冻结转录 r5–r23）
    trend_rows_prior = dev23["joint_evaluation_trend"]["by_round"]
    if [r["round"] for r in trend_rows_prior] != [
            "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "r16", "r17", "r18", "r19", "r20", "r22", "r23"]:
        _fail("趋势历史行（dev-r23）不符")
    # r21 跳号声明冻结原文=dev-r22 在案引用逐字继承
    if dev22["r21_skip_declaration"]["r21_status"] != \
            "冻结计划未执行位（槽位永久留空）":
        _fail("r21 跳号声明继承源状态不符")
    # typology 基线锚（rubric 链式回放前提）
    if typology["matrix"]["round_totals"]["r16"]["families"]["contact"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            typology_sha != _sha(REL_TYPOLOGY):
        _fail("typology contact 基线/实测 sha 不符（r16=10）")
    # 24 份 reader-raw 全 64 位锚（与 run 登记逐一实测核对）
    if set(raw_files) != set(READER_RAW_PREFIXES):
        _fail("reader-raw 清单与 24 件锚集合不符")
    for key, rec in raw_files.items():
        got = _sha(rec["path_rel"])
        if got != rec["sha256"] or not got.startswith(
                READER_RAW_PREFIXES[key]):
            _fail(f"reader-raw 实测 sha 与锚不符: {key}")
    # run-r24 盘上件哈希=简报锚（8a9bdb7d）
    if not run24_sha.startswith("8a9bdb7d"):
        _fail("run-r24 实测 sha 与 8a9bdb7d 锚不符")


def build_dev_record() -> dict:
    """构建 round24-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    protected = verify_protected_files()
    run = _json_load(REL_RUN_R24)
    run16 = _json_load(REL_RUN_R16)
    run19 = _json_load(REL_RUN_R19)
    run20 = _json_load(REL_RUN_R20)
    run22 = _json_load(REL_RUN_R22)
    run23 = _json_load(REL_RUN_R23)
    prep = _json_load(REL_PREP_R24)
    dev19 = _json_load(REL_DEV_R19)
    dev20 = _json_load(REL_DEV_R20)
    dev22 = _json_load(REL_DEV_R22)
    dev23 = _json_load(REL_DEV_R23)
    typology = _json_load(REL_TYPOLOGY)
    guidance23_sha = _sha(REL_GUIDANCE_R23)
    axis_sha = _sha(REL_AXIS_PLAN)
    typology_sha = _sha(REL_TYPOLOGY)
    run24_sha = _sha(REL_RUN_R24)
    _verify_facts(run, run16, run19, run20, run22, run23, prep, dev19,
                  dev20, dev22, dev23, typology, guidance23_sha, axis_sha,
                  typology_sha, run24_sha, run["reader"]["raw_files"])

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

    # 24 份 reader-raw 哈希清单（全 64 位实测）
    reader_raw_manifest = {
        key: {"path_rel": rec["path_rel"], "sha256": rec["sha256"],
              "sha256_prefix_expected": READER_RAW_PREFIXES[key]}
        for key, rec in sorted(run["reader"]["raw_files"].items())}

    # 联合评价趋势：r5–r23 行=round23-dev-record 在案行（冻结转录）；
    # r24 行=本轮 run 实测
    trend_rows = list(dev23["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17",
                                            "r18", "r19", "r20", "r22",
                                            "r23"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r24",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R24, "sha256": run24_sha},
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
            "全旗标合计口径仅作附记（76/131=0.580153，非弃权 55+弃权 76）；"
            "本轮预注册主通道=归因三支判据（(nid) G1 维持且 M4(n=6)≥"
            "0.261904→not_instance_dominated；instance_dominated 支因 M4 "
            "条件超出不命中——split-half 内为聚合稳的分解事实）；bottom "
            "全旗聚合弃权率 18/26=0.692308 为侧观察度量[M2，较 r16 基线"
            "回落、高于 r19–r23]；实例层/视角层分列、全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 1.0=1.0−0.0（bottom-i1/i2=0.0 全非弃权、"
                     "i3–i6=1.0 全弃权）；top 逐实例两板合计口径极差 "
                     "0.882353=1.0−0.117647（top-i1=1.0 全弃权 vs top-i2="
                     "0.117647 双峰结构）；M4(n=6) 12 格口径极差=0.888889"
                     "（top-i1/applied 1.0−top-i2/prep1 0.111111）——两口径"
                     "分列、跨口径比较=描述性声明"),
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
                 "空）；读者产物为冻结证据，本包零改动；派发模式=24 派次"
                 "（4 格×6 实例=12 个 reader 智能体各包同侧两板，"
                 "instance_serial_two_wave 两波次串行保序）；R24T/R24B "
                 "前缀=派发层覆盖（指引字节复用、其 §6 示例前缀 R23T-/"
                 "R23B- 为落盘原文——r16/r22「字节复用+派发层前缀覆盖」"
                 "先例同型、前缀差异登记在案）；flag_id 编号行为=12/12 有"
                 "旗实例全部同实例跨板连续、24 格全部≥1 旗=零零旗格（与 "
                 "prep-record naming「同实例同侧跨板连续」声明相符）；轮内"
                 "同名旗号跨实例出现[R24T-015 见于 top-i2 与 top-i6 等]="
                 "实例间编号独立语义的直接观测、按 (instance, state, "
                 "flag_id) 限定不混淆；本轮无派发操作事故；v1.2 工具规约"
                 "沿用 24/24 派次自述合规与输出格式披露如实登记为混杂因素"
                 "披露，不作废"),
        "parse_rejections": list(run["parse_rejections"]),
        "raw_files": reader_raw_manifest,
        "reader_ids": dict(run["reader"]["reader_ids"]),
        "reader_instance_note": run["reader"]["reader_instance_note"],
        "reroute_by_instance": dict(fc["reroute_by_instance"]),
        "reroute_class_production": fc["reroute_class_production"],
    }

    diagnostic_result = {
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": (
            "representative_configuration（top-i3+bottom-i3，"
            "measurement_design item 4 n=6 口径：每视角 flag_count 升序"
            "第 3 序位（下中位）实例——top 升序 11/15/16/17/22/24 第 3 序位"
            "=top-i3 唯一、bottom 升序 4/4/4/4/4/6 第 3/4 序位同为 4"
            "[i1/i2/i3/i5/i6 五实例并列]→按实例编号先序取 bottom-i3——"
            "bottom tie 如实登记，与 r22/r23 中位数实例口径的差异=v1.3 "
            "附录显式声明）"),
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

    # G2 分岔记录延续（关键机制观察链，照 r20 g1_bifurcation_record/r22
    # g2_bifurcation_record/r23 同名记录先例，如实单列不凌驾字母裁决；
    # 本轮 G2=0 清零=资格门满足——分岔记录转入「链闭合状态」登记）
    g2_bifurcation_record = {
        "bifurcation": (
            "guard 设计意图（top 视非弃权旗标 frame_box_pct 几何门=负责任"
            "报告的报告框 hygiene 守门、出局条目不得回升）与字母裁决的关"
            "系本轮第三换型：r22=G2 破坏压过 M1 带内复制（字母=regressed）"
            "；r23=G2 出局条目未清零本身进裁决（字母=confounded）；r24 "
            "G2=几何门面积比出局条目数被 prep-record 预注册降格为「实测"
            "观察项、非本轮字母支」（G2>0 才触发资格门剔除）——本轮实测 "
            "r19=0→r22=2→r23=1→r24=0 清零（top 非弃权旗 47 条无一超门）、"
            "资格门满足=r24 入排序（r20/r22/r23 后首个资格轮）；字母裁决"
            "本轮由 M4(n=6)/split_half 双判据承担（not_instance_dominated）"
            "——G2 链与字母的两账分列模式维持、本轮无 G2-字母分岔（如实"
            "登记）；r22 字母=regressed、r23 字母=confounded 维持不改写"),
        "continuation": {
            "mode": ("分叉记账模式延续（照 r20 g1_bifurcation_record/r22 "
                     "g2_bifurcation_record/r23 同名记录先例：字母/机制"
                     "教训分列、不合并、不改写）"),
            "round22_dev_record": {
                "path_rel": REL_DEV_R22,
                "sha256": _sha(REL_DEV_R22),
                "sha256_prefix_expected": "b4b8fbe9",
                "section": ("g2_bifurcation_record（r22 轮出局条目摘录与"
                            "反事实构造在案=本链登记起点）"),
            },
            "round23_dev_record": {
                "path_rel": REL_DEV_R23,
                "sha256": _sha(REL_DEV_R23),
                "sha256_prefix_expected": "343a6747",
                "section": ("g2_bifurcation_record（r23 轮 R23T-004 出局"
                            "条目摘录在案=本链上一环）"),
            },
        },
        "counts": {
            "g2_geometry_gate_r19": 0,
            "g2_geometry_gate_r22": 2,
            "g2_geometry_gate_r23": 1,
            "g2_geometry_gate_r24": 0,
            "g2_rejected_entries_r24": 0,
            "g2_eligibility_gate_satisfied_r24": True,
            "g1_bottom_courtyard_non_abstain_r24": dict(EXPECT_G1_R24),
            "g1_baseline_r16_live": dict(EXPECT_G1_BASELINE),
            "g1_r20_broken_registered": dict(EXPECT_G1_R20_BROKEN),
            "contact_family_abstain_flags_rubric_r24": 4,
            "m4_n6_exceeds": True,
            "split_half_within": True,
            "verdict": "not_instance_dominated",
        },
        "counterfactual_check": {
            "function": "attribution_verdict_fixed_point",
            "guards_ok_false": ["guard_interrupted", "guard_interrupted_g1"],
            "both_within": ["instance_dominated",
                            "instance_dominated_both_within"],
            "m4_exceeds_split_within": [
                "not_instance_dominated",
                "not_instance_dominated_m4_exceeds"],
            "split_exceeds_m4_within": [
                "not_instance_dominated",
                "not_instance_dominated_split_half_exceeds"],
            "both_exceed": ["not_instance_dominated",
                            "not_instance_dominated_both_exceed"],
            "note": ("同一 G1 维持输入下 M4 降入 261904 内且 split-half 内"
                     "即字母翻转为 instance_dominated"
                     "（attribution_verdict_fixed_point(261903, 90640, "
                     "True) 构造可复算）；本轮 M4=888889≥261904→"
                     "not_instance_dominated=五态纯函数、构造可测"),
        },
        "declared_date": DECLARED_DATE,
        "letter_vs_fact": {
            "letter": ("not_instance_dominated（(nid) 支="
                       "not_instance_dominated_m4_exceeds；唯一正式裁决，"
                       "轮后不改写；后续任何机制归因不得改判本轮字母；r22 "
                       "字母=regressed、r23 字母=confounded 亦维持不改写）"),
            "gate_chain_fact": ("G2 几何门出局条目 r22=2→r23=1→r24=0 清零"
                                "（r19=0 对照在案；top 非弃权旗 47 条无一"
                                "超门）——机制观察单列、不进字母、不改写字"
                                "母"),
            "status": ("两账分列、不合并、不改写（照 r20 g1_bifurcation_"
                       "record/r22/r23 g2_bifurcation_record「字母/机制"
                       "教训分列」先例）"),
        },
        "observation": (
            "G2 链闭合状态登记：几何门出局条目经 r22（2=silk 宽框）→r23"
            "（1=合并铜块）→r24（0）逐轮回落清零——r22 型宽框与 r23 型合并"
            "体两类机制均未再现（n=6 扩容下 12 个 top 非弃权旗含 6 条 "
            "courtyard 类+6 条 other/silk 类近邻报告、无一 area_ratio>10）"
            "；G2 守门本轮满足资格门语义（guard_ok=不升）且 r24 入排序——"
            "字母裁决与 G2 链分账模式维持；G1=六 bottom 实例 courtyard 非"
            "弃权全 0 维持（r20 破坏 2/0/0 在案=分岔记录）"),
        "role": ("机制教训单列：不凌驾、不改写字母裁决（not_instance_"
                 "dominated 维持唯一正式裁决）；不进任何度量；描述性记录、"
                 "非因果证明"),
        "trigger_source": ("G2 链闭合登记触发=几何门出局条目 r24=0 清零"
                           "（r19=0→r22=2→r23=1→r24=0）；本轮字母判据另由"
                           "M4(n=6)/split_half 双判据承担（非 M1 量级漂移"
                           "路径）"),
    }

    # 三轴实验总收束位（comparison_rule 排序；r24 入排序=r20/r22/r23 后
    # 首个资格轮；guidance-r19 胜出记录维持 conditional/double-entry 现状）
    three_axis_experiment_closeout = {
        "attribution_status_axis3_benefit": (
            "guidance-r19 胜出记录维持 conditional/double-entry 现状：M1 "
            "量级在 r22 新鲜实例群带内复现已登记（机制方向支持）、守门 G2 "
            "于 r22 破坏（字母=regressed 在案）、r23 归因轮落 confounded"
            "（在案）、本轮 r24=实例群扩容轮落 not_instance_dominated（M4 "
            "条件超出=离散超出抽样尺度）——r24 五键 (0.551…, 0.692…, 28, "
            "0.888889) 中 M4/split-half=实例群轴的描述性边界判据、非 guidance-"
            "r19 配置效应读数；复制未达成、不升级：三轴判据（判据内容/"
            "渲染/指引）本轮零触碰（唯一实验变量=实例数 n）、三轴收束决议"
            "与轴停止决议不变；两账并列、不合并、不改写"),
        "comparison_rule_note": (
            "比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json "
            "为准（b6ec6467；FROZEN=先于 R17–R21 任何实验轮盲读冻结）；"
            "r24 在该计划时间界之外（r21 槽位永久留空后的实例群扩容归因"
            "轮=非三判据轴任何一支重开、轴停止决议不变），本轮结果仅登记"
            "于对照账、不触发任何计划内规则分支"),
        "development_domain_discipline": (
            "按协议 v1 §4，本批证据属 development 域，不得冒充未见留出；"
            "in_calibrated_range 恒 False 直到正式采纳（须人工批准）；"
            "达标证据仍须留出集"),
        "final_conclusion_unchanged": (
            "三轴实验最终结论维持=收益最大配置=轴3 单变量（guidance-r19，"
            "M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4；按冻结 "
            "iv_final_selection 全部已测配置中排序最优者）——r24 实例群"
            "扩容归因轮不改变该收束（r24 入排序居 r19 之后第二、唯一实验"
            "变量=实例数 n=非三判据轴重开），仅在机制观察层新增「逐实例"
            "双峰结构+split-half 稳与极差爆拉并存=聚合稳/个体散+G2 链"
            "清零+类别门 6 条逐轮新高」四项事实"),
        "ranking": {
            "eligible_rows": ["r16_baseline", "r17_axis1", "r18_axis2",
                              "r19_axis3", "r24_expansion"],
            "excluded_rows": {
                "r20_combo": "G1 破坏（2/0/0，run-r20 在案）",
                "r22_repeat": "G2 破坏（几何门 0→2，run-r22 在案）",
                "r23_repeat": "G2 破坏（几何门未清零 2→1，run-r23 在案）",
            },
            "ranking_order_best_first": ["r19_axis3", "r24_expansion",
                                         "r18_axis2", "r16_baseline",
                                         "r17_axis1"],
            "status": ("comparison_rule 排序（r24=G1/G2 满足=入排序、居 "
                       "r19 之后第二——M1 0.552381>0.461538、M2 0.692308>"
                       "0.571429）；r20/r22/r23 不入排序（资格门剔除、行仅"
                       "如实入账）"),
        },
        "role": ("三轴实验总收束位（development 域描述性边界工具、非门、"
                 "无字母语义、不凌驾 APR-0011 与阈值；两账并列、不合并、"
                 "不改写）"),
    }

    # 下一候选建议（如实单列、由用户拍板、本包不预写决策）
    next_candidate_suggestion = {
        "context": (
            "r24 实例群扩容归因轮字母=not_instance_dominated（G1 维持且 "
            "M4(n=6)=0.888889≥0.261904=离散超出抽样尺度、下一归因轴=判据"
            "内容[判据内容/其他输出侧]；split_half=0.018640≤0.09064=聚合"
            "稳；r23 字母=confounded、r22 字母=regressed 维持不改写）；实"
            "例群轴的单变量直接测量已完成（n=6 扩容未使逐实例离散收敛——"
            "双峰结构+split-half 稳/极差爆拉并存=聚合稳/个体散）；开发线"
            "收敛（连续达标=0、正式采纳门槛未达）——下一动作如实单列、由"
            "用户拍板、本包不预写决策"),
        "decision_authority": "由用户拍板（本包只列选项、不预写决策）",
        "options": [
            {
                "motivation": ("字母=not_instance_dominated 且归因结论位"
                               "已登记下一归因轴；留出集时机=开发线收敛（须"
                               "用户拍板在案；HOLDOUT-PLAN.md a4b80193 "
                               "Tier 1/2 候选清单零接触在案）；in_calibrated_"
                               "range 恒 False 直到正式采纳（须人工批准）"),
                "option": ("接受发展域现状收束训练环（不再追加迭代轮）；"
                           "留出集时机由用户判断"),
                "preregistration_required": False,
            },
            {
                "motivation": ("not_instance_dominated 支登记的下一归因轴="
                               "判据内容（判据内容/其他输出侧）：实例群轴已"
                               "单变量测毕（离散超出抽样尺度）——候选如实列"
                               "示；新预注册轮先于盲读冻结（prep-record 纪"
                               "律）；本包不预写设计"),
                "option": ("判据内容轴归因预注册轮（对判据条款语义/门限做"
                           "单变量操作化归因；须新 prep-record 先于盲读冻结"
                           "=预注册纪律；方向=归因结论位登记的下一归因轴）"),
                "preregistration_required": True,
            },
            {
                "motivation": ("split-half 稳（0.018640≤0.09064）与极差爆拉"
                               "（0.888889）并存=聚合稳/个体散；同指引重复轮"
                               "（r16/r22 先例同型——配置与 r23 完全同构[指"
                               "引字节复用、渲染字节冻结、仅实例重抽 n=6]）"
                               "可提供第三样本分离实例群漂移；或对其他输出侧"
                               "因素做操作化变更轮（须预注册）"),
                "option": ("再一轮同指引重复轮（第三样本；r16/r22 先例同型，"
                           "n=6 口径）或其他输出侧因素操作化归因轮"),
                "preregistration_required": True,
            },
        ],
        "status": ("下一候选建议（非冻结规则输出——三轴计划已收束、本轮"
                   "为计划外实例群扩容归因轮；本节为 dev-record "
                   "如实登记的选项清单）"),
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 12 派次（两态×i1–i6）全部"
                "旗标中弃权旗占比（6 位小数；本轮实测 58/105）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 18/26）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径=分型件 round_totals "
                "{r}.families.existence_blackdot 同法机械套用；本轮实测 "
                "28、全弃权、六实例逐实例分旗；M3 槽位定义维持冻结件黑点"
                "口径——contact=4 另列不占槽=判据侧对照账纪律延续）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差（本轮 n=6 口径=12 个（态,实例）格率"
                "极差 max−min=1.0−0.111111=0.888889；与 r16–r23 逐实例两板"
                "合计口径（3 格）的粒度差异=v1.3 扩容口径显式登记、跨口径"
                "比较=描述性声明、阈值 0.261904=r16 历史口径在案值原样引用"
                "不改写）",
            "split_half_M1_diff":
                "|M1(i1–i3 双视图聚合)−M1(i4–i6 双视图聚合)|（6 位定点整数"
                "；本轮实测 |0.543860−0.562500|=0.018640；阈值 0.09064="
                "r15→r16 纯重抽漂移在案参照、本轮首次启用）",
            "contact_family_abstain_flags_rubric":
                "contact 族弃权旗数（全视，分型件 rubric 口径；本轮实测 4"
                "[top 2+bottom 2]、r16 基线 10、r13–r16 链 8/15/5/10 在"
                "案——对照账另列、不占 M3 槽位）",
            "scope": ("跨轮统一口径：全部=24 派次全口径（非代表配置子集）、"
                      "与分型件同法；单位=旗标条数（M3/contact）或 6 位小"
                      "数率（M1/M2/M4/split_half_M1_diff）"),
        },
        "cross_round_status": {
            "measured_rows": {
                "r16_baseline": {"M1": 0.771429, "M2": 0.857143,
                                 "M3": 12, "M4": 0.261904},
                "r17_axis1": dict(EXPECT_R17_MEASURED),
                "r18_axis2": dict(EXPECT_R18_MEASURED),
                "r19_axis3": dict(EXPECT_R19_MEASURED),
                "r20_combo": dict(EXPECT_R20_MEASURED),
                "r22_repeat": dict(EXPECT_R22_MEASURED),
                "r23_repeat": dict(EXPECT_R23_MEASURED),
                "r24_expansion": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                  "M3": EXPECT_M3, "M4": EXPECT_M4,
                                  "split_half_M1_diff": EXPECT_SPLIT_HALF},
            },
            "note": ("八行并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合/"
                     "r22 重复轮/r23 归因轮/r24 扩容轮；前七行=round23-"
                     "dev-record 台账在案行逐值继承+本轮 live 交叉核对）；"
                     "按冻结 comparison_rule=(M1 升序, M2 升序, M3 升序, "
                     "M4 升序) 字典序：r20/r22/r23=G 守门破坏经资格门剔除"
                     "不入排序；r24=G1 维持+G2=0=资格门满足=入排序、居 "
                     "r19 之后第二；排序（不含 r20/r22/r23）=r19 轴3 第一、"
                     "r24 第二、r18 轴2 第三、r16 基线参照行第四、r17 轴1 "
                     "末位（M1=0.88 劣于基线=负向）——如实登记、不预写后续"
                     "决策"),
            "role": ("扩容轮五键八行并列登记（comparison_rule 冻结规则的"
                     "已测行并列；r16–r23 行=round23-dev-record 台账在案"
                     "行实测装载+各自 run 内嵌记录 live 复算交叉核对、r24 "
                     "行=本轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r24.json（8a9bdb7d…）盘上值"
            "装载（M1=58/105=0.552381 与 m.top_abstain_rate_r24、M2=18/26="
            "0.692308 与 m.r24_m_tuple_6dp.M2、M3=28 与 black_dot_tracking."
            "rubric_families（rubric 口径 existence_blackdot、r13–r16 132 "
            "条弃权旗重放对拍逐一相等）、M4=0.888889 与 m.r24_m_tuple_6dp."
            "M4、split_half=0.018640 与 m.split_half_M1_diff_r24、contact="
            "4 与 contact_family_abstain_flags_rubric_r24 逐一相等，fail-"
            "closed），非手抄；axis-plan 在案 r16 基线四键 [0.771429, "
            "0.857143, 12, 0.261904] 与 run-r24 baseline_cross_check 交叉"
            "核对一致；M1 绝对降幅 0.771429−0.552381=0.219048 超显著收益"
            "阈值 0.10（描述层命中、与字母裁决分列互不改写——r18/r19/r20/"
            "r22/r23 先例延续；跨轮实例群漂移混杂照旧声明、本轮唯一实验变"
            "量=实例数 n、实例群重抽+扩容=实验操作本身；主判据=归因三支"
            "判据、M4 条件超出→not_instance_dominated）"),
        "next_candidate_r24": (
            "见 next_candidate_suggestion（三选项如实单列、由用户拍板、"
            "本包不预写决策）"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "r24 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "significant_benefit_vs_r16": {
            "definition": ("「显著收益」=相对 r16 基线 M1 绝对降幅 ≥0.10（"
                           "阈值覆盖跨轮实例群漂移噪声的历史幅度，参照 "
                           "r15→r16 纯重抽变动 0.09064）"),
            "met": True,
            "note": ("r24 M1 绝对降幅 0.219048 ≥0.10=显著收益定义在描述层"
                     "命中（r18 降幅 0.126268、r19 降幅 0.309891、r22 降幅 "
                     "0.381185、r23 降幅 0.286581 亦 ≥0.10）；r24 降幅须与"
                     " n=6 分母效应（top 旗数 33→105）并读、实例群混杂照旧"
                     "声明；字母裁决与实验账分列互不改写"),
            "r18_drop_reference": EXPECT_R18_DROP_REFERENCE,
            "r19_drop_reference": EXPECT_R19_DROP_REFERENCE,
            "r22_drop_reference": EXPECT_R22_DROP_REFERENCE,
            "r23_drop_reference": EXPECT_R23_DROP_REFERENCE,
            "r24_m1_absolute_drop": EXPECT_R24_M1_ABSOLUTE_DROP,
        },
        "status": ("R24 实测 (M1,M2,M3,M4,split_half)=(0.552381, 0.692308,"
                   " 28, 0.888889, 0.018640)（contact=4 另列）；r24 入排序"
                   "（G1/G2 满足）、居 r19 之后第二；排序=r19_axis3 第一（"
                   "如实记录）；字母与实验账分列互不改写（本轮 not_instance_"
                   "dominated：M4 条件超出=离散超出抽样尺度、下一归因轴="
                   "判据内容）；guidance-r19 胜出记录维持 conditional/"
                   "double-entry 现状、复制未达成不升级；三轴实验已收束"
                   "（收益最大配置=r19_axis3 维持）"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4,
                                "split_half_M1_diff": EXPECT_SPLIT_HALF},
    }

    # 机制观察单列（逐实例分布/split-half 分解/三族对照/黑点/援引）
    mechanism_observation_r24 = {
        "citation_counts_vs_r19_r22_r23": {
            "r24_measured": {
                "flag_level_branch_literal": 0,
                "flag_level_iiia_literal": 7,
                "flag_level_s5b_literal": 0,
                "notes_level_iiia": "8/24 派次（bottom-i1/i2/i3/i5 两板）",
                "notes_level_s5b": ("0/24 派次（本轮指引字节复用、仍无 "
                                    "§5B 节=任何援引为零上下文）"),
                "notes_level_s6_clause": ("20/24 派次（非援引 4 派次="
                                          "applied/prep1-top-i3+applied/"
                                          "prep1-top-i5；指引字节复用、§6 "
                                          "条款随基座在案[非本轮变量]）"),
            },
            "r19_baseline_registered": {
                "flag_level": "旗级「(iii-a)」6 旗+「分支(」2 旗",
                "notes_level": "notes 级 10/12 派次",
                "source": ("run-r19/r23-prep-record run_r19_metric_anchor "
                           "在案"),
            },
            "r22_baseline_registered": {
                "flag_level": "旗级全 0",
                "notes_level": "notes 级 (iii-a)=6/12 派次",
                "source": "run-r22 在案",
            },
            "r23_baseline_registered": {
                "flag_level": "旗级全 0",
                "notes_level": "notes 级 (iii-a)=4/12、§6 条款=6/12",
                "source": "run-r23 在案",
            },
            "status": ("§5B、(iii-a) 与 §6 条款援引计数三集合分开记、对照 "
                       "r19/r22/r23 三基线如实（旗级 (iii-a)=7 旗逐旗摘录"
                       "在案 run-r24 iiia_flag_rows；notes 级 8/24 与 §6 "
                       "20/24=n=6 分母扩容下的机械计数、如实登记）；不进"
                       "字母裁决"),
        },
        "instance_distribution_observation": {
            "note": ("逐实例率分布（n=6 首次可看轮内分布形态；单列、不进"
                     "字母裁决）：top 六实例=1.0/0.117647/0.3125/0.863636/"
                     "0.545455/0.133333——双峰结构（top-i1=1.0 全弃权与 "
                     "top-i4=0.863636 为高峰、top-i2/top-i6≈0.11–0.13 为"
                     "低谷）；同一实例两板率接近（态内一致）、跨实例率跨越"
                     "整个值域=离散主要来自实例间异质性而非态间/判读噪声；"
                     "bottom 六实例=0.0/0.0/1.0/1.0/1.0/1.0（两极）；"
                     "聚合 M1=0.552381 落两峰之间=聚合值对实例抽样敏感的"
                     "直接展示；12 个（态,实例）格率极差[M4(n=6) 口径]="
                     "0.888889"),
            "top_rates": dict(EXPECT_TOP_INSTANCE_RATES),
            "bottom_rates": {"bottom-i1": 0.0, "bottom-i2": 0.0,
                             "bottom-i3": 1.0, "bottom-i4": 1.0,
                             "bottom-i5": 1.0, "bottom-i6": 1.0},
            "m4_12_cell_range": EXPECT_M4,
        },
        "split_half_decomposition": {
            "note": ("split-half 稳 vs 极差爆拉的分解解读（单列、不进字母"
                     "裁决）：split_half_M1_diff=0.018640（A=31/57=0.543860"
                     " vs B=27/48=0.562500）≤0.09064=对半聚合高度稳定；"
                     "同一数据 M4(n=6)=0.888889 远超 0.261904 参照——两者"
                     "并存=「聚合稳/个体散」分解：高/低弃权实例在对半中"
                     "配平使聚合抵近、逐实例率却跨越整个值域；抽样平均的"
                     "稳定性不等于个体判读的一致性、聚合稳定不构成判据收敛"
                     "证据（与本轮字母=not_instance_dominated 一致）"),
            "half_A": dict(EXPECT_SPLIT_HALVES["A_i1_i3"]),
            "half_B": dict(EXPECT_SPLIT_HALVES["B_i4_i6"]),
            "split_half_6dp": EXPECT_SPLIT_HALF_6DP,
            "threshold_6dp": SPLIT_HALF_THRESHOLD_6DP,
        },
        "rubric_families_vs_baselines": {
            "r19_registered": {"contact": 4, "existence_blackdot": 4,
                               "existence_other": 14},
            "r22_registered": {"contact": 2, "existence_blackdot": 4,
                               "existence_other": 12},
            "r23_registered": {"contact": 8, "existence_blackdot": 8,
                               "existence_other": 7},
            "r24_measured": {"contact": 4, "existence_blackdot": 28,
                             "existence_other": 44},
            "status": ("三族计数（分型件 rubric 口径）对照 r19（4/4/14）"
                       "与 r22（2/4/12）与 r23（8/8/7）三基线：contact 4="
                       "与 r19 持平、黑点 28=远高于三基线（n=6 扩容+实例"
                       "异质性；跨轮对照=描述性、如实声明）、存在性其他 "
                       "44=远高于三基线（同因）——r13–r16 132 条重放对拍"
                       "逐一相等后套用 r24，如实登记为度量教训、不改字母"),
        },
        "black_dot_observation": {
            "by_instance": dict(EXPECT_BLACK_DOT_BY_INSTANCE),
            "counts": ("黑点族弃权旗 28 条（全弃权、六实例逐实例分旗："
                       "top-i1/i4/i5 各两板 4+bottom-i3/i4/i5/i6 各两板 4）；"
                       "另黑点转非弃权旗 16 条（top-i2/top-i6/bottom-i1/"
                       "bottom-i2 各两板 4=黑色圆点/圆孔按 §4(ii) 孤立或"
                       "接触路径负责任报告）；判正常派次 2（applied/prep1-"
                       "top-i3 两板；对照 r15=3/r16=2/r18=2/r19=3/r20=4/"
                       "r22=4/r23=2）——如实单列"),
        },
        "top_abstain_typology_r24": {
            "counts": dict(EXPECT_TYPE_COUNTS),
            "note": ("top 弃权 58 条逐旗机械主出口分类（exit_type_"
                     "classify 关键词规则、与 rubric 族两套口径分列不合并；"
                     "逐旗 (instance, state, flag_id) 入账 run-r24 "
                     "abstain_typology.typology_rows）：接触性 26+存在性 "
                     "30+层归属其他 2（对照 r23 6/10/0、r22 2/14/0、r19 "
                     "5/13/0——n=6 扩容后绝对数 16→58、构成仍以存在性/"
                     "接触性两通道为主；rubric 链式回放 r13–r16 基线 "
                     "8/15/5/10 先核对一致才可应用 r24 分型[照 s78 模式]）"),
        },
        "role": ("机制观察单列（per r24-prep-record adjudication."
                 "mechanism_observation_separate 原文）：不进字母裁决、"
                 "不凌驾、不改写字母"),
    }

    # GT 里程碑延续（r22 agreement 首次计入维持；本轮 agreement≥4/6
    # v1.3 n=6 语义首次计入=四实例一致命中）
    gt_agreement_milestone = {
        "agreement_first_counted": (
            "r22 里程碑维持不改写：GT 条目层 agreement 口径自 r12 引入以来"
            "首次计入发生在 r22（≥2/3 语义、GT-REVC-P1-L1SHORT 双实例一致"
            "命中，round22-dev-record 在案）；本轮 r24=agreement≥4/6（v1.1"
            "「≥2/3 过半数」语义的 n=6 推广、v1.3 附录显式冻结）首次计入："
            "union=agreement=1/13=0.076923——GT-REVC-P1-L1SHORT 由 top-i2 "
            "R24T-015/top-i4 R24T-019/top-i5 R24T-009/top-i6 R24T-015 四"
            "实例一致命中（全部 prep1 态；对照 r22 双实例命中未在 r23 复现"
            "=单实例命中不稳定，本轮四实例一致=首个 n=6 口径 agreement 计"
            "入、稳定性信号如实登记、非能力断言）"),
        "gt_id": "GT-REVC-P1-L1SHORT",
        "hit_flags": sorted(f"{i}:{f}:{s}" for f, i, s
                            in EXPECT_GT_HIT_FLAGS),
        "recall": {"agreement": 0.076923, "union": 0.076923},
        "structural_note": ("bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
                            "side=top、bottom GT 无源在案 gt-audit-r1）；"
                            "GT 侧维持全关闭声明延续（gt-audit-r1 三候选"
                            "全部关闭、r9–r23 延续零改动、非新 GT）"),
    }

    honest_conclusion = (
        "本轮（development 域实例群扩容归因轮=多实例协议 v1.3[第二十四轮；"
        "执行 round23-dev-record 下一候选建议 (b)+用户 2026-09-10 拍板]；"
        "唯一实验变量=实例数 n：每视图 3→6[12 个 reader 智能体、24 派次、"
        "两波次串行]；指引字节复用 observation-guidance-r23.md[866b0157 "
        "实测锚、零改写零派生、派发层前缀覆盖 R23T/R23B→R24T/R24B=r16/r22 "
        "先例]+渲染零变更=renders-r14b 四图字节复用[与 r14–r23 盲读同一批"
        "文件]+GT/阈值/协议正文零变更（13 条冻结、v1/v1.1/v1.2 继承不改+"
        "v1.3 n 扩容附录[prep-record 内登记]）；changed_variables=1；实例"
        "群重抽+扩容=本轮实验操作本身；【跳号声明延续】r21=冻结预留全组合"
        "条件位永久留空、r22 跳号声明在案、r24 与该位无涉）24 派次 131 旗"
        "标中 76 弃权、55 非弃权：代表配置（top-i3+bottom-i3；下中位序位、"
        "bottom tie 按实例编号先序如实）gt_recall=0.0（0/13）、"
        "seed_match_rate=0.0（0/11，诊断口径，禁称 precision/FPR）、"
        "abstain_rate=0.45（9/20），联合评价 not_met（gt_recall、"
        "seed_match_rate 两项未达 APR-0011 暂行线；gt_count 13≥12 与 "
        "abstain_rate 0.45≤0.5 单分项入线；诊断对照，非采纳门；连续达标"
        "计数 0→0；GT 条目层 union=agreement=1/13=0.076923[L1SHORT 四实例"
        "一致命中=agreement≥4/6 v1.3 语义首次计入]，如实登记）。预注册假"
        "设（r23-confounded-residual-confound-instance-axis-attribution）"
        "归因三支判据裁决（按 r24-prep-record hypothesis_test.adjudication "
        "原文）=not_instance_dominated（字母口径，唯一正式裁决，轮后不改"
        "写）：落支=(nid) not_instance_dominated_m4_exceeds——本轮=G1 维"
        "持（六 bottom 实例 courtyard 非弃权全 0）且 M4(n=6)=0.888889≥"
        "0.261904（6 位定点 888889≥261904；12 格=（applied-top|prep1-top）"
        "×（i1–i6）各自实例率先 6 位定点取率再取最大−最小；阈值=r16 基线"
        "历史口径在案值原样引用、跨口径比较=描述性）且 split_half_M1_diff="
        "0.018640≤0.09064（6 位定点 18640≤90640）——离散超出抽样尺度、"
        "下一归因轴=判据内容（判据内容/其他输出侧）；instance_dominated "
        "支（双条件均内）不命中=n=6 扩容未使轮内逐实例离散收敛到 r16 基线"
        "极差尺度内；guard_interrupted 支（G1 破坏）未命中。guidance-r19 "
        "胜出记录维持 conditional/double-entry 现状、复制未达成不升级（"
        "r24=实例群轴轮、非三判据轴重开、r24 入排序居 r19 之后第二不改变"
        "收束）。「正确测出无效"
        "同样是有效证据」三向记账：字母=not_instance_dominated（三支判据"
        "按预注册原文执行）、机制观察=逐实例双峰结构（top-i1=1.0 vs top-i2/"
        "top-i6≈0.11–0.13）+split-half 稳与极差爆拉并存=聚合稳/个体散+G2 "
        "链清零（0→2→1→0、资格门满足=r24 入排序）+类别门 6 条逐轮新高+"
        "三族计数对照三基线（黑点 28 远高=n 扩容+实例异质性）+援引计数"
        "（旗级 (iii-a)=7、notes 级 §5B=0/24、(iii-a)=8/24、§6=20/24）"
        "（单列不进字母）、度量教训=M4 跨口径粒度差异（12 格 vs r16–r23 "
        "逐实例两板合计口径、描述性声明）+split_half 首次启用+实例群轴直接"
        "操纵的验证力度声明（部分重复≠独立重复：每实例两派次=同实例重复）"
        "——三账分列、不合并、不改写（g2_bifurcation_record 与归因结论位"
        "承载；反事实构造：M4 降入 261904 内且 split-half 内⇒instance_"
        "dominated、attribution_verdict_fixed_point(261903, 90640, True) "
        "可复算）。G2=0 清零=资格门满足（r20/r22/r23 后首个资格轮）；"
        "r23 字母=confounded 与 r22 字母=regressed 维持不改写。机制观察单"
        "列（不影响字母）：M2=bottom 全旗聚合弃权率 18/26=0.692308（对照 "
        "r16 12/14=0.857143、r19 4/7=0.571429、r20 4/14=0.285714、r22 2/"
        "10=0.2、r23 8/14=0.571429——较 r16 回落、高于 r19–r23）；GT 双口"
        "径 union=agreement=1/13（L1SHORT 四实例一致命中、agreement≥4/6 "
        "v1.3 语义首次计入）；通道归因几何门 0/类别门 6/视角门 0 对照 r19"
        "（0/2/0）与 r20（0/0/0）与 r22（2/4/1）与 r23（1/1/0）。实验对照"
        "账：本轮五键 (M1,M2,M3,M4,split_half)=(0.552381, 0.692308, 28, "
        "0.888889, 0.018640)（M3 槽位=冻结件黑点族口径、contact=4 另列不"
        "占槽），八行并列（r16 0.771429/0.857143/12/0.261904、r17 0.88/"
        "0.75/8/0.333333、r18 0.645161/0.684211/13/0.277778、r19 0.461538/"
        "0.571429/4/0.211111、r20 0.636364/0.285714/6/0.25、r22 0.390244/"
        "0.2/4/0.104545、r23 0.484848/0.571429/8/0.520833、r24 0.552381/"
        "0.692308/28/0.888889+split_half 0.018640）——r20/r22/r23 均资格"
        "门剔除不入排序；r24 入排序居 r19 之后第二；comparison_rule 排序="
        "r19_axis3 第一、r24 第二、r18 第三、r16 参照、r17 末位；显著收益"
        "定义描述层命中（M1 绝对降幅 0.219048≥0.10；r18 0.126268、r19 "
        "0.309891、r22 0.381185、r23 0.286581 亦 ≥0.10；r24 降幅须与 n=6 "
        "分母效应并读）——与字母裁决分列互不改写。三轴实验总收束位：最终"
        "结论维持=收益最大配置=轴3 单变量（guidance-r19）；r24 入排序不改"
        "变收束、实例数 n=非三判据轴重开；发展域证据不得冒充留出。下一候选"
        "建议（如实单列、由用户拍板、本包不预写决策）：(a) 接受发展域现状"
        "收束训练环、留出集时机由用户判断；(b) 判据内容轴归因轮（下一归因"
        "轴=判据内容）；(c) 同指引重复轮第三样本或其他输出侧因素操作化归因"
        "轮。not_instance_dominated=预注册阈值命中方向的描述性结论、非因果"
        "证明——「正确测出无效同样是有效证据」；单轮 development 域只描述"
        "不断言；字母裁决只回答「r19/r22/r23 三轮 M 元组离散是否为实例群抽"
        "样噪声所主导」的判据命中方向；部分重复≠独立重复（同域同编排实例"
        "池、验证力度如实声明）；机制观察/度量教训单列、不凌驾不改写字母"
        "裁决；APR-0011 门（代表配置）与字母裁决分列不合并；本轮判据均为"
        "描述性边界、非门阈值（门零改动）。逐实例残余差异即本轮测量对象"
        "（top 弃权率 1.0/0.117647/0.3125/0.863636/0.545455/0.133333、"
        "bottom 0.0/0.0/1.0/1.0/1.0/1.0——双峰/两极分布如实）；本轮无零旗"
        "格（24 格全部≥1 旗、零分母→None 口径未触发）。不做「能力已修复/"
        "已达成」类断言；in_calibrated_range 恒 False。本批证据按协议 v1 "
        "§4 属 development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r24-prep-record 判据=归因三支判据、阈值零"
         "改动；实例数扩容非判据收紧亦非放宽[no_loosening_note 在案]）。"),
        ("R16 对照基线=calibration-run-r16.json（同一聚合逻辑对内嵌实例记录"
         "双侧复算 top 27/35=0.771429、bottom 12/14=0.857143，与在案登记/"
         "axis-plan 锚交叉核对一致，不手工抄数）；r19/r22/r23 参照元组=各自"
         " run 内嵌实例记录 live 复算（18/39、4/7；16/41、2/10；16/33、"
         "8/14）+prep-record 冻结锚交叉核对一致；contact 对照基线=分型件 "
         "rubric 口径 10（r13–r16 链 8/15/5/10 重放对拍逐一相等后才套用 "
         "r24 分型，不手工抄数）；轮间对比只做方向性描述（跨轮实例群混杂"
         "照旧；本轮唯一实验变量=实例数 n、实例群重抽+扩容=实验操作本身）；"
         "M1 分母（top 旗数 35→39→22→41→33→105）随实例群规模变化、弃权率"
         "比较含分母效应，构成分解（top 弃权构成分型+rubric 族+援引分记+"
         "黑点转非弃权旗）单列补足。"),
        ("归因三支判据的描述性边界纪律：M4(n=6) 阈值 0.261904=r16 基线历史"
         "口径在案值原样引用（12 格 vs 逐实例两板合计口径的粒度差异=v1.3 "
         "扩容口径显式登记、跨口径比较=描述性）；split-half 阈值 0.09064="
         "r15→r16 纯重抽漂移在案参照；两者均不得事后收放；部分重复≠独立重复"
         "（同域同编排实例池、每实例两派次=同实例重复、验证力度如实声明）；"
         "本轮字母裁决只回答「M 元组三轮离散是否为实例群抽样噪声所主导」、"
         "不回答「判据条款是否有效」——后者=下一归因轴（判据内容）的范畴；"
         "G1 破坏（若发生）→guard_interrupted 独占（预注册三支恰三支、不新"
         "增字母支、不升级归因）。"),
        ("G2 分岔链闭合登记（判据设计机制教训，单列，供后续预注册参考、本轮"
         "不追溯适用）：guard 设计意图 vs 字母的分叉记账模式自 r20 "
         "g1_bifurcation_record/r22 g2_bifurcation_record[dev-r22="
         "b4b8fbe9 在案]/r23 同名记录[dev-r23=343a6747 在案]延续；本轮换型="
         "G2 被 prep-record 预注册降格为「实测观察项、非字母支」（G2>0 才"
         "触发资格门剔除）且实测清零（0→2→1→0、资格门满足=r24 入排序）——"
         "预注册字母优先（not_instance_dominated）=预注册纪律的正确执行；"
         "后续如需调整守门操作化定义，修订须走 prep-record 预注册（先于该轮"
         "盲读冻结）、不得事后改判本轮或既往轮次（r8–r23 字母裁决维持不变）。"),
        ("度量教训在案（供后续预注册参考、本轮不追溯适用）：M3 槽位定义维持"
         "冻结件黑点族口径、contact=4 另列不占槽=对照账纪律延续；contact 计"
         "数口径=分型件 rubric 机械套用（r13–r16 132 条重放对拍逐一相等后"
         "套用 r24；计数口径跨轮漂移是历史教训：r15 prose 口径 7 vs 分型件 "
         "rubric 口径 8 在案，axis-plan M3_caveat 已声明一律采用 rubric 口"
         "径）；本轮无零旗格（24 格全部≥1 旗）→零分母 None 口径未触发（先"
         "例条文照登记）；黑点 28 远高于 r19/r22/r23 三基线+M4(n=6) 跨口径"
         "粒度差异=12 格口径（prep-record M4_operationalization_note 延续）"
         "如实登记；实验对照账与字母裁决分列互不改写（r18–r23 先例延续）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=not_instance_"
         "dominated 维持不变（=离散超出抽样尺度、下一归因轴=判据内容的描述性"
         "边界结论、非因果证明；单轮 development 域方向性证据；主通道归因三支"
         "判据与 APR-0011 门分开表述、互不凌驾：门联合评价（代表配置）=not_"
         "met 如实分列）；不得回溯改判既往轮次（r8–r23 字母裁决维持不变、"
         "r22=regressed/r23=confounded 维持）；早期轮字母与实验账分列先例"
         "（r18：reject 但排序居首；r19：marginal 但排序居首；r20：reject 但"
         "降幅命中；r22：regressed 但 M1 带内复制；r23：confounded 但条款对"
         "目标起效；r24：not_instance_dominated 但 M1 降幅命中+入排序居第二）"
         "延续——多账分列不合并。"),
        ("通道归因方法：照抄 run-r15–run-r24 channel_attribution 的重放口径"
         "（deviation_note 承接），R16/R19/R20/R22/R23/R24 均以内嵌输入确定性"
         "重放并与 compare_v3 对拍（run-r24 channel_attribution.method）；"
         "重放复现与在案登记一致（fail-closed）；几何门 r24=0/类别门 r24=6/"
         "视角门 r24=0 如实计数、不构成字母裁决输入以外的门。"),
        ("读者实例行为与派发操作披露如实记录：R24 二十四派次 v1.2 规约自述合规"
         "（纯 Read 直读、24/24 派次自述「未读取盘上任何其他文件」[逐派次句子"
         "程序提取在案 run-r24 reader_tool_evidence]）；输出格式披露（24 件缩"
         "进格式冻结原始判读件、零改动直读）parse 校验全部通过；flag_id 编号"
         "行为=12/12 有旗实例全部同实例跨板连续、24 格全部≥1 旗=零零旗格（与"
         " prep-record naming 声明相符）；R24T/R24B 前缀=派发层覆盖（指引字节"
         "复用、其 §6 示例前缀 R23T-/R23B- 为落盘原文——r16/r22 先例同型、前"
         "缀差异登记在案）；本轮无派发操作事故。跨轮实例不同+轮内实例差异="
         "本轮归因主通道的测量对象（实例群轴直接操纵）；本轮轮前评审=pre_"
         "round_review 在案（r24-prep-record）。"),
    ]

    next_iteration_targets = [
        ("三轴实验总收束位登记：comparison_rule 排序（r19_axis3 第一、r24 "
         "入排序居第二、r18 第三、r16 参照行第四、r17 末位）；r20/r22/r23 "
         "不入排序（资格门剔除、行仅如实入账）；三轴实验最终结论维持=收益"
         "最大配置=轴3 单变量（guidance-r19，M1=0.461538 历史最佳、contact "
         "族 10→4、黑点族 13→4；按冻结 iv_final_selection 全部已测配置中排"
         "序最优者）；guidance-r19 胜出记录维持 conditional/double-entry 现"
         "状、复制未达成不升级（r24=实例群轴轮、非三判据轴重开）。"),
        ("下一候选建议（如实单列，供主审/用户决策；本包不预写决策）："
         "(a) 接受发展域现状收束训练环（不再追加迭代轮），留出集时机由用户"
         "判断（HOLDOUT-PLAN.md a4b80193 Tier 1/2 候选清单零接触在案；正式"
         "采纳门槛=连续 2 轮达标+人工批准未达成、不得写成已达成）；"
         "(b) 判据内容轴归因轮（not_instance_dominated 支登记的下一归因轴="
         "判据内容[判据内容/其他输出侧]；须新 prep-record 先于盲读冻结）；"
         "(c) 再一轮同指引重复轮（第三样本；r16/r22 先例同型、n=6 口径）或"
         "其他输出侧因素操作化归因轮；三选项均由用户拍板。"),
        ("实例群轴结论登记（本轮单变量直接测量的收口）：n=6 扩容未使轮内逐"
         "实例离散收敛到 r16 基线极差尺度内（M4(n=6)=0.888889≥0.261904）="
         "离散超出抽样尺度；split-half 稳定（0.018640≤0.09064）与极差爆拉并"
         "存=聚合稳/个体散的分解——实例群抽样噪声不足以解释 r19/r22/r23 三"
         "轮 M 元组离散的全部、判据内容轴升为下一归因轴（须新预注册轮）；不"
         "得事后改判 r24/r23 或既往轮次。"),
        ("留出集时机=开发线收敛（须用户拍板）：r24 字母=not_instance_"
         "dominated→收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批"
         "准未达成，不得写成已达成）；GT 侧维持全关闭声明延续（gt-audit-r1"
         "[1f20554a…]三候选全部关闭，r9–r23 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r24 union=agreement=1/13[L1SHORT 四"
         "实例一致命中、agreement≥4/6 v1.3 语义首次计入]=稳定性信号如实登"
         "记、非新 GT）；in_calibrated_range 恒 False 直到正式采纳（须人工"
         "批准）；达标证据仍须留出集（out/v3-tl2/holdout/HOLDOUT-PLAN.md "
         "a4b80193… 与 datasets/holdout-candidates-r1 在案）。"),
        ("判读侧残余问题登记：top 弃权 58 条接触性 26/存在性 30/其他 2（机械"
         "主出口分类、逐旗入账）；黑点族弃权 28 条远高于 r19/r22/r23 三基线"
         "（n=6 扩容+实例异质性）；本轮无零旗格（24 格全部≥1 旗）；reroute "
         "类 6 旗（弃权 4+非弃权 2、滥用型通道机械命中=0[「等长」/「蛇形」"
         "子串 6 旗零命中、对照 r23 的 2 旗否定式援引]）；类别门 r24=6 条"
         "（对照 r19=2、r20=0、r22=4、r23=1，逐轮新高、逐条在案）。"),
    ]

    round_identity_declaration = {
        "changed_variables": 1,
        "changed_variables_note": ("唯一实验变量=实例数 n：每视图 3→6（"
                                   "prep-record.changed_variables 长度=1 "
                                   "实测核对一致；实例群抽样规模轴=r23 "
                                   "confounded 支剩余混杂三轴的第一轴；判据"
                                   "内容轴与其他输出侧轴零触碰、留待后续预注"
                                   "册轮）；指引/渲染/GT/阈值/协议正文零变更"),
        "guidance_reuse": {
            "base": "observation-guidance-r23.md",
            "base_sha256_prefix": "866b0157",
            "byte_delta": 0,
            "derived": "observation-guidance-r23.md（同一文件、零派生）",
            "derived_sha256_prefix": "866b0157",
            "mode": "byte_reuse_dispatch_override",
            "transform_base_untouched": True,
        },
        "precedent": ("r16/r22 先例（指引字节复用+派发层前缀覆盖：r16=r15 "
                      "指引+R16T 前缀、r22=r19 指引+R22T/R22B 前缀）——与 "
                      "r23「指引落盘新件、派发前缀与指引一致」路径不同"),
        "round_nature": "实例群扩容归因轮（多实例协议 v1.3；第二十四轮）",
        "section6_prefix_override": (
            "§6 前缀差异登记：本轮指引字节复用、其 §6 示例旗 ID 前缀 R23T-"
            "/R23B- 与 round_id 落盘原文（2026-09-10-r23）为文件落盘原文"
            "（恰 4+1 处与 1 处，程序计数断言在案）；派发指令覆盖为 R24T/"
            "R24B/2026-09-10-r24/reader-r24-*——r16/r22「字节复用+派发层"
            "前缀覆盖」先例同型（对照 r23：指引落盘新件、无差异登记需求）"),
        "sole_variable": ("实例数 n：每视图 3→6（12 个 reader 智能体、24 "
                          "派次=4 视角格×6 实例、两波次串行；聚合口径 n=6 "
                          "推广=union≥1/6、agreement≥4/6、代表配置=下中位"
                          "序位）"),
    }

    r21_skip_declaration = {
        "declaration": (
            "【跳号声明延续】r21 号段=axis-experiment-plan-r17-r20（b6ec6467 "
            "冻结件）combination_decision_rule.ii_full_combination 预留的 "
            "R21 全组合条件位——per early_stop_rule.strong_single_axis_"
            "shortcut「……不铺全组合（R21 不做）」未触发、该槽位永久留空；"
            "round20-dev-record next_iteration_targets[0] 已登记「R21 不"
            "做」；r22 为该登记之后的时序下一轮（r22 跳号声明在案 "
            "round22-dev-record=b4b8fbe9 r21_skip_declaration）；r23 为 "
            "r22 之后的时序下一轮（r23 跳号声明在案 round23-dev-record="
            "343a6747）；r24 为 r23 之后的时序下一轮、与该 R21 全组合位无涉"
            "（非其执行、非其替代）——轮次号跳号以免台账歧义"),
        "frozen_quotes": dev22["r21_skip_declaration"]["frozen_quotes"],
        "r21_status": "冻结计划未执行位（槽位永久留空）",
        "role": ("轮次身份声明（如实登记；防台账歧义；冻结原文=dev-r22 在"
                 "案引用逐字继承）"),
    }

    return {
        "axis_experiment_ledger": axis_experiment_ledger,
        "declared_date": DECLARED_DATE,
        "diagnostic_result": diagnostic_result,
        "directional_observation_vs_r16": [
            ("R16→R24 派发与旗标量对照：盲读派次 12→24（协议侧 v1.3 n 扩容"
             "附录首轮执行、每视图实例 3→6=12 个 reader 智能体各包同侧两"
             "板）；旗标 47（r23）→131（十二实例旗数 top 24/17/16/22/11/"
             "15、bottom 4/4/4/6/4/4；非弃权 55+弃权 76）；全旗标合计弃权"
             "率 0.510638（24/47，r23 附记口径）→0.580153（76/131，附记口"
             "径）；预注册主通道归因三支判据：(nid) G1 维持且 M4(n=6)≥"
             "0.261904⇒not_instance_dominated（唯一正式裁决）；instance_"
             "dominated/guard_interrupted 两支不命中如实分列；代表配置"
             "（top-i3+bottom-i3；bottom tie 按实例编号先序）弃权率 0.428571"
             "（6/14，r19）→0.333333（4/12，r20）→0.466667（7/15，r22）→"
             "0.125（2/16，r23）→0.45（9/20，r24）。"),
            ("视角层三分列（measurement_design item 2，n=6 中位数=第 3/4 "
             "序位均值）：top 六实例弃权率 1.0/0.117647/0.3125/0.863636/"
             "0.545455/0.133333（r24，逐实例两板合计口径极差 0.882353；双峰"
             "结构=top-i1 全弃权 vs top-i2/top-i6 低谷）——聚合落点 27/35="
             "0.771429（r16 基线）→18/39=0.461538（r19）→14/22=0.636364"
             "（r20）→16/41=0.390244（r22）→16/33=0.484848（r23）→58/105="
             "0.552381（r24；较 r16 基线降 0.219048=显著收益定义描述层命"
             "中，须与 n=6 分母效应并读；本轮唯一实验变量=实例数 n）；"
             "bottom 六实例=0.0/0.0/1.0/1.0/1.0/1.0（极差 1.0）——bottom "
             "全旗聚合弃权率 12/14=0.857143（r16）→4/7=0.571429（r19）→"
             "4/14=0.285714（r20）→2/10=0.2（r22）→8/14=0.571429（r23）→"
             "18/26=0.692308（r24）；M4(n=6) 12 格口径极差=0.888889、"
             "split_half=0.018640（聚合稳/个体散分解）单列不进字母。"),
            ("matches 与 GT 双口径（measurement_design item 3，n=6 推广）："
             "r22 union=agreement=1/13（≥2/3 双实例一致命中=agreement 首次"
             "计入）→r23 union=2/13=0.153846、agreement=0/13→r24 union="
             "agreement=1/13=0.076923（GT-REVC-P1-L1SHORT 由 top-i2 R24T-"
             "015/top-i4 R24T-019/top-i5 R24T-009/top-i6 R24T-015 四实例一"
             "致命中=agreement≥4/6 v1.3 语义首次计入）；代表配置 gt_recall"
             "_total 0.0（0/13）、seed_match_rate 0.0（0/11，诊断口径，禁"
             "称 precision/FPR）——轮内 4 条命中全部落在非代表实例=代表配"
             "置对实例异质性的敏感性如实登记；bottom 非弃权旗零匹配属结构"
             "性（GT 13 条全部 side=top、bottom 无 GT 在案 gt-audit-r1）。"),
            ("通道归因（vs R19/R20/R22/R23，预注册重放方法）：几何门面积比"
             "出局 0→0→2→1→0（R19=0→R20=0→R22=2→R23=1→R24=0=清零=资格门"
             "满足[r22 型 silk 宽框与 r23 型合并体两类机制均未再现]）；类别"
             "门 2（r19）→0（r20）→4（r22）→1（r23）→6（r24，逐轮新高、"
             "逐条在案）；视角门 0→0→1→0→0。通道链自 r6：几何门 r6=1→r7="
             "0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→r15=0→r16=0→r17="
             "0→r18=0→r19=0→r20=0→r22=2→r23=1→r24=0。重放与 compare_v3 "
             "对拍一致。"),
            ("预注册假设（r23-confounded-residual-confound-instance-axis-"
             "attribution）归因三支判据字母裁决=not_instance_dominated（唯"
             "一正式裁决）：落支=(nid) not_instance_dominated_m4_exceeds"
             "（per r24-prep-record hypothesis_test.adjudication 原文：G1 "
             "维持且 M4(n=6)≥0.261904 或 split_half>0.09064→离散超出抽样"
             "尺度、下一归因轴=判据内容）；实测：R24 五键=(0.552381, "
             "0.692308, 28, 0.888889, 0.018640)（M1=top 全旗聚合弃权率 58/"
             "105、M2=bottom 18/26、M3=黑点族弃权旗数 28、M4=12 格极差 "
             "0.888889、split_half=0.018640）；比较集 live 复算 r16 (0."
             "771429, 0.857143, 12, 0.261904)/r19 (0.461538, 0.571429, 4, "
             "0.211111)/r22 (0.390244, 0.2, 4, 0.104545)/r23 (0.484848, "
             "0.571429, 8, 0.520833)→M4 6 位定点 888889≥261904=超出、"
             "split-half 18640≤90640=内——not_instance_dominated 支命中"
            "（M4 条件）；instance_dominated 支（双条件均内）不命中=n=6 "
            "扩容未使逐实例离散收敛；G1=六 bottom 实例 courtyard 非弃权全 "
            "0 维持（三支字母口径恰一支命中）；G2 出局条目 R19=0→R22=2→"
            "R23=1→R24=0（观察项非字母支）。"),
            ("机制观察单列（不凌驾）：(a) 逐实例率分布——top 六实例双峰结构"
             "（1.0 vs 0.117647/0.133333；n=6 首次可看轮内分布形态）、bottom "
             "两极（0/0/1/1/1/1）、聚合 M1 落两峰之间=聚合值对实例抽样敏感"
             "的直接展示；(b) split-half 分解——0.018640≤0.09064（A=31/57 "
             "vs B=27/48）与 M4=0.888889 并存=聚合稳/个体散（抽样平均的稳"
             "定性不等于个体判读一致性、聚合稳定不构成判据收敛证据）；(c) "
             "G2 链闭合（0→2→1→0 清零=资格门满足=r24 入排序）+类别门 6 条"
             "逐轮新高；(d) 援引分记（三条款分开记、互不合并）：旗级 §5B=0/"
             "(iii-a)=7/分支(=0（7 旗逐旗摘录在案 run-r24）；notes 级 §5B="
             "0/24、(iii-a)=8/24（对照 r19 10/12、r22 6/12、r23 4/12）、"
             "§6=20/24（对照 r23 6/12）；(e) rubric 族计数 contact 4/"
             "existence_blackdot 28/existence_other 44（r13–r16 132 条重放"
             "对拍逐一相等后套用 r24，链值 8/15/5/10 在案）——黑点 28 与存"
             "在性其他 44 远高于三基线（n=6 扩容+实例异质性、跨轮对照=描述"
             "性）；(f) top 弃权构成分型=接触性 26+存在性 30+其他 2（58 条"
             "机械主出口分类逐旗入案；对照 r23 6/10/0、r22 2/14/0）；(g) "
             "reroute 被动追踪=6 旗（弃权 4+非弃权 2）、滥用型通道机械命中="
             "0。"),
            ("bottom 通道单列（M2=18/26=0.692308 vs r16 基线 12/14=0.857143 "
             "vs r19 4/7=0.571429 vs r20 4/14=0.285714 vs r22 2/10=0.2 vs "
             "r23 8/14=0.571429；较 r16 回落、高于 r19–r23；不影响字母）："
             "bottom 弃权旗 18 条（bottom-i3–i6 全弃权）；bottom 非弃权 8 条"
             "（bottom-i1/i2 各两板 4=黑色圆点/圆孔孤立或接触路径负责任报"
             "告）；bottom courtyard 类旗标=0（G1 维持的直接构成）。"),
            ("工具行为与派发操作（协议侧 v1.2 沿用+v1.3 n 扩容附录，如实入"
             "账）：R24 二十四派次全部以 Read 工具直读内嵌图像、24/24 派次"
             "reading_notes 自述「未读取盘上任何其他文件」（逐派次句子程序"
             "提取在案）；全部判读输入严格限于（指引+该 PNG），零 GT/零诊"
             "断/零 legend/零 r22/r23 现象描述注入=非盲读违规；flag_id 编号"
             "行为=12/12 有旗实例全部同实例跨板连续、24 格全部≥1 旗=零零旗"
             "格（与 prep-record naming 声明相符）；R24T/R24B 前缀=派发层覆"
             "盖（r16/r22 先例同型、前缀差异登记在案）；本轮无派发操作事故；"
             "跨实例/跨视角禁止交流（24 次盲读相互独立）。"),
            ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延"
             "续，零阈值改动零期望）：courtyard 类旗标 7 条（top 弃权 1"
             "[top-i4 prep1 R24T-021]+top 非弃权 6[top-i4 两板 2+top-i5 "
             "两板 4 贴近报告]；bottom 0）——非弃权 courtyard 命中链 "
             "r16=1→r17=0→r18=0→r19=0→r20=0→r22=0→r23=1→r24=0；reroute "
             "类 6 条（弃权 4+非弃权 2[负责任报告]；滥用型通道机械命中=0）；"
             "产量链 r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2"
             "→r17=1→r18=3→r19=3→r20=2→r22=4→r23=2→r24=6。"),
        ],
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本件=R24 收口包 B（dev-record 分包）：development 域第 24 轮迭代"
        "（实例群扩容归因轮）的轮次开发记录；迭代轮不得冒充留出证据。",
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
            "after_r12": dict(dev23["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r24 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r24 全旗标合计 76/131=0.580153 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R23 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 "
                         "与 seed_match_rate 0.0 两项未达暂行线；gt_count "
                         "13≥12 与 abstain_rate 0.45≤0.5 单分项入线）——"
                         "GT 条目层 union=agreement=1/13 亦未达 0.75（双口"
                         "径与门分列如实；r22/r24 agreement 里程碑在案）"),
            },
        },
        "kind": KIND,
        "mechanism_observation_r24": mechanism_observation_r24,
        "next_candidate_suggestion": next_candidate_suggestion,
        "next_iteration_targets": next_iteration_targets,
        "notes": notes,
        "preregistration_chain": chain,
        "preregistration_chain_note": (
            "预注册链（含哈希）：axis-experiment-plan-r17-r20.json"
            "（b6ec6467…，用户 2026-09-09「三条轴单独/组合/全组合尝试，选择"
            "收益最大的继续」指令操作化=冻结比较规则[comparison_rule]+组合"
            "决策规则+early_stop_rule，先于 R17–R21 任何实验轮盲读冻结；r21 "
            "全组合槽位=条件位未触发、永久留空）→round20-dev-record.json"
            "（80e3e9e2…，收束+next_iteration_targets[1] 同指引重复轮候选；"
            "G1 分岔记录在案）→round22-dev-record.json（b4b8fbe9…，r22 收束"
            "+drift 0.09064 参照在案=split-half 阈值参照源；g2_bifurcation_"
            "record 在案）→round23-dev-record.json（343a6747…，r23 收束+下"
            "一候选建议 (b) 对剩余混杂（判据内容/实例群/其他输出侧因素）做"
            "新预注册轮归因=本轮设计出处与合法性依据；g2_bifurcation_record "
            "延续在案）→r24-prep-record.json（760af49f…，本轮预注册件，"
            "measurement_design 五条[n=6 扩写]聚合口径与 hypothesis_test."
            "adjudication 归因三支判据（instance_dominated=G1 维持且 M4(n="
            "6)<0.261904 且 split_half≤0.09064/not_instance_dominated=G1 "
            "维持且（M4≥0.261904 或 split_half>0.09064）/guard_interrupted="
            "G1 破坏）先于盲读冻结；changed_variables 长度=1；no_instrument_"
            "change=true；v1.3 n 扩容附录在件）→判读指引=observation-"
            "guidance-r23.md（866b0157…，字节复用零改写[派发层前缀覆盖 "
            "R23T/R23B→R24T/R24B=r16/r22 先例]）→渲染零变更（renders-r14b "
            "四图字节复用、与 r14–r23 盲读同一批文件[applied-top 298bc620/"
            "applied-bottom d7284259/prep1-top b2f84524/prep1-bottom "
            "d7284259；witness-r14b b63771f9 在案]）→24 次盲读[12/12 有旗"
            "实例同实例跨板连续、24 格全部≥1 旗=零零旗格、无派发事故；24 件"
            "哈希全 64 位锚在案 run.rader.raw_files/本件 flag_production."
            "raw_files]→run-r24（8a9bdb7d…，本链执行落盘；run_r22="
            "80a12c05/run_r23=15f58350 在案=比较集行 live 复算输入）；GT 重"
            "投影沿用 derivation-log-r5.json（62343380…）零新派生（GT 全部 "
            "side=top；渲染零变更=GT 重投影输入未变）；GT 冻结纪律：轮后未"
            "增删改；gt-audit-r1（1f20554a…）结论维持 GT 零改动（三候选关"
            "闭，gt_audit_reference 在案）"),
        "protected_files_verification": {
            "hashes": dict(protected),
            "note": ("受保护文件全 64 位 sha256 实测断言（开工/收工各验一次"
                     "；零改动红线；fail-closed）"),
            "role": "红线 1 执行证据",
        },
        "reference_hash_manifest": reference_hash_manifest,
        "round_id": ROUND_ID,
        "round_identity_declaration": round_identity_declaration,
        "round_label": ROUND_LABEL,
        "round_nature": (
            "development 域实例群扩容归因轮（第二十四轮；多实例协议 v1.3："
            "每视图实例数 3→6）：唯一实验变量=实例数 n（12 个 reader 智能体、"
            "24 次盲读=4 视角格×6 实例、两波次串行；判读指引字节复用 "
            "observation-guidance-r23.md[866b0157 实测锚、零改写零派生；派发"
            "层前缀覆盖 R23T/R23B→R24T/R24B=r16/r22 先例]）+渲染零变更="
            "renders-r14b 四图字节复用（与 r14–r23 盲读同一批文件；"
            "no_instrument_change=true[run 侧 instrument_change.changed="
            "False=仪器未变、实例群=派发编排层变量]）+GT 集/协议阈值与度量"
            "版本/比较器常量零改动（GT 重投影沿用 derivation-log-r5——零新"
            "派生；gt-audit-r1 三候选关闭结论延续）；协议=v1/v1.1/v1.2 继承"
            "不改+v1.3 n 扩容附录（prep-record 内登记、不新建协议文件；"
            "union≥1/6、agreement≥4/6、代表配置=下中位序位实例的 n=6 推广="
            "附录显式冻结、不得事后收放）；changed_variables=1；实例群重抽+"
            "扩容=本轮实验操作本身（实例群抽样规模轴=r23 confounded 支剩余"
            "混杂三轴的第一轴）；【跳号声明延续】r21 号段=axis-experiment-"
            "plan-r17-r20（b6ec6467 冻结件）预留的 R21 全组合条件位（"
            "early_stop_rule.strong_single_axis_shortcut 未触发、槽位永久"
            "留空；dev-r20 已登记「R21 不做」；r22/r23 跳号声明在案；r24 与"
            "该位无涉）；执行 round23-dev-record 下一候选建议 (b)+用户 "
            "2026-09-10 拍板；检验假设 r23-confounded-residual-confound-"
            "instance-axis-attribution（判据=r24-prep-record.json "
            "hypothesis_test.adjudication 归因三支判据，轮后如实执行：字母"
            "裁决唯一正式+机制观察/度量教训单列+G2 分岔记录延续；主通道归因"
            "三支判据与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自"
            "独立计算、互不凌驾、分开表述；measurement_design 聚合口径先于"
            "盲读冻结）；跨轮收益比较按 axis-plan 冻结规则（r24 行见 axis_"
            "experiment_ledger 八行并列：r24 入排序居 r19 之后第二、r20/"
            "r22/r23 资格门剔除；guidance-r19 胜出记录维持 conditional/"
            "double-entry 现状）；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "r21_skip_declaration": r21_skip_declaration,
        "run_record_ref": {"path_rel": REL_RUN_R24, "sha256": run24_sha},
        "schema_version": SCHEMA_VERSION,
        "three_axis_experiment_closeout": three_axis_experiment_closeout,
    }


def main() -> None:
    verify_protected_files()  # 开工锚
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s87-cal-r24-devrecord] round24-dev-record: {status}")
    print(f"[s87-cal-r24-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch=(nid) not_instance_dominated_m4_exceeds（G1 维持"
          f"且 M4(n=6)=0.888889≥0.261904）")
    print(f"[s87-cal-r24-devrecord] 归因三支判据: (id) instance_dominated="
          f"双条件均内=不命中（M4 超出）；(nid) not_instance_dominated=至少"
          f"一条件超出（M4 888889≥261904、split-half 18640≤90640）=命中⇒ "
          f"not_instance_dominated（唯一正式裁决）；(gi) guard_interrupted "
          f"未命中；G1=六 bottom 实例 courtyard 非弃权全 0 维持")
    print(f"[s87-cal-r24-devrecord] 归因结论（单列）: 离散超出抽样尺度（逐"
          f"实例双峰结构 top-i1=1.0 vs top-i2/top-i6≈0.11–0.13）——下一归因"
          f"轴=判据内容（判据内容/其他输出侧）；split-half 稳（0.018640≤"
          f"0.09064）与极差爆拉（0.888889）并存=聚合稳/个体散的分解；r23 "
          f"字母=confounded、r22 字母=regressed 维持不改写")
    print(f"[s87-cal-r24-devrecord] 机制观察: 三族 rubric 计数 contact 4/"
          f"黑点 28/存在性其他 44（对照 r19 4/4/14、r22 2/4/12、r23 8/8/7"
          f"——黑点与存在性远高=n 扩容+实例异质性）；援引旗级 §5B=0/"
          f"(iii-a)=7/分支(=0、notes 级 §5B=0/24+(iii-a)=8/24+§6=20/24；"
          f"G2 链 0→2→1→0 清零=资格门满足（r24 入排序）；类别门 6 条逐轮"
          f"新高")
    print(f"[s87-cal-r24-devrecord] GT: union=agreement=1/13=0.076923（"
          f"GT-REVC-P1-L1SHORT 四实例一致命中[top-i2/i4/i5/i6，全部 prep1]"
          f"；agreement≥4/6=v1.1 ≥2/3 语义 n=6 推广首次计入）；通道门 几何 "
          f"0/类别 6/视角 0（对照 r19 0/2/0、r20 0/0/0、r22 2/4/1、r23 "
          f"1/1/0）")
    print(f"[s87-cal-r24-devrecord] 台账与排序: 八行并列（r16/r17/r18/r19/"
          f"r20/r22/r23/r24）；r24 入排序居 r19 之后第二（G1/G2 满足）；"
          f"排序=r19_axis3 第一、r24 第二、r18 第三、r16 参照、r17 末位；"
          f"显著收益 0.219048≥0.10 描述层命中（与 n=6 分母效应并读）")
    print(f"[s87-cal-r24-devrecord] 下一候选建议（三选项、由用户拍板）: "
          f"(a) 接受发展域现状收束训练环+留出集时机用户判断；(b) 判据内容轴"
          f"归因轮（下一归因轴=判据内容）；(c) 同指引重复轮第三样本或其他输"
          f"出侧因素操作化归因轮")
    print(f"[s87-cal-r24-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s87-cal-r24-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0 in_calibrated_range=恒 False")
    print(f"[s87-cal-r24-devrecord] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print(f"[s87-cal-r24-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    verify_protected_files()  # 收工锚
    print("[s87-cal-r24-devrecord] R24 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=not_instance_dominated 唯一正式（not_instance_"
          "dominated_m4_exceeds 支=G1 维持且 M4 条件超出）；逐实例双峰结构/"
          "split-half 分解/G2 链闭合/度量教训单列不凌驾；r22=regressed、"
          "r23=confounded 维持不改写；in_calibrated_range 恒 False）")


if __name__ == "__main__":
    main()
