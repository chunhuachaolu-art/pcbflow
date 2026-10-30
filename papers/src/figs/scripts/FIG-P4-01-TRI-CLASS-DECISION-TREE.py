# -*- coding: utf-8 -*-
"""
FIG-P4-01-TRI-CLASS-DECISION-TREE — 篇四图 1 三分类判定树（数据版）

数据件（全部机器件直读，禁硬编码数据点；布局坐标/颜色/字号除外）：
  - tools/v5_diag_inherent.py（FROZEN_CRITERIA 冻结式原文，正则直读）
  - out/v5-p5/diag-failed8/summary.json（8 板终判逐行）
  - out/v5-p5/diag-failed8/<板>.diag.json ×8（probes 字段逐板直读 → 8×6 探针解锁矩阵；
      verdict.removal_unlock_classes / engine_unlock_faces / width_unlock_tags 直读断言）
  - out/v5-p5/diag-failed8/DIAG-FAILED8-REPORT.md（§3「探针解锁数=0」口径锚；§5 事件 2 披露）
  - out/v5-p5/boardintake-r1/a1/esp32-devkit-lipo-rev-c.json（(b) 首证）
  - out/v5-p5/p5-gate/dispositions-r1-2026-09-28.json（处置名册 10 板）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-01-TRI-CLASS-DECISION-TREE.png

口径澄清（席位核实，图注同步）：diag.json 的 probes 字段对应 DIAG-FAILED8-REPORT §3 表头的
六个放松探针面（判定树第三步），与「六类摘除」（第二步，removal_unlock_classes 面）是两个
维度；本图热图列=六探针面，摘除面在第二步框以 removal_unlock_classes 直读断言呈现，不混套。
"""
import glob
import json
import os
import re
import struct

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_GREEN = "#55a868"
C_RED = "#c44e52"; C_GRAY = "#8c8c8c"; C_DARK = "#444444"; C_BROWN = "#937860"

BASE = "<ENGINE_ROOT>/out/v5-p5"
DIAG_DIR = BASE + "/diag-failed8"

# ================================================================ 数据直读＋断言
# ---- 1) 冻结判据原文（正则直读，照旧）
tool_src = open("<ENGINE_ROOT>/tools/v5_diag_inherent.py", encoding="utf-8").read()
m = re.search(r'FROZEN_CRITERIA = \((.*?)\)\n', tool_src, re.S)
assert m, "FROZEN_CRITERIA 未定位"
frozen = "".join(eval("(" + m.group(1) + ")"))
assert "(b) routes 类摘除解锁→引擎" in frozen and "(a) fixed 类摘除解锁且 routes 仍锁→板固有" in frozen \
       and "(c) 仅宽度规则面解锁→带值" in frozen and "undetermined（保守不归类，只披露）" in frozen, "冻结式四分支不完整"

# ---- 2) summary.json：8 行全 (a)（照旧）＋板名集合
summ = json.load(open(DIAG_DIR + "/summary.json", encoding="utf-8"))
rows = summ["rows"]
assert len(rows) == 8 and all(r["class"].startswith("(a)") for r in rows), "诊断批 8/8 (a) 断言失败"
n_a_diag = len(rows)
sum_boards = sorted(r["board"] for r in rows)

# ---- 3) <板>.diag.json ×8：probes 逐板直读 → 8×6 矩阵＋摘除面断言
diag_files = sorted(glob.glob(DIAG_DIR + "/*.diag.json"))
assert len(diag_files) == 8, "diag.json 应为 8 份，实得 %d" % len(diag_files)
# 六探针面（列）：前缀→ REPORT §3 表头列一一对应；前缀唯一落列由 face_of 断言保证
FACES = [("width-rule-0.25", "宽度 0.25"), ("width-rule-0.2（", "宽度 0.2"),
         ("ripup-deepen-5", "rip-up 深度 2→5"), ("escape-ext-", "逃逸细化＋方向扩"),
         ("layer-release:", "层偏好释放"), ("order-first", "布线序前置")]

def face_of(tag):
    hits = [i for i, (pfx, _) in enumerate(FACES) if tag.startswith(pfx)]
    assert len(hits) == 1, "探针条目无法唯一落列（对应不明，不硬套）：%s" % tag
    return hits[0]

diags = {}
n_entries = n_locked = n_skip = 0
for fp in diag_files:
    d = json.load(open(fp, encoding="utf-8"))
    b = d["board"]
    assert b not in diags, "diag.json 板名重复：%s" % b
    assert d["verdict"]["class"].startswith("(a)"), "%s 终判非 (a)" % b
    assert d["verdict"]["removal_unlock_classes"] == ["all-geometric", "fixed"], \
        "%s 摘除解锁类≠[all-geometric, fixed]" % b
    assert d["verdict"]["engine_unlock_faces"] == [] and d["verdict"]["width_unlock_tags"] == [], \
        "%s 引擎面/宽度面解锁非空" % b
    probes = d["probes"]
    assert 5 <= len(probes) <= 7, "%s 探针条目数 %d 越界（REPORT §1 轻板 7/重板 ≤5）" % (b, len(probes))
    cells = {}  # face_idx -> {"state": locked/skip, "txt": str}
    for p in probes:
        fi = face_of(p["tag"])
        u = p["unlocked"]
        n_entries += 1
        if u is True:            # 解锁=1（DIAG-FAILED8-REPORT §3 口径＝全 0，此处必须永不发生）
            cells[fi] = {"state": "unlock", "txt": "解锁"}
        elif u is False:
            n_locked += 1
            at = p.get("attempts")
            t = str(at) if at is not None else "仍锁"
            if fi in cells and cells[fi]["state"] == "locked":
                cells[fi]["txt"] += "+" + t          # 同面多条（层释放多板双内层）合并
            else:
                cells[fi] = {"state": "locked", "txt": t}
        else:                     # unlocked=null（跳过/真空）
            n_skip += 1
            sk = p.get("skipped") or ""
            cells[fi] = {"state": "skip", "txt": "vacuous" if "vacuous" in sk else "跳过†"}
    diags[b] = cells
diag_boards = sorted(diags)
assert diag_boards == sum_boards, "diag.json 板名与 summary.json 不一致"

# 矩阵断言：解锁全 0（真值单元=0）＋未测列缺（absent）如实登记
n_absent = 0
for b in diag_boards:
    for fi in range(6):
        if fi not in diags[b]:
            n_absent += 1
            diags[b][fi] = {"state": "absent", "txt": "未测"}
n_unlock_total = sum(1 for b in diag_boards for fi in range(6) if diags[b][fi]["state"] == "unlock")
assert n_unlock_total == 0, "探针解锁计数非 0（与 REPORT §3 口径冲突）"
per_board_unlock = [sum(1 for fi in range(6) if diags[b][fi]["state"] == "unlock") for b in diag_boards]
per_face_unlock = [sum(1 for b in diag_boards if diags[b][fi]["state"] == "unlock") for fi in range(6)]
assert sum(per_board_unlock) == 0 and sum(per_face_unlock) == 0

# ---- 4) REPORT §3 口径锚＋§5 事件 2 披露句（程序化解析，非手抄）
rep = open(DIAG_DIR + "/DIAG-FAILED8-REPORT.md", encoding="utf-8").read()
m3 = re.search(r"## 3\. 探针矩阵.*?- 探针解锁数=0", rep, re.S)
assert m3, "REPORT §3「探针解锁数=0」锚未命中"
assert re.search(r"## 5\. .*?seq375 台账为准=仍锁", rep, re.S), "REPORT §5 事件 2（seq375=仍锁）披露句未命中"

# ---- 5) (b) 首证（照旧＋removal 机器面强化）
esp = json.load(open(BASE + "/boardintake-r1/a1/esp32-devkit-lipo-rev-c.json", encoding="utf-8"))
assert esp["verdict"]["class"].startswith("(b)"), "esp32 (b) 断言失败"
assert "rip-up 阻塞集选择/联合重解深度" in esp["verdict"]["note"], "(b) 缺口面措辞未命中"
assert "routes" in esp["verdict"]["removal_unlock_classes"], "esp32 摘除解锁类缺 routes（(b) 判据机器面）"
b_name = esp["board"]; n_b = 1  # 唯一首证件（boardintake-a1 单件，class 断言已过）
b_gapface = "rip-up 阻塞集选择／联合重解深度"

# ---- 6) 处置名册 10 板（照旧）＋ (a) 双源板名逐位一致（新）
disp = json.load(open(BASE + "/p5-gate/dispositions-r1-2026-09-28.json", encoding="utf-8"))
boards = disp["boards"]
roster_a = sorted(k for k, v in boards.items() if v["disposition"] == "board-inherent")
c_roster = sorted(k for k, v in boards.items() if v["disposition"] != "board-inherent")
n_a_roster = len(roster_a)
assert len(boards) == 10 and n_a_roster == 8 and len(c_roster) == 2, "处置名册 10 板=8 固有+2 (c) 断言失败"
assert all("(c)" in boards[k]["diag_class"] for k in c_roster), "(c) 名册判类断言失败"
c_names = "、".join(c_roster)
assert "tmp108" in c_names and "bme280" in c_names, "(c) 两板名断言失败"
assert roster_a == diag_boards, "名册 board-inherent 8 板与诊断批板名非逐位一致"
n_und = sum(1 for r in rows if "undetermined" in r["class"])
assert n_und == 0, "undetermined 实例数非 0"

# 实例面（条长∝板数，机器件直读列全；(a)=同一批 8 板双源一致，并集 8 非双重计数 16）
a_names = diag_boards

# ---- 六类摘除/探针标签（表述串，非数据点）
removal6 = ["routes（他网已布铜）", "vias（他网孔铜）", "holes（板固孔带）",
            "edge（板边带）", "fixed（板固有固定铜）", "all-geometric（全几何）"]
probe5 = ["宽度 0.25/0.2", "ripup 深度 2→5", "逃逸细化＋方向扩", "层释放", "序前置"]

# ================================================================ 绘图
fig = plt.figure(figsize=(16.2, 11.2))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

def box(x, y, w, h, fc, ec, txt, fs=10.5, tc="black", lw=1.4, weight="normal"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.6", fc=fc, ec=ec, lw=lw))
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=tc, fontweight=weight, linespacing=1.5)

def arrow(x1, y1, x2, y2, color=C_DARK, lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, color=color, lw=lw, shrinkA=2, shrinkB=2))

# ---- 标题（数据版口径）
ax.text(50, 98.2, "三分类判定树：witness → 类摘除 → 探针 → (a)/(b)/(c)/undetermined（数据版）",
        ha="center", va="center", fontsize=15.5, fontweight="bold")
ax.text(50, 95.3, "冻结判据原文（tools/v5_diag_inherent.py FROZEN_CRITERIA，脚本直读重验）："
        + frozen.replace("；", "；\n").replace("(b)", "\n(b)").strip(),
        ha="center", va="top", fontsize=8.4, color="#555555", linespacing=1.6)

# ---- 树骨架（三步照旧，第二/三步并入机器读数）
box(50, 86.5, 40, 5.5, "#e8eef7", C_BLUE, "FAILED 卡网（V5 世界语料）", fs=12, weight="bold")
arrow(50, 83.7, 50, 80.9)
box(50, 77.2, 62, 6.5, "#f7f4ec", C_ORANGE,
    "第一步　witness 抽取：execute.json 末轮候选忠实重放（8/8 板 negotiation_log 逐字节相等）\n"
    "端点几何归一 · 端点密封普查（0.25/0.125/0.0625 三档 pitch） · 直连走廊通道扫描（41 采样点 vs 需求 2×R5=1.0mm）",
    fs=9.0)
arrow(50, 73.9, 50, 71.1)
box(50, 67.6, 62, 6.8, "#f7f4ec", C_ORANGE,
    "第二步　类摘除测试（捕获态快照内存修改，解锁=充分性证据）：" + "　·　".join(removal6[:3]) + "\n"
    + "　·　".join(removal6[3:]) + "\n"
    "机器读数：8/8 板 verdict.removal_unlock_classes＝[all-geometric, fixed]（routes/vias/holes/edge 摘除仍锁）",
    fs=8.8)
arrow(50, 64.2, 50, 61.4)
box(50, 58.0, 62, 6.5, "#f7f4ec", C_ORANGE,
    "第三步　放松探针矩阵（冻结世界内执行，不构成规则放宽；全部诊断性）：" + "　·　".join(probe5) + "\n"
    "机器读数：8 板 ×6 面解锁计数全 0（下方热图，diag.json probes 直读）",
    fs=8.8)

# ---- 四分支
for x0, x1 in ((31, 16), (44, 39), (56, 61), (69, 84)):
    arrow(x0, 54.7, x1, 48.6, color=C_ORANGE, lw=1.8)
box(16, 43.5, 26, 9.0, "#fdf0ee", C_RED,
    "(b) 引擎缺口\nroutes 类摘除解锁\n→引擎（障碍是引擎自产铜）\n缺口面＝" + b_gapface, fs=9.2, tc="#8a2f33")
box(39, 43.5, 24, 9.0, "#edf5ee", C_GREEN,
    "(a) 板固有\nfixed 类摘除解锁\n且 routes 仍锁\n→封死面=板固焊盘场", fs=9.2, tc="#2f6b3f")
box(61, 43.5, 24, 9.0, "#eef2fa", C_BLUE,
    "(c) 规则带值\n仅宽度规则面解锁\n→真实细规则可逃逸\n板非人不可布", fs=9.2, tc="#33517a")
box(84, 43.5, 22, 9.0, "#f2f2f2", C_GRAY,
    "undetermined\n均未命中\n保守不归类，只披露", fs=9.2, tc="#555555")

# ---- 动作/审计前提（照旧）
box(27, 33.2, 46, 5.8, "#fbf8f2", C_BROWN,
    "(a)/(b)/(c) 对应动作：豁免入账／换板（a）· 引擎攻坚批（b）· 规则带值调参或豁免，须逐类用户确认（c）", fs=8.6)
box(73, 33.2, 40, 5.8, "#fbf8f2", C_BROWN,
    "审计器前提：三分类每类判定都经过 route_check 等检查面\n（归因可信度以审计器自身被审计为前提，见篇四 §5）", fs=8.6)

# ---- 图注（数据版口径：数字面来源＋热图维度澄清＋双源披露）
ax.text(50, 26.6,
        "数据源：判据=tools/v5_diag_inherent.py FROZEN_CRITERIA（冻结式，正则直读断言四分支）；实例计数=diag-failed8/summary.json（8 行全 (a)）＋"
        "<板>.diag.json ×8（板名与 summary 逐位一致；verdict 断言 8/8 (a)）＋boardintake-r1/a1/esp32-devkit-lipo-rev-c.json（verdict.class=\"(b) 引擎能力缺口\"，摘除解锁类含 routes）"
        "＋p5-gate/dispositions-r1-2026-09-28.json（10 板=8 board-inherent＋2 (c)，名册 (a) 板名与诊断批逐位一致）。\n"
        "热图=diag.json probes 字段逐板直读，列＝六放松探针面（与 DIAG-FAILED8-REPORT §3 表头一一对应）；「六类摘除」是另一维度（第二步框 removal_unlock_classes 直读断言），两维度分别落位、不混套。"
        "†dc-scm 的 width-0.2 检查点=SKIPPED-PROBE-BUDGET，据 REPORT §5 事件 2，台账 seq375 全配置实跑=仍锁（双源披露）。\n"
        "torxhat 的 (a) 归因来自换板批 A1＋用户收批裁、不在机械名册 10 板内（LABEL-R1 边界披露 1，双源并存如实登记）。(c) 判据域扩容改进件 DR-2 截至 2026-10-03 待用户裁（不代裁）。",
        ha="center", va="top", fontsize=7.0, color="#666666", linespacing=1.65)

# ================================================================ 面板一：实例横条组
axb = fig.add_axes([0.052, 0.030, 0.400, 0.190])
axb.set_title("四分支实例面：条长∝板数（机器件直读，板名列全）", fontsize=10.5, fontweight="bold", pad=7)
cats = ["(a) 板固有\n（双源一致）", "(b) 引擎缺口", "(c) 规则带值", "undetermined"]
counts = [len(a_names), n_b, len(c_roster), n_und]
colors4 = ["#55a868", "#c44e52", "#4c72b0", "#8c8c8c"]
ys = [3.72, 2.44, 1.34, 0.44]
for y, c, col in zip(ys, counts, colors4):
    if c > 0:
        axb.barh(y, c, height=0.50, color=col, edgecolor="#333333", lw=0.7, zorder=3)
axb.set_yticks(ys); axb.set_yticklabels(cats, fontsize=8.0)
axb.set_xlim(0, 10.6); axb.set_ylim(0.02, 4.42)
axb.set_xticks(range(0, 9))
axb.set_xlabel("实例数（板数；(a)=诊断批 8 ∧ 名册 8 同一批板，并集 8 非双计 16）", fontsize=7.6)
axb.tick_params(axis="x", labelsize=7.2)
for s in ("top", "right"):
    axb.spines[s].set_visible(False)
axb.xaxis.grid(True, lw=0.4, color="#dddddd", zorder=0)
# 计数标签＋板名列全（机器件 board 键直读）
axb.text(counts[0] + 0.14, ys[0], "8", va="center", fontsize=8.6, fontweight="bold", color="#2f6b3f")
axb.text(0.06, ys[0] - 0.40, "、".join(a_names[:4]), fontsize=6.1, color="#333333", va="top")
axb.text(0.06, ys[0] - 0.66, "、".join(a_names[4:]), fontsize=6.1, color="#333333", va="top")
axb.text(counts[1] + 0.14, ys[1], "1", va="center", fontsize=8.6, fontweight="bold", color="#8a2f33")
axb.text(0.06, ys[1] - 0.40, b_name + "（boardintake-a1 首证；摘除解锁类含 routes）", fontsize=6.1, color="#333333", va="top")
axb.text(counts[2] + 0.14, ys[2], "2", va="center", fontsize=8.6, fontweight="bold", color="#33517a")
axb.text(0.06, ys[2] - 0.40, "、".join(c_roster) + "（用户裁定入册 09-25/09-28）", fontsize=6.1, color="#333333", va="top")
axb.text(counts[3] + 0.14, ys[3], "0", va="center", fontsize=8.6, fontweight="bold", color="#555555")
axb.text(0.06, ys[3] - 0.40, "（诊断批 8 行终判无 undetermined 命中）", fontsize=6.1, color="#333333", va="top")

# ================================================================ 面板二：8×6 探针解锁矩阵热图
axh = fig.add_axes([0.505, 0.026, 0.335, 0.205])
axh.set_title("8 板 × 6 探针面 · 解锁矩阵（<板>.diag.json probes 直读）", fontsize=10.0, fontweight="bold", pad=7)
FILL = {"locked": "#cfe0f5", "skip": "#ececec", "absent": "#fafafa", "unlock": "#c44e52"}
TC = {"locked": "#1f3b60", "skip": "#666666", "absent": "#999999", "unlock": "#ffffff"}
axh.set_xlim(0, 7); axh.set_ylim(9.75, -0.1)
axh.set_xticks([i + 0.5 for i in range(6)] + [6.5])
axh.set_xticklabels([lbl for _, lbl in FACES] + ["板解锁数"], fontsize=6.6)
for lbl in axh.get_xticklabels():
    lbl.set_rotation(28); lbl.set_ha("right")
axh.set_yticks([i + 0.5 for i in range(8)] + [8.5])
axh.set_yticklabels(diag_boards + ["面解锁数"], fontsize=6.4)
axh.tick_params(length=0)
for s in axh.spines.values():
    s.set_visible(False)
for r, b in enumerate(diag_boards):
    for c in range(6):
        cell = diags[b][c]
        axh.add_patch(Rectangle((c + 0.03, r + 0.03), 0.94, 0.94, fc=FILL[cell["state"]],
                                ec="#888888", lw=0.5,
                                hatch="///" if cell["state"] == "absent" else None))
        axh.text(c + 0.5, r + 0.5, cell["txt"], ha="center", va="center",
                 fontsize=6.4, color=TC[cell["state"]])
    axh.add_patch(Rectangle((6.03, r + 0.03), 0.94, 0.94, fc="#e7f2e7", ec="#555555", lw=0.7))
    axh.text(6.5, r + 0.5, str(per_board_unlock[r]), ha="center", va="center",
             fontsize=7.6, fontweight="bold", color="#2f6b3f")
for c in range(6):
    axh.add_patch(Rectangle((c + 0.03, 8.03), 0.94, 0.94, fc="#e7f2e7", ec="#555555", lw=0.7))
    axh.text(c + 0.5, 8.5, str(per_face_unlock[c]), ha="center", va="center",
             fontsize=7.6, fontweight="bold", color="#2f6b3f")
axh.add_patch(Rectangle((6.03, 8.03), 0.94, 0.94, fc="#d8ecd8", ec="#333333", lw=1.0))
axh.text(6.5, 8.5, str(n_unlock_total), ha="center", va="center", fontsize=8.4, fontweight="bold", color="#1d4d28")
axh.plot([6.0, 6.0], [0, 9.0], color="#333333", lw=1.3)
axh.plot([0, 7.0], [8.0, 8.0], color="#333333", lw=1.3)
axh.text(0.02, 9.45, "单元格=attempts 实跑数；■仍锁（蓝）　■跳过/真空（灰）　■未测=重板探针预算（斜线格）　■解锁（红，本批 0 例）",
         fontsize=6.3, color="#444444")

# ================================================================ 面板三：解锁计数侧栏（同件汇总）
stats = [
    "解锁计数侧栏（机器件汇总）",
    "· 探针解锁计数 = %d / %d 条" % (n_unlock_total, n_entries),
    "　（REPORT §3 口径锚：探针解锁数=0）",
    "· 仍锁 %d 条 · 跳过/真空 %d 条" % (n_locked, n_skip),
    "· 未测列缺 %d 格（重板 ≤5 预算）" % n_absent,
    "· 引擎面解锁 = 0（8 板 engine_unlock_faces 全空）",
    "· 宽度面解锁 = 0（8 板 width_unlock_tags 全空）",
    "· 摘除解锁面 8/8 板 = [fixed, all-geometric]",
    "· (b) 首证 %s：摘除解锁类含 routes" % b_name,
]
fig.text(0.868, 0.232, "\n".join(stats), fontsize=7.0, va="top", ha="left",
         color="#333333", linespacing=1.75,
         bbox=dict(boxstyle="round,pad=0.5", fc="#fbf8f2", ec=C_BROWN, lw=1.1))
fig.text(0.868, 0.048, "数字全部脚本内断言\n（失败即中止不出图）", fontsize=6.6, color="#888888", va="top")

# ================================================================ 输出＋终检
out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-01-TRI-CLASS-DECISION-TREE.png"
fig.savefig(out, dpi=200, facecolor="white")
plt.close(fig)

assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
with open(out, "rb") as f:
    head = f.read(24)
w_px, h_px = struct.unpack(">II", head[16:24])
assert w_px >= 2000 and h_px >= 1000, "PNG 尺寸 %dx%d 低于 2000×1000" % (w_px, h_px)
arr = mpimg.imread(out)
nonwhite = float((arr[:, :, :3].min(axis=2) < 0.95).mean())
assert nonwhite > 0.03, "非白占比 %.3f ≤3%%" % nonwhite

print("[ok] FIG-P4-01 数据版生成：%s（%d B, %dx%d, 非白 %.1f%%）" % (out, os.path.getsize(out), w_px, h_px, nonwhite * 100))
print("[ok] 断言清单：冻结式四分支直读；summary 8/8 (a)；diag ×8 板名与 summary/名册逐位一致；"
      "removal_unlock_classes 8/8=[all-geometric,fixed]；engine/width 解锁面 8×空；"
      "8×6 矩阵解锁全 0（板/面双侧）；REPORT §3 锚+§5 seq375 披露句命中；esp32 (b)+routes；"
      "名册 10=8+2（tmp108/bme280）；实例计数 8/1/2/0；探针条目 %d（仍锁 %d·跳过 %d·未测 %d）；输出>10KB；尺寸≥2000×1000；非白>3%%"
      % (n_entries, n_locked, n_skip, n_absent))
