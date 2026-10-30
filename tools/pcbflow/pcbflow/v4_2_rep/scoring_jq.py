"""JUDGE-QUAL-R1 deterministic scoring, main side (judge qualification gate).

Implements the frozen metric caliber of PREREG-JUDGE-QUAL-R1-FROZEN.md
sections 3.7/3.8 (E:/ZCodeData/tmp/optimap-exec-r7/prereg/
PREREG-JUDGE-QUAL-R1-FROZEN.md, frozen 2026-10-11), reusing the frozen
r1/r2/R2/R3 primitives of ``pcbflow.v4_2_rep.scoring`` /
``pcbflow.v4_2_rep.scoring_r2`` read-only (this module adds a file; it
never modifies the siblings).  Arms Q (B-v1 structured intent packs) and
CTR (r2 SVG form), 2 arms x 3 reps x 16 pids = 96 readings, 369 route
judgments per arm, 738 total.

1. ``reproduce_r2()`` / the hard pre-emission gate inside ``score_jq()``
   -- pipeline regression through the existing frozen
   ``pcbflow.v4_2_rep.scoring.reproduce_r2()`` pathway (per PREREG
   section 3.8, identical to the REP-R2/R3 section 8.2 gate): recompute
   from out/v4.2-seat-r2/m1-readings/ + the frozen GT and require
   value-for-value equality with out/v4.2-seat-r2/m1-stats.json (ints
   exact, floats within 1e-9) BEFORE any JUDGE-QUAL number is emitted:
   tp=20 fp=6 fn=13 tn=84 precision=0.7692307692307693
   recall=0.6060606060606061 abstention_rate=0.0
   random_baseline=0.2682926829268293 gate.passed=true.  Any mismatch =
   stop-the-line repair (section 3.11 line 5).

2. Reading loading -- out/v4.2-judge-qual-r1/readings/<Q|CTR>/rep<k>/
   p<NN>.json, eight-key pcbflow.v4_2-jq-reading/1 (the R3-realized
   shape: arm/model_output/pid/rep/return_raw/schema/ts/validation; the
   judgment is the ``model_output`` flags; ``validation.passed`` must be
   true; "-rN" retry files resolve to the highest N per pid, r1
   ``_resolve_reading_files`` semantics).  Fail-closed on any final
   non-compliant reading (six frozen rules; a non-compliant final has no
   preregistered scoring caliber -- retry protocol and stop-the-line
   escalation live in the batch layer, section 3.11).

3. Section 3.7 metrics, all six items:
   3.7.1 four-cell + three rates per arm pooled over the 369 judgments
   (r2 caliber, wording identical to R2 section 7):
     tp = flag_bad & improvable          fp = flag_bad & not improvable
     fn = not flagged & improvable       (includes abstained improvable)
     tn = not flagged & not improvable   (includes abstained non-improvable)
   precision = tp/(tp+fp)  recall = tp/(tp+fn)
   abstention = abstain verdicts / 369
   random_baseline rb = improvable / 369 = 99/369 = 0.2682926829268293
   (frozen constant asserted on the real-world shape).
   3.7.2 session variance: per arm the 6 session recalls (session =
   rep x batch, batch one p01-p08 / batch two p09-p16) -> sample variance
   s^2 (n-1), std s, range (point estimates; CI from 3.8), plus the
   per-session drift table in the R2 section 4.3 shape (arm/rep/batch x
   tp/fp/fn/tn/precision/recall/abstain_rate).
   3.7.3 collapse -- hard: session recall == 0.0000, OR (session
   flag_bad total <= 2 AND tp == 0); soft: session recall < 0.5 x that
   arm's pooled recall; rates = counts/6, hard/soft reported separately.
   3.7.4 calibration -- ECE = not_available (the contract has no numeric
   confidence output); frozen caliber = verdict three-state conditional
   improvable rates P(imp|flag_bad) (= precision), P(imp|abstain),
   P(imp|no_flag), with the flag_bad >= no_flag monotonicity as the
   descriptive calibration read; reason_code six-code sublayer
   improvable rates as a descriptive appendix; no numeric gate.
   3.7.5 schema compliance = readings passing the six frozen validation
   rules / 48 per arm (fail-closed finals => 48/48 whenever scoring
   proceeds); first-attempt compliance from the R3-shape validation
   block is co-reported descriptively.
   3.6 stratification: model = constant layer column + note; reasoning
   effort = not_available (never filled with 0/default); board family
   (cal-f12 x8 / hol-f6 x4 / hol-f8 x4) x arm: five indicators
   (n_routes, improvable rate, precision, recall, abstention) + the
   calibration conditional rates per family.

4. Section 3.8 statistics: paired cluster bootstrap with cluster = the
   16 scenarios pooled across the 3 reps (never 48 scenario x rep
   clusters); ``rng = random.Random(20261011)``; B = 10000; each
   replicate draws ``idx = [rng.randrange(16) for _ in range(16)]``
   (with replacement) applied to BOTH arms; statistics = each arm's
   recall/precision/abstention and the Q-CTR diffs; CI95 = percentiles
   2.5/97.5 (linear interpolation on order statistics); undefined
   replicates (zero denominator) are excluded from the percentiles and
   counted in n_undefined, nothing imputed.  Session-variance parameter
   bootstrap (section 3.8 main statistic): inside the SAME replicate
   machinery, each of the 6 session recalls* is recomputed on the drawn
   scenario multiset restricted to that session's batch, using that
   rep's readings of the drawn scenarios; s2*/s*/range* follow; a
   replicate in which any of the 6 session recalls is undefined makes
   the variance parameter undefined for that arm (excluded + counted).
   Rep-level Q-CTR diffs (3 raw points, descriptive, no inference).

5. Section 3.10 qualification gate G1-G5 with the frozen values
   (user ruling 2026-10-11 "1 an recommendation"):
   G1  Q pooled precision >= max(2*rb, 0.4) (= 0.5366 on rb 0.2683)
       AND bootstrap CI95 lower bound >= 0.40
   G2  Q pooled abstention <= 0.5
   G3  Q hard collapse rate = 0/6
   G4  Q session recall range <= 0.35 (or s <= 0.10)
   G5  P(imp|flag_bad) >= P(imp|no_flag) (Q pooled)
   all-pass = judge qualification holds (usable as a routing evidence
   source; still not a production sign-off).  Any miss = judge stays
   shadow/diagnostic, filed as-is -- a legal negative result that
   triggers no rework (section 3.0).  Undefined inputs fail closed.

6. ``scan_pathd_references()`` -- the CTR-arm path-d disclosure channel
   (PREREG section 3.4 / R2 section 4.6 full clause): deterministic
   post-reading evidence scan with the four R2-report frozen patterns
   (literal 'd="M', 'path[- ]?d' case-insensitive, colon-d-M, SVG
   command string with space/comma variants); Q is scanned under the
   same caliber as the negative control (expected 0).  Disclosure only:
   no gate, no deletion, no exclusion, no stop-the-line.

7. ``verify_templates()`` -- pins out/v4.2-judge-qual-r1/templates.json
   to the frozen R1 corpus byte-for-byte: q_system/ctr_system equal to
   the (per-arm identical) frozen system text; q_head/q_tail equal to
   the longest common prefix/suffix of the 16 frozen user texts;
   user = head + middle + tail reconstructs all 16 packs exactly;
   per-pid sha256 anchors match; the blinding regex hits none of the
   six template strings (inherited from the frozen packs' zero-hit);
   the output contract names exactly the eight reading keys; the
   ``===PACK pNN===`` subject-output marker contract (dispatch layer)
   is present and self-consistent, and the marker never appears inside
   the six frozen template strings.

Outputs (canonical JSON, written only inside out/v4.2-judge-qual-r1/):
arm-q-stats.json, arm-ctr-stats.json, session-stats.json (12-session
flat drift table), paired-stats.json, qualification-gate.json.

Determinism: fixed seeds, no wall-clock, no host state, stdlib only --
identical inputs yield byte-identical files (reading ``ts`` fields are
input data and never copied into any output).

``run_all()`` ends with one line, ``print(json.dumps(summary))`` (keys:
n_readings, arms.<arm>.n_readings, qualification.passed,
qualification.gates_failed).
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

from pcbflow.v4_2_rep import scoring      # frozen r1/r2 primitives, read-only
from pcbflow.v4_2_rep import scoring_r2   # frozen REP-R2 layer, read-only

# ------------------------------------------------------------- frozen paths
# ROOT = .../tools/pcbflow  (this file: ROOT/pcbflow/v4_2_rep/scoring_jq.py)
ROOT = Path(__file__).resolve().parents[2]

GT_PATH = scoring.GT_PATH
PACKAGE_META_PATH = scoring.PACKAGE_META_PATH
R2_STATS_PATH = scoring.R2_STATS_PATH   # out/v4.2-seat-r2/m1-stats.json

JQ_OUT_DIR = ROOT / "out" / "v4.2-judge-qual-r1"
READINGS_ROOT = JQ_OUT_DIR / "readings"
TEMPLATES_PATH = JQ_OUT_DIR / "templates.json"
ARM_STATS_PATHS = {
    "Q": JQ_OUT_DIR / "arm-q-stats.json",
    "CTR": JQ_OUT_DIR / "arm-ctr-stats.json",
}
SESSION_STATS_PATH = JQ_OUT_DIR / "session-stats.json"
PAIRED_STATS_PATH = JQ_OUT_DIR / "paired-stats.json"
QUALIFICATION_GATE_PATH = JQ_OUT_DIR / "qualification-gate.json"

# frozen R1 pack corpora (PREREG section 3.1: byte-identical reuse)
PACKS_B_DIR = ROOT / "out" / "v4.2-rep-r1" / "packs-b"        # Q arm
TASKS_A_DIR = ROOT / "out" / "v4.2-rep-r1" / "tasks-a"        # CTR arm

# -------------------------------------------------------- frozen constants
ARMS = ("Q", "CTR")
REPS = (1, 2, 3)
N_REPS = len(REPS)

READING_SCHEMA = "pcbflow.v4_2-jq-reading/1"   # PREREG section 3.12
READING_KEYS = frozenset(("arm", "model_output", "pid", "rep", "return_raw",
                          "schema", "ts", "validation"))
TEMPLATES_SCHEMA = "pcbflow.v4_2-jq-templates/1"
ARM_STATS_SCHEMA = "pcbflow.v4_2-jq-arm-stats/1"
SESSION_STATS_SCHEMA = "pcbflow.v4_2-jq-session-stats/1"
PAIRED_STATS_SCHEMA = "pcbflow.v4_2-jq-paired-stats/1"
QUALIFICATION_GATE_SCHEMA = "pcbflow.v4_2-jq-qualification-gate/1"

BOOTSTRAP_SEED = 20261011  # PREREG section 3.8 (user ruling: seed frozen)
N_BOOTSTRAP = 10000
CI_LO = scoring.CI_LO  # 2.5
CI_HI = scoring.CI_HI  # 97.5

# PREREG section 3.7.1: rb = 99/369 = 0.2682926829268293 (frozen constant)
RB_FROZEN = 99.0 / 369.0
RB_FROZEN_TEXT = "99/369"

# PREREG section 3.10 gate values (frozen via user ruling 2026-10-11)
G1_PRECISION_CI_LOW_MIN = 0.40
G2_ABSTENTION_MAX = 0.5
G4_RANGE_MAX = 0.35
G4_STD_ALT = 0.10

# PREREG section 3.10 historical reference band, REPORT ONLY (frozen text)
HIST_REFERENCE = {
    "r2_b_recall": 0.7071, "r2_b_ci95": [0.5439, 0.8556],
    "r3_b_recall": 0.7879, "r3_b_ci95": [0.6577, 0.8975],
}

# PREREG section 3.6 board families (cal-f12 x8 / hol-f6 x4 / hol-f8 x4)
FAMILY_COUNTS = {"cal-f12": 8, "hol-f6": 4, "hol-f8": 4}

MODEL_LAYER = "会话驱动 GLM-5.3 (R46 harness-only)"
MODEL_NOTE = "模型维度非变异源（单水平常数层列）；换模型/推理档须重开（路线图 :197）"
REASONING_EFFORT_LAYER = "not_available"
REASONING_EFFORT_NOTE = ("harness 会话驱动无 reasoning_effort 控制，不以 0 或默认值填"
                         "（PREREG-REP-R2.md:41 无采样参数）")

# R2 section 4.6 / REP-R2-REPORT appendix A.6 frozen detection pattern set
PATHD_PATTERNS = (
    ("literal_d_eq_M", re.compile(r'd="M')),
    ("path_d_word", re.compile(r"path[- ]?d", re.IGNORECASE)),
    ("colon_d_M", re.compile(r"\bd:\s*M")),
    ("svg_command_string",
     re.compile(r"M\s*-?\d+(?:\.\d+)?\s*[ ,]\s*-?\d+.*?L\s*-?\d")),
)

# ---- subject output marker contract (batch dispatch layer; ask-pinned) ----
# The subject's per-pack output BEGINS with a dedicated line
# ``===PACK pNN===`` (pNN = pack id), followed by that pack's judgment
# body.  The marker is an orchestration-layer contract: it never enters
# the frozen ask texts (the six template strings) and is enforced by
# ``pcbflow.v4_2_rep.jq_glue.ingest_pack`` (first-line hard check) and
# pinned in templates.json output_contract.pack_marker.
PACK_MARKER_TEMPLATE = "===PACK {pid}==="
PACK_MARKER_PID_PATTERN = r"p[0-9]{2}"
PACK_MARKER_LINE_RE = re.compile(r"^===PACK (p[0-9]{2})===$")
SESSION_ASK_SCHEMA = "pcbflow.v4_2-jq-session-ask/1"

_PATHD_DISPOSAL_NOTE = (
    "R2 §4.6 全款：检测（确定性正则+人工复核双通道）→ 处置（不删读数、不改判读、"
    "不触发停线）→ 豁免（不作门、不作剔除 criterion；仅披露、仅解释链标注）")

_BLIND_RE = re.compile(r"(?:hol-|cal-|dev-|\bf[0-9]\b)")  # inspector semantics

# reuse from the frozen sibling modules
_load_json = scoring._load_json
_write_canonical = scoring._write_canonical
_resolve_reading_files = scoring._resolve_reading_files
_check_structure = scoring._check_structure
validate_six_rules = scoring.validate_six_rules
_percentile = scoring._percentile
_ratio = scoring._ratio

_gt_tables = scoring_r2._gt_tables
_batch_of = scoring_r2._batch_of
_reading_dir = scoring_r2._reading_dir
_CONF_KEYS = scoring_r2._CONF_KEYS   # tp, fp, fn, tn, abstain, n_routes
_row = scoring_r2._row               # counts + improvable/flag_bad + rates


# ----------------------------------------------------------------- helpers
def family_of(sid: str) -> str:
    """sid -> board family (cal-f12 / hol-f6 / hol-f8; section 3.6)."""
    family = sid.rsplit("-", 1)[0]
    if family not in FAMILY_COUNTS:
        raise RuntimeError("unknown board family for sid %r" % sid)
    return family


def reproduce_r2(r2_stats_path: Path = None,
                 gt_path: Path = None,
                 package_meta_path: Path = None,
                 readings_dir: Path = None) -> dict:
    """PREREG section 3.8 pre-emission r2 reproduction gate.

    Returns ``{passed, problems, produced}``.  With no arguments it is
    the frozen real gate through the existing
    ``pcbflow.v4_2_rep.scoring.reproduce_r2()`` pathway (via
    ``scoring_r2.reproduce_gate``): recompute the r2 M1' pooled stats
    from out/v4.2-seat-r2/m1-readings/ against the frozen GT and require
    value-for-value equality with out/v4.2-seat-r2/m1-stats.json (ints
    exact, floats within 1e-9).  Explicit paths select the
    parameterized twin (synthetic-fixture testing only).
    """
    return scoring_r2.reproduce_gate(r2_stats_path=r2_stats_path,
                                     gt_path=gt_path,
                                     package_meta_path=package_meta_path,
                                     readings_dir=readings_dir)


def _flags_from_reading(data, pid: str, arm: str, rep: int, route_set: set):
    """Eight-key pcbflow.v4_2-jq-reading/1 -> (flags, validation block).

    Hard checks (fail-closed, r3 semantics): exact eight-key set;
    ``validation.passed`` is true (an unvalidated/failed reading is not
    a locked final reading and has no scoring caliber); ``return_raw``
    and ``ts`` are strings; the frozen structural checker then runs on
    a flags-view shim (pid equality, arm == directory arm, schema == jq
    reading schema, model_output a list of well-formed per-route
    entries, route_id set == package route set, no duplicates; rep
    field equality).
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
    return flags, validation


# extended confusion: the frozen six keys + the abstain/no_flag split
# (caliber section 3.7.4) -- fn = noflag_imp + abstain_imp and
# tn = noflag_nonimp + abstain_nonimp are caliber identities.
_CONF_KEYS_JQ = _CONF_KEYS + ("abstain_imp", "abstain_nonimp",
                              "noflag_imp", "noflag_nonimp")


def _confusion_jq(flags, route_impr: dict) -> dict:
    """r2 caliber confusion + the verdict-x-improvable four-way split."""
    conf = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "abstain": 0, "n_routes": 0,
            "abstain_imp": 0, "abstain_nonimp": 0,
            "noflag_imp": 0, "noflag_nonimp": 0}
    for fl in flags:
        verdict = fl["verdict"]
        if verdict not in scoring.VERDICTS:
            raise RuntimeError("unknown verdict %r" % verdict)
        improvable = route_impr[fl["route_id"]]
        conf["n_routes"] += 1
        if verdict == "flag_bad":
            conf["tp" if improvable else "fp"] += 1
        else:
            if verdict == "abstain":
                conf["abstain"] += 1
                conf["abstain_imp" if improvable else "abstain_nonimp"] += 1
            else:
                conf["noflag_imp" if improvable else "noflag_nonimp"] += 1
            conf["fn" if improvable else "tn"] += 1
    return conf


def _sum_confs_jq(confs: list) -> dict:
    totals = {k: 0 for k in _CONF_KEYS_JQ}
    for conf in confs:
        for k in _CONF_KEYS_JQ:
            totals[k] += conf[k]
    return totals


def _reason_counts(flags, route_impr: dict) -> dict:
    """reason_code six-code sublayer counts: code -> [n, n_improvable]."""
    out = {code: [0, 0] for code in scoring.REASON_CODES}
    for fl in flags:
        code = fl["reason_code"]
        if code not in out:
            raise RuntimeError("unknown reason_code %r" % code)
        out[code][0] += 1
        if route_impr[fl["route_id"]]:
            out[code][1] += 1
    return out


def _sum_reasons(counts: list) -> dict:
    out = {code: [0, 0] for code in scoring.REASON_CODES}
    for table in counts:
        for code, (n, n_imp) in table.items():
            out[code][0] += n
            out[code][1] += n_imp
    return out


def _calibration_block(conf: dict, reasons: dict) -> dict:
    """Section 3.7.4 frozen calibration caliber (ECE = not_available)."""
    tp, fp = conf["tp"], conf["fp"]
    n_abstain = conf["abstain"]
    n_no_flag = conf["noflag_imp"] + conf["noflag_nonimp"]
    p_flag = _ratio(tp, tp + fp)          # == precision (identity)
    p_abstain = _ratio(conf["abstain_imp"], n_abstain)
    p_no_flag = _ratio(conf["noflag_imp"], n_no_flag)
    monotone = (None if p_flag is None or p_no_flag is None
                else bool(p_flag >= p_no_flag))
    return {
        "ece": "not_available",
        "ece_note": ("合同无数值置信输出（verdict 三态+reason_code 六码）→"
                     "ECE=not_available；冻结口径=verdict 三态条件 improvable 率"
                     "（PREREG §3.7.4）"),
        "three_state_conditional_improvable": {
            "P_imp_given_flag_bad": p_flag,
            "P_imp_given_abstain": p_abstain,
            "P_imp_given_no_flag": p_no_flag,
            "n_flag_bad": tp + fp,
            "n_abstain": n_abstain,
            "n_no_flag": n_no_flag,
        },
        "monotonicity_flag_bad_ge_no_flag": monotone,
        "monotonicity_note": ("组间单调性（flag_bad 组 ≥ no_flag 组）为描述性"
                              "校准读数，不作数值门（欠功效先例：R2 A 臂 2 旗、"
                              "CI [0,1]）"),
        "reason_code_sublayer": {
            code: {"n": n, "n_improvable": n_imp,
                   "improvable_rate": _ratio(n_imp, n)}
            for code, (n, n_imp) in sorted(reasons.items())
        },
    }


# ------------------------------------------------------ collapse (3.7.3)
_HARD_DEF = ("硬塌缩：会话 recall=0.0000，或（会话 flag_bad 总数 ≤2 且 tp=0）"
             "（PREREG §3.7.3）")
_SOFT_DEF = ("软塌缩：会话 recall < 0.5×该臂池化 recall（阈值随臂池化缩放）"
             "（PREREG §3.7.3）")


def classify_hard(session_row: dict) -> bool:
    """Hard collapse of one session row (counts + recall, r2 drift shape)."""
    recall = session_row.get("recall")
    flag_bad = session_row["tp"] + session_row["fp"]
    by_recall = recall is not None and recall == 0.0
    by_counts = flag_bad <= 2 and session_row["tp"] == 0
    return bool(by_recall or by_counts)


def classify_soft(session_row: dict, pooled_recall) -> bool:
    """Soft collapse of one session row against the arm pooled recall."""
    recall = session_row.get("recall")
    if recall is None or pooled_recall is None:
        return False
    return bool(recall < 0.5 * pooled_recall)


def collapse_block(per_session_rows: dict, pooled_recall) -> dict:
    """Section 3.7.3 hard/soft collapse classification for one arm."""
    hard, soft = [], []
    for key in sorted(per_session_rows):
        row = per_session_rows[key]
        if classify_hard(row):
            hard.append(key)
        if classify_soft(row, pooled_recall):
            soft.append(key)
    n_sessions = len(per_session_rows)
    return {
        "definition_hard": _HARD_DEF,
        "definition_soft": _SOFT_DEF,
        "pooled_recall": pooled_recall,
        "soft_threshold": (None if pooled_recall is None
                           else 0.5 * pooled_recall),
        "hard_sessions": hard,
        "hard_count": len(hard),
        "hard_rate": len(hard) / n_sessions if n_sessions else None,
        "soft_sessions": soft,
        "soft_count": len(soft),
        "soft_rate": len(soft) / n_sessions if n_sessions else None,
        "note": ("硬/软分列报告；会话 recall 未定义（分母 0）时硬塌缩第 1 判据"
                 "不可评、软塌缩判为不满足（fail-closed 如实呈现）"),
    }


# --------------------------------------------- session variance (3.7.2)
def _variance_params(values: list) -> dict:
    """Sample variance caliber (n-1) over the session recalls.

    Any undefined (None) recall makes every parameter None (fail-closed,
    reported as such); the raw values are always listed.
    """
    out = {"n": len(values), "mean": None, "sample_variance": None,
           "sample_std": None, "min": None, "max": None, "range": None,
           "all_defined": bool(values) and all(v is not None
                                               for v in values)}
    if not out["all_defined"]:
        return out
    n = len(values)
    mean = sum(values) / n
    out["mean"] = mean
    out["min"] = min(values)
    out["max"] = max(values)
    out["range"] = max(values) - min(values)
    if n >= 2:
        s2 = sum((v - mean) ** 2 for v in values) / (n - 1)
        out["sample_variance"] = s2
        out["sample_std"] = s2 ** 0.5
    return out


def session_variance_block(per_session_rows: dict) -> dict:
    """Section 3.7.2 point estimates for one arm's 6 session recalls."""
    recalls = {key: row.get("recall")
               for key, row in sorted(per_session_rows.items())}
    params = _variance_params(list(recalls.values()))
    params["session_recalls"] = recalls
    params["caliber"] = ("每臂 6 会话（rep×batch）recall 的样本方差 s²（n-1）、"
                         "标准差 s、极差（点估计）；CI 见 paired-stats.json"
                         "（PREREG §3.7.2/§3.8）")
    return params


# --------------------------------------------------------- load readings
def load_readings(readings_root: Path, meta: dict, route_impr: dict):
    """Resolve, validate and confuse every reading of the 2x3x|pid| grid.

    Returns (confusions, reasons, chosen_files, superseded,
    first_attempt_failed) with
      confusions[arm][rep][pid] = extended confusion dict (jq caliber)
      reasons[arm][pid]         = pooled six-code counts over the reps
      first_attempt_failed      = {(arm, rep, pid), ...} readings whose
                                   validation block records a retry
    Fail-closed: any structural/six-rule violation raises (the resolved
    file is the final post-retry reading; a non-compliant final reading
    has no preregistered scoring caliber -- retry/stop-the-line is the
    batch layer's job, PREREG section 3.11).
    """
    readings_root = Path(readings_root)
    pids = sorted(meta)
    confusions = {arm: {} for arm in ARMS}
    reasons = {arm: {} for arm in ARMS}
    chosen_files = {arm: {} for arm in ARMS}
    superseded = {arm: {} for arm in ARMS}
    first_attempt_failed = set()
    for arm in ARMS:
        for rep in REPS:
            directory = _reading_dir(readings_root, arm, rep)
            chosen, sup = _resolve_reading_files(directory, pids)
            conf = {}
            for pid in pids:
                sid = meta[pid]["sid"]
                route_set = set(route_impr[sid])
                data = _load_json(directory / chosen[pid])
                flags, validation = _flags_from_reading(data, pid, arm, rep,
                                                        route_set)
                problems = validate_six_rules(flags, route_set)
                if problems:
                    raise RuntimeError(
                        "non-compliant final reading %s rep%d/%s, refusing "
                        "to score:\n  %s" % (arm, rep, pid,
                                             "\n  ".join(problems)))
                conf[pid] = _confusion_jq(flags, route_impr[sid])
                reasons[arm].setdefault(pid, []).append(
                    _reason_counts(flags, route_impr[sid]))
                if validation.get("first_attempt_errors") or \
                        validation.get("retry"):
                    first_attempt_failed.add((arm, rep, pid))
            confusions[arm][rep] = conf
            chosen_files[arm][rep] = chosen
            if sup:
                superseded[arm][rep] = sup
    return (confusions, reasons, chosen_files, superseded,
            first_attempt_failed)


# --------------------------------------------------------- bootstrap (3.8)
_VAR_STATS = ("session_recall_var", "session_recall_std",
              "session_recall_range")
_RATE_STATS = ("recall", "precision", "abstention")


def _bootstrap_jq(cluster_rows: dict, session_rows: dict,
                  batch_of_index: list, seed: int = BOOTSTRAP_SEED,
                  n_boot: int = N_BOOTSTRAP) -> dict:
    """Paired cluster bootstrap over the scenario clusters (PREREG 3.8).

    cluster_rows: {arm: [per-scenario counts pooled across the 3 reps]}
    session_rows: {arm: {rep: [per-scenario counts]}} in identical
    sorted-sid order; batch_of_index[i] = batch (1/2) of cluster i.
    Each replicate draws ONE shared index list applied to both arms;
    pooled statistics consume the pooled cluster rows (16 scenarios x 3
    reps pooling, never 48 independent clusters); the session-variance
    parameters recompute the 6 session recalls* on the drawn multiset
    restricted to each session's batch from that rep's readings.  A
    zero-denominator statistic is undefined (excluded + counted); a
    replicate with any undefined session recall* makes that arm's
    variance parameters undefined.  Returns {statistic_key:
    {low, high, n_defined, n_undefined}}.
    """
    k = len(cluster_rows[ARMS[0]])
    for arm in ARMS:
        if len(cluster_rows[arm]) != k or \
                any(len(session_rows[arm][rep]) != k for rep in REPS):
            raise RuntimeError("arm cluster rows are not aligned")
    stat_keys = []
    for arm in ARMS:
        stat_keys += ["recall_%s" % arm, "precision_%s" % arm,
                      "abstention_%s" % arm] + \
            ["%s_%s" % (stat, arm) for stat in _VAR_STATS]
    for stat in _RATE_STATS + _VAR_STATS:
        stat_keys.append("%s_diff_Q-CTR" % stat)
    samples = {key: [] for key in stat_keys}
    undefined = {key: 0 for key in stat_keys}
    rng = random.Random(seed)
    for _ in range(n_boot):
        idx = [rng.randrange(k) for _ in range(k)]
        totals, rates, var_params = {}, {}, {}
        for arm in ARMS:
            tot = {f: 0 for f in _CONF_KEYS}
            for i in idx:
                row = cluster_rows[arm][i]
                for f in _CONF_KEYS:
                    tot[f] += row[f]
            totals[arm] = tot
            rates[arm] = {
                "recall": _ratio(tot["tp"], tot["tp"] + tot["fn"]),
                "precision": _ratio(tot["tp"], tot["tp"] + tot["fp"]),
                "abstention": _ratio(tot["abstain"], tot["n_routes"]),
            }
            sess_recalls = []
            for rep in REPS:
                for batch in (1, 2):
                    stot = {f: 0 for f in _CONF_KEYS}
                    for i in idx:
                        if batch_of_index[i] != batch:
                            continue
                        row = session_rows[arm][rep][i]
                        for f in _CONF_KEYS:
                            stot[f] += row[f]
                    sess_recalls.append(_ratio(stot["tp"],
                                               stot["tp"] + stot["fn"]))
            params = _variance_params(sess_recalls)
            var_params[arm] = {
                "session_recall_var": params["sample_variance"],
                "session_recall_std": params["sample_std"],
                "session_recall_range": params["range"],
            }
        for stat in _RATE_STATS + _VAR_STATS:
            getter = (lambda arm, s=stat: rates[arm][s] if s in rates[arm]
                      else var_params[arm][s])
            for arm in ARMS:
                val = getter(arm)
                if val is None:
                    undefined["%s_%s" % (stat, arm)] += 1
                else:
                    samples["%s_%s" % (stat, arm)].append(val)
            vq, vc = getter("Q"), getter("CTR")
            if vq is None or vc is None:
                undefined["%s_diff_Q-CTR" % stat] += 1
            else:
                samples["%s_diff_Q-CTR" % stat].append(vq - vc)
    ci = {}
    for key in stat_keys:
        if samples[key]:
            ci[key] = {"low": _percentile(samples[key], CI_LO),
                       "high": _percentile(samples[key], CI_HI),
                       "n_defined": len(samples[key]),
                       "n_undefined": undefined[key]}
        else:
            ci[key] = {"low": None, "high": None, "n_defined": 0,
                       "n_undefined": undefined[key]}
    return ci


# ------------------------------------------- path-d disclosure channel
def scan_pathd_references(readings_root: Path = READINGS_ROOT,
                          gt_path: Path = GT_PATH,
                          package_meta_path: Path = PACKAGE_META_PATH) -> dict:
    """CTR path-d evidence scan (R2 section 4.6 full clause, 3.4).

    Deterministic channel of the dual-channel detection (regex here;
    human review is the report layer's): every entry's evidence text of
    every resolved reading is scanned with the four frozen patterns.
    Q is scanned under the same caliber as the negative control
    (expected 0; a non-zero hit is disclosed as fabrication/recall, not
    deleted and not a stop-the-line).  Returns a report-ready dict;
    disclosure only -- no gate, no exclusion.
    """
    meta, route_impr, _sids = _gt_tables(gt_path, package_meta_path)
    readings_root = Path(readings_root)
    per_arm = {}
    for arm in ARMS:
        by_pattern = {name: 0 for name, _rx in PATHD_PATTERNS}
        hits, total_entries = [], 0
        for rep in REPS:
            directory = _reading_dir(readings_root, arm, rep)
            chosen, _sup = _resolve_reading_files(directory, sorted(meta))
            for pid in sorted(meta):
                sid = meta[pid]["sid"]
                route_set = set(route_impr[sid])
                data = _load_json(directory / chosen[pid])
                flags, _validation = _flags_from_reading(data, pid, arm, rep,
                                                         route_set)
                total_entries += len(flags)
                for fl in flags:
                    for name, rx in PATHD_PATTERNS:
                        if rx.search(fl["evidence"]):
                            by_pattern[name] += 1
                            hits.append({"rep": rep, "pid": pid,
                                         "route_id": fl["route_id"],
                                         "verdict": fl["verdict"],
                                         "pattern": name})
        per_arm[arm] = {"n_entries_scanned": total_entries,
                        "n_hits": len(hits), "by_pattern": by_pattern,
                        "hits": hits}
    return {
        "schema": "pcbflow.v4_2-jq-pathd-scan/1",
        "caliber": ("读数后检测通道（R2 §4.6 全款）：确定性正则四模式 + 人工复核"
                    "双通道；Q 臂同口径阴性对照（预期 0）"),
        "patterns": {name: rx.pattern for name, rx in PATHD_PATTERNS},
        "disposal": _PATHD_DISPOSAL_NOTE,
        "expected": {"CTR": "被测行为（r2 形态保真重跑，如实计数）",
                     "Q": "阴性对照，预期 0；非零=虚构/回忆性引用，如实披露"},
        "arms": per_arm,
    }


# ------------------------------------------------------ templates (rig)
def _lcp(texts: list) -> str:
    pre = texts[0]
    for t in texts[1:]:
        i, m = 0, min(len(pre), len(t))
        while i < m and pre[i] == t[i]:
            i += 1
        pre = pre[:i]
    return pre


def _lcs(texts: list) -> str:
    suf = texts[0]
    for t in texts[1:]:
        i, m = 0, min(len(suf), len(t))
        while i < m and suf[len(suf) - 1 - i] == t[len(t) - 1 - i]:
            i += 1
        suf = suf[len(suf) - i:]
    return suf


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_templates(templates_path: Path = TEMPLATES_PATH,
                     packs_b_dir: Path = PACKS_B_DIR,
                     tasks_a_dir: Path = TASKS_A_DIR) -> dict:
    """Pin templates.json to the frozen R1 corpus, byte-for-byte.

    Checks (all hard): the six template strings present; per arm the 16
    frozen packs share one system text equal to the template system;
    template head/tail equal the longest common prefix/suffix of the 16
    frozen user texts; user = head + middle + tail reconstructs every
    pack exactly; the frozen_sources sha256 table matches the on-disk
    files; the blinding regex hits none of the six template strings;
    the output contract names exactly the eight reading keys.
    Returns {passed, problems, per_arm summary}.
    """
    templates_path = Path(templates_path)
    problems: list = []
    tpl = _load_json(templates_path)
    if tpl.get("schema") != TEMPLATES_SCHEMA:
        problems.append("schema %r != %r" % (tpl.get("schema"),
                                             TEMPLATES_SCHEMA))
    for arm, key in (("Q", "q"), ("CTR", "ctr")):
        for part in ("system", "head", "tail"):
            if not isinstance(tpl.get("%s_%s" % (key, part)), str):
                problems.append("%s_%s missing/not a string" % (key, part))
    if problems:
        return {"passed": False, "problems": problems, "arms": {}}

    oc = tpl.get("output_contract", {})
    if sorted(oc.get("reading_keys", [])) != sorted(READING_KEYS):
        problems.append("output_contract.reading_keys %r != eight-key "
                        "contract %r" % (oc.get("reading_keys"),
                                         sorted(READING_KEYS)))
    if oc.get("reading_schema") != READING_SCHEMA:
        problems.append("output_contract.reading_schema %r != %r"
                        % (oc.get("reading_schema"), READING_SCHEMA))

    # ---- pack marker contract (dispatch layer, ask-pinned) ----
    marker = oc.get("pack_marker", {})
    if not isinstance(marker, dict):
        problems.append("output_contract.pack_marker missing/not an object")
    else:
        if marker.get("line_template") != PACK_MARKER_TEMPLATE:
            problems.append("pack_marker.line_template %r != %r"
                            % (marker.get("line_template"),
                               PACK_MARKER_TEMPLATE))
        if marker.get("pid_pattern") != PACK_MARKER_PID_PATTERN:
            problems.append("pack_marker.pid_pattern %r != %r"
                            % (marker.get("pid_pattern"),
                               PACK_MARKER_PID_PATTERN))
        for pid in ("p01", "p16"):
            line = PACK_MARKER_TEMPLATE.format(pid=pid)
            m = PACK_MARKER_LINE_RE.match(line)
            if m is None or m.group(1) != pid:
                problems.append("marker line %r does not round-trip the "
                                "frozen pid pattern" % line)
    ask_asm = oc.get("session_ask_assembly", {})
    if not isinstance(ask_asm, dict):
        problems.append("output_contract.session_ask_assembly missing/not "
                        "an object")
    elif ask_asm.get("schema") != SESSION_ASK_SCHEMA:
        problems.append("session_ask_assembly.schema %r != %r"
                        % (ask_asm.get("schema"), SESSION_ASK_SCHEMA))

    summary = {}
    for arm, key, directory in (("Q", "q", packs_b_dir), ("CTR", "ctr",
                                                          tasks_a_dir)):
        directory = Path(directory)
        files = sorted(directory.glob("p*.json"))
        if len(files) != 16:
            problems.append("%s: %d pack files != 16" % (arm, len(files)))
            continue
        systems, users, shas = [], [], {}
        for path in files:
            obj = _load_json(path)
            shas[obj["pid"]] = _sha256_file(path)
            systems.append(obj["system"])
            users.append(obj["user"])
        system, head, tail = (tpl["%s_system" % key], tpl["%s_head" % key],
                              tpl["%s_tail" % key])
        if len(set(systems)) != 1 or systems[0] != system:
            problems.append("%s: template system != frozen (identical) "
                            "pack system" % arm)
        if head != _lcp(users):
            problems.append("%s: q/ctr head != longest common prefix of the "
                            "16 frozen user texts" % arm)
        if tail != _lcs(users):
            problems.append("%s: tail != longest common suffix of the 16 "
                            "frozen user texts" % arm)
        for path, user in zip(files, users):
            if len(head) + len(tail) > len(user) or \
                    not user.startswith(head) or not user.endswith(tail):
                problems.append("%s: head+tail does not reconstruct %s"
                                % (arm, path.name))
        declared = tpl.get("frozen_sources", {}).get(arm, {}).get("sha256")
        if declared != shas:
            problems.append("%s: frozen_sources sha256 table drift" % arm)
        for name, text in (("system", system), ("head", head),
                           ("tail", tail)):
            if _BLIND_RE.search(text):
                problems.append("%s: blinding regex hit in template %s"
                                % (arm, name))
            if "===PACK " in text:
                problems.append("%s: dispatch-layer pack marker inside the "
                                "frozen template %s (marker never enters the "
                                "ask texts)" % (arm, name))
        summary[arm] = {"n_packs": len(files), "head_chars": len(head),
                        "tail_chars": len(tail), "sha256_anchored": True}
    return {"passed": not problems, "problems": problems, "arms": summary}


# ------------------------------------------------------------- score_jq()
def score_jq(gt_path: Path = GT_PATH,
             package_meta_path: Path = PACKAGE_META_PATH,
             readings_root: Path = READINGS_ROOT,
             out_dir: Path = JQ_OUT_DIR,
             reproduce: bool = True,
             reproduce_kwargs: dict = None) -> dict:
    """Gate on the r2 reproduction, then score both arms + the gate.

    Writes arm-q-stats.json, arm-ctr-stats.json, session-stats.json,
    paired-stats.json, qualification-gate.json (canonical JSON) inside
    ``out_dir`` (default out/v4.2-judge-qual-r1/) and returns the full
    result dict.  ``reproduce_kwargs`` redirects the gate's frozen
    inputs (synthetic-fixture testing only).
    """
    gate = None
    if reproduce:
        gate = reproduce_r2(**(reproduce_kwargs or {}))
        if not gate["passed"]:
            raise RuntimeError(
                "r2 reproduction gate FAILED -- JUDGE-QUAL statistics "
                "pipeline is buggy, refusing to emit any number "
                "(PREREG-JUDGE-QUAL-R1 section 3.8 / 3.11):\n  "
                + "\n  ".join(gate["problems"]))

    out_dir = Path(out_dir)
    meta, route_impr, sids_sorted = _gt_tables(gt_path, package_meta_path)
    pids = sorted(meta)
    families = {sid: family_of(sid) for sid in sids_sorted}
    fam_counts = {}
    for sid in sids_sorted:
        fam_counts[families[sid]] = fam_counts.get(families[sid], 0) + 1
    if fam_counts != FAMILY_COUNTS:
        raise RuntimeError("board family census %r != frozen %r"
                           % (fam_counts, FAMILY_COUNTS))
    (confusions, reasons, chosen_files, superseded,
     first_failed) = load_readings(readings_root, meta, route_impr)

    # ---- per-arm stats (pooled 369 + strata + 3.7.2/3.7.3/3.7.4/3.7.5)
    arm_stats = {}
    for arm in ARMS:
        all_confs = [confusions[arm][rep][pid] for rep in REPS
                     for pid in pids]
        pooled_conf = _sum_confs_jq(all_confs)
        pooled = _row(pooled_conf)
        all_reasons = [table for pid in pids for table in reasons[arm][pid]]
        reasons_arm = _sum_reasons(all_reasons)
        per_rep, per_session = {}, {}
        for rep in REPS:
            per_rep["rep%d" % rep] = _row(_sum_confs_jq(
                [confusions[arm][rep][pid] for pid in pids]))
            for batch in (1, 2):
                per_session["rep%d-batch%d" % (rep, batch)] = _row(
                    _sum_confs_jq([confusions[arm][rep][pid]
                                   for pid in pids
                                   if _batch_of(pid) == batch]))
        per_scenario = {}
        for sid in sids_sorted:
            per_scenario[sid] = _row(_sum_confs_jq(
                [confusions[arm][rep][pid] for rep in REPS for pid in pids
                 if meta[pid]["sid"] == sid]))
        per_family = {}
        for family in sorted(FAMILY_COUNTS):
            fam_sids = [sid for sid in sids_sorted
                        if families[sid] == family]
            fam_pids = [pid for pid in pids if meta[pid]["sid"] in fam_sids]
            conf = _sum_confs_jq([confusions[arm][rep][pid]
                                  for rep in REPS for pid in fam_pids])
            fam_reasons = _sum_reasons([table for pid in fam_pids
                                        for table in reasons[arm][pid]])
            row = _row(conf)
            per_family[family] = {
                "five_indicators": ["n_routes", "improvable_rate",
                                    "precision", "recall",
                                    "abstention_rate"],
                "n_scenarios": len(fam_sids),
                "n_routes": row["n_routes"],
                "improvable": row["improvable"],
                "improvable_rate": (row["improvable"] / row["n_routes"]
                                    if row["n_routes"] else None),
                "tp": row["tp"], "fp": row["fp"], "fn": row["fn"],
                "tn": row["tn"], "abstain": row["abstain"],
                "precision": row["precision"], "recall": row["recall"],
                "abstention_rate": row["abstention_rate"],
                "calibration": _calibration_block(conf, fam_reasons),
            }
        n_readings = N_REPS * len(pids)
        stats = {
            "schema": ARM_STATS_SCHEMA,
            "arm": arm,
            "prereg": "PREREG-JUDGE-QUAL-R1-FROZEN.md sections 3.7/3.8",
            "n_reps": N_REPS,
            "n_sessions": N_REPS * 2,
            "n_scenarios": len(sids_sorted),
            "n_readings": n_readings,
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
            "random_baseline_frozen": {"value": RB_FROZEN,
                                       "text": RB_FROZEN_TEXT,
                                       "matches": (
                                           pooled["n_routes"] == 369
                                           and pooled["improvable"] == 99
                                           and abs(pooled["improvable"]
                                                   / pooled["n_routes"]
                                                   - RB_FROZEN) <= 1e-12)},
            # fail-closed loader: every scored reading passed the six rules
            "schema_compliant_readings": n_readings,
            "schema_compliance_rate": 1.0,
            "first_attempt_compliant_readings": n_readings - sum(
                1 for key in first_failed if key[0] == arm),
            "first_attempt_compliance_rate": (
                (n_readings - sum(1 for key in first_failed
                                  if key[0] == arm)) / n_readings),
            "first_attempt_note": ("descriptive: from the R3-shape "
                                   "validation block (first_attempt_errors/"
                                   "retry); finals are fail-closed above"),
            "reading_files": {("rep%d" % rep): dict(chosen_files[arm][rep])
                              for rep in REPS},
            "per_rep": per_rep,
            "per_session": per_session,
            "per_scenario": per_scenario,
            "per_family": per_family,
            "calibration": _calibration_block(pooled_conf, reasons_arm),
            "session_variance": session_variance_block(per_session),
            "collapse": collapse_block(per_session, pooled["recall"]),
        }
        if any(superseded[arm].get(rep) for rep in REPS):
            stats["superseded_retries"] = {
                ("rep%d" % rep): superseded[arm][rep]
                for rep in REPS if superseded[arm].get(rep)}
        arm_stats[arm] = stats

    # ---- session flat table (12 rows: arm/rep/batch + counts + rates)
    sessions = []
    for arm in ARMS:
        for rep in REPS:
            for batch in (1, 2):
                row = arm_stats[arm]["per_session"]["rep%d-batch%d" % (rep,
                                                                       batch)]
                sessions.append({
                    "arm": arm, "rep": rep, "batch": batch,
                    "tp": row["tp"], "fp": row["fp"], "fn": row["fn"],
                    "tn": row["tn"], "recall": row["recall"],
                    "precision": row["precision"],
                    "abstain_rate": row["abstention_rate"],
                })
    session_stats = {"schema": SESSION_STATS_SCHEMA,
                     "n_sessions": len(sessions), "sessions": sessions}

    # ---- paired stats (pooled + cluster bootstrap + session variance)
    cluster_rows, session_rows = {}, {}
    for arm in ARMS:
        pooled_sid = {sid: {k: 0 for k in _CONF_KEYS}
                      for sid in sids_sorted}
        per_rep_sid = {rep: {sid: {k: 0 for k in _CONF_KEYS}
                             for sid in sids_sorted} for rep in REPS}
        for rep in REPS:
            for pid, conf in confusions[arm][rep].items():
                sid = meta[pid]["sid"]
                for k in _CONF_KEYS:
                    pooled_sid[sid][k] += conf[k]
                    per_rep_sid[rep][sid][k] += conf[k]
        cluster_rows[arm] = [pooled_sid[sid] for sid in sids_sorted]
        session_rows[arm] = {rep: [per_rep_sid[rep][sid]
                                   for sid in sids_sorted] for rep in REPS}
    batch_of_index = [_batch_of(pid_of_sid(meta, sid))
                      for sid in sids_sorted]
    # ONE bootstrap run feeds every reported CI (shared index lists, 3.8)
    ci = _bootstrap_jq(cluster_rows, session_rows, batch_of_index)
    pooled_rows = {arm: arm_stats[arm] for arm in ARMS}
    rep_level = {}
    for stat, field in (("recall", "recall"), ("precision", "precision"),
                        ("abstention", "abstention_rate")):
        points = {}
        for rep in REPS:
            vq = pooled_rows["Q"]["per_rep"]["rep%d" % rep][field]
            vc = pooled_rows["CTR"]["per_rep"]["rep%d" % rep][field]
            points["rep%d" % rep] = (None if vq is None or vc is None
                                     else vq - vc)
        rep_level["%s_diff" % stat] = points
    session_var_point = {arm: arm_stats[arm]["session_variance"]
                         for arm in ARMS}
    paired = {
        "schema": PAIRED_STATS_SCHEMA,
        "prereg": "PREREG-JUDGE-QUAL-R1-FROZEN.md section 3.8",
        "seed": BOOTSTRAP_SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_clusters": len(sids_sorted),
        "cluster_caliber": ("per-arm per-scenario counts pooled across the "
                            "3 reps before resampling (PREREG section 3.8; "
                            "never 48 scenario x rep clusters)"),
        "resample_unit": ("scenario (cluster bootstrap, 16 clusters, with "
                          "replacement)"),
        "paired_design": ("each replicate draws ONE scenario index list "
                          "applied to both arms"),
        "percentile_method": ("linear interpolation on order statistics "
                              "(numpy 'linear' equivalent)"),
        "undefined_replicate_convention": (
            "a statistic with zero denominator in a replicate (recall: no "
            "improvable route resampled; precision: no flag_bad resampled) "
            "is undefined; undefined replicates are excluded from the "
            "percentiles and counted in n_undefined; nothing is imputed"),
        "session_variance_bootstrap_caliber": (
            "PREREG section 3.8 main statistic: inside the same replicate "
            "machinery each of the 6 session recalls* is recomputed on the "
            "drawn scenario multiset restricted to that session's batch "
            "from that rep's readings of the drawn scenarios; s2*/s*/range* "
            "follow; a replicate in which any of the 6 session recalls is "
            "undefined makes that arm's variance parameters undefined "
            "(excluded + counted in n_undefined)"),
        "n_routes_per_arm": arm_stats["Q"]["n_routes"],
        "pooled": {
            "recall": {arm: pooled_rows[arm]["recall"] for arm in ARMS},
            "precision": {arm: pooled_rows[arm]["precision"]
                          for arm in ARMS},
            "abstention_rate": {arm: pooled_rows[arm]["abstention_rate"]
                                for arm in ARMS},
        },
        "comparisons": {
            "Q-CTR": {
                "role": "statistic = each arm's statistics and the "
                        "difference (PREREG section 3.8)",
                "direction": "arm Q minus arm CTR",
                "recall_diff": (None if pooled_rows["Q"]["recall"] is None
                                or pooled_rows["CTR"]["recall"] is None
                                else pooled_rows["Q"]["recall"]
                                - pooled_rows["CTR"]["recall"]),
                "precision_diff": (None
                                   if pooled_rows["Q"]["precision"] is None
                                   or pooled_rows["CTR"]["precision"] is None
                                   else pooled_rows["Q"]["precision"]
                                   - pooled_rows["CTR"]["precision"]),
                "abstention_diff": (
                    None if pooled_rows["Q"]["abstention_rate"] is None
                    or pooled_rows["CTR"]["abstention_rate"] is None
                    else pooled_rows["Q"]["abstention_rate"]
                    - pooled_rows["CTR"]["abstention_rate"]),
                "bootstrap_ci95": {
                    "recall_diff": dict(ci["recall_diff_Q-CTR"]),
                    "precision_diff": dict(ci["precision_diff_Q-CTR"]),
                    "abstention_diff": dict(ci["abstention_diff_Q-CTR"]),
                },
                "rep_level_recall_diff": rep_level["recall_diff"],
                "rep_level_precision_diff": rep_level["precision_diff"],
                "rep_level_abstention_diff": rep_level["abstention_diff"],
            },
        },
        "per_arm_bootstrap_ci95": {
            "recall": {arm: ci["recall_%s" % arm] for arm in ARMS},
            "precision": {arm: ci["precision_%s" % arm] for arm in ARMS},
            "abstention_rate": {arm: ci["abstention_%s" % arm]
                                for arm in ARMS},
        },
        "session_variance": {
            "point_estimates": {
                arm: {k: session_var_point[arm][k] for k in
                      ("n", "mean", "sample_variance", "sample_std", "min",
                       "max", "range", "all_defined", "session_recalls")}
                for arm in ARMS},
            "bootstrap_ci95": {
                "sample_variance": {arm: ci["session_recall_var_%s" % arm]
                                    for arm in ARMS},
                "sample_std": {arm: ci["session_recall_std_%s" % arm]
                               for arm in ARMS},
                "range": {arm: ci["session_recall_range_%s" % arm]
                          for arm in ARMS},
                "diff_Q-CTR": {
                    "sample_variance": ci["session_recall_var_diff_Q-CTR"],
                    "sample_std": ci["session_recall_std_diff_Q-CTR"],
                    "range": ci["session_recall_range_diff_Q-CTR"],
                },
            },
        },
    }

    # ---- qualification gate (section 3.10, frozen values)
    q = arm_stats["Q"]
    gate_json = _qualification_gate(q, ci)

    written = []
    for arm in ARMS:
        out = out_dir / ARM_STATS_PATHS[arm].name
        _write_canonical(out, arm_stats[arm])
        written.append(out)
    _write_canonical(out_dir / SESSION_STATS_PATH.name, session_stats)
    written.append(out_dir / SESSION_STATS_PATH.name)
    _write_canonical(out_dir / PAIRED_STATS_PATH.name, paired)
    written.append(out_dir / PAIRED_STATS_PATH.name)
    _write_canonical(out_dir / QUALIFICATION_GATE_PATH.name, gate_json)
    written.append(out_dir / QUALIFICATION_GATE_PATH.name)

    return {"reproduce": gate, "arms": arm_stats, "sessions": session_stats,
            "paired": paired, "qualification": gate_json,
            "written": written}


def pid_of_sid(meta: dict, sid: str) -> str:
    """sid -> pid (bijection already enforced by _gt_tables)."""
    for pid in sorted(meta):
        if meta[pid]["sid"] == sid:
            return pid
    raise RuntimeError("no pid maps to scenario %s" % sid)


def _qualification_gate(q_stats: dict, ci: dict) -> dict:
    """Section 3.10 G1-G5 with frozen values; undefined inputs fail closed."""
    rb = q_stats["random_baseline"]
    precision = q_stats["precision"]
    prec_ci = ci["precision_Q"]
    abstention = q_stats["abstention_rate"]
    collapse = q_stats["collapse"]
    variance = q_stats["session_variance"]
    cal = q_stats["calibration"]["three_state_conditional_improvable"]

    point_threshold = None if rb is None else max(2.0 * rb, 0.4)
    g1_point = (precision is not None and point_threshold is not None
                and precision >= point_threshold)
    g1_ci = (prec_ci["low"] is not None
             and prec_ci["low"] >= G1_PRECISION_CI_LOW_MIN)
    g2 = abstention is not None and abstention <= G2_ABSTENTION_MAX
    g3 = collapse["hard_count"] == 0
    g4_range, g4_std = variance["range"], variance["sample_std"]
    g4 = ((g4_range is not None and g4_range <= G4_RANGE_MAX)
          or (g4_std is not None and g4_std <= G4_STD_ALT))
    p_flag = cal["P_imp_given_flag_bad"]
    p_no_flag = cal["P_imp_given_no_flag"]
    g5 = p_flag is not None and p_no_flag is not None and p_flag >= p_no_flag

    gates = {
        "G1": {
            "criterion": ("Q 臂池化 precision 点估计 ≥ max(2×rb,0.4) 且 "
                          "CI95 下界 ≥0.40（PREREG §3.10）"),
            "precision": precision,
            "random_baseline": rb,
            "point_threshold": point_threshold,
            "ci95_low": prec_ci["low"],
            "ci_low_threshold": G1_PRECISION_CI_LOW_MIN,
            "point_estimate_passes": bool(g1_point),
            "ci_low_passes": bool(g1_ci),
            "passed": bool(g1_point and g1_ci),
        },
        "G2": {
            "criterion": "Q 臂池化 abstention ≤0.5（PREREG §3.10）",
            "abstention_rate": abstention,
            "threshold": G2_ABSTENTION_MAX,
            "passed": bool(g2),
        },
        "G3": {
            "criterion": "Q 臂硬塌缩率=0/6（PREREG §3.10；定义 §3.7.3）",
            "hard_sessions": collapse["hard_sessions"],
            "hard_count": collapse["hard_count"],
            "hard_rate": collapse["hard_rate"],
            "passed": bool(g3),
        },
        "G4": {
            "criterion": ("Q 臂会话 recall 极差 ≤0.35（或 s ≤0.10）"
                          "（PREREG §3.10）"),
            "range": g4_range,
            "range_threshold": G4_RANGE_MAX,
            "sample_std": g4_std,
            "std_threshold_alt": G4_STD_ALT,
            "undefined_session_recall": not variance["all_defined"],
            "passed": bool(g4),
        },
        "G5": {
            "criterion": ("calibration 单调性成立：P(imp|flag_bad) ≥ "
                          "P(imp|no_flag)（Q 臂池化，PREREG §3.10）"),
            "P_imp_given_flag_bad": p_flag,
            "P_imp_given_no_flag": p_no_flag,
            "passed": bool(g5),
        },
    }
    failed = [name for name in sorted(gates) if not gates[name]["passed"]]
    return {
        "schema": QUALIFICATION_GATE_SCHEMA,
        "prereg": "PREREG-JUDGE-QUAL-R1-FROZEN.md section 3.10 "
                  "(values frozen via user ruling 2026-10-11)",
        "gates": gates,
        "all_passed": not failed,
        "gates_failed": failed,
        "semantics": ("qualification gate，非结果筛选：未过门=judge 保持 "
                      "shadow/诊断、不得成为路线取舍或生产验收依据；未过门为"
                      "合法收档结果，不触发返工（PREREG §3.0）。过门=judge 资格"
                      "成立（可作路线证据源；仍非生产签核）。一切结论为当前席位"
                      "模型（会话驱动 GLM-5.3）下实证，换模型/推理档须重开。"
                      "undefined 输入一律 fail-closed 判不过。"),
        "historical_reference_band": {
            "note": ("报告项非门：跨批只作冻结档参照、不做跨批统计检验"
                     "（PREREG §3.10；R3 §10.9 先例）"),
            "r2_b_recall": HIST_REFERENCE["r2_b_recall"],
            "r2_b_ci95": list(HIST_REFERENCE["r2_b_ci95"]),
            "r3_b_recall": HIST_REFERENCE["r3_b_recall"],
            "r3_b_ci95": list(HIST_REFERENCE["r3_b_ci95"]),
        },
        "stratification_factors": {
            "model": {"levels": [MODEL_LAYER], "note": MODEL_NOTE},
            "reasoning_effort": {"levels": [REASONING_EFFORT_LAYER],
                                 "note": REASONING_EFFORT_NOTE},
            "board_family": {
                "levels": sorted(FAMILY_COUNTS),
                "scenario_counts": dict(FAMILY_COUNTS),
                "note": ("每族×每臂五指标+calibration 分层表见 "
                         "arm-{q,ctr}-stats.json per_family（PREREG §3.6）"),
            },
        },
    }


# --------------------------------------------------------------- run_all()
def run_all() -> dict:
    """Gate -> score -> write; the last printed line is the JSON summary."""
    result = score_jq()
    for arm in ARMS:
        s = result["arms"][arm]
        print("arm %s: tp=%d fp=%d fn=%d tn=%d flag_bad=%d precision=%r "
              "recall=%r abstention=%r compliant=%d/%d"
              % (arm, s["tp"], s["fp"], s["fn"], s["tn"], s["flag_bad"],
                 s["precision"], s["recall"], s["abstention_rate"],
                 s["schema_compliant_readings"], s["n_readings"]))
    qual = result["qualification"]
    print("qualification: all_passed=%r gates_failed=%s"
          % (qual["all_passed"], qual["gates_failed"]))
    n_readings = sum(result["arms"][arm]["n_readings"] for arm in ARMS)
    summary = {
        "n_readings": n_readings,
        "arms": {arm: {"n_readings": result["arms"][arm]["n_readings"]}
                 for arm in ARMS},
        "qualification": {"passed": qual["all_passed"],
                          "gates_failed": qual["gates_failed"]},
    }
    print(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    return result


# ------------------------------------------------------------------- main
def main(argv: list) -> int:
    argv = list(argv)
    if argv and argv[0] == "check":
        gate = reproduce_r2()
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
    if argv and argv[0] == "templates":
        report = verify_templates()
        print("templates verification vs %s" % TEMPLATES_PATH)
        if report["passed"]:
            for arm, summary in sorted(report["arms"].items()):
                print("  %s: %d packs anchored, head=%d chars, tail=%d chars"
                      % (arm, summary["n_packs"], summary["head_chars"],
                         summary["tail_chars"]))
            return 0
        for problem in report["problems"]:
            print("  FAIL %s" % problem)
        return 1
    if argv and argv[0] == "pathd":
        scan = scan_pathd_references()
        print(json.dumps(scan, sort_keys=True, ensure_ascii=False))
        return 0
    run_all()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
