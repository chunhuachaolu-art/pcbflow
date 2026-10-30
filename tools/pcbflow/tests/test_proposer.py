"""proposer 模块合成测试（SPEC-v3.0 TD11/TD3/TD2）。

全部合成数据：patch/搜索空间/指标/holdout 板均为手工构造，
不依赖真实板卡、外部执行或既有产物。
"""

from pcbflow import proposer

# ---------------------------------------------------------------------------
# 合成工厂
# ---------------------------------------------------------------------------

_BASE_HASH = "a" * 64
_ALLOWLIST = ("policy/route_params.json", "toolchain/lock.json")


def _patch(**overrides):
    """合法 proposal patch（TD11 schema 全字段；operation_kind 默认白名单类）。"""
    patch = {
        "schema_version": "3.0",
        "patch_id": "P-0001",
        "base_revision": "rev-0001",
        "base_artifact_hash": _BASE_HASH,
        "target_scope": "policy",
        "operation_kind": "policy_parameter_candidate",
        "changes": [{"path": "policy/route_params.json", "op": "set",
                     "value": {"via_cost": 4}}],
        "preconditions": [],
        "expected_affected_nodes": ["policy/route_params.json"],
        "rollback_plan": "恢复 base_revision 的 policy/route_params.json",
        "proposer_id": "proposer-alpha",
        "rationale": "合成测试 patch",
        "evidence_refs": ["b" * 64],
        "random_seed": 42,
        "determinism_claim": "byte_exact",
        "execution_allowed": False,
    }
    patch.update(overrides)
    return patch


def _space(**overrides):
    """合法搜索空间声明（TD3：数值/枚举参数 + 真实执行比例）。"""
    space = {
        "schema_version": "3.0",
        "space_id": "SS-0001",
        "profile_id": "revc-tbd1",
        "parameters": [
            {"name": "via_cost", "kind": "integer",
             "domain": {"values": [4], "min": 2, "max": 8, "step": 2}},
            {"name": "optimizer", "kind": "enum",
             "domain": {"values": ["cmaes", "sweep"]}},
        ],
        "max_parameter_count": 8,
        "explore_real_execution_ratio": 0.2,
    }
    space.update(overrides)
    return space


# 指标键名（与 proposer._OBJECTIVE_LAYOUT 约定一致）
_T1 = "hard_constraint_violations"
_T2 = "whitelist_guard_violations"
_T3A = "drc_batch_severity_error"
_T3B = "drc_final_severity_all"
_T4 = "route_success_rate"
_T5 = "resource_margin"
_T6A = "via_count"
_T6B = "layer_changes"
_T6C = "length_deviation"


def _full_metrics():
    return {
        _T1: 0, _T2: 0, _T3A: 0, _T3B: 3, _T4: 0.95, _T5: 0.12,
        _T6A: 120, _T6B: 40, _T6C: 0.8,
    }


# ---------------------------------------------------------------------------
# validate_patch（TD11）
# ---------------------------------------------------------------------------

def test_validate_patch_all_allowed_kinds_pass():
    for kind in proposer.ALLOWED_OPERATION_KINDS:
        assert proposer.validate_patch(
            _patch(operation_kind=kind), _ALLOWLIST) == [], kind


def test_validate_patch_forbidden_kinds_rejected():
    for kind in proposer.FORBIDDEN_OPERATION_KINDS:
        errors = proposer.validate_patch(
            _patch(operation_kind=kind), _ALLOWLIST)
        assert errors, kind
        # 语义层必须显式提到该禁类（schema enum 报错之外补明确提示）
        assert any(kind in e for e in errors), (kind, errors)


def test_validate_patch_execution_allowed_true_rejected():
    errors = proposer.validate_patch(_patch(execution_allowed=True), _ALLOWLIST)
    assert errors
    assert any("execution_allowed" in e for e in errors)


def test_validate_patch_path_outside_allowlist_rejected():
    patch = _patch(changes=[{"path": "board/out.kicad_pcb",
                             "op": "set", "value": {}}])
    errors = proposer.validate_patch(patch, _ALLOWLIST)
    assert errors
    assert any("board/out.kicad_pcb" in e for e in errors)
    # 空白名单 fail-closed：所有 path 一律拒绝
    assert proposer.validate_patch(_patch(), ())


def test_validate_patch_base_hash_must_be_64_hex():
    errors = proposer.validate_patch(
        _patch(base_artifact_hash="XYZ"), _ALLOWLIST)
    assert errors
    assert any("base_artifact_hash" in e for e in errors)


# ---------------------------------------------------------------------------
# evaluate_patch（TD11 分级；永不 auto_apply）
# ---------------------------------------------------------------------------

def test_evaluate_patch_eligible_for_adoption_flow():
    result = proposer.evaluate_patch(_patch(), _BASE_HASH, _ALLOWLIST)
    assert result["status"] == "eligible_for_adoption_flow"
    assert result["reasons"] == []
    assert "auto_apply" not in result


def test_evaluate_patch_sensitive_target_scope_human_review():
    result = proposer.evaluate_patch(
        _patch(target_scope="constraints"), _BASE_HASH, _ALLOWLIST)
    assert result["status"] == "human_review_candidate"
    assert result["reasons"]
    assert all(r.startswith("sensitive_scope:") for r in result["reasons"])
    assert "auto_apply" not in result


def test_evaluate_patch_sensitive_path_prefix_human_review():
    patch = _patch(changes=[{"path": "toolchain/lock.json",
                             "op": "set", "value": {"freerouting.optional": True}}])
    result = proposer.evaluate_patch(patch, _BASE_HASH, _ALLOWLIST)
    assert result["status"] == "human_review_candidate"
    assert any("toolchain" in r for r in result["reasons"])


def test_evaluate_patch_invalid_blocked():
    result = proposer.evaluate_patch(
        _patch(operation_kind="board_write"), _BASE_HASH, _ALLOWLIST)
    assert result["status"] == "blocked"
    assert result["reasons"]
    assert "auto_apply" not in result


def test_evaluate_patch_base_hash_mismatch_blocked():
    result = proposer.evaluate_patch(_patch(), "c" * 64, _ALLOWLIST)
    assert result["status"] == "blocked"
    assert any("base_artifact_hash_mismatch" in r for r in result["reasons"])


# ---------------------------------------------------------------------------
# validate_search_space（TD3/TD2）
# ---------------------------------------------------------------------------

def test_validate_search_space_valid():
    assert proposer.validate_search_space(_space()) == []


def test_validate_search_space_empty_enum_values():
    space = _space(parameters=[
        {"name": "optimizer", "kind": "enum", "domain": {"values": []}}])
    errors = proposer.validate_search_space(space)
    assert errors
    assert any("values" in e and "非空" in e for e in errors)


def test_validate_search_space_min_not_less_than_max():
    space = _space(parameters=[
        {"name": "via_cost", "kind": "integer",
         "domain": {"values": [4], "min": 8, "max": 2, "step": 2}}])
    errors = proposer.validate_search_space(space)
    assert errors
    assert any("严格小于" in e for e in errors)
    # min/max 缺一也 fail-closed
    missing_min = _space(parameters=[
        {"name": "via_cost", "kind": "float",
         "domain": {"values": [4.0], "max": 8.0}}])
    assert proposer.validate_search_space(missing_min)


def test_validate_search_space_step_not_positive():
    for bad_step in (0, -2):
        space = _space(parameters=[
            {"name": "via_cost", "kind": "integer",
             "domain": {"values": [4], "min": 2, "max": 8, "step": bad_step}}])
        errors = proposer.validate_search_space(space)
        assert errors, bad_step
        assert any("step" in e for e in errors), bad_step


def test_validate_search_space_max_parameter_count_too_small():
    errors = proposer.validate_search_space(
        _space(max_parameter_count=1))  # 实际 2 个参数
    assert errors
    assert any("max_parameter_count" in e for e in errors)


def test_validate_search_space_ratio_zero_or_missing():
    errors = proposer.validate_search_space(
        _space(explore_real_execution_ratio=0))
    assert errors
    assert any("explore_real_execution_ratio" in e for e in errors)
    # 未声明比例同样 fail-closed：探索候选必须真实执行
    space = _space()
    del space["explore_real_execution_ratio"]
    errors = proposer.validate_search_space(space)
    assert errors
    assert any("explore_real_execution_ratio" in e for e in errors)


# ---------------------------------------------------------------------------
# adoption_gate（TD2/TD3/L4/L5）
# ---------------------------------------------------------------------------

_WL = _T2            # 白名单指标（lower_is_better）
_REQ = "deficit_recall_miss"  # required 指标（lower_is_better）


def _gate(baseline, challenger, holdout, *, wl=(_WL,), req=(_REQ,),
          min_boards=1, directions=None):
    return proposer.adoption_gate(
        baseline, challenger,
        whitelist_metrics=wl, required_metrics=req,
        holdout_results=holdout,
        min_holdout_boards=min_boards,
        metric_directions=directions)


def test_adoption_gate_whitelist_regression_single_veto():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 1, _REQ: 4},
        [{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 5}}])
    assert result["decision"] == "reject"
    assert [v["metric"] for v in result["whitelist_violations"]] == [_WL]
    assert result["human_adoption_required"] is True


def test_adoption_gate_required_regression_reject():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 6},
        [{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 5}}])
    assert result["decision"] == "reject"
    assert result["per_metric"][_REQ]["regressed"] is True
    assert result["per_metric"][_REQ]["direction"] == "lower_is_better"
    assert any("required_metric_regression" in r for r in result["reasons"])


def test_adoption_gate_holdout_missing_blocked():
    result = _gate({_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4}, [])
    assert result["decision"] == "blocked"
    assert any("holdout_missing" in r for r in result["reasons"])
    assert result["holdout"]["denominator"] == 0
    assert result["human_adoption_required"] is True


def test_adoption_gate_holdout_insufficient_boards_blocked():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4},
        [{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 4}}],
        min_boards=2)
    assert result["decision"] == "blocked"
    assert any("holdout_insufficient" in r for r in result["reasons"])


def test_adoption_gate_holdout_board_regression_reject():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4},
        [{"board_id": "HB-1", "metrics": {_WL: 2, _REQ: 5}}])  # 单板白名单回退
    assert result["decision"] == "reject"
    assert any("holdout_board_regression" in r for r in result["reasons"])
    assert result["holdout"]["non_regressed_boards"] == 0
    assert result["holdout"]["regressed_boards"] == ["HB-1"]


def test_adoption_gate_all_pass_adopt_candidate_with_human_gate():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 0, _REQ: 4},
        [{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 4}},
         {"board_id": "HB-2", "metrics": {_WL: 0, _REQ: 5}}])
    assert result["decision"] == "adopt_candidate"
    assert result["human_adoption_required"] is True  # 机器门 ≠ adoption
    assert result["holdout"]["denominator"] == 2
    assert result["holdout"]["non_regressed_boards"] == 2
    assert result["holdout"]["non_regression_rate"] == 1.0
    assert result["whitelist_violations"] == []


def test_adoption_gate_metric_direction_higher_is_better():
    wl = (_T4,)  # route_success_rate 高者优先
    baseline, challenger_ok, challenger_bad = {_T4: 0.9}, {_T4: 0.95}, {_T4: 0.85}
    holdout = [{"board_id": "HB-1", "metrics": {_T4: 0.92}}]
    ok = _gate(baseline, challenger_ok, holdout, wl=wl, req=(),
               directions={_T4: "higher_is_better"})
    assert ok["decision"] == "adopt_candidate"
    bad = _gate(baseline, challenger_bad, holdout, wl=wl, req=(),
                directions={_T4: "higher_is_better"})
    assert bad["decision"] == "reject"
    assert [v["metric"] for v in bad["whitelist_violations"]] == [_T4]
    # 未声明方向时按 lower_is_better 保守处理：0.95 会被误判方向且判回退
    conservative = _gate(baseline, challenger_ok, holdout, wl=wl, req=())
    assert conservative["decision"] == "reject"


def test_adoption_gate_missing_metric_fail_closed():
    result = _gate(
        {_WL: 0, _REQ: 5}, {_WL: 0},  # challenger 缺 _REQ
        [{"board_id": "HB-1", "metrics": {_WL: 0, _REQ: 5}}])
    assert result["decision"] == "reject"
    assert result["per_metric"][_REQ]["regressed"] is True
    assert result["per_metric"][_REQ]["reason"] == "missing_or_non_numeric_challenger"


# ---------------------------------------------------------------------------
# objective_vector / compare_objectives（TD3 分层质量向量）
# ---------------------------------------------------------------------------

def test_objective_vector_full_and_missing():
    full = proposer.objective_vector(_full_metrics())
    assert full["missing"] == []
    assert full["tier1_hard_constraints"] == 0
    assert full["tier3_drc"] == {"batch_severity_error": 0,
                                 "final_severity_all": 3}
    assert full["tier4_route_success"] == 0.95
    assert full["tier6_ordinary"]["length_dev"] == 0.8

    empty = proposer.objective_vector({})
    assert set(empty["missing"]) == set(proposer.OBJECTIVE_METRIC_KEYS)
    assert empty["tier1_hard_constraints"] is None
    assert empty["tier3_drc"]["batch_severity_error"] is None
    assert empty["tier6_ordinary"] == {"via_count": None, "layer_changes": None,
                                       "length_dev": None}


def test_compare_objectives_low_tier_not_compensable():
    base = _full_metrics()
    # tier1 恶化 1，tier6 大幅改善 → 仍判劣（低层劣化不可被高层补偿）
    worse = dict(base, **{_T1: 1, _T6A: 10})
    assert proposer.compare_objectives(worse, base) == -1
    assert proposer.compare_objectives(
        proposer.objective_vector(worse),
        proposer.objective_vector(base)) == -1
    # 无低层劣化时 tier6 改善 → 更优
    better = dict(base, **{_T6A: 10})
    assert proposer.compare_objectives(better, base) == 1


def test_compare_objectives_tolerance():
    base = _full_metrics()
    a = dict(base, **{_T6A: 122})
    assert proposer.compare_objectives(a, base) == -1          # 零容差：122 劣于 120
    assert proposer.compare_objectives(a, base, {_T6A: 2}) == 0   # 容差内相等
    assert proposer.compare_objectives(a, base, {_T6A: 1}) == -1  # 超容差仍劣
    assert proposer.compare_objectives(base, base, {_T6A: 0}) == 0


def test_compare_objectives_none_is_worst():
    base = _full_metrics()
    raw_missing_t4 = {k: v for k, v in base.items() if k != _T4}
    vec_missing = proposer.objective_vector(raw_missing_t4)
    assert vec_missing["tier4_route_success"] is None
    assert _T4 in vec_missing["missing"]
    assert proposer.compare_objectives(vec_missing,
                                        proposer.objective_vector(base)) == -1
    assert proposer.compare_objectives(proposer.objective_vector(base),
                                        vec_missing) == 1
    # 双方同层皆 None → 该层相等，继续比高层
    both_missing = proposer.objective_vector(raw_missing_t4)
    assert proposer.compare_objectives(vec_missing, both_missing) == 0


def test_compare_objectives_higher_better_tiers():
    base = _full_metrics()
    assert proposer.compare_objectives(
        dict(base, **{_T4: 0.99}), base) == 1
    assert proposer.compare_objectives(
        dict(base, **{_T4: 0.90}), base) == -1
    assert proposer.compare_objectives(
        dict(base, **{_T5: 0.20}), base) == 1


def test_compare_objectives_equal_vectors():
    base = _full_metrics()
    assert proposer.compare_objectives(
        proposer.objective_vector(base),
        proposer.objective_vector(dict(base))) == 0
