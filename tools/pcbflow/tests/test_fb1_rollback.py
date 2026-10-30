"""FB-1 单测：批回滚路径（judge 接受晋升 / 拒绝整批回滚，工作板字节保护）。

直接以 importlib 加载编排驱动（scripts/fb1_arm_orchestrate.py），monkeypatch
其 FB1_ROOT 指向 tmp_path，全流程在 tmp_path 内完成（零 Rev-C 依赖）。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "fb1_arm_orchestrate_test",
        REPO / "scripts" / "fb1_arm_orchestrate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


WORKING = b"working-board-bytes-v1\n"
CANDIDATE = b"candidate-board-bytes-v2\n"


def _drc(types_severities):
    return {"violations": [{"type": t, "severity": s,
                            "items": [{"description": d}]}
                           for (t, s, d) in types_severities],
            "unconnected_items": []}


@pytest.fixture()
def drv(tmp_path, monkeypatch):
    mod = _load_driver()
    fb1_root = tmp_path / "out" / "coreboard-fb1"
    arm = fb1_root / "armx"
    ws = arm / "workspace" / "p3-replay"
    ws.mkdir(parents=True)
    (ws / "stm32h743-coreboard-revc.kicad_pcb").write_bytes(WORKING)
    (arm / "drc-input").mkdir()
    (arm / "drc-input" / "baseline-all.json").write_text(
        json.dumps(_drc([("courtyards_overlap", "warning", "x")])),
        encoding="utf-8")
    monkeypatch.setattr(mod, "FB1_ROOT", fb1_root)
    return mod, arm, ws


def _argns(**kw):
    import argparse
    return argparse.Namespace(**kw)


def test_judge_reject_rolls_back_whole_batch(drv):
    """新增 error → 拒绝：工作板字节不动，候选板移入 rejected/，账本记录。"""
    mod, arm, ws = drv
    cand_dir = ws / "candidate"
    cand_dir.mkdir()
    (cand_dir / "stm32h743-coreboard-revc.kicad_pcb").write_bytes(CANDIDATE)
    (arm / "drc-input" / "cand.json").write_text(
        json.dumps(_drc([("clearance", "error", "AAA;BBB")])),
        encoding="utf-8")

    args = _argns(arm="armx", label="fb1-test-batch",
                  baseline=str(arm / "drc-input" / "baseline-all.json"),
                  candidate_drc=str(arm / "drc-input" / "cand.json"),
                  candidate=str(cand_dir / "stm32h743-coreboard-revc.kicad_pcb"))
    mod.cmd_judge(args)

    # 工作板字节未动（整批回滚核心断言）
    assert (ws / "stm32h743-coreboard-revc.kicad_pcb").read_bytes() == WORKING
    # 候选板存证于 rejected/
    rej = list((arm / "rejected").glob("*-board.kicad_pcb"))
    assert len(rej) == 1 and rej[0].read_bytes() == CANDIDATE
    # 账本：accepted=false + 回滚记录 + 工作板 sha 记账
    led = json.loads((arm / "batch-ledger.json").read_text(encoding="utf-8"))
    assert led["batches"][0]["accepted"] is False
    assert led["batches"][0]["new_errors_vs_baseline"] == 1
    assert led["batches"][0]["board_write"]["promoted"] is False
    assert led["batches"][0]["board_write"]["board_sha256_unchanged"] == \
        _sha_bytes(WORKING)
    assert led["rejected_batches"] == ["fb1-test-batch"]


def test_judge_accept_promotes_candidate(drv):
    """零新增 error → 接受：候选板晋升为工作板，账本记录前后 sha。"""
    mod, arm, ws = drv
    cand_dir = ws / "candidate"
    cand_dir.mkdir()
    (cand_dir / "stm32h743-coreboard-revc.kicad_pcb").write_bytes(CANDIDATE)
    (arm / "drc-input" / "cand.json").write_text(
        json.dumps(_drc([("courtyards_overlap", "warning", "x")])),
        encoding="utf-8")

    args = _argns(arm="armx", label="fb1-test-batch",
                  baseline=str(arm / "drc-input" / "baseline-all.json"),
                  candidate_drc=str(arm / "drc-input" / "cand.json"),
                  candidate=str(cand_dir / "stm32h743-coreboard-revc.kicad_pcb"))
    mod.cmd_judge(args)

    assert (ws / "stm32h743-coreboard-revc.kicad_pcb").read_bytes() == CANDIDATE
    led = json.loads((arm / "batch-ledger.json").read_text(encoding="utf-8"))
    b = led["batches"][0]
    assert b["accepted"] is True
    assert b["board_write"]["promoted"] is True
    assert b["board_write"]["board_sha256_before"] == _sha_bytes(WORKING)
    assert b["board_write"]["board_sha256_after"] == _sha_bytes(CANDIDATE)
    assert led["zero_new_errors_accepted_batches"] is True
    assert led["rejected_batches"] == []


def test_judge_reject_after_accept_keeps_zero_accepted_invariant(drv):
    """先接受后拒绝的混合序列：accepted 批零新增口径与 rejected 清单并存。"""
    mod, arm, ws = drv
    cand_dir = ws / "candidate"
    cand_dir.mkdir()

    (cand_dir / "stm32h743-coreboard-revc.kicad_pcb").write_bytes(CANDIDATE)
    (arm / "drc-input" / "cand-ok.json").write_text(
        json.dumps(_drc([])), encoding="utf-8")
    mod.cmd_judge(_argns(arm="armx", label="b1",
                         baseline=str(arm / "drc-input" / "baseline-all.json"),
                         candidate_drc=str(arm / "drc-input" / "cand-ok.json"),
                         candidate=str(cand_dir / "stm32h743-coreboard-revc.kicad_pcb")))

    (cand_dir / "stm32h743-coreboard-revc.kicad_pcb").write_bytes(b"v3\n")
    (arm / "drc-input" / "cand-bad.json").write_text(
        json.dumps(_drc([("shorting_items", "error", "A;B")])), encoding="utf-8")
    mod.cmd_judge(_argns(arm="armx", label="b2",
                         baseline=str(arm / "drc-input" / "baseline-all.json"),
                         candidate_drc=str(arm / "drc-input" / "cand-bad.json"),
                         candidate=str(cand_dir / "stm32h743-coreboard-revc.kicad_pcb")))

    led = json.loads((arm / "batch-ledger.json").read_text(encoding="utf-8"))
    assert [b["accepted"] for b in led["batches"]] == [True, False]
    assert led["zero_new_errors_accepted_batches"] is True
    assert led["zero_new_errors_so_far"] is False
    assert led["rejected_batches"] == ["b2"]
    # 终态工作板=最近一次接受批的候选（b3 被回滚未落地）
    assert (ws / "stm32h743-coreboard-revc.kicad_pcb").read_bytes() == CANDIDATE


def test_attempt_rows_filter_rejects_unknown_row(drv, tmp_path):
    mod, arm, ws = drv
    fb1_root = mod.FB1_ROOT
    (fb1_root / "ledger-61rows.json").write_text(json.dumps(
        {"rows": [{"row_id": "RPL-000", "net": "AAA", "net_id": "N001",
                   "bus_id": None, "plan_status": "SAT", "plan_fail": None,
                   "unknown_reason": None, "batch": 1,
                   "committed_in_baseline": True}]}),
        encoding="utf-8")
    args = _argns(arm="armx", ripup="true", rows="RPL-999")
    with pytest.raises(SystemExit):
        mod.cmd_attempt(args)
