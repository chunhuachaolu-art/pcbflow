# -*- coding: utf-8 -*-
"""
FIG-P4-08-LOO-AUC-DUAL-ARM — 篇四图 8 LOO-AUC 双臂（LR/GBDT×主/敏感性口径）（候选图）

数据件（全部机器件直读，禁硬编码）：
  - <ENGINE_ROOT>/out/routability-r1/metrics.json（calibers 双口径 AUC/CI/loo_predictions）
  - <ENGINE_ROOT>/out/routability-r1/PREREG-ROUTABILITY-R1.md（特征表区块 sha256 程序化重算锚）
  - <ENGINE_ROOT>/out/routability-r1/FREEZE-RECORD.json（冻结链比对）
产出：<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-08-LOO-AUC-DUAL-ARM.png
"""
import hashlib
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

C_BLUE = "#4c72b0"; C_ORANGE = "#dd8452"; C_RED = "#c44e52"; C_GRAY = "#8c8c8c"

M = json.load(open("<ENGINE_ROOT>/out/routability-r1/metrics.json", encoding="utf-8"))
cal = M["calibers"]
assert cal["main"]["n"] == 13 and cal["main"]["n_pos"] == 4 and cal["main"]["n_neg"] == 9, "主口径 n=13（4+/9−）断言失败"
assert cal["sensitivity"]["n"] == 16 and cal["sensitivity"]["n_pos"] == 4 and cal["sensitivity"]["n_neg"] == 12, "敏感性 n=16 断言失败"
assert M["n_boards_feature_matrix"] == 20 and M["defensive_exclusions"][0]["board"] == "throwing-star-pro", "20 板/剔除 1 断言失败"
assert cal["main"]["lr"]["auc"] == 1.0 and cal["main"]["gbdt"]["auc"] == 0.75, "主口径 AUC 锚断言失败"
assert abs(cal["sensitivity"]["lr"]["auc"] - 5 / 6) < 1e-12 and cal["sensitivity"]["gbdt"]["auc"] == 0.75, "敏感性 AUC 锚断言失败"

# 特征表冻结 sha256 程序化重算锚（禁手抄）
prereg_txt = open("<ENGINE_ROOT>/out/routability-r1/PREREG-ROUTABILITY-R1.md", encoding="utf-8").read()
mb = re.search(r"<!-- FEATURE-TABLE-START -->(.*?)<!-- FEATURE-TABLE-END -->", prereg_txt, re.S)
assert mb, "特征表区块标记未定位"
block_sha = hashlib.sha256(mb.group(1).encode("utf-8")).hexdigest()
fr = json.load(open("<ENGINE_ROOT>/out/routability-r1/FREEZE-RECORD.json", encoding="utf-8"))
assert block_sha == fr["feature_table_sha256"] == M["prereg_freeze_sha256"], "冻结链三件 sha 一致断言失败"
assert block_sha.startswith("ea0a275f"), "sha16=ea0a275f 断言失败"

def auc_mw(y, p):
    """Mann-Whitney AUC（平均秩处理并列）"""
    y = np.asarray(y); p = np.asarray(p)
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p), float)
    sp = p[order]; i = 0
    while i < len(sp):
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    pos = ranks[y == 1].sum(); n1 = int((y == 1).sum()); n0 = int((y == 0).sum())
    return (pos - n1 * (n1 + 1) / 2.0) / (n1 * n0)

def roc(y, p):
    y = np.asarray(y); p = np.asarray(p)
    thr = np.unique(np.concatenate([[p.min() - 1], np.sort(p)[::-1], [p.max() + 1]]))[::-1]
    pts = []
    for t in thr:
        tp = int(((p >= t) & (y == 1)).sum()); fp = int(((p >= t) & (y == 0)).sum())
        pts.append((fp / max(1, (y == 0).sum()), tp / max(1, (y == 1).sum())))
    return np.array(pts)

fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6))
panels = [("main", "lr", C_BLUE, "主口径（n=13＝4 可布＋9 固有不可布）· LR"),
          ("main", "gbdt", C_ORANGE, "主口径（n=13）· GBDT"),
          ("sensitivity", "lr", "#8172b3", "敏感性口径（n=16＝4＋12）· LR"),
          ("sensitivity", "gbdt", C_RED, "敏感性口径（n=16）· GBDT")]
for ax, (ck, arm, col, title) in zip(axes.flat, panels):
    c = cal[ck]
    lp = c["loo_predictions"]
    y = [e["y_true"] for e in lp]; p = [e["p_" + arm] for e in lp]
    assert len(lp) == c["n"], "loo 预测数=n 断言失败"
    auc_r = auc_mw(y, p)
    assert abs(auc_r - c[arm]["auc"]) < 1e-9, "AUC 程序化重算≠机器件 %s/%s: %r vs %r" % (ck, arm, auc_r, c[arm]["auc"])
    pts = roc(y, p)
    ax.step(pts[:, 0], pts[:, 1], where="post", color=col, lw=2.6)
    ax.fill_between(pts[:, 0], pts[:, 1], step="post", color=col, alpha=0.14)
    ax.plot([0, 1], [0, 1], ls="--", lw=1.2, color=C_GRAY)
    lo, hi = c[arm]["auc_ci95"]
    ax.set_title("%s\nLOO-AUC=%.3f（重算=%.3f，逐位一致）　bootstrap B=2000 CI95=[%s, %s]" % (
        title, c[arm]["auc"], auc_r, lo, hi), fontsize=10.6)
    ax.set_xlabel("假正率（不可布板误判为可布）", fontsize=9.5)
    ax.set_ylabel("真正率", fontsize=9.5)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.06)
    ax.set_aspect("equal")
    ax.grid(ls=":", alpha=0.4)
    if ck == "main" and arm == "lr":
        ax.text(0.5, 0.06, "完全分离读数（CI=[1,1]）\n不构成判别力断言", ha="center", fontsize=9.2,
                color="#8a2f33", fontweight="bold",
                bbox=dict(fc="#fdf0ee", ec=C_RED, boxstyle="round,pad=0.3"))

fi_lr = cal["main"]["feature_importance_rank"]["lr"]
fi_gb = cal["main"]["feature_importance_rank"]["gbdt"]
ranks = {}
for ck in ("main", "sensitivity"):
    for arm in ("lr", "gbdt"):
        ranks[(ck, arm)] = [x["feature"] for x in cal[ck]["feature_importance_rank"][arm][:5]]
# 机器件严格读数断言（metrics.json feature_importance_rank 逐臂）：
# ①四组合头名全部 ∈ {F13, F25}；②F13 四组合全进前二；③F25 双 GBDT 臂第 1；④F27 三组合进前三、敏感性 GBDT 其余 26 条全 0
assert all(ranks[k][0] in ("F13", "F25") for k in ranks), "头名 ∈{F13,F25} 断言失败"
assert all(ranks[k].index("F13") <= 1 for k in ranks), "F13 全前二断言失败"
assert ranks[("main", "gbdt")][0] == "F25" and ranks[("sensitivity", "gbdt")][0] == "F25", "F25 双 GBDT 第 1 断言失败"
assert ranks[("main", "lr")][2] == "F27" and ranks[("main", "gbdt")][2] == "F27" and ranks[("sensitivity", "lr")][1] == "F27", "F27 三组合前三断言失败"
nz_sens_gbdt = [x["feature"] for x in cal["sensitivity"]["feature_importance_rank"]["gbdt"] if x["importance"] > 0]
assert set(nz_sens_gbdt) == {"F25", "F13"}, "敏感性 GBDT 非零仅 F25/F13 断言失败"
coef13 = [x for x in fi_lr if x["feature"] == "F13"][0]["coef"]
imp25 = [x for x in fi_gb if x["feature"] == "F25"][0]["importance"]
assert abs(coef13 - 0.5025401638010503) < 1e-12 and abs(imp25 - 0.4664499240774765) < 1e-12, "F13/F25 系数断言失败"

fig.suptitle("篇四图 8　进场预测器 v0：LOO-AUC 双臂×双口径（候选图；特征排序 F13/F27/F25 跨臂稳定）",
             fontsize=14, fontweight="bold", y=0.995)
fig.text(0.5, 0.017,
         "数据源：out/routability-r1/metrics.json（calibers.main/sensitivity 的 AUC/CI/loo_predictions 直读；每面板 AUC 由 loo_predictions 以 Mann-Whitney 秩法程序化重算，逐位一致断言）。\n"
         "冻结链锚：PREREG 特征表区块 sha256 程序化重算=%s…＝FREEZE-RECORD.feature_table_sha256＝metrics.prereg_freeze_sha256（三件一致，前 16 位 ea0a275f）。\n"
         "特征排序（metrics.json feature_importance_rank 严格读数）：四组合头名全部 ∈ {F13, F25}——F13 通孔盘占比（LR 主口径 coef=%+.4f，LR 两口径第 1）、F25 障碍密度（GBDT importance=%.4f，GBDT 两口径第 1）；\n"
         "F27 最近邻焊盘间距进主口径双臂（第 3）与敏感性 LR（第 2）前三。注：F25 在 LR 两口径未入前三（主口径第 5、敏感性前 5 未入）、敏感性 GBDT 非零仅 F25/F13（其余 26 条全 0）——正文 §6.4「四组合前三全部由三条占据」系报告 L78 概括句沿用，本图按机器件逐臂读数如实呈现（差异随批披露，不代裁）。\n"
         "F13 方向与冻结先验相反（实数据押「贴片密布才难布」：正类组均值 0.908 vs 负类 0.123，预注册纪律下如实记录这一反转）。\n"
         "结论措辞冻结＝「%s」（不得外推为「预测器可用」）；20 板特征矩阵剔除 throwing-star-pro（board.json 缺失=convert 同败，defensive_exclusions）。候选图，画否随批呈裁。",
         ha="center", fontsize=8, color="#666666", linespacing=1.8)

out = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P4-08-LOO-AUC-DUAL-ARM.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
assert os.path.exists(out) and os.path.getsize(out) > 10 * 1024, "输出缺失或 ≤10KB"
print("[ok] FIG-P4-08 生成：%s（%d B）双口径 n+AUC 锚+四面板重算一致+冻结链三件 sha 断言全过" % (out, os.path.getsize(out)))
