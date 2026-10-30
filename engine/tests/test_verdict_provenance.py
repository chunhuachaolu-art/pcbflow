# -*- coding: utf-8 -*-
"""V5-EXECUTOR-ENG-R1 W-2 verdict_provenance 字段钉（executor 0.9.0）。

DESIGN-DECISION §5 测试计划 B 组：
  B9 可布 fixture 经 select=UNKNOWN → ROUTED 且值逐字=executor-renegotiated
     短语（PREREG E-J4 L34 原文逐字嵌入）；
  B10 §3 取值表全组合表驱动钉（纯函数面）；
  B11 带/不带 kwarg 双跑 routes+negotiation_log canonical 字节等（纯读数）；
  B12 selection_verdict 非法值 → ExecutorError（fail-closed）；
  B13 E-J4 重点案例 syn-r02 全量（UNKNOWN→ROUTED+短语）+r05/r07/r10
      判定器级零触发（批级读数走 runner 复跑）。

fixture 只读面：boards/synth-r1、out/v5-p5/exec-eng-r1/probe/adv-board.json。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import load_board  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import (ExecutorError, execute_candidate,  # noqa: E402
                         _verdict_provenance)
from v5.planner import plan_candidates  # noqa: E402
from v5.selection import select_best  # noqa: E402
from v5.executor import _BoardView, _Context, _seal_survey_rows  # noqa: E402
from v5 import executor as EX  # noqa: E402

SYNTH = os.path.join(ROOT, "boards", "synth-r1")
ADV_FIXTURE = os.path.join(ROOT, "out", "v5-p5", "exec-eng-r1", "probe",
                           "adv-board.json")
PHRASE_UNKNOWN_ROUTED = "executor-renegotiated（终态出自执行器重协商，非 selection 直选）"
PHRASE_SAT_ROUTED = "selection-certified（selection 直选候选，执行器落实布通）"
PHRASE_UNSAT_ROUTED = ("contradictory-selection-unsat（selection UNSAT 而执行器"
                       "布通——口径冲突，须披露复核）")
PHRASE_FAILED_SHORT = ("execute-short-circuit:sealed-short-circuit"
                       "（事前短路：全层异网固定铜密封构造性无解）")
PHRASE_FAILED_EXH = "execute-exhausted（终态出自执行器穷举失败，非 selection 判定）"


def _load_synth(bid):
    with open(os.path.join(SYNTH, "%s.board.v1.json" % bid),
              encoding="utf-8") as f:
        return load_board(json.load(f))


def _cand(board):
    return {"route_order": [p["partition_id"] for p in board["partitions"]],
            "layer_assignment": {p["partition_id"]: board["stackup"][0]["id"]
                                 for p in board["partitions"]}}


def _unknown_routed_board(bid):
    """selection=UNKNOWN（fail-closed 滤除≠不可布）而执行器可布通的板：
    返回 (board, 首个布通候选)；断言 selection 终选读数=UNKNOWN。"""
    board = _load_synth(bid)
    c_art, _fp = compile_board(board)
    cands = plan_candidates(board, c_art)
    res = select_best(board, cands)
    assert res["verdict"] == "UNKNOWN", res["verdict"]
    assert res["best"] is None
    return board, cands[0]


# ------------------------------------------------ B9 UNKNOWN→ROUTED 短语

def test_provenance_unknown_routed_phrase():
    board, cand = _unknown_routed_board("syn-r02")
    res = execute_candidate(board, cand, selection_verdict="UNKNOWN")
    assert res["verdict"] == "ROUTED"
    assert res["verdict_provenance"] == PHRASE_UNKNOWN_ROUTED


# ------------------------------------------------ B10 取值表全组合

def test_provenance_matrix():
    assert _verdict_provenance("ROUTED", "UNKNOWN") == PHRASE_UNKNOWN_ROUTED
    assert _verdict_provenance("ROUTED", "SAT") == PHRASE_SAT_ROUTED
    assert _verdict_provenance("ROUTED", "UNSAT") == PHRASE_UNSAT_ROUTED
    assert _verdict_provenance("FAILED", "UNKNOWN") == PHRASE_FAILED_EXH
    assert _verdict_provenance("FAILED", "SAT") == PHRASE_FAILED_EXH
    assert _verdict_provenance("FAILED", "UNSAT", short_circuit=True) == \
        PHRASE_FAILED_SHORT
    # kwarg 未提供（None）→ 键省略（纯函数返回 None）
    for verdict in ("ROUTED", "FAILED"):
        assert _verdict_provenance(verdict, None) is None
    # token（中文释义）式：机器可按「（」前缀切分
    for tok in (PHRASE_UNKNOWN_ROUTED, PHRASE_SAT_ROUTED,
                PHRASE_UNSAT_ROUTED, PHRASE_FAILED_SHORT, PHRASE_FAILED_EXH):
        assert "（" in tok and tok.split("（")[0]


# ------------------------------------------------ B11 纯读数（双跑字节等）

def test_provenance_readout_only():
    with open(ADV_FIXTURE, encoding="utf-8") as f:
        board = json.load(f)
    cand = _cand(board)
    plain = execute_candidate(board, cand)
    with_kw = execute_candidate(board, cand, selection_verdict="UNKNOWN")
    assert plain["verdict"] == with_kw["verdict"] == "ROUTED"
    assert "verdict_provenance" not in plain   # 缺省省键=主线字节等
    assert canonical.canonical_json(plain["routes"]) == \
        canonical.canonical_json(with_kw["routes"])
    assert canonical.canonical_json(plain["negotiation_log"]) == \
        canonical.canonical_json(with_kw["negotiation_log"])
    assert canonical.canonical_json(plain["per_net"]) == \
        canonical.canonical_json(with_kw["per_net"])


# ------------------------------------------------ B12 kwarg 合同

@pytest.mark.parametrize("bad", ["sat", "SAT ", "", "FOO", 1, True, [],
                                 object()])
def test_provenance_contract(bad):
    with pytest.raises(ExecutorError, match="selection_verdict"):
        execute_candidate({}, {}, selection_verdict=bad)


def test_provenance_contract_valid_values_accepted():
    """合法受值面（None/三态）经 kwarg 校验不抛（板面另核；对抗板秒级）。"""
    with open(ADV_FIXTURE, encoding="utf-8") as f:
        board = json.load(f)
    cand = _cand(board)
    for v in ("SAT", "UNSAT", "UNKNOWN"):
        res = execute_candidate(board, cand, selection_verdict=v)
        assert "verdict_provenance" in res
    res = execute_candidate(board, cand)
    assert "verdict_provenance" not in res


# ------------------------------------------------ B13 E-J4 重点案例

def test_provenance_4boards_pin():
    """syn-r02 全量：UNKNOWN→ROUTED+短语逐字；r05/r07/r10 判定器级零触发
    （E-J4 批级读数走 runner 复跑，DESIGN §4）。"""
    board, cand = _unknown_routed_board("syn-r02")
    res = execute_candidate(board, cand, selection_verdict="UNKNOWN")
    assert res["verdict"] == "ROUTED"
    assert res["verdict_provenance"] == PHRASE_UNKNOWN_ROUTED
    for bid in ("syn-r05", "syn-r07", "syn-r10"):
        b = _load_synth(bid)
        view = _BoardView(b)
        route_order, _assign = EX._validate_candidate(b, _cand(b))
        rows = _seal_survey_rows(_Context(b), route_order)
        assert rows and not [r for r in rows if r["sealed"]], bid
