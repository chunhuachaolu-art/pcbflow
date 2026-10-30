#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design1_run.py — DESIGN-1 编排脚本（剩余 5 行的设计级出路提案矩阵）。

对象：live 板（stm32h743-coreboard-revc，冻结见证 sha 前缀 dbfea089）快照
副本上的 5 目标网（S1/RIPUP-1 权威行号）。本包零写 live：产出=量化的设计
变更提案矩阵（类 A U1 锚件位姿/引脚场变更、类 B 端点侧变更、类 C waiver
台账），求解验证全部在快照副本/staging 变体上做。

纪律（S1/S2 同源）：
- live 板零写（pre/post sha256 双验）；全程内存 dry-run；
- SAT=witness+L1 终判全过+独立复核；无 witness 不写 SAT；禁自动改判；
- route_grid.py/cli.py/config.py 零改动；cli.py 零依赖；
- 新逻辑=pcbflow/design1_proposal.py（纯函数）+ 本编排脚本；
- 核心产物 canonical JSON、无 wall-clock。

用法（tools/pcbflow 下）：
  python scripts/design1_run.py classb   # 类 B：端点变体重解（快照副本）
  python scripts/design1_run.py classa   # 类 A：U1 移位/剥除重解（staging 变体）
  python scripts/design1_run.py assemble # 决策矩阵 + waiver 台账 + 汇总 JSON
"""

from __future__ import annotations

import datetime
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import board_writer, design1_proposal as D1  # noqa: E402
from pcbflow import hashing, live2s1_experiment as L2S1   # noqa: E402
from pcbflow import live2s2_proposal as P2                # noqa: E402
from pcbflow import residual_cmd, route_grid              # noqa: E402

PCBFLOW_ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(PCBFLOW_ROOT, "out", D1.DESIGN1_DATASET)
WS_DIR = os.path.join(OUT_DIR, "workspace")
SNAP_DIR = os.path.join(WS_DIR, "live")
STAGING_DIR = os.path.join(WS_DIR, "staging")
ROWS_DIR = os.path.join(OUT_DIR, "rows")
PROGRESS = os.path.join(OUT_DIR, "PROGRESS.md")
S1_DIR = os.path.join(PCBFLOW_ROOT, "out", "coreboard-live2b-s1")

REVC_DIR = os.path.join("<HOME>", ".zcode",
                        "workspace", "default", "design", "coreboard",
                        "kicad", "stm32h743-coreboard-revc")
BOARD_FILES = ("stm32h743-coreboard-revc.kicad_pcb",
               "stm32h743-coreboard-revc.kicad_pro")

LN = {0: "F.Cu", 6: "In2.Cu", 4: "In1.Cu", 2: "B.Cu"}


def _fail(msg):
    print("DESIGN1-FAIL: %s" % msg)
    _progress_note("FAIL: %s" % msg)
    sys.exit(1)


def _write_canonical(path, obj):
    data = hashing.canonical_json_bytes(obj)
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds")


def _progress_note(line):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write("- %s %s\n" % (_now(), line))
    print("progress: %s" % line, flush=True)


def preflight():
    for rel, prefix in D1.PROTECTED:
        p = os.path.join(PCBFLOW_ROOT, rel)
        sha = hashing.sha256_file(p)
        if not sha.startswith(prefix):
            _fail("受保护文件 %s sha=%s… 与期望 %s 不符" % (rel, sha[:8], prefix))
    live_sha = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if not live_sha.startswith(D1.LIVE_BOARD_SHA_PREFIX):
        _fail("live 板 sha=%s… 与冻结见证 %s 不符"
              % (live_sha[:8], D1.LIVE_BOARD_SHA_PREFIX))
    if not os.path.exists(os.path.join(SNAP_DIR, BOARD_FILES[0])):
        os.makedirs(SNAP_DIR, exist_ok=True)
        for name in BOARD_FILES:
            shutil.copy2(os.path.join(REVC_DIR, name),
                         os.path.join(SNAP_DIR, name))
    snap_sha = hashing.sha256_file(os.path.join(SNAP_DIR, BOARD_FILES[0]))
    if snap_sha != live_sha:
        _fail("快照板 sha=%s… 与 live 板 %s… 不符" % (snap_sha[:12], live_sha[:12]))
    return live_sha


def _load_bm(dir_path):
    return route_grid.board_model(dir_path)


def _router(bm):
    pa = bm["pa"]
    return pa["Router"](bm["mirror"], legality=pa["Legality"](bm["mirror"]),
                        corridor_of=None, log=lambda *_a: None)


def _target_rows(bm):
    return L2S1.assign_target_rows(residual_cmd._read_opens_rows(bm))


def _s1_cert_cut(net):
    path = os.path.join(S1_DIR, "rows", "%s_%s.json" % (D1.TARGET_ROWS[net], net))
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("certificate_cut_count")


def _ladder(router, bm, net, A, B, margins):
    steps = []
    for mg in margins:
        plan = router._fresh_plan(net, (A[0], A[1], frozenset(A[2])),
                                  (B[0], B[1], frozenset(B[2])))
        bb = P2.widened_bbox(bm["mirror"].bbox(), A[0], A[1], B[0], B[1], mg)
        p = router._try_route(plan, bb)
        r = P2.normalize_plan(p, net)
        steps.append({"margin_mm": mg, "route": r,
                      "region_bbox_mm": [round(v, 4) for v in bb]})
        print("  margin=%s ok=%s fail=%s segs=%d" % (
            mg, r["ok"], r["fail"], len(r["segments"])), flush=True)
        if r["ok"]:
            break
    return steps


def _independent_check(bm, net, route, A, B):
    """witness 独立复核（live2s2_run 同式，双端泛化）：fresh Legality 逐段/
    逐孔 + 两端落铜 + 变体端在既有同网铜上。"""
    pa = bm["pa"]
    G = pa["geometry"]
    leg = pa["Legality"](bm["mirror"])
    seg_bad, via_bad = [], []
    for (L, x1, y1, x2, y2) in route["segments"]:
        ok, margin, viol = leg.seg_legal(L, (x1, y1), (x2, y2),
                                         route["width"], net)
        if not ok:
            seg_bad.append({"seg": [L, x1, y1, x2, y2], "margin": margin,
                            "violator": str(viol)})
    L0, L1l = pa["LAYERS"][0], pa["LAYERS"][1]
    for (x, y) in route["vias"]:
        ok, margin, viol = leg.via_legal(x, y, net, L0, L1l,
                                         size=route["via_size"],
                                         drill=route["via_drill"])
        if not ok:
            via_bad.append({"via": [x, y], "margin": margin,
                            "violator": str(viol)})

    def touches(pt, ls):
        for (L, x1, y1, x2, y2) in route["segments"]:
            if L in ls and G.seg_pt_dist(pt[0], pt[1], x1, y1, x2, y2) <= 1e-6:
                return True
        return any(math.hypot(x - pt[0], y - pt[1]) <= 0.025 + 1e-6
                   for (x, y) in route["vias"])

    a_touch = touches(A[:2], set(A[2]))
    b_touch = touches(B[:2], set(B[2]))
    m = bm["mirror"]
    a_on, b_on = False, False
    for side_pt, ls, flag in ((A[:2], A[2], "a"), (B[:2], B[2], "b")):
        hit = False
        for L in ls:
            for it in m.query_copper(L, side_pt[0] - 0.5, side_pt[1] - 0.5,
                                     side_pt[0] + 0.5, side_pt[1] + 0.5):
                if it.net == net and any(G.pt_prim_dist(side_pt[0],
                                                        side_pt[1], pr) <= 1e-6
                                         for pr in it.prims):
                    hit = True
                    break
            if hit:
                break
        if flag == "a":
            a_on = hit
        else:
            b_on = hit
    return {"seg_checked": len(route["segments"]), "seg_bad": seg_bad,
            "via_checked": len(route["vias"]), "via_bad": via_bad,
            "a_touch": a_touch, "b_touch": b_touch,
            "a_on_existing_net_copper": a_on,
            "b_on_existing_net_copper": b_on,
            "all_ok": not seg_bad and not via_bad and a_touch and b_touch
            and a_on and b_on}


def _collect_copper(bm):
    """镜像 → (tracks, vias)（strip/pocket_wall 输入形状；层名齐备）。"""
    tracks, vias = [], []
    seen_t, seen_v = set(), set()
    for L in bm["pa"]["LAYERS"]:
        for it in bm["mirror"].query_copper(L, -1000, -1000, 1000, 1000):
            g = P2.parse_item_desc(it.desc)
            if not g:
                continue
            if it.kind == "track":
                k = (L, g["x1"], g["y1"], g["x2"], g["y2"], g["net"])
                if k not in seen_t:
                    seen_t.add(k)
                    tracks.append({"layer": L, "layer_name": LN.get(L, "L%s" % L),
                                   "net": g["net"], "x1": g["x1"], "y1": g["y1"],
                                   "x2": g["x2"], "y2": g["y2"],
                                   "width": g["width"]})
            elif it.kind == "via":
                k = (g["x"], g["y"], g["net"])
                if k not in seen_v:
                    seen_v.add(k)
                    vias.append({"x": g["x"], "y": g["y"], "net": g["net"],
                                 "size": g["size"], "drill": g["drill"]})
    return tracks, vias


def _pth_pad_geometry(bm, ref, number):
    """ref.number 焊盘 → (cx, cy, r_pad, r_drill)（镜像 pad + 板文本 drill）。"""
    G = bm["pa"]["geometry"]
    cx = cy = None
    r_pad = None
    for L in bm["pa"]["LAYERS"]:
        for it in bm["mirror"].query_copper(L, -1000, -1000, 1000, 1000):
            if it.kind != "pad":
                continue
            g = P2.parse_item_desc(it.desc)
            if not g or g["ref"] != ref or g["number"] != number:
                continue
            cx, cy = g["x"], g["y"]
            pb = G.prim_bbox(it.prims[0])
            r_pad = round(max(pb[2] - pb[0], pb[3] - pb[1]) / 2.0, 4)
            break
        if cx is not None:
            break
    if cx is None:
        _fail("焊盘 %s.%s 未命中镜像" % (ref, number))
    r_drill = None
    for L in bm["pa"]["LAYERS"]:
        for h in bm["mirror"].query_holes(L, cx - 1.5, cy - 1.5, cx + 1.5,
                                          cy + 1.5):
            pb = G.prim_bbox(h.prim)
            hx, hy = round((pb[0] + pb[2]) / 2.0, 4), round((pb[1] + pb[3]) / 2.0, 4)
            if abs(hx - cx) < 0.02 and abs(hy - cy) < 0.02 and not h.npth:
                r_drill = round((pb[2] - pb[0]) / 2.0, 4)
                break
        if r_drill is not None:
            break
    if r_drill is None:
        _fail("焊盘 %s.%s 未命中 PTH 钻孔" % (ref, number))
    return cx, cy, r_pad, r_drill


def _write_row(name, obj):
    os.makedirs(ROWS_DIR, exist_ok=True)
    path = os.path.join(ROWS_DIR, name)
    sha = _write_canonical(path, obj)
    print("row -> %s (sha=%s…)" % (os.path.relpath(path, PCBFLOW_ROOT),
                                   sha[:8]), flush=True)
    return path


# ---- 类 B：端点变体 -------------------------------------------------------------
PAD_ENLARGE_MM = 2.1   # J3/J4 PTH 焊盘 1.7 → 2.1（pad 加大几何变体）
PAD_ENLARGE_D = 0.95   # 加大后环带中带落点（d∈[0.85,1.05]，孔距裕量 0.10mm）


def _rim_trials(bm, net, row_id, side, A, B, pad_ref, pad_number, rims,
                mech, r_pad, r_drill, premise, ladder, results,
                board_change=None):
    router = _router(bm)
    for rim in rims:
        Vl = (rim["x"], rim["y"], list(A[2] if side == "A" else B[2]))
        (Pa, Pb) = (Vl, B) if side == "A" else (A, Vl)
        steps = _ladder(router, bm, net, Pa, Pb, ladder)
        indep = None
        if any(s["route"]["ok"] for s in steps):
            w = next(s for s in steps if s["route"]["ok"])["route"]
            indep = _independent_check(bm, net, w, Pa, Pb)
        results.append(D1.endpoint_variant_row(
            row_id, net, side,
            dict(rim, kind="pth_pad_rim", pad="%s.%s" % (pad_ref, pad_number),
                 r_pad=r_pad, r_drill=r_drill, lock_mechanism=mech,
                 premise=premise),
            steps, indep, _s1_cert_cut(net), board_change=board_change))


def cmd_classb():
    live_sha = preflight()
    bm = _load_bm(SNAP_DIR)
    rows = _target_rows(bm)
    with open(os.path.join(SNAP_DIR, BOARD_FILES[0]), encoding="utf-8",
              newline="") as f:
        base_text = f.read()
    results = []
    G = bm["pa"]["geometry"]

    # --- VBAT（RPL-056）：B 侧分量备选落点（数据级，最优先） ---
    row = rows["VBAT"]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    B = (row["bx"], row["by"], list(row["blayers"]))
    comps = bm["mirror"].connectivity("VBAT")
    b_comp = None
    for g in comps:
        for it in g:
            if it == "ZONE":
                continue
            if it.kind == "track" and (it.layers & set(B[2])) and any(
                    G.pt_prim_dist(B[0], B[1], pr) <= 1e-6 for pr in it.prims):
                b_comp = g
                break
        if b_comp:
            break
    if b_comp is None:
        _fail("VBAT B 侧分量未命中")
    descs = [(it.desc, it.layers) for it in b_comp if it != "ZONE"]
    lands = D1.same_net_landings(descs, (A[0], A[1]), (B[0], B[1]),
                                 top_k=5)
    print("VBAT landings: %s" % [(l["kind"], l["x"], l["y"],
                                  l["dist_to_a_mm"]) for l in lands],
          flush=True)
    router = _router(bm)
    for i, ld in enumerate(lands):
        Bl = (ld["x"], ld["y"], list(ld["layers"]))
        steps = _ladder(router, bm, "VBAT", A, Bl,
                        (3.0, 5.0, 8.0, 12.0))
        indep = None
        if any(s["route"]["ok"] for s in steps):
            w = next(s for s in steps if s["route"]["ok"])["route"]
            indep = _independent_check(bm, "VBAT", w, A, Bl)
        variant = {"kind": ld["kind"], "x": ld["x"], "y": ld["y"],
                   "desc": ld["desc"], "dist_to_a_mm": ld["dist_to_a_mm"],
                   "idx": i,
                   "premise": "B 端点改落同网 B 侧连通分量既有铜（via/走线端/"
                              "pad），锁定 PTH 焊盘 J4.20 零改动"}
        results.append(D1.endpoint_variant_row(
            "RPL-056", "VBAT", "B", variant, steps, indep,
            _s1_cert_cut("VBAT")))

    # --- VBAT rim 证据（零裕量退化环带） + A 端 SMD 偏移变体 ---
    cx, cy, r_pad, r_drill = _pth_pad_geometry(bm, "J4", "20")
    mech = D1.pad_lock_mechanism(r_pad, r_drill)
    _rim_trials(bm, "VBAT", "RPL-056", "B", A, B, "J4", "20",
                D1.rim_endpoints(cx, cy, r_pad, r_drill, (0,)), mech,
                r_pad, r_drill,
                "B 端点改落 J4.20 环带内缘（d_min=0.85=r_pad，零裕量退化点，"
                "作为几何证据运行）", (5.0, 8.0), results)
    best_land = lands[0] if lands else None
    u1pads = _pad_index(bm)
    p6 = u1pads.get(("U1", "6"))
    if p6 and best_land:
        offs = D1.smd_endpoint_offsets(p6["x"], p6["y"], 1.5, 0.3,
                                       [(-0.70, 0.0), (-0.70, -0.10),
                                        (0.0, -0.10)])
        Bl = (best_land["x"], best_land["y"], list(best_land["layers"]))
        for off in offs:
            Al = (off["x"], off["y"], list(A[2]))
            steps = _ladder(router, bm, "VBAT", Al, Bl, (5.0, 8.0, 12.0))
            indep = None
            if any(s["route"]["ok"] for s in steps):
                w = next(s for s in steps if s["route"]["ok"])["route"]
                indep = _independent_check(bm, "VBAT", w, Al, Bl)
            results.append(D1.endpoint_variant_row(
                "RPL-056", "VBAT", "A",
                dict(off, kind="smd_pad_offset", pad="U1.6",
                     premise="A 端点在 U1.6 焊盘矩形内偏移（数据级）；B 端="
                             "B 侧分量落点 idx0"),
                steps, indep, _s1_cert_cut("VBAT")))

    # --- SWDIO（RPL-054）：退化环带证据 + J4.13 pad 加大（2.1）+ 环带中带东点 ---
    row = rows["SWDIO"]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    B = (row["bx"], row["by"], list(row["blayers"]))
    cx, cy, r_pad, r_drill = _pth_pad_geometry(bm, "J4", "13")
    mech = D1.pad_lock_mechanism(r_pad, r_drill)
    _rim_trials(bm, "SWDIO", "RPL-054", "A", A, B, "J4", "13",
                D1.rim_endpoints(cx, cy, r_pad, r_drill, (0, 90, 270)), mech,
                r_pad, r_drill,
                "A 端点改落 J4.13 环带内缘（d_min=0.85=r_pad，零裕量退化点）；"
                "同网仅 2 pad（无测试点），A 侧分量=裸焊盘",
                (5.0, 8.0), results)
    new_text, chg = D1.enlarge_pth_pad(base_text, "J4", "13", PAD_ENLARGE_MM)
    tag = "b-swdio-pad13-enlarge"
    stage_dir, stage_sha = _stage_from_text(tag, new_text)
    bm2 = _load_bm(stage_dir)
    cx2, cy2, rp2, rd2 = _pth_pad_geometry(bm2, "J4", "13")
    mech2 = D1.pad_lock_mechanism(rp2, rd2)
    _rim_trials(bm2, "SWDIO", "RPL-054", "A", A, B, "J4", "13",
                D1.rim_endpoints(cx2, cy2, rp2, rd2, (0, 45), d=PAD_ENLARGE_D),
                mech2, rp2, rd2,
                "J4.13 pad 加大至 %g（r_pad=%g）后环带 [%g,%g] 非退化，落点 "
                "d=%g 孔距裕量 %g" % (PAD_ENLARGE_MM, rp2,
                                      mech2["open_annulus"]["d_min"], rp2,
                                      PAD_ENLARGE_D,
                                      round(PAD_ENLARGE_D - rd2
                                            - D1.PTH_HOLE_CLEARANCE
                                            - D1.ROUTE_WIDTH / 2.0, 4)),
                (3.0, 5.0, 8.0, 12.0), results,
                board_change={
                    "kind": "pad_enlarge", "pad": "J4.13",
                    "size_change": chg,
                    "edit_points": ["board 文本 pad 节点 (size)",
                                    "封装库 coreboard.pretty 同步（应用时）",
                                    "邻件间隙复核：J4 pitch 2.54 → pad 间隙 "
                                    "0.44mm（> class clearance 0.2）"],
                    "staged_sha256": stage_sha,
                })
    _progress_note("classb %s staged sha=%s…" % (tag, stage_sha[:8]))

    # --- LTDC_VSYNC（RPL-052）：退化环带证据 + J3.5 pad 加大 + 中带西点 ---
    row = rows["LTDC_VSYNC"]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    B = (row["bx"], row["by"], list(row["blayers"]))
    cx, cy, r_pad, r_drill = _pth_pad_geometry(bm, "J3", "5")
    mech = D1.pad_lock_mechanism(r_pad, r_drill)
    _rim_trials(bm, "LTDC_VSYNC", "RPL-052", "B", A, B, "J3", "5",
                D1.rim_endpoints(cx, cy, r_pad, r_drill, (180, 90, 270)), mech,
                r_pad, r_drill,
                "B 端点改落 J3.5 环带内缘（d_min=0.85=r_pad，零裕量退化点）；"
                "同网仅 2 pad，B 侧分量=裸焊盘",
                (5.0, 8.0), results)
    new_text, chg = D1.enlarge_pth_pad(base_text, "J3", "5", PAD_ENLARGE_MM)
    tag = "b-ltdc-pad5-enlarge"
    stage_dir, stage_sha = _stage_from_text(tag, new_text)
    bm2 = _load_bm(stage_dir)
    cx2, cy2, rp2, rd2 = _pth_pad_geometry(bm2, "J3", "5")
    mech2 = D1.pad_lock_mechanism(rp2, rd2)
    _rim_trials(bm2, "LTDC_VSYNC", "RPL-052", "B", A, B, "J3", "5",
                D1.rim_endpoints(cx2, cy2, rp2, rd2, (180,), d=PAD_ENLARGE_D),
                mech2, rp2, rd2,
                "J3.5 pad 加大至 %g 后环带非退化，落点 d=%g 孔距裕量 %g"
                % (PAD_ENLARGE_MM, PAD_ENLARGE_D,
                   round(PAD_ENLARGE_D - rd2 - D1.PTH_HOLE_CLEARANCE
                         - D1.ROUTE_WIDTH / 2.0, 4)),
                (3.0, 5.0, 8.0, 12.0), results,
                board_change={
                    "kind": "pad_enlarge", "pad": "J3.5",
                    "size_change": chg,
                    "edit_points": ["board 文本 pad 节点 (size)",
                                    "封装库 coreboard.pretty 同步（应用时）",
                                    "邻件间隙复核：J3 pitch 2.54 → pad 间隙 "
                                    "0.44mm（> class clearance 0.2）"],
                    "staged_sha256": stage_sha,
                })
    _progress_note("classb %s staged sha=%s…" % (tag, stage_sha[:8]))

    for i, r in enumerate(results):
        v = r["variant"]
        _write_row("classb_%s_%s_s%s_%s_%d.json"
                   % (r["row_id"], r["net"], r["variant_side"],
                      v.get("kind", "landing"), i), r)
        _progress_note("classb %s %s side=%s variant=%s -> %s"
                       % (r["row_id"], r["net"], r["variant_side"],
                          v.get("kind"), r["design1_status"]))
    print("classb done: %d candidates" % len(results))


# ---- 证书级核证（win1 同款：最优变体端点的板级 UNSAT 证书） ----------------------
def cmd_certify():
    preflight()
    from pcbflow import win1_window
    bm = _load_bm(SNAP_DIR)
    router0 = _router(bm)
    out = []

    def _run(bm_i, net, row_id, A, B, candidate_ref, staged_sha, note):
        r = route_grid.route_one(bm_i, net, A[0], A[1], A[2],
                                 B[0], B[1], B[2])
        bb = bm_i["mirror"].bbox()
        nodes = win1_window.region_nodes(bb, A[0], A[1], B[0], B[1],
                                         win1_window.WIN1_BOARD_MARGIN_MM)
        row = {"net": net, "ax": A[0], "ay": A[1], "bx": B[0], "by": B[1]}
        step = win1_window._cert_step(bm_i, row, r,
                                      win1_window.WIN1_BOARD_MARGIN_MM,
                                      nodes["nodes"])
        step.update({"tier": "board_certify", "window_nodes": nodes["nodes"],
                     "margin_mm": win1_window.WIN1_BOARD_MARGIN_MM,
                     "skipped": False})
        status = step["status"]
        cert = step.get("certificate")
        obj = {
            "row_id": row_id, "net": net,
            "design1_class": "B",
            "candidate_kind": "endpoint_variant_cert",
            "candidate_ref": candidate_ref,
            "variant_endpoints": {"A": [A[0], A[1]], "B": [B[0], B[1]]},
            "design1_status": status,
            "board_sha256": bm_i["pcb_sha256"],
            "staged_board": staged_sha,
            "cert_cut_count": (cert or {}).get("cut_count"),
            "cert_verified": (cert or {}).get("verified"),
            "cert_scope": (cert or {}).get("scope"),
            "unknown_reason": step.get("unknown_reason"),
            "note": note,
            "restricted_declarations": [
                "证书=win1/route_grid 同款 restricted blocking certificate"
                "（0.05mm 格心 4 邻格网+同格位过孔+端点 8 邻辐条，冻结铜，"
                "整板窗）；verified=true 经 verify_cert 独立复核",
                "UNSAT 语义=该变体端点对（A→B′）在冻结板上不可布——该出路"
                "候选被证书否证；UNKNOWN=模型开放（候选通径）或门拒，不自动"
                "改判",
            ],
        }
        _write_row("cert_%s_%s.json" % (row_id, net), obj)
        _progress_note("cert %s %s -> %s cut=%s" % (
            row_id, net, status, obj["cert_cut_count"]))
        out.append(obj)

    # 1) VBAT：最优分量落点（track_end idx0）——快照板
    rows = _target_rows(bm)
    row = rows["VBAT"]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    _run(bm, "VBAT", "RPL-056",
         A, (6.5098, 35.0698, list(row["blayers"])),
         {"kind": "track_end", "xy": [6.5098, 35.0698],
          "source": "B 侧连通分量最近落点（classb idx0）"},
         None, "B′=B 侧分量最近既有铜落点；板级证书核证该数据级出路")

    # 2) SWDIO：pad 加大 staging 板 + 环带中带东点
    stage = os.path.join(STAGING_DIR, "b-swdio-pad13-enlarge")
    if not os.path.exists(os.path.join(stage, BOARD_FILES[0])):
        _fail("缺 staging 板（先跑 classb）")
    bm2 = _load_bm(stage)
    rows2 = _target_rows(bm2)
    row = rows2["SWDIO"]
    B = (row["bx"], row["by"], list(row["blayers"]))
    _run(bm2, "SWDIO", "RPL-054",
         (3.58, 26.11, list(row["alayers"])), B,
         {"kind": "pth_pad_rim_enlarged", "xy": [3.58, 26.11],
          "pad": "J4.13", "d": 0.95, "r_pad": 1.05},
         bm2["pcb_sha256"], "J4.13 pad 加大至 2.1 后环带中带东点；板级证书核证")

    # 3) LTDC_VSYNC：pad 加大 staging 板 + 环带中带西点
    stage = os.path.join(STAGING_DIR, "b-ltdc-pad5-enlarge")
    if not os.path.exists(os.path.join(stage, BOARD_FILES[0])):
        _fail("缺 staging 板（先跑 classb）")
    bm2 = _load_bm(stage)
    rows2 = _target_rows(bm2)
    row = rows2["LTDC_VSYNC"]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    _run(bm2, "LTDC_VSYNC", "RPL-052",
         A, (63.28, 21.95, list(row["blayers"])),
         {"kind": "pth_pad_rim_enlarged", "xy": [63.28, 21.95],
          "pad": "J3.5", "d": 0.95, "r_pad": 1.05},
         bm2["pcb_sha256"], "J3.5 pad 加大至 2.1 后环带中带西点；板级证书核证")

    print("certify done: %d" % len(out))


# ---- 类 A：U1 移位 / 口袋墙剥除 ---------------------------------------------------
def _stage_from_text(tag, board_text):
    d = os.path.join(STAGING_DIR, tag)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, BOARD_FILES[0])
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(board_text)
    shutil.copy2(os.path.join(SNAP_DIR, BOARD_FILES[1]),
                 os.path.join(d, BOARD_FILES[1]))
    return d, hashing.sha256_file(dst)


def _solve_on(bm2, net, router2, ladder):
    row = _target_rows(bm2)[net]
    A = (row["ax"], row["ay"], list(row["alayers"]))
    B = (row["bx"], row["by"], list(row["blayers"]))
    steps = _ladder(router2, bm2, net, A, B, ladder)
    indep = None
    if any(s["route"]["ok"] for s in steps):
        w = next(s for s in steps if s["route"]["ok"])["route"]
        indep = _independent_check(bm2, net, w, A, B)
    return steps, indep, (A, B)


def cmd_classa():
    preflight()
    from pcbflow import win1_window
    bm = _load_bm(SNAP_DIR)
    with open(os.path.join(SNAP_DIR, BOARD_FILES[0]), encoding="utf-8",
              newline="") as f:
        base_text = f.read()
    tracks, vias = _collect_copper(bm)
    u1_xy = P2.footprint_at(base_text, "U1")
    results = []

    # U1 pad bbox 与邻件间隙（爆炸半径约束核算）
    G = bm["pa"]["geometry"]
    pad_idx = _pad_index(bm)

    def bbox_of(ref):
        xs, ys = [], []
        for (r, n), p in pad_idx.items():
            if r == ref:
                for pr in p["prims"]:
                    pb = G.prim_bbox(pr)
                    xs += [pb[0], pb[2]]
                    ys += [pb[1], pb[3]]
        return [round(min(xs), 4), round(min(ys), 4),
                round(max(xs), 4), round(max(ys), 4)]
    b_u1 = bbox_of("U1")
    neighbors = {r: bbox_of(r) for r in ("U2", "C4", "C5")}
    gap_checks = {}
    for cand in D1.u1_shift_candidates(u1_xy):
        gap_checks[cand["label"]] = {
            r: D1.shift_gap_after(b_u1, bb, cand["dx"], cand["dy"])
            for r, bb in neighbors.items()}

    # U1 账单（爆炸半径）
    u1_pads = [p for (r, n), p in pad_idx.items() if r == "U1"]
    bill = P2.disturbance_bill("U1", u1_pads, tracks, vias, "NONE_TARGET",
                               G.pt_prim_dist)
    bill_summary = D1.blast_radius_summary(bill, "U1")

    # A1：U1 整移（纯移位，铜冻结——诚实呈现"移位不解锁"或解锁）
    def _cert_or_unknown(bm_i, net, A, B):
        """窗梯无 witness 时的板级证书分类（certified 不可布 vs 模型开放）。"""
        r = route_grid.route_one(bm_i, net, A[0], A[1], A[2],
                                 B[0], B[1], B[2])
        bb = bm_i["mirror"].bbox()
        nodes = win1_window.region_nodes(bb, A[0], A[1], B[0], B[1],
                                         win1_window.WIN1_BOARD_MARGIN_MM)
        row = {"net": net, "ax": A[0], "ay": A[1], "bx": B[0], "by": B[1]}
        return win1_window._cert_step(bm_i, row, r,
                                      win1_window.WIN1_BOARD_MARGIN_MM,
                                      nodes["nodes"]), nodes["nodes"]

    for cand in D1.u1_shift_candidates(u1_xy):
        moved = P2.move_footprint(base_text, "U1", cand["dx"], cand["dy"])
        tag = "a1-%s" % cand["label"]
        stage_dir, stage_sha = _stage_from_text(tag, moved)
        bm2 = _load_bm(stage_dir)
        router2 = _router(bm2)
        for net in ("FMC_SDNE0", "GNDA"):
            row_n = _target_rows(bm2)[net]
            A = (row_n["ax"], row_n["ay"], list(row_n["alayers"]))
            B = (row_n["bx"], row_n["by"], list(row_n["blayers"]))
            steps = _ladder(router2, bm2, net, A, B,
                            D1.VARIANT_MARGIN_LADDER_SHORT)
            indep = None
            cert_note = None
            if any(s["route"]["ok"] for s in steps):
                w = next(s for s in steps if s["route"]["ok"])["route"]
                indep = _independent_check(bm2, net, w, A, B)
            else:
                cstep, cnodes = _cert_or_unknown(bm2, net, A, B)
                cert_note = {"tier": cstep["status"], "cut": (cstep.get(
                    "certificate") or {}).get("cut_count"),
                    "verified": (cstep.get("certificate") or {}).get(
                        "verified"), "window_nodes": cnodes,
                    "unknown_reason": cstep.get("unknown_reason")}
            obj = D1.shift_or_strip_row(
                D1.TARGET_ROWS[net], net, "u1_shift", cand, steps, indep,
                _s1_cert_cut(net),
                dict(bill_summary, gap_checks=gap_checks.get(cand["label"]),
                     staged_sha256=stage_sha),
                D1.ENGINEERING_LAYOUT)
            obj["board_cert_after_change"] = cert_note
            results.append(obj)
        _progress_note("a1 %s staged sha=%s… solved 2 nets" % (tag,
                                                               stage_sha[:8]))

    # A2：口袋墙 surgical strip（R∈{1.5, 2.5}；protect 已收网；剥后仍无
    # witness 时给板级证书分类）
    pockets = (("FMC_SDNE0", 22.325, 33.65), ("GNDA", 22.325, 30.15))
    for net, px, py in pockets:
        for radius in (1.5, 2.5):
            wall = D1.pocket_wall(tracks, vias, px, py, radius,
                                  exclude_nets={net},
                                  protect_nets=set(D1.APPLIED_NETS))
            stripped_text, cnt = P2.strip_copper(base_text, wall["segments"],
                                                 wall["vias"])
            tag = "a2-strip-%s-r%g" % (net, radius)
            stage_dir, stage_sha = _stage_from_text(tag, stripped_text)
            bm2 = _load_bm(stage_dir)
            router2 = _router(bm2)
            row_n = _target_rows(bm2)[net]
            A = (row_n["ax"], row_n["ay"], list(row_n["alayers"]))
            B = (row_n["bx"], row_n["by"], list(row_n["blayers"]))
            steps = _ladder(router2, bm2, net, A, B,
                            (3.0, 5.0, 8.0, 12.0))
            indep = None
            cert_note = None
            if any(s["route"]["ok"] for s in steps):
                w = next(s for s in steps if s["route"]["ok"])["route"]
                indep = _independent_check(bm2, net, w, A, B)
            else:
                cstep, cnodes = _cert_or_unknown(bm2, net, A, B)
                cert_note = {"tier": cstep["status"], "cut": (cstep.get(
                    "certificate") or {}).get("cut_count"),
                    "verified": (cstep.get("certificate") or {}).get(
                        "verified"), "window_nodes": cnodes,
                    "unknown_reason": cstep.get("unknown_reason")}
            wall_bill = {
                "stripped": cnt,
                "net_histogram": wall["net_histogram"],
                "protected_hits": wall["protected_hits"],
                "radius_mm": radius,
                "obligation": "剥除段所属网在 U1 各自焊盘处新增断点，需重布"
                              "（重布可行性本包未验证，如实申报）",
            }
            obj = D1.shift_or_strip_row(
                D1.TARGET_ROWS[net], net, "pocket_wall_strip",
                {"pocket": [px, py], "radius_mm": radius,
                 "protect_nets": list(D1.APPLIED_NETS)}, steps, indep,
                _s1_cert_cut(net), wall_bill, D1.ENGINEERING_BOARD)
            obj["board_cert_after_change"] = cert_note
            results.append(obj)
            _progress_note("a2 %s stripped=%s staged sha=%s… -> %s%s"
                           % (tag, cnt, stage_sha[:8],
                              obj["design1_status"],
                              "" if not cert_note else
                              " cert=%s cut=%s" % (cert_note["tier"],
                                                   cert_note["cut"])))

    for i, r in enumerate(results):
        label = ""
        ch = r.get("change") or {}
        if isinstance(ch, dict):
            label = str(ch.get("label") or ch.get("radius_mm") or "")
        _write_row("classa_%s_%s_%s_%s_%d.json"
                   % (r["row_id"], r["net"], r["candidate_kind"], label, i), r)
    print("classa done: %d candidates" % len(results))


def _pad_index(bm):
    """镜像 pad CopperItem → {(ref, number): {net, prims, x, y}}（缓存）。"""
    key = "_design1_pad_index"
    if key in bm:
        return bm[key]
    G = bm["pa"]["geometry"]
    idx = {}
    for L in bm["pa"]["LAYERS"]:
        for it in bm["mirror"].query_copper(L, -1000, -1000, 1000, 1000):
            if it.kind != "pad":
                continue
            g = P2.parse_item_desc(it.desc)
            if not g:
                continue
            k = (g["ref"], g["number"])
            if k not in idx:
                idx[k] = {"number": g["number"], "net": g["net"],
                          "x": g["x"], "y": g["y"], "prims": it.prims}
    bm[key] = idx
    return idx


# ---- 汇总 -----------------------------------------------------------------------
def cmd_assemble():
    live_sha = preflight()
    rows = []
    for name in sorted(os.listdir(ROWS_DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(ROWS_DIR, name), encoding="utf-8") as f:
            rows.append(json.load(f))
    if not rows:
        _fail("无候选行（先跑 classb/classa）")
    matrix = D1.decision_matrix(rows)
    view = D1.matrix_view(matrix)

    waivers = [
        D1.waiver_row(
            "RPL-054", "SWDIO",
            "out/coreboard-live2b-s1/rows/RPL-054_SWDIO.json"
            "（端点自锁割 8：J4.13 PTH 焊盘 drill d=1.0 八邻辐条全层封闭）",
            "调试口 SWDIO 暂不经排针 J4 引出：调试时改用杜邦/夹具从 U1.124 "
            "或 J4.13 环带临时飞线；或批准类 B 环带端点变体落线",
            "制造成本 0；板功能不受制造影响",
            "J4 排针上的 SWDIO 针不可用（SWD 调试需临时飞线）；"
            "U1 固件烧写/调试流程受影响",
            "任一类 B 端点变体（RPL-054 环带）获 witness 并批准落线"),
        D1.waiver_row(
            "RPL-052", "LTDC_VSYNC",
            "out/coreboard-live2b-s1/rows/RPL-052_LTDC_VSYNC.json"
            "（board 割 3088 + B 端 J3.5 PTH 自锁割 8）",
            "LCD 接口 VSYNC 暂缺：仅影响使用 LCD 的场景；核心板作为非显示"
            "用途时可接受；或批准类 B 环带端点变体落线",
            "制造成本 0",
            "J3 LCD 排针 VSYNC 针无效——LCD 时序无法正常工作（其余 LCD 信"
            "号不受影响）；非显示应用无影响",
            "任一类 B 端点变体（RPL-052 环带）获 witness 并批准落线"),
        D1.waiver_row(
            "RPL-056", "VBAT",
            "out/coreboard-live2b-s1/rows/RPL-056_VBAT.json"
            "（board 割 300864 + B 端 J4.20 PTH 自锁割 8）",
            "电池馈电经 R9/CRTC 既有铜在板内连通（B 侧分量含 R9.2/CRTC.1/"
            "via），仅 J4.20 针未连；不用电池背电时可接受；或批准类 B 备选"
            "落点变体落线",
            "制造成本 0",
            "J4.20 电池馈电针无效——RTC/备份域掉电数据丢失（主电源供电时 "
            "VBAT 域仍经板内铜得电，功能影响限于电池切换场景）",
            "任一类 B 备选落点变体（RPL-056）获 witness 并批准落线"),
        D1.waiver_row(
            "RPL-038", "FMC_SDNE0",
            "out/coreboard-live2b-s1/rows/RPL-038_FMC_SDNE0.json"
            "（board 割 591；口袋=A 端 U1.44 被 U1 引脚场围死）",
            "SDRAM 片选 0 缺失：SDRAM 不可用场景才可接受（核心板多数应用"
            "依赖 SDRAM）——默认不接受，除非产品确认无 SDRAM 需求",
            "制造成本 0",
            "SDRAM（U2）不能使能——依赖外部 RAM 的应用全失效",
            "类 A 口袋墙剥除/U1 扇出重排候选获 witness 并批准落线"),
        D1.waiver_row(
            "RPL-039", "GNDA",
            "out/coreboard-live2b-s1/rows/RPL-039_GNDA.json"
            "（board 割 301004；口袋=B 端 U1.37 被 U1 引脚场围死）",
            "模拟地独立回流断开：ADC 精度场景受影响；或批准类 A 剥除候选"
            "（注意 3V3 受保护段豁免后是否仍可解）",
            "制造成本 0",
            "U1.37 模拟地引脚未回 GNDA 网——VDDA/模拟域回流路径劣化，"
            "ADC 采样噪声/精度风险上升（不影响数字功能）",
            "类 A 口袋墙剥除候选获 witness 并批准落线"),
    ]

    fs_diff = None
    fs_pre = os.path.join(OUT_DIR, "failure-set-startwork.json")
    fs_post = os.path.join(OUT_DIR, "failure-set-endwork.json")
    if os.path.exists(fs_pre) and os.path.exists(fs_post):
        with open(fs_pre, encoding="utf-8") as f:
            pre = json.load(f)
        with open(fs_post, encoding="utf-8") as f:
            post = json.load(f)
        fs_diff = L2S1.failure_set_diff(pre["ids"], post["ids"])
        fs_diff["pre_count"] = pre["count"]
        fs_diff["post_count"] = post["count"]

    live_after = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if live_after != live_sha:
        _fail("收工核对：live 板 sha 变了")
    snap_after = hashing.sha256_file(os.path.join(SNAP_DIR, BOARD_FILES[0]))

    # staging DRC 摘要（kicad-cli 由 Bash 仅在副本执行；无 drc.json 记 None）
    drc = {}
    for tag in ("t0-design1-baseline", "a2-gnda-r1.5-witness",
                "a2-fmc-r1.5-witness"):
        p = os.path.join(STAGING_DIR, tag, "drc.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                o = json.load(f)
            drc[tag] = {"violations": len(o.get("violations", [])),
                        "unconnected_items": len(o.get("unconnected_items",
                                                       []))}
        else:
            drc[tag] = None

    prl = [os.path.relpath(os.path.join(dp, fn), OUT_DIR)
           for dp, _dn, fns in os.walk(OUT_DIR) for fn in fns
           if fn.endswith(".kicad_prl")]
    obj = {
        "schema_version": D1.DESIGN1_SCHEMA,
        "artifact_kind": D1.DESIGN1_ARTIFACT_KIND,
        "dataset": D1.DESIGN1_DATASET,
        "date": D1.DESIGN1_DATE,
        "live_board_sha256": live_after,
        "snapshot_unchanged": snap_after == live_sha,
        "counts": {
            "candidates": len(rows),
            "SAT": sum(1 for r in rows if r["design1_status"] == "SAT"),
            "UNKNOWN": sum(1 for r in rows
                           if r["design1_status"] == "UNKNOWN"),
            "UNSAT": sum(1 for r in rows if r["design1_status"] == "UNSAT"),
        },
        "decision_matrix": view,
        "waiver_ledger": waivers,
        "drc_staging": drc,
        "gates": {"failure_set_diff": fs_diff},
        "guards": {
            "live_board_unchanged": live_after == live_sha,
            "kicad_prl_files_in_out": prl,
            "cli_py_dependency": "none",
            "route_grid_change": "none",
            "datasets_dir_writes": "none",
        },
        "note": "DESIGN-1 核心产物（canonical，无 wall-clock）；逐候选证据见 "
                "rows/*.json；本包零写 live，一切提案待用户拍板",
    }
    sha = _write_canonical(os.path.join(OUT_DIR, "design1-results.json"), obj)
    print("design1-results.json sha=%s… counts=%s" % (sha[:8], obj["counts"]),
          flush=True)
    _progress_note("assemble ok: %s" % obj["counts"])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "assemble"
    if cmd == "classb":
        cmd_classb()
    elif cmd == "certify":
        cmd_certify()
    elif cmd == "classa":
        cmd_classa()
    elif cmd == "assemble":
        cmd_assemble()
    else:
        _fail("未知子命令 %s" % cmd)


if __name__ == "__main__":
    main()
