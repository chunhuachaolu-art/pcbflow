# -*- coding: utf-8 -*-
"""
篇三 图②：世界换版时序（D6→D8→R1→R1-W6/W-B′→ED-X，各时点四树哈希标注）。

数据来源（全部直读机器件；哈希/文件计数程序化解析，禁手抄）：
  - D6 相邻锚：out/v5-p5/p5-sessions/world-code-baseline.json 与 world-code-closeout.json
      （P5 会话波 baseline==closeout DRIFT-FREE；D6 时点四树在 §3.4 表 1 无单值登记，
      取 D6 落地后的最近机器锚并在图中如实标注）
  - D8：out/v5-p5/trial/P5-CLOSEOUT-ADDENDUM-D8-2026-09-22.md §3（L30–31）
  - R1：out/v5-p5/trial/LEAD-REVIEW-R1-2026-09-25.md 面 2（L12）
  - R1-W6/W-B′：out/v5-p5/r1/w6d-fourtrees-final.json（W-6 段收尾）
  - ED-X：out/v5-p5/r1/edx/fourtrees-close.json（close 块；open 块应==W-B′ 终值）
  - 交叉对账：P3-V5-ENGINE-R2-2026-10-03.md §3.4 表 1 四树锚列（D8/R1/W-6/ED-X 四行）
断言：五时点×四树解析齐；ED-X open==W-B′ 终值；p5-sessions baseline==closeout；
  D8/R1/W-B′/ED-X 锚与论文表 1 登记值逐位一致；输出存在且 >10KB。
"""
import hashlib
import json
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyArrowPatch

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

BASE = "<ENGINE_ROOT>/out/v5-p5"
PAPER = "<ENGINE_ROOT>/out/paper-program-r2/P3-V5-ENGINE-R2-2026-10-03.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P3-02-WORLD-RESWAP-TIMELINE-FOURTREES.png"
TREES = ["v5", "tests", "tools", "schemas"]


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tree_from_json(path, block=None):
    d = json.load(open(path, encoding="utf-8"))
    if block:
        d = d[block]
    return {t: (d[t][0], d[t][1]) for t in TREES}


def tree_from_md(path):
    t = open(path, encoding="utf-8").read()
    out = {}
    for tree in TREES:
        m = re.search(tree + r"=([0-9a-f]{8,16})/(\d+)", t)
        assert m, f"{path} 未解析到 {tree} 树锚"
        out[tree] = (m.group(1), int(m.group(2)))
    return out


# ---- 五时点取数（全部机器件直读）----
d6 = tree_from_json(f"{BASE}/p5-sessions/world-code-baseline.json")
d6_close = tree_from_json(f"{BASE}/p5-sessions/world-code-closeout.json")
assert d6 == d6_close, "p5-sessions baseline != closeout（DRIFT-FREE 断言失败）"

d8 = tree_from_md(f"{BASE}/trial/P5-CLOSEOUT-ADDENDUM-D8-2026-09-22.md")
r1 = tree_from_md(f"{BASE}/trial/LEAD-REVIEW-R1-2026-09-25.md")
w6 = tree_from_json(f"{BASE}/r1/w6d-fourtrees-final.json")
edx_close = tree_from_json(f"{BASE}/r1/edx/fourtrees-close.json", "close")
edx_open = tree_from_json(f"{BASE}/r1/edx/fourtrees-close.json", "open")
assert edx_open == w6, "ED-X open 块 != W-B′ 收尾四树（换版链条断裂）"

points = [
    ("D6 出口对齐\n2026-09-18/19 ⑥波", d6, "焊盘真实层跨/逃逸桩端点扎铜/\n板边距 0.2mm/分类器词表四类\n（D6 时点无单值四树登记，\n示相邻机器锚＝P5 会话波 baseline）"),
    ("D8 全板孔\n2026-09-22", d8, "board.holes[] 全板清单/oval 保守\n外接圆/NPTH 入清单/0.25mm 单值单源"),
    ("R1 世界换版三件\n2026-09-25", r1, "FLUTE Steiner＋adapter 0.4.0\n全 pad 质心＋schema board.v1\n＋executor 0.8.0 逐拓扑边"),
    ("R1-W6 W-B′\n2026-09-26", w6, "route_check 0.4.1 plated-union\n（审计器自身被审计翻案修复）"),
    ("ED-X\n2026-09-27", edx_close, "kicad_export 0.5.0（「≥2 逐点」\n多端网导出遗留缺口全修）"),
]

# ---- 交叉对账：论文 §3.4 表 1 四树锚列 ----
paper = open(PAPER, encoding="utf-8").read()
sec34 = paper.split("### 3.4 版本总表")[1].split("## 4 世界合同")[0]


def paper_anchor(row_kw):
    for line in sec34.splitlines():
        if line.startswith("| ") and row_kw in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            col = cells[3]
            out = {}
            for tree in TREES:
                m = re.search(tree + r"=([0-9a-f]{8,16})/(\d+)", col)
                assert m, f"表 1 {row_kw} 行未含 {tree} 锚: {col[:80]}"
                out[tree] = (m.group(1), int(m.group(2)))
            return out
    raise AssertionError(f"表 1 未找到行 {row_kw}")


for kw, idx, tag in [("D8 收口", 1, "D8"), ("R1 收尾", 2, "R1"),
                     ("W-6 段收尾", 3, "W-B′"), ("ED-X 收尾", 4, "ED-X")]:
    pa = paper_anchor(kw)
    got = points[idx][1]
    for tree in TREES:
        assert pa[tree][0].startswith(got[tree][0][:8]) and got[tree][0].startswith(pa[tree][0][:8]), \
            f"{tag} {tree} 锚与表 1 不一致: {got[tree]} vs {pa[tree]}"
        assert pa[tree][1] == got[tree][1], f"{tag} {tree} 文件计数与表 1 不一致"
# DISPATCH-LOG 交叉（D8 四树前缀亦见 DISPATCH-LOG 红线自查节）
dl = open("<ENGINE_ROOT>/DISPATCH-LOG.md", encoding="utf-8").read()
for tree in TREES:
    assert d8[tree][0][:8] in dl, f"D8 {tree} 前缀未在 DISPATCH-LOG 出现"

for p in [f"{BASE}/p5-sessions/world-code-baseline.json",
          f"{BASE}/trial/P5-CLOSEOUT-ADDENDUM-D8-2026-09-22.md",
          f"{BASE}/trial/LEAD-REVIEW-R1-2026-09-25.md",
          f"{BASE}/r1/w6d-fourtrees-final.json",
          f"{BASE}/r1/edx/fourtrees-close.json"]:
    print("source sha256[:16] =", sha256f(p)[:16], p)

# ---- 绘图：时序带 + 四树矩阵（哈希漂移着色）----
fig = plt.figure(figsize=(15.5, 9.2), dpi=300)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
ax.set_xlim(-0.62, 4.95)
ax.set_ylim(0, 12.6)
ax.axis("off")

CHANGED, SAME = "#F5B7B1", "#D5F5E3"
for i, (name, trees, desc) in enumerate(points):
    x = i
    ax.add_patch(plt.Rectangle((x - 0.46, 11.05), 0.92, 1.32, fc="#D6EAF8", ec="#1f618d", lw=1.4))
    ax.text(x, 12.05, name, ha="center", va="center", fontsize=11.5, fontweight="bold")
    ax.text(x, 11.32, desc, ha="center", va="center", fontsize=7.3, color="#1b2631")
    if i < 4:
        ax.add_patch(FancyArrowPatch((x + 0.46, 11.7), (x + 0.54, 11.7), mutation_scale=16,
                                     arrowstyle="-|>", color="#154360", lw=2))
for j, tree in enumerate(TREES):
    y = 9.55 - j * 1.62
    ax.text(-0.56, y, f"{tree} 树\n（哈希/文件数）", ha="left", va="center", fontsize=11, fontweight="bold")
    for i, (name, trees_d, _) in enumerate(points):
        h, n = trees_d[tree]
        changed = i == 0 or points[i - 1][1][tree][0] != h
        ax.add_patch(plt.Rectangle((i - 0.46, y - 0.62), 0.92, 1.24,
                                   fc=CHANGED if changed else SAME, ec="#566573", lw=1.1))
        ax.text(i, y + 0.14, h, ha="center", va="center", fontsize=8.2, family="monospace",
                fontweight="bold" if changed else "normal")
        ax.text(i, y - 0.33, f"/{n} 文件", ha="center", va="center", fontsize=8.5, color="#424949")

ax.text(-0.56, 10.72, "四树锚（全文件 sha256 聚合取前 16 位，算法=out/v5-p5/r1/_snap4.py）；红=相对上一时点哈希漂移（换版本体），绿=零漂移",
        ha="left", va="center", fontsize=9.2, color="#7b241c")
ax.text(-0.56, 2.55, "合同四件兜底（每次换版全验）：①四树哈希开工/收尾双快照，白名单外漂移即停线　②双跑字节等（canonical 产物逐字节相等）\n"
        "③G1–G5 门（tools/build_p5_gate.py 可重跑）　④修订门五条（目标不降/同世界证据/逐类豁免用户逐类确认/逐类披露/判据一与 5x-equal 不受影响）",
        ha="left", va="center", fontsize=9.6,
        bbox=dict(boxstyle="round,pad=0.4", fc="#FEF9E7", ec="#B7950B", lw=1.2))
ax.text(-0.56, 0.85, "换版中的诚实工程案例全部留痕：单行哨兵 or ()→or {}、pyc 竞态、审计器自身被审计翻案（ED-2）、export 遗留缺口（ED-X）",
        ha="left", va="center", fontsize=9.6, color="#7b241c")
ax.set_title("世界换版时序：D6→D8→R1→R1-W6/W-B′→ED-X（各时点四树哈希标注）",
             fontsize=15.5, fontweight="bold", pad=6)

fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
n_changed = sum(1 for i in range(1, 5) for tree in TREES if points[i][1][tree][0] != points[i - 1][1][tree][0])
assert n_changed >= 6, f"换版漂移格子数 {n_changed} 异常少"
print(f"OK FIG-P3-02 世界换版时序 {OUT} {size} bytes；漂移格={n_changed}/16")
print("ED-X schemas 自 D8 起恒定:", all(p[1]['schemas'][0] == d8['schemas'][0] for p in points[1:]))
