"""R1 会话测试：APR-0011 校准达标线暂时采纳登记（approvals_r4）+
校准域状态 v3 + 评估协议 v1 冻结锚。

覆盖：
- approvals_r4 常量与布局（日期=人工声明常量 2026-09-06、revision/
  checkpoint 标识、scope 合法枚举值=checker、r1/r2/r3 文件名不冲突）；
- APR-0011 bundle 构造（纯函数）：evidence 齐全→结构合法、
  gate_write_scan 全空、APR-0011 在案（disposition+ledger entry）、
  rationale_text 语义要点逐条在案（人工指示原文引用+「暂时/
  provisional」+「不翻转」+BL-4/TD5+seed_match_rate 命名对账+
  CONTAINMENT_MIN/AREA_RATIO_MAX 零变化）、byte-exact 重放；
- evidence 缺一→fail-closed ValueError（五个逻辑名逐一）；
- ledger 链 verify 零错误+verify_supersedes 零错误+checkpoint 一致
  （verify_against_checkpoint）；
- 域状态 v3 纯函数构造：status/supersedes（记 v2 盘上 hash）/
  threshold_baseline（五项数值+APR-0011+provisional_supersedable+
  precision_metric_mapping）/gt_count_current=4/gt_expansion_required=
  12/auto_triage=blocked；输入 dict 零变异；GT 计数不符 fail-closed；
- APR-0011 批准**不改变任何机器谓词**的显式断言：构造无置真路径
  （in_calibrated_range_current is False）+ 门写扫描全空 +
  度量阈值常量 CONTAINMENT_MIN/AREA_RATIO_MAX 零变化；
- 落盘集成锚（只读 out/）：r4 三件（bundle/ledger/处置单件）+ 两新件
  （domain-v3/protocol）在盘且相互一致（payload_ref/账本字节/
  checkpoint/evidence_registry 对盘实测）；domain-v3 落盘件与纯函数
  构造 byte-exact 一致；protocol 冻结状态行与逐条条款在案；
  域 v1/v2 及校准 evidence 冻结件 hash 零变化。

纯内存构造（生成器模式）：零子进程/零写盘/零网络；集成锚只读。
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import approvals_r4 as ar4          # noqa: E402
from pcbflow import calibration as cal           # noqa: E402
from pcbflow import disposition as disp          # noqa: E402
from pcbflow import hashing, ledger              # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")

APR_DIR = os.path.join(REPO, "out", "v3-approvals")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

#: 域 v1/v2 与校准 evidence 冻结件锚（收尾零变化断言用）
FROZEN_DOMAIN_V1_SHA256 = (
    "b2b98737c674868a534a6ca6d264914462fb64d1f67a4d0a71f8f85919b3fb0f")
FROZEN_DOMAIN_V2_SHA256 = (
    "6e5b2437252c116a242ed1bddd8854a18c53d1b954d60f3c3507e36340253c9e")
FROZEN_PROCESS_V1_SHA256 = (
    "8e33aa0d30fc23ae058633720c405aeaecf176bfb9a34c2f331390f3a2cc1cca")
FROZEN_PROCESS_V2_SHA256 = (
    "6e793f365e0b67ca8fe3203d7c500adddb7983d005c2822d78fff4f1620bb12d")
FROZEN_RUN_V2_SHA256 = (
    "c3ea9a2e6d326e0f8d3c095c9606673886113e577356861989131a8a3bc22877")
FROZEN_RUN_V3_R2_SHA256 = (
    "0f7278f4c43f7cdef09391ead0c0fc7202f80fa6ac72217bb9d569def6246766")

R4_FILE_NAMES = (
    "approvals-bundle-r4.json",
    "decision-ledger-r4.jsonl",
    "disposition-APR-0011-calibration-threshold-provisional-adoption.json",
)
R4_NEW_CAL_NAMES = ("calibration-domain-v3.json",
                    "evaluation-protocol-v1.md")


# ---------------------------------------------------------------------------
# approvals_r4 常量与布局
# ---------------------------------------------------------------------------

def test_r4_constants_and_layout():
    assert ar4.APPROVAL_DATE_R4 == "2026-09-06"      # 人工声明常量
    assert ar4.APPROVER == "user"
    assert ar4.APPROVER_ROLE == "human_authority"
    assert ar4.APPROVALS_REVISION_R4 == "v3-approvals-r4"
    assert ar4.CHECKPOINT_ID_R4 == "CKPT-V3-APPROVALS-R4"
    assert [s["approval_id"] for s in ar4.APPROVAL_SPECS_R4] == ["APR-0011"]
    spec = ar4.APPROVAL_SPECS_R4[0]
    assert spec["kind"] == "accept"
    # scope 枚举无 calibration 项：按 APR-0008 先例如实取 checker
    assert spec["scope"] == "checker"
    assert spec["scope"] in ("candidate", "constraint", "checker",
                             "physics", "external", "waiver_policy",
                             "adoption", "profile", "corpus")
    assert spec["rationale_code"] == \
        "calibration_threshold_provisionally_adopted"
    assert spec["fact_refs"] == ["TL-2", "critic_calibration_in_range",
                                 "calibration_threshold_baseline"]
    assert spec["evidence"] == ("process_v1", "domain_v2", "run_v2",
                                "run_v3_on_r2", "process_v2")
    assert ar4.disposition_filename(spec) == \
        "disposition-APR-0011-calibration-threshold-provisional-adoption.json"
    # 达标线基线五项数值（process-v1 §5 提案逐项同一）
    tb = ar4.THRESHOLD_BASELINE_R4
    assert tb["gt_recall_min"] == 0.75
    assert tb["seed_match_rate_min"] == 0.5
    assert tb["abstain_rate_max"] == 0.5
    assert tb["consecutive_rounds_required"] == 2
    assert tb["gt_count_min"] == 12
    assert tb["approved_by"] == "APR-0011"
    assert tb["approval_date"] == "2026-09-06"
    assert tb["adoption"] == "provisional_supersedable"
    # r1/r2/r3 登记文件名不被 r4 复用（追加批次、不覆写）
    prior = {"approvals-bundle.json", "decision-ledger.jsonl",
             "approvals-bundle-r2.json", "decision-ledger-r2.jsonl",
             "approvals-bundle-r3.json", "decision-ledger-r3.jsonl",
             "disposition-APR-0010-item-run-r2-disposition.json"}
    r4_names = set(ar4.disposition_filename(s)
                   for s in ar4.APPROVAL_SPECS_R4) | set(R4_FILE_NAMES)
    assert not (prior & r4_names)


# ---------------------------------------------------------------------------
# APR-0011 bundle 构造（纯函数）
# ---------------------------------------------------------------------------

def _evidence_hashes():
    hashes, errors = ar4.collect_evidence_hashes(REPO)
    assert errors == []
    return hashes


def test_build_bundle_r4_pure_and_valid():
    hashes = _evidence_hashes()
    b1 = ar4.build_approvals_bundle_r4(hashes)
    b2 = ar4.build_approvals_bundle_r4(hashes)
    assert (hashing.canonical_json_bytes(b1)
            == hashing.canonical_json_bytes(b2))     # byte-exact 重放
    assert b1["approval_count"] == 1
    assert b1["approval_date"] == "2026-09-06"
    assert b1["revision"] == "v3-approvals-r4"
    assert b1["ledger_verify"] == {"chain_errors": [],
                                   "supersedes_errors": []}
    assert all(v == [] for v in b1["gate_write_scan"].values())
    # APR-0011 在案（disposition + ledger entry）
    entries = b1["ledger_entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["entry_kind"] == "disposition"
    assert entry["authority"] == "human"
    assert entry["trust_level"] == "untrusted"
    assert entry["disposition_refs"] == ["APR-0011"]
    assert entry["snapshot_revision"] == "v3-approvals-r4"
    spec = ar4.APPROVAL_SPECS_R4[0]
    assert entry["artifact_hashes"] == {name: hashes[name]
                                        for name in spec["evidence"]}
    rec = b1["dispositions"][0]
    assert rec["disposition_id"] == "APR-0011"
    assert entry["payload_ref"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(rec))
    assert rec["kind"] == "accept" and rec["approver"] == "user"
    assert rec["approver_role"] == "human_authority"
    assert b1["threshold_baseline"]["approved_by"] == "APR-0011"
    # rationale 语义要点逐条在案
    text = rec["rationale_text"]
    assert "2026-09-06" in text
    assert ar4.INSTRUCTION_QUOTE_R4 in text          # 指示原文逐字引用
    assert "暂时" in text and "provisional" in text
    assert "supersedes" in text and "不构成永久承诺" in text
    assert "不是自动分流资格" in text and "恒 blocked" in text
    assert "BL-4" in text and "TD5" in text
    assert "不翻转" in text and "仍 False" in text
    assert "seed_match_rate" in text and "precision_vs_seed_gt" in text
    assert "口径同一" in text and "禁称完整 precision/FPR" in text
    assert "CONTAINMENT_MIN=0.5" in text and "AREA_RATIO_MAX=10.0" in text
    assert "不写任何机器门" in text and "不改任何冻结产物" in text
    assert len(text) <= 4096


def test_build_bundle_r4_evidence_missing_fail_closed():
    hashes = _evidence_hashes()
    for name, _ in ar4.EVIDENCE_FILES_R4:
        broken = dict(hashes)
        broken.pop(name)
        with pytest.raises(ValueError):
            ar4.build_approvals_bundle_r4(broken)
    with pytest.raises(ValueError):
        ar4.build_approvals_bundle_r4({})


def test_collect_evidence_hashes_r4_missing_root():
    hashes, errors = ar4.collect_evidence_hashes(
        os.path.join(REPO, "no", "such", "root"))
    assert hashes == {} and len(errors) == len(ar4.EVIDENCE_FILES_R4)


# ---------------------------------------------------------------------------
# ledger 链 verify + checkpoint 一致
# ---------------------------------------------------------------------------

def test_r4_ledger_chain_verify_and_checkpoint():
    bundle = ar4.build_approvals_bundle_r4(_evidence_hashes())
    entries = bundle["ledger_entries"]
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    assert ledger.verify_against_checkpoint(
        entries, bundle["ledger_checkpoint"]) == []
    ckpt = bundle["ledger_checkpoint"]
    assert ckpt["checkpoint_id"] == "CKPT-V3-APPROVALS-R4"
    assert ckpt["entry_count"] == 1 and ckpt["entry_seq"] == 0
    assert bundle["ledger_file_sha256"] == hashing.sha256_bytes(
        ar4.ledger_file_bytes(entries))


# ---------------------------------------------------------------------------
# 域状态 v3 纯函数构造
# ---------------------------------------------------------------------------

def _domain_v2():
    with open(os.path.join(CAL_DIR, "calibration-domain-v2.json"),
              encoding="utf-8") as f:
        return json.load(f)


def test_build_domain_v3_pure_function():
    v2 = _domain_v2()
    v2_snapshot = hashing.canonical_json_bytes(v2)   # 输入零变异锚
    d = ar4.build_calibration_domain_v3(
        v2, evidence_hashes=_evidence_hashes(),
        protocol_sha256="a" * 64)
    assert (hashing.canonical_json_bytes(v2) == v2_snapshot)
    # byte-exact 重放
    d2 = ar4.build_calibration_domain_v3(
        v2, evidence_hashes=_evidence_hashes(),
        protocol_sha256="a" * 64)
    assert (hashing.canonical_json_bytes(d)
            == hashing.canonical_json_bytes(d2))
    assert d["domain_id"] == "calibration-domain-v3"
    assert d["domain_version"] == "3.0"
    assert d["declared_date"] == "2026-09-06"
    assert d["status"] == "threshold_provisionally_adopted"
    # supersedes 记 v2 盘上 hash（先验锚）
    assert d["supersedes"]["domain"] == "calibration-domain-v2"
    assert d["supersedes"]["sha256"] == FROZEN_DOMAIN_V2_SHA256
    # threshold_baseline 块
    tb = d["threshold_baseline"]
    assert tb["gt_recall_min"] == 0.75
    assert tb["seed_match_rate_min"] == 0.5
    assert tb["abstain_rate_max"] == 0.5
    assert tb["consecutive_rounds_required"] == 2
    assert tb["gt_count_min"] == 12
    assert tb["approved_by"] == "APR-0011"
    assert tb["approval_date"] == "2026-09-06"
    assert tb["adoption"] == "provisional_supersedable"
    assert "seed_match_rate" in tb["precision_metric_mapping"]
    assert "precision_vs_seed_gt" in tb["precision_metric_mapping"]
    assert "口径同一" in tb["precision_metric_mapping"]
    assert d["gt_count_current"] == 4
    assert d["gt_expansion_required"] == 12
    assert d["auto_triage"] == "blocked"
    # 实测轮次转录（两轮均未达标）
    basis = d["in_calibrated_range_basis"]
    assert basis["status"] == "not_met_current"
    assert basis["rounds_measured"] == 2
    assert basis["rounds"][0]["gt_recall"] == 0.25
    assert basis["rounds"][1]["seed_match_rate"] == 0.142857
    assert d["evaluation_protocol"]["metric"] == "calibration-metric-v3"
    assert d["evaluation_protocol"]["status"] == "frozen_from_this_round"
    # v2 携带块零变化（metric/ground_truth 原样，v1/v2 文件不动）
    assert d["metric"] == v2["metric"]
    assert d["ground_truth"] == v2["ground_truth"]


def test_build_domain_v3_gt_count_mismatch_fail_closed():
    v2 = _domain_v2()
    broken = json.loads(json.dumps(v2))
    broken["ground_truth"]["entry_count"] = 5
    with pytest.raises(ValueError):
        ar4.build_calibration_domain_v3(
            broken, evidence_hashes=_evidence_hashes(),
            protocol_sha256="a" * 64)
    with pytest.raises(ValueError):
        ar4.build_calibration_domain_v3(
            v2, evidence_hashes={}, protocol_sha256="a" * 64)
    with pytest.raises(ValueError):
        ar4.build_calibration_domain_v3(
            v2, evidence_hashes=_evidence_hashes(), protocol_sha256="")


# ---------------------------------------------------------------------------
# APR-0011 批准不改变任何机器谓词（显式断言）
# ---------------------------------------------------------------------------

def test_apr_0011_flips_no_machine_predicate():
    hashes = _evidence_hashes()
    bundle = ar4.build_approvals_bundle_r4(hashes)
    # 1) 门写扫描全空（处置对象不含任何门写禁区键）
    assert bundle["gate_write_scan"] == {"APR-0011": []}
    rec = bundle["dispositions"][0]
    assert disp.validate_no_gate_write(rec) == []
    # 2) 构造无置真路径：域 v3 的 in_calibrated_range_current 恒 False
    v2 = _domain_v2()
    d = ar4.build_calibration_domain_v3(
        v2, evidence_hashes=hashes, protocol_sha256="a" * 64)
    assert d["in_calibrated_range_current"] is False
    assert d["auto_triage"] == "blocked"
    assert d["in_calibrated_range_basis"]["status"] == "not_met_current"
    # 3) 度量阈值常量不因本批准变化
    assert cal.CONTAINMENT_MIN == 0.5
    assert cal.AREA_RATIO_MAX == 10.0
    assert cal.METRIC_VERSION_V3 == "calibration-metric-v3"
    # 4) rationale/冻结状态文本：语义红线在案
    assert "不翻转" in rec["rationale_text"]
    assert "critic_calibration_in_range" in \
        bundle["frozen_machine_gate_status"]
    assert "自动分流仍 blocked" in bundle["frozen_machine_gate_status"]


# ---------------------------------------------------------------------------
# 落盘集成锚（只读；r1/r2/r3 字节不动）
# ---------------------------------------------------------------------------

def test_r4_artifacts_on_disk_consistent():
    for name in R4_FILE_NAMES + R4_NEW_CAL_NAMES:
        assert os.path.isfile(os.path.join(APR_DIR if name in R4_FILE_NAMES
                                           else CAL_DIR, name)), name
    bundle = json.load(open(os.path.join(APR_DIR,
                                         "approvals-bundle-r4.json"),
                            encoding="utf-8"))
    ledger_disk = hashing.sha256_file(
        os.path.join(APR_DIR, "decision-ledger-r4.jsonl"))
    assert ledger_disk == bundle["ledger_file_sha256"]
    entries = [json.loads(line) for line in open(
        os.path.join(APR_DIR, "decision-ledger-r4.jsonl"),
        encoding="utf-8").read().splitlines()]
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    assert ledger.verify_against_checkpoint(
        entries, bundle["ledger_checkpoint"]) == []
    assert len(entries) == 1
    assert entries[0]["disposition_refs"] == ["APR-0011"]
    assert entries[0]["authority"] == "human"
    assert entries[0]["trust_level"] == "untrusted"
    for spec in ar4.APPROVAL_SPECS_R4:
        path = os.path.join(APR_DIR, ar4.disposition_filename(spec))
        assert hashing.sha256_file(path) == entries[0]["payload_ref"]
    for item in bundle["evidence_registry"]:
        disk = hashing.sha256_file(
            os.path.join(REPO, *item["path"].split("/")))
        assert disk == item["sha256"], item["name"]
    # 域 v3 落盘件与纯函数构造 byte-exact 一致（协议 hash 为盘上实值）
    protocol_path = os.path.join(CAL_DIR, "evaluation-protocol-v1.md")
    protocol_sha = hashing.sha256_file(protocol_path)
    expected_v3 = ar4.build_calibration_domain_v3(
        _domain_v2(), evidence_hashes=_evidence_hashes(),
        protocol_sha256=protocol_sha)
    disk_v3_bytes = open(os.path.join(CAL_DIR,
                                      "calibration-domain-v3.json"),
                         "rb").read()
    assert disk_v3_bytes == hashing.canonical_json_bytes(expected_v3)
    disk_v3 = json.loads(disk_v3_bytes.decode("utf-8"))
    assert disk_v3["status"] == "threshold_provisionally_adopted"
    assert disk_v3["supersedes"]["sha256"] == FROZEN_DOMAIN_V2_SHA256
    assert disk_v3["in_calibrated_range_current"] is False
    assert disk_v3["auto_triage"] == "blocked"
    # 协议冻结件内容锚（状态行+逐条条款）
    protocol = open(protocol_path, encoding="utf-8").read()
    assert "本协议自本轮起冻结" in protocol
    assert "metric=calibration-metric-v3" in protocol
    assert "后续修订=新版本文件，不回写" in protocol
    assert "seed_match_rate ≥ 0.5" in protocol and "gt_recall ≥ 0.75" \
        in protocol
    assert "abstain_rate ≤ 0.5" in protocol
    assert "连续 2 轮" in protocol and "GT ≥ 12" in protocol
    assert "未建立，TBD" in protocol and "人工批准+独立裁定" in protocol
    assert "不得为凑表生成新 GT" in protocol
    assert "flag_views" in protocol and "view_check=full" in protocol
    assert "禁称完整 precision/FPR" in protocol
    assert "不构成电气事实" in protocol
    assert "降级为 development 证据" in protocol


def test_calibration_frozen_evidence_untouched_on_disk():
    anchors = {
        "calibration-domain-v1.json": FROZEN_DOMAIN_V1_SHA256,
        "calibration-domain-v2.json": FROZEN_DOMAIN_V2_SHA256,
        "calibration-process-v1.md": FROZEN_PROCESS_V1_SHA256,
        "calibration-process-v2.md": FROZEN_PROCESS_V2_SHA256,
        "calibration-run-v2.json": FROZEN_RUN_V2_SHA256,
        "calibration-run-v3-on-r2-inputs.json": FROZEN_RUN_V3_R2_SHA256,
    }
    for name, expected in anchors.items():
        assert hashing.sha256_file(
            os.path.join(CAL_DIR, name)) == expected, name
