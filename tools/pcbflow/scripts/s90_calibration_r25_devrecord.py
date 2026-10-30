#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s90_calibration_r25_devrecord.py — R25 CLOSE 包 B：
round25-dev-record.json 生成器（纯函数+防覆写，dev-record 分包纪律；
结构血统=s78/s83/s87 同构重建）。

R25=development 域判据内容轴归因轮（三混杂轴归因链第三轴执行轮：r23
框宽排除[confounded 在案]→r24 实例群排除[not_instance_dominated 在案]→
r25 判据内容[本轮]；本轮=第二十五轮；执行 round24-dev-record 下一候选
建议选项(b)（判据内容轴归因预注册轮——原文逐字在案）+用户 2026-09-10
拍板选项(b)定向判据内容轴；hypothesis_id=r24-not-instance-dominated-
criterion-boundary-operationalization-attribution）。唯一实验变量=判读
指引 §4 末尾弃权边界操作化条款（observation-guidance-r25.md=86af24dd
由 observation-guidance-r23.md 866b0157 机械变换派生落盘新件、byte
delta=+937；唯一语义变量=§4 末尾条款[§5 标题行之前插入、逐字冻结]；
随变更的机械变换同步项=轮次身份四处更新+变更声明节整体重写+§6 示例旗
ID 前缀机械替换 R23T-→R25T-（4 处）/R23B-→R25B-（1 处）/reader-r23-→
reader-r25-（1 处）=派发层命名与指引一致、无前缀差异登记需求——s70/
s80 机械变换派生先例同型；对照 r16/r22/r24 字节复用+派发层覆盖路径）+
渲染零变更=renders-r14b 四图字节复用+GT/阈值/协议正文零变更[v1/v1.1/
v1.2 继承不改+v1.3 n=6 附录沿用 r24、无新增附录；n=6 口径与 r24 完全
同构、实例群重抽=轮际固有混杂非实验操作；protocol-v2=holdout 冻结件
本轮不启用]）。
【跳号声明延续】r21 号段=axis-experiment-plan-r17-r20（b6ec6467 冻结件）
预留的 R21 全组合条件位——未触发、槽位永久留空（round20-dev-record
next_iteration_targets[0] 已登记「R21 不做」、r22 跳号声明在案
round22-dev-record=b4b8fbe9 r21_skip_declaration 冻结原文引用）；r25 为
r24 之后的时序下一轮、与该 R21 全组合位无涉。
预注册假设归因三支判据轮后裁决（按 r25-prep-record hypothesis_test.
adjudication 原文、脚本实测落支、不预写）=not_criterion_dominated（字母
口径，唯一正式裁决，轮后不改写）：G1 维持（六 bottom 实例 courtyard 非
弃权旗全=0）且 M4(n=6)=1.0≥0.261904（6 位定点 1000000≥261904；M4 阈值
=r16 基线历史口径在案值原样引用）——M4 条件超出→边界操作化未收敛个体
散=判据内容非主因（残余归因=其他输出侧/模型侧固有；归因链三轴[框宽/
实例群/判据内容]全部排除完毕、残余=其他输出侧/模型侧固有=如实登记、
不新造第四轴名称只描述）；split_half_M1_diff=0.260377（6 位定点 260377）
>0.09064（6 位定点 90640）=聚合亦移动、与 r24 的 0.018640 反转=机制观察
单列如实登记（条款改变了聚合行为；split_half 本轮不进分支判定=与 r24
双判据分支的差异如实登记）。机制观察单列：M1 降/M2 升分解（M1
0.552381→0.433735=降 0.118646、M2 0.692308→0.916667=升 0.224359；两向
均不进字母、APR-0011 门指标照常分列）、逐实例率分布（top-i5=1.0 高峰/
top-i6=0.142857 低谷跨越值域）、三族计数 contact 3/existence_blackdot
22/existence_other 20（r13–r16 132 条重放对拍逐一相等后套用）对照 r19
（4/4/14）与 r22（2/4/12）与 r23（8/8/7）与 r24（4/28/44）四基线、
援引计数（旗级 §5B=0/(iii-a)=11/分支(=0/弃权边界条款=16+三问=13；notes
级 §5B=0/24、(iii-a)=12/24、§6=9/24、弃权边界条款=24/24[三问 22/24]）
+条款行为观察（三问援引率 22/24、弃权理由候选解释列举率 58/58 弃权旗
逐旗列举=条款三问之(3) 直接行为观测）单列、G2 几何门 r19=0→r22=2→
r23=1→r24=0→r25=0 清零维持=资格门满足（r25 入排序）。零旗格=2 格
（applied/prep1-bottom-i1 合法零旗输出、弃权率=None 口径触发=不编造
数值；零旗格均在 bottom 侧、M4 top 12 格集合不含=逐格率口径不受影响
如实声明）。GT：union=1/13=0.076923（GT-REVC-AP-1-R5U6 由 applied-top-i4
R25T-005 单实例命中）、agreement=0/13（1/6<4/6 不计入；r22 首次
agreement 计入的 2/3 里程碑与 r24 的 4/6 首计入维持不改写）；通道归因：
几何门 0、类别门 1、视角门 0 对照 r19（0/2/0）与 r20（0/0/0）与 r22
（2/4/1）与 r23（1/1/0）与 r24（0/6/0）。联合门：joint not_met、连续=0、
in_calibrated_range 恒 False 照常。台账九行并列（r16 基线/r17 轴1/
r18 轴2/r19 轴3/r20/r22/r23/r24/r25；前八行=round24-dev-record 台账
在案行逐值继承+本轮 live 复算交叉核对）；排序=r25_this_round 第一
（M1=0.433735 全场最低、G1/G2 满足=入排序）、r19_axis3 第二、r24 第三、
r18/r16 参照/r17 末位；显著收益 0.337694≥0.10 描述层命中（r18
0.126268/r19 0.309891/r22 0.381185/r23 0.286581/r24 0.219048 亦命中）。
「正确测出无效同样是有效证据」三向记账：字母（三支判据按预注册原文执
行）、机制观察（五键落点+三族计数+援引计数+条款行为观察+G2 出局条目
[本轮=0 空摘录]+逐实例率分布+split-half 分解，单列不进字母）、度量
教训（M4 跨口径粒度差异=描述性声明[12 格 vs r16–r23 逐实例两板合计
口径]+split_half 分支使命完成+判据内容轴单变量操作化的验证力度声明
[部分重复≠独立重复；本轮唯一实验变量=判据内容条款、实例群重抽=轮际
固有混杂]，单列）——三账分列、不合并、不改写。R25 五键=(M1, M2, M3,
M4, split_half_M1_diff)=(0.433735, 0.916667, 22, 1.0, 0.260377)
（M1=top 全旗聚合弃权率 36/83、M2=bottom 22/24、M3=黑点族 rubric 口径
22、M4=12 个（态,实例）格弃权率极差 1.0−0.0）。
下一候选建议（如实单列、由用户拍板、本包不预写决策）三选项：(a) 接受
发展域现状收束训练环、留出集时机由用户判断（HOLDOUT-PLAN a4b80193
Tier 1/2 候选清单零接触在案）；(b) 其他输出侧因素操作化归因轮（残余
归因=其他输出侧/模型侧固有=归因链排除完毕后的唯一剩余方向；须新
prep-record 先于盲读冻结）；(c) 同指引重复轮（第三样本分离实例群漂移）
或收束训练环。

生成器纪律（s69/s72/s75/s78/s83/s87 血统）：
- 受保护文件锚（开工/收工各验一次）：pcbflow/cli.py/pcbflow/config.py/
  toolchain_lock.json 全 64 位 sha256 实测断言（fail-closed）；
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（逐件实测，fail-closed 交叉核对；
  24 份 reader-raw 全 64 位锚逐一实测）；
- 日期只用常量 DECLARED_DATE="2026-09-10"；
- 防覆写护栏：round25-dev-record.json 已存在且字节不同→FAIL；
  字节等同→幂等跳过零覆写；
- 本脚本只写 round25-dev-record.json 一件（s89 零 dev-record 写入
  的分包边界由本包闭合）。

用法：python scripts/s90_calibration_r25_devrecord.py   （仓库根执行）
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
ROUND_ID = "2026-09-10-r25"
ROUND_LABEL = "r25"
SCHEMA_VERSION = "3.0"
KIND = "tl2_calibration_round25_dev_record"
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

REL_RUN_R25 = "out/v3-tl2/calibration/calibration-run-r25.json"
REL_RUN_R24 = "out/v3-tl2/calibration/calibration-run-r24.json"
REL_RUN_R23 = "out/v3-tl2/calibration/calibration-run-r23.json"
REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_RUN_R16 = "out/v3-tl2/calibration/calibration-run-r16.json"
REL_RUN_R19 = "out/v3-tl2/calibration/calibration-run-r19.json"
REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_PREP_R25 = "out/v3-tl2/calibration/r25-prep-record.json"
REL_GUIDANCE_R25 = "out/v3-tl2/calibration/observation-guidance-r25.md"
REL_GUIDANCE_R23 = "out/v3-tl2/calibration/observation-guidance-r23.md"
REL_GUIDANCE_R19 = "out/v3-tl2/calibration/observation-guidance-r19.md"
REL_AXIS_PLAN = "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json"
REL_TYPOLOGY = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_DEV_R22 = "out/v3-tl2/calibration/round22-dev-record.json"
REL_DEV_R23 = "out/v3-tl2/calibration/round23-dev-record.json"
REL_DEV_R24 = "out/v3-tl2/calibration/round24-dev-record.json"
REL_OUT = "out/v3-tl2/calibration/round25-dev-record-v2.json"
#: v2 追加件（DEV-E0-004）：与 r1 冻结件差异恰=protected_files_
#: verification 的 cli.py 锚（6ed4f3fd→0a738047，铜环案接纳）；r1 零回写。

INSTANCE_ORDER = tuple(
    [f"top-i{i}" for i in range(1, 7)]
    + [f"bottom-i{i}" for i in range(1, 7)])

# 引用件哈希清单（简报在案锚；逐件 live 实测比对，fail-closed）
REFERENCE_HASH_EXPECTED = {
    "run_r25": (REL_RUN_R25, "251102e8"),
    "prep_r25": (REL_PREP_R25, "0943a8ec"),
    "guidance_r25": (REL_GUIDANCE_R25, "86af24dd"),
    "guidance_r23_base": (REL_GUIDANCE_R23, "866b0157"),
    "guidance_r19_base": (REL_GUIDANCE_R19, "8633bda5"),
    "run_r16": (REL_RUN_R16, "2c1f8265"),
    "run_r19": (REL_RUN_R19, "e5755a11"),
    "run_r20": (REL_RUN_R20, "6573a59a"),
    "run_r22": (REL_RUN_R22, "80a12c05"),
    "run_r23": (REL_RUN_R23, "15f58350"),
    "run_r24": (REL_RUN_R24, "8a9bdb7d"),
    "dev_r19": (REL_DEV_R19, "0e2fdd69"),
    "dev_r20": (REL_DEV_R20, "80e3e9e2"),
    "dev_r22": (REL_DEV_R22, "b4b8fbe9"),
    "dev_r23": (REL_DEV_R23, "343a6747"),
    "dev_r24": (REL_DEV_R24, "1a344edf"),
    "axis_plan": (REL_AXIS_PLAN, "b6ec6467"),
    "typology": (REL_TYPOLOGY, "6dadac8d"),
}

# 归因三支判据实测锚（写盘前 fail-closed 与 run-r25 盘上值逐一核对；
# 6 位定点整数比较，与 s89 M4_THRESHOLD_6DP/SPLIT_HALF_THRESHOLD_6DP
# 同锚；split_half 本轮=机制观察单列、不进分支判定）
M4_THRESHOLD_6DP = 261_904
SPLIT_HALF_THRESHOLD_6DP = 90_640
EXPECT_TOP_ABSTAIN_R25 = 36
EXPECT_TOP_FLAGS_R25 = 83
EXPECT_TOP_RATE_R25 = 0.433735
EXPECT_BOTTOM_ABSTAIN_R25 = 22
EXPECT_BOTTOM_FLAGS_R25 = 24
EXPECT_BOTTOM_RATE_R25 = 0.916667
EXPECT_TOP_R16_BASELINE_LIVE = "27/35"
EXPECT_TOP_R16_BASELINE_VALUE = 0.771429
EXPECT_BOTTOM_R16_BASELINE_LIVE = "12/14"
EXPECT_BOTTOM_R16_BASELINE_VALUE = 0.857143
EXPECT_CONTACT_R25 = 3
EXPECT_CONTACT_R16_BASELINE = 10
EXPECT_CONTACT_CHAIN_R13_R16 = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
# 实验对照账五键（axis-experiment-plan benefit_metrics 口径按 n=6 扩写；
# M3 槽位=冻结件黑点族 rubric 口径、本轮实测 22）
EXPECT_M1 = 0.433735
EXPECT_M2 = 0.916667
EXPECT_M3 = 22
EXPECT_M4 = 1.0
EXPECT_M4_6DP = 1_000_000
EXPECT_SPLIT_HALF = 0.260377
EXPECT_SPLIT_HALF_6DP = 260_377
EXPECT_SPLIT_HALVES = {"A_i1_i3": {"abstain": 18, "flags": 53,
                                   "rate_6dp": 339_623},
                       "B_i4_i6": {"abstain": 18, "flags": 30,
                                   "rate_6dp": 600_000}}
EXPECT_R16_BASELINE_M1_M2_M3_M4 = [0.771429, 0.857143, 12, 0.261904]
# r17/r18/r19/r20/r22/r23/r24 已测行（dev-r24/run 在案行装载；排序现状
# 对照）
EXPECT_R17_MEASURED = {"M1": 0.88, "M2": 0.75, "M3": 8, "M4": 0.333333}
EXPECT_R18_MEASURED = {"M1": 0.645161, "M2": 0.684211, "M3": 13,
                       "M4": 0.277778}
EXPECT_R19_MEASURED = {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                       "M4": 0.211111}
EXPECT_R20_MEASURED = {"M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25}
EXPECT_R22_MEASURED = {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
EXPECT_R23_MEASURED = {"M1": 0.484848, "M2": 0.571429, "M3": 8,
                       "M4": 0.520833}
EXPECT_R24_MEASURED = {"M1": 0.552381, "M2": 0.692308, "M3": 28,
                       "M4": 0.888889, "split_half_M1_diff": 0.01864}
EXPECT_R19_DROP_REFERENCE = 0.309891
EXPECT_R18_DROP_REFERENCE = 0.126268
EXPECT_R22_DROP_REFERENCE = 0.381185
EXPECT_R23_DROP_REFERENCE = 0.286581
EXPECT_R24_DROP_REFERENCE = 0.219048
EXPECT_R25_M1_ABSOLUTE_DROP = 0.337694
# 逐实例旗数/弃权记账（r25 实测；12 实例；bottom-i1=零旗格）
EXPECT_COUNTS = {"top-i1": 10, "top-i2": 15, "top-i3": 28, "top-i4": 17,
                 "top-i5": 6, "top-i6": 7, "bottom-i1": 0, "bottom-i2": 4,
                 "bottom-i3": 6, "bottom-i4": 4, "bottom-i5": 6,
                 "bottom-i6": 4}
EXPECT_ABSTAIN = {"top-i1": 3, "top-i2": 7, "top-i3": 8, "top-i4": 11,
                  "top-i5": 6, "top-i6": 1, "bottom-i1": 0, "bottom-i2": 4,
                  "bottom-i3": 4, "bottom-i4": 4, "bottom-i5": 6,
                  "bottom-i6": 4}
EXPECT_TOP_INSTANCE_RATES = {"top-i1": 0.3, "top-i2": 0.466667,
                             "top-i3": 0.285714, "top-i4": 0.647059,
                             "top-i5": 1.0, "top-i6": 0.142857}
# 三支判据布尔（not_criterion_dominated 命中=M4 条件超出）
EXPECT_TYPE_COUNTS = {"contact": 5, "existence": 20, "other_layer": 11}
EXPECT_BLACK_DOT_BY_INSTANCE = {"top-i1": 0, "top-i2": 0, "top-i3": 4,
                                "top-i4": 2, "top-i5": 0, "top-i6": 0,
                                "bottom-i1": 0, "bottom-i2": 4,
                                "bottom-i3": 2, "bottom-i4": 4,
                                "bottom-i5": 6, "bottom-i6": 0}
EXPECT_RUBRIC_COUNTS = {"contact": 3, "existence_blackdot": 22,
                        "existence_other": 20, "other": 13,
                        "semantic_confusion": 0}
# 援引期望（与 run-r25 实测逐一相等，fail-closed；多计数分开记）
EXPECT_FLAG_IIIA = 11
EXPECT_NOTES_IIIA_SOURCES = sorted([
    "applied-bottom-i1", "applied-bottom-i4", "applied-top-i1",
    "applied-top-i3", "applied-top-i4", "applied-top-i6",
    "prep1-bottom-i1", "prep1-bottom-i4", "prep1-top-i1",
    "prep1-top-i3", "prep1-top-i4", "prep1-top-i6",
])
EXPECT_NOTES_S6_COUNT = 9
EXPECT_NOTES_CLAUSE_COUNT = 24
EXPECT_NOTES_SANWEN_COUNT = 22
EXPECT_FLAG_CLAUSE = 16
EXPECT_FLAG_SANWEN = 13
EXPECT_ABSTAIN_FLAGS_TOTAL = 58
EXPECT_ABSTAIN_FLAGS_WITH_CAND_EXPLAIN = 58
# 守门（G1 六实例全 0 维持；G2 r19=0→r22=2→r23=1→r24=0→r25=0 清零维持=
# 资格门满足）
EXPECT_G1_R25 = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0,
                 "bottom-i4": 0, "bottom-i5": 0, "bottom-i6": 0}
EXPECT_G1_BASELINE = {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_G1_R20_BROKEN = {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
EXPECT_GATES_R25 = {"geometry": 0, "category": 1, "view": 0}
EXPECT_GATES_R19 = {"geometry": 0, "category": 2, "view": 0}
EXPECT_GATES_R20 = {"geometry": 0, "category": 0, "view": 0}
EXPECT_GATES_R22 = {"geometry": 2, "category": 4, "view": 1}
EXPECT_GATES_R23 = {"geometry": 1, "category": 1, "view": 0}
EXPECT_GATES_R24 = {"geometry": 0, "category": 6, "view": 0}
# GT 命中明细（union=1/13、agreement=0；R5U6 单实例命中）
EXPECT_GT_GT_IDS = ["GT-REVC-AP-1-R5U6"]
EXPECT_GT_HIT_FLAGS = {("R25T-005", "top-i4", "applied")}
# 代表配置（下中位序位=top-i1+bottom-i4；bottom tie=编号先序）
EXPECT_REPRESENTATIVE = {"top": "top-i1", "bottom": "bottom-i4"}
# 零旗格（applied/prep1-bottom-i1 两格=合法零旗输出）
EXPECT_ZERO_FLAG_PARTS = [("bottom-i1", "applied"), ("bottom-i1", "prep1")]
# 24 份 reader-raw 全 64 位锚（与 run-r25 reader.raw_files 逐一实测核对）
READER_RAW_PREFIXES = {
    "applied-top-i1": "c1bd92ab", "prep1-top-i1": "676dfa3f",
    "applied-top-i2": "a02a18ab", "prep1-top-i2": "a23784a4",
    "applied-top-i3": "e35dd70e", "prep1-top-i3": "ffc837c2",
    "applied-top-i4": "8ccf8c21", "prep1-top-i4": "951b3dd3",
    "applied-top-i5": "269fd091", "prep1-top-i5": "256824af",
    "applied-top-i6": "a53c39d0", "prep1-top-i6": "8c461096",
    "applied-bottom-i1": "efed3330", "prep1-bottom-i1": "f1a8e7dc",
    "applied-bottom-i2": "02b146f5", "prep1-bottom-i2": "3fe0dbdf",
    "applied-bottom-i3": "87f7e546", "prep1-bottom-i3": "fdbed646",
    "applied-bottom-i4": "1e81bc51", "prep1-bottom-i4": "dde0217d",
    "applied-bottom-i5": "e0da53f5", "prep1-bottom-i5": "74266233",
    "applied-bottom-i6": "15547e7a", "prep1-bottom-i6": "ea46c389",
}


def _fail(msg: str) -> None:
    raise SystemExit(f"[s90-cal-r25-devrecord] FAIL: {msg}")


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

def attribution_verdict_fixed_point(m4_6dp: int, g1_ok: bool) -> tuple:
    """主通道归因三支判据（纯函数；与 s89.adjudicate_attribution 同判据
    同锚——判据原文=r25-prep-record hypothesis_test.adjudication；全部
    6 位定点整数比较、字母裁决无浮点路径；M4 单判据、split_half=机制
    观察单列不进分支[与 r24 双判据分支的差异如实登记]）。

    (cd)  criterion_dominated=G1 维持且 M4(n=6)<261904→弃权边界显式化
          收敛个体散=判据内容为个体散主因；
    (ncd) not_criterion_dominated=G1 维持且 M4(n=6)≥261904→边界操作化
          未收敛个体散=判据内容非主因（残余归因=其他输出侧/模型侧
          固有）；
    (gi)  guard_interrupted=G1 破坏（任一 bottom 实例 courtyard 非弃权
          旗>0）→归因悬置、机制观察照常（支序最高）。
    返回 (verdict, branch_key)；本函数与 run-r25 盘上裁决互为交叉核对。
    """
    if not g1_ok:
        return ("guard_interrupted", "guard_interrupted_g1")
    if m4_6dp < M4_THRESHOLD_6DP:
        return ("criterion_dominated", "criterion_dominated_m4_within")
    return ("not_criterion_dominated", "not_criterion_dominated_m4_exceeds")


def _view_abstain_aggregate(run: dict, view: str):
    names = sorted(n for n in run["instances"] if n.startswith(view))
    flags = sum(run["instances"][n]["combined"]["flag_count"] for n in names)
    abstain = sum(run["instances"][n]["combined"]["abstain_count"]
                  for n in names)
    return flags, abstain


def _verify_facts(run: dict, run16: dict, run19: dict, run20: dict,
                  run22: dict, run23: dict, run24: dict, prep: dict,
                  dev19: dict, dev20: dict, dev22: dict, dev23: dict,
                  dev24: dict, typology: dict,
                  guidance25_sha: str, guidance23_sha: str, axis_sha: str,
                  typology_sha: str, run25_sha: str, raw_files: dict) -> None:
    # ---- 受保护文件（开工锚；全 64 位） ----
    verify_protected_files()
    # ---- run-r25 常量与裁决 ----
    if run["kind"] != "tl2_calibration_run_r25":
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
            "r24-not-instance-dominated-criterion-boundary-" \
            "operationalization-attribution":
        _fail("hypothesis_id 不符")
    if ht["verdict"] != "not_criterion_dominated":
        _fail("verdict != not_criterion_dominated")
    if "唯一正式裁决" not in ht["verdict_text"]:
        _fail("verdict_text 应含「唯一正式裁决」")
    m = ht["measurement"]
    if (m["crit_not_criterion_dominated"] is not True
            or m["crit_guard_interrupted"] is not False
            or m["crit_criterion_dominated"] is not False):
        _fail("归因三支判据布尔不符（not_criterion_dominated=True；"
              "guard_interrupted=False；criterion_dominated=False）")
    if not m["letter_branch"].startswith("(ncd)"):
        _fail("落支应为 (ncd) 支")
    if "0.261904" not in m["letter_branch"] or \
            "判据内容非主因" not in m["letter_branch"]:
        _fail("落支文本应含 M4 条件超出+判据内容非主因")
    if m["verdict"] != "not_criterion_dominated":
        _fail("measurement.verdict != not_criterion_dominated")
    # 归因三支纯函数交叉核对（实际输入=M4=1000000 超出、G1 维持→
    # not_criterion_dominated_m4_exceeds；构造反事实：M4 内→
    # criterion_dominated、G1 破坏→guard_interrupted=三态可复算）
    if attribution_verdict_fixed_point(1_000_000, True) != \
            ("not_criterion_dominated",
             "not_criterion_dominated_m4_exceeds"):
        _fail("归因纯函数实际输入复算不符（M4 超出→ncd_m4）")
    if attribution_verdict_fixed_point(261_903, True) != \
            ("criterion_dominated", "criterion_dominated_m4_within"):
        _fail("归因纯函数反事实复算不符（M4 内→criterion_dominated）")
    if attribution_verdict_fixed_point(261_904, True) != \
            ("not_criterion_dominated",
             "not_criterion_dominated_m4_exceeds"):
        _fail("归因纯函数边界复算不符（M4 恰=261904=超出）")
    if attribution_verdict_fixed_point(0, True) != \
            ("criterion_dominated", "criterion_dominated_m4_within"):
        _fail("归因纯函数端点复算不符（M4=0=内）")
    if attribution_verdict_fixed_point(1_000_000, False) != \
            ("guard_interrupted", "guard_interrupted_g1"):
        _fail("归因纯函数反事实复算不符（G1 破坏→guard_interrupted）")
    # 本轮实测（top 36/83、bottom 22/24）
    ft, at = _view_abstain_aggregate(run, "top")
    fb, ab = _view_abstain_aggregate(run, "bottom")
    if (ft, at) != (EXPECT_TOP_FLAGS_R25, EXPECT_TOP_ABSTAIN_R25):
        _fail("top 聚合不符（83/36）")
    if (fb, ab) != (EXPECT_BOTTOM_FLAGS_R25, EXPECT_BOTTOM_ABSTAIN_R25):
        _fail("bottom 聚合不符（24/22）")
    if m["top_abstain_rate_r25"] != EXPECT_TOP_RATE_R25 or \
            m["r25_m_tuple_6dp"]["M1"] != EXPECT_TOP_RATE_R25:
        _fail("M1 不符（36/83=0.433735）")
    if m["r25_m_tuple_6dp"] != {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4,
                                "split_half_M1_diff": EXPECT_SPLIT_HALF}:
        _fail("M 五键不符（0.433735/0.916667/22/1.0/0.260377）")
    if "36/83" not in m["top_abstain_rate_r25_arithmetic"]:
        _fail("M1 算式文本不符")
    if m["m4_top_rate_range_r25"] != EXPECT_M4:
        _fail("M4(n=6) 不符（1.0）")
    if m["split_half_M1_diff_r25"] != EXPECT_SPLIT_HALF \
            or round(m["split_half_M1_diff_r25"] * 1000000) != \
            EXPECT_SPLIT_HALF_6DP:
        _fail("split_half 不符（0.260377）")
    # 单判据定点整数复核（避免浮点）：1000000≥261904=超出；
    # split-half 260377>90640=聚合亦移动（机制观察单列）
    if not (EXPECT_M4_6DP >= M4_THRESHOLD_6DP):
        _fail("(ncd) M4 条件超出复核不符（1000000≥261904）")
    if not (EXPECT_SPLIT_HALF_6DP > SPLIT_HALF_THRESHOLD_6DP):
        _fail("split-half 聚合移动复核不符（260377>90640）")
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
    # r19/r20/r22/r23/r24 对照行=各自 run live 复算+登记交叉核对
    for doc, want, top_pair, bot_pair in (
            (run19, EXPECT_R19_MEASURED, (39, 18), (7, 4)),
            (run20, EXPECT_R20_MEASURED, (22, 14), (14, 4)),
            (run22, EXPECT_R22_MEASURED, (41, 16), (10, 2)),
            (run23, EXPECT_R23_MEASURED, (33, 16), (14, 8)),
            (run24, EXPECT_R24_MEASURED, (105, 58), (26, 18))):
        f_x, a_x = _view_abstain_aggregate(doc, "top")
        fb_x, ab_x = _view_abstain_aggregate(doc, "bottom")
        if (f_x, a_x) != top_pair or (fb_x, ab_x) != bot_pair:
            _fail(f"{want} live 复算不符（{top_pair}、{bot_pair}）")
    rows_live = ht["measurement"]["comparison_rows_live"]
    if rows_live["r19_axis3"] != EXPECT_R19_MEASURED \
            or rows_live["r22_repeat_live"] != EXPECT_R22_MEASURED \
            or rows_live["r23_repeat_live"] != EXPECT_R23_MEASURED \
            or rows_live["r24_expansion_live"] != {
                "M1": EXPECT_R24_MEASURED["M1"],
                "M2": EXPECT_R24_MEASURED["M2"],
                "M3": EXPECT_R24_MEASURED["M3"],
                "M4": EXPECT_R24_MEASURED["M4"]} \
            or rows_live["r16_baseline"] != {
                "M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}:
        _fail("比较集 live 复算装载不符")
    # contact 族（另列主度量对照）：实测 3、基线 10、链重放 8/15/5/10
    if m["contact_family_abstain_flags_rubric_r25"] != EXPECT_CONTACT_R25 \
            or m["contact_r16_baseline_registered"] != \
            EXPECT_CONTACT_R16_BASELINE or \
            m["contact_r16_baseline_live_replay"] != \
            EXPECT_CONTACT_CHAIN_R13_R16:
        _fail("contact 实测/基线/链重放不符（3、10、8/15/5/10）")
    # 逐实例旗数/弃权率与 r25 对照（本轮 2 格零旗格=bottom-i1 两板）
    counts = {n: run["instances"][n]["combined"]["flag_count"]
              for n in INSTANCE_ORDER}
    abstains = {n: run["instances"][n]["combined"]["abstain_count"]
                for n in INSTANCE_ORDER}
    if counts != EXPECT_COUNTS or abstains != EXPECT_ABSTAIN:
        _fail("逐实例旗数/弃权率不符")
    rates = {n: run["instances"][n]["combined"]["abstain_rate"]
             for n in INSTANCE_ORDER if n.startswith("top")}
    if rates != EXPECT_TOP_INSTANCE_RATES:
        _fail("top 逐实例弃权率不符（实测锚）")
    if run["instances"]["bottom-i1"]["combined"]["abstain_rate"] is not None:
        _fail("bottom-i1 零旗格弃权率应为 None（cal._ratio 先例）")
    # 零旗标格=2（applied/prep1-bottom-i1；item 5 None 口径触发）
    if [(z["instance"], z["state"])
            for z in run["reader"]["zero_flag_parts"]["parts"]] != \
            EXPECT_ZERO_FLAG_PARTS:
        _fail("零旗标格与实测不符（应为 bottom-i1 两板）")
    # 代表配置与门（top-i1+bottom-i4；下中位序位、bottom tie=编号先序）
    agg = run["aggregation_representative"]
    if (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) != (14, 7, 0.5, 0.0, 0.0):
        _fail("代表配置聚合不符")
    if run["compliance_representative"]["joint_evaluation"] != "not_met" or \
            run["compliance_representative"]["consecutive_rounds"][
                "consecutive_met_count"] != 0 or \
            run["compliance_representative"][
                "critic_calibration_in_range"] is not False:
        _fail("联合门/连续计数/in_calibrated_range 不符")
    if run["representative_configuration"]["members"] != \
            EXPECT_REPRESENTATIVE:
        _fail("代表配置成员不符（top-i1+bottom-i4）")
    if run["representative_configuration"]["selection"]["top"][
            "tie"] is not False or \
            run["representative_configuration"]["selection"]["bottom"][
                "tie"] is not True:
        _fail("代表配置 tie 语义不符（top 第 3 序位唯一、bottom tie 按"
              "实例编号先序）")
    # 守门通道（G1 六实例全 0 维持；G2 0→2→1→0→0 清零维持=资格门满足）
    gc = m["guard_channel"]
    if gc["g1_ok"] is not True or gc["g2_guard_ok"] is not True or \
            gc["guards_ok"] is not True or \
            gc["g2_geometry_gate_r19"] != 0 or \
            gc["g2_geometry_gate_r22"] != 2 or \
            gc["g2_geometry_gate_r23"] != 1 or \
            gc["g2_geometry_gate_r24"] != 0 or \
            gc["g2_geometry_gate_r25"] != 0:
        _fail("守门通道不符（G1 维持、G2 0→2→1→0→0 清零维持）")
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    if g12["g1_bottom_courtyard_non_abstain_r25"] != EXPECT_G1_R25 or \
            g12["g1_r16_baseline_live"] != EXPECT_G1_BASELINE or \
            g12["g1_r20_broken_registered"] != EXPECT_G1_R20_BROKEN:
        _fail("守门 G1 实测不符（六实例全 0 维持；基线/r20 对照）")
    # GT 双口径：union=1/13、agreement=0（R5U6 单实例命中）
    dual = run["gt_match_dual"]
    if (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) != (1, 0, 13):
        _fail("双口径不符（union=1/13、agreement=0/13）")
    if dual["union"]["gt_ids"] != EXPECT_GT_GT_IDS or \
            dual["agreement"]["gt_ids"] != [] or \
            dual["union"]["gt_recall_union"] != 0.076923 or \
            dual["agreement"]["gt_recall_agreement"] != 0.0:
        _fail("GT 命中登记不符（R5U6、union 1/13=0.076923）")
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    if len(hits) != 1 or hits[0]["matched_by_count"] != 1:
        _fail("GT 命中明细不符（R5U6 1/6 实例命中）")
    if {(h["flag_id"], h["instance"], h["state"])
            for h in hits[0]["hits"]} != EXPECT_GT_HIT_FLAGS:
        _fail("GT 命中旗明细不符（R25T-005@top-i4/applied）")
    # 通道门计数（几何/类别/视角；r25 vs r19 vs r20 vs r22 vs r23 vs r24）
    ca = run["channel_attribution"]
    n_geom_r25 = len(ca["channel_1_geometry_gate"][
        "r25_area_ratio_rejected_entries"])
    n_cat_r25 = len(ca["channel_2_category_gate"][
        "r25_category_mismatch_entries"])
    n_view_r25 = len(ca["view_gate_observations"]["r25_entries"])
    n_geom_r24 = ca["gate_chain_since_r6"][
        "geometry_gate_area_ratio_rejected_by_round"]["r24"]
    n_cat_r19 = len(ca["channel_2_category_gate"][
        "r19_category_mismatch_entries"])
    n_cat_r20 = len(ca["channel_2_category_gate"][
        "r20_category_mismatch_entries"])
    n_cat_r22 = len(ca["channel_2_category_gate"][
        "r22_category_mismatch_entries"])
    n_cat_r24 = len(ca["channel_2_category_gate"][
        "r24_category_mismatch_entries"])
    if (n_geom_r25, n_cat_r25, n_view_r25) != \
            (EXPECT_GATES_R25["geometry"], EXPECT_GATES_R25["category"],
             EXPECT_GATES_R25["view"]):
        _fail("r25 通道门计数不符（0/1/0）")
    if (n_geom_r19 := ca["gate_chain_since_r6"][
            "geometry_gate_area_ratio_rejected_by_round"]["r19"]) != \
            EXPECT_GATES_R19["geometry"]:
        _fail("r19 几何门计数不符")
    if (n_cat_r19, n_cat_r20, n_cat_r22, n_cat_r24) != \
            (EXPECT_GATES_R19["category"], EXPECT_GATES_R20["category"],
             EXPECT_GATES_R22["category"], EXPECT_GATES_R24["category"]) \
            or n_geom_r24 != EXPECT_GATES_R24["geometry"] or n_geom_r25 != \
            ca["gate_chain_since_r6"][
                "geometry_gate_area_ratio_rejected_by_round"]["r25"]:
        _fail("r19/r20/r22/r24/r25 通道门计数不符")
    # 机制观察：援引分记、黑点族、top 分型、rubric 族、split-half 分解
    mo = ht["mechanism_observation"]
    cc = mo["criterion_citation_observation"]
    ccounts = cc["citation_counts"]
    if ccounts["flag_level_s5b_literal"] != 0 or \
            ccounts["flag_level_iiia_literal"] != EXPECT_FLAG_IIIA or \
            ccounts["flag_level_branch_literal"] != 0 or \
            ccounts["flag_level_clause_literal"] != EXPECT_FLAG_CLAUSE or \
            ccounts["flag_level_sanwen_literal"] != EXPECT_FLAG_SANWEN:
        _fail("旗级援引不符（§5B=0、(iii-a)=11、分支(=0、条款=16、三问=13）")
    if ccounts["notes_level_s5b"] != 0 or \
            ccounts["notes_level_iiia"] != 12 or \
            ccounts["notes_level_s6_clause"] != EXPECT_NOTES_S6_COUNT or \
            ccounts["notes_level_clause"] != EXPECT_NOTES_CLAUSE_COUNT or \
            ccounts["notes_level_sanwen"] != EXPECT_NOTES_SANWEN_COUNT:
        _fail("notes 级援引不符（§5B=0/24、(iii-a)=12/24、§6=9/24、"
              "条款=24/24、三问=22/24）")
    if ccounts["notes_level_iiia_sources"] != EXPECT_NOTES_IIIA_SOURCES:
        _fail("notes 级援引来源清单不符（多计数分开记）")
    if ccounts["abstain_flags_with_cand_explain"] != \
            EXPECT_ABSTAIN_FLAGS_WITH_CAND_EXPLAIN or \
            ccounts["abstain_flags_total"] != EXPECT_ABSTAIN_FLAGS_TOTAL:
        _fail("弃权理由候选解释列举率不符（58/58）")
    bdt = mo["black_dot_tracking"]
    if bdt["all_abstain"] is not True or \
            bdt["by_instance"] != EXPECT_BLACK_DOT_BY_INSTANCE or \
            len(bdt["black_dot_flags"]) != 22:
        _fail("黑点族弃权 22 旗全弃权不符")
    if bdt["blackdot_to_non_abstain_count"] != 4:
        _fail("黑点转非弃权旗计数不符（4 条）")
    rf = bdt["rubric_families"]
    if rf["counts"] != EXPECT_RUBRIC_COUNTS:
        _fail("rubric 族计数不符（3/22/20/0/13）")
    if rf["replay_proof"]["per_flag_total"] != 132:
        _fail("rubric 重放对拍不符（132 条）")
    ty = mo["abstain_typology"]
    if ty["type_counts"] != EXPECT_TYPE_COUNTS or \
            len(ty["typology_rows"]) != 36:
        _fail("top 弃权构成分型不符（接触性 5+存在性 20+其他 11；36 条）")
    sh = mo["split_half_decomposition"]
    if sh["split_half_6dp"] != EXPECT_SPLIT_HALF_6DP or \
            sh["half_A"] != EXPECT_SPLIT_HALVES["A_i1_i3"] or \
            sh["half_B"] != EXPECT_SPLIT_HALVES["B_i4_i6"]:
        _fail("split-half 分解不符（339623/600000、260377）")
    # 实验对照账：九行并列/排序（r25 入排序居首）/归因结论位
    ecl = mo["experiment_comparison_ledger"]
    if ecl["r25_measured"]["M1"] != EXPECT_M1 or \
            ecl["r25_measured"]["M2"] != EXPECT_M2 or \
            ecl["r25_measured"]["M3"] != EXPECT_M3 or \
            ecl["r25_measured"]["M4"] != EXPECT_M4 or \
            ecl["r25_measured"]["M1_arithmetic"] != "36/83" or \
            ecl["r25_measured"]["M2_arithmetic"] != "22/24" or \
            ecl["r25_measured"]["split_half_M1_diff"] != \
            EXPECT_SPLIT_HALF or \
            ecl["r25_measured"]["contact_family_abstain_flags_rubric"] != \
            3 or ecl["r25_measured"]["existence_other_family"] != 20:
        _fail("实验对照账五键/另列键不符")
    if ecl["r17_axis1_row"] != EXPECT_R17_MEASURED or \
            ecl["r18_axis2_row"] != EXPECT_R18_MEASURED or \
            ecl["r19_axis3_row"] != EXPECT_R19_MEASURED or \
            ecl["r20_combo_registered_row"] != EXPECT_R20_MEASURED or \
            ecl["r22_repeat_registered_row"] != EXPECT_R22_MEASURED or \
            ecl["r23_repeat_registered_row"] != EXPECT_R23_MEASURED or \
            ecl["r24_expansion_registered_row"] != {
                "M1": EXPECT_R24_MEASURED["M1"],
                "M2": EXPECT_R24_MEASURED["M2"],
                "M3": EXPECT_R24_MEASURED["M3"],
                "M4": EXPECT_R24_MEASURED["M4"]}:
        _fail("r17–r24 对照行不符")
    if ecl["r16_baseline_registered"]["M1"] != 0.771429 or \
            ecl["r16_baseline_registered"]["M4"] != 0.261904:
        _fail("r16 基线行不符")
    # 台账前八行=round24-dev-record 台账在案行逐值继承（live 交叉核对）
    rows24 = dev24["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    if {k: rows24["r16_baseline"][k]
         for k in ("M1", "M2", "M3", "M4")} != \
            {k: ecl["r16_baseline_registered"][k]
             for k in ("M1", "M2", "M3", "M4")}:
        _fail("台账 r16 行与 dev-r24 继承不符")
    if rows24["r17_axis1"] != ecl["r17_axis1_row"] \
            or rows24["r18_axis2"] != ecl["r18_axis2_row"] \
            or rows24["r19_axis3"] != ecl["r19_axis3_row"] \
            or {k: rows24["r20_combo"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r20_combo_registered_row"] \
            or {k: rows24["r22_repeat"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r22_repeat_registered_row"] \
            or {k: rows24["r23_repeat"][k]
                for k in ("M1", "M2", "M3", "M4")} != \
            ecl["r23_repeat_registered_row"] \
            or rows24["r24_expansion"] != \
            {"M1": EXPECT_R24_MEASURED["M1"], "M2": EXPECT_R24_MEASURED["M2"],
             "M3": EXPECT_R24_MEASURED["M3"], "M4": EXPECT_R24_MEASURED["M4"],
             "split_half_M1_diff": EXPECT_R24_MEASURED[
                 "split_half_M1_diff"]}:
        _fail("台账 r17–r24 行与 dev-r24 在案行继承不符")
    rk = ecl["ranking_by_comparison_rule"]
    if rk["ranking_order_best_first"] != ["r25_this_round", "r19_axis3",
                                          "r24_expansion", "r18_axis2",
                                          "r16_baseline", "r17_axis1"] or \
            rk["r25_eligibility"] is not True or \
            rk["r24_eligibility"] is not True or \
            rk["r20_eligibility"] is not False or \
            rk["r22_eligibility"] is not False or \
            rk["r23_eligibility"] is not False:
        _fail("comparison_rule 排序不符（r25 第一、r24 在案入排序；"
              "r20/r22/r23 资格门剔除）")
    att = ecl["attribution_conclusion"]["conclusion"]
    if "not_criterion_dominated" not in att or "0.261904" not in att or \
            "残余归因" not in att:
        _fail("归因结论位不符（not_criterion_dominated/0.261904/残余归因）")
    sb = ecl["significant_benefit_vs_r16"]
    if sb["met"] is not True or \
            sb["r25_m1_absolute_drop"] != EXPECT_R25_M1_ABSOLUTE_DROP or \
            sb["r19_drop_reference"] != EXPECT_R19_DROP_REFERENCE or \
            sb["r18_drop_reference"] != EXPECT_R18_DROP_REFERENCE or \
            sb["r22_drop_reference"] != EXPECT_R22_DROP_REFERENCE or \
            sb["r23_drop_reference"] != EXPECT_R23_DROP_REFERENCE or \
            sb["r24_drop_reference"] != EXPECT_R24_DROP_REFERENCE:
        _fail("显著收益不符（0.337694≥0.10；r19 参照 0.309891）")
    shift = ecl["m1_m2_shift_observation"]
    if "m1" not in shift or "0.118646" not in shift["m1"] or \
            "0.224359" not in shift["m2"]:
        _fail("M1 降/M2 升分解单列不符（降 0.118646/升 0.224359）")
    # 判据引用=prep-record 原文（逐字一致，共键比对）
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("criterion_dominated", "not_criterion_dominated",
              "guard_interrupted", "letter_branch_map",
              "fixed_point_comparison_note", "g2_observation_separate",
              "m1_m2_gate_separate", "descriptive_boundary_note",
              "mechanism_observation_separate", "metric_lesson_separate",
              "three_way_bookkeeping"):
        if q[k] != adj[k]:
            _fail(f"预注册判据摘录与 prep-record 不一致: {k}")
    if prep["hypothesis_test"]["hypothesis_id"] != ht["hypothesis_id"]:
        _fail("prep-record hypothesis_id 不一致")
    # 指引机械派生锚（mechanical_transform_derive；条款在件断言）
    gr = prep["guidance_reuse"]
    if gr["mode"] != "mechanical_transform_derive" or \
            gr["base"] != "observation-guidance-r23.md" or \
            gr["derived"] != "observation-guidance-r25.md":
        _fail("guidance_reuse 机械派生声明不符")
    if gr["base_sha256"] != guidance23_sha or guidance23_sha != \
            _sha(REL_GUIDANCE_R23):
        _fail("r23 指引实测 sha 与 866b0157 锚不符")
    if gr["derived_sha256"] != guidance25_sha or guidance25_sha != \
            _sha(REL_GUIDANCE_R25):
        _fail("r25 指引实测 sha 与 86af24dd 锚不符")
    if gr["byte_size"] != {"base": 23125, "delta": 937, "derived": 24062}:
        _fail("指引字节账不符（23125+937=24062）")
    clause_text = gr["edit_list"][5]["text_full"]
    g25_text = open(_rel(REL_GUIDANCE_R25), encoding="utf-8").read()
    if not clause_text or clause_text not in g25_text:
        _fail("§4(终) 条款全文未逐字见于 r25 指引（在件断言失败）")
    if "三问" not in g25_text or "把握不足本身不构成弃权理由" not in g25_text:
        _fail("r25 指引缺条款 needle（在件断言失败）")
    if len(prep["changed_variables"]) != 1 or \
            prep["no_instrument_change"] is not True:
        _fail("changed_variables=1/条款单变量、no_instrument_change 不符")
    if "guidance-s4-abstain-boundary-operationalization-clause" \
            not in json.dumps(prep["changed_variables"], ensure_ascii=False):
        _fail("changed_variables 应为 §4 末尾弃权边界操作化条款单变量")
    # 预注册引用：run→prep 实测一致；轴计划冻结锚实测一致
    if ht["preregistration_ref"]["sha256"] != _sha(REL_PREP_R25):
        _fail("prep-record sha 实测与登记不符")
    if axis_sha != _sha(REL_AXIS_PLAN):
        _fail("axis-plan 实测 sha 与冻结锚不符")
    # 执行授权链（dev24 下一候选建议选项(b)+用户 2026-09-10 拍板；r24 字母
    # =not_instance_dominated、r23 字母=confounded、r22 字母=regressed 维持
    # 不改写）
    cand = dev24["next_candidate_suggestion"]["options"][1]
    if "判据内容轴" not in cand["option"] or "预注册" not in cand["option"]:
        _fail("dev-r24 选项 (b) 判据内容轴授权原文不符")
    if dev24["round_id"] != "2026-09-10-r24" or \
            dev24["hypothesis_test_i"]["verdict"] != "not_instance_dominated":
        _fail("dev-r24 先验件常量不符")
    if dev23["round_id"] != "2026-09-10-r23" or \
            dev23["hypothesis_test_i"]["verdict"] != "confounded":
        _fail("dev-r23 先验件常量不符")
    if dev22["round_id"] != "2026-09-09-r22" or \
            dev22["hypothesis_test_i"]["verdict"] != "regressed":
        _fail("dev-r22 先验件常量不符")
    if "g2_bifurcation_record" not in dev22 or \
            "g2_bifurcation_record" not in dev23 or \
            "g2_bifurcation_record" not in dev24:
        _fail("dev-r22/dev-r23/dev-r24 g2_bifurcation_record 延续引用源"
              "缺失")
    if dev20["round_id"] != "2026-09-09-r20" or \
            dev20["hypothesis_test_i"]["verdict"] != "reject":
        _fail("dev-r20 先验件常量不符")
    if dev19["round_id"] != "2026-09-09-r19" or \
            dev19["hypothesis_test_i"]["verdict"] != "marginal":
        _fail("r19 dev-record 先验件常量不符")
    # 联合评价趋势历史行（dev-r24 冻结转录 r5–r24）
    trend_rows_prior = dev24["joint_evaluation_trend"]["by_round"]
    if [r["round"] for r in trend_rows_prior] != [
            "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "r16", "r17", "r18", "r19", "r20", "r22", "r23",
            "r24"]:
        _fail("趋势历史行（dev-r24）不符")
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
    # run-r25 盘上件哈希=简报锚（251102e8）
    if not run25_sha.startswith("251102e8"):
        _fail("run-r25 实测 sha 与 251102e8 锚不符")


def build_dev_record() -> dict:
    """构建 round25-dev-record（纯函数：只读盘上冻结输入+常量）。"""
    protected = verify_protected_files()
    run = _json_load(REL_RUN_R25)
    run16 = _json_load(REL_RUN_R16)
    run19 = _json_load(REL_RUN_R19)
    run20 = _json_load(REL_RUN_R20)
    run22 = _json_load(REL_RUN_R22)
    run23 = _json_load(REL_RUN_R23)
    run24 = _json_load(REL_RUN_R24)
    prep = _json_load(REL_PREP_R25)
    dev19 = _json_load(REL_DEV_R19)
    dev20 = _json_load(REL_DEV_R20)
    dev22 = _json_load(REL_DEV_R22)
    dev23 = _json_load(REL_DEV_R23)
    dev24 = _json_load(REL_DEV_R24)
    typology = _json_load(REL_TYPOLOGY)
    guidance25_sha = _sha(REL_GUIDANCE_R25)
    guidance23_sha = _sha(REL_GUIDANCE_R23)
    axis_sha = _sha(REL_AXIS_PLAN)
    typology_sha = _sha(REL_TYPOLOGY)
    run25_sha = _sha(REL_RUN_R25)
    _verify_facts(run, run16, run19, run20, run22, run23, run24, prep,
                  dev19, dev20, dev22, dev23, dev24, typology,
                  guidance25_sha, guidance23_sha, axis_sha, typology_sha,
                  run25_sha, run["reader"]["raw_files"])

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

    # 联合评价趋势：r5–r24 行=round24-dev-record 在案行（冻结转录）；
    # r25 行=本轮 run 实测
    trend_rows = list(dev24["joint_evaluation_trend"]["by_round"])
    if [r["round"] for r in trend_rows] != ["r5", "r6", "r7", "r8", "r9",
                                            "r10", "r11", "r12", "r13",
                                            "r14", "r15", "r16", "r17",
                                            "r18", "r19", "r20", "r22",
                                            "r23", "r24"]:
        _fail("趋势历史行不符")
    trend_rows.append({
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "matches_total": agg["matches_total"],
        "round": "r25",
        "round_id": ROUND_ID,
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "source": {"path_rel": REL_RUN_R25, "sha256": run25_sha},
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
            "全旗标合计口径仅作附记（58/107=0.542056，非弃权 49+弃权 58）；"
            "本轮预注册主通道=归因三支判据（(ncd) G1 维持且 M4(n=6)≥"
            "0.261904→not_criterion_dominated；criterion_dominated 支因 "
            "M4 条件超出不命中；split_half=机制观察单列不进分支）；bottom "
            "全旗聚合弃权率 22/24=0.916667 为侧观察度量[M2，较 r16 基线与 "
            "r19–r24 全部上升、M2 升=机制观察单列]；实例层/视角层分列、"
            "全旗标合计非主通道"),
        "abstain_rate_by_instance": {
            n: run["instances"][n]["combined"]["abstain_rate"]
            for n in INSTANCE_ORDER},
        "abstain_rate_range_by_view": {
            "bottom": run["view_layer"]["bottom"]["abstain_rate_range"],
            "note": ("bottom 极差 0.333333=1.0−0.666667（按可计算实例；"
                     "bottom-i1=零旗格 None 不计入并如实注明[合法零旗输出]"
                     "）；top 逐实例两板合计口径极差 0.857143=1.0−0.142857"
                     "（top-i5=1.0 全弃权 vs top-i6=0.142857 个体散跨越"
                     "值域）；M4(n=6) 12 格口径极差=1.0（top-i5/applied "
                     "1.0−top-i6/applied 0.0）——两口径分列、跨口径比较="
                     "描述性声明"),
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
                 "instance_serial_two_wave 两波次串行保序）；R25T/R25B "
                 "前缀=指引 §6 落盘固化（observation-guidance-r25.md=r23 "
                 "基座 866b0157 机械变换派生新件 86af24dd、其 §6 示例前缀"
                 "已在件——s70/s80 机械派生先例同型；对照 r16/r22/r24 字节"
                 "复用+派发层覆盖路径）；flag_id 编号行为=11/11 有旗实例"
                 "全部同实例跨板连续+2 格零旗标[bottom-i1 两板 flags=[]="
                 "合法零旗输出、弃权率=None 口径触发]（与 prep-record "
                 "naming「同实例同侧跨板连续」声明相符）；轮内同名旗号跨"
                 "实例出现[R25T-001 见于 top-i1–i6 六实例等]=实例间编号"
                 "独立语义的直接观测、按 (instance, state, flag_id) 限定"
                 "不混淆；本轮无派发操作事故；v1.2 工具规约沿用 24/24 派次"
                 "自述合规与输出格式披露如实登记为混杂因素披露，不作废"),
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
            "representative_configuration（top-i1+bottom-i4，"
            "measurement_design item 4 n=6 口径：每视角 flag_count 升序"
            "第 3 序位（下中位）实例——top 升序 6/7/10/15/17/28 第 3 序位"
            "=top-i1 唯一、bottom 升序 0/4/4/4/6/6[bottom-i1 零旗格]第 3/4 "
            "序位同为 4[i2/i4/i6 三实例并列]→按实例编号先序取 bottom-i4——"
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
    # g2_bifurcation_record/r23/r24 同名记录先例，如实单列不凌驾字母裁决；
    # 本轮 G2=0 清零维持=资格门满足——分岔记录维持「链闭合状态」登记）
    g2_bifurcation_record = {
        "bifurcation": (
            "guard 设计意图（top 视非弃权旗标 frame_box_pct 几何门=负责任"
            "报告的报告框 hygiene 守门、出局条目不得回升）与字母裁决的关"
            "系本轮换型登记：r22=G2 破坏压过 M1 带内复制（字母=regressed）"
            "；r23=G2 出局条目未清零本身进裁决（字母=confounded）；r24="
            "G2 被 prep-record 预注册降格为「实测观察项、非本轮字母支」（"
            "G2>0 才触发资格门剔除）且实测清零；r25 延续 r24 口径=G2=观察"
            "项非字母支且实测再度清零（r19=0→r22=2→r23=1→r24=0→r25=0、"
            "资格门满足=r25 入排序）；字母裁决本轮由 M4(n=6) 单判据承担"
            "（not_criterion_dominated；split_half=机制观察单列）——G2 链"
            "与字母的两账分列模式维持、本轮无 G2-字母分岔（如实登记）；"
            "r22 字母=regressed、r23 字母=confounded、r24 字母=not_"
            "instance_dominated 维持不改写"),
        "continuation": {
            "mode": ("分叉记账模式延续（照 r20 g1_bifurcation_record/r22 "
                     "g2_bifurcation_record/r23/r24 同名记录先例：字母/机制"
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
            "round24_dev_record": {
                "path_rel": REL_DEV_R24,
                "sha256": _sha(REL_DEV_R24),
                "sha256_prefix_expected": "1a344edf",
                "section": ("g2_bifurcation_record（r24 轮 G2 链闭合状态"
                            "登记在案=本链上一环）"),
            },
        },
        "counts": {
            "g2_geometry_gate_r19": 0,
            "g2_geometry_gate_r22": 2,
            "g2_geometry_gate_r23": 1,
            "g2_geometry_gate_r24": 0,
            "g2_geometry_gate_r25": 0,
            "g2_rejected_entries_r25": 0,
            "g2_eligibility_gate_satisfied_r25": True,
            "g1_bottom_courtyard_non_abstain_r25": dict(EXPECT_G1_R25),
            "g1_baseline_r16_live": dict(EXPECT_G1_BASELINE),
            "g1_r20_broken_registered": dict(EXPECT_G1_R20_BROKEN),
            "contact_family_abstain_flags_rubric_r25": 3,
            "m4_n6_exceeds": True,
            "split_half_branch_role": ("机制观察单列、不进分支判定"
                                       "（本轮 260377>90640=聚合亦移动；"
                                       "与 r24 双判据分支的差异如实登记）"),
            "verdict": "not_criterion_dominated",
        },
        "counterfactual_check": {
            "function": "attribution_verdict_fixed_point",
            "guards_ok_false": ["guard_interrupted", "guard_interrupted_g1"],
            "m4_within": ["criterion_dominated",
                          "criterion_dominated_m4_within"],
            "m4_exceeds": [
                "not_criterion_dominated",
                "not_criterion_dominated_m4_exceeds"],
            "note": ("同一 G1 维持输入下 M4 降入 261904 内即字母翻转为 "
                     "criterion_dominated（attribution_verdict_fixed_point"
                     "(261903, True) 构造可复算）；本轮 M4=1000000≥261904→"
                     "not_criterion_dominated=三态纯函数、构造可测"
                     "[split_half 已不在分支判定内=与 r24 的差异如实登记]"),
        },
        "declared_date": DECLARED_DATE,
        "letter_vs_fact": {
            "letter": ("not_criterion_dominated（(ncd) 支="
                       "not_criterion_dominated_m4_exceeds；唯一正式裁决，"
                       "轮后不改写；后续任何机制归因不得改判本轮字母；r24 "
                       "字母=not_instance_dominated、r23 字母=confounded、"
                       "r22 字母=regressed 亦维持不改写）"),
            "gate_chain_fact": ("G2 几何门出局条目 r22=2→r23=1→r24=0→r25="
                                "0 清零维持（r19=0 对照在案；top 非弃权旗 "
                                "47 条无一超门）——机制观察单列、不进字母、"
                                "不改写字母"),
            "status": ("两账分列、不合并、不改写（照 r20 g1_bifurcation_"
                       "record/r22/r23/r24 g2_bifurcation_record「字母/机制"
                       "教训分列」先例）"),
        },
        "observation": (
            "G2 链闭合状态登记维持：几何门出局条目经 r22（2=silk 宽框）→"
            "r23（1=合并铜块）→r24（0）→r25（0）连续两轮清零——r22 型"
            "宽框与 r23 型合并体两类机制在条款轮亦未再现（本轮 top 非弃权旗 "
            "47 条含 6 条 courtyard 类+41 条 other/silk 类报告、无一 "
            "area_ratio>10）；G2 守门本轮满足资格门语义（guard_ok=不升）"
            "且 r25 入排序——字母裁决与 G2 链分账模式维持；G1=六 bottom "
            "实例 courtyard 非弃权全 0 维持（r20 破坏 2/0/0 在案=分岔"
            "记录）"),
        "role": ("机制教训单列：不凌驾、不改写字母裁决（not_criterion_"
                 "dominated 维持唯一正式裁决）；不进任何度量；描述性记录、"
                 "非因果证明"),
        "trigger_source": ("G2 链闭合登记触发=几何门出局条目 r25=0 清零"
                           "维持（r19=0→r22=2→r23=1→r24=0→r25=0）；本轮"
                           "字母判据由 M4(n=6) 单判据承担（非 M1 量级漂移"
                           "路径）"),
    }

    # 三轴实验总收束位（comparison_rule 排序；r25 入排序居首；guidance-r19
    # 胜出记录维持 conditional/double-entry 现状）
    three_axis_experiment_closeout = {
        "attribution_status_axis3_benefit": (
            "guidance-r19 胜出记录维持 conditional/double-entry 现状：M1 "
            "量级在 r22 新鲜实例群带内复现已登记（机制方向支持）、守门 G2 "
            "于 r22 破坏（字母=regressed 在案）、r23 归因轮落 confounded"
            "（在案）、r24 实例群扩容轮落 not_instance_dominated（在案）、"
            "本轮 r25=判据内容轴轮落 not_criterion_dominated（M4 条件超出"
            "=边界操作化未收敛个体散）——r25 五键 (0.433…, 0.916…, 22, "
            "1.0) 中 M4=判据内容轴的描述性边界判据、非 guidance-r19 配置"
            "效应读数；复制未达成、不升级：三轴判据（判据内容/渲染/指引）"
            "收束决议与轴停止决议不变（本轮=判据内容轴单变量操作化、非判据"
            "调参轴重开、§4 原文与任何量化判据零修改）；两账并列、不合并、"
            "不改写"),
        "comparison_rule_note": (
            "比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json "
            "为准（b6ec6467；FROZEN=先于 R17–R21 任何实验轮盲读冻结）；"
            "r25 在该计划时间界之外（r21 槽位永久留空后的判据内容轴归因"
            "轮=非三判据轴任何一支重开、轴停止决议不变），本轮结果仅登记"
            "于对照账、不触发任何计划内规则分支"),
        "development_domain_discipline": (
            "按协议 v1 §4，本批证据属 development 域，不得冒充未见留出；"
            "in_calibrated_range 恒 False 直到正式采纳（须人工批准）；"
            "达标证据仍须留出集"),
        "final_conclusion_unchanged": (
            "三轴实验最终结论维持=收益最大配置=轴3 单变量（guidance-r19，"
            "M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4；按冻结 "
            "iv_final_selection 全部已测配置中排序最优者）——r25 判据内容"
            "轴归因轮不改变该收束（r25 入排序居首=M1 0.433735 为全场最低、"
            "但唯一实验变量=判据内容条款=非三判据轴重开[判据内容零修改、"
            "仅边界显式化]，仅在机制观察层新增「条款操作化未收敛个体散+"
            "split-half 聚合亦移动+M1 降/M2 升并存+G2 链连续清零+类别门 "
            "1 条」五项事实；跨轮实例群漂移混杂照旧声明=M1 降与实例群重抽"
            "混同、不构成配置效应证据）"),
        "ranking": {
            "eligible_rows": ["r16_baseline", "r17_axis1", "r18_axis2",
                              "r19_axis3", "r24_expansion",
                              "r25_this_round"],
            "excluded_rows": {
                "r20_combo": "G1 破坏（2/0/0，run-r20 在案）",
                "r22_repeat": "G2 破坏（几何门 0→2，run-r22 在案）",
                "r23_repeat": "G2 破坏（几何门未清零 2→1，run-r23 在案）",
            },
            "ranking_order_best_first": ["r25_this_round", "r19_axis3",
                                         "r24_expansion", "r18_axis2",
                                         "r16_baseline", "r17_axis1"],
            "status": ("comparison_rule 排序（r25=G1/G2 满足=入排序、居首"
                       "——M1 0.433735 全场最低、M2 0.916667 全场最高两向"
                       "如实并列）；r20/r22/r23 不入排序（资格门剔除、行仅"
                       "如实入账）；r24 在案入排序居第三"),
        },
        "role": ("三轴实验总收束位（development 域描述性边界工具、非门、"
                 "无字母语义、不凌驾 APR-0011 与阈值；两账并列、不合并、"
                 "不改写）"),
    }

    # 下一候选建议（如实单列、由用户拍板、本包不预写决策）
    next_candidate_suggestion = {
        "context": (
            "r25 判据内容轴归因轮字母=not_criterion_dominated（G1 维持且 "
            "M4(n=6)=1.0≥0.261904=边界操作化未收敛个体散、判据内容非主因、"
            "残余归因=其他输出侧/模型侧固有；split_half=0.260377>0.09064="
            "聚合亦移动[与 r24 反转]、机制观察单列；r24 字母=not_instance_"
            "dominated、r23 字母=confounded、r22 字母=regressed 维持不改"
            "写）；归因链三轴[框宽/实例群/判据内容]全部排除完毕——开发线"
            "收敛（连续达标=0、正式采纳门槛未达）——下一动作如实单列、由"
            "用户拍板、本包不预写决策"),
        "decision_authority": "由用户拍板（本包只列选项、不预写决策）",
        "options": [
            {
                "motivation": ("字母=not_criterion_dominated 且归因链三轴"
                               "排除完毕=判据内容操作化归因收口；留出集时机"
                               "=开发线收敛（须用户拍板在案；HOLDOUT-PLAN.md"
                               " a4b80193 Tier 1/2 候选清单零接触在案）；"
                               "in_calibrated_range 恒 False 直到正式采纳"
                               "（须人工批准）"),
                "option": ("接受发展域现状收束训练环（不再追加迭代轮）；"
                           "留出集时机由用户判断"),
                "preregistration_required": False,
            },
            {
                "motivation": ("归因链排除完毕后的唯一剩余方向=其他输出侧/"
                               "模型侧固有（本轮归因结论位登记的残余归因位）"
                               "——候选如实列示；新预注册轮先于盲读冻结"
                               "（prep-record 纪律）；本包不预写设计"),
                "option": ("其他输出侧因素操作化归因轮（对残余归因位做"
                           "单变量操作化；须新 prep-record 先于盲读冻结="
                           "预注册纪律；不新造第四轴名称、只描述方向）"),
                "preregistration_required": True,
            },
            {
                "motivation": ("split-half 本轮 0.260377>0.09064=聚合亦"
                               "移动、r24 为 0.018640=聚合稳——条款改变聚合"
                               "行为的机制观察需第三样本分离实例群漂移与条款"
                               "效应（同指引重复轮 r16/r22 先例同型——配置与 "
                               "r25 完全同构[指引复用、渲染字节冻结、仅实例"
                               "重抽 n=6]）；或收束训练环"),
                "option": ("再一轮同指引重复轮（第三样本；r16/r22 先例同型，"
                           "r25 指引字节复用路径）或收束训练环"),
                "preregistration_required": True,
            },
        ],
        "status": ("下一候选建议（非冻结规则输出——三轴计划已收束、本轮"
                   "为计划外判据内容轴归因轮；本节为 dev-record "
                   "如实登记的选项清单）"),
    }

    axis_experiment_ledger = {
        "benefit_metrics_definitions": {
            "M1_top_aggregate_abstain_rate":
                "top 全旗聚合弃权率=该轮 top 视 12 派次（两态×i1–i6）全部"
                "旗标中弃权旗占比（6 位小数；本轮实测 36/83）",
            "M2_bottom_aggregate_abstain_rate":
                "bottom 全旗聚合弃权率（同法；本轮实测 22/24）",
            "M3_blackdot_abstain_flags_rubric":
                "黑点族弃权旗数（rubric 口径=分型件 round_totals "
                "{r}.families.existence_blackdot 同法机械套用；本轮实测 "
                "22、全弃权、逐实例分旗；M3 槽位定义维持冻结件黑点"
                "口径——contact=3 另列不占槽=判据侧对照账纪律延续）",
            "M4_top_per_instance_rate_range":
                "top 逐实例弃权率极差（本轮 n=6 口径=12 个（态,实例）格率"
                "极差 max−min=1.0−0.0=1.0；与 r16–r23 逐实例两板"
                "合计口径（3 格）的粒度差异=v1.3 扩容口径显式登记、跨口径"
                "比较=描述性声明、阈值 0.261904=r16 历史口径在案值原样引用"
                "不改写）",
            "split_half_M1_diff":
                "|M1(i1–i3 双视图聚合)−M1(i4–i6 双视图聚合)|（6 位定点整数"
                "；本轮实测 |0.339623−0.600000|=0.260377>0.09064=聚合亦"
                "移动[与 r24 的 0.018640 反转=机制观察如实登记]；阈值 "
                "0.09064=r15→r16 纯重抽漂移在案参照；本轮=机制观察单列、"
                "不进分支判定[与 r24 双判据分支的差异如实登记]）",
            "contact_family_abstain_flags_rubric":
                "contact 族弃权旗数（全视，分型件 rubric 口径；本轮实测 3"
                "[top 3+bottom 0]、r16 基线 10、r13–r16 链 8/15/5/10 在"
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
                "r24_expansion": dict(EXPECT_R24_MEASURED),
                "r25_this_round": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                   "M3": EXPECT_M3, "M4": EXPECT_M4,
                                   "split_half_M1_diff": EXPECT_SPLIT_HALF},
            },
            "note": ("九行并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合/"
                     "r22 重复轮/r23 归因轮/r24 扩容轮/r25 条款轮；前八行="
                     "round24-dev-record 台账在案行逐值继承+本轮 live 交叉"
                     "核对）；按冻结 comparison_rule=(M1 升序, M2 升序, "
                     "M3 升序, M4 升序) 字典序：r20/r22/r23=G 守门破坏经"
                     "资格门剔除不入排序；r25=G1 维持+G2=0=资格门满足=入"
                     "排序、居首（M1=0.433735 全场最低、M2=0.916667 全场"
                     "最高两向如实并列）；排序（不含 r20/r22/r23）=r25 "
                     "第一、r19 轴3 第二、r24 第三、r18 轴2 第四、r16 基线"
                     "参照行第五、r17 轴1 末位（M1=0.88 劣于基线=负向）——"
                     "如实登记、不预写后续决策"),
            "role": ("条款轮五键九行并列登记（comparison_rule 冻结规则的"
                     "已测行并列；r16–r24 行=round24-dev-record 台账在案"
                     "行实测装载+各自 run 内嵌记录 live 复算交叉核对、r25 "
                     "行=本轮 run 实测装载；均 fail-closed）"),
        },
        "frozen_plan_ref": {"path_rel": REL_AXIS_PLAN, "sha256": axis_sha},
        "measured_note": (
            "实测全部由本件从 calibration-run-r25.json（251102e8…）盘上值"
            "装载（M1=36/83=0.433735 与 m.top_abstain_rate_r25、M2=22/24="
            "0.916667 与 m.r25_m_tuple_6dp.M2、M3=22 与 black_dot_tracking."
            "rubric_families（rubric 口径 existence_blackdot、r13–r16 132 "
            "条弃权旗重放对拍逐一相等）、M4=1.0 与 m.r25_m_tuple_6dp."
            "M4、split_half=0.260377 与 m.split_half_M1_diff_r25、contact="
            "3 与 contact_family_abstain_flags_rubric_r25 逐一相等，fail-"
            "closed），非手抄；axis-plan 在案 r16 基线四键 [0.771429, "
            "0.857143, 12, 0.261904] 与 run-r25 baseline_cross_check 交叉"
            "核对一致；M1 绝对降幅 0.771429−0.433735=0.337694 超显著收益"
            "阈值 0.10（描述层命中、与字母裁决分列互不改写——r18/r19/r20/"
            "r22/r23/r24 先例延续；跨轮实例群漂移混杂照旧声明、本轮唯一实验"
            "变量=判据内容条款、实例群重抽=轮际固有混杂；主判据=归因三支"
            "判据、M4 条件超出→not_criterion_dominated；M1 降=机制观察+"
            "APR-0011 门指标照常分列、不构成 criterion_dominated 证据）"),
        "next_candidate_r25": (
            "见 next_candidate_suggestion（三选项如实单列、由用户拍板、"
            "本包不预写决策）"),
        "role": ("实验对照账（axis-experiment-plan-r17-r20 冻结比较规则的 "
                 "r25 行登记；development 域描述性边界工具、非门、无字母语"
                 "义、不凌驾 APR-0011 与阈值）"),
        "significant_benefit_vs_r16": {
            "definition": ("「显著收益」=相对 r16 基线 M1 绝对降幅 ≥0.10（"
                           "阈值覆盖跨轮实例群漂移噪声的历史幅度，参照 "
                           "r15→r16 纯重抽变动 0.09064）"),
            "met": True,
            "note": ("r25 M1 绝对降幅 0.337694 ≥0.10=显著收益定义在描述层"
                     "命中（r18 降幅 0.126268、r19 降幅 0.309891、r22 降幅 "
                     "0.381185、r23 降幅 0.286581、r24 降幅 0.219048 亦 "
                     "≥0.10）；r25 降幅须与 n=6 分母效应（top 旗数 105→83）"
                     "并读、实例群混杂照旧声明；M1 降=机制观察+APR-0011 门"
                     "指标照常分列、本轮字母只看 M4 个体散（per prep-record"
                     " m1_m2_gate_separate 原文）；字母裁决与实验账分列互"
                     "不改写"),
            "r18_drop_reference": EXPECT_R18_DROP_REFERENCE,
            "r19_drop_reference": EXPECT_R19_DROP_REFERENCE,
            "r22_drop_reference": EXPECT_R22_DROP_REFERENCE,
            "r23_drop_reference": EXPECT_R23_DROP_REFERENCE,
            "r24_drop_reference": EXPECT_R24_DROP_REFERENCE,
            "r25_m1_absolute_drop": EXPECT_R25_M1_ABSOLUTE_DROP,
        },
        "status": ("R25 实测 (M1,M2,M3,M4,split_half)=(0.433735, 0.916667,"
                   " 22, 1.0, 0.260377)（contact=3 另列）；r25 入排序"
                   "（G1/G2 满足）、居首；排序=r25_this_round 第一（"
                   "如实记录）；字母与实验账分列互不改写（本轮 not_criterion_"
                   "dominated：M4 条件超出=边界操作化未收敛个体散、判据内容"
                   "非主因、残余归因=其他输出侧/模型侧固有）；guidance-r19 "
                   "胜出记录维持 conditional/double-entry 现状、复制未达成"
                   "不升级；三轴实验已收束"
                   "（收益最大配置=r19_axis3 维持）"),
        "this_round_measured": {"M1": EXPECT_M1, "M2": EXPECT_M2,
                                "M3": EXPECT_M3, "M4": EXPECT_M4,
                                "split_half_M1_diff": EXPECT_SPLIT_HALF},
    }

    # 机制观察单列（逐实例分布/split-half 分解/三族对照/黑点/援引/条款
    # 行为观察/M1 降 M2 升分解）
    mechanism_observation_r25 = {
        "citation_counts_vs_r19_r22_r23_r24": {
            "r25_measured": {
                "flag_level_branch_literal": 0,
                "flag_level_clause_literal": 16,
                "flag_level_iiia_literal": 11,
                "flag_level_s5b_literal": 0,
                "flag_level_sanwen_literal": 13,
                "notes_level_clause": ("24/24 派次（弃权边界条款[三问/弃权"
                                       "边界/§4(终) 任一 token]全部派次"
                                       "援引）"),
                "notes_level_cand_explain": ("17/24 派次 notes 级含「候选"
                                             "解释」+58/58 弃权旗 "
                                             "location_evidence 逐旗列举候"
                                             "选解释=条款三问之(3) 行为观测"),
                "notes_level_iiia": "12/24 派次（bottom-i1/i4+top-i1/i3/i4/"
                                    "i6 两板）",
                "notes_level_s5b": ("0/24 派次（本轮指引=r25 派生件、仍无 "
                                    "§5B 节=任何援引为零上下文）"),
                "notes_level_s6_clause": ("9/24 派次（§6 报告框收敛条款随"
                                          "基座在案[非本轮变量]）"),
                "notes_level_sanwen": "22/24 派次（非含派次=applied/prep1-"
                                      "bottom-i6 两派次）",
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
            "r24_baseline_registered": {
                "flag_level": "旗级全 0",
                "notes_level": "notes 级 (iii-a)=8/24、§6 条款=20/24",
                "source": "run-r24 在案",
            },
            "status": ("§5B、(iii-a)、§6 与 §4(终) 条款援引计数多集合分开"
                       "记、对照 r19/r22/r23/r24 四基线如实（旗级 (iii-a)="
                       "11 旗逐旗摘录在案 run-r25 iiia_flag_rows；弃权边界"
                       "条款=本轮唯一新增判据变量、r24 前无在案基线=如实"
                       "声明）；不进字母裁决"),
        },
        "clause_behavior_observation": {
            "role": ("条款行为观察（本轮唯一实验变量=§4 末尾弃权边界操作化"
                     "条款的行为效应；机制观察单列、不进字母裁决）"),
            "cand_explain_listing_rate": ("弃权理由候选解释列举率=58/58 "
                                          "弃权旗（location_evidence 逐旗含"
                                          "「候选解释」=条款三问之(3)「弃权"
                                          "理由须逐条列出各候选解释」的直接"
                                          "行为观测；与 r24 无条款基线无可比"
                                          "口径如实声明）"),
            "sanwen_citation_rate": ("三问援引率（notes 级）=22/24 派次（"
                                     "applied/prep1-bottom-i6 两派次非含）；"
                                     "旗级「三问」字面援引=13 旗（均弃权旗）"),
            "m1_m2_shift": ("M1 降/M2 升分解：M1 0.552381→0.433735=降 "
                            "0.118646、M2 0.692308→0.916667=升 0.224359——"
                            "两向均不进字母（per prep-record "
                            "m1_m2_gate_separate 原文：本轮字母只看 M4 个体"
                            "散、不看 M1）；弃权→低 confidence 非弃权旗=旗"
                            "仍设立、非「判正常」=条款未放宽判据的输出侧"
                            "佐证"),
            "split_half_behavior": ("split-half 0.260377>0.09064=聚合亦"
                                    "移动（与 r24 的 0.018640=聚合稳反转）"
                                    "——条款改变了聚合行为、机制观察如实"
                                    "登记（不进分支判定）"),
            "status": ("条款行为观察如实单列（描述性、非因果证明；不凌驾"
                       "字母裁决）"),
        },
        "instance_distribution_observation": {
            "note": ("逐实例率分布（机制观察；单列、不进字母裁决）：top 六"
                     "实例=0.3/0.466667/0.285714/0.647059/1.0/0.142857——"
                     "top-i5=1.0（6/6 全弃权）与 top-i4=0.647059 为高峰、"
                     "top-i6=0.142857 与 top-i3=0.285714 为低谷（对照 r24 "
                     "的 1.0/0.863636 高峰与 0.117647/0.133333 低谷：两轮"
                     "实例群全量重抽、个体散在条款操作化后仍跨越整个值域="
                     "判据内容非主因的逐实例层佐证，如实单列）；同一实例"
                     "两板率接近（态内一致）、跨实例率跨越整个值域=离散主要"
                     "来自实例间异质性而非态间/判读噪声；bottom 六实例="
                     "None/1.0/0.666667/1.0/1.0/1.0（bottom-i1=零旗格 "
                     "None[合法零旗输出]）；聚合 M1=0.433735 落高低实例"
                     "之间=聚合值对实例抽样敏感的直接展示；12 个（态,实例）"
                     "格率极差[M4(n=6) 口径]=1.0"),
            "top_rates": dict(EXPECT_TOP_INSTANCE_RATES),
            "bottom_rates": {"bottom-i1": None, "bottom-i2": 1.0,
                             "bottom-i3": 0.666667, "bottom-i4": 1.0,
                             "bottom-i5": 1.0, "bottom-i6": 1.0},
            "m4_12_cell_range": EXPECT_M4,
        },
        "split_half_decomposition": {
            "note": ("split-half 分解解读（单列、不进字母裁决；与 r24 的"
                     "机制观察反转如实登记）：split_half_M1_diff=0.260377"
                     "（A=18/53=0.339623 vs B=18/30=0.600000）>0.09064="
                     "对半聚合显著分化（低编号半区明显低于高编号半区）；与 "
                     "r24（0.018640≤0.09064=聚合稳）反转=条款改变了聚合"
                     "行为（不同实例对条款的行为响应不同构、对半聚合不再"
                     "互相抵近）；同一数据 M4(n=6)=1.0 远超 0.261904 参照="
                     "个体散未收敛——聚合移动与个体散未收敛并存，与字母="
                     "not_criterion_dominated 一致但不构成其证据（两账"
                     "分列）"),
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
            "r24_registered": {"contact": 4, "existence_blackdot": 28,
                               "existence_other": 44},
            "r25_measured": {"contact": 3, "existence_blackdot": 22,
                             "existence_other": 20},
            "status": ("三族计数（分型件 rubric 口径）对照 r19（4/4/14）"
                       "与 r22（2/4/12）与 r23（8/8/7）与 r24（4/28/44）"
                       "四基线：contact 3=四轮最低、黑点 22=低于 r24 的 28、"
                       "高于 r19/r22/r23 三基线（实例群重抽=轮际混杂；跨轮"
                       "对照=描述性、如实声明）、存在性其他 20=低于 r24 的 "
                       "44；另 other=13 为 n=6 口径新高（r19–r24 均 0、"
                       "如实登记）——r13–r16 132 条重放对拍逐一相等后套用 "
                       "r25，如实登记为度量教训、不改字母"),
        },
        "black_dot_observation": {
            "by_instance": dict(EXPECT_BLACK_DOT_BY_INSTANCE),
            "counts": ("黑点族弃权旗 22 条（全弃权、逐实例分旗：top-i3 两"
                       "板 4+top-i4 两板 2+bottom-i2 两板 4+bottom-i3 两板 "
                       "2+bottom-i4 两板 4+bottom-i5 两板 6）；另黑点转非"
                       "弃权旗 4 条（top-i6 两板 4=圆点/实心深色按条款三问"
                       "之(1) 可定位路径设旗）；判正常派次 6（applied/prep1-"
                       "bottom-i1[零旗格派次]+applied/prep1-top-i1+applied/"
                       "prep1-top-i5；对照 r15=3/r16=2/r18=2/r19=3/r20=4/"
                       "r22=4/r23=2/r24=2）——如实单列"),
        },
        "top_abstain_typology_r25": {
            "counts": dict(EXPECT_TYPE_COUNTS),
            "note": ("top 弃权 36 条逐旗机械主出口分类（exit_type_"
                     "classify 关键词规则、与 rubric 族两套口径分列不合并；"
                     "逐旗 (instance, state, flag_id) 入账 run-r25 "
                     "abstain_typology.typology_rows）：接触性 5+存在性 "
                     "20+层归属其他 11（对照 r24 26/30/2、r23 6/10/0、r22 "
                     "2/14/0、r19 5/13/0——条款轮 top 弃权绝对数 58→36、"
                     "层归属其他占比上升 2/58→11/36；rubric 链式回放 r13–"
                     "r16 基线 8/15/5/10 先核对一致才可应用 r25 分型[照 "
                     "s78 模式]）"),
        },
        "role": ("机制观察单列（per r25-prep-record adjudication."
                 "mechanism_observation_separate 原文）：不进字母裁决、"
                 "不凌驾、不改写字母"),
    }

    # GT 里程碑延续（r22 agreement 首次计入+r24 的 4/6 首计入维持；
    # 本轮 agreement 不计入=单实例命中）
    gt_agreement_milestone = {
        "agreement_first_counted": (
            "r22 里程碑维持不改写：GT 条目层 agreement 口径自 r12 引入以来"
            "首次计入发生在 r22（≥2/3 语义、GT-REVC-P1-L1SHORT 双实例一致"
            "命中，round22-dev-record 在案）；r24 里程碑维持不改写："
            "agreement≥4/6（v1.1「≥2/3 过半数」语义的 n=6 推广、v1.3 附录"
            "显式冻结）首次计入=L1SHORT 四实例一致命中（round24-dev-record "
            "在案）；本轮 r25=agreement 不计入：union=1/13=0.076923"
            "（GT-REVC-AP-1-R5U6 由 applied-top-i4 R25T-005 单实例命中"
            "[courtyard 类非弃权贴近报告]；1/6<4/6=agreement 空集——对照 "
            "r23 双命中亦未计入 agreement：单/双实例命中的轮际不稳定如实"
            "登记、非能力断言）"),
        "gt_id": "GT-REVC-AP-1-R5U6",
        "hit_flags": sorted(f"{i}:{f}:{s}" for f, i, s
                            in EXPECT_GT_HIT_FLAGS),
        "recall": {"agreement": 0.0, "union": 0.076923},
        "structural_note": ("bottom 非弃权旗零匹配属结构性（GT 13 条全部 "
                            "side=top、bottom GT 无源在案 gt-audit-r1）；"
                            "GT 侧维持全关闭声明延续（gt-audit-r1 三候选"
                            "全部关闭、r9–r24 延续零改动、非新 GT）"),
    }

    honest_conclusion = (
        "本轮（development 域判据内容轴归因轮=三混杂轴归因链第三轴执行轮"
        "[第二十五轮；执行 round24-dev-record 下一候选建议选项(b)+用户 "
        "2026-09-10 拍板选项(b)定向判据内容轴]；唯一实验变量=判读指引 §4 "
        "末尾弃权边界操作化条款[observation-guidance-r25.md=86af24dd 由 "
        "observation-guidance-r23.md 866b0157 机械变换派生落盘新件、byte "
        "delta=+937、§4 原文与任何量化判据零修改]；渲染零变更=renders-r14b "
        "四图字节复用[与 r14–r24 盲读同一批文件]+GT/阈值/协议正文零变更"
        "（13 条冻结、v1/v1.1/v1.2 继承不改+v1.3 n=6 附录沿用 r24、无新增"
        "附录；n=6 口径与 r24 完全同构、实例群重抽=轮际固有混杂）；"
        "changed_variables=1；【跳号声明延续】r21=冻结预留全组合条件位永久"
        "留空、r22 跳号声明在案、r25 与该位无涉）24 派次 107 旗标中 58 "
        "弃权、49 非弃权：代表配置（top-i1+bottom-i4；下中位序位、bottom "
        "tie 按实例编号先序如实）gt_recall=0.0（0/13）、seed_match_rate="
        "0.0（0/7，诊断口径，禁称 precision/FPR）、abstain_rate=0.5（7/14），"
        "联合评价 not_met（gt_recall、seed_match_rate 两项未达 APR-0011 "
        "暂行线；gt_count 13≥12 与 abstain_rate 0.5≤0.5 单分项入线；诊断"
        "对照，非采纳门；连续达标计数 0→0；GT 条目层 union=1/13=0.076923"
        "[R5U6 单实例命中]、agreement=0/13[1/6<4/6 不计入]，如实登记）。"
        "预注册假设（r24-not-instance-dominated-criterion-boundary-"
        "operationalization-attribution）归因三支判据裁决（按 r25-prep-"
        "record hypothesis_test.adjudication 原文）=not_criterion_dominated"
        "（字母口径，唯一正式裁决，轮后不改写）：落支=(ncd) not_criterion_"
        "dominated_m4_exceeds——本轮=G1 维持（六 bottom 实例 courtyard 非"
        "弃权全 0）且 M4(n=6)=1.0≥0.261904（6 位定点 1000000≥261904；12 "
        "格=（applied-top|prep1-top）×（i1–i6）各自实例率先 6 位定点取率"
        "再取最大−最小；阈值=r16 基线历史口径在案值原样引用、跨口径比较="
        "描述性）——弃权边界操作化未收敛个体散=判据内容非主因（残余归因="
        "其他输出侧/模型侧固有；归因链三轴[框宽/实例群/判据内容]全部排除"
        "完毕、残余=其他输出侧/模型侧固有=如实登记、不新造第四轴名称只"
        "描述）；criterion_dominated 支不命中=弃权边界显式化未使个体散收敛"
        "到 r16 基线极差尺度内；guard_interrupted 支（G1 破坏）未命中。"
        "split_half_M1_diff=0.260377>0.09064=聚合亦移动、与 r24 的 0.018640"
        "（聚合稳）反转=条款改变了聚合行为（机制观察单列、不进分支判定"
        "[与 r24 双判据分支的差异如实登记]）。「正确测出无效同样是有效证据」"
        "三向记账：字母=not_criterion_dominated（三支判据按预注册原文执行）、"
        "机制观察=逐实例率分布（top-i5=1.0 vs top-i6=0.142857 跨越值域）+"
        "split-half 聚合移动+M1 降/M2 升分解（0.552381→0.433735 降 "
        "0.118646；0.692308→0.916667 升 0.224359；两向均不进字母、APR-0011 "
        "门指标照常分列）+条款行为观察（三问援引率 22/24、弃权边界条款 "
        "notes 级 24/24、弃权理由候选解释列举率 58/58）+G2 链连续清零"
        "（0→2→1→0→0、资格门满足=r25 入排序）+类别门 1 条+三族计数对照四"
        "基线（黑点 22 低于 r24 的 28、other 13=n=6 口径新高）（单列不进"
        "字母）、度量教训=M4 跨口径粒度差异（12 格 vs r16–r23 逐实例两板"
        "合计口径、描述性声明）+split_half 分支使命完成+判据内容轴单变量"
        "操作化的验证力度声明（部分重复≠独立重复：每实例两派次=同实例重复；"
        "本轮唯一实验变量=判据内容条款、实例群重抽=轮际固有混杂）——三账"
        "分列、不合并、不改写（g2_bifurcation_record 与归因结论位承载；"
        "反事实构造：M4 降入 261904 内⇒criterion_dominated、"
        "attribution_verdict_fixed_point(261903, True) 可复算）。G2=0 清零"
        "维持=资格门满足（r25 入排序居首）；r24 字母=not_instance_dominated "
        "与 r23 字母=confounded、r22 字母=regressed 维持不改写。机制观察"
        "单列（不影响字母）：M2=bottom 全旗聚合弃权率 22/24=0.916667（对照 "
        "r16 12/14=0.857143、r19 4/7=0.571429、r20 4/14=0.285714、r22 2/"
        "10=0.2、r23 8/14=0.571429、r24 18/26=0.692308——较 r16 与 r19–"
        "r24 全部上升=M2 升如实单列）；零旗格=2 格（applied/prep1-bottom-i1 "
        "合法零旗输出、弃权率=None 口径触发=不编造数值；零旗格均在 bottom "
        "侧、M4 top 12 格集合不含=逐格率口径不受影响）；GT 双口径 union=1/"
        "13、agreement=0（R5U6 单实例命中）；通道归因几何门 0/类别门 1/"
        "视角门 0 对照 r19（0/2/0）与 r20（0/0/0）与 r22（2/4/1）与 r23"
        "（1/1/0）与 r24（0/6/0）。实验对照账：本轮五键 (M1,M2,M3,M4,"
        "split_half)=(0.433735, 0.916667, 22, 1.0, 0.260377)（M3 槽位=冻结"
        "件黑点族口径、contact=3 另列不占槽），九行并列（r16 0.771429/"
        "0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、r18 0.645161/"
        "0.684211/13/0.277778、r19 0.461538/0.571429/4/0.211111、r20 "
        "0.636364/0.285714/6/0.25、r22 0.390244/0.2/4/0.104545、r23 "
        "0.484848/0.571429/8/0.520833、r24 0.552381/0.692308/28/0.888889+"
        "split_half 0.018640、r25 0.433735/0.916667/22/1.0+split_half "
        "0.260377）——r20/r22/r23 均资格门剔除不入排序；r25 入排序居首、"
        "r24 在案入排序；comparison_rule 排序=r25 第一、r19 第二、r24 第三、"
        "r18 第四、r16 参照、r17 末位；显著收益定义描述层命中（M1 绝对降幅 "
        "0.337694≥0.10；r18 0.126268、r19 0.309891、r22 0.381185、r23 "
        "0.286581、r24 0.219048 亦 ≥0.10；r25 降幅须与分母效应并读、与"
        "实例群重抽混同如实声明）——与字母裁决分列互不改写。guidance-r19 "
        "胜出记录维持 conditional/double-entry 现状、复制未达成不升级。三轴"
        "实验总收束位：最终结论维持=收益最大配置=轴3 单变量（guidance-r19）；"
        "r25 入排序居首不改变收束、判据内容条款=非三判据轴重开（判据内容"
        "零修改、仅边界显式化）；发展域证据不得冒充留出。下一候选建议（"
        "如实单列、由用户拍板、本包不预写决策）：(a) 接受发展域现状收束"
        "训练环、留出集时机由用户判断；(b) 其他输出侧因素操作化归因轮"
        "（残余归因位）；(c) 同指引重复轮第三样本或收束训练环。"
        "not_criterion_dominated=预注册阈值命中方向的描述性结论、非因果"
        "证明——「正确测出无效同样是有效证据」；单轮 development 域只描述"
        "不断言；字母裁决只回答「弃权边界显式化后个体散是否收敛=判据内容"
        "是否为个体散主因」的判据命中方向；部分重复≠独立重复（同域同编排"
        "实例池、验证力度如实声明）；机制观察/度量教训单列、不凌驾不改写"
        "字母裁决；APR-0011 门（代表配置）与字母裁决分列不合并；本轮判据"
        "均为描述性边界、非门阈值（门零改动）。逐实例残余差异=个体散的"
        "测量对象（top 弃权率 0.3/0.466667/0.285714/0.647059/1.0/0.142857、"
        "bottom None/1.0/0.666667/1.0/1.0/1.0 如实）；本轮零旗格=2 格"
        "（bottom-i1 两板、None 口径触发）。不做「能力已修复/已达成」类"
        "断言；in_calibrated_range 恒 False。本批证据按协议 v1 §4 属 "
        "development 域，不得冒充留出。")

    notes = [
        ("比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、不翻转 "
         "critic_calibration_in_range（恒 False 维持 fail-closed）。"),
        ("seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；同板"
         "不同渲染不是独立板（process-v2 §4 联合评价）；多实例聚合并列口径不"
         "构成任何门的放宽或收紧（r25-prep-record 判据=归因三支判据、阈值零"
         "改动；弃权边界操作化=执行细则增补、§4 原文与任何量化判据零修改"
         "[no_loosening_note 在案]）。"),
        ("R16 对照基线=calibration-run-r16.json（同一聚合逻辑对内嵌实例记录"
         "双侧复算 top 27/35=0.771429、bottom 12/14=0.857143，与在案登记/"
         "axis-plan 锚交叉核对一致，不手工抄数）；r19/r22/r23/r24 参照元组="
         "各自 run 内嵌实例记录 live 复算（18/39、4/7；16/41、2/10；16/33、"
         "8/14；58/105、18/26）+prep-record 冻结锚交叉核对一致；contact 对照"
         "基线=分型件 rubric 口径 10（r13–r16 链 8/15/5/10 重放对拍逐一相等"
         "后才套用 r25 分型，不手工抄数）；轮间对比只做方向性描述（跨轮实例"
         "群混杂照旧；本轮唯一实验变量=判据内容条款、实例群重抽=轮际固有"
         "混杂）；M1 分母（top 旗数 35→39→22→41→33→105→83）随实例群规模"
         "变化、弃权率比较含分母效应，构成分解（top 弃权构成分型+rubric 族+"
         "援引分记+条款行为观察+黑点转非弃权旗）单列补足。"),
        ("归因三支判据的描述性边界纪律：M4(n=6) 阈值 0.261904=r16 基线历史"
         "口径在案值原样引用（12 格 vs 逐实例两板合计口径的粒度差异=v1.3 "
         "扩容口径显式登记、跨口径比较=描述性）；split-half 阈值 0.09064="
         "r15→r16 纯重抽漂移在案参照；两者均不得事后收放；split_half 本轮="
         "机制观察单列、不进分支判定（与 r24 双判据分支的差异如实登记："
         "实例群轴已由 r24 测毕、拆半阈值 0.09064=90640 的分支使命完成）；"
         "部分重复≠独立重复（同域同编排实例池、每实例两派次=同实例重复、"
         "验证力度如实声明）；本轮字母裁决只回答「弃权边界显式化后个体散"
         "是否收敛=判据内容是否为个体散主因」、不回答「条款本身是否有效"
         "操作」——not_criterion_dominated 支=残余归因如实登记（其他输出"
         "侧/模型侧固有、不新造第四轴名称）；G1 破坏（若发生）→guard_"
         "interrupted 独占（预注册三支恰三支、不新增字母支、不升级归因）。"),
        ("G2 分岔链闭合登记维持（判据设计机制教训，单列，供后续预注册参考、"
         "本轮不追溯适用）：guard 设计意图 vs 字母的分叉记账模式自 r20 "
         "g1_bifurcation_record/r22 g2_bifurcation_record[dev-r22="
         "b4b8fbe9 在案]/r23 同名记录[dev-r23=343a6747 在案]/r24 同名记录"
         "[dev-r24=1a344edf 在案]延续；r24 换型=G2 被 prep-record 预注册"
         "降格为「实测观察项、非字母支」（G2>0 才触发资格门剔除）且实测"
         "清零（0→2→1→0）；本轮延续同口径且实测再度清零（→r25=0、资格门"
         "满足=r25 入排序）——预注册字母优先（not_criterion_dominated）="
         "预注册纪律的正确执行；后续如需调整守门操作化定义，修订须走 "
         "prep-record 预注册（先于该轮盲读冻结）、不得事后改判本轮或既往"
         "轮次（r8–r24 字母裁决维持不变）。"),
        ("度量教训在案（供后续预注册参考、本轮不追溯适用）：M3 槽位定义维持"
         "冻结件黑点族口径、contact=3 另列不占槽=对照账纪律延续；contact 计"
         "数口径=分型件 rubric 机械套用（r13–r16 132 条重放对拍逐一相等后"
         "套用 r25；计数口径跨轮漂移是历史教训：r15 prose 口径 7 vs 分型件 "
         "rubric 口径 8 在案，axis-plan M3_caveat 已声明一律采用 rubric 口"
         "径）；本轮零旗格=2 格（applied/prep1-bottom-i1 合法零旗输出）→"
         "零分母 None 口径触发=不编造数值（实例弃权率=None、bottom 视角层"
         "中位数=None+min/max 按可计算实例；零旗格均在 bottom 侧、M4 top "
         "12 格集合不含=逐格率口径不受影响，per prep-record "
         "M4_operationalization_note 口径如实声明）；黑点 22 低于 r24 的 28+"
         "M4(n=6) 跨口径粒度差异=12 格口径延续登记；other 族 13=n=6 口径"
         "新高（r19–r24 均 0）如实登记；实验对照账与字母裁决分列互不改写"
         "（r18–r24 先例延续）。"),
        ("假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；机制观察"
         "/度量教训单列，不得凌驾或改写字母裁决；本轮字母裁决=not_criterion_"
         "dominated 维持不变（=边界操作化未收敛个体散、判据内容非主因的描述"
         "性边界结论、非因果证明；单轮 development 域方向性证据；主通道归因"
         "三支判据与 APR-0011 门分开表述、互不凌驾：门联合评价（代表配置）="
         "not_met 如实分列）；不得回溯改判既往轮次（r8–r24 字母裁决维持不变、"
         "r22=regressed/r23=confounded/r24=not_instance_dominated 维持）；"
         "早期轮字母与实验账分列先例（r18：reject 但排序居首；r19：marginal "
         "但排序居首；r20：reject 但降幅命中；r22：regressed 但 M1 带内复制；"
         "r23：confounded 但条款对目标起效；r24：not_instance_dominated 但 "
         "M1 降幅命中+入排序居第二；r25：not_criterion_dominated 但 M1 降幅"
         "命中+入排序居首）延续——多账分列不合并。"),
        ("通道归因方法：照抄 run-r15–run-r25 channel_attribution 的重放口径"
         "（deviation_note 承接），R16/R19/R20/R22/R23/R24/R25 均以内嵌输入"
         "确定性重放并与 compare_v3 对拍（run-r25 channel_attribution."
         "method）；重放复现与在案登记一致（fail-closed）；几何门 r25=0/"
         "类别门 r25=1/视角门 r25=0 如实计数、不构成字母裁决输入以外的门。"),
        ("读者实例行为与派发操作披露如实记录：R25 二十四派次 v1.2 规约自述合规"
         "（纯 Read 直读、24/24 派次自述「未读取盘上任何其他文件」[逐派次句子"
         "程序提取在案 run-r25 reader_tool_evidence]）；输出格式披露（24 件缩"
         "进格式冻结原始判读件、零改动直读）parse 校验全部通过；flag_id 编号"
         "行为=11/11 有旗实例全部同实例跨板连续+2 格零旗标[bottom-i1 两板"
         "合法零旗输出、理由在其 reading_notes 在案]（与 prep-record naming "
         "声明相符）；R25T/R25B 前缀=指引 §6 落盘固化（r23 基座机械派生新件、"
         "s70/s80 先例同型）；本轮无派发操作事故。跨轮实例不同+轮内实例差异="
         "个体散的测量对象（实例群重抽=轮际固有混杂、非实验操作）；本轮轮前"
         "评审=pre_round_review 在案（r25-prep-record）。"),
    ]

    next_iteration_targets = [
        ("三轴实验总收束位登记：comparison_rule 排序（r25_this_round 第一、"
         "r19_axis3 第二、r24 第三、r18 第四、r16 参照行第五、r17 末位）；"
         "r20/r22/r23 不入排序（资格门剔除、行仅如实入账）；三轴实验最终"
         "结论维持=收益最大配置=轴3 单变量（guidance-r19，M1=0.461538 历史"
         "最佳、contact 族 10→4、黑点族 13→4；按冻结 iv_final_selection 全"
         "部已测配置中排序最优者）；guidance-r19 胜出记录维持 conditional/"
         "double-entry 现状、复制未达成不升级（r25=判据内容轴轮、非三判据"
         "轴重开[判据内容零修改、仅边界显式化]；r25 M1 最低与实例群重抽"
         "混同、不构成配置效应证据）。"),
        ("下一候选建议（如实单列，供主审/用户决策；本包不预写决策）："
         "(a) 接受发展域现状收束训练环（不再追加迭代轮），留出集时机由用户"
         "判断（HOLDOUT-PLAN.md a4b80193 Tier 1/2 候选清单零接触在案；正式"
         "采纳门槛=连续 2 轮达标+人工批准未达成、不得写成已达成）；"
         "(b) 其他输出侧因素操作化归因轮（归因链三轴[框宽/实例群/判据内容]"
         "排除完毕后的残余归因位=唯一剩余方向；须新 prep-record 先于盲读"
         "冻结；不新造第四轴名称、只描述方向）；(c) 再一轮同指引重复轮"
         "（第三样本；r16/r22 先例同型、r25 指引字节复用路径）或收束训练环；"
         "三选项均由用户拍板。"),
        ("归因链收口登记（三混杂轴归因链的收口）：r23 框宽排除（confounded）"
         "→r24 实例群排除（not_instance_dominated）→r25 判据内容排除"
         "（not_criterion_dominated）——三轴全部排除完毕、残余=其他输出侧/"
         "模型侧固有=如实登记（不新造第四轴名称、只描述）；split-half 反转"
         "（r24=0.018640 聚合稳→r25=0.260377 聚合移动）=条款改变聚合行为的"
         "机制观察、单列不进分支；不得事后改判 r25/r24 或既往轮次。"),
        ("留出集时机=开发线收敛（须用户拍板）：r25 字母=not_criterion_"
         "dominated→收敛未宣告、连续=0（正式采纳门槛=连续 2 轮达标+人工批"
         "准未达成，不得写成已达成）；GT 侧维持全关闭声明延续（gt-audit-r1"
         "[1f20554a…]三候选全部关闭，r9–r24 延续零改动；GT 13 条全部 side="
         "top、bottom 零匹配属结构性；r25 union=1/13[R5U6 单实例命中]、"
         "agreement=0=轮际不稳定如实登记、非新 GT）；in_calibrated_range 恒 "
         "False 直到正式采纳（须人工批准）；达标证据仍须留出集（out/v3-tl2/"
         "holdout/HOLDOUT-PLAN.md a4b80193… 与 datasets/holdout-candidates-r1 "
         "在案）。"),
        ("判读侧残余问题登记：top 弃权 36 条接触性 5/存在性 20/其他 11（机械"
         "主出口分类、逐旗入账）；黑点族弃权 22 条（低于 r24 的 28、高于 "
         "r19/r22/r23 三基线）；本轮零旗格=2 格（bottom-i1 两板合法零旗"
         "输出）；reroute 类 6 旗（弃权 4+非弃权 2、滥用型通道机械命中=4"
         "[top-i1 两板弃权旗候选解释逐条列举中的蛇形/等长候选+top-i4 两板"
         "非弃权旗字面；对照 r24 的 6 旗零命中]）；类别门 r25=1 条（对照 "
         "r19=2、r20=0、r22=4、r23=1、r24=6，逐条在案）."),
    ]

    round_identity_declaration = {
        "changed_variables": 1,
        "changed_variables_note": ("唯一实验变量=判读指引 §4 末尾弃权边界"
                                   "操作化条款（prep-record.changed_variables"
                                   " 长度=1 实测核对一致；判据内容轴=须指引"
                                   "文本变更的轴[r24-prep-record "
                                   "single_variable_rationale 预登记留待"
                                   "后续预注册轮——本轮即该后续轮]；非判据"
                                   "调参轴重开：axis-experiment-plan-r17-"
                                   "r20 三轴收束决议与轴停止决议不变、§4 "
                                   "原文与任何量化判据零修改）；渲染/GT/阈值/"
                                   "协议正文零变更"),
        "guidance_reuse": {
            "base": "observation-guidance-r23.md",
            "base_sha256_prefix": "866b0157",
            "byte_delta": 937,
            "derived": "observation-guidance-r25.md（机械变换派生落盘新件）",
            "derived_sha256_prefix": "86af24dd",
            "mode": "mechanical_transform_derive",
            "sole_variable": ("§4 末尾弃权边界操作化条款（§5 标题行之前"
                              "插入、逐字冻结；随变更的机械变换同步项=轮次"
                              "身份四处更新+变更声明节整体重写+§6 示例旗 ID "
                              "前缀机械替换 R23T-→R25T-（4 处）/R23B-→"
                              "R25B-（1 处）/reader-r23-→reader-r25-（1 处）"
                              "）"),
            "transform_base_untouched": True,
        },
        "precedent": ("s70「r15 指引机械变换派生 r19 指引」/s80「r19→r23」"
                      "先例同型——与 r16/r22/r24「指引字节复用+派发层前缀"
                      "覆盖」路径不同（本轮=落盘固化路径：§6 示例前缀已在"
                      "件、派发层命名与指引一致、无前缀差异登记需求）"),
        "round_nature": "判据内容轴归因轮（§4 末尾弃权边界操作化条款轮；"
                        "第二十五轮）",
        "section6_prefix_override": (
            "§6 前缀=落盘固化登记：本轮指引=observation-guidance-r25.md"
            "（86af24dd）为 r23 基座 866b0157 机械变换派生新件，其 §6 示例"
            "旗 ID 前缀 R25T-（恰 4 处）/R25B-（恰 1 处）/reader-r25-（恰 "
            "1 处）已在件（程序计数断言在案）；派发指令命名与指引一致=无"
            "前缀差异登记需求（对照 r22/r24：指引字节复用+派发层覆盖=前缀"
            "差异登记在案）"),
        "sole_variable": ("§4 末尾弃权边界操作化条款（三问依次自问的执行"
                          "细则：不能定位→不设旗；均不能归入 §2 封闭集→"
                          "other_advisory+弃权；两条以上实质不同候选解释且"
                          "均无独有可辨特征→弃权；否则必须设非弃权旗、"
                          "confidence 如实取低值——把握不足本身不构成弃权"
                          "理由；三问之外的任何理由不构成弃权依据、三问顺序"
                          "不得颠倒；§4 反放宽条款原文不变）"),
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
            "343a6747）；r24 为 r23 之后的时序下一轮（r24 跳号声明在案 "
            "round24-dev-record=1a344edf）；r25 为 r24 之后的时序下一轮、"
            "与该 R21 全组合位无涉（非其执行、非其替代）——轮次号跳号以免"
            "台账歧义"),
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
            ("R24→R25 派发与旗标量对照：盲读派次 24→24（n=6 口径与 r24 完全"
             "同构=4 格×6 实例=12 个 reader 智能体各包同侧两板、两波次串"
             "行；实例群全量重抽=轮际固有混杂）；旗标 131（r24）→107（十二"
             "实例旗数 top 10/15/28/17/6/7、bottom 0/4/6/4/6/4；非弃权 49+"
             "弃权 58）；全旗标合计弃权率 0.580153（76/131，r24 附记口径）→"
             "0.542056（58/107，附记口径）；预注册主通道归因三支判据：(ncd) "
             "G1 维持且 M4(n=6)≥0.261904⇒not_criterion_dominated（唯一正式"
             "裁决）；criterion_dominated/guard_interrupted 两支不命中如实"
             "分列；代表配置（top-i1+bottom-i4；bottom tie 按实例编号先序）"
             "弃权率 0.45（9/20，r24）→0.5（7/14，r25）。"),
            ("视角层三分列（measurement_design item 2，n=6 中位数=第 3/4 "
             "序位均值）：top 六实例弃权率 0.3/0.466667/0.285714/0.647059/"
             "1.0/0.142857（r25，逐实例两板合计口径极差 0.857143；top-i5 "
             "全弃权 vs top-i6 低谷=个体散跨越值域）——聚合落点 27/35="
             "0.771429（r16 基线）→18/39=0.461538（r19）→14/22=0.636364"
             "（r20）→16/41=0.390244（r22）→16/33=0.484848（r23）→58/105="
             "0.552381（r24）→36/83=0.433735（r25；较 r16 基线降 0.337694="
             "显著收益定义描述层命中，须与分母效应并读；较 r24 降 0.118646="
             "M1 降[机制观察单列、不构成 criterion_dominated 证据]；本轮唯"
             "一实验变量=判据内容条款）；bottom 六实例=None/1.0/0.666667/"
             "1.0/1.0/1.0（bottom-i1=零旗格 None[合法零旗输出]，可计算实例"
             "极差 0.333333）——bottom 全旗聚合弃权率 12/14=0.857143（r16）"
             "→4/7=0.571429（r19）→4/14=0.285714（r20）→2/10=0.2（r22）→"
             "8/14=0.571429（r23）→18/26=0.692308（r24）→22/24=0.916667"
             "（r25；M2 升=机制观察单列）；M4(n=6) 12 格口径极差=1.0、"
             "split_half=0.260377（聚合亦移动[与 r24 反转]、机制观察单列）"
             "不进字母。"),
            ("matches 与 GT 双口径（measurement_design item 3，n=6 推广）："
             "r22 union=agreement=1/13（≥2/3 双实例一致命中=agreement 首次"
             "计入）→r23 union=2/13、agreement=0→r24 union=agreement=1/13"
             "（L1SHORT 四实例一致命中=agreement≥4/6 v1.3 语义首次计入）→"
             "r25 union=1/13=0.076923（GT-REVC-AP-1-R5U6 由 applied-top-i4 "
             "R25T-005 单实例命中[courtyard 类非弃权贴近报告]）、agreement="
             "0/13（1/6<4/6 不计入）——单/双实例命中的轮际不稳定如实登记；"
             "代表配置 gt_recall_total 0.0（0/13）、seed_match_rate 0.0（0/"
             "7，诊断口径，禁称 precision/FPR）——轮内唯一命中落在非代表"
             "实例=代表配置对实例异质性的敏感性如实登记；bottom 非弃权旗零"
             "匹配属结构性（GT 13 条全部 side=top、bottom 无 GT 在案 "
             "gt-audit-r1）。"),
            ("通道归因（vs R19/R20/R22/R23/R24，预注册重放方法）：几何门面积"
             "比出局 0→0→2→1→0→0（R19=0→R20=0→R22=2→R23=1→R24=0→R25=0="
             "清零维持=资格门满足）；类别门 2（r19）→0（r20）→4（r22）→1"
             "（r23）→6（r24）→1（r25=prep1/top-i1 R25T-009 silk×R4J3，逐"
             "条在案）；视角门 0→0→1→0→0→0。通道链自 r6：几何门 r6=1→r7="
             "0→r8=0→r9=0→r10=0→r11=0→r12=0→r13=0→r14=1→r15=0→r16=0→r17="
             "0→r18=0→r19=0→r20=0→r22=2→r23=1→r24=0→r25=0。重放与 "
             "compare_v3 对拍一致。"),
            ("预注册假设（r24-not-instance-dominated-criterion-boundary-"
             "operationalization-attribution）归因三支判据字母裁决=not_"
             "criterion_dominated（唯一正式裁决）：落支=(ncd) not_criterion_"
             "dominated_m4_exceeds（per r25-prep-record hypothesis_test."
             "adjudication 原文：G1 维持且 M4(n=6)≥0.261904→边界操作化未"
             "收敛个体散=判据内容非主因；残余归因=其他输出侧/模型侧固有）；"
             "实测：R25 五键=(0.433735, 0.916667, 22, 1.0, 0.260377)（M1="
             "top 全旗聚合弃权率 36/83、M2=bottom 22/24、M3=黑点族弃权旗数 "
             "22、M4=12 格极差 1.0、split_half=0.260377[机制观察单列]）；"
             "比较集 live 复算 r16 (0.771429, 0.857143, 12, 0.261904)/r19 "
             "(0.461538, 0.571429, 4, 0.211111)/r22 (0.390244, 0.2, 4, "
             "0.104545)/r23 (0.484848, 0.571429, 8, 0.520833)/r24 (0.552381,"
             " 0.692308, 28, 0.888889)→M4 6 位定点 1000000≥261904=超出——"
             "not_criterion_dominated 支命中（M4 条件）；criterion_dominated "
             "支不命中=弃权边界显式化未使个体散收敛；G1=六 bottom 实例 "
             "courtyard 非弃权全 0 维持（三支字母口径恰一支命中）；G2 出局"
             "条目 R19=0→R22=2→R23=1→R24=0→R25=0（观察项非字母支）。"),
            ("机制观察单列（不凌驾）：(a) 逐实例率分布——top 六实例个体散跨"
             "越值域（1.0 vs 0.142857；条款操作化后未收敛=判据内容非主因的"
             "逐实例层佐证）、bottom 含零旗格 None；(b) split-half 分解——"
             "0.260377>0.09064（A=18/53 vs B=18/30）=聚合亦移动[与 r24 的 "
             "0.018640 反转=条款改变聚合行为、机制观察如实登记]；(c) M1 降/"
             "M2 升分解——M1 降 0.118646/M2 升 0.224359（两向均不进字母、"
             "APR-0011 门指标照常分列）；(d) 条款行为观察——三问援引率 22/24、"
             "弃权边界条款 notes 级 24/24、弃权理由候选解释列举率 58/58=条款"
             "三问之(3) 直接行为观测；(e) G2 链连续清零（0→2→1→0→0=资格门"
             "满足=r25 入排序）+类别门 1 条；(f) 援引分记（多条款分开记、互"
             "不合并）：旗级 §5B=0/(iii-a)=11/分支(=0/弃权边界条款=16+三问="
             "13（11 旗逐旗摘录在案 run-r25）；notes 级 §5B=0/24、(iii-a)="
             "12/24（对照 r19 10/12、r22 6/12、r23 4/12、r24 8/24）、§6=9/"
             "24（对照 r23 6/12、r24 20/24）；(g) rubric 族计数 contact 3/"
             "existence_blackdot 22/existence_other 20+other 13（r13–r16 "
             "132 条重放对拍逐一相等后套用 r25，链值 8/15/5/10 在案）——"
             "黑点 22 低于 r24 的 28、other=n=6 口径新高；(h) top 弃权构成"
             "分型=接触性 5+存在性 20+其他 11（36 条机械主出口分类逐旗入案；"
             "对照 r24 26/30/2）；(i) reroute 被动追踪=6 旗（弃权 4+非弃权 "
             "2）、滥用型通道机械命中=4。"),
            ("bottom 通道单列（M2=22/24=0.916667 vs r16 基线 12/14=0.857143 "
             "vs r19 4/7=0.571429 vs r20 4/14=0.285714 vs r22 2/10=0.2 vs "
             "r23 8/14=0.571429 vs r24 18/26=0.692308；较 r16 与 r19–r24 "
             "全部上升=M2 升[机制观察单列、不影响字母]）：bottom 弃权旗 22 "
             "条（i2/i4/i5/i6 全弃权+i3 部分弃权）；bottom 非弃权 2 条"
             "（bottom-i3 两板）；bottom-i1=零旗格（两板 flags=0=合法零旗"
             "输出、弃权率=None 口径触发=不编造数值）；bottom courtyard 类"
             "旗标=0（G1 维持的直接构成）。"),
            ("工具行为与派发操作（协议侧 v1.2 沿用+v1.3 n=6 附录沿用 r24，"
             "如实入账）：R25 二十四派次全部以 Read 工具直读内嵌图像、24/24 "
             "派次 reading_notes 自述「未读取盘上任何其他文件」（逐派次句子"
             "程序提取在案）；全部判读输入严格限于（指引+该 PNG），零 GT/零"
             "诊断/零 legend/零 r23/r24 现象描述注入=非盲读违规；flag_id "
             "编号行为=11/11 有旗实例全部同实例跨板连续+2 格零旗标（与 "
             "prep-record naming 声明相符）；R25T/R25B 前缀=指引 §6 落盘"
             "固化（s70/s80 机械派生先例同型）；本轮无派发操作事故；跨实例/"
             "跨视角禁止交流（24 次盲读相互独立）。"),
            ("courtyard 被动追踪与 reroute 被动追踪（run-record 链先例延"
             "续，零阈值改动零期望）：courtyard 类旗标 13 条（top 弃权 7"
             "[top-i2 两板 2+top-i3 两板 2+top-i4 3]+top 非弃权 6[top-i1 "
             "两板 4+top-i4 两板 2 贴近报告]；bottom 0）——非弃权 courtyard "
             "命中链 r16=1→r17=0→r18=0→r19=0→r20=0→r22=0→r23=1→r24=0→"
             "r25=1（applied-top-i4 R25T-005↔GT-REVC-AP-1-R5U6）；reroute "
             "类 6 条（弃权 4+非弃权 2[负责任报告]；滥用型通道机械命中=4）；"
             "产量链 r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1→r15=4→r16=2"
             "→r17=1→r18=3→r19=3→r20=2→r22=4→r23=2→r24=6→r25=6。"),
        ],
        "domain_basis_quote": run["evaluation_domain_note"]["basis_quote"] +
        "本件=R25 收口包 B（dev-record 分包）：development 域第 25 轮迭代"
        "（判据内容轴归因轮）的轮次开发记录；迭代轮不得冒充留出证据。",
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
            "after_r12": dict(dev24["joint_evaluation_trend"]["after_r12"]),
            "aggregation_scope_note": (
                "r5–r10 行=各轮 run-record 全旗标聚合（单实例/轮口径在案）；"
                "r11–r25 行=代表配置口径（measurement_design item 4）——两口"
                "径并列如实、不混同（r25 全旗标合计 58/107=0.542056 仅作附"
                "记）"),
            "by_round": trend_rows,
            "consecutive_met_count_now": 0,
            "note": ("连续达标计数变动：0（R24 后）→0（本轮）；正式采纳门槛"
                     "（连续 2 轮达标+人工批准）未达成，不得写成已达成"),
            "this_round": {
                "joint_evaluation": comp["joint_evaluation"],
                "note": ("本轮联合评价（代表配置）not_met（gt_recall 0.0 "
                         "与 seed_match_rate 0.0 两项未达暂行线；gt_count "
                         "13≥12 与 abstain_rate 0.5≤0.5 单分项入线）——"
                         "GT 条目层 union=1/13 亦未达 0.75（双口径与门分列"
                         "如实；r22/r24 agreement 里程碑在案）"),
            },
        },
        "kind": KIND,
        "mechanism_observation_r25": mechanism_observation_r25,
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
            "新预注册轮归因；g2_bifurcation_record 延续在案）→"
            "round24-dev-record.json（1a344edf…，r24 收束+next_candidate_"
            "suggestion 选项(b)「判据内容轴归因预注册轮」=本轮设计出处与"
            "合法性依据；r24 字母=not_instance_dominated 维持不改写；"
            "g2_bifurcation_record 延续在案）→r25-prep-record.json（"
            "0943a8ec…，本轮预注册件，measurement_design 五条[n=6 口径与 "
            "r24 完全同构]聚合口径与 hypothesis_test.adjudication 归因三支"
            "判据（criterion_dominated=G1 维持且 M4(n=6)<0.261904/"
            "not_criterion_dominated=G1 维持且 M4(n=6)≥0.261904/"
            "guard_interrupted=G1 破坏；split_half=机制观察单列）先于盲读"
            "冻结；changed_variables 长度=1；no_instrument_change=true；"
            "guidance=observation-guidance-r25.md=observation-guidance-"
            "r23.md 866b0157 机械变换派生落盘新件[86af24dd、byte delta=+937]"
            "）→判读指引=observation-guidance-r25.md（86af24dd…，本轮唯一"
            "判读依据；§6 示例前缀 R25T-/R25B- 落盘固化）→渲染零变更"
            "（renders-r14b 四图字节复用、与 r14–r24 盲读同一批文件[applied-"
            "top 298bc620/applied-bottom d7284259/prep1-top b2f84524/"
            "prep1-bottom d7284259；witness-r14b b63771f9 在案]）→24 次盲读"
            "[11/11 有旗实例同实例跨板连续+2 格零旗标=bottom-i1 两板合法零旗"
            "输出、无派发事故；24 件哈希全 64 位锚在案 run.reader.raw_files/"
            "本件 flag_production.raw_files]→run-r25（251102e8…，本链执行"
            "落盘；run_r24=8a9bdb7d 在案=比较集 r24 行 live 复算输入与台账"
            "继承源）；GT 重投影沿用 derivation-log-r5.json（62343380…）零新"
            "派生（GT 全部 side=top；渲染零变更=GT 重投影输入未变）；GT 冻结"
            "纪律：轮后未增删改；gt-audit-r1（1f20554a…）结论维持 GT 零改动"
            "（三候选关闭，gt_audit_reference 在案）"),
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
            "development 域判据内容轴归因轮（第二十五轮；三混杂轴归因链第三"
            "轴执行轮：r23 框宽排除→r24 实例群排除→r25 判据内容）：唯一实验"
            "变量=判读指引 §4 末尾弃权边界操作化条款（observation-guidance-"
            "r25.md=observation-guidance-r23.md 866b0157 机械变换派生落盘"
            "新件[86af24dd、byte delta=+937；§4 原文与任何量化判据零修改、"
            "仅边界显式化——s70/s80 先例同型]）+渲染零变更="
            "renders-r14b 四图字节复用（与 r14–r24 盲读同一批文件；"
            "no_instrument_change=true[run 侧 instrument_change.changed="
            "False=仪器未变、判据内容=指引侧变量]）+GT 集/协议阈值与度量"
            "版本/比较器常量零改动（GT 重投影沿用 derivation-log-r5——零新"
            "派生；gt-audit-r1 三候选关闭结论延续）；协议=v1/v1.1/v1.2 继承"
            "不改+v1.3 n=6 附录沿用 r24（本轮无新增附录；union≥1/6、"
            "agreement≥4/6、代表配置=下中位序位实例的 n=6 推广=附录显式"
            "冻结、不得事后收放；n=6 口径与 r24 完全同构、实例群重抽=轮际"
            "固有混杂非实验操作）；changed_variables=1；【跳号声明延续】r21 "
            "号段=axis-experiment-plan-r17-r20（b6ec6467 冻结件）预留的 R21 "
            "全组合条件位（early_stop_rule.strong_single_axis_shortcut 未"
            "触发、槽位永久留空；dev-r20 已登记「R21 不做」；r22/r23/r24 "
            "跳号声明在案；r25 与该位无涉）；执行 round24-dev-record 下一"
            "候选建议选项(b)（判据内容轴归因预注册轮）+用户 2026-09-10 拍板"
            "选项(b)定向判据内容轴；检验假设 r24-not-instance-dominated-"
            "criterion-boundary-operationalization-attribution（判据="
            "r25-prep-record.json hypothesis_test.adjudication 归因三支判据，"
            "轮后如实执行：字母裁决唯一正式+机制观察/度量教训单列+条款行为"
            "观察单列+G2 分岔记录延续；主通道归因三支判据与 APR-0011 门"
            "（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）与 "
            "CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独立计算、互不凌驾、"
            "分开表述；measurement_design 聚合口径先于盲读冻结）；跨轮收益"
            "比较按 axis-plan 冻结规则（r25 行见 axis_experiment_ledger 九行"
            "并列：r25 入排序居首、r20/r22/r23 资格门剔除；guidance-r19 "
            "胜出记录维持 conditional/double-entry 现状）；按协议 v1 §4，"
            "迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "r21_skip_declaration": r21_skip_declaration,
        "run_record_ref": {"path_rel": REL_RUN_R25, "sha256": run25_sha},
        "schema_version": SCHEMA_VERSION,
        "three_axis_experiment_closeout": three_axis_experiment_closeout,
    }


def main() -> None:
    verify_protected_files()  # 开工锚
    dev = build_dev_record()
    dev_bytes = hashing.canonical_json_bytes(dev)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, dev_bytes, REL_OUT)
    print(f"[s90-cal-r25-devrecord] round25-dev-record: {status}")
    print(f"[s90-cal-r25-devrecord] hypothesis "
          f"({dev['hypothesis_test_i']['hypothesis_id']}): "
          f"verdict={dev['hypothesis_test_i']['verdict']} "
          f"letter_branch=(ncd) not_criterion_dominated_m4_exceeds（G1 维持"
          f"且 M4(n=6)=1.0≥0.261904）")
    print(f"[s90-cal-r25-devrecord] 归因三支判据: (cd) criterion_dominated="
          f"M4 内=不命中（M4 超出）；(ncd) not_criterion_dominated=M4 条件"
          f"超出（1000000≥261904；split_half=260377>90640=聚合亦移动、机制"
          f"观察单列不进分支）=命中⇒ not_criterion_dominated（唯一正式裁决）；"
          f"(gi) guard_interrupted 未命中；G1=六 bottom 实例 courtyard 非弃"
          f"权全 0 维持")
    print(f"[s90-cal-r25-devrecord] 归因结论（单列）: 边界操作化未收敛个体散="
          f"判据内容非主因（残余归因=其他输出侧/模型侧固有；归因链三轴[框宽/"
          f"实例群/判据内容]全部排除完毕、不新造第四轴名称只描述）；split-half "
          f"聚合亦移动（0.260377>0.09064、与 r24 的 0.018640 反转=条款改变"
          f"聚合行为）；M1 降 0.118646/M2 升 0.224359 分解单列；r24 字母="
          f"not_instance_dominated、r23 字母=confounded、r22 字母=regressed "
          f"维持不改写")
    print(f"[s90-cal-r25-devrecord] 条款行为观察: 三问援引率 22/24（notes 级）、"
          f"弃权边界条款 24/24、弃权理由候选解释列举率 58/58 弃权旗"
          f"（条款三问之(3) 直接行为观测）")
    print(f"[s90-cal-r25-devrecord] 机制观察: 三族 rubric 计数 contact 3/"
          f"黑点 22/存在性其他 20+other 13（对照 r19 4/4/14、r22 2/4/12、"
          f"r23 8/8/7、r24 4/28/44）；援引旗级 §5B=0/(iii-a)=11/分支(=0/"
          f"条款=16+三问=13、notes 级 §5B=0/24+(iii-a)=12/24+§6=9/24+条款="
          f"24/24；G2 链 0→2→1→0→0 清零维持=资格门满足（r25 入排序居首）；"
          f"类别门 1 条；零旗格=2 格[bottom-i1 两板合法零旗输出]")
    print(f"[s90-cal-r25-devrecord] GT: union=1/13=0.076923（GT-REVC-AP-1-"
          f"R5U6 由 applied-top-i4 R25T-005 单实例命中）、agreement=0/13"
          f"（1/6<4/6 不计入）；通道门 几何 0/类别 1/视角 0（对照 r19 0/2/0、"
          f"r20 0/0/0、r22 2/4/1、r23 1/1/0、r24 0/6/0）")
    print(f"[s90-cal-r25-devrecord] 台账与排序: 九行并列（r16/r17/r18/r19/"
          f"r20/r22/r23/r24/r25）；r25 入排序居首（G1/G2 满足）；排序=r25 "
          f"第一、r19 第二、r24 第三、r18 第四、r16 参照、r17 末位；显著收益 "
          f"0.337694≥0.10 描述层命中（与分母效应及实例群重抽混同如实声明）")
    print(f"[s90-cal-r25-devrecord] 下一候选建议（三选项、由用户拍板）: "
          f"(a) 接受发展域现状收束训练环+留出集时机用户判断；(b) 其他输出侧"
          f"因素操作化归因轮（残余归因位）；(c) 同指引重复轮第三样本或收束"
          f"训练环")
    print(f"[s90-cal-r25-devrecord] run_record_ref: "
          f"{dev['run_record_ref']['path_rel']} sha256[:8]="
          f"{dev['run_record_ref']['sha256'][:8]}")
    print(f"[s90-cal-r25-devrecord] joint(代表配置)="
          f"{dev['diagnostic_result']['joint_evaluation']} "
          f"abstain_rate_total={dev['diagnostic_result'][
              'abstain_rate_total']} 连续达标=0 in_calibrated_range=恒 False")
    print(f"[s90-cal-r25-devrecord] sha256 {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))}")
    print(f"[s90-cal-r25-devrecord] sha256[:8] {Path(REL_OUT).name} = "
          f"{hashing.sha256_file(str(out_path))[:8]}")
    verify_protected_files()  # 收工锚
    print("[s90-cal-r25-devrecord] R25 dev-record 落盘完成（development 域；"
          "不是门；字母裁决=not_criterion_dominated 唯一正式（not_criterion_"
          "dominated_m4_exceeds 支=G1 维持且 M4 条件超出；残余归因=其他输出"
          "侧/模型侧固有）；split-half 聚合移动/条款行为观察/M1 降 M2 升分解/"
          "G2 链闭合/度量教训单列不凌驾；r22=regressed、r23=confounded、"
          "r24=not_instance_dominated 维持不改写；in_calibrated_range 恒 "
          "False）")


if __name__ == "__main__":
    main()
