# -*- coding: utf-8 -*-
"""
篇三 图①（数据版）：V5 确定性布线引擎五层架构图——版本/LOC/四树锚/测试面数字面。

与旧版（纯结构示意）的差别：每个数字面直读机器件并断言——
  1) 七组件版本＝源码直读（正本）：v5/ 与 tools/ 源文件版本常量正则解析；
  2) 论文表 1（P3 §3.4）程序化解析＝定格对照（对账正本=DISPATCH-LOG 各收口节）；
  3) LOC＝各组件源文件行数（程序化计数）；
  4) 四树锚＝out/v5-p5/r1/world-code-closeout.json（定格 2026-09-25）×
     现树重算（out/v5-p5/r1/_snap4.py 同算法：全文件 sha256 聚合取前 16 位，排除 __pycache__）；
  5) 测试面＝out/paper-program-r2/caliber-r1/c3_pytest_collect.json（C-3 定论口径）。

口径披露（重要）：V5-R7/R8（2026-10-04/05 收口）晚于论文表 1 定格（批④，2026-10-02），
源码 6/7 组件版本与四树哈希已前进——任务书「源码版本==表 1×7」「四树重算==closeout」
两条断言今日不可能通过。本图按任务书「源码是正本，论文是对照」条款双轨呈现两时点
真值，漂移程序化计算入图如实披露，不伪造断言通过；表 1 是否随 R7/R8 rebase 待主审裁。

断言层：层名×6 与三态锚命中 §3.1；表 1 七行==expect×7（表 1 现文仍=批④定格值）；
定格批列 7/7；源码版本解析×7；LOC>0×7＋schemas 合计>0；四树重算产出 4 键；
c3 算术锚（collected==p+s；Σper_file==T_now；T_now−Σ今日新增==collected；
collected−批④新钉==批③ logged；rc==0）；输出存在>10KB；PNG≥2000×1000（IHDR 直读）。

绘图纪律：显式 add_axes 固定画布（不用 tight_layout/bbox_inches=tight——二者叠加
曾致画布外扩 4372px、右列版面整体错位）；长文本程序化折行；中文＋Agg＋unicode_minus=False。
"""
import hashlib
import json
import os
import re
import struct

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

ROOT = "<ENGINE_ROOT>"
PAPER = ROOT + "/out/paper-program-r2/P3-V5-ENGINE-R2-2026-10-03.md"
CLOSEOUT = ROOT + "/out/v5-p5/r1/world-code-closeout.json"
C3 = ROOT + "/out/paper-program-r2/caliber-r1/c3_pytest_collect.json"
OUT = ROOT + "/out/paper-program-r2/figs/FIG-P3-01-ENGINE-FIVE-LAYER-ARCH.png"

# ---- 数据件直读 ----
text = open(PAPER, encoding="utf-8").read()

# §3.1 五层链（层名+职责锚短语逐层命中断言，照旧保留）
sec31 = text.split("### 3.1 五层与三态证书")[1].split("### 3.2")[0]
chain = [
    ("canonical schema", "board.v1 / failcert.v1 跨文件＋文件内 $ref 三态，fail-closed 拒绝未登记形态"),
    ("adapter", "KiCad .kicad_pcb → board.v1"),
    ("executor", "A*＋106 计划阶梯细化＋逃逸双阶段＋ripup"),
    ("route_check", "三重审计：routes 合同/网内一致性/层连通"),
    ("drc", "单源静态扫描"),
    ("kicad 导出器", "round-trip 合同"),
]
for name, duty in chain:
    assert name.split()[0] in sec31, f"层名未在 §3.1 命中: {name}"
assert "三态证书" in sec31 and "fail-closed" in sec31
assert "三态实锚 SAT=adv-02/UNSAT=demo-01/UNKNOWN=adv-03" in sec31, "三态证书实锚原文未命中"

# §3.4 表 1（定格对照面；对账正本=DISPATCH-LOG 各收口节）
sec34 = text.split("### 3.4 版本总表")[1].split("## 4 世界合同")[0]
rows = re.findall(r"^\| (\w+) \| \*\*(.+?)\*\*", sec34, re.M)
ver = dict(rows)
assert len(rows) == 7, f"表 1 组件行数 {len(rows)} != 7"
fixed = {}
for line in sec34.splitlines():
    if not line.startswith("| ") or line.startswith("| 组件") or line.startswith("|---"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) >= 3 and cells[0] in ("executor", "route_check", "drc", "adapter",
                                        "runner", "kicad_export", "diag_inherent"):
        fixed[cells[0]] = cells[2]
assert len(fixed) == 7, f"定格批列解析 {len(fixed)} != 7"
expect = {
    "executor": "v5.executor/0.9.0",
    "route_check": "v5.route_check/0.4.1",
    "drc": "v5.drc/0.3.0",
    "adapter": "0.4.0",
    "runner": "run_p5_board 0.5.0",
    "kicad_export": "0.5.0",
    "diag_inherent": "v5.diag_inherent/1.1.1",
}
for k, v in expect.items():
    assert k in ver, f"表 1 缺组件 {k}"
    assert ver[k] == v, f"{k} 表 1 值 {ver[k]!r} != {v!r}"

# ---- 七组件源码直读（正本）：版本常量正则＋LOC 行数 ----
SRC = {
    "executor":      ("v5/executor.py",               r'^EXECUTOR_VERSION = "([^"]+)"'),
    "route_check":   ("v5/route_check.py",            r'^ROUTE_CHECK_VERSION = "([^"]+)"'),
    "drc":           ("v5/drc.py",                    r'^VERSION = "([^"]+)"'),
    "adapter":       ("v5/adapters/kicad_adapter.py", r'ADAPTER_NAME = "([^"]+)"'),
    "runner":        ("tools/run_p5_board.py",        r'^VERSION = "([^"]+)"'),
    "kicad_export":  ("v5/kicad_export.py",           r'^VERSION = "([^"]+)"'),
    "diag_inherent": ("tools/v5_diag_inherent.py",    r'^TOOL_VERSION = "([^"]+)"'),
}
COMPS = ["executor", "route_check", "drc", "adapter", "runner", "kicad_export", "diag_inherent"]
src_ver, loc = {}, {}
for comp, (rel, pat) in SRC.items():
    txt = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(pat, txt, re.M)
    assert m, f"源码版本常量未命中: {rel} ({pat})"
    src_ver[comp] = m.group(1)
    loc[comp] = len(txt.splitlines())
    assert loc[comp] > 0, f"LOC<=0: {rel}"
schemas_dir = os.path.join(ROOT, "schemas")
schemas_files = sorted(f for f in os.listdir(schemas_dir) if f.endswith(".json"))
schemas_loc = sum(len(open(os.path.join(schemas_dir, f), encoding="utf-8")
                     .read().splitlines()) for f in schemas_files)
assert schemas_loc > 0 and len(schemas_files) == 5, "schemas 树件数/行数异常"


def triple(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s)
    return tuple(int(g) for g in m.groups())


drift_ver = [c for c in COMPS if triple(src_ver[c]) != triple(ver[c])]
match_ver = [c for c in COMPS if c not in drift_ver]
print(f"[披露] 源码==表1 一致 {len(match_ver)}/7: {match_ver}；漂移 {len(drift_ver)}/7:")
for c in drift_ver:
    print(f"       {c}: 表1定格 {ver[c]} -> 源码现读 {src_ver[c]}")

# ---- 四树锚：closeout 定格 × 现树重算（_snap4 同算法，只读）----
def tree_code(t):
    lines = []
    for dp, dns, fns in os.walk(t):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for fn in fns:
            p = os.path.join(dp, fn)
            rp = os.path.relpath(p, t).replace(os.sep, "/")
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            lines.append(f"{rp}:{h}")
    lines.sort()
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()[:16], len(lines)


closeout = json.load(open(CLOSEOUT, encoding="utf-8"))
TREES = ["v5", "tests", "tools", "schemas"]
tree_now = {t: tree_code(os.path.join(ROOT, t)) for t in TREES}
assert set(tree_now) == set(closeout["trees"]) == set(TREES), "四树键不齐"
tree_drift = [t for t in TREES if tree_now[t] != tuple(closeout["trees"][t])]
print(f"[披露] 四树重算==closeout：{'全部一致' if not tree_drift else '漂移 ' + str(len(tree_drift)) + '/4: ' + str(tree_drift)}")
for t in TREES:
    cs, cn = closeout["trees"][t]
    ns, nn = tree_now[t]
    print(f"       {t}: closeout {cs}/{cn} -> 现树 {ns}/{nn}")

# ---- 测试面：c3_pytest_collect.json（C-3 定论口径）----
c3 = json.load(open(C3, encoding="utf-8"))
rec = c3["reconciliation"]
col_key = [k for k in rec if k.startswith("批④_collected_logged")][0]
b3_key = [k for k in rec if k.startswith("批③_collected_logged")][0]
collected = rec[col_key]
m = re.search(r"\((\d+)p\+(\d+)s\)", col_key)
passed, skipped = int(m.group(1)), int(m.group(2))
t_now = rec["T_now_whole_tree"]
today_added = rec["today_added"]
added_sum = sum(today_added.values())
n_files = len(c3["per_file"])
n_sum = sum(v["n"] for v in c3["per_file"].values())
b4_new = sum(rec["batch4_new_file"].values())
b3_logged = rec[b3_key]
assert collected == passed + skipped, "c3: collected != passed+skipped"
assert n_sum == t_now, "c3: Σper_file != T_now"
assert t_now - added_sum == collected, "c3: T_now−Σ今日新增 != collected"
assert collected - b4_new == b3_logged, "c3: closure_B 算术不闭合"
assert c3["whole_tree_rc"] == 0, "c3: whole_tree_rc != 0"

# ---- 绘图（固定画布：显式 add_axes，不用 tight_layout / bbox_inches=tight）----
fig = plt.figure(figsize=(16.5, 11.2), dpi=220)
ax = fig.add_axes([0.012, 0.012, 0.976, 0.938])
ax.set_xlim(0, 16.5)
ax.set_ylim(0, 11.2)
ax.axis("off")

colors = ["#BFD8E8", "#C9E2C5", "#F5CBA7", "#E8DAEF", "#F9E79F", "#FADBD8"]
BOX_X, BOX_W, BOX_H, STEP, TOP = 1.05, 7.1, 1.24, 1.52, 9.9
layer_comp = [None, "adapter", "executor", "route_check", "drc", "kicad_export"]
loc_max = max(list(loc.values()) + [schemas_loc])

for i, (name, duty) in enumerate(chain):
    top = TOP - i * STEP
    ax.add_patch(FancyBboxPatch((BOX_X, top - BOX_H), BOX_W, BOX_H,
                                boxstyle="round,pad=0.06", fc=colors[i], ec="#34495e", lw=1.3))
    comp = layer_comp[i]
    if comp is None:
        src_txt, loc_n, loc_path = f"schemas 树 {len(schemas_files)} 件", schemas_loc, "schemas/*.json"
        paper_txt, judge = "—", ""
    else:
        src_txt, loc_n, loc_path = src_ver[comp], loc[comp], SRC[comp][0]
        paper_txt = ver[comp]
        judge = "一致" if comp in match_ver else "▲漂移"
    ax.text(BOX_X + 0.22, top - 0.30, f"第 {i + 1} 层 · {name}", fontsize=11.5,
            fontweight="bold", va="center")
    ax.text(BOX_X + BOX_W - 0.15, top - 0.30, f"现读 {src_txt}　{judge}",
            fontsize=9.2, fontweight="bold", color="#154360", va="center", ha="right")
    ax.text(BOX_X + 0.22, top - 0.62, duty, fontsize=8.6, color="#1b2631", va="center")
    ax.text(BOX_X + BOX_W - 0.15, top - 0.62, f"表 1 定格 {paper_txt}",
            fontsize=8.2, color="#7d3c98", va="center", ha="right")
    bw = loc_n / loc_max * 3.3
    ax.add_patch(Rectangle((BOX_X + 0.25, top - 1.04), bw, 0.22,
                           fc="#154360", ec="none", alpha=0.75))
    ax.text(BOX_X + 0.25 + bw + 0.12, top - 0.93, f"LOC {loc_n}（{loc_path}）",
            fontsize=8.2, va="center", color="#154360")
    if i < len(chain) - 1:
        ax.add_patch(FancyArrowPatch((4.6, top - BOX_H - 0.02), (4.6, top - STEP + 0.02),
                                     mutation_scale=16, arrowstyle="-|>", color="#154360", lw=1.8))

ax.text(4.6, 10.72, "KiCad .kicad_pcb 板输入（真实板＋合成板域）", fontsize=10.5,
        ha="center", color="#154360")
ax.add_patch(FancyArrowPatch((4.6, 10.52), (4.6, TOP + 0.02), mutation_scale=16,
                             arrowstyle="-|>", color="#154360", lw=1.8))
ax.text(4.6, 0.78, "routes/canonical 产物（round-trip 合同，双跑字节等）", fontsize=10.5,
        ha="center", color="#154360")
ax.text(4.6, 0.50, "运行层终态：FAILED（exhaustion-cause 归因）/ ROUTED", fontsize=8.6,
        ha="center", color="#7b241c")

# 三态证书侧栏（§3.1 实锚照旧）
ax.add_patch(FancyBboxPatch((0.18, 1.1), 0.55, 8.8, boxstyle="round,pad=0.05",
                            fc="#FDF2E9", ec="#935116", lw=1.2))
ax.text(0.36, 9.72, "证书层三态", fontsize=11, fontweight="bold", rotation=90,
        ha="center", va="top", color="#935116")
for yy, st in zip([8.6, 6.6, 4.6], ["SAT 全端点连通且审计全过", "UNSAT 带独立复核失败证书",
                                    "UNKNOWN 资源耗尽 fail-closed"]):
    ax.text(0.66, yy, st, fontsize=8.8, rotation=90, va="center", ha="center", color="#935116")

RX, RW = 8.55, 7.5
# 口径披露条（程序化注入漂移计数）
ax.add_patch(FancyBboxPatch((RX, 9.42), RW, 0.68, boxstyle="round,pad=0.05",
                            fc="#FDEDEC", ec="#943126", lw=1.1))
ax.text(RX + 0.15, 9.94, f"口径披露：V5-R7/R8（2026-10-04/05 收口）晚于表 1 定格（批④ 2026-10-02）——"
        f"源码 {len(drift_ver)}/7 组件版本、四树 {len(tree_drift)}/4 已前进。",
        fontsize=7.4, va="center", color="#7b241c")
ax.text(RX + 0.15, 9.60, "本图按「源码正本×表 1 定格」双轨呈现；「源码==表 1」「四树==closeout」"
        "两断言今日不可过，如实披露不伪造；表 1 rebase 待主审裁。",
        fontsize=7.4, va="center", color="#7b241c")

# 面板 A：七组件版本对账表
ax.text(RX + 0.15, 9.12, "七组件版本对账（源码直读＝正本 × 论文表 1＝定格）", fontsize=11,
        fontweight="bold", va="center", color="#154360")
cols = [(RX + 0.15, "组件"), (RX + 1.30, "源码现读（正本）"), (RX + 3.25, "表 1 定格"),
        (RX + 5.15, "LOC"), (RX + 5.95, "判定")]
for cx, htxt in cols:
    ax.text(cx, 8.78, htxt, fontsize=8, fontweight="bold", va="center", color="#34495e")
for j, comp in enumerate(COMPS):
    ry = 8.50 - j * 0.36
    if j % 2 == 1:
        ax.add_patch(Rectangle((RX + 0.05, ry - 0.13), RW - 0.1, 0.30, fc="#f4f6f7", ec="none"))
    ok = comp in match_ver
    ax.text(cols[0][0], ry, comp, fontsize=8, va="center")
    ax.text(cols[1][0], ry, src_ver[comp], fontsize=7.8, va="center",
            color="#154360", fontweight="bold")
    ax.text(cols[2][0], ry, ver[comp], fontsize=7.8, va="center", color="#7d3c98")
    ax.text(cols[3][0], ry, str(loc[comp]), fontsize=7.8, va="center")
    ax.text(cols[4][0], ry, "一致" if ok else "▲漂移", fontsize=7.8, va="center",
            color="#1e8449" if ok else "#c0392b", fontweight="bold")
fixed_items = [f"{c}={fixed[c]}" for c in COMPS]
for li in range(0, len(fixed_items), 3):
    ax.text(RX + 0.15, 6.02 - li / 3 * 0.20, ("定格批（表 1 列 3）：" if li == 0 else "")
            + " ｜ ".join(fixed_items[li:li + 3]), fontsize=6.2, va="center", color="#5d6d7e")
path_items = [f"{SRC[c][0]} {loc[c]} 行" for c in COMPS]
for li in range(0, len(path_items), 4):
    ax.text(RX + 0.15, 5.42 - li / 4 * 0.20, ("LOC 源文件：" if li == 0 else "")
            + " ｜ ".join(path_items[li:li + 4])
            + (f" ｜ schemas/*.json×{len(schemas_files)} 合计 {schemas_loc} 行"
               if li + 4 >= len(path_items) else ""),
            fontsize=6.2, va="center", color="#5d6d7e")

# 面板 B：四树锚
ax.text(RX + 0.15, 5.02, "四树锚面板（sha16/文件数：closeout 定格 × 现树重算）", fontsize=11,
        fontweight="bold", va="center", color="#154360")
for cx, htxt in [(RX + 0.15, "树"), (RX + 1.05, "closeout 定格（2026-09-25）"),
                 (RX + 3.95, "现树重算（_snap4 同算法）"), (RX + 6.65, "判定")]:
    ax.text(cx, 4.70, htxt, fontsize=8, fontweight="bold", va="center", color="#34495e")
for j, t in enumerate(TREES):
    ry = 4.40 - j * 0.42
    cs, cn = closeout["trees"][t]
    ns, nn = tree_now[t]
    ok = (cs, cn) == (ns, nn)
    ax.text(RX + 0.15, ry, t, fontsize=8.2, va="center", fontweight="bold")
    ax.text(RX + 1.05, ry, f"{cs}/{cn}", fontsize=7.8, va="center", color="#7d3c98")
    ax.text(RX + 3.95, ry, f"{ns}/{nn}", fontsize=7.8, va="center", color="#154360")
    ax.text(RX + 6.65, ry, "一致" if ok else "漂移", fontsize=7.8, va="center",
            color="#1e8449" if ok else "#c0392b", fontweight="bold")
ax.text(RX + 0.15, 2.62, "重算＝全文件 sha256 聚合取前 16 位（排除 __pycache__）；"
        "closeout＝out/v5-p5/r1/world-code-closeout.json（V5-R1 收口）",
        fontsize=6.6, va="center", color="#5d6d7e")

# 面板 C：测试面 chip（C-3 定论口径）
ax.add_patch(FancyBboxPatch((RX, 0.42), RW, 2.0, boxstyle="round,pad=0.06",
                            fc="#EAF2F8", ec="#1f618d", lw=1.2))
ax.text(RX + 0.15, 2.18, "测试面（c3_pytest_collect.json；C-3 定论口径）", fontsize=10.5,
        fontweight="bold", va="center", color="#1f618d")
ax.text(RX + 0.15, 1.80, f"{collected} collected ＝ {passed} passed ＋ {skipped} skipped",
        fontsize=13, fontweight="bold", va="center", color="#1f618d")
added_join = "＋".join(f"{k.split('/')[-1]} {v}" for k, v in today_added.items())
ax.text(RX + 0.15, 1.44, f"whole_tree_rc={c3['whole_tree_rc']} ｜ per_file {n_files} 件 ｜ "
        f"T_now {t_now} ＝ {collected} ＋ 今日新增 {added_sum}（{added_join}）",
        fontsize=8.0, va="center", color="#1b2631")
ax.text(RX + 0.15, 1.14, f"closure_B：{collected} − {b4_new}（批④新钉 contract 件）＝ {b3_logged} ＝ 批③ logged",
        fontsize=8.0, va="center", color="#1b2631")
ax.text(RX + 0.15, 0.80, "口径＝C-3 定论（2026-10-05 勘误「+13」混基相减；collected 与 passed＋skipped 同基）",
        fontsize=7.0, va="center", color="#5d6d7e")

ax.text(8.25, 0.16, "数据来源：七组件版本/LOC＝v5 与 tools 源码直读（现树 2026-10-05）；表 1 定格/定格批＝P3 §3.4 程序化解析；"
        "四树＝world-code-closeout.json＋同算法现树重算；测试面＝c3_pytest_collect.json",
        fontsize=6.8, ha="center", va="center", color="#5d6d7e")

ax.set_title("V5 确定性布线引擎五层架构（数据版：源码版本直读＋LOC＋四树锚＋测试面）\n"
             "层名/职责/三态锚＝§3.1 原文命中；版本＝源码正本×表 1 定格双轨；四树＝定格×现树重算双轨；测试计数＝C-3 定论",
             fontsize=14.5, fontweight="bold", pad=10)

fig.savefig(OUT)
plt.close(fig)

# ---- 输出断言 ----
assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
with open(OUT, "rb") as f:
    head = f.read(24)
assert head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR", "PNG 头异常"
w, h = struct.unpack(">II", head[16:24])
assert w >= 2000 and h >= 1000, f"PNG 尺寸 {w}x{h} <2000x1000"

print("OK FIG-P3-01 五层架构数据版", OUT, size, "bytes", f"{w}x{h}")
print("断言：层名×6/三态锚=过；表1七行==expect=过；定格批 7/7=过；源码版本解析×7=过；"
      "LOC>0×7+schemas=过；四树重算 4 键=过；c3 算术×5=过；>10KB=过；尺寸=过")
print(f"披露：源码==表1 → {len(match_ver)}/7 一致（{len(drift_ver)} 漂移）；四树重算==closeout → "
      f"{4 - len(tree_drift)}/4 一致（{len(tree_drift)} 漂移）——两断言不可过，双轨披露")
print("源码现读:", {c: src_ver[c] for c in COMPS})
print("现树四锚:", {t: f"{tree_now[t][0]}/{tree_now[t][1]}" for t in TREES})
print(f"测试面: {collected}={passed}p+{skipped}s rc={c3['whole_tree_rc']} 件数={n_files}")
