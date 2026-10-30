# -*- coding: utf-8 -*-
"""verify —— 验证核: 直接调用 v5.drc 同源函数族判定候选编辑合法性。

禁止平行实现（已裁架构原则: 画板规范=门规范同语义）。同源绑定面:
- v5.drc.Copper / check_clearance（R5, same_net_exempt=True 同网豁免,
  返回 (violations, checked)）/ check_edge_clearance（D6-3 板边 0.2mm 带）
- v5.drc.normalize_holes / hole_track_blocked（track face; 端点豁免=孔心
  与本分区端点重合, route_check._hole_violations 与 executor.edge_blocked
  同式同豁免）/ hole_via_blocked（via face, 零豁免）
- v5.kicad_export.via_model_params（via 几何单源）; 线宽 0.3=引擎基线约定
  （badgeleds/pmod-bme280 基线 routes 全 0.3, prereg 冻结）。

候选归责=**差集法**: base 场景（在场铜）违例键集合 vs full 场景（含候选）
违例键集合, 新增违例=候选引入（板固有 pad 贴边/板固孔对在 base 已在、不
归责候选——与 route_check「板内固有缺陷不归责 routes」纪律同构）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..")))

from v5 import drc  # noqa: E402  同源绑定核心
from v5.metrics import clearance as _cl  # noqa: E402
from v5.kicad_export import via_model_params  # noqa: E402

WIDTH_MM = 0.3
HALF_WIDTH = WIDTH_MM / 2.0


def endpoint_mm(board, pid):
    for p in board["partitions"]:
        if p["partition_id"] == pid:
            return [(float(e[0]), float(e[1]))
                    for e in p["geometry"]["endpoints"]]
    raise KeyError(pid)


def _pad_coppers(state):
    """板固焊盘铜（固定面; route_check._PadCopper 同形态: circle→pad 圆,
    rect→band; layers=all → 每信号层一枚; 仅显式 pad_terminals 入场景）。"""
    layers = state.signal_layers()
    out = []
    for p in state.board["partitions"]:
        pid = p["partition_id"]
        items = p["geometry"].get("pad_terminals") or []
        if not items:
            continue
        eps = endpoint_mm(state.board, pid)
        for net in state.board["nets"]:
            if pid not in net["partitions"]:
                continue
            for item in items:
                center = eps[item["endpoint"]]
                for layer in layers:
                    cid = "pad:%s:%d" % (pid, item["endpoint"])
                    if item["shape"] == "circle":
                        cu = drc.Copper(net["net_id"], cid, layer,
                                        pad=(center, float(item["size_mm"][0]) / 2.0))
                    else:
                        hw = float(item["size_mm"][0]) / 2.0
                        hh = float(item["size_mm"][1]) / 2.0
                        cu = drc.Copper(net["net_id"], cid, layer,
                                        band=(center[0] - hw, center[1] - hh,
                                              center[0] + hw, center[1] + hh))
                    cu.partition_id = pid
                    cu.is_pad_terminal = True
                    out.append(cu)
    return out


def _seg_copper(state, seg):
    from . import instantiate as inst
    pts, _stub = inst.segment_mm(state, seg)
    cu = drc.Copper(seg["net_id"], seg["shape_id"], seg["layer"],
                    polyline=[(float(p[0]), float(p[1])) for p in pts],
                    half_width=HALF_WIDTH)
    cu.partition_id = seg["partition_id"]
    return cu


def _via_coppers(state, vias=None):
    layers = state.signal_layers()
    r = via_model_params(state.board)["radius"]
    out = []
    for v in (state.vias if vias is None else vias):
        mm = state.lattice.to_mm(*v["grid"])
        for layer in layers:
            cu = drc.Copper(v["net_id"], v["shape_id"], layer, pad=(mm, r))
            cu.partition_id = None
            cu.is_via = True
            out.append(cu)
    return out


def _scene(state, extra_coppers=()):
    coppers = _pad_coppers(state)
    for s in state.segs:
        coppers.append(_seg_copper(state, s))
    coppers.extend(_via_coppers(state))
    coppers.extend(extra_coppers)
    return coppers


def _vkey(v):
    return (v.rule, str(v.subject_a), str(v.subject_b),
            json.dumps(v.data, sort_keys=True))


def ws_tuple(board):
    """workspace dict → (x0,y0,x1,y1) 元组（route_check._BoardView 同形态）。"""
    ws = board["workspace"]
    return (float(ws["x_min"]), float(ws["y_min"]),
            float(ws["x_max"]), float(ws["y_max"]))


def _viol_keys(coppers, state):
    """场景 → (R5+edge 违例键集合, R5 违例列表)。"""
    ws = ws_tuple(state.board)
    r5v, _checked = drc.check_clearance(
        coppers, state.board["hard_rules"]["R5"]["min_clearance_mm"],
        same_net_exempt=True)
    edgev = drc.check_edge_clearance(coppers, ws)
    keys = set(_vkey(v) for v in r5v) | set(_vkey(v) for v in edgev)
    return keys, r5v, edgev


def _new_violations(state, extra_coppers):
    base_keys, _b5, _be = _viol_keys(_scene(state), state)
    full_keys, f5, fe = _viol_keys(_scene(state, extra_coppers), state)
    new_keys = full_keys - base_keys
    if not new_keys:
        return []
    for v in list(f5) + list(fe):
        if _vkey(v) in new_keys:
            rule = v.rule
            if rule == "R5":
                return [{"code": "V_CLEARANCE",
                         "detail": "%s|%s gap=%s" % (v.subject_a, v.subject_b,
                                                     v.data.get("gap_mm"))}]
            return [{"code": "V_EDGE",
                     "detail": "%s pos=%s" % (v.subject_a, v.data.get("pos"))}]
    return [{"code": "V_CLEARANCE", "detail": "unattributed new violation"}]


def _hole_exempt(board, pid):
    """端点豁免孔索引（route_check 同式: 孔心与本分区任一端点重合 EPS 内）。"""
    eps = endpoint_mm(board, pid)
    holes = drc.normalize_holes(board.get("holes"))
    exempt = set()
    for hi, (hx, hy, _hr) in enumerate(holes):
        for ex, ey in eps:
            if abs(hx - ex) <= _cl.EPS and abs(hy - ey) <= _cl.EPS:
                exempt.add(hi)
                break
    return exempt


def check_route_candidate(state, net_id, pid, layer, expanded):
    """候选段（格点展开序）→ 违例 dict 列表（空=合法, 可落铜）。"""
    from . import instantiate as inst
    holes = drc.normalize_holes(state.board.get("holes"))
    exempt = _hole_exempt(state.board, pid)
    fake = {"shape_id": "cand:seg", "net_id": net_id, "partition_id": pid,
            "layer": layer, "grid": [list(p) for p in expanded]}
    pts, _stub = inst.segment_mm(state, fake)
    for hi, (hx, hy, hr) in enumerate(holes):
        if hi in exempt:
            continue
        for a, b in zip(pts[:-1], pts[1:]):
            if drc.hole_track_blocked((hx, hy), hr, a, b, HALF_WIDTH):
                return [{"code": "V_HOLE_TRACK",
                         "detail": "hole:%d seg %s-%s" % (hi, a, b)}]
    cand = _seg_copper(state, fake)
    return _new_violations(state, [cand])


def check_via_candidate(state, net_id, grid):
    """候选 via → 违例 dict 列表（孔零豁免 + 差集归责）。"""
    holes = drc.normalize_holes(state.board.get("holes"))
    vm = via_model_params(state.board)
    mm = state.lattice.to_mm(*grid)
    for hi, (hx, hy, hr) in enumerate(holes):
        if drc.hole_via_blocked((hx, hy), hr, mm, vm["radius"]):
            return [{"code": "V_HOLE_VIA", "detail": "hole:%d at %s" % (hi, list(grid))}]
    fake = {"shape_id": "cand:via", "net_id": net_id, "grid": list(grid)}
    return _new_violations(state, _via_coppers(state, [fake]))


def full_check(state):
    """终态全量复核（G-CP 面）: 与候选判定同一函数族, 双保险。"""
    scene = _scene(state)
    ws = ws_tuple(state.board)
    r5v, _checked = drc.check_clearance(
        scene, state.board["hard_rules"]["R5"]["min_clearance_mm"],
        same_net_exempt=True)
    out = list(r5v)
    out.extend(drc.check_edge_clearance(scene, ws))
    return out
