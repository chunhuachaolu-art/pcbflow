#!/usr/bin/env python
"""S20-T3：校准度量 v2 正式化落盘（out/v3-tl2/calibration/）。

库侧 pcbflow/calibration.py（compare_v2 + AREA_RATIO_MAX）纯函数构造；
本脚本只做磁盘实读对账 + canonical 落盘（防覆写）：

- calibration-metric-v2-selfcheck.json：v2 比较器合成用例自证
  （整板大框 F-014 型被拒/正常邻域框通过/面积比边界 10.0 恰过、
  12.0 拒/containment 边界 0.5 恰过、低于 0.5 拒）+ GT 自比较
  （GT 视作 reader flags 全匹配、面积比全 1.0）+ v1 对归档首测
  输入复算与已归档 record canonical 一致；
- calibration-domain-v2.json：域 manifest v2（GT 不变绑定 + metric
  v2 声明；v1 manifest/产物原样保留；面积比上限=proposal_only
  待人工；本包不执行新 reader 轮）。

evidence 磁盘实读 fail-closed；日期=声明常量 2026-09-05；无
wall-clock/主机路径（路径一律仓库相对 POSIX）。v1 产物字节不动。

用法：python scripts/s20_calibration_v2_formalize.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"
DECLARED_DATE = "2026-09-05"

READER_KEYS = ("flag_id", "category", "confidence", "abstain",
               "frame_box_pct")


def _fail(msg: str) -> None:
    print(f"[s20-cal2] FAIL: {msg}")
    sys.exit(1)


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(REPO.joinpath(*rel.split("/"))))


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _reader_flags_from_raw(raw_path: Path) -> list:
    """归档首测 reader 原文 → 比较器五键投影（内容零改动）。"""
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    flags = []
    for board in raw["per_board"]:
        for f in board["flags"]:
            flags.append({k: f[k] for k in READER_KEYS})
    return flags


def main() -> None:
    gt_rel = "out/v3-tl2/calibration/ground-truth-v1.json"
    raw_rel = "out/v3-tl2/calibration/reader-raw-cal-v1.txt"
    run1_rel = "out/v3-tl2/calibration/calibration-run-v1.json"
    mf1_rel = "out/v3-tl2/calibration/calibration-domain-v1.json"
    process_rel = "out/v3-tl2/calibration/calibration-process-v1.md"
    for rel in (gt_rel, raw_rel, run1_rel, mf1_rel, process_rel):
        if not REPO.joinpath(*rel.split("/")).is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")

    gt_doc = json.loads(REPO.joinpath(*gt_rel.split("/"))
                        .read_text(encoding="utf-8"))
    gt_entries = gt_doc["gt_entries"]
    archived = json.loads(REPO.joinpath(*run1_rel.split("/"))
                          .read_text(encoding="utf-8"))
    mf1 = json.loads(REPO.joinpath(*mf1_rel.split("/"))
                     .read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # 自证 1：v1 复算与已归档 record canonical 一致（v1 路径零回归）
    # ------------------------------------------------------------------
    flags = _reader_flags_from_raw(
        REPO.joinpath(*raw_rel.split("/")))
    v1_recomputed = cal.compare(flags, gt_entries)
    v1_identical = (hashing.canonical_json_bytes(v1_recomputed)
                    == hashing.canonical_json_bytes(archived))
    if not v1_identical:
        _fail("v1 复算与归档 record 不一致（v1 路径被扰动；拒绝落盘）")

    # ------------------------------------------------------------------
    # 自证 2：v2 合成用例（精确二进制小数构造，无浮点边界模糊）
    # GT 框 [0.5,0.5,0.625,0.625]：宽=高=0.125，面积=0.015625（精确）
    # ------------------------------------------------------------------
    synth_gt = [{
        "gt_id": "GT-SYNTH-1", "category": "courtyard_crowding",
        "side": "top", "board_box_mm": [1.0, 1.0, 2.0, 2.0],
        "frame_box_pct": [0.5, 0.5, 0.625, 0.625],
        "drc_types": ["courtyards_overlap"], "cluster_refs": ["SY"],
        "basis_refs": ["synthetic"], "description": "合成边界用例",
    }]

    def _flag(fid, box):
        return {"flag_id": fid, "category": "courtyard_crowding",
                "confidence": 0.9, "abstain": False, "frame_box_pct": box}

    def _run2(fl):
        return cal.compare_v2(fl, synth_gt)

    cases = []

    # 整板大框（F-014 型）：containment=1.0 但面积比 12.0 → 拒
    r = _run2([_flag("SY-WHOLE", [0.3125, 0.375, 0.8125, 0.75])])
    cases.append({
        "case": "whole_board_style_frame_ratio_12_rejected",
        "reader_box": [0.3125, 0.375, 0.8125, 0.75],
        "containment": 1.0, "area_ratio": 12.0,
        "v2_matched": bool(r["matches"]),
        "v2_ratio_rejected": r["reader_ratio_rejected_ids"] == ["SY-WHOLE"],
        "v2_false_positive": r["reader_false_positive_ids"] == ["SY-WHOLE"],
    })

    # 面积比恰=10.0（0.5×0.3125 / 0.125×0.125）：过（≤ 语义）
    r = _run2([_flag("SY-EXACT10", [0.3125, 0.40625, 0.8125, 0.71875])])
    cases.append({
        "case": "area_ratio_exactly_max_accepted",
        "reader_box": [0.3125, 0.40625, 0.8125, 0.71875],
        "containment": 1.0, "area_ratio": 10.0,
        "v2_matched": (r["matches"]
                       and r["matches"][0]["area_ratio"] == 10.0),
    })

    # 正常邻域框（1.8496×）：过
    r = _run2([_flag("SY-NB", [0.48, 0.48, 0.65, 0.65])])
    cases.append({
        "case": "normal_neighborhood_box_accepted",
        "reader_box": [0.48, 0.48, 0.65, 0.65],
        "containment": 1.0, "area_ratio": 1.8496,
        "v2_matched": bool(r["matches"]),
    })

    # containment 恰=0.5（面积比 1.0）：过（≥ 语义，与 v1 一致）
    r = _run2([_flag("SY-C05", [0.4375, 0.5, 0.5625, 0.625])])
    cases.append({
        "case": "containment_exactly_min_accepted",
        "reader_box": [0.4375, 0.5, 0.5625, 0.625],
        "containment": 0.5, "area_ratio": 1.0,
        "v2_matched": (r["matches"]
                       and r["matches"][0]["containment"] == 0.5),
    })

    # containment=0.4（<0.5）：拒（v1 同规则）
    r = _run2([_flag("SY-C04", [0.4375, 0.5, 0.55, 0.625])])
    cases.append({
        "case": "containment_below_min_rejected",
        "reader_box": [0.4375, 0.5, 0.55, 0.625],
        "containment": 0.4, "area_ratio": 1.0,
        "v2_matched": False,
        "v2_false_positive": r["reader_false_positive_ids"] == ["SY-C04"],
    })

    for c in cases:
        if not c["v2_matched"] and not c.get("v2_false_positive"):
            _fail(f"合成用例断言不成立: {c['case']}")

    # ------------------------------------------------------------------
    # 自证 3：归档首测输入下的 v1/v2 差异（F-014 型整板框）
    # ------------------------------------------------------------------
    r2_arch = cal.compare_v2(flags, gt_entries)
    f014 = next((x for x in r2_arch["reader_ratio_rejected_detail"]
                 if x["flag_id"] == "F-014"), None)
    if f014 is None or "F-012" not in r2_arch["reader_matched_ids"]:
        _fail("归档输入 v2 复算不符合预期（F-014 拒/F-012 过）")

    # 自证 4：GT 自比较（GT 视作 reader flags）v2 全匹配、面积比全 1.0
    gflags = [{"flag_id": e["gt_id"], "category": e["category"],
               "confidence": 1.0, "abstain": False,
               "frame_box_pct": e["frame_box_pct"]}
              for e in gt_entries]
    rself = cal.compare_v2(gflags, gt_entries)
    if rself["gt_matched_count"] != len(gt_entries) \
            or rself["reader_false_positive_ids"]:
        _fail("GT 自比较 v2 非全匹配")
    if any(m["area_ratio"] != 1.0 for m in rself["matches"]):
        _fail("GT 自比较面积比非 1.0")

    selfcheck = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_metric_v2_selfcheck",
        "declared_date": DECLARED_DATE,
        "metric_versions": {"v1": cal.METRIC_VERSION,
                            "v2": cal.METRIC_VERSION_V2},
        "area_ratio_max": cal.AREA_RATIO_MAX,
        "area_ratio_max_rationale": cal.AREA_RATIO_MAX_RATIONALE,
        "inputs": {
            "ground_truth": {"path_rel": gt_rel, "sha256": _sha(gt_rel)},
            "reader_raw_cal_v1": {"path_rel": raw_rel,
                                  "sha256": _sha(raw_rel)},
            "archived_run_v1": {"path_rel": run1_rel,
                                "sha256": _sha(run1_rel)},
        },
        "v1_recompute": {
            "note": "v1 比较器对归档首测输入（五键投影）复算；判据=与"
                    "已归档 record 的 canonical 字节一致（归档文件为 "
                    "pretty-print 落盘，非 canonical 字节口径，故以 "
                    "canonical 对账为准）。",
            "record_canonical_equal": v1_identical,
            "recall": v1_recomputed["gt_recall"],
            "precision": v1_recomputed["reader_precision_vs_seed_gt"],
        },
        "v1_vs_v2_on_archived_inputs": {
            "v1": {"matches": [m["flag_id"] for m in
                               archived["matches"]],
                   "recall": archived["gt_recall"],
                   "precision": archived["reader_precision_vs_seed_gt"]},
            "v2": {"matches": [m["flag_id"] for m in r2_arch["matches"]],
                   "recall": r2_arch["gt_recall"],
                   "precision": r2_arch["reader_precision_vs_seed_gt"],
                   "ratio_rejected": r2_arch["reader_ratio_rejected_ids"]},
            "note": "差异=整板大框 F-014（containment 1.0、面积比 "
                    "441.227947）在 v2 被面积比上限拒绝、如实计为未匹配"
                    "（v1 产物不改写，首测 record 绑定 v1 不动）。",
        },
        "f014_type_detail": f014,
        "synthetic_cases": cases,
        "gt_selfcheck_v2": {
            "rule": "GT 视作 reader flags 与自身比较应全匹配（箱体/类别"
                    "一致性 sanity，非校准指标主张）",
            "gt_count": len(gt_entries),
            "gt_matched_count": rself["gt_matched_count"],
            "reader_false_positive_ids": rself["reader_false_positive_ids"],
            "area_ratios": [m["area_ratio"] for m in rself["matches"]],
        },
        "is_gate": False,
        "notes": [
            "比较器是 advisory 侧分析，不是门：本自证不翻转 "
            "critic_calibration_in_range（谓词语义不变）；面积比上限"
            "属 proposal_only，正式采纳须人工批准。",
            "本包不执行新 reader 盲读轮：v2 下尚无校准轮结果，无任何"
            "达标主张。",
        ],
    }

    # ------------------------------------------------------------------
    # manifest v2（GT 不变 + metric v2 声明；v1 原样保留）
    # ------------------------------------------------------------------
    selfcheck_path = CAL / "calibration-metric-v2-selfcheck.json"
    mf2_path = CAL / "calibration-domain-v2.json"
    for t in (selfcheck_path, mf2_path):
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    selfcheck_sha = _write_canonical(selfcheck_path, selfcheck)
    print(f"[s20-cal2] 自证：calibration-metric-v2-selfcheck.json "
          f"sha256={selfcheck_sha[:16]}…（v1 复算 canonical 一致="
          f"{v1_identical}，合成用例 {len(cases)} 条全过）")

    # provenance 沿用 v1 manifest 并对盘上实文件复验（fail-closed）
    for name, src in mf1["provenance"].items():
        if _sha(src["path_rel"]) != src["sha256"]:
            _fail(f"provenance 复验失败: {name}")
    board = mf1["board"]
    if _sha(board["path_rel"]) != board["sha256"]:
        _fail("board hash 复验失败")

    manifest_v2 = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_domain",
        "domain_id": "calibration-domain-v2",
        "domain_version": "2.0",
        "status": "process_formalized_threshold_proposal_pending",
        "declared_date": DECLARED_DATE,
        "board": board,
        "ground_truth": {
            "entry_count": mf1["ground_truth"]["entry_count"],
            "gt_ids": mf1["ground_truth"]["gt_ids"],
            "categories": mf1["ground_truth"]["categories"],
            "path_rel": gt_rel,
            "sha256": _sha(gt_rel),
            "frozen": True,
            "note": "GT 与 v1 逐字节同一文件（ground-truth-v1.json），"
                    "冻结不动；扩样走新版本文件（见 process 文档 §3）。",
        },
        "metric": {
            "metric_version": cal.METRIC_VERSION_V2,
            "containment_min": cal.CONTAINMENT_MIN,
            "area_ratio_max": cal.AREA_RATIO_MAX,
            "area_ratio_max_rationale": cal.AREA_RATIO_MAX_RATIONALE,
            "is_gate": False,
            "definition": (
                "匹配=abstain=False 且类别相等且 containment(读者框∩GT框"
                "/GT框面积) ≥ containment_min 且 读者框面积/GT框面积 ≤ "
                "area_ratio_max（同量级邻域上限，依据见 rationale 与 "
                "process 文档 §4）；abstain 单列不参与匹配。先写死后跑，"
                "阈值不后调。"),
            "threshold_adoption": "proposal_only_pending_human_approval",
            "v1_preserved": {
                "metric_version": cal.METRIC_VERSION,
                "manifest": {"path_rel": mf1_rel, "sha256": _sha(mf1_rel)},
                "run": {"path_rel": run1_rel, "sha256": _sha(run1_rel)},
                "note": "v1 度量与其产物原样保留（版本字段区分，不回写"
                        "不重算归档件）。",
            },
            "note": "比较器输出为 advisory 侧分析；不进任何 gate 谓词，"
                    "不翻转 critic_calibration_in_range（谓词语义不变，"
                    "恒 False 维持 fail-closed）。面积比上限取值依据见 "
                    "AREA_RATIO_MAX_RATIONALE（第一性原理先写死，非结果"
                    "反推）。",
        },
        "conversion_rule": mf1["conversion_rule"],
        "split_declaration": mf1["split_declaration"],
        "provenance": mf1["provenance"],
        "process_doc": {
            "path_rel": process_rel,
            "sha256": _sha(process_rel),
            "note": "校准轮运行规程/GT 冻结扩样规则/度量版本化纪律/"
                    "达标阈值提案（proposal_only 待人工）。",
        },
        "selfcheck": {
            "path_rel": "out/v3-tl2/calibration/"
                        "calibration-metric-v2-selfcheck.json",
            "sha256": selfcheck_sha,
        },
        "renders_ref": {
            "path_rel": mf1_rel,
            "key": "renders",
            "note": "渲染沿 v1 manifest（同批渲染、hash 已在 v1 绑定；"
                    "v2 不复制不重渲染）。",
        },
        "usage_policy": (
            "标注 pipeline 侧、不混入 reader 视野；盲读轮由主智能体按 "
            "process 文档 §2 规程另行派发（本包未执行）；面积比上限"
            " proposal 采纳前，critic_calibration_in_range 恒 False、"
            "flags=[] 一律 blocked（fail-closed 语义零改动）。"),
        "notes": [
            "v2=流程正式化版本：GT 不变 + metric v2 声明 + 运行规程在案"
            "（calibration-process-v1.md）；v1 manifest 与首测 record "
            "原样保留。",
            "整板大框度量观察（F-014 案例，面积比 441×）由 metric v2 "
            "面积比上限修复；v1→v2 差异如实记录在 selfcheck。",
        ],
    }
    mf2_sha = _write_canonical(mf2_path, manifest_v2)
    print(f"[s20-cal2] manifest：calibration-domain-v2.json "
          f"sha256={mf2_sha[:16]}…（GT 绑定={manifest_v2['ground_truth']['sha256'][:16]}…，"
          f"metric={cal.METRIC_VERSION_V2}，proposal_only 待人工）")
    print("[s20-cal2] 度量 v2 正式化完成（未执行新 reader 轮；v1 字节不动）")


if __name__ == "__main__":
    main()
