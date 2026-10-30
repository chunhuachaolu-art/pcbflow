# -*- coding: utf-8 -*-
"""
篇三 图⑦：SV1 候选集=恰 6 唯一拓扑示意（2–31 端点 partition→quantize(1e-6) 去重→
L 两朝向＋Z 形走廊平移；去重前 10 组合中 4 组逐位相同路径）。

数据来源（直读机器件）：
  - <ENGINE_ROOT>/out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md
      §1 实现注 1/2（L27–28）：「板文件 partition 端点数 2-31 不等…端点 quantize(1e-6)
      去重后按 (x,y) 字典序成链、相邻对 L 形（基线恒先 x 后 y）」；
      「候选集 = 6 个唯一拓扑（任务书上界 ≤10）：『两朝向 × x/y 各 ±1』的 10 个组合中
      4 个与其它组合产生逐位相同路径，按去重集实现：L-XF / L-YF / ZX± / ZY±
      （Z 形=对应走廊线平移 1 格点=0.5mm，canvas lattice 先例）」
  - sv1-results.json（同目录 out/sv1-results.json，sha 锚同图⑥）三板板名互证
断言：6 拓扑名/端点数域 2-31/quantize(1e-6)/0.5mm 格点/10 组合去重 4 逐位相同——
  全部在 VERDICT 原文程序化命中；输出存在且 >10KB。
图注口径：结构示意（拓扑骨架画法＝端点 S/E＋格点网，非板件坐标渲染）。
"""
import hashlib
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.lines import Line2D

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

VERDICT = "<ENGINE_ROOT>/out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md"
SV1J = "<ENGINE_ROOT>/out/hier-route-r1/solver/out/sv1-results.json"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P3-07-SV1-SIX-UNIQUE-TOPOLOGIES.png"

vt = open(VERDICT, encoding="utf-8").read()
for kw in ["端点数 2-31", "quantize(1e-6)", "6 个唯一拓扑", "两朝向 × x/y 各 ±1",
           "L-XF / L-YF / ZX± / ZY±", "0.5mm", "4 个与其它组合产生逐位相同路径",
           "字典序成链", "相邻对 L 形"]:
    assert kw in vt, f"VERDICT 缺锚词: {kw}"

sv = json.load(open(SV1J, encoding="utf-8"))
sha = hashlib.sha256(open(SV1J, "rb").read()).hexdigest()
assert sha.startswith("b18059a2f32c3ba8"), "sv1-results.json sha 锚重算失败"
boards = [sv["boards"][k]["board_id"] for k in ("HR1-BOARD-A", "HR1-BOARD-B", "HR1-BOARD-C")]
assert boards == ["thatmicpre-v2", "pmod-crypto", "badgeleds-do-electronics"]

# ---- 六拓扑骨架（格点单位；Z 形=走廊线平移 1 格点）----
S, E = (0, 0), (6, 4)
MIDX, MIDY = 3, 2
topo = {
    "L-XF（先 x 后 y，基线）": [(0, 0), (6, 0), (6, 4)],
    "L-YF（先 y 后 x）": [(0, 0), (0, 4), (6, 4)],
    "ZX+（走廊 x 向 +1 格点）": [(0, 0), (4, 0), (4, 4), (6, 4)],
    "ZX−（走廊 x 向 −1 格点）": [(0, 0), (2, 0), (2, 4), (6, 4)],
    "ZY+（走廊 y 向 +1 格点）": [(0, 0), (0, 3), (6, 3), (6, 4)],
    "ZY−（走廊 y 向 −1 格点）": [(0, 0), (0, 1), (6, 1), (6, 4)],
}

fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.0), dpi=300)
for ax, (name, pts) in zip(axes.flat, topo.items()):
    # 格点网（1 格点=0.5mm）
    for gx in range(-1, 8):
        for gy in range(-1, 6):
            ax.plot(gx, gy, marker=".", color="#D5DBDB", markersize=4, zorder=1)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, "-", color="#1A5276", lw=3.4, zorder=3,
            solid_capstyle="round", solid_joinstyle="round")
    ax.plot(*S, "o", color="#C0392B", markersize=13, zorder=4)
    ax.plot(*E, "s", color="#1E8449", markersize=12, zorder=4)
    ax.annotate("S 端点", S, textcoords="offset points", xytext=(-8, -16), fontsize=10, color="#C0392B")
    ax.annotate("E 端点", E, textcoords="offset points", xytext=(-10, 10), fontsize=10, color="#1E8449")
    # 中段平移标注（Z 形）
    if name.startswith("Z"):
        if "ZX" in name:
            ax.annotate("中间走廊段\nx 平移 ±1 格点", (pts[1][0], MIDY), textcoords="offset points",
                        xytext=(10, -34), fontsize=9, color="#7D3C98")
        else:
            ax.annotate("中间走廊段\ny 平移 ±1 格点", (MIDX, pts[1][1]), textcoords="offset points",
                        xytext=(-64, 12), fontsize=9, color="#7D3C98")
    ax.set_xlim(-1.5, 7.5)
    ax.set_ylim(-1.5, 5.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(name, fontsize=12.5, fontweight="bold")
    for sp in ax.spines.values():
        sp.set_color("#AEB6BF")

fig.suptitle("SV1 候选集＝恰 6 唯一拓扑（结构示意）：2–31 端点 partition → quantize(1e-6) 去重 → 相邻端点对 L/Z 链化\n"
             "「两朝向 × x/y 各 ±1」10 组合中 4 个与其它组合逐位相同路径 → 去重集 L-XF／L-YF／ZX±／ZY±（Z 形=走廊线平移 1 格点=0.5mm）",
             fontsize=14, fontweight="bold", y=0.99)
fig.text(0.5, 0.015,
         f"语义源：out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md §1 实现注 1/2（程序化锚词断言）｜读数件 sv1-results.json sha16={sha[:16]}（重算一致）｜输入三板={'/'.join(boards)}",
         ha="center", fontsize=9.5, color="#566573")
fig.tight_layout(rect=[0, 0.03, 1, 0.92])
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
print(f"OK FIG-P3-07 六唯一拓扑示意 {OUT} {size} bytes")
