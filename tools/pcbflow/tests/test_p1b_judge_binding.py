"""P1-B judge 绑定修正测试（pre → execution → post → check 实际绑定）。

全部合成数据：不依赖真实板卡、外部执行或既有 out/ 产物。
覆盖合同缺陷修正：
1. build_post 强制 execution_id 与 pre_record 一致（post 可绑另一次执行的洞）；
2. evaluate_pre 的 toolchain_lock_sha256 两侧必须在场且匹配（context 缺键
   静默放行的洞）；
3. adoption_check_v2 绑定级采纳检查（ref 命中 + execution_id 一致 + 拷贝
   上下文字段逐一相等 + 可选复跑 pre 门）；
4. v1 adoption_check 行为不变冒烟。
"""

import pytest

from pcbflow import judge


def _h(ch: str) -> str:
    return ch * 64


# ---------------------------------------------------------------------------
# 合成工厂（与 test_tl1 同构；execution_id 用 14 字符串验证 12 位前缀截断）
# ---------------------------------------------------------------------------

def _pre(execution_id="EXEC-AAAA-0001", **over):
    kw = dict(
        execution_id=execution_id,
        project_id="revc-coreboard",
        profile_id="revc-tbd1",
        candidate_id="CAND-0001",
        source_snapshot_sha256=_h("a"),
        toolchain_lock_sha256=_h("b"),
        executor={"backend": "deterministic-internal", "protocol": "internal",
                  "version": "1", "capability": "route-v1"},
        write_scope="staging_only",
        allowlist=("staging/board.kicad_pcb",),
        required_checks=("drc_batch", "drc_final"),
        upstream_hashes={"constraints_sha256": _h("c")},
        patch_preconditions=())
    kw.update(over)
    return judge.build_pre(**kw)


def _ctx(**over):
    ctx = {"source_snapshot_sha256": _h("a"),
           "toolchain_lock_sha256": _h("b"),
           "constraints_sha256": _h("c")}
    ctx.update(over)
    return ctx


def _post(pre, **over):
    kw = dict(
        execution_id=pre["execution_id"],
        pre_record=pre,
        output_hash=_h("d"),
        l1_legal=True,
        layer_pure=True,
        drc_batch_ref=_h("e"),
        drc_final_ref=_h("f"),
        erc_ref=_h("1"),
        test_manifest_hash=_h("2"),
        replay_ref=_h("3"),
        solver={"status": "UNSAT", "proof_ref": _h("7")})
    kw.update(over)
    return judge.build_post(**kw)


# ---------------------------------------------------------------------------
# build_post：执行 ID 绑定（缺陷 1 修正）
# ---------------------------------------------------------------------------

def test_build_post_execution_id_mismatch_raises():
    # post 携带另一次执行的 execution_id → ValueError，消息含两侧前 12 位
    pre = _pre(execution_id="EXEC-AAAA-0001")
    with pytest.raises(ValueError) as excinfo:
        _post(pre, execution_id="EXEC-BBBB-0002")
    msg = str(excinfo.value)
    assert "EXEC-AAAA-00" in msg   # pre 侧前 12 位
    assert "EXEC-BBBB-00" in msg   # post 侧前 12 位


def test_build_post_matching_execution_id_builds():
    # 一致 → 正常构造，post.execution_id == pre.execution_id，ref 命中
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    assert post["execution_id"] == "EXEC-AAAA-0001"
    assert post["execution_id"] == pre["execution_id"]
    assert post["pre_record_ref"] == judge.pre_record_sha256(pre)


# ---------------------------------------------------------------------------
# evaluate_pre：toolchain 两侧在场且匹配（缺陷 2 修正）
# ---------------------------------------------------------------------------

def test_evaluate_pre_context_missing_toolchain_fails():
    # context 缺 toolchain_lock_sha256 → fail（不再静默放行），reason 命中"缺"
    ctx = _ctx()
    del ctx["toolchain_lock_sha256"]
    result = judge.evaluate_pre(_pre(), ctx)
    assert result["pre_ok"] is False
    assert any("缺" in e and "toolchain_lock_sha256" in e
               for e in result["failed"])
    # 显式 None 同样 fail
    result_none = judge.evaluate_pre(_pre(), _ctx(toolchain_lock_sha256=None))
    assert result_none["pre_ok"] is False
    assert any("缺" in e for e in result_none["failed"])


def test_evaluate_pre_context_toolchain_mismatch_fails():
    # context toolchain 与 record 不同 → fail（既有行为，防回归）
    result = judge.evaluate_pre(_pre(), _ctx(toolchain_lock_sha256=_h("9")))
    assert result["pre_ok"] is False
    assert any("不一致" in e for e in result["failed"])


# ---------------------------------------------------------------------------
# adoption_check_v2：绑定级采纳检查
# ---------------------------------------------------------------------------

def test_v2_execution_id_bound_to_other_execution_rejected():
    # post 绑定另一次执行（pre_records 含两条 pre，post.execution_id 指向
    # 另一条）→ errors 非空
    pre_a = _pre(execution_id="EXEC-AAAA-0001")
    pre_b = _pre(execution_id="EXEC-BBBB-0002", candidate_id="CAND-0002")
    post = _post(pre_a)
    forged = dict(post, execution_id="EXEC-BBBB-0002")  # 手改 post 执行 ID
    errors = judge.adoption_check_v2([pre_a, pre_b], forged)
    assert errors
    assert any("execution_id" in e for e in errors)


def test_v2_failed_pre_rejected_with_context_inputs():
    # pre 未通过（提供会 fail 的 ctx：toolchain 不一致）→ errors 非空
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    bad_ctx = _ctx(toolchain_lock_sha256=_h("9"))
    errors = judge.adoption_check_v2([pre], post, context_inputs=bad_ctx)
    assert errors
    assert any("pre 未通过" in e for e in errors)


def test_v2_tampered_copy_field_rejected():
    # post 的拷贝上下文字段被手改（constraints_sha256 与 pre 不同）→ 非空
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    forged = dict(post, constraints_sha256=_h("9"))
    errors = judge.adoption_check_v2([pre], forged)
    assert errors
    assert any("constraints_sha256" in e for e in errors)


def test_v2_ref_not_in_pre_set_rejected():
    # pre_record_ref 不在集合内 → errors 非空（与 v1 行为对齐）
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    forged = dict(post, pre_record_ref=_h("f"))
    errors = judge.adoption_check_v2([pre], forged)
    assert errors
    assert any("不可采纳" in e for e in errors)


def test_v2_full_binding_with_context_accepts():
    # 全绑定一致 + ctx 提供且 pre_ok → errors == []（ctx 未提供同样可采纳）
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    assert judge.adoption_check_v2([pre], post, context_inputs=_ctx()) == []
    assert judge.adoption_check_v2([pre], post) == []


def test_v2_same_drc_counts_do_not_bind():
    # 两份 DRC 错误计数相同 ≠ 同一候选：两条 pre（不同 execution_id）各自
    # build_post 且 drc refs 用同一 hash 值；adoption_check_v2 只认
    # execution_id/上下文绑定的那条，另一条判不可采纳。
    pre_a = _pre(execution_id="EXEC-AAAA-0001")
    pre_b = _pre(execution_id="EXEC-BBBB-0002")
    post_a = _post(pre_a, drc_batch_ref=_h("e"), drc_final_ref=_h("f"))
    post_b = _post(pre_b, drc_batch_ref=_h("e"), drc_final_ref=_h("f"))
    # DRC ref 完全相同、执行不同：计数相同不构成绑定
    assert post_a["drc_batch_ref"] == post_b["drc_batch_ref"]
    assert post_a["drc_final_ref"] == post_b["drc_final_ref"]
    assert post_a["execution_id"] != post_b["execution_id"]
    # 账本只含 pre_a：自身绑定可采纳；post_b 不可借同计数 DRC 证据被采纳
    assert judge.adoption_check_v2([pre_a], post_a) == []
    errors = judge.adoption_check_v2([pre_a], post_b)
    assert errors
    assert any("不可采纳" in e for e in errors)
    # 更强情形：把 post_b 的 ref 手改指向 pre_a，仍被执行 ID 绑定拒绝
    forged = dict(post_b, pre_record_ref=judge.pre_record_sha256(pre_a))
    errors2 = judge.adoption_check_v2([pre_a, pre_b], forged)
    assert errors2
    assert any("execution_id" in e for e in errors2)


def test_v1_adoption_check_behavior_unchanged_smoke():
    # v1 合同不变：只看 pre_record_ref 是否在已落账 hash 集内
    pre = _pre(execution_id="EXEC-AAAA-0001")
    post = _post(pre)
    ref = judge.pre_record_sha256(pre)
    assert judge.adoption_check({ref}, post) == []
    errs = judge.adoption_check(set(), post)
    assert errs
    assert any("不可采纳" in e for e in errs)
    # v1 无 context_inputs 复跑语义（签名不变）
    with pytest.raises(TypeError):
        judge.adoption_check({ref}, post, context_inputs=_ctx())
