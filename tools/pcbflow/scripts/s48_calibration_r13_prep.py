#!/usr/bin/env python
"""CAL-R13-PREP：R13 指引侧单变量变更轮（§4 存在性判断一般判据可操作
化轮）预备见证包（写 out/v3-tl2/calibration/observation-guidance-r13.md
与 r13-prep-record.json）。

R13 轮性质（预注册，非事后）：**单变量指引侧变更轮**——基准指引=
observation-guidance-r12.md（0ac22fcd），唯一指引侧实质变更=§4 存在性
判断一般判据 (i)(ii) 整段替换为量化版 (i)(ii)(iii)（系统性正常特征判据
（量化）/关注现象判据/接触性判据；引导句逐字保留）+ §4 末尾增补 r13
对照说明；执行 round12-dev-record next_iteration_targets[0]（用户
2026-09-08 拍板排程本轮，并拍板「R13 方向需额外评审+视觉 MCP 放开用
量」——额外评审已由编排侧以 3 名独立诊断审查员（D1/D2/D3，非校准
reader、零 flag 零 GT 接触）执行，报告 diag-r13-review/D1.md、D2.md、
D3.md，先实测 sha256 后引用；属编排侧诊断证据、不属盲读链，R13 reader
仍按盲读纪律执行，零诊断报告内容）。协议侧零变更：v1.2 沿用（无新增
版本，纯 Read 直读规约原文适用；v1.1 的 n=3 多实例与聚合口径全部沿
用）。渲染零字节复用 R5 冻结件（零仪器变更、零重渲染）。本脚本只做
PREP，不做盲读、不做任何视觉判读、不写轮测试。

检验假设（hypothesis_id=r12-dev-record-candidate-0-s4i-operationalize）：
§4 存在性判据可操作化后，bottom 视同批形态的跨实例裁决收敛——量化判
据使该类形态被一致地判入「系统性正常特征→不报告」路径，单实例大规模
非弃权报告消失。支持=bottom 视角层 courtyard 类非弃权旗数极差 ≤5 且
bottom 聚合非弃权 courtyard 旗总数 ≤5（且 top 几何门守门无回升）；拒
绝=极差 >5 或聚合 ≥10。基线数字（r12 bottom courtyard 非弃权旗数
18/0/0、极差=18；三裁决=18 非弃权/0 旗/2 弃权）只作为已落盘 run-record
在案值记入本编排侧 prep-record，不进任何指引文件（指引零轮次结果数
字；诊断报告数字同样只入本记录、不进指引）。

功能（out/ 仅新建两个文件：observation-guidance-r13.md、
r13-prep-record.json；既有产物零改动，observation-guidance-r12.md 零
字节不动）：

  1. fail-closed 复核 observation-guidance-r12.md：sha256 前 8=0ac22fcd
     （不符即停=基准指引疑被改动）；并与 r12-prep-record.json
     guidance.sha256 登记值交叉核对（链自洽）。
  2. fail-closed 复核 r12-prep-record.json：sha256 前 8=d393cf27、
     schema_version=3.0、kind=tl2_calibration_r12_prep_record、
     round_id_constant=2026-09-07-r12（不符即停）；探测
     renders_reuse.png_witness 结构取 renders-r5 四件 PNG 见证常量并要
     求登记自洽（sha256_measured == sha256_witness_constant 且
     match_to_witness_constant 为真；不符即停）；framing_reference.
     sha256 与盘上实测交叉核对（链自洽）；protocol_amendment.
     v1_file_preserved 登记值与盘上 evaluation-protocol-v1.md 实测交
     叉核对（链自洽）。
  3. fail-closed 复核 R5 渲染输入链：render-framing-r5.json
     frozen_inputs.r4_frozen_pdfs 四件冻结 PDF sha256 实测比对（全
     match 才继续）；并复核 frozen_inputs 无 renders-r5 输出 PNG 哈希
     登记字段（r5 前缀键不存在、r4_frozen_png_sha256_reference 在场，
     不符即停）。
  4. fail-closed 复核 renders-r5 四件 PNG：magic + sha256 实测 vs 上述
     见证常量（全 match 才继续；防改动冻结渲染）。
  5. fail-closed 复核 round12-dev-record.json：sha256 前 8=1411dab6、
     round_id=2026-09-07-r12（不符即停）；从 next_iteration_targets 按
     内容标记唯一定位 §4(i) 可操作性修订候选（实测索引回填并要求
     =[0]）；取 run_record_ref 的 path_rel/sha256 作基线在案引用。
  6. fail-closed 复核 diag-r13-review 三报告：D1/D2/D3 sha256 实测 vs
     冻结锚常量（哈希接触、零内容解析；不符即停=诊断证据疑被改动）。
  7. 由 observation-guidance-r12.md 机械变换生成 observation-guidance-
     r13.md（§4 (i)(ii)→(i)(ii)(iii) 可操作化替换，引导句逐字保留；
     §4 末尾 r8 对照说明块之后、§5 之前增补 r13 对照说明；头部标题/
     round_id_constant/声明日期/本轮性质行/本轮变更声明节（四 bullet：
     变更/非放宽/不变/归因计划）按 r12 同款结构重写；机械替换：
     2026-09-07-r12→2026-09-08-r13、R12T-→R13T-、R12B-→R13B-、
     reader-r12→reader-r13，标题轮次标识 R12→R13 一并。其余文本逐字承
     r12）。变换前后逐项计数断言（锚点出现次数不符即停）+输出侧禁词
     断言（零 GT、零轮次结果数字、零诊断报告数字）。
  8. 落盘 r13-prep-record.json（canonical JSON=
     hashing.canonical_json_bytes：ensure_ascii=False / sort_keys /
     indent=1 / LF；顶层键集合与 r12-prep-record 逐键镜像断言，文档化
     差异=+pre_round_review（额外评审记录，本轮新增）；hypothesis_test
     键集合与 r12 逐键镜像零差异；measurement_design 五条照抄
     r12-prep-record 原文）；同参重建两次逐字节一致自证；防覆写守卫
     ——目标文件已存在且重建字节非逐字节等同→FAIL，等同→允许幂等重
     跑（零覆写）；落盘后重读盘面字节回验。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-08 / 2026-09-08-r13）；
hash=sha256_file 字节口径（PNG 仅做哈希与 magic 检查，零内容判读；
诊断报告仅哈希、零内容解析）；无 subprocess / 无网络 / 无主机绝对路
径；不读 GT / reader-raw-* / calibration-run-* / derivation-log-* /
compare 产物（round12-dev-record 仅读 round_id、next_iteration_targets
与 run_record_ref 字段取预注册原文与在案引用；r12-prep-record 仅用于
取 PNG 见证常量与链交叉核对）；无 git。指引文件内零 GT、零轮次结果
数字、零诊断报告数字（输出侧禁词断言执行）。

用法：python scripts/s48_calibration_r13_prep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
R12_PREP_RECORD = CAL_DIR / "r12-prep-record.json"
R12_DEV_RECORD = CAL_DIR / "round12-dev-record.json"
GUIDANCE_R12 = CAL_DIR / "observation-guidance-r12.md"
GUIDANCE_R13 = CAL_DIR / "observation-guidance-r13.md"
RECORD = CAL_DIR / "r13-prep-record.json"
PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
DIAG_DIR = CAL_DIR / "diag-r13-review"

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r13"

#: 冻结基线锚（开工实测给定；不符即停）。GUIDANCE_R12=基准指引（r12 轮
#: 落盘产物；本脚本只读、零写入）；开工/收工由编排侧另验受保护文件；
#: 本脚本内亦 fail-closed 复核。
GUIDANCE_R12_SHA_PREFIX = "0ac22fcd"
R12_PREP_RECORD_SHA_PREFIX = "d393cf27"
R12_DEV_RECORD_SHA_PREFIX = "1411dab6"

#: diag-r13-review 三报告冻结锚（开工实测给定；哈希接触、零内容解析；
#: 不符即停=诊断证据疑被改动）
DIAG_REPORT_ANCHORS = {
    "D1": ("D1.md", "2387daed"),
    "D2": ("D2.md", "b79bc617"),
    "D3": ("D3.md", "c09154a4"),
}

#: round12-dev-record next_iteration_targets 的内容定位标记
#: （§4(i) 可操作性修订候选=指引侧候选=本轮执行的指引侧变更；按标记唯
#: 一定位、实际索引实测回填并要求相符=[0]，不符即停）
MARK_CANDIDATE_S4 = "§4(i) 判据的可操作性修订候选"
MARK_CANDIDATE_S4_PLAN = "单变量纪律"

#: render-framing-r5.json 中 R5 渲染输入侧冻结 PDF 的登记
#: （frozen_inputs.r4_frozen_pdfs；本脚本 fail-closed 实测比对）
FROZEN_PDF_RELS = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: renders-r5 四件 PNG 的固定遍历顺序（确定性；见证常量从 r12-prep-record
#: renders_reuse.png_witness 登记探测取得，不在此硬编码）
RENDERS_R5_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 顶层键集合相对 r12-prep-record 的文档化差异（本轮新增额外评审记录键；
#: 零其他增删）
TOP_LEVEL_KEY_DELTA_REMOVE = ()
TOP_LEVEL_KEY_DELTA_ADD = ("pre_round_review",)

#: hypothesis_test 键集合相对 r12-prep-record 零差异（13 键逐键镜像）
HT_KEY_DELTA_REMOVE = ()
HT_KEY_DELTA_ADD = ()

# ---------------------------------------------------------------------------
# 指引生成（纯函数：r12 全文逐字 + 恰三组变更）
# ---------------------------------------------------------------------------

OLD_TITLE = "# R12 轮 reader 判读指引（observation-guidance-r12）"
NEW_TITLE = "# R13 轮 reader 判读指引（observation-guidance-r13）"

OLD_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-07"
NEW_DATE_LINE = "- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-08"

OLD_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（suspicious_reroute「整段规则周期」"
    "判据收窄轮）+ 协议侧跨轮工具行为规约 v1.2（派发层，读者不可见，见对"
    "照说明）**。渲染零变更（复用 R5 冻结渲染件：零仪器变更、零重渲染）；"
    "本轮指引侧唯一变更=判读指引 §3A 类别 4 示例 c 收窄替换（预注册见"
    "下），指引落盘后由编排侧重新盲读。")

NEW_NATURE_LINE = (
    "- 本轮性质：**单变量指引侧变更轮（§4 存在性判断一般判据可操作化"
    "轮）**。渲染零变更（复用 R5 冻结渲染件）；本轮唯一变更=判读指引 "
    "§4 存在性判断一般判据可操作化替换（预注册见下），指引落盘后由编排"
    "侧重新盲读。")

#: §4 存在性判断一般判据旧段（r8 增补；(i) 起至反放宽条款止；替换锚。
#: 引导句「判断「弃权适用于」条所述……另按以下中性一般启发推理：」不在
#: 替换范围内、逐字保留）
OLD_S4_SEGMENT = (
    "(i) 同一形态在**同类图形之间规则地、成体系地重复出现**（沿阵列、成"
    "排或成组分布，与任何单个图形的缺陷假设无特定关联）→ 更可能是**正常"
    "设计特征**（通用 PCB 域知识内可能存在常规图形解释，如散热辐条/热隔"
    "离盘形态、安装孔、基准点、极性标记类；此处为「可能解释」而非断言，"
    "也不限于所列形态）；(ii) 形态**孤立出现**、或与周边同类图形的常规形"
    "态**不一致**（打破所在组的规律）→ 更可能是**关注现象**。本启发为一"
    "般推理依据，不构成对任何具体板面内容的断言；判「正常设计特征」与判"
    "「关注现象」承担**同等判断责任**——仅因形态不熟悉、不确定其设计含"
    "义，不构成判为正常设计特征的理由（此时仍按「弃权适用于」条处理）。")

#: 替换后的 §4 存在性判断一般判据量化版（包指令给定文本，一字不改；
#: (i)(ii)(iii) 可操作化，结尾反放宽条款原文保留）
NEW_S4_SEGMENT = (
    "(i) **系统性正常特征判据（量化）**——同一形态作为**最小重复单元**"
    "（如单个焊盘/单个图形所带的图元）在同类图形中**至少出现 3 处**、"
    "**沿同一阵列或成组对齐分布**、**出现在至少 2 条不同的阵列/边上**、"
    "且各处**形态尺寸与样式一致**（渲染容差内的微小差异不算不一致）→ 更"
    "可能是**正常设计特征**（通用 PCB 域知识内可能存在常规图形解释，如散"
    "热辐条/热隔离盘形态、安装孔、基准点、极性标记类；此处为「可能解释」"
    "而非断言，也不限于所列形态）。计数以最小重复单元为准；多个单元之间"
    "的联合外观（如相邻轮廓的交叠/搭接）是单元图元相互接近的结果，不得以"
    "「成对出现率未过半」否定系统性；(ii) **关注现象判据**——形态**孤立"
    "出现**（仅 1–2 处）、或与周边同类图形的常规形态**不一致**（打破所在"
    "组的规律）、或位置虽成体系但各处**形态尺寸/样式明显不一致** → 更可"
    "能是**关注现象**；(iii) **接触性判据（判「交叠/接触」类现象前适"
    "用）**——须先分辨**真实接触**（图形材料连通）与**视觉贴近**（存在"
    "小于当前分辨率的间隙）：能负责任区分时按事实处理；无法区分时，接触"
    "与否按存在性不确定处理（按「弃权适用于」条输出弃权旗），不得将视觉"
    "贴近直接计为交叠。本启发为一般推理依据，不构成对任何具体板面内容的"
    "断言；判「正常设计特征」与判「关注现象」承担**同等判断责任**——仅"
    "因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由（此时"
    "仍按「弃权适用于」条处理）。")

#: §4 末尾追加的 r13 对照说明（包指令给定文本，一字不改；置于既有 r8
#: 对照说明块之后、"## 5" 之前）
CONTRAST_NOTE_R13 = (
    "（对照说明（r13 增补）：r8 增补的存在性判断一般判据 (i)(ii) 自本轮"
    "起被上述量化版 (i)(ii)(iii) **可操作化替换**——「规则地、成体系地重"
    "复」细化为可数判据（≥3 处+沿同一阵列/成组对齐+≥2 条不同阵列/边+形"
    "态逐处一致），计数单元显式定为最小重复单元（相邻单元间的联合交叠外"
    "观不得替代单元级计数、成对出现率不构成否定系统性的依据），并新增接"
    "触性判据（真实接触 vs 视觉贴近，不可区分→按存在性弃权）。量化阈值"
    "为一般判据、非期望清单；判断责任标准一字未松（同等判断责任与「仅因"
    "形态不熟悉不构成判为正常设计特征的理由」反放宽条款原文保留）。§4 其"
    "余文本（总原则、两条显式判据、三路出口）、类别封闭集与其余各节一字"
    "未动。）")

SEC_START = "## 本轮变更声明（预注册，非事后）"
SEC_END_ANCHOR = "\n## 1. 角色与任务"

BULLET_CHANGE = (
    "- **变更（指引侧恰一项）：** **§4 存在性判断一般判据 (i)(ii) 可操"
    "作化替换为量化版 (i)(ii)(iii)**——r8 增补判据 (i)「同一形态在同类图"
    "形之间规则地、成体系地重复出现」与 (ii)「孤立出现/与周边同类图形的"
    "常规形态不一致→关注现象」整段替换为：(i) **系统性正常特征判据（量"
    "化）**（同一形态作为最小重复单元至少出现 3 处、沿同一阵列或成组对齐"
    "分布、出现在至少 2 条不同的阵列/边上、各处形态尺寸与样式一致 → 更"
    "可能是正常设计特征；计数以最小重复单元为准，相邻单元间的联合交叠外"
    "观不得替代单元级计数、不得以「成对出现率未过半」否定系统性）；(ii) "
    "**关注现象判据**（孤立出现=仅 1–2 处、打破所在组规律、位置成体系但"
    "形态尺寸/样式明显不一致 → 更可能是关注现象）；(iii) **接触性判据**"
    "（判「交叠/接触」类现象前先分辨真实接触与视觉贴近，无法区分→按「弃"
    "权适用于」条输出弃权旗，不得将视觉贴近直接计为交叠）；并在 §4 末尾"
    "（既有对照说明块之后、第 5 节之前）增补一条 r13 对照说明。全文见 "
    "§4 存在性判断一般判据。措辞中性一般化，零具体板、位号、坐标、数量"
    "期望，零轮次结果数字。")

BULLET_NO_LOOSENING = (
    "- **非放宽声明：** 本轮变更为**可操作化**（把定性裁量细化为可数判"
    "据）——**判断责任标准一字未松**；反放宽条款「仅因形态不熟悉、不确"
    "定其设计含义，不构成判为正常设计特征的理由」**原文保留**于替换后文"
    "本内；判「正常设计特征」与判「关注现象」承担**同等**判断责任原样保"
    "留；「弃权适用于」「弃权不适用于」两条显式判据、总原则「宁可 "
    "abstain 不硬标」、三路出口显式化原文保留；量化阈值为一般判据、非期"
    "望清单，不构成期望数量或分布提示；接触性判据为存在性弃权方向的澄清"
    "（不可区分→弃权），不降低报告义务；§3、§3A、§5、§6、§7 与 §4 其余"
    "文本一字不动；不降低任何存在性、归类、定位或报告的责任门槛。")

BULLET_UNCHANGED = (
    "- **不变：** 渲染（复用 R5 冻结渲染件）、角色与盲读纪律（§1）、类别"
    "枚举（6 类逐字，§2）、§3 邻域框收窄判据与坐标口径、§3A 全部示例（六"
    "类全部示例含示例 c「整段规则周期」判据逐字保留；r9/r12 对照说明原位"
    "保留）、§4 其余文本（总原则、两条显式判据、存在性判断一般判据引导"
    "句、三路出口显式化、confidence 定义与弃权 flag 输出细节、既有 r6/r8 "
    "对照说明原文原位）、courtyard 中性说明（§5）、输出 schema（单 JSON、"
    "per_image、flag 恰六键、无 side 字段，§6）、格式对齐提示（§7）、"
    "bottom 视口径（沿用 r4 指引：top/bottom 判读口径在图像空间完全一致、"
    "不做镜像换算；未为 bottom 单独定图层清单——该属渲染侧变更，不在本"
    "轮）、v1.2 工具行为规约沿用（纯 Read 直读，派发层，本轮无协议侧变"
    "更）。机械替换仅：视角前缀 R12T/R12B→R13T/R13B、round_id_constant→"
    "`2026-09-08-r13`（及示例中 reader-r12→reader-r13）。")

BULLET_ATTRIBUTION = (
    "- **归因计划：** 本轮检验「判读语义歧义」病根的指引侧处置（区别于 "
    "r10 采样侧、r11–r12 工具侧处置）；bottom 主通道（视角层 courtyard 类"
    "非弃权旗数收敛）=top 方向性附录；跨轮对比为方向性（reader 实例群与"
    "工具代际混杂照旧声明）；轮内多实例分布照旧如实分列。归因计划详见编"
    "排侧 r13-prep-record（指引内零数字）。本指引零 GT、零轮次结果数字。")

NEW_SECTION_BODY = (
    SEC_START + "\n\n" + BULLET_CHANGE + "\n\n" + BULLET_NO_LOOSENING +
    "\n\n" + BULLET_UNCHANGED + "\n\n" + BULLET_ATTRIBUTION + "\n\n")

#: 输出侧禁词断言（指引零 GT、零轮次结果数字、零诊断报告数字的清单法
#: 自动化；均为在案轮次结果分数/分数记法/盘上产物 id 前缀/诊断报告统计
#: 数字，r12 指引全文与本轮新增文本均不含）
FORBIDDEN_IN_GUIDANCE = (
    "GT-", "ground-truth", "ground_truth", "abstain_rate",
    "0.222222", "0.727273", "0.285714", "0.226415", "0.133333",
    "0.153846", "0.307692", "0.154", "0.076923", "0.421053",
    "0.529412", "0.090909", "0.071429", "0.431818", "0.875",
    "0.833333", "0.375", "0.95",
    "4/14", "8/11", "4/18", "2/15", "12/53", "1/13", "2/13", "3/20",
    "19/44", "9/10", "18/0/2", "18/0/0",
    "43.1", "232", "周期 10", "1–9px",
    "R8T-", "R9T-", "R10T-", "R11T-", "R11B-",
    "R12T-", "R12B-", "reader-r10", "reader-r11",
    "2026-09-07",
)


def _fail(msg: str) -> None:
    print(f"[r13-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _replace_counted(text: str, old: str, new: str, expected: int,
                     label: str) -> str:
    """计数受控替换：old 出现次数 != expected 即停。"""
    n = text.count(old)
    if n != expected:
        _fail(f"锚点计数不符：{label} 期望 {expected} 次，实测 {n} 次")
    return text.replace(old, new)


def build_guidance(r12_text: str) -> str:
    """由 r12 指引全文生成 r13 指引（纯函数；同入参必得同输出）。

    顺序纪律：先做替换与插入（其锚点均不含机械替换模式），再做机械替
    换，最后整体重写标题/声明日期/本轮性质行/变更声明节（新文本内含
    r12→r13 箭头记法与 R12T/R12B 记法，故机械替换必须先行，避免自命
    中）。
    """
    text = r12_text

    # ---- 前置计数断言（r12 输入侧锚点）----
    for pat, n in (
            ("2026-09-07-r12", 2),  # round_id 行 + 变更声明节内记法
            ("R12T-", 4),           # §6 表行 ×2 + 格式示例 flag_id ×2
            ("R12B-", 1),           # §6 表行
            ("reader-r12", 2),      # 格式示例 reader_id + 变更声明节内记法
            (OLD_TITLE, 1),
            (OLD_DATE_LINE, 1),
            (OLD_NATURE_LINE, 1),
            (OLD_S4_SEGMENT, 1),
            ("（对照说明（r12 增补）", 1),  # §3A 既有 r12 增补块
            ("（对照说明（r9 增补）", 1),   # §3A 既有 r9 增补块
            ("（对照说明（r8 增补）", 1),   # §4 既有 r8 增补块
            ("（对照说明（r13 增补）", 0),  # r13 增补块尚不存在
            ("\n\n## 5. courtyard 说明", 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1)):
        if text.count(pat) != n:
            _fail(f"r12 指引锚点计数不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")

    # ---- (1) §4 存在性判断一般判据 (i)(ii)→(i)(ii)(iii) 可操作化替换
    #      （引导句逐字保留）----
    text = _replace_counted(text, OLD_S4_SEGMENT, NEW_S4_SEGMENT, 1,
                            "§4 存在性判断一般判据段")

    # ---- (2) §4 末尾追加 r13 对照说明（r8 对照说明块之后、"## 5" 之前）----
    text = _replace_counted(
        text, "\n\n## 5. courtyard 说明",
        "\n\n" + CONTRAST_NOTE_R13 + "\n\n## 5. courtyard 说明", 1,
        "r13 对照说明插入点")

    # ---- (3) 机械替换（round_id / 视角前缀 / 示例 reader-id；变更声明节
    #      旧文本此时仍在场、随后整体重写，其内被替换的记法不影响结果）----
    text = _replace_counted(text, "2026-09-07-r12", "2026-09-08-r13", 2,
                            "round_id_constant")
    text = _replace_counted(text, "R12T-", "R13T-", 4, "flag 前缀 R12T-")
    text = _replace_counted(text, "R12B-", "R13B-", 1, "flag 前缀 R12B-")
    text = _replace_counted(text, "reader-r12", "reader-r13", 2, "reader-id")

    # ---- (4) 标题、声明日期行、本轮性质行 ----
    text = _replace_counted(text, OLD_TITLE, NEW_TITLE, 1, "标题")
    text = _replace_counted(text, OLD_DATE_LINE, NEW_DATE_LINE, 1,
                            "声明日期行")
    text = _replace_counted(text, OLD_NATURE_LINE, NEW_NATURE_LINE, 1,
                            "本轮性质行")

    # ---- (5) 变更声明节整体重写（r12 同款结构，r13 内容四 bullet）----
    start = text.index(SEC_START)
    end = text.index(SEC_END_ANCHOR)
    if not start < end:
        _fail("变更声明节锚点顺序异常")
    text = text[:start] + NEW_SECTION_BODY + text[end + 1:]

    # ---- 输出侧禁词断言（零 GT、零轮次结果数字、零诊断报告数字）----
    for pat in FORBIDDEN_IN_GUIDANCE:
        if pat in text:
            _fail(f"r13 指引含禁词（零 GT/零轮次结果数字/零诊断报告数字"
                  f"自检失败）：{pat}")

    # ---- 后置计数断言（r13 输出侧）----
    for pat, n in (
            ("R12T-", 0),
            ("R12B-", 0),
            ("2026-09-07-r12", 0),
            ("2026-09-07", 0),
            ("2026-09-08-r13", 2),
            ("R13T-", 4),
            ("R13B-", 1),
            ("reader-r13-top", 1),
            ("reader-r12", 1),      # 仅存于新节「reader-r12→reader-r13」记法
            (OLD_S4_SEGMENT, 0),
            (NEW_S4_SEGMENT, 1),
            (CONTRAST_NOTE_R13, 1),
            ("（对照说明（r12 增补）", 1),
            ("（对照说明（r9 增补）", 1),
            ("（对照说明（r8 增补）", 1),
            ("（对照说明（r13 增补）", 1),
            (NEW_TITLE, 1),
            (NEW_DATE_LINE, 1),
            (NEW_NATURE_LINE, 1),
            (SEC_START, 1),
            (SEC_END_ANCHOR, 1)):
        if text.count(pat) != n:
            _fail(f"r13 指引后置断言不符：{pat[:24]}… 期望 {n}，"
                  f"实测 {text.count(pat)}")
    return text


# ---------------------------------------------------------------------------
# fail-closed 验证（镜像 s46 模式；零写入）
# ---------------------------------------------------------------------------

def _load_png_witness_constants(r12_record: dict) -> dict:
    """探测 r12-prep-record renders_reuse.png_witness 结构，取见证常量。

    结构要求（不符即停）：list、恰 4 项、每项含 state_side / path_rel /
    sha256_witness_constant / sha256_measured / match_to_witness_constant；
    登记自洽要求：sha256_measured == sha256_witness_constant 且
    match_to_witness_constant 为真、path_rel 指向 renders-r5/<side>.png。
    """
    witness = r12_record.get("renders_reuse", {}).get("png_witness")
    if not isinstance(witness, list) or len(witness) != 4:
        _fail("r12-prep-record renders_reuse.png_witness 结构不符（非 4 项列表）")
    by_side = {}
    for item in witness:
        for key in ("state_side", "path_rel", "sha256_witness_constant",
                    "sha256_measured", "match_to_witness_constant"):
            if key not in item:
                _fail(f"png_witness 项缺键 {key}（结构探测失败）")
        by_side[item["state_side"]] = item
    if sorted(by_side) != sorted(RENDERS_R5_SIDES):
        _fail(f"png_witness state_side 集不符：{sorted(by_side)}")
    constants = {}
    for side in RENDERS_R5_SIDES:
        item = by_side[side]
        expected_rel = f"out/v3-tl2/calibration/renders-r5/{side}.png"
        if item["path_rel"] != expected_rel:
            _fail(f"{side} png_witness path_rel 不符：{item['path_rel']}")
        if item["sha256_measured"] != item["sha256_witness_constant"]:
            _fail(f"{side} png_witness 登记不自洽（measured != witness_constant）")
        if item["match_to_witness_constant"] is not True:
            _fail(f"{side} png_witness 登记自洽位不为真")
        constants[side] = item["sha256_witness_constant"]
    return constants


def _check_frozen_input_pdfs(framing: dict) -> list:
    """R5 渲染输入链复核：frozen_inputs.r4_frozen_pdfs 登记值 vs 盘上实测。"""
    registered = {item["state_side"]: item
                  for item in framing["frozen_inputs"]["r4_frozen_pdfs"]}
    results = []
    for state_side, rel in FROZEN_PDF_RELS.items():
        item = registered.get(state_side)
        if item is None:
            _fail(f"render-framing-r5.json 缺 {state_side} 的冻结 PDF 登记")
        if item["path_rel"] != rel:
            _fail(f"{state_side} 冻结 PDF 路径不符：{item['path_rel']} != {rel}")
        measured = _sha(REPO / rel)
        results.append({
            "state_side": state_side,
            "path_rel": rel,
            "sha256_registered": item["sha256"],
            "sha256_measured": measured,
            "match": measured == item["sha256"],
        })
    bad = [r for r in results if not r["match"]]
    if bad:
        _fail(f"R5 冻结输入 PDF 复核不符（渲染输入链疑被改动）：{bad}")
    return results


def _check_framing_raster_field(framing: dict) -> None:
    """复核 frozen_inputs 无 renders-r5 输出 PNG 哈希登记字段（与在案记录
    raster_output_hash_field_probe 结论一致；不符即停=framing 结构漂移）。"""
    fi_keys = list(framing.get("frozen_inputs", {}).keys())
    if any("r5" in k.lower() for k in fi_keys):
        _fail(f"render-framing-r5 frozen_inputs 出现 r5 前缀键（与在案探测结"
              f"论不符，framing 结构漂移）：{fi_keys}")
    if "r4_frozen_png_sha256_reference" not in fi_keys:
        _fail("render-framing-r5 frozen_inputs 缺 r4_frozen_png_sha256_"
              "reference（与在案探测结论不符，framing 结构漂移）")


def _check_renders_r5_pngs(constants: dict) -> list:
    """renders-r5 四件 PNG：magic 检查 + 实测 sha256 vs 登记见证常量。"""
    results = []
    for state_side in RENDERS_R5_SIDES:
        expected = constants[state_side]
        path = CAL_DIR / "renders-r5" / f"{state_side}.png"
        if not path.exists():
            _fail(f"renders-r5 PNG 缺失：{path}")
        with path.open("rb") as f:
            magic = f.read(8)
        if magic != PNG_MAGIC:
            _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        results.append({
            "state_side": state_side,
            "path_rel": f"out/v3-tl2/calibration/renders-r5/{state_side}.png",
            "sha256_measured": measured,
            "sha256_witness_constant": expected,
            "match_to_witness_constant": measured == expected,
        })
    bad = [r for r in results if not r["match_to_witness_constant"]]
    if bad:
        _fail(f"renders-r5 PNG 实测与登记见证常量不符（R5 冻结渲染疑被改动）：{bad}")
    return results


def _check_diag_reports() -> list:
    """diag-r13-review 三报告：实测 sha256 vs 冻结锚（先实测哈希后引；
    哈希接触、零内容解析）。"""
    results = []
    for reviewer in ("D1", "D2", "D3"):
        name, anchor = DIAG_REPORT_ANCHORS[reviewer]
        path = DIAG_DIR / name
        if not path.exists():
            _fail(f"诊断报告缺失：{path}")
        measured = _sha(path)
        if not measured.startswith(anchor):
            _fail(f"诊断报告 {name} sha 前 8={measured[:8]} != 预期 {anchor}"
                  f"（诊断证据疑被改动，立即停止）")
        results.append({
            "reviewer": reviewer,
            "path_rel": f"out/v3-tl2/calibration/diag-r13-review/{name}",
            "sha256_measured": measured,
            "sha256_prefix_expected": anchor,
            "match": True,
        })
    return results


def _extract_preregistration(dev_record: dict) -> dict:
    """从 round12-dev-record 取预注册原文与在案引用。

    next_iteration_targets 按内容标记唯一定位 §4(i) 可操作性修订候选
    （实际索引实测回填并要求=[0]，定位不到或歧义即停）；另取
    run_record_ref 的 path_rel/sha256 作基线在案引用。
    """
    targets = dev_record.get("next_iteration_targets")
    if not isinstance(targets, list) or len(targets) < 1:
        _fail("round12-dev-record next_iteration_targets 结构不符")
    g_idx = [i for i, t in enumerate(targets)
             if isinstance(t, str) and MARK_CANDIDATE_S4 in t]
    if len(g_idx) != 1:
        _fail(f"next_iteration_targets 标记定位歧义：s4={g_idx}")
    if g_idx[0] != 0:
        _fail(f"§4(i) 可操作性修订候选实测索引={g_idx[0]} != 预注册给定 [0]")
    guidance_text = targets[g_idx[0]]
    if MARK_CANDIDATE_S4_PLAN not in guidance_text:
        _fail("§4(i) 可操作性修订候选项缺「单变量纪律」标记")

    run_ref = dev_record.get("run_record_ref", {})
    if not isinstance(run_ref, dict) or "path_rel" not in run_ref \
            or "sha256" not in run_ref:
        _fail("round12-dev-record run_record_ref 缺 path_rel/sha256"
              "（在案引用结构漂移）")

    return {
        "index_zero_based": g_idx[0],
        "candidate_target": guidance_text,
        "r12_run_record_ref": {"path_rel": run_ref["path_rel"],
                               "sha256": run_ref["sha256"]},
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, framing_sha: str, r12_record_sha: str, dev_record_sha: str,
                 protocol_v1_sha: str, guidance_r12_sha: str,
                 guidance_r13_sha: str, pdf_results: list, png_results: list,
                 diag_results: list, quotes: dict,
                 measurement_items: list) -> dict:
    """构建 r13-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r13_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r13",
        "round_nature": (
            "单变量指引侧变更轮（§4 存在性判断一般判据可操作化）：判读指"
            "引由 r12 指引（observation-guidance-r12.md，0ac22fcd）机械变"
            "换生成 observation-guidance-r13.md（指引侧唯一实质变更=§4 "
            "(i)(ii)→(i)(ii)(iii) 可操作化替换+§4 末尾 r13 对照说明；执行 "
            "round12-dev-record next_iteration_targets[0]，用户 2026-09-08 "
            "已拍板排程本轮并授权额外评审，见 pre_round_review），渲染零字"
            "节复用 R5 冻结件（零仪器变更、零重渲染）；协议 v1.2 沿用无新"
            "增版本（派发层纯 Read 直读规约原文适用；v1.1 的 n=3 多实例与"
            "聚合口径全部沿用，见 protocol_amendment）；指引先于本轮盲读"
            "落盘、落盘即冻结；盲读由编排侧在本记录之后以 12 次独立实例盲"
            "读执行"),
        "pre_round_review": {
            "declaration": (
                "额外评审记录（本轮新增键；r12-prep-record 顶层键镜像+本键"
                "=文档化差异）：用户 2026-09-08 拍板「R13 方向需额外评审+"
                "视觉 MCP 放开用量」后，编排侧在指引落盘前执行的诊断性评"
                "审；属编排侧诊断证据（用户授权的额外评审），不属盲读链—"
                "—R13 reader 仍按盲读纪律执行（上下文=指引+PNG+命名指令，"
                "零诊断报告内容）"),
            "execution": (
                "3 名独立诊断审查员（D1/D2/D3，非校准 reader、零 flag 零 "
                "GT 接触）对 renders-r5 两张 bottom PNG（applied-bottom/"
                "prep1-bottom，盘上字节一致）做像素级盘点、层归属分析、候"
                "选措辞 W1/W2/W3 应用实测"),
            "reports": diag_results,
            "reports_note": (
                "三报告先实测 sha256 后引用（本脚本哈希接触、零内容解析；"
                "冻结锚不符即停）；报告内容不进指引、不进任何 reader 上下"
                "文"),
            "key_facts": {
                "bottom_renders_pixel_identical": (
                    "两 bottom 渲染逐像素相同（三审查员独立证实；与 "
                    "renders_reuse.png_witness 登记的 applied-bottom="
                    "prep1-bottom 字节一致相符）"),
                "butterfly_morphology": (
                    "蝶形形态=逐盘自带图元（孤立焊盘带完整花瓣、无邻居有半"
                    "翼），严格周期 10、四边平移副本恒等、形态单族"),
                "adjacency_statistics": (
                    "相邻对 232 中翼材料入中点区 100（43.1%）、其中真融合 "
                    "20、近触（1–9px 亚感知缝）80"),
                "wording_candidates": (
                    "W1（计数≥3+沿阵列对齐）为唯一能把 r12 三裁决（18 非弃"
                    "权/0 旗/2 弃权）收敛一致的候选，W2/W3 过半率判据对周"
                    "期性单元级特征系统性误判——本轮 §4 量化判据采 W1 方向"
                    "（另含最小重复单元计数与接触性判据）"),
                "layer_attribution": (
                    "全部白色同一渲染图层族（>95%），具体 EDA 层名不可判"
                    "（单色压平）=渲染侧消歧候选延续"),
            },
            "facts_note": (
                "以上为诊断报告事实的如实摘要，仅入本记录、不进指引（指引"
                "零轮次结果数字、零板面断言）；统计数字属诊断证据、非本轮"
                "判读结果"),
        },
        "user_directive_note": (
            "用户 2026-09-08 拍板两项（本记录=首次落盘登记，见 "
            "pre_round_review 与 hypothesis_test.preregistered_criteria_"
            "quote.user_directive_2026_09_08）：(1) R13 方向（§4 存在性判"
            "据可操作化）需额外评审——已执行=诊断三报告；(2) 视觉 MCP 放"
            "开用量（诊断评审阶段授权；不改变 reader 盲读纪律——reader 仍"
            "纯 Read 直读原图）"),
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "amendment_version": "v1.2（沿用，无新增版本）",
            "amendment_mode": (
                "无新增修订：v1.2 原文适用（纯 Read 直读规约自 r12 起随派"
                "发指令生效，本轮照旧）；v1.1 的 n=3 多实例与聚合口径全部"
                "沿用；本轮单变量=指引侧恰一项，协议侧零变更"),
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视角"
                "层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径并"
                "列、联合门代表配置+实例间范围并列（measurement_design 五"
                "条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派发"
                "指令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/放"
                "大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查看"
                "原图（同一原图可重复查看）」——仪器行为钉住；属派发层，读"
                "者上下文=指引+单张 PNG+派发指令（含规约条款），零 GT；不"
                "影响判读语义——分类判据零变更，仅输入手段固定"),
            "motivation_note": (
                "沿用声明（无新增动机条目）：v1.2 于 r12 轮以追加式落定"
                "（r10/r11 实测 8/12 派次自选 PIL 局部裁剪放大的工具异质性"
                "已由规约钉住，r12 实测 12/12 派次自述合规在案）；本轮无新"
                "增协议条款"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": "22dc7337",
                "sha256_measured": protocol_v1_sha,
                "zero_byte_preserved": True,
                "note": (
                    "v1 原文零字节保留（r11/r12 轮同口径在案登记，实测交叉"
                    "核对 r12-prep-record 登记值相符，本轮继续沿用）；本轮"
                    "无新增版本、不新建协议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实例"
                "（i1/i2/i3）；实例上下文=指引（observation-guidance-r13.md）"
                "+单张 PNG+派发命名指令（含 v1.2 工具行为规约硬性条款），零 "
                "GT、零诊断报告内容（pre_round_review 报告不进任何 reader 上"
                "下文）；两波次串行保序（同一实例先 applied 后 prep1，"
                "flag_id 编号跨板连续）"),
            "naming": (
                "reader_id=reader-r13-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R13T/R13B（本轮指引生成时已由 §6 的 R12T/R12B 机械替换写入 "
                "R13T/R13B 与 reader-r13 示例——机械覆盖随指引落盘固化；实"
                "例后缀 i{1,2,3} 仍由派发指令机械补全）；实例间编号独立，同"
                "实例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.2 沿用声明，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "renders_reuse": {
            "declaration": (
                "复用 R5 冻结渲染：renders-r5/ 四件 PNG 原样，零仪器变更、"
                "零重渲染；渲染输入侧冻结 PDF 另行复核（见下）"),
            "framing_reference": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r5.json",
                "sha256": framing_sha,
            },
            "png_witness_source": {
                "path_rel": "out/v3-tl2/calibration/r12-prep-record.json",
                "sha256": r12_record_sha,
                "note": (
                    "renders-r5 四件 PNG 见证常量照抄 r12-prep-record.json "
                    "renders_reuse.png_witness 登记（来源链：r12-prep-record "
                    "取自 r11-prep-record，r11-prep-record 取自 r10-prep-"
                    "record，r10-prep-record 取自 r9-prep-record，r9-prep-"
                    "record 取自 r8-prep-record，r8-prep-record 取自 r7-"
                    "prep-record，源头=2026-09-06 s35/s33 首跑实测；本脚本"
                    "探测该结构取常量并要求登记自洽，另对来源文件以 "
                    "d393cf27 锚 fail-closed 复核），非本脚本新测——R13 零"
                    "仪器变更、零重渲染，不产生新见证"),
            },
            "raster_output_hash_field_probe": {
                "field_found": False,
                "finding": (
                    "render-framing-r5.json 中不存在 renders-r5 输出 PNG "
                    "的哈希登记字段；frozen_inputs.r4_frozen_png_sha256_"
                    "reference 登记的是 R4 轮冻结 PNG 参考值（与 renders-r5 "
                    "实测不符，属预期：R5 仪器 dpi/crop 变更后 PNG 字节本不"
                    "相同）；本脚本已复核该结构结论仍成立（不符即停）"),
                "resolution": (
                    "故 renders-r5 PNG 见证常量以 r12-prep-record.json 登记"
                    "值为准（见 png_witness_source），本脚本 fail-closed 实"
                    "测比对（防改动见证）"),
            },
            "frozen_input_pdfs_check": {
                "scope": ("render-framing-r5.json frozen_inputs."
                          "r4_frozen_pdfs（R5 渲染输入链）"),
                "count": len(pdf_results),
                "all_match": True,
                "results": pdf_results,
            },
            "png_witness": png_results,
            "png_witness_note": (
                "applied-bottom 与 prep1-bottom 盘上字节一致（sha256 相同）"
                "为 R5 渲染实测事实（沿用 r12-prep-record 登记，本脚本实测仍"
                "符），照实登记，不含任何 GT 含义；pre_round_review 三份诊"
                "断报告独立证实两 bottom 渲染逐像素相同，与本哈希登记相符"),
            "no_instrument_change": True,
        },
        "guidance": {
            "path_rel": "out/v3-tl2/calibration/observation-guidance-r13.md",
            "sha256": guidance_r13_sha,
            "frozen_on_write": True,
            "baseline": {
                "path_rel":
                    "out/v3-tl2/calibration/observation-guidance-r12.md",
                "sha256_prefix_expected": GUIDANCE_R12_SHA_PREFIX,
                "sha256_measured": guidance_r12_sha,
                "match": guidance_r12_sha.startswith(GUIDANCE_R12_SHA_PREFIX),
                "role": (
                    "指引作者唯一事实源（r12 轮落盘产物；另加包指令，GT 已"
                    "剥离）"),
            },
            "change_summary": (
                "相对 r12 指引恰三组差异：§4 存在性判断一般判据 (i)(ii) 段"
                "整段替换为量化版 (i)(ii)(iii)（r8 增补段从「(i) 同一形态」"
                "起至「（此时仍按「弃权适用于」条处理）。」止替换，引导句"
                "「判断「弃权适用于」条所述**疑似形态是否为真实的关注现"
                "象**时，除该条既有判断标准（原样适用、责任标准一字不松）"
                "外，另按以下中性一般启发推理：」逐字保留）；§4 末尾（r8 "
                "对照说明块之后、§5 之前）增补一条 r13 对照说明；头部（标"
                "题、round_id_constant、声明日期、本轮性质行、本轮变更声明"
                "节按 r12 同款结构重写为本轮四 bullet：变更/非放宽/不变/归"
                "因计划）与 §6 视角前缀/示例 reader-id 的机械替换"
                "（2026-09-07-r12→2026-09-08-r13、R12T-→R13T-、R12B-→R13B-、"
                "reader-r12→reader-r13，标题轮次标识 R12→R13、声明日期 "
                "2026-09-07→2026-09-08 一并）。其余文本逐字承 r12 指引。"),
        },
        "changed_variables": [
            {
                "id": "s4-existence-criteria-operationalize-i-ii-iii",
                "target": ("observation-guidance-r13.md §4 存在性判断一般"
                           "判据（指引侧恰一项；单变量轮）"),
                "description": (
                    "§4 存在性判断一般判据 (i)(ii) 整段替换为量化版 "
                    "(i)(ii)(iii)（措辞一字不改地使用包指令给定文本；引导"
                    "句逐字保留）：「规则地、成体系地重复」细化为可数判据"
                    "（≥3 处+沿同一阵列/成组对齐+≥2 条不同阵列/边+形态逐处"
                    "一致），计数单元显式定为最小重复单元（相邻单元间的联"
                    "合交叠外观不得替代单元级计数、成对出现率不构成否定系"
                    "统性的依据），并新增接触性判据（真实接触 vs 视觉贴近，"
                    "不可区分→按存在性弃权）；另在 §4 末尾（r8 对照说明块"
                    "之后、§5 之前）增补 r13 对照说明一行（措辞一字不改地"
                    "使用包指令给定文本）。"),
                "old_text": OLD_S4_SEGMENT,
                "new_text": NEW_S4_SEGMENT,
                "contrast_note_added": CONTRAST_NOTE_R13,
                "attribution_channel": (
                    "bottom courtyard 收敛主通道（视角层 courtyard 类非弃权"
                    "旗数极差：基线 r12=18；支持=极差 ≤5 且 bottom 聚合非弃"
                    "权 courtyard 旗总数 ≤5；拒绝=极差 >5 或聚合 ≥10）；守"
                    "门=top 视角非弃权旗标仍守 §3 收窄判据（几何门面积比出"
                    "局条目无回升）"),
            },
        ],
        "manipulated_factor": (
            "恰一项变更变量（指引侧单变量=§4 存在性判断一般判据可操作化替"
            "换，见 changed_variables[0]）；渲染/GT/阈值/协议零变更（v1.2 "
            "沿用无新增版本）"),
        "unchanged_components": [
            "渲染：R5 冻结渲染件逐字节复用（零仪器变更、零重渲染；四件 PNG "
            "实测=在案见证常量）",
            "角色与盲读纪律（r13 指引 §1，逐字承 r12 指引）",
            "类别枚举：6 类逐字（critic.FLAG_CATEGORIES 顺序与圆括号中性释"
            "义零改动；r13 指引 §2）",
            "§3 邻域框收窄判据与坐标口径（r13 指引 §3，逐字承 r12 指引）",
            "§3A 类别判据示例：全部逐字承 r12 指引（六类全部示例含示例 c"
            "「整段规则周期」判据；§3A 末尾 r9/r12 对照说明原位保留）",
            "§4 其余文本：总原则「宁可 abstain 不硬标」、「弃权适用于」「弃"
            "权不适用于」两条显式判据、存在性判断一般判据引导句、三路出口"
            "显式化、confidence 定义与弃权 flag 输出细节、既有对照说明"
            "（r6/r8 增补块）原文原位（仅存在性判断一般判据 (i)(ii) 段整段"
            "替换+末尾另增 r13 对照说明）",
            "courtyard 中性说明（r13 指引 §5，逐字承 r12 指引）",
            "输出 schema：单 JSON、顶层三键、per_image、flag 恰六键、无 "
            "side 字段（r13 指引 §6，仅视角前缀/示例 reader-id 机械替换）",
            "格式对齐提示（r13 指引 §7；fail-closed 校验口径，逐字承 r12 "
            "指引）",
            "bottom 视口径：沿用 r4 指引不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算；为 bottom 单独定图层清单属渲染侧变"
            "更，不在本轮）",
            "GT 集：零改动（gt-audit-r1 三候选全部关闭在案；GT 侧不再有候"
            "选，r9–r12 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改动（只作"
            "口径引用）",
            "评估协议：v1.2 沿用无新增版本（evaluation-protocol-v1.md 零字"
            "节保留；本轮不新建协议文件，见 protocol_amendment）",
            "机械替换仅：视角前缀 R12T/R12B→R13T/R13B；round_id_constant "
            "2026-09-07-r12→2026-09-08-r13（及示例中 reader-r12→reader-r13）；"
            "标题轮次标识 R12→R13；声明日期 2026-09-07→2026-09-08",
        ],
        "bottom_view_note": (
            "bottom 视沿用 r4 指引口径不改（top/bottom 判读口径在图像空间"
            "完全一致、不做镜像换算）；bottom 零旗标分母=0 时弃权率按 "
            "cal._ratio 先例=None 口径照旧（r10–r12 在案）；渲染侧 bottom "
            "图层清单+蝶形粘连层归属消歧属渲染侧变更，仍为后续轮候选"
            "（round12-dev-record next_iteration_targets[1] 在案；pre_"
            "round_review 层归属事实：具体 EDA 层名在单色压平渲染下不可判），"
            "不在本轮"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R13 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注册，"
                "聚合口径全部如实并列、不二选一、不挑优（五条 items 照抄 "
                "r12-prep-record measurement_design.items 原文，仅本声明行"
                "轮次编号更新）"),
            "items": measurement_items,
        },
        "hypothesis_test": {
            "hypothesis_id": "r12-dev-record-candidate-0-s4i-operationalize",
            "hypothesis": (
                "§4 存在性判据可操作化后，bottom 视同批形态的跨实例裁决收"
                "敛——量化判据使该类形态被一致地判入「系统性正常特征→不报"
                "告」路径，单实例大规模非弃权报告消失。"),
            "test_design": (
                "单变量指引侧变更轮：指引由 r12 指引（observation-"
                "guidance-r12.md，0ac22fcd）机械变换生成 observation-"
                "guidance-r13.md（§4 (i)(ii)→(i)(ii)(iii) 可操作化替换+§4 "
                "末尾 r13 对照说明+头部机械替换），渲染 R5 冻结件复用、GT/"
                "阈值零变更；协议 v1.2 沿用无新增版本（派发层纯 Read 直读"
                "规约原文适用，v1.1 多实例与聚合口径沿用）；12 次盲读=4 视"
                "角格×3 实例；诊断评审（pre_round_review）为编排侧证据、不"
                "进任何 reader 上下文。"),
            "baseline_reference": {
                "note": (
                    "r12 实测基线（编排侧记录；引用已落盘 run-record 在案"
                    "值；数字仅入 prep-record，不进指引文件——指引零轮次结"
                    "果数字）。bottom 三实例对同批白色蝶形粘连形态三种裁决="
                    "round12-dev-record 机制观察在案（§4(i) 判据轴不稳定）："
                    "bottom-i1=18 条非弃权 courtyard「孤立、打破规律」/"
                    "bottom-i2=0 旗「系统性重复→正常」/bottom-i3=2 弃权旗"
                    "「疑似合并异常无法确认」；bottom courtyard 类非弃权旗"
                    "数 18/0/0、极差=18。"),
                "r12_bottom_three_verdicts": {
                    "bottom-i1": {
                        "non_abstain_courtyard_count": 18,
                        "verdict": "孤立、打破规律→关注现象（18 条非弃权 courtyard）",
                    },
                    "bottom-i2": {
                        "non_abstain_courtyard_count": 0,
                        "verdict": "系统性重复→正常设计特征（0 旗）",
                    },
                    "bottom-i3": {
                        "non_abstain_courtyard_count": 0,
                        "verdict": "疑似合并异常无法确认（2 弃权旗）",
                    },
                },
                "bottom_courtyard_non_abstain_by_instance": {
                    "bottom-i1": 18, "bottom-i2": 0, "bottom-i3": 0,
                },
                "range": 18,
                "sources": {
                    "r12_run_record": quotes["r12_run_record_ref"],
                    "r12_dev_record": {
                        "path_rel":
                            "out/v3-tl2/calibration/round12-dev-record.json",
                        "sha256": dev_record_sha,
                    },
                },
            },
            "support_condition": (
                "bottom 视角层 courtyard 类非弃权旗数极差 ≤5 且 bottom 聚合"
                "非弃权 courtyard 旗总数 ≤5，且 top 视角非弃权旗标仍守 §3 收"
                "窄判据（几何门面积比出局条目无回升），则可操作化生效获支"
                "持。"),
            "reject_condition": (
                "bottom courtyard 非弃权旗数极差 >5 或 bottom 聚合非弃权 "
                "courtyard ≥10，则分歧未收敛（操作化无效），如实记录。"),
            "null_result_note": (
                "结果无论方向如实；以 bottom 收敛为准、top 方向性附录；「正"
                "确测出无效同样是有效证据」；5/10 为本轮预注册描述性边界，"
                "非 APR-0011 门（门照常独立计算，互不凌驾）；跨轮实例群混"
                "杂照旧声明。"),
            "declaration": (
                "bottom 视角层 courtyard 类非弃权旗数极差（本轮假设主通道）"
                "按逐实例如实计数（bottom-i1/i2/i3 三分列）；bottom 聚合非"
                "弃权 courtyard 旗总数并列如实；top 视角全类照常如实记录"
                "（几何门守门独立复核）；跨实例=同轮同指引（v1.2 规约沿"
                "用），跨轮对比=方向性；「正确测出无效同样是有效证据」。"),
            "preregistered_criteria_quote": {
                "candidate_0_target": quotes["candidate_target"],
                "user_directive_2026_09_08": (
                    "用户拍板（2026-09-08，编排侧在案；本记录=首次落盘登"
                    "记）：(1) R13 方向需额外评审（执行=3 名独立诊断审查员 "
                    "D1/D2/D3，报告 out/v3-tl2/calibration/diag-r13-review/，"
                    "见 pre_round_review）；(2) 视觉 MCP 放开用量（诊断评审"
                    "阶段授权；不改变 reader 盲读纪律——reader 仍纯 Read 直"
                    "读原图）"),
            },
            "preregistration_ref": {
                "path_rel": "out/v3-tl2/calibration/round12-dev-record.json",
                "sha256": dev_record_sha,
                "sha256_prefix_expected": R12_DEV_RECORD_SHA_PREFIX,
                "field": "next_iteration_targets",
                "item_indices_zero_based": [quotes["index_zero_based"]],
                "note": (
                    "引用原文逐字摘录（措辞按文件原文，未改写）：索引 [0]="
                    "§4(i) 判据的可操作性修订候选（指引侧候选，本轮执行的指"
                    "引侧变更，用户 2026-09-08 拍板排程 R13——拍板原文以本记"
                    "录 user_directive_2026_09_08 首次落盘登记）。先于 R13 "
                    "盲读落盘预注册（本记录=预注册件）。"),
            },
            "primary_channel_metric": (
                "bottom 视角层 courtyard 类非弃权旗数极差（基线 r12=18）；"
                "bottom 聚合非弃权 courtyard 旗总数并列（拒绝通道要件）；执"
                "行由编排侧在 close 包执行。"),
            "metric_lesson_application": (
                "r9–r12 教训链延续（产量计数+构成分析互补、逐实例如实分列"
                "不聚合掩盖）；round12-dev-record metric_design_lesson 登记"
                "的「§4(i) 判据可操作性修订候选」本轮执行；本轮=对「判读语"
                "义歧义」病根的指引侧处置首验（区别于 r10 采样侧、r11–r12 "
                "工具侧）；全部预注册于本记录、先于盲读冻结，不追溯改判既"
                "往轮次（r8–r12 字母裁决维持不变）。"),
            "secondary_observation": (
                "接触性判据 (iii) 首验（弃权旗中「接触 vs 贴近不可区分」类"
                "理由如实登记，逐旗引用原文证据）；top 全类分布方向性记录；"
                "courtyard 密集旗被动追踪延续（零阈值改动零期望）；bottom "
                "零旗标=None 口径照旧（pcbflow/calibration.py _ratio 先"
                "例）。"),
        },
        "attribution_plan": {
            "declaration": (
                "本轮变更变量恰一项（指引侧单变量=§4 存在性判断一般判据可"
                "操作化替换）、检验恰一个假设（round12-dev-record "
                "next_iteration_targets[0]；hypothesis_id=r12-dev-record-"
                "candidate-0-s4i-operationalize）；归因分层：本轮检验「判"
                "读语义歧义」病根的指引侧处置（区别于 r10 采样侧、r11–r12 "
                "工具侧处置）；跨轮对比（vs r10–r12）为方向性（实例群+工具"
                "代际混杂照旧声明）；bottom 主通道=top 方向性附录"),
            "primary_channel": {
                "change": (
                    "s4-existence-criteria-operationalize-i-ii-iii（指引侧"
                    "单变量）"),
                "metric": (
                    "bottom 视角层 courtyard 类非弃权旗数极差（bottom 三实"
                    "例 i1/i2/i3 逐实例 courtyard 类非弃权旗数 max−min；基"
                    "线 r12=18）；bottom 聚合非弃权 courtyard 旗总数并列"
                    "（拒绝通道要件）"),
                "support": (
                    "极差 ≤5 且 bottom 聚合非弃权 courtyard 旗总数 ≤5 → 可"
                    "操作化生效获支持"),
                "reject": (
                    "极差 >5 或 bottom 聚合非弃权 courtyard ≥10 → 分歧未收"
                    "敛（操作化无效），如实记录"),
            },
            "guard_channel": {
                "metric": (
                    "top 视角非弃权旗标 frame_box_pct 几何门（面积比出局条"
                    "目）"),
                "requirement": (
                    "§3 收窄判据零变更（逐字承 r12 指引），非弃权框仍须满"
                    "足；几何门面积比出局条目无回升"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角层三"
                "分列聚合+GT 匹配双口径+联合门代表配置/范围并列；APR-0011 阈"
                "值零改动）；bottom 主通道=top 方向性附录（bottom GT 无源在"
                "案，bottom 旗标与 GT 匹配应为空——结构性，不影响收敛计数口"
                "径）；归因分组逻辑由编排侧在 close 包执行；本指引零 GT、零"
                "轮次结果数字、零诊断报告数字（基线数字仅入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "本轮指引侧变更为可操作化方向（定性裁量细化为可数判据）：§4 "
            "(i)(ii) 由「规则地、成体系地重复/孤立不一致」的定性启发细化为 "
            "(i)(ii)(iii) 量化判据——量化阈值（≥3 处、≥2 条阵列/边）为一般"
            "判据、非期望清单，只收窄裁量空间、不改变责任标准：判断责任标"
            "准一字未松；反放宽条款「仅因形态不熟悉、不确定其设计含义，不"
            "构成判为正常设计特征的理由」原文保留；判「正常设计特征」与判"
            "「关注现象」同等判断责任原文保留；接触性判据为存在性弃权方向"
            "的澄清（不可区分→弃权），不降低报告义务；§3/§3A/§5/§6/§7 与 "
            "§4 其余文本一字不动，不降低任何存在性、归类、定位或报告的责"
            "任门槛；APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动；度量设计五条聚合口径沿用、不构成任何门的放宽或收紧——门"
            "照常独立计算"),
        "no_instrument_change": True,
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic）、ground-truth-*、reader-raw-*、calibration-run-*、"
            "derivation-log-*、任何 compare/评估产物；指引作者唯一输入="
            "observation-guidance-r12.md（0ac22fcd 锚 fail-closed，本脚本"
            "只读零写入）+包指令；r12-prep-record.json 仅用于取 renders-r5 "
            "PNG 见证常量与链交叉核对（hash 锚=d393cf27 先验证）；"
            "round12-dev-record.json 仅读取 round_id、next_iteration_targets"
            "（标记定位 [0]）与 run_record_ref 字段取预注册原文摘录与在案引"
            "用（hash 锚=1411dab6 先验证）；diag-r13-review 三报告仅实测 "
            "sha256（哈希接触、零内容解析；其内容事实由编排侧诊断包给定、"
            "仅入本记录 pre_round_review 键，不进指引、不进 reader 上下"
            "文）；render-framing-r5.json 仅输入链复核；observation-"
            "guidance-r13.md 落盘即冻结；reader 派发（后续编排侧执行）上下"
            "文=observation-guidance-r13.md+单张 PNG+派发指令（R13T/R13B "
            "前缀、reader-r13-{top,bottom}-i{1,2,3}、v1.2 工具行为规约硬性"
            "条款），零 GT、零诊断报告内容、零其他盘上文件；跨实例/跨视角禁"
            "止交流（12 次盲读相互独立、不得交换判读信息——独立性是多实例"
            "协议的前提）。"),
        "no_visual_reading": True,
    }


def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (FRAMING_R5, R12_PREP_RECORD, R12_DEV_RECORD, GUIDANCE_R12,
                 PROTOCOL_V1, DIAG_DIR):
        if not path.exists():
            _fail(f"缺失：{path}")

    # ---- 冻结锚与见证验证（fail-closed）----
    import json

    r12_record = json.loads(R12_PREP_RECORD.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    dev_record = json.loads(R12_DEV_RECORD.read_text(encoding="utf-8"))
    r12_record_sha = _sha(R12_PREP_RECORD)
    framing_sha = _sha(FRAMING_R5)
    dev_record_sha = _sha(R12_DEV_RECORD)
    protocol_v1_sha = _sha(PROTOCOL_V1)
    if not r12_record_sha.startswith(R12_PREP_RECORD_SHA_PREFIX):
        _fail(f"r12-prep-record sha 前 8={r12_record_sha[:8]} != 预期 "
              f"{R12_PREP_RECORD_SHA_PREFIX}（见证来源锚不符，立即停止）")
    if not dev_record_sha.startswith(R12_DEV_RECORD_SHA_PREFIX):
        _fail(f"round12-dev-record sha 前 8={dev_record_sha[:8]} != 预期 "
              f"{R12_DEV_RECORD_SHA_PREFIX}（冻结锚不符，立即停止）")
    if r12_record.get("schema_version") != "3.0":
        _fail("r12-prep-record schema_version != 3.0（结构漂移）")
    if r12_record.get("kind") != "tl2_calibration_r12_prep_record":
        _fail("r12-prep-record kind 不符（结构漂移）")
    if r12_record.get("round_id_constant") != "2026-09-07-r12":
        _fail("r12-prep-record round_id_constant != 2026-09-07-r12（结构漂移）")
    if dev_record.get("round_id") != "2026-09-07-r12":
        _fail("round12-dev-record round_id != 2026-09-07-r12（结构漂移）")

    # ---- r12 指引零字节复核（基准指引；只读）----
    guidance_r12_sha = _sha(GUIDANCE_R12)
    if not guidance_r12_sha.startswith(GUIDANCE_R12_SHA_PREFIX):
        _fail(f"r12 指引 sha 前 8={guidance_r12_sha[:8]} != 预期 "
              f"{GUIDANCE_R12_SHA_PREFIX}（基准指引疑被改动，立即停止）")
    registered_guidance_sha = (r12_record.get("guidance") or {}).get("sha256")
    if registered_guidance_sha != guidance_r12_sha:
        _fail("r12-prep-record guidance.sha256 登记值与盘上实测不符"
              "（链自洽破坏，立即停止）")

    # ---- framing/协议链自洽（与 r12-prep-record 登记交叉核对）----
    registered_framing_sha = (r12_record.get("renders_reuse") or {}).get(
        "framing_reference", {}).get("sha256")
    if registered_framing_sha != framing_sha:
        _fail("r12-prep-record renders_reuse.framing_reference.sha256 登记"
              "值与盘上实测不符（链自洽破坏，立即停止）")
    v1_preserved = (r12_record.get("protocol_amendment") or {}).get(
        "v1_file_preserved", {})
    if v1_preserved.get("sha256_measured") != protocol_v1_sha:
        _fail("r12-prep-record protocol_amendment.v1_file_preserved."
              "sha256_measured 登记值与盘上 evaluation-protocol-v1.md 实测"
              "不符（链自洽破坏，立即停止）")

    png_constants = _load_png_witness_constants(r12_record)
    _check_framing_raster_field(framing)
    pdf_results = _check_frozen_input_pdfs(framing)
    png_results = _check_renders_r5_pngs(png_constants)
    diag_results = _check_diag_reports()
    quotes = _extract_preregistration(dev_record)

    # ---- 指引构建 + byte-exact 自证 + 防覆写守卫 ----
    r12_text = GUIDANCE_R12.read_text(encoding="utf-8")
    guidance_text = build_guidance(r12_text)
    if build_guidance(r12_text) != guidance_text:
        _fail("同参重建不一致（byte-exact 破坏）: observation-guidance-r13.md")
    guidance_bytes = guidance_text.encode("utf-8")

    if GUIDANCE_R13.exists():
        existing = GUIDANCE_R13.read_bytes()
        if existing != guidance_bytes:
            _fail("observation-guidance-r13.md 已存在且重建字节不一致"
                  "（防覆写；拒绝覆写）")
        print("[r13-prep] 重跑自证：observation-guidance-r13.md 重建字节与既有"
              "文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆写）。")
    else:
        GUIDANCE_R13.write_bytes(guidance_bytes)
        if GUIDANCE_R13.read_bytes() != guidance_bytes:
            _fail("回读不一致: observation-guidance-r13.md")
    guidance_r13_sha = _sha(GUIDANCE_R13)

    # ---- 记录构建 + byte-exact 自证 ----
    measurement_items = r12_record["measurement_design"]["items"]
    record = build_record(framing_sha=framing_sha,
                          r12_record_sha=r12_record_sha,
                          dev_record_sha=dev_record_sha,
                          protocol_v1_sha=protocol_v1_sha,
                          guidance_r12_sha=guidance_r12_sha,
                          guidance_r13_sha=guidance_r13_sha,
                          pdf_results=pdf_results,
                          png_results=png_results,
                          diag_results=diag_results,
                          quotes=quotes,
                          measurement_items=measurement_items)
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(framing_sha=framing_sha,
                           r12_record_sha=r12_record_sha,
                           dev_record_sha=dev_record_sha,
                           protocol_v1_sha=protocol_v1_sha,
                           guidance_r12_sha=guidance_r12_sha,
                           guidance_r13_sha=guidance_r13_sha,
                           pdf_results=pdf_results,
                           png_results=png_results,
                           diag_results=diag_results,
                           quotes=quotes,
                           measurement_items=measurement_items)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r13-prep-record")

    # ---- 顶层键集合与 r12-prep-record 镜像断言（文档化差异：+pre_round_review）----
    expected_keys = (set(r12_record.keys())
                     - set(TOP_LEVEL_KEY_DELTA_REMOVE)
                     | set(TOP_LEVEL_KEY_DELTA_ADD))
    if set(record.keys()) != expected_keys:
        _fail(f"r13-prep-record 顶层键集合与 r12-prep-record 镜像（文档化差"
              f"异：-{TOP_LEVEL_KEY_DELTA_REMOVE} +{TOP_LEVEL_KEY_DELTA_ADD}）"
              f"不符：多={sorted(set(record.keys()) - expected_keys)}，"
              f"少={sorted(expected_keys - set(record.keys()))}")
    ht_expected = (set(r12_record["hypothesis_test"].keys())
                   - set(HT_KEY_DELTA_REMOVE)
                   | set(HT_KEY_DELTA_ADD))
    if set(record["hypothesis_test"].keys()) != ht_expected:
        _fail(f"hypothesis_test 键集合镜像（文档化差异："
              f"-{HT_KEY_DELTA_REMOVE} +{HT_KEY_DELTA_ADD}）不符："
              f"多={sorted(set(record['hypothesis_test'].keys()) - ht_expected)}，"
              f"少={sorted(ht_expected - set(record['hypothesis_test'].keys()))}")

    # ---- 结构自证：changed_variables 恰 1 项、度量设计五条照抄、域声明 ----
    cv = record["changed_variables"]
    if not isinstance(cv, list) or len(cv) != 1:
        _fail("changed_variables 必须恰 1 项（指引侧单变量轮）")
    if cv[0]["old_text"] != OLD_S4_SEGMENT or cv[0]["new_text"] != NEW_S4_SEGMENT:
        _fail("changed_variables[0] 新旧全文对照与指引变换常量不符")
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5（预注册度量设计）")
    if md["items"] != r12_record["measurement_design"]["items"]:
        _fail("measurement_design.items 与 r12-prep-record 登记不符"
              "（五条应照抄原文）")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"]["zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved 必须为真")
    if len(record["pre_round_review"]["reports"]) != 3:
        _fail("pre_round_review.reports 必须恰 3 份（D1/D2/D3）")

    # ---- 防覆写守卫 + 重跑自证 ----
    if RECORD.exists():
        existing = RECORD.read_bytes()
        if existing == record_bytes:
            print(f"[r13-prep] 重跑自证：r13-prep-record.json 重建字节与既有"
                  f"文件逐字节一致（字节级可重跑）；防覆写守卫生效（零覆"
                  f"写）。sha256={hashing.sha256_bytes(existing)[:16]}…")
            print(f"[r13-prep] 工件 sha256："
                  f"observation-guidance-r13.md={guidance_r13_sha}；"
                  f"r13-prep-record.json={hashing.sha256_bytes(existing)}")
            print(f"[r13-prep] 基准指引零字节复核（收工侧随编排另验）："
                  f"observation-guidance-r12.md={guidance_r12_sha}")
            return
        _fail("r13-prep-record.json 已存在且重建字节不一致（防覆写；拒绝覆写）")

    RECORD.write_bytes(record_bytes)
    if RECORD.read_bytes() != record_bytes:
        _fail("回读不一致: r13-prep-record.json")
    record_sha = _sha(RECORD)
    print(f"[r13-prep] 验证通过：基准指引锚 {GUIDANCE_R12_SHA_PREFIX} OK"
          f"（只读，零写入）；r12-prep-record 见证来源锚 "
          f"{R12_PREP_RECORD_SHA_PREFIX} OK；round12-dev-record 锚 "
          f"{R12_DEV_RECORD_SHA_PREFIX} OK（预注册候选=索引 "
          f"[{quotes['index_zero_based']}] 原文摘录在案）；diag-r13-review "
          f"三报告锚实测 OK（哈希接触、零内容解析）；renders-r5 四件 "
          f"PNG 实测=在案见证常量（magic OK）；R5 冻结输入 PDF "
          f"{len(pdf_results)} 件全 match")
    print(f"[r13-prep] 指引变换断言全过（§4 (i)(ii)→(i)(ii)(iii) 可操作化替"
          f"换=引导句逐字保留、r13 对照说明=r8 对照说明之后 §5 之前、既有"
          f"r9/r12/r8 增补块原位保留、机械替换计数受控、输出侧禁词断言零 "
          f"GT/零轮次结果数字/零诊断报告数字）")
    print(f"[r13-prep] 写出：observation-guidance-r13.md sha256={guidance_r13_sha}")
    print(f"[r13-prep] 写出：r13-prep-record.json sha256={record_sha}"
          f"（canonical JSON；同参重建两次逐字节一致；顶层键镜像 r12，文档化"
          f"差异：+pre_round_review）")


if __name__ == "__main__":
    main()
