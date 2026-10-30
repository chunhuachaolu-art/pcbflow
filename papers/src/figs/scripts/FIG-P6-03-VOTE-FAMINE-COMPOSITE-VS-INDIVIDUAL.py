# -*- coding: utf-8 -*-
"""
FIG-P6-03 — P6 图 3：票荒对照（动作级多数票在生成域丢解：合票通道 vs 三席个体重放）
数据源（机器件直读）：
  1. out/canvas-toolchain/act-m3/diag-seat-replay.json —— m3 修整批 15 席位批×2 板轮始态独立重放
     （个体可达最优：badgeleds 8/9、bme280 10/13）
  2. out/canvas-toolchain/act-m3/ledger-{badgeleds,bme280}.jsonl —— 合票（多数票合成）通道
     R2–R5 补连轮 accepted route 动作数（=0：几何零重合→合成通道零补连落地）
  3. out/canvas-toolchain/act-m2r2/stats/stats-products.json m2_comparison —— m2 冷启动整板
     三板合票终态连通（0/9、1/13、3/16，含 ledger_sha256 锚）
  4. out/canvas-toolchain/act-m2/ledger-*.jsonl —— m2_comparison 的 ledger sha256 程序化重算比对
  5. out/canvas-toolchain/act-m2/diag-seat-replay-*.json —— m2 三板个体重放最优
断言：m3 重放记录 15×2、两板个体最优=8/9 与 10/13；m3 补连轮（R2–R5）合票 route 落地=0；
  m2 合票=(0,1,3) 对 (9,13,16)；m2 个体最优=(5,2,8)；三件 ledger sha 重算一致；输出>10KB。
"""
import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
CT = os.path.join(REPO, "out/canvas-toolchain")
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-03-VOTE-FAMINE-COMPOSITE-VS-INDIVIDUAL.png")

BOARDS = ["badgeleds-do-electronics", "pmod-bme280", "pmod-crypto"]
SHORT = {"badgeleds-do-electronics": "badgeleds\n(9 网)", "pmod-bme280": "bme280\n(13 网)",
         "pmod-crypto": "crypto\n(16 网)"}

# ---- 取数 1：m3 个体重放 + 合票通道 ----
m3 = json.load(open(os.path.join(CT, "act-m3/diag-seat-replay.json"), encoding="utf-8"))
m3_conn, m3_max, m3_den = {}, {}, {}
for b, rows in m3.items():
    conns = [int(r["conn"].split("/")[0]) for r in rows]
    m3_conn[b] = conns
    m3_max[b] = max(conns)
    m3_den[b] = int(rows[0]["conn"].split("/")[1])
assert len(m3) == 2 and all(len(v) == 15 for v in m3_conn.values()), "m3 重放记录数异常"
assert m3_max["badgeleds-do-electronics"] == 8 and m3_den["badgeleds-do-electronics"] == 9
assert m3_max["pmod-bme280"] == 10 and m3_den["pmod-bme280"] == 13

comp_routes = {}
for b in ["badgeleds-do-electronics", "pmod-bme280"]:
    n = 0
    for line in open(os.path.join(CT, f"act-m3/ledger-{b}.jsonl"), encoding="utf-8"):
        d = json.loads(line)
        if d["round"] >= 2:  # R2–R5 = 补连（生成域）轮；R1 为收敛式修整轮
            n += sum(1 for a in (d.get("accepted") or []) if a.get("action") == "route")
    comp_routes[b] = n
assert all(v == 0 for v in comp_routes.values()), f"m3 补连轮合票 route 落地 {comp_routes} != 0"

# ---- 取数 2：m2 合票 vs 个体 ----
stats = json.load(open(os.path.join(CT, "act-m2r2/stats/stats-products.json"), encoding="utf-8"))
m2c = stats["m2_comparison"]
m2_comp = {b: m2c[b]["connectivity_true"] for b in BOARDS}
m2_den = {b: m2c[b]["connectivity_total"] for b in BOARDS}
assert [m2_comp[b] for b in BOARDS] == [0, 1, 3] and [m2_den[b] for b in BOARDS] == [9, 13, 16]
m2_ind = {}
for b in BOARDS:
    rows = json.load(open(os.path.join(CT, f"act-m2/diag-seat-replay-{b}.json"), encoding="utf-8"))
    m2_ind[b] = max(r["connectivity_true"] for r in rows)
    h = hashlib.sha256(open(os.path.join(CT, f"act-m2/ledger-{b}.jsonl"), "rb").read()).hexdigest()
    assert h == m2c[b]["ledger_sha256"], f"{b} m2 ledger sha 重算不一致"
assert [m2_ind[b] for b in BOARDS] == [5, 2, 8], [m2_ind[b] for b in BOARDS]

print(f"[read] m3 个体重放最优：badgeleds {m3_max['badgeleds-do-electronics']}/9、"
      f"bme280 {m3_max['pmod-bme280']}/13；合票通道 R2–R5 补连 route 落地={comp_routes}")
print(f"[read] m2 合票={[m2_comp[b] for b in BOARDS]} vs 个体={[m2_ind[b] for b in BOARDS]}"
      f"（分母 {[m2_den[b] for b in BOARDS]}；三件 m2 ledger sha256 重算一致）")

# ---- 绘图 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.6, 5.8), dpi=300,
                               gridspec_kw={"width_ratios": [1.05, 1.35]})

# 左：m2 冷启动整板生成——合票 vs 个体最优（分组柱）
x = np.arange(3)
w = 0.36
ax1.bar(x - w / 2, [m2_comp[b] for b in BOARDS], w, color="#c44e52", label="合票通道（多数票合成终态）")
ax1.bar(x + w / 2, [m2_ind[b] for b in BOARDS], w, color="#55a868", label="三席个体重放最优")
for i, b in enumerate(BOARDS):
    ax1.text(x[i] - w / 2, m2_comp[b] + 0.15, f"{m2_comp[b]}/{m2_den[b]}", ha="center",
             fontsize=10, color="#c44e52", fontweight="bold")
    ax1.text(x[i] + w / 2, m2_ind[b] + 0.15, f"{m2_ind[b]}/{m2_den[b]}", ha="center",
             fontsize=10, color="#2c5e33", fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels([SHORT[b] for b in BOARDS], fontsize=10)
ax1.set_ylabel("连通网数", fontsize=10.5)
ax1.set_ylim(0, 10.8)
ax1.set_title("m2 冷启动整板生成：合票通道丢解", fontsize=12, fontweight="bold")
ax1.legend(fontsize=9, loc="upper left")
ax1.grid(alpha=0.3, axis="y")

# 右：m3 修整批 R1–R5 逐席位批个体重放分布（点带）+ 个体最优标注
order = ["badgeleds-do-electronics", "pmod-bme280"]
colors = {"badgeleds-do-electronics": "#4c72b0", "pmod-bme280": "#dd8452"}
for k, b in enumerate(order):
    rows = m3[b]
    rounds = sorted({r["seat"].split("-")[0] for r in rows})
    for r in rows:
        rn = r["seat"].split("-")[0]
        xi = rounds.index(rn) + (k - 0.5) * 0.32
        yv = int(r["conn"].split("/")[0])
        ax2.scatter(xi, yv, s=46, color=colors[b], alpha=0.75, edgecolors="white", lw=0.6, zorder=3)
    best_round = max(rows, key=lambda r: int(r["conn"].split("/")[0]))
    ax2.annotate(f"个体最优 {m3_max[b]}/{m3_den[b]}（{best_round['seat']}）",
                 xy=(rounds.index(best_round["seat"].split("-")[0]) + (k - 0.5) * 0.32, m3_max[b]),
                 xytext=(rounds.index(best_round["seat"].split("-")[0]) + (k - 0.5) * 0.32 - 0.55,
                         m3_max[b] + 1.05),
                 fontsize=8.8, color=colors[b], fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=colors[b], lw=0.9))
ax2.axhspan(-0.5, 0.5, color="#c44e52", alpha=0.12)
ax2.text(4.28, 0.28, "← 合票通道补连轮（R2–R5）route 落地 0：三席几何零重合",
         fontsize=8.8, color="#8a3030", ha="right", va="center")
ax2.set_xticks(range(5))
ax2.set_xticklabels([f"R{i}" for i in range(1, 6)], fontsize=10)
ax2.set_xlabel("m3 修整批轮次（R1=收敛式修整·三席整批 canonical 全同；R2–R5=补连生成域）", fontsize=10)
ax2.set_ylabel("个体重放连通网数（轮始态独立重放）", fontsize=10.5)
ax2.set_title("m3 修整批：席位个体能力足够，票合通道丢解", fontsize=12, fontweight="bold")
ax2.set_ylim(-1.2, 12.5)
ax2.grid(alpha=0.3, axis="y")
handles = [plt.Line2D([], [], marker="o", ls="", color=colors[b], label=SHORT[b].replace("\n", " "))
           for b in order]
ax2.legend(handles=handles, fontsize=9, loc="upper left")

fig.suptitle("票荒对照：动作级多数票仅收敛域成立，生成域合票 0 而个体可达 8/9、10/13",
             fontsize=13.5, fontweight="bold", y=1.02)
fig.text(0.5, -0.048,
         "图注：左=act-m2 冷启动整板生成（合票终态取 act-m2r2/stats m2_comparison，ledger sha256 三件程序化重算一致；"
         "个体最优取 act-m2/diag-seat-replay-*）。右=act-m3 修整批 15 席位批/板轮始态独立重放（diag-seat-replay.json）；"
         "R2–R5 合票通道 accepted route=0（ledger-*.jsonl 程序计数）。处置立规：冷启动整板生成禁用动作级多数票（正文 §4.1）。",
         ha="center", fontsize=8.2, color="#444444")
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
print(f"[ok] {OUT} ({sz} B)")
