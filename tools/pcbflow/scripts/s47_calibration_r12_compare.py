#!/usr/bin/env python
"""CAL-R12-CLOSE：reader 判读迭代第十二轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s45_calibration_r11_compare.py 同构，仅输入与轮次
常量不同；R12=development 域单变量指引侧变更轮（§3A 类别 4 示例 c
「整段规则周期」判据收窄替换；observation-guidance-r12.md=0ac22fcd
由 r9 指引 a0c10154 机械变换生成）+协议侧派发层 v1.2 工具行为规约
（读者不可见，不改判读语义）；渲染 R5 冻结件复用+GT/阈值零变更）；
检验 r11 预注册候选假设（r11-dev-record-candidate-1-example-c-tighten，
判据=r12-prep-record.json hypothesis_test 预注册原文）：

  T1  解析 12 个 reader-raw-r12-*.txt（4 视角格×3 实例；fail-closed：
      非法 JSON 即停止；逐旗标过 calibration fail-closed 校验，被拒者
      如实入拒收清单，reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段）。
  T2  按 r12-prep-record.json measurement_design 五条预注册聚合口径
      执行（先于盲读冻结）：(1) 实例主记录=六实例各自两板合计
      flag_count/abstain_count/abstain_rate（6 位小数；零旗标分母
      =None）/非弃权清单/逐旗 containment+area_ratio 匹配明细；
      (2) 视角层=每视角 3 实例 flag_count/abstain_rate/matches 各
      中位数+min+max 三分列不取整（bottom 弃权率含 None 实例：中位数
      =None、min/max/极差按可计算实例计算并如实注明）；
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
      预注册主通道（滥用型弃权旗计数，操作化定义）逐旗执行：对 reroute
      类弃权旗 location_evidence 做「等长|蛇形」子串 fail-closed 检出
      （子串命中集=程序实测、与登记表逐一相等）后逐条核对形态描述：
      弃权理由**依赖**候选解释（以候选解释为由对非整段周期形态弃权）
      者计滥用型；排除式引用（明写「不适用」候选解释）非依赖、不计；
      实测滥用型=0 且 reroute 类非弃权旗=1≥1（R12T-001 边界报告）
      ⇒ 字母裁决=supported；reroute 总量=3（非零→非「不可判」）。
      机制观察单列（不凌驾字母裁决）：工具规约 v1.2 钉住工具轴
      （12/12 派次自述纯 Read 直读=规约合规）但轮内实例方差反而爆拉
      （top 极差 0.375/bottom 可计算极差 0.95，对比 r11 的 0.153846/
      0.0）——分歧轴转移到 §4(i)「系统性重复 vs 孤立不一致」判据本身
      （bottom 三实例对同一批白色蝶形粘连给出三种裁决）。
      → calibration-run-r12.json。
  T3  development 域记录（本轮性质=指引侧收窄+协议侧 v1.2 首轮；
      R11→R12 方向性对照（只描述不下能力断言）/假设裁决/联合评价趋势
      （r5→r12）/下一迭代目标——延续引用 gt-audit-r1.json（1f20554a…）
      结论：GT 侧已全部关闭；预注册链=round11-dev-record（66e41bbf…）
      →r12-prep-record（d393cf27…）→run-r12；引用 run-r12 落盘 sha
      单向引用）→ round12-dev-record.json。

通道归因纪律（vs R11；方法照抄 s34/s36/s39/s41/s43/s45 deviation_note
口径）：本轮对 R11 与 R12 均以内嵌输入（reader_flags/gt_entries/
flag_views，run sha 在案）+ compare_v3 同源几何原语（calibration.
_containment/_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）
确定性重放通道分类，并与各态 compare_v3 的 matches∪duplicate_reports
对拍复核。跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是
通道级不是旗级。

读者实例披露（如实入账，不作废）：R12 十二派次全部以 Read 工具直读、
自述未做任何裁剪/放大/像素分析等程序化处理（逐派次 reading_notes 原文
自述在案）——协议 v1.2 工具行为规约首轮执行、12/12 派次自述合规；
跨轮实例不同+轮内实例差异=混杂因素照旧声明。输出格式实例披露（编排侧
落盘前处理，盘上件=冻结证据）：12 件均经 json.dump indent=1 重序列化
落盘（内容逐键忠实）；无围栏剥离；12 件 parse 校验全部通过。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r12）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s47_calibration_r12_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-07-r12"
ROUND_LABEL = "r12"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_GUIDANCE_R12 = "out/v3-tl2/calibration/observation-guidance-r12.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
REL_PREP_R9 = "out/v3-tl2/calibration/r9-prep-record.json"
REL_PREP_R10 = "out/v3-tl2/calibration/r10-prep-record.json"
REL_PREP_R11 = "out/v3-tl2/calibration/r11-prep-record.json"
REL_PREP_R12 = "out/v3-tl2/calibration/r12-prep-record.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
REL_DEV_R9 = "out/v3-tl2/calibration/round9-dev-record.json"
REL_DEV_R10 = "out/v3-tl2/calibration/round10-dev-record.json"
REL_DEV_R11 = "out/v3-tl2/calibration/round11-dev-record.json"
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
REL_RUN_R12 = "out/v3-tl2/calibration/calibration-run-r12.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round12-dev-record.json"

#: 12 份盲读原始件（6 实例×2 板；实例内编号跨板连续）。
RAW_FILES = {
    "applied-top-i1":
        "out/v3-tl2/calibration/reader-raw-r12-applied-top-i1.txt",
    "prep1-top-i1":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-top-i1.txt",
    "applied-top-i2":
        "out/v3-tl2/calibration/reader-raw-r12-applied-top-i2.txt",
    "prep1-top-i2":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-top-i2.txt",
    "applied-top-i3":
        "out/v3-tl2/calibration/reader-raw-r12-applied-top-i3.txt",
    "prep1-top-i3":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-top-i3.txt",
    "applied-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r12-applied-bottom-i1.txt",
    "prep1-bottom-i1":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-bottom-i1.txt",
    "applied-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r12-applied-bottom-i2.txt",
    "prep1-bottom-i2":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-bottom-i2.txt",
    "applied-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r12-applied-bottom-i3.txt",
    "prep1-bottom-i3":
        "out/v3-tl2/calibration/reader-raw-r12-prep1-bottom-i3.txt",
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

#: R12 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r12-prep-record renders_reuse.png_witness
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R12 复核见证=r12-prep-record
#: renders_reuse.frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r12-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r12-prep-record.json frozen_input_pdfs_check 实测值；
#: guidance-r12 锚=r12-prep-record.json guidance.sha256 全长（落盘即
#: 冻结）、guidance-r9 锚=其 baseline.sha256_measured 全长；prep-r12
#: 锚=r11-dev-record 锚=任务给定先验（盘上实测一致）；其余沿用 s45
#: 在案锚。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R8:
        "aad43270b1c88d446511737416f3cc191e0f882a925e9e03ef3af1a5ef207993",
    REL_GUIDANCE_R9:
        "a0c10154c4a4c2c7721dbd0a5f12861885e20d09ca0e3d06edc54b1b64e848a8",
    REL_GUIDANCE_R12:
        "0ac22fcd046bf9c3997c84895d4388af0d0dbbfdefd424a8887787ae2be7ea67",
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
    REL_PREP_R12:
        "d393cf2722f797d3f43955cd58e8e1e39846ad31b66903c188ceedefb5f006de",
    REL_DEV_R8:
        "437e149c3ae4d96653111be968f7d80d86ecbca7f6bb42a31f370ec5af78515d",
    REL_DEV_R9:
        "5ee18d61fc1464a92a6e9bbe46d269245748abb836bc07e535a42cff9aa57c43",
    REL_DEV_R10:
        "da4e85f97d216527aa5fd7027392d79d7935d5a79d200695c6b22510d65d628a",
    REL_DEV_R11:
        "66e41bbff7e20208525950c9af3f802e0ddde2746833f05d6bff23f26cf56389",
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
    REL_RUN_R11:
        "ec05e472f97f7cdbff37ea206282fb797a765b6d9f6985b25c5603b7a255d376",
    RAW_FILES["applied-top-i1"]:
        "0f3922151a4e968a49d3bb425aaaaf2db2101b365a9b580bee6f8e40c35d2946",
    RAW_FILES["prep1-top-i1"]:
        "beb500b00c04eb436778209f383a2c7e073005e94a766d56d9a66fed34a82ef2",
    RAW_FILES["applied-top-i2"]:
        "cdda32f143c1de1bf55d81cc59c9dc8e662fe475c6f21eb56a0df01f008a7288",
    RAW_FILES["prep1-top-i2"]:
        "c5cdb5667ab3fd03bf30365db0f933e89c68ff781c0f7e39c7409cb25f75ed4e",
    RAW_FILES["applied-top-i3"]:
        "4b9fdfbe377cbbac3789972bdeb464b930e87ae215a40b52890de0e280d88cf8",
    RAW_FILES["prep1-top-i3"]:
        "babe1ab2dcc5ac984d5bc6f3897ac28128c07c95851f5dec77c496e4dad608f2",
    RAW_FILES["applied-bottom-i1"]:
        "6fc1f6450694869f6ffc6d7111f99711c5f8f7bda2bad30df1256787ed87259c",
    RAW_FILES["prep1-bottom-i1"]:
        "82f470ea027b5e13654fc043b8e5cd7addb871f3600ab6fa58fd5457c4c5f1cd",
    RAW_FILES["applied-bottom-i2"]:
        "4fe3e17d68d72d50ce7f8d02af92d21932d541acc6eaf8ce4d399c39edfe31ff",
    RAW_FILES["prep1-bottom-i2"]:
        "503addb565d8cf391de9ebdf2c6aa1b1a13602b87d77596a211cd11dd47b483b",
    RAW_FILES["applied-bottom-i3"]:
        "e0c0b2d1abc6ff655575b1e81affe8f6b39832c342dce251c8177fd2bff2a4c8",
    RAW_FILES["prep1-bottom-i3"]:
        "914a723bd41ff929c926686b2dc84452f9eb8adb4caedf1d81a37b83015c8355",
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
    "盲读词只含图像路径+observation-guidance-r12.md（0ac22fcd，由 r9 "
    "指引 a0c10154 机械变换生成、落盘即冻结）路径+视角前缀与实例 "
    "reader_id（R12T/R12B 前缀与 reader-r12-{top,bottom}-i{1,2,3} 已随"
    "指引 §6 机械替换落盘固化——与 r11 派发侧覆盖不同，本轮替换随指引"
    "落盘；实例后缀 i{1,2,3} 由派发指令机械补全）+起始序号+v1.2 工具"
    "行为规约硬性条款（禁止对图像做任何程序化处理（裁剪/放大/像素分析/"
    "衍生图像生成等）；判读只允许以 Read 工具查看原图（同一原图可重复"
    "查看））；无任何 GT 坐标/类别提示/期望缺陷描述；读图者不接触 GT/"
    "派生台账/任何校准产物路径；跨实例/跨视角禁止交流（12 次盲读相互"
    "独立——独立性是多实例协议的前提，per r12-prep-record "
    "read_prohibition_note）")

#: 派发模式结构化记录（R12=指引侧收窄+协议侧 v1.2：每格 3 实例、
#: 两波次串行保序；派发结构与 r11 同构，v1.2 规约为唯一新增条款）。
DISPATCH_MODE = {
    "mode": "instance_serial_two_wave",
    "cells": ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"],
    "instances_per_cell": 3,
    "dispatch_count_total": 12,
    "within_instance_serial_order": "同一实例先 applied 后 prep1（flag_id "
                                    "编号跨板连续；实例间编号独立）",
    "flag_id_continuity": {
        "top-i1": "R12T-001..008（applied 001..004→prep1 005..008）",
        "top-i2": "R12T-001..006（applied 001..003→prep1 004..006）",
        "top-i3": "R12T-001..008（applied 001..003→prep1 004..008）",
        "bottom-i1": "R12B-001..020（applied 001..002→prep1 003..020）",
        "bottom-i2": "0 旗（applied 0 旗→prep1 0 旗）",
        "bottom-i3": "R12B-001..002（applied 001..002→prep1 0 旗）",
    },
    "diff_note": ("R11→R12 派发结构同构（12 派次=4 格×3 实例，两波次"
                  "串行保序、同实例先 applied 后 prep1）；本轮变更="
                  "指引侧 §3A 类别 4 示例 c 收窄替换（R12T/R12B 前缀"
                  "已随指引落盘固化，非派发侧覆盖）+协议侧派发层 v1.2 "
                  "工具行为规约硬性条款（12/12 派次自述合规，见 "
                  "reader_instance_note；指引/渲染/GT/阈值实质判据"
                  "通道的其余部分零变更）"),
}

#: 读者实例披露（如实入账，不作废；逐派次以 reading_notes 原文为准）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R12 十二派次全部以 Read 工具"
    "直读内嵌图像、自述未做任何裁剪/放大/像素分析等程序化处理（逐派次 "
    "reading_notes 原文自述在案）——协议 v1.2 工具行为规约（派发指令"
    "硬性条款：禁止程序化图像处理、只允许 Read 直读原图）首轮执行、"
    "12/12 派次自述合规（工具轴钉住；r10/r11 实测 8/12 派次 PIL 局部"
    "裁剪放大的自选异质性在本轮自述口径中为零）；全部判读输入仍严格"
    "限于（指引+该 PNG），零外部信息、零 GT/零其他文件接触=非盲读"
    "违规；跨轮实例不同+轮内实例差异=混杂因素照旧声明（本轮每视角 "
    "n=3 给出轮内实例间范围，轮内样本仍小、development 域只描述不断言"
    "）。输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件"
    "均经 json.dump indent=1 重序列化落盘（内容逐键忠实）；无围栏剥离"
    "本先例记录（r7/r10/r11 有围栏剥离或原样落盘先例，本轮零围栏剥离、"
    "零原样落盘件）；12 件 parse 校验全部通过、均非盲读违规")

#: 逐文件原始消息格式异常（如实入账；盘上件=编排侧落盘后的冻结证据，
#: parse 均为 direct JSON 解析、零 repair）。
_COMPACT_NOTE = "原始消息即紧凑单行 JSON，原样落盘（无格式异常）"
_RESERIALIZED_NOTE = ("原始消息格式不一，编排侧经 json.dump indent=1 "
                      "重序列化落盘（内容逐键忠实；parse 校验通过；非盲读"
                      "违规）")
RAW_MESSAGE_FORMAT_NOTES = {
    "applied-top-i1": _RESERIALIZED_NOTE,
    "applied-top-i2": _RESERIALIZED_NOTE,
    "applied-top-i3": _RESERIALIZED_NOTE,
    "applied-bottom-i1": _RESERIALIZED_NOTE,
    "applied-bottom-i2": _RESERIALIZED_NOTE,
    "applied-bottom-i3": _RESERIALIZED_NOTE,
    "prep1-top-i1": _RESERIALIZED_NOTE,
    "prep1-top-i2": _RESERIALIZED_NOTE,
    "prep1-top-i3": _RESERIALIZED_NOTE,
    "prep1-bottom-i1": _RESERIALIZED_NOTE,
    "prep1-bottom-i2": _RESERIALIZED_NOTE,
    "prep1-bottom-i3": _RESERIALIZED_NOTE,
}

GUIDANCE_NOTE = (
    "本轮指引=observation-guidance-r12.md（0ac22fcd，落盘即冻结）：由 "
    "r9 指引（observation-guidance-r9.md，a0c10154，r11 轮零字节复用件"
    "=指引作者唯一事实源）机械变换生成——恰三类差异：§3A 类别 4 示例 c "
    "收窄替换（r9 增补原文删除，替换为「整段规则周期」判据）；§3A 末尾"
    "（r9 对照说明原位保留、其后、§4 之前）增补一条 r12 对照说明；头部"
    "与 §6 视角前缀/示例 reader-id 机械替换（恰四处：2026-09-07-r9→"
    "2026-09-07-r12、R9T-→R12T-、R9B-→R12B-、reader-r9→reader-r12）。"
    "其余文本逐字承 r9 指引（含 §4 两条对照说明与 §3A r9 对照说明原位"
    "保留）；R12T/R12B 前缀随指引落盘固化（与 r11 派发侧机械覆盖不同）；"
    "指引侧变更=收紧方向（候选解释可用前提收窄、判断责任标准一字未松）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 12 轮迭代"
    "（development 域单变量指引侧变更轮（+协议侧派发层 v1.2 追加式）："
    "迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "单变量指引侧变更轮（§3A 类别 4 示例 c「整段规则周期」判据收窄"
    "替换；observation-guidance-r12.md 由 r9 指引机械变换生成）+协议侧"
    "派发层 v1.2 工具行为规约（读者不可见、不改判读语义）：渲染 R5 "
    "冻结件复用+GT/阈值零变更；判读语义通道的变更变量恰一项（指引侧）")

#: 预注册主通道子串检出对（操作化定义：「等长|蛇形」子串 fail-closed
#: 检出；命中集=程序实测、与逐旗登记表逐一相等，不符即中止）。
MISUSE_SUBSTRINGS = ("等长", "蛇形")

#: 滥用型判定语义（操作化定义的执行细则，随 run-record 落盘）：
#: 滥用型=reroute 类弃权旗的弃权理由**依赖**候选解释（以等长/蛇形候选
#: 解释为由对非整段周期形态弃权）；排除式引用（明写「不适用」候选解释、
#: 弃权理由=存在性无法确认）非依赖、不计滥用型——与 r12-prep-record
#: reject_condition 原文语义（「reader 仍以候选解释为由对非周期形态
#: 弃权」）一致。
MISUSE_RULE_NOTE = (
    "滥用型判定语义（r12-prep-record.json hypothesis_test.support_"
    "condition 操作化定义的执行细则）：对 reroute 类弃权旗 location_"
    "evidence 做「等长|蛇形」子串 fail-closed 检出（命中集=程序实测，"
    "与逐旗登记表 declared_substring_hits 逐一相等，不符即中止）后逐条"
    "核对形态描述（form_desc_excerpt 逐字 substring 校验）：凡弃权理由"
    "**依赖**候选解释（以等长/蛇形候选解释为由对非整段规则周期形态弃权"
    "——引用候选解释且描述为局部波状/抖动/单次大弯折/大范围绕行者）计"
    "滥用型（adjudication=misuse_dependency_citation）；排除式引用"
    "（明写「不适用」候选解释、弃权理由=存在性无法确认）非依赖、不计"
    "（adjudication=exclusion_citation_not_dependency）；子串零命中="
    "未援引候选解释（adjudication=no_candidate_citation）。 reroute 类"
    "非弃权旗不在弃权旗计数范围内、单列为边界报告方向（support 要件）。"
    "逐旗留 substring 证据；判定结果无论方向如实入账")

#: reroute 类旗标逐旗判定登记表（主通道操作化定义执行；摘录与子串命中
#: 均须与 reader-raw 原文实测一致——fail-closed，不符即中止）。
REROUTE_ADJUDICATION = [
    {"source": "applied-top-i1", "flag_id": "R12T-001", "abstain": False,
     "declared_substring_hits": ["蛇形"],
     "form_desc_excerpt": "该形态仅贯穿局部段，并非全程规则周期的蛇形。",
     "adjudication": "non_abstain_boundary_report",
     "note": ("非弃权旗：不在滥用型弃权旗计数范围内（计数范围=reroute "
              "类弃权旗），单列为 reroute 类非弃权旗=support 要件（≥1）"
              "的载体；形态=局部之字/回折且明写「并非全程规则周期的"
              "蛇形」=收窄判据正确适用后按 §4 关注路径报告——边界报告"
              "方向保留（r11 R11T-018/020 同向先例延续）")},
    {"source": "applied-top-i1", "flag_id": "R12T-002", "abstain": True,
     "declared_substring_hits": [],
     "form_desc_excerpt": ("看似呈平滑弯曲/S 形连续弧线，与周边 45° "
                           "折线布线不一致"),
     "adjudication": "no_candidate_citation",
     "note": ("「等长|蛇形」子串零命中（fail-closed 实测=登记一致）="
              "未援引候选解释；弃权理由=存在性无法确认（连续曲线绕行 "
              "vs 短折线视觉效果分辨率不足）——非滥用型")},
    {"source": "prep1-top-i3", "flag_id": "R12T-008", "abstain": True,
     "declared_substring_hits": ["等长", "蛇形"],
     "form_desc_excerpt": ("属仅局部出现的小幅弯折、不构成整段规则周期"
                           "形态（按 r12 收窄判据不适用等长/蛇形候选"
                           "解释）"),
     "adjudication": "exclusion_citation_not_dependency",
     "note": ("子串命中（等长+蛇形）=引用出现，但为**排除式引用**：明写"
              "「按 r12 收窄判据不适用等长/蛇形候选解释」（指引 §3A "
              "示例 c 收窄替换文本的直接适用）、弃权理由=存在性无法"
              "确认（疑为异常弯折或多余残段但无法负责任确认）——引用"
              "非依赖、非「以候选解释为由弃权」，不计滥用型（排除式"
              "引用恰是收窄措辞生效的行为学证据）")},
]

#: v1.2 工具规约合规证据（12/12 派次逐派次 reading_notes 逐字摘录；
#: substring fail-closed 校验）。
READER_TOOL_EVIDENCE = [
    {"source": "applied-top-i1",
     "excerpt": "仅以 Read 工具纯直读给定原图 applied-top.png"},
    {"source": "prep1-top-i1",
     "excerpt": "查看手段为纯 Read 工具直读同一原图"},
    {"source": "applied-top-i2",
     "excerpt": "查看图像的手段为纯 Read 工具直读原图"},
    {"source": "prep1-top-i2",
     "excerpt": "仅使用 Read 工具对原图 prep1-top.png 直接查看"},
    {"source": "applied-top-i3",
     "excerpt": "查看手段为 Read 工具对原图的纯直读"},
    {"source": "prep1-top-i3",
     "excerpt": "仅以 Read 工具直接查看原图 prep1-top.png"},
    {"source": "applied-bottom-i1",
     "excerpt": "仅使用 Read 工具对原图 applied-bottom.png 直接整图查看"},
    {"source": "prep1-bottom-i1",
     "excerpt": "仅以 Read 工具对原图 prep1-bottom.png 直接查看"},
    {"source": "applied-bottom-i2",
     "excerpt": "仅以 Read 工具直读原图 applied-bottom.png 判读"},
    {"source": "prep1-bottom-i2",
     "excerpt": "仅以 Read 工具直读原图 prep1-bottom.png"},
    {"source": "applied-bottom-i3",
     "excerpt": "仅使用 Read 工具直接查看原图共 3 次"},
    {"source": "prep1-bottom-i3",
     "excerpt": "仅以 Read 工具直读原始 PNG（prep1-bottom.png）"},
]

#: §4(i) 判据轴转移证据（bottom 三实例对同一批白色蝶形粘连的三种裁决；
#: 摘录逐字来自 reading_notes/location_evidence 原文；substring 校验）。
CRITERION_AXIS_EVIDENCE = [
    {"source": "prep1-bottom-i1", "kind": "reading_notes", "flag_id": None,
     "instance": "bottom-i1", "verdict": "非弃权 courtyard 18 条",
     "excerpt": "呈孤立、非周期分布，打破所在阵列的均匀分离规律",
     "reading": "§4 启发(ii)孤立不一致→关注现象（18 条非弃权 "
                "courtyard_crowding，R12B-003..020）"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes", "flag_id": None,
     "instance": "bottom-i2", "verdict": "0 旗（两板均零旗标）",
     "excerpt": "白色蝶形连接形态在整个边框阵列上系统性、成体系地重复出现",
     "reading": "§4 判据(i)系统性重复→正常设计特征（三路出口之(1)，"
                "不报告）"},
    {"source": "applied-bottom-i3", "kind": "location_evidence",
     "flag_id": "R12B-002",
     "instance": "bottom-i3", "verdict": "2 条弃权 courtyard",
     "excerpt": "打破周边成对合并的规律节律，但也可能只是上下两行各自的"
                "合并因交错节律而视觉贴近，无法在该分辨率下负责任确认",
     "reading": "疑似打破规律但存在性无法确认→弃权（R12B-001/R12B-002，"
                "低置信 courtyard_crowding）"},
]

#: bottom 零旗标「正常特征→不报告」通道使用证据（逐字摘录）。
BOTTOM_ZERO_EVIDENCE = [
    {"source": "applied-bottom-i2", "kind": "reading_notes",
     "excerpt": "故本图 flags 为空"},
    {"source": "prep1-bottom-i2", "kind": "reading_notes",
     "excerpt": "综合：本图无可负责任报告的 DRC 类关注点，flags 为空"},
    {"source": "prep1-bottom-i3", "kind": "reading_notes",
     "excerpt": "故无弃权旗；flags 为空"},
]


def _fail(msg: str) -> None:
    print(f"[s47-cal-r12] FAIL: {msg}")
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

    R12 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                    "note": ("R12 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮单变量指引侧变更轮（示例 c "
                             "收窄）+协议侧派发层 v1.2 工具规约）")},
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
    abstain_rate = cal._ratio(n_ab, n_fl)
    if abstain_rate is None:
        arith = ("abstain_rate = %d/%d = None（零旗标分母，按库侧 "
                 "cal._ratio 先例=None，measurement_design item 5；"
                 "不编造数值）" % (n_ab, n_fl))
    else:
        arith = ("abstain_rate = %d/%d = %s（分母=该实例该视角全部旗标，"
                 "跨两板合计；measurement_design item 1）"
                 % (n_ab, n_fl, abstain_rate))
    return {
        "instance": name, "view": view,
        "reader_id": parsed[spec["parts"][0]]["reader_id"],
        "parts": {"applied": spec["parts"][0], "prep1": spec["parts"][1]},
        "states": {"applied": blk_appl, "prep1": blk_prep},
        "combined": {
            "flag_count": n_fl,
            "abstain_count": n_ab,
            "scored": n_sc,
            "abstain_rate": abstain_rate,
            "abstain_rate_arithmetic": arith,
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
    """视角层聚合（measurement_design item 2；每视角 3 实例三分列）。

    bottom 弃权率含 None 实例（bottom-i2 零旗标分母，item 5 口径）：
    中位数含 None 无法定义→None（不编造数值）；min/max/极差按可计算
    实例计算并如实注明（None 实例不计入、如实标注）。
    """
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
        computable = [v for v in ar_vals if v is not None]
        none_names = [n for n in names if ar[n] is None]
        if none_names:
            ar_median = None
            ar_min, ar_max = min(computable), max(computable)
            ar_range = cal._round6(ar_max - ar_min)
            ar_median_note = (
                "弃权率中位数含 None 实例（%s 零旗标分母→None，cal._ratio "
                "先例、measurement_design item 5）无法定义→None（不编造"
                "数值）；min/max 按可计算实例（%s）计算"
                % ("/".join(none_names),
                   "/".join(n for n in names if ar[n] is not None)))
            range_arithmetic = (
                "实例间弃权率极差（max−min，按可计算实例）= %s − %s = %s"
                "（%s = %s/%s/%s；%s 零旗标分母→None 不计入、如实注明——"
                "measurement_design item 5 口径）"
                % (ar_max, ar_min, ar_range,
                   "/".join(names), ar_vals[0], ar_vals[1], ar_vals[2],
                   "/".join(none_names)))
        else:
            ar_median = _median3(ar_vals)
            ar_median_note = "三实例弃权率均有定义（中位数=排序后第 2）"
            ar_min, ar_max = min(ar_vals), max(ar_vals)
            ar_range = cal._round6(ar_max - ar_min)
            range_arithmetic = (
                "实例间弃权率极差（max−min）= %s − %s = %s（%s/%s/%s = "
                "%s/%s/%s）"
                % (ar_max, ar_min, ar_range, names[0], names[1], names[2],
                   ar_vals[0], ar_vals[1], ar_vals[2]))
        ar_block = {
            "by_instance": ar,
            "median": ar_median,
            "min": ar_min,
            "max": ar_max,
        }
        if none_names:
            ar_block["median_note"] = ar_median_note
        out[view] = {
            "instances": names,
            "flag_count": {"by_instance": fc,
                           "median": _median3(fc_vals),
                           "min": min(fc_vals), "max": max(fc_vals)},
            "abstain_rate": ar_block,
            "matches": {"by_instance": mt,
                        "median": _median3(mt_vals),
                        "min": min(mt_vals), "max": max(mt_vals)},
            "abstain_rate_range": ar_range,
            "abstain_rate_range_arithmetic": range_arithmetic,
        }
    return out


def build_gt_dual(instances: dict, gt_applied: list, gt_prep1: list) -> dict:
    """GT 匹配聚合双口径（measurement_design item 3）。

    逐 GT 条目 matched_by_count（0..3）=同视角 3 实例中命中该条目的
    实例数（命中判定=该实例对应态 compare_v3 的 matches 含该 gt_id，
    即逐旗 containment/area_ratio 过门+一对一指派后在 GT 条目上归并）；
    union（≥1 实例命中即计）与 agreement（≥2/3 实例命中才计）两口径
    并列；召回分母=GT 13 条；bottom 无 GT 在案（gt-audit-r1：bottom
    GT=无源已关闭）⇒ bottom 旗标与 GT 匹配应为空（如实）。
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
        "denominator_note": ("召回分母=GT 13 条（applied 9+prep1 4；"
                            "全部 side=top——bottom 无 GT 在案 "
                            "gt-audit-r1：bottom GT=无源已关闭，bottom "
                            "旗标与 GT 匹配应为空，如实）"),
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
    """两态联合聚合（照 s45 口径；此处置于代表配置）。"""
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
        rates = [c["abstain_rate"] for c in comb]
        computable = [r for r in rates if r is not None]
        none_names = [n for n, r in zip(names, rates) if r is None]
        rate_block = {
            "min": min(computable) if computable else None,
            "max": max(computable) if computable else None,
        }
        if none_names:
            rate_block["note"] = (
                "%s 零旗标分母→abstain_rate=None（cal._ratio 先例、"
                "measurement_design item 5）；min/max 按可计算实例（%s）"
                "计算，不编造数值" % ("/".join(none_names),
                                    "/".join(n for n, r in
                                             zip(names, rates)
                                             if r is not None)))
        out[view] = {
            "instances": names,
            "flag_count": {"min": min(c["flag_count"] for c in comb),
                           "max": max(c["flag_count"] for c in comb)},
            "abstain_count": {"min": min(c["abstain_count"] for c in comb),
                              "max": max(c["abstain_count"] for c in comb)},
            "abstain_rate": rate_block,
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
                 "配置全部旗标）；APR-0011 阈值零改动，与预注册主通道"
                 "判据各自独立计算、互不凌驾"},
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
                       "r11": "not_met（在案）",
                       "r12": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": ("本轮联合评价未达标（代表配置 gt_recall 0.0 与 "
                     "seed_match_rate 0.0 与 abstain_rate 0.9 三项未达"
                     "暂行线；gt_count 13≥12 达线），连续计数仍"
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
# 逐旗失败通道归因（vs R11；方法照抄 s34/s36/s39/s41/s43/s45：
# 通道级，非旗级）
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


def reroute_abstain_nonabstain(states: dict) -> tuple:
    """reroute 类弃权/非弃权旗数（弃权旗=滥用型计数的作用域）。"""
    ab = non = 0
    for blk in states.values() if isinstance(states, dict) else states:
        for f in blk["reader_flags"]:
            if f["category"] == "suspicious_reroute":
                if f["abstain"]:
                    ab += 1
                else:
                    non += 1
    return ab, non


def build_channel_attribution(run_r6: dict, run_r7: dict, run_r8: dict,
                              run_r9: dict, run_r11: dict,
                              inst_blocks: list, inst_replays: dict) -> dict:
    """通道归因小节（vs R11；通道级分组，非旗级配对；链自 r6 衔接）。"""
    # R11 十二件以内嵌输入重放并与各态 compare_v3 对拍（run sha 在案）
    r11_replays = {}
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            blk = run_r11["instances"][name]["states"][st]
            rp = channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
            if not replay_matches_agree(rp, blk["compare_v3"]):
                _fail(f"R11 {name}/{st} 通道重放与 compare_v3 对拍不一致")
            r11_replays[(name, st)] = rp
    for key, rp in inst_replays.items():
        blk = next(b for b in inst_blocks if b["_part_key"] == key)
        if not replay_matches_agree(rp, blk["compare_v3"]):
            _fail(f"R12 {key} 通道重放与 compare_v3 对拍不一致")

    def pick_r12(failure):
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

    def pick_r11(failure):
        rows = []
        for name in INSTANCE_ORDER:
            for st in ("applied", "prep1"):
                for e in r11_replays[(name, st)]["entries"]:
                    if e["failure"] == failure:
                        rows.append(_channel_entry(dict(
                            e, state=st, instance=name)))
        rows.sort(key=lambda x: (x["instance"], x["state"], x["flag_id"],
                                 x["gt_id"]))
        return rows

    geo_r11 = pick_r11("area_ratio_rejected")
    geo_r12 = pick_r12("area_ratio_rejected")
    cat_r11 = pick_r11("category_mismatch")
    cat_r12 = pick_r12("category_mismatch")
    view_r11 = pick_r11("view_gate")
    view_r12 = pick_r12("view_gate")
    # 与 run-r11 在案登记交叉核对（fail-closed：重放结果须与在案一致）
    if geo_r11 != run_r11["channel_attribution"]["channel_1_geometry_gate"][
            "r11_area_ratio_rejected_entries"]:
        _fail("R11 几何门重放与 run-r11 在案登记不一致")
    if cat_r11 != run_r11["channel_attribution"]["channel_2_category_gate"][
            "r11_category_mismatch_entries"]:
        _fail("R11 类别门重放与 run-r11 在案登记不一致")
    if view_r11 != run_r11["channel_attribution"][
            "view_gate_observations"]["r11_entries"]:
        _fail("R11 视角门重放与 run-r11 在案登记不一致")

    geo_change = (
        "几何门通道（R11→R12）：面积比出局条目 0→0（R7 起连续空；无回升，"
        "guard 通道要求满足）——r12 非弃权旗 25 条与同态 GT 的近邻交叠"
        "条目为空集：top 非弃权旗与同态 GT 零 ≥0.5 containment 交叠；"
        "bottom 非弃权旗 19 条（18 courtyard+1 placement）与 GT（13 条"
        "全部 side=top；bottom 无 GT 在案 gt-audit-r1）零 ≥0.5 "
        "containment 交叠；§3 收窄判据守门无回升。")
    cat_change = (
        "类别门通道（R11→R12）：类别不符出局条目 1→0（r12 重放零类别门"
        "条目；R11T-012↔GT-REVC-AP-8-R1Q2 为 r11 唯一条目、本轮无再现）"
        "；多实例样本量极小，只描述不断言。")

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
            "r10": len(run_r11["channel_attribution"][
                "channel_1_geometry_gate"]["r10_area_ratio_rejected_entries"]),
            "r11": len(geo_r11),
            "r12": len(geo_r12),
        },
        "category_gate_category_mismatch_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_2_category_gate"),
            "r7": _gate_count(run_r7, 7, "channel_2_category_gate"),
            "r8": _gate_count(run_r8, 8, "channel_2_category_gate"),
            "r9": _gate_count(run_r9, 9, "channel_2_category_gate"),
            "r10": len(run_r11["channel_attribution"][
                "channel_2_category_gate"]["r10_category_mismatch_entries"]),
            "r11": len(cat_r11),
            "r12": len(cat_r12),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0→r10=0→r11=0→r12=0；类别门 "
                 "r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→r12=0（R12 零条目；"
                 "r11 唯一条目 R11T-012↔AP-8 本轮无再现）"),
    }
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R12, "sha256": _sha(REL_PREP_R12)},
            "declaration": (
                "本轮恰两项变更变量（指引侧单变量=示例 c 收窄替换、协议侧"
                "派发层=v1.2 工具行为规约）、检验恰一个假设（round11-dev-"
                "record next_iteration_targets[1]；hypothesis_id=r11-dev-"
                "record-candidate-1-example-c-tighten）；归因分层：reroute "
                "类主通道指标主要归因于措辞收窄（工具规约不改变分类判据"
                "语义）（r12-prep-record.json attribution_plan.declaration "
                "原文）"),
            "primary_channel": {
                "change_id": "reroute-example-c-full-segment-periodic-"
                             "tighten（指引侧单变量）",
                "metric": prep_doc_primary_channel_metric(),
            },
            "guard_channel": {
                "metric": "其余类别非弃权旗 frame_box_pct 几何门（面积比"
                          "出局条目）",
                "requirement": ("§3 收窄判据零变更（逐字承 r9 指引），非"
                                "弃权框仍须满足；几何门面积比出局条目无"
                                "回升"),
            },
        },
        "method": {
            "source_of_r11_detail": (
                "calibration-run-r11.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39/s41/s43/s45 deviation_note 口径："
                "本轮对 R11 与 R12 均以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5（含 None=无交集）"
                "无条目；近邻且视角不符=view_gate；近邻且面积比>上限="
                "area_ratio_rejected（几何门）；近邻且面积比≤上限且类别"
                "不符=category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r11_candidate_pairs_by_instance_state": {
                    f"{name}/{st}": [list(p) for p in
                                     r11_replays[(name, st)]
                                     ["candidate_pairs"]]
                    for name in INSTANCE_ORDER
                    for st in ("applied", "prep1")},
                "r12_candidate_pairs_by_part": {
                    key: [list(p) for p in inst_replays[key]
                          ["candidate_pairs"]] for key in RAW_FILES},
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R11 十二件复算与 "
                         "run-r11 在案一致：恰 4 候选对=4 matches；R12 "
                         "十二件重放全部复现：候选对=空集，matches=0）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R11T/R11B 与 R12T/R12B 来自"
            "不同 reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r11_area_ratio_rejected_entries": geo_r11,
            "r12_area_ratio_rejected_entries": geo_r12,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r11_category_mismatch_entries": cat_r11,
            "r12_category_mismatch_entries": cat_r12,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r11_entries": view_r11,
            "r12_entries": view_r12,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮重放"
                     "均无视角门条目——r11 bottom 7 旗全部弃权；r12 "
                     "bottom 非弃权旗 19 条（bottom-i1 18 courtyard+1 "
                     "placement）与同态 GT 零 ≥0.5 containment 交叠"
                     "（GT 13 条全部 side=top；bottom 无 GT 在案 "
                     "gt-audit-r1：bottom GT=无源已关闭⇒bottom 旗标与 "
                     "GT 匹配应为空，如实）。"),
        },
        "gate_chain_since_r6": chain,
        "r12_specific_observations": [
            "R12 六实例 44 旗标（非弃权 25、弃权 19）中，matches（逐实例"
            "逐态 compare_v3）合计 0 条：GT 条目层 union=0/13（0.0）、"
            "agreement=0/13（0.0）、代表配置 gt_recall_total=0/13（0.0）"
            "——r11 的 4 条逐实例命中（union 4/13）本轮零再现；bottom 19 "
            "条非弃权旗零匹配属结构性（GT 13 条全部 side=top，bottom GT "
            "无源在案 gt-audit-r1）；top 非弃权旗 6 条（1 reroute+2 "
            "courtyard+3 silk）与同态 GT 零 ≥0.5 containment 交叠。",
            "R12 suspicious_reroute 旗标 3 条：R12T-001（top-i1 applied，"
            "非弃权边界报告）+R12T-002（top-i1 applied，弃权）+R12T-008"
            "（top-i3 prep1，弃权）；逐实例产量 top-i1=2/top-i3=1；"
            "r8=1→r9=0→r10=2→r11=3→r12=3；构成变化：r11（1 弃权+2 "
            "非弃权，全部 top-i3）→r12（1 非弃权+2 弃权，跨 top-i1/"
            "top-i3）；滥用型弃权旗 r10=2→r11=1→r12=0（主通道，见 "
            "hypothesis_test）。",
            "R12 类别门 0 条（r11=1 条后归零）；几何门连续第 6 轮为空；"
            "视角门两轮均空。",
            "courtyard 被动追踪（prep-record 预注册）：非弃权 courtyard "
            "旗 20 条（top-i2 R12T-001、top-i3 R12T-001、bottom-i1 "
            "R12B-003..020 共 18 条）零命中；bottom 18 条因 GT 全部 "
            "side=top 无从命中（bottom GT 无源在案）；courtyard 匹配 "
            "r8=1→r9=0→r10=1→r11=3→r12=0；GT/阈值零改动、零期望"
            "（run-r12 courtyard_tracking 节）。",
        ],
    }


def prep_doc_primary_channel_metric() -> str:
    """主通道度量文本（取自 r12-prep-record attribution_plan）。"""
    return _json_load(REL_PREP_R12)["attribution_plan"]["primary_channel"][
        "metric"]


# ---------------------------------------------------------------------------
# 预注册假设（r11-dev-record-candidate-1-example-c-tighten）裁决
# （字母裁决+主通道滥用型操作化逐旗判定+机制观察单列）
# ---------------------------------------------------------------------------

def verify_reroute_adjudication(instances: dict, raw_texts: dict) -> list:
    """主通道逐旗判定（操作化定义执行；fail-closed）。

    对 reroute 类旗标全列逐旗：
    - 子串命中集=程序实测（MISUSE_SUBSTRINGS 对 location_evidence），
      须与登记表 declared_substring_hits 逐一相等（含顺序）；
    - form_desc_excerpt 逐字 substring 校验（防转述失真）；
    - abstain 属性与登记表一致；
    - 滥用型=adjudication == "misuse_dependency_citation"（弃权理由依赖
      候选解释）；排除式引用/零命中不计。
    返回逐旗判定行（含实测子串与证据），并在不符时中止。
    """
    declared = {row["flag_id"]: row for row in REROUTE_ADJUDICATION}
    live = []
    for name in INSTANCE_ORDER:
        for d in instances[name]["per_flag_gt_detail"]:
            if d["category"] != "suspicious_reroute":
                continue
            fid = d["flag_id"]
            if fid not in declared:
                _fail(f"reroute 旗标缺逐旗判定登记: {fid}")
            row = declared[fid]
            # 取原始 location_evidence（raw 原文）
            loc = None
            for key, rel in RAW_FILES.items():
                if key != row["source"]:
                    continue
                doc = json.loads(_rel(rel).read_text(encoding="utf-8"))
                for img in doc["per_image"]:
                    for f in img["flags"]:
                        if f["flag_id"] == fid:
                            loc = f["location_evidence"]
            if loc is None:
                _fail(f"逐旗判定登记 source/flag_id 与盘上件不符: {fid}")
            hits = [s for s in MISUSE_SUBSTRINGS if s in loc]
            if hits != row["declared_substring_hits"]:
                _fail(f"子串命中实测与登记不符: {fid} "
                      f"实测={hits} 登记={row['declared_substring_hits']}")
            if row["form_desc_excerpt"] not in raw_texts[row["source"]]:
                _fail(f"形态描述摘录与 reader 原文不符: {fid}")
            if row["abstain"] is not d["abstain"]:
                _fail(f"登记 abstain 与实例明细不符: {fid}")
            live.append({
                "source": row["source"], "flag_id": fid,
                "instance": name, "state": d["state"],
                "abstain": d["abstain"],
                "detected_substring_hits": hits,
                "declared_substring_hits": row["declared_substring_hits"],
                "form_desc_excerpt": row["form_desc_excerpt"],
                "adjudication": row["adjudication"],
                "misuse": row["adjudication"] == "misuse_dependency_"
                                                 "citation",
                "note": row["note"]})
    live.sort(key=lambda r: (r["instance"], r["flag_id"]))
    if len(live) != len(REROUTE_ADJUDICATION):
        _fail("逐旗判定登记表与实测 reroute 旗标数不符")
    return live


def build_hypothesis_test(run_r8: dict, run_r9: dict, run_r10: dict,
                          run_r11: dict, instances: dict, view_layer: dict,
                          attribution: dict, raw_texts: dict,
                          parsed_notes: dict, reroute_rows: list) -> dict:
    """假设（r11-dev-record-candidate-1-example-c-tighten）裁决节（预注册
    判据执行；字母裁决唯一正式+机制观察单列）。

    字母裁决（唯一正式裁决）=判据 r12-prep-record.json hypothesis_test
    原文：support=「滥用型弃权旗=0（操作化定义：对 reroute 类弃权旗的
    location_evidence 做「等长|蛇形」子串 fail-closed 检出后，逐条核对
    形态描述——凡引用候选解释且描述为局部波状/抖动/单次大弯折/大范围
    绕行者计滥用型）且 reroute 类非弃权旗≥1（边界报告方向保留）」；
    reject=「滥用型弃权旗≥1」；reroute 类旗标总量=0 → 记「不可判」。
    实测 reroute 总量=3（非零）、滥用型=0（逐旗判定：R12T-002 子串零
    命中=未援引；R12T-008 排除式引用非依赖）、reroute 类非弃权旗=1
    （R12T-001 边界报告）⇒ 字母裁决=supported。0.2/0.1 类描述性边界
    本轮无（判据=计数型）；与 APR-0011 门各自独立计算、互不凌驾、
    run-record 内分开表述。机制观察单列、不凌驾、不改写字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R12)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    # 预注册链交叉核对（r11-dev-record 锚已在 FROZEN_SHA256 校验；
    # 其 next_iteration_targets 被本 prep-record 逐字摘录预注册）
    dev11 = _json_load(REL_DEV_R11)
    ref = ht["preregistration_ref"]
    if ref["path_rel"] != REL_DEV_R11 or \
            dev11["next_iteration_targets"][ref["item_indices_zero_based"][0]] \
            != ht["preregistered_criteria_quote"]["candidate_0_target"]:
        _fail("prep-record 预注册摘录（candidate_0）与 round11-dev-record "
              "原文不符")
    if dev11["next_iteration_targets"][ref["item_indices_zero_based"][1]] \
            != ht["preregistered_criteria_quote"]["candidate_1_target"]:
        _fail("prep-record 预注册摘录（candidate_1）与 round11-dev-record "
              "原文不符")
    # 基线数字与在案 run 交叉核对（fail-closed）
    base = ht["baseline_reference"]
    r10_ab, _r10_non = reroute_abstain_nonabstain(run_r10["states"])
    # run-r11 为六实例结构（无顶层 states）：逐实例态块合并计数
    r11_ab = r11_non = 0
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            blk = run_r11["instances"][name]["states"][st]
            for f in blk["reader_flags"]:
                if f["category"] == "suspicious_reroute":
                    if f["abstain"]:
                        r11_ab += 1
                    else:
                        r11_non += 1
    if base["r10"]["misuse_abstain_flag_count"] != r10_ab:
        _fail("prep-record r10 滥用型基线与 run-r10 实测不符")
    if base["r11"]["misuse_abstain_flag_count"] != r11_ab:
        _fail("prep-record r11 滥用型基线与 run-r11 实测不符")
    if base["r11"]["boundary_non_abstain_reroute_count"] != r11_non:
        _fail("prep-record r11 非弃权 reroute 基线与 run-r11 实测不符")
    if reroute_production(run_r8["states"]) != 1 \
            or reroute_production(run_r9["states"]) != 0 \
            or reroute_production(run_r10["states"]) != 2 \
            or run_r11["reader"]["flag_count"]["reroute_class_production"] \
            != 3:
        _fail("reroute 类产量链与在案 run 不符")

    # 主通道实测（操作化逐旗判定）
    misuse_rows = [r for r in reroute_rows if r["abstain"]]
    misuse_count = sum(1 for r in misuse_rows if r["misuse"])
    non_abstain_rows = [r for r in reroute_rows if not r["abstain"]]
    reroute_total = len(reroute_rows)
    supported = (misuse_count == 0) and (len(non_abstain_rows) >= 1)
    rejected = misuse_count >= 1
    undeterminable = reroute_total == 0
    if supported == rejected:
        _fail("主通道判定自洽性破坏（support 与 reject 互斥）")
    verdict = ("undeterminable" if undeterminable
               else ("supported" if supported else "reject"))
    verdict_text = (
        "按预注册判据（r12-prep-record.json hypothesis_test 原文）=支持"
        "（字母口径，唯一正式裁决）：12 次盲读 reroute 类旗标总量=3"
        "（非零→非「不可判」）；滥用型弃权旗=0（操作化定义逐旗执行："
        "R12T-002「等长|蛇形」子串零命中=未援引候选解释；R12T-008 子串"
        "命中为**排除式引用**（明写「按 r12 收窄判据不适用等长/蛇形候选"
        "解释」=指引收窄文本的直接适用）非依赖——无「以候选解释为由对"
        "非整段周期形态弃权」的滥用型旗标）且 reroute 类非弃权旗=1≥1"
        "（R12T-001 边界报告：形态局部之字回折、明写并非全程规则周期"
        "蛇形——收窄判据正确适用后的关注路径报告，边界报告方向保留）"
        "⇒ support_condition 满足。注意：supported≠假设被证实的统计"
        "证明——单轮 n=3、跨轮实例群混杂照旧（development 域只描述"
        "不断言）；「正确测出无效同样是有效证据」的对称面=支持结果同样"
        "只作方向性证据；机制观察单列（工具规约钉住工具轴≠判读一致，"
        "§4(i) 判据轴成为新的不稳定轴），不凌驾、不改写字母裁决；"
        "APR-0011 门（代表配置）=not_met 与裁决=supported 分列不合并。")
    # 证据摘录逐字校验（v1.2 工具规约合规 12/12 + §4(i) 三裁决）
    for ev in READER_TOOL_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"工具规约合规摘录与 reader 原文不符: {ev['source']}")
    for ev in CRITERION_AXIS_EVIDENCE:
        if ev["kind"] == "reading_notes":
            if ev["excerpt"] not in parsed_notes[ev["source"]]:
                _fail(f"判据轴证据摘录与 reader 原文不符: {ev['source']}")
        else:
            if ev["excerpt"] not in raw_texts[ev["source"]]:
                _fail(f"判据轴证据摘录与 reader 原文不符: {ev['flag_id']}")
    for ev in BOTTOM_ZERO_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"bottom 零旗证据摘录与 reader 原文不符: {ev['source']}")
    reroute_r8 = reroute_production(run_r8["states"])
    reroute_r9 = reroute_production(run_r9["states"])
    reroute_r10 = reroute_production(run_r10["states"])
    reroute_by_instance = {
        n: sum(1 for d in instances[n]["per_flag_gt_detail"]
               if d["category"] == "suspicious_reroute")
        for n in INSTANCE_ORDER}
    reroute_r12 = sum(reroute_by_instance.values())
    geo_r12 = attribution["channel_1_geometry_gate"][
        "r12_area_ratio_rejected_entries"]
    geo_r11 = attribution["channel_1_geometry_gate"][
        "r11_area_ratio_rejected_entries"]
    guard_ok = len(geo_r12) == 0 and len(geo_r12) <= len(geo_r11)
    top_range = view_layer["top"]["abstain_rate_range"]
    bottom_range = view_layer["bottom"]["abstain_rate_range"]
    top_rates = view_layer["top"]["abstain_rate"]["by_instance"]
    bottom_rates = view_layer["bottom"]["abstain_rate"]["by_instance"]
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=supported "
                 "不因本观察改写）"),
        "tool_axis_pinned_vs_criterion_axis": {
            "observation": (
                "工具规约 v1.2 钉住了工具轴：12/12 派次自述纯 Read 直读"
                "、未做任何裁剪/放大/像素分析等程序化处理（逐派次 "
                "reading_notes 原文自述在案；r10/r11 实测 8/12 派次自选 "
                "PIL 局部裁剪放大的工具异质性在本轮自述口径中为零）——"
                "但轮内实例方差反而爆拉：top 弃权率极差 0.375（0.875/"
                "0.833333/0.5）、bottom 可计算极差 0.95（0.05/None/1.0），"
                "对比 r11 的 top 0.153846/bottom 0.0——分歧轴从工具行为"
                "转移到 §4(i)「系统性重复 vs 孤立不一致」判据本身：bottom "
                "三实例对同一批白色蝶形粘连给出三种裁决（bottom-i1=18 条"
                "非弃权 courtyard「孤立、打破规律」/bottom-i2=0 旗「系统"
                "性重复→正常」/bottom-i3=2 弃权旗「疑似合并异常无法确认」"
                "）；top i1/i2（0.875/0.833333）与 top i3（0.5）的弃权率"
                "分化亦大。即：工具行为一致 ≠ 判读一致；§4(i) 判据在纯"
                "直读分辨率下是新的不稳定轴（如实单列；不构成已证因果"
                "关系，样本量极小）。"),
            "tool_evidence": READER_TOOL_EVIDENCE,
            "tool_evidence_check": ("12/12 派次摘录逐字来自对应 "
                                    "reading_notes（substring fail-closed "
                                    "校验通过）"),
            "reader_note_evidence": CRITERION_AXIS_EVIDENCE,
            "reader_note_evidence_check": ("摘录逐字来自对应 reader-raw（"
                                           "reading_notes/location_evidence "
                                           "原文；substring fail-closed "
                                           "校验通过）"),
            "status": ("r11 机制结论（「跨轮实例群/工具代际主导，轮内同日"
                       "采样相对稳定」）的本轮修正证据：工具轴钉住后轮内"
                       "方差不降反升——轮内不稳定的主要来源不在工具行为，"
                       "而在判据语义（§4(i)）在低分辨率直读下的解释空间"),
        },
        "within_vs_cross_round_variance": {
            "observation": (
                "轮内视角极差 top 0.375（0.875−0.5）/bottom 可计算 0.95"
                "（1.0−0.05；bottom-i2 零旗标→None 不计入、如实注明）"
                "vs r11 的 top 0.153846/bottom 0.0——v1.2 工具规约钉住"
                "工具轴后轮内一致性未如预期维持小带（prep-record "
                "secondary_observation 预期「实例间弃权率极差维持小带」"
                "未发生，如实记录、不预设）；跨轮聚合弃权率链 r9 0.727273"
                "→r10 0.285714→r11 代表配置 0.133333→r12 代表配置 "
                "0.285714（口径分列如实）。"),
            "cross_round_abstain_rates": {
                "r9": run_r9["aggregation"]["abstain_rate_total"],
                "r10": run_r10["aggregation"]["abstain_rate_total"],
                "r11_representative":
                    run_r11["aggregation_representative"][
                        "abstain_rate_total"],
                "r12_representative_note": (
                    "见 aggregation_representative.abstain_rate_total"
                    "（代表配置口径，measurement_design item 4）"),
            },
            "within_round_ranges": {
                "r11": {"top": 0.153846, "bottom": 0.0},
                "r11_source": ("run-r11 在案（run sha ec05e472…）；引用"
                               "在案值"),
                "r12": {"top": top_range, "bottom_computable": bottom_range,
                        "bottom_note": ("bottom-i2 零旗标分母→None 不计入"
                                        "极差（measurement_design item 5）")},
            },
            "status": ("轮内方差爆拉与主通道 supported 并存：措辞收窄在"
                       "reroute 类通道的行为学信号成立（滥用型清零+排除式"
                       "引用出现），但 §4(i) 判据轴的不稳定被工具钉住后"
                       "显形——「正确测出无效同样是有效证据」的同构：测出"
                       "新不稳定轴同样是有效证据"),
        },
        "reroute_flag_production": {
            "r8": reroute_r8,
            "r8_detail": "R8T-014（弃权旗；run-r8 在案）",
            "r9": reroute_r9,
            "r9_detail": "四份 r9 原始件零 suspicious_reroute 旗标（run-r9 在案）",
            "r10": reroute_r10,
            "r10_detail": ("R10T-012/R10T-013（均弃权；location_evidence "
                           "明确引用「r9 示例 c」判据=滥用型基线 2）"),
            "r11": run_r11["reader"]["flag_count"][
                "reroute_class_production"],
            "r11_detail": ("R11T-006（弃权，滥用型基线 1）+R11T-018/"
                           "R11T-020（非弃权边界报告 2），全部出自 "
                           "top-i3"),
            "r12": reroute_r12,
            "r12_by_instance": reroute_by_instance,
            "r12_detail": ("R12T-001（非弃权边界报告 1，top-i1）+R12T-002"
                           "（弃权、未援引候选解释，top-i1）+R12T-008"
                           "（弃权、排除式引用，top-i3）——构成变化：r11 "
                           "1 弃权+2 非弃权（全 top-i3）→r12 1 非弃权+"
                           "2 弃权（跨 top-i1/top-i3）"),
            "misuse_chain": {"r10": r10_ab, "r11": r11_ab,
                             "r12": misuse_count,
                             "note": ("滥用型弃权旗计数（主通道）：基线 "
                                      "r10=2（R10T-012/013 援引候选解释"
                                      "弃权）→r11=1（R11T-006「形态规整但"
                                      "不呈规则周期折叠」援引候选解释弃权）"
                                      "→r12=0（本轮实测）——收窄措辞生效"
                                      "获支持（字母裁决=supported）"),
                             "non_abstain_chain": {
                                 "r11": r11_non, "r12": len(non_abstain_rows),
                                 "note": ("reroute 类非弃权旗（边界报告"
                                          "方向）：r11=2（R11T-018/020）→"
                                          "r12=1（R12T-001）——保留（"
                                          "support 要件 ≥1 满足）")},
                             },
        },
    }
    metric_design_lesson = {
        "role": ("度量设计教训（如实，供未来预注册参考；本轮不追溯"
                 "适用）"),
        "lesson": (
            "本轮主通道=滥用型弃权旗计数（构成分析，预注册操作化定义逐旗"
            "执行），实测 0→字母裁决=supported；并列预注册的轮内一致性"
            "观察（secondary_observation 预期「实例间弃权率极差维持小带」"
            "）实测 top 0.375/bottom 可计算 0.95——预期未发生。构成分析"
            "通道（计数）与聚合通道（极差）在同一轮一正一反：单轮单一"
            "聚合读数（如全旗标弃权率）不足以定位效果，逐旗构成+逐实例"
            "分列是必要口径（r9→r12 教训链延续：产量计数+构成分析互补、"
            "逐实例如实分列不聚合掩盖）。"),
        "status": ("下一轮候选教训（如实登记）：§4(i)「系统性重复 vs "
                   "孤立不一致」判据的可操作性修订候选（如「系统性重复」"
                   "的量化判据/至少 n 处重复的阈值化措辞）若排程，属指引"
                   "侧变更、须预注册+单变量纪律，且不得反向放宽（反放宽"
                   "条款与三路出口保留）；不得回溯改判既往轮次（r8–r12 "
                   "字母裁决维持不变）"),
    }
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R12,
                                "sha256": _sha(REL_PREP_R12)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "null_result_note": ht["null_result_note"],
            "test_design": ht["test_design"],
            "declaration": ht["declaration"],
            "metric_lesson_application": ht["metric_lesson_application"],
            "candidate_0_target":
                ht["preregistered_criteria_quote"]["candidate_0_target"],
            "candidate_1_target":
                ht["preregistered_criteria_quote"]["candidate_1_target"],
            "user_directive_2026_09_07":
                ht["preregistered_criteria_quote"][
                    "user_directive_2026_09_07"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "misuse_rule_note": MISUSE_RULE_NOTE,
        "measurement": {
            "reroute_total_r12": reroute_total,
            "undeterminable_condition_met": undeterminable,
            "misuse_abstain_flag_count_r12": misuse_count,
            "reroute_non_abstain_count_r12": len(non_abstain_rows),
            "support_condition_met": supported,
            "reject_condition_met": rejected,
            "reroute_by_instance_r12": reroute_by_instance,
            "reroute_flag_detail_r12": reroute_rows,
            "baseline_cross_check": {
                "r10_misuse_registered":
                    base["r10"]["misuse_abstain_flag_count"],
                "r10_misuse_live": r10_ab,
                "r11_misuse_registered":
                    base["r11"]["misuse_abstain_flag_count"],
                "r11_misuse_live": r11_ab,
                "r11_non_abstain_registered":
                    base["r11"]["boundary_non_abstain_reroute_count"],
                "r11_non_abstain_live": r11_non,
                "note": ("基线数字与在案 run-record（run sha 锚在案）交叉"
                         "核对一致（fail-closed）；基线=编排侧在案登记值，"
                         "live=本轮从内嵌输入重放实测"),
            },
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "其余类别非弃权旗标面积比出局条目 R11=0→R12=0（无回升"
                    "）；guard_ok（守门观察如实记录；类别门 R12=0 条非"
                    "守门范围，见 channel_attribution.channel_2_category_"
                    "gate）"),
                "guard_ok": guard_ok,
                "note": ("守门通道按 r12-prep-record attribution_plan."
                         "guard_channel 独立复核（support_condition=滥用"
                         "型+非弃权双条件，守门非其组成要件）——两项独立"
                         "计算、结果如实分列；本轮 guard_ok=True"),
            },
            "secondary_observation_within_round": {
                "declaration": (
                    "prep-record secondary_observation 预注册：v1.2 首轮"
                    "的轮内一致性（预期「实例间弃权率极差维持小带」）——"
                    "实测 top 0.375（0.875/0.833333/0.5）、bottom 可计算 "
                    "0.95（0.05/None/1.0；bottom-i2 零旗标→None 不计入、"
                    "如实注明）：预期未发生，如实记录（观察项零阈值、"
                    "不预设方向）"),
                "range_top": top_range,
                "range_top_arithmetic": view_layer["top"][
                    "abstain_rate_range_arithmetic"],
                "range_bottom_computable": bottom_range,
                "range_bottom_arithmetic": view_layer["bottom"][
                    "abstain_rate_range_arithmetic"],
                "r11_baseline": {"top": 0.153846, "bottom": 0.0,
                                 "source": "run-r11 在案（ec05e472…）"},
            },
            "courtyard_secondary_observation": (
                "courtyard 密集旗被动追踪延续（零阈值改动零期望；"
                "round11-dev-record next_iteration_targets[3] 在案）——"
                "实测见 courtyard_tracking 节（非弃权 20 条零命中；"
                "bottom 18 条因 GT 全 top 无从命中）"),
            "aggregate_context": {
                "abstain_rate_r9":
                    run_r9["aggregation"]["abstain_rate_total"],
                "abstain_rate_r10":
                    run_r10["aggregation"]["abstain_rate_total"],
                "abstain_rate_r11_representative":
                    run_r11["aggregation_representative"][
                        "abstain_rate_total"],
                "abstain_rate_r12_representative_note": (
                    "代表配置聚合弃权率见 aggregation_representative."
                    "abstain_rate_total（本轮聚合口径按 measurement_design "
                    "五条预注册执行，代表配置/逐实例/双口径分列）"),
                "apr0011_joint_evaluation_representative": "not_met",
                "note": (
                    "跨轮聚合弃权率（口径分列如实）：r9 0.727273（8/11，"
                    "全旗标）→r10 0.285714（4/14，全旗标）→r11 0.133333"
                    "（2/15，代表配置）→r12 见代表配置分列；APR-0011 四项"
                    "照常独立如实执行（代表配置口径 gt_count 13≥12 达线，"
                    "gt_recall 0.0<0.75、seed_match_rate 0.0<0.5 与 "
                    "abstain_rate 0.9>0.5 未达暂行线→joint=not_met）。"
                    "主通道判据与门各自独立计算、互不凌驾（prep-record "
                    "null_result_note 原文语义）——门联合=not_met 与裁决="
                    "supported 分列不合并"),
            },
            "r12_total_flags_note": (
                "六实例合计 44 旗标（非弃权 25、弃权 19；全旗标合计弃权率 "
                "0.431818 仅作附记——本轮预注册聚合口径=实例层/视角层/"
                "双口径/代表配置，全旗标合计非主通道）"),
        },
        "verdict": verdict,
        "verdict_rule": (
            f"support={ht['support_condition']}；"
            f"reject={ht['reject_condition']}；reroute 类旗标总量=0 → "
            f"{ht['null_result_note']}"
            "（r12-prep-record.json hypothesis_test 判据原文，轮后如实"
            "执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_design_lesson": metric_design_lesson,
        "stratified_observation": {
            "top": {"r11_representative_rate":
                    run_r11["aggregation_representative"][
                        "abstain_rate_total"],
                    "r11_within_range": 0.153846,
                    "r12_by_instance": top_rates,
                    "r12_range": top_range,
                    "direction": ("r11 三实例 0.0/0.153846/0.15（轮内极差 "
                                  "0.153846）→r12 三实例 0.875/0.833333/"
                                  "0.5（轮内极差 0.375）——弃权率整体"
                                  "上移且分化拉大；v1.2 钉住工具轴后判据"
                                  "侧方差显形（机制观察单列）")},
            "bottom": {"r11_representative_rate":
                       run_r11["aggregation_representative"][
                           "abstain_rate_total"],
                       "r11_within_range": 0.0,
                       "r12_by_instance": bottom_rates,
                       "r12_range_computable": bottom_range,
                       "r12_range_note": ("bottom-i2 零旗标分母→None，"
                                          "极差按可计算实例计算并如实注明"
                                          "（measurement_design item 5）"),
                       "direction": ("r11 三实例一致 1.0（7 旗全弃权）→"
                                     "r12 三实例三种裁决（0.05/None/1.0）："
                                     "bottom-i1 20 旗 1 弃权（18 条非弃权 "
                                     "courtyard）、bottom-i2 两板零旗标、"
                                     "bottom-i3 2 旗全弃权——同一批白色"
                                     "蝶形粘连的实例间分化（§4(i) 判据轴，"
                                     "机制观察单列）")},
            "confounder_note": (
                "跨轮 reader 实例不同+轮内实例差异=混杂因素照旧声明；"
                "v1.2 工具规约把工具行为钉住（12/12 自述合规）但判读实例"
                "仍为不同实例；每视角 n=3 仍为小样本；development 域"
                "方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(instances: dict, run_r8: dict, run_r9: dict,
                             run_r11: dict) -> dict:
    """courtyard 被动追踪（r12-prep-record secondary_observation 预注册；
    零阈值改动、零期望；bottom 非弃权 18 条零命中如实入账）。"""
    prep_doc = _json_load(REL_PREP_R12)
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
        "note_source": {"path_rel": REL_PREP_R12,
                        "sha256": _sha(REL_PREP_R12), "quote": note_quote},
        "declaration": ("被动追踪（prep-record secondary_observation 预"
                        "注册延续）：如实记录 courtyard 类旗标匹配表现"
                        "（零阈值改动、零期望、不得为提高命中调阈值）"),
        "r12_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": "弃权旗不参与匹配（abstain 单列）",
        },
        "courtyard_matches_r12": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r11": run_r11["courtyard_tracking"][
            "courtyard_matches_r11"],
        "courtyard_matches_r11_detail": (
            "R11 非弃权 courtyard 14 条中 3 条命中（top-i1 R11T-009↔"
            "GT-REVC-P1-R4J3、top-i3 R11T-010↔GT-REVC-AP-1-R5U6/R11T-003"
            "↔GT-REVC-AP-6-R2LED2；run-r11 在案）"),
        "courtyard_matches_r10": run_r11["courtyard_tracking"][
            "courtyard_matches_r10"],
        "courtyard_matches_r10_detail": (
            "R10T-011↔GT-REVC-P1-R4J3（containment 0.829864、面积比 "
            "1.770688；run-r10 在案，run-r11 转录在案）"),
        "courtyard_matches_r9": run_r11["courtyard_tracking"][
            "courtyard_matches_r9"],
        "courtyard_matches_r9_detail": (
            "R9 top 非弃权 courtyard 2 条与同态 GT 零交集、弃权 2 条；"
            "run-r9 在案，run-r11 转录在案"),
        "courtyard_matches_r8": run_r11["courtyard_tracking"][
            "courtyard_matches_r8"],
        "courtyard_matches_r8_detail": (
            "R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、面积比 "
            "2.688288；run-r8 在案，run-r11 转录在案）"),
        "same_domain_note": (
            "r11 三条 courtyard 命中与 r8 R8T-004、r10 R10T-011 同域"
            "（Y1/R4J3 类 courtyard 密集区）——r12 零再现（top 2 条非弃权 "
            "courtyard 未达近邻门；bottom 18 条因 GT 全部 side=top 无从"
            "命中，bottom GT 无源在案 gt-audit-r1）；GT/阈值零改动"),
        "bottom_observation": {
            "fact": ("R12 bottom 22 旗（bottom-i1 20+bottom-i2 0+"
                     "bottom-i3 2）：bottom-i1 含 18 条非弃权 courtyard"
                     "（prep1 蝶形粘连）+1 非弃权 placement+1 弃权；"
                     "bottom-i3 2 旗全弃权；bottom 非弃权旗 19 条零匹配"
                     "（GT 13 条全部 side=top，bottom GT 无源在案 "
                     "gt-audit-r1⇒bottom 旗标与 GT 匹配应为空，如实）；"
                     "bottom-i2×applied、bottom-i2×prep1、bottom-i3×"
                     "prep1 三格零旗标（分母为零→弃权率按 cal._ratio "
                     "先例=None，不编造数值）；「正常特征→不报告」通道"
                     "继续使用（bottom-i2 两派次与 prep1-bottom-i3 "
                     "reading_notes 原文自述在案）"),
            "evidence": BOTTOM_ZERO_EVIDENCE,
            "evidence_check": ("摘录逐字来自对应 reading_notes（substring "
                               "fail-closed 校验通过）"),
            "rate_note": BOTTOM_ZERO_PART_NOTE,
        },
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


BOTTOM_ZERO_PART_NOTE = (
    "bottom 三格零旗标（bottom-i2×applied、bottom-i2×prep1、bottom-i3×"
    "prep1，均 0 旗）：分母为零、弃权率无定义，按库侧 cal._ratio 先例 "
    "（pcbflow/calibration.py _ratio：零分母→None）如实为 None（绝不"
    "编造数值；measurement_design item 5 预注册口径）；实例层 bottom-i2 "
    "两板合计=0 旗→实例级弃权率=None（bottom-i1/bottom-i3 有定义）；"
    "视角层 bottom 弃权率中位数亦为 None（含 None 实例、不编造数值），"
    "极差按可计算实例（bottom-i1/bottom-i3）计算=0.95 并如实注明")


def build_run() -> dict:
    """run-r12 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    run_r11 = _json_load(REL_RUN_R11)
    attribution = build_channel_attribution(
        run_r6, run_r7, run_r8, run_r9, run_r11, inst_blocks, inst_replays)
    raw_texts = {k: _rel(rel).read_text(encoding="utf-8")
                 for k, rel in RAW_FILES.items()}
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    reroute_rows = verify_reroute_adjudication(instances, raw_texts)
    run_r10 = _json_load(REL_RUN_R10)
    hyp = build_hypothesis_test(run_r8, run_r9, run_r10, run_r11, instances,
                                view_layer, attribution, raw_texts,
                                parsed_notes, reroute_rows)
    courtyard = build_courtyard_tracking(instances, run_r8, run_r9, run_r11)

    prep_r12 = _json_load(REL_PREP_R12)
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
            "五键投影（process-v1 §2 步骤3）；R12 reroute 类三旗 "
            "location_evidence 逐字在案（R12T-001 非弃权边界报告「并非"
            "全程规则周期的蛇形」、R12T-002 存在性弃权未援引候选解释、"
            "R12T-008 排除式引用「按 r12 收窄判据不适用等长/蛇形候选"
            "解释」——hypothesis_test 主通道逐旗判定在案）"),
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
        {"path_rel": REL_PREP_R12, "role": "r12_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R12)},
        {"path_rel": REL_GUIDANCE_R12, "role": "observation_guidance_r12",
         "sha256": _sha(REL_GUIDANCE_R12)},
        {"path_rel": REL_GUIDANCE_R9,
         "role": "observation_guidance_r9_baseline",
         "sha256": _sha(REL_GUIDANCE_R9)},
        {"path_rel": REL_GUIDANCE_R8, "role": "observation_guidance_r8_chain",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_DEV_R11,
         "role": "r11_dev_record_preregistration_source",
         "sha256": _sha(REL_DEV_R11)},
        {"path_rel": REL_PREP_R11, "role": "r11_prep_record_witness_source",
         "sha256": _sha(REL_PREP_R11)},
        {"path_rel": REL_DEV_R10, "role": "r10_dev_record_witness_chain",
         "sha256": _sha(REL_DEV_R10)},
        {"path_rel": REL_PREP_R10, "role": "r10_prep_record_witness_chain",
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
        "kind": "tl2_calibration_run_r12",
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
                "in_calibrated_range 恒 False（协议 v1 §1/§4；v1.2 追加"
                "式修订若被正式采纳其对门的评价含义须另行声明）"),
            "protocol_ref": {"path_rel": REL_PROTOCOL,
                             "sha256": _sha(REL_PROTOCOL)},
        },
        "instrument_change": {
            "nature": INSTRUMENT_NATURE,
            "components": [
                "reroute-example-c-full-segment-periodic-tighten（指引侧"
                "单变量；§3A 类别 4 示例 c 收窄替换）",
                "protocol-v1-2-reader-tool-behavior-rule（协议侧派发层；"
                "v1.2 工具行为规约，不改判读语义）"],
            "unchanged_components": list(prep_r12["unchanged_components"]),
            "changed_variables_registered": [
                {"id": v["id"], "target": v["target"],
                 "description": v["description"],
                 "attribution_channel": v["attribution_channel"]}
                for v in prep_r12["changed_variables"]],
            "protocol_amendment": {
                "amendment_version": prep_r12["protocol_amendment"][
                    "amendment_version"],
                "amendment_mode": prep_r12["protocol_amendment"][
                    "amendment_mode"],
                "v1_file_preserved": prep_r12["protocol_amendment"][
                    "v1_file_preserved"],
                "note": ("evaluation-protocol-v1→v1.2 追加式修订（只追加"
                         "reader 派发指令的工具行为规约（派发层），不改动 "
                         "v1/v1.1 任何既有条款语义；v1 文件零字节保留、"
                         "不回写；本轮不新建协议版本文件）"),
            },
            "attribution_note": prep_r12["attribution_plan"]["declaration"],
            "ref": {"path_rel": REL_PREP_R12, "sha256": _sha(REL_PREP_R12)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL),
                     "amendment_version": "v1.2（追加式；v1 文件零字节"
                                          "保留，见 protocol_amendment）"},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实；命名覆盖 R9T/R9B→R12T/R12B 与示例 reader-id "
            "reader-r9→reader-r12 已随 r12 指引 §6 机械替换落盘固化"
            "（per r12-prep-record protocol_amendment.naming：与 r11 的"
            "派发侧机械覆盖不同，本轮替换随指引落盘；实例后缀 i{1,2,3} "
            "由派发指令机械补全；命名属机械替换、判读实质判据零变更；"
            "实例间编号独立、同实例跨板连续）"),
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
                     "全部关闭（r8 轮同日审计，结论 r9/r10/r11/r12 延续"
                     "引用）；该审计非本轮预注册件（deviations 在案），其"
                     "结论维持本轮 GT 零改动；bottom 旗标与 GT 匹配应为空"
                     "（结构性：GT 13 条全部 side=top）；round11-dev-"
                     "record gt_audit_ref/next_iteration_targets 引用其"
                     "结论（GT 侧已全部关闭）"),
        },
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r11 相同；"
                                   "只作口径引用，APR-0011 阈值零改动）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r12 指引 §4（逐字承 r9 指引）：r8 两条显式判据（弃权"
                    "适用于存在/归类不确定；弃权不适用于仅范围不确定）、"
                    "存在性一般判据（系统性重复 vs 孤立不一致启发）与三路"
                    "出口显式化原文保留；§3A 类别 4 含 r12 收窄替换示例 c"
                    "（「整段规则周期」判据：仅整段全程规则、周期、节律"
                    "一致的折叠才可把等长/蛇形候选解释列入候选；仅局部"
                    "小幅波状/抖动、单次大弯折或大范围绕行不适用；示例="
                    "判据说明，非期望清单；反放宽条款原样）；abstain=true="
                    "现象是否存在或归属哪类无法负责任地判断；abstain 单列"
                    "不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("协议侧 v1.1 多实例口径沿用+派发层 "
                                      "v1.2 工具规约（本轮新增条款）：12 次"
                                      "盲读=4 视角格×3 实例（i1/i2/i3），"
                                      "两波次串行保序（同一实例先 applied "
                                      "后 prep1，flag_id 编号跨板连续、"
                                      "实例间编号独立）；每派次指令含 v1.2 "
                                      "硬性条款（禁止程序化图像处理、只"
                                      "允许 Read 直读原图）；每图独立判读；"
                                      "跨实例/跨视角禁止交流"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R12,
                                 "sha256": _sha(REL_GUIDANCE_R12),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R9,
                                     "sha256": _sha(REL_GUIDANCE_R9),
                                     "role": ("指引作者唯一事实源（r9 指引"
                                              "=r11 轮零字节复用件）")},
                                 "change_note": GUIDANCE_NOTE},
            },
            "note": ("轮次预注册链：round11-dev-record.json（66e41bbf…，"
                     "next_iteration_targets[0]/[1] 原文被 r12-prep-record "
                     "逐字摘录预注册+用户 2026-09-07 拍板两项（方案 (a) "
                     "n=3 已于 r11 执行；示例 c 措辞修改排程 R12 本轮"
                     "执行））→r12-prep-record.json（d393cf27…，本轮预"
                     "注册件，measurement_design 五条聚合口径与 "
                     "hypothesis_test 判据先于盲读冻结）先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；渲染"
                     "复用见证=四 PNG 盘上实测 sha 与见证常量逐一相等+"
                     "渲染输入侧冻结 PDF 复核一致；见证常量源=r11-prep-"
                     "record.json（9074df2d…），在案）；observation-"
                     "guidance-r12.md（0ac22fcd…）由 r9 指引（a0c10154…）"
                     "机械变换生成、落盘即冻结（指引侧唯一实质变更=示例 c "
                     "收窄替换+r12 对照说明+机械替换）；GT 重投影"
                     "（derivation-log-r5.json，13 条 frame_box_pct_r5）"
                     "已在案沿用（渲染未变=零新派生）；盲读后本包只做比对"
                     "与记录（读者产物零改动）。GT 冻结纪律：轮后未增删改；"
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
            "r11_run": {"path_rel": REL_RUN_R11, "sha256": _sha(REL_RUN_R11)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）与 R9"
                     "（§3A 示例 c 增补轮）与 R10（零变更重复轮）与 R11"
                     "（协议侧单变量轮：每视角实例 1→3，v1.1 追加式）run "
                     "在案；R12=单变量指引侧变更轮（示例 c 收窄）+协议侧"
                     "派发层 v1.2；轮间对比见 round12-dev-record.json 的"
                     "方向性观察与 channel_attribution、hypothesis_test"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器/视角层聚合/双口径归并/代表配置选取与通道重放为纯函数"
            "（六实例旗数 8/6/8/20/0/2→代表配置唯一可复算），无 "
            "wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-07-r12（事件序="
            "预注册冻结（round11-dev-record（66e41bbf…，在案）→r12-prep-"
            "record（d393cf27…，本轮预注册件）→r12 指引落盘（0ac22fcd…）"
            "→复用渲染见证）→12 次盲读→比对记录；在案延续=gt-audit-r1 "
            "只读 GT 源审计（r8 轮落盘，本轮延续引用其结论，GT 零改动"
            "维持））"),
    }


DEV_OBSERVATIONS = [
    "R11→R12 派发与旗标量对照：盲读派次 12→12（协议侧 v1.2 工具行为规约"
    "钉住工具轴：12/12 派次自述纯 Read 直读、未做任何程序化处理）；旗标 "
    "53→44（六实例 8/6/8/20/0/2；非弃权 41→25、弃权 12→19）；全旗标"
    "合计弃权率 0.226415（12/53）→0.431818（19/44，附记口径）；预注册"
    "主通道=滥用型弃权旗计数（操作化逐旗判定）：r10=2→r11=1→r12=0，"
    "reroute 类非弃权旗 r11=2→r12=1（边界报告方向保留）——示例 c 收窄"
    "主通道字母裁决=supported；reroute 类总量 r11=3→r12=3（构成变化：r11 1 弃权+2 "
    "非弃权全部出自 top-i3→r12 1 非弃权（top-i1 R12T-001）+2 弃权"
    "（top-i1 R12T-002/top-i3 R12T-008））；代表配置（top=top-i1：中位 8 "
    "由 top-i1/top-i3 同为 8 相切、按先序取 i1 并如实注明 tie；bottom="
    "bottom-i3：中位 2 唯一）弃权率 0.133333（2/15）→0.9（9/10）。",
    "视角层三分列（measurement_design item 2）：top 弃权率 0.0/0.153846/"
    "0.15（r11，极差 0.153846）→0.875/0.833333/0.5（r12，极差 0.375）；"
    "bottom 1.0/1.0/1.0（r11，极差 0.0）→0.05/None/1.0（r12，可计算"
    "极差 0.95；bottom-i2 零旗标分母→None 不计入、如实注明，measurement_"
    "design item 5）——轮内实例方差在工具轴钉住后反而爆拉（机制观察单列"
    "：§4(i) 判据轴成为新的不稳定轴）；旗数 top 8/6/8、bottom 20/0/2"
    "（r11：top 13/13/20、bottom 2/3/2）。",
    "matches 与 GT 双口径（measurement_design item 3）：r11 逐实例逐态 "
    "matches 合计 4 条→r12 零匹配（六实例全部 matches=0）：GT 条目层 "
    "union=4/13（0.307692）→0/13（0.0）、agreement=0/13（0.0，两轮均 "
    "0）；代表配置 gt_recall_total 0.076923（1/13）→0.0（0/13）。bottom "
    "19 条非弃权旗（18 courtyard+1 placement）零匹配属结构性：GT 13 条"
    "全部 side=top、bottom 无 GT 在案（gt-audit-r1：bottom GT=无源已"
    "关闭）⇒ bottom 旗标与 GT 匹配应为空，如实；top 非弃权旗 6 条与同态 "
    "GT 零 ≥0.5 containment 交叠。",
    "通道归因（vs R11，预注册重放方法）：几何门面积比出局 0→0（R7 起"
    "连续空，guard 通道无回升）；类别门 1→0（r11 唯一条目 R11T-012↔"
    "GT-REVC-AP-8-R1Q2 本轮无再现）；视角门 0→0（r12 bottom 非弃权旗与 "
    "GT 零近邻交叠）。通道链自 r6 起：几何门 r6=1→r7=0→r8=0→r9=0→"
    "r10=0→r11=0→r12=0；类别门 r6=1→r7=0→r8=1→r9=0→r10=0→r11=1→"
    "r12=0。",
    "预注册假设（r11-dev-record-candidate-1-example-c-tighten）字母裁决="
    "支持（滥用型弃权旗=0 且 reroute 类非弃权旗=1≥1；r12-prep-record "
    "判据原文执行；唯一正式裁决；reroute 总量=3 非零→非「不可判」）；"
    "守门通道独立复核（几何门 0→0 无回升）通过。逐旗判定证据：R12T-002"
    "「等长|蛇形」子串零命中=未援引候选解释；R12T-008 子串命中为排除式"
    "引用（明写「按 r12 收窄判据不适用等长/蛇形候选解释」）非依赖；"
    "R12T-001 非弃权边界报告（「并非全程规则周期的蛇形」）=收窄判据正确"
    "适用后的关注路径报告。机制观察单列（不凌驾）：工具规约 v1.2 钉住"
    "工具轴（12/12 纯直读）但轮内实例方差爆拉（top 0.375/bottom 可计算 "
    "0.95 vs r11 0.153846/0.0）——分歧轴转移到 §4(i)「系统性重复 vs "
    "孤立不一致」判据本身：bottom 三实例对同一批白色蝶形粘连给出三种"
    "裁决（bottom-i1=18 条非弃权 courtyard「孤立、打破规律」/bottom-i2="
    "0 旗「系统性重复→正常」/bottom-i3=2 弃权旗「疑似合并异常无法确认」"
    "）；「正确测出无效同样是有效证据」的同构：测出新不稳定轴同样是有效"
    "证据。",
    "工具行为（协议侧 v1.2 首轮执行，如实入账）：R12 十二派次全部以 "
    "Read 工具直读内嵌图像、自述未做任何裁剪/放大/像素分析等程序化处理"
    "（逐派次 reading_notes 原文自述在案）；r10/r11 实测 8/12 派次自选 "
    "PIL 局部裁剪放大的工具异质性在本轮自述口径中为零——工具轴钉住；"
    "跨轮实例不同+轮内实例差异=混杂因素照旧声明（reader_instance_note）。",
    "输出格式实例披露（编排侧落盘前处理，盘上件=冻结证据）：12 件均经 "
    "json.dump indent=1 重序列化（内容逐键忠实）；无围栏剥离本先例记录"
    "（r7/r10/r11 有围栏剥离或原样落盘先例，本轮零围栏剥离、零原样落盘"
    "件）——12 件 parse 校验全部通过，均非盲读违规。",
    "courtyard 被动追踪（prep-record 预注册延续）：R12 非弃权 courtyard "
    "旗 20 条（top-i2 R12T-001、top-i3 R12T-001、bottom-i1 R12B-003.."
    "020 共 18 条）零命中（r11 14 条 3 命中→r12 20 条 0 命中；bottom 18 "
    "条因 GT 全部 side=top 无从命中）；弃权 courtyard 9 条（top 7+"
    "bottom 2）；courtyard 匹配 r8=1→r9=0→r10=1→r11=3→r12=0；GT/阈值"
    "零改动、零期望。",
    "bottom 观察（measurement_design item 5）：R12 bottom 22 旗=非弃权 "
    "19+弃权 3——r11（7 旗全弃权、零非弃权）后 bottom 首次出现非弃权旗"
    "（bottom-i1 18 条蝶形粘连 courtyard+1 条 placement）；bottom-i2 两"
    "板零旗标、bottom-i3 2 旗全弃权——三实例三种裁决（机制观察单列）；"
    "bottom-i2×applied、bottom-i2×prep1、bottom-i3×prep1 三格零旗标"
    "（分母为零→弃权率按 cal._ratio 先例=None，不编造数值）；实例层 "
    "bottom-i2 flag_count=0→实例级弃权率=None；「正常特征→不报告」通道"
    "继续使用（bottom-i2 两派次与 prep1-bottom-i3 reading_notes 原文"
    "自述在案）。",
    "跨轮 flag_id 不构成同旗配对（R11T/R11B 与 R12T/R12B 来自不同 "
    "reader 实例）；通道归因是通道级不是旗级（run-r12 channel_attribution."
    "pairing_caveat）；重放与 compare_v3 对拍一致（R11 十二件复算与 "
    "run-r11 在案一致、R12 十二件全部复现：候选对=空集）。",
]

DEV_NEXT_TARGETS = [
    "§4(i) 判据的可操作性修订候选（指引侧，本轮实测导出、须预注册后执行，"
    "注意不得反向放宽）：bottom 三实例对同一批白色蝶形粘连给出三种裁决"
    "（bottom-i1 18 条非弃权「孤立、打破规律」/bottom-i2 0 旗「系统性"
    "重复→正常」/bottom-i3 2 弃权「疑似合并异常无法确认」）——「系统性"
    "重复 vs 孤立不一致」启发在纯直读分辨率下是新的不稳定轴（r12 机制"
    "观察在案）；候选方案：给「系统性重复」加量化判据（如同一形态在全图"
    "至少 n 处重复才可援引判据(i)）或明确「孤立」的可操作判据；措辞修改"
    "属指引侧变更、须预注册+单变量纪律，反放宽条款（「仅因形态不熟悉、"
    "不确定其设计含义，不构成判为正常设计特征的理由」）与三路出口一字"
    "保留；不得回溯改判既往轮次（r8–r12 字母裁决维持不变）。",
    "渲染侧 bottom 图层清单+蝶形粘连层归属消歧候选（r6–r12-prep-record "
    "在案候选；r12 bottom-i1 自述「轮廓归属 courtyard 层还是丝印层在该"
    "合成视图下无法完全区分」、bottom 三实例对同一批蝶形粘连三种裁决——"
    "bottom 图层清单缺失的影响仍无法与实例差异分离）：属渲染侧变更，须"
    "预注册+声明零仪器变更纪律例外。",
    "示例 c 收窄保留观察（指引侧，零变更候选）：r12 字母裁决=supported"
    "（滥用型 0+排除式引用出现+边界非弃权报告保留）——单轮 n=3 方向性"
    "证据（development 域只描述不断言）；后续轮继续被动追踪滥用型弃权旗"
    "计数（零期望；若回升如实记录）；r11 双向效应证据链（r10 援引弃权/"
    "r11 边界非弃权/r12 滥用型清零）在案。",
    "courtyard 密集旗追踪延续（指引侧观察候选）：r12 非弃权 courtyard 20 "
    "条零命中（top 2 条未达近邻门、bottom 18 条因 GT 全部 side=top 无从"
    "命中）；r11 三命中（Y1/R4J3 类密集区）本轮零再现；继续被动追踪"
    "（GT/阈值零改动；不得为提高命中调阈值；无期望）。",
    "GT 侧已全关闭声明延续：r8 轮同日只读审计 gt-audit-r1（1f20554a…）"
    "三候选全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、L1NB "
    "框径=合理维持现框），r9–r12 延续零改动——GT 侧已全部关闭，后续迭代"
    "回归指引侧/渲染侧/协议侧；bottom 零匹配的结构性原因（bottom GT 无"
    "源）在案。",
    "留出集已就绪待开发线收敛：Tier 1/2 留出材料已下载就绪"
    "（out/v3-tl2/holdout/HOLDOUT-PLAN.md a4b80193… 与 datasets/"
    "holdout-candidates-r1，用户 2026-09-07 拍板并行包在案）——达标证据"
    "仍须留出集；in_calibrated_range 恒 False 直到正式采纳（须人工批准）。",
    "迭代目标不变式：任何仪器/指引/协议变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；in_calibrated_"
    "range 恒 False 直到正式采纳；连续达标计数 0（R11 后）→0（本轮，"
    "代表配置口径），正式采纳门槛未达成；多实例聚合口径（union/agreement、"
    "代表配置+范围）若转正式须另行声明其对门的评价含义（v1.1/v1.2 "
    "scope_note）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round12-dev-record 文档构建（T3；单向引用 run-r12 sha）。"""
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
    run_r11 = _json_load(REL_RUN_R11)
    trend_rows.append({
        "round": "r11", "round_id": run_r11["round_id"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total":
            run_r11["aggregation_representative"]["flag_count_total"],
        "abstain_count_total":
            run_r11["aggregation_representative"]["abstain_count_total"],
        "abstain_rate_total":
            run_r11["aggregation_representative"]["abstain_rate_total"],
        "matches_total":
            run_r11["aggregation_representative"]["matches_total"],
        "gt_recall_total":
            run_r11["aggregation_representative"]["gt_recall_total"],
        "seed_match_rate_total":
            run_r11["aggregation_representative"]["seed_match_rate_total"],
        "joint_evaluation":
            run_r11["compliance_representative"]["joint_evaluation"],
        "source": {"path_rel": REL_RUN_R11,
                   "sha256": _sha(REL_RUN_R11)},
    })
    trend_rows.append({
        "round": "r12", "round_id": run_doc["round_id"],
        "aggregation_scope": "representative_configuration（item 4）",
        "flag_count_total": agg["flag_count_total"],
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "matches_total": agg["matches_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "source": {"path_rel": REL_RUN_R12, "sha256": run_sha},
    })
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round12_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域单变量指引侧变更轮+协议侧派发层规约轮（第十二"
            "轮；v1.2 首轮）：指引侧唯一实质变更=§3A 类别 4 示例 c 收窄"
            "替换（r9 增补原文删除、替换为「整段规则周期」判据+§3A 末尾 "
            "r12 对照说明；observation-guidance-r12.md=0ac22fcd 由 r9 指引"
            " a0c10154 机械变换生成、落盘即冻结；执行 round11-dev-record "
            "next_iteration_targets[1]，用户 2026-09-07 已拍板排程本轮），"
            "协议侧 evaluation-protocol-v1→v1.2 追加式（执行 next_"
            "iteration_targets[0] 固定 reader 工具行为规约案：派发指令"
            "统一禁止程序化图像处理、只允许 Read 直读原图——属派发层、"
            "读者不可见、不改变任何分类判据语义；v1 文件零字节保留、"
            "不回写；v1.1 的 n=3 多实例与聚合口径全部沿用）；R5 冻结渲染"
            "件逐字节复用（零仪器变更、零重渲染，PNG 见证在案），GT 集/"
            "协议阈值与度量版本/比较器常量零改动（GT 重投影沿用 "
            "derivation-log-r5——渲染未变=零新派生；gt-audit-r1 三候选"
            "关闭结论延续）；指引侧变更=收紧方向（候选解释可用前提收窄、"
            "判断责任标准一字未松，不构成任何放宽）；检验 r11 预注册候选"
            "假设 r11-dev-record-candidate-1-example-c-tighten（判据="
            "r12-prep-record.json hypothesis_test，轮后如实执行：字母裁决"
            "唯一正式+机制观察单列）；主通道判据（滥用型弃权旗计数）与 "
            "APR-0011 门（gt_recall≥0.75/seed_match_rate≥0.5/abstain_"
            "rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量各自独立"
            "计算、互不凌驾、分开表述；measurement_design 五条聚合口径"
            "（实例主记录/视角层三分列/GT 匹配双口径/代表配置+范围并列/"
            "bottom 零分母=None）先于盲读冻结；命名覆盖 R9T/R9B→R12T/"
            "R12B 已随指引落盘固化（protocol_amendment.naming，判读实质"
            "零变更）；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "preregistration_chain_note": (
            "预注册链（含哈希）：round11-dev-record.json（66e41bbf…，"
            "next_iteration_targets[0]/[1] 原文+用户 2026-09-07 拍板）→"
            "r12-prep-record.json（d393cf27…，逐字摘录候选原文预注册+"
            "measurement_design 五条聚合口径与 hypothesis_test 判据先于"
            "盲读冻结=本轮执行依据）→run-r12（本链执行落盘）；observation-"
            "guidance-r12.md（0ac22fcd…）由 r9 指引（a0c10154…）机械变换"
            "生成、落盘即冻结；渲染复用见证源=r11-prep-record.json"
            "（9074df2d…）"),
        "run_record_ref": {"path_rel": REL_RUN_R12, "sha256": run_sha},
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
                                            "预注册主通道=滥用型弃权旗计数"
                                            "（操作化逐旗判定，实例层/视角"
                                            "层分列）"),
            "abstain_rate_by_instance": {
                n: run_doc["instances"][n]["combined"]["abstain_rate"]
                for n in INSTANCE_ORDER},
            "abstain_rate_range_by_view": {
                "top": run_doc["view_layer"]["top"]["abstain_rate_range"],
                "bottom": run_doc["view_layer"]["bottom"][
                    "abstain_rate_range"],
                "bottom_note": ("可计算实例极差（bottom-i2 零旗标→None "
                                "不计入，如实注明；measurement_design "
                                "item 5）"),
            },
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
                     "模式=12 派次（4 格×3 实例，两波次串行保序）；命名"
                     "覆盖 R9T/R9B→R12T/R12B 随指引落盘固化；v1.2 工具"
                     "规约首轮 12/12 派次自述合规与输出格式披露（12 件 "
                     "indent=1 重序列化；无围栏剥离）如实登记为混杂因素"
                     "披露，不作废"),
        },
        "diagnostic_result": {
            "aggregation_scope": "representative_configuration（top-i1+"
                                 "bottom-i3，measurement_design item 4；"
                                 "top 中位 8 由 top-i1/top-i3 同为 8 相切、"
                                 "按先序取 i1 并如实注明 tie；bottom 中位 "
                                 "2=bottom-i3 唯一）",
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
                                       "聚合（单实例/轮口径在案）；r11/r12 "
                                       "行=代表配置口径（measurement_"
                                       "design item 4）——两口径并列如实、"
                                       "不混同（r12 全旗标合计 19/44="
                                       "0.431818 仅作附记）"),
            "after_r11": {"consecutive_met_count": 0,
                          "note": "R11 联合评价 not_met（在案，代表配置"
                                  "口径），连续达标计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价（代表配置）not_met（"
                                   "gt_recall 0.0 与 seed_match_rate 0.0 "
                                   "与 abstain_rate 0.9>0.5 三项未达暂行"
                                   "线；gt_count 13≥12 单分项入线）——"
                                   "GT 条目层 union 口径 0/13=0.0 亦未达 "
                                   "0.75（双口径与门分列如实）"},
            "consecutive_met_count_now": 0,
            "by_round": trend_rows,
            "note": "连续达标计数变动：0（R11 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r11": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，单变量指引侧变更轮（示例 c 收窄替换）+"
            "协议侧派发层 v1.2 工具规约首轮：R5 冻结渲染复用+GT/阈值零"
            "变更）12 派次 44 旗标中 19 弃权、25 非弃权：代表配置（top-i1+"
            "bottom-i3：top 中位 8 tie 取先序、bottom 中位 2 唯一）"
            "gt_recall=0.0（0/13）、"
            "seed_match_rate=0.0（0/1，诊断口径，禁称 precision/FPR）、"
            "abstain_rate=0.9（9/10），联合评价 not_met（gt_recall、"
            "seed_match_rate 与 abstain_rate 三项未达 APR-0011 暂行线；"
            "诊断对照，非采纳"
            "门；连续达标计数 0→0；GT 条目层 union=0/13、agreement=0/13 "
            "双口径并列）。预注册假设（r11-dev-record-candidate-1-example-"
            "c-tighten）裁决（按 r12-prep-record hypothesis_test 判据）="
            "支持（字母口径，唯一正式裁决）：滥用型弃权旗=0（操作化逐旗"
            "判定：R12T-002 子串零命中=未援引；R12T-008 排除式引用非依赖"
            "）且 reroute 类非弃权旗=1≥1（R12T-001 边界报告）；reroute "
            "总量=3 非零→非「不可判」。三条机制结论如实单列（不凌驾字母"
            "裁决）：①示例 c 收窄生效=滥用型清零+边界报告保留+排除式引用"
            "出现（「按 r12 收窄判据不适用等长/蛇形候选解释」=收窄文本的"
            "直接适用；supported≠统计证明，单轮 n=3 方向性、development "
            "域只描述不断言）；②工具钉住≠判读一致：v1.2 把工具轴钉住"
            "（12/12 派次自述纯 Read 直读）但轮内实例方差爆拉（top 极差 "
            "0.375/bottom 可计算极差 0.95 vs r11 0.153846/0.0），§4(i)"
            "「系统性重复 vs 孤立不一致」判据成为新的不稳定轴（bottom 三"
            "实例对同一批白色蝶形粘连三种裁决：bottom-i1=18 条非弃权/"
            "bottom-i2=0 旗/bottom-i3=2 弃权；读者原文摘录 substring "
            "校验在案 reader_note_evidence）——「正确测出无效同样是有效"
            "证据」的同构：测出新不稳定轴同样是有效证据；③聚合弃权率与"
            "实例方差双升"
            "（全旗标合计 0.226415→0.431818 附记口径；top 0.0/0.153846/"
            "0.15→0.875/0.833333/0.5）：v1.2 的可比性目标只达成「工具"
            "维度」，判读维度一致性未达成。bottom 19 条非弃权旗零匹配属"
            "结构性（GT 13 条全部 side=top，bottom GT 无源在案 gt-audit-"
            "r1）；bottom 三格零旗标与 bottom-i2 实例级弃权率按 cal._ratio "
            "先例=None（不编造数值）；「正常特征→不报告」通道继续使用。"
            "工具行为混杂如实入账（12/12 派次 v1.2 合规自述在案）；输出"
            "格式披露（12 件 indent=1 重序列化；无围栏剥离）如实登记、"
            "均非盲读违规。GT 侧三候选经 gt-audit-r1 全部关闭（延续零"
            "改动，GT 侧不再有候选）。不做「能力已修复/已达成」类断言；"
            "in_calibrated_range 恒 False。本批证据按协议 v1 §4 属 "
            "development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）；多实例"
            "聚合并列口径不构成任何门的放宽或收紧（r12-prep-record "
            "no_loosening_note：本轮指引侧变更为收紧方向、协议侧 v1.2 "
            "只固定输入手段）。",
            "R11 对照基线=calibration-run-r11.json（ec05e472…，在案）；"
            "R8/R9/R10 对照基线=calibration-run-r8.json（3c580eb3…）/r9"
            "（e16420e5…）/r10（622c9099…，在案）；轮间对比只做方向性"
            "描述。",
            "通道归因方法：照抄 run-r11 channel_attribution 的重放口径"
            "（deviation_note 承接），R11 与 R12 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r12 "
            "channel_attribution.method）；R11 重放结果与 run-r11 在案"
            "登记逐一核对一致（fail-closed）。",
            "读者实例行为披露如实记录：R12 十二派次 v1.2 规约自述合规"
            "（纯 Read 直读、未做程序化处理，逐派次 reading_notes 原文"
            "在案）；输出格式披露（12 件 json.dump indent=1 重序列化内容"
            "逐键忠实；无围栏剥离）parse 校验全部通过。跨轮 reader 实例"
            "不同+轮内实例差异=混杂因素，每视角 n=3。",
            "假设裁决纪律：字母裁决=唯一正式裁决（预注册判据原文执行）；"
            "机制观察单列，不得凌驾或改写字母裁决；本轮字母裁决=supported "
            "维持不变（supported≠统计证明——单轮 n=3 小样本方向性证据；"
            "主通道判据与 APR-0011 门分开表述、互不凌驾：门联合评价（"
            "代表配置）=not_met 如实分列）。",
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
                                run_r10: dict, run_r11: dict, parsed: dict,
                                raw_texts: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    inst = run_doc["instances"]
    counts = {n: inst[n]["combined"]["flag_count"] for n in INSTANCE_ORDER}
    if counts != {"top-i1": 8, "top-i2": 6, "top-i3": 8, "bottom-i1": 20,
                  "bottom-i2": 0, "bottom-i3": 2}:
        _fail("观察文本实例旗数与实测不一致")
    abst = {n: inst[n]["combined"]["abstain_count"] for n in INSTANCE_ORDER}
    if abst != {"top-i1": 7, "top-i2": 5, "top-i3": 4, "bottom-i1": 1,
                "bottom-i2": 0, "bottom-i3": 2}:
        _fail("观察文本实例弃权记账与实测不一致")
    agg = run_doc["aggregation_representative"]
    if agg["abstain_rate_total"] != 0.9 or "0.9（9/10）" not in obs:
        _fail("观察文本代表配置弃权率与实测不一致")
    hyp = run_doc["hypothesis_test"]
    if hyp["verdict"] != "supported":
        _fail("假设字母裁决与预注册判据复算不符")
    if hyp["measurement"]["misuse_abstain_flag_count_r12"] != 0 \
            or hyp["measurement"]["reroute_non_abstain_count_r12"] != 1 \
            or hyp["measurement"]["reroute_total_r12"] != 3:
        _fail("主通道计数与实测不一致")
    vl = run_doc["view_layer"]
    if vl["top"]["abstain_rate_range"] != 0.375 \
            or vl["bottom"]["abstain_rate_range"] != 0.95:
        _fail("视角层极差与观察文本不一致")
    if "0.375" not in obs or "0.431818" not in obs:
        _fail("观察文本缺实测数字（0.375/0.431818）")
    dual = run_doc["gt_match_dual"]
    if dual["union"]["count"] != 0 or dual["agreement"]["count"] != 0:
        _fail("双口径计数与实测不一致")
    if dual["union"]["gt_recall_union"] != 0.0:
        _fail("union gt_recall 与实测不一致")
    matches_all = sorted(
        (m["flag_id"], m["gt_id"]) for n in INSTANCE_ORDER
        for m in inst[n]["combined"]["matches_detail"])
    if matches_all != []:
        _fail("matches 明细与观察文本不一致（r12 应零匹配）")
    if reroute_production(run_r8["states"]) != 1 \
            or reroute_production(run_r9["states"]) != 0 \
            or reroute_production(run_r10["states"]) != 2 \
            or run_r11["reader"]["flag_count"]["reroute_class_production"] \
            != 3 \
            or run_doc["reader"]["flag_count"]["reroute_class_production"] \
            != 3:
        _fail("reroute 类产量与字母裁决输入不一致")
    for need in ("12→12", "53→44",
                 "8/6/8/20/0/2", "0.0（0/13）", "0/13", "R12T-001",
                 "R12T-002", "R12T-008", "R11T-012", "示例 c", "supported",
                 "判据轴", "0.95", "0.375", "0.153846", "bottom-i1",
                 "bottom-i2", "bottom-i3", "蝶形", "None", "gt-audit-r1",
                 "12/12", "indent=1", "tie", "先序", "r6=1→r7=0",
                 "纯 Read 直读", "排除式引用"):
        if need not in obs:
            _fail(f"观察文本缺实测数字/事实 {need}")
    # 通道条目数与文本一致（几何 R11 0→R12 0；类别 R11 1→R12 0）
    ca = run_doc["channel_attribution"]
    if len(ca["channel_1_geometry_gate"]["r12_area_ratio_rejected_entries"]) \
            != 0 or len(ca["channel_2_category_gate"][
                "r12_category_mismatch_entries"]) != 0:
        _fail("通道条目数与观察文本声明不一致")
    # courtyard 追踪与实测一致（r12 非弃权 courtyard 命中=0、非弃权 20）
    ct = run_doc["courtyard_tracking"]
    if ct["courtyard_matches_r12"] != 0 or len(
            ct["r12_courtyard_flags"]["non_abstain"]) != 20:
        _fail("courtyard 追踪计数与实测不一致")
    if len(ct["r12_courtyard_flags"]["abstain"]) != 9:
        _fail("courtyard 弃权旗计数与实测不一致")
    # 逐旗判定/工具规约/判据轴/bottom 零旗证据摘录逐字在案
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    for r in run_doc["hypothesis_test"]["measurement"][
            "reroute_flag_detail_r12"]:
        if r["form_desc_excerpt"] not in raw_texts[r["source"]]:
            _fail(f"逐旗判定摘录与 reader 原文不符: {r['flag_id']}")
    for ev in mo["tool_axis_pinned_vs_criterion_axis"]["tool_evidence"]:
        if ev["excerpt"] not in parsed[ev["source"]]["reading_notes"]:
            _fail(f"工具规约摘录与 reader 原文不符: {ev['source']}")
    for ev in mo["tool_axis_pinned_vs_criterion_axis"][
            "reader_note_evidence"]:
        src_text = (parsed[ev["source"]]["reading_notes"]
                    if ev["kind"] == "reading_notes"
                    else raw_texts[ev["source"]])
        if ev["excerpt"] not in src_text:
            _fail(f"判据轴摘录与 reader 原文不符: {ev.get('flag_id')}")
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
        _fail("同参重建不一致（byte-exact 破坏）: run-r12")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), _json_load(REL_RUN_R9),
        _json_load(REL_RUN_R10), _json_load(REL_RUN_R11), parsed, raw_texts)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R12), run_bytes,
                         "calibration-run-r12.json")
    run_sha = _sha(REL_RUN_R12)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round12-dev-record")
    dev_status = _commit(_rel(REL_DEV_RECORD), dev_bytes,
                         "round12-dev-record.json")

    vl = run["view_layer"]
    agg = run["aggregation_representative"]
    comp = run["compliance_representative"]
    hyp = run["hypothesis_test"]
    print(f"[s47-cal-r12] 解析：12 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {run['reader']['flag_count']['total']}"
          f"（非弃权 25、弃权 19）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s47-cal-r12] 视角注入：{run['reader']['view_injection']['rule']}")
    for n in INSTANCE_ORDER:
        c = run["instances"][n]["combined"]
        print(f"[s47-cal-r12] {n}: flags={c['flag_count']} "
              f"abstain={c['abstain_count']} rate={c['abstain_rate']} "
              f"matches={c['matches_total']} "
              f"gt_union={c['gt_matched_union']}")
    print(f"[s47-cal-r12] view_layer: top range={vl['top']['abstain_rate_range']}"
          f" bottom range(可计算)={vl['bottom']['abstain_rate_range']}")
    print(f"[s47-cal-r12] gt_dual: union={run['gt_match_dual']['union']['count']}"
          f"/13 agreement={run['gt_match_dual']['agreement']['count']}/13")
    print(f"[s47-cal-r12] representative: top={run['representative_configuration']['members']['top']}"
          f" bottom={run['representative_configuration']['members']['bottom']}"
          f" -> abstain_rate_total={agg['abstain_rate_total']} "
          f"gt_recall={agg['gt_recall_total']} "
          f"seed={agg['seed_match_rate_total']}")
    print(f"[s47-cal-r12] hypothesis ({hyp['hypothesis_id']}): -> "
          f"{hyp['verdict']}（字母裁决；滥用型="
          f"{hyp['measurement']['misuse_abstain_flag_count_r12']}"
          f"/reroute 非弃权={hyp['measurement']['reroute_non_abstain_count_r12']}"
          f"/总量={hyp['measurement']['reroute_total_r12']}；机制观察单列）")
    print(f"[s47-cal-r12] compliance(代表配置): joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s47-cal-r12] channel_attribution: "
          f"geo R11={len(ca['channel_1_geometry_gate']['r11_area_ratio_rejected_entries'])}"
          f"→R12={len(ca['channel_1_geometry_gate']['r12_area_ratio_rejected_entries'])}, "
          f"cat R11={len(ca['channel_2_category_gate']['r11_category_mismatch_entries'])}"
          f"→R12={len(ca['channel_2_category_gate']['r12_category_mismatch_entries'])}")
    print(f"[s47-cal-r12] commit: run={run_status} dev={dev_status}")
    for rel in (REL_RUN_R12, REL_DEV_RECORD):
        print(f"[s47-cal-r12] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s47-cal-r12] R12 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
