"""A4-INTENTPACK-R1 (REP-R1) deterministic scoring, main side (r2 caliber).

Implements the frozen metric caliber of PREREG-REP-R1.md sections 6/7
(out/v4.2-rep-r1/PREREG-REP-R1.md, v1 2026-09-30):

1. ``reproduce_r2()`` -- pipeline regression: recompute the r2 M1' pooled
   stats from out/v4.2-seat-r2/m1-readings/ against the frozen GT
   (out/v4.2-seat/m1/gt.json) and the pid->sid map
   (out/v4.2-seat/m1/packages/package-meta.json).  Must reproduce
   out/v4.2-seat-r2/m1-stats.json value-for-value (ints exact, floats
   within 1e-9) before any REP-R1 number is emitted (PREREG section 7,
   "r2 chi tongji fuxian jianyan"; regression seed 20260913 registered in
   that file -- the pooled stats themselves consume no randomness).

2. ``score_arms()`` -- same caliber over out/v4.2-rep-r1/arm-{a,b}-readings/
   (file schema v4.2-rep-r1-reading/1; "-rN" retry files resolve to the
   highest N), plus per-arm schema-compliance pid counts (PREREG section 6
   six validation rules) and the paired cluster bootstrap of PREREG
   section 7 (seed 20260930, B=10000, resample unit = the 16 scenarios,
   the SAME resampled index set applied to both arms, percentile CI95 at
   2.5/97.5, no asymptotic approximation).

Caliber (PREREG section 6, wording identical to the r2 file):
  pooled per-route confusion, reading flags x GT per_route improvable:
    tp = flag_bad & improvable          fp = flag_bad & not improvable
    fn = not flagged & improvable       (includes abstained improvable)
    tn = not flagged & not improvable   (includes abstained non-improvable)
  precision = tp/(tp+fp)    recall = tp/(tp+fn)
  abstention_rate = abstain verdicts / n_routes
  random_baseline = improvable routes / n_routes
  r2 band, REPORT ONLY in REP-R1 (no gate, J4):
    precision >= max(2*random_baseline, 0.4) and abstention <= 0.5.

Bootstrap convention for undefined replicates (declared, deterministic):
  a statistic is undefined in a replicate when its denominator is 0
  (recall: no improvable route resampled; precision: no flag_bad
  resampled).  Undefined replicates are EXCLUDED from the percentiles and
  counted in ``n_undefined`` next to every CI.  Nothing is imputed.

Determinism: fixed seeds, no wall-clock, no host state, stdlib only.
Canonical JSON output: sorted keys, indent=1, ensure_ascii=False,
allow_nan=False, trailing newline, LF line endings, UTF-8 -- identical
inputs yield byte-identical files.

This module reads only the frozen inputs named above and writes only
out/v4.2-rep-r1/arm-a-stats.json, arm-b-stats.json, paired-stats.json.
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path

# ------------------------------------------------------------- frozen paths
# ROOT = .../tools/pcbflow  (this file: ROOT/pcbflow/v4_2_rep/scoring.py)
ROOT = Path(__file__).resolve().parents[2]

GT_PATH = ROOT / "out" / "v4.2-seat" / "m1" / "gt.json"
PACKAGE_META_PATH = ROOT / "out" / "v4.2-seat" / "m1" / "packages" / "package-meta.json"
R2_READINGS_DIR = ROOT / "out" / "v4.2-seat-r2" / "m1-readings"
R2_STATS_PATH = ROOT / "out" / "v4.2-seat-r2" / "m1-stats.json"

REP_OUT_DIR = ROOT / "out" / "v4.2-rep-r1"
ARM_READINGS_DIRS = {
    "A": REP_OUT_DIR / "arm-a-readings",
    "B": REP_OUT_DIR / "arm-b-readings",
}
ARM_STATS_PATHS = {
    "A": REP_OUT_DIR / "arm-a-stats.json",
    "B": REP_OUT_DIR / "arm-b-stats.json",
}
PAIRED_STATS_PATH = REP_OUT_DIR / "paired-stats.json"

# -------------------------------------------------------- frozen constants
VERDICTS = ("flag_bad", "no_flag", "abstain")
REASON_CODES = (
    "detour_excess",
    "congestion_crossing",
    "blocks_escape",
    "clearance_risk",
    "suboptimal_layer",
    "uncertain",
)
ENTRY_KEYS = frozenset(("route_id", "verdict", "reason_code", "evidence"))

READING_SCHEMA = "v4.2-rep-r1-reading/1"
ARM_STATS_SCHEMA = "v4.2-rep-r1-arm-stats/1"
PAIRED_STATS_SCHEMA = "v4.2-rep-r1-paired-stats/1"

R2_STATS_SCHEMA = "v4.2-r2-m1-stats/1"
R2_REGISTERED_SEED = 20260913  # mirrors the "seed" field of m1-stats.json

BOOTSTRAP_SEED = 20260930  # PREREG-REP-R1 section 7
N_BOOTSTRAP = 10000
CI_LO = 2.5
CI_HI = 97.5
ABSTENTION_MAX = 0.5
PRECISION_FLOOR = 0.4

_READING_NAME_RE = re.compile(r"^(p\d{2})(?:-r(\d+))?\.json$")


# ----------------------------------------------------------------- helpers
def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _canonical_json_bytes(obj) -> bytes:
    """Canonical deterministic serialization (see module docstring)."""
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      indent=1, allow_nan=False) + "\n"
    return text.encode("utf-8")


def _write_canonical(path: Path, obj) -> None:
    path.write_bytes(_canonical_json_bytes(obj))


def _gt_tables(gt_path: Path = GT_PATH):
    """Return (pid->sid meta, sid->(route_id->improvable), sorted sids)."""
    meta = _load_json(PACKAGE_META_PATH)
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


def _resolve_reading_files(directory: Path, pids):
    """Pick, per pid, the newest reading file ('-rN' retry > base file).

    Returns (pid -> filename, pid -> list of superseded filenames).
    """
    per_pid: dict = {pid: {} for pid in pids}  # pid -> {retry_no: name}
    for entry in sorted(directory.iterdir()):
        if entry.suffix != ".json":
            continue
        m = _READING_NAME_RE.match(entry.name)
        if m is None:
            raise RuntimeError("unrecognized reading filename %s in %s"
                               % (entry.name, directory))
        pid, rno = m.group(1), int(m.group(2) or 0)
        if pid not in per_pid:
            raise RuntimeError("reading %s matches no package pid" % entry.name)
        if rno in per_pid[pid]:
            raise RuntimeError("duplicate retry number for %s: %s"
                               % (pid, entry.name))
        per_pid[pid][rno] = entry.name
    chosen, superseded = {}, {}
    for pid in pids:
        if not per_pid[pid]:
            raise RuntimeError("no reading file for %s in %s" % (pid, directory))
        top = max(per_pid[pid])
        chosen[pid] = per_pid[pid][top]
        rest = [per_pid[pid][r] for r in sorted(per_pid[pid]) if r != top]
        if rest:
            superseded[pid] = rest
    return chosen, superseded


def _check_structure(data, pid: str, route_set, *, expect_arm=None,
                     expect_schema=None):
    """Hard integrity checks (fail-closed); returns the flags list."""
    if not isinstance(data, dict):
        raise RuntimeError("%s: reading is not a JSON object" % pid)
    if data.get("pid") != pid:
        raise RuntimeError("pid field %r != filename pid %r"
                           % (data.get("pid"), pid))
    if expect_arm is not None and data.get("arm") != expect_arm:
        raise RuntimeError("%s: arm field %r != expected %r"
                           % (pid, data.get("arm"), expect_arm))
    if expect_schema is not None and data.get("schema") != expect_schema:
        raise RuntimeError("%s: schema field %r != expected %r"
                           % (pid, data.get("schema"), expect_schema))
    flags = data.get("flags")
    if not isinstance(flags, list):
        raise RuntimeError("%s: 'flags' is not a list" % pid)
    for fl in flags:
        if not isinstance(fl, dict) or not isinstance(fl.get("route_id"), str):
            raise RuntimeError("%s: malformed flag entry" % pid)
        if fl["route_id"] not in route_set:
            raise RuntimeError("%s: route_id %r not in package route set"
                               % (pid, fl["route_id"]))
    rids = [fl["route_id"] for fl in flags]
    if len(rids) != len(set(rids)):
        raise RuntimeError("%s: duplicate route_id in reading" % pid)
    if set(rids) != route_set:
        raise RuntimeError("%s: route_id set != package route set" % pid)
    return flags


def validate_six_rules(flags, route_set) -> list:
    """PREREG-REP-R1 section 6, the six frozen validation rules.

    Returns a list of violation strings (empty == compliant).
    """
    problems = []
    rids = [fl.get("route_id") if isinstance(fl, dict) else None for fl in flags]
    # rules 1+2: exactly one entry per route, route_id set equality
    if len(flags) != len(route_set) or set(r for r in rids if isinstance(r, str)) != route_set:
        problems.append("rule1/2: %s entries vs %s routes / route_id set mismatch"
                        % (len(flags), len(route_set)))
    for i, fl in enumerate(flags):
        if not isinstance(fl, dict):
            problems.append("entry[%d]: not an object" % i)
            continue
        # rule 6: exactly the four keys, all non-empty strings
        if set(fl) != ENTRY_KEYS:
            problems.append("entry[%d]: key set %s != four-key contract"
                            % (i, sorted(fl)))
            continue
        if not all(isinstance(fl[k], str) and fl[k] != "" for k in ENTRY_KEYS):
            problems.append("entry[%d]: a contract value is not a non-empty string" % i)
            continue
        # rule 3: verdict enum
        if fl["verdict"] not in VERDICTS:
            problems.append("entry[%d]: verdict %r not in enum" % (i, fl["verdict"]))
        # rule 4: reason_code enum
        if fl["reason_code"] not in REASON_CODES:
            problems.append("entry[%d]: reason_code %r not in enum"
                            % (i, fl["reason_code"]))
        # rule 5: flag_bad needs non-empty evidence (implied by rule 6's
        # non-empty strings, checked explicitly for caliber fidelity)
        if fl["verdict"] == "flag_bad" and fl["evidence"].strip() == "":
            problems.append("entry[%d]: flag_bad with empty evidence" % i)
    return problems


def _confusion(flags, route_impr: dict) -> dict:
    """Pooled-caliber confusion for one reading (structural checks applied)."""
    tp = fp = fn = tn = abstain = 0
    for fl in flags:
        verdict = fl["verdict"]
        if verdict not in VERDICTS:
            raise RuntimeError("unknown verdict %r" % verdict)
        improvable = route_impr[fl["route_id"]]
        if verdict == "flag_bad":
            if improvable:
                tp += 1
            else:
                fp += 1
        else:
            if verdict == "abstain":
                abstain += 1
            if improvable:
                fn += 1
            else:
                tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "abstain": abstain,
            "n_routes": len(flags)}


def _per_scenario(pid_conf: dict, meta: dict) -> dict:
    """pid-keyed confusions -> sid-keyed rows (adds GT improvable count)."""
    rows = {}
    for pid, conf in pid_conf.items():
        sid = meta[pid]["sid"]
        if sid in rows:
            raise RuntimeError("two pids map to scenario %s" % sid)
        rows[sid] = conf
    return rows


def _pool(per_scenario_rows: dict, sids_sorted: list) -> dict:
    totals = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "abstain": 0, "n_routes": 0}
    for sid in sids_sorted:
        for k in totals:
            totals[k] += per_scenario_rows[sid][k]
    tp, fp, fn = totals["tp"], totals["fp"], totals["fn"]
    n = totals["n_routes"]
    return {
        "n_routes": n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": totals["tn"],
        "abstain": totals["abstain"],
        "precision": tp / (tp + fp) if (tp + fp) > 0 else None,
        "recall": tp / (tp + fn) if (tp + fn) > 0 else None,
        "abstention_rate": totals["abstain"] / n if n else None,
        "random_baseline": (tp + fn) / n if n else None,
    }


def _r2_band(precision, abstention_rate, random_baseline) -> dict:
    precision_min = max(2.0 * random_baseline, PRECISION_FLOOR)
    return {
        "note": ("historical r2 acceptance band, reported only -- REP-R1 "
                 "sets no gate (PREREG-REP-R1 section 6 / J4)"),
        "random_baseline": random_baseline,
        "precision_min": precision_min,
        "abstention_max": ABSTENTION_MAX,
        "precision": precision,
        "precision_meets_band": (precision is not None
                                 and precision >= precision_min),
        "abstention_rate": abstention_rate,
        "abstention_within_band": (abstention_rate is not None
                                   and abstention_rate <= ABSTENTION_MAX),
    }


# ----------------------------------------------------- r2 reproduction (1)
def reproduce_r2(gt_path: Path = GT_PATH,
                 package_meta_path: Path = PACKAGE_META_PATH,
                 readings_dir: Path = R2_READINGS_DIR) -> dict:
    """Recompute the r2 M1' pooled stats dict (m1-stats.json shape)."""
    meta, route_impr, sids_sorted = _gt_tables(gt_path)
    chosen, _superseded = _resolve_reading_files(
        readings_dir, sorted(meta))
    pid_conf = {}
    for pid in sorted(meta):
        sid = meta[pid]["sid"]
        data = _load_json(readings_dir / chosen[pid])
        flags = _check_structure(data, pid, set(route_impr[sid]))
        pid_conf[pid] = _confusion(flags, route_impr[sid])
    pooled = _pool(_per_scenario(pid_conf, meta), sids_sorted)
    if pooled["n_routes"] != sum(m["n_routes"] for m in meta.values()):
        raise RuntimeError("r2 reading route count disagrees with package-meta")
    gate = _r2_band(pooled["precision"], pooled["abstention_rate"],
                    pooled["random_baseline"])
    return {
        "schema": R2_STATS_SCHEMA,
        "seed": R2_REGISTERED_SEED,
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


def _compare(actual, expected, path: str, problems: list, tol: float = 1e-9):
    """Recursive comparator: ints/strings/bools exact, floats within tol."""
    if isinstance(expected, bool) or isinstance(actual, bool):
        if not (isinstance(actual, bool) and isinstance(expected, bool)
                and actual == expected):
            problems.append("%s: bool mismatch %r != %r" % (path, actual, expected))
    elif isinstance(expected, dict):
        if not isinstance(actual, dict):
            problems.append("%s: expected object, got %r" % (path, type(actual).__name__))
            return
        for key in sorted(set(expected) | set(actual)):
            if key not in actual:
                problems.append("%s.%s: missing in produced" % (path, key))
            elif key not in expected:
                problems.append("%s.%s: unexpected in produced" % (path, key))
            else:
                _compare(actual[key], expected[key], "%s.%s" % (path, key),
                         problems, tol)
    elif isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)) or isinstance(actual, bool):
            problems.append("%s: expected number, got %r" % (path, actual))
        elif isinstance(expected, float) or isinstance(actual, float):
            if not math.isfinite(abs(actual - expected)) or \
                    abs(actual - expected) > tol:
                problems.append("%s: float diff %g > %g (%r vs %r)"
                                % (path, abs(actual - expected), tol,
                                   actual, expected))
        elif actual != expected:
            problems.append("%s: int mismatch %r != %r" % (path, actual, expected))
    else:
        if actual != expected:
            problems.append("%s: %r != %r" % (path, actual, expected))


def check_r2_reproduction(r2_stats_path: Path = R2_STATS_PATH,
                          **reproduce_kwargs) -> tuple:
    """Return (passed, problems, produced, expected) for the r2 gate."""
    produced = reproduce_r2(**reproduce_kwargs)
    expected = _load_json(r2_stats_path)
    problems: list = []
    _compare(produced, expected, "$", problems)
    return (not problems), problems, produced, expected


# --------------------------------------------------------- bootstrap (3)
def _percentile(values, q: float) -> float:
    """Linear interpolation on order statistics (numpy 'linear' method)."""
    if not values:
        raise RuntimeError("percentile of empty sample")
    s = sorted(values)
    rank = (q / 100.0) * (len(s) - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return float(s[lo])
    frac = rank - lo
    return float(s[lo]) * (1.0 - frac) + float(s[hi]) * frac


def _ratio(num: int, den: int):
    return num / den if den > 0 else None


def _bootstrap_paired(rows_a: list, rows_b: list, seed: int = BOOTSTRAP_SEED,
                      n_boot: int = N_BOOTSTRAP) -> dict:
    """Paired cluster bootstrap over the 16 scenarios (PREREG section 7).

    rows_* are per-scenario confusion rows in identical (sorted-sid) order;
    each replicate draws one shared index list for both arms.
    """
    k = len(rows_a)
    if len(rows_b) != k:
        raise RuntimeError("arm cluster rows are not aligned")
    keys = ("recall_a", "recall_b", "recall_diff",
            "precision_a", "precision_b", "precision_diff",
            "abstention_a", "abstention_b", "abstention_diff")
    samples = {key: [] for key in keys}
    undefined = {key: 0 for key in keys}
    rng = random.Random(seed)
    for _ in range(n_boot):
        idx = [rng.randrange(k) for _ in range(k)]
        sums = {}
        for tag, rows in (("a", rows_a), ("b", rows_b)):
            tot = {"tp": 0, "fp": 0, "fn": 0, "abstain": 0, "n_routes": 0}
            for i in idx:
                row = rows[i]
                for field in tot:
                    tot[field] += row[field]
            sums[tag] = tot
        rec = {tag: _ratio(sums[tag]["tp"], sums[tag]["tp"] + sums[tag]["fn"])
               for tag in ("a", "b")}
        pre = {tag: _ratio(sums[tag]["tp"], sums[tag]["tp"] + sums[tag]["fp"])
               for tag in ("a", "b")}
        abr = {tag: _ratio(sums[tag]["abstain"], sums[tag]["n_routes"])
               for tag in ("a", "b")}
        for key, pair in (("recall", rec), ("precision", pre),
                          ("abstention", abr)):
            for tag in ("a", "b"):
                val = pair[tag]
                if val is None:
                    undefined["%s_%s" % (key, tag)] += 1
                else:
                    samples["%s_%s" % (key, tag)].append(val)
            if pair["a"] is None or pair["b"] is None:
                undefined["%s_diff" % key] += 1
            else:
                samples["%s_diff" % key].append(pair["b"] - pair["a"])
    ci = {}
    for key in keys:
        ci[key] = {
            "low": _percentile(samples[key], CI_LO),
            "high": _percentile(samples[key], CI_HI),
            "n_defined": len(samples[key]),
            "n_undefined": undefined[key],
        }
    return ci


# ------------------------------------------------------------ score_arms
def score_arms(rep_out_dir: Path = REP_OUT_DIR,
               gt_path: Path = GT_PATH) -> dict:
    """Score both arms + paired bootstrap; write the three stats JSONs."""
    meta, route_impr, sids_sorted = _gt_tables(gt_path)
    arm_stats = {}
    cluster_rows = {}
    for arm, letter in (("a", "A"), ("b", "B")):
        readings_dir = rep_out_dir / ("arm-%s-readings" % arm)
        chosen, superseded = _resolve_reading_files(readings_dir, sorted(meta))
        pid_conf, violations = {}, []
        for pid in sorted(meta):
            sid = meta[pid]["sid"]
            route_set = set(route_impr[sid])
            data = _load_json(readings_dir / chosen[pid])
            flags = _check_structure(data, pid, route_set,
                                     expect_arm=letter,
                                     expect_schema=READING_SCHEMA)
            problems = validate_six_rules(flags, route_set)
            if problems:
                violations.extend("[%s] %s" % (pid, p) for p in problems)
            pid_conf[pid] = _confusion(flags, route_impr[sid])
        if violations:
            # PREREG section 9: a final non-compliant reading = stop-the-line
            # escalation; scoring it has no preregistered caliber.
            raise RuntimeError(
                "non-compliant readings present, refusing to score:\n  "
                + "\n  ".join(violations))
        rows = _per_scenario(pid_conf, meta)
        for sid in sids_sorted:  # GT improvable count, for the audit table
            rows[sid] = dict(rows[sid])
            rows[sid]["improvable"] = sum(1 for v in route_impr[sid].values() if v)
        pooled = _pool(rows, sids_sorted)
        stats = {
            "schema": ARM_STATS_SCHEMA,
            "arm": letter,
            "n_scenarios": len(sids_sorted),
            "n_routes": pooled["n_routes"],
            "tp": pooled["tp"],
            "fp": pooled["fp"],
            "fn": pooled["fn"],
            "tn": pooled["tn"],
            "precision": pooled["precision"],
            "recall": pooled["recall"],
            "abstention_rate": pooled["abstention_rate"],
            "random_baseline": pooled["random_baseline"],
            # non-compliant readings raise above (PREREG section 9
            # stop-the-line), so every scored pid is compliant by here
            "schema_compliant_pids": len(meta),
            "schema_compliance_rate": len(meta) / len(meta),
            "reading_files": chosen,
            "per_scenario": {
                sid: {k: rows[sid][k] for k in
                      ("n_routes", "improvable", "tp", "fp", "fn", "tn",
                       "abstain")}
                for sid in sids_sorted
            },
        }
        if superseded:
            stats["superseded_retries"] = superseded
        arm_stats[letter] = stats
        cluster_rows[letter] = [rows[sid] for sid in sids_sorted]

    pa, pb = arm_stats["A"], arm_stats["B"]
    paired = {
        "schema": PAIRED_STATS_SCHEMA,
        "seed": BOOTSTRAP_SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_clusters": len(sids_sorted),
        "resample_unit": "scenario (cluster bootstrap, PREREG-REP-R1 section 7)",
        "paired_design": ("each replicate draws ONE scenario index list "
                          "applied to both arms"),
        "percentile_method": ("linear interpolation on order statistics "
                              "(numpy 'linear' equivalent)"),
        "undefined_replicate_convention": (
            "a statistic with zero denominator in a replicate (recall: no "
            "improvable route resampled; precision: no flag_bad resampled) "
            "is undefined; undefined replicates are excluded from the "
            "percentiles and counted in n_undefined; nothing is imputed"),
        "n_routes": pa["n_routes"],
        "confusion": {
            "arm_a": {k: pa[k] for k in ("tp", "fp", "fn", "tn")},
            "arm_b": {k: pb[k] for k in ("tp", "fp", "fn", "tn")},
        },
        "point_estimates": {
            "recall_a": pa["recall"],
            "recall_b": pb["recall"],
            "recall_diff": pb["recall"] - pa["recall"],
            "precision_a": pa["precision"],
            "precision_b": pb["precision"],
            "precision_diff": pb["precision"] - pa["precision"],
            "abstention_rate_a": pa["abstention_rate"],
            "abstention_rate_b": pb["abstention_rate"],
            "abstention_diff": pb["abstention_rate"] - pa["abstention_rate"],
        },
        "bootstrap_ci": _bootstrap_paired(cluster_rows["A"], cluster_rows["B"]),
        "r2_band_reference": {
            "arm_a": _r2_band(pa["precision"], pa["abstention_rate"],
                              pa["random_baseline"]),
            "arm_b": _r2_band(pb["precision"], pb["abstention_rate"],
                              pb["random_baseline"]),
        },
    }

    written = []
    for letter, path in ARM_STATS_PATHS.items():
        out = rep_out_dir / path.name
        _write_canonical(out, arm_stats[letter])
        written.append(out)
    out = rep_out_dir / PAIRED_STATS_PATH.name
    _write_canonical(out, paired)
    written.append(out)
    return {"arm_a": arm_stats["A"], "arm_b": arm_stats["B"],
            "paired": paired, "written": written}


# ------------------------------------------------------------------- main
def _self_test() -> int:
    ok, problems, produced, expected = check_r2_reproduction()
    print("r2 reproduction check vs %s" % R2_STATS_PATH)
    print("  comparator: ints/strings/bools exact, floats |diff| <= 1e-9")
    if ok:
        print("  PASS: tp=%d fp=%d fn=%d tn=%d precision=%r recall=%r "
              "abstention_rate=%r random_baseline=%r gate.passed=%r"
              % (produced["tp"], produced["fp"], produced["fn"],
                 produced["tn"], produced["precision"], produced["recall"],
                 produced["abstention_rate"], produced["random_baseline"],
                 produced["gate"]["passed"]))
    else:
        for p in problems:
            print("  FAIL %s" % p)
    # internal consistency: percentile routine vs numpy, when available
    try:
        import numpy as np
    except ImportError:
        print("  percentile cross-check vs numpy: SKIPPED (numpy absent)")
        return 0 if ok else 1
    rng = random.Random(7)
    sample = [rng.random() for _ in range(10000)]
    worst = 0.0
    for q in (2.5, 97.5, 50.0, 0.0, 100.0):
        d = abs(_percentile(sample, q) - float(np.percentile(sample, q)))
        worst = max(worst, d)
    ok_np = worst <= 1e-12
    print("  percentile cross-check vs numpy.percentile: %s (worst |diff|=%.3g)"
          % ("PASS" if ok_np else "FAIL", worst))
    return 0 if (ok and ok_np) else 1


def main(argv: list) -> int:
    rc = _self_test()
    if rc != 0:
        return rc
    if "score" in argv:
        result = score_arms()
        for arm in ("A", "B"):
            s = result["arm_%s" % arm.lower()]
            print("arm %s: tp=%d fp=%d fn=%d tn=%d precision=%r recall=%r "
                  "abstention=%r compliant_pids=%d/%d"
                  % (arm, s["tp"], s["fp"], s["fn"], s["tn"], s["precision"],
                     s["recall"], s["abstention_rate"],
                     s["schema_compliant_pids"], s["n_scenarios"]))
        pe = result["paired"]["point_estimates"]
        print("paired: recall_diff=%r precision_diff=%r abstention_diff=%r"
              % (pe["recall_diff"], pe["precision_diff"], pe["abstention_diff"]))
        import hashlib
        for path in result["written"]:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            print("wrote %s sha256=%s" % (path, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
