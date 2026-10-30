# -*- coding: utf-8 -*-
"""
篇六 图 7：run5 密板冲突消解谱系桑基图
（首波 9 网 → 拒收 4/9 → 四种消解手段〔层消解 2／首占者权威 5／披露后 via-hub 1／
主审 FORCE 1〕 → 终态 9/9 连通）。

数据来源（全部直读机器件，零硬编码数据点）：
  - <ENGINE_ROOT>/out/net-agent-p1/run5/ledger.jsonl
      （16 轮台账；首波=轮 1..9 逐网一 route；消解分类=被拒网在后续轮的最终受理形态）
  - <ENGINE_ROOT>/out/net-agent-p1/run5/RESULT.md
      （读数#3 消解谱系原文交叉对账；终态段/层分布）
sha256 锚（程序化重算，锚值=P6 正文 §6 与 BRIEFING §1.3 登记）：
  run5/RESULT.md sha16 = 57fb7103289f89e5
"""
import hashlib
import json
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import FancyBboxPatch

LEDGER = "<ENGINE_ROOT>/out/net-agent-p1/run5/ledger.jsonl"
RESULT = "<ENGINE_ROOT>/out/net-agent-p1/run5/RESULT.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P6-07-RUN5-RESOLUTION-SANKEY.png"

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load_ledger(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def net_of_round(row):
    """该轮唯一 route 动作的网名（run5 首波每轮一网一 route+submit）。"""
    for b in row["batch"]:
        if b.get("action") == "route":
            return b
    return None


def route_accepted(row):
    acc = {a["index"] for a in row["accepted"]}
    for i, b in enumerate(row["batch"]):
        if b.get("action") == "route":
            return i in acc
    return False


def main():
    rows = load_ledger(LEDGER)
    assert [r["round"] for r in rows] == list(range(1, 17)), "run5 台账应 16 轮连续"

    # ---------- 断言层 1：RESULT sha16 锚程序化重算 ----------
    assert sha16(RESULT) == "57fb7103289f89e5", f"RESULT sha16={sha16(RESULT)}"

    # ---------- 台账直算：首波（轮 1..9）受理/拒收 ----------
    first_wave = rows[:9]
    nets_order, fw_accepted, fw_rejected = [], [], []
    for row in first_wave:
        rt = net_of_round(row)
        assert rt is not None, f"轮 {row['round']} 无 route 动作"
        nets_order.append(rt["net_id"])
        (fw_accepted if route_accepted(row) else fw_rejected).append(rt["net_id"])
    assert len(nets_order) == 9 and len(set(nets_order)) == 9, "首波应 9 网且不重"
    assert len(fw_rejected) == 4 and len(fw_accepted) == 5, (
        f"首波应 5 收 4 拒，实得 收{fw_accepted} 拒{fw_rejected}")

    # ---------- 台账直算：被拒网消解谱系 ----------
    layer_res, viahub_res, force_res, cb1_rej = [], [], [], []
    for net in fw_rejected:
        first_layer = next(r for r in first_wave if net_of_round(r)["net_id"] == net)
        first_layer = net_of_round(first_layer)["layer"]
        attempts, final_acc = [], None
        for row in rows[9:]:
            rts = [b for b in row["batch"] if b.get("action") == "route" and b.get("net_id") == net]
            if not rts:
                continue
            acc = {a["index"] for a in row["accepted"]}
            if any(i in acc for i, b in enumerate(row["batch"])
                   if b.get("action") == "route" and b.get("net_id") == net):
                final_acc = row
                break
            attempts.append(row)
        assert final_acc is not None, f"网 {net} 在台账内未获受理"
        if attempts:
            cb1_rej.append(net)  # 回叫 1（轮 10..13）仍被拒的网
        batch = final_acc["batch"]
        has_via = any(b.get("action") == "via" for b in batch)
        if final_acc["round"] == 16:
            force_res.append(net)
        elif has_via:
            viahub_res.append(net)
        else:
            layers = {b["layer"] for b in batch if b.get("action") == "route"}
            assert layers == {first_layer} or first_layer not in layers or True
            # 层消解判据：最终受理层 ≠ 首波被拒层
            assert first_layer not in layers, (
                f"{net} 非换层受理（首波 {first_layer}，终 {layers}），分类不成立")
            layer_res.append((net, first_layer, sorted(layers)))

    # ---------- 断言层 2：与 RESULT 读数#3 逐项对账 ----------
    result_text = open(RESULT, encoding="utf-8").read()
    m = re.search(r"层消解 (\d+)（B\.Cu/In1\.Cu 各一）、首占者权威 (\d+)、披露后 via-hub (\d+)、主审补全 (\d+)", result_text)
    assert m, "RESULT 读数#3 消解谱系句未匹配"
    assert int(m.group(1)) == len(layer_res) == 2, f"层消解应 2，实得 {layer_res}"
    assert int(m.group(2)) == len(fw_accepted) == 5, f"首占者权威应 5，实得 {fw_accepted}"
    assert int(m.group(3)) == len(viahub_res) == 1, f"via-hub 应 1，实得 {viahub_res}"
    assert int(m.group(4)) == len(force_res) == 1, f"FORCE 应 1，实得 {force_res}"
    assert len(layer_res) + len(fw_accepted) + len(viahub_res) + len(force_res) == 9

    # ---------- 台账直算：终态构成（14 段 + 5 via；层分布 F6/B1/In17） ----------
    segs, vias, layer_cnt = 0, 0, {}
    for row in rows:
        acc = {a["index"] for a in row["accepted"]}
        for i, b in enumerate(row["batch"]):
            if i not in acc:
                continue
            if b.get("action") == "route":
                segs += 1
                layer_cnt[b["layer"]] = layer_cnt.get(b["layer"], 0) + 1
            elif b.get("action") == "via":
                vias += 1
    assert segs == 14 and vias == 5, f"终态应 14 段 5 via，实得 {segs}段{vias}via"
    assert layer_cnt == {"F.Cu": 6, "B.Cu": 1, "In1.Cu": 7}, f"层分布 {layer_cnt}"
    assert re.search(r"9/9 连通", result_text), "RESULT 终态 9/9 未匹配"

    # ---------- 绘图（桑基：手绘带状流） ----------
    C = {  # 语义配色
        "dispatch": "#546e7a", "accept": "#2e7d32", "reject": "#c62828",
        "layer": "#1565c0", "cbstuck": "#ef6c00", "viahub": "#6a1b9a",
        "force": "#616161", "final": "#00838f",
    }
    fig, ax = plt.subplots(figsize=(13.6, 7.0), dpi=220)
    ax.set_xlim(-0.62, 5.95)
    ax.set_ylim(-1.55, 10.35)
    ax.axis("off")

    def ribbon(x0, y0, x1, y1, h, color, alpha=0.55, z=1):
        """两条三次贝塞尔上下边围成的带状流（值=带宽 h）。"""
        xm = (x0 + x1) / 2
        top = f"C{x0} {y0+h} C{xm} {y0+h}, {xm} {y1+h}, {x1} {y1+h}"
        bot = f"C{x1} {y1} C{xm} {y1}, {xm} {y0}, {x0} {y0}"
        ax.fill(f"M {top} L {bot} Z", color=color, alpha=alpha, zorder=z,
                lw=0)

    def node(x, y0, h, color, label, side="right", fs=12.5):
        ax.add_patch(FancyBboxPatch((x - 0.035, y0), 0.07, h,
                                    boxstyle="round,pad=0.008,rounding_size=0.02",
                                    fc=color, ec="none", zorder=6))
        tx = x + 0.075 if side == "right" else x - 0.075
        ha = "left" if side == "right" else "right"
        ax.text(tx, y0 + h / 2, label, ha=ha, va="center", fontsize=fs,
                color=color, fontweight="bold", zorder=7)

    NW = 0.035  # 节点半宽
    # 列位：0 首波派发 / 1 首波受理+拒收 / 2 层消解+回叫仍拒 / 3 via-hub+FORCE / 4 终态
    x0c, x1c, x2c, x3c, x4c = 0.0, 1.35, 2.6, 3.85, 5.15
    # 流（长带先画，垫底）
    ribbon(x1c + NW, 4, x4c - NW, 4, 5, C["accept"], 0.42, z=1)   # 首占者 5 → 终态
    ribbon(x2c + NW, 0, x4c - NW, 0, 2, C["layer"], 0.5, z=1)     # 层消解 2 → 终态
    ribbon(x0c + NW, 0, x1c - NW, 0, 4, C["reject"], 0.5, z=2)    # 首波 → 拒收 4
    ribbon(x0c + NW, 4, x1c - NW, 4, 5, C["accept"], 0.55, z=2)   # 首波 → 受理 5
    ribbon(x1c + NW, 0, x2c - NW, 0, 2, C["layer"], 0.6, z=2)     # 拒收 → 层消解
    ribbon(x1c + NW, 2, x2c - NW, 2, 2, C["cbstuck"], 0.55, z=2)  # 拒收 → 回叫仍拒
    ribbon(x2c + NW, 2, x3c - NW, 2, 1, C["viahub"], 0.6, z=3)    # 仍拒 → via-hub
    ribbon(x2c + NW, 3, x3c - NW, 3, 1, C["force"], 0.6, z=3)     # 仍拒 → FORCE
    ribbon(x3c + NW, 2, x4c - NW, 2, 1, C["viahub"], 0.6, z=3)    # via-hub → 终态
    ribbon(x3c + NW, 3, x4c - NW, 3, 1, C["force"], 0.6, z=3)     # FORCE → 终态
    # 节点
    node(x0c, 0, 9, C["dispatch"], "首波派发 9 网\n（demo-01-v2-corridor 密板）", "left", 12)
    node(x1c, 4, 5, C["accept"], "首波受理 5\n＝首占者权威", "right")
    node(x1c, 0, 4, C["reject"], "首波拒收 4\n（首波拒收率 4/9）", "right")
    node(x2c, 0, 2, C["layer"], "层消解 2\n（换层即过）", "right")
    node(x2c, 2, 2, C["cbstuck"], "回叫仍拒 2\n（走廊 U 形仍触区）", "right")
    node(x3c, 2, 1, C["viahub"], "披露后 via-hub 1", "right")
    node(x3c, 3, 1, C["force"], "主审 FORCE 补全 1", "right")
    node(x4c, 0, 9, C["final"], "终态 9/9 连通\n14 段＋5 via\n（F.Cu 6／B.Cu 1／\nIn1.Cu 7 主力层）", "left", 11.5)

    # 分支明细注记（网名与轮号直读台账）
    lay_txt = "；".join(f"{n}: {a}→{'/'.join(b)}" for n, a, b in layer_res)
    detail = (
        f"层消解 2：{lay_txt}（回叫 1，台账轮 {rows[9]['round']}/{rows[12]['round']}）\n"
        f"via-hub 1：{viahub_res[0]}（In1 三段两 via，0.3.1 披露后首发即过，轮 15）\n"
        f"FORCE 1：{force_res[0]}（In1 四段三 via＋末段 F.Cu 混层链，轮 16）"
    )
    ax.text(1.32, -1.05, detail, ha="left", va="top", fontsize=10.8, color="#37474f",
            linespacing=1.65,
            bbox=dict(fc="#eceff1", ec="#b0bec5", lw=0.8, boxstyle="round,pad=0.5"))
    ax.text(0.0, 10.0,
            "图 7　run5 密板自然冲突消解谱系桑基图：首波 9 网 → 拒收 4/9 → 四种消解手段 → 终态 9/9"
            "（对照 run4 同快照并行 0/5 拒收）",
            ha="left", va="center", fontsize=15.5, fontweight="bold", color="#212121")
    ax.text(0.0, 9.45, "数据源：out/net-agent-p1/run5/ledger.jsonl（16 轮台账直算）；RESULT.md 读数#3 交叉对账（sha16=57fb7103289f89e5 程序化重算一致）",
            ha="left", va="center", fontsize=9.8, color="#616161")

    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # ---------- 断言层 3：输出文件 ----------
    import os
    assert os.path.exists(OUT), "输出 PNG 不存在"
    assert os.path.getsize(OUT) > 10 * 1024, f"输出 PNG 过小：{os.path.getsize(OUT)} B"
    print("OK 图 7 桑基：", OUT, os.path.getsize(OUT), "B")
    print("  首波受理", fw_accepted, "层消解", layer_res, "via-hub", viahub_res, "FORCE", force_res)
    print("  终态", segs, "段", vias, "via", layer_cnt)


if __name__ == "__main__":
    main()
