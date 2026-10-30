# -*- coding: utf-8 -*-
"""转译器 v5.model_bridge 测试（主审亲做件，2026-09-14）。

覆盖：令牌表（choice_vocabulary）、五通道合同级 fail-closed、逐 combo 单项
裁决（坏令牌/未知键/部分指派缺省/去重）、候选本体合同（M-###/model-shadow/
v5.model_bridge 前缀/P3 端点直线/空 trace）、注入闸门事务式、便捷链、双跑
canonical 字节等、与 threearm 合同同锁。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pytest  # noqa: E402

from fixtures_v2 import build_v2_board  # noqa: E402
from v5 import board as bmod  # noqa: E402
from v5 import canonical, compiler, threearm  # noqa: E402
from v5.model_bridge import (MODEL_BRIDGE_VERSION, ModelBridgeError,  # noqa: E402
                             choice_vocabulary, translate,
                             translate_and_inject)

BOARD_PATH = os.path.join(os.path.dirname(__file__), "..", "boards", "d",
                          "adv-05-eqlen-vs-layerpref.board.v1.json")


@pytest.fixture(scope="module")
def board_art():
    with open(BOARD_PATH, encoding="utf-8") as f:
        b = bmod.load_board(json.load(f))
    art, _fp = compiler.compile_board(b)
    return b, art


@pytest.fixture(scope="module")
def vocab(board_art):
    b, _ = board_art
    return choice_vocabulary(b)


def _ordinal(vocab, order=None, combos=None):
    pids = sorted(vocab)
    return {
        "ranked_options": [{"label": "x"}],
        "ranked_combos": combos if combos is not None else [
            {pids[0]: vocab[pids[0]][0]}],
        "routing_order": order if order is not None else list(pids),
        "defect_scan": [],
        "principle_objection": "",
    }


# ---------------------------------------------------------------- 令牌表

def test_vocab_matches_policy_expansion(board_art, vocab):
    b, _ = board_art
    assert set(vocab) == {p["partition_id"] for p in b["partitions"]}
    for part in b["partitions"]:
        toks = vocab[part["partition_id"]]
        assert all(t.startswith("L:") for t in toks)
        assert len(toks) >= 1
    # adv-05：any 策略分区=三信号层；锁层分区=单层
    assert vocab["MS1"] == ["L:F.Cu", "L:In1.Cu", "L:B.Cu"]
    assert vocab["EQA"] == ["L:F.Cu"]


# ---------------------------------------------------------------- 合同级 fail-closed

def test_translate_rejects_bad_routing_order(board_art, vocab):
    b, art = board_art
    pids = sorted(vocab)
    with pytest.raises(ModelBridgeError) as ei:
        translate(_ordinal(vocab, order=pids[:-1]), b, art)
    assert "routing_order" in str(ei.value)
    with pytest.raises(ModelBridgeError):
        translate(_ordinal(vocab, order=pids + [pids[0]]), b, art)  # 重复


def test_translate_rejects_missing_channels(board_art, vocab):
    b, art = board_art
    o = _ordinal(vocab)
    del o["routing_order"]
    with pytest.raises(ModelBridgeError):
        translate(o, b, art)
    o = _ordinal(vocab)
    o["ranked_combos"] = {"P1": "L:F.Cu"}
    with pytest.raises(ModelBridgeError):
        translate(o, b, art)


def test_translate_empty_combos_legal(board_art, vocab):
    b, art = board_art
    out = translate(_ordinal(vocab, combos=[]), b, art)
    assert out["candidates"] == []
    assert out["report"]["accepted"] == 0


# ---------------------------------------------------------------- 逐 combo 裁决

def test_translate_combo_adjudication(board_art, vocab):
    b, art = board_art
    pids = sorted(vocab)
    good = {pids[0]: vocab[pids[0]][0], pids[3]: vocab[pids[3]][-1]}
    ordinal = _ordinal(vocab, combos=[
        dict(good, label="ok"),
        {pids[0]: "L:NOPE", "label": "bad token"},          # 令牌不在偏好集
        {pids[0]: "F.Cu", "label": "no L: prefix"},          # 缺 L: 前缀
        {"rogue": 1, "label": "unknown key"},                # 未知键
        dict(good, label="dup"),                             # 与 ok 同指派
        [1, 2],                                              # 非 dict
    ])
    out = translate(ordinal, b, art)
    assert len(out["candidates"]) == 1
    assert out["report"]["duplicates"] == 1
    reasons = [r["reason"] for r in out["report"]["rejected"]]
    assert len(reasons) == 4
    assert any("NOPE" in r for r in reasons)
    assert any("L:" in r for r in reasons)
    assert any("unknown_key" in r for r in reasons)
    assert any("not_a_dict" in r for r in reasons)
    for r in out["report"]["rejected"]:
        assert set(r) == {"index", "reason", "raw_value"}


def test_translate_partial_combo_gets_default_head(board_art, vocab):
    """部分指派：缺键分区=偏好首层（与 planner 无理念臂缺省同源）。"""
    b, art = board_art
    pids = sorted(vocab)
    out = translate(_ordinal(vocab, combos=[{pids[0]: vocab[pids[0]][0]}]), b, art)
    c = out["candidates"][0]["layer_assignment"]
    assert c[pids[0]] == vocab[pids[0]][0][2:]
    for pid in pids[1:]:
        assert c[pid] == vocab[pid][0][2:]


# ---------------------------------------------------------------- 候选本体合同

def test_candidate_shape_matches_frozen_contract(board_art, vocab):
    b, art = board_art
    out = translate(_ordinal(vocab), b, art)
    c = out["candidates"][0]
    assert c["candidate_id"] == "M-001"
    assert c["arm"] == "model-shadow"
    assert c["provenance"]["generator"] == MODEL_BRIDGE_VERSION
    assert c["provenance"]["rules_consumed"] == []
    assert c["provenance"]["compiled_sha256"] == \
        canonical.canonical_sha256(art)
    assert c["generation_trace"] == []
    for part in b["partitions"]:
        pid = part["partition_id"]
        assert c["polylines"][pid] == \
            [list(pt) for pt in part["geometry"]["endpoints"]]  # P3 端点直线
    assert sorted(c["layer_assignment"]) == sorted(c["polylines"])


def test_inject_gateway_is_transactional(board_art, vocab):
    """注入闸门二次校验+事务式：好批可入；含坏 id 的整批拒绝、arm3 原状。"""
    b, art = board_art
    arms = threearm.run_three_arms(b, art)
    good = translate(_ordinal(vocab), b, art)["candidates"]
    threearm.inject_model_candidates(arms["arm3"], good)
    assert len(arms["arm3"]["model_candidates"]) == 1

    bad = [dict(good[0], candidate_id="M-002"),
           dict(good[0], candidate_id="C-001")]      # 引擎 id 空间=违约
    with pytest.raises(threearm.ThreeArmError):
        threearm.inject_model_candidates(arms["arm3"], bad)
    assert len(arms["arm3"]["model_candidates"]) == 1  # 未半登记


def test_translate_and_inject_chain(board_art, vocab):
    b, art = board_art
    arms = threearm.run_three_arms(b, art)
    arm3, report = translate_and_inject(arms["arm3"], _ordinal(vocab), art)
    assert report["schema_version"] == "v5.mbridge-report.v1"
    assert len(arm3["model_candidates"]) == report["accepted"]
    assert len(threearm.arm3_candidates(arm3)) == \
        len(arm3["base_candidates"]) + report["accepted"]


# ---------------------------------------------------------------- 确定性

def test_double_run_canonical_byte_equal(board_art, vocab):
    b, art = board_art
    ordinal = _ordinal(vocab, combos=[
        {"MS1": "L:B.Cu"}, {"MS2": "L:In1.Cu"}, {"MS1": "L:NOPE"}])
    a = translate(ordinal, b, art)
    c = translate(ordinal, b, art)
    assert canonical.canonical_json(a) == canonical.canonical_json(c)
    assert canonical.canonical_json(a["report"]) == \
        canonical.canonical_json(c["report"])


def test_non_candidate_channels_disclosed(board_art, vocab):
    b, art = board_art
    rep = translate(_ordinal(vocab), b, art)["report"]
    assert rep["non_candidate_channels"] == ["ranked_options", "defect_scan",
                                             "principle_objection"]


# ---------------------------------------------------------------- 真席位产物回归

def test_rehearsal_seat_outputs_translate_clean():
    """彩排三席真实 output 全部 0 拒绝（链路证据的行为锁）。"""
    base = os.path.join(os.path.dirname(__file__), "..", "out", "v5-p5",
                        "rehearsal", "runs")
    with open(BOARD_PATH, encoding="utf-8") as f:
        b = bmod.load_board(json.load(f))
    art, _fp = compiler.compile_board(b)
    for seat in ("seat-shadow-b-glm1", "seat-shadow-b-glm2",
                 "seat-shadow-b-dsf"):
        path = os.path.join(base, seat, "output.json")
        if not os.path.isfile(path):
            continue  # 证据目录缺席时跳过（不造红灯）
        with open(path, encoding="utf-8") as f:
            ordinal = json.load(f)
        rep = translate(ordinal, b, art)["report"]
        assert rep["rejected"] == [], (seat, rep["rejected"])
        assert rep["accepted"] >= 1
