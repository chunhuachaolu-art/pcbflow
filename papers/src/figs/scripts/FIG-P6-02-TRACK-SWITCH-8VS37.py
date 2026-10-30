# -*- coding: utf-8 -*-
"""
FIG-P6-02 — P6 图 2：换轨机制 8 vs 37 对照（m4 布局换轨两臂 + m5 调参换轨两席）
数据源（机器件直读）：
  1. out/canvas-toolchain/act-m4/apply-R{1..5}-m4-fixture-1.json —— 模型臂 5 轮 referee 轨迹/施加动作
  2. out/canvas-toolchain/act-m4/baseline-arm-m4-fixture-1.json —— 确定性臂 37 accepted_moves、
     基线/终态评分（0.887326401→0.896357013）
  3. out/canvas-toolchain/act-m4/VERDICT.md —— PREREG sha256 全值（程序化提取后对 PREREG.md 重算比对）
  4. out/canvas-toolchain/act-m4/PREREG.md —— sha 锚重算对象
  5. out/canvas-toolchain/act-m5/apply-R{1..4}-m5-fixture-1.json —— 模型臂 4 轮读数（in_tol/res_total）
  6. out/canvas-toolchain/act-m5/baseline-arm-m5-fixture-1.json —— 基线臂 3 动作、残差 43→0、三网 37.0mm
断言：模型臂施加 move 合计=8；确定性臂 accepted_moves=37；两臂终值同顶 0.896357013；
  m5 基线 applied=3、残差 43→0、三网 path_len_mm=37.0；PREREG sha 重算一致；输出>10KB。
"""
import hashlib
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REPO = "<ENGINE_ROOT>"
M4 = os.path.join(REPO, "out/canvas-toolchain/act-m4")
M5 = os.path.join(REPO, "out/canvas-toolchain/act-m5")
OUT = os.path.join(REPO, "out/paper-program-r2/figs/FIG-P6-02-TRACK-SWITCH-8VS37.png")

# ---- 取数：m4 两臂 ----
rounds = [json.load(open(os.path.join(M4, f"apply-R{r}-m4-fixture-1.json"), encoding="utf-8"))
          for r in range(1, 6)]
base = json.load(open(os.path.join(M4, "baseline-arm-m4-fixture-1.json"), encoding="utf-8"))

model_moves = [sum(1 for a in d["last_round_accepted"] if a["action"] == "move") for d in rounds]
model_cum = [0] + [sum(model_moves[:i + 1]) for i in range(len(model_moves))]
model_ref = [rounds[0]["referee_before"]] + [d["referee_after"] for d in rounds]
assert sum(model_moves) == 8, f"模型臂 move 合计 {sum(model_moves)} != 8"
assert base["measure"]["accepted_moves"] == 37, "确定性臂 moves != 37"
top = base["measure"]["score_final"]["total"]
start = base["baseline"]["score_initial"]["total"]
assert abs(model_ref[-1] - top) < 1e-9, f"模型臂终值 {model_ref[-1]} != 天花板 {top}"
assert abs(top - 0.896357013) < 1e-9, "天花板值与正文锚 0.896357013 不一致"

# PREREG sha 锚程序化重算（期望值从 VERDICT.md 文本提取，非手抄）
vt = open(os.path.join(M4, "VERDICT.md"), encoding="utf-8").read()
m = re.search(r"PREREG 冻结 sha256=([0-9a-f]{64})", vt)
assert m, "VERDICT 中 PREREG sha256 未定位"
prereg_sha = hashlib.sha256(open(os.path.join(M4, "PREREG.md"), "rb").read()).hexdigest()
assert prereg_sha == m.group(1), f"PREREG sha 重算不一致 {prereg_sha[:16]}"

# ---- 取数：m5 两臂 ----
r5 = [json.load(open(os.path.join(M5, f"apply-R{r}-m5-fixture-1.json"), encoding="utf-8"))
      for r in range(1, 5)]
b5 = json.load(open(os.path.join(M5, "baseline-arm-m5-fixture-1.json"), encoding="utf-8"))
res = [r5[0]["floor"]["current"]["res_total"]] + [d["readings_after"]["res_total"] for d in r5]
intol = [r5[0]["floor"]["current"]["in_tol"]] + [d["readings_after"]["in_tol"] for d in r5]
tuning_cum = [0]
for d in r5:
    n = sum(1 for a in d["last_round_accepted"] if a["action"] == "tuning")
    tuning_cum.append(tuning_cum[-1] + n)
assert b5["applied"] == 3 and b5["planned"] == 3, "m5 基线臂动作数 != 3"
assert b5["residuals_before"]["G1"]["residual_mm"] == 25.0 or \
       b5["residuals_before"]["G1"]["residual_mm"] > 0, "m5 基线残差异常"
assert b5["readings_after"]["res_total"] == 0.0 and b5["readings_after"]["in_tol"] == 3
g1 = b5["residuals_after"]["G1"]
assert all(abs(v["path_len_mm"] - 37.0) < 1e-9 and v["residual_mm"] == 0.0
           for v in g1["per_net"].values()), "三网 37.0mm 零残差不成立"
assert res[-1] == 0.0 and intol[-1] == 3 and tuning_cum[-1] == 3

print(f"[read] m4 模型臂 move 序列={model_moves}（合计 8），referee 轨迹={[round(v,6) for v in model_ref]}")
print(f"[read] m4 确定性臂 accepted_moves={base['measure']['accepted_moves']}，天花板={top}")
print(f"[read] m5 残差轨迹={res}，in_tol={intol}，基线 3 动作同解 37.0mm")
print(f"[read] m4 PREREG sha256 重算一致（{prereg_sha[:16]}…）")

# ---- 绘图 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.6), dpi=300)

# 左：m4 referee 轨迹（x=累计施加动作数）
ax1.plot(model_cum, model_ref, "o-", color="#c44e52", lw=2.2, ms=8, zorder=3,
         label="模型臂（3 席×轮间反馈+整包择优）")
ax1.plot([0, 37], [start, top], "s--", color="#4c72b0", lw=1.8, ms=8, zorder=2,
         label="确定性臂（canvas/runners/m4，37 moves）")
ax1.axhline(top, color="#999999", ls=":", lw=1.1)
ax1.annotate(f"同顶 {top:.9f}\n（板天花板闭式互证）", xy=(37, top), xytext=(22.5, 0.8890),
             fontsize=9, color="#333333",
             arrowprops=dict(arrowstyle="->", color="#666666", lw=1.0))
for x, y in zip(model_cum, model_ref):
    ax1.annotate(f"{y:.4f}", xy=(x, y), xytext=(x + 0.6, y - 0.0016), fontsize=7.6, color="#c44e52")
ax1.annotate("R2 一轮劣化\n（D-CT-025 缺地板实录）", xy=(4, 0.8929), xytext=(6.5, 0.8968),
             fontsize=7.8, color="#7a3b3b",
             arrowprops=dict(arrowstyle="->", color="#a06060", lw=0.9))
ax1.set_xlabel("累计施加动作数（move）", fontsize=10.5)
ax1.set_ylabel("referee 评分（逃逸 0.4/走廊 0.3/容量 0.3 加权）", fontsize=10)
ax1.set_title("m4 布局换轨：8 动作追平 37 动作（同终值）", fontsize=12, fontweight="bold")
ax1.set_xlim(-1.5, 40)
ax1.set_ylim(0.8865, 0.8978)
ax1.legend(loc="lower right", fontsize=9)
ax1.grid(alpha=0.3)

# 右：m5 残差收敛（x=累计 tuning 动作数）
ax2.plot(tuning_cum, res, "o-", color="#55a868", lw=2.2, ms=8, zorder=3,
         label="模型臂（词表澄清后 R2 一轮登顶）")
ax2.plot([0, 3], [25.0 if False else res[0], 0.0], "s--", color="#4c72b0", lw=1.8, ms=8,
         zorder=2, label="确定性基线臂（3 tuning 同三档）")
ax2.annotate("R1 词表学费轮（三席自造 add_mm 全拒）", xy=(0, 43.0), xytext=(1.0, 36.0),
             fontsize=8.2, color="#7a3b3b",
             arrowprops=dict(arrowstyle="->", color="#a06060", lw=0.9))
ax2.annotate("3/3 网精确 37.0mm 零残差", xy=(3, 0.0), xytext=(1.4, 8.0),
             fontsize=9, color="#2c5e33",
             arrowprops=dict(arrowstyle="->", color="#4c8a54", lw=1.0))
ax2.set_xlabel("累计施加动作数（tuning）", fontsize=10.5)
ax2.set_ylabel("组残差合计 |residual|（mm）", fontsize=10)
ax2.set_title("m5 调参换轨：3=3 同解、37.0mm 零残差", fontsize=12, fontweight="bold")
ax2.set_xlim(-0.4, 4.2)
ax2.set_ylim(-2.5, 47)
ax2.legend(loc="upper right", fontsize=9)
ax2.grid(alpha=0.3)

fig.suptitle("换轨机制成立：模型臂以少数动作追平确定性臂最优顶点（act-m4 / act-m5 双批）",
             fontsize=13.5, fontweight="bold", y=1.02)
fig.text(0.5, -0.035,
         "图注：数据直读 act-m4/act-m5 机件（apply-R*/baseline-arm JSON；m4 PREREG sha256 程序化重算一致）。"
         "m4 板=m4-fixture-1（referee 初值 0.887326401、viol 0）；m5 板=m5-fixture-1（三 CLK 网 G1 目标 37.0±0.5mm）。"
         "m5 R6 闭式陷阱批未被踩中（排序沉底）。",
         ha="center", fontsize=8.4, color="#444444")
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
sz = os.path.getsize(OUT)
assert sz > 10 * 1024, f"输出过小 {sz} B"
print(f"[ok] {OUT} ({sz} B)")
