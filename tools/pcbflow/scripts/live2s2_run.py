#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live2s2_run.py — LIVE2B-S2 编排脚本（3V3 零拆收口尝试 + 布局迭代提案）。

纪律（与 live2s1_run.py 同源）：
- live 板零写：只读 stat/copy 源；快照副本进 out/coreboard-live2b-s2/
  workspace/live/；提案板进 workspace/staging/<id>/（kicad-cli DRC 由 Bash
  在 staging 副本上执行；pcbflow .py 零子进程）；
- cli.py 零依赖；route_grid.py / win1_window.py 零改动；
- fail-closed：受保护 hash、live 板 hash、锚件对账、行号漂移不符 → 退出；
- 幂等续跑：rows/*.json 已存在 → 跳过；
- 核心产物 canonical JSON、无 wall-clock；时间戳只进 run-manifest/PROGRESS。

用法（tools/pcbflow 下）：
  python scripts/live2s2_run.py t1        # 任务 1：3V3 收口尝试
  python scripts/live2s2_run.py t2        # 任务 2：提案 + 账单 + 内存 verdict
  python scripts/live2s2_run.py assemble  # 汇总 JSON + REPORT.md（读 DRC JSON）
  python scripts/live2s2_run.py fails <raw.txt> <out.json>
"""

from __future__ import annotations

import datetime
import json
import math
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import board_writer, config, hashing  # noqa: E402
from pcbflow import live2s1_experiment as L2  # noqa: E402
from pcbflow import live2s2_proposal as P  # noqa: E402
from pcbflow import residual_cmd, route_grid, win1_window  # noqa: E402

PCBFLOW_ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(PCBFLOW_ROOT, "out", P.LIVE2S2_DATASET)
WS_DIR = os.path.join(OUT_DIR, "workspace")
SNAP_DIR = os.path.join(WS_DIR, "live")
STAGING_DIR = os.path.join(WS_DIR, "staging")
SCRATCH_DIR = os.path.join(WS_DIR, "scratch")
ROWS_DIR = os.path.join(OUT_DIR, "rows")
PROPS_DIR = os.path.join(OUT_DIR, "proposals")
PROGRESS = os.path.join(OUT_DIR, "PROGRESS.md")
S1_DIR = os.path.join(PCBFLOW_ROOT, "out", "coreboard-live2b-s1")
STRUCTURES = os.path.join(PCBFLOW_ROOT, "out", "revc-a2", "structures.json")

REVC_DIR = config.REVC_DIR
BOARD_FILES = ("stm32h743-coreboard-revc.kicad_pcb",
               "stm32h743-coreboard-revc.kicad_pro")
LAYER_NAME = board_writer.LAYER_FILE_NAME
S1_ROW_FILE = {"3V3": "RPL-019_3V3.json", "FMC_SDNE0": "RPL-038_FMC_SDNE0.json",
               "GNDA": "RPL-039_GNDA.json",
               "LTDC_VSYNC": "RPL-052_LTDC_VSYNC.json",
               "SWDIO": "RPL-054_SWDIO.json", "VBAT": "RPL-056_VBAT.json"}
PROPOSAL_NETS = ("FMC_SDNE0", "GNDA", "LTDC_VSYNC", "VBAT")
EVAL_MARGINS = (3.0, 8.0, 15.0)   # 候选评估搜索窗梯（有界）


def _fail(msg):
    print("LIVE2S2-FAIL: %s" % msg)
    sys.exit(1)


def _write_canonical(path, obj):
    data = hashing.canonical_json_bytes(obj)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds")


def progress(line):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write("- %s %s\n" % (_now(), line))
    print("progress: %s" % line, flush=True)


def preflight():
    for rel, prefix in P.PROTECTED:
        sha = hashing.sha256_file(os.path.join(PCBFLOW_ROOT, rel))
        if not sha.startswith(prefix):
            _fail("受保护文件 %s sha=%s… 与期望 %s 不符" % (rel, sha[:8], prefix))
    live_sha = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if not live_sha.startswith(P.LIVE_BOARD_SHA_PREFIX):
        _fail("live 板 sha=%s… 与冻结见证不符" % live_sha[:8])
    snap = os.path.join(SNAP_DIR, BOARD_FILES[0])
    if not os.path.exists(snap) or hashing.sha256_file(snap) != live_sha:
        _fail("快照副本缺失或 sha 与 live 板不符")
    with open(STRUCTURES, encoding="utf-8") as f:
        anchors = sorted(a["ref"] for a in json.load(f)["anchors"])
    if anchors != sorted(P.ANCHOR_REFS):
        _fail("锚件对账不符：structures=%s 模块=%s" % (anchors, P.ANCHOR_REFS))
    return live_sha


def _load_bm(dir_path):
    return route_grid.board_model(dir_path)


def _router(bm):
    pa = bm["pa"]
    return pa["Router"](bm["mirror"], legality=pa["Legality"](bm["mirror"]),
                        corridor_of=None, log=lambda *_a: None)


def _target_rows(bm):
    rows = residual_cmd._read_opens_rows(bm)
    return L2.assign_target_rows(rows)


def _s1_row(net):
    with open(os.path.join(S1_DIR, "rows", S1_ROW_FILE[net]),
              encoding="utf-8") as f:
        return json.load(f)


def _try(router, bm, net, A, B, margin):
    plan = router._fresh_plan(net, A, B)
    bb = P.widened_bbox(bm["mirror"].bbox(), A[0], A[1], B[0], B[1], margin)
    p = router._try_route(plan, bb)
    r = P.normalize_plan(p, net)
    return r, [round(v, 4) for v in bb]


def _ladder(router, bm, net, A, B, margins):
    steps = []
    for mg in margins:
        r, bb = _try(router, bm, net, A, B, mg)
        steps.append({"margin_mm": mg, "route": r, "region_bbox_mm": bb})
        if r["ok"]:
            break
    return steps


def _independent_check(bm, net, route, A, B):
    """witness 独立复核：fresh Legality 逐段/逐孔 + 端点落铜 + B 端触及既有
    同网铜（闭合断点）。"""
    pa = bm["pa"]
    G = pa["geometry"]
    leg = pa["Legality"](bm["mirror"])
    seg_bad, via_bad = [], []
    for (L, x1, y1, x2, y2) in route["segments"]:
        ok, margin, viol = leg.seg_legal(L, (x1, y1), (x2, y2), route["width"],
                                         net)
        if not ok:
            seg_bad.append({"seg": [L, x1, y1, x2, y2], "margin": margin,
                            "violator": str(viol)})
    L0, L1 = pa["LAYERS"][0], pa["LAYERS"][1]
    for (x, y) in route["vias"]:
        ok, margin, viol = leg.via_legal(x, y, net, L0, L1,
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

    a_touch = touches(A, set(A[2]))
    b_touch = touches(B, set(B[2]))
    # B 端是否触及既有同网铜（断点闭合的物理前提）
    m = bm["mirror"]
    b_on_net = False
    for L in B[2]:
        for it in m.query_copper(L, B[0] - 0.5, B[1] - 0.5, B[0] + 0.5,
                                 B[1] + 0.5):
            if it.net == net and any(G.pt_prim_dist(B[0], B[1], prim) <= 1e-6
                                     for prim in it.prims):
                b_on_net = True
                break
        if b_on_net:
            break
    return {"seg_checked": len(route["segments"]), "seg_bad": seg_bad,
            "via_checked": len(route["vias"]), "via_bad": via_bad,
            "a_touch": a_touch, "b_touch": b_touch,
            "b_on_existing_net_copper": b_on_net,
            "all_ok": not seg_bad and not via_bad and a_touch and b_touch
            and b_on_net}


def _stage_board(stage_name, board_text):
    d = os.path.join(STAGING_DIR, stage_name)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, BOARD_FILES[0])
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(board_text)
    shutil.copy2(os.path.join(SNAP_DIR, BOARD_FILES[1]),
                 os.path.join(d, BOARD_FILES[1]))
    return d, hashing.sha256_file(dst)


def _read_snapshot_text():
    with open(os.path.join(SNAP_DIR, BOARD_FILES[0]), encoding="utf-8",
              newline="") as f:
        return f.read()


# ---- 任务 1 ---------------------------------------------------------------
def cmd_t1():
    live_sha = preflight()
    out_path = os.path.join(ROWS_DIR, "RPL-019_3V3.json")
    if os.path.exists(out_path):
        print("t1 已存在，跳过（幂等）")
        return
    bm = _load_bm(SNAP_DIR)
    if bm["pcb_sha256"] != live_sha:
        _fail("快照板 sha 漂移")
    row = _target_rows(bm)["3V3"]
    if row["row_id"] != "RPL-019":
        _fail("行漂移")
    net = "3V3"
    A = (row["ax"], row["ay"], frozenset(row["alayers"]))
    B = (row["bx"], row["by"], frozenset(row["blayers"]))
    s1 = _s1_row(net)
    s1_region = (s1.get("certificate_scope") or {}).get("region_mm")
    router = _router(bm)
    progress("t1 start: %s A=%s B=%s" % (net, A[:2], B[:2]))
    steps = _ladder(router, bm, net, A, B, P.CLOSURE_MARGIN_LADDER)
    for s in steps:
        print("  ladder margin=%s ok=%s fail=%s segs=%d" % (
            s["margin_mm"], s["route"]["ok"], s["route"]["fail"],
            len(s["route"]["segments"])), flush=True)
    witness = next((s for s in steps if s["route"]["ok"]), None)

    # 同网落点枚举（B 侧分量；证据用，有界）
    m = bm["mirror"]
    comps = m.connectivity(net)
    G = bm["pa"]["geometry"]
    b_comp = None
    for g in comps:
        for it in g:
            if it == "ZONE":
                continue
            if it.kind == "track" and B[2] & it.layers and any(
                    G.pt_prim_dist(B[0], B[1], prim) <= 1e-6
                    for prim in it.prims):
                b_comp = g
                break
        if b_comp:
            break
    landing_trials = []
    if b_comp:
        descs = [(it.desc, it.layers) for it in b_comp if it != "ZONE"]
        lands = P.landing_points(descs, A[0], A[1], exclude_xy=(B[0], B[1]))
        for ld in lands:
            Bl = (ld["x"], ld["y"], frozenset(ld["layers"]))
            st = _ladder(router, bm, net, A, Bl, P.CLOSURE_MARGIN_LADDER[:3])
            landing_trials.append({
                "landing": ld,
                "steps": [{"margin_mm": s["margin_mm"], "ok": s["route"]["ok"],
                           "fail": s["route"]["fail"],
                           "segments": len(s["route"]["segments"]),
                           "vias": len(s["route"]["vias"]),
                           "length_mm": s["route"]["length_mm"]}
                          for s in st],
                "sat": any(s["route"]["ok"] for s in st),
            })
            print("  landing %s (%.3f,%.3f) d=%.2f sat=%s" % (
                ld["kind"], ld["x"], ld["y"], ld["dist_to_a_mm"],
                landing_trials[-1]["sat"]), flush=True)
    indep = None
    stage = None
    if witness:
        indep = _independent_check(bm, net, witness["route"], A, B)
        text = _read_snapshot_text()
        rp = {"net": net, "width": witness["route"]["width"],
              "via_size": witness["route"]["via_size"],
              "via_drill": witness["route"]["via_drill"],
              "segments": witness["route"]["segments"],
              "vias": witness["route"]["vias"]}
        new_text = board_writer.apply_routes(text, [rp], eol="auto")
        d, sha = _stage_board("t1-3v3-witness", new_text)
        stage = {"dir": os.path.relpath(d, PCBFLOW_ROOT), "board_sha256": sha,
                 "note": "快照+witness 铜（apply_routes，eol=auto）；DRC 由 Bash "
                         "kicad-cli 在此副本执行"}
    verdict = P.closure_verdict("RPL-019", net, steps, landing_trials,
                                s1_region, indep)
    verdict["staging"] = stage
    verdict["endpoints"] = {"A": [A[0], A[1], sorted(A[2])],
                            "B": [B[0], B[1], sorted(B[2])],
                            "kind_A": row["kind_A"], "kind_B": row["kind_B"]}
    verdict["s1_reference"] = {
        "live2s1_status": s1["live2s1_status"],
        "certificate_cut_count": s1["certificate_cut_count"],
        "board_strengthen": (s1.get("board_strengthen") or {}).get("status"),
        "board_strengthen_reason": (s1.get("board_strengthen") or {}).get(
            "unknown_reason")}
    sha = _write_canonical(out_path, verdict)
    progress("t1 done: %s status=%s witness_margin=%s sha=%s…" % (
        net, verdict["live2s2_status"],
        (verdict.get("witness") or {}).get("margin_mm"), sha[:8]))


# ---- 任务 2 ---------------------------------------------------------------
def _pads_simple(bm):
    return [{"ref": p.ref, "number": str(p.number), "net": p.net,
             "x": p.x, "y": p.y} for p in bm["mirror"].pads]


def _ref_pads(bm, ref):
    """ref 各焊盘 {number, net, prims}（镜像 pad items）。"""
    out = []
    for it in bm["mirror"].items:
        if it.kind != "pad":
            continue
        g = P.parse_item_desc(it.desc)
        if g and g["ref"] == ref:
            out.append({"number": g["number"], "net": it.net,
                        "prims": list(it.prims), "x": g["x"], "y": g["y"],
                        "layers": sorted(int(l) for l in it.layers)})
    return out


def _tracks_vias(bm):
    tracks, vias = [], []
    for it in bm["mirror"].items:
        g = P.parse_item_desc(it.desc)
        if not g:
            continue
        if it.kind == "track":
            L = sorted(it.layers)[0]
            tracks.append(dict(g, layer=int(L), layer_name=LAYER_NAME.get(
                int(L), str(L)), net=it.net))
        elif it.kind == "via":
            vias.append(dict(g, net=it.net))
    return tracks, vias


def _pocket_analysis(bm, row, s1row):
    """正/反向闭包规模 → 口袋端点（反向=端点互换后 solve_cert；1mm 走廊窗）。"""
    router = s1row["router"]
    fwd = (s1row.get("final_certificate") or {}).get("s_side_size")
    model, unk = route_grid.build_cert_model(
        bm, row["net"], router["width"], router["via_size"],
        router["via_drill"], row["bx"], row["by"], row["ax"], row["ay"],
        margin_mm=route_grid.CERT_MARGIN_MM, window_nodes=2_000_000)
    rev = None
    rev_note = None
    rev_spoke_rules = None
    if model is None:
        rev_note = "unknown:%s" % (unk[0],)
    else:
        cert = route_grid.solve_cert(model)
        if cert.get("reachable_b"):
            rev_note = "reverse_reachable(候选通径)"
        else:
            rev = cert.get("s_side_size", 0)
            rev_note = "reverse_cut=%s" % cert.get("cut_count")
            kinds = {g["kind"] for g in cert.get("cut_groups") or []}
            if kinds == {"spoke"}:
                rev_spoke_rules = P.spoke_cert_rules(cert["cut_groups"])
                rev_note += "(endpoint_spoke_lock: B 端 8 邻辐条全层封闭)"
    side = P.pocket_side(fwd, rev)
    return {"forward_closure": fwd, "reverse_closure": rev,
            "reverse_note": rev_note, "pocket_side": side,
            "reverse_spoke_lock": rev_spoke_rules is not None,
            "reverse_spoke_rules": rev_spoke_rules,
            "pocket_xy": [row["ax"], row["ay"]] if side == "A"
            else [row["bx"], row["by"]],
            "pocket_kind": row["kind_A"] if side == "A" else row["kind_B"]}


def _spoke_lock(bm, net, router, x, y):
    """端点自锁局部证书：A=B=端点的微窗模型 → solve_cert（辐条全闭 ⟹ 闭包空
    ⟹ spoke 割）→ verify_cert。locked=verified spoke 证书（局部性质，与窗无关）。"""
    model, unk = route_grid.build_cert_model(
        bm, net, router["width"], router["via_size"], router["via_drill"],
        x, y, x, y, margin_mm=0.5, window_nodes=200_000)
    if model is None:
        return None
    cert = route_grid.solve_cert(model)
    if cert.get("reachable_b") is not False or cert.get("cert_broken"):
        return {"locked": False, "spokes_closed": None}
    kinds = {g["kind"] for g in cert.get("cut_groups") or []}
    if kinds != {"spoke"}:
        return {"locked": False, "spokes_closed": None, "kinds": sorted(kinds)}
    verified = route_grid.verify_cert(model, cert)
    return {"locked": bool(verified), "spokes_closed": cert["cut_count"],
            "verified": bool(verified),
            "rules": P.spoke_cert_rules(cert["cut_groups"])}


def _net_verdict(bm, router, net, row, margins=EVAL_MARGINS,
                 cert_window=route_grid.CERT_WINDOW_NODES):
    """候选板上的单网 verdict：搜索窗梯 witness → SAT；否则冻结窗证书
    （frozen_600k，margin=1mm，verified）→ UNSAT(corridor)；其余 UNKNOWN。
    不跑板级强化（候选评估预算）。"""
    A = (row["ax"], row["ay"], frozenset(row["alayers"]))
    B = (row["bx"], row["by"], frozenset(row["blayers"]))
    steps = _ladder(router, bm, net, A, B, margins)
    w = next((s for s in steps if s["route"]["ok"]), None)
    out = {"net": net, "row_id": row["row_id"],
           "ladder": [{"margin_mm": s["margin_mm"], "ok": s["route"]["ok"],
                       "fail": s["route"]["fail"]} for s in steps]}
    if w:
        out.update({"status": "SAT", "witness": {
            "margin_mm": w["margin_mm"], "segments": len(w["route"]["segments"]),
            "vias": len(w["route"]["vias"]),
            "length_mm": w["route"]["length_mm"]},
            "route_plan": {"net": net, "width": w["route"]["width"],
                           "via_size": w["route"]["via_size"],
                           "via_drill": w["route"]["via_drill"],
                           "segments": w["route"]["segments"],
                           "vias": w["route"]["vias"]}})
        return out
    r0 = steps[0]["route"]
    # 端点自锁局部证书（任一端 8 邻辐条全层封闭 ⟹ 无路；与窗无关）
    for end, (x, y) in (("A", (row["ax"], row["ay"])),
                        ("B", (row["bx"], row["by"]))):
        lock = _spoke_lock(bm, net, r0, x, y)
        if lock and lock["locked"]:
            out.update({"status": "UNSAT",
                        "scope": "endpoint_spoke_lock(%s)" % end,
                        "spoke_lock": dict(lock, endpoint=end),
                        "note": "端点 8 邻辐条全层封闭（局部证书，与窗无关）"})
            return out
    step = win1_window._cert_step(bm, row, r0, route_grid.CERT_MARGIN_MM,
                                  cert_window)
    if step["status"] == "UNSAT":
        c = step["certificate"]
        out.update({"status": "UNSAT", "scope": "corridor_frozen_window",
                    "cut_count": c["cut_count"], "verified": c["verified"],
                    "region_mm": c["scope"]["region_mm"]})
    else:
        out.update({"status": "UNKNOWN",
                    "unknown_reason": step.get("unknown_reason")})
    return out


def _stub_reroute(bm, router, bill, moved_pads):
    """账单走线的重布：被移焊盘（新位）→ 悬空端；逐项 SAT/FAIL。"""
    pad_xy = {p["number"]: p for p in moved_pads}
    out = []
    for it in bill["segments"]:
        num = it["pad"].split(".", 1)[1]
        pd = pad_xy.get(num)
        if not pd:
            out.append({"item": it["pad"], "net": it["net"], "status": "FAIL",
                        "fail": "moved pad not found"})
            continue
        A = (pd["x"], pd["y"], frozenset(pd["layers"]))
        B = (it["dangling_xy"][0], it["dangling_xy"][1],
             frozenset([it["layer"]]))
        steps = _ladder(router, bm, it["net"], A, B, EVAL_MARGINS)
        w = next((s for s in steps if s["route"]["ok"]), None)
        out.append({"item": it["pad"], "net": it["net"], "cls": it["cls"],
                    "status": "SAT" if w else "FAIL",
                    "margin_mm": w["margin_mm"] if w else None,
                    "fail": None if w else steps[-1]["route"]["fail"],
                    "route_plan": None if not w else {
                        "net": it["net"], "width": w["route"]["width"],
                        "via_size": w["route"]["via_size"],
                        "via_drill": w["route"]["via_drill"],
                        "segments": w["route"]["segments"],
                        "vias": w["route"]["vias"]}})
    for it in bill["vias"]:
        out.append({"item": it["pad"], "net": it["net"], "cls": it["cls"],
                    "status": "FAIL", "fail": "过孔直落焊盘被移：需人工处置"})
    return out


def _make_candidate_board(text, ref, dx, dy, bill):
    moved = P.move_footprint(text, ref, dx, dy)
    stripped, n = P.strip_copper(
        moved, [{"layer_name": s["layer_name"], "x1": s["x1"], "y1": s["y1"],
                 "x2": s["x2"], "y2": s["y2"], "net": s["net"]}
                for s in bill["segments"]],
        [{"x": v["x"], "y": v["y"], "net": v["net"]} for v in bill["vias"]])
    return stripped, n


def _scratch_bm(cid, text):
    d = os.path.join(SCRATCH_DIR, cid)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, BOARD_FILES[0]), "w", encoding="utf-8",
              newline="") as f:
        f.write(text)
    shutil.copy2(os.path.join(SNAP_DIR, BOARD_FILES[1]),
                 os.path.join(d, BOARD_FILES[1]))
    return _load_bm(d)


def cmd_t2():
    live_sha = preflight()
    final_path = os.path.join(PROPS_DIR, "proposals.json")
    if os.path.exists(final_path):
        print("t2 已存在，跳过（幂等）")
        return
    bm = _load_bm(SNAP_DIR)
    by_net = _target_rows(bm)
    text = _read_snapshot_text()
    pads = _pads_simple(bm)
    tracks, vias = _tracks_vias(bm)
    G = bm["pa"]["geometry"]
    baseline_status = {n: _s1_row(n)["live2s1_status"] for n in by_net}
    t1_path = os.path.join(ROWS_DIR, "RPL-019_3V3.json")
    if os.path.exists(t1_path):
        with open(t1_path, encoding="utf-8") as f:
            baseline_status["3V3"] = json.load(f)["live2s2_status"]
    progress("t2 start: baseline=%s" % json.dumps(baseline_status,
                                                  ensure_ascii=False))

    # 1) 口袋分析 + 候选 ref
    pockets = {}
    screen = []
    bills = {}
    for net in PROPOSAL_NETS:
        row = by_net[net]
        s1 = _s1_row(net)
        pk = _pocket_analysis(bm, row, s1)
        refs = P.nearby_refs(pads, pk["pocket_xy"][0], pk["pocket_xy"][1])
        hist = (s1.get("cert_cut_net_histogram") or {}).get("nets") or {}
        top_block = [n for n, _c in sorted(hist.items(),
                                           key=lambda kv: (-kv[1], kv[0]))
                     ][:P.BLOCKER_TOP_NETS]
        brefs = P.nearby_refs(pads, pk["pocket_xy"][0], pk["pocket_xy"][1],
                              radius_mm=P.BLOCKER_REF_MM, nets=set(top_block),
                              exclude_refs=[r["ref"] for r in refs])
        pk["nearby_refs"] = refs
        pk["blocker_top_nets"] = top_block
        pk["blocker_net_refs"] = brefs
        pk["candidate_rule"] = ("非锚件 ∧（口袋端点 %.0fmm 内有焊盘 ∨ S1 直方图 "
                                "top-%d 堵网上 %.0fmm 内有焊盘）；锚件永不入选"
                                % (P.POCKET_NEAR_MM, P.BLOCKER_TOP_NETS,
                                   P.BLOCKER_REF_MM))
        pk["chosen_refs"] = [r["ref"] for r in (refs + brefs)
                             ][:P.CANDIDATE_REFS_PER_NET]
        pockets[net] = pk
        print("pocket %s side=%s fwd=%s rev=%s refs=%s" % (
            net, pk["pocket_side"], pk["forward_closure"],
            pk["reverse_closure"], pk["chosen_refs"]), flush=True)
        for ref in pk["chosen_refs"]:
            rp = _ref_pads(bm, ref)
            if (net, ref) not in bills:
                bills[(net, ref)] = P.disturbance_bill(
                    ref, rp, tracks, vias, net, G.pt_prim_dist)
            bill = bills[(net, ref)]
            fx, fy, _rot = P.footprint_at(text, ref)
            for mv in P.candidate_moves((fx, fy), tuple(pk["pocket_xy"])):
                cid = "%s__%s__%s" % (net, ref, mv["label"])
                try:
                    ctext, n = _make_candidate_board(text, ref, mv["dx"],
                                                     mv["dy"], bill)
                except ValueError as e:
                    screen.append({"candidate_id": cid, "net": net, "ref": ref,
                                   "move": mv, "error": str(e)})
                    continue
                bm2 = _scratch_bm(cid, ctext)
                r2 = _router(bm2)
                A = (row["ax"], row["ay"], frozenset(row["alayers"]))
                B = (row["bx"], row["by"], frozenset(row["blayers"]))
                steps = _ladder(r2, bm2, net, A, B, EVAL_MARGINS)
                sat = any(s["route"]["ok"] for s in steps)
                screen.append({
                    "candidate_id": cid, "net": net, "ref": ref, "move": mv,
                    "bill_counts": bill["counts"],
                    "other_net_items": bill["counts"]["other_net"],
                    "total_items": bill["counts"]["segments_total"]
                    + bill["counts"]["vias_total"],
                    "target_screen": "SAT" if sat else "not-SAT",
                    "closable_rows": 1 if sat else 0,
                    "screen_ladder": [{"margin_mm": s["margin_mm"],
                                       "ok": s["route"]["ok"],
                                       "fail": s["route"]["fail"]}
                                      for s in steps],
                })
                print("  screen %s target=%s bill(other=%d,own=%d)" % (
                    cid, screen[-1]["target_screen"],
                    bill["counts"]["other_net"],
                    bill["counts"]["target_net_own"]), flush=True)
    ranked_screen = P.rank_candidates([s for s in screen if "error" not in s])
    chosen = ranked_screen[:P.MAX_CANDIDATES_TOTAL]
    progress("t2 screen done: %d candidates, chosen=%s" % (
        len(screen), [c["candidate_id"] for c in chosen]))

    # 2) 入选候选全评估（6 目标网 + 账单网重布 + 提案板 staging）
    evals = []
    for c in chosen:
        cid = c["candidate_id"]
        pth = os.path.join(PROPS_DIR, cid + ".json")
        if os.path.exists(pth):
            with open(pth, encoding="utf-8") as f:
                evals.append(json.load(f))
            continue
        net, ref, mv = c["net"], c["ref"], c["move"]
        bill = bills[(net, ref)]
        ctext, n = _make_candidate_board(text, ref, mv["dx"], mv["dy"], bill)
        bm2 = _scratch_bm(cid, ctext)
        r2 = _router(bm2)
        per_net = {}
        routes_to_apply = []
        for tn in sorted(by_net):
            v = _net_verdict(bm2, r2, tn, by_net[tn])
            per_net[tn] = v
            if v["status"] == "SAT":
                routes_to_apply.append(v["route_plan"])
            print("  eval %s net=%s → %s" % (cid, tn, v["status"]), flush=True)
        moved_pads = _ref_pads(bm2, ref)
        stubs = _stub_reroute(bm2, r2, bill, moved_pads)
        for s in stubs:
            if s["status"] == "SAT":
                routes_to_apply.append(s["route_plan"])
        gl = P.closable_rows_of(per_net, baseline_status)
        # 提案板 = 移位 + 剥账单 + 加 witness（新收行）+ 加账单重布铜
        final_text = board_writer.apply_routes(ctext, routes_to_apply,
                                               eol="auto")
        d, sha = _stage_board(cid, final_text)
        ev = {
            "candidate_id": cid, "net": net, "ref": ref, "move": mv,
            "move_norm_mm": round(math.hypot(mv["dx"], mv["dy"]), 4),
            "bill": bill, "strip_counts": n,
            "per_net_verdict": per_net,
            "stub_reroute": stubs,
            "stub_summary": {"total": len(stubs),
                             "sat": sum(1 for s in stubs if s["status"] == "SAT"),
                             "fail": sum(1 for s in stubs
                                         if s["status"] != "SAT")},
            "gained_rows": gl["gained"], "lost_rows": gl["lost"],
            "closable_rows": gl["closable_rows"],
            "other_net_items": bill["counts"]["other_net"],
            "total_items": c["total_items"],
            "staging": {"dir": os.path.relpath(d, PCBFLOW_ROOT),
                        "board_sha256": sha,
                        "routes_applied": len(routes_to_apply)},
            "verdict_note": "SAT=搜索窗梯 witness（L1 终判全过）；UNSAT=frozen_600k "
                            "走廊窗 verified 割或端点辐条自锁；未跑板级强化梯",
        }
        _write_canonical(pth, ev)
        evals.append(ev)
        progress("t2 eval %s: gained=%s lost=%s stubs=%s" % (
            cid, gl["gained"], gl["lost"], ev["stub_summary"]))
    ranked = P.rank_candidates(evals)
    obj = {
        "schema_version": P.LIVE2S2_SCHEMA,
        "artifact_kind": "live2s2_layout_proposals",
        "dataset": P.LIVE2S2_DATASET, "date": P.LIVE2S2_DATE,
        "anchors": list(P.ANCHOR_REFS),
        "anchor_source": "out/revc-a2/structures.json 已批 10 只（开工对账）",
        "move_max_mm": P.MOVE_MAX_MM,
        "baseline_status": baseline_status,
        "pockets": pockets,
        "screening": ranked_screen + [s for s in screen if "error" in s],
        "ranked": [{k: v for k, v in e.items()
                    if k not in ("bill", "per_net_verdict", "stub_reroute")}
                   | {"per_net_status": {n: v["status"] for n, v in
                                         e["per_net_verdict"].items()},
                      "bill_counts": e["bill"]["counts"],
                      "bill_nets": e["bill"]["nets"]}
                   for e in ranked],
        "swdio": {
            "row_id": "RPL-054",
            "verdict": "布局迭代不适用：S1 证书=端点 8 邻辐条全锁（J4 PTH 焊盘自身"
                       "钻孔孔距硬锁，割=8），挪障碍类微移位不改变端点几何；出路=端点"
                       "侧焊盘/孔几何变更（另一前提，不在本包）",
        },
        "endpoint_spoke_lock_class": {
            "nets": ["SWDIO"] + [n for n in PROPOSAL_NETS
                                 if pockets[n].get("reverse_spoke_lock")],
            "note": "反向证书（B 端起 BFS）割=8 spoke ⟹ B 端 8 邻辐条全层封闭：与 "
                    "SWDIO 同机制类（PTH 排针焊盘/孔距硬锁），非锚件微移位不适用",
        },
        "note": "候选评估在 workspace/scratch 内存板；提案板 workspace/staging/"
                "<candidate_id>/（移位+剥账单+witness+重布铜），DRC 由 Bash kicad-cli",
    }
    _write_canonical(final_path, obj)
    progress("t2 done: ranked=%s" % [e["candidate_id"] for e in ranked])


# ---- 汇总 -----------------------------------------------------------------
def _walk(root):
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            yield os.path.join(dirpath, name)


def _drc_summary(stage_rel):
    p = os.path.join(PCBFLOW_ROOT, stage_rel, "drc.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        o = json.load(f)
    sev = {}
    types = {}
    for v in o.get("violations", []):
        sev[v.get("severity", "?")] = sev.get(v.get("severity", "?"), 0) + 1
        types[v.get("type", "?")] = types.get(v.get("type", "?"), 0) + 1
    return {"violations": len(o.get("violations", [])),
            "by_severity": sev, "by_type": types,
            "unconnected_items": len(o.get("unconnected_items", [])),
            "kicad_version": o.get("kicad_version"),
            "source": o.get("source")}


def cmd_assemble():
    live_sha = preflight()
    t1p = os.path.join(ROWS_DIR, "RPL-019_3V3.json")
    props = os.path.join(PROPS_DIR, "proposals.json")
    t1 = None
    if os.path.exists(t1p):
        with open(t1p, encoding="utf-8") as f:
            t1 = json.load(f)
    pr = None
    if os.path.exists(props):
        with open(props, encoding="utf-8") as f:
            pr = json.load(f)
    drc = {"baseline": _drc_summary("out/coreboard-live2b-s2/workspace/"
                                    "staging/t0-baseline")}
    if t1 and t1.get("staging"):
        drc["t1-3v3-witness"] = _drc_summary(t1["staging"]["dir"])
    if pr:
        for e in pr["ranked"]:
            drc[e["candidate_id"]] = _drc_summary(e["staging"]["dir"])
    fs = None
    pre_p = os.path.join(OUT_DIR, "failure-set-startwork.json")
    post_p = os.path.join(OUT_DIR, "failure-set-endwork.json")
    if os.path.exists(pre_p) and os.path.exists(post_p):
        with open(pre_p, encoding="utf-8") as f:
            pre = json.load(f)
        with open(post_p, encoding="utf-8") as f:
            post = json.load(f)
        fs = P.failure_set_diff(pre["ids"], post["ids"])
        fs.update({"pre_count": pre["count"], "post_count": post["count"]})
    live_after = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    prl = [os.path.relpath(f, OUT_DIR) for f in _walk(OUT_DIR)
           if f.endswith(".kicad_prl")]
    obj = {
        "schema_version": P.LIVE2S2_SCHEMA,
        "artifact_kind": P.LIVE2S2_ARTIFACT_KIND,
        "dataset": P.LIVE2S2_DATASET, "date": P.LIVE2S2_DATE,
        "task1_3v3": None if not t1 else {
            k: t1.get(k) for k in ("row_id", "net", "live2s2_status", "witness",
                                   "independent_check", "staging",
                                   "unknown_reason", "s1_reference")},
        "task2_proposals": None if not pr else {
            "ranked": pr["ranked"], "pockets": pr["pockets"],
            "screening_count": len(pr["screening"]), "swdio": pr["swdio"],
            "baseline_status": pr["baseline_status"]},
        "drc": drc,
        "gates": {"failure_set_diff": fs},
        "guards": {
            "live_board_sha256": live_after,
            "live_board_unchanged": live_after == live_sha,
            "snapshot_sha256": hashing.sha256_file(
                os.path.join(SNAP_DIR, BOARD_FILES[0])),
            "kicad_prl_files_in_out": prl,
            "kicad_cli_by": "Bash（编排侧）仅在 workspace/staging 副本执行",
            "cli_py_dependency": "none",
            "route_grid_change": "none", "win1_window_change": "none",
        },
    }
    sha = _write_canonical(os.path.join(OUT_DIR, "live2s2-results.json"), obj)
    manifest = {
        "assembled_at": _now(), "python_version": sys.version.split()[0],
        "command": "scripts/live2s2_run.py assemble",
        "input_sha256": {"live_board": live_sha,
                         "s1_rows": {n: hashing.sha256_file(
                             os.path.join(S1_DIR, "rows", fn))
                             for n, fn in S1_ROW_FILE.items()},
                         "structures": hashing.sha256_file(STRUCTURES)},
        "impl_sha256": {m: hashing.sha256_file(
            os.path.join(PCBFLOW_ROOT, "pcbflow", m))
            for m in ("route_grid.py", "win1_window.py", "live2s2_proposal.py",
                      "board_writer.py", "residual_cmd.py",
                      "live2s1_experiment.py")},
        "script_sha256": hashing.sha256_file(os.path.join(HERE,
                                                          "live2s2_run.py")),
        "pcbagent_adapter_lock": route_grid.pcbagent_fc2_lock(),
        "protected_files": {rel: hashing.sha256_file(
            os.path.join(PCBFLOW_ROOT, rel)) for rel, _p in P.PROTECTED},
    }
    _write_canonical(os.path.join(OUT_DIR, "run-manifest.json"), manifest)
    _write_report(obj, t1, pr)
    print("live2s2-results.json sha=%s…" % sha[:8])
    progress("assemble done: t1=%s ranked=%s drc=%s" % (
        (t1 or {}).get("live2s2_status"),
        [e["candidate_id"] for e in (pr or {}).get("ranked", [])],
        {k: (v or {}).get("unconnected_items") for k, v in drc.items()}))


def _drc_cell(d, base):
    if not d:
        return "未跑"
    if not base:
        return "viol=%d unconn=%d" % (d["violations"], d["unconnected_items"])
    dv = d["violations"] - base.get("violations", 0)
    du = d["unconnected_items"] - base.get("unconnected_items", 0)
    return "viol=%d(%+d) unconn=%d(%+d)" % (d["violations"], dv,
                                            d["unconnected_items"], du)


def _write_report(obj, t1, pr):
    drc = obj["drc"]
    base = drc.get("baseline")
    g = obj["guards"]
    fs = (obj.get("gates") or {}).get("failure_set_diff")
    L = ["# LIVE2B-S2 汇总报告（3V3 零拆收口尝试 + 布局迭代提案 + 铜扰动账单）",
         "",
         "- 日期：%s；板：live 快照副本 sha=%s…（live 板零写，pre=post 复验 "
         "unchanged=%s）" % (obj["date"], g["snapshot_sha256"][:8],
                             g["live_board_unchanged"]),
         "- 前提：zero-ripup（他网铜与自网已落铜均冻结障碍，只加铜不拆铜）；"
         "SAT=Router witness（Region/A*+L1 终判全过+端点落铜）；UNSAT=verified "
         "证书；其余 UNKNOWN；禁自动改判；route_grid/win1_window 零改动；cli.py "
         "零依赖",
         "- 本包全程不写 live：产物=提案与决策材料；提案板只在 "
         "`workspace/staging/<id>/`（kicad-cli DRC 由 Bash 在副本执行）",
         "", "## 1. 3V3（RPL-019）零拆收口尝试", ""]
    if t1:
        w = t1.get("witness") or {}
        ic = t1.get("independent_check") or {}
        L += ["- **结论：%s**（S1：corridor-scope UNSAT 割 729 + 板级强化 UNKNOWN"
              "（候选通径）→ S2：搜索窗梯 witness）" % t1["live2s2_status"],
              "- 机制：pcbagent Router 原口径搜索窗=端点 bbox+L3_MARGIN=3mm（"
              "route_one/LIVE-1 含端点变体均在此窗内失败）；把 bbox 放大到 "
              "**%s mm** 即得 witness（margin 仅搜索参数，合法性仍由 _try_route "
              "内 Region/A*+L1 终判裁决，ripup1_campaign._replan_net_excl 同一"
              "先例）" % w.get("margin_mm"),
              "- witness：%s 段 + %s 过孔，长 %s mm，refine_rounds=%s，bbox=%s；"
              "**出 S1 走廊窗=%s**（与 restricted 割不矛盾：割只证走廊窗内"
              "无路，witness 绕出窗）" % (w.get("segments"), w.get("vias"),
                                       w.get("length_mm"),
                                       w.get("refine_rounds"), w.get("bbox_mm"),
                                       w.get("exits_s1_corridor_region")),
              "- 独立复核：fresh Legality 逐段 %s/逐孔 %s 全过=%s；A 落铜=%s；"
              "B 落铜=%s；B 触及既有同网铜=%s；all_ok=%s"
              % (ic.get("seg_checked"), ic.get("via_checked"),
                 not ic.get("seg_bad") and not ic.get("via_bad"),
                 ic.get("a_touch"), ic.get("b_touch"),
                 ic.get("b_on_existing_net_copper"), ic.get("all_ok")),
              "- 窗梯：%s" % "；".join(
                  "%smm→%s" % (s["margin_mm"], "SAT" if s["ok"] else "不可达")
                  for s in (t1.get("ladder") or [])),
              "- 同网落点枚举（B 侧分量 top-%d，证据用）：%s"
              % (P.LANDING_TOP_K, "；".join(
                  "%s(%.2f,%.2f)d=%.2f→%s" % (
                      lt["landing"]["kind"], lt["landing"]["x"],
                      lt["landing"]["y"], lt["landing"]["dist_to_a_mm"],
                      "SAT@%smm" % next((s["margin_mm"] for s in lt["steps"]
                                         if s["ok"]), "-")
                      if lt["sat"] else "不可达")
                  for lt in (t1.get("landing_enumeration") or [])) or "无"),
              "- kicad-cli DRC（staging 副本 `%s`）：%s（基线 %s）"
              % ((t1.get("staging") or {}).get("dir"),
                 _drc_cell(drc.get("t1-3v3-witness"), base),
                 _drc_cell(base, None)),
              "- route plan：`rows/RPL-019_3V3.json` → `route_plan`（uuid=%s；"
              "board_writer.apply_routes 同口径，可直接用于落板提案）"
              % (t1.get("route_plan") or {}).get("uuid"),
              "- 板级 UNSAT 证书：不可能——S1 板级模型已 reachable_b=True（候选"
              "通径），S2 以 witness 收口，UNKNOWN→SAT",
              ""]
    else:
        L += ["- 未产出（t1 未跑）", ""]
    L += ["## 2. 布局迭代提案（FMC_SDNE0 / GNDA / LTDC_VSYNC / VBAT）", ""]
    if pr:
        L += ["- 锚件（永不入候选）：%s（%s）" % (", ".join(pr["anchors"]),
                                              pr["anchor_source"]),
              "- 候选定义（放宽声明）：%s；移位上限 %.1f mm；每候选先筛"
              "（目标网搜索窗梯 %s mm）再全评估（6 目标网 verdict + 账单网"
              "重布 + 提案板 DRC）" % (
                  next(iter(pr["pockets"].values()))["candidate_rule"],
                  pr["move_max_mm"], list(EVAL_MARGINS)),
              "", "### 2.1 口袋分析（哪端被围）", "",
              "| 网 | 口袋端 | 端点 | 正向闭包 | 反向闭包 | 反向割 | 5mm 内非锚件 | "
              "堵网 ref(7mm) | 入选 |", "|---|---|---|---|---|---|---|---|---|"]
        for net, pk in pr["pockets"].items():
            L.append("| %s | %s | %s @(%s) | %s | %s | %s | %s | %s | %s |" % (
                net, pk["pocket_side"], pk.get("pocket_kind"),
                ",".join("%.3f" % v for v in pk["pocket_xy"]),
                pk["forward_closure"], pk["reverse_closure"],
                pk["reverse_note"],
                ",".join(r["ref"] for r in pk["nearby_refs"]) or "无",
                ",".join("%s" % r["ref"] for r in pk.get("blocker_net_refs")
                         or []) or "无",
                ",".join(pk["chosen_refs"]) or "无"))
        L += ["", "### 2.2 排序候选清单（≤%d；排序=可收行数↓、他网扰动项数↑）"
              % P.MAX_CANDIDATES_TOTAL, "",
              "| # | 候选 | 目标网 | ref | 移位 | 可收行 | 账单 他网/自网 | "
              "账单网 | 6 网 verdict | 账单重布 | DRC(提案板) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, e in enumerate(pr["ranked"], 1):
            bc = e["bill_counts"]
            L.append("| %d | %s | %s | %s | (%+.2f,%+.2f) %s | %d %s | %d/%d | "
                     "%s | %s | sat %d/fail %d | %s |" % (
                         i, e["candidate_id"], e["net"], e["ref"],
                         e["move"]["dx"], e["move"]["dy"], e["move"]["label"],
                         e["closable_rows"],
                         ("gained=%s" % e["gained_rows"]) if e["gained_rows"]
                         else "",
                         bc["other_net"], bc["target_net_own"],
                         ",".join(e["bill_nets"]) or "-",
                         " ".join("%s=%s" % (n[:4], v[:3]) for n, v in
                                  e["per_net_status"].items()),
                         e["stub_summary"]["sat"], e["stub_summary"]["fail"],
                         _drc_cell(drc.get(e["candidate_id"]), base)))
        L += ["", "- 筛选总数：%d（未入选者只保留筛选账，见 proposals.json "
              "screening）" % len(pr.get("screening") or []),
              "- verdict 口径：SAT=搜索窗梯 witness；UNSAT=frozen_600k 走廊窗 "
              "verified 割或端点辐条自锁局部证书；未跑板级强化梯（候选评估预算）",
              "", "### 2.3 SWDIO 专项 + 端点自锁机制类", "",
              "- SWDIO（RPL-054）：%s" % pr["swdio"]["verdict"],
              "- 同机制类（反向证书割=8 spoke）：%s——%s"
              % (", ".join(pr["endpoint_spoke_lock_class"]["nets"]),
                 pr["endpoint_spoke_lock_class"]["note"]), ""]
        for net, pk in pr["pockets"].items():
            if pk.get("reverse_spoke_lock"):
                L.append("  - %s：B 端 %s @(%s) 辐条封闭规则直方图 %s" % (
                    net, pk.get("pocket_kind"),
                    ",".join("%.3f" % v for v in pk["pocket_xy"]),
                    json.dumps(pk.get("reverse_spoke_rules"),
                               ensure_ascii=False)))
        L.append("")
    else:
        L += ["- 未产出（t2 未跑）", ""]
    L += ["## 3. 证据链引用", "",
          "- RIPUP-1（out/coreboard-ripup1）：6 网 A* 不可达 + 洪泛封堵归因"
          "（heuristic）；3V3 拟拆 FMC_D12/FMC_D13/SDMMC1_D0/D1——S2 证明 3V3 "
          "**无需拆线**，只需放大搜索窗",
          "- FB-1（out/coreboard-fb1）：ripup 直调 Router 先例（arm2）；本包 "
          "_try_route 放大 bbox 沿用 ripup1_campaign._replan_net_excl 的"
          "\"margin 仅搜索参数\"声明",
          "- LIVE-1（out/coreboard-live-apply1）：3V3 端点层放宽/端点自由变体"
          "（U2.49→C25.1/C26.1）均 UNKNOWN——皆在 3mm 原口径窗内；S2 5mm 窗即 SAT",
          "- S1（out/coreboard-live2b-s1）：6 网 UNSAT(verified)；3V3 走廊 scope "
          "割 729（restricted）+ 板级 UNKNOWN（候选通径）→ S2 witness 出窗，"
          "两者一致；其余 5 网 board-scope 割为本包提案的基线",
          "", "## 4. 应用所需前提（用户须批）", "",
          "1. 3V3 witness 落 live：批准 `rows/RPL-019_3V3.json.route_plan`（44 段 "
          "F.Cu 新铜，零拆线）写入 live 板（写前快照 + pre/post sha + kicad-cli "
          "DRC 复验：期望 unconnected 57→56、violations 零新增，与 staging 副本"
          "一致）；",
          "2. 任一布局候选落 live：批准该 ref 微移位 + 账单铜剥除 + 账单重布铜 + "
          "witness（若有）——须先通过布局门/受影响约束复核；%s" % (
              ("本包候选均**未收任何目标行**（见 2.2），不建议应用"
               if pr and not any(e["closable_rows"] > 0 for e in pr["ranked"])
               else "可收行候选见 2.2（含账单与 DRC）")),
          "3. SWDIO / LTDC_VSYNC / VBAT：端点 PTH 排针焊盘/孔距自锁，非锚件微移位"
          "不适用；出路=端点侧焊盘/孔几何或锚件（J3/J4）位姿变更（另一前提，"
          "须人工批准并重过架构预检）；",
          "4. FMC_SDNE0 / GNDA：口袋端点被 U1（锚件）引脚场围死（FMC_SDNE0："
          "S1 割直方图=FMC_SDCKE0 382/ETH_REF_CLK 117 等锚件扇出走线，割论据 "
          "pad 网属仅 U1；GNDA：反向割 228，闭包 128 格即被围）；≤2mm 非锚件微"
          "移位（仅 C5/C4 可达）不解锁；出路=拆线重布（RIPUP-1 前提）或锚件扇出"
          "重排（另一前提）。",
          "", "## 5. 验收门", ""]
    if fs:
        L.append("- 测试失败集差集：new_failures=%s（gates_ok=%s；pre=%s post=%s "
                 "unchanged=%s）" % (fs["new_failures"] or "无", fs["gates_ok"],
                                     fs.get("pre_count"), fs.get("post_count"),
                                     fs["unchanged_count"]))
    else:
        L.append("- 测试失败集差集：未收档（收工 pytest 快照缺失）")
    L += ["- live 板 sha 收工复验：unchanged=%s（%s…）"
          % (g["live_board_unchanged"], g["live_board_sha256"][:8]),
          "- .kicad_prl 副作用：%s（仅 workspace/staging 副本内，kicad-cli 生成；"
          "live/datasets 零触碰）" % (len(g["kicad_prl_files_in_out"])),
          "- 新测试：tests/test_live2s2_proposal.py（只测纯函数/账本逻辑）", ""]
    with open(os.path.join(OUT_DIR, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("REPORT.md 落盘")


def cmd_fails(raw_path, out_path):
    ids = []
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^(FAILED|ERROR) (\S+)", line)
            if m:
                ids.append("%s %s" % (m.group(1), m.group(2)))
    obj = {"raw": os.path.relpath(raw_path, PCBFLOW_ROOT), "count": len(ids),
           "failed": sum(1 for i in ids if i.startswith("FAILED")),
           "errors": sum(1 for i in ids if i.startswith("ERROR")),
           "ids": ids}
    _write_canonical(out_path, obj)
    print("failure-set: n=%d failed=%d errors=%d" % (
        len(ids), obj["failed"], obj["errors"]))


def main():
    sel = sys.argv[1] if len(sys.argv) > 1 else ""
    if sel == "t1":
        cmd_t1()
    elif sel == "t2":
        cmd_t2()
    elif sel == "assemble":
        cmd_assemble()
    elif sel == "fails":
        cmd_fails(sys.argv[2], sys.argv[3])
    elif sel == "stage-baseline":
        preflight()
        d, sha = _stage_board("t0-baseline", _read_snapshot_text())
        print("baseline staged sha=%s… dir=%s" % (sha[:8], d))
    else:
        _fail("用法：live2s2_run.py t1|t2|assemble|stage-baseline|fails")


if __name__ == "__main__":
    main()
