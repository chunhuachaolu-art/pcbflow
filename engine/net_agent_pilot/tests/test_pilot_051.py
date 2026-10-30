# -*- coding: utf-8 -*-
"""pilot 0.5.1 回归: slice 轮号防呆（F-4）+ ripup 重验对照披露（F-3）。

F-3 以真实数据金标锚定: run11-armB 撤 +3V3 的分叉（=run12 起点，已收口
DISPATCH-LOG 2026-09-28）复跑必须产出 revived/dropped 计数、网集与尾态
哈希逐位一致（披露纯增量、行为零漂移）。板/源账只读（conftest
badgeleds 先例），分叉产物写 tmp。
0.6.0（V8-PILOT-060 D-6）金标重锚: anchor_semantics v2 串入 state_facts
哈希 ⟹ v1 时代尾态锚不复算（世界漂移非回归）——期望值由复算程序化提取
注入（out/net-agent-p1/pilot06/reanchor_golden.py），旧值以注释保留为
迁移对照。
"""
import argparse
import contextlib
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from net_agent_pilot import pilot

_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOARD = os.path.join(_ROOT, "out", "v5-p5", "boards", "pmod-crypto",
                     "board.json")
SRC_RUN = os.path.join(_ROOT, "out", "net-agent-p1", "run11-armB")
# 金标重锚（V8-PILOT-060 D-6, 2026-10-04）: canvas anchor_semantics v2 串入
# state_facts 哈希 ⟹ v1 时代锚不复算（世界漂移非回归）。新值由复算程序化
# 提取注入（out/net-agent-p1/pilot06/reanchor_golden.py; 禁手抄），旧值以
# 注释保留为迁移对照（old→new）:
#   EXPECT_TAIL:    '4251d356554db1a5' → '04360108e62baea0' (漂移)
#   EXPECT_N_REVIVED: 8 → 8 (不变)
#   EXPECT_N_DROPPED: 7 → 7 (不变)
#   EXPECT_REVIVED_NETS: ['/IO1', '/RESET', '/SCL', '/SDA', 'GND'] → ['/IO1', '/RESET', '/SCL', '/SDA', 'GND'] (不变)
#   EXPECT_DROPPED_NETS: ['/SDA', 'GND', 'Net-(R1-Pad2)'] → ['/SDA', 'GND', 'Net-(R1-Pad2)'] (不变)
EXPECT_TAIL = "04360108e62baea0"
EXPECT_N_REVIVED = 8
EXPECT_N_DROPPED = 7
EXPECT_REVIVED_NETS = {"/IO1", "/RESET", "/SCL", "/SDA", "GND"}
EXPECT_DROPPED_NETS = {"/SDA", "GND", "Net-(R1-Pad2)"}


@pytest.fixture(scope="module")
def fork(tmp_path_factory):
    d = tmp_path_factory.mktemp("fork")
    new = str(d / "run12-gold")
    with contextlib.redirect_stdout(io.StringIO()):
        pilot.cmd_ripup(argparse.Namespace(
            board=BOARD, run=SRC_RUN, new_run=new, net="+3V3"))
    return new


def test_ripup_revalidation_golden(fork):
    rj = json.load(open(os.path.join(fork, "ripup.json"), encoding="utf-8"))
    assert rj["schema_version"] == "net-agent-p1/ripup-v2"
    rev = rj["revalidation"]
    # 行为零漂移: 分叉尾态与 run12 收口锚逐位一致
    assert rj["final_state_sha256"].startswith(EXPECT_TAIL)
    assert rev["n_revived"] == EXPECT_N_REVIVED and \
        rev["n_dropped"] == EXPECT_N_DROPPED
    assert {e["net_id"] for e in rev["revived"]} == EXPECT_REVIVED_NETS
    assert {e["net_id"] for e in rev["dropped"]} == EXPECT_DROPPED_NETS
    # dropped 全带拒收码（挤掉面可归因）
    assert all(e["code"] for e in rev["dropped"])
    # 分叉链完整性
    with contextlib.redirect_stdout(io.StringIO()):
        pilot.cmd_verify(argparse.Namespace(board=BOARD, run=fork))


def test_slice_round_guard(fork):
    # 倒退轮号: 拒切（+3V3 在分叉态未连通，可切）
    with pytest.raises(SystemExit) as ei:
        pilot.cmd_slice(argparse.Namespace(
            board=BOARD, run=fork, net="+3V3", round=1, tag=None,
            prior_rejection=None, playbook=None))
    assert "倒退" in str(ei.value)
    # 超前 >1: 并行预留允许 + warn 披露（尾轮 16 → next 17）
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        pilot.cmd_slice(argparse.Namespace(
            board=BOARD, run=fork, net="+3V3", round=20, tag="guard-probe",
            prior_rejection=None, playbook=None))
    first = json.loads(buf.getvalue().splitlines()[0])
    assert first["warn"] == "round_ahead" and first["next"] == 17
    # 缺省: 尾轮+1 自动对齐
    with contextlib.redirect_stdout(io.StringIO()):
        pilot.cmd_slice(argparse.Namespace(
            board=BOARD, run=fork, net="+3V3", round=None, tag=None,
            prior_rejection=None, playbook=None))
    assert os.path.isfile(os.path.join(
        fork, "rounds", "r17-3V3", "brief.md"))
