"""pcbflow.v4_1.e4family -- E4 L1 规模阶梯：30 网级合成大场景族 f11（堵 K4）。

任务书 §3 E4 L1：30 网级合成大场景族（新族 f11 起）；密度设计须产生
真实拥塞（E3 遗留：让 In2 利用率有非零动因）；出口=全链绿+拥塞/层利用
观察台账。

域设计（schema pcbflow.v4_1.e4board/1；字段与 mlboard 同构，net 数放开）：

- 每场景 30 网（n01..n30），全部 default 类，4 层 F.Cu/In1.Cu/In2.Cu/B.Cu，
  bbox 60x45（30 网 x 60 endpoint pad 的容纳域）；
- 端点：左右各两列 pad（x=4/8 与 x=52/56），列内 y=1.5+3.0*i（3.0mm
  间距：1.2mm pad +0.35 阻挡扩边后留 ~1.1mm 通道，0.25 格点可穿）；
  配对左列->右列，右列 y 由 seed 偏移（列内循环移位）产生跨行走向；
- 拥塞构造（In2 非零动因）：外层双墙（F.Cu+B.Cu 全高 x 带 [23,27]）
  迫使全部 30 网下潜内层穿越；In1 墙留两门（各 6mm 高，容量 ~24 道
  < 30 网），In2 墙留一门（6mm，容量 ~12 道）——In1 门先饱和，剩余网
  被迫 In2（分层 via 成本 F..In1=4.0 < F..In2=5.5 偏好序保持）；
- 门位按场景 seed 抖动（0.5 倍数平移），族内拓扑多样性来自门位+配对；
- 规则与 mlfamily 冻结参数一致（grid=0.25/clearance=0.25/width=0.20
  双类同宽/via pad=0.40 hole=0.20——格点契约物理一致论证同 mlfamily）。

全链：生成 -> 校验 -> solver2 求解（分层默认 via 成本；flat 对照臂）
-> mlchain.check_ml_solution 独立复查（via 跨度/层合法/宽度/异网
clearance 双引擎交叉）。f9/f10、f1-f8 与 112 manifest 零改动。

CLI：python -m pcbflow.v4_1.e4family --out out/v4.1-engineering/e4/l1-family
（canonical JSON；零 wall-clock；零子进程——router/solver 进程内 import）。
"""

from __future__ import annotations

import hashlib

from . import DECLARED_DATE
from .canonical import write_canonical_json
from .costmodel import ViaCostModel
from .mlfamily import ML_LAYERS, ML_RULES

__all__ = [
    "E4BOARD_SCHEMA", "E4_FAMILY", "E4_BBOX_MM", "E4_RULES", "E4_NET_COUNT",
    "scenario_ids_e4", "seed_for_e4", "generate_e4_scenario",
    "validate_e4board", "run_l1_chain", "main",
]

E4BOARD_SCHEMA = "pcbflow.v4_1.e4board/1"
E4_FAMILY = "f11"
E4_BBOX_MM = [0.0, 0.0, 60.0, 45.0]
E4_RULES = dict(ML_RULES)          # 与 mlfamily 冻结参数逐键一致
E4_NET_COUNT = 30

#: 8 场景：dev-f11-01..04 / cal-f11-05..06 / hol-f11-07..08（全部
#: satisfiable 设计；hol 若实跑 unsat 如实登记不渲染 sat）。
_E4_SPLIT_SERIALS = [
    ("development", range(1, 5)),
    ("calibration", range(5, 7)),
    ("holdout", range(7, 9)),
]
_E4_SPLIT_PREFIX = {"development": "dev", "calibration": "cal",
                    "holdout": "hol"}

_PAD_W = 1.2
_PAD_H = 1.2
_WALL_X0 = 23.0
_WALL_X1 = 27.0
_WALL_Y0 = 0.5
_WALL_Y1 = 44.5
_GATE_H = 6.0
_GATE_H_IN2 = 20.0


class E4FamilyError(ValueError):
    """f11 族生成/校验 fail-closed。"""


def scenario_ids_e4():
    """(scenario_id, split, serial) 确定性列表。"""
    out = []
    for split, serials in _E4_SPLIT_SERIALS:
        for s in serials:
            out.append(("%s-%s-%02d" % (_E4_SPLIT_PREFIX[split],
                                        E4_FAMILY, s), split, s))
    return out


def seed_for_e4(scenario_id):
    digest = hashlib.sha256(scenario_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


# ---------------------------------------------------------------- 生成

def _gate_positions(seed):
    """In1 两窄门/In2 一高门的 y 起点（0.5 倍数；按 seed 抖动）。

    容量设计（首跑 7/8 后的容量保证修正，DEV-E4-002）：
    - In1 两门各 6mm（容量 ~9/门，合计 ~18 < 30 → In1 先饱和，>=12 网
      被迫 In2——In2 非零动因保持）；
    - In2 门 20mm（容量 ~35 >= 30 → 全部网可走 In2 兜底=sat 保证）；
    - In1 两门间隔墙 >= 6mm（走廊不交叠：首跑 dev-f11-04 相邻门
      （间隔 2mm）发生同层栅栏互堵的教训）。
    """
    import random
    rng = random.Random(seed)

    def _pick(lo, hi):
        steps = int(round((hi - lo) / 0.5))
        return round(lo + 0.5 * rng.randint(0, steps), 1)

    gates = {}
    gates["in1_a"] = _pick(2.0, 12.0)
    # 两门间隔墙 >= 6.0（走廊分离；上限 35.5 保证上门+6 <= 41.5）
    gates["in1_b"] = _pick(gates["in1_a"] + _GATE_H + 6.0, 35.5)
    # In2 高门 20mm：起点带 [2.0, 23.5]（门顶 <= 43.5）
    gates["in2"] = _pick(2.0, 23.5)
    return gates


def _wall_rects(gates):
    """墙体 keepout 矩形族（外层双墙全高；In1 两门；In2 一门）。"""
    def band(y0, y1):
        return [_WALL_X0, y0, _WALL_X1, y1]

    rects = []
    # F.Cu + B.Cu 全高墙
    rects.append(("wall-F", band(_WALL_Y0, _WALL_Y1), ["F.Cu"]))
    rects.append(("wall-B", band(_WALL_Y0, _WALL_Y1), ["B.Cu"]))
    # In1 两门：三段墙
    a0, a1 = gates["in1_a"], gates["in1_a"] + _GATE_H
    b0, b1 = gates["in1_b"], gates["in1_b"] + _GATE_H
    rects.append(("wall-In1-low", band(_WALL_Y0, a0 - 0.5), ["In1.Cu"]))
    rects.append(("wall-In1-mid", band(a1 + 0.5, b0 - 0.5), ["In1.Cu"]))
    rects.append(("wall-In1-high", band(b1 + 0.5, _WALL_Y1), ["In1.Cu"]))
    # In2 一门（高门 20mm 容量兜底）：两段墙
    c0, c1 = gates["in2"], gates["in2"] + _GATE_H_IN2
    rects.append(("wall-In2-low", band(_WALL_Y0, c0 - 0.5), ["In2.Cu"]))
    rects.append(("wall-In2-high", band(c1 + 0.5, _WALL_Y1), ["In2.Cu"]))
    return rects


def _is_half_mult(v):
    q = float(v) / 0.5
    return abs(q - round(q)) <= 1e-6


def generate_e4_scenario(scenario_id, split, serial):
    """确定性生成一个 f11 场景（30 网）。"""
    import random
    seed = seed_for_e4(scenario_id)
    rng = random.Random(seed)
    gates = _gate_positions(seed)
    rects = _wall_rects(gates)

    pads = []
    nets = []
    comps_l = ["U1", "U2"]
    comps_r = ["J1", "J2"]
    pin = {"U1": 0, "U2": 0, "J1": 0, "J2": 0}
    n_per_col = E4_NET_COUNT // 2
    # 右列 y 映射：每列一个随机双射（permutation）——保距离约束的
    # 前提下产生跨行走向多样性（非双射映射会产生同列同 y 冲突 pad）
    perms = []
    for _c in range(2):
        perm = list(range(n_per_col))
        rng.shuffle(perm)
        perms.append(perm)
    for i in range(E4_NET_COUNT):
        nid = "n%02d" % (i + 1)
        col = i // n_per_col            # 0 -> 左列 A / 1 -> 左列 B
        idx = i % n_per_col
        y_l = 1.5 + 3.0 * idx
        # 右列 y：列内双射重排（跨行走向）
        ridx = perms[col][idx]
        y_r = 1.5 + 3.0 * ridx
        cl = comps_l[col]
        cr = comps_r[col]
        pin[cl] += 1
        pin[cr] += 1
        pl = {"pad_id": "%s-%d" % (cl, pin[cl]), "net_id": nid,
              "x_mm": 4.0 if col == 0 else 8.0, "y_mm": y_l,
              "w_mm": _PAD_W, "h_mm": _PAD_H, "layer": "F.Cu"}
        pr = {"pad_id": "%s-%d" % (cr, pin[cr]), "net_id": nid,
              "x_mm": 52.0 if col == 0 else 56.0, "y_mm": y_r,
              "w_mm": _PAD_W, "h_mm": _PAD_H, "layer": "F.Cu"}
        pads.extend([pl, pr])
        nets.append({"net_id": nid, "net_class": "default",
                     "endpoints": [pl["pad_id"], pr["pad_id"]]})

    keepouts = [{"keepout_id": kid, "rect_mm": rect, "layers": lys}
                for (kid, rect, lys) in rects]

    obj = {
        "schema": E4BOARD_SCHEMA,
        "scenario_id": scenario_id,
        "split": split,
        "family": E4_FAMILY,
        "seed": seed,
        "serial": serial,
        "board": {"bbox_mm": list(E4_BBOX_MM), "layers": list(ML_LAYERS)},
        "rules": {k: (dict(v) if isinstance(v, dict) else
                      (list(v) if isinstance(v, list) else v))
                  for k, v in E4_RULES.items()},
        "pads": pads,
        "nets": nets,
        "keepouts": keepouts,
        "relations": [{"relation_id": "rel-bus-01", "relation_type": "bus",
                       "members": [n["net_id"] for n in nets],
                       "parent_id": None}],
        "label": "satisfiable",
        "gates_mm": {"in1_a": [gates["in1_a"], gates["in1_a"] + _GATE_H],
                     "in1_b": [gates["in1_b"], gates["in1_b"] + _GATE_H],
                     "in2": [gates["in2"], gates["in2"] + _GATE_H_IN2]},
    }
    errs = validate_e4board(obj)
    if errs:
        raise E4FamilyError("f11 生成自检失败（生成器 bug）: %r" % (errs,))
    _post_check(obj)
    return obj


def _post_check(obj):
    """生成期几何自检：同列相邻 pad 中心距 >=2.0；pad 中心到同层 keepout
    平面距离 >=1.0；net 端点间距 >=8mm。违反=生成器 bug。"""
    pads = obj["pads"]
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            dx = abs(pads[i]["x_mm"] - pads[j]["x_mm"])
            dy = abs(pads[i]["y_mm"] - pads[j]["y_mm"])
            if dx < 1e-9 and dy < 2.0 - 1e-9 and i != j:
                # 同列（x 相同）才要求 2.0 间距；异列由 dx 拉开
                if dx + dy < 2.0 - 1e-9:
                    raise E4FamilyError(
                        "pad 对过近（<2.0mm）: %r vs %r"
                        % (pads[i]["pad_id"], pads[j]["pad_id"]))
    by_net = {}
    for p in pads:
        by_net.setdefault(p["net_id"], []).append(p)
    for nid, ps in by_net.items():
        d = ((ps[0]["x_mm"] - ps[1]["x_mm"]) ** 2
             + (ps[0]["y_mm"] - ps[1]["y_mm"]) ** 2) ** 0.5
        if d < 8.0 - 1e-9:
            raise E4FamilyError("net %s 端点间距 <8mm: %.3f" % (nid, d))
    for p in pads:
        for k in obj["keepouts"]:
            if p["layer"] not in k["layers"]:
                continue
            x0, y0, x1, y1 = k["rect_mm"]
            gx = max(x0 - p["x_mm"], p["x_mm"] - x1, 0.0)
            gy = max(y0 - p["y_mm"], p["y_mm"] - y1, 0.0)
            if (gx * gx + gy * gy) ** 0.5 < 1.0 - 1e-9:
                raise E4FamilyError(
                    "pad %s 距同层 keepout %s <1.0mm"
                    % (p["pad_id"], k["keepout_id"]))


# ---------------------------------------------------------------- 校验

def validate_e4board(obj):
    """e4board 对象校验 -> 错误列表（空=合法；独立实现，零 import v4exp）。"""
    errs = []
    if not isinstance(obj, dict):
        return ["root: 不是对象"]
    if obj.get("schema") != E4BOARD_SCHEMA:
        errs.append("schema: 期望 %r，实际 %r" % (E4BOARD_SCHEMA,
                                                  obj.get("schema")))
    if obj.get("family") != E4_FAMILY:
        errs.append("family: 非法 %r（E4 族=%r）" % (obj.get("family"),
                                                     E4_FAMILY))
    if obj.get("split") not in ("development", "calibration", "holdout"):
        errs.append("split: 非法 %r" % (obj.get("split"),))
    if not isinstance(obj.get("seed"), int) or isinstance(obj["seed"], bool) \
            or obj["seed"] < 0:
        errs.append("seed: 必须是非负整数")
    if obj.get("label") not in ("satisfiable", "unsatisfiable"):
        errs.append("label: 非法 %r" % (obj.get("label"),))
    board = obj.get("board") or {}
    if board.get("layers") != ML_LAYERS:
        errs.append("board.layers: 恒为 %r，实际 %r"
                    % (ML_LAYERS, board.get("layers")))
    if board.get("bbox_mm") != E4_BBOX_MM:
        errs.append("board.bbox_mm: 恒为 %r，实际 %r"
                    % (E4_BBOX_MM, board.get("bbox_mm")))
    if obj.get("rules") != E4_RULES:
        errs.append("rules: 冻结为 E4_RULES（与 mlfamily 一致），实际 %r"
                    % (obj.get("rules"),))
    layer_set = set(ML_LAYERS)
    pads = obj.get("pads")
    if not isinstance(pads, list) or len(pads) != 2 * E4_NET_COUNT:
        errs.append("pads: 必须恰 %d 个（30 网端点），实际 %d"
                    % (2 * E4_NET_COUNT, len(pads) if isinstance(pads, list)
                       else -1))
        pads = pads if isinstance(pads, list) else []
    pad_ids, pad_net = set(), {}
    for i, p in enumerate(pads):
        w = "pads[%d]" % i
        if not isinstance(p, dict):
            errs.append("%s: 不是对象" % w)
            continue
        pid, nid = p.get("pad_id"), p.get("net_id")
        if not isinstance(pid, str) or not pid:
            errs.append("%s.pad_id: 非法 %r" % (w, pid))
        elif pid in pad_ids:
            errs.append("%s.pad_id: 重复 %r" % (w, pid))
        pad_ids.add(pid)
        if not isinstance(nid, str) or not nid:
            errs.append("%s.net_id: 非法 %r" % (w, nid))
        pad_net[pid] = nid
        for k in ("x_mm", "y_mm"):
            if not _is_half_mult(p.get(k)):
                errs.append("%s.%s: 须 0.5 倍数，实际 %r" % (w, k, p.get(k)))
        for k in ("w_mm", "h_mm"):
            if not (isinstance(p.get(k), (int, float)) and p.get(k) > 0):
                errs.append("%s.%s: 须正数，实际 %r" % (w, k, p.get(k)))
        if p.get("layer") not in layer_set:
            errs.append("%s.layer: 层 %r 不在栈" % (w, p.get("layer")))
    nets = obj.get("nets")
    if not isinstance(nets, list) or len(nets) != E4_NET_COUNT:
        errs.append("nets: 必须恰 %d 网，实际 %d"
                    % (E4_NET_COUNT, len(nets) if isinstance(nets, list)
                       else -1))
        nets = nets if isinstance(nets, list) else []
    net_ids = set()
    for i, n in enumerate(nets):
        w = "nets[%d]" % i
        if not isinstance(n, dict):
            errs.append("%s: 不是对象" % w)
            continue
        nid = n.get("net_id")
        if not isinstance(nid, str) or not nid:
            errs.append("%s.net_id: 非法 %r" % (w, nid))
        elif nid in net_ids:
            errs.append("%s.net_id: 重复 %r" % (w, nid))
        net_ids.add(nid)
        if n.get("net_class") not in ("default", "clock"):
            errs.append("%s.net_class: 非法 %r" % (w, n.get("net_class")))
        eps = n.get("endpoints")
        if not isinstance(eps, list) or len(eps) != 2:
            errs.append("%s.endpoints: 恰 2 个 endpoint" % w)
        else:
            for e in eps:
                if e not in pad_ids:
                    errs.append("%s.endpoints: %r 无对应 pad" % (w, e))
                elif pad_net.get(e) != nid:
                    errs.append("%s.endpoints: %r 的 net 与 %r 不一致"
                                % (w, e, nid))
    keepouts = obj.get("keepouts")
    if not isinstance(keepouts, list):
        errs.append("keepouts: 必须是列表")
        keepouts = []
    ko_ids = set()
    for i, k in enumerate(keepouts):
        w = "keepouts[%d]" % i
        if not isinstance(k, dict):
            errs.append("%s: 不是对象" % w)
            continue
        kid = k.get("keepout_id")
        if not isinstance(kid, str) or not kid:
            errs.append("%s.keepout_id: 缺失" % w)
        elif kid in ko_ids:
            errs.append("%s.keepout_id: 重复 %r" % (w, kid))
        ko_ids.add(kid)
        rect = k.get("rect_mm")
        if (not isinstance(rect, list) or len(rect) != 4
                or not all(isinstance(v, (int, float)) for v in rect)):
            errs.append("%s.rect_mm: 必须 4 个数值" % w)
        else:
            if rect[0] >= rect[2] or rect[1] >= rect[3]:
                errs.append("%s.rect_mm: 需 x0<x1 且 y0<y1" % w)
            for j, v in enumerate(rect):
                if not _is_half_mult(v):
                    errs.append("%s.rect_mm[%d]: 须 0.5 倍数，实际 %r"
                                % (w, j, v))
        ls = k.get("layers")
        if not isinstance(ls, list) or not ls:
            errs.append("%s.layers: 必须是非空层列表" % w)
        else:
            for l in ls:
                if l not in layer_set:
                    errs.append("%s.layers: 层 %r 不在栈" % (w, l))
    rels = obj.get("relations")
    if not isinstance(rels, list):
        errs.append("relations: 必须是列表")
    return errs


# ---------------------------------------------------------------- 全链

def _layer_dist(world, routes):
    per_count = {name: 0 for name in world.layers}
    per_len = {name: 0.0 for name in world.layers}
    for r in routes:
        name = str(r["layer"])
        per_count[name] = per_count.get(name, 0) + 1
        pts = r["polyline_mm"]
        length = sum(((float(b[0]) - float(a[0])) ** 2
                      + (float(b[1]) - float(a[1])) ** 2) ** 0.5
                     for a, b in zip(pts, pts[1:]))
        per_len[name] = round(per_len.get(name, 0.0) + length, 6)
    return {"per_layer_route_count": per_count,
            "per_layer_length_mm": per_len}


def _in2_share(dist):
    total = sum(dist["per_layer_length_mm"].values())
    ln = dist["per_layer_length_mm"].get("In2.Cu", 0.0)
    return {"in2_route_count": dist["per_layer_route_count"].get("In2.Cu", 0),
            "in2_length_mm": ln,
            "in2_length_share": round(ln / total, 6) if total > 0 else 0.0}


def _gate_occupancy(world, routes, gates_mm):
    """穿墙路线的内层门归属统计（拥塞观察：每门承载网数）。"""
    x_mid = (_WALL_X0 + _WALL_X1) / 2.0
    counts = {"in1_a": 0, "in1_b": 0, "in2": 0}
    for r in routes:
        if str(r["layer"]) not in ("In1.Cu", "In2.Cu"):
            continue
        pts = r["polyline_mm"]
        hit = False
        for (x, y) in pts:
            if abs(float(x) - x_mid) <= (_WALL_X1 - _WALL_X0) / 2.0 + 1e-9:
                key = "in1" if str(r["layer"]) == "In1.Cu" else "in2x"
                if key == "in1":
                    for g in ("in1_a", "in1_b"):
                        g0, g1 = gates_mm[g]
                        if g0 - 1e-9 <= float(y) <= g1 + 1e-9:
                            counts[g] += 1
                            hit = True
                            break
                else:
                    g0, g1 = gates_mm["in2"]
                    if g0 - 1e-9 <= float(y) <= g1 + 1e-9:
                        counts["in2"] += 1
                        hit = True
                if hit:
                    break
    return counts


def run_l1_chain():
    """L1 全链：8 场景 生成->校验->求解（分层+flat 双臂）->独立复查。

    返回 (records, summary)。零 IO（纯计算）；落盘由 main 负责。
    """
    from ..v4exp.grid import GridWorld
    from .mlchain import check_ml_solution, mlboard_to_v4exp_board
    from .solver2 import solve_board2

    records = []
    for (sid, split, serial) in scenario_ids_e4():
        ml = generate_e4_scenario(sid, split, serial)
        board = mlboard_to_v4exp_board(ml)
        order = sorted(n["net_id"] for n in ml["nets"])
        world = GridWorld(board)

        model = ViaCostModel(list(world.layers))   # 分层默认参数
        layered = solve_board2(board, {"route_order": order,
                                       "group": "E4-L1-layered"},
                               cost_model=model)
        flat = solve_board2(board, {"route_order": order,
                                    "group": "E4-L1-flat"})

        chk_l = check_ml_solution(ml, layered)
        chk_f = check_ml_solution(ml, flat)

        dist_l = _layer_dist(world, layered["routes"])
        dist_f = _layer_dist(world, flat["routes"])
        cl = chk_l["check"]
        records.append({
            "scenario_id": sid,
            "family": E4_FAMILY,
            "split": split,
            "serial": serial,
            "seed": ml["seed"],
            "gates_mm": ml["gates_mm"],
            "validate_errors": 0,
            "layered": {
                "status": layered["status"],
                "route_count": len(layered["routes"]),
                "via_count": layered["metrics"]["via_count"],
                "objective": layered["metrics"]["objective"],
                "objective_layered": layered["metrics"]["objective_layered"],
                "violations_sum": sum(layered["metrics"]["violations"]
                                      .values()),
                "all_connected": layered["metrics"]["all_connected"],
                "max_congestion_overlap_cells":
                    layered["metrics"]["max_congestion_overlap_cells"],
                "per_layer_route_count": dist_l["per_layer_route_count"],
                "per_layer_length_mm": dist_l["per_layer_length_mm"],
                "in2": _in2_share(dist_l),
                "gate_occupancy": _gate_occupancy(world, layered["routes"],
                                                  ml["gates_mm"]),
                "check_gate_pass": chk_l["gate_pass"],
                "check_hard_violations": len(cl["clearance_hard_violations"]),
                "check_cross_disagreements": len(
                    cl["cross_engine_disagreements"]),
                "check_via_span_illegal": len(cl["via_span_illegal"]),
                "check_layer_illegal": len(cl["layer_illegal"]),
                "check_width_illegal": len(cl["width_illegal"]),
                "check_min_foreign_clearance_mm":
                    cl["min_foreign_clearance_mm"],
                "check_pair_pruned": cl["pair_stats"]["pruned_far_by_bbox"],
                "check_pair_same_layer_foreign":
                    cl["pair_stats"]["same_layer_foreign_pairs"],
            },
            "flat": {
                "status": flat["status"],
                "via_count": flat["metrics"]["via_count"],
                "objective": flat["metrics"]["objective"],
                "violations_sum": sum(flat["metrics"]["violations"].values()),
                "all_connected": flat["metrics"]["all_connected"],
                "in2": _in2_share(dist_f),
                "check_gate_pass": chk_f["gate_pass"],
            },
        })
    sat_l = sum(1 for r in records if r["layered"]["status"] == "sat")
    sat_f = sum(1 for r in records if r["flat"]["status"] == "sat")
    hard = sum(r["layered"]["check_hard_violations"] for r in records)
    cross = sum(r["layered"]["check_cross_disagreements"] for r in records)
    in2_scen = sum(1 for r in records
                   if r["layered"]["in2"]["in2_length_share"] > 0)
    in2_flat_scen = sum(1 for r in records
                        if r["flat"]["in2"]["in2_length_share"] > 0)
    summary = {
        "scenario_count": len(records),
        "validate_error_total": sum(r["validate_errors"] for r in records),
        "sat_layered": sat_l,
        "sat_flat": sat_f,
        "check_hard_violation_total": hard,
        "check_cross_disagreement_total": cross,
        "gate_l1_chain_green": (sat_l == len(records) and hard == 0
                                and cross == 0),
        "in2_nonzero_scenarios_layered": in2_scen,
        "in2_nonzero_scenarios_flat": in2_flat_scen,
        "in2_nonzero_share_layered": round(in2_scen / len(records), 6),
    }
    return records, summary


def main(argv=None):
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e4family")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    records, summary = run_l1_chain()
    boards = {sid: None for (sid, _s, _n) in scenario_ids_e4()}
    for (sid, split, serial) in scenario_ids_e4():
        ml = generate_e4_scenario(sid, split, serial)
        write_canonical_json(out / ("board-%s.json" % sid), ml)
    result = {
        "schema": "pcbflow.v4_1.e4-l1-chain/1",
        "declared_date": DECLARED_DATE,
        "family": E4_FAMILY,
        "net_count_per_scenario": E4_NET_COUNT,
        "records": records,
        "summary": summary,
    }
    write_canonical_json(out / "l1-chain.json", result)
    obs = {
        "schema": "pcbflow.v4_1.e4-l1-congestion-observations/1",
        "declared_date": DECLARED_DATE,
        "note": "拥塞/层利用观察台账（E3 遗留 In2 非零动因构造的实测；"
                "分层+冻结对照双报告口径，判读不设门）",
        "records": [{k: r[k] for k in ("scenario_id", "gates_mm",
                                       "layered", "flat")}
                    for r in records],
        "summary": summary,
    }
    write_canonical_json(out / "congestion-observations.json", obs)
    print("f11 L1: %d scenarios, sat_layered=%d/%d, hard=%d, cross=%d, "
          "in2_nonzero(layered)=%d scenarios"
          % (summary["scenario_count"], summary["sat_layered"],
             summary["scenario_count"], summary["check_hard_violation_total"],
             summary["check_cross_disagreement_total"],
             summary["in2_nonzero_scenarios_layered"]))
    return 0 if summary["gate_l1_chain_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
