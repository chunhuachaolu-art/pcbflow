"""pcbflow editor — ③ E 简版骨架编辑器（FB2；SPEC v1.3 §15 A2 顺延位；v1.2 §4 E 行/§5 B 期）。

范围封顶 = 骨架编辑：同屏拖件（非锚件位姿 x,y,rot）+ 拖拐点（总线骨架内部顶点），
不做全能画布（其余功能一律砍，v1.2 风险表）。

边界（HANDOFF §2 FB2 门 + v1.2 §③/§9）：
- 编辑器不改任何板文件，零写路径（生成器模式：stdout、零落盘、零子进程）；
- 唯一产物 = layout.json 提案（editor-proposal，schema 1.3 新核心产物族，A3）；
- 提案不直接生效：须重过 ③ 布局门/架构预检并经人工批准（确认点 #4）后才可转换应用；
- 锚件永不移动（structures anchors；移动须人工批准并重过门）；
- side/zone/骨架端点（出口侧锚定）/ref 与 bus 身份不可变；
- 核心包无 GUI 硬依赖：本命令只发射自包含离线 HTML（数据内嵌、无外部资源、
  无网络调用）；交互发生在浏览器，导出提案后由 validate 选择项做确定性校验。

数据绑定零漂移：bundle 与校验基准均派生自 coplace_cmd.build_products（同一装载
函数链），不另建第二套坐标/结构口径。

config.py 零新增常量（复用 ③ 常量；UI 常量模块内聚）——历史命令 config_sha256
不因本命令漂移；editor_cmd 自身 hash 单独记入 run_manifest（FF config 隔离先例，
SPEC v1.3 §14.3 A3/§15 FF-1）。
"""

from __future__ import annotations

import datetime
import json
import math
import os

from . import compile_cmd, config, coplace_cmd, envelope, geo, hashing
from .coplace_cmd import (abs_pads, body_bbox, edge_cuts_bbox,
                          import_placement_csv, shape_of, state_from_board,
                          state_with_csv_zones, uq)

SCHEMA_EDITOR = "1.3"          # 新核心产物族（A3：v1.3 起新产物 schema_version=1.3）
DEFAULT_OUT_DIR = config.load_project_manifest().out_dirs["editor"]  # G1+ W-2：值不变来源集中
PROJECT_ID = compile_cmd.PROJECT_ID

# ---- UI/契约常量（非算法阈值；不进 config.py，理由见模块 docstring） -------------
ANGLE_STEP_DEG = 45            # v1.2 §③ 变量：拐点限 45°/90°
GRID_TOL = 1e-6                # 量化/角度容差（0.05mm 格上十进制精确）
FLOAT_EQ = 1e-6

EDITOR_NOTES = (
    "E 简版骨架编辑器（FB2）。同屏拖件+拖拐点；范围封顶=骨架编辑。锚件锁定；"
    "side/zone/骨架端点/ref/bus 身份不可变；坐标 0.05mm 量化；旋转 90° 步进；"
    "拐点最小间距 1.0mm（③ _bend_spacing_ok 同式硬守卫；45°/90° 为 L 形构造风格，"
    "③ 运行时不强制（_bend_candidates 允许轴对齐微移产生非整 45° 段），编辑器同源："
    "角度软记录不阻断）。编辑器不写板文件；导出的 editor-proposal 须重过 ③ 布局门"
    "并经人工批准（确认点 #4）后方可转换/应用（v1.2 §③/§9.4）。"
)


# ---- bundle 构造（与 ③ 同源；只读） -------------------------------------------
def _pad_body_rows(board, st):
    """每 ref：pad bbox（板内包含口径，同 ③ board_edge）与体 bbox（含 0.25 膨胀，
    绘制用）的相对中心偏移+半宽高（mm，**世界系、基准 rot**；两行同帧）。
    旋转由 k×90° 整数变换（Δrot）复原，与 ③ _rot90 同向。"""
    shapes = {ref: shape_of(fp) for ref, fp in sorted(board["footprints"].items())}
    rows = {}
    qnt = config.CPLACE_QUANT
    for ref in sorted(shapes):
        shape = shapes[ref]
        pos = st[ref]
        xs, ys = [], []
        for p in abs_pads(shape, pos["x"], pos["y"], pos["rot"]):
            xs += [p["x"] - p["w"] / 2 / qnt, p["x"] + p["w"] / 2 / qnt]
            ys += [p["y"] - p["h"] / 2 / qnt, p["y"] + p["h"] / 2 / qnt]
        if not xs:
            xs = ys = [pos["x"], pos["y"]]
        pad_bb = (min(xs), min(ys), max(xs), max(ys))     # 量子（绝对、世界系）
        body_bb = body_bbox(shapes, st, ref)              # 量子（绝对、含膨胀）
        rows[ref] = {
            "pad": {"ox_mm": round((pad_bb[0] + pad_bb[2]) / 2 * qnt
                                   - uq(pos["x"]), 3),
                    "oy_mm": round((pad_bb[1] + pad_bb[3]) / 2 * qnt
                                   - uq(pos["y"]), 3),
                    "hw_mm": round((pad_bb[2] - pad_bb[0]) / 2 * qnt, 3),
                    "hh_mm": round((pad_bb[3] - pad_bb[1]) / 2 * qnt, 3)},
            "body": {"ox_mm": round((body_bb[0] + body_bb[2]) / 2 * qnt
                                    - uq(pos["x"]), 3),
                     "oy_mm": round((body_bb[1] + body_bb[3]) / 2 * qnt
                                    - uq(pos["y"]), 3),
                     "hw_mm": round((body_bb[2] - body_bb[0]) / 2 * qnt, 3),
                     "hh_mm": round((body_bb[3] - body_bb[1]) / 2 * qnt, 3)},
        }
    return rows


def build_bundle(out_dir_rel=DEFAULT_OUT_DIR):
    """③ 权威装载链 → 编辑器数据包（只读派生，不另建口径）。"""
    cop = coplace_cmd.build_products(out_dir_rel)
    layout = cop["layout"]["obj"]
    layout_sha = cop["layout"]["sha256"]

    board = geo.parse_board(config.AUDIT_P3_BOARD)
    baseline = import_placement_csv(config.AUDIT_P3_PLACEMENT_CSV)
    st = state_with_csv_zones(state_from_board(board), baseline)
    geom = _pad_body_rows(board, st)
    edge_rect = edge_cuts_bbox(config.AUDIT_P3_BOARD)
    demand = {b["bus_id"]: b["demand_width_mm"]
              for b in layout["layer_plan"]["buses"]}

    placements = []
    for p in sorted(layout["placements"], key=lambda r: r["ref"]):
        g = geom[p["ref"]]
        placements.append({
            "ref": p["ref"], "x": p["x"], "y": p["y"], "rot": p["rot"],
            "side": p["side"], "zone": p["zone"],
            "anchor": p["role"] == "anchor_locked",
            "pad": g["pad"], "body": g["body"],
            "base_rot": p["rot"],
        })
    skeletons = [{
        "bus_id": s["bus_id"], "chain": s["chain"], "net_ids": s["net_ids"],
        "segments": [{"from_ref": seg["from_ref"], "to_ref": seg["to_ref"],
                      "polyline": seg["polyline"],
                      "demand_width_mm": demand.get(s["bus_id"])}
                     for seg in s["segments"]],
    } for s in layout["skeletons"]]

    bundle = {
        "schema_version": SCHEMA_EDITOR,
        "artifact_kind": "editor_bundle",
        "tool": "pcbflow-editor",
        "tool_version": config.TOOL_VERSION,
        "project": PROJECT_ID,
        "coordinate_system": {
            "name": "pcbflow-internal-mm", "units": "mm",
            "axis": "x 右正、y 下正（KiCad 屏幕系）",
            "rotation": "逆时针为正（KiCad 约定）；90° 步进 (x,y)→(y,−x)",
            "not_geographic": True,
        },
        "constants": {
            "quant_mm": config.CPLACE_QUANT,
            "rot_step_deg": config.CPLACE_ROT_STEP,
            "min_bend_spacing_mm": config.CPLACE_MIN_BEND_SPACING_MM,
            "angle_step_deg": ANGLE_STEP_DEG,
        },
        "board": {
            "bbox_mm": [round(v, 3) for v in board["bbox"]],
            "edge_rect_mm": [round(v, 3) for v in edge_rect] if edge_rect else None,
            "footprints": len(board["footprints"]),
        },
        "placements": placements,
        "skeletons": skeletons,
        "base": {
            "layout_sha256": layout_sha,
            "board_sha256": hashing.sha256_file(config.AUDIT_P3_BOARD),
            "placement_csv_sha256": hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV),
            "seed_sha256": hashing.sha256_file(config.SEED_PATH),
            "registry_snapshot_hash":
                layout["registry_consumption"]["registry_snapshot_hash"],
        },
        "notes": EDITOR_NOTES,
    }
    _self_check(bundle)
    return bundle


def _self_check(bundle):
    """发射前确定性自检（envelope verdict 的事实来源）。"""
    refs = [p["ref"] for p in bundle["placements"]]
    assert len(refs) == len(set(refs)), "bundle ref 重复"
    anchors = {p["ref"] for p in bundle["placements"] if p["anchor"]}
    assert len(anchors) == 10, f"锚件数 {len(anchors)} != 10（structures anchors）"
    buses = [s["bus_id"] for s in bundle["skeletons"]]
    assert len(buses) == len(set(buses)), "bundle bus_id 重复"
    for s in bundle["skeletons"]:
        for seg in s["segments"]:
            assert len(seg["polyline"]) >= 3, f"{s['bus_id']} 段点数 <3"
            assert seg["demand_width_mm"] is not None, f"{s['bus_id']} 缺需求宽"


# ---- HTML（自包含离线；数据内嵌；无外部资源/网络调用） --------------------------
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>pcbflow E 骨架编辑器 — STM32H743 Rev-C（FB2）</title>
<style>
:root { --bg:#14171c; --panel:#1d2129; --line:#2e3542; --fg:#d7dce4; --dim:#8b94a3;
        --accent:#4da3ff; --anchor:#e05555; --sel:#ffd24d; }
* { box-sizing:border-box; margin:0; padding:0; }
html,body { height:100%; background:var(--bg); color:var(--fg);
  font:13px/1.5 "Segoe UI","Microsoft YaHei",system-ui,sans-serif; overflow:hidden; }
header { display:flex; align-items:center; gap:14px; padding:8px 14px;
  background:var(--panel); border-bottom:1px solid var(--line); flex-wrap:wrap; }
header h1 { font-size:14px; font-weight:600; }
header .sub { color:var(--dim); font-size:12px; }
.chips { display:flex; gap:8px; }
.chip { background:#262c37; border:1px solid var(--line); border-radius:10px;
  padding:1px 9px; font-size:12px; color:var(--dim); }
.chip b { color:var(--fg); }
button { background:#2a3140; color:var(--fg); border:1px solid var(--line);
  border-radius:6px; padding:5px 12px; cursor:pointer; font:inherit; }
button:hover { border-color:var(--accent); }
button.primary { background:#2b4a77; border-color:var(--accent); }
main { display:flex; height:calc(100% - 84px); }
#stage { flex:1; position:relative; }
svg { width:100%; height:100%; display:block; cursor:default; }
svg.panning { cursor:grabbing; }
aside { width:270px; background:var(--panel); border-left:1px solid var(--line);
  padding:12px; overflow-y:auto; font-size:12px; }
aside h2 { font-size:12px; color:var(--dim); margin:0 0 8px; font-weight:600; }
aside .kv { display:grid; grid-template-columns:78px 1fr; gap:2px 8px; }
aside .kv span:nth-child(odd) { color:var(--dim); }
aside .rules li { margin-left:14px; color:var(--dim); }
aside .rules { margin-top:4px; }
footer { padding:6px 14px; background:var(--panel); border-top:1px solid var(--line);
  color:var(--dim); font-size:11.5px; }
.part rect { fill-opacity:.92; }
.part text { pointer-events:none; }
.part.locked rect { stroke:var(--anchor); stroke-width:2.4; }
.part.sel rect { stroke:var(--sel); stroke-width:2.4; stroke-dasharray:6 3; }
.vtx { fill:#fff; stroke:#333; cursor:move; }
.vtx.end { fill:var(--anchor); cursor:not-allowed; }
.vtx.sel { stroke:var(--sel); stroke-width:2.4; }
#toast { position:absolute; left:50%; bottom:22px; transform:translateX(-50%);
  background:#3a2b2b; color:#ffb4b4; border:1px solid #7a4040; border-radius:6px;
  padding:6px 14px; opacity:0; transition:opacity .25s; pointer-events:none;
  max-width:70%; }
#toast.show { opacity:1; }
#toast.ok { background:#22332a; color:#a8e6c3; border-color:#3f6b52; }
</style>
</head>
<body>
<header>
  <h1>pcbflow E 骨架编辑器</h1><span class="sub">STM32H743 Rev-C · p3 冻结基线（只读快照）</span>
  <div class="chips">
    <span class="chip">件 <b id="c-parts">0</b></span>
    <span class="chip">锚件 <b id="c-anch">0</b></span>
    <span class="chip">总线 <b id="c-bus">0</b></span>
    <span class="chip">改动 <b id="c-chg">0</b></span>
  </div>
  <span style="flex:1"></span>
  <button id="b-undo" title="Ctrl+Z">撤销</button>
  <button id="b-reset">重置</button>
  <button id="b-export" class="primary">导出提案 layout.json</button>
</header>
<main>
  <div id="stage">
    <svg id="board" xmlns="http://www.w3.org/2000/svg"></svg>
    <div id="toast"></div>
  </div>
  <aside>
    <h2>选中对象</h2>
    <div class="kv" id="props">（未选中）</div>
    <h2 style="margin-top:16px">操作</h2>
    <ul class="rules">
      <li>拖件：按住元件拖动（0.05mm 量化）</li>
      <li>旋转：选中后按 <b>R</b>（90° 步进）</li>
      <li>微移：选中后方向键（Shift=0.5mm）</li>
      <li>拖拐点：按住白点拖动（间距 1.0mm 守卫；角度软记录）</li>
      <li>平移/缩放：空白处拖动 / 滚轮</li>
    </ul>
    <h2 style="margin-top:16px">锁定（不可编辑）</h2>
    <ul class="rules">
      <li>锚件（红框）位姿锁死</li>
      <li>骨架端点（红点）= 出口侧锚定</li>
      <li>side / zone / ref / bus 身份</li>
    </ul>
  </aside>
</main>
<footer>红线：编辑器不写任何板文件；本提案导出后须重过 ③ 布局门并经人工批准（确认点 #4）
方可转换/应用；锚件移动须人工批准并重过布局门/架构预检（v1.2 §①/§③）。坐标=KiCad 板坐标系（x 右、y 下，mm）。</footer>
<script type="application/json" id="pcbflow-bundle">__BUNDLE__</script>
<script>
"use strict";
const B = JSON.parse(document.getElementById("pcbflow-bundle").textContent);
const C = B.constants;
const snap = v => Math.round(v / C.quant_mm) * C.quant_mm;
const r3 = v => Math.round(v * 1000) / 1000;

// 状态：仅可变量（x,y,rot / 拐点）；其余一律取自 B（不可变）
const state = {
  pl: {},                                            // ref -> {x,y,rot}
  sk: B.skeletons.map(s => ({bus_id: s.bus_id,
    segments: s.segments.map(g => ({polyline: g.polyline.map(p => p.slice())}))})),
  sel: null,                                         // {kind:'part'|'vtx', ...}
};
B.placements.forEach(p => { state.pl[p.ref] = {x:p.x, y:p.y, rot:p.rot}; });
const baseOf = ref => B.placements.find(p => p.ref === ref);
const baseSkOf = bus => B.skeletons.find(s => s.bus_id === bus);
const undoStack = [];

function cloneState() {
  return {pl: Object.fromEntries(Object.entries(state.pl).map(
            ([r, v]) => [r, {...v}])),
          sk: state.sk.map(s => ({bus_id: s.bus_id,
            segments: s.segments.map(g => ({polyline: g.polyline.map(p => p.slice())}))}))};
}
function pushUndo() { undoStack.push(cloneState());
  if (undoStack.length > 200) undoStack.shift(); }
function doUndo() {
  if (!undoStack.length) { toast("无可撤销", false); return; }
  const s = undoStack.pop();
  state.pl = s.pl; state.sk = s.sk; state.sel = null;
  render(); toast("已撤销", true);
}

// 旋转几何（与 ③ _rot90 同向）：k×90° 步进 (x,y)→(y,−x)
function rot90(x, y, k) { k = ((k % 4) + 4) % 4;
  for (let i = 0; i < k; i++) { const t = x; x = y; y = -t; } return [x, y]; }
function boxAt(ref, kind) {                    // kind: 'pad'|'body'
  const p = baseOf(ref), v = state.pl[ref], g = p[kind];
  const k = Math.round((v.rot - p.base_rot) / 90);
  const [ox, oy] = rot90(g.ox_mm, g.oy_mm, k);
  const even = (k % 2 === 0);
  const hw = even ? g.hw_mm : g.hh_mm, hh = even ? g.hh_mm : g.hw_mm;
  return [v.x + ox - hw, v.y + oy - hh, v.x + ox + hw, v.y + oy + hh];
}
const BUS_COLORS = ["#4da3ff","#59c983","#e0a955","#c98bd8","#5ad1c9","#e07b9d","#9aa7ff"];
const busColor = id => BUS_COLORS[B.skeletons.findIndex(s => s.bus_id === id)
  % BUS_COLORS.length] || "#4da3ff";
function zoneHue(z) { let h = 0;
  for (const ch of (z || "")) h = (h * 31 + ch.codePointAt(0)) % 360; return h; }

// ---- 视图（viewBox = 世界 mm；滚轮缩放/空白拖平移） ---------------------------
// SVG 默认 preserveAspectRatio="xMidYMid meet"：元素宽高比 ≠ viewBox 宽高比时
// 内容按较小轴缩放并居中（信箱留白）——px↔mm 映射必须经 viewT()，禁满幅线性。
const svg = document.getElementById("board");
let vb = null;
function viewT() {
  const r = svg.getBoundingClientRect();
  const s = Math.min(r.width / vb.w, r.height / vb.h);
  return {s, ox: r.left + (r.width - vb.w * s) / 2,
          oy: r.top + (r.height - vb.h * s) / 2};
}
function fitView() {
  const [x0, y0, x1, y1] = B.board.bbox_mm, m = 6;
  let w = x1 - x0 + 2 * m, h = y1 - y0 + 2 * m;
  const r = svg.getBoundingClientRect();
  if (r.width && r.height) {
    const asp = r.width / r.height;
    if (w / h < asp) w = h * asp; else h = w / asp;
  }
  vb = {x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - h / 2, w, h};
  applyView();
}
function mmPerPx() { return viewT().s; }
function applyView() {
  svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
  const px = mmPerPx();
  svg.querySelectorAll(".vtx").forEach(c => c.setAttribute("r",
    ((c.classList.contains("end") ? 3.2 : 4.5) * px).toFixed(3)));
  svg.querySelectorAll("text.lbl").forEach(t =>
    t.setAttribute("font-size", Math.max(0.9, 2.6 * px).toFixed(2)));
}
function toWorld(ev) {
  const t = viewT();
  return {x: vb.x + (ev.clientX - t.ox) / t.s, y: vb.y + (ev.clientY - t.oy) / t.s};
}
svg.addEventListener("wheel", ev => {
  ev.preventDefault();
  const w = toWorld(ev), f = ev.deltaY > 0 ? 1.15 : 1 / 1.15;
  const nw = Math.min(400, Math.max(8, vb.w * f)), nh = nw * vb.h / vb.w;
  vb = {x: w.x - (w.x - vb.x) * nw / vb.w, y: w.y - (w.y - vb.y) * nh / vb.h,
        w: nw, h: nh};
  applyView();
}, {passive: false});

// ---- 渲染 ---------------------------------------------------------------------
function el(name, attrs, parent) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  (parent || svg).appendChild(n); return n;
}
function render() {
  svg.innerHTML = "";
  const defs = el("defs", {});
  const pat = el("pattern", {id: "grid", width: 1, height: 1,
    patternUnits: "userSpaceOnUse"}, defs);
  el("path", {d: "M 1 0 L 0 0 0 1", fill: "none", stroke: "#222833",
    "stroke-width": 0.02}, pat);
  el("rect", {x: vb.x, y: vb.y, width: vb.w, height: vb.h, fill: "url(#grid)"});
  const er = B.board.edge_rect_mm || B.board.bbox_mm;
  el("rect", {x: er[0], y: er[1], width: er[2] - er[0], height: er[3] - er[1],
    fill: "none", stroke: "#5a6577", "stroke-width": 0.12});
  // 骨架：半透明需求宽带来 + 细中线（同屏可见 7 总线）
  state.sk.forEach((s, si) => {
    const col = busColor(s.bus_id), bsk = baseSkOf(s.bus_id);
    s.segments.forEach((g, gi) => {
      const d = g.polyline.map((p, i) => `${i ? "L" : "M"} ${p[0]} ${p[1]}`).join(" ");
      el("path", {d, fill: "none", stroke: col,
        "stroke-width": bsk.segments[gi].demand_width_mm,
        "stroke-opacity": 0.13, "stroke-linejoin": "round"});
      el("path", {d, fill: "none", stroke: col, "stroke-width": 0.12});
    });
  });
  // 器件（普通件先画，锚件最上层）
  const order = [...B.placements].sort((a, b) =>
    (a.anchor - b.anchor) || (a.ref < b.ref ? -1 : 1));
  order.forEach(p => {
    const v = state.pl[p.ref], bb = boxAt(p.ref, "body");
    const g = el("g", {"class": "part" + (p.anchor ? " locked" : "")
      + (state.sel && state.sel.kind === "part" && state.sel.ref === p.ref
         ? " sel" : ""), "data-part": p.ref});
    const hue = zoneHue(p.zone);
    el("rect", {x: bb[0].toFixed(3), y: bb[1].toFixed(3),
      width: (bb[2] - bb[0]).toFixed(3), height: (bb[3] - bb[1]).toFixed(3),
      fill: p.anchor ? "#5a2d2d" : `hsl(${hue} 40% 26%)`,
      stroke: p.anchor ? "#e05555" : `hsl(${hue} 45% 60%)`,
      "stroke-width": p.anchor ? 0.18 : 0.08}, g);
    const t = el("text", {"class": "lbl", x: v.x, y: v.y + 0.5,
      "text-anchor": "middle", fill: p.anchor ? "#ffb4b4" : "#cfd6e0"}, g);
    t.textContent = (p.anchor ? "🔒" : "") + p.ref;
  });
  // 拐点手柄（端点=红=锁定）
  const px = mmPerPx();
  state.sk.forEach((s, si) => s.segments.forEach((g, gi) =>
    g.polyline.forEach((pt, vi) => {
      const end = vi === 0 || vi === g.polyline.length - 1;
      el("circle", {"class": "vtx" + (end ? " end" : "")
        + (state.sel && state.sel.kind === "vtx"
           && state.sel.bus === s.bus_id && state.sel.seg === gi
           && state.sel.vi === vi ? " sel" : ""),
        cx: pt[0], cy: pt[1], r: ((end ? 3.2 : 4.5) * px).toFixed(3),
        "data-vtx": `${s.bus_id}|${gi}|${vi}`});
    })));
  document.getElementById("c-parts").textContent = B.placements.length;
  document.getElementById("c-anch").textContent =
    B.placements.filter(p => p.anchor).length;
  document.getElementById("c-bus").textContent = B.skeletons.length;
  document.getElementById("c-chg").textContent = countChanges();
  showProps();
}
function countChanges() {
  let n = 0;
  B.placements.forEach(p => { const v = state.pl[p.ref];
    if (v.x !== p.x || v.y !== p.y || v.rot !== p.rot) n++; });
  state.sk.forEach((s, si) => s.segments.forEach((g, gi) => {
    const o = baseSkOf(s.bus_id).segments[gi].polyline;
    g.polyline.forEach((pt, vi) => {
      if (pt[0] !== o[vi][0] || pt[1] !== o[vi][1]) n++; }); }));
  return n;
}
function showProps() {
  const d = document.getElementById("props");
  if (!state.sel) { d.textContent = "（未选中）"; return; }
  if (state.sel.kind === "part") {
    const p = baseOf(state.sel.ref), v = state.pl[p.ref];
    d.innerHTML = `<span>ref</span><span>${p.ref}${p.anchor ? "（锚）" : ""}</span>
      <span>x/y</span><span>${r3(v.x)} / ${r3(v.y)} mm</span>
      <span>基线 x/y</span><span>${p.x} / ${p.y} mm</span>
      <span>rot</span><span>${v.rot}°（基线 ${p.rot}°）</span>
      <span>side/zone</span><span>${p.side} / ${p.zone || "—"}</span>`;
  } else {
    const {bus, seg, vi} = state.sel;
    const g = baseSkOf(bus).segments[seg];
    const pt = state.sk.find(x => x.bus_id === bus).segments[seg].polyline[vi];
    const end = vi === 0 || vi === g.polyline.length - 1;
    d.innerHTML = `<span>总线</span><span>${bus}（${g.from_ref}→${g.to_ref}）</span>
      <span>顶点</span><span>#${vi}${end ? "（端点锁定）" : ""}</span>
      <span>x/y</span><span>${r3(pt[0])} / ${r3(pt[1])} mm</span>
      <span>基线 x/y</span><span>${g.polyline[vi][0]} / ${g.polyline[vi][1]} mm</span>
      <span>需求宽</span><span>${g.demand_width_mm} mm</span>`;
  }
}

// ---- 守卫（与 Python 验证器同式：间距硬守卫；角度软记录不阻断） ------------------
const EPS = 1e-9;
function spacingOk(a, b) {
  return Math.hypot(b[0] - a[0], b[1] - a[1]) >= C.min_bend_spacing_mm - EPS;
}
function vertexGuardsOk(pts, vi) {
  if (vi > 0 && !spacingOk(pts[vi - 1], pts[vi]))
    return `最小拐点间距 ${C.min_bend_spacing_mm}mm 守卫（与前一顶点）`;
  if (vi < pts.length - 1 && !spacingOk(pts[vi], pts[vi + 1]))
    return `最小拐点间距 ${C.min_bend_spacing_mm}mm 守卫（与后一顶点）`;
  return null;
}

// ---- 拖拽交互（同屏：拖件 + 拖拐点） --------------------------------------------
let drag = null;
svg.addEventListener("pointerdown", ev => {
  const vtxEl = ev.target.closest ? ev.target.closest("[data-vtx]") : null;
  const partEl = ev.target.closest ? ev.target.closest("[data-part]") : null;
  if (vtxEl) {
    const [bus, seg, vi] = vtxEl.getAttribute("data-vtx").split("|");
    const pts = state.sk.find(s => s.bus_id === bus).segments[+seg].polyline;
    state.sel = {kind: "vtx", bus, seg: +seg, vi: +vi};
    if (+vi === 0 || +vi === pts.length - 1) {
      render(); toast("骨架端点锁定：出口侧锚定（skeleton-seed），不可拖动", false);
      return;
    }
    const w = toWorld(ev);
    drag = {kind: "vtx", bus, seg: +seg, vi: +vi,
            dx: pts[+vi][0] - w.x, dy: pts[+vi][1] - w.y, orig: pts[+vi].slice()};
  } else if (partEl) {
    const ref = partEl.getAttribute("data-part"), p = baseOf(ref);
    state.sel = {kind: "part", ref};
    if (p.anchor) {
      render(); toast(`锚件 ${ref} 锁定：移动须人工批准并重过布局门/架构预检`, false);
      return;
    }
    const v = state.pl[ref], w = toWorld(ev);
    drag = {kind: "part", ref, dx: v.x - w.x, dy: v.y - w.y,
            orig: [v.x, v.y, v.rot]};
  } else {
    drag = {kind: "pan", sx: ev.clientX, sy: ev.clientY, vb: {...vb}};
    svg.classList.add("panning");
  }
  if (drag) { try { svg.setPointerCapture(ev.pointerId); } catch (e) {} }
  render();
});
svg.addEventListener("pointermove", ev => {
  if (!drag) return;
  if (drag.kind === "pan") {
    const s = viewT().s;
    vb = {...drag.vb,
      x: drag.vb.x - (ev.clientX - drag.sx) / s,
      y: drag.vb.y - (ev.clientY - drag.sy) / s};
    applyView(); return;
  }
  const w = toWorld(ev);
  if (drag.kind === "part") {
    const v = state.pl[drag.ref];
    v.x = snap(w.x + drag.dx); v.y = snap(w.y + drag.dy);
  } else {
    const pts = state.sk.find(s => s.bus_id === drag.bus)
      .segments[drag.seg].polyline;
    pts[drag.vi] = [snap(w.x + drag.dx), snap(w.y + drag.dy)];
  }
  render();
});
svg.addEventListener("pointerup", () => {
  if (!drag) return;
  svg.classList.remove("panning");
  if (drag.kind === "vtx") {
    const pts = state.sk.find(s => s.bus_id === drag.bus)
      .segments[drag.seg].polyline;
    const bad = vertexGuardsOk(pts, drag.vi);
    if (bad) { pts[drag.vi] = drag.orig; toast(bad + "，已回退", false); }
    else if (pts[drag.vi][0] !== drag.orig[0] || pts[drag.vi][1] !== drag.orig[1]) {
      pushUndo(); toast("拐点已移动", true);
    }
  } else if (drag.kind === "part") {
    const v = state.pl[drag.ref];
    if (v.x !== drag.orig[0] || v.y !== drag.orig[1]) { pushUndo();
      toast(`${drag.ref} 已移动 Δ(${r3(v.x - drag.orig[0])}, `
        + `${r3(v.y - drag.orig[1])}) mm`, true); }
  }
  drag = null; render();
});
window.addEventListener("keydown", ev => {
  if (ev.key === "Escape") { state.sel = null; render(); }
  else if ((ev.key === "r" || ev.key === "R") && state.sel
           && state.sel.kind === "part") {
    const p = baseOf(state.sel.ref);
    if (p.anchor) { toast(`锚件 ${p.ref} 锁定：旋转同样须人工批准`, false); return; }
    pushUndo();
    state.pl[p.ref].rot = (state.pl[p.ref].rot + C.rot_step_deg) % 360;
    render(); toast(`${p.ref} 旋转 +${C.rot_step_deg}°`, true);
  } else if (ev.key === "z" && (ev.ctrlKey || ev.metaKey)) {
    ev.preventDefault(); doUndo();
  } else if (ev.key.startsWith("Arrow") && state.sel
             && state.sel.kind === "part") {
    const p = baseOf(state.sel.ref);
    if (p.anchor) return;
    ev.preventDefault(); pushUndo();
    const d = ev.shiftKey ? 0.5 : C.quant_mm, v = state.pl[p.ref];
    if (ev.key === "ArrowLeft") v.x = snap(v.x - d);
    if (ev.key === "ArrowRight") v.x = snap(v.x + d);
    if (ev.key === "ArrowUp") v.y = snap(v.y - d);
    if (ev.key === "ArrowDown") v.y = snap(v.y + d);
    render();
  }
});
document.getElementById("b-undo").onclick = doUndo;
document.getElementById("b-reset").onclick = () => {
  pushUndo();
  B.placements.forEach(p => { state.pl[p.ref] = {x: p.x, y: p.y, rot: p.rot}; });
  state.sk = B.skeletons.map(s => ({bus_id: s.bus_id,
    segments: s.segments.map(g => ({polyline: g.polyline.map(p => p.slice())}))}));
  state.sel = null; render(); toast("已重置为基线", true);
};

// ---- 提案导出（唯一产物；不写任何板文件） ---------------------------------------
function buildProposal() {
  const placement_changes = [], vertex_changes = [];
  B.placements.forEach(p => { const v = state.pl[p.ref];
    if (v.x !== p.x || v.y !== p.y || v.rot !== p.rot)
      placement_changes.push({ref: p.ref, from: [p.x, p.y, p.rot],
        to: [r3(v.x), r3(v.y), v.rot]}); });
  state.sk.forEach((s, si) => s.segments.forEach((g, gi) => {
    const o = baseSkOf(s.bus_id).segments[gi].polyline;
    g.polyline.forEach((pt, vi) => {
      if (pt[0] !== o[vi][0] || pt[1] !== o[vi][1])
        vertex_changes.push({bus_id: s.bus_id, segment_index: gi,
          vertex_index: vi, from: [o[vi][0], o[vi][1]],
          to: [r3(pt[0]), r3(pt[1])]}); }); }));
  placement_changes.sort((a, b) => a.ref < b.ref ? -1 : 1);
  vertex_changes.sort((a, b) => a.bus_id < b.bus_id ? -1
    : a.bus_id > b.bus_id ? 1 : a.segment_index - b.segment_index
    || a.vertex_index - b.vertex_index);
  return {
    schema_version: B.schema_version,
    artifact_kind: "editor_proposal",
    tool: "pcbflow-editor", tool_version: B.tool_version,
    mode: "manual_skeleton_edit",
    project: B.project,
    base: B.base,
    placements: B.placements.map(p => { const v = state.pl[p.ref];
      return {ref: p.ref, x: r3(v.x), y: r3(v.y), rot: v.rot,
              side: p.side, zone: p.zone}; })
      .sort((a, b) => a.ref < b.ref ? -1 : 1),
    skeletons: state.sk.map((s, si) => ({bus_id: s.bus_id,
      segments: s.segments.map((g, gi) => ({from_ref: B.skeletons[si]
        .segments[gi].from_ref, to_ref: B.skeletons[si].segments[gi].to_ref,
        polyline: g.polyline.map(p => [r3(p[0]), r3(p[1])])}))})),
    changes: {placement_changes, vertex_changes},
    notes: B.notes,
  };
}
document.getElementById("b-export").onclick = () => {
  const proposal = buildProposal();
  if (!proposal.changes.placement_changes.length
      && !proposal.changes.vertex_changes.length)
    toast("无改动：仍可导出（等同基线的提案）", true);
  const blob = new Blob([JSON.stringify(proposal, null, 1) + "\n"],
    {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "editor-proposal.json";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  toast("提案已导出（editor-proposal.json）", true);
};

// 确定性会话证据口（不引入额外能力，仅暴露既有函数）
window.__pcbflowEditor = {version: 1, buildProposal, state: cloneState,
  base: () => JSON.parse(JSON.stringify(B))};

function toast(msg, ok) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.className = "show" + (ok ? " ok" : "");
  clearTimeout(t._h); t._h = setTimeout(() => t.className = "", 2400);
}
window.addEventListener("resize", applyView);
fitView(); render();
</script>
</body>
</html>
"""


def build_html(bundle) -> str:
    embedded = hashing.json_dumps(bundle).replace("</", "<\\/")
    html = _HTML_TEMPLATE.replace("__BUNDLE__", embedded)
    assert "__BUNDLE__" not in html
    return html


# ---- 提案校验（确定性；与浏览器端守卫同式） -------------------------------------
def _on_grid(v, quant):
    return abs(v / quant - round(v / quant)) <= GRID_TOL


def _r(v, n=3):
    return round(float(v), n)


def _pose_box_mm(pl_row, x, y, rot):
    """bundle 行 + 新位姿 → pad/body bbox（mm；k×90° 整数变换，同 ③ _rot90）。"""
    out = {}
    for kind in ("pad", "body"):
        g = pl_row[kind]
        k = int(round((rot - pl_row["base_rot"]) / 90)) % 4
        ox, oy = g["ox_mm"], g["oy_mm"]
        for _ in range(k):
            ox, oy = oy, -ox
        hw, hh = (g["hw_mm"], g["hh_mm"]) if k % 2 == 0 else (g["hh_mm"], g["hw_mm"])
        out[kind] = (x + ox - hw, y + oy - hh, x + ox + hw, y + oy + hh)
    return out


def _display_path(path):
    """核心产物内只出现 pcbflow 内相对路径（禁主机绝对路径，§14.3）。"""
    p = str(path).replace("\\", "/")
    root = config.PCBFLOW_ROOT.replace("\\", "/").rstrip("/") + "/"
    if p.startswith(root):
        return p[len(root):]
    return p.rsplit("/", 1)[-1]


def _wellformed(proposal):
    """类型防御：垃圾输入 → 结构问题清单（后续语义检查假定通过本门）。"""
    problems = []
    pl = proposal.get("placements")
    sk = proposal.get("skeletons")
    if not isinstance(pl, list):
        problems.append("placements 非列表")
        pl = []
    for i, row in enumerate(pl):
        if not isinstance(row, dict):
            problems.append(f"placements[{i}] 非对象"); continue
        for f in ("ref", "x", "y", "rot", "side", "zone"):
            if f not in row:
                problems.append(f"placements[{i}] 缺字段 {f}")
        try:
            float(row["x"]); float(row["y"])
            if float(row["rot"]) != int(row["rot"]):
                problems.append(f"placements[{i}].rot 非整数")
        except (TypeError, ValueError):
            problems.append(f"placements[{i}] x/y/rot 非数值")
    if not isinstance(sk, list):
        problems.append("skeletons 非列表")
        sk = []
    for i, s in enumerate(sk):
        if not isinstance(s, dict) or not isinstance(s.get("segments"), list):
            problems.append(f"skeletons[{i}] 结构非法"); continue
        for gi, seg in enumerate(s["segments"]):
            pts = seg.get("polyline") if isinstance(seg, dict) else None
            if not isinstance(pts, list):
                problems.append(f"skeletons[{i}].segments[{gi}].polyline 非列表")
                continue
            for vi, pt in enumerate(pts):
                if (not isinstance(pt, (list, tuple)) or len(pt) != 2):
                    problems.append(
                        f"skeletons[{i}].segments[{gi}].polyline[{vi}] 非二元组")
                    continue
                try:
                    float(pt[0]); float(pt[1])
                except (TypeError, ValueError):
                    problems.append(
                        f"skeletons[{i}].segments[{gi}].polyline[{vi}] 非数值")
    return problems


def validate_proposal(proposal_path, out_dir_rel=DEFAULT_OUT_DIR):
    """editor-proposal → 校验报告（统一 envelope 包装）。

    校验项（每项独立 pass/fail；任何 fail → status=blocked/verdict=red）：
      proposal_schema / proposal_wellformed / base_binding（六 hash 过期=conflict）/
      identity_refs / anchor_lock / immutables_side_zone / pose_quant /
      skeleton_endpoints / vertex_rules / board_containment / changes_log。
    """
    try:
        with open(proposal_path, encoding=config.ENCODING) as f:
            proposal = json.load(f)
        assert isinstance(proposal, dict)
        malformed = None
    except (OSError, json.JSONDecodeError, AssertionError) as exc:
        proposal, malformed = None, f"{type(exc).__name__}: {exc}"

    disp = _display_path(proposal_path)
    checks = []

    def add(cid, ok, detail):
        checks.append({"id": cid, "pass": bool(ok), "detail": detail})

    if malformed:
        add("proposal_readable", False, malformed)
        env = envelope.build_envelope(
            command="editor", status="failed", verdict="fail",
            inputs=[{"path": disp, "sha256": None, "role": "config"}],
            artifacts=[], determinism_claim="byte_exact",
            diagnostics=[{"id": "malformed_proposal", "title": malformed}],
            data={"validation": {"checks": checks},
                  "note": "提案不可读/非法 JSON"},
            command_kind="core", schema_version=SCHEMA_EDITOR)
        return env, None

    base = build_bundle(out_dir_rel)
    quant = base["constants"]["quant_mm"]
    min_spacing = base["constants"]["min_bend_spacing_mm"]
    angle_step = base["constants"]["angle_step_deg"]

    # 1. schema
    add("proposal_schema",
        proposal.get("schema_version") == SCHEMA_EDITOR
        and proposal.get("artifact_kind") == "editor_proposal"
        and proposal.get("tool") == "pcbflow-editor"
        and proposal.get("mode") == "manual_skeleton_edit",
        {"schema_version": proposal.get("schema_version"),
         "artifact_kind": proposal.get("artifact_kind"),
         "tool": proposal.get("tool"), "mode": proposal.get("mode"),
         "expect": {"schema_version": SCHEMA_EDITOR,
                    "artifact_kind": "editor_proposal",
                    "tool": "pcbflow-editor",
                    "mode": "manual_skeleton_edit"}})

    # 2. 类型防御门（后续语义检查假定本门通过）
    problems = _wellformed(proposal)
    add("proposal_wellformed", not problems, {"problems": problems})

    # 3. base 绑定（过期=conflict 语义，不静默择一）
    cur = base["base"]
    got = proposal.get("base") or {}
    stale_fields = [k for k in sorted(cur) if got.get(k) != cur[k]]
    add("base_binding", not stale_fields,
        {"current": cur, "proposal": got, "mismatched_fields": stale_fields,
         "note": "任何不匹配=stale/conflict：基线已变，提案须在新基线上重做"
                 "（SPEC §9.4 placement 事实源；不擅自择一）"})

    # 4. 身份：ref/bus/段数/点数不增删
    base_refs = sorted(p["ref"] for p in base["placements"])
    prop_refs = sorted(str(p.get("ref")) for p in proposal.get("placements") or [])
    base_buses = {s["bus_id"]: [len(g["polyline"]) for g in s["segments"]]
                  for s in base["skeletons"]}
    prop_buses = {str(s.get("bus_id")):
                  [len(g.get("polyline") or []) for g in s.get("segments") or []]
                  for s in proposal.get("skeletons") or []}
    add("identity_refs",
        base_refs == prop_refs and len(prop_refs) == len(set(prop_refs))
        and base_buses == prop_buses,
        {"ref_set_equal": base_refs == prop_refs,
         "duplicate_refs": len(prop_refs) != len(set(prop_refs)),
         "bus_layout_equal": base_buses == prop_buses,
         "expect_buses": base_buses, "got_buses": prop_buses})

    # 5-7. 位姿：锚件锁 / side·zone 不可变 / 量化与旋转步进
    base_by_ref = {p["ref"]: p for p in base["placements"]}
    anchor_bad, imm_bad, quant_bad = [], [], []
    for row in sorted(proposal.get("placements") or [],
                      key=lambda r: str(r.get("ref"))):
        b = base_by_ref.get(row.get("ref"))
        if b is None:
            continue
        if (b["anchor"] and (_r(row["x"]) != b["x"] or _r(row["y"]) != b["y"]
                             or int(row["rot"]) != b["rot"])):
            anchor_bad.append({"ref": b["ref"],
                               "base": [b["x"], b["y"], b["rot"]],
                               "got": [_r(row["x"]), _r(row["y"]),
                                       int(row["rot"])]})
        if row.get("side") != b["side"] or row.get("zone") != b["zone"]:
            imm_bad.append({"ref": b["ref"], "field": "side/zone",
                            "base": [b["side"], b["zone"]],
                            "got": [row.get("side"), row.get("zone")]})
        if (not _on_grid(row["x"], quant) or not _on_grid(row["y"], quant)
                or int(row["rot"]) % config.CPLACE_ROT_STEP != 0
                or not 0 <= int(row["rot"]) < 360):
            quant_bad.append({"ref": row.get("ref"), "x": row.get("x"),
                              "y": row.get("y"), "rot": row.get("rot")})
    add("anchor_lock", not anchor_bad,
        {"violations": anchor_bad,
         "note": "锚件永不自动移动；人工移动须批准并重过布局门/架构预检"})
    add("immutables_side_zone", not imm_bad, {"violations": imm_bad,
        "note": "side/zone 非 ③ 变量（变量=x,y,rot+拐点，SPEC §9.3）"})
    add("pose_quant", not quant_bad,
        {"violations": quant_bad, "quant_mm": quant,
         "rot_step_deg": config.CPLACE_ROT_STEP})

    # 8-9. 骨架：端点锁 / 被编辑拐点的量化与间距（③ _bend_spacing_ok 同式）；
    #       角度=软记录（③ 运行时不强制 45°/90°，编辑器同源不阻断）
    end_bad, vtx_bad, soft_angle = [], [], []
    base_sk = {s["bus_id"]: s for s in base["skeletons"]}
    for s in sorted(proposal.get("skeletons") or [],
                    key=lambda x: str(x.get("bus_id"))):
        bs = base_sk.get(s.get("bus_id"))
        if bs is None:
            continue
        for gi, seg in enumerate(s.get("segments") or []):
            bpts = bs["segments"][gi]["polyline"]
            pts = [[_r(p[0]), _r(p[1])] for p in (seg.get("polyline") or [])]
            if len(pts) != len(bpts):
                continue  # identity_refs 已记
            for vi, pt in enumerate(pts):
                if vi in (0, len(pts) - 1):
                    if pt != [_r(bpts[vi][0]), _r(bpts[vi][1])]:
                        end_bad.append({"bus_id": s["bus_id"],
                                        "segment_index": gi, "vertex_index": vi,
                                        "base": bpts[vi], "got": pt})
                    continue
                if pt == [_r(bpts[vi][0]), _r(bpts[vi][1])]:
                    continue  # 未编辑的基线拐点：③ 既成事实，不施加编辑器守卫
                if not (_on_grid(pt[0], quant) and _on_grid(pt[1], quant)):
                    vtx_bad.append({"bus_id": s["bus_id"], "segment_index": gi,
                                    "vertex_index": vi, "kind": "off_grid",
                                    "pt": pt})
                for nb in (pts[vi - 1], pts[vi + 1]):
                    d = math.hypot(nb[0] - pt[0], nb[1] - pt[1])
                    if d < min_spacing - FLOAT_EQ:
                        vtx_bad.append({"bus_id": s["bus_id"],
                                        "segment_index": gi, "vertex_index": vi,
                                        "kind": "min_spacing", "gap_mm": _r(d),
                                        "limit_mm": min_spacing})
                for a, c in ((pts[vi - 1], pt), (pt, pts[vi + 1])):
                    dx, dy = c[0] - a[0], c[1] - a[1]
                    if dx == 0 and dy == 0:
                        vtx_bad.append({"bus_id": s["bus_id"],
                                        "segment_index": gi, "vertex_index": vi,
                                        "kind": "zero_length_segment", "pt": a})
                        continue
                    ang = math.degrees(math.atan2(dy, dx))
                    if abs(ang / angle_step - round(ang / angle_step)) > 1e-7:
                        soft_angle.append({"bus_id": s["bus_id"],
                                           "segment_index": gi,
                                           "vertex_index": vi,
                                           "angle_deg": _r(ang, 4)})
    add("skeleton_endpoints", not end_bad,
        {"violations": end_bad,
         "note": "端点=出口侧锚定（skeleton-seed），仅内部拐点可编辑"})
    add("vertex_rules", not vtx_bad,
        {"violations": vtx_bad, "min_bend_spacing_mm": min_spacing,
         "quant_mm": quant,
         "note": "硬守卫=被编辑拐点的 0.05mm 量化 + 到相邻顶点间距 ≥1.0mm"
                 "（③ _bend_spacing_ok 同式，coplace_cmd.py:1051）；未编辑的基线"
                 "拐点（可离格/退化腿）为 ③ 既成事实不施此卫"})
    soft_angle.sort(key=lambda r: (r["bus_id"], r["segment_index"],
                                   r["vertex_index"]))

    # 10. 板内包含（pad 口径，同 ③ board_edge：pad 含半尺寸在 Edge.Cuts bbox 内）
    edge = base["board"]["edge_rect_mm"]
    out_rows = []
    if edge is not None:
        for row in sorted(proposal.get("placements") or [],
                          key=lambda r: str(r.get("ref"))):
            b = base_by_ref.get(row.get("ref"))
            if b is None:
                continue
            box = _pose_box_mm(b, _r(row["x"]), _r(row["y"]),
                               int(row["rot"]))["pad"]
            if (box[0] < edge[0] - FLOAT_EQ or box[1] < edge[1] - FLOAT_EQ
                    or box[2] > edge[2] + FLOAT_EQ or box[3] > edge[3] + FLOAT_EQ):
                out_rows.append({"ref": row.get("ref"),
                                 "pad_bbox_mm": [_r(v) for v in box],
                                 "edge_rect_mm": edge})
    add("board_containment", not out_rows,
        {"violations": out_rows, "edge_rect_mm": edge,
         "note": "pad bbox（不含体膨胀）须在 Edge.Cuts bbox 内——同 ③ board_edge "
                 "口径（evidence 级；精确裁决=⑥ courtyard DRC）"})

    # 11. changes 对账（提案自述 vs 重建差分；declared≠derived 红线 D7 同精神）
    pc, vc = [], []
    for row in sorted(proposal.get("placements") or [],
                      key=lambda r: str(r.get("ref"))):
        b = base_by_ref.get(row.get("ref"))
        if b is None:
            continue
        if (_r(row["x"]) != b["x"] or _r(row["y"]) != b["y"]
                or int(row["rot"]) != b["rot"]):
            pc.append({"ref": b["ref"], "from": [b["x"], b["y"], b["rot"]],
                       "to": [_r(row["x"]), _r(row["y"]), int(row["rot"])]})
    for s in sorted(proposal.get("skeletons") or [],
                    key=lambda x: str(x.get("bus_id"))):
        bs = base_sk.get(s.get("bus_id"))
        if bs is None:
            continue
        for gi, seg in enumerate(s.get("segments") or []):
            bpts = bs["segments"][gi]["polyline"]
            for vi, pt in enumerate(seg.get("polyline") or []):
                if [_r(pt[0]), _r(pt[1])] != [_r(bpts[vi][0]), _r(bpts[vi][1])]:
                    vc.append({"bus_id": s["bus_id"], "segment_index": gi,
                               "vertex_index": vi,
                               "from": [_r(bpts[vi][0]), _r(bpts[vi][1])],
                               "to": [_r(pt[0]), _r(pt[1])]})
    ch = proposal.get("changes") or {}
    log_ok = (ch.get("placement_changes") == pc
              and ch.get("vertex_changes") == vc)
    add("changes_log", log_ok,
        {"recomputed_placement_changes": pc, "recomputed_vertex_changes": vc,
         "declared_placement_changes": ch.get("placement_changes"),
         "declared_vertex_changes": ch.get("vertex_changes"),
         "note": "自述改动须与重建差分一致（declared≠derived 红线）"})

    all_pass = all(c["pass"] for c in checks)
    report = {
        "schema_version": SCHEMA_EDITOR,
        "artifact_kind": "editor_proposal_validation",
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "project": PROJECT_ID,
        "proposal_path": disp,
        "checks": checks,
        "summary": {
            "all_pass": all_pass,
            "failed": [c["id"] for c in checks if not c["pass"]],
            "placement_change_count": len(pc),
            "vertex_change_count": len(vc),
        },
        "soft_angle_report": {
            "rows": soft_angle,
            "authority": "advisory_only",
            "note": "被编辑拐点的相邻段方向非 45° 步进清单：③ 运行时守卫=仅间距"
                    "（_bend_candidates 轴对齐微移本就产生非整 45° 段），故软记录"
                    "不阻断；重过 ③ 门时由证据向量（bends/detour）统一裁决",
        },
        "note": "校验=编辑器契约（身份/锚件/不可变项/量化/拐点守卫/包含性/对账）；"
                "通过≠③ 布局门通过：提案须重过 ③ 布局门+架构预检并经人工批准"
                "（确认点 #4）方可转换/应用。",
    }
    env = envelope.build_envelope(
        command="editor", status="ok" if all_pass else "blocked",
        verdict="pass" if all_pass else "red",
        inputs=[{"path": disp, "sha256": hashing.sha256_file(proposal_path),
                 "role": "config"}],
        artifacts=[], determinism_claim="byte_exact",
        diagnostics=[] if all_pass else
            [{"id": c["id"], "title": f"校验失败：{c['id']}"}
             for c in checks if not c["pass"]],
        data={"validation": report},
        command_kind="core", schema_version=SCHEMA_EDITOR)
    return env, report


# ---- 产物发射 -------------------------------------------------------------------
def build_products(out_dir_rel=DEFAULT_OUT_DIR):
    """editor 产物构建：bundle → HTML 报告 → inputs/artifacts 清单落盘。

    输入四源=p3-placement-gates-pass 板快照+placement.csv（③ 权威装载
    链）+skeleton-seed（注册表）+layout.json 重建；全部 sha 记账。
    产物=editor HTML 报告（build_html 自 bundle 装配）+清单装配。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)
    bundle = build_bundle(out_dir_rel)
    html = build_html(bundle)
    html_bytes = html.encode(config.ENCODING)

    inputs = [
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": bundle["base"]["board_sha256"], "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/placement.csv",
         "sha256": bundle["base"]["placement_csv_sha256"], "role": "spec"},
        {"path": "out/revc-a3/skeleton-seed.json",
         "sha256": bundle["base"]["seed_sha256"], "role": "registry"},
        {"path": "out/revc-b1/layout.json（③ 权威装载链重建）",
         "sha256": bundle["base"]["layout_sha256"], "role": "config"},
    ]
    artifacts = [{
        "path": f"{out_dir_rel}/editor.html",
        "sha256": hashing.sha256_bytes(html_bytes),
        "role": "core",
    }]
    env = envelope.build_envelope(
        command="editor", status="ok", verdict="pass",
        inputs=inputs, artifacts=artifacts,
        metrics={
            "placements": len(bundle["placements"]),
            "anchors": sum(1 for p in bundle["placements"] if p["anchor"]),
            "buses": len(bundle["skeletons"]),
            "bundle_self_check": "pass（身份唯一/锚件 10/总线需求宽齐）",
            "html_bytes": len(html_bytes),
        },
        diagnostics=[],
        data={
            "command_status": "implemented",
            "gate": {
                "gate": "E_editor_usability（拖件+拖拐点同屏可用）",
                "gate_status": "pending",
                "checker": "browser_session_evidence + 人工可随时复核",
                "note": "确定性部分（数据绑定/离线纯净/导出契约/守卫同式）由测试"
                        "覆盖；交互可用性由浏览器会话证据+人工复核",
            },
            "board_write": False,
            "note": EDITOR_NOTES,
        },
        command_kind="core", schema_version=SCHEMA_EDITOR)

    manifest = {
        "schema_version": SCHEMA_EDITOR,
        "command": "editor",
        "started_at": t0.isoformat(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "elapsed_s": round((datetime.datetime.now(datetime.timezone.utc)
                            - t0).total_seconds(), 3),
        "python_version": f"{os.sys.version_info.major}."
                          f"{os.sys.version_info.minor}."
                          f"{os.sys.version_info.micro}",
        "tool_version": config.TOOL_VERSION,
        "config_sha256": hashing.sha256_file(config.__file__),
        "editor_cmd_sha256": hashing.sha256_file(__file__),
        "spec_sha256": hashing.sha256_file(
            os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "spec_version": "v1.3",
        "schema_versions": {"editor_bundle": SCHEMA_EDITOR,
                            "editor_proposal": SCHEMA_EDITOR,
                            "envelope": SCHEMA_EDITOR},
        "input_sha256": {
            "board_p3": bundle["base"]["board_sha256"],
            "placement_csv_p3": bundle["base"]["placement_csv_sha256"],
            "skeleton_seed": bundle["base"]["seed_sha256"],
            "layout_3_rebuild": bundle["base"]["layout_sha256"],
            "registry_snapshot": bundle["base"]["registry_snapshot_hash"],
        },
        "artifact_sha256": {f"{out_dir_rel}/editor.html":
                            artifacts[0]["sha256"]},
        "board_write": False,
        "note": "E 编辑器=可选 Web 组件（核心包无 GUI 硬依赖）；UI 常量模块内聚、"
                "config.py 零新增（历史 config_sha256 不漂移；editor_cmd hash 单列）",
    }
    return {
        "html": {"obj": None, "bytes": html_bytes,
                 "sha256": hashing.sha256_bytes(html_bytes)},
        "bundle": {"obj": bundle,
                   "bytes": hashing.canonical_json_bytes(bundle),
                   "sha256": hashing.sha256_bytes(
                       hashing.canonical_json_bytes(bundle))},
        "envelope": {"obj": env, "bytes": hashing.canonical_json_bytes(env),
                     "sha256": hashing.sha256_bytes(
                         hashing.canonical_json_bytes(env))},
        "run_manifest": {"obj": manifest,
                         "bytes": hashing.canonical_json_bytes(manifest),
                         "sha256": hashing.sha256_bytes(
                             hashing.canonical_json_bytes(manifest))},
    }
