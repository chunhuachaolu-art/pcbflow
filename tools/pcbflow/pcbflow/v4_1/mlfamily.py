"""pcbflow.v4_1.mlfamily -- 多层合成场景族（E2 新增族 f9/f10；堵 K2）。

任务书 §3 E2：合成场景族扩展——新增多层族（f9 起）；f1–f8 双层族与既有
112 场景 manifest 零改动（回归基线，hash 对照 E0 baseline.json）。

域设计（schema pcbflow.v4_1.mlboard/1）：

- 层栈恒为 4 层 [F.Cu, In1.Cu, In2.Cu, B.Cu]（任务书起步口径）；
- 板形状与 v4exp 板 schema 同构（bbox/layers/rules/pads/nets/keepouts/
  relations/label），使求解适配层（mlchain.mlboard_to_v4exp_board）为
  纯投影——v4exp 求解器零改动红线不破；
- 多层特有：pad 可位于任意铜层（f9 端点跨外层 → 强制换层）；keepout
  可指定层子集（内层墙/外层墙）；net class 的 allowed_layers 生效
  （default=全 4 层；clock=[F.Cu, B.Cu] 外层对）；
- 规则参数与 v4exp 冻结格点契约物理一致（E2 全链检查腿用 v4_1 精确
  几何内核复查求解输出，要求格点可达间距 ≥ 物理要求）：
  grid=0.25、clearance=0.25、width(default)=width(clock)=0.20、
  via pad=0.40/hole=0.20——双类同宽是格点契约与逐类宽度分轨的显式
  设计决定（逐类宽度/间距对拍在 e2parity 域，不混入本族；见 e2 报告）。

族语义：

- f9 多层换层族：3–5 网，左排 pad 在 F.Cu、右排 pad 在 B.Cu（端点跨
  外层 → 贯通换层必经）；In1+In2 中央横墙（留中央门洞）迫使路线在
  内层门洞处集中或绕行；satisfiable；
- f10 内层走廊族：3–5 网，端点同在 F.Cu；F.Cu+B.Cu 双外层墙（留门洞）
  迫使下沉内层走内层走廊再回升；其中 hol-03/hol-04 为多层不可满足
  构造（endpoint 被全 4 层环形 keepout 围死——换层不可逃逸），label
  = unsatisfiable，全链按 failed 如实报告（不渲染 sat）。

确定性：无 wall-clock、无网络；seed = sha256(scenario_id) 前 4 字节
大端整数（沿 v4exp gen_scenarios.seed_for 策略）；同 out_dir 重跑逐
字节一致（canonical JSON）。

零 IO（生成纯函数）、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import hashlib
import random

__all__ = [
    "MLBOARD_SCHEMA", "ML_FAMILIES", "ML_LAYERS", "ML_RULES",
    "BBOX_MM", "SPLIT3", "SERIALS_ML", "scenario_ids_ml", "seed_for_ml",
    "validate_mlboard", "generate_ml_scenario", "generate_all_ml",
    "MLNetClassError",
]

MLBOARD_SCHEMA = "pcbflow.v4_1.mlboard/1"
ML_FAMILIES = ("f9", "f10")
ML_LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
BBOX_MM = [0.0, 0.0, 40.0, 30.0]

#: 规则参数（与 v4exp 冻结格点契约物理一致，见模块 docstring 论证）
ML_RULES = {
    "grid_mm": 0.25,
    "clearance_mm": 0.25,
    "width_mm": {"default": 0.2, "clock": 0.2},
    "via": {"pad_mm": 0.4, "hole_mm": 0.2},
    "allowed_layers": {
        "default": list(ML_LAYERS),
        "clock": ["F.Cu", "B.Cu"],
    },
}

SPLIT3 = {"development": "dev", "calibration": "cal", "holdout": "hol"}
SERIALS_ML = [
    ("development", range(1, 7)),
    ("calibration", range(7, 9)),
    ("holdout", range(9, 11)),
]

COMPONENTS = ["U1", "U2", "J2", "J3", "U3", "U4"]
PAD_W = 1.2
PAD_H = 1.2

_NET_CLASSES_ML = ("default", "clock")


class MLNetClassError(ValueError):
    """mlboard 校验 fail-closed。"""


def seed_for_ml(scenario_id):
    """seed = sha256(scenario_id) 前 4 字节大端整数（v4exp 同策略）。"""
    digest = hashlib.sha256(scenario_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def scenario_ids_ml():
    """(scenario_id, family, split, serial) 全列表（确定性序）。"""
    out = []
    for fam in ML_FAMILIES:
        for split, serials in SERIALS_ML:
            for s in serials:
                out.append(("%s-%s-%02d" % (SPLIT3[split], fam, s),
                            fam, split, s))
    return out


# ---------------------------------------------------------------- 校验

def _is_mm_mult(v, mult):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    q = float(v) / mult
    return abs(q - round(q)) <= 1e-6


def validate_mlboard(obj):
    """mlboard 对象校验 -> 错误列表（空=合法；独立实现，零 import v4exp）。"""
    errs = []
    if not isinstance(obj, dict):
        return ["root: 不是对象"]
    if obj.get("schema") != MLBOARD_SCHEMA:
        errs.append("schema: 期望 %s，实际 %r" % (MLBOARD_SCHEMA,
                                                  obj.get("schema")))
    if obj.get("family") not in ML_FAMILIES:
        errs.append("family: 非法 %r（多层族=%r）" % (obj.get("family"),
                                                     ML_FAMILIES))
    if obj.get("split") not in SPLIT3:
        errs.append("split: 非法 %r" % (obj.get("split"),))
    if not isinstance(obj.get("seed"), int) or isinstance(obj.get("seed"), bool) \
            or obj["seed"] < 0:
        errs.append("seed: 必须是非负整数")
    if obj.get("label") not in ("satisfiable", "unsatisfiable"):
        errs.append("label: 非法 %r" % (obj.get("label"),))

    board = obj.get("board") or {}
    if board.get("layers") != ML_LAYERS:
        errs.append("board.layers: 多层族恒为 %r，实际 %r"
                    % (ML_LAYERS, board.get("layers")))
    bbox = board.get("bbox_mm")
    if (not isinstance(bbox, list) or len(bbox) != 4
            or not all(isinstance(v, (int, float)) for v in bbox)):
        errs.append("board.bbox_mm: 必须 4 个数值")
    else:
        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            errs.append("board.bbox_mm: 需 x0<x1 且 y0<y1")

    rules = obj.get("rules") or {}
    if rules != ML_RULES:
        errs.append("rules: 多层族规则冻结为 ML_RULES（格点契约物理一致"
                    "论证），实际 %r" % (rules,))

    layer_set = set(ML_LAYERS)
    pads = obj.get("pads")
    if not isinstance(pads, list) or not pads:
        errs.append("pads: 必须是非空列表")
        pads = []
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
            if not _is_mm_mult(p.get(k), 0.5):
                errs.append("%s.%s: 须 0.5 倍数，实际 %r" % (w, k, p.get(k)))
        for k in ("w_mm", "h_mm"):
            if not _is_mm_mult(p.get(k), 0.05) or not p.get(k, 0) > 0:
                errs.append("%s.%s: 须正的 0.05 倍数，实际 %r"
                            % (w, k, p.get(k)))
        if p.get("layer") not in layer_set:
            errs.append("%s.layer: 层 %r 不在多层栈" % (w, p.get("layer")))

    nets = obj.get("nets")
    if not isinstance(nets, list) or not nets:
        errs.append("nets: 必须是非空列表")
        nets = []
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
        if n.get("net_class") not in _NET_CLASSES_ML:
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
                if not _is_mm_mult(v, 0.5):
                    errs.append("%s.rect_mm[%d]: 须 0.5 倍数，实际 %r"
                                % (w, j, v))
        ls = k.get("layers")
        if not isinstance(ls, list) or not ls:
            errs.append("%s.layers: 必须是非空层列表" % w)
        else:
            for l in ls:
                if l not in layer_set:
                    errs.append("%s.layers: 层 %r 不在多层栈" % (w, l))

    rels = obj.get("relations")
    if not isinstance(rels, list):
        errs.append("relations: 必须是列表")
        rels = []
    rel_ids = set()
    for i, r in enumerate(rels):
        w = "relations[%d]" % i
        if not isinstance(r, dict):
            errs.append("%s: 不是对象" % w)
            continue
        rid = r.get("relation_id")
        if not isinstance(rid, str) or not rid:
            errs.append("%s.relation_id: 缺失" % w)
        elif rid in rel_ids:
            errs.append("%s.relation_id: 重复 %r" % (w, rid))
        rel_ids.add(rid)
        if r.get("relation_type") not in ("bus", "clock_group"):
            errs.append("%s.relation_type: 非法 %r" % (w, r.get("relation_type")))
        for m in r.get("members") or []:
            if m not in net_ids:
                errs.append("%s.members: %r 不是已定义 net" % (w, m))
    return errs


# ---------------------------------------------------------------- 生成

class _PadAlloc:
    """组件/引脚号分配（沿 v4exp PadAlloc 语义，独立实现）。"""

    def __init__(self):
        self.pin = {}

    def pad(self, comp, net_id, x, y, layer):
        n = self.pin.get(comp, 0) + 1
        self.pin[comp] = n
        return {"pad_id": "%s-%d" % (comp, n), "net_id": net_id,
                "x_mm": x, "y_mm": y, "w_mm": PAD_W, "h_mm": PAD_H,
                "layer": layer}


def _spaced(rng, count, lo, hi, gap):
    """[lo,hi] 内取 count 个 0.5 倍数值，两两间距 >= gap（有序统计法）。"""
    step = 0.5
    d = int(round(gap / step))
    mlo, mhi = int(round(lo / step)), int(round(hi / step))
    span = mhi - mlo - (count - 1) * d
    if span < 0:
        raise RuntimeError("spaced 不可行 count=%d lo=%s hi=%s gap=%s"
                           % (count, lo, hi, gap))
    picks = sorted(rng.randint(0, span) for _ in range(count))
    return [step * (p + i * d + mlo) for i, p in enumerate(picks)]


def _post_check(obj):
    """生成期自检：pad 中心到各 keepout 矩形（同层）平面距离 >= 1.0mm；
    endpoint 间距 >= 8mm；pad 两两中心距 >= 2.0mm。违反=生成器 bug。"""
    pads, keepouts = obj["pads"], obj["keepouts"]
    for p in pads:
        for k in keepouts:
            if p["layer"] not in k["layers"]:
                continue
            x0, y0, x1, y1 = k["rect_mm"]
            dx = max(x0 - p["x_mm"], 0.0, p["x_mm"] - x1)
            dy = max(y0 - p["y_mm"], 0.0, p["y_mm"] - y1)
            if (dx * dx + dy * dy) ** 0.5 < 1.0:
                raise RuntimeError(
                    "%s: pad %s 距 keepout %s 过近" % (obj["scenario_id"],
                                                       p["pad_id"],
                                                       k["keepout_id"]))
    by_id = {p["pad_id"]: p for p in pads}
    for n in obj["nets"]:
        a, b = (by_id[e] for e in n["endpoints"])
        dist = ((a["x_mm"] - b["x_mm"]) ** 2
                + (a["y_mm"] - b["y_mm"]) ** 2) ** 0.5
        if dist < 8.0:
            raise RuntimeError("%s: net %s endpoint 间距 %.2f < 8mm"
                               % (obj["scenario_id"], n["net_id"], dist))
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            d = ((pads[i]["x_mm"] - pads[j]["x_mm"]) ** 2
                 + (pads[i]["y_mm"] - pads[j]["y_mm"]) ** 2) ** 0.5
            if d < 2.0:
                raise RuntimeError("%s: pad %s/%s 间距 %.2f < 2mm"
                                   % (obj["scenario_id"], pads[i]["pad_id"],
                                      pads[j]["pad_id"], d))


def _finish(scenario_id, split, family, seed, pads, nets, keepouts,
            relations, label):
    obj = {
        "schema": MLBOARD_SCHEMA,
        "scenario_id": scenario_id,
        "split": split,
        "family": family,
        "seed": seed,
        "board": {"bbox_mm": list(BBOX_MM), "layers": list(ML_LAYERS)},
        "rules": {
            "grid_mm": ML_RULES["grid_mm"],
            "clearance_mm": ML_RULES["clearance_mm"],
            "width_mm": dict(ML_RULES["width_mm"]),
            "via": dict(ML_RULES["via"]),
            "allowed_layers": {k: list(v) for k, v in
                               ML_RULES["allowed_layers"].items()},
        },
        "pads": pads,
        "nets": nets,
        "keepouts": keepouts,
        "relations": relations,
        "label": label,
        "ml_meta": {
            "layer_stack": list(ML_LAYERS),
            "via_span_policy": "inclusive-stack-interval (layerstack)",
            "design_note": "多层族规则=格点契约物理一致参数；逐类宽度/"
                           "间距对拍在 e2parity 域",
        },
    }
    errs = validate_mlboard(obj)
    if errs:
        raise RuntimeError("%s 生成校验失败: %s" % (scenario_id, errs))
    _post_check(obj)
    return obj


def gen_f9(sid, split, seed, rng):
    """f9 多层换层族：左排 F.Cu / 右排 B.Cu（端点跨外层）；In1+In2 中央
    横墙留门洞（内层集中走廊）；1 个 clock 网（限外层对 [F.Cu, B.Cu]）。"""
    alloc = _PadAlloc()
    n = rng.choice([3, 4, 5])
    lys = _spaced(rng, n, 4.0, 26.0, 3.0)
    rys = _spaced(rng, n, 4.0, 26.0, 3.0)
    gate_y0 = 12.0
    gate_y1 = 18.0
    pads, nets = [], []
    clock_idx = n - 1  # 末网为 clock（外层对限层）
    for i in range(n):
        nid = "n%d" % (i + 1)
        cls = "clock" if i == clock_idx else "default"
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, rng.choice([3.0, 5.0]), lys[i],
                              "F.Cu"))
        pads.append(alloc.pad(cb, nid, rng.choice([35.0, 37.0]), rys[i],
                              "B.Cu"))
        nets.append({"net_id": nid, "net_class": cls,
                     "endpoints": [pads[-2]["pad_id"], pads[-1]["pad_id"]]})
    # 内层墙（In1+In2）：上下两条，留中央门洞 [12,18]
    inner = ["In1.Cu", "In2.Cu"]
    keepouts = [
        {"keepout_id": "kw1", "rect_mm": [8.0, 0.0, 32.0, gate_y0],
         "layers": list(inner)},
        {"keepout_id": "kw2", "rect_mm": [8.0, gate_y1, 32.0, 30.0],
         "layers": list(inner)},
    ]
    relations = ([{"relation_id": "CLK-1", "relation_type": "clock_group",
                   "members": ["n%d" % (clock_idx + 1)], "parent_id": None}]
                 if n >= 1 else [])
    return _finish(sid, split, "f9", seed, pads, nets, keepouts,
                   relations, "satisfiable")


def gen_f10(sid, split, seed, rng):
    """f10 内层走廊族：端点同 F.Cu；外层双墙（F.Cu+B.Cu）留门洞迫使
    下沉内层；hol-03/04 为全 4 层环形围死的多层不可满足构造。"""
    alloc = _PadAlloc()
    if split == "holdout":
        # 多层不可满足（holdout 两个实例）：n1 的 endpoint 之一被全 4 层
        # 环形 keepout 围死（换层不可逃逸——f5 双层环形构造的多层推广；
        # n 限 2–3：环外 pad 槽位 [4,12]/gap2 容量所限，同 v4exp f5 口径）
        n = rng.choice([2, 3])
        ex = rng.choice([16.0, 18.0, 20.0, 22.0])
        ey = rng.choice([16.0, 18.0])
        ys = _spaced(rng, 1 + 2 * (n - 1), 4.0, 12.0, 2.0)
        pads = [alloc.pad("U1", "n1", ex, ey, "F.Cu"),
                alloc.pad("J2", "n1", 5.0, ys[0], "F.Cu")]
        nets = [{"net_id": "n1", "net_class": "default",
                 "endpoints": [pads[0]["pad_id"], pads[1]["pad_id"]]}]
        k = 1
        for i in range(n - 1):
            nid = "n%d" % (i + 2)
            ca, cb = COMPONENTS[2 * (i + 1) % 6], COMPONENTS[(2 * (i + 1) + 1) % 6]
            pads.append(alloc.pad(ca, nid, 5.0, ys[k], "F.Cu"))
            pads.append(alloc.pad(cb, nid, 35.0, ys[k + 1], "F.Cu"))
            nets.append({"net_id": nid, "net_class": "default",
                         "endpoints": [pads[-2]["pad_id"],
                                       pads[-1]["pad_id"]]})
            k += 2
        keepouts = [
            {"keepout_id": "kr1", "rect_mm": [ex - 3.0, ey - 3.0, ex + 3.0, ey - 1.0],
             "layers": list(ML_LAYERS)},
            {"keepout_id": "kr2", "rect_mm": [ex - 3.0, ey + 1.0, ex + 3.0, ey + 3.0],
             "layers": list(ML_LAYERS)},
            {"keepout_id": "kr3", "rect_mm": [ex - 3.0, ey - 1.0, ex - 1.0, ey + 1.0],
             "layers": list(ML_LAYERS)},
            {"keepout_id": "kr4", "rect_mm": [ex + 1.0, ey - 1.0, ex + 3.0, ey + 1.0],
             "layers": list(ML_LAYERS)},
        ]
        return _finish(sid, split, "f10", seed, pads, nets, keepouts, [],
                       "unsatisfiable")
    n = rng.choice([3, 4, 5])
    lys = _spaced(rng, n, 4.0, 26.0, 3.0)
    rys = _spaced(rng, n, 4.0, 26.0, 3.0)
    gate_y0 = 13.0
    gate_y1 = 17.0
    pads, nets = [], []
    for i in range(n):
        nid = "n%d" % (i + 1)
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, rng.choice([3.0, 5.0]), lys[i],
                              "F.Cu"))
        pads.append(alloc.pad(cb, nid, rng.choice([35.0, 37.0]), rys[i],
                              "F.Cu"))
        nets.append({"net_id": nid, "net_class": "default",
                     "endpoints": [pads[-2]["pad_id"], pads[-1]["pad_id"]]})
    outer = ["F.Cu", "B.Cu"]
    keepouts = [
        {"keepout_id": "kw1", "rect_mm": [8.0, 0.0, 32.0, gate_y0],
         "layers": list(outer)},
        {"keepout_id": "kw2", "rect_mm": [8.0, gate_y1, 32.0, 30.0],
         "layers": list(outer)},
    ]
    return _finish(sid, split, "f10", seed, pads, nets, keepouts, [],
                   "satisfiable")


_GENS = {"f9": gen_f9, "f10": gen_f10}


def generate_ml_scenario(scenario_id):
    """scenario_id -> mlboard 对象（确定性；seed 由 id 派生）。"""
    for sid, fam, split, serial in scenario_ids_ml():
        if sid == scenario_id:
            seed = seed_for_ml(sid)
            return _GENS[fam](sid, split, seed, random.Random(seed))
    raise MLNetClassError("未知多层场景 id（fail-closed）: %r" % (scenario_id,))


def generate_all_ml():
    """全部多层场景（20 个：f9×10 + f10×10）对象列表（确定性序）。"""
    out = []
    for sid, fam, split, serial in scenario_ids_ml():
        seed = seed_for_ml(sid)
        out.append(_GENS[fam](sid, split, seed, random.Random(seed)))
    return out
