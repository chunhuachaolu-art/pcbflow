# -*- coding: utf-8 -*-
"""canvas.placecheck -- 布间放置 validator（合同 §1 Lane-M4 伴件）。

**口径标注（verdict/测试一律显式）: 本件是新 validator，非 v5.drc 移植。**
与 v5.drc 的关系=补充非替代: v5.drc（经 canvas.validate）管铜面对铜面
DRC（段折线/via 盘/pad 精确几何），placecheck 管**放置预检**——move/
rotate/flip 候选在落铜/落段之前的布间合法性（合同 §2 三动作的
V_PLACEMENT_COLLISION 判定源）。铜面对铜面判定一律走 canvas.validate/
v5.drc，本件不平行实现；板边禁布带裕量也归 v5.drc edge 判定，本件只查
外接矩形含于板框（无裕量，披露）。

检查对象（三面，确定性检查序: 分区存在 → 候选良构/值域 → 板框内 → 布间间距）:
- 布间间距: 分区 pad 场**外接矩形** vs 其它分区 pad 场外接矩形（各含
  覆盖后位置——覆盖合成序=canvas.state docstring 钉死的
  rotate→flip→move→resnap，本件经 PlacementsView 借用 CanvasState 方法
  逐字节同源，不另写覆盖算术），rect-rect 间距 ≥ 阈值。同网分区对缺省
  豁免（R5 same_net_exempt 纪律镜像，参数可关）。
- 板框内: 候选分区 pad 场外接矩形须含于 board.workspace。
- 格点贴合: candidate["move"] 须为二元整数格点且在 lattice 域内
  （协议格点纪律同源; 覆盖合成末步 resnap 由 canvas.state 承担）。

阈值推导（缺省，docstring 披露）: min_gap_mm=None →
board["hard_rules"]["R5"]["min_clearance_mm"]——与 v5.drc.check_clearance
同阈值单源，不另立阈值; 参数化 min_gap_mm 仅为测试/实验注入，激活跑
冻结于 prereg。

**真板实测披露（badgeleds-do-electronics）**: 真板分区=2-pad 器件，
端点跨距 15~40mm，pad 场外接矩形基线即互相重叠（36 对中 28 对
rect-gap < 0.5mm 阈值）——包络语义下真板一切 move/rotate/flip 候选
结构性拒收（V_PLACEMENT_COLLISION）。本车道按合同口径如实实现并在此
+REPORT 披露; 按包络改判（如 per-pad 包络）属合同修订裁决，归编排体。
合成微板基线无违例，接受路径全量可测。

原因码（placecheck 命名空间; 词表追加式，接线登记归编排体）:
- E_UNKNOWN_PARTITION（新码）: partition_id 不在 board.partitions——
  合同 REV 注记「E 侧无专属码，随 placecheck 语义定」，本件定名;
- E_NON_INTEGER_GRID / E_GRID_OUT_OF_BOUNDS: 借 protocol 既有码同名同义
  （非格点 / 格点·值域越出 lattice 域或 rotate∉{0,1,2,3}）;
- V_PLACEMENT_EDGE（新码）: pad 场外接矩形越出板框;
- V_PLACEMENT_COLLISION: 合同 §2 语义码（借 protocol 常量）。
"""
import math

from . import protocol as _p
from . import state as _cst

#: 间距比较容差（gap < min_gap - EPS 判违例; == 阈值合法）
EPS = 1e-9
#: 板框 containment 容差（覆盖合成浮点噪声余量）
FRAME_EPS = 1e-6

# ---- 原因码（E_UNKNOWN_PARTITION/V_PLACEMENT_EDGE 为本件新码）----
E_UNKNOWN_PARTITION = "E_UNKNOWN_PARTITION"
V_PLACEMENT_EDGE = "V_PLACEMENT_EDGE"


def default_min_gap_mm(board):
    """缺省阈值推导: hard_rules.R5.min_clearance_mm（v5.drc 同阈值单源）。"""
    return float(board["hard_rules"]["R5"]["min_clearance_mm"])


class PlacementsView(object):
    """board/lattice/placements 三元组的覆盖视图。

    借用 canvas.state.CanvasState 方法（未绑定函数挂载: board_partition/
    board_endpoint_mm/placement/effective_endpoint_mm/effective_anchors），
    覆盖合成序与 canvas.state 逐字节同源——placecheck/referee 对「假设
    覆盖」的求值不复制波1 覆盖算术。anchors=anchor_map(board, lattice)
    （effective_anchors 无覆盖路径消费，语义同构造期锚）。"""

    board_partition = _cst.CanvasState.board_partition
    board_endpoint_mm = _cst.CanvasState.board_endpoint_mm
    placement = _cst.CanvasState.placement
    effective_endpoint_mm = _cst.CanvasState.effective_endpoint_mm
    effective_anchors = _cst.CanvasState.effective_anchors

    def __init__(self, board, lattice, placements):
        self.board = board
        self.lattice = lattice
        self.placements = placements
        self.anchors = _cst.anchor_map(board, lattice)


def covered_endpoints_mm(board, lattice, placements, pid):
    """覆盖后分区端点 mm（合成序同 canvas.state；无覆盖=原位）。"""
    return PlacementsView(board, lattice, placements).effective_endpoint_mm(pid)


def covered_anchors(board, lattice, placements, pid):
    """覆盖后分区端点锚（格点）。"""
    return PlacementsView(board, lattice, placements).effective_anchors(pid)


def merge_candidate(placements, partition_id, candidate):
    """当前覆盖 × 候选（部分键）→ 完整覆盖 dict。

    candidate 键集 ⊆ {"move","rotate","flip"}（合同外键=ValueError，
    fail-closed）; 缺键=承袭当前覆盖（canvas.state.set_placement 的
    _KEEP 同语义）。**绝对语义**: 候选值即覆盖后目标值——协议动作的
    相对→绝对折算（rotate: (cur+turns)%4; flip: 取反; move: 绝对
    target）是调用方（runner/接线层）的义务，见 runners/m4 与 REPORT
    接线契约。"""
    if not isinstance(candidate, dict):
        raise ValueError("candidate 须为 dict（得到 %s）"
                         % type(candidate).__name__)
    extra = set(candidate) - {"move", "rotate", "flip"}
    if extra:
        raise ValueError("candidate 合同外键 %s" % sorted(extra))
    cur = {"move": None, "rotate": 0, "flip": False}
    if partition_id in placements:
        cov = placements[partition_id] or {}
        cur = {"move": cov.get("move"),
               "rotate": int(cov.get("rotate", 0)) % 4,
               "flip": bool(cov.get("flip", False))}
    out = dict(cur)
    if "move" in candidate:
        mv = candidate["move"]
        out["move"] = None if mv is None else [int(mv[0]), int(mv[1])]
    if "rotate" in candidate:
        out["rotate"] = int(candidate["rotate"]) % 4
    if "flip" in candidate:
        out["flip"] = bool(candidate["flip"])
    return out


def _pad_rect_on_view(view, pid):
    """分区 pad 场外接矩形 (x0,y0,x1,y1) mm（覆盖后）。

    - 每枚 pad_terminal 按覆盖后端点位置贡献其外接矩形（rect=size/2
      各向矩形; circle=半径外接方——包络取保守方形）;
    - 无 pad_terminals 的分区退化为端点零面积矩形并（合成板全覆盖，
      真板 9/9 分区有 pad_terminals，此分支为完备性披露）。"""
    part = view.board_partition(pid)
    if part is None:
        raise KeyError(pid)
    eps = view.effective_endpoint_mm(pid)
    items = (part.get("geometry") or {}).get("pad_terminals") or []
    rects = []
    for item in sorted(items, key=lambda q: q["endpoint"]):
        k = int(item["endpoint"])
        if not 0 <= k < len(eps):
            raise ValueError("%s pad_terminals.endpoint=%d 越界（端点数 %d）"
                             % (pid, k, len(eps)))
        cx, cy = eps[k]
        size = item["size_mm"]
        if item.get("shape") == "circle":
            hw = hh = float(size[0]) / 2.0
        else:
            hw = float(size[0]) / 2.0
            hh = float(size[1]) / 2.0
        rects.append((cx - hw, cy - hh, cx + hw, cy + hh))
    if not rects:
        rects = [(x, y, x, y) for (x, y) in eps]
    return (min(r[0] for r in rects), min(r[1] for r in rects),
            max(r[2] for r in rects), max(r[3] for r in rects))


def pad_field_rect(board, lattice, placements, pid):
    """单分区 pad 场外接矩形 mm（覆盖后; 新 validator 几何，非 v5.drc）。"""
    return _pad_rect_on_view(PlacementsView(board, lattice, placements), pid)


def pad_field_rects(board, lattice, placements):
    """全分区 pad 场外接矩形 {pid: (x0,y0,x1,y1)}（pid sorted 序构建）。"""
    view = PlacementsView(board, lattice, placements)
    return {pid: _pad_rect_on_view(view, pid)
            for pid in sorted(p["partition_id"]
                              for p in board["partitions"])}


def rect_gap_mm(a, b):
    """轴对齐矩形间距（布间度量; 两轴皆重叠时返回负侵入深度近似——
    任何 <阈值的值（含负）判违例，单调全覆盖）。"""
    dx = max(a[0] - b[2], b[0] - a[2])
    dy = max(a[1] - b[3], b[1] - a[3])
    if dx >= 0.0 and dy >= 0.0:
        return math.hypot(dx, dy)
    if dx >= 0.0:
        return dx
    if dy >= 0.0:
        return dy
    return -min(-dx, -dy)


def _net_of(board):
    """pid -> net_id 映射（无网分区不在表内——同网豁免只对两pid皆有网
    且同网生效，None==None 不视作同网）。"""
    out = {}
    for n in board["nets"]:
        for pid in n["partitions"]:
            out[pid] = n["net_id"]
    return out


def _is_grid_pair(v):
    return (isinstance(v, (list, tuple)) and len(v) == 2
            and all(isinstance(c, int) and not isinstance(c, bool)
                    for c in v))


def check_placement(board, lattice, placements, partition_id, candidate,
                    min_gap_mm=None, same_net_exempt=True):
    """单分区放置候选合法性（**新 validator，非 v5.drc 移植**）。

    签名（接线契约——编排体据此接 canvas/validate.py 三处占位; 见
    lane-m4 REPORT）:
      board:        board dict（v5.board.load_board 产物或合同内消费面）
      lattice:      canvas.state.Lattice
      placements:   当前覆盖 {pid: {"move","rotate","flip"}}（st.placements
                    直传; 无覆盖分区可不在 dict 内）
      partition_id: 候选分区
      candidate:    部分覆盖 dict（键集 ⊆ {"move","rotate","flip"}，缺键
                    承袭当前覆盖; **绝对语义**，相对→绝对折算归调用方）
      min_gap_mm:   布间阈值（None=hard_rules.R5.min_clearance_mm 推导）
      same_net_exempt: 同网分区对豁免布间间距（缺省 True，R5 纪律镜像）
    返回 (ok: bool, code: str|None, detail: str|None)。

    检查序（确定性优先级）: 分区存在(E_UNKNOWN_PARTITION) → move 非格点
    (E_NON_INTEGER_GRID) → move/rotate 值域(E_GRID_OUT_OF_BOUNDS) →
    板框内(V_PLACEMENT_EDGE) → 布间间距(V_PLACEMENT_COLLISION) →
    (True, None, None)。candidate 非 dict / 合同外键 / flip 非 bool =
    API 误用，ValueError fail-closed（无码可归，不静默）。"""
    pids = {p["partition_id"] for p in board["partitions"]}
    if partition_id not in pids:
        return (False, E_UNKNOWN_PARTITION, str(partition_id))
    if not isinstance(candidate, dict):
        raise ValueError("candidate 须为 dict（得到 %s）"
                         % type(candidate).__name__)
    extra = set(candidate) - {"move", "rotate", "flip"}
    if extra:
        raise ValueError("candidate 合同外键 %s" % sorted(extra))
    if min_gap_mm is None:
        min_gap_mm = default_min_gap_mm(board)
    min_gap_mm = float(min_gap_mm)
    if "move" in candidate and candidate["move"] is not None:
        mv = candidate["move"]
        if not _is_grid_pair(mv):
            return (False, _p.E_NON_INTEGER_GRID,
                    "move=%r 非二元整数格点" % (mv,))
        if not lattice.in_bounds(int(mv[0]), int(mv[1])):
            return (False, _p.E_GRID_OUT_OF_BOUNDS,
                    "move=%s 越出格点域 %s" % (list(mv), lattice.as_dict()))
    if "rotate" in candidate:
        rot = candidate["rotate"]
        if isinstance(rot, bool) or not isinstance(rot, int):
            return (False, _p.E_GRID_OUT_OF_BOUNDS,
                    "rotate=%r 非整数" % (rot,))
        if not 0 <= rot <= 3:
            return (False, _p.E_GRID_OUT_OF_BOUNDS,
                    "rotate=%r 越界 {0,1,2,3}" % (rot,))
    if "flip" in candidate and not isinstance(candidate["flip"], bool):
        raise ValueError("candidate.flip 须为 bool（得到 %r）"
                         % (candidate["flip"],))
    merged = merge_candidate(placements, partition_id, candidate)
    pl2 = dict(placements)
    pl2[partition_id] = merged
    view = PlacementsView(board, lattice, pl2)
    rect = _pad_rect_on_view(view, partition_id)
    ws = board["workspace"]
    if (rect[0] < float(ws["x_min"]) - FRAME_EPS
            or rect[1] < float(ws["y_min"]) - FRAME_EPS
            or rect[2] > float(ws["x_max"]) + FRAME_EPS
            or rect[3] > float(ws["y_max"]) + FRAME_EPS):
        return (False, V_PLACEMENT_EDGE,
                "pad 场越框 rect=(%.3f,%.3f,%.3f,%.3f) "
                "ws=(%.3f,%.3f,%.3f,%.3f)"
                % (rect + (float(ws["x_min"]), float(ws["y_min"]),
                           float(ws["x_max"]), float(ws["y_max"]))))
    net_of = _net_of(board)
    for q in sorted(pids):
        if q == partition_id:
            continue
        if (same_net_exempt and net_of.get(q) is not None
                and net_of.get(q) == net_of.get(partition_id)):
            continue
        gap = rect_gap_mm(rect, _pad_rect_on_view(view, q))
        if gap < min_gap_mm - EPS:
            return (False, _p.V_PLACEMENT_COLLISION,
                    "%s|%s gap=%.3f<%.3f（覆盖后 pad 场外接矩形）"
                    % (partition_id, q, gap, min_gap_mm))
    return (True, None, None)


def check_all_placements(board, lattice, placements,
                         min_gap_mm=None, same_net_exempt=True):
    """全场布间检查（新 validator，非 v5.drc 移植）→ 违例 dict 列表。

    每分区: 覆盖条目域检查（E_NON_INTEGER_GRID/E_GRID_OUT_OF_BOUNDS——
    条目域坏即标记该分区 invalid，跳过其板框/配对检查= fail-closed 不
    产出无意义几何判定）→ 板框（V_PLACEMENT_EDGE）。随后全分区对
    （sorted 组合序）: 布间间距（V_PLACEMENT_COLLISION）。
    违例 dict: {"code","detail","partition_id"} 单分区面 /
    {"code","detail","partitions":[a,b],"gap_mm"} 配对面; 列表序=检查序
    （确定性）。空列表=全场合法。"""
    if min_gap_mm is None:
        min_gap_mm = default_min_gap_mm(board)
    out = []
    invalid = set()
    pids = sorted(p["partition_id"] for p in board["partitions"])
    for pid in pids:
        if pid not in placements:
            continue
        cov = placements[pid] or {}
        mv = cov.get("move")
        if mv is not None:
            if not _is_grid_pair(mv):
                out.append({"code": _p.E_NON_INTEGER_GRID,
                            "partition_id": pid,
                            "detail": "move=%r 非二元整数格点" % (mv,)})
                invalid.add(pid)
                continue
            if not lattice.in_bounds(int(mv[0]), int(mv[1])):
                out.append({"code": _p.E_GRID_OUT_OF_BOUNDS,
                            "partition_id": pid,
                            "detail": "move=%s 越出格点域" % (list(mv),)})
                invalid.add(pid)
                continue
        rot = cov.get("rotate", 0)
        if isinstance(rot, bool) or not isinstance(rot, int) \
                or not 0 <= rot <= 3:
            out.append({"code": _p.E_GRID_OUT_OF_BOUNDS,
                        "partition_id": pid,
                        "detail": "rotate=%r 越界 {0,1,2,3}" % (rot,)})
            invalid.add(pid)
    view = PlacementsView(board, lattice, placements)
    rects = {pid: _pad_rect_on_view(view, pid) for pid in pids}
    ws = board["workspace"]
    for pid in pids:
        if pid in invalid:
            continue
        r = rects[pid]
        if (r[0] < float(ws["x_min"]) - FRAME_EPS
                or r[1] < float(ws["y_min"]) - FRAME_EPS
                or r[2] > float(ws["x_max"]) + FRAME_EPS
                or r[3] > float(ws["y_max"]) + FRAME_EPS):
            out.append({"code": V_PLACEMENT_EDGE, "partition_id": pid,
                        "detail": "pad 场越框 rect=(%.3f,%.3f,%.3f,%.3f)"
                                  % r})
    net_of = _net_of(board)
    n = len(pids)
    for x in range(n):
        for y in range(x + 1, n):
            a, b = pids[x], pids[y]
            if a in invalid or b in invalid:
                continue
            if (same_net_exempt and net_of.get(a) is not None
                    and net_of.get(a) == net_of.get(b)):
                continue
            gap = rect_gap_mm(rects[a], rects[b])
            if gap < min_gap_mm - EPS:
                out.append({"code": _p.V_PLACEMENT_COLLISION,
                            "partitions": [a, b],
                            "gap_mm": round(gap, 9),
                            "detail": "%s|%s gap=%.3f<%.3f"
                                      % (a, b, gap, min_gap_mm)})
    return out
