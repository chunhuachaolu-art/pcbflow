#!/usr/bin/env python
"""S24：校准比较器 v3 复算落盘（修正包 P3-A：一对一匹配+语义更名+
abstain 口径）。

职责（s20/s23 装配模式同构；既有产物零覆写零删除）：

  calibration-run-v3-on-r1-inputs.json   v3 对 v1 首测输入复算
  calibration-run-v3-on-r2-inputs.json   v3 对 v2 二测输入复算
  calibration-metric-v3-selfcheck.json   v3 构造性用例机器自检

机制：
- 输入（磁盘实读 fail-closed，先验 hash 锚不配即中止）：
  ground-truth-v1.json（零改动）、reader-raw-cal-v1/v2.txt、
  calibration-run-v1/v2.json（既有 v1/v2 归档件）；
- reader flags 复原：归档 run 件只含 report（无内嵌 flags）→ 按
  process-v1 §2 步骤 3 与 s20 既有口径从 reader-raw JSON 做五键投影
  {flag_id, category, confidence, abstain, frame_box_pct}（内容零
  改动、顺序保持）；投影结果先复算 v1/v2 与归档 record canonical
  逐字节对账（不一致即中止），方进入 v3 复算；
- v3 复算不含 flag_views（历史轮不冒充已做视角检查，
  view_check=not_applicable 如实标注；reader 原文 side 类字段不属
  协议五键、已投影剔除，复算不回读）；
- 自检：一对一去重/确定性（同分字典序+两次调用字节一致）/视角不
  设防标注/输出键契约（无 reader_false_positive_ids 递归查）/
  abstain 率算术/GT 自比较（视角 top 全匹配、视角 bottom 全拦）/
  CLI 进程内 round-trip/阈值沿用断言（不引入新可调阈值）/
  v2↔v3 归档输入对账（差异只允许来自一对一/更名/v2 已声明的面积
  比条件）；
- 收尾：同参重建逐字节比对（byte-exact 可重跑）+ 打印四新件
  （三 JSON + calibration-process-v2.md）sha256 前 8。

红线：out/ 只读，例外仅限本包三件新 JSON（process-v2.md 由本包
另行落盘，此处只读其 hash）；零子进程；无 wall-clock（日期=声明
常量 2026-09-05）；canonical JSON；不 commit/不翻转任何门。

用法：python scripts/s24_calibration_v3_recompute.py   （仓库根执行）
"""

from __future__ import annotations

import io
import json
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"
DECLARED_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）

READER_KEYS = ("flag_id", "category", "confidence", "abstain",
               "frame_box_pct")

REL_GT = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_RAW1 = "out/v3-tl2/calibration/reader-raw-cal-v1.txt"
REL_RAW2 = "out/v3-tl2/calibration/reader-raw-cal-v2.txt"
REL_RUN1 = "out/v3-tl2/calibration/calibration-run-v1.json"
REL_RUN2 = "out/v3-tl2/calibration/calibration-run-v2.json"
REL_MD = "out/v3-tl2/calibration/calibration-process-v2.md"

OUT_ON_R1 = CAL / "calibration-run-v3-on-r1-inputs.json"
OUT_ON_R2 = CAL / "calibration-run-v3-on-r2-inputs.json"
OUT_SELF = CAL / "calibration-metric-v3-selfcheck.json"

# 输入先验锚（P3-A 开工时实读入账；不配即中止——防篡改/防覆写）
FROZEN_SHA256 = {
    REL_GT: "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_RAW1: ("7f6a165d8af570861f53baa77f820205974e7051da8de2c4aa0f2c7c"
               "989246d3"),
    REL_RAW2: ("16034e277bd3c7b49e61bc5823241ccb5bfb92c6f69d9f88c8d9b9f"
               "c21e4d05d"),
    REL_RUN1: ("ff60a7bb4a6600dd417c6afa9d87122a13d26ee70ed0e1e0e45a625"
               "ab1cac31c"),
    REL_RUN2: ("c3ea9a2e6d326e0f8d3c095c9606673886113e577356861989131a8"
               "a3bc22877"),
}

EXTRACTION_NOTE = (
    "归档 run 件只含 report（无内嵌 flags）→ 从 reader-raw JSON 复原："
    "按 process-v1 §2 步骤3 与 s20 既有口径做五键投影 {flag_id, "
    "category, confidence, abstain, frame_box_pct}（内容零改动、顺序"
    "保持；side/description 等非协议键不进度量）；投影结果先复算 "
    "v1/v2 与归档 record canonical 逐字节对账一致（fail-closed）后方"
    "进入 v3 复算。")

VIEW_NOTE = (
    "按 P3-A 规定本轮复算不注入 flag_views（历史轮不冒充已做视角检查"
    "，view_check=not_applicable 如实标注）；reader 原始文本逐旗标另"
    "带 side 字段，但该字段不属协议五键、已按 process-v1 §2 投影剔除"
    "，v3 复算不回读其作为视角依据；未来盲读轮按 calibration-process"
    "-v2 §3 由编排侧显式注入 flag_views。")


def _fail(msg: str) -> None:
    print(f"[s24-cal3] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _write_canonical(path: Path, obj) -> bytes:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return data


def _extract_reader_flags(raw_rel: str) -> list:
    """归档 reader 原文 → 比较器五键投影（内容零改动；口径见
    EXTRACTION_NOTE）。"""
    raw = json.loads(_rel(raw_rel).read_text(encoding="utf-8"))
    flags = []
    for board in raw["per_board"]:
        for f in board["flags"]:
            flags.append({k: f[k] for k in READER_KEYS})
    return flags


def _cli_roundtrip_v3(flags: list, gt_entries: list) -> dict:
    """进程内 CLI round-trip（runpy __main__；stdin→stdout；零子进程）。"""
    payload = {"reader_flags": flags, "gt_entries": gt_entries,
               "metric_version": cal.METRIC_VERSION_V3}
    buf_out, buf_in = io.StringIO(), io.StringIO(json.dumps(payload))
    old_out, old_in = sys.stdout, sys.stdin
    sys.stdout, sys.stdin = buf_out, buf_in
    try:
        runpy.run_module("pcbflow.calibration", run_name="__main__",
                         alter_sys=False)
    finally:
        sys.stdout, sys.stdin = old_out, old_in
    return json.loads(buf_out.getvalue())


def _assert_no_fp_key(obj, path="report") -> None:
    """v3 键契约：任何层级不得出现越界命名键。"""
    if isinstance(obj, dict):
        for banned in ("reader_false_positive_ids",
                       "reader_precision_vs_seed_gt"):
            if banned in obj:
                _fail(f"键契约失败：{path} 出现越界键 {banned}")
        for k, v in obj.items():
            _assert_no_fp_key(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_fp_key(v, f"{path}[{i}]")


def _pairs(report) -> list:
    return [(m["flag_id"], m["gt_id"]) for m in report["matches"]]


def _gt(gt_id="GT-T1", side="top", category="courtyard_crowding",
        box=None):
    return cal.build_gt_entry(
        gt_id=gt_id, category=category, side=side,
        board_box_mm=[1.0, 2.0, 3.0, 4.0],
        frame_box_pct=box if box is not None else [0.4, 0.4, 0.5, 0.6],
        drc_types=["courtyards_overlap"], cluster_refs=["R4"],
        basis_refs=["synthetic"], description="v3 自检合成用例 GT")


def _flag(fid, box=(0.4, 0.4, 0.5, 0.6), category="courtyard_crowding",
          abstain=False):
    return {"flag_id": fid, "category": category, "confidence": 0.9,
            "abstain": abstain,
            "frame_box_pct": list(box) if box is not None else None}


def _synthetic_cases() -> list:
    """v3 构造性用例（断言不成立即中止；纯内存）。"""
    cases = []

    def _ok(case: str, cond: bool, **detail) -> None:
        if not cond:
            _fail(f"合成用例断言不成立: {case}")
        cases.append(dict({"case": case, "passed": True}, **detail))

    # 1) 一对一去重：三旗标同指一 GT → matches=1、duplicate_reports=2
    r = cal.compare_v3(
        [_flag("F-BIG", (0.35, 0.35, 0.55, 0.65)),
         _flag("F-MID", (0.38, 0.38, 0.52, 0.62)),
         _flag("F-SMALL", (0.42, 0.4, 0.48, 0.6))], [_gt()])
    _ok("one_to_one_dedup_three_flags_one_gt",
        len(r["matches"]) == 1 and len(r["duplicate_reports"]) == 2
        and r["seed_match_rate"] == 0.333333
        and _pairs(r) == [("F-MID", "GT-T1")]
        and all(d["reason"] == "gt_already_matched"
                for d in r["duplicate_reports"]),
        matches=_pairs(r), duplicate_reports=len(r["duplicate_reports"]),
        seed_match_rate=r["seed_match_rate"],
        note="重复报告不计入正确命中分母（seed 按 1/3 计，非 3/3）")

    # 2) 确定性：同分字典序 + 两次调用 canonical 字节一致
    r_flag_tie = cal.compare_v3([_flag("F-B2"), _flag("F-A2")], [_gt()])
    _ok("determinism_flag_id_tiebreak",
        _pairs(r_flag_tie) == [("F-A2", "GT-T1")]
        and [d["flag_id"] for d in r_flag_tie["duplicate_reports"]]
        == ["F-B2"], matches=_pairs(r_flag_tie))
    gts2 = [_gt("GT-A2"), _gt("GT-A1")]
    r_gt_tie = cal.compare_v3([_flag("F-1")], gts2)
    _ok("determinism_gt_id_tiebreak",
        _pairs(r_gt_tie) == [("F-1", "GT-A1")]
        and r_gt_tie["gt_missed_ids"] == ["GT-A2"],
        matches=_pairs(r_gt_tie))
    mixed_flags = [_flag("F-BIG", (0.35, 0.35, 0.55, 0.65)),
                   _flag("F-MID", (0.38, 0.38, 0.52, 0.62)),
                   _flag("F-A", abstain=True),
                   _flag("F-NB", (0.7, 0.7, 0.75, 0.75))]
    mixed_gts = [_gt("GT-T2"), _gt("GT-T1")]
    b1 = hashing.canonical_json_bytes(
        cal.compare_v3(mixed_flags, mixed_gts))
    b2 = hashing.canonical_json_bytes(
        cal.compare_v3(mixed_flags, mixed_gts))
    _ok("determinism_byte_identical_rerun", b1 == b2)

    # 3) 视角：不符 → view_mismatch+不匹配；缺键 → 不设防+partial
    r_vm = cal.compare_v3([_flag("F-V")], [_gt(side="top")],
                          flag_views={"F-V": "bottom"})
    _ok("view_mismatch_blocks_match",
        r_vm["matches"] == []
        and r_vm["view_mismatch"] == [
            {"flag_id": "F-V", "gt_id": "GT-T1", "flag_view": "bottom",
             "gt_side": "top"}]
        and r_vm["reader_unmatched_ids"] == ["F-V"]
        and r_vm["view_check"] == "full",
        view_mismatch=r_vm["view_mismatch"])
    r_pv = cal.compare_v3(
        [_flag("F-V"), _flag("F-W", (0.4, 0.4, 0.45, 0.6))],
        [_gt(side="top")], flag_views={"F-W": "top"})
    _ok("view_unenforced_partial_annotation",
        _pairs(r_pv) == [("F-V", "GT-T1")]
        and r_pv["view_check"] == "partial",
        view_check=r_pv["view_check"],
        note="映射缺键旗标视角不设防（如实 partial，不冒充已检查）")
    r_na = cal.compare_v3([_flag("F-V")], [_gt(side="top")])
    _ok("view_not_applicable_annotation",
        r_na["view_check"] == "not_applicable",
        view_check=r_na["view_check"])
    guard_ok = False
    for bad in ({"F-V": "left"}, {"NOPE": "top"}, "top", {1: "top"}):
        try:
            cal.compare_v3([_flag("F-V")], [_gt()], flag_views=bad)
        except ValueError:
            guard_ok = True
        else:
            guard_ok = False
            break
    _ok("flag_views_fail_closed", guard_ok,
        note="键/值非法 ValueError（fail-closed）")

    # 4) 输出键契约（递归无越界命名）+ abstain 率算术
    r_keys = cal.compare_v3(
        [_flag("F-M"), _flag("F-U", (0.7, 0.7, 0.75, 0.75)),
         _flag("F-NB", None), _flag("F-AB", abstain=True)], [_gt()])
    _assert_no_fp_key(r_keys)
    _ok("output_key_contract",
        r_keys["reader_unmatched_ids"] == ["F-U", "F-NB"]
        and r_keys["reader_unmatched_no_box_ids"] == ["F-NB"]
        and "seed_match_rate" in r_keys and "seed_metric_note" in r_keys
        and all(k in r_keys["abstain"] for k in
                ("abstain_ids", "abstain_count", "reader_flag_count",
                 "abstain_rate", "abstain_rate_definition")),
        note="v3 输出无 reader_false_positive_ids/"
             "reader_precision_vs_seed_gt（含嵌套）")
    r_ab = cal.compare_v3(
        [_flag("F-M"), _flag("F-A1", abstain=True),
         _flag("F-A2", abstain=True),
         _flag("F-U", (0.7, 0.7, 0.8, 0.8)),
         _flag("F-M2", (0.41, 0.41, 0.49, 0.59))], [_gt()])
    _ok("abstain_rate_arithmetic",
        r_ab["abstain"]["abstain_rate"] == 0.4
        and r_ab["abstain"]["abstain_count"] == 2
        and r_ab["abstain"]["reader_flag_count"] == 5
        and r_ab["reader_scored_count"] == 3,
        abstain_rate=r_ab["abstain"]["abstain_rate"])
    return cases


def _round_doc(round_label: str, raw_rel: str, run_rel: str,
               report: dict) -> dict:
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_run_v3_recompute",
        "declared_date": DECLARED_DATE,
        "round_label": round_label,
        "metric_version": cal.METRIC_VERSION_V3,
        "inputs_provenance": {
            "reader_raw": {"path_rel": raw_rel, "sha256": _sha(raw_rel)},
            "ground_truth": {"path_rel": REL_GT, "sha256": _sha(REL_GT)},
            "archived_run": {"path_rel": run_rel, "sha256": _sha(run_rel)},
            "flag_extraction": EXTRACTION_NOTE,
        },
        "flag_views": None,
        "view_check": "not_applicable",
        "view_note": VIEW_NOTE,
        "report": report,
    }


def build() -> dict:
    """全部产物内存构建（纯函数，可重入；同输入 ⇒ 同字节）。"""
    gt_doc = json.loads(_rel(REL_GT).read_text(encoding="utf-8"))
    gt_entries = gt_doc["gt_entries"]
    archived1 = json.loads(_rel(REL_RUN1).read_text(encoding="utf-8"))
    archived2 = json.loads(_rel(REL_RUN2).read_text(encoding="utf-8"))

    flags1 = _extract_reader_flags(REL_RAW1)
    flags2 = _extract_reader_flags(REL_RAW2)

    # 投影对账（fail-closed）：v1/v2 复算与归档 record canonical 一致
    v1_re = cal.compare(flags1, gt_entries)
    if hashing.canonical_json_bytes(v1_re) != \
            hashing.canonical_json_bytes(archived1):
        _fail("v1 投影复算与归档 calibration-run-v1.json 不一致")
    v2_re = cal.compare_v2(flags2, gt_entries)
    if hashing.canonical_json_bytes(v2_re) != \
            hashing.canonical_json_bytes(archived2):
        _fail("v2 投影复算与归档 calibration-run-v2.json 不一致")

    # v3 复算（不含 flag_views；历史轮如实 not_applicable）
    r1_v3 = cal.compare_v3(flags1, gt_entries)
    r2_v3 = cal.compare_v3(flags2, gt_entries)
    for r in (r1_v3, r2_v3):
        _assert_no_fp_key(r)
        if r["containment_min"] != cal.CONTAINMENT_MIN \
                or r["area_ratio_max"] != cal.AREA_RATIO_MAX:
            _fail("v3 复算阈值与声明常量不符")
        if r["view_check"] != "not_applicable":
            _fail("v3 复算 view_check 应为 not_applicable")

    # 阈值沿用断言（与归档轮声明值逐项相等；不允许来自阈值变化的差异）
    if archived1["containment_min"] != cal.CONTAINMENT_MIN \
            or archived2["containment_min"] != cal.CONTAINMENT_MIN \
            or archived2["area_ratio_max"] != cal.AREA_RATIO_MAX:
        _fail("归档轮阈值与声明常量不符（对账前提破坏）")

    # v2↔v3 归档输入对账：数值差异只允许来自一对一/更名
    v2_on_r1 = cal.compare_v2(flags1, gt_entries)
    if _pairs(v2_on_r1) != _pairs(r1_v3):
        _fail("v3 与 v2 对 r1 输入匹配对不一致（差异来源越界）")
    if v2_on_r1["reader_precision_vs_seed_gt"] != r1_v3["seed_match_rate"]:
        _fail("v3 与 v2 对 r1 输入比率不一致（差异来源越界）")
    if _pairs(archived2) != _pairs(r2_v3):
        _fail("v3 与归档 v2 对 r2 输入匹配对不一致（差异来源越界）")
    if archived2["reader_precision_vs_seed_gt"] != \
            r2_v3["seed_match_rate"]:
        _fail("v3 与归档 v2 对 r2 输入比率不一致（差异来源越界）")

    # GT 自比较（视角两态）：top 全匹配 / bottom 全拦
    gflags = [{"flag_id": e["gt_id"], "category": e["category"],
               "confidence": 1.0, "abstain": False,
               "frame_box_pct": e["frame_box_pct"]} for e in gt_entries]
    views_top = {e["gt_id"]: "top" for e in gt_entries}
    views_bottom = {e["gt_id"]: "bottom" for e in gt_entries}
    r_self_top = cal.compare_v3(gflags, gt_entries, flag_views=views_top)
    r_self_bot = cal.compare_v3(gflags, gt_entries,
                                flag_views=views_bottom)
    if r_self_top["gt_matched_count"] != len(gt_entries) \
            or r_self_top["view_check"] != "full" \
            or r_self_top["duplicate_reports"]:
        _fail("GT 自比较 v3（top 视角）非全匹配")
    expected_vm = sum(
        1 for f in gflags for e in gt_entries
        if f["category"] == e["category"])
    if r_self_bot["gt_matched_count"] != 0 \
            or len(r_self_bot["view_mismatch"]) != expected_vm:
        _fail("GT 自比较 v3（bottom 视角）未全拦/视角错配计数不符")

    # CLI 进程内 round-trip（r2 输入）与直接调用 canonical 一致
    cli_report = _cli_roundtrip_v3(flags2, gt_entries)
    if hashing.canonical_json_bytes(cli_report) != \
            hashing.canonical_json_bytes(r2_v3):
        _fail("CLI v3 round-trip 与直接调用不一致")

    syn_cases = _synthetic_cases()

    on_r1 = _round_doc("v3-on-r1-inputs", REL_RAW1, REL_RUN1, r1_v3)
    on_r2 = _round_doc("v3-on-r2-inputs", REL_RAW2, REL_RUN2, r2_v3)

    selfcheck = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_metric_v3_selfcheck",
        "declared_date": DECLARED_DATE,
        "metric_versions": {"v1": cal.METRIC_VERSION,
                            "v2": cal.METRIC_VERSION_V2,
                            "v3": cal.METRIC_VERSION_V3},
        "thresholds": {
            "containment_min": cal.CONTAINMENT_MIN,
            "area_ratio_max": cal.AREA_RATIO_MAX,
            "v3_defaults_equal_declared": (
                cal.compare_v3.__kwdefaults__["containment_min"]
                == cal.CONTAINMENT_MIN
                and cal.compare_v3.__kwdefaults__["area_ratio_max"]
                == cal.AREA_RATIO_MAX),
            "note": "v3 匹配规则参数沿用既有声明常量；本包不引入任何"
                    "新的可调阈值，v3 变化只允许是匹配结构（一对一）"
                    "与输出语义（更名/分列）。",
        },
        "thresholds_unchanged_from_v2": True,
        "inputs": {rel: {"path_rel": rel, "sha256": _sha(rel)}
                   for rel in (REL_GT, REL_RAW1, REL_RAW2,
                               REL_RUN1, REL_RUN2)},
        "extraction_note": EXTRACTION_NOTE,
        "view_note": VIEW_NOTE,
        "synthetic_cases": syn_cases,
        "gt_selfcheck_v3": {
            "rule": "GT 视作 reader flags 与自身比较应全匹配（箱体/类别"
                    "一致性 sanity，非校准指标主张）；视角两态：top 全"
                    "匹配、bottom 全拦（视角错配如实计数）",
            "gt_count": len(gt_entries),
            "matched_with_top_views": r_self_top["gt_matched_count"],
            "view_check_with_top_views": r_self_top["view_check"],
            "duplicate_reports_with_top_views":
                len(r_self_top["duplicate_reports"]),
            "matched_with_bottom_views": r_self_bot["gt_matched_count"],
            "view_mismatch_with_bottom_views":
                len(r_self_bot["view_mismatch"]),
        },
        "cli_roundtrip_v3": {
            "input": "r2 输入（五键投影 flags + ground-truth-v1.json）",
            "mode": "runpy __main__ 进程内 stdin→stdout（零子进程）",
            "canonical_equal_to_direct": True,
        },
        "archived_inputs_recompute": {
            "r1_v1_archived": {
                "metric_version": archived1["metric_version"],
                "matches": [f"{m['flag_id']}->{m['gt_id']}"
                            for m in archived1["matches"]],
                "gt_recall": archived1["gt_recall"],
                "reader_precision_vs_seed_gt":
                    archived1["reader_precision_vs_seed_gt"],
            },
            "r1_v2_on_same_inputs": {
                "metric_version": cal.METRIC_VERSION_V2,
                "matches": [f"{m['flag_id']}->{m['gt_id']}"
                            for m in v2_on_r1["matches"]],
                "gt_recall": v2_on_r1["gt_recall"],
                "reader_precision_vs_seed_gt":
                    v2_on_r1["reader_precision_vs_seed_gt"],
            },
            "r1_v3": {
                "metric_version": cal.METRIC_VERSION_V3,
                "matches": [f"{m['flag_id']}->{m['gt_id']}"
                            for m in r1_v3["matches"]],
                "gt_recall": r1_v3["gt_recall"],
                "seed_match_rate": r1_v3["seed_match_rate"],
                "abstain_rate": r1_v3["abstain"]["abstain_rate"],
                "duplicate_reports": len(r1_v3["duplicate_reports"]),
            },
            "r2_v2_archived": {
                "metric_version": archived2["metric_version"],
                "matches": [f"{m['flag_id']}->{m['gt_id']}"
                            for m in archived2["matches"]],
                "gt_recall": archived2["gt_recall"],
                "reader_precision_vs_seed_gt":
                    archived2["reader_precision_vs_seed_gt"],
            },
            "r2_v3": {
                "metric_version": cal.METRIC_VERSION_V3,
                "matches": [f"{m['flag_id']}->{m['gt_id']}"
                            for m in r2_v3["matches"]],
                "gt_recall": r2_v3["gt_recall"],
                "seed_match_rate": r2_v3["seed_match_rate"],
                "abstain_rate": r2_v3["abstain"]["abstain_rate"],
                "duplicate_reports": len(r2_v3["duplicate_reports"]),
            },
            "delta_note": (
                "r1：归档 v1 首测同 GT 重复命中（F-012 与 F-014 同命中 "
                "GT-REVC-P1-L1SHORT，其中 F-014 为整板大框、面积比 "
                "441×）→ v3 只保留 F-012（F-014 由 v2 已声明的面积比"
                "条件拒绝、一对一结构使重复命中不复存在），比率 "
                "0.2→0.1 的变化=去重语义，非阈值变化；v3 与 v2 对同"
                "输入的匹配对/比率逐项相等。r2：v3 与归档 v2 数值全等"
                "（1 匹配、recall 0.25、比率 1/7），差异仅键名/结构。"
                "两轮阈值与归档声明值逐项相等，复算差异不允许且不来自"
                "阈值变化。"),
        },
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本自证与两轮复算不进"
            "任何 gate 谓词、不翻转 critic_calibration_in_range（恒 "
            "False 维持 fail-closed）。",
            "v1/v2 度量与产物（calibration-run-v1/v2.json 等）原样"
            "保留：版本字段区分，不回写、不重算归档件。",
            "seed 匹配率命名约束：禁称 precision/FPR（见 "
            "calibration-process-v2 §4）；同板不同渲染不是独立板。",
            "达标线仍 proposal_only 待人工（纠偏词 P3-B 重申）；本包"
            "不执行新 reader 盲读轮。",
        ],
    }
    return {"on_r1": on_r1, "on_r2": on_r2, "selfcheck": selfcheck}


def main() -> None:
    for rel, want in FROZEN_SHA256.items():
        p = _rel(rel)
        if not p.is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")
        got = hashing.sha256_file(str(p))
        if got != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {got[:8]}…≠{want[:8]}…")
    if not _rel(REL_MD).is_file():
        _fail(f"输入缺失（fail-closed）: {REL_MD}")

    # 防覆写：目标三件必须尚不存在
    for t in (OUT_ON_R1, OUT_ON_R2, OUT_SELF):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    # 同参重建逐字节一致（byte-exact 可重跑前提自证）
    docs1 = build()
    docs2 = build()
    ser = {name: hashing.canonical_json_bytes(doc)
           for name, doc in docs1.items()}
    for name, doc in docs2.items():
        if hashing.canonical_json_bytes(doc) != ser[name]:
            _fail(f"同参重建不一致（byte-exact 破坏）: {name}")

    for name, path in (("on_r1", OUT_ON_R1), ("on_r2", OUT_ON_R2),
                       ("selfcheck", OUT_SELF)):
        data = _write_canonical(path, docs1[name])
        if path.read_bytes() != data:
            _fail(f"回读不一致: {path.name}")

    print(f"[s24-cal3] 投影对账：v1/v2 复算与归档 record canonical 一致"
          f"；自检合成用例 {len(docs1['selfcheck']['synthetic_cases'])}"
          f" 条全过")
    print(f"[s24-cal3] r1 复算 matches="
          f"{docs1['on_r1']['report']['matches']} recall="
          f"{docs1['on_r1']['report']['gt_recall']} seed="
          f"{docs1['on_r1']['report']['seed_match_rate']}")
    print(f"[s24-cal3] r2 复算 matches="
          f"{docs1['on_r2']['report']['matches']} recall="
          f"{docs1['on_r2']['report']['gt_recall']} seed="
          f"{docs1['on_r2']['report']['seed_match_rate']}")
    for rel in (REL_MD, "out/v3-tl2/calibration/"
                "calibration-run-v3-on-r1-inputs.json",
                "out/v3-tl2/calibration/"
                "calibration-run-v3-on-r2-inputs.json",
                "out/v3-tl2/calibration/"
                "calibration-metric-v3-selfcheck.json"):
        print(f"[s24-cal3] sha256[:8] {rel.split('/')[-1]} = "
              f"{_sha(rel)[:8]}")
    print("[s24-cal3] 校准度量 v3 复算落盘完成（历史轮零覆写；"
          "flag_views 未注入、view_check=not_applicable；不是门）")


if __name__ == "__main__":
    main()
