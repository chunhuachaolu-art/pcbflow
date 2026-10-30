"""PAPER-P1-1B 终态锚定测试（协议冻结件 + 审批一致性）。

只锚终态/不可变事实（R9）：协议 hash、预算上限、动作子集与批准件一致。
输入缺失时跳过（test_compile_revc 先例），不锚过程中间态。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "out" / "v4-exec" / "p3-revc"
PROTO = PKG / "protocol" / "protocol-p3-revc-v1.json"
APPROVAL = REPO / "out" / "v4-exec" / "p3-revc-approval" / \
    "APR-P3-REVC-r1.json"

pytestmark = pytest.mark.skipif(
    not (PROTO.is_file() and APPROVAL.is_file()),
    reason="P1-1B artifacts not present")


def _load(p):
    return json.loads(p.read_bytes().decode("utf-8"))


def test_protocol_schema_and_preregistration_priority():
    proto = _load(PROTO)
    assert proto["schema"] == "pcbflow.paperexec.p3revc-protocol/1"
    assert proto["preregistration_note"].startswith("本件冻结先于一切")
    assert proto["declared_date"] == "2026-09-12"


def test_protocol_pre_hash_matches_live_board():
    """零 live 写断言（终态）：live 板当前字节 hash == 协议冻结 pre-hash。"""
    import hashlib
    proto = _load(PROTO)
    live = REPO.parent.parent / \
        proto["board_source"]["path_workspace_relative"]
    assert live.is_file(), "live board missing"
    digest = hashlib.sha256(live.read_bytes()).hexdigest()
    assert digest == proto["board_source"]["pre_hash_sha256"]
    assert live.stat().st_size == proto["board_source"]["size_bytes"]


def test_protocol_budget_caps_frozen_concrete():
    proto = _load(PROTO)
    caps = proto["budget_caps"]
    assert caps["drc_calls_max"] == 30
    assert caps["wall_clock_hours_max"] == 5
    assert caps["token_budget_max"] == 1500000
    assert caps["batches_max"] == 3
    assert caps["nets_max"] == 30


def test_protocol_action_subset_matches_approval():
    proto = _load(PROTO)
    approval = _load(APPROVAL)
    assert proto["action_subset"]["allowed"] == \
        approval["action_subset"]["allowed"]
    assert proto["action_subset"]["allowed"] == [
        "replace_subpath", "move_vertex", "insert_via_candidate",
        "reject_route_patch"]


def test_protocol_criteria_and_drc_dual_severity():
    proto = _load(PROTO)
    assert proto["criteria"]["gate_conditions"][0].startswith(
        "零新增 severity-error")
    assert "unconnected" in proto["criteria"]["gate_conditions"][1]
    assert proto["drc_protocol"]["authority"].startswith("kicad-cli")
    assert proto["criteria"]["failure_path"].startswith(
        "任一门条件不满足")
