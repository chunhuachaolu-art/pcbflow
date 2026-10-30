# -*- coding: utf-8 -*-
"""
篇三 图⑥：SV1 重叠基线三板热图（A/B/C 板冲突段对 256/63/38、冲突网占比 94–100%）。

数据来源（直读机器件）：
  - <ENGINE_ROOT>/out/hier-route-r1/solver/out/sv1-results.json
      键 boards.HR1-BOARD-{A,B,C}.j2（total_conflict_pairs/avg_overlap_per_net/
      conflict_net_ratio/top_conflict_nets）与 .j3（baseline_pairs/after_pairs/reduction_ratio）
sha256 锚（程序化重算断言，锚值=SV1-VERDICT-2026-09-25.md 汇总读数件登记原文）：
  sv1-results.json 全 64 位 = b18059a2f32c3ba810702558ab85895413112891094561e621c72ac65dbfc674
断言：sha 全 64 位逐位一致；三板 total=256/63/38；占比 0.941/1.0/1.0（94–100% 带内）；
  j3 降幅 6.6/14.3/18.4%<30% 门；top1 网均为全局电源大网（GND/+3V3/VCC）；输出 >10KB。
"""
import hashlib
import json
import os

import matplotlib

matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

SRC = "<ENGINE_ROOT>/out/hier-route-r1/solver/out/sv1-results.json"
VERDICT = "<ENGINE_ROOT>/out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P3-06-SV1-THREE-BOARD-OVERLAP-HEATMAP.png"
ANCHOR_SHA = "b18059a2f32c3ba810702558ab85895413112891094561e621c72ac65dbfc674"

sha = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
assert sha == ANCHOR_SHA, f"sv1-results.json sha 重算不一致: {sha}"

# VERDICT 登记原文含同锚（防手抄：三处独立命中）
vt = open(VERDICT, encoding="utf-8").read()
assert sha in vt, "VERDICT 未登记该 sha（锚值来源核验失败）"

d = json.load(open(SRC, encoding="utf-8"))
KEYS = ["HR1-BOARD-A", "HR1-BOARD-B", "HR1-BOARD-C"]
labels, mat, ratios, tops = [], [], [], []
metrics_names = ["总冲突段对", "每网平均重叠段数", "冲突网占比（%）", "最重网冲突数", "J3 消解后冲突段对"]
raw_rows = []
for k in KEYS:
    b = d["boards"][k]
    j2, j3 = b["j2"], b["j3"]
    top1 = j2["top_conflict_nets"][0]
    row = [j2["total_conflict_pairs"], j2["avg_overlap_per_net"], j2["conflict_net_ratio"] * 100,
           top1["conflicts"], j3["after_pairs"]]
    raw_rows.append(row)
    ratios.append((j2["conflict_net_ratio"], j3["reduction_ratio"], top1))

# ---- 断言层 ----
assert [r[0] for r in raw_rows] == [256, 63, 38], f"总冲突段对 {[r[0] for r in raw_rows]}"
assert abs(raw_rows[0][2] - 94.117647) < 0.01 and raw_rows[1][2] == 100.0 and raw_rows[2][2] == 100.0
assert [r[4] for r in raw_rows] == [239, 54, 31], f"J3 消解后 {[r[4] for r in raw_rows]}"
red = [ratios[i][1] for i in range(3)]
assert all(r < 0.30 for r in red), f"J3 降幅超 30% 门: {red}"
assert [t[2]["net"] for t in ratios] == ["GND", "+3V3", "VCC"], "最重网非全局电源大网"
assert [t[2]["conflicts"] for t in ratios] == [122, 32, 17]

labels = [f"{k[-1]} 板 · {d['boards'][k]['board_id']}" for k in KEYS]

# ---- 绘图 ----
fig = plt.figure(figsize=(15.5, 8.4), dpi=300)
ax1 = fig.add_axes([0.06, 0.30, 0.56, 0.58])
ax2 = fig.add_axes([0.70, 0.12, 0.27, 0.74])

arr = np.array(raw_rows, dtype=float)
norm = (arr - arr.min(axis=0)) / (arr.max(axis=0) - arr.min(axis=0) + 1e-12)
im = ax1.imshow(norm, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
ax1.set_xticks(range(5))
ax1.set_xticklabels(metrics_names, fontsize=10.5, rotation=18, ha="right")
ax1.set_yticks(range(3))
ax1.set_yticklabels(labels, fontsize=11)
for i in range(3):
    for j in range(5):
        v = arr[i, j]
        txt = f"{v:.1f}" if j in (1,) else (f"{v:.1f}%" if j == 2 else f"{int(v)}")
        ax1.text(j, i, txt, ha="center", va="center", fontsize=11.5,
                 fontweight="bold", color="#1b2631")
ax1.set_title("A｜三板重叠基线热图（列内归一化着色，格内=机器件原值）", fontsize=12.5, fontweight="bold")

# 面板 B：三板 top-5 冲突网
colors3 = ["#1F618D", "#117A65", "#7D3C98"]
yt = []
ytick = []
ypos = 0
for i, k in enumerate(KEYS):
    tops5 = d["boards"][k]["j2"]["top_conflict_nets"]
    for j, item in enumerate(tops5):
        ax2.barh(ypos, item["conflicts"], height=0.72, color=colors3[i], edgecolor="#1b2631", lw=0.8)
        ax2.text(item["conflicts"] + 1.2, ypos, f"{item['net']} ({item['conflicts']})", va="center", fontsize=8.6)
        ypos -= 1
    ytick.append(ypos + 2.5)
    ypos -= 0.8
ax2.set_yticks(ytick)
ax2.set_yticklabels([f"{k[-1]} 板" for k in KEYS], fontsize=11.5, fontweight="bold")
ax2.invert_yaxis()
ax2.set_xlim(0, 165)
ax2.set_xlabel("冲突段对数（top-5 冲突网）", fontsize=11)
ax2.set_title("B｜每板 top-5 冲突网：最重均 GLOBAL 电源大网\n（A=GND 122／B=+3V3 32／C=VCC 17）",
              fontsize=12, fontweight="bold")

fig.suptitle("SV1 第一竖切·重叠基线首次量化：三板冲突段对 256/63/38、冲突网占比 94–100%（「重叠不是错误而是工作状态」实证）\n"
             f"J3 初消解降幅 {red[0]*100:.1f}/{red[1]*100:.1f}/{red[2]*100:.1f}%＜30% 门（FAIL 0/3，瓶颈=网级整链 6 拓扑候选自由度）；J4 双跑字节等 3/3",
             fontsize=13.5, fontweight="bold", y=0.985)
fig.text(0.5, 0.015, f"数据源：out/hier-route-r1/solver/out/sv1-results.json（sha256 重算逐位一致={sha[:16]}…，锚=SV1-VERDICT-2026-09-25.md 登记）",
         ha="center", fontsize=9.5, color="#566573")
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
print(f"OK FIG-P3-06 三板重叠热图 {OUT} {size} bytes")
print("raw_rows:", raw_rows, "| J3 降幅:", [f"{r:.3f}" for r in red])
