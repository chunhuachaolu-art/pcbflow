# -*- coding: utf-8 -*-
"""canvas.runners.m2 -- 粗布 runner（确定性算法布线器；合同 §1 波2 Lane-M2X）。

两层 API:
- ``plan_actions(st, budget) -> [action dicts]``: 对未连通网生成 canvas-edit-v2
  动作批（route/via/width_class/ripup；末批由 run_m2 补 submit 成协议批形态）。
  纯函数性: 不改传入 st（内部在 deepcopy 副本上演进；st.state_sha256 前后不变）。
- ``run_m2(st, budget) -> summary dict``: plan → ``canvas.protocol.apply_batch``
  应用 → 摘要（canonical_json 可直落，v5.canonical 同源）。

能力四件（任务书钉死）:
1. **多层布线**: 候选层序=stackup available 信号层自「网序偏移+链跳序」轮转
   （net k 首跳层=layers[k % n]，链内每跳顺次轮转一层）；跨层段衔接点按画板
   纪律强制 via 在场——衔接 via 与跳段同批原子试放（候选因 via 被拒=整候选
   被拒），轮转层序天然含「钉回前跳层」的同层衔接变体（同层衔接经端点锚
   附着，无需 via）。
2. **netclass 宽度强制**: 本 runner 规划的每网首动作=width_class（词表单源=
   ``canvas.validate.width_class_vocab``；选档=网内分区 max(current_a)==0→
   "min" 否则 "nom"，缺省保守）。已连通网整体不动（不重印宽度——width_class
   语义层不查几何，重印既有段可能未验证加宽；策略披露）。
3. **批量 ripup**: 规划网自身残段先 net 级 ripup 清场（net_id 寻址）；候选
   全败时经 ``validate_full`` 差集归责定位阻塞铜（新增违例对中非候选方
   主体），对可拆主体逐枚 **shape_id 寻址** ripup（seg:/via:；pad/hole/edge
   不可拆→换候选），每被拆网守卫至多 per_net_retry 枚（防乒乓）。
4. **过孔成本打包事实**: ``summary["via_cost_facts"]``（结构见 run_m2
   docstring 钉死）——runner 自有输出，不改 canvas/pack.py（K2 域文件）。

算法=确定性贪心顺序扫（无随机源、无搜索引擎、无 time/dict 序渗入）:
网按 net_id 字典序逐轮扫；每网端点锚（placement 覆盖后）排序成链，逐跳依
固定候选序试放，首个经 apply_batch 全受的候选即落（贪心不回溯）。候选序
（钉死）: ①单层 L 形直连（x-first → y-first × 轮转层序）②跨层 via 角过渡
（有序层对 × 两角）③k 步 U 形平行避障绕行（整条走廊平移 k 格: 走廊主轴=
|dx|>=|dy| 取水平，先绕垂直向再绕水平向）④k 步 Z 形换轴绕行（中段单列
c=b.i±k、a.i±k / 单行 r=b.j±k、a.j±k 直插——解开 ③ 无法移动端点腿的钉
腿阻塞）⑤⑥k 步门外折返阶梯（端点先向背离对端方向退出 k 再换轴门户——
解开端点邻域被非豁免板固孔钳死的死局; 偏移只取外向，列 c∈{a.i∓k,
b.i±k} × 行 r∈{a.j∓k,b.j±k} 4 组合; ⑤ 行门户/⑥ 列门户）。k=1..
per_net_retry × 符号 -1/+1（⑤⑥ 向外方向由 a/b 相对位置定）× 轮转层序;
跨族同 waypoint 序同层去重。跳无候选可落=该网本轮 unresolved（如实上
报；max_rounds 轮内重试）。一切几何/违例判定经
canvas.validate / v5.drc 同源（候选试放=副本上真 apply_batch；阻塞归责=
validate_full 差集），本件零平行几何实现。拆段重试扫描跳过首轮已判
"不可拆码"（V_HOLE_*/V_EDGE/E_*/附着类——他网拆段不改变其结局，确定性
等价省扫）。

budget 形态（钉死）::
    {"max_rounds": int>=1, "per_net_retry": int>=1}
- ``max_rounds``: 全网顺序扫轮数上限（后续轮重试上轮 unresolved/被拆网）；
- ``per_net_retry``: 一钮三用封顶——每跳 U 绕行深度 k 上限、每跳阻塞拆段
  重试次数上限、每被拆网被拆守卫上限。
缺省 ``DEFAULT_BUDGET={"max_rounds":3, "per_net_retry":6}``——激活跑 prereg
冻结值（修订须编排体发修订节）。非法 budget（非 dict/键集不符/非 int/bool
冒充/<1）一律 ValueError fail-closed，不静默收敛。
"""
import copy

from canvas import instantiate as cinst
from canvas import protocol as cproto
from canvas import validate as cval
from canvas.state import state_sha256
from v5.canonical import canonical_json

RUNNER_ID = "canvas-runners-m2/1.0.0"

#: 激活跑 prereg 冻结缺省预算（修订须编排体发修订节）
DEFAULT_BUDGET = {"max_rounds": 3, "per_net_retry": 6}

#: via 抽象成本单位（via_cost_model 披露常量；贪心候选序已按少 via 优先）
VIA_UNIT_COST = 10

_BUDGET_KEYS = ("max_rounds", "per_net_retry")


# ---------------------------------------------------------------- budget

def _normalize_budget(budget):
    if budget is None:
        budget = DEFAULT_BUDGET
    if not isinstance(budget, dict):
        raise ValueError("budget 须为 dict（得到 %r）" % (type(budget).__name__,))
    if set(budget) != set(_BUDGET_KEYS):
        raise ValueError("budget 键集须= %s（实得 %s）"
                         % (list(_BUDGET_KEYS), sorted(budget)))
    out = {}
    for key in _BUDGET_KEYS:
        v = budget[key]
        if isinstance(v, bool) or not isinstance(v, int) or v < 1:
            raise ValueError("budget[%s]=%r 须为 >=1 整数" % (key, v))
        out[key] = int(v)
    return out


# ---------------------------------------------------------------- 确定性小件

def _net_width_class(st, net_id):
    """选档（确定性）: 网内分区 max(current_a)==0 → "min"（≥R1.floor 的
    保守档），否则 "nom"。词表成员性由 width_class_vocab 保证（min/nom 恒在）。"""
    currents = []
    for pid in st.net_partitions(net_id):
        part = st.board_partition(pid)
        if part is not None:
            try:
                ca = part.get("current_a", 0)
            except AttributeError:
                ca = 0
            if isinstance(ca, (int, float)) and not isinstance(ca, bool):
                currents.append(float(ca))
    return "min" if not currents or max(currents) == 0.0 else "nom"


def _net_has_copper(st, net_id):
    return (any(s["net_id"] == net_id for s in st.segs.values())
            or any(v["net_id"] == net_id for v in st.vias.values())
            or any(t["net_id"] == net_id for t in st.tunings.values()))


def _terminals(st, net_id):
    """网全部分区的覆盖后端点锚（排序去重——确定性链序）。"""
    pts = set()
    for pid in st.net_partitions(net_id):
        for a in st.effective_anchors(pid):
            pts.add((int(a[0]), int(a[1])))
    return sorted(pts)


def _shape_owner(st, shape_id):
    if shape_id in st.segs:
        return st.segs[shape_id]["net_id"]
    if shape_id in st.vias:
        return st.vias[shape_id]["net_id"]
    if shape_id in st.tunings:
        return st.tunings[shape_id]["net_id"]
    return None


# ---------------------------------------------------------------- 候选序

def _hop_candidates(net_id, a, b, layers, base_idx, k_max, lattice):
    """单跳候选动作组列表（固定序，见模块 docstring ①②③④）。

    每元素=一组原子应用的动作（route/via dicts，无 submit）。越界/退化
    候选在此预筛（lattice.in_bounds 界算术，非几何违例判定）；跨族同
    waypoint 序同层去重（保序）。
    """
    a = (int(a[0]), int(a[1]))
    b = (int(b[0]), int(b[1]))
    n = len(layers)
    order = [layers[(base_idx + q) % n] for q in range(n)]

    def bounds_ok(points):
        return all(lattice.in_bounds(p[0], p[1]) for p in points)

    def route(wps, layer):
        return {"action": "route", "net_id": net_id,
                "waypoints": [[int(p[0]), int(p[1])] for p in wps],
                "layer": layer}

    def via(pt):
        return {"action": "via", "net_id": net_id,
                "grid": [int(pt[0]), int(pt[1])]}

    out = []
    seen = set()

    def add(cand):
        key = canonical_json(cand)
        if key in seen:
            return
        seen.add(key)
        out.append(cand)

    # ① 单层 L 形直连（[a,b]=x-first；[a,(a.i,b.j),b]=y-first）
    for layer in order:
        add([route([a, b], layer)])
        c = (a[0], b[1])
        if c not in (a, b) and bounds_ok([a, c, b]):
            add([route([a, c, b], layer)])
    # ② 跨层 via 角过渡（有序层对 × 两角；段衔接点=via 在场）
    for la in order:
        for lb in order:
            if la == lb:
                continue
            for c in ((b[0], a[1]), (a[0], b[1])):
                if c in (a, b) or not bounds_ok([a, c, b]):
                    continue
                add([route([a, c], la), via(c), route([c, b], lb)])
    # ③④ 避障绕行（k 升序统一推进: 每 k 层内 U 平移先、Z 换轴后）
    dx, dy = b[0] - a[0], b[1] - a[1]
    perp_j = abs(dx) >= abs(dy)      # 走廊主轴水平 → 垂直向=j
    for k in range(1, k_max + 1):
        for s in (-1, 1):
            # U 平行绕（走廊整体平移 k: 垂直向先、平行向后）
            u_perp = [a, (a[0] + (0 if perp_j else s * k), a[1] + (s * k if perp_j else 0)),
                      (b[0] + (0 if perp_j else s * k), b[1] + (s * k if perp_j else 0)), b]
            u_par = [a, (a[0] + (s * k if perp_j else 0), a[1] + (0 if perp_j else s * k)),
                     (b[0] + (s * k if perp_j else 0), b[1] + (0 if perp_j else s * k)), b]
            for wps in (u_perp, u_par):
                if bounds_ok(wps):
                    for layer in order:
                        add([route(wps, layer)])
            # Z 换轴绕（中段单行/单列直插，端点腿解钉）
            for end in (b, a):
                r = end[1] + s * k
                z_row = [a, (a[0], r), (b[0], r), b]
                c = end[0] + s * k
                z_col = [a, (c, a[1]), (c, b[1]), b]
                for wps in (z_row, z_col):
                    if bounds_ok(wps):
                        for layer in order:
                            add([route(wps, layer)])
    # ⑤⑥ 门外折返阶梯（端点先向"背离对端"方向退出 k 再换轴——解开端点
    # 邻域被非豁免板固孔钳死的死局; 偏移只取外向，确定性 4 组合/层）
    for k in range(1, k_max + 1):
        c_a = a[0] - k if a[0] <= b[0] else a[0] + k   # a 端 i 向外
        c_b = b[0] + k if b[0] >= a[0] else b[0] - k   # b 端 i 向外
        r_a = a[1] - k if a[1] <= b[1] else a[1] + k   # a 端 j 向外
        r_b = b[1] + k if b[1] >= a[1] else b[1] - k   # b 端 j 向外
        for c in (c_a, c_b):
            for r in (r_a, r_b):
                # ⑤ 行门户: 出 a 行 → 列 c → 行 r → b 列入
                wps_row = [a, (c, a[1]), (c, r), (b[0], r), b]
                # ⑥ 列门户: 出 a 列 → 行 r → 列 c → b 行入
                wps_col = [a, (a[0], r), (c, r), (c, b[1]), b]
                for wps in (wps_row, wps_col):
                    if bounds_ok(wps):
                        for layer in order:
                            add([route(wps, layer)])
    return out


def _with_junction_via(cand, net_id, junction_pt, prev_layer):
    """跨层衔接纪律: 候选首段层≠前跳层 → 追加衔接 via（与跳段同批原子）。

    同层衔接（或链首跳）经端点锚附着，无需 via。"""
    if prev_layer is None:
        return cand
    first_layer = next(x["layer"] for x in cand if x["action"] == "route")
    if first_layer == prev_layer:
        return cand
    return list(cand) + [{"action": "via", "net_id": net_id,
                          "grid": [int(junction_pt[0]), int(junction_pt[1])]}]


# ---------------------------------------------------------------- 阻塞归责

def _apply_unvalidated(trial, cand):
    """候选动作不经 validate 直落 trial（state 公有缝 add_seg/add_via，只用于
    归责试演场；trial 为私有副本，丢弃）。返回新增 shape_id 集。"""
    new_ids = set()
    for a in cand:
        if a["action"] == "route":
            expanded = cinst.expand_waypoints(a["waypoints"])
            pid = trial.net_partitions(a["net_id"])[0]
            cls = trial.widths.get(a["net_id"],
                                   cval.default_width_class(trial))
            seg = trial.add_seg(a["net_id"], pid, a["layer"], expanded, cls)
            new_ids.add(seg["shape_id"])
        elif a["action"] == "via":
            v = trial.add_via(a["net_id"], a["grid"])
            new_ids.add(v["shape_id"])
    return new_ids


def _blocker_shape_ids(scratch, cand):
    """候选的阻塞铜 shape_id（确定性排序）。

    归责法=validate_full 差集: 基场景违例键集 vs 含候选（未验证直落）场景
    键集（键=canonical_json(v.as_dict())）；新增违例对中非候选方主体若为
    seg:/via: 图元（可拆）即阻塞主体。pad:/hole:N/board-edge/zone 不可拆
    →不返回（调用方换候选）。几何判定全在 canvas.validate/v5.drc 内。"""
    base = cval.validate_full(scratch)
    base_keys = set(canonical_json(v.as_dict()) for v in base.violations)
    trial = copy.deepcopy(scratch)
    new_ids = _apply_unvalidated(trial, cand)
    report = cval.validate_full(trial)
    blockers = set()
    for v in report.violations:
        if canonical_json(v.as_dict()) in base_keys:
            continue
        for subj in (v.subject_a, v.subject_b):
            if subj in new_ids:
                continue
            if (subj.startswith("seg:") or subj.startswith("via:")) \
                    and _shape_owner(trial, subj) is not None:
                blockers.add(subj)
    return sorted(blockers)


# ---------------------------------------------------------------- 单跳/单网

#: 拆段不可救码（他网 ripup 不改变其结局——重试扫描跳过，确定性等价省扫）
_UNRIPPABLE_CODES = frozenset([
    cproto.V_HOLE_TRACK, cproto.V_HOLE_VIA, cproto.V_EDGE,
    cproto.V_ENDPT_NOT_ATTACHED, cproto.V_VIA_OFF_PATH,
    cproto.V_DUPLICATE_VIA, cproto.V_SELF_SNAG,
])


def _place_hop(scratch, net_id, a, b, layers, base_idx, prev_layer,
               budget, ripup_guard, acts):
    """试放单跳: 候选序扫描（副本真 apply_batch 验放）；全败→阻塞归责+
    批量 ripup 后重扫（≤per_net_retry 轮）。成功返回落层，失败 None。

    通过则把接受的动作用 apply_batch 落到 scratch 并 append 进 acts。
    重扫只重试 V_CLEARANCE/V_UNKNOWN_WIDTH_CLASS 类候选（拆段可救）;
    首轮判为 _UNRIPPABLE_CODES 的候选跳过（结局与拆段无关，见集合注释）。"""
    cands = _hop_candidates(net_id, a, b, layers, base_idx,
                            budget["per_net_retry"], scratch.lattice)
    keys = [canonical_json(cand) for cand in cands]
    unrippable = set()
    for attempt in range(budget["per_net_retry"] + 1):
        rep = None
        for cand, key in zip(cands, keys):
            if key in unrippable:
                continue
            full = _with_junction_via(cand, net_id, a, prev_layer)
            if rep is None:
                rep = full
            trial = copy.deepcopy(scratch)
            results = cproto.apply_batch(trial, full)
            if all(r["accepted"] for r in results):
                cproto.apply_batch(scratch, full)
                acts.extend(full)
                return next(x["layer"] for x in full
                            if x["action"] == "route")
            bad = next(r for r in results if not r["accepted"])
            if bad["code"] in _UNRIPPABLE_CODES:
                unrippable.add(key)
        if rep is None or attempt >= budget["per_net_retry"]:
            break       # 无可救候选（全判不可拆码）或重试额度用尽
        blockers = _blocker_shape_ids(scratch, rep)
        eligible = []
        for sid in blockers:
            owner = _shape_owner(scratch, sid)
            if owner is None or owner == net_id:
                continue
            if ripup_guard.get(owner, 0) >= budget["per_net_retry"]:
                continue
            if sid not in eligible:
                eligible.append(sid)
        if not eligible:
            break
        owners = {sid: _shape_owner(scratch, sid) for sid in eligible}
        ripups = [{"action": "ripup", "shape_id": sid}
                  for sid in sorted(eligible)]
        cproto.apply_batch(scratch, ripups)
        acts.extend(ripups)
        for sid in sorted(owners):
            owner = owners[sid]
            ripup_guard[owner] = ripup_guard.get(owner, 0) + 1
    return None


def _plan_net(scratch, net_id, budget, offsets, ripup_guard):
    """规划单网（在 scratch 上真落动作）; 返回 (actions, ok)。"""
    acts = []
    if _net_has_copper(scratch, net_id):
        rip = {"action": "ripup", "net_id": net_id}
        cproto.apply_batch(scratch, [rip])
        acts.append(rip)
    cls = _net_width_class(scratch, net_id)
    width_act = {"action": "width_class", "net_id": net_id, "class": cls}
    cproto.apply_batch(scratch, [width_act])
    acts.append(width_act)
    terms = _terminals(scratch, net_id)
    layers = scratch.signal_layers()
    ok = False
    if len(terms) >= 2 and layers:
        prev_layer = None
        chain_done = True
        for hidx in range(len(terms) - 1):
            a, b = terms[hidx], terms[hidx + 1]
            base_idx = (offsets[net_id] + hidx) % len(layers)
            placed = _place_hop(scratch, net_id, a, b, layers, base_idx,
                                prev_layer, budget, ripup_guard, acts)
            if placed is None:
                chain_done = False
                break
            prev_layer = placed
        if chain_done:
            scratch.recompute_connectivity()
            ok = bool(scratch.connectivity.get(net_id))
    if not ok and _net_has_copper(scratch, net_id):
        rip = {"action": "ripup", "net_id": net_id}
        cproto.apply_batch(scratch, [rip])
        acts.append(rip)
    return acts, ok


# ---------------------------------------------------------------- 两层 API

def plan_actions(st, budget=None):
    """确定性粗布规划: 未连通网 → canvas-edit-v2 动作列表（无 submit；
    run_m2 补 submit 成协议批）。不改 st（副本上演进）。

    轮结构: max_rounds 轮全网字典序扫；轮内每未连通网清残段→width_class→
    端点锚链逐跳试放（含阻塞网批量 ripup）；全网连通或无进展即停。"""
    budget = _normalize_budget(budget)
    scratch = copy.deepcopy(st)
    scratch.recompute_connectivity()
    nets = sorted(scratch.known_nets())
    offsets = {n: i for i, n in enumerate(nets)}
    ripup_guard = {n: 0 for n in nets}
    actions = []
    for _round in range(budget["max_rounds"]):
        progressed = False
        for net_id in nets:
            if scratch.connectivity.get(net_id):
                continue
            block, ok = _plan_net(scratch, net_id, budget, offsets,
                                  ripup_guard)
            actions.extend(block)
            if ok:
                progressed = True
        if all(scratch.connectivity.get(n) for n in nets):
            break
        if not progressed:
            break
    return actions


def _via_cost_facts(st, planned, results):
    """过孔成本打包事实（runner 自有输出; 不改 canvas/pack.py）。

    结构钉死: {vias_planned, vias_applied, vias_by_net, estimated_via_cost,
    via_cost_model{unit_cost, unit, candidate_order, junction_policy,
    drill_mm, annular_mm, signal_layers}}。drill/annular 只读抄录
    board["via_model"]（无显式表→None; v5.kicad_export 缺省不在此抄录——
    合同 §1 runner 不私触导出器）。"""
    vias_planned = sum(1 for a in planned if a.get("action") == "via")
    vias_applied = sum(1 for r in results
                       if r["accepted"] and r["action"] == "via")
    by_net = {}
    for sid in sorted(st.vias):
        net_id = st.vias[sid]["net_id"]
        by_net[net_id] = by_net.get(net_id, 0) + 1
    vm = st.board.get("via_model")
    vm = vm if isinstance(vm, dict) else {}

    def _num(key):
        v = vm.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return round(float(v), 9)
        return None

    return {
        "vias_planned": vias_planned,
        "vias_applied": vias_applied,
        "vias_by_net": {k: by_net[k] for k in sorted(by_net)},
        "estimated_via_cost": vias_applied * VIA_UNIT_COST,
        "via_cost_model": {
            "unit_cost": VIA_UNIT_COST,
            "unit": "abstract-via-cost",
            "candidate_order": ("single-layer L shapes first, cross-layer "
                                "via-corner transitions next, k-step U "
                                "detours last (k ascending) -- via-"
                                "minimizing greedy"),
            "junction_policy": ("via mandatory at layer-differing hop "
                                "junctions (atomic with the hop batch); "
                                "same-layer junction via endpoint-anchor "
                                "attachment fallback is inherent in the "
                                "layer rotation order"),
            "drill_mm": _num("drill"),
            "annular_mm": _num("annular"),
            "signal_layers": list(st.signal_layers()),
        },
    }


def run_m2(st, budget=None):
    """plan → canvas.protocol.apply_batch 应用 → 摘要 dict。

    摘要键集（钉死，canonical_json 可直落）::
        runner, board_id, budget, planned_action_count(不含 submit),
        applied_count(不含 submit), rejected_count, rejected[
        {index,action,code,detail}], rejected_histogram{code:n},
        nets_connected_before/after, unresolved_nets, via_cost_facts
        (见 _via_cost_facts docstring), state_sha256_before/after。
    正常路径 rejected 应为空（规划在镜像副本上已逐动作验放; 若非零则如实
    上报，不静默重试——fail-closed）。"""
    budget = _normalize_budget(budget)
    before_sha = state_sha256(st)
    before = [n for n in sorted(st.connectivity) if st.connectivity[n]]
    planned = plan_actions(st, budget)
    batch = list(planned) + [{"action": "submit"}]
    results = cproto.apply_batch(st, batch)
    st.recompute_connectivity()
    after = [n for n in sorted(st.connectivity) if st.connectivity[n]]
    unresolved = [n for n in sorted(st.connectivity)
                  if not st.connectivity[n]]
    rejected = [{"index": r["index"], "action": r["action"],
                 "code": r["code"], "detail": r["detail"]}
                for r in results if not r["accepted"]]
    histogram = {}
    for r in rejected:
        histogram[r["code"]] = histogram.get(r["code"], 0) + 1
    return {
        "runner": RUNNER_ID,
        "board_id": st.board["board_id"],
        "budget": dict(budget),
        "planned_action_count": len(planned),
        "applied_count": sum(1 for r in results
                             if r["accepted"] and r["action"] != "submit"),
        "rejected_count": len(rejected),
        "rejected": rejected,
        "rejected_histogram": {k: histogram[k] for k in sorted(histogram)},
        "nets_connected_before": before,
        "nets_connected_after": after,
        "unresolved_nets": unresolved,
        "via_cost_facts": _via_cost_facts(st, planned, results),
        "state_sha256_before": before_sha,
        "state_sha256_after": state_sha256(st),
    }
