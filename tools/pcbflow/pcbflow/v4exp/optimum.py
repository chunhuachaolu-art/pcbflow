"""pcbflow.v4exp.optimum -- exact optimum over the sequential route order.

CLI contract: read exactly one JSON request from stdin
({"board_path": ..., "out_path": ...}), compute, print the result JSON on
stdout and (when "out_path" is present) write it to that file.

Method: enumerate every permutation of the board's nets (only when there
are at most MAX_NETS_FOR_EXHAUSTION nets), solve each permutation with the
router's own core and empty preferences, and keep the minimum objective.
Ties keep the lexicographically smallest order (permutations are generated
in lexicographic order and replaced only on strict improvement).

Five-state discipline: UNSAT is claimed only with an exhaustive certificate
-- every permutation of the full order space failed.  Otherwise no UNSAT
conclusion is written at all.
"""

import itertools
import json
import os
import sys

try:
    from . import router
    from .grid import GridWorld, canonical_json
except ImportError:  # direct file run: python pcbflow/v4exp/optimum.py
    import router
    from grid import GridWorld, canonical_json

OPT_SCHEMA = "pcbflow.v4exp.optimum/1"
CERTIFICATE = "exhaustive_over_permutations_v1"
MAX_NETS_FOR_EXHAUSTION = 4


def run_optimum(board):
    """Exhaustive-permutation optimum for one board snapshot."""
    world = GridWorld(board)
    nets = sorted(world.net_ids)
    if len(nets) > MAX_NETS_FOR_EXHAUSTION:
        return {
            "schema": OPT_SCHEMA,
            "scenario_id": world.scenario_id,
            "opt_eligible": False,
        }
    best_obj = None
    best_order = []
    sat_permutations = 0
    permutations_tried = 0
    for perm in itertools.permutations(nets):
        permutations_tried += 1
        run = router.solve_board(board, {"route_order": list(perm), "group": "OPT"})
        if run.get("status") == "sat":
            sat_permutations += 1
            obj = float(run["metrics"]["objective"])
            if best_obj is None or obj < best_obj:
                best_obj = obj
                best_order = list(perm)
    out = {
        "schema": OPT_SCHEMA,
        "scenario_id": world.scenario_id,
        "opt_eligible": True,
        "permutations_tried": permutations_tried,
        "best_objective": best_obj,
        "best_order": best_order,
        "sat_permutations": sat_permutations,
        "certificate": CERTIFICATE,
    }
    if sat_permutations == 0:
        # exhaustive certificate: the whole (order-only) strategy space failed
        out["unsat_certified"] = True
    return out


def main():
    payload = json.loads(sys.stdin.read())
    with open(payload["board_path"], "r", encoding="utf-8") as f:
        board = json.load(f)
    result = run_optimum(board)
    out_path = payload.get("out_path")
    if out_path:
        d = os.path.dirname(str(out_path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(str(out_path), "w", encoding="utf-8") as f:
            f.write(canonical_json(result))
            f.write("\n")
    sys.stdout.write(canonical_json(result))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
