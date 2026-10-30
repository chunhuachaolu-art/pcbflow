"""PCBFlow 铜箔闭环 P1a —— 真实板铜箔事实模型（第三腿的板侧事实源）。

依据：铜箔闭环 P1a 任务书（接口契约由主审冻结，签名与字段名不可改）。
本模块只读、纯函数、零 IO 副作用：把 KiCad 板文本里**真实铜箔**
（顶层 `(segment` / `(via` / `(zone` / `(arc`）解析成带稳定身份的结构化
对象，供后续适配层 / 补丁引擎 / 回路驱动并行消费。

顶层节点扫描直接复用 `pcbflow.board_writer._top_level_nodes` 原语：
`top_level_copper_nodes()` 逐 tag 取 segment/via/zone/arc 的顶层跨度，
parse_copper 只认这一来源。另外 `_scan_all_top_level()` 是一次同规则、
单遍、给出**全部**顶层 tag 的普查，只用于发现"未识别的铜类顶层节点"
（原语需要给定 tag，先探 tag 再逐 tag 调原语会退化成多次全量扫描）；
两者在四个铜箔 tag 上的跨度一致性由测试钉死
（tests/test_copper_model.py::test_census_agrees_with_board_writer）。

R5（2026-09-11）单遍扫描与跨度复用 —— 入口形状见
tests/test_copper_model_spans_equivalence.py（**等价性是硬约束**）：
- `_scan_top_level_nodes()` 是一次遍历给出全部顶层节点跨度（文档序）的唯一
  扫描实现，`_scan_all_top_level()` / `top_level_copper_nodes()` /
  `scan_copper()` 都走它。逐 tag 调 `_top_level_nodes` 会退化成 4 次全量
  扫描 —— Rev-C（1.43 MB，2619 个铜箔顶层节点）实测 ≈0.67 s，是补丁单轮
  ≈4.4 s 的主要成本。
- 平衡判定**不融进**该循环，仍由未被改动的 `_balanced(text)` 独立完成：
  两者在 tag token 含 `"` 的病态输入上不等价（见 `_scan_top_level_nodes`
  docstring 里的反例，已由测试钉死）。
- `scan_copper(board_text) -> CopperScan`：**新入口**，把一次扫描的结果
  （`nodes` / `copper_spans` / `unknown_spans` / `balanced`）显式交给调用方。
- `parse_copper_scan(board_text, scan=None)` 与
  `iter_copper_nodes(board_text, scan=None)`：复用该结果的**新入口**，
  复用路径零额外扫描。
- 等价性契约：`parse_copper(text)` 与 `parse_copper_scan(text,
  scan_copper(text))` 产出**整份 json 逐字节相同**（含 identity_map 键序、
  span 字节偏移、identity_disambiguated 与 unrepresentable 的顺序与文案）；
  `scan.copper_spans` == `top_level_copper_nodes(text)`（任意输入），
  后者在快路径上与逐 tag 调 `board_writer._top_level_nodes(text, tag)` 相同。
  跨文本复用 scan 一律 fail-closed（ValueError），绝不静默错位。
- **既有入口签名与语义冻结**：`parse_copper(board_text)` /
  `parse_copper_file(path)` / `top_level_copper_nodes(board_text)` 仍是单参数、
  单参数默认值不变（`top_level_copper_nodes` 内部改走单遍快路径，产出逐字节
  不变，由 golden 摘要 + 差分模糊钉死）；新能力只走新入口。
- 单遍普查与逐 tag 原语在两类输入上走法不同（普查对深度 2 节点"整段跳过"、
  逐 tag 原语对未匹配节点"继续下潜"）：(a) 文本不平衡；(b) 深度 2 节点的
  tag token 内含 `"`。故 `_copper_spans_for` 在这两类输入上退回历史逐 tag
  走法，保证 `top_level_copper_nodes` 与 `CopperScan.copper_spans` 对
  **任意**输入都等于历史实现（差分模糊钉死）。真实板恒走快路径。

身份规则（冻结，v2 修正 —— `key` 是补丁引擎的对象寻址键，必须全局唯一）：
- 节点的 `(uuid "...")` 在**全板所有铜箔节点**（segment + via + zone 一起
  统计）中唯一 → `key` = 该 uuid 原样（identity_basis = `kicad_uuid`；
  形状与此前一致，向后兼容）；
- 该 uuid 被 ≥2 个铜箔节点共享 → `key` = `"<uuid>@<digest>"`，`digest` =
  该节点**自身几何**的 canonical 短摘要（sha256 前 12 位 hex，见下）。
  真实 Rev-C 板的 uuid 即此情形：它是**路由级**内容派生值
  （`board_writer.route_uuid` 口径：同一条 route 的所有 segment/via 写同一
  uuid），故共享是正常走线而非"不可表示"；此类节点逐条登记到
  `identity_disambiguated`（信息性统计），**不再**进 `unrepresentable`。
- 无 uuid → 回退 `"G:" + sha256(canonical(几何))[:16]`（`geometric_fallback`）；
  两类混用时 `mixed`；无任何铜箔对象时按 `kicad_uuid` 记（"没有任何对象
  发生回退"）。
- segment 的回退几何严格取契约口径 net|layer|width|起终点坐标；via/zone
  无 width/起终点，按同类口径泛化（via：net|layers|size|at；zone：
  net|layers|outline 全轮廓），保证不同几何 → 不同身份。
- KiCad5 语料的 `(tstamp ...)` **不作为** 身份（文件局部标记，跨版本/
  跨工具不可靠），故 KiCad5 铜箔按几何回退取身份。

digest 输入（写死，确定性；见 `_DIGEST_FIELDS`）：
`payload = [kind, <按下列固定顺序逐字段取值>]`，取值全部来自**该节点
解析后的量化字段**（坐标 6 位、宽度/尺寸/钻孔 3 位）——
- segment: net, layer, width, start, end
- via:     net, layers, size, drill, at, via_kind
- zone:    net, layers, outline_mm, params
`digest = sha256(canonical_json(payload))[:12]`（canonical = sort_keys +
紧凑分隔符，与模块其它 hash 同口径）。payload **只含该节点自身事实**
（无序号/索引/文档位置/同键其它节点信息），故同 uuid 的其它节点增删或
改几何时本节点 digest 不变（**不漂移**）；同 uuid 而几何不同的节点 →
digest 不同 → key 不同。

量化与 canonical（与 svg_route_package 同口径）：坐标 6 位小数，
宽度/尺寸/钻孔 3 位小数；列表按 `key` 稳定排序；`copper_sha256` =
sha256(canonical json of {segments, vias, zones} 的身份+几何字段)，
**排除** `identity_map`/`span`、zone 的 `fill_points` 与填充几何
（填充是 KiCad 派生数据，`fill_sha256` 不进事实哈希）；被消歧的对象同样
计入哈希（key 已含 digest）。`identity_map` 对**每个**铜箔节点各留一条，
value 的 `span` 就是该节点自身的 `[start, end]` 字节跨度。

fail-closed 铁律：任何无法表达的铜箔节点（顶层 `(arc ...)` 走线、无轮廓
的 zone、结构非法、未识别的铜类顶层节点、消歧后仍撞键
（`identity_key_collision`：同 uuid 且几何全同 / 几何全同的无 uuid 对象，
摘要必然相同）、板文本括号/字符串不平衡）一律进 `unrepresentable`
（带 kind/where/reason），**绝不静默丢弃**；顶层 `(segment`/`(via`/`(zone`/`(arc` 之外的内容一律不解析、不
改动（`footprint`/`module` 内的 pad 铜属板快照的 pad 对象类，不在 P1a
铜箔合同内，故不列为"未识别铜类节点"）。板文本不平衡时拒绝部分解析
（返回空列表 + 显式 `board_parse_error`），因为此时字节跨度不可信、
补丁引擎不得据此定位。

生成器模式：本模块不落盘、零子进程、零 wall-clock、零随机。
"""

from __future__ import annotations

import json
import re

from . import hashing
from . import sexpr_min
from .board_writer import _top_level_nodes  # noqa: F401  （扫描规则的参照实现：
#                                             _scan_top_level_full 与它逐 tag
#                                             等价，由测试直接比对钉死）

__all__ = [
    "SCHEMA", "parse_copper", "parse_copper_file",
    "top_level_copper_nodes",
    # R5 新入口：单遍扫描 / 跨度复用（既有入口签名与语义不变）
    "CopperScan", "scan_copper", "parse_copper_scan", "iter_copper_nodes",
    "KIND_SEGMENT", "KIND_VIA", "KIND_ZONE",
    "IDENTITY_KICAD_UUID", "IDENTITY_GEOMETRIC_FALLBACK", "IDENTITY_MIXED",
    "IDENTITY_DISAMBIGUATED_REASON", "COPPER_TOP_TAGS",
]

SCHEMA = "pcbflow.copper-model/1"

KIND_SEGMENT = "segment"
KIND_VIA = "via"
KIND_ZONE = "zone"

IDENTITY_KICAD_UUID = "kicad_uuid"
IDENTITY_GEOMETRIC_FALLBACK = "geometric_fallback"
IDENTITY_MIXED = "mixed"

#: `identity_disambiguated[*].reason` 的唯一取值：uuid 是路由级内容派生值，
#: 被同一条 route 的多个铜箔节点共享（消歧前的根因，见模块 docstring）
IDENTITY_DISAMBIGUATED_REASON = "route_level_uuid_shared"

#: 消歧 key 的分隔符：`"<uuid>@<digest>"`（uuid 不含 "@"，故可无损切分）
_DISAMBIGUATOR = "@"

#: 本阶段能被表达为铜箔对象的顶层 tag（其余顶层 tag 一律不解析为对象）
COPPER_TOP_TAGS = ("segment", "via", "zone", "arc")

#: KiCad 外层铜名（用于 via_kind 推断）
_OUTER_LAYERS = ("F.Cu", "B.Cu")

#: 豁免"未识别铜类节点"检查的顶层 tag（见模块 docstring）
_PAD_HOLDER_TAGS = ("footprint", "module")

_GEO_Q = 6   # 坐标量化位数（与 svg_route_package 同口径）
_DIM_Q = 3   # 宽度/尺寸/钻孔量化位数

# (layer "F.Cu") / (layer F.Cu) / (layers "F.Cu" "In2.Cu") 声明扫描
_LAYER_DECL_RE = re.compile(
    r"\(\s*layers?\s+((?:\"(?:[^\"\\]|\\.)*\"|[^\s()]+)"
    r"(?:\s+(?:\"(?:[^\"\\]|\\.)*\"|[^\s()]+))*)\s*\)")
_LAYER_TOK_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"|[^\s()]+")

# zone 参数里按数值量化的键（其余按原样字符串）
_ZONE_NUM_KEYS = ("min_thickness", "clearance", "thermal_gap",
                  "thermal_bridge_width", "arc_segments",
                  "island_removal_mode", "priority", "smoothing_max_error")

# copper_sha256 参与字段（身份 + 几何；uuid 由 key 覆盖，派生填充不进哈希）
_HASH_FIELDS = {
    KIND_SEGMENT: ("key", "net", "layer", "width", "start", "end"),
    KIND_VIA: ("key", "net", "at", "size", "drill", "layers", "via_kind"),
    KIND_ZONE: ("key", "net", "layers", "outline_mm", "params"),
}

# 消歧 digest 的输入字段（固定顺序；只含节点自身事实，见模块 docstring）
_DIGEST_FIELDS = {
    KIND_SEGMENT: ("net", "layer", "width", "start", "end"),
    KIND_VIA: ("net", "layers", "size", "drill", "at", "via_kind"),
    KIND_ZONE: ("net", "layers", "outline_mm", "params"),
}


# --------------------------------------------------------------- 基础工具

def _q(v, nd: int) -> float:
    return round(float(v), nd)


def _fnum(v):
    """token → float（非数值返回 None，绝不抛）。"""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _canonical(obj) -> str:
    """canonical json（sort_keys + 紧凑分隔符；与 svg_route_package 同口径）。

    形态登记=exec/CANONICAL-JSON-FORM-MAP-2026-09-25.md「铜族（紧凑）」：
    ensure_ascii=False+紧凑+sort_keys、无尾换行；跨族复用前必查该地图。
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _sha(obj) -> str:
    return hashing.sha256_text(_canonical(obj))


def _child(node, name: str):
    if not isinstance(node, list):
        return None
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def _leaf(node, tag=None, index: int = 1):
    """取节点第 index 个叶子；tag 给定则先定位同名字节点。"""
    if node is None:
        return None
    if tag is not None:
        node = _child(node, tag)
    if not isinstance(node, list) or len(node) <= index:
        return None
    v = node[index]
    return v if isinstance(v, str) else None


def _xy(node):
    """(start/end/at/xy x y) → [x, y]；非法返回 None。"""
    if not isinstance(node, list) or len(node) < 3:
        return None
    x, y = _fnum(node[1]), _fnum(node[2])
    if x is None or y is None:
        return None
    return [x, y]


def _num_leaf(node, tag: str):
    return _fnum(_leaf(node, tag, 1))


def _layers_of(node) -> list:
    """节点直接子层声明的层名列表（layer / layers，保序）。"""
    out = []
    if not isinstance(node, list):
        return out
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] in ("layer", "layers"):
            for v in c[1:]:
                if isinstance(v, str) and v:
                    out.append(v)
    return out


def _declared_layers_text(node_text: str) -> list:
    """文本级层声明扫描（未识别节点普查用；含嵌套 pad 层声明）。"""
    out = []
    for m in _LAYER_DECL_RE.finditer(node_text):
        for tok in _LAYER_TOK_RE.findall(m.group(1)):
            out.append(tok[1:-1] if tok.startswith('"') else tok)
    return out


def _is_copper_layer(name) -> bool:
    return isinstance(name, str) and name.endswith(".Cu")


def _balanced(text: str) -> bool:
    """括号/双引号平衡检查（与顶层扫描同口径的字符串转义语义）。"""
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
            else:
                return False  # 未闭合字符串
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _scan_top_level_nodes(text: str) -> list:
    """单遍顶层节点普查 → [(tag, start, end)]（文档序）。

    深度 1（板根）的**全部**顶层节点；命中即整段跳过（不进入嵌套子树）；
    tag 截止于空白/括号；双引号内转义（`\\` 跳两字节）不参与括号计数。
    与改动前的 `_scan_all_top_level` **逐字相同**（新增的平衡判定已拆走，
    见下），且与 `board_writer._top_level_nodes` 逐 tag 调用等价（测试钉死）。

    注意：本函数**不做**全文本平衡判定。曾尝试把 `_balanced` 的线性自动机
    融进本循环以省一趟扫描，但两者在病态输入上不等价：本循环对深度 2 节点
    "整段跳过"、跳过区由节点自身的迷你扫描处理（`instr` 从 False 起），
    而 `_balanced` 是**线性**引号自动机。反例（已在测试中钉死，见
    test_balanced_check_is_not_fused_into_the_scan 的 `evil` 常量：tag token
    内含双引号、正文内含连续三个双引号，迷你扫描吞掉后半段文本而线性自动机
    按引号开合继续计数）。
    故平衡判定仍由**未被改动的** `_balanced(text)` 独立完成（口径逐字节相同，
    Rev-C 1.43 MB 实测 ≈0.16 s/次，占单次解析 <12%）。
    """
    out = []
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif c == "(":
            depth += 1
            if depth == 2:
                j = i + 1
                while j < n and text[j] not in " \t\r\n()":
                    j += 1
                tag = text[i + 1:j]
                k, d, instr = j, 1, False
                while k < n and d > 0:
                    ch = text[k]
                    if instr:
                        if ch == "\\":
                            k += 2
                            continue
                        if ch == '"':
                            instr = False
                    elif ch == '"':
                        instr = True
                    elif ch == "(":
                        d += 1
                    elif ch == ")":
                        d -= 1
                    k += 1
                out.append((tag, i, k))
                depth -= 1
                i = k
                continue
        elif c == ")":
            depth -= 1
        i += 1
    return out


def _scan_all_top_level(text: str) -> list:
    """单遍全量顶层节点普查 → [(tag, start, end)]（文档序）。

    保留为独立函数（既有测试以它作普查基准），实现委托
    `_scan_top_level_nodes`，不再单独维护一份扫描逻辑。
    """
    return _scan_top_level_nodes(text)


class CopperScan:
    """一次扫描的结果（R5 跨度复用入口的载体，**只读视图**）。

    由 `scan_copper()` 构造，绑定到扫描时的 `board_text`：跨度只对该文本的
    字节坐标成立。`parse_copper_scan` / `iter_copper_nodes` 复用它之前会校验
    文本一致（同一对象或值相等），不一致即 `ValueError`（fail-closed，
    绝不静默错位）。对象本身不写盘、无子进程、无 wall-clock。

    - `nodes`：全部顶层节点 [(tag, start, end)]（文档序，防御性拷贝）；
    - `copper_spans`：铜箔顶层节点（文档序）。**保证** ==
      `top_level_copper_nodes(text)`（构造时按需退回逐 tag 原语，见
      `_copper_spans_for`），故复用它与直接调用冻结入口等价；
    - `unknown_spans`：其余 tag == `_unknown_top_nodes(text)`（未识别铜类普查用）；
    - `balanced`：括号/字符串平衡，取自**未被改动的** `_balanced(text)`
      （同一函数、同一口径，非重新实现）。
    """

    __slots__ = ("_text", "_nodes", "_copper", "balanced")

    def __init__(self, text: str, nodes: list, balanced: bool):
        self._text = text
        self._nodes = nodes
        self._copper = _copper_spans_for(text, nodes, balanced)
        self.balanced = balanced

    @property
    def text(self) -> str:
        """被扫描的板文本（只读引用；不拷贝）。"""
        return self._text

    @property
    def nodes(self) -> list:
        """全部顶层节点 [(tag, start, end)]（文档序）。"""
        return list(self._nodes)

    @property
    def copper_spans(self) -> list:
        """铜箔顶层节点 [(tag, start, end)]（文档序）== top_level_copper_nodes。"""
        return [tuple(n) for n in self._copper]

    @property
    def unknown_spans(self) -> list:
        """非铜箔 tag 的顶层节点（未识别铜类普查的输入）。"""
        return [n for n in self._nodes if n[0] not in COPPER_TOP_TAGS]

    def _bind(self, board_text) -> None:
        """校验 span 归属：跨文本复用一律 fail-closed。"""
        if board_text is self._text or board_text == self._text:
            return
        raise ValueError(
            "scan 与 board_text 不匹配：字节跨度只对扫描时的文本成立，"
            "跨文本复用会静默错位（拒绝）")

    def __repr__(self) -> str:
        return ("CopperScan(nodes=%d, copper=%d, unknown=%d, balanced=%s)"
                % (len(self._nodes), len(self._copper),
                   len(self.unknown_spans), self.balanced))


def _copper_spans_for(board_text: str, nodes: list, balanced: bool) -> list:
    """铜箔跨度：单遍普查过滤，或（不保证等价时）退回逐 tag 原语。

    单遍普查（`_scan_top_level_nodes`）与逐 tag 原语（`_top_level_nodes`）
    在两种输入上走法不同，**必须**退回逐 tag 路径以保持历史语义：
    1. 文本不平衡（括号/引号不配对）—— 深度记账不可靠；
    2. 任何深度 2 节点的 **tag token 内含 `"`** —— 普查的迷你扫描从 tag 之后
       起算（`instr` 初值 False），逐 tag 走法却会先走 tag 字节并在此处进入
       字符串态，两者对节点边界的判断随之不同（例：tag = `gr_te"paren`
       时普查把一个节点吞到文末，逐 tag 走法仍能发现其后的 arc/segment）。
       该窗口在真实板上恒不触发（全为标识符 tag），故快路径覆盖实际输入。

    两类情形都在测试里用差分模糊（对照 `_top_level_nodes`）钉死。
    """
    if balanced and not any('"' in t[0] for t in nodes):
        return [n for n in nodes if n[0] in COPPER_TOP_TAGS]
    return _top_level_copper_nodes_per_tag(board_text)


def scan_copper(board_text: str) -> CopperScan:
    """板文本 → `CopperScan`（R5 新入口：一次节点普查 + 一次平衡检查）。

    平衡判定直接调**未被改动的** `_balanced(text)`（口径逐字节相同）；
    节点普查由 `_scan_top_level_nodes` 一次完成（改动前是 4 次逐 tag 全量
    扫描 + 1 次普查）。`copper_spans` 保证等于 `top_level_copper_nodes(text)`
    （必要时构造期退回逐 tag 路径，见 `_copper_spans_for`）。
    纯函数：不改动输入、不落盘、无 wall-clock、无随机。
    """
    if not isinstance(board_text, str):
        raise ValueError("board_text: 不是字符串")
    return CopperScan(board_text, _scan_top_level_nodes(board_text),
                      _balanced(board_text))




# ----------------------------------------------------------------- 身份

def _geo_sha(payload) -> str:
    return hashing.sha256_text(_canonical(payload))


def _geo_key_segment(net, layer, width, start, end) -> str:
    """segment 几何回退（契约口径）：net|layer|width|起终点坐标。"""
    return "G:" + _geo_sha([net, layer, _q(width, _DIM_Q),
                            [_q(start[0], _GEO_Q), _q(start[1], _GEO_Q)],
                            [_q(end[0], _GEO_Q), _q(end[1], _GEO_Q)]])[:16]


def _geo_key_via(net, layers, size, at) -> str:
    """via 几何回退（同类泛化）：net|layers|size|at。"""
    return "G:" + _geo_sha([net, list(layers), _q(size, _DIM_Q),
                            [_q(at[0], _GEO_Q), _q(at[1], _GEO_Q)]])[:16]


def _geo_key_zone(net, layers, outline) -> str:
    """zone 几何回退（同类泛化）：net|layers|全轮廓。"""
    return "G:" + _geo_sha([net, list(layers),
                            [[_q(p[0], _GEO_Q), _q(p[1], _GEO_Q)]
                             for p in outline]])[:16]


def _identity_digest(kind: str, entry: dict) -> str:
    """消歧短摘要：sha256(canonical([kind, <_DIGEST_FIELDS 逐字段>]))[:12]。

    输入全部取自 entry 已量化的**自身**字段（无序号/索引/文档位置），故
    同 uuid 的其它节点增删或改几何时本摘要不变（不漂移）；几何不同的同
    uuid 节点（含跨 segment/via 复用，kind 前缀保证不同）摘要必然不同。
    字段顺序由 `_DIGEST_FIELDS[kind]` 写死，见模块 docstring。
    """
    payload = [kind]
    for field in _DIGEST_FIELDS[kind]:
        payload.append(entry[field])
    return _sha(payload)[:12]


def _fallback_key(kind: str, entry: dict) -> str:
    """无 uuid 节点的几何回退 key（口径与此前一致，逐字段取自 entry）。"""
    if kind == KIND_SEGMENT:
        return _geo_key_segment(entry["net"], entry["layer"], entry["width"],
                                entry["start"], entry["end"])
    if kind == KIND_VIA:
        return _geo_key_via(entry["net"], entry["layers"], entry["size"],
                            entry["at"])
    return _geo_key_zone(entry["net"], entry["layers"], entry["outline_mm"])


def _disambiguated_key(kind: str, entry: dict) -> str:
    """uuid 被共享的节点 → `"<uuid>@<digest>"`（全局唯一寻址键）。"""
    return "%s%s%s" % (entry["uuid"], _DISAMBIGUATOR,
                       _identity_digest(kind, entry))


def _uuid_of(node):
    u = _leaf(node, "uuid", 1)
    return u if isinstance(u, str) and u != "" else None


# ------------------------------------------------------------ 节点解析

def _parse_segment(node):
    """(segment ...) → (entry, None) 或 (None, reason)。"""
    start = _xy(_child(node, "start"))
    end = _xy(_child(node, "end"))
    width = _num_leaf(node, "width")
    layer = _leaf(node, "layer", 1)
    net = _leaf(node, "net", 1)
    bad = []
    if start is None:
        bad.append("start")
    if end is None:
        bad.append("end")
    if width is None or width <= 0:
        bad.append("width")
    if not isinstance(layer, str) or layer == "":
        bad.append("layer")
    if not isinstance(net, str) or net == "":
        bad.append("net")
    if bad:
        return None, "缺/非法字段: " + ",".join(bad)
    uuid = _uuid_of(node)
    entry = {
        "uuid": uuid,
        "key": None,   # 由 _assemble 统一赋（需先知道 uuid 的全板唯一性）
        "net": net,
        "layer": layer,
        "width": _q(width, _DIM_Q),
        "start": [_q(start[0], _GEO_Q), _q(start[1], _GEO_Q)],
        "end": [_q(end[0], _GEO_Q), _q(end[1], _GEO_Q)],
    }
    return entry, None


def _via_kind(token, layers):
    """via 类型：显式 token 优先；否则按层位置推断（外层 = F.Cu/B.Cu）。

    微孔 `micro` 不在冻结取值 {through, blind, buried} 内：按其涉及的外层
    数量归入 blind/buried（KiCad 微孔只连接相邻层，本质是盲/埋孔），
    该归约在 docstring 声明，属 P1a 已知表达损失。
    """
    if token in ("blind", "buried", "through"):
        return token
    if not layers:
        return None
    outer = [l for l in layers if l in _OUTER_LAYERS]
    if len(layers) >= 2 and len(outer) == len(layers):
        return "through"
    if len(outer) == 1:
        return "blind"
    return "buried"


def _parse_via(node):
    """(via [kind] ...) → (entry, None) 或 (None, reason)。"""
    at = _xy(_child(node, "at"))
    size = _num_leaf(node, "size")
    drill = _num_leaf(node, "drill")
    net = _leaf(node, "net", 1)
    layers = _layers_of(node)
    bad = []
    if at is None:
        bad.append("at")
    if size is None or size <= 0:
        bad.append("size")
    if drill is None or drill <= 0:
        bad.append("drill")
    if len(layers) < 2:
        bad.append("layers")
    if not isinstance(net, str) or net == "":
        bad.append("net")
    if bad:
        return None, "缺/非法字段: " + ",".join(bad)
    layers = layers[:2]
    token = node[1] if len(node) > 1 and isinstance(node[1], str) else None
    kind = _via_kind(token, layers)
    if kind is None:
        return None, "via_kind 无法判定: layers=%s" % (layers,)
    uuid = _uuid_of(node)
    entry = {
        "uuid": uuid,
        "key": None,   # 由 _assemble 统一赋（见 _parse_segment）
        "net": net,
        "at": [_q(at[0], _GEO_Q), _q(at[1], _GEO_Q)],
        "size": _q(size, _DIM_Q),
        "drill": _q(drill, _DIM_Q),
        "layers": list(layers),
        "via_kind": kind,
    }
    return entry, None


def _zone_params(node) -> dict:
    """zone 参数（确定性：只收已知标量键；数值按 3 位量化、整数保持整数）。"""
    def _put(params, name, node_):
        v = _fnum(_leaf(node_, None, 1))
        if v is not None:
            params[name] = int(v) if float(v).is_integer() else _q(v, _DIM_Q)

    params = {}
    hatch = _child(node, "hatch")
    if hatch is not None:
        toks = [v for v in hatch[1:] if isinstance(v, str)]
        if toks:
            params["hatch"] = " ".join(toks)
    cp = _child(node, "connect_pads")
    if cp is not None:
        mode = _leaf(cp, None, 1)
        if isinstance(mode, str) and mode:
            params["connect_pads_mode"] = mode
        _put(params, "clearance", _child(cp, "clearance"))
    fill = _child(node, "fill")
    if fill is not None:
        mode = _leaf(fill, None, 1)
        if isinstance(mode, str) and mode:
            params["fill"] = mode
        for name in _ZONE_NUM_KEYS:
            _put(params, "fill_" + name, _child(fill, name))
    for name in ("min_thickness", "priority", "smoothing_max_error"):
        _put(params, name, _child(node, name))
    return params


def _parse_zone(node):
    """(zone ...) → (entry, extra, None) 或 (None, None, reason)。

    extra = 轮廓点列表（供填充几何统计；填充不进事实哈希）。
    """
    net = _leaf(node, "net", 1)
    name = _leaf(node, "net_name", 1)
    layers = _layers_of(node)
    bad = []
    if not isinstance(net, str) or net == "":
        bad.append("net")
    if not layers:
        bad.append("layer")
    if bad:
        return None, None, "缺/非法字段: " + ",".join(bad)
    # KiCad5（(net 1) + (net_name GND)）：板侧 net 名取 net_name
    net_name = name if isinstance(name, str) and name else net
    polygon = _child(node, "polygon")
    pts = _child(polygon, "pts") if polygon is not None else None
    outline = []
    if pts is not None:
        for c in pts[1:]:
            if isinstance(c, list) and c and c[0] == "xy":
                p = _xy(c)
                if p is None:
                    return None, None, "polygon 顶点非法（xy 非数值对）"
                outline.append([_q(p[0], _GEO_Q), _q(p[1], _GEO_Q)])
    if len(outline) < 3:
        return None, None, ("zone 无有效轮廓：polygon/pts/xy 缺失或 <3 点"
                            "（实得 %d 点）" % len(outline))
    uuid = _uuid_of(node)
    entry = {
        "uuid": uuid,
        "key": None,   # 由 _assemble 统一赋（见 _parse_segment）
        "net": net_name,
        "layers": list(layers),
    }
    return entry, outline, None


def _zone_fill(node) -> "tuple[int, str]":
    """zone 填充几何（KiCad 派生）：点数 + canonical sha256。"""
    fills = []
    points = 0
    for c in node[1:]:
        if not (isinstance(c, list) and c and c[0] == "filled_polygon"):
            continue
        pts = _child(c, "pts")
        poly = []
        if pts is not None:
            for xy in pts[1:]:
                if isinstance(xy, list) and xy and xy[0] == "xy":
                    p = _xy(xy)
                    if p is not None:
                        poly.append([_q(p[0], _GEO_Q), _q(p[1], _GEO_Q)])
        points += len(poly)
        fills.append({"layer": _leaf(c, "layer", 1), "pts": poly})
    return points, _sha(fills)


# ------------------------------------------------------------ 组装与哈希

def _bind_identity(segments, vias, zones):
    """赋 key（全局唯一）→ identity_map / identity_disambiguated / 残留撞键。

    步骤（顺序即口径，见模块 docstring）：
    1. 统计每个 uuid 在**全板所有铜箔节点**（segment+via+zone）中的出现数；
    2. key：uuid 唯一 → 原样；uuid 被共享 → `"<uuid>@<digest>"`；无 uuid →
       几何回退 `"G:" + sha256(几何)[:16]`；随后按 key 稳定排序（同 key 保
       文档序）；
    3. `identity_map` 对每个对象各留一条，`span` = 该对象自身字节跨度；
       `identity_disambiguated` 逐条登记被消歧对象（按 kind 分组、组内按
       key 排序，确定性）；
    4. 消歧后仍撞键（同 uuid 且几何全同 / 几何全同的无 uuid 对象）→ 返回
       `collisions` 供 `unrepresentable` 逐条上报（首个保留在 identity_map，
       对象本身仍留在列表中，绝不静默并合）。

    返回 (identity_map, identity_disambiguated, collisions)。
    """
    groups = ((KIND_SEGMENT, segments), (KIND_VIA, vias), (KIND_ZONE, zones))
    mult = {}
    for _kind, items in groups:
        for it in items:
            u = it["uuid"]
            if u:
                mult[u] = mult.get(u, 0) + 1

    for kind, items in groups:
        for it in items:
            u = it["uuid"]
            if not u:
                it["key"] = _fallback_key(kind, it)
            elif mult[u] == 1:
                it["key"] = u
            else:
                it["key"] = _disambiguated_key(kind, it)
        items.sort(key=lambda e: e["key"])

    identity_map = {}
    disambiguated = []
    collisions = []
    for kind, items in groups:
        for i, it in enumerate(items):
            key = it["key"]
            span = [it["_span"][0], it["_span"][1]]
            if it["uuid"] and mult[it["uuid"]] > 1:
                disambiguated.append({
                    "key": key, "uuid": it["uuid"], "kind": kind,
                    "reason": IDENTITY_DISAMBIGUATED_REASON,
                })
            if key in identity_map:
                prev = identity_map[key]
                collisions.append({
                    "kind": "identity_key_collision",
                    "where": "%s#%d@%d" % (kind, i, span[0]),
                    "reason": "身份键 %r 消歧后仍不唯一（与 %s#%d span=[%d,%d]"
                              " 的自身几何摘要相同）：本 %s 对象保留在列表中"
                              "（不丢弃），但 identity_map 只能表达首个 span，"
                              "补丁引擎不得据此定位该对象"
                              % (key, prev["kind"], prev["index"],
                                 prev["span"][0], prev["span"][1], kind),
                })
                continue
            identity_map[key] = {"kind": kind, "index": i, "span": span}
    return identity_map, disambiguated, collisions


def _assemble(segments, vias, zones, unrep):
    """赋身份 → counts/basis → identity_map/disambiguated → copper_sha256。

    身份键全局唯一（见模块 docstring）：uuid 全板唯一 → 原样；被同一条
    route 的多个对象共享（Rev-C 的路由级 uuid）→ `"<uuid>@<digest>"`。
    这类共享**不是**"不可表示"，故只登记到 `identity_disambiguated`
    （信息性统计，不计入 counts）；真正消歧不掉的情形（摘要亦相同的几何
    全同对象）才进 unrepresentable（kind=identity_key_collision）。
    对象一个都不丢：所有对象（含被消歧者）都在 segments/vias/zones 列表
    与 copper_sha256 内。
    """
    groups = ((KIND_SEGMENT, segments), (KIND_VIA, vias), (KIND_ZONE, zones))
    identity_map, disambiguated, collisions = _bind_identity(
        segments, vias, zones)
    unrep.extend(collisions)

    uuid_n = sum(1 for _k, items in groups for it in items if it["uuid"])
    total = sum(len(items) for _k, items in groups)
    if uuid_n and uuid_n < total:
        basis = IDENTITY_MIXED
    elif uuid_n == 0 and total > 0:
        basis = IDENTITY_GEOMETRIC_FALLBACK
    else:
        basis = IDENTITY_KICAD_UUID

    payload = {}
    for name, kind, items in (("segments", KIND_SEGMENT, segments),
                              ("vias", KIND_VIA, vias),
                              ("zones", KIND_ZONE, zones)):
        fields = _HASH_FIELDS[kind]
        payload[name] = [{f: it[f] for f in fields} for it in items]
    for _kind, items in groups:
        for it in items:
            it.pop("_span", None)
    return {
        "schema": SCHEMA,
        "identity_basis": basis,
        "segments": segments,
        "vias": vias,
        "zones": zones,
        "unrepresentable": unrep,
        "identity_disambiguated": disambiguated,
        "counts": {"segments": len(segments), "vias": len(vias),
                   "zones": len(zones)},
        "identity_map": identity_map,
        "copper_sha256": _sha(payload),
    }


# ------------------------------------------------------------------ 入口

def _top_level_copper_nodes_per_tag(board_text: str) -> list:
    """历史实现（逐 tag 调 `board_writer._top_level_nodes` 后按 start 归并）。

    保留为**不平衡文本的兜底路径**：单遍普查（`_scan_top_level_nodes`）对
    深度 2 节点"命中即整段跳过"，而 `_top_level_nodes` 对**未匹配 tag** 的
    节点是"继续下潜"；文本不平衡（含未闭合字符串）时两者对未匹配节点的
    走法不同，跨度可能不同（例：`(kicad_pcb ("\\<换行>)(via)`）。平衡文本上
    两者逐 tag 相同（测试钉死）。`top_level_copper_nodes` 因此只在
    `balanced` 为真时走单遍快路径，否则退回本函数 —— 保证与历史实现
    对**任意**输入逐字节一致。
    """
    out = []
    for tag in COPPER_TOP_TAGS:
        for (s, e) in _top_level_nodes(board_text, tag):
            out.append((tag, s, e))
    out.sort(key=lambda t: t[1])
    return out


def top_level_copper_nodes(board_text: str) -> list:
    """四个铜箔 tag 的顶层节点跨度 [(tag, start, end)]（文档序）。

    **签名与语义冻结**：对任意输入与历史实现（逐 tag 调
    `board_writer._top_level_nodes` 后按 start 归并）逐字节等价 —— 平衡且
    tag token 不含 `"` 时走单遍普查（一次扫描；历史实现是 4 次全量扫描），
    否则退回 `_top_level_copper_nodes_per_tag`。退回条件与理由见
    `_copper_spans_for`。等价性由 tests/test_copper_model_spans_equivalence.py
    的差分模糊（对照 `_top_level_nodes`）与 golden 摘要钉死。
    需要跨调用复用时用 `scan_copper(...).copper_spans`（零额外扫描，且保证
    与本函数结果相同）。
    """
    nodes = _scan_top_level_nodes(board_text)
    return _copper_spans_for(board_text, nodes, _balanced(board_text))


def iter_copper_nodes(board_text: str, scan=None):
    """逐个产出铜箔顶层节点跨度 (tag, start, end)（文档序）。

    R5 新入口：`scan` 给定时**不再扫描**（复用 `scan.copper_spans`，其值保证
    等于 `top_level_copper_nodes(board_text)`），供补丁引擎式调用方
    （一次扫描 → 同时喂 `parse_copper_scan` 与节点遍历）使用；不给则等价于
    遍历 `top_level_copper_nodes(board_text)`。
    `scan` 与 `board_text` 不匹配时 fail-closed（ValueError，跨文本复用会
    静默错位）。
    """
    if scan is None:
        for node in top_level_copper_nodes(board_text):
            yield node
        return
    if not isinstance(scan, CopperScan):
        raise ValueError("scan: 不是 CopperScan（用 scan_copper 生成）")
    scan._bind(board_text)
    for node in scan._copper:
        yield tuple(node)


def _unknown_top_nodes(board_text: str) -> list:
    """非铜箔 tag 的顶层节点 [(tag, start, end)]（fail-closed 普查用）。

    扫描规则与 `_top_level_nodes` 一致（单遍，命中即跳过嵌套子树）；
    等价性由测试钉死。存在的理由：原语需要给定 tag，而"未识别的铜类
    顶层节点"必须先发现 tag —— 先探 tag 再逐 tag 调原语会退化为多次
    全量扫描，故此处保留一次同规则普查，只用于发现/过滤未知 tag。
    实现委托 `_scan_top_level_nodes`（同一单遍普查，与
    `CopperScan.unknown_spans` 等价；普查口径与文本平衡/tag 形态无关）。
    """
    return [n for n in _scan_top_level_nodes(board_text)
            if n[0] not in COPPER_TOP_TAGS]


def _parse_copper_with_scan(board_text: str, scan: CopperScan) -> dict:
    """`parse_copper` 的实现体：只消费 `scan`，不再自行扫描。"""
    unrep = []
    if not scan.balanced:
        unrep.append({
            "kind": "board_parse_error",
            "where": "board",
            "reason": "括号/双引号不平衡：拒绝部分解析（字节跨度不可信，"
                      "补丁引擎不得据此定位）",
        })
        return _assemble([], [], [], unrep)

    # 未识别的铜类顶层节点（fail-closed：显式记录，绝不静默跳过）
    for ordinal, (tag, s, e) in enumerate(scan.unknown_spans):
        if tag in _PAD_HOLDER_TAGS:
            continue
        layers = _declared_layers_text(board_text[s:e])
        if any(_is_copper_layer(l) for l in layers):
            unrep.append({
                "kind": "unrecognized_copper_node",
                "where": "%s#%d@%d" % (tag, ordinal, s),
                "reason": "顶层 %r 节点声明铜层 %s，但 P1a 合同只表达 "
                          "segment/via/zone/arc" % (tag, layers),
            })

    segments, vias, zones = [], [], []
    for ordinal, (tag, s, e) in enumerate(scan.copper_spans):
        where = "%s#%d@%d" % (tag, ordinal, s)
        node_text = board_text[s:e]
        if not _balanced(node_text):
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "节点括号不平衡"})
            continue
        if tag == "arc":
            unrep.append({
                "kind": "arc_track",
                "where": where,
                "reason": "顶层 (arc ...) 走线：P1a 铜箔合同无弧段表达"
                          "（不可近似为 segment，拒绝静默丢失）",
            })
            continue
        try:
            parsed = sexpr_min.parse(node_text)
        except sexpr_min.SexprError as exc:
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "s-expr 解析失败: %s" % exc})
            continue
        if len(parsed) != 1 or not isinstance(parsed[0], list):
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "节点形状非法（非单一列表）"})
            continue
        node = parsed[0]
        if tag == "segment":
            entry, reason = _parse_segment(node)
            if entry is None:
                unrep.append({"kind": "segment_malformed", "where": where,
                              "reason": reason})
                continue
            entry["_span"] = (s, e)
            segments.append(entry)
        elif tag == "via":
            entry, reason = _parse_via(node)
            if entry is None:
                unrep.append({"kind": "via_malformed", "where": where,
                              "reason": reason})
                continue
            entry["_span"] = (s, e)
            vias.append(entry)
        else:  # zone
            entry, outline, reason = _parse_zone(node)
            if entry is None:
                unrep.append({
                    "kind": "zone_no_outline" if "轮廓" in reason
                    else "zone_malformed",
                    "where": where, "reason": reason})
                continue
            points, fill_sha = _zone_fill(node)
            entry["outline_mm"] = outline
            entry["fill_points"] = points
            entry["fill_sha256"] = fill_sha
            entry["params"] = _zone_params(node)
            entry["_span"] = (s, e)
            zones.append(entry)
    return _assemble(segments, vias, zones, unrep)


def parse_copper_scan(board_text: str, scan=None) -> dict:
    """板文本 + 已扫描跨度 → 铜箔事实模型（R5 新入口，复用扫描）。

    与 `parse_copper(board_text)` **逐字节等价**（整份 json 相同：含
    `identity_map` 键序、span 偏移、`unrepresentable` / `identity_disambiguated`
    的顺序与文案），差别只在"谁来扫描"：
    - `scan=None`：自建（等价于 `parse_copper`，一次全量扫描）；
    - `scan=scan_copper(board_text)`：**零额外扫描**（补丁引擎在一次往返里
      同时要铜箔模型与节点跨度时，一次扫描即可喂两边）。

    `scan` 与 `board_text` 不匹配（既非同一对象亦非相等文本）→ ValueError。
    恰好这些顶层键：schema / identity_basis / segments / vias / zones /
    unrepresentable / identity_disambiguated / counts / identity_map /
    copper_sha256。
    """
    if not isinstance(board_text, str):
        raise ValueError("board_text: 不是字符串")
    if scan is None:
        scan = scan_copper(board_text)
    else:
        if not isinstance(scan, CopperScan):
            raise ValueError("scan: 不是 CopperScan（用 scan_copper 生成）")
        scan._bind(board_text)
    return _parse_copper_with_scan(board_text, scan)


def parse_copper(board_text: str) -> dict:
    """板文本 → 铜箔事实模型。

    恰好这些顶层键：schema / identity_basis / segments / vias / zones /
    unrepresentable / identity_disambiguated / counts / identity_map /
    copper_sha256。
    只读纯函数：不改动输入、不落盘、无 wall-clock、无随机。

    **签名与语义冻结**（R5 硬约束）：仍是单参数；实现等价于
    `parse_copper_scan(board_text)`（一次全量扫描）。需要复用扫描跨度时改用
    `parse_copper_scan`，产出逐字节相同。
    """
    return parse_copper_scan(board_text)


def parse_copper_file(path: str) -> dict:
    """读板文件 → parse_copper（newline="" 保留 CRLF，不做行尾归一化）。"""
    with open(path, encoding="utf-8", newline="") as f:
        return parse_copper(f.read())
