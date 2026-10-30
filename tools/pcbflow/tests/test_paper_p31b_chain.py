"""PAPER-P1-1B 终态锚定测试（快照 hash 链 + paired 记录 + 零 live 写）。

只锚终态：快照==live pre-hash、challenger hash 链、batch verdict 与留证
DRC JSON 独立复算一致、rollback 演练 pass、sidecar 日志零违例、gates
all_pass。输入缺失时跳过，不锚过程中间态（R9）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "out" / "v4-exec" / "p3-revc"
PERNET = PKG / "per-net-batch"
SNAPSHOT = PERNET / "snapshot-pristine.kicad_pcb"

pytestmark = pytest.mark.skipif(
    not (PKG.is_dir() and SNAPSHOT.is_file()),
    reason="P1-1B artifacts not present")


def _load(p):
    return json.loads(Path(p).read_bytes().decode("utf-8"))


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_snapshot_byte_identical_to_frozen_pre_hash():
    proto = _load(PKG / "protocol" / "protocol-p3-revc-v1.json")
    assert _sha(SNAPSHOT) == proto["board_source"]["pre_hash_sha256"]


def test_live_board_prl_baseline_unchanged_in_sidecar_log():
    """R2 守证终态：sidecar 日志每一行 live prl 未变、datasets 零 prl。"""
    log = PERNET / "sidecar-log.jsonl"
    assert log.is_file()
    lines = [ln for ln in
             log.read_bytes().decode("utf-8").splitlines() if ln.strip()]
    assert lines, "sidecar log empty"
    frozen = "d62c835bd79176eba5134b9c40844221fb204bccbdd2b5b31d943e2d521e3bf4"
    for ln in lines:
        entry = json.loads(ln)
        assert entry["live_prl_unchanged"] is True
        assert entry["live_prl_sha256"] == frozen
        assert entry["datasets_prl_count"] == 0


def test_batch_record_verdict_matches_independent_recompute():
    """DRC 独立可复核（终态）：从留证 DRC JSON 重算计数，须与已记录
    verdict 逻辑一致（blocked 亦可复算）。"""
    plan = _load(PERNET / "plan.json")
    for batch in plan["batches"]:
        bd = PERNET / batch
        rec = _load(bd / "batch-record.json")

        def counts(p):
            d = _load(p)
            vs = d.get("violations") or []
            return (sum(1 for v in vs if v.get("severity") == "error"),
                    len(d.get("unconnected_items") or []))

        be, bu = counts(PERNET / "baseline" / "drc-error.json")
        ce, _ = counts(bd / "drc-error.json")
        ca_u = counts(bd / "drc-all.json")[1]
        ba_u = counts(PERNET / "baseline" / "drc-all.json")[1]
        expected = "pass" if (ce == be and ca_u <= ba_u) else "blocked"
        assert rec["paired_result"] == expected
        assert rec["hash_chain"]["snapshot_sha256"] == _sha(SNAPSHOT)
        assert rec["hash_chain"]["challenger_post_hash_sha256"] == \
            _sha(bd / "challenger.kicad_pcb")
        if rec["paired_result"] == "blocked":
            rb = _load(bd / "rollback.json")
            assert rb["challenger_withdrawn"] is True
            assert rb["no_repair_no_retry"] is True
            assert rb["staging_equals_live_pre_hash"] is True


def test_rollback_drill_passed_before_batch():
    drill = _load(PERNET / "rollback-drill" / "rollback-drill.json")
    assert drill["verdict"] == "pass"
    assert drill["post_hash_sha256"] != drill["pre_hash_sha256"]
    assert drill["restored_hash_sha256"] == drill["pre_hash_sha256"]
    assert drill["checks"]["restored_drc_equals_baseline"] is True


def test_disposition_drills_three_kinds_ledger_chain_valid():
    import sys
    sys.path.insert(0, str(REPO))
    from pcbflow import ledger
    rec = _load(PKG / "dispositions" / "drill-record.json")
    assert len(rec["drills"]) >= 3
    assert set(rec["kinds"]) == {"accept", "reject", "known_open"}
    entries = _load(PKG / "dispositions" / "ledger.json")["entries"]
    assert ledger.verify_chain(entries) == []
    for e in entries:
        assert e["authority"] == "human"
        assert e["trust_level"] == "untrusted"


def test_gates_all_pass_and_experiment_result_recorded():
    gates = _load(PKG / "gates.json")
    assert gates["all_pass"] is True
    assert gates["checks"]["G3_rollback_drill_pass"] is True
    assert gates["checks"]["G4_disposition_drills_at_least_3"] is True
    assert gates["checks"]["G5_zero_sidecar_residue"] is True
    assert gates["experiment_result"] in ("pass", "blocked")


def test_p09_review_package_three_bind_and_png_hash():
    pkg = _load(PKG / "review-packages" / "P3REVC-BATCH-01" /
                "package.json")
    three = pkg["three_bind"]
    assert all(three.values()) and len(three) == 3
    assert three["board_snapshot_sha256"]
    for view in ("baseline_view", "diff_view"):
        rec = pkg[view]["png"]
        if rec.get("available"):
            name = "baseline-view.png" if view == "baseline_view" \
                else "diff-view.png"
            p = PKG / "review-packages" / "P3REVC-BATCH-01" / name
            assert _sha(p) == rec["png_sha256"]
    errs_path = PKG / "review-packages" / "P3REVC-BATCH-01" / "manifest.json"
    assert _load(errs_path)["batch_result"] in ("pass", "blocked")


def test_datasets_zero_prl_and_freeze_domain_untouched_by_package():
    """R2/R3 终态：datasets/ 零 .kicad_prl；冻结域无本包写入痕迹
    （p3-revc 包内一切文件均在自身目录下）。"""
    ds = REPO / "datasets"
    if ds.is_dir():
        assert list(ds.rglob("*.kicad_prl")) == []
    for forbidden in ("out/v4-experiment", "out/v4-comparative-experiment"):
        d = REPO / forbidden
        if d.is_dir():
            hits = [p for p in d.rglob("*")
                    if "p3-revc" in str(p)]
            assert hits == []
