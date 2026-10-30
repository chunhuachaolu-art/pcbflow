# -*- coding: utf-8 -*-
"""
FIG-P4-05-ESP32-GAPFACE — 篇四图 5 esp32 (b) 缺口面（候选图：rip-up 阻塞集选择／联合重解深度）

数据件（全部机器件直读，禁硬编码）：
  - <ENGINE_ROOT>/out/v5-p5/boardintake-r1/a1/esp32-devkit-lipo-rev-c.json
    （verdict.class=(b)、witness.class_removal_unlock 六类、blocker_census.route_blocker_nets、channel_scan）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-05-ESP32-GAPFACE.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_GREEN = "#55a868"; C_RED = "#c44e52"; C_GRAY = "#8c8c8c"

d = json.load(open("<ENGINE_ROOT>/out/v5-p5/boardintake-r1/a1/esp32-devkit-lipo-rev-c.json", encoding="utf-8"))
v = d["verdict"]
assert v["class"] == "(b) 引擎能力缺口" and v["removal_unlock_classes"] == ["all-geometric", "fixed", "routes"], "(b) 三解锁类断言失败"
assert v["width_unlock_mm"] == [], "(c) 宽度解锁面应为空"
cru = d["witness"]["class_removal_unlock"]
cls6 = {r["class"]: r for r in cru}
assert set(cls6) == {"routes", "vias", "holes", "edge", "fixed", "all-geometric"} and len(cru) == 6, "六类断言失败"
assert cls6["routes"]["unlocked"] is True and cls6["fixed"]["unlocked"] is True and cls6["all-geometric"]["unlocked"] is True
assert not any(cls6[k]["unlocked"] for k in ("vias", "holes", "edge")), "三类仍锁断言失败"
bc = d["witness"]["blocker_census"]
rbn = bc["route_blocker_nets"]
assert set(bc["engine_ripup_blocker_set"]) == set(rbn) and len(rbn) == 5, "5 阻塞网断言失败"
assert all(x["min_d_direct"] == 0.0 for x in rbn.values()), "min_d_direct=0 断言失败"
cs = d["witness"]["channel_scan"]
demand = cs["demand_2r5"]
chB, chF = cs["per_layer"]["B.Cu"][0], cs["per_layer"]["F.Cu"][0]
fn = d["failed_net"]
assert fn["net"] == "+5V" and "ripup-reroute-failed" in fn["exhaustion_cause"], "失败网断言失败"
assert abs(demand - 1.0) < 1e-9

fig = plt.figure(figsize=(13.0, 7.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1.0], hspace=0.52, wspace=0.25)

# 左上：六类摘除解锁面
ax = fig.add_subplot(gs[0, 0])
order = ["routes", "vias", "holes", "edge", "fixed", "all-geometric"]
vals = [1 if cls6[k]["unlocked"] else 0 for k in order]
cols = [C_GREEN if x else C_GRAY for x in vals]
bars = ax.barh(range(len(order))[::-1], [1.0] * 6, color=cols, height=0.6, edgecolor="#333333", lw=0.6)
for y, k, x in zip(range(len(order))[::-1], order, vals):
    r = cls6[k]
    ax.text(0.02, y + 0.13, "%s 类摘除→%s" % (k, "解锁" if x else "仍锁"),
            va="center", fontsize=10, color="white" if x else "#333333", fontweight="bold")
    ax.text(0.02, y - 0.20, "attempts=%d · 墙钟 %.1fs" % (r["attempts"], r["wall_s"]), va="center",
            fontsize=7.6, color="white" if x else "#555555")
ax.set_yticks([]); ax.set_xticks([])
ax.set_xlim(0, 1.0); ax.set_ylim(-0.6, 5.6)
ax.set_title("(b) 判据命中：routes 类摘除即解锁\n（引擎自产铜自锁，全程序首个 (b)）", fontsize=11)
for s in ax.spines.values():
    s.set_visible(False)

# 右上：rip-up 阻塞集五网
ax = fig.add_subplot(gs[0, 1])
names = list(rbn.keys())
cop = [rbn[n]["n_coppers"] for n in names]
ax.bar(range(len(names)), cop, color=C_ORANGE, width=0.58, edgecolor="#333333", lw=0.6)
for i, (n, c) in enumerate(zip(names, cop)):
    ax.text(i, c + 0.06, "%d 段已布铜\nmin d=0（压直连段）" % c, ha="center", fontsize=8.2, color="#96522e")
ax.set_xticks(range(len(names)))
ax.set_xticklabels([n.replace("Net-(", "").replace(")", "") for n in names], fontsize=8.4, rotation=12)
ax.set_ylabel("失败区内已布铜段数", fontsize=9.5)
ax.set_ylim(0, max(cop) + 0.75)
ax.set_title("rip-up 阻塞集（engine_ripup_blocker_set，5 网）\n失败网 +5V：ripup-reroute-failed（被 rip 网重布失败）", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", ls=":", alpha=0.4)

# 左下：通道
ax = fig.add_subplot(gs[1, 0])
lays = ["F.Cu", "B.Cu"]; chs = [chF, chB]
ax.bar([0, 1], chs, color=[C_BLUE, C_ORANGE], width=0.5, edgecolor="#333333", lw=0.6)
ax.axhline(demand, color=C_RED, lw=2.0, ls="--")
ax.text(1.42, demand, "需求 1.0mm", color=C_RED, fontsize=9.5, ha="right", va="bottom", fontweight="bold")
for i, c in enumerate(chs):
    ax.text(i, c + 0.05, "%.3f mm" % c, ha="center", fontsize=9.6, fontweight="bold")
ax.set_xticks([0, 1]); ax.set_xticklabels(["F.Cu", "B.Cu"])
ax.set_ylim(0, max(chs) + 0.35)
ax.set_ylabel("最窄通道（mm）", fontsize=9.5)
ax.set_title("直连走廊通道（41 采样点口径）：F.Cu 不足、B.Cu 贴限\n（通道非 (b) 主证据；摘除面才是）", fontsize=10.5)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", ls=":", alpha=0.4)

# 右下：缺口面文字框
ax = fig.add_subplot(gs[1, 1]); ax.axis("off")
ax.text(0.5, 0.86, "(b) 缺口面（机器件原文摘录）", ha="center", fontsize=11.5, fontweight="bold")
ax.text(0.5, 0.50, v["note"], ha="center", va="center", fontsize=10.2, color="#8a2f33", linespacing=1.9,
        bbox=dict(fc="#fdf0ee", ec=C_RED, boxstyle="round,pad=0.5"))
ax.text(0.5, 0.10, "R2 扫描（合成 9 格＋esp32 3 格双轴）零敏感后，\n缺口定位收窄至候选生成面→R1 对位（partition-judge.md L234-235）",
        ha="center", va="center", fontsize=8.8, color="#555555", linespacing=1.8)

fig.suptitle("篇四图 5　esp32 (b) 缺口面：rip-up 阻塞集选择／联合重解深度（候选图）",
             fontsize=14, fontweight="bold", y=0.995)
fig.text(0.5, 0.010,
         "数据源：out/v5-p5/boardintake-r1/a1/esp32-devkit-lipo-rev-c.json（verdict/class_removal_unlock/blocker_census/channel_scan 直读；"
         "工具=v5.diag_inherent/1.0.0，重放 faithful_basis=byte-equal）。\n"
         "BOARDINTAKE-R1（2026-09-24）：esp32 FAILED 434s（24 候选 tried 4）；候选图（画否随批呈裁，任务书 §5）。"
         "(b) 全程序仅 1 例，缺口面刻画基于单例（正文 §10 局限 7 如实披露）。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-05-ESP32-GAPFACE.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-05 生成：%s（%d B）(b) 六类摘除+5 阻塞网+通道断言全过" % (out, os.path.getsize(out)))
