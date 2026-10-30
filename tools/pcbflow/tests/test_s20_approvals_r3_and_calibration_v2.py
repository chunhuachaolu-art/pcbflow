"""S20 会话测试：ITEM-run-r2 队列关闭链 + APR-0010 r3 登记 + 度量 v2 +
__main__ 入口。

覆盖：
- 队列关闭（集成锚，只读 out/）：run-r2 queue-event-ledger 现 3 事件、
  verify_chain 全绿、首行 enqueue 字节未变（8d45c429…，逐行 JSON 重排
  对账）、QE-000001=assign / QE-000002=approve（actor=user、
  actor_role=human_final、reason_code=item_dispositioned_apr_0010、
  prev 链指向 8d45c429…）、projection_summary.queue_length=0；
- approvals_r3（纯函数）：APR-0010 bundle 构造（authority=human、
  trust_level=untrusted、payload_ref=处置 canonical sha、artifact
  hash 绑定 run-r2 三 evidence）、gate_write_scan 全空、byte-exact
  重放、evidence 缺失 fail-closed、r3 常量（日期=声明常量
  2026-09-05、revision/checkpoint 标识、r1/r2 文件名不冲突）、
  rationale 语义要点在案（12 旗全 advisory/队列关闭/语料板只读/
  critic 输出恒 untrusted）；
- r3 落盘集成锚（只读 out/v3-approvals/）：bundle/ledger/checkpoint/
  verify/处置单件相互一致、evidence_registry 对盘上实文件一致
  （queue-event-ledger=追加后字节）；r1/r2 文件名仍在（字节不动）；
- 度量 v2（纯函数）：AREA_RATIO_MAX=10.0 与 rationale 在案（先写死）、
  面积比恰 10.0 过/12.0 拒（containment 1.0 仍拒）、正常邻域框过、
  containment 边界 0.5 过/0.4 拒、abstain/no_box 语义同 v1、
  area_ratio_max 非法 fail-closed、GT 自比较全匹配（面积比 1.0）；
- 集成锚（只读）：v1 复算与已归档 calibration-run-v1.json canonical
  一致（v1 路径零回归）；归档输入下 v2 拒 F-014（面积比 441×）、
  过 F-012；manifest v2 绑定 GT/v1 manifest/v1 run/process doc/selfcheck
  hash 与盘上实文件一致、threshold_adoption=proposal_only；
- __main__ 入口：runpy 以 __main__ 执行（stdin→stdout canonical JSON）
  v1 缺省与 v2 显式可选；未知 metric_version / v1 带 area_ratio_max
  拒绝（fail-closed）。

纯内存构造（生成器模式）：零子进程/零写盘/零网络；集成锚只读。
"""

import io
import json
import os
import runpy
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import approvals_r3 as ar3          # noqa: E402
from pcbflow import calibration as cal           # noqa: E402
from pcbflow import hashing, ledger, queue       # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 队列关闭（集成锚：run-r2 账本）
# ---------------------------------------------------------------------------

def _load_run2_ledger():
    path = os.path.join(REPO, "out", "v3-tl2", "critic-runs", "run-r2",
                        "queue-event-ledger.jsonl")
    with open(path, "rb") as f:
        raw = f.read()
    events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    return raw, events


def test_run2_ledger_closed_state():
    raw, events = _load_run2_ledger()
    assert len(events) == 3
    assert queue.verify_chain(events) == []
    assert raw.endswith(b"\n")
    # 首行 enqueue 字节未变：既有行按落盘口径重排逐字节对账
    first_line = raw.split(b"\n")[0] + b"\n"
    assert first_line == (json.dumps(events[0], ensure_ascii=False,
                                     sort_keys=True) + "\n").encode("utf-8")
    assert events[0]["event"] == "enqueue"
    assert events[0]["item_id"] == "ITEM-run-r2"
    assert events[0]["event_sha256"] == \
        "8d45c42927d23028bf8a77813cb65519d5c28782a1e13c1d8ea9aa813c1f3a73"
    assign, approve = events[1], events[2]
    assert assign["event"] == "assign" and assign["event_seq"] == 1
    assert assign["actor"] == "user"
    assert assign["actor_role"] == "human_final"
    assert assign["prev_event_sha256"] == events[0]["event_sha256"]
    assert approve["event"] == "approve" and approve["event_seq"] == 2
    assert approve["actor"] == "user"
    assert approve["actor_role"] == "human_final"
    assert approve["reason_code"] == "item_dispositioned_apr_0010"
    assert approve["prev_event_sha256"] == assign["event_sha256"]
    summary = queue.projection_summary(events)
    assert summary["queue_length"] == 0
    assert summary["total_events"] == 3


# ---------------------------------------------------------------------------
# approvals_r3 纯函数
# ---------------------------------------------------------------------------

def _evidence_hashes():
    hashes, errors = ar3.collect_evidence_hashes(REPO)
    assert errors == []
    return hashes


def test_r3_constants_and_layout():
    assert ar3.APPROVAL_DATE_R3 == "2026-09-05"      # 人工声明常量
    assert ar3.APPROVALS_REVISION_R3 == "v3-approvals-r3"
    assert ar3.CHECKPOINT_ID_R3 == "CKPT-V3-APPROVALS-R3"
    assert [s["approval_id"] for s in ar3.APPROVAL_SPECS_R3] == ["APR-0010"]
    spec = ar3.APPROVAL_SPECS_R3[0]
    assert spec["kind"] == "accept" and spec["scope"] == "checker"
    assert spec["fact_refs"] == ["ITEM-run-r2", "CR-run-r2",
                                 "critic_flags_advisory"]
    assert spec["evidence"] == ("run_r2_raw_flags", "run_r2_record",
                                "run_r2_queue_ledger")
    # r1/r2 登记文件名不被 r3 复用（追加批次、不覆写）
    prior = {"approvals-bundle.json", "decision-ledger.jsonl",
             "ledger-checkpoint.json", "ledger-verify.json",
             "approvals-bundle-r2.json", "decision-ledger-r2.jsonl",
             "ledger-checkpoint-r2.json", "ledger-verify-r2.json"}
    r3_names = set(ar3.disposition_filename(s)
                   for s in ar3.APPROVAL_SPECS_R3) | {
        "approvals-bundle-r3.json", "decision-ledger-r3.jsonl",
        "ledger-checkpoint-r3.json", "ledger-verify-r3.json"}
    assert not (prior & r3_names)


def test_build_bundle_r3_pure_and_valid():
    hashes = _evidence_hashes()
    b1 = ar3.build_approvals_bundle_r3(hashes)
    b2 = ar3.build_approvals_bundle_r3(hashes)
    assert (hashing.canonical_json_bytes(b1)
            == hashing.canonical_json_bytes(b2))     # byte-exact 重放
    assert b1["approval_count"] == 1
    assert b1["approval_date"] == "2026-09-05"
    assert b1["revision"] == "v3-approvals-r3"
    assert b1["ledger_verify"] == {"chain_errors": [],
                                   "supersedes_errors": []}
    assert all(v == [] for v in b1["gate_write_scan"].values())
    entries = b1["ledger_entries"]
    assert len(entries) == 1
    spec = ar3.APPROVAL_SPECS_R3[0]
    entry = entries[0]
    assert entry["entry_kind"] == "disposition"
    assert entry["authority"] == "human"
    assert entry["trust_level"] == "untrusted"
    assert entry["disposition_refs"] == ["APR-0010"]
    assert entry["snapshot_revision"] == "v3-approvals-r3"
    assert entry["artifact_hashes"] == {name: hashes[name]
                                        for name in spec["evidence"]}
    rec = b1["dispositions"][0]
    assert entry["payload_ref"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(rec))
    assert rec["disposition_id"] == "APR-0010"
    assert rec["kind"] == "accept" and rec["approver"] == "user"
    assert rec["approver_role"] == "human_authority"
    # 语义要点在案
    text = rec["rationale_text"]
    assert "12 条旗标" in text and "5 条 abstain" in text
    assert "advisory 登记" in text and "关闭队列项" in text
    assert "语料板只读" in text and "处置≠改板" in text
    assert "critic 输出恒 untrusted" in text
    assert "human_final" in text and "item_dispositioned_apr_0010" in text


def test_build_bundle_r3_evidence_missing_fail_closed():
    hashes = _evidence_hashes()
    broken = dict(hashes)
    broken.pop("run_r2_queue_ledger")
    with pytest.raises(ValueError):
        ar3.build_approvals_bundle_r3(broken)
    with pytest.raises(ValueError):
        ar3.build_approvals_bundle_r3({})


def test_collect_evidence_hashes_r3_missing_root():
    hashes, errors = ar3.collect_evidence_hashes(
        os.path.join(REPO, "no", "such", "root"))
    assert hashes == {} and len(errors) == len(ar3.EVIDENCE_FILES_R3)


# ---------------------------------------------------------------------------
# r3 落盘集成锚（只读；r1/r2 字节不动）
# ---------------------------------------------------------------------------

def test_r3_artifacts_on_disk_consistent():
    ap_dir = os.path.join(REPO, "out", "v3-approvals")
    bundle = json.load(open(os.path.join(ap_dir,
                                         "approvals-bundle-r3.json"),
                            encoding="utf-8"))
    ledger_disk = hashing.sha256_file(
        os.path.join(ap_dir, "decision-ledger-r3.jsonl"))
    assert ledger_disk == bundle["ledger_file_sha256"]
    entries = [json.loads(line) for line in open(
        os.path.join(ap_dir, "decision-ledger-r3.jsonl"),
        encoding="utf-8").read().splitlines()]
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    assert len(entries) == 1
    verify = json.load(open(os.path.join(ap_dir, "ledger-verify-r3.json"),
                            encoding="utf-8"))
    assert verify["status"] == "ok" and verify["errors"] == []
    assert verify["entry_count"] == 1
    assert verify["ledger_file_sha256"] == bundle["ledger_file_sha256"]
    ckpt = json.load(open(os.path.join(ap_dir, "ledger-checkpoint-r3.json"),
                          encoding="utf-8"))
    assert ckpt == bundle["ledger_checkpoint"]
    assert ckpt["checkpoint_id"] == "CKPT-V3-APPROVALS-R3"
    assert ckpt["entry_count"] == 1
    for spec in ar3.APPROVAL_SPECS_R3:
        path = os.path.join(ap_dir, ar3.disposition_filename(spec))
        assert hashing.sha256_file(path) == entries[0]["payload_ref"]
    for item in bundle["evidence_registry"]:
        disk = hashing.sha256_file(
            os.path.join(REPO, *item["path"].split("/")))
        assert disk == item["sha256"], item["name"]
    # queue-event-ledger 证据=追加后字节（3 事件、关闭态）
    ledger_events = [json.loads(line) for line in open(
        os.path.join(REPO, "out", "v3-tl2", "critic-runs", "run-r2",
                     "queue-event-ledger.jsonl"),
        encoding="utf-8").read().splitlines()]
    assert len(ledger_events) == 3
    assert queue.verify_chain(ledger_events) == []


def test_r1_r2_artifacts_untouched_names_present():
    ap_dir = os.path.join(REPO, "out", "v3-approvals")
    for name in ("approvals-bundle.json", "decision-ledger.jsonl",
                 "approvals-bundle-r2.json", "decision-ledger-r2.jsonl",
                 "disposition-APR-0007-item-run-r1-disposition.json",
                 "disposition-APR-0009-verification-roadmap-tiers.json"):
        assert os.path.isfile(os.path.join(ap_dir, name)), name
    r2 = json.load(open(os.path.join(ap_dir, "approvals-bundle-r2.json"),
                        encoding="utf-8"))
    assert r2["revision"] == "v3-approvals-r2" and r2["approval_count"] == 3


# ---------------------------------------------------------------------------
# 度量 v2（纯函数；面积比上限先写死后跑）
# ---------------------------------------------------------------------------

def _gt(**over):
    base = dict(
        gt_id="GT-SYNTH-1", category="courtyard_crowding", side="top",
        board_box_mm=[1.0, 1.0, 2.0, 2.0],
        frame_box_pct=[0.5, 0.5, 0.625, 0.625],
        drc_types=["courtyards_overlap"], cluster_refs=["SY"],
        basis_refs=["synthetic"], description="合成边界用例")
    base.update(over)
    return cal.build_gt_entry(**base)


def _flag(fid, box, category="courtyard_crowding", abstain=False):
    return {"flag_id": fid, "category": category, "confidence": 0.9,
            "abstain": abstain, "frame_box_pct": box}


def test_metric_v2_constants_declared():
    assert cal.METRIC_VERSION_V2 == "calibration-metric-v2"
    assert cal.AREA_RATIO_MAX == 10.0
    assert cal.METRIC_VERSION == "calibration-metric-v1"   # v1 不动
    # 取值依据在案（第一性原理；禁结果反推）
    assert "同量级" in cal.AREA_RATIO_MAX_RATIONALE
    assert "10" in cal.AREA_RATIO_MAX_RATIONALE
    assert "proposal_only" in cal.AREA_RATIO_MAX_RATIONALE
    r = cal.compare_v2([], [_gt()])
    assert r["metric_version"] == "calibration-metric-v2"
    assert r["area_ratio_max"] == 10.0
    assert r["area_ratio_max_rationale"] == cal.AREA_RATIO_MAX_RATIONALE


def test_metric_v2_area_ratio_boundary():
    gt = [_gt()]
    # 面积比恰=10.0（0.5×0.3125 / 0.125×0.125，精确二进制小数）→ 过
    r = cal.compare_v2([_flag("F-E10", [0.3125, 0.40625, 0.8125,
                                        0.71875])], gt)
    assert r["matches"][0]["area_ratio"] == 10.0
    assert r["reader_false_positive_ids"] == []
    # 面积比 12.0（containment=1.0 仍拒）→ 拒且如实单列
    r2 = cal.compare_v2([_flag("F-R12", [0.3125, 0.375, 0.8125, 0.75])],
                        gt)
    assert r2["matches"] == []
    assert r2["reader_ratio_rejected_ids"] == ["F-R12"]
    assert r2["reader_ratio_rejected_detail"][0]["area_ratio"] == 12.0
    assert r2["reader_ratio_rejected_detail"][0]["containment"] == 1.0
    assert r2["reader_false_positive_ids"] == ["F-R12"]
    assert r2["gt_missed_ids"] == ["GT-SYNTH-1"]


def test_metric_v2_neighborhood_and_containment_boundary():
    gt = [_gt()]
    # 正常邻域框（面积比 1.8496×）→ 过
    r = cal.compare_v2([_flag("F-NB", [0.48, 0.48, 0.65, 0.65])], gt)
    assert r["matches"][0]["area_ratio"] == 1.8496
    assert r["gt_recall"] == 1.0
    # containment 恰=0.5（面积比 1.0）→ 过（≥ 语义与 v1 一致）
    r2 = cal.compare_v2([_flag("F-C05", [0.4375, 0.5, 0.5625, 0.625])],
                        gt)
    assert r2["matches"][0]["containment"] == 0.5
    assert r2["matches"][0]["area_ratio"] == 1.0
    # containment=0.4 → 拒（v1 同规则，面积比无关）
    r3 = cal.compare_v2([_flag("F-C04", [0.4375, 0.5, 0.55, 0.625])], gt)
    assert r3["matches"] == []
    assert r3["reader_false_positive_ids"] == ["F-C04"]


def test_metric_v2_abstain_no_box_and_validation():
    gt = [_gt()]
    flags = [_flag("F-A", [0.5, 0.5, 0.625, 0.625], abstain=True),
             {"flag_id": "F-N", "category": "courtyard_crowding",
              "confidence": 0.5, "abstain": False}]
    r = cal.compare_v2(flags, gt)
    assert r["reader_abstain_ids"] == ["F-A"]
    assert r["reader_unmatched_no_box_ids"] == ["F-N"]
    with pytest.raises(ValueError):
        cal.compare_v2([], [_gt()], area_ratio_max=0)
    with pytest.raises(ValueError):
        cal.compare_v2([], [_gt()], area_ratio_max=-1)
    with pytest.raises(ValueError):
        cal.compare_v2([], [_gt()], area_ratio_max=True)


def test_metric_v2_gt_selfcheck():
    entries = json.load(open(os.path.join(
        REPO, "out", "v3-tl2", "calibration", "ground-truth-v1.json"),
        encoding="utf-8"))["gt_entries"]
    gflags = [{"flag_id": e["gt_id"], "category": e["category"],
               "confidence": 1.0, "abstain": False,
               "frame_box_pct": e["frame_box_pct"]} for e in entries]
    r = cal.compare_v2(gflags, entries)
    assert r["gt_matched_count"] == 4
    assert r["reader_false_positive_ids"] == []
    assert [m["area_ratio"] for m in r["matches"]] == [1.0] * 4


# ---------------------------------------------------------------------------
# 集成锚（只读）：v1 零回归 + v2 对归档输入的 F-014 拒/F-012 过 +
# manifest v2 绑定
# ---------------------------------------------------------------------------

def _archived_cal_inputs():
    cal_dir = os.path.join(REPO, "out", "v3-tl2", "calibration")
    gt = json.load(open(os.path.join(cal_dir, "ground-truth-v1.json"),
                        encoding="utf-8"))
    raw = json.loads(open(os.path.join(cal_dir, "reader-raw-cal-v1.txt"),
                          encoding="utf-8").read())
    keys = ("flag_id", "category", "confidence", "abstain",
            "frame_box_pct")
    flags = [{k: f[k] for k in keys}
             for board in raw["per_board"] for f in board["flags"]]
    archived = json.load(open(os.path.join(cal_dir,
                                           "calibration-run-v1.json"),
                              encoding="utf-8"))
    return gt["gt_entries"], flags, archived


def test_v1_recompute_matches_archived_record():
    gt, flags, archived = _archived_cal_inputs()
    r1 = cal.compare(flags, gt)
    assert (hashing.canonical_json_bytes(r1)
            == hashing.canonical_json_bytes(archived))
    assert r1["metric_version"] == "calibration-metric-v1"
    assert r1["reader_matched_ids"] == ["F-012", "F-014"]   # v1 现状


def test_v2_on_archived_inputs_rejects_whole_board_frame():
    gt, flags, _ = _archived_cal_inputs()
    r2 = cal.compare_v2(flags, gt)
    assert "F-012" in r2["reader_matched_ids"]
    assert "F-014" not in r2["reader_matched_ids"]
    assert r2["reader_ratio_rejected_ids"] == ["F-014"]
    detail = r2["reader_ratio_rejected_detail"][0]
    assert detail["gt_id"] == "GT-REVC-P1-L1SHORT"
    assert detail["containment"] == 1.0
    assert detail["area_ratio"] == 441.227947
    # v2 下 F-014 如实计未匹配（度量补丁，不改写 v1 产物）
    assert "F-014" in r2["reader_false_positive_ids"]


def test_manifest_v2_and_selfcheck_on_disk():
    cal_dir = os.path.join(REPO, "out", "v3-tl2", "calibration")
    mf2 = json.load(open(os.path.join(cal_dir,
                                      "calibration-domain-v2.json"),
                         encoding="utf-8"))
    assert mf2["domain_id"] == "calibration-domain-v2"
    assert mf2["domain_version"] == "2.0"
    assert mf2["metric"]["metric_version"] == "calibration-metric-v2"
    assert mf2["metric"]["area_ratio_max"] == 10.0
    assert mf2["metric"]["is_gate"] is False
    assert mf2["metric"]["threshold_adoption"] == \
        "proposal_only_pending_human_approval"
    gt_path = os.path.join(cal_dir, "ground-truth-v1.json")
    assert mf2["ground_truth"]["sha256"] == hashing.sha256_file(gt_path)
    assert mf2["ground_truth"]["entry_count"] == 4
    assert mf2["metric"]["v1_preserved"]["manifest"]["sha256"] == \
        hashing.sha256_file(
            os.path.join(cal_dir, "calibration-domain-v1.json"))
    assert mf2["metric"]["v1_preserved"]["run"]["sha256"] == \
        hashing.sha256_file(
            os.path.join(cal_dir, "calibration-run-v1.json"))
    assert mf2["selfcheck"]["sha256"] == hashing.sha256_file(
        os.path.join(cal_dir, "calibration-metric-v2-selfcheck.json"))
    selfcheck = json.load(open(os.path.join(
        cal_dir, "calibration-metric-v2-selfcheck.json"),
        encoding="utf-8"))
    assert selfcheck["v1_recompute"]["record_canonical_equal"] is True
    assert all(c.get("v2_matched") or c.get("v2_false_positive")
               for c in selfcheck["synthetic_cases"])
    assert selfcheck["gt_selfcheck_v2"]["gt_matched_count"] == 4


def test_calibration_process_doc_on_disk():
    path = os.path.join(REPO, "out", "v3-tl2", "calibration",
                        "calibration-process-v1.md")
    text = open(path, encoding="utf-8").read()
    assert "proposal_only" in text and "待人工" in text
    assert "critic_calibration_in_range" in text
    assert "AREA_RATIO_MAX = 10.0" in text
    assert "先写死后跑" in text
    assert "不执行新的 reader 盲读轮" in text


# ---------------------------------------------------------------------------
# __main__ 入口（runpy 进程内执行；stdin→stdout canonical JSON）
# ---------------------------------------------------------------------------

_GT = {
    "gt_id": "GT-X-1", "category": "courtyard_crowding", "side": "top",
    "board_box_mm": [1.0, 2.0, 3.0, 4.0],
    "frame_box_pct": [0.1, 0.2, 0.3, 0.4],
    "drc_types": ["courtyards_overlap"], "cluster_refs": ["R4"],
    "basis_refs": ["x"], "description": "d",
}
_FLAG = {"flag_id": "F1", "category": "courtyard_crowding",
         "confidence": 0.9, "abstain": False,
         "frame_box_pct": [0.1, 0.2, 0.3, 0.4]}


def _run_cli() -> dict:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        runpy.run_module("pcbflow.calibration", run_name="__main__",
                         alter_sys=False)
    finally:
        sys.stdout = old
    return json.loads(buf.getvalue())


def test_main_entry_default_v1(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"reader_flags": [_FLAG], "gt_entries": [_GT]})))
    report = _run_cli()
    assert report["metric_version"] == "calibration-metric-v1"
    assert report["gt_recall"] == 1.0
    assert "area_ratio_max" not in report


def test_main_entry_metric_v2(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"reader_flags": [_FLAG], "gt_entries": [_GT],
         "metric_version": "calibration-metric-v2"})))
    report = _run_cli()
    assert report["metric_version"] == "calibration-metric-v2"
    assert report["area_ratio_max"] == 10.0
    assert report["matches"][0]["area_ratio"] == 1.0


def test_main_entry_fail_closed(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"reader_flags": [_FLAG], "gt_entries": [_GT],
         "metric_version": "calibration-metric-v9"})))
    with pytest.raises(ValueError):
        cal.main()
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"reader_flags": [_FLAG], "gt_entries": [_GT],
         "area_ratio_max": 5})))
    with pytest.raises(ValueError):
        cal.main()
