"""V4.2 M3 constraint-seat paired experiment engine (prereg-m3).

Arms: baseline = plain solve_board (stable order, no constraints);
treatment = solve_board_injected with validator-passed model constraints
(per-net corridor bias / keepout hard block).  Blocked constraint sets fall
back to the baseline solve with blocked=True disclosed (fail-closed, never
patched).  Model output enters ONLY via constraints.validate_constraints
-> constraints.injection_spec; geometry stays with the engine.
"""

from pcbflow.v4exp.router import solve_board
from pcbflow.v4_2.constraints import injection_spec, validate_constraints
from pcbflow.v4_2.mirror import solve_board_injected

M3_SYSTEM = (
    "You are a PCB routing constraint advisor reading the SVG source of a "
    "routed two-layer board (schema v4-svg-route-2). Machine facts live "
    "ONLY in data-* attributes; colors/classes are visual encodings. You "
    "propose INTENT-LEVEL routing constraints only: soft corridors to "
    "discourage and hard keepouts to forbid, for specific nets. You never "
    "emit geometry, never modify routes, never validate. Better to propose "
    "NOTHING than something low-confidence: an empty constraint set is a "
    "valid, respectable answer. Respond with JSON only."
)

M3_SUFFIX = """
Propose intent-level constraints for this board, or an empty set.
Output shape: a JSON OBJECT {"constraints": {"corridor": [{"layer": "<layer name>", "rect_mm": [x0, y0, x1, y1]}], "keepout": [{"layer": "<layer name>", "rect_mm": [x0, y0, x1, y1]}]}, "nets": ["<net_id>", ...]}.
- rects are axis-aligned boxes in the SAME coordinates as the SVG numbers (board mm), x0<x1, y0<y1;
- "nets" = the net_ids the constraints apply to (non-empty, only ids visible in the SVG);
- corridor = soft discourage (engine adds a cost penalty inside the rect for those nets); keepout = hard forbid (engine blocks the rect for those nets);
- a keepout rect must NOT cover any pad of the listed nets (that would seal the endpoint);
- rects must stay within the board outline expanded by 2.0 mm;
- propose at most 3 corridors and 3 keepouts; empty arrays + a valid nets list, or no constraints at all if nothing is confident.
JSON only."""


def request_for(board):
    return {"route_order": sorted(n["net_id"] for n in board["nets"]),
            "group": "A"}


def run_arm(board, payload):
    """One scenario, constraint arm vs baseline. Deterministic given the
    recorded model payload."""
    req = request_for(board)
    baseline = solve_board(board, req)
    out = {"baseline_status": baseline["status"],
           "baseline_objective": baseline["metrics"].get("objective"),
           "baseline_result": baseline}
    v = validate_constraints(board, payload or {})
    if not v["ok"]:
        out.update({"arm_status": "blocked",
                    "violations": v["violations"],
                    "treatment_status": baseline["status"],
                    "treatment_objective": out["baseline_objective"],
                    "treatment_result": baseline})
        return out
    spec = injection_spec(board, v["constraints"])
    treat = solve_board_injected(
        board, req,
        cost_bias_by_net=spec["cost_bias_by_net"],
        hard_keepout_by_net=spec["hard_keepout_by_net"])
    if treat["status"] == "sat":
        assert sum(treat["metrics"]["violations"].values()) == 0
        assert treat["metrics"]["all_connected"] is True
    out.update({"arm_status": "ok",
                "constraints": v["constraints"],
                "treatment_status": treat["status"],
                "treatment_objective": treat["metrics"].get("objective"),
                "treatment_result": treat})
    return out


def gain_pct(arm):
    """(baseline - treatment)/baseline * 100; positive = improvement."""
    if arm["baseline_objective"] is None or arm["treatment_objective"] is None:
        return None
    return round((arm["baseline_objective"] - arm["treatment_objective"])
                 / arm["baseline_objective"] * 100, 4)
