"""JUDGE-QUAL-R1 orchestration glue (工装席 dispatch/ingest/finalize layer).

Bridges the subject sessions to the frozen scorer
``pcbflow.v4_2_rep.scoring_jq`` (read-only reuse; this module is a new
file).  Three pinned entry points (signatures frozen by the batch ask):

1. ``ingest_pack(pid, raw, session, arm, rep, batch, attempt, pids)
   -> {ok, problems}`` -- wrap ONE pack's judgment body into the
   eight-key ``pcbflow.v4_2-jq-reading/1`` reading file under
   ``out/v4.2-judge-qual-r1/readings/<Q|CTR>/rep<k>/`` (the R2 layout
   ``scoring_jq.load_readings`` expects).  The subject output contract
   (templates.json ``output_contract.pack_marker``) is HARD-enforced:
   ``raw`` must BEGIN with the dedicated marker line ``===PACK pNN===``
   (pNN == this pid) followed by that pack's judgment body (a JSON
   OBJECT with exactly one key ``flags``; mechanical JSON extraction
   only -- no solver, no GT, no history).  ``validation.passed`` is
   set true ONLY when the structural checks (pid/arm/schema/route-set
   equality/no duplicates via the frozen ``scoring`` primitives) AND
   the six frozen rules (``scoring.validate_six_rules``) all pass; a
   non-compliant output is still written fail-closed with its
   violation list (a non-compliant FINAL has no preregistered scoring
   caliber -- retry protocol / stop-the-line per PREREG section 3.11).
   The route-id reference set comes from the FROZEN PACK TEXT ITSELF
   (Q: ``route_id=`` values of [segment-index]; CTR: unique
   ``data-route-id`` attributes) -- PREREG-REP-R2 section 7 rule 2
   reference -- so ingest never touches gt.json or package-meta (the
   blinding discipline, PREREG section 3.5, holds by construction;
   route-set equality with the GT side was cross-checked once, main
   side, read-only).  ``attempt`` >= 2 writes the R2 superseding retry
   name ``p<NN>-r<attempt-1>.json`` (resolver semantics of
   ``scoring._resolve_reading_files``: highest -rN wins), copies
   attempt 1's recorded errors into ``validation.first_attempt_errors``
   (R3-realized shape) and appends a ``schema-retry`` ledger event;
   append-only: an existing output filename is never rewritten, and a
   retry without its attempt-1 file on disk is refused.

2. ``finalize_session(session, arm, rep, batch) -> {ok, n, problems}``
   -- check the session's 8 packs are all present and every resolved
   (highest -rN) reading is validation-passed; rebuild the session ask
   from templates.json + the frozen pack files (per-pid ask = template
   system + frozen user text verified as head+middle+tail, byte-
   identical; ZERO dispatch wrapper -- the JQ frozen definition; R2's
   ledger precedent carried a +186-char wrapper that this batch does
   not have); compute ``ask_sha256`` = sha256 of the canonical JSON
   (``scoring._canonical_json_bytes``) of ``{schema: pcbflow.v4_2-jq-
   session-ask/1, arm, rep, batch, session, pid_order, asks: [[pid,
   system, user], ...]}``; then append one ``reading-append`` ledger
   event per pid ({arm, rep, batch, session, pid, file, sha256 of the
   reading file bytes, ask_chars = len(system)+len(user),
   return_chars = len(return_raw)} -- the R2 event shape extended with
   session/batch) plus one additive ``session-ask-pinned`` event
   carrying the digest (tooling addition beyond the R3 seven classes;
   disclosed).  Refuses to run twice for the same session
   (append-only ledger).  The result dict additionally carries
   ``ask_sha256``.

3. ``finish_and_score() -> {ok, gates, summary}`` -- verify all 12
   sessions (2 arms x 3 reps x 2 batches) finalized = 96 reading-
   append events; append the ``gt-unseal`` ledger event (all readings
   locked BEFORE any GT access, PREREG section 3.5); call
   ``scoring_jq.score_jq()`` (the r2 reproduction gate runs first and
   blocks all numbers on failure; then sections 3.7/3.8 statistics +
   the G1-G5 qualification gate); append ``scoring-done``; return the
   five gates and a summary.  Extra ``problems`` key on failure.

Extra public helpers (outside the pinned three): ``split_session_
output(text, pids)`` splits a full multi-pack subject reply by the
``===PACK pNN===`` markers (dispatch side of the same contract; marker
sequence != pids = structural violation); ``log_arm_start`` /
``log_session_start`` write the R3-shape start events (orchestrator
calls them when opening a session); ``marker_line`` renders a pid's
marker; ``verify_templates`` re-exports the frozen templates gate.

Sandbox: all writes stay inside ONE root (readings tree, ledger.jsonl,
stats five-piece).  The root defaults to ``out/v4.2-judge-qual-r1/``;
``set_root(path)`` redirects it wholesale -- the synthetic-session
self-test (``self_test``) uses a tmp sandbox and never touches the
real ``out/v4.2-judge-qual-r1/readings/`` or its ledger.  Frozen
inputs (R1 pack corpus, templates) are always read from their real
frozen paths, read-only.

Determinism note: reading ``ts`` fields and ledger ``ts`` fields are
wall-clock by design (R2/R3 precedent; ``scoring_jq`` never copies
``ts`` into any statistic).  Everything else is stdlib/fixed-seed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
import re

from pcbflow.v4_2_rep import scoring       # frozen r1/r2 primitives, read-only
from pcbflow.v4_2_rep import scoring_jq    # frozen JUDGE-QUAL scorer, read-only
from pcbflow.v4_2_rep import scoring_r2    # frozen REP-R2 layer, read-only

# ------------------------------------------------------------- frozen paths
ROOT = scoring.ROOT                        # .../tools/pcbflow

REAL_JQ_OUT_DIR = ROOT / "out" / "v4.2-judge-qual-r1"
JQ_OUT_DIR = REAL_JQ_OUT_DIR               # redirected by set_root()
READINGS_ROOT = JQ_OUT_DIR / "readings"
TEMPLATES_PATH = JQ_OUT_DIR / "templates.json"
LEDGER_PATH = JQ_OUT_DIR / "ledger.jsonl"

ARMS = scoring_jq.ARMS                     # ("Q", "CTR")
REPS = scoring_jq.REPS                     # (1, 2, 3)
READING_SCHEMA = scoring_jq.READING_SCHEMA          # pcbflow.v4_2-jq-reading/1
SESSION_ASK_SCHEMA = scoring_jq.SESSION_ASK_SCHEMA  # pcbflow.v4_2-jq-session-ask/1
BATCH_PIDS = {1: tuple("p%02d" % i for i in range(1, 9)),     # p01..p08
              2: tuple("p%02d" % i for i in range(9, 17))}    # p09..p16

PACK_MARKER_TEMPLATE = scoring_jq.PACK_MARKER_TEMPLATE      # ===PACK {pid}===
PACK_MARKER_LINE_RE = scoring_jq.PACK_MARKER_LINE_RE

_load_json = scoring._load_json
_write_canonical = scoring._write_canonical
_canonical_json_bytes = scoring._canonical_json_bytes
_resolve_reading_files = scoring._resolve_reading_files
_check_structure = scoring._check_structure
validate_six_rules = scoring.validate_six_rules
_reading_dir = scoring_r2._reading_dir
verify_templates = scoring_jq.verify_templates

# frozen R1 pack corpus dirs (the same dirs templates.json pins in
# frozen_sources; read-only)
PACK_DIRS = {"Q": scoring_jq.PACKS_B_DIR, "CTR": scoring_jq.TASKS_A_DIR}

# route-id extraction from the frozen pack text (PREREG-REP-R2 section 7
# rule 2 references; B: [segment-index] route_id= values, A: data-route-id)
_ROUTE_ID_B = re.compile(r"route_id=(\S+)")
_ROUTE_ID_A = re.compile(r'data-route-id="([^"]+)"')


# ------------------------------------------------------------------ sandbox
def set_root(path) -> None:
    """Redirect every glue write (readings/ledger/stats) into ``path``.

    Default = the real out/v4.2-judge-qual-r1/.  The synthetic-session
    self-test points this at a tmp sandbox so the real readings tree,
    ledger and stats are never touched.
    """
    global JQ_OUT_DIR, READINGS_ROOT, TEMPLATES_PATH, LEDGER_PATH
    JQ_OUT_DIR = Path(path)
    READINGS_ROOT = JQ_OUT_DIR / "readings"
    TEMPLATES_PATH = JQ_OUT_DIR / "templates.json"
    LEDGER_PATH = JQ_OUT_DIR / "ledger.jsonl"


# ------------------------------------------------------------------ ledger
def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _append_event(event: dict) -> None:
    """Append one JSONL ledger line (append-only, never rewrites)."""
    event = dict(event)
    event.setdefault("ts", _now_ts())
    line = json.dumps(event, sort_keys=True, ensure_ascii=False)
    with open(LEDGER_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _ledger_events() -> list:
    if not LEDGER_PATH.exists():
        return []
    return [json.loads(ln) for ln in
            LEDGER_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]


def log_arm_start(arm: str, rep: int) -> None:
    """R3-shape subject-arm-start event (orchestrator calls per arm/rep)."""
    if arm not in ARMS or rep not in REPS:
        raise RuntimeError("log_arm_start: arm %r rep %r off-grid" % (arm, rep))
    _append_event({"event": "subject-arm-start", "arm": arm, "rep": rep})


def log_session_start(session: str, arm: str, rep: int, batch: int) -> None:
    """R3-shape subject-session-start event (orchestrator calls at open)."""
    if arm not in ARMS or rep not in REPS or batch not in BATCH_PIDS:
        raise RuntimeError("log_session_start: (%r,%r,%r) off-grid"
                           % (arm, rep, batch))
    _append_event({"event": "subject-session-start", "session": session,
                   "arm": arm, "rep": rep, "batch": batch})


# ------------------------------------------------- marker contract helpers
def marker_line(pid: str) -> str:
    return PACK_MARKER_TEMPLATE.format(pid=pid)


def split_session_output(text: str, pids: list) -> dict:
    """Split a full subject reply by the ``===PACK pNN===`` markers.

    Returns ``{ok, problems, bodies: {pid: body}}``.  Hard checks: the
    reply consists only of marker-introduced sections; the marker
    sequence equals ``pids`` (no missing pack, no unknown/duplicate
    marker); each marker occupies its own line (``^===PACK pNN==$``).
    """
    problems: list = []
    bodies: dict = {}
    seen: list = []
    current = None
    for ln in text.splitlines():
        m = PACK_MARKER_LINE_RE.match(ln)
        if m is not None:
            if m.group(1) in seen:
                problems.append("duplicate marker %s" % m.group(1))
            seen.append(m.group(1))
            current = m.group(1)
            bodies[current] = []
            continue
        if current is not None:
            bodies[current].append(ln)
        elif ln.strip() != "":
            problems.append("non-empty content before the first marker: %r"
                            % ln[:80])
    if seen != list(pids):
        problems.append("marker sequence %s != pids %s" % (seen, list(pids)))
    out_bodies = {pid: "\n".join(bodies.get(pid, [])) for pid in pids}
    return {"ok": not problems, "problems": problems, "bodies": out_bodies}


def _extract_flags_json(body: str, pid: str) -> tuple:
    """Mechanical JSON extraction of the judgment body (no solver/GT).

    Returns (obj_or_None, problems).  Accepts the JSON OBJECT exactly
    (frozen tail contract: exactly one key ``flags``), or the same
    object embedded in surrounding prose/markdown fences (first ``{``
    to the last ``}``).  Nothing is interpreted beyond parsing.
    """
    problems: list = []
    text = body.strip()
    obj = None
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        lo, hi = text.find("{"), text.rfind("}")
        if lo == -1 or hi == -1 or hi <= lo:
            problems.append("%s: judgment body is not JSON (no object found)"
                            % pid)
        else:
            try:
                obj = json.loads(text[lo:hi + 1])
                problems.append("%s: judgment body had surrounding non-JSON "
                                "text (mechanically stripped)" % pid)
            except (json.JSONDecodeError, ValueError):
                problems.append("%s: judgment body is not a parsable JSON "
                                "object" % pid)
    if obj is not None and (not isinstance(obj, dict)
                            or set(obj) != {"flags"}):
        problems.append("%s: judgment body is not a JSON OBJECT with exactly "
                        "one key 'flags' (got %s)"
                        % (pid, sorted(obj) if isinstance(obj, dict)
                           else type(obj).__name__))
        obj = None
    return obj, problems


def _route_set_from_pack(arm: str, pid: str) -> set:
    """Route-id reference set from the FROZEN PACK TEXT (blinding-safe).

    Q (B-v1 intent pack): the ``route_id=`` values of [segment-index];
    CTR (r2 SVG form): the unique ``data-route-id`` attribute values.
    PREREG-REP-R2 section 7 rule 2 references; no gt.json / package-
    meta access anywhere in the ingest path.
    """
    pack = _load_json(PACK_DIRS[arm] / ("%s.json" % pid))
    user = pack["user"]
    if arm == "Q":
        rids = set(_ROUTE_ID_B.findall(user))
    else:
        # the reference is the set of distinct route ids (an attribute
        # may repeat across a route's geometry elements)
        rids = set(_ROUTE_ID_A.findall(user))
    if not rids:
        raise RuntimeError("%s: no route ids found in the frozen %s pack"
                           % (pid, arm))
    return rids


def _reading_path(arm: str, rep: int, pid: str, attempt: int) -> Path:
    name = "%s.json" % pid if attempt <= 1 else "%s-r%d.json" % (pid,
                                                                 attempt - 1)
    return _reading_dir(READINGS_ROOT, arm, rep) / name


def _resolve_session_files(directory: Path, pids: list) -> tuple:
    """Session-scoped twin of ``scoring._resolve_reading_files``.

    Same '-rN' resolution semantics, restricted to the session's pid
    set: readings of the OTHER batch sharing the arm/rep directory are
    ignored (the R2 layout puts one arm/rep's two batch sessions in
    one directory; ``scoring_jq`` later resolves the full 16-pid grid
    with the frozen resolver).  Unrecognized filenames still raise.
    """
    per_pid: dict = {pid: {} for pid in pids}
    for entry in sorted(directory.iterdir()):
        if entry.suffix != ".json":
            continue
        m = scoring._READING_NAME_RE.match(entry.name)
        if m is None:
            raise RuntimeError("unrecognized reading filename %s in %s"
                               % (entry.name, directory))
        pid, rno = m.group(1), int(m.group(2) or 0)
        if pid not in per_pid:
            continue
        if rno in per_pid[pid]:
            raise RuntimeError("duplicate retry number for %s: %s"
                               % (pid, entry.name))
        per_pid[pid][rno] = entry.name
    chosen, superseded = {}, {}
    for pid in pids:
        if not per_pid[pid]:
            raise RuntimeError("no reading file for %s in %s"
                               % (pid, directory))
        top = max(per_pid[pid])
        chosen[pid] = per_pid[pid][top]
        rest = [per_pid[pid][r] for r in sorted(per_pid[pid]) if r != top]
        if rest:
            superseded[pid] = rest
    return chosen, superseded


# ------------------------------------------------------------- ingest_pack
def ingest_pack(pid: str, raw: str, session: str, arm: str, rep: int,
                batch: int, attempt: int, pids: list) -> dict:
    """Ingest one pack's subject output; see the module docstring (1).

    The reading file is ALWAYS written (fail-closed record, append-
    only); ``ok`` is true only when the structural + six-rule checks
    all pass (``validation.passed`` mirrors ``ok``).
    """
    problems: list = []
    # ---- argument / grid checks (fail fast, nothing written)
    if arm not in ARMS:
        return {"ok": False, "problems": ["arm %r not in %s" % (arm, ARMS)]}
    if rep not in REPS:
        return {"ok": False, "problems": ["rep %r not in %s" % (rep, REPS)]}
    if batch not in BATCH_PIDS:
        return {"ok": False, "problems": ["batch %r not in (1, 2)" % batch]}
    if not isinstance(attempt, int) or isinstance(attempt, bool) \
            or attempt < 1:
        return {"ok": False, "problems": ["attempt %r is not an int >= 1"
                                          % (attempt,)]}
    if pid not in BATCH_PIDS[batch]:
        problems.append("pid %r does not belong to batch %d (%s)"
                        % (pid, batch, list(BATCH_PIDS[batch])))
    if pid not in pids:
        problems.append("pid %r not in the session pid list" % pid)
    if sorted(pids) != list(BATCH_PIDS[batch]):
        problems.append("pids %s != batch %d pid set %s"
                        % (sorted(pids), batch, list(BATCH_PIDS[batch])))
    if problems:
        return {"ok": False, "problems": problems}
    if not isinstance(raw, str) or raw == "":
        return {"ok": False, "problems": ["%s: raw output is empty/not a "
                                          "string" % pid]}

    # ---- marker contract: first line is exactly ===PACK <this pid>===
    first_nl = raw.find("\n")
    first_line = raw if first_nl == -1 else raw[:first_nl]
    body = "" if first_nl == -1 else raw[first_nl + 1:]
    m = PACK_MARKER_LINE_RE.match(first_line.rstrip("\r"))
    if m is None:
        problems.append("%s: output does not begin with the dedicated marker "
                        "line %r (first line %r)"
                        % (pid, marker_line(pid), first_line[:80]))
    elif m.group(1) != pid:
        problems.append("%s: marker names pack %s, expected %s"
                        % (pid, m.group(1), pid))

    # ---- judgment body -> flags (mechanical extraction only)
    flags_obj, body_problems = _extract_flags_json(body, pid)
    problems.extend(body_problems)

    # ---- structural + six-rule validation vs the frozen package
    if flags_obj is not None:
        shim = {"pid": pid, "arm": arm, "schema": READING_SCHEMA,
                "flags": flags_obj["flags"]}
        try:
            route_set = _route_set_from_pack(arm, pid)
            checked = _check_structure(shim, pid, route_set, expect_arm=arm,
                                       expect_schema=READING_SCHEMA)
            problems.extend(validate_six_rules(checked, route_set))
        except RuntimeError as exc:
            problems.append("%s: structural violation: %s" % (pid, exc))

    # ---- first-attempt errors (retry files carry attempt 1's record)
    first_attempt_errors: list = []
    if attempt >= 2:
        base = _reading_dir(READINGS_ROOT, arm, rep) / ("%s.json" % pid)
        if not base.exists():
            problems.append("%s: attempt %d has no attempt-1 reading %s"
                            % (pid, attempt, base.name))
        else:
            prev = _load_json(base)
            first_attempt_errors = list(prev["validation"]["errors"])

    # ---- write the reading (append-only; existing names never rewritten)
    out_path = _reading_path(arm, rep, pid, attempt)
    if out_path.exists():
        return {"ok": False,
                "problems": ["%s: reading %s already exists (append-only "
                             "lock; use the next attempt number)"
                             % (pid, out_path.name)]}
    validation = {"errors": problems,
                  "first_attempt_errors": first_attempt_errors,
                  "passed": not problems, "retry": attempt - 1}
    reading = {"schema": READING_SCHEMA, "arm": arm, "rep": rep, "pid": pid,
               "return_raw": raw,
               "model_output": (flags_obj["flags"]
                                if flags_obj is not None else []),
               "validation": validation, "ts": _now_ts()}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_canonical(out_path, reading)
    if attempt >= 2:
        _append_event({"event": "schema-retry", "session": session,
                       "arm": arm, "rep": rep, "batch": batch, "pid": pid,
                       "attempt": attempt, "file": out_path.name})
    return {"ok": not problems, "problems": problems}


# --------------------------------------------------------- finalize_session
def _session_ask(session: str, arm: str, rep: int, batch: int) -> dict:
    """Rebuild the session ask from templates.json + frozen pack files."""
    tpl = _load_json(TEMPLATES_PATH)
    key = "q" if arm == "Q" else "ctr"
    system = tpl["%s_system" % key]
    head, tail = tpl["%s_head" % key], tpl["%s_tail" % key]
    pids = list(BATCH_PIDS[batch])
    asks = []
    for pid in pids:
        pack = _load_json(PACK_DIRS[arm] / ("%s.json" % pid))
        user = pack["user"]
        if not (user.startswith(head) and user.endswith(tail)
                and len(head) + len(tail) <= len(user)):
            raise RuntimeError("%s: frozen user text does not decompose as "
                               "head+middle+tail (templates drift)" % pid)
        asks.append([pid, system, user])
    obj = {"schema": SESSION_ASK_SCHEMA, "arm": arm, "rep": rep,
           "batch": batch, "session": session, "pid_order": pids,
           "asks": asks}
    digest = hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()
    return {"obj": obj, "sha256": digest, "pids": pids}


def finalize_session(session: str, arm: str, rep: int, batch: int) -> dict:
    """Verify the 8 packs, pin ask_sha256, append reading-append events."""
    if arm not in ARMS:
        return {"ok": False, "n": 0, "problems": ["arm %r not in %s"
                                                  % (arm, ARMS)]}
    if rep not in REPS:
        return {"ok": False, "n": 0, "problems": ["rep %r not in %s"
                                                  % (rep, REPS)]}
    if batch not in BATCH_PIDS:
        return {"ok": False, "n": 0, "problems": ["batch %r not in (1, 2)"
                                                  % (batch,)]}

    # already finalized? (append-only ledger: never emit duplicates)
    for evt in _ledger_events():
        if evt.get("event") == "reading-append" and \
                evt.get("session") == session:
            return {"ok": False, "n": 0,
                    "problems": ["session %r already has reading-append "
                                 "events (append-only ledger)" % session]}

    pids = list(BATCH_PIDS[batch])
    directory = _reading_dir(READINGS_ROOT, arm, rep)
    try:
        chosen, _superseded = _resolve_session_files(directory, pids)
    except (RuntimeError, FileNotFoundError) as exc:
        return {"ok": False, "n": 0,
                "problems": ["%s/rep%d: %s" % (arm, rep, exc)]}
    problems: list = []
    n = 0
    ask = _session_ask(session, arm, rep, batch)
    ask_chars = {pid: len(system) + len(user)
                 for pid, system, user in ask["obj"]["asks"]}
    for pid in pids:
        data = _load_json(directory / chosen[pid])
        if data.get("validation", {}).get("passed") is not True:
            problems.append("%s: resolved reading %s is not validation-passed"
                            % (pid, chosen[pid]))
            continue
        raw_bytes = (directory / chosen[pid]).read_bytes()
        _append_event({
            "event": "reading-append", "session": session, "arm": arm,
            "rep": rep, "batch": batch, "pid": pid, "file": chosen[pid],
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "ask_chars": ask_chars[pid],
            "return_chars": len(data["return_raw"]),
        })
        n += 1
    if problems:
        return {"ok": False, "n": n, "problems": problems}
    # session-level ask pin (additive tooling event; see module docstring)
    _append_event({"event": "session-ask-pinned", "session": session,
                   "arm": arm, "rep": rep, "batch": batch,
                   "ask_sha256": ask["sha256"], "pid_order": ask["pids"]})
    return {"ok": True, "n": n, "problems": [], "ask_sha256": ask["sha256"]}


# --------------------------------------------------------- finish_and_score
def finish_and_score() -> dict:
    """gt-unseal -> score_jq -> scoring-done; return the five gates."""
    events = _ledger_events()
    finalized = {evt.get("session") for evt in events
                 if evt.get("event") == "reading-append"}
    n_append = sum(1 for evt in events
                   if evt.get("event") == "reading-append")
    if n_append != 96 or len(finalized) != 12:
        return {"ok": False, "gates": {}, "summary": {"n_readings":
                                                      n_append},
                "problems": ["expected 12 finalized sessions / 96 "
                             "reading-append events, found %d events over "
                             "%d sessions" % (n_append, len(finalized))]}
    if any(evt.get("event") == "gt-unseal" for evt in events):
        return {"ok": False, "gates": {}, "summary": {"n_readings":
                                                      n_append},
                "problems": ["gt-unseal already recorded (append-only)"]}

    _append_event({"event": "gt-unseal"})
    try:
        result = scoring_jq.score_jq(readings_root=READINGS_ROOT,
                                      out_dir=JQ_OUT_DIR)
    except RuntimeError as exc:
        return {"ok": False, "gates": {}, "summary": {"n_readings":
                                                      n_append},
                "problems": ["score_jq refused: %s" % exc]}
    _append_event({"event": "scoring-done",
                   "all_passed": result["qualification"]["all_passed"]})
    qual = result["qualification"]
    summary = {"n_readings": sum(result["arms"][arm]["n_readings"]
                                 for arm in ARMS),
               "all_passed": qual["all_passed"],
               "gates_failed": qual["gates_failed"],
               "written": [str(p) for p in result["written"]]}
    return {"ok": True, "gates": qual["gates"], "summary": summary}


# ------------------------------------------------------------- self_test()
def self_test(sandbox_dir) -> str:
    """Synthetic-session self-test (the mandatory rig check).

    Builds a full synthetic batch (2 arms x 3 reps x 2 batches = 12
    sessions, 96 packs) whose judgment bodies are the REAL R2 subject
    judgments read from out/v4.2-rep-r2/readings/ (Q <- B arm, CTR <-
    A arm, rep-for-rep -- the two frozen input forms this batch
    reuses; R2 readings carry no return_raw field, the five-key R2
    realized shape, so the raw text is rebuilt verbatim as the R3-
    realized return_raw form ``{"flags": [...]}`` and prefixed with
    the ===PACK pNN=== marker), then runs ingest_pack x96 ->
    finalize_session x12 -> finish_and_score INSIDE ``sandbox_dir``
    (set_root; the real out/v4.2-judge-qual-r1 readings/ledger/stats
    are untouched; the sandbox ledger is seeded with the real freeze
    line for shape fidelity).  Returns a one-line status string.
    """
    import shutil
    sandbox_dir = Path(sandbox_dir)
    if sandbox_dir.exists():
        raise RuntimeError("self_test sandbox %s already exists (refusing to "
                           "reuse)" % sandbox_dir)
    sandbox_dir.mkdir(parents=True)
    shutil.copyfile(REAL_JQ_OUT_DIR / "templates.json",
                    sandbox_dir / "templates.json")
    real_ledger = REAL_JQ_OUT_DIR / "ledger.jsonl"
    set_root(sandbox_dir)
    try:
        if real_ledger.exists():
            first = real_ledger.read_text(encoding="utf-8").splitlines()[0]
            with open(LEDGER_PATH, "a", encoding="utf-8") as fh:
                fh.write(first + "\n")
        r2_root = ROOT / "out" / "v4.2-rep-r2" / "readings"
        src_arm = {"Q": "B", "CTR": "A"}
        n_ok = 0
        failures = []
        ask_digests = []
        for arm in ARMS:
            for rep in REPS:
                for batch in (1, 2):
                    session = "selftest-%s-rep%d-b%d" % (arm.lower(), rep,
                                                         batch)
                    log_session_start(session, arm, rep, batch)
                    for pid in BATCH_PIDS[batch]:
                        src = _load_json(r2_root / src_arm[arm]
                                         / ("rep%d" % rep)
                                         / ("%s.json" % pid))
                        raw = marker_line(pid) + "\n" + \
                            json.dumps({"flags": src["flags"]},
                                       ensure_ascii=False)
                        res = ingest_pack(pid, raw, session, arm, rep,
                                          batch, 1, list(BATCH_PIDS[batch]))
                        if res["ok"]:
                            n_ok += 1
                        else:
                            failures.append("%s/%s: %s"
                                            % (session, pid, res["problems"]))
                    fin = finalize_session(session, arm, rep, batch)
                    if not fin["ok"]:
                        failures.append("finalize %s: %s"
                                        % (session, fin["problems"]))
                    else:
                        ask_digests.append(fin["ask_sha256"])
        fin_line = finish_and_score()
        n_gates = len(fin_line.get("gates") or {})
        if failures or not fin_line["ok"] or n_gates != 5:
            return ("SELFTEST FAIL: ingest_ok=%d/96 finalize_fail=%d "
                    "finish_ok=%r gates=%d first_failures=%s"
                    % (n_ok, sum(1 for f in failures
                                 if f.startswith("finalize")),
                       fin_line.get("ok"), n_gates, failures[:3]))
        gates = fin_line["gates"]
        return ("SELFTEST PASS: sandbox=%s ingest 96/96 ok, finalize 12/12 "
                "(n=8 each, 96 reading-append events, 12 ask_sha256 pins), "
                "finish_and_score ok with five gates %s gates_failed=%s "
                "(synthetic material: R2 real judgments Q<-B/CTR<-A, "
                "rep-for-rep; R2 readings carry no return_raw -> raw "
                "rebuilt as R3-shape {\"flags\":[...]} + ===PACK pNN=== "
                "marker)" % (sandbox_dir,
                             {g: gates[g]["passed"] for g in sorted(gates)},
                             fin_line["summary"]["gates_failed"]))
    finally:
        set_root(REAL_JQ_OUT_DIR)


if __name__ == "__main__":
    print("jq_glue: use ingest_pack/finalize_session/finish_and_score from "
          "the orchestrator; self_test(sandbox_dir) for the rig check")
