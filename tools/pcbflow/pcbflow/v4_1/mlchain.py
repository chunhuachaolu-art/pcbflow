"""pcbflow.v4_1.mlchain -- 多层族全链（生成 → 求解 → 检查；E2 G2.1）。

三层结构（任务书 §3 E2 红线：合成域求解器属 v4exp/ 零改动——多层求解
经本适配层以**只读库调用**方式复用 v4exp.router，不改 v4exp 任何字节）：

1. 生成：mlfamily.generate_ml_scenario（f9/f10 多层族，确定性 seed）；
2. 求解：mlboard_to_v4exp_board 纯投影（schema 换牌 + 剥离 ml_meta，
   其余字段逐键拷贝）→ v4exp.router.solve_board（格点 A*，多层状态空
   间 (ix,iy,layer,dir)，via 跨任意允许层对）；
3. 检查（v4_1 精确几何内核独立复查求解输出——不信任求解器自报）：
   - via 跨度合法性：from/to 层在栈内 + 跨度=栈序闭区间（layerstack）；
   - 层合法性：每 route 层 ∈ 该网 net class 的 allowed_layers；
   - 宽度合法性：每 route width == 类宽（mlfamily 双类同宽冻结参数）；
   - clearance 复查（Minkowski 核精确引擎）：全部异网物项对（track/
     via；via=全跨度层障碍）pred >= required - eps；hard=0 为门，
     保守带内标记描述性登记（E1 同口径：band 非门）；
   - 双引擎交叉：checker 外切多边形引擎对同几何独立复判，verdict 不
     一致 = cross_disagreement（blocked 登记，禁静默）；
   - 连通性/违例计数沿用求解器自报 metrics（其独立重算自 routes/vias
     JSON，v4exp 冻结口径）+ 本层零回写求解器。

gate（G2.1）：sat 预期场景 = 求解 sat + 检查全绿；unsat 预期场景 =
求解如实 failed（多层不可满足构造，不渲染 sat）。

CLI：python -m pcbflow.v4_1.mlchain --out <dir>
（产物 boards/ solver-runs/ mlchain-manifest.json；canonical JSON；
零 wall-clock——declared_date 常量；零子进程——router 为进程内 import）。
"""

from __future__ import annotations

from . import DECLARED_DATE
from .checker import CheckItem, IndependentGeometryChecker
from .checker import _capsule_polygon, _circumscribed_ngon
from .geometry import GeomItem, clearance_between_items
from .layerstack import LayerStack
from .mlfamily import ML_LAYERS, generate_all_ml, generate_ml_scenario
from .netclasses import NetClass, NetClassTable

__all__ = ["mlboard_to_v4exp_board", "solve_ml", "check_ml_solution",
           "run_ml_chain", "main"]

_CHAIN_SCHEMA = "pcbflow.v4_1.mlchain/1"
_EPS = 1e-12


# ---------------------------------------------------------------- 求解适配

def mlboard_to_v4exp_board(ml):
    """mlboard 对象 -> v4exp 板 dict（纯投影；零 v4exp 改动红线）。"""
    board = {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": ml["scenario_id"],
        "split": ml["split"],
        "family": ml["family"],
        "seed": ml["seed"],
        "board": {
            "bbox_mm": list(ml["board"]["bbox_mm"]),
            "layers": list(ml["board"]["layers"]),
        },
        "rules": {
            "grid_mm": ml["rules"]["grid_mm"],
            "clearance_mm": ml["rules"]["clearance_mm"],
            "width_mm": dict(ml["rules"]["width_mm"]),
            "via": dict(ml["rules"]["via"]),
            "allowed_layers": {k: list(v) for k, v in
                               ml["rules"]["allowed_layers"].items()},
        },
        "pads": [dict(p) for p in ml["pads"]],
        "nets": [dict(n) for n in ml["nets"]],
        "keepouts": [dict(k) for k in ml["keepouts"]],
        "relations": [dict(r) for r in ml["relations"]],
        "label": ml["label"],
    }
    return board


def solve_ml(ml, route_order=None):
    """mlboard -> v4exp 求解结果（只读库调用；确定性）。"""
    from ..v4exp import router  # 进程内 import：零子进程、零 v4exp 改动
    board = mlboard_to_v4exp_board(ml)
    order = list(route_order) if route_order is not None \
        else [n["net_id"] for n in ml["nets"]]
    return router.solve_board(board, {"route_order": order, "group": "E2-ML"})


# ---------------------------------------------------------------- 检查腿

def _netclass_table_for_ml(ml):
    """mlboard 规则 -> NetClassTable（Default+clock；逐网指派）。"""
    w = ml["rules"]["width_mm"]
    c = ml["rules"]["clearance_mm"]
    classes = {
        "Default": NetClass("Default", c, w["default"]),
        "clock": NetClass("clock", c, w["clock"]),
    }
    assignments = {}
    for n in ml["nets"]:
        cls = n["net_class"]
        assignments[n["net_id"]] = cls if cls != "default" else "Default"
    return NetClassTable(classes, assignments, [], "mlboard_rules_projection")


def _route_items_dual(run, ml=None):
    """求解输出（+板 pads）-> 双引擎物项（同序 1:1：精确核 GeomItem +
    外切多边形 CheckItem；同一几何源、两套独立几何建模——交叉判定用）。

    pads 计入障碍物项（net 相异才互查，同网 pad 豁免——求解器同口径）：
    多层语义=pad 仅在其所属铜层为障碍（f9/f10 无 THT pad；THT 全层
    障碍语义的 kicad-cli 对拍在 e2parity 域覆盖）。
    """
    stack = LayerStack(ML_LAYERS)
    exact, poly = [], []
    from .geometry import PadGeom
    for r in run.get("routes", []):
        nid = str(r["route_id"]).rsplit("-S", 1)[0]
        pts = r["polyline_mm"]
        for i in range(1, len(pts)):
            (ax, ay), (bx, by) = pts[i - 1], pts[i]
            src = {"route_id": r["route_id"], "leg": i}
            exact.append(GeomItem.from_track(
                nid, r["layer"], r["width_mm"], ax, ay, bx, by, src=src))
            poly.append(CheckItem(
                "track", nid, {r["layer"]},
                _capsule_polygon(ax, ay, bx, by, r["width_mm"] / 2.0),
                src=dict(src)))
    for v in run.get("vias", []):
        nid = str(v["via_id"]).rsplit("-V", 1)[0]
        size = v["drill_mm"] + 2.0 * v["annular_ring_mm"]
        span = stack.via_span(v["from_layer"], v["to_layer"])
        src = {"via_id": v["via_id"]}
        exact.append(GeomItem.from_via(
            nid, size, span, v["center_mm"][0], v["center_mm"][1], src=src))
        poly.append(CheckItem(
            "via", nid, set(span),
            _circumscribed_ngon(v["center_mm"][0], v["center_mm"][1],
                                size / 2.0), src=dict(src)))
    for p in (ml or {}).get("pads", []):
        pad = PadGeom("rect", p["x_mm"], p["y_mm"], p["w_mm"], p["h_mm"],
                      0.0, pad_id=p["pad_id"], net_id=p["net_id"],
                      layers=(p["layer"],))
        src = {"pad_id": p["pad_id"]}
        exact.append(GeomItem.from_pad(pad, {p["layer"]}, src=dict(src)))
        from .checker import _roundrect_polygon
        poly.append(CheckItem(
            "pad", p["net_id"], {p["layer"]},
            _roundrect_polygon(p["x_mm"], p["y_mm"], p["w_mm"] / 2.0,
                               p["h_mm"] / 2.0, 0.0, 0.0),
            src=dict(src)))
    return exact, poly


def _poly_item_clearance_vs(a_poly, b_poly):
    """两外切多边形物项间 clearance（多边形间距；相交=0 记负下界口径
    与精确引擎 overlap 一致：相交时 clearance=-(ra+rb) 量级仅报告用，
    判违例只需 <0——这里用 -1.0 哨兵，方向一致不冒充深度）。"""
    from .checker import _poly_distance
    d = _poly_distance(a_poly, b_poly)
    return 0.0 - 1.0 if d <= _EPS else d


def _item_bbox_exact(item):
    """精确物项全形包围盒（核顶点 ± 半径）。"""
    xs = [p[0] for p in item.core]
    ys = [p[1] for p in item.core]
    r = item.radius
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)


def _bbox_gap_lb(a, b):
    """两轴对齐包围盒间距下界（欧氏；相交=0）。"""
    gx = max(a[0] - b[2], b[0] - a[2], 0.0)
    gy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return (gx * gx + gy * gy) ** 0.5


#: 外切多边形超集的安全裕量：r(1/cos(pi/N)-1) 项，r<=0.2、N=32 时
#: <=0.001mm；取 0.01 留双引擎包围盒各自取舍余量。
_POLY_SUPERSET_MARGIN_MM = 0.01


def check_ml_solution(ml, run, conservative_band_mm=0.01):
    """求解输出独立复查（v4_1 双引擎；不信任求解器自报）。

    剪枝登记（不静默）：异网共层物项对先按全形包围盒欧氏间距下界剪枝
    ——bbox 间距 > required + 保守带 + 0.01 时两引擎均保证 clean（精确
    引擎 clearance >= bbox 下界；外切多边形超集偏差 <= 0.001 << 0.01），
    跳过近距离计算；剪枝计数入 returned 记录。
    """
    stack = LayerStack(ML_LAYERS)
    table = _netclass_table_for_ml(ml)
    allowed = dict(ml["rules"]["allowed_layers"])
    net_class_of = {n["net_id"]: n["net_class"] for n in ml["nets"]}

    # ---- via 跨度合法性 ----
    via_span_bad = []
    for v in run.get("vias", []):
        try:
            stack.via_span(v["from_layer"], v["to_layer"])
        except Exception as exc:  # LayerStackError -> fail-closed 登记
            via_span_bad.append({"via_id": v["via_id"], "error": str(exc)})

    # ---- 层/宽度合法性 ----
    layer_bad, width_bad = [], []
    for r in run.get("routes", []):
        nid = str(r["route_id"]).rsplit("-S", 1)[0]
        cls = net_class_of.get(nid, "default")
        if r["layer"] not in allowed.get(cls, allowed["default"]):
            layer_bad.append({"route_id": r["route_id"], "layer": r["layer"],
                              "net_class": cls})
        if abs(float(r["width_mm"])
               - ml["rules"]["width_mm"][cls]) > 1e-9:
            width_bad.append({"route_id": r["route_id"],
                              "width_mm": r["width_mm"],
                              "expected_mm": ml["rules"]["width_mm"][cls]})

    # ---- 双引擎 clearance 复查（同序物项对：精确核 + 外切多边形）----
    exact, poly = _route_items_dual(run, ml)
    bboxes = [_item_bbox_exact(it) for it in exact]
    hard_violations = []
    band_flags = []
    cross_disagreements = []
    min_clear = None
    pairs_same_layer_foreign = 0
    pairs_pruned_far = 0
    for i in range(len(exact)):
        for j in range(i + 1, len(exact)):
            a, b = exact[i], exact[j]
            if a.net == b.net:
                continue
            if not (a.layers & b.layers):
                continue
            pairs_same_layer_foreign += 1
            required = table.required_clearance(a.net, b.net)
            if _bbox_gap_lb(bboxes[i], bboxes[j]) > \
                    required + conservative_band_mm + \
                    _POLY_SUPERSET_MARGIN_MM:
                pairs_pruned_far += 1
                continue  # 两引擎均保证 clean（见 docstring 剪枝论证）
            res = clearance_between_items(a, b)
            if res is None:
                continue
            pred = res["clearance_mm"]
            overlap = res["overlap"]
            if min_clear is None or pred < min_clear:
                min_clear = pred
            hard = overlap or pred < required - _EPS
            if hard:
                hard_violations.append({
                    "pair": sorted([_item_ref(a), _item_ref(b)]),
                    "nets": sorted([a.net, b.net]),
                    "layers": sorted(a.layers & b.layers),
                    "pred_clearance_mm": None if overlap
                    else round(pred, 6),
                    "required_mm": round(required, 6),
                    "overlap": overlap,
                })
            elif pred < required + conservative_band_mm - _EPS:
                band_flags.append({
                    "pair": sorted([_item_ref(a), _item_ref(b)]),
                    "nets": sorted([a.net, b.net]),
                    "pred_clearance_mm": round(pred, 6),
                    "required_mm": round(required, 6),
                })
            # 交叉：外切多边形引擎独立判定同对（超集方向：只多判不少判）
            pred_poly = _poly_item_clearance_vs(poly[i].poly, poly[j].poly)
            hard_poly = pred_poly < required - _EPS
            if hard != hard_poly:
                cross_disagreements.append({
                    "pair": sorted([_item_ref(a), _item_ref(b)]),
                    "nets": sorted([a.net, b.net]),
                    "exact_hard": bool(hard),
                    "polygon_hard": bool(hard_poly),
                    "exact_pred_mm": None if overlap else round(pred, 6),
                    "polygon_pred_mm": round(pred_poly, 6),
                })

    solver_metrics = run.get("metrics", {})
    expected_sat = ml["label"] == "satisfiable"
    solver_sat = run.get("status") == "sat"
    checks = {
        "via_span_illegal": via_span_bad,
        "layer_illegal": layer_bad,
        "width_illegal": width_bad,
        "clearance_hard_violations": hard_violations,
        "clearance_band_flags": band_flags,
        "cross_engine_disagreements": cross_disagreements,
        "min_foreign_clearance_mm": None if min_clear is None
        else round(min_clear, 6),
        "pair_stats": {
            "same_layer_foreign_pairs": pairs_same_layer_foreign,
            "pruned_far_by_bbox": pairs_pruned_far,
            "pruning_rule": "bbox 欧氏间距下界 > required+band+0.01 时"
                            "两引擎均保证 clean（外切超集偏差 <=0.001）",
            "note": "min_foreign_clearance_mm 为未剪枝对全域最小（剪枝对"
                    " clearance > required+band+0.01，不可能更小）",
        },
    }
    gate_pass = (expected_sat == solver_sat)
    if expected_sat and solver_sat:
        gate_pass = (gate_pass
                     and not via_span_bad and not layer_bad and not width_bad
                     and not hard_violations and not cross_disagreements
                     and solver_metrics.get("all_connected") is True
                     and sum(solver_metrics.get("violations",
                                                {}).values()) == 0)
    return {
        "schema": _CHAIN_SCHEMA,
        "declared_date": DECLARED_DATE,
        "scenario_id": ml["scenario_id"],
        "family": ml["family"],
        "label": ml["label"],
        "expected": "sat" if expected_sat else "unsat",
        "solver": {
            "status": run.get("status"),
            "route_count": len(run.get("routes", [])),
            "via_count": len(run.get("vias", [])),
            "metrics": {
                "all_connected": solver_metrics.get("all_connected"),
                "unconnected": solver_metrics.get("unconnected"),
                "violations": solver_metrics.get("violations"),
                "total_length_mm": solver_metrics.get("total_length_mm"),
                "bend_count": solver_metrics.get("bend_count"),
                "objective": solver_metrics.get("objective"),
                "search_nodes": solver_metrics.get("search_nodes"),
            },
        },
        "check": checks,
        "gate_pass": bool(gate_pass),
    }


def _item_ref(item):
    return str(item.src.get("route_id") or item.src.get("via_id"))


# ---------------------------------------------------------------- 全链

def run_ml_chain():
    """生成 → 求解 → 检查 全链（20 场景；确定性）。"""
    records = []
    for ml in generate_all_ml():
        run = solve_ml(ml)
        rec = check_ml_solution(ml, run)
        rec["solver_run"] = run
        records.append(rec)
    return records


def main(argv=None):
    """CLI：python -m pcbflow.v4_1.mlchain --out <dir>"""
    import argparse
    from pathlib import Path
    from .canonical import write_canonical_json
    from .mlfamily import validate_mlboard
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.mlchain")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    out = Path(ns.out)
    (out / "boards").mkdir(parents=True, exist_ok=True)
    (out / "solver-runs").mkdir(parents=True, exist_ok=True)

    records = run_ml_chain()
    manifest_entries = []
    for rec in records:
        sid = rec["scenario_id"]
        ml = generate_ml_scenario(sid)
        errs = validate_mlboard(ml)
        if errs:
            raise RuntimeError("%s mlboard 校验失败: %s" % (sid, errs))
        board_path = out / "boards" / ("mlboard-%s.json" % sid)
        write_canonical_json(board_path, ml)
        run_path = out / "solver-runs" / ("%s.json" % sid)
        write_canonical_json(run_path, rec["solver_run"])
        run_rec = dict(rec)
        del run_rec["solver_run"]
        manifest_entries.append(run_rec)

    sat_expected = [r for r in manifest_entries if r["expected"] == "sat"]
    unsat_expected = [r for r in manifest_entries if r["expected"] == "unsat"]
    manifest = {
        "schema": _CHAIN_SCHEMA,
        "declared_date": DECLARED_DATE,
        "chain": ["mlfamily.generate_all_ml", "mlchain.solve_ml"
                  "(v4exp.router 只读库调用)", "mlchain.check_ml_solution"
                  "(v4_1 双引擎独立复查)"],
        "scenario_count": len(manifest_entries),
        "families": {
            fam: [r["scenario_id"] for r in manifest_entries
                  if r["family"] == fam]
            for fam in ("f9", "f10")
        },
        "expected_counts": {"sat": len(sat_expected),
                            "unsat": len(unsat_expected)},
        "gate_pass_count": sum(1 for r in manifest_entries if r["gate_pass"]),
        "via_total": sum(r["solver"]["via_count"]
                         for r in manifest_entries),
        "clearance_hard_total": sum(
            len(r["check"]["clearance_hard_violations"])
            for r in manifest_entries),
        "cross_disagreement_total": sum(
            len(r["check"]["cross_engine_disagreements"])
            for r in manifest_entries),
        "records": manifest_entries,
    }
    write_canonical_json(out / "mlchain-manifest.json", manifest)
    print("mlchain: %d scenarios, gate_pass=%d/%d, vias=%d, hard=%d, "
          "cross=%d" % (manifest["scenario_count"],
                        manifest["gate_pass_count"],
                        manifest["scenario_count"], manifest["via_total"],
                        manifest["clearance_hard_total"],
                        manifest["cross_disagreement_total"]))
    return 0 if manifest["gate_pass_count"] == manifest["scenario_count"] \
        else 1


if __name__ == "__main__":
    raise SystemExit(main())
