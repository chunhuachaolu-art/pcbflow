# -*- coding: utf-8 -*-
"""浏览器交互视图骨架（任务书 §3.7 / D001；P1 交付：L1 分区图状态）。

P2 增补（2026-09-13）：按 §3.7「视图状态按阶段」新增两个阶段视图——
- ``render_l2_view``：L2 包络图状态（每分区包络矩形 + 宽度先验区间标注）；
- ``render_l3_view``：L3 叠加与 J 项图状态（冲突高亮 + 容量热区）。
两者共用 L1 底图（zone/工作区/图例绘制原样复用），上叠各自状态层；
消费上游合同 v5.envelope.v1 / v5.conflicts.v1（形状只消费、不判定，
fail-closed 的合同形状校验照旧）。L3 冲突 subjects 两级命中（2026-09-13 集成
冒烟定版）：partition_id 直命中，否则命中条目 source_partitions 成员 → 高亮
其容器条目（overlay subjects 引用板级分区号、L1 聚类可能已合并，如 demo-01
P7/P9→PG-7）；两级都不中 fail-closed（语义详见 _resolve_subject）。

形态（§3.7）：本地静态 SVG + 原生 JS，零第三方依赖、零构建链；SVG 手拼字符串、
JS 内嵌。边界与不变式：
- **确定性渲染**：sorted 迭代、坐标/数值固定 %.3f、无时间戳无随机——同输入双跑
  字节相等是硬测试（§3.4）；
- **前端只显示不判定**：capacity、宽度先验、电流等全部是引擎算好后写死进 SVG
  文本与 data-* 属性的值；内嵌 JS 只读属性做显隐 / 高亮 / tooltip，不重算任何数；
- **视图不进测量环**（§3.4），仅供人/诊断席位判读；
- **整条高亮钩子**：分区元素组及其子元素统一携带 data-partition-id / data-layer /
  data-layers 属性，JS 点击后按 partition_id 聚合高亮、其余压暗（跨层可扩展）；
- **层色层线型双编码**（色盲安全）：F.Cu 红 / In1 绿 / B.Cu 蓝（KiCad 惯例，
  键名去 .Cu 后缀匹配），其余信号层按栈序色环生成（固定步进 137°），平面层极淡灰；
  线型按栈序 实线/长虚/短虚/点线 循环。

sidecar 合规口径（2026-09-13 已核对 v5/sidecar.py 与 tools/check_sidecar.py 原文）：
- 检查器只对 ``*.json`` 解析 provenance 头（check_sidecar.main 根目录与子目录
  walk 均只挑 .json；sidecar.check_file 对非 .json 只做路径允许检查）；
- 因此 write_view：(1) 一律先过 sidecar.assert_allowed，只准写 ALLOWED_ROOTS 之下；
  (2) 按任务书 §3.5「每个 sidecar 头部带 provenance」仍以**首行 HTML 注释**落头：
      ``<!-- v5.view provenance generator=v5.view generator_version=0.1.0 board_sha256=<hex> ... -->``
     generator / generator_version / board_sha256 三键与 sidecar.PROVENANCE_KEYS
     同名，文本 sidecar 的卫生可人工/脚本审计；
  (3) 命名走 sidecar.sidecar_name：``<board-id>.<kind>.<svg|html>``（§3.5）。
  由此 tools/check_sidecar.py 对含本模块产物的 out/ 树保持 GREEN（已验证：
  SVG/HTML 非 .json 不进头检查，路径合规即可）。
"""
import os
import re

from . import sidecar

GENERATOR = "v5.view"
VERSION = "0.2.0"  # P2：新增 L2 包络图 / L3 叠加与 J 项图两阶段视图

# ---- 视图版面常量（固定值，参与确定性字节等） ----
VIEW_W = 800
VIEW_H = 600
MARGIN = 46
LEGEND_BAND = 96  # 底部图例带高度（px），地图区 = VIEW_H - LEGEND_BAND

# ---- 分区 ptype 调色板（Okabe-Ito 色盲安全 8 色，映射表写死，§3.7） ----
PTYPE_ORDER = ("PWR", "CLK", "HS", "BUS", "DIFF", "MISC", "ANA", "ROUTED")
PTYPE_COLORS = {
    "PWR": "#d55e00",     # 朱红（电源）
    "CLK": "#e69f00",     # 橙（时钟）
    "HS": "#0072b2",      # 蓝（高速）
    "BUS": "#009e73",     # 蓝绿（总线）
    "DIFF": "#cc79a7",    # 紫粉（差分对）
    "MISC": "#8c8c8c",    # 灰（杂项）
    "ANA": "#56b4e9",     # 天蓝（模拟）
    "ROUTED": "#1a1a1a",  # 黑（既布=终态中性）
}
PTYPE_FALLBACK = "#606060"  # 枚举外 ptype 兜底色（视图不拒载，只兜底显示）

# ---- zone 三类样式（§3.7 L1：keepout 红/斜线、sensitive 橙、corridor 蓝） ----
ZONE_STYLES = {
    "keepout": {"stroke": "#cc0000", "fill": "url(#v5-hatch-keepout)", "fill_opacity": "0.55"},
    "sensitive": {"stroke": "#ff9900", "fill": "#ff9900", "fill_opacity": "0.18"},
    "corridor": {"stroke": "#0066cc", "fill": "#0066cc", "fill_opacity": "0.12"},
}

# ---- 冲突高亮样式（§3.7 L3：blocking 红实线轮廓 / advisory 橙短虚线轮廓；语义色
#      沿用 zone 红橙语义（红=硬/橙=软），线型区分高亮轮廓与 zone 本体） ----
CONFLICT_PAD_PX = 6.0  # 冲突轮廓在 subjects/zone 包围盒外的固定外扩（SVG px）
CONFLICT_SEVERITIES = ("blocking", "advisory")
CONFLICT_STYLES = {
    "blocking": {"stroke": "#cc0000", "dash": ""},
    "advisory": {"stroke": "#ff9900", "dash": "4,3"},
}

ENVELOPE_FILL_OPACITY = "0.18"  # §3.7：包络=层色低透明填充（~0.18），重叠处下层可见
ENVELOPE_MARGIN_DEFAULT = 0.6   # L1/L2 既有 envelope/margin 口径（metrics.envelope.DEFAULT_MARGIN）

# ---- 层色（KiCad 惯例：F.Cu 红 / In1 绿 / B.Cu 蓝；键=层 id 去 .Cu 后缀） ----
LAYER_BASE_COLORS = {"F": "#cc0000", "In1": "#008000", "B": "#0000cc"}
PLANE_COLOR = "#9a9a9a"  # 平面层：极淡灰（§3.7 D001 r2）
# 按层线型循环：实线 / 长虚 / 短虚 / 点线（色盲安全双编码，§3.7）
LAYER_DASHES = ("", "14,5", "5,4", "2,4")

_POLICY_SPLIT = re.compile(r"[\s/+,|;]+")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------- 基础工具

def _fmt(value):
    """固定三位小数；-0.000 归一为 0.000（确定性渲染的一部分）。"""
    text = "%.3f" % float(value)
    return "0.000" if text == "-0.000" else text


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _layer_ids(stackup):
    return [str(layer.get("id", "")) for layer in stackup]


def _layer_key(layer_id):
    return layer_id[:-3] if layer_id.endswith(".Cu") else layer_id


def layer_color(stackup, layer_id):
    """层色：KiCad 惯例三色写死；平面层极淡灰；其余信号层按栈序色环（步进 137°）。"""
    key = _layer_key(layer_id)
    if key in LAYER_BASE_COLORS:
        return LAYER_BASE_COLORS[key]
    ids = _layer_ids(stackup)
    entry = None
    for layer in stackup:
        if str(layer.get("id", "")) == layer_id:
            entry = layer
            break
    if entry is not None and entry.get("kind") == "plane":
        return PLANE_COLOR
    idx = ids.index(layer_id) if layer_id in ids else 0
    return "hsl(%d,62%%,38%%)" % ((137 * idx) % 360)


def layer_dash(stackup, layer_id):
    """按层线型：栈序循环 实线/长虚/短虚/点线；未定层（any/未知）画实线。"""
    ids = _layer_ids(stackup)
    if layer_id in ids:
        return LAYER_DASHES[ids.index(layer_id) % len(LAYER_DASHES)]
    return ""


def _policy_tokens(policy):
    return [tok for tok in _POLICY_SPLIT.split(str(policy or "")) if tok]


def _primary_layer(policy, stackup):
    """分区主层：layer_policy 里第一个真实存在的层 id；any/空/全未知 → 'any'。"""
    tokens = _policy_tokens(policy)
    if "any" in tokens or not tokens:
        return "any"
    for lid in _layer_ids(stackup):
        if lid in tokens:
            return lid
    return "any"


def _partition_visible_layers(policy, stackup):
    """该分区在哪些单层模式下可见（'all' 模式恒可见，另由调用方处理）。"""
    tokens = _policy_tokens(policy)
    if "any" in tokens:
        return _layer_ids(stackup)
    return [lid for lid in _layer_ids(stackup) if lid in tokens]


def _zone_visible_layers(zone_layers, stackup):
    """zone.layers='all' → 所有层；'signal' → 仅 signal 类层。"""
    if str(zone_layers) == "signal":
        return [str(layer.get("id", "")) for layer in stackup
                if layer.get("kind") == "signal"]
    return _layer_ids(stackup)


def _vis_attr(visible_layers):
    """data-layers 属性值：'all' + 各可见单层（HTML solo 下拉的显隐依据，前端零计算）。"""
    return _esc(" ".join(["all"] + list(visible_layers)))


def validate_mode(mode, board):
    """mode 只准 'all' 或 stackup 层 id，否则 ValueError（§3.7 单层独显合同）。"""
    if mode == "all":
        return
    if mode in _layer_ids(board.get("stackup", []) or []):
        return
    raise ValueError(
        "非法视图 mode=%r：只准 'all' 或 stackup 层 id（现有: %s）"
        % (mode, ",".join(_layer_ids(board.get("stackup", []) or [])) or "<无>"))


def _check_provenance(board, partition_table):
    """分区表与板的 provenance 对账（§3.1：证据链按 hash 对账而非文件名）。"""
    if not isinstance(partition_table, dict):
        return
    board_sha = (board.get("provenance", {}) or {}).get("board_sha256")
    table_sha = partition_table.get("board_sha256")
    if board_sha and table_sha and board_sha != table_sha:
        raise ValueError(
            "分区表 board_sha256=%r 与板 provenance.board_sha256=%r 不符（按 hash 对账失败）"
            % (table_sha, board_sha))
    board_id = board.get("board_id")
    table_id = partition_table.get("board_id")
    if board_id and table_id and board_id != table_id:
        raise ValueError("分区表 board_id=%r 与板 board_id=%r 不符" % (table_id, board_id))


class _Plane(object):
    """世界坐标 → SVG 坐标线性映射（等比缩放、居中；y 轴同为向下，不翻转）。"""

    def __init__(self, workspace, box_x, box_y, box_w, box_h):
        dx = max(float(workspace["x_max"]) - float(workspace["x_min"]), 1e-9)
        dy = max(float(workspace["y_max"]) - float(workspace["y_min"]), 1e-9)
        self.scale = min(box_w / dx, box_h / dy)
        self.x0 = float(workspace["x_min"])
        self.y0 = float(workspace["y_min"])
        self.ox = box_x + (box_w - dx * self.scale) / 2.0
        self.oy = box_y + (box_h - dy * self.scale) / 2.0

    def x(self, wx):
        return _fmt(self.ox + (float(wx) - self.x0) * self.scale)

    def y(self, wy):
        return _fmt(self.oy + (float(wy) - self.y0) * self.scale)

    def w(self, dw):
        return _fmt(float(dw) * self.scale)


# ---------------------------------------------------------------- SVG 渲染

def _render_zone(zone, plane, stackup, visible_layers, heat=None):
    """画单个 zone；heat 非 None 时（仅 corridor，L3 容量热区）：填充透明度改由
    occupancy/capacity 比值驱动、capacity 文本换成引擎账本值（前端不算数）。"""
    zone_id = _esc(zone.get("zone_id", ""))
    kind = str(zone.get("kind", "sensitive"))
    style = ZONE_STYLES.get(kind, ZONE_STYLES["sensitive"])
    rect = zone.get("rect", {}) or {}
    x = plane.x(rect.get("x_min", 0.0))
    y = plane.y(rect.get("y_min", 0.0))
    w = plane.w(float(rect.get("x_max", 0.0)) - float(rect.get("x_min", 0.0)))
    h = plane.w(float(rect.get("y_max", 0.0)) - float(rect.get("y_min", 0.0)))
    fill_opacity = str(heat["fill_opacity"]) if (heat and kind == "corridor") else style["fill_opacity"]
    lines = ['<g class="v5-zone" data-zone-id="%s" data-kind="%s" data-layers="%s">'
             % (zone_id, _esc(kind), _vis_attr(visible_layers))]
    lines.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" fill-opacity="%s"'
                 ' stroke="%s" stroke-width="1.5"/>'
                 % (x, y, w, h, style["fill"], fill_opacity, style["stroke"]))
    lines.append('<text class="v5-zone-label" x="%s" y="%s" font-size="11" fill="%s">%s</text>'
                 % (x, _fmt(float(y) + 13.0), style["stroke"], zone_id))
    if kind == "corridor" and heat is not None:
        # 容量热区：引擎账本的 occupancy/capacity 原样写死进文本与 data-*（§3.7）。
        lines.append('<text class="v5-zone-capacity" x="%s" y="%s" font-size="11"'
                     ' fill="%s" data-occupancy="%s" data-capacity="%s">%s</text>'
                     % (x, _fmt(float(y) + 26.0), style["stroke"],
                        _esc(str(heat["occupancy"])), _esc(str(heat["capacity"])),
                        _esc(str(heat["label"]))))
    elif kind == "corridor" and zone.get("capacity") is not None:
        # 引擎算好的 capacity 原样写死进 SVG 文本（§3.7：前端只显示不重算）。
        lines.append('<text class="v5-zone-capacity" x="%s" y="%s" font-size="11"'
                     ' fill="%s">capacity=%s</text>'
                     % (x, _fmt(float(y) + 26.0), style["stroke"], _fmt(zone["capacity"])))
    lines.append("</g>")
    return lines


def _render_partition(part, plane, stackup, visible_layers):
    """分区 = endpoints 双圆点 + 连线 + partition_id 文本；全元素带高亮钩子属性。"""
    pid = str(part.get("partition_id", ""))
    pid_esc = _esc(pid)
    ptype = str(part.get("ptype", ""))
    color = PTYPE_COLORS.get(ptype, PTYPE_FALLBACK)
    policy = str(part.get("layer_policy", "any"))
    prim = _primary_layer(policy, stackup)
    prim_esc = _esc(prim)
    dash = layer_dash(stackup, prim)
    dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
    endpoints = (part.get("geometry", {}) or {}).get("endpoints") or []
    if len(endpoints) != 2:
        raise ValueError("分区 %s geometry.endpoints 必须恰为 2 点，实得 %d"
                         % (pid, len(endpoints)))
    x1, y1 = plane.x(endpoints[0][0]), plane.y(endpoints[0][1])
    x2, y2 = plane.x(endpoints[1][0]), plane.y(endpoints[1][1])
    width = part.get("width_prior", {}) or {}
    lines = ['<g class="v5-part" id="v5-part-%s" data-partition-id="%s" data-ptype="%s"'
             ' data-layer="%s" data-layers="%s" data-layer-policy="%s"'
             ' data-w-min="%s" data-w-max="%s" data-current-a="%s" data-speed-class="%s">'
             % (pid_esc, pid_esc, _esc(ptype), prim_esc, _vis_attr(visible_layers),
                _esc(policy), _fmt(width.get("w_min", 0.0)), _fmt(width.get("w_max", 0.0)),
                _fmt(part.get("current_a", 0.0)), _esc(part.get("speed_class", "")))]
    for cx, cy in ((x1, y1), (x2, y2)):
        lines.append('<circle class="v5-pt" cx="%s" cy="%s" r="4" fill="%s"'
                     ' data-partition-id="%s" data-layer="%s"/>'
                     % (cx, cy, color, pid_esc, prim_esc))
    lines.append('<line class="v5-seg" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"'
                 ' stroke-width="2.5" stroke-opacity="0.75"%s'
                 ' data-partition-id="%s" data-layer="%s"/>'
                 % (x1, y1, x2, y2, color, dash_attr, pid_esc, prim_esc))
    lines.append('<text class="v5-label" x="%s" y="%s" font-size="11" fill="%s"'
                 ' data-partition-id="%s" data-layer="%s">%s</text>'
                 % (x1, _fmt(float(y1) - 6.0), color, pid_esc, prim_esc, pid_esc))
    lines.append("</g>")
    return lines


def _render_legends(stackup):
    band = VIEW_H - LEGEND_BAND
    lines = ['<g id="legend" data-kind="ptype-palette">']
    lines.append('<text x="%d" y="%d" font-size="12" font-weight="bold">分区类型图例</text>'
                 % (MARGIN, band + 18))
    for i, ptype in enumerate(PTYPE_ORDER):
        col, row = i % 4, i // 4
        x = MARGIN + 160 + col * 140
        y = band + 36 + row * 18
        lines.append('<g class="v5-legend-item" data-ptype="%s">'
                     '<rect x="%d" y="%d" width="14" height="10" fill="%s"/>'
                     '<text x="%d" y="%d" font-size="11" fill="#333333">%s</text></g>'
                     % (ptype, x, y - 10, PTYPE_COLORS[ptype], x + 19, y, ptype))
    lines.append("</g>")
    lines.append('<g id="layer-legend" data-kind="layer-legend">')
    lines.append('<text x="%d" y="%d" font-size="12" font-weight="bold">层图例（色+线型双编码）</text>'
                 % (MARGIN, band + 84))
    for j, lid in enumerate(_layer_ids(stackup)):
        x = MARGIN + 160 + j * 120
        y = band + 84
        dash = layer_dash(stackup, lid)
        dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
        lines.append('<g class="v5-legend-layer" data-layer="%s">'
                     '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"%s/>'
                     '<text x="%d" y="%d" font-size="11" fill="#333333">%s</text></g>'
                     % (_esc(lid), x, y - 4, x + 26, y - 4, layer_color(stackup, lid),
                        dash_attr, x + 32, y, _esc(lid)))
    lines.append("</g>")
    return lines


def _open_l1_base(board, partition_table, mode, svg_id, data_v5, title_prefix,
                  zone_heat=None):
    """L1 底图（L1/L2/L3 三阶段视图共用）：SVG 头 + defs + 白底 + zones +
    工作区边界框 + 分区层。返回 (out 行列表, plane 投影器)；out 不含图例与
    ``</svg>``，由调用方续写状态层后收尾。mode 校验与分区表对账在此统一做；
    zone_heat（仅 L3 容量热区）按 zone_id 透传给 _render_zone。"""
    stackup = board.get("stackup", []) or []
    validate_mode(mode, board)
    _check_provenance(board, partition_table)
    workspace = board["workspace"]
    map_h = VIEW_H - LEGEND_BAND
    plane = _Plane(workspace, MARGIN, MARGIN, VIEW_W - 2 * MARGIN, map_h - 2 * MARGIN)
    board_id = _esc(board.get("board_id", ""))
    board_sha = _esc((board.get("provenance", {}) or {}).get("board_sha256", ""))

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" id="%s"'
               ' data-v5="%s" data-mode="%s" data-board-id="%s"'
               ' data-board-sha256="%s" viewBox="0 0 %d %d" width="%d" height="%d">'
               % (svg_id, data_v5, mode, board_id, board_sha,
                  VIEW_W, VIEW_H, VIEW_W, VIEW_H))
    out.append('<title>%s %s（mode=%s）</title>' % (title_prefix, board_id, mode))
    out.append('<desc>v5.view 确定性渲染；所有数值为引擎预计算，前端只显示不判定（§3.7）。</desc>')
    out.append('<defs>'
               '<pattern id="v5-hatch-keepout" width="8" height="8"'
               ' patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
               '<rect x="0" y="0" width="8" height="8" fill="#ffffff"/>'
               '<line x1="0" y1="0" x2="0" y2="8" stroke="#cc0000" stroke-width="2"/>'
               '</pattern></defs>')
    out.append('<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (VIEW_W, VIEW_H))

    # zones（sorted 迭代；单层模式按 zone.layers 过滤）
    heat_map = zone_heat or {}
    for zone in sorted(board.get("zones", []) or [],
                       key=lambda z: str(z.get("zone_id", ""))):
        vis = _zone_visible_layers(zone.get("layers", "all"), stackup)
        if mode != "all" and mode not in vis:
            continue
        out.extend(_render_zone(zone, plane, stackup, vis,
                                heat_map.get(str(zone.get("zone_id", "")))))

    # 工作区边界矩形描边（f8-01：边界必须可见披露）
    out.append('<rect id="workspace-frame" x="%s" y="%s" width="%s" height="%s"'
               ' fill="none" stroke="#262626" stroke-width="2"/>'
               % (plane.x(workspace["x_min"]), plane.y(workspace["y_min"]),
                  plane.w(float(workspace["x_max"]) - float(workspace["x_min"])),
                  plane.w(float(workspace["y_max"]) - float(workspace["y_min"]))))

    # 分区（自底向上：层栈 自底→顶，再按 partition_id；单层模式按 layer_policy 过滤）
    parts = []
    if isinstance(partition_table, dict):
        parts = list(partition_table.get("partitions", []) or [])
    draw_stack = list(reversed(_layer_ids(stackup)))

    def _draw_key(part):
        prim = _primary_layer(part.get("layer_policy", "any"), stackup)
        idx = draw_stack.index(prim) if prim in draw_stack else len(draw_stack)
        return (idx, str(part.get("partition_id", "")))

    for part in sorted(parts, key=_draw_key):
        vis = _partition_visible_layers(part.get("layer_policy", "any"), stackup)
        if mode != "all" and mode not in vis:
            continue
        out.extend(_render_partition(part, plane, stackup, vis))

    return out, plane


def render_l1_view(board, partition_table, mode="all"):
    """渲染 L1 分区图 SVG 字符串。

    mode="all" 全层叠加（§3.7 模式 1：自底向上绘制、走线透明 0.75）；mode=具体层 id
    单层独显（按 layer_policy 与 zone.layers 过滤）。同输入双跑字节相等。
    """
    out, _ = _open_l1_base(board, partition_table, mode,
                           "v5-l1-view", "l1-partitions", "v5 L1 分区图")
    out.extend(_render_legends(board.get("stackup", []) or []))
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- L2/L3 状态层

def _parts_by_id(partition_table):
    """分区表 → {partition_id: partition}（视图查 subjects/ref 用，sorted 无关）。"""
    by_id = {}
    if isinstance(partition_table, dict):
        for part in partition_table.get("partitions", []) or []:
            by_id[str(part.get("partition_id", ""))] = part
    return by_id


def _check_envelope_artifact(artifact):
    """L2 上游合同（v5.envelope.v1）形状轻校验：fail-closed 报错；只查形状与
    artifact 标识，不动引擎判定（数值合法性由 L2 侧 validate_envelope_artifact 负责）。"""
    if not isinstance(artifact, dict):
        raise ValueError("render_l2_view: envelope_artifact 须为 dict，得到 %s"
                         % type(artifact).__name__)
    tag = artifact.get("artifact")
    if tag is not None and tag != "v5.envelope.v1":
        raise ValueError("render_l2_view: envelope_artifact.artifact=%r 须为 'v5.envelope.v1'"
                         % (tag,))
    if not isinstance(artifact.get("per_partition"), list):
        raise ValueError("render_l2_view: envelope_artifact.per_partition 须为列表")


def render_l2_view(board, partition_table, envelope_artifact, mode="all"):
    """渲染 L2 包络图状态 SVG 字符串（§3.7：L2 包络图（宽度先验区间））。

    L1 底图之上叠加：每分区包络矩形（层色低透明填充 + 层线型描边，复用既有
    envelope/margin 口径 0.6）+ 宽度先验区间标注（每分区一行文本
    ``<ref> w∈[w_min,w_max]→opt <opt>``，数值取自 envelope_artifact.per_partition
    ——引擎算好直接写死，前端不重算）。单层 mode 过滤同 L1 口径（分区 layer_policy）。
    同输入双跑字节相等。
    """
    stackup = board.get("stackup", []) or []
    _check_envelope_artifact(envelope_artifact)
    # 包络工件与板的证据链对账（复用既有机制：board_sha256/board_id 按 hash 对账）。
    _check_provenance(board, envelope_artifact)
    out, plane = _open_l1_base(board, partition_table, mode,
                               "v5-l2-view", "l2-envelope", "v5 L2 包络图")
    by_id = _parts_by_id(partition_table)
    for entry in sorted(envelope_artifact.get("per_partition", []) or [],
                        key=lambda e: str(e.get("partition_ref", ""))):
        ref = str(entry.get("partition_ref", ""))
        ref_esc = _esc(ref)
        part = by_id.get(ref)
        if part is None:
            raise ValueError(
                "render_l2_view: 包络条目 partition_ref=%r 未命中分区表（上游不一致，fail-closed）"
                % (ref,))
        policy = str(part.get("layer_policy", "any"))
        vis = _partition_visible_layers(policy, stackup)
        if mode != "all" and mode not in vis:
            continue
        prim = _primary_layer(policy, stackup)
        if prim == "any":
            # any 策略无单一层色：兜底中性灰 + 实线（文档化口径，与 ptype 兜底同色）。
            color, dash = PTYPE_FALLBACK, ""
        else:
            color, dash = layer_color(stackup, prim), layer_dash(stackup, prim)
        prim_esc = _esc(prim)
        dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
        env = entry.get("envelope_mm", []) or [0.0, 0.0, 0.0, 0.0]
        x = plane.x(env[0])
        y = plane.y(env[1])
        w = plane.w(float(env[2]) - float(env[0]))
        h = plane.w(float(env[3]) - float(env[1]))
        prior = entry.get("width_prior", {}) or {}
        width_text = "%s w∈[%s,%s]→opt %s" % (
            ref, _fmt(prior.get("w_min", 0.0)), _fmt(prior.get("w_max", 0.0)),
            _fmt(entry.get("optimal_width", 0.0)))
        lines = ['<g class="v5-envelope" data-partition-id="%s" data-layer="%s"'
                 ' data-layers="%s" data-kind="envelope" data-margin-mm="%s"'
                 ' data-w-min="%s" data-w-max="%s" data-opt-width="%s">'
                 % (ref_esc, prim_esc, _vis_attr(vis), _fmt(entry.get("margin_mm",
                                                                     ENVELOPE_MARGIN_DEFAULT)),
                    _fmt(prior.get("w_min", 0.0)), _fmt(prior.get("w_max", 0.0)),
                    _fmt(entry.get("optimal_width", 0.0)))]
        lines.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"'
                     ' fill-opacity="%s" stroke="%s" stroke-width="1.5"%s'
                     ' data-partition-id="%s" data-layer="%s"/>'
                     % (x, y, w, h, color, ENVELOPE_FILL_OPACITY, color, dash_attr,
                        ref_esc, prim_esc))
        lines.append('<text class="v5-envelope-width" x="%s" y="%s" font-size="11"'
                     ' fill="%s" data-partition-id="%s" data-layer="%s">%s</text>'
                     % (x, _fmt(float(y) - 4.0), color, ref_esc, prim_esc,
                        _esc(width_text)))
        lines.append("</g>")
        out.extend(lines)

    out.extend(_render_legends(stackup))
    out.append("</svg>")
    return "\n".join(out)


def _check_conflicts_artifact(artifact):
    """L3 上游合同（v5.conflicts.v1）形状轻校验：fail-closed；返回 conflicts 列表。
    severity 只准 blocking|advisory（驱动轮廓样式），conflict_id 必须非空。"""
    if not isinstance(artifact, dict):
        raise ValueError("render_l3_view: conflicts_artifact 须为 dict，得到 %s"
                         % type(artifact).__name__)
    tag = artifact.get("artifact")
    if tag is not None and tag != "v5.conflicts.v1":
        raise ValueError("render_l3_view: conflicts_artifact.artifact=%r 须为 'v5.conflicts.v1'"
                         % (tag,))
    items = artifact.get("conflicts")
    if not isinstance(items, list):
        raise ValueError("render_l3_view: conflicts_artifact.conflicts 须为列表")
    for i, cf in enumerate(items):
        if not isinstance(cf, dict):
            raise ValueError("render_l3_view: conflicts[%d] 须为对象" % i)
        severity = str(cf.get("severity", ""))
        if severity not in CONFLICT_SEVERITIES:
            raise ValueError("render_l3_view: conflicts[%d].severity=%r 须为 blocking|advisory"
                             % (i, cf.get("severity")))
        if not str(cf.get("conflict_id", "")):
            raise ValueError("render_l3_view: conflicts[%d].conflict_id 须为非空字符串" % i)
    return items


def _corridor_heat(board, corridor_stats):
    """corridor_stats（调用方自 L2 账本取的引擎值）→ {zone_id: heat}（容量热区）。

    - None → 空表：走廊只画常规色不加热（§3.7 口径）；
    - 每条须含 occupancy/capacity 数值（capacity>0）；heat.fill_opacity =
      occupancy/capacity 比值（钳到 [0,1]：SVG fill-opacity 上界，引擎原值照写在
      文本与 data-*，前端不算数）；heat.label = "<zid> <occ>/<cap> OVER|OK"。
    - 键必须命中板上 kind=="corridor" 的 zone，否则 fail-closed（上游笔误早暴露）。
    """
    if corridor_stats is None:
        return {}
    if not isinstance(corridor_stats, dict):
        raise ValueError("render_l3_view: corridor_stats 须为 dict 或 None，得到 %s"
                         % type(corridor_stats).__name__)
    corridor_ids = {str(z.get("zone_id", "")) for z in board.get("zones", []) or []
                    if z.get("kind") == "corridor"}
    heat = {}
    for zid in sorted(corridor_stats):
        stats = corridor_stats[zid]
        if (not isinstance(stats, dict) or "occupancy" not in stats
                or "capacity" not in stats):
            raise ValueError("render_l3_view: corridor_stats[%r] 须为含 occupancy/capacity"
                             " 的对象，得到 %r" % (zid, stats))
        if str(zid) not in corridor_ids:
            raise ValueError("render_l3_view: corridor_stats 键 %r 未命中板上 corridor zone"
                             "（现有: %s）" % (zid, ",".join(sorted(corridor_ids)) or "<无>"))
        occ = float(stats["occupancy"])
        cap = float(stats["capacity"])
        if cap <= 0:
            raise ValueError("render_l3_view: corridor_stats[%r].capacity 须 > 0，得到 %r"
                             % (zid, stats["capacity"]))
        ratio = min(max(occ / cap, 0.0), 1.0)
        heat[str(zid)] = {
            "fill_opacity": _fmt(ratio),
            "occupancy": _fmt(occ),
            "capacity": _fmt(cap),
            "label": "%s %s/%s %s" % (zid, _fmt(occ), _fmt(cap),
                                      "OVER" if occ > cap else "OK"),
        }
    return heat


def _resolve_subject(subject, by_id):
    """冲突 subject 两级命中（2026-09-13 集成冒烟定版的消费端归并语义）：

    冲突工件 subjects 引用**板级分区号**，而 L1 聚类可能已把板级分区合并
    （实测 demo-01：CF-002 subjects=[P1,P2,P4,P7,P9]，P7/P9 已合并进 PG-7；
    overlay 以板为输入不认识 L1，归并适配由视图消费端承担）：
    1. partition_id 直接命中（一级，原行为保留）；
    2. 否则命中任一条目的 source_partitions 成员 → 高亮目标=包含它的容器条目；
    两级都未命中 → None（调用方 fail-closed）。多容器命中取 sorted 首个
    （注册上 source_partitions 跨条目不相交，此处仅为防御性确定序）。
    """
    part = by_id.get(subject)
    if part is not None:
        return part
    for pid in sorted(by_id):
        sources = [str(s) for s in (by_id[pid].get("source_partitions") or [])]
        if subject in sources:
            return by_id[pid]
    return None


def _render_conflict(cf, plane, by_id, zones_by_id, stackup, mode):
    """画单个冲突高亮（blocking=红实线 / advisory=橙短虚线轮廓）。

    - subjects 逐个两级解析（_resolve_subject）：每个 subject 一条轮廓，圈住其
      目标条目端点包围盒外扩 CONFLICT_PAD_PX；rect 带整条高亮钩子
      data-conflict-id/data-severity/data-kind，另带 data-conflict-subject（原
      subject）与 data-partition-id（容器条目 id；直接命中时=subject 本身）；
    - 冲突引用的 zone（若有）另画一条 zone 轮廓（data-zone-id + severity 样式；
      不带 conflict-id 钩子——每冲突带钩子的轮廓恰为 subjects 数，对账无歧义，
      组级 closest 聚合仍可达）；
    - conflict_id / arithmetic（可复算式）写死为文本，锚定全部轮廓联合包围盒左上；
    - mode 过滤口径同 L1：subjects 目标条目层策略 ∪ zone.layers 含该层才画。
    """
    cid = str(cf.get("conflict_id", ""))
    cid_esc = _esc(cid)
    severity = str(cf.get("severity", ""))
    kind = str(cf.get("kind", ""))
    style = CONFLICT_STYLES[severity]
    hooks = ' data-conflict-id="%s" data-severity="%s" data-kind="%s"' % (
        cid_esc, _esc(severity), _esc(kind))

    resolved, vis = [], []
    for subj in [str(s) for s in (cf.get("subjects") or [])]:
        part = _resolve_subject(subj, by_id)
        if part is None:
            raise ValueError("render_l3_view: 冲突 %s 的 subject %r 两级均未命中分区表"
                             "（partition_id 与全部 source_partitions 都不含；"
                             "上游不一致，fail-closed）" % (cid, subj))
        vis.extend(_partition_visible_layers(str(part.get("layer_policy", "any")), stackup))
        resolved.append((subj, part))
    zid = cf.get("zone")
    zone = zones_by_id.get(str(zid)) if zid is not None else None
    if zid is not None and zone is None:
        raise ValueError("render_l3_view: 冲突 %s 的 zone %r 未命中板 zones"
                         "（上游不一致，fail-closed）" % (cid, zid))
    if zone is not None:
        vis.extend(_zone_visible_layers(zone.get("layers", "all"), stackup))
    if mode != "all" and mode not in vis:
        return []

    def _bbox_rect(pts):
        """世界坐标点集 → 联合包围盒外扩 PAD 后的 (x, y, x2, y2)（SVG px）。"""
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        return (float(plane.x(xs[0])) - CONFLICT_PAD_PX,
                float(plane.y(ys[0])) - CONFLICT_PAD_PX,
                float(plane.x(xs[-1])) + CONFLICT_PAD_PX,
                float(plane.y(ys[-1])) + CONFLICT_PAD_PX)

    dash_attr = ' stroke-dasharray="%s"' % style["dash"] if style["dash"] else ""
    lines = ['<g class="v5-conflict"%s>' % hooks]
    union = []  # 世界坐标点集（全部轮廓联合包围盒，conflict_id/算式文本锚定用）
    for subj, part in resolved:
        pts = [(float(pt[0]), float(pt[1]))
               for pt in (part.get("geometry", {}) or {}).get("endpoints") or []]
        if not pts:
            continue
        x, y, x2, y2 = _bbox_rect(pts)
        union.extend(pts)
        lines.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none"'
                     ' stroke="%s" stroke-width="2"%s%s'
                     ' data-conflict-subject="%s" data-partition-id="%s"/>'
                     % (_fmt(x), _fmt(y), _fmt(x2 - x), _fmt(y2 - y),
                        style["stroke"], dash_attr, hooks,
                        _esc(subj), _esc(str(part.get("partition_id", "")))))
    if zone is not None:
        zrect = zone.get("rect", {}) or {}
        zpts = [(float(zrect.get("x_min", 0.0)), float(zrect.get("y_min", 0.0))),
                (float(zrect.get("x_max", 0.0)), float(zrect.get("y_max", 0.0)))]
        x, y, x2, y2 = _bbox_rect(zpts)
        union.extend(zpts)
        lines.append('<rect class="v5-conflict-zone" x="%s" y="%s" width="%s"'
                     ' height="%s" fill="none" stroke="%s" stroke-width="2"%s'
                     ' data-zone-id="%s" data-severity="%s"/>'
                     % (_fmt(x), _fmt(y), _fmt(x2 - x), _fmt(y2 - y),
                        style["stroke"], dash_attr, _esc(str(zid)), _esc(severity)))
    if not union:
        raise ValueError("render_l3_view: 冲突 %s 无可画几何"
                         "（subjects 目标条目与 zone 均无坐标）" % cid)
    ux, uy, _, _ = _bbox_rect(union)
    lines.append('<text class="v5-conflict-id" x="%s" y="%s" font-size="11" fill="%s"%s>'
                 '%s</text>'
                 % (_fmt(ux), _fmt(uy + 13.0), style["stroke"], hooks, cid_esc))
    arithmetic = cf.get("arithmetic")
    if arithmetic is not None and str(arithmetic) != "":
        # 可复算式原样写死（引擎侧产出；§3.7 前端只显示不判定/不重算）。
        lines.append('<text class="v5-conflict-arithmetic" x="%s" y="%s" font-size="11"'
                     ' fill="%s"%s>%s</text>'
                     % (_fmt(ux), _fmt(uy + 26.0), style["stroke"], hooks,
                        _esc(str(arithmetic))))
    lines.append("</g>")
    return lines


def render_l3_view(board, partition_table, conflicts_artifact, corridor_stats=None,
                   mode="all"):
    """渲染 L3 叠加与 J 项图状态 SVG 字符串（§3.7：冲突高亮+容量热区）。

    L1 底图之上叠加：
    - 冲突高亮：blocking=红实线轮廓 / advisory=橙短虚线轮廓；subjects 逐个两级
      解析（partition_id 直命中，否则命中条目 source_partitions 成员 → 高亮其
      容器条目——overlay subjects 引用板级分区号而 L1 聚类可能已合并，归并语义
      见 _resolve_subject）后各画一条轮廓；conflict_id 与 arithmetic（可复算式）
      写死为文本；subject 轮廓带 data-conflict-id/data-severity/data-kind 高亮钩子
      及 data-conflict-subject（原 subject）/data-partition-id（容器条目 id）；
    - 容量热区：corridor zone 填充透明度 = occupancy/capacity 比值驱动，图例文本写
      引擎值（如 ``C1 7.050/4.300 OVER``）；数值由 corridor_stats 参数直传（调用方
      自 L2 账本取，不从 conflicts 的 arithmetic 解析——解析不可靠，文档化决定）；
      corridor_stats=None 时走廊只画常规色不加热。
    mode 过滤同 L1 口径。同输入双跑字节相等。
    """
    stackup = board.get("stackup", []) or []
    conflicts = _check_conflicts_artifact(conflicts_artifact)
    # 冲突工件与板的证据链对账（复用既有机制：board_sha256/board_id 按 hash 对账）。
    _check_provenance(board, conflicts_artifact)
    heat = _corridor_heat(board, corridor_stats)
    out, plane = _open_l1_base(board, partition_table, mode,
                               "v5-l3-view", "l3-overlays", "v5 L3 叠加与 J 项图",
                               zone_heat=heat)
    by_id = _parts_by_id(partition_table)
    zones_by_id = {str(z.get("zone_id", "")): z
                   for z in board.get("zones", []) or []}
    for cf in sorted(conflicts, key=lambda c: (str(c.get("conflict_id", "")),
                                               str(c.get("kind", "")))):
        out.extend(_render_conflict(cf, plane, by_id, zones_by_id, stackup, mode))

    out.extend(_render_legends(stackup))
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- HTML 骨架

_VIEW_CSS = (
    "body { margin: 0; font-family: sans-serif; background: #f2f2f2; }\n"
    "#v5-toolbar { background: #ffffff; border-bottom: 1px solid #cccccc;"
    " padding: 6px 12px; font-size: 13px; }\n"
    "#v5-toolbar select { margin: 0 8px; }\n"
    "#v5-hint { color: #666666; margin-left: 10px; }\n"
    "#v5-stage { padding: 8px; }\n"
    "#v5-stage svg { background: #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.25); }\n"
    "#v5-stage svg g.v5-part { cursor: pointer; }\n"
    "#v5-stage svg.v5-has-focus g.v5-part { opacity: 0.12; }\n"
    "#v5-stage svg.v5-has-focus g.v5-part.v5-focus { opacity: 1; }\n"
    "#v5-stage svg.v5-has-focus g.v5-zone { opacity: 0.3; }\n"
    "#v5-tooltip { position: fixed; display: none; background: #fffde7;"
    " border: 1px solid #888888; padding: 5px 8px; font-size: 12px;"
    " pointer-events: none; white-space: pre; z-index: 99; }"
)

# 原生 JS，零依赖；无 Date/Math.random（确定性）；只读 data-* 显示，不重算。
_VIEW_JS = """(function () {
  'use strict';
  var svg = document.getElementById('v5-l1-view');
  var solo = document.getElementById('v5-layer-solo');
  var tip = document.getElementById('v5-tooltip');
  if (!svg || !solo) { return; }

  // 层 solo（§3.7 模式 3）：显隐依据 = 渲染端预计算的 data-layers，前端零计算。
  function applySolo() {
    var mode = solo.value;
    svg.setAttribute('data-mode', mode);
    var nodes = svg.querySelectorAll('[data-layers]');
    for (var i = 0; i < nodes.length; i++) {
      var layers = (nodes[i].getAttribute('data-layers') || '').split(' ');
      nodes[i].style.display = (layers.indexOf(mode) !== -1) ? '' : 'none';
    }
    clearFocus();
  }

  function clearFocus() {
    svg.classList.remove('v5-has-focus');
    var marked = svg.querySelectorAll('.v5-focus');
    for (var i = 0; i < marked.length; i++) {
      marked[i].classList.remove('v5-focus');
    }
  }

  // 整条高亮（§3.7）：点击任一元素 → 同 data-partition-id 的组全部高亮、其余压暗；再点取消。
  svg.addEventListener('click', function (ev) {
    var t = ev.target;
    var g = (t && t.closest) ? t.closest('g.v5-part') : null;
    var wasFocused = g && g.classList.contains('v5-focus');
    clearFocus();
    if (g && !wasFocused) {
      var pid = g.getAttribute('data-partition-id');
      svg.classList.add('v5-has-focus');
      var parts = svg.querySelectorAll('g.v5-part');
      for (var i = 0; i < parts.length; i++) {
        if (parts[i].getAttribute('data-partition-id') === pid) {
          parts[i].classList.add('v5-focus');
        }
      }
    }
  });

  // 悬浮 tooltip：只读引擎写死的 data-* 预算值展示（前端只显示不判定）。
  svg.addEventListener('mousemove', function (ev) {
    var t = ev.target;
    var g = (t && t.closest) ? t.closest('g.v5-part') : null;
    if (!g) { tip.style.display = 'none'; return; }
    var at = function (name) { return g.getAttribute(name) || ''; };
    tip.textContent = [
      '分区 ' + at('data-partition-id') + ' [' + at('data-ptype') + ']',
      '层策略: ' + at('data-layer-policy'),
      '宽度先验: ' + at('data-w-min') + ' - ' + at('data-w-max') + ' mm',
      '电流: ' + at('data-current-a') + ' A',
      '速度等级: ' + at('data-speed-class')
    ].join('\\n');
    tip.style.display = 'block';
    tip.style.left = (ev.clientX + 14) + 'px';
    tip.style.top = (ev.clientY + 14) + 'px';
  });

  svg.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
  solo.addEventListener('change', applySolo);
  applySolo();
})();"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<title>v5 L1 分区图 — __BOARD_ID__</title>
<style>
__CSS__
</style>
</head>
<body>
<div id="v5-toolbar"><label for="v5-layer-solo">层 solo：</label><select id="v5-layer-solo">__OPTIONS__</select><span id="v5-hint">点击分区=整条高亮（再点取消）；悬浮=引擎预算值（只显示不重算）</span></div>
<div id="v5-stage">
__SVG__
</div>
<div id="v5-tooltip"></div>
<script>
__JS__
</script>
</body>
</html>
"""


def render_l1_html(board, partition_table):
    """交互 HTML：内嵌 mode=all 的 L1 SVG + 原生 JS（层 solo / 整条高亮 / 预算 tooltip）。

    独立单文件（无外链、无构建链）；确定性：同输入双跑字节相等。
    """
    svg = render_l1_view(board, partition_table, "all")
    options = ['<option value="all" selected="selected">all（全层叠加）</option>']
    for lid in _layer_ids(board.get("stackup", []) or []):
        options.append('<option value="%s">%s</option>' % (_esc(lid), _esc(lid)))
    return (_HTML_TEMPLATE
            .replace("__CSS__", _VIEW_CSS)
            .replace("__BOARD_ID__", _esc(board.get("board_id", "")))
            .replace("__OPTIONS__", "".join(options))
            .replace("__SVG__", svg)
            .replace("__JS__", _VIEW_JS))


# ---------------------------------------------------------------- 落盘（§3.5）

def _sniff_ext(payload):
    head = payload.lstrip()[:64].lower()
    if head.startswith("<svg"):
        return "svg"
    if head.startswith("<!doctype") or head.startswith("<html"):
        return "html"
    raise ValueError(
        "write_view: 无法识别的 payload（只收 render_l1/l2/l3_view 的 SVG 或"
        " render_l1_html 的 HTML）")


def _check_token(value, what):
    if not isinstance(value, str) or not _TOKEN_RE.match(value) or value in (".", ".."):
        raise ValueError("write_view: 非法 %s=%r（只准 [A-Za-z0-9._-] 且不为点号）" % (what, value))


def write_view(payload, kind, board_id, board_sha256, out_dir):
    """视图 sidecar 落盘（§3.5 卫生）。

    - 路径：只准写 sidecar.ALLOWED_ROOTS（out/）之下，越界抛 SidecarViolation；
    - 命名：``<board-id>.<kind>.<svg|html>``（sidecar.sidecar_name；扩展名由
      payload 形态嗅探：``<svg`` → svg，``<!doctype``/``<html`` → html）；
    - provenance 头：首行 HTML 注释（generator/generator_version/board_sha256
      三键与 sidecar.PROVENANCE_KEYS 同名）。**已验证口径**：tools/check_sidecar.py
      与 sidecar.check_file 只对 .json 解析 provenance 头、对其它扩展名只查路径，
      故文本 sidecar 保持检查 GREEN 的充分条件 = 路径在 ALLOWED_ROOTS 下；
      本头是为满足 §3.5「每个 sidecar 头部带 provenance」的文本形态落法。

    返回写入路径。
    """
    ext = _sniff_ext(payload)
    _check_token(kind, "kind")
    _check_token(board_id, "board_id")
    if not isinstance(board_sha256, str) or not _SHA_RE.match(board_sha256):
        raise ValueError("write_view: board_sha256 必须为 64 位小写 hex，实得 %r"
                         % (board_sha256,))
    path = os.path.join(out_dir, sidecar.sidecar_name(board_id, kind, ext))
    sidecar.assert_allowed(path)
    os.makedirs(out_dir, exist_ok=True)
    header = ("<!-- v5.view provenance generator=%s generator_version=%s"
              " board_sha256=%s board_id=%s kind=%s -->"
              % (GENERATOR, VERSION, board_sha256, board_id, kind))
    with open(path, "wb") as f:
        f.write((header + "\n" + payload).encode("utf-8"))
    return path


# ================================================================= P4：L7 布线图 / 爆炸分解 / L6 候选对比
# （2026-09-13 P4 第⑦路追加；任务书 §3.7 + P4 门「爆炸分解视图与 L7 布线图（过孔双环）
#  渲染正确」。追加式交付：以上既有函数/常量零改动，新常量/新函数全部在本节。）
#
# 上游合同 v5.routes.v1（与⑤执行器⑥导出器同锁，逐字消费）：
#   {"schema_version": "v5.routes.v1", "board_id": <str>, "board_sha256": <64hex>,
#    "routes": [{"partition_id","net_id","layer","polyline","width",
#                "transition_vias","return_vias"}, ...],
#    "negotiation_log": [<str>],
#    "provenance": {"generator": "v5.executor/…", "board_sha256": <64hex>}}
# 视图只消费不判定（§3.7）；形状/对账不符一律 ValueError fail-closed（带键路径）。
#
# 文档化最小决定（本节新增，均因合同无对应字段而取保守口径）：
# 1. 过孔双环取**所属路线的层色**（合同无 per-via 目标层字段，"两连接层各取一色"
#    需目标层信息，暂以单层色双环代替；形状语义由实心/空心区分 transition/return，
#    图例放地图区右上角白底盒——底部图例带已被 ptype+层图例占满，追加式不改常量）。
# 2. L7 底图分区=**板级 partitions**（render_l7_view 签名无分区表参数；routes 的
#    partition_id 引用板级分区，executor 以板为输入）。底图机制原样复用 _open_l1_base
#    （传只含 partitions 的 shim 表，不参与 hash 对账——板自身即对账基准）。
# 3. 爆炸分解面板序=stackup 声明序（顶→底）；只给 kind=="signal" 的层画面板（§3.7
#    「平面层只画极淡灰底不画线」）；共享 x 轴=各面板同宽同缩放（等比，min 取整宽）。
# 4. 爆炸分解跨面板连线只对 transition via 画（换层语义）；配对判据=同 net_id 或
#    同 partition_id（二取一；覆盖多段网跨分区衔接孔与 DIFF 共端点逃逸孔两类
#    executor 真实形态）、异层、且同一坐标点出现在对方 transition_vias 或折线顶点
#    （精确相等，同一执行器产出的同点浮点逐位一致）；每对只画一条（按面板序去重）；
#    孤儿 transition via（无配对）fail-closed。return via 无目标层语义，只画面板内
#    空心环。
# 5. L6 候选形状=planner 消费合同（candidate_id/arm/provenance/route_order/
#    layer_assignment/polylines/generation_trace）；候选无板 hash 字段，无法 hash
#    对账，只做分区/层命中 fail-closed。arm 不枚举硬校验（席位 B shadow 臂令牌未
#    在本视图消费的合同中定死），只要求非空字符串、原样展示。
# 6. 层合法性口径与 planner._signal_layer_ids 同锁：kind=="signal" 且 available is True。

ROUTES_SCHEMA = "v5.routes.v1"

# 过孔双环符号（px，固定值参与确定性字节等）
VIA_R_OUT = 4.2          # 外环半径
VIA_R_IN = 2.0           # 内环/实心芯半径
VIA_STROKE_W = 1.6       # 外环描边宽
ROUTE_OPACITY = "0.75"   # §3.7：走线透明 ~0.75，重叠处下层可见

# 爆炸分解版面（px，固定值）
EXPL_GAP = 8.0           # 面板间距
EXPL_TITLE_H = 16.0      # 面板标题条高（面板标题=层 id）
EXPL_TOP_PAD = 14.0
EXPL_BOTTOM_PAD = 14.0

# L6 候选对比版面（px，固定值）
L6_GAP = 10.0            # 面板间距
L6_TITLE_H = 18.0        # 面板标题条高（candidate_id（arm））


def _finite_num(value):
    """有限数值（bool 不算数；NaN/±inf 排除——防 _fmt 产出 nan 毒化 SVG）。"""
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and value == value
            and value != float("inf") and value != float("-inf"))


def _check_pt(pt, keypath):
    """[x,y] 点校验，返回 [float(x), float(y)]；不符带键路径 fail-closed。"""
    if not isinstance(pt, (list, tuple)) or len(pt) != 2:
        raise ValueError("%s 须为 [x,y] 二元组，得到 %r" % (keypath, pt))
    for v in pt:
        if not _finite_num(v):
            raise ValueError("%s 坐标须为有限数值，得到 %r" % (keypath, pt))
    return [float(pt[0]), float(pt[1])]


def _signal_layer_ids_strict(board):
    """可用信号层（与 planner._signal_layer_ids 同锁：kind==signal 且 available is True）。"""
    return [str(layer.get("id", "")) for layer in board.get("stackup", []) or []
            if layer.get("kind") == "signal" and layer.get("available") is True]


def _board_partition_ids(board):
    return {str(p.get("partition_id", "")) for p in board.get("partitions", []) or []}


def _board_net_partitions(board):
    """{net_id: [partition_id,...]}（routes 分区×净交叉对账用）。"""
    return {str(net.get("net_id", "")): [str(x) for x in (net.get("partitions") or [])]
            for net in board.get("nets", []) or []}


def _check_routes_doc(board, routes_doc, fn):
    """v5.routes.v1 形状轻校验（fail-closed 带键路径；数值合法性属⑤⑥，视图只查
    形状+对账+可画性）。返回逐条归一化（点全 float）的 routes 列表。"""
    if not isinstance(routes_doc, dict):
        raise ValueError("%s: routes 须为 dict，得到 %s"
                         % (fn, type(routes_doc).__name__))
    if routes_doc.get("schema_version") != ROUTES_SCHEMA:
        raise ValueError("%s: routes.schema_version=%r 须为 %r"
                         % (fn, routes_doc.get("schema_version"), ROUTES_SCHEMA))
    board_sha = (board.get("provenance", {}) or {}).get("board_sha256")
    if routes_doc.get("board_id") != board.get("board_id"):
        raise ValueError("%s: routes.board_id=%r 与板 board_id=%r 不符（fail-closed）"
                         % (fn, routes_doc.get("board_id"), board.get("board_id")))
    if routes_doc.get("board_sha256") != board_sha:
        raise ValueError("%s: routes.board_sha256=%r 与板 provenance.board_sha256"
                         " 对账失败（fail-closed）" % (fn, routes_doc.get("board_sha256")))
    log = routes_doc.get("negotiation_log")
    if not isinstance(log, list) or any(not isinstance(s, str) for s in log):
        raise ValueError("%s: routes.negotiation_log 须为字符串数组" % fn)
    prov = routes_doc.get("provenance")
    if not isinstance(prov, dict) or not str(prov.get("generator", "")):
        raise ValueError("%s: routes.provenance.generator 须为非空字符串" % fn)
    if prov.get("board_sha256") != board_sha:
        raise ValueError("%s: routes.provenance.board_sha256 与板对账失败（fail-closed）" % fn)

    routes = routes_doc.get("routes")
    if not isinstance(routes, list):
        raise ValueError("%s: routes.routes 须为列表" % fn)
    part_ids = _board_partition_ids(board)
    net_parts = _board_net_partitions(board)
    signal_ids = _signal_layer_ids_strict(board)
    checked = []
    for i, entry in enumerate(routes):
        base = "%s: routes[%d]" % (fn, i)
        if not isinstance(entry, dict):
            raise ValueError("%s 须为对象" % base)
        pid = entry.get("partition_id")
        if not isinstance(pid, str) or not pid or pid not in part_ids:
            raise ValueError("%s.partition_id=%r 须为板级分区 id（现有: %s）"
                             % (base, pid, ",".join(sorted(part_ids)) or "<无>"))
        nid = entry.get("net_id")
        if not isinstance(nid, str) or not nid or nid not in net_parts:
            raise ValueError("%s.net_id=%r 须为板级净 id（现有: %s）"
                             % (base, nid, ",".join(sorted(net_parts)) or "<无>"))
        if pid not in net_parts[nid]:
            raise ValueError("%s 交叉对账失败：分区 %r 不在净 %r 的 partitions %s 中"
                             % (base, pid, nid, net_parts[nid]))
        layer = entry.get("layer")
        if layer not in signal_ids:
            raise ValueError("%s.layer=%r 须为 stackup 可用信号层（现有: %s）"
                             % (base, layer, ",".join(signal_ids) or "<无>"))
        poly = entry.get("polyline")
        if not isinstance(poly, list) or len(poly) < 2:
            raise ValueError("%s.polyline 须为 ≥2 点折线，得到 %r" % (base, poly))
        pts = [_check_pt(pt, "%s.polyline[%d]" % (base, j)) for j, pt in enumerate(poly)]
        width = entry.get("width")
        if not _finite_num(width) or width <= 0:
            raise ValueError("%s.width 须为 >0 的有限数值，得到 %r" % (base, width))
        vias = {}
        for key in ("transition_vias", "return_vias"):
            raw = entry.get(key, [])
            if not isinstance(raw, list):
                raise ValueError("%s.%s 须为列表，得到 %r" % (base, key, raw))
            vias[key] = [_check_pt(pt, "%s.%s[%d]" % (base, key, j))
                         for j, pt in enumerate(raw)]
        checked.append({"partition_id": pid, "net_id": nid, "layer": layer,
                        "polyline": pts, "width": float(width),
                        "transition_vias": vias["transition_vias"],
                        "return_vias": vias["return_vias"]})
    return checked


def _render_via(kind, pt, plane, color, pid, nid, lid):
    """过孔双环符号：transition=实心双环（外环白底 + 内芯实心层色）；
    return=空心双环（外环白底 + 内环空心）。双环白底遮下层走线保可读。"""
    cx, cy = plane.x(pt[0]), plane.y(pt[1])
    lines = ['<g class="v5-via" data-via-kind="%s" data-partition-id="%s"'
             ' data-net-id="%s" data-layer="%s">'
             % (_esc(kind), pid, nid, lid)]
    lines.append('<circle cx="%s" cy="%s" r="%s" fill="#ffffff" stroke="%s"'
                 ' stroke-width="%s"/>' % (cx, cy, VIA_R_OUT, color, VIA_STROKE_W))
    if kind == "transition":
        lines.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s"'
                     ' stroke-width="1"/>' % (cx, cy, VIA_R_IN, color, color))
    else:
        lines.append('<circle cx="%s" cy="%s" r="%s" fill="#ffffff" stroke="%s"'
                     ' stroke-width="1"/>' % (cx, cy, VIA_R_IN, color))
    lines.append("</g>")
    return lines


def _render_route_lines(entry, plane, stackup):
    """单条 route（折线 + 双环过孔）：按层着色/线型，stroke-width=投影后 width
    （线宽=width 语义原样投影，不钳制）；整条高亮钩子 data-partition-id/data-net-id。"""
    pid = _esc(entry["partition_id"])
    nid = _esc(entry["net_id"])
    lid = _esc(entry["layer"])
    color = layer_color(stackup, entry["layer"])
    dash = layer_dash(stackup, entry["layer"])
    dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
    pts = " ".join("%s,%s" % (plane.x(p[0]), plane.y(p[1]))
                   for p in entry["polyline"])
    lines = ['<g class="v5-route" data-partition-id="%s" data-net-id="%s"'
             ' data-layer="%s" data-layers="%s" data-width="%s" data-via-t="%d"'
             ' data-via-r="%d">'
             % (pid, nid, lid, _vis_attr([entry["layer"]]), _fmt(entry["width"]),
                len(entry["transition_vias"]), len(entry["return_vias"]))]
    lines.append('<polyline class="v5-route-line" points="%s" fill="none" stroke="%s"'
                 ' stroke-width="%s" stroke-opacity="%s" stroke-linejoin="round"'
                 ' stroke-linecap="round"%s/>'
                 % (pts, color, plane.w(entry["width"]), ROUTE_OPACITY, dash_attr))
    for kind, key in (("transition", "transition_vias"), ("return", "return_vias")):
        for pt in entry[key]:
            lines.extend(_render_via(kind, pt, plane, color, pid, nid, lid))
    lines.append("</g>")
    return lines


def _render_via_legend():
    """过孔图例（双环符号）：地图区右上角白底盒（底部图例带已被 ptype+层图例占满，
    追加式不改既有常量）；样例色取中性深灰（层色见层图例）。"""
    x = VIEW_W - MARGIN - 196
    y = MARGIN + 6
    ink = "#333333"
    lines = ['<g id="via-legend" data-kind="via-legend">']
    lines.append('<rect x="%d" y="%d" width="196" height="54" fill="#ffffff"'
                 ' stroke="#262626" stroke-width="1"/>' % (x, y))
    lines.append('<text x="%d" y="%d" font-size="11" font-weight="bold" fill="#262626">'
                 '过孔图例（双环符号）</text>' % (x + 8, y + 14))
    lines.append('<circle cx="%d" cy="%d" r="%s" fill="#ffffff" stroke="%s"'
                 ' stroke-width="%s"/>' % (x + 16, y + 28, VIA_R_OUT, ink, VIA_STROKE_W))
    lines.append('<circle cx="%d" cy="%d" r="%s" fill="%s" stroke="%s" stroke-width="1"/>'
                 % (x + 16, y + 28, VIA_R_IN, ink, ink))
    lines.append('<text x="%d" y="%d" font-size="10" fill="#333333">'
                 'transition 换层（实心双环）</text>' % (x + 30, y + 32))
    lines.append('<circle cx="%d" cy="%d" r="%s" fill="#ffffff" stroke="%s"'
                 ' stroke-width="%s"/>' % (x + 16, y + 46, VIA_R_OUT, ink, VIA_STROKE_W))
    lines.append('<circle cx="%d" cy="%d" r="%s" fill="#ffffff" stroke="%s"'
                 ' stroke-width="1"/>' % (x + 16, y + 46, VIA_R_IN, ink))
    lines.append('<text x="%d" y="%d" font-size="10" fill="#333333">'
                 'return 回流（空心双环）</text>' % (x + 30, y + 50))
    lines.append("</g>")
    return lines


def render_l7_view(board, routes_doc, mode="all"):
    """渲染 L7 布线图 SVG 字符串（§3.7：L7 布线图（逐层切换）；P4 门：过孔双环）。

    - 底图：板级 partitions + zones 照 L1 口径（复用 _open_l1_base；文档化决定 2）；
    - routes 折线：按层着色/线型、stroke-width=width、透明 0.75；mode="all" 全层
      叠加（自底向上绘制）或单层 id 只画该层 routes（底图过滤同 L1 口径）；
    - 过孔双环：transition 实心双环 / return 空心双环（所属路线层色；图例区分）。
    同输入双跑字节相等。
    """
    stackup = board.get("stackup", []) or []
    entries = _check_routes_doc(board, routes_doc, "render_l7_view")
    base_table = {"partitions": list(board.get("partitions", []) or [])}
    out, plane = _open_l1_base(board, base_table, mode,
                               "v5-l7-view", "l7-routes", "v5 L7 布线图")
    draw_stack = list(reversed(_layer_ids(stackup)))
    visible = [e for e in entries if mode == "all" or e["layer"] == mode]

    def _draw_key(e):
        idx = draw_stack.index(e["layer"]) if e["layer"] in draw_stack else len(draw_stack)
        return (idx, e["partition_id"], e["net_id"])

    for e in sorted(visible, key=_draw_key):
        out.extend(_render_route_lines(e, plane, stackup))
    out.extend(_render_legends(stackup))
    out.extend(_render_via_legend())
    out.append("</svg>")
    return "\n".join(out)


def _via_partner(entries, idx, pt, stackup):
    """transition via 的跨层配对条目下标（文档化决定 4）：同 net_id **或** 同
    partition_id（二取一即可）、异层、同一坐标点（精确相等）出现在对方
    transition_vias 或折线顶点；多个命中取 stackup 序最小（防御性确定序）。
    无配对 → -1（调用方 fail-closed）。

    放宽依据（集成冒烟 demo-02 DF1 实证，executor 真实合同的两类形态）：
    ① 多段网跨分区衔接孔——同网异分区两侧 entry 双侧披露该点；② DIFF/共端点
    分区逃逸孔——焊盘固定铜不在 routes 中，过孔对焊盘的换层只能配到同分区
    另一网折线的共享端点顶点（net 不同、partition 相同）。"""
    entry = entries[idx]
    ids = _layer_ids(stackup)
    best, best_key = -1, None
    for j, other in enumerate(entries):
        if j == idx:
            continue
        if other["layer"] == entry["layer"]:
            continue
        if (other["net_id"] != entry["net_id"]
                and other["partition_id"] != entry["partition_id"]):
            continue
        hit = (any(p == pt for p in other["transition_vias"])
               or any(p == pt for p in other["polyline"]))
        if not hit:
            continue
        key = (ids.index(other["layer"]) if other["layer"] in ids else len(ids), j)
        if best_key is None or key < best_key:
            best_key, best = key, j
    return best


def render_exploded_view(board, routes_doc):
    """渲染爆炸分解视图 SVG 字符串（§3.7 模式 2：各层同坐标轴纵向堆叠多面板 +
    过孔跨面板连线；P4 引入）。

    - 面板：每信号层一个（stackup 声明序顶→底），共享 x 轴（同宽同缩放），面板
      标题=层 id（层色）；每面板内画 zones（按 zone.layers 过滤）+ 工作区边界 +
      该层 routes 折线与过孔环；
    - 跨面板连线：transition via 同 x 位置从层面板 A 连到配对面板 B（配对判据见
      _via_partner；每对一条，孤儿 fail-closed）；return via 只画面板内空心环。
    同输入双跑字节相等。
    """
    fn = "render_exploded_view"
    stackup = board.get("stackup", []) or []
    entries = _check_routes_doc(board, routes_doc, fn)
    panels = [str(layer.get("id", "")) for layer in stackup
              if layer.get("kind") == "signal"]
    if not panels:
        raise ValueError("%s: stackup 无 kind==signal 层，无法爆炸分解" % fn)
    workspace = board["workspace"]
    box_w = VIEW_W - 2 * MARGIN
    total_h = (VIEW_H - EXPL_BOTTOM_PAD) - EXPL_TOP_PAD
    panel_h = (total_h - (len(panels) - 1) * EXPL_GAP) / len(panels)
    planes = {}
    for i, lid in enumerate(panels):
        py = EXPL_TOP_PAD + i * (panel_h + EXPL_GAP)
        planes[lid] = _Plane(workspace, MARGIN, py + EXPL_TITLE_H, box_w,
                             panel_h - EXPL_TITLE_H)
    board_id = _esc(board.get("board_id", ""))
    board_sha = _esc((board.get("provenance", {}) or {}).get("board_sha256", ""))

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" id="v5-exploded-view"'
               ' data-v5="l7-exploded" data-board-id="%s" data-board-sha256="%s"'
               ' viewBox="0 0 %d %d" width="%d" height="%d">'
               % (board_id, board_sha, VIEW_W, VIEW_H, VIEW_W, VIEW_H))
    out.append('<title>v5 爆炸分解 %s</title>' % board_id)
    out.append('<desc>v5.view 确定性渲染；所有数值为引擎预计算，前端只显示不判定（§3.7）。</desc>')
    # 禁布斜线 pattern 定义：与 _open_l1_base 内联 defs 同文（追加式不可抽公共常量，
    # 复制一份；面板 zones 复用 _render_zone 会引用 #v5-hatch-keepout，缺 defs 即空填充）。
    out.append('<defs>'
               '<pattern id="v5-hatch-keepout" width="8" height="8"'
               ' patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
               '<rect x="0" y="0" width="8" height="8" fill="#ffffff"/>'
               '<line x1="0" y1="0" x2="0" y2="8" stroke="#cc0000" stroke-width="2"/>'
               '</pattern></defs>')
    out.append('<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (VIEW_W, VIEW_H))

    for i, lid in enumerate(panels):
        py = EXPL_TOP_PAD + i * (panel_h + EXPL_GAP)
        plane = planes[lid]
        color = layer_color(stackup, lid)
        dash = layer_dash(stackup, lid)
        dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
        out.append('<g class="v5-expanel" data-panel="%d" data-layer="%s">'
                   % (i, _esc(lid)))
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"'
                   ' stroke="#262626" stroke-width="1"/>'
                   % (_fmt(MARGIN), _fmt(py), _fmt(box_w), _fmt(panel_h)))
        out.append('<text class="v5-expanel-title" x="%s" y="%s" font-size="12"'
                   ' font-weight="bold" fill="%s">%s</text>'
                   % (_fmt(MARGIN + 6), _fmt(py + 12), color, _esc(lid)))
        # 层色/线型样本（面板标题旁，双编码照层图例口径）
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"'
                   ' stroke-width="3"%s/>'
                   % (_fmt(MARGIN + 90), _fmt(py + 8), _fmt(MARGIN + 116), _fmt(py + 8),
                      color, dash_attr))
        for zone in sorted(board.get("zones", []) or [],
                           key=lambda z: str(z.get("zone_id", ""))):
            if lid in _zone_visible_layers(zone.get("layers", "all"), stackup):
                out.extend(_render_zone(zone, plane, stackup, [lid]))
        out.append('<rect id="workspace-frame-p%d" x="%s" y="%s" width="%s" height="%s"'
                   ' fill="none" stroke="#262626" stroke-width="1.5"/>'
                   % (i, plane.x(workspace["x_min"]), plane.y(workspace["y_min"]),
                      plane.w(float(workspace["x_max"]) - float(workspace["x_min"])),
                      plane.w(float(workspace["y_max"]) - float(workspace["y_min"]))))
        layer_entries = [e for e in entries if e["layer"] == lid]
        for e in sorted(layer_entries, key=lambda e: (e["partition_id"], e["net_id"])):
            out.extend(_render_route_lines(e, plane, stackup))
        out.append("</g>")

    # 跨面板连线（overlay 后画，跨面板边框可见）；每对只画一条（按配对键去重，
    # entry 序先到先画——配对可不对称：via 只在owner entry 名下披露，同分区异网
    # 配对与焊盘逃逸孔均无「对侧迭代」保证，不能用面板序单向跳过）。
    # 无 entry 配对的过渡孔按焊盘逃逸孔处置（决定 4b）：该点=本分区端点（板合同
    # 「所有端点均为焊盘、位于首信号层面」）时，跨面板连线画向垫层面板（stackup
    # 首信号层）；点不在端点上仍 fail-closed。本层即垫层的逃逸孔无垂直跨度，不画线。
    pad_layer = panels[0]
    part_eps = {}
    for p in board.get("partitions", []) or []:
        eps = (p.get("geometry", {}) or {}).get("endpoints") or []
        part_eps[str(p.get("partition_id", ""))] = [list(e) for e in eps]
    drawn = set()
    for i, entry in enumerate(entries):
        for pt in entry["transition_vias"]:
            j = _via_partner(entries, i, pt, stackup)
            if j >= 0:
                partner_layer = entries[j]["layer"]
                key = (min(i, j), max(i, j), tuple(pt))
                if key in drawn:
                    continue
                drawn.add(key)
            elif any(e == pt for e in part_eps.get(entry["partition_id"], [])):
                partner_layer = pad_layer  # 焊盘逃逸孔（决定 4b）
            else:
                raise ValueError(
                    "%s: routes[%d].transition_vias 孤儿过孔 %r"
                    "（同 net_id 或同 partition_id 的异层条目 transition_vias"
                    "/折线顶点、本分区端点均无该点；上游不一致，fail-closed）"
                    % (fn, i, pt))
            if entry["layer"] == partner_layer:
                continue  # 本层即垫层的逃逸孔无垂直跨度
            x = planes[entry["layer"]].x(pt[0])
            y1 = planes[entry["layer"]].y(pt[1])
            y2 = planes[partner_layer].y(pt[1])
            color = layer_color(stackup, entry["layer"])
            out.append('<line class="v5-exvia-link" x1="%s" y1="%s" x2="%s" y2="%s"'
                       ' stroke="%s" stroke-width="1.2" stroke-dasharray="3,3"'
                       ' data-partition-id="%s" data-net-id="%s"/>'
                       % (x, y1, x, y2, color, _esc(entry["partition_id"]),
                          _esc(entry["net_id"])))
            for yy in (y1, y2):
                out.append('<circle cx="%s" cy="%s" r="2" fill="%s"/>'
                           % (x, yy, color))
    out.append("</svg>")
    return "\n".join(out)


def _check_candidates(board, candidates):
    """L6 候选形状轻校验（planner 消费合同子集；fail-closed 带键路径）。返回归一化
    候选列表。候选无板 hash 字段（planner 合同），无法 hash 对账，只做分区/层命中。"""
    fn = "render_l6_view"
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("%s: candidates 须为非空列表，得到 %s"
                         % (fn, type(candidates).__name__))
    part_ids = _board_partition_ids(board)
    signal_ids = _signal_layer_ids_strict(board)
    checked = []
    for i, cand in enumerate(candidates):
        base = "%s: candidates[%d]" % (fn, i)
        if not isinstance(cand, dict):
            raise ValueError("%s 须为 dict，得到 %s" % (base, type(cand).__name__))
        cid = cand.get("candidate_id")
        if not isinstance(cid, str) or not cid:
            raise ValueError("%s.candidate_id 须为非空字符串，得到 %r" % (base, cid))
        arm = cand.get("arm")
        if not isinstance(arm, str) or not arm:
            raise ValueError("%s.arm 须为非空字符串，得到 %r" % (base, arm))
        order = cand.get("route_order")
        if (not isinstance(order, list) or not order
                or any(not isinstance(x, str) or not x for x in order)):
            raise ValueError("%s.route_order 须为非空分区 id 字符串数组，得到 %r"
                             % (base, order))
        if len(order) != len(set(order)):
            raise ValueError("%s.route_order 含重复分区" % base)
        assign = cand.get("layer_assignment")
        polys = cand.get("polylines")
        if not isinstance(assign, dict):
            raise ValueError("%s.layer_assignment 须为 dict，得到 %s"
                             % (base, type(assign).__name__))
        if not isinstance(polys, dict):
            raise ValueError("%s.polylines 须为 dict，得到 %s"
                             % (base, type(polys).__name__))
        if sorted(map(str, assign)) != sorted(order):
            raise ValueError("%s.layer_assignment 键 %s 须恰为 route_order 分区 %s"
                             % (base, sorted(map(str, assign)), sorted(order)))
        if sorted(map(str, polys)) != sorted(order):
            raise ValueError("%s.polylines 键 %s 须恰为 route_order 分区 %s"
                             % (base, sorted(map(str, polys)), sorted(order)))
        norm_polys = {}
        for n, pid in enumerate(order):
            if pid not in part_ids:
                raise ValueError("%s.route_order[%d]=%r 未命中板级分区（现有: %s）"
                                 % (base, n, pid, ",".join(sorted(part_ids)) or "<无>"))
            layer = assign[pid]
            if layer not in signal_ids:
                raise ValueError("%s.layer_assignment[%s]=%r 须为 stackup 可用信号层"
                                 "（现有: %s）" % (base, pid, layer,
                                                  ",".join(signal_ids) or "<无>"))
            poly = polys[pid]
            if not isinstance(poly, list) or len(poly) < 2:
                raise ValueError("%s.polylines[%s] 须为 ≥2 点折线，得到 %r"
                                 % (base, pid, poly))
            norm_polys[pid] = [_check_pt(pt, "%s.polylines[%s][%d]" % (base, pid, k))
                               for k, pt in enumerate(poly)]
        checked.append({"candidate_id": cid, "arm": arm, "route_order": list(order),
                        "layer_assignment": {pid: str(assign[pid]) for pid in order},
                        "polylines": norm_polys})
    return checked


def render_l6_view(board, candidates):
    """渲染 L6 候选对比图 SVG 字符串（§3.7：L6 候选对比图（三臂并排））。

    每候选一个并排小面板：面板标题=``candidate_id（arm）``；面板内画该候选全部
    分区端点连线（polylines，P3 合同=端点直线），层着色/线型（layer_assignment），
    每分区带 route_order 序号标注（``n.partition_id``）；底部共用 ptype+层图例。
    候选按输入序（注册序）排列，不重排。同输入双跑字节相等。
    """
    stackup = board.get("stackup", []) or []
    cands = _check_candidates(board, candidates)
    n = len(cands)
    region_w = VIEW_W - 2 * MARGIN
    top = MARGIN
    panel_h = (VIEW_H - LEGEND_BAND) - MARGIN - 6
    panel_w = (region_w - (n - 1) * L6_GAP) / n
    workspace = board["workspace"]
    board_id = _esc(board.get("board_id", ""))
    board_sha = _esc((board.get("provenance", {}) or {}).get("board_sha256", ""))

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" id="v5-l6-view"'
               ' data-v5="l6-candidates" data-board-id="%s" data-board-sha256="%s"'
               ' data-candidate-count="%d" viewBox="0 0 %d %d" width="%d" height="%d">'
               % (board_id, board_sha, n, VIEW_W, VIEW_H, VIEW_W, VIEW_H))
    out.append('<title>v5 L6 候选对比 %s</title>' % board_id)
    out.append('<desc>v5.view 确定性渲染；所有数值为引擎预计算，前端只显示不判定（§3.7）。</desc>')
    out.append('<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (VIEW_W, VIEW_H))
    for i, cand in enumerate(cands):
        px = MARGIN + i * (panel_w + L6_GAP)
        plane = _Plane(workspace, px, top + L6_TITLE_H, panel_w,
                       panel_h - L6_TITLE_H)
        cid = _esc(cand["candidate_id"])
        arm = _esc(cand["arm"])
        out.append('<g class="v5-l6-panel" data-panel="%d" data-candidate-id="%s"'
                   ' data-arm="%s">' % (i, cid, arm))
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"'
                   ' stroke="#262626" stroke-width="1"/>'
                   % (_fmt(px), _fmt(top), _fmt(panel_w), _fmt(panel_h)))
        out.append('<text class="v5-l6-title" x="%s" y="%s" font-size="11"'
                   ' font-weight="bold" fill="#262626">%s（%s）</text>'
                   % (_fmt(px + 6), _fmt(top + 13), cid, arm))
        out.append('<rect id="workspace-frame-c%d" x="%s" y="%s" width="%s" height="%s"'
                   ' fill="none" stroke="#262626" stroke-width="1.5"/>'
                   % (i, plane.x(workspace["x_min"]), plane.y(workspace["y_min"]),
                      plane.w(float(workspace["x_max"]) - float(workspace["x_min"])),
                      plane.w(float(workspace["y_max"]) - float(workspace["y_min"]))))
        for order_n, pid in enumerate(cand["route_order"]):
            pts = cand["polylines"][pid]
            lid = cand["layer_assignment"][pid]
            color = layer_color(stackup, lid)
            dash = layer_dash(stackup, lid)
            dash_attr = ' stroke-dasharray="%s"' % dash if dash else ""
            pid_esc = _esc(pid)
            points = " ".join("%s,%s" % (plane.x(p[0]), plane.y(p[1])) for p in pts)
            out.append('<g class="v5-l6-route" data-candidate-id="%s"'
                       ' data-partition-id="%s" data-order="%d" data-layer="%s">'
                       % (cid, pid_esc, order_n + 1, _esc(lid)))
            out.append('<polyline class="v5-l6-line" points="%s" fill="none"'
                       ' stroke="%s" stroke-width="2" stroke-opacity="0.75"'
                       ' stroke-linejoin="round" stroke-linecap="round"%s/>'
                       % (points, color, dash_attr))
            for p in pts:
                out.append('<circle cx="%s" cy="%s" r="3" fill="%s"/>'
                           % (plane.x(p[0]), plane.y(p[1]), color))
            out.append('<text class="v5-l6-order" x="%s" y="%s" font-size="9"'
                       ' fill="%s">%d.%s</text>'
                       % (plane.x(pts[0][0]), _fmt(float(plane.y(pts[0][1])) - 5.0),
                          color, order_n + 1, pid_esc))
            out.append("</g>")
        out.append("</g>")
    out.extend(_render_legends(stackup))
    out.append("</svg>")
    return "\n".join(out)


# ================================================================= P5③：L8 终解+diff+复查旗标视图
# （2026-09-13 P5③ 追加；任务书 §3.7「L8 终解+diff+复查旗标图」+ P5-G4 门
#  「L8 终解+diff+复查旗标视图渲染正确」。追加式交付：以上既有函数/常量零改动，
#  新常量/新函数全部在本节；VERSION 与任何既有函数未触碰。）
#
# 上游合同：两终解 = v5.routes.v1 工件（executor 产物，与 render_l7_view 同锁，
# 复用 _check_routes_doc 形状/对账校验）；flags = v5.threearm.review_flags 的旗标
# 列表（advisory，不阻塞渲染）。视图只消费不判定（§3.7）。
#
# 差异判定语义与 v5.threearm.diff_solutions（v5.soldiff.v1）同锁：按
# (partition_id, net_id) 键归并 entry（文档序），逐键比较 layer/polyline/width
# 三字段。本节内联实现比较而非 import threearm——保持 view 模块只依赖 sidecar
# 的既有形态（P4 节先例：追加式不可抽公共依赖，复制一份），两处语义漂移由
# tests/test_p5_threearm.py 的同板对账测试钉住。
#
# 文档化最小决定（本节新增）：
# 1. 差异高亮色沿用 conflict advisory 语义色（橙 #ff9900 + 短虚线 4,3）——终解
#    diff 是「复查建议」级信息（席位 C advisory 不阻塞），不占用 blocking 红；
#    差异轮廓 = 该 (分区,净) 键在 A/B 两解全部坐标点的联合包围盒外扩
#    L8_DIFF_PAD_PX，**两面板各画一条**（世界坐标同框，缺侧面板也画——
#    「B 缺该网」本身就是差异，轮廓指示同一世界位置便于肉眼对位）。
# 2. 复查旗标角标盒=地图区右上角白底盒（过孔图例同款位；追加式不改版面常量）：
#    每旗一行 flag_id + severity + 键 + 字段徽标文本，完整 note 进 data-note
#    （tooltip 数据位，前端只显示）；flags 为空 → 单行「无」。
# 3. 两面板共享世界坐标（各面板独立 _Plane 同 workspace 同盒尺寸），routes
#    复用 _render_route_lines（层色/线型/过孔双环与 L7 同款）；zones 复用
#    _render_zone（全层可见，禁布斜线 pattern 在本节内联 defs，P4 先例）。

# L8 diff 视图版面（px，固定值参与确定性字节等）
L8_DIFF_PAD_PX = 5.0     # 差异轮廓在联合包围盒外的固定外扩
L8_FLAG_BOX_W = 240.0    # 复查旗标角标盒宽
L8_FLAG_ROW_H = 13.0     # 旗标行高

L8_DIFF_STYLE = {"stroke": "#ff9900", "dash": "4,3"}  # advisory 语义色（决定 1）
L8_FIELD_LABELS = {"layer": "层", "path": "路径", "width": "宽度"}


def _l8_check_flags(flags):
    """flags 轻校验（fail-closed）：list/tuple，每项 dict 含非空 flag_id 字符串、
    severity 字符串（缺省 advisory）、note 字符串。返回归一化旗标列表。"""
    fn = "render_l8_diff_view"
    if not isinstance(flags, (list, tuple)):
        raise ValueError("%s: flags 须为 list/tuple，得到 %s"
                         % (fn, type(flags).__name__))
    rows = []
    for i, flag in enumerate(flags):
        base = "%s: flags[%d]" % (fn, i)
        if not isinstance(flag, dict):
            raise ValueError("%s 须为 dict，得到 %s" % (base, type(flag).__name__))
        fid = flag.get("flag_id")
        if not isinstance(fid, str) or not fid:
            raise ValueError("%s.flag_id 须为非空字符串，得到 %r" % (base, fid))
        severity = flag.get("severity", "advisory")
        if not isinstance(severity, str) or not severity:
            raise ValueError("%s.severity 须为非空字符串，得到 %r" % (base, severity))
        note = flag.get("note", "")
        if not isinstance(note, str):
            raise ValueError("%s.note 须为字符串，得到 %r" % (base, note))
        rows.append({"flag_id": fid, "severity": severity, "note": note,
                     "partition_id": flag.get("partition_id"),
                     "net_id": flag.get("net_id"),
                     "fields": flag.get("fields")})
    return rows


def _l8_key_map(entries):
    """entries 按 (partition_id, net_id) 归并（文档序）→ diff 比较用摘要表。"""
    keys = {}
    for e in entries:
        key = (e["partition_id"], e["net_id"])
        acc = keys.setdefault(key, {"layers": [], "polyline": [], "widths": []})
        acc["layers"].append(e["layer"])
        acc["polyline"].extend([list(pt) for pt in e["polyline"]])
        acc["widths"].append(e["width"])
    return keys


def _l8_differences(entries_a, entries_b):
    """两终解 entries 的差异清单（语义与 v5.threearm.diff_solutions 同锁）：
    [(key, fields 排序表, 联合世界坐标点集)]，按 key 字典序。"""
    ka, kb = _l8_key_map(entries_a), _l8_key_map(entries_b)
    out = []
    for key in sorted(set(ka) | set(kb)):
        ea, eb = ka.get(key), kb.get(key)
        if ea == eb:
            continue
        fields = []
        if (ea or {}).get("layers") != (eb or {}).get("layers"):
            fields.append("layer")
        if (ea or {}).get("polyline") != (eb or {}).get("polyline"):
            fields.append("path")
        if (ea or {}).get("widths") != (eb or {}).get("widths"):
            fields.append("width")
        pts = []
        for side in (ea, eb):
            for pt in (side or {}).get("polyline", []):
                pts.append((float(pt[0]), float(pt[1])))
        out.append((key, sorted(fields), pts))
    return out


def _l8_render_flags_box(flag_rows):
    """复查旗标角标盒（地图区右上角白底盒；决定 2）。flags 空 → 单行「无」。"""
    x = VIEW_W - MARGIN - L8_FLAG_BOX_W
    y = MARGIN + 6
    rows = flag_rows or []
    box_h = 22.0 + len(rows) * L8_FLAG_ROW_H + 6.0
    lines = ['<g id="l8-flag-box" data-kind="review-flags" data-flag-count="%d">'
             % len(rows)]
    lines.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"'
                 ' stroke="#262626" stroke-width="1"/>'
                 % (_fmt(x), _fmt(y), _fmt(L8_FLAG_BOX_W), _fmt(box_h)))
    lines.append('<text x="%s" y="%s" font-size="11" font-weight="bold"'
                 ' fill="#262626">席位 C 复查旗标（advisory 不阻塞）</text>'
                 % (_fmt(x + 8), _fmt(y + 14)))
    if not rows:
        lines.append('<text class="v5-l8-flag" x="%s" y="%s" font-size="10"'
                     ' fill="#333333">无</text>' % (_fmt(x + 8), _fmt(y + 27)))
    for i, row in enumerate(rows):
        ry = y + 27 + i * L8_FLAG_ROW_H
        keys = ""
        if row["partition_id"] is not None:
            keys = " %s/%s" % (row["partition_id"], row["net_id"])
        field_txt = ""
        if isinstance(row["fields"], list) and row["fields"]:
            field_txt = " [%s]" % ",".join(
                L8_FIELD_LABELS.get(f, f) for f in row["fields"])
        label = "%s %s%s%s" % (row["flag_id"], row["severity"], keys, field_txt)
        lines.append('<text class="v5-l8-flag" x="%s" y="%s" font-size="10"'
                     ' fill="#333333" data-flag-id="%s" data-severity="%s"'
                     ' data-note="%s">%s</text>'
                     % (_fmt(x + 8), _fmt(ry), _esc(row["flag_id"]),
                        _esc(row["severity"]), _esc(row["note"]), _esc(label)))
    lines.append("</g>")
    return lines


def render_l8_diff_view(board, solution_a, solution_b, flags=()):
    """渲染 L8 终解+diff+复查旗标图 SVG 字符串（§3.7：L8 终解+diff+复查旗标图；
    P5-G4 门交付，P5③ 追加节）。

    - 两终解（v5.routes.v1 工件）并排双面板：终解 A 左、终解 B 右；各面板画
      zones + 工作区边界 + routes（层色/线型/过孔双环与 L7 同款）；
    - 差异高亮：逐 (分区,净) 键比较 layer/path/width（语义与 v5.threearm.
      diff_solutions 同锁），差异键在两面板各画一条橙色短虚线轮廓（联合包围盒
      外扩，缺侧面板同位画）+「Δ 分区/净 [层,路径]」徽标文本；
    - 复查旗标角标盒：flags（v5.threearm.review_flags 产出形状）逐旗一行，
      advisory 不阻塞；flags=() 且无差异时盒内单行「无」；
    - 两终解零差异时面板间顶部居中徽标「两终解结构一致（无差异点）」。
    同输入双跑字节相等。
    """
    fn = "render_l8_diff_view"
    stackup = board.get("stackup", []) or []
    entries_a = _check_routes_doc(board, solution_a, fn)
    entries_b = _check_routes_doc(board, solution_b, fn)
    flag_rows = _l8_check_flags(flags)
    diffs = _l8_differences(entries_a, entries_b)

    board_id = _esc(board.get("board_id", ""))
    board_sha = _esc((board.get("provenance", {}) or {}).get("board_sha256", ""))
    workspace = board["workspace"]
    region_w = VIEW_W - 2 * MARGIN
    top = MARGIN
    panel_h = (VIEW_H - LEGEND_BAND) - top - 6
    panel_w = (region_w - L6_GAP) / 2.0
    plane_a = _Plane(workspace, MARGIN, top + L6_TITLE_H, panel_w,
                     panel_h - L6_TITLE_H)
    plane_b = _Plane(workspace, MARGIN + panel_w + L6_GAP, top + L6_TITLE_H,
                     panel_w, panel_h - L6_TITLE_H)
    all_layers = _layer_ids(stackup)

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" id="v5-l8-diff-view"'
               ' data-v5="l8-diff" data-board-id="%s" data-board-sha256="%s"'
               ' data-diff-count="%d" data-flag-count="%d"'
               ' viewBox="0 0 %d %d" width="%d" height="%d">'
               % (board_id, board_sha, len(diffs), len(flag_rows),
                  VIEW_W, VIEW_H, VIEW_W, VIEW_H))
    out.append('<title>v5 L8 终解 diff %s</title>' % board_id)
    out.append('<desc>v5.view 确定性渲染；所有数值为引擎预计算，前端只显示不判定（§3.7）。</desc>')
    # 禁布斜线 pattern：与 _open_l1_base 内联 defs 同文（P4 先例：追加式复制一份）
    out.append('<defs>'
               '<pattern id="v5-hatch-keepout" width="8" height="8"'
               ' patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
               '<rect x="0" y="0" width="8" height="8" fill="#ffffff"/>'
               '<line x1="0" y1="0" x2="0" y2="8" stroke="#cc0000" stroke-width="2"/>'
               '</pattern></defs>')
    out.append('<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (VIEW_W, VIEW_H))

    if not diffs:
        out.append('<text class="v5-l8-identical" x="%s" y="%s" font-size="11"'
                   ' text-anchor="middle" fill="#0066cc">两终解结构一致（无差异点）</text>'
                   % (_fmt(MARGIN + panel_w + L6_GAP / 2.0), _fmt(top + 13)))

    # 双面板（终解 A 左 / 终解 B 右）
    for label, plane, entries in (("A", plane_a, entries_a),
                                  ("B", plane_b, entries_b)):
        px = MARGIN if label == "A" else MARGIN + panel_w + L6_GAP
        out.append('<g class="v5-l8-panel" data-panel="%s" data-route-count="%d">'
                   % (label, len(entries)))
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"'
                   ' stroke="#262626" stroke-width="1"/>'
                   % (_fmt(px), _fmt(top), _fmt(panel_w), _fmt(panel_h)))
        out.append('<text class="v5-l8-title" x="%s" y="%s" font-size="11"'
                   ' font-weight="bold" fill="#262626">终解 %s</text>'
                   % (_fmt(px + 6), _fmt(top + 13), label))
        for zone in sorted(board.get("zones", []) or [],
                           key=lambda z: str(z.get("zone_id", ""))):
            out.extend(_render_zone(zone, plane, stackup, all_layers))
        out.append('<rect id="workspace-frame-l8-%s" x="%s" y="%s" width="%s"'
                   ' height="%s" fill="none" stroke="#262626" stroke-width="1.5"/>'
                   % (label, plane.x(workspace["x_min"]), plane.y(workspace["y_min"]),
                      plane.w(float(workspace["x_max"]) - float(workspace["x_min"])),
                      plane.w(float(workspace["y_max"]) - float(workspace["y_min"]))))
        for e in sorted(entries, key=lambda e: (e["partition_id"], e["net_id"])):
            out.extend(_render_route_lines(e, plane, stackup))
        out.append("</g>")

    # 差异高亮（overlay 后画，跨面板可见；两面板各一条，世界联合包围盒同位）
    for (pid, nid), fields, pts in diffs:
        if not pts:
            continue  # 防御：无坐标不画轮廓（键差异仍计入 data-diff-count）
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        wx0, wy0, wx1, wy1 = xs[0], ys[0], xs[-1], ys[-1]
        badge = "Δ %s/%s [%s]" % (pid, nid,
                                  ",".join(L8_FIELD_LABELS.get(f, f) for f in fields))
        for label, plane in (("A", plane_a), ("B", plane_b)):
            x = float(plane.x(wx0)) - L8_DIFF_PAD_PX
            y = float(plane.y(wy0)) - L8_DIFF_PAD_PX
            x2 = float(plane.x(wx1)) + L8_DIFF_PAD_PX
            y2 = float(plane.y(wy1)) + L8_DIFF_PAD_PX
            dash_attr = ' stroke-dasharray="%s"' % L8_DIFF_STYLE["dash"]
            out.append('<g class="v5-l8-diff" data-panel="%s" data-partition-id="%s"'
                       ' data-net-id="%s" data-diff-fields="%s">'
                       % (label, _esc(pid), _esc(nid), _esc(",".join(fields))))
            out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none"'
                       ' stroke="%s" stroke-width="1.5"%s/>'
                       % (_fmt(x), _fmt(y), _fmt(x2 - x), _fmt(y2 - y),
                          L8_DIFF_STYLE["stroke"], dash_attr))
            out.append('<text class="v5-l8-diff-badge" x="%s" y="%s" font-size="10"'
                       ' fill="%s">%s</text>'
                       % (_fmt(x), _fmt(y - 3.0), L8_DIFF_STYLE["stroke"],
                          _esc(badge)))
            out.append("</g>")

    out.extend(_l8_render_flags_box(flag_rows))
    out.extend(_render_legends(stackup))
    out.append("</svg>")
    return "\n".join(out)
