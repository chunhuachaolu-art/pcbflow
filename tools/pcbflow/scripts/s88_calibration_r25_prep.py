#!/usr/bin/env python
"""CAL-R25-PREP：R25 判据内容轴归因轮（§4 末尾弃权边界操作化条款）预备
包（只新建两个文件：out/v3-tl2/calibration/observation-guidance-r25.md 与
out/v3-tl2/calibration/r25-prep-record.json——本轮仅有的两个 out/ 新产物；
datasets/ 与 out/ 既有文件只读、零改动，observation-guidance-r23.md 只读
零字节不动）。

R25 轮性质（预注册，非事后）：**判据内容轴归因轮（§4 末尾弃权边界操作
化条款轮；非判据调参轴重开——axis-experiment-plan-r17-r20 三轴实验收束
决议与轴停止决议不变；r24 not_instance_dominated 登记的下一归因轴执行
轮）**。归因链（三混杂轴）：r23 框宽排除（confounded，round23-dev-record
343a6747 在案）→r24 实例群排除（not_instance_dominated，run-r24=8a9bdb7d
/round24-dev-record=1a344edf 在案）→r25 判据内容（本轮）。r24 实测「聚合
稳[拆半 0.018640≤0.09064]与个体散[极差 0.888889、双峰结构]并存」=弃权边
界欠操作化假说的直接可测推论（边界显式化后若个体散收敛→判据内容主导）。
本轮唯一实验变量=判读指引 §4 末尾增补「弃权边界操作化条款」（判据内容
轴）；指引机械派生自 r23 基座（866b0157 全 64 位实测锚；s48/s54/s63/s67/
s70/s80 机械变换先例）；渲染/GT/阈值/n=6 协议全部维持 r24 冻结态。

指引机械派生（锚串命中数 fail-closed：锚恰 N 次否则 FAIL），任务枚举：
  (1) 标题行替换（轮次身份四处之一）；
  (2) round_id_constant bullet 2026-09-10-r23→2026-09-10-r25（之二）；
  (3) 声明日期 bullet 2026-09-10→2026-09-10（基座日期已是 2026-09-10，本
      任务=确认无操作 no-op，如实登记）（之三）；
  (4) 「本轮性质行」按判据内容轴口径重写（之四）；
  (5) 「本轮变更声明」节正文整体替换【任务枚举 8 项之外的必要补入项，偏
      差如实登记】：冻结区断言要求小写 r23 仅存「相对 observation-guidance
      -r23」恰 1 处+R23 系 token 残留=0，而基座变更声明节含 r19 血统引用
      与 R23T/R23B/reader-r23/r23-prep-record token——不整体重写则断言不
      可满足；s80 任务 5「变更声明节正文整体替换（任务给定文本逐字）」先
      例同型；
  (6) §4 末尾增补弃权边界操作化条款（在 §5 标题行之前插入；逐字）（之五）；
  (7) §6 示例旗 ID 前缀机械替换 R23T-→R25T-（恰 4 处）（之六）；
  (8) §6 示例旗 ID 前缀机械替换 R23B-→R25B-（恰 1 处）（之七）；
  (9) §6 示例 reader_id 前缀机械替换 reader-r23-→reader-r25-（恰 1 处）
      （之八）。
冻结区断言（逐字）：§2、§3（含 §3A）、§5（含 §5A）、§6 正文、§7 与基座
逐字一致（substring 区块断言；§6=基座 §6+前缀机械替换的区块等价复核）；
§4=基座 §4 原文完整保留+仅末尾追加该条款（区块等价断言）；反放宽句「仅
因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」恰 1 次；
R23 系 token（R23T/R23B/reader-r23 及一切大写 R23）残留=0（替换后；小写
r23 仅存变更声明基座血统引用「相对 observation-guidance-r23」恰 1 处——
r23 文件内保留 r19 引用同口径先例）；新增条款文本在产物中逐字在案；指引
内零轮次结果数字（r24 实测数字残留=0）。

预注册三支裁决（hypothesis_test.adjudication 逐字冻结，先于盲读；字母唯
一正式裁决；全部阈值比较=6 位定点整数交叉相乘、零浮点除法）：
  criterion_dominated：G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）
    且 M4(n=6) < 0.261904（锚=r16 基线 M4，axis-plan baselines_registered.
    r16_baseline + run-r24 baseline_cross_check 交叉核对）→ 弃权边界显式
    化收敛个体散=判据内容为个体散主因；
  not_criterion_dominated：G1 维持 且 M4(n=6) ≥ 0.261904 → 边界操作化未
    收敛个体散=判据内容非主因（残余归因=其他输出侧/模型侧固有；归因链
    如实登记）；
  guard_interrupted：G1 破坏 → 字母=guard_interrupted（归因悬置、机制观
    察照常、g1 分岔先例引用）。
本轮分支判据=M4(n=6) 单判据（split_half_M1_diff=机制观察单列、不进分支
判定——与 r24 双判据分支的差异如实登记：实例群轴已由 r24 测毕）。G2=实
测观察项（top 非弃权旗 area_ratio>10 出局条目；G2>0→资格门剔除不入排序；
对照 r19=0/r22=2/r23=1/r24=0）；M1/M2 变动=机制观察+APR-0011 门指标照常
分列（本轮字母只看个体散收敛、不看 M1 降不降——显式防止「为降弃权率而
操作化」的动机误读）。

判据锚（全部实测核对，fail-closed）：
  M4 阈值锚 0.261904=r16 基线 M4（axis-experiment-plan-r17-r20.json=
  b6ec6467 键位 baselines_registered.r16_baseline.M4_top_per_instance_rate
  _range；run-r24 baseline_cross_check 交叉核对）；
  比较集=r16 基线+r19+r22+r23+r24 实测元组（r24=(0.552381,0.692308,28,
  0.888889) 从 run-r24=8a9bdb7d 的 r24_m_tuple_6dp live 装载锚定、不手工
  抄；r19/r22/r23 三源交叉核对）；
  M3 分型件 rubric 词元口径链锚=abstain-typology-r13-r16.json（6dadac8d）
  装载+r13–r16=8/15/5/10 链回放先核对（在件键位=matrix.round_totals.r13–
  r16.families.contact=contact 族，分型件族标签如实登记；黑点族（M3）同
  件交叉锚=r16 existence_blackdot=12 == axis-plan r16_baseline.M3=12——
  规格括号映射与本脚本实测键位的对应关系如实登记，见 measurement_design
  .m_tuple_definitions.m3_rubric_lineage_note）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-10 / 2026-09-10-r25）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径（PNG
仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-* /
reader-raw-* / derivation-log-* / 任何 compare/诊断内容产物；run-r22/
run-r23/run-r24 仅读 hypothesis_test 顶层判据冻结值字段+guard_channel+
verdict+baseline_cross_check（GT 匹配与逐旗明细不读取不入记录）；dev-r24
仅读 axis_experiment_ledger 实测元组/台账行、g2_bifurcation_record 计数/
字母/G1 锚、hypothesis_test_i.verdict、next_candidate_suggestion 选项(b)
原文（GT 字段不转录）；无 git；阈值零修改；r23 指引只读零字节不动；记录
内零 GT、零期望数量/分布/坐标；指引内零轮次结果数字（基线数字仅入本编
排侧记录）；两产物落盘=确定性字节（变换/构造纯函数+同参重建两次逐字节一
致自证）+防覆写护栏（已存在且重建字节不同→FAIL，相同→幂等零覆写）+落
盘后回读验字节；保护三文件（pcbflow/cli.py、pcbflow/config.py、
toolchain_lock.json）开工/收工各验一次全 64 位 sha256。

用法：python scripts/s88_calibration_r25_prep.py
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
GUIDANCE_R25 = CAL_DIR / "observation-guidance-r25.md"
DEV_RECORD_R22 = CAL_DIR / "round22-dev-record.json"
DEV_RECORD_R23 = CAL_DIR / "round23-dev-record.json"
DEV_RECORD_R24 = CAL_DIR / "round24-dev-record.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
TYPOLOGY = CAL_DIR / "abstain-typology-r13-r16.json"
R23_PREP_RECORD = CAL_DIR / "r23-prep-record.json"
R24_PREP_RECORD = CAL_DIR / "r24-prep-record.json"
RUN_R22 = CAL_DIR / "calibration-run-r22.json"
RUN_R23 = CAL_DIR / "calibration-run-r23.json"
RUN_R24 = CAL_DIR / "calibration-run-r24.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
EVAL_PROTOCOL_V2 = CAL_DIR / "evaluation-protocol-v2.md"
RECORD = CAL_DIR / "r25-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"
CLI_PY = REPO / "pcbflow" / "cli.py"
CONFIG_PY = REPO / "pcbflow" / "config.py"
TOOLCHAIN_LOCK = REPO / "toolchain_lock.json"

DATE_CONSTANT = "2026-09-10"
ROUND_ID = "2026-09-10-r25"
ROUND_LABEL = "r25"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）。指引/渲染/r24 实测/M4 锚/分型件/保护
# 三文件=全 64 位 sha256 断言；其余链锚=前 8 位断言。
# ---------------------------------------------------------------------------
GUIDANCE_R23_SHA = ("866b0157acdf763faf68c18f72b383617a8feaa06a043"
                    "015b36f5d3cf7f50ca7")
DEV_RECORD_R24_SHA = ("1a344edfc4faa0d80d965ba2acd981975f15056a0211dc4c94"
                      "9e9ebb70d8cf1b")
AXIS_PLAN_SHA = ("b6ec646791064a33912354cb02323d64b3d2886ba8e4f73b1f91d93"
                 "596aa25ce")
TYPOLOGY_SHA = ("6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b5328"
                "3681bc80")
RUN_R24_SHA = ("8a9bdb7deba968ee08c8254c2e4f9e42d7ebabae1be3362228f4ef62"
               "d39e5dba")
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
DEV_RECORD_R23_SHA_PREFIX = "343a6747"
R23_PREP_RECORD_SHA_PREFIX = "3c42ace7"
R24_PREP_RECORD_SHA_PREFIX = "760af49f"
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

#: observation-guidance-r23.md 变换基座落盘事实锚（不符即停）
GUIDANCE_R23_BYTES = 23125
GUIDANCE_R23_FACTS = {
    "# R23 轮 reader 判读指引（observation-guidance-r23）": 1,
    "- round_id_constant: `2026-09-10-r23`": 1,
    "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-10": 1,
    "R23T-": 4,
    "R23B-": 1,
    "reader-r23-": 1,
    "## 5. courtyard 说明（中性）": 1,
    "## 2. 类别枚举": 1,
    "## 4. 置信度与弃权": 1,
    "## 6. 输出格式": 1,
    "## 7. 格式对齐提示": 1,
    "## 5B": 0,
    "renders-r14b": 2,
    "(iii-a)": 2,
    "R14": 4,
    "R19": 0,
    "R22": 0,
    "R24": 0,
    "r19": 1,   # 变更声明基座血统引用「相对 observation-guidance-r19」
    "r22": 0,
    "r24": 0,
    "2026-09-09": 0,
}

# ---------------------------------------------------------------------------
# 实测锚常量（=在案实测装载目标；probe 逐一断言，不符即停——防预注册
# 文本与在案事实漂移）
# ---------------------------------------------------------------------------
M_TUPLE_R16 = {"M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}
M_TUPLE_R19 = {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}
M_TUPLE_R22 = {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
M_TUPLE_R23 = {"M1": 0.484848, "M2": 0.571429, "M3": 8, "M4": 0.520833}
#: r24 元组（含拆半）=run-r24 r24_m_tuple_6dp live 装载目标（不手工抄：
#: probe 从盘上 live 装载后逐一断言，再以装载值入比较集）
M_TUPLE_R24_EXPECT = {"M1": 0.552381, "M2": 0.692308, "M3": 28,
                      "M4": 0.888889, "split_half_M1_diff": 0.01864}
M4_ANCHOR = 0.261904          # r16 基线 M4（axis-plan 在案）
M4_ANCHOR_6DP = 261904        # 6 位定点整数
DRIFT_TEXT = "0.09064"        # r15→r16 纯重抽漂移（raw text 在案锚）
DRIFT_6DP = 90640             # 0.09064 的 6 位定点整数
SPLIT_HALF_R24_6DP = 18640    # 0.018640 的 6 位定点整数
TOP_ABSTAIN_R24 = 58
TOP_FLAGS_R24 = 105
G2_R19 = 0
G2_R22 = 2
G2_R23 = 1
G2_R24 = 0
#: 分型件 rubric 口径链锚（abstain-typology-r13-r16.json 在件实测；
#: 8/15/5/10 链的在件键位=matrix.round_totals.r13–r16.families.contact）
TYPOLOGY_CONTACT_CHAIN = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
TYPOLOGY_R16_BLACKDOT = 12    # == axis-plan r16_baseline.M3（M3 口径交叉锚）

#: round24-dev-record 定位标记（fail-closed）
CANDIDATE_B_OPTION = (
    "判据内容轴归因预注册轮（对判据条款语义/门限做单变量操作化归因；须新 "
    "prep-record 先于盲读冻结=预注册纪律；方向=归因结论位登记的下一归因轴）")
CANDIDATE_B_QUOTE = (
    "(b) 判据内容轴归因预注册轮（对判据条款语义/门限做单变量操作化归因；"
    "须新 prep-record 先于盲读冻结=预注册纪律；方向=归因结论位登记的下一"
    "归因轴）")
AGGREGATE_STABLE_QUOTE = "双峰结构+split-half 稳/极差爆拉并存=聚合稳/个体散"

#: 归因三支判据原文（任务给定逐字冻结；json.loads 对拍断言见 main）
ADJ_CRITERION_DOMINATED = (
    "G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）且 M4(n=6) < "
    "0.261904（6 位定点整数交叉相乘比较；锚=r16 基线 M4，axis-plan "
    "baselines_registered.r16_baseline + run-r24 baseline_cross_check 交叉"
    "核对）→ 弃权边界显式化收敛个体散=判据内容为个体散主因")
ADJ_NOT_CRITERION_DOMINATED = (
    "G1 维持 且 M4(n=6) ≥ 0.261904 → 边界操作化未收敛个体散=判据内容非主"
    "因（残余归因=其他输出侧/模型侧固有；归因链如实登记）")
ADJ_GUARD_INTERRUPTED = (
    "G1 破坏 → 字母=guard_interrupted（归因悬置、机制观察照常、g1 分岔先"
    "例引用）")
NO_LOOSENING_SENTENCE = (
    "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由")

DESCRIPTIVE_BOUNDARY_NOTE = (
    "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/"
    "AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结"
    "件 axis-experiment-plan-r17-r20.json 为准")

# ---------------------------------------------------------------------------
# 指引机械变换常量（锚串命中数 fail-closed；s48/s54/s63/s67/s70/s80 先例）
# ---------------------------------------------------------------------------
OLD_TITLE = "# R23 轮 reader 判读指引（observation-guidance-r23）"
NEW_TITLE = "# R25 轮 reader 判读指引（observation-guidance-r25）"

OLD_ROUND_ID_LINE = "- round_id_constant: `2026-09-10-r23`"
NEW_ROUND_ID_LINE = "- round_id_constant: `2026-09-10-r25`"

#: 声明日期 bullet：基座已是 2026-09-10 → 本任务=确认无操作（no-op 如实
#: 登记；old==new）
DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-10"

OLD_NATURE_LINE = (
    "- 本轮性质：**单变量报告框收敛归因轮（输出格式/报告纪律轴；§6 报告"
    "框收敛条款轮；非判据调参轴重开——轴停止决议不变）**。渲染零变更（复"
    "用 R14 冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引 §6 "
    "增补报告框收敛条款（把 `frame_box_pct` 的语义钉住为「该旗所指现象的"
    "物理位置」：必须收窄到现象本体的最小外接——单个文字实例/单个图元/"
    "单组直接相连图元；禁止因描述便利扩大到邻域或整区；同一类现象的多个"
    "离散实例分旗各配小框；旗标产出与弃权判据零变更、弃权旗疑似区域框同"
    "样适用），指引落盘后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**判据内容轴归因轮（§4 末尾弃权边界操作化条款轮；非判据"
    "调参轴重开——axis-experiment-plan-r17-r20 三轴实验收束决议与轴停止决"
    "议不变；r24 not_instance_dominated 登记的下一归因轴执行轮）**。渲染零"
    "变更（复用 R14 冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判"
    "读指引 §4 末尾增补弃权边界操作化条款（把弃权边界操作化为三问依次自"
    "问的处置细则：不能定位→不设旗；不能归入 §2 封闭集→other_advisory+弃"
    "权；两条以上实质不同的候选解释且均无独有可辨特征→弃权；否则必须设"
    "非弃权旗、confidence 如实取低值——把握不足本身不构成弃权理由；§4 反"
    "放宽条款原文不变），指引落盘后由编排侧重新盲读。")

OLD_CHANGES_PARA = (
    "本轮（R23）为单变量报告框收敛归因轮（输出格式/报告纪律轴；非判据调"
    "参轴重开——轴停止决议不变）：相对 observation-guidance-r19 仅（1）"
    "更新标题与轮次标识，（2）重写本变更声明，（3）§6 增补报告框收敛条款"
    "（在「注意：flag 对象没有 side 字段」说明段之后、格式示例小节之前插"
    "入；把 frame_box_pct 的语义钉住为「该旗所指现象的物理位置」——必须"
    "收窄到该旗所指现象本体的最小外接（单个文字实例/单个图元/单组直接相"
    "连图元），禁止因描述便利扩大到邻域或整区；同一类现象含多个离散实例"
    "时按实例拆分、各配小框（flag_id 编号可连续）；条款为报告框几何纪律："
    "旗标产出与否、类别判定、弃权判据与报告义务零变更，弃权旗的疑似区域"
    "框同样适用，反放宽条款逐字保留；§6 其余文本、§2 类别枚举、§3/§3A "
    "位置与判据示例、§4 全文（含量化判据 (i)(ii)(iii)、(iii-a) 可操作分"
    "辨条款、三路出口、反放宽条款原文）、§5 courtyard 说明、§5A 渲染配"
    "色仪器注记、§7 格式对齐提示全部逐字不变），（4）§6 虚构示例旗 ID "
    "前缀机械替换为 R23T/R23B（reader_id 示例前缀同步为 reader-r23）。渲"
    "染零变更：本轮使用与 R14 完全相同的 renders-r14b 四图（字节复用）。"
    "预注册判据见 r23-prep-record.json hypothesis_test（先于任何盲读冻"
    "结）。")
NEW_CHANGES_PARA = (
    "本轮（R25）为判据内容轴归因轮（判据内容轴单变量；非判据调参轴重开—"
    "—axis-experiment-plan-r17-r20 三轴实验收束决议与轴停止决议不变）：相"
    "对 observation-guidance-r23 仅（1）更新标题与轮次标识，（2）重写本变"
    "更声明，（3）§4 末尾增补弃权边界操作化条款（在 §5 标题行之前插入；"
    "对任一候选现象依次自问三问并按答案处置——不能在图中定位并按 §6 框"
    "出→不设旗；不能归入 §2 封闭集类别之一→other_advisory+弃权；涉及两条"
    "以上实质不同的候选解释且各候选在当前分辨率下均无独有可辨特征→弃权"
    "（弃权理由须逐条列出各候选解释）；否则必须设非弃权旗、confidence 如"
    "实取低值——把握不足本身不构成弃权理由；三问之外的任何理由不构成弃权"
    "依据、三问顺序不得颠倒；条款为 §4 反放宽条款的执行细则、反放宽条款原"
    "文不变；§4 全文（含量化判据 (i)(ii)(iii)、(iii-a) 可操作分辨条款、三"
    "路出口、反放宽条款原文）逐字保留），（4）§6 虚构示例旗 ID 前缀机械替换为 "
    "R25T/R25B（reader_id 示例前缀同步为 reader-r25）。渲染零变更：本轮使"
    "用与 R14 完全相同的 renders-r14b 四图（字节复用）。§2 类别枚举、§3/"
    "§3A 位置与判据示例、§5 courtyard 说明、§5A 渲染配色仪器注记、§6 其余"
    "文本、§7 格式对齐提示全部逐字不变。预注册判据见 r25-prep-record.json "
    "hypothesis_test（先于任何盲读冻结）。")

#: §4 末尾增补条款（任务枚举之五；在 §5 标题行之前插入；逐字冻结、不得
#: 改动一字）
CLAUSE_INSERT_ANCHOR = "\n\n## 5. courtyard 说明（中性）"
CLAUSE_TEXT = (
    "**§4(终) 弃权边界操作化条款（r25 唯一新增判据变量）**：对任一候选现"
    "象，判读人须依次自问三问并按答案处置——(1) 现象能否在图中定位并按 "
    "§6 框出？不能定位→不设旗；(2) 现象能否归入 §2 封闭集类别之一？均不"
    "能→other_advisory+弃权；(3) 现象是否涉及两条以上实质不同的候选解释、"
    "且各候选在当前分辨率下均无独有可辨特征？是→弃权（弃权理由须逐条列"
    "出各候选解释）；否→必须设非弃权旗，confidence 如实取低值——把握不足"
    "本身不构成弃权理由（本句为 §4 反放宽条款的执行细则，反放宽条款原文"
    "不变）。三问之外的任何理由不构成弃权依据；三问顺序不得颠倒。")

PREFIX_EDITS = (
    ("R23T-", "R25T-", 4),
    ("R23B-", "R25B-", 1),
    ("reader-r23-", "reader-r25-", 1),
)

#: 区块边界标记
MARK_S2 = "## 2. 类别枚举"
MARK_S4 = "## 4. 置信度与弃权"
MARK_S5 = "## 5. courtyard 说明（中性）"
MARK_S6 = "## 6. 输出格式"
MARK_S7 = "## 7. 格式对齐提示"

#: r25 指引落盘后的一致性断言（任务要求逐项；不符即停）
GUIDANCE_R25_REQUIRED = {
    NEW_TITLE: 1,
    NEW_ROUND_ID_LINE: 1,
    DATE_LINE: 1,
    NEW_NATURE_LINE: 1,
    NEW_CHANGES_PARA: 1,
    CLAUSE_TEXT: 1,
    "R25T-": 4,
    "R25B-": 1,
    "reader-r25-": 1,
    "2026-09-10": 2,  # round_id 行「2026-09-10-r25」+声明日期行各 1 次
    # 新增条款 needle 族（逐字在案断言的细分锚）
    "§4(终) 弃权边界操作化条款": 1,
    "r25 唯一新增判据变量": 1,
    "三问之外的任何理由不构成弃权依据": 2,  # 条款+变更声明各 1
    "三问顺序不得颠倒": 2,  # 条款+变更声明各 1
    "把握不足本身不构成弃权理由": 3,  # 条款+性质行+变更声明各 1
    # 反放宽句恰 1 次（§4 逐字保留的落盘事实）
    NO_LOOSENING_SENTENCE: 1,
    "(iii-a)": 2,
    "renders-r14b": 2,
    "R14": 4,
    "## 5B": 0,
    # R23/R19/R22/R24 系大写 token 残留=0（替换+重写后）
    "R23": 0,
    "R19": 0,
    "R22": 0,
    "R24": 0,
    "2026-09-09": 0,
    # 指引内零轮次结果数字（r24 实测数字残留=0）
    "0.552381": 0,
    "0.692308": 0,
    "0.888889": 0,
    "0.01864": 0,
    "0.261904": 0,
    "0.09064": 0,
    "area_ratio": 0,
    "GT-": 0,
}
#: 小写血统 token 计数（替换后）
GUIDANCE_R25_R23_LOWERCASE = 1
GUIDANCE_R25_R23_LINEAGE = "相对 observation-guidance-r23 仅"
GUIDANCE_R25_R24_LOWERCASE = 1   # 本轮性质行「r24 not_instance_dominated」


# ---------------------------------------------------------------------------
# 工具（fail-closed）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[r25-prep] FAIL: {msg}")
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


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        _fail(f"机械变换锚「{label}」命中 {n} 次 != 1（锚串必须恰 1 次，"
              f"立即停止）")
    return text.replace(old, new)


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
    """observation-guidance-r23.md 变换基座身份探针（全 64 位锚+事实计数
    族；不符即停）。"""
    if sha != GUIDANCE_R23_SHA:
        _fail("基座指引全 64 位锚不符（probe 内部不一致）")
    if hashing.sha256_text(text) != sha:
        _fail("r23 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")
    if len(text.encode("utf-8")) != GUIDANCE_R23_BYTES:
        _fail(f"r23 指引字节数不符：{len(text.encode('utf-8'))} != "
              f"{GUIDANCE_R23_BYTES}")
    facts = {}
    for needle, want in GUIDANCE_R23_FACTS.items():
        got = text.count(needle)
        if got != want:
            _fail(f"r23 基座身份探针不符：{needle!r} 命中 {got} 次 != 预期 "
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
        "role": ("指引机械变换基座（两父之一）；只读零写入——变换基座落盘"
                 "事实锚（R23T-×4/R23B-×1/reader-r23-×1/round_id 2026-09-10"
                 "-r23/声明日期已为 2026-09-10）"),
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
                 "（盘上实测键位；run-r23/run-r24 baseline_cross_check 交叉"
                 "核对在案）；r16 基线四键=[0.771429, 0.857143, 12, "
                 "0.261904]"),
        "r16_baseline": M_TUPLE_R16,
    }


def probe_typology(typ: dict, sha: str) -> dict:
    """abstain-typology-r13-r16：分型件 rubric 口径链回放（fail-closed）。
    r13–r16=8/15/5/10 链的在件键位=matrix.round_totals.r13–r16.families.
    contact（contact 族，分型件族标签如实登记）；黑点族（M3）同件交叉锚=
    r16 existence_blackdot=12 == axis-plan r16_baseline.M3。"""
    if typ.get("kind") != "abstain_typology_posthoc_r13_r16":
        _fail(f"abstain-typology kind 不符：{typ.get('kind')!r}")
    if typ.get("declared_date") != "2026-09-08":
        _fail("abstain-typology declared_date != 2026-09-08")
    if typ.get("schema_version") != "3.0":
        _fail("abstain-typology schema_version != 3.0（结构漂移）")
    totals = typ.get("matrix", {}).get("round_totals", {})
    chain = {}
    for rnd in ("r13", "r14", "r15", "r16"):
        families = totals.get(rnd, {}).get("families", {})
        chain[rnd] = families.get("contact")
    if chain != TYPOLOGY_CONTACT_CHAIN:
        _fail(f"分型件 contact 族链回放不符：{chain!r} != "
              f"{TYPOLOGY_CONTACT_CHAIN!r}（r13–r16=8/15/5/10 链回放失败）")
    blackdot_r16 = totals.get("r16", {}).get("families", {}).get(
        "existence_blackdot")
    if blackdot_r16 != TYPOLOGY_R16_BLACKDOT:
        _fail(f"分型件 r16 existence_blackdot={blackdot_r16!r} != 12（M3 "
              f"rubric 口径交叉锚失败）")
    return {
        "path_rel": "out/v3-tl2/calibration/abstain-typology-r13-r16.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": TYPOLOGY_SHA[:8],
        "role": ("M3 分型件 rubric 词元口径链锚（先核对后引用）：r13–r16="
                 "8/15/5/10 链回放键位=matrix.round_totals.r13–r16."
                 "families.contact（contact 族、分型件族标签如实登记）；"
                 "黑点族（M3）同件交叉锚=r16 existence_blackdot=12 == "
                 "axis-plan r16_baseline.M3=12（rubric 词元口径同血统）"),
        "contact_chain_r13_r16": TYPOLOGY_CONTACT_CHAIN,
        "r16_existence_blackdot": TYPOLOGY_R16_BLACKDOT,
    }


def probe_run_r24(run: dict, sha: str) -> dict:
    """calibration-run-r24 判据冻结值锚定（fail-closed；只读顶层判据值
    字段+guard_channel+verdict+baseline_cross_check；GT 匹配与逐旗明细不
    读取不入记录）。r24 元组=live 装载（不手工抄）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r24 hypothesis_test 结构不符")
    if ht.get("verdict") != "not_instance_dominated":
        _fail(f"run-r24 verdict 锚不符：{ht.get('verdict')!r}（预期 "
              f"not_instance_dominated=r24 字母在案锚、轮后不改写）")
    if ht.get("hypothesis_id") != \
            "r23-confounded-residual-confound-instance-axis-attribution":
        _fail("run-r24 hypothesis_id 不符（r24 预注册假设锚）")
    m = ht.get("measurement", {})
    # r24 元组 live 装载（不手工抄）
    live = m.get("r24_m_tuple_6dp")
    if not isinstance(live, dict):
        _fail("run-r24 r24_m_tuple_6dp 结构不符")
    for key, want in M_TUPLE_R24_EXPECT.items():
        got = live.get(key)
        if got != want:
            _fail(f"run-r24 r24_m_tuple_6dp live 装载不符：{key}={got!r} != "
                  f"{want!r}")
    if m.get("top_abstain_count_r24") != TOP_ABSTAIN_R24 or \
            m.get("top_abstain_flags_r24") != TOP_FLAGS_R24 or \
            m.get("top_abstain_rate_r24") != live["M1"]:
        _fail("run-r24 M1 分子分母锚不符（58/105=0.552381）")
    if int(round(TOP_ABSTAIN_R24 * 1000000 / TOP_FLAGS_R24)) != \
            int(round(live["M1"] * 1000000)):
        _fail("自洽断言失败：58/105 六位定点 != 0.552381")
    if m.get("m4_top_rate_range_r24") != live["M4"] or \
            m.get("m4_threshold_6dp") != M4_ANCHOR_6DP:
        _fail("run-r24 M4 极差/阈值锚不符")
    if m.get("split_half_M1_diff_r24") != live["split_half_M1_diff"] or \
            m.get("split_half_threshold_6dp") != DRIFT_6DP:
        _fail("run-r24 split_half 锚不符（0.01864/阈值 90640）")
    if int(round(live["split_half_M1_diff"] * 1000000)) != SPLIT_HALF_R24_6DP:
        _fail("split_half 6 位定点自证失败（0.018640 != 18640）")
    if int(round(live["M4"] * 1000000)) != 888889:
        _fail("M4 6 位定点自证失败（0.888889 != 888889）")
    if m.get("g2_rejected_entries_zero") is not True:
        _fail("run-r24 g2_rejected_entries_zero != true（G2=0 锚不符）")
    gc = m.get("guard_channel", {})
    if gc.get("g1_ok") is not True or gc.get("g2_guard_ok") is not True or \
            gc.get("guards_ok") is not True:
        _fail("run-r24 守门锚不符（预期 G1 维持、G2 满足）")
    if gc.get("g2_geometry_gate_r19") != G2_R19 or \
            gc.get("g2_geometry_gate_r22") != G2_R22 or \
            gc.get("g2_geometry_gate_r23") != G2_R23 or \
            gc.get("g2_geometry_gate_r24") != G2_R24:
        _fail("run-r24 G2 几何门链锚不符（预期 r19=0/r22=2/r23=1/r24=0）")
    detail = m.get("bottom_courtyard_detail_r24", [])
    if not isinstance(detail, list) or len(detail) != 6:
        _fail("run-r24 bottom_courtyard_detail_r24 须恰 6 实例")
    for entry in detail:
        if entry.get("courtyard_non_abstain_count") != 0:
            _fail(f"run-r24 G1 锚不符：{entry.get('instance')!r} 非弃权 "
                  f"courtyard != 0（预期六实例全 0）")
    bcc = m.get("baseline_cross_check", {})
    if bcc.get("axis_plan_r16_baseline_M1_M2_M3_M4") != \
            [0.771429, 0.857143, 12, 0.261904]:
        _fail("run-r24 baseline_cross_check r16 基线四键不符（M4 阈值锚"
              "交叉核对失败）")
    for row_key, want in (("r19_row", M_TUPLE_R19), ("r22_row", M_TUPLE_R22),
                          ("r23_row", M_TUPLE_R23)):
        if bcc.get(f"{row_key}_live") != want or \
                bcc.get(f"{row_key}_registered") != want:
            _fail(f"run-r24 baseline_cross_check {row_key} live/registered "
                  f"不符（预期 {want!r}）")
    if bcc.get("r16_contact_live_replay") != TYPOLOGY_CONTACT_CHAIN:
        _fail("run-r24 baseline_cross_check.r16_contact_live_replay 与分型"
              "件 8/15/5/10 链不符（交叉核对失败）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r24.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": RUN_R24_SHA[:8],
        "role": ("r24 实测锚（run 件；本轮元组 live 装载源、不手工抄）："
                 "M tuple=(0.552381, 0.692308, 28, 0.888889、split_half="
                 "0.018640)（M1=58/105、M2=18/26）；G1 维持（六实例 "
                 "courtyard 非弃权全 0）；G2 几何门 r19=0/r22=2/r23=1/"
                 "r24=0；verdict=not_instance_dominated（轮后不改写）；"
                 "baseline_cross_check 与 axis-plan/分型件交叉核对在案"),
        "frozen_values": ("M tuple (M1,M2,M3,M4)=(0.552381, 0.692308, 28, "
                          "0.888889)+split_half_M1_diff=0.018640；verdict="
                          "not_instance_dominated；G1 维持；G2=0"),
        "m_tuple_r24_live": live,
    }


def probe_run_r23(run: dict, sha: str) -> dict:
    """calibration-run-r23 判据冻结值锚定（比较集 r23 行装载源之一）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r23 hypothesis_test 结构不符")
    if ht.get("verdict") != "confounded":
        _fail(f"run-r23 verdict 锚不符：{ht.get('verdict')!r}")
    m = ht.get("measurement", {})
    if m.get("r23_m_tuple_6dp") != M_TUPLE_R23:
        _fail(f"run-r23 r23_m_tuple_6dp 不符：{m.get('r23_m_tuple_6dp')!r}")
    if m.get("r19_reference_tuple") != M_TUPLE_R19:
        _fail("run-r23 r19_reference_tuple 不符")
    bcc = m.get("baseline_cross_check", {})
    if bcc.get("axis_plan_r16_baseline_M1_M2_M3_M4") != \
            [0.771429, 0.857143, 12, 0.261904]:
        _fail("run-r23 baseline_cross_check r16 基线四键不符")
    gc = m.get("guard_channel", {})
    if gc.get("g2_geometry_gate_r23") != G2_R23:
        _fail("run-r23 G2=1 锚不符")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r23.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": RUN_R23_SHA_PREFIX[:8],
        "role": ("r23 元组+r19 参照元组装载源（比较集多源之一；框宽排除"
                 "在案）：r23=(0.484848, 0.571429, 8, 0.520833)；verdict="
                 "confounded（轮后不改写）"),
    }


def probe_run_r22(run: dict, sha: str) -> dict:
    """calibration-run-r22 判据冻结值锚定（比较集 r22 行装载源之一）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r22 hypothesis_test 结构不符")
    if ht.get("verdict") != "regressed":
        _fail(f"run-r22 verdict 锚不符：{ht.get('verdict')!r}")
    m = ht.get("measurement", {})
    if m.get("r22_m_tuple_6dp") != M_TUPLE_R22:
        _fail(f"run-r22 r22_m_tuple_6dp 不符：{m.get('r22_m_tuple_6dp')!r}")
    if m.get("r19_reference_tuple") != M_TUPLE_R19:
        _fail("run-r22 r19_reference_tuple 不符")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r22.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": RUN_R22_SHA_PREFIX[:8],
        "role": ("r22 元组+r19 参照元组装载源（比较集多源之一）：r22=(0."
                 "390244, 0.2, 4, 0.104545)；verdict=regressed"),
    }


def probe_dev_record_r24(dev: dict, sha: str, dev_raw: str,
                         live_tuple: dict) -> dict:
    """round24-dev-record：r24 实测锚+字母+G1/G2 锚+候选(b)授权原文+聚合
    稳/个体散在案原文（GT 字段不转录）。"""
    if dev.get("kind") != "tl2_calibration_round24_dev_record":
        _fail("round24-dev-record kind 不符")
    if dev.get("round_id") != "2026-09-10-r24" or \
            dev.get("round_label") != "r24":
        _fail("round24-dev-record 轮次标识不符")
    if dev.get("declared_date") != "2026-09-10":
        _fail("round24-dev-record declared_date != 2026-09-10")
    if dev.get("schema_version") != "3.0":
        _fail("round24-dev-record schema_version != 3.0（结构漂移）")
    measured = dev.get("axis_experiment_ledger", {}).get(
        "this_round_measured", {})
    if measured != live_tuple:
        _fail(f"round24-dev-record 实测元组锚不符：{measured!r} != run-r24 "
              f"live {live_tuple!r}（两源一致性失败）")
    rows = dev.get("axis_experiment_ledger", {}).get(
        "cross_round_status", {}).get("measured_rows", {})
    for row_name, want in (("r16_baseline", M_TUPLE_R16),
                           ("r19_axis3", M_TUPLE_R19),
                           ("r22_repeat", M_TUPLE_R22),
                           ("r23_repeat", M_TUPLE_R23),
                           ("r24_expansion", live_tuple)):
        if rows.get(row_name) != want:
            _fail(f"round24-dev-record 台账行 {row_name} 不符："
                  f"{rows.get(row_name)!r} != {want!r}（比较集装载源锚）")
    if dev.get("hypothesis_test_i", {}).get("verdict") != \
            "not_instance_dominated":
        _fail("round24-dev-record hypothesis_test_i.verdict != "
              "not_instance_dominated")
    g2 = dev.get("g2_bifurcation_record")
    if not isinstance(g2, dict):
        _fail("round24-dev-record g2_bifurcation_record 结构不符")
    counts = g2.get("counts", {})
    if counts.get("g1_bottom_courtyard_non_abstain_r24") != \
            {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0,
             "bottom-i4": 0, "bottom-i5": 0, "bottom-i6": 0}:
        _fail("round24-dev-record G1 维持锚不符（r24 六实例全 0）")
    if counts.get("g2_eligibility_gate_satisfied_r24") is not True:
        _fail("round24-dev-record g2_eligibility_gate_satisfied_r24 != true")
    letter = g2.get("letter_vs_fact", {}).get("letter", "")
    if not letter.startswith("not_instance_dominated"):
        _fail(f"r24 字母锚不符：{letter!r}（预期 not_instance_dominated、"
              f"轮后不改写）")
    opts = dev.get("next_candidate_suggestion", {}).get("options", [])
    if len(opts) != 3:
        _fail(f"round24-dev-record 下一候选选项须恰 3 项：{len(opts)}")
    if opts[1].get("option") != CANDIDATE_B_OPTION:
        _fail(f"候选(b) 原文不符：{opts[1].get('option')!r}")
    if opts[1].get("preregistration_required") is not True:
        _fail("候选(b) preregistration_required != true")
    if AGGREGATE_STABLE_QUOTE not in dev_raw:
        _fail("round24-dev-record raw text 缺「聚合稳/个体散」在案原文"
              "（设计依据引用锚失败）")
    return {
        "path_rel": "out/v3-tl2/calibration/round24-dev-record.json",
        "sha256_measured": sha,
        "sha256_prefix_expected": DEV_RECORD_R24_SHA[:8],
        "role": ("本轮设计出处与合法性依据（两父之二）：not_instance_"
                 "dominated 归因转向登记+候选(b)授权原文+「聚合稳[拆半 "
                 "0.018640]与个体散[极差 0.888889、双峰结构]并存」在案原文"
                 "+r24 实测元组/G1/G2/字母锚+比较集台账行装载源"),
        "letter": "not_instance_dominated（唯一正式裁决、轮后不改写）",
        "measured_tuple": live_tuple,
        "candidate_b_quote": CANDIDATE_B_QUOTE,
        "aggregate_stable_quote": AGGREGATE_STABLE_QUOTE,
    }


def probe_drift_anchor(dev22_text: str, dev23_text: str) -> dict:
    """drift 0.09064 在案锚：raw text 计数（缺锚即 FAIL；先确认在案后才
    可引用——split_half 阈值口径的参照血统）。"""
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
# 指引机械变换（纯函数；锚串命中数 fail-closed）
# ---------------------------------------------------------------------------

def derive_guidance_r25(base_text: str) -> str:
    """observation-guidance-r25 全文=observation-guidance-r23 全文的确定
    性机械变换（9 组锚定编辑；锚恰 1 次否则 FAIL）。任务枚举之（1）–
    （4）=轮次身份四处（之(3)=声明日期 no-op 确认）；之（5）=变更声明节
    正文整体替换（冻结区 token 断言的必要补入项、s80 任务 5 先例同型、偏
    差如实登记）；之（6）=§4 末尾增补条款（§5 标题行之前插入）；之
    （7）–（9）=§6 前缀机械替换。"""
    for needle, want in GUIDANCE_R23_FACTS.items():
        n = base_text.count(needle)
        if n != want:
            _fail(f"r23 基座落盘事实锚不符：{needle!r} 命中 {n} 次 != 预期 "
                  f"{want} 次（立即停止）")
    t = base_text
    # （1）标题行替换
    t = _replace_once(t, OLD_TITLE, NEW_TITLE, "标题行")
    # （2）round_id_constant bullet
    t = _replace_once(t, OLD_ROUND_ID_LINE, NEW_ROUND_ID_LINE,
                      "round_id_constant bullet")
    # （3）声明日期 bullet：基座已是 2026-09-10 → 确认无操作（no-op）
    n = t.count(DATE_LINE)
    if n != 1:
        _fail(f"声明日期 bullet 锚命中 {n} 次 != 1（no-op 确认失败）")
    # （4）本轮性质行按判据内容轴口径重写
    t = _replace_once(t, OLD_NATURE_LINE, NEW_NATURE_LINE, "本轮性质行")
    # （5）「本轮变更声明」节正文整体替换（必要补入项；s80 任务 5 先例）
    t = _replace_once(t, OLD_CHANGES_PARA, NEW_CHANGES_PARA,
                      "本轮变更声明节正文")
    # 头部更新后、前缀替换前：R23 系旗 ID 前缀应恰为落盘原文 4/1/1
    for old, _, want in PREFIX_EDITS:
        n = t.count(old)
        if n != want:
            _fail(f"前缀替换前锚不符：{old!r} 命中 {n} 次 != {want} 次")
    # （6）§4 末尾增补弃权边界操作化条款（§5 标题行之前插入）
    n = t.count(CLAUSE_INSERT_ANCHOR)
    if n != 1:
        _fail(f"条款插入锚命中 {n} 次 != 1（立即停止）")
    t = t.replace(
        CLAUSE_INSERT_ANCHOR,
        "\n\n" + CLAUSE_TEXT + CLAUSE_INSERT_ANCHOR)
    # （7）–（9）§6 前缀机械替换
    for old, new, want in PREFIX_EDITS:
        n = t.count(old)
        if n != want:
            _fail(f"前缀替换锚不符：{old!r} 命中 {n} 次 != {want} 次")
        t = t.replace(old, new)
    return t


def assert_guidance_r25(derived: str, base: str) -> dict:
    """r25 指引一致性断言（冻结区逐字；不符即停）。"""
    for needle, want in GUIDANCE_R25_REQUIRED.items():
        n = derived.count(needle)
        if n != want:
            _fail(f"r25 指引断言不符：{needle[:40]!r} 命中 {n} 次 != {want} "
                  f"次")
    # 小写血统 token 计数
    n_r23 = derived.count("r23")
    if n_r23 != GUIDANCE_R25_R23_LOWERCASE:
        _fail(f"r25 指引小写 r23 残留 {n_r23} 处 != 恰 1 处（基座血统引用）")
    if derived.count(GUIDANCE_R25_R23_LINEAGE) != 1:
        _fail("r25 指引缺变更声明基座血统引用「相对 observation-guidance"
              "-r23 仅」恰 1 处")
    n_r24 = derived.count("r24")
    if n_r24 != GUIDANCE_R25_R24_LOWERCASE:
        _fail(f"r25 指引小写 r24 残留 {n_r24} 处 != 恰 1 处（本轮性质行）")
    n_r19 = derived.count("r19") + derived.count("r22")
    if n_r19 != 0:
        _fail(f"r25 指引小写 r19/r22 残留 {n_r19} 处 != 0")
    # §2、§3（含 §3A）逐字一致（substring）：「## 2.」起至「## 4.」止
    seg2_3 = base[base.index(MARK_S2):base.index(MARK_S4)]
    if seg2_3 not in derived:
        _fail("一致性断言失败：r25 与 r23 的 §2–§3（含 §3A）区块逐字不一致")
    # §4=基座 §4 原文完整保留+仅末尾追加该条款（区块等价断言；切片含
    # 「## 5.」标题前的尾随空行）
    base_s4 = base[base.index(MARK_S4):base.index(MARK_S5)]
    derived_s4 = derived[derived.index(MARK_S4):derived.index(MARK_S5)]
    if derived_s4 != base_s4 + CLAUSE_TEXT + "\n\n":
        _fail("一致性断言失败：§4 != 基座 §4 原文+仅末尾追加条款（区块"
              "等价失败）")
    # §5（含 §5A）逐字一致（substring）：「## 5.」起至「## 6.」止
    seg5 = base[base.index(MARK_S5):base.index(MARK_S6)]
    if seg5 not in derived:
        _fail("一致性断言失败：r25 与 r23 的 §5（含 §5A）区块逐字不一致")
    # §6 结构等价复核：实际 §6 区块==基座 §6 区块+前缀替换（零增补）
    base6 = base[base.index(MARK_S6):base.index(MARK_S7)]
    expect6 = base6
    for old, new, want in PREFIX_EDITS:
        if expect6.count(old) != want:
            _fail(f"§6 等价复核锚不符：{old!r}")
        expect6 = expect6.replace(old, new)
    actual6 = derived[derived.index(MARK_S6):derived.index(MARK_S7)]
    if actual6 != expect6:
        _fail("§6 结构等价复核失败：实际 §6 区块 != 基座 §6+前缀替换")
    # §7 逐字一致（substring）：「## 7.」标题起至文末（含（完））
    seg7 = base[base.index(MARK_S7):]
    if seg7 not in derived or not derived.endswith(seg7):
        _fail("一致性断言失败：r25 与 r23 的 §7 区块逐字不一致（含文末）")
    return {
        "seg2_3_bytes": len(seg2_3.encode("utf-8")),
        "seg4_base_bytes": len(base_s4.encode("utf-8")),
        "clause_bytes": len(CLAUSE_TEXT.encode("utf-8")),
        "seg5_bytes": len(seg5.encode("utf-8")),
        "seg6_base_bytes": len(base6.encode("utf-8")),
        "seg7_bytes": len(seg7.encode("utf-8")),
    }


# ---------------------------------------------------------------------------
# 预注册归因判据（hypothesis_test；逐字冻结先于盲读）
# ---------------------------------------------------------------------------

HYPOTHESIS_TEST_TEXT = r'''
{
 "adjudication": {
  "criterion_dominated": "G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）且 M4(n=6) < 0.261904（6 位定点整数交叉相乘比较；锚=r16 基线 M4，axis-plan baselines_registered.r16_baseline + run-r24 baseline_cross_check 交叉核对）→ 弃权边界显式化收敛个体散=判据内容为个体散主因",
  "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准",
  "fixed_point_comparison_note": "全部阈值比较=6 位定点整数交叉相乘、零浮点除法（r22/r23/r24 先例）：M4(n=6)<0.261904 ⟺ m4_6dp<261904（整数）；M4(n=6)≥0.261904 ⟺ m4_6dp≥261904；M4 自证=928571−666667=261904（r16 基线 top-i2/top-i1 两实例率之差，本脚本整数复算断言）；split_half_M1_diff 本轮=机制观察单列、不进分支判定（与 r24 双判据分支的差异如实登记：实例群轴已由 r24 测毕、拆半阈值 0.09064=90640 的分支使命完成——0.09064 在案锚=round22/round23-dev-record raw text 计数 dev22=9 处/dev23=6 处）；字母裁决无浮点路径",
  "g2_observation_separate": "G2（top 视非弃权旗标 frame_box_pct 几何门面积比>10 出局条目数）=实测观察项、非本轮字母支：G2>0 → r25 资格门剔除不入排序（r22/r23 先例；r19=0/r22=2/r23=1/r24=0 对照在案）；出局条目逐条摘录入机制观察（flag_id/category/area_ratio/containment/现象转述逐条如实、GT 字段不转录）；几何门照常独立计算、不改写三支字母、不参与 criterion_dominated/not_criterion_dominated 分支判定",
  "guard_interrupted": "G1 破坏 → 字母=guard_interrupted（归因悬置、机制观察照常、g1 分岔先例引用）",
  "letter_branch_map": "字母=三支之一（criterion_dominated/not_criterion_dominated/guard_interrupted），唯一正式裁决、轮后不改写：G1 破坏→guard_interrupted 独占（归因悬置）；G1 维持→由 M4(n=6) 恰定一支（<0.261904→criterion_dominated；≥0.261904→not_criterion_dominated）——三支互斥、恰一支命中、不新增字母支、不升级归因；r24 字母=not_instance_dominated 与 r23 字母=confounded、r22 字母=regressed 维持不改写",
  "m1_m2_gate_separate": "M1/M2 变动=机制观察+APR-0011 门指标照常分列——本轮字母只看个体散收敛（M4(n=6) 单判据）、不看 M1 降不降：M1 降不构成 criterion_dominated 证据、M1 升不构成 not_criterion_dominated 证据；显式防止「为降弃权率而操作化」的动机误读（弃权边界操作化条款不放宽判据——弃权→低 confidence 非弃权旗=旗仍设立、非「判正常」——把握不足本身不构成弃权理由（条款执行细则原文），见 no_loosening_note）；APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate≤0.5）门照常独立计算",
  "mechanism_observation_separate": "M1/M2/M3/三族计数/援引计数照常单列机制观察、不进字母裁决：M 元组（含 split_half_M1_diff）入实验对照账（比较集=r16 基线+r19/r22/r23/r24 实测元组，axis ledger 延续登记、rubric 口径）；contact/黑点/存在性三族计数（分型件 rubric 口径）对照 r19（4/4/14）/r22（2/4/12）/r23（8/8/7+semantic_confusion 1）/r24 在案基线；(iii-a)/§5B/§6 援引计数照记（本轮指引=observation-guidance-r25.md、无 §5B 节=任何援引为零上下文）；G2 出局条目（若有）逐条摘录；M3 与 split_half_M1_diff 单列对照 r19/r22/r23/r24；gt 照常",
  "metric_lesson_separate": "跨轮实例群漂移混杂照旧声明——本轮唯一实验变量=§4 末尾弃权边界操作化条款（判据内容轴），实例群重抽为轮际固有混杂、非本轮实验操作（n=6 口径与 r24 完全同构、实例群再次全量重抽照轮际惯例）；M4 口径粒度差异延续 r24 登记（12 格逐格率极差 vs r16–r23 逐实例两板合计口径——阈值 0.261904=r16 历史口径在案值原样引用不改写、跨口径比较=描述性、如实声明）；单轮 development 域只描述不断言；判据内容轴=指引文本变更轴：操作化条款只增补执行细则、不触碰 §4 原文与任何量化判据（(i)(ii)(iii)、(iii-a)、三路出口）——判据内容零修改、仅边界显式化（操作化）",
  "not_criterion_dominated": "G1 维持 且 M4(n=6) ≥ 0.261904 → 边界操作化未收敛个体散=判据内容非主因（残余归因=其他输出侧/模型侧固有；归因链如实登记）",
  "three_way_bookkeeping": "「正确测出无效同样是有效证据」三向记账：结果无论方向均如实入账——字母（三支判据按预注册原文执行、唯一正式裁决、轮后不改写）、机制观察（M 元组落点+三族计数+援引计数+G2 出局条目摘录，单列不进字母）、度量教训（判据内容轴单变量操作化的验证力度声明+M4 口径粒度延续登记，单列）——三账分列、不合并、不改写；criterion_dominated 支命中不构成「判据已收敛/能力已达成」类断言（归因结论如实登记而已）、not_criterion_dominated 支命中不构成对判据内容的否定性断言（仅登记残余归因=其他输出侧/模型侧固有；归因链如实登记）"
 },
 "hypothesis": "r24（实例群扩容归因轮）字母=not_instance_dominated（唯一正式裁决、轮后不改写）：G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）且 M4(n=6)=0.888889≥0.261904（6 位定点 888889≥261904）=离散超出抽样尺度、split_half_M1_diff=0.018640≤0.09064（18640≤90640）=聚合稳——r24 实测「聚合稳[拆半 0.018640]与个体散[极差 0.888889、双峰结构]并存」（round24-dev-record 1a344edf 在案；run-r24 8a9bdb7d live：M1=58/105=0.552381、M2=18/26=0.692308、M3=28、G2=0 资格门满足）。实例群轴单变量测毕→归因转向=判据内容（round24-dev-record next_candidate_suggestion options[1] 授权在案）。归因链：r23 框宽排除（confounded，round23-dev-record 343a6747 在案）→r24 实例群排除（not_instance_dominated）→r25 判据内容（本轮）。判据内容轴的可分变量=弃权边界操作化：r24 的「聚合稳/个体散并存」=弃权边界欠操作化假说的直接可测推论——若 r24 的个体散（双峰/极差爆拉）源于判读人对「何时必须设旗 vs 何时可弃权」的边界理解不一（判据内容因素），则边界显式化（§4 末尾三问条款）后个体散应收敛（M4(n=6)<0.261904→criterion_dominated=判据内容为个体散主因）；若离散源于其他输出侧/模型侧固有因素，则边界显式化后个体散不收敛（M4(n=6)≥0.261904→not_criterion_dominated=判据内容非主因、残余归因=其他输出侧/模型侧固有）。R25=判据内容轴归因轮（唯一实验变量=判读指引 §4 末尾增补弃权边界操作化条款；指引由 observation-guidance-r23.md 866b0157 机械变换派生 observation-guidance-r25.md；渲染零变更 renders-r14b 字节复用、GT/阈值/协议零变更、n=6 口径照 r24 完全同构），以 G1+M4(n=6) 做归因裁决（6 位定点整数交叉相乘比较）：criterion_dominated 支命中→弃权边界显式化收敛个体散=判据内容为个体散主因；not_criterion_dominated 支命中→边界操作化未收敛个体散=判据内容非主因；guard_interrupted 支（若 G1 破坏）→归因悬置、机制观察照常。",
 "hypothesis_id": "r24-not-instance-dominated-criterion-boundary-operationalization-attribution"
}
'''
import json as _json  # noqa: E402  (模块级对拍用；无 IO)

HYPOTHESIS_TEST = _json.loads(HYPOTHESIS_TEST_TEXT)

#: 预注册判据文本数值 needle（逐字在位断言；不符即停）
REQUIRED_NEEDLES = (
    "0.261904",
    "261904",
    "928571−666667=261904",
    "G1 维持（六 bottom 实例 courtyard 非弃权旗全=0）",
    "弃权边界显式化收敛个体散=判据内容为个体散主因",
    "边界操作化未收敛个体散=判据内容非主因",
    "残余归因=其他输出侧/模型侧固有",
    "字母=guard_interrupted（归因悬置、机制观察照常、g1 分岔先例引用）",
    "0.552381",
    "0.692308",
    "0.888889",
    "0.018640",
    "0.09064",
    "90640",
    "18640",
    "not_instance_dominated",
    "r19=0/r22=2/r23=1/r24=0",
    "资格门剔除不入排序",
    "聚合稳",
    "个体散",
    "双峰",
    "为降弃权率而操作化",
    "把握不足本身不构成弃权理由",
    "axis-plan baselines_registered.r16_baseline + run-r24 baseline_cross_check 交叉核对",
    "axis-experiment-plan-r17-r20.json 为准",
    "不进字母裁决",
)


# ---------------------------------------------------------------------------
# 记录构造（纯函数）
# ---------------------------------------------------------------------------

def build_record(*, guidance_ref: dict, dev24_ref: dict,
                 axis_ref: dict, typology_ref: dict, run24_ref: dict,
                 run23_ref: dict, run22_ref: dict, r23_record_sha: str,
                 r24_record_sha: str, witness_sha: str, protocol_v1_sha: str,
                 protocol_v2_sha: str, png_checks: list, drift_counts: dict,
                 derived_sha: str, derived_bytes: int, seg_bytes: dict,
                 m_tuple_r24_live: dict,
                 protected_hashes: dict) -> dict:
    """r25-prep-record 构造（25 键=r24-prep-record 25 键 schema 逐键镜像；
    canonical JSON sort_keys 落盘）。"""
    record = {}
    record["attribution_plan"] = {
        "attribution_chain": (
            "三混杂轴归因链（r23 confounded 归因转向登记的剩余混杂=判据内"
            "容/实例群/其他输出侧因素）：(1) r23 框宽排除——单变量报告框收"
            "敛轮 G2 出局 1>0 未清零、框宽非（唯一）主因（round23-dev-"
            "record 343a6747 在案、字母=confounded 轮后不改写）；(2) r24 "
            "实例群排除——实例群扩容轮 M4(n=6)=0.888889≥0.261904、离散超出"
            "抽样尺度（round24-dev-record 1a344edf/run-r24 8a9bdb7d 在案、"
            "字母=not_instance_dominated 轮后不改写）；(3) r25 判据内容—"
            "—本轮：弃权边界操作化后 M4(n=6) 落点裁决（criterion_dominated"
            "/not_criterion_dominated）；前两轴排除在案、轮后不改写"),
        "comparator_note": "比较器逐旗输出含失败通道明细",
        "declaration": (
            "本轮恰一个实验变量（判读指引 §4 末尾弃权边界操作化条款=判据内"
            "容轴单变量；渲染/GT/阈值/协议零变更、n=6 口径与 r24 完全同"
            "构）、检验恰一个假设（hypothesis_id=r24-not-instance-dominated"
            "-criterion-boundary-operationalization-attribution：弃权边界"
            "显式化后个体散（M4 极差）是否收敛=判据内容是否为个体散主"
            "因）；归因目的=M4(n=6) 落点裁决（三支：criterion_dominated="
            "判据内容为个体散主因；not_criterion_dominated=判据内容非主"
            "因、残余归因=其他输出侧/模型侧固有；guard_interrupted=归因悬"
            "置）；字母/机制观察/度量教训三分记账（mechanism_observation_"
            "separate 与 metric_lesson_separate 单列，不凌驾三支裁决）"),
        "design_rationale": (
            "r24 实测「聚合稳[拆半 0.018640≤0.09064]与个体散[极差 0.888889、"
            "双峰结构]并存」（round24-dev-record 1a344edf 在案原文：「" +
            AGGREGATE_STABLE_QUOTE + "」；run-r24 8a9bdb7d live 实测 "
            "split_half_M1_diff_r24=0.01864/m4_top_rate_range_r24=0.888889）"
            "=弃权边界欠操作化假说的直接可测推论：若 r24 的个体散（双峰/"
            "极差爆拉）源于判读人对「何时必须设旗 vs 何时可弃权」的边界理"
            "解不一（判据内容因素），则边界显式化（§4 末尾三问条款）后个体"
            "散应收敛（M4(n=6)<0.261904→criterion_dominated=判据内容为个"
            "体散主因）；若离散源于其他输出侧/模型侧固有因素，则边界显式化"
            "后个体散不收敛（M4(n=6)≥0.261904→not_criterion_dominated=判"
            "据内容非主因）——边界显式化前后 M4 极差落点=假说的直接可测量"),
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
            "先例在案、r24 六实例扩容口径 0 在案；G1 为「不得弃权」方向的"
            "反向风险守门；任一实例非零→G1 破坏→guard_interrupted 支）；"
            "G2=top 视非弃权旗标 frame_box_pct 几何门面积比>10 出局条目数"
            "=实测观察项（非本轮字母支）：G2>0→r25 资格门剔除不入排序"
            "（r22/r23 先例；r19=0/r22=2/r23=1/r24=0 对照在案）；G3 冻结"
            "纪律照常"),
        "primary_channel": (
            "M4(n=6)（top 12 格逐格弃权率极差）单判据归因裁决（三支，6 位"
            "定点整数交叉相乘比较、零浮点除法）——详见 hypothesis_test."
            "adjudication；M1/M2/M3/split_half_M1_diff 全元组照常入实验对"
            "照账（比较集=r16 基线+r19/r22/r23/r24 实测元组）；G2=实测观"
            "察项非本轮字母支；M1/M2 变动=机制观察+APR-0011 门指标照常分"
            "列（本轮字母只看个体散收敛、不看 M1 降不降——见 adjudication."
            "m1_m2_gate_separate）"),
        "single_variable_rationale": (
            "三混杂轴中判据内容轴的可分变量=弃权边界操作化（判据条款语义/"
            "门限的操作化显式化）：判据内容轴须指引文本变更（r24-prep-"
            "record single_variable_rationale 预登记「判据内容轴须指引文"
            "本变更、留待后续预注册轮」——本轮即该后续轮）；条款设计为纯"
            "执行细则增补（§4 原文零修改、量化判据 (i)(ii)(iii)/(iii-a)/"
            "三路出口/反放宽条款逐字保留）=判据内容的边界显式化、非判据调"
            "参（axis-experiment-plan-r17-r20 收束决议与轴停止决议不变）；"
            "实例群轴已由 r24 单变量测毕（not_instance_dominated）；其他"
            "输出侧轴=本轮不操纵（not_criterion_dominated 支命中时的残余"
            "归因位）"),
    }
    record["bottom_view_note"] = (
        "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16/R18/"
        "R19/R20/R22/R23/R24 完全相同文件：白墨图元→橙 (255,165,0)、板内"
        "空隙白→绿 (0,128,0)、其余层 kicad 原配色不变；四 PNG sha256_file "
        "实测=witness-r14b 登记值+任务给定全 64 位预期值双重 fail-closed "
        "比对一致）——渲染零变更；本轮唯一判读变更=§4 末尾弃权边界操作化"
        "条款（判据内容轴执行细则、非 bottom 配色或判读口径变更）；bottom "
        "视判读口径沿用 r4 指引原文不改（top/bottom 判读口径在图像空间完"
        "全一致、不做镜像换算）；本轮 bottom 侧 6 实例（bottom-i1–i6）各"
        "包同侧两板（先 applied 后 prep1、flag_id 同实例跨板连续）；"
        "bottom 零旗标分母=0 时弃权率按 cal._ratio 先例=None 口径照旧")
    record["changed_variables"] = [
        {
            "attribution_channel": (
                "归因裁决=hypothesis_test.adjudication 三支（criterion_"
                "dominated：G1 维持且 M4(n=6)<0.261904；not_criterion_"
                "dominated：G1 维持且 M4(n=6)≥0.261904；guard_interrupted："
                "G1 破坏）——全部阈值比较=6 位定点整数交叉相乘、零浮点除"
                "法；本轮分支判据=M4 单判据（split_half_M1_diff=机制观察"
                "单列、不进分支判定——与 r24 双判据分支的差异如实登记）"),
            "axis": "criterion_content（判据内容轴）",
            "axis_note": (
                "三混杂轴归因链（r23 框宽排除[confounded 在案]→r24 实例"
                "群排除[not_instance_dominated 在案]→r25 判据内容[本轮]）"
                "的第三轴执行轮；判据内容轴=须指引文本变更的轴（r24-prep-"
                "record single_variable_rationale 预登记留待后续预注册轮—"
                "—本轮即该后续轮）；非判据调参轴重开：axis-experiment-"
                "plan-r17-r20 三轴（判据侧轴1/轴2/轴3）收束决议与轴停止决"
                "议不变；条款只增补执行细则、§4 原文与任何量化判据零修改"),
            "description": (
                "§4 末尾增补弃权边界操作化条款（observation-guidance-r25.md "
                "由 observation-guidance-r23.md 866b0157 机械变换派生；在 "
                "§5 标题行之前插入；条款全文逐字见 guidance_reuse.edit_"
                "list[5].text_full）：对任一候选现象依次自问三问并按答案处"
                "置——(1) 不能定位→不设旗；(2) 均不能归入 §2 封闭集→"
                "other_advisory+弃权；(3) 两条以上实质不同候选解释且均无独"
                "有可辨特征→弃权（弃权理由逐条列出各候选解释）；否则必须"
                "设非弃权旗、confidence 如实取低值——把握不足本身不构成弃"
                "权理由（§4 反放宽条款的执行细则、反放宽条款原文不变）；三"
                "问之外的任何理由不构成弃权依据、三问顺序不得颠倒；随变更"
                "的机械变换同步项（非独立变量）：轮次身份四处更新（标题/"
                "round_id_constant/声明日期[无操作确认]/本轮性质行）、变更"
                "声明节正文整体重写（s80 任务 5 先例补入项）、§6 示例旗 ID "
                "前缀机械替换 R23T-→R25T-（4 处）/R23B-→R25B-（1 处）/"
                "reader-r23-→reader-r25-（1 处）——s48/s54/s63/s67/s70/s80 "
                "机械变换先例同型"),
            "id": "guidance-s4-abstain-boundary-operationalization-clause",
            "instrument_change": False,
            "target": (
                "observation-guidance-r25.md §4 末尾（§5 标题行之前新增条"
                "款段；不触碰 §4 原文与 §2/§3/§3A/§5/§5A/§6/§7 任何文本——"
                "脚本 substring 区块断言 fail-closed）"),
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
            "delta": derived_bytes - GUIDANCE_R23_BYTES,
            "derived": derived_bytes,
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
                    "板；本轮协议口径=v1/v1.1/v1.2 继承+v1.3 n=6 附录沿用 "
                    "r24"),
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v2.md",
                "sha256_measured": protocol_v2_sha,
                "sha256_prefix_expected": EVAL_PROTOCOL_V2_SHA_PREFIX,
            },
            "guidance_base_r23_transform_base": {
                "byte_size": GUIDANCE_R23_BYTES,
                "identity_facts": guidance_ref["identity_facts"],
                "path_rel": guidance_ref["path_rel"],
                "role": guidance_ref["role"],
                "sha256_measured": guidance_ref["sha256_measured"],
                "sha256_prefix_expected": guidance_ref["sha256_prefix_expected"],
            },
            "parent_2_round24_dev_record": {
                "aggregate_stable_quote": dev24_ref["aggregate_stable_quote"],
                "candidate_b_quote": dev24_ref["candidate_b_quote"],
                "letter": dev24_ref["letter"],
                "measured_tuple": dev24_ref["measured_tuple"],
                "path_rel": dev24_ref["path_rel"],
                "role": dev24_ref["role"],
                "sha256_measured": dev24_ref["sha256_measured"],
                "sha256_prefix_expected":
                    dev24_ref["sha256_prefix_expected"],
            },
            "r23_prep_record_transform_lineage": {
                "cross_check": (
                    "机械变换派生先例（s80 九锚变换：r19→r23 指引派生；本"
                    "轮 r23→r25 同型）"),
                "path_rel": "out/v3-tl2/calibration/r23-prep-record.json",
                "sha256": r23_record_sha,
            },
            "r24_prep_record_structure_lineage": {
                "cross_check": (
                    "25 键顶层结构逐键镜像（本轮判据/结构血统=r24；键集合"
                    "与 r24-prep-record 完全一致）"),
                "path_rel": "out/v3-tl2/calibration/r24-prep-record.json",
                "sha256": r24_record_sha,
            },
            "render_witness_r14b_byte_reuse": {
                "path_rel": "out/v3-tl2/calibration/render-witness-r14b.json",
                "sha256": witness_sha,
            },
            "run_r22_metric_anchor": {
                "path_rel": run22_ref["path_rel"],
                "role": run22_ref["role"],
                "sha256_measured": run22_ref["sha256_measured"],
                "sha256_prefix_expected":
                    run22_ref["sha256_prefix_expected"],
            },
            "run_r23_metric_anchor": {
                "path_rel": run23_ref["path_rel"],
                "role": run23_ref["role"],
                "sha256_measured": run23_ref["sha256_measured"],
                "sha256_prefix_expected":
                    run23_ref["sha256_prefix_expected"],
            },
            "run_r24_metric_anchor": {
                "frozen_values": run24_ref["frozen_values"],
                "path_rel": run24_ref["path_rel"],
                "role": run24_ref["role"],
                "sha256_measured": run24_ref["sha256_measured"],
                "sha256_prefix_expected":
                    run24_ref["sha256_prefix_expected"],
            },
            "typology_rubric_chain_anchor": {
                "contact_chain_r13_r16": typology_ref["contact_chain_r13_r16"],
                "path_rel": typology_ref["path_rel"],
                "role": typology_ref["role"],
                "r16_existence_blackdot": typology_ref["r16_existence_blackdot"],
                "sha256_measured": typology_ref["sha256_measured"],
                "sha256_prefix_expected":
                    typology_ref["sha256_prefix_expected"],
            },
            "consistency_assertion_measurements": seg_bytes,
        },
        "derived": "observation-guidance-r25.md",
        "derived_path_rel": "out/v3-tl2/calibration/observation-guidance-r25.md",
        "derived_sha256": derived_sha,
        "edit_list": [
            {"edit": 1, "kind": "标题行替换（轮次身份四处之一）",
             "expected_hits": 1, "old": OLD_TITLE, "new": NEW_TITLE},
            {"edit": 2,
             "kind": "round_id_constant bullet 替换（轮次身份四处之二）",
             "expected_hits": 1, "old": OLD_ROUND_ID_LINE,
             "new": NEW_ROUND_ID_LINE},
            {"edit": 3,
             "kind": "声明日期 bullet——基座落盘日期已为 2026-09-10，本任务"
                     "=确认无操作（no-op 确认，如实登记）（轮次身份四处之"
                     "三）",
             "expected_hits": 1, "old": DATE_LINE, "new": DATE_LINE,
             "noop_confirmed": True},
            {"edit": 4,
             "kind": "本轮性质行按判据内容轴口径重写（轮次身份四处之四）",
             "expected_hits": 1, "old": OLD_NATURE_LINE,
             "new": NEW_NATURE_LINE},
            {"edit": 5,
             "kind": "「本轮变更声明」节正文整体替换【任务枚举 8 项之外的"
                     "必要补入项，偏差如实登记】：冻结区断言要求小写 r23 仅"
                     "存「相对 observation-guidance-r23」恰 1 处+R23 系 "
                     "token 残留=0，基座变更声明节含 r19 血统引用与 R23T/"
                     "R23B/reader-r23/r23-prep-record token、不整体重写则"
                     "断言不可满足；s80 任务 5「变更声明节正文整体替换（任"
                     "务给定文本逐字）」先例同型",
             "expected_hits": 1, "old": OLD_CHANGES_PARA,
             "new": NEW_CHANGES_PARA,
             "content_sha256": hashing.sha256_text(NEW_CHANGES_PARA)},
            {"edit": 6,
             "kind": "§4 末尾增补弃权边界操作化条款（任务枚举之五；在 §5 "
                     "标题行之前插入；逐字冻结）",
             "expected_hits_insert_anchor": 1,
             "insert_anchor": CLAUSE_INSERT_ANCHOR,
             "region": "§4 末尾（r13 对照说明段之后、§5 标题行之前）",
             "text_full": CLAUSE_TEXT},
            {"edit": 7, "kind": "§6 示例旗 ID 前缀机械替换（top；恰 4 处）",
             "expected_hits": 4, "old": "R23T-", "new": "R25T-"},
            {"edit": 8, "kind": "§6 示例旗 ID 前缀机械替换（bottom；恰 1 处）",
             "expected_hits": 1, "old": "R23B-", "new": "R25B-"},
            {"edit": 9, "kind": "§6 示例 reader_id 前缀机械替换",
             "expected_hits": 1, "old": "reader-r23-", "new": "reader-r25-"},
        ],
        "mode": "mechanical_transform_derive",
        "verbatim_scope_note": (
            "冻结区=§2、§3（含 §3A）、§5（含 §5A）、§6 正文、§7 逐字与基"
            "座一致+§4=基座原文完整保留+仅末尾追加条款：§2 类别枚举、§3 位"
            "置口径（含邻域收窄判据）、§3A 类别判据示例、§5 courtyard 说明、"
            "§5A 渲染配色仪器注记、§7 格式对齐提示——r25 与 r23 逐字一致"
            "（脚本 substring 区块断言 fail-closed：「## 2. 类别枚举」→"
            "「## 4. 置信度与弃权」、「## 5. courtyard」→「## 6. 输出格"
            "式」、「## 7. 格式对齐提示」→文末三区块逐字节一致）；§4=基座 "
            "§4 全文（含量化判据 (i)(ii)(iii)、(iii-a) 可操作分辨条款、三"
            "路出口、反放宽条款原文——全句逐字原文仅于本记录 no_loosening_"
            "note 引用处登记）完整保留+仅末尾（§5 标题行之前）"
            "追加弃权边界操作化条款（区块等价断言 fail-closed）；§6=基座 "
            "§6+示例旗 ID 前缀机械替换（R23T-→R25T- 恰 4 处、R23B-→R25B- "
            "恰 1 处、reader-r23-→reader-r25- 恰 1 处）外逐字不变（§6 区块"
            "等价复核断言）；本轮指引内 R25T- 恰 4 处、R25B- 恰 1 处、"
            "reader-r25- 恰 1 处实测锚定；R23 系 token 残留=0（R23/R23T/"
            "R23B/reader-r23 全 0——替换+变更声明节重写后；小写 r23 仅存变"
            "更声明基座血统引用「相对 observation-guidance-r23」恰 1 处——"
            "r23 文件内保留 r19 引用同口径先例）；小写 r24 恰 1 处（本轮性"
            "质行「r24 not_instance_dominated 登记的下一归因轴执行轮」）；"
            "新增条款文本逐字在案（CLAUSE_TEXT needle 族逐一断言）；指引内"
            "零轮次结果数字（r24 实测数字 0.552381/0.692308/0.888889/"
            "0.01864/0.261904/0.09064 与 area_ratio/GT- 残留=0，基线数字仅"
            "入本编排侧记录）"),
        "zero_write_declaration": (
            "变换基座 observation-guidance-r23.md 零字节不动（本脚本对基座"
            "无任何写路径；实测哈希在 guidance_reuse.base_sha256，与开工实"
            "测 866b0157 锚 fail-closed 一致；收工二次复验）；本轮新建派生"
            "指引 observation-guidance-r25.md=机械变换产物（同参重建逐字节"
            "一致+防覆写护栏）——s70「r15 指引机械变换派生 r19 指引」/s80"
            "「r19→r23」先例同型"),
    }
    record["hypothesis_test"] = HYPOTHESIS_TEST
    record["instrument_change"] = {
        "changed": False,
        "declaration": (
            "本轮 prep 零重渲染、零 out/ 既有文件改动（四 PNG sha256_file "
            "实测=witness-r14b 登记值+任务给定全 64 位预期值双重比对；"
            "bottom 两板逐字节同 d7284259=两态同图如实声明；top 无配色 "
            "298bc620/b2f84524）；指引基座=observation-guidance-r23.md 只"
            "读零写入（866b0157）；本轮恰两个 out/ 新建文件="
            "observation-guidance-r25.md 与本记录"),
        "note": (
            "渲染与 r14/r15/r16/r18/r19/r20/r22/r23/r24 完全相同（"
            "renders-r14b 字节冻结，四 PNG 实测=witness-r14b 登记值），本"
            "轮唯一变更=判读指引 §4 末尾增补条款（非仪器侧）"),
        "renders": png_checks,
        "witness": (f"render-witness-r14b.json（{WITNESS_R14B_SHA_PREFIX}，"
                    "fail-closed 复核）"),
    }
    record["kind"] = "tl2_calibration_r25_prep_record"
    record["manipulated_factor"] = (
        "唯一操纵因素=判读指引 §4 末尾增补弃权边界操作化条款（criterion_"
        "boundary_operationalization；判据内容轴单点增补；observation-"
        "guidance-r25.md 由 observation-guidance-r23.md 866b0157 机械变换"
        "派生；条款全文逐字见 guidance_reuse.edit_list[5].text_full）；渲"
        "染（四图字节复用）/GT/阈值/协议与 §2/§3/§3A/§5/§5A/§6/§7 及 §4 "
        "原文零变更；changed_variables=1")
    record["measurement_design"] = {
        "comparison_set": {
            "note": (
                "比较集五行全部由盘上在案值多源装载交叉核对（fail-closed、"
                "非手抄）：r16=axis-plan baselines_registered.r16_baseline+"
                "run-r23 baseline_cross_check+run-r24 baseline_cross_check "
                "三源一致；r19=run-r22 r19_reference_tuple+run-r23 r19_"
                "reference_tuple+run-r24 r19_row（live==registered）+"
                "round24 台账 r19_axis3 多源一致；r22=run-r22 r22_m_tuple_"
                "6dp+run-r24 r22_row（live==registered）+round24 台账 r22_"
                "repeat 三源一致；r23=run-r23 r23_m_tuple_6dp+run-r24 r23_"
                "row（live==registered）+round24 台账 r23_repeat 三源一致；"
                "r24=run-r24 r24_m_tuple_6dp（live 装载、不手工抄）+"
                "round24-dev-record this_round_measured+round24 台账 r24_"
                "expansion 三源一致"),
            "rows": [
                {"role": "主基线=零变更最新轮", "round": "r16_baseline",
                 "tuple": M_TUPLE_R16},
                {"role": "轴3 单变量轮（历史最佳 M1）", "round": "r19",
                 "tuple": M_TUPLE_R19},
                {"role": "同指引重复轮（r16 先例）", "round": "r22",
                 "tuple": M_TUPLE_R22},
                {"role": "报告框收敛归因轮（框宽排除在案）", "round": "r23",
                 "tuple": M_TUPLE_R23},
                {"role": "实例群扩容归因轮（实例群排除在案、本轮设计出处）",
                 "round": "r24_expansion", "tuple": m_tuple_r24_live},
            ],
            "scope": (
                "M 元组比较为 development 域描述性对照（axis ledger 延续登"
                "记、rubric 口径）；跨轮实例群漂移混杂照旧声明；M4 跨口径"
                "粒度差异如实单列（见 m_tuple_definitions.M4 与 "
                "adjudication.metric_lesson_separate）；r24 行含 "
                "split_half_M1_diff 第五键（r24 首启键、本轮沿用）"),
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
                    "预注册、不得事后调整，沿 r24 冻结口径），计算一轮 "
                    "joint 结果；同时如实给出 per-metric 实例间范围（min.."
                    "max）；代表配置 joint 结果、per-metric 实例间范围、逐"
                    "实例原始记录（item 1）三者并列如实呈现，不合并、不挑"
                    "优；APR-0011 阈值零改动"),
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
                "差异=v1.3 扩容口径显式登记（r24 延续）；阈值 0.261904=r16 "
                "基线历史口径在案值原样引用不改写（跨口径比较=描述性、如实"
                "声明）"),
            "m3_rubric_lineage_note": (
                "M3 分型件 rubric 词元口径链锚（先核对后引用；任务括号映射"
                "如实登记）：abstain-typology-r13-r16.json（6dadac8d 全 64 "
                "位实测锚）装载+链回放先核对在案——r13–r16=8/15/5/10 链的"
                "在件键位=matrix.round_totals.r13–r16.families.contact"
                "（contact 族；分型件族标签如实登记，run-r24 baseline_cross_"
                "check.r16_contact_live_replay 同链交叉一致）；黑点族（M3）"
                "同件交叉锚=r16 existence_blackdot=12 == axis-plan "
                "r16_baseline.M3_blackdot_abstain_flags_rubric=12（rubric "
                "词元口径同血统）——M3 的 n=6 黑点族口径与 r24 完全同构、"
                "零改动"),
            "split_half_M1_diff": (
                "|M1(i1–i3 双视图聚合) − M1(i4–i6 双视图聚合)|（6 位定点整"
                "数交叉相乘比较）"),
            "split_half_operationalization_note": (
                "双视图=applied+prep1 两态合并聚合：a_6dp=round(i1–i3 弃权"
                "数×1000000/i1–i3 旗数)、b_6dp 同法（i4–i6）——6 位定点整"
                "数、不做浮点除法；split_half_6dp=|a_6dp−b_6dp|；阈值="
                "0.09064 的 6 位定点=90640 整数（r24 首启参照、在案锚=dev22"
                "=9 处/dev23=6 处 raw text 计数）；本轮=机制观察单列、不进"
                "分支判定（与 r24 的差异如实登记）"),
            "scope": (
                "全部=24 派次全口径（非代表配置子集）；单位=旗标条数（M3）"
                "或 6 位定点率（M1/M2/M4/split_half_M1_diff）；与 axis-"
                "experiment-plan-r17-r20 benefit_metrics 及分型件同血统按 "
                "n=6 扩写；五键口径与 r24-prep-record measurement_design."
                "m_tuple_definitions 完全同构、逐字沿袭（仅 m3_rubric_"
                "lineage_note/split_half_operationalization_note 按本轮链"
                "锚装载与单列口径补充登记）"),
        },
        "preregistration_declaration": (
            "本节先于 R25 盲读冻结（本记录=预注册件；evaluation-protocol-v1 "
            "§4 口径：轮次开始后不得增删）；五条逐条预注册+M 元组 n=6 口径"
            "与 r24 完全同构（M1/M2 双视图×6 实例聚合、M3=分型件 rubric 词"
            "元口径[abstain-typology-r13-r16.json=6dadac8d 装载+r13–r16=8/"
            "15/5/10 链回放先核对在案]、M4=12 格逐格率极差、split_half_M1_"
            "diff=|M1(i1–i3)−M1(i4–i6)| 双视图聚合），聚合口径全部如实并"
            "列、不二选一、不挑优（items 沿 r24-prep-record measurement_"
            "design.items 同一口径按本轮改写：24 派次=2 板×2 视图×6 实例、"
            "12 智能体各包同侧两板、编号同实例同侧跨板连续；reader 前缀 "
            "R25T/R25B=随本轮指引 §6 落盘固化；图像=renders-r14b 四图（字"
            "节复用）；聚合口径与 s71/s74/s77/s82/s86 比较脚本同血统；代表"
            "配置/逐实例/双口径分列）；比较集=r16 基线+r19+r22+r23+r24 实"
            "测元组（五行全部盘上在案值多源装载交叉核对、r24 行从 run-r24="
            "8a9bdb7d live 装载锚定、不手工抄）"),
    }
    record["no_instrument_change"] = True
    record["no_loosening_note"] = (
        "弃权边界操作化条款不放宽判据：条款只把弃权边界操作化为三问依次自"
        "问的执行细则——弃权→低 confidence 非弃权旗=旗仍设立、非「判正"
        "常」（三问之(3)「否→必须设非弃权旗，confidence 如实取低值——把握"
        "不足本身不构成弃权理由」方向上为收紧弃权出口、反放宽条款原文不变）；"
        "反放宽条款「" + NO_LOOSENING_SENTENCE + "」随 §4 基座原文逐字保留（本记录恰引用 1 次）；"
        "§2/§3/§3A/§5/§5A/§6/§7 与 §4 原文零变更（§2/§3/§5/§6/§7 substring "
        "区块断言+§4 区块等价断言 fail-closed），判据侧零措辞调整空间；显式"
        "防止「为降弃权率而操作化」的动机误读：本轮字母只看个体散收敛（M4），"
        "不看 M1 降不降——M1 降不构成 criterion_dominated 证据（见 "
        "adjudication.m1_m2_gate_separate），G1 守门照常独立计算；三问顺序"
        "不得颠倒、三问之外的任何理由不构成弃权依据（条款原文）；本轮三支"
        "判据（criterion_dominated/not_criterion_dominated/guard_"
        "interrupted）只用于归因方向，不触碰 APR-0011 门（gt_recall≥0.75/"
        "seed_match_rate≥0.5/abstain_rate≤0.5）与任何阈值常量（"
        "CONTAINMENT_MIN/AREA_RATIO_MAX，只作口径引用）——门照常独立计算；"
        "不构成任何阈值反向放宽")
    record["no_visual_reading"] = True
    record["pre_round_review"] = {
        "basis": (
            "免视觉评审声明：指引文本变更但渲染零变更（renders-r14b 四图全 "
            "64 位实测锚与 witness-r14b 登记值双重比对一致）——唯一新增判"
            "读面=§4 末尾弃权边界操作化条款（纯判据执行细则文本、零新图像"
            "内容）；r23 先例=指引变更轮免视觉评审照常执行（r23-prep-record "
            "同 status 在案）；授权链=round24-dev-record next_candidate_"
            "suggestion options[1]（原文逐字见 user_directive_note）+用户 "
            "2026-09-10 拍板选项(b)定向判据内容轴；预注册先于盲读冻结（本"
            "记录）"),
        "status": "satisfied_by_plan",
    }
    record["protected_files_verification"] = {
        "hashes": protected_hashes,
        "note": (
            "受保护文件全 64 位 sha256 实测断言（本脚本开工/收工各验一次；"
            "零改动红线；fail-closed）"),
        "role": ("红线执行证据（保护文件零改动+datasets/ 只读+out/ 只读除"
                 "声明新文件）"),
    }
    record["protocol_amendment"] = {
        "blind_read_execution": (
            "24 次盲读 = 4 视角格（applied-top/applied-bottom/prep1-bottom/"
            "prep1-top）× 6 实例（i1–i6）= 12 个 reader 智能体（top 侧 6 + "
            "bottom 侧 6），每个 agent 串行读同侧两板（先 applied 后 "
            "prep1、flag_id 跨板连续编号）产出 2 件 reader-raw-r25-*.txt；"
            "两波次串行（波1=top 侧 6 agent、波2=bottom 侧 6 agent）——照 "
            "r24 同构。reader 上下文=指引文件（observation-guidance-r25.md="
            "本轮落盘新指引）+该侧两张 PNG+派发命名指令（round 2026-09-10-"
            "r25、前缀 R25T/R25B、reader_id=reader-r25-top-iK / "
            "reader-r25-bottom-iK）；v1.2 工具行为规约硬性条款照抄（纯 "
            "Read 内联判读、禁止任何程序化图像处理）；零 GT、零历史判读件"
            "（含 r22–r24 reader-raw-*）、零诊断/探针内容、零 r23/r24 现"
            "象描述注入（本记录所载 r24 事实转述为编排侧引用，不进任何 "
            "reader 上下文）；输出 JSON schema 同 r23/r24（reader_id/"
            "per_image[{image,flags[{flag_id,category,confidence,abstain,"
            "frame_box_pct,location_evidence}]}]/reading_notes）；Write 工"
            "具落盘、禁长 heredoc；跨实例/跨视角禁止交流（24 次盲读相互独"
            "立、不得交换判读信息——独立性是多实例协议的前提，亦为本轮归"
            "因裁决有效性的前提）"),
        "changes": [],
        "naming": (
            "reader_id=reader-r25-{top,bottom}-i{1..6}；flag_id 前缀 R25T/"
            "R25B=随本轮指引 §6 落盘固化（本轮指引由 r23 基座机械变换派生、"
            "§6 示例前缀已机械替换为 R25T-/R25B-——派发层命名与指引 §6 一"
            "致、无前缀差异登记需求；r23 先例同型。对照 r22/r24：指引字节"
            "复用致派发层覆盖=前缀差异登记在案；本轮为落盘固化路径）；实例"
            "间编号独立，同实例同侧跨板连续"),
        "protocol_id": "evaluation-protocol-v1",
        "scope_note": (
            "本轮协议侧零变更（v1/v1.1/v1.2+v1.3 维持、无新增附录、"
            "changes=[]）；in_calibrated_range 恒 False 不变"),
        "v1_1_semantics": (
            "每视角多独立实例+聚合口径：实例层主记录、视角层中位数/最小/"
            "最大聚合、GT 匹配 union/agreement 双口径并列、联合门代表配置+"
            "实例间范围并列（measurement_design 五条）；本轮 n=6 执行（v1.1 "
            "原文 n=3 口径由 v1.3 附录推广、v1.1 语义不改）"),
        "v1_2_semantics": (
            "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派发指"
            "令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/放大/像"
            "素分析/衍生图像生成等）；判读只允许以 Read 工具查看原图（同一"
            "原图可重复查看）」——仪器行为钉住；属派发层，读者上下文=指引+"
            "同侧两张 PNG+派发指令（含规约条款），零 GT；不影响判读语义——"
            "分类判据零变更，仅输入手段固定"),
        "v1_3_semantics": (
            "r24 轮新增的 n 扩容附录本轮原样沿用（每视图实例数 3→6、24 派"
            "次、两波次串行、聚合口径 n=6 推广：union≥1/6、agreement≥4/6 "
            "过半数、代表配置=下中位序位实例）；本轮无新增版本、无附录修"
            "改——v1.3 语义以 r24-prep-record protocol_amendment 冻结件为"
            "准"),
        "v1_file_preserved": {
            "note": (
                "v1 原文零字节保留（r11–r24 轮同口径在案登记，本脚本 "
                "fail-closed 在盘+哈希复核）；v1.3=r24 记录内附录、本轮无"
                "新增协议文件；evaluation-protocol-v2.md=holdout 协议冻结"
                "件（s79 登记在案）本轮不启用——v2 生效≠holdout 启动，"
                "holdout 暂不启动=用户 2026-09-10 拍板"),
            "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
            "sha256_measured": protocol_v1_sha,
            "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
            "zero_byte_preserved": True,
        },
        "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
        "version": "v1.3 维持（v1/v1.1/v1.2 继承不改+v1.3 n=6 附录沿用 r24；"
                   "本轮协议侧零变更、无新增附录）",
    }
    record["read_prohibition_compliance"] = True
    record["read_prohibition_note"] = (
        "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+magic，"
        "零内容判读、零像素读取）、ground-truth-*、reader-raw-*、derivation-"
        "log-*、任何 compare/评估产物、diag 内容（零读取）；本脚本只读输入="
        "observation-guidance-r23.md（机械变换基座；866b0157 全 64 位锚 "
        "fail-closed，只读零写入——派生文本由本脚本机械变换构造）、round24-"
        "dev-record.json（1a344edf 两父之二；仅读 axis_experiment_ledger "
        "实测元组/台账行、g2_bifurcation_record 计数/字母/G1 锚（GT 字段不"
        "转录）、hypothesis_test_i.verdict、next_candidate_suggestion 选项"
        "(b)原文与聚合稳/个体散在案原文——本轮设计出处与合法性依据）、"
        "round22-dev-record.json（b4b8fbe9；仅读 drift 0.09064 raw text 计"
        "数）、round23-dev-record.json（343a6747；仅读 drift 0.09064 raw "
        "text 计数）、axis-experiment-plan-r17-r20.json（b6ec6467；仅读 "
        "baselines_registered r16 基线四键=M4 阈值锚）、abstain-typology-"
        "r13-r16.json（6dadac8d；仅读 matrix.round_totals 分族计数链=分型"
        "件 rubric 口径链回放）、calibration-run-r24.json（8a9bdb7d；仅读 "
        "hypothesis_test 顶层判据冻结值字段+guard_channel+verdict+baseline"
        "_cross_check——r24 元组 live 装载源；GT 匹配与逐旗明细不读取、不"
        "入记录）、calibration-run-r23.json（15f58350；同上口径）、"
        "calibration-run-r22.json（80a12c05；同上口径）、r23-prep-record."
        "json（3c42ace7；机械变换派生先例血统锚）、r24-prep-record.json"
        "（760af49f；结构血统与 25 键镜像来源+descriptive_boundary_note "
        "照抄源）、render-witness-r14b.json（b63771f9 锚 fail-closed；四 "
        "PNG 见证登记值）、evaluation-protocol-v1.md（仅在盘+哈希复核，锚="
        "22dc7337）、evaluation-protocol-v2.md（仅在盘+哈希复核，锚="
        "365b67ef；holdout 冻结件本轮不启用）；保护三文件（pcbflow/cli.py/"
        "pcbflow/config.py/toolchain_lock.json）仅哈希（开工/收工各验一"
        "次）；renders-r14b 四 PNG 仅哈希+magic（渲染字节冻结以 witness 登"
        "记哈希+任务给定全 64 位预期值双重比对为准）；本轮恰三个新建文件="
        "scripts/s88_calibration_r25_prep.py（生成器本体）与 observation-"
        "guidance-r25.md、r25-prep-record.json（本轮仅有的两个 out/ 新建"
        "文件；本轮无探针/诊断脚本）；reader 派发（后续编排侧执行）上下文="
        "observation-guidance-r25.md+同侧两张 PNG（renders-r14b）+派发指令"
        "（round 2026-09-10-r25、前缀 R25T/R25B=随指引落盘、reader_id="
        "reader-r25-{top,bottom}-i{1..6}、v1.2 工具行为规约硬性条款照"
        "抄），零 GT、零历史判读件、零诊断/探针内容、零 r23/r24 现象描述"
        "注入、零指引之外的解释；视觉判读禁止由编排/收口包兼任；跨实例/"
        "跨视角禁止交流（24 次盲读相互独立、不得交换判读信息——独立性是"
        "多实例协议的前提，亦为本轮归因裁决有效性的前提）。")
    record["round_id_constant"] = ROUND_ID
    record["round_label"] = ROUND_LABEL
    record["round_nature"] = (
        "判据内容轴归因轮（§4 末尾弃权边界操作化条款轮；非判据调参轴重开——"
        "axis-experiment-plan-r17-r20 三轴实验收束决议与轴停止决议不变；"
        "r24 not_instance_dominated 登记的下一归因轴执行轮；三混杂轴归因链"
        "：r23 框宽排除→r24 实例群排除→r25 判据内容；本轮=第二十五轮）："
        "唯一实验变量=判读指引 §4 末尾增补弃权边界操作化条款（observation-"
        "guidance-r25.md 由 observation-guidance-r23.md 866b0157 机械变换"
        "派生：轮次身份四处更新（标题/round_id_constant/声明日期[基座已是 "
        "2026-09-10=确认无操作]/本轮性质行）+变更声明节正文整体重写（s80 "
        "任务 5 先例补入项、偏差如实登记）+§4 末尾增补条款（§5 标题行之前"
        "插入、逐字）+§6 示例旗 ID 前缀机械替换 R23T-→R25T-（恰 4 处）、"
        "R23B-→R25B-（恰 1 处）、reader-r23-→reader-r25-（恰 1 处）；§2/§3"
        "（含 §3A）/§5（含 §5A）/§6 正文/§7 与基座逐字一致、§4=基座原文完"
        "整保留+仅末尾追加条款——脚本 substring 区块断言 fail-closed、反放"
        "宽条款逐字保留、R23 系 token 残留=0、新增条款恰 1 次）；渲染零变更"
        "=renders-r14b 四图字节复用（四 PNG sha256_file 实测与 render-"
        "witness-r14b.json 登记值+任务给定全 64 位预期值双重 fail-closed 比"
        "对一致，即 r14–r24 轮盲读所用同一批文件，见 instrument_change；"
        "bottom 两态同图如实声明）；GT/阈值/协议零变更（13 条冻结、v1/v1.1"
        "/v1.2 继承不改+v1.3 n=6 附录沿用 r24；evaluation-protocol-v2="
        "holdout 冻结件本轮不启用——v2 生效≠holdout 启动、holdout 暂不启"
        "动=用户 2026-09-10 拍板）；changed_variables=1（§4 末尾弃权边界操"
        "作化条款，见 changed_variables[0]）；执行 round24-dev-record 下一"
        "候选建议（b）（判据内容轴归因预注册轮——原文逐字见 user_directive_"
        "note）+用户 2026-09-10 拍板选项(b)定向判据内容轴；r24 字母裁决="
        "not_instance_dominated 维持不改写、r23=confounded、r22=regressed "
        "亦维持、不得回溯改判既往轮次（r8–r24 字母裁决维持不变）；r23 指引"
        "已在盘冻结、本轮只读零写入（r25=本轮落盘新指引）；盲读由编排侧在"
        "本记录之后以 24 次独立实例盲读执行（12 个 reader 智能体各包同侧两"
        "板=24 派次、照 r24 同构）")
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
                "即 r14–r24 轮盲读所用同一批文件；本轮零重渲染、零仪器变更"),
            "pngs": png_checks,
            "witness": (
                f"render-witness-r14b.json（{WITNESS_R14B_SHA_PREFIX}，fail-closed 复核）"),
        },
        "判读指引保留区逐字保留（observation-guidance-r25.md 由 r23 基座 "
        "866b0157 机械变换派生；脚本 substring 区块断言 fail-closed）："
        "§2 类别枚举、§3 位置口径（含邻域收窄判据）、§3A 类别判据示例、"
        "§5 courtyard 说明、§5A 渲染配色仪器注记、§6（除示例旗 ID 前缀机"
        "械替换外逐字不变）、§7 格式对齐提示与基座逐字一致；§4=基座原文完"
        "整保留+仅末尾追加弃权边界操作化条款（反放宽句恰 1 次在案）",
        "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，GT 侧"
        "不再有候选，r9–r24 延续引用）",
        "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_rate"
        "≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作口径引"
        "用；几何门照常独立计算）；M4 阈值锚 0.261904 与 drift 参照 "
        "0.09064=在案历史值原样引用、零修改",
        "评估协议：v1/v1.1/v1.2 继承不改（evaluation-protocol-v1.md 零字"
        "节保留、本轮不新建协议文件；v1.3 n=6 附录沿用 r24、本轮无新增附"
        "录；evaluation-protocol-v2=holdout 冻结件本轮不启用，见 protocol_"
        "amendment）",
        "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口径在图"
        "像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
        "度量设计与聚合口径：与 r24 完全同构（M 元组 n=6 口径五键照抄；仅"
        "轮次标识、reader 前缀与指引文件名按 r25 改写；split_half_M1_diff "
        "本轮=机制观察单列、不进分支判定——差异如实登记）",
    ]
    record["user_directive_note"] = (
        "用户 2026-09-10 拍板选项(b)定向判据内容轴→同日暂停→同日「请继续 "
        "r25」恢复（本记录=先于盲读冻结的预注册件）。r24 事实锚（"
        "calibration-run-r24.json 8a9bdb7d / round24-dev-record.json "
        "1a344edf 实测在案）：M=(0.552381, 0.692308, 28, 0.888889、split_"
        "half_M1_diff=0.018640)（M1=58/105、M2=18/26）、G2 几何门出局条目="
        "0（资格门满足；r19=0/r22=2/r23=1/r24=0 对照在案）、G1 维持（六 "
        "bottom 实例 courtyard 非弃权旗全=0）、归因三支判据字母裁决="
        "not_instance_dominated（唯一正式裁决、轮后不改写）——实例群轴单变"
        "量测毕（离散超出抽样尺度）、下一归因轴=判据内容；round24-dev-"
        "record next_candidate_suggestion options[1] 原文：「" +
        CANDIDATE_B_OPTION + "」——本轮=该候选的执行轮（判据内容轴单变量"
        "操作化归因）；r24 字母裁决=not_instance_dominated 维持、轮后不改"
        "写，r23=confounded、r22=regressed 亦维持；holdout 暂不启动（"
        "evaluation-protocol-v2=holdout 冻结件本轮不启用——v2 生效≠holdout "
        "启动）；预注册后执行")
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
    for path in (GUIDANCE_R23, DEV_RECORD_R22, DEV_RECORD_R23, DEV_RECORD_R24,
                 AXIS_PLAN, TYPOLOGY, R23_PREP_RECORD, R24_PREP_RECORD,
                 RUN_R22, RUN_R23, RUN_R24, WITNESS_R14B, EVAL_PROTOCOL_V1,
                 EVAL_PROTOCOL_V2):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件 GUIDANCE_R25 / RECORD 不做前置硬拒绝：落盘阶段防覆写护栏按
    # 红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等
    # 通过（零覆写）。

    # ---- 全 64 位锚（任何写路径之前；fail-closed）----
    guidance_sha = _require_full_sha(GUIDANCE_R23, GUIDANCE_R23_SHA,
                                     "observation-guidance-r23.md")
    dev24_sha = _require_full_sha(DEV_RECORD_R24, DEV_RECORD_R24_SHA,
                                  "round24-dev-record.json")
    axis_sha = _require_full_sha(AXIS_PLAN, AXIS_PLAN_SHA,
                                 "axis-experiment-plan-r17-r20.json")
    typology_sha = _require_full_sha(TYPOLOGY, TYPOLOGY_SHA,
                                     "abstain-typology-r13-r16.json")
    run24_sha = _require_full_sha(RUN_R24, RUN_R24_SHA,
                                  "calibration-run-r24.json")

    # ---- 前缀锚 ----
    dev22_sha = _require_prefix_sha(DEV_RECORD_R22, DEV_RECORD_R22_SHA_PREFIX,
                                    "round22-dev-record.json")
    dev23_sha = _require_prefix_sha(DEV_RECORD_R23, DEV_RECORD_R23_SHA_PREFIX,
                                    "round23-dev-record.json")
    r23_record_sha = _require_prefix_sha(R23_PREP_RECORD,
                                         R23_PREP_RECORD_SHA_PREFIX,
                                         "r23-prep-record")
    r24_record_sha = _require_prefix_sha(R24_PREP_RECORD,
                                         R24_PREP_RECORD_SHA_PREFIX,
                                         "r24-prep-record")
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
    dev24_text = DEV_RECORD_R24.read_text(encoding="utf-8")

    # ---- 结构探测（实测锚与授权链锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    run24 = json.loads(RUN_R24.read_text(encoding="utf-8"))
    run23 = json.loads(RUN_R23.read_text(encoding="utf-8"))
    run22 = json.loads(RUN_R22.read_text(encoding="utf-8"))
    dev24 = json.loads(dev24_text)
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    typology = json.loads(TYPOLOGY.read_text(encoding="utf-8"))
    r23_record = json.loads(R23_PREP_RECORD.read_text(encoding="utf-8"))
    r24_record = json.loads(R24_PREP_RECORD.read_text(encoding="utf-8"))
    if r23_record.get("kind") != "tl2_calibration_r23_prep_record" or \
            r23_record.get("round_label") != "r23" or \
            r23_record.get("schema_version") != "3.0":
        _fail("r23-prep-record 机械变换先例件结构漂移")
    if r24_record.get("kind") != "tl2_calibration_r24_prep_record" or \
            r24_record.get("round_label") != "r24" or \
            r24_record.get("schema_version") != "3.0":
        _fail("r24-prep-record 结构血统件结构漂移")

    probe_witness(witness)
    png_checks = check_renders_byte_freeze(witness)
    guidance_ref = probe_guidance_r23(guidance_text, guidance_sha)
    axis_ref = probe_axis_plan(axis_plan, axis_sha)
    typology_ref = probe_typology(typology, typology_sha)
    run24_ref = probe_run_r24(run24, run24_sha)
    run23_ref = probe_run_r23(run23, run23_sha)
    run22_ref = probe_run_r22(run22, run22_sha)
    dev24_ref = probe_dev_record_r24(dev24, dev24_sha, dev24_text,
                                     run24_ref["m_tuple_r24_live"])
    drift_counts = probe_drift_anchor(dev22_text, dev23_text)

    # descriptive_boundary_note 照抄血统源核对（fail-closed）
    lineage_note = (r24_record.get("hypothesis_test", {})
                    .get("adjudication", {})
                    .get("descriptive_boundary_note", ""))
    if DESCRIPTIVE_BOUNDARY_NOTE != lineage_note:
        _fail("descriptive_boundary_note 未照抄 r24-prep-record 血统原文")

    # ---- 判据逐字断言链：预注册判据原文→json.loads→常量→记录字段 ----
    ht_text = _json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != \
            "r24-not-instance-dominated-criterion-boundary-operationalization" \
            "-attribution":
        _fail("hypothesis_test.hypothesis_id 不符")
    adj = HYPOTHESIS_TEST["adjudication"]
    if set(adj.keys()) != {"criterion_dominated", "not_criterion_dominated",
                           "guard_interrupted", "letter_branch_map",
                           "g2_observation_separate", "m1_m2_gate_separate",
                           "mechanism_observation_separate",
                           "metric_lesson_separate",
                           "fixed_point_comparison_note",
                           "descriptive_boundary_note",
                           "three_way_bookkeeping"}:
        _fail(f"adjudication 三支+单列结构不符：{sorted(adj.keys())}")
    if adj["criterion_dominated"] != ADJ_CRITERION_DOMINATED or \
            adj["not_criterion_dominated"] != ADJ_NOT_CRITERION_DOMINATED or \
            adj["guard_interrupted"] != ADJ_GUARD_INTERRUPTED:
        _fail("归因三支判据原文与冻结常量不一致（逐字要求被破坏）")
    for needle in REQUIRED_NEEDLES:
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值/口径 {needle!r}"
                  f"（逐字要求破坏）")

    # ---- 定点整数自证（零浮点路径）----
    if 928571 - 666667 != M4_ANCHOR_6DP:
        _fail("M4 阈值锚 6 位定点自证失败：928571−666667 != 261904")
    if 862069 - 771429 != DRIFT_6DP:
        _fail("drift 6 位定点自证失败：862069−771429 != 90640")
    if int(round(M4_ANCHOR * 1000000)) != M4_ANCHOR_6DP:
        _fail("M4_ANCHOR_6DP 与 0.261904 不一致")
    if G2_R24 != 0 or G2_R23 != 1 or G2_R22 != 2 or G2_R19 != 0:
        _fail("G2 对照链常量不符（r19=0/r22=2/r23=1/r24=0）")

    # ---- 指引机械变换 + 冻结区断言 ----
    derived_text = derive_guidance_r25(guidance_text)
    seg_bytes = assert_guidance_r25(derived_text, guidance_text)
    derived_sha = hashing.sha256_text(derived_text)
    derived_bytes = len(derived_text.encode("utf-8"))

    # ---- 记录构建 + 断言 ----
    build_kwargs = dict(
        guidance_ref=guidance_ref, dev24_ref=dev24_ref, axis_ref=axis_ref,
        typology_ref=typology_ref, run24_ref=run24_ref, run23_ref=run23_ref,
        run22_ref=run22_ref, r23_record_sha=r23_record_sha,
        r24_record_sha=r24_record_sha, witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha, protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks, drift_counts=drift_counts,
        derived_sha=derived_sha, derived_bytes=derived_bytes,
        seg_bytes=seg_bytes, m_tuple_r24_live=run24_ref["m_tuple_r24_live"],
        protected_hashes=protected_hashes)
    record = build_record(**build_kwargs)
    # 结构镜像断言：顶层键集合=r24-prep-record 25 键逐键镜像（恰同、不少不多）
    missing = sorted(set(r24_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r24_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r24-prep-record 镜像不符：少={missing}，"
              f"多={extra}（预期 25 键逐键一致）")
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
    if cv["id"] != "guidance-s4-abstain-boundary-operationalization-clause" \
            or cv["instrument_change"] is not False:
        _fail("changed_variables[0] 不符（唯一操纵因素=§4 末尾弃权边界操"
              "作化条款）")
    if record["guidance_reuse"]["mode"] != "mechanical_transform_derive":
        _fail("guidance_reuse.mode 必须为 mechanical_transform_derive")
    if record["guidance_reuse"]["base_sha256"] != GUIDANCE_R23_SHA:
        _fail("guidance_reuse.base_sha256 与 866b0157 锚不符")
    if record["guidance_reuse"]["derived_sha256"] != derived_sha:
        _fail("guidance_reuse.derived_sha256 与派生实测不符")
    bs = record["guidance_reuse"]["byte_size"]
    if (bs["base"], bs["derived"]) != (GUIDANCE_R23_BYTES, derived_bytes) or \
            bs["delta"] != derived_bytes - GUIDANCE_R23_BYTES:
        _fail("guidance_reuse.byte_size 与实测不符")
    if record["round_id_constant"] != ROUND_ID or \
            record["round_label"] != ROUND_LABEL or \
            record["declared_date"] != DATE_CONSTANT:
        _fail("轮次标识不符（2026-09-10-r25 / r25 / 2026-09-10）")
    rn = record["round_nature"]
    for needle in ("判据内容轴归因轮", "唯一实验变量",
                   "§4 末尾增补弃权边界操作化条款", "非判据调参轴重开",
                   "轴停止决议不变", "r24 not_instance_dominated 登记的下一"
                   "归因轴执行轮", "机械变换派生", "866b0157", "渲染零变更",
                   "字节复用", "GT/阈值/协议零变更", "changed_variables=1",
                   "not_instance_dominated 维持不改写", "24 次独立实例盲读",
                   "确认无操作"):
        if needle not in rn:
            _fail(f"round_nature 缺「{needle}」声明")
    mf = record["manipulated_factor"]
    for needle in ("弃权边界操作化条款", "criterion_boundary_operationalization",
                   "866b0157", "changed_variables=1"):
        if needle not in mf:
            _fail(f"manipulated_factor 缺「{needle}」声明")
    if CLAUSE_TEXT not in mf and \
            CLAUSE_TEXT not in record["guidance_reuse"]["edit_list"][5].get(
                "text_full", ""):
        _fail("弃权边界操作化条款全文未逐字入件")
    nl = record["no_loosening_note"]
    for needle in ("不放宽判据", "把握不足本身不构成弃权理由",
                   "为降弃权率而操作化", "CONTAINMENT_MIN/AREA_RATIO_MAX",
                   NO_LOOSENING_SENTENCE):
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
                "M4_top_per_instance_rate_range", "split_half_M1_diff",
                "m3_rubric_lineage_note"):
        if key not in mtd:
            _fail(f"m_tuple_definitions 缺 {key}")
    if "12 派次" not in mtd["M1_top_aggregate_abstain_rate"] or \
            "12 个实例率" not in mtd["M4_top_per_instance_rate_range"] or \
            "0.09064" not in mtd["split_half_operationalization_note"] or \
            "6 位定点整数交叉相乘比较" not in mtd["split_half_M1_diff"] or \
            "8/15/5/10" not in mtd["m3_rubric_lineage_note"]:
        _fail("M 元组 n=6 口径声明不完整")
    rows = md["comparison_set"]["rows"]
    if [r["round"] for r in rows] != ["r16_baseline", "r19", "r22", "r23",
                                      "r24_expansion"]:
        _fail("comparison_set 比较集行不符")
    if (rows[0]["tuple"], rows[1]["tuple"], rows[2]["tuple"],
            rows[3]["tuple"]) != (M_TUPLE_R16, M_TUPLE_R19, M_TUPLE_R22,
                                  M_TUPLE_R23):
        _fail("comparison_set 元组值不符")
    if rows[4]["tuple"] != run24_ref["m_tuple_r24_live"]:
        _fail("comparison_set r24 行与 run-r24 live 装载不符")
    # protocol_amendment v1.3 维持、本轮零变更
    pa = record["protocol_amendment"]
    if "v1.3" not in pa["version"] or pa["changes"] != []:
        _fail("protocol_amendment 必须为 v1.3 维持（本轮协议侧零变更）")
    if "24 次盲读" not in pa["blind_read_execution"] or \
            "R25T/R25B" not in pa["blind_read_execution"] or \
            "reader-r25-top-iK" not in pa["blind_read_execution"] or \
            "禁长 heredoc" not in pa["blind_read_execution"]:
        _fail("protocol_amendment.blind_read_execution 缺盲读执行计划口径")
    if pa["v1_file_preserved"]["zero_byte_preserved"] is not True:
        _fail("v1_file_preserved.zero_byte_preserved 必须为真")
    # pre_round_review 免视觉评审声明（r23 先例）
    if record["pre_round_review"]["status"] != "satisfied_by_plan":
        _fail("pre_round_review.status 不符（r23 指引变更轮免视觉评审先例）")
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
    rebuild = build_record(**build_kwargs)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r25-prep-record")

    # ---- 落盘 1/2：observation-guidance-r25.md（防覆写护栏）----
    derived_b = derived_text.encode("utf-8")
    if GUIDANCE_R25.exists():
        if GUIDANCE_R25.read_bytes() != derived_b:
            _fail("observation-guidance-r25.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r25-prep] 重跑自证：observation-guidance-r25.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R25.write_bytes(derived_b)
        if GUIDANCE_R25.read_bytes() != derived_b:
            _fail("回读不一致: observation-guidance-r25.md")

    # ---- 落盘 2/2：r25-prep-record.json（防覆写护栏；派生指引 sha 已实测
    # 入 record——derived_sha 来自 sha256_text(derived_text)，与落盘字节同
    # 源，此处再以 sha256_file 交叉验证）----
    if hashing.sha256_file(str(GUIDANCE_R25)) != derived_sha:
        _fail("落盘后 observation-guidance-r25.md sha256_file 与 sha256_"
              "text 口径不一致（换行或编码漂移）")
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r25-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r25-prep] 重跑自证：r25-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r25-prep-record.json")

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
        _fail("收工基座指引 hash 与开工不一致（r23 指引零触碰红线被破坏）")

    # ---- 汇总打印 ----
    print("[r25-prep] 保护三文件开工/收工双验 PASS：pcbflow/cli.py="
          f"{CLI_PY_SHA[:8]}、pcbflow/config.py={CONFIG_PY_SHA[:8]}、"
          f"toolchain_lock.json={TOOLCHAIN_LOCK_SHA[:8]}（全 64 位实测一致）")
    print("[r25-prep] 机械变换锚 PASS：observation-guidance-r23.md="
          f"{guidance_sha}（866b0157，只读零写入，{GUIDANCE_R23_BYTES} B）；"
          f"9 组锚定编辑全部恰命中（含声明日期 no-op 确认与变更声明节必要"
          f"补入项）；冻结区断言 PASS（§2/§3/§5/§6/§7 逐字、§4=原文+仅末尾"
          f"追加条款、反放宽句恰 1 次、R23 系残留=0、小写 r23 恰 1 处、零"
          f"轮次结果数字）")
    print("[r25-prep] 字节冻结锚 PASS：renders-r14b 四图=applied-top "
          f"{PNG_APPLIED_TOP_SHA[:8]}/prep1-top {PNG_PREP1_TOP_SHA[:8]}/"
          f"applied-bottom {PNG_APPLIED_BOTTOM_SHA[:8]}/prep1-bottom "
          f"{PNG_PREP1_BOTTOM_SHA[:8]}（bottom 两态同图；全 64 位+witness "
          f"b63771f9 三重比对一致）")
    print("[r25-prep] 判据锚 PASS：M4 阈值锚 0.261904=axis-plan"
          f"（{axis_sha[:8]}）baselines_registered.r16_baseline 键位在案+"
          f"run-r24（{run24_sha[:8]}）baseline_cross_check 交叉核对；定点自"
          f"证 928571−666667=261904；drift 0.09064 在案计数 dev22={drift_counts['round22']}/"
          f"dev23={drift_counts['round23']}（round22-dev-record="
          f"{dev22_sha[:8]}、round23-dev-record={dev23_sha[:8]}），定点 "
          f"862069−771429=90640")
    print(f"[r25-prep] r24 实测锚 PASS：run-r24={run24_sha[:8]}"
          f"（M=(0.552381, 0.692308, 28, 0.888889、split_half=0.018640) "
          f"live 装载、G1 六实例全 0、G2=0、verdict=not_instance_dominated"
          f"维持不改写）；round24-dev-record={dev24_sha[:8]}（候选(b)原文逐"
          f"字在案+聚合稳/个体散原文在案）；比较集五行多源交叉核对一致；分"
          f"型件链锚 abstain-typology-r13-r16={typology_sha[:8]}（contact "
          f"族 r13–r16=8/15/5/10 链回放+黑点族 r16=12==axis-plan M3 交叉）")
    print(f"[r25-prep] 顶层键镜像断言：与 r24-prep-record 25 键逐键一致 "
          f"PASS（{len(record)} 键）；changed_variables=1；反放宽句恰 1 次；"
          f"归因三支判据原文逐字冻结（criterion_dominated/not_criterion_"
          f"dominated/guard_interrupted）")
    print(f"[r25-prep] 工件 sha256：observation-guidance-r25.md={derived_sha}"
          f"（{derived_bytes} B）；r25-prep-record.json={_sha(RECORD)}")


if __name__ == "__main__":
    main()
