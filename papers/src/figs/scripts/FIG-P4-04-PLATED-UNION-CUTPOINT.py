# -*- coding: utf-8 -*-
"""
FIG-P4-04-PLATED-UNION-CUTPOINT — 篇四图 4 plated-union 割点（route_check ③ 层连通审计误杀翻案）

数据件（全部机器件直读，禁硬编码坐标）：
  - <ENGINE_ROOT>/out/v5-p5/r1/ed2-diagnosis/crypto-ed2-analysis.json（+3V3 网 18 entries 拓扑/关节）
  - <ENGINE_ROOT>/out/v5-p5/boards/pmod-crypto/board.json（割点孔 drill/plated 板件直读）
  - <ENGINE_ROOT>/out/v5-p5/r1/ed2-diagnosis/pth-fix-preverify.json（修复前后分量数）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-04-PLATED-UNION-CUTPOINT.png
"""
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_F = "#4c72b0"; C_B = "#dd8452"; C_RED = "#c44e52"; C_GREEN = "#55a868"; C_GRAY = "#8c8c8c"

ana = json.load(open("<ENGINE_ROOT>/out/v5-p5/r1/ed2-diagnosis/crypto-ed2-analysis.json", encoding="utf-8"))
ecs = ana["entry_components"]
assert len(ecs) == 18 and ana["n_entries"] == 18 and ana["partition_id"] == "PT-_3V3", "18 entries +3V3 断言失败"

board = json.load(open("<ENGINE_ROOT>/out/v5-p5/boards/pmod-crypto/board.json", encoding="utf-8"))
holes = board["board"]["holes"]
plated_pts = [tuple(h["pos_mm"]) for h in holes if h.get("plated")]
def plated_at(pt):
    return next((h for h in holes if h.get("plated")
                 and abs(h["pos_mm"][0] - pt[0]) < 1e-3 and abs(h["pos_mm"][1] - pt[1]) < 1e-3), None)

disc = [j for j in ana["joints"] if not j["connected"]]
assert len(disc) == 1, "唯一不连通关节断言失败"
cut = disc[0]["pt"]
cut_hole = plated_at(cut)
assert cut_hole is not None and abs(cut_hole["drill_mm"] - 1.0) < 1e-9 and cut_hole["plated"] is True, \
    "割点=1.0mm plated 孔断言失败"
assert cut == [168.8156, 69.273], "割点坐标断言失败"
assert disc[0]["is_pad"] and disc[0]["layers"] == ["B.Cu", "F.Cu"] and disc[0]["n_vias"] == 0

# 并查复算（脚本内重演主审不依赖执行体脚本的复算口径）
def components(plated_union):
    parent = list(range(len(ecs)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    by_pt = defaultdict(list)
    for i, e in enumerate(ecs):
        for pt in [e["first"], e["last"]] + list(e.get("tv", [])):
            by_pt[(round(pt[0], 4), round(pt[1], 4))].append(i)
    for pt, idxs in by_pt.items():
        for i in range(1, len(idxs)):
            a, b = idxs[0], idxs[i]
            ea, eb = ecs[a], ecs[b]
            via_a = any(round(v[0], 4) == pt[0] and round(v[1], 4) == pt[1] for v in ea.get("tv", []))
            via_b = any(round(v[0], 4) == pt[0] and round(v[1], 4) == pt[1] for v in eb.get("tv", []))
            if ea["layer"] == eb["layer"] or (via_a and via_b) or (plated_union and plated_at(pt)):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb
    comp = defaultdict(list)
    for i in range(len(ecs)):
        comp[find(i)].append(i)
    return comp

pre = components(False); post = components(True)
assert len(pre) == 2 and ana["n_components"] == 2, "修复前 2 分量断言失败"
assert len(post) == 1, "修复后 1 分量断言失败"
pv = json.load(open("<ENGINE_ROOT>/out/v5-p5/r1/ed2-diagnosis/pth-fix-preverify.json", encoding="utf-8"))
p3 = [x for x in pv["multi_nets"] if x["net"] == "+3V3"][0]
assert p3["before"] == 2 and p3["after"] == 1 and p3["n_entries"] == 18, "preverify +3V3 2→1 断言失败"
v3 = pv["v3"]
assert v3 == {"before": 2, "after": 1}

pre_comp_of = {}
for cid, idxs in pre.items():
    for i in idxs:
        pre_comp_of[i] = cid

fig = plt.figure(figsize=(13.4, 7.8))
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.22)

# 左：+3V3 物理布线图（18 段按层着色、过孔、割点高亮）
ax = fig.add_subplot(gs[0])
for i, e in enumerate(ecs):
    (x1, y1), (x2, y2) = e["first"], e["last"]
    comp = pre_comp_of[i]
    col = C_F if e["layer"] == "F.Cu" else C_B
    ls = "-" if comp == pre_comp_of[0] else "--"
    ax.plot([x1, x2], [y1, y2], color=col, lw=2.6, ls=ls, alpha=0.9,
            solid_capstyle="round", zorder=3)
    for v in e.get("tv", []):
        ax.add_patch(Circle(v, 0.32, fc="white", ec=col, lw=1.6, zorder=4))
        ax.plot([v[0]], [v[1]], marker="+", color=col, markersize=6, zorder=5)
pad_pts = {(round(j["pt"][0], 3), round(j["pt"][1], 3)) for j in ana["joints"] if j["is_pad"]}
for (x, y) in pad_pts:
    ax.add_patch(Rectangle((x - 0.62, y - 0.62), 1.24, 1.24, fc="#e8e8e8", ec="#555555", lw=1.1, zorder=2))
ax.add_patch(Circle(cut, 1.9, fc="none", ec=C_RED, lw=3.0, zorder=6))
ax.annotate("割点 [168.8156, 69.273]\n板件直读：drill_mm=1.0，plated=true\n（1.0mm 电镀孔筒，连通 B.Cu/F.Cu 两层）",
            xy=(cut[0], cut[1]), xytext=(169.6, 71.9), fontsize=9.4, color="#8a2f33", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_RED, lw=2.0),
            bbox=dict(fc="#fdf0ee", ec=C_RED, boxstyle="round,pad=0.35"))
ax.set_title("pmod-crypto 网 +3V3 末轮候选布线（18 段；实线=分量A、虚线=分量B）", fontsize=11.5)
ax.set_xlabel("X（mm）", fontsize=10); ax.set_ylabel("Y（mm）", fontsize=10)
ax.set_aspect("equal"); ax.grid(ls=":", alpha=0.4)
ax.legend(handles=[plt.Line2D([], [], color=C_F, lw=3, label="F.Cu 段"),
                   plt.Line2D([], [], color=C_B, lw=3, label="B.Cu 段"),
                   plt.Line2D([], [], color="#555555", marker="+", ls="", label="过渡孔（tv）"),
                   plt.Line2D([], [], color=C_RED, lw=2.5, label="割点（plated 焊盘）")],
          loc="lower right", fontsize=8.6)

# 右：修复前后分量示意
ax2 = fig.add_subplot(gs[1])
ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
ax2.text(5, 9.55, "修复前（route_check 0.4.0）", ha="center", fontsize=11.5, fontweight="bold", color="#8a2f33")
ax2.text(1.55, 7.9, "分量B\n(B.Cu 侧)", ha="center", fontsize=9.2, color="#96522e")
ax2.add_patch(Circle((3.1, 7.6), 0.85, fc="#fbe3d3", ec=C_B, lw=2.2))
ax2.plot([1.0, 2.35], [7.6, 7.6], color=C_B, lw=3)
ax2.plot([3.85, 5.0], [7.6, 7.6], color=C_B, lw=3)
ax2.text(5.35, 7.9, "×\n孔筒层间连通\n未建模", ha="left", fontsize=8.6, color=C_RED, fontweight="bold")
ax2.plot([5.0, 6.3], [7.6, 7.0], color=C_RED, lw=2, ls="--")
ax2.add_patch(Circle((3.1, 7.6), 0.36, fc="white", ec=C_B, lw=1.6))
ax2.text(8.7, 7.9, "分量A\n(F.Cu 侧)", ha="center", fontsize=9.2, color="#33517a")
ax2.plot([6.6, 9.2], [6.85, 6.85], color=C_F, lw=3)
ax2.plot([7.0, 7.0], [6.85, 5.6], color=C_F, lw=3)
ax2.plot([7.0, 8.9], [5.6, 5.6], color=C_F, lw=3)
ax2.text(5, 4.8, "并查复算（脚本重演，与机器件逐位一致）：分量 2 = n_components", ha="center", fontsize=9, color="#8a2f33")
ax2.annotate("", xy=(5, 4.15), xytext=(5, 4.55), arrowprops=dict(arrowstyle="-|>", color=C_GREEN, lw=2.4))
ax2.text(5, 3.6, "修复后（route_check 0.4.1）", ha="center", fontsize=11.5, fontweight="bold", color="#2f6b3f")
ax2.add_patch(Circle((5, 2.3), 0.95, fc="#dcefe1", ec=C_GREEN, lw=2.6))
ax2.add_patch(Circle((5, 2.3), 0.4, fc="white", ec=C_GREEN, lw=1.8))
ax2.text(5, 1.7, "plated hole 全信号层 union\n→ 1 分量（电气连通，真 SAT 放行）", ha="center", fontsize=9.2, color="#2f6b3f", fontweight="bold")
ax2.text(5, 0.62, "pth-fix-preverify.json：v3 {before:2, after:1}；multi_nets 四网\n+3V3 2→1 · /SCL 2→1 · /SDA 1→1 · GND 1→1",
         ha="center", fontsize=8.2, color="#444444",
         bbox=dict(fc="#f4f9f5", ec=C_GREEN, boxstyle="round,pad=0.3"))

fig.suptitle("篇四图 4　plated-union 割点：route_check ③ 未建模 PTH 孔筒层间连通，出口击落真 SAT（误杀翻案证据链）",
             fontsize=14, fontweight="bold", y=0.99)
fig.text(0.5, 0.012,
         "数据源：crypto-ed2-analysis.json（18 entries/joints，割点 joints[connected=false] 唯一=[168.8156,69.273]）；"
         "pmod-crypto/board.json（holes 直读：drill_mm=1.0、plated=true，程序化定位断言）；pth-fix-preverify.json（分量 2→1）。\n"
         "并查复算=脚本内重演（同层共点/过渡孔共点/修复后 plated 焊盘共点三种并查口径），修复前 2 分量、加 plated union 后 1 分量，与两机器件逐位一致。"
         "修复=route_check 0.4.0→0.4.1；重判 3/3 全中（crypto/badgeleds/thin-pod 全 ROUTED）。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-04-PLATED-UNION-CUTPOINT.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-04 生成：%s（%d B）割点孔径+并查复算 2→1+preverify 三重断言全过" % (out, os.path.getsize(out)))
