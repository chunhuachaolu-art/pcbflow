# -*- coding: utf-8 -*-
"""canvas.loop 测试（Lane-K2）。

桩仅测试用、非平行实现；真件集成由编排体冒烟（loop↔protocol、apply 缝）。
覆盖：链式哈希台账双跑字节等（≥2）、链完整性、轮语义（applied/
batch-rejected/seat-stop）、replay 重放一致性+防篡改 fail-closed、
parser/apply 缝未接线 fail-closed。
"""

import json
import os
import sys

import pytest

from v5.canonical import canonical_json, canonical_sha256, sha256_bytes

from canvas.loop import ZERO_SHA, RunLoop, replay
from canvas.tests.test_k2_pack import StubState

REAL_BOARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "out", "v5-p5", "boards", "badgeleds-do-electronics", "board.json")


# ---------------------------------------------------------------------------
# 桩 parser / 桩 seat（确定性回放器）——仅测试用，非平行实现
# ---------------------------------------------------------------------------

class BatchReject(Exception):
    """桩批拒收（对齐 canvas.protocol.BatchReject 形态：code/detail）。"""

    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__("[%s] %s" % (code, detail))


def stub_parser(text, expected_round):
    """合同签名桩 parse_batch(text, expected_round)：JSON 批 + 轮号核验。"""
    batch = json.loads(text)
    if batch.get("round") != expected_round:
        raise BatchReject("E_ROUND_MISMATCH",
                          "期望 %r 实得 %r" % (expected_round, batch.get("round")))
    return batch["actions"]


def seat_script(script):
    """确定性回放器 seat_fn 桩：round->actions_text；未轮=停车 None。"""
    def seat(round_no, pack):
        assert "svg" in pack and "facts_json" in pack and "view_spec" in pack
        return script.get(round_no)
    return seat


BATCH_R1 = json.dumps({"round": 1, "actions": [
    {"action": "route", "net_id": "N1", "waypoints": [[0, 0], [1, 0]],
     "layer": "F.Cu"},
    {"action": "via", "net_id": "N1", "grid": [1, 0]},
    {"action": "submit"},
]})
BATCH_R2 = json.dumps({"round": 2, "actions": [
    {"action": "ripup", "shape_id": "seg:N1:nope"},   # 拒收（V_RIPUP_UNKNOWN）
    {"action": "route", "net_id": "N2", "waypoints": [[5, 0], [5, 2]],
     "layer": "B.Cu"},
    {"action": "submit"},
]})
BATCH_R2_BAD_ROUND = json.dumps({"round": 99, "actions": [
    {"action": "submit"}]})


def _run_two_rounds(ledger_path):
    st = StubState()
    seat = seat_script({1: BATCH_R1, 2: BATCH_R2})
    loop = RunLoop(st, ledger_path, seat, parser=stub_parser)
    return loop.run(max_rounds=5), st


def test_ledger_double_run_byte_equal(tmp_path):
    """确定性双跑字节等 ≥2：同初始态+同 seat/parser → 3 份台账两两逐字节等。"""
    paths = [str(tmp_path / ("ledger%d.jsonl" % i)) for i in range(3)]
    for p in paths:
        summary, _ = _run_two_rounds(p)
        assert summary["rounds_logged"] == 2
    blobs = [open(p, "rb").read() for p in paths]
    assert blobs[0] == blobs[1] == blobs[2]
    assert len(blobs[0].splitlines()) == 2


def test_ledger_chain_and_canonical(tmp_path):
    """首行 prev=64×"0"；逐行 prev=上行字节哈希；行=canonical_json。"""
    ledger = str(tmp_path / "ledger.jsonl")
    summary, st = _run_two_rounds(ledger)
    prev = ZERO_SHA
    with open(ledger, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    for i, line in enumerate(lines):
        record = json.loads(line.decode("utf-8"))
        assert record["prev_sha256"] == prev
        assert canonical_json(record) + b"\n" == line  # canonical 行
        assert record["round"] == i + 1
        prev = sha256_bytes(line)
    assert summary["final_state_sha256"] == st.state_sha256()
    assert json.loads(lines[1])["prev_sha256"] == sha256_bytes(lines[0])


def test_round_semantics_accepted_rejected_edit_list(tmp_path):
    """轮1 全接受；轮2 ripup 拒收进 rejected（码/明细），edit_list 只含接受动作。"""
    ledger = str(tmp_path / "ledger.jsonl")
    _, st = _run_two_rounds(ledger)
    with open(ledger, encoding="utf-8") as f:
        r1, r2 = [json.loads(l) for l in f.read().splitlines()]
    assert r1["verdict"] == "applied"
    assert [a["action"] for a in r1["accepted"]] == ["route", "via", "submit"]
    assert r1["rejected"] == []
    assert [a["action"] for a in r1["edit_list"]] == ["route", "via", "submit"]
    assert r2["verdict"] == "applied"
    assert len(r2["rejected"]) == 1 and r2["rejected"][0]["code"] == \
        "V_RIPUP_UNKNOWN"
    assert [a["action"] for a in r2["accepted"]] == ["route", "submit"]
    # 台账态哈希=轮末桩态哈希（edit_list 重放源）
    assert r2["state_sha256"] == st.state_sha256()
    # actions_sha256=席位原始输出哈希
    assert r1["actions_sha256"] == sha256_bytes(BATCH_R1.encode("utf-8"))


def test_batch_rejected_round_continues(tmp_path):
    """批拒收轮落行（verdict=batch-rejected、edit_list=[]）且循环继续。"""
    st = StubState()
    seat = seat_script({1: BATCH_R2_BAD_ROUND, 2: BATCH_R2})  # 轮2 给 round=2 批
    ledger = str(tmp_path / "ledger.jsonl")
    summary = RunLoop(st, ledger, seat, parser=stub_parser).run(max_rounds=5)
    assert summary["rounds_logged"] == 2
    assert summary["verdicts"] == ["batch-rejected", "applied", "seat-stop"]
    with open(ledger, encoding="utf-8") as f:
        r1, r2 = [json.loads(l) for l in f.read().splitlines()]
    assert r1["verdict"] == "batch-rejected" and r1["edit_list"] == []
    assert r1["rejected"][0]["code"] == "E_ROUND_MISMATCH"
    assert r2["verdict"] == "applied"


def test_seat_stop_no_line(tmp_path):
    """席位停车（None）→ 循环结束不落轮次行。"""
    st = StubState()
    ledger = str(tmp_path / "ledger.jsonl")
    summary = RunLoop(st, ledger, seat_script({}), parser=stub_parser).run(
        max_rounds=3)
    assert summary["rounds_logged"] == 0
    assert summary["verdicts"] == ["seat-stop"]
    assert not os.path.exists(ledger)


def test_max_rounds_cap(tmp_path):
    """max_rounds 尽 → 正常收束（seat 仍有后续轮也不跑）。"""
    st = StubState()
    seat = seat_script({1: BATCH_R1, 2: BATCH_R1.replace('"round": 1',
                                                         '"round": 2')})
    ledger = str(tmp_path / "ledger.jsonl")
    summary = RunLoop(st, ledger, seat, parser=stub_parser).run(max_rounds=1)
    assert summary["rounds_logged"] == 1
    with open(ledger, encoding="utf-8") as f:
        assert len(f.read().splitlines()) == 1


def test_append_guard_and_resume(tmp_path):
    """非追加模式拒覆盖既有台账；append=True 续链 prev 正确。"""
    ledger = str(tmp_path / "ledger.jsonl")
    _run_two_rounds(ledger)
    with pytest.raises(ValueError, match="防覆盖混链"):
        _run_two_rounds(ledger)
    st = StubState()
    seat = seat_script({3: BATCH_R2.replace('"round": 2', '"round": 3')})
    RunLoop(st, ledger, seat, parser=stub_parser).run(max_rounds=1,
                                                      append=True)
    with open(ledger, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    assert len(lines) == 3
    assert json.loads(lines[2])["prev_sha256"] == sha256_bytes(lines[1])


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------

def test_replay_consistency(tmp_path):
    """replay：链核验+edit_list 重放 → 终态哈希=台账末行=run 终态。"""
    ledger = str(tmp_path / "ledger.jsonl")
    summary, st = _run_two_rounds(ledger)
    # board_path 用真板 wrap 件（v5.board.load_board 校验链走真件锚）
    final = replay(ledger, REAL_BOARD_PATH,
                   state_factory=lambda board, path: StubState())
    assert final.state_sha256() == summary["final_state_sha256"]
    assert final.state_sha256() == st.state_sha256()


def test_replay_tampered_chain_fail_closed(tmp_path):
    """台账篡改（首行内容变动致次行 prev 失配）→ 链核验 fail-closed。"""
    ledger = str(tmp_path / "ledger.jsonl")
    _run_two_rounds(ledger)
    with open(ledger, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    record = json.loads(lines[0])
    record["tampered"] = True  # 首行字节变 → sha256 变 → 次行 prev 失配
    lines[0] = canonical_json(record) + b"\n"
    with open(ledger, "wb") as f:
        f.write(b"".join(lines))
    with pytest.raises(ValueError, match="链断裂"):
        replay(ledger, REAL_BOARD_PATH,
               state_factory=lambda board, path: StubState())


def test_replay_state_divergence_fail_closed(tmp_path):
    """初始态偏移（工厂桩预置 seg）→ 轮末哈希不复算，fail-closed。"""
    ledger = str(tmp_path / "ledger.jsonl")
    _run_two_rounds(ledger)

    class SkewedState(StubState):
        def __init__(self):
            StubState.__init__(self)
            self.segs = list(self.segs) + [{
                "shape_id": "seg:N1:extra", "net_id": "N1",
                "partition_id": "PT1", "layer": "F.Cu",
                "grid": [[9, 9]], "width_class": "default"}]

    with pytest.raises(ValueError, match="不复算"):
        replay(ledger, REAL_BOARD_PATH,
               state_factory=lambda board, path: SkewedState())


# ---------------------------------------------------------------------------
# 缝 fail-closed
# ---------------------------------------------------------------------------

def test_parser_gap_fail_closed(tmp_path, monkeypatch):
    """parser 未注入且 canvas.protocol 不可用 → RuntimeError（不静默）。"""
    monkeypatch.setitem(sys.modules, "canvas.protocol", None)  # 强制 ImportError
    st = StubState()
    ledger = str(tmp_path / "ledger.jsonl")
    with pytest.raises(RuntimeError, match="parser 未注入"):
        RunLoop(st, ledger, seat_script({1: BATCH_R1})).run(max_rounds=1)


def test_apply_seam_gap_fail_closed(tmp_path):
    """st 无 apply_action（apply 缝未接线）→ RuntimeError。"""
    class NoApplyState(StubState):
        apply_action = None  # 缝摘除：_apply_via_seam 判非 callable

    st = NoApplyState()
    with pytest.raises(RuntimeError, match="apply 缝未接线"):
        RunLoop(st, str(tmp_path / "l.jsonl"), seat_script({1: BATCH_R1}),
                parser=stub_parser).run(max_rounds=1)


def test_replay_requires_state_factory(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    _run_two_rounds(ledger)
    with pytest.raises(RuntimeError, match="state_factory"):
        replay(ledger, REAL_BOARD_PATH)
