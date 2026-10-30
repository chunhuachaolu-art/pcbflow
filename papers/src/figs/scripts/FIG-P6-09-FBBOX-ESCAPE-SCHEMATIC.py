# -*- coding: utf-8 -*-
"""
篇六 图 9：F-bbox 逃生数据版（板件几何＋run5 台账＋验证器直读）
  左（a）：单 route 动作＝整条 polyline 顶点 min/max 外接矩形（v5/drc.py Copper.as_rect）
      判 R6 禁布区（check_keepout）——包围盒触区即拒、实际线段绕开无效
      （ETH-MAC r3 U 形绕行 / MISC1 r4 U 形绕行，均 V_KEEPOUT 拒收）。
  右（b）：唯一逃生＝多 route＋转折格点自网 via 链——各段 bbox 局部化
      （MISC1 r15 披露后首发即过＝正对照；ETH-MAC r16 主审 FORCE 同构链）。
  下（c）：量化面——单 route 整链 bbox 面积 vs via 链各段 bbox 面积/最大值；
      r3 bbox∩K1 交叠面积（mm²）入图。

标注串纪律（本版升级）：图内一切坐标区间文字（x∈[…]×y∈[…] 类）均由
verdicts/as_rect 计算值 f-string 生成，脚本内零手写坐标区间字面量；成图前
统一回 parse 核验「标注串生成值==verdicts」。段数改为 len() 生成
（旧版手写「六段/6/6」实为 r15×3＋r16×4＝7 段，系手写笔误，本版消除）。

数据来源（全部直读机器件，零硬编码数据点/坐标）：
  - boards/d/demo-01-v2-corridor.board.v1.json（K1/K2 禁布区、走廊 C1、工作区、
    P3=ETH-MAC 与 P5=MISC1 端点 mm 坐标）
  - out/net-agent-p1/run5/ledger.jsonl（r3/r4 被拒单 route；r15/r16 via 链；
    格点→mm＝pitch 0.5（canvas/state.py DEFAULT_PITCH_MM，x0=y0=0））
  - v5/drc.py（直接 import 验证器自身 check_keepout 复算 R6 判定，断言与
    台账 verdict 逐位一致——最忠实口径）
sha256 锚（运行时程序化重算，锚值=P6 正文 §6 与 BRIEFING §1.3 登记）：
  run5/RESULT.md sha16 = 57fb7103289f89e5（见 main() 内 assert）
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, "<ENGINE_ROOT>")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Patch, Rectangle

from v5.drc import Copper, check_keepout  # 验证器自身代码（非重写）

BOARD = "<ENGINE_ROOT>/boards/d/demo-01-v2-corridor.board.v1.json"
LEDGER = "<ENGINE_ROOT>/out/net-agent-p1/run5/ledger.jsonl"
RESULT = "<ENGINE_ROOT>/out/net-agent-p1/run5/RESULT.md"
OUT = "<ENGINE_ROOT>/out/paper-program-r2/figs/FIG-P6-09-FBBOX-ESCAPE-SCHEMATIC.png"

PITCH = 0.5  # canvas/state.py DEFAULT_PITCH_MM；x0=y0=0（工作区 x_min/y_min=0 直读验证）

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

CIRC = "①②③④"
REG = []  # (标注串, 对应 rect) 登记；成图前统一回 parse 核验


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def to_mm(grid_pts):
    return [(i * PITCH, j * PITCH) for i, j in grid_pts]


def rect_area(bb):
    return max(0.0, bb[2] - bb[0]) * max(0.0, bb[3] - bb[1])


def reg(s, bb):
    REG.append((s, bb))
    return s


def verify_annotations():
    """回 parse 核验：标注串内坐标区间 == verdicts/as_rect/board rect 计算值。"""
    pat = re.compile(r"x∈\[(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\][× ]y∈\["
                     r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\]")
    for s, bb in REG:
        m = pat.search(s)
        assert m, f"标注串无法回解析：{s!r}"
        got = (float(m.group(1)), float(m.group(3)), float(m.group(2)), float(m.group(4)))
        assert got == (bb[0], bb[1], bb[2], bb[3]), f"标注串≠rect：{s!r} {bb} {got}"
    return len(REG)


def seg_line(idx, bb, area, with_area=True):
    deg = " 纵柱" if bb[2] == bb[0] else (" 横线" if bb[3] == bb[1] else "")
    tail = f" A={area:g}mm²" if with_area else ""
    return reg(f"段{CIRC[idx]} x∈[{bb[0]:g},{bb[2]:g}]×y∈[{bb[1]:g},{bb[3]:g}]"
               f"{deg}{tail}", bb)


def chain_min_gap(bbs, keepouts):
    """全链各段对 K1/K2 的最小错开间隙（由 rect 直算；>0 即不触区）。"""
    best = None
    for bi, bb in enumerate(bbs):
        for zid, k in keepouts:
            gx = max(k[0] - bb[2], bb[0] - k[2])
            gy = max(k[1] - bb[3], bb[1] - k[3])
            g = max(gx, gy)
            assert g > 0, f"段{CIRC[bi]} 触 {zid}：{bb}"
            if best is None or g < best[0]:
                best = (g, bi, zid)
    return best


def main():
    board = json.load(open(BOARD, encoding="utf-8"))
    with open(LEDGER, encoding="utf-8") as f:
        rows = {json.loads(l)["round"]: json.loads(l) for l in f if l.strip()}
    result_sha = sha16(RESULT)
    assert result_sha == "57fb7103289f89e5", f"run5 RESULT sha16 锚不符：{result_sha}"

    ws = board["workspace"]
    assert ws["x_min"] == 0.0 and ws["y_min"] == 0.0, "格点原点假设（x0=y0=0）需复核"
    zones = {z["zone_id"]: z for z in board["zones"]}
    k1 = (zones["K1"]["rect"]["x_min"], zones["K1"]["rect"]["y_min"],
          zones["K1"]["rect"]["x_max"], zones["K1"]["rect"]["y_max"])
    k2 = (zones["K2"]["rect"]["x_min"], zones["K2"]["rect"]["y_min"],
          zones["K2"]["rect"]["x_max"], zones["K2"]["rect"]["y_max"])
    c1z = zones["C1"]["rect"]
    keepouts = [("K1", k1), ("K2", k2)]
    parts = {p["partition_id"]: p for p in board["partitions"]}
    eth_ep = parts["P3"]["geometry"]["endpoints"]
    misc_ep = parts["P5"]["geometry"]["endpoints"]
    # 端点 x 落禁布区 x 投影（正文口径 ETH/MISC1 锚点）
    assert k1[0] <= eth_ep[0][0] <= k1[2], "ETH 锚 x 应落 K1 x 投影"
    assert k2[0] <= misc_ep[0][0] <= k2[2], "MISC1 锚 x 应落 K2 x 投影"

    def routes_of(rnd):
        return [b for b in rows[rnd]["batch"] if b.get("action") == "route"]

    def vias_of(rnd):
        return [b for b in rows[rnd]["batch"] if b.get("action") == "via"]

    r3, r4, r15, r16 = routes_of(3), routes_of(4), routes_of(15), routes_of(16)
    assert len(r3) == len(r4) == 1, f"r3/r4 应各 1 段，实得 {len(r3)}/{len(r4)}"
    assert len(r15) == 3 and len(r16) == 4, f"r15 应 3 段 r16 应 4 段，实得 {len(r15)}/{len(r16)}"
    assert len(vias_of(15)) == 2 and len(vias_of(16)) == 3, "via 数应 2/3"

    # ---------- 断言层：验证器自身 check_keepout 复算（mm 坐标） ----------
    verdicts = {}
    for rnd, rt_list in ((3, r3), (4, r4), (15, r15), (16, r16)):
        for i, b in enumerate(rt_list):
            cu = Copper(b["net_id"], f"r{rnd}:r{i}", b["layer"], polyline=to_mm(b["waypoints"]))
            vs = check_keepout([cu], keepouts)
            verdicts[(rnd, i)] = (cu.as_rect(), bool(vs), [v.subject_b for v in vs])
    # 单 route 整链 bbox → 拒
    assert verdicts[(3, 0)][1] and verdicts[(3, 0)][2] == ["K1"], verdicts[(3, 0)]
    assert verdicts[(4, 0)][1] and verdicts[(4, 0)][2] == ["K2"], verdicts[(4, 0)]
    # via 链各段 bbox 局部化 → 全过
    for key, (bb, viol, _) in verdicts.items():
        if key[0] in (15, 16):
            assert not viol, f"{key} 段 bbox 应避区：bbox={bb}"
    # 台账侧 verdict 逐位一致（r3/r4 route 拒收且码/区一致；r15/r16 全收）
    acc3 = {a["index"] for a in rows[3]["accepted"]}
    acc4 = {a["index"] for a in rows[4]["accepted"]}
    acc15 = {a["index"] for a in rows[15]["accepted"]}
    acc16 = {a["index"] for a in rows[16]["accepted"]}
    assert 0 not in acc3 and 0 not in acc4, "台账 r3/r4 route 应拒收"
    assert rows[3]["rejected"][0]["code"] == "V_KEEPOUT" and \
        rows[3]["rejected"][0]["detail"] == "zone:K1", "台账 r3 拒码应 V_KEEPOUT/zone:K1"
    assert rows[4]["rejected"][0]["code"] == "V_KEEPOUT" and \
        rows[4]["rejected"][0]["detail"] == "zone:K2", "台账 r4 拒码应 V_KEEPOUT/zone:K2"
    assert {0, 2, 4} <= acc15 and {0, 2, 4, 6} <= acc16, "台账 r15/r16 route 应全收"

    # ---------- 量化面：交叠面积 / 面积对比（全部由 rect 直算） ----------
    bb3, bb4 = verdicts[(3, 0)][0], verdicts[(4, 0)][0]
    a3, a4 = rect_area(bb3), rect_area(bb4)
    ox0, oy0 = max(bb3[0], k1[0]), max(bb3[1], k1[1])
    ox1, oy1 = min(bb3[2], k1[2]), min(bb3[3], k1[3])
    ov = (ox1 - ox0) * (oy1 - oy0)
    assert ox1 > ox0 and oy1 > oy0 and ov > 0, f"r3 bbox∩K1 交叠面积应>0，实得 {ov}"
    chain15 = [rect_area(verdicts[(15, i)][0]) for i in range(len(r15))]
    chain16 = [rect_area(verdicts[(16, i)][0]) for i in range(len(r16))]
    max15, max16 = max(chain15), max(chain16)
    assert a3 > 0 and a4 > 0, "单 route 整链 bbox 面积应>0"
    assert min(a3, a4) > max(max15, max16), "单 route 最小整链面积应大于链段最大面积"
    z15 = sum(1 for a in chain15 if a == 0)
    z16 = sum(1 for a in chain16 if a == 0)
    n_pass = len(r15) + len(r16)
    g15 = chain_min_gap([verdicts[(15, i)][0] for i in range(len(r15))], keepouts)
    g16 = chain_min_gap([verdicts[(16, i)][0] for i in range(len(r16))], keepouts)

    # ---------- 绘图 ----------
    fig = plt.figure(figsize=(14.2, 10.6), dpi=210)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.62, 1.0], hspace=0.16, wspace=0.10)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])
    axC = fig.add_subplot(gs[1, :])
    KO_FC, CO_FC, WI_FC = "#ffcdd2", "#fff9c4", "#f5f5f5"

    def base_panel(ax, title):
        ax.add_patch(Rectangle((ws["x_min"], ws["y_min"]),
                               ws["x_max"] - ws["x_min"], ws["y_max"] - ws["y_min"],
                               fc=WI_FC, ec="#90a4ae", lw=1.0, zorder=0))
        ax.add_patch(Rectangle((k1[0], k1[1]), k1[2] - k1[0], k1[3] - k1[1],
                               fc=KO_FC, ec="#c62828", lw=1.2, zorder=1))
        ax.add_patch(Rectangle((k2[0], k2[1]), k2[2] - k2[0], k2[3] - k2[1],
                               fc=KO_FC, ec="#c62828", lw=1.2, zorder=1))
        ax.add_patch(Rectangle((c1z["x_min"], c1z["y_min"]),
                               c1z["x_max"] - c1z["x_min"], c1z["y_max"] - c1z["y_min"],
                               fc=CO_FC, ec="#f9a825", lw=1.0, hatch="...", zorder=1, alpha=0.85))
        ax.text((k1[0] + k1[2]) / 2, (k1[1] + k1[3]) / 2,
                reg(f"K1 全层禁布区\nx∈[{k1[0]:g},{k1[2]:g}] y∈[{k1[1]:g},{k1[3]:g}]", k1),
                ha="center", va="center", fontsize=9.8, color="#b71c1c", zorder=8)
        ax.text((k2[0] + k2[2]) / 2, (k2[1] + k2[3]) / 2,
                reg(f"K2 全层禁布区\nx∈[{k2[0]:g},{k2[2]:g}] y∈[{k2[1]:g},{k2[3]:g}]", k2),
                ha="center", va="center", fontsize=9.8, color="#b71c1c", zorder=8)
        ax.text((c1z["x_min"] + c1z["x_max"]) / 2, 37.6,
                f"C1 走廊\nx∈[{c1z['x_min']:g},{c1z['x_max']:g}]",
                ha="center", fontsize=9.2, color="#f57f17", zorder=8)
        ax.set_xlim(-2.5, 52.5)
        ax.set_ylim(-2.5, 41.5)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=12.2)

    def draw_net(ax, endpoints, color, name):
        for x, y in endpoints:
            ax.plot(x, y, "s", ms=7, mfc="white", mec=color, mew=2.0, zorder=9)
        ax.annotate(name, endpoints[0], xytext=(0, -3.4), textcoords="offset points",
                    ha="center", fontsize=10.5, color=color, fontweight="bold")

    def draw_bbox(ax, bb, color, ls="--", lw=1.3, z=5, alpha=0.95):
        ax.add_patch(Rectangle((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1],
                               fill=False, ec=color, ls=ls, lw=lw, zorder=z, alpha=alpha))

    def draw_path(ax, mm_pts, color, lw=2.4, z=6, ls="-"):
        xs, ys = zip(*mm_pts)
        ax.plot(xs, ys, ls=ls, color=color, lw=lw, zorder=z, solid_capstyle="round")

    # —— （a）单 route → 整体 bbox 触区即拒（ETH r3 实拒样本） ——
    base_panel(axA, "（a）单 route 动作：整条 polyline 外接 bbox 判 R6 → 包围盒触区即拒\n"
                    "（ETH-MAC 轮3：U 形线段实际绕开 K1，仍 V_KEEPOUT 拒收）")
    draw_net(axA, eth_ep, "#37474f", "ETH-MAC")
    draw_net(axA, misc_ep, "#00695c", "MISC1")
    draw_path(axA, to_mm(r3[0]["waypoints"]), "#1565c0", lw=2.6)
    draw_bbox(axA, bb3, "#c62828", lw=2.0)
    axA.add_patch(Rectangle((ox0, oy0), ox1 - ox0, oy1 - oy0,
                            fc="#c62828", alpha=0.30, zorder=4))
    axA.annotate(reg(f"route bbox\nx∈[{bb3[0]:g},{bb3[2]:g}]×y∈[{bb3[1]:g},{bb3[3]:g}]", bb3),
                 xy=(bb3[2], 6.5), xytext=(44.0, 5.2),
                 ha="center", fontsize=10.4, color="#c62828", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.5))
    axA.annotate(f"bbox∩K1 交叠 {ov:g} mm²→拒收\n（实际线段绕开也无效）",
                 xy=((ox0 + ox1) / 2, (oy0 + oy1) / 2), xytext=(43.0, 33.0), ha="center",
                 fontsize=10.4, color="#c62828",
                 arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.2))
    draw_path(axA, to_mm(r4[0]["waypoints"]), "#00897b", lw=1.6, ls=(0, (4, 2)), z=5)
    draw_bbox(axA, bb4, "#8d6e63", lw=1.2, ls=":", z=4)
    axA.text(44.0, 13.8, reg(f"MISC1 轮4 同构拒\nbbox x∈[{bb4[0]:g},{bb4[2]:g}]×y∈[{bb4[1]:g},{bb4[3]:g}]", bb4),
             ha="center", va="top", fontsize=9.3, color="#8d6e63")

    # —— （b）多 route＋via 链 → 各段 bbox 局部化即过 ——
    base_panel(axB, "（b）多 route＋转折格点自网 via 链：各段 bbox 局部化 → 全部过 R6\n"
                    "（MISC1 轮15 披露后首发即过＝正对照；ETH-MAC 轮16 主审 FORCE 同构链）")
    draw_net(axB, eth_ep, "#37474f", "ETH-MAC")
    draw_net(axB, misc_ep, "#00695c", "MISC1")
    seg_colors = ["#6a1b9a", "#283593", "#00838f"]
    for i, b in enumerate(r15):
        draw_path(axB, to_mm(b["waypoints"]), seg_colors[i % 3], lw=2.4, z=7)
        draw_bbox(axB, verdicts[(15, i)][0], seg_colors[i % 3], lw=1.15, z=3, alpha=0.75)
    for v in vias_of(15):
        x, y = to_mm([v["grid"]])[0]
        axB.plot(x, y, "o", ms=8, mfc="white", mec="#6a1b9a", mew=2.2, zorder=9)
    for i, b in enumerate(r16):
        draw_path(axB, to_mm(b["waypoints"]), "#ef6c00", lw=2.0, z=6)
        draw_bbox(axB, verdicts[(16, i)][0], "#ef6c00", lw=1.0, z=2, alpha=0.65)
    for v in vias_of(16):
        x, y = to_mm([v["grid"]])[0]
        axB.plot(x, y, "o", ms=7.5, mfc="white", mec="#ef6c00", mew=2.0, zorder=9)
    v15 = [to_mm([v["grid"]])[0] for v in vias_of(15)]
    v16 = [to_mm([v["grid"]])[0] for v in vias_of(16)]
    lab15 = ("MISC1 轮15 via-hub 链（披露后首发即过）\n"
             + "\n".join(seg_line(i, verdicts[(15, i)][0], chain15[i]) for i in range(len(r15)))
             + f"\n最贴禁布区间隙 {g15[0]:g} mm（段{CIRC[g15[1]]} vs {g15[2]}）")
    axB.annotate(lab15, xy=v15[1], xytext=(0.8, 14.6), va="top", fontsize=9.0, color="#4a148c",
                 arrowprops=dict(arrowstyle="->", color="#6a1b9a", lw=1.3))
    hdr16 = f"（{len(r16)} 段共线·A 全 0）" if z16 == len(r16) else f"（{len(r16)} 段）"
    lab16 = (f"ETH 轮16 FORCE 链{hdr16}\n"
             + "\n".join(seg_line(i, verdicts[(16, i)][0], chain16[i], with_area=False)
                         for i in range(len(r16)))
             + f"\n最贴禁布区间隙 {g16[0]:g} mm（段{CIRC[g16[1]]} vs {g16[2]}）")
    axB.annotate(lab16, xy=v16[1], xytext=(33.2, 34.0), va="top", fontsize=9.0, color="#e65100",
                 arrowprops=dict(arrowstyle="->", color="#ef6c00", lw=1.3))
    axB.text(26, 1.2, f"各虚框=单段 route bbox（as_rect），均不触 K1/K2 → {n_pass}/{n_pass} 受理",
             ha="center", va="bottom", fontsize=9.8, color="#37474f")

    # —— （c）量化对比小图：单 route 整链面积 vs via 链各段面积/最大值 ——
    axC.set_title("（c）量化面：外接矩形（as_rect）面积对比——单 route 整链 bbox vs via 链各段 bbox",
                  fontsize=12.2)
    xs15 = [2.3, 3.05, 3.8]
    xs16 = [5.15, 5.85, 6.55, 7.25]
    axC.bar([0], [ov], width=0.62, color="#8e0000", hatch="//", ec="white", zorder=3)
    axC.bar([0], [a3 - ov], width=0.62, bottom=[ov], color="#e57373", zorder=3)
    axC.bar([0.95], [a4], width=0.62, color="#8d6e63", alpha=0.9, zorder=3)
    for x, a, c in zip(xs15, chain15, seg_colors):
        axC.bar([x], [a], width=0.58, color=c, zorder=3)
    for x, a in zip(xs16, chain16):
        axC.bar([x], [a], width=0.52, color="#ef6c00", zorder=3)
    axC.text(0, a3 + 12, f"A={a3:g}", ha="center", fontsize=10.0, fontweight="bold", color="#b71c1c")
    axC.text(0.95, a4 + 12, f"A={a4:g}", ha="center", fontsize=10.0, color="#5d4037")
    for i, (x, a) in enumerate(zip(xs15, chain15)):
        tag = "＝链最大" if (a == max15 and a > 0) else ""
        axC.text(x, a + 12, f"{CIRC[i]}A={a:g}{tag}", ha="center", fontsize=9.4, color="#4a148c")
    for i, x in enumerate(xs16):
        axC.text(x, 12, f"{CIRC[i]}A=0", ha="center", fontsize=9.4, color="#e65100")
    axC.hlines(max15, 2.0, 4.15, colors="#6a1b9a", ls="--", lw=1.4, zorder=4)
    axC.set_xticks([0.475, 3.05, 6.2])
    axC.set_xticklabels(["单 route 整链 bbox（r3/r4·均拒收）",
                         f"MISC1 r15 链段（{len(r15)} 段全过）",
                         f"ETH-MAC r16 链段（FORCE·{len(r16)} 段全过）"], fontsize=10.4)
    axC.set_ylabel("外接矩形面积（mm²）", fontsize=10.6)
    axC.set_ylim(0, 640)
    axC.set_xlim(-0.7, 8.2)
    axC.grid(axis="y", alpha=0.3)
    for xsep in (1.65, 4.55):
        axC.axvline(xsep, color="#cfd8dc", ls=":", lw=1.2)
    axC.text(0.985, 0.97, f"单 route 整链最小 {min(a3, a4):g} mm²＝via 链段最大 {max(max15, max16):g} mm²"
                          f" 的 {min(a3, a4) / max(max15, max16):.1f} 倍\n"
                          f"（r3 整链 {a3:g} mm² 为 r15 最大段的 {a3 / max15:.1f} 倍）",
             transform=axC.transAxes, ha="right", va="top", fontsize=10.2, color="#37474f")
    axC.legend(handles=[Patch(fc="#8e0000", hatch="//", ec="white",
                              label=f"r3 bbox∩K1 交叠 {ov:g} mm²（R6 拒收触发面）"),
                        Patch(fc="#e57373", label="r3 bbox 其余部分")],
               loc="upper right", bbox_to_anchor=(0.985, 0.86), fontsize=9.4, framealpha=0.95)
    axC.text(0.985, 0.60, f"注：纯竖/横共线段顶点 bbox 退化为线（A=0）；本批 r15 {z15}/{len(r15)} 段、"
                          f"r16 {z16}/{len(r16)} 段退化；as_rect＝折线顶点 min/max（不含半宽）",
             transform=axC.transAxes, ha="right", va="top", fontsize=9.0, color="#616161")

    # —— 标注串回 parse 核验（生成值==verdicts/board rect） ——
    n_checked = verify_annotations()

    fig.suptitle("图 9　F-bbox 逃生数据版（板件几何＋run5 台账＋验证器直读）："
                 "单 route 整体 bbox 触区即拒 vs 多 route＋via 链局部化",
                 fontsize=15.2, fontweight="bold", y=0.988)
    fig.text(0.5, 0.026,
             f"数据源：boards/d/demo-01-v2-corridor.board.v1.json（K1/K2/C1/端点 mm 直读）＋run5/ledger.jsonl（r3/r4/r15/r16 格点×{PITCH:g}mm）；\n"
             f"R6 判定＝直接调用验证器 v5/drc.check_keepout 复算（r3/r4 拒、r15/r16 共 {n_pass} 段全过，与台账 verdict 逐位一致；RESULT sha16={result_sha} 重算一致）",
             ha="center", va="bottom", fontsize=9.2, color="#616161")
    fig.text(0.5, 0.006,
             f"图内坐标区间/面积/间隙标注串全部由 verdicts（as_rect）计算值 f-string 生成并回 parse 核验（{n_checked} 条逐位一致）；"
             f"量化面：bbox∩K1 交叠 {ov:g} mm²、链段最大 {max(max15, max16):g} mm²、整链最小 {min(a3, a4):g} mm²",
             ha="center", va="bottom", fontsize=8.8, color="#757575")
    fig.subplots_adjust(left=0.060, right=0.992, top=0.925, bottom=0.088,
                        hspace=0.20, wspace=0.10)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    assert os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024, "输出 PNG 缺失或过小"
    print("OK 图 9：", OUT, os.path.getsize(OUT), "B")
    print(f"  量化面：交叠 {ov:g} mm²；单 route 面积 r3={a3:g} r4={a4:g}；"
          f"链段 r15={chain15} max={max15:g}、r16={chain16} max={max16:g}")
    print(f"  标注串回 parse 核验 {n_checked} 条全部一致；链最小间隙 r15={g15} r16={g16}")
    for k, v in sorted(verdicts.items()):
        print("  ", k, tuple(round(x, 2) for x in v[0]), "拒" if v[1] else "过", v[2])


if __name__ == "__main__":
    main()
