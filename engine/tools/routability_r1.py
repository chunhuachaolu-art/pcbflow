# -*- coding: utf-8 -*-
"""A3-ROUTABILITY-R1 W3：双口径双臂 LOO-CV 训练评估（可复现入口）。

特征表＝PREREG-ROUTABILITY-R1.md §2 冻结区块（sha256 见 FREEZE-RECORD.json，
冻结时刻 2026-09-30T21:39:08+08:00），逐特征按冻结计算式实现，不得改。
分析计划＝PREREG §3（超参一次性定死）：
  臂1 LR   = Pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
  臂2 GBDT = GradientBoostingClassifier(n_estimators=100, max_depth=2, random_state=20260930)
  LOO-CV 逐板留出；AUC/准确率(阈值0.5) + 板级 bootstrap B=2000 seed=20260930。
读数措辞冻结为「v0 可行性与特征排序」，不设达标门：AUC<0.5 照报。
数据来源仅 out/v5-p5/boards/<板名>/board.json（convert 产物）；
绝不读 execute.json / run-result.json / compiled.json。
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/ZCodeData/ZCodeProject/route-v5")
sys.path.insert(0, str(ROOT))
import v5.board  # noqa: E402  schema+跨字段+provenance 哈希链校验（等价校验载入）

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import GradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

BOARDS_DIR = ROOT / "out" / "v5-p5" / "boards"
OUT_DIR = ROOT / "out" / "routability-r1"
LABELS_PATH = OUT_DIR / "labels.json"
FREEZE_PATH = OUT_DIR / "FREEZE-RECORD.json"

# ---- 冻结常量（PREREG §2/§3）----
PITCH = 0.25                      # 口径 C1 格点 pitch（mm，冻结）
EDGE_BAND_MM = 2.0                # F24 边带宽（mm，冻结）
FEATURES = ["F%02d" % i for i in range(1, 29)]
LOG1P_FEATURES = {"F01", "F02", "F05", "F06", "F07", "F08", "F16", "F17", "F28"}  # 变换列（冻结）
SEED = 20260930                   # GBDT random_state 与 bootstrap RNG seed（冻结）
B_BOOT = 2000                     # bootstrap 副本数（冻结）
ACC_THRESHOLD = 0.5               # 准确率阈值（冻结；ŷ=1 ⇔ p̂≥0.5）

# ---- W4 进场预测卡约定 ----
CARD_COMB_POS = 0.70              # 综合读数（两臂概率均值）分档：≥0.70 推高
CARD_COMB_NEG = 0.30              # <0.30 推低；其间为中间带（W4 卡片报告约定，非模型口径）
FEATURE_NAMES_CN = {              # 冻结特征表中文名（PREREG §2），卡片可读性用
    "F01": "net_count 网数", "F02": "netted_pad_count 有网焊盘总数",
    "F03": "pads_per_net 网均焊盘数", "F04": "multi_term_net_frac 多终端网占比",
    "F05": "via_count_existing 既有过孔数", "F06": "seg_arc_count 既有走线段+圆弧数",
    "F07": "holes_total_count 板固孔总数", "F08": "board_area_mm2 板工作区面积",
    "F09": "aspect_ratio 板长宽比", "F10": "signal_layer_count 可用信号层数",
    "F11": "nets_per_layer 层均网数", "F12": "pad_area_frac 焊盘铜面积占板比",
    "F13": "thru_pad_frac 通孔盘占比", "F14": "steiner_per_layer 层均 Steiner 总长",
    "F15": "steiner_per_area 单位面积 Steiner 长", "F16": "steiner_max_net_mm 最长单网 Steiner 长",
    "F17": "steiner_mean_net_mm 网均 Steiner 长", "F18": "pwr_partition_frac PWR 型分区占比",
    "F19": "via_annular_mm_fill0 过孔环宽（缺省填 0）", "F20": "via_model_missing via_model 缺省指示",
    "F21": "grid_occ_fcu F.Cu 格点占用率", "F22": "grid_occ_worst_layer 最坏层格点占用率",
    "F23": "pad_edge_dist_mean 焊盘中心均板边距", "F24": "pad_frac_edge2mm 2mm 边带内焊盘占比",
    "F25": "obstacle_density 单位面积障碍数", "F26": "nn_dist_min 最近邻焊盘间距·最小值",
    "F27": "nn_dist_mean 最近邻焊盘间距·均值", "F28": "convert_anomaly_count convert 退化/失败信号计数",
}


# ----------------------------------------------------------------------------
# 1. 特征提取（冻结特征表逐特征实现）
# ----------------------------------------------------------------------------

def _pad_half_extents(pt):
    """pad_terminals 一条的半宽/半高（外接方形口径，表注 2）。

    circle: size_mm=[d] → d/2 × d/2；rect: size_mm=[w,h] → w/2 × h/2。
    """
    if pt["shape"] == "circle":
        d = float(pt["size_mm"][0])
        return d / 2.0, d / 2.0
    if pt["shape"] == "rect":
        w, h = float(pt["size_mm"][0]), float(pt["size_mm"][1])
        return w / 2.0, h / 2.0
    raise ValueError("未知 pad 形状 %r（特征表仅定义 circle/rect 分支）" % pt["shape"])


def _mark_square(occ, x0, y0, px, py, rx, ry):
    """切比雪夫方形占用：格点 (x0+i*PITCH, y0+j*PITCH) 满足 |gx-px|≤rx 且 |gy-py|≤ry。

    索引窗口先按解析式放宽 ±1 格，再对窗口内格点做精确 ≤ 判定（规避浮点边界舍入）。
    """
    ny, nx = occ.shape
    i_lo = max(0, math.ceil((px - rx - x0) / PITCH) - 1)
    i_hi = min(nx - 1, math.floor((px + rx - x0) / PITCH) + 1)
    j_lo = max(0, math.ceil((py - ry - y0) / PITCH) - 1)
    j_hi = min(ny - 1, math.floor((py + ry - y0) / PITCH) + 1)
    if i_lo > i_hi or j_lo > j_hi:
        return
    ii = np.arange(i_lo, i_hi + 1)
    jj = np.arange(j_lo, j_hi + 1)
    gx = x0 + ii * PITCH
    gy = y0 + jj * PITCH
    mask = (np.abs(gx[None, :] - px) <= rx) & (np.abs(gy[:, None] - py) <= ry)
    occ[j_lo:j_hi + 1, i_lo:i_hi + 1] |= mask


def _mark_circle(occ, x0, y0, px, py, r):
    """圆占用：‖g−pos‖₂ ≤ r（板固孔，含 oval 孔按 drill_mm/2 圆口径，表注 1）。"""
    ny, nx = occ.shape
    i_lo = max(0, math.ceil((px - r - x0) / PITCH) - 1)
    i_hi = min(nx - 1, math.floor((px + r - x0) / PITCH) + 1)
    j_lo = max(0, math.ceil((py - r - y0) / PITCH) - 1)
    j_hi = min(ny - 1, math.floor((py + r - y0) / PITCH) + 1)
    if i_lo > i_hi or j_lo > j_hi:
        return
    ii = np.arange(i_lo, i_hi + 1)
    jj = np.arange(j_lo, j_hi + 1)
    gx = x0 + ii * PITCH
    gy = y0 + jj * PITCH
    mask = (gx[None, :] - px) ** 2 + (gy[:, None] - py) ** 2 <= r * r
    occ[j_lo:j_hi + 1, i_lo:i_hi + 1] |= mask


def grid_occupancy_per_layer(board, clear_c):
    """口径 C1：各可用信号层格点占用率（表注 1，冻结）。

    格点集 x_i=x_min+i*0.25（i=0..⌊W/0.25⌋）、y_j 同理，含边界点。
    障碍＝pad_terminals（外接方形外扩 c）+ holes（圆，半径 drill/2+c）；
    既有铜不进障碍集（冻结近似边界）。
    """
    ws = board["workspace"]
    W = ws["x_max"] - ws["x_min"]
    H = ws["y_max"] - ws["y_min"]
    nx = int(math.floor(W / PITCH)) + 1
    ny = int(math.floor(H / PITCH)) + 1
    sig_layers = [L["id"] for L in board["stackup"]
                  if L["kind"] == "signal" and L.get("available") is True]
    out = {}
    for lid in sig_layers:
        occ = np.zeros((ny, nx), dtype=bool)
        for part in board["partitions"]:
            geo = part["geometry"]
            eps = geo["endpoints"]
            for pt in geo["pad_terminals"]:
                layers = pt["layers"]
                on_layer = (layers == "all") or (isinstance(layers, list) and lid in layers)
                if not on_layer:
                    continue
                px, py = eps[pt["endpoint"]]
                hw, hh = _pad_half_extents(pt)
                _mark_square(occ, ws["x_min"], ws["y_min"],
                             float(px), float(py), hw + clear_c, hh + clear_c)
        for h in board["holes"]:
            px, py = h["pos_mm"]
            r = float(h["drill_mm"]) / 2.0 + clear_c
            _mark_circle(occ, ws["x_min"], ws["y_min"], float(px), float(py), r)
        out[lid] = float(occ.sum()) / float(nx * ny)
    return out


def extract_features(board_name):
    """单板 28 特征（全部 convert 后静态量）。返回 dict[str, float]。"""
    path = BOARDS_DIR / board_name / "board.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    ar = d["adapter_report"]
    b = v5.board.load_board(d["board"])  # 外壳 {adapter_report, board, provenance}，校验内层 board（PREREG §1）

    ws = b["workspace"]
    W = float(ws["x_max"]) - float(ws["x_min"])
    H = float(ws["y_max"]) - float(ws["y_min"])
    area = W * H

    f = {}
    f["F01"] = float(ar["net_count"])
    f["F02"] = float(ar["netted_pad_count"])
    f["F03"] = f["F02"] / f["F01"]
    f["F04"] = float(ar["topology"]["multi_terminal_nets"]) / f["F01"]
    f["F05"] = float(ar["via_count"])
    f["F06"] = float(ar["segment_count"]) + float(ar["arc_count"])
    f["F07"] = float(len(b["holes"]))
    f["F08"] = area
    f["F09"] = W / H
    f["F10"] = float(sum(1 for L in b["stackup"]
                         if L["kind"] == "signal" and L.get("available") is True))
    f["F11"] = f["F01"] / f["F10"]

    pad_area = 0.0
    n_thru = 0
    n_pt = 0
    edge_dists = []
    for part in b["partitions"]:
        geo = part["geometry"]
        eps = geo["endpoints"]
        for pt in geo["pad_terminals"]:
            n_pt += 1
            if pt["shape"] == "circle":
                pad_area += float(pt["size_mm"][0]) ** 2
            elif pt["shape"] == "rect":
                pad_area += float(pt["size_mm"][0]) * float(pt["size_mm"][1])
            else:
                raise ValueError("未知 pad 形状 %r" % pt["shape"])
            if pt["layers"] == "all":
                n_thru += 1
            x, y = eps[pt["endpoint"]]
            x, y = float(x), float(y)
            edge_dists.append(min(x - ws["x_min"], ws["x_max"] - x,
                                  y - ws["y_min"], ws["y_max"] - y))
    f["F12"] = pad_area / area
    f["F13"] = float(n_thru) / f["F02"]

    totals = [float(t["total_mm"]) for t in b["topology"].values()]
    f["F14"] = sum(totals) / f["F10"]
    f["F15"] = sum(totals) / area
    f["F16"] = max(totals)
    f["F17"] = sum(totals) / len(totals)

    f["F18"] = float(sum(1 for p in b["partitions"] if p["ptype"] == "PWR")) / float(len(b["partitions"]))

    vm = b.get("via_model")
    if isinstance(vm, dict):
        f["F19"] = float(vm["annular_mm"])
        f["F20"] = 0.0
    else:
        f["F19"] = 0.0
        f["F20"] = 1.0

    clear_c = float(b["hard_rules"]["R5"]["min_clearance_mm"])
    occ = grid_occupancy_per_layer(b, clear_c)
    f["F21"] = occ["F.Cu"]
    f["F22"] = max(occ.values())

    f["F23"] = float(np.mean(edge_dists))
    f["F24"] = float(sum(1 for e in edge_dists if e <= EDGE_BAND_MM)) / float(n_pt)

    f["F25"] = (f["F05"] + f["F06"] + f["F07"]) / area

    pts = np.array([list(map(float, ep)) for part in b["partitions"]
                    for ep in part["geometry"]["endpoints"]], dtype=float)
    if len(pts) >= 2:
        diff = pts[:, None, :] - pts[None, :, :]
        d2 = (diff * diff).sum(axis=-1)
        np.fill_diagonal(d2, np.inf)
        nn = np.sqrt(d2.min(axis=1))  # 每点最近邻距离（有序对 i≠j，重合坐标合法产出 0，不去重）
        f["F26"] = float(nn.min())
        f["F27"] = float(nn.mean())
    else:
        raise ValueError("端子数 <2，最近邻特征不可算：%s" % board_name)

    f["F28"] = float(ar["degenerate_partitions"]
                     + ar["topology"]["mst_fallback_nets"]
                     + ar["pad_terminal_skipped"])

    for k, v in f.items():
        if not math.isfinite(v):
            raise ValueError("特征 %s 非有限值（NaN/Inf）：%s = %r（fail-closed，停止呈报）"
                             % (k, board_name, v))
    return f


# ----------------------------------------------------------------------------
# 2/3. 标签合并 + 训练评估
# ----------------------------------------------------------------------------

def make_lr():
    return Pipeline([("scaler", StandardScaler()),
                     ("lr", LogisticRegression(max_iter=1000))])


def make_gbdt():
    return GradientBoostingClassifier(n_estimators=100, max_depth=2, random_state=SEED)


def zero_var_keep(X):
    """折内零方差删除（表注 5：严格等值判定，无其它特征选择）。"""
    return [j for j in range(X.shape[1]) if not np.all(X[:, j] == X[0, j])]


def apply_transform(df_feats):
    X = df_feats[FEATURES].to_numpy(dtype=float).copy()  # .copy(): pandas 3.0 视图只读
    for j, name in enumerate(FEATURES):
        if name in LOG1P_FEATURES:
            X[:, j] = np.log1p(X[:, j])
    return X


def boot_ci(y, p):
    """板级 bootstrap 95% CI（对 LOO 预测重采样，不重训；PREREG §3.3）。

    每副本有放回抽 n 板；单类副本无法算 AUC → 剔除并计数（准确率照算）。
    每个 (口径, 臂) 用独立 default_rng(SEED)，保证复跑同读数。
    """
    rng = np.random.default_rng(SEED)
    yb = np.asarray(y, dtype=int)
    aucs, accs, dropped = [], [], 0
    for _ in range(B_BOOT):
        idx = rng.integers(0, len(yb), len(yb))
        ys, ps = yb[idx], p[idx]
        accs.append(float(np.mean((ps >= ACC_THRESHOLD) == (ys == 1))))
        if ys.min() == ys.max():
            dropped += 1
            continue
        aucs.append(float(roc_auc_score(ys, ps)))
    auc_ci = np.percentile(aucs, [2.5, 97.5]).tolist() if aucs else [float("nan")] * 2
    acc_ci = np.percentile(accs, [2.5, 97.5]).tolist()
    return auc_ci, acc_ci, dropped


def full_sample_importance(X, y):
    """全样本拟合两臂：LR 标准化系数（Scaler 之后那级的 coef_）与 GBDT feature_importances_。"""
    keep = zero_var_keep(X)
    names = [FEATURES[j] for j in keep]
    lr = make_lr().fit(X[:, keep], y)
    gb = make_gbdt().fit(X[:, keep], y)
    lr_df = pd.DataFrame({"feature": names, "value": lr.named_steps["lr"].coef_[0]})
    lr_df["abs_value"] = lr_df["value"].abs()
    lr_df = lr_df.sort_values(["abs_value", "feature"], ascending=[False, True]).reset_index(drop=True)
    gb_df = pd.DataFrame({"feature": names, "value": gb.feature_importances_})
    gb_df["abs_value"] = gb_df["value"].abs()
    gb_df = gb_df.sort_values(["abs_value", "feature"], ascending=[False, True]).reset_index(drop=True)
    return lr_df, gb_df, [FEATURES[j] for j in range(X.shape[1]) if j not in set(keep)]


def run_caliber(caliber, boards, y_map, df_feats):
    rows = df_feats[df_feats["board"].isin(boards)].reset_index(drop=True)
    y = np.array([int(y_map[b]) for b in rows["board"]], dtype=int)
    X = apply_transform(rows)
    p_lr, p_gb, fold_drops = loo_cv_named(X, y, list(rows["board"]))
    out = {
        "n": int(len(y)),
        "n_pos": int((y == 1).sum()),
        "n_neg": int((y == 0).sum()),
        "boards": list(rows["board"]),
    }
    importance_rows = []
    for arm, p in (("lr", p_lr), ("gbdt", p_gb)):
        auc = float(roc_auc_score(y, p))
        acc = float(np.mean((p >= ACC_THRESHOLD) == (y == 1)))
        auc_ci, acc_ci, dropped = boot_ci(y, p)
        out[arm] = {
            "auc": auc,
            "acc": acc,
            "auc_ci95": auc_ci,
            "acc_ci95": acc_ci,
            "auc_bootstrap_single_class_dropped": dropped,
        }
    out["loo_predictions"] = [
        {"board": b, "y_true": int(yi), "p_lr": float(pl), "p_gbdt": float(pg)}
        for b, yi, pl, pg in zip(rows["board"], y, p_lr, p_gb)
    ]
    lr_df, gb_df, full_drop = full_sample_importance(X, y)
    out["feature_importance_rank"] = {
        "lr": [{"feature": r.feature, "coef": float(r.value)} for r in lr_df.head(5).itertuples()],
        "gbdt": [{"feature": r.feature, "importance": float(r.value)} for r in gb_df.head(5).itertuples()],
    }
    out["zero_variance_dropped"] = {
        "full_sample_fit": full_drop,
        "loo_folds_with_drops": fold_drops,
    }
    for model_name, df_i in (("lr", lr_df), ("gbdt", gb_df)):
        for rank, r in enumerate(df_i.itertuples(), start=1):
            importance_rows.append({
                "caliber": caliber, "model": model_name, "rank": rank,
                "feature": r.feature, "value": float(r.value), "abs_value": float(r.abs_value),
            })
    return out, importance_rows


def loo_cv_named(X, y, board_names):
    """LOO-CV（板名标注零方差删除清单）。"""
    n = len(y)
    p_lr = np.zeros(n)
    p_gb = np.zeros(n)
    fold_drops = {}
    for i in range(n):
        tr = [k for k in range(n) if k != i]
        Xtr, ytr = X[tr], y[tr]
        keep = zero_var_keep(Xtr)
        drop = [FEATURES[j] for j in range(X.shape[1]) if j not in set(keep)]
        if drop:
            fold_drops[board_names[i]] = drop
        lr = make_lr().fit(Xtr[:, keep], ytr)
        gb = make_gbdt().fit(Xtr[:, keep], ytr)
        p_lr[i] = lr.predict_proba(X[i, keep].reshape(1, -1))[0, 1]
        p_gb[i] = gb.predict_proba(X[i, keep].reshape(1, -1))[0, 1]
    return p_lr, p_gb, fold_drops


# ----------------------------------------------------------------------------
# W4：进场预测卡（--card <板名>）
# ----------------------------------------------------------------------------

def build_card_markdown(board_name):
    """生成一页进场预测卡（markdown 文本）。

    语义＝新板 convert 完成时刻的读数：主口径训练集拟合双臂后对该板出概率。
    若该板本身在主口径训练集内 → 训练折剔除该板（留出口径，与 W3 LOO 同构，防自评虚高）。
    贡献口径＝LR 臂标准化系数 × 该板标准化特征值（同一训练折的 StandardScaler）。
    """
    if not (BOARDS_DIR / board_name / "board.json").exists():
        raise SystemExit("[card] 板 %s 无 board.json（convert 未完成或失败），无特征可算" % board_name)
    labels_list = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    y_main_map = {r["board"]: r["y_main"] for r in labels_list}
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    sha16 = freeze["feature_table_sha256"][:16]

    all_names = sorted(p.name for p in BOARDS_DIR.iterdir()
                       if p.is_dir() and (BOARDS_DIR / p.name / "board.json").exists())
    feats = {n: extract_features(n) for n in all_names}
    if board_name not in feats:
        raise SystemExit("[card] 板 %s 特征提取失败（不在特征可达集内）" % board_name)

    train_boards = [n for n in all_names if y_main_map.get(n) is not None and n != board_name]
    in_sample = y_main_map.get(board_name) is not None
    y = np.array([int(y_main_map[b]) for b in train_boards], dtype=int)
    X = apply_transform(pd.DataFrame([feats[b] for b in train_boards]))
    x_t = apply_transform(pd.DataFrame([feats[board_name]]))[0]
    keep = zero_var_keep(X)
    lr = make_lr().fit(X[:, keep], y)
    gb = make_gbdt().fit(X[:, keep], y)
    p_lr = float(lr.predict_proba(x_t[keep].reshape(1, -1))[0, 1])
    p_gb = float(gb.predict_proba(x_t[keep].reshape(1, -1))[0, 1])
    comb = (p_lr + p_gb) / 2.0
    if comb >= CARD_COMB_POS:
        comb_txt = "推高（倾向可布）"
    elif comb < CARD_COMB_NEG:
        comb_txt = "推低（倾向不可布）"
    else:
        comb_txt = "中间带（悬而不决，按普通板推进，不据本卡改道）"

    scaler = lr.named_steps["scaler"]
    lr_model = lr.named_steps["lr"]
    z = (x_t[keep] - scaler.mean_) / scaler.scale_
    coef = lr_model.coef_[0]
    contrib = coef * z
    kept_names = [FEATURES[j] for j in keep]
    order = sorted(range(len(kept_names)), key=lambda j: -abs(contrib[j]))
    top3 = [(kept_names[j], float(contrib[j]), float(z[j]), float(coef[j]),
             float(x_t[keep][j])) for j in order[:3]]

    gen_at = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = []
    lines.append("# 进场预测卡 —— %s" % board_name)
    lines.append("")
    lines.append("- 生成时刻：%s（本地时区）" % gen_at)
    lines.append("- 工具：`route-v5/tools/routability_r1.py --card %s`（A3-ROUTABILITY-R1 W4）" % board_name)
    lines.append("- 特征表冻结：sha256 前 16 位 `%s`（FREEZE-RECORD.json，2026-09-30T21:39:08+08:00 冻结）" % sha16)
    lines.append("")
    lines.append("## 1. 预测值（主口径 y_main：可布=1 vs 固有不可布(a)=0）")
    lines.append("")
    lines.append("| 臂 | 模型 | P(可布) |")
    lines.append("|---|---|---|")
    lines.append("| LR | Pipeline(StandardScaler, LogisticRegression(max_iter=1000)) | %.4f |" % p_lr)
    lines.append("| GBDT | GradientBoostingClassifier(n_estimators=100, max_depth=2) | %.4f |" % p_gb)
    lines.append("| **综合** | 两臂概率均值 | **%.4f → %s** |" % (comb, comb_txt))
    lines.append("")
    if in_sample:
        lines.append("读数口径：**该板在主口径训练集内（y_main=%d）**——训练折已剔除本板，"
                     "即留一（LOO）口径，与 W3 metrics.json 的 loo_predictions 同构；"
                     "此行仅为演示卡披露，真实新板进场卡无标签行。"
                     % int(y_main_map[board_name]))
    else:
        lines.append("读数口径：**新板读数**——该板不在主口径训练集内，训练折=主口径全部 %d 板。"
                     % len(train_boards))
    lines.append("")
    lines.append("## 2. Top-3 特征贡献（LR 臂：标准化系数 × 本板标准化值）")
    lines.append("")
    lines.append("| # | 特征 | 方向 | 贡献 | 本板标准化值 | LR 标准化系数 | 本板入模值（变换后） |")
    lines.append("|---|------|------|------|------|------|------|")
    for i, (name, c, zv, cv, xv) in enumerate(top3, start=1):
        direction = "推高可布性" if c > 0 else "推低可布性"
        lines.append("| %d | %s（%s） | %s | %+.4f | %+.4f | %+.4f | %.6g |"
                     % (i, name, FEATURE_NAMES_CN[name], direction, c, zv, cv, xv))
    lines.append("")
    lines.append("贡献=该特征把 LR 线性预测（logit）推向可布（+）/推离可布（−）的量；"
                 "仅 LR 臂可分解，GBDT 臂无对应分解，故贡献表只列 LR。")
    lines.append("")
    lines.append("## 3. 置信度说明")
    lines.append("")
    lines.append("> 本卡为 A3-ROUTABILITY-R1 **v0** 读数，定位冻结为「v0 可行性与特征排序」，"
                 "不是生产预测器，不得外推为「预测器可用」（任务书 §6 红线 5）。"
                 "训练样本为主口径小样本（n=13：4 可布 + 9 固有不可布），"
                 "双臂 LOO-CV 读数与 bootstrap 95% CI 见 `out/routability-r1/metrics.json`；"
                 "小样本下单一板概率不确定度大，本卡不构成 execute/弃板决策依据，"
                 "仅作进场时刻的特征画像与排序参考（任务书 §3 W4）。")
    lines.append("")
    lines.append("---")
    lines.append("脚注：特征定义=PREREG 冻结特征表 v1.0（28 条，convert 后静态量）；"
                 "入模变换 log1p 列与折内零方差删除同 W3 冻结口径；"
                 "综合读数分档（≥%.2f 推高 / <%.2f 推低 / 其间中间带）为 W4 卡片报告约定。" % (CARD_COMB_POS, CARD_COMB_NEG))
    lines.append("")
    return "\n".join(lines), {"p_lr": p_lr, "p_gbdt": p_gb, "comb": comb, "in_sample": in_sample}


# ----------------------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser(description="A3-ROUTABILITY-R1：双臂可布性读数（W3 训练评估 / W4 进场预测卡）")
    ap.add_argument("--card", metavar="板名", help="输出该板一页进场预测卡（markdown 到 stdout）")
    ap.add_argument("--out", metavar="路径", help="与 --card 连用：卡写入该文件（utf-8）而非仅打印")
    args = ap.parse_args()

    if args.card:
        text, info = build_card_markdown(args.card)
        if args.out:
            path = Path(args.out)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print("[card] %s：p_lr=%.4f p_gbdt=%.4f 综合=%.4f（%s）→ 写入 %s"
                  % (args.card, info["p_lr"], info["p_gbdt"], info["comb"],
                     "样本内 LOO 口径" if info["in_sample"] else "新板口径", path))
        else:
            print(text)
        return
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    prereg_sha = freeze["feature_table_sha256"]  # 程序性读取，禁手抄

    labels_list = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    y_main_map = {r["board"]: r["y_main"] for r in labels_list}
    y_sens_map = {r["board"]: r["y_sens"] for r in labels_list}

    # 特征提取 + 防御性排除（表注 6，fail-closed）
    records, exclusions = [], []
    all_dirs = sorted(p.name for p in BOARDS_DIR.iterdir() if p.is_dir())
    for name in all_dirs:
        if not (BOARDS_DIR / name / "board.json").exists():
            exclusions.append({"board": name, "reason": "board.json 缺失（特征不可得，特征可得性排除）"})
            continue
        try:
            feats = extract_features(name)
        except v5.board.BoardLoadError as e:
            exclusions.append({"board": name, "reason": "board 载入校验失败：%s" % e})
            continue
        d = json.loads((BOARDS_DIR / name / "board.json").read_text(encoding="utf-8"))
        ar = d["adapter_report"]
        if ar.get("net_count", 0) == 0 or ar.get("netted_pad_count", 0) == 0 \
                or "topology" not in d["board"]:
            exclusions.append({"board": name,
                               "reason": "net_count/netted_pad_count=0 或 topology 缺失（表注 6 防御性排除）"})
            continue
        rec = {"board": name}
        rec.update(feats)
        rec["y_main"] = y_main_map.get(name) if name in y_main_map else None
        rec["y_sens"] = y_sens_map.get(name) if name in y_sens_map else None
        records.append(rec)

    df = pd.DataFrame(records, columns=["board"] + FEATURES + ["y_main", "y_sens"])

    # 板并集：有特征文件且有标签（labels.json 在册）
    labeled = set(y_main_map) | set(y_sens_map)
    unlabeled_with_features = [b for b in df["board"] if b not in labeled]
    if unlabeled_with_features:
        exclusions.append({"board": ",".join(unlabeled_with_features),
                           "reason": "有 board.json 但 labels.json 无记录（不入建模集）"})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "features.csv", index=False, encoding="utf-8")

    main_boards = [r["board"] for r in records if r["y_main"] is not None]
    sens_boards = [r["board"] for r in records if r["y_sens"] is not None]
    cal_main, imp_rows_main = run_caliber("main", main_boards, y_main_map, df)
    cal_sens, imp_rows_sens = run_caliber("sensitivity", sens_boards, y_sens_map, df)

    # 顶层 loo_predictions（核验口径）：两口径×两臂板级逐板（板名/真值/预测概率）
    loo_all = [{"caliber": cname, "board": r["board"], "y_true": r["y_true"],
                "p_lr": r["p_lr"], "p_gbdt": r["p_gbdt"]}
               for cname, cal in (("main", cal_main), ("sensitivity", cal_sens))
               for r in cal["loo_predictions"]]

    metrics = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "prereg_freeze_sha256": prereg_sha,
        "conclusion_wording": "v0 可行性与特征排序",
        "n_boards_feature_matrix": int(len(df)),
        "defensive_exclusions": exclusions,
        "loo_predictions": loo_all,
        "calibers": {"main": cal_main, "sensitivity": cal_sens},
    }
    (OUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")

    imp_df = pd.DataFrame(imp_rows_main + imp_rows_sens,
                          columns=["caliber", "model", "rank", "feature", "value", "abs_value"])
    imp_df.to_csv(OUT_DIR / "feature-importance.csv", index=False, encoding="utf-8")

    # 人类可读摘要（stdout）
    print("特征矩阵 n=%d 板 × %d 特征；防御性排除 %d 条" % (len(df), len(FEATURES), len(exclusions)))
    for e in exclusions:
        print("  排除：%s —— %s" % (e["board"], e["reason"]))
    for cname, cal in (("main", cal_main), ("sensitivity", cal_sens)):
        print("[%s] n=%d (pos=%d, neg=%d)" % (cname, cal["n"], cal["n_pos"], cal["n_neg"]))
        for arm in ("lr", "gbdt"):
            m = cal[arm]
            print("  %-4s AUC=%.4f CI95=[%.4f, %.4f]（bootstrap 单类剔除 %d/%d） | acc=%.4f CI95=[%.4f, %.4f]"
                  % (arm, m["auc"], m["auc_ci95"][0], m["auc_ci95"][1],
                     m["auc_bootstrap_single_class_dropped"], B_BOOT,
                     m["acc"], m["acc_ci95"][0], m["acc_ci95"][1]))
        print("  LOO 预测：" + "; ".join(
            "%s y=%d p_lr=%.3f p_gbdt=%.3f" % (r["board"], r["y_true"], r["p_lr"], r["p_gbdt"])
            for r in cal["loo_predictions"]))
        print("  重要性前五 LR：  " + ", ".join("%s(%.3f)" % (r["feature"], r["coef"])
                                              for r in cal["feature_importance_rank"]["lr"]))
        print("  重要性前五 GBDT：" + ", ".join("%s(%.4f)" % (r["feature"], r["importance"])
                                              for r in cal["feature_importance_rank"]["gbdt"]))
    print("产物：%s | %s | %s" % (OUT_DIR / "features.csv", OUT_DIR / "metrics.json",
                                  OUT_DIR / "feature-importance.csv"))


if __name__ == "__main__":
    main()
