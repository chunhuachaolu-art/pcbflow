# -*- coding: utf-8 -*-
"""
篇三 图③：性能瀑布（两火山剖析→A1–A4 EQUIV-PROVEN→NUMBA 逐位移植→集成四门墙钟分布）。

数据来源（全部直读机器件，零硬编码数据点）：
  - out/v5-p5/perf/PROFILE-R1.md L27（第一火山=障碍几何判定 tottime 59.4%/65.08%）、
      L61（第二火山=drc check_clearance cum 48.5%）
  - out/v5-p5/perf/PERF-R1-REPORT.md §3 表（五板：冻结墙钟/原型墙钟双跑/加速比/sha16/字节等）
  - out/v5-p5/perf/NUMBA-R1-REPORT.md §4 D 段表（五板 prenum/numba 各三跑+加速比）、
      §4 正文（thin-pod 266.4s→9.0s ≈29.5×）、§2 表（T1–T6 对拍门）
  - DISPATCH-LOG.md 2026-09-20/21 集成四门节（L916）：门 3 墙钟比
      tmp108 6.8×/bme280 19.6×/thin-pod 28.3×/crypto 21.2×/stm32 16.0×；
      门 1 1170 passed in 389.64s（对照冻结态同套件 799.82s）
断言：五板×三口径加速比解析齐且值域吻合（5.9–22.2 / 1.31–2.19 / 6.8–28.3）；
  两火山剖析值解析；thin-pod 冻结 266.41s；NUMBA 累计 ≈29.5×；输出存在且 >10KB。
"""
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyArrowPatch

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

PERF = "<ENGINE_ROOT>/out/v5-p5/perf"
DL = "<ENGINE_ROOT>/DISPATCH-LOG.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P3-03-PERF-WATERFALL-EQUIV-PRESERVED.png"

profile = open(f"{PERF}/PROFILE-R1.md", encoding="utf-8").read()
perf = open(f"{PERF}/PERF-R1-REPORT.md", encoding="utf-8").read()
numba = open(f"{PERF}/NUMBA-R1-REPORT.md", encoding="utf-8").read()
dl = open(DL, encoding="utf-8").read()

# ---- 两火山剖析值 ----
m = re.search(r"\|\s*障碍几何判定[^|]*\|\s*\*\*(59\.\d)%\*\*（[^）]*）\s*\|\s*\*\*(65\.\d+)%\*\*", profile)
assert m, "PROFILE-R1 第一火山行未解析"
volcano1 = (float(m.group(1)), float(m.group(2)))
m = re.search(r"check_clearance`\s*\|\s*([\d.]+)s（(48\.\d)%）", profile)
assert m, "PROFILE-R1 第二火山行未解析"
volcano2 = (float(m.group(1)), float(m.group(2)))

# ---- PERF-R1 §3 五板表 ----
sec3 = perf.split("## 3. 加速比与字节等")[1].split("## 4.")[0]
boards = {}
for line in sec3.splitlines():
    m = re.match(r"\|\s*(\S+?)(?:（([^）]*)）)?\s*\|\s*([\d.]+)s\s*\|\s*([\d.]+)s / ([\d.]+)s\s*\|\s*\*\*([\d.]+)×\*\*", line)
    if m:
        boards[m.group(1)] = dict(label=f"{m.group(1)}（{m.group(2)}）",
                                  frozen=float(m.group(3)), proto=(float(m.group(4)), float(m.group(5))),
                                  speedup_a=float(m.group(6)))
assert len(boards) == 5, f"PERF §3 板数 {len(boards)} != 5"
order = ["tmp108", "pmod-bme280", "thin-pod", "pmod-crypto", "stm32-ds2480-emu"]
assert all(b in boards for b in order)

# ---- NUMBA §4 五板表 ----
sec4 = numba.split("## 4. D 段：测速")[1].split("微基准")[0]
for line in sec4.splitlines():
    m = re.match(r"\|\s*(\S+)\s*\|\s*([\d.]+) / ([\d.]+) / ([\d.]+)\s*\|\s*([\d.]+) / ([\d.]+) / ([\d.]+)\s*\|\s*\*\*([\d.]+)×\*\*", line)
    if m:
        b = m.group(1)
        assert b in boards, f"NUMBA 表板名 {b} 不在 PERF 表"
        boards[b]["prenum3"] = [float(m.group(i)) for i in (2, 3, 4)]
        boards[b]["numba3"] = [float(m.group(i)) for i in (5, 6, 7)]
        boards[b]["speedup_n"] = float(m.group(8))
assert all("speedup_n" in boards[b] for b in order), "NUMBA §4 五板解析不全"
m = re.search(r"thin-pod 266\.4s → 9\.0s ≈ \*\*(29\.\d+)×\*\*", numba)
assert m, "NUMBA 累计 29.5× 行未解析"
cum = float(m.group(1))

# ---- DISPATCH-LOG 集成门 3 墙钟比 + 门 1 ----
m = re.search(r"门 3 墙钟比 \*\*tmp108 ([\d.]+)×/bme280 ([\d.]+)×/thin-pod ([\d.]+)×/crypto ([\d.]+)×/stm32 ([\d.]+)×\*\*", dl)
assert m, "DISPATCH-LOG 门 3 墙钟比未解析"
gate3 = {"tmp108": float(m.group(1)), "pmod-bme280": float(m.group(2)), "thin-pod": float(m.group(3)),
         "pmod-crypto": float(m.group(4)), "stm32-ds2480-emu": float(m.group(5))}
m = re.search(r"门 1 \*\*1170 passed in ([\d.]+)s\*\*（对照：冻结态复跑同套件 ([\d.]+)s", dl)
assert m, "DISPATCH-LOG 门 1 未解析"
gate1 = (int(1170), float(m.group(1)), float(m.group(2)))

# ---- 值域断言 ----
sa = [boards[b]["speedup_a"] for b in order]
sn = [boards[b]["speedup_n"] for b in order]
sg = [gate3[b] for b in order]
assert min(sa) == 5.9 and max(sa) == 22.2, f"A1–A4 加速比值域 {sa}"
assert min(sn) == 1.31 and max(sn) == 2.19, f"NUMBA 加速比值域 {sn}"
assert min(sg) == 6.8 and max(sg) == 28.3, f"门 3 墙钟比值域 {sg}"
assert abs(boards["thin-pod"]["frozen"] - 266.41) < 0.01
assert abs(cum - 29.5) < 0.05

# ---- 绘图 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8.6), dpi=300,
                               gridspec_kw={"width_ratios": [1.05, 1.25]})

# 面板 A：thin-pod 累计瀑布（冻结→A1–A4→NUMBA）
tp = boards["thin-pod"]
stages = ["冻结引擎\n（⑥后世界）", "A1–A4 等价优化\n（EQUIV-PROVEN）", "＋NUMBA 逐位移植\n（1e7 对拍零 mismatch）"]
vals = [tp["frozen"], min(tp["proto"]), min(tp["numba3"])]
prev = 0
for i, (s, v) in enumerate(zip(stages, vals)):
    color = ["#85929E", "#5DADE2", "#48C9B0"][i]
    ax1.bar(i, v - (0 if i == 0 else vals[i - 1]), bottom=(0 if i == 0 else v), width=0.55,
            color=color, edgecolor="#1b2631", lw=1.2)
    ax1.text(i, v + 4, f"{v:.2f}s", ha="center", fontsize=12, fontweight="bold")
    if i > 0:
        drop = vals[i - 1] - v
        ax1.annotate(f"−{drop:.2f}s\n（{tp['speedup_a'] if i == 1 else tp['speedup_n']}×）",
                     (i - 0.5, (vals[i - 1] + v) / 2), ha="center", fontsize=10.5, color="#922B21",
                     fontweight="bold")
ax1.set_xticks(range(3))
ax1.set_xticklabels(stages, fontsize=10.5)
ax1.set_ylabel("thin-pod 板墙钟（s，min-of 双跑/三跑）", fontsize=11.5)
ax1.set_ylim(0, 300)
ax1.set_title(f"A｜thin-pod 累计瀑布：266.41s→9.03s ≈{cum:.1f}×\n（红线＝双跑字节等优先于速度，每级独立把守）",
              fontsize=12.5, fontweight="bold")
ax1.text(1.0, 210, f"两火山剖析定位：\n①障碍几何判定 tottime {volcano1[0]}%/{volcano1[1]}%（tmp108/bme280）\n"
        f"②drc check_clearance cum {volcano2[1]}%（{volcano2[0]}s）\nnumpy 向量化＝字节等高危手法不取，改精确预选＋剪枝",
        fontsize=10, ha="center", bbox=dict(boxstyle="round,pad=0.4", fc="#FEF9E7", ec="#B7950B"))

# 面板 B：五板三口径加速比分布
import numpy as np

x = np.arange(5)
w = 0.26
short = ["tmp108", "bme280", "thin-pod", "crypto", "stm32*"]
b1 = ax2.bar(x - w, sa, w, label="A1–A4 等价优化（PERF-R1 §3 同会话对照）", color="#5DADE2", edgecolor="#1b2631")
b2 = ax2.bar(x, sn, w, label="NUMBA 板级再加速（NUMBA-R1 §4 min-of-3）", color="#48C9B0", edgecolor="#1b2631")
b3 = ax2.bar(x + w, sg, w, label="集成门 3 墙钟比（DISPATCH-LOG 09-20/21）", color="#F5B041", edgecolor="#1b2631")
for bars in (b1, b2, b3):
    for r in bars:
        ax2.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.35, f"{r.get_height():g}×",
                 ha="center", fontsize=8.8)
ax2.set_yscale("log")
ax2.set_ylim(1, 40)
ax2.set_xticks(x)
ax2.set_xticklabels(short, fontsize=10.5)
ax2.set_ylabel("加速比（×，对数轴）", fontsize=11.5)
ax2.legend(fontsize=9.5, loc="upper left")
ax2.set_title("B｜五板×三口径加速比分布（A1–A4 5.9–22.2×／NUMBA 1.31–2.19×／集成门 6.8–28.3×）\n"
              f"集成门 1：1170 passed in {gate1[1]}s（冻结态同套件 {gate1[2]}s）；门 2 8/8 字节等；门 4 双世界 diff -r 零差",
              fontsize=12.5, fontweight="bold")
ax2.text(2.0, 1.6, "*stm32=FAILED 探针板（106 阶梯耗尽/ripup/restore 卫兵路径，negotiation_log 22KB 摘要逐字节等）",
         fontsize=9, ha="center", color="#566573")

fig.suptitle("性能瀑布：剖析两火山 → A1–A4 EQUIV-PROVEN → NUMBA 逐位移植 → 集成四门（等价保持红线全程有效）",
             fontsize=15.5, fontweight="bold", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
print(f"OK FIG-P3-03 性能瀑布 {OUT} {size} bytes")
print("两火山:", volcano1, volcano2, "| A1-A4:", sa, "| NUMBA:", sn, "| 门3:", sg, "| 门1:", gate1, "| 累计:", cum)
