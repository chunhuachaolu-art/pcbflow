# -*- coding: utf-8 -*-
r"""V5-EXECUTOR-ENG-R1 版本钉与解析面兼容钉（executor 0.9.0）。

DESIGN-DECISION §5 测试计划 C 组（C14/C15）：
  C14 EXECUTOR_VERSION=="v5.executor/0.9.0" 且 ROUTED 工件
      provenance.generator 随之；ROUTES_SCHEMA_VERSION 不变钉；
  C15 build_g1_assessment.py:68-70 解析面前缀兼容钉（FAILED after
      (\d+) attempts / exhaustion-cause= 对短路 log 成立）；per_net 与
      execute_candidate 返回面既有键面零删改钉。

fixture 只读面：boards/synth-r1/syn-u01（短路 log 面）、
out/v5-p5/exec-eng-r1/probe/adv-board.json（ROUTED 工件面）。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5.board import load_board  # noqa: E402
from v5.executor import EXECUTOR_VERSION, execute_candidate  # noqa: E402
from v5.route_check import ROUTES_SCHEMA_VERSION  # noqa: E402

SYNTH = os.path.join(ROOT, "boards", "synth-r1")
ADV_FIXTURE = os.path.join(ROOT, "out", "v5-p5", "exec-eng-r1", "probe",
                           "adv-board.json")
_PER_NET_KEYS = {"partition_id", "net_id", "status", "attempts", "negotiated",
                 "vias", "length_mm", "width_mm", "layers"}
_RESULT_KEYS = {"verdict", "routes", "per_net", "negotiation_log"}


def _cand(board):
    return {"route_order": [p["partition_id"] for p in board["partitions"]],
            "layer_assignment": {p["partition_id"]: board["stackup"][0]["id"]
                                 for p in board["partitions"]}}


def test_version_pin():
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    # （W-1 SC-1 事前短路 sealed-short-circuit+W-2 verdict_provenance
    # 出口读数面；详见 executor 模块 docstring）
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步（候选出口事件接线）
    assert ROUTES_SCHEMA_VERSION == "v5.routes.v1"   # 不变钉（零 schema 改动）


def test_version_pin_routes_generator():
    """ROUTED 工件 provenance.generator 随版本（对抗板 fixture 秒级）。"""
    with open(ADV_FIXTURE, encoding="utf-8") as f:
        board = json.load(f)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED"
    assert res["routes"]["provenance"]["generator"] == EXECUTOR_VERSION
    assert res["routes"]["schema_version"] == ROUTES_SCHEMA_VERSION


def test_parser_compat_shortcircuit_log():
    r"""短路 log 对既有解析面前缀兼容（out/v5-p5/_logs/build_g1_assessment.
    py:68-70 同款 regex：r"FAILED after \d+ attempts" 与 'exhaustion-cause='
    子串）；per_net/返回面既有键零删改。"""
    with open(os.path.join(SYNTH, "syn-u01.board.v1.json"),
              encoding="utf-8") as f:
        board = load_board(json.load(f))
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED"
    # 返回面键：既有四键零删改；verdict_provenance=纯新增可选键
    assert _RESULT_KEYS <= set(res)
    assert set(res) - _RESULT_KEYS <= {"verdict_provenance"}
    # 解析面 regex（build_g1_assessment.py:68-70 逐字同款）
    failed_re = re.compile(r"FAILED after \d+ attempts")
    assert any(failed_re.search(ln) for ln in res["negotiation_log"])
    assert any("exhaustion-cause=" in ln for ln in res["negotiation_log"])
    m = re.search(r"FAILED after (\d+) attempts", "\n".join(
        res["negotiation_log"]))
    assert m and int(m.group(1)) == 0
    # per_net 条目键集与穷举失败条目同构（零删改）
    assert res["per_net"] and set(res["per_net"][0]) == _PER_NET_KEYS
    # execute 侧既有读数面（runner 消费）：status/attempts/negotiated/layers
    pn = res["per_net"][0]
    assert pn["status"] == "failed" and pn["attempts"] == 0 \
        and pn["negotiated"] is False and pn["layers"] == []
