"""pcbflow.v4_1.netclasses -- net class 载入与逐网 clearance 矩阵（E1 交付
件 2；任务书 §3 E1）。

载入源优先序（fail-closed，不静默挑源）：

1. 板文本 net_class 节点（KiCad <= 8 板内格式；成员=节点内 (net "名")）；
2. .kicad_pro 工程文件 net_settings（KiCad >= 8：classes +
   netclass_assignments（精确指派）+ netclass_patterns（通配模式，
   fnmatch 语义，列表序首匹配）；
3. 显式声明缺省（declared_defaults：调用方显式给出 Default 类参数，
   仅 advisory 用，来源须可追溯）；
4. 以上皆缺 -> NetClassNotAvailable（fail-closed 显式登记 not_available，
   消费方必须 blocked，不得隐式假定数值）。

多源并存=ambiguous_source 错误（不静默择一）。

clearance 语义：两网间要求间距 = max(两类 clearance)（KiCad 口径：异网
物项对取两侧 net class 的较大 clearance）。

校验 fail-closed：类名空/缺失 Default 类/非有限或负 clearance/track_width/
via 尺寸、模式引用未定义类、未知 JSON 结构。

零 IO（输入文本/已解析对象）、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import fnmatch
import math

from .. import sexpr_min

__all__ = [
    "NetClassError", "NetClassNotAvailable", "NetClass", "NetClassTable",
    "load_netclasses", "netclass_table_from_board_text",
    "netclass_table_from_kicad_pro", "netclass_table_from_declared_defaults",
]


class NetClassError(ValueError):
    """net class 校验 fail-closed。"""


class NetClassNotAvailable(NetClassError):
    """net class 缺失（fail-closed 显式 not_available）。"""


def _num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise NetClassError("%s 非数值（fail-closed）: %r" % (what, v))
    v = float(v)
    if not math.isfinite(v):
        raise NetClassError("%s 非有限数（fail-closed）: %r" % (what, v))
    return v


def _nonneg(v, what):
    v = _num(v, what)
    if v < 0.0:
        raise NetClassError("%s 为负（fail-closed）: %r" % (what, v))
    return v


class NetClass:
    __slots__ = ("name", "clearance_mm", "track_width_mm", "via_dia_mm",
                 "via_drill_mm")

    def __init__(self, name, clearance_mm, track_width_mm=None,
                 via_dia_mm=None, via_drill_mm=None):
        if not isinstance(name, str) or not name:
            raise NetClassError("类名非法（fail-closed）: %r" % (name,))
        self.name = name
        self.clearance_mm = _nonneg(clearance_mm, "%s.clearance" % name)
        self.track_width_mm = None if track_width_mm is None \
            else _nonneg(track_width_mm, "%s.track_width" % name)
        self.via_dia_mm = None if via_dia_mm is None \
            else _nonneg(via_dia_mm, "%s.via_dia" % name)
        self.via_drill_mm = None if via_drill_mm is None \
            else _nonneg(via_drill_mm, "%s.via_drill" % name)

    def as_dict(self):
        return {
            "name": self.name,
            "clearance_mm": round(self.clearance_mm, 6),
            "track_width_mm": None if self.track_width_mm is None
            else round(self.track_width_mm, 6),
            "via_dia_mm": None if self.via_dia_mm is None
            else round(self.via_dia_mm, 6),
            "via_drill_mm": None if self.via_drill_mm is None
            else round(self.via_drill_mm, 6),
        }


class NetClassTable:
    """逐网 clearance 矩阵（载入后只读）。"""

    def __init__(self, classes, assignments, patterns, source):
        if not classes:
            raise NetClassError("类表为空（fail-closed）")
        if "Default" not in classes:
            raise NetClassError("缺 Default 类（fail-closed）: %r"
                                % (sorted(classes),))
        self.classes = dict(classes)
        self.default = self.classes["Default"]
        self.assignments = dict(assignments)
        self.patterns = list(patterns)
        self.source = source
        self.ambiguities = []
        for net, cls in self.assignments.items():
            if cls not in self.classes:
                raise NetClassError("精确指派引用未定义类（fail-closed）: "
                                    "%r -> %r" % (net, cls))
        seen = set()
        for cls, pat in self.patterns:
            if cls not in self.classes:
                raise NetClassError("模式引用未定义类（fail-closed）: "
                                    "%r -> %r" % (pat, cls))
            key = (pat, cls)
            if key in seen:
                raise NetClassError("重复模式（fail-closed）: %r" % (key,))
            seen.add(key)
        self._ambiguity_seen = set()

    # ------------------------------------------------------------ 查询

    def resolve(self, net):
        """网 -> NetClass：精确指派 -> 模式（列表序首匹配）-> Default。"""
        if not isinstance(net, str):
            raise NetClassError("网名非法（fail-closed）: %r" % (net,))
        cls = self.assignments.get(net)
        if cls is not None:
            return self.classes[cls]
        matched = [(c, pat) for (c, pat) in self.patterns
                   if fnmatch.fnmatchcase(net, pat)]
        if matched:
            # 列表序首匹配为解析结果；多模式命中且类不同 -> 显式登记歧义
            if len(matched) > 1 and len({c for c, _ in matched}) > 1 \
                    and net not in self._ambiguity_seen:
                self._ambiguity_seen.add(net)
                self.ambiguities.append({
                    "net": net,
                    "matched": [[c, p] for c, p in matched[:4]],
                    "resolved": matched[0][0],
                    "rule": "first_in_list",
                })
            return self.classes[matched[0][0]]
        return self.default

    def required_clearance(self, net_a, net_b):
        """两网间要求 clearance（KiCad 口径：取两侧较大）。"""
        return max(self.resolve(net_a).clearance_mm,
                   self.resolve(net_b).clearance_mm)

    def matrix(self, nets):
        """逐网矩阵 {net: {"class": name, "clearance_mm": c,
        "track_width_mm": w}}（G1 报告产物用）。"""
        out = {}
        for net in sorted(set(nets)):
            c = self.resolve(net)
            out[net] = {
                "class": c.name,
                "clearance_mm": round(c.clearance_mm, 6),
                "track_width_mm": None if c.track_width_mm is None
                else round(c.track_width_mm, 6),
            }
        return out

    def status_dict(self):
        return {
            "source": self.source,
            "status": "ok",
            "class_count": len(self.classes),
            "pattern_count": len(self.patterns),
            "assignment_count": len(self.assignments),
            "ambiguities": list(self.ambiguities),
            "classes": {n: c.as_dict()
                        for n, c in sorted(self.classes.items())},
        }


# ---------------------------------------------------------------- 载入器

def netclass_table_from_board_text(text):
    """路径：板内 net_class 节点（KiCad <= 8 板格式）。

    缺 net_class 节点 -> 返回 None（由 load_netclasses 统一 fail-closed）。
    """
    roots = [n for n in sexpr_min.parse(text)
             if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise NetClassError("expect exactly one kicad_pcb root")
    classes, assignments = {}, {}
    for node in roots[0][1:]:
        if not isinstance(node, list) or not node or node[0] != "net_class":
            continue
        if len(node) < 2 or not isinstance(node[1], str):
            raise NetClassError("net_class 缺类名（fail-closed）")
        name = node[1]
        clearance = None
        track = None
        via_dia = via_dri = None
        for sub in node[2:]:
            if not isinstance(sub, list) or len(sub) < 2:
                continue
            tag = sub[0]
            if tag == "clearance":
                clearance = _nonneg(float(sub[1]), "%s.clearance" % name)
            elif tag in ("track_width", "trace_width"):
                track = _nonneg(float(sub[1]), "%s.track_width" % name)
            elif tag == "via_dia":
                via_dia = _nonneg(float(sub[1]), "%s.via_dia" % name)
            elif tag == "via_dri":
                via_dri = _nonneg(float(sub[1]), "%s.via_drill" % name)
            elif tag == "net" and isinstance(sub[1], str):
                assignments[sub[1]] = name
        if clearance is None:
            raise NetClassError("net_class %s 缺 clearance（fail-closed）"
                                % name)
        classes[name] = NetClass(name, clearance, track, via_dia, via_dri)
    if not classes:
        return None
    return NetClassTable(classes, assignments, [],
                         "board_net_class_nodes")


def netclass_table_from_kicad_pro(pro_obj):
    """路径：.kicad_pro net_settings（KiCad >= 8 工程文件，已解析对象）。"""
    if not isinstance(pro_obj, dict):
        raise NetClassError("kicad_pro 须为 dict（fail-closed）")
    ns = pro_obj.get("net_settings")
    if not isinstance(ns, dict) or not ns.get("classes"):
        return None
    classes = {}
    for c in ns["classes"]:
        if not isinstance(c, dict) or not c.get("name"):
            raise NetClassError("net_settings.classes 项缺 name（fail-closed）")
        name = c["name"]
        if "clearance" not in c:
            raise NetClassError("类 %s 缺 clearance（fail-closed）" % name)
        classes[name] = NetClass(
            name, c["clearance"],
            c.get("track_width") if c.get("track_width") is not None
            else c.get("trace_width"),
            c.get("via_dia"), c.get("via_dri"))
    assignments = {}
    raw_assign = ns.get("netclass_assignments")
    if isinstance(raw_assign, dict):
        for net, cls in raw_assign.items():
            assignments[net] = cls
    patterns = []
    raw_pat = ns.get("netclass_patterns")
    if isinstance(raw_pat, list):
        for p in raw_pat:
            if not isinstance(p, dict) or "netclass" not in p \
                    or "pattern" not in p:
                raise NetClassError("netclass_patterns 项结构非法（fail-closed）")
            patterns.append((p["netclass"], p["pattern"]))
    return NetClassTable(classes, assignments, patterns,
                         "kicad_pro_net_settings")


def netclass_table_from_declared_defaults(clearance_mm, track_width_mm=None,
                                          source_note=""):
    """路径：显式声明缺省（仅 Default 类；advisory 用，须可追溯）。"""
    table = NetClassTable(
        {"Default": NetClass("Default", clearance_mm, track_width_mm)},
        {}, [], "declared_defaults")
    table.declared_source_note = str(source_note)
    return table


def load_netclasses(board_text=None, kicad_pro_obj=None,
                    declared_defaults=None):
    """统一 fail-closed 载入。

    - 多源并存 -> NetClassError(ambiguous_source)；
    - 全缺 -> NetClassNotAvailable（显式 not_available）。
    declared_defaults=(clearance, track_width) 元组。
    """
    got = []
    t_board = None
    if board_text is not None:
        t_board = netclass_table_from_board_text(board_text)
        if t_board is not None:
            got.append("board_net_class_nodes")
    t_pro = None
    if kicad_pro_obj is not None:
        t_pro = netclass_table_from_kicad_pro(kicad_pro_obj)
        if t_pro is not None:
            got.append("kicad_pro_net_settings")
    t_decl = None
    if declared_defaults is not None:
        try:
            clearance, track = declared_defaults
        except (TypeError, ValueError):
            raise NetClassError(
                "declared_defaults 须为 (clearance, track_width)（fail-closed）")
        t_decl = netclass_table_from_declared_defaults(
            clearance, track,
            source_note="declared by caller (advisory; traceable)")
        got.append("declared_defaults")
    if len(got) > 1:
        raise NetClassError("多源并存=ambiguous_source（fail-closed）: %r"
                            % (got,))
    if len(got) == 1:
        for t in (t_board, t_pro, t_decl):
            if t is not None:
                return t
    raise NetClassNotAvailable(
        "net class 不可用（fail-closed 显式登记 not_available：板内无 "
        "net_class 节点、未提供 kicad_pro、未声明缺省——消费方必须 blocked）")
