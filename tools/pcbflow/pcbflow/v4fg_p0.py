"""pcbflow.v4fg_p0 -- 细格点求解宿主 P0 spike（FINE-GRID-SOLVER-HOST 决策件
§3，frozen 2026-09-13 R39；prereg=out/v4fg-p0/prereg-p0.json v2）。

定位：纯投影级测量包——对 E4 证 0.25mm 不可达行集做 0.05mm 细格点的
成本-可达性实测，产出 S-FG1（成本上限）/S-FG2（有效性阈值）定值依据。

复用机制（盘上零改动红线）：
  细格点=进程内常量覆盖（fine_grid_context 上下文管理器）：对
  pcbflow.v4exp.grid / pcbflow.v4_1.e4revc / pcbflow.v4_1.solver2 命名
  空间的 import 绑定副本按 prereg v2 constants_map 赋新值，退出恢复。
  pcbflow/v4exp/（冻结契约）与 pcbflow/v4_1/ 一切文件盘上零字节改动；
  投影/阻挡栅格/A* 全部 import 既有组件（RevCProjection/route_row/
  solver2._astar2 经 route_row）。

CLI ops（编排，全部确定性、零网络零模型零板写零 kicad-cli）：
  select / barm / aarm / curves

红线：staging/live 板只读；受保护三文件零变化；canonical JSON；
declared_date=2026-09-13 常量（非 wall-clock）。
"""

from __future__ import annotations

import contextlib
import gc
import json
import math
import pathlib
import time
import tracemalloc

from .v4_1.canonical import write_canonical_json
from .v4_1.costmodel import ViaCostModel  # noqa: F401（口径登记用）
from .v4_1.e4revc import (GRID_MM as _E4REVCo_GRID_MM,  # noqa: F401
                          RevCProjection, _seg_point_dist2,
                          extract_board_bbox, route_row)
from .v4_1.netclasses import load_netclasses

__all__ = [
    "fine_grid_context", "WindowedProjection", "P0Context",
    "corridor_window_for_row", "barm_window_for_row",
    "bottleneck_for_row", "escape_radius_for_endpoint",
    "select_rows_by_prereg", "extract_universe",
    "op_select", "op_barm", "op_aarm", "op_curves",
]

DECLARED_DATE = "2026-09-13"
PREREG_SHA256 = ("9ffb51a6a0b4ede9ad26a0440979f46027b26fe2d918f5d8190d"
                 "0772ceeb239e")
OUT_DIR_DEFAULT = "out/v4fg-p0"
_E4_DIR = "out/v4.1-engineering/e4"

#: prereg v2 fine_grid_contract（cell 计常量 x5 保持物理语义）
FINE_GRID_MM = 0.05
COARSE_GRID_MM = 0.25
_SCALE = int(round(COARSE_GRID_MM / FINE_GRID_MM))   # 5
_CORRIDOR_SAT_MM = 1.5
_CORRIDOR_MARGIN_MM = 1.6
_ESCAPE_CAP_CELLS = 60
_BARM_EXPAND_MM = 2.5
_BARM_MIN_SIDE_MM = 5.0
_SOLVE_REPS = 3
_ASTAR_REP_THRESHOLD_S = 60.0


class V4fgP0Error(ValueError):
    """v4fg P0 链 fail-closed。"""


# ================================================================ 细格点上下文

@contextlib.contextmanager
def fine_grid_context(grid_mm=FINE_GRID_MM):
    """进程内细格点常量覆盖（prereg v2 constants_map；退出恢复）。

    覆盖对象=各模块命名空间的绑定（含 from-import 拷贝），不动任何盘上
    文件。cell 计常量统一 x（0.25/0.05）；mm 计常量不变。
    """
    from .v4exp import grid as _grid_mod
    from .v4_1 import e4revc as _e4revc_mod
    from .v4_1 import solver2 as _solver2_mod
    k = COARSE_GRID_MM / grid_mm   # = 5（cell 计常量放大倍数）
    overrides = [
        (_grid_mod, "GRID_MM", grid_mm),
        (_grid_mod, "MIN_CENTER_SEPARATION_CELLS", int(round(2 * k))),
        (_grid_mod, "DILATION_RADIUS_CELLS", int(round(1 * k))),
        (_grid_mod, "VIA_FOOTPRINT_RADIUS_CELLS", int(round(1 * k))),
        (_e4revc_mod, "GRID_MM", grid_mm),
        (_e4revc_mod, "_SNAP_RADIUS_CELLS", int(round(10 * k))),
        (_solver2_mod, "GRID_MM", grid_mm),
        (_solver2_mod, "VIA_FOOTPRINT_RADIUS_CELLS", int(round(1 * k))),
        (_solver2_mod, "TURN_PENALTY_CELLS", int(round(2 * k))),
        (_solver2_mod, "VIA_COST_CELLS", int(round(32 * k))),
    ]
    saved = [(m, n, getattr(m, n)) for (m, n, _v) in overrides]
    try:
        for (m, n, v) in overrides:
            setattr(m, n, v)
        yield
    finally:
        for (m, n, v) in saved:
            setattr(m, n, v)


def _current_grid_mm():
    from .v4exp import grid as _grid_mod
    return _grid_mod.GRID_MM


# ================================================================ 窗投影

class WindowedProjection(RevCProjection):
    """窗口版 RevCProjection：GridWorld/raster 界=窗 bbox（夹到板 bbox）。

    窗世界含 2.0mm 工作域裕量（GridWorld 口径），裕量域与窗边内缩
    0.6mm 带按 e4revc 板边阻挡语义建模（保守：窗内可行域受窗边约束，
    prereg v2 corridor_metric.computed_on / b_arm.window）。
    """

    def __init__(self, board_text, window, kicad_pro_obj=None,
                 net_table=None, new_via_size=0.6):
        super().__init__(board_text, kicad_pro_obj=kicad_pro_obj,
                         net_table=net_table, new_via_size=new_via_size)
        bb = self.bbox
        win = [max(window[0], bb[0]), max(window[1], bb[1]),
               min(window[2], bb[2]), min(window[3], bb[3])]
        if win[0] >= win[2] or win[1] >= win[3]:
            raise V4fgP0Error("窗夹到板 bbox 后退化: %r" % (win,))
        self.bbox = win
        self._base_board["board"]["bbox_mm"] = list(win)
        from .v4exp.grid import GridWorld
        self.world = GridWorld(self._base_board)


def _row_bbox(row):
    xs = [row["a"]["x"], row["b"]["x"]]
    ys = [row["a"]["y"], row["b"]["y"]]
    return [min(xs), min(ys), max(xs), max(ys)]


def corridor_window_for_row(row, board_bbox):
    """prereg v2 corridor_window：行 bbox 外扩 1.6mm，夹到板 bbox。"""
    rb = _row_bbox(row)
    win = [rb[0] - _CORRIDOR_MARGIN_MM, rb[1] - _CORRIDOR_MARGIN_MM,
           rb[2] + _CORRIDOR_MARGIN_MM, rb[3] + _CORRIDOR_MARGIN_MM]
    return [max(win[0], board_bbox[0]), max(win[1], board_bbox[1]),
            min(win[2], board_bbox[2]), min(win[3], board_bbox[3])]


def barm_window_for_row(row, board_bbox):
    """prereg v2 b_arm.window：行 bbox 外扩 2.5mm；边长 <5mm 以中点为心
    扩到 5mm；再夹到板 bbox（实测行集下夹板不触发）。"""
    rb = _row_bbox(row)
    x0, y0 = rb[0] - _BARM_EXPAND_MM, rb[1] - _BARM_EXPAND_MM
    x1, y1 = rb[2] + _BARM_EXPAND_MM, rb[3] + _BARM_EXPAND_MM
    for lo_hi in ((0, 2), (1, 3)):
        lo, hi = lo_hi
        if x1 - x0 < _BARM_MIN_SIDE_MM:
            cx = (x0 + x1) / 2.0
            x0, x1 = cx - _BARM_MIN_SIDE_MM / 2.0, \
                cx + _BARM_MIN_SIDE_MM / 2.0
        if y1 - y0 < _BARM_MIN_SIDE_MM:
            cy = (y0 + y1) / 2.0
            y0, y1 = cy - _BARM_MIN_SIDE_MM / 2.0, \
                cy + _BARM_MIN_SIDE_MM / 2.0
    return [max(x0, board_bbox[0]), max(y0, board_bbox[1]),
            min(x1, board_bbox[2]), min(y1, board_bbox[3])]


# ================================================================ 上下文装载

class P0Context:
    """E4 前序资产装载（全部只读）：staging 链尾板 + rows.json + 批网集。"""

    def __init__(self, root="."):
        self.root = pathlib.Path(root)
        self.board_path = self.root / _E4_DIR / "l2-batches" / "staging" \
            / "revc.kicad_pcb"
        self.pro_path = self.root / _E4_DIR / "l2-batches" / "staging" \
            / "revc.kicad_pro"
        self.rows_path = self.root / _E4_DIR / "rows.json"
        self.board_bytes = self.board_path.read_bytes()
        import hashlib
        self.board_sha256 = hashlib.sha256(self.board_bytes).hexdigest()
        self.board_text = self.board_bytes.decode("utf-8")
        self.board_bbox = extract_board_bbox(self.board_text)
        pro_obj = None
        try:
            pro_obj = json.loads(self.pro_path.read_bytes().decode("utf-8"))
        except Exception:
            pro_obj = None
        self.net_table = load_netclasses(board_text=self.board_text,
                                         kicad_pro_obj=pro_obj)
        self.rows_obj = json.loads(self.rows_path.read_bytes()
                                   .decode("utf-8"))
        self.required_rows = [r for r in self.rows_obj["rows"]
                              if r.get("class") == "required"]
        self.rows_by_id = {r["row_id"]: r for r in self.required_rows}
        self.protected_for_net = {}
        for b in self.rows_obj["batches"]:
            for n in b["nets"]:
                self.protected_for_net[n] = tuple(sorted(b["nets"]))

    def protected_for(self, row):
        nets = self.protected_for_net.get(row["net"])
        if nets is None:
            raise V4fgP0Error("行网 %r 不在 E4 L2 批网集" % row["net"])
        return nets


def extract_universe(ctx):
    """prereg v2 universe_rule：L2 四批 ladder_trail 首条（A0）
    detail.reason == 'astar_unreachable' 的行（确定性序=row_id）。"""
    out = []
    for bname in ("batch-01", "batch-02", "batch-03", "batch-04"):
        p = ctx.root / _E4_DIR / "l2-batches" / bname / "candidates.json"
        obj = json.loads(p.read_bytes().decode("utf-8"))
        for lt in obj.get("ladder_trail", []):
            trail = lt.get("trail") or []
            if not trail:
                continue
            d0 = trail[0].get("detail") or {}
            if d0.get("reason") == "astar_unreachable":
                rid = lt["row_id"]
                if rid in ctx.rows_by_id:
                    out.append(rid)
    return sorted(set(out))


# ================================================================ 走廊度量

def _endpoint_layers(proj, ep):
    """端点候选层集（e4revc.endpoint_cells 同口径）。"""
    if ep.get("kind") == "track" and ep.get("layer"):
        cand = [ep["layer"]]
    elif ep.get("kind") == "pad":
        pad = proj._find_pad(ep)
        if pad:
            cand = [l for l in pad["layers"] if l in proj.world.layer_index]
        elif ep.get("layer"):
            cand = [ep["layer"]]
        else:
            cand = list(proj.copper)
    else:
        cand = list(proj.copper)
    if not cand:
        cand = [ep["layer"]] if ep.get("layer") else list(proj.copper)
    return [proj.world.layer_index[l] for l in cand
            if l in proj.world.layer_index]


def bottleneck_for_row(proj, row, blocked):
    """prereg v2 bottleneck_halfwidth_mm：逐层阻挡格心到线段 AB 的连续
    点-段距离最小值（1.5mm 饱和）；corridor=最优层。返回 (corridor,
    per_layer)。"""
    w = proj.world
    ax, ay = row["a"]["x"], row["a"]["y"]
    bx, by = row["b"]["x"], row["b"]["y"]
    sat2 = _CORRIDOR_SAT_MM * _CORRIDOR_SAT_MM
    per_layer = {}
    for li in range(len(proj.copper)):
        best2 = sat2
        for (ix, iy) in blocked.get(li) or ():
            d2 = _seg_point_dist2(w.center_mm_x(ix), w.center_mm_y(iy),
                                  ax, ay, bx, by)
            if d2 < best2:
                best2 = d2
        per_layer[proj.copper[li]] = round(math.sqrt(best2), 6)
    corridor = max(per_layer.values())
    return corridor, per_layer


def escape_radius_for_endpoint(proj, ep, blocked,
                                cap_cells=_ESCAPE_CAP_CELLS):
    """prereg v2 escape_radius_mm：Chebyshev 环 k=1..60 首个未阻挡格。"""
    w = proj.world
    grid = _current_grid_mm()
    lis = _endpoint_layers(proj, ep)
    ix0, iy0 = w.cell_x(ep["x"]), w.cell_y(ep["y"])
    for k in range(1, cap_cells + 1):
        for dx in range(-k, k + 1):
            for dy in range(-k, k + 1):
                if max(abs(dx), abs(dy)) != k:
                    continue
                ix, iy = ix0 + dx, iy0 + dy
                if not w.in_bounds(ix, iy):
                    continue
                for li in lis:
                    if (ix, iy) not in blocked[li]:
                        return round(k * grid, 6)
    return round(cap_cells * grid, 6)


# ================================================================ 选行

def select_rows_by_prereg(corridor_records):
    """prereg v2 selection_rule：最宽 5（corridor 降序/escape_min 升序/
    row_id 升序）+ 最窄 5（corridor 升序/escape_min 降序/row_id 升序）。"""
    keyed = []
    for r in corridor_records:
        keyed.append({
            "row_id": r["row_id"], "net": r["net"],
            "corridor_halfwidth_mm": r["corridor_halfwidth_mm"],
            "escape_min_mm": r["escape_min_mm"],
            "_rc": round(r["corridor_halfwidth_mm"], 4),
            "_re": round(r["escape_min_mm"], 4),
        })
    desc = sorted(keyed, key=lambda r: (-r["_rc"], r["_re"], r["row_id"]))
    asc = sorted(keyed, key=lambda r: (r["_rc"], -r["_re"], r["row_id"]))
    def _clean(seq, cls):
        out = []
        for i, r in enumerate(seq[:5]):
            out.append({"rank": i + 1, "group": cls, "row_id": r["row_id"],
                        "net": r["net"],
                        "corridor_halfwidth_mm": r["corridor_halfwidth_mm"],
                        "escape_min_mm": r["escape_min_mm"]})
        return out
    return _clean(desc, "widest"), _clean(asc, "narrowest")


# ================================================================ 测量工具

def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _run_with_peak(fn):
    """fn 在 tracemalloc 开启下执行 -> (result, peak_bytes)。"""
    gc.collect()
    tracemalloc.start()
    try:
        res = fn()
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
        gc.collect()
    return res, peak


def _solve_summary(res):
    if not res.get("ok"):
        return {"ok": False, "reason": res.get("reason"),
                "search_nodes": res.get("search_nodes", 0)}
    runs = res.get("runs") or []
    return {"ok": True, "reason": None,
            "search_nodes": res.get("search_nodes", 0),
            "runs_n": len(runs),
            "vias_n": max(0, len(runs) - 1),
            "path_cells_n": sum(len(c) for (_li, c) in runs)}


# ================================================================ 编排 ops

def _out_dir(root="."):
    p = pathlib.Path(root) / OUT_DIR_DEFAULT
    p.mkdir(parents=True, exist_ok=True)
    return p


def _progress(root, mutate):
    p = pathlib.Path(root) / OUT_DIR_DEFAULT / "progress.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.is_file():
        obj = json.loads(p.read_bytes().decode("utf-8"))
    else:
        obj = {
            "schema": "pcbflow.v4fg.p0-progress/1",
            "declared_date": DECLARED_DATE,
            "prereg_sha256": PREREG_SHA256,
            "steps": {},
            "budget": {"s_fg3_tokens": 50000000, "s_fg3_days": 14,
                       "note": "S-FG3 线级预算初始值（决策件 §4 草案；"
                               "P0 用量远低于）"},
            "token_ledger": [],
        }
    mutate(obj)
    write_canonical_json(p, obj)


def _log_step(root, step, payload):
    def _mut(o):
        o["steps"][step] = payload
    _progress(root, _mut)


def op_select(root="."):
    """走廊度量 + 选行（prereg v2 先冻结后计算）。"""
    ctx = P0Context(root)
    universe = extract_universe(ctx)
    if len(universe) != 43:
        raise V4fgP0Error("universe=%d != prereg expected 43" % len(universe))
    records = []
    for i, rid in enumerate(universe):
        row = ctx.rows_by_id[rid]
        protected = ctx.protected_for(row)
        win = corridor_window_for_row(row, ctx.board_bbox)
        with fine_grid_context():
            proj = WindowedProjection(ctx.board_text, win,
                                      net_table=ctx.net_table)
            blocked = proj.blocked_for(row["net"], protected=protected)
            corridor, per_layer = bottleneck_for_row(proj, row, blocked)
            ea = escape_radius_for_endpoint(proj, row["a"], blocked)
            eb = escape_radius_for_endpoint(proj, row["b"], blocked)
        del proj, blocked
        gc.collect()
        rec = {
            "row_id": rid, "net": row["net"],
            "row_signature": row["row_signature"],
            "corridor_halfwidth_mm": corridor,
            "bottleneck_per_layer_mm": per_layer,
            "escape_a_mm": ea, "escape_b_mm": eb,
            "escape_min_mm": round(min(ea, eb), 6),
            "window_mm": [round(v, 4) for v in win],
        }
        records.append(rec)
        if (i + 1) % 10 == 0 or i + 1 == len(universe):
            print("corridor %d/%d done (%s corridor=%.3f)"
                  % (i + 1, len(universe), rid, corridor), flush=True)
    widest, narrowest = select_rows_by_prereg(records)
    corridors = [r["corridor_halfwidth_mm"] for r in records]
    out = {
        "schema": "pcbflow.v4fg.p0-corridor/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "grid_mm": FINE_GRID_MM,
        "universe_rule_note": "A0-reason==astar_unreachable（43 行；与"
                              "报告 44 的口径差见 prereg report_discrepancy_note）",
        "rows": records,
        "summary": {
            "universe_count": len(records),
            "corridor_min": round(min(corridors), 6),
            "corridor_median": round(_median(corridors), 6),
            "corridor_max": round(max(corridors), 6),
            "corridor_ge_0p3": sum(1 for c in corridors if c >= 0.3),
            "corridor_ge_0p5": sum(1 for c in corridors if c >= 0.5),
        },
    }
    outd = _out_dir(root)
    write_canonical_json(outd / "corridor-metrics.json", out)
    sel = {
        "schema": "pcbflow.v4fg.p0-selection/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "universe_count": len(records),
        "widest_5": widest,
        "narrowest_5": narrowest,
        "selected_row_ids": sorted([r["row_id"] for r in widest]
                                   + [r["row_id"] for r in narrowest]),
    }
    write_canonical_json(outd / "row-selection.json", sel)
    _log_step(root, "select", {"status": "completed",
                               "universe_count": len(records),
                               "widest_5": [r["row_id"] for r in widest],
                               "narrowest_5": [r["row_id"] for r in narrowest]})
    return sel


def _barm_row(ctx, row):
    protected = ctx.protected_for(row)
    win = barm_window_for_row(row, ctx.board_bbox)
    # ---- 时延遍（tracemalloc 关）----
    with fine_grid_context():
        t0 = time.perf_counter()
        proj = WindowedProjection(ctx.board_text, win,
                                  net_table=ctx.net_table)
        blocked = proj.blocked_for(row["net"], protected=protected)
        build_s = time.perf_counter() - t0
        reps = []
        res_first = None
        for _i in range(_SOLVE_REPS):
            t0 = time.perf_counter()
            res = route_row(proj, row, blocked=blocked,
                            protected=protected)
            reps.append(time.perf_counter() - t0)
            if res_first is None:
                res_first = res
        solve_summary = _solve_summary(res_first)
        nx, ny = proj.world.nx, proj.world.ny
        layers_n = len(proj.copper)
        cells_per_layer = nx * ny
        del proj, blocked, res_first, res
        # ---- 内存遍（tracemalloc 开；前序对象已 del+gc）----
        def _full():
            p2 = WindowedProjection(ctx.board_text, win,
                                    net_table=ctx.net_table)
            b2 = p2.blocked_for(row["net"], protected=protected)
            r2 = route_row(p2, row, blocked=b2, protected=protected)
            return _solve_summary(r2)
        (_mem_summary, peak) = _run_with_peak(_full)
    return {
        "row_id": row["row_id"], "net": row["net"],
        "window_mm": [round(v, 4) for v in win],
        "window_cells_per_layer": cells_per_layer,
        "window_layers": layers_n,
        "build_s": round(build_s, 6),
        "solve_reps_s": [round(t, 6) for t in reps],
        "solve_median_s": round(_median(reps), 6),
        "solve": solve_summary,
        "tracemalloc_peak_mb": round(peak / (1024.0 * 1024.0), 3),
        "tracemalloc_note": "Windows 只计 Python 堆；栅格 set[tuple] 全计入",
    }


def _stage_cache(outd, key):
    """分段持久化（幂等续跑：环境杀长任务后按段恢复，测量协议不变）。"""
    return outd / ("%s.json" % key)


def _load_stage(outd, key):
    p = _stage_cache(outd, key)
    if p.is_file():
        try:
            return json.loads(p.read_bytes().decode("utf-8"))
        except Exception:
            return None
    return None


def _save_stage(outd, key, obj):
    write_canonical_json(_stage_cache(outd, key), obj)


def op_barm(root="."):
    """B 臂：10 选行逐行窗内 0.05mm A0 可达性/内存/时延实测。

    逐行结果即写 b-arm-rows/<rid>.json（幂等续跑——环境终止长任务后
    重启复用已完成行；测量协议每行不变，登记于 deviations）。
    """
    ctx = P0Context(root)
    outd = _out_dir(root)
    rows_dir = outd / "b-arm-rows"
    rows_dir.mkdir(parents=True, exist_ok=True)
    sel = json.loads((outd / "row-selection.json").read_bytes()
                     .decode("utf-8"))
    ids = sel["selected_row_ids"]
    recs = []
    for i, rid in enumerate(ids):
        cached = _load_stage(rows_dir, rid)
        if cached is not None:
            recs.append(cached)
            print("barm %d/%d %s (resumed)" % (i + 1, len(ids), rid),
                  flush=True)
            continue
        row = ctx.rows_by_id[rid]
        rec = _barm_row(ctx, row)
        write_canonical_json(rows_dir / ("%s.json" % rid), rec)
        recs.append(rec)
        print("barm %d/%d %s ok=%s median=%.3fs peak=%.1fMB"
              % (i + 1, len(ids), rid, rec["solve"]["ok"],
                 rec["solve_median_s"], rec["tracemalloc_peak_mb"]),
              flush=True)
    oks = [r for r in recs if r["solve"]["ok"]]
    out = {
        "schema": "pcbflow.v4fg.p0-barm/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "grid_mm": FINE_GRID_MM,
        "protocol_note": "A0 口径单射（无 layer_pref/waypoint）；protected="
                         "该行 E4 L2 批网集；时延=tracemalloc 关 3 次取"
                         "中位；内存=独立一遍 tracemalloc 开",
        "rows": recs,
        "summary": {
            "row_count": len(recs),
            "reachable": len(oks),
            "unreachable": len(recs) - len(oks),
            "reachability": round(len(oks) / float(len(recs)), 6)
            if recs else None,
            "reasons": sorted({r["solve"]["reason"] for r in recs}),
            "memory_peak_mb_max": round(max(
                (r["tracemalloc_peak_mb"] for r in recs), default=0.0), 3),
            "solve_median_s_max": round(max(
                (r["solve_median_s"] for r in recs), default=0.0), 6),
        },
    }
    write_canonical_json(outd / "b-arm.json", out)
    _log_step(root, "barm", {"status": "completed", **out["summary"]})
    return out


def _aarm_build(ctx, fine):
    """全板投影构建（时延遍 + 内存遍分开）。返回测量 dict。"""
    def _build():
        if fine:
            with fine_grid_context():
                proj = WindowedProjection(ctx.board_text,
                                          ctx.board_bbox,
                                          net_table=ctx.net_table)
                b = proj.blocked_for(_AARM_ROW_HOLDER["net"],
                                     protected=_AARM_ROW_HOLDER["prot"])
                return proj, b
        proj = WindowedProjection(ctx.board_text, ctx.board_bbox,
                                  net_table=ctx.net_table)
        b = proj.blocked_for(_AARM_ROW_HOLDER["net"],
                             protected=_AARM_ROW_HOLDER["prot"])
        return proj, b
    t0 = time.perf_counter()
    proj, blocked = _build()
    build_s = time.perf_counter() - t0
    cells = proj.world.nx * proj.world.ny
    dims = [proj.world.nx, proj.world.ny, len(proj.copper)]
    del proj, blocked
    gc.collect()
    def _build2():
        if fine:
            with fine_grid_context():
                p2 = WindowedProjection(ctx.board_text, ctx.board_bbox,
                                        net_table=ctx.net_table)
                return p2, p2.blocked_for(
                    _AARM_ROW_HOLDER["net"],
                    protected=_AARM_ROW_HOLDER["prot"])
        p2 = WindowedProjection(ctx.board_text, ctx.board_bbox,
                                net_table=ctx.net_table)
        return p2, p2.blocked_for(_AARM_ROW_HOLDER["net"],
                                  protected=_AARM_ROW_HOLDER["prot"])
    (_p2, _b2), peak = _run_with_peak(_build2)
    del _p2, _b2
    return {"grid_mm": FINE_GRID_MM if fine else COARSE_GRID_MM,
            "world_dims_cells": dims,
            "cells_total": cells * dims[2],
            "build_s": round(build_s, 6),
            "tracemalloc_peak_mb": round(peak / (1024.0 * 1024.0), 3),
            "tracemalloc_note": "Windows 只计 Python 堆；构建面"
                                "（parse+GridWorld+raster+blocked_for）"}


_AARM_ROW_HOLDER = {"net": None, "prot": ()}


def op_aarm(root="."):
    """A 臂：全板 0.25/0.05 投影成本 + 同行粗细 A* 时延 + 外推比。

    各段即写 a-arm-stages/（幂等续跑——环境终止长任务后按段恢复；
    测量协议不变，登记于 deviations）。
    """
    ctx = P0Context(root)
    outd = _out_dir(root)
    stg = outd / "a-arm-stages"
    stg.mkdir(parents=True, exist_ok=True)
    sel = json.loads((outd / "row-selection.json").read_bytes()
                     .decode("utf-8"))
    ids = sel["selected_row_ids"]
    rows = [ctx.rows_by_id[rid] for rid in ids]
    arow = min(rows, key=lambda r: (math.hypot(
        r["b"]["x"] - r["a"]["x"], r["b"]["y"] - r["a"]["y"]),
        r["row_id"]))
    protected = ctx.protected_for(arow)
    _AARM_ROW_HOLDER["net"] = arow["net"]
    _AARM_ROW_HOLDER["prot"] = protected
    print("aarm astar_row=%s net=%s" % (arow["row_id"], arow["net"]),
          flush=True)

    coarse_build = _load_stage(stg, "coarse-build")
    if coarse_build is None:
        coarse_build = _aarm_build(ctx, fine=False)
        _save_stage(stg, "coarse-build", coarse_build)
    print("coarse build done: %.1fs %.0fMB"
          % (coarse_build["build_s"],
             coarse_build["tracemalloc_peak_mb"]), flush=True)
    fine_build = _load_stage(stg, "fine-build")
    if fine_build is None:
        fine_build = _aarm_build(ctx, fine=True)
        _save_stage(stg, "fine-build", fine_build)
    print("fine build done: %.1fs %.0fMB"
          % (fine_build["build_s"], fine_build["tracemalloc_peak_mb"]),
          flush=True)

    # ---- A* 时延（同行粗；tracemalloc 关）----
    def _astar_measure_coarse():
        proj = WindowedProjection(ctx.board_text, ctx.board_bbox,
                                  net_table=ctx.net_table)
        blocked = proj.blocked_for(arow["net"], protected=protected)
        reps = []
        res0 = None
        for _i in range(_SOLVE_REPS):
            t0 = time.perf_counter()
            res = route_row(proj, row=arow, blocked=blocked,
                            protected=protected)
            reps.append(time.perf_counter() - t0)
            if res0 is None:
                res0 = res
        return _solve_summary(res0), _median(reps), reps

    coarse_astar = _load_stage(stg, "coarse-astar")
    if coarse_astar is None:
        s, m, reps = _astar_measure_coarse()
        coarse_astar = {"summary": s, "median_s": round(m, 6),
                        "reps_s": [round(t, 6) for t in reps]}
        _save_stage(stg, "coarse-astar", coarse_astar)
    print("coarse astar done: %s median=%.3fs"
          % (coarse_astar["summary"]["ok"], coarse_astar["median_s"]),
          flush=True)

    fine_astar = _load_stage(stg, "fine-astar")
    if fine_astar is None:
        # ---- 首对受控探针（FG-P0-003）：与 route_row 首对同源的
        # cand_a[0]×cand_b[0] 上直测 _astar2。可达 -> 完整 route_row
        # （首对即成功，快）；不可达 -> 单对口径如实报（49 对×全板
        # 穷尽不可行且不可中断，prereg astar_cap 条款的受控实现）。
        with fine_grid_context():
            proj = WindowedProjection(ctx.board_text, ctx.board_bbox,
                                      net_table=ctx.net_table)
            blocked = proj.blocked_for(arow["net"], protected=protected)
            t_probe0 = time.perf_counter()
            w = proj.world
            from .v4_1.solver2 import _astar2
            from .v4_1.e4revc import _layer_cost_fn
            allowed_sorted = sorted(w.layer_index[l]
                                    for l in proj.copper)
            ca = proj.endpoint_cells(arow["a"], blocked, allowed_sorted)
            own_a = proj.own_component_candidates(
                arow["net"], arow["a"], blocked, allowed_sorted,
                (arow["b"]["x"], arow["b"]["y"]))
            cb = proj.endpoint_cells(arow["b"], blocked, allowed_sorted)
            own_b = proj.own_component_candidates(
                arow["net"], arow["b"], blocked, allowed_sorted,
                (arow["a"]["x"], arow["a"]["y"]))
            cand_a = list(ca[:3]) + list(own_a[:4])
            cand_b = list(cb[:3]) + list(own_b[:4])
            cost = _layer_cost_fn(proj)
            probe = {"cand_pairs": len(cand_a) * len(cand_b)}
            if cand_a and cand_b:
                (_pa, _da, la, ax, ay, _atta) = cand_a[0]
                (_pb, _db, lb, bx, by, _attb) = cand_b[0]
                start = (ax, ay, w.layer_index[la])
                goal = (bx, by, w.layer_index[lb])
                t1 = time.perf_counter()
                seg, exp = _astar2(w, blocked, allowed_sorted, start,
                                   goal, False, cost)
                probe["first_pair_s"] = round(time.perf_counter() - t1, 6)
                probe["first_pair_ok"] = seg is not None
                probe["first_pair_nodes"] = exp
            else:
                probe["first_pair_ok"] = False
                probe["first_pair_s"] = 0.0
                probe["first_pair_nodes"] = 0
            probe["build_s"] = round(time.perf_counter() - t_probe0, 6)
            if probe.get("first_pair_ok"):
                # 可达 -> 完整 route_row（首对即成功）
                t1 = time.perf_counter()
                res = route_row(proj, row=arow, blocked=blocked,
                                protected=protected)
                fine_first = time.perf_counter() - t1
                fine_summary = _solve_summary(res)
                fine_reps = [fine_first]
                if fine_first <= _ASTAR_REP_THRESHOLD_S:
                    for _i in range(_SOLVE_REPS - 1):
                        t1 = time.perf_counter()
                        route_row(proj, row=arow, blocked=blocked,
                                  protected=protected)
                        fine_reps.append(time.perf_counter() - t1)
                build_part = probe["build_s"]
                fine_astar = {"summary": fine_summary,
                              "first_s": round(fine_first, 6),
                              "reps_s": [round(t, 6) for t in fine_reps],
                              "median_s": round(_median(fine_reps), 6),
                              "rep_policy": ("3 次取中位"
                                             if len(fine_reps) >= 3
                                             else "单次（>60s 不补测）"),
                              "build_s_in_context": round(build_part, 6),
                              "probe": probe}
            else:
                # 不可达 -> 单对口径（49 对×全板穷尽不可行；如实登记）
                fine_astar = {
                    "summary": {"ok": False,
                                "reason": "astar_unreachable",
                                "search_nodes": probe.get(
                                    "first_pair_nodes", 0)},
                    "first_s": probe.get("first_pair_s", 0.0),
                    "reps_s": [probe.get("first_pair_s", 0.0)],
                    "median_s": probe.get("first_pair_s", 0.0),
                    "rep_policy": "单对口径（首对 _astar2 直测；"
                                  "route_row 全候选环=不可达时 49 对×"
                                  "全板穷尽不可行，FG-P0-003）",
                    "build_s_in_context": probe["build_s"],
                    "probe": probe}
            del proj, blocked
        gc.collect()
        _save_stage(stg, "fine-astar", fine_astar)
    print("fine astar done: %s first=%s"
          % (fine_astar["summary"]["ok"], fine_astar["first_s"]),
          flush=True)

    def _ratio(a, b):
        if not b:
            return None
        return round(a / float(b), 3)

    out = {
        "schema": "pcbflow.v4fg.p0-aarm/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "astar_row": {"row_id": arow["row_id"], "net": arow["net"],
                      "row_signature": arow["row_signature"],
                      "endpoint_dist_mm": round(math.hypot(
                          arow["b"]["x"] - arow["a"]["x"],
                          arow["b"]["y"] - arow["a"]["y"]), 6)},
        "coarse_build": coarse_build,
        "fine_build": fine_build,
        "coarse_astar": coarse_astar,
        "fine_astar": fine_astar,
        "theoretical_cell_ratio": 25.0,
        "measured_ratios": {
            "cells": _ratio(fine_build["cells_total"],
                            coarse_build["cells_total"]),
            "memory_peak": _ratio(fine_build["tracemalloc_peak_mb"],
                                  coarse_build["tracemalloc_peak_mb"]),
            "build_s": _ratio(fine_build["build_s"],
                              coarse_build["build_s"]),
            "astar_median_s": _ratio(fine_astar["median_s"],
                                     coarse_astar["median_s"]),
            "astar_search_nodes": _ratio(
                fine_astar["summary"].get("search_nodes") or 0,
                coarse_astar["summary"].get("search_nodes") or 0),
        },
    }
    write_canonical_json(outd / "a-arm.json", out)
    _log_step(root, "aarm", {"status": "completed",
                             "astar_row": arow["row_id"],
                             "fine_build_mb": fine_build[
                                 "tracemalloc_peak_mb"],
                             "measured_ratios": out["measured_ratios"]})
    return out


def op_curves(root="."):
    """成本-可达性曲线 + S-FG1/S-FG2 定值依据（值本身 P1 prereg 冻结）。"""
    ctx = P0Context(root)
    outd = _out_dir(root)
    corridor = json.loads((outd / "corridor-metrics.json").read_bytes()
                          .decode("utf-8"))
    barm = json.loads((outd / "b-arm.json").read_bytes().decode("utf-8"))
    aarm = json.loads((outd / "a-arm.json").read_bytes().decode("utf-8"))
    by_id = {r["row_id"]: r for r in corridor["rows"]}

    points = []
    for r in barm["rows"]:
        c = by_id.get(r["row_id"], {})
        points.append({
            "row_id": r["row_id"],
            "point_kind": "b-arm-window",
            "cells_per_layer": r["window_cells_per_layer"],
            "build_s": r["build_s"],
            "tracemalloc_peak_mb": r["tracemalloc_peak_mb"],
            "solve_median_s": r["solve_median_s"],
            "ok": r["solve"]["ok"],
            "corridor_halfwidth_mm": c.get("corridor_halfwidth_mm"),
        })
    points.append({
        "point_kind": "a-arm-full-board-coarse",
        "cells_per_layer": aarm["coarse_build"]["world_dims_cells"][0]
        * aarm["coarse_build"]["world_dims_cells"][1],
        "build_s": aarm["coarse_build"]["build_s"],
        "tracemalloc_peak_mb": aarm["coarse_build"]["tracemalloc_peak_mb"],
        "solve_median_s": aarm["coarse_astar"]["median_s"],
        "ok": aarm["coarse_astar"]["summary"]["ok"],
    })
    points.append({
        "point_kind": "a-arm-full-board-fine",
        "cells_per_layer": aarm["fine_build"]["world_dims_cells"][0]
        * aarm["fine_build"]["world_dims_cells"][1],
        "build_s": aarm["fine_build"]["build_s"],
        "tracemalloc_peak_mb": aarm["fine_build"]["tracemalloc_peak_mb"],
        "solve_median_s": aarm["fine_astar"]["median_s"],
        "ok": aarm["fine_astar"]["summary"]["ok"],
    })

    reach = barm["summary"]
    oks = [r for r in barm["rows"] if r["solve"]["ok"]]
    # S-FG2 外推：43 行全域按分层样本可达率外推 committed rows 期望
    sample_reach = reach["reachability"]
    expected_rows = sample_reach * 43.0
    improvement_pct = 100.0 * expected_rows / 57.0
    mem_max = reach["memory_peak_mb_max"]
    lat_max = reach["solve_median_s_max"]
    fine_mb = aarm["fine_build"]["tracemalloc_peak_mb"]
    fine_astar_med = aarm["fine_astar"]["median_s"]

    threshold_basis = {
        "schema": "pcbflow.v4fg.p0-threshold-basis/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "note": "P0 只给定值依据与建议值；正式阈值由 P1 prereg 冻结",
        "s_fg1_cost": {
            "b_arm_observed": {
                "memory_peak_mb_max": mem_max,
                "solve_median_s_max": lat_max,
                "window_cells_per_layer_max": max(
                    (r["window_cells_per_layer"] for r in barm["rows"]),
                    default=0),
            },
            "a_arm_observed": {
                "full_board_fine_memory_mb": fine_mb,
                "full_board_fine_build_s": aarm["fine_build"]["build_s"],
                "full_board_fine_astar_median_s": fine_astar_med,
            },
            "suggested_values": {
                "sfg1_b_window_memory_mb_cap": round(mem_max * 2, 1),
                "sfg1_b_row_solve_s_cap": round(lat_max * 2, 1),
                "sfg1_a_full_board_memory_mb_cap": round(fine_mb * 2, 1),
                "derivation": "实测上包络 x2 安全系数（B 臂窗内存/单行"
                              "时延；A 臂全板内存）",
            },
        },
        "s_fg2_effectiveness": {
            "b_arm_reachability": sample_reach,
            "reachable_rows": reach["reachable"],
            "row_count": reach["row_count"],
            "extrapolation": {
                "universe_rows": 43,
                "expected_committed_rows": round(expected_rows, 2),
                "headless_unconnected_baseline": 57,
                "expected_improvement_pct": round(improvement_pct, 2),
                "pct_needed_for_10pct_band": round(
                    100.0 * 5.7 / 43.0, 2),
                "note": "10% 带=>=5.7 行=>=13.3% 全域可达率（B 臂样本"
                        "分层近似）；necessary-not-sufficient：窗内 A0 "
                        "可达!=实际 commit（预检/DRC/梯域在 P1）",
            },
            "honest_reading": ("若样本可达率低于 13.3% 阈，10% 带在"
                               "0.05mm 分辨率下已数学不可达——物理饱和"
                               "面主导，S-FG2 触发证据")
            if sample_reach < 5.7 / 43.0 else
            ("样本可达率高于 13.3% 数学阈——分辨率增益存在，P1 实测"
             "committed rows 判读"),
        },
        "decision_doc_ref": "exec/FINE-GRID-SOLVER-HOST-PROPOSAL-"
                            "2026-09-12.md §4（S-FG1/S-FG2 草案）",
    }
    curves = {
        "schema": "pcbflow.v4fg.p0-curves/1",
        "declared_date": DECLARED_DATE,
        "prereg_sha256": PREREG_SHA256,
        "cost_points": points,
        "cost_curve_reading": {
            "cells_vs_memory": "格数-内存（B 臂窗+全板两点粗细）",
            "cells_vs_build_s": "格数-构建时延",
            "cells_vs_solve_s": "格数-求解时延（窗中位；全板=astar_row）",
            "theoretical_cell_ratio_25": aarm["theoretical_cell_ratio"],
            "measured_ratios": aarm["measured_ratios"],
            "ratio_note": "实测比 vs 理论 25 的偏差=格子语义非线性"
                          "（阻挡集合基数量、A* 展开域、set 开销）",
        },
        "reachability_curve": [
            {"row_id": r["row_id"],
             "corridor_halfwidth_mm": r.get("corridor_halfwidth_mm"),
             "ok": r["ok"]}
            for r in points if r.get("row_id")
        ],
    }
    write_canonical_json(outd / "curves.json", curves)
    write_canonical_json(outd / "threshold-basis.json", threshold_basis)
    _log_step(root, "curves", {"status": "completed",
                               "b_arm_reachability": sample_reach,
                               "expected_improvement_pct": round(
                                   improvement_pct, 2)})
    return {"curves": curves, "threshold_basis": threshold_basis}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="pcbflow.v4fg_p0")
    ap.add_argument("op", choices=["select", "barm", "aarm", "curves"])
    ap.add_argument("--root", default=".")
    ns = ap.parse_args(argv)
    if ns.op == "select":
        rec = op_select(ns.root)
    elif ns.op == "barm":
        rec = op_barm(ns.root)
    elif ns.op == "aarm":
        rec = op_aarm(ns.root)
    else:
        rec = op_curves(ns.root)
    summary = {k: v for k, v in rec.items()
               if isinstance(v, (int, float, str, bool))}
    print("ok:", ns.op, json.dumps(summary, ensure_ascii=False)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
