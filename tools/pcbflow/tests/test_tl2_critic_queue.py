"""TL-2 会话测试：TD4 Critic advisory 分诊 + TD5 queue-event-ledger。

覆盖（SPEC-v3.0-PROPOSAL §TD4/§TD5；机器出口门：invalid/not_executed/
stale/低置信全部 blocked→人工；有限分流前通过分层指标门）：
- TD5 路由谓词逐条：每个条件单独置 False → blocked + failed_conditions
  含对应 id；全 True → queue_deprioritized；judge fail/白名单 →
  manual_queue_mandatory 注记；
- flags=[] 语义：critic_status=not_executed 时不是「无旗」而是 blocked；
- promotion_gate：样本不足/单板 recall 低/abstain 高/审计缺 →
  not_promoted；全过 → candidate；human_support 0.9 单独不晋升；
- L2 加旗律：add_flag 单调增长；模块无消旗函数（dir 断言）；
- 队列 hash 链：合法 5 事件链；篡改（body/prev/seq）→报错；重复
  enqueue 同 item→报错；approve 后再 review→报错；approve
  actor_role="agent"→报错；
- current_queue/projection_summary：2 open + 1 closed → length=2、
  by_reason 正确；
- audit_decision 三分支 + audit_config 校验。

纯内存构造（生成器模式）：零子进程/零写盘/零网络。
"""

import pytest

from pcbflow import critic, hashing, queue


def _sha(seed: str) -> str:
    return hashing.sha256_text(seed)


def _ok_run() -> dict:
    """全前置成立的 executed run（triage 全绿基线）。"""
    return critic.build_run(
        critic_run_id="CR-0001",
        candidate_id="CAND-0001",
        critic_status="executed",
        model={"provider": "mock-provider", "version": "1.2.3",
               "approved": True},
        input_hashes={"board": _sha("board"), "diff": _sha("diff"),
                      "summary": _sha("summary")},
        input_hashes_match=True,
        calibration={"in_calibrated_range": True},
        evidence_refs=[_sha("ev-1")],
        profile_promotion_state="shadow",
    )


def _triage(run, **over):
    kw = {"judge_gate_pass": True, "required_checkers_executed": True,
          "no_stale_or_unknown": True, "whitelist_item": False}
    kw.update(over)
    return critic.triage(run, **kw)


# ---------------------------------------------------------------------------
# TD5 路由谓词：逐条件
# ---------------------------------------------------------------------------

def test_triage_all_pass_queue_deprioritized():
    run = _ok_run()
    d = _triage(run)
    assert d == {"eligible": True, "status": "queue_deprioritized",
                 "failed_conditions": []}
    assert run["auto_route"] == d          # 写入 run 并返回
    assert critic.validate_run(run) == []  # 写入后仍 schema 合法


def test_triage_judge_gate_fail():
    d = _triage(_ok_run(), judge_gate_pass=False)
    assert d["eligible"] is False
    assert d["status"] == "critic_auto_route_blocked"
    assert "judge_gate_pass" in d["failed_conditions"]
    assert "manual_queue_mandatory" in d["failed_conditions"]


def test_triage_whitelist_item():
    d = _triage(_ok_run(), whitelist_item=True)
    assert d["eligible"] is False
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["item_not_whitelist",
                                      "manual_queue_mandatory"]


def test_triage_required_checkers_missing():
    d = _triage(_ok_run(), required_checkers_executed=False)
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["required_checkers_executed"]


def test_triage_stale_or_unknown():
    d = _triage(_ok_run(), no_stale_or_unknown=False)
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["no_stale_or_unknown"]


def test_triage_critic_status_not_executed():
    run = critic.build_run(
        critic_run_id="CR-0002", candidate_id="CAND-0001",
        critic_status="not_executed",
        model={"provider": "mock-provider", "version": "1.2.3",
               "approved": True},
        input_hashes={"board": _sha("board")},
        input_hashes_match=True,
        calibration={"in_calibrated_range": True})
    d = _triage(run)
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["critic_status_executed"]


def test_triage_schema_invalid():
    run = _ok_run()
    run["rogue_key"] = 1                  # additionalProperties=false
    d = _triage(run)
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["critic_schema_valid"]


def test_triage_input_hashes_mismatch():
    run = _ok_run()
    run["input_hashes_match"] = False
    d = _triage(run)
    assert d["failed_conditions"] == ["critic_input_hashes_match"]


def test_triage_model_not_approved():
    run = _ok_run()
    run["model"]["approved"] = False
    d = _triage(run)
    assert d["failed_conditions"] == ["critic_model_approved"]


def test_triage_calibration_out_of_range():
    run = _ok_run()
    run["calibration"]["in_calibrated_range"] = False
    d = _triage(run)
    assert d["failed_conditions"] == ["critic_calibration_in_range"]


def test_triage_flags_nonempty():
    run = _ok_run()
    critic.add_flag(run, "courtyard_crowding", 0.9,
                    location="U3 courtyard", evidence_ref=_sha("ev-c"))
    d = _triage(run)
    assert d["status"] == "critic_auto_route_blocked"
    assert d["failed_conditions"] == ["critic_flags_empty"]


# ---------------------------------------------------------------------------
# flags=[] 语义（TD4：不是无条件「无旗」）
# ---------------------------------------------------------------------------

def test_flags_empty_semantics_ok():
    s = critic.flags_empty_semantics(_ok_run())
    assert s["means_no_flags"] is True


def test_flags_empty_with_not_executed_is_blocked_not_clean():
    """flags=[] + critic_status=not_executed → blocked（不是无旗）。"""
    run = critic.build_run(
        critic_run_id="CR-0003", candidate_id="CAND-0002",
        critic_status="not_executed",
        model={"provider": "mock-provider", "version": None,
               "approved": False},
        input_hashes={"board": _sha("board")})
    assert run["flags"] == []
    d = _triage(run)
    assert d["eligible"] is False
    assert d["status"] == "critic_auto_route_blocked"
    assert "critic_status_executed" in d["failed_conditions"]
    s = critic.flags_empty_semantics(run)
    assert s["means_no_flags"] is False
    assert "executed" in s["reason"]


def test_flags_empty_semantics_missing_preconditions():
    for mutate in (
        lambda r: r.__setitem__("input_hashes_match", False),
        lambda r: r["model"].__setitem__("approved", False),
        lambda r: r["calibration"].__setitem__("in_calibrated_range", False),
        lambda r: r.__setitem__("rogue", 1),
        lambda r: critic.add_flag(r, "silk_readability", 0.7),
    ):
        run = _ok_run()
        mutate(run)
        s = critic.flags_empty_semantics(run)
        assert s["means_no_flags"] is False, s
        assert s["reason"]


# ---------------------------------------------------------------------------
# build_run / validate_run / add_flag（L2 加旗律）
# ---------------------------------------------------------------------------

def test_build_run_forces_advisory_only_and_self_check():
    run = _ok_run()
    assert run["advisory_only"] is True
    assert run["schema_validation"]["valid"] is True
    with pytest.raises(ValueError):       # 未知 opt 键 fail-closed
        critic.build_run(critic_run_id="CR-x", candidate_id="C",
                         critic_status="executed",
                         model={"provider": "p", "version": None,
                                "approved": True},
                         input_hashes={}, rogue_key=1)
    with pytest.raises(ValueError):       # executed 缺前置 → 构造期拒绝
        critic.build_run(critic_run_id="CR-y", candidate_id="C",
                         critic_status="executed",
                         model={"provider": "p", "version": None,
                                "approved": True},
                         input_hashes={"board": _sha("b")})


def test_validate_run_executed_requires_explicit_preconditions():
    for drop in ("input_hashes_match", "calibration"):
        run = _ok_run()
        del run[drop]
        errs = critic.validate_run(run)
        assert errs, drop
    run = _ok_run()
    del run["model"]["approved"]
    errs = critic.validate_run(run)
    assert errs and any("approved" in e for e in errs)


def test_add_flag_monotonic_and_no_unflag_api():
    run = _ok_run()
    assert run["flags"] == []
    critic.add_flag(run, "silk_readability", 0.81, location="R12")
    critic.add_flag(run, "suspicious_reroute", 0.42,
                    evidence_ref=_sha("ev-r"))
    assert [f["category"] for f in run["flags"]] == [
        "silk_readability", "suspicious_reroute"]     # 只增不减
    assert critic.validate_run(run) == []
    with pytest.raises(ValueError):
        critic.add_flag(run, "drc_error", 0.9)        # 类别不在 advisory 集
    with pytest.raises(ValueError):
        critic.add_flag(run, "silk_readability", 1.5)  # 置信度越界
    # L2 加旗律：模块不定义消旗/降级函数
    assert "remove_flag" not in dir(critic)
    assert "clear_flag" not in dir(critic)
    assert not hasattr(critic, "remove_flag")
    assert not hasattr(critic, "clear_flag")


# ---------------------------------------------------------------------------
# promotion_gate（TD4 晋升门）
# ---------------------------------------------------------------------------

def _ok_eval(**over) -> dict:
    ev = {
        "total_samples": 250,
        "per_board_metrics": [
            {"board_id": "BRD-1", "precision": 0.9, "recall": 0.92,
             "fpr": 0.05, "fnr": 0.08},
            {"board_id": "BRD-2", "precision": 0.85, "recall": 0.86,
             "fpr": 0.12, "fnr": 0.14},
        ],
        "abstain_rate": 0.05,
        "calibration_error": 0.03,
        "worst_board": {"board_id": "BRD-2", "recall": 0.78},
        "independent_audit": {"sample_count": 50, "pass": True},
        "human_support_rate": 0.9,
    }
    ev.update(over)
    return ev


def test_promotion_gate_all_pass_candidate():
    out = critic.promotion_gate(_ok_eval())
    assert out["promotion_state"] == "candidate"
    assert out["failed"] == []
    assert out["human_support_rate_ok"] is True


def test_promotion_gate_insufficient_samples():
    out = critic.promotion_gate(_ok_eval(total_samples=100))
    assert out["promotion_state"] == "not_promoted"
    assert "insufficient_samples" in out["failed"]
    assert "全量陪审" in out["note"]
    # min_samples 可参数覆盖
    out2 = critic.promotion_gate(_ok_eval(total_samples=100),
                                 min_samples=50)
    assert out2["promotion_state"] == "candidate"


def test_promotion_gate_board_recall_low():
    boards = _ok_eval()["per_board_metrics"]
    boards[1]["recall"] = 0.6
    out = critic.promotion_gate(_ok_eval(per_board_metrics=boards))
    assert out["promotion_state"] == "not_promoted"
    assert "board_recall_low:BRD-2" in out["failed"]


def test_promotion_gate_board_fpr_high():
    boards = _ok_eval()["per_board_metrics"]
    boards[0]["fpr"] = 0.3
    out = critic.promotion_gate(_ok_eval(per_board_metrics=boards))
    assert out["promotion_state"] == "not_promoted"
    assert "board_fpr_high:BRD-1" in out["failed"]


def test_promotion_gate_abstain_high():
    out = critic.promotion_gate(_ok_eval(abstain_rate=0.4))
    assert out["promotion_state"] == "not_promoted"
    assert "abstain_rate_high" in out["failed"]


def test_promotion_gate_calibration_error_high():
    out = critic.promotion_gate(_ok_eval(calibration_error=0.2))
    assert "calibration_error_high" in out["failed"]


def test_promotion_gate_worst_board_low():
    out = critic.promotion_gate(
        _ok_eval(worst_board={"board_id": "BRD-2", "recall": 0.5}))
    assert "worst_board_recall_low" in out["failed"]


def test_promotion_gate_audit_missing_or_failed():
    out = critic.promotion_gate(
        _ok_eval(independent_audit={"sample_count": 10, "pass": True}))
    assert out["promotion_state"] == "not_promoted"
    assert "audit_samples_insufficient" in out["failed"]
    out2 = critic.promotion_gate(
        _ok_eval(independent_audit={"sample_count": 50, "pass": False}))
    assert "audit_not_passed" in out2["failed"]
    out3 = critic.promotion_gate({k: v for k, v in _ok_eval().items()
                                  if k != "independent_audit"})
    assert "missing:independent_audit" in out3["failed"]


def test_promotion_gate_human_support_alone_does_not_promote():
    """human_support 0.9 单独不构成晋升：其他条件差时仍 not_promoted。"""
    bad = _ok_eval(total_samples=30,
                   per_board_metrics=[{"board_id": "BRD-X", "recall": 0.4,
                                       "fpr": 0.4}],
                   human_support_rate=0.9)
    out = critic.promotion_gate(bad)
    assert out["promotion_state"] == "not_promoted"
    assert out["human_support_rate_ok"] is True   # 记录但不放行
    # 反向：human_support 低不阻断 candidate（只作附加条件）
    out2 = critic.promotion_gate(_ok_eval(human_support_rate=0.5))
    assert out2["promotion_state"] == "candidate"
    assert out2["human_support_rate_ok"] is False


# ---------------------------------------------------------------------------
# queue-event-ledger：构造、hash 链与状态机
# ---------------------------------------------------------------------------

def _eq(events, **kw):
    return queue.make_event(events, **kw)


def _chain5():
    """合法 5 事件链：enqueue→assign→review→（并行 item）→approve。"""
    evs = queue.empty_ledger()["events"]
    refs = {"project_id": "coreboard", "profile_id": "revc",
            "snapshot_revision": "p3",
            "fact_ref": _sha("fact"), "gate_ref": _sha("gate"),
            "critic_ref": _sha("critic")}
    evs, e1 = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-1", actor="pcbflow-critic",
        actor_role="critic_model", reason_code="critic_auto_route_blocked",
        refs=refs))
    evs, e2 = queue.append(evs, _eq(
        evs, event="assign", item_id="ITEM-1", actor="triager",
        actor_role="agent"))
    evs, e3 = queue.append(evs, _eq(
        evs, event="review", item_id="ITEM-1", actor="alice",
        actor_role="human_reviewer"))
    evs, e4 = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-2", actor="pcbflow-critic",
        actor_role="critic_model", reason_code="judge_gate_fail"))
    evs, e5 = queue.append(evs, _eq(
        evs, event="approve", item_id="ITEM-1", actor="bob",
        actor_role="human_final"))
    return evs, [e1, e2, e3, e4, e5]


def test_queue_legal_five_event_chain():
    evs, ev = _chain5()
    assert len(evs) == 5
    assert queue.verify_chain(evs) == []
    assert [e["event_seq"] for e in evs] == [0, 1, 2, 3, 4]
    assert evs[0]["prev_event_sha256"] is None       # Genesis
    for i in range(1, 5):
        assert evs[i]["prev_event_sha256"] == evs[i - 1]["event_sha256"]
    # event_sha256 = 剔除链字段后的 body hash（确定性）
    for e in ev:
        assert e["event_sha256"] == queue.event_body_sha256(e)
    assert queue.event_body_sha256(ev[0]) == queue.event_body_sha256(ev[0])


def test_queue_tamper_body_detected():
    evs, _ = _chain5()
    tampered = [dict(e) for e in evs]
    tampered[1]["actor"] = "mallory"                 # 篡改记录体（不动 hash）
    errs = queue.verify_chain(tampered)
    assert errs
    assert any("event_sha256" in e for e in errs)    # 自身 body hash 失配
    # 攻击者重算被篡改事件的 event_sha256：仍必须被下家 prev 链断裂揭发
    rehashed = [dict(e) for e in evs]
    rehashed[1]["actor"] = "mallory"
    rehashed[1]["event_sha256"] = queue.event_body_sha256(rehashed[1])
    errs2 = queue.verify_chain(rehashed)
    assert errs2 and any("prev_event_sha256" in e for e in errs2)


def test_queue_tamper_reason_code_and_seq_detected():
    evs, _ = _chain5()
    t1 = [dict(e) for e in evs]
    t1[3]["reason_code"] = "forged"
    assert queue.verify_chain(t1)
    t2 = [dict(e) for e in evs]
    t2[1]["event_seq"] = 7                           # seq 不连续
    errs = queue.verify_chain(t2)
    assert any("event_seq" in e for e in errs)
    t3 = [dict(e) for e in evs]
    t3[2]["prev_event_sha256"] = _sha("broken-link")  # 链接被改
    errs = queue.verify_chain(t3)
    assert any("prev_event_sha256" in e for e in errs)


def test_queue_append_rejects_tampered_event():
    evs, _ = _chain5()
    bad = dict(evs[2])
    bad["actor"] = "mallory"                          # hash 未重算
    with pytest.raises(ValueError):
        queue.append(evs, bad)


def test_queue_duplicate_enqueue_rejected():
    evs = queue.empty_ledger()["events"]
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-1", actor="a",
        actor_role="agent", reason_code="r"))
    with pytest.raises(ValueError):                   # 同 item 再 enqueue
        _eq(evs, event="enqueue", item_id="ITEM-1", actor="a",
            actor_role="agent")
    # 终态（approve）后同 item 再 enqueue 同样报错
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="ITEM-1", actor="t",
        actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="approve", item_id="ITEM-1", actor="bob",
        actor_role="human_final"))
    with pytest.raises(ValueError):
        _eq(evs, event="enqueue", item_id="ITEM-1", actor="a",
            actor_role="agent")
    # 新 item_id 的 enqueue 不受影响
    ev2 = _eq(evs, event="enqueue", item_id="ITEM-2", actor="a",
              actor_role="agent")
    assert ev2["item_id"] == "ITEM-2"


def test_queue_event_after_terminal_rejected():
    evs, _ = _chain5()                                # ITEM-1 已 approve
    for kind in ("review", "assign", "escalate", "downgrade", "expire",
                 "approve"):
        with pytest.raises(ValueError):
            _eq(evs, event=kind, item_id="ITEM-1", actor="alice",
                actor_role="human_reviewer")


def test_queue_approve_requires_assigned_state():
    evs = queue.empty_ledger()["events"]
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-9", actor="a",
        actor_role="agent"))
    with pytest.raises(ValueError):                   # open 状态不可 approve
        _eq(evs, event="approve", item_id="ITEM-9", actor="bob",
            actor_role="human_final")
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="ITEM-9", actor="t",
        actor_role="agent"))
    evs, _ = queue.append(evs, _eq(                   # assign 后合法
        evs, event="approve", item_id="ITEM-9", actor="bob",
        actor_role="human_final"))
    assert queue.verify_chain(evs) == []


def test_queue_actor_role_constraints():
    evs = queue.empty_ledger()["events"]
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-1", actor="t", actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="ITEM-1", actor="t",
        actor_role="agent"))                          # 机器 assign（建议）OK
    with pytest.raises(ValueError):                   # agent 不得 approve
        _eq(evs, event="approve", item_id="ITEM-1", actor="autobot",
            actor_role="agent")
    with pytest.raises(ValueError):                   # 机器角色不得 review
        _eq(evs, event="review", item_id="ITEM-1", actor="autobot",
            actor_role="critic_model")
    evs, _ = queue.append(evs, _eq(
        evs, event="review", item_id="ITEM-1", actor="alice",
        actor_role="human_reviewer"))
    # 手工伪造的机器 approve 也必须被 verify_chain 揭发
    forged = dict(evs[-1])
    forged.update({"event": "approve", "actor": "autobot",
                   "actor_role": "agent", "event_seq": 3,
                   "prev_event_sha256": evs[-1]["event_sha256"]})
    forged["event_sha256"] = queue.event_body_sha256(forged)
    errs = queue.verify_chain(evs + [forged])
    assert any("人工裁决" in e for e in errs)


def test_queue_downgrade_returns_to_open():
    evs = queue.empty_ledger()["events"]
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="ITEM-5", actor="a",
        actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="ITEM-5", actor="t",
        actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="downgrade", item_id="ITEM-5", actor="alice",
        actor_role="human_reviewer"))
    with pytest.raises(ValueError):                   # 回 open：不可直接 approve
        _eq(evs, event="approve", item_id="ITEM-5", actor="bob",
            actor_role="human_final")
    assert queue.verify_chain(evs) == []


def test_queue_current_queue_and_projection_summary():
    evs = queue.empty_ledger()["events"]
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="A", actor="c", actor_role="agent",
        reason_code="critic_auto_route_blocked",
        refs={"fact_ref": _sha("f1")}))
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="B", actor="c", actor_role="agent",
        reason_code="judge_gate_fail"))
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="A", actor="t", actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="enqueue", item_id="C", actor="c", actor_role="agent",
        reason_code="critic_auto_route_blocked"))
    evs, _ = queue.append(evs, _eq(
        evs, event="assign", item_id="C", actor="t", actor_role="agent"))
    evs, _ = queue.append(evs, _eq(
        evs, event="approve", item_id="C", actor="bob",
        actor_role="human_final"))
    assert queue.verify_chain(evs) == []

    cur = queue.current_queue(evs)
    assert [it["item_id"] for it in cur] == ["A", "B"]      # 2 open，C 已闭
    a = cur[0]
    assert a["enqueued_event_seq"] == 0
    assert a["last_event"] == "assign"
    assert a["reason_code"] == "critic_auto_route_blocked"
    assert a["refs"] == {"fact_ref": _sha("f1")}
    assert cur[1]["last_event"] == "enqueue"

    s = queue.projection_summary(evs)
    assert s["queue_length"] == 2
    assert s["by_reason_code"] == {"critic_auto_route_blocked": 1,
                                   "judge_gate_fail": 1}
    assert s["by_last_event"] == {"assign": 1, "enqueue": 1}
    assert s["oldest_item_seq"] == 0
    assert s["total_events"] == 6

    empty = queue.projection_summary(queue.empty_ledger()["events"])
    assert empty == {"queue_length": 0, "by_reason_code": {},
                     "by_last_event": {}, "oldest_item_seq": None,
                     "total_events": 0}
    assert queue.empty_ledger() == {"events": []}


def test_queue_current_queue_rejects_tampered_ledger():
    evs, _ = _chain5()
    tampered = [dict(e) for e in evs]
    tampered[0]["reason_code"] = "forged"
    with pytest.raises(ValueError):
        queue.current_queue(tampered)
    with pytest.raises(ValueError):
        queue.projection_summary(tampered)


def test_queue_make_event_rejects_unknown_refs_and_event():
    evs = queue.empty_ledger()["events"]
    with pytest.raises(ValueError):
        _eq(evs, event="requeue", item_id="X", actor="a",
            actor_role="agent")
    with pytest.raises(ValueError):
        _eq(evs, event="enqueue", item_id="X", actor="a",
            actor_role="agent", refs={"rogue_ref": "v"})


# ---------------------------------------------------------------------------
# 抽样审计（独立质量控制；失败降级全量陪审）
# ---------------------------------------------------------------------------

def test_audit_config_validates():
    cfg = queue.audit_config(sample_rate=0.2, min_samples=5)
    assert cfg == {"sample_rate": 0.2, "min_samples": 5,
                   "fallback": "full_jury"}
    assert queue.audit_config(sample_rate=1, min_samples=1,
                              fallback="full_jury_v2")["fallback"] == \
        "full_jury_v2"
    for bad in ({"sample_rate": 0, "min_samples": 5},
                {"sample_rate": 1.5, "min_samples": 5},
                {"sample_rate": 0.2, "min_samples": 0}):
        with pytest.raises(ValueError):
            queue.audit_config(**bad)


def test_audit_decision_failed_last_audit_falls_back():
    cfg = queue.audit_config(sample_rate=0.2, min_samples=5)
    d = queue.audit_decision(cfg, queue_length=100, failed_last_audit=True)
    assert d["mode"] == "full_jury"
    assert d["reason"] == "audit_failed_full_jury"
    # 降级模式可配置
    cfg2 = queue.audit_config(sample_rate=0.2, min_samples=5,
                              fallback="full_jury_v2")
    d2 = queue.audit_decision(cfg2, queue_length=100,
                              failed_last_audit=True)
    assert d2["mode"] == "full_jury_v2"
    assert d2["reason"] == "audit_failed_full_jury"


def test_audit_decision_below_min_samples():
    cfg = queue.audit_config(sample_rate=0.2, min_samples=5)
    d = queue.audit_decision(cfg, queue_length=3, failed_last_audit=False)
    assert d["mode"] == "full_jury"
    assert d["reason"] == "below_min_samples"


def test_audit_decision_sampled_is_triage_not_pass():
    cfg = queue.audit_config(sample_rate=0.2, min_samples=5)
    d = queue.audit_decision(cfg, queue_length=50, failed_last_audit=False)
    assert d["mode"] == "sampled"
    assert d["sample_rate"] == 0.2
    assert "不是质量放行" in d["note"]        # 抽样是分流不是放行
    with pytest.raises(ValueError):          # 非法配置 fail-closed
        queue.audit_decision({"sample_rate": 0, "min_samples": 5},
                             queue_length=50, failed_last_audit=False)
