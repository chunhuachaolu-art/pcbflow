#!/usr/bin/env python
"""CAL-R6-CLOSE：reader 判读迭代第六轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s31_calibration_r5_compare.py 同构，仅输入与轮次
常量不同；R6=development 域指引侧变更轮，零仪器变更）：

  T1  解析 4 个 reader-raw-r6-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate + 逐旗失败通道
      归因（预注册计划执行）：applied 态=applied-top+applied-bottom
      旗标 vs ground-truth-v2 九条（GT 重投影继续用 derivation-log-r5
      的 frame_box_pct_r5——渲染未变=重投影输入未变，board_box_mm/
      side 等其余字段与 GT 文件逐字段原样）；prep1 态=prep1-top+
      prep1-bottom 旗标 vs ground-truth-v1 四条（同重投影规则）。
      达标线=APR-0011 暂时采纳基线，逐项诊断对照（禁改阈值措辞；
      seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称 precision/FPR）。
      → calibration-run-r6.json。
  T3  development 域记录（本轮性质=指引侧变更轮：零仪器变更、复用
      R5 冻结渲染；R5→R6 方向性对照与匹配位置对照（只描述不下能力
      断言）/下一迭代目标；引用 run-r6 落盘 sha 单向引用）→
      round6-dev-record.json。

通道归因纪律（预注册于 r6-prep-record.json attribution_plan）：
  两项指引变更命中不同度量通道——变更 1（邻域框口径收紧）→
  frame_box_pct 几何门（containment/area_ratio）；变更 2（类别判据
  示例化）→ 类别匹配门。实测偏差声明：run-r5 的 compare_v3 输出无
  逐旗 near-miss 明细键（v3 语义仅 duplicate_reports，R5 两态均为
  空），故通道分类以 run-r5 内嵌 reader_flags/gt_entries/flag_views
  （sha 在案）+ compare_v3 同源几何原语（calibration._containment/
  _area_ratio/CONTAINMENT_MIN=0.5/AREA_RATIO_MAX=10.0）确定性重放
  计算，并与 run-r5/run-r6 的 compare_v3 matches 对拍复核。跨轮
  flag_id 不构成同旗配对（不同 reader 实例），归因是通道级不是旗级。

纪律：out/ 既有文件零改动（防覆写 guard；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r6）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s34_calibration_r6_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-06-r6"
ROUND_LABEL = "r6"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R4 = "out/v3-tl2/calibration/observation-guidance-r4.md"
REL_GUIDANCE_R6 = "out/v3-tl2/calibration/observation-guidance-r6.md"
REL_PREP_R6 = "out/v3-tl2/calibration/r6-prep-record.json"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_RUN_R6 = "out/v3-tl2/calibration/calibration-run-r6.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round6-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r6-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r6-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r6-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r6-prep1-bottom.txt",
}
#: R6 零渲染：图像来源=R5 冻结渲染件原样复用（零重渲染、零仪器变更；
#: 见证=四 PNG 盘上 sha 与 s33/r6-prep-record 脚本常量逐一相等）。
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 渲染的输入侧冻结矢量 PDF（R6 复核见证=r6-prep-record
#: frozen_input_pdfs_check，全部一致；此处再锚定一次）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚=r6-prep-record.json renders_reuse.png_witness 实测值；
#: 四 PDF 锚=r6-prep-record.json frozen_input_pdfs_check 实测值。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R4:
        "c0706d0f176529b14228e9be7f54bcb3e38229e80dda6f4849909e838e09d0d3",
    REL_GUIDANCE_R6:
        "1accadbdb42946c9673b2ce786495df46829b335f43a42dc8d977dca27233bf0",
    REL_PREP_R6:
        "af85c93382e950370dff5aa41c1fb111562bd006621ca07580c0e50a266a3b67",
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
    RAW_FILES["applied-top"]:
        "ece9759d9647d682143e28d10d52aabc05ed45a8b9c4c32622c3c86e0d169c1f",
    RAW_FILES["applied-bottom"]:
        "6ed9b5eb4c504ebbf65630db81e24c90e6907b5a1583df5e84904d4ba5c8f071",
    RAW_FILES["prep1-top"]:
        "5be414acf35c8efc620d1aede19121944b3e92f8cc9e28f5f9c148f0a442cb7c",
    RAW_FILES["prep1-bottom"]:
        "624c599a12f3ecdeb59b94b28b3bc0e207d3ac6e6a7d2383bb00126e80cd5c05",
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
    "四图独立串行派发（applied 先于 prep1；视角内连续编号 top "
    "R6T-001..010、bottom R6B-001..007）；盲读派发词只含图像绝对路径+"
    "observation-guidance-r6.md 路径+视角前缀+起始序号；无任何 GT 坐标/"
    "类别提示/期望缺陷描述；读图者不接触 GT/派生台账/任何校准产物路径")

GUIDANCE_CHANGE_NOTE = (
    "本轮唯一变更=判读指引文本：observation-guidance-r6.md（先于盲读"
    "落盘、落盘即冻结；两项预注册变更=邻域框口径收紧 §3 + 类别判据"
    "示例化 §3A；其基线=observation-guidance-r4.md，r6-prep-record "
    "baseline 锚 c0706d0f…；机械替换仅视角前缀 R4T/R4B→R6T/R6B 与 "
    "round_id_constant 两处）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 6 轮迭代"
    "（development 域指引侧变更迭代轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = "零仪器变更（指引侧变更轮：复用 R5 冻结渲染）"
INSTRUMENT_COMPONENTS = [
    "邻域框口径收紧（observation-guidance-r6.md §3）：frame_box_pct "
    "由 r4 的「框住现象区域即可」升级为收窄至可见现象本身的邻域"
    "（现象延展范围+最小必要余量），不得包入大片未受影响区域",
    "类别判据示例化（observation-guidance-r6.md §3A 新增节）：6 合法"
    "类别逐类 1-2 个中性视觉判据示例（示例=判据说明非期望清单；零"
    "坐标/零数量/零板面引用）",
]
INSTRUMENT_UNCHANGED = [
    "渲染：复用 R5 冻结渲染件（零仪器变更、零重渲染；四 PNG 盘上 sha "
    "与 r6-prep-record 见证逐一相等；渲染输入侧冻结 PDF 复核一致）",
    "角色与盲读纪律（r6 指引 §1）、类别枚举 6 类逐字（§2）、置信度与"
    "弃权规则（§4）、courtyard 中性说明（§5）、输出 schema（§6）、"
    "格式对齐提示（§7）",
    "bottom 视口径：沿用 r4 指引不改（为 bottom 单独定图层清单属渲染"
    "侧变更，R7 候选，不在本轮）",
    "GT 集、协议与度量版本（GT 重投影继续用 derivation-log-r5——渲染"
    "未变=重投影输入未变）",
    "比较器阈值（CONTAINMENT_MIN=0.5 / AREA_RATIO_MAX=10.0 声明常量"
    "零覆盖）",
]
INSTRUMENT_ATTRIBUTION = (
    "r6-prep-record.json attribution_plan：本轮两项变更命中不同度量"
    "通道——变更 1（邻域框口径收紧）→ frame_box_pct 几何门"
    "（containment/area_ratio）；变更 2（类别判据示例化）→ 类别匹配"
    "门。比较器逐旗输出含失败通道明细；轮后按 R5 失败通道分组归因"
    "（分组逻辑由编排侧在本 close 包执行，见 run-r6 "
    "channel_attribution；跨轮 flag_id 不构成同旗配对，归因是通道级"
    "不是旗级）。渲染零变更下 R5→R6 任何 reader 表现变化首先归因于"
    "两项指引变更，而非内容、图层或分辨率。")


def _fail(msg: str) -> None:
    print(f"[s34-cal-r6] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    return json.loads(_rel(rel).read_text(encoding="utf-8"))


def _write_canonical(path: Path, obj) -> bytes:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return data


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
    清单（{flag_id, error}；reader 原文不修改）。
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

    R6 沿用该重投影：渲染未变（复用 R5 冻结渲染件）⇒ 重投影输入
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
                    "note": ("R6 零渲染：复用 R5 冻结渲染件（framing-r5 "
                             "预注册件在案；本轮唯一变更=判读指引两项）")},
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


def _aggregate(prep: dict, appl: dict) -> dict:
    p, a = prep["compare_v3"], appl["compare_v3"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
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
                       "r5": "not_met（在案）",
                       "r6": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
# 逐旗失败通道归因（预注册计划执行；通道级，非旗级）
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


def build_channel_attribution(run_r5: dict, prep: dict, appl: dict) -> dict:
    """通道归因小节（预注册计划执行；通道级分组，非旗级配对）。"""
    gt_by_state = {"prep1": prep["gt_entries"], "applied": appl["gt_entries"]}
    r5_replays = {}
    for st in ("prep1", "applied"):
        blk = run_r5["states"][st]
        r5_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r5_replays[st],
                                    blk["compare_v3"]):
            _fail(f"R5 {st} 态通道重放与 compare_v3 对拍不一致")
    r6_replays = {}
    for st, blk in (("prep1", prep), ("applied", appl)):
        r6_replays[st] = channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        gt_by_state[st])
        if not replay_matches_agree(r6_replays[st], blk["compare_v3"]):
            _fail(f"R6 {st} 态通道重放与 compare_v3 对拍不一致")

    def pick(replays, failure):
        rows = []
        for st in ("prep1", "applied"):
            for e in replays[st]["entries"]:
                if e["failure"] == failure:
                    rows.append(_channel_entry(dict(e, state=st)))
        rows.sort(key=lambda x: (x["state"], x["flag_id"], x["gt_id"]))
        return rows

    geo_r5 = pick(r5_replays, "area_ratio_rejected")
    geo_r6 = pick(r6_replays, "area_ratio_rejected")
    cat_r5 = pick(r5_replays, "category_mismatch")
    cat_r6 = pick(r6_replays, "category_mismatch")
    view_r6 = pick(r6_replays, "view_gate")
    view_r5 = pick(r5_replays, "view_gate")

    def _ids(rows):
        return [f"{r['flag_id']}↔{r['gt_id']}" for r in rows]

    geo_change = (
        "几何门通道（R5→R6）：面积比出局条目 2→1"
        f"（R5={_ids(geo_r5)}；R6={_ids(geo_r6)}）；R5 唯一成匹配的"
        "读者框（R5T-013↔GT-REVC-P1-L1NB，area_ratio=6.739726）与 R6 "
        "同 GT 近邻对（R6T-007↔GT-REVC-P1-L1SHORT，area_ratio="
        "12.706428）相比，同类近邻对的读者框面积比由 21.535106 收窄至 "
        "12.706428（仍超 AREA_RATIO_MAX=10.0 一个数量级内未达）——与"
        "收窄判据方向相容（通道级描述，非同旗配对）；但 R6 全局匹配 "
        "1→0（R5 唯一匹配区域 L1NB 在 R6 无非弃权旗标候选覆盖，最接近"
        "的 R6T-009 为弃权旗），即框收窄未转化为匹配增量。")
    cat_change = (
        "类别门通道（R5→R6）：类别不符出局条目 1→1 持平"
        f"（R5={_ids(cat_r5)}；R6={_ids(cat_r6)}）；类别判据示例化后，"
        "类别门仍在几何高度重叠处生效且重叠度上升（containment "
        "0.510336→0.882169）——silk_readability 旗标与 courtyard GT 框"
        "的近邻判类分歧未消除；样本量极小，只描述不断言。")
    return {
        "plan": {
            "ref": {"path_rel": REL_PREP_R6, "sha256": _sha(REL_PREP_R6)},
            "declaration": (
                "两项变更命中不同度量通道；轮后按 R5 失败通道分组归因"
                "（r6-prep-record.json attribution_plan.declaration 原文）"),
            "channel_1": {"change_id": "neighborhood-frame-tightening",
                          "gate": "frame_box_pct 几何门（containment / "
                                  "area_ratio）",
                          "metrics": ["containment", "area_ratio"]},
            "channel_2": {"change_id": "category-criteria-exemplification",
                          "gate": "类别匹配门"},
        },
        "method": {
            "source_of_r5_detail": (
                "calibration-run-r5.json 内嵌 reader_flags/gt_entries/"
                "flag_views（run sha 在案）"),
            "deviation_note": (
                "实测偏差声明：run-r5 的 compare_v3 输出无逐旗 near-miss "
                "明细键（度量 v3 语义仅 duplicate_reports，R5 两态均为"
                "空；逐旗 ratio_rejected 明细属度量 v2 键），故通道分类"
                "以 compare_v3 同源几何原语（calibration._containment/"
                "_area_ratio、CONTAINMENT_MIN=0.5、AREA_RATIO_MAX=10.0"
                "声明常量）对每非弃权旗标×同态 GT 确定性重放："
                "containment<0.5 无条目；近邻且视角不符=view_gate；近邻"
                "且面积比>上限=area_ratio_rejected（几何门）；近邻且面积"
                "比≤上限且类别不符=category_mismatch（类别门）；类别"
                "相符且双条件过=candidate。"),
            "replay_cross_check": {
                "r5_prep1_candidate_pairs": r5_replays["prep1"][
                    "candidate_pairs"],
                "r5_applied_candidate_pairs": r5_replays["applied"][
                    "candidate_pairs"],
                "r6_prep1_candidate_pairs": r6_replays["prep1"][
                    "candidate_pairs"],
                "r6_applied_candidate_pairs": r6_replays["applied"][
                    "candidate_pairs"],
                "agree_with_compare_v3": True,
                "note": ("重放 candidate 对=该态 compare_v3 的 "
                         "matches∪duplicate_reports（R5 matches=1、R6 "
                         "matches=0 均复现；两轮 duplicate 均为空）"),
            },
        },
        "pairing_caveat": (
            "跨轮 flag_id 不构成同旗配对（R5T/R5B 与 R6T/R6B 来自不同 "
            "reader 实例、不同判读实例）；下列分组是通道级归因，不是旗"
            "级配对；development 域只描述不断言能力"),
        "channel_1_geometry_gate": {
            "r5_area_ratio_rejected_entries": geo_r5,
            "r6_area_ratio_rejected_entries": geo_r6,
            "change": geo_change,
        },
        "channel_2_category_gate": {
            "r5_category_mismatch_entries": cat_r5,
            "r6_category_mismatch_entries": cat_r6,
            "change": cat_change,
        },
        "view_gate_observations": {
            "r5_entries": view_r5,
            "r6_entries": view_r6,
            "note": ("视角门（不入两预注册通道计数，如实单列）：R6 bottom "
                     "非弃权旗标 5 条（R6B-001/003/004/005/006）全部不入"
                     "候选——GT 13 条全部 side=top 且 bottom 旗标框与全部 "
                     "GT 几何 containment<0.5（compare_v3 view_mismatch "
                     "如实记录类别相符的视角不符对）；R5 bottom 2 旗标全"
                     "弃权、无视角门条目。"),
        },
        "beyond_channels_observations": [
            "弃权率回升（超出两通道范围的联合观察）：0.421053（8/19）→"
            "0.529412（9/17），高于 APR-0011 暂行线 0.5（差距 0.029412）"
            "；零仪器变更（渲染逐字节复用）下首先归因于两项指引变更——"
            "候选解释假设（未验证）：收窄判据提高「负责任定位」责任门槛，"
            "边界性观察从硬标转向弃权（R6 reader 原文多处「当前分辨率下"
            "无法确认……故弃权」）。",
            "R5 唯一匹配（R5T-013↔GT-REVC-P1-L1NB）未复现：R6 对 L1NB "
            "邻域最接近的旗标是弃权旗 R6T-009（[0.65, 0.58, 0.76, 0.77]）；"
            "非弃权旗标 R6T-007（silk）几何近邻但类别不符（通道 2 条目）。"
            "同区域旗标表现由「非弃权+匹配」转为「弃权+类别不符旗」，"
            "通道级实例：几何判定不确定性以弃权形式表达。",
        ],
    }


def build_run() -> dict:
    """run-r6 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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

    run_r5 = _json_load(REL_RUN_R5)
    attribution = build_channel_attribution(run_r5, prep, appl)

    agg = _aggregate(prep, appl)
    comp = _compliance(agg)

    serial = ["applied-top", "applied-bottom", "prep1-top", "prep1-bottom"]
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
            "total": len(appl["reader_flags"]) + len(prep["reader_flags"]),
        },
        "location_evidence_note": (
            "location_evidence 保留于 raw 原文（hash 在案），不进度量"
            "五键投影（process-v1 §2 步骤3）"),
        "serial_dispatch": serial,
        "view_injection": {
            "rule": VIEW_INJECTION_RULE,
            "mapping": {k: {img["image"]: img["view"]
                            for img in parsed[k]["images"]} for k in serial},
        },
    }

    frozen_artifacts = [
        {"path_rel": REL_PROTOCOL, "role": "evaluation_protocol",
         "sha256": _sha(REL_PROTOCOL)},
        {"path_rel": REL_PREP_R6, "role": "r6_prep_record_preregistration",
         "sha256": _sha(REL_PREP_R6)},
        {"path_rel": REL_GUIDANCE_R6,
         "role": "observation_guidance_r6_preregistration",
         "sha256": _sha(REL_GUIDANCE_R6)},
        {"path_rel": REL_GUIDANCE_R4, "role": "observation_guidance_r4_baseline",
         "sha256": _sha(REL_GUIDANCE_R4)},
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_DERIV_R5, "role": "gt_reprojection_log_r5",
         "sha256": _sha(REL_DERIV_R5)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
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
        "kind": "tl2_calibration_run_r6",
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
            "components": list(INSTRUMENT_COMPONENTS),
            "unchanged_components": list(INSTRUMENT_UNCHANGED),
            "attribution_note": INSTRUMENT_ATTRIBUTION,
            "ref": {"path_rel": REL_PREP_R6, "sha256": _sha(REL_PREP_R6)},
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
        "channel_attribution": attribution,
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖（与 r5 相同）",
            },
            "frozen_artifacts": frozen_artifacts,
            "reader_protocol": {
                "keys": ("五键 flag_id/category/confidence/abstain/"
                         "frame_box_pct + location_evidence（度量仅取"
                         "五键投影）"),
                "abstain_semantics": ("true=仅模糊怀疑、无法负责任定位/"
                                      "定类；abstain 单列不参与匹配"),
                "confidence": "∈[0,1]",
                "category_set": "critic.FLAG_CATEGORIES（枚举零改动）",
                "output": "单个 JSON 对象 {reader_id, per_image:[{image, flags}], reading_notes}",
                "per_view_dispatch": ("四图独立串行派发（applied 先于 "
                                      "prep1）；top/bottom 各一独立盲读；"
                                      "每图独立判读；视角内连续编号"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R6,
                                 "sha256": _sha(REL_GUIDANCE_R6),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "baseline_ref": {
                                     "path_rel": REL_GUIDANCE_R4,
                                     "sha256": _sha(REL_GUIDANCE_R4)},
                                 "change_note": GUIDANCE_CHANGE_NOTE},
            },
            "note": ("轮次预注册链：r6-prep-record.json 先于本轮盲读落盘"
                     "（零 GT 暴露声明在案 no_visual_reading=true；渲染"
                     "复用见证=四 PNG 盘上实测 sha 与脚本常量逐一相等+"
                     "渲染输入侧冻结 PDF 复核一致）；observation-"
                     "guidance-r6.md 落盘即冻结（两项预注册变更：邻域框"
                     "口径收紧+类别判据示例化）；GT 重投影（derivation-"
                     "log-r5.json，13 条 frame_box_pct_r5）已在案沿用"
                     "（渲染未变=零新派生）；盲读后本包只做比对与记录"
                     "（读者产物零改动）。GT 冻结纪律：轮后未增删改。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "r5_run": {"path_rel": REL_RUN_R5, "sha256": _sha(REL_RUN_R5)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）与 R5（有效分辨率"
                     "单变量轮）run 在案；轮间对比见 round6-dev-record."
                     "json 的方向性观察与 channel_attribution"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器与通道重放为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-06-r6（事件序="
            "预注册冻结（prep-record+guidance-r6）→复用渲染见证→盲读→"
            "比对记录）"),
    }


DEV_OBSERVATIONS = [
    "R5→R6 旗标量对照：19→17（非弃权 11→8、弃权 8→9），弃权率 "
    "0.421053（8/19）→0.529412（9/17），回升并高于 APR-0011 暂行线 "
    "0.5（差距 0.029412）；分态弃权率 applied 0.6（6/10）、prep1 "
    "0.428571（3/7）。零仪器变更（渲染逐字节复用，PNG 见证在案）下，"
    "该变化首先归因于判读指引两项预注册变更（邻域框口径收紧+类别判据"
    "示例化）。",
    "R5 的唯一框级匹配（R5T-013↔GT-REVC-P1-L1NB，containment=1.0、"
    "面积比 6.739726）在本轮未复现：R6 对 L1NB 邻域最接近的旗标是"
    "弃权旗 R6T-009（[0.65, 0.58, 0.76, 0.77]）；非弃权旗标 R6T-007"
    "（silk_readability，[0.645, 0.585, 0.765, 0.77]）几何近邻（对 "
    "L1NB containment=0.882169）但类别不符。gt_recall_total "
    "0.076923（1/13）→0.0（0/13）、seed_match_rate_total 0.090909"
    "（1/11）→0.0（0/8，诊断口径）。",
    "类别门通道（预注册归因计划通道 2）：R5 类别不符出局条目 1 条"
    "（R5T-010 silk_readability vs GT-REVC-P1-R4J3 courtyard_crowding，"
    "containment=0.510336）；R6 类别不符出局条目 1 条（R6T-007 "
    "silk_readability vs GT-REVC-P1-L1NB courtyard_crowding，"
    "containment=0.882169）。条目数持平（1→1），但几何重叠度上升"
    "（0.510336→0.882169）——类别判据示例化后类别门仍在几何高度重叠"
    "处生效；样本量极小，只描述不断言。",
    "几何门通道（预注册归因计划通道 1）：R5 面积比出局条目 2 条"
    "（R5T-005 vs GT-REVC-AP-7-C31U4 面积比=11.927；R5T-013 对 "
    "GT-REVC-P1-L1SHORT 面积比=21.535106）；R6 面积比出局条目 1 条"
    "（R6T-007 对 GT-REVC-P1-L1SHORT 面积比=12.706428）。同 GT 近邻对"
    "的读者框面积比由 21.535106 收窄至 12.706428（仍超 AREA_RATIO_MAX="
    "10.0，未达上限内）——与邻域框收窄判据方向相容（通道级描述，非"
    "同旗配对）；但匹配数 1→0，收窄未转化为匹配增量。",
    "弃权语义实例：R6 reading_notes 多处「当前分辨率下无法确认……"
    "故弃权」（reader 原文）；R6T-009（prep1 弃权）位于 R5 唯一匹配"
    "区域（L1NB 邻域）——通道级实例：几何判定不确定性以弃权形式表达，"
    "而非硬标。候选解释假设（未验证）：收窄判据提高「负责任定位」"
    "责任门槛，边界性观察从硬标转向弃权。",
    "bottom 视新事实：R5 bottom 2 旗标全弃权；R6 bottom 7 旗标中 "
    "5 条非弃权（R6B-001 courtyard_crowding、R6B-003/004/005/006 "
    "other_advisory）——但 GT 13 条全部 side=top，bottom 非弃权旗标"
    "全部不入候选（类别相符对记 view_mismatch，且 bottom 旗标框与全部 "
    "GT 几何 containment<0.5）；bottom 弃权 2 条（R6B-002、R6B-007）。",
    "跨轮 flag_id 不构成同旗配对（R5T/R5B 与 R6T/R6B 来自不同 reader "
    "实例）；通道归因是通道级不是旗级（run-r6 channel_attribution."
    "pairing_caveat）；重放与 compare_v3 对拍一致（R5 matches=1、R6 "
    "matches=0 均复现）。",
]

DEV_NEXT_TARGETS = [
    "弃权率回升：0.529412（9/17）高于 APR-0011 暂行线 0.5，差距 "
    "0.029412。候选解释假设（如实、未验证）：(a) 邻域框收窄判据提高"
    "「负责任定位」责任门槛，边界性观察从硬标转向弃权（R6 reader 原文"
    "多处「无法确认……故弃权」）；(b) 类别判据示例化后类别归属不确定性"
    "显性化（R6T-009 在 L1NB 邻域弃权而 R5 同区域曾成匹配）。候选方向="
    "弃权判据与定位判据的指引措辞再校准（须先预注册再盲读；不得为过线"
    "而放宽判据措辞；阈值 AREA_RATIO_MAX/CONTAINMENT_MIN 本身零改动）。",
    "bottom 视信息量（延续 R5 目标）：R6 bottom 首次出现 5 条非弃权"
    "旗标但全部不可匹配（GT 全 top+视角门+几何不近邻）——为 bottom 视"
    "单独定图层清单属渲染侧变更（R7 候选，r6-prep-record 在案）；评估 "
    "bottom 侧 GT 是否建立属协议侧变更（须预注册+人工批准，不在本轮）。",
    "类别门：R6T-007（silk_readability）与 courtyard GT（L1NB）几何"
    "高度重叠（containment=0.882169）——延续 R5 目标：评估指引中类别"
    "判据（尤其 silk_readability 与 courtyard_crowding 在「文字压焊盘/"
    "轮廓近邻」混合现象下）是否需更细区分判据（同样须预注册；单变量"
    "纪律下逐项变更）。",
    "几何门：R6T-007 对 GT-REVC-P1-L1SHORT 面积比 12.706428 仍超上限 "
    "10.0——邻域框收窄已在 R6 生效（同 GT 近邻对面积比 21.535106→"
    "12.706428）但未达上限内；候选方向=指引侧进一步收窄小目标邻域框"
    "口径，或如实接受该类近邻小 GT 框几何不可达（后者属度量/GT 侧候选"
    "变更，须预注册；不得为通过而调阈值）。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance/prep-record）并声明 development 域；达标证据"
    "仍须留出集（未建立，TBD）；in_calibrated_range 恒 False 直到正式"
    "采纳（须人工批准）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round6-dev-record 文档构建（T3；单向引用 run-r6 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round6_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域指引侧变更轮（第六轮）：本轮零仪器变更——复用 "
            "R5 冻结渲染件（零重渲染，PNG 见证在案），唯一变更=判读指引"
            "两项（邻域框口径收紧+类别判据示例化，预注册于盲读前）；GT "
            "集/协议与度量版本/比较器阈值与 R5 一致（GT 重投影沿用 "
            "derivation-log-r5——渲染未变=零新派生）；按协议 v1 §4，"
            "迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "run_record_ref": {"path_rel": REL_RUN_R6, "sha256": run_sha},
        "flag_production": {
            "reader_id": "reader-r6-blind",
            "raw_files": run_doc["reader"]["raw_files"],
            "flag_count_by_file": {
                key: run_doc["reader"]["parse"][key]["flag_count"]
                for key in ("applied-top", "applied-bottom", "prep1-top",
                            "prep1-bottom")},
            "non_abstain_count": agg["scored_total"],
            "abstain_count": agg["abstain_count_total"],
            "abstain_rate": agg["abstain_rate_total"],
            "parse_rejections": run_doc["parse_rejections"],
            "blind_discipline": DISPATCH_DISCIPLINE,
            "note": ("flag 全部通过 calibration fail-closed 校验（拒收"
                     "清单为空）；读者产物为冻结证据，本包零改动"),
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
        "joint_evaluation_trend": {
            "after_r5": {"consecutive_met_count": 0,
                         "note": "R5 联合评价 not_met（在案），连续达标"
                                 "计数=0"},
            "this_round": {"joint_evaluation": comp["joint_evaluation"],
                           "note": "本轮联合评价 not_met（gt_recall 与 "
                                   "seed_match_rate 未达暂行线且弃权率"
                                   "回升超 0.5）"},
            "consecutive_met_count_now": 0,
            "note": "连续达标计数变动：0（R5 后）→0（本轮）；正式采纳"
                    "门槛（连续 2 轮达标+人工批准）未达成，不得写成"
                    "已达成",
        },
        "directional_observation_vs_r5": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，零仪器变更、指引侧变更轮）17 旗标"
            "中 9 弃权、8 非弃权，matches=0：gt_recall=0.0（0/13）、"
            "seed_match_rate=0.0（0/8，诊断口径，禁称 precision/FPR）、"
            "abstain_rate=0.529412（9/17，较 R5 的 0.421053 回升并高于 "
            "0.5 暂行线），联合评价 not_met（三项未达 APR-0011 暂行线；"
            "诊断对照，非采纳门）。R5 唯一框级匹配未复现；通道归因"
            "（预注册计划）：几何门面积比出局条目 2→1 且同 GT 近邻对"
            "面积比 21.535106→12.706428（与收窄判据方向相容），类别门"
            "出局条目 1→1 持平且几何重叠度 0.510336→0.882169 上升；"
            "均为通道级描述（跨轮 flag_id 不构成同旗配对）。候选解释"
            "假设（未验证）：收窄判据提高定位责任门槛→边界观察转弃权。"
            "不做「能力已修复/已达成」类断言；连续达标计数 0→0，正式"
            "采纳门槛未达成。本批证据按协议 v1 §4 属 development 域，"
            "不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R5 对照基线=calibration-run-r5.json（2ed5a128…，在案）；"
            "R4 对照基线=calibration-run-r4.json（0cf8bb31…，在案）；"
            "轮间对比只做方向性描述。",
            "通道归因方法偏差声明：run-r5 compare_v3 输出无逐旗 near-miss "
            "明细键（实测），通道分类以 run-r5 内嵌输入+同源几何原语重放"
            "并与 compare_v3 matches 对拍（run-r6 channel_attribution."
            "method.deviation_note）。",
        ],
    }


def _assert_observation_numbers(agg: dict, attribution: dict) -> None:
    """DEV_OBSERVATIONS 文本与重放实测数字一致性（fail-closed）。"""
    obs = "\n".join(DEV_OBSERVATIONS)
    ab = agg["abstain_rate_total"]
    if f"{ab}" != "0.529412" or "0.529412" not in obs:
        _fail("观察文本弃权率与实测不一致")
    if "9/17" not in obs or agg["abstain_count_total"] != 9 \
            or agg["flag_count_total"] != 17:
        _fail("观察文本弃权记账与实测不一致")
    for need in ("0.510336", "0.882169", "11.927", "21.535106",
                 "12.706428", "6.739726"):
        if need not in obs:
            _fail(f"观察文本缺重放数字 {need}")
    # 通道条目数与文本一致（几何 2→1、类别 1→1）
    geo5 = attribution["channel_1_geometry_gate"][
        "r5_area_ratio_rejected_entries"]
    geo6 = attribution["channel_1_geometry_gate"][
        "r6_area_ratio_rejected_entries"]
    cat5 = attribution["channel_2_category_gate"][
        "r5_category_mismatch_entries"]
    cat6 = attribution["channel_2_category_gate"][
        "r6_category_mismatch_entries"]
    if not (len(geo5) == 2 and len(geo6) == 1
            and len(cat5) == 1 and len(cat6) == 1):
        _fail("通道条目数与观察文本声明不一致")


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
    out_run = _rel(REL_RUN_R6)
    out_dev = _rel(REL_DEV_RECORD)
    for t in (out_run, out_dev):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r6")

    # 落盘 run → 实测 sha → 构建 dev record（单向引用）
    out_run.write_bytes(run_bytes)
    if out_run.read_bytes() != run_bytes:
        _fail("回读不一致: calibration-run-r6.json")
    run_sha = _sha(REL_RUN_R6)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round6-dev-record")
    out_dev.write_bytes(dev_bytes)
    if out_dev.read_bytes() != dev_bytes:
        _fail("回读不一致: round6-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    print(f"[s34-cal-r6] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s34-cal-r6] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s34-cal-r6] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    print(f"[s34-cal-r6] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']}")
    print(f"[s34-cal-r6] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    ca = run["channel_attribution"]
    print(f"[s34-cal-r6] channel_attribution: "
          f"geo R5={len(ca['channel_1_geometry_gate']['r5_area_ratio_rejected_entries'])}"
          f"→R6={len(ca['channel_1_geometry_gate']['r6_area_ratio_rejected_entries'])}, "
          f"cat R5={len(ca['channel_2_category_gate']['r5_category_mismatch_entries'])}"
          f"→R6={len(ca['channel_2_category_gate']['r6_category_mismatch_entries'])}")
    for rel in (REL_RUN_R6, REL_DEV_RECORD):
        print(f"[s34-cal-r6] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s34-cal-r6] R6 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
