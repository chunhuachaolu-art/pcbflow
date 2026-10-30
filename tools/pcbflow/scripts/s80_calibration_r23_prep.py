#!/usr/bin/env python
"""CAL-R23-PREP：R23 单变量报告框收敛归因轮（输出格式/报告纪律轴；§6 报
告框收敛条款）预备包（只新建三个文件：scripts/s80_calibration_r23_prep.py
本体、out/v3-tl2/calibration/observation-guidance-r23.md 与
out/v3-tl2/calibration/r23-prep-record.json；datasets/ 与 out/ 既有文件
只读、零改动，observation-guidance-r19.md 只读零字节不动）。

R23 轮性质（预注册，非事后）：**单变量报告框收敛归因轮（输出格式/报
告纪律轴；非判据调参轴重开——axis-experiment-plan-r17-r20 三轴实验收
束决议与轴停止决议不变）**。r22 事实锚（round22-dev-record b4b8fbe9 在
案）：M1=0.390244 落复制带 [0.361538, 0.561538] 内但 G2 几何门 0→2
（两条 silk 负责任报告框 area_ratio≈16.4>10 出局，R22T-002/R22T-013，
现象=位号小字叠压、框取过宽）——分岔在案 g2_bifurcation_record（字母=
regressed 唯一正式裁决、不改写；M1 复制事实=机制观察单列）。本轮唯一
实验变量=判读指引 §6 增补报告框收敛条款（框收窄到现象本体最小外接：
单个文字实例/单个图元/单组直接相连图元；禁止因描述便利扩大到邻域或整
区；离散实例逐实例分旗各配小框；框的语义=「该旗所指现象的物理位置」
而非「该区域的概貌」）；渲染零变更=renders-r14b 四图字节复用；GT/阈
值/协议零变更（13 条冻结、v1.1+v1.2 维持；evaluation-protocol-v2=
holdout 冻结件本轮不启用——v2 生效≠holdout 启动）。

合法性依据与设计出处（实测锚 fail-closed）：
  1. round22-dev-record honest_conclusion 下一候选建议（b）——对 G2 的
     2 条出局条目做机制归因（报告框 hygiene 核实，处置轴=派发层框收敛
     指引、须新预注册轮）；本轮=该候选的执行轮（实施路径=§6 条款随指
     引落盘固化、较候选原文的派发层路径更进一步的落盘固化路径，r19
     「随指引落盘固化」先例同型，差异如实登记）。
  2. 用户 2026-09-10 拍板：r22 复制轮（字母=regressed）后执行 G2 报告
     框归因轮（本记录=该轮预注册件、先于盲读冻结）。
  3. round22-dev-record g2_bifurcation_record——两条出局条目摘录=条款
     设计依据（两父之二）。

指引生成=确定性机械变换（s48/s54/s63/s67/s70 先例；锚串命中数
fail-closed，锚恰 1 次否则 FAIL）。任务枚举编辑：
  (1) 标题行替换（轮次身份四处更新之一）；
  (2) round_id_constant bullet 2026-09-09-r19→2026-09-10-r23（之二）；
  (3) 声明日期 bullet 2026-09-09→2026-09-10（之三）；
  (4) 本轮性质行按输出格式/报告纪律轴口径重写（之四）；
  (5) 「本轮变更声明」节正文整体替换（任务给定文本逐字）；
  (6) §6 增补报告框收敛条款 bullet（「注意：flag 对象没有 side 字段」
      说明段之后、格式示例小节之前插入；逐字）；
  (7) §6 示例旗 ID 前缀机械替换 R19T-→R23T-（恰 4 处）；
  (8) §6 示例旗 ID 前缀机械替换 R19B-→R23B-（恰 1 处）；
  (9) §6 示例 reader_id 前缀机械替换 reader-r19-→reader-r23-（恰 1 处）。
冻结区=§2–§7 与 §4/§5A（逐字）：一致性断言进脚本——r23 与 r19 的
§2–§5、§7 逐字一致（substring 双断言：区块+文末到 EOF）、反放宽句
「仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由」恰
1 次、R19 系 token（R19/R19T/R19B/reader-r19）残留=0（§6 前缀替换后；
小写 r19 仅存变更声明基座血统引用「相对 observation-guidance-r19」恰
1 处——r19 文件内保留 observation-guidance-r15 引用同口径先例）、新条
款恰 1 次（唯一 needle 族逐一断言）、R23T- 恰 4/R23B- 恰 1/reader-r23
恰 1、指引内零轮次结果数字（r22 实测数字与 R22 token 残留=0）、两父
哈希先验（r19 指引 8633bda5+round22-dev-record b4b8fbe9，任何写路径之
前 fail-closed 验证）。

预注册三支裁决（先于盲读冻结；描述性边界注记照抄 r22-prep-record 血统
原文；M1 带内判定用 6 位定点整数交叉相乘、不做浮点除法）：
  replicated_hygiene：G2 出局条目=0 且 G1 维持（bottom courtyard 非弃
    权 0/0/0）且 M1 ∈ [0.361538, 0.561538]（r19±0.10）→ r22 字面降级
    （字母=regressed）归因=报告框 hygiene，r19 量级复制结论升级；
  confounded：G2 出局条目仍 >0 且 M1 落带内 → 框宽非（唯一）主因，归
    因转向（新出局条目逐条摘录入机制观察）；
  perturbed：M1 出带 → 框收敛扰动判读本身，降级为度量教训如实单列。
M4/M2/三族计数/援引计数照常单列机制观察（对照 r19 与 r22 双基线）。

no_loosening 要旨：框收敛不是判据收紧也不是放宽——旗标产出与弃权判据
零变更，仅报告框几何纪律；显式防止「框收敛压弃权率」的误读（弃权旗同
样受框纪律约束、G1 守门照常独立计算）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-10 / 2026-09-10-r23）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-*
/ reader-raw-* / derivation-log-* / 任何 compare/诊断内容产物；run-r22
仅读 hypothesis_test 顶层判据冻结值字段+guard_channel+verdict（GT 匹
配/逐旗明细不读取不入记录；出局条目摘录自 round22-dev-record 在盘转
录、GT 字段不转录）；无 git；r19 指引只读零写入；记录内零 GT、零期望
数量/分布/坐标；指引内零轮次结果数字（基线数字仅入本编排侧记录）；
observation-guidance-r23.md 与 r23-prep-record.json 落盘=确定性字节
（变换/构造纯函数+同参重建两次逐字节一致自证）+防覆写守卫（已存在且
重建字节不同→FAIL，相同→幂等零覆写）+落盘后回读验字节。

用法：python scripts/s80_calibration_r23_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R19 = CAL_DIR / "observation-guidance-r19.md"
GUIDANCE_R23 = CAL_DIR / "observation-guidance-r23.md"
DEV_RECORD_R22 = CAL_DIR / "round22-dev-record.json"
R22_PREP_RECORD = CAL_DIR / "r22-prep-record.json"
RUN_R22 = CAL_DIR / "calibration-run-r22.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
EVAL_PROTOCOL_V2 = CAL_DIR / "evaluation-protocol-v2.md"
RECORD = CAL_DIR / "r23-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"

DATE_CONSTANT = "2026-09-10"
ROUND_ID = "2026-09-10-r23"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）。两父哈希先验=前两项。
# ---------------------------------------------------------------------------
GUIDANCE_R19_SHA_PREFIX = "8633bda5"
DEV_RECORD_R22_SHA_PREFIX = "b4b8fbe9"
R22_PREP_RECORD_SHA_PREFIX = "63346ee6"
RUN_R22_SHA_PREFIX = "80a12c05"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
EVAL_PROTOCOL_V2_SHA_PREFIX = "365b67ef"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

RENDR14B_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
R14B_BOTTOM_SHA_PREFIX = "d7284259"

#: r19 基座落盘事实锚（变换基座；不符即停）
GUIDANCE_R19_FACTS = {
    "R19T-": 4,
    "R19B-": 1,
    "reader-r19-": 1,
    "## 5B": 0,
    "(iii-a)": 3,
    "renders-r14b": 2,
    "R14": 4,
    "r15": 1,
    "- round_id_constant: `2026-09-09-r19`": 1,
    "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由": 1,
}

# ---------------------------------------------------------------------------
# r22 实测锚常量（=在案实测装载目标；probe 逐一断言，不符即停——防预注
# 册文本与在案事实漂移）
# ---------------------------------------------------------------------------
M1_R22 = 0.390244                    # run-r22 top_abstain_rate_r22（16/41）
M2_R22 = 0.2                         # bottom 2/10
M3_R22 = 4
M4_R22 = 0.104545
TOP_ABSTAIN_R22 = 16
TOP_FLAGS_R22 = 41
M1_R19 = 0.461538                    # r19 带中心（run-r19 在案锚）
REPLICATED_BAND = 0.10
REPLICATED_LO = 0.361538
REPLICATED_HI = 0.561538
REJECT_M1_THRESHOLD = 0.771429       # r16 基线（regressed 截断）
R19_DROP = 0.309891                  # 0.771429−0.461538
G2_R19 = 0                           # run-r19 几何门面积比出局条目
G2_R22 = 2                           # run-r22 几何门面积比出局条目
AREA_RATIO_002 = 16.406371           # R22T-002（dev-r22 在案）
AREA_RATIO_013 = 16.369542           # R22T-013（dev-r22 在案）
CONTACT_R19 = 4                      # r19 三族 rubric（4/4/14）
BLACKDOT_R19 = 4
EXIST_OTHER_R19 = 14
CONTACT_R22 = 2                      # r22 三族 rubric（2/4/12）
BLACKDOT_R22 = 4
EXIST_OTHER_R22 = 12

#: round22-dev-record 定位标记（fail-closed）
MARK_CANDIDATE_B = (
    "对 G2 的 2 条出局条目做机制归因（报告框 hygiene 核实，处置轴=派发"
    "层框收敛指引、须新预注册轮）")
CANDIDATE_B_QUOTE = (
    "(b) 对 G2 的 2 条出局条目做机制归因（报告框 hygiene 核实，处置轴="
    "派发层框收敛指引、须新预注册轮）")

# ---------------------------------------------------------------------------
# 指引机械变换常量（锚串恰 1 次否则 FAIL；s48/s54/s63/s67/s70 先例）
# ---------------------------------------------------------------------------
OLD_TITLE = "# R19 轮 reader 判读指引（observation-guidance-r19）"
NEW_TITLE = "# R23 轮 reader 判读指引（observation-guidance-r23）"

OLD_ROUND_ID_LINE = "- round_id_constant: `2026-09-09-r19`"
NEW_ROUND_ID_LINE = "- round_id_constant: `2026-09-10-r23`"

OLD_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-09"
NEW_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-10"

OLD_NATURE_LINE = (
    "- 本轮性质：**单变量判据侧变更轮（轴3 §4(iii) 可操作分辨条款轮；"
    "axis-experiment-plan-r17-r20 stage1 之一）**。渲染零变更（复用 R14 "
    "冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引 §4 增补 "
    "(iii-a) 可操作分辨条款（把接触性判据的「无法区分」操作化为证据可见"
    "性三支判据：见间隙证据→按视觉贴近继续判定；见侵入证据→按接触/交叠"
    "处理；两者均无→方按 (iii) 原文弃权；反放宽条款逐字保留），指引落盘"
    "后由编排侧重新盲读。")
NEW_NATURE_LINE = (
    "- 本轮性质：**单变量报告框收敛归因轮（输出格式/报告纪律轴；§6 报告"
    "框收敛条款轮；非判据调参轴重开——轴停止决议不变）**。渲染零变更（复"
    "用 R14 冻结渲染件 renders-r14b，字节复用）；本轮唯一变更=判读指引 "
    "§6 增补报告框收敛条款（把 `frame_box_pct` 的语义钉住为「该旗所指现"
    "象的物理位置」：必须收窄到现象本体的最小外接——单个文字实例/单个图"
    "元/单组直接相连图元；禁止因描述便利扩大到邻域或整区；同一类现象的多"
    "个离散实例分旗各配小框；旗标产出与弃权判据零变更、弃权旗疑似区域框"
    "同样适用），指引落盘后由编排侧重新盲读。")

OLD_CHANGES_PARA = (
    "本轮（R19）为轴3 判据侧单变量轮：相对 observation-guidance-r15 仅"
    "（1）更新标题与轮次标识，（2）重写本变更声明，（3）§4 增补 (iii-a) "
    "可操作分辨条款（在 (iii) 接触性判据句之后、既有对照说明块之前插入；"
    "把「无法区分」操作化为证据可见性三支判据——见间隙证据→按视觉贴近继"
    "续判定；见侵入证据→按接触/交叠处理；两者均无→方按 (iii) 原文弃权；"
    "条款为判定路径的澄清而非判断责任的放松；§4 其余全部文本含量化判据 "
    "(i)(ii)(iii) 原文、三路出口与反放宽条款逐字不变），（4）虚构示例旗 "
    "ID 前缀改为 R19T/R19B。渲染零变更：本轮使用与 R14 完全相同的 "
    "renders-r14b 四图（字节复用）。§2 类别枚举、§3/§3A 位置与判据示例、"
    "§5 courtyard 说明、§5A 渲染配色仪器注记（原文逐字保留）、§6 输出格"
    "式、§7 格式对齐提示全部逐字不变。预注册判据见 r19-prep-record.json "
    "hypothesis_test（先于任何盲读冻结）。")
NEW_CHANGES_PARA = (
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

CLAUSE_INSERT_ANCHOR = (
    "reader 不标注、也不得自行添加 side 或其他任何键。\n\n### 格式示例")
CLAUSE_TEXT = (
    "- **报告框收敛条款（本轮增补）**：`frame_box_pct` 的语义是「**该旗"
    "所指现象的物理位置**」，不是「该区域的概貌」。每个旗的框必须收窄到"
    "**该旗所指现象本体的最小外接**：框的单一直接对象恰为**单个文字实例、"
    "单个图元、或单组直接相连的图元**三者之一（在第 3 节收窄判据与最小余"
    "量口径下取最小覆盖）；**不得因描述便利把框扩大到该现象的邻域、周边"
    "密集区或整区**。若同一类现象含多个**互不直接相连的离散实例**，应**"
    "逐实例分旗**报告——每旗各配自己的小框（`flag_id` 编号可连续），不得"
    "用一个宽框覆盖全部离散实例。本条款是报告框几何纪律：只约束报告框的"
    "几何口径，旗标产出与否、类别判定、弃权判据与报告义务零变更；弃权旗"
    "的疑似区域框同样适用本条（按第 4 节弃权规则给出疑似区域时，亦收窄到"
    "疑似现象本体的最小外接）。本条款不构成任何判据收紧或放宽，也不修改"
    "第 3 节位置口径的任何文本。")

PREFIX_EDITS = (
    ("R19T-", "R23T-", 4),
    ("R19B-", "R23B-", 1),
    ("reader-r19-", "reader-r23-", 1),
)

#: §6 区块边界（与 r19 的 §6 结构等价复核用）
MARK_S6 = "## 6. 输出格式"
MARK_S7 = "## 7. 格式对齐提示"

#: r23 指引落盘后的一致性断言（任务要求逐项；不符即停）
GUIDANCE_R23_REQUIRED = {
    NEW_TITLE: 1,
    NEW_ROUND_ID_LINE: 1,
    NEW_DATE_LINE: 1,
    "R23T-": 4,
    "R23B-": 1,
    "reader-r23-": 1,
    "2026-09-10": 2,  # round_id 行「2026-09-10-r23」+声明日期行各 1 次
    # 新条款恰 1 次（唯一 needle 族）
    "报告框收敛条款（本轮增补）": 1,
    "**该旗所指现象的物理位置**": 1,
    "**该旗所指现象本体的最小外接**": 1,
    "逐实例分旗": 1,
    "不得因描述便利把框扩大到": 1,
    "互不直接相连的离散实例": 1,
    "不是「该区域的概貌」": 1,
    # 反放宽句恰 1 次（§4 逐字保留的落盘事实）
    "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由": 1,
    "(iii-a)": 2,
    "renders-r14b": 2,
    "R14": 4,
    "## 5B": 0,
    # R19 系 token 残留=0（§6 前缀替换后）
    "R19": 0,
    "R15": 0,
    "r15": 0,
    "r22": 0,
    "R22": 0,
    "2026-09-09": 0,
    # 指引内零轮次结果数字
    "0.390244": 0,
    "16.406371": 0,
    "16.369542": 0,
    "area_ratio": 0,
    "GT-": 0,
}
#: 小写 r19 残留恰 1 处=变更声明基座血统引用（r19 文件保留 observation-
#: guidance-r15 引用同口径先例）；其余任何 r19 token 不存在
GUIDANCE_R23_R19_LOWERCASE = 1
GUIDANCE_R23_R19_LINEAGE = "相对 observation-guidance-r19 仅"


# ---------------------------------------------------------------------------
# 预注册收敛归因判据（逐字，先于任何盲读冻结；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "r22-g2-bifurcation-frame-box-hygiene-attribution",
  "hypothesis": "r22（同指引重复轮=收敛归因轮；唯一实验操作=实例群重抽）字面裁决=regressed（唯一正式裁决、轮后不改写），破坏源=守门 G2 单项：top 视非弃权旗标 frame_box_pct 几何门面积比出局条目 0→2（R22T-002 area_ratio=16.406371、R22T-013 area_ratio=16.369542，均 silk_readability 负责任报告；run-r22 在案），而 M1=16/41=0.390244 落复制带 [0.361538, 0.561538]（r19±0.10）内、contact=2≤7、G1=bottom courtyard 非弃权 0/0/0 维持——量级复制与守门破坏并存=分岔在案（round22-dev-record g2_bifurcation_record；counterfactual：replication_verdict_fixed_point(16, 41, 2, True)=replicated 构造可复算）。主因候选=(α) 报告框过宽：两条出局条目均为「多个离散文字实例合用一个宽框」的报告几何失范（现象=位号小字叠压而框取过宽，框的语义从「该旗所指现象的物理位置」漂移为「该区域的概貌」）；(β) 判据内容或实例群因素（框宽只是表象）。R23=单变量报告框 hygiene 轮（§6 增补报告框收敛条款：框收窄到现象本体最小外接、禁止邻域/整区框、离散实例逐实例分旗；渲染零变更 renders-r14b 字节复用、GT/阈值/协议零变更），以 G2 出局清零+M1 量级保持做归因裁决：replicated_hygiene 支命中→r22 字面降级归因=报告框 hygiene（输出格式/报告纪律轴），r19 量级复制结论升级（量级与守门纪律可同时复现）。",
  "adjudication": {
    "replicated_hygiene": "G2 出局条目=0（top 视非弃权旗标 frame_box_pct 几何门面积比出局条目数=0；对照 run-r19=0、run-r22=2 在案）且 G1 维持（bottom courtyard 非弃权 0/0/0）且 M1（top 全旗聚合弃权率，12 派次全口径）∈ [0.361538, 0.561538]（r19±0.10）→ r22 字面降级（字母=regressed）归因=报告框 hygiene（框宽为（唯一）主因），r19 量级复制结论升级。M1 带内判定=6 位定点整数交叉相乘：abstain_count×1000000 与 361538×top_flags、561538×top_flags 整数比较，不做浮点除法（r22 实测 16/41 复算=16000000∈[14823058, 23023058] 带内对照）",
    "confounded": "G2 出局条目仍 >0 且 M1 落带内（同式 6 位定点整数交叉相乘比较）→ 框宽非（唯一）主因，归因转向（判据内容/实例群/其他输出侧因素混杂主导）；新出局条目逐条摘录入机制观察（flag_id/category/area_ratio/containment/现象转述逐条如实、与 r22 两条出局条目 R22T-002/R22T-013 对照）；三轴收束决议不变",
    "perturbed": "M1 出带（abstain_count×1000000 < 361538×top_flags 或 > 561538×top_flags）→ 框收敛扰动判读本身（报告纪律变化改变了判读行为分布），降级为度量教训如实单列，不进任何归因升级、不改写 r22 字母=regressed",
    "mechanism_observation_separate": "M4/M2/三族计数/援引计数照常单列机制观察、不进字母裁决：M4（top 逐实例弃权率极差）三样本（r19=0.211111、r22=0.104545、本轮实测）如实并列；M2（bottom 全旗聚合弃权率）对照 r19=0.571429 与 r22=0.2 双基线；contact/黑点/存在性三族计数（分型件 rubric 口径）对照 r19（4/4/14）与 r22（2/4/12）双基线；(iii-a) 援引计数对照 r19（旗级 6 旗+分支字面 2 旗、notes 级 10/12 派次）与 r22（旗级全 0、notes 级 (iii-a)=6/12 派次）双基线，§5B 援引计数照记（本轮指引含 §6 新条款、仍无 §5B 节=基座结构在案，任何援引为零上下文）；G2 新出局条目（若有）逐条摘录；M1/M2/M3/M4 四元组入实验对照账（axis ledger 延续登记、rubric 口径）；gt 照常",
    "metric_lesson_separate": "跨轮实例群漂移混杂照旧声明——本轮唯一实验变量=§6 报告框收敛条款（输出格式/报告纪律轴），实例群重抽为轮际固有混杂、非本轮实验操作；字母=预注册阈值命中与否的描述性结论；部分重复≠独立重复（同域同编排实例池、验证力度如实声明）；replicated_hygiene/confounded/perturbed 三支的 M1 带宽（r19±0.10）为描述性边界、不得事后收放；报告框收敛不是判据收紧也不是放宽（见 no_loosening_note）",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

#: 预注册判据文本数值 needle（逐字在位断言；不符即停）
REQUIRED_NEEDLES = (
    "[0.361538, 0.561538]",
    "r19±0.10",
    "0.390244",
    "16/41",
    "16.406371",
    "16.369542",
    "361538×top_flags",
    "561538×top_flags",
    "abstain_count×1000000",
    "16000000∈[14823058, 23023058]",
    "G1 维持（bottom courtyard 非弃权 0/0/0）",
    "归因=报告框 hygiene",
    "框宽非（唯一）主因",
    "降级为度量教训如实单列",
    "replication_verdict_fixed_point(16, 41, 2, True)",
    "0.211111",
    "0.104545",
    "0.571429",
    "4/4/14",
    "2/4/12",
    "旗级 6 旗+分支字面 2 旗",
    "notes 级 10/12",
    "(iii-a)=6/12",
    "不进字母裁决",
    "不是判据收紧也不是放宽",
    "axis-experiment-plan-r17-r20.json 为准",
)


# ---------------------------------------------------------------------------
# 工具（fail-closed）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[r23-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        _fail(f"机械变换锚「{label}」命中 {n} 次 != 1（锚串必须恰 1 次，"
              f"立即停止）")
    return text.replace(old, new)


def check_renders_byte_reuse(witness: dict) -> list[dict]:
    """渲染零变更实测：四 PNG magic+sha256_file 实测 vs witness 登记值
    （bottom=renders.{applied,prep1}.sha256 两板同；
    top=top_zero_change_copies.{applied-top,prep1-top}.sha256）。"""
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
        expect = registered[side]
        if measured != expect:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与 witness 登记值不"
                  f"符（渲染零变更声明被破坏）：measured={measured} "
                  f"registered={expect}")
        if side.endswith("-bottom") and not measured.startswith(
                R14B_BOTTOM_SHA_PREFIX):
            _fail(f"renders-r14b/{side}.png sha 前 8={measured[:8]} != 预期 "
                  f"{R14B_BOTTOM_SHA_PREFIX}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "sha256_witness_registered": expect,
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "top_zero_change_copies." + side + ".sha256"),
            "witness_record": "out/v3-tl2/calibration/render-witness-r14b.json",
            "match": True,
        })
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（字节复用口径不符）")
    return results


def probe_witness(witness: dict) -> None:
    """render-witness-r14b 结构最小校验（kind/轮次/日期锚）。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")


def probe_dev_record_r22(dev: dict, dev_sha: str) -> dict:
    """round22-dev-record：g2_bifurcation_record 计数+两条出局条目摘录
    （条款设计依据；GT 字段不转录）+候选(b)授权原文+字母锚。"""
    if dev.get("kind") != "tl2_calibration_round22_dev_record":
        _fail("round22-dev-record kind 不符")
    if dev.get("round_id") != "2026-09-09-r22" or \
            dev.get("round_label") != "r22":
        _fail("round22-dev-record 轮次标识不符")
    if dev.get("declared_date") != "2026-09-09":
        _fail("round22-dev-record declared_date != 2026-09-09")
    if dev.get("schema_version") != "3.0":
        _fail("round22-dev-record schema_version != 3.0（结构漂移）")
    g2 = dev.get("g2_bifurcation_record")
    if not isinstance(g2, dict):
        _fail("round22-dev-record g2_bifurcation_record 结构不符")
    counts = g2.get("counts", {})
    if counts.get("g2_geometry_gate_r19") != G2_R19 or \
            counts.get("g2_geometry_gate_r22") != G2_R22:
        _fail(f"g2 几何门锚不符：r19={counts.get('g2_geometry_gate_r19')!r} "
              f"r22={counts.get('g2_geometry_gate_r22')!r}")
    if counts.get("m1_in_replication_band") is not True or \
            counts.get("m1_r22") != M1_R22:
        _fail("g2 分岔记录 M1 带内锚不符")
    if counts.get("g1_bottom_courtyard_non_abstain_r22") != \
            {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}:
        _fail("g2 分岔记录 G1 维持锚不符")
    letter = g2.get("letter_vs_fact", {}).get("letter", "")
    if not letter.startswith("regressed"):
        _fail(f"r22 字母锚不符：{letter!r}（预期 regressed、轮后不改写）")
    entries = g2.get("rejected_entries_excerpt")
    if not isinstance(entries, list) or len(entries) != 2:
        _fail("g2 出局条目摘录须恰 2 条")
    expect_entries = [
        {"flag_id": "R22T-002", "state": "applied", "instance": "top-i3",
         "category": "silk_readability",
         "area_ratio": AREA_RATIO_002, "containment": 0.804462},
        {"flag_id": "R22T-013", "state": "prep1", "instance": "top-i3",
         "category": "silk_readability",
         "area_ratio": AREA_RATIO_013, "containment": 1.0},
    ]
    transcript = []
    for entry, want in zip(entries, expect_entries):
        for key, val in want.items():
            if entry.get(key) != val:
                _fail(f"出局条目锚不符：{want['flag_id']}.{key}="
                      f"{entry.get(key)!r} != {val!r}")
        if AREA_RATIO_002 <= 10 or AREA_RATIO_013 <= 10:
            _fail("出局条目 area_ratio 未过 10（语义引用锚不符）")
        transcript.append({
            "flag_id": want["flag_id"],
            "state": want["state"],
            "instance": want["instance"],
            "category": want["category"],
            "area_ratio": want["area_ratio"],
            "containment": want["containment"],
            "corresponding_phenomenon":
                entry.get("corresponding_phenomenon", ""),
            "omitted_fields_note": (
                "gt_id/gt_category 不转录（本记录内零 GT 纪律）；全文见 "
                "round22-dev-record.json g2_bifurcation_record."
                "rejected_entries_excerpt"),
        })
    honest = dev.get("honest_conclusion", "")
    if MARK_CANDIDATE_B not in honest:
        _fail("round22-dev-record honest_conclusion 缺候选(b)原文定位标记")
    measured = dev.get("axis_experiment_ledger", {}).get(
        "this_round_measured", {})
    if measured != {"M1": M1_R22, "M2": M2_R22, "M3": M3_R22, "M4": M4_R22}:
        _fail(f"round22-dev-record 实测四元组锚不符：{measured!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/round22-dev-record.json",
        "sha256_measured": dev_sha,
        "role": ("条款设计依据（两父之二）：g2_bifurcation_record 两条出局"
                 "条目摘录（GT 字段不转录）+候选(b)授权原文+r22 字母锚"),
        "letter": "regressed（唯一正式裁决、轮后不改写）",
        "g2_counts": {
            "g2_geometry_gate_r19": G2_R19,
            "g2_geometry_gate_r22": G2_R22,
            "m1_in_replication_band": True,
            "g1_bottom_courtyard_non_abstain_r22": {
                "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0},
        },
        "candidate_b_quote": CANDIDATE_B_QUOTE,
        "rejected_entries_transcript": transcript,
    }


def probe_run_r22(run: dict, run_sha: str) -> dict:
    """calibration-run-r22 判据冻结值锚定（fail-closed；只读顶层判据值
    字段+guard_channel+verdict；GT 匹配与逐旗明细不读取不入记录）。"""
    ht = run.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r22 hypothesis_test 结构不符")
    if ht.get("verdict") != "regressed":
        _fail(f"run-r22 verdict 锚不符：{ht.get('verdict')!r}（预期 "
              f"regressed=r22 字母在案锚、轮后不改写）")
    if ht.get("hypothesis_id") != \
            "r20-dev-record-candidate-r19-config-same-guidance-repeat":
        _fail("run-r22 hypothesis_id 不符（r22 预注册假设锚）")
    m = ht.get("measurement", {})
    expect = {
        "r22_m_tuple_6dp": {"M1": M1_R22, "M2": M2_R22, "M3": M3_R22,
                            "M4": M4_R22},
        "r19_reference_tuple": {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                                "M4": 0.211111},
        "replication_band_6dp": [361538, 561538],
        "reject_m1_threshold_6dp": 771429,
        "top_abstain_count_r22": TOP_ABSTAIN_R22,
        "top_abstain_flags_r22": TOP_FLAGS_R22,
    }
    for key, want in expect.items():
        got = m.get(key)
        if got != want:
            _fail(f"run-r22 判据冻结值锚不符：{key}={got!r} != {want!r}")
    gc = m.get("guard_channel", {})
    if gc.get("g1_ok") is not True or gc.get("g2_guard_ok") is not False or \
            gc.get("guards_ok") is not False:
        _fail("run-r22 守门锚不符（预期 G1 维持、G2 破坏）")
    if gc.get("g2_geometry_gate_r19") != G2_R19 or \
            gc.get("g2_geometry_gate_r22") != G2_R22:
        _fail("run-r22 G2 几何门锚不符（预期 0→2）")
    # 判据数值自洽（预注册文本 ↔ 在案锚）
    if round(M1_R19 - REPLICATED_BAND, 6) != REPLICATED_LO or \
            round(M1_R19 + REPLICATED_BAND, 6) != REPLICATED_HI:
        _fail("自洽断言失败：replicated 带非 r19（0.461538）±0.10")
    if round(TOP_ABSTAIN_R22 / TOP_FLAGS_R22, 6) != M1_R22:
        _fail("自洽断言失败：16/41 != 0.390244")
    abstain_fp = TOP_ABSTAIN_R22 * 1000000
    lo_fp = REPLICATED_LO_6DP * TOP_FLAGS_R22
    hi_fp = REPLICATED_HI_6DP * TOP_FLAGS_R22
    if (lo_fp, hi_fp) != (14823058, 23023058):
        _fail(f"自洽断言失败：定点整数端点不符（{lo_fp}, {hi_fp}）")
    if not (lo_fp <= abstain_fp <= hi_fp):
        _fail("自洽断言失败：r22 M1=16/41 不在复制带内（与在案锚矛盾）")
    if round(REJECT_M1_THRESHOLD - M1_R19, 6) != R19_DROP:
        _fail("自洽断言失败：0.771429−0.461538 != 0.309891")
    for needle in REQUIRED_NEEDLES:
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值/口径 {needle!r}"
                  f"（逐字要求破坏）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r22.json",
        "sha256_measured": run_sha,
        "frozen_values": (
            f"M tuple (M1,M2,M3,M4)=({M1_R22}, {M2_R22}, {M3_R22}, "
            f"{M4_R22})（M1={TOP_ABSTAIN_R22}/{TOP_FLAGS_R22}、M2=2/10）；"
            "verdict=regressed（(g) regressed_guards 支、轮后不改写）；"
            "G2 几何门面积比出局条目 r19=0→r22=2（R22T-002/R22T-013）；"
            "复制带 [0.361538, 0.561538]=r19±0.10、regressed 截断 "
            "0.771429、G1 维持 0/0/0——hypothesis_test 判据文本数值的在"
            "案锚（GT 匹配与逐旗明细不读取）"),
    }


#: 复制带 6 位定点整数端点（judged against abstain_count×1000000）
REPLICATED_LO_6DP = 361538
REPLICATED_HI_6DP = 561538


# ---------------------------------------------------------------------------
# 指引机械变换（纯函数；锚串命中数 fail-closed）
# ---------------------------------------------------------------------------

def derive_guidance_r23(base_text: str) -> str:
    """observation-guidance-r23 全文=observation-guidance-r19 全文的确定
    性机械变换（9 组锚定编辑；锚恰 1 次否则 FAIL）。"""
    for needle, want in GUIDANCE_R19_FACTS.items():
        n = base_text.count(needle)
        if n != want:
            _fail(f"r19 基座落盘事实锚不符：{needle!r} 命中 {n} 次 != 预期 "
                  f"{want} 次（立即停止）")
    t = base_text
    t = _replace_once(t, OLD_TITLE, NEW_TITLE, "标题行")
    t = _replace_once(t, OLD_ROUND_ID_LINE, NEW_ROUND_ID_LINE,
                      "round_id_constant bullet")
    t = _replace_once(t, OLD_DATE_LINE, NEW_DATE_LINE, "声明日期 bullet")
    t = _replace_once(t, OLD_NATURE_LINE, NEW_NATURE_LINE, "本轮性质行")
    t = _replace_once(t, OLD_CHANGES_PARA, NEW_CHANGES_PARA,
                      "本轮变更声明节正文")
    # 头部更新后、前缀替换前：R19 系旗 ID 前缀应恰为落盘原文 4/1/1
    for old, _, want in PREFIX_EDITS:
        n = t.count(old)
        if n != want:
            _fail(f"前缀替换前锚不符：{old!r} 命中 {n} 次 != {want} 次")
    # §6 增补条款（注意段之后、格式示例小节之前）
    n = t.count(CLAUSE_INSERT_ANCHOR)
    if n != 1:
        _fail(f"条款插入锚命中 {n} 次 != 1（立即停止）")
    t = t.replace(
        CLAUSE_INSERT_ANCHOR,
        "reader 不标注、也不得自行添加 side 或其他任何键。\n\n"
        + CLAUSE_TEXT + "\n\n### 格式示例")
    # §6 前缀机械替换（任务枚举）
    for old, new, want in PREFIX_EDITS:
        n = t.count(old)
        if n != want:
            _fail(f"前缀替换锚不符：{old!r} 命中 {n} 次 != {want} 次")
        t = t.replace(old, new)
    return t


def assert_guidance_r23(derived: str, base: str) -> dict:
    """r23 指引一致性断言（任务要求逐项；不符即停）。"""
    for needle, want in GUIDANCE_R23_REQUIRED.items():
        n = derived.count(needle)
        if n != want:
            _fail(f"r23 指引断言不符：{needle!r} 命中 {n} 次 != {want} 次")
    n_r19 = derived.count("r19")
    if n_r19 != GUIDANCE_R23_R19_LOWERCASE:
        _fail(f"r23 指引小写 r19 残留 {n_r19} 处 != 恰 1 处（基座血统引用）")
    if GUIDANCE_R23_R19_LINEAGE not in derived:
        _fail("r23 指引缺变更声明基座血统引用「相对 observation-guidance"
              "-r19 仅」")
    # §2–§5 逐字一致（substring）：r19「## 2.」标题起至「## 6.」标题止
    seg2_5 = base[base.index("## 2. 类别枚举"):base.index(MARK_S6)]
    if seg2_5 not in derived:
        _fail("一致性断言失败：r23 与 r19 的 §2–§5 区块逐字不一致")
    # §7 逐字一致（substring）：「## 7.」标题起至文末（含（完））
    seg7 = base[base.index(MARK_S7):]
    if seg7 not in derived or not derived.endswith(seg7):
        _fail("一致性断言失败：r23 与 r19 的 §7 区块逐字不一致（含文末）")
    # §6 结构等价复核：实际 §6 区块==基座 §6 区块+前缀替换+条款插入
    base6 = base[base.index(MARK_S6):base.index(MARK_S7)]
    expect6 = base6
    for old, new, want in PREFIX_EDITS:
        if expect6.count(old) != want:
            _fail(f"§6 等价复核锚不符：{old!r}")
        expect6 = expect6.replace(old, new)
    expect6 = expect6.replace(
        CLAUSE_INSERT_ANCHOR,
        "reader 不标注、也不得自行添加 side 或其他任何键。\n\n"
        + CLAUSE_TEXT + "\n\n### 格式示例")
    actual6 = derived[derived.index(MARK_S6):derived.index(MARK_S7)]
    if actual6 != expect6:
        _fail("§6 结构等价复核失败：实际 §6 区块 != 基座 §6+条款+前缀替换")
    return {
        "seg2_5_bytes": len(seg2_5.encode("utf-8")),
        "seg7_bytes": len(seg7.encode("utf-8")),
        "clause_bytes": len(CLAUSE_TEXT.encode("utf-8")),
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance19_sha: str, guidance19_bytes_n: int,
                 guidance23_sha: str, guidance23_bytes_n: int,
                 seg_bytes: dict, r22_record_sha: str, dev_ref: dict,
                 run_ref: dict, witness_sha: str, protocol_v1_sha: str,
                 protocol_v2_sha: str, png_checks: list[dict]) -> dict:
    """构建 r23-prep-record 内容（纯函数：同入参必得同 dict）。"""
    edit_list = [
        {"edit": 1, "kind": "标题行替换（轮次身份四处更新之一）",
         "expected_hits": 1, "old": OLD_TITLE, "new": NEW_TITLE},
        {"edit": 2,
         "kind": "round_id_constant bullet 替换（轮次身份四处更新之二）",
         "expected_hits": 1, "old": OLD_ROUND_ID_LINE,
         "new": NEW_ROUND_ID_LINE},
        {"edit": 3, "kind": "声明日期 bullet 替换（轮次身份四处更新之三）",
         "expected_hits": 1, "old": OLD_DATE_LINE, "new": NEW_DATE_LINE},
        {"edit": 4,
         "kind": "本轮性质行按输出格式/报告纪律轴口径重写（轮次身份四处更"
                 "新之四）",
         "expected_hits": 1, "old": OLD_NATURE_LINE, "new": NEW_NATURE_LINE},
        {"edit": 5,
         "kind": "「本轮变更声明」节正文整体替换（任务枚举，逐字）",
         "expected_hits": 1, "old": OLD_CHANGES_PARA, "new": NEW_CHANGES_PARA,
         "content_sha256": hashing.sha256_text(NEW_CHANGES_PARA)},
        {"edit": 6,
         "kind": "§6 增补报告框收敛条款 bullet（「注意：flag 对象没有 "
                 "side 字段」说明段之后、格式示例小节之前插入；逐字）",
         "expected_hits_insert_anchor": 1,
         "insert_anchor": CLAUSE_INSERT_ANCHOR,
         "region": "§6 内（注意段之后、格式示例小节之前）",
         "text_full": CLAUSE_TEXT},
        {"edit": 7, "kind": "§6 示例旗 ID 前缀机械替换（top）",
         "expected_hits": 4, "old": "R19T-", "new": "R23T-"},
        {"edit": 8, "kind": "§6 示例旗 ID 前缀机械替换（bottom）",
         "expected_hits": 1, "old": "R19B-", "new": "R23B-"},
        {"edit": 9, "kind": "§6 示例 reader_id 前缀机械替换",
         "expected_hits": 1, "old": "reader-r19-", "new": "reader-r23-"},
    ]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r23_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r23",
        "round_nature": (
            "单变量报告框收敛归因轮（输出格式/报告纪律轴单变量；非判据调参"
            "轴重开——axis-experiment-plan-r17-r20 三轴实验收束决议与轴停止"
            "决议不变，本变量=输出格式/报告纪律轴=守门 G2 的报告框 hygiene "
            "轴，非三判据轴任何一支重开；本轮=第二十三轮）：唯一实验变量=判"
            "读指引 §6 增补报告框收敛条款（observation-guidance-r23.md 由 "
            "observation-guidance-r19.md 8633bda5 基座机械变换派生：轮次身"
            "份四处更新（标题/round_id_constant/声明日期/本轮性质）+变更声"
            "明节正文整体重写+§6 增补条款 bullet+§6 示例旗 ID 前缀机械替换 "
            "R19T-→R23T-（恰 4 处）、R19B-→R23B-（恰 1 处）、reader-r19→"
            "reader-r23（恰 1 处）；§2–§5/§7 与 §4/§5A 逐字保留——脚本 "
            "substring 断言 fail-closed、反放宽条款逐字保留、R19 系 token "
            "残留=0、新条款恰 1 次）；渲染零变更=renders-r14b 四图字节复用"
            "（四 PNG sha256_file 实测与 render-witness-r14b.json 登记值 "
            "fail-closed 比对一致，即 r14–r22 轮盲读所用同一批文件，见 "
            "instrument_change）；GT/阈值/协议零变更（13 条冻结、v1.1+v1.2 "
            "维持；evaluation-protocol-v2=holdout 协议冻结件本轮不启用——"
            "v2 生效≠holdout 启动）；changed_variables=1（§6 报告框收敛条"
            "款，见 changed_variables[0]）；执行 round22-dev-record "
            "honest_conclusion 下一候选建议（b）（对 G2 的 2 条出局条目做机"
            "制归因=报告框 hygiene 核实、须新预注册轮——原文逐字见 "
            "user_directive_note）+用户 2026-09-10 拍板「r22 复制轮（字母="
            "regressed）后执行 G2 报告框归因轮」；r22 字母裁决=regressed 维"
            "持不改写、不得回溯改判既往轮次（r8–r22 字母裁决维持不变）；"
            "r19 指引已在盘冻结、本轮只读零写入；盲读由编排侧在本记录之后以 "
            "12 次独立实例盲读执行（6 个 reader 实例各包两板=12 派次）"),
        "user_directive_note": (
            "用户 2026-09-10 拍板：r22 复制轮（字母=regressed）后执行 G2 "
            "报告框归因轮（本记录=该轮预注册件、先于盲读冻结）。r22 事实锚"
            "（round22-dev-record.json b4b8fbe9 实测在案）：M1=0.390244 落"
            "复制带 [0.361538, 0.561538] 内但 G2 几何门 0→2（两条 silk 负"
            "责任报告框 area_ratio≈16.4>10 出局，R22T-002/R22T-013，现象="
            "位号小字叠压、框取过宽；g2_bifurcation_record 两账分列在案：字"
            "母=regressed 与 M1 复制事实单列）；round22-dev-record "
            "honest_conclusion 下一候选建议（b）原文：「对 G2 的 2 条出局"
            "条目做机制归因（报告框 hygiene 核实，处置轴=派发层框收敛指引、"
            "须新预注册轮）」——本轮=该候选的执行轮（实施路径=§6 条款随指"
            "引落盘固化+派发层同步沿用，较候选原文的「派发层框收敛指引」进"
            "一步为落盘固化路径，r19「随指引落盘固化」先例同型，差异如实登"
            "记）；r22 字母裁决=regressed 维持、轮后不改写；轴停止决议不变"
            "（本变量=输出格式/报告纪律轴、非判据调参轴重开）；预注册后执行"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14/r15/r16/r18/r19/r20/r22 完全相同（"
                    "renders-r14b 字节复用，四 PNG 实测=witness-r14b 登记"
                    "值），本轮唯一变更=判读指引 §6（非仪器侧）",
            "renders": png_checks,
            "witness": "render-witness-r14b.json（b63771f9，fail-closed 复"
                       "核）",
            "declaration": (
                "本轮 prep 零重渲染、零 out/ 既有文件改动（四 PNG "
                "sha256_file 实测=witness-r14b 登记值；bottom 两板逐字节同 "
                "d7284259；top 无配色 298bc620/b2f84524）；指引基座="
                "observation-guidance-r19.md 只读零写入（8633bda5）；本轮"
                "恰两个 out/ 新建文件=observation-guidance-r23.md 与本记录"),
        },
        "no_instrument_change": True,
        "guidance_reuse": {
            "base": "observation-guidance-r19.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r19.md"),
            "base_sha256": guidance19_sha,
            "base_sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
            "mode": "mechanical_transform_derive",
            "derived": "observation-guidance-r23.md",
            "derived_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r23.md"),
            "derived_sha256": guidance23_sha,
            "byte_size": {"base": guidance19_bytes_n,
                          "delta": guidance23_bytes_n - guidance19_bytes_n,
                          "derived": guidance23_bytes_n},
            "edit_list": edit_list,
            "verbatim_scope_note": (
                "冻结区=§2–§7 与 §4/§5A 逐字：§2 类别枚举、§3 位置口径（含"
                "邻域收窄判据）、§3A 判据示例、§4 全文（含量化判据 "
                "(i)(ii)(iii)、(iii) 接触性判据、(iii-a) 可操作分辨条款、三"
                "路出口、反放宽条款「仅因形态不熟悉、不确定其设计含义，不构"
                "成判为正常设计特征的理由」原文逐字保留）、§5 courtyard 说"
                "明、§5A 渲染配色仪器注记、§7 格式对齐提示——r23 与 r19 的"
                "§2–§5、§7 逐字一致（脚本 substring 双断言：「## 2. 类别枚"
                "举」→「## 6. 输出格式」区块与「## 7. 格式对齐提示」→文末"
                "区块逐字节一致，fail-closed）；§6 除增补报告框收敛条款一条"
                "与示例旗 ID 前缀机械替换（R19T-→R23T- 恰 4 处、R19B-→"
                "R23B- 恰 1 处、reader-r19→reader-r23 恰 1 处）外逐字不变"
                "（§6 区块等价复核断言）；本轮指引内 R23T- 恰 4 处、R23B- "
                "恰 1 处、reader-r23 恰 1 处实测锚定；R19 系 token 残留=0"
                "（R19/R19T/R19B/reader-r19 全 0——§6 前缀替换后；小写 "
                "r19 仅存变更声明基座血统引用「相对 observation-guidance-"
                "r19」恰 1 处——r19 文件内保留 observation-guidance-r15 引"
                "用同口径先例）；本轮指引无 §5B 节（r19 基座=r15 结构在"
                "案）——§5B 援引计数机制观察照记、任何援引为零上下文；指引"
                "内零轮次结果数字（r22 实测数字与 R22 token 残留=0，基线数"
                "字仅入本编排侧记录）"),
            "zero_write_declaration": (
                "变换基座 observation-guidance-r19.md 零字节不动（本脚本对"
                "基座无任何写路径；实测哈希在 guidance_reuse.base_sha256，"
                "与开工实测 8633bda5 锚 fail-closed 一致）；本轮新建派生指"
                "引 observation-guidance-r23.md=机械变换产物（同参重建逐字"
                "节一致+防覆写守卫）——r19 轮 s70「r15 指引机械变换派生 "
                "r19 指引」先例同型"),
            "chain_anchors": {
                "parent_1_base_guidance_r19": {
                    "path_rel": (
                        "out/v3-tl2/calibration/observation-guidance-r19.md"),
                    "sha256_measured": guidance19_sha,
                    "sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
                    "role": "指引变换基座（两父之一）；只读零写入",
                },
                "parent_2_round22_dev_record": dev_ref,
                "r22_prep_record_structure_lineage": {
                    "path_rel": (
                        "out/v3-tl2/calibration/r22-prep-record.json"),
                    "sha256": r22_record_sha,
                    "cross_check": "24 键顶层结构逐键镜像（本轮判据/结构血"
                                   "统= r22）",
                },
                "run_r22_metric_anchor": run_ref,
                "render_witness_r14b_byte_reuse": {
                    "path_rel": (
                        "out/v3-tl2/calibration/render-witness-r14b.json"),
                    "sha256": witness_sha,
                },
                "evaluation_protocol_v1_preserved": {
                    "path_rel": (
                        "out/v3-tl2/calibration/evaluation-protocol-v1.md"),
                    "sha256": protocol_v1_sha,
                },
                "evaluation_protocol_v2_holdout_not_activated": {
                    "path_rel": (
                        "out/v3-tl2/calibration/evaluation-protocol-v2.md"),
                    "sha256_measured": protocol_v2_sha,
                    "sha256_prefix_expected": EVAL_PROTOCOL_V2_SHA_PREFIX,
                    "note": ("holdout 协议冻结件（s79 登记在案）本轮不启用"
                             "——v2 生效≠holdout 启动；本轮协议口径=v1.1+"
                             "v1.2"),
                },
                "consistency_assertion_measurements": seg_bytes,
            },
        },
        "changed_variables": [
            {
                "id": "guidance-s6-frame-box-convergence-clause",
                "axis": "output_format_report_discipline（输出格式/报告纪"
                        "律轴）",
                "axis_note": (
                    "非判据调参轴重开：axis-experiment-plan-r17-r20 三轴"
                    "（判据侧轴1/轴2/轴3）收束决议与轴停止决议不变；本变量"
                    "作用于报告输出几何纪律（守门 G2 的 hygiene 轴），不触"
                    "碰任何类别判据、弃权判据与阈值"),
                "target": (
                    "observation-guidance-r23.md §6（新增 bullet：注意段之"
                    "后、格式示例小节之前；全文逐字见 guidance_reuse."
                    "edit_list[5].text_full）"),
                "description": (
                    "§6 增补报告框收敛条款：frame_box_pct 的语义钉住为「该"
                    "旗所指现象的物理位置」而非「该区域的概貌」——必须收窄"
                    "到现象本体的最小外接（单个文字实例/单个图元/单组直接相"
                    "连图元），禁止因描述便利扩大到邻域或整区；同一类现象含"
                    "多个互不直接相连的离散实例时逐实例分旗、各配小框（"
                    "flag_id 编号可连续）；条款为报告框几何纪律：旗标产出与"
                    "否、类别判定、弃权判据与报告义务零变更，弃权旗疑似区域"
                    "框同样适用；随变更的机械变换同步项（非独立变量）：轮次"
                    "身份四处更新（标题/round_id_constant/声明日期/本轮性"
                    "质行）、变更声明节正文整体重写、§6 示例旗 ID 前缀机械"
                    "替换 R19T-→R23T-（4 处）/R19B-→R23B-（1 处）/"
                    "reader-r19→reader-r23（1 处）——s48/s54/s63/s67/s70 "
                    "机械变换先例同型"),
                "instrument_change": False,
                "attribution_channel": (
                    "G2 出局条目数清零（top 视非弃权旗标 frame_box_pct 几"
                    "何门面积比出局条目数=0；对照 run-r19=0、run-r22=2 在"
                    "案）主判据=hypothesis_test.adjudication 三支"
                    "（replicated_hygiene：G2=0 且 G1 维持且 M1∈[0.361538, "
                    "0.561538] r19±0.10；confounded：G2 仍>0 且 M1 在带内；"
                    "perturbed：M1 出带）"),
            },
        ],
        "manipulated_factor": (
            "唯一操纵因素=判读指引 §6 增补报告框收敛条款（输出格式/报告纪"
            "律轴单点增补；observation-guidance-r23.md 机械变换派生）；渲"
            "染（四图字节复用）/GT/阈值/协议与 §2–§5/§7/§4/§5A 判据文本零"
            "变更"),
        "unchanged_components": [
            {
                "byte_reuse": True,
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "note": "开工时 sha256_file 实测四 PNG 并与 render-witness-"
                        "r14b.json 登记值逐字比对（bottom=renders.applied/"
                        "prep1.sha256；top=top_zero_change_copies.sha256）"
                        "——四图即 r14–r22 轮盲读所用同一批文件；本轮零重"
                        "渲染、零仪器变更",
                "pngs": png_checks,
                "witness": "render-witness-r14b.json（b63771f9，fail-closed "
                           "复核）",
            },
            "判读指引保留区逐字保留（r19 基座 8633bda5 机械变换派生；脚本 "
            "substring 断言 fail-closed）：§2 类别枚举、§3 位置口径（含邻"
            "域收窄判据）、§3A 判据示例、§4 全文（含量化判据 (i)(ii)(iii)、"
            "(iii) 接触性判据、(iii-a) 可操作分辨条款、三路出口、反放宽条款"
            "「仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理"
            "由」原文逐字保留）、§5 courtyard 说明、§5A 渲染配色仪器注记、"
            "§7 格式对齐提示——r23 与 r19 的 §2–§5、§7 逐字一致；§6 除增"
            "补条款与前缀机械替换外逐字不变",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r22 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用；几何门照常独立计算）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件；evaluation-protocol-v2=holdout 冻结件"
            "本轮不启用，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口径"
            "在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "度量设计五条与聚合口径：沿 r22-prep-record measurement_design"
            ".items 同一口径（仅轮次标识、reader 前缀与渲染件名按 r23 改"
            "写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16/"
            "R18/R19/R20/R22 完全相同文件：白墨图元→橙 (255,165,0)、板内"
            "空隙白→绿 (0,128,0)、其余层 kicad 原配色不变；四 PNG "
            "sha256_file 实测=witness-r14b 登记值 fail-closed 比对一致）—"
            "—渲染零变更；本轮唯一判读变更=§6 报告框收敛条款（输出几何纪"
            "律、非 bottom 配色或判读口径变更）；bottom 视判读口径沿用 r4 "
            "指引原文不改（top/bottom 判读口径在图像空间完全一致、不做镜像"
            "换算）；bottom 零旗标分母=0 时弃权率按 cal._ratio 先例=None "
            "口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R23 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r22-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例、6 智能体各包两板、编号跨"
                "板连续；reader 前缀 R23T/R23B（随本轮指引 §6 落盘固化、"
                "派发命名与指引一致）；图像=renders-r14b 四图（字节复用）；"
                "聚合口径与 s71/s74/s77 比较脚本同血统；代表配置/逐实例/"
                "双口径分列）"),
            "items": [
                {
                    "item": 1,
                    "name": "主记录单位=实例",
                    "text": (
                        "每实例（6 个 reader 实例=智能体，各包两板：同一实"
                        "例先 applied 后 prep1）给出其视角两板合计的 "
                        "flag_count、abstain_count、abstain_rate（分母=该"
                        "实例该视角全部旗标，跨两板合计）、非弃权旗标清单、"
                        "逐旗与 GT 的 containment/area_ratio 匹配明细（比较"
                        "器 fail-closed 校验照旧；flag_id 编号同实例跨板连"
                        "续）"),
                },
                {
                    "item": 2,
                    "name": "视角层聚合",
                    "text": (
                        "每视角 3 实例的 flag_count/abstain_rate/matches 各"
                        "给中位数+最小值+最大值，如实三分列、不取整"),
                },
                {
                    "item": 3,
                    "name": "GT 匹配聚合双口径",
                    "text": (
                        "union（≥1 实例命中即计）与 agreement（≥2/3 实例命"
                        "中才计）两口径并列报告，均如实、不二选一；逐 GT 条"
                        "目给出 matched_by_count（0..3）"),
                },
                {
                    "item": 4,
                    "name": "联合门评价（APR-0011）",
                    "text": (
                        "代表配置=每视角取 flag_count 中位数实例组成代表配"
                        "置，计算一轮 joint 结果；同时如实给出 per-metric 实"
                        "例间范围（min..max）；代表配置 joint 结果、"
                        "per-metric 实例间范围、逐实例原始记录（item 1）三"
                        "者并列如实呈现，不合并、不挑优；APR-0011 阈值零改"
                        "动"),
                },
                {
                    "item": 5,
                    "name": "bottom 零旗标处理",
                    "text": (
                        "沿用库侧 cal._ratio 先例（pcbflow/calibration.py "
                        "_ratio：零分母→None）——实例/视角层遇零旗标分母"
                        "时弃权率=None+文字说明，不编造数值（r10 run-record "
                        "bottom=0/0→None 与 r22 bottom-i1 同口径在案）"),
                },
            ],
        },
        "hypothesis_test": HYPOTHESIS_TEST,
        "attribution_plan": {
            "declaration": (
                "本轮恰一个实验变量（判读指引 §6 报告框收敛条款=输出格式/"
                "报告纪律轴单变量；渲染/GT/阈值/协议零变更）、检验恰一个假"
                "设（hypothesis_id=r22-g2-bifurcation-frame-box-hygiene-"
                "attribution：r22 的 G2 破坏主因=报告框过宽——现象本体框 "
                "vs 邻域/整区框）；归因目的=G2 出局清零是否由框收敛条款达"
                "成且 M1 量级保持——r22 字面降级（字母=regressed、维持不改"
                "写）的归因判别（报告框 hygiene vs 深层混杂）；字母/机制观"
                "察/度量教训三分记账（mechanism_observation_separate 与 "
                "metric_lesson_separate 单列，不凌驾三支裁决）"),
            "primary_channel": {
                "change": (
                    "guidance-s6-frame-box-convergence-clause（判读指引 §6 "
                    "单点增补；非判据调参、非渲染/GT/阈值/协议变更——指引"
                    "由 r19 基座机械变换派生 observation-guidance-r23.md）"),
                "metric": (
                    "G2 出局条目数（top 视非弃权旗标 frame_box_pct 几何门"
                    "面积比出局条目数）清零与否+M1（top 全旗聚合弃权率，12 "
                    "派次全口径）落点归因裁决（三支）：replicated_hygiene="
                    "G2=0 且 G1 维持且 M1∈[0.361538, 0.561538]（r19±0.10）；"
                    "confounded=G2 仍>0 且 M1 在带内；perturbed=M1 出带——"
                    "详见 hypothesis_test.adjudication；M4/M2/三族计数/援引"
                    "计数单列机制观察、不进裁决"),
                "replicated_hygiene": (
                    "G2 出局条目=0 且 G1 维持且 M1 带内 → r22 字面降级归因"
                    "=报告框 hygiene（字母口径=replicated_hygiene 支），"
                    "r19 量级复制结论升级"),
                "confounded": (
                    "G2 出局条目仍 >0 且 M1 在带内 → 框宽非（唯一）主因，"
                    "归因转向（字母口径=confounded 支；新出局条目逐条摘录"
                    "入机制观察）"),
                "perturbed": (
                    "M1 出带 → 框收敛扰动判读本身，降级为度量教训如实单列"
                    "（字母口径=perturbed 支）"),
            },
            "guard_channel": {
                "metric": (
                    "G2'=top 视非弃权旗标 frame_box_pct 几何门面积比出局条"
                    "目数=0（对照 run-r19=0、run-r22=2 在案——本轮主通道计"
                    "数）；G1=bottom courtyard 非弃权 0/0/0 维持（对照 "
                    "r15–r19 与 r22 在案 0/0/0、r20 破坏 2/0/0 在案=分岔记"
                    "录；G1 为 (iii-a) 间隙支「不得弃权」方向的反向风险守"
                    "门）；G3 冻结纪律照常"),
                "requirement": (
                    "§6 报告框收敛条款落盘为本轮指引文本；§3 收窄判据逐字"
                    "保留（§2–§5 substring 断言 fail-closed），非弃权框仍"
                    "须满足几何门；G2 仍>0→confounded 支命中（归因转向）；"
                    "G1 破坏（若发生）→三支字母口径均不命中、按 guard_"
                    "channel 如实登记为守门破坏（预注册三支恰三支，其余情"
                    "形如实描述、不新增字母支、不升级归因）"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角"
                "层三分列聚合+GT 匹配双口径+联合门代表配置/范围并列；"
                "APR-0011 阈值零改动）；bottom GT 无源=bottom 旗标与 GT 匹"
                "配应为空（结构性在案，不影响收敛计数口径）；三支裁决/机制"
                "观察/度量教训三分记账、互不凌驾；归因分组逻辑由编排侧在 "
                "close 包执行；指引内零 GT、零轮次结果数字（基线数字仅入本"
                "编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止"
                    "（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "框收敛不是判据收紧也不是放宽：§6 报告框收敛条款只约束报告框的"
            "几何口径（输出格式/报告纪律轴），旗标产出与否、类别判定标准、"
            "弃权判据与报告义务零变更——§4 全文（含反放宽条款「仅因形态不"
            "熟悉、不确定其设计含义，不构成判为正常设计特征的理由」、量化"
            "判据 (i)(ii)(iii)、(iii-a) 可操作分辨条款、三路出口）与 §3 位"
            "置口径（含邻域收窄判据）随 r19 基座逐字保留（§2–§5/§7 "
            "substring 断言 fail-closed），判据侧零措辞调整空间；显式防止"
            "「框收敛压弃权率」的误读：弃权旗同样受框纪律约束（条款原文："
            "弃权旗的疑似区域框同样适用本条），弃权判据零变更、弃权率不因"
            "框几何纪律被系统性压低或抬高（G1 守门照常独立计算）；本轮三支"
            "判据（replicated_hygiene/confounded/perturbed）只用于归因方"
            "向，不触碰 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与任何阈值常量（CONTAINMENT_MIN/"
            "AREA_RATIO_MAX，只作口径引用）——门照常独立计算；不构成任何"
            "阈值反向放宽"),
        "pre_round_review": {
            "status": "satisfied_by_plan",
            "basis": (
                "round22-dev-record honest_conclusion 下一候选建议（b）（对"
                " G2 的 2 条出局条目做机制归因=报告框 hygiene 核实、须新预"
                "注册轮——原文逐字见 guidance_reuse.chain_anchors."
                "parent_2_round22_dev_record.candidate_b_quote）+用户 "
                "2026-09-10 拍板「r22 复制轮（字母=regressed）后执行 G2 报"
                "告框归因轮」；单变量=§6 报告框收敛条款（输出格式/报告纪律"
                "轴），渲染/GT/阈值/协议零变更、判据侧零触碰（§2–§5/§7 与 "
                "§4/§5A 逐字保留断言 fail-closed）——预注册先于盲读冻结"
                "（本记录）；axis-experiment-plan-r17-r20 轴停止决议不变、"
                "r22 字母裁决不改写"),
        },
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "version": "v1.1+v1.2 维持",
            "changes": [],
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口"
                            "径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视"
                "角层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径"
                "并列、联合门代表配置+实例间范围并列（measurement_design "
                "五条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派"
                "发指令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/"
                "放大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查"
                "看原图（同一原图可重复查看）」——仪器行为钉住；属派发层，"
                "读者上下文=指引+单张 PNG+派发指令（含规约条款），零 GT；"
                "不影响判读语义——分类判据零变更，仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": (
                    "out/v3-tl2/calibration/evaluation-protocol-v1.md"),
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_v1_sha,
                "zero_byte_preserved": protocol_v1_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11–r22 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件；evaluation-protocol-v2.md=holdout 协议冻结件"
                    "（s79 登记在案）本轮不启用——v2 生效≠holdout 启动，"
                    "本轮协议口径=v1.1+v1.2"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）=6 个 reader 实例（智能体）各包两板；本轮实"
                "例群全重抽（3 新实例/视角）；实例上下文=指引（observation-"
                "guidance-r23.md=本轮落盘新指引）+单张 PNG（renders-r14b "
                "四图）+派发命名指令（含 v1.2 工具行为规约硬性条款：纯 "
                "Read 内联判读、禁止任何程序化图像处理），零 GT、零历史判读"
                "件、零诊断/探针内容、零 r22 现象描述注入（本记录所载出局条"
                "目转述为编排侧引用，不进任何 reader 上下文）；两波次串行保"
                "序（同一实例先 applied 后 prep1，flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r23-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R23T/R23B（随本轮指引 §6 落盘固化——本轮派发层命名与指引 "
                "§6 一致、无前缀差异登记需求；对照 r22：指引字节复用致其 "
                "§6 落盘原文为 R19T-/R19B-、派发层覆盖 R22T/R22B=前缀差异"
                "登记在案（r16 先例：r15 指引+R16T 前缀）；r23 与 r19「随"
                "指引落盘固化」路径相同）；实例间编号独立，同实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic，零内容判读、零像素读取）、ground-truth-*、reader-raw-*、"
            "derivation-log-*、任何 compare/评估产物、diag 内容（零读取）；"
            "本脚本只读输入=observation-guidance-r19.md（判读指引变换基座；"
            "8633bda5 锚 fail-closed，只读零写入——派生文本由本脚本机械变"
            "换构造）、round22-dev-record.json（b4b8fbe9 两父之二；仅读 "
            "axis_experiment_ledger 实测四元组、g2_bifurcation_record 计数"
            "与两条出局条目摘录（GT 字段不转录）与 honest_conclusion 候选"
            "(b)原文——条款设计依据）、r22-prep-record.json（63346ee6；结"
            "构血统与 24 键镜像来源+descriptive_boundary_note 照抄源）、"
            "calibration-run-r22.json（80a12c05 锚；仅读 hypothesis_test "
            "顶层判据冻结值字段+guard_channel+verdict——M1=16/41=0.390244/"
            "verdict=regressed/G2 几何门 0→2；其 GT 匹配与逐旗明细内容不读"
            "取、不入记录）、render-witness-r14b.json（b63771f9 锚 fail-"
            "closed；四 PNG 见证登记值）、evaluation-protocol-v1.md（仅在"
            "盘+哈希复核，锚=22dc7337）、evaluation-protocol-v2.md（仅在盘"
            "+哈希复核，锚=365b67ef；holdout 冻结件本轮不启用）；"
            "renders-r14b 四 PNG 仅哈希+magic（渲染零变更以 witness 登记哈"
            "希比对为准）；本轮恰三个新建文件=scripts/s80_calibration_r23_"
            "prep.py（生成器本体）与 observation-guidance-r23.md、"
            "r23-prep-record.json（本轮仅有的两个 out/ 新建文件；本轮无探"
            "针/诊断脚本）；reader 派发（后续编排侧执行）上下文=observation"
            "-guidance-r23.md+单张 PNG（renders-r14b）+派发指令（R23T/"
            "R23B=随指引落盘、reader-r23-{top,bottom}-i{1,2,3}、v1.2 工具"
            "行为规约硬性条款），零 GT、零历史判读件、零 r19/r22 判读结果注"
            "入、零指引之外的解释；视觉判读禁止由编排/收口包兼任；跨实例/"
            "跨视角禁止交流（12 次盲读相互独立、不得交换判读信息——独立性"
            "是多实例协议的前提，亦为本轮归因裁决有效性的前提）。"),
        "no_visual_reading": True,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R19, DEV_RECORD_R22, R22_PREP_RECORD, RUN_R22,
                 WITNESS_R14B, EVAL_PROTOCOL_V1, EVAL_PROTOCOL_V2):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件 GUIDANCE_R23 / RECORD 不做前置硬拒绝：落盘阶段防覆写守卫按
    # 红线口径执行——已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等
    # 通过（零覆写）。（首轮创建前置=目标不存在，已由编排侧开工确认。）

    # ---- 两父哈希先验（任何写路径之前；fail-closed）----
    guidance19_sha = _sha(GUIDANCE_R19)
    dev22_sha = _sha(DEV_RECORD_R22)
    if not guidance19_sha.startswith(GUIDANCE_R19_SHA_PREFIX):
        _fail(f"两父哈希先验失败：observation-guidance-r19.md sha 前 8="
              f"{guidance19_sha[:8]} != 预期 {GUIDANCE_R19_SHA_PREFIX}"
              f"（变换基座疑被改动，立即停止）")
    if not dev22_sha.startswith(DEV_RECORD_R22_SHA_PREFIX):
        _fail(f"两父哈希先验失败：round22-dev-record.json sha 前 8="
              f"{dev22_sha[:8]} != 预期 {DEV_RECORD_R22_SHA_PREFIX}"
              f"（条款设计依据疑被改动，立即停止）")

    # ---- 其余冻结锚验证（fail-closed）----
    r22_record_sha = _sha(R22_PREP_RECORD)
    run22_sha = _sha(RUN_R22)
    witness_sha = _sha(WITNESS_R14B)
    protocol_v1_sha = _sha(EVAL_PROTOCOL_V1)
    protocol_v2_sha = _sha(EVAL_PROTOCOL_V2)
    for sha, prefix, label in (
            (r22_record_sha, R22_PREP_RECORD_SHA_PREFIX, "r22-prep-record"),
            (run22_sha, RUN_R22_SHA_PREFIX, "calibration-run-r22"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (protocol_v1_sha, EVAL_PROTOCOL_V1_SHA_PREFIX,
             "evaluation-protocol-v1"),
            (protocol_v2_sha, EVAL_PROTOCOL_V2_SHA_PREFIX,
             "evaluation-protocol-v2")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，立"
                  f"即停止）")

    # ---- 基座只读装载（零写入）----
    base_text = GUIDANCE_R19.read_text(encoding="utf-8")
    if hashing.sha256_text(base_text) != guidance19_sha:
        _fail("r19 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")

    # ---- 结构探测（r22 实测锚与授权链锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    run22 = json.loads(RUN_R22.read_text(encoding="utf-8"))
    dev22 = json.loads(DEV_RECORD_R22.read_text(encoding="utf-8"))
    r22_record = json.loads(R22_PREP_RECORD.read_text(encoding="utf-8"))
    if r22_record.get("kind") != "tl2_calibration_r22_prep_record" or \
            r22_record.get("round_label") != "r22" or \
            r22_record.get("schema_version") != "3.0":
        _fail("r22-prep-record 先例件结构漂移")
    probe_witness(witness)
    png_checks = check_renders_byte_reuse(witness)
    dev_ref = probe_dev_record_r22(dev22, dev22_sha)
    run_ref = probe_run_r22(run22, run22_sha)
    # descriptive_boundary_note 照抄血统源核对（fail-closed）
    lineage_note = (r22_record.get("hypothesis_test", {})
                    .get("adjudication", {})
                    .get("descriptive_boundary_note", ""))
    if HYPOTHESIS_TEST["adjudication"]["descriptive_boundary_note"] != \
            lineage_note:
        _fail("descriptive_boundary_note 未照抄 r22-prep-record 血统原文")

    # ---- 判据逐字断言链：预注册判据原文→json.loads→常量→记录字段 ----
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != \
            "r22-g2-bifurcation-frame-box-hygiene-attribution":
        _fail("hypothesis_test.hypothesis_id 不符")
    adj = HYPOTHESIS_TEST["adjudication"]
    if set(adj.keys()) != {"replicated_hygiene", "confounded", "perturbed",
                           "mechanism_observation_separate",
                           "metric_lesson_separate",
                           "descriptive_boundary_note"}:
        _fail(f"adjudication 三支+单列结构不符：{sorted(adj.keys())}")

    # ---- 指引派生 + 一致性断言 ----
    derived_text = derive_guidance_r23(base_text)
    seg_bytes = assert_guidance_r23(derived_text, base_text)
    derived_bytes = derived_text.encode("utf-8")
    guidance23_sha = hashing.sha256_text(derived_text)
    guidance23_bytes_n = len(derived_bytes)
    # 同参重建自证（纯函数）
    derived_rebuild = derive_guidance_r23(base_text)
    if derived_rebuild.encode("utf-8") != derived_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: observation-guidance-r23")

    # ---- 指引落盘（防覆写守卫 + 回读验字节；唯一写入目标=GUIDANCE_R23）----
    if GUIDANCE_R23.exists():
        if GUIDANCE_R23.read_bytes() != derived_bytes:
            _fail("observation-guidance-r23.md 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[r23-prep] 重跑自证：observation-guidance-r23.md 重建字节与"
              "既有文件逐字节一致（幂等通过，零覆写）")
    else:
        GUIDANCE_R23.write_bytes(derived_bytes)
        if GUIDANCE_R23.read_bytes() != derived_bytes:
            _fail("回读不一致: observation-guidance-r23.md")

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance19_sha=guidance19_sha,
        guidance19_bytes_n=len(base_text.encode("utf-8")),
        guidance23_sha=guidance23_sha,
        guidance23_bytes_n=guidance23_bytes_n,
        seg_bytes=seg_bytes,
        r22_record_sha=r22_record_sha,
        dev_ref=dev_ref,
        run_ref=run_ref,
        witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha,
        protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks)
    # 结构镜像断言：顶层键集合与 r22-prep-record 24 键逐键镜像
    missing = sorted(set(r22_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r22_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r22-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # 结构自证（单变量轮口径）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（渲染零变更）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True")
    if len(record["changed_variables"]) != 1:
        _fail(f"changed_variables 必须恰 1 项（实测 "
              f"{len(record['changed_variables'])}）")
    cv = record["changed_variables"][0]
    if cv["id"] != "guidance-s6-frame-box-convergence-clause":
        _fail("changed_variables[0].id 不符")
    if record["guidance_reuse"]["mode"] != "mechanical_transform_derive":
        _fail("guidance_reuse.mode 必须为 mechanical_transform_derive")
    if record["guidance_reuse"]["derived_sha256"] != guidance23_sha:
        _fail("guidance_reuse.derived_sha256 与实测不符")
    if not record["guidance_reuse"]["base_sha256"].startswith(
            GUIDANCE_R19_SHA_PREFIX):
        _fail("guidance_reuse.base_sha256 与 8633bda5 锚不符")
    if record["guidance_reuse"]["byte_size"]["base"] != 21435:
        _fail("guidance_reuse.byte_size.base 不符（预期 r19 指引 21435 B）")
    if record["guidance_reuse"]["byte_size"]["delta"] <= 0:
        _fail("guidance_reuse.byte_size.delta 应为正（增补条款+头部重写）")
    if len(record["guidance_reuse"]["edit_list"]) != 9:
        _fail("guidance_reuse.edit_list 必须恰 9 组锚定编辑")
    if record["round_id_constant"] != ROUND_ID or \
            record["round_label"] != "r23" or \
            record["declared_date"] != DATE_CONSTANT:
        _fail("轮次标识不符（2026-09-10-r23 / r23 / 2026-09-10）")
    rn = record["round_nature"]
    for needle in ("单变量报告框收敛归因轮", "输出格式/报告纪律轴",
                   "非判据调参轴重开", "轴停止决议不变", "changed_variables=1",
                   "轮次身份四处更新", "R19T-→R23T-", "逐字保留",
                   "机械变换派生"):
        if needle not in rn:
            _fail(f"round_nature 缺「{needle}」声明")
    if record["manipulated_factor"] is None or \
            "§6 增补报告框收敛条款" not in record["manipulated_factor"]:
        _fail("manipulated_factor 不符（唯一操纵因素=§6 条款）")
    nl = record["no_loosening_note"]
    for needle in ("不是判据收紧也不是放宽", "弃权旗同样受框纪律约束",
                   "框收敛压弃权率", "CONTAINMENT_MIN/AREA_RATIO_MAX"):
        if needle not in nl:
            _fail(f"no_loosening_note 缺「{needle}」声明")
    # adjudication 带宽定点整数与判据布尔（记录侧自证）
    if not (REPLICATED_LO_6DP * TOP_FLAGS_R22 <=
            TOP_ABSTAIN_R22 * 1000000 <=
            REPLICATED_HI_6DP * TOP_FLAGS_R22):
        _fail("记录侧自证失败：r22 M1 定点整数不在带内")
    if "361538×top_flags" not in adj["replicated_hygiene"] or \
            "abstain_count×1000000" not in adj["replicated_hygiene"] or \
            "561538×top_flags" not in adj["perturbed"]:
        _fail("adjudication.replicated_hygiene 缺定点整数判定口径")
    # measurement_design 五条
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    for needle in ("renders-r14b", "R23T/R23B", "6 智能体各包两板",
                   "s71/s74/s77 比较脚本同血统"):
        if needle not in md["preregistration_declaration"]:
            _fail(f"measurement_design 预注册声明缺 {needle!r} 口径")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"][
            "zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved "
              "必须为真")
    if "R23T/R23B" not in record["protocol_amendment"]["naming"] or \
            "随本轮指引 §6 落盘固化" not in \
            record["protocol_amendment"]["naming"]:
        _fail("protocol_amendment.naming 缺前缀落盘固化登记")
    if len({p["sha256_measured"] for p in png_checks}) != 3:
        _fail("四 PNG sha 集合应为 3 个不同值（两 bottom 同哈希）")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance19_sha=guidance19_sha,
        guidance19_bytes_n=len(base_text.encode("utf-8")),
        guidance23_sha=guidance23_sha,
        guidance23_bytes_n=guidance23_bytes_n,
        seg_bytes=seg_bytes,
        r22_record_sha=r22_record_sha,
        dev_ref=dev_ref,
        run_ref=run_ref,
        witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha,
        protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r23-prep-record")

    # ---- 防覆写守卫 + 落盘（唯一写入目标=RECORD；基座零写入）----
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r23-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r23-prep] 重跑自证：r23-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r23-prep-record.json")

    # ---- 汇总打印 ----
    print("[r23-prep] 两父哈希先验 PASS：变换基座 observation-guidance-"
          f"r19.md={guidance19_sha}（8633bda5，只读零写入，"
          f"{len(base_text.encode('utf-8'))} B）+条款设计依据 round22-dev-"
          f"record.json={dev22_sha}（b4b8fbe9）")
    print("[r23-prep] 结构血统锚 PASS：r22-prep-record="
          f"{r22_record_sha}（63346ee6，24 键镜像源）；run-r22="
          f"{run22_sha}（80a12c05，M1=16/41=0.390244、verdict=regressed、"
          f"G2 几何门 0→2）；witness-r14b={witness_sha}（b63771f9）；"
          f"protocol-v1={protocol_v1_sha}（22dc7337，零字节保留）；"
          f"protocol-v2={protocol_v2_sha}（365b67ef，holdout 冻结件本轮不"
          f"启用）")
    print("[r23-prep] 渲染零变更自证（四 PNG 实测=witness 登记值；字节复"
          "用、零仪器变更）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r23-prep] r22 实测锚自洽断言 PASS：0.461538±0.10=[0.361538, "
          "0.561538]；16/41=0.390244；定点整数 16000000∈[14823058, "
          "23023058] 带内；0.771429−0.461538=0.309891；出局条目 "
          "area_ratio 16.406371/16.369542 均 >10")
    print("[r23-prep] 指引机械变换 PASS：9 组锚定编辑（标题/round_id/日期/"
          "性质行/变更声明重写/§6 条款插入/前缀 4+1+1）；轮次身份四处更新"
          "+变更声明整体重写+§6 增补+前缀替换")
    print(f"[r23-prep] 一致性断言 PASS：§2–§5 逐字一致（{seg_bytes['seg2_5_bytes']} B "
          f"substring）+§7 逐字一致（{seg_bytes['seg7_bytes']} B substring 至文"
          f"末）+§6 区块等价复核；反放宽句恰 1 次；R19 系 token 残留=0（小"
          f"写 r19 恰 1 处=基座血统引用）；新条款恰 1 次（needle 族 7 项各"
          f"恰 1）；R23T-×4/R23B-×1/reader-r23-×1；零轮次结果数字")
    print("[r23-prep] §6 报告框收敛条款落盘全文：")
    print("  " + CLAUSE_TEXT)
    print("[r23-prep] 预注册三支裁决（先于盲读冻结）PASS："
          "replicated_hygiene=G2=0 且 G1 维持且 M1∈[0.361538, 0.561538]"
          "（r19±0.10，6 位定点整数交叉相乘）；confounded=G2 仍>0 且 M1 "
          "在带内→归因转向；perturbed=M1 出带→度量教训如实单列；"
          "descriptive_boundary_note 照抄 r22-prep-record 血统原文")
    print(f"[r23-prep] 顶层键镜像断言：与 r22-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）；changed_variables=1；edit_list=9 组")
    print(f"[r23-prep] 工件 sha256：observation-guidance-r23.md="
          f"{_sha(GUIDANCE_R23)}")
    print(f"[r23-prep] 工件 sha256：r23-prep-record.json={_sha(RECORD)}")


if __name__ == "__main__":
    main()
