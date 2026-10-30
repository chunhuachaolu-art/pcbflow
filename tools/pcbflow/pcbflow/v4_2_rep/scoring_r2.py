"""REP-R2 deterministic scoring, main side (three-arm multi-session replicate).

Implements the frozen metric caliber of PREREG-REP-R2.md sections 7/8
(out/v4.2-rep-r2/PREREG-REP-R2.md, v1 2026-10-01), reusing the frozen
REP-R1/r2 primitives of ``pcbflow.v4_2_rep.scoring`` read-only (this
module adds a file; it never modifies the sibling module):

1. ``reproduce_gate()`` / the hard pre-emission gate inside ``score_r2()``
   -- pipeline regression via the existing
   ``pcbflow.v4_2_rep.scoring.reproduce_r2()`` over
   out/v4.2-seat-r2/m1-readings/ + the frozen GT: must reproduce
   out/v4.2-seat-r2/m1-stats.json value-for-value (ints exact, floats
   within 1e-9) BEFORE any REP-R2 number is emitted (PREREG section 8.2;
   tp=20 fp=6 fn=13 tn=84 precision=0.7692307692307693
   recall=0.6060606060606061 abstention_rate=0.0
   random_baseline=0.2682926829268293).

2. ``score_r2()`` -- same per-route confusion caliber over
   out/v4.2-rep-r2/readings/<A|B|C>/rep<k>/p<NN>.json (file schema
   v4.2-rep-r2-reading/1; "-rN" retry files resolve to the highest N per
   pid, R1 ``_resolve_reading_files`` semantics), 3 arms x 3 reps x 16
   pids = 144 readings, 369 route judgments per arm:
     tp = flag_bad & improvable          fp = flag_bad & not improvable
     fn = not flagged & improvable       (includes abstained improvable)
     tn = not flagged & not improvable   (includes abstained non-improvable)
   precision = tp/(tp+fp)  recall = tp/(tp+fn)
   abstention_rate = abstain verdicts / n_routes
   random_baseline = improvable judgments / n_routes
   Stratified per rep (3 x 123), per session (6 = rep x batch, batch one
   = p01-p08 / batch two = p09-p16), per scenario (16, pooled across the
   three reps -- also the bootstrap cluster counts).

3. Paired cluster bootstrap (PREREG section 8.1): primary comparison
   recall(B)-recall(A), secondary recall(C)-recall(A), recall(B)-recall(C);
   resample unit = the 16 scenario clusters (counts pooled across the 3
   reps per arm), B=10000 replicates, seed 20261001, ONE shared index
   list per replicate applied to all three arms, percentile CI95 at
   2.5/97.5 (linear interpolation on order statistics).  Undefined
   replicates (zero denominator) are excluded from the percentiles and
   counted in n_undefined; nothing is imputed.  Rep-level paired diffs
   (3 points per comparison, descriptive, no inference) are reported as
   raw values.  The historical r2 acceptance band
   (precision >= max(2*random_baseline, 0.4) and abstention <= 0.5) is a
   REPORT ONLY reference per arm -- REP-R2 sets no gate (PREREG section
   7 / J4).

Outputs (canonical JSON, written only inside out/v4.2-rep-r2/):
   arm-a-stats.json, arm-b-stats.json, arm-c-stats.json,
   session-stats.json (18-session flat table), paired-stats.json.

Determinism: fixed seeds, no wall-clock, no host state, stdlib only --
identical inputs yield byte-identical files.

``run_all()`` ends with one line, ``print(json.dumps(summary))`` (keys:
n_readings, arms.<arm>.n_readings, primary.recall_diff/ci_low/ci_high).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from pcbflow.v4_2_rep import scoring  # frozen r1/r2 primitives, read-only reuse

# ------------------------------------------------------------- frozen paths
# ROOT = .../tools/pcbflow  (this file: ROOT/pcbflow/v4_2_rep/scoring_r2.py)
ROOT = Path(__file__).resolve().parents[2]

GT_PATH = scoring.GT_PATH
PACKAGE_META_PATH = scoring.PACKAGE_META_PATH
R2_STATS_PATH = scoring.R2_STATS_PATH

REP_OUT_DIR = ROOT / "out" / "v4.2-rep-r2"
READINGS_ROOT = REP_OUT_DIR / "readings"
ARM_STATS_PATHS = {
    "A": REP_OUT_DIR / "arm-a-stats.json",
    "B": REP_OUT_DIR / "arm-b-stats.json",
    "C": REP_OUT_DIR / "arm-c-stats.json",
}
SESSION_STATS_PATH = REP_OUT_DIR / "session-stats.json"
PAIRED_STATS_PATH = REP_OUT_DIR / "paired-stats.json"

# -------------------------------------------------------- frozen constants
ARMS = ("A", "B", "C")
REPS = (1, 2, 3)
N_REPS = len(REPS)
BATCH1_PIDS = frozenset("p%02d" % i for i in range(1, 9))   # p01..p08
BATCH2_PIDS = frozenset("p%02d" % i for i in range(9, 17))  # p09..p16

READING_SCHEMA = "v4.2-rep-r2-reading/1"
ARM_STATS_SCHEMA = "v4.2-rep-r2-arm-stats/1"
SESSION_STATS_SCHEMA = "v4.2-rep-r2-session-stats/1"
PAIRED_STATS_SCHEMA = "v4.2-rep-r2-paired-stats/1"

# PREREG-REP-R2 section 8.1: primary first, then the two secondary reads.
COMPARISONS = (("B", "A"), ("C", "A"), ("B", "C"))
PRIMARY_COMPARISON = COMPARISONS[0]

BOOTSTRAP_SEED = 20261001  # PREREG-REP-R2 section 8.1
N_BOOTSTRAP = 10000
CI_LO = scoring.CI_LO  # 2.5
CI_HI = scoring.CI_HI  # 97.5

_R2_BAND_NOTE = ("historical r2 acceptance band, reported only -- REP-R2 "
                 "sets no gate (PREREG-REP-R2 section 7 / J4)")

# reuse from the frozen sibling module: _load_json, _write_canonical,
# _resolve_reading_files, _check_structure, validate_six_rules, _confusion,
# _percentile, _ratio, _r2_band constants, check_r2_reproduction.
_load_json = scoring._load_json
_write_canonical = scoring._write_canonical
_resolve_reading_files = scoring._resolve_reading_files
_check_structure = scoring._check_structure
validate_six_rules = scoring.validate_six_rules
_confusion = scoring._confusion
_percentile = scoring._percentile
_ratio = scoring._ratio


# ----------------------------------------------------------------- helpers
def _gt_tables(gt_path: Path = GT_PATH,
               package_meta_path: Path = PACKAGE_META_PATH):
    """(pid->sid meta, sid->(route_id->improvable), sorted sids).

    Same contract as ``scoring._gt_tables`` with the package-meta path
    parameterized (the sibling hard-codes it); the real-data path is
    pinned by the reproduce gate, which runs through the sibling module.
    """
    meta = _load_json(package_meta_path)
    gt = _load_json(gt_path)
    scenarios = gt["scenarios"]
    route_impr = {
        sid: {rid: bool(r["improvable"]) for rid, r in sc["per_route"].items()}
        for sid, sc in scenarios.items()
    }
    if set(meta) != {"p%02d" % i for i in range(1, len(meta) + 1)}:
        raise RuntimeError("package-meta pid set is not a contiguous p01..pNN run")
    sids = [meta[pid]["sid"] for pid in sorted(meta)]
    if len(set(sids)) != len(sids) or set(sids) != set(scenarios):
        raise RuntimeError("pid->sid mapping is not a bijection onto GT scenarios")
    return meta, route_impr, sorted(scenarios)


def _reproduce_r2_param(gt_path: Path, package_meta_path: Path,
                        readings_dir: Path) -> dict:
    """Parameterized twin of ``scoring.reproduce_r2`` (same primitives).

    The sibling function accepts a ``package_meta_path`` argument but
    threads it to nothing -- ``scoring._gt_tables`` always loads the
    frozen real meta -- so the fully-redirectable twin re-runs the
    identical pipeline through the sibling's own primitives
    (_resolve_reading_files/_check_structure/_confusion/_per_scenario/
    _pool/_r2_band) with only the meta path threaded.  The REAL gate
    never uses this twin: it calls ``scoring.reproduce_r2()`` itself.
    """
    meta, route_impr, sids_sorted = _gt_tables(gt_path, package_meta_path)
    readings_dir = Path(readings_dir)
    chosen, _superseded = _resolve_reading_files(readings_dir, sorted(meta))
    pid_conf = {}
    for pid in sorted(meta):
        sid = meta[pid]["sid"]
        data = _load_json(readings_dir / chosen[pid])
        flags = _check_structure(data, pid, set(route_impr[sid]))
        pid_conf[pid] = _confusion(flags, route_impr[sid])
    pooled = scoring._pool(scoring._per_scenario(pid_conf, meta), sids_sorted)
    if pooled["n_routes"] != sum(m["n_routes"] for m in meta.values()):
        raise RuntimeError("r2 reading route count disagrees with package-meta")
    gate = scoring._r2_band(pooled["precision"], pooled["abstention_rate"],
                            pooled["random_baseline"])
    return {
        "schema": scoring.R2_STATS_SCHEMA,
        "seed": scoring.R2_REGISTERED_SEED,
        "n_routes": pooled["n_routes"],
        "tp": pooled["tp"],
        "fp": pooled["fp"],
        "fn": pooled["fn"],
        "tn": pooled["tn"],
        "precision": pooled["precision"],
        "recall": pooled["recall"],
        "abstention_rate": pooled["abstention_rate"],
        "random_baseline": pooled["random_baseline"],
        "gate": {
            "precision_min": gate["precision_min"],
            "abstention_max": gate["abstention_max"],
            "passed": (gate["precision_meets_band"]
                       and gate["abstention_within_band"]),
        },
    }


def reproduce_gate(r2_stats_path: Path = None,
                   gt_path: Path = None,
                   package_meta_path: Path = None,
                   readings_dir: Path = None) -> dict:
    """PREREG section 8.2 pre-emission gate (ints exact, floats <= 1e-9).

    With no arguments it is the frozen real gate through the existing
    ``pcbflow.v4_2_rep.scoring.reproduce_r2()`` (per PREREG section 8.2
    and the task charter); explicit paths select the parameterized twin
    (synthetic-fixture testing only).
    """
    if r2_stats_path is None and gt_path is None and \
            package_meta_path is None and readings_dir is None:
        passed, problems, produced, _expected = scoring.check_r2_reproduction()
        return {"passed": passed, "problems": problems, "produced": produced}
    produced = _reproduce_r2_param(
        gt_path if gt_path is not None else GT_PATH,
        package_meta_path if package_meta_path is not None
        else PACKAGE_META_PATH,
        readings_dir if readings_dir is not None else scoring.R2_READINGS_DIR)
    expected = _load_json(r2_stats_path if r2_stats_path is not None
                          else R2_STATS_PATH)
    problems: list = []
    scoring._compare(produced, expected, "$", problems)
    return {"passed": not problems, "problems": problems,
            "produced": produced}


def _batch_of(pid: str) -> int:
    if pid in BATCH1_PIDS:
        return 1
    if pid in BATCH2_PIDS:
        return 2
    raise RuntimeError("pid %r is neither batch one (p01-p08) nor two (p09-p16)"
                       % pid)


def _reading_dir(readings_root: Path, arm: str, rep: int) -> Path:
    return Path(readings_root) / arm / ("rep%d" % rep)


def load_readings(readings_root: Path, meta: dict, route_impr: dict):
    """Resolve, validate and confuse every reading of the 3x3x|pid| grid.

    Returns (confusions, chosen_files, superseded) with
      confusions[arm][rep][pid] = confusion dict   (r2 caliber)
      chosen_files[arm][rep][pid] = filename actually consumed
      superseded[arm][rep][pid]   = superseded '-rN' filenames (when any)
    Fail-closed: any structural/six-rule violation raises (PREREG
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
            directory = _reading_dir(readings_root, arm, rep)
            chosen, sup = _resolve_reading_files(directory, pids)
            conf = {}
            for pid in pids:
                sid = meta[pid]["sid"]
                route_set = set(route_impr[sid])
                data = _load_json(directory / chosen[pid])
                flags = _check_structure(data, pid, route_set,
                                         expect_arm=arm,
                                         expect_schema=READING_SCHEMA)
                if data.get("rep") != rep or \
                        isinstance(data.get("rep"), bool):
                    raise RuntimeError("%s rep%d/%s: rep field %r != %r"
                                       % (arm, rep, pid, data.get("rep"), rep))
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


_CONF_KEYS = ("tp", "fp", "fn", "tn", "abstain", "n_routes")


def _sum_confs(confs: list) -> dict:
    totals = {k: 0 for k in _CONF_KEYS}
    for conf in confs:
        for k in _CONF_KEYS:
            totals[k] += conf[k]
    return totals


def _row(conf: dict) -> dict:
    """Confusion counts + rates in the r2 caliber (None when undefined).

    improvable == tp + fn and flag_bad == tp + fp are caliber identities
    (every improvable route is either flagged or not; every flag_bad
    lands in tp or fp); abstained routes sit inside fn/tn per PREREG
    section 7.
    """
    tp, fp, fn, tn = conf["tp"], conf["fp"], conf["fn"], conf["tn"]
    n = conf["n_routes"]
    return {
        "n_routes": n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "improvable": tp + fn,
        "flag_bad": tp + fp,
        "abstain": conf["abstain"],
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "abstention_rate": _ratio(conf["abstain"], n),
    }


def _cluster_rows(confusions: dict, meta: dict, sids_sorted: list) -> dict:
    """Per-arm per-scenario counts pooled across the 3 reps (PREREG 8.1).

    Returns {arm: [row, ...] in identical sorted-sid order} where each
    row is the summed confusion of that arm's three rep readings of the
    scenario (bootstrap cluster counts).
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
    imputed (R1 frozen convention, PREREG section 8.1).
    """
    arms = tuple(cluster_rows)
    if not arms:
        raise RuntimeError("no arms supplied to the bootstrap")
    k = len(cluster_rows[arms[0]])
    for arm in arms[1:]:
        if len(cluster_rows[arm]) != k:
            raise RuntimeError("arm cluster rows are not aligned")
    stat_keys = []
    for arm in arms:
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
        for arm in arms:
            tot = {f: 0 for f in _CONF_KEYS}
            for i in idx:
                row = cluster_rows[arm][i]
                for f in _CONF_KEYS:
                    tot[f] += row[f]
            totals[arm] = tot
        recall = {arm: _ratio(totals[arm]["tp"],
                              totals[arm]["tp"] + totals[arm]["fn"])
                  for arm in arms}
        precision = {arm: _ratio(totals[arm]["tp"],
                                 totals[arm]["tp"] + totals[arm]["fp"])
                     for arm in arms}
        abstention = {arm: _ratio(totals[arm]["abstain"],
                                  totals[arm]["n_routes"])
                      for arm in arms}
        for stat, table in (("recall", recall), ("precision", precision),
                            ("abstention", abstention)):
            for arm in arms:
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


# ------------------------------------------------------------- score_r2()
def score_r2(gt_path: Path = GT_PATH,
             package_meta_path: Path = PACKAGE_META_PATH,
             readings_root: Path = READINGS_ROOT,
             out_dir: Path = REP_OUT_DIR,
             reproduce: bool = True,
             reproduce_kwargs: dict = None) -> dict:
    """Gate on the r2 reproduction, then score all three arms + pairing.

    Writes arm-{a,b,c}-stats.json, session-stats.json, paired-stats.json
    (canonical JSON) inside ``out_dir`` (default out/v4.2-rep-r2/) and
    returns the full result dict.  ``reproduce_kwargs`` redirects the
    gate's frozen inputs (synthetic-fixture testing only).
    """
    gate = None
    if reproduce:
        gate = reproduce_gate(**(reproduce_kwargs or {}))
        if not gate["passed"]:
            raise RuntimeError(
                "r2 reproduction gate FAILED -- REP-R2 statistics pipeline "
                "is buggy, refusing to emit any REP-R2 number "
                "(PREREG-REP-R2 section 8.2):\n  "
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

    # ---- session flat table (18 rows: arm/rep/batch + rates)
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
        for rep in REPS:
            r_hi = pooled_rows[hi]["per_rep"]["rep%d" % rep]["recall"]
            r_lo = pooled_rows[lo]["per_rep"]["rep%d" % rep]["recall"]
            rep_level["rep%d" % rep] = (None if r_hi is None or r_lo is None
                                        else r_hi - r_lo)
        comparisons["%s-%s" % (hi, lo)] = {
            "role": role,
            "direction": "arm %s minus arm %s (PREREG-REP-R2 section 1)" % (hi, lo),
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
            "rep_level_recall_diff": rep_level,
        }
    paired = {
        "schema": PAIRED_STATS_SCHEMA,
        "seed": BOOTSTRAP_SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_clusters": len(sids_sorted),
        "cluster_caliber": ("per-arm per-scenario counts pooled across the "
                            "3 reps before resampling (PREREG-REP-R2 "
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
        "n_routes_per_arm": arm_stats["A"]["n_routes"],
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
    result = score_r2()
    for arm in ARMS:
        s = result["arms"][arm]
        print("arm %s: tp=%d fp=%d fn=%d tn=%d flag_bad=%d precision=%r "
              "recall=%r abstention=%r compliant=%d/%d"
              % (arm, s["tp"], s["fp"], s["fn"], s["tn"], s["flag_bad"],
                 s["precision"], s["recall"], s["abstention_rate"],
                 s["schema_compliant_readings"], s["n_readings"]))
    comp = result["paired"]["comparisons"]["%s-%s" % PRIMARY_COMPARISON]
    print("primary recall(B)-recall(A)=%r CI95=[%r, %r] (seed=%d B=%d)"
          % (comp["recall_diff"], comp["bootstrap_ci95"]["recall_diff"]["low"],
             comp["bootstrap_ci95"]["recall_diff"]["high"],
             BOOTSTRAP_SEED, N_BOOTSTRAP))
    n_readings = sum(result["arms"][arm]["n_readings"] for arm in ARMS)
    summary = {
        "n_readings": n_readings,
        "arms": {arm: {"n_readings": result["arms"][arm]["n_readings"]}
                 for arm in ARMS},
        "primary": {
            "recall_diff": comp["recall_diff"],
            "ci_low": comp["bootstrap_ci95"]["recall_diff"]["low"],
            "ci_high": comp["bootstrap_ci95"]["recall_diff"]["high"],
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
