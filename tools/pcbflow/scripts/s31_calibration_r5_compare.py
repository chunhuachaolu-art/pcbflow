#!/usr/bin/env python
"""CAL-R5-CLOSE：reader 判读迭代第五轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用；
结构与接线方式照 s30_calibration_r4_compare.py 同构，仅输入与轮次
常量不同）：

  T1  解析 4 个 reader-raw-r5-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate：
      applied 态=applied-top+applied-bottom 旗标 vs ground-truth-v2
      九条（frame_box_pct=derivation-log-r5 的 frame_box_pct_r5，
      board_box_mm/side 等其余字段与 GT 文件逐字段原样）；prep1 态=
      prep1-top+prep1-bottom 旗标 vs ground-truth-v1 四条（同重投影
      规则）。达标线=APR-0011 暂时采纳基线，逐项诊断对照（禁改阈值
      措辞；seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称
      precision/FPR）。→ calibration-run-r5.json。
  T3  development 域记录（本轮性质=单变量仪器迭代/有效分辨率；
      R4→R5 方向性对照与匹配位置对照（只描述不下能力断言）/下一
      迭代目标；引用 run-r5 落盘 sha 单向引用）→
      round5-dev-record.json。

纪律：out/ 既有文件零改动（防覆写 guard；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r5）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s31_calibration_r5_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-06-r5"
ROUND_LABEL = "r5"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R5 = "out/v3-tl2/calibration/render-framing-r5.json"
REL_GUIDANCE_R4 = "out/v3-tl2/calibration/observation-guidance-r4.md"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round5-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r5-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r5-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r5-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r5-prep1-bottom.txt",
}
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r5/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r5/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r5/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r5/prep1-bottom.png",
}
#: R5 唯一图像来源=R4 冻结矢量 PDF（framing-r5 frozen_inputs.r4_frozen_pdfs；
#: 本轮零 kicad-cli 调用，任意 DPI 重光栅化=确定性）。
PDF_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.pdf",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.pdf",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.pdf",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.pdf",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚与 derivation-log-r5.json renders_r5.images[].sha256 逐一相等。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R5:
        "860aa91068871fcd35369ca8d9962e18cd7fdcc4fc37bab35e8e8a7186da0614",
    REL_GUIDANCE_R4:
        "c0706d0f176529b14228e9be7f54bcb3e38229e80dda6f4849909e838e09d0d3",
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
    RAW_FILES["applied-top"]:
        "138d0dacd3ff4d4176e7ca21a593e7a070f9f99a684462ce3c50ed2c0272210e",
    RAW_FILES["applied-bottom"]:
        "03e846d3f9941ef69c511169c85c850f649dce0c3dec8379b7ff7020d6489a74",
    RAW_FILES["prep1-top"]:
        "40af39f8477d12958a0a1644ce02a32d472282dc182f3ce93b73c0ea1c580082",
    RAW_FILES["prep1-bottom"]:
        "119d23903737d68633986d0da63db5306f9b5d46063b1f38f138ffb8c4985886",
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
    "盲读派发词只含渲染 PNG 绝对路径+observation-guidance-r4.md 要点；"
    "无任何 GT 坐标/类别提示/期望缺陷描述；读图者不接触 GT/派生台账/"
    "任何校准产物路径")

GUIDANCE_REUSE_NOTE = (
    "observation-guidance-r4.md 逐字沿用为本轮 reader 判读指引（单变量"
    "纪律：不写新指引；sha 锚定于 render-framing-r5.json "
    "frozen_inputs.guidance_reuse；沿用含其内部 round_id_constant"
    "「2026-09-06-r4」字样——本轮自身常量见 run-r5 的 round_id，两者"
    "不冲突：指引内容冻结不变是单变量设计的一部分）")

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 5 轮迭代"
    "（development 域单变量仪器迭代轮，迭代轮不得冒充留出证据）。")

INSTRUMENT_NATURE = "单变量变更（有效分辨率；非仪器整体更换）"
INSTRUMENT_COMPONENTS = [
    "光栅 dpi 320→640（线度×2、像素数×4）",
    "光栅化后裁剪到板像素界并留固定白边 120px（取景从整页收敛到板邻域）",
]
INSTRUMENT_UNCHANGED = [
    "矢量内容（R4 冻结 PDF 逐字节输入）",
    "图层清单（F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard / B 同构）",
    "40pt 组合页步骤（与 R4 逐字节等价，探针保真证明见 framing-r5）",
    "判读指引（observation-guidance-r4.md 逐字沿用）",
    "GT 集、协议与度量版本",
]
INSTRUMENT_ATTRIBUTION = (
    "render-framing-r5.json difference_from_r4：R4 相对 R3 为复合仪器"
    "更换（轮间变化不能单一归因）；R5 在 R4 冻结矢量输出上仅动有效"
    "分辨率，恢复单变量归因——R4→R5 的任何 reader 表现变化（含弃权率"
    "变化）首先归因于分辨率/取景，而非内容或图层。")


def _fail(msg: str) -> None:
    print(f"[s31-cal-r5] FAIL: {msg}")
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
    （按 gt_id 对齐 derivation-log-r5；其余字段逐字段原样）。"""
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
                    "note": ("R5 仪器预注册件（单变量有效分辨率变更："
                             "dpi 640+裁剪板界+白边 120px；矢量内容/图层/"
                             "指引与 R4 一致）")},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R5, "sha256": _sha(REL_DERIV_R5),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取本台账"
                     " frame_box_pct_r5（R5 仪器像素界重投影）；"
                     "board_box_mm/side 等其余字段与 GT 文件逐字段原样；"
                     "13 条全部 side=top")},
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
                       "r5": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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


def build_run() -> dict:
    """run-r5 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
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
        {"path_rel": REL_FRAMING_R5,
         "role": "render_framing_r5_preregistration",
         "sha256": _sha(REL_FRAMING_R5)},
        {"path_rel": REL_GUIDANCE_R4, "role": "observation_guidance_r4_reused",
         "sha256": _sha(REL_GUIDANCE_R4)},
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
         "role": "render_png_applied_top_r5", "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r5",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"], "role": "render_png_prep1_top_r5",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r5",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r5",
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
            "ref": {"path_rel": REL_FRAMING_R5, "sha256": _sha(REL_FRAMING_R5)},
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
        "preregistration": {
            "round_id_constant": ROUND_ID,
            "metric_version": cal.METRIC_VERSION_V3,
            "comparator": {
                "module": "pcbflow/calibration.py",
                "sha256_first8": _sha("pcbflow/calibration.py")[:8],
                "thresholds": {"containment_min": cal.CONTAINMENT_MIN,
                               "area_ratio_max": cal.AREA_RATIO_MAX},
                "thresholds_note": "声明常量，本轮零覆盖",
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
                "per_view_dispatch": ("top/bottom 各一独立盲读，串行派发"
                                      "（先 top 后 bottom）；每图独立判读"),
                "discipline": DISPATCH_DISCIPLINE,
                "guidance_ref": {"path_rel": REL_GUIDANCE_R4,
                                 "sha256": _sha(REL_GUIDANCE_R4),
                                 "frozen_before_render": True,
                                 "frozen_before_read": True,
                                 "reuse_note": GUIDANCE_REUSE_NOTE},
            },
            "note": ("轮次预注册链：render-framing-r5.json 先于本轮任何"
                     "官方渲染落盘（探针全内存、白边常量 120px 定稿先于"
                     "成图）；判读指引=observation-guidance-r4.md 逐字"
                     "沿用（单变量纪律）；GT 重投影（derivation-log-r5."
                     "json，13 条 frame_box_pct_r5）先于盲读落盘；盲读后"
                     "本包只做比对与记录（读者产物零改动）。GT 冻结纪律："
                     "轮后未增删改。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "r4_run": {"path_rel": REL_RUN_R4, "sha256": _sha(REL_RUN_R4)},
            "note": ("R3（3D 仪器）与 R4（2D PDF 仪器）run 在案；轮间"
                     "对比见 round5-dev-record.json 的方向性观察"
                     "（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-06-r5（事件序="
            "预注册冻结→渲染→GT 重投影→盲读→比对记录）"),
    }


DEV_OBSERVATIONS = [
    "R4→R5 旗标量对照：8→19（非弃权 2→11、弃权 6→8），弃权率 "
    "0.75（6/8）→0.421053（8/19）；分态弃权率 applied 4/9、prep1 4/10。"
    "单变量归因声明（framing-r5 difference_from_r4）下，该变化首先"
    "归因于有效分辨率（dpi 320→640+裁剪板界+白边 120px），而非内容"
    "或图层。",
    "本系列首个框级命中（r1–r4 在案 run 均 matches=0）：prep1 态 "
    "R5T-013（courtyard_crowding，[0.615, 0.585, 0.79, 0.8]）与 "
    "GT-REVC-P1-L1NB 一对一匹配（containment=1.0、面积比 6.739726≤"
    "AREA_RATIO_MAX=10.0）；gt_recall_total 0.0→0.076923（1/13）、"
    "seed_match_rate_total 0.0→0.090909（1/11，诊断口径）。",
    "applied 态 matches=0 的最近出局项：R5T-005（两态同位框 "
    "[0.185, 0.46, 0.315, 0.63]）与 GT-REVC-AP-7-C31U4 框重叠 "
    "containment=0.882465≥0.5，但读者框面积/GT 框面积≈11.93>"
    "AREA_RATIO_MAX=10.0 被面积比上限排除（位置已入邻域、面积仍超"
    "一个数量级）；prep1 态 R5T-010（silk_readability）与 "
    "GT-REVC-P1-R4J3 框重叠 containment=0.510336 但类别不符"
    "（silk_readability vs courtyard_crowding）不入候选。二者均为"
    "描述性位置记录，非度量命中。",
    "与 R4 匹配位置对照：R4 唯一非弃权旗标区（两态同位，r4 取景下 "
    "[0.178, 0.14, 0.224, 0.215]，换算板坐标约 [43.8, 19.3]–"
    "[58.8, 37.2]mm）与本轮任一非弃权旗标区在板坐标下零重叠；本轮"
    "非弃权旗标中 R5T-004/R5T-013（两态同位）完整覆盖 GT-REVC-P1-"
    "L1NB 与 GT-REVC-P1-L1SHORT（containment 均=1.0；L1NB 类别相符"
    "成匹配，L1SHORT 为 other_advisory 类别不符未匹配）。",
    "定位粒度：R5 非弃权旗标框换算板坐标后约 4.4×6.0mm 至 "
    "10.3×17.5mm，R4 唯一非弃权框约 15.0×17.9mm；与板线度像素 ×2"
    "（882→1765/1766）、板占比（短边）0.294→0.880299 的有效分辨率"
    "提升方向相容（描述性观察，derivation-log-r5 "
    "renders_r5.vs_r4_effective_resolution）。",
    "bottom 视结构性事实与 R4 相同：两 bottom 渲染仍逐字节相同"
    "（f87f8fec…，applied-bottom 与 prep1-bottom 内容级等价），本轮 "
    "bottom 各 1 旗标、全部弃权（other_advisory，「白色翼状/瓣状"
    "图形……无法负责任地归类」，reader 原文）；GT 13 条全部 side=top，"
    "bottom 旗标不参与匹配。",
    "弃权理由文本仍集中于「当前分辨率无法确认/无法负责任归类」"
    "（reader 原文，abstain 语义内），但同指引下非弃权旗标数量与"
    "覆盖类别（silk_readability 5 + courtyard_crowding 6）较 R4"
    "（仅 2 条 courtyard_crowding）增多；类别构成变化本轮可首先"
    "归因于分辨率/取景（单变量设计）。",
]

DEV_NEXT_TARGETS = [
    "面积比出局项：applied 态 R5T-005/R5T-014 与 GT-REVC-AP-7-C31U4 "
    "containment=0.882465 但面积比≈11.93 超上限——候选迭代方向=指引"
    "侧收紧邻域框口径（读者框收窄至缺陷邻域本身；属指引/仪器侧候选"
    "变更，须先预注册再盲读；度量阈值 AREA_RATIO_MAX 本身零改动）。",
    "类别判据清晰度：R5T-010 与 courtyard GT 框重叠但按 "
    "silk_readability 报告（类别不符不入候选）——评估指引中类别判据"
    "是否需示例化（同样须预注册；单变量纪律下逐项变更）。",
    "bottom 视信息量：延续 R4 目标——B 面图层构成下 bottom 盲读仍"
    "全弃权，评估为 bottom 视单独定图层清单或继续提高分辨率（同样须"
    "预注册）。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance）并声明 development 域；达标证据仍须留出集"
    "（未建立，TBD）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round5-dev-record 文档构建（T3；单向引用 run-r5 sha）。"""
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round5_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域单变量仪器迭代轮（第五轮）：本轮只改变一个"
            "仪器变量——有效分辨率（光栅 dpi 320→640+裁剪板界+白边 "
            "120px，预注册于盲读前），矢量内容/图层/判读指引/GT 集/"
            "协议与度量版本与 R4 一致，恢复单变量归因；按协议 v1 §4，"
            "迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "run_record_ref": {"path_rel": REL_RUN_R5, "sha256": run_sha},
        "flag_production": {
            "reader_id": "reader-r5-blind",
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
        "directional_observation_vs_r4": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，单变量仪器迭代=有效分辨率）19 旗标"
            "中 8 弃权、11 非弃权，matches=1（R5T-013↔GT-REVC-P1-L1NB，"
            "containment=1.0）：gt_recall=0.076923（1/13）、"
            "seed_match_rate=0.090909（1/11，诊断口径，禁称 "
            "precision/FPR）、abstain_rate=0.421053（8/19，较 R4 的 "
            "0.75 下降），联合评价 not_met（gt_recall 与 "
            "seed_match_rate 两项未达 APR-0011 暂行线；诊断对照，非"
            "采纳门）。本系列（r1–r4 在案 run 均 matches=0）首次出现"
            "框级命中，与弃权率下降、定位粒度变细等同为方向性观察，"
            "如实记录；不做「能力已修复/已达成」类断言；单变量归因"
            "声明下轮间变化首先归因于有效分辨率。本批证据按协议 v1 "
            "§4 属 development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
            "R4 对照基线=calibration-run-r4.json（0cf8bb31…，在案）；"
            "R3 对照基线=calibration-run-r3.json（0b09012e…，在案）；"
            "轮间对比只做方向性描述。",
        ],
    }


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
    out_run = _rel(REL_RUN_R5)
    out_dev = _rel(REL_DEV_RECORD)
    for t in (out_run, out_dev):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r5")

    # 落盘 run → 实测 sha → 构建 dev record（单向引用）
    out_run.write_bytes(run_bytes)
    if out_run.read_bytes() != run_bytes:
        _fail("回读不一致: calibration-run-r5.json")
    run_sha = _sha(REL_RUN_R5)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round5-dev-record")
    out_dev.write_bytes(dev_bytes)
    if out_dev.read_bytes() != dev_bytes:
        _fail("回读不一致: round5-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    print(f"[s31-cal-r5] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s31-cal-r5] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s31-cal-r5] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    print(f"[s31-cal-r5] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']}")
    print(f"[s31-cal-r5] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    for rel in (REL_RUN_R5, REL_DEV_RECORD):
        print(f"[s31-cal-r5] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s31-cal-r5] R5 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
