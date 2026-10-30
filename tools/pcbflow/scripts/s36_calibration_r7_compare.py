#!/usr/bin/env python
"""CAL-R7-CLOSE：reader 判读迭代第七轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s34_calibration_r6_compare.py 同构，仅输入与轮次
常量不同；R7=development 域单变量指引侧变更轮（§4 弃权适用性再
校准），零仪器变更，复用 R5 冻结渲染，检验 R6 预注册假设 (a)）：

  T1  解析 4 个 reader-raw-r7-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate + 分视角（top/
      bottom）分层弃权记账 + 逐旗失败通道归因（vs R6，照 s34 重放
      方法）：applied 态=applied-top+applied-bottom 旗标 vs
      ground-truth-v2 九条（GT 重投影继续用 derivation-log-r5 的
      frame_box_pct_r5——渲染未变=重投影输入未变，board_box_mm/
      side 等其余字段与 GT 文件逐字段原样）；prep1 态=prep1-top+
      prep1-bottom 旗标 vs ground-truth-v1 四条（同重投影规则）。
      达标线=APR-0011 暂时采纳基线，逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      预注册假设 (a) 裁决节：判据=r7-prep-record.json hypothesis_test
      原文（support=弃权率显著回落且非弃权框守 §3 收窄判据；reject=
      弃权率不降→不获支持），聚合裁决按判据如实执行，分视角分层
      观察如实附录（不凌驾聚合裁决）。
      → calibration-run-r7.json。
  T3  development 域记录（本轮性质=单变量指引侧变更轮：零仪器变更、
      复用 R5 冻结渲染；R6→R7 方向性对照与匹配位置对照（只描述不下
      能力断言）/假设 (a) 裁决/下一迭代目标；引用 run-r7 落盘 sha
      单向引用）→ round7-dev-record.json。

通道归因纪律（vs R6；方法照抄 s34 deviation_note 口径）：run-r6 已有
channel_attribution 先例；本轮对 R6 与 R7 均以内嵌输入（reader_flags/
gt_entries/flag_views，run sha 在案）+ compare_v3 同源几何原语
（calibration._containment/_area_ratio/CONTAINMENT_MIN=0.5/
AREA_RATIO_MAX=10.0）确定性重放通道分类，并与各态 compare_v3 的
matches∪duplicate_reports 对拍复核。跨轮 flag_id 不构成同旗配对
（不同 reader 实例），归因是通道级不是旗级。

纪律：out/ 既有文件零改动（防覆写 guard；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r7）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s36_calibration_r7_compare.py   （仓库根执行）
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

DECLARED_DATE = "2026-09-06"
ROUND_ID = "2026-09-06-r7"
ROUND_LABEL = "r7"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R6 = "out/v3-tl2/calibration/observation-guidance-r6.md"
REL_GUIDANCE_R7 = "out/v3-tl2/calibration/observation-guidance-r7.md"
REL_PREP_R6 = "out/v3-tl2/calibration/r6-prep-record.json"
REL_PREP_R7 = "out/v3-tl2/calibration/r7-prep-record.json"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_RUN_R6 = "out/v3-tl2/calibration/calibration-run-r6.json"
REL_RUN_R7 = "out/v3-tl2/calibration/calibration-run-r7.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round7-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r7-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r7-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r7-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r7-prep1-bottom.txt",
}
#: R7 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 r7-prep-record（源自 r6-prep-record）脚本
#: 常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R7 复核见证=r7-prep-record
#: frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r7-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r7-prep-record.json frozen_input_pdfs_check 实测值。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R6:
        "1accadbdb42946c9673b2ce786495df46829b335f43a42dc8d977dca27233bf0",
    REL_GUIDANCE_R7:
        "9e7a7b1322af1279c6c2cc12c248ed8157628c402834a71329256fc8ce04179d",
    REL_PREP_R6:
        "af85c93382e950370dff5aa41c1fb111562bd006621ca07580c0e50a266a3b67",
    REL_PREP_R7:
        "e48c37fee217f3745662875640c3bef4dea27906d76ee07f85ed981815a7b3f2",
    REL_DERIV_R5:
        "623433801e8953587b60baff7827b859887ae218fad8100fb038382afa5b8663",
    REL_GT_V1:
        "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_GT_V2:
        "e1cb63d5e05761feada0b2dd030018bc04c3d3d165f33adcda2b9b348bd4b3a9",
    REL_RUN_R3:
        "0b09012e01b2d9fbd0cf6afb0d71191c657746b078a0debb0703ed999af734cd",
    REL_RUN_R4:
        "0cf8bb3127f3d6b4cde2bd34abd5e9474294c14987116371d031d66da6dc8490",
    REL_RUN_R5:
        "2ed5a12867c203b6dce044944139fa255b0ebc86dac60719a50c7dd175ece0d6",
    REL_RUN_R6:
        "6e6ffdf77eacf92f9386e0ff8a281fe155fee9c5be5f487d83b0b96544f98251",
    RAW_FILES["applied-top"]:
        "96a906a643b7984631c69d1295c318df2ef5c61f78c9017a00208108865ab241",
    RAW_FILES["applied-bottom"]:
        "fa23aa5180fef8c12c7dc9a4a2d1a99fb9b3f19903801958e71ffede7de849d6",
    RAW_FILES["prep1-top"]:
        "e616444993ed7843464759decfdd2aafa736825b4ab680b3dd4ecdd7cf0400ff",
    RAW_FILES["prep1-bottom"]:
        "bb54cefed977c94ecf765ca2173ee0a2a1ec538e1f2c52dd3989a3f4b835237f",
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
    "两波并行派发（与 R6 全串行不同，如实记录）：波 1=applied-top 与 "
    "applied-bottom 并行（两视角编号独立）；波 2=prep1-top 与 "
    "prep1-bottom 并行；视角内 applied→prep1 串行顺序保持（top "
    "R7T-001..013：applied 001..007→prep1 008..013；bottom "
    "R7B-001..012：applied 001..006→prep1 007..012）；盲读派发词只含"
    "图像绝对路径+observation-guidance-r7.md 路径+视角前缀+起始序号；"
    "无任何 GT 坐标/类别提示/期望缺陷描述；读图者不接触 GT/派生台账/"
    "任何校准产物路径")

#: 派发模式结构化记录（R7 特有；R6=四图全串行，如实对照）。
PARALLEL_DISPATCH = {
    "mode": "two_wave_parallel",
    "wave_1_parallel": ["applied-top", "applied-bottom"],
    "wave_2_parallel": ["prep1-top", "prep1-bottom"],
    "within_view_serial_order": {"top": ["applied-top", "prep1-top"],
                                 "bottom": ["applied-bottom",
                                            "prep1-bottom"]},
    "flag_id_continuity": {"top": "R7T-001..013（applied 001..007→"
                                  "prep1 008..013）",
                           "bottom": "R7B-001..012（applied 001..006→"
                                     "prep1 007..012）"},
    "diff_note": ("R6=四图独立全串行派发（run-r6 reader.serial_dispatch "
                  "在案）；R7=两波并行、视角内 applied→prep1 串行顺序"
                  "保持；派发模式差异如实入账（流程差异观察，"
                  "development 域只描述不断言）"),
}

GUIDANCE_CHANGE_NOTE = (
    "本轮唯一变更=判读指引 §4 弃权适用性再校准（单变量轮）：把 r6 §4"
    "「宁可 abstain 不硬标：仅模糊怀疑、无法负责任地定位或定类时……」"
    "一条拆分为两类不确定性的显式判据（总原则保留）——（1）弃权适用于："
    "现象是否存在或归属哪类无法负责任地判断；（2）弃权不适用于：现象"
    "可见且已可归类、仅精确范围/边界/尺寸难以确定，此时正常报告并按 "
    "§3 邻域判据给框（措辞中性，零类别/位置/数量暗示）；其基线="
    "observation-guidance-r6.md，r7-prep-record baseline 锚 1accadbd…；"
    "机械替换仅视角前缀 R6T/R6B→R7T/R7B 与 round_id_constant 两处")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 7 轮迭代"
    "（development 域单变量指引侧变更迭代轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = (
    "零仪器变更（单变量指引侧变更轮：§4 弃权适用性再校准；复用 R5 "
    "冻结渲染）")


def _fail(msg: str) -> None:
    print(f"[s36-cal-r7] FAIL: {msg}")
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

    R7 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                    "note": ("R7 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮唯一变更=判读指引 §4 "
                             "弃权适用性再校准，单变量轮）")},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R5, "sha256": _sha(REL_DERIV_R5),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取该台账"
                     " frame_box_pct_r5（R5 仪器像素界重投影；本轮渲染"
                     "未变故零新派生、沿用之）；board_box_mm/side 等其余"
                     "字段与 GT 文件逐字段原样；13 条全部 side=top")},
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
            f"{a['reader_flag_count']}) = {n_ab}/{n_fl}",
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
            f"{by_view['bottom']['fraction']} = {by_view['bottom']['rate']}"
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
                       "r7": f"{ 'met' if all_met else 'not_met' }（本轮）"},
            "note": "本轮联合评价未达标，连续计数仍为 0" if not all_met
                    else "本轮联合评价达标，连续计数=1（development 域，"
                         "不计入正式采纳）",
        },
        "critic_calibration_in_range": False,
        "critic_calibration_in_range_note": (
            "轮后实测值如实记录；谓词语义不变（正式采纳须人工批准），"
            "自动分流恒 blocked（BL-4+TD5 合取约束，达标≠自动分流）；"
            "正式采纳前 in_calibrated_range 恒 False"),
    }


# ---------------------------------------------------------------------------
# 逐旗失败通道归因（vs R6；方法照抄 s34：通道级，非旗级）
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


def build_channel_attribution(run_r6: dict, prep: dict, appl: dict) -> dict:
    """通道归因小节（vs R6；通道级分组，非旗级配对）。"""
    gt_by_state = {"prep1": prep["gt_entries"], "applied": appl["gt_entries"]}
    r6_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r6["states"][st]
        r6_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r6_replays[st], blk["compare_v3"]):
            _fail(f"R6 {st} 态通道重放与 compare_v3 对拍不一致")
    r7_replays = {}
    for st, blk in (("prep1", prep), ("applied", appl)):
        r7_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r7_replays[st], blk["compare_v3"]):
            _fail(f"R7 {st} 态通道重放与 compare_v3 对拍不一致")

    def pick(replays, failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r6 = pick(r6_replays, "area_ratio_rejected")
    geo_r7 = pick(r7_replays, "area_ratio_rejected")
    cat_r6 = pick(r6_replays, "category_mismatch")
    cat_r7 = pick(r7_replays, "category_mismatch")
    view_r6 = pick(r6_replays, "view_gate")
    view_r7 = pick(r7_replays, "view_gate")

    def _ids(rows):
        return [f"{r['flag_id']}↔{r['gt_id']}" for r in rows]

    geo_change = (
        "几何门通道（R6→R7）：面积比出局条目 1→0（R6="
        f"{_ids(geo_r6)}，面积比 12.706428；R7=空）。R7 全部 10 条非弃权"
        "旗标与同态 GT 的最大 containment<0.5（重放零近邻对），连几何门"
        "都未触及——非弃权框未出现面积比出局，与 §3 收窄判据未放宽方向"
        "相容（通道级描述，非同旗配对）；但 R7 全局匹配 0→0 持平，"
        "matches 连续两轮为空。")
    cat_change = (
        "类别门通道（R6→R7）：类别不符出局条目 1→0（R6="
        f"{_ids(cat_r6)}，containment 0.882169；R7=空）——R7 非弃权旗标"
        "无任何 containment≥0.5 的 GT 近邻对，类别门未在几何重叠处生效"
        "（R6 该门在 0.882169 高重叠处生效）；matches 0→0 持平；样本量"
        "极小，只描述不断言。")
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R7, "sha256": _sha(REL_PREP_R7)},
            "declaration": (
                "本轮恰一项变更、检验恰一个假设（r6 预注册候选 (a)）；"
                "轮后按弃权率变化方向归因（r7-prep-record.json "
                "attribution_plan.declaration 原文）"),
            "primary_channel": {
                "change_id": "abstain-applicability-recalibration",
                "metric": "弃权率（abstain 旗占比，相对 r6）",
            },
            "guard_channel": {
                "metric": "非弃权旗 frame_box_pct 几何门（containment / "
                          "area_ratio）",
                "requirement": "§3 收窄判据一字未动，非弃权框仍须满足",
            },
        },
        "method": {
            "source_of_r6_detail": (
                "calibration-run-r6.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "方法照抄 s34 deviation_note 口径：run-r6 已有 "
                "channel_attribution 先例（其登记的 R5/R6 重放值在案），"
                "本轮对 R6 与 R7 均以内嵌输入+compare_v3 同源几何原语"
                "（calibration._containment/_area_ratio、CONTAINMENT_MIN="
                "0.5、AREA_RATIO_MAX=10.0 声明常量）对每非弃权旗标×同态 "
                "GT 确定性重放通道分类：containment<0.5 无条目；近邻且"
                "视角不符=view_gate；近邻且面积比>上限=area_ratio_"
                "rejected（几何门）；近邻且面积比≤上限且类别不符="
                "category_mismatch（类别门）；类别相符且双条件过="
                "candidate。"),
            "replay_cross_check": {
                "r6_prep1_candidate_pairs": r6_replays["prep1"][
                    "candidate_pairs"],
                "r6_applied_candidate_pairs": r6_replays["applied"][
                    "candidate_pairs"],
                "r7_prep1_candidate_pairs": r7_replays["prep1"][
                    "candidate_pairs"],
                "r7_applied_candidate_pairs": r7_replays["applied"][
                    "candidate_pairs"],
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R6 与 R7 两态 "
                         "matches 均为 0、duplicate 均为空，全部复现）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R6T/R6B 与 R7T/R7B 来自不同 "
            "reader 实例、不同判读实例）；下列分组是通道级归因，不是旗"
            "级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r6_area_ratio_rejected_entries": geo_r6,
            "r7_area_ratio_rejected_entries": geo_r7,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r6_category_mismatch_entries": cat_r6,
            "r7_category_mismatch_entries": cat_r7,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r6_entries": view_r6,
            "r7_entries": view_r7,
            "note": ("视角门（不入两预注册通道计数，如实单列）：两轮均无"
                     "条目——R7 bottom 12/12 旗标全部弃权（无一非弃权入"
                     "重放），bottom 全弃权使视角可比性检验在本轮失去非弃"
                     "权样本（如实记录）；R6 bottom 5 条非弃权旗标框与"
                     "全部 GT 几何 containment<0.5（compare_v3 "
                     "view_mismatch 如实记录类别相符的视角不符对，不入"
                     "重放条目）。"),
        },
        "r7_specific_observations": [
            "R7T-012（prep1 弃权，[0.665, 0.585, 0.76, 0.675]）再次落在 "
            "R6T-009（prep1 弃权，[0.65, 0.58, 0.76, 0.77]）同区域：对 "
            "GT-REVC-P1-L1NB（r5 重投影框）containment R6T-009=0.839393、"
            "R7T-012=0.415663——该 GT 邻域连续两轮以弃权表达（弃权旗不"
            "参与匹配，通道级描述非旗级配对）。",
            "R7 top 非弃权旗含 suspicious_reroute 3 条（R7T-002/R7T-004 "
            "applied、R7T-009 prep1）与 courtyard_crowding 非弃权 1 条"
            "（R7T-003）；R5/R6 非弃权旗类别分布从未出现 "
            "suspicious_reroute（R5=silk_readability+courtyard_crowding、"
            "R6=silk_readability+other_advisory+courtyard_crowding）——"
            "如实记录为指引侧行为变化观察（§4 弃权适用性显式分列后 "
            "reroute 类现象以非弃权报告；跨轮 reader 实例不同=混杂因素，"
            "不构成因果断言）。",
            "R7T-005（applied 弃权，[0.14, 0.33, 0.33, 0.42]）的疑似区域"
            "框对 GT-REVC-AP-2-Y1C35 containment=1.0、类别相符"
            "（courtyard_crowding）、面积比=3.537565——若非弃权即满足"
            "双条件候选；存在性不确定以弃权表达，抑制了一个本可成立的"
            "候选对（abstain 单列不参与匹配=度量语义如实执行；通道级"
            "实例，非旗级归因）。",
            "bottom 全弃权（12/12）：R7 bottom readers 把「疑似形态是"
            "真实缺陷还是正常焊盘特征（如热隔离盘）」判为存在性不确定→"
            "弃权（reader 原文「无法负责任地判定其为真实关注现象……还是"
            "正常系统性焊盘特征」）；§4 显式分列后 bottom 层全部走弃权"
            "适用侧，与假设 (a) 预期方向相反的层内观察（如实附录）。",
        ],
    }


# ---------------------------------------------------------------------------
# 预注册假设 (a) 裁决（判据=r7-prep-record.json hypothesis_test 原文）
# ---------------------------------------------------------------------------

def build_hypothesis_test(run_r6: dict, agg: dict, prep: dict,
                          appl: dict, attribution: dict) -> dict:
    """假设 (a) 裁决节（预注册判据执行；聚合裁决 + 分层观察如实附录）。

    support=「弃权率相对 r6 显著回落、且非弃权旗标框仍守 §3 收窄判据」；
    reject=「弃权率不降→不获支持」。聚合弃权率 0.529412（R6）→0.6
    （R7）未回落 ⇒ (a) 不获支持；分视角分层如实单列（top 回落、bottom
    全弃权反向），分层不得凌驾聚合裁决。
    """
    prep_doc = _json_load(REL_PREP_R7)
    ht = prep_doc["hypothesis_test"]
    plan = prep_doc["attribution_plan"]
    r6_rate = run_r6["aggregation"]["abstain_rate_total"]
    r7_rate = agg["abstain_rate_total"]
    fell = r7_rate < r6_rate
    strat_r6 = _stratified_abstain(run_r6["states"])
    strat_r7 = _stratified_abstain({"prep1": prep, "applied": appl})
    geo_r7 = attribution["channel_1_geometry_gate"][
        "r7_area_ratio_rejected_entries"]
    # 守门通道观察（不改变裁决：聚合裁决由弃权率主通道判据单独决定）
    guard_ok = len(geo_r7) == 0
    supported = fell and guard_ok
    verdict = "supported" if supported else "not_supported"
    verdict_text = (
        "聚合层面按预注册判据=(a) 不获支持：聚合弃权率 0.529412（9/17）"
        "→0.6（15/25）未回落，预注册 reject_condition 命中（弃权主导"
        "因素为「存在性不确定」而非「范围不确定」，本轮 §4 措辞再校准"
        "对该主导因素无效）。分层观察如实附录：top 层 0.7（7/10）→"
        "0.230769（3/13）大幅回落（方向与 (a) 相容）；bottom 层 0.285714"
        "（2/7）→1.0（12/12）全弃权（反向；R7 bottom readers 把「疑似"
        "形态是真实缺陷还是正常焊盘特征（如热隔离盘）」判为存在性不确定"
        "→弃权）。分层观察不得凌驾聚合裁决；跨轮 reader 实例不同=混杂"
        "因素、每格 n=1 无统计效力、development 域方向性描述，不得写成"
        "已证因果关系。")
    return {
        "kind": "preregistered_hypothesis_test",
        "hypothesis_id": ht["hypothesis_id"],
        "preregistration_ref": {"path_rel": REL_PREP_R7,
                                "sha256": _sha(REL_PREP_R7)},
        "preregistered_criteria_quote": {
            "hypothesis": ht["hypothesis"],
            "support_condition": ht["support_condition"],
            "reject_condition": ht["reject_condition"],
            "test_design": ht["test_design"],
            "null_result_note": ht["null_result_note"],
        },
        "primary_channel_metric": plan["primary_channel"]["metric"],
        "measurement": {
            "abstain_rate_r6": r6_rate,
            "abstain_r6_fraction": "9/17",
            "abstain_rate_r7": r7_rate,
            "abstain_r7_fraction": f"{agg['abstain_count_total']}/"
                                   f"{agg['flag_count_total']}",
            "abstain_rate_delta": cal._round6(r7_rate - r6_rate),
            "abstain_rate_fell": fell,
            "guard_channel": {
                "metric": plan["guard_channel"]["metric"],
                "requirement": plan["guard_channel"]["requirement"],
                "observation": (
                    "R7 非弃权旗标面积比出局条目 1→0（R6=1 条：R6T-007↔"
                    "GT-REVC-P1-L1SHORT 面积比 12.706428；R7=0 条）；R7 "
                    "全部 10 条非弃权框与同态 GT 无 containment≥0.5 近邻"
                    "对——未出现违反 §3 收窄判据的迹象（守门观察如实"
                    "记录）"),
                "guard_ok": guard_ok,
                "note": ("守门通道观察不改变裁决：聚合裁决由弃权率主通道"
                         "判据单独决定（reject_condition 命中，主通道未"
                         "过则无论守门如何均不获支持）"),
            },
        },
        "verdict": verdict,
        "verdict_rule": (
            "support=「弃权率相对 r6 显著回落且非弃权旗标框仍守 §3 收窄"
            "判据→获支持」；reject=「弃权率不降→不获支持」"
            "（r7-prep-record.json hypothesis_test 判据原文，轮后如实"
            "执行；结果无论方向均如实入账）"),
        "verdict_text": verdict_text,
        "stratified_observation": {
            "top": {"r6_rate": strat_r6["top"]["rate"],
                    "r6_fraction": strat_r6["top"]["fraction"],
                    "r7_rate": strat_r7["top"]["rate"],
                    "r7_fraction": strat_r7["top"]["fraction"],
                    "direction": "回落（与 (a) 方向相容）"},
            "bottom": {"r6_rate": strat_r6["bottom"]["rate"],
                       "r6_fraction": strat_r6["bottom"]["fraction"],
                       "r7_rate": strat_r7["bottom"]["rate"],
                       "r7_fraction": strat_r7["bottom"]["fraction"],
                       "direction": "升至全弃权（与 (a) 反向）"},
            "bottom_interpretation": (
                "R7 bottom readers 把「疑似形态是真实缺陷还是正常焊盘"
                "特征（如热隔离盘）」判为存在性不确定→弃权（reader 原文"
                "reading_notes：按指引 §4 弃权判据以低置信度弃权报告）"),
            "confounder_note": (
                "跨轮 reader 实例不同=混杂因素；每格 n=1 无统计效力；"
                "development 域方向性描述"),
            "precedence_note": (
                "分层观察不得凌驾聚合裁决；不构成已证因果关系"),
        },
    }


def build_run() -> dict:
    """run-r7 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
    attribution = build_channel_attribution(run_r6, prep, appl)
    agg = _aggregate(prep, appl)
    comp = _compliance(agg)
    hyp = build_hypothesis_test(run_r6, agg, prep, appl, attribution)

    prep_r7 = _json_load(REL_PREP_R7)
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
        {"path_rel": REL_PREP_R7, "role": "r7_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R7)},
        {"path_rel": REL_GUIDANCE_R7,
         "role": "observation_guidance_r7_preregistration",
         "sha256": _sha(REL_GUIDANCE_R7)},
        {"path_rel": REL_GUIDANCE_R6, "role": "observation_guidance_r6_baseline",
         "sha256": _sha(REL_GUIDANCE_R6)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": REL_PREP_R6, "role": "r6_prep_record_witness_source",
         "sha256": _sha(REL_PREP_R6)},
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
        "kind": "tl2_calibration_run_r7",
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
                "弃权适用性再校准（observation-guidance-r7.md §4，恰一项、"
                "单变量轮）：把 r6 §4「宁可 abstain 不硬标：仅模糊怀疑、"
                "无法负责任地定位或定类时……」拆分为两类不确定性的显式"
                "判据（总原则保留）——（1）弃权适用于：现象是否存在或"
                "归属哪类无法负责任地判断；（2）弃权不适用于：现象可见"
                "且已可归类、仅精确范围/边界/尺寸难以确定，此时正常报告"
                "并按 §3 邻域判据给框（措辞中性，零类别/位置/数量暗示）",
            ],
            "unchanged_components": list(prep_r7["unchanged_components"]),
            "attribution_note": (
                "r7-prep-record.json attribution_plan：本轮恰一项变更、"
                "检验恰一个假设（r6 预注册候选 (a)）——主通道=弃权率"
                "（abstain 旗占比，相对 r6；support=显著回落且非弃权框守 "
                "§3 收窄判据→(a) 获支持；reject=不降→不获支持）；守门"
                "通道=非弃权旗 frame_box_pct 几何门（containment/"
                "area_ratio，§3 收窄判据一字未动、不因本轮变更放松）。"
                "轮后按弃权率变化方向归因（见 run-r7 hypothesis_test "
                "裁决节）；跨轮 flag_id 不构成同旗配对，归因是通道级"
                "不是旗级。渲染零变更下 R6→R7 任何 reader 表现变化首先"
                "归因于 §4 措辞变更与派发模式差异（两波并行，如实入账），"
                "而非内容、图层或分辨率。"),
            "ref": {"path_rel": REL_PREP_R7, "sha256": _sha(REL_PREP_R7)},
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
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r6 相同）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": (
                    "r7 §4 显式分列：abstain=true=现象是否存在或归属哪类"
                    "无法负责任地判断（弃权适用侧）；现象可见且已可归类、"
                    "仅精确范围/边界/尺寸难以确定→正常报告（弃权不适用"
                    "侧，按 §3 邻域判据给框）；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("两波并行派发：波 1=applied-top 与 "
                                      "applied-bottom 并行；波 2=prep1-top "
                                      "与 prep1-bottom 并行；视角内 "
                                      "applied→prep1 串行顺序保持；"
                                      "top/bottom 各一独立盲读；每图"
                                      "独立判读；视角内连续编号"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R7,
                                 "sha256": _sha(REL_GUIDANCE_R7),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R6,
                                     "sha256": _sha(REL_GUIDANCE_R6)},
                                 "change_note": GUIDANCE_CHANGE_NOTE},
            },
            "note": ("轮次预注册链：r7-prep-record.json 先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；渲染"
                     "复用见证=四 PNG 盘上实测 sha 与脚本常量逐一相等+"
                     "渲染输入侧冻结 PDF 复核一致；见证常量源=r6-prep-"
                     "record.json，在案）；observation-guidance-r7.md "
                     "落盘即冻结（恰一项预注册变更：§4 弃权适用性再"
                     "校准）；GT 重投影（derivation-log-r5.json，13 条 "
                     "frame_box_pct_r5）已在案沿用（渲染未变=零新派生）；"
                     "盲读后本包只做比对与记录（读者产物零改动）。GT "
                     "冻结纪律：轮后未增删改。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "r6_run": {"path_rel": REL_RUN_R6, "sha256": _sha(REL_RUN_R6)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）与 R6（指引侧两变更轮）run 在案；轮间"
                     "对比见 round7-dev-record.json 的方向性观察与 "
                     "channel_attribution、hypothesis_test（development "
                     "域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器与通道重放为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-06-r7（事件序="
            "预注册冻结（prep-record+guidance-r7）→复用渲染见证→盲读→"
            "比对记录）"),
    }


DEV_OBSERVATIONS = [
    "R6→R7 旗标量对照：17→25（非弃权 8→10、弃权 9→15），聚合弃权率 "
    "0.529412（9/17）→0.6（15/25），继续高于 APR-0011 暂行线 0.5；"
    "分态弃权率 applied 0.6（6/10）→0.538462（7/13）、prep1 0.428571"
    "（3/7）→0.666667（8/12）。零仪器变更（渲染逐字节复用，PNG 见证"
    "在案）下，该变化首先归因于 §4 弃权适用性措辞变更与派发模式差异"
    "（R6 全串行→R7 两波并行，如实入账）。",
    "分视角弃权率（预注册假设 (a) 检验的分层观察，如实附录）：top "
    "0.7（7/10）→0.230769（3/13）大幅回落（与 (a) 方向相容）；bottom "
    "0.285714（2/7）→1.0（12/12）全弃权（反向）。跨轮 reader 实例不同="
    "混杂因素、每格 n=1 无统计效力；分层不得凌驾聚合裁决（聚合 0.6 未"
    "回落→(a) 不获支持）。",
    "matches 0→0 持平：gt_recall_total 0.0（0/13）两轮持平、"
    "seed_match_rate_total 0.0（0/8）→0.0（0/10，诊断口径）。R7 全部 "
    "10 条非弃权旗标与同态 GT 的最大 containment<0.5——通道重放零近邻"
    "对（几何门 0、类别门 0、视角门 0），R6 的两类近邻出局条目（几何 "
    "1：R6T-007↔GT-REVC-P1-L1SHORT 面积比 12.706428；类别 1：R6T-007↔"
    "GT-REVC-P1-L1NB containment 0.882169）在 R7 均未再现。",
    "R7T-012（prep1 弃权，[0.665, 0.585, 0.76, 0.675]）再次落在 R6T-009"
    "（prep1 弃权，[0.65, 0.58, 0.76, 0.77]）同区域：对 GT-REVC-P1-L1NB"
    "（r5 重投影框）containment R6T-009=0.839393、R7T-012=0.415663——"
    "该 GT 邻域连续两轮以弃权表达（弃权旗不参与匹配，通道级描述）。",
    "R7 top 非弃权旗含 suspicious_reroute 3 条（R7T-002/R7T-004/R7T-009）"
    "与 courtyard_crowding 1 条（R7T-003）；R5/R6 非弃权旗类别分布从未"
    "出现 suspicious_reroute——如实记录为指引侧行为变化观察（跨轮 "
    "reader 实例不同=混杂因素，不构成因果断言）。",
    "R7T-005（applied 弃权，[0.14, 0.33, 0.33, 0.42]）的疑似区域框对 "
    "GT-REVC-AP-2-Y1C35 containment=1.0、类别相符、面积比=3.537565——"
    "若非弃权即满足双条件候选；存在性不确定以弃权表达，抑制了一个本可"
    "成立的候选对（abstain 单列不参与匹配=度量语义如实执行；通道级"
    "实例）。",
    "bottom 全弃权（12/12）：R7 bottom readers 把「疑似形态是真实缺陷"
    "还是正常焊盘特征（如热隔离盘）」判为存在性不确定→弃权（reader "
    "原文「无法负责任地判定其为真实关注现象……还是正常系统性焊盘"
    "特征」）；§4 显式分列后 bottom 层全部走弃权适用侧，与假设 (a) "
    "预期方向相反的层内观察。",
    "跨轮 flag_id 不构成同旗配对（R6T/R6B 与 R7T/R7B 来自不同 reader "
    "实例）；通道归因是通道级不是旗级（run-r7 channel_attribution."
    "pairing_caveat）；重放与 compare_v3 对拍一致（R6 与 R7 两态 "
    "matches∪duplicates 均为空、重放 candidate 均为空，全部复现）。",
]

DEV_NEXT_TARGETS = [
    "假设 (a) 不获支持后的方向（预注册判据执行结果如实入账）：聚合弃权"
    "主导=存在性不确定，bottom 层最显著（12/12 全弃权）。候选方向（均"
    "须先预注册再执行，如实列出）：(i) 「真实缺陷 vs 正常焊盘特征（如"
    "热隔离盘/安装孔）」存在性判据的指引侧再校准（§4 措辞，单变量纪律；"
    "不得为过线放宽判据措辞）；(ii) bottom 侧 GT/判例是否建立属协议/GT "
    "侧候选变更（须预注册+人工批准，不在指引单变量轮内）；(iii) 为 "
    "bottom 单独定图层清单属渲染侧变更（r6/r7-prep-record 在案候选）。",
    "reroute 非弃权旗的几何近邻性观察：R7 首现 3 条 suspicious_reroute "
    "非弃权旗（R5/R6 从未），全部与同态 GT containment<0.5——GT 集无"
    "布线类判例，评估 GT 扩充（布线类判例）属 GT 侧候选变更（须预注册+"
    "人工批准；阈值 AREA_RATIO_MAX/CONTAINMENT_MIN 本身零改动）。",
    "L1NB 邻域连续两轮弃权（R6T-009 containment=0.839393、R7T-012 "
    "containment=0.415663）：候选方向=对该邻域现象的定位/存在性判据"
    "指引侧再校准，或 GT 侧框径复核（后者属 GT 侧候选变更，须预注册；"
    "不得为通过而调阈值）。",
    "top 层方向观察：top 弃权率 0.7→0.230769 大幅回落且 R7 top 非弃权"
    "框无面积比/类别出局条目（零近邻对）——分视角方向分裂（top 回落/"
    "bottom 反向）下，后续迭代若继续指引侧单变量轮，分层弃权记账已落盘"
    "（run-r7 aggregation.abstain_rate_by_view），评估口径可按层观察。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round7-dev-record 文档构建（T3；单向引用 run-r7 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round7_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域单变量指引侧变更轮（第七轮）：本轮零仪器变更"
            "——复用 R5 冻结渲染件（零重渲染，PNG 见证在案），唯一变更="
            "判读指引 §4 弃权适用性再校准（恰一项，预注册于盲读前）；"
            "检验 R6 预注册候选假设 (a)（判据=r7-prep-record.json "
            "hypothesis_test，轮后如实执行）；GT 集/协议与度量版本/比较器"
            "阈值与 R6 一致（GT 重投影沿用 derivation-log-r5——渲染未变="
            "零新派生）；按协议 v1 §4，迭代轮证据不冒充未见留出，"
            "in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "run_record_ref": {"path_rel": REL_RUN_R7, "sha256": run_sha},
        "flag_production": {
            "reader_id": "reader-r7-blind",
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
            "note": ("flag 全部通过 calibration fail-closed 校验（拒收"
                     "清单为空）；读者产物为冻结证据，本包零改动；派发"
                     "模式=两波并行（与 R6 全串行不同，如实入账）"),
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
        "hypothesis_test_a": run_doc["hypothesis_test"],
        "joint_evaluation_trend": {
            "after_r6": {"consecutive_met_count": 0,
                         "note": "R6 联合评价 not_met（在案），连续达标"
                                 "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价 not_met（gt_recall 与 "
                                   "seed_match_rate 未达暂行线且弃权率 "
                                   "0.6 继续高于 0.5）"},
            "consecutive_met_count_now": 0,
            "note": "连续达标计数变动：0（R6 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r6": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，零仪器变更、单变量指引侧变更轮）25 "
            "旗标中 15 弃权、10 非弃权，matches=0：gt_recall=0.0（0/13）、"
            "seed_match_rate=0.0（0/10，诊断口径，禁称 precision/FPR）、"
            "abstain_rate=0.6（15/25，较 R6 的 0.529412 未回落并高于 0.5 "
            "暂行线），联合评价 not_met（三项未达 APR-0011 暂行线；诊断"
            "对照，非采纳门）。预注册假设 (a) 裁决（按 r7-prep-record "
            "hypothesis_test 判据）=不获支持：聚合弃权率未回落；分层如实"
            "单列（top 0.7→0.230769 回落、bottom 0.285714→1.0 全弃权），"
            "跨轮 reader 实例不同=混杂因素、每格 n=1、不构成已证因果"
            "关系。通道归因（vs R6，预注册重放方法）：R6 两类近邻出局"
            "条目（几何 1、类别 1）在 R7 均未再现（全部非弃权旗标 "
            "containment<0.5，零近邻对）；R7T-012 与 R6T-009 同区域弃权"
            "（L1NB 邻域连续两轮以弃权表达）；R7 首现 suspicious_reroute "
            "非弃权旗 3 条（R5/R6 从未，行为变化观察）。不做「能力已"
            "修复/已达成」类断言；连续达标计数 0→0，正式采纳门槛未达成。"
            "本批证据按协议 v1 §4 属 development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R6 对照基线=calibration-run-r6.json（6e6ffdf7…，在案）；"
            "R5 对照基线=calibration-run-r5.json（2ed5a128…，在案）；"
            "轮间对比只做方向性描述。",
            "通道归因方法：照抄 run-r6 channel_attribution 的重放口径"
            "（deviation_note 承接），R6 与 R7 均以内嵌输入确定性重放并"
            "与 compare_v3 matches∪duplicates 对拍（run-r7 "
            "channel_attribution.method）。",
            "派发模式偏差如实记录：R6=四图全串行，R7=两波并行（视角内 "
            "applied→prep1 串行顺序保持）；跨轮派发模式不同本身构成流程"
            "差异观察（development 域只描述不断言）。",
        ],
    }


def _non_abstain_categories(run_doc: dict) -> set:
    cats = set()
    for st in ("prep1", "applied"):
        blk = run_doc["states"][st]
        abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
        for f in blk["reader_flags"]:
            if f["flag_id"] not in abst:
                cats.add(f["category"])
    return cats


def _assert_observation_numbers(run_doc: dict, run_r5: dict, run_r6: dict,
                                attribution: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    agg = run_doc["aggregation"]
    ab = agg["abstain_rate_total"]
    if f"{ab}" != "0.6" or "0.6（15/25）" not in obs:
        _fail("观察文本弃权率与实测不一致")
    if agg["abstain_count_total"] != 15 or agg["flag_count_total"] != 25:
        _fail("观察文本弃权记账与实测不一致")
    if run_doc["hypothesis_test"]["verdict"] != "not_supported":
        _fail("假设 (a) 聚合裁决与预期不符（预注册判据）")
    for need in ("0.529412", "0.230769", "3/13", "12/12", "7/10", "2/7",
                 "0.839393", "0.415663", "3.537565", "12.706428",
                 "0.882169", "0.538462", "0.666667"):
        if need not in obs:
            _fail(f"观察文本缺实测数字 {need}")
    # 分视角记账与 run 落盘一致
    by_view = agg["abstain_rate_by_view"]
    if by_view["top"] != 0.230769 or by_view["bottom"] != 1.0:
        _fail("分视角弃权率与观察文本不一致")
    # 通道条目数与文本一致（几何 R6 1→R7 0；类别 R6 1→R7 0）
    geo6 = attribution["channel_1_geometry_gate"][
        "r6_area_ratio_rejected_entries"]
    geo7 = attribution["channel_1_geometry_gate"][
        "r7_area_ratio_rejected_entries"]
    cat6 = attribution["channel_2_category_gate"]["r6_category_mismatch_entries"]
    cat7 = attribution["channel_2_category_gate"]["r7_category_mismatch_entries"]
    if not (len(geo6) == 1 and len(geo7) == 0
            and len(cat6) == 1 and len(cat7) == 0):
        _fail("通道条目数与观察文本声明不一致")
    # reroute 类行为变化声明与三轮实测一致
    if "suspicious_reroute" in _non_abstain_categories(run_r5) \
            or "suspicious_reroute" in _non_abstain_categories(run_r6):
        _fail("R5/R6 不应存在 suspicious_reroute 非弃权旗（观察文本声明）")
    r7_reroute = [f["flag_id"] for st in ("prep1", "applied")
                  for f in run_doc["states"][st]["reader_flags"]
                  if f["category"] == "suspicious_reroute"
                  and not f["abstain"]]
    if len(r7_reroute) != 3:
        _fail("R7 suspicious_reroute 非弃权旗数与观察文本不一致")
    # R7T-005 弃权框 vs AP-2 双条件数值（containment=1.0、ar=3.537565）
    blk = run_doc["states"]["applied"]
    f005 = next(f for f in blk["reader_flags"] if f["flag_id"] == "R7T-005")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-AP-2-Y1C35")
    if cal._round6(cal._containment(f005["frame_box_pct"],
                                    g["frame_box_pct"])) != 1.0 \
            or cal._round6(cal._area_ratio(f005["frame_box_pct"],
                                           g["frame_box_pct"])) != 3.537565:
        _fail("R7T-005 弃权框双条件数值与观察文本不一致")
    # R7T-012 / R6T-009 对 L1NB 的 containment 数值
    deriv = _json_load(REL_DERIV_R5)
    nb = {e["gt_id"]: e["frame_box_pct_r5"]
          for e in deriv["entries"]}["GT-REVC-P1-L1NB"]
    f012 = next(f for f in run_doc["states"]["prep1"]["reader_flags"]
                if f["flag_id"] == "R7T-012")
    f009 = next(f for f in run_r6["states"]["prep1"]["reader_flags"]
                if f["flag_id"] == "R6T-009")
    if cal._round6(cal._containment(f009["frame_box_pct"], nb)) != 0.839393 \
            or cal._round6(cal._containment(f012["frame_box_pct"],
                                            nb)) != 0.415663:
        _fail("L1NB 邻域 containment 数值与观察文本不一致")


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
    out_run = _rel(REL_RUN_R7)
    out_dev = _rel(REL_DEV_RECORD)
    for t in (out_run, out_dev):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r7")

    # 观察文本数字自检（落盘前）
    _assert_observation_numbers(
        run, _json_load(REL_RUN_R5), _json_load(REL_RUN_R6),
        run["channel_attribution"])

    # 落盘 run → 实测 sha → 构建 dev record（单向引用）
    out_run.write_bytes(run_bytes)
    if out_run.read_bytes() != run_bytes:
        _fail("回读不一致: calibration-run-r7.json")
    run_sha = _sha(REL_RUN_R7)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round7-dev-record")
    out_dev.write_bytes(dev_bytes)
    if out_dev.read_bytes() != dev_bytes:
        _fail("回读不一致: round7-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    hyp = run["hypothesis_test"]
    print(f"[s36-cal-r7] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s36-cal-r7] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s36-cal-r7] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    bv = agg["abstain_rate_by_view"]
    print(f"[s36-cal-r7] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']} "
          f"(top {bv['top']} / bottom {bv['bottom']})")
    print(f"[s36-cal-r7] hypothesis (a): {hyp['hypothesis_id']} -> "
          f"{hyp['verdict']}")
    print(f"[s36-cal-r7] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s36-cal-r7] channel_attribution: "
          f"geo R6={len(ca['channel_1_geometry_gate']['r6_area_ratio_rejected_entries'])}"
          f"→R7={len(ca['channel_1_geometry_gate']['r7_area_ratio_rejected_entries'])}, "
          f"cat R6={len(ca['channel_2_category_gate']['r6_category_mismatch_entries'])}"
          f"→R7={len(ca['channel_2_category_gate']['r7_category_mismatch_entries'])}")
    for rel in (REL_RUN_R7, REL_DEV_RECORD):
        print(f"[s36-cal-r7] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s36-cal-r7] R7 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
