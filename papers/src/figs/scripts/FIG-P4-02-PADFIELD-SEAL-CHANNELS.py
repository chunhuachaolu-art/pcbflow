# -*- coding: utf-8 -*-
"""
FIG-P4-02-PADFIELD-SEAL-CHANNELS — 篇四图 2 焊盘场封死几何（逐板最窄通道 vs 走廊需求 1.0mm）

数据件（全部机器件直读，禁硬编码）：
  - <ENGINE_ROOT>/out/v5-p5/diag-failed8/*.diag.json（8 板逐板 witness：
    witness.channel_scan.per_layer=<层, [最窄通道mm, 直连段最小距离mm, 左间隙, 右间隙, 阻挡1id, 阻挡2id]>，
    exhaustion_cause、net、verdict.class）
  - 期望值锚（脚本断言）：atmega 0.03／m2 0.65／om 0.90／pmod 0.222／thunderbolt 0.458／usb 1.09（mm，DIAG-FAILED8-REPORT §2 逐板表）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-02-PADFIELD-SEAL-CHANNELS.png
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_GREEN = "#55a868"; C_RED = "#c44e52"; C_GRAY = "#8c8c8c"

SRC = "<ENGINE_ROOT>/out/v5-p5/diag-failed8"
EXPECT = {  # 报告 §2 逐板表锚值（关键值断言，容差 0.005）
    "atmega32u4-breakout": 0.03, "m2-pcie-adapter": 0.65, "om-flexgrid-v4-rigid-pcb": 0.90,
    "pmod-i2c24io": 0.222, "thunderbolt-pcie-adapter": 0.458, "usb-gigabit-rev-e": 1.09,
}

recs = []
for p in sorted(glob.glob(SRC + "/*.diag.json")):
    d = json.load(open(p, encoding="utf-8"))
    cs = d["witness"]["channel_scan"]
    demand = cs["demand_2r5"]
    best = None
    for lay, v in cs["per_layer"].items():
        if v is None:
            continue
        if best is None or v[0] < best[1]:
            best = (lay, v[0], v)
    recs.append(dict(board=d["board"], net=d["net"], cause=d["exhaustion_cause"],
                     demand=demand, layer=best[0] if best else None,
                     ch=best[1] if best else None, blk1=(best[2][4] if best else None),
                     dmin=(best[2][1] if best else None),
                     cls=d["verdict"]["class"], path=p))
assert len(recs) == 8, "8 板断言失败"
assert all(abs(demand - 1.0) < 1e-9 for r in recs for demand in [r["demand"]]), "需求 1.0mm 断言失败"
assert all(r["cls"].startswith("(a)") for r in recs), "8/8 (a) 断言失败"
for r in recs:
    if r["board"] in EXPECT:
        assert abs(r["ch"] - EXPECT[r["board"]]) < 0.005, "锚值断言失败 %s: %s" % (r["board"], r["ch"])
no_ch = [r for r in recs if r["ch"] is None]
assert len(no_ch) == 2 and {r["board"] for r in no_ch} == {"dc-scm-rot-jumper-card", "stm32-ds2480-emu"}, \
    "两板无有限走廊读数断言失败"

def short_blk(s):
    if not s:
        return ""
    seg = s.split(":")
    if seg[0] == "fixed" and "pad" in s:
        return "板固焊盘 " + seg[3].split(":")[0]
    if seg[0] == "route":
        return "引擎已布铜 " + seg[1]
    return s[:28]

recs.sort(key=lambda r: (r["ch"] is None, -(r["ch"] or 0)))

fig, ax = plt.subplots(figsize=(13.2, 7.6))
ys = list(range(len(recs)))[::-1]
for y, r in zip(ys, recs):
    if r["ch"] is None:
        ax.barh(y, 0.06, color="white", edgecolor=C_GRAY, hatch="///", height=0.62)
        ax.text(0.09, y, "无有限走廊读数（%s）" % (
            "直连走廊空旷、封死在绕行域" if r["board"] == "dc-scm-rot-jumper-card" else "障碍稠密：U2-Pad2 距路径 0.45mm＜R5"),
            va="center", fontsize=8.6, color="#555555")
    else:
        under = r["ch"] < 1.0
        ax.barh(y, r["ch"], color=(C_RED if under else C_ORANGE), height=0.62,
                edgecolor="#333333", lw=0.6)
        ax.text(r["ch"] + 0.015, y + 0.06, "%.3f mm" % r["ch"], va="center", fontsize=9.6,
                fontweight="bold", color=("#8a2f33" if under else "#96522e"))
        note = "（贴限超出需求侧；(a) 证据=d=0 焊盘场压直连段）" if not under else ""
        ax.text(r["ch"] + 0.015, y - 0.22, "最窄层 %s · 直连段最小距离 %s mm%s" % (
            r["layer"], ("0（压焊盘）" if r["dmin"] == 0.0 else "%.3f" % r["dmin"]), note),
            va="center", fontsize=7.8, color="#666666")
        ax.text(0.012, y, short_blk(r["blk1"]), va="center", fontsize=7.6, color="white" if r["ch"] > 0.30 else "#333333")

ax.axvline(1.0, color=C_BLUE, lw=2.2, ls="--")
ax.text(1.0, 7.7, "走廊需求 2×R5 = 1.0 mm", color=C_BLUE, fontsize=10.5, ha="center", fontweight="bold",
        bbox=dict(fc="white", ec=C_BLUE, boxstyle="round,pad=0.25"))

labels = ["%s\n卡网 %s" % (r["board"], r["net"]) for r in recs]
ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=9.2)
ax.set_xlabel("直连走廊两侧最近障碍中心线间距（mm）", fontsize=11)
ax.set_xlim(0, 1.36)
ax.set_title("篇四图 2　八板焊盘场封死几何：逐板最窄通道 vs 走廊需求 1.0mm（8/8 终判 (a) 板固有）",
             fontsize=14, fontweight="bold", pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", ls=":", alpha=0.45)

fig.text(0.5, 0.012,
         "数据源：out/v5-p5/diag-failed8/*.diag.json（8 件逐板 witness，witness.channel_scan.per_layer 直读；需求=demand_2r5）。"
         "锚值断言：atmega 0.030／m2 0.650／om 0.900／pmod 0.222／thunderbolt 0.458／usb 1.090（与 DIAG-FAILED8-REPORT.md §2 逐板表一致，容差 0.005mm）。\n"
         "统一证据链：routes/vias/holes/edge 四类摘除仍锁、仅 fixed 与 all-geometric 摘除解锁（封死面=板固焊盘场）；探针矩阵解锁数=0。"
         "usb 板 1.09mm 系贴限超出需求侧，其 (a) 证据为 d=0 焊盘场压直连段而非通道不足。",
         ha="center", fontsize=8, color="#666666", linespacing=1.7)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-02-PADFIELD-SEAL-CHANNELS.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-02 生成：%s（%d B）8 板读数+6 锚值+需求 1.0+2 板无读数断言全过" % (out, os.path.getsize(out)))
