"""JUDGE-QUAL-R1 scoring_jq tests: frozen gates + synthetic worlds + history.

Synthetic world: 16 real-named scenarios (cal-f12-01..08 / hol-f6-01..04 /
hol-f8-01..04, the frozen section 3.6 family census) x 1 route each (16
routes, 5 improvable -> rb 15/48 = 0.3125 pooled over 3 reps), p01..p16
(batch one p01-p08 = cal-f12, batch two p09-p16 = hol families), 2 arms
(Q/CTR) x 3 reps x 16 pids = 96 eight-key (pcbflow.v4_2-jq-reading/1)
readings per world.  Two worlds share the corpus:

- good world: Q flags exactly the 5 improvable routes every rep (perfect
  judge) -> G1-G5 all pass, qualification holds;
- drift world: Q rep2 batch one abstains the whole session (hard
  collapse, session variance 1/6, P(imp|abstain) 2/8) -> G3/G4 fail.

Expected confusions are hand-computed literals; every other stratum is
recounted independently in-test.  The frozen real anchors (the r2
reproduction gate over out/v4.2-seat-r2/m1-stats.json, the section 3.7.3
collapse calibration against the frozen REP-R2/R3 session stats, and the
templates.json pinning to the frozen R1 pack corpus) are checked in the
last tests.

Run from the repo root (tools/pcbflow), PYTHONUTF8=1 per pytest.ini.
"""

import json
import math
import os
import random
import re

import pytest

from pcbflow.v4_2_rep import scoring
from pcbflow.v4_2_rep import scoring_jq
from pcbflow.v4_2_rep import scoring_r2

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REAL_OUT = os.path.join(_ROOT, "out", "v4.2-judge-qual-r1")
R2_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r2")
R3_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r3")
R1_PACKS_B = os.path.join(_ROOT, "out", "v4.2-rep-r1", "packs-b")
R1_TASKS_A = os.path.join(_ROOT, "out", "v4.2-rep-r1", "tasks-a")

# ------------------------------------------------------------ synthetic GT
SIDS = (["cal-f12-%02d" % i for i in range(1, 9)]
        + ["hol-f6-%02d" % i for i in (1, 2, 3, 4)]
        + ["hol-f8-%02d" % i for i in (1, 2, 3, 4)])
PIDS = ["p%02d" % i for i in range(1, 17)]
PID_SID = dict(zip(PIDS, SIDS))
IMPROVABLE = {  # 5 improvable of 16 routes
    "cal-f12-07": True, "cal-f12-08": True,
    "hol-f6-01": True, "hol-f6-04": True, "hol-f8-01": True,
}
# flag/abstain targets shared by both worlds (per sid, single route r1)
Q_FLAG = {"cal-f12-07", "cal-f12-08", "hol-f6-01", "hol-f6-04", "hol-f8-01"}
CTR_FLAG = {"cal-f12-07", "cal-f12-02"}
CTR_ABSTAIN = {"hol-f8-01"}
DRIFT_ABSTAIN_REP2_B1 = set(SIDS[:8])          # cal-f12-01..08 (batch one)

_VERDICT_OF = {"f": "flag_bad", "n": "no_flag", "a": "abstain"}


def _q_verdict(sid, rep):
    if rep == 2 and sid in DRIFT_ABSTAIN_REP2_B1:
        return "abstain"          # drift world: rep2 batch one collapses
    return "flag_bad" if sid in Q_FLAG else "no_flag"


def _ctr_verdict(sid, rep):
    if sid in CTR_FLAG:
        return "flag_bad"
    if sid in CTR_ABSTAIN:
        return "abstain"
    return "no_flag"


# hand-computed pooled anchors
#   good Q:    tp=15 fp=0  fn=0  tn=33 abstain=0  n=48 (5 imp x 3 reps)
#   drift Q:   tp=13 fp=0  fn=2  tn=33 abstain=8  n=48
#   CTR (both): tp=3 fp=3 fn=12 tn=30 abstain=3  n=48
GOOD_Q_POOLED = {"tp": 15, "fp": 0, "fn": 0, "tn": 33, "abstain": 0,
                 "n_routes": 48, "improvable": 15, "flag_bad": 15,
                 "precision": 1.0, "recall": 1.0,
                 "abstention_rate": 0.0}
DRIFT_Q_POOLED = {"tp": 13, "fp": 0, "fn": 2, "tn": 33, "abstain": 8,
                  "n_routes": 48, "improvable": 15, "flag_bad": 13,
                  "precision": 1.0, "recall": 13.0 / 15.0,
                  "abstention_rate": 8.0 / 48.0}
CTR_POOLED = {"tp": 3, "fp": 3, "fn": 12, "tn": 30, "abstain": 3,
              "n_routes": 48, "improvable": 15, "flag_bad": 6,
              "precision": 0.5, "recall": 0.2,
              "abstention_rate": 3.0 / 48.0}


# ------------------------------------------------- independent recount (b)
def _recount(drift=False):
    """Independent recount over the synthetic corpus.

    Returns confusions[arm][rep][pid] in the jq extended caliber,
    computed by hand from the verdict rules.
    """
    confusions = {arm: {rep: {} for rep in (1, 2, 3)} for arm in ("Q", "CTR")}
    for arm in ("Q", "CTR"):
        for rep in (1, 2, 3):
            for pid in PIDS:
                sid = PID_SID[pid]
                if arm == "Q":
                    verdict = _q_verdict(sid, rep) if drift else \
                        ("flag_bad" if sid in Q_FLAG else "no_flag")
                else:
                    verdict = _ctr_verdict(sid, rep)
                improvable = IMPROVABLE.get(sid, False)
                conf = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "abstain": 0,
                        "n_routes": 1, "abstain_imp": 0, "abstain_nonimp": 0,
                        "noflag_imp": 0, "noflag_nonimp": 0}
                if verdict == "flag_bad":
                    conf["tp" if improvable else "fp"] += 1
                else:
                    if verdict == "abstain":
                        conf["abstain"] += 1
                        conf["abstain_imp" if improvable
                             else "abstain_nonimp"] += 1
                    else:
                        conf["noflag_imp" if improvable
                             else "noflag_nonimp"] += 1
                    conf["fn" if improvable else "tn"] += 1
                confusions[arm][rep][pid] = conf
    return confusions


# ------------------------------------------------------ world construction
def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def _flags_list(arm, rep, pid, verdict, retry=0):
    reason = "detour_excess" if verdict == "flag_bad" else "uncertain"
    return [{
        "route_id": "r1",
        "verdict": verdict,
        "reason_code": reason,
        "evidence": "ev %s rep%d %s retry%d" % (arm, rep, pid, retry),
    }]


def _reading_obj(arm, rep, pid, verdict, retry=0, first_errors=None):
    return {
        "schema": scoring_jq.READING_SCHEMA,
        "arm": arm,
        "pid": pid,
        "rep": rep,
        "model_output": _flags_list(arm, rep, pid, verdict, retry),
        "return_raw": "```json\n...synthetic...\n```",
        "ts": "2026-10-11T00:00:00",
        "validation": {"errors": [], "passed": True, "retry": retry,
                       "first_attempt_errors": first_errors or []},
    }


def build_world(root, drift=False):
    """Materialize GT + meta + readings + gate fixtures; returns paths."""
    root = str(root)
    os.makedirs(root, exist_ok=True)
    gt = {"gt_version": "synthetic-test/1", "scenarios": {}}
    for sid in SIDS:
        gt["scenarios"][sid] = {
            "n_routes": 1,
            "per_route": {"r1": {"net_id": "n1",
                                 "improvable": IMPROVABLE.get(sid, False)}},
        }
    gt_path = os.path.join(root, "gt.json")
    _write_json(gt_path, gt)
    meta_path = os.path.join(root, "package-meta.json")
    _write_json(meta_path, {pid: {"sid": PID_SID[pid], "n_routes": 1}
                            for pid in PIDS})

    readings_root = os.path.join(root, "readings")
    for arm in ("Q", "CTR"):
        for rep in (1, 2, 3):
            directory = os.path.join(readings_root, arm, "rep%d" % rep)
            os.makedirs(directory)
            for pid in PIDS:
                sid = PID_SID[pid]
                if arm == "Q":
                    verdict = _q_verdict(sid, rep) if drift else \
                        ("flag_bad" if sid in Q_FLAG else "no_flag")
                else:
                    verdict = _ctr_verdict(sid, rep)
                # retry fixtures (both worlds): base + -r1 for Q rep2 p02,
                # lone -r1 (no base) for CTR rep3 p16
                if arm == "Q" and rep == 2 and pid == "p02":
                    _write_json(os.path.join(directory, "p02.json"),
                                _reading_obj(arm, rep, pid, "no_flag"))
                    _write_json(
                        os.path.join(directory, "p02-r1.json"),
                        _reading_obj(arm, rep, pid, verdict, retry=1,
                                     first_errors=["rule1/2: mismatch"]))
                    continue
                if arm == "CTR" and rep == 3 and pid == "p16":
                    _write_json(
                        os.path.join(directory, "p16-r1.json"),
                        _reading_obj(arm, rep, pid, verdict, retry=1,
                                     first_errors=["rule6: key set"]))
                    continue
                _write_json(os.path.join(directory, "%s.json" % pid),
                            _reading_obj(arm, rep, pid, verdict))

    # gate fixtures: a mini r2 world (r1/r2 four-key readings) + m1-stats
    r2_readings = os.path.join(root, "r2-m1-readings")
    os.makedirs(r2_readings)
    for pid in PIDS:
        sid = PID_SID[pid]
        verdict = "flag_bad" if IMPROVABLE.get(sid, False) else "no_flag"
        _write_json(
            os.path.join(r2_readings, "%s.json" % pid),
            {"schema": "v4.2-rep-r2-reading/1", "arm": "B", "rep": 1,
             "pid": pid, "flags": _flags_list("B", 1, pid, verdict)})
    r2_stats_path = os.path.join(root, "m1-stats.json")
    produced = scoring_r2._reproduce_r2_param(gt_path, meta_path, r2_readings)
    _write_json(r2_stats_path, produced)
    return gt_path, meta_path, readings_root, r2_readings, r2_stats_path


def _score_kwargs(world, out_dir):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = world
    return {"gt_path": gt_path, "package_meta_path": meta_path,
            "readings_root": readings_root, "out_dir": out_dir,
            "reproduce_kwargs": {"gt_path": gt_path,
                                 "package_meta_path": meta_path,
                                 "readings_dir": r2_readings,
                                 "r2_stats_path": r2_stats_path}}


@pytest.fixture(scope="module")
def good_world(tmp_path_factory):
    return build_world(tmp_path_factory.mktemp("jq_good"), drift=False)


@pytest.fixture(scope="module")
def drift_world(tmp_path_factory):
    return build_world(tmp_path_factory.mktemp("jq_drift"), drift=True)


@pytest.fixture(scope="module")
def good_result(good_world, tmp_path_factory):
    out = tmp_path_factory.mktemp("jq_good_out")
    return scoring_jq.score_jq(**_score_kwargs(good_world, out)), out


@pytest.fixture(scope="module")
def drift_result(drift_world, tmp_path_factory):
    out = tmp_path_factory.mktemp("jq_drift_out")
    return scoring_jq.score_jq(**_score_kwargs(drift_world, out)), out


# --------------------------------------------- 1. frozen real reproduce gate
def test_reproduce_r2_real_frozen_values():
    gate = scoring_jq.reproduce_r2()
    assert gate["passed"] and gate["problems"] == []
    p = gate["produced"]
    assert (p["tp"], p["fp"], p["fn"], p["tn"]) == (20, 6, 13, 84)
    assert p["n_routes"] == 123 and p["abstention_rate"] == 0.0
    for key, want in (("precision", 0.7692307692307693),
                      ("recall", 0.6060606060606061),
                      ("random_baseline", 0.2682926829268293)):
        assert abs(p[key] - want) <= 1e-9, (key, p[key], want)
    assert p["gate"]["passed"] is True


def test_reproduce_r2_synthetic_redirect(tmp_path):
    # the parameterized twin keeps the gate testable on synthetic fixtures
    # (fresh world: this test tampers with its m1-stats fixture)
    world = build_world(tmp_path / "w", drift=False)
    gt_path, meta_path, _rr, r2_readings, r2_stats_path = world
    gate = scoring_jq.reproduce_r2(gt_path=gt_path,
                                   package_meta_path=meta_path,
                                   readings_dir=r2_readings,
                                   r2_stats_path=r2_stats_path)
    assert gate["passed"]
    tampered = json.load(open(r2_stats_path, encoding="utf-8"))
    tampered["tp"] += 1
    _write_json(r2_stats_path, tampered)
    gate2 = scoring_jq.reproduce_r2(gt_path=gt_path,
                                    package_meta_path=meta_path,
                                    readings_dir=r2_readings,
                                    r2_stats_path=r2_stats_path)
    assert not gate2["passed"] and gate2["problems"]


def test_score_jq_gate_blocks_on_failure(drift_world, tmp_path):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        drift_world
    tampered = json.load(open(r2_stats_path, encoding="utf-8"))
    tampered["recall"] = 0.5
    broken = tmp_path / "broken-m1-stats.json"
    _write_json(str(broken), tampered)
    with pytest.raises(RuntimeError, match="reproduction gate FAILED"):
        scoring_jq.score_jq(
            gt_path=gt_path, package_meta_path=meta_path,
            readings_root=readings_root, out_dir=tmp_path / "o",
            reproduce_kwargs={"gt_path": gt_path,
                              "package_meta_path": meta_path,
                              "readings_dir": r2_readings,
                              "r2_stats_path": str(broken)})


# --------------------------------- 2. eight-key parsing + retry resolution
def test_eight_key_parsing_retry_and_first_attempt(drift_world):
    gt_path, meta_path, readings_root, _rr, _rs = drift_world
    meta, route_impr, _sids = scoring_jq._gt_tables(gt_path, meta_path)
    confusions, reasons, chosen, superseded, first_failed = \
        scoring_jq.load_readings(readings_root, meta, route_impr)
    assert chosen["Q"][2]["p02"] == "p02-r1.json"
    assert superseded["Q"][2] == {"p02": ["p02.json"]}
    assert chosen["CTR"][3]["p16"] == "p16-r1.json"
    assert "p16" not in superseded.get("CTR", {}).get(3, {})
    assert first_failed == {("Q", 2, "p02"), ("CTR", 3, "p16")}
    # every confusion matches the independent recount, and the frozen
    # four-cell caliber (scoring._confusion) agrees on the six keys
    want = _recount(drift=True)
    for arm in ("Q", "CTR"):
        for rep in (1, 2, 3):
            for pid in PIDS:
                got = confusions[arm][rep][pid]
                assert got == want[arm][rep][pid], (arm, rep, pid)
                sid = meta[pid]["sid"]
                verdict = (_q_verdict(sid, rep) if arm == "Q"
                           else _ctr_verdict(sid, rep))
                flags = [{"route_id": "r1", "verdict": verdict,
                          "reason_code": "detour_excess"
                          if verdict == "flag_bad" else "uncertain",
                          "evidence": "ev"}]
                frozen = scoring._confusion(flags, route_impr[sid])
                assert frozen == {k: got[k]
                                  for k in scoring_r2._CONF_KEYS}


# ------------------------------------------------ 3. pooled caliber anchors
def test_good_world_q_pooled_literal(good_result):
    result, _out = good_result
    q = result["arms"]["Q"]
    for key, want in GOOD_Q_POOLED.items():
        assert q[key] == want, (key, q[key], want)
    assert q["random_baseline"] == 15.0 / 48.0
    assert q["random_baseline_frozen"]["matches"] is False  # not 369/99
    assert q["schema_compliant_readings"] == 48
    assert q["schema_compliance_rate"] == 1.0
    assert q["first_attempt_compliant_readings"] == 47  # Q rep2 p02 retried
    assert q["first_attempt_compliance_rate"] == 47.0 / 48.0


def test_drift_world_pooled_literals(drift_result):
    result, _out = drift_result
    for key, want in DRIFT_Q_POOLED.items():
        assert result["arms"]["Q"][key] == want, key
    for key, want in CTR_POOLED.items():
        assert result["arms"]["CTR"][key] == want, key
    # caliber identities: fn = abstain_imp + noflag_imp etc.
    q = result["arms"]["Q"]
    conf = {"abstain_imp": 2, "abstain_nonimp": 6, "noflag_imp": 0,
            "noflag_nonimp": 27}
    assert q["fn"] == conf["abstain_imp"] + conf["noflag_imp"] == 2
    assert q["tn"] == conf["abstain_nonimp"] + conf["noflag_nonimp"] == 33
    assert q["abstain"] == conf["abstain_imp"] + conf["abstain_nonimp"] == 8


def test_strata_add_up_and_family_census(good_result):
    result, _out = good_result
    for arm in ("Q", "CTR"):
        s = result["arms"][arm]
        keys = ("tp", "fp", "fn", "tn", "abstain", "n_routes")
        assert len(s["per_rep"]) == 3 and len(s["per_session"]) == 6
        assert len(s["per_scenario"]) == 16
        for part in ("per_rep", "per_session", "per_scenario"):
            tot = {k: sum(row[k] for row in s[part].values())
                   for k in keys}
            assert {k: tot[k] for k in keys} == {k: s[k] for k in keys}
        # section 3.6 family census: five indicators per family per arm
        assert sorted(s["per_family"]) == ["cal-f12", "hol-f6", "hol-f8"]
        assert [s["per_family"][f]["n_scenarios"]
                for f in ("cal-f12", "hol-f6", "hol-f8")] == [8, 4, 4]
        fam_tot = {k: sum(s["per_family"][f][k]
                          for f in s["per_family"])
                   for k in ("tp", "fp", "fn", "tn", "abstain", "n_routes")}
        assert {k: fam_tot[k] for k in keys} == {k: s[k] for k in keys}
        for family, row in s["per_family"].items():
            assert row["improvable_rate"] == \
                row["improvable"] / row["n_routes"]
            assert row["five_indicators"] == [
                "n_routes", "improvable_rate", "precision", "recall",
                "abstention_rate"]


# ------------------------------------------------ 4. calibration (3.7.4)
def test_calibration_blocks(good_result, drift_result):
    good, _g = good_result
    drift, _d = drift_result
    qg = good["arms"]["Q"]["calibration"]
    assert qg["ece"] == "not_available"
    three = qg["three_state_conditional_improvable"]
    assert three["P_imp_given_flag_bad"] == 1.0
    assert three["P_imp_given_abstain"] is None      # zero abstentions
    assert three["P_imp_given_no_flag"] == 0.0
    assert qg["monotonicity_flag_bad_ge_no_flag"] is True
    qd = drift["arms"]["Q"]["calibration"]
    threed = qd["three_state_conditional_improvable"]
    assert threed["P_imp_given_flag_bad"] == 1.0     # == precision identity
    assert threed["P_imp_given_abstain"] == pytest.approx(2.0 / 8.0)
    assert threed["P_imp_given_no_flag"] == 0.0
    assert threed["n_flag_bad"] == 13 and threed["n_abstain"] == 8
    assert threed["n_no_flag"] == 27
    assert qd["monotonicity_flag_bad_ge_no_flag"] is True
    # reason_code sublayer: flags carry detour_excess, rest uncertain
    sub = qd["reason_code_sublayer"]
    assert sub["detour_excess"]["n"] == 13
    assert sub["detour_excess"]["n_improvable"] == 13
    assert sub["detour_excess"]["improvable_rate"] == 1.0
    assert sub["uncertain"]["n"] == 35               # 48 - 13 flags
    assert sub["uncertain"]["n_improvable"] == 2     # the abstained pair
    assert sub["uncertain"]["improvable_rate"] == pytest.approx(2.0 / 35.0)
    assert set(sub) == set(scoring.REASON_CODES)


# ------------------------------------- 5. session variance + collapse (3.7)
def test_session_variance_and_drift_table(drift_result):
    result, _out = drift_result
    q = result["arms"]["Q"]["session_variance"]
    assert q["session_recalls"] == {
        "rep1-batch1": 1.0, "rep1-batch2": 1.0,
        "rep2-batch1": 0.0, "rep2-batch2": 1.0,
        "rep3-batch1": 1.0, "rep3-batch2": 1.0}
    assert q["all_defined"] is True
    assert q["sample_variance"] == pytest.approx(1.0 / 6.0)
    assert q["sample_std"] == pytest.approx(math.sqrt(1.0 / 6.0))
    assert q["range"] == 1.0 and q["min"] == 0.0 and q["max"] == 1.0
    c = result["arms"]["CTR"]["session_variance"]
    assert c["sample_variance"] == pytest.approx(0.075)
    assert c["sample_std"] == pytest.approx(math.sqrt(0.075))
    assert c["range"] == 0.5
    # 12-session drift table: R2 section 4.3 shape, ordered rows
    sessions = result["sessions"]["sessions"]
    assert len(sessions) == 12
    assert [("%s%d%d" % (r["arm"], r["rep"], r["batch"])) for r in sessions] \
        == ["%s%d%d" % (arm, rep, batch)
            for arm in ("Q", "CTR") for rep in (1, 2, 3)
            for batch in (1, 2)]
    for row in sessions:
        assert set(row) == {"arm", "rep", "batch", "tp", "fp", "fn", "tn",
                            "recall", "precision", "abstain_rate"}
    q_b1_rep2 = [r for r in sessions
                 if r["arm"] == "Q" and r["rep"] == 2 and r["batch"] == 1][0]
    assert q_b1_rep2["recall"] == 0.0 and q_b1_rep2["abstain_rate"] == 1.0


def test_collapse_blocks(drift_result):
    result, _out = drift_result
    q = result["arms"]["Q"]["collapse"]
    assert q["hard_sessions"] == ["rep2-batch1"]
    assert q["hard_count"] == 1 and q["hard_rate"] == pytest.approx(1 / 6)
    assert q["soft_sessions"] == ["rep2-batch1"]  # 0.0 < 0.5*13/15
    assert q["soft_threshold"] == pytest.approx(0.5 * 13.0 / 15.0)
    c = result["arms"]["CTR"]["collapse"]
    assert c["hard_sessions"] == ["rep1-batch2", "rep2-batch2", "rep3-batch2"]
    assert c["hard_rate"] == pytest.approx(0.5)
    # CTR batch-one sessions: recall 0.5, flag_bad = 2 <= 2 but tp = 1
    # -> count rule does not fire, recall rule does not fire: not hard
    assert c["hard_count"] == 3
    assert c["soft_sessions"] == ["rep1-batch2", "rep2-batch2",
                                  "rep3-batch2"]  # 0.0 < 0.5*0.2
    assert c["soft_rate"] == pytest.approx(0.5)


# ------------------------------------------------------- 6. bootstrap (3.8)
def _cluster_inputs(world, drift):
    gt_path, meta_path, readings_root, _rr, _rs = world
    meta, route_impr, sids = scoring_jq._gt_tables(gt_path, meta_path)
    confusions, _r, _c, _s, _f = scoring_jq.load_readings(
        readings_root, meta, route_impr)
    cluster_rows, session_rows = {}, {}
    for arm in ("Q", "CTR"):
        pooled_sid = {sid: {k: 0 for k in scoring_r2._CONF_KEYS}
                      for sid in sids}
        per_rep_sid = {rep: {sid: {k: 0 for k in scoring_r2._CONF_KEYS}
                             for sid in sids} for rep in (1, 2, 3)}
        for rep in (1, 2, 3):
            for pid, conf in confusions[arm][rep].items():
                sid = meta[pid]["sid"]
                for k in scoring_r2._CONF_KEYS:
                    pooled_sid[sid][k] += conf[k]
                    per_rep_sid[rep][sid][k] += conf[k]
        cluster_rows[arm] = [pooled_sid[sid] for sid in sids]
        session_rows[arm] = {rep: [per_rep_sid[rep][sid]
                                   for sid in sids] for rep in (1, 2, 3)}
    batch_of_index = [1 if pid <= "p08" else 2
                      for pid in (scoring_jq.pid_of_sid(meta, sid)
                                  for sid in sids)]
    return cluster_rows, session_rows, batch_of_index


def test_bootstrap_reproducible_and_counted(drift_world):
    cluster_rows, session_rows, batches = _cluster_inputs(drift_world, True)
    ci1 = scoring_jq._bootstrap_jq(cluster_rows, session_rows, batches,
                                   seed=scoring_jq.BOOTSTRAP_SEED,
                                   n_boot=500)
    ci2 = scoring_jq._bootstrap_jq(cluster_rows, session_rows, batches,
                                   seed=scoring_jq.BOOTSTRAP_SEED,
                                   n_boot=500)
    assert ci1 == ci2
    ci3 = scoring_jq._bootstrap_jq(cluster_rows, session_rows, batches,
                                   seed=1, n_boot=500)
    assert ci3 != ci1  # fixed seed: deterministic, never flaky
    for key, entry in ci1.items():
        assert entry["n_defined"] + entry["n_undefined"] == 500, key
        if entry["n_defined"]:
            assert entry["low"] <= entry["high"], key
    # abstention never undefined (n* > 0 in every replicate)
    assert ci1["abstention_Q"]["n_undefined"] == 0
    # session-variance parameters hit the undefined convention whenever a
    # replicate draws no improvable route of some batch (documented caliber)
    assert ci1["session_recall_var_Q"]["n_undefined"] > 0
    assert ci1["session_recall_var_diff_Q-CTR"]["n_undefined"] >= \
        ci1["session_recall_var_Q"]["n_undefined"]


def test_paired_stats_and_rep_level(drift_result):
    result, _out = drift_result
    paired = result["paired"]
    assert paired["seed"] == 20261011 and paired["n_bootstrap"] == 10000
    assert paired["n_clusters"] == 16
    comp = paired["comparisons"]["Q-CTR"]
    assert comp["recall_diff"] == pytest.approx(13.0 / 15.0 - 0.2)
    assert comp["precision_diff"] == pytest.approx(1.0 - 0.5)
    assert comp["abstention_diff"] == pytest.approx(8.0 / 48.0 - 3.0 / 48.0)
    # rep-level 3 points: rep1 1.0-0.2, rep2 0.6-0.2, rep3 1.0-0.2
    assert comp["rep_level_recall_diff"] == {
        "rep1": pytest.approx(0.8), "rep2": pytest.approx(0.4),
        "rep3": pytest.approx(0.8)}
    # Q precision is 1.0 in every defined replicate -> CI degenerates
    pq = paired["per_arm_bootstrap_ci95"]["precision"]["Q"]
    assert pq["low"] == 1.0 and pq["high"] == 1.0
    assert pq["n_defined"] + pq["n_undefined"] == 10000
    assert pq["n_undefined"] > 0  # replicates that drew zero Q flags
    sv = paired["session_variance"]
    assert sv["point_estimates"]["Q"]["sample_variance"] == \
        pytest.approx(1.0 / 6.0)
    assert sv["point_estimates"]["CTR"]["sample_variance"] == \
        pytest.approx(0.075)
    for stat, entry in sv["bootstrap_ci95"]["sample_variance"].items():
        if stat == "diff_Q-CTR":
            assert entry["n_defined"] + entry["n_undefined"] == 10000
            continue
        assert entry["n_defined"] + entry["n_undefined"] == 10000
        assert entry["low"] is not None and entry["high"] is not None
    assert "16 clusters" in paired["resample_unit"]
    assert "never 48" in paired["cluster_caliber"]


# ------------------------------------------- 7. qualification gates (3.10)
def test_good_world_qualification_passes(good_result):
    result, _out = good_result
    gate = result["qualification"]
    assert gate["all_passed"] is True and gate["gates_failed"] == []
    g = gate["gates"]
    assert g["G1"]["point_threshold"] == pytest.approx(max(2 * 15 / 48, 0.4))
    assert g["G1"]["ci95_low"] == 1.0 and g["G1"]["passed"] is True
    assert g["G2"]["abstention_rate"] == 0.0 and g["G2"]["passed"] is True
    assert g["G3"]["hard_count"] == 0 and g["G3"]["passed"] is True
    assert g["G4"]["range"] == 0.0 and g["G4"]["passed"] is True
    assert g["G5"]["P_imp_given_flag_bad"] == 1.0
    assert g["G5"]["P_imp_given_no_flag"] == 0.0
    assert g["G5"]["passed"] is True
    assert gate["stratification_factors"]["reasoning_effort"]["levels"] == \
        ["not_available"]
    assert gate["historical_reference_band"]["r2_b_recall"] == 0.7071
    assert gate["historical_reference_band"]["r3_b_ci95"] == [0.6577, 0.8975]


def test_drift_world_gates_g3_g4_fail(drift_result):
    result, _out = drift_result
    gate = result["qualification"]
    assert gate["gates_failed"] == ["G3", "G4"]
    assert gate["all_passed"] is False
    g = gate["gates"]
    assert g["G1"]["passed"] is True   # precision 1.0, CI [1,1]
    assert g["G2"]["passed"] is True   # abstention 8/48 <= 0.5
    assert g["G3"]["passed"] is False and g["G3"]["hard_count"] == 1
    assert g["G4"]["passed"] is False and g["G4"]["range"] == 1.0
    assert g["G4"]["sample_std"] == pytest.approx(math.sqrt(1 / 6))
    assert g["G5"]["passed"] is True


def test_gate_fail_closed_on_undefined_inputs():
    def q_stats(precision, recall_no_flag, variance_range, hard_count,
                all_defined, abstention=0.0, rb=0.3):
        return {
            "random_baseline": rb, "precision": precision,
            "abstention_rate": abstention,
            "collapse": {"hard_count": hard_count, "hard_sessions": [],
                         "hard_rate": hard_count / 6},
            "session_variance": {"range": variance_range,
                                 "sample_std": None,
                                 "all_defined": all_defined},
            "calibration": {"three_state_conditional_improvable": {
                "P_imp_given_flag_bad": precision,
                "P_imp_given_no_flag": recall_no_flag}},
        }
    ci = {"precision_Q": {"low": None, "high": None, "n_defined": 0,
                          "n_undefined": 10000}}
    # precision None (zero flags) -> G1 fails closed
    gate = scoring_jq._qualification_gate(
        q_stats(None, 0.0, 0.0, 0, True), ci)
    assert gate["gates"]["G1"]["passed"] is False
    # undefined session recall -> G4 fails closed
    gate = scoring_jq._qualification_gate(
        q_stats(1.0, 0.0, None, 0, False), ci)
    assert gate["gates"]["G4"]["passed"] is False
    assert gate["gates"]["G4"]["undefined_session_recall"] is True
    # P(imp|no_flag) None (all flagged or all abstained) -> G5 fails closed
    gate = scoring_jq._qualification_gate(
        q_stats(1.0, None, 0.0, 0, True), ci)
    assert gate["gates"]["G5"]["passed"] is False
    # a clean minimal configuration passes G1 only with a real CI low
    ci_ok = {"precision_Q": {"low": 0.5, "high": 1.0, "n_defined": 10000,
                             "n_undefined": 0}}
    gate = scoring_jq._qualification_gate(
        q_stats(0.6, 0.5, 0.1, 0, True), ci_ok)
    for name in ("G1", "G2", "G3", "G4", "G5"):
        assert gate["gates"][name]["passed"] is True, name
    assert gate["all_passed"] is True


# ---------------------------------------------- 8. fail-closed validation
def _mutate_and_expect_raise(tmp_path, drift, mutate):
    world = build_world(tmp_path / "w", drift=drift)
    out = tmp_path / "out"
    out.mkdir()
    mutate(world[2])
    with pytest.raises(RuntimeError):
        scoring_jq.score_jq(**_score_kwargs(world, out))


def test_fail_closed_invalid_verdict(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "CTR", "rep1", "p03.json")
        data = json.load(open(path, encoding="utf-8"))
        data["model_output"][0]["verdict"] = "maybe"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, False, mutate)


def test_fail_closed_seven_key_reading(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        del data["ts"]  # eight-key contract violated
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, False, mutate)


def test_fail_closed_unvalidated_reading(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["validation"]["passed"] = False
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, False, mutate)


def test_fail_closed_arm_schema_rep_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["arm"] = "CTR"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path / "m1", False, mutate)

    def mutate2(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["schema"] = "v4.2-rep-r3-reading/1"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path / "m2", False, mutate2)

    def mutate3(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["rep"] = 3
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path / "m3", False, mutate3)


def test_fail_closed_missing_reading(tmp_path):
    def mutate(readings_root):
        os.remove(os.path.join(readings_root, "CTR", "rep2", "p10.json"))
    _mutate_and_expect_raise(tmp_path, False, mutate)


def test_fail_closed_empty_evidence(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "Q", "rep1", "p07.json")
        data = json.load(open(path, encoding="utf-8"))
        data["model_output"][0]["verdict"] = "flag_bad"
        data["model_output"][0]["evidence"] = "   "
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, False, mutate)


# ------------------------------------------------ 9. end-to-end determinism
def test_score_jq_deterministic_bytes(tmp_path):
    outs = []
    for tag in ("o1", "o2"):
        world = build_world(tmp_path / ("w_" + tag), drift=True)
        out = tmp_path / tag
        out.mkdir()
        scoring_jq.score_jq(**_score_kwargs(world, out))
        outs.append({p.name: p.read_bytes()
                     for p in sorted(out.glob("*.json"))})
    assert sorted(outs[0]) == ["arm-ctr-stats.json", "arm-q-stats.json",
                               "paired-stats.json",
                               "qualification-gate.json",
                               "session-stats.json"]
    assert outs[0] == outs[1]  # byte-deterministic across fresh worlds
    raw = outs[0]["qualification-gate.json"]
    assert raw.endswith(b"\n") and b"\r" not in raw
    assert raw.decode("utf-8") == json.dumps(
        json.loads(raw.decode("utf-8")), sort_keys=True,
        ensure_ascii=False, indent=1, allow_nan=False) + "\n"


# ------------------------------------------------- 10. path-d scan channel
def test_pathd_scan_hits_and_negative_control(tmp_path):
    world = build_world(tmp_path / "w", drift=False)
    readings_root = world[2]
    path = os.path.join(readings_root, "Q", "rep1", "p01.json")
    data = json.load(open(path, encoding="utf-8"))
    data["model_output"][0]["evidence"] = \
        'stub route d="M 36,8 L 36,8" (zero-length path d reference)'
    _write_json(path, data)
    scan = scoring_jq.scan_pathd_references(
        readings_root=readings_root, gt_path=world[0],
        package_meta_path=world[1])
    assert scan["arms"]["Q"]["n_hits"] >= 2  # literal + command-string
    assert scan["arms"]["Q"]["by_pattern"]["literal_d_eq_M"] == 1
    assert scan["arms"]["Q"]["n_entries_scanned"] == 48
    assert scan["arms"]["CTR"]["n_hits"] == 0  # negative control clean
    assert "R2 §4.6" in scan["disposal"]


# ------------------------- 11. section 3.7.3 calibration on frozen history
def _session_rows(out_dir, arm):
    data = json.load(open(os.path.join(out_dir, "session-stats.json"),
                          encoding="utf-8"))
    return {(r["arm"], r["rep"], r["batch"]): r for r in data["sessions"]
            if r["arm"] == arm}


def _arm_recall(out_dir, arm):
    data = json.load(open(os.path.join(out_dir,
                                       "arm-%s-stats.json" % arm.lower()),
                          encoding="utf-8"))
    return data["recall"]


def test_collapse_calibration_r2_b_rep2_batch1_hard():
    # PREREG section 3.7.3: "R2 B rep2 batch 1 (1 flag all fp, recall 0)
    # -> hard collapse" (frozen session stats, 1 flag_bad all fp)
    rows = _session_rows(R2_OUT, "B")
    row = rows[("B", 2, 1)]
    assert (row["tp"], row["fp"]) == (0, 1) and row["recall"] == 0.0
    assert scoring_jq.classify_hard(row) is True


def test_collapse_calibration_r3_b_rep2_batch2_soft_not_hard():
    # PREREG section 3.7.3: "R3 B rep2 batch 2 (recall 0.2941 < 0.3940 =
    # 0.5x0.7879) -> soft collapse not hard"
    rows = _session_rows(R3_OUT, "B")
    row = rows[("B", 2, 2)]
    assert row["recall"] == pytest.approx(0.2941, abs=1e-4)
    assert scoring_jq.classify_hard(row) is False
    pooled = _arm_recall(R3_OUT, "B")
    assert pooled == pytest.approx(0.7879, abs=1e-4)
    assert 0.5 * pooled == pytest.approx(0.3940, abs=1e-4)
    assert scoring_jq.classify_soft(row, pooled) is True


def test_collapse_calibration_r2_a_scaled_threshold():
    # the scaled soft threshold does not misjudge the one working session
    # of the floor arm: recall 0.0588 >= 0.5 x pooled 0.0101
    rows = _session_rows(R2_OUT, "A")
    pooled = _arm_recall(R2_OUT, "A")
    assert pooled == pytest.approx(1 / 99)
    working = rows[("A", 1, 2)]
    assert working["recall"] == pytest.approx(1 / 17)
    assert scoring_jq.classify_soft(working, pooled) is False
    # zero-recall sessions of the same arm sit below half of the arm
    # level (correct scaled characterization, not a fixed-band artifact)
    floor = rows[("A", 1, 1)]
    assert floor["recall"] == 0.0
    assert scoring_jq.classify_soft(floor, pooled) is True


def test_collapse_calibration_r2_c_pooled_floor_no_soft():
    # pooled recall exactly 0 -> threshold 0 -> no session is strictly
    # below it: the floor arm is characterized by hard, not soft, collapse
    rows = _session_rows(R2_OUT, "C")
    pooled = _arm_recall(R2_OUT, "C")
    assert pooled == 0.0
    assert all(scoring_jq.classify_soft(row, pooled) is False
               for row in rows.values())
    assert any(scoring_jq.classify_hard(row) for row in rows.values())


# ------------------------------------------------- 12. arm order (3.1 draw)
def test_arm_order_precomputation():
    # PREREG section 3.1: random.Random(20261011) shuffle of ['Q','CTR']
    # -> base permutation, rep k order = base right-rotated k-1
    base = ["Q", "CTR"]
    random.Random(20261011).shuffle(base)
    assert base == ["Q", "CTR"]
    orders = []
    for k in (1, 2, 3):
        orders.append(base[-(k - 1):] + base[:-(k - 1)] if k > 1
                      else list(base))
    assert orders == [["Q", "CTR"], ["CTR", "Q"], ["Q", "CTR"]]


# ------------------------------------------------ 13. templates (the rig)
_TEMPLATES_PATH = os.path.join(REAL_OUT, "templates.json")


def test_templates_file_exists_and_schema():
    assert os.path.isfile(_TEMPLATES_PATH)
    tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
    assert tpl["schema"] == scoring_jq.TEMPLATES_SCHEMA
    for key in ("q_system", "q_head", "q_tail", "ctr_system", "ctr_head",
                "ctr_tail"):
        assert isinstance(tpl[key], str) and tpl[key]


def test_verify_templates_pins_frozen_corpus():
    report = scoring_jq.verify_templates()
    assert report["passed"], report["problems"]
    assert set(report["arms"]) == {"Q", "CTR"}
    for arm, summary in report["arms"].items():
        assert summary["n_packs"] == 16
        assert summary["sha256_anchored"] is True


def test_templates_independent_rederivation():
    """Re-derive head/tail/system from the frozen corpus independently."""
    tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
    import hashlib
    for arm, key, directory in (("Q", "q", R1_PACKS_B),
                                ("CTR", "ctr", R1_TASKS_A)):
        files = sorted(f for f in os.listdir(directory)
                       if re.match(r"^p\d{2}\.json$", f))
        assert len(files) == 16
        systems, users, shas = [], [], {}
        for name in files:
            obj = json.load(open(os.path.join(directory, name),
                                 encoding="utf-8"))
            systems.append(obj["system"])
            users.append(obj["user"])
            shas[obj["pid"]] = hashlib.sha256(
                open(os.path.join(directory, name), "rb").read()).hexdigest()
        assert len(set(systems)) == 1
        assert tpl["%s_system" % key] == systems[0]
        # longest common prefix / suffix, recomputed here
        pre = users[0]
        for u in users[1:]:
            i = 0
            while i < min(len(pre), len(u)) and pre[i] == u[i]:
                i += 1
            pre = pre[:i]
        suf = users[0]
        for u in users[1:]:
            i = 0
            while i < min(len(suf), len(u)) and \
                    suf[len(suf) - 1 - i] == u[len(u) - 1 - i]:
                i += 1
            suf = suf[len(suf) - i:]
        assert tpl["%s_head" % key] == pre
        assert tpl["%s_tail" % key] == suf
        # exact reconstruction of every frozen user text
        for u in users:
            assert u.startswith(pre) and u.endswith(suf)
            assert u == pre + u[len(pre):len(u) - len(suf)] + suf
        assert tpl["frozen_sources"][arm]["sha256"] == shas


def test_templates_contract_blocks():
    tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
    oc = tpl["output_contract"]
    assert sorted(oc["reading_keys"]) == sorted(scoring_jq.READING_KEYS)
    assert oc["reading_schema"] == scoring_jq.READING_SCHEMA
    assert oc["arm_values"] == ["Q", "CTR"]
    discipline = tpl["subject_discipline"]
    clauses = discipline["clauses"]
    assert len(clauses) == 6            # R2 section 4 six clauses verbatim
    assert "零工具、零文件访问、零命令" in clauses[0]
    assert "abstain" in clauses[1]
    assert "求解器" in clauses[3]
    assert "不追加任何纪律文本" in discipline["application"]["note"]
    pathd = tpl["pathd_disclosure_channel"]
    assert pathd["arm"] == "CTR"
    assert "§4.6" in pathd["caliber"]
    assert len(pathd["patterns"]) == 4

# ------------------------------------------------------------- jq_glue tests
from pcbflow.v4_2_rep import jq_glue  # noqa: E402


def test_templates_marker_contract_pinned():
    """output_contract.pack_marker + session_ask_assembly are pinned."""
    tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
    oc = tpl["output_contract"]
    marker = oc["pack_marker"]
    assert marker["line_template"] == scoring_jq.PACK_MARKER_TEMPLATE
    assert marker["pid_pattern"] == scoring_jq.PACK_MARKER_PID_PATTERN
    for pid in ("p01", "p08", "p09", "p16"):
        line = scoring_jq.PACK_MARKER_TEMPLATE.format(pid=pid)
        m = scoring_jq.PACK_MARKER_LINE_RE.match(line)
        assert m is not None and m.group(1) == pid
    assert scoring_jq.PACK_MARKER_LINE_RE.match("===PACK p1===") is None
    assert scoring_jq.PACK_MARKER_LINE_RE.match("===PACK p011===") is None
    assert scoring_jq.PACK_MARKER_LINE_RE.match("x===PACK p01===") is None
    assert oc["session_ask_assembly"]["schema"] == \
        scoring_jq.SESSION_ASK_SCHEMA
    # verify_templates (which now checks both blocks) passes on the real file
    report = scoring_jq.verify_templates()
    assert report["passed"], report["problems"]


_DEL = object()


@pytest.fixture
def templates_mutator(tmp_path):
    """Copy templates.json into tmp, mutate fields, return the path."""
    def make(mut=None, inject=None):
        path = tmp_path / ("templates-%d.json" % next(_counter))
        tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
        if mut:
            for dotted, value in mut.items():
                node = tpl
                keys = dotted.split(".")
                for k in keys[:-1]:
                    node = node[k]
                if value is _DEL:
                    del node[keys[-1]]
                else:
                    node[keys[-1]] = value
        if inject:
            tpl.update(inject)
        scoring._write_canonical(path, tpl)
        return str(path)
    return make


def _counter_gen():
    i = 0
    while True:
        i += 1
        yield i


_counter = _counter_gen()


def test_verify_templates_rejects_marker_contract_drift(templates_mutator):
    base = dict(packs_b_dir=R1_PACKS_B, tasks_a_dir=R1_TASKS_A)
    good = scoring_jq.verify_templates(
        templates_path=templates_mutator(), **base)
    assert good["passed"], good["problems"]
    bad_line = scoring_jq.verify_templates(templates_path=templates_mutator(
        mut={"output_contract.pack_marker.line_template": "##PACK {pid}##"}),
        **base)
    assert not bad_line["passed"] and any("line_template" in p
                                          for p in bad_line["problems"])
    bad_pat = scoring_jq.verify_templates(templates_path=templates_mutator(
        mut={"output_contract.pack_marker.pid_pattern": "p[0-9]{3}"}), **base)
    assert not bad_pat["passed"] and any("pid_pattern" in p
                                         for p in bad_pat["problems"])
    no_ask = scoring_jq.verify_templates(templates_path=templates_mutator(
        mut={"output_contract.session_ask_assembly": _DEL}), **base)
    assert not no_ask["passed"] and any("session_ask_assembly" in p
                                        for p in no_ask["problems"])
    # marker injected into a frozen template string -> hard fail
    tpl = json.load(open(_TEMPLATES_PATH, encoding="utf-8"))
    injected = dict(tpl)
    injected["q_tail"] = "===PACK p01===\n" + tpl["q_tail"]
    p2 = templates_mutator(inject=injected)
    bad_inject = scoring_jq.verify_templates(templates_path=p2, **base)
    assert not bad_inject["passed"] and any("pack marker inside" in p
                                            for p in bad_inject["problems"])


def test_glue_split_session_output():
    pids = ["p01", "p02"]
    text = ('===PACK p01===\n{"flags": []}\n===PACK p02===\n'
            '{"flags": []}')
    res = jq_glue.split_session_output(text, pids)
    assert res["ok"], res["problems"]
    assert res["bodies"]["p01"] == '{"flags": []}'
    assert not jq_glue.split_session_output(
        "===PACK p02===\nx\n===PACK p01===\ny", pids)["ok"]      # order
    assert not jq_glue.split_session_output(
        "===PACK p01===\nx", pids)["ok"]                          # missing
    assert not jq_glue.split_session_output(
        "===PACK p01===\nx\n===PACK p01===\ny", pids)["ok"]     # duplicate
    assert not jq_glue.split_session_output(
        "junk\n===PACK p01===\nx\n===PACK p02===\ny", pids)["ok"]


@pytest.fixture
def glue_sandbox(tmp_path):
    import shutil
    sandbox = tmp_path / "glue-sandbox"
    sandbox.mkdir()
    shutil.copyfile(os.path.join(REAL_OUT, "templates.json"),
                    sandbox / "templates.json")
    jq_glue.set_root(sandbox)
    yield jq_glue
    jq_glue.set_root(jq_glue.REAL_JQ_OUT_DIR)


def _r2_flags(arm, rep, pid):
    path = os.path.join(R2_OUT, "readings", arm, "rep%d" % rep,
                        "%s.json" % pid)
    return json.load(open(path, encoding="utf-8"))["flags"]


def _raw(arm, rep, pid):
    return jq_glue.marker_line(pid) + "\n" + json.dumps(
        {"flags": _r2_flags(arm, rep, pid)}, ensure_ascii=False)


def test_glue_ingest_pack_marker_and_reading(glue_sandbox):
    jq = glue_sandbox
    pids = ["p%02d" % i for i in range(1, 9)]
    raw = _raw("B", 1, "p01")
    res = jq.ingest_pack("p01", raw, "s-q-r1-b1", "Q", 1, 1, 1, pids)
    assert res["ok"], res["problems"]
    reading = json.load(open(os.path.join(
        str(jq.READINGS_ROOT), "Q", "rep1", "p01.json"), encoding="utf-8"))
    assert sorted(reading) == sorted(scoring_jq.READING_KEYS)
    assert reading["validation"]["passed"] is True
    assert reading["return_raw"] == raw
    assert len(reading["model_output"]) == len(_r2_flags("B", 1, "p01"))
    # wrong marker pid -> structural violation, fail-closed file written
    bad = jq.ingest_pack("p02", jq_glue.marker_line("p03") + "\n"
                         + json.dumps({"flags": _r2_flags("B", 1, "p02")}),
                         "s-q-r1-b1", "Q", 1, 1, 1, pids)
    assert not bad["ok"] and any("marker names pack" in p
                                 for p in bad["problems"])
    bad_reading = json.load(open(os.path.join(
        str(jq.READINGS_ROOT), "Q", "rep1", "p02.json"), encoding="utf-8"))
    assert bad_reading["validation"]["passed"] is False
    # no marker at all
    nomark = jq.ingest_pack("p03", json.dumps(
        {"flags": _r2_flags("B", 1, "p03")}), "s-q-r1-b1", "Q", 1, 1, 1, pids)
    assert not nomark["ok"] and any("does not begin with" in p
                                    for p in nomark["problems"])
    # append-only refusal on the same attempt
    again = jq.ingest_pack("p01", raw, "s-q-r1-b1", "Q", 1, 1, 1, pids)
    assert not again["ok"] and any("already exists" in p
                                   for p in again["problems"])
    # off-grid guards
    assert not jq.ingest_pack("p01", raw, "s", "X", 1, 1, 1, pids)["ok"]
    assert not jq.ingest_pack("p09", _raw("B", 1, "p09"), "s", "Q", 1, 1,
                              1, pids)["ok"]          # p09 not in batch 1


def test_glue_retry_supersede_naming(glue_sandbox):
    jq = glue_sandbox
    pids = ["p%02d" % i for i in range(1, 9)]
    good = _raw("B", 2, "p04")
    broken = jq_glue.marker_line("p04") + "\nnot json at all"
    r1 = jq.ingest_pack("p04", broken, "s-q-r2-b1", "Q", 2, 1, 1, pids)
    assert not r1["ok"]
    r2 = jq.ingest_pack("p04", good, "s-q-r2-b1", "Q", 2, 1, 2, pids)
    assert r2["ok"], r2["problems"]
    rd = os.path.join(str(jq.READINGS_ROOT), "Q", "rep2")
    assert os.path.isfile(os.path.join(rd, "p04.json"))
    assert os.path.isfile(os.path.join(rd, "p04-r1.json"))
    retry = json.load(open(os.path.join(rd, "p04-r1.json"), encoding="utf-8"))
    assert retry["validation"]["retry"] == 1
    assert retry["validation"]["first_attempt_errors"] == \
        json.load(open(os.path.join(rd, "p04.json"),
                       encoding="utf-8"))["validation"]["errors"]
    events = [json.loads(ln) for ln in open(
        str(jq.LEDGER_PATH), encoding="utf-8")]
    assert any(e["event"] == "schema-retry" and e["pid"] == "p04"
               for e in events)
    # a retry without its attempt-1 file is refused
    orphan = jq.ingest_pack("p05", _raw("B", 2, "p05"), "s-q-r2-b1", "Q", 2,
                            1, 2, pids)
    assert not orphan["ok"] and any("no attempt-1 reading" in p
                                    for p in orphan["problems"])


def test_glue_finalize_session_checks_and_ask(tmp_path, glue_sandbox):
    jq = glue_sandbox
    pids = ["p%02d" % i for i in range(1, 9)]
    for pid in pids:
        res = jq.ingest_pack(pid, _raw("A", 3, pid), "s-ctr-r3-b1", "CTR",
                             3, 1, 1, pids)
        assert res["ok"], res["problems"]
    fin = jq.finalize_session("s-ctr-r3-b1", "CTR", 3, 1)
    assert fin["ok"] and fin["n"] == 8
    assert len(fin["ask_sha256"]) == 64
    # ask rebuild is deterministic and byte-anchored to the frozen corpus
    again = jq._session_ask("s-ctr-r3-b1", "CTR", 3, 1)
    assert again["sha256"] == fin["ask_sha256"]
    tpl = json.load(open(os.path.join(REAL_OUT, "templates.json"),
                         encoding="utf-8"))
    asks = dict((pid, (sys_s, user)) for pid, sys_s, user
                in again["obj"]["asks"])
    assert asks["p01"][0] == tpl["ctr_system"]
    assert asks["p01"][1].startswith(tpl["ctr_head"])
    assert asks["p01"][1].endswith(tpl["ctr_tail"])
    # second finalize of the same session is refused (append-only)
    dup = jq.finalize_session("s-ctr-r3-b1", "CTR", 3, 1)
    assert not dup["ok"] and any("already has reading-append" in p
                                 for p in dup["problems"])
    # a session with a non-passed reading refuses to finalize its events
    broken = jq_glue.marker_line("p01") + "\nnope"
    assert not jq.ingest_pack("p01", broken, "s-q-r1-b1", "Q", 1, 1, 1,
                              pids)["ok"]
    for pid in pids[1:]:
        assert jq.ingest_pack(pid, _raw("B", 1, pid), "s-q-r1-b1", "Q", 1,
                              1, 1, pids)["ok"]
    fin2 = jq.finalize_session("s-q-r1-b1", "Q", 1, 1)
    assert not fin2["ok"] and any("not validation-passed" in p
                                  for p in fin2["problems"])
    # finish_and_score refuses before all 12 sessions are finalized
    fin3 = jq.finish_and_score()
    assert not fin3["ok"] and any("96" in p for p in fin3["problems"])


def test_glue_finalize_batch2_scoped_resolver(tmp_path, glue_sandbox):
    """Batch two resolves only its own pids in the shared arm/rep dir."""
    jq = glue_sandbox
    pids1 = ["p%02d" % i for i in range(1, 9)]
    pids2 = ["p%02d" % i for i in range(9, 17)]
    for pid in pids2:
        assert jq.ingest_pack(pid, _raw("B", 1, pid), "s-q-r1-b2", "Q", 1,
                              2, 1, pids2)["ok"]
    # batch one not ingested at all: batch-two finalize still works
    fin = jq.finalize_session("s-q-r1-b2", "Q", 1, 2)
    assert fin["ok"] and fin["n"] == 8
    assert not os.path.exists(os.path.join(str(jq.READINGS_ROOT), "Q",
                                           "rep1", "p01.json"))


def test_glue_self_test_full_chain(tmp_path):
    """The mandatory synthetic-session self-test as a pytest regression."""
    sandbox = tmp_path / "selftest-sandbox"

    def snapshot_real_tree():
        readings_dir = os.path.join(REAL_OUT, "readings")
        files = sorted(
            os.path.relpath(os.path.join(dirpath, name), readings_dir)
            for dirpath, _subdirs, names in os.walk(readings_dir)
            for name in names)
        ledger = open(os.path.join(REAL_OUT, "ledger.jsonl"),
                      encoding="utf-8").read()
        return files, ledger

    files_before, ledger_before = snapshot_real_tree()
    line = jq_glue.self_test(sandbox)
    assert line.startswith("SELFTEST PASS"), line
    # the real out tree stays untouched: the R1 readings directory has
    # existed since the 2026-10-11 E2 first reading, so non-interference
    # is witnessed by before/after identity (ledger bytes + file set),
    # not by absence
    assert snapshot_real_tree() == (files_before, ledger_before)
    # existence + frozen shape: 2 arms x 3 reps, one base reading per pid
    # (the 96 eight-key readings), retry files only as pNN-rK.json sidecars
    readings_dir = os.path.join(REAL_OUT, "readings")
    assert os.path.isdir(readings_dir)
    for arm in ("Q", "CTR"):
        arm_dir = os.path.join(readings_dir, arm)
        assert sorted(os.listdir(arm_dir)) == ["rep1", "rep2", "rep3"]
        for rep in ("rep1", "rep2", "rep3"):
            names = sorted(os.listdir(os.path.join(arm_dir, rep)))
            assert [n for n in names
                    if re.match(r"^p\d{2}\.json$", n)] == \
                sorted("%s.json" % pid for pid in PIDS)
            assert all(re.match(r"^p\d{2}(-r\d+)?\.json$", n)
                       for n in names)
    # append-only ledger: the freeze anchor stays the first event
    assert json.loads(ledger_before.strip().splitlines()[0])["event"] == \
        "freeze"
