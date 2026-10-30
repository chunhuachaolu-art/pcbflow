#!/usr/bin/env python
"""CAL-R4-CLOSE：reader 判读迭代第四轮收口包（比对+记录落盘）。

职责（库侧 pcbflow/* 零改动，只 import；本脚本仅编排+纯函数调用）：

  T1  解析 4 个 reader-raw-r4-*.txt（fail-closed：非法 JSON 即停止；
      逐旗标过 calibration fail-closed 校验，被拒者如实入拒收清单，
      reader 产物零改动）；视角注入=图像名确定性映射
      （*-top.png→top、*-bottom.png→bottom；reader 产物无 side 字段，
      视角由编排侧注入 compare_v3 的 flag_views）。
  T2  双态 compare_v3（声明常量零覆盖）+ aggregate：
      applied 态=applied-top+applied-bottom 旗标 vs ground-truth-v2
      九条（frame_box_pct=derivation-log-r4 的 frame_box_pct_r4，
      board_box_mm/side 等其余字段与 GT 文件逐字段原样）；prep1 态=
      prep1-top+prep1-bottom 旗标 vs ground-truth-v1 四条（同重投影
      规则）。达标线=APR-0011 暂时采纳基线，逐项诊断对照（禁改阈值
      措辞；seed_match_rate 带 SEED_METRIC_NOTE 口径，禁称
      precision/FPR）。→ calibration-run-r4.json。
  T3  development 域记录（本轮性质/仪器复合变更/诚实结论/方向性观察/
      下一迭代目标；引用 run-r4 落盘 sha 单向引用）→
      round4-dev-record.json。

纪律：out/ 既有文件零改动（防覆写 guard；本包仅两新 JSON）；域声明=
development（协议 v1 §1/§4：迭代轮不得冒充留出证据）；无 wall-clock
（日期/轮次=声明常量 2026-09-06 / 2026-09-06-r4）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；输入先验
锚不符即中止；同参重建逐字节一致（byte-exact 可重跑）；零子进程/零
网络；datasets/ 零写入；不 git commit/push。

用法：python scripts/s30_calibration_r4_compare.py   （仓库根执行）
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
ROUND_ID = "2026-09-06-r4"
ROUND_LABEL = "r4"
EVALUATION_DOMAIN = "development"

REL_PROTOCOL = "out/v3-tl2/calibration/evaluation-protocol-v1.md"
REL_FRAMING_R4 = "out/v3-tl2/calibration/render-framing-r4.json"
REL_GUIDANCE_R4 = "out/v3-tl2/calibration/observation-guidance-r4.md"
REL_INTEGRITY_R4 = "out/v3-tl2/calibration/staging-integrity-r4.json"
REL_WITNESS_R4 = "out/v3-tl2/calibration/render-witness-r4.json"
REL_DERIV_R4 = "out/v3-tl2/calibration/derivation-log-r4.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_RUN_R3 = "out/v3-tl2/calibration/calibration-run-r3.json"
REL_RUN_R4 = "out/v3-tl2/calibration/calibration-run-r4.json"
REL_DEV_RECORD = "out/v3-tl2/calibration/round4-dev-record.json"

RAW_FILES = {
    "applied-top": "out/v3-tl2/calibration/reader-raw-r4-applied-top.txt",
    "applied-bottom":
        "out/v3-tl2/calibration/reader-raw-r4-applied-bottom.txt",
    "prep1-top": "out/v3-tl2/calibration/reader-raw-r4-prep1-top.txt",
    "prep1-bottom": "out/v3-tl2/calibration/reader-raw-r4-prep1-bottom.txt",
}
PNG_FILES = {
    "applied-top": "out/v3-tl2/calibration/renders-r4/applied-top.png",
    "applied-bottom": "out/v3-tl2/calibration/renders-r4/applied-bottom.png",
    "prep1-top": "out/v3-tl2/calibration/renders-r4/prep1-top.png",
    "prep1-bottom": "out/v3-tl2/calibration/renders-r4/prep1-bottom.png",
}

#: 输入先验锚（收口包开工时实读入账；不配即中止——防篡改/防覆写）。
#: 四 PNG 锚与 render-witness-r4.json renders[].sha256 逐一相等。
FROZEN_SHA256 = {
    REL_PROTOCOL:
        "22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e",
    REL_FRAMING_R4:
        "7d41181636434d242cfd4fa6e6e460e922ec1ea537497f54d0016f0993012f98",
    REL_GUIDANCE_R4:
        "c0706d0f176529b14228e9be7f54bcb3e38229e80dda6f4849909e838e09d0d3",
    REL_INTEGRITY_R4:
        "0458f3a8d14cb2c03a71d90f6bf421e52adc62309ae26be6a812531b68459c6d",
    REL_WITNESS_R4:
        "369c722ed6c740f9b7a3597665c510a4feeac27da03431a18c0ec5148b1d6e98",
    REL_DERIV_R4:
        "4611ddb6b817a872371a8430b55b2427fc7b09f56f5689d6266f022fb83e7a94",
    REL_GT_V1:
        "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_GT_V2:
        "e1cb63d5e05761feada0b2dd030018bc04c3d3d165f33adcda2b9b348bd4b3a9",
    REL_RUN_R3:
        "0b09012e01b2d9fbd0cf6afb0d71191c657746b078a0debb0703ed999af734cd",
    RAW_FILES["applied-top"]:
        "ce8e4c05632c06a068a1a243251c31a18c3d5d2876c6f253533c89cf9e679752",
    RAW_FILES["applied-bottom"]:
        "2b902e095a2cb122aedb29982a4f0bfdf5b9c99a49528256ac648329f9cce07c",
    RAW_FILES["prep1-top"]:
        "e54e78d9cdaf710685a95687648da92f21b50b1cc4ff165cbb55fa277b8d5953",
    RAW_FILES["prep1-bottom"]:
        "094f8d4a5a2e2771abbf4f63a8ecb0bd8ab63cad7b91b121919811ec3b0ef2aa",
    PNG_FILES["applied-top"]:
        "8f3d07aec19b5f96df87a78a9c944eb763cd842580ab247b89de0c34a7034f7a",
    PNG_FILES["applied-bottom"]:
        "ba0b7259d1c18950974edd28230ba34883a548f962f2b93e5b88da425f30d84e",
    PNG_FILES["prep1-top"]:
        "8b9fbb65122f7a5049cccd493ed478e5bca19ebaa90003277d5926c881811fa8",
    PNG_FILES["prep1-bottom"]:
        "ba0b7259d1c18950974edd28230ba34883a548f962f2b93e5b88da425f30d84e",
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

DOMAIN_BASIS_QUOTE = (
    "evaluation-protocol-v1.md §1：development=Rev-C 种子域；§4：每轮"
    "盲读前冻结 reader 协议/模型与提示词版本/度量版本/GT 集，轮次开始"
    "后不得增删；若根据某批评测结果调整协议/度量/GT，该批整体降级为 "
    "development 证据，不得冒充未见留出。本轮为同域第 4 轮迭代"
    "（development 域仪器迭代轮，迭代轮不得冒充留出证据）。")


def _fail(msg: str) -> None:
    print(f"[s30-cal-r4] FAIL: {msg}")
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


def _gt_entries_with_r4_reprojection(gt_rel: str, deriv_doc: dict) -> list:
    """GT 文件条目 + R4 重投影：frame_box_pct ← frame_box_pct_r4
    （按 gt_id 对齐 derivation-log-r4；其余字段逐字段原样）。"""
    r4 = {e["gt_id"]: e["frame_box_pct_r4"] for e in deriv_doc["entries"]}
    out = []
    for e in _json_load(gt_rel)["gt_entries"]:
        if e["gt_id"] not in r4:
            _fail(f"derivation-log-r4 缺 gt_id 重投影: {e['gt_id']}")
        e2 = dict(e)
        e2["frame_box_pct"] = list(r4[e["gt_id"]])
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
        "framing": {"path_rel": REL_FRAMING_R4, "sha256": _sha(REL_FRAMING_R4),
                    "note": "R4 仪器预注册件（2D PDF plot+fitz 光栅化）"},
        "gt_file": {"path_rel": gt_rel, "sha256": gt_sha,
                    "role": ("gt_seed（prep1 态 4 条）" if state == "prep1"
                             else "gt_expansion（applied 态 9 条）")},
        "gt_reprojection": {
            "path_rel": REL_DERIV_R4, "sha256": _sha(REL_DERIV_R4),
            "note": ("compare 输入 gt_entries 的 frame_box_pct 取本台账"
                     " frame_box_pct_r4（R4 仪器像素界重投影）；"
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
                       "r3": "not_met（在案）",
                       "r4": f"{ 'met' if all_met else 'not_met' }（本轮）"},
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
    """run-r4 文档内存构建（纯函数可重入；同输入 ⇒ 同字节）。"""
    parsed = {key: parse_reader_raw(rel) for key, rel in RAW_FILES.items()}

    rejections = []
    for key in RAW_FILES:
        for img in parsed[key]["images"]:
            for r in img["rejected"]:
                rejections.append({"file": key, **r})
    for key in RAW_FILES:
        if not parsed[key]["images"]:
            _fail(f"reader-raw per_image 空: {key}")

    deriv = _json_load(REL_DERIV_R4)
    gt_applied = _gt_entries_with_r4_reprojection(REL_GT_V2, deriv)
    gt_prep1 = _gt_entries_with_r4_reprojection(REL_GT_V1, deriv)
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
            "applied_top": len(appl["reader_flags"]),
            "applied_bottom": sum(
                1 for f in appl["reader_flags"]
                if appl["flag_views"][f["flag_id"]] == "bottom"),
            "prep1_top": len(prep["reader_flags"]),
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
        {"path_rel": REL_FRAMING_R4, "role": "render_framing_r4_preregistration",
         "sha256": _sha(REL_FRAMING_R4)},
        {"path_rel": REL_GUIDANCE_R4, "role": "observation_guidance_r4",
         "sha256": _sha(REL_GUIDANCE_R4)},
        {"path_rel": REL_INTEGRITY_R4, "role": "staging_integrity_r4",
         "sha256": _sha(REL_INTEGRITY_R4)},
        {"path_rel": REL_WITNESS_R4, "role": "render_witness_r4",
         "sha256": _sha(REL_WITNESS_R4)},
        {"path_rel": REL_DERIV_R4, "role": "gt_reprojection_log_r4",
         "sha256": _sha(REL_DERIV_R4)},
        {"path_rel": REL_GT_V1, "role": "gt_seed_prep1",
         "sha256": _sha(REL_GT_V1)},
        {"path_rel": REL_GT_V2, "role": "gt_expansion_applied",
         "sha256": _sha(REL_GT_V2)},
        {"path_rel": PNG_FILES["applied-top"], "role": "render_png_applied_top_r4",
         "sha256": _sha(PNG_FILES["applied-top"])},
        {"path_rel": PNG_FILES["applied-bottom"],
         "role": "render_png_applied_bottom_r4",
         "sha256": _sha(PNG_FILES["applied-bottom"])},
        {"path_rel": PNG_FILES["prep1-top"], "role": "render_png_prep1_top_r4",
         "sha256": _sha(PNG_FILES["prep1-top"])},
        {"path_rel": PNG_FILES["prep1-bottom"],
         "role": "render_png_prep1_bottom_r4",
         "sha256": _sha(PNG_FILES["prep1-bottom"])},
    ]

    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_r4",
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
            "nature": "复合变更（仪器整体更换，非参数微调）",
            "components": [
                "3D pcb render → 2D pcb export pdf + fitz 光栅化"
                "（投影/外观/成像几何）",
                "新增 courtyard 轮廓层（F.Courtyard/B.Courtyard）",
            ],
            "attribution_note": (
                "render-framing-r4.json difference_from_r3：本轮 reader "
                "表现的任何轮间变化都不能单一归因于 courtyard 可见性，"
                "须视为仪器整体更换"),
            "ref": {"path_rel": REL_FRAMING_R4, "sha256": _sha(REL_FRAMING_R4)},
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
                                 "frozen_before_read": True},
            },
            "note": ("轮次预注册链：framing-r4/guidance-r4 先于渲染落盘并"
                     "固定 sha（staging-integrity-r4.json）；GT 重投影先于"
                     "盲读落盘；盲读后本包只做比对与记录（读者产物零改动）"
                     "。GT 冻结纪律：轮后未增删改。"),
        },
        "reference_rounds": {
            "r3_run": {"path_rel": REL_RUN_R3, "sha256": _sha(REL_RUN_R3)},
            "note": ("R3（3D 仪器）run 在案；轮间对比见 round4-dev-record"
                     ".json 的方向性观察（development 域，只描述不断言）"),
        },
        "deterministic_recompute_note": (
            "同输入 byte-exact 可重跑：盲读原文为固定输入（hash 在案），"
            "比较器为纯函数，无 wall-clock"),
        "no_wallclock_note": (
            "无机器时间戳；轮次标识=声明常量 2026-09-06-r4（事件序="
            "预注册冻结→渲染→GT 重投影→盲读→比对记录）"),
    }


DEV_OBSERVATIONS = [
    "两轮 matches 均为 0（13 条 GT 全未命中）：seed_match_rate 保持 "
    "0.0，gt_recall 保持 0.0；本轮未产生框级命中，方向性与 R3 相同。",
    "弃权率 0.75（6/8）显著高于 R3 的 0.142857（2/14）：本轮 bottom 视 "
    "4/4 全弃权、top 视 2/4 弃权；弃权原因集中于「当前分辨率无法确认"
    "是否接触/重叠」（reader 原文，abstain 语义内）。",
    "本轮非弃权旗标 2 条均为 courtyard_crowding（top 视，两态同位同文"
    "框 [0.178, 0.14, 0.224, 0.215]）；R3 两态非弃权旗标 12 条中含 "
    "1 条 courtyard_crowding（prep1 态 R3T-004）与 5 条 silk_readability"
    "等；类别构成随仪器复合变更发生变化，归因不可拆分（framing-r4 "
    "difference_from_r3 声明）。",
    "本轮两 bottom 渲染逐字节相同（applied-bottom.png 与 prep1-bottom.png "
    "同为 ba0b7259…，B 面图层两态一致的仪器事实）；bottom 视 4 旗标全"
    "弃权且 GT 全部 side=top，bottom 旗标未参与匹配。",
    "R4 图幅中板像素占比更低（board_px_fraction_of_height≈0.294，"
    "render-witness-r4；R3 3D 渲染板占图幅比例更高），与读者多次以"
    "「当前分辨率」弃权的表述在方向上相容；仅为仪器参数的描述性观察。",
]

DEV_NEXT_TARGETS = [
    "渲染可读性：提高光栅化 dpi 或缩小页面白边占比，使板像素占比与"
    "缺陷特征尺寸进入可辨认区间（本轮读者弃权理由集中于分辨率不足；"
    "属仪器侧候选变更，须先预注册再渲染）。",
    "bottom 视信息量：B 面图层构成（B.CrtYd 无图元、B 面要素少）下 "
    "bottom 盲读全部弃权——评估是否为 bottom 视单独定图层清单或提高"
    "分辨率（同样须预注册）。",
    "迭代目标不变式：任何仪器/指引变更后重跑盲读前，先冻结预注册件"
    "（framing/guidance）并声明 development 域；达标证据仍须留出集"
    "（未建立，TBD）。",
]


def build_dev_record(run_doc: dict, run_sha: str) -> dict:
    """round4-dev-record 文档构建（T3；单向引用 run-r4 sha）。"""
    appl, prep = run_doc["states"]["applied"], run_doc["states"]["prep1"]
    agg = run_doc["aggregation"]
    comp = run_doc["compliance"]
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_round4_dev_record",
        "round_id": ROUND_ID,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "domain_basis_quote": DOMAIN_BASIS_QUOTE,
        "round_nature": (
            "development 域仪器迭代轮（第四轮）：本轮更换渲染仪器"
            "（预注册于盲读前）并重跑双态盲读与比对；按协议 v1 §4，"
            "迭代轮证据不冒充未见留出，in_calibrated_range 恒 False"),
        "instrument_change": run_doc["instrument_change"],
        "preregistration_chain": {
            item["role"]: {"path_rel": item["path_rel"],
                           "sha256": item["sha256"]}
            for item in run_doc["preregistration"]["frozen_artifacts"]
        },
        "run_record_ref": {"path_rel": REL_RUN_R4, "sha256": run_sha},
        "flag_production": {
            "reader_id": "reader-r4-blind",
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
        "directional_observation_vs_r3": DEV_OBSERVATIONS,
        "honest_conclusion": (
            "本轮（development 域，仪器复合变更）8 旗标中 6 弃权、2 非"
            "弃权，matches=0：gt_recall=0.0、seed_match_rate=0.0、"
            "abstain_rate=0.75，联合评价 not_met（诊断对照，非采纳门）。"
            "与非弃权旗标出现 courtyard_crowding 类别及 bottom 全弃权等"
            "方向性现象一并如实记录；不做「能力已修复/已达成」类断言，"
            "轮间变化不可单一归因于 courtyard 层（仪器整体更换）。本批"
            "证据按协议 v1 §4 属 development 域，不得冒充留出。"),
        "next_iteration_targets": DEV_NEXT_TARGETS,
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本记录不进任何 gate 谓词、"
            "不翻转 critic_calibration_in_range（恒 False 维持 fail-closed）。",
            "seed_match_rate 命名约束：禁称 precision/FPR（process-v2 §4）；"
            "同板不同渲染不是独立板（process-v2 §4 联合评价）。",
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
    out_run = _rel(REL_RUN_R4)
    out_dev = _rel(REL_DEV_RECORD)
    for t in (out_run, out_dev):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    run = build_run()
    run_bytes = hashing.canonical_json_bytes(run)

    # byte-exact 可重跑自证（同参重建两次逐字节一致）
    run2 = build_run()
    if hashing.canonical_json_bytes(run2) != run_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: run-r4")

    # 落盘 run → 实测 sha → 构建 dev record（单向引用）
    out_run.write_bytes(run_bytes)
    if out_run.read_bytes() != run_bytes:
        _fail("回读不一致: calibration-run-r4.json")
    run_sha = _sha(REL_RUN_R4)

    dev = build_dev_record(run, run_sha)
    dev_bytes = hashing.canonical_json_bytes(dev)
    dev2 = build_dev_record(build_run(), run_sha)
    if hashing.canonical_json_bytes(dev2) != dev_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: round4-dev-record")
    out_dev.write_bytes(dev_bytes)
    if out_dev.read_bytes() != dev_bytes:
        _fail("回读不一致: round4-dev-record.json")

    agg = run["aggregation"]
    comp = run["compliance"]
    print(f"[s30-cal-r4] 解析：4 reader-raw 全部 direct JSON 解析成功；"
          f"旗标 {agg['flag_count_total']}（非弃权 {agg['scored_total']}、"
          f"弃权 {agg['abstain_count_total']}）；拒收清单 "
          f"{len(run['parse_rejections'])} 条")
    print(f"[s30-cal-r4] 视角注入：{run['reader']['view_injection']['rule']}")
    for st in ("applied", "prep1"):
        r = run["states"][st]["compare_v3"]
        print(f"[s30-cal-r4] {st}: flags={r['reader_flag_count']} "
              f"scored={r['reader_scored_count']} matches={len(r['matches'])} "
              f"gt_recall={r['gt_recall']} seed={r['seed_match_rate']} "
              f"abstain_rate={r['abstain']['abstain_rate']} "
              f"view_check={run['states'][st]['view_check']}")
    print(f"[s30-cal-r4] aggregate: gt_recall_total={agg['gt_recall_total']} "
          f"seed_match_rate_total={agg['seed_match_rate_total']} "
          f"abstain_rate_total={agg['abstain_rate_total']}")
    print(f"[s30-cal-r4] compliance: joint={comp['joint_evaluation']} "
          f"in_range={comp['critic_calibration_in_range']} "
          f"domain={run['evaluation_domain']}")
    for rel in (REL_RUN_R4, REL_DEV_RECORD):
        print(f"[s30-cal-r4] sha256[:8] {Path(rel).name} = {_sha(rel)[:8]}")
    print("[s30-cal-r4] R4 收口落盘完成（development 域；不是门；"
          "reader 产物与既有 out/ 件零改动）")


if __name__ == "__main__":
    main()
