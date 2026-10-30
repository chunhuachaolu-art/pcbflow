# -*- coding: utf-8 -*-
"""
FIG-P4-03-TMP108-ENDPOINT-ABSTRACTION — 篇四图 3 tmp108 旧（2 端）/新（4 端）端点对照

数据件（全部机器件直读，禁硬编码坐标）：
  - 旧世界（R1 换版前）：<ENGINE_ROOT>/out/v5-p5/boards-pre-r1/tmp108/board.json（board.partitions[PT-A0]）
  - 新世界（R1）：<ENGINE_ROOT>/out/v5-p5/boards/tmp108/board.json（同键）
  - 密封复算读数：<DATA_ROOT>/.zcode/dev-experience/state/partition-judge.md L242（正交邻 0.235mm／对角走廊 0.442mm vs R5=0.5mm）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-03-TMP108-ENDPOINT-ABSTRACTION.png
"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_F = "#4c72b0"; C_B = "#dd8452"; C_RED = "#c44e52"; C_GREEN = "#55a868"; C_GRAY = "#8c8c8c"

def load_pt(path):
    d = json.load(open(path, encoding="utf-8"))
    pt = [q for q in d["board"]["partitions"] if q["partition_id"] == "PT-A0"]
    assert len(pt) == 1, "PT-A0 未唯一定位"
    return pt[0]

old = load_pt("<ENGINE_ROOT>/out/v5-p5/boards-pre-r1/tmp108/board.json")
new = load_pt("<ENGINE_ROOT>/out/v5-p5/boards/tmp108/board.json")

oe = old["geometry"]["endpoints"]; otp = old["geometry"]["pad_terminals"]
ne = new["geometry"]["endpoints"]; ntp = new["geometry"]["pad_terminals"]
assert len(oe) == 2 and len(ne) == 4, "旧 2 端/新 4 端断言失败"
assert "abstracted to 2 endpoints" in old["note"] and "4 terminal nodes" in new["note"], "note 措辞断言失败"
ep1 = [t for t in ntp if t["endpoint"] == 1][0]
assert ep1["shape"] == "circle" and abs(ep1["size_mm"][0] - 0.265) < 1e-9, "ep1 ⌀0.265 circle 断言失败"
assert abs(ne[1][0] - 139.196) < 1e-9 and abs(ne[1][1] - 114.046) < 1e-6, "ep1=(139.196,114.046) 断言失败"
assert not any(abs(x[0] - ne[1][0]) < 1e-6 and abs(x[1] - ne[1][1]) < 1e-6 for x in oe), "ep1 应在旧世界缺席"
assert abs(oe[0][0] - 137.16) < 1e-9 and abs(oe[1][0] - 145.158517) < 1e-6, "旧端点坐标断言失败"

# 密封复算读数（读数件直读）
pj = open("<DATA_ROOT>/.zcode/dev-experience/state/partition-judge.md", encoding="utf-8").read().split("\n")
L242 = pj[241]
mv = re.search(r"正交邻\s*([0-9.]+)mm/对角走廊\s*([0-9.]+)mm\s*vs\s*R5=([0-9.]+)mm", L242)
assert mv, "partition-judge L242 密封复算读数未命中"
d_orth, d_diag, r5 = float(mv.group(1)), float(mv.group(2)), float(mv.group(3))
assert (d_orth, d_diag, r5) == (0.235, 0.442, 0.5), "密封复算三值断言失败"

XMIN, XMAX, YMIN, YMAX = 135.9, 146.6, 113.0, 115.7

def draw_pads(ax, eps, tps, ghost_idx=()):
    for t in tps:
        x, y = eps[t["endpoint"]]
        ghost = t["endpoint"] in ghost_idx
        if t["shape"] == "rect":
            w, h = t["size_mm"]
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h,
                         fc=("none" if ghost else (C_F if "F.Cu" in t["layers"] else C_B)),
                         ec=(C_GRAY if ghost else "#222222"), lw=1.6, ls=("--" if ghost else "-"), zorder=3))
        else:
            r = t["size_mm"][0] / 2
            ax.add_patch(Circle((x, y), r, fc=("none" if ghost else C_F),
                         ec=(C_GRAY if ghost else "#222222"), lw=1.6, ls=("--" if ghost else "-"), zorder=3))
        ax.text(x, y - 0.32, "ep%d" % t["endpoint"], ha="center", fontsize=8.4, zorder=4,
                color=("#888888" if ghost else "#222222"))
        ax.text(x, y + 0.30, "%s %s×%s" % (t["layers"][0], *(t["size_mm"] if t["shape"] == "rect" else (t["size_mm"][0], "φ"))),
                ha="center", fontsize=7.2, zorder=4, color="#444444")

fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.6))

ax = axes[0]
draw_pads(ax, ne, ntp, ghost_idx=(1, 3))
ax.plot([oe[0][0], oe[1][0]], [oe[0][1], oe[1][1]], color=C_B, lw=2.6, alpha=0.85, zorder=2)
ax.text((oe[0][0] + oe[1][0]) / 2, (oe[0][1] + oe[1][1]) / 2 + 0.14,
        "旧世界唯一抽象边（2 端直连）", ha="center", fontsize=8.8, color="#96522e")
c = Circle(ne[1], 0.5, fc="none", ec=C_RED, lw=2.0, ls=":", zorder=5)
ax.add_patch(c)
ax.annotate("ep1=(139.196, 114.046)\ncircle φ0.265（F.Cu）\n在旧世界 endpoints 完全缺席",
            xy=(ne[1][0], ne[1][1]), xytext=(139.9, 114.62), fontsize=9.2, color="#8a2f33",
            arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.8), fontweight="bold")
ax.text(139.196, 113.42, "R5=0.5 间隙环（虚线圆）", ha="center", fontsize=8, color=C_RED)
ax.set_title("旧世界（R1 换版前）：2 端抽象\nnote=\"%s\"" % old["note"], fontsize=11.5)

ax = axes[1]
draw_pads(ax, ne, ntp)
ax.plot([ne[i][0] for i in (0, 1)], [ne[i][1] for i in (0, 1)], color=C_F, lw=2.2, alpha=0.8, zorder=2)
ax.plot([ne[i][0] for i in (2, 3)], [ne[i][1] for i in (2, 3)], color=C_B, lw=2.2, alpha=0.8, zorder=2)
ax.plot([ne[i][0] for i in (1, 2)], [ne[i][1] for i in (1, 2)], color=C_GREEN, lw=1.4, ls="--", zorder=2)
ax.add_patch(Circle(ne[1], 0.5, fc="none", ec=C_RED, lw=2.0, ls=":", zorder=5))
ax.annotate("密封复算（主审独立坐实）：\n正交邻 %.3fmm ／ 对角走廊 %.3fmm\n均 ＜ R5=%.1fmm → (c) 规则带值\n（真实细规则可逃逸、板非人不可布）" % (d_orth, d_diag, r5),
            xy=(ne[1][0], ne[1][1] - 0.5), xytext=(140.1, 113.18), fontsize=9.2, color="#33517a",
            arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.8),
            bbox=dict(fc="#eef2fa", ec=C_RED, boxstyle="round,pad=0.35"), fontweight="bold")
ax.set_title("新世界（R1）：4 端显式拓扑\nnote=\"%s\"" % new["note"], fontsize=11.5)

for ax in axes:
    ax.set_xlim(XMIN, XMAX); ax.set_ylim(YMIN, YMAX); ax.set_aspect("equal")
    ax.set_xlabel("X（mm）", fontsize=10); ax.set_ylabel("Y（mm）", fontsize=10)
    ax.grid(ls=":", alpha=0.4)
    ax.add_patch(Rectangle((0.993, 0.02), 0.006, 0.1, transform=ax.transAxes, fc="none"))

fig.suptitle("篇四图 3　tmp108 A0 网（密封环）端点抽象：旧 2 端 vs 新 4 端对照（(c) 规则带值·换版端点盲区）",
             fontsize=14, fontweight="bold", y=0.99)
fig.text(0.5, 0.015,
         "数据源：旧=out/v5-p5/boards-pre-r1/tmp108/board.json、新=out/v5-p5/boards/tmp108/board.json（board.partitions[PT-A0].geometry，坐标/形状/尺寸板件直读）；"
         "密封复算读数=state/partition-judge.md L242（正则直读，0.235/0.442/0.5 三值断言过）。\n"
         "时序注：完整跑首败网=GND 而非 HALT 预断的 A0（彼时截断件；A0 密封证据独立成立，勘误如实入档 partition-judge.md L261）。"
         "R7 netclass-edge 挂账、DR-2 判据域扩容截至 2026-10-03 待用户裁（不代裁）。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-03-TMP108-ENDPOINT-ABSTRACTION.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-03 生成：%s（%d B）旧2/新4端+ep1 缺席+⌀0.265+密封三值断言全过" % (out, os.path.getsize(out)))
