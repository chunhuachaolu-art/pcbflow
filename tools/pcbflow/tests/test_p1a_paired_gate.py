"""P1-A：逐板配对 adoption 机器门（proposer.adoption_gate_paired）测试。

覆盖被修正的合同缺陷（L5 逐板不回退的真实落地）：
- 跨板回退不得因全局基线被掩盖（同测试内用 legacy 门对照演示缺陷本身）；
- 配对有效性 fail-closed（缺门指标/缺侧证据/回显不一致/非法 hash →
  排除出两个分母并附原因）；
- 两个分母（板分母/执行分母）防重复板伪装多样本；
- holdout_pairs 为空=分母 0（在库语料板数不替代执行分母）；
- legacy adoption_gate 行为不变，仅新增 gate_mode 显式标记
  （global_baseline_legacy 不得用于真实采纳资格）。

依赖 cwd=pcbflow 根（既有测试约定）。纯函数测试：无 IO、无 wall-clock。
"""

from __future__ import annotations

import pytest

from pcbflow import proposer

_D = "a" * 64          # design_inputs_sha256（合法 64hex）
_L = "b" * 64          # toolchain_lock_sha256（合法 64hex）
_WL = "guard_violations"   # 白名单指标（lower_is_better）
_REQ = "route_cost"        # required 指标（lower_is_better）
_GATE_KW = dict(whitelist_metrics=(_WL,), required_metrics=(_REQ,))


def _metrics(**values):
    """两侧同构 metrics 底座：白名单 0、required 10，可逐项覆盖。"""
    m = {_WL: 0, _REQ: 10}
    m.update(values)
    return m


def _side(config_id, execution_id, output, metrics, *, board_id=None,
          profile_id=None, check_refs=None):
    """构造单侧执行证据（回显/check_refs 可选）。"""
    side = {"config_id": config_id, "execution_id": execution_id,
            "output_sha256": output, "metrics": dict(metrics)}
    if board_id is not None:
        side["board_id"] = board_id
    if profile_id is not None:
        side["profile_id"] = profile_id
    if check_refs is not None:
        side["check_refs"] = dict(check_refs)
    return side


def _pair(board_id="B-1", profile_id="P-1", *, design=_D, lock=_L,
          baseline=None, challenger=None, b_board=None, c_board=None,
          b_profile=None, c_profile=None):
    """构造一条默认有效的配对记录（同板同 profile 同设计输入/锁）。"""
    return {
        "board_id": board_id, "profile_id": profile_id,
        "design_inputs_sha256": design, "toolchain_lock_sha256": lock,
        "baseline": baseline or _side(
            "CFG-BASE", "EXEC-B-1", "c" * 64, _metrics(),
            board_id=b_board, profile_id=b_profile),
        "challenger": challenger or _side(
            "CFG-CAND", "EXEC-C-1", "d" * 64, _metrics(),
            board_id=c_board, profile_id=c_profile),
    }


def _gate(pairs, **overrides):
    kw = dict(_GATE_KW, holdout_pairs=pairs)
    kw.update(overrides)
    return proposer.adoption_gate_paired(**kw)


# ---------------------------------------------------------------------------
# 1) 跨板回退不因全局基线误放行（被修正缺陷的对照演示）
# ---------------------------------------------------------------------------

def test_cross_board_regression_not_excused_by_global_baseline():
    # 板 A：baseline=100 → challenger=100（对自身不回退，构造为有效对）
    board_a = _pair(
        board_id="A",
        baseline=_side("CFG-A0", "EXEC-A0", "c" * 64,
                       _metrics(route_cost=100.0)),
        challenger=_side("CFG-A1", "EXEC-A1", "d" * 64,
                         _metrics(route_cost=100.0)))
    # 板 B：自身 baseline=10 → challenger=20（lower is better，真实回退）
    board_b = _pair(
        board_id="B",
        baseline=_side("CFG-B0", "EXEC-B0", "e" * 64,
                       _metrics(route_cost=10.0)),
        challenger=_side("CFG-B1", "EXEC-B1", "f" * 64,
                         _metrics(route_cost=20.0)))
    paired = _gate([board_a, board_b])
    assert paired["decision"] == "reject"
    assert paired["gate_mode"] == "paired_v1"
    assert paired["holdout"]["regressed_boards"] == [
        {"profile_id": "P-1", "board_id": "B",
         "design_inputs_sha256": _D, "toolchain_lock_sha256": _L}]
    assert paired["holdout"]["non_regressed_boards"] == 1
    assert paired["holdout"]["non_regression_rate"] == 0.5
    # 对照（缺陷本身）：legacy 门把同一板 B 锚定到全局 baseline=100
    # （即板 A 的基线）——20 < 100 → 不判回退 → 放行。这就是被修正的
    # "跨板回退被全局基线掩盖"静默回退路径。
    legacy = proposer.adoption_gate(
        {_WL: 0, _REQ: 100.0}, {_WL: 0, _REQ: 20.0},
        whitelist_metrics=(_WL,), required_metrics=(_REQ,),
        holdout_results=[{"board_id": "B",
                          "metrics": {_WL: 0, _REQ: 20.0}}])
    assert legacy["decision"] == "adopt_candidate"   # 误放行（缺陷）
    assert legacy["gate_mode"] == "global_baseline_legacy"


# ---------------------------------------------------------------------------
# 2) 同板有效改善 / 持平 → 不回退
# ---------------------------------------------------------------------------

def test_same_board_improvement_and_tie_not_regressed():
    improved = _gate([_pair(challenger=_side(
        "CFG-CAND", "EXEC-C-1", "d" * 64, _metrics(route_cost=9.0)))])
    assert improved["decision"] == "adopt_candidate"
    assert improved["holdout"]["board_denominator"] == 1
    assert improved["holdout"]["non_regressed_boards"] == 1
    assert improved["holdout"]["non_regression_rate"] == 1.0
    # 持平（相等值，容差 0）不算回退
    tie = _gate([_pair(challenger=_side(
        "CFG-CAND", "EXEC-C-1", "d" * 64, _metrics(route_cost=10.0)))])
    assert tie["decision"] == "adopt_candidate"
    assert tie["holdout"]["violations"] == []
    assert tie["human_adoption_required"] is True    # 机器门 ≠ adoption


# ---------------------------------------------------------------------------
# 3) 真实回退 → reject；方向反转（higher_is_better challenger 更低）→ 回退
# ---------------------------------------------------------------------------

def test_true_regression_and_direction_reversal_reject():
    regressed = _gate([_pair(challenger=_side(
        "CFG-CAND", "EXEC-C-1", "d" * 64, _metrics(route_cost=11.0)))])
    assert regressed["decision"] == "reject"
    assert regressed["per_metric"][_REQ][0]["regressed"] is True
    assert regressed["per_metric"][_REQ][0]["board_id"] == "B-1"
    assert regressed["per_metric"][_REQ][0]["delta"] == 1.0
    # 方向反转：higher_is_better 指标 challenger 更低 → 回退
    pair = _pair(
        baseline=_side("CFG-BASE", "EXEC-B-1", "c" * 64,
                       {_WL: 0, "yield_rate": 0.90}),
        challenger=_side("CFG-CAND", "EXEC-C-1", "d" * 64,
                         {_WL: 0, "yield_rate": 0.85}))
    flipped = proposer.adoption_gate_paired(
        whitelist_metrics=("yield_rate",), required_metrics=(),
        holdout_pairs=[pair],
        metric_directions={"yield_rate": "higher_is_better"})
    assert flipped["decision"] == "reject"
    assert [v["metric"] for v in flipped["whitelist_violations"]] == \
        ["yield_rate"]
    # 未声明方向时保守按 lower_is_better：0.85 会被判"改善"（不回退），
    # 方向声明是调用方的合同义务
    conservative = proposer.adoption_gate_paired(
        whitelist_metrics=("yield_rate",), required_metrics=(),
        holdout_pairs=[pair])
    assert conservative["decision"] == "adopt_candidate"


# ---------------------------------------------------------------------------
# 4) 单侧缺门指标 → 配对无效 → no_valid_pairs → blocked
# ---------------------------------------------------------------------------

def test_one_side_missing_metric_no_valid_pairs_blocked():
    bad = _pair(challenger=_side(
        "CFG-CAND", "EXEC-C-1", "d" * 64, {_WL: 0}))   # challenger 缺 _REQ
    result = _gate([bad])
    assert result["decision"] == "blocked"
    assert any("no_valid_pairs" in r for r in result["reasons"])
    assert result["holdout"]["board_denominator"] == 0
    assert result["holdout"]["execution_denominator"] == 0
    assert len(result["holdout"]["excluded_pairs"]) == 1
    assert any("challenger.metric_missing" in r
               for r in result["holdout"]["excluded_pairs"][0]["reasons"])


# ---------------------------------------------------------------------------
# 5) 缺 baseline 侧证据（缺 execution_id / output_sha256）→ 配对无效
# ---------------------------------------------------------------------------

def test_missing_baseline_side_evidence_pair_invalid():
    no_exec = _pair(baseline={"config_id": "CFG-BASE",
                              "output_sha256": "c" * 64,
                              "metrics": _metrics()})
    result = _gate([no_exec])
    assert result["decision"] == "blocked"
    assert any("baseline.execution_id_invalid" in r
               for r in result["holdout"]["excluded_pairs"][0]["reasons"])
    bad_output = _pair()
    bad_output["baseline"]["output_sha256"] = "NOTAHASH"
    result2 = _gate([bad_output])
    assert result2["decision"] == "blocked"
    assert any("baseline.output_sha256_invalid" in r
               for r in result2["holdout"]["excluded_pairs"][0]["reasons"])


# ---------------------------------------------------------------------------
# 6) 回显 board_id/profile_id 不一致（错板/错 profile）→ 配对无效
# ---------------------------------------------------------------------------

def test_echo_board_or_profile_mismatch_pair_invalid():
    wrong_board = _pair(c_board="OTHER-BOARD")
    result = _gate([wrong_board])
    assert result["decision"] == "blocked"
    assert any("challenger.board_id_echo_mismatch" in r
               for r in result["holdout"]["excluded_pairs"][0]["reasons"])
    wrong_profile = _pair(b_profile="OTHER-PROFILE")
    result2 = _gate([wrong_profile])
    assert result2["decision"] == "blocked"
    assert any("baseline.profile_id_echo_mismatch" in r
               for r in result2["holdout"]["excluded_pairs"][0]["reasons"])


# ---------------------------------------------------------------------------
# 7) 重复板：板分母计 1、执行分母计 2；决策按板数判
# ---------------------------------------------------------------------------

def test_duplicate_board_counts_once_in_board_denominator():
    p1 = _pair()
    p2 = _pair()                       # 同 (profile, board, design, lock) 组
    p2["challenger"] = _side("CFG-CAND2", "EXEC-C-2", "e" * 64,
                             _metrics(route_cost=9.0))
    result = _gate([p1, p2])
    assert result["holdout"]["board_denominator"] == 1
    assert result["holdout"]["execution_denominator"] == 2
    assert result["decision"] == "adopt_candidate"     # 有效板 1 ≥ min 1
    # 决策按板数判：min_holdout_boards=2 时 1 板不足 → blocked
    blocked = _gate([p1, p2], min_holdout_boards=2)
    assert blocked["decision"] == "blocked"
    assert any("holdout_pairs_insufficient" in r for r in blocked["reasons"])


# ---------------------------------------------------------------------------
# 8) hash 格式非法 → 配对无效
# ---------------------------------------------------------------------------

def test_invalid_hash_format_pair_invalid():
    bad_design = _pair(design="zzz")           # 非 64hex
    result = _gate([bad_design])
    assert result["decision"] == "blocked"
    assert any("design_inputs_sha256_invalid" in r
               for r in result["holdout"]["excluded_pairs"][0]["reasons"])
    bad_output = _pair()
    bad_output["challenger"]["output_sha256"] = "A" * 64   # 大写非法
    result2 = _gate([bad_output])
    assert result2["decision"] == "blocked"
    assert any("challenger.output_sha256_invalid" in r
               for r in result2["holdout"]["excluded_pairs"][0]["reasons"])


# ---------------------------------------------------------------------------
# 9) holdout_pairs=[] → blocked（在库 holdout 数量不能替代执行分母）
# ---------------------------------------------------------------------------

def test_empty_holdout_pairs_blocked_zero_execution_denominator():
    result = _gate([])
    assert result["decision"] == "blocked"
    assert any("holdout_pairs_missing" in r for r in result["reasons"])
    assert result["holdout"]["board_denominator"] == 0
    assert result["holdout"]["execution_denominator"] == 0
    assert result["holdout"]["non_regression_rate"] == 0.0
    # 本用例即分母 0：库内 holdout 语料板数（哪怕 12 板）不能替代
    # 执行分母——逐板配对执行证据必须真实存在才能计入分母


# ---------------------------------------------------------------------------
# 10) legacy 门行为不变（冒烟）+ gate_mode 显式标记
# ---------------------------------------------------------------------------

def test_legacy_gate_unchanged_smoke_with_gate_mode():
    result = proposer.adoption_gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4},
        whitelist_metrics=(_WL,), required_metrics=(_REQ,),
        holdout_results=[{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 4}},
                         {"board_id": "HB-2",
                          "metrics": {_WL: 0, _REQ: 5}}])
    assert result["decision"] == "adopt_candidate"
    assert result["holdout"]["denominator"] == 2       # 旧结构键不变
    assert result["holdout"]["non_regressed_boards"] == 2
    assert result["human_adoption_required"] is True
    assert result["gate_mode"] == "global_baseline_legacy"  # P1-A 新增键
    blocked = proposer.adoption_gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4},
        whitelist_metrics=(_WL,), required_metrics=(_REQ,),
        holdout_results=[])
    assert blocked["decision"] == "blocked"
    assert any("holdout_missing" in r for r in blocked["reasons"])


# ---------------------------------------------------------------------------
# 补充：排除对不污染有效分母；非法入参 ValueError（fail-closed）
# ---------------------------------------------------------------------------

def test_excluded_pairs_do_not_poison_valid_denominators():
    good = _pair(board_id="GOOD")
    bad = _pair(board_id="BAD", design="short")
    result = _gate([good, bad])
    assert result["holdout"]["board_denominator"] == 1
    assert result["holdout"]["execution_denominator"] == 1
    assert len(result["holdout"]["excluded_pairs"]) == 1
    assert result["holdout"]["excluded_pairs"][0]["pair_index"] == 1
    assert result["decision"] == "adopt_candidate"


def test_invalid_inputs_raise_valueerror_fail_closed():
    with pytest.raises(ValueError):
        _gate([_pair()], min_holdout_boards=0)
    with pytest.raises(ValueError):
        _gate([_pair()], min_holdout_boards=True)   # bool 不算整数
    with pytest.raises(ValueError):
        proposer.adoption_gate_paired(
            whitelist_metrics=(_WL,), required_metrics=(_REQ,),
            holdout_pairs="not-a-list")
    with pytest.raises(ValueError):
        _gate([_pair()], metric_directions={_REQ: "sideways"})
