# -*- coding: utf-8 -*-
"""canvas.pack —— 席位载体（Lane-K2；接口合同 §1 pack 节）。

pack_view(st) -> {svg, facts_json, view_spec}；write_pack(pack, dir_path) 落
view.svg / view-facts.json / view-spec.json 三件。

**文档化最小决定（逐字披露）**：

- **板固孔席位投影（D-CT-016 对症，2026-09-25 用户裁定采纳）**：
  facts_json 在 state_facts 投影之上增补 ``holes`` 键（每项 grid/mm/r_mm，
  v5.drc.normalize_holes 单源+lattice.snap 同源格点化，排序钉死）。**只作
  数据披露**——禁布判定权威仍在 canvas.validate/v5.drc（防平行实现）；
  **state_facts 本体不动**（其哈希=链式台账锚，改动会破已收口激活跑的
  replay 链），故增补在 pack_view 侧对 facts 副本进行。

- **state 缝的兼容 accessor**：合同 §1 写 ``state_facts(st)``/``state_sha256(st)``
  （函数形态），车道任务书写 ``st.state_facts()``（方法形态）。本件
  :func:`state_call` 兼容两者：优先实例方法；否则查 ``st`` 类型所属模块的
  同名模块级函数（真件 canvas.state 已被加载时经 sys.modules 取，不静态
  import——K1 并行车道未落地时零依赖）。两者皆无 → AttributeError
  fail-closed（缝未接线，不静默）。
- **pad 图元源=st.anchors**（partition_id -> 两端点锚），shape_id 取
  ``pad:<partition_id>:a|b``——pack 显示层自有寻址，**不进** state 图元
  shape_id 空间（state 的 pad 不在图元清单，属 board 分区抽象）。
- **placement 覆盖不做锚位换算**：pad 渲染位置=anchors 原位；覆盖以
  ``data-placement`` 机器事实原样透传。理由：覆盖后锚位换算归
  canvas.instantiate/K1（合同 §1 connectivity 节），pack 自算即平行实现，
  禁。
- **格点→像素映射**：x = MARGIN_PX + (i - min_i) * CELL_PX（y 同理 j）。
  纯显示层线性映射，与 lat 的 mm 语义无关；lat 原样投影进 view_spec（须
  canonical 可序列化，fail-closed）。
- **data-layer 取值**：seg=其 layer；via="*"（全叠层通孔，v5.kicad_export
  口径 layers 首..尾）；pad="all"（pad_terminals layers=all 对应）；tuning="-"
  （合同 tunings 图元无 layer 字段，如实标注层不适用）。
- **确定性**：图元全按 shape_id/partition_id 排序渲染；整数像素；无时间戳
  无随机；属性序由构造固定——同输入双跑字节相等（硬测试）。
- view-spec.json / view-facts.json 落盘用 v5.canonical（sort_keys 紧凑）；
  write_pack 直写文件（合同未对 pack 落盘加 sidecar 卫生，导出器侧才有）。
"""

import os

from v5.canonical import canonical_json, canonical_text

GENERATOR = "canvas.pack"
VERSION = "1.0.0"

# 渲染常数（确定性披露：整数像素，纯显示层）
CELL_PX = 20
MARGIN_PX = 40
PAD_HALF_PX = 6
VIA_R_PX = 4
SEG_STROKE_PX = 2

_COLOR_BG = "#ffffff"
_COLOR_GRID = "#dddddd"
_COLOR_PAD = "#4a4a4a"
_COLOR_SEG = "#1a6ac9"
_COLOR_VIA = "#c9761a"
_COLOR_TUN = "#7a1ac9"


# ---------------------------------------------------------------------------
# state 缝兼容 accessor（loop.py 复用；真件集成由编排体冒烟钉合）
# ---------------------------------------------------------------------------

def state_call(st, name):
    """按方法→模块函数序调用 state 的 ``name`` 钩子（state_facts/state_sha256）。

    优先 ``st.name()``（车道任务书桩签名形态）；否则经 ``sys.modules`` 查
    ``st`` 类型所属模块的模块级 ``name(st)``（合同 §1 函数形态，真件
    canvas.state 已加载时生效）。两者皆无抛 AttributeError（fail-closed）。
    """
    hook = getattr(st, name, None)
    if callable(hook):
        return hook()
    import sys
    module = sys.modules.get(type(st).__module__)
    fn = getattr(module, name, None) if module is not None else None
    if callable(fn):
        return fn(st)
    raise AttributeError(
        "state 缝未接线: %r 无 %s 方法，其模块 %r 亦无同名函数（真接线=编排体"
        "集成冒烟）" % (st, name, type(st).__module__))


def _attr(st, name, expect):
    """读 state 属性并校验形态（list/dict），缺属性即 AttributeError。"""
    if not hasattr(st, name):
        raise AttributeError("state 缝未接线: st.%s 缺失（合同 §1 图元清单）"
                             % name)
    value = getattr(st, name)
    if not isinstance(value, expect):
        raise TypeError("st.%s 须为 %s，实得 %s"
                        % (name, expect.__name__, type(value).__name__))
    return value


# ---------------------------------------------------------------------------
# SVG 基元
# ---------------------------------------------------------------------------

def _esc(text):
    """SVG 属性值转义（& < > "）。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _compact(obj):
    """机器事实紧凑 JSON（无空格；canonical 键序）。"""
    return canonical_text(obj)


def _grid_points(grid):
    """归一格点字段为 [[i, j], ...]：点列原样；单点 [i, j] 包一层。"""
    if not isinstance(grid, list):
        raise TypeError("grid 须为 list，实得 %r" % (grid,))
    if grid and isinstance(grid[0], list):
        return grid
    return [grid]


class _Canvas(object):
    """格点→像素画布（显示层映射 + viewport 汇集）。"""

    def __init__(self, min_i, min_j, max_i, max_j):
        self.min_i, self.min_j = min_i, min_j
        self.max_i, self.max_j = max_i, max_j
        span_i = max(0, max_i - min_i)
        span_j = max(0, max_j - min_j)
        self.width = span_i * CELL_PX + 2 * MARGIN_PX
        self.height = span_j * CELL_PX + 2 * MARGIN_PX

    def px(self, i, j):
        return (MARGIN_PX + (i - self.min_i) * CELL_PX,
                MARGIN_PX + (j - self.min_j) * CELL_PX)

    def viewport(self):
        return {"min_i": self.min_i, "min_j": self.min_j,
                "max_i": self.max_i, "max_j": self.max_j,
                "width_px": self.width, "height_px": self.height}


def _bounds(points):
    """格点集合的 (min_i, min_j, max_i, max_j)；空集=(0,0,0,0)。"""
    if not points:
        return 0, 0, 0, 0
    return (min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points))


def _data_attrs(kind, shape_id, net, layer, grid, extra=()):
    """固定属性序的 data-* 机器事实段（值一律双引号包裹 + 转义，确定性）。"""
    parts = [
        'data-kind="%s"' % _esc(kind),
        'data-shape-id="%s"' % _esc(shape_id),
        'data-net="%s"' % _esc(net),
        'data-layer="%s"' % _esc(layer),
        'data-grid="%s"' % _esc(_compact(grid)),
    ]
    parts.extend(extra)
    return " ".join(parts)


def _kv_attr(name, value):
    """单条 data-* 属性（引号包裹）。"""
    return '%s="%s"' % (name, _esc(value))


def _partition_nets(board):
    """partition_id -> net_id（board.nets 反转）；一分区被多网引用即 fail-closed。"""
    mapping = {}
    for net in board.get("nets", []):
        for ref in net.get("partitions", []):
            if ref in mapping and mapping[ref] != net["net_id"]:
                raise ValueError(
                    "分区 %r 被多网引用（%r, %r）——板语义不容"
                    % (ref, mapping[ref], net["net_id"]))
            mapping[ref] = net["net_id"]
    return mapping


def _layer_ids(board):
    """[(layer_id, available)] 按板 stackup 序（可见性初值=available）。"""
    out = []
    for layer in board.get("stackup", []):
        if isinstance(layer, dict) and layer.get("id"):
            out.append((layer["id"], bool(layer.get("available", True))))
    return out


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def _hole_facts(st):
    """板固孔席位投影（D-CT-016）：[(x,y,r)] 单源归一 → grid 格点化数据。

    v5.drc.normalize_holes（判定侧同源）+ lattice.snap（锚同源映射）；mm 值
    9 位量化防浮点尾差；输出按 (grid, mm, r) 排序钉死（确定性）。只披露数据，
    不算禁布半径（避让换算归席位提示词，判定权威归 validate/v5.drc）。"""
    from v5 import drc
    holes_norm = drc.normalize_holes(st.board.get("holes"))
    if not holes_norm:
        return []                       # 空孔板零接触（K2 桩态亦走此路）
    lat = getattr(st, "lattice", None)
    if lat is None:
        raise AttributeError("state 缝未接线: st.lattice 缺失（板含 %d 孔"
                             "须格点阵才能席位投影，fail-closed）" % len(holes_norm))
    out = []
    for x, y, r in holes_norm:
        i, j = lat.snap(x, y)
        out.append({"grid": [int(i), int(j)],
                    "mm": [round(float(x), 9), round(float(y), 9)],
                    "r_mm": round(float(r), 9)})
    out.sort(key=lambda h: (h["grid"], h["mm"], h["r_mm"]))
    return out


def pack_view(st):
    """画板态 → 席位盲包载体 {svg: str, facts_json: str, view_spec: dict}。

    SVG 每图元带 data-shape-id/data-net/data-layer/data-grid/data-kind 机器
    事实，kind 覆盖 pad/seg/via/tuning 四类；facts_json=state_facts canonical
    投影；view_spec 含层可见性/视窗/渲染常数/lat 投影。
    """
    board = _attr(st, "board", dict)
    anchors = _attr(st, "anchors", dict)
    segs = _attr(st, "segs", (list, dict))
    vias = _attr(st, "vias", (list, dict))
    tunings = _attr(st, "tunings", (list, dict))
    placements = _attr(st, "placements", dict)

    facts = state_call(st, "state_facts")
    if not isinstance(facts, dict):
        raise TypeError("state_facts() 须返回 dict，实得 %s"
                        % type(facts).__name__)
    facts = dict(facts)                      # 不改 state_facts 本体（链哈希面）
    facts["holes"] = _hole_facts(st)         # D-CT-016 席位投影（pack 侧增补）
    facts_json = canonical_text(facts)

    # segs/vias/tunings 容合同两种容器（list 或 {shape_id: obj}），统一取值列表
    seg_list = segs.values() if isinstance(segs, dict) else list(segs)
    via_list = vias.values() if isinstance(vias, dict) else list(vias)
    tun_list = tunings.values() if isinstance(tunings, dict) else list(tunings)
    seg_list = sorted(seg_list, key=lambda s: s["shape_id"])
    via_list = sorted(via_list, key=lambda s: s["shape_id"])
    tun_list = sorted(tun_list, key=lambda s: s["shape_id"])

    part_nets = _partition_nets(board)

    # pad 事实（anchors 原位；placement 覆盖透传，见模块 docstring 披露）
    pads = []
    for pid in sorted(anchors.keys()):
        pair = anchors[pid]
        if not (isinstance(pair, list) and len(pair) == 2):
            raise TypeError("anchors[%r] 须为两端点列表，实得 %r" % (pid, pair))
        override = placements.get(pid)
        for side, point in zip(("a", "b"), pair):
            pads.append({
                "shape_id": "pad:%s:%s" % (pid, side),
                "net": part_nets.get(pid, ""),
                "grid": list(point),
                "placement": override,
            })

    # 全图元格点汇集 → viewport
    all_points = [p["grid"] for p in pads]
    for seg in seg_list:
        all_points.extend(_grid_points(seg["grid"]))
    for via in via_list:
        all_points.extend(_grid_points(via["grid"]))
    for tun in tun_list:
        all_points.extend(_grid_points(tun["grid"]))
    canvas = _Canvas(*_bounds(all_points))

    # ---- SVG 组装（固定序：背景 → 网格 → pad → seg → via → tuning）
    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
               'width="%d" height="%d">'
               % (canvas.width, canvas.height, canvas.width, canvas.height))
    out.append("<!-- generator=%s version=%s deterministic -->"
               % (GENERATOR, VERSION))
    out.append('<rect x="0" y="0" width="%d" height="%d" fill="%s"/>'
               % (canvas.width, canvas.height, _COLOR_BG))

    # 背景网格线（视窗格点线；非图元，无 data-* 机器事实）
    out.append('<g class="grid">')
    i = canvas.min_i
    while True:
        x, _ = canvas.px(i, 0)
        if x > canvas.width - MARGIN_PX and i > canvas.min_i:
            break
        out.append('<line x1="%d" y1="0" x2="%d" y2="%d" stroke="%s" '
                   'stroke-width="1"/>' % (x, x, canvas.height, _COLOR_GRID))
        if i >= canvas.max_i:
            break
        i += 1
    j = canvas.min_j
    while True:
        _, y = canvas.px(0, j)
        if y > canvas.height - MARGIN_PX and j > canvas.min_j:
            break
        out.append('<line x1="0" y1="%d" x2="%d" y2="%d" stroke="%s" '
                   'stroke-width="1"/>' % (y, canvas.width, y, _COLOR_GRID))
        if j >= canvas.max_j:
            break
        j += 1
    out.append("</g>")

    # pad（anchors 原位；placement 覆盖仅作机器事实透传，不换算锚位）
    out.append('<g class="pads">')
    for pad in pads:
        x, y = canvas.px(pad["grid"][0], pad["grid"][1])
        extra = []
        if pad["placement"] is not None:
            extra.append(_kv_attr("data-placement",
                                  _compact(pad["placement"])))
        out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" %s/>'
                   % (x - PAD_HALF_PX, y - PAD_HALF_PX,
                      2 * PAD_HALF_PX, 2 * PAD_HALF_PX, _COLOR_PAD,
                      _data_attrs("pad", pad["shape_id"], pad["net"], "all",
                                  pad["grid"], extra)))
    out.append("</g>")

    # seg
    out.append('<g class="segs">')
    for seg in seg_list:
        pts = _grid_points(seg["grid"])
        xy = " ".join("%d,%d" % canvas.px(p[0], p[1]) for p in pts)
        out.append('<polyline points="%s" fill="none" stroke="%s" '
                   'stroke-width="%d" %s/>'
                   % (xy, _COLOR_SEG, SEG_STROKE_PX,
                      _data_attrs("seg", seg["shape_id"], seg["net_id"],
                                  seg["layer"], pts)))
    out.append("</g>")

    # via
    out.append('<g class="vias">')
    for via in via_list:
        pts = _grid_points(via["grid"])
        x, y = canvas.px(pts[0][0], pts[0][1])
        out.append('<circle cx="%d" cy="%d" r="%d" fill="%s" %s/>'
                   % (x, y, VIA_R_PX, _COLOR_VIA,
                      _data_attrs("via", via["shape_id"], via["net_id"],
                                  "*", pts)))
    out.append("</g>")

    # tuning（虚线标记；data-tuning-kind 带 accordion/detour 子类）
    out.append('<g class="tunings">')
    for tun in tun_list:
        pts = _grid_points(tun["grid"])
        xy = " ".join("%d,%d" % canvas.px(p[0], p[1]) for p in pts)
        extra = [_kv_attr("data-tuning-kind", tun["kind"]),
                 _kv_attr("data-group-id", tun["group_id"])]
        out.append('<polyline points="%s" fill="none" stroke="%s" '
                   'stroke-width="%d" stroke-dasharray="6 4" %s/>'
                   % (xy, _COLOR_TUN, SEG_STROKE_PX,
                      _data_attrs("tuning", tun["shape_id"], tun["net_id"],
                                  "-", pts, extra)))
    out.append("</g>")

    out.append("</svg>")
    svg = "\n".join(out) + "\n"

    view_spec = {
        "format": "canvas-pack-v1",
        "generator": GENERATOR,
        "generator_version": VERSION,
        "layers": {lid: visible for lid, visible in _layer_ids(board)},
        "viewport": canvas.viewport(),
        "render": {
            "cell_px": CELL_PX, "margin_px": MARGIN_PX,
            "pad_half_px": PAD_HALF_PX, "via_r_px": VIA_R_PX,
            "seg_stroke_px": SEG_STROKE_PX,
        },
        "lat": _attr(st, "lat", object),
        "kinds": ["pad", "seg", "via", "tuning"],
        "placement_overlay_note": (
            "pad 位置=anchors 原位；placement 覆盖以 data-placement 机器事实"
            "透传，锚位换算归 canvas.instantiate（防平行实现）"),
        "board_sha256": _attr(st, "board_sha256", str),
    }
    # view_spec 须 canonical 可序列化（lat 投影 fail-closed 在此暴露）
    canonical_json(view_spec)

    return {"svg": svg, "facts_json": facts_json, "view_spec": view_spec}


def write_pack(pack, dir_path):
    """落盘三件：view.svg / view-facts.json / view-spec.json（canonical）。"""
    dir_path = os.fspath(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    paths = {
        "view.svg": os.path.join(dir_path, "view.svg"),
        "view-facts.json": os.path.join(dir_path, "view-facts.json"),
        "view-spec.json": os.path.join(dir_path, "view-spec.json"),
    }
    with open(paths["view.svg"], "wb") as f:
        f.write(pack["svg"].encode("utf-8"))
    with open(paths["view-facts.json"], "wb") as f:
        f.write(pack["facts_json"].encode("utf-8"))
    with open(paths["view-spec.json"], "wb") as f:
        f.write(canonical_json(pack["view_spec"]))
    return paths
