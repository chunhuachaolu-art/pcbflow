"""REP-R3 scoring_r3 tests: frozen r2 reproduction gate + synthetic world.

Synthetic small sample: 9 scenarios / 14 routes / 9 pids (p01-p09, both
batches occupied), 3 arms x 3 reps x 9 pids = 81 eight-key
(v4.2-rep-r3-reading/1) readings, verdicts given as explicit per-(arm,
rep) literal strings over a canonical route order.  Expected confusions
are (a) hand-computed literals for arm B rep 1 and the pooled arm B, and
(b) an independent in-test recount from the literals for every other
stratum (per rep / per session / per scenario / paired diffs).  Retry
('-rN') resolution, abstain routing into fn/tn, same-seed bootstrap
reproducibility, the three-comparison set with the CP abstention diff,
fail-closed validation and byte-determinism of the five stats files are
all exercised on the synthetic world; the real frozen gate values
(out/v4.2-seat-r2/m1-stats.json) and the real REP-R3 run (independent
recount over out/v4.2-rep-r3/readings/) are pinned in the last tests.

Run from the repo root (tools/pcbflow), PYTHONUTF8=1 per pytest.ini.
"""

import json
import os

import pytest

from pcbflow.v4_2_rep import scoring
from pcbflow.v4_2_rep import scoring_r2
from pcbflow.v4_2_rep import scoring_r3

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REAL_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r3")

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
    ("B", 1): "fnafnanfnanfaf",
    ("B", 2): "nfnafnafnfnana",
    ("B", 3): "afnfnafnafnafn",
    ("BP", 1): "ffnfnaffnfnaff",
    ("BP", 2): "nffnafnfnnfaff",
    ("BP", 3): "affnanfnafnaff",
    ("CP", 1): "aaaaaaafaaaaaa",
    ("CP", 2): "nanaananananaa",
    ("CP", 3): "fanaanafanafna",
}
VERDICT_OF = {"f": "flag_bad", "n": "no_flag", "a": "abstain"}

# retry bodies: (arm, rep, pid) -> list of (suffix, verdict-over-this-pid)
# base file bodies that would change the counts if wrongly consumed
RETRY_BASE = {
    ("B", 2, "p02"): [("p02.json", "nnn"), ("p02-r1.json", None)],
    ("CP", 3, "p03"): [("p03.json", "ff"), ("p03-r1.json", "aa"),
                       ("p03-r2.json", None)],
}
# None = the SPEC verdicts (the retry body that must win)

# hand-computed anchors (route order + IMPROVABLE above):
#   B rep1 "fnafnanfnanfaf": tp=3 fp=2 fn=5 tn=4 abstain=4 n=14
#   B pooled:                tp=6 fp=8 fn=18 tn=10 abstain=12 n=42
B_REP1_LITERAL = {"tp": 3, "fp": 2, "fn": 5, "tn": 4, "abstain": 4,
                  "n_routes": 14}
B_POOLED_LITERAL = {"tp": 6, "fp": 8, "fn": 18, "tn": 10, "abstain": 12,
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
    for arm in scoring_r3.ARMS:
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


def _flags_list(arm, rep, pid, verdicts):
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
    return flags


def _reading_obj(arm, rep, pid, verdicts, retry=0):
    """Eight-key v4.2-rep-r3-reading/1 (judgment = model_output)."""
    return {
        "schema": "v4.2-rep-r3-reading/1",
        "arm": arm,
        "pid": pid,
        "rep": rep,
        "model_output": _flags_list(arm, rep, pid, verdicts),
        "return_raw": "```json\n...synthetic...\n```",
        "ts": "2026-10-03T00:00:00",
        "validation": {"errors": [], "first_attempt_errors": [],
                       "passed": True, "retry": retry},
    }


def _r2_reading_obj(arm, rep, pid, verdicts):
    """r1/r2-shape gate fixture (four-key reading, judgment = flags)."""
    return {"schema": "v4.2-rep-r2-reading/1", "arm": arm, "rep": rep,
            "pid": pid, "flags": _flags_list(arm, rep, pid, verdicts)}


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
    for arm in scoring_r3.ARMS:
        for rep in (1, 2, 3):
            directory = os.path.join(readings_root, arm, "rep%d" % rep)
            os.makedirs(directory)
            for pid in PIDS:
                key = (arm, rep, pid)
                if key in RETRY_BASE:
                    for i, (fname, body) in enumerate(RETRY_BASE[key]):
                        verdicts = (_spec_verdicts(arm, rep, pid)
                                    if body is None else
                                    {rid: VERDICT_OF[ch] for rid, ch
                                     in zip(ROUTES[PID_SID[pid]], body)})
                        _write_json(os.path.join(directory, fname),
                                    _reading_obj(arm, rep, pid, verdicts,
                                                 retry=i))
                else:
                    _write_json(
                        os.path.join(directory, "%s.json" % pid),
                        _reading_obj(arm, rep, pid,
                                     _spec_verdicts(arm, rep, pid)))

    # gate fixtures: a mini r2 world (r1/r2-shape readings) + its m1-stats
    r2_readings = os.path.join(root, "r2-m1-readings")
    os.makedirs(r2_readings)
    for pid in PIDS:
        _write_json(
            os.path.join(r2_readings, "%s.json" % pid),
            _r2_reading_obj("B", 1, pid, _spec_verdicts("B", 1, pid)))
    r2_stats_path = os.path.join(root, "m1-stats.json")
    produced = scoring_r2._reproduce_r2_param(gt_path, meta_path, r2_readings)
    _write_json(r2_stats_path, produced)
    return gt_path, meta_path, readings_root, r2_readings, r2_stats_path


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return build_world(tmp_path_factory.mktemp("rep_r3_world"))


def _score(tmp_path, world_tuple, **extra):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        world_tuple
    out = tmp_path / "out"
    out.mkdir()
    return scoring_r3.score_r3(
        gt_path=gt_path, package_meta_path=meta_path,
        readings_root=readings_root, out_dir=out,
        reproduce_kwargs={"gt_path": gt_path,
                          "package_meta_path": meta_path,
                          "readings_dir": r2_readings,
                          "r2_stats_path": r2_stats_path}), out


# --------------------------------------------- 1. frozen real reproduce gate
def test_reproduce_gate_real_frozen_values():
    # goes through pcbflow.v4_2_rep.scoring.reproduce_r2() itself
    gate = scoring_r3.reproduce_gate()
    assert gate["passed"] and gate["problems"] == []
    p = gate["produced"]
    assert (p["tp"], p["fp"], p["fn"], p["tn"]) == (20, 6, 13, 84)
    assert p["n_routes"] == 123 and p["abstention_rate"] == 0.0
    for key, want in (("precision", 0.7692307692307693),
                      ("recall", 0.6060606060606061),
                      ("random_baseline", 0.2682926829268293)):
        assert abs(p[key] - want) <= 1e-9, (key, p[key], want)
    assert p["gate"]["passed"] is True


# --------------------------------- 2. eight-key parsing + '-rN' resolution
def test_eight_key_parsing_and_retry_resolution(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    meta, route_impr, _sids = scoring_r3._gt_tables(gt_path, meta_path)
    confusions, chosen, superseded = scoring_r3.load_readings(
        readings_root, meta, route_impr)
    assert chosen["B"][2]["p02"] == "p02-r1.json"
    assert chosen["CP"][3]["p03"] == "p03-r2.json"
    assert superseded["B"][2] == {"p02": ["p02.json"]}
    # sibling semantics: superseded listed in retry-number order (base=0 first)
    assert superseded["CP"][3] == {"p03": ["p03.json", "p03-r1.json"]}
    # the retry body (SPEC) is what got consumed, not the base bodies
    assert confusions["B"][2]["p02"] == EXPECTED_CONFS["B"][2]["p02"]
    assert confusions["CP"][3]["p03"] == EXPECTED_CONFS["CP"][3]["p03"]
    # negative proof: the base bodies would have produced other counts
    base_b = _confuse({rid: "no_flag" for rid in ROUTES["s01"]}, "s01")
    assert base_b != EXPECTED_CONFS["B"][2]["p02"]
    base_c = _confuse({rid: "flag_bad" for rid in ROUTES["s02"]}, "s02")
    assert base_c != EXPECTED_CONFS["CP"][3]["p03"]
    # every consumed confusion matches the independent recount
    for arm in scoring_r3.ARMS:
        for rep in (1, 2, 3):
            for pid in PIDS:
                assert confusions[arm][rep][pid] == \
                    EXPECTED_CONFS[arm][rep][pid], (arm, rep, pid)


def test_arm_stats_records_superseded_retries(tmp_path):
    result, _out = _score(tmp_path, build_world(tmp_path / "w"))
    b = result["arms"]["B"]
    assert b["reading_files"]["rep2"]["p02"] == "p02-r1.json"
    assert b["superseded_retries"]["rep2"] == {"p02": ["p02.json"]}
    cp = result["arms"]["CP"]
    assert cp["superseded_retries"]["rep3"] == {"p03": ["p03.json",
                                                        "p03-r1.json"]}
    # the real-world retry shape (base file absent, lone -r1) also resolves
    assert "superseded_retries" not in result["arms"]["BP"]


# ------------------------------------------------ 3. confusion-caliber anchors
def test_confusion_caliber_hand_literals(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    meta, route_impr, _sids = scoring_r3._gt_tables(gt_path, meta_path)
    confusions, _chosen, _sup = scoring_r3.load_readings(
        readings_root, meta, route_impr)
    rep1 = scoring_r3._sum_confs([confusions["B"][1][pid] for pid in PIDS])
    assert {k: rep1[k] for k in B_REP1_LITERAL} == B_REP1_LITERAL
    pooled = scoring_r3._sum_confs([confusions["B"][rep][pid]
                                    for rep in (1, 2, 3) for pid in PIDS])
    row = scoring_r3._row(pooled)
    for k, want in B_POOLED_LITERAL.items():
        assert row[k] == want, (k, row[k], want)
    # caliber identities + abstain routing (fn/tn, never tp/fp)
    assert row["improvable"] == row["tp"] + row["fn"] == 24  # 8 routes x 3
    assert row["flag_bad"] == row["tp"] + row["fp"] == 14
    # abstained improvable sits in fn, abstained non-improvable in tn:
    # B rep1 (s01,r3)=abstain+improvable and (s03,r1)=abstain+non-improvable
    b1 = scoring_r3._sum_confs([confusions["B"][1][pid] for pid in PIDS])
    assert b1["fn"] >= 2 and b1["tn"] >= 2 and b1["abstain"] == 4
    # explicit abstain classification from the raw verdicts:
    # CP rep1 is all-abstain but one flag: every abstained improvable -> fn,
    # every abstained non-improvable -> tn; tp/fp come only from the flag
    cp1 = scoring_r3._sum_confs([confusions["CP"][1][pid] for pid in PIDS])
    assert cp1["abstain"] == 13 and cp1["n_routes"] == 14
    assert cp1["fn"] + cp1["tn"] == 13
    assert cp1["tp"] + cp1["fp"] == 1


def test_expected_pools_match_independent_recount(tmp_path):
    result, _out = _score(tmp_path, build_world(tmp_path / "w"))
    for arm in scoring_r3.ARMS:
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
        ["%s%d%d" % (arm, rep, batch)
         for arm in scoring_r3.ARMS for rep in (1, 2, 3) for batch in (1, 2)]
    for r in sess:
        assert set(r) == {"arm", "rep", "batch", "tp", "fp", "fn", "tn",
                          "recall", "precision", "abstain_rate"}
    for arm in scoring_r3.ARMS:
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
    result, _out = _score(tmp_path, build_world(tmp_path / "w"))
    for arm in scoring_r3.ARMS:
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
    meta, route_impr, sids = scoring_r3._gt_tables(gt_path, meta_path)
    confusions, _c, _s = scoring_r3.load_readings(readings_root, meta,
                                                  route_impr)
    return scoring_r3._cluster_rows(confusions, meta, sids), sids


def test_bootstrap_same_seed_reproducible(world):
    gt_path, meta_path, readings_root, _rr, _rs = world
    rows, _sids = _cluster_rows_from_world(gt_path, meta_path, readings_root)
    ci1 = scoring_r3._bootstrap_three_arm(rows, seed=20261003, n_boot=500)
    ci2 = scoring_r3._bootstrap_three_arm(rows, seed=20261003, n_boot=500)
    assert ci1 == ci2
    ci3 = scoring_r3._bootstrap_three_arm(rows, seed=1, n_boot=500)
    assert ci3 != ci1  # fixed seeds: deterministic, never flaky
    for key, entry in ci1.items():
        assert entry["n_defined"] + entry["n_undefined"] == 500, key
        if entry["n_defined"]:
            assert entry["low"] <= entry["high"], key
    # abstention never undefined (n* > 0 in every replicate)
    assert ci1["abstention_CP"]["n_undefined"] == 0
    assert ci1["abstention_diff_CP-B"]["n_undefined"] == 0
    # the seeded pipeline CI at B=10000 is fixed too
    ci_full = scoring_r3._bootstrap_three_arm(rows, seed=20261003)
    assert ci_full["recall_diff_BP-B"]["n_defined"] == 10000


def test_bootstrap_clusters_pool_three_reps(world):
    # cluster counts are per-scenario sums across the 3 reps (PREREG 8.1)
    gt_path, meta_path, readings_root, _rr, _rs = world
    rows, sids = _cluster_rows_from_world(gt_path, meta_path, readings_root)
    for arm in scoring_r3.ARMS:
        for sid, row in zip(sids, rows[arm]):
            want = _sum([EXPECTED_CONFS[arm][rep][pid]
                         for rep in (1, 2, 3) for pid in PIDS
                         if PID_SID[pid] == sid])
            assert {k: row[k] for k in want} == want, (arm, sid)


# ------------------------------ 5. three comparisons + CP abstention diff
def test_three_comparisons_and_abstention_diff(tmp_path):
    result, _out = _score(tmp_path, build_world(tmp_path / "w"))
    paired = result["paired"]
    comp = paired["comparisons"]
    assert list(comp) == ["BP-B", "CP-B", "CP-BP"]  # primary first
    assert comp["BP-B"]["role"] == "primary"
    assert comp["CP-B"]["role"] == "secondary"
    assert comp["CP-BP"]["role"] == "secondary"
    recalls = {arm: paired["pooled"]["recall"][arm]
               for arm in scoring_r3.ARMS}
    abst = {arm: paired["pooled"]["abstention_rate"][arm]
            for arm in scoring_r3.ARMS}
    prec = {arm: paired["pooled"]["precision"][arm]
            for arm in scoring_r3.ARMS}
    # primary read: recall(BP) - recall(B)
    assert comp["BP-B"]["recall_diff"] == recalls["BP"] - recalls["B"]
    assert comp["BP-B"]["recall_diff"] == 0.5 - 0.25
    # secondary reads: abstention(CP)-abstention(B), recall(CP)-recall(B)
    assert comp["CP-B"]["abstention_diff"] == abst["CP"] - abst["B"]
    assert comp["CP-B"]["abstention_diff"] == 28.0 / 42.0 - 12.0 / 42.0
    assert comp["CP-B"]["recall_diff"] == recalls["CP"] - recalls["B"]
    # precision paired diffs co-reported over the same comparison set
    for name, (hi, lo) in (("BP-B", ("BP", "B")), ("CP-B", ("CP", "B")),
                           ("CP-BP", ("CP", "BP"))):
        assert comp[name]["recall_diff"] == recalls[hi] - recalls[lo]
        assert comp[name]["precision_diff"] == prec[hi] - prec[lo]
        assert comp[name]["abstention_diff"] == abst[hi] - abst[lo]
        for stat in ("recall_diff", "precision_diff", "abstention_diff"):
            ci = comp[name]["bootstrap_ci95"][stat]
            assert ci["n_defined"] + ci["n_undefined"] == 10000
        # rep-level paired diffs: exactly 3 raw points per statistic,
        # equal to the per-rep independent recount
        for rep in (1, 2, 3):
            w_hi = _sum([EXPECTED_CONFS[hi][rep][pid] for pid in PIDS])
            w_lo = _sum([EXPECTED_CONFS[lo][rep][pid] for pid in PIDS])
            assert comp[name]["rep_level_recall_diff"]["rep%d" % rep] == (
                w_hi["tp"] / (w_hi["tp"] + w_hi["fn"])
                - w_lo["tp"] / (w_lo["tp"] + w_lo["fn"]))
            # precision is None when a rep pooled no flag_bad (e.g. CP rep2)
            den_hi = w_hi["tp"] + w_hi["fp"]
            den_lo = w_lo["tp"] + w_lo["fp"]
            want_prec = (None if den_hi == 0 or den_lo == 0
                         else w_hi["tp"] / den_hi - w_lo["tp"] / den_lo)
            assert comp[name]["rep_level_precision_diff"]["rep%d" % rep] == \
                want_prec, (name, rep)
            assert comp[name]["rep_level_abstention_diff"]["rep%d" % rep] == (
                w_hi["abstain"] / w_hi["n_routes"]
                - w_lo["abstain"] / w_lo["n_routes"])
        # CP rep2 pooled no flag_bad at all: that rep-level point is None
        cp2 = _sum([EXPECTED_CONFS["CP"][2][pid] for pid in PIDS])
        assert cp2["tp"] + cp2["fp"] == 0
        assert comp["CP-B"]["rep_level_precision_diff"]["rep2"] is None
    # CP abstention point estimate + CI95 available for the 8.3 attribution
    cp_ci = paired["per_arm_bootstrap_ci95"]["abstention_rate"]["CP"]
    assert cp_ci["n_defined"] == 10000 and cp_ci["n_undefined"] == 0
    assert cp_ci["low"] <= abst["CP"] <= cp_ci["high"]
    # frozen seeds / design fields
    assert paired["seed"] == 20261003 and paired["n_bootstrap"] == 10000
    assert paired["n_clusters"] == 9
    # cross-batch REP-R2 references, report only
    ref = paired["cross_batch_reference"]
    assert ref["r2_arm_c_abstention_rate"] == 331.0 / 369.0
    assert ref["r2_arm_b_abstention_rate"] == 0.0


# ------------------------------------------------ 6. gate wiring fail-closed
def test_score_r3_gate_pass_and_fail(tmp_path):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    out = tmp_path / "out"
    out.mkdir()
    kw = {"gt_path": gt_path, "package_meta_path": meta_path,
          "readings_dir": r2_readings, "r2_stats_path": r2_stats_path}
    result = scoring_r3.score_r3(gt_path=gt_path,
                                 package_meta_path=meta_path,
                                 readings_root=readings_root, out_dir=out,
                                 reproduce_kwargs=kw)
    assert result["reproduce"]["passed"] is True

    tampered = json.load(open(r2_stats_path, encoding="utf-8"))
    tampered["tp"] += 1
    _write_json(r2_stats_path, tampered)
    with pytest.raises(RuntimeError, match="reproduction gate FAILED"):
        scoring_r3.score_r3(gt_path=gt_path,
                            package_meta_path=meta_path,
                            readings_root=readings_root, out_dir=out,
                            reproduce_kwargs=kw)


# ---------------------------------------------- 7. fail-closed validation
def _mutate_and_expect_raise(tmp_path, mutate):
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(tmp_path / "w")
    out = tmp_path / "out"
    out.mkdir()
    mutate(readings_root)
    kw = {"gt_path": gt_path, "package_meta_path": meta_path,
          "readings_dir": r2_readings, "r2_stats_path": r2_stats_path}
    with pytest.raises(RuntimeError):
        scoring_r3.score_r3(gt_path=gt_path,
                            package_meta_path=meta_path,
                            readings_root=readings_root, out_dir=out,
                            reproduce_kwargs=kw)


def test_fail_closed_invalid_verdict(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "BP", "rep1", "p04.json")
        data = json.load(open(path, encoding="utf-8"))
        data["model_output"][0]["verdict"] = "maybe"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_arm_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["arm"] = "BP"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_rep_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["rep"] = 2
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_schema_mismatch(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["schema"] = "v4.2-rep-r2-reading/1"
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_missing_reading(tmp_path):
    def mutate(readings_root):
        os.remove(os.path.join(readings_root, "CP", "rep2", "p09.json"))
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_duplicate_route_entry(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep2", "p05.json")
        data = json.load(open(path, encoding="utf-8"))
        data["model_output"] = data["model_output"] + \
            [dict(data["model_output"][0])]
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_seven_key_reading(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        del data["ts"]  # eight-key contract violated
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


def test_fail_closed_unvalidated_reading(tmp_path):
    def mutate(readings_root):
        path = os.path.join(readings_root, "B", "rep1", "p01.json")
        data = json.load(open(path, encoding="utf-8"))
        data["validation"]["passed"] = False
        _write_json(path, data)
    _mutate_and_expect_raise(tmp_path, mutate)


# ------------------------------------------------ 8. end-to-end determinism
def _score_kwargs(tmp_path, tag):
    w = tmp_path / ("w_" + tag)
    gt_path, meta_path, readings_root, r2_readings, r2_stats_path = \
        build_world(w)
    out = tmp_path / tag
    out.mkdir()
    return {"gt_path": gt_path, "package_meta_path": meta_path,
            "readings_root": readings_root, "out_dir": out,
            "reproduce_kwargs": {"gt_path": gt_path,
                                 "package_meta_path": meta_path,
                                 "readings_dir": r2_readings,
                                 "r2_stats_path": r2_stats_path}}


def test_score_r3_deterministic_bytes(tmp_path):
    outs = []
    for tag in ("o1", "o2"):
        scoring_r3.score_r3(**_score_kwargs(tmp_path, tag))
        out = tmp_path / tag
        outs.append({p.name: p.read_bytes()
                     for p in sorted(out.glob("*-stats.json"))})
    assert sorted(outs[0]) == ["arm-b-stats.json", "arm-bp-stats.json",
                               "arm-cp-stats.json", "paired-stats.json",
                               "session-stats.json"]
    assert outs[0] == outs[1]  # byte-deterministic across fresh worlds
    paired = json.loads(outs[0]["paired-stats.json"].decode("utf-8"))
    assert paired["schema"] == "v4.2-rep-r3-paired-stats/1"
    # r2 band is a report-only reference with no gate
    band = paired["r2_band_reference"]
    assert "no gate" in band["note"]
    for arm in scoring_r3.ARMS:
        entry = band["arms"][arm]
        assert entry["precision_min"] == max(2.0 * (24.0 / 42.0), 0.4)
        assert entry["abstention_max"] == 0.5
        assert isinstance(entry["passes_band"], bool)


# ------------------------------------------- 9. real frozen data end-to-end
def _real_independent_recount():
    """Recount the real 144 readings by hand (gt x model_output only)."""
    gt = json.load(open(scoring_r3.GT_PATH, encoding="utf-8"))
    meta = json.load(open(scoring_r3.PACKAGE_META_PATH, encoding="utf-8"))
    route_impr = {sid: {rid: bool(r["improvable"])
                        for rid, r in sc["per_route"].items()}
                  for sid, sc in gt["scenarios"].items()}
    totals = {arm: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "abstain": 0,
                    "n_routes": 0} for arm in scoring_r3.ARMS}
    for arm in scoring_r3.ARMS:
        for rep in (1, 2, 3):
            directory = os.path.join(str(scoring_r3.READINGS_ROOT), arm,
                                     "rep%d" % rep)
            for pid in sorted(meta):
                # latest -rN per pid, by hand (max retry number)
                names = [n for n in os.listdir(directory)
                         if n.startswith(pid)]
                def rno(n):
                    base = n[len(pid):-len(".json")]
                    return int(base[2:]) if base.startswith("-r") else 0
                name = max(names, key=rno)
                data = json.load(open(os.path.join(directory, name),
                                      encoding="utf-8"))
                sid = meta[pid]["sid"]
                assert data["arm"] == arm and data["rep"] == rep \
                    and data["pid"] == pid
                tot = totals[arm]
                for fl in data["model_output"]:
                    improvable = route_impr[sid][fl["route_id"]]
                    if fl["verdict"] == "flag_bad":
                        tot["tp" if improvable else "fp"] += 1
                    else:
                        if fl["verdict"] == "abstain":
                            tot["abstain"] += 1
                        tot["fn" if improvable else "tn"] += 1
                    tot["n_routes"] += 1
    return totals


def test_real_run_all_summary_and_independent_recount(capsys):
    recount = _real_independent_recount()
    result = scoring_r3.run_all()
    for arm in scoring_r3.ARMS:
        s = result["arms"][arm]
        r = recount[arm]
        assert (s["tp"], s["fp"], s["fn"], s["tn"], s["abstain"]) == \
            (r["tp"], r["fp"], r["fn"], r["tn"], r["abstain"]), arm
        assert s["n_routes"] == 369 and s["improvable"] == 99
        assert s["n_readings"] == 48
        assert s["recall"] == s["tp"] / (s["tp"] + s["fn"])
        assert s["precision"] == s["tp"] / (s["tp"] + s["fp"])
        assert s["abstention_rate"] == s["abstain"] / 369
        assert s["random_baseline"] == 99.0 / 369.0
    # the real-world retry (B rep1 p04: lone p04-r1.json, no base file)
    # resolves to the retry file and records no superseded set
    assert result["arms"]["B"]["reading_files"]["rep1"]["p04"] == "p04-r1.json"
    assert "superseded_retries" not in result["arms"]["B"]
    # primary/secondary reads off the recounted pooled values
    arms = result["arms"]
    comp = result["paired"]["comparisons"]
    assert comp["BP-B"]["recall_diff"] == \
        arms["BP"]["recall"] - arms["B"]["recall"]
    assert comp["CP-B"]["abstention_diff"] == \
        arms["CP"]["abstention_rate"] - arms["B"]["abstention_rate"]
    assert comp["CP-B"]["recall_diff"] == \
        arms["CP"]["recall"] - arms["B"]["recall"]
    ci = comp["BP-B"]["bootstrap_ci95"]["recall_diff"]
    assert ci["n_defined"] + ci["n_undefined"] == 10000
    assert ci["low"] <= comp["BP-B"]["recall_diff"] <= ci["high"]
    # cross-batch references, report only
    ref = result["paired"]["cross_batch_reference"]
    assert ref["r2_arm_c_abstention_rate"] == pytest.approx(0.8970, abs=1e-4)
    assert ref["r2_arm_b_abstention_rate"] == 0.0
    lines = capsys.readouterr().out.strip().splitlines()
    summary = json.loads(lines[-1])
    assert set(summary) == {"n_readings", "arms", "primary",
                            "abstention_cp"}
    assert summary["n_readings"] == 144
    assert summary["arms"] == {"B": {"n_readings": 48},
                               "BP": {"n_readings": 48},
                               "CP": {"n_readings": 48}}
    assert summary["primary"]["recall_diff"] == \
        arms["BP"]["recall"] - arms["B"]["recall"]
    assert summary["primary"]["ci_low"] == ci["low"]
    assert summary["primary"]["ci_high"] == ci["high"]
    cp_ci = comp["CP-B"]["bootstrap_ci95"]["abstention_diff"]
    assert summary["abstention_cp"]["diff"] == \
        arms["CP"]["abstention_rate"] - arms["B"]["abstention_rate"]
    assert summary["abstention_cp"]["ci_low"] == cp_ci["low"]
    assert summary["abstention_cp"]["ci_high"] == cp_ci["high"]
    # five stats files exist in out/v4.2-rep-r3/ after the run
    for name in ("arm-b-stats.json", "arm-bp-stats.json",
                 "arm-cp-stats.json", "session-stats.json",
                 "paired-stats.json"):
        assert os.path.isfile(os.path.join(REAL_OUT, name)), name
    # canonical JSON: sorted keys, indent=1, LF, trailing newline
    raw = open(os.path.join(REAL_OUT, "paired-stats.json"), "rb").read()
    assert raw.endswith(b"\n") and b"\r" not in raw
    assert raw.decode("utf-8") == json.dumps(
        json.loads(raw.decode("utf-8")), sort_keys=True, ensure_ascii=False,
        indent=1, allow_nan=False) + "\n"


# --------------------------- 11. real BP/CP derivation gates
# PACK-SPEC-REP-R3-TRAJ promised test-enforced derivation gates (its §9.2);
# delivered only-add in the 2026-10-03 closure fix batch (deviation D-R3-F1):
# independent re-derivation of packs-bp/packs-cp from the frozen R1/R2
# sources, byte-exact against the on-disk products, plus the §6 frozen byte
# table and spec §7 gates 1-11.

import re as _re

from pcbflow.v4_2.inspector import _IDENTITY_RE, _JUDGE_SUFFIX

_R1_REAL_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r1")
_R2_REAL_OUT = os.path.join(_ROOT, "out", "v4.2-rep-r2")
_BP_DIR = os.path.join(REAL_OUT, "packs-bp")
_CP_DIR = os.path.join(REAL_OUT, "packs-cp")
_TRAJ_PIDS = ["p%02d" % i for i in range(1, 17)]

# PACK-SPEC-REP-R3-TRAJ §6 frozen table: pid -> (nRoutes, bpBytes, cpBytes)
_TRAJ_FROZEN = {
    "p01": (8, 28727, 31062), "p02": (9, 46544, 47383),
    "p03": (4, 21180, 22101), "p04": (7, 26867, 28608),
    "p05": (8, 39715, 40414), "p06": (7, 27546, 29252),
    "p07": (10, 30181, 33360), "p08": (7, 25081, 27352),
    "p09": (8, 40642, 41182), "p10": (10, 30234, 33406),
    "p11": (7, 25485, 27375), "p12": (10, 29991, 33165),
    "p13": (4, 21912, 22752), "p14": (6, 23123, 24845),
    "p15": (10, 30483, 33617), "p16": (8, 41345, 41746),
}
_GEOM_RE = _re.compile(
    r'^[ \t]*<path id="geom-([^"]+)" d="([^"]+)" class="[^"]*"/>$')
_DTOK_RE = _re.compile(r'([ML])\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)')
_TRAJ_HEADER = ("[trajectories] frame=board-mm y_axis=down-positive "
                "per-route incumbent polyline waypoints "
                "(matches [segment-index] route_id set)")
_BP_FORBIDDEN = ["<svg", "<path", 'd="M', "data-pcbflow-schema",
                 "viewBox", "data-route-id", "data-object-kind"]
_CP_LINE_RE = _re.compile(r'^[ \t]*route \S+ polyline-mm: ')
_BP_TAIL = "=== END PCBFLOW-INTENTPACK-V1 ===\n"


def _traj_polyline(d):
    toks = _DTOK_RE.findall(d)
    assert toks and toks[0][0] == "M"
    assert all(t[0] == "L" for t in toks[1:])
    assert _DTOK_RE.sub("", d).strip() == ""
    return "->".join("(%s %s)" % (x, y) for _, x, y in toks)


def _segment_index_routes(b_user):
    out, in_sec = [], False
    for line in b_user.split("\n"):
        if line.startswith("[segment-index]"):
            in_sec = True
        elif in_sec and line.startswith("["):
            break
        elif in_sec:
            m = _re.search(r"route_id=(\S+)", line)
            if m:
                out.append(m.group(1))
    return out


def _derive_bp(a_user, b_user):
    polys = {}
    for line in a_user.split("\n"):
        m = _GEOM_RE.match(line)
        if m:
            assert m.group(1) not in polys
            polys[m.group(1)] = _traj_polyline(m.group(2))
    assert set(polys) == set(_segment_index_routes(b_user))
    lines = b_user.split("\n")
    anchors = [i for i, l in enumerate(lines) if l == "[task]"]
    assert len(anchors) == 1
    data = [rid + ": " + polys[rid] for rid in sorted(polys)]
    i = anchors[0]
    return "\n".join(lines[:i] + [_TRAJ_HEADER] + data + lines[i:])


def _derive_cp(a_user):
    out, replaced = [], 0
    for line in a_user.split("\n"):
        m = _GEOM_RE.match(line)
        if m:
            indent = line[:len(line) - len(line.lstrip(" \t"))]
            out.append(indent + "route " + m.group(1) + " polyline-mm: "
                       + _traj_polyline(m.group(2)))
            replaced += 1
        else:
            out.append(line)
    assert replaced > 0
    return "\n".join(out), replaced


def test_traj_frozen_table_totals():
    assert sum(v[0] for v in _TRAJ_FROZEN.values()) == 123
    assert sum(v[1] for v in _TRAJ_FROZEN.values()) == 489056
    assert sum(v[2] for v in _TRAJ_FROZEN.values()) == 517620


def test_traj_derivation_deterministic():
    a = json.load(open(os.path.join(_R1_REAL_OUT, "tasks-a", "p01.json"),
                       encoding="utf-8"))
    b = json.load(open(os.path.join(_R1_REAL_OUT, "packs-b", "p01.json"),
                       encoding="utf-8"))
    assert _derive_bp(a["user"], b["user"]) == _derive_bp(a["user"], b["user"])
    assert _derive_cp(a["user"]) == _derive_cp(a["user"])


@pytest.mark.parametrize("pid", _TRAJ_PIDS)
def test_bp_cp_derivation_all_spec7_gates(pid):
    n_routes, bp_bytes, cp_bytes = _TRAJ_FROZEN[pid]
    a = json.load(open(os.path.join(_R1_REAL_OUT, "tasks-a",
                                    pid + ".json"), encoding="utf-8"))
    b = json.load(open(os.path.join(_R1_REAL_OUT, "packs-b",
                                    pid + ".json"), encoding="utf-8"))
    c2 = json.load(open(os.path.join(_R2_REAL_OUT, "packs-c",
                                     pid + ".json"), encoding="utf-8"))
    bp = json.load(open(os.path.join(_BP_DIR, pid + ".json"),
                        encoding="utf-8"))
    cp = json.load(open(os.path.join(_CP_DIR, pid + ".json"),
                        encoding="utf-8"))

    # gate 1: key sets, pid passthrough, system byte-equality
    assert sorted(bp.keys()) == ["pid", "system", "user"]
    assert sorted(cp.keys()) == ["pid", "system", "user"]
    assert bp["pid"] == b["pid"] == pid and cp["pid"] == a["pid"] == pid
    assert bp["system"] == b["system"]
    assert cp["system"] == a["system"]

    # gate 2: geom line count == n_routes; four route-id sets equal
    # (geom ids / data-route-id / [segment-index] / derivation inputs)
    geom = [m for m in (_GEOM_RE.match(l) for l in a["user"].split("\n")) if m]
    assert len(geom) == n_routes
    geom_rids = {m.group(1) for m in geom}
    assert geom_rids == set(_re.findall(r'data-route-id="([^"]+)"', a["user"]))
    assert geom_rids == set(_segment_index_routes(b["user"]))

    # gates 5/10 (+9 budget): byte-exact independent re-derivation of both
    # packs against the on-disk products, frozen byte table, 48000 budget
    bp_user = _derive_bp(a["user"], b["user"])
    cp_user, cp_replaced = _derive_cp(a["user"])
    assert cp_replaced == n_routes
    assert bp["user"] == bp_user
    assert cp["user"] == cp_user
    assert len(bp["user"].encode("utf-8")) == bp_bytes <= 48000
    assert len(cp["user"].encode("utf-8")) == cp_bytes <= 48000

    # gate 3: BP forbidden tokens (spec §7.3, seven strings)
    for tok in _BP_FORBIDDEN:
        assert tok not in bp["user"]

    # gate 4: blindness regex over both products, user and system
    for doc in (bp["user"], bp["system"], cp["user"], cp["system"]):
        assert not _IDENTITY_RE.search(doc)

    # gate 7: BP has exactly one standalone [task] line
    assert bp["user"].split("\n").count("[task]") == 1

    # gate 8: geom residue zero in both products
    for tok in ("<path", 'd="M', "geom-"):
        assert tok not in bp["user"] and tok not in cp["user"]

    # gate 6: CP minus its replace lines == R2 frozen C user, byte-exact
    cp_lines = cp["user"].split("\n")
    stripped = [l for l in cp_lines if not _CP_LINE_RE.match(l)]
    assert sum(1 for l in cp_lines if _CP_LINE_RE.match(l)) == n_routes
    assert "\n".join(stripped) == c2["user"]

    # gate 11: judge-suffix / pack-tail anchors
    assert cp["user"].endswith(_JUDGE_SUFFIX)
    assert bp["user"].endswith(_BP_TAIL)

    # BP section shape (spec §4): one header line, n_routes data lines in
    # lexicographic route_id order, [task] immediately after the section
    blines = bp["user"].split("\n")
    heads = [i for i, l in enumerate(blines) if l == _TRAJ_HEADER]
    assert len(heads) == 1
    data = blines[heads[0] + 1:heads[0] + 1 + n_routes]
    for off, rid in enumerate(sorted(geom_rids)):
        assert data[off].startswith(rid + ": (")
    assert blines[heads[0] + 1 + n_routes] == "[task]"
