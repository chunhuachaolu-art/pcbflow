"""pcbflow.v4exp.grid -- integer lattice world for the V4 experiment.

All geometric decisions in the v4 experiment happen on a 0.25 mm integer
lattice:

  * millimetre coordinates are converted to lattice indices once, at
    board load time; every comparison afterwards is integer-exact;
  * obstacle growth, via footprints and the frozen separation rule are
    expressed in cells; millimetre values reappear only when emitting
    polylines;
  * the work area is the board bbox grown by WORKSPACE_MARGIN_MM; cells
    outside it act as boundary walls (A* simply cannot leave the range).

Frozen hard clearance contract (write-down of the data contract):
two different nets are legal iff their centre-line lattice distance is
at least MIN_CENTER_SEPARATION_CELLS (Chebyshev metric -- the
conservative reading: Chebyshev >= 2 implies Manhattan >= 2 too).
"""

import json
import math

GRID_MM = 0.25
WORKSPACE_MARGIN_MM = 2.0

#: Frozen hard constraint: minimum centre-line distance between two
#: different nets, in lattice cells (0.5 mm at the 0.25 mm grid).
MIN_CENTER_SEPARATION_CELLS = 2
#: Cells blocked around an already-routed net's raw geometry.
DILATION_RADIUS_CELLS = MIN_CENTER_SEPARATION_CELLS - 1
#: A via occupies its centre cell plus the 8-neighbourhood, on both layers.
VIA_FOOTPRINT_RADIUS_CELLS = 1

BOARD_SCHEMA = "pcbflow.v4exp.board/1"


class V4ExpError(ValueError):
    """Raised for contract violations in inputs (bad schema, bad order, ...)."""


def canonical_json(obj):
    """Deterministic JSON text: sorted keys, tight separators, ASCII only."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def dilate(cells, radius=DILATION_RADIUS_CELLS):
    """Chebyshev dilation of a set of (ix, iy) cells."""
    out = set()
    for (x, y) in cells:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                out.add((x + dx, y + dy))
    return out


def separation_violation(cells_a, cells_b):
    """True iff the two raw geometries are closer than the frozen rule.

    min Chebyshev(a, b) < MIN_CENTER_SEPARATION_CELLS  <=>  dilate(a) & b != {}
    """
    if not cells_a or not cells_b:
        return False
    return len(dilate(cells_a, DILATION_RADIUS_CELLS) & set(cells_b)) > 0


class GridWorld:
    """Parsed board snapshot on the integer lattice."""

    def __init__(self, board, anchor_exemption=False):
        """anchor_exemption (V4-E4 contract, default False): when true,
        static_blocked_for_net(nid) subtracts each of nid's own pad
        rectangle cells (margin=0, pad body only, no growth) from the
        blocked set on that pad's layer -- the start/endpoint anchor
        area of the net being routed.  Default False keeps the
        pre-E4 behaviour byte-for-byte (own pads were already skipped
        as block sources; the exemption additionally undoes neighbour
        margin/keepout coverage over the pad body itself)."""
        if not isinstance(board, dict) or board.get("schema") != BOARD_SCHEMA:
            raise V4ExpError("board schema must be %s" % BOARD_SCHEMA)
        rules = board["rules"]
        if abs(float(rules["grid_mm"]) - GRID_MM) > 1e-12:
            raise V4ExpError("v4exp requires rules.grid_mm == 0.25")
        self.board = board
        self.scenario_id = str(board["scenario_id"])
        self.layers = [str(s) for s in board["board"]["layers"]]
        self.layer_index = {name: i for i, name in enumerate(self.layers)}
        x0, y0, x1, y1 = (float(v) for v in board["board"]["bbox_mm"])
        self.origin_x = x0 - WORKSPACE_MARGIN_MM
        self.origin_y = y0 - WORKSPACE_MARGIN_MM
        self.nx = int(round((x1 + WORKSPACE_MARGIN_MM - self.origin_x) / GRID_MM)) + 1
        self.ny = int(round((y1 + WORKSPACE_MARGIN_MM - self.origin_y) / GRID_MM)) + 1
        self.clearance_mm = float(rules["clearance_mm"])
        self.width_mm = {str(k): float(v) for k, v in rules["width_mm"].items()}
        self.allowed_by_class = {
            str(k): [str(s) for s in v]
            for k, v in rules.get("allowed_layers", {}).items()
        }
        via = rules.get("via", {})
        self.via_pad_mm = float(via.get("pad_mm", 0.6))
        self.via_hole_mm = float(via.get("hole_mm", 0.3))

        self.net_ids = []
        self.net_class = {}
        self.net_endpoints = {}
        for net in board["nets"]:
            nid = str(net["net_id"])
            eps = [str(p) for p in net["endpoints"]]
            if len(eps) != 2:
                raise V4ExpError("net %s must have exactly 2 endpoints" % nid)
            if nid in self.net_class:
                raise V4ExpError("duplicate net %s" % nid)
            self.net_ids.append(nid)
            self.net_class[nid] = str(net["net_class"])
            self.net_endpoints[nid] = eps

        self.pad_by_id = {}
        self.pad_ids_of_net = {nid: [] for nid in self.net_ids}
        for pad in board["pads"]:
            pid = str(pad["pad_id"])
            if pid in self.pad_by_id:
                raise V4ExpError("duplicate pad %s" % pid)
            self.pad_by_id[pid] = pad
            self.pad_ids_of_net.setdefault(str(pad["net_id"]), []).append(pid)
        for nid in self.net_ids:
            for pid in self.net_endpoints[nid]:
                if pid not in self.pad_by_id:
                    raise V4ExpError("net %s endpoint %s has no pad" % (nid, pid))
                if str(self.pad_by_id[pid]["net_id"]) != nid:
                    raise V4ExpError("pad %s does not belong to net %s" % (pid, nid))

        self.keepouts = []
        for ko in board.get("keepouts", []):
            rect = [float(v) for v in ko["rect_mm"]]
            names = [str(s) for s in ko.get("layers", self.layers)]
            lis = tuple(self.layer_index[n] for n in names if n in self.layer_index)
            self.keepouts.append((rect, lis))

        self.anchor_exemption = bool(anchor_exemption)

    # ---------- coordinate helpers ----------

    def cell_x(self, x_mm):
        return int(round((float(x_mm) - self.origin_x) / GRID_MM))

    def cell_y(self, y_mm):
        return int(round((float(y_mm) - self.origin_y) / GRID_MM))

    def center_mm_x(self, ix):
        return self.origin_x + ix * GRID_MM

    def center_mm_y(self, iy):
        return self.origin_y + iy * GRID_MM

    def in_bounds(self, ix, iy):
        return 0 <= ix < self.nx and 0 <= iy < self.ny

    def net_width(self, nid):
        cls = self.net_class[nid]
        return self.width_mm.get(cls, self.width_mm.get("default", 0.3))

    def net_allowed_layer_indices(self, nid):
        cls = self.net_class[nid]
        names = (self.allowed_by_class.get(cls)
                 or self.allowed_by_class.get("default")
                 or self.layers)
        return [self.layer_index[n] for n in names if n in self.layer_index]

    def pad_rect(self, pad):
        x, y = float(pad["x_mm"]), float(pad["y_mm"])
        hw, hh = float(pad["w_mm"]) / 2.0, float(pad["h_mm"]) / 2.0
        return [x - hw, y - hh, x + hw, y + hh]

    def cells_in_rect(self, rect, margin):
        """Cells whose centre lies inside rect grown by margin (closed set).

        Growing first and then testing centres conservatively implements
        "grow the rectangle, round up to the lattice": a cell centre lying
        exactly at the margin distance is blocked.
        """
        x0, y0, x1, y1 = rect
        x0 -= margin
        y0 -= margin
        x1 += margin
        y1 += margin
        ix0 = max(int(math.ceil((x0 - self.origin_x) / GRID_MM - 1e-9)), 0)
        ix1 = min(int(math.floor((x1 - self.origin_x) / GRID_MM + 1e-9)), self.nx - 1)
        iy0 = max(int(math.ceil((y0 - self.origin_y) / GRID_MM - 1e-9)), 0)
        iy1 = min(int(math.floor((y1 - self.origin_y) / GRID_MM + 1e-9)), self.ny - 1)
        out = set()
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                out.add((ix, iy))
        return out

    def static_blocked_for_net(self, nid):
        """Order-independent obstacles for one net, per layer index.

        Sources: other nets' pads (own endpoints are exempt) and keepouts,
        both grown by clearance + half of this net's trace width.

        V4-E4 contract -- anchor_exemption: when the world was built with
        anchor_exemption=True, the trailing step below subtracts, for every
        pad owned by nid (on that pad's layer), the pad rectangle body cells
        (cells_in_rect(pad_rect(pad), margin=0); no growth) from blocked.
        This frees nid's start/endpoint anchor cells from neighbour margin
        and keepout coverage so _astar is not dead on arrival at the start
        cell.  The exemption is per-net: nid's pads remain margin blockers
        for every other net's view (static_blocked_for_net(other_nid) is
        unchanged).  Escape corridors beyond the pad body are NOT
        guaranteed; failure there is reported as-is.  Default False keeps
        the pre-E4 behaviour byte-for-byte.
        """
        margin = self.clearance_mm + self.net_width(nid) / 2.0
        blocked = {li: set() for li in range(len(self.layers))}
        for pad in self.board["pads"]:
            if str(pad["net_id"]) == nid:
                continue
            li = self.layer_index[str(pad["layer"])]
            blocked[li] |= self.cells_in_rect(self.pad_rect(pad), margin)
        for rect, lis in self.keepouts:
            for li in lis:
                blocked[li] |= self.cells_in_rect(rect, margin)
        if self.anchor_exemption:
            for pid in self.pad_ids_of_net.get(nid, []):
                pad = self.pad_by_id[pid]
                li = self.layer_index[str(pad["layer"])]
                blocked[li] -= self.cells_in_rect(self.pad_rect(pad), 0)
        return blocked


class RoutedState:
    """Raw lattice geometry of already routed nets, with a dilated cache."""

    def __init__(self):
        self.cells = {}    # net_id -> {layer_idx: set((ix, iy))} raw geometry
        self.dilated = {}  # net_id -> {layer_idx: set} exclusion for others

    def add_net(self, net_id, cells_per_layer):
        self.cells[net_id] = {li: set(s) for li, s in cells_per_layer.items()}
        self.dilated[net_id] = {li: dilate(s) for li, s in cells_per_layer.items()}

    def blocked_from_others(self, net_id):
        """Union of the dilated geometry of every net except net_id."""
        out = {}
        for other, per in self.dilated.items():
            if other == net_id:
                continue
            for li, cells in per.items():
                out.setdefault(li, set()).update(cells)
        return out


def geometry_from_routes(world, routes, vias):
    """Rebuild per-net lattice geometry from emitted route/via dicts.

    This is the independent view used by the metric re-check: it parses
    only the emitted JSON structures, never solver-internal state.
    """
    per_net = {}
    for r in routes:
        nid = str(r["route_id"]).rsplit("-S", 1)[0]
        per = per_net.setdefault(nid, {li: set() for li in range(len(world.layers))})
        li = world.layer_index[str(r["layer"])]
        prev = None
        for p in r["polyline_mm"]:
            cx, cy = world.cell_x(p[0]), world.cell_y(p[1])
            per[li].add((cx, cy))
            if prev is not None:
                sx = (cx > prev[0]) - (cx < prev[0])
                sy = (cy > prev[1]) - (cy < prev[1])
                wx, wy = prev[0] + sx, prev[1] + sy
                while (wx, wy) != (cx, cy):
                    per[li].add((wx, wy))
                    wx += sx
                    wy += sy
            prev = (cx, cy)
    for v in vias:
        nid = str(v["via_id"]).rsplit("-V", 1)[0]
        per = per_net.setdefault(nid, {li: set() for li in range(len(world.layers))})
        cx = world.cell_x(v["center_mm"][0])
        cy = world.cell_y(v["center_mm"][1])
        lf = world.layer_index[str(v["from_layer"])]
        lt = world.layer_index[str(v["to_layer"])]
        r = VIA_FOOTPRINT_RADIUS_CELLS
        for li in (lf, lt):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    per[li].add((cx + dx, cy + dy))
    return per_net
