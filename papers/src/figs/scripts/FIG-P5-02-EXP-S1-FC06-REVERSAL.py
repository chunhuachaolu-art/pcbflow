# -*- coding: utf-8 -*-
"""
篇五 图②：EXP-S1 fc-06 反超轨迹 —— 档位臂（TIER）终值 266.0 = oracle，反超全序臂（FULL）
终值 272.0；全序臂四轮未达 oracle；TIER 靠 R1 探针实测发现 266.0、R2 主案晋升采纳。

数据来源（全部直读机器件，零硬编码数据点）：
  - <ENGINE_ROOT>/out/guide-exp-s1/state/TIER.json（fc-06 逐轮主案+探针）
  - <ENGINE_ROOT>/out/guide-exp-s1/state/FULL.json（同上）
  - <ENGINE_ROOT>/out/guide-exp-s1/ceilings/ceilings.json
      （FULL l4-fc-06 ceiling=266.0 mode=exact space=720；TIER ceiling=266.0 mode=exact space=540）
对账件：GUIDE-EXP-S1-VERDICT-2026-09-17.md §1（fc-06 行：基线 276.5 / TIER R4 266.0 /
FULL R4 272.0 / oracle 266.0）、§2 G-Q3（R1 探针实测→R2 主案改排命中 266.0 oracle）。
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

S1 = "<ENGINE_ROOT>/out/guide-exp-s1"
TIER = f"{S1}/state/TIER.json"
FULL = f"{S1}/state/FULL.json"
CEIL = f"{S1}/ceilings/ceilings.json"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P5-02-EXP-S1-FC06-REVERSAL.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False
SCEN = "l4-fc-06"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def arm_data(state):
    sc = state["scenarios"][SCEN]
    rounds = sc["rounds"]
    main = [rounds[str(r)]["main"]["objective"] for r in range(len(rounds))]
    probes = []
    for r in range(len(rounds)):
        for p in rounds[str(r)].get("probes", []):
            if isinstance(p, dict) and p.get("objective") is not None:
                probes.append((r, p["objective"], p.get("label")))
    return main, probes


def main():
    tier, full = load(TIER), load(FULL)
    ceil = load(CEIL)

    tier_main, tier_probes = arm_data(tier)
    full_main, full_probes = arm_data(full)
    oracle_full = ceil["per"]["FULL"][SCEN]
    oracle_tier = ceil["per"]["TIER"][SCEN]

    # ---------- 断言层 ----------
    assert tier["arm"] == "TIER" and full["arm"] == "FULL"
    assert len(tier_main) == len(full_main) == 5, "双臂各应 5 轮（R0..R4）"
    assert tier_main == [276.5, 280.0, 266.0, 271.5, 266.0], f"TIER 轨迹不符：{tier_main}"
    assert full_main == [276.5, 280.0, 276.5, 273.0, 272.0], f"FULL 轨迹不符：{full_main}"
    assert tier_main[0] == full_main[0] == 276.5, "R0 应为基线 276.5"
    assert oracle_full["ceiling"] == 266.0 and oracle_full["mode"] == "exact" and oracle_full["space"] == 720
    assert oracle_tier["ceiling"] == 266.0 and oracle_tier["mode"] == "exact" and oracle_tier["space"] == 540
    assert min(tier_main) == 266.0 and tier_main[-1] == 266.0, "TIER 终值应 266.0=oracle"
    assert max(full_main) == 280.0 and full_main[-1] == 272.0 and min(full_main) == 272.0, (
        "FULL 终值应 272.0 且四轮未达 266.0"
    )
    assert min(o for _, o, _ in full_probes) == 272.0 and 266.0 not in [o for _, o, _ in full_probes], (
        "FULL 探针亦不应出现 266.0"
    )
    tier_r1 = [o for r, o, _ in tier_probes if r == 1]
    assert min(tier_r1) == 266.0, f"TIER R1 探针应实测到 266.0：{tier_r1}"
    assert any(o == 266.0 for r, o, l in tier_probes if r == 1 and l == "high-gap-first"), (
        "R1 命中 266.0 的探针应为 high-gap-first"
    )
    print("[assert] EXP-S1 fc-06 断言全过：TIER [276.5,280,266,271.5,266]/FULL [276.5,280,276.5,273,272]/"
          "oracle=266(720全枚举)/R1探针high-gap-first实测266/R2晋升")

    # ---------- 画图层 ----------
    rr = list(range(5))
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    fig.subplots_adjust(left=0.10, right=0.86, top=0.87, bottom=0.12)

    ax.axhline(276.5, color="#8d6e63", ls=":", lw=1.2)
    ax.text(4.06, 276.7, "R0 基线 276.5", color="#8d6e63", fontsize=9.2, va="bottom")
    ax.axhline(266.0, color="#2e7d32", ls="--", lw=1.6)
    ax.text(4.06, 266.2, "oracle＝通道天花板 266.0\n（FULL 720 排列全枚举；\nTIER 540 档位展开精确）",
            color="#2e7d32", fontsize=9.0, va="bottom")

    ax.plot(rr, full_main, "s--", color="#ef6c00", lw=1.8, ms=6.5, label="FULL 全序臂（每网完整排序）")
    ax.plot(rr, tier_main, "o-", color="#1565c0", lw=2.2, ms=7, label="TIER 档位臂（网分档＋档间序）")

    # 探针实测点（两臂，透明小标）
    ax.scatter([r for r, o, _ in tier_probes], [o for r, o, _ in tier_probes],
               marker="v", s=34, color="#1565c0", alpha=0.45, zorder=2,
               label="TIER 探针实测（≤3/轮）")
    ax.scatter([r for r, o, _ in full_probes], [o for r, o, _ in full_probes],
               marker="v", s=34, color="#ef6c00", alpha=0.45, zorder=2,
               label="FULL 探针实测（≤3/轮）")

    ax.annotate("R1 探针 high-gap-first 实测 266.0（发现）\nR2 主案晋升采纳即中 oracle",
                xy=(1, 266.0), xytext=(0.04, 267.6), fontsize=9.4, color="#1565c0",
                arrowprops=dict(arrowstyle="->", color="#1565c0", lw=1.2))
    ax.annotate("FULL 终值 272.0\n（四轮＋探针均未达 oracle）",
                xy=(4, 272.0), xytext=(2.62, 279.2), fontsize=9.4, color="#ef6c00",
                arrowprops=dict(arrowstyle="->", color="#ef6c00", lw=1.2))
    ax.annotate("TIER 终值 266.0＝oracle（反超全序臂 6.0）",
                xy=(4, 266.0), xytext=(1.86, 262.1), fontsize=9.4, color="#2e7d32",
                arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.2))

    ax.set_xticks(rr)
    ax.set_xticklabels([f"R{r}" + ("（基线）" if r == 0 else "") for r in rr], fontsize=10)
    ax.set_xlim(-0.35, 5.55)
    ax.set_ylim(259.5, 284.5)
    ax.set_xlabel("轮次", fontsize=11)
    ax.set_ylabel("主案 objective（成本单位）", fontsize=11)
    ax.set_title("EXP-S1 场景 fc-06（四层合成板）：档位臂靠探针晋升反超全序臂（终值 266 vs 272）",
                 fontsize=12)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="center right", fontsize=9.3, frameon=False)

    fig.savefig(OUT, dpi=300)
    plt.close(fig)
    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或 <10KB"
    print(f"[done] {OUT}  size={os.path.getsize(OUT)}B")


if __name__ == "__main__":
    main()
