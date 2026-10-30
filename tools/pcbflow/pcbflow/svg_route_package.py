"""PCBFlow V4.0-A —— 代码化 SVG route package（生产模块）。

方案依据：V4-SUPERVISOR-PLAN-2026-09-09.md §2/§3/§4/§9（阶段 V4.0-A：
无模型、无写板，只生成与校验）。本模块自包含全部生产逻辑；v4exp 只作
只读参考，本文件不导入、不修改 pcbflow/v4exp/（红线）。

数据合同（§3）：
- SVG 根节点 data-pcbflow-schema="v4-svg-route-2"，绑定
  data-board-snapshot-sha256 / data-route-manifest-sha256 /
  data-zones-facts-sha256，
  data-coordinate-system="pcbflow-internal-mm"、data-y-axis="down-positive"、
  mm viewBox、preserveAspectRatio="xMidYMid meet"；
- route 对象带 route_id/net_id/relation_id/line_type/parent_id/layer/
  width_mm/state/source/endpoint/constraint-refs 全套 data-* 属性；
  关系对象（route_relation）、via、keepout、图例按 §3.2–3.4；
- via 的 parent_id 允许为 null（SVG `data-parent-id=""`，与 route 的既有
  约定一致）：真实板存在**独立过孔**（无同身份走线的 via，如 GND 缝合孔），
  独立过孔是合法铜箔而非缺陷（P1b 适配层放宽）。给了 parent_id 时的一切
  校验与行为逐字不变：必须指向存在的 route，且不得为空串。
- 机器身份优先于颜色（§2.2）：颜色/线型/class 只是可视化编码，机器事实
  只从 data-* 属性读取；图例本身带版本与 sha256（legend_record，§2.3）。

数据合同版本（v2 = 本模块当前产出；铜箔闭环 P3 扩合同）
------------------------------------------------------
- `SVG_SCHEMA = "v4-svg-route-2"`、
  `MANIFEST_SCHEMA_VERSION = "v4-route-manifest-2"`；**v1 常量保留导出**
  （`SVG_SCHEMA_V1 = "v4-svg-route-1"` /
  `MANIFEST_SCHEMA_VERSION_V1 = "v4-route-manifest-1"`）。v1 产物仍可读：
  其 XML/字段语义未被改写、也不被本模块覆写；但 `verify_consistency` 只对
  v2 签发"一致"结论 —— 把 v1 产物当 v2 校验会**如实**报出版本违规（绝不
  静默接受、绝不"看起来一样"）。下游要显式分流时用
  `is_legacy_package(svg_schema, manifest_schema)`。
- v1 → v2 的唯一差异：新增 `zone` 对象（manifest 顶层 `zones` /
  `zones_summary` / `zones_facts_sha256`，SVG `<g data-object-kind="zone">`，
  图例新增 zone 行）。route/via/relation/pad/keepout/board_edge 的字段、
  语义、量化位数与 hash 口径**逐字不变**（route/via 的既有断言不受影响）。

zone 对象（v2 新增；本阶段只读进入镜像，zone 的写操作在 P3b 另做）
------------------------------------------------------------------
- manifest 顶层 `zones`：每项
  `{zone_id, svg_id, net_id, layers, outline_kind, outline_mm, fill_state,
  fill:{derived, fill_sha256, fill_points}}`。`outline_mm` 按 6 位量化
  （与 route polyline 同口径）、`zone_id` 唯一、列表按 `zone_id` 稳定排序、
  `outline_kind` 本阶段仅 `"polygon"`。
- **事实 vs 派生（不得混淆）**：`net_id`/`layers`/`outline_kind`/`outline_mm`/
  `fill_state` 是 zone 的事实投影，进 `zones_facts_sha256`（该投影的 canonical
  sha256）；KiCad 的 `filled_polygon` 派生数据（`fill.fill_sha256`/
  `fill.fill_points`）**不进事实投影**，且以 `fill.derived=true` 显式标记
  （SVG 侧 `data-fill-derived="true"`）。`fill_sha256` 以 `*_sha256` 结尾，
  按 §9 本就不进 manifest payload hash；`zones_facts_sha256` 同理不进
  payload hash，但由 `verify_consistency` 规则 5 强制重算核对（不作为
  未校验的"自证"字段）。
- **fill_state 语义（关键：生成器不得猜）**：
  `fill_state ∈ ZONE_FILL_STATES = ("fresh","stale","unknown")`，由**调用方
  显式传入**。未传入 → `"unknown"`（绝不假定 fresh）。声明 `"fresh"` 必须
  同时给出 `fill_sha256` 指纹证据，否则 `ValueError` —— 无证据不得声称
  填充新鲜。`stale`/`unknown` 在 manifest 逐条可读
  （`zones[*].fill_state`）、在 SVG 可读（`data-fill-state`），并汇总进
  `zones_summary`（含 `not_fresh_zone_ids`）供 P3b"未重填不得采纳"策略直接
  消费。轮廓变了而填充未重填 ⇒ 调用方给 `stale`；本模块只如实搬运。
- SVG 呈现：`<g id="zone-<zone_id>" data-object-kind="zone" data-zone-id
  data-net-id data-layers data-outline-kind data-fill-state data-fill-derived
  data-fill-projection="outline_only" data-fill-sha256 data-fill-points>`
  内含**唯一**轮廓 `<path id="geom-zone-<zone_id>">`。`d` 用板 mm 世界坐标
  （与 route 同约定）且是**闭合**多边形：首顶点在末尾重复一次（末组坐标必须
  与首组逐位相同），除该闭合点外逐点与 `outline_mm` 零容差。真实填充几何
  （Rev-C 实测 5715 + 18795 点，占板文件近 12%）**不入 SVG**（体积不可接受），
  只画轮廓 + 轮廓的低透明度填充投影，`data-fill-projection="outline_only"`
  明示"这是轮廓投影、不是填充事实"。

一致性核对（§4 规则 1–5）对 zone 的覆盖：规则 1 svg_id/zone_id/net_id 一一
对应；规则 2 轮廓 path 解析后与 `outline_mm` 零容差（含闭合点校验、点数 ≥3）；
规则 3 `layers`/`outline_kind`/`fill_state`/派生标记与 manifest 逐字一致；
规则 5 `zones_facts_sha256` 与 `zones_summary` 重算一致 + SVG 根
`data-zones-facts-sha256` 绑定。

坐标合同：SVG path d / cx / cy / viewBox 直接使用板 mm 世界坐标
（viewBox min-x/min-y = board bbox 原点 - MARGIN_MM），不做 "0 0" 平移；
因此 parse_svg_polyline 的输出与 manifest.polyline_mm 可做零容差
round-trip（两边各自量化到 6 位小数后必须逐点相等）。渲染语义与
xMidYMid meet 下 v4exp 的平移约定完全等价。

一致性核对（§4 解析规则 1–5，fail-closed）：svg_id/route_id/net_id 与
manifest entry 一一对应；SVG path 坐标解析后与 polyline_mm 零容差一致；
layer/width/state/relation 等字段一致；manifest/SVG/snapshot 的 hash 绑定。
任何不一致（含解析失败、结构非法）都进入返回的违规列表，空列表 = 一致；
绝不"以视觉为准"。

canonical（§9）：无 wall-clock、无主机绝对路径；稳定排序（route/via/
relation/pad/keepout 一律按 id 排序）；固定 6 位/3 位小数；固定 XML 属性
顺序；hash = sha256(canonical json)，canonical 形式 sort_keys + 紧凑分隔符
+ 递归剔除 *_sha256 键（含 manifest_payload_sha256 与
board_snapshot_sha256 自身）；摘要复用 pcbflow.hashing.sha256_text。

生成器模式：零子进程、零 argv、零 wall-clock、零网络、零落盘；
PNG 视觉投影是可选函数（缺 Pillow 时返回明确 not_available，不抛裸异常；
机器事实绝不从 PNG 读取）。
"""

from __future__ import annotations

import io
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal

from . import hashing

__all__ = [
    "SVG_SCHEMA", "MANIFEST_SCHEMA_VERSION", "LEGEND_VERSION",
    "SVG_SCHEMA_V1", "MANIFEST_SCHEMA_VERSION_V1", "is_legacy_package",
    "SVG_COORD_SYSTEM", "SVG_Y_AXIS", "PRESERVE_ASPECT_RATIO", "MARGIN_MM",
    "LINE_TYPES", "RELATION_TYPES", "ROUTE_STATES", "ROUTE_SOURCES",
    "ZONE_FILL_STATES", "ZONE_OUTLINE_KINDS", "SVG_ZONE_ATTRS",
    "LEGEND_COLORS", "STATE_COLORS",
    "build", "build_manifest", "build_svg", "verify_consistency",
    "parse_svg_polyline", "parse_svg_zone_outline", "zone_facts_sha256",
    "legend_record", "render_png",
]

# ---- 合同常量（V4-SUPERVISOR-PLAN §2/§3；铜箔闭环 P3 提升到 v2） -----------
# v2 = 新增 zone 对象（见模块 docstring）；v1 常量保留导出，v1 产物仍可读、
# 不被覆写语义，但 verify_consistency 只对 v2 签发"一致"结论。
SVG_SCHEMA = "v4-svg-route-2"
MANIFEST_SCHEMA_VERSION = "v4-route-manifest-2"
SVG_SCHEMA_V1 = "v4-svg-route-1"
MANIFEST_SCHEMA_VERSION_V1 = "v4-route-manifest-1"
LEGEND_VERSION = "pcbflow-v4-legend-1"
SVG_COORD_SYSTEM = "pcbflow-internal-mm"
SVG_Y_AXIS = "down-positive"
PRESERVE_ASPECT_RATIO = "xMidYMid meet"
SVG_VERSION = "1.1"
SVG_NS = "http://www.w3.org/2000/svg"
MARGIN_MM = 2.0  # viewBox 世界坐标边距 M

# §2.2 line_type 全集（颜色只是可视化编码，见表 §2.3）
LINE_TYPES = ("signal", "power", "ground", "diff_p", "diff_n", "clock",
              "bus_trunk", "bus_member", "keepout_boundary", "via_stub")
# §3.3 关系类型（differential_pair/bus 等显式表达，不靠颜色猜）
RELATION_TYPES = ("bus", "differential_pair", "clock_group", "topology_trunk")
# §2.2 state 全集
ROUTE_STATES = ("locked", "baseline", "candidate", "proposed", "conflict",
                "rejected")
# §2.2 source 全集（对象来自哪一方）
ROUTE_SOURCES = ("baseline", "solver", "planner", "human_edit")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DEC6_RE = re.compile(r"^-?\d+\.\d{6}$")
DEC3_RE = re.compile(r"^-?\d+\.\d{3}$")
CONSTRAINT_REF_RE = re.compile(r"^C-[a-z][a-z-]*-\d{3}$")

# v2 新增：zone 的 fill_state 全集（调用方显式传入；生成器不猜）
ZONE_FILL_STATES = ("fresh", "stale", "unknown")
# v2 新增：zone 轮廓种类（本阶段仅多边形）
ZONE_OUTLINE_KINDS = ("polygon",)

SVG_OBJECT_KINDS = ("route_segment", "via", "route_relation", "pad",
                    "keepout", "board_edge", "zone")
SVG_ROUTE_ATTRS = ("data-route-id", "data-net-id", "data-relation-id",
                   "data-line-type", "data-parent-id", "data-layer",
                   "data-width-mm", "data-state", "data-source",
                   "data-endpoint-start", "data-endpoint-end",
                   "data-constraint-refs")
SVG_VIA_ATTRS = ("data-via-id", "data-net-id", "data-parent-id",
                 "data-from-layer", "data-to-layer", "data-drill-mm",
                 "data-annular-ring-mm")
SVG_RELATION_ATTRS = ("data-relation-id", "data-relation-type",
                      "data-member-ids")
# v2：zone 组的必填 data-*（派生填充标记另查，见 _collect_zone）
SVG_ZONE_ATTRS = ("data-zone-id", "data-net-id", "data-layers",
                  "data-outline-kind", "data-fill-state")

# ---- 图例（§2.3：颜色/线型只是可视化编码；图例本身有版本和 hash） ----------
LEGEND_COLORS = {
    "signal": "#3B82F6", "power": "#DC2626", "ground": "#374151",
    "diff_p": "#8B5CF6", "diff_n": "#14B8A6", "clock": "#F97316",
    "bus_trunk": "#22C55E", "bus_member": "#06B6D4",
    "keepout_boundary": "#111111", "via_stub": "#7C3AED"}
STATE_COLORS = {"candidate": "#EAB308", "conflict": "#EC4899"}
VIA_COLOR = "#111111"
PAD_FILL = "#9CA3AF"
KEEPOUT_COLOR = "#111111"
BOARD_EDGE_COLOR = "#111111"
ZONE_COLOR = "#0EA5E9"        # v2：zone 轮廓/投影色（仅可视化编码）
ZONE_FILL_OPACITY = "0.10"    # 轮廓投影透明度（真实填充几何不入 SVG）

# SVG 图例框实际绘制的行（legend_record.entries 是权威全集，绘制是其投影）
_LEGEND_DRAW_ROWS = (
    ("line-signal", "signal"), ("line-clock", "clock"),
    ("line-bus_trunk", "bus_trunk"), ("line-bus_member", "bus_member"),
    ("line-candidate", "candidate"), ("line-conflict", "conflict"),
    ("via", "via"), ("pad", "pad"), ("keepout", "keepout"),
    ("zone", "zone"))


class _ContractError(ValueError):
    """SVG/manifest 合同违规（fail-closed 解析错误；ValueError 子类）。"""


def is_legacy_package(svg_schema, manifest_schema) -> bool:
    """(svg_schema, manifest_schema) 是否为 **v1**（无 zone 对象）产物。

    仅用于让下游**显式分流**：v1 产物仍可读（其 XML/字段未被本模块改写），
    但不满足 v2 合同；`verify_consistency` 对 v1 会如实报版本违规（绝不静默
    接受、绝不覆写语义）。返回 False 不等于"版本合法"——只表示不是这对
    已知的 v1 常量组合。
    """
    return (svg_schema == SVG_SCHEMA_V1
            and manifest_schema == MANIFEST_SCHEMA_VERSION_V1)


# ------------------------------------------------------------- canonical/hash

def _strip_sha(obj):
    """递归剔除 *_sha256 键（凡被 hash 的对象先做这一步，§9）。"""
    if isinstance(obj, dict):
        return {k: _strip_sha(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [_strip_sha(v) for v in obj]
    return obj


def _canonical_json(obj) -> str:
    """铜族+strip_sha 形态（先剥自指 sha 再取形）——登记=
    exec/CANONICAL-JSON-FORM-MAP-2026-09-25.md。"""
    return json.dumps(_strip_sha(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _sha256_of(obj) -> str:
    """canonical sha256（复用 pcbflow.hashing.sha256_text）。"""
    return hashing.sha256_text(_canonical_json(obj))


def _q3(v) -> float:
    return round(float(v), 3)


def _q6(v) -> float:
    return round(float(v), 6)


def _fmt3(v) -> str:
    return f"{float(v):.3f}"


def _fmt6(v) -> str:
    return f"{float(v):.6f}"


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _require_unique(ids: list, what: str) -> None:
    seen = set()
    for i in ids:
        if i in seen:
            raise ValueError(f"{what} 重复: {i!r}")
        seen.add(i)


def _index(entries, key: str) -> dict:
    """把 manifest 侧对象列表按 id 键收敛为 dict（非法项忽略，另行报违规）。"""
    out = {}
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and isinstance(e.get(key), str):
                out[e[key]] = e
    return out


def legend_record() -> dict:
    """图例记录（§2.3）：图例本身有版本和 sha256。

    颜色/线型仅是可视化编码（§2.2），记录中每项都声明其对应的机器事实
    data-* 字段；禁止从颜色反推事实。legend_sha256 对剔除 *_sha256 键后
    的 canonical 形式计算。
    """
    entries = []
    for lt in LINE_TYPES:
        entries.append({"item": "line_type", "value": lt,
                        "color": LEGEND_COLORS[lt],
                        "machine_fact": f"data-line-type={lt}"})
    for st in ("candidate", "conflict"):
        entries.append({"item": "state", "value": st,
                        "color": STATE_COLORS[st],
                        "machine_fact": f"data-state={st}"})
    entries.append({"item": "via", "value": "via", "color": VIA_COLOR,
                    "machine_fact": "data-object-kind=via"})
    entries.append({"item": "pad", "value": "pad", "color": PAD_FILL,
                    "machine_fact": "data-object-kind=pad"})
    entries.append({"item": "keepout", "value": "keepout",
                    "color": KEEPOUT_COLOR,
                    "machine_fact": "data-object-kind=keepout"})
    entries.append({"item": "zone", "value": "zone", "color": ZONE_COLOR,
                    "machine_fact": "data-object-kind=zone",
                    "note": "SVG 内 zone 只画轮廓与其低透明度投影"
                            "（data-fill-projection=outline_only）：真实填充"
                            "几何是 KiCad 派生数据，不入 SVG、不入事实哈希"})
    rec = {"legend_version": LEGEND_VERSION,
           "color_is_visual_only": True,
           "note": "颜色/线型/class 仅是可视化编码，机器事实只来自 data-*"
                   " 属性（V4-SUPERVISOR-PLAN §2.2/§2.3）",
           "entries": entries}
    rec["legend_sha256"] = _sha256_of(rec)
    return rec


# ---------------------------------------------------------------- build 侧

def _qpolyline(poly) -> list:
    _require(isinstance(poly, list) and len(poly) >= 2,
             "polyline_mm: 至少 2 个点")
    out = []
    for i, p in enumerate(poly):
        _require(isinstance(p, (list, tuple)) and len(p) == 2
                 and _num(p[0]) and _num(p[1]),
                 f"polyline_mm[{i}]: 必须是 [x, y] 数值对")
        out.append([_q6(p[0]), _q6(p[1])])
    return out


def _qoutline(poly) -> list:
    """zone 轮廓量化（6 位，与 polyline 同口径）；多边形至少 3 点。"""
    _require(isinstance(poly, list) and len(poly) >= 3,
             "outline_mm: 多边形轮廓至少 3 个点")
    out = []
    for i, p in enumerate(poly):
        _require(isinstance(p, (list, tuple)) and len(p) == 2
                 and _num(p[0]) and _num(p[1]),
                 f"outline_mm[{i}]: 必须是 [x, y] 数值对")
        out.append([_q6(p[0]), _q6(p[1])])
    return out


def _zone_fact_projection(zone: dict) -> dict:
    """zone 的**事实投影**（进 zones_facts_sha256 的唯一字段集）。

    只含事实与调用方声明的 fill_state；**不含** fill 派生组
    （fill_sha256/fill_points/derived 一类 KiCad 派生数据）。fill_state 进
    事实投影是因为 P3b 的"未重填不得采纳"策略直接读它，它必须防篡改可检。
    """
    return {"zone_id": zone.get("zone_id"), "net_id": zone.get("net_id"),
            "layers": zone.get("layers"),
            "outline_kind": zone.get("outline_kind"),
            "outline_mm": zone.get("outline_mm"),
            "fill_state": zone.get("fill_state")}


def zone_facts_sha256(zones) -> str:
    """zone 事实投影的 canonical sha256（按 zone_id 稳定排序后计算）。

    这是 zone 的**事实哈希**（轮廓/net/layers/outline_kind/fill_state）；
    填充派生数据（fill_sha256/fill_points）刻意不在其中 —— 改派生数据不得
    改变事实哈希，改轮廓必须改变它。下游可独立重算本函数做交叉核对。
    """
    proj = [_zone_fact_projection(z) for z in (zones or [])
            if isinstance(z, dict)]
    proj.sort(key=lambda d: str(d.get("zone_id")))
    return _sha256_of(proj)


def _check_board(board: dict) -> None:
    """板快照对象最小形状校验（生产者侧严格，非法即 ValueError）。"""
    _require(isinstance(board, dict), "board: 不是对象")
    _require(isinstance(board.get("scenario_id"), str)
             and board["scenario_id"] != "", "board.scenario_id 缺失")
    b = board.get("board")
    _require(isinstance(b, dict), "board.board: 缺失")
    bbox = b.get("bbox_mm")
    _require(isinstance(bbox, list) and len(bbox) == 4
             and all(_num(v) for v in bbox),
             "board.board.bbox_mm: 必须是 4 个数值")
    _require(bbox[0] < bbox[2] and bbox[1] < bbox[3],
             "board.board.bbox_mm: 需 x0<x1 且 y0<y1")
    pads = board.get("pads") or []
    _require(isinstance(pads, list), "board.pads: 必须是列表")
    for i, p in enumerate(pads):
        _require(isinstance(p, dict), f"board.pads[{i}]: 不是对象")
        for f in ("pad_id", "net_id", "x_mm", "y_mm", "w_mm", "h_mm",
                  "layer"):
            _require(f in p, f"board.pads[{i}]: 缺字段 {f}")
    for name in ("keepouts", "relations"):
        _require(isinstance(board.get(name) or [], list),
                 f"board.{name}: 必须是列表")


def _norm_route(raw: dict) -> dict:
    _require(isinstance(raw, dict), "ref.routes[*]: 不是对象")
    rid = raw.get("route_id")
    _require(isinstance(rid, str) and rid != "", "route: route_id 缺失")
    where = f"route {rid}"
    for f in ("net_id", "relation_ids", "line_type", "layer", "width_mm",
              "polyline_mm", "endpoint_ids", "constraint_refs", "state",
              "source"):
        _require(f in raw, f"{where}: 缺字段 {f}")
    _require(raw["line_type"] in LINE_TYPES,
             f"{where}: line_type {raw['line_type']!r} 非法")
    _require(raw["state"] in ROUTE_STATES,
             f"{where}: state {raw['state']!r} 非法")
    _require(raw["source"] in ROUTE_SOURCES,
             f"{where}: source {raw['source']!r} 非法")
    _require(isinstance(raw["layer"], str) and raw["layer"] != "",
             f"{where}: layer 非法")
    _require(_num(raw["width_mm"]) and raw["width_mm"] > 0,
             f"{where}: width_mm 必须为正数")
    _require(isinstance(raw["net_id"], str) and raw["net_id"] != "",
             f"{where}: net_id 非法")
    rel = raw["relation_ids"]
    _require(isinstance(rel, list) and all(isinstance(v, str) for v in rel),
             f"{where}: relation_ids 必须是字符串列表")
    eps = raw["endpoint_ids"]
    _require(isinstance(eps, list) and len(eps) == 2
             and all(isinstance(v, str) and v for v in eps),
             f"{where}: endpoint_ids 必须是 2 个非空字符串")
    refs = raw["constraint_refs"]
    _require(isinstance(refs, list) and all(isinstance(v, str) for v in refs),
             f"{where}: constraint_refs 必须是字符串列表")
    for ref in refs:
        _require(CONSTRAINT_REF_RE.match(ref),
                 f"{where}: constraint ref {ref!r} 形状不符"
                 "（C-<kind>-<3位百分毫米>）")
    parent = raw.get("parent_id")
    _require(parent is None or isinstance(parent, str),
             f"{where}: parent_id 非法")
    return {"route_id": rid, "svg_id": f"route-{rid}",
            "net_id": raw["net_id"], "relation_ids": [str(v) for v in rel],
            "line_type": raw["line_type"], "parent_id": parent,
            "layer": raw["layer"], "width_mm": _q3(raw["width_mm"]),
            "polyline_mm": _qpolyline(raw["polyline_mm"]),
            "endpoint_ids": [str(v) for v in eps],
            "constraint_refs": [str(v) for v in refs],
            "state": raw["state"], "source": raw["source"]}


def _norm_via(raw: dict) -> dict:
    _require(isinstance(raw, dict), "ref.vias[*]: 不是对象")
    vid = raw.get("via_id")
    _require(isinstance(vid, str) and vid != "", "via: via_id 缺失")
    where = f"via {vid}"
    for f in ("net_id", "parent_id", "from_layer", "to_layer", "center_mm",
              "drill_mm", "annular_ring_mm"):
        _require(f in raw, f"{where}: 缺字段 {f}")
    _require(isinstance(raw["net_id"], str) and raw["net_id"] != "",
             f"{where}: net_id 非法")
    pid = raw["parent_id"]
    # 放宽（P1b 适配层）：parent_id 允许 None = 独立过孔（真实板上大量无同身份
    # 走线的 via，如 GND 缝合孔；独立过孔是合法铜箔而非缺陷）。给了 parent_id
    # 时其形状校验与 build_manifest/verify 的存在性校验逐字不变。
    _require(pid is None or (isinstance(pid, str) and pid != ""),
             f"{where}: parent_id 必须是 None 或指向存在的 route 的非空字符串")
    for f in ("from_layer", "to_layer"):
        _require(isinstance(raw[f], str) and raw[f] != "",
                 f"{where}: {f} 非法")
    c = raw["center_mm"]
    _require(isinstance(c, (list, tuple)) and len(c) == 2
             and _num(c[0]) and _num(c[1]),
             f"{where}: center_mm 必须是 [x, y] 数值对")
    _require(_num(raw["drill_mm"]) and raw["drill_mm"] > 0,
             f"{where}: drill_mm 必须为正数")
    _require(_num(raw["annular_ring_mm"]) and raw["annular_ring_mm"] >= 0,
             f"{where}: annular_ring_mm 必须 >= 0")
    return {"via_id": vid, "net_id": raw["net_id"], "parent_id": pid,
            "from_layer": raw["from_layer"], "to_layer": raw["to_layer"],
            "center_mm": [_q6(c[0]), _q6(c[1])],
            "drill_mm": _q3(raw["drill_mm"]),
            "annular_ring_mm": _q3(raw["annular_ring_mm"])}


def _norm_relation(raw: dict) -> dict:
    _require(isinstance(raw, dict), "board.relations[*]: 不是对象")
    rid = raw.get("relation_id")
    _require(isinstance(rid, str) and rid != "",
             "relation: relation_id 缺失")
    _require(raw.get("relation_type") in RELATION_TYPES,
             f"relation {rid}: relation_type {raw.get('relation_type')!r} 非法")
    members = raw.get("members")
    _require(isinstance(members, list) and members
             and all(isinstance(v, str) and v for v in members),
             f"relation {rid}: members 必须是非空字符串列表")
    pid = raw.get("parent_id")
    _require(pid is None or isinstance(pid, str),
             f"relation {rid}: parent_id 非法")
    return {"relation_id": rid, "relation_type": raw["relation_type"],
            "members": list(members), "parent_id": pid}


def _norm_zone(raw: dict) -> dict:
    """zone 归一化（v2 新增；见模块 docstring 的 zone 合同）。

    入参（调用方显式传入，扁平）：
    `{zone_id, net_id, layers, outline_mm, outline_kind?, fill_state?,
    fill_sha256?, fill_points?}`。

    fill_state 语义（生成器**不猜**）：未传入 → `"unknown"`；声明 `"fresh"`
    必须同时给出 `fill_sha256` 指纹证据，否则 ValueError —— 无证据不得声称
    填充新鲜（filled_polygon 是 KiCad 派生数据，改轮廓后必然过期）。
    """
    _require(isinstance(raw, dict), "ref.zones[*]: 不是对象")
    zid = raw.get("zone_id")
    _require(isinstance(zid, str) and zid != "", "zone: zone_id 缺失")
    where = f"zone {zid}"
    for f in ("net_id", "layers", "outline_mm"):
        _require(f in raw, f"{where}: 缺字段 {f}")
    _require(isinstance(raw["net_id"], str) and raw["net_id"] != "",
             f"{where}: net_id 非法")
    layers = raw["layers"]
    _require(isinstance(layers, list) and layers
             and all(isinstance(v, str) and v != "" for v in layers),
             f"{where}: layers 必须是非空字符串列表")
    kind = raw.get("outline_kind", ZONE_OUTLINE_KINDS[0])
    _require(kind in ZONE_OUTLINE_KINDS,
             f"{where}: outline_kind {kind!r} 非法（本阶段仅 "
             f"{list(ZONE_OUTLINE_KINDS)}）")
    outline = _qoutline(raw["outline_mm"])
    # fill_state：调用方显式传入；未传入一律 unknown（绝不假定 fresh）
    fs = raw.get("fill_state", "unknown")
    _require(fs in ZONE_FILL_STATES,
             f"{where}: fill_state {fs!r} 非法（{list(ZONE_FILL_STATES)}）")
    sha = raw.get("fill_sha256")
    if sha is not None:
        _require(isinstance(sha, str) and SHA256_RE.match(sha),
                 f"{where}: fill_sha256 不是 64 位小写 hex")
    points = raw.get("fill_points")
    if points is not None:
        _require(isinstance(points, int) and not isinstance(points, bool)
                 and points >= 0,
                 f"{where}: fill_points 必须是非负整数")
    _require(not (fs == "fresh" and sha is None),
             f"{where}: fill_state='fresh' 但未给填充指纹（fill_sha256）："
             "无证据不得声称 fresh（本模块不猜测填充新鲜度）")
    return {"zone_id": zid, "svg_id": f"zone-{zid}", "net_id": raw["net_id"],
            "layers": [str(v) for v in layers], "outline_kind": kind,
            "outline_mm": outline, "fill_state": fs,
            "fill": {"derived": True, "fill_sha256": sha,
                     "fill_points": points}}


def _zones_summary(zones: list) -> dict:
    """zone 的 fill_state 汇总（供 P3b"未重填不得采纳"直接消费）。"""
    counts = {s: sum(1 for z in zones if z.get("fill_state") == s)
              for s in ZONE_FILL_STATES}
    return {
        "count": len(zones),
        "fill_state_counts": counts,
        "not_fresh_zone_ids": sorted(
            (z.get("zone_id") for z in zones
             if z.get("fill_state") != "fresh"), key=str),
        "fill_state_is_caller_declared": True,
        "note": "fill_state 由调用方显式传入，生成器不猜测/不假定 fresh："
                "fresh=轮廓与填充指纹同时给出；stale=轮廓已改而填充未重填；"
                "unknown=无重填证据。消费方（P3b『未重填不得采纳』）应读本"
                " summary 或逐条 zones[*].fill_state",
    }


def build_manifest(board: dict, ref: dict) -> dict:
    """由板快照对象与 ref 路由对象构建 route-manifest（§4）。

    board/ref 是 dict（板快照对象形如 pcbflow 板模型；ref 含 routes/vias
    列表）。纯函数：稳定排序（route/via/relation 按 id）、固定量化
    （几何 6 位、宽度/钻孔 3 位小数）、无时间戳无主机路径。
    """
    _check_board(board)
    _require(isinstance(ref, dict), "ref: 不是对象")
    _require(isinstance(ref.get("routes"), list), "ref.routes: 必须是列表")
    _require(isinstance(ref.get("vias"), list), "ref.vias: 必须是列表")
    sid = board["scenario_id"]
    if ref.get("scenario_id") not in (None, sid):
        raise ValueError("ref.scenario_id 与 board.scenario_id 不一致")
    routes = [_norm_route(r) for r in ref["routes"]]
    _require_unique([r["route_id"] for r in routes], "route_id")
    routes.sort(key=lambda r: r["route_id"])
    vias = [_norm_via(v) for v in ref["vias"]]
    _require_unique([v["via_id"] for v in vias], "via_id")
    vias.sort(key=lambda v: v["via_id"])
    route_ids = {r["route_id"] for r in routes}
    for v in vias:
        if v["parent_id"] is None:
            continue  # None = 独立过孔（见模块 docstring），不指向任何 route
        _require(v["parent_id"] in route_ids,
                 f"via {v['via_id']}: parent_id {v['parent_id']!r} 不存在")
    relations = [_norm_relation(r) for r in (board.get("relations") or [])]
    _require_unique([r["relation_id"] for r in relations], "relation_id")
    relations.sort(key=lambda r: r["relation_id"])
    # v2：zone（可选；缺省 = 空列表，v1 形状的调用方不受影响）
    _require(isinstance(ref.get("zones") or [], list),
             "ref.zones: 必须是列表")
    zones = [_norm_zone(z) for z in (ref.get("zones") or [])]
    _require_unique([z["zone_id"] for z in zones], "zone_id")
    zones.sort(key=lambda z: z["zone_id"])
    rec = legend_record()
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "scenario_id": sid,
        "board_snapshot_sha256": _sha256_of(board),
        "board_bbox_mm": [_q6(v) for v in board["board"]["bbox_mm"]],
        "svg_coordinate_system": SVG_COORD_SYSTEM,
        "legend_version": rec["legend_version"],
        "legend_sha256": rec["legend_sha256"],
        "rules": board.get("rules") or {},
        "relations": relations,
        "routes": routes,
        "vias": vias,
        "zones": zones,
        "zones_summary": _zones_summary(zones),
    }
    # zone 事实哈希（不含填充派生字段）；以 *_sha256 结尾，按 §9 不进
    # payload hash，由 verify 规则 5 强制重算核对（不是"自证"字段）。
    manifest["zones_facts_sha256"] = zone_facts_sha256(zones)
    manifest["manifest_payload_sha256"] = _sha256_of(manifest)
    return manifest


def _style_block() -> str:
    rows = ["  <style>",
            "    .route{fill:none;stroke-linecap:square;stroke-linejoin:miter}"]
    for lt in LINE_TYPES:
        rows.append(f"    .route-{lt}{{stroke:{LEGEND_COLORS[lt]}}}")
    rows.append(f"    .route-candidate{{stroke:{STATE_COLORS['candidate']};"
                "stroke-opacity:0.85}")
    rows.append(f"    .route-conflict{{stroke:{STATE_COLORS['conflict']};"
                "stroke-dasharray:0.6 0.4}")
    rows.append("    .layer-BCu{stroke-dasharray:1.2 0.6}")
    rows.append("    .via{fill:none;stroke:" + VIA_COLOR + ";stroke-width:0.12}")
    rows.append("    .pad{fill:" + PAD_FILL
                + ";stroke:#4B5563;stroke-width:0.08}")
    rows.append("    .keepout{fill:none;stroke:" + KEEPOUT_COLOR
                + ";stroke-width:0.1;stroke-dasharray:0.8 0.4}")
    rows.append("    .board-edge{fill:none;stroke:" + BOARD_EDGE_COLOR
                + ";stroke-width:0.15}")
    rows.append("    .zone-outline{fill:" + ZONE_COLOR + ";fill-opacity:"
                + ZONE_FILL_OPACITY + ";stroke:" + ZONE_COLOR
                + ";stroke-width:0.1;stroke-dasharray:1.0 0.5}")
    rows.append("    .legend-label{font-size:1.4px;fill:#111111}")
    rows.append("  </style>")
    return "\n".join(rows)


def _route_class(route: dict) -> str:
    layer = "F" if route["layer"] == "F.Cu" else "B"
    return (f"route route-{route['line_type']} route-{route['state']}"
            f" layer-{layer}Cu")


def _route_group(route: dict) -> str:
    rid = route["route_id"]
    d = "M " + " L ".join(f"{_fmt6(p[0])} {_fmt6(p[1])}"
                          for p in route["polyline_mm"])
    lines = [
        f'<g id="route-{_esc(rid)}"'
        f' data-object-kind="route_segment"'
        f' data-route-id="{_esc(rid)}"'
        f' data-net-id="{_esc(route["net_id"])}"',
        f'     data-relation-id="{_esc(" ".join(route["relation_ids"]))}"'
        f' data-line-type="{route["line_type"]}"'
        f' data-parent-id="{_esc(route["parent_id"] or "")}"',
        f'     data-layer="{_esc(route["layer"])}"'
        f' data-width-mm="{_fmt3(route["width_mm"])}"'
        f' data-state="{route["state"]}" data-source="{route["source"]}"',
        f'     data-endpoint-start="{_esc(route["endpoint_ids"][0])}"'
        f' data-endpoint-end="{_esc(route["endpoint_ids"][1])}"'
        f' data-constraint-refs='
        f'"{_esc(",".join(route["constraint_refs"]))}">',
        f'  <path id="geom-{_esc(rid)}" d="{d}"'
        f' class="{_route_class(route)}"/>',
        "</g>"]
    return "\n".join(lines)


def _zone_group(zone: dict) -> str:
    """zone 组（v2）：轮廓 path（世界坐标闭合多边形）+ 全套 data-* 机器事实。

    轮廓 path d：首顶点在末尾重复一次（闭合）；除该闭合点外逐点与
    manifest.outline_mm 零容差。真实填充几何不入 SVG（见模块 docstring），
    只画轮廓与其低透明度填充投影（data-fill-projection="outline_only"）。
    """
    zid = zone["zone_id"]
    outline = zone["outline_mm"]
    pts = list(outline) + [outline[0]]  # 闭合（首点重复）
    d = "M " + " L ".join(f"{_fmt6(p[0])} {_fmt6(p[1])}" for p in pts)
    fill = zone.get("fill") or {}
    sha = fill.get("fill_sha256") or ""
    pts_n = fill.get("fill_points")
    points = "" if pts_n is None else str(int(pts_n))
    return "\n".join([
        f'<g id="zone-{_esc(zid)}" data-object-kind="zone"',
        f'     data-zone-id="{_esc(zid)}"'
        f' data-net-id="{_esc(zone["net_id"])}"'
        f' data-layers="{_esc(" ".join(zone["layers"]))}"'
        f' data-outline-kind="{_esc(zone["outline_kind"])}"'
        f' data-fill-state="{_esc(zone["fill_state"])}"',
        f'     data-fill-derived="true" data-fill-projection="outline_only"'
        f' data-fill-sha256="{_esc(sha)}" data-fill-points="{points}">',
        f'  <path id="geom-zone-{_esc(zid)}" d="{d}" class="zone-outline"/>',
        "</g>"])


def _via_circle(via: dict) -> str:
    cx, cy = via["center_mm"]
    r = via["drill_mm"] / 2 + via["annular_ring_mm"]
    return (
        f'<circle id="via-{_esc(via["via_id"])}" data-object-kind="via"'
        f' data-via-id="{_esc(via["via_id"])}"'
        f' data-net-id="{_esc(via["net_id"])}"'
        f' data-parent-id="{_esc(via["parent_id"] or "")}"'
        f' data-from-layer="{_esc(via["from_layer"])}"'
        f' data-to-layer="{_esc(via["to_layer"])}"'
        f' data-drill-mm="{_fmt3(via["drill_mm"])}"'
        f' data-annular-ring-mm="{_fmt3(via["annular_ring_mm"])}"'
        f' cx="{_fmt6(cx)}" cy="{_fmt6(cy)}" r="{_fmt6(r)}"/>')


def _legend_svg(vx0: float, vy0: float, vw: float) -> str:
    rec = legend_record()
    rows = _LEGEND_DRAW_ROWS
    x0 = vx0 + vw - 14.0
    y0 = vy0 + 1.6
    out = [f'<g id="legend" data-legend-version="{LEGEND_VERSION}"'
           f' data-legend-sha256="{rec["legend_sha256"]}">',
           f'  <rect x="{_fmt6(x0 - 0.8)}" y="{_fmt6(y0 - 1.0)}"'
           f' width="13.0" height="{_fmt6(1.9 * len(rows) + 1.2)}"'
           f' fill="#FFFFFF" fill-opacity="0.85"'
           f' stroke="#111111" stroke-width="0.08"/>']
    for i, (kind, label) in enumerate(rows):
        cy = y0 + 1.9 * i
        seg = f'  <g id="legend-item-{kind}">'
        if kind.startswith("line-"):
            key = kind[5:]
            color = STATE_COLORS.get(key) or LEGEND_COLORS.get(key, "#111111")
            seg += (f'<line x1="{_fmt6(x0)}" y1="{_fmt6(cy)}"'
                    f' x2="{_fmt6(x0 + 3.0)}" y2="{_fmt6(cy)}"'
                    f' stroke="{color}" stroke-width="0.4"/>')
        elif kind == "via":
            seg += (f'<circle cx="{_fmt6(x0 + 1.5)}" cy="{_fmt6(cy)}" r="0.5"'
                    f' fill="none" stroke="{VIA_COLOR}" stroke-width="0.16"/>')
        elif kind == "pad":
            seg += (f'<rect x="{_fmt6(x0)}" y="{_fmt6(cy - 0.5)}"'
                    f' width="1.6" height="1.0" fill="{PAD_FILL}"/>')
        elif kind == "zone":
            seg += (f'<rect x="{_fmt6(x0)}" y="{_fmt6(cy - 0.5)}"'
                    f' width="1.6" height="1.0" fill="{ZONE_COLOR}"'
                    f' fill-opacity="{ZONE_FILL_OPACITY}"'
                    f' stroke="{ZONE_COLOR}" stroke-width="0.12"'
                    f' stroke-dasharray="0.5 0.3"/>')
        else:
            seg += (f'<rect x="{_fmt6(x0)}" y="{_fmt6(cy - 0.5)}"'
                    f' width="1.6" height="1.0" fill="none"'
                    f' stroke="{KEEPOUT_COLOR}" stroke-width="0.12"'
                    f' stroke-dasharray="0.5 0.3"/>')
        seg += (f'<text x="{_fmt6(x0 + 4.0)}" y="{_fmt6(cy + 0.5)}"'
                f' class="legend-label">{label}</text></g>')
        out.append(seg)
    out.append("</g>")
    return "\n".join(out)


def build_svg(board: dict, manifest: dict) -> str:
    """由 board + manifest 生成代码化 SVG（§3）。

    根节点合同属性固定顺序；route/via/relation/keepout/pad 的机器事实全部
    在 data-* 属性；path d 使用板 mm 世界坐标。渲染前先复核 manifest 内部
    hash（fail-closed：被篡改的 manifest 拒绝渲染）。纯函数，只返回文本。
    """
    _check_board(board)
    _require(isinstance(manifest, dict), "manifest: 不是对象")
    _require(manifest.get("schema_version") == MANIFEST_SCHEMA_VERSION,
             "manifest.schema_version 非法，拒绝渲染")
    _require(manifest.get("manifest_payload_sha256") == _sha256_of(manifest),
             "manifest 与 manifest_payload_sha256 不一致，拒绝渲染"
             "（fail-closed）")
    bbox = manifest.get("board_bbox_mm")
    _require(isinstance(bbox, list) and len(bbox) == 4
             and all(_num(v) for v in bbox),
             "manifest.board_bbox_mm 非法，拒绝渲染")
    x0, y0, x1, y1 = [float(v) for v in bbox]
    vx0, vy0 = x0 - MARGIN_MM, y0 - MARGIN_MM
    vw, vh = (x1 - x0) + 2.0 * MARGIN_MM, (y1 - y0) + 2.0 * MARGIN_MM
    for r in manifest.get("routes") or []:
        _require(isinstance(r, dict), "manifest.routes[*]: 不是对象")
        for f in ("route_id", "net_id", "relation_ids", "line_type",
                  "parent_id", "layer", "width_mm", "polyline_mm",
                  "endpoint_ids", "constraint_refs", "state", "source"):
            _require(f in r, f"manifest route: 缺字段 {f}")
    for v in manifest.get("vias") or []:
        _require(isinstance(v, dict), "manifest.vias[*]: 不是对象")
        for f in ("via_id", "net_id", "parent_id", "from_layer", "to_layer",
                  "center_mm", "drill_mm", "annular_ring_mm"):
            _require(f in v, f"manifest via: 缺字段 {f}")
    zones = manifest.get("zones") or []
    _require(isinstance(zones, list), "manifest.zones: 必须是列表，拒绝渲染")
    for z in zones:
        _require(isinstance(z, dict), "manifest.zones[*]: 不是对象")
        for f in ("zone_id", "net_id", "layers", "outline_kind",
                  "outline_mm", "fill_state", "fill"):
            _require(f in z, f"manifest zone: 缺字段 {f}")
        _require(isinstance(z["outline_mm"], list) and len(z["outline_mm"]) >= 3,
                 "manifest zone: outline_mm 点数 < 3，拒绝渲染")
        _require(z["outline_kind"] in ZONE_OUTLINE_KINDS,
                 "manifest zone: outline_kind 非法，拒绝渲染")
        _require(z["fill_state"] in ZONE_FILL_STATES,
                 "manifest zone: fill_state 非法，拒绝渲染")
        _require(isinstance(z["fill"], dict)
                 and z["fill"].get("derived") is True,
                 "manifest zone: fill 必须显式标记 derived=true，拒绝渲染")
    # zones_facts_sha256 是 *_sha256 键（不进 payload hash）：显式核对，防止
    # 被篡改的事实哈希被当作可信绑定渲染出去（fail-closed）。
    _require(manifest.get("zones_facts_sha256") == zone_facts_sha256(zones),
             "manifest.zones_facts_sha256 与 zone 事实投影不一致，拒绝渲染"
             "（fail-closed）")

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"'
        f' version="{SVG_VERSION}"'
        f' data-pcbflow-schema="{SVG_SCHEMA}"'
        ' data-board-snapshot-sha256="'
        + _esc(manifest["board_snapshot_sha256"]) + '"'
        ' data-route-manifest-sha256="'
        + _esc(manifest["manifest_payload_sha256"]) + '"'
        ' data-zones-facts-sha256="'
        + _esc(manifest["zones_facts_sha256"]) + '"'
        f' data-coordinate-system="{SVG_COORD_SYSTEM}"'
        f' data-y-axis="{SVG_Y_AXIS}"'
        f' viewBox="{_fmt6(vx0)} {_fmt6(vy0)} {_fmt6(vw)} {_fmt6(vh)}"'
        f' preserveAspectRatio="{PRESERVE_ASPECT_RATIO}">',
        '  <title id="board-title">'
        + _esc(manifest.get("scenario_id", "")) + "</title>"]
    parts.append(_style_block())
    parts.append(
        '  <rect id="board-edge" data-object-kind="board_edge"'
        f' x="{_fmt6(x0)}" y="{_fmt6(y0)}" width="{_fmt6(x1 - x0)}"'
        f' height="{_fmt6(y1 - y0)}" class="board-edge"/>')
    # zone 在 route/via 之下绘制（铺铜是背景铜）；按 zone_id 稳定排序
    for zone in sorted(zones, key=lambda z: str(z.get("zone_id", ""))):
        parts.append("  " + _zone_group(zone).replace("\n", "\n  "))
    keepouts = sorted(board.get("keepouts") or [],
                      key=lambda k: str(k.get("keepout_id", "")))
    for k in keepouts:
        rx0, ry0, rx1, ry1 = [float(v) for v in k["rect_mm"]]
        parts.append(
            f'  <rect id="keepout-{_esc(k["keepout_id"])}"'
            f' data-object-kind="keepout"'
            f' data-keepout-id="{_esc(k["keepout_id"])}"'
            f' data-layers="{_esc(" ".join(k["layers"]))}"'
            f' x="{_fmt6(rx0)}" y="{_fmt6(ry0)}" width="{_fmt6(rx1 - rx0)}"'
            f' height="{_fmt6(ry1 - ry0)}" class="keepout"/>')
    pads = sorted(board.get("pads") or [],
                  key=lambda p: str(p.get("pad_id", "")))
    for p in pads:
        px = float(p["x_mm"]) - float(p["w_mm"]) / 2
        py = float(p["y_mm"]) - float(p["h_mm"]) / 2
        parts.append(
            f'  <rect id="pad-{_esc(p["pad_id"])}" data-object-kind="pad"'
            f' data-pad-id="{_esc(p["pad_id"])}"'
            f' data-net-id="{_esc(p["net_id"])}"'
            f' data-layer="{_esc(p["layer"])}"'
            f' x="{_fmt6(px)}" y="{_fmt6(py)}" width="{_fmt6(p["w_mm"])}"'
            f' height="{_fmt6(p["h_mm"])}" class="pad"/>')
    for r in sorted((board.get("relations") or []),
                    key=lambda r: str(r.get("relation_id", ""))):
        parts.append(
            f'  <g id="relation-{_esc(r["relation_id"])}"'
            f' data-object-kind="route_relation"'
            f' data-relation-id="{_esc(r["relation_id"])}"'
            f' data-relation-type="{r["relation_type"]}"'
            f' data-member-ids="{_esc(" ".join(r["members"]))}"></g>')
    for route in manifest["routes"]:
        parts.append("  " + _route_group(route).replace("\n", "\n  "))
    for via in manifest["vias"]:
        parts.append("  " + _via_circle(via))
    parts.append("  " + _legend_svg(vx0, vy0, vw).replace("\n", "\n  "))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build(board: dict, ref: dict) -> tuple:
    """生成 (svg_text, manifest_dict)。纯函数，无副作用、无 IO。"""
    manifest = build_manifest(board, ref)
    return build_svg(board, manifest), manifest


# ---------------------------------------------------------------- 解析侧

def _safe_local(tag) -> "str | None":
    if not isinstance(tag, str):
        return None
    if tag.startswith("{" + SVG_NS + "}"):
        return tag[len(SVG_NS) + 2:]
    return None


def _dec(text: str, pattern: "re.Pattern", where: str) -> float:
    if not isinstance(text, str) or not pattern.match(text):
        raise _ContractError(f"{where}: 数值 {text!r} 不是合同定点小数")
    return float(Decimal(text))


def _dec6(text: str, where: str) -> float:
    return _dec(text, DEC6_RE, where)


def _dec3(text: str, where: str) -> float:
    return _dec(text, DEC3_RE, where)


def _split_ids(text: str, where: str) -> list:
    if text == "":
        return []
    ids = text.split(" ")
    if any(i == "" for i in ids):
        raise _ContractError(f"{where}: id 列表 {text!r} 含空 token")
    return ids


def _split_csv(text: str, where: str) -> list:
    if text == "":
        return []
    ids = text.split(",")
    if any(i == "" for i in ids):
        raise _ContractError(f"{where}: csv 列表 {text!r} 含空 token")
    return ids


def _parse_path_d(d: str, where: str) -> list:
    """合同 path d：'M x y' 后跟若干 'L x y'，坐标一律 6 位定点小数。"""
    tokens = d.split(" ")
    if len(tokens) < 6 or len(tokens) % 3 != 0:
        raise _ContractError(f"{where}: d 串 token 数不合法: {d!r}")
    pts = []
    for i in range(0, len(tokens), 3):
        cmd = tokens[i]
        if i == 0:
            if cmd != "M":
                raise _ContractError(
                    f"{where}: d 首命令必须是 M，实际 {cmd!r}")
        elif cmd != "L":
            raise _ContractError(
                f"{where}: d 第 {i // 3 + 1} 命令必须是 L，实际 {cmd!r}")
        x = _dec6(tokens[i + 1], f"{where}.x[{i // 3}]")
        y = _dec6(tokens[i + 2], f"{where}.y[{i // 3}]")
        pts.append([x, y])
    return pts


def _parse_closed_path_d(d: str, where: str) -> list:
    """合同 zone 轮廓 path d：'M p0' 后跟 'L pi'，末点必须与首点逐位相同。

    返回**去掉重复闭合点**的轮廓顶点（与 manifest.outline_mm 同长，可零容差
    逐点比较）。至少 3 个不同顶点（d 至少 4 组坐标）。
    """
    pts = _parse_path_d(d, where)
    if len(pts) < 4:
        raise _ContractError(
            f"{where}: 闭合多边形至少 4 组坐标（3 个不同顶点 + 重复首点），"
            f"实际 {len(pts)} 组")
    if pts[0] != pts[-1]:
        raise _ContractError(
            f"{where}: zone 轮廓必须是闭合多边形（末点必须与首点逐位相同）")
    return pts[:-1]


def _parse_viewbox(text: str) -> list:
    parts = text.split(" ")
    if len(parts) != 4:
        raise _ContractError(f"viewBox: 必须 4 个 token，实际 {text!r}")
    vals = [_dec6(p, f"viewBox[{i}]") for i, p in enumerate(parts)]
    if vals[2] <= 0 or vals[3] <= 0:
        raise _ContractError(f"viewBox: 宽高必须为正，实际 {text!r}")
    return vals


def parse_svg_polyline(svg_text: str, svg_id: str) -> list:
    """从 SVG 中定位 <g id="svg_id">（route 组），解析其唯一 path 的 d 属性。

    返回板 mm 世界坐标折线 [[x, y], ...]（本模块 viewBox 采用世界坐标约定，
    path d 即板 mm）。与 manifest.polyline_mm 可做零容差 round-trip：
    两边各自量化到 6 位小数后必须逐点相等。结构不合法抛 _ContractError
    （ValueError 子类，fail-closed）。
    """
    _require(isinstance(svg_text, str), "svg_text: 不是字符串")
    _require(isinstance(svg_id, str) and svg_id != "",
             "svg_id: 必须是非空字符串")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise _ContractError(f"SVG: XML 语法错误: {exc}") from exc
    hits = [el for el in root.iter()
            if isinstance(el.tag, str) and el.attrib.get("id") == svg_id]
    if not hits:
        raise _ContractError(f"SVG: 找不到 id={svg_id!r} 的元素")
    if len(hits) > 1:
        raise _ContractError(f"SVG: id={svg_id!r} 重复出现 {len(hits)} 次")
    el = hits[0]
    if (_safe_local(el.tag) != "g"
            or el.attrib.get("data-object-kind") != "route_segment"):
        raise _ContractError(
            f"{svg_id!r}: 不是 route 组"
            "（期望 <g data-object-kind=route_segment>）")
    kids = list(el)
    paths = [c for c in kids if c.tag == "{" + SVG_NS + "}path"]
    if len(kids) != 1 or len(paths) != 1:
        raise _ContractError(
            f"{svg_id!r}: route 组必须恰含 1 个 path 子元素")
    return _parse_path_d(paths[0].attrib.get("d", ""), f"{svg_id}.path.d")


def parse_svg_zone_outline(svg_text: str, zone_id: str) -> list:
    """从 SVG 中定位 <g id="zone-zone_id"> 并解析其唯一轮廓 path 的 d。

    返回板 mm 世界坐标轮廓顶点 [[x, y], ...]（**不含**重复的闭合首点），与
    manifest 中该 zone 的 `outline_mm` 可做零容差 round-trip。结构不合法
    （找不到 / id 重复 / 非 zone 组 / path 数 ≠ 1 / 非闭合多边形）抛
    _ContractError（ValueError 子类，fail-closed）。
    """
    _require(isinstance(svg_text, str), "svg_text: 不是字符串")
    _require(isinstance(zone_id, str) and zone_id != "",
             "zone_id: 必须是非空字符串")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise _ContractError(f"SVG: XML 语法错误: {exc}") from exc
    el_id = f"zone-{zone_id}"
    hits = [el for el in root.iter()
            if isinstance(el.tag, str) and el.attrib.get("id") == el_id]
    if not hits:
        raise _ContractError(f"SVG: 找不到 id={el_id!r} 的元素")
    if len(hits) > 1:
        raise _ContractError(f"SVG: id={el_id!r} 重复出现 {len(hits)} 次")
    el = hits[0]
    if (_safe_local(el.tag) != "g"
            or el.attrib.get("data-object-kind") != "zone"):
        raise _ContractError(
            f"{el_id!r}: 不是 zone 组（期望 <g data-object-kind=zone>）")
    kids = list(el)
    paths = [c for c in kids
             if isinstance(c.tag, str) and c.tag == "{" + SVG_NS + "}path"]
    if len(kids) != 1 or len(paths) != 1:
        raise _ContractError(f"{el_id!r}: zone 组必须恰含 1 个轮廓 path 子元素")
    return _parse_closed_path_d(paths[0].attrib.get("d", ""),
                                f"{el_id}.path.d")


# ---------------------------------------------------------------- verify 侧

def _root_contract_violations(root) -> list:
    out = []
    if _safe_local(root.tag) != "svg":
        return [f"根标签必须是 {{{SVG_NS}}}svg，实际 {root.tag!r}"]
    a = root.attrib
    if a.get("version") != SVG_VERSION:
        out.append(f"svg@version 期望 {SVG_VERSION!r}，"
                   f"实际 {a.get('version')!r}")
    if a.get("data-pcbflow-schema") != SVG_SCHEMA:
        out.append(f"svg@data-pcbflow-schema 期望 {SVG_SCHEMA!r}，"
                   f"实际 {a.get('data-pcbflow-schema')!r}")
    if a.get("data-coordinate-system") != SVG_COORD_SYSTEM:
        out.append(f"svg@data-coordinate-system 期望 "
                   f"{SVG_COORD_SYSTEM!r}，"
                   f"实际 {a.get('data-coordinate-system')!r}")
    if a.get("data-y-axis") != SVG_Y_AXIS:
        out.append(f"svg@data-y-axis 期望 {SVG_Y_AXIS!r}，"
                   f"实际 {a.get('data-y-axis')!r}")
    if a.get("preserveAspectRatio") != PRESERVE_ASPECT_RATIO:
        out.append(f"svg@preserveAspectRatio 期望 "
                   f"{PRESERVE_ASPECT_RATIO!r}，"
                   f"实际 {a.get('preserveAspectRatio')!r}")
    for name in ("data-board-snapshot-sha256", "data-route-manifest-sha256"):
        v = a.get(name, "")
        if not SHA256_RE.match(v):
            out.append(f"svg@{name} 不是 64 位小写 hex: {v!r}")
    try:
        _parse_viewbox(a.get("viewBox", ""))
    except _ContractError as exc:
        out.append(str(exc))
    return out


def _collect_route(el, bad) -> "dict | None":
    attrs = el.attrib
    for name in SVG_ROUTE_ATTRS:
        if name not in attrs:
            bad(f"route 组 {attrs.get('id', '?')}: 缺必填属性 {name}")
            return None
    rid = attrs["data-route-id"]
    if rid == "":
        bad(f"route 组 {attrs.get('id', '?')}: data-route-id 为空")
        return None
    where = f"route {rid}"
    gid = attrs.get("id", "")
    if gid != f"route-{rid}":
        bad(f"{where}: 组 id 期望 'route-{rid}'，实际 {gid!r}")
    if attrs["data-line-type"] not in LINE_TYPES:
        bad(f"{where}: 未知 data-line-type {attrs['data-line-type']!r}")
    if attrs["data-state"] not in ROUTE_STATES:
        bad(f"{where}: 未知 data-state {attrs['data-state']!r}")
    if attrs["data-source"] not in ROUTE_SOURCES:
        bad(f"{where}: 未知 data-source {attrs['data-source']!r}")
    if attrs["data-endpoint-start"] == "" or attrs["data-endpoint-end"] == "":
        bad(f"{where}: endpoint 为空")
    width = None
    try:
        width = _dec3(attrs["data-width-mm"], f"{where}.data-width-mm")
        if width <= 0:
            bad(f"{where}: data-width-mm 必须为正")
    except _ContractError as exc:
        bad(str(exc))
    rel_ids = None
    try:
        rel_ids = _split_ids(attrs["data-relation-id"],
                             f"{where}.data-relation-id")
    except _ContractError as exc:
        bad(str(exc))
    refs = None
    try:
        refs = _split_csv(attrs["data-constraint-refs"],
                          f"{where}.data-constraint-refs")
        for ref in refs:
            if not CONSTRAINT_REF_RE.match(ref):
                bad(f"{where}: constraint ref {ref!r} 形状不符")
    except _ContractError as exc:
        bad(str(exc))
    polyline = None
    kids = list(el)
    paths = [c for c in kids
             if isinstance(c.tag, str) and c.tag == "{" + SVG_NS + "}path"]
    if len(kids) != 1 or len(paths) != 1:
        bad(f"{where}: route 组必须恰含 1 个 path 子元素")
    else:
        p_attrs = paths[0].attrib
        path_id = p_attrs.get("id", "")
        if path_id != f"geom-{rid}":
            bad(f"{where}: path id 期望 'geom-{rid}'，实际 {path_id!r}")
        try:
            polyline = _parse_path_d(p_attrs.get("d", ""), f"{where}.path.d")
        except _ContractError as exc:
            bad(str(exc))
    return {"route_id": rid, "svg_id": gid,
            "net_id": attrs["data-net-id"], "relation_ids": rel_ids,
            "line_type": attrs["data-line-type"],
            "parent_id": attrs["data-parent-id"] or None,
            "layer": attrs["data-layer"], "width_mm": width,
            "state": attrs["data-state"], "source": attrs["data-source"],
            "endpoint_ids": [attrs["data-endpoint-start"],
                             attrs["data-endpoint-end"]],
            "constraint_refs": refs, "polyline_mm": polyline}


def _collect_via(el, bad) -> "dict | None":
    attrs = el.attrib
    for name in SVG_VIA_ATTRS:
        if name not in attrs:
            bad(f"via 组 {attrs.get('id', '?')}: 缺必填属性 {name}")
            return None
    vid = attrs["data-via-id"]
    if vid == "":
        bad(f"via 组 {attrs.get('id', '?')}: data-via-id 为空")
        return None
    where = f"via {vid}"
    gid = attrs.get("id", "")
    if gid != f"via-{vid}":
        bad(f"{where}: 元素 id 期望 'via-{vid}'，实际 {gid!r}")
    # data-parent-id="" = 独立过孔（parent_id=null 的合法表达，见模块 docstring）；
    # 非空时其存在性由 _structure_violations 核对。
    drill = ring = None
    try:
        drill = _dec3(attrs["data-drill-mm"], f"{where}.data-drill-mm")
        ring = _dec3(attrs["data-annular-ring-mm"],
                     f"{where}.data-annular-ring-mm")
        if drill <= 0 or ring < 0:
            bad(f"{where}: drill/ring 数值非法")
    except _ContractError as exc:
        bad(str(exc))
    center = None
    try:
        center = [_dec6(attrs.get("cx", ""), f"{where}.cx"),
                  _dec6(attrs.get("cy", ""), f"{where}.cy")]
    except _ContractError as exc:
        bad(str(exc))
    return {"via_id": vid, "svg_id": gid, "net_id": attrs["data-net-id"],
            "parent_id": attrs["data-parent-id"] or None,
            "from_layer": attrs["data-from-layer"],
            "to_layer": attrs["data-to-layer"],
            "drill_mm": drill, "annular_ring_mm": ring,
            "center_mm": center}


def _collect_zone(el, bad) -> "dict | None":
    """收集 zone 组（v2）：必填 data-*、派生标记、闭合轮廓 path。"""
    attrs = el.attrib
    for name in SVG_ZONE_ATTRS:
        if name not in attrs:
            bad(f"zone 组 {attrs.get('id', '?')}: 缺必填属性 {name}")
            return None
    zid = attrs["data-zone-id"]
    if zid == "":
        bad(f"zone 组 {attrs.get('id', '?')}: data-zone-id 为空")
        return None
    where = f"zone {zid}"
    gid = attrs.get("id", "")
    if gid != f"zone-{zid}":
        bad(f"{where}: 组 id 期望 'zone-{zid}'，实际 {gid!r}")
    if attrs["data-net-id"] == "":
        bad(f"{where}: data-net-id 为空（net 身份不可缺省）")
    if attrs["data-outline-kind"] not in ZONE_OUTLINE_KINDS:
        bad(f"{where}: 未知 data-outline-kind "
            f"{attrs['data-outline-kind']!r}")
    if attrs["data-fill-state"] not in ZONE_FILL_STATES:
        bad(f"{where}: 未知 data-fill-state {attrs['data-fill-state']!r}")
    # 派生填充数据必须显式标记（不得与事实混为一谈）
    if attrs.get("data-fill-derived") != "true":
        bad(f"{where}: 派生填充数据必须显式标记 "
            "data-fill-derived=\"true\"（派生数据不得混入事实）")
    fsha = attrs.get("data-fill-sha256", "")
    if fsha != "" and not SHA256_RE.match(fsha):
        bad(f"{where}: data-fill-sha256 不是 64 位小写 hex: {fsha!r}")
    fpoints = attrs.get("data-fill-points", "")
    if fpoints != "" and not re.fullmatch(r"\d+", fpoints):
        bad(f"{where}: data-fill-points 必须是非负十进制整数: {fpoints!r}")
    layers = None
    try:
        layers = _split_ids(attrs["data-layers"], f"{where}.data-layers")
        if not layers:
            bad(f"{where}: data-layers 不能为空")
    except _ContractError as exc:
        bad(str(exc))
    outline = None
    kids = list(el)
    paths = [c for c in kids
             if isinstance(c.tag, str) and c.tag == "{" + SVG_NS + "}path"]
    if len(kids) != 1 or len(paths) != 1:
        bad(f"{where}: zone 组必须恰含 1 个轮廓 path 子元素")
    else:
        p_attrs = paths[0].attrib
        path_id = p_attrs.get("id", "")
        if path_id != f"geom-zone-{zid}":
            bad(f"{where}: path id 期望 'geom-zone-{zid}'，实际 {path_id!r}")
        try:
            outline = _parse_closed_path_d(p_attrs.get("d", ""),
                                           f"{where}.path.d")
        except _ContractError as exc:
            bad(str(exc))
    return {"zone_id": zid, "svg_id": gid,
            "net_id": attrs["data-net-id"], "layers": layers,
            "outline_kind": attrs["data-outline-kind"],
            "fill_state": attrs["data-fill-state"],
            "fill_derived": attrs.get("data-fill-derived"),
            "fill_sha256": fsha, "fill_points": fpoints,
            "outline": outline}


def _collect_relation(el, bad) -> "dict | None":
    attrs = el.attrib
    for name in SVG_RELATION_ATTRS:
        if name not in attrs:
            bad(f"relation 组 {attrs.get('id', '?')}: 缺必填属性 {name}")
            return None
    rid = attrs["data-relation-id"]
    if rid == "":
        bad(f"relation 组 {attrs.get('id', '?')}: data-relation-id 为空")
        return None
    where = f"relation {rid}"
    gid = attrs.get("id", "")
    if gid != f"relation-{rid}":
        bad(f"{where}: 组 id 期望 'relation-{rid}'，实际 {gid!r}")
    if attrs["data-relation-type"] not in RELATION_TYPES:
        bad(f"{where}: 未知 data-relation-type "
            f"{attrs['data-relation-type']!r}")
    members = None
    try:
        members = _split_ids(attrs["data-member-ids"],
                             f"{where}.data-member-ids")
        if not members:
            bad(f"{where}: relation 成员不能为空")
    except _ContractError as exc:
        bad(str(exc))
    return {"relation_id": rid, "svg_id": gid,
            "relation_type": attrs["data-relation-type"],
            "member_ids": members}


def _collect_svg_objects(root, bad):
    """遍历整棵树收集 route/via/relation/zone/pad/图例；返回六元组。"""
    routes, vias, rels, pads, zones = {}, {}, {}, {}, {}
    legend = None
    seen_elem_ids = set()
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        tag = _safe_local(el.tag)
        if tag is None:
            bad(f"标签 {el.tag!r} 不在 SVG 命名空间 {{{SVG_NS}}}")
            continue
        attrs = el.attrib
        eid = attrs.get("id")
        if eid is not None:
            if eid in seen_elem_ids:
                bad(f"SVG: 元素 id 重复 {eid!r}")
            seen_elem_ids.add(eid)
        kind = attrs.get("data-object-kind")
        if kind is not None and kind not in SVG_OBJECT_KINDS:
            bad(f"{tag}#{eid or ''}: 未知 data-object-kind {kind!r}")
        if kind == "route_segment":
            fr = _collect_route(el, bad)
            if fr is not None:
                if fr["route_id"] in routes:
                    bad(f"SVG: route_id 重复 {fr['route_id']!r}")
                else:
                    routes[fr["route_id"]] = fr
        elif kind == "via":
            fv = _collect_via(el, bad)
            if fv is not None:
                if fv["via_id"] in vias:
                    bad(f"SVG: via_id 重复 {fv['via_id']!r}")
                else:
                    vias[fv["via_id"]] = fv
        elif kind == "zone":
            fz = _collect_zone(el, bad)
            if fz is not None:
                if fz["zone_id"] in zones:
                    bad(f"SVG: zone_id 重复 {fz['zone_id']!r}")
                else:
                    zones[fz["zone_id"]] = fz
        elif kind == "route_relation":
            fr = _collect_relation(el, bad)
            if fr is not None:
                if fr["relation_id"] in rels:
                    bad(f"SVG: relation_id 重复 {fr['relation_id']!r}")
                else:
                    rels[fr["relation_id"]] = fr
        elif kind == "pad":
            for name in ("data-pad-id", "data-net-id", "data-layer"):
                if name not in attrs:
                    bad(f"pad {eid or '?'}: 缺必填属性 {name}")
                    break
            else:
                pid = attrs["data-pad-id"]
                if pid in pads:
                    bad(f"SVG: pad_id 重复 {pid!r}")
                else:
                    pads[pid] = {"pad_id": pid,
                                 "net_id": attrs["data-net-id"],
                                 "layer": attrs["data-layer"]}
        if attrs.get("data-legend-version") is not None:
            if legend is not None:
                bad("SVG: 图例组重复（多个 data-legend-version）")
            legend = {"legend_version": attrs.get("data-legend-version"),
                      "legend_sha256": attrs.get("data-legend-sha256")}
    return routes, vias, rels, pads, zones, legend


def _identity_violations(svg_routes, svg_vias, svg_rels, manifest) -> list:
    """§4 规则 1：svg_id/route_id/net_id 与 manifest entry 一一对应。"""
    out = []
    man_routes = manifest.get("routes")
    man_vias = manifest.get("vias")
    man_rels = manifest.get("relations")
    for name, val in (("routes", man_routes), ("vias", man_vias),
                      ("relations", man_rels)):
        if not isinstance(val, list):
            out.append(f"manifest.{name}: 必须是列表")
    man_routes = man_routes if isinstance(man_routes, list) else []
    man_vias = man_vias if isinstance(man_vias, list) else []
    man_rels = man_rels if isinstance(man_rels, list) else []

    m_routes = {}
    for i, e in enumerate(man_routes):
        if not isinstance(e, dict):
            out.append(f"manifest.routes[{i}]: 不是对象")
            continue
        rid = e.get("route_id")
        if not isinstance(rid, str) or rid == "":
            out.append(f"manifest.routes[{i}]: route_id 缺失")
            continue
        if rid in m_routes:
            out.append(f"manifest: route_id 重复 {rid!r}")
        m_routes[rid] = e
    only_svg = sorted(set(svg_routes) - set(m_routes))
    only_man = sorted(set(m_routes) - set(svg_routes))
    if only_svg:
        out.append(f"route 仅在 SVG 中: {only_svg}")
    if only_man:
        out.append(f"route 仅在 manifest 中: {only_man}")
    for rid in sorted(set(svg_routes) & set(m_routes)):
        fr, mr = svg_routes[rid], m_routes[rid]
        if mr.get("svg_id") != f"route-{rid}":
            out.append(f"route {rid}: manifest.svg_id 期望 "
                       f"'route-{rid}'，实际 {mr.get('svg_id')!r}")
        if fr["svg_id"] != mr.get("svg_id"):
            out.append(f"route {rid}.svg_id: svg={fr['svg_id']!r} "
                       f"manifest={mr.get('svg_id')!r}")
        if fr["net_id"] != mr.get("net_id"):
            out.append(f"route {rid}.net_id: svg={fr['net_id']!r} "
                       f"manifest={mr.get('net_id')!r}")

    m_vias = {}
    for i, e in enumerate(man_vias):
        if not isinstance(e, dict):
            out.append(f"manifest.vias[{i}]: 不是对象")
            continue
        vid = e.get("via_id")
        if not isinstance(vid, str) or vid == "":
            out.append(f"manifest.vias[{i}]: via_id 缺失")
            continue
        if vid in m_vias:
            out.append(f"manifest: via_id 重复 {vid!r}")
        m_vias[vid] = e
    if set(svg_vias) != set(m_vias):
        out.append(f"via 集合不等: svg_only="
                   f"{sorted(set(svg_vias) - set(m_vias))} manifest_only="
                   f"{sorted(set(m_vias) - set(svg_vias))}")
    for vid in sorted(set(svg_vias) & set(m_vias)):
        if svg_vias[vid]["net_id"] != m_vias[vid].get("net_id"):
            out.append(f"via {vid}.net_id: svg="
                       f"{svg_vias[vid]['net_id']!r} manifest="
                       f"{m_vias[vid].get('net_id')!r}")

    m_rels = {}
    for i, e in enumerate(man_rels):
        if not isinstance(e, dict):
            out.append(f"manifest.relations[{i}]: 不是对象")
            continue
        rid = e.get("relation_id")
        if not isinstance(rid, str) or rid == "":
            out.append(f"manifest.relations[{i}]: relation_id 缺失")
            continue
        if rid in m_rels:
            out.append(f"manifest: relation_id 重复 {rid!r}")
        m_rels[rid] = e
    if set(svg_rels) != set(m_rels):
        out.append(f"relation 集合不等: svg_only="
                   f"{sorted(set(svg_rels) - set(m_rels))} manifest_only="
                   f"{sorted(set(m_rels) - set(svg_rels))}")
    return out


def _zone_identity_violations(svg_zones, manifest) -> list:
    """§4 规则 1（zone）：svg_id/zone_id/net_id/layers 与 manifest 一一对应。"""
    out = []
    man = manifest.get("zones")
    if not isinstance(man, list):
        out.append("manifest.zones: 必须是列表（v2 合同）")
        man = []
    m = {}
    for i, e in enumerate(man):
        if not isinstance(e, dict):
            out.append(f"manifest.zones[{i}]: 不是对象")
            continue
        zid = e.get("zone_id")
        if not isinstance(zid, str) or zid == "":
            out.append(f"manifest.zones[{i}]: zone_id 缺失")
            continue
        if zid in m:
            out.append(f"manifest: zone_id 重复 {zid!r}")
        m[zid] = e
    only_svg = sorted(set(svg_zones) - set(m))
    only_man = sorted(set(m) - set(svg_zones))
    if only_svg:
        out.append(f"zone 仅在 SVG 中: {only_svg}")
    if only_man:
        out.append(f"zone 仅在 manifest 中: {only_man}")
    for zid in sorted(set(svg_zones) & set(m)):
        fz, mz = svg_zones[zid], m[zid]
        if mz.get("svg_id") != f"zone-{zid}":
            out.append(f"zone {zid}: manifest.svg_id 期望 'zone-{zid}'，"
                       f"实际 {mz.get('svg_id')!r}")
        if fz["svg_id"] != mz.get("svg_id"):
            out.append(f"zone {zid}.svg_id: svg={fz['svg_id']!r} "
                       f"manifest={mz.get('svg_id')!r}")
        if fz["net_id"] != mz.get("net_id"):
            out.append(f"zone {zid}.net_id: svg={fz['net_id']!r} "
                       f"manifest={mz.get('net_id')!r}")
        if fz["layers"] is not None and fz["layers"] != mz.get("layers"):
            out.append(f"zone {zid}.layers: svg={fz['layers']!r} "
                       f"manifest={mz.get('layers')!r}")
    return out


def _zone_geometry_violations(svg_zones, manifest) -> list:
    """§4 规则 2（zone）：轮廓 path 解析后与 outline_mm 零容差（含点数 ≥3）。"""
    out = []
    m = _index(manifest.get("zones"), "zone_id")
    for zid in sorted(svg_zones):
        fz = svg_zones[zid]
        mz = m.get(zid)
        if mz is None:
            continue  # 身份违规已另行报告
        mo = mz.get("outline_mm")
        if not isinstance(mo, list) or len(mo) < 3:
            out.append(f"zone {zid}: manifest.outline_mm 点数 < 3"
                       "（多边形轮廓非法）")
            continue
        bad_shape = False
        mpq = []
        for i, p in enumerate(mo):
            if not (isinstance(p, (list, tuple)) and len(p) == 2
                    and _num(p[0]) and _num(p[1])):
                out.append(f"zone {zid}: manifest.outline_mm[{i}] 形状非法")
                bad_shape = True
                break
            mpq.append([_q6(p[0]), _q6(p[1])])
        if bad_shape or fz["outline"] is None:
            continue
        spo = [[_q6(p[0]), _q6(p[1])] for p in fz["outline"]]
        if spo != mpq:
            out.append(f"zone {zid}: SVG 轮廓坐标与 outline_mm 不一致"
                       "（零容差）")
    return out


def _zone_field_violations(svg_zones, manifest) -> list:
    """§4 规则 3/4（zone）：字段一致 + 派生标记 + fill_state 一致。"""
    out = []
    m = _index(manifest.get("zones"), "zone_id")
    for zid in sorted(set(svg_zones) & set(m)):
        fz, mz = svg_zones[zid], m[zid]
        mfs = mz.get("fill_state")
        if mfs not in ZONE_FILL_STATES:
            out.append(f"zone {zid}.fill_state: manifest 非法值 {mfs!r}")
        else:
            if fz["fill_state"] != mfs:
                out.append(f"zone {zid}.fill_state: svg={fz['fill_state']!r} "
                           f"manifest={mfs!r}")
        if fz["outline_kind"] != mz.get("outline_kind"):
            out.append(f"zone {zid}.outline_kind: svg={fz['outline_kind']!r} "
                       f"manifest={mz.get('outline_kind')!r}")
        fill = mz.get("fill")
        if not isinstance(fill, dict) or fill.get("derived") is not True:
            out.append(f"zone {zid}: manifest.fill 必须显式标记 derived=true"
                       "（派生数据不得混入事实字段）")
            continue
        # 派生填充指纹在 SVG 上的投影也必须与 manifest 一致（零容差字符串）
        msha = fill.get("fill_sha256") or ""
        mpoints = ("" if fill.get("fill_points") is None
                   else str(int(fill["fill_points"])))
        if fz["fill_sha256"] != msha:
            out.append(f"zone {zid}.fill_sha256: svg={fz['fill_sha256']!r} "
                       f"manifest={msha!r}")
        if fz["fill_points"] != mpoints:
            out.append(f"zone {zid}.fill_points: svg={fz['fill_points']!r} "
                       f"manifest={mpoints!r}")
    return out


def _geometry_violations(svg_routes, svg_vias, root, manifest) -> list:
    """§4 规则 2：SVG path 坐标解析后与 polyline_mm 零容差一致。"""
    out = []
    a = root.attrib
    bbox = manifest.get("board_bbox_mm")
    if not (isinstance(bbox, list) and len(bbox) == 4
            and all(_num(v) for v in bbox)):
        out.append("manifest.board_bbox_mm: 缺失或形状非法")
    else:
        try:
            vb = _parse_viewbox(a.get("viewBox", ""))
            x0, y0, x1, y1 = [float(v) for v in bbox]
            exp = [_q6(x0 - MARGIN_MM), _q6(y0 - MARGIN_MM),
                   _q6((x1 - x0) + 2 * MARGIN_MM),
                   _q6((y1 - y0) + 2 * MARGIN_MM)]
            if [_q6(v) for v in vb] != exp:
                out.append(f"viewBox {a.get('viewBox')!r} != "
                           f"board_bbox_mm+2M 期望 {exp}")
        except _ContractError as exc:
            out.append(str(exc))

    m_routes = _index(manifest.get("routes"), "route_id")
    for rid in sorted(svg_routes):
        fr = svg_routes[rid]
        mr = m_routes.get(rid)
        if mr is None or fr["polyline_mm"] is None:
            continue  # 身份/解析违规已另行报告
        mp = mr.get("polyline_mm")
        if not (isinstance(mp, list) and len(mp) >= 2):
            out.append(f"route {rid}: manifest.polyline_mm 形状非法")
            continue
        bad_shape = False
        mpq = []
        for i, p in enumerate(mp):
            if not (isinstance(p, (list, tuple)) and len(p) == 2
                    and _num(p[0]) and _num(p[1])):
                out.append(f"route {rid}: manifest.polyline_mm[{i}] 形状非法")
                bad_shape = True
                break
            mpq.append([_q6(p[0]), _q6(p[1])])
        if bad_shape:
            continue
        spq = [[_q6(p[0]), _q6(p[1])] for p in fr["polyline_mm"]]
        if spq != mpq:
            out.append(f"route {rid}: SVG path 坐标与 polyline_mm 不一致"
                       f"（零容差）")
    m_vias = _index(manifest.get("vias"), "via_id")
    for vid in sorted(svg_vias):
        fv = svg_vias[vid]
        mv = m_vias.get(vid)
        if mv is None or fv["center_mm"] is None:
            continue
        c = mv.get("center_mm")
        if not (isinstance(c, (list, tuple)) and len(c) == 2
                and _num(c[0]) and _num(c[1])):
            out.append(f"via {vid}: manifest.center_mm 形状非法")
            continue
        if [_q6(fv["center_mm"][0]), _q6(fv["center_mm"][1])] \
                != [_q6(c[0]), _q6(c[1])]:
            out.append(f"via {vid}: SVG cx/cy 与 center_mm 不一致（零容差）")
    return out


def _field_violations(svg_routes, svg_vias, svg_rels, manifest) -> list:
    """§4 规则 3：SVG 声明的 layer/width/state/relation 等与 manifest 一致。"""
    out = []
    m_routes = _index(manifest.get("routes"), "route_id")
    for rid in sorted(set(svg_routes) & set(m_routes)):
        fr, mr = svg_routes[rid], m_routes[rid]
        for field in ("line_type", "layer", "state", "source"):
            if fr[field] != mr.get(field):
                out.append(f"route {rid}.{field}: svg={fr[field]!r} "
                           f"manifest={mr.get(field)!r}")
        if fr["parent_id"] != mr.get("parent_id"):
            out.append(f"route {rid}.parent_id: svg={fr['parent_id']!r} "
                       f"manifest={mr.get('parent_id')!r}")
        if fr["relation_ids"] is not None \
                and fr["relation_ids"] != mr.get("relation_ids"):
            out.append(f"route {rid}.relation_ids: svg="
                       f"{fr['relation_ids']!r} "
                       f"manifest={mr.get('relation_ids')!r}")
        if fr["endpoint_ids"] != mr.get("endpoint_ids"):
            out.append(f"route {rid}.endpoint_ids: svg="
                       f"{fr['endpoint_ids']!r} "
                       f"manifest={mr.get('endpoint_ids')!r}")
        if fr["constraint_refs"] is not None \
                and fr["constraint_refs"] != mr.get("constraint_refs"):
            out.append(f"route {rid}.constraint_refs: svg="
                       f"{fr['constraint_refs']!r} "
                       f"manifest={mr.get('constraint_refs')!r}")
        mw = mr.get("width_mm")
        if not _num(mw):
            out.append(f"route {rid}.width_mm: manifest 非数值 {mw!r}")
        elif fr["width_mm"] is not None and _q3(fr["width_mm"]) != _q3(mw):
            out.append(f"route {rid}.width_mm: svg={fr['width_mm']} "
                       f"manifest={mw}")
    m_vias = _index(manifest.get("vias"), "via_id")
    for vid in sorted(set(svg_vias) & set(m_vias)):
        fv, mv = svg_vias[vid], m_vias[vid]
        for field in ("parent_id", "from_layer", "to_layer"):
            if fv[field] != mv.get(field):
                out.append(f"via {vid}.{field}: svg={fv[field]!r} "
                           f"manifest={mv.get(field)!r}")
        for field in ("drill_mm", "annular_ring_mm"):
            mvv = mv.get(field)
            if not _num(mvv):
                out.append(f"via {vid}.{field}: manifest 非数值 {mvv!r}")
            elif fv[field] is not None and _q3(fv[field]) != _q3(mvv):
                out.append(f"via {vid}.{field}: svg={fv[field]} "
                           f"manifest={mvv}")
    m_rels = _index(manifest.get("relations"), "relation_id")
    for rid in sorted(set(svg_rels) & set(m_rels)):
        fr, mr = svg_rels[rid], m_rels[rid]
        if fr["relation_type"] != mr.get("relation_type"):
            out.append(f"relation {rid}.relation_type: svg="
                       f"{fr['relation_type']!r} "
                       f"manifest={mr.get('relation_type')!r}")
        if fr["member_ids"] is not None \
                and fr["member_ids"] != mr.get("members"):
            out.append(f"relation {rid}.members: svg={fr['member_ids']!r} "
                       f"manifest={mr.get('members')!r}")
    return out


def _structure_violations(svg_routes, svg_rels, manifest, net_registry) -> list:
    """身份结构：parent 存在且无环、via parent 指向 route（None=独立过孔除外）、
    relation 成员是已注册 net（机器身份检查，与视觉无关）。"""
    out = []
    m_routes = _index(manifest.get("routes"), "route_id")
    route_ids = set(m_routes)
    for rid in sorted(route_ids):
        pid = m_routes[rid].get("parent_id")
        if pid is not None and pid not in route_ids:
            out.append(f"route {rid}: parent_id {pid!r} 不存在")
    for rid in sorted(route_ids):
        seen = {rid}
        cur = m_routes[rid].get("parent_id")
        while cur is not None:
            if cur in seen:
                out.append(f"route {rid}: parent 链有环")
                break
            if cur not in route_ids:
                break
            seen.add(cur)
            cur = m_routes[cur].get("parent_id")
    for vid, e in sorted(_index(manifest.get("vias"), "via_id").items()):
        pid = e.get("parent_id")
        if pid is None:
            continue  # 独立过孔（见模块 docstring）：合法，不指向任何 route
        if not isinstance(pid, str) or pid not in route_ids:
            out.append(f"via {vid}: parent_id {pid!r} 不指向存在的 route")
    rels = manifest.get("relations")
    rels = rels if isinstance(rels, list) else []
    for e in rels:
        if not isinstance(e, dict):
            continue
        rid = e.get("relation_id")
        members = e.get("members")
        if not isinstance(members, list):
            continue
        for m in members:
            if m not in net_registry:
                out.append(f"relation {rid}: member {m!r} 不是已注册 net")
    for rid, fr in sorted(svg_rels.items()):
        if fr["member_ids"] is None:
            continue
        for m in fr["member_ids"]:
            if m not in net_registry:
                out.append(f"relation {rid}: SVG member {m!r} "
                           "不是已注册 net")
    return out


def _hash_violations(root, manifest, snapshot, legend) -> list:
    """§4 规则 5：manifest/SVG/snapshot hash 绑定 + 图例绑定。"""
    out = []
    a = root.attrib
    payload = manifest.get("manifest_payload_sha256")
    if not isinstance(payload, str) or not SHA256_RE.match(payload):
        out.append(f"manifest.manifest_payload_sha256 非法: {payload!r}")
    recomputed = _sha256_of(manifest)
    if payload != recomputed:
        out.append("manifest.manifest_payload_sha256 != 重算值")
    bsha = manifest.get("board_snapshot_sha256")
    if not isinstance(bsha, str) or not SHA256_RE.match(bsha):
        out.append(f"manifest.board_snapshot_sha256 非法: {bsha!r}")
    if a.get("data-board-snapshot-sha256") != bsha:
        out.append("SVG data-board-snapshot-sha256 != "
                   "manifest.board_snapshot_sha256")
    if a.get("data-route-manifest-sha256") != payload:
        out.append("SVG data-route-manifest-sha256 != "
                   "manifest.manifest_payload_sha256")
    # v2：zone 事实哈希（事实投影，不含填充派生字段）必须重算一致，且 SVG
    # 根节点绑定它。zones_facts_sha256 以 *_sha256 结尾（不进 payload hash），
    # 因此这里的重算核对是它的唯一强制绑定，不得省略。
    zsha = manifest.get("zones_facts_sha256")
    if not isinstance(zsha, str) or not SHA256_RE.match(zsha):
        out.append(f"manifest.zones_facts_sha256 非法: {zsha!r}")
    elif isinstance(manifest.get("zones"), list):
        if zsha != zone_facts_sha256(manifest["zones"]):
            out.append("manifest.zones_facts_sha256 != zone 事实投影重算值"
                       "（zone 轮廓/net/layers/outline_kind/fill_state 被篡改）")
    if a.get("data-zones-facts-sha256") != zsha:
        out.append("SVG data-zones-facts-sha256 != "
                   "manifest.zones_facts_sha256")
    # v2：zones_summary 必须与逐条 zone 的 fill_state 一致（P3b 读它做
    # "未重填不得采纳"判定，必须防篡改）
    summary = manifest.get("zones_summary")
    zlist = manifest.get("zones")
    if not isinstance(summary, dict):
        out.append("manifest.zones_summary: 必须是对象（v2 合同）")
    elif isinstance(zlist, list):
        exp = _zones_summary([z for z in zlist if isinstance(z, dict)])
        if summary.get("count") != len(zlist):
            out.append("manifest.zones_summary.count != len(manifest.zones)")
        if summary.get("fill_state_counts") != exp["fill_state_counts"]:
            out.append("manifest.zones_summary.fill_state_counts 与逐条 zone 的"
                       " fill_state 不符")
        if summary.get("not_fresh_zone_ids") != exp["not_fresh_zone_ids"]:
            out.append("manifest.zones_summary.not_fresh_zone_ids 与逐条 zone"
                       " 的 fill_state 不符")
    if manifest.get("svg_coordinate_system") != SVG_COORD_SYSTEM:
        out.append("manifest.svg_coordinate_system 非法")
    rec = legend_record()
    if manifest.get("legend_version") != LEGEND_VERSION:
        out.append(f"manifest.legend_version 期望 {LEGEND_VERSION!r}，"
                   f"实际 {manifest.get('legend_version')!r}")
    if manifest.get("legend_sha256") != rec["legend_sha256"]:
        out.append("manifest.legend_sha256 != legend_record 重算值")
    if legend is None:
        out.append("SVG 缺图例组（data-legend-version）")
    else:
        if legend["legend_version"] != manifest.get("legend_version"):
            out.append("SVG 图例 data-legend-version != "
                       "manifest.legend_version")
        if legend["legend_sha256"] != manifest.get("legend_sha256"):
            out.append("SVG 图例 data-legend-sha256 != "
                       "manifest.legend_sha256")
    if snapshot is not None:
        if not isinstance(snapshot, dict):
            out.append("snapshot: 不是对象")
        else:
            if _sha256_of(snapshot) != bsha:
                out.append("snapshot sha256 != "
                           "manifest.board_snapshot_sha256"
                           "（快照过期或被篡改 → blocked）")
            sid = snapshot.get("scenario_id")
            if sid is not None and sid != manifest.get("scenario_id"):
                out.append("snapshot.scenario_id != manifest.scenario_id")
    return out


def _verify_all(svg_text: str, manifest: dict, snapshot) -> list:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        return [f"SVG: XML 语法错误: {exc}"]
    out = []
    bad = out.append
    out += _root_contract_violations(root)
    routes, vias, rels, pads, zones, legend = _collect_svg_objects(root, bad)
    out += _identity_violations(routes, vias, rels, manifest)
    out += _geometry_violations(routes, vias, root, manifest)
    out += _field_violations(routes, vias, rels, manifest)
    out += _zone_identity_violations(zones, manifest)
    out += _zone_geometry_violations(zones, manifest)
    out += _zone_field_violations(zones, manifest)
    net_registry = {r["net_id"] for r in routes.values()}
    net_registry |= {p["net_id"] for p in pads.values()}
    # v2：zone 的 net 也是本产物内的铜箔事实网（与 pad 同口径）
    net_registry |= {z["net_id"] for z in zones.values()
                     if isinstance(z.get("net_id"), str) and z["net_id"]}
    m_routes = _index(manifest.get("routes"), "route_id")
    net_registry |= {e.get("net_id") for e in m_routes.values()
                     if isinstance(e.get("net_id"), str)}
    out += _structure_violations(routes, rels, manifest, net_registry)
    out += _hash_violations(root, manifest, snapshot, legend)
    return out


def verify_consistency(svg_text: str, manifest: dict,
                       snapshot: "dict | None" = None) -> list:
    """核对 SVG 代码与 route-manifest（及 snapshot）的一致性（§4 规则 1–5）。

    返回违规原因列表；空列表 = 完全一致。fail-closed：XML 语法错误、合同
    属性缺失、枚举非法、坐标零容差不一致、字段不一致、id/parent/relation
    结构非法、manifest 自身 hash 不符、SVG 根 hash 属性与 manifest 不符、
    snapshot hash 不符（快照过期/被篡改）——任何一种都产出违规项；
    本函数内部异常也按违规处理，绝不返回假阳性空列表，绝不"以视觉为准"。
    """
    if not isinstance(manifest, dict):
        return ["manifest: 不是对象"]
    if not isinstance(svg_text, str):
        return ["svg_text: 不是字符串"]
    try:
        return sorted(_verify_all(svg_text, manifest, snapshot))
    except Exception as exc:  # 任何内部异常都按违规处理（fail-closed）
        return [f"verify: 内部异常按违规处理: "
                f"{exc.__class__.__name__}: {exc}"]


# ---------------------------------------------------------------- PNG（可选）

def _dash_segment(dr, p0, p1, dash, gap, color, width) -> None:
    import math
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        dr.line([(p0[0] + ux * pos, p0[1] + uy * pos),
                 (p0[0] + ux * end, p0[1] + uy * end)],
                fill=color, width=width)
        pos = end + gap


def _dash_rect(dr, a, b, color, width) -> None:
    _dash_segment(dr, (a[0], a[1]), (b[0], a[1]), 4.0, 3.0, color, width)
    _dash_segment(dr, (b[0], a[1]), (b[0], b[1]), 4.0, 3.0, color, width)
    _dash_segment(dr, (b[0], b[1]), (a[0], b[1]), 4.0, 3.0, color, width)
    _dash_segment(dr, (a[0], b[1]), (a[0], a[1]), 4.0, 3.0, color, width)


def render_png(board: dict, manifest: dict, width: int = 1600,
               height: int = 900, view_spec=None) -> dict:
    """可选 PNG 视觉投影（§2.1 产物 4，给人与多模态模型看）。

    缺 Pillow 等重依赖时返回 {"available": False, "status":
    "not_available", "reason": ...}，不抛裸异常。只返回 PNG 字节不落盘；
    机器事实绝不从 PNG 读取（§2.2，像素只是定位提示）。确定性渲染：
    无时间戳/无元数据注入，同输入逐字节一致。

    V4-EXEC-P10 扩展（向后兼容）：可选 ``view_spec``（V4-EXEC-P10
    route-viewer 的 T3 视图规格；canonical 形态见
    ``pcbflow.v4_route_viewer.normalize_view_spec``，非法即 ValueError
    fail-closed）。**``view_spec=None``（默认）＝既有行为：输出字节与
    返回键集与历史完全一致（测试以 golden hash 钉死）**。给定 view-spec
    时生成聚焦投影（按 layers/line_types/states/show_pads/show_keepouts/
    focus 过滤），分辨率以 spec 的 ``resolution_px`` 为准（spec 是
    canonical 合同），返回 dict 额外带 ``view_spec_sha256`` 键。
    """
    if view_spec is None:
        return _render_png_core(board, manifest, width, height,
                                spec=None, members=None)
    from . import v4_route_viewer as _vrv  # 惰性导入：默认路径零新依赖
    spec = _vrv.normalize_view_spec(view_spec, manifest, board)
    members = _vrv.view_spec_focus_members(spec, manifest, board)
    out = _render_png_core(board, manifest,
                           spec["resolution_px"][0], spec["resolution_px"][1],
                           spec=spec, members=members)
    if out.get("available"):
        out["view_spec_sha256"] = _vrv.view_spec_sha256(spec)
    return out


def _render_png_core(board: dict, manifest: dict, width: int, height: int,
                     *, spec=None, members=None) -> dict:
    """render_png 绘制内核（spec=None 时所有过滤谓词为恒真＝历史行为）。"""
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:  # 重依赖缺失 → 明确 not_available
        return {"available": False, "status": "not_available",
                "reason": f"PIL/Pillow 不可用: "
                          f"{exc.__class__.__name__}: {exc}"}
    _check_board(board)
    _require(isinstance(manifest, dict), "manifest: 不是对象")
    x0, y0, x1, y1 = [float(v) for v in manifest["board_bbox_mm"]]
    bw, bh = x1 - x0, y1 - y0
    margin = 24
    scale = min((width - 2 * margin) / bw, (height - 2 * margin) / bh)
    ox = (width - bw * scale) / 2
    oy = (height - bh * scale) / 2

    def px(x, y):
        return (ox + (x - x0) * scale, oy + (y - y0) * scale)

    # ---- view-spec 过滤谓词（spec=None → 恒真；单一绘制实现两种口径） ----
    layers = set(spec["layers"]) if spec else set()
    line_types = set(spec["line_types"]) if spec else set()
    states = set(spec["states"]) if spec else set()
    fnet = (members or {}).get("net_ids")
    froute = (members or {}).get("route_ids")
    fparent = (members or {}).get("parent_ids")

    def keep_route(r: dict) -> bool:
        if spec is None:
            return True
        if layers and r.get("layer") not in layers:
            return False
        if line_types and r.get("line_type") not in line_types:
            return False
        if states and r.get("state") not in states:
            return False
        if fnet is not None and r.get("net_id") not in fnet:
            return False
        if froute is not None and r.get("route_id") not in froute:
            return False
        if fparent is not None and r.get("parent_id") not in fparent:
            return False
        return True

    def keep_via(v: dict) -> bool:
        if spec is None:
            return True
        if layers and v.get("from_layer") not in layers \
                and v.get("to_layer") not in layers:
            return False
        if fnet is not None and v.get("net_id") not in fnet:
            return False
        if froute is not None and v.get("parent_id") not in froute:
            return False
        if fparent is not None and v.get("parent_id") not in fparent:
            return False
        return True

    def keep_pad(p: dict) -> bool:
        if spec is None:
            return True
        if not spec["show_pads"]:
            return False
        if fnet is not None and p.get("net_id") not in fnet:
            return False
        return True

    img = Image.new("RGB", (width, height), "#FFFFFF")
    dr = ImageDraw.Draw(img)
    dr.rectangle([px(x0, y0), px(x1, y1)], outline=BOARD_EDGE_COLOR, width=2)
    for k in sorted(board.get("keepouts") or [],
                    key=lambda k: str(k.get("keepout_id", ""))):
        if spec is not None and not spec["show_keepouts"]:
            continue
        r = k["rect_mm"]
        _dash_rect(dr, px(r[0], r[1]), px(r[2], r[3]), KEEPOUT_COLOR, 1)
    for p in sorted(board.get("pads") or [],
                    key=lambda p: str(p.get("pad_id", ""))):
        if not keep_pad(p):
            continue
        dr.rectangle(
            [px(float(p["x_mm"]) - float(p["w_mm"]) / 2,
                float(p["y_mm"]) - float(p["h_mm"]) / 2),
             px(float(p["x_mm"]) + float(p["w_mm"]) / 2,
                float(p["y_mm"]) + float(p["h_mm"]) / 2)],
            fill=PAD_FILL, outline="#4B5563")
    for r in manifest.get("routes") or []:
        if not keep_route(r):
            continue
        color = (STATE_COLORS.get(r.get("state"))
                 or LEGEND_COLORS.get(r.get("line_type"),
                                      LEGEND_COLORS["signal"]))
        pts = [px(q[0], q[1]) for q in r["polyline_mm"]]
        lw = max(1, int(round(float(r.get("width_mm", 0.3)) * scale * 1.6)))
        dr.line(pts, fill=color, width=lw, joint="curve")
    for v in manifest.get("vias") or []:
        if not keep_via(v):
            continue
        cx, cy = px(v["center_mm"][0], v["center_mm"][1])
        rpx = max(3.0, (float(v["drill_mm"]) / 2
                        + float(v["annular_ring_mm"])) * scale)
        dr.ellipse([cx - rpx, cy - rpx, cx + rpx, cy + rpx],
                   outline=VIA_COLOR, width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return {"available": True, "width": width, "height": height,
            "png_bytes": buf.getvalue()}
