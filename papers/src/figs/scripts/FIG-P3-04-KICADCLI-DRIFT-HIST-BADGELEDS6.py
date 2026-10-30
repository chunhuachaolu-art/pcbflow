# -*- coding: utf-8 -*-
"""
篇三 图④：kicad-cli 10.0.5 非确定性——badgeleds 同字节 6 跑 DRC totals 漂移直方图。

D-1 口径落定（任务书 §3）：主审候选域（out/v5-p5/_logs/、p5-gate/、p5-sessions/）未定位
六跑 totals 正本；本席第一步再扫（三候选域+逐 run 日志聚合模式均零命中）后扩域全仓扫描，
正本定位成功＝机器件口径成图（无需降级）：
  - <ENGINE_ROOT>/out/v5-p5/trial/badgeleds-do-electronics.trial.json
      键 drc_nondeterminism.observed_totals_in_order = [95, 96, 102, 97, 102, 97]（与任务书
      锚值逐位一致）、n_runs=6、ledger_seqs、same_input_sha256（== stages.export.sha256，
      同字节输入内证）；finding=「P4-G3 在 demo 板实测总数稳定，真实板上总数亦不稳」
辅助源（口径注记）：P3 正文 §6.1（P5-UP3-aggregate-v1 聚合口径：每轮 5 跑、至多 3 轮、
  无全等轮=union-max＋披露）。
断言：totals 与锚值 [95,96,102,97,102,97] 逐位一致；n_runs=6；same_input_sha256 与
  export 段 sha256 相等；min/max 值域 95–102；输出存在且 >10KB。
"""
import hashlib
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

SRC = "<ENGINE_ROOT>/out/v5-p5/trial/badgeleds-do-electronics.trial.json"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P3-04-KICADCLI-DRIFT-HIST-BADGELEDS6.png"

raw = open(SRC, "rb").read()
src_sha16 = hashlib.sha256(raw).hexdigest()[:16]
d = json.loads(raw.decode("utf-8"))
dn = d["drc_nondeterminism"]
totals = dn["observed_totals_in_order"]
n_runs = dn["n_runs"]
seqs = dn["ledger_seqs"]
in_sha = dn["same_input_sha256"]
exp_sha = d["stages"]["export"]["sha256"]

# ---- 断言层 ----
assert totals == [95, 96, 102, 97, 102, 97], f"六跑 totals 与任务书锚值不一致: {totals}"
assert n_runs == 6 and len(totals) == 6 and len(seqs) == 6, f"跑数口径异常: n_runs={n_runs}"
assert in_sha == exp_sha, "same_input_sha256 != export sha256（同字节输入内证失败）"
assert min(totals) == 95 and max(totals) == 102, f"值域异常 {totals}"
assert "总数漂移" in dn["finding"] and "P4-G3" in dn["finding"], "finding 口径原文未命中"
assert d["risk_conclusion"]["genuine_count"] == 0, "genuine_count 非 0"

# ---- 绘图 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 7.2), dpi=300,
                               gridspec_kw={"width_ratios": [1.2, 1]})

runs = list(range(1, 7))
colors = ["#5DADE2" if t != max(totals) else "#E74C3C" for t in totals]
bars = ax1.bar(runs, totals, width=0.55, color=colors, edgecolor="#1b2631", lw=1.1)
for r, t in zip(runs, totals):
    ax1.text(r, t + 0.8, str(t), ha="center", fontsize=13, fontweight="bold")
ax1.axhline(sum(totals) / 6, color="#7D3C98", ls="--", lw=1.6)
ax1.text(6.42, sum(totals) / 6 + 0.6, f"均值 {sum(totals)/6:.2f}", color="#7D3C98",
         fontsize=10.5, ha="right")
ax1.set_xticks(runs)
ax1.set_xticklabels([f"第 {i} 跑\n(台账 seq {s})" for i, s in zip(runs, seqs)], fontsize=10)
ax1.set_ylim(88, 106)
ax1.set_ylabel("kicad-cli DRC totals（违例总数）", fontsize=11.5)
ax1.set_title("A｜badgeleds 同字节输入 6 跑逐跑 totals（漂移 95–102，极差 7）\n"
              f"same_input_sha256={in_sha[:16]}…（==export 段 sha256，同字节内证）",
              fontsize=12, fontweight="bold")

from collections import Counter

cnt = Counter(totals)
vals = sorted(cnt)
bars2 = ax2.bar([str(v) for v in vals], [cnt[v] for v in vals], width=0.5,
                color=["#5DADE2", "#5DADE2", "#F5B041", "#E74C3C"], edgecolor="#1b2631", lw=1.1)
for r, v in zip(bars2, vals):
    ax2.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.05, f"{cnt[v]} 跑",
             ha="center", fontsize=12.5, fontweight="bold")
ax2.set_ylim(0, 2.8)
ax2.set_xlabel("totals 取值", fontsize=11.5)
ax2.set_ylabel("出现跑数", fontsize=11.5)
ax2.set_title("B｜取值分布：95×1／96×1／97×2／102×2（无全等轮）", fontsize=12, fontweight="bold")
ax2.text(0.5, -0.62, "6 跑仅 4 个取值、最高值 102 出现 2 次——「多跑取一次」不可复现，",
         transform=ax2.transAxes, fontsize=9.5, ha="center", color="#566573")
ax2.text(0.5, -0.70, "证据口径必须钉死运行方式（P5-UP3-aggregate-v1：每轮 5 跑、至多 3 轮、无全等轮=union-max＋披露）",
         transform=ax2.transAxes, fontsize=9.5, ha="center", color="#566573")

fig.suptitle("kicad-cli 10.0.5 非确定性两事实之②：真实板同字节多跑总数漂移（badgeleds，P5① 试跑首发现）\n"
             "对照事实①：by-type 归类并发竞态（demo 板同字节两跑总数同 27=27、clearance/shorting 归类漂移，P4 门首发现）——「总数稳定」不外推",
             fontsize=13.5, fontweight="bold", y=1.00)
fig.text(0.5, 0.005, f"数据源（机器件口径）：out/v5-p5/trial/badgeleds-do-electronics.trial.json（本批重算 sha16={src_sha16}）"
         " 键 drc_nondeterminism.observed_totals_in_order｜genuine 6 跑恒 0",
         ha="center", fontsize=9.5, color="#566573")
fig.tight_layout(rect=[0, 0.025, 1, 0.90])
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)

assert os.path.exists(OUT), "输出 PNG 未生成"
size = os.path.getsize(OUT)
assert size > 10 * 1024, f"输出 PNG {size}B ≤10KB"
print(f"OK FIG-P3-04 kicad-cli 漂移直方图 {OUT} {size} bytes")
print("totals:", totals, "| n_runs:", n_runs, "| ledger_seqs:", seqs, "| src sha16:", src_sha16)
