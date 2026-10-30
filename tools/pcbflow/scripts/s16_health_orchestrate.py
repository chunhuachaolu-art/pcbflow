"""S16 TL-6 环路健康度/readiness 投影编排（编排侧脚本）。

本脚本=编排侧（非生成器）：读既有 out/ 产物（只读）+盘上实测 sha256，
调用 pcbflow.health_projection 纯函数，落盘 out/v3-tl6/ 两个核产物：

  health-projection.json        全量投影（四指标+辅助刻度+readiness matrix
                                +open blockers+语料分母）
  health-projection.sha256      投影文件 sidecar（sha256 hex）
  health-projection-gate.json   健康度 gate-record（四机器谓词；内嵌
                                TL-6 出口门 blocked 如实，不申请 closure）

红线：既有 out/ 与 datasets/ 只读；零子进程；无 wall-clock（日期=人工
会话声明常量）；canonical JSON byte-exact；本脚本收尾自校验=同参重建
逐字节比对（byte-exact 重跑验证）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing, health_projection as hp  # noqa: E402
from pcbflow import queue as queue_mod  # noqa: E402

S16_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）

TL6_DIR = REPO / "out" / "v3-tl6"

RUN_R1 = "out/v3-tl2/critic-runs/run-r1"

# 证据清单（repo 相对 POSIX 路径）——只读；sha256 全部盘上实测
EVIDENCE_PATHS = {
    "module": "pcbflow/health_projection.py",
    "tl0_gate_2l": "out/v3-tl0/gate-record-smoke-2l.json",
    "tl0_gate_4l": "out/v3-tl0/gate-record-smoke-4l.json",
    "tl1_gate": "out/v3-tl1/gate-record.json",
    "tl2_record": f"{RUN_R1}/critic-run-record-CR-run-r1.json",
    "tl2_ledger": f"{RUN_R1}/queue-event-ledger.jsonl",
    "tl2_raw_flags": f"{RUN_R1}/raw-flags.json",
    "tl2_apr5": "out/v3-approvals/disposition-APR-0005-critic-duty-level.json",
    "tl2_apr7": "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json",
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


def build_everything(hashes: dict):
    """同参确定性构建（byte-exact 重跑验证的基础）。"""
    # ---- 解析既有产物（只读） ------------------------------------------
    events = parse_queue_events(REPO / EVIDENCE_PATHS["tl2_ledger"])
    record = read_json(REPO / EVIDENCE_PATHS["tl2_record"])
    raw_flags = read_json(REPO / EVIDENCE_PATHS["tl2_raw_flags"])
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
    # S17 起 ITEM-run-r1 人工 verdict 侧（fail-closed：缺 disposition
    # 或语义不符 → human_supports_flags=False，不虚构支持）：
    # APR-0007（kind=accept、fact_refs 含 critic_flags_advisory）=人工
    # 将 7 条 flag 全部 advisory 登记并闭合队列 = 人工支持旗标登记。
    human_supports_flags = False
    apr7_evidence = None
    if hashes.get("tl2_apr7"):
        apr7 = read_json(REPO / EVIDENCE_PATHS["tl2_apr7"])
        if (apr7.get("kind") == "accept"
                and "critic_flags_advisory" in (apr7.get("fact_refs") or [])
                and apr7.get("disposition_id") == "APR-0007"):
            human_supports_flags = True
            apr7_evidence = {"run_id": record["critic_run_id"],
                             "path": EVIDENCE_PATHS["tl2_apr7"],
                             "sha256": hashes["tl2_apr7"]}

    # ---- 四指标 --------------------------------------------------------
    queue_metric = hp.project_manual_queue(
        events,
        ledger_path=EVIDENCE_PATHS["tl2_ledger"],
        ledger_sha256=hashes["tl2_ledger"])

    board_flag_counts: dict = {}
    abstain_count = 0
    flags_total = 0
    for board in raw_flags.get("per_board", []):
        pid = board.get("profile_id")
        n = len(board.get("flags", []))
        board_flag_counts[pid] = board_flag_counts.get(pid, 0) + n
        for f in board.get("flags", []):
            flags_total += 1
            if f.get("abstain"):
                abstain_count += 1
    critic_runs = [{
        "run_id": record["critic_run_id"],
        "critic_status": record["critic_status"],
        "input_hashes_match": record["input_hashes_match"],
        "critic_ref": hashes["tl2_record"],
        "in_calibrated_range": record["calibration"]["in_calibrated_range"],
        "flags_total": flags_total,
        "abstain_count": abstain_count,
        "board_flag_counts": board_flag_counts,
        "human_supports_flags": human_supports_flags,
    }]
    record_evidence = [{"run_id": record["critic_run_id"],
                        "path": EVIDENCE_PATHS["tl2_record"],
                        "sha256": hashes["tl2_record"]}]
    if apr7_evidence:
        record_evidence.append(apr7_evidence)
    critic_metric = hp.project_critic_agreement(
        critic_runs, events, record_evidence=record_evidence)

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
    proposer_metric = hp.project_proposer_acceptance(
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
        ])

    nonreg_metric = hp.project_non_regression(
        [],
        evidence=[{"path": EVIDENCE_PATHS["tl4_gate_2l"],
                   "sha256": hashes["tl4_gate_2l"]},
                  {"path": EVIDENCE_PATHS["tl4_gate_4l"],
                   "sha256": hashes["tl4_gate_4l"]}])

    metrics = [queue_metric, critic_metric, proposer_metric,
               nonreg_metric]

    # ---- 辅助刻度 ------------------------------------------------------
    summary = queue_mod.projection_summary(events)
    open_items = queue_mod.current_queue(events)
    queue_summary = {
        "oldest_item_id": (open_items[0]["item_id"] if open_items
                           else None),
        "oldest_item_seq": summary["oldest_item_seq"],
        "last_event_seq": max(ev.get("event_seq", 0) for ev in events),
        "age_events": (max(ev.get("event_seq", 0) for ev in events)
                       - summary["oldest_item_seq"])
        if summary["oldest_item_seq"] is not None else None,
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
         "evidence": [{"path": "out/v3-tl6/health-projection-gate.json",
                       "note": "本包 gate record（自引；sha256 见其 "
                               "projection_ref）"}]},
    ]
    aux = hp.auxiliary_scales(
        tl3_coverage=tl3_cov,
        dag_nodes=dag_nodes,
        queue_summary=queue_summary,
        physics_report_revision=tl3_report.get("snapshot_revision"),
        gate_inputs_revision=tl3_cov.get("snapshot_revision"))

    # ---- readiness matrix ---------------------------------------------
    matrix_evidence = {
        "TL-0-G1": [
            {"path": EVIDENCE_PATHS["tl0_gate_2l"],
             "sha256": hashes["tl0_gate_2l"]},
            {"path": EVIDENCE_PATHS["tl0_gate_4l"],
             "sha256": hashes["tl0_gate_4l"]}],
        "TL-1-G1": [{"path": EVIDENCE_PATHS["tl1_gate"],
                     "sha256": hashes["tl1_gate"]}],
        "TL-2": [
            {"path": EVIDENCE_PATHS["tl2_record"],
             "sha256": hashes["tl2_record"]},
            {"path": EVIDENCE_PATHS["tl2_ledger"],
             "sha256": hashes["tl2_ledger"]},
            {"path": EVIDENCE_PATHS["tl2_apr5"],
             "sha256": hashes["tl2_apr5"]}],
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
        "TL-5-G": [{"path": EVIDENCE_PATHS["tl5_gate_v4"],
                    "sha256": hashes["tl5_gate_v4"]}],
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
    matrix = hp.readiness_matrix(matrix_evidence)
    blockers = hp.open_production_blockers()

    # ---- 语料分母（三库 100 板） ----------------------------------------
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
    corpus = hp.corpus_denominator_block(by_dataset, by_split)

    projection = hp.build_projection(
        session_date=S16_DATE,
        evaluator_code_sha256=hashes["module"],
        metrics=metrics,
        aux_scales=aux,
        matrix=matrix,
        blockers=blockers,
        corpus_denominator=corpus,
    )
    return projection, events, record


def gate_inputs(hashes: dict) -> list:
    inputs = [{"artifact_id": k, "path": p, "sha256": hashes[k],
               "status": "present"} for k, p in EVIDENCE_PATHS.items()]
    return inputs


def main() -> int:
    hashes = measure_hashes()
    projection, _, _ = build_everything(hashes)

    TL6_DIR.mkdir(parents=True, exist_ok=True)
    proj_path = TL6_DIR / "health-projection.json"
    proj_bytes = hashing.canonical_json_bytes(projection)
    proj_path.write_bytes(proj_bytes)
    proj_sha = hashing.sha256_text(proj_bytes.decode("utf-8"))
    (TL6_DIR / "health-projection.sha256").write_text(
        proj_sha + "\n", encoding="utf-8", newline="")

    measured = {EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    gate = hp.build_gate_record(
        projection=projection,
        projection_sha256=proj_sha,
        projection_path="out/v3-tl6/health-projection.json",
        predicates=predicates,
        failure_codes=failures,
        inputs=gate_inputs(hashes),
        evaluator_code_sha256=hashes["module"],
    )
    gate_path = TL6_DIR / "health-projection-gate.json"
    gate_bytes = hashing.canonical_json_bytes(gate)
    gate_path.write_bytes(gate_bytes)

    # ---- byte-exact 重跑自校验 ------------------------------------------
    proj2, _, _ = build_everything(hashes)
    if hashing.canonical_json_bytes(proj2) != proj_path.read_bytes():
        print("FAIL: projection byte-exact 重跑不一致")
        return 1

    print("== S16 TL-6 health projection ==")
    print("projection:", rel_repo(proj_path), proj_sha[:16])
    print("gate:      ", rel_repo(gate_path),
          hashing.sha256_text(gate_bytes.decode("utf-8"))[:16])
    print("BYTE-EXACT RERUN VERIFIED")
    for m in projection["metrics"]:
        val = m["value"] if m["status"] == hp.STATUS_VALUE else m["status"]
        print(f"  {m['metric_id']}: {val}"
              + (f" ({m['numerator']}/{m['denominator']})"
                 if m["status"] == hp.STATUS_VALUE
                 and m["denominator"] is not None else ""))
    print("  dag_blocked:", projection["auxiliary_scales"]["dag_blocked"]
          ["count"])
    print("  exit_gate:", gate["gate_record"]["exit_gate"]["result"],
          "blockers:",
          gate["gate_record"]["exit_gate"]["open_blockers"])
    print("  predicates:",
          {p["id"]: p["value"] for p in predicates})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
