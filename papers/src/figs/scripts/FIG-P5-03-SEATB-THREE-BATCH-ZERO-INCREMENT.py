# -*- coding: utf-8 -*-
"""
篇五 图③：席位 B 真实板三批零终解增量对照 ——
  批一 会话波单轮（14 板）：③==② 14/14、模型增量 0/14（单轮批，无轮级提升概念）；
  批二 SEAT-B-RESTORE（14 板 24 轮）：轮级提升 9/24、板级 6/14（全在 8 块 FAILED 板），
      终解增量 0/14（③==② 14/14）；
  批三 SEATB-SUPPLEMENT（7 板 18 轮）：轮级提升 9/18、板级 4/7（FAILED 域 4/5），
      终解增量 0/7（③==② 7/7）。

数据来源（全部直读机器件，零硬编码数据点）：
  - <ENGINE_ROOT>/out/v5-p5/p5-sessions/g4-table.json（批一 14 板逐板）
  - <ENGINE_ROOT>/out/v5-p5/seatb-restore/lead-review-checks.json（批二 agg/rows/crossrun）
  - <ENGINE_ROOT>/out/v5-p5/seatb-restore/*.seatb.json（批二逐板 arm3_eq_arm2）
  - <ENGINE_ROOT>/out/v5-p5/seatb-supplement/*.seatb.json（批三逐板 n_rounds/n_promoted_rounds/arm3_eq_arm2）
  - <ENGINE_ROOT>/out/v5-p5/seatb-supplement/lead-review-checks-supplement.json
      （F6 18 轮复算零偏差、F9 ③==② 7/7、rounds_detail 晋升轮 9）
"""
import glob
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

P5 = "<ENGINE_ROOT>/out/v5-p5"
G4 = f"{P5}/p5-sessions/g4-table.json"
RESTORE = f"{P5}/seatb-restore/lead-review-checks.json"
RESTORE_BOARDS = f"{P5}/seatb-restore/*.seatb.json"
SUPP_BOARDS = f"{P5}/seatb-supplement/*.seatb.json"
SUPP_LR = f"{P5}/seatb-supplement/lead-review-checks-supplement.json"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P5-03-SEATB-THREE-BATCH-ZERO-INCREMENT.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    g4 = load(G4)
    rst = load(RESTORE)
    slr = load(SUPP_LR)

    # ---------- 批一：会话波单轮（g4-table.json 逐板） ----------
    b1_boards = len(g4)
    b1_eq = sum(1 for e in g4 if e["arm3_eq_arm2"])
    b1_inc = sum(1 for e in g4 if e["g4"].get("model_increment"))
    b1_sat = sum(1 for e in g4 if e["arm3_verdict"] == "ROUTED")
    b1_failed = sum(1 for e in g4 if e["arm3_verdict"] == "FAILED")
    assert b1_boards == 14 and b1_eq == 14 and b1_inc == 0, (b1_boards, b1_eq, b1_inc)
    assert (b1_sat, b1_failed) == (6, 8), (b1_sat, b1_failed)
    assert all(e["channel"] == "wave" for e in g4), "批一应全为 wave 通道"

    # ---------- 批二：RESTORE（lead-review-checks.json agg + 逐板 seatb.json） ----------
    agg = rst["agg"]
    assert agg["n_boards"] == 14 and agg["total_rounds"] == 24 and agg["promoted_rounds"] == 9
    assert agg["round_level_rate"] == 0.375 and agg["board_level_rate"] == 0.4286
    assert agg["boards_with_promotion"] == 6 and len(agg["boards_promoted"]) == 6
    assert agg["g4_true_counts"]["model_increment"] == 0
    b2_eq = 0
    rows_by_board = {r["board"]: r for r in rst["rows"]}
    prom_boards_failed = [r["sat"] for r in rst["rows"] if r["prom"] > 0]
    for p in glob.glob(RESTORE_BOARDS):
        d = load(p)
        b2_eq += 1 if d["arm3_eq_arm2"] else 0
        bd = d["board"]
        assert bd in rows_by_board, f"逐板件 {bd} 不在 lead-review rows"
    assert b2_eq == 14, "RESTORE 逐板 arm3_eq_arm2 应 14/14"
    assert all(s == "FAILED" for s in prom_boards_failed), "提升板应全在 FAILED 域"
    assert sum(r["n"] for r in rst["rows"]) == 24 and sum(r["prom"] for r in rst["rows"]) == 9
    assert rst["crossrun"]["matched"] == 14 and rst["crossrun"]["mismatched"] == []
    b2_rounds, b2_prom = agg["total_rounds"], agg["promoted_rounds"]
    b2_boards = agg["n_boards"]

    # ---------- 批三：SUPPLEMENT（逐板 seatb.json + lead-review-checks-supplement.json） ----------
    b3_boards, b3_rounds, b3_prom, b3_eq, b3_inc, b3_prom_boards, b3_failed = 0, 0, 0, 0, 0, 0, 0
    supp_files = sorted(glob.glob(SUPP_BOARDS))
    for p in supp_files:
        d = load(p)
        b3_boards += 1
        b3_rounds += d["n_rounds"]
        b3_prom += d["n_promoted_rounds"]
        b3_eq += 1 if d["arm3_eq_arm2"] else 0
        b3_inc += 1 if d["g4"].get("model_increment") else 0
        b3_prom_boards += 1 if d["n_promoted_rounds"] > 0 else 0
        b3_failed += 1 if d["arm3_execute"]["verdict"] == "FAILED" else 0
    assert b3_boards == 7 and b3_rounds == 18 and b3_prom == 9, (b3_boards, b3_rounds, b3_prom)
    assert b3_eq == 7 and b3_inc == 0 and b3_prom_boards == 4 and b3_failed == 5, (
        b3_eq, b3_inc, b3_prom_boards, b3_failed
    )
    rd = slr["rounds_detail"]
    rd_prom = sum(1 for bd, rs in rd.items() for r in rs if r.get("promoted") is not None)
    assert sum(len(rs) for rs in rd.values()) == 18 and rd_prom == 9, "rounds_detail 晋升轮应 9/18"
    assert slr["faces"]["F6-rounds"]["status"] == "PASS" and "总轮数 18" in slr["faces"]["F6-rounds"]["detail"]
    f9 = slr["faces"]["F9-arm3eq2"]
    assert f9["status"] == "PASS" and "7/7" in f9["detail"], f9
    assert slr["verdict"] == "ACCEPT_WITH_NONBLOCKING_DEFECTS"

    print(f"[assert] 三批断言全过：会话波 eq {b1_eq}/{b1_boards} inc {b1_inc}/{b1_boards}（6SAT+8FAILED）；"
          f"RESTORE {b2_prom}/{b2_rounds} 轮提升·板级 {agg['boards_with_promotion']}/{b2_boards} 全 FAILED·"
          f"eq {b2_eq}/{b2_boards} inc 0；SUPPLEMENT {b3_prom}/{b3_rounds} 轮提升·板级 {b3_prom_boards}/{b3_boards}"
          f"（FAILED 域 4/5）·eq {b3_eq}/{b3_boards} inc 0")

    # ---------- 画图层 ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8))
    fig.subplots_adjust(left=0.065, right=0.985, top=0.84, bottom=0.17, wspace=0.24)

    cats = ["会话波单轮\n（席位 B，14 板）", "SEAT-B-RESTORE\n（14 板 24 轮）", "SEATB-SUPPLEMENT\n（7 板 18 轮）"]

    # (a) 轮内机制激活：提升轮占比
    xs = range(3)
    ax1.bar(1, b2_prom / b2_rounds, width=0.5, color="#1565c0", edgecolor="black", linewidth=0.8)
    ax1.bar(2, b3_prom / b3_rounds, width=0.5, color="#5e35b1", edgecolor="black", linewidth=0.8)
    ax1.text(1, b2_prom / b2_rounds + 0.022, f"{b2_prom}/{b2_rounds} 轮（37.5%）", ha="center",
             fontsize=10, color="#1565c0")
    ax1.text(2, b3_prom / b3_rounds + 0.022, f"{b3_prom}/{b3_rounds} 轮（50.0%）", ha="center",
             fontsize=10, color="#5e35b1")
    ax1.text(0, 0.028, "—（单轮提案批，\n无轮级提升概念）", ha="center", fontsize=9.6, color="#616161")
    ax1.text(1, -0.062, "板级 6/14（提升板\n全在 8 块 FAILED 板）", ha="center", fontsize=8.8, color="#37474f")
    ax1.text(2, -0.062, "板级 4/7\n（FAILED 域 4/5）", ha="center", fontsize=8.8, color="#37474f")
    ax1.set_xticks(list(xs))
    ax1.set_xticklabels(cats, fontsize=9.6)
    ax1.set_ylim(-0.005, 0.62)
    ax1.set_yticks([0, 0.125, 0.25, 0.375, 0.5])
    ax1.set_yticklabels(["0%", "12.5%", "25%", "37.5%", "50%"])
    ax1.set_ylabel("轮级提升轮占比", fontsize=10.5)
    ax1.set_title("(a) 轮内机制真实激活：提升轮（探针晋升）\n在多轮批真实发生且集中在 FAILED 域", fontsize=11)
    ax1.grid(axis="y", alpha=0.25)

    # (b) 终解层：③==② 字节等 vs 模型增量
    eq_rates = [b1_eq / b1_boards, b2_eq / b2_boards, b3_eq / b3_boards]
    inc_rates = [b1_inc / b1_boards, 0, b3_inc / b3_boards]
    eq_labels = [f"{b1_eq}/{b1_boards}", f"{b2_eq}/{b2_boards}", f"{b3_eq}/{b3_boards}"]
    inc_labels = [f"0/{b1_boards}", f"0/{b2_boards}", f"0/{b3_boards}"]
    w = 0.34
    x1 = [x - w / 2 for x in xs]
    x2 = [x + w / 2 for x in xs]
    ax2.bar(x1, eq_rates, width=w, color="#90a4ae", edgecolor="black", linewidth=0.8,
            label="③==② 终解与基线 canonical 字节等")
    ax2.bar(x2, inc_rates, width=w, color="#c62828", edgecolor="black", linewidth=0.8,
            label="终解模型增量（g4 model_increment）")
    for x, v, lab in zip(x1, eq_rates, eq_labels):
        ax2.text(x, v + 0.03, lab, ha="center", fontsize=10, color="#455a64")
    for x, lab in zip(x2, inc_labels):
        ax2.text(x, 0.035, lab, ha="center", fontsize=10, color="#c62828", fontweight="bold")
    ax2.set_xticks(list(xs))
    ax2.set_xticklabels(cats, fontsize=9.6)
    ax2.set_ylim(0, 1.24)
    ax2.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax2.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax2.set_ylabel("板数占比", fontsize=10.5)
    ax2.set_title("(b) 终解层三批一致：终解增量全零\n（A4 终选按 canonical 指纹兜底回基线）", fontsize=11)
    ax2.legend(loc="upper center", fontsize=9.2, frameon=False, ncol=1)
    ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("席位 B 真实板三批对照（会话波 ⑥后世界 / RESTORE ⑥后世界 / SUPPLEMENT D8 世界）："
                 "轮内有提升、终解增量三批全零", fontsize=12, y=0.99)
    fig.savefig(OUT, dpi=300)
    plt.close(fig)
    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或 <10KB"
    print(f"[done] {OUT}  size={os.path.getsize(OUT)}B")


if __name__ == "__main__":
    main()
