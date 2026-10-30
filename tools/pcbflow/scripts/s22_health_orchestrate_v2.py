"""S22 TL-6 健康度重投影 v2 编排（编排侧脚本）。

职责（对照 S16 首投影，机制同构、口径与谓词不变）：

  health-projection-v2.json        v2 全量投影（四指标活算更新+readiness
                                   逐格重评+BL 重评+语料分母转换覆盖更新）
  health-projection-gate-v2.json   v2 健康度 gate-record（四机器谓词不变；
                                   内嵌 TL-6 出口门 blocked 如实）
  projection-diff-v1-to-v2.json    逐格差异表（v1 冻结件 → v2，path 级
                                   before/after；纯函数 build_projection_diff）

红线：既有 out/ 与 datasets/ 只读（v1 冻结件 hash 先验断言，不符即中止）；
零子进程；无 wall-clock（日期=人工会话声明常量）；canonical JSON byte-exact；
本脚本收尾自校验=同参重建逐字节比对。v1 三冻结件
（health-projection.json / -gate.json / .sha256）一字不动、版本化不覆写。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing, health_projection as hp  # noqa: E402
from pcbflow import queue as queue_mod  # noqa: E402

S22_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）

TL6_DIR = REPO / "out" / "v3-tl6"
V1_PROJECTION = "out/v3-tl6/health-projection.json"
V2_PROJECTION = "out/v3-tl6/health-projection-v2.json"

# v1 冻结件先验锚（S16 入账 98677d11；不配即中止——防覆写 fail-closed）
FROZEN_V1_SHA256 = ("98677d116a5d9f0b024b81e758051629f23e8b79c1b2d026aaa"
                    "534cd45092d66")

RUN_R1 = "out/v3-tl2/critic-runs/run-r1"
RUN_R2 = "out/v3-tl2/critic-runs/run-r2"
CAL = "out/v3-tl2/calibration"

# 证据清单（repo 相对 POSIX 路径）——只读；sha256 全部盘上实测
EVIDENCE_PATHS = {
    "module": "pcbflow/health_projection.py",
    "tl0_gate_2l": "out/v3-tl0/gate-record-smoke-2l.json",
    "tl0_gate_4l": "out/v3-tl0/gate-record-smoke-4l.json",
    "tl1_gate": "out/v3-tl1/gate-record.json",
    "tl2_record_r1": f"{RUN_R1}/critic-run-record-CR-run-r1.json",
    "tl2_ledger_r1": f"{RUN_R1}/queue-event-ledger.jsonl",
    "tl2_raw_flags_r1": f"{RUN_R1}/raw-flags.json",
    "tl2_apr5": "out/v3-approvals/disposition-APR-0005-critic-duty-level.json",
    "tl2_apr7": "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json",
    "tl2_record_r2": f"{RUN_R2}/critic-run-record-CR-run-r2.json",
    "tl2_ledger_r2": f"{RUN_R2}/queue-event-ledger.jsonl",
    "tl2_raw_flags_r2": f"{RUN_R2}/raw-flags.json",
    "tl2_apr10": "out/v3-approvals/disposition-APR-0010-item-run-r2-disposition.json",
    "cal_run_v1": f"{CAL}/calibration-run-v1.json",
    "cal_run_v2": f"{CAL}/calibration-run-v2.json",
    "cal_domain_v2": f"{CAL}/calibration-domain-v2.json",
    "cal_process_v1": f"{CAL}/calibration-process-v1.md",
    "tl3_gate": "out/v3-tl3/gate-record.json",
    "tl3_coverage": "out/v3-tl3/physics-coverage.json",
    "tl3_report": "out/v3-tl3/physics-report.json",
    "tl4_gate_2l": "out/v3-tl4/gate-record-tl4-v2-smoke-2l.json",
    "tl4_gate_4l": "out/v3-tl4/gate-record-tl4-v2-smoke-4l.json",
    "tl4_patch_2l": "out/v3-tl4/proposal-patch-smoke-2l.json",
    "tl4_patch_4l": "out/v3-tl4/proposal-patch-smoke-4l.json",
    "tl4_apr4": "out/v3-approvals/disposition-APR-0004-tl4-adoption-disposition.json",
    "tl5_gate_v4": "out/v3-tl5/gate-record-tl5-v4.json",
    "manifest_pcbbm": "out/v3-tl5/dataset-manifest-pcbbenchmarks-r1-v3.json",
    "manifest_pcbench": "out/v3-tl5/dataset-manifest-pcbench-r1-v3.json",
    "manifest_demos": "out/v3-tl5/dataset-manifest-kicad-demos-r1.json",
    "manifest_demos_r2": "out/v3-tl5/dataset-manifest-kicad-demos-r2.json",
    "k9_batch_summary": "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json",
    "arc1": "out/v3-archive/disposition-ARC-0001-td7-line-archive.json",
    "arc2": "out/v3-archive/disposition-ARC-0002-toolchain-lock-proposal.json",
    "arc3": "out/v3-archive/disposition-ARC-0003-d20-batch-gate-semantics.json",
    "arc4": "out/v3-archive/disposition-ARC-0004-freerouting-v241-upgrade.json",
    "td7_gate_frozen": "out/v3-td7/gate-record-td7.json",
}


def rel_repo(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def measure_hashes() -> dict:
    return {k: hashing.sha256_file(str(REPO / p))
            for k, p in EVIDENCE_PATHS.items()}


def parse_queue_events(path: Path) -> list:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def predicate_map(gate_record: dict) -> dict:
    return {p["id"]: p["value"]
            for p in gate_record["gate_record"]["required_predicates"]}


def count_flags(raw_flags: dict) -> tuple:
    board_counts: dict = {}
    abstain = 0
    total = 0
    for board in raw_flags.get("per_board", []):
        pid = board.get("profile_id")
        n = len(board.get("flags", []))
        board_counts[pid] = board_counts.get(pid, 0) + n
        for f in board.get("flags", []):
            total += 1
            if f.get("abstain"):
                abstain += 1
    return total, abstain, board_counts


def apr_supports_flags(apr: dict, expected_id: str) -> bool:
    """fail-closed：kind=accept + critic_flags_advisory 在 fact_refs + id 对上
    才算人工支持旗标登记；缺任一 → False（不虚构支持）。"""
    return (apr.get("kind") == "accept"
            and "critic_flags_advisory" in (apr.get("fact_refs") or [])
            and apr.get("disposition_id") == expected_id)


def calibration_observation_block(key: str, rec: dict,
                                  hashes: dict) -> dict:
    path = EVIDENCE_PATHS[key]
    return {
        "source_id": rec.get("metric_version", key),
        "path": path,
        "sha256": hashes[key],
        "sha256_8": hashes[key][:8],
        "metric_version": rec.get("metric_version"),
        "gt_count": rec.get("gt_count"),
        "gt_recall": rec.get("gt_recall"),
        "reader_precision_vs_seed_gt": rec.get("reader_precision_vs_seed_gt"),
        "reader_flag_count": rec.get("reader_flag_count"),
        "reader_scored_count": rec.get("reader_scored_count"),
        "reader_abstain_count": len(rec.get("reader_abstain_ids") or []),
        "advisory_note": ("校准域种子实测（advisory 侧比较器输出，非门、"
                          "不翻转任何谓词）"),
    }


def reference_batch_block(bs: dict, hashes: dict) -> dict:
    up = bs.get("upstream_reference_state", {})
    unstable = up.get("dual_severity_unstable_boards") or []
    unavailable = up.get("drc_unavailable_boards") or []
    conn = up.get("connectivity_violation_boards") or []
    return {
        "batch_id": bs.get("batch_id"),
        "path": EVIDENCE_PATHS["k9_batch_summary"],
        "sha256": hashes["k9_batch_summary"],
        "sha256_8": hashes["k9_batch_summary"][:8],
        "boards_consistency_pass":
            bs.get("reference_check", {}).get("consistency_distribution",
                                              {}).get("pass"),
        "boards_total": bs.get("denominator", {}).get("boards"),
        "all_consistency_pass":
            bs.get("reference_check", {}).get("all_consistency_pass"),
        "d19b_dual_severity_unstable_boards": len(unstable),
        "drc_unavailable_boards": len(unavailable),
        "connectivity_violation_boards": len(conn),
        "scope_note": ("k9 转换域参考态回归证据层（S21）：验证「转换复现原始板"
                       "参考态」（计数对账+byte-exact 重放+hash 链绑定），"
                       "不是 autotune 不回退执行面——不改变本指标分母/状态，"
                       "不入 TL-5 门分母（37 profile 不变）、BL 清单语义不变"),
        "honest_caveats_note": ("参考态实况如实登记：kicad-cli 双 severity "
                                "error 分类跨运行不稳=%d 板（D19(b) 类，非"
                                "转换缺陷）、DRC baseline 不可得=%d 板"
                                "（kicad-cli 拒加载 20260624+ 格式，exit=3，"
                                "不虚构计数）、连通类违例=%d 板（参考态自带，"
                                "不进 consistency 判定）"
                                % (len(unstable), len(unavailable), len(conn))),
    }


def conversion_coverage_block(hashes: dict) -> dict:
    return {
        "boards_total": 100,
        "s16_baseline_coverage": 83,
        "basis": ("pcbbm 2 + pcbench 81（S10 r1 转换域）+ kicad-demos 17"
                  "（S18 k9 扩展）=100 板；S18 入账口径"),
        "k9_r2_manifest": {
            "path": EVIDENCE_PATHS["manifest_demos_r2"],
            "sha256": hashes["manifest_demos_r2"],
            "sha256_8": hashes["manifest_demos_r2"][:8],
        },
        "note": ("TL-5 门分母（37 profile）与 BL 清单语义不变；r2 manifest "
                 "为转换域扩展证据，不入门分母、不回填 r1"),
    }


def build_everything(hashes: dict):
    """同参确定性构建（byte-exact 重跑验证的基础）。"""
    # ---- 解析既有产物（只读） ------------------------------------------
    ledger_r1 = {"path": EVIDENCE_PATHS["tl2_ledger_r1"],
                 "sha256": hashes["tl2_ledger_r1"],
                 "events": parse_queue_events(
                     REPO / EVIDENCE_PATHS["tl2_ledger_r1"])}
    ledger_r2 = {"path": EVIDENCE_PATHS["tl2_ledger_r2"],
                 "sha256": hashes["tl2_ledger_r2"],
                 "events": parse_queue_events(
                     REPO / EVIDENCE_PATHS["tl2_ledger_r2"])}
    record_r1 = read_json(REPO / EVIDENCE_PATHS["tl2_record_r1"])
    record_r2 = read_json(REPO / EVIDENCE_PATHS["tl2_record_r2"])
    raw_flags_r1 = read_json(REPO / EVIDENCE_PATHS["tl2_raw_flags_r1"])
    raw_flags_r2 = read_json(REPO / EVIDENCE_PATHS["tl2_raw_flags_r2"])
    apr7 = read_json(REPO / EVIDENCE_PATHS["tl2_apr7"])
    apr10 = read_json(REPO / EVIDENCE_PATHS["tl2_apr10"])
    cal_v1 = read_json(REPO / EVIDENCE_PATHS["cal_run_v1"])
    cal_v2 = read_json(REPO / EVIDENCE_PATHS["cal_run_v2"])
    tl3_cov = read_json(REPO / EVIDENCE_PATHS["tl3_coverage"])
    tl3_report = read_json(REPO / EVIDENCE_PATHS["tl3_report"])
    tl4_gate_2l = read_json(REPO / EVIDENCE_PATHS["tl4_gate_2l"])
    tl4_gate_4l = read_json(REPO / EVIDENCE_PATHS["tl4_gate_4l"])
    patch_2l = read_json(REPO / EVIDENCE_PATHS["tl4_patch_2l"])
    patch_4l = read_json(REPO / EVIDENCE_PATHS["tl4_patch_4l"])
    apr4 = read_json(REPO / EVIDENCE_PATHS["tl4_apr4"])
    manifest_pcbbm = read_json(REPO / EVIDENCE_PATHS["manifest_pcbbm"])
    manifest_pcbench = read_json(REPO / EVIDENCE_PATHS["manifest_pcbench"])
    manifest_demos = read_json(REPO / EVIDENCE_PATHS["manifest_demos"])
    k9_batch = read_json(REPO / EVIDENCE_PATHS["k9_batch_summary"])

    # 编排侧 fail-closed 守卫：两账本验链 + enqueue critic_ref 与盘上实测
    # record hash 全等（绑定信任先于投影）。
    for l in (ledger_r1, ledger_r2):
        errs = queue_mod.verify_chain(l["events"])
        if errs:
            raise SystemExit(f"编排中止：账本链校验失败 {l['path']} {errs}")
    for l, rec_key in ((ledger_r1, "tl2_record_r1"),
                       (ledger_r2, "tl2_record_r2")):
        for ev in l["events"]:
            if ev.get("event") == "enqueue" \
                    and ev.get("critic_ref") != hashes[rec_key]:
                raise SystemExit(
                    f"编排中止：{l['path']} enqueue critic_ref 与实测 "
                    f"record hash 不符")

    # ---- 指标一：人工队列（多账本合取） ---------------------------------
    queue_metric = hp.project_manual_queue_multi(
        [ledger_r1, ledger_r2],
        baseline=1,
        baseline_basis=("前一 revision（v3-tl6-r1，冻结件 98677d11…）"
                        "manual_queue_length=1——首投影值作基线"))

    # ---- 指标二：Critic 一致率（装配侧）+ 校准侧实测分列 ----------------
    f1, a1, b1 = count_flags(raw_flags_r1)
    f2, a2, b2 = count_flags(raw_flags_r2)
    critic_runs = [
        {"run_id": record_r1["critic_run_id"],
         "critic_status": record_r1["critic_status"],
         "input_hashes_match": record_r1["input_hashes_match"],
         "critic_ref": hashes["tl2_record_r1"],
         "in_calibrated_range":
             record_r1["calibration"]["in_calibrated_range"],
         "flags_total": f1, "abstain_count": a1,
         "board_flag_counts": b1,
         "human_supports_flags": apr_supports_flags(apr7, "APR-0007")},
        {"run_id": record_r2["critic_run_id"],
         "critic_status": record_r2["critic_status"],
         "input_hashes_match": record_r2["input_hashes_match"],
         "critic_ref": hashes["tl2_record_r2"],
         "in_calibrated_range":
             record_r2["calibration"]["in_calibrated_range"],
         "flags_total": f2, "abstain_count": a2,
         "board_flag_counts": b2,
         "human_supports_flags": apr_supports_flags(apr10, "APR-0010")},
    ]
    record_evidence = [
        {"run_id": record_r1["critic_run_id"],
         "path": EVIDENCE_PATHS["tl2_record_r1"],
         "sha256": hashes["tl2_record_r1"]},
        {"run_id": "APR-0007", "path": EVIDENCE_PATHS["tl2_apr7"],
         "sha256": hashes["tl2_apr7"]},
        {"run_id": record_r2["critic_run_id"],
         "path": EVIDENCE_PATHS["tl2_record_r2"],
         "sha256": hashes["tl2_record_r2"]},
        {"run_id": "APR-0010", "path": EVIDENCE_PATHS["tl2_apr10"],
         "sha256": hashes["tl2_apr10"]},
    ]
    calibration_observation = [
        calibration_observation_block("cal_run_v1", cal_v1, hashes),
        calibration_observation_block("cal_run_v2", cal_v2, hashes),
    ]
    critic_metric = hp.project_critic_agreement_v2(
        critic_runs, ledger_r1["events"] + ledger_r2["events"],
        record_evidence=record_evidence,
        calibration_observation=calibration_observation,
        baseline_basis=("前一 revision（v3-tl6-r1）该指标 not_available"
                        "（分母 0）——无数值可作基线；本 revision 为首个"
                        "冻结一致率数值（装配侧 run 级）"))

    # ---- 指标三：Proposer 接受率（无新 adoption 事件，语义同 v1） -------
    def patch_candidate(p: dict) -> dict:
        profile = p["base_revision"].replace("BASE-", "").rsplit("-r1", 1)[0]
        return {"patch_id": p["patch_id"], "kind": p["operation_kind"],
                "version": p["model_version"], "profile": profile}

    pm2 = predicate_map(tl4_gate_2l)
    pm4 = predicate_map(tl4_gate_4l)
    for k in ("holdout_non_regression_evidenced",
              "adoption_machine_gate_pass", "judge_post_ok"):
        if pm2[k] != pm4[k]:
            raise SystemExit(f"编排中止：TL-4 两 profile 谓词 {k} 不一致 "
                             f"（{pm2[k]} vs {pm4[k]}）")
    machine_gate = {k: pm2[k] for k in ("holdout_non_regression_evidenced",
                                        "judge_post_ok",
                                        "adoption_machine_gate_pass")}
    proposer_metric = hp.project_proposer_acceptance_v2(
        [patch_candidate(patch_2l), patch_candidate(patch_4l)], apr4,
        machine_gate,
        patch_evidence=[
            {"path": EVIDENCE_PATHS["tl4_patch_2l"],
             "sha256": hashes["tl4_patch_2l"]},
            {"path": EVIDENCE_PATHS["tl4_patch_4l"],
             "sha256": hashes["tl4_patch_4l"]},
            {"path": EVIDENCE_PATHS["tl4_gate_2l"],
             "sha256": hashes["tl4_gate_2l"]},
            {"path": EVIDENCE_PATHS["tl4_gate_4l"],
             "sha256": hashes["tl4_gate_4l"]},
            {"path": EVIDENCE_PATHS["tl4_apr4"],
             "sha256": hashes["tl4_apr4"]},
        ],
        baseline=0.0,
        baseline_basis=("前一 revision（v3-tl6-r1）值 0.0"
                        "（0/2 human_approved_machine_blocked）作基线"))

    # ---- 指标四：跨板不回退（执行分母仍 0）+ k9 参考态证据层单列 --------
    nonreg_metric = hp.project_non_regression_v2(
        [],
        evidence=[{"path": EVIDENCE_PATHS["tl4_gate_2l"],
                   "sha256": hashes["tl4_gate_2l"]},
                  {"path": EVIDENCE_PATHS["tl4_gate_4l"],
                   "sha256": hashes["tl4_gate_4l"]}],
        evidence_extra=[{"path": EVIDENCE_PATHS["k9_batch_summary"],
                         "sha256": hashes["k9_batch_summary"]}],
        reference_batch=reference_batch_block(k9_batch, hashes))

    metrics = [queue_metric, critic_metric, proposer_metric,
               nonreg_metric]

    # ---- 辅助刻度 ------------------------------------------------------
    open_items = []
    oldest_seq = None
    last_seq = 0
    for l in (ledger_r1, ledger_r2):
        open_items.extend(it["item_id"]
                          for it in queue_mod.current_queue(l["events"]))
        last_seq = max(last_seq,
                       max(ev.get("event_seq", 0) for ev in l["events"]))
        s = queue_mod.projection_summary(l["events"])
        if s["oldest_item_seq"] is not None:
            oldest_seq = (s["oldest_item_seq"] if oldest_seq is None
                          else min(oldest_seq, s["oldest_item_seq"]))
    queue_summary = {
        "oldest_item_id": (open_items[0] if open_items else None),
        "oldest_item_seq": oldest_seq,
        "last_event_seq": last_seq,
        "age_events": (last_seq - oldest_seq
                       if oldest_seq is not None else None),
    }
    dag_nodes = [
        {"node": "TL-3-G1", "state": "fail",
         "evidence": [{"path": EVIDENCE_PATHS["tl3_gate"],
                       "sha256": hashes["tl3_gate"]}]},
        {"node": "TL-4-G", "state": "fail",
         "evidence": [{"path": EVIDENCE_PATHS["tl4_gate_2l"],
                       "sha256": hashes["tl4_gate_2l"]},
                      {"path": EVIDENCE_PATHS["tl4_gate_4l"],
                       "sha256": hashes["tl4_gate_4l"]}]},
        {"node": "TL-6", "state": "blocked",
         "self_reference": True,
         "evidence": [{"path": "out/v3-tl6/health-projection-gate-v2.json",
                       "note": "本包 gate record（自引；sha256 见其 "
                               "projection_ref）"}]},
    ]
    aux = hp.auxiliary_scales(
        tl3_coverage=tl3_cov,
        dag_nodes=dag_nodes,
        queue_summary=queue_summary,
        physics_report_revision=tl3_report.get("snapshot_revision"),
        gate_inputs_revision=tl3_cov.get("snapshot_revision"))

    # ---- readiness matrix（逐格重评） -----------------------------------
    matrix_evidence = {
        "TL-0-G1": [
            {"path": EVIDENCE_PATHS["tl0_gate_2l"],
             "sha256": hashes["tl0_gate_2l"]},
            {"path": EVIDENCE_PATHS["tl0_gate_4l"],
             "sha256": hashes["tl0_gate_4l"]}],
        "TL-1-G1": [{"path": EVIDENCE_PATHS["tl1_gate"],
                     "sha256": hashes["tl1_gate"]}],
        "TL-2": [
            {"path": EVIDENCE_PATHS["tl2_record_r1"],
             "sha256": hashes["tl2_record_r1"]},
            {"path": EVIDENCE_PATHS["tl2_ledger_r1"],
             "sha256": hashes["tl2_ledger_r1"]},
            {"path": EVIDENCE_PATHS["tl2_apr5"],
             "sha256": hashes["tl2_apr5"]},
            {"path": EVIDENCE_PATHS["tl2_record_r2"],
             "sha256": hashes["tl2_record_r2"]},
            {"path": EVIDENCE_PATHS["tl2_ledger_r2"],
             "sha256": hashes["tl2_ledger_r2"]},
            {"path": EVIDENCE_PATHS["tl2_apr7"],
             "sha256": hashes["tl2_apr7"]},
            {"path": EVIDENCE_PATHS["tl2_apr10"],
             "sha256": hashes["tl2_apr10"]}],
        "TL-3-G1": [
            {"path": EVIDENCE_PATHS["tl3_gate"],
             "sha256": hashes["tl3_gate"]},
            {"path": EVIDENCE_PATHS["tl3_coverage"],
             "sha256": hashes["tl3_coverage"]}],
        "TL-4-G": [
            {"path": EVIDENCE_PATHS["tl4_gate_2l"],
             "sha256": hashes["tl4_gate_2l"]},
            {"path": EVIDENCE_PATHS["tl4_gate_4l"],
             "sha256": hashes["tl4_gate_4l"]},
            {"path": EVIDENCE_PATHS["tl4_apr4"],
             "sha256": hashes["tl4_apr4"]}],
        "TL-5-G": [
            {"path": EVIDENCE_PATHS["tl5_gate_v4"],
             "sha256": hashes["tl5_gate_v4"]},
            {"path": EVIDENCE_PATHS["manifest_demos_r2"],
             "sha256": hashes["manifest_demos_r2"]},
            {"path": EVIDENCE_PATHS["k9_batch_summary"],
             "sha256": hashes["k9_batch_summary"]}],
        "TD7-QUAL-G": [
            {"path": EVIDENCE_PATHS["td7_gate_frozen"],
             "sha256": hashes["td7_gate_frozen"]},
            {"path": EVIDENCE_PATHS["arc1"], "sha256": hashes["arc1"]},
            {"path": EVIDENCE_PATHS["arc2"], "sha256": hashes["arc2"]},
            {"path": EVIDENCE_PATHS["arc3"], "sha256": hashes["arc3"]},
            {"path": EVIDENCE_PATHS["arc4"], "sha256": hashes["arc4"]}],
        "production_signoff_ready": [
            {"path": EVIDENCE_PATHS["tl3_gate"],
             "sha256": hashes["tl3_gate"]},
            {"path": EVIDENCE_PATHS["tl4_gate_2l"],
             "sha256": hashes["tl4_gate_2l"]}],
    }
    matrix = hp.readiness_matrix_v2(matrix_evidence)
    blockers = hp.open_production_blockers_v2()

    # ---- 语料分母（三库 100 板；转换域覆盖更新） -------------------------
    def split_count(m, key):
        v = m.get("dataset_splits", {}).get(key)
        return len(v) if isinstance(v, list) else 0

    by_dataset = {
        "pcbbenchmarks-r1": (split_count(manifest_pcbbm, "train")
                             + split_count(manifest_pcbbm, "validation")
                             + split_count(manifest_pcbbm, "holdout")),
        "pcbench-r1": (split_count(manifest_pcbench, "train")
                       + split_count(manifest_pcbench, "validation")
                       + split_count(manifest_pcbench, "holdout")),
        "kicad-demos-r1": (split_count(manifest_demos, "train")
                           + split_count(manifest_demos, "validation")
                           + split_count(manifest_demos, "holdout")),
    }
    by_split = {
        ds: {"train": split_count(m, "train"),
             "validation": split_count(m, "validation"),
             "holdout": split_count(m, "holdout")}
        for ds, m in (("pcbbenchmarks-r1", manifest_pcbbm),
                      ("pcbench-r1", manifest_pcbench),
                      ("kicad-demos-r1", manifest_demos))
    }
    corpus = hp.corpus_denominator_block_v2(
        by_dataset, by_split,
        conversion_coverage=conversion_coverage_block(hashes))

    projection = hp.build_projection_v2(
        session_date=S22_DATE,
        evaluator_code_sha256=hashes["module"],
        metrics=metrics,
        aux_scales=aux,
        matrix=matrix,
        blockers=blockers,
        corpus_denominator=corpus,
    )
    return projection


def gate_inputs(hashes: dict) -> list:
    return [{"artifact_id": k, "path": p, "sha256": hashes[k],
             "status": "present"} for k, p in EVIDENCE_PATHS.items()]


def build_diff_payload(v2: dict, v2_sha: str, hashes: dict) -> dict:
    """逐格差异表载荷：v1 冻结件（先验 hash 断言）→ v2。"""
    v1_path = REPO / V1_PROJECTION
    v1_sha = hashing.sha256_file(str(v1_path))
    if v1_sha != FROZEN_V1_SHA256:
        raise SystemExit(
            f"编排中止：v1 冻结件 hash 不符（实测 {v1_sha[:8]}…，"
            f"先验 {FROZEN_V1_SHA256[:8]}…）——防覆写 fail-closed")
    v1 = read_json(v1_path)
    diff = hp.build_projection_diff(v1, v2)
    return {
        "schema_version": "3.0",
        "diff_id": "HP-DIFF-v3-tl6-r1-to-r2",
        "from": {"path": V1_PROJECTION, "sha256": v1_sha,
                 "sha256_8": v1_sha[:8],
                 "projection_id": v1.get("projection_id"),
                 "revision": v1.get("revision")},
        "to": {"path": V2_PROJECTION, "sha256": v2_sha,
               "sha256_8": v2_sha[:8],
               "projection_id": v2.get("projection_id"),
               "revision": v2.get("revision")},
        "frozen_v1_unchanged": True,
        "diff": diff,
    }


def main() -> int:
    hashes = measure_hashes()
    projection = build_everything(hashes)

    TL6_DIR.mkdir(parents=True, exist_ok=True)
    proj_path = TL6_DIR / "health-projection-v2.json"
    proj_bytes = hashing.canonical_json_bytes(projection)
    proj_path.write_bytes(proj_bytes)
    proj_sha = hashing.sha256_text(proj_bytes.decode("utf-8"))

    measured = {EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    gate = hp.build_gate_record_v2(
        projection=projection,
        projection_sha256=proj_sha,
        projection_path=V2_PROJECTION,
        predicates=predicates,
        failure_codes=failures,
        inputs=gate_inputs(hashes),
        evaluator_code_sha256=hashes["module"],
    )
    gate_path = TL6_DIR / "health-projection-gate-v2.json"
    gate_path.write_bytes(hashing.canonical_json_bytes(gate))

    diff_payload = build_diff_payload(projection, proj_sha, hashes)
    diff_path = TL6_DIR / "projection-diff-v1-to-v2.json"
    diff_bytes = hashing.canonical_json_bytes(diff_payload)
    diff_path.write_bytes(diff_bytes)

    # ---- byte-exact 重跑自校验 ------------------------------------------
    proj2 = build_everything(hashes)
    if hashing.canonical_json_bytes(proj2) != proj_path.read_bytes():
        print("FAIL: projection-v2 byte-exact 重跑不一致")
        return 1
    diff2 = build_diff_payload(projection, proj_sha, hashes)
    if hashing.canonical_json_bytes(diff2) != diff_path.read_bytes():
        print("FAIL: diff byte-exact 重跑不一致")
        return 1

    print("== S22 TL-6 health projection v2 ==")
    print("projection-v2:", rel_repo(proj_path), proj_sha[:16])
    print("gate-v2:      ", rel_repo(gate_path),
          hashing.sha256_file(str(gate_path))[:16])
    print("diff:         ", rel_repo(diff_path),
          hashing.sha256_file(str(diff_path))[:16])
    print("BYTE-EXACT RERUN VERIFIED")
    for m in projection["metrics"]:
        val = m["value"] if m["status"] == hp.STATUS_VALUE else m["status"]
        extra = (f" ({m['numerator']}/{m['denominator']})"
                 if m["status"] == hp.STATUS_VALUE
                 and m["denominator"] is not None else "")
        print(f"  {m['metric_id']}: {val}{extra}")
    print("  dag_blocked:", projection["auxiliary_scales"]["dag_blocked"]
          ["count"])
    print("  exit_gate:", gate["gate_record"]["exit_gate"]["result"],
          "blockers:",
          gate["gate_record"]["exit_gate"]["open_blockers"])
    print("  predicates:",
          {p["id"]: p["value"] for p in predicates})
    dsum = diff_payload["diff"]["summary"]
    print("  diff summary:", dsum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
