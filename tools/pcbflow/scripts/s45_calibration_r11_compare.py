#!/usr/bin/env python
"""CAL-R11-CLOSE：reader 判读迭代第十一轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s43_calibration_r10_compare.py 同构，仅输入与轮次
常量不同；R11=development 域协议侧单变量变更轮（每视角独立实例数
1→3；evaluation-protocol-v1→v1.1 追加式修订；指引 r9 零字节复用+
R5 冻结渲染复用+GT/阈值零变更；唯一实验操纵=协议侧多实例修订——
执行 round10-dev-record next_iteration_targets[0] 方案 (a)「每格多
实例重复读」n=3，用户 2026-09-07 拍板，预注册于 r11-prep-record）；
检验 R10 预注册候选假设（r10-dev-record-candidate-0-i-multi-instance）：

  T1  解析 12 个 reader-raw-r11-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r11-prep-record.json measurement_design 五条预注册聚合口径
      执行（先于盲读冻结）：(1) 实例主记录=六实例各自两板合计
      flag_count/abstain_count/abstain_rate（6 位小数）/非弃权清单/
      逐旗 containment+area_ratio 匹配明细；(2) 视角层=每视角 3 实例
      flag_count/abstain_rate/matches 各中位数+min+max 三分列不取整；
      (3) GT 匹配双口径=union（≥1 实例命中）与 agreement（≥2/3）并列
      +逐 GT 条目 matched_by_count（0..3；召回分母=GT 13 条）；
      (4) 联合门（APR-0011 阈值零改动）=代表配置（每视角 flag_count
      中位数实例；中位不唯一取先序并如实注明 tie）算一轮 joint+
      per-metric 实例间范围+逐实例原始记录三者并列不挑优；(5) bottom
      零旗标分母=按库侧 cal._ratio 先例 None+文字说明不编造。
      双态 compare_v3（声明常量零覆盖；GT 重投影继续用 derivation-log-
      r5 的 frame_box_pct_r5——渲染未变=重投影输入未变）+达标线=
      APR-0011 暂时采纳基线逐项诊断对照（禁改阈值措辞；seed_match_rate
      带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册假设（r10-dev-record-candidate-0-i-multi-instance）裁决：
      字母裁决（唯一正式）判据=r11-prep-record hypothesis_test 原文：
      support=≥1 视角实例间弃权率极差 ≥0.2；reject=全视角 <0.2；全视角
      <0.1 记强 reject 分层。实测 top 极差 0.153846（<0.2）、bottom
      极差 0.0（<0.2）⇒ 字母裁决=reject；强 reject 分层不成立（top
      0.153846≥0.1）⇒ 如实记「reject，未达强 reject」。机制观察单列
      （不凌驾字母裁决）：轮内实例方差实测远小于跨轮摆动（r8→r9→r10
      聚合弃权 0.222222→0.727273→0.285714 vs 本轮轮内视角极差 top
      0.153846/bottom 0.0）——r10 定律修正为「跨轮（实例群/工具代际）
      因素主导，轮内同日采样相对稳定」；本轮假设（轮内实例方差显著）
      字母 reject 恰恰是有信息量的负结果（「正确测出无效同样是有效
      证据」）。示例 c 双向效应新证据：同实例（top i3）对不规则抖动
      按其边界条款报非弃权 reroute（R11T-018/020），而 r10 实例援引
      同一示例走弃权——示例 c 的效果随实例而异，如实记录。
      → calibration-run-r11.json。
  T3  development 域记录（本轮性质=协议侧 v1.1 首轮；R10→R11 方向性
      对照与匹配位置对照（只描述不下能力断言）/假设裁决/联合评价趋势
      （r5→r11）/下一迭代目标——延续引用 gt-audit-r1.json（1f20554a…）
      结论：GT 侧已全部关闭；预注册链=r10-dev-record（da4e85f9…）→
      r11-prep-record（9074df2d…）→run-r11；引用 run-r11 落盘 sha
      单向引用）→ round11-dev-record.json。

通道归因纪律（vs R10；方法照抄 s34/s36/s39/s41/s43 deviation_note
口径）：本轮对 R10 与 R11 均以内嵌输入（reader_flags/gt_entries/
flag_views，run sha 在案）+ compare_v3 同源几何原语（calibration.
_containment/_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）
确定性重放通道分类，并与各态 compare_v3 的 matches∪duplicate_reports
对拍复核。跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是
通道级不是旗级。

读者实例披露（如实入账，不作废）：R11 十二派次全部以 Read 工具直读
内嵌图像（各派次自述内嵌返回、非 URL 转传、无外部视觉 API）；8/12
派次自述对给定 PNG 做 PIL 局部裁剪放大（2-25 处不等；applied-top-i1
第一派次最重：像素颜色分类掩膜+字符化像素图+连通域/包围盒测量；
applied-bottom-i1/i2/i3 与 prep1-bottom-i3 共四派次自述纯直读未做
裁剪/放大——如实按各派次 reading_notes 原文记账）；全部输入仍仅源自
给定 PNG=非盲读违规，但属实例自选工具行为差异；跨轮实例不同+轮内
实例差异=混杂因素照旧声明。输出格式实例披露（编排侧落盘前处理，盘上
件=冻结证据）：applied-bottom i2/i3、prep1-top i1/i2/i3、prep1-bottom
i2/i3 七件经 json.dump indent=1 重序列化（内容逐键忠实；reader 原输出
格式不一：紧凑单行/多行缩进混杂），prep1-bottom-i1 为多行缩进 JSON
Write 原文落盘，其余四件（applied-top-i1/i2/i3、applied-bottom-i1）
为紧凑单行原样落盘；无围栏剥离本先例记录（r7/r10 有）。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r11）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s45_calibration_r11_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-07-r11"
ROUND_LABEL = "r11"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
REL_PREP_R9 = "out/v3-tl2/calibration/r9-prep-record.json"
REL_PREP_R10 = "out/v3-tl2/calibration/r10-prep-record.json"
REL_PREP_R11 = "out/v3-tl2/calibration/r11-prep-record.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DEV_R10 = "out/v3-tl2/calibration/round10-dev-record.json"
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
REL_RUN_R11 = "out/v3-tl2/calibration/calibration-run-r11.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round11-dev-record.json"

#: 12 份盲读原始件（6 实例×2 板；实例内编号跨板连续）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r11-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r11-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r11-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r11-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r11-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r11-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r11-prep1-bottom-i3.txt",
}

#: 六实例=本轮主记录单位（measurement_design item 1）；每实例=同视角
#: 两板（applied+prep1）两派次，实例间编号独立、同实例跨板连续
#: （protocol_amendment.blind_read_execution/naming）。
INSTANCES = {
    "top-i1": {"view": "top",
               "parts": ("applied-top-i1", "prep1-top-i1")},
    "top-i2": {"view": "top",
               "parts": ("applied-top-i2", "prep1-top-i2")},
    "top-i3": {"view": "top",
               "parts": ("applied-top-i3", "prep1-top-i3")},
    "bottom-i1": {"view": "bottom",
                  "parts": ("applied-bottom-i1", "prep1-bottom-i1")},
    "bottom-i2": {"view": "bottom",
                  "parts": ("applied-bottom-i2", "prep1-bottom-i2")},
    "bottom-i3": {"view": "bottom",
                  "parts": ("applied-bottom-i3", "prep1-bottom-i3")},
}
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")

#: R11 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r11-prep-record renders_reuse.png_witness
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R11 复核见证=r11-prep-record
#: renders_reuse.frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r11-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r11-prep-record.json frozen_input_pdfs_check 实测值；
#: guidance-r9 锚=r11-prep-record.json guidance_reuse.sha256_measured
#: 全长（零字节复用）；prep-r11 锚与 r10-dev-record 锚=任务给定先验
#: （盘上实测一致）；其余沿用 s43 在案锚。
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
    REL_PREP_R11:
        "9074df2d9a91175981379c398982e082c72293677e07a848bc4da7c81f5359a0",
    REL_DEV_R8:
        "437e149c3ae4d96653111be968f7d80d86ecbca7f6bb42a31f370ec5af78515d",
    REL_DEV_R9:
        "5ee18d61fc1464a92a6e9bbe46d269245748abb836bc07e535a42cff9aa57c43",
    REL_DEV_R10:
        "da4e85f97d216527aa5fd7027392d79d7935d5a79d200695c6b22510d65d628a",
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
    REL_RUN_R10:
        "622c9099e83198ddb0110300ec6b9be612e21cc19cec7f285966807a6035ef85",
    RAW_FILES["applied-top-i1"]:
        "e9432d3ed7280f5c0e009afe73c23ad62b1d6496d78d454d58e6301360d80615",
    RAW_FILES["prep1-top-i1"]:
        "d3c114bcae45a5ade6a3749c1d7dc7ec9b785b41070a4d2b73ad3d009c059380",
    RAW_FILES["applied-top-i2"]:
        "1046144f27bc2ca23385a287b1f258ce84cddcfbacb781eaa893c36363eb6451",
    RAW_FILES["prep1-top-i2"]:
        "fd93e23d1ff47b467c9b36e51d4876c80a61c19039e7c8301b7043583a8013e0",
    RAW_FILES["applied-top-i3"]:
        "2fdc864697f83709d5a84f9472c8f49e0b163b15c622c0919de12667d5e345ff",
    RAW_FILES["prep1-top-i3"]:
        "cf8052957b3462d4a0dd29e70fe1abf453cd3dbfc8572521d457f730b855c0e0",
    RAW_FILES["applied-bottom-i1"]:
        "242ab86f7e26ce9b8e52475cec50eadb63e6724978957b00b54437311e7b53b3",
    RAW_FILES["prep1-bottom-i1"]:
        "820798d4b40f484210d886b4a89c725d89f9a122f00190ddf9393bca6c04afb5",
    RAW_FILES["applied-bottom-i2"]:
        "6fd7a21cc48f97541ce1faee5ce59a8edaad365c8a373f0f12bb6aa2012e7ddd",
    RAW_FILES["prep1-bottom-i2"]:
        "7b0b4b2180282ef96fa2b79d747ea4ccbcbf61a627a0f192d6220d8956356b9a",
    RAW_FILES["applied-bottom-i3"]:
        "f98bf0c2d13bb6c4b9689d57b1090938986860fd987fa195d74dc514611416e5",
    RAW_FILES["prep1-bottom-i3"]:
        "0282fab7b190ca769c261d65120e2a38ddb29ec4544b7804f31c7d7efebeda6b",
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
    "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
    "prep1-bottom）×每格 3 实例（i1/i2/i3）；两波次串行保序（同一实例"
    "先 applied 后 prep1，flag_id 编号跨板连续、实例间编号独立）；每派次"
    "盲读词只含图像路径+observation-guidance-r9.md（r9 指引零字节复用）"
    "路径+视角前缀与实例 reader_id（机械命名覆盖 R9T/R9B→R11T/R11B、"
    "reader-r9-*→reader-r11-{top,bottom}-i{1,2,3}，per r11-prep-record "
    "guidance_reuse）+起始序号；无任何 GT 坐标/类别提示/期望缺陷描述；"
    "读图者不接触 GT/派生台账/任何校准产物路径；跨实例/跨视角禁止交流"
    "（12 次盲读相互独立——独立性是多实例协议的前提，per r11-prep-record "
    "read_prohibition_note）")

#: 派发模式结构化记录（R11=协议侧 v1.1：每格 3 实例、两波次串行保序）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1（flag_id "
                                    "编号跨板连续；实例间编号独立）",
    "flag_id_continuity": {
        "top-i1": "R11T-001..013（applied 001..006→prep1 007..013）",
        "top-i2": "R11T-001..013（applied 001..005→prep1 006..013）",
        "top-i3": "R11T-001..020（applied 001..012→prep1 013..020）",
        "bottom-i1": "R11B-001..002（applied 0 旗→prep1 001..002）",
        "bottom-i2": "R11B-001..003（applied 001..003→prep1 0 旗）",
        "bottom-i3": "R11B-001..002（applied 001..002→prep1 0 旗）",
    },
    "diff_note": ("R7–R10=两波并行（每格 1 实例）；R11=协议侧 v1.1 单变量"
                  "变更：每视角实例数 1→3（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；唯一变更变量="
                  "协议侧实例数（指引/渲染/GT/阈值零变更）；机械命名覆盖 "
                  "R9T/R9B→R11T/R11B 与 reader-r9-*→reader-r11-{top,"
                  "bottom}-i{1,2,3}（per r11-prep-record guidance_reuse，"
                  "命名属编排侧机械替换、判读实质零变更）+读者实例行为"
                  "差异（8/12 派次自述 PIL 局部裁剪放大、4/12 派次纯 "
                  "Read 直读；输出格式异常披露如实入账，见 "
                  "reader_instance_note，development 域只描述不断言）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R11 十二派次全部以 Read 工具直读"
    "内嵌图像（各派次 reading_notes 自述内嵌图像返回、非 URL 转传、无"
    "外部视觉 API）；8/12 派次自述对给定 PNG 做 PIL 局部裁剪放大（"
    "2-25 处不等：applied-top-i1 第一派次最重——除裁剪放大外另做像素"
    "颜色分类掩膜+字符化像素图+连通域/包围盒测量；prep1-top-i1 约 20 "
    "处、applied-top-i2 约 15 处、prep1-top-i2 14 处 2.5x-5x、"
    "applied-top-i3 约 20 处 4x/8x、prep1-top-i3 25 处 3-7x、"
    "prep1-bottom-i1 2 处 3x/4x、prep1-bottom-i2 多个局部+numpy 颜色"
    "统计），4/12 派次自述纯 Read 直读未做裁剪/放大（applied-bottom-"
    "i1/i2/i3、prep1-bottom-i3，reading_notes 原文自述在案）；全部判读"
    "输入仍严格限于（指引+该 PNG），裁剪/放大/掩膜/连通域枚举全部派生"
    "自给定 PNG、零外部信息、零 GT/零其他文件接触=非盲读违规，但属实例"
    "自选工具行为差异；跨轮实例不同+轮内实例差异=混杂因素照旧声明"
    "（本轮每视角 n=3 给出轮内实例间范围，轮内样本仍小、development 域"
    "只描述不断言）。输出格式实例披露（编排侧落盘前处理，盘上件=冻结"
    "证据）：applied-bottom i2/i3、prep1-top i1/i2/i3、prep1-bottom "
    "i2/i3 七件经 json.dump indent=1 重序列化（内容逐键忠实；reader 原"
    "输出格式不一：紧凑单行/多行缩进混杂），prep1-bottom-i1 为多行缩进 "
    "JSON Write 原文落盘，其余四件（applied-top-i1/i2/i3、applied-"
    "bottom-i1）为紧凑单行原样落盘；无围栏剥离本先例记录（r7/r10 有"
    "围栏剥离先例，本轮零围栏剥离）；12 件 parse 校验全部通过、均非"
    "盲读违规")

#: 逐文件原始消息格式异常（如实入账；盘上件=编排侧落盘后的冻结证据，
#: parse 均为 direct JSON 解析、零 repair）。
_COMPACT_NOTE = "原始消息即紧凑单行 JSON，原样落盘（无格式异常）"
_RESERIALIZED_NOTE = ("原始消息格式不一，编排侧经 json.dump indent=1 "
                      "重序列化落盘（内容逐键忠实；parse 校验通过；非盲读"
                      "违规）")
RAW_MESSAGE_FORMAT_NOTES = {
    "applied-top-i1": _COMPACT_NOTE,
    "applied-top-i2": _COMPACT_NOTE,
    "applied-top-i3": _COMPACT_NOTE,
    "applied-bottom-i1": _COMPACT_NOTE,
    "applied-bottom-i2": _RESERIALIZED_NOTE,
    "applied-bottom-i3": _RESERIALIZED_NOTE,
    "prep1-top-i1": _RESERIALIZED_NOTE,
    "prep1-top-i2": _RESERIALIZED_NOTE,
    "prep1-top-i3": _RESERIALIZED_NOTE,
    "prep1-bottom-i1": ("原始消息为多行缩进 JSON，Write 原文落盘（parse "
                        "校验通过；非盲读违规）"),
    "prep1-bottom-i2": _RESERIALIZED_NOTE,
    "prep1-bottom-i3": _RESERIALIZED_NOTE,
}

GUIDANCE_REUSE_NOTE = (
    "本轮零指引变更：observation-guidance-r9.md 零字节复用（本轮唯一"
    "判读依据，r9 指引落盘即冻结；本轮零指引作者动作、零文本变更、无新"
    "指引文件；锚 a0c10154…）；唯一例外=机械命名覆盖（r11-prep-record "
    "guidance_reuse.mechanical_naming_override）：指引 §6 的 flag_id "
    "前缀 R9T/R9B→R11T/R11B 与 reader_id reader-r9-*→reader-r11-{top,"
    "bottom}-i{1,2,3}（命名属编排侧机械替换，非判据变更；判读实质判据"
    "零变更；实例间编号独立、同实例跨板连续），由派发指令给出；§3A "
    "示例 c 措辞修改已排程 R12（用户 2026-09-07 拍板），本轮零指引变更")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 11 轮迭代"
    "（development 域协议侧单变量变更轮：v1.1 追加式修订只改盲读执行"
    "与聚合口径，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "协议侧单变量变更轮（唯一变更变量=每视角独立 reader 实例数 1→3，"
    "evaluation-protocol-v1→v1.1 追加式修订；指引 r9 零字节复用+R5 "
    "冻结渲染复用+GT/阈值零变更；判读实质判据的变更变量恰零个）")

#: 预注册描述性边界（measurement_design/attribution_plan：0.2/0.1 只
#: 用于本轮假设检验方向归因，与 APR-0011 门分列，非阈值常量改动）。
BOUNDARY_SUPPORT = 0.2
BOUNDARY_STRONG_REJECT = 0.1

BOTTOM_ZERO_PART_NOTE = (
    "bottom 三格零旗标（bottom-i1×applied、bottom-i2×prep1、bottom-i3×"
    "prep1，均 0 旗）：分母为零、弃权率无定义，按库侧 cal._ratio 先例 "
    "（pcbflow/calibration.py _ratio：零分母→None）如实为 None（绝不"
    "编造数值；measurement_design item 5 预注册口径；r10 run-record "
    "bottom=0/0→None 同口径在案）；实例层（两板合计）六实例全部 ≥1 旗"
    "=实例级弃权率全部有定义（bottom 三实例=1.0）")


def _fail(msg: str) -> None:
    print(f"[s45-cal-r11] FAIL: {msg}")
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

    R11 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                 gt_rel: str, gt_sha: str, raw_key: str,
                 parsed: dict, gt_entries: list) -> dict:
    """单实例单态块：内嵌 reader_flags/gt_entries/flag_views+compare_v3。"""
    flags = []
    flag_views = {}
    for img in parsed[raw_key]["images"]:
        for f in img["flags"]:
            flags.append(f)
            flag_views[f["flag_id"]] = img["view"]
    report = cal.compare_v3(flags, gt_entries, flag_views=flag_views)
    if report["containment_min"] != cal.CONTAINMENT_MIN \
            or report["area_ratio_max"] != cal.AREA_RATIO_MAX:
        _fail("compare_v3 阈值与声明常量不符")
    # 零旗标格（bottom 三格）无可覆盖旗标：库侧 view_check=not_applicable
    # （不冒充已检查）；有旗格必须 full。
    want_view = "full" if flags else "not_applicable"
    if report["view_check"] != want_view:
        _fail(f"{raw_key} view_check 应为 {want_view}（实测 "
              f"{report['view_check']}）")
    return {
        "state": state_desc,
        "source_board": {"path_rel": board_rel, "sha256": board_sha},
        "framing": {"path_rel": REL_FRAMING_R5, "sha256": _sha(REL_FRAMING_R5),
                    "note": ("R11 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮协议侧单变量轮：唯一变更"
                             "变量=每视角实例数 1→3）")},
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


def build_flag_gt_detail(flags: list, flag_views: dict, gt_entries: list,
                         report: dict, state: str) -> list:
    """逐旗 GT 重叠明细（measurement_design item 1；纯函数）。"""
    matched_by_flag = {m["flag_id"]: m for m in report["matches"]}
    abst = set(report["abstain"]["abstain_ids"])
    rows = []
    for f in flags:
        fid = f["flag_id"]
        if fid in abst:
            rows.append({"flag_id": fid, "state": state, "abstain": True,
                         "category": f["category"],
                         "gt_overlaps": [], "containment_all_none": None,
                         "matched": False, "matched_gt_id": None,
                         "note": "弃权旗不参与匹配（abstain 单列）"})
            continue
        overlaps = []
        none_cnt = 0
        for e in gt_entries:
            c = cal._containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None:
                none_cnt += 1
                continue
            ar = cal._area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            fv = flag_views.get(fid)
            if fv is not None and fv != e["side"]:
                channel = "view_gate"
            elif ar is None or ar > cal.AREA_RATIO_MAX:
                channel = "area_ratio_rejected"
            elif e["category"] != f["category"]:
                channel = "category_mismatch"
            else:
                channel = "candidate"
            overlaps.append({
                "gt_id": e["gt_id"], "gt_category": e["category"],
                "containment": cal._round6(c),
                "area_ratio": (cal._round6(ar) if ar is not None else None),
                "channel": channel})
        overlaps.sort(key=lambda x: x["gt_id"])
        m = matched_by_flag.get(fid)
        rows.append({"flag_id": fid, "state": state, "abstain": False,
                     "category": f["category"], "gt_overlaps": overlaps,
                     "containment_all_none": none_cnt == len(gt_entries),
                     "matched": bool(m),
                     "matched_gt_id": (m["gt_id"] if m else None)})
    rows.sort(key=lambda r: r["flag_id"])
    return rows


def build_instance_record(name: str, spec: dict, parsed: dict,
                          gt_applied: list, gt_prep1: list) -> dict:
    """实例主记录（measurement_design item 1；两板合计口径）。"""
    view = spec["view"]
    blk_appl = _state_block(
        "applied", "ASM-7 终检后终态", "out/revc-asm/board/applied.kicad_pcb",
        APPLIED_SHA_FROZEN, REL_GT_V2, _sha(REL_GT_V2),
        spec["parts"][0], parsed, gt_applied)
    blk_prep = _state_block(
        "prep1", "ASM-P1 批前快照（种子域）",
        "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb", PREP1_SHA_FROZEN,
        REL_GT_V1, _sha(REL_GT_V1), spec["parts"][1], parsed, gt_prep1)
    n_fl = (len(blk_appl["reader_flags"]) +
            len(blk_prep["reader_flags"]))
    n_ab = (blk_appl["compare_v3"]["abstain"]["abstain_count"] +
            blk_prep["compare_v3"]["abstain"]["abstain_count"])
    n_sc = (blk_appl["compare_v3"]["reader_scored_count"] +
            blk_prep["compare_v3"]["reader_scored_count"])
    matches_detail = []
    gt_matched_ids = []
    for st, blk in (("applied", blk_appl), ("prep1", blk_prep)):
        for m in blk["compare_v3"]["matches"]:
            matches_detail.append(dict(
                m, state=st,
                containment=cal._round6(m["containment"]),
                area_ratio=cal._round6(m["area_ratio"])))
            gt_matched_ids.append(m["gt_id"])
    matches_detail.sort(key=lambda m: (m["state"], m["flag_id"]))
    abstain_ids = sorted(
        blk_appl["compare_v3"]["abstain"]["abstain_ids"] +
        blk_prep["compare_v3"]["abstain"]["abstain_ids"])
    non_abstain_ids = sorted(
        [f["flag_id"] for f in blk_appl["reader_flags"]] +
        [f["flag_id"] for f in blk_prep["reader_flags"]])
    non_abstain_ids = [i for i in non_abstain_ids if i not in set(abstain_ids)]
    per_flag_detail = (
        build_flag_gt_detail(blk_appl["reader_flags"],
                             blk_appl["flag_views"], gt_applied,
                             blk_appl["compare_v3"], "applied")
        + build_flag_gt_detail(blk_prep["reader_flags"],
                               blk_prep["flag_views"], gt_prep1,
                               blk_prep["compare_v3"], "prep1"))
    per_flag_detail.sort(key=lambda r: r["flag_id"])
    return {
        "instance": name, "view": view,
        "reader_id": parsed[spec["parts"][0]]["reader_id"],
        "parts": {"applied": spec["parts"][0], "prep1": spec["parts"][1]},
        "states": {"applied": blk_appl, "prep1": blk_prep},
        "combined": {
            "flag_count": n_fl,
            "abstain_count": n_ab,
            "scored": n_sc,
            "abstain_rate": cal._ratio(n_ab, n_fl),
            "abstain_rate_arithmetic": f"abstain_rate = {n_ab}/{n_fl}"
                                       f" = {cal._ratio(n_ab, n_fl)}"
                                       "（分母=该实例该视角全部旗标，跨"
                                       "两板合计；measurement_design "
                                       "item 1）",
            "matches_total": len(matches_detail),
            "matches_detail": matches_detail,
            "gt_matched_union": len(set(gt_matched_ids)),
            "gt_recall_union": cal._ratio(len(set(gt_matched_ids)), 13),
            "seed_match_rate": cal._ratio(len(matches_detail), n_sc),
            "abstain_ids": abstain_ids,
            "non_abstain_flag_ids": non_abstain_ids,
        },
        "per_flag_gt_detail": per_flag_detail,
    }


def _median3(vals: list):
    """恰 3 值的中位数（排序后取第 2；measurement_design item 2：
    中位数+最小值+最大值三分列、不取整）。"""
    if len(vals) != 3:
        _fail(f"median3 需恰 3 值: {vals}")
    return sorted(vals)[1]


def build_view_layer(instances: dict) -> dict:
    """视角层聚合（measurement_design item 2；每视角 3 实例三分列）。"""
    out = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        fc = {n: instances[n]["combined"]["flag_count"] for n in names}
        ar = {n: instances[n]["combined"]["abstain_rate"] for n in names}
        mt = {n: instances[n]["combined"]["matches_total"] for n in names}
        fc_vals = [fc[n] for n in names]
        ar_vals = [ar[n] for n in names]
        mt_vals = [mt[n] for n in names]
        out[view] = {
            "instances": names,
            "flag_count": {"by_instance": fc,
                           "median": _median3(fc_vals),
                           "min": min(fc_vals), "max": max(fc_vals)},
            "abstain_rate": {"by_instance": ar,
                             "median": _median3(ar_vals),
                             "min": min(ar_vals), "max": max(ar_vals)},
            "matches": {"by_instance": mt,
                        "median": _median3(mt_vals),
                        "min": min(mt_vals), "max": max(mt_vals)},
            "abstain_rate_range": cal._round6(max(ar_vals) - min(ar_vals)),
            "abstain_rate_range_arithmetic":
                f"实例间弃权率极差（max−min）= {max(ar_vals)} − "
                f"{min(ar_vals)} = {cal._round6(max(ar_vals) - min(ar_vals))}"
                f"（{names[0]}/{names[1]}/{names[2]} = "
                f"{ar_vals[0]}/{ar_vals[1]}/{ar_vals[2]}）",
        }
    return out


def build_gt_dual(instances: dict, gt_applied: list, gt_prep1: list) -> dict:
    """GT 匹配聚合双口径（measurement_design item 3）。

    逐 GT 条目 matched_by_count（0..3）=同视角 3 实例中命中该条目的
    实例数（命中判定=该实例对应态 compare_v3 的 matches 含该 gt_id，
    即逐旗 containment/area_ratio 过门+一对一指派后在 GT 条目上归并）；
    union（≥1 实例命中即计）与 agreement（≥2/3 实例命中才计）两口径
    并列；召回分母=GT 13 条。
    """
    state_of_gt = {}
    ordered = []
    for e in gt_applied:
        state_of_gt[e["gt_id"]] = "applied"
        ordered.append(e)
    for e in gt_prep1:
        state_of_gt[e["gt_id"]] = "prep1"
        ordered.append(e)
    per_gt = []
    for e in ordered:
        gid = e["gt_id"]
        st = state_of_gt[gid]
        hits = []
        for n in INSTANCE_ORDER:
            if instances[n]["view"] != e["side"]:
                continue
            for m in instances[n]["combined"]["matches_detail"]:
                if m["gt_id"] == gid:
                    hits.append({"instance": n, "flag_id": m["flag_id"],
                                 "state": m["state"],
                                 "containment": m["containment"],
                                 "area_ratio": m["area_ratio"]})
        hits.sort(key=lambda h: h["instance"])
        per_gt.append({
            "gt_id": gid, "category": e["category"], "side": e["side"],
            "state": st,
            "gt_role": ("gt_expansion（applied 态）" if st == "applied"
                        else "gt_seed（prep1 态）"),
            "matched_by_count": len(hits),
            "hits": hits})
    union_ids = [g["gt_id"] for g in per_gt if g["matched_by_count"] >= 1]
    agreement_ids = [g["gt_id"] for g in per_gt if g["matched_by_count"] >= 2]
    return {
        "denominator": 13,
        "denominator_note": "召回分母=GT 13 条（applied 9+prep1 4）",
        "hit_rule": ("命中判定=每实例逐旗 containment/area_ratio 过门"
                     "（CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明常量"
                     "零改动）+一对一指派后在 GT 条目上归并；top 视角=3 "
                     "实例、bottom 视角=3 实例"),
        "union": {"rule": "≥1 实例命中即计", "gt_ids": union_ids,
                  "count": len(union_ids),
                  "gt_recall_union": cal._ratio(len(union_ids), 13)},
        "agreement": {"rule": "≥2/3 实例命中才计", "gt_ids": agreement_ids,
                      "count": len(agreement_ids),
                      "gt_recall_agreement": cal._ratio(
                          len(agreement_ids), 13)},
        "per_gt": per_gt,
    }


def pick_representative(instances: dict) -> dict:
    """代表配置选取（measurement_design item 4：每视角 flag_count
    中位数实例；中位不唯一取先序并如实注明 tie）。"""
    sel = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        counts = {n: instances[n]["combined"]["flag_count"] for n in names}
        med = _median3(list(counts.values()))
        tied = [n for n in names if counts[n] == med]
        sel[view] = {
            "selected": tied[0],
            "median_flag_count": med,
            "tie": len(tied) > 1,
            "tie_note": ("flag_count 中位 %d 不唯一（%s 同为 %d）→按先序"
                         "取 %s，如实注明 tie（measurement_design item 4 "
                         "无挑优语义；不预设、不挑优）"
                         % (med, "/".join(tied), med, tied[0]))
            if len(tied) > 1 else "中位实例唯一（%s）" % tied[0],
            "flag_count_by_instance": counts,
        }
    return {
        "rule": ("measurement_design item 4（预注册）：代表配置=每视角取 "
                 "flag_count 中位数实例组成代表配置，计算一轮 joint 结果"),
        "selection": sel,
        "members": {"top": sel["top"]["selected"],
                    "bottom": sel["bottom"]["selected"]},
    }


def _merge_state_blocks(blocks: list, state: str, state_desc: str,
                        gt_entries: list) -> dict:
    """代表配置合并态块（同态两实例旗标拼接；视角注入合并）。"""
    flags = []
    flag_views = {}
    for blk in blocks:
        flags.extend(blk["reader_flags"])
        flag_views.update(blk["flag_views"])
    report = cal.compare_v3(flags, gt_entries, flag_views=flag_views)
    if report["view_check"] != "full":
        _fail(f"代表配置 {state} 态 view_check 应为 full")
    return {
        "state": state_desc,
        "members": [b["members_note"] for b in blocks],
        "gt_file": blocks[0]["gt_file"],
        "gt_reprojection": blocks[0]["gt_reprojection"],
        "gt_entries": gt_entries,
        "reader_flags": flags,
        "flag_views": flag_views,
        "view_check": report["view_check"],
        "compare_v3": report,
    }


def _aggregate(prep: dict, appl: dict) -> dict:
    """两态联合聚合（照 s43 口径；此处置于代表配置）。"""
    p, a = prep["compare_v3"], appl["compare_v3"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    cells: dict = {v: {"abstain_count": 0, "flag_count": 0}
                   for v in ("top", "bottom")}
    for blk in (prep, appl):
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            cell = cells[view]
            cell["flag_count"] += 1
            if fid in abst:
                cell["abstain_count"] += 1
    by_view = {}
    for view, cell in cells.items():
        cell["rate"] = cal._ratio(cell["abstain_count"], cell["flag_count"])
        cell["fraction"] = f"{cell['abstain_count']}/{cell['flag_count']}"
        by_view[view] = dict(cell)
    return {
        "scope": ("代表配置两态联合（measurement_design item 4 预注册："
                  "代表配置=每视角 flag_count 中位数实例；与 per-metric "
                  "实例间范围、逐实例原始记录三者并列如实呈现，不合并、"
                  "不挑优）"),
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
        },
        "abstain_rate_by_view_arithmetic":
            f"abstain_rate_by_view: top = {by_view['top']['fraction']} = "
            f"{by_view['top']['rate']}；bottom = "
            f"{by_view['bottom']['fraction']} = "
            f"{by_view['bottom']['rate']}",
        "abstain_rate_definition": cal.ABSTAIN_RATE_DEFINITION,
        "seed_metric_note": cal.SEED_METRIC_NOTE,
    }


def build_metric_ranges(instances: dict) -> dict:
    """per-metric 实例间范围（measurement_design item 4 三并列之二）。"""
    out = {}
    for view in ("top", "bottom"):
        names = [n for n in INSTANCE_ORDER
                 if instances[n]["view"] == view]
        comb = [instances[n]["combined"] for n in names]
        out[view] = {
            "instances": names,
            "flag_count": {"min": min(c["flag_count"] for c in comb),
                           "max": max(c["flag_count"] for c in comb)},
            "abstain_count": {"min": min(c["abstain_count"] for c in comb),
                              "max": max(c["abstain_count"] for c in comb)},
            "abstain_rate": {"min": min(c["abstain_rate"] for c in comb),
                             "max": max(c["abstain_rate"] for c in comb)},
            "matches_total": {"min": min(c["matches_total"] for c in comb),
                              "max": max(c["matches_total"] for c in comb)},
            "gt_matched_union": {"min": min(c["gt_matched_union"]
                                            for c in comb),
                                 "max": max(c["gt_matched_union"]
                                            for c in comb)},
            "scored": {"min": min(c["scored"] for c in comb),
                       "max": max(c["scored"] for c in comb)},
        }
    return out


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
                 f"{agg['gt_count_total']}（代表配置口径）"},
        {"id": "seed_match_rate_ge_0.5", "threshold": 0.5,
         "actual": agg["seed_match_rate_total"],
         "met": agg["seed_match_rate_total"] >= 0.5,
         "note": f"seed_match_rate_total={agg['matches_total']}/"
                 f"{agg['scored_total']}（诊断值，禁称 precision/FPR）"},
        {"id": "abstain_rate_le_0.5", "threshold": 0.5,
         "actual": agg["abstain_rate_total"],
         "met": agg["abstain_rate_total"] <= 0.5,
         "note": f"abstain_rate_total={agg['abstain_count_total']}/"
                 f"{agg['flag_count_total']}（单位=旗标条数；分母=代表"
                 "配置全部旗标）；APR-0011 阈值零改动，与预注册描述性"
                 "边界 0.2/0.1 各自独立计算、互不凌驾"},
    ]


def _compliance(agg: dict) -> dict:
    criteria = _criteria(agg)
    all_met = all(c["met"] for c in criteria)
    return {
        "baseline": "APR-0011（provisional_supersedable；"
                    "evaluation-protocol-v1 §3 联合评价；阈值零改动）",
        "scope_note": ("本轮联合评价按 measurement_design item 4 以代表"
                       "配置计算；与 per-metric 实例间范围、逐实例原始"
                       "记录三者并列如实呈现，不合并、不挑优"),
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
                       "r9": "not_met（在案）", "r10": "not_met（在案）",
                       "r11": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": ("本轮联合评价未达标（代表配置 gt_recall 0.076923 与 "
                     "seed_match_rate 0.076923 两项未达暂行线；abstain_"
                     "rate 0.133333≤0.5 与 gt_count 达线），连续计数仍"
                     "为 0" if not all_met
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
# 逐旗失败通道归因（vs R10；方法照抄 s34/s36/s39/s41/s43：通道级，非旗级）
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
            "area_ratio", "state", "instance")
    return {k: e[k] for k in keep if k in e}


def reroute_production_blocks(blocks: list) -> int:
    """reroute 类旗标产量（弃权+非弃权合计，全视角；纯函数）。

    入参=态块列表（实例态块或 run_doc 态块值均可）。
    """
    n = 0
    for blk in blocks:
        for f in blk["reader_flags"]:
            if f["category"] == "suspicious_reroute":
                n += 1
    return n


def reroute_production(states: dict) -> int:
    """reroute 类旗标产量（states 映射版；兼容 run_doc["states"]）。"""
    return reroute_production_blocks(list(states.values()))


def build_channel_attribution(run_r6: dict, run_r7: dict, run_r8: dict,
                              run_r9: dict, run_r10: dict,
                              inst_blocks: list, inst_replays: dict) -> dict:
    """通道归因小节（vs R10；通道级分组，非旗级配对；链自 r6 衔接）。"""
    r10_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r10["states"][st]
        r10_replays[st] = channel_replay(blk["reader_flags"],
                                         blk["flag_views"],
                                         blk["gt_entries"])
        if not replay_matches_agree(r10_replays[st], blk["compare_v3"]):
            _fail(f"R10 {st} 态通道重放与 compare_v3 对拍不一致")
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R11 {key} 通道重放与 compare_v3 对拍不一致")

    def pick_r11(failure):
        rows = []
        for blk in inst_blocks:
            rp = inst_replays[blk["_part_key"]]
            for e in rp["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=blk["_state"],
                                                    instance=blk[
                                                        "_instance"])))
        rows.sort(key=lambda x: (x["instance"], x["state"], x["flag_id"],
                                 x["gt_id"]))
        return rows

    def pick_r10(failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in r10_replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r10 = pick_r10("area_ratio_rejected")
    geo_r11 = pick_r11("area_ratio_rejected")
    cat_r10 = pick_r10("category_mismatch")
    cat_r11 = pick_r11("category_mismatch")
    view_r10 = pick_r10("view_gate")
    view_r11 = pick_r11("view_gate")

    geo_change = (
        "几何门通道（R10→R11）：面积比出局条目 0→0（两轮均空；无回升，"
        "guard 通道要求满足）——r11 非弃权旗 41 条中与同态 GT 近邻的旗标"
        "全部双条件通过或类别出局，未出现面积比出局；§3 收窄判据守门无"
        "回升（R7 起连续为空）。")
    if len(cat_r11) != 1 or cat_r11[0]["flag_id"] != "R11T-012" \
            or cat_r11[0]["gt_id"] != "GT-REVC-AP-8-R1Q2":
        _fail("类别门 R11 生效条目与声明不符（应为恰 1 条 R11T-012↔AP-8）")
    cat_change = (
        "类别门通道（R10→R11）：类别不符出局条目 0→1（R11T-012，"
        "applied-top-i3，silk_readability↔GT-REVC-AP-8-R1Q2，containment "
        f"{cat_r11[0]['containment']}、面积比 {cat_r11[0]['area_ratio']}"
        "——近邻双几何条件通过但类别不符）；多"
        "实例协议下类别门首次出现生效实例；样本量极小，只描述不断言。")

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
            "r9": _gate_count(run_r9, 9, "channel_1_geometry_gate"),
            "r10": len(geo_r10),
            "r11": len(geo_r11),
        },
        "category_gate_category_mismatch_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_2_category_gate"),
            "r7": _gate_count(run_r7, 7, "channel_2_category_gate"),
            "r8": _gate_count(run_r8, 8, "channel_2_category_gate"),
            "r9": _gate_count(run_r9, 9, "channel_2_category_gate"),
            "r10": len(cat_r10),
            "r11": len(cat_r11),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0；类别门 "
                 "r6=1→r7=0→r8=1→r9=0→r10=0→r11=1（R11T-012 类别不符）；"
                 "多实例（41 非弃权旗 vs r10 的 10 条）下类别门再现生效"
                 "实例"),
    }
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R11, "sha256": _sha(REL_PREP_R11)},
            "declaration": (
                "本轮恰一个协议侧操纵变量（每视角独立实例数 1→3）、检验"
                "恰一个假设（round10-dev-record next_iteration_targets[0] "
                "方案 (a)）；轮后按每视角实例间弃权率极差相对预注册描述性"
                "边界 0.2/0.1 的方向归因（r11-prep-record.json "
                "attribution_plan.declaration 原文）"),
            "primary_channel": {
                "change_id": "per-view-instance-count-1-to-3",
                "metric": ("实例间弃权率极差（每视角分列；预注册描述性"
                           "边界：任一视角 ≥0.2 支持、全部视角 <0.2 拒绝、"
                           "全部视角 <0.1 强 reject 分层标注）；实例间"
                           "旗标产量极差与 GT 匹配双口径附录"),
            },
            "guard_channel": {
                "metric": "其余类别非弃权旗 frame_box_pct 几何门（面积比"
                          "出局条目）",
                "requirement": ("§3 收窄判据零变更（指引零字节复用），非"
                                "弃权框仍须满足；几何门面积比出局条目无"
                                "回升"),
            },
        },
        "method": {
            "source_of_r10_detail": (
                "calibration-run-r10.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43 deviation_note 口径：本轮"
                "对 R10 与 R11 均以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5（含 None=无交集）"
                "无条目；近邻且视角不符=view_gate；近邻且面积比>上限="
                "area_ratio_rejected（几何门）；近邻且面积比≤上限且类别"
                "不符=category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r10_prep1_candidate_pairs":
                    r10_replays["prep1"]["candidate_pairs"],
                "r10_applied_candidate_pairs":
                    r10_replays["applied"]["candidate_pairs"],
                "r11_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R10 prep1 恰 1 对且"
                         "恰为 matches、applied=0；R11 十二件重放全部复现"
                         "：候选对=各实例 matches）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R10T/R10B 与 R11T/R11B 来自"
            "不同 reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r10_area_ratio_rejected_entries": geo_r10,
            "r11_area_ratio_rejected_entries": geo_r11,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r10_category_mismatch_entries": cat_r10,
            "r11_category_mismatch_entries": cat_r11,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r10_entries": view_r10,
            "r11_entries": view_r11,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮重放"
                     "均无视角门条目——R11 bottom 7 旗全部弃权（零非弃权 "
                     "bottom 旗）、top 旗与同态 GT（13 条全部 side=top）"
                     "视角相符；bottom 零非弃权旗⇒bottom matches=0。"),
        },
        "gate_chain_since_r6": chain,
        "r11_specific_observations": [
            "R11 六实例 53 旗标（非弃权 41、弃权 12）中，matches（逐实例"
            "逐态 compare_v3）合计 4 条：top-i1 R11T-009↔GT-REVC-P1-R4J3"
            "（containment 0.723377、面积比 0.734272，prep1 态——与 r8 "
            "R8T-004、r10 R10T-011 同域）、top-i2 R11T-012↔GT-REVC-P1-"
            "L1SHORT（containment 1.0、面积比 1.756578，prep1 态，"
            "other_advisory=铜短路按缺陷性质诚实映射类）、top-i3 R11T-010"
            "↔GT-REVC-AP-1-R5U6（containment 0.927745、面积比 1.75184，"
            "applied 态）与 R11T-003↔GT-REVC-AP-6-R2LED2（containment "
            "0.689959、面积比 1.10596，applied 态）；bottom 三实例零非"
            "弃权旗=零匹配。GT 条目层 union=4/13（0.307692）、agreement="
            "0/13（0.0）——四条命中各由恰一个实例贡献（matched_by_count "
            "全部=1），无一 GT 条目被 ≥2 实例同时命中。",
            "R11 suspicious_reroute 旗标 3 条全部出自 top-i3（R11T-006 "
            "弃权+R11T-018/020 非弃权）；逐实例产量 0/0/3（i3：1 弃权+"
            "2 非弃权）；r8=1→r9=0→r10=2→r11=3；示例 c "
            "双向效应新证据见 hypothesis_test.mechanism_observation。",
            "R11 类别门 1 条（R11T-012↔AP-8）为 r10（0 条）后首次生效"
            "实例；几何门连续第 5 轮为空；视角门两轮均空。",
            "courtyard 被动追踪（prep-record 预注册）：非弃权 courtyard "
            "旗 14 条中 3 条命中（top-i1 R11T-009↔R4J3、top-i3 R11T-010"
            "↔AP-1-R5U6/R11T-003↔AP-6-R2LED2，全部与 r8/r10 命中同域="
            "Y1/R4J3 类 courtyard 密集区）；bottom courtyard 3 条全部"
            "弃权（R11B-003、R11B-001/002）；GT/阈值零改动、零期望"
            "（run-r11 courtyard_tracking 节）。",
        ],
    }


# ---------------------------------------------------------------------------
# 预注册假设（r10-dev-record-candidate-0-i-multi-instance）裁决
# （字母裁决+强 reject 分层+机制观察单列）
# ---------------------------------------------------------------------------

#: 示例 c 双向效应证据（摘录必须逐字来自对应 reader-raw 原文；
#: substring 校验=防转述失真）。
EXAMPLE_C_EVIDENCE = [
    {"source": "prep1-top-i3", "kind": "reading_notes", "flag_id": None,
     "excerpt": ("两处连线不规则抖动段按 r9 示例 c 的界限（形态不规则、"
                 "无规律的绕行仍按关注现象处理）报告为 suspicious_reroute"
                 "。")},
    {"source": "prep1-top-i3", "kind": "location_evidence",
     "flag_id": "R11T-018",
     "excerpt": "该形态不规则、无规律，按关注现象报告。"},
    {"source": "prep1-top-i3", "kind": "location_evidence",
     "flag_id": "R11T-020",
     "excerpt": "该形态不规则、无规律，按关注现象报告。"},
    {"source": "applied-top-i3", "kind": "location_evidence",
     "flag_id": "R11T-006",
     "excerpt": ("形态规整但不呈规则周期折叠，按存在性一般判据推理后仍"
                 "无法负责任确认其为设计意图（如等长/保护类走线的候选"
                 "解释）还是可疑改道，故弃权。")},
]

#: 工具行为证据（PIL vs 纯直读；逐字摘录）。
TOOL_BEHAVIOR_EVIDENCE = [
    {"source": "applied-top-i1", "kind": "reading_notes",
     "excerpt": "像素颜色分类掩膜"},
    {"source": "prep1-bottom-i1", "kind": "reading_notes",
     "excerpt": "用 Python/PIL 仅从该 PNG 派生两处放大裁剪"},
    {"source": "applied-bottom-i1", "kind": "reading_notes",
     "excerpt": "未做裁剪/放大或任何其他视觉处理"},
    {"source": "applied-bottom-i2", "kind": "reading_notes",
     "excerpt": "未做任何裁剪、放大或其他视觉辅助操作"},
    {"source": "applied-bottom-i3", "kind": "reading_notes",
     "excerpt": "未做裁剪、放大或任何其他视觉处理"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "excerpt": "未做裁剪、放大或其他图像操作"},
]

#: bottom 零旗标「正常特征→不报告」通道使用证据（逐字摘录）。
BOTTOM_ZERO_EVIDENCE = [
    {"source": "applied-bottom-i1", "kind": "reading_notes",
     "excerpt": "因此本轮 flags 为空：此为零报告而非跳读"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "excerpt": "最终零 flag"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "excerpt": "综上，本图无可负责任定位并归入六类封闭集的关注现象，"
                "flags 为空"},
]


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          instances: dict, view_layer: dict,
                          attribution: dict, raw_texts: dict,
                          parsed_notes: dict) -> dict:
    """假设（r10-dev-record-candidate-0-i-multi-instance）裁决节（预注册
    判据执行；字母裁决唯一正式+强 reject 分层+机制观察单列）。

    字母裁决（唯一正式裁决）=判据 r11-prep-record.json hypothesis_test
    原文：support=「≥1 个视角的实例间弃权率极差（max−min）≥0.2」；
    reject=「全部视角实例间弃权率极差 <0.2」；补充分层=「全视角极差
    <0.1 记『强 reject』并如实标注」。实测 top 极差 0.153846（<0.2）、
    bottom 极差 0.0（<0.2）⇒ 字母裁决=reject；top 0.153846≥0.1 ⇒ 强
    reject 分层不成立 ⇒ 如实记「reject，未达强 reject」。0.2/0.1 为
    本轮预注册描述性边界，与 APR-0011 门各自独立计算、互不凌驾、
    run-record 内分开表述。机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R11)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    # 基线数字与 prep-record 登记交叉核对（fail-closed）
    rounds = ht["baseline_reference"]["rounds"]
    if rounds["r10"] != run_r10["aggregation"]["abstain_rate_total"]:
        _fail("prep-record r10 弃权率基线与 run-r10 实测不符")
    if rounds["r9"] != run_r9["aggregation"]["abstain_rate_total"]:
        _fail("prep-record r9 弃权率基线与 run-r9 实测不符")
    if rounds["r8"] != run_r8["aggregation"]["abstain_rate_total"]:
        _fail("prep-record r8 弃权率基线与 run-r8 实测不符")
    rate_r8 = run_r8["aggregation"]["abstain_rate_total"]
    rate_r9 = run_r9["aggregation"]["abstain_rate_total"]
    rate_r10 = run_r10["aggregation"]["abstain_rate_total"]
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    supported = (top_range >= BOUNDARY_SUPPORT
                 or bottom_range >= BOUNDARY_SUPPORT)
    strong_reject = (top_range < BOUNDARY_STRONG_REJECT
                     and bottom_range < BOUNDARY_STRONG_REJECT)
    verdict = "supported" if supported else "reject"
    verdict_text = (
        "按预注册判据（r11-prep-record.json hypothesis_test 原文）=拒绝"
        "（字母口径，唯一正式裁决）：全部视角实例间弃权率极差 <0.2（top "
        f"{top_range}={max(top_rates.values())}−{min(top_rates.values())}"
        "、bottom " f"{bottom_range}={max(bottom_rates.values())}−"
        f"{min(bottom_rates.values())}）——同日同指引（r9 指引零字节复用）"
        "同渲染（R5 冻结件复用）下轮内实例方差未达 0.2 描述性边界，"
        "「r10 观测到的摆动主要由实例级因素贡献」未获支持、r10 跨轮摆动"
        "主要归于跨轮因素（如工具行为代际漂移）而非轮内实例采样，n=1 "
        "稳定性优于预判（方向性结论，见 mechanism_observation 单列）。"
        "强 reject 分层不成立：top 极差 0.153846≥0.1（非全视角 <0.1）"
        "⇒ 如实记「reject，未达强 reject」。字母裁决如实执行、结果无论"
        "方向均如实入账；机制观察单列于后，不凌驾、不改写字母裁决。"
        "注意：reject≠假设被证伪的统计证明——单轮 n=3 仍是小样本方向性"
        "证据（development 域只描述不断言）；0.2/0.1 为本轮预注册描述性"
        "边界，与 APR-0011 门各自独立计算、互不凌驾（本轮门联合评价（"
        "代表配置）=not_met 与裁决=reject 分列不合并）；「正确测出无效"
        "同样是有效证据」。")
    # 证据摘录逐字校验（防转述失真）
    for ev in EXAMPLE_C_EVIDENCE:
        if ev["kind"] == "reading_notes":
            if ev["excerpt"] not in parsed_notes[ev["source"]]:
                _fail(f"机制观察摘录与 reader 原文不符: {ev['source']}")
        else:
            if ev["excerpt"] not in raw_texts[ev["source"]]:
                _fail(f"机制观察摘录与 reader 原文不符: {ev['flag_id']}")
    for ev in TOOL_BEHAVIOR_EVIDENCE + BOTTOM_ZERO_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"证据摘录与 reader 原文不符: {ev['source']}")
    reroute_r8 = reroute_production(run_r8["states"])
    reroute_r9 = reroute_production(run_r9["states"])
    reroute_r10 = reroute_production(run_r10["states"])
    reroute_by_instance = {
        n: sum(1 for d in instances[n]["per_flag_gt_detail"]
               if d["category"] == "suspicious_reroute")
        for n in INSTANCE_ORDER}
    reroute_r11 = sum(reroute_by_instance.values())
    geo_r11 = attribution["channel_1_geometry_gate"][
        "r11_area_ratio_rejected_entries"]
    geo_r10 = attribution["channel_1_geometry_gate"][
        "r10_area_ratio_rejected_entries"]
    guard_ok = len(geo_r11) == 0 and len(geo_r11) <= len(geo_r10)
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=reject "
                 "不因本观察改写）"),
        "within_vs_cross_round_variance": {
            "observation": (
                "轮内实例方差实测远小于跨轮摆动：r8→r9→r10 聚合弃权 "
                "0.222222→0.727273→0.285714（跨轮三轮摆动幅度约 0.5）vs "
                "本轮轮内视角极差 top 0.153846/bottom 0.0（同日同指引同"
                "渲染下 3 实例）——r10 定律（「实例差异主导摆动」的单"
                "实例推断）修正为「跨轮（实例群/工具代际）因素主导，轮内"
                "同日采样相对稳定」；对本轮假设（轮内实例方差显著）字母 "
                "reject 恰恰是有信息量的负结果（「正确测出无效同样是有效"
                "证据」）。top 极差 0.153846 虽未达 0.2 边界但非零（"
                "0.0 vs 0.153846 vs 0.15），bottom 三实例一致（1.0/1.0/"
                "1.0，且 7 旗全部弃权）——轮内方差存在的方向性迹象与"
                "「实质离散」判据未达并存，如实分列。"),
            "cross_round_abstain_rates": {"r8": rate_r8, "r9": rate_r9,
                                          "r10": rate_r10},
            "within_round_ranges": {"top": top_range, "bottom": bottom_range},
            "status": ("度量不稳定的定位从「实例采样」收窄到「跨轮实例群/"
                       "工具代际」；多实例协议（n=3）首次给出轮内置信带"
                       "（实例间 min..max）——本轮 union/agreement 与代表"
                       "配置三口径并列首次落地（measurement_design 五条"
                       "预注册执行）"),
        },
        "example_c_bidirectional_effect": {
            "observation": (
                "示例 c 双向效应新证据（如实记录）：同实例（top i3）对"
                "不规则抖动按其边界条款报非弃权 reroute（R11T-018/020，"
                "「形态不规则、无规律，按关注现象报告」）——而 r10 实例"
                "援引同一示例走弃权路径（R10T-012/013，run-r10 "
                "mechanism_observation.flag_location_evidence 在案）；"
                "同实例内并存：top i3 对「形态规整但不呈规则周期折叠」的"
                "大范围绕行仍按存在性一般判据弃权（R11T-006）——示例 c "
                "的效果随实例而异（r10=弃权理由词汇、r11 top-i3=边界"
                "条款被用于非弃权报告、r11 同实例 R11T-006 仍弃权），"
                "措辞修改已排程 R12（用户 2026-09-07 拍板，本轮零指引"
                "变更），如实记录。"),
            "evidence": EXAMPLE_C_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reader-raw（reading_notes/"
                               "location_evidence 原文；substring "
                               "fail-closed 校验通过）"),
            "r10_contrast_ref": {
                "path_rel": REL_RUN_R10, "sha256": _sha(REL_RUN_R10),
                "summary": ("R10T-012/013 location_evidence 明确援引"
                            "「按 r9 示例 c 与第 4 节判据」后仍走弃权路径"
                            "（run-r10 hypothesis_test.mechanism_"
                            "observation.flag_location_evidence 在案）")},
        },
        "reroute_flag_production": {
            "r8": reroute_r8,
            "r8_detail": "R8T-014（弃权旗；run-r8 在案）",
            "r9": reroute_r9,
            "r9_detail": "四份 r9 原始件零 suspicious_reroute 旗标（run-r9 在案）",
            "r10": reroute_r10,
            "r10_detail": ("R10T-012/R10T-013（均弃权；location_evidence "
                           "明确引用「r9 示例 c」判据）"),
            "r11": reroute_r11,
            "r11_by_instance": reroute_by_instance,
            "r11_detail": ("R11T-006（弃权）+R11T-018/R11T-020（非弃权），"
                           "全部出自 top-i3——逐实例产量 0/0/3（i3："
                           "1 弃权+2 非弃权）"),
        },
        "tool_behavior_evidence": TOOL_BEHAVIOR_EVIDENCE,
        "tool_behavior_note": (
            "工具行为异质性（实例自选，如实入账）：R11 十二派次 8/12 "
            "自述 PIL 局部裁剪放大（2-25 处不等；applied-top-i1 第一"
            "派次最重含像素掩膜+字符化像素图+连通域/包围盒测量），4/12 "
            "纯 Read 直读（applied-bottom-i1/i2/i3、prep1-bottom-i3，"
            "reading_notes 原文自述在案）；全部输入仍仅源自给定 PNG=非"
            "盲读违规；跨轮实例不同+轮内实例差异=混杂因素照旧声明；"
            "「实例数 1→3」操纵未（也无法）固定工具行为——跨轮可比性"
            "协议候选（统一允许/禁止 PIL 类操作或每轮固定混合配比）须"
            "预注册后执行（见 round11-dev-record "
            "next_iteration_targets）"),
    }
    metric_design_lesson = {
        "role": ("度量设计教训（如实，供未来预注册参考；本轮不追溯"
                 "适用）"),
        "lesson": (
            "本轮假设主通道=实例间弃权率极差（预注册描述性边界 0.2/0.1），"
            "实测 top 0.153846/bottom 0.0→字母裁决=reject（未达强 "
            "reject）；r8→r9→r10 跨轮摆动（0.222222→0.727273→0.285714）"
            "远大于本轮轮内实例极差（top 0.153846/bottom 0.0）——单点"
            "读数不稳定性主要来自跨轮因素而非轮内采样方差；多实例聚合"
            "口径（union/agreement 并列、代表配置+范围并列）首次给出"
            "轮内置信带，是度量设计演进第一步（measurement_design 五条"
            "预注册先于盲读冻结，不追溯往轮；r8/r9/r10 字母裁决维持"
            "不变）。"),
        "status": ("下一轮协议侧候选教训（如实登记）：跨轮可比性协议"
                   "候选（固定 reader 工具行为规约或每轮固定混合配比）"
                   "与跨轮中位数门控（r10-prep-record 引用的候选方案 "
                   "(b)，至今未执行）均须另行预注册后采用，不得回溯改判"
                   "既往轮次（本轮字母裁决=reject 维持）"),
    }
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R11,
                                "sha256": _sha(REL_PREP_R11)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "test_design": ht["test_design"],
            "null_result_note": ht["null_result_note"],
            "secondary_observation": ht["secondary_observation"],
            "candidate_0_target":
                ht["preregistered_criteria_quote"]["candidate_0_target"],
            "user_directive_2026_09_07":
                ht["preregistered_criteria_quote"][
                    "user_directive_2026_09_07"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "measurement": {
            "abstain_rate_r8": rate_r8,
            "abstain_rate_r8_fraction": "4/18",
            "abstain_rate_r9": rate_r9,
            "abstain_rate_r9_fraction": "8/11",
            "abstain_rate_r10": rate_r10,
            "abstain_rate_r10_fraction": "4/14",
            "abstain_rate_r11_by_instance": {
                n: instances[n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER},
            "abstain_rate_r11_by_instance_fraction": {
                n: ("%d/%d" % (instances[n]["combined"]["abstain_count"],
                               instances[n]["combined"]["flag_count"]))
                for n in INSTANCE_ORDER},
            "range_top": top_range,
            "range_top_arithmetic": view_layer["top"][
                "abstain_rate_range_arithmetic"],
            "range_bottom": bottom_range,
            "range_bottom_arithmetic": view_layer["bottom"][
                "abstain_rate_range_arithmetic"],
            "verdict_boundary_support": BOUNDARY_SUPPORT,
            "verdict_boundary_strong_reject": BOUNDARY_STRONG_REJECT,
            "boundary_source": (
                "r11-prep-record.json attribution_plan.primary_channel."
                "metric（预注册描述性边界：任一视角 ≥0.2 支持、全部视角 "
                "<0.2 拒绝、全部视角 <0.1 强 reject 分层标注）"),
            "support_condition_met": supported,
            "strong_reject_condition_met": strong_reject,
            "boundary_independence_note": (
                "0.2/0.1 为本轮预注册描述性边界（hypothesis_test 判据），"
                "非 APR-0011 门 evaluation 本身，也非 CONTAINMENT_MIN/"
                "AREA_RATIO_MAX 阈值常量改动——门三指标照常独立如实计算、"
                "互不凌驾（r11-prep-record null_result_note 原文语义）；"
                "本轮门联合评价（代表配置）=not_met（gt_recall 0.076923"
                "<0.75、seed_match_rate 0.076923<0.5）与裁决=reject "
                "分列不合并"),
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "其余类别非弃权旗标面积比出局条目 R10=0→R11=0（无回升"
                    "）；guard_ok（守门观察如实记录；类别门 R11=1 条非"
                    "守门范围，见 channel_attribution.channel_2_category_"
                    "gate）"),
                "guard_ok": guard_ok,
                "note": ("守门通道按 r11-prep-record attribution_plan."
                         "guard_channel 独立复核（r11 support_condition="
                         "极差边界单条件，守门非其组成要件）——两项独立"
                         "计算、结果如实分列；本轮 guard_ok=True"),
            },
            "reroute_secondary_observation": {
                "declaration": (
                    "prep-record secondary_observation 预注册：reroute 类"
                    "逐实例产量对照（示例 c 词汇效应在 n=3 下的监测，零"
                    "期望）——实测 r8=1→r9=0→r10=2→r11=3（逐实例 0/0/"
                    "3，i3：1 弃权+2 非弃权）；示例 c 效果随实例而异"
                    "（见 mechanism_observation.example_c_bidirectional_"
                    "effect）"),
                "reroute_production_r8": reroute_r8,
                "reroute_production_r9": reroute_r9,
                "reroute_production_r10": reroute_r10,
                "reroute_production_r11": reroute_r11,
                "r11_detail": ("R11T-006（弃权）+R11T-018/R11T-020（非"
                               "弃权），全部出自 top-i3"),
            },
            "aggregate_context": {
                "abstain_rate_r8": rate_r8,
                "abstain_rate_r9": rate_r9,
                "abstain_rate_r10": rate_r10,
                "abstain_rate_r11_representative": None,
                "abstain_rate_r11_representative_note": (
                    "代表配置聚合弃权率见 aggregation_representative."
                    "abstain_rate_total（本轮聚合口径按 measurement_design "
                    "五条预注册执行，代表配置/逐实例/双口径分列）"),
                "apr0011_joint_evaluation_representative": "not_met",
                "note": (
                    "跨轮聚合弃权率 0.727273（8/11）→0.285714（4/14）→"
                    "本轮六实例 12/53=0.226415（如实附记：全旗标合计口径"
                    "）vs 代表配置分列；APR-0011 四项照常独立如实执行（"
                    "代表配置口径 gt_count 13≥12 与 abstain_rate 达线，"
                    "gt_recall 0.076923<0.75 与 seed_match_rate 0.076923"
                    "<0.5 未达暂行线→joint=not_met）。0.2/0.1 描述性边界"
                    "与门各自独立计算、互不凌驾（prep-record "
                    "null_result_note 原文）——门联合=not_met 与裁决="
                    "reject 分列不合并"),
            },
            "r11_total_flags_note": (
                "六实例合计 53 旗标（非弃权 41、弃权 12；全旗标合计弃权率 "
                "0.226415 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道）"),
        },
        "verdict": verdict,
        "strong_reject_stratification": {
            "rule": ("补充分层（r11-prep-record reject_condition 原文）："
                     "全视角极差 <0.1 记「强 reject」并如实标注"),
            "claimed": strong_reject,
            "note": ("强 reject 分层不成立：top 极差 0.153846≥0.1——"
                     "如实记「reject，未达强 reject」（分层标注如实、"
                     "不因 bottom 极差 0.0<0.1 而整体标注强 reject）"),
        },
        "verdict_rule": (
            f"support={ht['support_condition']}；"
            f"reject={ht['reject_condition']}"
            "（r11-prep-record.json hypothesis_test 判据原文，轮后如实"
            "执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_design_lesson": metric_design_lesson,
        "stratified_observation": {
            "top": {"r10_rate": rate_r10, "r10_fraction": "4/14",
                    "r11_by_instance": top_rates,
                    "r11_range": top_range,
                    "direction": ("r10 单实例 0.285714（4/14）→r11 三实例 "
                                  "0.0/0.153846/0.15（轮内极差 0.153846）——"
                                  "r10 单点读数落入本轮实例间范围内，"
                                  "轮内方差未达 0.2 边界")},
            "bottom": {"r10_rate": None, "r10_fraction": "0/0",
                       "r11_by_instance": bottom_rates,
                       "r11_range": bottom_range,
                       "direction": ("bottom 三实例弃权率一致 1.0（7 旗"
                                     "全部弃权、零非弃权旗）——r10 同格 "
                                     "0/0 零旗标（rate=null）→r11 有旗但"
                                     "全弃权；matches=0 与 r10 一致")},
            "confounder_note": (
                "跨轮 reader 实例不同+轮内实例差异（8/12 派次 PIL 局部"
                "裁剪放大 vs 4/12 纯直读）=混杂因素照旧声明；每视角 n=3 "
                "仍为小样本；development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r10: dict) -> dict:
    """courtyard 被动追踪（r11-prep-record secondary_observation 预注册；
    零阈值改动、零期望；bottom 全弃权观察如实入账）。"""
    prep_doc = _json_load(REL_PREP_R11)
    note_quote = prep_doc["hypothesis_test"]["secondary_observation"]
    for ev in BOTTOM_ZERO_EVIDENCE:
        if ev["excerpt"] not in _rel(
                RAW_FILES[ev["source"]]).read_text(encoding="utf-8"):
            _fail(f"bottom 零旗标证据摘录与 reader 原文不符: {ev['source']}")
    non_abstain_rows, abstain_rows = [], []
    for n in INSTANCE_ORDER:
        rec = instances[n]
        abst = set(rec["combined"]["abstain_ids"])
        matched_ids = {m["flag_id"]: m
                       for m in rec["combined"]["matches_detail"]}
        for d in rec["per_flag_gt_detail"]:
            if d["category"] != "courtyard_crowding" or d["abstain"]:
                continue
            overlaps = d["gt_overlaps"]
            ars = [o["area_ratio"] for o in overlaps
                   if o["area_ratio"] is not None]
            m = matched_ids.get(d["flag_id"])
            non_abstain_rows.append({
                "flag_id": d["flag_id"], "instance": n,
                "state": d["state"], "view": rec["view"],
                "gt_entries_checked": len(
                    rec["states"][d["state"]]["gt_entries"]),
                "containment_all_none": d["containment_all_none"],
                "area_ratio_min": min(ars) if ars else None,
                "area_ratio_max": max(ars) if ars else None,
                "matches": 1 if m else 0,
                "matched_detail": (
                    {"gt_id": m["gt_id"], "state": m["state"],
                     "containment": m["containment"],
                     "area_ratio": m["area_ratio"]} if m else None)})
        for fid in sorted(abst):
            d = next(x for x in rec["per_flag_gt_detail"]
                     if x["flag_id"] == fid)
            if d["category"] == "courtyard_crowding":
                abstain_rows.append({"flag_id": fid, "instance": n,
                                     "state": d["state"],
                                     "view": rec["view"]})
    non_abstain_rows.sort(key=lambda r: (r["instance"], r["flag_id"]))
    abstain_rows.sort(key=lambda r: (r["instance"], r["flag_id"]))
    return {
        "note_source": {"path_rel": REL_PREP_R11,
                        "sha256": _sha(REL_PREP_R11), "quote": note_quote},
        "declaration": ("被动追踪（prep-record secondary_observation 预"
                        "注册）：如实记录 courtyard 类旗标匹配表现（示例 c "
                        "词汇效应监测与 courtyard 追踪并列预注册；零阈值"
                        "改动、零期望、不得为提高命中调阈值）"),
        "r11_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": "弃权旗不参与匹配（abstain 单列）",
        },
        "courtyard_matches_r11": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r10": run_r10["courtyard_tracking"][
            "courtyard_matches_r10"],
        "courtyard_matches_r10_detail": (
            "R10T-011↔GT-REVC-P1-R4J3（containment 0.829864、面积比 "
            "1.770688；run-r10 在案）"),
        "courtyard_matches_r9": run_r9["courtyard_tracking"][
            "courtyard_matches_r9"],
        "courtyard_matches_r9_detail": (
            "R9 top 非弃权 courtyard 2 条（R9T-001/R9T-002）与同态 GT "
            "零交集、弃权 2 条（R9T-007/R9T-008）；run-r9 在案"),
        "courtyard_matches_r8": run_r9["courtyard_tracking"][
            "courtyard_matches_r8"],
        "courtyard_matches_r8_source_note": (
            "run-r8 无 courtyard_tracking 节（该节自 r9 起在案）；r8 值"
            "取自 run-r9 courtyard_tracking.courtyard_matches_r8 在案值"),
        "courtyard_matches_r8_detail": (
            "R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、面积比 "
            "2.688288；run-r8 在案）"),
        "same_domain_note": (
            "r11 三条 courtyard 命中（top-i1 R11T-009↔R4J3、top-i3 "
            "R11T-010↔AP-1-R5U6、R11T-003↔AP-6-R2LED2）与 r8 R8T-004、"
            "r10 R10T-011 命中同域（Y1/R4J3 类 courtyard 密集区）——"
            "courtyard 密集区可命中性跨轮复现；GT/阈值零改动"),
        "bottom_observation": {
            "fact": ("R11 bottom 7 旗（bottom-i1 prep1 2、bottom-i2 "
                     "applied 3、bottom-i3 applied 2）全部弃权——bottom "
                     "非弃权旗=0、matches=0；r10 同格两格零旗标→r11 "
                     "有旗但全弃权；prep1-bottom i2/i3 与 applied-bottom "
                     "i1 三格零旗标（「正常特征→不报告」通道继续使用，"
                     "reading_notes 原文自述在案）"),
            "evidence": BOTTOM_ZERO_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）"),
            "rate_note": BOTTOM_ZERO_PART_NOTE,
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r11 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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

    instances = {name: build_instance_record(name, INSTANCES[name], parsed,
                                             gt_applied, gt_prep1)
                 for name in INSTANCE_ORDER}
    view_layer = build_view_layer(instances)
    gt_dual = build_gt_dual(instances, gt_applied, gt_prep1)

    # 实例态块平铺（供通道归因重放；带定位元数据）
    inst_blocks = []
    for name in INSTANCE_ORDER:
        for st, part in (("applied", INSTANCES[name]["parts"][0]),
                         ("prep1", INSTANCES[name]["parts"][1])):
            blk = dict(instances[name]["states"][st])
            blk["_part_key"] = part
            blk["_instance"] = name
            blk["_state"] = st
            inst_blocks.append(blk)
    inst_replays = {
        blk["_part_key"]: channel_replay(blk["reader_flags"],
                                         blk["flag_views"],
                                         blk["gt_entries"])
        for blk in inst_blocks}

    # 代表配置（measurement_design item 4）：每视角 flag_count 中位数实例
    rep = pick_representative(instances)
    top_name = rep["members"]["top"]
    bot_name = rep["members"]["bottom"]
    rep_appl = _merge_state_blocks(
        [dict(instances[top_name]["states"]["applied"],
              members_note=f"{top_name}/applied-top（{top_name}）"),
         dict(instances[bot_name]["states"]["applied"],
              members_note=f"{bot_name}/applied-bottom（{bot_name}）")],
        "applied", "ASM-7 终检后终态（代表配置）", gt_applied)
    rep_prep = _merge_state_blocks(
        [dict(instances[top_name]["states"]["prep1"],
              members_note=f"{top_name}/prep1-top（{top_name}）"),
         dict(instances[bot_name]["states"]["prep1"],
              members_note=f"{bot_name}/prep1-bottom（{bot_name}）")],
        "prep1", "ASM-P1 批前快照（种子域；代表配置）", gt_prep1)
    agg = _aggregate(rep_prep, rep_appl)
    comp = _compliance(agg)
    metric_ranges = build_metric_ranges(instances)

    run_r6 = _json_load(REL_RUN_R6)
    run_r7 = _json_load(REL_RUN_R7)
    run_r8 = _json_load(REL_RUN_R8)
    run_r9 = _json_load(REL_RUN_R9)
    run_r10 = _json_load(REL_RUN_R10)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r10, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, instances,
                                view_layer, attribution, raw_texts,
                                parsed_notes)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9, run_r10)

    prep_r11 = _json_load(REL_PREP_R11)
    serial = list(RAW_FILES)
    by_view = {"top": 0, "bottom": 0}
    abst_by_view = {"top": 0, "bottom": 0}
    by_category: dict = {}
    abstain_by_instance = {}
    reroute_by_instance = {n: 0 for n in INSTANCE_ORDER}
    for name in INSTANCE_ORDER:
        abstain_by_instance[name] = instances[name]["combined"][
            "abstain_count"]
        reroute_by_instance[name] = sum(
            1 for d in instances[name]["per_flag_gt_detail"]
            if d["category"] == "suspicious_reroute")
        for st in ("applied", "prep1"):
            blk = instances[name]["states"][st]
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
    n_total = sum(instances[n]["combined"]["flag_count"]
                  for n in INSTANCE_ORDER)
    n_abstain_total = sum(abstain_by_instance.values())
    reader_block = {
        "dispatch_discipline": DISPATCH_DISCIPLINE,
        "dispatch_mode": DISPATCH_MODE,
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
            "by_instance": {n: instances[n]["combined"]["flag_count"]
                            for n in INSTANCE_ORDER},
            "abstain_by_instance": abstain_by_instance,
            "by_state": {"applied": sum(
                len(instances[n]["states"]["applied"]["reader_flags"])
                for n in INSTANCE_ORDER),
                "prep1": sum(len(instances[n]["states"]["prep1"][
                    "reader_flags"]) for n in INSTANCE_ORDER)},
            "by_view": {"top": by_view["top"], "bottom": by_view["bottom"]},
            "abstain_by_view": {"top": abst_by_view["top"],
                                "bottom": abst_by_view["bottom"]},
            "by_category": by_category,
            "reroute_by_instance": reroute_by_instance,
            "reroute_class_production": sum(reroute_by_instance.values()),
            "total": n_total,
        },
        "reader_instance_note": READER_INSTANCE_NOTE,
        "location_evidence_note": (
            "location_evidence 保留于 raw 原文（hash 在案），不进度量"
            "五键投影（process-v1 §2 步骤3）；prep1-top-i3 的 reading_"
            "notes 与 R11T-018/020 location_evidence 明确援引「r9 示例 c "
            "的界限」（mechanism_observation.example_c_bidirectional_"
            "effect 逐字摘录在案）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
        "bottom_zero_flag_parts": {
            "parts": [
                {"instance": n, "state": st,
                 "flag_count": len(instances[n]["states"][st]
                                   ["reader_flags"])}
                for n in INSTANCE_ORDER for st in ("applied", "prep1")
                if not instances[n]["states"][st]["reader_flags"]],
            "note": BOTTOM_ZERO_PART_NOTE,
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R11, "role": "r11_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R11)},
        {"path_rel": REL_GUIDANCE_R9,
         "role": "observation_guidance_r9_zero_byte_reuse",
         "sha256": _sha(REL_GUIDANCE_R9)},
        {"path_rel": REL_GUIDANCE_R8, "role": "observation_guidance_r8_baseline",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_DEV_R10,
         "role": "r10_dev_record_preregistration_source",
         "sha256": _sha(REL_DEV_R10)},
        {"path_rel": REL_PREP_R10, "role": "r10_prep_record_witness_source",
         "sha256": _sha(REL_PREP_R10)},
        {"path_rel": REL_DEV_R9, "role": "r9_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R9)},
        {"path_rel": REL_PREP_R9, "role": "r9_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R9)},
        {"path_rel": REL_PREP_R8, "role": "r8_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R8)},
        {"path_rel": REL_PREP_R7, "role": "r7_prep_record_witness_chain",
         "sha256": _sha(REL_PREP_R7)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_GT_AUDIT, "role": "gt_audit_r1_closed",
         "sha256": _sha(REL_GT_AUDIT)},
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
        "kind": "tl2_calibration_run_r11",
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
                "in_calibrated_range 恒 False（协议 v1 §1/§4；v1.1 追加"
                "式修订若被正式采纳其对门的评价含义须另行声明）"),
            "protocol_ref": {"path_rel": REL_PROTOCOL,
                             "sha256": _sha(REL_PROTOCOL)},
        },
        "instrument_change": {
            "nature": INSTRUMENT_NATURE,
            "components": ["per-view-instance-count-1-to-3（协议侧唯一"
                           "操纵；非指引/渲染/GT/阈值变更）"],
            "unchanged_components": list(prep_r11["unchanged_components"]),
            "protocol_amendment": {
                "amendment_version": prep_r11["protocol_amendment"][
                    "amendment_version"],
                "amendment_mode": prep_r11["protocol_amendment"][
                    "amendment_mode"],
                "v1_file_preserved": prep_r11["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("evaluation-protocol-v1→v1.1 追加式修订（只追加"
                         "盲读执行与聚合口径，不改动 v1 任何既有条款语义；"
                         "v1 文件零字节保留、不回写；本轮不新建协议版本"
                         "文件）"),
            },
            "attribution_note": (
                "r11-prep-record.json attribution_plan：本轮恰一个协议侧"
                "操纵变量（每视角独立实例数 1→3）、检验恰一个假设（"
                "round10-dev-record next_iteration_targets[0] 方案 (a)"
                "「每格多实例重复读」n=3，r10-dev-record-candidate-0-i-"
                "multi-instance）——主通道=实例间弃权率极差（预注册描述性"
                "边界 0.2/0.1：任一视角 ≥0.2 支持、全部视角 <0.2 拒绝、"
                "全部视角 <0.1 强 reject 分层；0.2/0.1 与 APR-0011 门各自"
                "独立计算、互不凌驾、run-record 内分开表述）；守门通道="
                "其余类别非弃权旗 frame_box_pct 几何门（面积比出局条目无"
                "回升）。轮后按极差相对边界方向归因（见 run-r11 "
                "hypothesis_test：字母裁决唯一正式、强 reject 分层如实、"
                "机制观察单列不凌驾——本轮机制观察：轮内实例方差实测远小"
                "于跨轮摆动，度量不稳定定位收窄到「跨轮实例群/工具代际」"
                "；示例 c 效果随实例而异）；跨轮 flag_id 不构成同旗配对，"
                "归因是通道级不是旗级。渲染零变更下 R10→R11 的实例数操纵"
                "不改变指引/渲染/GT/阈值任何实质；实例自选工具行为差异"
                "（8/12 派次 PIL 局部裁剪放大 vs 4/12 纯直读）如实入账"
                "（reader_instance_note）。"),
            "ref": {"path_rel": REL_PREP_R11, "sha256": _sha(REL_PREP_R11)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.1（追加式；v1 文件零字节"
                                          "保留，见 protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；机械命名覆盖（r11-prep-record guidance_reuse."
            "mechanical_naming_override）：指引 §6 的 flag_id 前缀 "
            "R9T/R9B→R11T/R11B、reader_id reader-r9-*→reader-r11-{top,"
            "bottom}-i{1,2,3}（命名属编排侧机械替换，非判据变更；判读"
            "实质判据零变更；实例间编号独立、同实例跨板连续）"),
        "coverage_caveat": cal.COVERAGE_CAVEAT_V3,
        "reader": reader_block,
        "instances": instances,
        "parse_rejections": rejections,
        "view_layer": view_layer,
        "gt_match_dual": gt_dual,
        "representative_configuration": rep,
        "aggregation_representative": agg,
        "compliance_representative": comp,
        "metric_ranges_instance": metric_ranges,
        "parallel_record_note": (
            "measurement_design item 4 三者并列如实呈现（不合并、不挑优）："
            "①代表配置 joint 结果（aggregation_representative/"
            "compliance_representative）；②per-metric 实例间范围"
            "（metric_ranges_instance）；③逐实例原始记录（instances，"
            "measurement_design item 1）——另有 GT 匹配双口径"
            "（gt_match_dual，item 3）与视角层三分列（view_layer，"
            "item 2）并列"),
        "hypothesis_test": hyp,
        "channel_attribution": attribution,
        "courtyard_tracking": courtyard,
        "gt_audit_reference": {
            "path_rel": REL_GT_AUDIT, "sha256": _sha(REL_GT_AUDIT),
            "note": ("只读 GT 源审计（gt-audit-r1，2026-09-07，"
                     "sha 1f20554a…）：bottom GT=无源已关闭、reroute GT="
                     "无源已关闭、L1NB 框径=合理维持现框——GT 侧三候选"
                     "全部关闭（r8 轮同日审计，结论 r9/r10/r11 延续引用）；"
                     "该审计非本轮预注册件（deviations 在案），其结论维持"
                     "本轮 GT 零改动；round11-dev-record gt_audit_ref/"
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
                "thresholds_note": "声明常量，本轮零覆盖（与 r10 相同；"
                                   "只作口径引用，APR-0011 阈值零改动）",
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
                    "说明，非期望清单；反放宽条款原样；示例 c 措辞修改已"
                    "排程 R12、本轮零指引变更）；abstain=true=现象是否"
                    "存在或归属哪类无法负责任地判断；abstain 单列不参与"
                    "匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("协议侧 v1.1（本轮唯一变更）：12 次"
                                      "盲读=4 视角格×3 实例（i1/i2/i3），"
                                      "两波次串行保序（同一实例先 applied "
                                      "后 prep1，flag_id 编号跨板连续、"
                                      "实例间编号独立）；每图独立判读；"
                                      "跨实例/跨视角禁止交流"),
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
            "note": ("轮次预注册链：round10-dev-record.json（da4e85f9…，"
                     "next_iteration_targets[0] 候选方案 (a) 原文被 "
                     "r11-prep-record 逐字摘录预注册+用户 2026-09-07 拍板"
                     "两项（方案 (a) n=3 本轮执行；示例 c 措辞修改排程 "
                     "R12））→r11-prep-record.json（9074df2d…，本轮预"
                     "注册件，measurement_design 五条聚合口径先于盲读"
                     "冻结）先于本轮盲读落盘（零 GT 暴露声明在案 "
                     "no_visual_reading=true；渲染复用见证=四 PNG 盘上"
                     "实测 sha 与见证常量逐一相等+渲染输入侧冻结 PDF 复核"
                     "一致；见证常量源=r10-prep-record.json（3791edb1…），"
                     "在案）；observation-guidance-r9.md 零字节复用（锚 "
                     "a0c10154…，零指引作者动作）；GT 重投影（derivation-"
                     "log-r5.json，13 条 frame_box_pct_r5）已在案沿用"
                     "（渲染未变=零新派生）；盲读后本包只做比对与记录"
                     "（读者产物零改动）。GT 冻结纪律：轮后未增删改；"
                     "gt-audit-r1 结论维持 GT 零改动（三候选关闭，"
                     "gt_audit_reference 在案）。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "r7_run": {"path_rel": REL_RUN_R7, "sha256": _sha(REL_RUN_R7)},
            "r8_run": {"path_rel": REL_RUN_R8, "sha256": _sha(REL_RUN_R8)},
            "r9_run": {"path_rel": REL_RUN_R9, "sha256": _sha(REL_RUN_R9)},
            "r10_run": {"path_rel": REL_RUN_R10, "sha256": _sha(REL_RUN_R10)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）与 R9"
                     "（§3A 示例 c 增补轮）与 R10（零变更重复轮）run 在案；"
                     "R11=协议侧单变量轮（每视角实例 1→3，v1.1 追加式）；"
                     "轮间对比见 round11-dev-record.json 的方向性观察与 "
                     "channel_attribution、hypothesis_test（development "
                     "域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取与通道重放为纯函数"
            "（六实例旗数 13/13/20/2/3/2→代表配置唯一可复算），无 "
            "wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-07-r11（事件序="
            "预注册冻结（round10-dev-record（da4e85f9…，在案）→r11-prep-"
            "record（9074df2d…，本轮预注册件）→复用渲染见证）→12 次盲读→"
            "比对记录；在案延续=gt-audit-r1 只读 GT 源审计（r8 轮落盘，"
            "本轮延续引用其结论，GT 零改动维持））"),
    }


DEV_OBSERVATIONS = [
    "R10→R11 派发与旗标量对照：盲读派次 4→12（协议侧唯一操纵=每视角实例 "
    "1→3）；旗标 14→53（六实例 13/13/20/2/3/2；非弃权 10→41、弃权 "
    "4→12）；全旗标合计弃权率 0.285714（4/14）→0.226415（12/53，附记"
    "口径）；预注册主通道=实例间弃权率极差：top 0.153846（0.0/0.153846/"
    "0.15）、bottom 0.0（1.0/1.0/1.0）——轮内极差均 <0.2（bottom 同为 "
    "1.0）；代表配置（top-i1+bottom-i1，两视角中位实例均有 tie、按先序"
    "取 i1 并如实注明）弃权率 0.133333（2/15）。",
    "matches 与 GT 双口径（measurement_design item 3 首次落地）：r10 "
    "matches=1（单实例口径）→r11 逐实例逐态 matches 合计 4 条（top-i1 "
    "R11T-009↔R4J3、top-i2 R11T-012↔L1SHORT、top-i3 R11T-010↔AP-1-"
    "R5U6/R11T-003↔AP-6-R2LED2；bottom 三实例零非弃权旗=零匹配）——"
    "GT 条目层 union=4/13（gt_recall_union 0.307692）、agreement=0/13"
    "（0.0）：四条命中各由恰一个实例贡献（逐 GT matched_by_count 全部 "
    "≤1），无一 GT 条目被 ≥2 实例同时命中；代表配置 gt_recall_total="
    "0.076923（1/13）。命中位置与 r8 R8T-004、r10 R10T-011 同域（R4J3/"
    "Y1 类 courtyard 密集区）外，r11 新增 L1SHORT（other_advisory，铜"
    "短路按缺陷性质诚实映射类）与 AP-1/AP-6（Y1 区 courtyard）两类命中。",
    "通道归因（vs R10，预注册重放方法）：几何门面积比出局 0→0（R7 起"
    "连续空，guard 通道无回升）；类别门 0→1（R11T-012，applied-top-i3，"
    "silk_readability↔GT-REVC-AP-8-R1Q2，containment 0.616745、面积比 "
    "1.648816，近邻双几何条件通过但类别不符）；视角门 0→0（bottom 7 旗"
    "全部弃权=零非弃权 bottom 旗）。通道链自 r6 起：几何门 r6=1→r7=0→"
    "r8=0→r9=0→r10=0→r11=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1。",
    "预注册假设（r10-dev-record-candidate-0-i-multi-instance）字母裁决="
    "拒绝（全部视角实例间弃权率极差 <0.2：top 0.153846、bottom 0.0；"
    "r11-prep-record 判据原文执行；唯一正式裁决）；强 reject 分层不成立"
    "（top 0.153846≥0.1）→如实记「reject，未达强 reject」；守门通道"
    "独立复核（几何门 0→0 无回升）通过。机制观察单列（不凌驾）：轮内"
    "实例方差实测远小于跨轮摆动（r8→r9→r10 聚合弃权 0.222222→0.727273"
    "→0.285714 vs 轮内视角极差 top 0.153846/bottom 0.0）——r10 定律"
    "修正为「跨轮（实例群/工具代际）因素主导，轮内同日采样相对稳定」，"
    "度量不稳定的定位从「实例采样」收窄到「跨轮实例群/工具代际」；"
    "「正确测出无效同样是有效证据」。示例 c 双向效应新证据：同实例"
    "（top i3）对不规则抖动按其边界条款报非弃权 reroute（R11T-018/020），"
    "r10 实例援引同一示例走弃权——示例 c 的效果随实例而异；reroute "
    "逐实例产量 0/0/3（i3：1 弃权 R11T-006+2 非弃权 R11T-018 与 "
    "R11T-020）。",
    "工具行为异质性（实例自选，如实入账）：R11 十二派次全部 Read 直读"
    "内嵌图像（非 URL 转传/无外部视觉 API）；8/12 派次自述 PIL 局部裁剪"
    "放大（2-25 处不等，applied-top-i1 第一派次最重含像素掩膜+字符化"
    "像素图+连通域/包围盒测量），4/12 派次自述纯直读（applied-bottom-"
    "i1/i2/i3、prep1-bottom-i3，reading_notes 原文自述在案）；跨轮实例"
    "不同+轮内实例差异=混杂因素照旧声明（reader_instance_note）。",
    "输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：applied-"
    "bottom i2/i3、prep1-top i1/i2/i3、prep1-bottom i2/i3 七件经 json."
    "dump indent=1 重序列化（内容逐键忠实；reader 原输出格式不一：紧凑"
    "单行/多行缩进混杂），prep1-bottom-i1 为多行缩进 JSON Write 原文"
    "落盘，其余四件紧凑单行原样落盘；无围栏剥离本先例记录（r7/r10 有）"
    "——12 件 parse 校验全部通过，均非盲读违规。",
    "courtyard 被动追踪（prep-record 预注册）：R11 非弃权 courtyard 旗 "
    "14 条中 3 条命中（top-i1 R11T-009↔GT-REVC-P1-R4J3 containment "
    "0.723377/面积比 0.734272、top-i3 R11T-010↔GT-REVC-AP-1-R5U6 "
    "0.927745/1.75184、R11T-003↔GT-REVC-AP-6-R2LED2 0.689959/1.10596），"
    "全部与 r8 R8T-004、r10 R10T-011 命中同域（Y1/R4J3 类 courtyard "
    "密集区）；bottom courtyard 3 条全部弃权；courtyard 匹配 r8=1→r9=0"
    "→r10=1→r11=3；GT/阈值零改动、零期望。",
    "bottom 观察（measurement_design item 5）：bottom 7 旗全部弃权（"
    "零非弃权旗=零匹配）；bottom-i1×applied、bottom-i2×prep1、"
    "bottom-i3×prep1 三格零旗标（分母为零→弃权率按 cal._ratio 先例="
    "None，不编造数值）；「正常特征→不报告」通道继续使用（applied-"
    "bottom-i1/prep1-bottom-i2/prep1-bottom-i3 reading_notes 原文自述"
    "在案）；bottom 零旗标现象自 r11 起首次获得实例间重复观测（三实例"
    "逐格口径）。",
    "跨轮 flag_id 不构成同旗配对（R10T/R10B 与 R11T/R11B 来自不同 "
    "reader 实例）；通道归因是通道级不是旗级（run-r11 channel_"
    "attribution.pairing_caveat）；重放与 compare_v3 对拍一致（R10 两态"
    "与 R11 十二件全部复现：候选对=各实例 matches）。",
]

DEV_NEXT_TARGETS = [
    "跨轮可比性协议候选（协议侧，本轮实测导出、须预注册后执行）：r11 实测"
    "轮内实例方差（top 极差 0.153846/bottom 0.0）≪跨轮摆动（r8→r9→r10 "
    "0.222222→0.727273→0.285714）——度量不稳定定位收窄到「跨轮实例群/"
    "工具代际」；候选方案：固定 reader 工具行为规约（统一允许/禁止 PIL "
    "类局部裁剪放大等操作，r11 实测 8/12 派次 PIL vs 4/12 纯直读）或"
    "每轮固定实例混合配比（如固定 PIL/直读派次比例）；对应 r10-prep-"
    "record 引用的候选方案 (b)（跨轮中位数门控，至今未执行）。诸案均须"
    "先预注册再执行，不得回溯改判既往轮次（r8/r9/r10/r11 字母裁决维持"
    "不变）。",
    "示例 c 措辞修改（指引侧，用户 2026-09-07 已拍板排程 R12——"
    "user_directive_2026_09_07 原文在案）：r11 新证据=示例 c 效果随实例"
    "而异（top i3 对不规则抖动按其边界条款报非弃权 reroute R11T-018/"
    "020、对规整大范围绕行仍弃权 R11T-006；r10 实例援引同一示例走弃权）"
    "——R12 措辞修改预注册时将该双向效应证据纳入判据；指引侧变更须"
    "预注册+单变量纪律。",
    "渲染侧 bottom 图层清单仍是候选（r6–r11-prep-record 在案候选；r11 "
    "bottom 7 旗全部弃权、零非弃权旗=零匹配，bottom 图层清单缺失的影响"
    "仍无法与实例差异分离）；属渲染侧变更，须预注册+声明零仪器变更纪律"
    "例外。",
    "courtyard 密集旗追踪延续（指引侧观察候选）：r11 三条命中（top-i1 "
    "R11T-009↔R4J3、top-i3 R11T-010↔AP-1-R5U6/R11T-003↔AP-6-R2LED2）"
    "与 r8 R8T-004、r10 R10T-011 同域（Y1/R4J3 类 courtyard 密集区）"
    "——可命中性跨轮复现；继续被动追踪（GT/阈值零改动；不得为提高命中"
    "调阈值；无期望）。",
    "GT 侧已全关闭声明延续：r8 轮同日只读审计 gt-audit-r1（1f20554a…）"
    "三候选全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、L1NB "
    "框径=合理维持现框），r9/r10/r11 延续零改动——GT 侧已全部关闭，"
    "后续迭代回归指引侧/渲染侧/协议侧。",
    "迭代目标不变式：任何仪器/指引/协议变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）；连续达标计数 0（R10 后）→0（本轮，代表配置"
    "口径），正式采纳门槛未达成；多实例聚合口径（union/agreement、"
    "代表配置+范围）若转正式须另行声明其对门的评价含义（v1.1 scope_note）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round11-dev-record 文档构建（T3；单向引用 run-r11 sha）。"""
    agg = run_doc["aggregation_representative"]
    comp = run_doc["compliance_representative"]
    trend_rows = []
    for r in (5, 6, 7, 8, 9, 10):
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
        "round": "r11", "round_id": run_doc["round_id"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "matches_total": agg["matches_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "source": {"path_rel": REL_RUN_R11, "sha256": run_sha},
    })
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round11_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域协议侧单变量变更轮（第十一轮；v1.1 首轮）："
            "唯一变更变量=每视角独立 reader 实例数 1→3（evaluation-"
            "protocol-v1→v1.1 追加式修订，只追加盲读执行与聚合口径、不"
            "改动 v1 任何既有条款语义；v1 文件零字节保留、不回写）——"
            "判读指引 observation-guidance-r9.md 零字节复用（无新指引"
            "文件，零文本变更，锚 a0c10154…；示例 c 措辞修改已排程 R12，"
            "用户 2026-09-07 拍板），R5 冻结渲染件逐字节复用（零仪器"
            "变更、零重渲染，PNG 见证在案），GT 集/协议阈值与度量版本/"
            "比较器常量零改动（GT 重投影沿用 derivation-log-r5——渲染"
            "未变=零新派生；gt-audit-r1 三候选关闭结论延续）；唯一实验"
            "操纵=协议侧多实例修订（执行 round10-dev-record next_"
            "iteration_targets[0] 方案 (a)「每格多实例重复读」n=3，"
            "预注册于 r11-prep-record，链 da4e85f9→9074df2d）；检验 r10 "
            "预注册候选假设 r10-dev-record-candidate-0-i-multi-instance"
            "（判据=r11-prep-record.json hypothesis_test，轮后如实执行："
            "字母裁决唯一正式+强 reject 分层如实标注+机制观察单列）；"
            "预注册描述性边界 0.2/0.1 只用于本轮假设检验方向归因，与 "
            "APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量"
            "各自独立计算、互不凌驾、分开表述；measurement_design 五条"
            "聚合口径（实例主记录/视角层三分列/GT 匹配双口径/代表配置"
            "+范围并列/bottom 零分母=None）先于盲读冻结、本轮首次落地；"
            "机械命名覆盖 R9T/R9B→R11T/R11B 与 reader-r9-*→reader-r11-"
            "{top,bottom}-i{1,2,3}（guidance_reuse，判读实质零变更）；"
            "按协议 v1 §4，迭代轮证据不冒充未见留出，in_calibrated_range "
            "恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "preregistration_chain_note": (
            "预注册链（含哈希）：round10-dev-record.json（da4e85f9…，"
            "next_iteration_targets[0] 候选方案 (a) 原文+用户 2026-09-07 "
            "拍板）→r11-prep-record.json（9074df2d…，逐字摘录候选原文"
            "预注册+measurement_design 五条聚合口径先于盲读冻结=本轮"
            "执行依据）→run-r11（本链执行落盘）；observation-guidance-"
            "r9.md 零字节复用（锚 a0c10154…）；渲染复用见证源=r10-prep-"
            "record.json（3791edb1…）"),
        "run_record_ref": {"path_rel": REL_RUN_R11, "sha256": run_sha},
        "gt_audit_ref": run_doc["gt_audit_reference"],
        "flag_production": {
            "reader_ids": run_doc["reader"]["reader_ids"],
            "raw_files": run_doc["reader"]["raw_files"],
            "flag_count_by_file": {
                key: run_doc["reader"]["parse"][key]["flag_count"]
                for key in RAW_FILES},
            "flag_count_by_instance": run_doc["reader"]["flag_count"][
                "by_instance"],
            "abstain_by_instance": run_doc["reader"]["flag_count"][
                "abstain_by_instance"],
            "non_abstain_count": sum(
                run_doc["reader"]["flag_count"]["by_category"][c][
                    "non_abstain"]
                for c in run_doc["reader"]["flag_count"]["by_category"]),
            "abstain_count": sum(run_doc["reader"]["flag_count"][
                "abstain_by_instance"].values()),
            "abstain_rate_all_flags": cal._ratio(
                sum(run_doc["reader"]["flag_count"][
                    "abstain_by_instance"].values()),
                run_doc["reader"]["flag_count"]["total"]),
            "abstain_rate_all_flags_note": ("全旗标合计口径仅作附记；本轮"
                                            "预注册主通道=实例间弃权率"
                                            "极差（实例层/视角层分列）"),
            "abstain_rate_by_instance": {
                n: run_doc["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER},
            "abstain_rate_range_by_view": {
                "top": run_doc["view_layer"]["top"]["abstain_rate_range"],
                "bottom": run_doc["view_layer"]["bottom"][
                    "abstain_rate_range"]},
            "flag_count_by_category": run_doc["reader"]["flag_count"][
                "by_category"],
            "reroute_by_instance": run_doc["reader"]["flag_count"][
                "reroute_by_instance"],
            "reroute_class_production": run_doc["reader"]["flag_count"][
                "reroute_class_production"],
            "parse_rejections": run_doc["parse_rejections"],
            "blind_discipline": DISPATCH_DISCIPLINE,
            "reader_instance_note": READER_INSTANCE_NOTE,
            "note": ("flag 全部通过 calibration fail-closed 校验（拒收"
                     "清单为空）；读者产物为冻结证据，本包零改动；派发"
                     "模式=12 派次（4 格×3 实例，两波次串行保序）；机械"
                     "命名覆盖 R9T/R9B→R11T/R11B（guidance_reuse）；读者"
                     "实例行为差异（8/12 派次 PIL 局部裁剪放大、4/12 派次"
                     "纯 Read 直读）与输出格式异常披露（七件 indent=1 重"
                     "序列化+一件 Write 原文+四件原样；无围栏剥离）如实"
                     "登记为混杂因素，不作废"),
        },
        "diagnostic_result": {
            "aggregation_scope": "representative_configuration（top-i1+"
                                 "bottom-i1，measurement_design item 4）",
            "joint_evaluation": comp["joint_evaluation"],
            "criteria": [{"id": c["id"], "actual": c["actual"],
                          "threshold": c["threshold"], "met": c["met"]}
                         for c in comp["criteria"]],
            "gt_recall_total": agg["gt_recall_total"],
            "seed_match_rate_total": agg["seed_match_rate_total"],
            "abstain_rate_total": agg["abstain_rate_total"],
            "gt_match_dual": {
                "union": run_doc["gt_match_dual"]["union"],
                "agreement": run_doc["gt_match_dual"]["agreement"],
            },
            "metric_ranges_instance": run_doc["metric_ranges_instance"],
            "seed_metric_note": cal.SEED_METRIC_NOTE,
        },
        "hypothesis_test_i": run_doc["hypothesis_test"],
        "joint_evaluation_trend": {
            "aggregation_scope_note": ("r5–r10 行=各轮 run-record 全旗标"
                                       "聚合（单实例/轮口径在案）；r11 行="
                                       "代表配置口径（measurement_design "
                                       "item 4）——两口径并列如实、不"
                                       "混同（r11 全旗标合计 12/53="
                                       "0.226415 仅作附记）"),
            "after_r10": {"consecutive_met_count": 0,
                          "note": "R10 联合评价 not_met（在案），连续达标"
                                  "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价（代表配置）not_met（"
                                   "gt_recall 0.076923 与 seed_match_rate "
                                   "0.076923 未达暂行线；abstain_rate "
                                   "0.133333≤0.5 单分项入线）——GT 条目"
                                   "层 union 口径 4/13=0.307692 亦未达 "
                                   "0.75（双口径与门分列如实）"},
            "consecutive_met_count_now": 0,
            "by_round": trend_rows,
            "note": "连续达标计数变动：0（R10 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r10": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，协议侧单变量变更轮：指引 r9 零字节复用"
            "+R5 冻结渲染复用+GT/阈值零变更，唯一操纵=每视角实例 1→3）"
            "12 派次 53 旗标中 12 弃权、41 非弃权：代表配置（top-i1+"
            "bottom-i1）gt_recall=0.076923（1/13）、seed_match_rate="
            "0.076923（1/13，诊断口径，禁称 precision/FPR）、abstain_"
            "rate=0.133333（2/15），联合评价 not_met（gt_recall 与 "
            "seed_match_rate 两项未达 APR-0011 暂行线；诊断对照，非采纳"
            "门；连续达标计数 0→0）。预注册假设（r10-dev-record-"
            "candidate-0-i-multi-instance）裁决（按 r11-prep-record "
            "hypothesis_test 判据）=拒绝（字母口径，唯一正式裁决）：全部"
            "视角实例间弃权率极差 <0.2（top 0.153846、bottom 0.0）；强 "
            "reject 分层不成立（top 0.153846≥0.1）——「reject，未达强 "
            "reject」如实入账。三条机制结论如实单列（不凌驾字母裁决）："
            "①轮内实例方差实测远小于跨轮摆动（r8→r9→r10 0.222222→"
            "0.727273→0.285714 vs 轮内极差 top 0.153846/bottom 0.0）——"
            "度量不稳定的定位从「实例采样」收窄到「跨轮实例群/工具代际」"
            "，r10 定律修正为「跨轮（实例群/工具代际）因素主导，轮内同日"
            "采样相对稳定」；本轮字母 reject 恰恰是有信息量的负结果"
            "（「正确测出无效同样是有效证据」）；②示例 c 效果随实例而异"
            "（top i3 按其边界条款对不规则抖动报非弃权 reroute R11T-018/"
            "020、对规整绕行仍弃权 R11T-006；r10 实例援引同一示例走弃权）"
            "，措辞修改已排程 R12（用户拍板在案）；③多实例聚合口径首次"
            "落地：GT 匹配 union=4/13（0.307692）/agreement=0/13（0.0）"
            "与代表配置 1/13（0.076923）三口径并列——四条逐实例命中无一"
            "被 ≥2 实例同时命中（matched_by_count 全部 ≤1），轮内置信带"
            "（实例间 min..max）首次可用。bottom 7 旗全部弃权=零匹配；"
            "三格零旗标弃权率按 cal._ratio 先例=None（不编造数值）；"
            "「正常特征→不报告」通道继续使用。工具行为混杂如实入账"
            "（8/12 派次 PIL 局部裁剪放大、4/12 纯直读）；输出格式异常"
            "披露（七件 indent=1 重序列化、一件 Write 原文、四件原样；"
            "无围栏剥离）如实登记、均非盲读违规。GT 侧三候选经 gt-audit-"
            "r1 全部关闭（延续零改动，GT 侧不再有候选）。不做「能力已"
            "修复/已达成」类断言；in_calibrated_range 恒 False。本批证据"
            "按协议 v1 §4 属 development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）；多实例"
            "聚合并列口径不构成任何门的放宽或收紧（r11-prep-record "
            "no_loosening_note）。",
            "R10 对照基线=calibration-run-r10.json（622c9099…，在案）；"
            "R8/R9 对照基线=calibration-run-r8.json（3c580eb3…）/r9（"
            "e16420e5…，在案）；轮间对比只做方向性描述。",
            "通道归因方法：照抄 run-r10 channel_attribution 的重放口径"
            "（deviation_note 承接），R10 与 R11 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r11 "
            "channel_attribution.method）。",
            "读者实例行为偏差如实记录：R11 十二派次 8/12 自述对给定 PNG "
            "做 PIL 局部裁剪放大（2-25 处不等；applied-top-i1 第一派次"
            "最重含像素掩膜+字符化像素图+连通域/包围盒测量）、4/12 纯 "
            "Read 直读（applied-bottom-i1/i2/i3、prep1-bottom-i3，逐派次"
            "reading_notes 原文自述在案）；输出格式异常披露（applied-"
            "bottom i2/i3、prep1-top i1/i2/i3、prep1-bottom i2/i3 七件 "
            "json.dump indent=1 重序列化内容逐键忠实、prep1-bottom-i1 "
            "多行缩进 Write 原文、applied-top 三件与 applied-bottom-i1 "
            "紧凑单行原样；无围栏剥离本先例记录）parse 校验全部通过。"
            "跨轮 reader 实例不同+轮内实例差异=混杂因素，每视角 n=3。",
            "假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；"
            "强 reject 分层与机制观察单列，不得凌驾或改写字母裁决；本轮"
            "字母裁决=reject 维持不变（reject≠统计证伪——单轮 n=3 小"
            "样本方向性证据；0.2/0.1 描述性边界与 APR-0011 门分开表述、"
            "互不凌驾：门联合评价（代表配置）=not_met 如实分列）。",
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


def _assert_observation_numbers(run_doc: dict, run_r8: dict, run_r9: dict,
                                run_r10: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 13, "top-i2": 13, "top-i3": 20, "bottom-i1": 2,
                  "bottom-i2": 3, "bottom-i3": 2}:
        _fail("观察文本实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 0, "top-i2": 2, "top-i3": 3, "bottom-i1": 2,
                "bottom-i2": 3, "bottom-i3": 2}:
        _fail("观察文本实例弃权记账与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.133333 or "0.133333（2/15）" not in obs:
        _fail("观察文本代表配置弃权率与实测不一致")
    if run_doc["hypothesis_test"]["verdict"] != "reject":
        _fail("假设字母裁决与预注册判据复算不符")
    if run_doc["hypothesis_test"]["strong_reject_stratification"][
            "claimed"] is not False:
        _fail("强 reject 分层与实测不符")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.153846 \
            or vl["bottom"]["abstain_rate_range"] != 0.0:
        _fail("视角层极差与观察文本不一致")
    if "0.153846" not in obs or "0.226415" not in obs:
        _fail("观察文本缺实测数字（0.153846/0.226415）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 4 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.307692:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (m["flag_id"], m["gt_id"]) for n in INSTANCE_ORDER
        for m in inst[n]["combined"]["matches_detail"])
    if matches_all != [("R11T-003", "GT-REVC-AP-6-R2LED2"),
                       ("R11T-009", "GT-REVC-P1-R4J3"),
                       ("R11T-010", "GT-REVC-AP-1-R5U6"),
                       ("R11T-012", "GT-REVC-P1-L1SHORT")]:
        _fail("matches 明细与观察文本不一致")
    if reroute_production(run_r8["states"]) != 1 \
            or reroute_production(run_r9["states"]) != 0 \
            or reroute_production(run_r10["states"]) != 2 \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] != 3:
        _fail("reroute 类产量与字母裁决输入不一致")
    for need in ("0.222222", "0.727273", "0.285714", "4→12", "14→53",
                 "13/13/20/2/3/2", "0.076923", "0.307692", "R11T-009",
                 "R11T-012", "R11T-010", "R11T-003", "R11T-018", "R11T-020",
                 "R11T-006", "示例 c", "强 reject", "跨轮", "PIL",
                 "0.616745", "1.648816", "0.723377", "0.927745",
                 "0.689959", "r11=3", "None"):
        if need not in obs:
            _fail(f"观察文本缺实测数字/事实 {need}")
    # 通道条目数与文本一致（几何 R10 0→R11 0；类别 R10 0→R11 1）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r11_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r11_category_mismatch_entries"]) != 1:
        _fail("通道条目数与观察文本声明不一致")
    # courtyard 追踪与实测一致（r11 非弃权 courtyard 命中=3）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r11"] != 3 or len(
            ct["r11_courtyard_flags"]["non_abstain"]) != 14:
        _fail("courtyard 追踪计数与实测不一致")
    hits = [r for r in ct["r11_courtyard_flags"]["non_abstain"]
            if r["matches"]]
    if sorted(r["flag_id"] for r in hits) != ["R11T-003", "R11T-009",
                                              "R11T-010"]:
        _fail("courtyard 命中身份与实测不一致")
    # 示例 c/工具行为/bottom 零旗证据摘录逐字在案
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    for ev in mo["example_c_bidirectional_effect"]["evidence"]:
        if ev["excerpt"] not in raw_texts[ev["source"]]:
            _fail(f"示例 c 摘录与 reader 原文不符: {ev['flag_id']}")
    for ev in mo["tool_behavior_evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"工具行为摘录与 reader 原文不符: {ev['source']}")
    for ev in run_doc["courtyard_tracking"]["bottom_observation"]["evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"bottom 零旗证据摘录与 reader 原文不符: {ev['source']}")


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
        _fail("同参重建不一致（byte-exact 破坏）: run-r11")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R11), run_bytes,
                         "calibration-run-r11.json")
    run_sha = _sha(REL_RUN_R11)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round11-dev-record")
    dev_status = _commit(_rel(REL_DEV_RECORD), dev_bytes,
                         "round11-dev-record.json")

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s45-cal-r11] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 41、弃权 12）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s45-cal-r11] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s45-cal-r11] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s45-cal-r11] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range={vl['bottom']['abstain_rate_range']}")
    print(f"[s45-cal-r11] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s45-cal-r11] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    print(f"[s45-cal-r11] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；top 极差 {hyp['measurement']['range_top']}"
          f"/bottom 极差 {hyp['measurement']['range_bottom']}；强 reject "
          f"分层 claimed={hyp['strong_reject_stratification']['claimed']}"
          f"，机制观察单列）")
    print(f"[s45-cal-r11] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s45-cal-r11] channel_attribution: "
          f"geo R10={len(ca['channel_1_geometry_gate']['r10_area_ratio_rejected_entries'])}"
          f"→R11={len(ca['channel_1_geometry_gate']['r11_area_ratio_rejected_entries'])}, "
          f"cat R10={len(ca['channel_2_category_gate']['r10_category_mismatch_entries'])}"
          f"→R11={len(ca['channel_2_category_gate']['r11_category_mismatch_entries'])}")
    print(f"[s45-cal-r11] commit: run={run_status} dev={dev_status}")
    for rel in (REL_RUN_R11, REL_DEV_RECORD):
        print(f"[s45-cal-r11] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s45-cal-r11] R11 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
