# -*- coding: utf-8 -*-
"""
FIG-P6-06 — P6 图 6：四环境时长/质量分离散点（时长轴 log；质量面全重合）
数据源（机器件直读）：
  1. out/canvas-toolchain/seat-switch-r1/review/lead-review-checks.json —— 三道逐席
     duration_s＋质量旗标（T0 t0_exact_match / T1-T2 structure_ok），42 席全 True（质量面全重合）
  2. out/canvas-toolchain/seat-switch-r1/{a,b,c}/analysis.json —— 逐席 duration_ms/subagent_tokens
     （token 成本面；时长读数与 review 件 duration_s 双源互证）
  3. out/canvas-toolchain/seat-switch-r1/{a,b,c}/REPORT.md —— 环境模型自报行（SWA=deepseek-flash、
     SWB=gpt-6-sol、SWC=GLM-5.3；源文解析非手抄）
  4. out/canvas-toolchain/seat-stall-r1/analysis.json —— 第四环境（SEAT-STALL 健康窗基线道 GLM-5.3）
     逐席时长/回收（token_notify_rate=1.0、零停滞）
断言：三道 14×3=42 席质量旗标全 True（T0 exact 12/12、T1/T2 structure_ok 30/30）；
  review duration_s 与 analysis duration_ms/1000 双源一致（42/42）；四环境时长全域≈4.9–199.0s；输出>10KB。
"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
CT = os.path.join(REPO, "out/canvas-toolchain")
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-06-SEAT-SWITCH-DURATION-QUALITY-SCATTER.png")

# ---- 取数 1：三道质量+时长（review 件） ----
rv = json.load(open(os.path.join(CT, "seat-switch-r1/review/lead-review-checks.json"),
                    encoding="utf-8"))
lane_model = {}
data = []
for lane in ["SWA", "SWB", "SWC"]:
    for s in rv[lane]["seats"]:
        q = s.get("t0_exact_match", s.get("structure_ok"))
        assert q is True, f"{s['seat']} 质量旗标非 True"
        data.append(dict(seat=s["seat"], lane=lane, fam=s["fam"],
                         dur=s["duration_s"], tok=None, qual=q))
n_t0 = sum(1 for d in data if d["fam"] == "T0")
n_struct = sum(1 for d in data if d["fam"] != "T0")
assert len(data) == 42 and n_t0 == 12 and n_struct == 30
assert all(d["qual"] for d in data), "质量面非全重合"

# ---- 取数 2：analysis.json 时长/token 双源互证 + 环境模型名（REPORT 源文解析） ----
lane_dirs = {"SWA": "a", "SWB": "b", "SWC": "c"}
tok_by_seat = {}
for lane, ld in lane_dirs.items():
    an = json.load(open(os.path.join(CT, f"seat-switch-r1/{ld}/analysis.json"), encoding="utf-8"))
    for sid, s in an["seats"].items():
        tok_by_seat[sid] = s["subagent_tokens"]
        ds = s["duration_ms"] / 1000.0
        row = next(d for d in data if d["seat"] == sid)
        assert abs(ds - row["dur"]) < 0.15, f"{sid} 时长双源不一致 {ds} vs {row['dur']}"
        row["tok"] = s["subagent_tokens"]
    rep = open(os.path.join(CT, f"seat-switch-r1/{ld}/REPORT.md"), encoding="utf-8").read()
    seg = rep[rep.find("model_self_report"):][:260]
    mm = re.search(r"([0-9a-f]{8}-[0-9a-f-]{27}/[a-z0-9.\-]+)", seg)
    if mm:  # SWA/SWB：环境串 uuid/模型名
        lane_model[lane] = mm.group(1).split("/")[1]
    else:
        mm2 = re.search(r"model_self_report[=：: ]+([A-Za-z0-9.\-]+)", seg)
        assert mm2, f"{lane} 模型自报行未解析"
        lane_model[lane] = mm2.group(1)

# ---- 取数 3：基线道（SEAT-STALL 健康窗，GLM-5.3） ----
base = json.load(open(os.path.join(CT, "seat-stall-r1/analysis.json"), encoding="utf-8"))
base_rows = [dict(seat=sid, fam=s["family"], dur=s["duration_ms"] / 1000.0, tok=s["subagent_tokens"])
             for sid, s in base["seats"].items()]
assert len(base_rows) == 14 and base["summary"]["stall_candidates"] == 0
assert base["summary"]["token_notify_rate"] == 1.0

all_durs = [d["dur"] for d in data] + [b["dur"] for b in base_rows]
lane_durs = [d["dur"] for d in data]
tok_tot = {lane: sum(d["tok"] for d in data if d["lane"] == lane) for lane in lane_dirs}
print(f"[read] 三道 42 席质量旗标全 True（T0 exact {n_t0}/12、T1/T2 structure_ok {n_struct}/30）")
print(f"[read] 环境映射={lane_model}；三道时长 {min(lane_durs):.1f}–{max(lane_durs):.1f}s；"
      f"四环境全域 {min(all_durs):.1f}–{max(all_durs):.1f}s")
print(f"[read] 三道 token 合计={tok_tot}（基线道 1,221,219；对照见 REPORT §3 −9%~−24%）")

# ---- 绘图 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.4, 5.9), dpi=300,
                               gridspec_kw={"width_ratios": [1.5, 1.0]})
LCOL = {"SWA": "#dd8452", "SWB": "#c44e52", "SWC": "#4c72b0", "BASE": "#8172b2"}
LNAM = {"SWA": f"SWA·{lane_model['SWA']}", "SWB": f"SWB·{lane_model['SWB']}",
        "SWC": f"SWC·{lane_model['SWC']}", "BASE": "基线道·GLM-5.3（SEAT-STALL 健康窗）"}
MK = {"T0": "o", "T1": "s", "T2": "^"}

for lane in ["SWA", "SWB", "SWC"]:
    for fam in ["T0", "T1", "T2"]:
        xs = [d["dur"] for d in data if d["lane"] == lane and d["fam"] == fam]
        ax1.scatter(xs, [1.0] * len(xs), s=64, marker=MK[fam], color=LCOL[lane],
                    alpha=0.85, edgecolors="white", lw=0.7, zorder=3,
                    label=f"{LNAM[lane]}·{fam}" if lane == "SWA" else None)
xs = [b["dur"] for b in base_rows]
ax1.scatter(xs, [1.0] * len(xs), s=52, marker="D", facecolors="none", edgecolors=LCOL["BASE"],
            lw=1.6, zorder=2, label=LNAM["BASE"])

ax1.set_xscale("log")
ax1.set_ylim(0.965, 1.035)
ax1.set_yticks([1.0])
ax1.set_yticklabels(["1.0（结构合格/T0 逐字精确）"])
ax1.set_xlabel("席位时长（秒，对数轴）", fontsize=11)
ax1.set_ylabel("输出质量（结构合格率）", fontsize=11)
ax1.set_title("时长对环境敏感（10–24×）而质量面全重合", fontsize=12, fontweight="bold")
ax1.axhline(1.0, color="#2c8a3f", lw=1.0, ls="--", alpha=0.6)
ax1.text(5.6, 1.016, "三道 42/42 结构合格＋T0 12/12 exact＋零占段触碰", fontsize=9, color="#2c5e33")
ax1.text(5.6, 0.975, "基线道（第四环境）14 席完成即写全回收、零停滞（质量读数口径见 REPORT）",
         fontsize=8.2, color="#5a4a7a")
hnd, lab = ax1.get_legend_handles_labels()
ax1.legend(hnd[:3] + [hnd[-1]], [lab[i] for i in [0, 1, 2]] + [lab[-1]],
           fontsize=8.2, loc="upper right", ncol=1)
ax1.grid(alpha=0.3, which="both")

# 右：token 成本面（同席位，按环境分列）
lanes = ["SWA", "SWB", "SWC", "BASE"]
for i, lane in enumerate(lanes):
    toks = [d["tok"] for d in data if d["lane"] == lane] if lane != "BASE" \
        else [b["tok"] for b in base_rows]
    ax2.scatter(np.full(len(toks), i) + np.random.default_rng(7 + i).uniform(-0.13, 0.13, len(toks)),
                toks, s=40, color=LCOL[lane], alpha=0.8, edgecolors="white", lw=0.6, zorder=3)
    ax2.text(i, max(toks) * 1.30, f"中位 {int(np.median(toks)):,}", ha="center", fontsize=8.6)
ax2.set_yscale("log")
ax2.set_xticks(range(4))
ax2.set_xticklabels([LNAM[l].replace("（SEAT-STALL 健康窗）", "\n健康窗") for l in lanes], fontsize=8.4)
ax2.set_ylabel("席位 token（对数轴）", fontsize=11)
ax2.set_title("token 成本面：三道 −9%~−24%（成本变量）", fontsize=12, fontweight="bold")
ax2.grid(alpha=0.3, axis="y", which="both")

fig.suptitle("通道环境效应：换模型改成本不改产出合规性（SEAT-SWITCH-R1 四环境×14 席受控对照）",
             fontsize=13.5, fontweight="bold", y=1.02)
fig.text(0.5, -0.045,
         "图注：四环境=三道（SWA/SWB/SWC，模型自报行源文解析于各道 REPORT.md）+SEAT-STALL 基线道（GLM-5.3，state/canvas-toolchain.md:58 口径）。"
         "质量/时长=review/lead-review-checks.json 逐席旗标与 duration_s（42/42 与 analysis.json duration_ms 双源一致）；"
         "token=三道 analysis.json 逐席 subagent_tokens；基线道 14 席 token_notify_rate=1.0。",
         ha="center", fontsize=8.0, color="#444444")
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
print(f"[ok] {OUT} ({sz} B)")
