# -*- coding: utf-8 -*-
"""
FIG-P1-B1-SHORTS57-FAMILY-R1 — 篇一新增图：b1 真实板窗 57 条 DRC shorts 家族分解图
（31+18+8 构成；五修后归零）

数据纪律：直读机器证据 JSON，禁止硬编码数据值（脚本内常量仅作断言期望值）。
证据件（均为绝对路径）：
  [1] <WORKSPACE>/tools/pcbflow/out/v4-e4-r1/diag-shorts57/items-classified.json
      —— 57 行逐条分类（category_counts / group_counts / rows；DIAG-SHORTS57-2026-09-24.md 机读表）
  [2] <WORKSPACE>/tools/pcbflow/out/v4-e4-r1/b1/drc-baseline-summary.json
      —— 五修前 b1：shorts=57（kicad-cli 10.0.5）
  [3] <WORKSPACE>/tools/pcbflow/out/v4-e4-r2/b1/drc-baseline-summary.json
      —— 五修后 b1：shorts=0、unconnected=0
  [4] 两版 solver-run-baseline.json —— SAT 状态（修复未牺牲可布性）
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PCB = "<WORKSPACE>/tools/pcbflow"
ITEMS = os.path.join(PCB, "out/v4-e4-r1/diag-shorts57/items-classified.json")
DRC_PRE = os.path.join(PCB, "out/v4-e4-r1/b1/drc-baseline-summary.json")
DRC_POST = os.path.join(PCB, "out/v4-e4-r2/b1/drc-baseline-summary.json")
SOLVER_PRE = os.path.join(PCB, "out/v4-e4-r1/b1/solver-run-baseline.json")
SOLVER_POST = os.path.join(PCB, "out/v4-e4-r2/b1/solver-run-baseline.json")
OUT_PNG = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P1-B1-SHORTS57-FAMILY-R1.png"

# ---------- 读机器件 ----------
items = json.load(open(ITEMS, encoding="utf-8"))
pre = json.load(open(DRC_PRE, encoding="utf-8"))
post = json.load(open(DRC_POST, encoding="utf-8"))
sat_pre = json.load(open(SOLVER_PRE, encoding="utf-8"))
sat_post = json.load(open(SOLVER_POST, encoding="utf-8"))

cat = items["category_counts"]
grp = items["group_counts"]
rows = items["rows"]
cats = ["C1-obstacle-rotation-shape", "C2-obstacle-bbox-clip", "C3-separation-contract-desync"]

# 组→类映射与组代表冲突串（数据驱动，从 rows 提取）
grp_cat = {}
grp_conflict = {}
for r in rows:
    g = r["dedup_group"]
    grp_cat[g] = r["category"]
    if r.get("is_group_representative"):
        grp_conflict[g] = r["conflict"]

# ---------- 断言 ----------
errs = []


def chk(cond, msg):
    if not cond:
        errs.append(msg)


chk(items["total_rows"] == 57, f"total_rows != 57 ({items['total_rows']})")
chk(len(rows) == 57, f"rows != 57 ({len(rows)})")
chk(sum(cat.values()) == 57, f"category_counts 和 != 57 ({sum(cat.values())})")
chk(sum(grp.values()) == 57, f"group_counts 和 != 57 ({sum(grp.values())})")
chk(cat["C1-obstacle-rotation-shape"] == 31, "C1 != 31")
chk(cat["C2-obstacle-bbox-clip"] == 18, "C2 != 18")
chk(cat["C3-separation-contract-desync"] == 8, "C3 != 8")
chk(len(grp) == 5, f"冲突组数 != 5 ({len(grp)})")
chk(items["unique_uuid_pairs"] == 4, "唯一对象对 != 4")
# 组计数与类计数交叉吻合：G1+G2+G3→C1，G4→C2，G5→C3
for c, gs in [("C1-obstacle-rotation-shape", ["G1", "G2", "G3"]),
              ("C2-obstacle-bbox-clip", ["G4"]),
              ("C3-separation-contract-desync", ["G5"])]:
    s = sum(grp[g] for g in gs)
    chk(s == cat[c], f"{c}: 组和 {s} != 类计数 {cat[c]}")
    for g in gs:
        chk(grp_cat[g] == c, f"{g} 组类归属 {grp_cat[g]} != {c}")
chk(set(grp_conflict) == set(grp), "组代表冲突串不全")
# 前后读数
chk(pre["shorts"] == 57, f"修复前 shorts != 57 ({pre['shorts']})")
chk(post["shorts"] == 0, f"修复后 shorts != 0 ({post['shorts']})")
chk(post["unconnected_items"] == 0, "修复后 unconnected != 0")
chk(sat_pre.get("status") == "sat", "修复前 solver != sat")
chk(sat_post.get("status") == "sat", "修复后 solver != sat")

if errs:
    for e in errs:
        print("ASSERT FAIL:", e)
    raise SystemExit(2)
print("[asserts] 全部通过：57=31+18+8（类）＝9+9+13+18+8（组，交叉吻合）；"
      f"shorts {pre['shorts']}→{post['shorts']}；前后均 SAT")

# ---------- 画图 ----------
fig = plt.figure(figsize=(13.2, 7.6), dpi=200)
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.52,
                      left=0.055, right=0.975, top=0.875, bottom=0.075)

C_C1, C_C2, C_C3 = "#4c72b0", "#dd8452", "#937860"
cat_colors = {"C1-obstacle-rotation-shape": C_C1, "C2-obstacle-bbox-clip": C_C2,
              "C3-separation-contract-desync": C_C3}
cat_names = {"C1-obstacle-rotation-shape": "C1 障碍形状旋转缺陷",
             "C2-obstacle-bbox-clip": "C2 障碍宇宙 bbox 裁剪",
             "C3-separation-contract-desync": "C3 分离契约脱同步"}
cat_fix = {"C1-obstacle-rotation-shape": "D1 绝对角判据",
           "C2-obstacle-bbox-clip": "D2 keepout∩工作区相交",
           "C3-separation-contract-desync": "D3 分离常量 3 格"}

# —— (a) 家族构成：修复前 57（三段堆叠）→ 修复后 0 ——
ax = fig.add_subplot(gs[0])
y_pre, y_post = 1.0, 0.0
xoff = 0.0
for c in cats:
    v = cat[c]
    ax.barh(y_pre, v, left=xoff, height=0.56, color=cat_colors[c], edgecolor="white", lw=1.2)
    ax.text(xoff + v / 2, y_pre, f"{cat_names[c]}\n{v} 条\n（修复＝{cat_fix[c]}）",
            ha="center", va="center", fontsize=9.6, color="white", fontweight="bold")
    xoff += v
ax.barh(y_post, 0, height=0.56, color="none")
ax.text(1.2, y_post, f"0 条（shorts={post['shorts']}，unconnected={post['unconnected_items']}，SAT 保持）",
        ha="left", va="center", fontsize=10.5, color="#2d6a4f", fontweight="bold")
ax.annotate("", xy=(0.9, y_post + 0.30), xytext=(30, y_pre - 0.30),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.6,
                            connectionstyle="arc3,rad=-0.25"))
ax.text(30, y_pre + 0.42, f"修复前（E4-R1）：shorts={pre['shorts']} 条＝31＋18＋8，去重后仅 5 个冲突组／4 个唯一对象对",
        ha="center", fontsize=10.5)
ax.text(30, y_pre + 0.76, "放大器：整条 route 共用一个 uuid，KiCad 按 0.1mm 重叠边逐条上报（4 个物理冲突→57 条）",
        ha="center", fontsize=9.5, color="#6b6b6b")
ax.text(0.0, y_post - 0.42, "修复后（E4-R2 五修 268c631）：", ha="left", fontsize=10.5, color="#2d6a4f")
ax.set_xlim(-1, 62)
ax.set_ylim(-0.62, 1.95)
ax.set_yticks([y_pre, y_post])
ax.set_yticklabels(["修复前\nE4-R1", "修复后\nE4-R2"], fontsize=10.5)
ax.set_xlabel("DRC shorting_items 条数（kicad-cli 10.0.5）", fontsize=10.5)
ax.set_title("(a) b1 真实板窗 57 条 shorts 的家族构成与五修归零", fontsize=12, loc="left")
ax.spines[["top", "right"]].set_visible(False)

# —— (b) 5 个冲突组明细（数据驱动标注） ——
ax2 = fig.add_subplot(gs[1])
gkeys = sorted(grp.keys())
xs = range(len(gkeys))
for i, g in enumerate(gkeys):
    c = grp_cat[g]
    ax2.bar(i, grp[g], width=0.58, color=cat_colors[c], edgecolor="white", lw=1.0)
    ax2.text(i, grp[g] + 0.35, str(grp[g]), ha="center", fontsize=12, fontweight="bold")
ax2.set_xticks(list(xs))
ax2.set_xticklabels([f"{g}\n{grp_conflict[g]}" for g in gkeys], fontsize=8.8)
ax2.set_ylabel("上报条数", fontsize=10.5)
ax2.set_ylim(0, 21)
ax2.set_title("(b) 去重后 5 个冲突组（G1–G3→C1／G4→C2／G5→C3，组大小＝该 route 与对侧对象的重叠 0.1mm 边数）",
              fontsize=10.8, loc="left")
ax2.spines[["top", "right"]].set_visible(False)
handles = [Rectangle((0, 0), 1, 1, fc=cat_colors[c]) for c in cats]
ax2.legend(handles, [f"{cat_names[c]}（{cat[c]} 条，修复＝{cat_fix[c]}）" for c in cats],
           fontsize=9.3, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.16), ncol=1)

fig.suptitle("b1 真实板窗 DRC shorts 家族分解：57＝31（旋转判据）＋18（中心点收录）＋8（分离常量），五修后归零且 SAT 保持",
             fontsize=13, y=0.968)

fig.savefig(OUT_PNG)
plt.close(fig)

# ---------- 输出断言 ----------
chk(os.path.exists(OUT_PNG), "输出 PNG 不存在")
sz = os.path.getsize(OUT_PNG)
chk(sz > 10 * 1024, f"输出 PNG 过小: {sz} B")
if errs:
    for e in errs:
        print("ASSERT FAIL:", e)
    raise SystemExit(2)
print(f"[output] {OUT_PNG} ({sz} B)")
