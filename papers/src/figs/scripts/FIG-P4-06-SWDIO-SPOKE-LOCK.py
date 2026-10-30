# -*- coding: utf-8 -*-
"""
FIG-P4-06-SWDIO-SPOKE-LOCK — 篇四图 6 端点自锁 8 辐条（SWDIO J4 PTH 八方向全锁，割=8）

数据件（全部机器件直读，禁硬编码坐标）：
  - <WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/live2s1-results.json（rows[SWDIO]：
    cut_groups.items 8 辐条、why.per_layer 封锁 cell bbox、scope res/region、verified）
  - <WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/workspace/live/stm32h743-coreboard-revc.kicad_pcb
    （J4/U1 footprint at + pad at 板件直读：J4.13 与 U1.124 焊盘几何）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-06-SWDIO-SPOKE-LOCK.png
"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_RED = "#c44e52"; C_GREEN = "#55a868"; C_GRAY = "#8c8c8c"

res_path = "<WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/live2s1-results.json"
d = json.load(open(res_path, encoding="utf-8"))
row = [r for r in d["rows"] if r.get("net") == "SWDIO"]
assert len(row) == 1, "SWDIO 行未唯一定位"
row = row[0]
bs = row["board_strengthen"]
cert = bs["certificate"]
assert cert["cut_count"] == 8 and row["certificate_cut_count"] == 8, "割=8 断言失败"
assert bs["status"] == "UNSAT" and row.get("live2s1_status") == "UNSAT" and cert["verified"] is True, "verified UNSAT 断言失败"
grp = cert["cut_groups"][0]
assert len(cert["cut_groups"]) == 1 and grp["kind"] == "spoke", "唯一 spoke 割组断言失败"
items = [tuple(x) for x in grp["items"]]
scope = row["certificate_scope"]
res = scope["res_mm"]; region = scope["region_mm"]
assert res == 0.05 and region == [0.0, 0.0, 70.0, 70.0], "0.05mm 格／70×70 板域断言失败"
# 8 项应为同一格点的全部 8 个 8 邻（端点自锁）
xs = sorted({a for a, b in items}); ys = sorted({b for a, b in items})
assert len(xs) == 3 and len(ys) == 3, "辐条邻域 3×3 断言失败"
node = (xs[1], ys[1])
expect = {(node[0] + dx, node[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - {node}
assert set(items) == expect and len(items) == 8, "8 辐条=端点 8 邻全覆盖断言失败"
node_mm = (node[0] * res, node[1] * res)
pl = grp["why"]["per_layer"]
layers_closed = sorted({p["layer"] for p in pl})
assert layers_closed == [0, 6], "封锁层 0/6（F.Cu+B.Cu）断言失败"
why0 = pl[0]["why"]
assert why0["dist"] == 0.0 and why0["rule"] == "hole_clearance" and pl[0]["closed"] == "cell", "hole_clearance d=0 断言失败"
bbox = why0["prim_bbox"]
spokes_open = [tuple(x) for x in cert.get("spokes_b_open", [])]
assert len(spokes_open) == 8, "B 端 8 辐条开断言失败"
oxs = sorted({a for _, a, b in spokes_open}); oys = sorted({b for _, a, b in spokes_open})
onode = (oxs[1], oys[1]); onode_mm = (onode[0] * res, onode[1] * res)

# 板件直读（kicad_pcb 解析 J4.13 / U1.124）
pcb = open("<WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/workspace/live/"
           "stm32h743-coreboard-revc.kicad_pcb", encoding="utf-8", errors="replace").read()

def footprint_pad(ref, pad_name):
    m = re.search(r'\(property "Reference" "%s"' % ref, pcb)
    assert m, "Reference %s 未定位" % ref
    seg = pcb[pcb.rfind("(footprint", 0, m.start()):]
    at = re.search(r'\(at ([-0-9.]+) ([-0-9.]+)', seg)
    fx, fy = float(at.group(1)), float(at.group(2))
    pm = re.search(r'\(pad "%s" (\w+) (\w+)[^\n()]*\n\s*\(at ([-0-9.]+) ([-0-9.]+)\)\n\s*\(size ([-0-9.]+) ([-0-9.]+)\)(?:\n\s*\(drill ([-0-9.]+)\))?' % pad_name, seg)
    ptype, shape, px, py = pm.group(1), pm.group(2), float(pm.group(3)), float(pm.group(4))
    w, h = float(pm.group(5)), float(pm.group(6))
    drill = pm.group(7)
    nm = re.search(r'\(net "([^"]+)"\)', seg[pm.start():pm.start() + 600])
    return dict(ptype=ptype, shape=shape, x=fx + px, y=fy + py, w=w, h=h,
                drill=(float(drill) if drill else None), net=nm.group(1) if nm else None)

j4 = footprint_pad("J4", "13")
u1 = footprint_pad("U1", "124")
assert j4["net"] == "SWDIO" and u1["net"] == "SWDIO", "两焊盘 SWDIO 网断言失败"
assert j4["ptype"] == "thru_hole" and j4["shape"] == "circle" and j4["drill"] == 1.0 and abs(j4["w"] - 1.7) < 1e-9, "J4.13 PTH 几何断言失败"
assert abs(j4["x"] - 2.63) < 1e-9 and abs(j4["y"] - 26.11) < 1e-9, "J4.13=(2.63,26.11) 断言失败"
assert abs(u1["x"] - 47.675) < 1e-9 and abs(u1["y"] - 16.15) < 1e-9, "U1.124=(47.675,16.15) 断言失败"
dist = ((j4["x"] - u1["x"]) ** 2 + (j4["y"] - u1["y"]) ** 2) ** 0.5
assert abs(dist - 46.1) < 0.1, "飞线 46.1mm 直线断言失败"
# 端点格心 vs 焊盘中心（0.05 格吸附一致性）
assert abs(node_mm[0] - j4["x"]) < 0.05 and abs(node_mm[1] - j4["y"]) < 0.05, "J4 端点格心≈焊盘中心断言失败"
assert abs(onode_mm[0] - u1["x"]) < 0.05 and abs(onode_mm[1] - u1["y"]) < 0.05, "U1 端点格心≈焊盘中心断言失败"

fig = plt.figure(figsize=(13.2, 7.4))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.15], wspace=0.18)

# 左：板级总览
ax = fig.add_subplot(gs[0])
ax.add_patch(Rectangle((region[0], region[1]), region[2], region[3], fc="#fafafa", ec="#555555", lw=1.4))
ax.plot([j4["x"], u1["x"]], [j4["y"], u1["y"]], ls="--", lw=1.6, color=C_GRAY)
ax.annotate("", xy=(u1["x"], u1["y"]), xytext=(j4["x"], j4["y"]),
            arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.6, ls="--"))
ax.add_patch(Circle((j4["x"], j4["y"]), 1.4, fc=C_RED, ec="#222222", lw=1.2, zorder=5))
ax.add_patch(Rectangle((u1["x"] - 1.2, u1["y"] - 0.55), 2.4, 1.1, fc=C_BLUE, ec="#222222", lw=1.2, zorder=5))
# U1 端 8 辐条全开（spokes_b_open 板件直读渲染：B 端邻格全开）
for (lay, a, b) in spokes_open:
    nx, ny = a * res, b * res
    dx, dy = nx - onode_mm[0], ny - onode_mm[1]
    L = max(abs(dx), abs(dy)) or 1.0
    ax.plot([u1["x"] + dx / L * 1.1, u1["x"] + dx / L * 2.4],
            [u1["y"] + dy / L * 1.1, u1["y"] + dy / L * 2.4],
            color=C_BLUE, lw=2.6, solid_capstyle="round", zorder=4)
    ax.add_patch(Circle((u1["x"] + dx / L * 2.65, u1["y"] + dy / L * 2.65), 0.6,
                        fc=C_BLUE, ec="#222222", lw=0.8, zorder=4))
ax.annotate("J4.13 PTH (2.63, 26.11)\n端点自锁（8 辐条全锁，割=8）", xy=(j4["x"] + 1.0, j4["y"]),
            xytext=(9.5, 33.5), fontsize=9.6, color="#8a2f33", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.8))
ax.annotate("U1.124 SMD (47.675, 16.15)\n8 辐条全开（B 端开放）", xy=(u1["x"] - 1.2, u1["y"]),
            xytext=(29.0, 9.0), fontsize=9.6, color="#33517a", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.8))
ax.text((j4["x"] + u1["x"]) / 2, (j4["y"] + u1["y"]) / 2 + 1.6, "直连 %.1f mm（SWDIO 飞线工单基线）" % dist,
        fontsize=8.8, color="#555555", rotation=0)
ax.set_xlim(-3, 74); ax.set_ylim(-3, 74)
ax.set_aspect("equal"); ax.grid(ls=":", alpha=0.35)
ax.set_xlabel("X（mm）", fontsize=10); ax.set_ylabel("Y（mm）", fontsize=10)
ax.set_title("743 板（70×70mm）SWDIO 两端点\n（restricted 证书域 res=0.05mm 格心）", fontsize=11)

# 右：J4 PTH 端点自锁放大
ax = fig.add_subplot(gs[1])
bx0, by0, bx1, by1 = bbox
pad_r = j4["w"] / 2
ax.add_patch(Circle((j4["x"], j4["y"]), pad_r, fc="#f0d9d5", ec="#222222", lw=2.0, zorder=3))
ax.add_patch(Circle((j4["x"], j4["y"]), j4["drill"] / 2, fc="white", ec="#222222", lw=1.5, zorder=4))
ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fc="none", ec=C_ORANGE, lw=2.4, ls="-.",
                       hatch="////", zorder=6, alpha=0.9))
gx0, gx1 = int((bx0 - 1.2) / res), int((bx1 + 1.2) / res) + 1
gy0, gy1 = int((by0 - 1.2) / res), int((by1 + 1.2) / res) + 1
for gi in range(gx0, gx1 + 1):
    for gj in range(gy0, gy1 + 1):
        is_node = (gi == node[0] and gj == node[1])
        is_nbr = (gi, gj) in expect
        if is_node:
            ax.add_patch(Circle((gi * res, gj * res), 0.075, fc=C_BLUE, ec="#222222", lw=1.4, zorder=7))
        elif is_nbr:
            ax.add_patch(Circle((gi * res, gj * res), 0.055, fc="white", ec=C_RED, lw=1.6, zorder=7))
        else:
            ax.plot([gi * res], [gj * res], marker=".", color="#bbbbbb", markersize=2.6, zorder=2)
for (a, b) in sorted(expect):
    ax.plot([node[0] * res, a * res], [node[1] * res, b * res], color=C_RED, lw=2.4, ls="--", zorder=5)
    ax.plot([((node[0] + a) / 2) * res], [((node[1] + b) / 2) * res], marker="x", color=C_RED,
            markersize=11, markeredgewidth=2.6, zorder=8)
ax.annotate("封锁 cell：hole_clearance\ndist=0.0（层 0/6＝F.Cu+B.Cu）\nprim_bbox=%s" % bbox,
            xy=(bx1, by0), xytext=(bx1 + 0.28, by0 - 0.52), fontsize=9.0, color="#96522e",
            arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=1.8))
ax.text(j4["x"], j4["y"] - 0.86, "J4.13 孔盘 φ1.7／孔 φ1.0（板件直读）", ha="center", fontsize=8.6)
ax.text(bx0 + 0.5, by1 + 0.42, "端点格心 (%.2f, %.2f) 的 8 条辐条全部被割（红×8）→ 割数=8" % node_mm,
        ha="center", fontsize=9.4, color="#8a2f33", fontweight="bold")
ax.set_xlim(bx0 - 1.35, bx1 + 1.35); ax.set_ylim(by0 - 1.5, by1 + 1.15)
ax.set_aspect("equal"); ax.grid(ls=":", alpha=0.3)
ax.set_xlabel("X（mm）", fontsize=10); ax.set_ylabel("Y（mm）", fontsize=10)
ax.set_title("J4 PTH 端点自锁放大（0.05mm 格心＋8 邻辐条模型）", fontsize=11)

fig.suptitle("篇四图 6　端点自锁 8 辐条：SWDIO J4 PTH 八方向全锁（割=8，verified UNSAT，割数即机制签名）",
             fontsize=14, fontweight="bold", y=0.995)
fig.text(0.5, 0.012,
         "数据源：live2s1-results.json rows[SWDIO]（cut_groups 8 项=端点 8 邻全覆盖、程序化集合断言；spokes_b_open=U1 端 8 邻全开）；"
         "stm32h743-coreboard-revc.kicad_pcb（J4/U1 footprint at＋pad at 直读解析，J4.13=(2.63,26.11) φ1.7/孔φ1.0、U1.124=(47.675,16.15)）。\n"
         "证书口径：restricted_lattice_center_4neigh_vias（0.05mm 格心 4 邻格网＋同格位过孔＋端点 8 邻辐条，ripup=False 冻结铜）——restricted blocking certificate，不等价全域物理不可布。"
         "0Ω 跳线只破端点自锁型（J3.5 铜链包含 JU1_PAD，探针已证可破）；SWDIO 飞线工单 46.1mm AWG30 已批待装配。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-06-SWDIO-SPOKE-LOCK.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-06 生成：%s（%d B）割=8+8 邻全覆盖+J4/U1 板件坐标+飞线 46.1mm 断言全过" % (out, os.path.getsize(out)))
