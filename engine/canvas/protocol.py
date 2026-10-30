# -*- coding: utf-8 -*-
"""canvas.protocol -- canvas-edit-v2 fail-closed ingest（合同 §1/§2 Lane-K1）。

两层拒收:
- **格式层（整批拒收, BatchReject）**: JSON parse 失败/非对象/actions 非数组/
  未知动作/缺键/合同外键/非整数格点/毫米坐标（浮点或字符串坐标渗透）/
  waypoints<2/无 submit/submit 后再有动作/round 不符/ripup 目标键非法/
  move.target 非格点/rotate.turns 非法。v1 原因码照合同词表原样实现
  （词表=追加式，新码只增不改义）。
- **语义层（逐动作拒收, 其余照常应用）**: 净/层/越界/附着/几何违例——
  判定归 canvas.validate（v5.drc 同源）；本件只定义码与归属。语义码是
  拒收直方图的数据源。

九动作枚举（合同 §2 钉死）: route/via/ripup/width_class/move/rotate/flip/
tuning/submit；REQUIRED/ALLOWED 键集严格照合同 §2 表格。

值域折算披露（合同词表无专属码处的就近归码，detail 全文说明）:
- waypoints 非数组 → E_NON_INTEGER_GRID（v1 的 E_WAYPOINTS_NOT_LIST 未入
  合同词表，折入非整数格点纪律码）;
- rotate.turns 非整数 → E_NON_INTEGER_GRID; turns∉{1,2,3} →
  E_GRID_OUT_OF_BOUNDS（值域越界码）。

tuning 动作不携带 grid（合同 §2 键集）: 基线折线=网首段（shape_id 序）的
已落段折线，由 apply 期推导入 state.tunings[].grid；group_id 语义（长度组
选段）冻结于 M5 激活跑 prereg。

循环 import（protocol→validate）用局部导入解。
"""

# ---- 格式层原因码（合同 §1 词表，追加式; 已投用码不得改义）----
E_PARSE = "E_PARSE"                    # 非 JSON 文本
E_NOT_OBJECT = "E_NOT_OBJECT"          # 顶层非对象
E_ACTIONS_NOT_LIST = "E_ACTIONS_NOT_LIST"
E_ACTION_NOT_OBJECT = "E_ACTION_NOT_OBJECT"
E_UNKNOWN_ACTION = "E_UNKNOWN_ACTION"
E_MISSING_KEY = "E_MISSING_KEY"
E_EXTRA_KEY = "E_EXTRA_KEY"
E_NON_INTEGER_GRID = "E_NON_INTEGER_GRID"   # 非整数格点（含 bool 冒充）
E_FLOAT_COORD = "E_FLOAT_COORD"        # 毫米/浮点/字符串坐标渗透
E_GRID_OUT_OF_BOUNDS = "E_GRID_OUT_OF_BOUNDS"
E_UNKNOWN_NET = "E_UNKNOWN_NET"
E_UNKNOWN_LAYER = "E_UNKNOWN_LAYER"
E_WAYPOINTS_TOO_FEW = "E_WAYPOINTS_TOO_FEW"
E_NO_SUBMIT = "E_NO_SUBMIT"            # 批内无 submit
E_TRAILING_ACTION = "E_TRAILING_ACTION"  # submit 后再有动作
E_ROUND_MISMATCH = "E_ROUND_MISMATCH"  # round 与画板当前轮不符
E_RIPUP_TARGET = "E_RIPUP_TARGET"      # ripup 既无 net_id 也无 shape_id / 二者同给

# ---- 语义层原因码（直方图源; v1 码语义原样保留）----
V_CLEARANCE = "V_CLEARANCE"            # R5 间距违例（v5.drc.check_clearance）
V_EDGE = "V_EDGE"                      # 板边禁布（v5.drc.check_edge_clearance）
V_HOLE_TRACK = "V_HOLE_TRACK"          # 走线触板固孔（drc.hole_track_blocked 同式端点豁免）
V_HOLE_VIA = "V_HOLE_VIA"              # 过孔触板固孔（drc.hole_via_blocked 零豁免）
V_ENDPT_NOT_ATTACHED = "V_ENDPT_NOT_ATTACHED"  # 段首/末未附着（锚或 via）
V_VIA_OFF_PATH = "V_VIA_OFF_PATH"      # via 不在本网任何段 waypoint 上
V_RIPUP_UNKNOWN = "V_RIPUP_UNKNOWN"    # ripup 目标不存在
V_DUPLICATE_VIA = "V_DUPLICATE_VIA"    # 同网同格点 via 已在场
V_SELF_SNAG = "V_SELF_SNAG"            # 段展开后长度为零（同点往返）

# ---- v2 追加语义码（合同 §2 各动作行）----
V_UNKNOWN_WIDTH_CLASS = "V_UNKNOWN_WIDTH_CLASS"  # class 不在板 netclass 词表
V_PLACEMENT_COLLISION = "V_PLACEMENT_COLLISION"  # 放置冲突（placecheck=M4 判定）
V_TUNING_KIND = "V_TUNING_KIND"        # kind 不在 {"accordion","detour"}
V_TUNING_PARAMS = "V_TUNING_PARAMS"    # 参数越界/非数/键集不符

# ---- 波2 接线追加码（编排体 2026-09-25; lane-m4 §5 接线契约 + lane-m5 §6 遗留;
#      追加式只增不改义，登记 D-CT-005/D-CT-006）----
E_UNKNOWN_PARTITION = "E_UNKNOWN_PARTITION"      # partition_id 不在 board.partitions
V_PLACEMENT_EDGE = "V_PLACEMENT_EDGE"            # 放置后分区出板框（placecheck）
V_KEEPOUT = "V_KEEPOUT"                          # 候选铜落入 R6 禁布区（编辑侧前置;
                                                  # 全态兜底=validate_full check_all→R6）

# ---- 席位简报拒收码表·单源（V8-PILOT-060 D-7, 2026-10-04）----
# 有序 tuple[(常量, 一句话语义)]，恰 9 码。语义文本以 PLAYBOOK-BRIEF v1.2
# 表为准迁移入内（v1.3 起 PLAYBOOK-BRIEF.md 码表节按本表刷新）; 消费面 =
# net_agent_pilot BRIEF_TEMPLATE 拒收码节渲染（自动补 v1.2 前缺失的
# V_HOLE_VIA）+ PLAYBOOK-BRIEF.md 漂移守卫测试（码集合全等 + 每码文本包含
# 表语义句）。本表只增不改义（词表纪律）; 语义描述性披露，判定零变更。
SEAT_REJECTION_CODES = (
    (V_CLEARANCE,
     "与他网铜间距 < 0.5mm（detail 形如 `seg:<net>:<id>|cand:seg gap=<v>`; "
     "其中 `<id>` 是全局 shape_id 计数、非网内段序——以坐标定位勿以序号; "
     "detail 还会追加 ` @cand=(x,y) vs (x2,y2)` 最近点对坐标=定位辅助，"
     "裁决仍以 gap 值为准）"),
    (V_EDGE, "走线贴板边（边带 0.2mm）"),
    (V_KEEPOUT, "走线/via 落入禁布区（地图上已投影为 #）"),
    (V_HOLE_TRACK, "走线压板固孔"),
    (V_HOLE_VIA, "via 压板固孔（对孔零豁免）"),
    (V_ENDPT_NOT_ATTACHED, "首末点不在端点锚/本网 via 格点上"),
    (V_SELF_SNAG, "路径展开后零长"),
    (V_DUPLICATE_VIA, "同格点重复放 via"),
    (V_VIA_OFF_PATH, "via 不在本网路径格点上"),
)

# ---- 九动作 REQUIRED/ALLOWED（合同 §2 表格严格照抄）----
REQUIRED_KEYS = {
    "route": ("net_id", "waypoints", "layer"),
    "via": ("net_id", "grid"),
    "ripup": (),
    "width_class": ("net_id", "class"),
    "move": ("partition_id", "target"),
    "rotate": ("partition_id", "turns"),
    "flip": ("partition_id",),
    "tuning": ("net_id", "group_id", "kind", "params"),
    "submit": (),
}
ALLOWED_KEYS = {
    "route": {"action", "net_id", "waypoints", "layer"},
    "via": {"action", "net_id", "grid"},
    "ripup": {"action", "net_id", "shape_id"},
    "width_class": {"action", "net_id", "class"},
    "move": {"action", "partition_id", "target"},
    "rotate": {"action", "partition_id", "turns"},
    "flip": {"action", "partition_id"},
    "tuning": {"action", "net_id", "group_id", "kind", "params"},
    "submit": {"action"},
}

ACTION_NAMES = tuple(sorted(REQUIRED_KEYS))


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
                raise BatchReject(E_NON_INTEGER_GRID,
                                  "%s.waypoints 须为 [[i,j],...] 数组（实得 %s）"
                                  % (path, type(wps).__name__))
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
        elif act == "move":
            _check_grid(a["target"], "%s.target" % path)
        elif act == "rotate":
            turns = a["turns"]
            if not _is_int(turns):
                raise BatchReject(E_NON_INTEGER_GRID,
                                  "%s.turns=%r 须为整数" % (path, turns))
            if turns not in (1, 2, 3):
                raise BatchReject(E_GRID_OUT_OF_BOUNDS,
                                  "%s.turns=%r 越界 {1,2,3}" % (path, turns))
        elif act == "tuning":
            if not isinstance(a["params"], dict):
                raise BatchReject(E_MISSING_KEY,
                                  "%s.params 须为平铺数值对象" % path)
        out.append(a)
        if act == "submit":
            submitted = True
    if not submitted:
        raise BatchReject(E_NO_SUBMIT, "批内无 submit")
    return out


# ---------------------------------------------------------------- 语义层

def tuning_base_grid(st, net_id):
    """tuning 基线折线（格点）: 网首段（shape_id 序）——合同 §2 tuning 动作
    不带 grid，基线由已落段推导；group 选段语义冻结于 M5 prereg。"""
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["net_id"] == net_id:
            return [list(p) for p in seg["grid"]]
    return []


def absolute_candidate(st, a):
    """协议相对动作（move target 绝格点 / rotate turns 相对 / flip 取反）
    → placecheck 绝对候选 dict（lane-m4 §5 接线契约折算式）。
    单源: validate_edit 与 apply_batch 两面消费同一折算，防漂移。"""
    cur = st.placement(a["partition_id"])
    act = a["action"]
    if act == "move":
        return {"move": list(a["target"])}
    if act == "rotate":
        return {"rotate": (int(cur["rotate"]) + int(a["turns"])) % 4}
    if act == "flip":
        return {"flip": not bool(cur["flip"])}
    raise ValueError("非放置动作 %r" % (act,))


def _build_batch_ctx(st, actions, expand_routes=False):
    """构造批内 route/via 视图。

    旧 ``apply_batch`` 保持原始 waypoint 口径；M2R3 一致性入口显式使用
    ``expand_routes=True``，使跳跃 route 的中间制造格点也能成为 via 的
    前向引用目标。该差异是显式 mode，而不是静默改变旧世界。
    """
    from . import instantiate as inst
    known_nets = st.known_nets()
    batch_vias = {}
    batch_route_pts = {}
    for a in actions:
        act = a.get("action")
        if act == "via" and a.get("net_id") in known_nets \
                and st.lattice.in_bounds(*a["grid"]):
            batch_vias.setdefault(a["net_id"], set()).add(tuple(a["grid"]))
        elif act == "route" and a.get("net_id") in known_nets:
            points = a["waypoints"]
            if expand_routes:
                points = inst.expand_waypoints(points)
            pts = {tuple(w) for w in points if st.lattice.in_bounds(*w)}
            batch_route_pts.setdefault(a["net_id"], set()).update(pts)
    return {"via_grids": batch_vias, "route_pts": batch_route_pts}


def _apply_batch_with_ctx(st, actions, batch_ctx):
    """单次批施加核心；调用者负责选择 legacy 或 consistent ctx。"""
    from . import validate
    results = []
    for idx, a in enumerate(actions):
        act = a["action"]
        if act == "submit":
            results.append({"index": idx, "action": act, "accepted": True})
            continue
        accepted, code, detail = validate.validate_edit(st, a, batch_ctx)
        if not accepted:
            results.append({"index": idx, "action": act, "accepted": False,
                            "code": code, "detail": detail})
            continue
        if act == "route":
            from . import instantiate as inst
            net_id = a["net_id"]
            pid = st.net_partitions(net_id)[0]
            cls = st.widths.get(net_id, validate.default_width_class(st))
            expanded = inst.expand_waypoints(a["waypoints"])
            if len(expanded) == 1:
                # 同锚重合退化网零长 route（D-CT-022 合法化）。
                expanded = [expanded[0], expanded[0]]
            seg = st.add_seg(net_id, pid, a["layer"], expanded, cls)
            results.append({"index": idx, "action": act, "accepted": True,
                            "shape_id": seg["shape_id"]})
        elif act == "via":
            via = st.add_via(a["net_id"], a["grid"])
            results.append({"index": idx, "action": act, "accepted": True,
                            "shape_id": via["shape_id"]})
        elif act == "ripup":
            if "net_id" in a:
                st.remove_net(a["net_id"])
                results.append({"index": idx, "action": act, "accepted": True,
                                "removed": "net:%s" % a["net_id"]})
            else:
                # 孤儿 via 回收延迟到批末；三连 GC 保持旧协议语义。
                st.remove_shape(a["shape_id"])
                results.append({"index": idx, "action": act, "accepted": True,
                                "removed": a["shape_id"]})
        elif act == "width_class":
            st.set_width_class(a["net_id"], a["class"])
            results.append({"index": idx, "action": act, "accepted": True,
                            "width_class": a["class"]})
        elif act == "tuning":
            grid = tuning_base_grid(st, a["net_id"])
            tun = st.add_tuning(a["net_id"], a["group_id"], a["kind"],
                                grid, a["params"])
            results.append({"index": idx, "action": act, "accepted": True,
                            "shape_id": tun["shape_id"]})
        else:
            from . import placecheck as _pc
            cand = absolute_candidate(st, a)
            cov = _pc.merge_candidate(st.placements, a["partition_id"], cand)
            st.set_placement(a["partition_id"], move=cov["move"],
                             rotate=cov["rotate"], flip=cov["flip"])
            results.append({"index": idx, "action": act, "accepted": True,
                            "partition_id": a["partition_id"],
                            "placement": {"move": cov["move"],
                                          "rotate": cov["rotate"],
                                          "flip": cov["flip"]}})
    st.recompute_connectivity()
    st.gc_dangling_vias()
    st.recompute_connectivity()
    return results


def apply_batch(st, actions, round_no=None):
    """语义层 legacy 批施加，保持 K1/M2/M3/M5 历史口径。"""
    return _apply_batch_with_ctx(st, actions, _build_batch_ctx(st, actions))


def _reorder_indexed(indexed):
    """只在 route/via 区段内排序；强连通分量内部保持原序。"""
    from . import instantiate as inst
    out = []

    def flush(segment):
        if not segment:
            return
        edges = {i: set() for i in range(len(segment))}
        paths = {}
        for i, (_orig, action) in enumerate(segment):
            if action.get("action") == "route":
                paths[i] = [tuple(p) for p in inst.expand_waypoints(
                    action["waypoints"])]
        for i, (_orig, action) in enumerate(segment):
            for j, (_other, candidate) in enumerate(segment):
                if i == j or action.get("net_id") != candidate.get("net_id"):
                    continue
                if action.get("action") == "route" and candidate.get("action") == "via":
                    if tuple(candidate["grid"]) in paths[i]:
                        edges[i].add(j)
                elif action.get("action") == "via" and candidate.get("action") == "route":
                    path = paths[j]
                    if path and tuple(action["grid"]) in (path[0], path[-1]):
                        edges[i].add(j)

        counter = [0]
        numbers, low, stack, stacked, components = {}, {}, [], set(), []

        def visit(node):
            numbers[node] = low[node] = counter[0]
            counter[0] += 1
            stack.append(node)
            stacked.add(node)
            for nxt in sorted(edges[node]):
                if nxt not in numbers:
                    visit(nxt)
                    low[node] = min(low[node], low[nxt])
                elif nxt in stacked:
                    low[node] = min(low[node], numbers[nxt])
            if low[node] == numbers[node]:
                component = []
                while True:
                    member = stack.pop()
                    stacked.remove(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(sorted(component))

        for i in range(len(segment)):
            if i not in numbers:
                visit(i)
        belongs = {node: ci for ci, component in enumerate(components)
                   for node in component}
        dag = {ci: set() for ci in range(len(components))}
        indegree = {ci: 0 for ci in dag}
        for node, neighbors in edges.items():
            for nxt in neighbors:
                src, dst = belongs[node], belongs[nxt]
                if src != dst and dst not in dag[src]:
                    dag[src].add(dst)
                    indegree[dst] += 1
        remaining = set(dag)
        while remaining:
            ready = [ci for ci in remaining if indegree[ci] == 0]
            if not ready:
                raise RuntimeError("M2R3 批依赖图缩并后仍成环")
            ci = min(ready, key=lambda k: min(components[k]))
            out.extend(segment[i] for i in components[ci])
            remaining.remove(ci)
            for nxt in dag[ci]:
                indegree[nxt] -= 1

    segment = []
    for item in indexed:
        if item[1].get("action") in {"route", "via"}:
            segment.append(item)
        else:
            flush(segment)
            segment = []
            out.append(item)
    flush(segment)
    return out


def reorder_batch(actions):
    """返回确定性深拷贝；非 route/via 动作和 submit 是 barrier。"""
    import copy as _copy
    return [action for _idx, action in _reorder_indexed(
        [(i, _copy.deepcopy(a)) for i, a in enumerate(actions)])]


def _grid_on_existing_path(st, net_id, grid):
    g = tuple(grid)
    return any(any(tuple(p) == g for p in s["grid"])
               for s in st.segs.values() if s["net_id"] == net_id) or any(
           any(tuple(p) == g for p in t["grid"])
           for t in st.tunings.values() if t["net_id"] == net_id)


def _cascade_dependencies(st, active, result_by_orig):
    """返回 (orig_index -> forced rejection) 的单调 route/via 级联集合。"""
    from . import instantiate as inst
    accepted = {idx for idx, r in result_by_orig.items()
                if r.get("accepted") is True and r.get("action") != "submit"}
    accepted_vias = {}
    accepted_routes = {}
    for idx, action in active:
        if idx not in accepted:
            continue
        net = action.get("net_id")
        if action.get("action") == "via":
            accepted_vias.setdefault((net, tuple(action["grid"])), set()).add(idx)
        elif action.get("action") == "route":
            accepted_routes[idx] = (net, [tuple(p) for p in
                                          inst.expand_waypoints(action["waypoints"])])
    existing_vias = {net: set(st.via_grids(net)) for net in st.known_nets()}
    forced = {}
    for idx, action in active:
        if idx not in accepted:
            continue
        act = action.get("action")
        net = action.get("net_id")
        if act == "route":
            pts = accepted_routes[idx][1]
            anchors = {tuple(p) for pid in st.net_partitions(net)
                       for p in st.effective_anchors(pid)}
            missing = []
            for endpoint in (pts[0], pts[-1]):
                if endpoint in anchors or endpoint in existing_vias.get(net, set()):
                    continue
                if not accepted_vias.get((net, endpoint)):
                    missing.append(list(endpoint))
            if missing:
                forced[idx] = {"index": idx, "action": act,
                                "accepted": False,
                                "code": V_ENDPT_NOT_ATTACHED,
                                "detail": "批内 via 未落地，端点缺少存活附着: %s" % missing}
        elif act == "via":
            grid = tuple(action["grid"])
            if _grid_on_existing_path(st, net, grid):
                continue
            carrier = any(net == rnet and grid in set(points)
                          for _rid, (rnet, points) in accepted_routes.items())
            if not carrier:
                forced[idx] = {"index": idx, "action": act,
                                "accepted": False,
                                "code": V_VIA_OFF_PATH,
                                "detail": "批内载体 route 未落地，via 不在存活路径上: %s"
                                          % (list(grid),)}
    return forced


def _copy_consistent_state(dst, src):
    import copy as _copy
    for name in ("segs", "vias", "widths", "placements", "tunings",
                 "_seg_seq", "_tun_seq", "connectivity", "chain_detail"):
        setattr(dst, name, _copy.deepcopy(getattr(src, name)))


def apply_consistent_batch(st, actions, round_no=None):
    """M2R3 一致性批施加：重排、整批 ctx、固定点和单次提交。

    所有试演在 base 深拷贝上进行，避免 ``_seg_seq``/``_tun_seq`` 污染真实态。
    结果按原输入 index 返回；调用者可用 :func:`reorder_batch` 取得 ledger
    的实际执行序列。旧 ``apply_batch`` 保持 legacy 语义不变。
    """
    import copy as _copy
    original = [_copy.deepcopy(a) for a in actions]
    ordered = _reorder_indexed(list(enumerate(original)))
    base = _copy.deepcopy(st)
    active = list(ordered)
    last_rejections = {}
    final_trial = None
    final_results = {}
    max_iter = max(1, len(active) + 1)
    for _iteration in range(max_iter):
        trial = _copy.deepcopy(base)
        trial_actions = [a for _idx, a in active]
        ctx = _build_batch_ctx(trial, trial_actions, expand_routes=True)
        raw_results = _apply_batch_with_ctx(trial, trial_actions, ctx)
        by_orig = {active[r["index"]][0]: dict(r) for r in raw_results}
        for idx, r in by_orig.items():
            if not r.get("accepted"):
                last_rejections[idx] = dict(r)
        forced = _cascade_dependencies(base, active, by_orig)
        remove = {idx for idx, r in by_orig.items() if not r.get("accepted")}
        remove.update(forced)
        if not remove:
            final_trial = trial
            final_results = by_orig
            break
        for idx, r in forced.items():
            last_rejections[idx] = r
        active = [(idx, a) for idx, a in active if idx not in remove]
    else:
        raise RuntimeError("M2R3 batch fixed-point 未收敛（fail-closed，真实态未改）")

    _copy_consistent_state(st, final_trial)
    out = []
    for idx, action in enumerate(original):
        if action.get("action") == "submit":
            out.append({"index": idx, "action": "submit", "accepted": True})
        elif idx in final_results:
            out.append(dict(final_results[idx], index=idx))
        elif idx in last_rejections:
            out.append(dict(last_rejections[idx], index=idx,
                            action=action.get("action"), accepted=False))
        else:
            out.append({"index": idx, "action": action.get("action"),
                        "accepted": False, "code": V_ENDPT_NOT_ATTACHED,
                        "detail": "一致性批施加未产生确定性结果"})
    return out
