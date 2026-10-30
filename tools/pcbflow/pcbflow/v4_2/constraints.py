"""V4.2 M3 intent-level constraint contract: validator + injection spec.

prereg-m3 constraint_contract_v1: model output shape
{constraints: {corridor: [{layer, rect_mm}], keepout: [{layer, rect_mm}]},
 nets: [net_id]}; corridor = soft discourage (frozen extra cost, per-net),
keepout = hard block (per-net).  The validator is deterministic and
fail-closed: any violation blocks the whole constraint set (the treatment
arm falls back to the baseline solve, blocked disclosed -- never patched).

Escape check (taskbook M3 "不封锁端点逃逸"): for rect-only constraints on
this domain, convex containment of a listed net's pad region (grown by
clearance + half trace width) is the exact sealing condition -- no keepout
rect may overlap any applicable net's grown pad box (prereg disclosure:
simpler than the 0.05mm BFS wording, exact for rects).

Coordinate frame: v4-svg-route-2 package numbers ARE board mm (zero-offset
round-trip test-enforced) -- rects are consumed as-is, zero conversion.
"""

from pcbflow.v4exp.grid import GridWorld, V4ExpError

#: Frozen corridor discourage cost per cell-step (prereg-m3).
CORRIDOR_EXTRA_COST = 5.0
WORKSPACE_MARGIN_MM = 2.0


def _is_rect_ok(rect):
    if (not isinstance(rect, list) or len(rect) != 4
            or not all(isinstance(v, (int, float)) for v in rect)):
        return False
    return rect[0] < rect[2] and rect[1] < rect[3]


def _pad_boxes(world, nid):
    margin = world.clearance_mm + world.net_width(nid) / 2.0
    out = []
    for pid in world.net_endpoints[nid]:
        pad = world.pad_by_id[pid]
        w, h = float(pad["w_mm"]) / 2.0, float(pad["h_mm"]) / 2.0
        out.append((float(pad["x_mm"]) - w - margin,
                    float(pad["y_mm"]) - h - margin,
                    float(pad["x_mm"]) + w + margin,
                    float(pad["y_mm"]) + h + margin,
                    world.layer_index[str(pad["layer"])]))
    return out


def validate_constraints(board, payload):
    """Deterministic fail-closed validation. Returns
    {ok, violations[], constraints} -- constraints present only when ok."""
    world = GridWorld(board)
    v = []
    if not isinstance(payload, dict):
        return {"ok": False, "violations": ["payload not an object"],
                "constraints": None}
    c = payload.get("constraints")
    if not isinstance(c, dict):
        return {"ok": False, "violations": ["constraints missing/not object"],
                "constraints": None}
    nets = c.get("nets", payload.get("nets"))
    corridor_items = c.get("corridor", [])
    keepout_items = c.get("keepout", [])
    empty_proposal = (isinstance(corridor_items, list) and not corridor_items
                      and isinstance(keepout_items, list) and not keepout_items)
    if (not isinstance(nets, list)
            or not all(isinstance(n, str) for n in nets)
            or (not nets and not empty_proposal)):
        v.append("nets must be a non-empty list of strings")
        nets = []
    unknown = [n for n in nets if n not in set(world.net_ids)]
    if unknown:
        v.append("unknown nets: %s" % ",".join(unknown))
    net_set = set(nets) & set(world.net_ids)
    x0, y0, x1, y1 = (float(t) for t in world.board["board"]["bbox_mm"])
    ws = [x0 - WORKSPACE_MARGIN_MM, y0 - WORKSPACE_MARGIN_MM,
          x1 + WORKSPACE_MARGIN_MM, y1 + WORKSPACE_MARGIN_MM]
    normalized = {"corridor": [], "keepout": [], "nets": sorted(net_set)}
    seen = set()
    for kind in ("corridor", "keepout"):
        items = c.get(kind, [])
        if not isinstance(items, list):
            v.append("%s must be a list" % kind)
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                v.append("%s[%d] not an object" % (kind, i))
                continue
            layer = item.get("layer")
            if layer not in world.layer_index:
                v.append("%s[%d] unknown layer %r" % (kind, i, layer))
                continue
            rect = item.get("rect_mm")
            if not _is_rect_ok(rect):
                v.append("%s[%d] malformed/reversed rect" % (kind, i))
                continue
            if (rect[0] < ws[0] or rect[1] < ws[1]
                    or rect[2] > ws[2] or rect[3] > ws[3]):
                v.append("%s[%d] rect outside routing workspace" % (kind, i))
                continue
            key = (kind, layer, tuple(round(float(t), 6) for t in rect))
            if key in seen:
                v.append("%s[%d] duplicate rect" % (kind, i))
                continue
            seen.add(key)
            if kind == "keepout":
                li = world.layer_index[layer]
                for nid in net_set:
                    for (px0, py0, px1, py1, pli) in _pad_boxes(world, nid):
                        if (pli == li and rect[0] < px1 and rect[2] > px0
                                and rect[1] < py1 and rect[3] > py0):
                            v.append("keepout[%d] seals pad escape of net %s"
                                     % (i, nid))
                            break
            normalized[kind].append({"layer": layer,
                                     "rect_mm": [round(float(t), 6)
                                                 for t in rect]})
    if v:
        return {"ok": False, "violations": v, "constraints": None}
    return {"ok": True, "violations": [], "constraints": normalized}


def injection_spec(board, validated):
    """Validated constraints -> mirror per-net injection maps."""
    world = GridWorld(board)
    bias_by_net = {}
    ko_by_net = {}
    for item in validated["corridor"]:
        li = world.layer_index[item["layer"]]
        cells = world.cells_in_rect(item["rect_mm"], 0.0)
        for nid in validated["nets"]:
            d = bias_by_net.setdefault(nid, {})
            for (ix, iy) in cells:
                d[(li, ix, iy)] = CORRIDOR_EXTRA_COST
    for item in validated["keepout"]:
        li = world.layer_index[item["layer"]]
        cells = set(world.cells_in_rect(item["rect_mm"], 0.0))
        for nid in validated["nets"]:
            ko_by_net.setdefault(nid, {}).setdefault(li, set()).update(cells)
    return {"cost_bias_by_net": {k: v for k, v in bias_by_net.items() if v},
            "hard_keepout_by_net": {k: v for k, v in ko_by_net.items() if v}}


def build_negative_set(board):
    """Constructed illegal constraint sets, >= 30 cases across >= 6
    categories (prereg G-M3a; P1 negative-set discipline)."""
    world = GridWorld(board)
    nid = sorted(world.net_ids)[0]
    x0, y0, x1, y1 = (float(t) for t in world.board["board"]["bbox_mm"])
    pad = world.pad_by_id[world.net_endpoints[nid][0]]
    cases = []

    def C(cid, payload):
        cases.append((cid, payload))

    for k in range(4):
        C("malformed_rect_%d" % k,
          {"constraints": {"corridor": [{"layer": "F.Cu",
                                         "rect_mm": [1, 2, 3]}], "keepout": []},
           "nets": [nid]})
        C("reversed_rect_%d" % k,
          {"constraints": {"corridor": [{"layer": "F.Cu",
                                         "rect_mm": [20.0, 20.0, 10.0, 10.0]}],
                           "keepout": []}, "nets": [nid]})
        C("out_of_workspace_%d" % k,
          {"constraints": {"keepout": [{"layer": "B.Cu",
                                        "rect_mm": [x0 - 30.0, y0 - 30.0,
                                                    x0 - 1.0, y0 - 1.0]}],
                           "corridor": []}, "nets": [nid]})
        C("unknown_layer_%d" % k,
          {"constraints": {"corridor": [{"layer": "In9.Cu",
                                         "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
                           "keepout": []}, "nets": [nid]})
        C("unknown_net_%d" % k,
          {"constraints": {"corridor": [{"layer": "F.Cu",
                                         "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
                           "keepout": []}, "nets": ["n99"]})
        C("empty_nets_%d" % k,
          {"constraints": {"corridor": [{"layer": "F.Cu",
                                         "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
                           "keepout": []}, "nets": []})
        C("pad_sealing_%d" % k,
          {"constraints": {"keepout": [{"layer": str(pad["layer"]),
                                        "rect_mm": [float(pad["x_mm"]) - 1.0,
                                                    float(pad["y_mm"]) - 1.0,
                                                    float(pad["x_mm"]) + 1.0,
                                                    float(pad["y_mm"]) + 1.0]}],
                           "corridor": []}, "nets": [nid]})
        C("duplicate_rect_%d" % k,
          {"constraints": {"corridor": [
              {"layer": "F.Cu", "rect_mm": [10.0, 10.0, 12.0, 12.0]},
              {"layer": "F.Cu", "rect_mm": [10.0, 10.0, 12.0, 12.0]}],
              "keepout": []}, "nets": [nid]})
    return cases
