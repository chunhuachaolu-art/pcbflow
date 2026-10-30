# -*- coding: utf-8 -*-
"""
篇六 图 8：ripup vs 绕行成本柱状图（run6 中等栅 + run8 封死栅并列）
  A＝无栅基线 59 格步；B＝绕行（S4 西绕）73 步＝+14（+24%）；
  C＝拆栅重布（S6）59 步＝C−A=0（仅换列）；封死栅下绕行=∞（C3 机械封锁证明）、
  拆栅唯一解（run8：S6 71 步；S4 三轮拒收烧 396,881 tokens 零 V 铜）。

数据来源（全部直读机器件，零硬编码数据点）：
  - out/net-agent-p1/run6/ledger.jsonl（S1/S4/S6 路径格步=waypoints 曼哈顿和直算）
  - out/net-agent-p1/run6/RESULT.md（六阶段账交叉对账）
  - out/net-agent-p1/run8/ledger.jsonl（S1=59、S4 三轮拒收、S6=71 直算）
  - out/net-agent-p1/run8/fence-probes/seal-proof.json（C2 封栅前 BFS 最短 59；
    C3 封栅后 post_reachable=false → 绕行=∞ 机械证明）
  - out/net-agent-p1/run8/RESULT.md（r04/r05/r06/r08 席位 tokens 遥测轮次表解析）
sha256 锚（程序化重算，锚值=P6 正文 §7.1/§8.2 与 BRIEFING §1.3 登记）：
  run6/RESULT.md sha16 = 0fcb9145e5c4d0bf；run8/RESULT.md sha16 = 549f438538e5890f
"""
import hashlib
import json
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Rectangle

R6_LED = "<ENGINE_ROOT>/out/net-agent-p1/run6/ledger.jsonl"
R6_RES = "<ENGINE_ROOT>/out/net-agent-p1/run6/RESULT.md"
R8_LED = "<ENGINE_ROOT>/out/net-agent-p1/run8/ledger.jsonl"
R8_SP = "<ENGINE_ROOT>/out/net-agent-p1/run8/fence-probes/seal-proof.json"
R8_RES = "<ENGINE_ROOT>/out/net-agent-p1/run8/RESULT.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P6-08-RIPUP-VS-DETOUR-COST.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load_ledger(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def grid_steps(wps):
    """台账格点坐标的路径格步（曼哈顿和；P6 §7.1 口径）。"""
    return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(wps, wps[1:]))


def v_net_route(row, net):
    """该轮受害网 V 的 route 动作与受理态。"""
    acc = {a["index"] for a in row["accepted"]}
    for i, b in enumerate(row["batch"]):
        if b.get("action") == "route" and b.get("net_id") == net:
            return b, (i in acc)
    return None, None


def parse_r8_tokens(result_text):
    """run8/RESULT.md 轮次表：席位轮的 tokens 列（如 84,083）。"""
    tok = {}
    for line in result_text.splitlines():
        m = re.match(r"\|\s*(r\d+)\s*\|", line)
        if not m:
            continue
        mm = re.search(r"\|\s*([\d,]{4,})\s*\|\s*$", line)
        if mm:
            tok[m.group(1)] = int(mm.group(1).replace(",", ""))
    return tok


def main():
    rows6, rows8 = load_ledger(R6_LED), load_ledger(R8_LED)
    assert [r["round"] for r in rows6] == list(range(1, 8)), "run6 台账应 7 轮"
    assert [r["round"] for r in rows8] == list(range(1, 9)), "run8 台账应 8 轮"

    # ---------- 断言层 1：sha16 锚程序化重算 ----------
    assert sha16(R6_RES) == "0fcb9145e5c4d0bf", f"run6 RESULT sha16={sha16(R6_RES)}"
    assert sha16(R8_RES) == "549f438538e5890f", f"run8 RESULT sha16={sha16(R8_RES)}"

    # ---------- run6 台账直算：A/B/C 三支路格步 ----------
    V = "Net-(D1-Pad1)"
    a6, acc = v_net_route(rows6[0], V)
    assert acc, "run6 S1 基线应受理"
    A = grid_steps(a6["waypoints"])
    b6, acc = v_net_route(rows6[3], V)
    assert acc, "run6 S4 绕行应受理"
    B = grid_steps(b6["waypoints"])
    c6, acc = v_net_route(rows6[6], V)
    assert acc, "run6 S6 重布应受理"
    C = grid_steps(c6["waypoints"])
    assert (A, B, C) == (59, 73, 59), f"run6 应 59/73/59，实得 {A}/{B}/{C}"
    r6_text = open(R6_RES, encoding="utf-8").read()
    for st in (59, 73):
        assert re.search(rf"= {st} 步", r6_text), f"run6 RESULT 未匹配「{st} 步」"
    assert B - A == 14 and abs((B - A) / A - 0.24) < 5e-3, "绕行溢价应 +14 步（+24%）"
    assert C - A == 0, "拆栅重布 C−A 应 0 步"

    # ---------- run8 台账直算：S1/S4×3 拒/S6；seal-proof C2/C3 ----------
    a8, acc = v_net_route(rows8[0], V)
    assert acc and grid_steps(a8["waypoints"]) == 59, "run8 S1 基线应 59 步受理"
    s4 = []
    for row in rows8[3:6]:
        rt, acc = v_net_route(row, V)
        assert rt is not None and not acc, f"run8 轮 {row['round']} S4 应拒收"
        s4.append((row["round"], grid_steps(rt["waypoints"]),
                   next(a["code"] for a in row["rejected"])))
    c8, acc = v_net_route(rows8[7], V)
    assert acc, "run8 S6 应受理"
    C8 = grid_steps(c8["waypoints"])
    assert C8 == 71, f"run8 S6 应 71 步，实得 {C8}"

    sp = json.load(open(R8_SP, encoding="utf-8"))
    assert sp["v_net"] == V and sp["outcome"] == "SEALED"
    assert sp["C2_pre_fence_reachable"] is True and sp["C2_shortest_grid_steps"] == 59
    tr = sp["trials"][0]
    assert tr["C3_sealed"] is True and tr["post_reachable"] is False, "C3 封栅后应不可达"

    # ---------- run8 tokens：RESULT 轮次表解析 + 求和对账 ----------
    r8_text = open(R8_RES, encoding="utf-8").read()
    tok = parse_r8_tokens(r8_text)
    assert tok.get("r04") == 84083 and tok.get("r05") == 124910 and tok.get("r06") == 187888, (
        f"S4 三轮 tokens 解析异常：{tok}")
    assert tok.get("r08") == 61709, f"S6 tokens 解析异常：{tok}"
    s4_burn = tok["r04"] + tok["r05"] + tok["r06"]
    total = s4_burn + tok["r08"]
    assert (s4_burn, total) == (396881, 458590), f"token 账应 396,881/458,590，实得 {s4_burn}/{total}"
    saving = s4_burn / total
    assert abs(saving - 0.865) < 5e-4, f"检测省额应 86.5%，实得 {saving:.4f}"

    # ---------- 绘图 ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.8, 6.6), dpi=220)
    CY_A, CY_B, CY_C = "#1565c0", "#ef6c00", "#2e7d32"

    bars1 = ax1.bar([0, 1, 2], [A, B, C], width=0.58,
                    color=[CY_A, CY_B, CY_C], alpha=0.92)
    ax1.set_xticks([0, 1, 2])
    ax1.set_xticklabels(["A＝无栅基线\n（S1 席位 1 轮 0 回叫）",
                         "B＝绕行\n（S4 西绕，1 轮 0 回叫）",
                         "C＝拆栅重布\n（S6，1 轮 0 回叫\n＋拆栅 FORCE 2 轮 ≈0 token）"],
                       fontsize=10.6)
    for x, v in zip([0, 1, 2], [A, B, C]):
        ax1.text(x, v + 1.2, f"{v} 格步", ha="center", fontsize=12.5, fontweight="bold")
    ax1.annotate(f"B−A＝+{B-A} 步（+{(B-A)/A:.0%}）\n绕行长度永久背负", xy=(1, B), xytext=(1.52, 84),
                 fontsize=11, color=CY_B, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=CY_B, lw=1.4))
    ax1.annotate(f"C−A＝{C-A} 步（仅换列）\n＋机械成本一次性（≈0 token）", xy=(2, C), xytext=(2.35, 40),
                 fontsize=11, color=CY_C, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=CY_C, lw=1.4))
    ax1.set_ylim(0, 96)
    ax1.set_ylabel("路径成本（格步，直算自台账 waypoints 曼哈顿和）", fontsize=11)
    ax1.set_title("run6 中等栅（东/西旁路恒开）：绕行可行但 +24%\n判别不等式实测：ripup（0 步＋机械≈0）严格优于绕行", fontsize=12.6)

    # run8：绕行=∞（C3 证明）以截断阴影柱表达
    xs = [0, 1, 2]
    labels = ["S1 基线\n（席位 59 步＝C2 BFS\n三次独立复现之一）",
              "S4 封死栅绕行\n（C3 BFS 不可达）",
              "S6 拆栅重布\n（拆栅 FORCE ≈0 token\n＋席位 71 步）"]
    ax2.bar([0], [59], width=0.58, color=CY_A, alpha=0.92)
    ax2.bar([2], [71], width=0.58, color=CY_C, alpha=0.92)
    ax2.add_patch(Rectangle((0.71, 88), 0.58, 8, facecolor="#c62828", alpha=0.5,
                            hatch="///", edgecolor="#c62828", lw=1.2))
    ax2.add_patch(Rectangle((0.71, 78), 0.58, 8, facecolor="white", edgecolor="#c62828", lw=1.2, zorder=5))
    ax2.add_patch(Rectangle((0.71, 70), 0.58, 8, facecolor="#c62828", alpha=0.5,
                            hatch="///", edgecolor="#c62828", lw=1.2, zorder=6))
    ax2.text(1.0, 100.5, "∞", ha="center", fontsize=26, color="#c62828", fontweight="bold")
    ax2.text(0, 61.5, "59 格步", ha="center", fontsize=12.5, fontweight="bold")
    ax2.text(2, 73.5, "71 格步（+20%）", ha="center", fontsize=12.5, fontweight="bold")
    ax2.text(1, 66, "唯一解＝拆栅\n（机械轮）", ha="center", fontsize=10.8, color="#c62828")
    ax2.set_xticks(xs)
    ax2.set_xticklabels(labels, fontsize=10.6)
    ax2.set_ylim(0, 112)
    ax2.set_title("run8 封死栅（R7 双层闭环 i∈[23,35]×j∈[1,8]）：绕行=∞\n"
                  f"S4 三轮席位拒收烧 {s4_burn:,} tokens 零 V 铜 → 检测省额 {saving:.1%}"
                  f"（token 账 {total:,}＝S4 {s4_burn:,}＋S6 {tok['r08']:,}）",
                  fontsize=12.6)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", ls=":", alpha=0.45)
    fig.suptitle("图 8　ripup vs 绕行成本：run6 中等栅与 run8 封死栅并列（格步直算自 run6/run8 台账）",
                 fontsize=15.5, fontweight="bold", y=0.995)
    fig.text(0.5, 0.012,
             "数据源：run6/ledger.jsonl 与 run8/ledger.jsonl（格步=waypoints 曼哈顿和直算）；run8/fence-probes/seal-proof.json（C2=59/C3 不可达）；"
             "tokens=run8/RESULT.md 轮次表（sha16 锚 0fcb9145e5c4d0bf／549f438538e5890f 程序化重算一致）",
             ha="center", fontsize=9.6, color="#616161")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或过小"
    print("OK 图 8：", OUT, os.path.getsize(OUT), "B")
    print("  run6 A/B/C =", A, B, C, f"(+{B-A} 步 +{(B-A)/A:.0%}; C−A={C-A})")
    print("  run8 S4 拒收三轮 =", s4, "S6 =", C8, "tokens", s4_burn, "/", total, f"省额 {saving:.1%}")


if __name__ == "__main__":
    main()
