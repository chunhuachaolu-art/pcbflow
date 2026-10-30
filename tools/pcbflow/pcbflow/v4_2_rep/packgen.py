"""REP-R1 B-arm structured intent pack generator (PACK-SPEC-REP-R1.md v1).

Generation path (taskbook A4 + PACK-SPEC §6):
  board snapshot (read-only json) -> Board object construction ->
  pcbflow.v4_2.gt.incumbent_run (frozen deterministic re-solve) ->
  serialize structured intent pack per the frozen spec, field by field.

Notes on two frozen-code facts (both verified 2026-10-01):
- pcbflow.v4exp.model.board_from_obj rejects family 'f12'
  (v4exp/model.py:299 checks FAMILIES = f1..f8 at model.py:31; f12 is the
  v4_2-owned family whose emitter constructs model.Board directly,
  v4_2/family.py:61).  Snapshots are therefore validated + materialized by
  constructing the v4exp Board dataclass from the snapshot object the same
  way board_from_obj does, without the f1..f8 registry gate; solve_board
  consumes the raw dict exactly as the frozen v4_2 tests do
  (tests/test_v4_2_m1.py:53 uses json.load dict -> incumbent_run).
- inspector.package_svg returns only the SVG; the manifest needed for
  source_manifest_sha256 is rebuilt through svg_route_package.build with a
  mirror of package_svg's route enrichment and asserted byte-equal to
  inspector.package_svg's output on every call (drift -> ValueError).
"""

import json
import os
import re

from pcbflow import svg_route_package as srp
from pcbflow.v4exp import model as v4exp_model
from pcbflow.v4_2.gt import incumbent_run
from pcbflow.v4_2.inspector import (_IDENTITY_RE, _JUDGE_SUFFIX,
                                    INSPECTOR_SYSTEM, assign_pids, blind,
                                    package_svg)

# ------------------------------------------------------------- frozen texts
# PREREG-REP-R1.md §12.1 (system, frozen verbatim)
PACK_SYSTEM = (
    "You are a PCB routing inspector reading a structured intent pack of a "
    "routed two-layer board (schema pcbflow-intentpack-v1). Machine facts "
    "live ONLY in the pack's structured sections (occupancy grids, netlist "
    "adjacency, constraints); there is no visual encoding to interpret. You "
    "can only ADD flags: you never modify geometry, never execute changes, "
    "never drop existing flags. For every route (segment) in the pack output "
    "exactly one entry. Use abstain when the facts are insufficient for a "
    "judgment. Respond with JSON only."
)

# PREREG §12.2 header declaration lines 2-3 (frozen verbatim; line 1 carries
# the pid).  Fixed-text byte count incl. line 1 with a 3-char pid: 1003.
_HEADER_LINE2 = (
    "Structured intent pack for PCB route inspection (machine facts only, no "
    "visual encoding). Sections in order: [grid]/[legend]/[occupy:<layer>] "
    "(occupancy grids), [pads]/[netlist]/[segment-index]/[vias] (netlist "
    "adjacency), [rules]/[workspace]/[keepouts] (constraints), [task] "
    "(instructions + output schema)."
)
_HEADER_LINE3 = (
    "How to read occupancy grids: each [occupy:<layer>] block is a "
    "run-length-encoded cell grid over the routing workspace for that copper "
    'layer. Row "iy:<runs>" is grid row iy; runs decode left-to-right: '
    '"<char><count>" means char repeats count times (count omitted = 1). '
    "Cell (ix,iy) spans [origin_x+ix*cell, origin_x+(ix+1)*cell) x "
    "[origin_y+iy*cell, origin_y+(iy+1)*cell) in mm, origin and cell size "
    "are declared in [grid]. Legend: '.'=free cell, '#'=keepout, 'P'=pad "
    "footprint, '*'=via, any other char=that segment's code (see "
    "[segment-index]). Occupancy marks segment-centerline cells; copper "
    "width is a scalar in [rules] and is NOT inflated into the grid."
)

# PACK-SPEC §4.3 (legend line, frozen)
_LEGEND_LINE = (
    "[legend] .=free #=keepout P=pad *=via letter=segment code (see "
    "[segment-index]); occupancy marks segment-centerline cells, copper "
    "width NOT inflated"
)

# PREREG §12.2 [task] block (frozen verbatim; 1134 bytes incl. trailing \n)
_TASK_LINES = (
    "[task]",
    'Judge every route (every entry of [segment-index]). Output shape: a '
    'JSON OBJECT with exactly one key "flags" whose value is an array with '
    'EXACTLY ONE entry per route in the pack (no duplicates, none missing). '
    'Each entry: {"route_id", "verdict", "reason_code", "evidence"}.',
    "- verdict must be exactly one of: flag_bad, no_flag, abstain.",
    "- reason_code must be EXACTLY one of these strings and nothing else: "
    "detour_excess, congestion_crossing, blocks_escape, clearance_risk, "
    "suboptimal_layer, uncertain.",
    "- evidence must cite the specific structured fact you used (occupancy "
    "cell, pad position, keepout rect, via placement, netlist adjacency).",
    "- An empty flags array means no_flag for every route (that is a valid "
    "answer; do not force flags).",
    "Coordinate frame: all coordinates in this pack are board-frame "
    "millimetres, y grows downward (declared in [grid]); grid cells are "
    "indexed (ix,iy) with the origin given in [grid]. IMPORTANT: routing is "
    "LEGAL up to 2.0 mm beyond the board outline on all four sides (routing "
    "workspace margin, see [workspace]); geometry outside the board edge "
    "but within that band is NOT a defect.",
    "JSON only.",
)

_END_LINE = "=== END PCBFLOW-INTENTPACK-V1 ==="

# PACK-SPEC §4.4 rev-r1: 23 distinct capitals, no I/O/P (no digits in codes,
# so no "f<digit>" pattern can ever appear in an RLE run string).
SEGMENT_CODES = "ABCDEFGHJKLMNQRSTUVWXYZ"
assert len(SEGMENT_CODES) == 23 and len(set(SEGMENT_CODES)) == 23
assert not (set("IOP") & set(SEGMENT_CODES))

MAX_SEGMENTS = 23                # PACK-SPEC §4.4 / §6.7
USER_BYTE_LIMIT = 48000          # PACK-SPEC §6.6 hard ceiling
USER_BYTE_TARGET = 36000         # target (not a gate)

# PREREG §11.2 forbidden strings (literal substring search over user+system)
FORBIDDEN_TOKENS = ("<svg", "<path", 'd="M', "data-pcbflow-schema",
                    "viewBox", "data-route-id", "data-object-kind")

# PACK-SPEC §5 frozen byte table (validator gate §7.14; sid -> user bytes)
FROZEN_USER_BYTES = {
    "cal-f12-01": 9431, "cal-f12-02": 9393, "cal-f12-03": 9385,
    "cal-f12-04": 9391, "cal-f12-05": 8896, "cal-f12-06": 8982,
    "cal-f12-07": 8857, "cal-f12-08": 8708, "hol-f6-01": 8155,
    "hol-f6-02": 7622, "hol-f6-03": 7988, "hol-f6-04": 7542,
    "hol-f8-01": 11044, "hol-f8-02": 10624, "hol-f8-03": 10763,
    "hol-f8-04": 10465,
}

ALL_SIDS = (["cal-f12-%02d" % i for i in range(1, 9)]
            + ["hol-f6-%02d" % i for i in (1, 2, 3, 4)]
            + ["hol-f8-%02d" % i for i in (1, 2, 3, 4)])

_VERIFY_SCHEMA = "pcbflow.v4_2_rep.packgen-verify/1"
_ID_SHAPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*$")  # §4.15
_TOL = 1e-9                       # closed-interval containment tolerance §4.5


# ------------------------------------------------------------ path helpers

def repo_root_from_here():
    """.../tools/pcbflow (this file lives in <root>/pcbflow/v4_2_rep/)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        os.pardir, os.pardir))


def scenario_sid_paths(repo_root):
    """sid -> read-only snapshot path (cal-* seat dir, hol-* cmp dir)."""
    seat = os.path.join(repo_root, "out", "v4.2-seat", "m1", "scenarios")
    cmpd = os.path.join(repo_root, "out", "v4-comparative-experiment")
    out = {}
    for sid in ALL_SIDS:
        name = "board-snapshot-%s.json" % sid
        path = (os.path.join(seat, name) if sid.startswith("cal-")
                else os.path.join(cmpd, name))
        if not os.path.isfile(path):
            raise ValueError("missing board snapshot: %s" % path)
        out[sid] = path
    return out


def pid_assignment():
    """Deterministic sid->pid via inspector.assign_pids (spec §1/§6.2)."""
    return assign_pids(ALL_SIDS)


def verify_pid_sid(pid):
    """pid -> sid (deterministic inverse of pid_assignment)."""
    for sid, p in pid_assignment().items():
        if p == pid:
            return sid
    raise ValueError("unknown pid %r" % pid)


def arm_a_tasks(repo_root):
    """r1 frozen blinded tasks (tasks-calibration.json, read-only)."""
    path = os.path.join(repo_root, "out", "v4.2-seat", "m1", "packages",
                        "tasks-calibration.json")
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    tasks = obj["tasks"] if isinstance(obj, dict) else obj
    return {t["pid"]: t for t in tasks}


# ------------------------------------------------------------- board loading

def load_board_snapshot(path):
    """Load + validate a board snapshot; returns the raw dict.

    Materializes the v4exp Board dataclass the way board_from_obj does
    (field-for-field) so a malformed snapshot fails loudly here; the f1..f8
    FAMILIES registry gate is not applied because f12 is a v4_2-owned family
    outside that registry (see module docstring).
    """
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    m = v4exp_model
    rules = m.Rules(grid_mm=obj["rules"]["grid_mm"],
                    clearance_mm=obj["rules"]["clearance_mm"],
                    width_mm=dict(obj["rules"]["width_mm"]),
                    via=m.ViaRules(pad_mm=obj["rules"]["via"]["pad_mm"],
                                   hole_mm=obj["rules"]["via"]["hole_mm"]),
                    allowed_layers={k: list(v) for k, v
                                    in obj["rules"]["allowed_layers"].items()})
    m.Board(scenario_id=obj["scenario_id"], split=obj["split"],
            family=obj["family"], seed=obj["seed"],
            bbox_mm=list(obj["board"]["bbox_mm"]),
            layers=list(obj["board"]["layers"]), rules=rules,
            pads=[m.Pad(**p) for p in obj["pads"]],
            nets=[m.Net(n["net_id"], n["net_class"], list(n["endpoints"]))
                  for n in obj["nets"]],
            keepouts=[m.Keepout(k["keepout_id"], list(k["rect_mm"]),
                                list(k["layers"]))
                      for k in obj["keepouts"]],
            relations=[m.Relation(r["relation_id"], r["relation_type"],
                                  list(r["members"]), r.get("parent_id"))
                       for r in obj["relations"]],
            label=obj["label"])
    return obj


# ------------------------------------------------------------- grid geometry

def _dec(v):
    """Decimal original text for [rules]/width values (§4.14)."""
    if isinstance(v, bool):
        raise ValueError("bool is not a rules value")
    if isinstance(v, int):
        return str(v)
    return repr(float(v))


def _cell_index(v, origin, cell):
    """mm -> cell index, exactness-checked (§4.8: round((v-origin)/cell))."""
    q = (float(v) - origin) / cell
    i = int(round(q))
    if abs(q - i) > 1e-6:
        raise ValueError("off-grid coordinate %r (origin=%r cell=%r)"
                         % (v, origin, cell))
    return i


def _anchor_span(lo, hi, origin, cell, n_max):
    """ix values whose anchor origin+ix*cell lies in [lo, hi] (closed,
    tolerance 1e-9; §4.5 rules 3-4)."""
    out = []
    ix = 0
    while origin + ix * cell < lo - _TOL:
        ix += 1
    while origin + ix * cell <= hi + _TOL and ix < n_max:
        out.append(ix)
        ix += 1
    return out


def _polyline_cells(polyline_mm, origin_x, origin_y, cell):
    """Walk an orthogonal on-grid polyline cell-by-cell (both endpoints
    included; consecutive duplicate points removed).  A zero-length stub
    (single point after dedup) yields exactly its one cell (§4.5 rule 1)."""
    pts = [(_cell_index(p[0], origin_x, cell),
            _cell_index(p[1], origin_y, cell)) for p in polyline_mm]
    if not pts:
        raise ValueError("empty polyline")
    ded = [pts[0]]
    for p in pts[1:]:
        if p != ded[-1]:
            ded.append(p)
    cells = []
    if len(ded) == 1:
        return [ded[0]]
    for (x0, y0), (x1, y1) in zip(ded, ded[1:]):
        if x0 != x1 and y0 != y1:
            raise ValueError("non-orthogonal polyline segment %r->%r"
                             % ((x0, y0), (x1, y1)))
        if x0 == x1:
            step = 1 if y1 >= y0 else -1
            walk = [(x0, y) for y in range(y0, y1 + step, step)]
        else:
            step = 1 if x1 >= x0 else -1
            walk = [(x, y0) for x in range(x0, x1 + step, step)]
        if not cells:
            cells.extend(walk)
        else:
            cells.extend(walk[1:])          # shared corner between legs
    return cells


def assign_segment_codes(route_ids):
    """sorted(route_id) -> codes from SEGMENT_CODES (§4.4); >23 = stop."""
    rts = sorted(str(r) for r in route_ids)
    if len(rts) > MAX_SEGMENTS:
        raise ValueError("segment count %d > %d (PACK-SPEC §4.4)"
                         % (len(rts), MAX_SEGMENTS))
    return {rid: SEGMENT_CODES[i] for i, rid in enumerate(rts)}


# ---------------------------------------------------------------- RLE codec

def rle_encode(row):
    """'<char><count>' runs, count written only when >= 2 (§4.4)."""
    out = []
    prev = row[0]
    n = 1
    for c in row[1:]:
        if c == prev:
            n += 1
        else:
            out.append(prev + (str(n) if n >= 2 else ""))
            prev = c
            n = 1
    out.append(prev + (str(n) if n >= 2 else ""))
    return "".join(out)


def rle_decode(runs):
    """Decode per §4.4: after a marker char / segment code take the longest
    consecutive digit string as count (absent = 1)."""
    out = []
    i = 0
    while i < len(runs):
        c = runs[i]
        j = i + 1
        while j < len(runs) and runs[j].isdigit():
            j += 1
        count = int(runs[i + 1:j] or "1")
        out.extend(c * count)
        i = j
    return "".join(out)


# ------------------------------------------------------- user text builder

def build_user_text(board, run, pid):
    """Serialize one B-arm user text (PACK-SPEC §2-§4, field by field).

    Raises ValueError on any frozen-gate violation: >23 segments, off-grid
    / non-orthogonal geometry, forbidden token, blinding leak, byte budget
    or frozen byte-table drift (§5/§7.14).
    """
    if run.get("status") != "sat":
        raise ValueError("incumbent not sat: %r" % run.get("status"))
    bbox = [float(v) for v in board["board"]["bbox_mm"]]
    layers = [str(s) for s in board["board"]["layers"]]
    rules = board["rules"]
    cell = float(rules["grid_mm"])
    origin_x = round(bbox[0] - 2.0, 10)
    origin_y = round(bbox[1] - 2.0, 10)
    nx = int(round((bbox[2] - bbox[0] + 4.0) / cell))
    ny = int(round((bbox[3] - bbox[1] + 4.0) / cell))

    route_ids = sorted(str(r["route_id"]) for r in run["routes"])
    code_of = assign_segment_codes(route_ids)
    rt_by = {str(r["route_id"]): r for r in run["routes"]}

    # ---- section 1: occupancy grids (§4.4/§4.5) -------------------------
    grid = {L: [["."] * nx for _ in range(ny)] for L in layers}
    seg_collisions = []
    for rid in route_ids:                      # rule 1: sorted order,
        r = rt_by[rid]                         # later segment overwrites
        L = str(r["layer"])
        if L not in grid:
            raise ValueError("route %s on unknown layer %r" % (rid, L))
        for (x, y) in _polyline_cells(r["polyline_mm"], origin_x, origin_y,
                                      cell):
            cur = grid[L][y][x]
            if cur not in (".", code_of[rid]):
                seg_collisions.append((L, x, y, cur, code_of[rid]))
            grid[L][y][x] = code_of[rid]
    for v in sorted(run["vias"], key=lambda v: str(v["via_id"])):  # rule 2
        x = _cell_index(v["center_mm"][0], origin_x, cell)
        y = _cell_index(v["center_mm"][1], origin_y, cell)
        for L in (str(v["from_layer"]), str(v["to_layer"])):
            if L in grid and grid[L][y][x] == ".":
                grid[L][y][x] = "*"
    for k in sorted(board["keepouts"],
                    key=lambda k: str(k["keepout_id"])):          # rule 3
        r = [float(v) for v in k["rect_mm"]]
        for L in (str(s) for s in k["layers"]):
            if L not in grid:
                continue
            for ix in _anchor_span(r[0], r[2], origin_x, cell, nx):
                for iy in _anchor_span(r[1], r[3], origin_y, cell, ny):
                    if grid[L][iy][ix] == ".":
                        grid[L][iy][ix] = "#"
    for p in sorted(board["pads"],
                    key=lambda p: str(p["pad_id"])):              # rule 4
        L = str(p["layer"])
        if L not in grid:
            continue
        for ix in _anchor_span(float(p["x_mm"]) - float(p["w_mm"]) / 2.0,
                               float(p["x_mm"]) + float(p["w_mm"]) / 2.0,
                               origin_x, cell, nx):
            for iy in _anchor_span(float(p["y_mm"]) - float(p["h_mm"]) / 2.0,
                                   float(p["y_mm"]) + float(p["h_mm"]) / 2.0,
                                   origin_y, cell, ny):
                if grid[L][iy][ix] == ".":
                    grid[L][iy][ix] = "P"

    lines = []
    lines.append("=== PCBFLOW-INTENTPACK-V1 pid=%s ===" % pid)   # §4.1
    lines.append(_HEADER_LINE2)
    lines.append(_HEADER_LINE3)
    lines.append("[grid] frame=board-mm y_axis=down-positive cell=%.2fmm "
                 "origin=(%.2f,%.2f) nx=%d ny=%d"
                 % (cell, origin_x, origin_y, nx, ny))            # §4.2
    lines.append(_LEGEND_LINE)                                    # §4.3
    for L in layers:                                              # §4.4
        lines.append("[occupy:%s]" % L)
        for iy in range(ny):
            lines.append("%d:%s" % (iy, rle_encode(grid[L][iy])))

    # ---- section 2: netlist adjacency (§4.6-§4.9) ------------------------
    lines.append("[pads]")
    for p in sorted(board["pads"], key=lambda p: str(p["pad_id"])):
        lines.append("%s net=%s layer=%s center=(%.2f,%.2f) size=%.1fx%.1fmm"
                     % (p["pad_id"], p["net_id"], p["layer"],
                        float(p["x_mm"]), float(p["y_mm"]),
                        float(p["w_mm"]), float(p["h_mm"])))
    segs_of = {}
    for r in run["routes"]:
        segs_of.setdefault(str(r["net_id"]), []).append(str(r["route_id"]))
    lines.append("[netlist]")
    for n in sorted(board["nets"], key=lambda n: str(n["net_id"])):
        nid = str(n["net_id"])
        lines.append("net %s class=%s pads=%s segments=%s"
                     % (nid, n["net_class"],
                        ",".join(str(p) for p in n["endpoints"]),
                        "+".join(sorted(segs_of.get(nid, [])))))
    lines.append("[segment-index]")
    for rid in route_ids:
        r = rt_by[rid]
        p0 = r["polyline_mm"][0]
        p1 = r["polyline_mm"][-1]
        lines.append("%s route_id=%s net=%s layer=%s width_mm=%s "
                     "endpoint_cells=(%d,%d)->(%d,%d)"
                     % (code_of[rid], rid, r["net_id"], r["layer"],
                        _dec(r["width_mm"]),
                        _cell_index(p0[0], origin_x, cell),
                        _cell_index(p0[1], origin_y, cell),
                        _cell_index(p1[0], origin_x, cell),
                        _cell_index(p1[1], origin_y, cell)))
    lines.append("[vias]")
    vias = sorted(run["vias"], key=lambda v: str(v["via_id"]))
    if not vias:
        lines.append("(none)")
    for v in vias:
        lines.append("%s parent=%s net=%s at_cell=(%d,%d) layers=%s->%s"
                     % (v["via_id"], v["parent_id"], v["net_id"],
                        _cell_index(v["center_mm"][0], origin_x, cell),
                        _cell_index(v["center_mm"][1], origin_y, cell),
                        v["from_layer"], v["to_layer"]))

    # ---- section 3: constraints (§4.10-§4.12) ----------------------------
    vr = rules["via"]
    annular = round((float(vr["pad_mm"]) - float(vr["hole_mm"])) / 2.0, 3)
    lines.append("[rules] clearance_mm=%s width_mm_default=%s "
                 "width_mm_clock=%s via_pad_mm=%s via_hole_mm=%s "
                 "via_annular_ring_mm=%s grid_mm=%s allowed_layers_default=%s "
                 "allowed_layers_clock=%s"
                 % (_dec(rules["clearance_mm"]),
                    _dec(rules["width_mm"]["default"]),
                    _dec(rules["width_mm"]["clock"]),
                    _dec(vr["pad_mm"]), _dec(vr["hole_mm"]), _dec(annular),
                    _dec(rules["grid_mm"]),
                    "+".join(str(s) for s in rules["allowed_layers"]["default"]),
                    "+".join(str(s) for s in rules["allowed_layers"]["clock"])))
    lines.append("[workspace] board_bbox_mm=[%.2f,%.2f,%.2f,%.2f] "
                 "routing_workspace_mm=[%.2f,%.2f,%.2f,%.2f] "
                 "workspace_margin_mm=2.0 (routing is LEGAL in the 2.0mm band "
                 "beyond the board outline on all four sides)"
                 % (bbox[0], bbox[1], bbox[2], bbox[3],
                    origin_x, origin_y,
                    round(bbox[2] + 2.0, 10), round(bbox[3] + 2.0, 10)))
    lines.append("[keepouts]")
    if not board["keepouts"]:
        lines.append("(none)")
    for k in sorted(board["keepouts"], key=lambda k: str(k["keepout_id"])):
        r = [float(v) for v in k["rect_mm"]]
        lines.append("%s layers=%s rect_mm=[%.2f,%.2f,%.2f,%.2f]"
                     % (k["keepout_id"],
                        "+".join(str(s) for s in k["layers"]),
                        r[0], r[1], r[2], r[3]))

    # ---- section 4: task block + tail (§4.13, PREREG §12.2) -------------
    lines.extend(_TASK_LINES)
    lines.append(_END_LINE)
    text = "\n".join(lines) + "\n"

    # ---- frozen gates (PACK-SPEC §6.5-§6.7, §7.14) ----------------------
    user_bytes = len(text.encode("utf-8"))
    if user_bytes > USER_BYTE_LIMIT:
        raise ValueError("user %d bytes > %d (PACK-SPEC §6.6)"
                         % (user_bytes, USER_BYTE_LIMIT))
    frozen = FROZEN_USER_BYTES.get(str(board["scenario_id"]))
    if frozen is not None and user_bytes != frozen:
        raise ValueError("user %d bytes != frozen table %d for %s "
                         "(PACK-SPEC §5/§7.14)"
                         % (user_bytes, frozen, board["scenario_id"]))
    for tok in FORBIDDEN_TOKENS:
        if tok in text or tok in PACK_SYSTEM:
            raise ValueError("forbidden token %r present (PREREG §11.2)" % tok)
    if _IDENTITY_RE.search(text) or _IDENTITY_RE.search(PACK_SYSTEM):
        raise ValueError("blinding leak in generated text (§6.5)")
    for secret in (str(board["scenario_id"]), str(board["family"]),
                   str(board["seed"]), str(board["split"]),
                   str(board["label"])):
        if secret and (secret in text or secret in PACK_SYSTEM):
            raise ValueError("identity field %r leaked (§6.5)" % secret)
    return text


# --------------------------------------------------------- anchors (§6.3/§4)

def _enriched_routes(board, run):
    """Mirror of inspector.package_svg's solver->v2 enrichment (needed to
    rebuild the manifest through srp.build; asserted byte-equal against
    inspector.package_svg on every call -- see build_pack)."""
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
            poly = [poly[0], poly[0]]      # zero-length stub stays visible
        routes.append(dict(r, polyline_mm=poly,
                           relation_ids=rel_of.get(str(r["net_id"]), []),
                           line_type=("clock"
                                      if classes.get(str(r["net_id"])) == "clock"
                                      else "signal"),
                           constraint_refs=[]))
    return routes


def build_pack(board, run, pid):
    """One B pack dict (§1 top-level keys) + rebuilt A-arm SVG bytes."""
    svg_frozen = package_svg(board, run)
    svg2, manifest = srp.build(board, {"routes": _enriched_routes(board, run),
                                       "vias": run["vias"]})
    if svg2 != svg_frozen:
        raise ValueError("manifest rebuild drifted from "
                         "inspector.package_svg output")
    return {
        "pid": pid,
        "system": PACK_SYSTEM,
        "user": build_user_text(board, run, pid),
        "source_manifest_sha256": manifest["manifest_payload_sha256"],
        "source_board_sha256": srp._sha256_of(board),
    }, svg_frozen, manifest


# ------------------------------------------------------------- text parsing

_OCCUPY_TAG_RE = re.compile(r"^\[occupy:([^\]]+)\]$")
_PAD_RE = re.compile(
    r"^(?P<pad_id>\S+) net=(?P<net>\S+) layer=(?P<layer>\S+) "
    r"center=\((?P<x>-?\d+\.\d\d),(?P<y>-?\d+\.\d\d)\) "
    r"size=(?P<w>\d+\.\d)x(?P<h>\d+\.\d)mm$")
_NET_RE = re.compile(
    r"^net (?P<net_id>\S+) class=(?P<cls>\S+) pads=(?P<pads>\S*) "
    r"segments=(?P<segs>\S*)$")
_SEG_RE = re.compile(
    r"^(?P<code>[A-Z]) route_id=(?P<rid>\S+) net=(?P<net>\S+) "
    r"layer=(?P<layer>\S+) width_mm=(?P<w>\S+) "
    r"endpoint_cells=\((?P<x0>-?\d+),(?P<y0>-?\d+)\)"
    r"->\((?P<x1>-?\d+),(?P<y1>-?\d+)\)$")
_VIA_RE = re.compile(
    r"^(?P<via_id>\S+) parent=(?P<parent>\S+) net=(?P<net>\S+) "
    r"at_cell=\((?P<x>-?\d+),(?P<y>-?\d+)\) "
    r"layers=(?P<lf>\S+)->(?P<lt>\S+)$")
_KEEPOUT_RE = re.compile(
    r"^(?P<kid>\S+) layers=(?P<layers>\S+) "
    r"rect_mm=\[(?P<x0>-?\d+\.\d\d),(?P<y0>-?\d+\.\d\d),"
    r"(?P<x1>-?\d+\.\d\d),(?P<y1>-?\d+\.\d\d)\]$")
_GRID_RE = re.compile(
    r"^\[grid\] frame=board-mm y_axis=down-positive cell=(?P<cell>\d+\.\d\d)mm "
    r"origin=\((?P<ox>-?\d+\.\d\d),(?P<oy>-?\d+\.\d\d)\) "
    r"nx=(?P<nx>\d+) ny=(?P<ny>\d+)$")
_RULES_RE = re.compile(
    r"^\[rules\] clearance_mm=(?P<c>\S+) width_mm_default=(?P<wd>\S+) "
    r"width_mm_clock=(?P<wc>\S+) via_pad_mm=(?P<vp>\S+) "
    r"via_hole_mm=(?P<vh>\S+) via_annular_ring_mm=(?P<va>\S+) "
    r"grid_mm=(?P<g>\S+) allowed_layers_default=(?P<ld>\S+) "
    r"allowed_layers_clock=(?P<lc>\S+)$")
_WS_RE = re.compile(
    r"^\[workspace\] board_bbox_mm=\[(?P<b>[^\]]+)\] "
    r"routing_workspace_mm=\[(?P<w>[^\]]+)\] workspace_margin_mm=2\.0 "
    r"\(routing is LEGAL in the 2\.0mm band beyond the board outline "
    r"on all four sides\)$")


def parse_user_text(text):
    """Parse + whitelist-validate a B user text (PACK-SPEC §2, §7.2).

    Returns a facts dict: pid, grid params, occupancy rows (decoded chars),
    pads, nets, segments, vias, rules, workspace, keepouts.  Raises
    ValueError on any out-of-whitelist line, section order violation, RLE
    length mismatch, or fixed-text drift.
    """
    if not text.endswith("\n"):
        raise ValueError("user text must end with newline")
    lines = text.split("\n")
    if lines[-1] != "":
        raise ValueError("bad terminator")
    lines = lines[:-1]
    if not lines or lines[-1] != _END_LINE:
        raise ValueError("missing END line")
    body = lines[:-1]
    m = re.match(r"^=== PCBFLOW-INTENTPACK-V1 pid=(p\d\d) ===$", body[0])
    if not m:
        raise ValueError("bad header line 1: %r" % body[0])
    facts = {"pid": m.group(1)}
    if body[1] != _HEADER_LINE2 or body[2] != _HEADER_LINE3:
        raise ValueError("header declaration drift")
    i = 3

    def expect(prefix, kind="tag"):
        if i >= len(body) or not body[i].startswith(prefix):
            raise ValueError("expected %s at line %d: %r" % (kind, i, body[i]))

    # [grid] + [legend] (fixed)
    expect("[grid] ")
    gm = _GRID_RE.match(body[i])
    if not gm:
        raise ValueError("bad [grid] line: %r" % body[i])
    facts["grid"] = {"cell": float(gm.group("cell")),
                     "origin_x": float(gm.group("ox")),
                     "origin_y": float(gm.group("oy")),
                     "nx": int(gm.group("nx")), "ny": int(gm.group("ny"))}
    i += 1
    if body[i] != _LEGEND_LINE:
        raise ValueError("legend line drift: %r" % body[i])
    i += 1

    # occupancy blocks (one per layer, board order)
    facts["layers"] = []
    facts["occupy"] = {}
    while i < len(body) and body[i].startswith("[occupy:"):
        om = _OCCUPY_TAG_RE.match(body[i])
        if not om:
            raise ValueError("bad occupy tag: %r" % body[i])
        layer = om.group(1)
        i += 1
        rows = []
        for iy in range(facts["grid"]["ny"]):
            row = body[i]
            i += 1
            head, _, runs = row.partition(":")
            if head != str(iy):
                raise ValueError("row index drift %r != %d" % (head, iy))
            decoded = rle_decode(runs)
            if len(decoded) != facts["grid"]["nx"]:
                raise ValueError("row %d decodes to %d != nx %d"
                                 % (iy, len(decoded), facts["grid"]["nx"]))
            legal = set(".#P*" + SEGMENT_CODES)
            if set(decoded) - legal:
                raise ValueError("illegal char in row %d" % iy)
            if rle_encode(decoded) != runs:
                raise ValueError("row %d RLE round-trip mismatch" % iy)
            rows.append(decoded)
        facts["layers"].append(layer)
        facts["occupy"][layer] = rows

    # [pads]
    expect("[pads]")
    i += 1
    facts["pads"] = []
    while i < len(body) and not body[i].startswith("["):
        if body[i] == "(none)":
            i += 1
            break
        pm = _PAD_RE.match(body[i])
        if not pm:
            raise ValueError("bad pad row: %r" % body[i])
        facts["pads"].append({k: pm.group(k) for k in
                              ("pad_id", "net", "layer", "x", "y", "w", "h")})
        i += 1

    # [netlist]
    expect("[netlist]")
    i += 1
    facts["nets"] = []
    while i < len(body) and not body[i].startswith("["):
        if body[i] == "(none)":
            i += 1
            break
        nm = _NET_RE.match(body[i])
        if not nm:
            raise ValueError("bad net row: %r" % body[i])
        facts["nets"].append({k: (nm.group(k).split(",") if k == "pads" else
                                  nm.group(k).split("+") if k == "segs" else
                                  nm.group(k))
                              for k in ("net_id", "cls", "pads", "segs")})
        i += 1

    # [segment-index]
    expect("[segment-index]")
    i += 1
    facts["segments"] = []
    while i < len(body) and not body[i].startswith("["):
        if body[i] == "(none)":
            i += 1
            break
        sm = _SEG_RE.match(body[i])
        if not sm:
            raise ValueError("bad segment row: %r" % body[i])
        if sm.group("code") not in SEGMENT_CODES:
            raise ValueError("bad segment code %r" % sm.group("code"))
        facts["segments"].append({k: sm.group(k) for k in
                                  ("code", "rid", "net", "layer", "w",
                                   "x0", "y0", "x1", "y1")})
        i += 1

    # [vias]
    expect("[vias]")
    i += 1
    facts["vias"] = []
    while i < len(body) and not body[i].startswith("["):
        if body[i] == "(none)":
            i += 1
            break
        vm = _VIA_RE.match(body[i])
        if not vm:
            raise ValueError("bad via row: %r" % body[i])
        facts["vias"].append({k: vm.group(k) for k in
                              ("via_id", "parent", "net", "x", "y", "lf", "lt")})
        i += 1

    # [rules] + [workspace] + [keepouts]
    expect("[rules] ")
    rm = _RULES_RE.match(body[i])
    if not rm:
        raise ValueError("bad [rules] line: %r" % body[i])
    facts["rules"] = {k: rm.group(k) for k in rm.groupdict()}
    i += 1
    expect("[workspace] ")
    wm = _WS_RE.match(body[i])
    if not wm:
        raise ValueError("bad [workspace] line: %r" % body[i])
    facts["workspace"] = {"board_bbox": wm.group("b"),
                          "routing_workspace": wm.group("w")}
    i += 1
    expect("[keepouts]")
    i += 1
    facts["keepouts"] = []
    while i < len(body) and not body[i].startswith("["):
        if body[i] == "(none)":
            i += 1
            break
        km = _KEEPOUT_RE.match(body[i])
        if not km:
            raise ValueError("bad keepout row: %r" % body[i])
        facts["keepouts"].append({k: km.group(k) for k in
                                  ("kid", "layers", "x0", "y0", "x1", "y1")})
        i += 1

    # [task] block: exact frozen bytes
    if body[i:i + len(_TASK_LINES)] != list(_TASK_LINES):
        raise ValueError("[task] block drift at line %d" % i)
    i += len(_TASK_LINES)
    if i != len(body):
        raise ValueError("content outside whitelist after [task]: %r"
                         % body[i:])
    facts["n_segments"] = len(facts["segments"])
    facts["n_vias"] = len(facts["vias"])
    return facts


# ------------------------------------- from-facts occupancy replay (§7.7)

def replay_occupancy(facts):
    """Independently re-rasterize from the parsed text facts per §4.5 and
    compare cell-by-cell with the occupancy grids carried in the text.

    Segment polylines are read out of the grids themselves (PACK-SPEC §3:
    the connected cells of a segment code ARE the polyline); each code's
    cells must form a 4-connected orthogonal set containing both declared
    endpoint cells (a zero-length stub = exactly one cell).  Via/keepout/
    pad cells are replayed with the write-only-if-free priority semantics;
    any cell a segment would need to share with another segment code, or
    any disagreement with the text grid, raises ValueError.
    """
    g = facts["grid"]
    nx, ny = g["nx"], g["ny"]
    layers = facts["layers"]
    replay = {L: [["."] * nx for _ in range(ny)] for L in layers}

    # rule 1 -- segment cells (read from the text grid), code by code in
    # [segment-index] order (= sorted route_id order)
    text_cells = {}
    for L in layers:
        for iy, row in enumerate(facts["occupy"][L]):
            for ix, c in enumerate(row):
                if c not in ".#P*":
                    text_cells.setdefault((L, c), []).append((ix, iy))
    for seg in facts["segments"]:
        code = seg["code"]
        ep0 = (int(seg["x0"]), int(seg["y0"]))
        ep1 = (int(seg["x1"]), int(seg["y1"]))
        cells = text_cells.get((seg["layer"], code))
        if not cells:
            raise ValueError("segment %s has no occupancy cells"
                             % seg["rid"])
        if ep0 not in cells or ep1 not in cells:
            raise ValueError("segment %s endpoints not on its cells"
                             % seg["rid"])
        if len(cells) == 1:
            if ep0 != ep1:
                raise ValueError("single-cell segment %s must be a stub"
                                 % seg["rid"])
        cs = set(cells)
        # 4-connectivity walk between the two endpoints
        frontier = {ep0}
        reached = {ep0}
        while frontier and ep1 not in reached:
            nxt = set()
            for (x, y) in frontier:
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = (x + d[0], y + d[1])
                    if p in cs and p not in reached:
                        nxt.add(p)
            reached |= nxt
            frontier = nxt
        if ep1 not in reached:
            raise ValueError("segment %s cells not connected" % seg["rid"])
        for (x, y) in cells:
            cur = replay[seg["layer"]][y][x]
            if cur not in (".", code):
                raise ValueError("segment-segment cell collision at %s %r"
                                 % (seg["layer"], (x, y)))
            replay[seg["layer"]][y][x] = code

    # rule 2 -- vias (only free cells)
    for v in facts["vias"]:
        x, y = int(v["x"]), int(v["y"])
        for L in (v["lf"], v["lt"]):
            if L in replay and replay[L][y][x] == ".":
                replay[L][y][x] = "*"

    # rule 3 -- keepouts (anchor containment, only free cells)
    for k in facts["keepouts"]:
        for L in k["layers"].split("+"):
            if L not in replay:
                continue
            for ix in _anchor_span(float(k["x0"]), float(k["x1"]),
                                   g["origin_x"], g["cell"], nx):
                for iy in _anchor_span(float(k["y0"]), float(k["y1"]),
                                       g["origin_y"], g["cell"], ny):
                    if replay[L][iy][ix] == ".":
                        replay[L][iy][ix] = "#"

    # rule 4 -- pads (anchor containment, only free cells)
    for p in facts["pads"]:
        cx, cy = float(p["x"]), float(p["y"])
        for ix in _anchor_span(cx - float(p["w"]) / 2.0,
                               cx + float(p["w"]) / 2.0,
                               g["origin_x"], g["cell"], nx):
            for iy in _anchor_span(cy - float(p["h"]) / 2.0,
                                   cy + float(p["h"]) / 2.0,
                                   g["origin_y"], g["cell"], ny):
                if replay[p["layer"]][iy][ix] == ".":
                    replay[p["layer"]][iy][ix] = "P"

    for L in layers:
        for iy in range(ny):
            got = "".join(replay[L][iy])
            if got != facts["occupy"][L][iy]:
                raise ValueError("occupancy replay mismatch %s row %d"
                                 % (L, iy))
    return replay


def verify_pack_text(text):
    """All text-level checks for one B user text; returns facts or raises."""
    facts = parse_user_text(text)
    replay_occupancy(facts)                    # §7.7 cell-by-cell
    for tok in FORBIDDEN_TOKENS:               # §7.3
        if tok in text:
            raise ValueError("forbidden token %r" % tok)
    if _IDENTITY_RE.search(text):              # §7.4
        raise ValueError("identity regex hit")
    if len(text.encode("utf-8")) > USER_BYTE_LIMIT:      # §7.5
        raise ValueError("byte budget exceeded")
    if facts["n_segments"] > MAX_SEGMENTS:
        raise ValueError(">23 segments")
    for decl in ("y_axis=down-positive", "workspace_margin_mm=2.0",
                 "2.0 mm beyond the board outline"):
        if decl not in text:
            raise ValueError("missing declaration %r" % decl)
    return facts


# ------------------------------------------------------------- file writers

def _canonical_dump(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def generate_all(repo_root=None, out_root=None, double_run=True):
    """Generate 16 B packs + 16 A extractions + self-verify report.

    Deterministic double run (§7.8): every board is re-solved and the user
    text rebuilt; byte equality with the first pass is enforced.  Returns
    the verify report dict (also written to out_root/packgen-verify.json).
    """
    repo_root = repo_root or repo_root_from_here()
    out_root = out_root or os.path.join(repo_root, "out", "v4.2-rep-r1")
    sid_paths = scenario_sid_paths(repo_root)
    pids = pid_assignment()
    a_tasks = arm_a_tasks(repo_root)

    packs_dir = os.path.join(out_root, "packs-b")
    tasks_dir = os.path.join(out_root, "tasks-a")
    os.makedirs(packs_dir, exist_ok=True)
    os.makedirs(tasks_dir, exist_ok=True)

    meta_path = os.path.join(repo_root, "out", "v4.2-seat", "m1", "packages",
                             "package-meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta_pid_ok = (set(meta.keys()) == {"p%02d" % (i + 1) for i in range(16)}
                   and all(meta[p]["sid"] == s for s, p in pids.items()))

    # GT readiness, key sets only (§7.11 -- no judgment values are read)
    gt_path = os.path.join(repo_root, "out", "v4.2-seat", "m1", "gt.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_keys = set(json.load(f).get("scenarios", {}).keys())
    gt_ready = gt_keys == set(ALL_SIDS)

    per_pid = {}
    written = {}
    for sid in ALL_SIDS:
        board = load_board_snapshot(sid_paths[sid])
        run = incumbent_run(board)
        pid = pids[sid]
        pack, svg_frozen, manifest = build_pack(board, run, pid)
        verify_pack_text(pack["user"])

        # determinism double run (§7.8): fresh solve, rebuild, compare bytes
        if double_run:
            run2 = incumbent_run(board)
            pack2, _, _ = build_pack(board, run2, pid)
            if pack2["user"] != pack["user"]:
                raise ValueError("double-run drift for %s" % sid)
            if pack2["source_manifest_sha256"] != pack["source_manifest_sha256"]:
                raise ValueError("double-run manifest drift for %s" % sid)

        # ---- A-arm anchoring (§6.4): byte identity with r1 frozen text
        a_task = a_tasks[pid]
        a_user = a_task["user"]
        rebuilt_a = blind(svg_frozen, sid, pid) + "\n" + _JUDGE_SUFFIX
        a_user_eq = (rebuilt_a == a_user)
        a_sys_eq = (a_task["system"] == INSPECTOR_SYSTEM)
        m = re.search(r'data-route-manifest-sha256="([0-9a-f]+)"', a_user)
        a_manifest_eq = bool(m) and m.group(1) == manifest["manifest_payload_sha256"]
        b = re.search(r'data-board-snapshot-sha256="([0-9a-f]+)"', a_user)
        a_board_eq = bool(b) and b.group(1) == pack["source_board_sha256"]
        if not (a_user_eq and a_sys_eq and a_manifest_eq and a_board_eq):
            raise ValueError("A-arm anchoring failed for %s (%s)"
                             % (sid, pid))

        # ---- route-set equality with A SVG data-route-id set (hard gate 4)
        a_routes = set(re.findall(r'data-route-id="([^"]+)"', a_user))
        b_routes = {s["rid"] for s in parse_user_text(pack["user"])["segments"]}
        if a_routes != b_routes:
            raise ValueError("B route set != A data-route-id set for %s"
                             % pid)

        # ---- id set gates (§7.13) against source objects
        facts = parse_user_text(pack["user"])
        if ({s["rid"] for s in facts["segments"]}
                != {str(r["route_id"]) for r in run["routes"]}):
            raise ValueError("route_id set gate failed: %s" % pid)
        if ({p["pad_id"] for p in facts["pads"]}
                != {str(p["pad_id"]) for p in board["pads"]}):
            raise ValueError("pad_id set gate failed: %s" % pid)
        if ({n["net_id"] for n in facts["nets"]}
                != {str(n["net_id"]) for n in board["nets"]}):
            raise ValueError("net_id set gate failed: %s" % pid)
        if ({k["kid"] for k in facts["keepouts"]}
                != {str(k["keepout_id"]) for k in board["keepouts"]}):
            raise ValueError("keepout_id set gate failed: %s" % pid)
        if ({v["via_id"] for v in facts["vias"]}
                != {str(v["via_id"]) for v in run["vias"]}):
            raise ValueError("via_id set gate failed: %s" % pid)
        for ident in ([s["rid"] for s in facts["segments"]]
                      + [p["pad_id"] for p in facts["pads"]]
                      + [n["net_id"] for n in facts["nets"]]
                      + [k["kid"] for k in facts["keepouts"]]
                      + [v["via_id"] for v in facts["vias"]]):
            if not _ID_SHAPE_RE.match(ident):
                raise ValueError("id shape violation: %r" % ident)

        # ---- write artifacts
        pack_path = os.path.join(packs_dir, "%s.json" % pid)
        with open(pack_path, "wb") as f:
            f.write(_canonical_dump(pack))
        a_out = {"pid": pid, "system": a_task["system"], "user": a_user}
        a_path = os.path.join(tasks_dir, "%s.json" % pid)
        with open(a_path, "wb") as f:
            f.write(_canonical_dump(a_out))
        written[pid] = (pack_path, a_path)

        user_bytes = len(pack["user"].encode("utf-8"))
        frozen = FROZEN_USER_BYTES[sid]
        per_pid[pid] = {
            "sid": sid,
            "user_bytes": user_bytes,
            "user_bytes_frozen_table": frozen,
            "frozen_byte_table_match": user_bytes == frozen,
            "byte_budget": {"limit": USER_BYTE_LIMIT,
                            "target": USER_BYTE_TARGET,
                            "within_target": user_bytes <= USER_BYTE_TARGET},
            "n_segments": facts["n_segments"],
            "n_vias": facts["n_vias"],
            "ascii_only": pack["user"].isascii(),
            "forbidden_token_hits": {
                tok: (pack["user"].count(tok) + pack["system"].count(tok))
                for tok in FORBIDDEN_TOKENS},
            "blind_scan": {
                "identity_regex_user": len(_IDENTITY_RE.findall(pack["user"])),
                "identity_regex_system":
                    len(_IDENTITY_RE.findall(pack["system"])),
                "sid_absent": sid not in pack["user"] + pack["system"],
                "family_absent": str(board["family"])
                                 not in pack["user"] + pack["system"],
                "seed_absent": str(board["seed"])
                               not in pack["user"] + pack["system"],
                "split_absent": str(board["split"])
                                not in pack["user"] + pack["system"],
                "label_absent": str(board["label"])
                                not in pack["user"] + pack["system"],
                "declarations_present": all(
                    d in pack["user"] for d in
                    ("y_axis=down-positive", "workspace_margin_mm=2.0",
                     "2.0 mm beyond the board outline")),
            },
            "route_set_match_arm_a": {
                "n_routes_b": len(b_routes),
                "n_routes_a": len(a_routes),
                "equal": a_routes == b_routes,
            },
            "occupancy_replay_ok": True,
            "id_set_gates_ok": True,
            "determinism_double_run": bool(double_run),
            "anchors": {
                "source_manifest_sha256": pack["source_manifest_sha256"],
                "source_board_sha256": pack["source_board_sha256"],
                "arm_a_user_byte_equal": a_user_eq,
                "arm_a_system_equal": a_sys_eq,
                "arm_a_manifest_attr_equal": a_manifest_eq,
                "arm_a_board_attr_equal": a_board_eq,
            },
        }

    gates_ok = all(
        v["frozen_byte_table_match"]
        and v["user_bytes"] <= USER_BYTE_LIMIT
        and all(c == 0 for c in v["forbidden_token_hits"].values())
        and v["blind_scan"]["identity_regex_user"] == 0
        and v["blind_scan"]["identity_regex_system"] == 0
        and all(v["blind_scan"][k] for k in
                ("sid_absent", "family_absent", "seed_absent", "split_absent",
                 "label_absent", "declarations_present"))
        and v["route_set_match_arm_a"]["equal"]
        and v["n_segments"] <= MAX_SEGMENTS
        and v["occupancy_replay_ok"] and v["id_set_gates_ok"]
        and all(v["anchors"][k] for k in
                ("arm_a_user_byte_equal", "arm_a_system_equal",
                 "arm_a_manifest_attr_equal", "arm_a_board_attr_equal"))
        for v in per_pid.values())

    report = {
        "schema": _VERIFY_SCHEMA,
        "spec": "PACK-SPEC-REP-R1.md v1 (2026-09-30)",
        "generator": "pcbflow.v4_2_rep.packgen",
        "n_packs": len(per_pid),
        "pids": sorted(per_pid.keys()),
        "gates_all_passed": gates_ok,
        "determinism_double_run": bool(double_run),
        "meta_pid_map_matches_assign_pids": meta_pid_ok,
        "gt_readiness": {"exists": os.path.isfile(gt_path),
                         "n_scenario_keys": len(gt_keys),
                         "keys_match_sid_set": gt_ready},
        "per_pid": per_pid,
    }
    verify_path = os.path.join(out_root, "packgen-verify.json")
    with open(verify_path, "wb") as f:
        f.write(_canonical_dump(report))
    report["_written"] = written
    return report


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="REP-R1 B-arm intent pack generator (PACK-SPEC-REP-R1)")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--no-double-run", action="store_true")
    args = ap.parse_args(argv)
    report = generate_all(repo_root=args.repo_root, out_root=args.out_root,
                          double_run=not args.no_double_run)
    n = report["n_packs"]
    ok = report["gates_all_passed"]
    print("packgen: %d packs, gates_all_passed=%s" % (n, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
