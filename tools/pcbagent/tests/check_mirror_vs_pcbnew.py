# -*- coding: utf-8 -*-
"""镜像几何 vs pcbnew(SWIG) 参考逐项比对（B1 交叉验证）。

用法（系统 python）：python tests/check_mirror_vs_pcbnew.py --project <dir> --ref <json>
容差：位置/宽度 1e-6 mm（内部 nm 整数），角度 1e-4°。
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbagent.mirror import BoardMirror, STACK_ORDER_ALL  # noqa: E402

POS_TOL = 1e-6
ANG_TOL = 1e-3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--ref", required=True)
    args = ap.parse_args()

    ref = json.load(open(args.ref, encoding="utf-8"))
    m = BoardMirror(args.project)
    errors = []

    # ---- pads ----
    my_pads = {}
    for p in m.pads:
        my_pads[(p.ref, p.number)] = p
    ref_pads = {}
    for p in ref["pads"]:
        ref_pads[(p["ref"], p["number"])] = p
    if len(my_pads) != len(ref_pads):
        errors.append(f"pad count {len(my_pads)} != ref {len(ref_pads)}")
    for k, rp in ref_pads.items():
        mp = my_pads.get(k)
        if mp is None:
            errors.append(f"pad {k} missing in mirror")
            continue
        if abs(mp.x - rp["x"]) > POS_TOL or abs(mp.y - rp["y"]) > POS_TOL:
            errors.append(f"pad {k} pos mirror=({mp.x:.6f},{mp.y:.6f}) "
                          f"ref=({rp['x']:.6f},{rp['y']:.6f})")
        if abs(mp.w - rp["w"]) > POS_TOL or abs(mp.h - rp["h"]) > POS_TOL:
            errors.append(f"pad {k} size mirror=({mp.w},{mp.h}) ref=({rp['w']},{rp['h']})")
        # 角度模 180 等价（矩形对称）
        dang = abs((mp.rot - rp["orient"]) % 180.0)
        dang = min(dang, 180.0 - dang)
        if dang > ANG_TOL:
            errors.append(f"pad {k} rot mirror={mp.rot} ref={rp['orient']}")
        if mp.drill and abs(mp.drill - rp["drill"]) > POS_TOL:
            errors.append(f"pad {k} drill mirror={mp.drill} ref={rp['drill']}")
        if set(mp.layers) != set(rp["layers"]) and not mp.npth:
            errors.append(f"pad {k} layers mirror={sorted(mp.layers)} "
                          f"ref={sorted(rp['layers'])}")

    # ---- tracks ----
    my_tracks = [(t.layer, t.x1, t.y1, t.x2, t.y2, t.width, t.net) for t in m.tracks]
    ref_tracks = [(t["layer"], t["x1"], t["y1"], t["x2"], t["y2"], t["width"], t["net"])
                  for t in ref["tracks"]]
    if len(my_tracks) != len(ref_tracks):
        errors.append(f"track count {len(my_tracks)} != ref {len(ref_tracks)}")
    ref_set = {}
    for t in ref_tracks:
        ref_set[t] = ref_set.get(t, 0) + 1
    for t in my_tracks:
        if ref_set.get(t, 0) > 0:
            ref_set[t] -= 1
        else:
            errors.append(f"track not in ref: {t}")
            if len(errors) > 30:
                break

    # ---- vias ----
    my_vias = sorted((v.x, v.y, v.size, v.drill, v.net) for v in m.vias)
    ref_vias = sorted((v["x"], v["y"], v["size"], v["drill"], v["net"])
                      for v in ref["vias"])
    if len(my_vias) != len(ref_vias):
        errors.append(f"via count {len(my_vias)} != ref {len(ref_vias)}")
    for a, b in zip(my_vias, ref_vias):
        if any(abs(x - y) > POS_TOL for x, y in zip(a[:4], b[:4])) or a[4] != b[4]:
            errors.append(f"via mismatch mirror={a} ref={b}")
            if len(errors) > 40:
                break

    print(f"pads={len(my_pads)}/{len(ref_pads)} tracks={len(my_tracks)}/"
          f"{len(ref_tracks)} vias={len(my_vias)}/{len(ref_vias)}")
    if errors:
        print(f"MISMATCHES: {len(errors)}")
        for e in errors[:40]:
            print(" -", e)
        return 1
    print("MIRROR == PCBNEW REF: 100%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
