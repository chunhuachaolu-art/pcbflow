#!/usr/bin/env python
"""CAL-R9-CLOSE：reader 判读迭代第九轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s39_calibration_r8_compare.py 同构，仅输入与轮次
常量不同；R9=development 域单变量指引侧变更轮（§3A 类别 4
suspicious_reroute 增补示例 c：蛇形/等长规则周期形态按 §4 存在性
一般判据推理的候选解释说明；§3A 末尾另增一条对照说明），零仪器
变更，复用 R5 冻结渲染；并落地 round8-dev-record 度量设计教训的
协议侧前瞻预注册（主通道=现象类旗标产量计数，自本轮起适用、不
追溯 r8）；检验 R8 预注册候选假设 (ii)（r8-dev-record-candidate-ii））：

  T1  解析 4 个 reader-raw-r9-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate + 分视角（top/
      bottom）分层弃权记账 + 逐旗失败通道归因（vs R8，照 s39 重放
      方法；通道链自 r6 起逐轮衔接）：applied 态=applied-top+
      applied-bottom 旗标 vs ground-truth-v2 九条（GT 重投影继续用
      derivation-log-r5 的 frame_box_pct_r5——渲染未变=重投影输入
      未变，board_box_mm/side 等其余字段与 GT 文件逐字段原样）；
      prep1 态=prep1-top+prep1-bottom 旗标 vs ground-truth-v1 四条
      （同重投影规则）。达标线=APR-0011 暂时采纳基线，逐项诊断对照
      （禁改阈值措辞；seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称
      precision/FPR）。
      预注册假设 (ii) 裁决节（三分结构，两分如实分离）：(1) 字母裁决
      （唯一正式裁决，判据=r9-prep-record.json hypothesis_test 原文：
      support=全视角 reroute 类旗标产量（弃权+非弃权合计）=0 且其余
      类别非弃权旗标仍守 §3 收窄判据（几何门面积比出局条目无回升）；
      reject=reroute 类产量 ≥1）；(2) 机制观察（单列，不凌驾字母
      裁决：两个 top reader 判读注记均报告未观察到蛇形/等长类形态
      ——刺激本体缺席，reroute 产量=0 无法归因于判据化解，「判据
      有效」证据不足）；(3) 度量设计教训（本轮为 r8 度量教训前瞻
      落地首轮，实测暴露「产量计数无法区分『判据化解』与『刺激
      缺席』」——协议侧候选，不追溯改判本轮）。
      → calibration-run-r9.json。
  T3  development 域记录（本轮性质=单变量指引侧变更轮：零仪器变更、
      复用 R5 冻结渲染；R8→R9 方向性对照与匹配位置对照（只描述不
      下能力断言）/假设 (ii) 三分裁决/下一迭代目标——延续引用
      gt-audit-r1.json（1f20554a…）结论：bottom GT/reroute GT/L1NB
      框径三候选全部关闭，GT 侧不再有候选；预注册链=r8-dev-record
      （437e149c…）→r9-prep-record（dd979632…）→run-r9；引用 run-r9
      落盘 sha 单向引用）→ round9-dev-record.json。

通道归因纪律（vs R8；方法照抄 s34/s36/s39 deviation_note 口径）：本轮
对 R8 与 R9 均以内嵌输入（reader_flags/gt_entries/flag_views，run sha
在案）+ compare_v3 同源几何原语（calibration._containment/
_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放
通道分类，并与各态 compare_v3 的 matches∪duplicate_reports 对拍
复核。跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是通道级
不是旗级。

读者实例披露（如实入账，不作废）：R9 四个 reader 实例全部用 Read
工具直接取得内嵌图像（无 URL 转传、无外部视觉工具）——比 R8（四
实例中三个经外部视觉分析工具 analyze_image 读图）的仪器异质性更低；
prep1-top 实例对同一 PNG 执行三次 Read 分区复核（其实例行为，如实
记账）；prep1-top 实例的最终消息在 JSON 对象之后附了一行非 JSON
杂音文本（内容为无关营销字句），编排侧落盘时只保留纯 JSON 主体、
parse 校验通过——输出格式异常，非盲读违规（其判读输入仍严格限于
指引+该 PNG）；跨轮 reader 实例不同=混杂因素，每格 n=1。

纪律：out/ 既有文件零改动（防覆写 guard：目标已存在且与重建字节
不同→FAIL，字节等同→幂等跳过零覆写；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r9）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s41_calibration_r9_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-07-r9"
ROUND_LABEL = "r9"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_GUIDANCE_R9 = "out/v3-tl2/calibration/observation-guidance-r9.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
REL_PREP_R9 = "out/v3-tl2/calibration/r9-prep-record.json"
REL_DEV_R8 = "out/v3-tl2/calibration/round8-dev-record.json"
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
REL_DEV_RECORD = "out/v3-tl2/calibration/round9-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r9-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r9-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r9-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r9-prep1-bottom.txt",
}
#: R9 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r9-prep-record（源自 r8-prep-record）脚本
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R9 复核见证=r9-prep-record
#: renders_reuse.frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r9-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r9-prep-record.json frozen_input_pdfs_check 实测值；
#: guidance-r9 锚=r9-prep-record.json guidance.sha256 全长；
#: prep-r9 锚与 r8-dev-record 锚=任务给定先验（盘上实测一致）。
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
    REL_DEV_R8:
        "437e149c3ae4d96653111be968f7d80d86ecbca7f6bb42a31f370ec5af78515d",
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
    RAW_FILES["applied-top"]:
        "042e32824acbd5a835af5981fc0918bdd97e494d27736f63da82d430fc54f79b",
    RAW_FILES["applied-bottom"]:
        "ebc72929d51eff9324ee17d3f2baa2c9819a002e2a7a2be090895e0257fad9a9",
    RAW_FILES["prep1-top"]:
        "528718bc70b0004cfb7a8fef421d9a7fcbeb19d8d7c0d59204daa5b76395763a",
    RAW_FILES["prep1-bottom"]:
        "3ef420a379bfdb0852b3bc4ef120bcfbf7d8b17e85d8cb2782c738876e08c631",
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
    "两波并行派发（与 R7/R8 相同；视角内 applied→prep1 串行顺序保持）："
    "波 1=applied-top 与 applied-bottom 并行（两视角编号独立）；波 2="
    "prep1-top 与 prep1-bottom 并行；视角内 applied→prep1 串行顺序保持"
    "（top R9T-001..009：applied 001..004→prep1 005..009；bottom "
    "R9B-001..002：applied 001→prep1 002）；盲读派发词只含图像路径+"
    "observation-guidance-r9.md 路径+视角前缀+起始序号；无任何 GT 坐标/"
    "类别提示/期望缺陷描述；读图者不接触 GT/派生台账/任何校准产物路径")

#: 派发模式结构化记录（R9 与 R7/R8 同模式：两波并行）。
PARALLEL_DISPATCH = {
    "mode": "two_wave_parallel",
    "wave_1_parallel": ["applied-top", "applied-bottom"],
    "wave_2_parallel": ["prep1-top", "prep1-bottom"],
    "within_view_serial_order": {"top": ["applied-top", "prep1-top"],
                                 "bottom": ["applied-bottom",
                                            "prep1-bottom"]},
    "flag_id_continuity": {"top": "R9T-001..009（applied 001..004→"
                                  "prep1 005..009）",
                           "bottom": "R9B-001..002（applied 001→"
                                     "prep1 002）"},
    "diff_note": ("R6=四图独立全串行派发（run-r6 reader.serial_dispatch "
                  "在案）；R7 起改为两波并行、视角内 applied→prep1 串行"
                  "顺序保持，R9 与 R7/R8 派发模式相同（模式差异相对 R7 "
                  "消除）；R9 特有流程差异=读者实例行为差异（四实例全部 "
                  "Read 直读内嵌图像、prep1-top 三次 Read 分区复核、"
                  "prep1-top 最终消息附非 JSON 杂音已剥离，见 "
                  "reader_instance_note，如实入账，development 域只描述"
                  "不断言）"),
}

#: 读者实例披露（如实入账，不作废）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R9 四个 reader 实例全部用 Read "
    "工具直接取得内嵌图像（无 URL 转传、无外部视觉工具）——比 R8（四"
    "实例中三个因 Read 返回 CDN URL 改经外部视觉分析工具 analyze_image "
    "读图）的仪器异质性更低；判读输入均严格限于（指引+该 PNG），零 GT/"
    "零其他文件接触。实例行为差异如实记账：(1) prep1-top 实例对同一 "
    "PNG 执行三次 Read 分区复核（reader 原文：「对同一文件共执行三次 "
    "Read 以分区复核（顶部文字带、右中密集簇、左中簇、底部梳齿带）」，"
    "未借助缩放或其他视觉工具）；(2) prep1-top 实例的最终消息在 JSON "
    "对象之后附了一行非 JSON 杂音文本（内容为无关营销字句），编排侧"
    "落盘时只保留纯 JSON 主体、parse 校验通过——输出格式异常，非盲读"
    "违规（其判读输入仍只有指引+该 PNG）。跨轮 reader 实例不同=混杂"
    "因素，每格 n=1 无统计效力")

GUIDANCE_CHANGE_NOTE = (
    "本轮唯一变更=判读指引 §3A 类别 4 suspicious_reroute 增补示例 c（"
    "单变量轮）：「整段连线呈规则、周期性的来回折叠形态（蛇形/等长"
    "匹配类布线的常见样式）时，该规则周期形态本身可按第 4 节存在性"
    "判断一般判据推理——同类通用布线样式的常规设计解释是候选解释之一；"
    "形态不规则、无规律的绕行仍按关注现象处理。（示例=判据说明，非"
    "期望清单，不代表图中存在此类现象。）」；另在 §3A 末尾（第 6 类"
    "示例之后、§4 之前）增补一条 r9 对照说明；示例 a、b 原文保留；§4 "
    "三路出口与反放宽条款原文保留（「仅因形态不熟悉、不确定其设计"
    "含义，不构成判为正常设计特征的理由」原样；判「正常设计特征」与"
    "判「关注现象」承担同等判断责任）；其基线=observation-guidance-"
    "r8.md，r9-prep-record baseline 锚 aad43270…；机械替换仅视角前缀 "
    "R8T/R8B→R9T/R9B 与 round_id_constant 一处（及示例 reader-id）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 9 轮迭代"
    "（development 域单变量指引侧变更迭代轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "零仪器变更（单变量指引侧变更轮：§3A 类别 4 增补示例 c+§3A 末尾"
    "对照说明；复用 R5 冻结渲染）")


def _fail(msg: str) -> None:
    print(f"[s41-cal-r9] FAIL: {msg}")
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

    R9 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                    "note": ("R9 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮唯一变更=判读指引 §3A "
                             "类别 4 增补示例 c，单变量轮）")},
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
    两态块（compare_v3.abstain.abstain_ids + flag_views）。
    """
    cells: dict = {}
    for st in ("prep1", "applied"):
        blk = states[st]
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            cell = cells.setdefault(view, {"abstain_count": 0,
                                           "flag_count": 0})
            cell["flag_count"] += 1
            if fid in abst:
                cell["abstain_count"] += 1
    for view, cell in cells.items():
        cell["rate"] = cal._ratio(cell["abstain_count"], cell["flag_count"])
        cell["fraction"] = f"{cell['abstain_count']}/{cell['flag_count']}"
    return cells


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
        },
        "abstain_rate_by_view_arithmetic":
            f"abstain_rate_by_view: top = {by_view['top']['fraction']} = "
            f"{by_view['top']['rate']}；bottom = "
            f"{by_view['bottom']['fraction']} = "
            f"{by_view['bottom']['rate']}"
            "（分层记账如实单列，不参评任何单一达标判断）",
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
                 "旗标）"},
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
                       "r9": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": ("本轮联合评价未达标（gt_recall 与 seed_match_rate "
                     "两项未达暂行线，abstain_rate 0.727273>0.5 回升破线"
                     "——R8 首次入线（0.222222≤0.5）后未续上），连续"
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
# 逐旗失败通道归因（vs R8；方法照抄 s34/s36/s39：通道级，非旗级）
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
                              prep: dict, appl: dict) -> dict:
    """通道归因小节（vs R8；通道级分组，非旗级配对；链自 r6 衔接）。"""
    gt_by_state = {"prep1": prep["gt_entries"], "applied": appl["gt_entries"]}
    r8_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r8["states"][st]
        r8_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r8_replays[st], blk["compare_v3"]):
            _fail(f"R8 {st} 态通道重放与 compare_v3 对拍不一致")
    r9_replays = {}
    for st, blk in (("prep1", prep), ("applied", appl)):
        r9_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r9_replays[st], blk["compare_v3"]):
            _fail(f"R9 {st} 态通道重放与 compare_v3 对拍不一致")

    def pick(replays, failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r8 = pick(r8_replays, "area_ratio_rejected")
    geo_r9 = pick(r9_replays, "area_ratio_rejected")
    cat_r8 = pick(r8_replays, "category_mismatch")
    cat_r9 = pick(r9_replays, "category_mismatch")
    view_r8 = pick(r8_replays, "view_gate")
    view_r9 = pick(r9_replays, "view_gate")

    def _ids(rows):
        return [f"{r['flag_id']}↔{r['gt_id']}" for r in rows]

    geo_change = (
        "几何门通道（R8→R9）：面积比出局条目 0→0（两轮均空）。R9 全部 "
        "3 条非弃权旗标（R9T-001/R9T-002 courtyard_crowding、R9T-005 "
        "silk_readability）与同态 GT 全部条目零交集（containment=None="
        "无交集，未及近邻门）——非弃权框未出现面积比出局，§3 收窄判据"
        "守门无回升（R7 起连续为空）；R9 全局匹配 1→0。")
    cat_change = (
        "类别门通道（R8→R9）：类别不符出局条目 1→0（R8=" +
        "、".join(_ids(cat_r8)) +
        "，containment 1.0、面积比 4.961299；R9 三条非弃权旗与同态 GT "
        "零交集，类别门本轮无生效实例）；matches 1→0；样本量极小，只"
        "描述不断言。")

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
            "r8": len(geo_r8),
            "r9": len(geo_r9),
        },
        "category_gate_category_mismatch_by_round": {
            "r6": _gate_count(run_r6, 6, "channel_2_category_gate"),
            "r7": _gate_count(run_r7, 7, "channel_2_category_gate"),
            "r8": len(cat_r8),
            "r9": len(cat_r9),
        },
        "note": ("几何门 r6=1→r7=0→r8=0→r9=0；类别门 r6=1→r7=0→r8=1→"
                 "r9=0（本轮三条非弃权旗与同态 GT 零交集，两门均无生效"
                 "实例）；matches r8=1→r9=0"),
    }
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R9, "sha256": _sha(REL_PREP_R9)},
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（round8-dev-record "
                "next_iteration_targets[2] 指引侧候选；度量教训=[3] 协议"
                "侧前瞻落地）；轮后按 reroute 类旗标产量变化方向归因"
                "（r9-prep-record.json attribution_plan.declaration 原文）"),
            "primary_channel": {
                "change_id": "reroute-serpentine-criterion-example-c",
                "metric": ("现象类旗标产量计数（弃权+非弃权合计，按类别"
                           "分列）——reroute 类主通道（基线 r8=1）"),
            },
            "guard_channel": {
                "metric": "其余类别非弃权旗 frame_box_pct 几何门（面积比"
                          "出局条目）",
                "requirement": ("§3 收窄判据一字未动，非弃权框仍须满足；"
                                "几何门面积比出局条目无回升，不因本轮变更"
                                "放松"),
            },
        },
        "method": {
            "source_of_r8_detail": (
                "calibration-run-r8.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36/s39 deviation_note 口径：本轮对 R8 与 "
                "R9 均以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5（含 None=无交集）"
                "无条目；近邻且视角不符=view_gate；近邻且面积比>上限="
                "area_ratio_rejected（几何门）；近邻且面积比≤上限且类别"
                "不符=category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r8_prep1_candidate_pairs": r8_replays["prep1"][
                    "candidate_pairs"],
                "r8_applied_candidate_pairs": r8_replays["applied"][
                    "candidate_pairs"],
                "r9_prep1_candidate_pairs": r9_replays["prep1"][
                    "candidate_pairs"],
                "r9_applied_candidate_pairs": r9_replays["applied"][
                    "candidate_pairs"],
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R8 applied=1 对且恰"
                         "为 matches、prep1=0；R9 两态均 0；全部复现）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R8T/R8B 与 R9T/R9B 来自不同 "
            "reader 实例、不同判读实例；轮内实例行为差异见 "
            "reader.reader_instance_note=混杂因素）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r8_area_ratio_rejected_entries": geo_r8,
            "r9_area_ratio_rejected_entries": geo_r9,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r8_category_mismatch_entries": cat_r8,
            "r9_category_mismatch_entries": cat_r9,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r8_entries": view_r8,
            "r9_entries": view_r9,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮重放"
                     "均无视角门条目——R8 bottom 3 旗中 1 条非弃权"
                     "（R8B-001，与全部同态 top GT containment<0.5 未及"
                     "视角门）；R9 bottom 2 旗全弃权（无非弃权样本）；"
                     "R9 三条非弃权旗全在 top 视角、与同态 GT（13 条均 "
                     "side=top）零交集（containment=None=无交集），未及"
                     "视角门。"),
        },
        "gate_chain_since_r6": chain,
        "r9_specific_observations": [
            "R9 三条非弃权旗（R9T-001/R9T-002 courtyard_crowding、"
            "R9T-005 silk_readability）与同态 GT 全部条目零交集"
            "（containment=None=无交集，未及 GT 邻域）——与 R8 R8T-004"
            "（containment 0.838782 命中 AP-8）相比定位未及 GT 邻域；"
            "matches 1→0；gt_recall_total 0.076923（1/13）→0.0（0/13）。",
            "R9 零 suspicious_reroute 旗标（弃权+非弃权合计 0；R8 基线="
            "1 条 R8T-014 弃权旗）；两个 top reader 的 reading_notes 均"
            "明确报告本轮未观察到蛇形/等长类规则折叠形态——示例 c 判据"
            "无适用对象（刺激本体缺席；见 hypothesis_test."
            "mechanism_observation，机制观察单列不凌驾字母裁决）。",
            "R9 弃权 8/11（0.727273）——R8 4/18（0.222222）入线后回升"
            "破线（>0.5，APR-0011 abstain_rate_le_0.5 单分项 not_met 如"
            "实）；分视角 top 6/9（0.666667）、bottom 2/2（1.0）；"
            "reader 实例行为差异（四实例全部 Read 直读、prep1-top 三次 "
            "Read 分区复核、prep1-top 最终消息附非 JSON 杂音已剥离）与"
            "跨轮实例不同=混杂因素，如实入账（reader_instance_note）。",
            "courtyard 被动追踪（prep-record 预注册）：R9 top 非弃权 "
            "courtyard 2 条（R9T-001/R9T-002，均与同态 GT 零交集、定位"
            "未及 GT 邻域）、弃权 2 条（R9T-007/R9T-008）；courtyard 类"
            "匹配 1→0（R8 R8T-004↔GT-REVC-AP-8-R1Q2 为 R9 前唯一 "
            "courtyard 命中）；GT/阈值零改动、零期望（run-r9 "
            "courtyard_tracking 节）。",
        ],
    }


# ---------------------------------------------------------------------------
# 预注册假设 (ii) 裁决（三分结构：字母裁决+机制观察+度量设计教训）
# ---------------------------------------------------------------------------

READER_NOTE_EVIDENCE = [
    {"source": "applied-top", "flag_view": "top",
     "excerpt": ("全图未见可负责任确认的 suspicious_reroute、"
                 "placement_pattern_anomaly、doc_artifact_mismatch 类"
                 "现象，故未报告该三类；亦未见规则周期性来回折叠（蛇形/"
                 "等长类）形态，r9 增补的示例 c 判据本轮无适用对象")},
    {"source": "prep1-top", "flag_view": "top",
     "excerpt": "整图未观察到呈规则、周期性来回折叠的整段连线"},
    {"source": "prep1-top", "flag_view": "top",
     "excerpt": "故本轮无 suspicious_reroute 旗标"},
    {"source": "applied-bottom", "flag_view": "bottom",
     "excerpt": ("无可视布线故 suspicious_reroute（含 §3A 类别 4 示例 c "
                 "的蛇形/等长形态判据）在本图无适用对象")},
    {"source": "prep1-bottom", "flag_view": "bottom",
     "excerpt": "未发现呈孤立、无规律绕行形态的连线"},
]


def build_hypothesis_test(run_r8: dict, agg: dict, prep: dict,
                          appl: dict, attribution: dict,
                          parsed_notes: dict) -> dict:
    """假设 (ii) 裁决节（预注册判据执行；三分结构，两分如实分离）。

    字母裁决（唯一正式裁决）=判据 r9-prep-record.json hypothesis_test
    原文：support=「R9 盲读全视角 reroute 类旗标产量（弃权+非弃权合计）
    =0（基线 r8=1），且其余类别非弃权旗标仍守 §3 收窄判据（几何门
    面积比出局条目无回升）」；reject=「R9 reroute 类旗标产量 ≥1」。
    实测 reroute 产量=0 且几何门 0→0 无回升 ⇒ (ii) 获支持（字母口径）。
    机制观察与度量设计教训单列、不凌驾、不改写字母裁决；机制观察如实
    指出：刺激本体缺席，产量=0 无法归因于判据化解。
    """
    prep_doc = _json_load(REL_PREP_R9)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    strat_r8 = _stratified_abstain(run_r8["states"])
    strat_r9 = _stratified_abstain({"prep1": prep, "applied": appl})
    reroute_r8 = ht["baseline_reference"]["reroute_class_flag_production_total"]
    reroute_r9 = reroute_production({"prep1": prep, "applied": appl})
    support_zero = reroute_r9 == 0
    geo_r9 = attribution["channel_1_geometry_gate"][
        "r9_area_ratio_rejected_entries"]
    geo_r8 = attribution["channel_1_geometry_gate"][
        "r8_area_ratio_rejected_entries"]
    guard_ok = len(geo_r9) == 0 and len(geo_r9) <= len(geo_r8)
    supported = support_zero and guard_ok
    verdict = "supported" if supported else "not_supported"
    verdict_text = (
        "按预注册判据（r9-prep-record.json hypothesis_test 原文）=获支持"
        "（字母口径，唯一正式裁决）：R9 盲读全视角 reroute 类旗标产量"
        "（弃权+非弃权合计）实测 0（四份原始件零 suspicious_reroute "
        "旗标；基线 r8=1），且其余类别非弃权旗标仍守 §3 收窄判据（几何"
        "门面积比出局条目 R8=0→R9=0 无回升）——support_condition 两"
        "要件均满足。字母裁决如实执行、结果无论方向均如实入账；机制"
        "观察与度量设计教训单列于后，不凌驾、不改写字母裁决。注意："
        "获支持≠判据被证明有效——机制观察如实单列：本轮 reroute 类"
        "刺激本体缺席，产量=0 无法归因于判据化解，「判据有效」证据"
        "不足。")
    # 机制观察证据：摘录必须逐字来自对应 reader-raw 的 reading_notes
    for ev in READER_NOTE_EVIDENCE:
        if ev["excerpt"] not in parsed_notes[ev["source"]]:
            _fail(f"机制观察摘录与 reader 原文不符: {ev['source']}")
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=supported "
                 "不因本观察改写）"),
        "reroute_flag_production": {
            "r8": reroute_r8,
            "r8_detail": ht["baseline_reference"]["reroute_class_detail"],
            "r9": reroute_r9,
            "r9_detail": ("四份原始件零 suspicious_reroute 旗标（弃权+"
                          "非弃权合计，全视角）"),
        },
        "reader_note_evidence": READER_NOTE_EVIDENCE,
        "observation": (
            "两个 top reader 的 reading_notes 均明确报告本轮未观察到"
            "蛇形/等长类规则折叠形态——示例 c 判据无适用对象（applied-"
            "top 原文：「亦未见规则周期性来回折叠（蛇形/等长类）形态，"
            "r9 增补的示例 c 判据本轮无适用对象」；prep1-top 原文：「"
            "整图未观察到呈规则、周期性来回折叠的整段连线」「故本轮无 "
            "suspicious_reroute 旗标」）；两个 bottom reader 亦报告无"
            "可视布线/无孤立无规律绕行（见 reader_note_evidence 逐字"
            "摘录，落盘前经与 reader-raw 原文 substring 校验）。即 "
            "reroute 类产量=0 无法归因于判据化解——刺激本体缺席，"
            "「判据有效」证据不足。"),
        "conclusion": (
            "字母裁决获支持（reroute 产量 0+守门无回升）≠ 示例 c 判据"
            "有效；本轮证据与「刺激缺席」同样相容——刺激缺席时判据无"
            "适用对象，「判据化解」假说在本轮未被检验（「正确测出无效"
            "同样是有效证据」的镜像面：测出『零产量』不等于测出『判据"
            "起效』）"),
        "confounder_note": (
            "跨轮 reader 实例不同+轮内实例行为差异（四实例全部 Read "
            "直读、prep1-top 三次 Read 分区复核，见 reader.reader_"
            "instance_note）=混杂因素；每格 n=1 无统计效力；development "
            "域方向性描述，不构成已证因果关系"),
    }
    metric_design_lesson = {
        "role": ("度量设计教训（如实，供未来预注册参考；本轮不追溯"
                 "适用）"),
        "lesson": (
            "本轮为 r8 度量教训前瞻落地首轮（主通道=现象类旗标产量"
            "计数，替代旗标内弃权率）：本轮实测暴露「产量计数无法区分"
            "『判据化解』与『刺激缺席』」——reroute 类产量=0 既与「"
            "判据化解了疑似形态」相容、也与「本轮渲染中根本不存在该类"
            "形态」相容（reader 判读注记支持后者：两 top reader 均报告"
            "未观察到该类形态）。产量计数作为主通道，在刺激可能缺席的"
            "轮次不具备归因分辨力。"),
        "status": ("下一轮协议侧候选教训（如实登记）：未来轮须预注册后"
                   "采用（如产量计数与刺激存在性核验配对、或刺激受控"
                   "渲染），不得回溯改判本轮（本轮字母裁决=supported "
                   "维持）"),
    }
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R9,
                                "sha256": _sha(REL_PREP_R9)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "test_design": ht["test_design"],
            "null_result_note": ht["null_result_note"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "measurement": {
            "reroute_class_production_r8": reroute_r8,
            "reroute_class_production_r8_detail":
                ht["baseline_reference"]["reroute_class_detail"],
            "reroute_class_production_r9": reroute_r9,
            "reroute_class_production_r9_detail": (
                "四份原始件零 suspicious_reroute 旗标（弃权+非弃权合计，"
                "全视角；比较器对盘面旗标按类别复算一致）"),
            "support_threshold": 0,
            "reject_threshold_ge": 1,
            "reroute_production_zero": support_zero,
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "其余类别非弃权旗标面积比出局条目 R8=0→R9=0（无回升）；"
                    "R9 三条非弃权旗标与同态 GT 全部条目零交集"
                    "（containment=None=无交集），未及几何门——守门通过"
                    "（守门观察如实记录）"),
                "guard_ok": guard_ok,
                "note": ("守门通道观察是 support_condition 第二要件（非"
                         "额外守门条款）：两要件均满足→字母裁决=获支持"),
            },
            "aggregate_context": {
                "abstain_rate_r8": run_r8["aggregation"][
                    "abstain_rate_total"],
                "abstain_rate_r9": agg["abstain_rate_total"],
                "note": ("聚合弃权率 0.222222（4/18）→0.727273（8/11）"
                         ">0.5 回升破线——R8 首次入线后未续上，联合评价 "
                         "APR-0011 四项如实执行（gt_recall 0.0、"
                         "seed_match_rate 0.0、abstain_rate 0.727273 均"
                         "未达暂行线→joint=not_met）。聚合口径如实记录，"
                         "不改变字母裁决（字母判据=reroute 类产量+守门，"
                         "非聚合弃权率）"),
            },
        },
        "verdict": verdict,
        "verdict_rule": (
            "support=「R9 盲读全视角 reroute 类旗标产量（弃权+非弃权"
            "合计）=0（基线 r8=1），且其余类别非弃权旗标仍守 §3 收窄"
            "判据（几何门面积比出局条目无回升），则假设获支持」；"
            "reject=「R9 reroute 类旗标产量 ≥1（该类形态仍未被判据"
            "化解），则假设不获支持」（r9-prep-record.json "
            "hypothesis_test 判据原文，轮后如实执行；结果无论方向均"
            "如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_design_lesson": metric_design_lesson,
        "stratified_observation": {
            "top": {"r8_rate": strat_r8["top"]["rate"],
                    "r8_fraction": strat_r8["top"]["fraction"],
                    "r9_rate": strat_r9["top"]["rate"],
                    "r9_fraction": strat_r9["top"]["fraction"],
                    "direction": "回升（top 2/15=0.133333→6/9=0.666667；"
                                 "与旗标分母骤缩并存，如实记账）"},
            "bottom": {"r8_rate": strat_r8["bottom"]["rate"],
                       "r8_fraction": strat_r8["bottom"]["fraction"],
                       "r9_rate": strat_r9["bottom"]["rate"],
                       "r9_fraction": strat_r9["bottom"]["fraction"],
                       "direction": "回升（bottom 2/3=0.666667→2/2=1.0）"},
            "confounder_note": (
                "跨轮 reader 实例不同=混杂因素；轮内实例行为差异（全部 "
                "Read 直读、prep1-top 三次 Read 分区复核）=额外混杂因素；"
                "每格 n=1 无统计效力；development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_courtyard_tracking(prep: dict, appl: dict, run_r8: dict) -> dict:
    """courtyard 被动追踪（r9-prep-record 预注册；零阈值改动、零期望）。"""
    prep_doc = _json_load(REL_PREP_R9)
    note_quote = prep_doc["hypothesis_test"]["courtyard_tracking_note"]
    non_abstain_rows, abstain_rows = [], []
    for st, blk in (("prep1", prep), ("applied", appl)):
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
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
            non_abstain_rows.append({
                "flag_id": f["flag_id"], "state": st,
                "view": blk["flag_views"][f["flag_id"]],
                "frame_box_pct": f["frame_box_pct"],
                "gt_entries_checked": gt_total,
                "containment_none_count": none_cnt,
                "containment_all_none": none_cnt == gt_total,
                "area_ratio_min": min(ars) if ars else None,
                "area_ratio_max": max(ars) if ars else None,
                "matches": 0,
                "note": ("与同态 GT 全部条目零交集（containment=None）"
                         "→ 定位未及 GT 邻域（非阈值问题："
                         "CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 声明"
                         "常量零改动）"),
            })
    non_abstain_rows.sort(key=lambda r: r["flag_id"])
    abstain_rows.sort(key=lambda r: r["flag_id"])
    return {
        "note_source": {"path_rel": REL_PREP_R9, "sha256": _sha(REL_PREP_R9),
                        "quote": note_quote},
        "declaration": ("被动追踪（prep-record 预注册）：如实记录 "
                        "courtyard 类旗标匹配表现；GT/阈值零改动、零"
                        "期望、不得为提高命中调阈值"),
        "r9_courtyard_flags": {
            "non_abstain": non_abstain_rows,
            "abstain": abstain_rows,
            "abstain_note": "弃权旗不参与匹配（abstain 单列）",
        },
        "courtyard_matches_r9": sum(r["matches"] for r in non_abstain_rows),
        "courtyard_matches_r8": 1,
        "courtyard_matches_r8_detail": (
            "R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、面积比 "
            "2.688288；run-r8 在案）——R9 前唯一 courtyard 命中"),
        "threshold_note": ("CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0 "
                           "声明常量零改动；零期望、不为提高命中调阈值"),
    }


def build_run() -> dict:
    """run-r9 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    attribution = build_channel_attribution(run_r6, run_r7, run_r8,
                                            prep, appl)
    agg = _aggregate(prep, appl)
    comp = _compliance(agg)
    parsed_notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    hyp = build_hypothesis_test(run_r8, agg, prep, appl, attribution,
                                parsed_notes)
    courtyard = build_courtyard_tracking(prep, appl, run_r8)

    prep_r9 = _json_load(REL_PREP_R9)
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
            "五键投影（process-v1 §2 步骤3）"),
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R9, "role": "r9_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R9)},
        {"path_rel": REL_GUIDANCE_R9,
         "role": "observation_guidance_r9_preregistration",
         "sha256": _sha(REL_GUIDANCE_R9)},
        {"path_rel": REL_GUIDANCE_R8, "role": "observation_guidance_r8_baseline",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_DEV_R8,
         "role": "r8_dev_record_preregistration_source",
         "sha256": _sha(REL_DEV_R8)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_PREP_R8, "role": "r8_prep_record_witness_source",
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
        "kind": "tl2_calibration_run_r9",
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
            "components": [
                "存在性/类别判据示例增补（observation-guidance-r9.md "
                "§3A，恰一项、单变量轮）：§3A 类别 4 suspicious_reroute "
                "增补示例 c（示例 a、b 原文保留）——「整段连线呈规则、"
                "周期性的来回折叠形态（蛇形/等长匹配类布线的常见样式）"
                "时，该规则周期形态本身可按第 4 节存在性判断一般判据"
                "推理——同类通用布线样式的常规设计解释是候选解释之一；"
                "形态不规则、无规律的绕行仍按关注现象处理。（示例=判据"
                "说明，非期望清单，不代表图中存在此类现象。）」；另在 "
                "§3A 末尾（第 6 类示例之后、§4 之前）增补一条 r9 对照"
                "说明（措辞一字不改地使用包指令给定文本）；§4 三路出口"
                "与反放宽条款原文保留（不降低任何存在性、归类、定位或"
                "报告的责任门槛）",
            ],
            "unchanged_components": list(prep_r9["unchanged_components"]),
            "attribution_note": (
                "r9-prep-record.json attribution_plan：本轮恰一项变更、"
                "检验恰一个假设（r8-dev-record 预注册候选 (ii)，"
                "r8-dev-record-candidate-ii）——主通道=reroute 类旗标"
                "产量计数（弃权+非弃权合计，基线 r8=1；support=0 且守门"
                "通过→获支持；reject=≥1→不获支持）；守门通道=其余类别"
                "非弃权旗 frame_box_pct 几何门（面积比出局条目无回升，"
                "§3 收窄判据一字未动）。轮后按 reroute 类旗标产量变化"
                "方向归因（见 run-r9 hypothesis_test 三分裁决节：字母"
                "裁决唯一正式、机制观察与度量设计教训单列不凌驾——本轮"
                "机制观察：刺激本体缺席，产量=0 无法归因于判据化解）；"
                "跨轮 flag_id 不构成同旗配对，归因是通道级不是旗级。"
                "渲染零变更下 R8→R9 任何 reader 表现变化首先归因于 §3A "
                "示例 c 增补与读者实例行为差异（reader_instance_note，"
                "如实入账），而非内容、图层或分辨率。"),
            "ref": {"path_rel": REL_PREP_R9, "sha256": _sha(REL_PREP_R9)},
        },
        "protocol": {"protocol_id": "evaluation-protocol-v1",
                     "sha256": _sha(REL_PROTOCOL)},
        "naming_constraints": (
            "seed_match_rate 禁称 precision/FPR；reader_unmatched_ids="
            "unmatched/unadjudicated，不据此计算误报率；框命中不构成"
            "电气事实"),
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
                     "全部关闭（r8 轮同日审计，结论本轮延续引用）；该"
                     "审计非本轮预注册件（deviations 在案），其结论维持"
                     "本轮 GT 零改动；round9-dev-record gt_audit_ref/"
                     "next_iteration_targets 引用其结论（GT 侧不再有"
                     "候选）"),
        },
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r8 相同）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r9 §4：r8 两条显式判据（弃权适用于存在/归类不确定；"
                    "弃权不适用于仅范围不确定）、存在性一般判据（系统性"
                    "重复 vs 孤立不一致启发）与三路出口显式化原文保留；"
                    "§3A 类别 4 增补示例 c（规则周期折叠形态按 §4 存在性"
                    "一般判据推理的候选解释说明；形态不规则、无规律的"
                    "绕行仍按关注现象处理；示例=判据说明，非期望清单；"
                    "反放宽条款原样）；abstain=true=现象是否存在或归属"
                    "哪类无法负责任地判断；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("两波并行派发（与 R7/R8 相同）：波 1="
                                      "applied-top 与 applied-bottom 并行；"
                                      "波 2=prep1-top 与 prep1-bottom 并行；"
                                      "视角内 applied→prep1 串行顺序保持；"
                                      "top/bottom 各一独立盲读；每图独立"
                                      "判读；视角内连续编号"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R9,
                                 "sha256": _sha(REL_GUIDANCE_R9),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R8,
                                     "sha256": _sha(REL_GUIDANCE_R8)},
                                 "change_note": GUIDANCE_CHANGE_NOTE},
            },
            "note": ("轮次预注册链：r8-dev-record.json（437e149c…，"
                     "next_iteration_targets[2]/[3] 两项原文被 r9-prep-"
                     "record 逐字摘录预注册）→r9-prep-record.json"
                     "（dd979632…）先于本轮盲读落盘（零 GT 暴露声明在案 "
                     "no_visual_reading=true；渲染复用见证=四 PNG 盘上"
                     "实测 sha 与见证常量逐一相等+渲染输入侧冻结 PDF "
                     "复核一致；见证常量源=r8-prep-record.json，在案）；"
                     "observation-guidance-r9.md 落盘即冻结（恰一项预"
                     "注册变更：§3A 类别 4 增补示例 c+§3A 末尾对照说明）；"
                     "GT 重投影（derivation-log-r5.json，13 条 "
                     "frame_box_pct_r5）已在案沿用（渲染未变=零新派生）；"
                     "盲读后本包只做比对与记录（读者产物零改动）。GT "
                     "冻结纪律：轮后未增删改；gt-audit-r1 结论维持 GT "
                     "零改动（三候选关闭，gt_audit_reference 在案）。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "r7_run": {"path_rel": REL_RUN_R7, "sha256": _sha(REL_RUN_R7)},
            "r8_run": {"path_rel": REL_RUN_R8, "sha256": _sha(REL_RUN_R8)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）与 R8（§4 存在性判据增补轮）run "
                     "在案；轮间对比见 round9-dev-record.json 的方向性"
                     "观察与 channel_attribution、hypothesis_test"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器与通道重放为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-07-r9（事件序="
            "预注册冻结（r8-dev-record（437e149c…，在案）→r9-prep-"
            "record+guidance-r9）→复用渲染见证→盲读→比对记录；同日在"
            "案=gt-audit-r1 只读 GT 源审计（r8 轮落盘，本轮延续引用其"
            "结论，GT 零改动维持））"),
    }


DEV_OBSERVATIONS = [
    "R8→R9 旗标量对照：18→11（非弃权 14→3、弃权 4→8），聚合弃权率 "
    "0.222222（4/18）→0.727273（8/11）——R8 首次入线（≤0.5）后回升破线"
    "（>0.5，APR-0011 abstain_rate_le_0.5 单分项 not_met 如实）；分态"
    "弃权率 applied 0.090909（1/11）→0.6（3/5）、prep1 0.428571（3/7）→"
    "0.833333（5/6）。零仪器变更（渲染逐字节复用，PNG 见证在案）下，"
    "该变化首先归因于 §3A 示例 c 增补与读者实例行为差异"
    "（reader_instance_note：四实例全部 Read 直读=仪器异质性较 R8 降低；"
    "跨轮实例不同=混杂因素），而非内容、图层或分辨率。",
    "分视角弃权率：top 0.133333（2/15）→0.666667（6/9）、bottom "
    "0.666667（2/3）→1.0（2/2）双双回升；旗标分母骤缩（top 15→9、"
    "bottom 3→2）与弃权占比上升并存，如实记账（分层观察不凌驾字母"
    "裁决）。",
    "matches 1→0：R9 三条非弃权旗（R9T-001/R9T-002 courtyard_crowding、"
    "R9T-005 silk_readability）与同态 GT 全部条目零交集（containment="
    "None=无交集，未及 GT 邻域，非阈值问题）；gt_recall_total 0.076923"
    "（1/13）→0.0（0/13）、seed_match_rate_total 0.071429（1/14）→0.0"
    "（0/3，诊断口径，禁称 precision/FPR）。",
    "通道归因（vs R8，预注册重放方法）：几何门面积比出局 0→0（R7 起"
    "连续空）；类别门 1→0（R8=R8T-010↔GT-REVC-P1-R4J3 containment "
    "1.0、面积比 4.961299；R9 三条非弃权旗零交集、类别门无生效实例）；"
    "视角门 0→0（R9 bottom 2 旗全弃权，无非弃权样本）。通道链自 r6 起："
    "几何门 r6=1→r7=0→r8=0→r9=0；类别门 r6=1→r7=0→r8=1→r9=0。",
    "预注册假设 (ii) 字母裁决=获支持（reroute 类旗标产量 0+守门无回升，"
    "r9-prep-record 判据原文执行；唯一正式裁决）；机制观察单列（不凌驾）："
    "两个 top reader 的 reading_notes 均明确报告未观察到蛇形/等长类规则"
    "折叠形态——示例 c 判据无适用对象，reroute 产量=0 无法归因于判据"
    "化解（刺激本体缺席），「判据有效」证据不足；度量设计教训如实入账"
    "（本轮为 r8 度量教训【产量计数】前瞻落地首轮，实测暴露「产量计数"
    "无法区分『判据化解』与『刺激缺席』」——下一轮协议侧候选，不追溯"
    "改判本轮字母裁决）。",
    "R9 四实例全部 Read 直读内嵌图像（无 URL 转传、无外部视觉工具）——"
    "比 R8（3/4 借助 analyze_image）仪器异质性更低；prep1-top 对同一 "
    "PNG 三次 Read 分区复核（reader 原文在案）；prep1-top 最终消息 JSON "
    "对象后附一行非 JSON 杂音（无关营销字句），落盘只保留纯 JSON 主体、"
    "parse 校验通过（输出格式异常，非盲读违规——其输入仍只有指引+PNG）。"
    "跨轮 reader 实例不同=混杂因素，每格 n=1。",
    "courtyard 被动追踪（prep-record 预注册）：R9 top 非弃权 courtyard "
    "2 条（R9T-001/R9T-002）与同态 GT 零交集（定位未及 GT 邻域、非阈值"
    "问题）、弃权 2 条（R9T-007/R9T-008）；courtyard 类匹配 1→0（R8 "
    "R8T-004↔GT-REVC-AP-8-R1Q2 为 R9 前唯一 courtyard 命中）；GT/阈值"
    "零改动、零期望。",
    "跨轮 flag_id 不构成同旗配对（R8T/R8B 与 R9T/R9B 来自不同 reader "
    "实例）；通道归因是通道级不是旗级（run-r9 channel_attribution."
    "pairing_caveat）；重放与 compare_v3 对拍一致（R8 applied 1 对="
    "matches、prep1 空；R9 两态均空）。",
]

DEV_NEXT_TARGETS = [
    "弃权率回升（0.222222→0.727273）的实例异质性归因追问（候选，须预"
    "注册后执行）：R9 弃权率回升与 reader 实例更替完全混淆（每格 n=1，"
    "development 域只描述不断言）——候选方案：(a) 同指引重复轮（同 r9 "
    "指引+同 R5 渲染再盲读一轮，分离实例差异与指引效应）；(b) 多 reader "
    "重复读（同一 PNG 多实例并行判读，分离实例内/实例间方差）。两案"
    "均为流程侧候选，须先预注册再执行。",
    "渲染侧 bottom 图层清单仍是候选（r6/r7/r8/r9-prep-record 在案候选；"
    "bottom 面无封装/走线几何，gt-audit-r1 A1 在案；R9 bottom 2 旗全"
    "弃权、无可视布线/丝印可评——与 R8B-003 元层弃权同方向）；属渲染"
    "侧变更，须预注册+声明零仪器变更纪律例外。",
    "courtyard 密集旗追踪延续（指引侧观察候选）：R9 top 非弃权 courtyard "
    "2 条（R9T-001/R9T-002）与同态 GT 零交集=定位未及 GT 邻域（非阈值"
    "问题）；继续被动追踪（GT/阈值零改动；不得为提高命中调阈值；无"
    "期望）。",
    "度量侧教训（协议侧候选，本轮实测导出）：产量计数无法区分『判据"
    "化解』与『刺激缺席』——下一轮候选=产量计数与刺激存在性核验配对"
    "（如刺激受控渲染、或 reroute 类形态存在性先验核验），须预注册后"
    "采用，不得回溯改判本轮（本轮字母裁决=supported 维持）。",
    "GT 侧不再有候选：r8 轮同日只读审计 gt-audit-r1（1f20554a…）三候选"
    "全部关闭（bottom GT=无源已关闭、reroute GT=无源已关闭、L1NB 框径="
    "合理维持现框），本轮延续零改动——GT 侧已全部关闭，后续迭代回归"
    "指引侧/渲染侧/协议侧。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）；连续达标计数 0（R8 后）→0（本轮），正式采纳"
    "门槛未达成。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round9-dev-record 文档构建（T3；单向引用 run-r9 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    trend_rows = []
    for r in (5, 6, 7, 8):
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
        "round": "r9", "round_id": run_doc["round_id"],
        "flag_count_total": agg["flag_count_total"],
        "abstain_count_total": agg["abstain_count_total"],
        "abstain_rate_total": agg["abstain_rate_total"],
        "matches_total": agg["matches_total"],
        "gt_recall_total": agg["gt_recall_total"],
        "seed_match_rate_total": agg["seed_match_rate_total"],
        "joint_evaluation": comp["joint_evaluation"],
        "source": {"path_rel": REL_RUN_R9, "sha256": run_sha},
    })
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round9_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域单变量指引侧变更轮（第九轮）：本轮零仪器变更"
            "——复用 R5 冻结渲染件（零重渲染，PNG 见证在案），唯一变更="
            "判读指引 §3A 类别 4 suspicious_reroute 增补示例 c（蛇形/"
            "等长规则周期形态按 §4 存在性一般判据推理的候选解释说明）+"
            "§3A 末尾对照说明（恰一项变更目标 "
            "reroute-serpentine-criterion-example-c，预注册于盲读前）；"
            "并落地 round8-dev-record 度量设计教训的协议侧前瞻预注册"
            "（主通道=现象类旗标产量计数，自本轮起适用、不追溯 r8）；"
            "检验 R8 预注册候选假设 (ii)（判据=r9-prep-record.json "
            "hypothesis_test，轮后如实执行，三分结构：字母裁决唯一正式+"
            "机制观察单列+度量设计教训）；GT 集/协议与度量版本/比较器"
            "阈值与 R8 一致（GT 重投影沿用 derivation-log-r5——渲染未变="
            "零新派生；gt-audit-r1 三候选关闭结论延续，GT 零改动维持）；"
            "按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "preregistration_chain_note": (
            "预注册链（含哈希）：r8-dev-record.json（437e149c…，"
            "next_iteration_targets[2]/[3] 两项候选原文）→r9-prep-record"
            ".json（dd979632…，逐字摘录两项原文预注册=本轮执行依据）→"
            "run-r9（本链执行落盘）；observation-guidance-r9.md 落盘即"
            "冻结（锚 a0c10154…）；渲染复用见证源=r8-prep-record.json"
            "（237920a5…）"),
        "run_record_ref": {"path_rel": REL_RUN_R9, "sha256": run_sha},
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
                     "模式=两波并行（与 R7/R8 相同）；读者实例行为差异"
                     "（四实例全部 Read 直读、prep1-top 三次 Read 分区"
                     "复核、prep1-top 最终消息附非 JSON 杂音已剥离）如实"
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
            "after_r8": {"consecutive_met_count": 0,
                         "note": "R8 联合评价 not_met（在案），连续达标"
                                 "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价 not_met（gt_recall 0.0 "
                                   "与 seed_match_rate 0.0 未达暂行线；"
                                   "abstain_rate 0.727273>0.5 回升破线——"
                                   "R8 首次入线后未续上）"},
            "consecutive_met_count_now": 0,
            "by_round": trend_rows,
            "note": "连续达标计数变动：0（R8 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r8": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，零仪器变更、单变量指引侧变更轮：§3A "
            "类别 4 增补示例 c）11 旗标中 8 弃权、3 非弃权，matches=0："
            "gt_recall=0.0（0/13）、seed_match_rate=0.0（0/3，诊断口径，"
            "禁称 precision/FPR）、abstain_rate=0.727273（8/11，较 R8 "
            "0.222222 回升破线），联合评价 not_met（gt_recall、"
            "seed_match_rate、abstain_rate 三项均未达 APR-0011 暂行线；"
            "诊断对照，非采纳门；连续达标计数 0→0）。预注册假设 (ii) "
            "裁决（按 r9-prep-record hypothesis_test 判据）=获支持（"
            "字母口径，唯一正式裁决）：reroute 类旗标产量 0（基线 r8=1）"
            "且几何门面积比出局条目 0→0 无回升；机制观察单列（不凌驾）："
            "两个 top reader 判读注记均明确报告未观察到蛇形/等长类规则"
            "折叠形态——示例 c 判据无适用对象，产量=0 无法归因于判据"
            "化解（刺激本体缺席），「判据有效」证据不足（获支持≠判据"
            "有效）；度量设计教训如实入账（产量计数无法区分化解与刺激"
            "缺席——下一轮协议侧候选，不回溯改判本轮）。读者实例行为"
            "差异（四实例全部 Read 直读、prep1-top 三次 Read 分区复核、"
            "一条最终消息附非 JSON 杂音已剥离）如实登记为混杂因素；"
            "弃权率回升与实例更替完全混淆（每格 n=1），归因追问列入"
            "下一迭代候选。GT 侧三候选经 gt-audit-r1 全部关闭（延续"
            "零改动，GT 侧不再有候选）。不做「能力已修复/已达成」类"
            "断言；in_calibrated_range 恒 False。本批证据按协议 v1 §4 "
            "属 development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R8 对照基线=calibration-run-r8.json（3c580eb3…，在案）；"
            "R7 对照基线=calibration-run-r7.json（62b34b71…，在案）；"
            "轮间对比只做方向性描述。",
            "通道归因方法：照抄 run-r8 channel_attribution 的重放口径"
            "（deviation_note 承接），R8 与 R9 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r9 "
            "channel_attribution.method）。",
            "读者实例行为偏差如实记录：四实例全部 Read 工具直读内嵌图像"
            "（无 URL 转传、无外部视觉工具；较 R8 三实例经外部视觉分析"
            "工具读图的仪器异质性更低）；prep1-top 实例对同一 PNG 三次 "
            "Read 分区复核；prep1-top 实例最终消息在 JSON 对象后附一行"
            "非 JSON 杂音文本（无关营销字句），编排侧落盘只保留纯 JSON "
            "主体、parse 校验通过（输出格式异常，非盲读违规——其输入仍"
            "只有指引+PNG）。跨轮 reader 实例不同=混杂因素，每格 n=1。",
            "假设裁决三分结构纪律：字母裁决=唯一正式裁决（预注册判据"
            "原文执行）；机制观察与度量设计教训单列，不得凌驾或改写字母"
            "裁决；本轮字母裁决=supported 维持不变（获支持≠判据有效——"
            "刺激缺席见 mechanism_observation）。",
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


def _assert_observation_numbers(run_doc: dict, run_r8: dict,
                                attribution: dict, parsed: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    agg = run_doc["aggregation"]
    ab = agg["abstain_rate_total"]
    if f"{ab}" != "0.727273" or "0.727273（8/11）" not in obs:
        _fail("观察文本弃权率与实测不一致")
    if agg["abstain_count_total"] != 8 or agg["flag_count_total"] != 11:
        _fail("观察文本弃权记账与实测不一致")
    if agg["scored_total"] != 3 or agg["matches_total"] != 0 \
            or agg["gt_matched_total"] != 0:
        _fail("观察文本非弃权/匹配记账与实测不一致")
    if run_doc["hypothesis_test"]["verdict"] != "supported":
        _fail("假设 (ii) 字母裁决与预注册判据复算不符")
    if reroute_production(run_doc["states"]) != 0:
        _fail("reroute 类产量与字母裁决输入不一致")
    if reroute_production(run_r8["states"]) != 1:
        _fail("R8 reroute 基线产量与 prep-record 登记不符")
    for need in ("0.222222", "0.6", "0.833333", "0.133333", "0.666667",
                 "1.0", "0.090909", "0.428571", "0.076923", "0.071429",
                 "18→11", "1→0", "4.961299", "0/13", "0/3", "8/11"):
        if need not in obs:
            _fail(f"观察文本缺实测数字 {need}")
    # 分视角记账与 run 落盘一致
    by_view = agg["abstain_rate_by_view"]
    if by_view["top"] != 0.666667 or by_view["bottom"] != 1.0:
        _fail("分视角弃权率与观察文本不一致")
    # 通道条目数与文本一致（几何 R8 0→R9 0；类别 R8 1→R9 0）
    geo8 = attribution["channel_1_geometry_gate"][
        "r8_area_ratio_rejected_entries"]
    geo9 = attribution["channel_1_geometry_gate"][
        "r9_area_ratio_rejected_entries"]
    cat8 = attribution["channel_2_category_gate"]["r8_category_mismatch_entries"]
    cat9 = attribution["channel_2_category_gate"]["r9_category_mismatch_entries"]
    if not (len(geo8) == 0 and len(geo9) == 0
            and len(cat8) == 1 and len(cat9) == 0):
        _fail("通道条目数与观察文本声明不一致")
    if cat8[0]["flag_id"] != "R8T-010" \
            or cat8[0]["gt_id"] != "GT-REVC-P1-R4J3":
        _fail("类别门条目与观察文本声明不一致")
    # courtyard 追踪与实测一致（R9 top 非弃权 courtyard=2；R8=6）
    r9_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_doc, "top")
                    if f["category"] == "courtyard_crowding"]
    r8_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_r8, "top")
                    if f["category"] == "courtyard_crowding"]
    if sorted(r9_courtyard) != ["R9T-001", "R9T-002"] \
            or sorted(r8_courtyard) != ["R8T-002", "R8T-004", "R8T-006",
                                        "R8T-007", "R8T-012", "R8T-013"]:
        _fail("courtyard 旗计数与观察文本声明不一致")
    # courtyard 追踪明细：非弃权 2 条全部 containment 零交集
    ct = run_doc["courtyard_tracking"]["r9_courtyard_flags"]["non_abstain"]
    if [r["flag_id"] for r in ct] != ["R9T-001", "R9T-002"] \
            or not all(r["containment_all_none"] and r["matches"] == 0
                       for r in ct):
        _fail("courtyard 追踪明细与实测不一致")
    # R8 matches 明细数值（R8T-004 vs AP-8，基线完整性）
    matches8 = run_r8["states"]["applied"]["compare_v3"]["matches"]
    if len(matches8) != 1 or matches8[0]["flag_id"] != "R8T-004" \
            or matches8[0]["containment"] != 0.838782 \
            or matches8[0]["area_ratio"] != 2.688288:
        _fail("R8 基线 matches 明细与在案值不一致")
    # R8T-010 vs R4J3 类别门数值
    blk8 = run_r8["states"]["prep1"]
    f010 = next(f for f in blk8["reader_flags"]
                if f["flag_id"] == "R8T-010")
    g = next(e for e in blk8["gt_entries"]
             if e["gt_id"] == "GT-REVC-P1-R4J3")
    if cal._round6(cal._containment(f010["frame_box_pct"],
                                    g["frame_box_pct"])) != 1.0 \
            or cal._round6(cal._area_ratio(f010["frame_box_pct"],
                                           g["frame_box_pct"])) != 4.961299:
        _fail("R8T-010 类别门数值与观察文本不一致")
    # 机制观察摘录逐字来自 reader 原文（防转述失真）
    notes = {k: parsed[k]["reading_notes"] for k in RAW_FILES}
    for ev in run_doc["hypothesis_test"]["mechanism_observation"][
            "reader_note_evidence"]:
        if ev["excerpt"] not in notes[ev["source"]]:
            _fail(f"机制观察摘录与 reader 原文不符: {ev['source']}")
    # 机制观察产量数与实测一致
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    if mo["reroute_flag_production"]["r8"] != 1 \
            or mo["reroute_flag_production"]["r9"] != 0:
        _fail("机制观察 reroute 产量与实测不一致")
    # 非弃权旗三条身份与零交集声明一致
    non_abstain = sorted(_non_abstain_flags_by_view(run_doc, "top")
                         + _non_abstain_flags_by_view(run_doc, "bottom"),
                         key=lambda f: f["flag_id"])
    if [f["flag_id"] for f in non_abstain] != ["R9T-001", "R9T-002",
                                               "R9T-005"]:
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
    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r9")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R8), run["channel_attribution"], parsed)

    # 落盘 run（防覆写护栏：字节等同→幂等跳过；不同→FAIL）→ 实测 sha
    run_status = _commit(_rel(REL_RUN_R9), run_bytes,
                         "calibration-run-r9.json")
    run_sha = _sha(REL_RUN_R9)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round9-dev-record")
    dev_status = _commit(_rel(REL_DEV_RECORD), dev_bytes,
                         "round9-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    hyp = run["hypothesis_test"]
    print(f"[s41-cal-r9] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s41-cal-r9] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s41-cal-r9] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    bv = agg["abstain_rate_by_view"]
    print(f"[s41-cal-r9] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']} "
          f"(top {bv['top']} / bottom {bv['bottom']})")
    print(f"[s41-cal-r9] hypothesis (ii): {hyp['hypothesis_id']} -> "
          f"{hyp['verdict']}（字母裁决；reroute 产量="
          f"{hyp['measurement']['reroute_class_production_r9']}，机制观察"
          f"与度量设计教训单列）")
    print(f"[s41-cal-r9] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s41-cal-r9] channel_attribution: "
          f"geo R8={len(ca['channel_1_geometry_gate']['r8_area_ratio_rejected_entries'])}"
          f"→R9={len(ca['channel_1_geometry_gate']['r9_area_ratio_rejected_entries'])}, "
          f"cat R8={len(ca['channel_2_category_gate']['r8_category_mismatch_entries'])}"
          f"→R9={len(ca['channel_2_category_gate']['r9_category_mismatch_entries'])}")
    print(f"[s41-cal-r9] commit: run={run_status} dev={dev_status}")
    for rel in (REL_RUN_R9, REL_DEV_RECORD):
        print(f"[s41-cal-r9] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s41-cal-r9] R9 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
