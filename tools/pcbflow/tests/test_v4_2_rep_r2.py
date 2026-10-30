"""REP-R2 scoring_r2 tests: frozen r2 reproduction gate + synthetic world.

Synthetic small sample: 9 scenarios / 14 routes / 9 pids (p01-p09, both
batches occupied), 3 arms x 3 reps x 9 pids = 81 readings, verdicts
given as explicit per-(arm, rep) literal strings over a canonical route
order.  Expected confusions are (a) hand-computed literals for arm A
rep 1 and the pooled arm A, and (b) an independent in-test recount from
the literals for every other stratum (per rep / per session / per
scenario / paired diffs).  Retry ('-rN') resolution, fail-closed
validation, same-seed bootstrap reproducibility and byte-determinism of
the five stats files are all exercised on the synthetic world; the real
frozen gate values (out/v4.2-seat-r2/m1-stats.json) and the real REP-R2
run are pinned in the last two tests.

Run from the repo root (tools/pcbflow), PYTHONUTF8=1 per pytest.ini.
"""

import json
import os

import pytest

from pcbflow.v4_2_rep import scoring
from pcbflow.v4_2_rep import scoring_r2

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REAL_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r2")

# ------------------------------------------------------------ synthetic GT
ROUTES = {
    "s01": ["r1", "r2", "r3"],
    "s02": ["r1", "r2"],
    "s03": ["r1", "r2", "r3"],
    "s04": ["r1"],
    "s05": ["r1"],
    "s06": ["r1"],
    "s07": ["r1"],
    "s08": ["r1"],
    "s09": ["r1"],
}
# canonical route order for the SPEC strings below
ROUTE_ORDER = [("s%02d" % s, r) for s in range(1, 10) for r in ROUTES["s%02d" % s]]
IMPROVABLE = {  # per (sid, rid); 8 improvable of 14 routes
    ("s01", "r1"): True, ("s01", "r2"): False, ("s01", "r3"): True,
    ("s02", "r1"): False, ("s02", "r2"): True,
    ("s03", "r1"): False, ("s03", "r2"): False, ("s03", "r3"): True,
    ("s04", "r1"): True,
    ("s05", "r1"): False,
    ("s06", "r1"): True,
    ("s07", "r1"): False,
    ("s08", "r1"): True,
    ("s09", "r1"): True,
}
PID_SID = {"p01": "s03", "p02": "s01", "p03": "s02", "p04": "s04",
           "p05": "s05", "p06": "s06", "p07": "s07", "p08": "s08",
           "p09": "s09"}
PIDS = sorted(PID_SID)

# verdict literals over ROUTE_ORDER: f=flag_bad, n=no_flag, a=abstain
SPEC = {
    ("A", 1): "fnafnanfnanfaf",
    ("A", 2): "nfnafnafnfnana",
    ("A", 3): "afnfnafnafnafn",
    ("B", 1): "ffnfnaffnfnaff",
    ("B", 2): "nffnafnfnnfaff",
    ("B", 3): "affnanfnafnaff",
    ("C", 1): "aaaaaaafaaaaaa",
    ("C", 2): "nanaananananaa",
    ("C", 3): "fanaanafanafna",
}
VERDICT_OF = {"f": "flag_bad", "n": "no_flag", "a": "abstain"}

# retry bodies: (arm, rep, pid) -> list of (suffix, verdict-over-this-pid)
# base file bodies that would change the counts if wrongly consumed
RETRY_BASE = {
    ("A", 2, "p02"): [("p02.json", "nnn"), ("p02-r1.json", None)],
    ("C", 3, "p03"): [("p03.json", "ff"), ("p03-r1.json", "aa"),
                      ("p03-r2.json", None)],
}
# None = the SPEC verdicts (the retry body that must win)

# hand-computed anchors (route order + IMPROVABLE above):
#   A rep1 "fnafnanfnanfaf": tp=3 fp=2 fn=5 tn=4 abstain=4 n=14
#   A pooled:                tp=6 fp=8 fn=18 tn=10 abstain=12 n=42
A_REP1_LITERAL = {"tp": 3, "fp": 2, "fn": 5, "tn": 4, "abstain": 4,
                  "n_routes": 14}
A_POOLED_LITERAL = {"tp": 6, "fp": 8, "fn": 18, "tn": 10, "abstain": 12,
                    "n_routes": 42, "precision": 6.0 / 14.0,
                    "recall": 6.0 / 24.0, "abstention_rate": 12.0 / 42.0}


# ------------------------------------------------- independent recount (b)
def _spec_verdicts(arm, rep, pid):
    sid = PID_SID[pid]
    chars = SPEC[(arm, rep)]
    out = {}
    i = 0
    for s, r in ROUTE_ORDER:
        if s == sid:
            out[r] = VERDICT_OF[chars[i]]
        i += 1
    return out


def _confuse(verdicts, sid):
    """The r2 caliber applied by hand: flag_bad x improvable, abstain
    lands in fn (improvable) or tn (non-improvable)."""
    tp = fp = fn = tn = abstain = 0
    for rid, verdict in verdicts.items():
        improvable = IMPROVABLE[(sid, rid)]
        if verdict == "flag_bad":
            tp += 1 if improvable else 0
            fp += 0 if improvable else 1
        else:
            fn += 1 if improvable else 0
            tn += 0 if improvable else 1
            if verdict == "abstain":
                abstain += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "abstain": abstain,
            "n_routes": len(verdicts)}


def _sum(confs):
    return {k: sum(c[k] for c in confs) for k in
            ("tp", "fp", "fn", "tn", "abstain", "n_routes")}


def _expected_confusions():
    out = {}
    for arm in "ABC":
        out[arm] = {}
        for rep in (1, 2, 3):
            out[arm][rep] = {
                pid: _confuse(_spec_verdicts(arm, rep, pid), PID_SID[pid])
                for pid in PIDS}
    return out


EXPECTED_CONFS = _expected_confusions()


# ------------------------------------------------------ world construction
def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def _reading_obj(arm, rep, pid, verdicts):
    sid = PID_SID[pid]
    flags = []
    for rid in ROUTES[sid]:
        verdict = verdicts[rid]
        flags.append({
            "route_id": rid,
            "verdict": verdict,
            "reason_code": "detour_excess" if verdict == "flag_bad"
                           else "uncertain",
            "evidence": "ev %s %s %s %s" % (arm, rep, pid, rid),
        })
    return {"schema": "v4.2-rep-r2-reading/1", "arm": arm, "rep": rep,
            "pid": pid, "flags": flags}


def build_world(root):
    """Materialize the synthetic GT + meta + readings + gate fixtures.

    Returns (gt_path, meta_path, readings_root, r2_readings_dir,
    r2_stats_path).
    """
    root = str(root)
    os.makedirs(root, exist_ok=True)
    gt = {"gt_version": "synthetic-test/1", "scenarios": {}}
    for sid, rids in ROUTES.items():
        gt["scenarios"][sid] = {
            "n_routes": len(rids),
            "per_route": {rid: {"net_id": "n%s" % rid,
                                "improvable": IMPROVABLE[(sid, rid)]}
                          for rid in rids},
        }
    gt_path = os.path.join(root, "gt.json")
    _write_json(gt_path, gt)
    meta_path = os.path.join(root, "package-meta.json")
    _write_json(meta_path, {pid: {"sid": PID_SID[pid],
                                 "n_routes": len(ROUTES[PID_SID[pid]])}
                            for pid in PIDS})

    readings_root = os.path.join(root, "readings")
    for arm in "ABC":
        for rep in (1, 2, 3):
            directory = os.path.join(readings_root, arm, "rep%d" % rep)
            os.makedirs(directory)
            for pid in PIDS:
                key = (arm, rep, pid)
                if key in RETRY_BASE:
                    for fname, body in RETRY_BASE[key]:
                        verdicts = (_spec_verdicts(arm, rep, pid)
                                    if body is None else
                                    {rid: VERDICT_OF[ch] for rid, ch
                                     in zip(ROUTES[PID_SID[pid]], body)})
                        _write_json(os.path.join(directory, fname),
                                    _reading_obj(arm, rep, pid, verdicts))
                else:
                    _write_json(
                        os.path.join(directory, "%s.json" % pid),
                        _reading_obj(arm, rep, pid,
                                     _spec_verdicts(arm, rep, pid)))

    # gate fixtures: a mini r2 world (arm A rep1 verdicts) + its m1-stats
    r2_readings = os.path.join(root, "r2-m1-readings")
    os.makedirs(r2_readings)
    for pid in PIDS:
        _write_json(
            os.path.join(r2_readings, "%s.json" % pid),
            _reading_obj("A", 1, pid, _spec_verdicts("A", 1, pid)))
    r2_stats_path = os.path.join(root, "m1-stats.json")
    produced = scoring_r2._reproduce_r2_param(gt_path, meta_path, r2_readings)
    _write_json(r2_stats_path, produced)
    return gt_path, meta_path, readings_root, r2_readings, r2_stats_path


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return build_world(tmp_path_factory.mktemp("rep_r2_world"))


# --------------------------------------------- 1. frozen real reproduce gate
def test_reproduce_gate_real_frozen_values():
    gate = scoring_r2.reproduce_gate()
    assert gate["passed"] and gate["problems"] == []
    p = gate["produced"]
    assert (p["tp"], p["fp"], p["fn"], p["tn"]) == (20, 6, 13, 84)
    assert p["n_routes"] == 123 and p["abstention_rate"] == 0.0
    for key, want in (("precision", 0.7692307692307693),
                      ("recall", 0.6060606060606061),
                      ("random_baseline", 0.2682926829268293)):
        assert abs(p[key] - want) <= 1e-9, (key, p[key], want)


# ----------------------------------------------- 2. '-rN' retry resolution
def test_retry_resolution_takes_highest_rn(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    meta, route_impr, _sids = scoring_r2._gt_tables(gt_path, meta_path)
    confusions, chosen, superseded = scoring_r2.load_readings(
        readings_root, meta, route_impr)
    assert chosen["A"][2]["p02"] == "p02-r1.json"
    assert chosen["C"][3]["p03"] == "p03-r2.json"
    assert superseded["A"][2] == {"p02": ["p02.json"]}
    # sibling semantics: superseded listed in retry-number order (base=0 first)
    assert superseded["C"][3] == {"p03": ["p03.json", "p03-r1.json"]}
    # the retry body (SPEC) is what got consumed, not the base bodies
    assert confusions["A"][2]["p02"] == EXPECTED_CONFS["A"][2]["p02"]
    assert confusions["C"][3]["p03"] == EXPECTED_CONFS["C"][3]["p03"]
    # negative proof: the base bodies would have produced other counts
    base_a = _confuse({rid: "no_flag" for rid in ROUTES["s01"]}, "s01")
    assert base_a != EXPECTED_CONFS["A"][2]["p02"]
    base_c = _confuse({rid: "flag_bad" for rid in ROUTES["s02"]}, "s02")
    assert base_c != EXPECTED_CONFS["C"][3]["p03"]


def test_arm_stats_records_superseded_retries(tmp_path):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    out = tmp_path / "o"
    out.mkdir()
    result = scoring_r2.score_r2(
        gt_path=gt_path, package_meta_path=meta_path,
        readings_root=readings_root, out_dir=out,
        reproduce_kwargs={"gt_path": gt_path,
                          "package_meta_path": meta_path,
                          "readings_dir": r2_readings,
                          "r2_stats_path": r2_stats_path})
    a = result["arms"]["A"]
    assert a["reading_files"]["rep2"]["p02"] == "p02-r1.json"
    assert a["superseded_retries"]["rep2"] == {"p02": ["p02.json"]}
    c = result["arms"]["C"]
    assert c["superseded_retries"]["rep3"] == {"p03": ["p03.json",
                                                      "p03-r1.json"]}


# ------------------------------------------------ 3. confusion-caliber anchors
def test_confusion_caliber_hand_literals(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    meta, route_impr, _sids = scoring_r2._gt_tables(gt_path, meta_path)
    confusions, _chosen, _sup = scoring_r2.load_readings(
        readings_root, meta, route_impr)
    rep1 = scoring_r2._sum_confs([confusions["A"][1][pid] for pid in PIDS])
    assert {k: rep1[k] for k in A_REP1_LITERAL} == A_REP1_LITERAL
    pooled = scoring_r2._sum_confs([confusions["A"][rep][pid]
                                    for rep in (1, 2, 3) for pid in PIDS])
    row = scoring_r2._row(pooled)
    for k, want in A_POOLED_LITERAL.items():
        assert row[k] == want, (k, row[k], want)
    # caliber identities + abstain routing (fn/tn, never tp/fp)
    assert row["improvable"] == row["tp"] + row["fn"] == 24  # 8 routes x 3
    assert row["flag_bad"] == row["tp"] + row["fp"] == 14
    # abstained improvable sits in fn, abstained non-improvable in tn:
    # A rep1 (s01,r3)=abstain+improvable and (s03,r1)=abstain+non-improvable
    a1 = scoring_r2._sum_confs([confusions["A"][1][pid] for pid in PIDS])
    assert a1["fn"] >= 2 and a1["tn"] >= 2 and a1["abstain"] == 4


def test_expected_pools_match_independent_recount(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    result = scoring_r2.score_r2(
        gt_path=gt_path, package_meta_path=meta_path,
        readings_root=readings_root, out_dir=out,
        reproduce_kwargs={"gt_path": gt_path,
                          "package_meta_path": meta_path,
                          "readings_dir": r2_readings,
                          "r2_stats_path": r2_stats_path})
    for arm in "ABC":
        want = _sum([EXPECTED_CONFS[arm][rep][pid]
                     for rep in (1, 2, 3) for pid in PIDS])
        got = result["arms"][arm]
        for k, v in want.items():
            assert got[k] == v, (arm, k, got[k], v)
        assert got["precision"] == got["tp"] / (got["tp"] + got["fp"])
        assert got["recall"] == got["tp"] / (got["tp"] + got["fn"])
        assert got["abstention_rate"] == got["abstain"] / got["n_routes"]
        assert got["random_baseline"] == 24.0 / 42.0
        # per-rep stratum equals the independent recount
        for rep in (1, 2, 3):
            w = _sum([EXPECTED_CONFS[arm][rep][pid] for pid in PIDS])
            g = got["per_rep"]["rep%d" % rep]
            for k, v in w.items():
                assert g[k] == v, (arm, rep, k)
        # per-session stratum (batch one = p01-p08, batch two = p09-p16)
        for rep in (1, 2, 3):
            for batch, pids in ((1, PIDS[:8]), (2, PIDS[8:])):
                w = _sum([EXPECTED_CONFS[arm][rep][pid] for pid in pids])
                g = got["per_session"]["rep%d-batch%d" % (rep, batch)]
                for k, v in w.items():
                    assert g[k] == v, (arm, rep, batch, k)
        # per-scenario stratum = that scenario's readings pooled over reps
        for sid in sorted(ROUTES):
            pids_of = [pid for pid in PIDS if PID_SID[pid] == sid]
            w = _sum([EXPECTED_CONFS[arm][rep][pid]
                      for rep in (1, 2, 3) for pid in pids_of])
            g = got["per_scenario"][sid]
            for k, v in w.items():
                assert g[k] == v, (arm, sid, k)
            assert g["n_routes"] == 3 * len(ROUTES[sid])
    # session flat table: exact columns, order, batch split, sums
    sess = result["sessions"]["sessions"]
    assert len(sess) == 18
    assert [("%s%d%d" % (r["arm"], r["rep"], r["batch"])) for r in sess] == \
        ["%s%d%d" % (arm, rep, batch) for arm in "ABC" for rep in (1, 2, 3)
         for batch in (1, 2)]
    for r in sess:
        assert set(r) == {"arm", "rep", "batch", "tp", "fp", "fn", "tn",
                          "recall", "precision", "abstain_rate"}
    for arm in "ABC":
        rows = [r for r in sess if r["arm"] == arm]
        assert {k: sum(r[k] for r in rows) for k in ("tp", "fp", "fn", "tn")} \
            == {k: result["arms"][arm][k] for k in ("tp", "fp", "fn", "tn")}
        for rep in (1, 2, 3):
            b1 = [r for r in rows if r["rep"] == rep and r["batch"] == 1][0]
            b2 = [r for r in rows if r["rep"] == rep and r["batch"] == 2][0]
            assert b1["tp"] + b2["tp"] == result["arms"][arm][
                "per_rep"]["rep%d" % rep]["tp"]
            assert b1["tn"] + b2["tn"] == result["arms"][arm][
                "per_rep"]["rep%d" % rep]["tn"]


def test_stratified_counts_add_up(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    result = scoring_r2.score_r2(
        gt_path=gt_path, package_meta_path=meta_path,
        readings_root=readings_root, out_dir=out,
        reproduce_kwargs={"gt_path": gt_path,
                          "package_meta_path": meta_path,
                          "readings_dir": r2_readings,
                          "r2_stats_path": r2_stats_path})
    for arm in "ABC":
        s = result["arms"][arm]
        keys = ("tp", "fp", "fn", "tn", "abstain", "n_routes")
        assert len(s["per_rep"]) == 3 and len(s["per_session"]) == 6
        assert len(s["per_scenario"]) == 9
        for part in ("per_rep", "per_session", "per_scenario"):
            tot = _sum(list(s[part].values()))
            assert {k: tot[k] for k in keys} == \
                {k: s[k] for k in keys}, (arm, part)
        assert s["n_readings"] == 27 and s["n_routes"] == 42


# ------------------------------------------------------- 4. bootstrap bits
def _cluster_rows_from_world(gt_path, meta_path, readings_root):
    meta, route_impr, sids = scoring_r2._gt_tables(gt_path, meta_path)
    confusions, _c, _s = scoring_r2.load_readings(readings_root, meta,
                                                  route_impr)
    return scoring_r2._cluster_rows(confusions, meta, sids), sids


def test_bootstrap_same_seed_reproducible(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    rows, _sids = _cluster_rows_from_world(gt_path, meta_path, readings_root)
    ci1 = scoring_r2._bootstrap_three_arm(rows, seed=20261001, n_boot=500)
    ci2 = scoring_r2._bootstrap_three_arm(rows, seed=20261001, n_boot=500)
    assert ci1 == ci2
    ci3 = scoring_r2._bootstrap_three_arm(rows, seed=1, n_boot=500)
    assert ci3 != ci1  # fixed seeds: deterministic, never flaky
    for key, entry in ci1.items():
        assert entry["n_defined"] + entry["n_undefined"] == 500, key
        if entry["n_defined"]:
            assert entry["low"] <= entry["high"], key
    # the seeded pipeline CI at B=10000 is fixed too
    ci_full = scoring_r2._bootstrap_three_arm(rows, seed=20261001)
    assert ci_full["recall_diff_B-A"]["n_defined"] == 10000


def test_bootstrap_clusters_pool_three_reps(world):
    # cluster counts are per-scenario sums across the 3 reps (PREREG 8.1)
    gt_path, meta_path, readings_root, _rr, _rs = world
    rows, sids = _cluster_rows_from_world(gt_path, meta_path, readings_root)
    for arm in "ABC":
        for sid, row in zip(sids, rows[arm]):
            want = _sum([EXPECTED_CONFS[arm][rep][pid]
                         for rep in (1, 2, 3) for pid in PIDS
                         if PID_SID[pid] == sid])
            assert {k: row[k] for k in want} == want, (arm, sid)


# ------------------------------------------------ 5. gate wiring fail-closed
def test_score_r2_gate_pass_and_fail(tmp_path):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    out = tmp_path / "out"
    out.mkdir()
    kw = {"gt_path": gt_path, "package_meta_path": meta_path,
          "readings_dir": r2_readings, "r2_stats_path": r2_stats_path}
    result = scoring_r2.score_r2(gt_path=gt_path,
                                 package_meta_path=meta_path,
                                 readings_root=readings_root, out_dir=out,
                                 reproduce_kwargs=kw)
    assert result["reproduce"]["passed"] is True

    tampered = json.load(open(r2_stats_path, encoding="utf-8"))
    tampered["tp"] += 1
    _write_json(r2_stats_path, tampered)
    with pytest.raises(RuntimeError, match="reproduction gate FAILED"):
        scoring_r2.score_r2(gt_path=gt_path, package_meta_path=meta_path,
                            readings_root=readings_root, out_dir=out,
                            reproduce_kwargs=kw)


# ---------------------------------------------- 6. fail-closed validation
def _mutate_and_expect_raise(tmp_path, mutate):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    out = tmp_path / "out"
    out.mkdir()
    mutate(readings_root)
    kw = {"gt_path": gt_path, "package_meta_path": meta_path,
          "readings_dir": r2_readings, "r2_stats_path": r2_stats_path}
    with pytest.raises(RuntimeError):
        scoring_r2.score_r2(gt_path=gt_path, package_meta_path=meta_path,
                            readings_root=readings_root, out_dir=out,
                            reproduce_kwargs=kw)


def test_fail_closed_invalid_verdict(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p04.json")
        data = json.load(open(path, encoding="utf-8"))
        data["flags"][0]["verdict"] = "maybe"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_arm_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "A", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["arm"] = "C"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_rep_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "A", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["rep"] = 2
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_schema_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "A", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["schema"] = "v4.2-rep-r1-reading/1"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_missing_reading(tmp_path):
    def mutate(readings_root):
        os.remove(os.path.join(readings_root, "C", "rep2", "p09.json"))
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_duplicate_route_entry(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep2", "p05.json")
        data = json.load(open(path, encoding="utf-8"))
        data["flags"] = data["flags"] + [dict(data["flags"][0])]
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


# ------------------------------------------------ 7. end-to-end determinism
def test_score_r2_deterministic_bytes_and_pairing(tmp_path):
    outs = []
    for tag in ("o1", "o2"):
        w = tmp_path / ("w_" + tag)
        w.mkdir()
        out = tmp_path / tag
        out.mkdir()
        gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
            build_world(w)
        scoring_r2.score_r2(
            gt_path=gt_path, package_meta_path=meta_path,
            readings_root=readings_root, out_dir=out,
            reproduce_kwargs={"gt_path": gt_path,
                              "package_meta_path": meta_path,
                              "readings_dir": r2_readings,
                              "r2_stats_path": r2_stats_path})
        outs.append({p.name: p.read_bytes()
                     for p in sorted(out.glob("*-stats.json"))})
    assert sorted(outs[0]) == ["arm-a-stats.json", "arm-b-stats.json",
                               "arm-c-stats.json", "paired-stats.json",
                               "session-stats.json"]
    assert outs[0] == outs[1]  # byte-deterministic across fresh worlds
    paired = json.loads(outs[0]["paired-stats.json"].decode("utf-8"))
    comp = paired["comparisons"]
    assert comp["B-A"]["role"] == "primary"
    assert comp["C-A"]["role"] == "secondary"
    assert comp["B-C"]["role"] == "secondary"
    recalls = {arm: paired["pooled"]["recall"][arm] for arm in "ABC"}
    for name, (hi, lo) in (("B-A", ("B", "A")), ("C-A", ("C", "A")),
                           ("B-C", ("B", "C"))):
        assert comp[name]["recall_diff"] == recalls[hi] - recalls[lo]
        # rep-level paired diffs: 3 raw points, equal to per-rep recount
        for rep in (1, 2, 3):
            w_hi = _sum([EXPECTED_CONFS[hi][rep][pid] for pid in PIDS])
            w_lo = _sum([EXPECTED_CONFS[lo][rep][pid] for pid in PIDS])
            assert comp[name]["rep_level_recall_diff"]["rep%d" % rep] == (
                w_hi["tp"] / (w_hi["tp"] + w_hi["fn"])
                - w_lo["tp"] / (w_lo["tp"] + w_lo["fn"]))
    ci = comp["B-A"]["bootstrap_ci95"]["recall_diff"]
    assert ci["n_defined"] == 10000 and ci["n_undefined"] == 0
    assert ci["low"] <= comp["B-A"]["recall_diff"] <= ci["high"]
    # r2 band is a report-only reference with no gate
    band = paired["r2_band_reference"]
    assert "no gate" in band["note"]
    for arm in "ABC":
        entry = band["arms"][arm]
        assert entry["precision_min"] == max(2.0 * (24.0 / 42.0), 0.4)
        assert entry["abstention_max"] == 0.5
        assert isinstance(entry["passes_band"], bool)


# ------------------------------------------- 8. real frozen data end-to-end
def test_real_run_all_summary_and_frozen_numbers(capsys):
    result = scoring_r2.run_all()
    for arm, want in (("A", (1, 1, 98, 269)), ("B", (70, 43, 29, 227)),
                      ("C", (0, 8, 99, 262))):
        s = result["arms"][arm]
        assert (s["tp"], s["fp"], s["fn"], s["tn"]) == want, arm
        assert s["n_routes"] == 369 and s["improvable"] == 99
        assert s["abstention_rate"] == s["abstain"] / 369
    assert result["arms"]["A"]["recall"] == 1.0 / 99.0
    assert result["arms"]["B"]["recall"] == 70.0 / 99.0
    assert result["arms"]["C"]["abstain"] == 331
    comp = result["paired"]["comparisons"]["B-A"]
    assert comp["recall_diff"] == 70.0 / 99.0 - 1.0 / 99.0
    assert comp["rep_level_recall_diff"] == {
        "rep1": 0.6666666666666667, "rep2": 0.48484848484848486,
        "rep3": 0.9393939393939394}
    assert comp["bootstrap_ci95"]["recall_diff"]["low"] == 0.5362318840579711
    assert comp["bootstrap_ci95"]["recall_diff"]["high"] == 0.8416666666666667
    lines = capsys.readouterr().out.strip().splitlines()
    summary = json.loads(lines[-1])
    assert set(summary) == {"n_readings", "arms", "primary"}
    assert summary["n_readings"] == 144
    assert summary["arms"] == {"A": {"n_readings": 48},
                               "B": {"n_readings": 48},
                               "C": {"n_readings": 48}}
    assert summary["primary"]["recall_diff"] == 70.0 / 99.0 - 1.0 / 99.0
    assert summary["primary"]["ci_low"] == 0.5362318840579711
    assert summary["primary"]["ci_high"] == 0.8416666666666667
    # five stats files exist in out/v4.2-rep-r2/ after the run
    for name in ("arm-a-stats.json", "arm-b-stats.json", "arm-c-stats.json",
                 "session-stats.json", "paired-stats.json"):
        assert os.path.isfile(os.path.join(REAL_OUT, name)), name


# ---------------------------- 9. C-derivation independent recomputation gate
# PACK-SPEC-REP-R2-C §6.2 promise ("test_v4_2_rep_r2.py 内置同规则独立复算并
# 对盘上 packs-c/ 逐 pid 断言 §4 全部门"), found missing by LEAD-REVIEW 2026-10-02
# (report D-R2-4) and backfilled by the 2026-10-03 fix batch (user ruling R53).
# Additive only: no existing test is modified.
import re as _re

from pcbflow.v4_2.inspector import _IDENTITY_RE, _JUDGE_SUFFIX

R1_REAL_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r1")

_GEOM_LINE_RE = _re.compile(r'^\s*<path id="geom-([^"]+)"')
_STRIP_RE = _re.compile(r"^[ \t]*<path id=\"geom-")

# frozen reference table from PACK-SPEC-REP-R2-C §3: pid -> (n_routes, C-user bytes)
_C_FROZEN = {
    "p01": (8, 11270), "p02": (9, 11814), "p03": (4, 8504),
    "p04": (7, 10573), "p05": (8, 11117), "p06": (7, 10577),
    "p07": (10, 12473), "p08": (7, 10401), "p09": (8, 11117),
    "p10": (10, 12474), "p11": (7, 10573), "p12": (10, 12474),
    "p13": (4, 8503), "p14": (6, 9707), "p15": (10, 12474),
    "p16": (8, 11117),
}


def _rederive_c(au: str) -> str:
    return "\n".join(l for l in au.split("\n") if not _STRIP_RE.match(l))


def test_c_frozen_table_totals():
    assert sum(v[0] for v in _C_FROZEN.values()) == 123
    assert min(v[1] for v in _C_FROZEN.values()) == 8503
    assert max(v[1] for v in _C_FROZEN.values()) == 12474


@pytest.mark.parametrize("pid", sorted(_C_FROZEN))
def test_c_pack_all_spec4_gates(pid):
    n_frozen, bytes_frozen = _C_FROZEN[pid]
    a = json.load(open(os.path.join(R1_REAL_OUT, "tasks-a", pid + ".json"),
                       encoding="utf-8"))
    c = json.load(open(os.path.join(REAL_OUT, "packs-c", pid + ".json"),
                       encoding="utf-8"))
    au, cu = a["user"], c["user"]
    # gate 1: key set / pid passthrough / system byte-equal to A
    assert sorted(c.keys()) == ["pid", "system", "user"]
    assert c["pid"] == pid
    assert c["system"] == a["system"]
    # gate 2: removed-line count == n_routes (and == frozen table value)
    aroutes = set(_re.findall(r'data-route-id="([^"]+)"', au))
    derived = _rederive_c(au)
    removed = len(au.split("\n")) - len(derived.split("\n"))
    assert removed == len(aroutes) == n_frozen
    # gate 3: C route set == A route set
    assert set(_re.findall(r'data-route-id="([^"]+)"', cu)) == aroutes
    # gate 4: removed geom-id set == route set (bijection)
    geom_ids = {m.group(1) for l in au.split("\n")
                if (m := _GEOM_LINE_RE.match(l))}
    assert geom_ids == aroutes
    # gate 5: zero residue of path geometry
    assert "<path" not in cu
    assert ' d="M' not in cu
    # gate 6: judge suffix intact on both A and C (imported constant)
    assert au.rstrip("\n").endswith(_JUDGE_SUFFIX)
    assert cu.rstrip("\n").endswith(_JUDGE_SUFFIX)
    # gate 7: byte fidelity -- C is exactly A minus the geom lines
    assert cu == derived
    # gate 8: blindness regex zero-hit on C user and system
    assert not _IDENTITY_RE.search(cu)
    assert not _IDENTITY_RE.search(c["system"])
    # gate 9: frozen byte-table gate (exact, no tolerance)
    assert len(cu.encode("utf-8")) == bytes_frozen
    # gate 10: derivation determinism (same input, same bytes)
    assert _rederive_c(au) == derived


def test_c_pack_totals_and_strip_purity():
    total_removed = 0
    for pid in sorted(_C_FROZEN):
        a = json.load(open(os.path.join(R1_REAL_OUT, "tasks-a", pid + ".json"),
                           encoding="utf-8"))
        lines = a["user"].split("\n")
        geom = [l for l in lines if _GEOM_LINE_RE.match(l)]
        non_geom_matching = [l for l in geom if not _STRIP_RE.match(l)]
        # strip regex covers every geom line: no geom line escapes removal
        assert non_geom_matching == [], pid
        total_removed += len(geom)
    assert total_removed == 123
