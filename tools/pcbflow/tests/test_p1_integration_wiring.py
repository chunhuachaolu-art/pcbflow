"""P1/P2 纠偏新接口的编排层集成复验（V3-RECOMMENDATIONS §4.1）。

与 test_p1a/p1b/p1c/p2 纯函数测试的分工：本文件全部走**编排层入口**
（autotune_chain.build_chain / v3cli / critic_run 消费路径 / artifact_roles
公共消费合同，带真实 smoke profile fixtures），证明真实链路确实调用
P1/P2 纠偏新接口，而不是只有纯函数测试通过。产品代码零改动：接线证据
用 monkeypatch spy 在调用缝合处捕获（不改被调方语义，只记录与透传）。

三条现状判定（本文件断言即记录，复验结论见各测试 docstring）：
1. adoption_gate_paired 已接线：autotune_chain.build_chain 内 adoption
   决策唯一来源=proposer.adoption_gate_paired（autotune_chain.py:820），
   bundle 的 adoption artifact hash 锚定该门返回值；proposer.adoption_gate
   在编排层仅剩 build_negative_witnesses 的合成负向 witness 调用
   （:672-686，holdout_results= 合成板，非真实采纳路径）——合法角色，
   非残留缺口。
2. judge 绑定在 critic_run 的现状=批准设计：TL-2 ingest_run 以
   judge_gate_pass 布尔（缺省 False，fail-closed）接收编排侧实测值，
   critic_run 内无 evaluate_pre/build_pre/adoption_check 绑定引用；
   完整 P1-B 绑定（execution_id 绑定/工具链对账）在 TL-4 链内真实执行
   （autotune_chain.py:899-964）并在本文件经真实链记录复验。非接线缺口。
3. artifact_roles staging 接线=故意延迟（APR-0014）：STAGING_BINDING_POLICY
   enforcement 明示"下一轮 TL-5 staging 生产恢复时接线"；本文件以模块
   引用扫描断言当前包内仅 schemas.py 引用 artifact_roles（生产编排模块
   零引用），未来任何提前/意外接线都会被该观察断言暴露。

依赖 cwd=pcbflow 根（既有测试约定）。只读 profiles/；零写盘、零网络、
无 wall-clock 断言。
"""

from __future__ import annotations

import inspect
import json
import os
import pkgutil

import pytest

from pcbflow import artifact_roles as ar
from pcbflow import autotune_chain, critic, critic_run, hashing, judge
from pcbflow import proposer, v3cli

P4L = os.path.join("profiles", "smoke-4l")
P2L = os.path.join("profiles", "smoke-2l")
PATHS = {
    "smoke-4l": {
        "profile": os.path.join(P4L, "profile.json"),
        "manifest": os.path.join(P4L, "manifest.json"),
        "space": os.path.join(P4L, "inputs", "search-space.json"),
        "baseline": os.path.join(P4L, "inputs", "baseline-config.json"),
    },
    "smoke-2l": {
        "profile": os.path.join(P2L, "profile.json"),
        "manifest": os.path.join(P2L, "manifest.json"),
        "space": os.path.join(P2L, "inputs", "search-space.json"),
        "baseline": os.path.join(P2L, "inputs", "baseline-config.json"),
    },
}


# ---------------------------------------------------------------------------
# 真实 smoke 链 fixture（构造方式与 tests/test_tl4_autotune_chain.py 一致）
# ---------------------------------------------------------------------------

def _load(profile_tag):
    p = PATHS[profile_tag]
    hashes, errors = v3cli._autotune_input_hashes(
        p["manifest"], p["space"], p["baseline"])
    assert errors == []
    return {
        "profile": json.load(open(p["profile"], encoding="utf-8")),
        "space": json.load(open(p["space"], encoding="utf-8")),
        "baseline": json.load(open(p["baseline"], encoding="utf-8")),
        "constraints": json.load(
            open(os.path.join(os.path.dirname(p["manifest"]), "inputs",
                              "constraints.json"), encoding="utf-8")),
        "hashes": hashes,
    }


def _build(profile_tag, **overrides):
    d = _load(profile_tag)
    bundle = autotune_chain.build_chain(
        d["profile"], d["space"], d["baseline"], d["constraints"],
        d["hashes"], snapshot_revision="smoke-r1",
        evaluator={"name": "pcbflow-v3-autotune-chain", "version": "1.0",
                   "code_sha256": hashing.sha256_file(
                       autotune_chain.__file__)},
        **overrides)
    return bundle, d


def _independent_context(d):
    """外部审计口径：从链输入独立导出 evaluate_pre 所需 context。"""
    return {
        "toolchain_lock_sha256": d["hashes"]["toolchain_lock"],
        "constraints_sha256": d["hashes"]["constraints"],
        "source_snapshot_sha256": hashing.sha256_bytes(
            hashing.canonical_json_bytes(dict(d["hashes"]))),
    }


# ===========================================================================
# P1-A：autotune 链 → adoption_gate_paired 接线复验
# ===========================================================================

def test_chain_adoption_invokes_paired_gate_not_legacy(monkeypatch):
    """接线证据：真实链的 adoption 决策唯一来源=adoption_gate_paired。

    spy 捕获（透传不改语义）：(1) 配对门恰被调 1 次、入参为链级白名单/
    required/方向表、holdout_pairs=链内事实（空）；(2) bundle 的
    adoption_gate_result artifact hash 与 ledger backtest 事件锚定的就是
    spy 捕获的门返回值（密码学绑定，非字段巧合）；(3) legacy
    adoption_gate 在链内只出现在 build_negative_witnesses 的 3 次合成
    负向 witness（全部带 holdout_results= 合成板）——即 :672-686 三处
    旧门调用的角色=负向路径机器复核，不参与真实采纳资格。
    """
    calls = {"paired": [], "legacy": []}
    real_paired = proposer.adoption_gate_paired
    real_legacy = proposer.adoption_gate

    def spy_paired(**kw):
        result = real_paired(**kw)
        calls["paired"].append((kw, result))
        return result

    def spy_legacy(*args, **kw):
        result = real_legacy(*args, **kw)
        calls["legacy"].append(kw)
        return result

    monkeypatch.setattr(proposer, "adoption_gate_paired", spy_paired)
    monkeypatch.setattr(proposer, "adoption_gate", spy_legacy)
    bundle, _ = _build("smoke-4l")

    # (1) 配对门恰 1 次、链级入参
    assert len(calls["paired"]) == 1
    kw, gate_result = calls["paired"][0]
    assert kw["holdout_pairs"] == []
    assert kw["whitelist_metrics"] == autotune_chain.WHITELIST_METRICS
    assert kw["required_metrics"] == autotune_chain.REQUIRED_METRICS
    assert kw["metric_directions"] == autotune_chain.METRIC_DIRECTIONS
    # (2) 链产物锚定的就是该门返回值（adoption 节字段逐一同源）
    gate_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(gate_result))
    assert bundle["artifact_hashes"]["adoption_gate_result"] == gate_sha
    backtest = bundle["ledger_entries"][4]
    assert backtest["entry_kind"] == "backtest"
    assert backtest["artifact_hashes"]["adoption_gate_result"] == gate_sha
    assert bundle["adoption"]["decision"] == gate_result["decision"]
    assert bundle["adoption"]["reasons"] == gate_result["reasons"]
    assert bundle["adoption"]["per_metric"] == gate_result["per_metric"]
    assert bundle["adoption"]["holdout"] == gate_result["holdout"]
    assert bundle["adoption"]["gate_mode"] == gate_result["gate_mode"]
    # (3) legacy 门仅剩合成负向 witness 角色
    assert len(calls["legacy"]) == 3
    assert all("holdout_results" in lw for lw in calls["legacy"])


def test_chain_rejects_real_board_regression_same_board_anchored(monkeypatch):
    """同板 baseline 锚定经真实链生效：逐板回退 → 链级 reject，不被全局
    基线掩盖。

    构造：用真实链第一次运行的 baseline/challenger metrics 作为逐板配对
    证据注入（模拟 TL-5 恢复后真实 holdout_pairs 进入链路）。HOLDOUT-B
    自身 baseline 优于全局（length_deviation 0.2 < 全局 0.4），其
    challenger 0.396 对自身回退、对全局仍"改善"——legacy 全局门据此误
    放行（缺陷对照）；配对门按同板锚定判回退 → 真实链端到端 reject，
    delta 只能来自同板差（0.396-0.2=0.196），且门谓词 evidence 如实
    记录 decision=reject。
    """
    bundle0, d = _build("smoke-4l")
    baseline_metrics = bundle0["baseline"]["metrics"]
    challenger_metrics = bundle0["challenger"]["metrics"]
    global_len = baseline_metrics["length_deviation"]
    assert global_len == pytest.approx(0.4)
    own_baseline = dict(baseline_metrics, length_deviation=global_len * 0.5)
    board_challenger = dict(challenger_metrics,
                            length_deviation=global_len * 0.99)
    # 缺陷对照：legacy 全局门把 challenger 锚到全局 0.4 → 0.396<0.4 判
    # "改善" → adopt_candidate（跨板回退被全局基线掩盖，纯函数层
    # test_p1a 已证；此处用真实链 metrics 复现在编排输入口径上仍成立）
    legacy = proposer.adoption_gate(
        baseline_metrics, board_challenger,
        whitelist_metrics=autotune_chain.WHITELIST_METRICS,
        required_metrics=autotune_chain.REQUIRED_METRICS,
        metric_directions=autotune_chain.METRIC_DIRECTIONS,
        holdout_results=[{"board_id": "HOLDOUT-B",
                          "metrics": dict(board_challenger)}])
    assert legacy["decision"] == "adopt_candidate"
    assert legacy["gate_mode"] == "global_baseline_legacy"

    design = d["hashes"]["profile"]
    lock = d["hashes"]["toolchain_lock"]

    def pair(board_id, base_m, chall_m, exec_b, exec_c):
        return {
            "board_id": board_id, "profile_id": "smoke-4l",
            "design_inputs_sha256": design,
            "toolchain_lock_sha256": lock,
            "baseline": {"config_id": "CFG-BASE", "execution_id": exec_b,
                         "output_sha256": design,
                         "metrics": dict(base_m),
                         "board_id": board_id, "profile_id": "smoke-4l"},
            "challenger": {"config_id": "CFG-CAND", "execution_id": exec_c,
                           "output_sha256": lock,
                           "metrics": dict(chall_m),
                           "board_id": board_id, "profile_id": "smoke-4l"},
        }

    pairs = [
        pair("HOLDOUT-A", baseline_metrics, challenger_metrics,
             "EXEC-HA-BASE", "EXEC-HA-CAND"),
        pair("HOLDOUT-B", own_baseline, board_challenger,
             "EXEC-HB-BASE", "EXEC-HB-CAND"),
    ]
    real_paired = proposer.adoption_gate_paired

    def inject(**kw):
        kw["holdout_pairs"] = list(kw.get("holdout_pairs") or []) + pairs
        return real_paired(**kw)

    monkeypatch.setattr(proposer, "adoption_gate_paired", inject)
    bundle, _ = _build("smoke-4l")
    adoption = bundle["adoption"]
    assert adoption["decision"] == "reject"
    assert adoption["gate_mode"] == "paired_v1"
    assert any("required_metric_regression" in r
               for r in adoption["reasons"])
    assert adoption["holdout"]["board_denominator"] == 2
    assert adoption["holdout"]["execution_denominator"] == 2
    assert [b["board_id"]
            for b in adoption["holdout"]["regressed_boards"]] == ["HOLDOUT-B"]
    assert adoption["holdout"]["non_regressed_boards"] == 1
    rows = [e for e in adoption["per_metric"]["length_deviation"]
            if e["board_id"] == "HOLDOUT-B"]
    assert rows and rows[0]["regressed"] is True
    # delta=0.396-0.2=0.196：只有同板锚定才会产生该值（全局锚定为改善）
    assert rows[0]["delta"] == pytest.approx(global_len * 0.49)
    # 链级后果：出口门谓词如实记录 reject（不伪造 pass）
    pred = {p["id"]: p for p in bundle["gate_record"]["required_predicates"]}
    assert pred["adoption_machine_gate_pass"]["value"] is False
    assert "decision=reject" in pred["adoption_machine_gate_pass"]["evidence"]
    assert pred["holdout_non_regression_evidenced"]["value"] is False


def test_chain_without_paired_evidence_blocked_not_silent_legacy_fallback():
    """holdout 对结构性缺失 → 真实链 blocked（配对口径），不静默回退
    全局门。

    链内无逐板配对执行证据（TL-5 未启动）是事实：adoption 决策必须是
    paired_v1 语义下的 blocked（holdout_pairs_missing、双分母为 0），
    而不是借 legacy 全局/合成口径伪造判定或放行。holdout 摘要不含
    legacy 键（denominator），理由措辞为配对口径。
    """
    bundle, _ = _build("smoke-4l")
    adoption = bundle["adoption"]
    assert adoption["decision"] == "blocked"
    assert adoption["gate_mode"] == "paired_v1"
    assert adoption["reasons"] == [
        "holdout_pairs_missing: 缺逐板配对 holdout 证据（fail-closed）"]
    assert adoption["holdout"]["board_denominator"] == 0
    assert adoption["holdout"]["execution_denominator"] == 0
    assert adoption["holdout"]["non_regression_rate"] == 0.0
    assert "denominator" not in adoption["holdout"]     # 无 legacy 分母键
    # 在库语料板数不得替代执行分母：链全程只执行搜索空间候选（无逐板
    # 配对证据），adoption 仍 blocked——50 候选/11 真实执行不被伪装分母
    assert len(bundle["executions"]) == 11
    # 链级出口：出口门同样 blocked（不伪造 pass），notes 声明口径
    assert bundle["gate_record"]["result"] == "blocked"
    assert "不得宣称出口门通过" in json.dumps(bundle, ensure_ascii=False)


def test_chain_low_dof_consumes_paired_board_denominator():
    """下游编排消费的是配对门的板分母：TD2 低自由度按 board_denominator
    判定，而非在库语料板数。

    真实链把 adoption_gate_paired 的 holdout.board_denominator 喂给
    check_low_dof（autotune_chain.py:825-826）：分母 0 → 样本不足，
    smoke-4l 双参数变更不合规（如实 False）；出口门谓词 evidence 记录
    "板分母 0"。smoke-2l 单参数变更则合规——分母来源相同。
    """
    bundle4, _ = _build("smoke-4l")
    low = bundle4["low_dof"]
    assert low["samples_insufficient"] is True
    assert low["changed_params"] == ["route_grid_mm", "via_penalty"]
    assert low["low_dof_compliant"] is False
    pred = {p["id"]: p
            for p in bundle4["gate_record"]["required_predicates"]}
    assert pred["low_dof_contract_compliant"]["value"] is False
    assert "板分母 0" in pred["low_dof_contract_compliant"]["evidence"]
    assert pred["low_dof_contract_compliant"]["evidence"].index(
        "0") < pred["low_dof_contract_compliant"]["evidence"].index(
        str(autotune_chain.LOW_DOF_MIN_HOLDOUT_BOARDS))
    bundle2, _ = _build("smoke-2l")
    low2 = bundle2["low_dof"]
    assert low2["samples_insufficient"] is True       # 同一配对分母来源
    assert low2["low_dof_compliant"] is True          # 单参数变更豁免


def test_chain_missing_input_hash_binding_fails_closed():
    """§4.2(6) 编排级负向（链上路径）：input_hashes 缺任一 64hex 绑定 →
    build_chain 入口 fail-closed ValueError，不产出链 bundle。"""
    d = _load("smoke-4l")
    for missing in ("toolchain_lock", "board", "baseline_config"):
        broken = {k: v for k, v in d["hashes"].items() if k != missing}
        with pytest.raises(ValueError, match="fail-closed"):
            autotune_chain.build_chain(
                d["profile"], d["space"], d["baseline"], d["constraints"],
                broken, snapshot_revision="smoke-r1",
                evaluator={"name": "e", "version": "1",
                           "code_sha256": "a" * 64})
        with pytest.raises(ValueError, match=missing):
            autotune_chain.build_chain(
                d["profile"], d["space"], d["baseline"], d["constraints"],
                broken, snapshot_revision="smoke-r1",
                evaluator={"name": "e", "version": "1",
                           "code_sha256": "a" * 64})


# ===========================================================================
# P1-B：judge 绑定（execution_id 绑定 / 工具链对账）经真实链复验
# ===========================================================================

def test_chain_judge_binding_end_to_end_on_real_records():
    """真实链的 judge pre→post 满足 P1-B 绑定不变量，且可被外部审计
    独立复验。

    链内（autotune_chain.py:899-964）build_pre→evaluate_pre→build_post
    →evaluate_post 真实执行：post.execution_id 与 pre 一致、
    pre_record_ref=pre canonical hash、adoption_check_v2 绑定检查通过；
    外部审计用链输入独立导出 context 复跑 evaluate_pre 仍 pre_ok=True
    （绑定可验证，非链内自说自话）；账本 judge_pre_hash 一致。
    """
    bundle, d = _build("smoke-4l")
    pre, post = bundle["judge_pre"], bundle["judge_post"]
    assert pre["execution_id"] == "TL4-AUTOTUNE-smoke-4l-R1"
    assert post["execution_id"] == pre["execution_id"]
    assert post["pre_record_ref"] == judge.pre_record_sha256(pre)
    assert bundle["judge_pre_evaluation"]["pre_ok"] is True
    assert bundle["judge_post_evaluation"]["post_ok"] is False   # 如实
    assert judge.adoption_check_v2([pre], post) == []
    # 外部独立复验（context 从链输入导出，非读链内部状态）
    assert judge.evaluate_pre(pre, _independent_context(d)) == \
        {"pre_ok": True, "failed": []}
    entries = bundle["ledger_entries"]
    assert entries[1]["entry_kind"] == "judge_pre"
    assert entries[1]["judge_pre_hash"] == judge.pre_record_sha256(pre)
    assert entries[3]["judge_post_hash"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(post))


def test_chain_post_execution_id_mismatch_rejected_on_real_pre():
    """P1-B 执行 ID 绑定在真实链记录上触发：真实链 A 的 pre 不得被绑定
    到另一次真实链运行的 execution_id（build_post ValueError）；伪造
    post 执行 ID 经 adoption_check_v2 拒绝。"""
    bundle_a, _ = _build("smoke-4l")
    exec_b = "TL4-AUTOTUNE-smoke-4l-R2"
    bundle_b, _ = _build("smoke-4l", execution_id=exec_b)
    pre_a, pre_b = bundle_a["judge_pre"], bundle_b["judge_pre"]
    post_a = bundle_a["judge_post"]
    assert pre_a["execution_id"] != pre_b["execution_id"]
    with pytest.raises(ValueError) as excinfo:
        judge.build_post(
            execution_id=exec_b, pre_record=pre_a, output_hash="d" * 64,
            l1_legal=True, layer_pure=True)
    msg = str(excinfo.value)
    assert pre_a["execution_id"][:12] in msg
    assert exec_b[:12] in msg
    # 账本级采纳检查：手改 post 执行 ID → execution_id 绑定拒绝
    forged = dict(post_a, execution_id=pre_b["execution_id"])
    errors = judge.adoption_check_v2([pre_a, pre_b], forged)
    assert errors
    assert any("execution_id" in e for e in errors)


def test_chain_pre_recheck_missing_or_stale_toolchain_context_fails():
    """P1-B 工具链对账在真实链 pre 上触发（编排产出记录 × 环境漂移）：
    context 缺 toolchain_lock_sha256 → fail（不再静默放行）；stale
    （环境锁漂移为另一合法 hash）→ 不一致 fail；上游 constraints 缺失
    → 缺失 fail。链自身内部对账 pre_ok=True——负向只在漂移侧触发。"""
    bundle, d = _build("smoke-4l")
    pre = bundle["judge_pre"]
    assert bundle["judge_pre_evaluation"]["pre_ok"] is True
    missing = _independent_context(d)
    del missing["toolchain_lock_sha256"]
    result = judge.evaluate_pre(pre, missing)
    assert result["pre_ok"] is False
    assert any("缺" in e and "toolchain_lock_sha256" in e
               for e in result["failed"])
    stale = _independent_context(d)
    stale["toolchain_lock_sha256"] = "f" * 64          # 合法 64hex 但漂移
    result2 = judge.evaluate_pre(pre, stale)
    assert result2["pre_ok"] is False
    assert any("不一致" in e for e in result2["failed"])
    no_constraints = _independent_context(d)
    del no_constraints["constraints_sha256"]
    result3 = judge.evaluate_pre(pre, no_constraints)
    assert result3["pre_ok"] is False
    assert any("constraints_sha256" in e for e in result3["failed"])


def test_critic_run_judge_gate_boolean_passthrough_observation():
    """现状观察（判定=批准设计，非接线缺口）：TL-2 critic_run 以
    judge_gate_pass 布尔（缺省 False=fail-closed）接收编排侧实测值，
    模块内无 evaluate_pre/build_pre/adoption_check 绑定引用；完整 P1-B
    绑定在 TL-1/TL-4 链内执行（本文件上两测已复验）。TD5 分流真实消费
    该布尔：False → 分流阻断并强制人工队列；True（其余不满足）→
    judge_gate_pass 条件消失（布尔确被消费而非忽略）。
    """
    source = inspect.getsource(critic_run)
    assert "evaluate_pre" not in source
    assert "build_pre" not in source
    assert "adoption_check" not in source
    param = inspect.signature(critic_run.ingest_run).parameters[
        "judge_gate_pass"]
    assert param.default is False
    # critic_run 启用 __future__ annotations → 注解为字符串 'bool'
    assert param.annotation in (bool, "bool")
    # TD5 消费路径（ingest_run 内部调 critic.triage）
    blocked = critic.triage(
        {"critic_status": "executed"}, judge_gate_pass=False,
        required_checkers_executed=True, no_stale_or_unknown=True,
        whitelist_item=False)
    assert blocked["eligible"] is False
    assert "judge_gate_pass" in blocked["failed_conditions"]
    assert critic.MANUAL_QUEUE_MANDATORY in blocked["failed_conditions"]
    consumed = critic.triage(
        {"critic_status": "executed"}, judge_gate_pass=True,
        required_checkers_executed=False, no_stale_or_unknown=True,
        whitelist_item=False)
    assert "judge_gate_pass" not in consumed["failed_conditions"]
    assert consumed["eligible"] is False               # 其余条件仍守门


# ===========================================================================
# P2：artifact_roles 消费合同经公共接口（编排接线=故意延迟的观察）
# ===========================================================================

def _manifest_binding(source_sha256):
    return {"kind": ar.SBK_DATASET_MANIFEST_ENTRY,
            "manifest_ref": "out/v3-tl5/dataset-manifest-r2.json",
            "entry_key": "demo/board_a", "source_sha256": source_sha256}


def _source_decl():
    return ar.build_artifact_role_declaration(
        role=ar.ROLE_SOURCE, artifact_id="board-a", format_id="kicad_pcb",
        format_version="20171130",
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_TOOL_LOADABLE],
        source_binding=_manifest_binding("a" * 64), transform=None,
        output_sha256="a" * 64, rule_dependencies=[], check_scope=None,
        loss_notes=None)


def _analysis_decl():
    return ar.build_artifact_role_declaration(
        role=ar.ROLE_ANALYSIS, artifact_id="board-a.kicad_pcb",
        format_id="analysis", format_version="k9-path-r1",
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES],
        source_binding=_manifest_binding("a" * 64),
        transform={"description": "text-level normalization",
                   "tool": "pcbflow.corpus_convert",
                   "tool_version": "k9-path-r1", "saved_by": "scripts/s18"},
        output_sha256="b" * 64, rule_dependencies=[],
        check_scope=None,
        loss_notes={"graphics_and_text": "not in normalized board",
                    "zones": "not in normalized board"})


def _staging_decl():
    return ar.build_artifact_role_declaration(
        role=ar.ROLE_STAGING, artifact_id="board-a", format_id="kicad_pcb",
        format_version="20171130",
        capabilities=[ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_manifest_binding("a" * 64),
        transform={"description": "tool-saved staging package",
                   "tool": "kicad-cli", "tool_version": "10.0.5",
                   "saved_by": "kicad-cli pcb drc --save-board"},
        output_sha256="c" * 64, rule_dependencies=["kicad-cli default drc"],
        check_scope=ar.CHECK_SCOPE_BARE, loss_notes=None)


def _executor_kw():
    return dict(executor_backend="kicad-cli", executor_version="10.0.5",
                supported_formats=["kicad_pcb"],
                capabilities=list(ar.EXECUTION_CAPABILITIES))


def test_artifact_roles_consumption_contract_realistic_scenarios():
    """现实消费场景（经公共接口）：

    - source：作为绑定源声明合法（validate_declaration==[]，可被分析/
      转换消费），但**不可被执行器消费**（source_package_read_only，
      执行必须走 staging 包）——合同是"只读绑定源"，与简报口语
      "source 可消费"的差异按盘上合同为准；
    - analysis：构造即拒（analysis_model_not_executable），即使
      artifact_id 带 .kicad_pcb 后缀（path/后缀不参与判定）；
    - staging：能力/格式/check_scope 全匹配 → 可消费（[]）；
      能力超出执行器支持集 → 拒（capability_not_supported）。
    """
    src = _source_decl()
    assert ar.validate_declaration(src) == []
    errs_src = ar.validate_executor_consumption(src, **_executor_kw())
    assert [e["code"] for e in errs_src] == ["source_package_read_only"]
    ana = _analysis_decl()
    errs_ana = ar.validate_executor_consumption(ana, **_executor_kw())
    assert [e["code"] for e in errs_ana] == ["analysis_model_not_executable"]
    stg = _staging_decl()
    assert ar.validate_executor_consumption(stg, **_executor_kw()) == []
    over = dict(stg, capabilities=sorted(
        list(stg["capabilities"]) + [ar.CAP_TRANSFORM_TARGET
                                     if hasattr(ar, "CAP_TRANSFORM_TARGET")
                                     else ar.CAP_ANALYSIS_FEATURES]))
    errs_over = ar.validate_executor_consumption(over, **_executor_kw())
    assert any(e["code"] == "capability_not_supported" for e in errs_over)


def test_artifact_roles_staging_policy_deferred_wiring_observation():
    """现状观察（判定=故意延迟接线，APR-0014 批准）：

    - STAGING_BINDING_POLICY status=adopted / approval_ref=APR-0014 /
      enforcement 明示"下一轮 TL-5 staging 生产恢复时接线"；
    - 模块引用扫描：包内仅 schemas（contract id 引用）与
      artifact_roles 自身出现该模块引用；生产编排模块（autotune_chain/
      critic_run/judge/check_stage/v3cli）零引用——当前"未接线"状态
      被本断言钉住，未来任何提前/意外接线都会在此暴露。
    """
    policy = ar.STAGING_BINDING_POLICY
    assert policy["status"] == "adopted"
    assert policy["approval_ref"] == "APR-0014"
    assert "TL-5" in policy["enforcement"]
    assert "接线" in policy["enforcement"]
    import pcbflow
    hits = set()
    for modinfo in pkgutil.iter_modules(pcbflow.__path__):
        module = __import__("pcbflow." + modinfo.name, fromlist=["x"])
        if "artifact_roles" in inspect.getsource(module):
            hits.add(modinfo.name)
    assert hits == {"artifact_roles", "schemas"}


def test_staging_artifact_executor_entry_gated_by_policy_contract():
    """staging 按 policy 的现实入口场景：APR-0014 规则（未来 TL-5 staging
    产物必须携带声明+通过 validate_executor_consumption 才可进 executor）
    在公共接口上的消费闸门语义——无声明 → block；声明+消费检查通过 →
    allow；声明不满足消费合同（check_scope 缺 / 格式不支持）→ block。
    闸门本体是产品公共接口；测试内包装函数仅按 policy 文本组合调用
    （生产链接线本身按 APR-0014 故意延迟，见上一观察）。"""

    def staging_executor_entry_gate(declaration, **executor_kw):
        if ar.STAGING_BINDING_POLICY.get("status") != "adopted":
            raise ValueError("staging 绑定政策未生效")
        if declaration is None:
            return {"allowed": False,
                    "reasons": [{"code": "declaration_missing"}]}
        errors = (ar.validate_declaration(declaration)
                  + ar.validate_executor_consumption(declaration,
                                                     **executor_kw))
        return {"allowed": not errors, "reasons": errors}

    assert staging_executor_entry_gate(
        _staging_decl(), **_executor_kw())["allowed"] is True
    blocked_none = staging_executor_entry_gate(None, **_executor_kw())
    assert blocked_none["allowed"] is False
    no_scope = dict(_staging_decl(), check_scope=None)
    blocked_scope = staging_executor_entry_gate(no_scope, **_executor_kw())
    assert blocked_scope["allowed"] is False
    assert any(e["code"] == "check_scope_missing"
               for e in blocked_scope["reasons"])
    bad_format = dict(_staging_decl(), format_id="gds")
    blocked_fmt = staging_executor_entry_gate(bad_format, **_executor_kw())
    assert blocked_fmt["allowed"] is False
    assert any(e["code"] == "format_not_supported"
               for e in blocked_fmt["reasons"])


# ===========================================================================
# §4.2(6) 编排级负向（链上路径）与最外层入口
# ===========================================================================

def test_chain_judge_post_fail_keeps_gate_blocked():
    """§4.2(6)：judge_post 如实 fail（smoke 闭式 executor 无 DRC 产物可
    绑 drc refs）沿链传播 → 出口门 judge_post_ok=False 且 gate blocked
    （missing_input）——judge 负向在链上路径生效，不因 adoption 已
    blocked 而被短路或粉饰。"""
    bundle, _ = _build("smoke-4l")
    post_eval = bundle["judge_post_evaluation"]
    assert post_eval["post_ok"] is False
    assert any("drc_batch_ref" in f for f in post_eval["failed"])
    record = bundle["gate_record"]
    pred = {p["id"]: p for p in record["required_predicates"]}
    assert pred["judge_post_ok"]["value"] is False
    assert "post_ok=False" in pred["judge_post_ok"]["evidence"]
    assert pred["judge_pre_ok"]["value"] is True       # pre/post 独立如实
    assert record["result"] == "blocked"
    assert "missing_input" in record["failure_codes"]
    inputs = {i["artifact_id"]: i for i in record["inputs"]}
    assert inputs["holdout_corpus"]["status"] == "missing"
    assert inputs["holdout_corpus"]["sha256"] is None


def test_v3cli_entry_end_to_end_paired_gate_and_blocked(capsys):
    """最外层编排入口（v3cli proposer --select autotune-chain）端到端：
    真实 profile 文件 → 链 → adoption=paired_v1 blocked、出口门
    blocked、exit 2、账本零错、adoption artifact hash 在场（64hex）。
    """
    p = PATHS["smoke-4l"]
    rc = v3cli.main([
        "proposer", "--select", "autotune-chain",
        "--profile", p["profile"], "--space", p["space"],
        "--baseline", p["baseline"], "--snapshot-revision", "smoke-r1"])
    out = capsys.readouterr().out
    d = json.loads(out)
    assert rc == 2
    assert d["status"] == "blocked"
    assert d["adoption"]["decision"] == "blocked"
    assert d["adoption"]["gate_mode"] == "paired_v1"
    assert d["adoption"]["holdout"]["board_denominator"] == 0
    assert d["gate_record"]["result"] == "blocked"
    assert d["ledger_verify"] == {"chain_errors": [],
                                  "supersedes_errors": []}
    assert len(d["artifact_hashes"]["adoption_gate_result"]) == 64
