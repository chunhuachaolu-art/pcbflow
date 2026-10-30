"""TL-4 autotune 编排测试（smoke-2l/smoke-4l 全链；SPEC-v3.0 §3 TL-4/TD3/TD2/TD11）。

依赖 cwd=pcbflow 根（既有测试约定）。使用真实 profiles 合同输入：
manifest（params 搜索域+scope）/ profile / inputs/{search-space,
baseline-config,constraints,board}.json。断言的是红线行为：
  - 确定性候选生成（重跑 byte-exact、candidate_id 稳定、域外 baseline
    fail-closed）；
  - 代理只做预筛（不可 promotion）；固定比例真实执行；代理缺席保守全量；
  - 分层质量向量（无标量总和）；vector_best 逐指标回退如实入账，
    challenger 在零回退池内选择；
  - holdout 缺失（TL-5 未启动）→ adoption blocked；TL-4 gate blocked
    （不得伪造 pass）；低自由度（样本不足只许单参数）如实判定；
  - TD11：patch execution_allowed=false、无自动 apply 路径、旧 config
    immutable 保留；无人工 disposition 的 adoption 不可执行；
  - ledger 六事件（proposal→judge_pre→execution→judge_post→backtest→
    gate）hash 链完整、checkpoint 可验；
  - 生成器纪律：stdout canonical JSON byte-exact、无 wall-clock、无主机路径。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import autotune_chain, hashing, proposer, schemas, v3cli
from pcbflow import gate as gate_mod
from pcbflow import judge as judge_mod
from pcbflow import ledger as ledger_mod

P2L = os.path.join("profiles", "smoke-2l")
P4L = os.path.join("profiles", "smoke-4l")
PATHS = {
    "smoke-2l": {
        "profile": os.path.join(P2L, "profile.json"),
        "manifest": os.path.join(P2L, "manifest.json"),
        "space": os.path.join(P2L, "inputs", "search-space.json"),
        "baseline": os.path.join(P2L, "inputs", "baseline-config.json"),
    },
    "smoke-4l": {
        "profile": os.path.join(P4L, "profile.json"),
        "manifest": os.path.join(P4L, "manifest.json"),
        "space": os.path.join(P4L, "inputs", "search-space.json"),
        "baseline": os.path.join(P4L, "inputs", "baseline-config.json"),
    },
}


def _load(profile_tag):
    p = PATHS[profile_tag]
    hashes, errors = v3cli._autotune_input_hashes(
        p["manifest"], p["space"], p["baseline"])
    assert errors == []
    return {
        "profile": json.load(open(p["profile"], encoding="utf-8")),
        "manifest": json.load(open(p["manifest"], encoding="utf-8")),
        "space": json.load(open(p["space"], encoding="utf-8")),
        "baseline": json.load(open(p["baseline"], encoding="utf-8")),
        "constraints": json.load(
            open(os.path.join(os.path.dirname(p["manifest"]), "inputs",
                              "constraints.json"), encoding="utf-8")),
        "hashes": hashes,
    }


def _build(profile_tag):
    d = _load(profile_tag)
    return autotune_chain.build_chain(
        d["profile"], d["space"], d["baseline"], d["constraints"],
        d["hashes"], snapshot_revision="smoke-r1",
        evaluator={"name": "pcbflow-v3-autotune-chain", "version": "1.0",
                   "code_sha256": hashing.sha256_file(
                       autotune_chain.__file__)}), d


# ---------------------------------------------------------------------------
# 搜索空间声明（manifest params scope + search-space/baseline 合同）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tag", ["smoke-2l", "smoke-4l"])
def test_profile_search_space_declared_and_valid(tag):
    d = _load(tag)
    assert schemas.validate("search_space", d["space"]) == []
    assert proposer.validate_search_space(d["space"]) == []
    assert autotune_chain.validate_baseline_config(
        d["baseline"], d["space"]) == []
    assert autotune_chain.validate_chain_inputs(d["space"], d["baseline"]) == []
    # manifest.params 与 search-space 参数名一致，且逐参数声明了 scope
    mf_params = {p["name"]: p for p in d["manifest"]["params"]}
    space_params = {p["name"] for p in d["space"]["parameters"]}
    assert set(mf_params) == space_params
    for name, param in mf_params.items():
        assert param["source"] and param["source"].startswith("scope:"), name
        assert param["domain"] and "values" in param["domain"], name


def test_baseline_out_of_domain_rejected():
    d = _load("smoke-4l")
    bad = json.loads(json.dumps(d["baseline"]))
    bad["values"]["route_grid_mm"] = 0.55          # 不在 0.1 步进网格上
    errors = autotune_chain.validate_baseline_config(bad, d["space"])
    assert any("不在参数域/网格内" in e for e in errors)
    out_of_range = json.loads(json.dumps(d["baseline"]))
    out_of_range["values"]["via_penalty"] = 99
    assert autotune_chain.validate_baseline_config(out_of_range,
                                                   d["space"])


def test_baseline_keys_must_match_space_exactly():
    d = _load("smoke-2l")
    extra = json.loads(json.dumps(d["baseline"]))
    extra["values"]["via_penalty"] = 3              # 空间未声明
    errors = autotune_chain.validate_baseline_config(extra, d["space"])
    assert any("未声明参数" in e for e in errors)
    missing = json.loads(json.dumps(d["baseline"]))
    del missing["values"]["route_grid_mm"]
    assert any("缺参数" in e for e in
               autotune_chain.validate_baseline_config(missing, d["space"]))
    cross = json.loads(json.dumps(d["baseline"]))
    cross["profile_id"] = "smoke-4l"
    assert any("不一致" in e for e in
               autotune_chain.validate_baseline_config(cross, d["space"]))


def test_float_domain_without_step_rejected():
    d = _load("smoke-4l")
    space = json.loads(json.dumps(d["space"]))
    space["parameters"][0]["domain"].pop("step")
    with pytest.raises(ValueError, match="step"):
        autotune_chain.enumerate_candidates(
            space, d["baseline"]["values"])


def test_enumeration_deterministic_in_domain_with_stable_ids():
    d = _load("smoke-4l")
    cands = autotune_chain.enumerate_candidates(
        d["space"], d["baseline"]["values"])
    assert len(cands) == 50                          # 5 grid × 10 via_penalty
    assert [c["candidate_id"] for c in cands] == \
        [f"CAND-{i:04d}" for i in range(1, 51)]
    again = autotune_chain.enumerate_candidates(
        d["space"], d["baseline"]["values"])
    assert cands == again                            # 重跑全等
    values = {tuple(sorted(c["values"].items())) for c in cands}
    assert len(values) == 50                         # 无重复点
    by_id = {c["candidate_id"]: c for c in cands}
    assert by_id["CAND-0001"]["values"] == {"route_grid_mm": 0.4,
                                            "via_penalty": 1}
    assert by_id["CAND-0015"]["values"] == {"route_grid_mm": 0.5,
                                            "via_penalty": 5}
    # baseline 必须是网格点
    base_cand = autotune_chain.find_baseline_candidate(
        cands, d["baseline"]["values"])
    assert base_cand["candidate_id"] == "CAND-0015"
    with pytest.raises(ValueError, match="网格"):
        autotune_chain.enumerate_candidates(
            d["space"], {"route_grid_mm": 0.45, "via_penalty": 5})


# ---------------------------------------------------------------------------
# smoke 级真实执行（闭式评估器）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tag", ["smoke-2l", "smoke-4l"])
def test_evaluator_metrics_respond_to_knobs(tag):
    d = _load(tag)
    fine = autotune_chain.evaluate_config_smoke(
        d["profile"], d["constraints"], {"route_grid_mm": 0.4})
    coarse = autotune_chain.evaluate_config_smoke(
        d["profile"], d["constraints"], {"route_grid_mm": 0.8})
    assert fine["resource_margin"] > coarse["resource_margin"]
    assert set(fine) == set(proposer.OBJECTIVE_METRIC_KEYS)
    assert all(isinstance(v, float) for v in fine.values())
    # 硬约束：栅格粗于可实现轨道 → 违例（4l power_rail 0.5；2l diff_pair）
    assert fine["hard_constraint_violations"] == 0.0
    assert coarse["hard_constraint_violations"] >= 1.0
    # via_penalty 降低过孔估计、抬高长度偏差（模型声明响应）
    d4 = _load("smoke-4l")
    low_pen = autotune_chain.evaluate_config_smoke(
        d4["profile"], d4["constraints"],
        {"route_grid_mm": 0.4, "via_penalty": 2})
    high_pen = autotune_chain.evaluate_config_smoke(
        d4["profile"], d4["constraints"],
        {"route_grid_mm": 0.4, "via_penalty": 8})
    assert high_pen["via_count"] < low_pen["via_count"]
    assert high_pen["length_deviation"] > low_pen["length_deviation"]


def test_evaluator_rejects_unknown_knob():
    d = _load("smoke-2l")
    with pytest.raises(ValueError, match="不支持参数"):
        autotune_chain.evaluate_config_smoke(
            d["profile"], d["constraints"], {"mystery_knob": 1})


# ---------------------------------------------------------------------------
# 代理预筛与固定比例真实执行
# ---------------------------------------------------------------------------

def test_proxy_prescreen_ranks_only_and_not_promotion_eligible():
    d = _load("smoke-4l")
    cands = autotune_chain.enumerate_candidates(
        d["space"], d["baseline"]["values"])
    proxy = autotune_chain.proxy_prescreen(cands, available=True)
    assert set(proxy) == {"ranking", "proxy_model"}
    assert proxy["ranking"][:10] == [f"CAND-{i:04d}" for i in range(1, 11)]
    assert proxy["proxy_model"]["promotion_eligible"] is False
    assert proxy["proxy_model"]["unexecuted_candidates_eligible"] is False
    # 代理缺席 → None（调用方必须保守回退）
    assert autotune_chain.proxy_prescreen(cands, available=False) is None


def test_selection_ratio_and_baseline_always_executed():
    d = _load("smoke-4l")
    cands = autotune_chain.enumerate_candidates(
        d["space"], d["baseline"]["values"])
    proxy = autotune_chain.proxy_prescreen(cands, available=True)
    selected, plan = autotune_chain.select_real_execution(
        cands, d["space"], "CAND-0015", proxy)
    assert len(selected) == 11                       # ceil(50×0.2)=10 + baseline
    assert "CAND-0015" in selected                   # 基线恒真实执行
    assert plan["required_min_count"] == 10
    assert plan["selected_count"] >= plan["required_min_count"]
    assert plan["proxy_used"] is True
    assert plan["baseline_appended_after_proxy_selection"] is True
    # 2l：ratio=1.0 → 全量
    d2 = _load("smoke-2l")
    cands2 = autotune_chain.enumerate_candidates(
        d2["space"], d2["baseline"]["values"])
    selected2, plan2 = autotune_chain.select_real_execution(
        cands2, d2["space"], "CAND-0002",
        autotune_chain.proxy_prescreen(cands2, available=True))
    assert len(selected2) == 3 and plan2["required_min_count"] == 3


def test_proxy_unavailable_falls_back_to_full_execution():
    d = _load("smoke-4l")
    cands = autotune_chain.enumerate_candidates(
        d["space"], d["baseline"]["values"])
    selected, plan = autotune_chain.select_real_execution(
        cands, d["space"], "CAND-0015", None)
    assert selected == [c["candidate_id"] for c in cands]
    assert plan["fallback"] == "conservative_full_execution"
    assert plan["proxy_used"] is False


# ---------------------------------------------------------------------------
# 全链：challenger/adoption/ledger/gate（两 profile）
# ---------------------------------------------------------------------------

def test_chain_2l_honest_outcomes():
    bundle, d = _build("smoke-2l")
    assert bundle["chain_kind"] == "tl4-autotune-chain"
    assert bundle["executions"] and all(
        e["execution_level"] == autotune_chain.EXECUTION_LEVEL
        for e in bundle["executions"])
    assert len(bundle["executions"]) == 3             # ratio=1.0 全量
    assert bundle["winner"]["candidate_id"] == "CAND-0001"
    assert bundle["winner"]["values"] == {"route_grid_mm": 0.4}
    assert bundle["winner"]["vector_best_regressions"] == []
    assert bundle["challenger"]["candidate_id"] == "CAND-0001"
    assert bundle["challenger"]["comparison_vs_baseline"] == 1
    assert bundle["adoption"]["decision"] == "blocked"
    # P1-A：真实路径已迁至逐板配对门，理由措辞为配对口径
    assert bundle["adoption"]["reasons"] == [
        "holdout_pairs_missing: 缺逐板配对 holdout 证据（fail-closed）"]
    assert bundle["adoption"]["gate_mode"] == "paired_v1"
    assert bundle["low_dof"]["low_dof_compliant"] is True
    assert bundle["low_dof"]["changed_params"] == ["route_grid_mm"]


def test_chain_4l_vector_best_regression_recorded_challenger_feasible():
    bundle, d = _build("smoke-4l")
    # vector_best 因 via_penalty=10 使 length_deviation 回退 → 如实入账
    assert bundle["winner"]["candidate_id"] == "CAND-0010"
    assert bundle["winner"]["vector_best_regressions"] == ["length_deviation"]
    # challenger 在零回退池内选最优
    assert bundle["challenger"]["candidate_id"] == "CAND-0008"
    assert bundle["challenger"]["values"] == {"route_grid_mm": 0.4,
                                              "via_penalty": 8}
    assert bundle["challenger"]["comparison_vs_baseline"] == 1
    regressions = autotune_chain.per_metric_regressions(
        bundle["baseline"]["metrics"], bundle["challenger"]["metrics"])
    assert regressions == []
    # 低自由度：holdout 分母 0 < 2，双参数变更不合规（如实 False）
    assert bundle["low_dof"]["samples_insufficient"] is True
    assert bundle["low_dof"]["low_dof_compliant"] is False
    assert bundle["adoption"]["decision"] == "blocked"
    # P1-A：配对门两个分母（板/执行）均为 0
    assert bundle["adoption"]["holdout"]["board_denominator"] == 0
    assert bundle["adoption"]["holdout"]["execution_denominator"] == 0


def test_chain_ledger_six_events_valid_and_hash_bound():
    for tag in ("smoke-2l", "smoke-4l"):
        bundle, _ = _build(tag)
        entries = bundle["ledger_entries"]
        assert [e["entry_kind"] for e in entries] == [
            "proposal", "judge_pre", "execution", "judge_post",
            "backtest", "gate"]
        assert [e["entry_id"] for e in entries] == [
            f"TL4-E-{i:04d}" for i in range(1, 7)]
        assert ledger_mod.verify_chain(entries) == []
        assert ledger_mod.verify_supersedes(entries) == []
        assert ledger_mod.verify_against_checkpoint(
            entries, bundle["ledger_checkpoint"]) == []
        assert bundle["ledger_file_sha256"] == hashing.sha256_bytes(
            autotune_chain.ledger_file_bytes(entries))
        # gate 输入绑定 ledger 前缀（judge 前五事件；gate 事件在门之后入账）
        assert bundle["ledger_prefix_sha256"] == hashing.sha256_bytes(
            autotune_chain.ledger_file_bytes(entries[:5]))
        # proposal 事件锚定 patch hash；execution 事件锚定执行记录 hash
        assert entries[0]["proposal_sha256"] == hashing.sha256_bytes(
            hashing.canonical_json_bytes(bundle["proposal_patch"]))
        assert entries[2]["execution_ref"] == bundle["execution_ref"]


def test_chain_patch_td11_contract():
    bundle, _ = _build("smoke-4l")
    patch = bundle["proposal_patch"]
    assert schemas.validate("proposal_patch", patch) == []
    assert patch["execution_allowed"] is False
    assert patch["operation_kind"] == "policy_parameter_candidate"
    assert all(c["path"] == "policy/route_params.json"
               for c in patch["changes"])
    assert patch["determinism_claim"] == "byte_exact"
    assert patch["random_seed"] is None                # 全枚举无随机成分
    assert proposer.validate_patch(
        patch, autotune_chain.TARGET_PATH_ALLOWLIST) == []
    assert bundle["patch_evaluation"]["status"] == \
        proposer.PATCH_STATUS_ELIGIBLE
    assert "auto_apply" not in bundle["patch_evaluation"]


def test_chain_judge_pre_ok_post_fail_honest():
    bundle2l, _ = _build("smoke-2l")
    assert bundle2l["judge_pre_evaluation"]["pre_ok"] is True
    post2l = bundle2l["judge_post"]
    assert judge_mod.adoption_check(
        {judge_mod.pre_record_sha256(bundle2l["judge_pre"])}, post2l) == []
    assert post2l["physics_status"] == "not_required"
    assert bundle2l["judge_post_evaluation"]["post_ok"] is False
    assert any("drc_batch_ref" in f
               for f in bundle2l["judge_post_evaluation"]["failed"])
    bundle4l, _ = _build("smoke-4l")
    # smoke-4l profile required physics → TL-3 已判 fail，如实继承
    assert bundle4l["judge_post"]["physics_status"] == "fail"
    assert bundle4l["judge_post_evaluation"]["post_ok"] is False


def test_chain_gate_record_blocked_machine_verifiable():
    bundle, _ = _build("smoke-4l")
    record = bundle["gate_record"]
    assert record["gate_kind"] == "training_loop"
    assert record["result"] == "blocked"              # 不得伪造 pass
    assert "missing_input" in record["failure_codes"]
    inputs = {i["artifact_id"]: i for i in record["inputs"]}
    assert inputs["holdout_corpus"]["status"] == "missing"
    assert inputs["holdout_corpus"]["sha256"] is None
    pred = {p["id"]: p["value"] for p in record["required_predicates"]}
    assert pred["search_space_valid"] is True
    assert pred["candidate_search_deterministic"] is True
    assert pred["real_execution_ratio_satisfied"] is True
    assert pred["proxy_used_for_prescreen_only"] is True
    assert pred["layered_objective_vector_no_scalar_sum"] is True
    assert pred["winner_not_worse_than_baseline"] is True
    assert pred["whitelist_zero_degradation"] is True
    assert pred["low_dof_contract_compliant"] is False
    assert pred["holdout_non_regression_evidenced"] is False
    assert pred["adoption_machine_gate_pass"] is False
    assert pred["human_adoption_disposition_present"] is False
    assert pred["tl5_independent_holdout_corpus_available"] is False
    assert pred["judge_pre_ok"] is True
    assert pred["judge_post_ok"] is False
    assert pred["old_config_immutable_retained"] is True
    assert pred["ledger_chain_valid"] is True
    assert all(p.get("evidence") for p in record["required_predicates"])
    assert bundle["gate_verify_errors"] == []
    assert gate_mod.verify_gate_record(record) == []
    assert len(bundle["gate_core_hash"]) == 64
    assert record["evaluation_metadata"] == {
        "evaluated_at": None, "host": None, "elapsed_s": None}


def test_chain_adoption_pending_human_no_auto_apply_and_old_config_kept():
    bundle, _ = _build("smoke-2l")
    adoption = bundle["adoption"]
    assert adoption["human_adoption_required"] is True
    assert adoption["adoption_status"] == "pending_human_disposition"
    assert adoption["auto_apply"] is False
    assert adoption["old_config_retained"] is True
    raw = json.dumps(bundle, ensure_ascii=False)
    assert '"auto_apply": true' not in raw
    # 旧 config immutable：链构建前后 baseline 输入文件 hash 不变（零写盘）
    path = PATHS["smoke-2l"]["baseline"]
    before = hashing.sha256_file(path)
    _build("smoke-2l")
    assert hashing.sha256_file(path) == before
    text = json.dumps(bundle, ensure_ascii=False)
    assert "不构成 TL-4 出口门通过" in text


def test_chain_deterministic_byte_exact_rerun():
    for tag in ("smoke-2l", "smoke-4l"):
        b1, _ = _build(tag)
        b2, _ = _build(tag)
        assert hashing.canonical_json_bytes(b1) == \
            hashing.canonical_json_bytes(b2)


# ---------------------------------------------------------------------------
# 负向 witness（TD2/TD3/TD11/L4/L5 闭门路径）
# ---------------------------------------------------------------------------

def test_negative_witnesses_fail_closed_paths():
    bundle, _ = _build("smoke-4l")
    w = bundle["negative_witnesses"]
    w1 = w["holdout_regression_rejects"]["gate"]
    assert w1["decision"] == "reject"
    assert any("holdout_board_regression" in r for r in w1["reasons"])
    w2 = w["whitelist_degradation_rejects_and_blocks_adoption"]["gate"]
    assert w2["decision"] == "reject"
    assert any("whitelist_regression" in r for r in w2["reasons"])
    w3 = w["insufficient_samples_blocked"]["gate"]
    assert w3["decision"] == "blocked"
    assert any("holdout_insufficient" in r for r in w3["reasons"])
    w4 = w["adoption_without_human_disposition_not_executable"]
    assert w4["waiver_generated"] is False
    assert w4["errors"]                                 # 无 policy ⇒ 全拒
    assert w4["gate_write_scan"] == []
    assert w4["patch_execution_allowed"] is False
    w5 = w["proxy_unavailable_falls_back_to_full_execution"]
    assert w5["full_execution_fallback"] is True
    assert w5["selected_count"] == w5["total_candidates"] == 50
    w6 = w["adoption_failure_retains_old_config"]
    assert w6["old_config_retained"] is True
    assert w6["auto_apply_path_exists"] is False
    assert w6["chain_write_scope"] == "none"


def test_low_dof_rule_direct():
    ok = autotune_chain.check_low_dof(
        {"a": 1, "b": 2}, {"a": 1, "b": 3}, 0)
    assert ok["samples_insufficient"] is True
    assert ok["low_dof_compliant"] is True             # 单参数变更
    bad = autotune_chain.check_low_dof(
        {"a": 1, "b": 2}, {"a": 9, "b": 3}, 0)
    assert bad["low_dof_compliant"] is False           # 双参数 + 样本不足
    rich = autotune_chain.check_low_dof(
        {"a": 1, "b": 2}, {"a": 9, "b": 3}, 5)
    assert rich["samples_insufficient"] is False
    assert rich["low_dof_compliant"] is True           # 样本充足不解禁


# ---------------------------------------------------------------------------
# v3cli E2E + 生成器纪律
# ---------------------------------------------------------------------------

def _run_cli(capsys, argv):
    rc = v3cli.main(argv)
    out = capsys.readouterr().out
    return rc, out, json.loads(out)


@pytest.mark.parametrize("tag", ["smoke-2l", "smoke-4l"])
def test_v3cli_autotune_chain_e2e_blocked(capsys, tag):
    p = PATHS[tag]
    rc, raw, d = _run_cli(capsys, [
        "proposer", "--select", "autotune-chain",
        "--profile", p["profile"], "--space", p["space"],
        "--baseline", p["baseline"], "--snapshot-revision", "smoke-r1"])
    assert rc == 2                                    # gate blocked → exit 2
    assert d["command"] == "v3-proposer"
    assert d["select"] == "autotune-chain"
    assert d["status"] == "blocked"
    assert d["gate_record"]["result"] == "blocked"
    assert d["ledger_verify"] == {"chain_errors": [],
                                  "supersedes_errors": []}
    assert d["gate_verify_errors"] == []
    assert d["gate_evaluator_bound"]["code_sha256"] == \
        hashing.sha256_file(autotune_chain.__file__)


def test_v3cli_autotune_chain_byte_exact_and_clean(capsys):
    p = PATHS["smoke-4l"]
    argv = ["proposer", "--select", "autotune-chain",
            "--profile", p["profile"], "--space", p["space"],
            "--baseline", p["baseline"]]
    _, raw1, _ = _run_cli(capsys, argv)
    _, raw2, _ = _run_cli(capsys, argv)
    assert raw1 == raw2                               # 重跑 byte-exact
    assert raw1 == hashing.canonical_json_bytes(
        json.loads(raw1)).decode("utf-8")             # stdout 即 canonical
    assert "C:\\\\" not in raw1                       # 无主机路径
    assert json.loads(raw1)["gate_record"][
        "evaluation_metadata"]["evaluated_at"] is None


def test_v3cli_autotune_chain_missing_input_blocked(capsys):
    p = PATHS["smoke-4l"]
    rc, _, d = _run_cli(capsys, [
        "proposer", "--select", "autotune-chain",
        "--profile", p["profile"], "--space",
        "profiles/smoke-4l/inputs/nope.json",
        "--baseline", p["baseline"]])
    assert rc == 2
    assert d["status"] == "blocked"
    assert any("search_space" in e for e in d["errors"])


def test_v3cli_autotune_chain_needs_all_args(capsys):
    rc, _, d = _run_cli(capsys, ["proposer", "--select", "autotune-chain"])
    assert rc == 1
    assert d["status"] == "failed"
    assert "--profile" in d["error"]


def test_v3cli_proposer_existing_selects_unchanged(capsys, tmp_path):
    """既有 validate/evaluate/adoption select 合同不回归。"""
    space = {
        "schema_version": "3.0", "space_id": "SS-X", "profile_id": "p",
        "parameters": [{"name": "k", "kind": "enum",
                        "domain": {"values": [1, 2]}}],
        "max_parameter_count": 1, "explore_real_execution_ratio": 0.5,
    }
    sp = tmp_path / "space.json"
    sp.write_text(json.dumps(space), encoding="utf-8")
    rc, _, d = _run_cli(capsys, ["proposer", "--select", "validate",
                                 "--patch", str(sp),
                                 "--allowlist", str(sp)])
    assert rc == 2 and d["status"] == "blocked"       # patch schema 会拒绝
