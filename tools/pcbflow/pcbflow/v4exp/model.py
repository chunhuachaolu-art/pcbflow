"""V4exp 板模型（schema pcbflow.v4exp.board/1）+ canonical JSON/hash 工具。

数据合同见派发 prompt（钉死字段名，逐字符照抄）。本模块只做：
1) 板模型 dataclass 构造与校验（mm 值 0.05 倍数、pad 中心/keepout 边界 0.5 倍数、
   net_id/pad_id 形状、每 net 恰 2 endpoint、clock 网络必须在某 relation 里等）；
2) canonical json / sha256（sort_keys + 紧凑分隔符 + UTF-8；被 hash 的对象先
   递归剔除 *_sha256 键）；
3) 确定性命名的 JSON 读写（键序确定、LF 换行、UTF-8）。

零子进程、零 argv、零 wall-clock。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

SCHEMA_BOARD = "pcbflow.v4exp.board/1"
SCHEMA_SCENARIO_MANIFEST = "pcbflow.v4exp.scenario-manifest/1"
MANIFEST_SCHEMA_VERSION = "v4-route-manifest-1"
LEGEND_VERSION = "v4exp-legend-1"
SVG_SCHEMA = "v4-svg-route-1"
SVG_COORD_SYSTEM = "pcbflow-internal-mm"
SVG_Y_AXIS = "down-positive"

SPLITS = ("development", "calibration", "holdout")
# f6/f7/f8 为 v4cmp 全面对照实验新增 holdout-only 拓扑族（cmp_scenarios）；
# 上一轮 50 场景不受影响，历史产物不回填。
FAMILIES = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8")
LABELS = ("satisfiable", "unsatisfiable")
NET_CLASSES = ("default", "clock")
RELATION_TYPES = ("bus", "differential_pair", "clock_group")
LINE_TYPES = ("signal", "clock", "bus_trunk", "bus_member")

MARGIN_MM = 2.0  # SVG 坐标系边距 M

_NET_ID_RE = re.compile(r"^n([1-9])$")
_PAD_ID_RE = re.compile(r"^[A-Z][A-Za-z0-9]*-[0-9]+$")


# ---------------------------------------------------------------- canonical

def canonical_json(obj) -> str:
    """合同规定的 canonical 形式：sort_keys + 紧凑分隔符 + 非 ASCII 保留。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_bytes(obj) -> bytes:
    return canonical_json(obj).encode("utf-8")


def strip_sha(obj):
    """递归剔除 *_sha256 键（凡被 hash 的对象先做这一步）。

    叶调用消除版（SEC-PERF 2026-09-19）：容器分支内联叶类型判断，
    仅 dict/list 值才递归；值语义与旧版逐位一致（容器全量重建、
    键过滤口径 isinstance(str)+endswidth 不变；str/int/float 子类
    走 isinstance 回退分支）。
    """
    t = type(obj)
    if t is dict:
        return {k: (strip_sha(v) if type(v) is dict or type(v) is list
                    else v)
                for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if t is list:
        return [strip_sha(v) if type(v) is dict or type(v) is list else v
                for v in obj]
    if isinstance(obj, dict):
        return {k: (strip_sha(v) if isinstance(v, (dict, list)) else v)
                for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [strip_sha(v) if isinstance(v, (dict, list)) else v
                for v in obj]
    return obj


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_bytes(strip_sha(obj))).hexdigest()


def write_json(path: str, obj) -> None:
    """确定性落盘：contract 字段序 + 2 空格缩进 + LF + 末尾换行。"""
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_stdin_json():
    import sys
    return json.loads(sys.stdin.read())


# ---------------------------------------------------------------- 数值口径

def is_mm_mult(v, mult: float) -> bool:
    """v 是否为 mult 的倍数（浮点安全：商与最近整数的偏差 <= 1e-6）。"""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    q = float(v) / mult
    return abs(q - round(q)) <= 1e-6


def mm(v) -> float:
    """几何量统一量化到 0.001mm，避免二进制浮点尾巴进入产物。"""
    return round(float(v), 3)


def fmt6(v) -> str:
    return f"{float(v):.6f}"


def fmt3(v) -> str:
    return f"{float(v):.3f}"


def constraint_ref(kind: str, value_mm: float) -> str:
    """constraint_refs 统一口径：C-<kind>-<3位百分毫米>，如 C-width-030
    （0.30mm -> 030；与合同样例 C-clearance-030,C-width-030 同构）。"""
    return f"C-{kind}-{int(round(float(value_mm) * 100)):03d}"


# ---------------------------------------------------------------- dataclass

@dataclass
class ViaRules:
    pad_mm: float = 0.6
    hole_mm: float = 0.3

    def to_obj(self) -> dict:
        return {"pad_mm": self.pad_mm, "hole_mm": self.hole_mm}


@dataclass
class Rules:
    grid_mm: float = 0.25
    clearance_mm: float = 0.3
    width_mm: dict = field(default_factory=lambda: {"default": 0.3,
                                                    "clock": 0.4})
    via: ViaRules = field(default_factory=ViaRules)
    allowed_layers: dict = field(default_factory=lambda: {
        "default": ["F.Cu", "B.Cu"], "clock": ["F.Cu"]})

    def to_obj(self) -> dict:
        return {"grid_mm": self.grid_mm, "clearance_mm": self.clearance_mm,
                "width_mm": dict(self.width_mm),
                "via": self.via.to_obj(),
                "allowed_layers": {k: list(v)
                                   for k, v in self.allowed_layers.items()}}


@dataclass
class Pad:
    pad_id: str
    net_id: str
    x_mm: float
    y_mm: float
    w_mm: float
    h_mm: float
    layer: str

    def to_obj(self) -> dict:
        return {"pad_id": self.pad_id, "net_id": self.net_id,
                "x_mm": self.x_mm, "y_mm": self.y_mm,
                "w_mm": self.w_mm, "h_mm": self.h_mm, "layer": self.layer}


@dataclass
class Net:
    net_id: str
    net_class: str
    endpoints: list

    def to_obj(self) -> dict:
        return {"net_id": self.net_id, "net_class": self.net_class,
                "endpoints": list(self.endpoints)}


@dataclass
class Keepout:
    keepout_id: str
    rect_mm: list
    layers: list

    def to_obj(self) -> dict:
        return {"keepout_id": self.keepout_id, "rect_mm": list(self.rect_mm),
                "layers": list(self.layers)}


@dataclass
class Relation:
    relation_id: str
    relation_type: str
    members: list
    parent_id: object = None

    def to_obj(self) -> dict:
        return {"relation_id": self.relation_id,
                "relation_type": self.relation_type,
                "members": list(self.members), "parent_id": self.parent_id}


@dataclass
class Board:
    scenario_id: str
    split: str
    family: str
    seed: int
    bbox_mm: list
    layers: list
    rules: Rules
    pads: list
    nets: list
    keepouts: list
    relations: list
    label: str

    def to_obj(self) -> dict:
        return {"schema": SCHEMA_BOARD, "scenario_id": self.scenario_id,
                "split": self.split, "family": self.family,
                "seed": self.seed,
                "board": {"bbox_mm": list(self.bbox_mm),
                          "layers": list(self.layers)},
                "rules": self.rules.to_obj(),
                "pads": [p.to_obj() for p in self.pads],
                "nets": [n.to_obj() for n in self.nets],
                "keepouts": [k.to_obj() for k in self.keepouts],
                "relations": [r.to_obj() for r in self.relations],
                "label": self.label}

    # 便捷查询
    def pad_by_id(self, pad_id: str):
        for p in self.pads:
            if p.pad_id == pad_id:
                return p
        return None

    def net_by_id(self, net_id: str):
        for n in self.nets:
            if n.net_id == net_id:
                return n
        return None

    def relation_ids_of_net(self, net_id: str) -> list:
        return [r.relation_id for r in self.relations
                if net_id in r.members]

    def net_class_width(self, net_class: str) -> float:
        return self.rules.width_mm.get(net_class,
                                       self.rules.width_mm["default"])

    def net_allowed_layers(self, net_class: str) -> list:
        return list(self.rules.allowed_layers.get(
            net_class, self.rules.allowed_layers["default"]))


# ---------------------------------------------------------------- 校验

# scenario_id 合法字符集（SEC-B-04 收口，align-r1 2026-09-25）：单段标识符
# 直接拼入 route-manifest-%s.json / route-preview-%s.svg 文件名，须防
# ../ 穿越与路径分隔符（对齐 corpus_pcbench MANIFEST_PATH_RE_STR 的
# 无斜杠单段口径；".." 另行显式禁——字符集内连续两点仍属路径上跳）。
_SCENARIO_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _num_err(where, v, mult, need_half=False, errs=None, label=""):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        errs.append(f"{where}: {label}不是数值")
        return
    if not is_mm_mult(v, 0.05):
        errs.append(f"{where}: {label}={v} 不是 0.05 的倍数")
    if need_half and not is_mm_mult(v, 0.5):
        errs.append(f"{where}: {label}={v} 不是 0.5 的倍数")


def validate_board(obj) -> list:
    """按合同校验板模型对象；返回错误列表（空 = 合法）。"""
    errs = []
    if not isinstance(obj, dict):
        return ["root: 不是对象"]
    if obj.get("schema") != SCHEMA_BOARD:
        errs.append(f"schema: 期望 {SCHEMA_BOARD}，实际 {obj.get('schema')!r}")
    sid = obj.get("scenario_id")
    if not isinstance(sid, str) or not sid:
        errs.append("scenario_id: 缺失或非字符串")
    elif not _SCENARIO_ID_RE.match(sid) or ".." in sid:
        errs.append(f"scenario_id: 非法字符（仅 [A-Za-z0-9._-] 且禁 ..）: {sid!r}")
    if obj.get("split") not in SPLITS:
        errs.append(f"split: 非法 {obj.get('split')!r}")
    if obj.get("family") not in FAMILIES:
        errs.append(f"family: 非法 {obj.get('family')!r}")
    seed = obj.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        errs.append("seed: 必须是非负整数")
    if obj.get("label") not in LABELS:
        errs.append(f"label: 非法 {obj.get('label')!r}")

    board = obj.get("board") or {}
    bbox = board.get("bbox_mm")
    if (not isinstance(bbox, list) or len(bbox) != 4
            or not all(isinstance(v, (int, float)) for v in bbox)):
        errs.append("board.bbox_mm: 必须是 4 个数值")
    else:
        for i, v in enumerate(bbox):
            _num_err(f"board.bbox_mm[{i}]", v, 0.05, errs=errs, label="坐标")
        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            errs.append("board.bbox_mm: 需 x0<x1 且 y0<y1")
    layers = board.get("layers")
    if (not isinstance(layers, list) or not layers
            or not all(isinstance(v, str) and v for v in layers)):
        errs.append("board.layers: 必须是非空字符串列表")
    layer_set = set(layers or [])

    rules = obj.get("rules") or {}
    if not is_mm_mult(rules.get("grid_mm"), 0.05):
        errs.append("rules.grid_mm: 缺失或不是 0.05 的倍数")
    if not is_mm_mult(rules.get("clearance_mm"), 0.05):
        errs.append("rules.clearance_mm: 缺失或不是 0.05 的倍数")
    width = rules.get("width_mm") or {}
    for k in ("default", "clock"):
        if not is_mm_mult(width.get(k), 0.05) or not width.get(k) > 0:
            errs.append(f"rules.width_mm.{k}: 缺失或不是正的 0.05 倍数")
    via = rules.get("via") or {}
    for k in ("pad_mm", "hole_mm"):
        if not is_mm_mult(via.get(k), 0.05) or not via.get(k) > 0:
            errs.append(f"rules.via.{k}: 缺失或不是正的 0.05 倍数")
    if via.get("hole_mm") is not None and via.get("pad_mm") is not None \
            and via["hole_mm"] >= via["pad_mm"]:
        errs.append("rules.via: hole_mm 必须小于 pad_mm")
    allowed = rules.get("allowed_layers") or {}
    for k in ("default", "clock"):
        ls = allowed.get(k)
        if not isinstance(ls, list) or not ls:
            errs.append(f"rules.allowed_layers.{k}: 必须是非空层列表")
        else:
            for l in ls:
                if l not in layer_set:
                    errs.append(f"rules.allowed_layers.{k}: 层 {l!r} 不在板层中")

    pads = obj.get("pads")
    if not isinstance(pads, list) or not pads:
        errs.append("pads: 必须是非空列表")
        pads = []
    pad_ids = set()
    pad_net = {}
    for i, p in enumerate(pads):
        where = f"pads[{i}]"
        if not isinstance(p, dict):
            errs.append(f"{where}: 不是对象")
            continue
        pid = p.get("pad_id")
        if not isinstance(pid, str) or not _PAD_ID_RE.match(pid or ""):
            errs.append(f"{where}.pad_id: 形如 U1-1/J2-3，实际 {pid!r}")
        elif pid in pad_ids:
            errs.append(f"{where}.pad_id: 重复 {pid!r}")
        pad_ids.add(pid)
        nid = p.get("net_id")
        if not isinstance(nid, str) or not _NET_ID_RE.match(nid or ""):
            errs.append(f"{where}.net_id: 形如 n1..n9，实际 {nid!r}")
        pad_net[pid] = nid
        for k in ("x_mm", "y_mm"):
            _num_err(f"{where}.{k}", p.get(k), 0.05, need_half=True,
                     errs=errs, label=k)
        for k in ("w_mm", "h_mm"):
            _num_err(f"{where}.{k}", p.get(k), 0.05, errs=errs, label=k)
            if not (isinstance(p.get(k), (int, float))
                    and p.get(k) > 0):
                errs.append(f"{where}.{k}: 必须为正")
        if p.get("layer") not in layer_set:
            errs.append(f"{where}.layer: 层 {p.get('layer')!r} 不在板层中")

    nets = obj.get("nets")
    if not isinstance(nets, list) or not nets:
        errs.append("nets: 必须是非空列表")
        nets = []
    net_ids = set()
    clock_nets = []
    for i, n in enumerate(nets):
        where = f"nets[{i}]"
        if not isinstance(n, dict):
            errs.append(f"{where}: 不是对象")
            continue
        nid = n.get("net_id")
        if not isinstance(nid, str) or not _NET_ID_RE.match(nid or ""):
            errs.append(f"{where}.net_id: 形如 n1..n9，实际 {nid!r}")
        elif nid in net_ids:
            errs.append(f"{where}.net_id: 重复 {nid!r}")
        net_ids.add(nid)
        if n.get("net_class") not in NET_CLASSES:
            errs.append(f"{where}.net_class: 非法 {n.get('net_class')!r}")
        elif n["net_class"] == "clock":
            clock_nets.append(nid)
        eps = n.get("endpoints")
        if not isinstance(eps, list) or len(eps) != 2:
            errs.append(f"{where}.endpoints: 每个 net 恰好 2 个 endpoint")
        else:
            for e in eps:
                if e not in pad_ids:
                    errs.append(f"{where}.endpoints: endpoint {e!r} 无对应 pad")
                elif pad_net.get(e) != nid:
                    errs.append(f"{where}.endpoints: {e!r} 的 net_id 与"
                                f" {nid!r} 不一致")

    keepouts = obj.get("keepouts")
    if not isinstance(keepouts, list):
        errs.append("keepouts: 必须是列表")
        keepouts = []
    ko_ids = set()
    for i, k in enumerate(keepouts):
        where = f"keepouts[{i}]"
        if not isinstance(k, dict):
            errs.append(f"{where}: 不是对象")
            continue
        kid = k.get("keepout_id")
        if not isinstance(kid, str) or not kid:
            errs.append(f"{where}.keepout_id: 缺失")
        elif kid in ko_ids:
            errs.append(f"{where}.keepout_id: 重复 {kid!r}")
        ko_ids.add(kid)
        rect = k.get("rect_mm")
        if (not isinstance(rect, list) or len(rect) != 4
                or not all(isinstance(v, (int, float)) for v in rect)):
            errs.append(f"{where}.rect_mm: 必须 4 个数值")
        else:
            for j, v in enumerate(rect):
                _num_err(f"{where}.rect_mm[{j}]", v, 0.05, need_half=True,
                         errs=errs, label="边界")
            if rect[0] >= rect[2] or rect[1] >= rect[3]:
                errs.append(f"{where}.rect_mm: 需 x0<x1 且 y0<y1")
            if isinstance(bbox, list) and len(bbox) == 4:
                if (rect[0] < bbox[0] or rect[1] < bbox[1]
                        or rect[2] > bbox[2] or rect[3] > bbox[3]):
                    errs.append(f"{where}.rect_mm: 超出板 bbox")
        ls = k.get("layers")
        if not isinstance(ls, list) or not ls:
            errs.append(f"{where}.layers: 必须是非空层列表")
        else:
            for l in ls:
                if l not in layer_set:
                    errs.append(f"{where}.layers: 层 {l!r} 不在板层中")

    relations = obj.get("relations")
    if not isinstance(relations, list):
        errs.append("relations: 必须是列表")
        relations = []
    rel_ids = set()
    related_net_ids = set()
    for i, r in enumerate(relations):
        where = f"relations[{i}]"
        if not isinstance(r, dict):
            errs.append(f"{where}: 不是对象")
            continue
        rid = r.get("relation_id")
        if not isinstance(rid, str) or not rid:
            errs.append(f"{where}.relation_id: 缺失")
        elif rid in rel_ids:
            errs.append(f"{where}.relation_id: 重复 {rid!r}")
        rel_ids.add(rid)
        if r.get("relation_type") not in RELATION_TYPES:
            errs.append(f"{where}.relation_type: 非法 {r.get('relation_type')!r}")
        members = r.get("members")
        if not isinstance(members, list) or len(members) < 1:
            errs.append(f"{where}.members: 至少 1 个成员")
        else:
            if r.get("relation_type") == "differential_pair" \
                    and len(members) != 2:
                errs.append(f"{where}.members: differential_pair"
                            " 恰好 2 个成员")
            for m in members:
                if m not in net_ids:
                    errs.append(f"{where}.members: 成员 {m!r} 不是已定义 net")
                else:
                    related_net_ids.add(m)
        if "parent_id" in r and r.get("parent_id") is not None \
                and r.get("parent_id") not in rel_ids:
            errs.append(f"{where}.parent_id: 引用未知 relation")
    for nid in clock_nets:
        if nid not in related_net_ids:
            errs.append(f"nets: clock 网络 {nid} 必须出现在某个 relation 里")

    return errs


def board_from_obj(obj) -> Board:
    """校验并构造 Board dataclass；非法抛 ValueError。"""
    errs = validate_board(obj)
    if errs:
        raise ValueError("board 校验失败: " + "; ".join(errs))
    rules = Rules(
        grid_mm=obj["rules"]["grid_mm"],
        clearance_mm=obj["rules"]["clearance_mm"],
        width_mm=dict(obj["rules"]["width_mm"]),
        via=ViaRules(pad_mm=obj["rules"]["via"]["pad_mm"],
                     hole_mm=obj["rules"]["via"]["hole_mm"]),
        allowed_layers={k: list(v)
                        for k, v in obj["rules"]["allowed_layers"].items()})
    return Board(
        scenario_id=obj["scenario_id"], split=obj["split"],
        family=obj["family"], seed=obj["seed"],
        bbox_mm=list(obj["board"]["bbox_mm"]),
        layers=list(obj["board"]["layers"]),
        rules=rules,
        pads=[Pad(**p) for p in obj["pads"]],
        nets=[Net(n["net_id"], n["net_class"], list(n["endpoints"]))
              for n in obj["nets"]],
        keepouts=[Keepout(k["keepout_id"], list(k["rect_mm"]), list(k["layers"]))
                  for k in obj["keepouts"]],
        relations=[Relation(r["relation_id"], r["relation_type"],
                            list(r["members"]), r.get("parent_id"))
                   for r in obj["relations"]],
        label=obj["label"])
