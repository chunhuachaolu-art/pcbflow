# -*- coding: utf-8 -*-
"""
篇六 图 10：run8–13 直布线经济学瀑布
  (a) run8 封死栅 token 瀑布：S4 三轮烧损 396,881（占席位总开销 458,590 的 86.5%
      ＝「检测先于派发」省额）＋S6 重布 61,709 → 合计 458,590；
  (b) run12 召回协商溢价：+3V3 召回链 3 席 932,383 ＝ 首波席 132,135 的 7.06×；
      /SDA 重试席 474,469 ＝ 首波席 93,868 的 5.06×（HN-2 协商显著贵）；
  (c) run13 成批仲裁：五席 8,553,415 ＝ run11-armB 全程 1,983,297 的 4.31×；
      剔除 +3V3 异常席（6,557,198）后 1,996,217 ≈ 持平。

数据来源（全部直读机器件，零硬编码数据点）：
  - out/net-agent-p1/run8/RESULT.md（r04/r05/r06/r08 tokens 轮次表解析）
  - out/net-agent-p1/run11-armA/tokens.jsonl（20 行，和=2,147,011）
  - out/net-agent-p1/run11-armB/tokens.jsonl（17 行，和=1,983,297；+3V3 首波 132,135、
    /SDA 首波 93,868 ＝协商溢价基数）
  - out/net-agent-p1/run12/tokens.jsonl（4 行；+3V3 召回链 3 行、/SDA 重试 1 行）
  - out/net-agent-p1/run13/tokens.jsonl（5 行；+3V3 异常席 6,557,198）
  - out/net-agent-p1/run12/RESULT.md、run13/RESULT.md（读数交叉对账）
sha256 锚（程序化重算，锚值=P6 正文 §8.5/§8.6 与 BRIEFING §1.3 登记）：
  run8/RESULT.md sha16 = 549f438538e5890f
  run12/LEAD-REVIEW-RUN12-2026-09-28.md sha16 = f9843cc2ce67e92e
  run11/LEAD-REVIEW-RUN11-2026-09-28.md sha16 = 051255e129638b75
"""
import hashlib
import json
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

R8_RES = "<ENGINE_ROOT>/out/net-agent-p1/run8/RESULT.md"
A11 = "<ENGINE_ROOT>/out/net-agent-p1/run11-armA/tokens.jsonl"
B11 = "<ENGINE_ROOT>/out/net-agent-p1/run11-armB/tokens.jsonl"
T12 = "<ENGINE_ROOT>/out/net-agent-p1/run12/tokens.jsonl"
T13 = "<ENGINE_ROOT>/out/net-agent-p1/run13/tokens.jsonl"
RES12 = "<ENGINE_ROOT>/out/net-agent-p1/run12/RESULT.md"
RES13 = "<ENGINE_ROOT>/out/net-agent-p1/run13/RESULT.md"
LR12 = "<ENGINE_ROOT>/out/net-agent-p1/run12/LEAD-REVIEW-RUN12-2026-09-28.md"
LR11 = "<ENGINE_ROOT>/out/net-agent-p1/run11/LEAD-REVIEW-RUN11-2026-09-28.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P6-10-V8-RUN8-13-ECON-WATERFALL.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load_tokens(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def parse_r8_tokens(result_text):
    tok = {}
    for line in result_text.splitlines():
        m = re.match(r"\|\s*(r\d+)\s*\|", line)
        if m:
            mm = re.search(r"\|\s*([\d,]{4,})\s*\|\s*$", line)
            if mm:
                tok[m.group(1)] = int(mm.group(1).replace(",", ""))
    return tok


def main():
    # ---------- 断言层 1：sha16 锚程序化重算 ----------
    assert sha16(R8_RES) == "549f438538e5890f", f"run8 RESULT sha16={sha16(R8_RES)}"
    assert sha16(LR12) == "f9843cc2ce67e92e", f"run12 LEAD-REVIEW sha16={sha16(LR12)}"
    assert sha16(LR11) == "051255e129638b75", f"run11 LEAD-REVIEW sha16={sha16(LR11)}"

    # ---------- (a) run8：token 瀑布（RESULT 轮次表解析） ----------
    tok = parse_r8_tokens(open(R8_RES, encoding="utf-8").read())
    assert tok.get("r04") == 84083 and tok.get("r05") == 124910 and tok.get("r06") == 187888
    assert tok.get("r08") == 61709
    s4_burn = tok["r04"] + tok["r05"] + tok["r06"]
    s6 = tok["r08"]
    total8 = s4_burn + s6
    assert (s4_burn, s6, total8) == (396881, 61709, 458590)
    saving = s4_burn / total8
    assert abs(saving - 0.865) < 5e-4, f"检测省额应 86.5%，实得 {saving:.4f}"

    # ---------- (b) run12：协商溢价（tokens.jsonl 直算） ----------
    armA, armB, t12, t13 = load_tokens(A11), load_tokens(B11), load_tokens(T12), load_tokens(T13)
    assert len(armA) == 20 and len(armB) == 17 and len(t12) == 4 and len(t13) == 5
    assert sum(r["tokens"] for r in armA) == 2147011, "run11-armA 和应 2,147,011"
    b_total = sum(r["tokens"] for r in armB)
    assert b_total == 1983297, "run11-armB 和应 1,983,297"
    assert sum(r["tokens"] for r in t12) == 1406852, "run12 和应 1,406,852"
    v33_chain = [r for r in t12 if r["net"] == "+3V3"]
    assert len(v33_chain) == 3
    v33_chain_sum = sum(r["tokens"] for r in v33_chain)
    base_v33 = [r for r in armB if r["net"] == "+3V3" and r["round"] == 1][0]["tokens"]
    sda_retry = [r for r in t12 if r["net"] == "/SDA"][0]["tokens"]
    base_sda = [r for r in armB if r["net"] == "/SDA" and r["round"] == 6][0]["tokens"]
    assert (v33_chain_sum, base_v33, sda_retry, base_sda) == (932383, 132135, 474469, 93868)
    r_v33, r_sda = v33_chain_sum / base_v33, sda_retry / base_sda
    assert round(r_v33, 2) == 7.06, f"+3V3 溢价 {r_v33:.4f}"
    # /SDA：机器算 474,469/93,868=5.0546→5.05×；run12/RESULT L30 与 P6 §8.6 写 5.06×
    # （0.01 舍入向差）——按「机器件为准＋图注披露」处置，不代裁。
    assert abs(r_sda - 5.0546) < 2e-4, f"/SDA 溢价机器值 {r_sda:.4f}"
    res12 = open(RES12, encoding="utf-8").read()
    assert re.search(r"932,383 tokens，对照其 run11-armB 首波席 132,135 = \*\*7\.06×\*\*", res12)
    assert re.search(r"474,469，对照其 run11-armB 首波席 93,868 = 5\.06×", res12)

    # ---------- (c) run13：仲裁成本（tokens.jsonl 直算） ----------
    t13_total = sum(r["tokens"] for r in t13)
    anom = [r for r in t13 if r["net"] == "+3V3"][0]
    others = t13_total - anom["tokens"]
    assert (t13_total, anom["tokens"], others) == (8553415, 6557198, 1996217)
    r_arb = t13_total / b_total
    assert round(r_arb, 2) == 4.31, f"仲裁倍率 {r_arb:.3f}"
    assert abs(others / b_total - 1.0) < 7e-3, "剔除异常席后应≈持平"
    res13 = open(RES13, encoding="utf-8").read()
    assert re.search(r"8,553,415 tokens（\+3V3 6,557,198", res13)
    assert re.search(r"剔除 \+3V3 异常席后 1,996,217≈持平", res13)
    assert re.search(r"1,983,297=4\.31×", res13)

    # ---------- 绘图 ----------
    fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(15.2, 6.8), dpi=220)
    RED, BLUE, GREY, PURP = "#c62828", "#1565c0", "#78909c", "#6a1b9a"

    # (a) run8 瀑布
    axa.bar([0], [s4_burn], width=0.6, color=RED, alpha=0.92)
    axa.bar([1], [s6], bottom=[s4_burn], width=0.6, color=BLUE, alpha=0.92)
    axa.bar([2], [total8], width=0.6, color=GREY, alpha=0.92)
    axa.axhline(s4_burn, color=RED, ls="--", lw=1.3, alpha=0.8)
    axa.text(-0.42, s4_burn + 9000, f"S4 三轮烧损 {s4_burn:,}\n（三轮拒收：北墙正穿→顶带孔区→南逃东墙，零 V 铜）",
             fontsize=10.2, color=RED, fontweight="bold")
    axa.text(1, s4_burn + s6 / 2, f"+S6 重布\n{s6:,}", ha="center", va="center",
             fontsize=10.4, color="white", fontweight="bold")
    axa.text(2, total8 / 2, f"合计\n{total8:,}", ha="center", va="center",
             fontsize=10.6, color="white", fontweight="bold")
    axa.annotate(f"检测省额＝{saving:.1%}\n（S3 后即跑封锁扫描，S4 三轮全免）",
                 xy=(0.0, s4_burn * 0.55), xytext=(0.62, 235000), fontsize=10.6, color=RED,
                 arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    axa.set_xticks([0, 1, 2])
    axa.set_xticklabels(["S4 烧损\n（3 轮席位拒收）", "S6 重布\n（2/2 受理 71 步）", "run8 席位\n总开销"], fontsize=10.4)
    axa.set_ylim(0, 560000)
    axa.set_title("(a) run8 封死栅：烧损与检测省额瀑布\n（首获席位 token 遥测）", fontsize=12.4)

    # (b) run12 协商溢价
    xs = [0, 1, 2.6, 3.6]
    vals = [base_v33, v33_chain_sum, base_sda, sda_retry]
    cols = [BLUE, PURP, BLUE, PURP]
    axb.bar(xs, vals, width=0.62, color=cols, alpha=0.9)
    for x, v in zip(xs, vals):
        axb.text(x, v + 16000, f"{v:,}", ha="center", fontsize=10.6, fontweight="bold")
    axb.annotate("", xy=(1, v33_chain_sum), xytext=(0, base_v33),
                 arrowprops=dict(arrowstyle="->", color=PURP, lw=1.6))
    axb.text(0.5, 760000, f"×{r_v33:.2f}", ha="center", fontsize=14, color=PURP, fontweight="bold")
    axb.text(3.1, 420000, f"×{r_sda:.2f}", ha="center", fontsize=14, color=PURP, fontweight="bold")
    axb.text(1.8, 1035000, "注：/SDA 机器算 474,469/93,868＝5.0546→×5.05；run12/RESULT L30 与正文 §8.6 记 ×5.06（0.01 舍入向差），此处按机器件口径标注并披露",
             ha="center", fontsize=8.8, color="#616161")
    axb.set_xticks(xs)
    axb.set_xticklabels(["+3V3 首波席\n（run11-armB r01）", "+3V3 召回链\n（run12 三席 r18/19/20）",
                         "/SDA 首波席\n（run11-armB r06）", "/SDA 重试席\n（run12 r22）"], fontsize=9.8)
    axb.set_ylim(0, 1080000)
    axb.set_title("(b) run12 召回协商溢价（HN-2：协商显著贵）\n"
                  f"召回链 {v33_chain_sum:,} tokens vs 首波席 {base_v33:,}", fontsize=12.4)

    # (c) run13 仲裁
    axc.bar([0], [b_total], width=0.58, color=BLUE, alpha=0.9)
    axc.bar([1], [others], width=0.58, color="#2e7d32", alpha=0.9,
            label="常规四席（/RESET//SCL/两回叫席）")
    axc.bar([1], [anom["tokens"]], bottom=[others], width=0.58, color=RED, alpha=0.9,
            label="+3V3 异常席（F-6' 自证深度无上限）")
    axc.text(0, b_total + 130000, f"{b_total:,}", ha="center", fontsize=10.8, fontweight="bold", color=BLUE)
    axc.text(1, t13_total + 130000, f"{t13_total:,}", ha="center", fontsize=10.8, fontweight="bold", color=RED)
    axc.text(1, others / 2, f"{others:,}", ha="center", va="center", fontsize=10.2,
             color="white", fontweight="bold")
    axc.text(1, others + anom["tokens"] / 2, f"{anom['tokens']:,}", ha="center", va="center",
             fontsize=10.2, color="white", fontweight="bold")
    axc.annotate(f"×{r_arb:.2f}", xy=(0.5, 6300000), fontsize=15, color=RED,
                 fontweight="bold", ha="center")
    axc.axhline(b_total, color=BLUE, ls="--", lw=1.2, alpha=0.8)
    axc.text(1.52, b_total - 700000, f"剔除异常席后 {others:,}\n≈ 对照 {b_total:,}（持平）",
             fontsize=10.0, color="#2e7d32", ha="center",
             bbox=dict(fc="#e8f5e9", ec="#a5d6a7", boxstyle="round,pad=0.32"))
    axc.set_xticks([0, 1])
    axc.set_xticklabels(["对照：run11-armB 全程\n（17 轮 7/9）", "run13 臂 B 成批仲裁\n（五席，终态 6/9）"], fontsize=10.2)
    axc.set_ylim(0, 9900000)
    axc.legend(fontsize=9.2, loc="upper left", framealpha=0.9)
    axc.set_title("(c) run13 成批仲裁：4.31× 与异常席剔除\n（HB-2 可量化；+3V3 十端网板固死端 9/10）", fontsize=12.4)

    for ax in (axa, axb, axc):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", ls=":", alpha=0.4)
        ax.set_ylabel("tokens", fontsize=10.6)
        ax.yaxis.set_major_formatter(lambda v, _: f"{int(v):,}")
    fig.suptitle("图 10　run8–13 直布线经济学瀑布：检测省额 86.5%／协商 7.06×／仲裁 4.31×／剔除异常席后持平",
                 fontsize=15.5, fontweight="bold", y=1.0)
    fig.text(0.5, 0.008,
             "数据源：run8/RESULT.md 轮次表（sha16=549f438538e5890f 重算一致）＋run11-armA/armB、run12、run13 tokens.jsonl 逐席直算；"
             "LEAD-REVIEW 锚 f9843cc2ce67e92e／051255e129638b75 重算一致；run12/run13 RESULT 读数句 regex 对账",
             ha="center", fontsize=9.4, color="#616161")
    fig.tight_layout(rect=(0, 0.032, 1, 0.95))
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或过小"
    print("OK 图 10：", OUT, os.path.getsize(OUT), "B")
    print(f"  (a) S4 {s4_burn:,} + S6 {s6:,} = {total8:,}，省额 {saving:.1%}")
    print(f"  (b) +3V3 {v33_chain_sum:,}/{base_v33:,}={r_v33:.2f}×；/SDA {sda_retry:,}/{base_sda:,}={r_sda:.2f}×")
    print(f"  (c) run13 {t13_total:,} = {r_arb:.2f}× armB {b_total:,}；剔除异常席 {others:,} ≈ 持平")


if __name__ == "__main__":
    main()
