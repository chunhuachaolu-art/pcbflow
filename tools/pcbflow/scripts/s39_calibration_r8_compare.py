#!/usr/bin/env python
"""CAL-R8-CLOSE：reader 判读迭代第八轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s36_calibration_r7_compare.py 同构，仅输入与轮次
常量不同；R8=development 域单变量指引侧变更轮（§4 存在性判断一般
判据增补：系统性重复 vs 孤立不一致启发 + 三路出口显式化），零仪器
变更，复用 R5 冻结渲染，检验 R7 预注册候选 (i)（r7-dev-record
next_iteration_targets 首条候选方向））：

  T1  解析 4 个 reader-raw-r8-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate + 分视角（top/
      bottom）分层弃权记账 + 逐旗失败通道归因（vs R7，照 s36 重放
      方法）：applied 态=applied-top+applied-bottom 旗标 vs
      ground-truth-v2 九条（GT 重投影继续用 derivation-log-r5 的
      frame_box_pct_r5——渲染未变=重投影输入未变，board_box_mm/
      side 等其余字段与 GT 文件逐字段原样）；prep1 态=prep1-top+
      prep1-bottom 旗标 vs ground-truth-v1 四条（同重投影规则）。
      达标线=APR-0011 暂时采纳基线，逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册假设 (i) 裁决节（三分结构，两分如实分离）：(1) 字母裁决
      （唯一正式裁决，判据=r8-prep-record.json hypothesis_test 原文：
      support=bottom 层弃权率 <0.5 且 top 层守门通过；reject=bottom
      层未回落至 <0.5）；(2) 机制观察（单列，不凌驾字母裁决：化解通道
      绕过旗标产量，弃权率不测量它）；(3) 度量设计教训（协议侧候选，
      本轮不追溯适用，不得回溯改判）。
      → calibration-run-r8.json。
  T3  development 域记录（本轮性质=单变量指引侧变更轮：零仪器变更、
      复用 R5 冻结渲染；R7→R8 方向性对照与匹配位置对照（只描述不下
      能力断言）/假设 (i) 三分裁决/下一迭代目标——必须引用同日只读
      GT 审计 gt-audit-r1.json（1f20554a…）结论：bottom GT/reroute
      GT/L1NB 框径三候选全部关闭；引用 run-r8 落盘 sha 单向引用）
      → round8-dev-record.json。

通道归因纪律（vs R7；方法照抄 s34/s36 deviation_note 口径）：本轮对
R7 与 R8 均以内嵌输入（reader_flags/gt_entries/flag_views，run sha
在案）+ compare_v3 同源几何原语（calibration._containment/
_area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放
通道分类，并与各态 compare_v3 的 matches∪duplicate_reports 对拍
复核。跨轮 flag_id 不构成同旗配对（不同 reader 实例），归因是通道级
不是旗级。

读者实例披露（如实入账，不作废）：R8 四个读者实例中三个
（applied-bottom/prep1-top/prep1-bottom）因 Read 工具对其实例返回
CDN URL 而改经外部视觉分析工具（analyze_image，图像自动上传 CDN）
读取给定 PNG 本身；判读输入仍严格限于（指引+该 PNG），零 GT/零其他
文件接触；该读图方式与 R5–R7 及 R8 applied-top（本地逐区放大）不同
=轮内与跨轮读者实例差异（混杂因素），如实登记为 reader 节
reader_instance_note。

纪律：out/ 既有文件零改动（防覆写 guard；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-07 / 2026-09-07-r8）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s39_calibration_r8_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-07-r8"
ROUND_LABEL = "r8"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R7 = "out/v3-tl2/calibration/observation-guidance-r7.md"
REL_GUIDANCE_R8 = "out/v3-tl2/calibration/observation-guidance-r8.md"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_PREP_R8 = "out/v3-tl2/calibration/r8-prep-record.json"
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
REL_DEV_RECORD = "out/v3-tl2/calibration/round8-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r8-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r8-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r8-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r8-prep1-bottom.txt",
}
#: R8 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r8-prep-record（源自 r7-prep-record）脚本
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R8 复核见证=r8-prep-record
#: renders_reuse.frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r8-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r8-prep-record.json frozen_input_pdfs_check 实测值。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R7:
        "9e7a7b1322af1279c6c2cc12c248ed8157628c402834a71329256fc8ce04179d",
    REL_GUIDANCE_R8:
        "aad43270b1c88d446511737416f3cc191e0f882a925e9e03ef3af1a5ef207993",
    REL_PREP_R7:
        "e48c37fee217f3745662875640c3bef4dea27906d76ee07f85ed981815a7b3f2",
    REL_PREP_R8:
        "237920a54fa28d3f37e7926e744b51bb7c29cd8f69797c626ad2c9c7d6b01efa",
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
    RAW_FILES["applied-top"]:
        "145ef24c53c10a0e0bad9761f96517e97bd9a39a4a4e12807b46fe68ba06c912",
    RAW_FILES["applied-bottom"]:
        "6bea87f539384580c0c4c40ebab0949962391cb70066778b97e75f594ffdb5a8",
    RAW_FILES["prep1-top"]:
        "00bd8616fc253e0d10dcaf95f8f873eaaff325d3b3edae13f6dc989fff43632c",
    RAW_FILES["prep1-bottom"]:
        "81ec7f4ab869973a9c5e879f4a89a00f80618fc23ea3ee418ad2a8b2f96f19e6",
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
    "两波并行派发（与 R7 相同、与 R6 全串行不同，如实记录）：波 1="
    "applied-top 与 applied-bottom 并行（两视角编号独立）；波 2="
    "prep1-top 与 prep1-bottom 并行；视角内 applied→prep1 串行顺序保持"
    "（top R8T-001..015：applied 001..009→prep1 010..015；bottom "
    "R8B-001..003：applied 001..002→prep1 003）；盲读派发词只含图像"
    "绝对路径+observation-guidance-r8.md 路径+视角前缀+起始序号；无任何 "
    "GT 坐标/类别提示/期望缺陷描述；读图者不接触 GT/派生台账/任何校准"
    "产物路径")

#: 派发模式结构化记录（R8 与 R7 同模式：两波并行）。
PARALLEL_DISPATCH = {
    "mode": "two_wave_parallel",
    "wave_1_parallel": ["applied-top", "applied-bottom"],
    "wave_2_parallel": ["prep1-top", "prep1-bottom"],
    "within_view_serial_order": {"top": ["applied-top", "prep1-top"],
                                 "bottom": ["applied-bottom",
                                            "prep1-bottom"]},
    "flag_id_continuity": {"top": "R8T-001..015（applied 001..009→"
                                  "prep1 010..015）",
                           "bottom": "R8B-001..003（applied 001..002→"
                                     "prep1 003）"},
    "diff_note": ("R6=四图独立全串行派发（run-r6 reader.serial_dispatch "
                  "在案）；R7 起改为两波并行、视角内 applied→prep1 串行"
                  "顺序保持，R8 与 R7 派发模式相同（模式差异相对 R7 消除）；"
                  "R8 特有流程差异=读者实例读图方式差异（见 "
                  "reader_instance_note，如实入账，development 域只描述"
                  "不断言）"),
}

#: 读者实例披露（如实入账，不作废）。
READER_INSTANCE_NOTE = (
    "读者实例披露（如实入账，不作废）：R8 四个读者实例中三个"
    "（applied-bottom/prep1-top/prep1-bottom）因 Read 工具对其实例返回 "
    "CDN URL 而改经外部视觉分析工具（analyze_image，图像自动上传 CDN）"
    "读取给定 PNG 本身；判读输入仍严格限于（指引+该 PNG），零 GT/零其他"
    "文件接触；该读图方式与 R5–R7 及 R8 applied-top（本地逐区放大）不同"
    "=轮内与跨轮读者实例差异（混杂因素），如实登记于本注，不作废、"
    "不构成对判读的否定")

GUIDANCE_CHANGE_NOTE = (
    "本轮唯一变更=判读指引 §4 存在性判断一般判据增补（单变量轮）：在 "
    "r7 §4 两条显式判据（弃权适用于/弃权不适用于）原文保留的前提下，"
    "为「弃权适用于」一条增补（1）系统性重复 vs 孤立不一致启发（同类"
    "图形间规则成体系重复→更可能正常设计特征，通用 PCB 域知识内常规"
    "图形可能解释如散热辐条/热隔离盘形态、安装孔、基准点、极性标记类；"
    "孤立或不一致→更可能关注现象）与（2）三路出口显式化（判为正常设计"
    "特征→不报告；疑似但无法负责任确认→弃权路径；存在且可归类→正常"
    "报告路径）（措辞中性一般化，零具体板/位号/坐标/数量期望；r8 指引"
    "「非放宽声明」：责任标准维持 r7 语义、判「正常设计特征」与判「关注"
    "现象」承担同等判断责任）；其基线=observation-guidance-r7.md，"
    "r8-prep-record baseline 锚 9e7a7b13…；机械替换仅视角前缀 "
    "R7T/R7B→R8T/R8B 与 round_id_constant 两处")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 8 轮迭代"
    "（development 域单变量指引侧变更迭代轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "零仪器变更（单变量指引侧变更轮：§4 存在性判断一般判据增补；复用 "
    "R5 冻结渲染）")


def _fail(msg: str) -> None:
    print(f"[s39-cal-r8] FAIL: {msg}")
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

    R8 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                    "note": ("R8 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮唯一变更=判读指引 §4 "
                             "存在性判断一般判据增补，单变量轮）")},
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
                       "r7": "not_met（在案）",
                       "r8": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": ("本轮联合评价未达标（gt_recall 与 seed_match_rate "
                     "两项未达暂行线），连续计数仍为 0；abstain_rate 项 "
                     "0.222222≤0.5 为 R5 后首次满足（单分项如实记录，"
                     "不构成联合达标）" if not all_met
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
# 逐旗失败通道归因（vs R7；方法照抄 s34/s36：通道级，非旗级）
# ---------------------------------------------------------------------------

def channel_replay(flags: list, flag_views: dict, gt_entries: list) -> dict:
    """近邻失败通道重放（纯函数；与 compare_v3 同源几何原语）。

    对每个非弃权旗标与同态全部 GT 条目计算 containment/area_ratio：
    containment<CONTAINMENT_MIN → 无条目（非近邻）；
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


def build_channel_attribution(run_r7: dict, prep: dict, appl: dict) -> dict:
    """通道归因小节（vs R7；通道级分组，非旗级配对）。"""
    gt_by_state = {"prep1": prep["gt_entries"], "applied": appl["gt_entries"]}
    r7_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r7["states"][st]
        r7_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r7_replays[st], blk["compare_v3"]):
            _fail(f"R7 {st} 态通道重放与 compare_v3 对拍不一致")
    r8_replays = {}
    for st, blk in (("prep1", prep), ("applied", appl)):
        r8_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r8_replays[st], blk["compare_v3"]):
            _fail(f"R8 {st} 态通道重放与 compare_v3 对拍不一致")

    def pick(replays, failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r7 = pick(r7_replays, "area_ratio_rejected")
    geo_r8 = pick(r8_replays, "area_ratio_rejected")
    cat_r7 = pick(r7_replays, "category_mismatch")
    cat_r8 = pick(r8_replays, "category_mismatch")
    view_r7 = pick(r7_replays, "view_gate")
    view_r8 = pick(r8_replays, "view_gate")

    def _ids(rows):
        return [f"{r['flag_id']}↔{r['gt_id']}" for r in rows]

    geo_change = (
        "几何门通道（R7→R8）：面积比出局条目 0→0（两轮均空）。R8 全部 "
        "14 条非弃权旗标与同态 GT 的近邻对恰 2 个（applied：R8T-004↔"
        "GT-REVC-AP-8-R1Q2 containment 0.838782、面积比 2.688288→候选"
        "成匹配；prep1：R8T-010↔GT-REVC-P1-R4J3 containment 1.0、面积比"
        " 4.961299→类别不符出局），均满足面积比≤10——非弃权框未出现"
        "面积比出局，与 §3 收窄判据未放宽方向相容（通道级描述，非同旗"
        "配对）；R8 全局匹配 0→1（R5 后首个 matches）。")
    cat_change = (
        "类别门通道（R7→R8）：类别不符出局条目 0→1（R7=空；R8="
        f"{_ids(cat_r8)}，containment 1.0、面积比 4.961299——R8T-010 为 "
        "silk_readability 旗（右上连接器区位号连印辨读受阻），其框完全"
        "包含 GT-REVC-P1-R4J3（courtyard_crowding），视角相符、几何双"
        "条件过、类别不符出局）——类别门本轮在 containment 1.0 高重叠处"
        "生效；matches 0→1；样本量极小，只描述不断言。")
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R8, "sha256": _sha(REL_PREP_R8)},
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（r7 dev-record 预注册"
                "候选 (i)）；轮后按 bottom 层弃权率变化方向归因"
                "（r8-prep-record.json attribution_plan.declaration 原文）"),
            "primary_channel": {
                "change_id": "existence-criteria-reinforcement",
                "metric": ("bottom 视角层弃权率（相对 R7 基线 12/12=1.0；"
                           "预注册阈值 <0.5）"),
            },
            "guard_channel": {
                "metric": "top 层非弃权旗 frame_box_pct 几何门（面积比出局"
                          "条目）",
                "requirement": ("§3 收窄判据一字未动，非弃权框仍须满足；"
                                "几何门面积比出局条目无回升，不因本轮变更"
                                "放松"),
            },
        },
        "method": {
            "source_of_r7_detail": (
                "calibration-run-r7.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34/s36 deviation_note 口径：本轮对 R7 与 R8 均"
                "以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5 无条目；近邻且"
                "视角不符=view_gate；近邻且面积比>上限=area_ratio_"
                "rejected（几何门）；近邻且面积比≤上限且类别不符="
                "category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r7_prep1_candidate_pairs": r7_replays["prep1"][
                    "candidate_pairs"],
                "r7_applied_candidate_pairs": r7_replays["applied"][
                    "candidate_pairs"],
                "r8_prep1_candidate_pairs": r8_replays["prep1"][
                    "candidate_pairs"],
                "r8_applied_candidate_pairs": r8_replays["applied"][
                    "candidate_pairs"],
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R7 两态均为 0；R8 "
                         "applied=1 对且恰为 matches、duplicate 为空，"
                         "prep1=0；全部复现）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R7T/R7B 与 R8T/R8B 来自不同 "
            "reader 实例、不同判读实例；R8 另有轮内读图方式差异=混杂"
            "因素，见 reader.reader_instance_note）；下列分组是通道级"
            "归因，不是旗级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r7_area_ratio_rejected_entries": geo_r7,
            "r8_area_ratio_rejected_entries": geo_r8,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r7_category_mismatch_entries": cat_r7,
            "r8_category_mismatch_entries": cat_r8,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r7_entries": view_r7,
            "r8_entries": view_r8,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮重放"
                     "均无视角门条目——R7 bottom 12/12 全弃权（无非弃权"
                     "样本）；R8 bottom 3 旗中 1 条非弃权（R8B-001 "
                     "placement_pattern_anomaly，框 [0.72,0.685,0.8,"
                     "0.75]），为 R6 后 bottom 首条非弃权旗，但其框与"
                     "全部同态 GT（13 条均 side=top）containment<0.5"
                     "（零几何近邻对），未及视角门——视角可比性检验在本"
                     "轮重新获得 bottom 非弃权样本但仍零几何近邻。"),
        },
        "r8_specific_observations": [
            "R8 top 非弃权 courtyard_crowding 旗 6 条（applied-top 4："
            "R8T-002/R8T-004/R8T-006/R8T-007；prep1-top 2：R8T-012/"
            "R8T-013），较 R7 top 非弃权 courtyard 1 条（R7T-003）显著"
            "增多——§5 courtyard 近邻判据（示例 b 贴靠/极近形态）下庭院类"
            "旗标激增带来 matches 机会：R8T-004↔GT-REVC-AP-8-R1Q2 成匹配"
            "（containment 0.838782、面积比 2.688288；R5 后首个 matches）；"
            "其余 courtyard 旗（R8T-002/R8T-006/"
            "R8T-007/R8T-012/R8T-013）与同态 GT containment<0.5（定位"
            "未及 GT 邻域）。偏差入账：派发词称 applied-top「5 条 "
            "courtyard+2 placement」，盘面实测=4 条 courtyard（R8T-002/"
            "004/006/007）+2 条 placement（R8T-005/009）+3 条 silk"
            "（R8T-001/003/008），以盘面为准。",
            "R8T-014 蛇形走线以「可能等长匹配」弃权（suspicious_reroute、"
            "abstain=true、框 [0.37,0.27,0.48,0.40]，reader 原文：「该"
            "形态可能为常规等长匹配设计而非缺陷绕行，无法负责任确认其为"
            "可疑改道，故弃权」）——reroute 类现象从 R7 的非弃权报告"
            "（R7T-002/R7T-004/R7T-009 共 3 条）转为存在性歧义弃权"
            "（三路出口第二路）；弃权不参与匹配。",
            "R8B-003 整板无丝印的元层弃权（silk_readability、abstain="
            "true、框 [0.07,0.06,0.94,0.94] 近乎全图）——「完全无丝印」"
            "的存在性（设计无丝印 vs 渲染未叠加丝印层）无法从单张合成图"
            "负责任确认（reader 原文明示）；弃权不参与匹配（该全图框不"
            "构成任何 GT 候选）；与假设 reject_condition 的解释方向一致"
            "（指向需渲染侧图层信息等更强证据通道）。",
            "prep1-bottom 旗标产量 6→1（R7 6 旗全弃权→R8 1 旗弃权）；"
            "bottom 合计旗标产量 12→3（R8=1 非弃权报告 R8B-001+2 弃权 "
            "R8B-002/R8B-003）——R7 bottom 占主导的沙漏/白色轮廓类"
            "（热释辐条形态）存在性歧义弃权，本轮经 §4 系统性重复启发"
            "化解为「正常设计特征→不报告」（三路出口第一路），该化解"
            "通道绕过旗标产量（详见 hypothesis_test.mechanism_observation）。",
        ],
    }


# ---------------------------------------------------------------------------
# 预注册假设 (i) 裁决（三分结构：字母裁决+机制观察+度量设计教训）
# ---------------------------------------------------------------------------

def build_hypothesis_test(run_r7: dict, agg: dict, prep: dict,
                          appl: dict, attribution: dict) -> dict:
    """假设 (i) 裁决节（预注册判据执行；三分结构，两分如实分离）。

    字母裁决（唯一正式裁决）=判据 r8-prep-record.json hypothesis_test
    原文：support=「bottom 层弃权率 <0.5 且 top 层守门通过」；reject=
    「bottom 层弃权率未回落至 <0.5」。实测 bottom 0.666667（2/3）≥0.5
    ⇒ (i) 不获支持。机制观察与度量设计教训单列、不凌驾、不改写字母
    裁决；聚合弃权率入线（0.222222<0.5，R5 后首次）如实记录于
    aggregate_context，亦不改变字母裁决。
    """
    prep_doc = _json_load(REL_PREP_R8)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    strat_r7 = _stratified_abstain(run_r7["states"])
    strat_r8 = _stratified_abstain({"prep1": prep, "applied": appl})
    bottom_r7 = strat_r7["bottom"]["rate"]
    bottom_r8 = strat_r8["bottom"]["rate"]
    threshold = 0.5
    below = bottom_r8 < threshold
    fell = bottom_r8 < bottom_r7
    geo_r8 = attribution["channel_1_geometry_gate"][
        "r8_area_ratio_rejected_entries"]
    geo_r7 = attribution["channel_1_geometry_gate"][
        "r7_area_ratio_rejected_entries"]
    guard_ok = len(geo_r8) == 0 and len(geo_r8) <= len(geo_r7)
    supported = below and guard_ok
    verdict = "supported" if supported else "not_supported"
    verdict_text = (
        "按预注册判据（r8-prep-record.json hypothesis_test 原文）=不获"
        "支持（字母口径，唯一正式裁决）：R8 盲读 bottom 视角层弃权率 "
        "0.666667（2/3）相对 R7 基线 1.0（12/12）有回落（0.666667<1.0）"
        "但未回落至预注册阈值 <0.5，reject_condition 命中（bottom 层"
        "弃权率未回落至 <0.5——存在性歧义非指引措辞可完全化解，指向需"
        "渲染侧图层信息等更强证据通道；本轮 R8B-003 整板无丝印元层弃权"
        "即其实例）。守门通道观察（top 层几何门面积比出局条目 0→0 无"
        "回升）通过，但主通道判据未过则无论守门如何均不获支持。字母"
        "裁决如实执行、结果无论方向均如实入账；机制观察与度量设计教训"
        "单列于后，不凌驾、不改写字母裁决。")
    mechanism_observation = {
        "role": ("机制观察（单列，不凌驾字母裁决；字母裁决=not_"
                 "supported 不因本观察改写）"),
        "bottom_flag_production": {
            "r7": 12, "r7_detail": "12/12 全弃权（applied-bottom 6+"
                                   "prep1-bottom 6）",
            "r8": 3, "r8_detail": "1 非弃权报告（R8B-001）+2 弃权"
                                  "（R8B-002/R8B-003）"},
        "observation": (
            "R7 bottom 占主导的沙漏/白色轮廓类（热释辐条形态）存在性"
            "歧义弃权，本轮经 §4 系统性重复启发被化解为「正常设计特征→"
            "不报告」（三路出口第一路；R8 applied-bottom reader 原文 "
            "reading_notes：「四周边缘阵列及右侧列中大量出现的 2/3/4 瓣"
            "白色轮廓（热释辐条形态）呈成体系重复且节距不变、铜环不相"
            "交，按 §4 存在性一般判据判为正常设计特征，不报告」；R8 "
            "prep1-bottom reader 原文：「周边双排圆形焊盘的 courtyard "
            "轮廓沿整环成体系、均匀地相邻接触/贴合……按『系统性重复="
            "正常设计特征』→不报告」）。该化解通道以「不进入 flags」为"
            "输出，绕过旗标产量——弃权率（分母=旗标条数）不测量化解行为"
            "本身：bottom 旗标产量 12→3，剩余 3 旗中 2 旗弃权（分母骤"
            "缩使 2/3=0.666667 仍≥0.5）。"),
        "conclusion": ("判据字母未达（bottom 0.666667≥0.5）≠ 启发无效；"
                       "机制上启发确实化解了目标歧义类（bottom 层旗标"
                       "产量骤降与化解相容）"),
        "confounder_note": (
            "跨轮 reader 实例不同+轮内读图方式差异（reader.reader_"
            "instance_note：三个实例经外部视觉分析工具读图）=混杂因素；"
            "每格 n=1 无统计效力；development 域方向性描述，不构成已证"
            "因果关系"),
    }
    metric_design_lesson = {
        "role": ("度量设计教训（如实，供未来预注册参考；本轮不追溯"
                 "适用）"),
        "lesson": (
            "预注册裁决判据应测量化解通道本身（如按现象类的化解计数、"
            "或以含被化解现象为分母的旗标产量率），而非仅旗标内弃权率："
            "三路出口第一路（判为正常设计特征→不报告）不产生任何旗标，"
            "旗标内弃权率对其不敏感——本轮实例：化解机制生效（bottom "
            "旗标产量 12→3）但剩余旗标内弃权率 2/3=0.666667 仍≥0.5，"
            "字母判据测不到化解。"),
        "status": ("协议侧候选变更：未来轮须预注册后采用，不得回溯改判"
                   "本轮（本轮字母裁决=not_supported 维持）"),
    }
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R8,
                                "sha256": _sha(REL_PREP_R8)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "test_design": ht["test_design"],
            "null_result_note": ht["null_result_note"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "measurement": {
            "bottom_abstain_rate_r7": bottom_r7,
            "bottom_r7_fraction": strat_r7["bottom"]["fraction"],
            "bottom_abstain_rate_r8": bottom_r8,
            "bottom_r8_fraction": strat_r8["bottom"]["fraction"],
            "preregistered_threshold": threshold,
            "bottom_below_threshold": below,
            "bottom_rate_fell": fell,
            "bottom_rate_delta": cal._round6(bottom_r8 - bottom_r7),
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "top 层非弃权旗标面积比出局条目 R7=0→R8=0（无回升）；"
                    "R8 top 13 条非弃权旗标与同态 GT 近邻对恰 2 个"
                    "（R8T-004↔GT-REVC-AP-8-R1Q2 候选成匹配 containment "
                    "0.838782 面积比 2.688288；R8T-010↔GT-REVC-P1-R4J3 "
                    "类别不符出局 containment 1.0 面积比 4.961299），均"
                    "满足面积比≤10——top 层守门通过（守门观察如实记录）"),
                "guard_ok": guard_ok,
                "note": ("守门通道观察不改变裁决：字母裁决由 bottom 层"
                         "弃权率主通道判据单独决定（reject_condition "
                         "命中，主通道未过则无论守门如何均不获支持）"),
            },
            "aggregate_context": {
                "abstain_rate_r7": run_r7["aggregation"][
                    "abstain_rate_total"],
                "abstain_rate_r8": agg["abstain_rate_total"],
                "note": ("聚合弃权率 0.6（15/25）→0.222222（4/18）<0.5"
                         "=R5 后首次满足 abstain_rate_le_0.5 暂行线"
                         "（APR-0011 单分项）；联合评价仍按 APR-0011 四项"
                         "如实执行（gt_recall 0.076923 与 seed_match_rate "
                         "0.071429 仍低于暂行线→joint=not_met）。聚合"
                         "入线如实记录，不改变字母裁决（字母判据=bottom "
                         "层弃权率，非聚合弃权率）"),
            },
        },
        "verdict": verdict,
        "verdict_rule": (
            "support=「R8 盲读 bottom 视角层弃权率相对 R7 基线（12/12="
            "1.0）显著回落——预注册阈值：bottom 层弃权率 <0.5——且 top "
            "层非弃权旗标仍守 §3 收窄判据（几何门面积比出局条目无回升）"
            "→获支持」；reject=「bottom 层弃权率未回落至 <0.5→不获"
            "支持」（r8-prep-record.json hypothesis_test 判据原文，轮后"
            "如实执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "mechanism_observation": mechanism_observation,
        "metric_design_lesson": metric_design_lesson,
        "stratified_observation": {
            "top": {"r7_rate": strat_r7["top"]["rate"],
                    "r7_fraction": strat_r7["top"]["fraction"],
                    "r8_rate": strat_r8["top"]["rate"],
                    "r8_fraction": strat_r8["top"]["fraction"],
                    "direction": "回落（top 层连续两轮低位；与假设方向"
                                 "相容）"},
            "bottom": {"r7_rate": strat_r7["bottom"]["rate"],
                       "r7_fraction": strat_r7["bottom"]["fraction"],
                       "r8_rate": strat_r8["bottom"]["rate"],
                       "r8_fraction": strat_r8["bottom"]["fraction"],
                       "direction": "回落但未达预注册阈值 <0.5（字母判据"
                                    "未过；主通道裁决由此决定）"},
            "confounder_note": (
                "跨轮 reader 实例不同=混杂因素；轮内读图方式差异（三个"
                "实例经外部视觉分析工具）=额外混杂因素；每格 n=1 无统计"
                "效力；development 域方向性描述"),
            "precedence_note": (
                "分层观察与机制观察均不得凌驾字母裁决；不构成已证因果"
                "关系"),
        },
    }


def build_run() -> dict:
    """run-r8 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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

    run_r7 = _json_load(REL_RUN_R7)
    attribution = build_channel_attribution(run_r7, prep, appl)
    agg = _aggregate(prep, appl)
    comp = _compliance(agg)
    hyp = build_hypothesis_test(run_r7, agg, prep, appl, attribution)

    prep_r8 = _json_load(REL_PREP_R8)
    serial = ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"]
    by_view = {"top": 0, "bottom": 0}
    abst_by_view = {"top": 0, "bottom": 0}
    for st in ("prep1", "applied"):
        blk = prep if st == "prep1" else appl
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for fid, view in blk["flag_views"].items():
            by_view[view] += 1
            if fid in abst:
                abst_by_view[view] += 1
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
        {"path_rel": REL_PREP_R8, "role": "r8_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R8)},
        {"path_rel": REL_GUIDANCE_R8,
         "role": "observation_guidance_r8_preregistration",
         "sha256": _sha(REL_GUIDANCE_R8)},
        {"path_rel": REL_GUIDANCE_R7, "role": "observation_guidance_r7_baseline",
         "sha256": _sha(REL_GUIDANCE_R7)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_PREP_R7, "role": "r7_prep_record_witness_source",
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
        "kind": "tl2_calibration_run_r8",
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
                "存在性判断一般判据增补（observation-guidance-r8.md §4，"
                "恰一项、单变量轮）：在 r7 §4 两条显式判据原文保留的前提"
                "下，为「弃权适用于」一条增补——（1）系统性重复 vs 孤立"
                "不一致启发（同类图形间规则成体系重复→更可能正常设计"
                "特征，通用 PCB 域知识内常规图形可能解释如散热辐条/热"
                "隔离盘形态、安装孔、基准点、极性标记类；孤立或不一致→"
                "更可能关注现象）；（2）三路出口显式化（判为正常设计特征"
                "→不报告；疑似但无法负责任确认→弃权路径；存在且可归类→"
                "正常报告路径）（措辞中性一般化，零具体板/位号/坐标/"
                "数量期望）",
            ],
            "unchanged_components": list(prep_r8["unchanged_components"]),
            "attribution_note": (
                "r8-prep-record.json attribution_plan：本轮恰一项变更、"
                "检验恰一个假设（r7 dev-record 预注册候选 (i)）——主通道="
                "bottom 视角层弃权率（相对 R7 基线 12/12=1.0；预注册阈值 "
                "<0.5；support=<0.5 且 top 层守门通过→获支持；reject=未"
                "回落至 <0.5→不获支持）；守门通道=top 层非弃权旗 "
                "frame_box_pct 几何门（面积比出局条目无回升，§3 收窄"
                "判据一字未动）。轮后按 bottom 层弃权率变化方向归因（见 "
                "run-r8 hypothesis_test 三分裁决节：字母裁决唯一正式、"
                "机制观察与度量设计教训单列不凌驾）；跨轮 flag_id 不构成"
                "同旗配对，归因是通道级不是旗级。渲染零变更下 R7→R8 任何 "
                "reader 表现变化首先归因于 §4 存在性判据增补与读者实例"
                "读图方式差异（reader_instance_note，如实入账），而非"
                "内容、图层或分辨率。"),
            "ref": {"path_rel": REL_PREP_R8, "sha256": _sha(REL_PREP_R8)},
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
        "gt_audit_reference": {
            "path_rel": REL_GT_AUDIT, "sha256": _sha(REL_GT_AUDIT),
            "note": ("同日只读 GT 源审计（gt-audit-r1，2026-09-07，"
                     "sha 1f20554a…）：bottom GT=无源已关闭、reroute GT="
                     "无源已关闭、L1NB 框径=合理维持现框——GT 侧三候选"
                     "全部关闭；该审计与本轮盲读并行落盘、非本轮预注册件"
                     "（deviations 在案），其结论维持本轮 GT 零改动；"
                     "round8-dev-record next_iteration_targets 引用其"
                     "结论"),
        },
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r7 相同）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r8 §4：r7 两条显式判据（弃权适用于存在/归类不确定；"
                    "弃权不适用于仅范围不确定）原文保留+存在性一般判据"
                    "（系统性重复 vs 孤立不一致启发）+三路出口显式化"
                    "（判为正常设计特征→不报告；疑似无法负责任确认→"
                    "弃权；存在且可归类→正常报告）；abstain=true=现象"
                    "是否存在或归属哪类无法负责任地判断；abstain 单列"
                    "不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("两波并行派发（与 R7 相同）：波 1="
                                      "applied-top 与 applied-bottom 并行；"
                                      "波 2=prep1-top 与 prep1-bottom 并行；"
                                      "视角内 applied→prep1 串行顺序保持；"
                                      "top/bottom 各一独立盲读；每图独立"
                                      "判读；视角内连续编号"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R8,
                                 "sha256": _sha(REL_GUIDANCE_R8),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R7,
                                     "sha256": _sha(REL_GUIDANCE_R7)},
                                 "change_note": GUIDANCE_CHANGE_NOTE},
            },
            "note": ("轮次预注册链：r8-prep-record.json 先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；渲染"
                     "复用见证=四 PNG 盘上实测 sha 与脚本常量逐一相等+"
                     "渲染输入侧冻结 PDF 复核一致；见证常量源=r7-prep-"
                     "record.json，在案）；observation-guidance-r8.md "
                     "落盘即冻结（恰一项预注册变更：§4 存在性判断一般"
                     "判据增补）；GT 重投影（derivation-log-r5.json，"
                     "13 条 frame_box_pct_r5）已在案沿用（渲染未变=零新"
                     "派生）；盲读后本包只做比对与记录（读者产物零改"
                     "动）。GT 冻结纪律：轮后未增删改；同日只读 GT 源"
                     "审计 gt-audit-r1.json 结论维持 GT 零改动（三候选"
                     "关闭，gt_audit_reference 在案）。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "r7_run": {"path_rel": REL_RUN_R7, "sha256": _sha(REL_RUN_R7)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）与 R7（§4 弃权"
                     "适用性再校准轮）run 在案；轮间对比见 round8-dev-"
                     "record.json 的方向性观察与 channel_attribution、"
                     "hypothesis_test（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器与通道重放为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-07-r8（事件序="
            "预注册冻结（prep-record+guidance-r8）→复用渲染见证→盲读→"
            "比对记录；同日并行=gt-audit-r1 只读 GT 源审计，"
            "gt_audit_reference 在案）"),
    }


DEV_OBSERVATIONS = [
    "R7→R8 旗标量对照：25→18（非弃权 10→14、弃权 15→4），聚合弃权率 "
    "0.6（15/25）→0.222222（4/18）——R5 后首次满足 APR-0011 "
    "abstain_rate_le_0.5 暂行线；分态弃权率 applied 0.538462（7/13）→"
    "0.090909（1/11）、prep1 0.666667（8/12）→0.428571（3/7）。零仪器"
    "变更（渲染逐字节复用，PNG 见证在案）下，该变化首先归因于 §4 存在"
    "性判断一般判据增补与读者实例读图方式差异（reader_instance_note："
    "三个实例经外部视觉分析工具读图，如实入账，混杂因素）。",
    "分视角弃权率（假设 (i) 检验的分层观察，如实附录）：top 0.230769"
    "（3/13）→0.133333（2/15）连续两轮回落；bottom 1.0（12/12）→"
    "0.666667（2/3）回落但未达预注册阈值 <0.5⇒假设 (i) 字母裁决="
    "not_supported（唯一正式裁决，r8-prep-record 判据原文执行）；机制"
    "观察单列（不凌驾）：bottom 旗标产量 12→3，R7 占主导的沙漏/白色"
    "轮廓类存在性歧义经系统性重复启发化解为「正常设计特征→不报告」"
    "（三路出口第一路），该化解通道绕过旗标产量、弃权率（分母=旗标"
    "数）不测量它——判据字母未达 ≠ 启发无效。",
    "matches 0→1：R8T-004↔GT-REVC-AP-8-R1Q2（containment 0.838782、"
    "面积比 2.688288）——R5 后首个 matches（R5 唯一命中=R5T-013↔"
    "GT-REVC-P1-L1NB）；gt_recall_total 0.0（0/13）→0.076923（1/13）、"
    "seed_match_rate_total 0.0（0/10）→0.071429（1/14，诊断口径，禁称 "
    "precision/FPR）。",
    "通道归因（vs R7，预注册重放方法）：几何门面积比出局 0→0（两轮均"
    "空）；类别门 0→1（R8T-010↔GT-REVC-P1-R4J3 containment 1.0、面积比"
    " 4.961299，silk_readability vs courtyard_crowding 类别不符出局——"
    "R8 首个近邻出局条目，R8T-010 为 silk 旗其框完全包含 R4J3 GT）；"
    "视角门 0→0（R8B-001 为 R6 后 bottom 首条非弃权旗，与全部同态 top "
    "GT containment<0.5，未及视角门）。",
    "R8 top 庭院类旗标激增：非弃权 courtyard_crowding 6 条（applied-top"
    " 4：R8T-002/004/006/007；prep1-top 2：R8T-012/013；R7 top 非弃权 "
    "courtyard 1 条=R7T-003）；其中 R8T-004 命中 AP-8，其余 courtyard "
    "旗与同态 GT containment<0.5（定位未及 GT 邻域，非阈值问题）。偏差"
    "入账：派发词称 applied-top「5 条 courtyard+2 placement」，盘面实测"
    "=4 条 courtyard+2 条 placement（R8T-005/009）+3 条 silk（R8T-001/"
    "003/008），以盘面为准。",
    "R8T-014 蛇形走线以「可能等长匹配」弃权（category="
    "suspicious_reroute、abstain=true；R7 的 reroute 非弃权行为 3 条"
    "本轮未再现，reroute 类现象以存在性歧义弃权表达）；R8B-003 整板无"
    "丝印的元层弃权（框 [0.07,0.06,0.94,0.94] 近乎全图，abstain 不参"
    "与匹配，不构成全图框候选；reader 原文无法区分设计无丝印 vs 渲染"
    "未叠加丝印层——指向渲染侧图层信息通道）。",
    "prep1-bottom 旗标产量 6→1（R7 6 旗全弃权→R8 1 旗弃权）；bottom "
    "合计 12→3（1 报告 R8B-001+2 弃权 R8B-002/R8B-003）——化解通道"
    "（正常设计特征→不报告）绕过旗标产量，见 run-r8 hypothesis_test."
    "mechanism_observation。",
    "跨轮 flag_id 不构成同旗配对（R7T/R7B 与 R8T/R8B 来自不同 reader "
    "实例；R8 另有轮内读图方式差异=混杂因素）；通道归因是通道级不是"
    "旗级（run-r8 channel_attribution.pairing_caveat）；重放与 "
    "compare_v3 对拍一致（R7 两态 matches∪duplicates 空、R8 applied "
    "1 对=matches、prep1 空）。",
]

DEV_NEXT_TARGETS = [
    "GT 侧三候选全部关闭（引用 gt-audit-r1.json，sha 1f20554a…，"
    "2026-09-07 只读 GT 源审计结论）：(a) bottom GT=无源已关闭——Rev-C "
    "判例域内零 bottom 侧真实判例（80 文件 DRC 族零 B 面条目；两态板 "
    "72/72 封装 F.Cu、B.Cu 走线段=0，bottom 面无缺陷几何载体），bottom "
    "GT 不建立、任何 bottom GT 条目都只能是无源标注；(b) reroute GT="
    "无源已关闭——仓库唯一布线台账=ASM-P1 刻意重布（批门 ACCEPT，语义"
    "与 suspicious_reroute 相反），不扩充布线类 GT（R8T-014 弃权旗保留"
    "为 reader 侧观察）；(c) L1NB 框径=合理维持现框（±1.0mm=全集统一"
    "预注册常量、w 膨胀比 1.273973=13 条最小、同框 R5T-013 containment "
    "1.0 命中在案）——GT 侧不再动，后续迭代回归指引侧/渲染侧。",
    "courtyard 密集旗的匹配表现追踪（指引侧观察候选）：R8 top 非弃权 "
    "courtyard 6 条中 1 条命中（R8T-004↔AP-8）；未命中 5 条（R8T-002/"
    "006/007/012/013）与同态 GT containment<0.5=定位未及 GT 邻域（非"
    "阈值问题）；后续轮继续追踪（GT/阈值零改动；不得为提高命中调"
    "阈值）。",
    "蛇形走线/等长匹配判据（指引侧候选）：R8T-014 以「可能等长匹配"
    "设计」弃权——suspicious_reroute 的存在性判据（等长匹配 vs 可疑"
    "绕行的形态区分）属 §4/§3A 指引侧候选变更（单变量纪律；reroute GT "
    "已关闭=不走 GT 扩充路径）；须先预注册再执行。",
    "度量设计教训（协议侧候选，本轮不追溯适用）：未来轮预注册裁决判据"
    "应测量化解通道本身（按现象类的化解计数/含被化解现象的旗标产量率），"
    "而非仅旗标内弃权率；须预注册后采用，不得回溯改判本轮（本轮字母"
    "裁决=not_supported 维持）。",
    "渲染侧 bottom 图层清单仍是候选（r6/r7/r8-prep-record 在案候选；"
    "R8B-003 整板无丝印元层弃权明示单张合成图无法确认丝印层缺失=渲染"
    "侧图层信息通道；bottom 面无封装/走线几何，gt-audit-r1 A1 在案）；"
    "属渲染侧变更，须预注册+声明零仪器变更纪律例外。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）；连续达标计数 0（R7 后）→0（本轮），正式采纳"
    "门槛未达成。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round8-dev-record 文档构建（T3；单向引用 run-r8 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round8_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域单变量指引侧变更轮（第八轮）：本轮零仪器变更"
            "——复用 R5 冻结渲染件（零重渲染，PNG 见证在案），唯一变更="
            "判读指引 §4 存在性判断一般判据增补（系统性重复 vs 孤立不"
            "一致启发+三路出口显式化，恰一项，预注册于盲读前）；检验 R7 "
            "预注册候选假设 (i)（判据=r8-prep-record.json "
            "hypothesis_test，轮后如实执行，三分结构：字母裁决唯一正式+"
            "机制观察单列+度量设计教训）；GT 集/协议与度量版本/比较器"
            "阈值与 R7 一致（GT 重投影沿用 derivation-log-r5——渲染未变="
            "零新派生；同日 gt-audit-r1 只读审计关闭 GT 侧三候选，GT 零"
            "改动维持）；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "run_record_ref": {"path_rel": REL_RUN_R8, "sha256": run_sha},
        "gt_audit_ref": run_doc["gt_audit_reference"],
        "flag_production": {
            "reader_id": "reader-r8-blind",
            "raw_files": run_doc["reader"]["raw_files"],
            "flag_count_by_file": {
                key: run_doc["reader"]["parse"][key]["flag_count"]
                for key in ("applied-top", "applied-bottom", "prep1-top",
                            "prep1-bottom")},
            "non_abstain_count": agg["scored_total"],
            "abstain_count": agg["abstain_count_total"],
            "abstain_rate": agg["abstain_rate_total"],
            "abstain_rate_by_view": agg["abstain_rate_by_view"],
            "parse_rejections": run_doc["parse_rejections"],
            "blind_discipline": DISPATCH_DISCIPLINE,
            "reader_instance_note": READER_INSTANCE_NOTE,
            "note": ("flag 全部通过 calibration fail-closed 校验（拒收"
                     "清单为空）；读者产物为冻结证据，本包零改动；派发"
                     "模式=两波并行（与 R7 相同）；读者实例读图方式差异"
                     "（三个实例经外部视觉分析工具读图）如实登记为混杂"
                     "因素，不作废"),
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
            "after_r7": {"consecutive_met_count": 0,
                         "note": "R7 联合评价 not_met（在案），连续达标"
                                 "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价 not_met（gt_recall "
                                   "0.076923 与 seed_match_rate 0.071429 "
                                   "未达暂行线；abstain_rate 0.222222≤0.5 "
                                   "为 R5 后首次满足该单分项，联合口径仍"
                                   "not_met）"},
            "consecutive_met_count_now": 0,
            "note": "连续达标计数变动：0（R7 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r7": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，零仪器变更、单变量指引侧变更轮：§4 "
            "存在性判断一般判据增补）18 旗标中 4 弃权、14 非弃权，"
            "matches=1（R8T-004↔GT-REVC-AP-8-R1Q2，R5 后首个）："
            "gt_recall=0.076923（1/13）、seed_match_rate=0.071429（1/14，"
            "诊断口径，禁称 precision/FPR）、abstain_rate=0.222222（4/18，"
            "R5 后首次≤0.5 暂行线），联合评价 not_met（gt_recall 与 "
            "seed_match_rate 两项未达 APR-0011 暂行线；诊断对照，非采纳"
            "门；连续达标计数 0→0）。预注册假设 (i) 裁决（按 r8-prep-"
            "record hypothesis_test 判据）=不获支持（字母口径，唯一正式"
            "裁决）：bottom 层弃权率 0.666667（2/3）未回落至 <0.5；机制"
            "观察单列（不凌驾）：bottom 旗标产量 12→3，沙漏/白色轮廓类"
            "存在性歧义经系统性重复启发化解为「正常设计特征→不报告」"
            "（三路出口第一路），该化解通道绕过旗标产量、弃权率不测量"
            "它——判据字母未达≠启发无效；度量设计教训如实入账（未来轮"
            "预注册须测量化解通道本身，不回溯改判本轮）。读者实例读图"
            "方式差异（三个实例经外部视觉分析工具读图）如实登记为混杂"
            "因素。GT 侧三候选经同日只读审计 gt-audit-r1 全部关闭（"
            "bottom GT/reroute GT/L1NB 框径），后续迭代回归指引侧/渲染"
            "侧。不做「能力已修复/已达成」类断言；in_calibrated_range "
            "恒 False。本批证据按协议 v1 §4 属 development 域，不得"
            "冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R7 对照基线=calibration-run-r7.json（62b34b71…，在案）；"
            "R6 对照基线=calibration-run-r6.json（6e6ffdf7…，在案）；"
            "轮间对比只做方向性描述。",
            "通道归因方法：照抄 run-r7 channel_attribution 的重放口径"
            "（deviation_note 承接），R7 与 R8 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r8 "
            "channel_attribution.method）。",
            "读者实例读图方式偏差如实记录：applied-bottom/prep1-top/"
            "prep1-bottom 三实例经外部视觉分析工具读图（analyze_image，"
            "图像经 CDN），与 R5–R7 及 R8 applied-top（本地逐区放大）"
            "不同=轮内与跨轮读者实例差异（混杂因素，如实入账，不作废）。",
            "假设裁决三分结构纪律：字母裁决=唯一正式裁决（预注册判据"
            "原文执行）；机制观察与度量设计教训单列，不得凌驾或改写字母"
            "裁决；本轮字母裁决=not_supported 维持不变。",
        ],
    }


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


def _assert_observation_numbers(run_doc: dict, run_r7: dict,
                                attribution: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    agg = run_doc["aggregation"]
    ab = agg["abstain_rate_total"]
    if f"{ab}" != "0.222222" or "0.222222（4/18）" not in obs:
        _fail("观察文本弃权率与实测不一致")
    if agg["abstain_count_total"] != 4 or agg["flag_count_total"] != 18:
        _fail("观察文本弃权记账与实测不一致")
    if agg["scored_total"] != 14 or agg["matches_total"] != 1 \
            or agg["gt_matched_total"] != 1:
        _fail("观察文本非弃权/匹配记账与实测不一致")
    if run_doc["hypothesis_test"]["verdict"] != "not_supported":
        _fail("假设 (i) 字母裁决与预期不符（预注册判据）")
    for need in ("0.6", "0.090909", "0.428571", "0.133333", "0.666667",
                 "0.838782", "2.688288", "4.961299", "0.076923",
                 "0.071429", "6→1", "12→3", "1/13", "1/14"):
        if need not in obs:
            _fail(f"观察文本缺实测数字 {need}")
    # 分视角记账与 run 落盘一致
    by_view = agg["abstain_rate_by_view"]
    if by_view["top"] != 0.133333 or by_view["bottom"] != 0.666667:
        _fail("分视角弃权率与观察文本不一致")
    # 通道条目数与文本一致（几何 R7 0→R8 0；类别 R7 0→R8 1）
    geo7 = attribution["channel_1_geometry_gate"][
        "r7_area_ratio_rejected_entries"]
    geo8 = attribution["channel_1_geometry_gate"][
        "r8_area_ratio_rejected_entries"]
    cat7 = attribution["channel_2_category_gate"]["r7_category_mismatch_entries"]
    cat8 = attribution["channel_2_category_gate"]["r8_category_mismatch_entries"]
    if not (len(geo7) == 0 and len(geo8) == 0
            and len(cat7) == 0 and len(cat8) == 1):
        _fail("通道条目数与观察文本声明不一致")
    if cat8[0]["flag_id"] != "R8T-010" \
            or cat8[0]["gt_id"] != "GT-REVC-P1-R4J3":
        _fail("类别门条目与观察文本声明不一致")
    # courtyard 激增声明与实测一致（R8 top 非弃权 courtyard=6；R7=1）
    r8_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_doc, "top")
                    if f["category"] == "courtyard_crowding"]
    r7_courtyard = [f["flag_id"] for f in
                    _non_abstain_flags_by_view(run_r7, "top")
                    if f["category"] == "courtyard_crowding"]
    if sorted(r8_courtyard) != ["R8T-002", "R8T-004", "R8T-006",
                                "R8T-007", "R8T-012", "R8T-013"] \
            or r7_courtyard != ["R7T-003"]:
        _fail("courtyard 旗计数与观察文本声明不一致")
    # matches 明细数值（R8T-004 vs AP-8）
    matches = run_doc["states"]["applied"]["compare_v3"]["matches"]
    if len(matches) != 1 or matches[0]["flag_id"] != "R8T-004" \
            or matches[0]["gt_id"] != "GT-REVC-AP-8-R1Q2" \
            or matches[0]["containment"] != 0.838782 \
            or matches[0]["area_ratio"] != 2.688288:
        _fail("applied 态 matches 明细与观察文本不一致")
    # R8T-010 vs R4J3 类别门数值
    blk = run_doc["states"]["prep1"]
    f010 = next(f for f in blk["reader_flags"] if f["flag_id"] == "R8T-010")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-P1-R4J3")
    if cal._round6(cal._containment(f010["frame_box_pct"],
                                    g["frame_box_pct"])) != 1.0 \
            or cal._round6(cal._area_ratio(f010["frame_box_pct"],
                                           g["frame_box_pct"])) != 4.961299:
        _fail("R8T-010 类别门数值与观察文本不一致")
    # 机制观察数字：bottom 旗标产量 12→3、prep1-bottom 6→1
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    if mo["bottom_flag_production"]["r7"] != 12 \
            or mo["bottom_flag_production"]["r8"] != 3:
        _fail("机制观察 bottom 旗标产量与实测不一致")
    r7_bottom = [f for st in ("prep1", "applied")
                 for f in run_r7["states"][st]["reader_flags"]
                 if run_r7["states"][st]["flag_views"][f["flag_id"]]
                 == "bottom"]
    r8_bottom = [f for st in ("prep1", "applied")
                 for f in run_doc["states"][st]["reader_flags"]
                 if run_doc["states"][st]["flag_views"][f["flag_id"]]
                 == "bottom"]
    r8_non_abst_bottom = [f for f in r8_bottom if not f["abstain"]]
    if len(r7_bottom) != 12 or len(r8_bottom) != 3 \
            or len(r8_non_abst_bottom) != 1 \
            or r8_non_abst_bottom[0]["flag_id"] != "R8B-001":
        _fail("bottom 旗标产量实测与机制观察声明不一致")
    r7_p1b = [f for f in run_r7["states"]["prep1"]["reader_flags"]
              if run_r7["states"]["prep1"]["flag_views"][f["flag_id"]]
              == "bottom"]
    r8_p1b = [f for f in run_doc["states"]["prep1"]["reader_flags"]
              if run_doc["states"]["prep1"]["flag_views"][f["flag_id"]]
              == "bottom"]
    if len(r7_p1b) != 6 or len(r8_p1b) != 1:
        _fail("prep1-bottom 旗标产量 6→1 与实测不一致")


def main() -> None:
    # 输入先验锚（fail-closed）
    for rel, want in FROZEN_SHA256.items():
        p = _rel(rel)
        if not p.is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")
        got = _sha(rel)
        if got != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {got[:8]}…≠{want[:8]}…")

    # 防覆写：目标两件必须尚不存在
    out_run = _rel(REL_RUN_R8)
    out_dev = _rel(REL_DEV_RECORD)
    for t in (out_run, out_dev):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r8")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R7), run["channel_attribution"])

    # 落盘 run → 实测 sha → 构建 dev record（单向引用）
    out_run.write_bytes(run_bytes)
    if out_run.read_bytes() != run_bytes:
        _fail("回读不一致: calibration-run-r8.json")
    run_sha = _sha(REL_RUN_R8)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round8-dev-record")
    out_dev.write_bytes(dev_bytes)
    if out_dev.read_bytes() != dev_bytes:
        _fail("回读不一致: round8-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    hyp = run["hypothesis_test"]
    print(f"[s39-cal-r8] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s39-cal-r8] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s39-cal-r8] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    bv = agg["abstain_rate_by_view"]
    print(f"[s39-cal-r8] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']} "
          f"(top {bv['top']} / bottom {bv['bottom']})")
    print(f"[s39-cal-r8] hypothesis (i): {hyp['hypothesis_id']} -> "
          f"{hyp['verdict']}（字母裁决；机制观察与度量设计教训单列）")
    print(f"[s39-cal-r8] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s39-cal-r8] channel_attribution: "
          f"geo R7={len(ca['channel_1_geometry_gate']['r7_area_ratio_rejected_entries'])}"
          f"→R8={len(ca['channel_1_geometry_gate']['r8_area_ratio_rejected_entries'])}, "
          f"cat R7={len(ca['channel_2_category_gate']['r7_category_mismatch_entries'])}"
          f"→R8={len(ca['channel_2_category_gate']['r8_category_mismatch_entries'])}")
    for rel in (REL_RUN_R8, REL_DEV_RECORD):
        print(f"[s39-cal-r8] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s39-cal-r8] R8 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
