# -*- coding: utf-8 -*-
"""protocol —— canvas-edit-v1 编辑协议 fail-closed ingest。

两层拒收:
- **格式层（整批拒收+原因码）**: JSON parse 失败/非对象/actions 非数组/未知
  动作/缺键/非整数格点/毫米坐标（浮点或字符串坐标渗透）/越界格点/未知网/
  未知层/waypoints<2/无 submit/round 不符/submit 后再有动作。词表=追加式
  （新码只增不改义）。
- **语义层（逐动作拒收, 其余照常应用）**: 几何/附着违例（验证核 v5.drc 同
  源判定, 见 verify.py）→ 该动作拒收+原因码, 批内后续动作继续。语义码是
  拒收直方图的数据源。

动作枚举（任务书钉死）: route(net_id, waypoints, layer) / via(net_id, grid) /
ripup(net_id | shape_id) / submit()。
"""
from . import verify

# ---- 格式层原因码（追加式词表; 已投用码不得改义）----
E_PARSE = "E_PARSE"                    # 非 JSON 文本
E_NOT_OBJECT = "E_NOT_OBJECT"          # 顶层非对象
E_ACTIONS_NOT_LIST = "E_ACTIONS_NOT_LIST"
E_ACTION_NOT_OBJECT = "E_ACTION_NOT_OBJECT"
E_UNKNOWN_ACTION = "E_UNKNOWN_ACTION"
E_MISSING_KEY = "E_MISSING_KEY"
E_EXTRA_KEY = "E_EXTRA_KEY"
E_NON_INTEGER_GRID = "E_NON_INTEGER_GRID"   # 非整数格点（含 bool 冒充）
E_FLOAT_COORD = "E_FLOAT_COORD"        # 毫米/浮点坐标渗透（值形如 126.16）
E_GRID_OUT_OF_BOUNDS = "E_GRID_OUT_OF_BOUNDS"
E_UNKNOWN_NET = "E_UNKNOWN_NET"
E_UNKNOWN_LAYER = "E_UNKNOWN_LAYER"
E_WAYPOINTS_TOO_FEW = "E_WAYPOINTS_TOO_FEW"
E_WAYPOINTS_NOT_LIST = "E_WAYPOINTS_NOT_LIST"
E_NO_SUBMIT = "E_NO_SUBMIT"            # 批内无 submit
E_TRAILING_ACTION = "E_TRAILING_ACTION"  # submit 后再有动作
E_ROUND_MISMATCH = "E_ROUND_MISMATCH"  # round 与画板当前轮不符
E_RIPUP_TARGET = "E_RIPUP_TARGET"      # ripup 既无 net_id 也无 shape_id / 二者同给

# ---- 语义层原因码（直方图源）----
V_CLEARANCE = "V_CLEARANCE"            # R5 间距违例（v5.drc.check_clearance）
V_EDGE = "V_EDGE"                      # 板边禁布（v5.drc.check_edge_clearance）
V_HOLE_TRACK = "V_HOLE_TRACK"          # 走线触板固孔（drc.hole_track_blocked 同式端点豁免）
V_HOLE_VIA = "V_HOLE_VIA"              # 过孔触板固孔（drc.hole_via_blocked 零豁免）
V_ENDPT_NOT_ATTACHED = "V_ENDPT_NOT_ATTACHED"  # 段首/末未附着（锚或 via）
V_VIA_OFF_PATH = "V_VIA_OFF_PATH"      # via 不在本网任何段 waypoint 上
V_RIPUP_UNKNOWN = "V_RIPUP_UNKNOWN"    # ripup 目标不存在
V_DUPLICATE_VIA = "V_DUPLICATE_VIA"    # 同网同格点 via 已在场
V_SELF_SNAG = "V_SELF_SNAG"            # 段展开后长度为零（同点往返）

REQUIRED_KEYS = {
    "route": ("net_id", "waypoints", "layer"),
    "via": ("net_id", "grid"),
    "ripup": (),
    "submit": (),
}
ALLOWED_KEYS = {
    "route": {"action", "net_id", "waypoints", "layer"},
    "via": {"action", "net_id", "grid"},
    "ripup": {"action", "net_id", "shape_id"},
    "submit": {"action"},
}


class BatchReject(Exception):
    """格式层整批拒收（code + 证据路径）。"""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _check_grid(v, path):
    """单格点 [i,j]: 必须二元整数列表; 拒毫米坐标渗透。"""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise BatchReject(E_NON_INTEGER_GRID, "%s 须为 [i,j] 二元（得到 %r）" % (path, v))
    for c in v:
        if isinstance(c, bool):
            raise BatchReject(E_NON_INTEGER_GRID, "%s 布尔冒充格点 %r" % (path, c))
        if isinstance(c, float):
            raise BatchReject(E_FLOAT_COORD, "%s 浮点坐标 %r（毫米坐标一律整批拒收）" % (path, c))
        if isinstance(c, str):
            raise BatchReject(E_FLOAT_COORD, "%s 字符串坐标 %r" % (path, c))
        if not isinstance(c, int):
            raise BatchReject(E_NON_INTEGER_GRID, "%s 非整数 %r" % (path, c))


def parse_batch(text, expected_round):
    """格式层校验: 文本 → 合法动作列表（整批拒收语义）。"""
    import json
    try:
        doc = json.loads(text)
    except Exception as exc:
        raise BatchReject(E_PARSE, "JSON 解析失败: %s" % (exc,))
    if not isinstance(doc, dict):
        raise BatchReject(E_NOT_OBJECT, "顶层须为对象")
    if doc.get("round") != expected_round:
        raise BatchReject(E_ROUND_MISMATCH,
                          "round=%r 期望 %r" % (doc.get("round"), expected_round))
    actions = doc.get("actions")
    if not isinstance(actions, list):
        raise BatchReject(E_ACTIONS_NOT_LIST, "actions 须为数组")
    out = []
    submitted = False
    for k, a in enumerate(actions):
        path = "actions[%d]" % k
        if not isinstance(a, dict):
            raise BatchReject(E_ACTION_NOT_OBJECT, "%s 须为对象" % path)
        act = a.get("action")
        if act not in REQUIRED_KEYS:
            raise BatchReject(E_UNKNOWN_ACTION, "%s 未知动作 %r" % (path, act))
        if submitted:
            raise BatchReject(E_TRAILING_ACTION, "%s 在 submit 之后" % path)
        extra = set(a) - ALLOWED_KEYS[act]
        if extra:
            raise BatchReject(E_EXTRA_KEY, "%s 合同外键 %s" % (path, sorted(extra)))
        missing = [key for key in REQUIRED_KEYS[act] if key not in a]
        if missing:
            raise BatchReject(E_MISSING_KEY, "%s 缺键 %s" % (path, sorted(missing)))
        if act == "route":
            wps = a["waypoints"]
            if not isinstance(wps, list):
                raise BatchReject(E_WAYPOINTS_NOT_LIST, "%s.waypoints 须为数组" % path)
            if len(wps) < 2:
                raise BatchReject(E_WAYPOINTS_TOO_FEW, "%s.waypoints<2" % path)
            for n, w in enumerate(wps):
                _check_grid(w, "%s.waypoints[%d]" % (path, n))
        elif act == "via":
            _check_grid(a["grid"], "%s.grid" % path)
        elif act == "ripup":
            if ("net_id" in a) == ("shape_id" in a):
                raise BatchReject(E_RIPUP_TARGET,
                                 "%s 须恰给 net_id 或 shape_id 之一" % path)
        out.append(a)
        if act == "submit":
            submitted = True
    if not submitted:
        raise BatchReject(E_NO_SUBMIT, "批内无 submit")
    return out


def apply_batch(state, actions, round_no):
    """语义层: 逐动作应用（verify 判定几何/附着）, 返回逐动作结果列表。

    结果元素: {index, action, accepted, shape_id?, code?, detail?}。

    **批内累积视图**（跨层链鸡生蛋解法: 段附着需 via 在场、via on-path
    又需段在场——链完整性是批级性质, 几何合法性是逐步性质）:
    - route 附着集 = 端点锚 ∪ 已落 via ∪ 批内全部 via 动作格点（同网）;
    - via on-path 集 = 已落段 waypoints ∪ 批内全部 route waypoints（同网）。
    几何验证仍按应用序逐条（先行接受项成为后续项的在场铜）。若被依赖的
    via/route 后续被几何拒收, 先行项成悬空铜（合法但不连通——探索负担
    归模型, facts 如实报 unrouted）。"""
    known_nets = {n["net_id"] for n in state.board["nets"]}
    batch_vias = {}      # net_id -> {grid}
    batch_route_pts = {}  # net_id -> {grid}
    for a in actions:
        if a["action"] == "via" and a["net_id"] in known_nets:
            g = tuple(a["grid"])
            if state.lattice.in_bounds(*g):
                batch_vias.setdefault(a["net_id"], set()).add(g)
        elif a["action"] == "route" and a["net_id"] in known_nets:
            batch_route_pts.setdefault(a["net_id"], set()).update(
                tuple(w) for w in a["waypoints"])
    results = []
    for idx, a in enumerate(actions):
        act = a["action"]
        if act == "submit":
            results.append({"index": idx, "action": act, "accepted": True})
            continue
        if act == "route":
            res = _apply_route(state, a, batch_vias)
        elif act == "via":
            res = _apply_via(state, a, batch_route_pts)
        else:
            res = _apply_ripup(state, a)
        res["index"] = idx
        res["action"] = act
        results.append(res)
    state.recompute_connectivity()
    state.gc_dangling_vias()
    state.recompute_connectivity()
    return results


def _apply_route(state, a, batch_vias=None):
    net_id = a["net_id"]
    layer = a["layer"]
    grid = [tuple(w) for w in a["waypoints"]]
    known_nets = {n["net_id"] for n in state.board["nets"]}
    if net_id not in known_nets:
        return {"accepted": False, "code": E_UNKNOWN_NET, "detail": net_id}
    if layer not in state.signal_layers():
        return {"accepted": False, "code": E_UNKNOWN_LAYER, "detail": layer}
    pids = state.net_partitions(net_id)
    pid = pids[0]
    for g in grid:
        if not state.lattice.in_bounds(*g):
            return {"accepted": False, "code": E_GRID_OUT_OF_BOUNDS,
                    "detail": list(g)}
    # 展开曼哈顿（instantiate 同源）
    from . import instantiate as inst
    expanded = inst.expand_waypoints(grid)
    if len(expanded) < 2:
        return {"accepted": False, "code": V_SELF_SNAG, "detail": "展开后零长"}
    # 附着纪律: 首/末 ∈ {端点锚} ∪ via 格点（已落 ∪ 批内）
    anchors = {tuple(x) for x in state.anchors[pid]}
    vias = set(state.via_grids(net_id))
    if batch_vias:
        vias |= batch_vias.get(net_id, set())
    h, t = expanded[0], expanded[-1]
    for pt, side in ((h, "head"), (t, "tail")):
        if pt not in anchors and pt not in vias:
            return {"accepted": False, "code": V_ENDPT_NOT_ATTACHED,
                    "detail": "%s %s 须为端点锚或本网 via 格点" % (side, list(pt))}
    # 验证核（v5.drc 同源; 候选+在场全场景）
    viols = verify.check_route_candidate(state, net_id, pid, layer, expanded)
    if viols:
        v = viols[0]
        return {"accepted": False, "code": v["code"], "detail": v["detail"]}
    seg = state.add_seg(net_id, pid, layer, [list(p) for p in expanded])
    return {"accepted": True, "shape_id": seg["shape_id"]}


def _apply_via(state, a, batch_route_pts=None):
    net_id = a["net_id"]
    grid = tuple(a["grid"])
    known_nets = {n["net_id"] for n in state.board["nets"]}
    if net_id not in known_nets:
        return {"accepted": False, "code": E_UNKNOWN_NET, "detail": net_id}
    if not state.lattice.in_bounds(*grid):
        return {"accepted": False, "code": E_GRID_OUT_OF_BOUNDS, "detail": list(grid)}
    if grid in state.via_grids(net_id):
        return {"accepted": False, "code": V_DUPLICATE_VIA, "detail": list(grid)}
    # on-path 纪律: 已落段 waypoints ∪ 批内 route waypoints（同网）
    on_path = any(
        any(tuple(p) == grid for p in s["grid"])
        for s in state.segs if s["net_id"] == net_id)
    if not on_path and batch_route_pts:
        on_path = grid in batch_route_pts.get(net_id, set())
    if not on_path:
        return {"accepted": False, "code": V_VIA_OFF_PATH, "detail": list(grid)}
    # 验证核: via 铜 vs 板固孔（零豁免）+ 场景 clearance/edge
    viols = verify.check_via_candidate(state, net_id, grid)
    if viols:
        v = viols[0]
        return {"accepted": False, "code": v["code"], "detail": v["detail"]}
    via = state.add_via(net_id, list(grid))
    return {"accepted": True, "shape_id": via["shape_id"]}


def _apply_ripup(state, a):
    if "net_id" in a:
        net_id = a["net_id"]
        known = {n["net_id"] for n in state.board["nets"]}
        if net_id not in known:
            return {"accepted": False, "code": E_UNKNOWN_NET, "detail": net_id}
        had = any(s["net_id"] == net_id for s in state.segs) or \
            any(v["net_id"] == net_id for v in state.vias)
        if not had:
            return {"accepted": False, "code": V_RIPUP_UNKNOWN, "detail": net_id}
        state.remove_net(net_id)
        return {"accepted": True, "removed": "net:%s" % net_id}
    sid = a["shape_id"]
    if not state.remove_shape(sid):
        return {"accepted": False, "code": V_RIPUP_UNKNOWN, "detail": sid}
    state.gc_dangling_vias()
    return {"accepted": True, "removed": sid}
