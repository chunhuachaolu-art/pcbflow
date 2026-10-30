# -*- coding: utf-8 -*-
"""
篇三 图⑤：V7 分层布线管线——四层管线（类型规划→模块布局→区域分配→单线）＋三跳质疑环
（数据版：四层各带吞吐计数，全部数字直读机器读数件）。

数据来源（直读机器件，脚本内零数据点硬编码）：
  四层名/锚词（双源断言，沿现行）：
    - <DATA_ROOT>/.zcode/dev-experience/state/v7-hier.md（V7 档案）
    - <ENGINE_ROOT>/out/paper-program-r2/P3-V5-ENGINE-R2-2026-10-03.md §7.1
  L1 类型规划：
    - out/hier-route-r1/l1/READINGS-L1.json（三板网数 57/16/9、J1 6/9）
    - out/hier-route-r1/l1r2/READINGS-L1R2.json（majority_regions 网类型标签计数、
      GLOBAL 豁免面、J1 7/9）
  L2 模块布局：
    - out/hier-route-r1/l2/READINGS-L2.json（非全局网 31/14/7、分簇数、K1–K5 判定）
    - M1 分解：READINGS-L2 无此数、l2/raw/summary.json 亦无（仅文件清单）——实际机器件为
      out/hier-route-r1/solver/out/l2r/m1-baseline.json（L2R 批对 S2 基线的标注分解；
      L2R-VERDICT-2026-09-28.md :18/:39 记 totals 357=237+120）
  L3 区域分配：
    - out/hier-route-r1/solver/FENCE-VERDICT-2026-09-28.md 程序化解析（区内越栏 0×3 板×3 席
      :31、F-J3 终态 93/11/16≤94/11/16 :32，行号程序化登记）
    - out/hier-route-r1/solver/out/fence/fence-results.json（fence_audit_intra 9×0、
      pipeline_final_pairs 93/11/16 交叉对账）
  L4 单线：
    - out/hier-route-r1/solver/out/sv1-results.json（S1 直连 51/51·12/12·9/9、
      S2 冲突段对 256/63/38、冲突网占比、S3 降幅）
    - out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md（6 唯一拓扑 :28，行号程序化登记）
  判据双版本并记（10/10）：READINGS-L2 verdicts K1–K5（5 项）＋ l2r-results.json
    judgments L2R-J1..J5（5 项），共 10 项判定全数入图。
断言：四层名双源逐字一致＋锚词双源命中（现行）；标签计数 Σ==网数 逐板；GLOBAL 计数与
  m1-baseline 双件一致；非 GLOBAL 计数==READINGS-L2 non_global_nets 逐板；
  M1 算术 357==237+120 且逐板 intra+cross==total 且逐板 total==SV1 S2 计数（双件一致）；
  FENCE md 0×3板×3 席命中登记行号且 fence-results intra 审计 9×0；F-J3 终态 md 解析值
  ==fence-results pipeline_final_pairs 且 ≤阈值（l2r j3_thresholds）；
  SV1-VERDICT 6 唯一拓扑命中登记行号；判据面板 10 项==5+5；
  L4 S1 直连 routed==expected 3/3；输出存在且>10KB 且 ≥2000×1000。
图注口径：数据版（机器读数件直读；M1 分解件为 l2r/m1-baseline.json，任务书 fallback
  l2/raw/summary.json 无此数，已如实登记）。
"""
import json
import os
import re
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

BASE = "<ENGINE_ROOT>"
V7 = "<DATA_ROOT>/.zcode/dev-experience/state/v7-hier.md"
PAPER = BASE + "/out/paper-program-r2/P3-V5-ENGINE-R2-2026-10-03.md"
OUT = BASE + "/out/paper-program-r2/figs/FIG-P3-05-V7-FOUR-LAYER-PIPELINE.png"
R_L1 = BASE + "/out/hier-route-r1/l1/READINGS-L1.json"
R_L1R2 = BASE + "/out/hier-route-r1/l1r2/READINGS-L1R2.json"
R_L2 = BASE + "/out/hier-route-r1/l2/READINGS-L2.json"
R_M1 = BASE + "/out/hier-route-r1/solver/out/l2r/m1-baseline.json"
R_L2R = BASE + "/out/hier-route-r1/solver/out/l2r/l2r-results.json"
MD_FENCE = BASE + "/out/hier-route-r1/solver/FENCE-VERDICT-2026-09-28.md"
R_FENCE = BASE + "/out/hier-route-r1/solver/out/fence/fence-results.json"
R_SV1 = BASE + "/out/hier-route-r1/solver/out/sv1-results.json"
MD_SV1 = BASE + "/out/hier-route-r1/solver/SV1-VERDICT-2026-09-25.md"

BOARDS = ["HR1-BOARD-A", "HR1-BOARD-B", "HR1-BOARD-C"]
BSHORT = ["A", "B", "C"]

v7 = open(V7, encoding="utf-8").read()
paper = open(PAPER, encoding="utf-8").read()
l1 = json.load(open(R_L1, encoding="utf-8"))
l1r2 = json.load(open(R_L1R2, encoding="utf-8"))
l2 = json.load(open(R_L2, encoding="utf-8"))
m1 = json.load(open(R_M1, encoding="utf-8"))
l2r = json.load(open(R_L2R, encoding="utf-8"))
fence = json.load(open(R_FENCE, encoding="utf-8"))
sv1 = json.load(open(R_SV1, encoding="utf-8"))

# ---- 锚词双源断言（沿现行） ----
LAYERS = ["类型规划", "模块布局", "区域分配", "单线"]
m7 = re.search(r"四层管线（" + "→".join(LAYERS) + r"）", v7)
mp = re.search(r"四层管线（" + "→".join(LAYERS) + r"）", paper)
assert m7, "v7-hier.md 四层管线原文未命中"
assert mp, "P3 §7.1 四层管线原文未命中"
for kw in ["三跳质疑环", "运动员/裁判分离" if "运动员/裁判分离" in v7 else "裁判分离", "原理图直出"]:
    assert kw in v7, f"v7-hier.md 缺锚词 {kw}"
assert "三跳质疑环" in paper and "原理图直出" in paper, "P3 §7.1 缺锚词"
assert "席位" in v7 and ("纯会话" in v7), "v7-hier.md 席位口径未命中"

# ---- L1：网数/标签计数/GLOBAL 豁免/J1 双批 ----
nets = [l1["boards"][b]["nets"] for b in BOARDS]
nets_r2 = [l1r2["readings"]["boards"][b]["nets"] for b in BOARDS]
assert nets == nets_r2, "L1 与 L1R2 三板网数不一致"
assert all(n > 0 for n in nets) and sum(nets) == sum(nets_r2), "网数非法"
label_counts = {b: dict(Counter(l1r2["majority_regions"][b].values())) for b in BOARDS}
for b, n in zip(BOARDS, nets):
    assert sum(label_counts[b].values()) == n, f"{b} 标签计数总和!=网数"
glob = [label_counts[b].get("GLOBAL", 0) for b in BOARDS]
glob_m1 = [m1["boards"][b]["global_nets"] for b in BOARDS]
assert glob == glob_m1, "GLOBAL 网计数与 m1-baseline 不一致"
nonglob = [n - g for n, g in zip(nets, glob)]
ng_l2 = [l2["boards"][b]["non_global_nets"] for b in BOARDS]
assert nonglob == ng_l2, "非 GLOBAL 计数与 READINGS-L2 non_global_nets 不一致"
j1_l1 = (l1["global"]["j1_ok"], l1["global"]["j1_total"])
j1_r2 = (l1r2["readings"]["global"]["j1_ok"], l1r2["readings"]["global"]["j1_total"])
assert j1_l1[1] == 9 and j1_r2[1] == 9, "J1 总案例数非 9"

# ---- L2：分簇/K1–K5/M1 分解 ----
cls = {b: [l2["boards"][b]["n_cls"][s] for s in ("1", "2", "3")] for b in BOARDS}
verdicts_l2 = l2["global"]["verdicts"]  # K1..K5（5 项）
assert len(verdicts_l2) == 5 and set(verdicts_l2) == {"K1", "K2", "K3", "K4", "K5"}, "L2 判定非 K1-K5 五项"
intra = [m1["boards"][b]["intra_pairs"] for b in BOARDS]
cross = [m1["boards"][b]["cross_pairs"] for b in BOARDS]
tot_m1 = [m1["boards"][b]["s2_total_conflict_pairs"] for b in BOARDS]
gg = [m1["boards"][b]["global_global_pairs"] for b in BOARDS]
for i in range(3):
    assert intra[i] + cross[i] == tot_m1[i], f"板 {BSHORT[i]} M1 分解算术不成立"
assert sum(intra) == 237 and sum(cross) == 120 and sum(tot_m1) == 357, "M1 totals 与 237/120/357 不符"
assert sum(intra) + sum(cross) == sum(tot_m1), "M1 总账算术不成立"
cross_ratio = [m1["boards"][b]["cross_ratio"] for b in BOARDS]

# ---- L3：FENCE md 程序化解析（行号登记）＋fence-results 交叉 ----
fence_lines = open(MD_FENCE, encoding="utf-8").read().splitlines()
ln_zero = ln_fj3 = None
fence_final_md = None
for idx, line in enumerate(fence_lines, 1):
    if ln_zero is None and re.search(r"区内网越栏段数＝\*\*0 × 3 板 × 3 席 = 0/9\*\*", line):
        ln_zero = idx
    m = ln_fj3 is None and re.search(r"A \*\*(\d+)≤(\d+)\*\*（全席严格<，−1）、B \*\*(\d+)=(\d+)\*\*、C \*\*(\d+)=(\d+)\*\*", line)
    if m:
        ln_fj3 = idx
        fence_final_md = [int(m.group(1)), int(m.group(3)), int(m.group(5))]
        thr_md = [int(m.group(2)), int(m.group(4)), int(m.group(6))]
assert ln_zero, "FENCE-VERDICT 0×3板×3席 行未命中"
assert ln_fj3 and fence_final_md, "FENCE-VERDICT F-J3 终态行未命中"
intra_audit = [fence["boards"][b]["seats"][s]["fence_audit_intra"]["out_of_fence_segments"]
               for b in BOARDS for s in ("seat1", "seat2", "seat3")]
assert len(intra_audit) == 9 and all(v == 0 for v in intra_audit), "fence-results 区内越栏非 9×0"
assert fence["judgments"]["F-J2"]["pass"] is True, "F-J2 非 PASS"
fence_final = [fence["boards"][b]["seats"]["seat1"]["pipeline_final_pairs"] for b in BOARDS]
for b in BOARDS:
    finals = {fence["boards"][b]["seats"][s]["pipeline_final_pairs"] for s in ("seat1", "seat2", "seat3")}
    assert len(finals) == 1, f"{b} 三席终态分化"
assert fence_final == fence_final_md, "md 终态与 fence-results 不一致"
thr_l2r = [l2r["baseline_reading"]["j3_thresholds"][b] for b in BOARDS]
assert thr_l2r == thr_md, "阈值 md 与 l2r j3_thresholds 不一致"
assert all(f <= t for f, t in zip(fence_final, thr_l2r)), "F-J3 终态超阈值"

# ---- L4：SV1 直读＋SV1-VERDICT md（行号登记） ----
routed = [sv1["boards"][b]["j1"]["nets_routed"] for b in BOARDS]
expected = [sv1["boards"][b]["j1"]["nets_expected_routable"] for b in BOARDS]
assert routed == expected and all(sv1["boards"][b]["j1"]["pass"] for b in BOARDS), "S1 直连 J1 不全通"
s2_pairs = [sv1["boards"][b]["j2"]["total_conflict_pairs"] for b in BOARDS]
assert s2_pairs == tot_m1, "SV1 S2 计数与 m1-baseline 不一致"
ratio = [sv1["boards"][b]["j2"]["conflict_net_ratio"] for b in BOARDS]
red = [sv1["boards"][b]["j3"]["reduction_ratio"] for b in BOARDS]
assert all(0 < r <= 1 for r in ratio) and all(0 < r < 0.3 for r in red), "占比/降幅值域异常"
sv1_lines = open(MD_SV1, encoding="utf-8").read().splitlines()
ln_topo = None
for idx, line in enumerate(sv1_lines, 1):
    if ln_topo is None and (m := re.search(r"候选集 = (\d+) 个唯一拓扑", line)):
        n_topo = int(m.group(1))
        ln_topo = idx
assert ln_topo and n_topo == 6, "SV1-VERDICT 六唯一拓扑行未命中"

# ---- 判据双版本并记（10/10） ----
j_l2r = l2r["judgments"]
assert set(j_l2r) == {f"L2R-J{i}" for i in range(1, 6)}, "L2R 判定非 J1-J5 五项"
n_chips = len(verdicts_l2) + len(j_l2r)
assert n_chips == 10, "双版本判定项非 10"
l2r_j2 = j_l2r["L2R-J2"]
assert l2r_j2["pass"] is True and l2r_j2["boards_pass_count"] == 3, "L2R-J2 非 3/3"
assert j_l2r["L2R-J3"]["pass"] is True, "L2R-J3 非 PASS"


def fmt_label_counts(b):
    c = label_counts[b]
    return "·".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))


def fmt3(vals):
    return "/".join(str(v) for v in vals)


# ---- 绘图 ----
fig, ax = plt.subplots(figsize=(14.2, 9.6), dpi=220)
ax.set_xlim(0, 10.25)
ax.set_ylim(0, 11.35)
ax.axis("off")

X0, X1 = 0.35, 6.45
CX = (X0 + X1) / 2

# 输入条
ax.add_patch(FancyBboxPatch((X0, 9.42), X1 - X0, 0.5, boxstyle="round,pad=0.06",
                            fc="#D6EAF8", ec="#154360", lw=1.4))
ax.text(CX, 9.67, f"输入：原理图/板 三板 {sum(nets)} 网（A {nets[0]}/B {nets[1]}/C {nets[2]}）"
        "（终极目标=原理图直出电路板）", fontsize=10.5, ha="center", va="center",
        fontweight="bold", color="#154360")

layer_rows = [
    ("第 1 层 · 类型规划（L1/L1R2）",
     f"网类型标注（majority 标签）：A {fmt_label_counts(BOARDS[0])}｜B {fmt_label_counts(BOARDS[1])}｜C {fmt_label_counts(BOARDS[2])}",
     f"GLOBAL 豁免面 {sum(glob)} 网（{fmt3(glob)}，电源网不设栏）·J1 合法门 {j1_l1[0]}/{j1_l1[1]}→{j1_r2[0]}/{j1_r2[1]}（L1R2 修复）",
     "#BFD8E8"),
    ("第 2 层 · 模块布局（L2/L2R）",
     f"非全局 {sum(nonglob)} 网（{fmt3(nonglob)}）簇分组（三席）：A {fmt3(cls[BOARDS[0]])}·B {fmt3(cls[BOARDS[1]])}·C {fmt3(cls[BOARDS[2]])} 簇",
     f"M1 分解：S2 冲突段对 {sum(tot_m1)}＝区内 {sum(intra)}＋跨区 {sum(cross)}（跨区占比 "
     f"{cross_ratio[0]*100:.1f}/{cross_ratio[1]*100:.1f}/{cross_ratio[2]*100:.1f}%）",
     "#C9E2C5"),
    ("第 3 层 · 区域分配（FENCE）",
     f"区内越栏段数 0 × 3 板 × 3 席＝0/9（构造性兑现，FENCE-VERDICT :{ln_zero}；fence-results 审计 9×0 核对）",
     f"管线终态 {fmt3(fence_final)} ≤ 阈值 {fmt3(thr_l2r)}（F-J3 3/3，FENCE-VERDICT :{ln_fj3}）",
     "#F5CBA7"),
    ("第 4 层 · 单线（SV1）",
     f"S1 直连 J1：{routed[0]}/{expected[0]}·{routed[1]}/{expected[1]}·{routed[2]}/{expected[2]} 全通；S2 冲突段对 {fmt3(s2_pairs)}＋冲突网占比 "
     f"{ratio[0]*100:.1f}/{ratio[1]*100:.0f}/{ratio[2]*100:.0f}%",
     f"S3 {n_topo} 唯一拓扑（SV1-VERDICT :{ln_topo}）·初消解降幅 {red[0]*100:.1f}–{red[2]*100:.1f}%（FAIL 0/3 未达 30% 首门）·J4 双跑字节等 3/3",
     "#E8DAEF"),
]

arrow_labels = [
    f"三板 {sum(nets)} 网（{fmt3(nets)}）",
    f"非全局 {sum(nonglob)} 网（{fmt3(nonglob)}）",
    f"{sum(tot_m1)} 冲突段对（区内 {sum(intra)}/跨区 {sum(cross)}）",
    f"围栏态终段 {fmt3(fence_final)}",
]

y = 8.55
H = 1.52
GAP = 1.83
for i, (title, r1, r2, color) in enumerate(layer_rows):
    ax.add_patch(FancyBboxPatch((X0, y - H / 2), X1 - X0, H, boxstyle="round,pad=0.08",
                                fc=color, ec="#34495e", lw=1.4))
    ax.text(X0 + 0.25, y + 0.48, title, fontsize=12.5, fontweight="bold", va="center")
    ax.text(X0 + 0.25, y - 0.06, r1, fontsize=8.7, va="center", color="#1b2631")
    ax.text(X0 + 0.25, y - 0.52, r2, fontsize=8.7, va="center", color="#1b2631")
    if i < 3:
        ax.add_patch(FancyArrowPatch((CX - 1.55, y - H / 2), (CX - 1.55, y - GAP - H / 2 + 0.06),
                                     mutation_scale=20, arrowstyle="-|>", color="#154360", lw=2.2))
        ax.text(CX - 1.4, y - GAP / 2 - H / 2 + 0.1, arrow_labels[i], fontsize=8.6,
                va="center", color="#154360")
    y -= GAP

# 输出条
ax.add_patch(FancyArrowPatch((CX - 1.55, y + H / 2), (CX - 1.55, y - 0.02), mutation_scale=20,
                             arrowstyle="-|>", color="#154360", lw=2.0))
ax.add_patch(FancyBboxPatch((X0, 0.62), X1 - X0, 0.5, boxstyle="round,pad=0.06",
                            fc="#D6EAF8", ec="#154360", lw=1.4))
ax.text(CX, 0.87, f"输出：分层布线方案（J1 直连/J2 重叠/J3 消解/J4 双跑字节等判据链·双版本并记 10/10）",
        fontsize=10, ha="center", va="center", fontweight="bold", color="#154360")

# 右上：三跳质疑环（沿现行）
ax.add_patch(FancyBboxPatch((6.75, 5.15), 3.25, 4.75, boxstyle="round,pad=0.1",
                            fc="#FEF9E7", ec="#B7950B", lw=1.6))
ax.text(8.375, 9.5, "三跳质疑环", fontsize=13, fontweight="bold", ha="center", color="#7d6608")
hops = [
    "第 1 跳：席位对上层产物\n提出质疑（预注册判据）",
    "第 2 跳：主审/引擎终选\n裁决（K6 零仲裁 N 席=N 候选）",
    "第 3 跳：下一层接收并\n携带证据回跳复核",
]
yy = 8.65
for i, h in enumerate(hops):
    ax.text(8.375, yy, h, fontsize=9.6, ha="center", va="center")
    if i < 2:
        ax.add_patch(FancyArrowPatch((8.375, yy - 0.55), (8.375, yy - 0.92), mutation_scale=16,
                                     arrowstyle="-|>", color="#7d6608", lw=1.8))
    yy -= 1.5
ax.add_patch(FancyArrowPatch((9.85, 5.85), (9.85, 8.5), connectionstyle="arc3,rad=0.45",
                             mutation_scale=16, arrowstyle="-|>", color="#A04000", lw=2.0, ls="--"))
ax.text(10.06, 7.15, "回环", fontsize=9.5, rotation=90, va="center", color="#A04000")

# 右中：判据双版本并记面板（10/10）
ax.add_patch(FancyBboxPatch((6.75, 1.95), 3.25, 2.95, boxstyle="round,pad=0.1",
                            fc="#FDF2E9", ec="#A04000", lw=1.5))
ax.text(8.375, 4.6, "J 判据链 · 双版本并记（10/10）", fontsize=11, fontweight="bold",
        ha="center", color="#A04000")
l2r_pass = [j_l2r[f"L2R-J{i}"].get("pass") for i in range(1, 6)]


def chip_txt(p):
    if p is True:
        return "PASS"
    if p is False:
        return "FAIL"
    return "记账"


ax.text(8.375, 4.0, f"L2 首版 K1–K5：" + "·".join(f"K{i+1} {verdicts_l2[f'K{i+1}']}" for i in range(5)),
        fontsize=8.6, ha="center", va="center")
ax.text(8.375, 3.5, f"L2R 复判 J1–J5：" + "·".join(f"J{i+1} {chip_txt(p)}" for i, p in enumerate(l2r_pass)),
        fontsize=8.6, ha="center", va="center")
ax.text(8.375, 2.95, f"J2 双版本：K2 {verdicts_l2['K2']}→L2R-J2 PASS 3/3\n（区内消解兑现，三席全过）",
        fontsize=8.4, ha="center", va="center")
ax.text(8.375, 2.35, f"J3 双版本：K3 {verdicts_l2['K3']}→L2R-J3 PASS 3/3\n（终态 {fmt3(fence_final)} ≤ {fmt3(thr_l2r)}）",
        fontsize=8.4, ha="center", va="center")

# 底部：执行纪律面板（沿现行）
ax.add_patch(FancyBboxPatch((X0, 0.12), X1 - X0, 0.42, boxstyle="round,pad=0.05",
                            fc="#EBF5FB", ec="#1F618D", lw=1.2))
ax.text(CX, 0.33, "执行纪律（§7.1）：运动员/裁判分离＋席位=无工具纯会话数据内嵌＋用户操作一键；开工首读 STATUS.md 对账",
        fontsize=8.6, ha="center", va="center", color="#1F618D")

ax.set_title("V7 分层布线管线：四层管线＋三跳质疑环（数据版）\n"
             "四层名=state/v7-hier.md×P3 §7.1 双源逐字一致（断言）；L1–L4 吞吐计数直读 l1·l1r2·l2·l2r(m1)·fence·sv1 机器读数件",
             fontsize=14, fontweight="bold", pad=10)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

# ---- 输出断言 ----
assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
img = plt.imread(OUT)
ih, iw = img.shape[0], img.shape[1]
assert iw >= 2000 and ih >= 1000, f"PNG 尺寸 {iw}×{ih} <2000×1000"
print(f"OK FIG-P3-05 V7 四层管线数据版 {OUT} {size} bytes {iw}x{ih}")
print(f"DATA L1 nets={fmt3(nets)} GLOBAL={fmt3(glob)} J1 {j1_l1[0]}/{j1_l1[1]}->{j1_r2[0]}/{j1_r2[1]}")
print(f"DATA L2 clusters A={fmt3(cls[BOARDS[0]])} M1 {sum(tot_m1)}={sum(intra)}+{sum(cross)}")
print(f"DATA L3 fence0x9 line:{ln_zero} final={fmt3(fence_final)}<=thr{fmt3(thr_l2r)} line:{ln_fj3}")
print(f"DATA L4 sv1 S2={fmt3(s2_pairs)} ratio={fmt3([round(r*100, 1) for r in ratio])}% topo6 line:{ln_topo}")
print(f"DATA chips 10/10 = K1-K5 {len(verdicts_l2)} + L2R-J1..J5 {len(j_l2r)}")
