"""S23 TL-6 健康度重投影 v3 编排（修正包 P1-C：指标语义更正）。

职责（对照 S22 装配模式，机制同构；s22 文件本身零改动）：

  health-projection-v3.json       v3 全量投影（五指标：队列/处置完成率
                                  （流程，2/2）/判断一致率（not_available）/
                                  接受率/跨板不回退；P1-C 拆分口径）
  health-projection-gate-v3.json  v3 健康度 gate-record（四机器谓词；
                                  内嵌 TL-6 出口门 blocked 如实）
  projection-diff-v2-to-v3.json   逐格差异表（v2 冻结件先验锚 → v3；
                                  纯函数 build_projection_diff）
  metric-correction-note-v1.json  指标更正说明（更正对象/拆分/零门翻转/
                                  冻结件不覆写声明）

语料分母口径（S23 起）：四库实测装配——r1 三库（manifest dataset_splits
train/validation/holdout 求和）+ corpus-r2-r1（datasets/ manifest
counts.boards/counts.by_tier 实测；train/val-candidate=候选未定 split、
holdout-pool=预冻结池，以 by_split 显式键诚实分列，不虚报已定 split）；
转换域覆盖口径不变（S18 入账，r2 语料只过入库级 parse 门）。

红线：out/ 只读，例外仅限上述四件新文件；v1/v2 六冻结件 hash 先验断言
（不符即中止——防覆写 fail-closed）；datasets/ 只读；零子进程；无
wall-clock（日期=人工会话声明常量 2026-09-05）；canonical JSON
byte-exact；收尾自校验=同参重建逐字节比对，并打印各文件 sha256 前 8。
缺陷更正背景：v2 冻结件 critic_agreement_rate=1.0（2/2）把 run 级处置
登记计成逐旗标一致率（语义混用）；v3 拆分为处置完成率（流程）与判断
一致率（not_available）——零门翻转（TL-6-G 仍 blocked、
production_signoff_ready 仍 false、自动分流仍 blocked）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing, health_projection as hp  # noqa: E402
from pcbflow import queue as queue_mod  # noqa: E402

S23_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）

TL6_DIR = REPO / "out" / "v3-tl6"
V1_PROJECTION = "out/v3-tl6/health-projection.json"
V2_PROJECTION = "out/v3-tl6/health-projection-v2.json"
V3_PROJECTION = "out/v3-tl6/health-projection-v3.json"

# v1/v2 冻结件先验锚（入账 hash；不配即中止——防覆写 fail-closed）
FROZEN_V1_SHA256 = ("98677d116a5d9f0b024b81e758051629f23e8b79c1b2d026aaa"
                    "534cd45092d66")
FROZEN_V1_GATE_SHA256 = ("66135e61a7166f0cc3f2763a908bfee18bdefecae1b9ae5fc"
                         "5139cffeb0d87aa")
FROZEN_V1_SIDECAR_SHA256 = ("2d946cef538e493de580650df45cd4f6e1a7a9aebcf615"
                            "162b4e5d3efb49d8ae")
FROZEN_V2_SHA256 = ("990bbf98cd665ce30610124473a638bbaff9c087883753107d526b"
                    "6267de7535")
FROZEN_V2_GATE_SHA256 = ("827200ff99edafc5b8e1661b69a15e58caced0019e9280f7e"
                         "c10f9f73171f2d8")
FROZEN_V2_DIFF_SHA256 = ("da22f874c70cd6aa40c11f866d55feeed015487bc760a91ec"
                         "2f106cea4ca4d03")

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
    "manifest_corpus_r2": "datasets/corpus-r2-r1/manifest.json",
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


def assert_frozen_unchanged() -> None:
    """v1/v2 六冻结件 hash 先验断言（任何写入发生前执行；不符即中止）。"""
    checks = (
        (V1_PROJECTION, FROZEN_V1_SHA256),
        ("out/v3-tl6/health-projection-gate.json", FROZEN_V1_GATE_SHA256),
        ("out/v3-tl6/health-projection.sha256", FROZEN_V1_SIDECAR_SHA256),
        (V2_PROJECTION, FROZEN_V2_SHA256),
        ("out/v3-tl6/health-projection-gate-v2.json", FROZEN_V2_GATE_SHA256),
        ("out/v3-tl6/projection-diff-v1-to-v2.json", FROZEN_V2_DIFF_SHA256),
    )
    for rel, expect in checks:
        got = hashing.sha256_file(str(REPO / rel))
        if got != expect:
            raise SystemExit(
                f"编排中止：冻结件 hash 不符（{rel} 实测 {got[:8]}…，"
                f"先验 {expect[:8]}…）——防覆写 fail-closed")


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


def conversion_coverage_block(hashes: dict, corpus_manifest: dict) -> dict:
    """转换域覆盖块：S18 入账口径 100 板不变；corpus-r2-r1 以入库级
    parse 门证据单列（零 kicad-cli/零渲染），不注册入覆盖口径、不回填。"""
    counts = corpus_manifest.get("counts") or {}
    by_bucket = counts.get("by_version_bucket") or {}
    k5 = int(by_bucket.get("20171130", 0))
    m1229 = int(by_bucket.get("20241229", 0))
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
        "corpus_r2_parse_gate": {
            "path": EVIDENCE_PATHS["manifest_corpus_r2"],
            "sha256": hashes["manifest_corpus_r2"],
            "sha256_8": hashes["manifest_corpus_r2"][:8],
            "boards": int(counts.get("boards", 0)),
            "kicad5_bucket_20171130": k5,
            "modern_bucket_20241229": m1229,
            "registration": ("入库级 parse 门证据（全量 sexpr 解析；"
                             "20171130 桶过 corpus_convert.parse_kicad5_"
                             "board；零 kicad-cli/零渲染）——未注册入转换域"
                             "覆盖口径，不回填 boards_total"),
        },
        "note": ("TL-5 门分母（37 profile）与 BL 清单语义不变；kicad-demos "
                 "r2 manifest 为 k9 转换域扩展证据，不入门分母、不回填 r1；"
                 "corpus-r2-r1 为入库级 parse 门证据单列（含 20171130×%d 与"
                 " 20241229×%d 等桶，均只过 parse 门，未注册入本覆盖口径）"
                 "——boards_total 维持 100（S18 入账），不据此回填"
                 % (k5, m1229)),
    }


def build_everything(hashes: dict):
    """同参确定性构建（byte-exact 重跑验证的基础；P1-C v3 口径）。"""
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
    manifest_corpus_r2 = read_json(
        REPO / EVIDENCE_PATHS["manifest_corpus_r2"])
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

    # ---- 指标一：人工队列（多账本合取；复用 v2 函数，revision 覆写） ----
    queue_metric = hp.project_manual_queue_multi(
        [ledger_r1, ledger_r2],
        revision=hp.PROJECTION_REVISION_V3,
        baseline=0,
        baseline_basis=("前一 revision（v3-tl6-r2，冻结件 990bbf98…）"
                        "manual_queue_length=0——冻结值作基线"))

    # ---- 指标二/三：处置完成率（流程）+ 判断一致率（not_available） -----
    # P1-C：不再从 APR 处置推导 human_supports_flags（该推导正是 v2 语义
    # 混用的缺陷源）；处置终态只取队列事件，旗标对错一律 not_available。
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
         "board_flag_counts": b1},
        {"run_id": record_r2["critic_run_id"],
         "critic_status": record_r2["critic_status"],
         "input_hashes_match": record_r2["input_hashes_match"],
         "critic_ref": hashes["tl2_record_r2"],
         "in_calibrated_range":
             record_r2["calibration"]["in_calibrated_range"],
         "flags_total": f2, "abstain_count": a2,
         "board_flag_counts": b2},
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
    disposition_metric = hp.project_critic_disposition_completion(
        critic_runs, ledger_r1["events"] + ledger_r2["events"],
        record_evidence=record_evidence)
    judgment_metric = hp.project_critic_judgment_agreement(
        critic_runs, ledger_r1["events"] + ledger_r2["events"],
        record_evidence=record_evidence,
        calibration_observation=calibration_observation)

    # ---- 指标四：Proposer 接受率（复用 v2 语义，revision 覆写） ---------
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
        revision=hp.PROJECTION_REVISION_V3,
        baseline=0.0,
        baseline_basis=("前一 revision（v3-tl6-r2）值 0.0"
                        "（0/2 human_approved_machine_blocked）作基线"))

    # ---- 指标五：跨板不回退（复用 v2 语义，revision 覆写） --------------
    nonreg_metric = hp.project_non_regression_v2(
        [],
        evidence=[{"path": EVIDENCE_PATHS["tl4_gate_2l"],
                   "sha256": hashes["tl4_gate_2l"]},
                  {"path": EVIDENCE_PATHS["tl4_gate_4l"],
                   "sha256": hashes["tl4_gate_4l"]}],
        evidence_extra=[{"path": EVIDENCE_PATHS["k9_batch_summary"],
                         "sha256": hashes["k9_batch_summary"]}],
        reference_batch=reference_batch_block(k9_batch, hashes),
        revision=hp.PROJECTION_REVISION_V3)

    metrics = [queue_metric, disposition_metric, judgment_metric,
               proposer_metric, nonreg_metric]

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
         "evidence": [{"path": "out/v3-tl6/health-projection-gate-v3.json",
                       "note": "本包 gate record（自引；sha256 见其 "
                               "projection_ref）"}]},
    ]
    aux = hp.auxiliary_scales(
        tl3_coverage=tl3_cov,
        dag_nodes=dag_nodes,
        queue_summary=queue_summary,
        physics_report_revision=tl3_report.get("snapshot_revision"),
        gate_inputs_revision=tl3_cov.get("snapshot_revision"))

    # ---- readiness matrix（v3 逐格重评；P1-C 口径） ----------------------
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
    matrix = hp.readiness_matrix_v3(matrix_evidence)
    blockers = hp.open_production_blockers_v3()

    # ---- 语料分母（四库实测：r1 三库 dataset_splits + corpus-r2-r1
    #      counts.boards/by_tier；复用 v3 块，v1/v2 输出字节稳定） -------
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
    # corpus-r2-r1：manifest 实测装配（不硬编码板数）；tier 口径如实——
    # train/val-candidate=候选未定 split（显式键 train_val_candidate 分列，
    # 不虚报 train/validation）；holdout-pool=预冻结池（显式键
    # holdout_pool，永不参与调参、不计入 holdout、不进不回退执行分母）。
    corpus_counts = manifest_corpus_r2.get("counts") or {}
    corpus_boards = int(corpus_counts.get("boards", 0))
    corpus_by_tier = corpus_counts.get("by_tier") or {}
    if corpus_boards <= 0 \
            or sum(int(v) for v in corpus_by_tier.values()) != corpus_boards:
        raise SystemExit(
            "编排中止：corpus-r2-r1 manifest counts.boards 与 "
            "counts.by_tier 合计不符（fail-closed）")
    if "train/val-candidate" not in corpus_by_tier \
            or "holdout-pool" not in corpus_by_tier:
        raise SystemExit(
            "编排中止：corpus-r2-r1 manifest counts.by_tier 缺 "
            "train/val-candidate 或 holdout-pool 键（fail-closed）")
    by_dataset["corpus-r2-r1"] = corpus_boards
    by_split["corpus-r2-r1"] = {
        "train": 0,
        "validation": 0,
        "holdout": 0,
        "train_val_candidate": int(corpus_by_tier["train/val-candidate"]),
        "holdout_pool": int(corpus_by_tier["holdout-pool"]),
    }
    corpus = hp.corpus_denominator_block_v3(
        by_dataset, by_split,
        conversion_coverage=conversion_coverage_block(
            hashes, manifest_corpus_r2))

    projection = hp.build_projection_v3(
        session_date=S23_DATE,
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


def build_diff_payload(v3: dict, v3_sha: str) -> dict:
    """逐格差异表载荷：v2 冻结件（先验 hash 断言）→ v3（从盘读 v2 原件，
    不重算 v2）。"""
    v2_path = REPO / V2_PROJECTION
    v2_sha = hashing.sha256_file(str(v2_path))
    if v2_sha != FROZEN_V2_SHA256:
        raise SystemExit(
            f"编排中止：v2 冻结件 hash 不符（实测 {v2_sha[:8]}…，先验 "
            f"{FROZEN_V2_SHA256[:8]}…）——防覆写 fail-closed")
    v2 = read_json(v2_path)
    diff = hp.build_projection_diff(v2, v3)
    return {
        "schema_version": "3.0",
        "diff_id": "HP-DIFF-v3-tl6-r2-to-r3",
        "from": {"path": V2_PROJECTION, "sha256": v2_sha,
                 "sha256_8": v2_sha[:8],
                 "projection_id": v2.get("projection_id"),
                 "revision": v2.get("revision")},
        "to": {"path": V3_PROJECTION, "sha256": v3_sha,
               "sha256_8": v3_sha[:8],
               "projection_id": v3.get("projection_id"),
               "revision": v3.get("revision")},
        "frozen_v2_unchanged": True,
        "diff": diff,
    }


def build_note_payload(v3: dict, v3_sha: str) -> dict:
    """更正说明载荷：更正对象=v2 冻结件（盘上实测 hash；先验锚在构造函数
    内 fail-closed 校验）。"""
    v2_sha = hashing.sha256_file(str(REPO / V2_PROJECTION))
    return hp.build_metric_correction_note(
        session_date=S23_DATE,
        v2_projection_sha256=v2_sha,
        v3_projection=v3,
        v3_projection_sha256=v3_sha)


def main() -> int:
    assert_frozen_unchanged()  # 先验：v1/v2 六冻结件一字不动（写入前执行）
    hashes = measure_hashes()
    projection = build_everything(hashes)

    TL6_DIR.mkdir(parents=True, exist_ok=True)
    proj_path = TL6_DIR / "health-projection-v3.json"
    proj_bytes = hashing.canonical_json_bytes(projection)
    proj_path.write_bytes(proj_bytes)
    proj_sha = hashing.sha256_text(proj_bytes.decode("utf-8"))

    measured = {EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates, failures = hp.gate_predicates(projection, measured)
    gate = hp.build_gate_record_v3(
        projection=projection,
        projection_sha256=proj_sha,
        projection_path=V3_PROJECTION,
        predicates=predicates,
        failure_codes=failures,
        inputs=gate_inputs(hashes),
        evaluator_code_sha256=hashes["module"],
    )
    gate_path = TL6_DIR / "health-projection-gate-v3.json"
    gate_bytes = hashing.canonical_json_bytes(gate)
    gate_path.write_bytes(gate_bytes)

    diff_payload = build_diff_payload(projection, proj_sha)
    diff_path = TL6_DIR / "projection-diff-v2-to-v3.json"
    diff_bytes = hashing.canonical_json_bytes(diff_payload)
    diff_path.write_bytes(diff_bytes)

    note_payload = build_note_payload(projection, proj_sha)
    note_path = TL6_DIR / "metric-correction-note-v1.json"
    note_bytes = hashing.canonical_json_bytes(note_payload)
    note_path.write_bytes(note_bytes)

    # ---- byte-exact 重跑自校验（四件全部同参重建比对） -------------------
    proj2 = build_everything(hashes)
    if hashing.canonical_json_bytes(proj2) != proj_path.read_bytes():
        print("FAIL: projection-v3 byte-exact 重跑不一致")
        return 1
    measured2 = {EVIDENCE_PATHS[k]: v for k, v in hashes.items()}
    predicates2, failures2 = hp.gate_predicates(proj2, measured2)
    gate2 = hp.build_gate_record_v3(
        projection=proj2, projection_sha256=proj_sha,
        projection_path=V3_PROJECTION, predicates=predicates2,
        failure_codes=failures2, inputs=gate_inputs(hashes),
        evaluator_code_sha256=hashes["module"])
    if hashing.canonical_json_bytes(gate2) != gate_path.read_bytes():
        print("FAIL: gate-v3 byte-exact 重跑不一致")
        return 1
    if hashing.canonical_json_bytes(
            build_diff_payload(proj2, proj_sha)) != diff_path.read_bytes():
        print("FAIL: diff byte-exact 重跑不一致")
        return 1
    if hashing.canonical_json_bytes(
            build_note_payload(proj2, proj_sha)) != note_path.read_bytes():
        print("FAIL: correction-note byte-exact 重跑不一致")
        return 1

    print("== S23 TL-6 health projection v3 (P1-C metric correction) ==")
    print("projection-v3:  ", rel_repo(proj_path),
          hashing.sha256_file(str(proj_path))[:8])
    print("gate-v3:        ", rel_repo(gate_path),
          hashing.sha256_file(str(gate_path))[:8])
    print("diff-v2-to-v3:  ", rel_repo(diff_path),
          hashing.sha256_file(str(diff_path))[:8])
    print("correction-note:", rel_repo(note_path),
          hashing.sha256_file(str(note_path))[:8])
    print("BYTE-EXACT RERUN VERIFIED (4 artifacts)")
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
    print("  diff summary:", diff_payload["diff"]["summary"])
    print("  note: zero_gate_flip =",
          note_payload["readiness_impact"]["zero_gate_flip"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
