# -*- coding: utf-8 -*-
"""pcbnew(SWIG) 参考导出器——用 F:\\kicad\\bin\\python.exe 运行。

只读加载板文件，导出 pads/tracks/vias 的权威几何到 JSON，供
check_mirror_vs_pcbnew.py 与镜像逐项比对。绝不 SaveBoard。
"""
import json
import os
import sys

import pcbnew

proj = sys.argv[1]
out_path = sys.argv[2]

board_path = None
pro_path = None
for f in os.listdir(proj):
    if f.endswith(".kicad_pro"):
        pro_path = os.path.join(proj, f)
import os as _os
if pro_path:
    stem = _os.path.splitext(_os.path.basename(pro_path))[0]
    cand = _os.path.join(proj, stem + ".kicad_pcb")
    if _os.path.exists(cand):
        board_path = cand
if board_path is None:
    for f in os.listdir(proj):
        if f.endswith(".kicad_pcb"):
            board_path = os.path.join(proj, f)
            break

b = pcbnew.LoadBoard(board_path)
MM = 1000000.0

pads = []
for p in b.GetPads():
    fp = p.GetParentFootprint()
    pos = p.GetPosition()
    sz = p.GetSize()
    ds = p.GetDrillSize()
    layers = []
    lset = p.GetLayerSet()
    for lname, lid in (("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu),
                       ("In1.Cu", pcbnew.In1_Cu), ("In2.Cu", pcbnew.In2_Cu)):
        if lset.Contains(lid):
            layers.append(int(lid))
    pads.append({
        "ref": fp.GetReference() if fp else "?",
        "number": p.GetNumber(),
        "net": p.GetNetname(),
        "x": pos.x / MM, "y": pos.y / MM,
        "orient": p.GetOrientation().AsDegrees(),
        "w": sz.x / MM, "h": sz.y / MM,
        "drill": ds.x / MM if ds.x else 0.0,
        "layers": layers,
    })

tracks = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        continue
    s, e = t.GetStart(), t.GetEnd()
    tracks.append({
        "layer": int(t.GetLayer()),
        "x1": s.x / MM, "y1": s.y / MM, "x2": e.x / MM, "y2": e.y / MM,
        "width": t.GetWidth() / MM, "net": t.GetNetname(),
    })

vias = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA":
        continue
    pos = t.GetPosition()
    # T6 坑：GetWidth() 无参触发 assert 洪水；用带层参数形式
    try:
        size = t.GetWidth(int(t.GetLayer())) / MM
    except Exception:
        size = 0.0
    vias.append({
        "x": pos.x / MM, "y": pos.y / MM,
        "size": size,
        "drill": t.GetDrill() / MM,
        "net": t.GetNetname(),
    })

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({"pads": pads, "tracks": tracks, "vias": vias}, fh)
print(f"exported pads={len(pads)} tracks={len(tracks)} vias={len(vias)} -> {out_path}")
