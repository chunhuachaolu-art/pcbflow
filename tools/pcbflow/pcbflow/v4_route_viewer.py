"""V4-EXEC-P10 route-viewer 交互视图（MASTER D-9；纯代码、零模型 token）。

确定性生成器：``build_route_viewer(board, manifest, svg_text) -> 自包含 HTML``
（纯函数）。视图层恒为表现层皮肤：**不改任何 authority**——不写板、不写
manifest、不接实验；一切过滤/高亮/计数只读 SVG 的 data-* 机器事实与
manifest 对象集（颜色=图例不是机器事实，R6）。

设计要点（派发词 §4）：

1. 自包含单文件：SVG 内联 + 原生 JS，零 CDN/零外部资源/零网络（file://
   可开、离线可用）；canonical：无 wall-clock、无主机路径、无随机源；
   同输入双跑字节一致（测试钉死）。
2. hash 链沿 P0 合同：HTML 根元素绑定 ``data-board-snapshot-sha256`` +
   ``data-route-manifest-payload-sha256``（具名 hash；禁用未限定
   manifest_sha256）。生成前 fail-closed 复核 board/manifest/SVG 三方
   hash 一致，且 manifest 逐对象（route/via/zone/board pad）在 SVG 内
   唯一可寻址——不一致即 ValueError，不出视图。
3. 交互模式搬自 ``pcbflow/editor_cmd.py``（viewBox 世界 mm 坐标 +
   viewT/fitView/applyView/mmPerPx 滚轮缩放+拖拽平移；搬模式不搬文件，
   editor_cmd.py 零改动）。
4. T0 过滤（图层/line_type/state 复选框 + hover tooltip 机器事实）、
   T1 高亮（同 net 全亮其余压暗 / net_id·route_id 搜索 / relation·parent
   组高亮）、T2 导航（缩放平移 + 图例 + 逐层/逐类型/逐状态计数侧栏 +
   DOM↔manifest 对象集一致性徽章）、T3 视图规格导出（当前过滤态 →
   view-spec JSON，供 ``svg_route_package.render_png`` 生成聚焦投影）。

T3 边界（R4/R8 重申）：view-spec 产物要进任何实验的模型臂输入 = 改变
实验输入，须新预注册；本模块只交付能力，不接任何实验。

生成器纪律（R10）：纯函数、canonical 序列化、无 wall-clock、无主机
绝对路径、零网络；仅标准库 + 包内 hashing/svg_route_package。
"""

from __future__ import annotations

import json
import re

from . import hashing
from . import svg_route_package as srp

#: viewer 自身 schema（HTML 根 data-pcbflow-viewer）
VIEWER_SCHEMA = "pcbflow.v4exec.route-viewer/1"

#: T3 视图规格 schema（viewer 导出 ↔ render_png 消费的合同）
VIEW_SPEC_SCHEMA = "pcbflow.v4exec.view-spec/1"

#: focus 目标种类（net / 单 route / relation 组 / parent 组）
FOCUS_KINDS = ("net", "route", "relation", "parent")

#: viewer 导出 view-spec 的默认目标分辨率（px；[宽, 高]）
DEFAULT_SPEC_RESOLUTION = (1600, 900)

_ACCEPTED_MANIFEST_SCHEMAS = (srp.MANIFEST_SCHEMA_VERSION,
                              srp.MANIFEST_SCHEMA_VERSION_V1)
_ACCEPTED_SVG_SCHEMAS = (srp.SVG_SCHEMA, srp.SVG_SCHEMA_V1)

_ROOT_ATTR_RE = re.compile(r"<svg\b[^>]*>")
_ATTR_RE_CACHE: "dict[str, re.Pattern]" = {}


# ---------------------------------------------------------------------------
# canonical 序列化（P0 口径：sort_keys + 紧凑分隔符 + 递归剔除 *_sha256 键）
# ---------------------------------------------------------------------------

def _strip_sha(obj):
    """递归剔除 *_sha256 键（凡被 P0 合同 hash 的对象先做这一步）。"""
    if isinstance(obj, dict):
        return {k: _strip_sha(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [_strip_sha(v) for v in obj]
    return obj


def _payload_sha256(obj) -> str:
    """P0 具名 hash 口径（与 srp._sha256_of / vrd.object_sha256 同规则）。"""
    text = json.dumps(_strip_sha(obj), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashing.sha256_text(text)


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _root_attr(svg_text: str, name: str) -> "str | None":
    """读 SVG 根元素属性（只解析首个 <svg ...> 开标签）。"""
    pat = _ATTR_RE_CACHE.get(name)
    if pat is None:
        pat = re.compile(r'\b' + re.escape(name) + r'="([^"]*)"')
        _ATTR_RE_CACHE[name] = pat
    m = _ROOT_ATTR_RE.search(svg_text)
    if not m:
        return None
    a = pat.search(m.group(0))
    return a.group(1) if a else None


# ---------------------------------------------------------------------------
# T3：view-spec 规格化（canonical；render_png 消费前必须过这一步）
# ---------------------------------------------------------------------------

def normalize_view_spec(spec, manifest: dict, board: dict) -> dict:
    """校验并 canonical 化 view-spec（非法 ValueError，fail-closed）。

    规则：

    - ``schema`` 必须为 :data:`VIEW_SPEC_SCHEMA`；
    - ``layers`` / ``line_types`` / ``states``：可选列表，空或缺失 = 不过滤
      （全集）；元素须分别存在于 manifest 对象集 / srp.LINE_TYPES /
      srp.ROUTE_STATES——未知值 fail-closed（宁可拒绝不出错图）；
    - ``focus``：null 或 ``{"kind": net|route|relation|parent, "id": ...}``；
      id 必须在 manifest/board 对象集中存在；
    - ``show_pads`` / ``show_keepouts``：布尔（缺省 true）；
    - ``resolution_px``：可选 [w, h]（正整数）；
    - ``bindings``：若给，必须与 manifest 的 board_snapshot_sha256 /
      manifest_payload_sha256 一致（防张冠李戴的规格套错板）。

    返回 canonical dict（键序固定、列表去重排序）；此形态即
    :func:`view_spec_sha256` 的哈希对象。
    """
    _require(isinstance(spec, dict), "view-spec: 不是对象")
    _require(spec.get("schema") == VIEW_SPEC_SCHEMA,
             f"view-spec.schema 非法（须为 {VIEW_SPEC_SCHEMA}）")

    routes = manifest.get("routes") or []
    vias = manifest.get("vias") or []

    def _idset(values, what):
        return set(values) if values else set()

    man_layers = set()
    for r in routes:
        man_layers.add(str(r.get("layer", "")))
    for v in vias:
        man_layers.add(str(v.get("from_layer", "")))
        man_layers.add(str(v.get("to_layer", "")))
    for p in (board.get("pads") or []):
        man_layers.add(str(p.get("layer", "")))
    man_layers.discard("")

    def _norm_list(key, allowed, what):
        raw = spec.get(key)
        if raw is None or raw == []:
            return []
        _require(isinstance(raw, list) and all(isinstance(x, str) for x in raw),
                 f"view-spec.{key}: 须为字符串列表")
        out = sorted(set(raw))
        for x in out:
            _require(x in allowed, f"view-spec.{key}: 未知值 {x!r}（{what}）")
        return out

    layers = _norm_list("layers", man_layers, "manifest 对象集之外的层")
    line_types = _norm_list("line_types", set(srp.LINE_TYPES),
                            "srp.LINE_TYPES 之外")
    states = _norm_list("states", set(srp.ROUTE_STATES),
                        "srp.ROUTE_STATES 之外")

    raw_focus = spec.get("focus")
    focus = None
    if raw_focus is not None:
        _require(isinstance(raw_focus, dict), "view-spec.focus: 不是对象")
        kind = raw_focus.get("kind")
        fid = raw_focus.get("id")
        _require(kind in FOCUS_KINDS,
                 f"view-spec.focus.kind 非法（须为 {FOCUS_KINDS} 之一）")
        _require(isinstance(fid, str) and fid, "view-spec.focus.id 缺失")
        if kind == "net":
            ok = fid in {str(r.get("net_id")) for r in routes} \
                | {str(v.get("net_id")) for v in vias}
        elif kind == "route":
            ok = fid in {str(r.get("route_id")) for r in routes}
        elif kind == "relation":
            ok = fid in {str(rel.get("relation_id"))
                         for rel in (board.get("relations") or [])}
        else:  # parent
            ok = fid in {str(r.get("parent_id")) for r in routes
                         if r.get("parent_id")} \
                | {str(v.get("parent_id")) for v in vias
                   if v.get("parent_id")}
        _require(ok, f"view-spec.focus: {kind} id {fid!r} 不在对象集中"
                     "（fail-closed）")
        focus = {"kind": kind, "id": fid}

    show_pads = spec.get("show_pads", True)
    show_keepouts = spec.get("show_keepouts", True)
    _require(isinstance(show_pads, bool), "view-spec.show_pads 须为布尔")
    _require(isinstance(show_keepouts, bool),
             "view-spec.show_keepouts 须为布尔")

    resolution = list(DEFAULT_SPEC_RESOLUTION)
    raw_res = spec.get("resolution_px")
    if raw_res is not None:
        _require(isinstance(raw_res, list) and len(raw_res) == 2
                 and all(isinstance(x, int) and not isinstance(x, bool)
                         and x > 0 for x in raw_res),
                 "view-spec.resolution_px: 须为 [正整数宽, 正整数高]")
        resolution = [int(raw_res[0]), int(raw_res[1])]

    raw_bind = spec.get("bindings")
    if raw_bind is not None:
        _require(isinstance(raw_bind, dict), "view-spec.bindings: 不是对象")
        expect = {"board_snapshot_sha256":
                  manifest.get("board_snapshot_sha256"),
                  "route_manifest_payload_sha256":
                  manifest.get("manifest_payload_sha256")}
        for k, v in expect.items():
            got = raw_bind.get(k)
            _require(got == v, f"view-spec.bindings.{k} 与 manifest 不一致"
                     "（fail-closed，规格不得套错板）")

    return {
        "schema": VIEW_SPEC_SCHEMA,
        "layers": layers,
        "line_types": line_types,
        "states": states,
        "show_pads": show_pads,
        "show_keepouts": show_keepouts,
        "focus": focus,
        "resolution_px": resolution,
        "bindings": {
            "board_snapshot_sha256":
                manifest.get("board_snapshot_sha256"),
            "route_manifest_payload_sha256":
                manifest.get("manifest_payload_sha256"),
        },
    }


def view_spec_sha256(normalized_spec: dict) -> str:
    """normalized view-spec 的 canonical sha256（紧凑 sort_keys；**不剔除**
    bindings 里的 *_sha256 键——绑定是规格身份的一部分，与 manifest payload
    hash 的剔除规则刻意不同，见 docstring）。"""
    text = json.dumps(normalized_spec, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashing.sha256_text(text)


def view_spec_focus_members(spec: dict, manifest: dict, board: dict):
    """focus 目标的成员 id 集（按 kind 展开；net→net_id 集、route→单
    route_id、relation→members(net_id 集)、parent→parent_id 集）。"""
    focus = spec.get("focus")
    if not focus:
        return None
    kind, fid = focus["kind"], focus["id"]
    if kind == "net":
        return {"net_ids": {fid}}
    if kind == "route":
        return {"route_ids": {fid}}
    if kind == "relation":
        for rel in (board.get("relations") or []):
            if str(rel.get("relation_id")) == fid:
                return {"net_ids": {str(m) for m in rel.get("members") or []}}
        return {"net_ids": set()}
    return {"parent_ids": {fid}}


# ---------------------------------------------------------------------------
# viewer 元数据（侧栏计数/分组词表；全部由 board+manifest 派生）
# ---------------------------------------------------------------------------

def _viewer_meta(board: dict, manifest: dict) -> dict:
    routes = manifest.get("routes") or []
    vias = manifest.get("vias") or []
    zones = manifest.get("zones") or []
    pads = board.get("pads") or []
    keepouts = board.get("keepouts") or []
    relations = board.get("relations") or []

    layers = set()
    for r in routes:
        layers.add(str(r.get("layer", "")))
    for v in vias:
        layers.add(str(v.get("from_layer", "")))
        layers.add(str(v.get("to_layer", "")))
    for p in pads:
        layers.add(str(p.get("layer", "")))
    layers.discard("")

    routes_by_layer = {L: 0 for L in layers}
    for r in routes:
        routes_by_layer[str(r.get("layer", ""))] += 1
    vias_by_layer = {L: 0 for L in layers}
    for v in vias:
        vias_by_layer[str(v.get("from_layer", ""))] += 1

    lt_order = [t for t in srp.LINE_TYPES
                if any(str(r.get("line_type")) == t for r in routes)]
    extra_lt = sorted({str(r.get("line_type")) for r in routes}
                      - set(srp.LINE_TYPES))
    st_order = [s for s in srp.ROUTE_STATES
                if any(str(r.get("state")) == s for r in routes)]
    extra_st = sorted({str(r.get("state")) for r in routes}
                      - set(srp.ROUTE_STATES))
    line_types = lt_order + extra_lt
    states = st_order + extra_st

    parents = {}
    for r in routes:
        pid = r.get("parent_id")
        if pid:
            parents[str(pid)] = parents.get(str(pid), 0) + 1
    for v in vias:
        pid = v.get("parent_id")
        if pid:
            parents[str(pid)] = parents.get(str(pid), 0) + 1

    return {
        "layers": sorted(layers),
        "line_types": line_types,
        "states": states,
        "routes_by_layer": routes_by_layer,
        "vias_by_layer": vias_by_layer,
        "routes_by_line_type": {
            t: sum(1 for r in routes if str(r.get("line_type")) == t)
            for t in line_types},
        "routes_by_state": {
            s: sum(1 for r in routes if str(r.get("state")) == s)
            for s in states},
        "parents": sorted(parents.items()),
        "relations": [{"relation_id": str(rel.get("relation_id")),
                       "relation_type": str(rel.get("relation_type")),
                       "members": [str(m) for m in
                                   (rel.get("members") or [])]}
                      for rel in relations],
        "counts": {"routes": len(routes), "vias": len(vias),
                   "zones": len(zones), "pads": len(pads),
                   "keepouts": len(keepouts),
                   "relations": len(relations)},
        "net_ids": sorted({str(r.get("net_id")) for r in routes}
                          | {str(v.get("net_id")) for v in vias}),
        "route_ids": sorted(str(r.get("route_id")) for r in routes),
        "via_ids": sorted(str(v.get("via_id")) for v in vias),
        "pad_ids": sorted(str(p.get("pad_id")) for p in pads),
    }


# ---------------------------------------------------------------------------
# 主生成器
# ---------------------------------------------------------------------------

def build_route_viewer(board: dict, manifest: dict, svg_text: str, *,
                       title: "str | None" = None) -> str:
    """board + manifest + SVG → 自包含交互 viewer HTML（纯函数）。

    fail-closed 前置校验（任一不符即 ValueError，不出视图）：

    1. manifest schema ∈ {v4-route-manifest-2, v4-route-manifest-1}，且
       ``manifest_payload_sha256`` 与重算一致；
    2. board canonical sha == manifest.board_snapshot_sha256（P0 具名 hash）；
    3. SVG 根 data-route-manifest-sha256 / data-board-snapshot-sha256 与
       manifest 一致（三方绑定）；
    4. manifest 逐对象（route/via/zone）与 board 逐 pad 在 SVG 内
       data-*-id 可寻址（逐对象过滤/高亮的可达性前提）。

    canonical：同输入双跑字节一致；无 wall-clock / 主机路径 / 网络。
    """
    _require(isinstance(board, dict), "build_route_viewer: board 不是对象")
    _require(isinstance(manifest, dict),
             "build_route_viewer: manifest 不是对象")
    _require(isinstance(svg_text, str) and "<svg" in svg_text,
             "build_route_viewer: svg_text 不是 SVG 文本")
    _require(manifest.get("schema_version") in _ACCEPTED_MANIFEST_SCHEMAS,
             "build_route_viewer: manifest.schema_version 非法")
    _require(_payload_sha256(manifest)
             == manifest.get("manifest_payload_sha256"),
             "build_route_viewer: manifest 与 manifest_payload_sha256 不"
             "一致（fail-closed）")
    _require(_payload_sha256(board)
             == manifest.get("board_snapshot_sha256"),
             "build_route_viewer: board canonical sha 与 manifest."
             "board_snapshot_sha256 不一致（fail-closed）")
    svg_schema = _root_attr(svg_text, "data-pcbflow-schema")
    _require(svg_schema in _ACCEPTED_SVG_SCHEMAS,
             "build_route_viewer: SVG data-pcbflow-schema 非法")
    _require(_root_attr(svg_text, "data-route-manifest-sha256")
             == manifest.get("manifest_payload_sha256"),
             "build_route_viewer: SVG 根 data-route-manifest-sha256 与 "
             "manifest 不一致（fail-closed）")
    _require(_root_attr(svg_text, "data-board-snapshot-sha256")
             == manifest.get("board_snapshot_sha256"),
             "build_route_viewer: SVG 根 data-board-snapshot-sha256 与 "
             "manifest 不一致（fail-closed）")

    # 逐对象可寻址（route/via/zone 来自 manifest；pad 来自 board）
    for r in manifest.get("routes") or []:
        rid = _esc(str(r.get("route_id", "")))
        _require(f'data-route-id="{rid}"' in svg_text,
                 f"build_route_viewer: route {r.get('route_id')!r} 未在 SVG "
                 "内寻址（fail-closed）")
    for v in manifest.get("vias") or []:
        vid = _esc(str(v.get("via_id", "")))
        _require(f'data-via-id="{vid}"' in svg_text,
                 f"build_route_viewer: via {v.get('via_id')!r} 未在 SVG 内"
                 "寻址（fail-closed）")
    for z in manifest.get("zones") or []:
        zid = _esc(str(z.get("zone_id", "")))
        _require(f'data-zone-id="{zid}"' in svg_text,
                 f"build_route_viewer: zone {z.get('zone_id')!r} 未在 SVG "
                 "内寻址（fail-closed）")
    for p in board.get("pads") or []:
        pid = _esc(str(p.get("pad_id", "")))
        _require(f'data-pad-id="{pid}"' in svg_text,
                 f"build_route_viewer: pad {p.get('pad_id')!r} 未在 SVG 内"
                 "寻址（fail-closed）")

    meta = _viewer_meta(board, manifest)
    scenario = str(manifest.get("scenario_id", ""))
    doc_title = f"route-viewer: {title or scenario}"

    # 内联 SVG：剥 XML 声明（HTML 文档内非法且无意义）
    inline_svg = svg_text
    m = re.match(r"^\s*<\?xml[^>]*\?>\s*", inline_svg)
    if m:
        inline_svg = inline_svg[m.end():]
    inline_svg = inline_svg.rstrip("\n")

    bundle = {"manifest": manifest, "viewer": meta}
    bundle_json = json.dumps(bundle, sort_keys=True,
                             separators=(",", ":"),
                             ensure_ascii=False).replace("<", "\\u003c")

    board_sha = str(manifest["board_snapshot_sha256"])
    man_sha = str(manifest["manifest_payload_sha256"])

    parts = []
    parts.append('<!DOCTYPE html>')
    parts.append(
        f'<html lang="zh-CN" data-pcbflow-viewer="{VIEWER_SCHEMA}"'
        f' data-board-snapshot-sha256="{_esc(board_sha)}"'
        f' data-route-manifest-payload-sha256="{_esc(man_sha)}">')
    parts.append('<head>')
    parts.append('<meta charset="utf-8">')
    parts.append(f'<title>{_esc(doc_title)}</title>')
    parts.append(_CSS)
    parts.append('</head>')
    parts.append('<body>')
    parts.append(_header_html(doc_title, meta))
    parts.append('<main>')
    parts.append(_sidebar_html(meta))
    parts.append(
        f'<div id="stage">{inline_svg}'
        '<div id="tooltip" hidden></div></div>')
    parts.append('</main>')
    parts.append(_footer_html(board_sha, man_sha, meta))
    parts.append(
        '<script type="application/json" id="viewer-bundle">'
        f'{bundle_json}</script>')
    parts.append(_JS)
    parts.append('</body>')
    parts.append('</html>')
    return "\n".join(parts) + "\n"


def _header_html(doc_title: str, meta: dict) -> str:
    c = meta["counts"]
    return (
        '<header>'
        f'<span id="doc-title">{_esc(doc_title)}</span>'
        f'<span class="chip">routes <b>{c["routes"]}</b></span>'
        f'<span class="chip">vias <b>{c["vias"]}</b></span>'
        f'<span class="chip">zones <b>{c["zones"]}</b></span>'
        f'<span class="chip">pads <b>{c["pads"]}</b></span>'
        '<span style="flex:1"></span>'
        '<input id="search" type="text" placeholder="搜索 net_id / route_id /'
        ' via_id / pad_id" autocomplete="off">'
        '<button id="b-search">高亮</button>'
        '<button id="b-clear">清除</button>'
        '<button id="b-fit">适配</button>'
        '<button id="b-spec" class="primary">导出 view-spec</button>'
        '</header>')


def _sidebar_html(meta: dict) -> str:
    c = meta["counts"]
    h = ['<aside id="sidebar">']

    h.append('<section><h2>图层（叠加显示）</h2>')
    for layer in meta["layers"]:
        nr = meta["routes_by_layer"].get(layer, 0)
        nv = meta["vias_by_layer"].get(layer, 0)
        h.append(
            f'<label class="ck"><input type="checkbox" data-filter="layer" '
            f'value="{_esc(layer)}" checked> {_esc(layer)}'
            f'（route {nr} / via {nv}）</label>')
    h.append('</section>')

    h.append('<section><h2>line_type</h2>')
    for t in meta["line_types"]:
        n = meta["routes_by_line_type"].get(t, 0)
        h.append(
            f'<label class="ck"><input type="checkbox" '
            f'data-filter="line-type" value="{_esc(t)}" checked> '
            f'{_esc(t)}（{n}）</label>')
    h.append('<p class="hint">via 无 line_type 属性，不受此过滤约束</p>'
             '</section>')

    h.append('<section><h2>state（对照过滤）</h2>')
    for s in meta["states"]:
        n = meta["routes_by_state"].get(s, 0)
        h.append(
            f'<label class="ck"><input type="checkbox" '
            f'data-filter="state" value="{_esc(s)}" checked> '
            f'{_esc(s)}（{n}）</label>')
    h.append('<p class="hint">diff 复查：勾选/取消 state 即前后对照</p>'
             '</section>')

    h.append('<section><h2>板件</h2>')
    h.append(f'<label class="ck"><input type="checkbox" id="ck-pads" '
             f'checked> pads（{c["pads"]}）</label>')
    h.append(f'<label class="ck"><input type="checkbox" id="ck-keepouts" '
             f'checked> keepouts（{c["keepouts"]}）</label>')
    h.append('</section>')

    h.append('<section><h2>组高亮（relation / parent）</h2>')
    for rel in meta["relations"]:
        h.append(
            f'<button class="grp" data-group-kind="relation" '
            f'data-group-id="{_esc(rel["relation_id"])}">'
            f'{_esc(rel["relation_id"])} · {_esc(rel["relation_type"])}'
            f'（{len(rel["members"])} 网）</button>')
    for pid, n in meta["parents"]:
        h.append(
            f'<button class="grp" data-group-kind="parent" '
            f'data-group-id="{_esc(pid)}">parent {_esc(pid)}（{n}）</button>')
    if not meta["relations"] and not meta["parents"]:
        h.append('<p class="hint">本视图无 relation/parent 组</p>')
    h.append('</section>')

    h.append('<section><h2>状态</h2>'
             '<div class="kv" id="hl-label">（未高亮）</div>'
             '<div class="kv" id="spec-status">（未导出）</div>'
             '<div class="kv" id="dom-badge">DOM↔manifest 一致性：检测中'
             '</div></section>')
    h.append('</aside>')
    return "".join(h)


def _footer_html(board_sha: str, man_sha: str, meta: dict) -> str:
    return (
        '<footer>视图层恒为表现层：本 viewer 只读 data-* 机器事实与 '
        'manifest 对象集，不写板、不改 manifest、不做 authority（颜色='
        '图例不是机器事实）。拖拽平移 / 滚轮缩放；点击对象高亮同网，点击'
        '空白清除。<br>hash 链（P0 具名 hash）：board-snapshot='
        f'<code>{_esc(board_sha[:16])}…</code> manifest-payload='
        f'<code>{_esc(man_sha[:16])}…</code>（完整值在 html 根 data-* 与'
        ' view-spec bindings）</footer>')


_CSS = """<style>
:root{color-scheme:light}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font:13px/1.45 system-ui,"Segoe UI",sans-serif;background:#f4f5f7;color:#1c2430}
header{display:flex;align-items:center;gap:8px;padding:6px 12px;background:#1c2430;color:#e7ecf3;flex-wrap:wrap}
header #doc-title{font-weight:600;margin-right:8px}
.chip{background:#2b3648;border-radius:10px;padding:1px 8px;font-size:12px}
.chip b{color:#ffd166}
input[type=text]{min-width:230px;padding:3px 8px;border-radius:4px;border:1px solid #5a6577;background:#121822;color:#e7ecf3}
button{padding:3px 10px;border-radius:4px;border:1px solid #5a6577;background:#2b3648;color:#e7ecf3;cursor:pointer}
button.primary{background:#2563eb;border-color:#2563eb}
button.grp{display:block;width:100%;text-align:left;margin:2px 0;background:#e7ecf3;color:#1c2430;border:1px solid #b7c0cd}
button.grp:hover{background:#d8e2f0}
main{display:flex;height:calc(100% - 66px)}
#sidebar{width:250px;overflow:auto;background:#fff;border-right:1px solid #d5dae2;padding:8px 12px}
#sidebar h2{font-size:12px;margin:12px 0 4px;color:#5a6577;text-transform:uppercase;letter-spacing:.04em}
#sidebar section:first-child h2{margin-top:2px}
label.ck{display:block;margin:1px 0}
.hint{color:#7b8494;font-size:11px;margin:4px 0}
.kv{font-size:11px;color:#39414e;word-break:break-all}
#stage{flex:1;position:relative;overflow:hidden;background:#fff}
#stage>svg{width:100%;height:100%;display:block;cursor:grab}
#stage>svg.panning{cursor:grabbing}
#stage svg .off{display:none}
#stage svg .dim{opacity:.12}
#stage svg .hl{opacity:1}
#stage svg [data-object-kind]{cursor:pointer}
#tooltip{position:fixed;z-index:30;background:#121822;color:#e7ecf3;padding:6px 8px;border-radius:6px;font-size:12px;pointer-events:none;max-width:340px;white-space:pre-line}
#tooltip b{color:#ffd166}
footer{position:fixed;bottom:0;left:0;right:0;background:#e7ecf3;border-top:1px solid #d5dae2;font-size:11px;color:#39414e;padding:3px 12px}
footer code{background:#fff;padding:0 3px;border-radius:3px}
#spec-panel{position:fixed;z-index:40;right:12px;top:52px;width:430px;max-height:75vh;overflow:auto;background:#fff;border:1px solid #b7c0cd;border-radius:8px;padding:10px;display:none}
#spec-panel textarea{width:100%;height:220px;font:11px/1.4 ui-monospace,Consolas,monospace}
</style>"""


_JS = """<script>
"use strict";
// pcbflow V4-EXEC-P10 route-viewer（自包含；零网络/零外部资源/零时钟）。
// 交互模式取自 pcbflow/editor_cmd.py（viewBox 世界 mm + viewT/fitView/
// applyView/mmPerPx；搬模式不搬文件）。只读 data-*；零写回。
const BUNDLE = JSON.parse(document.getElementById("viewer-bundle").textContent);
const M = BUNDLE.manifest;
const V = BUNDLE.viewer;
const svg = document.querySelector("#stage > svg");
const stage = document.getElementById("stage");
const tip = document.getElementById("tooltip");
const objs = Array.prototype.slice.call(
    svg.querySelectorAll("[data-object-kind]"));
const KINDS = {route: "route_segment", via: "via", pad: "pad",
               zone: "zone", keepout: "keepout"};
const segNodes = objs.filter(n => n.getAttribute("data-object-kind") === "route_segment");
const viaNodes = objs.filter(n => n.getAttribute("data-object-kind") === "via");
const padNodes = objs.filter(n => n.getAttribute("data-object-kind") === "pad");
const koNodes  = objs.filter(n => n.getAttribute("data-object-kind") === "keepout");

// ---- T2 导航：viewBox = 世界 mm（x 右 y 下；SVG 内部坐标系，不翻转） ----
// preserveAspectRatio="xMidYMid meet"：px<->mm 映射必须经 viewT()（禁满幅线性）。
const VB0 = svg.getAttribute("viewBox").split(/\\s+/).map(Number);
let vb = null;
function viewT() {
  const r = svg.getBoundingClientRect();
  const s = Math.min(r.width / vb.w, r.height / vb.h);
  return {s: s,
          ox: r.left + (r.width - vb.w * s) / 2,
          oy: r.top + (r.height - vb.h * s) / 2};
}
function fitView() {
  let w = VB0[2], h = VB0[3];
  const r = svg.getBoundingClientRect();
  if (r.width && r.height) {
    const asp = r.width / r.height;
    if (w / h < asp) { w = h * asp; } else { h = w / asp; }
  }
  vb = {x: VB0[0] + VB0[2] / 2 - w / 2,
        y: VB0[1] + VB0[3] / 2 - h / 2, w: w, h: h};
  applyView();
}
function mmPerPx() { return viewT().s; }
function applyView() {
  svg.setAttribute("viewBox",
    vb.x + " " + vb.y + " " + vb.w + " " + vb.h);
}
function toWorld(ev) {
  const t = viewT();
  return {x: vb.x + (ev.clientX - t.ox) / t.s,
          y: vb.y + (ev.clientY - t.oy) / t.s};
}
svg.addEventListener("wheel", ev => {
  ev.preventDefault();
  const w = toWorld(ev), f = ev.deltaY > 0 ? 1.15 : 1 / 1.15;
  const nw = Math.min(400, Math.max(2, vb.w * f)),
        nh = nw * vb.h / vb.w;
  vb = {x: w.x - (w.x - vb.x) * nw / vb.w,
        y: w.y - (w.y - vb.y) * nh / vb.h, w: nw, h: nh};
  applyView();
}, {passive: false});
// 拖拽平移 + 点击选择（位移 < 4px 视为点击）
let drag = null;
stage.addEventListener("pointerdown", ev => {
  drag = {x: ev.clientX, y: ev.clientY, vb: {x: vb.x, y: vb.y}, moved: false};
  svg.classList.add("panning");
});
window.addEventListener("pointermove", ev => {
  if (drag) {
    const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) { drag.moved = true; }
    const s = mmPerPx();
    vb = {x: drag.vb.x - dx / s, y: drag.vb.y - dy / s,
          w: vb.w, h: vb.h};
    applyView();
  }
  const t = ev.target.closest ? ev.target.closest("[data-object-kind]") : null;
  if (t && stage.contains(t)) { showTip(ev, t); } else { hideTip(); }
});
window.addEventListener("pointerup", ev => {
  if (drag && !drag.moved) { handleClick(ev); }
  drag = null;
  svg.classList.remove("panning");
});

// ---- T0：hover tooltip（机器事实全部来自 data-*） ----
const TIP_FIELDS = {
  route_segment: ["route_id", "net_id", "layer", "width_mm", "line_type",
                  "state", "source", "endpoint_start", "endpoint_end"],
  via: ["via_id", "net_id", "from_layer", "to_layer", "drill_mm",
        "annular_ring_mm", "parent_id"],
  pad: ["pad_id", "net_id", "layer"],
  zone: ["zone_id", "net_id", "layers", "fill_state"],
  keepout: ["keepout_id", "layers"],
};
function showTip(ev, node) {
  const kind = node.getAttribute("data-object-kind");
  const fields = TIP_FIELDS[kind] || [];
  const lines = ["[" + kind + "]"];
  for (const f of fields) {
    const v = node.getAttribute("data-" + f.replace(/_/g, "-"));
    if (v !== null && v !== "") { lines.push(f + ": " + v); }
  }
  tip.textContent = lines.join("\\n");
  tip.hidden = false;
  tip.style.left = Math.min(window.innerWidth - 350, ev.clientX + 14) + "px";
  tip.style.top = (ev.clientY + 14) + "px";
}
function hideTip() { tip.hidden = true; }

// ---- T0：过滤（图层叠加 / line_type / state；via 仅受图层约束） ----
function checkedValues(name) {
  const out = [];
  document.querySelectorAll('input[data-filter="' + name + '"]:checked')
    .forEach(c => out.push(c.value));
  return out;
}
function applyFilters() {
  const layers = new Set(checkedValues("layer"));
  const lts = new Set(checkedValues("line-type"));
  const states = new Set(checkedValues("state"));
  for (const n of segNodes) {
    const ok = (!layers.size || layers.has(n.getAttribute("data-layer")))
        && (!lts.size || lts.has(n.getAttribute("data-line-type")))
        && (!states.size || states.has(n.getAttribute("data-state")));
    n.classList.toggle("off", !ok);
  }
  for (const n of viaNodes) {
    const ok = !layers.size
        || layers.has(n.getAttribute("data-from-layer"))
        || layers.has(n.getAttribute("data-to-layer"));
    n.classList.toggle("off", !ok);
  }
  const padsOn = document.getElementById("ck-pads").checked;
  padNodes.forEach(n => n.classList.toggle("off", !padsOn));
  const koOn = document.getElementById("ck-keepouts").checked;
  koNodes.forEach(n => n.classList.toggle("off", !koOn));
}
document.querySelectorAll("#sidebar input[type=checkbox]")
  .forEach(c => c.addEventListener("change", applyFilters));

// ---- T1：高亮（同 net 全亮其余压暗 / 搜索 / 组高亮） ----
let focus = null;   // null | {kind:"net"|"route"|"via"|"pad"|"relation"|"parent", id}
function clearHighlight() {
  focus = null;
  objs.forEach(n => n.classList.remove("hl", "dim"));
  document.getElementById("hl-label").textContent = "（未高亮）";
}
function highlightBy(pred, label) {
  let hit = 0;
  for (const n of objs) {
    const k = n.getAttribute("data-object-kind");
    if (k !== "route_segment" && k !== "via" && k !== "pad") { continue; }
    const on = pred(n);
    n.classList.toggle("hl", on);
    n.classList.toggle("dim", !on);
    if (on) { hit++; }
  }
  document.getElementById("hl-label").textContent =
    label + "（命中 " + hit + " 对象）";
}
function netPred(netId) {
  return n => n.getAttribute("data-net-id") === netId;
}
function handleClick(ev) {
  const t = ev.target.closest
    ? ev.target.closest("[data-object-kind]") : null;
  if (!t || !stage.contains(t)) { clearHighlight(); return; }
  const kind = t.getAttribute("data-object-kind");
  if (kind === "board_edge" || kind === "keepout"
      || kind === "route_relation") { clearHighlight(); return; }
  const netId = t.getAttribute("data-net-id");
  if (!netId) { clearHighlight(); return; }
  focus = {kind: "net", id: netId};
  highlightBy(netPred(netId), "net " + netId);
}
document.getElementById("b-clear").addEventListener("click", clearHighlight);
document.getElementById("b-search").addEventListener("click", doSearch);
document.getElementById("search").addEventListener("keydown", ev => {
  if (ev.key === "Enter") { doSearch(); }
});
function doSearch() {
  const q = document.getElementById("search").value.trim();
  if (!q) { return; }
  if (V.net_ids.indexOf(q) >= 0) {
    focus = {kind: "net", id: q};
    highlightBy(netPred(q), "net " + q);
    return;
  }
  if (V.route_ids.indexOf(q) >= 0) {
    focus = {kind: "route", id: q};
    highlightBy(n => n.getAttribute("data-route-id") === q,
                "route " + q);
    return;
  }
  if (V.via_ids.indexOf(q) >= 0) {
    focus = {kind: "route", id: q};   // via 聚焦：单对象投影（route 槽位）
    highlightBy(n => n.getAttribute("data-via-id") === q, "via " + q);
    return;
  }
  if (V.pad_ids.indexOf(q) >= 0) {
    const t = svg.querySelector('[data-pad-id="' + q + '"]');
    const netId = t ? t.getAttribute("data-net-id") : null;
    if (netId) {
      focus = {kind: "net", id: netId};
      highlightBy(netPred(netId), "pad " + q + " → net " + netId);
      return;
    }
  }
  document.getElementById("hl-label").textContent =
    "未找到：" + q + "（net/route/via/pad id 之外）";
}
document.querySelectorAll("button.grp").forEach(b => {
  b.addEventListener("click", () => {
    const gid = b.getAttribute("data-group-id");
    if (b.getAttribute("data-group-kind") === "relation") {
      let members = [];
      for (const rel of V.relations) {
        if (rel.relation_id === gid) { members = rel.members; }
      }
      const ms = new Set(members);
      focus = {kind: "relation", id: gid};
      highlightBy(n => ms.has(n.getAttribute("data-net-id")),
                  "relation " + gid + "（" + members.length + " 网）");
    } else {
      focus = {kind: "parent", id: gid};
      highlightBy(n => n.getAttribute("data-parent-id") === gid,
                  "parent " + gid);
    }
  });
});

// ---- T2：DOM<->manifest 对象集一致性徽章（页内自检，只读） ----
(function () {
  const ok = segNodes.length === (M.routes || []).length
      && viaNodes.length === (M.vias || []).length;
  const el = document.getElementById("dom-badge");
  el.textContent = "DOM↔manifest 一致性：route " + segNodes.length + "/"
      + (M.routes || []).length + " via " + viaNodes.length + "/"
      + (M.vias || []).length + (ok ? " ✓ 一致" : " ✗ 不一致");
  el.style.color = ok ? "#166534" : "#b91c1c";
})();

// ---- T3：view-spec 导出（当前过滤态 -> canonical JSON） ----
document.getElementById("b-fit").addEventListener("click", fitView);
const specPanel = document.createElement("div");
specPanel.id = "spec-panel";
specPanel.innerHTML =
    '<h3 style="margin:2px 0 6px">当前 view-spec（T3）</h3>'
  + '<textarea id="spec-text" readonly></textarea>'
  + '<p class="hint">canonical JSON：列明选择器语义、目标层/网/组、目标'
  + '分辨率与 hash 绑定。render_png(view_spec=…) 消费本规格生成聚焦投影'
  + ' PNG（能力交付；进任何实验输入须新预注册）。</p>'
  + '<button id="b-copy">复制</button> '
  + '<button id="b-dl">下载 JSON</button> '
  + '<button id="b-close">关闭</button>';
document.body.appendChild(specPanel);
function currentSpec() {
  function sv(name) { const v = checkedValues(name); v.sort(); return v; }
  return {
    schema: "pcbflow.v4exec.view-spec/1",
    layers: sv("layer"),
    line_types: sv("line-type"),
    states: sv("state"),
    show_pads: document.getElementById("ck-pads").checked,
    show_keepouts: document.getElementById("ck-keepouts").checked,
    focus: focus ? {kind: focus.kind, id: focus.id} : null,
    resolution_px: [1600, 900],
    selectors: {
      route_layer: '[data-object-kind="route_segment"][data-layer∈layers]',
      via_layers: '[data-object-kind="via"]（from/to 层任一命中）',
      line_type: '[data-line-type∈line_types]（route 属性；via 无此属性）',
      state: '[data-state∈states]（route 属性；via 无此属性）',
      focus_net: '[data-net-id=id]',
      focus_route: '[data-route-id=id]（via 搜索聚焦=单对象投影）',
      focus_parent: '[data-parent-id=id]',
      focus_relation: 'board.relations[relation_id].members（net_id 集）'
    },
    bindings: {
      board_snapshot_sha256: M.board_snapshot_sha256,
      route_manifest_payload_sha256: M.manifest_payload_sha256
    }
  };
}
document.getElementById("b-spec").addEventListener("click", () => {
  document.getElementById("spec-text").value =
    JSON.stringify(currentSpec(), null, 2);
  specPanel.style.display = "block";
  document.getElementById("spec-status").textContent =
    "view-spec 已导出（面板内复制/下载）";
});
document.getElementById("b-close").addEventListener("click", () => {
  specPanel.style.display = "none";
});
document.getElementById("b-copy").addEventListener("click", () => {
  const ta = document.getElementById("spec-text");
  ta.select();
  try { document.execCommand("copy"); } catch (e) { /* file:// 下可失败*/ }
});
document.getElementById("b-dl").addEventListener("click", () => {
  const blob = new Blob(
    [document.getElementById("spec-text").value],
    {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "view-spec.json";
  a.click();
  URL.revokeObjectURL(a.href);
});

// 初始化
applyFilters();
fitView();
window.addEventListener("resize", () => { if (vb) { applyView(); } });
</script>"""


__all__ = ["VIEWER_SCHEMA", "VIEW_SPEC_SCHEMA", "FOCUS_KINDS",
           "DEFAULT_SPEC_RESOLUTION", "build_route_viewer",
           "normalize_view_spec", "view_spec_sha256",
           "view_spec_focus_members"]
