"""只读板几何提取（② 输入：p3 布局时点快照）。纯内存、零落盘、零子进程。

KiCad 10 板 s-expr（sexpr_min 解析）：
  (footprint "LIB" (at x y [rot]) (property "Reference" "REF") (pad "N" type (at x y [rot]) (size w h) (net "NAME")))
坐标变换（已用 opens.csv 61 断点 83 个焊盘端点交叉验证，含 19 个旋转封装端点）：
  abs = fp_at + R(rot)·pad_at，R 为 KiCad 屏幕逆时针（y 向下）：
    ax = fx + px·cos + py·sin ; ay = fy + py·cos − px·sin
浮点只用于读入坐标与刚体变换；比较全部带固定容差/取整（SPEC §2.2）。
"""

from __future__ import annotations

import math

from . import sexpr_min

SIDES = ("N", "E", "S", "W")  # 稳定顺序（角垫并列时的 tie-break 序）


def _at_xy(node):
    at = sexpr_min.find_first(node, "at")
    x, y = float(at[1]), float(at[2])
    rot = float(at[3]) if len(at) > 3 and isinstance(at[3], str) else 0.0
    return x, y, rot


def transform(px, py, fx, fy, rot_deg):
    r = math.radians(rot_deg)
    c, s = math.cos(r), math.sin(r)
    return (fx + px * c + py * s, fy + py * c - px * s)


def parse_board(path):
    """板文件 → {footprints, pads, bbox}。只读解析 + finalize。"""
    root = sexpr_min.load_file(path)[0]
    footprints = {}
    for fp in sexpr_min.find_all(root, "footprint"):
        ref = None
        for prop in sexpr_min.find_all(fp, "property"):
            if sexpr_min.get_str(prop, 1) == "Reference":
                ref = sexpr_min.get_str(prop, 2)
        if ref is None:
            continue
        fx, fy, rot = _at_xy(fp)
        pads = []
        for pad in sexpr_min.find_all(fp, "pad"):
            num = sexpr_min.get_str(pad, 1)
            px, py, _ = _at_xy(pad)
            size = sexpr_min.find_first(pad, "size")
            w = float(size[1]) if size else 0.0
            h = float(size[2]) if size else 0.0
            netnode = sexpr_min.find_first(pad, "net")
            net = sexpr_min.get_str(netnode, 1) if netnode else None
            ax, ay = transform(px, py, fx, fy, rot)
            pads.append({"ref": ref, "num": num, "net": net,
                         "x": ax, "y": ay, "w": w, "h": h})
        footprints[ref] = {"ref": ref, "x": fx, "y": fy, "rot": rot, "pads": pads}
    return finalize_board(footprints)


def finalize_board(footprints):
    """补齐派生几何：pad 绝对侧别、封装 pad-bbox、全板 bbox（合成板同用）。"""
    all_pads = sorted((p for f in footprints.values() for p in f["pads"]),
                      key=lambda p: (p["ref"], p["num"]))
    for ref, f in footprints.items():
        xs = [p["x"] for p in f["pads"]]
        ys = [p["y"] for p in f["pads"]]
        f["bbox"] = (min(xs), min(ys), max(xs), max(ys)) if xs else (f["x"], f["y"],
                                                                     f["x"], f["y"])
    for p in all_pads:
        x0, y0, x1, y1 = footprints[p["ref"]]["bbox"]
        # 最近边距离（角垫若与两条边距离并列（容差内）→ 记两侧，逃逸需求保守计数）
        d = {"N": abs(p["y"] - y0), "S": abs(y1 - p["y"]),
             "E": abs(x1 - p["x"]), "W": abs(p["x"] - x0)}
        m = min(d[s] for s in SIDES)
        tol = 1e-6
        p["side"] = [s for s in SIDES if d[s] <= m + tol]

    xs = [p["x"] for p in all_pads]
    ys = [p["y"] for p in all_pads]
    return {"footprints": footprints, "pads": all_pads,
            "bbox": (min(xs), min(ys), max(xs), max(ys))}


def bbox_inflate(bb, m):
    return (bb[0] - m, bb[1] - m, bb[2] + m, bb[3] + m)


def bbox_area(bb):
    return max(0.0, bb[2] - bb[0]) * max(0.0, bb[3] - bb[1])


def point_in_bbox(x, y, bb):
    return bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]


def seg_samples(x0, y0, x1, y1, step):
    """线段等距采样（含两端），步长 step（mm）。确定性：采样数=ceil(len/step)+1。"""
    length = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(math.ceil(length / step)) + 1) if length > 0 else 1
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return out


def seg_rect_hits_segment(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    """通道矩形（轴对齐）与线段相交测试（粗判：采样+包围盒，确定性）。"""
    for x, y in seg_samples(ax0, ay0, ax1, ay1, 0.1):
        if bx0 <= x <= bx1 and by0 <= y <= by1:
            return True
    return False
