"""TL-4 holdout 解锁评估测试（S9，路径 b；SPEC-v3.0 §3 TL-4/TD2/TD3/TD11）。

依赖 cwd=pcbflow 根（既有测试约定），只读消费真实盘上产物：
out/v3-tl4/v1 门记录与 patch/bundle、out/v3-tl5/ 门记录 v3+两库 manifest、
out/v3-approvals/APR-0004。断言的是红线行为：
  - 逐谓词重估：tl5 语料可用性/人工处置在场=可由既有产物作实（v2 翻
    true）；holdout 不回退/adoption 机器门/judge_post（+4l low_dof）=
    结构性缺（v2 保持 false，无翻转入口——机器强制，防凑门）；
  - 路径 a（真实板搜索空间）拒绝理由=盘上事实（corpus 四段消费可调
    参数=0；策略参数化目标函数空真/reward hacking；DRC 指标 config 恒
    不变）；路径 b 选中；
  - TL-5 门非 pass / binding hash 不一致 / 谓词已 pass 的链 → 一律
    fail-closed；
  - TL-5 check 产物（参考态 DRC）不可充当 executor DRC ref（防语义
    偷换）；v2 门记录人工不可直写、重跑 byte-exact、无 wall-clock。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import autotune_chain, gate as gate_mod, hashing, v3cli

TL4 = os.path.join("out", "v3-tl4")
TL5 = os.path.join("out", "v3-tl5")
APR = os.path.join("out", "v3-approvals")

REAL = {
    "tl5_wrapper": os.path.join(TL5, "gate-record-tl5-v3.json"),
    "manifest_bm": os.path.join(
        TL5, "dataset-manifest-pcbbenchmarks-r1-v3.json"),
    "manifest_pc": os.path.join(TL5, "dataset-manifest-pcbench-r1-v2.json"),
    "apr": os.path.join(
        APR, "disposition-APR-0004-tl4-adoption-disposition.json"),
    "approvals_ledger": os.path.join(APR, "decision-ledger.jsonl"),
    "v1_2l": os.path.join(TL4, "gate-record-smoke-2l.json"),
    "v1_4l": os.path.join(TL4, "gate-record-smoke-4l.json"),
    "pp_2l": os.path.join(TL4, "proposal-patch-smoke-2l.json"),
    "pp_4l": os.path.join(TL4, "proposal-patch-smoke-4l.json"),
    "bundle_2l": os.path.join(TL4, "chain-bundle-smoke-2l.json"),
    "bundle_4l": os.path.join(TL4, "chain-bundle-smoke-4l.json"),
}


def _j(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _inputs():
    tl5w = _j(REAL["tl5_wrapper"])
    return {
        "tl5w": tl5w,
        "v1": {"smoke-2l": _j(REAL["v1_2l"])["gate_record"],
               "smoke-4l": _j(REAL["v1_4l"])["gate_record"]},
        "patch_ids": {"smoke-2l": _j(REAL["pp_2l"])["patch_id"],
                      "smoke-4l": _j(REAL["pp_4l"])["patch_id"]},
        "changed": {
            "smoke-2l": _j(REAL["bundle_2l"])["challenger"]["changed_params"],
            "smoke-4l": _j(REAL["bundle_4l"])["challenger"]["changed_params"]},
        "manifests": [_j(REAL["manifest_bm"]), _j(REAL["manifest_pc"])],
        "apr": _j(REAL["apr"]),
        "bindings": {
            "tl5_gate_record_core": tl5w["gate_core_hash"],
            "dataset_manifest_pcbbenchmarks_r1_v3":
                hashing.sha256_file(REAL["manifest_bm"]),
            "dataset_manifest_pcbench_r1_v2":
                hashing.sha256_file(REAL["manifest_pc"]),
            "adoption_disposition_apr0004":
                hashing.sha256_file(REAL["apr"]),
            "approvals_decision_ledger":
                hashing.sha256_file(REAL["approvals_ledger"]),
        },
        "evaluator": {
            "name": "pcbflow-v3-autotune-chain", "version": "1.1",
            "code_sha256": hashing.sha256_file(autotune_chain.__file__)},
    }


def _build(**override):
    d = _inputs()
    kwargs = dict(
        v1_gate_records=d["v1"], patch_ids=d["patch_ids"],
        changed_params=d["changed"], tl5_gate_record=d["tl5w"]["gate_record"],
        dataset_manifests=d["manifests"], adoption_disposition=d["apr"],
        binding_hashes=d["bindings"], evaluator=d["evaluator"])
    kwargs.update(override)
    return autotune_chain.build_holdout_unlock(**kwargs), d


# ---------------------------------------------------------------------------
# 语料事实与处置覆盖
# ---------------------------------------------------------------------------

def test_corpus_facts_from_real_manifests():
    facts = autotune_chain.holdout_corpus_facts(_inputs()["manifests"])
    assert facts["corpus_available"] is True
    assert facts["holdout_board_count"] == 12        # bm11 + pcbench 11
    assert facts["holdout_frozen_readonly"] is True
    assert facts["split_disjoint"] is True
    assert "kitspace_T32_ref" in facts["holdout_boards"]  # t32-ref 不双计
    assert {x["holdout_count"] for x in facts["holdout_count_by_dataset"]} \
        == {1, 11}


def test_corpus_facts_fail_closed():
    with pytest.raises(ValueError):
        autotune_chain.holdout_corpus_facts([{"no_splits": True}])
    bad = json.loads(json.dumps(_inputs()["manifests"][0]))
    bad["dataset_splits"]["holdout_frozen_readonly"] = False
    facts = autotune_chain.holdout_corpus_facts(
        [bad, _inputs()["manifests"][1]])
    assert facts["holdout_frozen_readonly"] is False
    assert facts["corpus_available"] is False        # 未冻结不作实可用


def test_disposition_coverage_positive_and_negative():
    d = _inputs()
    for pid in d["patch_ids"].values():
        cover = autotune_chain.adoption_disposition_covers(d["apr"], pid)
        assert cover["present"] is True
    wrong = autotune_chain.adoption_disposition_covers(
        d["apr"], "PP-OTHER-R1-CAND-9999")
    assert wrong["present"] is False
    assert any("fact_refs" in r for r in wrong["reasons"])
    waive = dict(d["apr"], kind="waive")
    assert autotune_chain.adoption_disposition_covers(
        waive, d["patch_ids"]["smoke-2l"])["present"] is False


# ---------------------------------------------------------------------------
# 路径决策与逐谓词重估
# ---------------------------------------------------------------------------

def test_path_b_selected_with_verified_grounds():
    memo = _build()[0]["evaluation_memo"]
    assert memo["path_decision"]["selected"] == "b"
    assert memo["path_decision"]["options"]["a"]["verdict"] == \
        "rejected_not_executable_honestly"
    assert len(memo["path_decision"]["options"]["a"]["grounds"]) == 3
    assert memo["corpus_facts"]["holdout_board_count"] == 12
    assert memo["executed_holdout_denominator"] == 0
    assert memo["low_dof_analysis"]["multi_param_unlocked"] is False
    assert memo["low_dof_analysis"]["corpus_satisfies_threshold"] is True
    assert memo["adoption_status_after_reevaluation"].startswith(
        "human_approved_machine_blocked")
    assert memo["fact_corrections"][0]["verified_count"] == 12


def test_predicate_flip_matrix_per_profile():
    result = _build()[0]
    for pid in ("smoke-2l", "smoke-4l"):
        table = {r["id"]: r for r in
                 result["evaluation_memo"]["predicate_reevaluation"][pid]}
        # 可作实 → v2 翻 true
        for flippable in ("tl5_independent_holdout_corpus_available",
                          "human_adoption_disposition_present"):
            assert table[flippable]["v1_value"] is False
            assert table[flippable]["v2_value"] is True
        # 结构性缺 → v2 保持 false
        for structural in ("holdout_non_regression_evidenced",
                           "adoption_machine_gate_pass", "judge_post_ok"):
            assert table[structural]["v1_value"] is False
            assert table[structural]["v2_value"] is False
        # low_dof 沿用 v1（分母=已执行板数=0；语料 12 不替代）
        assert table["low_dof_contract_compliant"]["v2_value"] == \
            table["low_dof_contract_compliant"]["v1_value"]


def test_structural_predicates_have_no_flip_entrypoint():
    """机器强制：构建函数不存在把三个执行依赖谓词置 true 的参数路径。"""
    import inspect
    sig = inspect.signature(autotune_chain.build_holdout_unlock)
    for name, param in sig.parameters.items():
        assert "holdout" not in name or param.kind not in (
            inspect.Parameter.VAR_KEYWORD,), name
    # 结构性谓词 value 在 _v2_predicates 内为常量 False：负向函数级断言
    result = _build()[0]
    for pid, spec in result["gate_specs_v2"].items():
        preds = {p["id"]: p for p in spec["required_predicates"]}
        assert preds["holdout_non_regression_evidenced"]["value"] is False
        assert preds["judge_post_ok"]["value"] is False
        assert preds["adoption_machine_gate_pass"]["value"] is False


def test_drc_reference_products_ineligible_as_executor_refs():
    memo = _build()[0]["evaluation_memo"]
    ruling = memo["drc_ref_eligibility"]
    assert ruling["tl5_check_products"] == "ineligible_as_executor_drc_ref"
    assert "参考 routed 态" in ruling["reason"]
    # v2 门输入不绑定任何 DRC 产物为 executor ref（只绑语料/处置证据）
    for spec in _build()[0]["gate_specs_v2"].values():
        ids = {i["artifact_id"] for i in spec["inputs"]}
        assert not any("drc" in i for i in ids)
        assert "holdout_corpus_tl5_gate_record" in ids


# ---------------------------------------------------------------------------
# v2 门评估（机器三态：证据在但不过 → fail）
# ---------------------------------------------------------------------------

def test_v2_gate_machine_verdict_fail_with_exact_codes():
    result = _build()[0]
    expected = result["evaluation_memo"]["expected_v2_failure_codes"]
    for pid, spec in result["gate_specs_v2"].items():
        record = gate_mod.evaluate_gate(**spec)
        assert gate_mod.verify_gate_record(record) == []
        assert record["result"] == "fail"      # 输入全 present+谓词不过
        assert sorted(record["failure_codes"]) == sorted(expected[pid])
        assert record["predicate_version"] == "pv2"
        assert record["disposition_refs"] == ["APR-0004"]
        # v1 输入原样保留（除 holdout_corpus 由 missing 换为绑定证据）
        v1_ids = {i["artifact_id"] for i in
                  _inputs()["v1"][pid]["inputs"]}
        v2_ids = {i["artifact_id"] for i in record["inputs"]}
        assert v1_ids - v2_ids == {"holdout_corpus"}
    assert expected["smoke-4l"] == sorted(
        expected["smoke-2l"] + ["predicate_failed:low_dof_contract_compliant"])


def test_v1_records_and_inputs_untouched_by_builder():
    before = json.loads(json.dumps(_inputs()["v1"]))
    _build()
    assert _inputs()["v1"] == before        # 纯函数：v1 记录零改动


# ---------------------------------------------------------------------------
# fail-closed 负向
# ---------------------------------------------------------------------------

def test_tl5_gate_not_pass_rejected():
    d = _inputs()
    blocked = json.loads(json.dumps(d["tl5w"]))
    blocked["gate_record"]["result"] = "blocked"
    # core hash 对账同步改为篡改后重算值——隔离验证"result 非 pass"检查本身
    bindings = dict(d["bindings"], tl5_gate_record_core=gate_mod.gate_core_hash(
        blocked["gate_record"]))
    with pytest.raises(ValueError, match="非 pass"):
        _build(tl5_gate_record=blocked["gate_record"],
               binding_hashes=bindings)


def test_binding_hash_mismatch_rejected():
    d = _inputs()
    bad = dict(d["bindings"], tl5_gate_record_core="0" * 64)
    with pytest.raises(ValueError, match="不一致"):
        _build(binding_hashes=bad)
    missing = {k: v for k, v in d["bindings"].items()
               if k != "approvals_decision_ledger"}
    with pytest.raises(ValueError, match="64hex"):
        _build(binding_hashes=missing)


def test_v1_pass_chain_not_reevaluable_here():
    d = _inputs()
    doctored = json.loads(json.dumps(d["v1"]))
    for pid in doctored:
        for p in doctored[pid]["required_predicates"]:
            if p["id"] == "adoption_machine_gate_pass":
                p["value"] = True
    with pytest.raises(ValueError, match="只处理 v1 blocked"):
        _build(v1_gate_records=doctored)


def test_keyset_mismatch_rejected():
    d = _inputs()
    with pytest.raises(ValueError, match="键集"):
        _build(patch_ids={"smoke-2l": d["patch_ids"]["smoke-2l"]})


# ---------------------------------------------------------------------------
# 确定性与生成器纪律
# ---------------------------------------------------------------------------

def test_builder_deterministic_byte_exact():
    r1 = hashing.canonical_json_bytes(_build()[0])
    r2 = hashing.canonical_json_bytes(_build()[0])
    assert r1 == r2
    text = r1.decode("utf-8")
    assert "C:\\\\" not in text
    assert not any(tok in text for tok in (
        "evaluated_at\": \"", "elapsed_s\": 0", '"host": "'))


def test_v3cli_gate_e2e_on_v2_spec(capsys, tmp_path):
    result = _build()[0]
    spec_path = tmp_path / "spec.json"
    spec_path.write_bytes(hashing.canonical_json_bytes(
        result["gate_specs_v2"]["smoke-4l"]))
    rc = v3cli.main(["gate", "--spec", str(spec_path)])
    out = capsys.readouterr().out
    d = json.loads(out)
    assert rc in (1, 2, 3)
    assert d["command"] == "v3-gate"
    assert d["gate_record"]["result"] == "fail"
    assert d["verify_errors"] == []
    assert "predicate_failed:holdout_non_regression_evidenced" in \
        d["gate_record"]["failure_codes"]
    # stdout canonical 且与直接求值 byte 一致
    direct = gate_mod.evaluate_gate(**result["gate_specs_v2"]["smoke-4l"])
    assert d["gate_core_hash"] == gate_mod.gate_core_hash(direct)


def test_execution_record_builder():
    written = [{"path": "out/v3-tl4/eval-holdout-unlock.json",
                "sha256": "a" * 64}]
    recheck = {"x": {"v1_binding": "b" * 64, "now": "b" * 64,
                     "unchanged": True}}
    rec = autotune_chain.build_unlock_execution_record(
        written_files=written, baseline_config_recheck=recheck,
        protected_files_recheck=recheck,
        datasets_zero_write={"snapshot_files": 340, "changed": 0,
                             "note": "declared_by_orchestration"})
    assert rec["adoption_applied"] is False
    assert rec["written_files"] == written
    with pytest.raises(ValueError):
        autotune_chain.build_unlock_execution_record(
            written_files=[{"path": "x", "sha256": "short"}],
            baseline_config_recheck=recheck,
            protected_files_recheck=recheck,
            datasets_zero_write={})


def test_low_dof_denominator_is_executed_not_corpus():
    """TD2 分母口径：语料在库板数不替代已执行对比板数。"""
    ok1 = autotune_chain.check_low_dof(
        {"a": 1, "b": 2}, {"a": 9, "b": 3},
        autotune_chain.EXECUTED_HOLDOUT_DENOMINATOR)
    assert ok1["holdout_denominator"] == 0
    assert ok1["low_dof_compliant"] is False        # 双参数+分母 0
    rich = autotune_chain.check_low_dof(
        {"a": 1, "b": 2}, {"a": 9, "b": 3},
        12)                                         # 12 板已执行对比后
    assert rich["samples_insufficient"] is False
    assert rich["low_dof_compliant"] is True        # 届时才解禁多参数
