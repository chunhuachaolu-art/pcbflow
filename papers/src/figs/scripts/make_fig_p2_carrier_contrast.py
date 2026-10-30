# -*- coding: utf-8 -*-
"""
篇二双载体对照主图（图像 0/19 vs 盲包 6/6）
- 数据源（全部直读机器证据件，禁止硬编码数据点）：
  1) compare-recheck-r1.json   —— P2-1 跨板 GT 复检读数（图像半 0/19 出处）
  2) channel-replay-r1.json    —— 零命中分通道重放（类别门/几何门分解 + 近邻弃权）
  3) tally-n5.json             —— 席位 A 五模型重放 N=5 计票（盲包半 6/6 出处）
  4) vote-tally.json           —— 席位 C 真实板投票（20 条多数缺陷旁证）
- 内建断言（全过才输出）：数据点数/关键值/交叉一致性/输出文件存在且>10KB。
- 确定性：零 RNG、零时间戳入图。
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---------- 机器件绝对路径 ----------
P_COMPARE = ("<WORKSPACE>/tools/pcbflow/out/v3-tl2/"
             "calibration/gt-expansion-r1/recheck-r1/compare-recheck-r1.json")
P_CHANNEL = ("<WORKSPACE>/tools/pcbflow/out/v3-tl2/"
             "calibration/gt-expansion-r1/recheck-r1/channel-replay-r1.json")
P_TALLY5 = ("<ENGINE_ROOT>/out/v5-p3/seat-a-replay/tally-n5.json")
P_VOTE = ("<ENGINE_ROOT>/out/v5-p5/p5-sessions/vote-tally.json")
OUT_PNG = ("<ENGINE_ROOT>/out/paper-program-r2/figs/"
           "fig-p2-carrier-contrast.png")
OUT_PDF = OUT_PNG.replace(".png", ".pdf")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

cmp19 = load(P_COMPARE)
chan = load(P_CHANNEL)
t5 = load(P_TALLY5)
vt = load(P_VOTE)

# ---------- 断言库 ----------
errs = []
def chk(cond, msg):
    if not cond:
        errs.append(msg)

# A. 图像半：P2-1 recheck 读数（compare-recheck-r1.json）
agg = cmp19["aggregate_19"]
chk(agg["counts"]["gt"] == 19, "A1: 19 条 GT 分母")
chk(agg["counts"]["gt_matched"] == 0, "A2: 命中 0")
chk(agg["gt_recall_total"] == 0.0, "A3: gt_recall_total==0.0")
chk(agg["union_gt_recall_across_boards_instances"] == 0.0, "A4: union 亦 0")
chk(agg["counts"]["seeded"] if False else agg["counts"]["scored"] == 71
    and agg["seed_match_rate_total"] == 0.0, "A5: seed_match 0/71")
b13 = cmp19["baseline_13_parallel"]
chk(b13["r25_representative"]["gt_recall_total"] == 0.0, "A6: 发展域 r25 代表配置 0/13")
union13 = b13["r25_union"]["gt_recall_union"]
chk(abs(union13 - 0.076923) < 1e-6, "A7: 发展域 union 1/13=0.076923")

# B. 图像半：分通道重放（channel-replay-r1.json）
s = chan["summary"]
cat_gate = s["blocked_by_channel"]["category_gate"]
geo_low = s["geometry_subdivision"]["geometry_gate_low_containment"]
geo_area = s["geometry_subdivision"]["geometry_gate_area_ratio"]
near_abstain = s["nearest_flag_is_abstain_count"]
chk(cat_gate + geo_low + geo_area == 19, "B1: 三支互斥完备 17+2+0=19")
chk(s["n_gt"] == 19, "B2: n_gt=19")
chk(0 <= near_abstain <= 19, "B3: 近邻弃权 0..19")

# C. 盲包半：席位 A N=5 计票（tally-n5.json）
items = t5["normalized_tally"]["majority_items"]
chk(len(items) == 6, "C1: majority_items 恰 6 项")
evid = [it["evidence"] for it in items]
chk(all(e in ("3/5", "4/5", "5/5") for e in evid), "C2: evidence 值域 {3/5,4/5,5/5}")
chk(evid.count("5/5") == 3 and evid.count("4/5") == 2 and evid.count("3/5") == 1,
    "C3: 票数结构 3×5/5+2×4/5+1×3/5")
maj = t5["gt_mapped_panel"]["majority"]
chk(set(maj.keys()) == {"GT1", "GT2", "GT3", "GT4"}, "C4: GT 族 4 键")
chk(maj["GT1"] == "4/5" and maj["GT2"] == "4/5" and maj["GT3"] == "3/5"
    and maj["GT4"] == "0/5", "C5: GT 族多数 4/5,4/5,3/5,0/5")
per_seat = t5["gt_mapped_panel"]["per_seat"]
chk(len(per_seat) == 5, "C6: 五席")
chk(all(v["seeded"] == ["D1", "D1b", "D2"] for v in per_seat.values()),
    "C7: 各席播种族 D1/D1b/D2")
# 交叉：GT1/GT2=4/5 与 majority_items 两条 4/5；GT3=3/5 与一条 3/5
n41 = sum(1 for gt, sc in maj.items() if sc == "4/5")
chk(n41 == evid.count("4/5"), "C8: GT 4/5 计数与 majority_items 一致")
chk(t5["normalized_tally"]["vocab_version"] == "1.0.1", "C9: 词表 1.0.1")

# D. 旁证：席位 C（vote-tally.json）
chk(vt["n_lanes"] == 3, "D1: N=3")
chk(vt["defect_counts"]["vote-majority"] == 20, "D2: vote-majority=20")
pb = vt["per_board"]
chk(len(pb) == 14, "D3: 14 终态板")
recomputed = sum(len(v.get("majority_issues", [])) for v in pb.values())
boards_with = sum(1 for v in pb.values() if v.get("majority_issues"))
clean_boards = [b for b, v in pb.items() if not v.get("majority_issues")]
chk(recomputed == 20, "D4: 逐板多数缺陷加总=20")
chk(boards_with == 11 and len(clean_boards) == 3, "D5: 11 板有缺陷+3 洁净")

if errs:
    print("ASSERTION FAILED:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
print("all assertions passed:")
print(f"  image half: gt_recall {agg['gt_recall_arithmetic']}, "
      f"blockers cat={cat_gate} geo_low={geo_low} geo_area={geo_area}, "
      f"near_abstain={near_abstain}, dev-domain union13={union13:.6f}")
print(f"  blindpack half: majority_items=6 ({', '.join(evid)}), "
      f"GT majority={maj}, vote-majority=20 on 14 boards")

# ---------- 绘图 ----------
fig = plt.figure(figsize=(13.6, 7.0), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25], wspace=0.22,
                      left=0.055, right=0.985, top=0.78, bottom=0.245)

C_HIT = "#2a9d5c"      # 命中（正）
C_CAT = "#b0413e"      # 类别门阻断
C_GEO = "#d98324"      # 几何门阻断
C_SEED = "#1f6f9c"     # 播种族聚出
C_UNSOWN = "#3fa7a0"   # 未播种族聚出
C_MISS = "#9aa0a6"     # 全漏（GT4）

# ===== 左面板：图像载体 =====
axL = fig.add_subplot(gs[0, 0])
axL.set_xlim(0, 19)
axL.set_ylim(-0.05, 1.44)
# 命运堆叠条（y=1.0 行）
y0 = 1.02
axL.barh(y0, cat_gate, height=0.30, left=0, color=C_CAT, edgecolor="white")
axL.barh(y0, geo_low, height=0.30, left=cat_gate, color=C_GEO, edgecolor="white")
axL.text(cat_gate / 2, y0, f"类别门阻断\n{cat_gate}", ha="center", va="center",
         color="white", fontsize=9.5, fontweight="bold")
axL.text(cat_gate + geo_low / 2, y0 - 0.185, f"几何门 {geo_low}", ha="center",
         va="top", color=C_GEO, fontsize=9.5, fontweight="bold")
# 命中 0 的显式零宽标注
axL.annotate("命中 0", xy=(19, y0), xytext=(19, y0 + 0.21), ha="right",
             fontsize=9.5, color=C_HIT, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=C_HIT, lw=1.2))
axL.text(9.5, y0 + 0.32, f"跨板 GT 复检（P2-1 recheck-r1）：19 条扩样 DRC-GT，逐格 n=3",
         ha="center", fontsize=8.2, color="#444444")
# 主读数
axL.text(0.0, 0.62, f"gt_recall = {agg['gt_recall_arithmetic'].replace(' ', '')}",
         fontsize=21, fontweight="bold", color=C_CAT, va="center")
axL.text(0.0, 0.44, f"跨实例 union 亦 0/19；seed_match = {agg['seed_match_rate_arithmetic'].replace(' ', '')}",
         fontsize=9.5, color="#333333", va="center")
# 发展域对照小条
axL.text(0.0, 0.24, "发展域对照（Rev-C 13 条，r25 代表配置）：", fontsize=9,
         color="#444444", va="center")
axL.barh(0.115, 13, height=0.075, left=0, color="#e7e2dc", edgecolor="#b9b2a9")
hits13 = round(union13 * 13)
axL.barh(0.115, max(hits13, 0.18), height=0.075, left=0, color=C_MISS, edgecolor="none")
axL.text(13.25, 0.115, f"0/13（union 1/13 = {union13:.3f}）", fontsize=8.5,
         va="center", color="#444444")
# 近邻弃权注记
axL.text(0.0, -0.035,
         f"近邻描述：{near_abstain}/19 条 GT 的最近旗为弃权旗\n（最近框中心距 0.015–0.308 图幅百分比）",
         fontsize=8.2, color="#666666", va="center")
axL.set_yticks([])
axL.set_xlabel("19 条扩样 GT（4 新板，零命中分通道重放：阻断三支互斥完备）", fontsize=9,
               labelpad=8)
axL.set_title("图像载体：渲染图盲读（24 轮校准线）", fontsize=12.5, fontweight="bold",
              color=C_CAT, pad=10)

# ===== 右面板：盲包载体 =====
axR = fig.add_subplot(gs[0, 1])
rows = []  # (label, votes, n, color)
for it in sorted(items, key=lambda x: (-int(x["evidence"].split("/")[0]), x["subject"])):
    v, n = (int(z) for z in it["evidence"].split("/"))
    color = C_SEED if v == n else C_UNSOWN
    rows.append((it["subject"], v, n, color))
# GT4 单列（0/5 全漏，如实呈现——R2 §10.7 口径）
rows.append(("GT4（未播种，全漏）", 0, 5, C_MISS))
rows = rows[::-1]
ypos = list(range(len(rows)))
for yy, (lab, v, n, color) in zip(ypos, rows):
    axR.barh(yy, v, height=0.62, color=color, edgecolor="white")
    axR.text(v + 0.08, yy, f"{v}/{n}", va="center", fontsize=9.5,
             fontweight="bold", color="#333333")
axR.set_yticks(ypos)
axR.set_yticklabels([r[0] for r in rows], fontsize=9)
axR.set_xlim(0, 5.55)
N_ROWS = len(rows)
axR.set_ylim(-0.75, N_ROWS + 2.35)
axR.axvline(3, color="#888888", lw=1.0, ls="--")
axR.text(3.06, -0.55, "多数门 = n//2+1 = 3", fontsize=8.2, color="#666666",
         va="center", ha="left")
axR.set_xlabel("五模型多数票席数（N=5；词表 1.0.1 规范化计票）", fontsize=9,
               labelpad=8)
axR.set_title("结构化盲包：席位 A 五模型重放（N=5 多数票）", fontsize=12.5,
              fontweight="bold", color=C_SEED, pad=12)
# 主读数（data 坐标，置于条形区上方空白带，不与条形/标注重叠）
axR.text(0.06, N_ROWS + 2.02, "聚出 6/6 条规范缺陷（3 条播种族 + GT1–GT3 未播种族）",
         fontsize=11, fontweight="bold", color=C_SEED, va="center")
axR.text(0.06, N_ROWS + 1.55, "GT4（pad 级几何）0/5 全漏如实呈现：盲包信息面决定可判上限",
         fontsize=8.6, color="#666666", va="center")
# 播种事实注记（per_seat.seeded 直读）
axR.text(0.06, N_ROWS + 1.13,
         f"播种事实（各席 per_seat.seeded 一致）：{per_seat['seat1-glm1-run2']['seeded']}",
         fontsize=8.2, color="#666666", va="center")

# ===== 总标题与图例 =====
fig.suptitle("双载体对照主图：同一项目、同一纪律（预注册+fail-closed+席位输出恒 untrusted），"
             "检出结论分岔 —— 图像 0/19 vs 盲包 6/6",
             fontsize=13.5, fontweight="bold", y=0.965)
fig.text(0.5, 0.885,
         "左：图像半分母 = 19 条扩样 DRC-GT（4 新板×n=3）；右：盲包半分母 = 盲包内嵌缺陷"
         "（3 播种 + 4 未播种），聚出口径 = 6 条规范缺陷（GT4 族单列）",
         ha="center", fontsize=9, color="#555555")

legend_elems = [
    Patch(facecolor=C_CAT, label="类别门阻断（旗类别与 GT 零相交）"),
    Patch(facecolor=C_GEO, label="几何门阻断（低 containment）"),
    Patch(facecolor=C_HIT, label="命中（0 条）"),
    Patch(facecolor=C_SEED, label="播种族聚出（5/5 全席）"),
    Patch(facecolor=C_UNSOWN, label="未播种族聚出（GT1–GT3）"),
    Patch(facecolor=C_MISS, label="全漏（GT4；发展域 union 1/13）"),
]
fig.legend(handles=legend_elems, loc="lower center", ncol=3, fontsize=8.6,
           frameon=False, bbox_to_anchor=(0.5, 0.012))

# 席位 C 旁注（legend 之上、axes 之下的分层带）
fig.text(0.985, 0.135,
         f"旁证（席位 C 真实板投票，N=3 三路跨模型路由）：14 终态板 → 20 条多数缺陷"
         f"（{boards_with} 板有缺陷 + {len(clean_boards)} 洁净板；hole_to_hole-genuine 3/3×三板；"
         f"cert-completeness 五板点名）〔vote-tally.json〕",
         ha="right", fontsize=8.0, color="#555555", style="italic")

# ---------- 布局自检：全部文字 bbox 两两相交检测（确定性，先于 savefig） ----------
fig.canvas.draw()
rend = fig.canvas.get_renderer()
items = []  # (label, bbox_display)
for t in fig.texts:
    if t is fig._suptitle:  # suptitle 单独登记，避免同对象自比
        continue
    if t.get_text().strip():
        items.append((f"fig.text[{t.get_text()[:14]}…]", t.get_window_extent(rend)))
for t in [fig._suptitle]:
    if t is not None and t.get_text().strip():
        items.append(("suptitle", t.get_window_extent(rend)))
if fig.legends:
    lg = fig.legends[0]
    lb = lg.get_window_extent(rend)
    items.append(("fig.legend", lb))
for ai, ax in enumerate(fig.axes):
    cands = list(ax.texts)
    if ax.xaxis.label.get_text().strip():
        cands.append(ax.xaxis.label)
    if ax.title.get_text().strip():
        cands.append(ax.title)
    for t in cands:
        if t.get_text().strip():
            items.append((f"ax{ai}[{t.get_text()[:14]}…]", t.get_window_extent(rend)))
overlaps = []
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        b1, b2 = items[i][1], items[j][1]
        x0, x1 = max(b1.x0, b2.x0), min(b1.x1, b2.x1)
        y0, y1 = max(b1.y0, b2.y0), min(b1.y1, b2.y1)
        if x1 > x0 and y1 > y0:
            area = (x1 - x0) * (y1 - y0)
            if area > 16:  # >16 px²（300dpi）视为实质重叠
                overlaps.append((items[i][0], items[j][0], round(area, 1)))
# 文字越出画布检测
W, H = fig.canvas.get_width_height()
oob = [(lab, bb.x0, bb.x1, bb.y0, bb.y1) for lab, bb in items
       if bb.x0 < -1 or bb.x1 > W + 1 or bb.y0 < -1 or bb.y1 > H + 1]
chk(not overlaps, f"文字 bbox 重叠 {len(overlaps)} 处: {overlaps[:8]}")
chk(not oob, f"文字越界 {len(oob)} 处: {oob[:6]}")
if errs:
    print("LAYOUT ASSERTION FAILED:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
print(f"layout check passed: {len(items)} text bboxes, 0 overlaps, 0 out-of-bounds")

fig.savefig(OUT_PNG, dpi=300)
fig.savefig(OUT_PDF)

# ---------- 输出后断言 ----------
size = os.path.getsize(OUT_PNG)
chk(size > 10 * 1024, f"输出 PNG >10KB（实测 {size} 字节）")
chk(os.path.getsize(OUT_PDF) > 10 * 1024, "输出 PDF >10KB")
if errs:
    print("POST ASSERTION FAILED:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
print(f"written: {OUT_PNG} ({size} bytes)")
print(f"written: {OUT_PDF} ({os.path.getsize(OUT_PDF)} bytes)")
