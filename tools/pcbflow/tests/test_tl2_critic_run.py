"""S14 会话测试：TL-2 critic run 管线（bundle 构建 + ingest/分诊）。

覆盖（SPEC-v3.0-PROPOSAL §TD4/§TD5；APR-0005 advisory_only）：
- reader_task_card：输出合同形状/禁止事项/untrusted 注记；
- build_input_bundle：byte-exact 确定性（同输入两次构建 canonical 字节
  一致）、allowed_categories 与 critic.FLAG_CATEGORIES 及 schemas 枚举
  对齐、无 wall-clock/主机路径、非法输入 ValueError（未知键/坏 hash/
  缺 observation/单面渲染/重复板/坏 split）；
- ingest_run 正向：executed 赋值、record 过 critic_run_record 合同
  schema、flags=[] 语义由五条件合取判定（无校准域恒 blocked→enqueue）；
  全谓词+校准域成立→queue_deprioritized 无事件；
- ingest_run 负向（fail-closed）：类别越界/置信度越界（含布尔）/
  位置证据或说明为空/reader_id 缺失/读者自封 status/非 JSON/缺板 →
  invalid+原因；渲染或源板 hash 不符/缺实测值 → invalid+
  input_hashes_match=False；sidecar 或 run_id 不符/bundle 结构坏 →
  ValueError；APR-0005 锚未过 → invalid+model.approved=False；
- queue 事件：enqueue 绑 critic_ref=record canonical sha；两 run 同账本
  链完整；篡改暴露由 pcbflow.queue 合同保证。

纯内存构造（生成器模式）：零子进程/零写盘/零网络。
"""

import json

import pytest

from pcbflow import critic, critic_run, hashing, queue, schemas


def _sha(seed: str) -> str:
    return hashing.sha256_text(seed)


PROF_A = "prof-train"
PROF_B = "prof-hold"


def _boards_input():
    return [
        {"profile_id": PROF_A, "split": "train",
         "split_basis": "manifest dataset_splits.train",
         "source_board": {"path_rel": f"datasets/x/{PROF_A}.kicad_pcb",
                          "sha256": _sha("src-a")},
         "profile": {"path_rel": f"profiles/{PROF_A}/profile.json",
                     "sha256": _sha("prof-a")},
         "renders": [
             {"file_rel": f"renders/{PROF_A}-bottom.png", "side": "bottom",
              "sha256": _sha("ra-bottom"), "observation": "底面走线可辨"},
             {"file_rel": f"renders/{PROF_A}-top.png", "side": "top",
              "sha256": _sha("ra-top"), "observation": "顶面丝印可辨"}]},
        {"profile_id": PROF_B, "split": "holdout",
         "split_basis": "manifest dataset_splits.holdout",
         "source_board": {"path_rel": f"datasets/y/{PROF_B}.kicad_pcb",
                          "sha256": _sha("src-b")},
         "profile": {"path_rel": f"profiles/{PROF_B}/profile.json",
                     "sha256": _sha("prof-b")},
         "renders": [
             {"file_rel": f"renders/{PROF_B}-bottom.png", "side": "bottom",
              "sha256": _sha("rb-bottom"), "observation": "底面敷铜可辨"},
             {"file_rel": f"renders/{PROF_B}-top.png", "side": "top",
              "sha256": _sha("rb-top"), "observation": "顶面位号可辨"}]},
    ]


def _bundle(**over) -> dict:
    kw = dict(run_id="run-t", selection_rule="1 train + 1 holdout 规则",
              boards=_boards_input(), approval_sha256=_sha("apr-0005"),
              calibration_domain_established=False)
    kw.update(over)
    return critic_run.build_input_bundle(**kw)


def _actual_hashes(bundle: dict) -> dict:
    m = {}
    for b in bundle["boards"]:
        pid = b["profile_id"]
        m[f"source_board:{pid}"] = b["source_board"]["sha256"]
        m[f"profile:{pid}"] = b["profile"]["sha256"]
        for r in b["renders"]:
            m[f"render:{r['file_rel']}"] = r["sha256"]
    return m


def _flag(**over) -> dict:
    f = {"category": "silk_readability", "confidence": 0.8,
         "location_evidence": "U3 pad2 附近", "description": "丝印叠压焊盘",
         "abstain": False}
    f.update(over)
    return f


def _raw(**over) -> str:
    doc = {"reader_id": "reader-1",
           "per_board": [{"profile_id": PROF_A, "flags": [_flag()]},
                         {"profile_id": PROF_B, "flags": []}],
           "reading_notes": f"{PROF_B} 无旗：底/顶未见异常"}
    doc.update(over)
    return json.dumps(doc, ensure_ascii=False)


def _ingest(bundle=None, raw=None, **over) -> dict:
    b = bundle if bundle is not None else _bundle()
    kw = dict(run_id=b["run_id"], bundle=b,
              raw_flags_text=raw if raw is not None else _raw(),
              expected_bundle_sha256=critic_run.bundle_sha256(b),
              actual_hashes=_actual_hashes(b), approval_ok=True)
    kw.update(over)
    return critic_run.ingest_run(**kw)


# ---------------------------------------------------------------------------
# reader_task_card 与 bundle 构建
# ---------------------------------------------------------------------------

def test_reader_task_card_contract():
    card = critic_run.reader_task_card(
        renders_by_profile={PROF_A: ["renders/a-top.png"]})
    shape = card["output_contract"]["shape"]
    assert sorted(shape) == sorted(critic_run.RAW_TOPLEVEL_KEYS)
    flag_shape = shape["per_board"][0]["flags"][0]
    assert sorted(flag_shape) == sorted(critic_run.RAW_FLAG_KEYS)
    assert "untrusted" in card["untrusted_note"]
    assert "abstain=true" in card["output_contract"]["requirements"] \
        and "只输出观察" in card["output_contract"]["requirements"]
    assert card["inputs"]["renders"] == {PROF_A: ["renders/a-top.png"]}
    assert card["inputs"]["bundle_fields"] == (
        "allowed_categories", "confidence_scale", "prohibitions", "boards")


def test_bundle_byte_exact_and_categories_alignment():
    b1, b2 = _bundle(), _bundle()
    a1 = hashing.canonical_json_bytes(b1)
    assert a1 == hashing.canonical_json_bytes(b2)          # byte-exact
    assert critic_run.bundle_sha256(b1) == hashing.sha256_bytes(a1)
    text = a1.decode("utf-8")
    for banned in ("timestamp", "generated_at", "wall_clock", "C:\\",
                   "F:\\", str(__import__("pathlib").Path.cwd())):
        assert banned not in text, banned
    assert b1["allowed_categories"] == list(critic.FLAG_CATEGORIES)
    enum = schemas.SCHEMAS["critic_run_record"]["properties"]["flags"][
        "items"]["properties"]["category"]["enum"]
    assert b1["allowed_categories"] == enum                # 与注册表对齐
    assert b1["approval"]["duty_level"] == "advisory_only"
    assert b1["calibration"]["domain_established"] is False
    # boards 顺序规范化（按 profile_id 排序，构造序无关）
    assert [b["profile_id"] for b in b1["boards"]] == sorted(
        [PROF_A, PROF_B])


def test_bundle_rejects_invalid_inputs():
    with pytest.raises(ValueError):        # 坏 sha 格式
        _bundle(approval_sha256="nothex")
    with pytest.raises(ValueError):        # run_id 空
        _bundle(run_id="")
    boards = _boards_input()
    boards[0]["rogue_key"] = 1             # 未知键 fail-closed
    with pytest.raises(ValueError):
        _bundle(boards=boards)
    boards = _boards_input()
    boards[1]["renders"] = boards[1]["renders"][:1]        # 缺底/顶
    with pytest.raises(ValueError):
        _bundle(boards=boards)
    boards = _boards_input()
    boards[0]["renders"][0]["observation"] = ""            # 空观感
    with pytest.raises(ValueError):
        _bundle(boards=boards)
    boards = _boards_input()
    boards[1]["profile"]["sha256"] = "zz"                  # 坏 hash
    with pytest.raises(ValueError):
        _bundle(boards=boards)
    boards = _boards_input()
    boards[1]["split"] = "train"           # 重复 profile_id（同 A/B 集）
    boards[1]["profile_id"] = PROF_A
    with pytest.raises(ValueError):
        _bundle(boards=boards)
    boards = _boards_input()
    boards[0]["split"] = "unknown"         # 坏 split
    with pytest.raises(ValueError):
        _bundle(boards=boards)


def test_validate_bundle_malformed_rejected():
    for mutate in (
        lambda b: b.__setitem__("kind", "other"),
        lambda b: b.__setitem__("allowed_categories", ["drc_error"]),
        lambda b: b.__setitem__("calibration", {}),
        lambda b: b.__setitem__("approval", {"disposition_id": "APR-0006"}),
        lambda b: b.__setitem__("boards", []),
        lambda b: b.pop("reader_task_card"),
    ):
        b = _bundle()
        mutate(b)
        with pytest.raises(ValueError):
            critic_run.validate_bundle(b)


# ---------------------------------------------------------------------------
# ingest 正向：executed 赋值与 TD5 路由
# ---------------------------------------------------------------------------

def test_ingest_executed_blocked_uncalibrated_enqueue():
    b = _bundle()
    out = _ingest(bundle=b)
    rec = out["record"]
    assert rec["critic_status"] == "executed"      # 管线赋值
    assert rec["advisory_only"] is True
    assert rec["model"] == {"provider": "subagent_critic_reader",
                            "version": "reader-1", "approved": True}
    assert rec["input_hashes_match"] is True
    assert rec["calibration"] == {"in_calibrated_range": False}
    assert [f["category"] for f in rec["flags"]] == ["silk_readability"]
    assert sorted(rec["flags"][0]) == ["category", "confidence", "location"]
    assert rec["flags"][0]["location"] == "U3 pad2 附近"
    raw_sha = hashing.sha256_text(_raw())
    assert out["raw_flags_sha256"] == raw_sha
    assert raw_sha in rec["evidence_refs"]         # 原文保全进 evidence
    assert out["abstain_count"] == 0
    # 合同 schema 对齐
    assert schemas.validate("critic_run_record", rec) == []
    assert critic.validate_run(rec) == []
    assert out["record_sha256"] == hashing.sha256_bytes(
        hashing.canonical_json_bytes(rec))
    # 无校准域 → flags=[] 语义不成立 → blocked → 人工 enqueue
    assert out["invalid_reasons"] == []
    assert out["triage"]["eligible"] is False
    assert out["triage"]["status"] == "critic_auto_route_blocked"
    assert out["record"]["critic_outcome"] == "blocked"
    assert out["queue_events"] and out["queue_events"][0]["event"] == "enqueue"
    ev = out["queue_events"][0]
    assert ev["item_id"] == "ITEM-run-t"
    assert ev["reason_code"] == "critic_auto_route_blocked"
    assert ev["critic_ref"] == out["record_sha256"]
    assert queue.verify_chain(out["ledger_events"]) == []
    # input_hashes 绑定 bundle 声明 + 原文 + 批准锚
    ih = rec["input_hashes"]
    assert ih["raw_flags"] == raw_sha
    assert ih["approval:APR-0005"] == _sha("apr-0005")
    assert ih[f"render:renders/{PROF_A}-top.png"] == _sha("ra-top")
    assert ih[f"source_board:{PROF_B}"] == _sha("src-b")
    assert all(len(v) == 64 for v in ih.values())


def test_ingest_flags_empty_uncalibrated_is_blocked_not_clean():
    """flags=[] + 无校准域：五条件不合取 → 不是「无旗」，blocked 入队。"""
    out = _ingest(raw=_raw(per_board=[
        {"profile_id": PROF_A, "flags": []},
        {"profile_id": PROF_B, "flags": []}]),
        judge_gate_pass=True, required_checkers_executed=True,
        no_stale_or_unknown=True)
    rec = out["record"]
    assert rec["critic_status"] == "executed"
    assert rec["flags"] == []
    d = out["triage"]
    assert d["eligible"] is False
    assert d["failed_conditions"] == ["critic_calibration_in_range"]
    s = critic.flags_empty_semantics(rec)
    assert s["means_no_flags"] is False
    assert "calibration" in s["reason"] or "校准" in s["reason"] \
        or "in_calibrated_range" in s["reason"]
    assert out["queue_events"]                     # 入人工队列


def test_ingest_eligible_when_calibrated_and_all_predicates_pass():
    """校准域成立 + flags=[] + 全谓词过 → queue_deprioritized（无事件）。"""
    b = _bundle(calibration_domain_established=True)
    out = _ingest(bundle=b, raw=_raw(per_board=[
        {"profile_id": PROF_A, "flags": []},
        {"profile_id": PROF_B, "flags": []}]),
        judge_gate_pass=True, required_checkers_executed=True,
        no_stale_or_unknown=True)
    rec = out["record"]
    assert out["triage"] == {"eligible": True,
                             "status": "queue_deprioritized",
                             "failed_conditions": []}
    assert rec["auto_route"] == out["triage"]
    assert rec["critic_outcome"] == "advisory"
    assert out["queue_events"] == []
    assert out["ledger_events"] == []
    assert critic.flags_empty_semantics(rec)["means_no_flags"] is True


def test_ingest_flags_nonempty_routes_manual_even_when_calibrated():
    b = _bundle(calibration_domain_established=True)
    out = _ingest(bundle=b, judge_gate_pass=True,
                  required_checkers_executed=True, no_stale_or_unknown=True)
    assert out["triage"]["eligible"] is False
    assert out["triage"]["failed_conditions"] == ["critic_flags_empty"]
    assert out["queue_events"]


def test_ingest_abstain_flags_mapped_and_counted():
    out = _ingest(raw=_raw(per_board=[
        {"profile_id": PROF_A,
         "flags": [_flag(abstain=True, confidence=0.4,
                         description="不确定是否叠压")]},
        {"profile_id": PROF_B, "flags": []}]))
    rec = out["record"]
    assert out["abstain_count"] == 1
    assert len(rec["flags"]) == 1                  # abstain 旗不丢（保全）
    assert rec["flags"][0]["confidence"] == 0.4
    assert rec["critic_status"] == "executed"


# ---------------------------------------------------------------------------
# ingest 负向：untrusted 读取者输出 fail-closed
# ---------------------------------------------------------------------------

def _assert_invalid(out, *needles):
    rec = out["record"]
    assert rec["critic_status"] == "invalid"
    assert rec["critic_outcome"] == "blocked"
    assert schemas.validate("critic_run_record", rec) == []
    assert critic.validate_run(rec) == []
    for needle in needles:
        assert any(needle in r for r in out["invalid_reasons"]), \
            (needle, out["invalid_reasons"])
    assert out["queue_events"]                     # invalid → 人工队列


def test_ingest_invalid_category_out_of_enum():
    raw = _raw(per_board=[{"profile_id": PROF_A,
                           "flags": [_flag(category="drc_error")]},
                          {"profile_id": PROF_B, "flags": []}])
    _assert_invalid(_ingest(raw=raw), "category", "drc_error")


def test_ingest_invalid_confidence_out_of_range():
    for bad in (1.5, -0.1, True):
        raw = _raw(per_board=[{"profile_id": PROF_A,
                               "flags": [_flag(confidence=bad)]},
                              {"profile_id": PROF_B, "flags": []}])
        _assert_invalid(_ingest(raw=raw), "confidence")


def test_ingest_invalid_empty_location_or_description():
    raw = _raw(per_board=[{"profile_id": PROF_A,
                           "flags": [_flag(location_evidence="")]},
                          {"profile_id": PROF_B, "flags": []}])
    _assert_invalid(_ingest(raw=raw), "location_evidence")
    raw = _raw(per_board=[{"profile_id": PROF_A,
                           "flags": [_flag(description="  ")]},
                          {"profile_id": PROF_B, "flags": []}])
    _assert_invalid(_ingest(raw=raw), "description")


def test_ingest_missing_reader_id_is_invalid():
    raw = _raw()
    doc = json.loads(raw)
    del doc["reader_id"]
    out = _ingest(raw=json.dumps(doc, ensure_ascii=False))
    _assert_invalid(out, "reader_id")
    assert out["record"]["model"]["version"] is None


def test_ingest_reader_self_claimed_status_rejected():
    """读者自封 critic_status=executed：未知顶层键 → invalid（不采信）。"""
    raw = _raw(critic_status="executed", valid=True)
    out = _ingest(raw=raw)
    _assert_invalid(out, "未知顶层键")
    assert out["record"]["critic_status"] == "invalid"


def test_ingest_raw_not_json_is_invalid():
    _assert_invalid(_ingest(raw="{not json"), "不是合法 JSON")


def test_ingest_missing_or_duplicate_board_is_invalid():
    raw = _raw(per_board=[{"profile_id": PROF_A, "flags": []}])
    _assert_invalid(_ingest(raw=raw), "缺少 bundle 板")
    raw = _raw(per_board=[{"profile_id": PROF_A, "flags": []},
                          {"profile_id": PROF_A, "flags": []},
                          {"profile_id": PROF_B, "flags": []}])
    _assert_invalid(_ingest(raw=raw), "重复")


def test_ingest_hash_mismatch_is_invalid():
    """渲染/源板 hash 对盘上实测不符 → invalid + input_hashes_match=False。"""
    actual = _actual_hashes(_bundle())
    actual[f"render:renders/{PROF_A}-top.png"] = _sha("drifted")
    out = _ingest(actual_hashes=actual)
    _assert_invalid(out, f"render:renders/{PROF_A}-top.png")
    rec = out["record"]
    assert rec["input_hashes_match"] is False
    assert rec["critic_status"] == "invalid"
    # 旗标仍映射保全（raw 本身合法），由人工队列裁决
    assert [f["category"] for f in rec["flags"]] == ["silk_readability"]


def test_ingest_missing_actual_hash_is_invalid():
    actual = _actual_hashes(_bundle())
    del actual[f"source_board:{PROF_B}"]
    _assert_invalid(_ingest(actual_hashes=actual), "缺少盘上实测值")
    _assert_invalid(_ingest(actual_hashes={}), "缺少盘上实测值")


def test_ingest_raw_flags_disk_hash_mismatch_is_invalid():
    actual = _actual_hashes(_bundle())
    actual["raw_flags"] = _sha("other-bytes")
    _assert_invalid(_ingest(actual_hashes=actual), "raw_flags")


def test_ingest_sidecar_or_runid_mismatch_is_valueerror():
    b = _bundle()
    with pytest.raises(ValueError):                # sidecar 对不上
        _ingest(bundle=b, expected_bundle_sha256=_sha("tampered"))
    with pytest.raises(ValueError):                # run_id 不符
        _ingest(bundle=b, run_id="run-other")
    with pytest.raises(ValueError):                # bundle 结构坏
        bad = _bundle()
        bad["kind"] = "rogue"
        _ingest(bundle=bad)


def test_ingest_approval_anchor_fail_closed():
    out = _ingest(approval_ok=False)
    _assert_invalid(out, "APR-0005")
    rec = out["record"]
    assert rec["model"]["approved"] is False
    assert rec["critic_status"] == "invalid"


# ---------------------------------------------------------------------------
# queue 事件链（与 pcbflow.queue 合同对齐）
# ---------------------------------------------------------------------------

def test_two_runs_single_ledger_chain():
    r1 = _ingest()
    r2 = _ingest(bundle=_bundle(run_id="run-u"),
                 run_id="run-u",
                 raw=_raw(),
                 ledger_events=r1["ledger_events"])
    assert r1["queue_events"][0]["event_seq"] == 0
    ledger = r2["ledger_events"]
    assert len(ledger) == 2
    assert ledger[1]["event_seq"] == 1
    assert ledger[1]["prev_event_sha256"] == ledger[0]["event_sha256"]
    assert ledger[1]["item_id"] == "ITEM-run-u"
    assert queue.verify_chain(ledger) == []
    summary = queue.projection_summary(ledger)
    assert summary["queue_length"] == 2
    assert summary["by_reason_code"] == {"critic_auto_route_blocked": 2}


def test_ledger_tamper_after_ingest_detected():
    out = _ingest()
    tampered = [dict(e) for e in out["ledger_events"]]
    tampered[0]["reason_code"] = "forged"
    with pytest.raises(ValueError):
        queue.current_queue(tampered)


# ---------------------------------------------------------------------------
# provenance 披露绑定与 raw 位置容差红线（S14 第二段）
# ---------------------------------------------------------------------------

def test_ingest_provenance_hashes_bound():
    """raw 结构性修复披露：provenance 绑定进 input_hashes/evidence_refs。"""
    prov = {"raw_flags_as_returned": _sha("orig"),
            "raw_flags_repair_disclosure": _sha("disc")}
    out = _ingest(provenance_hashes=prov)
    rec = out["record"]
    assert rec["input_hashes"]["provenance:raw_flags_as_returned"] == \
        _sha("orig")
    assert rec["input_hashes"]["provenance:raw_flags_repair_disclosure"] == \
        _sha("disc")
    assert rec["evidence_refs"] == [out["raw_flags_sha256"], _sha("orig"),
                                    _sha("disc")]
    assert schemas.validate("critic_run_record", rec) == []
    assert critic.validate_run(rec) == []


def test_ingest_provenance_invalid_inputs_rejected():
    with pytest.raises(ValueError):        # 非 64-hex 值
        _ingest(provenance_hashes={"bad": "zz"})
    with pytest.raises(ValueError):        # 名字含命名空间分隔符
        _ingest(provenance_hashes={"render:x": _sha("y")})


def test_raw_nested_reading_notes_rejected_fail_closed():
    """读取者把 reading_notes 写进板对象：fail-closed 拒绝（不做位置容错）。"""
    raw = json.dumps({
        "reader_id": "reader-1",
        "per_board": [{"profile_id": PROF_A, "flags": [],
                       "reading_notes": "nested"}],
        "reading_notes": "top"}, ensure_ascii=False)
    _assert_invalid(_ingest(raw=raw), "未知键", "reading_notes")
