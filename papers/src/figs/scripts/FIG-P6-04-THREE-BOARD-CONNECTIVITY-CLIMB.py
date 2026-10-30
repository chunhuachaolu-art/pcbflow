# -*- coding: utf-8 -*-
"""
FIG-P6-04 — P6 图 4：三板连通爬升曲线（m2 → M2R2 → M2R3 → V6-DIAG-R1 四批）
数据源（机器件直读）：
  1. out/canvas-toolchain/act-m2r2/stats/stats-products.json —— m2_comparison（m2 基线 0/9,1/13,3/16）
     + round_curves（M2R2 逐轮连通）+ final_readings（M2R2 终态）
  2. out/canvas-toolchain/act-m2r2/stats/stats-products.json inputs_sha256 —— apply 件 sha 锚重算
  3. out/canvas-toolchain/act-m2r3/apply-R*-<board>.json —— M2R3 逐轮 readings_after.connectivity
  4. out/canvas-toolchain/v6-diag-r1/apply-R*-<board>.json —— DIAG-R1 席位面重跑逐轮连通
     （floor.current=轮始态：crypto 12/16→13、bme280 8/13→9；badgeleds 不上场）
  5. out/canvas-toolchain/v6-diag-r1/triage-matrix.json —— badgeleds 唯一剩余网分类=板固有
     （门槛门正确拦截=不上场依据）
断言：M2R2 终态=(8,8,12)；M2R3 终态=(8,4,8)；DIAG-R1 终态 crypto=13、bme280=9；
  m2 基线=(0,1,3)；badgeleds 剩余网数=1 且 classification=板固有；sha 锚重算一致；输出>10KB。
"""
import glob
import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
CT = os.path.join(REPO, "out/canvas-toolchain")
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-04-THREE-BOARD-CONNECTIVITY-CLIMB.png")

BOARDS = ["badgeleds-do-electronics", "pmod-bme280", "pmod-crypto"]
LABEL = {"badgeleds-do-electronics": "badgeleds（9 网）",
         "pmod-bme280": "bme280（13 网）",
         "pmod-crypto": "crypto（16 网）"}
COLOR = {"badgeleds-do-electronics": "#4c72b0",
         "pmod-bme280": "#dd8452",
         "pmod-crypto": "#55a868"}

stats = json.load(open(os.path.join(CT, "act-m2r2/stats/stats-products.json"), encoding="utf-8"))
m2c, curves = stats["m2_comparison"], stats["round_curves"]

# M2R2 apply 件 sha 锚程序化重算（抽三件）
for rel, exp in list(stats["inputs_sha256"].items()):
    if rel.endswith(("apply-R1-badgeleds-do-electronics.json", "apply-R3-pmod-bme280.json",
                     "apply-R7-pmod-crypto.json")):
        h = hashlib.sha256(open(os.path.join(REPO, rel), "rb").read()).hexdigest()
        assert h == exp, f"sha 重算不一致 {rel}"


def lane_final(lane, b):
    fs = sorted(glob.glob(os.path.join(CT, lane, f"apply-R*-{b}.json")))
    traj, start = [], None
    for f in fs:
        d = json.load(open(f, encoding="utf-8"))
        ra = d.get("readings_after") or {}
        fc = ((d.get("floor") or {}).get("current") or {})
        if start is None and fc.get("connectivity") is not None:
            start = fc["connectivity"]
        if ra.get("connectivity") is not None:
            traj.append(ra["connectivity"])
    return start, traj


m2_base = {b: m2c[b]["connectivity_true"] for b in BOARDS}
m2_den = {b: m2c[b]["connectivity_total"] for b in BOARDS}
m2r2 = {b: curves[b][-1]["connectivity"] for b in BOARDS}
m2r3_start, m2r3_traj = {}, {}
for b in BOARDS:
    m2r3_start[b], m2r3_traj[b] = lane_final("act-m2r3", b)
diag_start, diag_traj = {}, {}
for b in ["pmod-bme280", "pmod-crypto"]:
    diag_start[b], diag_traj[b] = lane_final("v6-diag-r1", b)

assert [m2_base[b] for b in BOARDS] == [0, 1, 3]
assert [m2r2[b] for b in BOARDS] == [8, 8, 12], [m2r2[b] for b in BOARDS]
assert [m2r3_traj[b][-1] for b in BOARDS] == [8, 4, 8], [m2r3_traj[b][-1] for b in BOARDS]
assert diag_traj["pmod-crypto"][-1] == 13 and diag_start["pmod-crypto"] == 12
assert diag_traj["pmod-bme280"][-1] == 9 and diag_start["pmod-bme280"] == 8

# badgeleds 不上场依据：triage-matrix 唯一 badgeleds 网分类=板固有
tri = json.load(open(os.path.join(CT, "v6-diag-r1/triage-matrix.json"), encoding="utf-8"))
bl_nets = [n for n in tri["nets"] if n["board"] == "badgeleds-do-electronics"]
assert len(bl_nets) == 1 and bl_nets[0]["classification"] == "板固有", \
    [(n["net_id"], n["classification"]) for n in bl_nets]

print(f"[read] m2 基线={[m2_base[b] for b in BOARDS]}；M2R2 终态={[m2r2[b] for b in BOARDS]}"
      f"；M2R3 终态={[m2r3_traj[b][-1] for b in BOARDS]}")
print(f"[read] DIAG-R1 席位面重跑：crypto {diag_start['pmod-crypto']}→{diag_traj['pmod-crypto'][-1]}/16、"
      f"bme280 {diag_start['pmod-bme280']}→{diag_traj['pmod-bme280'][-1]}/13；"
      f"badgeleds 不上场（剩余唯一网 {bl_nets[0]['net_id']} 分类=板固有，门槛门拦截）")

# ---- 绘图：x=批内轮次（分批分段折线），批间虚线衔接 ----
fig, ax = plt.subplots(figsize=(13.0, 6.2), dpi=300)
seg_x = {"m2": 0, "M2R2": 1, "M2R3": 2, "DIAG-R1": 3}
gap = 0.06

for b in BOARDS:
    den = m2_den[b]
    # m2 起点
    xs = [seg_x["m2"]]
    ys = [m2_base[b]]
    # M2R2 段（逐轮）
    xs += [seg_x["M2R2"] + gap * (i + 1) for i in range(len(curves[b]))]
    ys += [c["connectivity"] for c in curves[b]]
    ax.plot(xs, ys, "-o", color=COLOR[b], lw=2.0, ms=5, label=LABEL[b])
    # M2R3 段
    xs2 = [seg_x["M2R3"] + gap * (i + 1) for i in range(len(m2r3_traj[b]))]
    ax.plot(xs2, [m2r3_traj[b][i] for i in range(len(m2r3_traj[b]))], "-o", color=COLOR[b],
            lw=2.0, ms=5)
    ax.plot([xs[-1], xs2[0]], [ys[-1], m2r3_traj[b][0]], ":", color=COLOR[b], lw=1.4)
    # DIAG-R1 段
    if b in diag_traj:
        xs3 = [seg_x["DIAG-R1"] + gap * (i + 1) for i in range(len(diag_traj[b]))]
        ax.plot(xs3, diag_traj[b], "-o", color=COLOR[b], lw=2.0, ms=5)
        ax.plot([xs2[-1], xs3[0]], [m2r3_traj[b][-1], diag_traj[b][0]], ":", color=COLOR[b], lw=1.4)
        ax.annotate(f"{diag_traj[b][-1]}/{den}", xy=(xs3[-1], diag_traj[b][-1]),
                    xytext=(xs3[-1] + 0.03, diag_traj[b][-1] + 0.45), fontsize=9,
                    color=COLOR[b], fontweight="bold")
    else:
        ax.annotate("不上场（门槛门拦截：唯一剩余网\n分类=板固有 Net-(C1-Pad1)）",
                    xy=(xs2[-1], m2r3_traj[b][-1]), xytext=(seg_x["DIAG-R1"] - 0.30,
                                                            m2r3_traj[b][-1] + 2.3),
                    fontsize=8.2, color=COLOR[b],
                    arrowprops=dict(arrowstyle="->", color=COLOR[b], lw=0.9))
    # 关键点标注
    for xx, yy, t in [(xs[0], ys[0], f"{m2_base[b]}/{den}"),
                      (xs[-1], ys[-1], f"{ys[-1]}/{den}"),
                      (xs2[-1], m2r3_traj[b][-1], f"{m2r3_traj[b][-1]}/{den}")]:
        ax.annotate(t, xy=(xx, yy), xytext=(xx - 0.045, yy + 0.5), fontsize=8.6, color=COLOR[b])

for name, xx in seg_x.items():
    ax.axvline((xx - 0.055) if xx else -0.28, color="#cccccc", lw=0.8, ls="--")
    ax.text(xx + 0.28, 16.6, name, fontsize=11.5, fontweight="bold", color="#333333")
ax.text(seg_x["m2"] + 0.10, 15.7, "冷启动基线\n(盲孔死锁+票荒)", fontsize=8.0, color="#555555")
ax.text(seg_x["M2R2"] + 0.18, 15.7, "三修复合跑\n(换轨+holes投影+反馈)", fontsize=8.0, color="#555555")
ax.text(seg_x["M2R3"] + 0.12, 15.7, "D-CT-034 修复\n(语义对齐/增益未兑现)", fontsize=8.0, color="#555555")
ax.text(seg_x["DIAG-R1"] + 0.10, 15.7, "席位面重跑\n(A-可达网)", fontsize=8.0, color="#555555")

ax.set_xlim(-0.45, 4.15)
ax.set_ylim(-0.8, 17.6)
ax.set_xticks([])
ax.set_ylabel("连通网数（canvas 世界判据一读数）", fontsize=11)
ax.set_title("三板连通爬升：m2 → M2R2 → M2R3 → V6-DIAG-R1（机制增益坐实，0/3 全连通=硬天花板）",
             fontsize=13, fontweight="bold")
ax.legend(loc="center right", fontsize=9.5)
ax.grid(alpha=0.25, axis="y")
fig.text(0.5, 0.005,
         "图注：数据直读 act-m2r2/stats/stats-products.json（m2_comparison/round_curves，apply 件 sha 锚程序化重算一致）、"
         "act-m2r3/apply-R*、v6-diag-r1/apply-R*（floor.current=轮始态）与 triage-matrix.json（badgeleds 不上场依据）。"
         "段内实线=批内逐轮；批间点线=跨批衔接（M2R3/DIAG-R1 起点=floor.current 机件直读）。DIAG-R1 增益：crypto +IO1（R4 胜者席单层长径）、bme280 +SW2（clearance 继承 via）。",
         ha="center", fontsize=8.0, color="#444444")
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
print(f"[ok] {OUT} ({sz} B)")
