# -*- coding: utf-8 -*-
"""W-D/W-E G1 直读判读（ED-X 呈裁期的披露口径）：绕过 run-result 消费面
（export 崩致其不更新），直接读四板 execute.json 判「全端点连通口径」
——execute verdict=ROUTED 即 route_check 0.4.1 语义（plated 孔筒连通计入）
下的全端点连通过审。程序化产出 JSON；正式 build_p5_gate 全门换血待 ED-X
修复批后补跑（ED2FIX-EXPORT-GAP-DISCLOSURE-2026-09-26.md 呈裁点 2）。
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = ["pmod-crypto", "badgeleds-do-electronics", "thin-pod",
          "thatmicpre-v2"]
OUT = os.path.join(ROOT, "out", "v5-p5", "r1", "w6d-g1-direct-read.json")

rows = []
for b in BOARDS:
    p = os.path.join(ROOT, "out", "v5-p5", "boards", b, "execute.json")
    row = {"board": b}
    if not os.path.isfile(p):
        row["execute_present"] = False
        rows.append(row)
        continue
    row["execute_present"] = True
    row["execute_sha256"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    d = json.load(open(p, encoding="utf-8"))
    ex = d["execute"]
    rd = d.get("routes_doc") or {}
    row["exec_verdict"] = ex.get("verdict")
    row["n_routes_entries"] = len(rd.get("routes") or [])
    row["nets"] = sorted({e["net_id"] for e in (rd.get("routes") or [])})
    # 0.4.1 全端点连通口径：ROUTED=出口自检（含 ③ PTH union 语义）全过
    row["all_endpoint_connected"] = (ex.get("verdict") == "ROUTED")
    # 审计器版本披露面（裁 4）：check.json 的 route_check_version
    cp = os.path.join(ROOT, "out", "v5-p5", "boards", b, "check.json")
    if os.path.isfile(cp):
        chk = json.load(open(cp, encoding="utf-8")).get("check") or {}
        row["route_check_version"] = chk.get("route_check_version")
    rows.append(row)

sat = sum(1 for r in rows if r.get("all_endpoint_connected"))
doc = {
    "generated": sys.argv[1] if len(sys.argv) > 1 else "",
    "caliber": ("全端点连通口径（route_check 0.4.1：plated 孔筒连通计入；"
                "execute verdict=ROUTED 即过审）——ED-X 呈裁期直读披露口径，"
                "正式 build_p5_gate 换血待 ED-X 修复批"),
    "n_sat": sat,
    "denominator": len(BOARDS),
    "rows": rows,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print("SAT %d/%d（全端点连通口径，直读）" % (sat, len(BOARDS)))
for r in rows:
    print("  %-28s %s" % (r["board"],
                          r.get("exec_verdict") if r["execute_present"]
                          else "（execute 未出）"))
print("落盘", OUT)
