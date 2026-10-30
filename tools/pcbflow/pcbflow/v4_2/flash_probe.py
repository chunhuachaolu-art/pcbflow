"""P0-c tested-model probe plumbing (GLM-5.3-Flash) -- taskbook §3 M0.

Measures, for the M1 flag contract v1 draft round trip: HTTP connectivity,
structured-output schema compliance, enum-violation rate, refusal rate,
latency and token usage.  Readings feed the M1 calibration band setting --
judgment quality is NOT measured here (that is M1's job).

Dual-model separation (taskbook §2.7): every reading in this module is
produced by the tested model via direct API calls.  The API key is taken
from the environment (ZCODE_BIGMODEL_KEY) by the orchestrator and must
never appear in any file this module writes or prints.

Network I/O lives here on the orchestration side only; nothing in this
module is imported by solver/validator core paths (taskbook §2 red line
"no network subprocesses in core" preserved).

Run:  ZCODE_BIGMODEL_KEY=... python -m pcbflow.v4_2.flash_probe < job.json
       (job.json schema: see run_probe docstring)  -> verdict JSON on stdout

RETIRED 2026-09-13 (ADJUDICATION R46 + user-level AGENTS.md ban on
out-of-harness LLM API calls): the call_flash external-API form is
archive-only -- r1 historical evidence, do not invoke for new work.
Model-side work now runs inside the ZCode harness (session-driven or
subagent; see exec/prompts/V4.2-R2-TESTED-MODEL-SWAP-PROMPT.md).
Pure helpers (build_task, validate_flag_response) remain reusable as
contract references.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

from pcbflow.v4exp.grid import canonical_json
from pcbflow.v4exp.router import solve_board

FLAG_VERDICTS = ("flag_bad", "no_flag", "abstain")
#: Draft enum -- plumbing probe only; the real reason_code enum is frozen
#: in the M1 pre-registration (taskbook §3 M1).
REASON_CODES_DRAFT = ("detour_excess", "congestion_crossing", "blocks_escape",
                      "clearance_risk", "suboptimal_layer", "uncertain")

FLAG_SCHEMA_NAME = "flag_contract_v1"

FLAG_TASK_SYSTEM = (
    "You are a PCB routing inspector. You read machine facts about routed "
    "traces on a two-layer board and judge, per trace, whether it looks "
    "like an improvable/bad route. You can only ADD flags: you never "
    "modify geometry, never execute changes, never drop existing flags. "
    "For every route listed, output exactly one entry. Use abstain when "
    "the facts are insufficient for a judgment. Respond with JSON only, "
    "matching the provided schema."
)


def flag_contract_schema():
    """Strict json_schema for the flag contract v1 draft (response_format)."""
    return {
        "type": "object",
        "properties": {
            "flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "route_id": {"type": "string"},
                        "verdict": {"type": "string",
                                    "enum": list(FLAG_VERDICTS)},
                        "reason_code": {"type": "string",
                                        "enum": list(REASON_CODES_DRAFT)},
                        "evidence": {"type": "string"},
                    },
                    "required": ["route_id", "verdict", "reason_code",
                                 "evidence"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["flags"],
        "additionalProperties": False,
    }


def _route_facts(routes):
    out = []
    for r in routes:
        poly = r["polyline_mm"]
        bends = 0
        for i in range(2, len(poly)):
            dx1 = poly[i - 1][0] - poly[i - 2][0]
            dy1 = poly[i - 1][1] - poly[i - 2][1]
            dx2 = poly[i][0] - poly[i - 1][0]
            dy2 = poly[i][1] - poly[i - 1][1]
            if (dx1 > 0) != (dx2 > 0) or (dy1 > 0) != (dy2 > 0):
                bends += 1
        length = sum(((poly[i][0] - poly[i - 1][0]) ** 2
                      + (poly[i][1] - poly[i - 1][1]) ** 2) ** 0.5
                     for i in range(1, len(poly)))
        out.append({"route_id": r["route_id"], "layer": r["layer"],
                    "width_mm": r["width_mm"],
                    "length_mm": round(length, 3), "bend_count": bends,
                    "polyline_mm": poly})
    return out


def build_task(board, pid):
    """Blinded inspector task from a scenario snapshot (label/family/split/
    seed/scenario_id stripped; deterministic stable-order solve for facts)."""
    req = {"route_order": sorted(n["net_id"] for n in board["nets"]),
           "group": "A"}
    run = solve_board(board, req)
    keepouts = [[[float(v) for v in ko["rect_mm"]],
                 [str(s) for s in ko.get("layers", [])]]
                for ko in board.get("keepouts", [])]
    facts = {
        "board": {"bbox_mm": [float(v) for v in board["board"]["bbox_mm"]],
                  "layers": [str(s) for s in board["board"]["layers"]],
                  "keepouts": keepouts, "n_nets": len(board["nets"])},
        "routes": _route_facts(run["routes"]),
    }
    user = ("Board and route machine facts (coordinates in mm, origin at "
            "bbox lower-left; polylines are centre-lines):\n"
            + json.dumps(facts, ensure_ascii=True, sort_keys=True)
            + "\n\nJudge every route: for each route_id output "
              "{\"route_id\", \"verdict\" in {flag_bad, no_flag, abstain}, "
              "\"reason_code\" from the enum, \"evidence\" citing the fact "
              "you used (e.g. polyline segment / keepout rect). JSON only.")
    return {"pid": pid, "system": FLAG_TASK_SYSTEM, "user": user,
            "n_routes": len(facts["routes"])}


def validate_flag_response(obj):
    """Hand-rolled strict validation of the flag contract (no external deps).

    Returns schema/enum readings; never raises on bad payloads.
    """
    res = {"schema_pass": False, "errors": [], "enum_violations": [],
           "n_flags": 0, "n_flag_bad": 0, "n_no_flag": 0, "n_abstain": 0,
           "abstain_rate": None}
    if not isinstance(obj, dict) or not isinstance(obj.get("flags"), list):
        res["errors"].append("top-level object with 'flags' array missing")
        return res
    for i, fl in enumerate(obj["flags"]):
        if not isinstance(fl, dict):
            res["errors"].append("flag[%d] not an object" % i)
            continue
        for k in ("route_id", "verdict", "reason_code", "evidence"):
            if k not in fl or not isinstance(fl[k], str) or not fl[k]:
                res["errors"].append("flag[%d] missing/empty %s" % (i, k))
        if fl.get("verdict") not in FLAG_VERDICTS:
            res["enum_violations"].append(
                "flag[%d] verdict=%r" % (i, fl.get("verdict")))
        if fl.get("reason_code") not in REASON_CODES_DRAFT:
            res["enum_violations"].append(
                "flag[%d] reason_code=%r" % (i, fl.get("reason_code")))
    res["n_flags"] = len(obj["flags"])
    verdicts = [fl.get("verdict") for fl in obj["flags"]
                if isinstance(fl, dict)]
    res["n_flag_bad"] = verdicts.count("flag_bad")
    res["n_no_flag"] = verdicts.count("no_flag")
    res["n_abstain"] = verdicts.count("abstain")
    if verdicts:
        res["abstain_rate"] = round(res["n_abstain"] / len(verdicts), 4)
    res["schema_pass"] = not res["errors"] and not res["enum_violations"]
    return res


def _extract_content(body):
    """chat-completions body -> (text, finish_reason, usage_dict)."""
    text = None
    finish = None
    usage = {}
    try:
        choices = body.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            text = msg.get("content")
            finish = choices[0].get("finish_reason")
        usage = body.get("usage") or {}
    except (AttributeError, TypeError):
        pass
    return text, finish, usage


def _looks_like_param_error(err_text):
    t = (err_text or "").lower()
    return any(s in t for s in ("reasoning_effort", "thinking", "unknown",
                                "invalid parameter", "unexpected"))


def call_flash(endpoint, api_key, model, task, sampling, reasoning_shape,
               timeout_s):
    """One POST /chat/completions call. Returns a readings dict; the API
    key is used only in the Authorization header and never echoed."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": task["system"]},
            {"role": "user", "content": task["user"]},
        ],
        "temperature": float(sampling.get("temperature", 0.1)),
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": FLAG_SCHEMA_NAME,
                                            "strict": True,
                                            "schema": flag_contract_schema()}},
    }
    if reasoning_shape:
        body.update(reasoning_shape)
    req = urllib.request.Request(
        endpoint, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key},
        method="POST")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            http_status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        http_status = e.code
    except Exception as e:  # network layer: recorded as transport failure
        return {"http_status": None, "error": "%s: %s" % (type(e).__name__, e),
                "latency_ms": int((time.monotonic() - t0) * 1000)}
    latency_ms = int((time.monotonic() - t0) * 1000)
    reading = {"http_status": http_status, "latency_ms": latency_ms}
    try:
        body_json = json.loads(raw)
    except ValueError:
        reading["error"] = "non-JSON body"
        reading["raw_excerpt"] = raw[:300]
        return reading
    if http_status != 200:
        reading["error"] = (body_json.get("error") or {}).get("message", "")[:300]
        reading["param_error"] = _looks_like_param_error(reading["error"])
        return reading
    text, finish, usage = _extract_content(body_json)
    reading["finish_reason"] = finish
    reading["usage"] = {"prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens")}
    reading["content"] = text
    return reading


def _parse_content_json(text):
    """Best-effort strict-then-lenient parse of the model content."""
    if not isinstance(text, str) or not text.strip():
        return None, "empty content"
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
    try:
        return json.loads(t), None
    except ValueError as e:
        return None, "json parse: %s" % e


def run_probe(job):
    """job keys: endpoint, model, sampling {temperature}, timeout_s,
    reasoning_param_shapes (list, tried in order; first that yields HTTP 200
    is frozen for the rest of the run), tasks (list of build_task outputs),
    task_repeats (int, default 1).
    Returns the verdict dict (no key material anywhere)."""
    api_key = os.environ.get("ZCODE_BIGMODEL_KEY", "")
    if not api_key:
        return {"error": "ZCODE_BIGMODEL_KEY not set"}
    endpoint = job["endpoint"]
    model = job["model"]
    sampling = job.get("sampling", {"temperature": 0.1})
    timeout_s = int(job.get("timeout_s", 120))
    shapes = job.get("reasoning_param_shapes") or [{"reasoning_effort": "low"}]
    repeats = int(job.get("task_repeats", 1))
    verdict = {"model": model, "endpoint": endpoint, "sampling": sampling,
               "reasoning_shapes_tried": shapes, "working_reasoning_shape": None,
               "calls": []}
    for task in job["tasks"]:
        for rep in range(repeats):
            for shape in shapes:
                reading = call_flash(endpoint, api_key, model, task,
                                     sampling, shape, timeout_s)
                reading["pid"] = task["pid"]
                reading["repeat"] = rep
                reading["n_routes"] = task["n_routes"]
                if reading.get("http_status") == 200:
                    parsed, perr = _parse_content_json(reading.pop("content", None))
                    if parsed is None:
                        reading["parse_ok"] = False
                        reading["parse_error"] = perr
                        reading["validation"] = validate_flag_response(None)
                    else:
                        reading["parse_ok"] = True
                        reading["model_output"] = parsed
                        reading["validation"] = validate_flag_response(parsed)
                    verdict["working_reasoning_shape"] = shape
                    verdict["calls"].append(reading)
                    break
                # param-shaped 400 -> try next shape; other errors -> record
                if not reading.get("param_error"):
                    verdict["calls"].append(reading)
                    break
    ok = [c for c in verdict["calls"] if c.get("http_status") == 200]
    refused = [c for c in ok
               if c.get("finish_reason") not in (None, "stop")
               or not c.get("parse_ok")]
    enum_bad = [c for c in ok
                if c.get("validation", {}).get("enum_violations")]
    schema_bad = [c for c in ok if not c.get("validation", {}).get("schema_pass")]
    usage_tot = sum((c.get("usage") or {}).get("total_tokens") or 0 for c in ok)
    lat = [c["latency_ms"] for c in ok]
    verdict["summary"] = {
        "n_calls": len(verdict["calls"]),
        "http_ok": len(ok),
        "parse_ok": sum(1 for c in ok if c.get("parse_ok")),
        "schema_pass": len(ok) - len(schema_bad),
        "enum_violation_calls": len(enum_bad),
        "refusal_or_unparseable_calls": len(refused),
        "mean_latency_ms": (sum(lat) // len(lat)) if lat else None,
        "tested_side_total_tokens": usage_tot,
    }
    return verdict


def main():
    job = json.loads(sys.stdin.read())
    sys.stdout.write(json.dumps(run_probe(job), ensure_ascii=True, indent=1))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
