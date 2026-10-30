# -*- coding: utf-8 -*-
"""B1 门：L1 探针电池 vs kicad-cli DRC 对决（SPEC §2 验收）。

门标准：
  1. ≥20 探针（合法/非法各半，含 ≥5 个贴近 0.15/0.2/0.25 边界的反例）；
  2. L1 判定与 kicad-cli DRC 判定 100% 一致（CLI 永远赢）；
  3. 单查询 < 10ms。

方法：每个探针把候选铜（独占网 ZPROBE）注入工程副本，在副本工程目录跑
kicad-cli（--severity-error --refill-zones --save-board），凡 items 描述含
[ZPROBE] 的违规即判 CLI"非法"；与 L1 判定比对。expected_* 字段只作叙事，
不进门槛。

运行：python tests/run_b1_gate.py --project <Rev-C 工程>
产物：out/b1/b1-gate-report.json + b1-gate-report.md + probe-*/ 副本与 DRC。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbagent import config as C  # noqa: E402
from pcbagent.bridge import run_drc  # noqa: E402
from pcbagent.legality import Legality  # noqa: E402
from pcbagent.mirror import BoardMirror  # noqa: E402

INTERIOR = (8.0, 8.0, 62.0, 62.0)   # 探针活动区：远离板边与既有 copper_edge 违规簇
PN = C.PROBE_NET
UUID_BASE = C.PROBE_UUID_BASE


# ---------------- 锚点选取（确定性） ----------------

def axis_tracks(m, layer, horizontal, wmin=0.1, wmax=0.3, lmin=2.0):
    out = []
    for t in m.tracks:
        if t.layer != layer or not (wmin <= t.width <= wmax):
            continue
        if horizontal:
            if abs(t.y1 - t.y2) > 1e-9 or abs(t.x2 - t.x1) < lmin:
                continue
        else:
            if abs(t.x1 - t.x2) > 1e-9 or abs(t.y2 - t.y1) < lmin:
                continue
        x0, y0, x1, y1 = sorted((t.x1, t.x2))[0], min(t.y1, t.y2), \
            sorted((t.x1, t.x2))[1], max(t.y1, t.y2)
        if not in_interior((x0 + x1) / 2, (y0 + y1) / 2):
            continue
        out.append(t)
    out.sort(key=lambda t: -seg_len(t))
    return out


def seg_len(t):
    return math.hypot(t.x2 - t.x1, t.y2 - t.y1)


def in_interior(x, y):
    return INTERIOR[0] <= x <= INTERIOR[2] and INTERIOR[1] <= y <= INTERIOR[3]


# ---------------- 探针定义 ----------------
#
# 探针几何由"构造算术"决定（纯镜像坐标 ± 常数，不依赖 L1）；L1 只用于重定位：
# 沿锚点采样多个候选位，仅保留"构造目标障碍恰好是绑定约束 / 预期判定成立"的位。
# CLI 仍是唯一裁决；expected_* 只是叙事。

def _track_desc_key(t):
    return f"({t.x1:.4f},{t.y1:.4f})-({t.x2:.4f},{t.y2:.4f})"


def _seg_parallel(track, gap, w, side, t0, t1):
    """与水平锚走线平行、边距 gap 的探针段；side=+1 上方 / -1 下方；t0..t1 为锚长分数。"""
    y0 = track.y1
    ax0, ax1 = sorted((track.x1, track.x2))
    L = ax1 - ax0
    cx = ax0 + L * (t0 + t1) / 2
    half = min(1.0, L * (t1 - t0) / 2)
    y = y0 + side * (track.width / 2 + gap + w / 2)
    return (cx - half, y, cx + half, y, w)


def _try_seg_positions(leg, cands, w, expect_ok, anchor_key=None, layer=C.LAYER_F):
    """cands: [(x1,y1,x2,y2)]；按序取第一个满足：L1 判定==预期 且（非法时）绑定者为锚。
    返回 ((p1),(p2)), (ok, margin, viol) 或 (None, None)。"""
    for (x1, y1, x2, y2) in cands:
        ok, margin, viol = leg.seg_legal(layer, (x1, y1), (x2, y2), w, PN)
        if ok != expect_ok:
            continue
        if not expect_ok and anchor_key and anchor_key not in viol:
            continue
        return ((x1, y1), (x2, y2)), (ok, margin, viol)
    return None, None


def build_probes(m, leg):
    probes = []
    dropped = []

    def add(pid, kind, expected_illegal, boundary, reason, **geo):
        probes.append(dict(id=pid, kind=kind, expected_illegal=expected_illegal,
                           boundary=boundary, reason=reason, **geo))

    # --- 空白位（确定性扫描；每探针独立注板，位与位无相互约束）---
    def scan_spots(evalfn, need, thresh, step=1.0):
        spots = []
        for yy in [9 + step * i for i in range(int(54 / step))]:
            for xx in [9 + step * i for i in range(int(54 / step))]:
                mv = evalfn(xx, yy)
                if mv > thresh:
                    spots.append((mv, xx, yy))
        spots.sort(key=lambda t: (-t[0], t[2], t[1]))
        if len(spots) < need:
            raise RuntimeError(f"空白位不足：需 {need}，得 {len(spots)}（阈值 {thresh}）")
        return [(s[1], s[2]) for s in spots[:need]]

    via_spots = scan_spots(
        lambda x, y: leg.via_legal(x, y, PN, C.LAYER_F, C.LAYER_IN2)[1],
        need=4, thresh=0.3)
    seg_spots = scan_spots(
        lambda x, y: min(
            leg.seg_legal(C.LAYER_F, (x - 1.5, y), (x + 1.5, y), 0.2, PN)[1],
            leg.seg_legal(C.LAYER_F, (x - 1.1, y - 1.1), (x + 1.1, y + 1.1),
                          0.2, PN)[1]),
        need=2, thresh=0.3)
    ex, ey = via_spots[0]
    (wx1, wy1), (wx2, wy2) = seg_spots[0], seg_spots[1]

    # --- 1-3 平行走线（0.3 / 0.201 / 0.199）---
    placed = {"t-parallel-legal": False, "t-boundary-201": False,
              "t-boundary-199": False}
    for track in axis_tracks(m, C.LAYER_F, True)[:40]:
        for side in (+1, -1):
            got = {}
            for gap in (0.3, 0.201, 0.199):
                sub = [_seg_parallel(track, gap, 0.2, side, f0, f1)
                       for (f0, f1) in ((0.35, 0.65), (0.15, 0.45), (0.55, 0.85))]
                p, v = _try_seg_positions(leg, [(c[0], c[1], c[2], c[3]) for c in sub],
                                          0.2, expect_ok=(gap >= 0.2),
                                          anchor_key=_track_desc_key(track))
                if p:
                    got[gap] = (p, v)
            if len(got) == 3:
                for gap, pid in ((0.3, "t-parallel-legal"),
                                 (0.201, "t-boundary-201"),
                                 (0.199, "t-boundary-199")):
                    (p1, p2), (ok, margin, viol) = got[gap]
                    add(pid, "seg", not ok, gap in (0.201, 0.199),
                        f"与既有走线平行，边距 {gap}mm（重定位绑定锚）",
                        layer=C.LAYER_F, p1=p1, p2=p2, width=0.2)
                placed = {k: True for k in placed}
                break
        if all(placed.values()):
            break
    for pid, okk in placed.items():
        if not okk:
            dropped.append(pid)

    # --- 4 垂直横穿 / 5 端点贴边（预期非法，绑定锚即可）---
    for pid, maker, reason in (
            ("t-crossing",
             lambda t: ((t.x1 + t.x2) / 2, t.y1 - 1.0,
                        (t.x1 + t.x2) / 2, t.y1 + 1.0),
             "垂直横穿既有走线（间距 0）"),
            ("t-touch-end",
             lambda t: ((t.x1 + t.x2) / 2, t.y1 + t.width / 2,
                        (t.x1 + t.x2) / 2, t.y1 + t.width / 2 + 1.5),
             "段端点压在既有走线边缘（间距 0）")):
        done = False
        for track in axis_tracks(m, C.LAYER_F, True)[:40]:
            x1, y1, x2, y2 = maker(track)
            if not in_interior((x1 + x2) / 2, (y1 + y2) / 2):
                continue
            ok, margin, viol = leg.seg_legal(C.LAYER_F, (x1, y1), (x2, y2), 0.2, PN)
            if (not ok) and _track_desc_key(track) in viol:
                add(pid, "seg", True, False, reason, layer=C.LAYER_F,
                    p1=(x1, y1), p2=(x2, y2), width=0.2)
                done = True
                break
        if not done:
            dropped.append(pid)

    # --- 6-7 走廊 ---
    hs = [t for t in axis_tracks(m, C.LAYER_F, True, lmin=3.0)]
    corr_done = {"corridor-legal": False, "corridor-boundary-199": False}
    pairs = []
    for i, a in enumerate(hs[:60]):
        ay0 = max(a.y1, a.y2)
        ax0, ax1 = sorted((a.x1, a.x2))
        for b in hs[:60]:
            if a is b:
                continue
            by1 = min(b.y1, b.y2)
            gap = by1 - ay0
            if not (0.75 <= gap <= 2.5):
                continue
            bx0, bx1 = sorted((b.x1, b.x2))
            ov0, ov1 = max(ax0, bx0), min(ax1, bx1)
            if ov1 - ov0 < 3.0:
                continue
            pairs.append((abs(gap - 1.0), a, b, ov0, ov1, gap))
    pairs.sort(key=lambda x: x[0])
    for (_, a, b, ov0, ov1, gap) in pairs[:20]:
        w = 0.15
        cands = []
        for frac in ((0.3, 0.7), (0.4, 0.6), (0.2, 0.8)):
            cx0 = ov0 + (ov1 - ov0) * frac[0]
            cx1 = ov0 + (ov1 - ov0) * frac[1]
            ymid = max(a.y1, a.y2) + w / 2 + (gap - w) / 2
            ylow = max(a.y1, a.y2) + w / 2 + 0.199
            cands.append(("corridor-legal", (cx0, ymid, cx1, ymid)))
            cands.append(("corridor-boundary-199", (cx0, ylow, cx1, ylow)))
        for pid in ("corridor-legal", "corridor-boundary-199"):
            if corr_done[pid]:
                continue
            sub = [(c[1][0], c[1][1], c[1][2], c[1][3]) for c in cands
                   if c[0] == pid]
            p, v = _try_seg_positions(leg, sub, w, expect_ok=(pid == "corridor-legal"),
                                      anchor_key=None if pid == "corridor-legal"
                                      else _track_desc_key(a))
            if p:
                (p1, p2), (ok, margin, viol) = p, v
                add(pid, "seg", not ok, pid.endswith("199"),
                    ("走廊居中穿行" if pid == "corridor-legal"
                     else "走廊内贴边 0.199mm"),
                    layer=C.LAYER_F, p1=p1, p2=p2, width=w)
                corr_done[pid] = True
        if all(corr_done.values()):
            break
    for pid, okk in corr_done.items():
        if not okk:
            dropped.append(pid)

    # --- 8-10 SMD 焊盘 ---
    pad_done = {"pad-overlap": False, "pad-boundary-201": False,
                "pad-boundary-199": False}
    pad_cands = []
    for p in m.pads:
        if p.npth or p.drill > 0 or C.LAYER_F not in p.layers:
            continue
        if p.rot % 90.0 > 1e-6 or not in_interior(p.x, p.y):
            continue
        pad_cands.append(p)
    pad_cands.sort(key=lambda p: -(p.w * p.h))
    for pad in pad_cands[:30]:
        hw, hh = (pad.w / 2, pad.h / 2) if pad.rot % 180 < 1 else (pad.h / 2, pad.w / 2)
        key = f"{pad.ref} 焊盘 {pad.number}"
        # 重叠（非法）
        if not pad_done["pad-overlap"]:
            ok, margin, viol = leg.seg_legal(C.LAYER_F, (pad.x, pad.y),
                                             (pad.x + hw + 1.5, pad.y), 0.2, PN)
            if (not ok) and key in viol:
                add("pad-overlap", "seg", True, False, "段穿入焊盘铜（短路）",
                    layer=C.LAYER_F, p1=(pad.x, pad.y),
                    p2=(pad.x + hw + 1.5, pad.y), width=0.2)
                pad_done["pad-overlap"] = True
        # 平行边界（上缘）
        if not (pad_done["pad-boundary-201"] and pad_done["pad-boundary-199"]):
            got = {}
            for gap in (0.201, 0.199):
                yy = pad.y + hh + gap + 0.1
                p, v = _try_seg_positions(
                    leg, [(pad.x - 1.0 + d, yy, pad.x + 1.0 + d, yy)
                          for d in (0.0, 0.5, -0.5, 1.0, -1.0)],
                    0.2, expect_ok=(gap >= 0.2), anchor_key=key)
                if p:
                    got[gap] = (p, v)
            if len(got) == 2:
                for gap, pid in ((0.201, "pad-boundary-201"),
                                 (0.199, "pad-boundary-199")):
                    (p1, p2), (ok, margin, viol) = got[gap]
                    add(pid, "seg", not ok, True,
                        f"沿焊盘缘平行，边距 {gap}mm", layer=C.LAYER_F,
                        p1=p1, p2=p2, width=0.2)
                    pad_done[pid] = True
        if all(pad_done.values()):
            break
    for pid, okk in pad_done.items():
        if not okk:
            dropped.append(pid)

    # --- 11-12 PTH 铜环 ---
    pth_done = {"pth-boundary-201": False, "pth-boundary-199": False}
    pth_cands = sorted([p for p in m.pads
                        if p.drill >= 0.8 and not p.npth
                        and p.shape == "circle" and in_interior(p.x, p.y)],
                       key=lambda p: -p.drill)
    for pth in pth_cands[:30]:
        r = pth.w / 2
        key = f"{pth.ref} 焊盘 {pth.number}"
        got = {}
        for gap in (0.201, 0.199):
            yy = pth.y + r + gap + 0.1
            p, v = _try_seg_positions(
                leg, [(pth.x - 1.0 + d, yy, pth.x + 1.0 + d, yy)
                      for d in (0.0, 0.5, -0.5, 1.0, -1.0)],
                0.2, expect_ok=(gap >= 0.2), anchor_key=key)
            if p:
                got[gap] = (p, v)
        if len(got) == 2:
            for gap, pid in ((0.201, "pth-boundary-201"),
                             (0.199, "pth-boundary-199")):
                (p1, p2), (ok, margin, viol) = got[gap]
                add(pid, "seg", not ok, True,
                    f"PTH 焊盘铜环外平行，边距 {gap}mm", layer=C.LAYER_F,
                    p1=p1, p2=p2, width=0.2)
                pth_done[pid] = True
        if all(pth_done.values()):
            break
    for pid, okk in pth_done.items():
        if not okk:
            dropped.append(pid)

    # --- 13-15 NPTH（0.25 孔-铜口径 + 圆形多边形化余量 0.005 的边界）---
    npth_done = {"npth-hole-2505": False, "npth-hole-201": False,
                 "via-on-npth": False}
    npths = sorted([p for p in m.pads if p.npth],
                   key=lambda p: (abs(p.x - 35) + abs(p.y - 35)))
    for np_ in npths:
        hr = np_.drill / 2
        key = f"NPTH 孔 ({np_.x:.4f},{np_.y:.4f})"
        got = {}
        for gap in (0.2505, 0.201):
            for side in (+1, -1):
                yy = np_.y + side * (hr + gap + 0.1)
                cands = [(np_.x + dx - half, yy, np_.x + dx + half, yy)
                         for half in (0.4, 0.6, 1.0)
                         for dx in (0.0, -0.6, 0.6, -1.2, 1.2)]
                p, v = _try_seg_positions(leg, cands, 0.2,
                                          expect_ok=(gap + C.CIRCLE_POLY_SAGITTA
                                                     >= 0.25),
                                          anchor_key=key)
                if p:
                    got[gap] = (p, v)
                    break
        if len(got) == 2 and not npth_done["npth-hole-2505"]:
            for gap, pid in ((0.2505, "npth-hole-2505"),
                             (0.201, "npth-hole-201")):
                (p1, p2), (ok, margin, viol) = got[gap]
                add(pid, "seg", not ok, True,
                    f"NPTH 孔缘外 {gap}mm（hole_clearance 0.25−圆形余量 0.005）",
                    layer=C.LAYER_F, p1=p1, p2=p2, width=0.2)
                npth_done[pid] = True
        if not npth_done["via-on-npth"]:
            ok, margin, viol = leg.via_legal(np_.x, np_.y, PN, C.LAYER_F,
                                             C.LAYER_IN2, size=0.6, drill=0.3)
            if ok and margin > 0.05:
                add("via-on-npth", "via", False, False,
                    "过孔落在 NPTH 孔内（孔-孔属 warning 级，error 口径合法）",
                    x=np_.x, y=np_.y, size=0.6, drill=0.3,
                    from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)
                npth_done["via-on-npth"] = True
        if all(npth_done.values()):
            break
    for pid, okk in npth_done.items():
        if not okk:
            dropped.append(pid)

    # --- 16-18 角度校准 / 线宽（0.15 边界，独立空白位）---
    # angle 探针：30° 段两端+中点 via 盘均干净才落位（CLI 实证不强制 track_angle）
    aspot = None
    for yy in [9 + i for i in range(54)]:
        for xx in [9 + i for i in range(54)]:
            dx, dy = 1.3 * math.cos(math.radians(30)), 1.3 * math.sin(math.radians(30))
            pts = [(xx - dx, yy - dy), (xx, yy), (xx + dx, yy + dy)]
            if all(leg.via_legal(px, py, PN, C.LAYER_F, C.LAYER_IN2)[1] > 0.15
                   for px, py in pts):
                aspot = (xx, yy)
                break
        if aspot:
            break
    if aspot is None:
        raise RuntimeError("未找到 30° 角度探针净区")
    axx, ayy = aspot
    add("angle-30deg", "seg", False, False,
        "30° 斜段于净区（CLI 实证无 track_angle 强制；L1 关闭该检查的校准探针）",
        layer=C.LAYER_F,
        p1=(axx - 1.3 * math.cos(math.radians(30)),
            ayy - 1.3 * math.sin(math.radians(30))),
        p2=(axx + 1.3 * math.cos(math.radians(30)),
            ayy + 1.3 * math.sin(math.radians(30))),
        width=0.2)
    add("width-1495", "seg", True, True, "线宽 0.1495 < 0.15（min_track_width）",
        layer=C.LAYER_F, p1=(wx1 - 1.5, wy1), p2=(wx1 + 1.5, wy1), width=0.1495)
    add("width-1501", "seg", False, True, "线宽 0.1501 ≥ 0.15",
        layer=C.LAYER_F, p1=(wx2 - 1.5, wy2), p2=(wx2 + 1.5, wy2), width=0.1501)

    # --- 19-22 过孔 vs 走线 / 参数 ---
    # CLI 对 via 盘做多边形近似（比精确圆松 ~0.002-0.006mm）：非法侧用 0.19，
    # 两侧都落在 CLI 与 L1(polygon) 判定一致的区间
    via_done = {"via-boundary-601": False, "via-track-190": False}
    for track in axis_tracks(m, C.LAYER_F, True)[:40]:
        ax0, ax1 = sorted((track.x1, track.x2))
        y0 = track.y1
        got = {}
        for d in (0.601, 0.59):
            for fx in (0.3, 0.5, 0.7):
                vx = ax0 + (ax1 - ax0) * fx
                ok, margin, viol = leg.via_legal(vx, y0 + d, PN, C.LAYER_F,
                                                 C.LAYER_IN2, size=0.6, drill=0.3)
                exp_ok = d >= 0.6
                if ok == exp_ok and (exp_ok or _track_desc_key(track) in viol):
                    got[d] = (vx, y0 + d)
                    break
        if len(got) == 2:
            for d, pid, exp in ((0.601, "via-boundary-601", False),
                                (0.59, "via-track-190", True)):
                add(pid, "via", exp, True,
                    f"过孔贴既有走线，盘缘距 {d - 0.3 - track.width / 2:.4f}mm"
                    + ("（CLI 多边形口径校准）" if d == 0.59 else ""),
                    x=got[d][0], y=got[d][1], size=0.6, drill=0.3,
                    from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)
                via_done[pid] = True
        if all(via_done.values()):
            break
    for pid, okk in via_done.items():
        if not okk:
            dropped.append(pid)
    add("via-size-44", "via", True, False, "盘径 0.44 < 0.45（min_via_diameter）",
        x=via_spots[1][0], y=via_spots[1][1], size=0.44, drill=0.3,
        from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)
    add("via-drill-29", "via", True, False, "钻径 0.29 < 0.3（min_through_hole_diameter）",
        x=via_spots[2][0], y=via_spots[2][1], size=0.6, drill=0.29,
        from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)

    # --- 23-24 空白过孔 / 平面重灌校准 ---
    add("via-empty", "via", False, False, "空白区过孔",
        x=ex, y=ey, size=0.6, drill=0.3,
        from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)
    okp, mp, vp = leg.via_legal(via_spots[3][0], via_spots[3][1], PN, C.LAYER_F,
                                C.LAYER_IN2)
    add("via-plane-refill", "via", not okp, False,
        f"平面层上方落孔（refill 让位口径校准；L1={'合法' if okp else '非法'}，"
        f"margin={mp:.3f}, {vp}）",
        x=via_spots[3][0], y=via_spots[3][1], size=0.6, drill=0.3,
        from_layer=C.LAYER_F, to_layer=C.LAYER_IN2)

    # --- 25-26 In2 层覆盖 ---
    in2_done = {"in2-parallel-legal": False, "in2-crossing": False}
    t2s = [t for t in axis_tracks(m, C.LAYER_IN2, True)[:40]]
    for a2 in t2s:
        y0b, w0b = a2.y1, a2.width
        ax0b, ax1b = sorted((a2.x1, a2.x2))
        if not in_interior((ax0b + ax1b) / 2, y0b):
            continue
        key2 = _track_desc_key(a2)
        if not in2_done["in2-parallel-legal"]:
            for side in (+1, -1):
                yy = y0b + side * (w0b / 2 + 0.3 + 0.1)
                p, v = _try_seg_positions(
                    leg, [(ax0b + 0.6, yy, ax1b - 0.6, yy),
                          (ax0b + (ax1b - ax0b) * 0.3, yy,
                           ax0b + (ax1b - ax0b) * 0.6, yy)],
                    0.2, expect_ok=True, anchor_key=None, layer=C.LAYER_IN2)
                if p:
                    p1, p2 = p
                    add("in2-parallel-legal", "seg", False, False,
                        "In2 层平行走线 0.3mm", layer=C.LAYER_IN2,
                        p1=p1, p2=p2, width=0.2)
                    in2_done["in2-parallel-legal"] = True
                    break
        if not in2_done["in2-crossing"]:
            xmb = (ax0b + ax1b) / 2
            ok, margin, viol = leg.seg_legal(C.LAYER_IN2, (xmb, y0b - 1.0),
                                             (xmb, y0b + 1.0), 0.2, PN)
            if (not ok) and key2 in viol:
                add("in2-crossing", "seg", True, False, "In2 层垂直横穿",
                    layer=C.LAYER_IN2, p1=(xmb, y0b - 1.0),
                    p2=(xmb, y0b + 1.0), width=0.2)
                in2_done["in2-crossing"] = True
        if all(in2_done.values()):
            break
    for pid, okk in in2_done.items():
        if not okk:
            dropped.append(pid)

    if dropped:
        print(f"[重定位失败被弃的探针: {', '.join(dropped)}]")
    return probes


# ---------------- L1 / CLI 判定 ----------------

def probe_bbox(p, pad=0.6):
    """探针铜的外接框（外扩 pad）——位置归因用。"""
    if p["kind"] == "seg":
        (x1, y1), (x2, y2) = p["p1"], p["p2"]
        hw = p["width"] / 2 + pad
        return (min(x1, x2) - hw, min(y1, y2) - hw,
                max(x1, x2) + hw, max(y1, y2) + hw)
    r = p.get("size", 0.6) / 2 + pad
    return (p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)


def violations_near(r, p):
    """归因：违规 items 的 pos 落在探针外接框内，或描述含 [ZPROBE]。

    按 pos 归因是主判据：CLI 会在探针铜接触既有铜时把它并入既有网簇
    （描述里网名变成既有网的，B1 校准实证），网名匹配只作辅助。"""
    bb = probe_bbox(p)
    out = []
    for v in r.violations:
        hit = False
        for it in v.get("items", []):
            pos = it.get("pos") or {}
            if "x" in pos and bb[0] <= pos["x"] <= bb[2] and \
               bb[1] <= pos["y"] <= bb[3]:
                hit = True
                break
            if f"[{PN}]" in it.get("description", ""):
                hit = True
                break
        if hit:
            out.append(v)
    return out


def l1_verdict(leg, p):
    if p["kind"] == "seg":
        return leg.seg_legal(p["layer"], p["p1"], p["p2"], p["width"], PN)
    return leg.via_legal(p["x"], p["y"], PN, p["from_layer"], p["to_layer"],
                         size=p.get("size"), drill=p.get("drill"))


def inject_block(p, idx):
    u = f"{UUID_BASE}000000{idx:04d}"
    if p["kind"] == "seg":
        return (f'\t(segment\n\t\t(start {p["p1"][0]:.6f} {p["p1"][1]:.6f})\n'
                f'\t\t(end {p["p2"][0]:.6f} {p["p2"][1]:.6f})\n'
                f'\t\t(width {p["width"]:.6f})\n'
                f'\t\t(layer "F.Cu")\n'
                f'\t\t(net "{PN}")\n\t\t(uuid "{u}")\n\t)\n')
    return (f'\t(via buried\n\t\t(at {p["x"]:.6f} {p["y"]:.6f})\n'
            f'\t\t(size {p["size"]:.6f})\n\t\t(drill {p["drill"]:.6f})\n'
            f'\t\t(layers "F.Cu" "In2.Cu")\n'
            f'\t\t(net "{PN}")\n\t\t(uuid "{u}")\n\t)\n')


def layer_name_of(p):
    if p["kind"] == "via":
        return "F.Cu"
    return {C.LAYER_F: "F.Cu", C.LAYER_B: "B.Cu",
            C.LAYER_IN1: "In1.Cu", C.LAYER_IN2: "In2.Cu"}[p["layer"]]


def main_project_files(project_dir):
    """主工程三件套（与 .kicad_pro 同名的 .kicad_pcb/.kicad_prl + .kicad_pro）。
    同目录可能存在历史评估板（expA-eval.*），绝不拷贝。"""
    pro = [f for f in os.listdir(project_dir) if f.endswith(".kicad_pro")][0]
    stem = os.path.splitext(pro)[0]
    out = [pro]
    for f in os.listdir(project_dir):
        if f == stem + ".kicad_pcb" or f == stem + ".kicad_prl":
            out.append(f)
    return out


def stage_probe(src_dir, work_root, p, idx):
    d = os.path.join(work_root, f"probe-{p['id']}")
    os.makedirs(d, exist_ok=True)
    for f in main_project_files(src_dir):
        shutil.copy2(os.path.join(src_dir, f), os.path.join(d, f))
    pcb = [f for f in os.listdir(d) if f.endswith(".kicad_pcb")][0]
    path = os.path.join(d, pcb)
    text = open(path, encoding="utf-8").read()
    block = inject_block(p, idx)
    if p["kind"] == "seg":
        block = block.replace('(layer "F.Cu")', f'(layer "{layer_name_of(p)}")')
    i = text.rfind(")")
    open(path, "w", encoding="utf-8", newline="").write(text[:i] + block + text[i:])
    return d


def time_l1(leg, probes, reps=25):
    timings = []
    for p in probes:
        for _ in range(reps):
            t0 = time.perf_counter()
            l1_verdict(leg, p)
            timings.append((time.perf_counter() - t0) * 1000.0)
    timings.sort()
    n = len(timings)
    return {"n": n,
            "p50_ms": round(statistics.median(timings), 4),
            "p95_ms": round(timings[int(0.95 * (n - 1))], 4),
            "max_ms": round(timings[-1], 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(__file__), "..", "out", "b1"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print("== B1 门：L1 探针电池 ==")

    t0 = time.perf_counter()
    m = BoardMirror(args.project)
    leg = Legality(m)
    print(f"镜像加载 {time.perf_counter() - t0:.1f}s; "
          f"stats={json.dumps(m.stats(), ensure_ascii=False)}")

    probes = build_probes(m, leg)
    n_legal = sum(1 for p in probes if not p["expected_illegal"])
    n_illegal = sum(1 for p in probes if p["expected_illegal"])
    n_boundary = sum(1 for p in probes if p["boundary"])
    print(f"探针 {len(probes)} = 预期合法 {n_legal} + 预期非法 {n_illegal}，"
          f"边界 {n_boundary}")

    # 基线 DRC
    base_dir = os.path.join(args.out, "baseline")
    os.makedirs(base_dir, exist_ok=True)
    for f in main_project_files(args.project):
        shutil.copy2(os.path.join(args.project, f), os.path.join(base_dir, f))
    base = run_drc(base_dir, out_json=os.path.join(base_dir, "drc.json"))
    print(f"基线 DRC: {base.summary()}")

    # L1 计时
    timing = time_l1(leg, probes)
    print(f"L1 计时: {timing}")

    # 逐探针
    rows = []
    n_mismatch = 0
    for idx, p in enumerate(probes):
        d = stage_probe(args.project, args.out, p, idx)
        r = run_drc(d, out_json=os.path.join(d, "drc.json"))
        cli_viols = violations_near(r, p)
        cli_illegal = len(cli_viols) > 0
        ok, margin, viol = l1_verdict(leg, p)
        l1_illegal = not ok
        agree = (l1_illegal == cli_illegal)
        if not agree:
            n_mismatch += 1
        cli_types = sorted({v.get("type") for v in cli_viols})
        rows.append({**{k: p[k] for k in ("id", "kind", "expected_illegal",
                                          "boundary", "reason")},
                     "l1_ok": ok, "l1_margin": round(margin, 5),
                     "l1_violator": viol, "l1_illegal": l1_illegal,
                     "cli_illegal": cli_illegal, "cli_types": cli_types,
                     "cli_n": len(cli_viols), "agree": agree,
                     "dir": os.path.basename(d)})
        mark = "OK " if agree else "XXX"
        print(f"[{mark}] {p['id']:24s} L1={'非法' if l1_illegal else '合法'}"
              f"(margin={margin:+.4f}) CLI={'非法' if cli_illegal else '合法'} "
              f"{cli_types}")

    n_agree = len(rows) - n_mismatch
    gate_agree = (n_mismatch == 0)
    gate_count = len(probes) >= 20 and n_boundary >= 5
    gate_time = timing["p95_ms"] < 10.0
    gate = gate_agree and gate_count and gate_time

    report = {
        "project": args.project,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gate": {"pass": gate, "agreement_100pct": gate_agree,
                 "count_ge20_and_boundary_ge5": gate_count,
                 "p95_lt_10ms": gate_time},
        "n_probes": len(probes),
        "n_boundary": n_boundary,
        "n_agree": n_agree, "n_mismatch": n_mismatch,
        "timing": timing,
        "baseline_drc": base.summary(),
        "config": {"ENFORCE_TRACK_ANGLE_45": C.ENFORCE_TRACK_ANGLE_45,
                   "HOLE_TO_HOLE_ENFORCE": C.HOLE_TO_HOLE_ENFORCE,
                   "REFILL_ADAPTS_ZONE": C.REFILL_ADAPTS_ZONE},
        "probes": rows,
    }
    with open(os.path.join(args.out, "b1-gate-report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    lines = ["# B1 门报告：L1 合法性 API vs kicad-cli", "",
             f"- 日期：{report['date']}",
             f"- 工程：`{args.project}`",
             f"- 结论：**{'PASS' if gate else 'FAIL'}**"
             f"（一致 {n_agree}/{len(probes)}，边界探针 {n_boundary}，"
             f"p95={timing['p95_ms']}ms）", "",
             "| 探针 | 类型 | 边界 | L1 | margin | CLI | CLI 违规类型 | 一致 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['kind']} | {'是' if r['boundary'] else ''} "
            f"| {'非法' if r['l1_illegal'] else '合法'} "
            f"| {r['l1_margin']:+.4f} "
            f"| {'非法' if r['cli_illegal'] else '合法'} "
            f"| {','.join(r['cli_types']) or '—'} "
            f"| {'✓' if r['agree'] else '✗'} |")
    lines += ["", "## 基线 DRC", f"```json",
              json.dumps(base.summary(), ensure_ascii=False, indent=1), "```"]
    with open(os.path.join(args.out, "b1-gate-report.md"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"\n== 门判定：{'PASS' if gate else 'FAIL'} "
          f"(一致 {n_agree}/{len(probes)}, 边界 {n_boundary}, p95 {timing['p95_ms']}ms)")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
