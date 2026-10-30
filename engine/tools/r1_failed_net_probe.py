# -*- coding: utf-8 -*-
"""r1_failed_net_probe.py — V5-R1 W-6 失败网端点密封几何 witness 探针。

D-1 立规（主审复核 2026-09-25）：HALT 类呈裁件的引擎实测主张必须附
可复算数据件。本探针沿主审复核 §1-6 方法（独立几何复算）程序化重现：
对指定板的失败网，枚举其每个端点邻域内的异网 pad，计算铜边隙（形状
感知：circle/rect 最小铜距离），与 v5 规则集阈值（hard_rules.R5）及
真实细规则可逃逸阈值（主审口径：0.1mm 线宽+~0.17mm 间隙）对比落盘。

V5-DIAG-REPLAY-R1 W-5（2026-10-02）双口径化：输出面并列披露两口径——
① pad-pad 口径（原有）：邻域 pad 铜对被测 pad 铜的形状感知最近点铜隙，
最宽逃逸走廊=邻域最大铜边隙（主审复核 §1-6 同式）；
② track-pad／全方向射线口径（新增，建议源=r1/bme280-diag/LEAD-REVIEW-
   DIAG-BME280-2026-09-28.md:34「sealed 判定口径（pad-pad 铜隙而非
   track-pad/全方向射线）建议随同升级并双口径披露」）：16 向（22.5°
   步进）射线（长=邻域半径）中心线到邻域 pad 铜的最小距离——中心线
   口径=引擎 R5 判定面（中心线到异网铜 ≥ R5 才可走）。
判定语句仍止于「对照阈值」层；处置定性（(a)/(c)/豁免）终裁归主审/用户。

只读板世界（board.json），不改任何产物；输出 JSON 数据件供披露表
witness 引用。

用法：
  python tools/r1_failed_net_probe.py --board tmp108 --partition PT-A0 \
      --out out/v5-p5/r1/witness/tmp108-A0-geometry.json [--radius 1.6]
"""
import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = os.path.join(ROOT, "out", "v5-p5", "boards")

PROBE_VERSION = "r1_failed_net_probe/1.1"   # W-5 版本登记（1.0=单口径
# pad-pad；1.1=+track-pad/全方向射线口径双披露）

# 真实细规则可逃逸阈值（主审复核 §1-6 口径：6mil fab 常规能力，
# 0.1mm 线宽 + ~0.17mm 间隙）
FINE_RULE_ESCAPABLE_MM = 0.27
# 同口径换算到 track 中心线口径：铜-铜 0.17 + 0.1mm 线半宽 0.05 = 0.22
# （换算披露项，非独立定值；判读披露归主审/用户）
FINE_RULE_ESCAPABLE_CENTERLINE_MM = 0.22
# track-pad／全方向射线口径：方向数与步进（8 向补半角=16 向全方向覆盖）
RAY_DIRECTIONS = 16


def shape_half(padt):
    """pad 铜半尺寸：circle→(r, r)；rect→(hw, hh)。"""
    s = padt["size_mm"]
    if padt["shape"] == "circle":
        return s[0] / 2.0, s[0] / 2.0
    return s[0] / 2.0, s[1] / 2.0


def copper_gap(pa, sa, pb, sb):
    """两 pad 铜面最小距离（mm），形状感知最近点口径（主审复核 §1-6
    同式：两 ⌀d 圆盘=中心距−半径和）：
      circle-circle：dist(中心) − rA − rB
      rect-rect：AABB 轴分离（对角=欧氏组合）
      circle-rect：圆心到盒最近点距离 − r
    """
    if sa["shape"] == "circle" and sb["shape"] == "circle":
        return math.dist(pa, pb) - (sa["size_mm"][0] + sb["size_mm"][0]) / 2.0
    if sa["shape"] == "rect" and sb["shape"] == "rect":
        hx = (sa["size_mm"][0] + sb["size_mm"][0]) / 2.0
        hy = (sa["size_mm"][1] + sb["size_mm"][1]) / 2.0
        dx = abs(pa[0] - pb[0]) - hx
        dy = abs(pa[1] - pb[1]) - hy
        if dx < 0 and dy < 0:   # 铜重叠（异网不应发生，如实落值）
            return math.hypot(dx, dy)
        return math.hypot(max(dx, 0.0), max(dy, 0.0))
    # circle-rect（归一：a=圆、b=盒）
    if sb["shape"] == "circle":
        pa, sa, pb, sb = pb, sb, pa, sa
    r = sa["size_mm"][0] / 2.0
    hx, hy = sb["size_mm"][0] / 2.0, sb["size_mm"][1] / 2.0
    qx = max(abs(pa[0] - pb[0]) - hx, 0.0)
    qy = max(abs(pa[1] - pb[1]) - hy, 0.0)
    return math.hypot(qx, qy) - r


def layers_of(padt):
    ls = padt.get("layers")
    if ls == "all" or ls is None:
        return None   # 通孔 pad（全层）
    return set(ls)


# --------------------------------------------- track-pad／全方向射线口径（W-5）

def _seg_point_dist(a, b, p):
    """点 p 到线段 (a,b) 的距离。"""
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay
    dd = dx * dx + dy * dy
    if dd <= 0.0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / dd))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def _seg_seg_dist(a, b, c, d):
    """两线段最小距离（相交=0）。精确式：距离函数在参数 box 上联合凸，
    非平行段的最小值必在某端点-对段投影达到（平行重叠段投影同值）——
    min(四端点对另段距离) 即精确；相交另判归 0。"""
    def _orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        if v > 1e-12:
            return 1
        if v < -1e-12:
            return -1
        return 0

    def _on_seg(p, q, r):
        return (min(p[0], q[0]) - 1e-12 <= r[0] <= max(p[0], q[0]) + 1e-12
                and min(p[1], q[1]) - 1e-12 <= r[1] <= max(p[1], q[1]) + 1e-12)

    o1, o2 = _orient(a, b, c), _orient(a, b, d)
    o3, o4 = _orient(c, d, a), _orient(c, d, b)
    if (o1 != o2 and o3 != o4) or (o1 == 0 and _on_seg(a, b, c)) \
            or (o2 == 0 and _on_seg(a, b, d)) \
            or (o3 == 0 and _on_seg(c, d, a)) \
            or (o4 == 0 and _on_seg(c, d, b)):
        return 0.0
    return min(_seg_point_dist(a, b, c), _seg_point_dist(a, b, d),
               _seg_point_dist(c, d, a), _seg_point_dist(c, d, b))


def seg_pad_gap(a, b, center, padt):
    """射线段 (a,b) 中心线到 pad 铜的最小距离（track-pad 口径；形状感知：
    circle=点线距−r、rect=段-矩形边最小距，与 pad-pad 口径同一铜几何源）。"""
    if padt["shape"] == "circle":
        r = padt["size_mm"][0] / 2.0
        return _seg_point_dist(a, b, center) - r
    hx, hy = padt["size_mm"][0] / 2.0, padt["size_mm"][1] / 2.0
    x0, y0 = center[0] - hx, center[1] - hy
    x1, y1 = center[0] + hx, center[1] + hy
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    best = float("inf")
    for i in range(4):
        c, d = corners[i], corners[(i + 1) % 4]
        best = min(best, _seg_seg_dist(a, b, c, d))
    # 线段入矩形内部（含穿贯）时四边距离为 0——正确（铜重叠=零隙）
    return best


def track_ray_caliber(pos, near, radius, r5):
    """track-pad／全方向射线口径（W-5 ②）：自端点中心 16 向（22.5° 步进）
    射线（长=邻域半径），逐向取射线中心线到邻域 pad 铜最小距离；最宽走廊
    =逐向最大值。中心线口径=引擎 R5 判定面（中心线到异网铜 ≥ R5 才可走），
    与 pad-pad 口径（铜-铜，R5+线半宽阈值）并列披露。near=该端点邻域内
    层交叠障碍集（probe() 既有面）。"""
    per_dir = {}
    for k in range(RAY_DIRECTIONS):
        ang = math.radians(22.5 * k)
        d = (math.cos(ang), math.sin(ang))
        b = (pos[0] + d[0] * radius, pos[1] + d[1] * radius)
        gap = None
        for ob in near:
            g = seg_pad_gap(pos, b, ob["pos"], ob["pt"])
            gap = g if gap is None else min(gap, g)
        per_dir["%g" % (22.5 * k)] = None if gap is None else round(gap, 4)
    gaps = [g for g in per_dir.values() if g is not None]
    max_c = max(gaps) if gaps else None
    out = {
        "n_directions": RAY_DIRECTIONS,
        "direction_step_deg": 22.5,
        "ray_length_mm": radius,
        "per_direction_gap_mm": per_dir,
        "max_corridor_mm": max_c,
        "min_gap_mm": min(gaps) if gaps else None,
        "v5_r5_centerline_mm": r5,
        "sealed_under_v5_rules": (max_c is not None and max_c < r5),
        "fine_rule_escapable_threshold_centerline_mm":
            FINE_RULE_ESCAPABLE_CENTERLINE_MM,
        "escapable_under_fine_rules":
            (max_c is not None
             and max_c >= FINE_RULE_ESCAPABLE_CENTERLINE_MM),
        "note": ("track-pad/全方向射线口径（16 向×22.5°，射线长=邻域半径；"
                 "track 中心线到邻域 pad 铜最小距离，中心线口径=引擎 R5 判定"
                 "面）；障碍面=层交叠+中心距≤radius+2.0 粗筛（射线尖端的远侧"
                 " pad 计入，宽于 pad-pad 口径的 ≤radius 邻域面）；细规则中心"
                 "线阈值=%.2f=主审口径铜-铜 0.17+0.1mm 线半宽 0.05 换算（换算"
                 "披露项，非独立定值）；判定止于对照阈值层，处置定性终裁归"
                 "主审/用户" % FINE_RULE_ESCAPABLE_CENTERLINE_MM)}
    return out


def probe(board, partition_id, radius, trace_w):
    parts = {p["partition_id"]: p for p in board["partitions"]}
    tgt = parts[partition_id]
    geo = tgt["geometry"]
    r5 = board["hard_rules"]["R5"]["min_clearance_mm"]
    via = board.get("via_model") or {}
    via_drill = via.get("drill_mm") or via.get("drill") or 0.3
    via_dia = (via.get("diameter_mm") or via.get("diameter")
               or via_drill + 2.0 * (via.get("annular_mm") or 0.15))
    via_half = via_dia / 2.0

    # 障碍面：全板其它 partition 的全部 pad（同网 partition 排除）
    obstacles = []
    for pid, p in parts.items():
        if pid == partition_id:
            continue
        g = p["geometry"]
        for pt in g["pad_terminals"]:
            obstacles.append({
                "partition": pid, "pt": pt,
                "pos": g["endpoints"][pt["endpoint"]]})

    endpoints_out = []
    for i, pos in enumerate(geo["endpoints"]):
        pt = next(x for x in geo["pad_terminals"]
                  if x["endpoint"] == i)
        lay = layers_of(pt)
        near = []
        zone = []   # W-5：射线口径障碍面（层交叠+粗筛 radius+2.0，同 pad-pad
        for ob in obstacles:   # 粗筛余量——射线尖端的远侧 pad 也计入）
            olay = layers_of(ob["pt"])
            # 层交叠判定：通孔 pad（None=all）与任何层交叠；否则层集交
            if lay is not None and olay is not None and not (lay & olay):
                continue
            d_c = math.dist(pos, ob["pos"])
            if d_c > radius + 2.0:   # 粗筛（半径+最大 pad 径余量）
                continue
            zone.append(ob)
            gap = copper_gap(pos, pt, ob["pos"], ob["pt"])
            if d_c <= radius:
                near.append({
                    "partition": ob["partition"],
                    "center": [round(ob["pos"][0], 4), round(ob["pos"][1], 4)],
                    "center_dist_mm": round(d_c, 4),
                    "shape": ob["pt"]["shape"],
                    "size_mm": ob["pt"]["size_mm"],
                    "layers": (sorted(lay) if lay is not None
                               else sorted(olay) if olay is not None
                               else "all"),
                    "copper_gap_mm": round(gap, 4)})
        near.sort(key=lambda x: x["copper_gap_mm"])
        gap_min = near[0]["copper_gap_mm"] if near else None
        # 最宽逃逸走廊（主审复核 §1-6 口径：escape 存在性=邻域任一
        # 方向走廊够宽，取邻域最大铜边隙为其下界——对角走廊案例
        # ep1 正交 0.235/对角 0.442 判读以此为准）
        gap_max = near[-1]["copper_gap_mm"] if near else None
        ep_out = {
            "endpoint_index": i,
            "center": [round(pos[0], 4), round(pos[1], 4)],
            "shape": pt["shape"], "size_mm": pt["size_mm"],
            "layers": (sorted(lay) if lay is not None else "all"),
            "n_neighbors_within_radius_mm": len(near),
            "min_copper_gap_mm": gap_min,
            "max_corridor_gap_mm": gap_max,
            "neighbors": near[:12]}
        # W-5 ②：track-pad／全方向射线口径（与 pad-pad 口径并列披露）
        ep_out["track_ray_caliber"] = track_ray_caliber(pos, zone, radius, r5)
        if gap_max is not None:
            ep_out["calibers"] = {
                "v5_r5_plus_half_width_mm": round(r5 + trace_w / 2.0, 4),
                "sealed_under_v5_rules": gap_max < r5 + trace_w / 2.0,
                "v5_r5_flat_mm": r5,
                "sealed_under_r5_flat": gap_max < r5,
                "fine_rule_escapable_threshold_mm": FINE_RULE_ESCAPABLE_MM,
                "escapable_under_fine_rules": gap_max >= FINE_RULE_ESCAPABLE_MM,
                "via_escape_needs_gap_ge_mm": round(
                    2.0 * (r5 + via_half), 4)}
            if gap_max < r5 + trace_w / 2.0:
                ep_out["reading"] = (
                    "v5 R5=%.2fmm 口径下最宽逃逸走廊 %.3fmm（最小邻隙 "
                    "%.3fmm）无 escape 通道（rule-value-sealed）"
                    % (r5, gap_max, gap_min))
                if gap_max >= FINE_RULE_ESCAPABLE_MM:
                    ep_out["reading"] += (
                        "；最宽走廊 ≥ 细规则可逃逸阈值 %.2fmm（真实细规则"
                        "（0.1mm 线宽级）下可逃逸=(c) 类证据）"
                        % FINE_RULE_ESCAPABLE_MM)
        endpoints_out.append(ep_out)
    return {
        "probe": PROBE_VERSION,
        "board_id": board["board_id"],
        "partition_id": partition_id,
        "board_sha256": board["provenance"]["board_sha256"],
        "calibers": [
            "pad-pad（形状感知最近点铜隙；escape=邻域最大铜边隙——主审复核"
            " §1-6 同式）",
            "track-ray（16 向×22.5° 全方向射线中心线到邻域 pad 铜——引擎 R5 "
            "中心线判定面；W-5 双口径化新增）"],
        "params": {
            "neighborhood_radius_mm": radius,
            "trace_width_for_caliber_mm": trace_w,
            "obstacle_scope": "全板异网 partition 全部 pad（同层/通孔）"},
        "rules_cited": {
            "R5_min_clearance_mm": r5,
            "fine_rule_escapable_mm": FINE_RULE_ESCAPABLE_MM,
            "fine_rule_escapable_centerline_mm":
                FINE_RULE_ESCAPABLE_CENTERLINE_MM,
            "via_model": via,
            "via_half_mm_used": via_half},
        "endpoints": endpoints_out,
        "note": "只读几何复算（主审复核 §1-6 方法的程序化重现；W-5 双口径"
                "披露=pad-pad 铜隙+track-pad 全方向射线中心线）；处置定性终裁"
                "归主审/用户，本件仅提供阈值对照数据。",
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--partition", default=None,
                    help="失败网 partition id（如 PT-A0）；缺省取 run-result"
                         " first_fail_net 对应 partition")
    ap.add_argument("--radius", type=float, default=1.6)
    ap.add_argument("--trace-width", type=float, default=0.2,
                    help="escape 口径线宽（HALT §1.2 引擎实跑口径=0.2）")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    bpath = os.path.join(BOARDS, args.board, "board.json")
    board = json.load(open(bpath, encoding="utf-8"))["board"]
    pid = args.partition
    if pid is None:
        rr = os.path.join(BOARDS, args.board, "run-result.json")
        first = json.load(open(rr, encoding="utf-8"))["run"]["execute"][
            "tried_candidates"][0]["first_fail_net"]
        for n in board["nets"]:
            if n["net_id"] == first:
                pid = n["partitions"][0]
                break
        if pid is None:
            raise SystemExit("first_fail_net=%s 无 partition 映射" % first)
    doc = probe(board, pid, args.radius, args.trace_width)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    for ep in doc["endpoints"]:
        print("ep%d %s gap_min=%s %s" % (
            ep["endpoint_index"], ep["center"], ep["min_copper_gap_mm"],
            (ep.get("reading") or "")[:80]))
    print("saved: %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
