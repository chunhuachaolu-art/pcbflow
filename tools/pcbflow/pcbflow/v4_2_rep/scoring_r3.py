"""REP-R3 deterministic scoring, main side (B/BP/CP trajectory-summary replicate).

Implements the frozen metric caliber of PREREG-REP-R3.md sections 7/8
(out/v4.2-rep-r3/PREREG-REP-R3.md, v1 2026-10-03), reusing the frozen
r1/r2/REP-R2 primitives of ``pcbflow.v4_2_rep.scoring`` and
``pcbflow.v4_2_rep.scoring_r2`` read-only (this module adds a file; it
never modifies the siblings):

1. ``reproduce_gate()`` / the hard pre-emission gate inside ``score_r3()``
   -- pipeline regression via the existing
   ``pcbflow.v4_2_rep.scoring.reproduce_r2()`` (threaded through
   ``scoring_r2.reproduce_gate()``) over out/v4.2-seat-r2/m1-readings/ +
   the frozen GT: must reproduce out/v4.2-seat-r2/m1-stats.json
   value-for-value (ints exact, floats within 1e-9) BEFORE any REP-R3
   number is emitted (PREREG-REP-R3 section 8.2; tp=20 fp=6 fn=13 tn=84
   precision=0.7692307692307693 recall=0.6060606060606061
   abstention_rate=0.0 random_baseline=0.2682926829268293).

2. ``score_r3()`` -- same per-route confusion caliber over
   out/v4.2-rep-r3/readings/<B|BP|CP>/rep<k>/p<NN>.json (file schema
   v4.2-rep-r3-reading/1, EIGHT keys arm/model_output/pid/rep/
   return_raw/schema/ts/validation; the judgment is the ``model_output``
   flags; "-rN" retry files resolve to the highest N per pid, r1
   ``_resolve_reading_files`` semantics), 3 arms x 3 reps x 16 pids =
   144 readings, 369 route judgments per arm:
     tp = flag_bad & improvable          fp = flag_bad & not improvable
     fn = not flagged & improvable       (includes abstained improvable)
     tn = not flagged & not improvable   (includes abstained non-improvable)
   precision = tp/(tp+fp)  recall = tp/(tp+fn)
   abstention_rate = abstain verdicts / n_routes
   random_baseline = improvable judgments / n_routes (= 99/369)
   Stratified per rep (3 x 123), per session (6 = rep x batch, batch one
   = p01-p08 / batch two = p09-p16), per scenario (16, pooled across the
   three reps -- also the bootstrap cluster counts).

3. Paired cluster bootstrap (PREREG section 8.1): primary comparison
   recall(BP)-recall(B); secondary abstention(CP)-abstention(B) and
   recall(CP)-recall(B); precision paired diffs co-reported over the
   same comparison set; resample unit = the 16 scenario clusters
   (counts pooled across the 3 reps per arm), B=10000 replicates, seed
   20261003, ONE shared index list per replicate applied to all three
   arms, percentile CI95 at 2.5/97.5 (linear interpolation on order
   statistics).  Undefined replicates (zero denominator) are excluded
   from the percentiles and counted in n_undefined; nothing is imputed
   (abstention has no undefined case: n* > 0 always, recorded as such).
   Rep-level paired diffs (3 raw points per comparison per statistic,
   descriptive, no inference) are reported as raw values.  The
   historical r2 acceptance band (precision >= max(2*random_baseline,
   0.4) and abstention <= 0.5) is a REPORT ONLY reference per arm, and
   the cross-batch REP-R2 abstention references (R2 arm C = 0.8970...,
   R2 arm B = 0.0) are REPORT ONLY constants -- REP-R3 sets no gate
   (PREREG section 7 / J4).

Outputs (canonical JSON, written only inside out/v4.2-rep-r3/):
   arm-b-stats.json, arm-bp-stats.json, arm-cp-stats.json,
   session-stats.json (18-session flat table), paired-stats.json.

Determinism: fixed seeds, no wall-clock, no host state, stdlib only --
identical inputs yield byte-identical files (reading ``ts`` fields are
input data and are never copied into any output).

``run_all()`` ends with one line, ``print(json.dumps(summary))`` (keys:
n_readings, arms.<arm>.n_readings, primary.recall_diff/ci_low/ci_high
[BP-B], abstention_cp.diff/ci_low/ci_high [abstention(CP)-abstention(B)]).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from pcbflow.v4_2_rep import scoring      # frozen r1/r2 primitives, read-only
from pcbflow.v4_2_rep import scoring_r2   # frozen REP-R2 layer, read-only

# ------------------------------------------------------------- frozen paths
# ROOT = .../tools/pcbflow  (this file: ROOT/pcbflow/v4_2_rep/scoring_r3.py)
ROOT = Path(__file__).resolve().parents[2]

GT_PATH = scoring.GT_PATH
PACKAGE_META_PATH = scoring.PACKAGE_META_PATH
R2_STATS_PATH = scoring.R2_STATS_PATH

REP_OUT_DIR = ROOT / "out" / "v4.2-rep-r3"
READINGS_ROOT = REP_OUT_DIR / "readings"
ARM_STATS_PATHS = {
    "B": REP_OUT_DIR / "arm-b-stats.json",
    "BP": REP_OUT_DIR / "arm-bp-stats.json",
    "CP": REP_OUT_DIR / "arm-cp-stats.json",
}
SESSION_STATS_PATH = REP_OUT_DIR / "session-stats.json"
PAIRED_STATS_PATH = REP_OUT_DIR / "paired-stats.json"

# -------------------------------------------------------- frozen constants
# frozen draw-table lexicographic order (PREREG-REP-R3 section 5)
ARMS = ("B", "BP", "CP")
REPS = (1, 2, 3)
N_REPS = len(REPS)

READING_SCHEMA = "v4.2-rep-r3-reading/1"
# PREREG-REP-R3 section 6 (R53① eight-key reading contract)
READING_KEYS = frozenset(("arm", "model_output", "pid", "rep", "return_raw",
                          "schema", "ts", "validation"))
ARM_STATS_SCHEMA = "v4.2-rep-r3-arm-stats/1"
SESSION_STATS_SCHEMA = "v4.2-rep-r3-session-stats/1"
PAIRED_STATS_SCHEMA = "v4.2-rep-r3-paired-stats/1"

# PREREG-REP-R3 section 8.1: primary read first, then the two secondary.
COMPARISONS = (("BP", "B"), ("CP", "B"), ("CP", "BP"))
PRIMARY_COMPARISON = COMPARISONS[0]

BOOTSTRAP_SEED = 20261003  # PREREG-REP-R3 section 8.1
N_BOOTSTRAP = 10000
CI_LO = scoring.CI_LO  # 2.5
CI_HI = scoring.CI_HI  # 97.5

# cross-batch historical reference, REPORT ONLY (task charter / frozen
# REP-R2 files): out/v4.2-rep-r2/arm-c-stats.json abstention_rate =
# 331/369 = 0.8970189701897019; arm-b-stats.json = 0/369 = 0.0
R2_C_ABSTENTION_RATE = 331.0 / 369.0
R2_B_ABSTENTION_RATE = 0.0

_R2_BAND_NOTE = ("historical r2 acceptance band, reported only -- REP-R3 "
                 "sets no gate (PREREG-REP-R3 section 7 / J4)")

# reuse from the frozen sibling modules: _load_json, _write_canonical,
# _resolve_reading_files, _check_structure, validate_six_rules, _confusion,
# _percentile, _ratio (scoring); _gt_tables, reproduce_gate, _sum_confs,
# _row, _batch_of, _reading_dir, _CONF_KEYS (scoring_r2).
_load_json = scoring._load_json
_write_canonical = scoring._write_canonical
_resolve_reading_files = scoring._resolve_reading_files
_check_structure = scoring._check_structure
validate_six_rules = scoring.validate_six_rules
_confusion = scoring._confusion
_percentile = scoring._percentile
_ratio = scoring._ratio

_gt_tables = scoring_r2._gt_tables
reproduce_gate = scoring_r2.reproduce_gate
_sum_confs = scoring_r2._sum_confs
_row = scoring_r2._row
_batch_of = scoring_r2._batch_of
_CONF_KEYS = scoring_r2._CONF_KEYS


# ----------------------------------------------------------------- helpers
def _flags_from_reading(data, pid: str, arm: str, rep: int, route_set: set):
    """Eight-key v4.2-rep-r3-reading/1 -> the judgment flags list.

    Hard checks (fail-closed): exact eight-key set; ``validation.passed``
    is true (a reading that failed its own pipeline validation is not a
    locked final reading and has no scoring caliber); ``return_raw`` and
    ``ts`` are strings; then the frozen r1 structural checker runs on a
    flags-view shim carrying the reading's own pid/arm/schema fields
    (pid equality, arm == directory arm, schema == r3 reading schema,
    model_output is a list of well-formed per-route entries, route_id
    set == package route set, no duplicates).
    """
    if not isinstance(data, dict):
        raise RuntimeError("%s: reading is not a JSON object" % pid)
    if set(data) != READING_KEYS:
        raise RuntimeError("%s: key set %s != eight-key reading contract %s"
                           % (pid, sorted(data), sorted(READING_KEYS)))
    validation = data["validation"]
    if not isinstance(validation, dict) or validation.get("passed") is not True:
        raise RuntimeError("%s: validation.passed is not true -- unvalidated/"
                           "failed reading, refusing to score" % pid)
    for key in ("return_raw", "ts"):
        if not isinstance(data[key], str):
            raise RuntimeError("%s: %s is not a string" % (pid, key))
    shim = {"pid": data["pid"], "arm": data["arm"], "schema": data["schema"],
            "flags": data["model_output"]}
    flags = _check_structure(shim, pid, route_set, expect_arm=arm,
                             expect_schema=READING_SCHEMA)
    if data["rep"] != rep or isinstance(data["rep"], bool):
        raise RuntimeError("%s: rep field %r != %r" % (pid, data["rep"], rep))
    return flags


def load_readings(readings_root: Path, meta: dict, route_impr: dict):
    """Resolve, validate and confuse every reading of the 3x3x|pid| grid.

    Returns (confusions, chosen_files, superseded) with
      confusions[arm][rep][pid] = confusion dict   (r2 caliber)
      chosen_files[arm][rep][pid] = filename actually consumed
      superseded[arm][rep][pid]   = superseded '-rN' filenames (when any)
    Fail-closed: any structural/six-rule violation raises (PREREG-REP-R3
    sections 7/10 -- the resolved file is the final post-retry reading;
    a non-compliant final reading has no preregistered scoring caliber).
    """
    readings_root = Path(readings_root)
    pids = sorted(meta)
    confusions = {arm: {} for arm in ARMS}
    chosen_files = {arm: {} for arm in ARMS}
    superseded = {arm: {} for arm in ARMS}
    for arm in ARMS:
        for rep in REPS:
            directory = scoring_r2._reading_dir(readings_root, arm, rep)
            chosen, sup = _resolve_reading_files(directory, pids)
            conf = {}
            for pid in pids:
                sid = meta[pid]["sid"]
                route_set = set(route_impr[sid])
                data = _load_json(directory / chosen[pid])
                flags = _flags_from_reading(data, pid, arm, rep, route_set)
                problems = validate_six_rules(flags, route_set)
                if problems:
                    raise RuntimeError(
                        "non-compliant final reading %s rep%d/%s, refusing "
                        "to score:\n  %s" % (arm, rep, pid,
                                             "\n  ".join(problems)))
                conf[pid] = _confusion(flags, route_impr[sid])
            confusions[arm][rep] = conf
            chosen_files[arm][rep] = chosen
            if sup:
                superseded[arm][rep] = sup
    return confusions, chosen_files, superseded


def _cluster_rows(confusions: dict, meta: dict, sids_sorted: list) -> dict:
    """Per-arm per-scenario counts pooled across the 3 reps (PREREG 8.1).

    Returns {arm: [row, ...] in identical sorted-sid order} where each
    row is the summed confusion of that arm's three rep readings of the
    scenario (bootstrap cluster counts; intra-cluster cross-rep and
    cross-arm correlation is preserved, never 48 independent clusters).
    """
    rows = {}
    for arm in ARMS:
        per_sid = {sid: {k: 0 for k in _CONF_KEYS} for sid in sids_sorted}
        for rep in REPS:
            for pid, conf in confusions[arm][rep].items():
                sid = meta[pid]["sid"]
                for k in _CONF_KEYS:
                    per_sid[sid][k] += conf[k]
        rows[arm] = [per_sid[sid] for sid in sids_sorted]
    return rows


# --------------------------------------------------------- bootstrap (3)
def _bootstrap_three_arm(cluster_rows: dict, seed: int = BOOTSTRAP_SEED,
                         n_boot: int = N_BOOTSTRAP) -> dict:
    """Paired cluster bootstrap over the scenario clusters (PREREG 8.1).

    cluster_rows maps arm -> per-scenario count rows in identical
    (sorted-sid) order; each replicate draws ONE shared index list
    applied to all three arms.  Returns {statistic_key:
    {low, high, n_defined, n_undefined}}; undefined replicates (zero
    denominator) are excluded from the percentiles and counted, nothing
    imputed (r1 frozen convention; abstention has no undefined case --
    n* > 0 always -- and is recorded with n_undefined == 0).
    """
    k = len(cluster_rows[ARMS[0]])
    for arm in ARMS[1:]:
        if len(cluster_rows[arm]) != k:
            raise RuntimeError("arm cluster rows are not aligned")
    stat_keys = []
    for arm in ARMS:
        stat_keys += ["recall_%s" % arm, "precision_%s" % arm,
                      "abstention_%s" % arm]
    for hi, lo in COMPARISONS:
        stat_keys += ["%s_diff_%s-%s" % (stat, hi, lo)
                      for stat in ("recall", "precision", "abstention")]
    samples = {key: [] for key in stat_keys}
    undefined = {key: 0 for key in stat_keys}
    rng = random.Random(seed)
    for _ in range(n_boot):
        idx = [rng.randrange(k) for _ in range(k)]
        totals = {}
        for arm in ARMS:
            tot = {f: 0 for f in _CONF_KEYS}
            for i in idx:
                row = cluster_rows[arm][i]
                for f in _CONF_KEYS:
                    tot[f] += row[f]
            totals[arm] = tot
        recall = {arm: _ratio(totals[arm]["tp"],
                              totals[arm]["tp"] + totals[arm]["fn"])
                  for arm in ARMS}
        precision = {arm: _ratio(totals[arm]["tp"],
                                 totals[arm]["tp"] + totals[arm]["fp"])
                     for arm in ARMS}
        abstention = {arm: _ratio(totals[arm]["abstain"],
                                  totals[arm]["n_routes"])
                      for arm in ARMS}
        for stat, table in (("recall", recall), ("precision", precision),
                            ("abstention", abstention)):
            for arm in ARMS:
                val = table[arm]
                if val is None:
                    undefined["%s_%s" % (stat, arm)] += 1
                else:
                    samples["%s_%s" % (stat, arm)].append(val)
            for hi, lo in COMPARISONS:
                key = "%s_diff_%s-%s" % (stat, hi, lo)
                if table[hi] is None or table[lo] is None:
                    undefined[key] += 1
                else:
                    samples[key].append(table[hi] - table[lo])
    ci = {}
    for key in stat_keys:
        if samples[key]:
            ci[key] = {
                "low": _percentile(samples[key], CI_LO),
                "high": _percentile(samples[key], CI_HI),
                "n_defined": len(samples[key]),
                "n_undefined": undefined[key],
            }
        else:
            ci[key] = {"low": None, "high": None, "n_defined": 0,
                       "n_undefined": undefined[key]}
    return ci


def _r2_band_arm(pooled_row: dict) -> dict:
    """Historical r2 band reference for one arm (report only, no gate)."""
    band = scoring._r2_band(pooled_row["precision"],
                            pooled_row["abstention_rate"],
                            pooled_row["improvable"] / pooled_row["n_routes"])
    band["note"] = _R2_BAND_NOTE
    band["passes_band"] = bool(band["precision_meets_band"]
                               and band["abstention_within_band"])
    return band


# ------------------------------------------------------------- score_r3()
def score_r3(gt_path: Path = GT_PATH,
             package_meta_path: Path = PACKAGE_META_PATH,
             readings_root: Path = READINGS_ROOT,
             out_dir: Path = REP_OUT_DIR,
             reproduce: bool = True,
             reproduce_kwargs: dict = None) -> dict:
    """Gate on the r2 reproduction, then score all three arms + pairing.

    Writes arm-{b,bp,cp}-stats.json, session-stats.json, paired-stats.json
    (canonical JSON) inside ``out_dir`` (default out/v4.2-rep-r3/) and
    returns the full result dict.  ``reproduce_kwargs`` redirects the
    gate's frozen inputs (synthetic-fixture testing only).
    """
    gate = None
    if reproduce:
        gate = reproduce_gate(**(reproduce_kwargs or {}))
        if not gate["passed"]:
            raise RuntimeError(
                "r2 reproduction gate FAILED -- REP-R3 statistics pipeline "
                "is buggy, refusing to emit any REP-R3 number "
                "(PREREG-REP-R3 section 8.2):\n  "
                + "\n  ".join(gate["problems"]))

    out_dir = Path(out_dir)
    meta, route_impr, sids_sorted = _gt_tables(gt_path, package_meta_path)
    pids = sorted(meta)
    confusions, chosen_files, superseded = load_readings(
        readings_root, meta, route_impr)

    # ---- per-arm stats (pooled 369 + per_rep + per_session + per_scenario)
    arm_stats = {}
    for arm in ARMS:
        all_confs = [confusions[arm][rep][pid]
                     for rep in REPS for pid in pids]
        pooled = _row(_sum_confs(all_confs))
        per_rep = {}
        for rep in REPS:
            per_rep["rep%d" % rep] = _row(_sum_confs(
                [confusions[arm][rep][pid] for pid in pids]))
        per_session = {}
        for rep in REPS:
            for batch in (1, 2):
                per_session["rep%d-batch%d" % (rep, batch)] = _row(_sum_confs(
                    [confusions[arm][rep][pid]
                     for pid in pids if _batch_of(pid) == batch]))
        per_scenario = {}
        for sid in sids_sorted:
            per_scenario[sid] = _row(_sum_confs(
                [confusions[arm][rep][pid] for rep in REPS
                 for pid in pids if meta[pid]["sid"] == sid]))
        stats = {
            "schema": ARM_STATS_SCHEMA,
            "arm": arm,
            "n_reps": N_REPS,
            "n_sessions": N_REPS * 2,
            "n_scenarios": len(sids_sorted),
            "n_readings": N_REPS * len(pids),
            "n_routes": pooled["n_routes"],
            "tp": pooled["tp"],
            "fp": pooled["fp"],
            "fn": pooled["fn"],
            "tn": pooled["tn"],
            "improvable": pooled["improvable"],
            "flag_bad": pooled["flag_bad"],
            "abstain": pooled["abstain"],
            "precision": pooled["precision"],
            "recall": pooled["recall"],
            "abstention_rate": pooled["abstention_rate"],
            "random_baseline": (pooled["improvable"] / pooled["n_routes"]
                                if pooled["n_routes"] else None),
            # fail-closed above: every scored reading passed the six rules
            "schema_compliant_readings": N_REPS * len(pids),
            "schema_compliance_rate": 1.0,
            "reading_files": {("rep%d" % rep): dict(chosen_files[arm][rep])
                              for rep in REPS},
            "per_rep": per_rep,
            "per_session": per_session,
            "per_scenario": per_scenario,
        }
        if any(superseded[arm].get(rep) for rep in REPS):
            stats["superseded_retries"] = {
                ("rep%d" % rep): superseded[arm][rep]
                for rep in REPS if superseded[arm].get(rep)}
        arm_stats[arm] = stats

    # ---- session flat table (18 rows: arm/rep/batch + counts + rates)
    sessions = []
    for arm in ARMS:
        for rep in REPS:
            for batch in (1, 2):
                row = _row(_sum_confs(
                    [confusions[arm][rep][pid] for pid in pids
                     if _batch_of(pid) == batch]))
                sessions.append({
                    "arm": arm,
                    "rep": rep,
                    "batch": batch,
                    "tp": row["tp"],
                    "fp": row["fp"],
                    "fn": row["fn"],
                    "tn": row["tn"],
                    "recall": row["recall"],
                    "precision": row["precision"],
                    "abstain_rate": row["abstention_rate"],
                })
    session_stats = {
        "schema": SESSION_STATS_SCHEMA,
        "n_sessions": len(sessions),
        "sessions": sessions,
    }

    # ---- paired stats (pooled + three-arm cluster bootstrap + rep level)
    cluster_rows = _cluster_rows(confusions, meta, sids_sorted)
    pooled_rows = {arm: arm_stats[arm] for arm in ARMS}
    # ONE bootstrap run feeds every reported CI: all statistics must come
    # from the same replicate draws (shared index list, PREREG 8.1).
    ci = _bootstrap_three_arm(cluster_rows)
    comparisons = {}
    for hi, lo in COMPARISONS:
        role = "primary" if (hi, lo) == PRIMARY_COMPARISON else "secondary"
        rep_level = {}
        for stat, field in (("recall", "recall"), ("precision", "precision"),
                            ("abstention", "abstention_rate")):
            points = {}
            for rep in REPS:
                v_hi = pooled_rows[hi]["per_rep"]["rep%d" % rep][field]
                v_lo = pooled_rows[lo]["per_rep"]["rep%d" % rep][field]
                points["rep%d" % rep] = (None if v_hi is None or v_lo is None
                                         else v_hi - v_lo)
            rep_level["%s_diff" % stat] = points
        comparisons["%s-%s" % (hi, lo)] = {
            "role": role,
            "direction": "arm %s minus arm %s (PREREG-REP-R3 section 8.1)"
                         % (hi, lo),
            "recall_diff": (None if pooled_rows[hi]["recall"] is None
                            or pooled_rows[lo]["recall"] is None
                            else pooled_rows[hi]["recall"]
                            - pooled_rows[lo]["recall"]),
            "precision_diff": (None if pooled_rows[hi]["precision"] is None
                               or pooled_rows[lo]["precision"] is None
                               else pooled_rows[hi]["precision"]
                               - pooled_rows[lo]["precision"]),
            "abstention_diff": (None
                                if pooled_rows[hi]["abstention_rate"] is None
                                or pooled_rows[lo]["abstention_rate"] is None
                                else pooled_rows[hi]["abstention_rate"]
                                - pooled_rows[lo]["abstention_rate"]),
            "bootstrap_ci95": {
                "recall_diff": dict(ci["recall_diff_%s-%s" % (hi, lo)]),
                "precision_diff": dict(ci["precision_diff_%s-%s" % (hi, lo)]),
                "abstention_diff": dict(ci["abstention_diff_%s-%s" % (hi, lo)]),
            },
            "rep_level_recall_diff": rep_level["recall_diff"],
            "rep_level_precision_diff": rep_level["precision_diff"],
            "rep_level_abstention_diff": rep_level["abstention_diff"],
        }
    paired = {
        "schema": PAIRED_STATS_SCHEMA,
        "seed": BOOTSTRAP_SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_clusters": len(sids_sorted),
        "cluster_caliber": ("per-arm per-scenario counts pooled across the "
                            "3 reps before resampling (PREREG-REP-R3 "
                            "section 8.1)"),
        "resample_unit": ("scenario (cluster bootstrap, 16 clusters, with "
                          "replacement)"),
        "paired_design": ("each replicate draws ONE scenario index list "
                          "applied to all three arms"),
        "percentile_method": ("linear interpolation on order statistics "
                              "(numpy 'linear' equivalent)"),
        "undefined_replicate_convention": (
            "a statistic with zero denominator in a replicate (recall: no "
            "improvable route resampled; precision: no flag_bad resampled) "
            "is undefined; undefined replicates are excluded from the "
            "percentiles and counted in n_undefined; nothing is imputed"),
        "abstention_undefined_note": ("abstention has no undefined case: "
                                      "n* > 0 in every replicate, so its "
                                      "n_undefined is always 0 (PREREG "
                                      "section 8.1)"),
        "n_routes_per_arm": arm_stats["B"]["n_routes"],
        "pooled": {
            "recall": {arm: pooled_rows[arm]["recall"] for arm in ARMS},
            "precision": {arm: pooled_rows[arm]["precision"] for arm in ARMS},
            "abstention_rate": {arm: pooled_rows[arm]["abstention_rate"]
                                for arm in ARMS},
        },
        "comparisons": comparisons,
        "per_arm_bootstrap_ci95": {
            "recall": {arm: ci["recall_%s" % arm] for arm in ARMS},
            "precision": {arm: ci["precision_%s" % arm] for arm in ARMS},
            "abstention_rate": {arm: ci["abstention_%s" % arm]
                                for arm in ARMS},
        },
        "r2_band_reference": {
            "note": _R2_BAND_NOTE,
            "arms": {arm: _r2_band_arm(pooled_rows[arm]) for arm in ARMS},
        },
        "cross_batch_reference": {
            "note": ("cross-batch REP-R2 abstention references, REPORT "
                     "ONLY -- frozen values of out/v4.2-rep-r2/arm-c-stats."
                     "json (331/369) and arm-b-stats.json (0/369); no "
                     "inference is drawn across batches"),
            "r2_arm_c_abstention_rate": R2_C_ABSTENTION_RATE,
            "r2_arm_c_abstain_over_n": "331/369",
            "r2_arm_b_abstention_rate": R2_B_ABSTENTION_RATE,
            "r2_arm_b_abstain_over_n": "0/369",
        },
    }

    written = []
    for arm in ARMS:
        out = out_dir / ARM_STATS_PATHS[arm].name
        _write_canonical(out, arm_stats[arm])
        written.append(out)
    _write_canonical(out_dir / SESSION_STATS_PATH.name, session_stats)
    written.append(out_dir / SESSION_STATS_PATH.name)
    _write_canonical(out_dir / PAIRED_STATS_PATH.name, paired)
    written.append(out_dir / PAIRED_STATS_PATH.name)

    return {"reproduce": gate, "arms": arm_stats, "sessions": session_stats,
            "paired": paired, "written": written}


# --------------------------------------------------------------- run_all()
def run_all() -> dict:
    """Gate -> score -> write; the last printed line is the JSON summary."""
    result = score_r3()
    for arm in ARMS:
        s = result["arms"][arm]
        print("arm %s: tp=%d fp=%d fn=%d tn=%d flag_bad=%d precision=%r "
              "recall=%r abstention=%r compliant=%d/%d"
              % (arm, s["tp"], s["fp"], s["fn"], s["tn"], s["flag_bad"],
                 s["precision"], s["recall"], s["abstention_rate"],
                 s["schema_compliant_readings"], s["n_readings"]))
    comp = result["paired"]["comparisons"]["%s-%s" % PRIMARY_COMPARISON]
    print("primary recall(BP)-recall(B)=%r CI95=[%r, %r] (seed=%d B=%d)"
          % (comp["recall_diff"], comp["bootstrap_ci95"]["recall_diff"]["low"],
             comp["bootstrap_ci95"]["recall_diff"]["high"],
             BOOTSTRAP_SEED, N_BOOTSTRAP))
    n_readings = sum(result["arms"][arm]["n_readings"] for arm in ARMS)
    cp = result["paired"]["comparisons"]["CP-B"]
    summary = {
        "n_readings": n_readings,
        "arms": {arm: {"n_readings": result["arms"][arm]["n_readings"]}
                 for arm in ARMS},
        "primary": {
            "recall_diff": comp["recall_diff"],
            "ci_low": comp["bootstrap_ci95"]["recall_diff"]["low"],
            "ci_high": comp["bootstrap_ci95"]["recall_diff"]["high"],
        },
        "abstention_cp": {
            "diff": cp["abstention_diff"],
            "ci_low": cp["bootstrap_ci95"]["abstention_diff"]["low"],
            "ci_high": cp["bootstrap_ci95"]["abstention_diff"]["high"],
        },
    }
    print(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    return result


# ------------------------------------------------------------------- main
def main(argv: list) -> int:
    argv = list(argv)
    if argv and argv[0] == "check":
        gate = reproduce_gate()
        print("r2 reproduction gate vs %s" % R2_STATS_PATH)
        print("  comparator: ints/strings/bools exact, floats |diff| <= 1e-9")
        if gate["passed"]:
            p = gate["produced"]
            print("  PASS: tp=%d fp=%d fn=%d tn=%d precision=%r recall=%r "
                  "abstention_rate=%r random_baseline=%r"
                  % (p["tp"], p["fp"], p["fn"], p["tn"], p["precision"],
                     p["recall"], p["abstention_rate"], p["random_baseline"]))
            return 0
        for problem in gate["problems"]:
            print("  FAIL %s" % problem)
        return 1
    run_all()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
