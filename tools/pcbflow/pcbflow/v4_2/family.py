"""V4.2 M1 scenario family f12 -- v4_2-owned crowded family (prereg-m1).

Taskbook §3 M1 calibration set needs a NEW crowded family (f1-f8 are frozen
read-only; taskbook §2.4).  f12 = "staggered four-wall squeeze": four
single-layer keepout walls alternating F/B/F/B with staggered gaps; net
count 5-7.  Satisfiability by construction: every wall blocks exactly one
layer, so at every x at least one layer is fully open (f6's argument with
one more wall -- more via decisions, tighter squeeze).

Determinism: seed = gen_scenarios.seed_for(sid) (sha256-derived, the frozen
cmp convention); same sid -> byte-identical board.  Board schema/geometry
contract identical to the frozen families (same BBOX/LAYERS/Rules/PadAlloc/
_post_check via read-only imports).
"""

import json
import os
import random

from pcbflow.v4exp import model
from pcbflow.v4exp.gen_scenarios import (BBOX, COMPONENTS, LAYERS, PadAlloc,
                                         _post_check, seed_for, spaced_values)
from pcbflow.v4exp.model import Keepout, Net, Rules

F12_IDS = ["cal-f12-%02d" % i for i in range(1, 9)]

#: Frozen generation parameter tables (prereg-m1 scenario_sets.cal_new_family)
_K1_X = (8.0, 9.0)
_K2_X = (14.0, 15.0, 16.0)
_K3_X = (21.0, 22.0)
_K4_X = (27.0, 28.0, 29.0)
_KB_Y = (9.0, 10.0)
_NET_COUNTS = (5, 6, 7)


def gen_f12(sid, split, seed, rng) -> model.Board:
    """f12 staggered four-wall squeeze (see module docstring)."""
    alloc = PadAlloc()
    n = rng.choice(_NET_COUNTS)
    xa = rng.choice(_K1_X)
    xb = rng.choice(_K2_X)
    xc = rng.choice(_K3_X)
    xd = rng.choice(_K4_X)
    yb = rng.choice(_KB_Y)
    yd = rng.choice(_KB_Y)
    keepouts = [
        Keepout("k1", [xa, 3.0, xa + 1.0, 20.0], ["F.Cu"]),
        Keepout("k2", [xb, yb, xb + 1.0, 27.0], ["B.Cu"]),
        Keepout("k3", [xc, 3.0, xc + 1.0, 20.0], ["F.Cu"]),
        Keepout("k4", [xd, yd, xd + 1.0, 27.0], ["B.Cu"]),
    ]
    lys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    rys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    pads, nets = [], []
    for i in range(n):
        nid = "n%d" % (i + 1)
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, 4.0, lys[i]))
        pads.append(alloc.pad(cb, nid, 36.0, rys[i]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    board = model.Board(scenario_id=sid, split=split, family="f12",
                        seed=seed, bbox_mm=list(BBOX), layers=list(LAYERS),
                        rules=Rules(), pads=pads, nets=nets,
                        keepouts=keepouts, relations=[], label="satisfiable")
    _post_check(board)
    return board


def generate_f12_board(sid, split="calibration"):
    rng = random.Random(seed_for(sid))
    return gen_f12(sid, split, seed_for(sid), rng)


def emit(out_dir):
    """Write the 8 frozen f12 board snapshots; returns per-file sha256."""
    import hashlib
    os.makedirs(out_dir, exist_ok=True)
    hashes = {}
    for sid in F12_IDS:
        obj = generate_f12_board(sid).to_obj()
        text = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True) + "\n"
        path = os.path.join(out_dir, "board-snapshot-%s.json" % sid)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        hashes[sid] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return hashes
