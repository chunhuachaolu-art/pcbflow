"""PCBFlow 铜箔闭环 P1b —— 真实 KiCad 板 → SVG/manifest 输入适配层（只读）。

职责（"KiCad 铜箔 ↔ manifest ↔ SVG"三向对应的第二腿）：把**真实板**
（KiCad `.kicad_pcb` 文本）与**网络注册表**（`net-registry.json` 逐网视图）
编译成 `pcbflow.svg_route_package.build(board, ref)` 可直接消费的
`(board_dict, ref_dict)`，从而得到全板铜箔的 SVG + manifest。

只读铁律：不写任何板文件、不改注册表、零子进程（**不调 kicad-cli**）、
零 wall-clock、零随机、零网络。产物不含主机路径（canonical hash 域内禁
绝对路径）：需自证来源时只放 sha256，不放路径字符串。

读板铁律：一律 `open(path, encoding="utf-8", newline="")`（保留 CRLF）。
本仓库既有 `residual_cmd._replay_pristine_text` 用默认文本模式读会把
CRLF 归一成 LF，是已知陷阱；适配层不得重蹈（`copper_model.parse_copper_file`
同口径）。sha256 另以二进制读（`hashing.sha256_file`），与文本模式无关。

冻结 API::

    build_inputs(board_path, registry, *, scenario_id, copper=None)
        -> (board_dict, ref_dict)
    build_inputs_report(board_path, registry, *, scenario_id, copper=None)
        -> dict   # 显式上报清单（== board_dict["adapter_notes"]）

对象粒度与身份（1:1，不做任何合并）
----------------------------------
- **1 个铜箔 segment 节点 ↔ 1 条 route**：`route_id = copper["segments"][*]["key"]`
  （`copper_model` 的稳定寻址键：uuid 唯一时=uuid，uuid 被共享时
  `"<uuid>@<几何摘要>"`）；`polyline_mm = [[x1,y1],[x2,y2]]`（segment 起终点）；
  `endpoint_ids = ["@<x1:%.6f>,<y1:%.6f>", "@<x2:%.6f>,<y2:%.6f>"]`
  （确定性节点 id，仅是几何锚点）；`constraint_refs = []`（真实铜箔无约束库
  引用，空列表在生成器契约上合法）；`state = source = "baseline"`；
  `parent_id = None`（真实板无 manifest 侧父子语义）。
- **1 个铜箔 via 节点 ↔ 1 个 via**：`via_id = key`；`from_layer/to_layer`
  取 via 的 `layers[0]/layers[1]`；`center_mm = at`；`drill_mm = drill`；
  `annular_ring_mm = max(0, (size - drill) / 2)`（size/drill 缺失时该式按 0
  算并**逐条上报**；drill 缺失/非正时 via 无法表达 → 丢弃并上报，不编造）。
  **`parent_id` 一律 None**：真实板大量过孔是独立过孔（无同 key 走线，例如
  GND 缝合孔），独立过孔是合法铜箔而非缺陷 —— 这是 P1b 对
  `svg_route_package` 合同的唯一放宽（`_norm_via` 允许 None；SVG
  `data-parent-id=""`，与 route 既有约定一致）。

板级字段（`board_dict["board"]`）
--------------------------------
- `bbox_mm`：**焊盘外沿 ∪ copper** 并集（geo 焊盘 x±w/2, y±h/2 与铜箔几何
  bbox 的并集，6 位量化；用焊盘外沿而非焊盘中心范围，避免 viewBox 裁掉
  焊盘边缘）；`bbox_basis` 写明口径（本阶段**不解析 Edge.Cuts 板框**，
  该缺口记入上报清单 `board_level_gaps`）。
- `layers`：板内顶层 `(layers ...)` 节点解析出的层名（保序）；取不到时按
  铜箔实际声明的层回退，再退到 `["F.Cu", "B.Cu"]`，三种口径分别写入
  `layers_basis ∈ {board_top_level_layers, copper_declared_layers,
  fallback_two_layer}` 并记入上报清单。
- 追加键（生成器 `_check_board` 只校验必需字段与形状、**不拒绝额外键**）：
  `source_board_sha256`（板文件 sha256）、`copper_sha256`
  （= `copper["copper_sha256"]`）、`identity_basis`
  （= `copper["identity_basis"]`）、`bbox_basis`、`layers_basis`。

焊盘（`board_dict["pads"]`）
---------------------------
由 `geo.parse_board(board_path)` 映射：`pad_id = f"{ref}.{num}"`（与注册表
`REF.PIN` 端点约定一致）、`x_mm/y_mm/w_mm/h_mm` 取 geo 的（w/h 是封装原始
`(size ...)`，未做 pad 旋转后的轴对齐包围盒换算，该缺口记入上报清单）、
`net_id` **必须**经注册表解析（板上的 net 名 → net_id；经 `net_name`，其次
经 `aliases`）。解析不到的 net **绝不静默编造 net_id**：该 pad 的 `net_id`
置为 `""`（"无已注册网络身份"，非编造的 id）并逐条进上报清单
（`pads_without_registered_net`，含 registry 是否已 `excluded_nets` 列账）。
`pad_id` 在本板重复时（真实 Rev-C 存在：空编号机械焊盘、J5 屏蔽垫、
SW1 复用编号）第 2 个起确定性加后缀 `#2/#3/...`（避免 SVG 元素 id 重复，
几何一个不丢）并逐条上报。

`layer` 由板文本里焊盘自身的 `(layers ...)` 判定（**真相在板上**）：
含 `*.Cu` → `"*.Cu"`（通孔/全铜层，KiCad 的原生表达）；单一铜层 → 该层；
多铜层 → 空格连接的稳定序；无任何铜层（如仅 paste 的垫）或取不到层声明
→ 回退 `"F.Cu"`（唯一无证据情形下的确定默认）并逐条上报 `pad_layer_fallback`。
**注意**：`geo` 的 `side`（N/E/S/W 列表）是**封装 pad-bbox 的罗盘侧**（逃逸
方向代理），不是铜面，"前=F.Cu/后=B.Cu" 的 side→layer 推导在语义上不成立，
故本适配层不用它作 layer 依据（批判性修正，已实测：真实板 564 个焊盘中
168 个是 `*.Cu` 通孔垫，其 side 分布在四个方向）。

关系（`board_dict["relations"]`）
--------------------------------
注册表 `relations`（dict）→ 生成器 `{relation_id, relation_type, members,
parent_id=None}`。`kind → RELATION_TYPES` 映射表（写死；依据取自注册表
编译源 `pcbflow/net_registry.py` 与 `structures.json` 的实际谱系）::

    differential_pair → differential_pair   # 直译；RDP-USB（members=USB D±）
    length_group      → bus                 # 时序组=并行总线组（RLG-G_* 与
                                            #   structures.mapping.timing_groups
                                            #   1:1，即 config.NINE_GROUPS）
    symmetry_class    → bus                 # 其 members 直接取自
                                            #   structures["buses"][*]["members"]
                                            #   （BUS_USB/BUS_FMC），本即总线组
    bus               → bus                 # 直译
    clock_group       → clock_group         # 直译
    topology_trunk    → topology_trunk      # 直译

映射表外的 kind **不得硬塞**：该 relation 不进 `board_dict["relations"]`
（也就不进 SVG/manifest），逐条进上报清单 `unmapped_relation_kinds`；
其成员网在 route 的 `relation_ids` 里也不出现（route 只引用已发出的
relation，保证 SVG/manifest 内引用闭合）。

其他
----
- `board_dict["keepouts"] = []`：**本阶段不做板级 keepout 解析**（不在范围），
  故为空列表；这是显式声明而非"没有 keepout"的断言（真实板若有 keepout
  规则不在此腿表达）。

zone（`ref_dict["zones"]`，铜箔闭环 P3 合同 v2 纳入；只读）
----------------------------------------------------------
- **1 个铜箔 zone 节点 ↔ 1 个 zone**：`zone_id = key`（同 route/via 的稳定
  寻址键；重复时确定性加后缀并上报）；`net_id` **必须**经注册表解析
  （板上 net 名 → net_id，经 `net_name` 其次 `aliases`）；`layers` 直取板上
  声明（保序）；`outline_mm` 取 **zone 轮廓**（`polygon/pts`，6 位量化）而
  **不是**填充几何；`outline_kind = "polygon"`。
- **派生数据如实标记**：`fill_sha256`/`fill_points` 取自 `copper_model` 对
  KiCad `filled_polygon` 的统计（派生数据；生成器把它们放进 manifest 的
  `fill` 组并标 `derived: true`，**不进** zone 事实哈希）。
- **`fill_state` 一律 `"unknown"`（绝不谎称 fresh）**：适配层不跑
  kicad-cli、不重算填充，本阶段**没有**任何"填充已按当前轮廓重填"的证据，
  故如实标 `unknown`（生成器侧也只在调用方显式给出指纹时才允许 `fresh`）。
  该值在 manifest 逐条可读、在 SVG 可读（`data-fill-state`）、并汇总进
  `zones_summary.not_fresh_zone_ids` —— 供 P3b"未重填不得采纳"直接消费。
- net 未注册 / 轮廓不可表达（缺失、<3 点、形状非法）的 zone **不进** ref
  （net_id 不可编造），逐条上报：前者进 `unmapped_nets`（`occurrences.zones`
  / `subjects.zones`），后者进 `zones_unrepresentable`；两者合并计数到
  `zones_not_represented`（`zones_not_represented` 现在只数**未表达**的
  zone，已表达的 zone 见 `zones_in_manifest`）。
- **合同边界**：`board_binding.verify_board_binding` 仍把 zone 记在
  `pending["zone_contract_v2"]`（该模块属另一工作流，本阶段**不改**）；本阶段
  的 zone 核对在 `board_svg_adapter`（事实映射 + 上报）与 `svg_route_package`
  （manifest↔SVG 两条腿 + `zones_facts_sha256`）侧完成。`board_binding` 的
  pending 条目待其工作流清理（详见 `zones_in_manifest["reason"]`）。
- route/via 的 `net_id` 一律取注册表 net_id；`line_type` 由注册表
  `electrical_role.value` 映射::

      power_rail / power_switch_node / power_feedback / power_enable → power
      ground_return / ground_return_analog                          → ground
      differential_positive                                         → diff_p
      differential_negative                                         → diff_n
      clock / crystal_node                                          → clock
      其余（ordinary_signal / ordinary_gpio / ordinary_control /
      test_or_configuration / reset / analog_sensitive）             → signal

  角色缺失或落在映射表外的取值同样给 `signal`，但必须记入上报清单
  （`line_type_defaulted`，按 net 去重）——"能映射的映射、映射不了的显式报出"。
- 板上的 net 名解析不到 net_id 的 segment/via **不进入** ref（net_id 不可
  编造），逐条上报 `unmapped_nets`（带 identity key 与出现次数）。
- `copper` 参数可注入（同一板文本的 `copper_model.parse_copper*` 产物，
  含 `copper_sha256`）；缺省时按 `copper_model.parse_copper_file(board_path)`
  读取（内部已是 `newline=""`）。

fail-closed：能映射的映射，映射不了的**显式报出**，绝不静默丢弃或编造。
入参形状非法（registry 非对象 / scenario_id 空 / copper 缺字段）与板文本
不可解析（`geo.parse_board` 的 `sexpr_min.SexprError` 是 ValueError 子类）
一律抛 `ValueError`：宁可不产出，也不产出半成品。

**已知口径**（生成器 verify 侧的 net 全集只取产物内出现的 route/pad net，
无注册表入参）：若注册表某 relation 的成员网在本板既无焊盘也无走线（该网
无铜箔事实），关系仍如实发出，但 `verify_consistency` 会对该成员各报一条
『不是已注册 net』（SVG 侧 + manifest 侧）。该情形已在
`adapter_notes["relation_member_gaps"]` 逐条登记（可归属、不静默）。

本模块不落盘；报告随 `board_dict["adapter_notes"]` 一并返回（该键不在
生成器要求的字段形状内，不污染合同；`*_sha256` 键按 §9 不参与 canonical
hash，其余诊断内容参与 board_snapshot_sha256）。
"""

from __future__ import annotations

import re

from . import copper_model, geo, hashing, sexpr_min

__all__ = [
    "ADAPTER_SCHEMA", "ELECTRICAL_ROLE_TO_LINE_TYPE", "DEFAULT_LINE_TYPE",
    "RELATION_KIND_TO_TYPE", "BBOX_BASIS", "LAYERS_BASIS_BOARD",
    "LAYERS_BASIS_COPPER", "LAYERS_BASIS_FALLBACK", "MISSING_NET_ID",
    "ZONE_FILL_STATE_UNKNOWN", "ZONE_OUTLINE_KIND",
    "build_inputs", "build_inputs_report",
]

ADAPTER_SCHEMA = "pcbflow.board-svg-adapter/1"

#: zone 本阶段的 fill_state：适配层不跑 kicad-cli、不重算 filled_polygon，
#: **没有**"填充已按当前轮廓重填"的证据 → 如实标 "unknown"（绝不谎称
#: fresh；取值口径与 svg_route_package.ZONE_FILL_STATES 一致）
ZONE_FILL_STATE_UNKNOWN = "unknown"

#: zone 轮廓种类：本阶段只从 polygon/pts 取多边形轮廓
ZONE_OUTLINE_KIND = "polygon"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: 无证据时的确定默认线型（"查不到角色"必须同时进上报清单）
DEFAULT_LINE_TYPE = "signal"

#: 注册表 electrical_role.value → 生成器 LINE_TYPES（依据见模块 docstring）
ELECTRICAL_ROLE_TO_LINE_TYPE = {
    "power_rail": "power",
    "power_switch_node": "power",
    "power_feedback": "power",
    "power_enable": "power",
    "ground_return": "ground",
    "ground_return_analog": "ground",
    "differential_positive": "diff_p",
    "differential_negative": "diff_n",
    "clock": "clock",
    "crystal_node": "clock",
    "ordinary_signal": "signal",
    "ordinary_gpio": "signal",
    "ordinary_control": "signal",
    "test_or_configuration": "signal",
    "reset": "signal",
    "analog_sensitive": "signal",
}

#: 注册表 relations[*].kind → 生成器 RELATION_TYPES（谱系依据见 docstring）
RELATION_KIND_TO_TYPE = {
    "differential_pair": "differential_pair",
    "length_group": "bus",
    "symmetry_class": "bus",
    "bus": "bus",
    "clock_group": "clock_group",
    "topology_trunk": "topology_trunk",
}

#: bbox 口径（写进 board.bbox_basis）：pads ∪ copper 并集
BBOX_BASIS = "pads_copper_union"

#: board.layers 的三种来源口径（写进 board.layers_basis）
LAYERS_BASIS_BOARD = "board_top_level_layers"
LAYERS_BASIS_COPPER = "copper_declared_layers"
LAYERS_BASIS_FALLBACK = "fallback_two_layer"

#: pad 无已注册网络身份时的 net_id（非编造 id；逐条上报）
MISSING_NET_ID = ""

_FALLBACK_LAYERS = ("F.Cu", "B.Cu")
_FALLBACK_PAD_LAYER = "F.Cu"
_COPPER_SUFFIX = ".Cu"
_ALL_COPPER = "*.Cu"
_TOP_LAYER_NAME_INDEX = 1  # (0 "F.Cu" signal [别名]) → 层名在第 1 个叶子


# ------------------------------------------------------------------ 基础

def _q6(v) -> float:
    return round(float(v), 6)


def _q3(v) -> float:
    return round(float(v), 3)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _read_board_text(board_path: str) -> str:
    """读板文本（newline="" 保留 CRLF；见模块 docstring 的读板铁律）。"""
    _require(isinstance(board_path, str) and board_path != "",
             "board_path: 必须是非空字符串")
    with open(board_path, encoding="utf-8", newline="") as f:
        return f.read()


def _root(text: str):
    """板文本 → 顶层节点（parse 失败返回 None，由调用方记入缺口）。"""
    try:
        parsed = sexpr_min.parse(text)
    except sexpr_min.SexprError:
        return None
    if len(parsed) != 1 or not isinstance(parsed[0], list):
        return None
    return parsed[0]


def _direct_children(node, tag: str) -> list:
    if not isinstance(node, list):
        return []
    return [c for c in node[1:]
            if isinstance(c, list) and c and c[0] == tag]


def _top_level_layer_names(root) -> list:
    """顶层 `(layers ...)` → 层名列表（保序）。

    KiCad6+：`(layers (0 "F.Cu" signal) ...)`，层名在第 2 个叶子；
    KiCad5：`(layers F.Cu B.Cu ...)`，层名即叶子本身。取不到返回 []。
    """
    out = []
    for node in _direct_children(root, "layers"):
        for entry in node[1:]:
            if isinstance(entry, list):
                name = sexpr_min.get_str(entry, _TOP_LAYER_NAME_INDEX)
                if isinstance(name, str) and name:
                    out.append(name)
            elif isinstance(entry, str) and entry:
                out.append(entry)
        break  # 顶层只应有一个 (layers ...)
    return out


def _copper_layer_of(declared_layers) -> "str | None":
    """焊盘层声明 → 单值 layer（保留 `*.Cu` 通孔表达）；无铜层返回 None。"""
    copper = [l for l in declared_layers
              if isinstance(l, str) and l.endswith(_COPPER_SUFFIX)]
    if not copper:
        return None
    if _ALL_COPPER in copper:
        return _ALL_COPPER
    uniq = sorted(set(copper))
    return uniq[0] if len(uniq) == 1 else " ".join(uniq)


def _pad_layer_map(root) -> dict:
    """板文本 → {(ref, num): [layer_str, ...]}（同键多垫按文档序排列）。

    只读顶层 footprint 的 Reference 属性与 pad 的编号/层声明（纯文本结构
    读取，不重算几何；几何归 geo）。键值的顺序与 `geo.parse_board` 的 pads
    顺序在与 (ref, num) 同组的子序列上一致（两者皆文档序），故可按下标对齐。
    """
    out = {}
    for fp in _direct_children(root, "footprint"):
        ref = None
        for prop in sexpr_min.find_all(fp, "property"):
            if sexpr_min.get_str(prop, 1) == "Reference":
                ref = sexpr_min.get_str(prop, 2)
        if not isinstance(ref, str) or ref == "":
            continue
        for pad in sexpr_min.find_all(fp, "pad"):
            num = sexpr_min.get_str(pad, 1)
            if not isinstance(num, str):
                num = ""
            layers_node = sexpr_min.find_first(pad, "layers")
            declared = list(layers_node[1:]) if layers_node else []
            out.setdefault((ref, num), []).append(
                _copper_layer_of(declared))
    return out


# ------------------------------------------------------------------ 注册表

def _net_index(registry: dict):
    """注册表 → (name→net_id, net_id→record, excluded_names, 别名命中数)。

    先按 `net_name` 建索引，再用 `aliases` 补齐缺失键（同名冲突时
    `net_name` 优先；别名同样取自注册表，故不是编造身份）。
    """
    by_name, records, excluded = {}, {}, set()
    nets = [n for n in (registry.get("nets") or []) if isinstance(n, dict)]
    for n in nets:
        nid, name = n.get("net_id"), n.get("net_name")
        if not (isinstance(nid, str) and nid):
            continue
        records[nid] = n
        if isinstance(name, str) and name and name not in by_name:
            by_name[name] = nid
    alias_hits = 0
    for n in nets:
        nid = n.get("net_id")
        if not (isinstance(nid, str) and nid):
            continue
        for alias in n.get("aliases") or []:
            if isinstance(alias, str) and alias and alias not in by_name:
                by_name[alias] = nid
                alias_hits += 1
    for e in registry.get("excluded_nets") or []:
        if isinstance(e, dict) and isinstance(e.get("net_name"), str):
            excluded.add(e["net_name"])
    return by_name, records, excluded, alias_hits


def _relation_index(registry: dict):
    """注册表 relations → (net_id→relation_ids, 已映射 relations, 未映射)。

    注册表 `relations` 实测为 dict（relation_id → 记录）；同时兼容 list
    形状。kind 无法映射的不进产物（不硬塞），逐条返回给上报清单。
    """
    raw = registry.get("relations")
    if isinstance(raw, dict):
        items = [raw[k] for k in sorted(raw)]
    elif isinstance(raw, list):
        items = list(raw)
    else:
        items = []
    by_net, mapped, unmapped = {}, [], []
    for rel in items:
        if not isinstance(rel, dict):
            continue
        rid, members, kind = (rel.get("relation_id"), rel.get("members"),
                              rel.get("kind"))
        if not (isinstance(rid, str) and rid):
            continue
        if not (isinstance(members, list) and members
                and all(isinstance(m, str) and m for m in members)):
            continue
        rtype = RELATION_KIND_TO_TYPE.get(kind)
        if rtype is None:
            unmapped.append({
                "relation_id": rid, "kind": kind, "members": sorted(members),
                "reason": "注册表 kind 在 RELATION_TYPES 中无对应（不得硬塞）："
                          "该关系不进 SVG/manifest，显式上报"})
            continue
        mapped.append({"relation_id": rid, "relation_type": rtype,
                       "members": sorted(members), "parent_id": None})
        for m in members:
            by_net.setdefault(m, set()).add(rid)
    for m in by_net:
        by_net[m] = sorted(by_net[m])
    mapped.sort(key=lambda r: r["relation_id"])
    return by_net, mapped, unmapped


# ------------------------------------------------------------------ 几何

def _copper_bbox(copper: dict):
    """铜箔几何 bbox（segment 起终点 / via at±半径 / zone 轮廓点）。"""
    xs, ys = [], []
    for s in copper.get("segments") or []:
        for p in (s.get("start"), s.get("end")):
            if isinstance(p, list) and len(p) == 2:
                xs.append(float(p[0]))
                ys.append(float(p[1]))
    for v in copper.get("vias") or []:
        at = v.get("at")
        if not (isinstance(at, list) and len(at) == 2):
            continue
        r = float(v.get("size") or 0.0) / 2.0
        xs += [float(at[0]) - r, float(at[0]) + r]
        ys += [float(at[1]) - r, float(at[1]) + r]
    for z in copper.get("zones") or []:
        for p in z.get("outline_mm") or []:
            if isinstance(p, list) and len(p) == 2:
                xs.append(float(p[0]))
                ys.append(float(p[1]))
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _pad_bbox(pads) -> "tuple | None":
    """焊盘**外沿** bbox（x±w/2, y±h/2）；无焊盘返回 None。

    pad 的 w/h 未做旋转后轴对齐换算（见 board_level_gaps），故外沿是
    近似包围盒；用外沿而非 geo.bbox（焊盘中心范围）可避免 viewBox 裁掉
    焊盘边缘。
    """
    xs, ys = [], []
    for p in pads or []:
        px, py = float(p["x"]), float(p["y"])
        pw, ph = float(p["w"]), float(p["h"])
        xs += [px - pw / 2.0, px + pw / 2.0]
        ys += [py - ph / 2.0, py + ph / 2.0]
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _union_bbox(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _unique_id(base: str, seen: dict, notes: list, kind: str,
               subject: str) -> str:
    """同一命名空间内确定性唯一 id（首次原样；重复加 `#2/#3/...` 并上报）。

    真实 Rev-C 存在同 key 铜箔节点（共享 uuid 的路由级内容派生值：2262 个
    segment / 2171 个不同 key、355 个 via / 353 个不同 key）与同 (ref, num)
    焊盘（564 个垫 / 553 个不同键）：生成器要求 route_id/via_id 唯一、SVG
    要求元素 id 唯一，故此处**确定性消歧**而非丢弃或抛错，每次消歧逐条记账。
    """
    base = str(base)
    if base not in seen:
        seen[base] = 1
        return base
    n = seen[base] + 1
    candidate = "%s#%d" % (base, n)
    while candidate in seen:
        n += 1
        candidate = "%s#%d" % (base, n)
    seen[base] = n
    seen[candidate] = 1
    notes.append({"kind": kind, "base_id": base, "id": candidate,
                  "subject": subject,
                  "reason": "同一身份键在本板出现多次（copper_model 已按 "
                            "duplicate_identity_key 登记歧义）：为满足生成器 "
                            "id 唯一约束确定性加序号后缀，对象不丢弃"})
    return candidate


def _endpoint_id(x, y) -> str:
    return "@%.6f,%.6f" % (x, y)


# ------------------------------------------------------------------ 入口

def _check_inputs(board_path, registry, scenario_id, copper) -> None:
    _require(isinstance(registry, dict), "registry: 必须是注册表对象")
    _require(isinstance(scenario_id, str) and scenario_id != "",
             "scenario_id: 必须是非空字符串")
    if copper is not None:
        _require(isinstance(copper, dict), "copper: 必须是对象")
        for f in ("segments", "vias", "copper_sha256"):
            _require(f in copper, f"copper: 缺字段 {f}")
        _require(isinstance(copper["segments"], list)
                 and isinstance(copper["vias"], list),
                 "copper.segments/vias: 必须是列表")
        if copper.get("zones") is not None:
            _require(isinstance(copper["zones"], list),
                     "copper.zones: 必须是列表")


def _bump(no_net: dict, net_name, kind: str, subject) -> None:
    """未解析 net 的台账累加（fail-closed：显式记账，绝不静默丢弃）。"""
    key = net_name if isinstance(net_name, str) and net_name else "<no-net-name>"
    entry = no_net.setdefault(key, {"net_name": net_name,
                                    "registry_excluded": False,
                                    "occurrences": {"pads": 0, "segments": 0,
                                                    "vias": 0, "zones": 0},
                                    "subjects": {"pads": [], "segments": [],
                                                 "vias": [], "zones": []}})
    entry["occurrences"][kind] += 1
    entry["subjects"][kind].append(subject)


def build_inputs(board_path: str, registry: dict, *, scenario_id: str,
                 copper: "dict | None" = None) -> tuple:
    """真实板 + 注册表 → `(board_dict, ref_dict)`，可直接喂
    `svg_route_package.build(board, ref)`。

    纯函数：只读、无副作用、零子进程、无 wall-clock、无主机路径。
    能映射的映射；映射不了的一律进 `board_dict["adapter_notes"]`
    （见 `build_inputs_report`），绝不静默丢弃或编造。
    """
    _check_inputs(board_path, registry, scenario_id, copper)
    text = _read_board_text(board_path)
    board_sha = hashing.sha256_file(board_path)
    if copper is None:
        copper = copper_model.parse_copper_file(board_path)
    root = _root(text)

    by_name, records, excluded, alias_hits = _net_index(registry)
    rel_by_net, relations, unmapped_rels = _relation_index(registry)

    # ---- 板级层表与缺口台账 ----------------------------------------------
    gaps = []
    layers = _top_level_layer_names(root) if root is not None else []
    if layers:
        layers_basis = LAYERS_BASIS_BOARD
    else:
        derived = []
        for layer in [s.get("layer") for s in copper.get("segments") or []] \
                + [l for v in copper.get("vias") or []
                   for l in (v.get("layers") or [])]:
            if isinstance(layer, str) and layer.endswith(_COPPER_SUFFIX) \
                    and layer not in derived:
                derived.append(layer)
        if derived:
            layers, layers_basis = derived, LAYERS_BASIS_COPPER
            gaps.append({"item": "board_top_level_layers",
                         "status": "fallback_copper_declared_layers",
                         "detail": "板文本无顶层 (layers ...)（或解析失败）："
                                   "层表取自铜箔自身声明"})
        else:
            layers = list(_FALLBACK_LAYERS)
            layers_basis = LAYERS_BASIS_FALLBACK
            gaps.append({"item": "board_top_level_layers",
                         "status": "fallback_two_layer",
                         "detail": "板文本无顶层 (layers ...) 且铜箔未声明层："
                                   "回退 %s" % (list(_FALLBACK_LAYERS),)})
    if root is None:
        gaps.append({"item": "board_text_parse", "status": "failed",
                     "detail": "顶层 s-expr 解析失败：焊盘层声明不可用"
                               "（pads 全部走 layer 回退）"})
    gaps.append({"item": "board_frame_edge_cuts", "status": "not_parsed",
                 "detail": "本阶段不解析 Edge.Cuts 板框：bbox 取 pads∪copper "
                           "并集，非板框范围"})
    gaps.append({"item": "pad_rotation_bbox", "status": "not_applied",
                 "detail": "pad 的 w/h 取封装原始 (size ...)，未做旋转后的"
                           "轴对齐包围盒换算"})
    gaps.append({"item": "board_keepouts", "status": "not_parsed",
                 "detail": "本阶段不做板级 keepout 解析：board.keepouts 为空"
                           "列表（显式声明，非『无 keepout』断言）"})

    # ---- pads -------------------------------------------------------------
    parsed = geo.parse_board(board_path)
    pad_layers = _pad_layer_map(root) if root is not None else {}
    layer_ordinal = {}
    pads, dup_notes, no_net = [], [], {}
    pad_layer_fb = []
    seen_pads = {}
    for p in parsed["pads"]:
        ref, num = p["ref"], p["num"]
        key = (ref, num)
        idx = layer_ordinal.get(key, 0)
        layer_ordinal[key] = idx + 1
        declared = pad_layers.get(key) or []
        layer = declared[idx] if idx < len(declared) else None
        layer_fallback = layer is None
        if layer_fallback:
            layer = _FALLBACK_PAD_LAYER  # 无证据时的确定默认（逐条上报）
        raw_pad_id = "%s.%s" % (ref, num)
        pad_id = _unique_id(raw_pad_id, seen_pads, dup_notes,
                            "duplicate_pad_id", "pad %s" % raw_pad_id)
        if layer_fallback:
            pad_layer_fb.append(pad_id)
        net_name = p["net"]
        net_id = by_name.get(net_name) if isinstance(net_name, str) else None
        if net_id is None:
            net_id = MISSING_NET_ID
            _bump(no_net, net_name, "pads", pad_id)
        pads.append({"pad_id": pad_id, "net_id": net_id,
                     "x_mm": _q6(p["x"]), "y_mm": _q6(p["y"]),
                     "w_mm": _q6(p["w"]), "h_mm": _q6(p["h"]),
                     "layer": layer})
    pads.sort(key=lambda x: x["pad_id"])

    # ---- routes（1 个 segment 节点 ↔ 1 条 route） --------------------------
    routes = []
    seen_routes = {}
    line_type_defaulted = {}
    rejected = []
    for seg in copper.get("segments") or []:
        key = seg.get("key")
        start, end = seg.get("start"), seg.get("end")
        width = seg.get("width")
        defect = None
        if not (isinstance(start, list) and len(start) == 2
                and isinstance(end, list) and len(end) == 2):
            defect = "start/end 缺失或形状非法"
        elif not isinstance(width, (int, float)) or isinstance(width, bool) \
                or float(width) <= 0:
            defect = "width 缺失/非正（生成器要求 width_mm > 0）"
        elif not (isinstance(seg.get("layer"), str) and seg.get("layer")):
            defect = "layer 缺失/非法"
        if defect is not None:
            rejected.append({"kind": "segment_unrepresentable", "key": key,
                             "net_name": seg.get("net"), "reason": defect})
            continue
        net_name = seg.get("net")
        net_id = by_name.get(net_name) if isinstance(net_name, str) else None
        if net_id is None:  # net_id 不可编造 → 该 route 不进 ref（显式上报）
            _bump(no_net, net_name, "segments", key)
            continue
        role = (records.get(net_id) or {}).get("electrical_role")
        role_value = role.get("value") if isinstance(role, dict) else None
        line_type = ELECTRICAL_ROLE_TO_LINE_TYPE.get(role_value)
        if line_type is None:
            line_type = DEFAULT_LINE_TYPE
            line_type_defaulted[net_id] = {
                "net_id": net_id,
                "net_name": (records.get(net_id) or {}).get("net_name"),
                "electrical_role": role_value,
                "line_type": DEFAULT_LINE_TYPE,
                "reason": "electrical_role 缺失或不在映射表内：给 signal 并"
                          "显式上报（不静默）"}
        x1, y1 = float(start[0]), float(start[1])
        x2, y2 = float(end[0]), float(end[1])
        routes.append({
            "route_id": _unique_id(key, seen_routes, dup_notes,
                                   "duplicate_copper_key",
                                   "segment net=%s" % (net_name,)),
            "net_id": net_id,
            "relation_ids": list(rel_by_net.get(net_id, ())),
            "line_type": line_type,
            "layer": seg["layer"],
            "width_mm": _q3(width),
            "polyline_mm": [[_q6(x1), _q6(y1)], [_q6(x2), _q6(y2)]],
            "endpoint_ids": [_endpoint_id(x1, y1), _endpoint_id(x2, y2)],
            "constraint_refs": [],
            "state": "baseline",
            "source": "baseline",
            "parent_id": None,
        })

    # ---- vias（1 个 via 节点 ↔ 1 个 via；parent_id 一律 None=独立过孔） ---
    vias = []
    seen_vias = {}
    via_size_notes = []
    for v in copper.get("vias") or []:
        key = v.get("key")
        net_name = v.get("net")
        net_id = by_name.get(net_name) if isinstance(net_name, str) else None
        if net_id is None:
            _bump(no_net, net_name, "vias", key)
            continue
        size, drill = v.get("size"), v.get("drill")
        layers_v = [l for l in (v.get("layers") or [])
                    if isinstance(l, str) and l]
        at = v.get("at")
        bad = []
        if not (isinstance(at, list) and len(at) == 2):
            bad.append("at")
        if len(layers_v) < 2:
            bad.append("layers(<2)")
        if not isinstance(drill, (int, float)) or isinstance(drill, bool) \
                or float(drill) <= 0:
            bad.append("drill(缺失或非正)")
        if bad:
            via_size_notes.append({
                "kind": "via_unrepresentable", "via_key": key,
                "net_name": net_name, "missing_or_bad": bad,
                "reason": "生成器要求 drill_mm>0 且 from/to layer 非空：该过孔"
                          "无法表达 → 不进入 ref（不编造钻孔/层值），显式上报"})
            continue
        if isinstance(size, (int, float)) and not isinstance(size, bool):
            ring = max(0.0, (float(size) - float(drill)) / 2.0)
        else:
            ring = 0.0
            via_size_notes.append({
                "kind": "via_missing_size", "via_key": key,
                "net_name": net_name, "missing_or_bad": ["size"],
                "reason": "size 缺失：annular_ring_mm 按 0 处理（显式上报）"})
        vias.append({
            "via_id": _unique_id(key, seen_vias, dup_notes,
                                 "duplicate_copper_key",
                                 "via net=%s" % (net_name,)),
            "net_id": net_id,
            "parent_id": None,  # 独立过孔（见模块 docstring）
            "from_layer": layers_v[0],
            "to_layer": layers_v[1],
            "center_mm": [_q6(at[0]), _q6(at[1])],
            "drill_mm": _q3(drill),
            "annular_ring_mm": _q3(ring),
        })

    # ---- zones（1 个铜箔 zone 节点 ↔ 1 个 zone；合同 v2，只读进入镜像） ---
    # 事实：net_id/layers/outline_mm（轮廓，非填充）；派生：fill_sha256/
    # fill_points（KiCad filled_polygon，生成器标 derived=true）；fill_state
    # 一律 "unknown"（无重填证据，绝不谎称 fresh）。
    zones = []
    seen_zones = {}
    zone_notes = []
    zone_dropped = []
    for z in copper.get("zones") or []:
        key = z.get("key")
        net_name = z.get("net")
        net_id = by_name.get(net_name) if isinstance(net_name, str) else None
        if net_id is None:  # net_id 不可编造 → 该 zone 不进 ref（显式上报）
            _bump(no_net, net_name, "zones", key)
            zone_dropped.append(key)
            continue
        layers_z = [l for l in (z.get("layers") or [])
                    if isinstance(l, str) and l]
        outline = z.get("outline_mm")
        bad = []
        if not layers_z:
            bad.append("layers(缺失/空)")
        if not (isinstance(outline, list) and len(outline) >= 3
                and all(isinstance(p, (list, tuple)) and len(p) == 2
                        and isinstance(p[0], (int, float))
                        and isinstance(p[1], (int, float))
                        and not isinstance(p[0], bool)
                        and not isinstance(p[1], bool) for p in outline)):
            bad.append("outline_mm(缺失/不足 3 点/形状非法)")
        if bad:
            zone_notes.append({
                "kind": "zone_unrepresentable", "zone_key": key,
                "net_name": net_name, "missing_or_bad": bad,
                "reason": "生成器要求 zone 轮廓为 >=3 点的多边形：该 zone 无法"
                          "表达 → 不进入 ref（不编造轮廓/层值），显式上报"})
            zone_dropped.append(key)
            continue
        fill_sha = z.get("fill_sha256")
        if not (isinstance(fill_sha, str) and _SHA256_RE.match(fill_sha)):
            fill_sha = None
            zone_notes.append({
                "kind": "zone_fill_fingerprint_dropped", "zone_key": key,
                "net_name": net_name, "missing_or_bad": ["fill_sha256"],
                "reason": "派生填充指纹形状非法（非 64 位小写 hex）：按缺失"
                          "处理（不编造指纹；fill_state 仍是 unknown）"})
        points = z.get("fill_points")
        if not (isinstance(points, int) and not isinstance(points, bool)
                and points >= 0):
            points = None
            zone_notes.append({
                "kind": "zone_fill_fingerprint_dropped", "zone_key": key,
                "net_name": net_name, "missing_or_bad": ["fill_points"],
                "reason": "派生填充点数形状非法（非非负整数）：按缺失处理"
                          "（不编造点数；fill_state 仍是 unknown）"})
        zones.append({
            "zone_id": _unique_id(key, seen_zones, dup_notes,
                                  "duplicate_copper_key",
                                  "zone net=%s" % (net_name,)),
            "net_id": net_id,
            "layers": list(layers_z),
            "outline_kind": ZONE_OUTLINE_KIND,
            "outline_mm": [[_q6(p[0]), _q6(p[1])] for p in outline],
            # 本阶段无重填证据 → unknown（见模块 docstring 的 zone 一节）
            "fill_state": ZONE_FILL_STATE_UNKNOWN,
            "fill_sha256": fill_sha,
            "fill_points": points,
        })

    # ---- bbox（pads ∪ copper） -------------------------------------------
    bb = _union_bbox(_pad_bbox(parsed.get("pads")), _copper_bbox(copper))
    _require(bb is not None, "board bbox: 焊盘与铜箔皆空，无法确定 bbox")
    bbox = [_q6(bb[0]), _q6(bb[1]), _q6(bb[2]), _q6(bb[3])]
    if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        bbox = [_q6(bbox[0] - 0.5), _q6(bbox[1] - 0.5),
                _q6(bbox[2] + 0.5), _q6(bbox[3] + 0.5)]
        gaps.append({"item": "board_bbox_degenerate", "status": "inflated",
                     "detail": "pads∪copper 并集面积为零：按 ±0.5mm 确定性"
                               "外扩以得到非零 viewBox（显式上报）"})

    # ---- 关系成员闭合性检查 ----------------------------------------------
    emitted_nets = {p["net_id"] for p in pads if p["net_id"]}
    emitted_nets |= {r["net_id"] for r in routes}
    rel_gaps = []
    for rel in relations:
        missing = [m for m in rel["members"] if m not in emitted_nets]
        if missing:
            rel_gaps.append({
                "relation_id": rel["relation_id"], "members_missing": missing,
                "reason": "该关系成员在本次产物（焊盘/走线）中未出现：关系仍"
                          "发出（成员含未布线网是合法事实），但生成器校验侧的 "
                          "net 全集只取产物内出现的网，故会报『不是已注册 net』"})

    # ---- 上报清单 ---------------------------------------------------------
    unmapped_nets = []
    for name in sorted(no_net, key=str):
        e = dict(no_net[name])
        e["registry_excluded"] = e["net_name"] in excluded
        e["subjects"] = {k: sorted(str(s) for s in v)
                         for k, v in e["subjects"].items()}
        unmapped_nets.append(e)
    copper_zones = copper.get("zones") or []
    notes = {
        "schema": ADAPTER_SCHEMA,
        "scenario_id": scenario_id,
        "board_source_sha256": board_sha,
        "copper_sha256": copper.get("copper_sha256"),
        "identity_basis": copper.get("identity_basis"),
        "bbox_basis": BBOX_BASIS,
        "layers_basis": layers_basis,
        "counts": {
            "pads": len(pads),
            "pads_without_registered_net": sum(
                e["occurrences"]["pads"] for e in unmapped_nets),
            "routes": len(routes),
            "routes_dropped_unmapped_net": sum(
                e["occurrences"]["segments"] for e in unmapped_nets)
                + sum(1 for r in rejected
                      if r["kind"] == "segment_unrepresentable"),
            "vias": len(vias),
            "vias_dropped": sum(e["occurrences"]["vias"]
                                for e in unmapped_nets)
                            + sum(1 for n in via_size_notes
                                  if n["kind"] == "via_unrepresentable"),
            "relations": len(relations),
            "relations_unmapped_kind": len(unmapped_rels),
            "unmapped_nets": len(unmapped_nets),
            "line_type_defaulted_nets": len(line_type_defaulted),
            "ids_disambiguated": len(dup_notes),
            "zones": len(zones),
            "zones_dropped": len(zone_dropped),
            "zones_unrepresentable": len(zone_notes),
            "zones_not_represented": len(zone_dropped),
            "copper_unrepresentable": len(copper.get("unrepresentable") or []),
        },
        "unmapped_nets": unmapped_nets,
        "unmapped_relation_kinds": unmapped_rels,
        "line_type_defaulted": [line_type_defaulted[k]
                                for k in sorted(line_type_defaulted)],
        "vias_missing_size_or_drill": via_size_notes,
        "segments_unrepresentable": rejected,
        "pad_layer_fallback": {
            "kind": "pad_layer_fallback", "count": len(pad_layer_fb),
            "pads": sorted(pad_layer_fb),
            "reason": "板文本未给出该焊盘的铜层声明（或仅 paste 层）：layer "
                      "回退 'F.Cu'（确定默认）并逐条上报，不静默"},
        "ids_disambiguated": dup_notes,
        "zones_in_manifest": {
            "count": len(zones),
            "zone_ids": sorted(z["zone_id"] for z in zones),
            "net_ids": sorted({z["net_id"] for z in zones}),
            "layers": sorted({l for z in zones for l in z["layers"]}),
            # 与 zone_ids 同序（按 zone_id 排序）逐条对齐，便于人读对账
            "outline_points": [len(z["outline_mm"]) for z in
                               sorted(zones, key=lambda x: x["zone_id"])],
            "fill_state_counts": {
                s: sum(1 for z in zones if z["fill_state"] == s)
                for s in ("fresh", "stale", "unknown")},
            "fill_state": ZONE_FILL_STATE_UNKNOWN,
            "fill_state_basis": "adapter_no_refill_evidence",
            "reason": "本阶段 zone 只读进入镜像（SVG/manifest 合同 v2）："
                      "outline_mm（轮廓，非填充）是事实、进 "
                      "svg_route_package.zones_facts_sha256；fill_sha256/"
                      "fill_points 是 KiCad 派生数据并在 manifest 标 "
                      "derived=true；fill_state 一律 'unknown' —— 适配层不跑 "
                      "kicad-cli、不重算 filled_polygon，无『已按当前轮廓重填』"
                      "的证据，故绝不谎称 fresh。zone 的写操作（补丁）在 P3b "
                      "另做。注：pcbflow/board_binding.py 的 pending "
                      "'zone_contract_v2' 属另一工作流（本阶段不改该模块），"
                      "待其清理；本阶段的 zone 核对在 board_svg_adapter 与 "
                      "svg_route_package 两侧完成"},
        "zones_not_represented": {
            "count": len(zone_dropped),
            "keys": sorted(str(k) for k in zone_dropped),
            "reason": "板上 zone 里**未**进入 manifest 的部分（net 未注册 → "
                      "不编造 net_id；或轮廓缺失/<3 点/形状非法 → 不可表达）："
                      "数量/身份键显式列账，绝不假装已表达（已表达者见 "
                      "zones_in_manifest）"},
        "zones_unrepresentable": zone_notes,
        "relation_member_gaps": rel_gaps,
        "board_level_gaps": gaps,
        "alias_resolved_net_names": alias_hits,
        "cardinality": ("route 粒度 = 1 铜箔 segment ↔ 1 route（1:1，不做多段"
                        "合并）；via 粒度 = 1 铜箔 via ↔ 1 via，parent_id 一律 "
                        "None（独立过孔=P1b 合同放宽的唯一处）；zone 粒度 = "
                        "1 铜箔 zone ↔ 1 zone（1:1；outline_mm=轮廓事实，"
                        "fill_*=派生数据，fill_state 一律 unknown）；"
                        "board.keepouts 显式为空（本阶段不解析板级 keepout）"),
    }
    board = {
        "scenario_id": scenario_id,
        "board": {
            "bbox_mm": bbox,
            "layers": list(layers),
            "source_board_sha256": board_sha,
            "copper_sha256": copper.get("copper_sha256"),
            "identity_basis": copper.get("identity_basis"),
            "bbox_basis": BBOX_BASIS,
            "layers_basis": layers_basis,
        },
        "rules": {},
        "pads": pads,
        "relations": relations,
        "keepouts": [],
        "adapter_notes": notes,
    }
    ref = {"scenario_id": scenario_id, "routes": routes, "vias": vias,
           "zones": zones}
    return board, ref


def build_inputs_report(board_path: str, registry: dict, *, scenario_id: str,
                        copper: "dict | None" = None) -> dict:
    """显式上报清单：未映射 net / 未映射 relation kind / 缺 size-drill 的 via /
    层与 bbox 口径 / 缺失的板级信息 / 身份消歧 / zone 进入镜像（
    `zones_in_manifest`，含 fill_state=unknown 的依据）/ **未**表达的 zone
    （`zones_not_represented`）/ 关系成员缺口。

    等价于 `build_inputs(...)[0]["adapter_notes"]`（同一份确定性产物），
    单列函数便于调用方只取诊断，且不污染生成器要求的字段形状。
    """
    board, _ref = build_inputs(board_path, registry,
                               scenario_id=scenario_id, copper=copper)
    return board["adapter_notes"]
