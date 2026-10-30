"""V4.2 M1 inspector harness: blinded v4-svg-route-2 packages -> tested model.

prereg-m1 inspector_contract_v1: input = the SVG source of a v4-svg-route-2
route package built by pcbflow/svg_route_package.py (read-only import) over
the synthetic board snapshot + the stable-order incumbent run; presented
text is blinded (scenario_id -> opaque pid; no family/split/label/seed
tokens -- test-enforced).  Machine facts live ONLY in data-* attributes
(colors are encodings).  The task text carries the P0-c hardened output
contract (exact object shape, exact enums, one entry per route, no
duplicates) and the mandatory routing-workspace disclosure.

All judgment calls go to the TESTED model (GLM-5.3-Flash) via
flash_probe.call_flash -- dual-model separation §2.7 (dev-side model never
produces readings).  API key only ever enters the Authorization header via
the orchestrator's environment variable.
"""

import hashlib
import re

from pcbflow import svg_route_package as srp
from pcbflow.v4_2.flash_probe import (call_flash, validate_flag_response,
                                      _parse_content_json)

INSPECTOR_SYSTEM = (
    "You are a PCB routing inspector reading the SVG source of a routed "
    "two-layer board (schema v4-svg-route-2). Machine facts live ONLY in "
    "data-* attributes; colors, classes and line styles are visual "
    "encodings and carry no fact. You can only ADD flags: you never modify "
    "geometry, never execute changes, never drop existing flags. For every "
    "route in the package output exactly one entry. Use abstain when the "
    "facts are insufficient for a judgment. Respond with JSON only."
)

_JUDGE_SUFFIX = """
Judge every route. Output shape: a JSON OBJECT with exactly one key "flags" whose value is an array with EXACTLY ONE entry per route in the package (no duplicates, none missing). Each entry: {"route_id", "verdict", "reason_code", "evidence"}.
- verdict must be exactly one of: flag_bad, no_flag, abstain.
- reason_code must be EXACTLY one of these strings and nothing else: detour_excess, congestion_crossing, blocks_escape, clearance_risk, suboptimal_layer, uncertain.
- evidence must cite the specific data-* fact you used (route attribute, keepout rect, pad position, via placement).
- An empty flags array means no_flag for every route (that is a valid answer; do not force flags).
Coordinate frame: the SVG viewBox is the board frame in mm (y grows downward per the root data-y-axis attribute). IMPORTANT: routing is LEGAL up to 2.0 mm beyond the board outline on all four sides (routing workspace margin); geometry outside the board edge but within that band is NOT a defect.
JSON only."""

_IDENTITY_RE = re.compile(r"(?:hol-|cal-|dev-|\bf[0-9]\b)")


def package_svg(board, run):
    """v4-svg-route-2 SVG source for a synthetic board + incumbent run.

    Solver route dicts are enriched to the v2 production contract with the
    three fields v4exp does not emit: relation_ids (board relation
    membership), line_type (net class mapping: clock -> clock, else
    signal), constraint_refs (no constraints in the synthetic domain ->
    empty list).  Everything else passes through untouched.
    """
    rel_of = {}
    for rel in board.get("relations") or []:
        for nid in rel.get("members") or rel.get("nets") or []:
            rel_of.setdefault(str(nid), []).append(str(rel.get("relation_id")))
    classes = {str(n["net_id"]): str(n.get("net_class", "default"))
               for n in board["nets"]}
    routes = []
    for r in run["routes"]:
        rid = str(r["route_id"])
        poly = list(r["polyline_mm"])
        if len(poly) < 2:
            # solver single-cell runs (pad cell == via landing) are
            # degenerate zero-length stubs: serialize as a zero-length
            # 2-point segment (v2 contract minimum; the route stays visible
            # and flaggable -- never hidden). prereg note 1.
            poly = [poly[0], poly[0]]
        routes.append(dict(r,
                           polyline_mm=poly,
                           relation_ids=rel_of.get(str(r["net_id"]), []),
                           line_type=("clock"
                                      if classes.get(str(r["net_id"])) == "clock"
                                      else "signal"),
                           constraint_refs=[]))
    svg, _manifest = srp.build(board, {"routes": routes,
                                       "vias": run["vias"]})
    return svg


def assign_pids(sids):
    """Deterministic opaque ids: sort sids by sha256, enumerate p01.. (prereg)."""
    ordered = sorted(sids, key=lambda s: hashlib.sha256(s.encode()).hexdigest())
    return {sid: "p%02d" % (i + 1) for i, sid in enumerate(ordered)}


def blind(svg_text, sid, pid):
    """Strip scenario identity from the presented text (prereg blinding)."""
    blinded = svg_text.replace(sid, pid)
    if _IDENTITY_RE.search(blinded):
        hits = sorted(set(m.group(0) for m in _IDENTITY_RE.finditer(blinded)))
        raise ValueError("blinding leak: identity tokens remain: %s" % hits)
    return blinded


def inspector_task(svg_text, pid):
    return {"pid": pid, "system": INSPECTOR_SYSTEM,
            "user": svg_text + "\n" + _JUDGE_SUFFIX}


def run_inspector(endpoint, model, sampling, task, api_key, timeout_s=110,
                  reasoning_shape=None):
    """One tested-model inspector call -> reading dict (never raises on bad
    payloads; every failure is a recorded, visible outcome)."""
    shape = reasoning_shape or {"reasoning_effort": "low"}
    reading = call_flash(endpoint, api_key, model, task, sampling, shape,
                         timeout_s)
    reading["pid"] = task["pid"]
    if reading.get("http_status") == 200:
        parsed, perr = _parse_content_json(reading.pop("content", None))
        reading["parse_ok"] = parsed is not None
        reading["parse_error"] = perr
        reading["validation"] = validate_flag_response(parsed)
        reading["model_output"] = parsed
    return reading
