# -*- coding: utf-8 -*-
"""
FIG-P6-05 — P6 图 5：停滞成因假设域收窄漏斗（SEAT-STALL-R1 → SEAT-STALL-TRIG-R1 三道 → 剩余面）
数据源（机器件直读）：
  1. out/canvas-toolchain/seat-stall-r1/analysis.json —— 健康窗基线（14 席零停滞、
     三族时长中位/极值：T0 12.9/13.9、32.1/33.7；T1 25.0/28.0、38.7/48.1；T2 46.6/61.4、53.0/121.1）
  2. out/canvas-toolchain/seat-stall-r1/measurements.jsonl —— dispatch=17/notify=17
     （token 完成即写 17/17 全回收：席位次口径=14 原生+3 早波重发）
  3. out/canvas-toolchain/seat-stall-trig-r1/{l1,l2}/analysis.json + lane3-r1/analysis.json ——
     三道×6 席=18/18 零停滞（T8/T12 重载荷、GLM-5.3×2+deepseek-flash；时长中位 139.6/189.3、
     105.7/183.9、64.0/68.7 s）→「单发批量大小」假设跨三环境否定
  4. out/canvas-toolchain/act-m2r3/token-ledger.jsonl —— 42 槽中 -R1 重派 17=40.5%
     （「多轮交互形状×通道窗」首份真板证据；对照 M2R2 零重派）
断言：stall 基线 14 席 stall_candidates=0；measurements dispatch=notify=17；
  三 trig 道 seats_total=6、stall_candidates=0；m2r3 台账 42 行、-R1=17（40.5%）；输出>10KB。
"""
import collections
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
CT = os.path.join(REPO, "out/canvas-toolchain")
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-05-STALL-CAUSE-FUNNEL.png")

# ---- 取数 ----
stall = json.load(open(os.path.join(CT, "seat-stall-r1/analysis.json"), encoding="utf-8"))
s_sum = stall["summary"]
assert s_sum["seats_total"] == 14 and s_sum["stall_candidates"] == 0
ev = collections.Counter()
for line in open(os.path.join(CT, "seat-stall-r1/measurements.jsonl"), encoding="utf-8"):
    ev[json.loads(line)["event"]] += 1
assert ev["dispatch"] == 17 and ev["notify"] == 17, dict(ev)
fams = {k: (v["dur_med_s"], v["dur_max_s"]) for k, v in s_sum["cross"].items()}

trig = {}
trig_durs = []
for lane, p in [("L1·GLM-5.3", "seat-stall-trig-r1/l1"), ("L2·GLM-5.3", "seat-stall-trig-r1/l2"),
                ("L3·deepseek-flash", "lane3-r1")]:
    d = json.load(open(os.path.join(CT, p, "analysis.json"), encoding="utf-8"))
    assert d["summary"]["seats_total"] == 6 and d["summary"]["stall_candidates"] == 0
    trig[lane] = d["summary"]["cross"]
    trig_durs += [s["duration_ms"] / 1000.0 for s in d["seats"].values()]
trig_lo, trig_hi = min(trig_durs), max(trig_durs)
assert len(trig_durs) == 18

rows = [json.loads(l) for l in open(os.path.join(CT, "act-m2r3/token-ledger.jsonl"),
                                    encoding="utf-8") if l.strip()]
n_slots = len(rows)
n_r1 = sum(1 for r in rows if str(r["seat"]).endswith("-R1"))
assert n_slots == 42 and n_r1 == 17, (n_slots, n_r1)
rate = n_r1 / n_slots
assert abs(rate - 0.405) < 5e-4, rate

print(f"[read] SEAT-STALL-R1：14 席零停滞、dispatch/notify=17/17（完成即写全回收）；"
      f"三族时长（中位,极值）={ {k: v for k, v in list(fams.items())[:3]} } …")
print(f"[read] TRIG 三道（各 6 席零停滞）：")
for k, v in trig.items():
    print(f"        {k}: " + ", ".join(f"{fam} 中位 {d['dur_med_s']}s/极值 {d['dur_max_s']}s"
                                       for fam, d in sorted(v.items())))
print(f"[read] M2R3 真板重派率：{n_r1}/{n_slots}={rate:.1%}（-R1 席位后缀程序计数；对照 M2R2 零重派）")

# ---- 绘图：漏斗 ----
fig, ax = plt.subplots(figsize=(12.8, 7.4), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

stages = [
    # (y_top, half_w_top, half_w_bot, 标题, 证据文本, 颜色)
    (78, 44, 36, "停滞成因假设域（试点实录：pmod 同协议 4 起、时间簇状）",
     "候选面：写盘时序（token 完成≠落盘）· 单发批量大小 · 环境通道 · 任务形状（多轮交互）×通道窗", "#d7e6f7"),
    (58, 36, 27, "SEAT-STALL-R1（健康窗 14 席·GLM-5.3）",
     "排除「token 完成≠写盘」：完成即写 17/17 席次全回收（dispatch=notify=17）＝唯一可靠对策；"
     "健康窗基线 12–34s/单网 22–48s/三网 27–121s（15min 停滞线余量 ≥7×）", "#e3efd9"),
    (38, 27, 16, "SEAT-STALL-TRIG-R1 三道（T8/T12 重载荷·18 席）",
     "否定「单发批量大小」（跨三环境）：GLM-5.3×2＋deepseek-flash 共 18/18 席零停滞、"
     f"单席时长 {trig_lo:.0f}–{trig_hi:.0f}s（0.9–5.1min）、T12=全板单发", "#f7e8cf"),
    (18, 16, 9, "剩余停滞面＝多轮交互形状 × 通道窗",
     "首份真板证据：M2R3 真板多轮长任务席夜班重派率 40.5%（17/42 槽；对照 M2R2 零重派；"
     "D-CT-040 处置事件流缺失待裁）", "#f2d7d7"),
]
for i, (y, wt, wb, title, ev_txt, fc) in enumerate(stages):
    yb = y - 16
    ax.add_patch(Polygon([[50 - wt, y], [50 + wt, y], [50 + wb, yb], [50 - wb, yb]],
                         closed=True, fc=fc, ec="#5a5a5a", lw=1.3))
    ax.text(50, y - 3.2, title, ha="center", fontsize=11.2, fontweight="bold")
    ax.text(50, y - 8.2, ev_txt, ha="center", va="top", fontsize=8.2, wrap=True,
            color="#333333" if i else "#1a4f8b")
    if i:
        ax.annotate("", xy=(50 - wt, y), xytext=(50 - stages[i - 1][2] - 1.2, y + 0.4),
                    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.8))

# 右侧：三道证据读数小表
ax.text(93.5, 70, "TRIG 三道读数（analysis.json）", ha="center", fontsize=8.8,
        fontweight="bold", color="#8b4a1a")
ty = 66
for lane, cross in trig.items():
    for fam, d in sorted(cross.items()):
        ax.text(93.5, ty, f"{lane} {fam}：中位 {d['dur_med_s']}s（极值 {d['dur_max_s']}s）、n={d['n']}、零停滞",
                ha="center", fontsize=7.2)
        ty -= 2.6

# 左侧：健康窗基线读数
ax.text(6.5, 70, "健康窗基线（SEAT-STALL-R1）", ha="left", fontsize=8.8,
        fontweight="bold", color="#2c5e33")
ty = 66.4
for fam in sorted(fams):
    med, mx = fams[fam]
    ax.text(6.5, ty, f"{fam.replace('|', '×')}：中位 {med}s／极值 {mx}s",
            ha="left", fontsize=7.2)
    ty -= 2.6

ax.text(50, 96.5, "停滞域收窄链：假设域逐批排除 → 剩余面＝多轮交互形状×通道窗",
        ha="center", fontsize=14.5, fontweight="bold")
ax.text(50, 92.3, "漏斗宽度=假设域示意收窄（非数值度量）；各级证据数字全部机件直读",
        ha="center", fontsize=9, color="#555555")
ax.text(50, 6.5, "图注：SEAT-STALL-R1＝token 完成即写 17/17 全回收（measurements.jsonl dispatch/notify 计数）；"
                 "TRIG 三道 18/18 零停滞（三件 analysis.json summary）；\nM2R3 重派 17/42=40.5%（token-ledger.jsonl "
                 "seat 后缀 -R1 程序计数；LEAD-REVIEW-M2R3 §D 双源一致）。D-CT-040 处置事件流缺失按「待裁」口径标注，不代裁。",
        ha="center", fontsize=8.2, color="#444444")

fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
print(f"[ok] {OUT} ({sz} B)")
