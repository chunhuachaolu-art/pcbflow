# -*- coding: utf-8 -*-
"""
FIG-P6-01 — P6 图 1（数据版）：两套动作合同对照（V6 九动作画板合同 vs V8 布线席位动作域）
＋台账用量数据面（提案动作直方图×受理/拒收计数）＋拒收-回叫-验证闭环＋FORCE 逐 run 计数。
数据源（机器件直读，禁硬编码数据点）：
  词表三源（现行保留）：
    1. canvas/protocol.py —— REQUIRED_KEYS 九动作（源码解析）
    2. canvas/CANVAS-API-CONTRACT.md —— §2 canvas-edit-v2 动作枚举表（双源互证）
    3. net_agent_pilot/pilot.py —— V8 席位台账动作域 / --prior-rejection 回叫 / via 面投影图例
  用量面（本批新增）：
    4. out/canvas-toolchain/act-*/ledger-*.jsonl —— V6 侧台账（在盘自定位全并入）
       行语义：有 batch 键 → batch=提案全表（act-m2r3/act-clearance 等）；
       无 batch 键 → edit_list 为受理投影，提案全表由 accepted+rejected 按 index 重建
       （act-m4/m5 全受理行 edit_list 即提案；act-m2/m2r2/m3 有拒收行走重建）；
       verdict=batch-rejected 行为批级拒收（E_* 批级错误，无动作级投影，不入动作直方图）。
    5. out/net-agent-p1/run{5,6,8,9,12}/ledger.jsonl —— V8 侧台账（batch=提案全表）；
       run10/11/13 无 ledger.jsonl（在盘核验为缺，如实记缺不入）。
    6. out/net-agent-p1/run*/rounds/FORCE-*/proposal.json —— FORCE 前缀提案件逐 run 计数
       （run5 首例 ETH，FORCE 目录不入席位 ledger，grep=0 已核）。
断言：九动作双源一致（现行全套保留）＋提案直方图与逐条重数一致＋逐类受理+拒收==提案计数
  ＋两线总动作数>0＋FORCE run5==1 且首例名含 ETH＋输出>10KB。
"""
import ast
import glob
import json
import os
import re
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-01-ACTION-CONTRACT-V6-V8.png")

# ================= 词表三源直读（现行保留） =================
# 源 1：九动作词表（canvas/protocol.py REQUIRED_KEYS，源码解析非手抄）
proto_src = open(os.path.join(REPO, "canvas/protocol.py"), encoding="utf-8").read()
m = re.search(r"REQUIRED_KEYS = \{(.*?)\n\}", proto_src, re.S)
assert m, "protocol.py REQUIRED_KEYS 未定位"
required = ast.literal_eval("{" + m.group(1) + "}")
assert len(required) == 9, f"九动作数 {len(required)} != 9"
assert set(required) == {"route", "via", "ripup", "width_class", "move",
                          "rotate", "flip", "tuning", "submit"}, sorted(required)

# 源 2：合同 §2 表（CANVAS-API-CONTRACT.md，双源互证）
contract = open(os.path.join(REPO, "canvas/CANVAS-API-CONTRACT.md"), encoding="utf-8").read()
tbl = re.search(r"## 2\. canvas-edit-v2 动作枚举.*?\n(.*?)\n\n", contract, re.S).group(1)
contract_actions = [ln.split("|")[1].strip() for ln in tbl.splitlines()
                    if ln.startswith("|") and ln.split("|")[1].strip() not in ("动作", "") and
                    not set(ln.split("|")[1].strip()) <= {"-", ":"}]
assert set(contract_actions) == set(required), "合同 §2 表与 REQUIRED_KEYS 不一致"
reject_codes_line = [l for l in contract.splitlines() if l.strip().startswith("V_CLEARANCE/V_EDGE")][0]
n_v2_codes = len(re.findall(r"V_[A-Z_]+", reject_codes_line))

# 源 3：V8 席位台账动作域（pilot.py 源文解析）
pilot = open(os.path.join(REPO, "net_agent_pilot/pilot.py"), encoding="utf-8").read()
ms = re.search(r"route/via/ripup/submit", pilot)
assert ms, "pilot.py 席位台账动作域文本未定位"
v8_domain = set(ms.group(0).split("/"))
v8_domain = {a for a in v8_domain if a.isalpha()}
assert v8_domain == {"route", "via", "ripup", "submit"}, v8_domain
assert '"--prior-rejection"' in pilot or "--prior-rejection" in pilot, "回叫参数未定位"
prior_help = re.search(r'"上轮 result\.json 路径（回叫简报嵌入拒收记录）"', pilot)
assert prior_help, "--prior-rejection help 文本未定位"
assert "+ 格 = 走线可过" in pilot, "via 面投影图例未定位（0.3.2 地图语义）"

print(f"[read] 九动作={sorted(required)}")
print(f"[read] V8 席位动作域={sorted(v8_domain)}（pilot 台账动作域，其余动作 fail-closed）")
print(f"[read] 合同 v1+追加拒收码词表条数（§1 列举）≈ {n_v2_codes}（追加式、只增不改义）")

# ================= 用量面：台账直读（提案全表口径） =================
# 直方图显示序（布局选择；断言其为词表排列）
ORDER = ["route", "via", "ripup", "width_class", "move", "rotate", "flip", "tuning", "submit"]
assert set(ORDER) == set(required) and len(ORDER) == 9
CN = {"route": "走线", "via": "过孔", "ripup": "撤铜", "width_class": "网宽档",
      "move": "分区移动", "rotate": "旋转", "flip": "翻面", "tuning": "等长调参", "submit": "批末提交"}


def tally_ledger(rows, label):
    """提案全表口径统计：返回 (prop_by, acc_by, rej_by, batch_rej_rows, n_prop_rows)。
    每行提案全表 P：有 batch 键→batch；无 batch 且 rejected 空→edit_list；
    无 batch 且 rejected 非空→accepted+rejected 按 index 重建（edit_list=受理投影）。
    逐行 invariant 断言；直方图双路计数（流式 Counter vs 重数列表）事后对账。"""
    prop_by, acc_by, rej_by = Counter(), Counter(), Counter()
    batch_rej_rows = 0
    raw_action_words = []  # 重数路径：全部提案动作词摊平
    for r in rows:
        vd = r.get("verdict", "?")
        acc, rej = r.get("accepted", []), r.get("rejected", [])
        if vd == "batch-rejected":  # 批级拒收：无动作级投影
            assert r.get("edit_list", []) == [] and r.get("batch", []) == [] and acc == [], \
                f"{label} 批级拒收行结构异常: {sorted(r.keys())}"
            assert len(rej) == 1 and rej[0].get("index") is None, f"{label} 批级拒收行 rejected 异常"
            batch_rej_rows += 1
            continue
        assert vd == "applied", f"{label} 未知 verdict={vd}"
        idx_all = [a.get("index") for a in acc] + [x.get("index") for x in rej]
        assert all(isinstance(i, int) for i in idx_all), f"{label} index 非整数"
        assert len(set(idx_all)) == len(idx_all), f"{label} index 重复"
        if "batch" in r:
            P = r["batch"]
            assert sorted(idx_all) == list(range(len(P))), \
                f"{label} accepted+rejected index 并集 != batch 全表 ({len(P)} vs {len(idx_all)})"
        elif not rej:
            P = r["edit_list"]
            assert sorted(a.get("index") for a in acc) == list(range(len(P))), \
                f"{label} 全受理行 accepted != edit_list 范围"
        else:
            P = [None] * (len(acc) + len(rej))
            for item in acc + rej:
                P[item["index"]] = item
            assert all(x is not None for x in P), f"{label} 重建提案有缺位"
            P = [{"action": x["action"]} for x in P]
        for x in P:
            prop_by[x["action"]] += 1
            raw_action_words.append(x["action"])
        for a in acc:
            acc_by[a["action"]] += 1
        for x in rej:
            rej_by[x["action"]] += 1  # 批级行已在上方 continue，此处均为动作级
    # 对账：直方图计数与逐条重数一致（两条独立计数路径）
    recount = Counter(raw_action_words)
    assert dict(prop_by) == dict(recount), f"{label} 直方图 {dict(prop_by)} != 重数 {dict(recount)}"
    # 对账：逐类 受理+拒收 == 提案（提案全表被逐条裁决）
    for k in prop_by:
        assert acc_by[k] + rej_by[k] == prop_by[k], \
            f"{label} {k}: 受理{acc_by[k]}+拒收{rej_by[k]} != 提案{prop_by[k]}"
    assert sum(prop_by.values()) == len(raw_action_words)
    return prop_by, acc_by, rej_by, batch_rej_rows


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


# ---- V6 侧：canvas act-* 全部在盘 ledger 自定位并入 ----
CT = os.path.join(REPO, "out/canvas-toolchain")
v6_files = sorted(glob.glob(os.path.join(CT, "act-*", "ledger-*.jsonl")))
assert v6_files, "canvas 侧 ledger 一件未定位"
v6_prop, v6_acc, v6_rej = Counter(), Counter(), Counter()
v6_brej = 0
v6_runs = sorted({os.path.relpath(f, CT).split(os.sep)[0] for f in v6_files})
for f in v6_files:
    p, a, r_, b = tally_ledger(load_jsonl(f), os.path.relpath(f, CT))
    v6_prop.update(p); v6_acc.update(a); v6_rej.update(r_); v6_brej += b
for k in v6_prop:  # 汇总层再对账
    assert v6_acc[k] + v6_rej[k] == v6_prop[k], f"V6 汇总 {k} 受理+拒收 != 提案"
v6_total = sum(v6_prop.values())

# ---- V8 侧：run5/6/8/9/12 ledger（batch=提案全表） ----
NP = os.path.join(REPO, "out/net-agent-p1")
V8_RUNS = ["run5", "run6", "run8", "run9", "run12"]  # 任务书点名清单（口径指定）
V8_ABSENT = ["run10", "run11", "run13"]              # 任务书点名「无 ledger 记缺不入」
v8_prop, v8_acc, v8_rej = Counter(), Counter(), Counter()
v8_brej = 0
for run in V8_RUNS:
    f = os.path.join(NP, run, "ledger.jsonl")
    assert os.path.exists(f), f"{run} ledger 意外缺失"
    p, a, r_, b = tally_ledger(load_jsonl(f), run)
    v8_prop.update(p); v8_acc.update(a); v8_rej.update(r_); v8_brej += b
for k in v8_prop:
    assert v8_acc[k] + v8_rej[k] == v8_prop[k], f"V8 汇总 {k} 受理+拒收 != 提案"
v8_total = sum(v8_prop.values())
absent_ok = [r for r in V8_ABSENT if not os.path.exists(os.path.join(NP, r, "ledger.jsonl"))]
assert absent_ok == V8_ABSENT, f"V8 缺件核验异常: 在盘 {set(V8_ABSENT) - set(absent_ok)}"
assert set(v8_prop) <= v8_domain, f"V8 台账出现域外动作 {set(v8_prop) - v8_domain}"

# ---- FORCE 计数：rounds/FORCE-*/proposal.json 逐 run ----
force = {}
force_names = {}
for run in V8_RUNS:
    dirs = sorted(glob.glob(os.path.join(NP, run, "rounds", "FORCE-*")))
    force[run] = sum(1 for d in dirs if os.path.isfile(os.path.join(d, "proposal.json")))
    force_names[run] = [os.path.basename(d) for d in dirs if os.path.isfile(os.path.join(d, "proposal.json"))]
assert force["run5"] == 1 and "ETH" in force_names["run5"][0], \
    f"FORCE run5 首例异常: {force_names['run5']}"
force_total = sum(force.values())
assert force_total == sum(force.values()) and force_total >= 1

# ---- 两线总动作数>0（任务书断言） ----
assert v6_total > 0 and v8_total > 0, f"总动作数 V6={v6_total} V8={v8_total}"

print(f"[read] V6 台账 {len(v6_files)} 件（{', '.join(v6_runs)}）: 提案 {v6_total} 动作 "
      f"受理 {sum(v6_acc.values())} 拒收 {sum(v6_rej.values())} 批级拒收 {v6_brej} 行")
print(f"[read] V6 提案直方图: {dict(v6_prop)}")
print(f"[read] V8 台账 {V8_RUNS}: 提案 {v8_total} 动作 受理 {sum(v8_acc.values())} "
      f"拒收 {sum(v8_rej.values())} 批级拒收 {v8_brej} 行")
print(f"[read] V8 提案直方图: {dict(v8_prop)}")
print(f"[read] FORCE 逐 run: {force}（合计 {force_total}；run10/11/13 无 ledger 如实记缺不入）")

# ================= 绘图（数据版） =================
fig, ax = plt.subplots(figsize=(15, 10), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, fc, ec="#333333", lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                                fc=fc, ec=ec, lw=lw))


def arrow(p1, p2, style="-|>", color="#333333", lw=1.6, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                                 color=color, lw=lw, linestyle=ls, shrinkA=2, shrinkB=2))


# ---- 顶部标题（数据版口径） ----
ax.text(50, 97.6, "两套动作合同对照＋台账用量：V6 画板直绘 vs V8 直布线（同一 canvas-edit-v2 fail-closed 底座）",
        ha="center", fontsize=14.5, fontweight="bold")
ax.text(50, 94.2, "数据版 · 动作词表三源直读互证（protocol.py REQUIRED_KEYS／合同 §2 表／pilot.py 动作域）；"
        f"用量面=台账逐行直读（V6 {len(v6_files)} 件 / V8 {len(V8_RUNS)} run，提案全表口径，逐行 index 对账后计数）",
        ha="center", fontsize=8.2, color="#555555")

# ---- 上带左：V6 九动作词表 ----
box(2, 52.5, 45, 38.5, "#eaf2fb")
ax.text(24.5, 88.6, "V6 画板直绘席位：九动作全词表（合同 §2）", ha="center",
        fontsize=11.5, fontweight="bold", color="#1a4f8b")
groups = [
    (75.0, "布线类", ["route 走线（整数格点折线）", "via 过孔（路径格点）", "ripup 撤铜（net_id/shape_id）"]),
    (64.0, "布局类", ["move 分区移动 · rotate 旋转（90°×turns）", "flip 翻面"]),
    (53.0, "调参/提交", ["width_class 网宽档 · tuning 等长调参", "（accordion/detour）· submit 批末提交（唯一收尾）"]),
]
for gy, gname, items in groups:
    box(4, gy, 41, 10.4, "#d7e6f7", ec="#7a9cc6", lw=0.8)
    ax.text(6, gy + 8.3, gname, fontsize=9, fontweight="bold", color="#1a4f8b")
    for j, it in enumerate(items):
        ax.text(7.5, gy + 5.6 - 2.4 * j, it, fontsize=8.2)
v6_seen = [a for a in ORDER if a in v6_prop]
v6_unseen = [a for a in ORDER if a not in v6_prop]

# ---- 上带右：V8 布线席位 ----
box(53, 52.5, 45, 38.5, "#fdf1e3")
ax.text(75.5, 88.6, "V8 直布线席位：台账动作域 4 动作（fail-closed）", ha="center",
        fontsize=11.5, fontweight="bold", color="#8b4a1a")
v8_items = [
    "route 单网走线（L 形展开、避 # 格）",
    "via 过孔（全层铜盘、via 面真值投影 +）",
    "ripup 撤铜（派生账本分叉） · submit 批末提交",
    "其余五动作（width_class/move/rotate/flip/tuning）＝席位面 fail-closed",
    "席位简报（0.5.x）：地图只是提示，机械验证器才是唯一裁决",
]
y = 84.6
for it in v8_items:
    ax.text(55.5, y, it, fontsize=8.4, color="#8b4a1a")
    y -= 3.4
box(55, 56.4, 41, 10.2, "#f7e0c8", ec="#c48850", lw=0.8)
ax.text(57, 64.6, "协议演进 0.3.0→0.5.1（载体=pilot.py）：", fontsize=8.2, fontweight="bold", color="#8b4a1a")
for i, t in enumerate(["0.3.1 F-bbox 披露 · 0.3.2 via 面投影", "0.5.0 debrief/PLAYBOOK · 0.5.1 ripup 重验披露"]):
    ax.text(57, 61.8 - 2.7 * i, t, fontsize=7.9)

# ---- 上带中缝：共享验证核 ----
box(46.9, 60, 6.2, 24, "#e8f5e9", ec="#4c8a54")
ax.text(50, 81.6, "共享验证核", ha="center", fontsize=9.2, fontweight="bold", color="#2c5e33")
ax.text(50, 77.4, "canvas-edit-v2\nparse_batch\nfail-closed", ha="center", fontsize=7.4, color="#2c5e33")
ax.text(50, 70.0, "v5.drc 同源绑定\n（Copper/间距/孔/\n禁布区/连通账本）", ha="center", fontsize=7.0, color="#2c5e33")
ax.text(50, 62.8, "拒收码词表追加式", ha="center", fontsize=7.0, color="#2c5e33")
arrow((45.4, 66), (46.9, 66)); arrow((53.1, 66), (54.4, 66))
ax.text(50, 56.8, "动作提案（纯 JSON 文件）", ha="center", fontsize=7.6, color="#333333")

# ---- 中带：V6 / V8 台账用量直方图 ----
C_ACC, C_REJ = "#3b78c4", "#c4534b"


def histogram(x0, y0, w, h, prop, acc, rej, title, sub, kinds):
    box(x0, y0, w, h, "#ffffff", ec="#888888", lw=1.0)
    ax.text(x0 + w / 2, y0 + h - 2.0, title, ha="center", fontsize=10.2, fontweight="bold")
    ax.text(x0 + w / 2, y0 + h - 4.6, sub, ha="center", fontsize=7.3, color="#555555")
    n = len(kinds)
    top, bottom = y0 + h - 6.6, y0 + 2.6
    slot = (top - bottom) / n
    bar_h = min(slot * 0.62, 1.9)
    lab_x = x0 + 1.4          # 动作标签区
    bar_a, bar_w = x0 + 9.6, w - 16.6   # 条起点与可用条宽
    mx = max(prop[k] for k in kinds)
    for i, k in enumerate(kinds):
        yc = top - slot * (i + 0.5)
        ax.text(lab_x, yc, f"{k}", fontsize=7.6, ha="left", va="center", fontweight="bold")
        ax.text(lab_x + 0.2, yc - slot * 0.34, CN[k], fontsize=6.2, ha="left", va="center", color="#666666")
        wa = bar_w * acc[k] / mx
        wr = bar_w * rej[k] / mx
        if wa > 0:
            ax.add_patch(FancyBboxPatch((bar_a, yc - bar_h / 2), wa, bar_h,
                                        boxstyle="square,pad=0", fc=C_ACC, ec="none"))
        if wr > 0:
            ax.add_patch(FancyBboxPatch((bar_a + wa + 0.25, yc - bar_h / 2), wr, bar_h,
                                        boxstyle="square,pad=0", fc=C_REJ, ec="none"))
        ax.text(bar_a + bar_w + 0.7, yc, f"受 {acc[k]} / 拒 {rej[k]}",
                fontsize=6.6, va="center", color="#333333")


v6_sub = (f"{len(v6_files)} 件 ledger 全并入 · 词表 9 类中出现 {len(v6_seen)} 类（未出现：{'、'.join(v6_unseen)}）· "
          f"提案 {v6_total}＝受理 {sum(v6_acc.values())}＋拒收 {sum(v6_rej.values())}（批级拒收 {v6_brej} 行不入谱）")
histogram(2, 28.5, 45, 21.5, v6_prop, v6_acc, v6_rej,
          "V6 侧台账用量：提案动作直方图（受理/拒收双色）", v6_sub, v6_seen)
v8_sub = (f"{'、'.join(V8_RUNS)} · 提案 {v8_total} ＝ 受理 {sum(v8_acc.values())} "
          f"＋ 拒收 {sum(v8_rej.values())}（批级拒收 {v8_brej} 行；run10/11/13 无 ledger 记缺不入）")
v8_seen = [a for a in ORDER if a in v8_prop]
histogram(53, 28.5, 45, 21.5, v8_prop, v8_acc, v8_rej,
          "V8 侧台账用量：提案动作直方图（受理/拒收双色）", v8_sub, v8_seen)
ax.add_patch(FancyBboxPatch((31.5, 29.3), 1.4, 0.9, boxstyle="square,pad=0", fc=C_ACC, ec="none"))
ax.text(33.2, 29.75, "受理", fontsize=6.4, va="center")
ax.add_patch(FancyBboxPatch((36.5, 29.3), 1.4, 0.9, boxstyle="square,pad=0", fc=C_REJ, ec="none"))
ax.text(38.2, 29.75, "拒收", fontsize=6.4, va="center")
ax.add_patch(FancyBboxPatch((82.5, 29.3), 1.4, 0.9, boxstyle="square,pad=0", fc=C_ACC, ec="none"))
ax.text(84.2, 29.75, "受理", fontsize=6.4, va="center")
ax.add_patch(FancyBboxPatch((87.5, 29.3), 1.4, 0.9, boxstyle="square,pad=0", fc=C_REJ, ec="none"))
ax.text(89.2, 29.75, "拒收", fontsize=6.4, va="center")

# ---- 下带左：拒收-回叫闭环 ----
box(2, 3, 45, 24, "#f4f4f4", ec="#666666")
ax.text(24.5, 24.6, "拒收-回叫-验证闭环（两线共用）", ha="center", fontsize=10.6, fontweight="bold")
loop = [
    (8.2, 17.8, "席位产出提案\n（盲包·数据内嵌）"),
    (19.8, 17.8, "验证器逐动作裁决\n受理 / 逐字拒收文"),
    (31.4, 17.8, "拒收文逐字回叫\n（--prior-rejection\n嵌入下一轮任务书）"),
    (42.0, 17.8, "席位携拒收码\n修正重交"),
]
for x, yy, t in loop:
    box(x - 4.3, yy - 4.2, 9.4, 9.4, "#ffffff", ec="#888888", lw=0.9)
    ax.text(x + 0.4, yy, t, ha="center", va="center", fontsize=6.6)
for i in range(3):
    arrow((loop[i][0] + 5.0, loop[i][1]), (loop[i + 1][0] - 4.4, loop[i + 1][1]), lw=1.3)
arrow((loop[3][0] + 5.0, loop[3][1] - 2.2), (loop[0][0] - 4.2, loop[0][1] - 2.2),
      color="#8a8a8a", ls="--", lw=1.2)
ax.text(24.5, 11.4, f"台账链式哈希（ledger.jsonl 状态链）＋reach 证书落盘＋verify 重放全链＝机械真值投影",
        ha="center", fontsize=7.2)
ax.text(24.5, 8.6, f"本图受理/拒收计数即由台账逐行直读并经 index 对账（受+拒＝提案，逐类核验）",
        ha="center", fontsize=7.2)
ax.text(24.5, 5.4, "语义分叉三例回灌披露面：F-bbox（0.3.1）· scratch/施加裂缝（D-CT-034）· 盲孔投影（D-CT-016）",
        ha="center", fontsize=7.0, color="#7a3b3b")

# ---- 下带右：FORCE 通道＋逐 run 计数 ----
box(53, 3, 45, 24, "#fbeaea", ec="#a04040")
ax.text(75.5, 24.6, "FORCE 机械补全通道＋逐 run 提案件计数", ha="center", fontsize=10.6,
        fontweight="bold", color="#7a2020")
ax.text(75.5, 20.8, "主审专属（非席位动作）：席位预算耗尽而机制上存在解时，主审以 FORCE 轮直接\n"
        "施加机械构造的合法动作（FORCE- 前缀提案目录，正常过验证器；不入席位 ledger）",
        ha="center", fontsize=7.2)
ax.text(75.5, 16.2, f"在盘 FORCE 提案件逐 run 计数（rounds/FORCE-*/proposal.json 直数）：",
        ha="center", fontsize=7.6, fontweight="bold", color="#7a2020")
cell_w = 45 / (len(V8_RUNS) + 1) - 0.8
for i, run in enumerate(V8_RUNS):
    cx = 53 + 0.6 + cell_w * (i + 0.5) + 0.4 * i
    box(cx - cell_w / 2, 10.4, cell_w, 4.4, "#ffffff", ec="#a04040", lw=0.8)
    ax.text(cx, 13.6, run, ha="center", fontsize=7.4, color="#7a2020")
    ax.text(cx, 11.6, f"{force[run]} 件", ha="center", fontsize=8.6, fontweight="bold", color="#7a2020")
cx = 53 + 0.6 + cell_w * (len(V8_RUNS) + 0.5) + 0.4 * len(V8_RUNS)
box(cx - cell_w / 2, 10.4, cell_w, 4.4, "#f5d5d5", ec="#a04040", lw=1.0)
ax.text(cx, 13.6, "合计", ha="center", fontsize=7.4, color="#7a2020")
ax.text(cx, 11.6, f"{force_total} 件", ha="center", fontsize=8.6, fontweight="bold", color="#7a2020")
ax.text(75.5, 7.4, f"run5 首例（{'、'.join(force_names['run5'])}，任务书口径：席位两轮未解、FORCE 四段三 via 一发过）；\n"
        "run6/run8 各为 ripup/fence 探针批 FORCE（ripupD1/fenceD2/ripupD2/ripupD1walled）",
        ha="center", fontsize=6.8, color="#7a3b3b")
arrow((47.6, 16), (52.4, 16), color="#a04040", ls="--", lw=1.3)
ax.text(50, 17.6, "预算耗尽", ha="center", fontsize=6.8, color="#a04040")

# ---- 图例角标（数据版口径） ----
ax.text(2, 1.6, "图注（数据版）：动作词表三源直读——canvas/protocol.py REQUIRED_KEYS（与 CANVAS-API-CONTRACT §2 表双源互证）、"
        "V8 席位动作域=net_agent_pilot/pilot.py；", fontsize=6.8, color="#444444")
ax.text(2, 0.2, f"用量面=out/canvas-toolchain/act-*/ledger-*.jsonl（在盘 {len(v6_files)} 件全并入）与 "
        f"out/net-agent-p1/run{'/'.join(V8_RUNS)}/ledger.jsonl 逐行直读（batch=提案全表；无 batch 行由 accepted+rejected 按 index 重建；"
        f"run10/11/13 无台账件如实记缺不入）；FORCE=rounds/FORCE-* 提案件直数。断言：直方图与逐条重数一致、逐类受+拒＝提案、两线总动作数>0。",
        fontsize=6.8, color="#444444")

fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
from PIL import Image  # 尺寸自检（≥2000×1000）
im = Image.open(OUT)
assert im.width >= 2000 and im.height >= 1000, f"尺寸不足 {im.size}"
print(f"[ok] {OUT} ({sz} B, {im.width}x{im.height}) 九动作={len(required)}，V8 域={sorted(v8_domain)}，"
      f"V6 提案 {v6_total}（{dict(v6_prop)}），V8 提案 {v8_total}（{dict(v8_prop)}），FORCE={force}")
