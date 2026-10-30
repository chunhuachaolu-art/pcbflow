# -*- coding: utf-8 -*-
"""
FIG-P4-07-U1-SHIFT-CUT-EXPLOSION — 篇四图 7 U1 西移割数爆炸（750/186,264 vs 基线）＋报废面

数据件（全部机器件直读，禁硬编码）：
  - <WORKSPACE>/tools/pcbflow/out/coreboard-design1/design1-results.json（counts＋live sha）
  - <WORKSPACE>/tools/pcbflow/out/coreboard-design1/rows/classa_RPL-038/039_*u1_shift*.json（4 案 cut/tier/verified/blast）
  - <WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/live2s1-results.json（S1 基线割数 FMC 591/GNDA 301004 交叉锚）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-07-U1-SHIFT-CUT-EXPLOSION.png
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_GREEN = "#55a868"; C_RED = "#c44e52"; C_GRAY = "#8c8c8c"

D1 = "<WORKSPACE>/tools/pcbflow/out/coreboard-design1/design1-results.json"
d1 = json.load(open(D1, encoding="utf-8"))
cnt = d1["counts"]
assert cnt["candidates"] == 29 and cnt["SAT"] == 4 and cnt["UNKNOWN"] == 22 and cnt["UNSAT"] == 3, "29 候选计数断言失败"
assert d1["live_board_sha256"].startswith("dbfea089"), "live sha dbfea089 断言失败"

cases = {}
for p in sorted(glob.glob("<WORKSPACE>/tools/pcbflow/out/coreboard-design1/rows/classa_*u1_shift*.json")):
    r = json.load(open(p, encoding="utf-8"))
    bc = r["board_cert_after_change"]
    br = r["blast_radius"]
    key = (r["net"], r["change"]["label"])
    cases[key] = dict(cut=bc["cut"], tier=bc["tier"], verified=bc["verified"],
                      dx=r["change"]["dx"], nets=len(br["net_list"]), segs=br["segments"], row=r["row_id"],
                      baseline=r["baseline"])
assert len(cases) == 4, "4 西移案断言失败"
assert all(c["tier"] == "UNSAT" and c["verified"] is True for c in cases.values()), "全 UNSAT verified 断言失败"
assert all(c["nets"] == 115 and c["segs"] == 149 for c in cases.values()), "报废面 149 段/115 网断言失败"
assert cases[("FMC_SDNE0", "u1_shift_W_1mm")]["cut"] == 750 and cases[("FMC_SDNE0", "u1_shift_W_2mm")]["cut"] == 750
assert cases[("GNDA", "u1_shift_W_1mm")]["cut"] == 186264 and cases[("GNDA", "u1_shift_W_2mm")]["cut"] == 186264

# S1 基线交叉锚（live2s1 机器件）
l2 = json.load(open("<WORKSPACE>/tools/pcbflow/out/coreboard-live2b-s1/live2s1-results.json", encoding="utf-8"))
base = {r["net"]: r["certificate_cut_count"] for r in l2["rows"]}
assert base["FMC_SDNE0"] == 591 and base["GNDA"] == 301004, "基线 591/301004 断言失败"
for (net, lab), c in cases.items():
    assert "cut=%d" % c["cut"] not in c["baseline"]  # 基线串只含 S1 值
    assert str(base[net]) in c["baseline"], "baseline 串与 live2s1 一致断言失败 %s" % net

fig = plt.figure(figsize=(13.0, 7.4))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.24)

ax = fig.add_subplot(gs[0])
nets = ["FMC_SDNE0", "GNDA"]
confs = ["S1 基线", "西移 1mm", "西移 2mm"]
vals = np.array([[base["FMC_SDNE0"], cases[("FMC_SDNE0", "u1_shift_W_1mm")]["cut"], cases[("FMC_SDNE0", "u1_shift_W_2mm")]["cut"]],
                 [base["GNDA"], cases[("GNDA", "u1_shift_W_1mm")]["cut"], cases[("GNDA", "u1_shift_W_2mm")]["cut"]]])
cols = [C_BLUE, C_ORANGE, C_RED]
x = np.arange(len(nets)); w = 0.24
for j, (conf, col) in enumerate(zip(confs, cols)):
    bars = ax.bar(x + (j - 1) * w, vals[:, j], width=w, color=col, edgecolor="#333333", lw=0.6, label=conf)
    for xi, v in zip(x + (j - 1) * w, vals[:, j]):
        ax.text(xi, v * 1.18, "{:,}".format(int(v)), ha="center", fontsize=9.0, fontweight="bold", color=col)
ax.set_yscale("log"); ax.set_ylim(300, 1.6e6)
ax.set_xticks(x); ax.set_xticklabels(["FMC_SDNE0（FMC 走廊）", "GNDA（口袋墙）"], fontsize=10.5)
ax.set_ylabel("board_cert_after_change 割数（log）", fontsize=10.5)
ax.set_title("U1 西移换版后割数（tier=UNSAT、verified=true，4 案）\n"
             "西移不是解：FMC %.0f→750（×1.27）、GNDA 30万级→186,264（口袋换了形态）" % base["FMC_SDNE0"], fontsize=11.5)
ax.legend(fontsize=9.5, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", ls=":", alpha=0.45)
ax.annotate("", xy=(0.28, 900), xytext=(0.28, 520), arrowprops=dict(arrowstyle="-|>", color=C_RED, lw=1.8))
ax.text(0.34, 780, "×%.2f" % (750 / base["FMC_SDNE0"]), fontsize=9, color=C_RED, fontweight="bold")

# 右：DESIGN-1 全景
ax = fig.add_subplot(gs[1])
dm = d1["decision_matrix"]
kinds = {}
for r in dm:
    kinds.setdefault(r["candidate"], []).append(r)
order = ["pocket_wall_strip", "endpoint_variant", "endpoint_variant_cert", "u1_shift"]
disp = {"pocket_wall_strip": "口袋墙剥除", "endpoint_variant": "端点变体", "endpoint_variant_cert": "端点变体证书", "u1_shift": "U1 西移"}
stat_cols = {"SAT": C_GREEN, "UNKNOWN": C_GRAY, "UNSAT": C_RED}
ypos = list(range(len(order)))[::-1]
for y, k in zip(ypos, order):
    rs = kinds[k]
    seg = 0.0
    for st in ("SAT", "UNKNOWN", "UNSAT"):
        n = sum(1 for r in rs if r["status"] == st)
        if n:
            ax.barh(y, n, left=seg, height=0.55, color=stat_cols[st], edgecolor="#333333", lw=0.6)
            ax.text(seg + n / 2, y, "%d" % n if n > 1 else "", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
            seg += n
    ax.text(seg + 0.25, y, "%s（%d 案）" % (disp[k], len(rs)), va="center", fontsize=9.4)
ax.set_yticks([]); ax.set_xlim(0, 27)
ax.set_xlabel("DESIGN-1 29 候选终态分布（counts：SAT 4／UNKNOWN 22／UNSAT 3）", fontsize=10)
ax.set_title("DESIGN-1 设计级提案全景：\n口袋墙剥除条件 SAT；U1 西移全案 UNSAT", fontsize=11.5)
for s in ax.spines.values():
    s.set_visible(False)
ax.text(0.5, -0.24, "报废面：被移 ref 焊盘附着铜失效＝149 段／115 网（blast_radius 板件直读；框架版「119 网」为转写误，机器件 nets=115）",
        transform=ax.transAxes, ha="center", fontsize=8.6, color="#8a2f33")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=C_GREEN, ec="#333"), plt.Rectangle((0, 0), 1, 1, fc=C_GRAY, ec="#333"),
                   plt.Rectangle((0, 0), 1, 1, fc=C_RED, ec="#333")],
          labels=["SAT", "UNKNOWN", "UNSAT"], loc="lower right", fontsize=9)

fig.suptitle("篇四图 7　「挪 MCU 解口袋」量化否证：U1 西移 1/2mm 割数 750/186,264（verified UNSAT）＋115 网报废面",
             fontsize=14, fontweight="bold", y=0.995)
fig.text(0.5, 0.010,
         "数据源：coreboard-design1/design1-results.json（counts 29=4/22/3、live sha dbfea089…）；rows/classa_RPL-038/039_*u1_shift*.json 四案"
         "（board_cert_after_change.cut/tier/verified、blast_radius.net_list/segments 直读）；S1 基线=coreboard-live2b-s1/live2s1-results.json（591/301004 交叉锚断言）。\n"
         "西移两案均 verified UNSAT＝「挪 MCU」直觉被量化钉死；GNDA/FMC 口袋墙剥除为条件式 SAT（被剥网重布义务未验证，staged DRC unconn 55→58/61 净收益可能为负——正文 §8.1）。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-07-U1-SHIFT-CUT-EXPLOSION.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-07 生成：%s（%d B）29 计数+4 案割数+报废面+基线交叉锚断言全过" % (out, os.path.getsize(out)))
