"""P2-7 逐旗标人工裁定接入测试（V3-RECOMMENDATIONS §4.2 优先级 2）。

覆盖：
- schemas.py 追加式注册 critic-flag-verdict-v1：REGISTRY_VERSION=3.0 不动、
  既有条目哈希零变化（r4 账本钉值）、新条目 hash 稳定且与全表互异；
- verdict 枚举封闭集正负向（fail-closed 四值集）、required/多余键、
  provenance hash 与 declared_date 形状合同；
- pcbflow.critic.flag_verdict_agreement：聚合正例（confirmed 3/4=0.75）、
  P2-5 三分计数（unadjudicated/uncertain/无裁定不进分母任何一侧）、
  fail-closed（未知 flag_id/run 错配/缺 hash/hash 不符/重复裁定→ValueError
  拒算）、空裁定列表与全不可判定 → not_available（None+说明，不编造数值）；
- pcbflow.critic.project_judgment_agreement_with_verdicts（投影位接入，
  health_projection.py 本体零改动——其模块 hash 被冻结投影 v3 织入）：
  无裁定=同参委托 hp 本体（canonical byte 等价的零变化通道）、
  有有效裁定=实值接入（3/4=0.75）、投影层 fail-closed（schema 非法/
  run 错配/hash 对账失败/缺证据指针/重复裁定 → blocked）、canonical
  确定性。

纯内存构造（生成器模式）：零子进程/零网络/零墙钟/零 out/ 写入。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import critic, hashing, schemas  # noqa: E402
from pcbflow import health_projection as hp  # noqa: E402

_VERDICT_SCHEMA = "critic-flag-verdict-v1"
_DATE = "2026-09-10"   # 人工声明常量（生成器纪律：非 wall-clock）

# r4 账本 schema_validation 钉值（既有条目哈希零变化的先验锚；与
# tests/test_p2b_adopt_registration.py 同源）
_R4_DISPOSITION_SCHEMA_SHA = (
    "09dd31fdeabb6656a0236dfd44e81bcd3013c9ded9463a7f93a66c0315fca71d")


def _sha(seed: str) -> str:
    return hashing.sha256_text(seed)


def _run(n_flags=4, run_id="CR-run-v1"):
    """构造合法 critic run（executed 语义前置显式给出）并加 n_flags 面旗。"""
    run = critic.build_run(
        critic_run_id=run_id, candidate_id="cand-1",
        critic_status="executed",
        model={"provider": "offline-critic", "version": "v0",
               "approved": True},
        input_hashes={"sheet": _sha("sheet")},
        input_hashes_match=True,
        calibration={"in_calibrated_range": False},
        critic_outcome="advisory")
    categories = ("silk_readability", "courtyard_crowding",
                  "suspicious_reroute", "other_advisory")
    for i in range(n_flags):
        critic.add_flag(run, categories[i % len(categories)],
                        0.5 + 0.01 * i, location=f"loc-{i}")
    return run


def _verdicts(run, spec, **over):
    """spec=[(flag_index, verdict)] → 裁定记录列表（hash 绑定实测注入）。"""
    ids = critic.run_flag_ids(run)
    out = []
    for i, v in spec:
        rec = {
            "schema_version": "3.0",
            "verdict_record_id": f"VR-{run['critic_run_id']}-{i}",
            "critic_run_id": run["critic_run_id"],
            "flag_id": ids[i],
            "verdict": v,
            "adjudicator": "human-adjudicator",
            "declared_date": _DATE,
            "critic_run_record_sha256":
                critic.critic_run_record_sha256(run),
        }
        rec.update(over)
        out.append(rec)
    return out


def _valid_verdict_record(run, index=0, verdict="confirmed"):
    return _verdicts(run, [(index, verdict)])[0]


# ---------------------------------------------------------------------------
# ① schema 追加式注册（REGISTRY_VERSION 不动 + 既有条目零改动）
# ---------------------------------------------------------------------------

def test_schema_additive_registration_and_registry_version_frozen():
    assert _VERDICT_SCHEMA in schemas.SCHEMAS
    assert schemas.REGISTRY_VERSION == "3.0"          # 升版被禁止
    assert len(schemas.SCHEMAS) == 22                 # 16+1+1（追加式：+observation-row-v1 @2026-09-12）+REPAIR-P3 W-5 四孤儿名 @2026-09-22（快照同步随追加演进；哈希断言不受影响）
    # 既有 15 schema + artifact-role-declaration-v1 全部仍在
    for name in ("gate_record", "disposition_record", "judge_pre_record",
                 "judge_post_record", "decision_ledger_entry",
                 "critic_run_record", "queue_event", "physics_report",
                 "physics_coverage", "bring_up_report",
                 "external_execution_record", "proposal_patch",
                 "search_space", "project_manifest", "profile",
                 "artifact-role-declaration-v1"):
        assert name in schemas.SCHEMAS, name
    # 既有条目哈希零变化（r4 账本钉值先验锚；追加不改既有条目）
    assert schemas.schema_hash("disposition_record") == \
        _R4_DISPOSITION_SCHEMA_SHA
    # 新条目：重算稳定、64 hex、与全表互异
    h1 = schemas.schema_hash(_VERDICT_SCHEMA)
    h2 = schemas.schema_hash(_VERDICT_SCHEMA)
    assert h1 == h2 and len(h1) == 64
    hs = {name: schemas.schema_hash(n) for n in schemas.SCHEMAS}
    assert len(set(hs.values())) == len(hs)


# ---------------------------------------------------------------------------
# ② verdict 枚举封闭集（正负向）
# ---------------------------------------------------------------------------

def test_schema_verdict_enum_closed_set():
    run = _run()
    for v in critic.VERDICT_VALUES:                    # 四值全合法
        rec = _valid_verdict_record(run, verdict=v)
        assert schemas.validate(_VERDICT_SCHEMA, rec) == [], v
    assert critic.VERDICT_VALUES == ("confirmed", "false_positive",
                                     "unadjudicated", "uncertain")
    for bad in ("supported", "true_positive", "false_negtive", "",
                "confirmed ", None, 1, True):          # 封闭集外 fail-closed
        rec = _valid_verdict_record(run)
        rec["verdict"] = bad
        errs = schemas.validate(_VERDICT_SCHEMA, rec)
        assert errs and "enum" in errs[0], bad


# ---------------------------------------------------------------------------
# ③ required 六字段 + additionalProperties=false
# ---------------------------------------------------------------------------

def test_schema_required_fields_and_closed_shape():
    run = _run()
    base = _valid_verdict_record(run)
    assert schemas.validate(_VERDICT_SCHEMA, base) == []
    for key in ("verdict_record_id", "critic_run_id", "flag_id", "verdict",
                "adjudicator", "declared_date"):
        rec = dict(base)
        rec.pop(key)
        errs = schemas.validate(_VERDICT_SCHEMA, rec)
        assert errs and key in errs[0], key
    rec = dict(base)
    rec["unexpected"] = 1
    errs = schemas.validate(_VERDICT_SCHEMA, rec)
    assert errs and "多余键" in errs[0]


# ---------------------------------------------------------------------------
# ④ provenance hash 绑定字段与 declared_date 形状合同
# ---------------------------------------------------------------------------

def test_schema_provenance_hash_and_date_shapes():
    run = _run()
    # hash 绑定字段：64-hex 合法；缺省合法（schema 层可选）；坏 hash 拒
    rec = _valid_verdict_record(run)
    assert schemas.validate(_VERDICT_SCHEMA, rec) == []
    rec2 = dict(rec)
    rec2.pop("critic_run_record_sha256")
    assert schemas.validate(_VERDICT_SCHEMA, rec2) == []
    rec3 = dict(rec)
    rec3["critic_run_record_sha256"] = "zz"
    assert schemas.validate(_VERDICT_SCHEMA, rec3), "坏 hash 必须拒"
    # declared_date：YYYY-MM-DD 形状合同
    rec4 = dict(rec)
    rec4["declared_date"] = "2026-9-10"
    assert schemas.validate(_VERDICT_SCHEMA, rec4), "日期形状必须拒"
    # evidence_ref 可空可 64-hex；note 可携带（≤512）
    rec5 = dict(rec, evidence_ref=None, note="人工判读记录（难例）")
    assert schemas.validate(_VERDICT_SCHEMA, rec5) == []
    rec6 = dict(rec, evidence_ref=_sha("ev"))
    assert schemas.validate(_VERDICT_SCHEMA, rec6) == []


# ---------------------------------------------------------------------------
# ⑤ flag_id 确定性派生
# ---------------------------------------------------------------------------

def test_flag_id_derivation_deterministic_and_index_distinct():
    run = _run(n_flags=4)
    ids = critic.run_flag_ids(run)
    assert len(ids) == 4 and all(len(i) == 64 for i in ids)
    assert ids == critic.run_flag_ids(run)             # 重算稳定
    assert ids[0] == critic.flag_id("CR-run-v1", 0, run["flags"][0])
    # 索引参与派生：同 run 内内容完全相同的重复旗标 id 互异（P2-4 单列）
    twin_run = critic.build_run(
        critic_run_id="CR-twin", candidate_id="c", critic_status="executed",
        model={"provider": "p", "version": "v", "approved": True},
        input_hashes={"sheet": _sha("s")}, input_hashes_match=True,
        calibration={"in_calibrated_range": False})
    twin_flag = {"category": "other_advisory", "confidence": 0.5}
    twin_run["flags"] += [dict(twin_flag), dict(twin_flag)]
    twin_ids = critic.run_flag_ids(twin_run)
    assert twin_ids[0] != twin_ids[1]
    # run 非 dict / 缺 critic_run_id → fail-closed
    with pytest.raises(ValueError, match="dict"):
        critic.run_flag_ids(None)
    with pytest.raises(ValueError, match="critic_run_id"):
        critic.run_flag_ids({"flags": []})


# ---------------------------------------------------------------------------
# ⑥ 聚合正例：confirmed 3/4=0.75
# ---------------------------------------------------------------------------

def test_agreement_positive_three_of_four():
    run = _run(n_flags=4)
    verdicts = _verdicts(run, [(0, "confirmed"), (1, "confirmed"),
                               (2, "confirmed"), (3, "false_positive")])
    out = critic.flag_verdict_agreement(run, verdicts)
    assert out["status"] == "value"
    assert out["agreement_rate"] == 0.75
    assert (out["numerator"], out["denominator"]) == (3, 4)
    assert out["counts"] == {"confirmed": 3, "false_positive": 1,
                             "unadjudicated_or_pending": 0}
    assert out["verdict_breakdown"]["no_verdict_record"] == 0
    assert out["flags_total"] == 4 and out["verdicts_total"] == 4
    assert out["run_id"] == "CR-run-v1"
    assert "P2-5" in out["denominator_basis"]


# ---------------------------------------------------------------------------
# ⑦ P2-5 三分计数：不可判定不进分母任何一侧
# ---------------------------------------------------------------------------

def test_three_way_counts_undecidable_excluded():
    run = _run(n_flags=6)
    verdicts = _verdicts(run, [(0, "confirmed"), (1, "confirmed"),
                               (2, "false_positive"), (3, "unadjudicated"),
                               (4, "uncertain")])       # 旗 5 无裁定=pending
    out = critic.flag_verdict_agreement(run, verdicts)
    assert out["status"] == "value"
    assert out["agreement_rate"] == 2 / 3
    assert (out["numerator"], out["denominator"]) == (2, 3)
    assert out["counts"] == {"confirmed": 2, "false_positive": 1,
                             "unadjudicated_or_pending": 3}
    assert out["pending_flag_count"] == 1
    assert out["verdict_breakdown"] == {
        "confirmed": 2, "false_positive": 1, "no_verdict_record": 1,
        "unadjudicated": 1, "uncertain": 1}


# ---------------------------------------------------------------------------
# ⑧ fail-closed：未知 flag_id / 重复裁定
# ---------------------------------------------------------------------------

def test_agreement_fail_closed_unknown_flag_and_duplicate():
    run = _run(n_flags=4)
    stranger = _valid_verdict_record(run, index=0)
    stranger["flag_id"] = _sha("stranger-flag")
    with pytest.raises(ValueError, match="未知 flag_id"):
        critic.flag_verdict_agreement(run, [stranger])
    dup = _verdicts(run, [(0, "confirmed"), (0, "false_positive")])
    dup[1]["verdict_record_id"] = "VR-dup-second"
    with pytest.raises(ValueError, match="重复裁定"):
        critic.flag_verdict_agreement(run, dup)
    # verdicts 非列表 → fail-closed
    with pytest.raises(ValueError, match="列表"):
        critic.flag_verdict_agreement(run, {"verdict": "confirmed"})


# ---------------------------------------------------------------------------
# ⑨ fail-closed：run 错配 / 缺 hash / hash 不符
# ---------------------------------------------------------------------------

def test_agreement_fail_closed_run_and_hash_binding():
    run = _run(n_flags=4)
    mismatched = _valid_verdict_record(run)
    mismatched["critic_run_id"] = "CR-other"
    with pytest.raises(ValueError, match="run 错配"):
        critic.flag_verdict_agreement(run, [mismatched])
    no_hash = _valid_verdict_record(run)
    no_hash.pop("critic_run_record_sha256")
    with pytest.raises(ValueError, match="provenance"):
        critic.flag_verdict_agreement(run, [no_hash])
    bad_hash = _valid_verdict_record(run)
    bad_hash["critic_run_record_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="不符"):
        critic.flag_verdict_agreement(run, [bad_hash])
    # 裁定记录 schema 非法（缺 declared_date）→ 拒算
    invalid = _valid_verdict_record(run)
    invalid.pop("declared_date")
    with pytest.raises(ValueError, match="schema 非法"):
        critic.flag_verdict_agreement(run, [invalid])


# ---------------------------------------------------------------------------
# ⑩ 空裁定列表 → not_available（不编造数值）
# ---------------------------------------------------------------------------

def test_empty_verdicts_not_available_semantics():
    run = _run(n_flags=4)
    for empty in ([], None):
        out = critic.flag_verdict_agreement(run, empty)
        assert out["status"] == "not_available"
        assert out["agreement_rate"] is None
        assert out["numerator"] is None and out["denominator"] == 0
        assert "不编造数值" in out["reason"]
        assert "pending" in out["reason"]
        assert out["counts"] == {"confirmed": 0, "false_positive": 0,
                                 "unadjudicated_or_pending": 4}
        assert out["flags_total"] == 4 and out["verdicts_total"] == 0
    # run 非 dict → fail-closed
    with pytest.raises(ValueError, match="dict"):
        critic.flag_verdict_agreement("not-a-dict", [])


# ---------------------------------------------------------------------------
# ⑪ 全不可判定 → not_available（不得产出 0.0/1.0 冒充）
# ---------------------------------------------------------------------------

def test_all_undecidable_not_available_no_fabrication():
    run = _run(n_flags=4)
    verdicts = _verdicts(run, [(0, "unadjudicated"), (1, "uncertain"),
                               (2, "unadjudicated")])
    out = critic.flag_verdict_agreement(run, verdicts)
    assert out["status"] == "not_available"
    assert out["agreement_rate"] is None and out["numerator"] is None
    assert out["denominator"] == 0
    assert "可判定" in out["reason"] and "不编造数值" in out["reason"]
    assert out["counts"]["unadjudicated_or_pending"] == 4


# ---------------------------------------------------------------------------
# ⑫ 投影：无裁定 → not_available 路径输出零变化（接入的零变化通道）
# ---------------------------------------------------------------------------

def _projection_fixture(hashes_match=(True, True)):
    runs = [
        {"run_id": "CR-run-v1", "critic_status": "executed",
         "input_hashes_match": hashes_match[0], "flags_total": 4,
         "abstain_count": 0, "in_calibrated_range": False,
         "board_flag_counts": {"bm11": 3, "launchxl": 1}},
        {"run_id": "CR-run-v2", "critic_status": "executed",
         "input_hashes_match": hashes_match[1], "flags_total": 2,
         "abstain_count": 1, "in_calibrated_range": False,
         "board_flag_counts": {"bm11": 2}},
    ]
    evidence = [
        {"run_id": "CR-run-v1", "path": "out/x/rec-v1.json",
         "sha256": _sha("rec-v1")},
        {"run_id": "APR-X1", "path": "out/x/apr-x1.json",
         "sha256": _sha("apr-x1")},
        {"run_id": "CR-run-v2", "path": "out/x/rec-v2.json",
         "sha256": _sha("rec-v2")},
    ]
    calibration = [{"source_id": "cal1", "path": "out/x/cal1.json",
                    "sha256": _sha("cal1"), "sha256_8": _sha("cal1")[:8],
                    "gt_recall": 0.25,
                    "advisory_note": "校准域种子实测（非门）"}]
    return runs, evidence, calibration


def test_projection_no_verdicts_not_available_unchanged():
    runs, evidence, cal = _projection_fixture()
    m1 = hp.project_critic_judgment_agreement(
        runs, [], record_evidence=evidence, calibration_observation=cal)
    # 接入入口（无裁定）vs hp 本体同参调用：canonical byte 等价（零变化）
    w1 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=None)
    w2 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=[])
    assert hashing.canonical_json_bytes(w1) == \
        hashing.canonical_json_bytes(m1)
    assert hashing.canonical_json_bytes(w2) == \
        hashing.canonical_json_bytes(m1)
    # 既有 not_available 语义逐项保持
    assert m1["metric_id"] == "critic_judgment_agreement_rate"
    assert m1["status"] == "not_available"
    assert m1["denominator"] == 0
    assert m1["value"] is None and m1["numerator"] is None
    assert "逐旗标" in m1["reason"] and "不得由修正程序代创标签" in m1["reason"]
    assert m1["revision"] == hp.PROJECTION_REVISION_V3
    assert m1["aux"]["metric_kind"] == "quality"
    assert m1["aux"]["flags_total"] == 6
    assert "verdict_intake" not in m1["aux"]
    for k in hp.DESCRIPTOR_KEYS:
        assert k in m1
    # 既有 blocked 路径同样保持（hash mismatch → trust_invalid）
    runs_bad, evidence_b, cal_b = _projection_fixture(
        hashes_match=(True, False))
    m3 = hp.project_critic_judgment_agreement(
        runs_bad, [], record_evidence=evidence_b,
        calibration_observation=cal_b)
    assert m3["status"] == "blocked" and "trust_invalid" in m3["reason"]


# ---------------------------------------------------------------------------
# ⑬ 投影：有有效裁定 → 实值接入；无效裁定 → blocked（fail-closed）
# ---------------------------------------------------------------------------

def _projection_verdicts():
    def rec(rid, vid, flag_seed, verdict):
        return {"schema_version": "3.0", "verdict_record_id": vid,
                "critic_run_id": rid, "flag_id": _sha(flag_seed),
                "verdict": verdict, "adjudicator": "human-adjudicator",
                "declared_date": _DATE,
                "critic_run_record_sha256": _sha("rec-v1" if rid ==
                                                 "CR-run-v1" else "rec-v2")}
    return [rec("CR-run-v1", "VR-1", "f1", "confirmed"),
            rec("CR-run-v1", "VR-2", "f2", "confirmed"),
            rec("CR-run-v1", "VR-3", "f3", "confirmed"),
            rec("CR-run-v1", "VR-4", "f4", "false_positive"),
            rec("CR-run-v2", "VR-5", "g1", "unadjudicated")]


def test_projection_with_verdicts_value_and_blocked_paths():
    runs, evidence, cal = _projection_fixture()
    m = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=_projection_verdicts())
    assert m["status"] == "value"
    assert (m["numerator"], m["denominator"]) == (3, 4)
    assert m["value"] == 0.75
    assert m["revision"] == hp.PROJECTION_REVISION_V3
    intake = m["aux"]["verdict_intake"]
    assert intake["verdict_records_total"] == 5
    assert intake["counts_p2_5"] == {"confirmed": 3, "false_positive": 1,
                                     "unadjudicated_or_pending": 1}
    assert intake["per_run"]["CR-run-v1"] == {
        "confirmed": 3, "false_positive": 1, "undecidable": 0, "verdicts": 4}
    assert intake["runs_with_verdict_records"] == \
        ["CR-run-v1", "CR-run-v2"]
    assert "本轮在案" in m["dataset"]
    assert m["aux"]["flags_total"] == 6
    # 校准侧实测分列不混写（基座 aux 家族保持）
    assert m["aux"]["calibration_side_measured"][0]["source_id"] == "cal1"
    # fail-closed：run 错配 → blocked
    stranger = _projection_verdicts()[0]
    stranger["critic_run_id"] = "CR-unknown"
    mb = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=[stranger])
    assert mb["status"] == "blocked" and "run 错配" in mb["reason"]
    # fail-closed：hash 对账失败 → blocked
    bad = _projection_verdicts()[0]
    bad["critic_run_record_sha256"] = _sha("other-record")
    mb2 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=[bad])
    assert mb2["status"] == "blocked" and "不符" in mb2["reason"]
    # fail-closed：绑定 run 无证据指针 → blocked（P2-9 缺证即 blocked）
    noev = _projection_verdicts()[0]
    evidence_norun = [e for e in evidence if e["run_id"] != "CR-run-v1"]
    mb6 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence_norun,
        calibration_observation=cal, flag_verdicts=[noev])
    assert mb6["status"] == "blocked" and "缺证" in mb6["reason"]
    # fail-closed：schema 非法 → blocked
    invalid = _projection_verdicts()[0]
    invalid.pop("declared_date")
    mb3 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=[invalid])
    assert mb3["status"] == "blocked" and "schema 非法" in mb3["reason"]
    # fail-closed：同 flag 重复裁定 → blocked
    dup = dict(_projection_verdicts()[0])
    dup["verdict_record_id"] = "VR-dup"
    mb4 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=[_projection_verdicts()[0], dup])
    assert mb4["status"] == "blocked" and "重复" in mb4["reason"]
    # 全不可判定 → not_available（不冒充数值）
    undec = [v for v in _projection_verdicts()
             if v["verdict"] == "unadjudicated"]
    mb5 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=undec)
    assert mb5["status"] == "not_available"
    assert mb5["value"] is None and mb5["denominator"] == 0
    assert "不编造数值" in mb5["reason"]


# ---------------------------------------------------------------------------
# ⑭ canonical 确定性（聚合核与投影同参重建 byte-exact）
# ---------------------------------------------------------------------------

def test_canonical_determinism_agreement_and_projection():
    run = _run(n_flags=4)
    verdicts = _verdicts(run, [(0, "confirmed"), (1, "confirmed"),
                               (2, "confirmed"), (3, "false_positive")])
    a1 = critic.flag_verdict_agreement(run, verdicts)
    a2 = critic.flag_verdict_agreement(run, verdicts)
    assert hashing.canonical_json_bytes(a1) == \
        hashing.canonical_json_bytes(a2)
    runs, evidence, cal = _projection_fixture()
    p1 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=_projection_verdicts())
    p2 = critic.project_judgment_agreement_with_verdicts(
        runs, [], record_evidence=evidence, calibration_observation=cal,
        flag_verdicts=_projection_verdicts())
    assert hashing.canonical_json_bytes(p1) == \
        hashing.canonical_json_bytes(p2)
