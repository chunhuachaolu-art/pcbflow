# -*- coding: utf-8 -*-
"""
FIG-P1-R55-3P-FOUR-GATES-R1 — 篇一新增图：R55-3′ 修复批四门读数图
（w5/w6 shorts 55→0 与 SAT 保持的分组呈现；SMOKE/G-R1/G-R2/G-3 四门）

数据纪律：直读机器证据 JSON，禁止硬编码数据值（脚本内常量仅作断言期望值）。
证据件（均为绝对路径）：
  [1] <WORKSPACE>/tools/pcbflow/out/v4-r55-1/compare-e5r3.json
      —— R55-3′ 16 世界×两臂 vs E5R3 对照（G-R1/G-R2/G-3 门块＋逐行 a_shorts/status）
      注：REPORT-R55-3P.md §5 引「compare-e5r3-r3.json」，盘上实际文件名=compare-e5r3.json，
          内容与其 §1/§2 读数逐项吻合（w5 sat/27 路由、w6 sat/18 路由、w10/11 shorts 1/1、
          w13–15 shorts 19/18/18），文件头 prereg 字段为管线脚本 R55-1 时代残留指针
          （prereg-r55-1.md sha16=3a26a0bab9d148ee，已程序化重算吻合）。
  [2] <WORKSPACE>/tools/pcbflow/out/v4-r55-1/double-run-records.json
      —— G-3 门：31 组同进程双跑 byte_equal 记录
  [3] .../out/v4-r55-1/w5/drc-baseline-summary.json + solver-run-baseline.json（SMOKE 门直读）
  [4] .../out/v4-r55-1/w6/drc-baseline-summary.json + solver-run-baseline.json（G-R1 门直读）
prereg 锚：prereg-r55-3p.md sha256 前 16 位=5a11fcb495e442be（脚本内程序化重算断言）。
"""
import json
import hashlib
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ---------- 中文字体 ----------
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = "<WORKSPACE>/tools/pcbflow/out/v4-r55-1"
CMP = os.path.join(ROOT, "compare-e5r3.json")
DRR = os.path.join(ROOT, "double-run-records.json")
PREREG = os.path.join(ROOT, "prereg-r55-3p.md")
OUT_PNG = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P1-R55-3P-FOUR-GATES-R1.png"

# ---------- 读机器件 ----------
cmpd = json.load(open(CMP, encoding="utf-8"))
drr = json.load(open(DRR, encoding="utf-8"))
rows = {r["key"]: r for r in cmpd["rows"]}

drc = {}
solver = {}
for w in ("w5", "w6"):
    drc[w] = json.load(open(os.path.join(ROOT, w, "drc-baseline-summary.json"), encoding="utf-8"))
    solver[w] = json.load(open(os.path.join(ROOT, w, "solver-run-baseline.json"), encoding="utf-8"))

# prereg sha16 程序化重算（禁止手抄）
sha16 = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()[:16]

# ---------- 断言（全部通过才画） ----------
errs = []


def chk(cond, msg):
    if not cond:
        errs.append(msg)


# 门块
chk(cmpd["G-R1"]["pass"] is True, "G-R1 pass != true")
chk(cmpd["G-R2"]["pass"] is True, "G-R2 pass != true")
chk(cmpd["G-R2"]["sat_regressions"] == [], "G-R2 sat_regressions 非空")
chk(cmpd["G-3"]["pass"] is True, "G-3 pass != true")

# 16 世界零劣化：逐窗逐臂 r55 状态 == e5r3 状态
chk(len(cmpd["rows"]) == 16, f"rows != 16 ({len(cmpd['rows'])})")
for k, r in rows.items():
    for arm, v in r["arms"].items():
        chk(v["r55"]["status"] == v["e5r3"]["status"],
            f"{k}/{arm}: r55={v['r55']['status']} != e5r3={v['e5r3']['status']}")
# 原零窗（e5r3 shorts=0）在 r55 保持 0
for k, r in rows.items():
    if r["a_shorts"]["e5r3"] == 0:
        chk(r["a_shorts"]["r55"] == 0, f"{k}: 原零窗 e5r3=0 但 r55={r['a_shorts']['r55']}")

# w5/w6 核心读数：shorts 55→0、SAT 保持、路由数
for w, routes_expect, gate in (("w5", 27, "SMOKE"), ("w6", 18, "G-R1")):
    chk(rows[w]["a_shorts"]["e5r3"] == 55, f"{w}: e5r3 shorts != 55")
    chk(rows[w]["a_shorts"]["r55"] == 0, f"{w}: r55 shorts != 0")
    for arm, v in rows[w]["arms"].items():
        chk(v["r55"]["status"] == "sat", f"{w}/{arm}: r55 status != sat")
        chk(v["e5r3"]["status"] == "sat", f"{w}/{arm}: e5r3 status != sat")
    # 直读 DRC/solver 交叉验证（不经 compare 件）
    chk(drc[w]["shorts"] == 0, f"{w}: drc-baseline-summary shorts != 0")
    chk(drc[w]["unconnected_items"] == 0, f"{w}: unconnected_items != 0")
    chk(solver[w].get("status") == "sat", f"{w}: solver status != sat")
    n_routes = len(solver[w].get("routes", []))
    chk(n_routes == routes_expect, f"{w}: routes={n_routes} != {routes_expect}（{gate} 门读数）")
    # compare 件内 r55 routes 与 solver 直读一致
    chk(rows[w]["arms"]["baseline"]["r55"]["routes"] == routes_expect,
        f"{w}: compare routes 与 solver 直读不一致")

# G-3：31 组全 byte_equal
chk(len(drr) == 31, f"double-run records != 31 ({len(drr)})")
chk(all(r.get("byte_equal") is True for r in drr), "double-run 存在 byte_equal != true")

# prereg sha16
chk(sha16 == "5a11fcb495e442be", f"prereg sha16 重算不符: {sha16}")

if errs:
    for e in errs:
        print("ASSERT FAIL:", e)
    raise SystemExit(2)
print("[asserts] 全部通过：16 行零劣化；w5/w6 shorts 55→0 且 SAT 保持（27/18 路由）；"
      f"31/31 byte_equal；prereg sha16={sha16} 吻合")

# ---------- 画图 ----------
fig = plt.figure(figsize=(13.6, 8.2), dpi=200)
gs = fig.add_gridspec(2, 2, height_ratios=[2.05, 1.0], hspace=0.42, wspace=0.22,
                      left=0.075, right=0.975, top=0.885, bottom=0.09)

C_BEFORE = "#c44e52"   # 修复前（E5R3）
C_AFTER = "#55a868"    # 修复后（R55-3′）
C_SAT = "#55a868"
C_FAIL = "#b8b8b8"

# —— (a) w5/w6 分组柱状：shorts 55→0 ——
ax = fig.add_subplot(gs[0, :])
x = [0, 1]
bw = 0.32
before = [rows[w]["a_shorts"]["e5r3"] for w in ("w5", "w6")]
after = [rows[w]["a_shorts"]["r55"] for w in ("w5", "w6")]
b1 = ax.bar([i - bw / 2 for i in x], before, bw, color=C_BEFORE, label="修复前 E5R3（55 家族在案）")
b2 = ax.bar([i + bw / 2 for i in x], after, bw, color=C_AFTER, label="修复后 R55-3′（全层阻挡）")
for xi, v in zip(x, before):
    ax.text(xi - bw / 2, v + 1.2, str(v), ha="center", va="bottom", fontsize=13, fontweight="bold", color=C_BEFORE)
for xi, v in zip(x, after):
    ax.text(xi + bw / 2, v + 1.2, str(v), ha="center", va="bottom", fontsize=13, fontweight="bold", color=C_AFTER)
ax.set_xticks(x)
ax.set_xticklabels(["w5（SMOKE 门）", "w6（G-R1 门）"], fontsize=12)
ax.set_ylabel("DRC shorts 条数（kicad-cli 10.0.5）", fontsize=11)
ax.set_ylim(0, 68)
ax.set_title("(a) w5/w6 短路数 55→0，且修复前后均 SAT（SAT 保持）", fontsize=12.5, loc="left")
ax.legend(fontsize=10.5, frameon=False, loc="upper right")
for xi, w in zip(x, ("w5", "w6")):
    nr = len(solver[w]["routes"])
    ax.text(xi, 62, f"SAT 保持\nA/C 两臂 sat→sat\n基线臂 {nr} 条路由",
            ha="center", va="top", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.32", fc="#eef5ef", ec=C_SAT, lw=0.9))
ax.spines[["top", "right"]].set_visible(False)

# —— (b) G-R2：16 世界×两臂 SAT 状态矩阵（零劣化） ——
ax2 = fig.add_subplot(gs[1, 0])
keys = [r["key"] for r in cmpd["rows"]]
arms = ["baseline", "challenger"]
arm_names = ["A 臂（基线序）", "C 臂（挑战序）"]
for iy, k in enumerate(keys):
    for ix, arm in enumerate(arms):
        if arm not in rows[k]["arms"]:
            # b1 行只有 baseline 臂（E5R3/R55 设计即如此）：空白格＋“—”
            ax2.text(ix + 0.46, len(keys) - 1 - iy + 0.46, "—", ha="center", va="center",
                     fontsize=10, color="#9a9a9a")
            continue
        st = rows[k]["arms"][arm]["r55"]["status"]
        col = C_SAT if st == "sat" else C_FAIL
        ax2.add_patch(Rectangle((ix, len(keys) - 1 - iy), 0.92, 0.92, fc=col,
                                ec="#4a4a4a", lw=0.6, ls="-" if st == "sat" else (0, (2, 1.4))))
hl = {"w5", "w6"}
for iy, k in enumerate(keys):
    yy = len(keys) - 1 - iy
    if k in hl:
        ax2.add_patch(Rectangle((-1.55, yy), 0.42, 0.92, fc="#f2c94c", ec="none"))
    ax2.text(-0.62, yy + 0.46, k, ha="right", va="center", fontsize=9.3,
             fontweight="bold" if k in hl else "normal")
ax2.set_xlim(-1.7, 2.05)
ax2.set_ylim(-0.35, len(keys) - 0.05)
ax2.set_xticks([0.46, 1.46])
ax2.set_xticklabels(arm_names, fontsize=10)
ax2.set_yticks([])
ax2.tick_params(axis="x", length=0)
for s in ax2.spines.values():
    s.set_visible(False)
ax2.set_title("(b) G-R2 回归门：16 世界×两臂 vs E5R3 逐窗零劣化\n"
              "（每格=R55-3′ 状态，与 E5R3 全同构：sat→sat／failed→failed；黄色条=w5/w6，仅 shorts 归零、SAT 不变）",
              fontsize=10.2, loc="left")
ax2.text(1.98, len(keys) - 0.55, "■ SAT    □ FAILED", ha="right", va="top", fontsize=9.5)

# —— (c) G-3：31 组双跑字节等 ——
ax3 = fig.add_subplot(gs[1, 1])
for i, r in enumerate(drr):
    col = 8 if i < 8 else 12
    rowi = i // col
    xxi = i % col
    ax3.add_patch(Rectangle((xxi, -rowi), 0.86, 0.86, fc=C_SAT, ec="#ffffff", lw=1.0))
ax3.set_xlim(-0.3, 12.1)
ax3.set_ylim(-2.9, 1.6)
ax3.axis("off")
ax3.text(0.0, 1.28, "(c) G-3 完整性门：31 组（15 窗×2 臂＋b1×A）同进程双跑", fontsize=10.2, ha="left")
ax3.text(0.0, 0.92, "全部 byte_equal=true（solver-run sha256 逐组相等）", fontsize=10.2, ha="left")
ax3.text(0.0, -2.75, f"n={len(drr)}／byte_equal 全过（读自 double-run-records.json）",
         fontsize=9.5, color="#3a3a3a", ha="left")

fig.suptitle("R55-3′ 修复批四门读数：w5/w6 短路 55→0 且 SAT 保持，16 世界零劣化、31 组双跑字节等"
             "（PRE 机械预检另过，读数见 REPORT-R55-3P §1）", fontsize=13.5, y=0.965)

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
