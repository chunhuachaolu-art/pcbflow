# -*- coding: utf-8 -*-
"""
篇五 图①：SCALE-R1 —— n8 全枚举两值直方图（474.5 真全局最优，证伪无探针臂 SA 的
「475.5 结构下界」宣称）＋ n16 hard mode 双臂轨迹（SB 探针 gambit 实测 1489.5 = null_min）。

数据来源（全部直读机器件，零硬编码数据点）：
  - <ENGINE_ROOT>/out/guide-scale-r1/p0/oracle-scl-n08.json
      （40,320 排列全枚举；直方图 histogram_top100；best_objective/best_order）
  - <ENGINE_ROOT>/out/guide-scale-r1/p0/null-summary.json
      （scl-n16 objective_min = null_min = 1489.5；sat_count 17/400）
  - <ENGINE_ROOT>/out/guide-scale-r1/state/SA.json、SB.json
      （双臂逐轮主案 objective，rounds 0..4）
sha256 锚（程序化重算，锚值来自 GUIDE-SCALE-R1-VERDICT-2026-09-17.md §7）：
  oracle-scl-n08 sha16=d481ff2553e0ec7e；null-summary sha16=faf48825
  （VERDICT 登记原文：oracle …d481ff2553e0ec7e7bce97c8667e252f951c4139bbb7de9a193256d20655bcd3、
    null-summary faf48825…）
"""
import hashlib
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

BASE = "<ENGINE_ROOT>/out/guide-scale-r1"
ORACLE = f"{BASE}/p0/oracle-scl-n08.json"
NULLSUM = f"{BASE}/p0/null-summary.json"
SA = f"{BASE}/state/SA.json"
SB = f"{BASE}/state/SB.json"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P5-01-SCALE-R1-N8-HIST-N16-GAMBIT.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def arm_traj(state, scen):
    rounds = state["scenarios"][scen]["rounds"]
    return [rounds[str(r)]["main"]["objective"] for r in range(len(rounds))]


def main():
    oracle = load(ORACLE)
    nullsum = load(NULLSUM)
    sa, sb = load(SA), load(SB)

    # ---------- 断言层：与终判件 GUIDE-SCALE-R1-VERDICT 对账 ----------
    assert sha16(ORACLE) == "d481ff2553e0ec7e", f"oracle sha16={sha16(ORACLE)}"
    assert sha16(NULLSUM).startswith("faf48825"), f"null-summary sha16={sha16(NULLSUM)}"
    assert oracle["permutations"] == 40320 and oracle["sat_order_count"] == 40320
    assert oracle["scenario_id"] == "scl-n08"
    hist = oracle["histogram_top100"]
    assert len(hist) == 2, f"直方图应仅两值，实得 {len(hist)}"
    vals = sorted(v for v, c in hist)
    assert vals == [474.5, 475.5], f"两值应为 474.5/475.5，实得 {vals}"
    assert sum(c for v, c in hist) == 40320, "直方图计数和应为 40320"
    assert all(c == 20160 for v, c in hist), "每值计数应各 20160"
    assert oracle["best_objective"] == 474.5
    assert oracle["best_order"] == ["n1", "n2", "n3", "n4", "n6", "n5", "n7", "n8"], (
        f"最优序不符：{oracle['best_order']}"
    )
    n16 = nullsum["per"]["scl-n16"]
    assert n16["objective_min"] == 1489.5 and n16["sat_count"] == 17 and n16["n_orders"] == 400

    sa_n8, sb_n8 = arm_traj(sa, "scl-n08"), arm_traj(sb, "scl-n08")
    sa_n16, sb_n16 = arm_traj(sa, "scl-n16"), arm_traj(sb, "scl-n16")
    assert len(sa_n8) == len(sb_n8) == len(sa_n16) == len(sb_n16) == 5, "双臂各应 5 轮（R0..R4）"
    assert all(v == 475.5 for v in sa_n8), f"SA-n08 应全程 475.5，实得 {sa_n8}"
    assert sb_n8 == [475.5, 475.5, 474.5, 474.5, 474.5], f"SB-n08 轨迹不符：{sb_n8}"
    assert sa_n16[0] == 1515.5 and min(sa_n16) == 1515.5, f"SA-n16 四轮不应低于基线 1515.5：{sa_n16}"
    assert sb_n16[0] == 1515.5 and sb_n16[-1] == 1489.5 and min(sb_n16) == 1489.5, (
        f"SB-n16 应自基线 1515.5 摸到 1489.5：{sb_n16}"
    )
    sat_rate = n16["sat_count"] / n16["n_orders"]
    assert 0.04 < sat_rate < 0.05  # 17/400=4.25%（约 96% 排列致死）
    print("[assert] SCALE-R1 断言全过：40320/两值/474.5/最优序/1489.5/17of400/双臂轨迹")

    # ---------- 画图层 ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6))
    fig.subplots_adjust(left=0.07, right=0.985, top=0.86, bottom=0.14, wspace=0.28)

    # (a) n8 全枚举直方图
    xs = [str(v) for v, c in hist]
    ys = [c for v, c in hist]
    colors = ["#2e7d32", "#9e9e9e"]
    bars = ax1.bar(xs, ys, width=0.52, color=colors, edgecolor="black", linewidth=0.8)
    for b, c in zip(bars, ys):
        ax1.text(b.get_x() + b.get_width() / 2, c + 260, f"{c:,}", ha="center", fontsize=10)
    ax1.set_ylim(0, 24500)
    ax1.set_xlabel("主案 objective（成本单位）", fontsize=10.5)
    ax1.set_ylabel("排列数", fontsize=10.5)
    ax1.set_title("(a) scl-n08 全枚举 objective 直方图\n"
                  f"（{oracle['permutations']:,} 排列全可布，分布仅两值）", fontsize=11)
    ax1.annotate("全局最优 474.5\n最优序 n1,n2,n3,n4,n6,n5,n7,n8\n＝探针臂（SB）发现并采纳的那一序",
                 xy=(0, 20160), xytext=(0.02, 0.965), textcoords="axes fraction",
                 ha="left", va="top", fontsize=9.2, color="#2e7d32",
                 arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.1))
    ax1.annotate("475.5＝无探针臂（SA）终值；其「结构下界」宣称\n被全枚举证伪（存在 20,160 个更优排列）",
                 xy=(1, 20160), xytext=(0.98, 0.965), textcoords="axes fraction",
                 ha="right", va="top", fontsize=9.2, color="#616161",
                 arrowprops=dict(arrowstyle="->", color="#616161", lw=1.1))

    # (b) n16 hard mode 双臂轨迹
    rr = list(range(5))
    ax2.plot(rr, sa_n16, "o--", color="#9e9e9e", lw=1.6, ms=6, label="SA 无探针臂")
    ax2.plot(rr, sb_n16, "o-", color="#1565c0", lw=2.0, ms=6.5, label="SB 探针臂")
    ax2.axhline(n16["objective_min"], color="#2e7d32", ls=":", lw=1.6)
    ax2.text(4.02, n16["objective_min"], "null_min＝参照顶 1489.5", color="#2e7d32",
             fontsize=9.2, va="center")
    ax2.axhline(1515.5, color="#8d6e63", ls=":", lw=1.2)
    ax2.text(4.02, 1515.7, "基线 1515.5", color="#8d6e63", fontsize=9.2, va="bottom")
    ax2.annotate("R3 结构性 gambit 实测 1489.5＝null_min\n（较基线 −1.71%；400 序抽样仅 17 序可行）",
                 xy=(3, 1489.5), xytext=(1.10, 1493.5), fontsize=9.2, color="#1565c0",
                 arrowprops=dict(arrowstyle="->", color="#1565c0", lw=1.1))
    ax2.annotate("SA 四轮从未低于基线", xy=(4, 1515.5), xytext=(2.35, 1523.5),
                 fontsize=9.2, color="#616161",
                 arrowprops=dict(arrowstyle="->", color="#9e9e9e", lw=1.0))
    ax2.set_xticks(rr)
    ax2.set_xticklabels([f"R{r}" + ("（基线）" if r == 0 else "") for r in rr], fontsize=9.5)
    ax2.set_xlim(-0.3, 6.1)
    ax2.set_ylim(1483.5, 1528.5)
    ax2.set_xlabel("轮次", fontsize=10.5)
    ax2.set_ylabel("主案 objective（成本单位）", fontsize=10.5)
    ax2.set_title("(b) scl-n16（hard mode）双臂主案轨迹\n（约 96% 排列致死；两臂 R0 同自基线出发）", fontsize=11)
    ax2.legend(loc="upper left", fontsize=9.5, frameon=False)
    ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("SCALE-R1：n8 全枚举证 474.5 为真全局最优（证伪无探针臂下界宣称）；n16 探针 gambit 摸到 null_min=1489.5",
                 fontsize=12, y=0.985)
    fig.savefig(OUT, dpi=300)
    plt.close(fig)

    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或 <10KB"
    print(f"[done] {OUT}  size={os.path.getsize(OUT)}B")


if __name__ == "__main__":
    main()
