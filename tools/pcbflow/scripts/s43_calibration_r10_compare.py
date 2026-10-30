#!/usr/bin/env python
"""CAL-R10-CLOSE：reader 判读迭代第十轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s41_calibration_r9_compare.py 同构，仅输入与轮次
常量不同；R10=development 域零变更重复轮（同指引+同渲染+全新四
实例盲读；恰零个变更变量，唯一实验操纵=reader 实例群更替——执行
round9-dev-record next_iteration_targets[0] 候选方案 (a)「同指引重复
轮」，预注册于 r10-prep-record）；检验 R9 预注册候选假设
（r9-dev-record-candidate-0a）：

  T1  解析 4 个 reader-raw-r10-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate + 分视角（top/
      bottom）分层弃权记账（bottom 本轮零旗标=分母为零，rate=null
      如实处理，绝不编造数值）+ 逐旗失败通道归因（vs R9，照 s41 重放
      方法；通道链自 r6 起逐轮衔接）：applied 态=applied-top+
      applied-bottom 旗标 vs ground-truth-v2 九条（GT 重投影继续用
      derivation-log-r5 的 frame_box_pct_r5——渲染未变=重投影输入
      未变，board_box_mm/side 等其余字段与 GT 文件逐字段原样）；
      prep1 态=prep1-top+prep1-bottom 旗标 vs ground-truth-v1 四条
      （同重投影规则）。达标线=APR-0011 暂时采纳基线，逐项诊断对照
      （禁改阈值措辞；seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称
      precision/FPR）。
      预注册假设（r9-dev-record-candidate-0a）裁决节（三分结构，两分
      如实分离）：(1) 字母裁决（唯一正式裁决，判据=r10-prep-record
      hypothesis_test 原文：support=R10 abstain_rate_total ≤ 0.5（预
      注册裁决边界，相对 r9 回落、靠近 r8 一侧）；reject=> 0.5）；
      0.5 与 APR-0011 门各自独立计算、互不凌驾，run-record 内两者
      分开表述；(2) 机制观察（单列，不凌驾字母裁决：reroute 类产量
      r9=0→r10=2（R10T-012/013 均弃权、location_evidence 明确引用
      「r9 示例 c」判据）——两条直接结论：r9「刺激缺席」机制观察被
      证伪为实例群特异；示例 c 实际功能=为「等长匹配候选解释 vs 可疑
      绕行」的弃权理由提供判据词汇（reader 明确援引后仍走弃权路径），
      即该增补未化解存在性歧义、反而成为弃权理由的组成部分——与 r9
      预注册假设设想的「化解通道」方向相反，如实记录）；(3) 度量设计
      教训（r8→r9→r10 弃权率三轮摆动=单实例/轮设计的弃权率度量不
      稳定证据；实例群更替捆绑「采样差异」与「自选工具行为差异」无
      法分离——协议侧候选，不追溯改判本轮）。
      → calibration-run-r10.json。
  T3  development 域记录（本轮性质=零变更重复轮：恰零个变更变量、
      唯一操纵=实例群更替；R9→R10 方向性对照与匹配位置对照（只描述
      不下能力断言）/假设三分裁决/下一迭代目标——延续引用 gt-audit-
      r1.json（1f20554a…）结论：bottom GT/reroute GT/L1NB 框径三候选
      全部关闭，GT 侧已全部关闭；预注册链=r9-dev-record（5ee18d61…）
      →r10-prep-record（3791edb1…）→run-r10；引用 run-r10 落盘 sha
      单向引用）→ round10-dev-record.json。

通道归因纪律（vs R9；方法照抄 s34/s36/s39/s41 deviation_note 口径）：
本轮对 R9 与 R10 均以内嵌输入（reader_flags/gt_entries/flag_views，
run sha 在案）+ compare_v3 同源几何原语（calibration._containment/
_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放通道
分类，并与各态 compare_v3 的 matches∪duplicate_reports 对拍复核。
跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是通道级不是
旗级。

读者实例披露（如实入账，不作废）：R10 四实例中三个（applied-bottom、
prep1-top、prep1-bottom）自述对给定 PNG 做了 PIL 局部裁剪放大
（2x-6x/LANCZOS）乃至像素级连通域枚举，一个（applied-top）纯 Read
直读——与 R9（4/4 纯 Read 直读）相比是仪器行为面的显著摆动；全部
输入仍仅源自给定 PNG=非盲读违规，但属实例自选工具行为差异。「实例
群更替」这一操纵因素实际捆绑了「采样差异」与「自选工具行为差异」
两个子因素，本轮设计无法分离二者——如实记为混杂因素。输出格式实例
异常（编排侧落盘前处理，盘上件=冻结证据）：prep1-bottom 原始消息带
markdown 代码围栏（按 r7 先例剥离围栏后落盘、parse 校验通过）；
prep1-top 为多行缩进 JSON（原样落盘）；applied-bottom 消息含 JSON
前置文字（仅保留 JSON 主体）——均非盲读违规。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r10）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s43_calibration_r10_compare.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"

DECLARED_DATE = "2026-09-07"
ROUND_ID = "2026-09-07-r10"
ROUND_LABEL = "r10"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
REL_PREP_R9 = "out/v3-tl2/calibration/r9-prep-record.json"
REL_PREP_R10 = "out/v3-tl2/calibration/r10-prep-record.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_GT_AUDIT = "out/v3-tl2/calibration/gt-audit-r1.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_RUN_R6 = "out/v3-tl2/calibration/calibration-run-r6.json"
REL_RUN_R7 = "out/v3-tl2/calibration/calibration-run-r7.json"
REL_RUN_R8 = "out/v3-tl2/calibration/calibration-run-r8.json"
REL_RUN_R9 = "out/v3-tl2/calibration/calibration-run-r9.json"
REL_RUN_R10 = "out/v3-tl2/calibration/calibration-run-r10.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round10-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r10-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r10-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r10-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r10-prep1-bottom.txt",
}
#: R10 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r10-prep-record（源自 r9-prep-record）脚本
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R10 复核见证=r10-prep-record
#: renders_reuse.frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r10-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r10-prep-record.json frozen_input_pdfs_check 实测值；
#: guidance-r9 锚=r10-prep-record.json guidance_reuse.sha256_measured
#: 全长（零字节复用）；prep-r10 锚与 r9-dev-record 锚=任务给定先验
#: （盘上实测一致）。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R8:
        "aad43270b1c88d446511737416f3cc191e0f882a925e9e03ef3af1a5ef207993",
    REL_GUIDANCE_R9:
        "a0c10154c4a4c2c7721dbd0a5f12861885e20d09ca0e3d06edc54b1b64e848a8",
    REL_PREP_R7:
        "e48c37fee217f3745662875640c3bef4dea27906d76ee07f85ed981815a7b3f2",
    REL_PREP_R8:
        "237920a54fa28d3f37e7926e744b51bb7c29cd8f69797c626ad2c9c7d6b01efa",
    REL_PREP_R9:
        "dd979632cf5ec51c870a6ab23f9f86953f2e0ce473db5866b3bd851ed6626173",
    REL_PREP_R10:
        "3791edb10f2ab677d77b73feb3adf96177699c2903b5fc8b56186f8228509f72",
    REL_DEV_R8:
        "437e149c3ae4d96653111be968f7d80d86ecbca7f6bb42a31f370ec5af78515d",
    REL_DEV_R9:
        "5ee18d61fc1464a92a6e9bbe46d269245748abb836bc07e535a42cff9aa57c43",
    REL_DERIV_R5:
        "623433801e8953587b60baff7827b859887ae218fad8100fb038382afa5b8663",
    REL_GT_V1:
        "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_GT_V2:
        "e1cb63d5e05761feada0b2dd030018bc04c3d3d165f33adcda2b9b348bd4b3a9",
    REL_GT_AUDIT:
        "1f20554a833d75cdbcf7df3c8212f39fd6b818bc25f47157325b44ab9804824b",
    REL_RUN_R3:
        "0b09012e01b2d9fbd0cf6afb0d71191c657746b078a0debb0703ed999af734cd",
    REL_RUN_R4:
        "0cf8bb3127f3d6b4cde2bd34abd5e9474294c14987116371d031d66da6dc8490",
    REL_RUN_R5:
        "2ed5a12867c203b6dce044944139fa255b0ebc86dac60719a50c7dd175ece0d6",
    REL_RUN_R6:
        "6e6ffdf77eacf92f9386e0ff8a281fe155fee9c5be5f487d83b0b96544f98251",
    REL_RUN_R7:
        "62b34b7129c69bc53dde8faf15d98927e946fc96fa446e43f859b4ef2e8e37be",
    REL_RUN_R8:
        "3c580eb34f1c39d5d6705b7b5303d016327fa049bdc1bc014ebe86214006fb4b",
    REL_RUN_R9:
        "e16420e5c8efc5759a4a48ceee954bb72da6064ad6b57d577de913300e683d05",
    RAW_FILES["applied-top"]:
        "f7a0e52bd7db4be5f008221a40d706163d7117af15dcbc9876289764f53461b5",
    RAW_FILES["applied-bottom"]:
        "6af5a740cb4a1fe4e828133152d711b5bd41ccfcb1727484f4fb3b60e95c16b0",
    RAW_FILES["prep1-top"]:
        "1b2f285cfeb901cc8f7e9a9daef0c7cd772eccf15fe6b6af09400c919e684f68",
    RAW_FILES["prep1-bottom"]:
        "7c6baf4313c2baede25105d27fe34665b0407781e8061829517948ceccee1125",
    PNG_FILES["applied-top"]:
        "298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5ca85e0f4f12a3cd0",
    PNG_FILES["applied-bottom"]:
        "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9",
    PNG_FILES["prep1-top"]:
        "b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca54c58f688d44f8",
    PNG_FILES["prep1-bottom"]:
        "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9",
    PDF_FILES["applied-top"]:
        "0028957c5ec9477d9dbde723c2dd6bfe93f58ec075c95caee86cb915c555667d",
    PDF_FILES["applied-bottom"]:
        "95dcdb59f9ef368a7a89665c964b43b7492ac11c48c2f98d9cc19efaab30a793",
    PDF_FILES["prep1-top"]:
        "770a50bb3089cdd48505ae320e7199a8f467bcc947c22d767c78a401d81dd35b",
    PDF_FILES["prep1-bottom"]:
        "6675458e1c7fa235c6f91c55e3a9bc5789d62126b2d9cca89f8e4512d001d47a",
}

#: 视角注入规则（确定性；读者产物无 side 字段，视角由图像名决定）。
VIEW_INJECTION_RULE = (
    "图像名 basename 确定性映射：*-top.png→top、*-bottom.png→bottom"
    "（盲读派发时每图独立给定，视角=图像名后缀；由编排侧注入 "
    "compare_v3 的 flag_views，reader 产物无 side 字段、不含视角信息）")

READER_KEYS = ("flag_id", "category", "confidence", "abstain",
               "frame_box_pct")

APPLIED_SHA_FROZEN = (
    "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85")
PREP1_SHA_FROZEN = (
    "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0bc5497fc5a62c7")

DISPATCH_DISCIPLINE = (
    "两波并行派发（与 R7/R8/R9 相同；视角内 applied→prep1 串行顺序"
    "保持）：波 1=applied-top 与 applied-bottom 并行（两视角编号独立）；"
    "波 2=prep1-top 与 prep1-bottom 并行；视角内 applied→prep1 串行顺序"
    "保持（top R10T-001..014：applied 001..002→prep1 003..014；bottom "
    "R10B 前缀已派发、本轮 bottom 两格零旗标=零 R10B 产出）；盲读派发"
    "词只含图像路径+observation-guidance-r9.md（r9 指引零字节复用）路径"
    "+视角前缀（机械命名覆盖 R9T/R9B→R10T/R10B、reader-r9-*→"
    "reader-r10-*，per r10-prep-record guidance_reuse）+起始序号；无任何"
    " GT 坐标/类别提示/期望缺陷描述；读图者不接触 GT/派生台账/任何校准"
    "产物路径")

#: 派发模式结构化记录（R10 与 R7/R8/R9 同模式：两波并行）。
PARALLEL_DISPATCH = {
    "mode": "two_wave_parallel",
    "wave_1_parallel": ["applied-top", "applied-bottom"],
    "wave_2_parallel": ["prep1-top", "prep1-bottom"],
    "within_view_serial_order": {"top": ["applied-top", "prep1-top"],
                                 "bottom": ["applied-bottom",
                                            "prep1-bottom"]},
    "flag_id_continuity": {"top": "R10T-001..014（applied 001..002→"
                                  "prep1 003..014）",
                           "bottom": "R10B 前缀已派发；本轮 bottom 两格"
                                     "零旗标（R10B-xxx 零产出）"},
    "diff_note": ("R6=四图独立全串行派发（run-r6 reader.serial_dispatch "
                  "在案）；R7 起改为两波并行、视角内 applied→prep1 串行"
                  "顺序保持，R10 与 R7/R8/R9 派发模式相同（模式差异相对 "
                  "R7 消除）；R10 特有流程差异=机械命名覆盖 R9T/R9B→"
                  "R10T/R10B 与 reader-r9-*→reader-r10-*（per r10-prep-"
                  "record guidance_reuse，命名属编排侧机械替换、判读实质"
                  "零变更）+读者实例行为差异（3/4 实例 PIL 局部裁剪放大/"
                  "像素级连通域枚举、applied-top 纯 Read 直读；输出格式"
                  "异常三例如实入账，见 reader_instance_note，"
                  "development 域只描述不断言）"),
}

#: 读者实例披露（如实入账，不作废）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R10 四实例中三个（applied-bottom、"
    "prep1-top、prep1-bottom）自述对给定 PNG 做了 PIL 局部裁剪放大"
    "（2x-6x/LANCZOS）乃至像素级连通域枚举，一个（applied-top）用 Read "
    "工具纯直读内嵌图像——与 R9（四实例全部纯 Read 直读）相比是仪器"
    "行为面的显著摆动；全部判读输入仍严格限于（指引+该 PNG），裁剪/"
    "放大/连通域枚举全部派生自给定 PNG、零外部信息、零 GT/零其他文件"
    "接触=非盲读违规，但属实例自选工具行为差异。「实例群更替」这一操纵"
    "因素实际捆绑了「采样差异」与「自选工具行为差异」两个子因素，本轮"
    "设计无法分离二者——如实记为混杂因素；每格 n=1 无统计效力。输出"
    "格式实例异常（编排侧落盘前处理，盘上件=冻结证据）：applied-bottom "
    "消息含 JSON 前置文字（仅保留 JSON 主体）、prep1-top 为多行缩进 "
    "JSON（原样落盘）、prep1-bottom 带 markdown 代码围栏（按 r7 先例"
    "剥离围栏后落盘），parse 校验全部通过，均非盲读违规")

#: 逐文件原始消息格式异常（如实入账；盘上件=编排侧落盘后的冻结证据，
#: parse 均为 direct JSON 解析、零 repair）。
RAW_MESSAGE_FORMAT_NOTES = {
    "applied-top": "原始消息即纯 JSON，原样落盘（无格式异常）",
    "applied-bottom": ("原始消息含 JSON 前置文字，编排侧落盘时仅保留 "
                       "JSON 主体、parse 校验通过（输出格式实例异常，"
                       "非盲读违规）"),
    "prep1-top": ("原始消息为多行缩进 JSON，原样落盘（parse 校验通过；"
                  "非盲读违规）"),
    "prep1-bottom": ("原始消息带 markdown 代码围栏，编排侧按 r7 先例"
                     "剥离围栏后落盘、parse 校验通过（输出格式实例异常，"
                     "非盲读违规）"),
}

GUIDANCE_REUSE_NOTE = (
    "本轮零指引变更：observation-guidance-r9.md 零字节复用（本轮唯一"
    "判读依据，r9 指引落盘即冻结；本轮零指引作者动作、零文本变更、无新"
    "指引文件；锚 a0c10154…）；唯一例外=机械命名覆盖（r10-prep-record "
    "guidance_reuse.mechanical_naming_override）：指引 §6 的 flag_id "
    "前缀 R9T/R9B→R10T/R10B 与 reader_id reader-r9-*→reader-r10-*（"
    "命名属编排侧机械替换，非判据变更；判读实质判据零变更），由派发"
    "指令给出")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 10 轮迭代"
    "（development 域零变更重复轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "零仪器变更（零变更重复轮：指引 r9 零字节复用+R5 冻结渲染复用+"
    "全新四实例盲读；恰零个变更变量，唯一实验操纵=reader 实例群更替）")


def _fail(msg: str) -> None:
    print(f"[s43-cal-r10] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    return json.loads(_rel(rel).read_text(encoding="utf-8"))


def view_for_image(image: str) -> str:
    """图像名 → 视角（确定性；非 top/bottom 后缀即 ValueError）。"""
    if image.endswith("-top.png"):
        return "top"
    if image.endswith("-bottom.png"):
        return "bottom"
    raise ValueError(f"view_for_image: 图像名无视角后缀 {image!r}")


def parse_reader_raw(raw_rel: str) -> dict:
    """reader-raw 文件解析（T1；fail-closed；reader 产物零改动）。

    返回 {reader_id, images:[{image, view, flags, rejected}], notes,
    direct_json_parse, repair}；flags=五键投影（READER_KEYS，顺序保持
    内容零改动），rejected=被 calibration fail-closed 校验拒收的旗标
    清单（{image, flag_id, error}；reader 原文不修改）。
    """
    text = _rel(raw_rel).read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        _fail(f"reader-raw 非法 JSON（fail-closed 停止）: {raw_rel}: {exc}")
    if not isinstance(doc, dict) or sorted(doc) != sorted(
            ("reader_id", "per_image", "reading_notes")):
        _fail(f"reader-raw 顶层键非法: {raw_rel}: {sorted(doc)}")
    images = []
    for entry in doc["per_image"]:
        if not isinstance(entry, dict) or sorted(entry) != sorted(
                ("image", "flags")):
            _fail(f"reader-raw per_image 条目键非法: {raw_rel}")
        image = entry["image"]
        view = view_for_image(image)
        flags, rejected = [], []
        for f in entry["flags"]:
            try:
                cal._normalize_reader_flags([f])
            except ValueError as exc:
                rejected.append({"image": image, "flag_id": f.get("flag_id"),
                                 "error": str(exc)})
                continue
            flags.append({k: f[k] for k in READER_KEYS})
        images.append({"image": image, "view": view, "flags": flags,
                       "rejected": rejected})
    return {"reader_id": doc["reader_id"], "images": images,
            "reading_notes": doc["reading_notes"],
            "direct_json_parse": True, "repair": "no_repair"}


def _gt_entries_with_r5_reprojection(gt_rel: str, deriv_doc: dict) -> list:
    """GT 文件条目 + R5 重投影：frame_box_pct ← frame_box_pct_r5
    （按 gt_id 对齐 derivation-log-r5；其余字段逐字段原样）。

    R10 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
    （板 Edge.Cuts bbox + renders-r5 PNG 像素界）未变，本轮零新派生。
    """
    r5 = {e["gt_id"]: e["frame_box_pct_r5"] for e in deriv_doc["entries"]}
    out = []
    for e in _json_load(gt_rel)["gt_entries"]:
        if e["gt_id"] not in r5:
            _fail(f"derivation-log-r5 缺 gt_id 重投影: {e['gt_id']}")
        e2 = dict(e)
        e2["frame_box_pct"] = list(r5[e["gt_id"]])
        out.append(e2)
    cal.validate_gt_entries(out)
    return out


def _state_block(state: str, state_desc: str, board_rel: str, board_sha: str,
                 gt_rel: str, gt_sha: str, raw_keys: tuple,
                 parsed: dict, gt_entries: list) -> dict:
    """单态块：内嵌 reader_flags/gt_entries/flag_views + compare_v3 报告。"""
    flags = []
    flag_views = {}
    for key in raw_keys:
        for img in parsed[key]["images"]:
            for f in img["flags"]:
                flags.append(f)
                flag_views[f["flag_id"]] = img["view"]
    report = cal.compare_v3(flags, gt_entries, flag_views=flag_views)
    if report["containment_min"] != cal.CONTAINMENT_MIN \
            or report["area_ratio_max"] != cal.AREA_RATIO_MAX:
        _fail("compare_v3 阈值与声明常量不符")
    if report["view_check"] != "full":
        _fail(f"{state} 态 flag_views 应全覆盖（view_check=full）")
    return {
        "state": state_desc,
        "source_board": {"path_rel": board_rel, "sha256": board_sha},
        "framing": {"path_rel": REL_FRAMING_R5, "sha256": _sha(REL_FRAMING_R5),
                    "note": ("R10 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮零变更重复轮：恰零个变更"
                             "变量，唯一操纵=reader 实例群更替）")},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R5, "sha256": _sha(REL_DERIV_R5),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取该台账"
                     " frame_box_pct_r5（R5 仪器像素界重投影；本轮渲染"
                     "未变故零新派生、沿用之）；board_box_mm/side 等其余"
                     "字段与 GT 文件逐字段原样；13 条全部 side=top"),
        },
        "gt_entries": gt_entries,
        "reader_flags": flags,
        "flag_views": flag_views,
        "view_check": report["view_check"],
        "compare_v3": report,
    }


def _stratified_abstain(states: dict) -> dict:
    """分视角（top/bottom）弃权记账（纯函数；分母=该视角全部旗标）。

    返回 {view: {abstain_count, flag_count, rate, fraction}}；输入=
    两态块（compare_v3.abstain.abstain_ids + flag_views）。两视角恒
    出现在结果中：零旗标视（本轮 bottom 0/0）rate=cal._ratio 零分母
    口径=None（弃权率无定义；绝不编造数值）。
    """
    cells: dict = {v: {"abstain_count": 0, "flag_count": 0}
                   for v in ("top", "bottom")}
    for st in ("prep1", "applied"):
        blk = states[st]
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            cell = cells[view]
            cell["flag_count"] += 1
            if fid in abst:
                cell["abstain_count"] += 1
    for view, cell in cells.items():
        cell["rate"] = cal._ratio(cell["abstain_count"], cell["flag_count"])
        cell["fraction"] = f"{cell['abstain_count']}/{cell['flag_count']}"
    return cells


BOTTOM_ZERO_FLAG_NOTE = (
    "bottom 两格本轮零旗标（0/0）：分母为零、弃权率无定义，按比较器 "
    "cal._ratio 零分母口径如实为 null（绝不编造数值）；r9 同格 3 旗全"
    "弃权、r8 同格 2/3 弃权——bottom 零旗标本身是本轮实例群的判读产出"
    "事实（「正常特征→不报告」通道被使用，见 courtyard_tracking."
    "bottom_zero_flag_observation）")


def _aggregate(prep: dict, appl: dict) -> dict:
    p, a = prep["compare_v3"], appl["compare_v3"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    by_view = _stratified_abstain({"prep1": prep, "applied": appl})
    return {
        "scope": ("两态联合（同板不同渲染=同一样本重复观察，联合评价"
                  "不拼凑样本量；process-v2 §4）"),
        "flag_count_total": n_fl,
        "gt_count_total": n_gt,
        "matches_total": n_match,
        "gt_matched_total": n_gm,
        "scored_total": n_sc,
        "abstain_count_total": n_ab,
        "gt_recall_total": cal._ratio(n_gm, n_gt),
        "gt_recall_arithmetic": f"gt_recall_total = ({p['gt_matched_count']}"
                                f"+{a['gt_matched_count']})/({p['gt_count']}"
                                f"+{a['gt_count']}) = {n_gm}/{n_gt}",
        "seed_match_rate_total": cal._ratio(n_match, n_sc),
        "seed_match_rate_arithmetic":
            f"seed_match_rate_total = ({len(p['matches'])}+"
            f"{len(a['matches'])})/({p['reader_scored_count']}+"
            f"{a['reader_scored_count']}) = {n_match}/{n_sc}",
        "abstain_rate_total": cal._ratio(n_ab, n_fl),
        "abstain_rate_arithmetic": f"abstain_rate_total = "
            f"({p['abstain']['abstain_count']}+"
            f"{a['abstain']['abstain_count']})/({p['reader_flag_count']}+"
            f"{a['abstain']['reader_flag_count']}) = {n_ab}/{n_fl}",
        "abstain_rate_by_state": {
            "applied": a["abstain"]["abstain_rate"],
            "applied_fraction":
                f"{a['abstain']['abstain_count']}/"
                f"{a['abstain']['reader_flag_count']}",
            "prep1": p["abstain"]["abstain_rate"],
            "prep1_fraction":
                f"{p['abstain']['abstain_count']}/"
                f"{p['abstain']['reader_flag_count']}",
        },
        "abstain_rate_by_view": {
            "top": by_view["top"]["rate"],
            "top_fraction": by_view["top"]["fraction"],
            "bottom": by_view["bottom"]["rate"],
            "bottom_fraction": by_view["bottom"]["fraction"],
            "bottom_note": BOTTOM_ZERO_FLAG_NOTE,
        },
        "abstain_rate_by_view_arithmetic":
            f"abstain_rate_by_view: top = {by_view['top']['fraction']} = "
            f"{by_view['top']['rate']}；bottom = "
            f"{by_view['bottom']['fraction']} = "
            f"{by_view['bottom']['rate']}"
            "（bottom 零旗标=分母为零，弃权率无定义——零旗标视不编造"
            "数值；分层记账如实单列，不参评任何单一达标判断）",
        "abstain_rate_definition": cal.ABSTAIN_RATE_DEFINITION,
        "seed_metric_note": cal.SEED_METRIC_NOTE,
    }


def _criteria(agg: dict) -> list:
    return [
        {"id": "gt_count_ge_12", "threshold": 12,
         "actual": agg["gt_count_total"],
         "met": agg["gt_count_total"] >= 12,
         "note": ("有效分母=v1 四条（prep1 态）+v2 九条（applied 态）"
                  "=13；全部条目在派生台账声明可见性依据（协议 §3.5 "
                  "排除口径无剔除项）")},
        {"id": "gt_recall_ge_0.75", "threshold": 0.75,
         "actual": agg["gt_recall_total"],
         "met": agg["gt_recall_total"] >= 0.75,
         "note": f"gt_recall_total={agg['gt_matched_total']}/"
                 f"{agg['gt_count_total']}"},
        {"id": "seed_match_rate_ge_0.5", "threshold": 0.5,
         "actual": agg["seed_match_rate_total"],
         "met": agg["seed_match_rate_total"] >= 0.5,
         "note": f"seed_match_rate_total={agg['matches_total']}/"
                 f"{agg['scored_total']}（诊断值，禁称 precision/FPR）"},
        {"id": "abstain_rate_le_0.5", "threshold": 0.5,
         "actual": agg["abstain_rate_total"],
         "met": agg["abstain_rate_total"] <= 0.5,
         "note": f"abstain_rate_total={agg['abstain_count_total']}/"
                 f"{agg['flag_count_total']}（单位=旗标条数；分母=全部"
                 "旗标）；本轮该分项 met，但与预注册假设裁决边界各自"
                 "独立计算、互不凌驾"},
    ]


def _compliance(agg: dict) -> dict:
    criteria = _criteria(agg)
    all_met = all(c["met"] for c in criteria)
    return {
        "baseline": "APR-0011（provisional_supersedable；"
                    "evaluation-protocol-v1 §3 联合评价）",
        "criteria": criteria,
        "joint_evaluation": "met" if all_met else "not_met",
        "joint_evaluation_rule": "任一不满足即未达标（协议 v1 §3）",
        "consecutive_rounds": {
            "id": "consecutive_2_rounds", "required": 2,
            "consecutive_met_count": 0,
            "met": False,
            "rounds": {"r1": "not_met（在案）", "r2": "not_met（在案）",
                       "r3": "not_met（在案）", "r4": "not_met（在案）",
                       "r5": "not_met（在案）", "r6": "not_met（在案）",
                       "r7": "not_met（在案）", "r8": "not_met（在案）",
                       "r9": "not_met（在案）",
                       "r10": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": ("本轮联合评价未达标（gt_recall 0.076923 与 "
                     "seed_match_rate 0.1 两项未达暂行线；abstain_rate "
                     "0.285714≤0.5 与 gt_count 达线——R9 破线的 abstain "
                     "分项本轮重新入线，但联合评价仍 not_met），连续"
                     "计数仍为 0" if not all_met
                     else "本轮联合评价达标，连续计数=1（development 域，"
                          "不计入正式采纳）"),
        },
        "critic_calibration_in_range": False,
        "critic_calibration_in_range_note": (
            "轮后实测值如实记录；谓词语义不变（正式采纳须人工批准），"
            "自动分流恒 blocked（BL-4+TD5 合取约束，达标≠自动分流）；"
            "正式采纳前 in_calibrated_range 恒 False"),
    }


# ---------------------------------------------------------------------------
# 逐旗失败通道归因（vs R9；方法照抄 s34/s36/s39/s41：通道级，非旗级）
# ---------------------------------------------------------------------------

def channel_replay(flags: list, flag_views: dict, gt_entries: list) -> dict:
    """近邻失败通道重放（纯函数；与 compare_v3 同源几何原语）。

    对每个非弃权旗标与同态全部 GT 条目计算 containment/area_ratio：
    containment<CONTAINMENT_MIN（含 None=无交集）→ 无条目（非近邻）；
    近邻且视角不符 → view_gate（视角门，不入两预注册通道计数）；
    近邻且面积比>AREA_RATIO_MAX → area_ratio_rejected（几何门）；
    近邻且面积比≤上限且类别不符 → category_mismatch（类别门）；
    类别相符且双条件过 → candidate（一对一指派候选）。
    返回 {entries, candidate_pairs}；candidate_pairs 与该态
    compare_v3 的 matches∪duplicate_reports 对拍复核。
    """
    entries = []
    for f in flags:
        if f["abstain"]:
            continue
        for e in gt_entries:
            c = cal._containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None or c < cal.CONTAINMENT_MIN:
                continue
            ar = cal._area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            base = {"flag_id": f["flag_id"], "category": f["category"],
                    "gt_id": e["gt_id"], "gt_category": e["category"],
                    "flag_view": flag_views.get(f["flag_id"]),
                    "gt_side": e["side"], "containment": cal._round6(c)}
            if flag_views.get(f["flag_id"]) and \
                    flag_views[f["flag_id"]] != e["side"]:
                entries.append(dict(base, failure="view_gate",
                                    area_ratio=(cal._round6(ar)
                                                if ar is not None else None)))
            elif ar is None or ar > cal.AREA_RATIO_MAX:
                entries.append(dict(base, failure="area_ratio_rejected",
                                    area_ratio=(cal._round6(ar)
                                                if ar is not None else None)))
            elif e["category"] != f["category"]:
                entries.append(dict(base, failure="category_mismatch",
                                    area_ratio=cal._round6(ar)))
            else:
                entries.append(dict(base, failure="candidate",
                                    area_ratio=cal._round6(ar)))
    entries.sort(key=lambda x: (x["flag_id"], x["gt_id"]))
    candidate_pairs = sorted((x["flag_id"], x["gt_id"]) for x in entries
                             if x["failure"] == "candidate")
    return {"entries": entries, "candidate_pairs": candidate_pairs}


def replay_matches_agree(replay: dict, report: dict) -> bool:
    """重放 candidate 对拍该态 compare_v3（matches∪duplicates）。"""
    ref = sorted([(m["flag_id"], m["gt_id"]) for m in report["matches"]]
                 + [(d["flag_id"], d["gt_id"])
                    for d in report["duplicate_reports"]])
    return replay["candidate_pairs"] == ref


def _channel_entry(e: dict) -> dict:
    keep = ("flag_id", "category", "gt_id", "gt_category", "containment",
            "area_ratio", "state")
    return {k: e[k] for k in keep}


def _non_abstain_flags_by_view(run_doc: dict, view: str) -> list:
    out = []
    for st in ("prep1", "applied"):
        blk = run_doc["states"][st]
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for f in blk["reader_flags"]:
            if f["flag_id"] not in abst and \
                    blk["flag_views"][f["flag_id"]] == view:
                out.append(f)
    return out


def reroute_production(states: dict) -> int:
    """reroute 类旗标产量（弃权+非弃权合计，全视角；纯函数）。

    入参=states 映射 {"prep1": 态块, "applied": 态块}（run_doc["states"]
    或内存态块均可）。
    """
    n = 0
    for st in ("prep1", "applied"):
        for f in states[st]["reader_flags"]:
            if f["category"] == "suspicious_reroute":
                n += 1
    return n


def build_channel_attribution(run_r6: dict, run_r7: dict, run_r8: dict,
                              run_r9: dict, prep: dict, appl: dict) -> dict:
    """通道归因小节（vs R9；通道级分组，非旗级配对；链自 r6 衔接）。"""
    gt_by_state = {"prep1": prep["gt_entries"], "applied": appl["gt_entries"]}
    r9_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r9["states"][st]
        r9_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r9_replays[st], blk["compare_v3"]):
            _fail(f"R9 {st} 态通道重放与 compare_v3 对拍不一致")
    r10_replays = {}
    for st, blk in (("prep1", prep), ("applied", appl)):
        r10_replays[st] = channel_replay(blk["reader_flags"],
                                         blk["flag_views"],
                                         gt_by_state[st])
        if not replay_matches_agree(r10_replays[st], blk["compare_v3"]):
            _fail(f"R10 {st} 态通道重放与 compare_v3 对拍不一致")

    def pick(replays, failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r9 = pick(r9_replays, "area_ratio_rejected")
    geo_r10 = pick(r10_replays, "area_ratio_rejected")
    cat_r9 = pick(r9_replays, "category_mismatch")
    cat_r10 = pick(r10_replays, "category_mismatch")
    view_r9 = pick(r9_replays, "view_gate")
    view_r10 = pick(r10_replays, "view_gate")

    geo_change = (
        "几何门通道（R9→R10）：面积比出局条目 0→0（两轮均空）。R10 唯一"
        "近邻条目 R10T-011（courtyard_crowding↔GT-REVC-P1-R4J3，"
        "containment 0.829864、面积比 1.770688）双条件通过=candidate 成"
        "匹配；其余 9 条非弃权旗标与同态 GT 全部条目零交集（"
        "containment=None=无交集，未及近邻门）——非弃权框未出现面积比"
        "出局，§3 收窄判据守门无回升（R7 起连续为空）；matches R9=0→"
        "R10=1。")
    cat_change = (
        "类别门通道（R9→R10）：类别不符出局条目 0→0（两轮均空；R10 非弃"
        "权旗中唯一近邻条目 R10T-011 类别相符且双条件过=直接候选成匹配，"
        "类别门本轮无生效实例）；matches 0→1；样本量极小，只描述不断言。")

    def _gate_count(doc, num, key):
        return len(doc["channel_attribution"][key][
            f"r{num}_{'area_ratio_rejected' if key == 'channel_1_geometry_gate' else 'category_mismatch'}_entries"])

    chain = {
        "scope": ("通道归因链自 r6 起逐轮在案（各轮 run-record "
                  "channel_attribution，run sha 锚在案）；跨轮 flag_id "
                  "不构成同旗配对，通道级归因"),
        "geometry_gate_area_ratio_rejected_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_1_geometry_gate"),
            "r7": _gate_count(run_r7, 7, "channel_1_geometry_gate"),
            "r8": _gate_count(run_r8, 8, "channel_1_geometry_gate"),
            "r9": len(geo_r9),
            "r10": len(geo_r10),
        },
        "category_gate_category_mismatch_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_2_category_gate"),
            "r7": _gate_count(run_r7, 7, "channel_2_category_gate"),
            "r8": _gate_count(run_r8, 8, "channel_2_category_gate"),
            "r9": len(cat_r9),
            "r10": len(cat_r10),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0；类别门 r6=1→r7=0→"
                 "r8=1→r9=0→r10=0（R10 唯一近邻条目 R10T-011 双条件通过"
                 "=candidate，两门均无生效实例）；matches r9=0→r10=1"),
    }
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R10, "sha256": _sha(REL_PREP_R10)},
            "declaration": (
                "本轮恰零个变更变量、检验恰一个假设（round9-dev-record "
                "next_iteration_targets[0] 候选方案 (a)；唯一操纵=实例群"
                "更替）；轮后按 abstain_rate_total 相对预注册裁决边界 0.5 "
                "的方向归因（r10-prep-record.json attribution_plan."
                "declaration 原文）"),
            "primary_channel": {
                "change_id": "reader-instance-group-swap",
                "metric": ("abstain_rate_total（预注册裁决边界=0.5：≤0.5 "
                           "支持、>0.5 拒绝）；按类别/视角分列产量计数"
                           "附录"),
            },
            "guard_channel": {
                "metric": "其余类别非弃权旗 frame_box_pct 几何门（面积比"
                          "出局条目）",
                "requirement": ("§3 收窄判据零变更（零变更轮），非弃权框"
                                "仍须满足；几何门面积比出局条目无回升"),
            },
        },
        "method": {
            "source_of_r9_detail": (
                "calibration-run-r9.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41 deviation_note 口径：本轮对 R9 "
                "与 R10 均以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5（含 None=无交集）"
                "无条目；近邻且视角不符=view_gate；近邻且面积比>上限="
                "area_ratio_rejected（几何门）；近邻且面积比≤上限且类别"
                "不符=category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r9_prep1_candidate_pairs": r9_replays["prep1"][
                    "candidate_pairs"],
                "r9_applied_candidate_pairs": r9_replays["applied"][
                    "candidate_pairs"],
                "r10_prep1_candidate_pairs": r10_replays["prep1"][
                    "candidate_pairs"],
                "r10_applied_candidate_pairs": r10_replays["applied"][
                    "candidate_pairs"],
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R9 两态均 0；R10 "
                         "prep1 恰 1 对且恰为 matches、applied=0；全部"
                         "复现）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R9T/R9B 与 R10T/R10B 来自不同 "
            "reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r9_area_ratio_rejected_entries": geo_r9,
            "r10_area_ratio_rejected_entries": geo_r10,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r9_category_mismatch_entries": cat_r9,
            "r10_category_mismatch_entries": cat_r10,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r9_entries": view_r9,
            "r10_entries": view_r10,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮重放"
                     "均无视角门条目——R10 全部 14 旗标均在 top 视角、"
                     "同态 GT 13 条全部 side=top；bottom 两格零旗标（零"
                     "非弃权样本）；R10 非弃权旗中 9 条与同态 GT 零交集"
                     "未及视角门、唯一近邻 R10T-011 视角相符。"),
        },
        "gate_chain_since_r6": chain,
        "r10_specific_observations": [
            "R10 非弃权 10 条中 9 条与同态 GT 全部条目零交集"
            "（containment=None=无交集，未及 GT 邻域，非阈值问题）；"
            "唯一例外 R10T-011（courtyard_crowding）↔GT-REVC-P1-R4J3 "
            "双条件通过（containment 0.829864、面积比 1.770688）成匹配"
            "——matches 0→1（R8 R8T-004↔AP-8 后再次命中）；"
            "gt_recall_total 0.0（0/13）→0.076923（1/13）。",
            "R10 suspicious_reroute 旗标 2 条（R10T-012/R10T-013，均"
            "弃权；r9=0、r8=1 条 R8T-014 弃权旗）——r9「刺激缺席」机制"
            "观察被证伪为实例群特异：J4 扇出区波状形态客观存在（r9 实例"
            "群未观察到、r10 实例群观察到）；示例 c 在 r10 的实际功能="
            "为「等长匹配候选解释 vs 可疑绕行」的弃权理由提供判据词汇"
            "（reader 明确援引「按 r9 示例 c 与第 4 节判据」后仍走弃权"
            "路径）——该增补未化解存在性歧义、反而成为弃权理由的组成"
            "部分，与 r9 预注册假设设想的「化解通道」方向相反，如实"
            "记录（见 hypothesis_test.mechanism_observation，单列不凌驾"
            "字母裁决）。",
            "R10 弃权 4/14（0.285714）——r9 8/11（0.727273）回落、重新"
            "入线（≤0.5，靠近 r8 的 0.222222 一侧，APR-0011 abstain_"
            "rate_le_0.5 单分项本轮 met 如实）；分视角 top 4/14"
            "（0.285714）、bottom 0/0（零旗标无弃权率定义，rate=null 如"
            "实处理）；reader 实例行为差异（3/4 实例 PIL 局部裁剪放大/"
            "像素级连通域枚举、applied-top 纯 Read 直读）与跨轮实例不同="
            "混杂因素，如实入账（reader_instance_note）。",
            "courtyard 被动追踪（prep-record 预注册）：R10 top 非弃权 "
            "courtyard 3 条（R10T-009/R10T-010/R10T-011；R10T-011↔"
            "GT-REVC-P1-R4J3 containment 0.829864、面积比 1.770688=r8 "
            "R8T-004 后再次 courtyard 命中；R10T-009/R10T-010 与同态 GT "
            "零交集）、弃权 1 条（R10T-002，applied 态）；courtyard 类"
            "匹配 r8=1→r9=0→r10=1；GT/阈值零改动、零期望（run-r10 "
            "courtyard_tracking 节）。bottom 两格 0 旗：r9 同格 3 旗全"
            "弃权→r10 判为正常特征不报告——「正常特征→不报告」通道在 "
            "bottom 被本轮实例群使用的直接证据（applied-bottom reading_"
            "notes 原文自述在案，逐字摘录经 substring 校验）。",
        ],
    }


# ---------------------------------------------------------------------------
# 预注册假设（r9-dev-record-candidate-0a）裁决
# （三分结构：字母裁决+机制观察+度量设计教训）
# ---------------------------------------------------------------------------

READER_NOTE_EVIDENCE = [
    {"source": "applied-top", "flag_view": "top",
     "excerpt": ("按 §3A 示例 c 的口径对全图走线做了蛇形/等长折叠形态"
                 "排查，未发现可负责任确认的规则、周期性来回折叠形态")},
    {"source": "prep1-top", "flag_view": "top",
     "excerpt": ("J4 排针扇出区多根走线出现局部小幅波状起伏"
                 "（R10T-012/013），形态接近规则周期微折叠，按 r9 示例 c "
                 "与第 4 节存在性判断一般判据无法在等长匹配类常规设计解释"
                 "与可疑绕行之间负责任取舍，均按弃权路径输出")},
    {"source": "applied-bottom", "flag_view": "bottom",
     "excerpt": "全图无长走线、无蛇形/等长折叠、无绕行改道、无断开残段"},
    {"source": "prep1-bottom", "flag_view": "bottom",
     "excerpt": ("全图无丝印文字、无可见布线走线、无文本标注，故 "
                 "silk_readability / suspicious_reroute / "
                 "doc_artifact_mismatch 均无可报告现象")},
]

#: flag 级 location_evidence 摘录（示例 c 被明确援引后仍走弃权路径的
#: 直接证据；substring 校验对象=reader-raw 盘上原文全文）。
FLAG_LOCATION_EVIDENCE = [
    {"source": "prep1-top", "flag_id": "R10T-012", "flag_view": "top",
     "excerpt": ("按 r9 示例 c 与第 4 节判据，无法负责任排除等长匹配类"
                 "常规设计解释、亦无法确认其为异常绕行，故弃权。")},
    {"source": "prep1-top", "flag_id": "R10T-013", "flag_view": "top",
     "excerpt": "同样无法在等长匹配类样式与可疑绕行之间负责任取舍，故弃权。"},
]

#: bottom「正常特征→不报告」通道使用证据（逐字摘录）。
BOTTOM_ZERO_FLAG_EVIDENCE = [
    {"source": "applied-bottom", "flag_view": "bottom",
     "excerpt": ("本图 flags 为 0，系按 §4 三路出口逐项判为『正常设计"
                 "特征→不报告』后的结果，而非未检。")},
]


def build_hypothesis_test(run_r8: dict, run_r9: dict, agg: dict, prep: dict,
                          appl: dict, attribution: dict, parsed_notes: dict,
                          raw_texts: dict) -> dict:
    """假设（r9-dev-record-candidate-0a）裁决节（预注册判据执行；三分
    结构，两分如实分离）。

    字母裁决（唯一正式裁决）=判据 r10-prep-record.json hypothesis_test
    原文：support=「R10 盲读 abstain_rate_total ≤ 0.5（即相对 r9 回落、
    靠近 r8 一侧）」；reject=「R10 abstain_rate_total > 0.5」。实测
    abstain_rate_total=0.285714（4/14）≤0.5 ⇒ 获支持（字母口径）。
    0.5 为本轮预注册裁决边界，与 APR-0011 门各自独立计算、互不凌驾、
    run-record 内分开表述。机制观察与度量设计教训单列、不凌驾、不改写
    字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R10)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    strat_r9 = _stratified_abstain(run_r9["states"])
    strat_r10 = _stratified_abstain({"prep1": prep, "applied": appl})
    boundary = 0.5
    rate_r10 = agg["abstain_rate_total"]
    # 基线数字与 prep-record 登记交叉核对（fail-closed）
    if ht["baseline_reference"]["abstain_rate_total"] != \
            run_r9["aggregation"]["abstain_rate_total"]:
        _fail("prep-record r9 弃权率基线与 run-r9 实测不符")
    if ht["baseline_reference"]["reference_round_abstain"]["r8"] != \
            run_r8["aggregation"]["abstain_rate_total"]:
        _fail("prep-record r8 弃权率基线与 run-r8 实测不符")
    rate_r9 = run_r9["aggregation"]["abstain_rate_total"]
    rate_r8 = run_r8["aggregation"]["abstain_rate_total"]
    at_or_below = rate_r10 is not None and rate_r10 <= boundary
    geo_r10 = attribution["channel_1_geometry_gate"][
        "r10_area_ratio_rejected_entries"]
    geo_r9 = attribution["channel_1_geometry_gate"][
        "r9_area_ratio_rejected_entries"]
    guard_ok = len(geo_r10) == 0 and len(geo_r10) <= len(geo_r9)
    supported = at_or_below
    verdict = "supported" if supported else "not_supported"
    verdict_text = (
        "按预注册判据（r10-prep-record.json hypothesis_test 原文）=获支持"
        "（字母口径，唯一正式裁决）：R10 盲读 abstain_rate_total 实测 "
        f"{rate_r10}（4/14）≤0.5（预注册裁决边界）——r9 回升 0.727273 在"
        "同指引（r9 指引零字节复用）+同渲染（R5 冻结件复用）+新实例群下"
        "回落至 0.285714，靠近 r8 的 0.222222 一侧，「实例差异主导 r9 "
        "回升」获方向性支持。字母裁决如实执行、结果无论方向均如实入账；"
        "机制观察与度量设计教训单列于后，不凌驾、不改写字母裁决。注意："
        "获支持≠假设被证实——方向性证据非统计证明（n=1 实例群、单次"
        "重复）；0.5 为本轮假设检验预注册裁决边界，与 APR-0011 门各自"
        "独立计算、互不凌驾（本轮门联合评价=not_met 与裁决=supported "
        "分列不合并）；实例群更替捆绑自选工具行为差异（见 "
        "mechanism_observation.confounder_note）。")
    # 机制观察证据：摘录必须逐字来自对应 reader-raw（reading_notes 或
    # location_evidence 原文；防转述失真）
    for ev in READER_NOTE_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"机制观察摘录与 reader 原文不符: {ev['source']}")
    for ev in FLAG_LOCATION_EVIDENCE:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"location_evidence 摘录与 reader 原文不符: {ev['flag_id']}")
    reroute_r8 = reroute_production(run_r8["states"])
    reroute_r9 = reroute_production(run_r9["states"])
    reroute_r10 = reroute_production({"prep1": prep, "applied": appl})
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=supported "
                 "不因本观察改写）"),
        "reroute_flag_production": {
            "r8": reroute_r8,
            "r8_detail": "R8T-014（弃权旗；run-r8 在案）",
            "r9": reroute_r9,
            "r9_detail": "四份 r9 原始件零 suspicious_reroute 旗标（run-r9 在案）",
            "r10": reroute_r10,
            "r10_detail": ("R10T-012/R10T-013（均弃权；location_evidence "
                           "明确引用「r9 示例 c」判据）"),
        },
        "reader_note_evidence": READER_NOTE_EVIDENCE,
        "flag_location_evidence": FLAG_LOCATION_EVIDENCE,
        "observation": (
            "两条直接结论（如实单列）：(i) r9 的「刺激缺席」机制观察被"
            "证伪为实例群特异——J4 扇出区波状形态客观存在（r9 实例群未"
            "观察到、r10 实例群观察到；prep1-top 原文：「J4 排针扇出区"
            "多根走线出现局部小幅波状起伏（R10T-012/013）」；applied-top "
            "仍报告未观察到该类形态=实例内差异并存的直接证据）；(ii) "
            "示例 c 在 r10 的实际功能=为「等长匹配候选解释 vs 可疑绕行」"
            "的弃权理由提供判据词汇——R10T-012/013 的 location_evidence "
            "明确援引「按 r9 示例 c 与第 4 节判据」「按 r9 示例 c 与第 "
            "4 节存在性判断一般判据」后仍走弃权路径，即该增补未化解"
            "存在性歧义、反而成为弃权理由的组成部分——与 r9 预注册假设"
            "设想的「化解通道」方向相反，如实记录（「正确测出无效同样"
            "是有效证据」）。"),
        "conclusion": (
            "字母裁决获支持（弃权率 0.285714≤0.5）≠ 假设被证实——"
            "方向性支持非统计证明（n=1 实例群）；机制观察两条直接结论"
            "如实单列：r9「刺激缺席」观察被证伪为实例群特异；示例 c "
            "增补未化解存在性歧义、反而成为弃权理由的组成部分（与 r9 "
            "预注册假设设想的「化解通道」方向相反）；「正确测出无效"
            "同样是有效证据」——示例 c 的化解目标在本轮测得无效，同样"
            "是有效证据"),
        "confounder_note": (
            "工具行为异质性（实例自选，如实入账）：R10 四实例中 3 个"
            "（applied-bottom、prep1-top、prep1-bottom）自述对给定 PNG "
            "做了 PIL 局部裁剪放大（2x-6x/LANCZOS）乃至像素级连通域枚举，"
            "1 个（applied-top）纯 Read 直读；与 r9（4/4 纯 Read 直读）"
            "相比是仪器行为面的显著摆动；全部输入仍仅源自给定 PNG=非盲读"
            "违规。「实例群更替」这一操纵因素实际捆绑了「采样差异」与"
            "「自选工具行为差异」两个子因素，本轮设计无法分离二者——"
            "混杂因素；每格 n=1 无统计效力；development 域方向性描述，"
            "不构成已证因果关系"),
    }
    metric_design_lesson = {
        "role": ("度量设计教训（如实，供未来预注册参考；本轮不追溯"
                 "适用）"),
        "lesson": (
            "本轮假设主通道=abstain_rate_total（预注册裁决边界 0.5），"
            "实测 0.285714≤0.5→字母裁决=supported；但 r8→r9→r10 弃权率 "
            "0.222222→0.727273→0.285714 的三轮摆动本身构成「单实例/轮"
            "设计的弃权率度量不稳定」的直接证据（每格 n=1、跨轮实例群"
            "全更替）；且本轮「实例群更替」操纵实际捆绑「采样差异」与"
            "「自选工具行为差异」（3/4 实例 PIL 局部裁剪放大/像素级连通"
            "域枚举 vs applied-top 纯 Read 直读），设计上无法分离——"
            "弃权率作为主通道在单实例设计下既不稳定也不可归因分解。"),
        "status": ("下一轮协议侧候选教训（如实登记）：度量稳定性候选="
                   "每格多实例重复读（n≥3）或跨轮中位数门控，须预注册后"
                   "采用，不得回溯改判本轮（本轮字母裁决=supported "
                   "维持）"),
    }
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R10,
                                "sha256": _sha(REL_PREP_R10)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "test_design": ht["test_design"],
            "null_result_note": ht["null_result_note"],
            "candidate_0_plan_a_target":
                ht["preregistered_criteria_quote"][
                    "candidate_0_plan_a_target"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "measurement": {
            "abstain_rate_r8": rate_r8,
            "abstain_rate_r8_fraction": "4/18",
            "abstain_rate_r9": rate_r9,
            "abstain_rate_r9_fraction": "8/11",
            "abstain_rate_r10": rate_r10,
            "abstain_rate_r10_fraction": (
                f"{agg['abstain_count_total']}/{agg['flag_count_total']}"),
            "verdict_boundary": boundary,
            "boundary_source": (
                "r10-prep-record.json attribution_plan.primary_channel."
                "metric（预注册裁决边界=0.5：≤0.5 支持、>0.5 拒绝）"),
            "abstain_rate_at_or_below_boundary": at_or_below,
            "boundary_independence_note": (
                "0.5 为本轮预注册裁决边界（hypothesis_test 判据），非 "
                "APR-0011 门 evaluation 本身——门三指标照常独立如实计算、"
                "互不凌驾（r10-prep-record null_result_note 原文语义）；"
                "本轮两口径方向巧合一致（abstain_rate 0.285714 同≤0.5），"
                "但门的联合评价=not_met（gt_recall 0.076923<0.75、"
                "seed_match_rate 0.1<0.5）与裁决=supported 分列不合并"),
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "其余类别非弃权旗标面积比出局条目 R9=0→R10=0（无回升）；"
                    "R10 非弃权 10 条中 9 条与同态 GT 零交集（containment="
                    "None=无交集），唯一近邻 R10T-011 双条件通过=candidate "
                    "成匹配——守门通过（守门观察如实记录）"),
                "guard_ok": guard_ok,
                "note": ("守门通道按 r10-prep-record attribution_plan."
                         "guard_channel 独立复核（r10 support_condition="
                         "弃权率边界单条件，守门非其组成要件）——两项独立"
                         "计算、结果如实分列；本轮 guard_ok=True"),
            },
            "reroute_secondary_observation": {
                "declaration": (
                    "prep-record secondary_observation 预注册：reroute 类"
                    "产量对照——实测 r9=0→r10=2，触发「若 R10 出现 reroute "
                    "类旗标（产量≥1），则 r9「刺激缺席」机制观察需修正为"
                    "实例群特异性」分支（如实执行，见 "
                    "mechanism_observation）"),
                "reroute_production_r8": reroute_r8,
                "reroute_production_r9": reroute_r9,
                "reroute_production_r10": reroute_r10,
                "r10_detail": "R10T-012/R10T-013（均弃权）",
            },
            "aggregate_context": {
                "abstain_rate_r8": rate_r8,
                "abstain_rate_r9": rate_r9,
                "abstain_rate_r10": rate_r10,
                "apr0011_joint_evaluation": "not_met",
                "note": (
                    "聚合弃权率 0.727273（8/11）→0.285714（4/14）回落至 "
                    "≤0.5（靠近 r8 的 0.222222 一侧）；APR-0011 四项照常"
                    "独立如实执行（gt_count 13≥12 与 abstain_rate "
                    "0.285714≤0.5 达线，gt_recall 0.076923<0.75 与 "
                    "seed_match_rate 0.1<0.5 未达暂行线→joint=not_met）。"
                    "0.5 既是本轮假设预注册裁决边界也是 APR-0011 abstain_"
                    "rate 阈值，但两者各自独立计算、互不凌驾（prep-record "
                    "null_result_note 原文）——门联合=not_met 与裁决="
                    "supported 分列不合并"),
            },
        },
        "verdict": verdict,
        "verdict_rule": (
            f"support={ht['support_condition']}；"
            f"reject={ht['reject_condition']}"
            "（r10-prep-record.json hypothesis_test 判据原文，轮后如实"
            "执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_design_lesson": metric_design_lesson,
        "stratified_observation": {
            "top": {"r8_rate": 0.133333,
                    "r8_fraction": "2/15",
                    "r9_rate": strat_r9["top"]["rate"],
                    "r9_fraction": strat_r9["top"]["fraction"],
                    "r10_rate": strat_r10["top"]["rate"],
                    "r10_fraction": strat_r10["top"]["fraction"],
                    "direction": "回落（top 6/9=0.666667→4/14=0.285714；"
                                 "旗标分母 9→14 扩大与弃权占比回落并存，"
                                 "如实记账）"},
            "bottom": {"r8_rate": 0.666667, "r8_fraction": "2/3",
                       "r9_rate": strat_r9["bottom"]["rate"],
                       "r9_fraction": strat_r9["bottom"]["fraction"],
                       "r10_rate": strat_r10["bottom"]["rate"],
                       "r10_fraction": strat_r10["bottom"]["fraction"],
                       "direction": ("bottom 本轮零旗标（0/0，分母为零、"
                                     "rate=null 如实处理，不编造数值）——"
                                     "r9 同格 2/2 全弃权→r10 判为正常特征"
                                     "不报告（「正常特征→不报告」通道使用，"
                                     "见 courtyard_tracking."
                                     "bottom_zero_flag_observation）")},
            "confounder_note": (
                "跨轮 reader 实例不同=本轮被操纵因素（同时是混杂因素："
                "无法与采样差异分离）；轮内实例行为差异（3/4 实例 PIL "
                "局部裁剪放大/像素级连通域枚举、applied-top 纯 Read 直读）"
                "=额外混杂因素；每格 n=1 无统计效力；development 域"
                "方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(prep: dict, appl: dict, run_r8: dict,
                             run_r9: dict) -> dict:
    """courtyard 被动追踪（r10-prep-record secondary_observation 预注册；
    零阈值改动、零期望；bottom 零旗标观察如实入账）。"""
    prep_doc = _json_load(REL_PREP_R10)
    note_quote = prep_doc["hypothesis_test"]["secondary_observation"]
    for ev in BOTTOM_ZERO_FLAG_EVIDENCE:
        if ev["excerpt"] not in _rel(RAW_FILES[ev["source"]]).read_text(
                encoding="utf-8"):
            _fail(f"bottom 零旗标证据摘录与 reader 原文不符: {ev['source']}")
    non_abstain_rows, abstain_rows = [], []
    for st, blk in (("prep1", prep), ("applied", appl)):
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        matched_by_flag = {m["flag_id"]: m
                           for m in blk["compare_v3"]["matches"]}
        for f in blk["reader_flags"]:
            if f["category"] != "courtyard_crowding":
                continue
            if f["flag_id"] in abst:
                abstain_rows.append({"flag_id": f["flag_id"], "state": st,
                                     "view": blk["flag_views"][
                                         f["flag_id"]]})
                continue
            ars, none_cnt, gt_total = [], 0, 0
            for e in blk["gt_entries"]:
                gt_total += 1
                c = cal._containment(f["frame_box_pct"],
                                     e["frame_box_pct"])
                ar = cal._area_ratio(f["frame_box_pct"],
                                     e["frame_box_pct"])
                if c is None or c < cal.CONTAINMENT_MIN:
                    if c is None:
                        none_cnt += 1
                if ar is not None:
                    ars.append(cal._round6(ar))
            m = matched_by_flag.get(f["flag_id"])
            non_abstain_rows.append({
                "flag_id": f["flag_id"], "state": st,
                "view": blk["flag_views"][f["flag_id"]],
                "frame_box_pct": f["frame_box_pct"],
                "gt_entries_checked": gt_total,
                "containment_none_count": none_cnt,
                "containment_all_none": none_cnt == gt_total,
                "area_ratio_min": min(ars) if ars else None,
                "area_ratio_max": max(ars) if ars else None,
                "matches": 1 if m else 0,
                "matched_detail": (
                    {"gt_id": m["gt_id"], "containment": m["containment"],
                     "area_ratio": m["area_ratio"]} if m else None),
                "note": ("与同态 GT 唯一近邻 GT-REVC-P1-R4J3 双条件通过="
                         "candidate 成匹配（r8 R8T-004 后再次 courtyard "
                         "命中；非阈值问题：CONTAINMENT_MIN=0.5/"
                         "AREA_RATIO_MAX=10.0 声明常量零改动）" if m else
                         "与同态 GT 全部条目零交集（containment=None）"
                         "→ 定位未及 GT 邻域（非阈值问题："
                         "CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明"
                         "常量零改动）"),
            })
    non_abstain_rows.sort(key=lambda r: r["flag_id"])
    abstain_rows.sort(key=lambda r: r["flag_id"])
    return {
        "note_source": {"path_rel": REL_PREP_R10, "sha256": _sha(REL_PREP_R10),
                        "quote": note_quote},
        "declaration": ("被动追踪（prep-record secondary_observation 预"
                        "注册）：如实记录 courtyard 类旗标匹配表现；GT/"
                        "阈值零改动、零期望、不得为提高命中调阈值"),
        "r10_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": "弃权旗不参与匹配（abstain 单列）",
        },
        "courtyard_matches_r10": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r9": 0,
        "courtyard_matches_r9_detail": (
            "R9 top 非弃权 courtyard 2 条（R9T-001/R9T-002）与同态 GT "
            "零交集、弃权 2 条（R9T-007/R9T-008）；run-r9 在案"),
        "courtyard_matches_r8": 1,
        "courtyard_matches_r8_detail": (
            "R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、面积比 "
            "2.688288；run-r8 在案）"),
        "bottom_zero_flag_observation": {
            "fact": ("R10 bottom 两格（applied-bottom/prep1-bottom）均 "
                     "0 旗标；r9 同格 3 旗全弃权（R9T/R9B 口径：R9B-001/"
                     "R9B-002 及 prep1 弃权旗）→r10 判为正常特征不报告"),
            "channel_used": ("「正常特征→不报告」通道在 bottom 被本轮"
                             "实例群使用的直接证据"),
            "evidence": BOTTOM_ZERO_FLAG_EVIDENCE,
            "evidence_check": ("摘录逐字来自 applied-bottom reading_notes"
                               "（substring fail-closed 校验通过）"),
            "rate_note": BOTTOM_ZERO_FLAG_NOTE,
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r10 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}

    rejections = []
    for key in RAW_FILES:
        for img in parsed[key]["images"]:
            for r in img["rejected"]:
                rejections.append({"file": key, **r})
    for key in RAW_FILES:
        if not parsed[key]["images"]:
            _fail(f"reader-raw per_image 空: {key}")

    deriv = _json_load(REL_DERIV_R5)
    gt_applied = _gt_entries_with_r5_reprojection(REL_GT_V2, deriv)
    gt_prep1 = _gt_entries_with_r5_reprojection(REL_GT_V1, deriv)
    if len(gt_applied) != 9 or len(gt_prep1) != 4:
        _fail("GT 条目数不符（applied=9、prep1=4）")

    appl = _state_block(
        "applied", "ASM-7 终检后终态", "out/revc-asm/board/applied.kicad_pcb",
        APPLIED_SHA_FROZEN, REL_GT_V2, _sha(REL_GT_V2),
        ("applied-top", "applied-bottom"), parsed, gt_applied)
    prep = _state_block(
        "prep1", "ASM-P1 批前快照（种子域）",
        "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb", PREP1_SHA_FROZEN,
        REL_GT_V1, _sha(REL_GT_V1), ("prep1-top", "prep1-bottom"), parsed,
        gt_prep1)

    run_r6 = _json_load(REL_RUN_R6)
    run_r7 = _json_load(REL_RUN_R7)
    run_r8 = _json_load(REL_RUN_R8)
    run_r9 = _json_load(REL_RUN_R9)
    attribution = build_channel_attribution(run_r6, run_r7, run_r8, run_r9,
                                            prep, appl)
    agg = _aggregate(prep, appl)
    comp = _compliance(agg)
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    hyp = build_hypothesis_test(run_r8, run_r9, agg, prep, appl, attribution,
                                parsed_notes, raw_texts)
    courtyard = build_courtyard_tracking(prep, appl, run_r8, run_r9)

    prep_r10 = _json_load(REL_PREP_R10)
    serial = ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"]
    by_view = {"top": 0, "bottom": 0}
    abst_by_view = {"top": 0, "bottom": 0}
    by_category: dict = {}
    for st in ("prep1", "applied"):
        blk = prep if st == "prep1" else appl
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            by_view[view] += 1
            if fid in abst:
                abst_by_view[view] += 1
        for f in blk["reader_flags"]:
            cell = by_category.setdefault(f["category"],
                                          {"total": 0, "non_abstain": 0,
                                           "abstain": 0})
            cell["total"] += 1
            if f["flag_id"] in abst:
                cell["abstain"] += 1
            else:
                cell["non_abstain"] += 1
    reader_block = {
        "dispatch_discipline": DISPATCH_DISCIPLINE,
        "reader_ids": {k: parsed[k]["reader_id"] for k in serial},
        "raw_files": {k: {"path_rel": RAW_FILES[k], "sha256": _sha(RAW_FILES[k])}
                      for k in serial},
        "parse": {k: {"direct_json_parse": parsed[k]["direct_json_parse"],
                      "repair": parsed[k]["repair"],
                      "raw_message_format_note": RAW_MESSAGE_FORMAT_NOTES[k],
                      "flag_count": sum(len(i["flags"])
                                        for i in parsed[k]["images"]),
                      "rejected_count": sum(len(i["rejected"])
                                            for i in parsed[k]["images"])}
                  for k in serial},
        "flag_count": {
            "applied_top": len([f for f in appl["reader_flags"]
                                if appl["flag_views"][f["flag_id"]] == "top"]),
            "applied_bottom": sum(
                1 for f in appl["reader_flags"]
                if appl["flag_views"][f["flag_id"]] == "bottom"),
            "prep1_top": len([f for f in prep["reader_flags"]
                              if prep["flag_views"][f["flag_id"]] == "top"]),
            "prep1_bottom": sum(
                1 for f in prep["reader_flags"]
                if prep["flag_views"][f["flag_id"]] == "bottom"),
            "by_state": {"applied": len(appl["reader_flags"]),
                         "prep1": len(prep["reader_flags"])},
            "by_view": {"top": by_view["top"], "bottom": by_view["bottom"]},
            "abstain_by_view": {"top": abst_by_view["top"],
                                "bottom": abst_by_view["bottom"]},
            "by_category": by_category,
            "reroute_class_production": reroute_production(
                {"prep1": prep, "applied": appl}),
            "total": len(appl["reader_flags"]) + len(prep["reader_flags"]),
        },
        "parallel_dispatch": PARALLEL_DISPATCH,
        "reader_instance_note": READER_INSTANCE_NOTE,
        "location_evidence_note": (
            "location_evidence 保留于 raw 原文（hash 在案），不进度量"
            "五键投影（process-v1 §2 步骤3）；R10T-012/013 的 "
            "location_evidence 明确援引「r9 示例 c」判据（mechanism_"
            "observation.flag_location_evidence 逐字摘录在案）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R10, "role": "r10_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R10)},
        {"path_rel": REL_GUIDANCE_R9,
         "role": "observation_guidance_r9_zero_byte_reuse",
         "sha256": _sha(REL_GUIDANCE_R9)},
        {"path_rel": REL_GUIDANCE_R8, "role": "observation_guidance_r8_baseline",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_DEV_R9,
         "role": "r9_dev_record_preregistration_source",
         "sha256": _sha(REL_DEV_R9)},
        {"path_rel": REL_PREP_R9, "role": "r9_prep_record_witness_source",
         "sha256": _sha(REL_PREP_R9)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_PREP_R8, "role": "r8_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R8)},
        {"path_rel": REL_PREP_R7, "role": "r7_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R7)},
        {"path_rel": PDF_FILES["applied-top"],
         "role": "source_image_pdf_applied_top_r4",
         "sha256": _sha(PDF_FILES["applied-top"])},
        {"path_rel": PDF_FILES["applied-bottom"],
         "role": "source_image_pdf_applied_bottom_r4",
         "sha256": _sha(PDF_FILES["applied-bottom"])},
        {"path_rel": PDF_FILES["prep1-top"],
         "role": "source_image_pdf_prep1_top_r4",
         "sha256": _sha(PDF_FILES["prep1-top"])},
        {"path_rel": PDF_FILES["prep1-bottom"],
         "role": "source_image_pdf_prep1_bottom_r4",
         "sha256": _sha(PDF_FILES["prep1-bottom"])},
        {"path_rel": PNG_FILES["applied-top"],
         "role": "render_png_applied_top_r5_reused",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r5_reused",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"],
         "role": "render_png_prep1_top_r5_reused",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r5_reused",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r10",
        "round_id": ROUND_ID,
        "round_label": ROUND_LABEL,
        "declared_date": DECLARED_DATE,
        "metric_version": cal.METRIC_VERSION_V3,
        "evaluation_domain": EVALUATION_DOMAIN,
        "evaluation_domain_note": {
            "declared": EVALUATION_DOMAIN,
            "basis_quote": DOMAIN_BASIS_QUOTE,
            "in_calibrated_range": False,
            "in_calibrated_range_note": (
                "development 域迭代轮不构成留出证据；正式采纳前 "
                "in_calibrated_range 恒 False（协议 v1 §1/§4）"),
            "protocol_ref": {"path_rel": REL_PROTOCOL,
                             "sha256": _sha(REL_PROTOCOL)},
        },
        "instrument_change": {
            "nature": INSTRUMENT_NATURE,
            "components": [],
            "unchanged_components": list(prep_r10["unchanged_components"]),
            "attribution_note": (
                "r10-prep-record.json attribution_plan：本轮恰零个变更"
                "变量、检验恰一个假设（round9-dev-record next_iteration_"
                "targets[0] 候选方案 (a)「同指引重复轮」，r9-dev-record-"
                "candidate-0a）——唯一操纵=reader 实例群更替；主通道="
                "abstain_rate_total（预注册裁决边界=0.5：≤0.5 支持、"
                ">0.5 拒绝；0.5 与 APR-0011 门各自独立计算、互不凌驾、"
                "run-record 内分开表述）；守门通道=其余类别非弃权旗 "
                "frame_box_pct 几何门（面积比出局条目无回升）。轮后按 "
                "abstain_rate_total 相对边界方向归因（见 run-r10 "
                "hypothesis_test 三分裁决节：字母裁决唯一正式、机制观察"
                "与度量设计教训单列不凌驾——本轮机制观察：reroute 类产量 "
                "r9=0→r10=2，r9「刺激缺席」被证伪为实例群特异、示例 c "
                "实际功能=弃权理由词汇非化解）；跨轮 flag_id 不构成同旗"
                "配对，归因是通道级不是旗级。渲染零变更下 R9→R10 任何 "
                "reader 表现变化首先归因于实例群更替（含其捆绑的自选工具"
                "行为差异，reader_instance_note 如实入账），而非内容、"
                "图层或分辨率。"),
            "ref": {"path_rel": REL_PREP_R10, "sha256": _sha(REL_PREP_R10)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL)},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；机械命名覆盖（r10-prep-record guidance_reuse."
            "mechanical_naming_override）：指引 §6 的 flag_id 前缀 "
            "R9T/R9B→R10T/R10B、reader_id reader-r9-*→reader-r10-*"
            "（命名属编排侧机械替换，非判据变更；判读实质判据零变更）"),
        "coverage_caveat": cal.COVERAGE_CAVEAT_V3,
        "reader": reader_block,
        "states": {"applied": appl, "prep1": prep},
        "parse_rejections": rejections,
        "aggregation": agg,
        "compliance": comp,
        "hypothesis_test": hyp,
        "channel_attribution": attribution,
        "courtyard_tracking": courtyard,
        "gt_audit_reference": {
            "path_rel": REL_GT_AUDIT, "sha256": _sha(REL_GT_AUDIT),
            "note": ("只读 GT 源审计（gt-audit-r1，2026-09-07，"
                     "sha 1f20554a…）：bottom GT=无源已关闭、reroute GT="
                     "无源已关闭、L1NB 框径=合理维持现框——GT 侧三候选"
                     "全部关闭（r8 轮同日审计，结论 r9/r10 延续引用）；该"
                     "审计非本轮预注册件（deviations 在案），其结论维持"
                     "本轮 GT 零改动；round10-dev-record gt_audit_ref/"
                     "next_iteration_targets 引用其结论（GT 侧已全部"
                     "关闭）"),
        },
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r9 相同）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r9 §4（零字节复用）：r8 两条显式判据（弃权适用于"
                    "存在/归类不确定；弃权不适用于仅范围不确定）、存在性"
                    "一般判据（系统性重复 vs 孤立不一致启发）与三路出口"
                    "显式化原文保留；§3A 类别 4 含 r9 增补示例 c（规则"
                    "周期折叠形态按 §4 存在性一般判据推理的候选解释说明；"
                    "形态不规则、无规律的绕行仍按关注现象处理；示例=判据"
                    "说明，非期望清单；反放宽条款原样）；abstain=true="
                    "现象是否存在或归属哪类无法负责任地判断；abstain "
                    "单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("两波并行派发（与 R7/R8/R9 相同）："
                                      "波 1=applied-top 与 applied-bottom "
                                      "并行；波 2=prep1-top 与 prep1-bottom "
                                      "并行；视角内 applied→prep1 串行顺序"
                                      "保持；top/bottom 各一独立盲读；每图"
                                      "独立判读；视角内连续编号"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R9,
                                 "sha256": _sha(REL_GUIDANCE_R9),
                                 "zero_byte_reuse": True,
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R8,
                                     "sha256": _sha(REL_GUIDANCE_R8)},
                                 "change_note": GUIDANCE_REUSE_NOTE},
            },
            "note": ("轮次预注册链：round9-dev-record.json（5ee18d61…，"
                     "next_iteration_targets[0] 候选方案 (a) 原文被 "
                     "r10-prep-record 逐字摘录预注册）→r10-prep-record"
                     ".json（3791edb1…，本轮预注册件）先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；渲染"
                     "复用见证=四 PNG 盘上实测 sha 与见证常量逐一相等+"
                     "渲染输入侧冻结 PDF 复核一致；见证常量源=r9-prep-"
                     "record.json（dd979632…），在案）；observation-"
                     "guidance-r9.md 零字节复用（锚 a0c10154…，零指引"
                     "作者动作）；GT 重投影（derivation-log-r5.json，13 "
                     "条 frame_box_pct_r5）已在案沿用（渲染未变=零新"
                     "派生）；盲读后本包只做比对与记录（读者产物零改动）。"
                     "GT 冻结纪律：轮后未增删改；gt-audit-r1 结论维持 GT "
                     "零改动（三候选关闭，gt_audit_reference 在案）。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "r7_run": {"path_rel": REL_RUN_R7, "sha256": _sha(REL_RUN_R7)},
            "r8_run": {"path_rel": REL_RUN_R8, "sha256": _sha(REL_RUN_R8)},
            "r9_run": {"path_rel": REL_RUN_R9, "sha256": _sha(REL_RUN_R9)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）与 R9"
                     "（§3A 示例 c 增补轮）run 在案；R10=零变更重复轮"
                     "（同指引+同渲染+新实例群）；轮间对比见 "
                     "round10-dev-record.json 的方向性观察与 "
                     "channel_attribution、hypothesis_test（development "
                     "域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器与通道重放为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-07-r10（事件序="
            "预注册冻结（round9-dev-record（5ee18d61…，在案）→r10-prep-"
            "record（3791edb1…，本轮预注册件）→复用渲染见证）→盲读→"
            "比对记录；在案延续=gt-audit-r1 只读 GT 源审计（r8 轮落盘，"
            "本轮延续引用其结论，GT 零改动维持））"),
    }


DEV_OBSERVATIONS = [
    "R9→R10 旗标量对照：11→14（非弃权 3→10、弃权 8→4），聚合弃权率 "
    "0.727273（8/11）→0.285714（4/14）——r9 回升在同指引（零字节复用）+"
    "同渲染（R5 冻结件复用）+新实例群下回落至 ≤0.5，靠近 r8 的 0.222222 "
    "一侧（APR-0011 abstain_rate_le_0.5 单分项本轮 met 如实）；分态弃权率 "
    "applied 0.6（3/5）→0.5（1/2）、prep1 0.833333（5/6）→0.25（3/12）。"
    "零变更轮（恰零个变更变量）下，该回落首先归因于唯一操纵=实例群更替"
    "（「实例差异主导 r9 回升」获方向性支持；跨轮实例不同=混杂因素，"
    "每格 n=1）——但实例群更替实际捆绑「采样差异」与「自选工具行为差异」"
    "（见工具行为条目），本轮设计无法分离。",
    "分视角弃权率：top 0.666667（6/9）→0.285714（4/14）回落；bottom "
    "1.0（2/2）→0/0——bottom 两格本轮零旗标，分母为零、弃权率无定义，"
    "rate=null 如实处理（绝不编造数值）；r9 bottom 同格 3 旗全弃权→r10 "
    "判为正常特征不报告（「正常特征→不报告」通道首次被实例群在 bottom "
    "使用，applied-bottom reading_notes 原文自述在案）。",
    "matches 0→1：R10 非弃权 10 条中 9 条与同态 GT 全部条目零交集"
    "（containment=None=无交集，未及 GT 邻域，非阈值问题），唯一例外 "
    "R10T-011（courtyard_crowding）↔GT-REVC-P1-R4J3 双条件通过"
    "（containment 0.829864、面积比 1.770688）=r8 R8T-004↔AP-8 后再次 "
    "courtyard 命中；gt_recall_total 0.0（0/13）→0.076923（1/13）、"
    "seed_match_rate_total 0.0（0/3）→0.1（1/10）（诊断口径，禁称 "
    "precision/FPR）。",
    "通道归因（vs R9，预注册重放方法）：几何门面积比出局 0→0（R7 起"
    "连续空）；类别门 0→0（R10 唯一近邻条目 R10T-011 类别相符且双条件过"
    "=直接候选成匹配，类别门无生效实例）；视角门 0→0（R10 全部 14 旗标"
    "均在 top、GT 13 条全部 side=top；bottom 零非弃权旗）。通道链自 r6 "
    "起：几何门 r6=1→r7=0→r8=0→r9=0→r10=0；类别门 r6=1→r7=0→r8=1→"
    "r9=0→r10=0。",
    "预注册假设（r9-dev-record-candidate-0a）字母裁决=获支持（abstain_"
    "rate_total 0.285714≤0.5 预注册裁决边界，r10-prep-record 判据原文"
    "执行；唯一正式裁决）；守门通道独立复核（几何门 0→0 无回升）通过。"
    "机制观察单列（不凌驾）：reroute 类产量 r9=0→r10=2（R10T-012/013，"
    "均弃权，location_evidence 明确引用「r9 示例 c」判据）——两条直接"
    "结论：(i) r9「刺激缺席」机制观察被证伪为实例群特异（J4 扇出区波状"
    "形态客观存在：r9 实例群未观察到、r10 实例群观察到）；(ii) 示例 c "
    "在 r10 的实际功能=为「等长匹配候选解释 vs 可疑绕行」的弃权理由提供"
    "判据词汇（reader 明确援引后仍走弃权路径）——该增补未化解存在性歧义、"
    "反而成为弃权理由的组成部分，与 r9 预注册假设设想的「化解通道」方向"
    "相反，如实记录（「正确测出无效同样是有效证据」）。",
    "工具行为异质性（实例自选，如实入账）：R10 四实例中三个"
    "（applied-bottom、prep1-top、prep1-bottom）自述对给定 PNG 做了 "
    "PIL 局部裁剪放大（2x-6x/LANCZOS）乃至像素级连通域枚举，一个"
    "（applied-top）纯 Read 直读——与 R9（4/4 纯 Read 直读）相比是仪器"
    "行为面的显著摆动；全部输入仍仅源自给定 PNG=非盲读违规；「实例群"
    "更替」这一操纵因素实际捆绑了「采样差异」与「自选工具行为差异」两个"
    "子因素，本轮设计无法分离二者——如实记为混杂因素"
    "（reader_instance_note）。",
    "输出格式实例异常（编排侧落盘前处理，盘上件=冻结证据）：prep1-bottom "
    "原始消息带 markdown 代码围栏（按 r7 先例剥离围栏后落盘、parse 校验"
    "通过）；prep1-top 为多行缩进 JSON（原样落盘）；applied-bottom 消息"
    "含 JSON 前置文字（仅保留 JSON 主体）——三例 parse 校验全部通过，"
    "均非盲读违规（判读输入仍只有指引+该 PNG）。",
    "courtyard 被动追踪（prep-record 预注册）：R10 top 非弃权 courtyard "
    "3 条——R10T-011 命中 GT-REVC-P1-R4J3（containment 0.829864、面积比 "
    "1.770688）、R10T-009/R10T-010 与同态 GT 零交集（定位未及 GT 邻域、"
    "非阈值问题）；弃权 1 条（R10T-002，applied 态）；courtyard 类匹配 "
    "r8=1→r9=0→r10=1；GT/阈值零改动、零期望。",
    "跨轮 flag_id 不构成同旗配对（R9T/R9B 与 R10T/R10B 来自不同 reader "
    "实例）；通道归因是通道级不是旗级（run-r10 channel_attribution."
    "pairing_caveat）；重放与 compare_v3 对拍一致（R9 两态均空；R10 "
    "prep1 恰 1 对=matches、applied 空）。",
]

DEV_NEXT_TARGETS = [
    "度量稳定性候选（协议侧，本轮实测导出、须预注册后执行）：r8→r9→r10 "
    "弃权率 0.222222→0.727273→0.285714 三轮摆动=单实例/轮设计的弃权率"
    "度量不稳定证据（每格 n=1、跨轮实例群全更替）——候选方案：每格多"
    "实例重复读（n≥3，分离实例内/实例间方差）或跨轮中位数门控（以多轮"
    "中位数替代单轮值作主通道输入）；对应 r10-prep-record 引用的候选方案 "
    "(b)（多 reader 重复读，至今未执行）。两案均须先预注册再执行，不得"
    "回溯改判既往轮次。",
    "示例 c 去留评估候选（r11 指引侧，须预注册）：r10 实测示例 c 的实际"
    "功能=弃权理由词汇（R10T-012/013 reader 明确援引「按 r9 示例 c 与"
    "第 4 节判据」后仍走弃权路径）而非判据化解——评估其保留/修改/移除"
    "时，判据应为其「弃权理由词汇效应 vs 化解目标」的对照（该增补未化解"
    "存在性歧义、反而成为弃权理由的组成部分）；指引侧变更须预注册+"
    "单变量纪律。",
    "渲染侧 bottom 图层清单仍是候选（r6/r7/r8/r9-prep-record/"
    "r10-prep-record 在案候选；R10 bottom 两格零旗标——「正常特征→不"
    "报告」通道被实例群使用在案，bottom 图层清单缺失的影响仍无法与实例"
    "差异分离）；属渲染侧变更，须预注册+声明零仪器变更纪律例外。",
    "courtyard 密集旗追踪延续（指引侧观察候选）：R10T-011↔GT-REVC-P1-"
    "R4J3（containment 0.829864、面积比 1.770688）为 r8 R8T-004 后再次 "
    "courtyard 命中、R10T-009/R10T-010 零交集——继续被动追踪（GT/阈值"
    "零改动；不得为提高命中调阈值；无期望）。",
    "GT 侧已全关闭声明延续：r8 轮同日只读审计 gt-audit-r1（1f20554a…）"
    "三候选全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、L1NB "
    "框径=合理维持现框），r9/r10 延续零改动——GT 侧已全部关闭，后续迭代"
    "回归指引侧/渲染侧/协议侧。",
    "迭代目标不变式：任何仪器/指引/协议变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）；连续达标计数 0（R9 后）→0（本轮），正式采纳"
    "门槛未达成。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round10-dev-record 文档构建（T3；单向引用 run-r10 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    trend_rows = []
    for r in (5, 6, 7, 8, 9):
        d = _json_load(f"out/v3-tl2/calibration/calibration-run-r{r}.json")
        a_, c_ = d["aggregation"], d["compliance"]
        trend_rows.append({
            "round": f"r{r}", "round_id": d["round_id"],
            "flag_count_total": a_["flag_count_total"],
            "abstain_count_total": a_["abstain_count_total"],
            "abstain_rate_total": a_["abstain_rate_total"],
            "matches_total": a_["matches_total"],
            "gt_recall_total": a_["gt_recall_total"],
            "seed_match_rate_total": a_["seed_match_rate_total"],
            "joint_evaluation": c_["joint_evaluation"],
            "source": {"path_rel":
                       f"out/v3-tl2/calibration/calibration-run-r{r}.json",
                       "sha256": _sha(
                           f"out/v3-tl2/calibration/"
                           f"calibration-run-r{r}.json")},
        })
    trend_rows.append({
        "round": "r10", "round_id": run_doc["round_id"],
        "flag_count_total": agg["flag_count_total"],
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "matches_total": agg["matches_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "source": {"path_rel": REL_RUN_R10, "sha256": run_sha},
    })
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round10_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域零变更重复轮（第十轮）：本轮恰零个变更变量——"
            "判读指引 observation-guidance-r9.md 零字节复用（无新指引"
            "文件，零文本变更，锚 a0c10154…），R5 冻结渲染件逐字节复用"
            "（零仪器变更、零重渲染，PNG 见证在案），GT 集/协议与度量"
            "版本/比较器阈值零改动（GT 重投影沿用 derivation-log-r5——"
            "渲染未变=零新派生；gt-audit-r1 三候选关闭结论延续）；唯一"
            "实验操纵=reader 实例群更替（全新四实例，四格各一——执行 "
            "round9-dev-record next_iteration_targets[0] 候选方案 (a)"
            "「同指引重复轮」，预注册于 r10-prep-record，链 5ee18d61→"
            "3791edb1）；检验 r9 预注册候选假设 r9-dev-record-candidate-"
            "0a（判据=r10-prep-record.json hypothesis_test，轮后如实"
            "执行，三分结构：字母裁决唯一正式+机制观察单列+度量设计"
            "教训）；预注册裁决边界 0.5 只用于本轮假设检验字母裁决，"
            "与 APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）各自独立计算、互不凌驾、分开表述；机械"
            "命名覆盖 R9T/R9B→R10T/R10B 与 reader-r9-*→reader-r10-*"
            "（guidance_reuse，判读实质零变更）；按协议 v1 §4，迭代轮"
            "证据不冒充未见留出，in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "preregistration_chain_note": (
            "预注册链（含哈希）：round9-dev-record.json（5ee18d61…，"
            "next_iteration_targets[0] 候选方案 (a) 原文）→r10-prep-"
            "record.json（3791edb1…，逐字摘录候选原文预注册=本轮执行"
            "依据）→run-r10（本链执行落盘）；observation-guidance-r9.md "
            "零字节复用（锚 a0c10154…）；渲染复用见证源=r9-prep-record"
            ".json（dd979632…）"),
        "run_record_ref": {"path_rel": REL_RUN_R10, "sha256": run_sha},
        "gt_audit_ref": run_doc["gt_audit_reference"],
        "flag_production": {
            "reader_ids": run_doc["reader"]["reader_ids"],
            "raw_files": run_doc["reader"]["raw_files"],
            "flag_count_by_file": {
                key: run_doc["reader"]["parse"][key]["flag_count"]
                for key in ("applied-top", "applied-bottom", "prep1-top",
                            "prep1-bottom")},
            "non_abstain_count": agg["scored_total"],
            "abstain_count": agg["abstain_count_total"],
            "abstain_rate": agg["abstain_rate_total"],
            "abstain_rate_by_view": agg["abstain_rate_by_view"],
            "flag_count_by_category": run_doc["reader"]["flag_count"][
                "by_category"],
            "reroute_class_production": run_doc["reader"]["flag_count"][
                "reroute_class_production"],
            "parse_rejections": run_doc["parse_rejections"],
            "blind_discipline": DISPATCH_DISCIPLINE,
            "reader_instance_note": READER_INSTANCE_NOTE,
            "note": ("flag 全部通过 calibration fail-closed 校验（拒收"
                     "清单为空）；读者产物为冻结证据，本包零改动；派发"
                     "模式=两波并行（与 R7/R8/R9 相同）；机械命名覆盖 "
                     "R9T/R9B→R10T/R10B（guidance_reuse）；读者实例行为"
                     "差异（3/4 实例 PIL 局部裁剪放大/像素级连通域枚举、"
                     "applied-top 纯 Read 直读）与输出格式异常三例如实"
                     "登记为混杂因素，不作废"),
        },
        "diagnostic_result": {
            "joint_evaluation": comp["joint_evaluation"],
            "criteria": [{"id": c["id"], "actual": c["actual"],
                          "threshold": c["threshold"], "met": c["met"]}
                         for c in comp["criteria"]],
            "gt_recall_total": agg["gt_recall_total"],
            "seed_match_rate_total": agg["seed_match_rate_total"],
            "abstain_rate_total": agg["abstain_rate_total"],
            "seed_metric_note": cal.SEED_METRIC_NOTE,
        },
        "hypothesis_test_i": run_doc["hypothesis_test"],
        "joint_evaluation_trend": {
            "after_r9": {"consecutive_met_count": 0,
                         "note": "R9 联合评价 not_met（在案），连续达标"
                                 "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价 not_met（gt_recall "
                                   "0.076923 与 seed_match_rate 0.1 未达"
                                   "暂行线；abstain_rate 0.285714≤0.5 "
                                   "单分项重新入线——R9 破线后回落，但"
                                   "联合评价仍 not_met）"},
            "consecutive_met_count_now": 0,
            "by_round": trend_rows,
            "note": "连续达标计数变动：0（R9 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r9": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，零变更重复轮：同指引+同渲染+新实例群，"
            "唯一操纵=实例群更替）14 旗标中 4 弃权、10 非弃权，matches=1："
            "gt_recall=0.076923（1/13）、seed_match_rate=0.1（1/10，诊断"
            "口径，禁称 precision/FPR）、abstain_rate=0.285714（4/14，"
            "较 R9 0.727273 回落至 ≤0.5、靠近 R8 的 0.222222 一侧），"
            "联合评价 not_met（gt_recall 与 seed_match_rate 两项未达 "
            "APR-0011 暂行线；abstain_rate 单分项本轮 met；诊断对照，"
            "非采纳门；连续达标计数 0→0）。预注册假设（r9-dev-record-"
            "candidate-0a）裁决（按 r10-prep-record hypothesis_test 判据）"
            "=获支持（字母口径，唯一正式裁决）：abstain_rate_total "
            "0.285714≤0.5 预注册裁决边界——「实例差异主导 r9 回升」获"
            "方向性支持（方向性证据非统计证明：每格 n=1、实例群单次"
            "重复；0.5 为本轮"
            "假设检验裁决边界，与 APR-0011 门各自独立计算、互不凌驾，"
            "门联合=not_met 与裁决=supported 分列不合并）。机制观察单列"
            "（不凌驾）三条如实：①实例群因素主导弃权率摆动获方向性支持="
            "单实例/轮设计的弃权率度量不稳定证据（r8→r9→r10 0.222222→"
            "0.727273→0.285714 三轮摆动；且实例群更替捆绑自选工具行为"
            "差异——3/4 实例 PIL 局部裁剪放大/像素级连通域枚举 vs "
            "applied-top 纯 Read 直读——本轮设计无法分离，混杂因素如实"
            "入账）；②示例 c 实际功能=弃权理由词汇非化解（reroute 类"
            "产量 r9=0→r10=2，R10T-012/013 均弃权且 location_evidence "
            "明确援引示例 c——r9「刺激缺席」机制观察被证伪为实例群特异；"
            "「正确测出无效同样是有效证据」）；③bottom「正常特征→不报告」"
            "通道首次被实例群使用（r9 同格 3 旗全弃权→r10 零旗标，"
            "applied-bottom reading_notes 原文自述在案）。输出格式实例"
            "异常三例（applied-bottom 前置文字剥离、prep1-top 缩进 JSON "
            "原样、prep1-bottom 围栏剥离）如实登记、均非盲读违规。GT 侧"
            "三候选经 gt-audit-r1 全部关闭（延续零改动，GT 侧不再有"
            "候选）。不做「能力已修复/已达成」类断言；in_calibrated_"
            "range 恒 False。本批证据按协议 v1 §4 属 development 域，"
            "不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R9 对照基线=calibration-run-r9.json（e16420e5…，在案）；"
            "R8 对照基线=calibration-run-r8.json（3c580eb3…，在案）；"
            "轮间对比只做方向性描述。",
            "通道归因方法：照抄 run-r9 channel_attribution 的重放口径"
            "（deviation_note 承接），R9 与 R10 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r10 "
            "channel_attribution.method）。",
            "读者实例行为偏差如实记录：R10 四实例中 3 个自述对给定 PNG "
            "做 PIL 局部裁剪放大（2x-6x/LANCZOS）乃至像素级连通域枚举、"
            "1 个（applied-top）纯 Read 直读（较 R9 4/4 纯 Read 是仪器"
            "行为面显著摆动；全部输入仍仅源自给定 PNG=非盲读违规）；"
            "输出格式异常三例（applied-bottom 消息含 JSON 前置文字仅保留"
            " JSON 主体、prep1-top 多行缩进 JSON 原样落盘、prep1-bottom "
            "带 markdown 代码围栏按 r7 先例剥离后落盘）parse 校验全部"
            "通过。跨轮 reader 实例不同=本轮被操纵因素且捆绑自选工具"
            "行为差异=混杂因素，每格 n=1。",
            "假设裁决三分结构纪律：字母裁决=唯一正式裁决（预注册判据"
            "原文执行）；机制观察与度量设计教训单列，不得凌驾或改写字母"
            "裁决；本轮字母裁决=supported 维持不变（获支持≠假设被证实——"
            "方向性证据非统计证明；0.5 裁决边界与 APR-0011 门分开表述、"
            "互不凌驾：门联合评价=not_met 如实分列）。",
        ],
    }


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


def _assert_observation_numbers(run_doc: dict, run_r9: dict, run_r8: dict,
                                attribution: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    agg = run_doc["aggregation"]
    ab = agg["abstain_rate_total"]
    if f"{ab}" != "0.285714" or "0.285714（4/14）" not in obs:
        _fail("观察文本弃权率与实测不一致")
    if agg["abstain_count_total"] != 4 or agg["flag_count_total"] != 14:
        _fail("观察文本弃权记账与实测不一致")
    if agg["scored_total"] != 10 or agg["matches_total"] != 1 \
            or agg["gt_matched_total"] != 1:
        _fail("观察文本非弃权/匹配记账与实测不一致")
    if run_doc["hypothesis_test"]["verdict"] != "supported":
        _fail("假设字母裁决与预注册判据复算不符")
    if reroute_production(run_doc["states"]) != 2 \
            or reroute_production(run_r9["states"]) != 0 \
            or reroute_production(run_r8["states"]) != 1:
        _fail("reroute 类产量与字母裁决输入不一致")
    for need in ("0.222222", "0.727273", "11→14", "0→1", "0.5（1/2）",
                 "0.25（3/12）", "0.666667", "1.0", "0/0", "0.076923",
                 "0.1（1/10）", "0.829864", "1.770688", "R10T-011",
                 "示例 c", "证伪", "正常特征→不报告", "PIL", "围栏",
                 "4/14", "8/11"):
        if need not in obs:
            _fail(f"观察文本缺实测数字 {need}")
    # 分视角记账与 run 落盘一致（bottom 零旗标 rate=None）
    by_view = agg["abstain_rate_by_view"]
    if by_view["top"] != 0.285714 or by_view["bottom"] is not None:
        _fail("分视角弃权率与观察文本不一致")
    # 通道条目数与文本一致（几何 R9 0→R10 0；类别 R9 0→R10 0）
    geo9 = attribution["channel_1_geometry_gate"][
        "r9_area_ratio_rejected_entries"]
    geo10 = attribution["channel_1_geometry_gate"][
        "r10_area_ratio_rejected_entries"]
    cat9 = attribution["channel_2_category_gate"][
        "r9_category_mismatch_entries"]
    cat10 = attribution["channel_2_category_gate"][
        "r10_category_mismatch_entries"]
    if not (len(geo9) == 0 and len(geo10) == 0
            and len(cat9) == 0 and len(cat10) == 0):
        _fail("通道条目数与观察文本声明不一致")
    # courtyard 追踪与实测一致（R10 top 非弃权 courtyard=3；R9=2；R8=6）
    r10_courtyard = [f["flag_id"] for f in
                     _non_abstain_flags_by_view(run_doc, "top")
                     if f["category"] == "courtyard_crowding"]
    r9_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_r9, "top")
                    if f["category"] == "courtyard_crowding"]
    r8_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_r8, "top")
                    if f["category"] == "courtyard_crowding"]
    if sorted(r10_courtyard) != ["R10T-009", "R10T-010", "R10T-011"] \
            or sorted(r9_courtyard) != ["R9T-001", "R9T-002"] \
            or sorted(r8_courtyard) != ["R8T-002", "R8T-004", "R8T-006",
                                        "R8T-007", "R8T-012", "R8T-013"]:
        _fail("courtyard 旗计数与观察文本声明不一致")
    # courtyard 追踪明细：R10T-011 恰 1 命中（双条件数值）；其余零交集
    ct = run_doc["courtyard_tracking"]["r10_courtyard_flags"]["non_abstain"]
    hit = [r for r in ct if r["matches"]]
    if len(hit) != 1 or hit[0]["flag_id"] != "R10T-011" \
            or hit[0]["matched_detail"]["gt_id"] != "GT-REVC-P1-R4J3" \
            or hit[0]["matched_detail"]["containment"] != 0.829864 \
            or hit[0]["matched_detail"]["area_ratio"] != 1.770688:
        _fail("courtyard 追踪命中明细与实测不一致")
    if not all(r["containment_all_none"] and r["matches"] == 0
               for r in ct if r["flag_id"] != "R10T-011"):
        _fail("courtyard 追踪零交集明细与实测不一致")
    if run_doc["courtyard_tracking"]["courtyard_matches_r10"] != 1:
        _fail("courtyard 命中合计与实测不一致")
    # R9/R8 基线 matches 明细数值（R9 零匹配；R8T-004 vs AP-8）
    if len(run_r9["states"]["applied"]["compare_v3"]["matches"]) != 0 \
            or len(run_r9["states"]["prep1"]["compare_v3"]["matches"]) != 0:
        _fail("R9 基线 matches 与在案值不一致")
    matches8 = run_r8["states"]["applied"]["compare_v3"]["matches"]
    if len(matches8) != 1 or matches8[0]["flag_id"] != "R8T-004" \
            or matches8[0]["containment"] != 0.838782 \
            or matches8[0]["area_ratio"] != 2.688288:
        _fail("R8 基线 matches 明细与在案值不一致")
    # R10T-011 vs R4J3 双条件数值独立复算
    blk = run_doc["states"]["prep1"]
    f011 = next(f for f in blk["reader_flags"]
                if f["flag_id"] == "R10T-011")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-P1-R4J3")
    if cal._round6(cal._containment(f011["frame_box_pct"],
                                    g["frame_box_pct"])) != 0.829864 \
            or cal._round6(cal._area_ratio(f011["frame_box_pct"],
                                           g["frame_box_pct"])) != 1.770688:
        _fail("R10T-011 双条件数值与观察文本不一致")
    # 机制观察摘录逐字来自 reader 原文（防转述失真）
    notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    for ev in mo["reader_note_evidence"]:
        if ev["excerpt"] not in notes[ev["source"]]:
            _fail(f"机制观察摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["flag_location_evidence"]:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"location_evidence 摘录与 reader 原文不符: "
                  f"{ev['flag_id']}")
    # 机制观察产量数与实测一致
    if mo["reroute_flag_production"]["r8"] != 1 \
            or mo["reroute_flag_production"]["r9"] != 0 \
            or mo["reroute_flag_production"]["r10"] != 2:
        _fail("机制观察 reroute 产量与实测不一致")
    # bottom 零旗标证据摘录逐字在案
    for ev in run_doc["courtyard_tracking"]["bottom_zero_flag_observation"][
            "evidence"]:
        if ev["excerpt"] not in notes[ev["source"]]:
            _fail(f"bottom 零旗标证据摘录与 reader 原文不符: {ev['source']}")
    # 非弃权旗十条身份与零交集声明一致
    non_abstain = sorted(_non_abstain_flags_by_view(run_doc, "top")
                         + _non_abstain_flags_by_view(run_doc, "bottom"),
                         key=lambda f: f["flag_id"])
    if [f["flag_id"] for f in non_abstain] != [
            "R10T-001", "R10T-003", "R10T-004", "R10T-005", "R10T-006",
            "R10T-007", "R10T-008", "R10T-009", "R10T-010", "R10T-011"]:
        _fail("非弃权旗身份与观察文本声明不一致")


def main() -> None:
    # 输入先验锚（fail-closed）
    for rel, want in FROZEN_SHA256.items():
        p = _rel(rel)
        if not p.is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")
        got = _sha(rel)
        if got != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {got[:8]}…≠{want[:8]}…")

    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r10")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R9), _json_load(REL_RUN_R8),
        run["channel_attribution"], parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R10), run_bytes,
                         "calibration-run-r10.json")
    run_sha = _sha(REL_RUN_R10)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round10-dev-record")
    dev_status = _commit(_rel(REL_DEV_RECORD), dev_bytes,
                         "round10-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    hyp = run["hypothesis_test"]
    print(f"[s43-cal-r10] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s43-cal-r10] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s43-cal-r10] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    bv = agg["abstain_rate_by_view"]
    print(f"[s43-cal-r10] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']} "
          f"(top {bv['top']} / bottom {bv['bottom']}——零旗标无弃权率定义)")
    print(f"[s43-cal-r10] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；边界 0.5、实测 "
          f"{hyp['measurement']['abstain_rate_r10']}；reroute 产量="
          f"{hyp['measurement']['reroute_secondary_observation']['reroute_production_r10']}"
          f"，机制观察与度量设计教训单列）")
    print(f"[s43-cal-r10] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s43-cal-r10] channel_attribution: "
          f"geo R9={len(ca['channel_1_geometry_gate']['r9_area_ratio_rejected_entries'])}"
          f"→R10={len(ca['channel_1_geometry_gate']['r10_area_ratio_rejected_entries'])}, "
          f"cat R9={len(ca['channel_2_category_gate']['r9_category_mismatch_entries'])}"
          f"→R10={len(ca['channel_2_category_gate']['r10_category_mismatch_entries'])}")
    print(f"[s43-cal-r10] commit: run={run_status} dev={dev_status}")
    for rel in (REL_RUN_R10, REL_DEV_RECORD):
        print(f"[s43-cal-r10] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s43-cal-r10] R10 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
