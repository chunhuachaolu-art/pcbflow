"""Rev-C USB 差分对板面实际几何提取（只读；stdout 重定向落盘）。

输入：snapshots/p3-placement-gates-pass 板快照（只读）。
输出：USB_DP/USB_DM（含 _C）段清单与配对几何（同层平行最近边距）。
"""
import json
import math
import re
import sys

BOARD = ("../../design/coreboard/kicad/stm32h743-coreboard-revc/"
         "stm32h743-coreboard-revc.kicad_pcb")
NETS = ["USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"]


def parse(path):
    text = open(path, encoding="utf-8").read()
    segs = []
    # KiCad 10：段为多行块，net 以名字为键（无数字码）
    pat = re.compile(
        r'\(segment\s+\(start (-?[\d.]+) (-?[\d.]+)\)\s+\(end (-?[\d.]+) '
        r'(-?[\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+'
        r'\(net "([^"]+)"\)')
    for m in pat.finditer(text):
        segs.append({
            "start": [float(m.group(1)), float(m.group(2))],
            "end": [float(m.group(3)), float(m.group(4))],
            "width": float(m.group(5)),
            "layer": m.group(6),
            "net": m.group(7),
        })
    return segs


def seg_vec(s):
    return (s["end"][0] - s["start"][0], s["end"][1] - s["start"][1])


def seg_len(s):
    return math.hypot(*seg_vec(s))


def pt_seg_dist(p, s):
    ax, ay = s["start"]; bx, by = s["end"]; px, py = p
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def seg_gap(s1, s2):
    """两线段中心线最小距离 - 各自半宽 = 边到边距离。"""
    d = min(pt_seg_dist(s1["start"], s2), pt_seg_dist(s1["end"], s2))
    d = min(d, pt_seg_dist(s2["start"], s1), pt_seg_dist(s2["end"], s1))
    return d - (s1["width"] + s2["width"]) / 2.0


def seg_angle(v):
    return math.degrees(math.atan2(v[1], v[0])) % 180.0


def main():
    segs = parse(BOARD)
    out = {"board": BOARD, "pairs": {}}
    for a, b in [("USB_DP", "USB_DM"), ("USB_DP_C", "USB_DM_C")]:
        sa = [s for s in segs if s["net"] == a]
        sb = [s for s in segs if s["net"] == b]
        entry = {
            "seg_count": {a: len(sa), b: len(sb)},
            "widths": {a: sorted({s["width"] for s in sa}),
                       b: sorted({s["width"] for s in sb})},
            "layers": {a: sorted({s["layer"] for s in sa}),
                       b: sorted({s["layer"] for s in sb})},
            "length_mm": round(sum(seg_len(s) for s in sa), 4),
            "pair_analysis": [],
        }
        # 同层、近水平/近垂直的平行段做最近边距分析
        best = None
        for s1 in sa:
            for s2 in sb:
                if s1["layer"] != s2["layer"]:
                    continue
                ang_diff = abs(seg_angle(seg_vec(s1)) -
                               seg_angle(seg_vec(s2)))
                ang_diff = min(ang_diff, 180.0 - ang_diff)
                if ang_diff > 15.0 and (ang_diff < 75.0 or ang_diff > 105.0):
                    continue
                g = seg_gap(s1, s2)
                if g < 0:
                    continue
                overlap_len = min(seg_len(s1), seg_len(s2))
                rec = {"layer": s1["layer"],
                       "gap_mm": round(g, 4),
                       "w1": s1["width"], "w2": s2["width"],
                       "angle_diff_deg": round(ang_diff, 1)}
                if best is None or g < best["gap_mm"]:
                    best = rec
                if g < 1.0 and len(entry["pair_analysis"]) < 8:
                    entry["pair_analysis"].append(rec)
        entry["closest_parallel_gap"] = best
        out["pairs"][a + "+" + b] = entry
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
