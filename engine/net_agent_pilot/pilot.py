# -*- coding: utf-8 -*-
"""net_agent_pilot.pilot —— P1 编排 CLI（slice / ingest / status / export / verify）。

用法（route-v5 根）:
  python -m net_agent_pilot.pilot slice  --run run1 --net "Net-(D1-Pad1)"
  python -m net_agent_pilot.pilot ingest --run run1 --round-dir rounds/01-D1
  python -m net_agent_pilot.pilot status --run run1
  python -m net_agent_pilot.pilot export --run run1
  python -m net_agent_pilot.pilot verify --run run1
  python -m net_agent_pilot.pilot scan   --board boards/d [--out scan.json]
  python -m net_agent_pilot.pilot ripup  --run runA --net N --new-run runB

round 目录 = out/net-agent-p1/<run>/rounds/<tag>/，内含:
  brief.md      席位任务书（盲包: 地图+协议+交付契约）
  facts.json    切片事实（board/state hash 锚 + 障碍清单，审计面）
  proposal.json 席位回执（子智能体落盘，ingest 只读）
  result.json   ingest 结果摘要（accepted/rejected + 轮末态哈希）

台账 = out/net-agent-p1/<run>/ledger.jsonl（RunLoop 批模式链式哈希，
全局轮号=跨网 attempt 计数；replay 为状态单源重建路径）。

切片地图是保守提示投影（advisory）: 他网焊盘/板固孔/已布铜 + R5 间距 +
自身半宽 + 板边带; 0.3.2 起 # 之外另有 via 面真值投影（+ 格 = 走线可过、
放 via 触禁——v5 中心线世界: cand:via gap = 中心距 − via 半径
〔via_model_params 单源携带，缺省 0.3〕）;
几何裁决唯一权威=validate_edit 的 v5.drc 同源调用。
"""

import argparse
import json
import math
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from canvas.integration import (  # noqa: E402
    build_state, load_wrapped_board, make_loop_state)
from canvas import loop as canvas_loop          # noqa: E402
from v5.canonical import canonical_json         # noqa: E402
from v5 import geometry_semantics as _gs        # noqa: E402
from v5 import drc as _drc                      # noqa: E402  OPT-04 第二刀别名单源
from v5.adapters.kicad_adapter import (         # noqa: E402  OPT-04 第二刀派生源
    DEFAULT_WIDTH_PRIOR as _DEFAULT_WIDTH_PRIOR)

# OPT-04 第一刀（EXEC-R2）：几何语义声明接线——map/reach 双消费方登记+版本
# 可查出口（薄委托契约见 v5/geometry_semantics.py docstring）。仅声明与输出
# 披露键，不改任何数值策略/本地常量/投影公式（第二刀收口对象本刀不动）。
_gs.declare_consumer("map")     # 保守地图面（cmd_slice 地图 facts / census）
_gs.declare_consumer("reach")   # strict reach 面（cmd_reach）
GEOMETRY_SEMANTICS_VERSION = _gs.VERSION

GENERATOR = "net_agent_pilot.pilot"
VERSION = "0.6.0"      # 0.6.0（V8-PILOT-060）: a·ROI 全板化+层合并布尔化（D-1/D-2）;
                        # b①·checked_pairs 双型（D-3）; b②·export 复现诊断（D-4）;
                        # c·V_CLEARANCE detail @cand 坐标（D-5, canvas 侧）;
                        # d·v1 台账迁移重放（D-6）; e·拒收码表单源渲染（D-7）;
                        # export --out-dir（D-9）。
                        # 0.5.1: ripup 重验对照披露（revived/dropped，run12 F-3）+ slice 轮号防呆（F-4）
                        # 0.5.0: 经验回流环——debrief 复盘包命令 + 简报 playbook 插槽
                        # （用户令: 席位经验汇总筛选迭代; 滤网=机械验证，落地=结构层）。
                        # 0.4.0: reach 封锁扫描。0.3.2: via 面真值投影（+ 符号）
BOARD_DEFAULT = os.path.join("out", "v5-p5", "boards",
                             "badgeleds-do-electronics", "board.json")
OUT_ROOT = os.path.join("out", "net-agent-p1")

# OPT-04 第二刀（EXEC-R3/R3-1，G1 裁 R31-02）：几何常数最小别名同源化 +
# 删除板无关 VIA_RADIUS_MM 第二源——via 半径改由 _obstacles 单点取
# via_model_params（board.via_model 优先）后经 obs["via_radius_mm"] 携带，
# _via_blocked_at 只读携带值，板无关常量与 0.3 回退均不存在。别名=活树
# 单源引用（非第二份拷贝）；不改 drc/adapter/export/geometry_semantics、
# 保守投影公式、退化段阈值或 R5 分面。
TRACK_HALF_MM = _DEFAULT_WIDTH_PRIOR["w_min"] / 2.0   # 缺省档宽半宽（adapter DEFAULT_WIDTH_PRIOR 单源派生; IEEE754 /2 精确: 0.3/2.0 与 0.15 逐位相等）
EDGE_MARGIN_MM = _drc.EDGE_CLEARANCE_MM               # check_edge_clearance 缺省板边带（v5.drc 单源别名）
HOLE_TO_HOLE_MM = _drc.HOLE_TO_HOLE_MM                # v5.drc 板固孔禁布带 margin（hole_via/track_blocked 单源; 非 R5）


# ---------------------------------------------------------------- 载入/状态

def _board_path(args):
    """板路径归一（normpath 统一斜杠风格——state_facts 内嵌 board_path
    原始串，斜杠风格不同=态哈希漂移；归一后任意写法同哈希）。"""
    p = args.board
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(_REPO, p))


def _run_dir(args):
    p = args.run
    return p if os.path.isabs(p) else os.path.join(_REPO, OUT_ROOT, p)


def _ledger_path(run_dir):
    return os.path.join(run_dir, "ledger.jsonl")


def load_board(board_path):
    """wrap 件取体 / 裸 board.v1 原样（判别式与 canvas.loop.replay 同款）。"""
    with open(board_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    board = (raw["board"] if "board" in raw and "schema_version" not in raw
             else raw)
    return board, board["provenance"]["board_sha256"], board_path


def _force_apply_accepted(st, actions, indexes):
    """迁移重放力迫落地（0.6.0 D-6; 镜像 out/canvas-toolchain/anchor-r1/
    run_anchor_r1.py `_force_apply_accepted` 语义 + pilot 台账动作面扩展
    ripup）: 只调 protocol 同款变异缝（add_seg/add_via/remove_net/
    remove_shape），**跳过验证**——重验证会把现行口径下翻案的动作补落/挤掉，
    终态内容漂移，违反「迁移=内容忠实」纪律。route/via/ripup/submit 之外
    的动作 fail-closed（pilot 席位台账动作域）。"""
    from canvas import instantiate as inst
    from canvas.validate import default_width_class
    applied = []
    for i in indexes:
        a = actions[i] if isinstance(i, int) and 0 <= i < len(actions) else None
        if not isinstance(a, dict):
            raise ValueError("迁移重放 accepted 索引 %r 越界/非动作" % (i,))
        act = a.get("action")
        if act == "submit":
            continue
        if act == "route":
            net_id = a["net_id"]
            pid = st.net_partitions(net_id)[0]
            cls = st.widths.get(net_id, default_width_class(st))
            expanded = inst.expand_waypoints(a["waypoints"])
            if len(expanded) == 1:
                expanded = [expanded[0], expanded[0]]
            seg = st.add_seg(net_id, pid, a["layer"], expanded, cls)
            applied.append(seg["shape_id"])
        elif act == "via":
            via = st.add_via(a["net_id"], a["grid"])
            applied.append(via["shape_id"])
        elif act == "ripup":
            if "net_id" in a:
                st.remove_net(a["net_id"])
                applied.append("net:%s" % a["net_id"])
            else:
                st.remove_shape(a["shape_id"])
                applied.append(a["shape_id"])
        else:
            raise ValueError("迁移重放遇冻结世界口径外动作 %r（pilot 台账断言 "
                             "route/via/ripup/submit）" % (act,))
    st.recompute_connectivity()
    st.gc_dangling_vias()
    st.recompute_connectivity()
    return applied


def _replay_migration(board, board_path, ledger):
    """v1 语义台账迁移重放（0.6.0 D-6）→ (st, 披露)。

    字节链（逐行 prev 哈希重算）+ 轮号连续性照旧 fail-closed；态哈希不再
    强等——v2 anchor_semantics 串进 state_facts 后 v1 时代台账逐轮
    state_sha256 在现行引擎下不复算（世界漂移，非台账损坏）。只力迫落地
    accepted 动作（跳过重验证），逐轮复算 sha 差异行登记。终态挂
    ``st.pilot_migration_disclosure``（rows/batch_rows/legacy_rows/
    diverged_rows/final_state_sha256）。"""
    st = make_loop_state(build_state(
        board, board_path, board["provenance"]["board_sha256"]))
    core = st._st
    prev = canvas_loop.ZERO_SHA
    last_round = 0
    n_rows = n_batch = n_legacy = 0
    diverged = []
    with open(ledger, "rb") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            record = json.loads(line.decode("utf-8"))
            if record.get("prev_sha256") != prev:
                raise ValueError(
                    "台账链断裂 @行%d: prev %r != 重算 %r"
                    % (line_no, record.get("prev_sha256"), prev))
            if record.get("round", last_round) != last_round + 1:
                raise ValueError("台账轮号不连续 @行%d（%r）"
                                 % (line_no, record.get("round")))
            last_round = record["round"]
            if "batch" in record:
                n_batch += 1
                idxs = [e.get("index") for e in (record.get("accepted") or [])
                        if isinstance(e, dict)]
                _force_apply_accepted(core, record["batch"], idxs)
            else:
                n_legacy += 1
                edit_list = record.get("edit_list", [])
                _force_apply_accepted(core, edit_list, range(len(edit_list)))
            n_rows += 1
            if core.sha256() != record.get("state_sha256"):
                diverged.append(line_no)
            prev = canvas_loop.sha256_bytes(line)
    st.pilot_migration_disclosure = {
        "rows": n_rows, "batch_rows": n_batch, "legacy_rows": n_legacy,
        "diverged_rows": diverged, "final_state_sha256": core.sha256()}
    return st


def _replay_ledger(ledger, board, board_path):
    """台账重放单源入口（0.6.0 D-6）: 严格 `canvas_loop.replay` 优先（链+
    轮+逐轮态哈希硬校验）；仅当败于「台账态哈希不复算」ValueError（v1 语义
    台账在 v2 引擎下的世界漂移）→ 判 v1 台账 → 迁移模式重放。其它
    ValueError（链断/轮号不连续/重放非确定性）不降级、照旧 fail-closed。"""
    try:
        return canvas_loop.replay(
            ledger, board_path,
            state_factory=lambda b, p: make_loop_state(build_state(
                b, p, b["provenance"]["board_sha256"])))
    except ValueError as exc:
        if not str(exc).startswith("台账态哈希不复算"):
            raise
        return _replay_migration(board, board_path, ledger)


def current_state(board, board_path, run_dir):
    """台账若在则 replay 重建（严格链+轮末态哈希硬校验; v1 语义台账→
    迁移重放，披露挂 st.pilot_migration_disclosure——0.6.0 D-6），否则初始态。"""
    ledger = _ledger_path(run_dir)
    if os.path.isfile(ledger):
        return _replay_ledger(ledger, board, board_path)
    sha = board["provenance"]["board_sha256"]
    return make_loop_state(build_state(board, board_path, sha))


def _next_round(run_dir):
    ledger = _ledger_path(run_dir)
    if not os.path.isfile(ledger):
        return 1
    _, last = canvas_loop._read_chain_tail(ledger)
    return last + 1


# ---------------------------------------------------------------- 几何投影

def _pt_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 <= 1e-18:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / l2
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _rr_dist(px, py, cx, cy, hw, hh):
    """点到圆角矩形边界的距离（矩形内=0）。"""
    dx = max(abs(px - cx) - hw, 0.0)
    dy = max(abs(py - cy) - hh, 0.0)
    return math.hypot(dx, dy)


def _obstacles(st, net_id):
    """本网视角的保守障碍集（mm）。返回 dict，键=图层无关/逐层两类。

    - pads: 他网焊盘铜（circle: (cx,cy,r)；rect: (cx,cy,hw,hh)）——
      本板焊盘 layers 全 "all"，两层都在场。
    - segs: 他网已布段（逐层，(polyline, half_w)）。
    - vias: 他网过孔（(mm, r=via_model_params 半径)，两层）。
    - holes: 板固孔（他网端点孔也计入——保守投影，验证器侧有端点豁免）。
    - holes_all: 全部板固孔不过滤（via 面用: V_HOLE_VIA 对孔**零豁免**，
      本网端点孔同样拦 via）。
    - via_radius_mm: 本板 via 铜半径标量（via_model_params 单源一次推导，
      board.via_model 优先、缺省 0.3）——他网 via 投影与候选 via 半径消费
      同源同值；_via_blocked_at 只读此携带值（第二刀删除板无关第二源）。
    """
    from canvas import instantiate as inst
    from v5 import drc
    from v5.kicad_export import via_model_params

    # OPT-04 第二刀（R31-03）: via 半径单源一次取得——他网 via 投影字面量
    # 与候选 via 半径消费共用同一值，经 obs["via_radius_mm"] 携带。
    via_r = via_model_params(st.board)["radius"]

    own_pids = set(st.net_partitions(net_id))
    own_eps = [tuple(e) for pid in sorted(own_pids)
               for e in st.effective_endpoint_mm(pid)]
    pads, segs, vias, holes = [], [], [], []
    for pid in sorted(st.known_partitions()):
        part = st.board_partition(pid)
        terms = (part.get("geometry") or {}).get("pad_terminals") or []
        eps = st.effective_endpoint_mm(pid)
        foreign = pid not in own_pids
        for t in sorted(terms, key=lambda q: q["endpoint"]):
            k = t.get("endpoint")
            if not isinstance(k, int) or k >= len(eps):
                continue
            cx, cy = eps[k]
            w = float(t["size_mm"][0])
            h = float(t["size_mm"][1]) if len(t["size_mm"]) > 1 else w
            item = ((cx, cy, w / 2.0) if t.get("shape") == "circle"
                    else (cx, cy, w / 2.0, h / 2.0))
            if foreign:
                pads.append(item)
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["net_id"] == net_id:
            continue
        cu = inst.seg_copper(st._st if hasattr(st, "_st") else st, seg)
        segs.append((seg["layer"], [(p[0], p[1]) for p in cu.polyline],
                     cu.half_width))
    for sid in sorted(st.vias):
        v = st.vias[sid]
        if v["net_id"] == net_id:
            continue
        mm = st.lattice.to_mm(*v["grid"])
        vias.append(((mm[0], mm[1]), via_r))
    holes_all = []
    for hx, hy, hr in drc.normalize_holes(st.board.get("holes")):
        holes_all.append((hx, hy, hr))
        # 本网端点孔豁免（同式保守：端点 EPS 重合不投影）——仅走线面;
        # via 面零豁免（hole_via_blocked 语义），holes_all 供 _via_blocked_at。
        # 豁免容差 1e-9（EXEC-R3 第二刀 R31-03 自 1e-6 收齐全仓口径，与
        # validate/executor/route_check 一致; 保持逐轴比较）。
        if any(abs(hx - ex) <= 1e-9 and abs(hy - ey) <= 1e-9
               for ex, ey in own_eps):
            continue
        holes.append((hx, hy, hr))
    # R6 keepout（编辑闸真实障碍: _v_route/_v_via → r6_prefilter_detail →
    # check_keepout，铜矩形 gap≤0 拒收）。sensitive/corridor 属全态/原理域，
    # 不入编辑闸 → 不投影（facts 披露 keepout 数）。
    zones = []
    for z in (st.board.get("zones") or []):
        if z.get("kind") != "keepout":
            continue
        r = z.get("rect") or {}
        try:
            zones.append((z.get("zone_id", "zone"), z.get("layers") or "all",
                          (float(r["x_min"]), float(r["y_min"]),
                           float(r["x_max"]), float(r["y_max"]))))
        except (KeyError, TypeError, ValueError):
            continue
    return {"pads": pads, "segs": segs, "vias": vias, "holes": holes,
            "holes_all": holes_all, "zones": zones,
            "via_radius_mm": via_r}


def _blocked_at(mm, obs, layer, clearance_mm):
    """格点 mm 中心线是否落入保守禁入区（track 面）。"""
    x, y = mm
    for pad in obs["pads"]:
        if len(pad) == 3:
            cx, cy, r = pad
            if math.hypot(x - cx, y - cy) < r + clearance_mm + TRACK_HALF_MM:
                return "pad"
        else:
            cx, cy, hw, hh = pad
            if _rr_dist(x, y, cx, cy, hw, hh) < clearance_mm + TRACK_HALF_MM:
                return "pad"
    for lay, poly, hw_other in obs["segs"]:
        if lay != layer:
            continue
        for a, b in zip(poly[:-1], poly[1:]):
            if _pt_seg_dist(x, y, a[0], a[1], b[0], b[1]) < \
                    clearance_mm + TRACK_HALF_MM + hw_other:
                return "route:" + lay
    for (cx, cy), r in obs["vias"]:
        if math.hypot(x - cx, y - cy) < r + clearance_mm + TRACK_HALF_MM:
            return "via"
    for hx, hy, hr in obs["holes"]:
        if math.hypot(x - hx, y - hy) < hr + clearance_mm + TRACK_HALF_MM:
            return "hole"
    for _zid, zlays, (zx0, zy0, zx1, zy1) in obs.get("zones", []):
        if zlays not in ("all", "signal") and layer not in zlays:
            continue
        if _rr_dist(x, y, (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0,
                    (zx1 - zx0) / 2.0, (zy1 - zy0) / 2.0) < TRACK_HALF_MM:
            return "zone"
    return None


def _via_blocked_at(mm, obs, layer, clearance_mm):
    """格点 mm 放**本网 via** 是否触禁（via 面真值投影; 地图 + 符号口径）。

    与 _blocked_at（走线面保守投影）的口径差——全部来自 v5.drc 单源:
    - via 铜盘半径 obs["via_radius_mm"]（via_model_params 单源携带，
      board.via_model 优先、缺省 0.3）替走线半宽 TRACK_HALF_MM，且走线侧
      **中心线口径不扣对方半宽**（_actual_gap polyline-polyline =
      segment_segment 裸距; run5 r14 "cand:via gap=0.4071067812" = 对角
      0.7071−0.3 逐位吻合）;
    - 板固孔**零豁免**（hole_via_blocked: 本网端点孔同拦 via）且 margin 用
      HOLE_TO_HOLE_MM=0.25 而非 R5;
    - via 是全层 pad 铜（via_coppers 每信号层一枚）→ 他网**任意层**走线都
      入判，不按渲染层过滤。
    板边不入判（check_edge_clearance 中心点口径: via 判定点=圆心，比走线
    保守面更松，不可能单独产生 +）。本函数是**真值**而非保守投影: + 格
    集合 = 放 via 必拒的精确格集（. 格放 via 必过净距面）。"""
    via_r = obs["via_radius_mm"]   # 第二刀（R31-03）: 只读携带值，无 0.3 回退
    x, y = mm
    for pad in obs["pads"]:
        if len(pad) == 3:
            cx, cy, r = pad
            if math.hypot(x - cx, y - cy) < r + clearance_mm + via_r:
                return "pad"
        else:
            cx, cy, hw, hh = pad
            if _rr_dist(x, y, cx, cy, hw, hh) < clearance_mm + via_r:
                return "pad"
    for lay, poly, _hw_other in obs["segs"]:
        for a, b in zip(poly[:-1], poly[1:]):
            if _pt_seg_dist(x, y, a[0], a[1], b[0], b[1]) < \
                    clearance_mm + via_r:
                return "route:" + lay
    for (cx, cy), r in obs["vias"]:
        if math.hypot(x - cx, y - cy) < r + clearance_mm + via_r:
            return "via"
    for hx, hy, hr in obs.get("holes_all", []):
        if math.hypot(x - hx, y - hy) < hr + HOLE_TO_HOLE_MM + via_r:
            return "hole"
    for _zid, zlays, (zx0, zy0, zx1, zy1) in obs.get("zones", []):
        if zlays not in ("all", "signal") and layer not in zlays:
            continue
        # via as_rect = ±via_r 方框; check_keepout rect_rect_gap ≤ 0 拒 → 触边即禁
        if _rr_dist(x, y, (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0,
                    (zx1 - zx0) / 2.0, (zy1 - zy0) / 2.0) <= via_r:
            return "zone"
    return None


def _edge_blocked(st, i, j):
    lat = st.lattice
    x, y = lat.to_mm(i, j)
    ws = st.board["workspace"]
    m = EDGE_MARGIN_MM + TRACK_HALF_MM
    return not (ws["x_min"] + m <= x <= ws["x_max"] - m
                and ws["y_min"] + m <= y <= ws["y_max"] - m)


# ---------------------------------------------------------------- 切片渲染

def _ascii_map(st, net_id, obs, clearance_mm, roi_mode="full"):
    """逐信号层 ROI 地图（行=j 降序、列=i 升序；A/B=端点锚，# 走线禁走，
    + 走线可过但放 via 不可，. 两者皆可）。

    0.6.0 D-1: roi 缺省恒为板全域 (0,0,i_max,j_max)（全板化; 旧 margin=12
    端点周边口径只经 slice --roi legacy 复现）。0.6.0 D-2: 格 cells 只存
    (blocked_bool, via_blocked_bool) 真值——不存 reason 串（旧口径
    "route:F.Cu"≠"route:B.Cu" 致阻塞集相同层不合并、同图分印，run8 遗留
    0.3.3 候选; 渲染/统计仅用真值，行为面不变）。
    同阻塞集的层合并渲染一张（fresh 板无已布铜时各信号层同图）。
    返回 (text, layers_rendered, roi, stats)。
    """
    lat = st.lattice
    pids = st.net_partitions(net_id)
    anchors = []
    for pid in pids:
        for a in st.effective_anchors(pid):
            anchors.append(tuple(a))
    if roi_mode == "legacy":
        pts = [tuple(a) for pid in pids for a in st.effective_anchors(pid)]
        margin = 12
        roi = (max(0, min(p[0] for p in pts) - margin),
               max(0, min(p[1] for p in pts) - margin),
               min(lat.i_max, max(p[0] for p in pts) + margin),
               min(lat.j_max, max(p[1] for p in pts) + margin))
    else:
        roi = (0, 0, lat.i_max, lat.j_max)   # D-1 全板

    layers = st.signal_layers()
    grids = {}
    for layer in layers:
        cells = {}
        for j in range(roi[1], roi[3] + 1):
            for i in range(roi[0], roi[2] + 1):
                why = bool(_edge_blocked(st, i, j)
                           or _blocked_at(lat.to_mm(i, j), obs, layer,
                                          clearance_mm))
                via_why = (None if why else bool(_via_blocked_at(
                    lat.to_mm(i, j), obs, layer, clearance_mm)))
                cells[(i, j)] = (why, via_why)
        grids[layer] = cells
    # 同图合并：阻塞集逐格相等的层共用一张
    groups = []
    for layer in layers:
        for g in groups:
            if grids[g[0]] == grids[layer]:
                g.append(layer)
                break
        else:
            groups.append([layer])

    # 端点标签: 两端网沿用 A/B；多端网用数字 1..N（重合锚取先到标签）
    if len(anchors) <= 2:
        labels = {anc: lab for anc, lab in zip(
            anchors, ["A", "B"][:len(anchors)])}
    else:
        labels = {}
        for k, anc in enumerate(anchors):
            labels.setdefault(anc, str(k + 1))

    maps = []
    for g in groups:
        lines = []
        # ROI 原点披露（0.5.0: run9 复盘——4/7 席位自行反推列偏移、1 席因此
        # 误读撞 #; 行首 5 字符=行号标签，首个数据字符=i=roi[0]）
        lines.append("/".join(g) + "（ROI: i ∈ [%d,%d]、j ∈ [%d,%d]; "
                     "每行前 5 个字符是行号 j 标签，第一个地图字符 = i=%d）"
                     % (roi[0], roi[2], roi[1], roi[3], roi[0]))
        # 列标尺（每 10 列一个数字行）
        header = [" " * 5]
        for i in range(roi[0], roi[2] + 1):
            header.append(str(i // 10 % 10) if i % 10 == 0 else " ")
        lines.append("".join(header))
        for j in range(roi[3], roi[1] - 1, -1):
            row = ["%4d " % j]
            for i in range(roi[0], roi[2] + 1):
                ij = (i, j)
                if ij in labels:
                    row.append(labels[ij])
                elif ij in anchors:
                    row.append("a")
                elif grids[g[0]][ij][0]:
                    row.append("#")
                elif grids[g[0]][ij][1]:
                    row.append("+")
                else:
                    row.append(".")
            lines.append("".join(row))
        maps.append("\n".join(lines))
    vals = grids[groups[0][0]].values()
    stats = {"roi": list(roi),
             "blocked_cells": sum(1 for v in vals if v[0]),
             "via_only_cells": sum(1 for v in vals if not v[0] and v[1])}
    return "\n\n".join(maps), [g for g in groups], roi, stats


BRIEF_TEMPLATE = """# 单网布线任务 · round {round}

你是 PCB 布线席位，只负责把下面这一条网连通，不做任何其它事。

## 目标
- net_id: {net_id}
{terminals}

## 板面事实（round {round} 时点的保守投影）
- 格点阵: pitch {pitch}mm；格点 [i,j] 的毫米坐标 x = {x0} + {pitch}*i，y = {y0} + {pitch}*j；i ∈ [0,{i_max}]，j ∈ [0,{j_max}]。
- 图例: {anchor_legend}；# = 禁走格（他网焊盘/板固孔/已布铜/禁布区的保守投影，含 0.5mm 间距与自身 0.15mm 半宽）；+ = 走线可过、**放 via 不可**（via 面投影）；. = 自由格（走线/放 via 皆可）。
- 地图行 = j（从大到小），列 = i（从小到大）。{map_scope_note}
- **地图只是提示；机械验证器才是唯一裁决。** 若走线被拒收，以拒收 detail 为准修正。

{maps}

- 层: {layers}；{pad_note}{bcu_note}
- 走线宽度: 缺省档 0.3mm（本任务不要发 width_class 动作）。
- 板固孔 {n_holes} 个、禁布区 {n_zones} 个（均已含入 # 投影）；via 直径 0.6mm，{via_hint}。**放 via 比走线挑**: + 格 = 走线可过但放 via 会触净距拒收（via 铜盘半径 0.3mm 比走线半宽 0.15mm 胖）; 且板固孔对 via **零豁免**——别把 via 放在孔上或本网端点孔旁（孔径+0.25mm 禁布带）。
{zone_facts}{zone_semantics}{playbook_note}

## 输出动作协议（canvas-edit-v2，fail-closed）
把一个 JSON 对象写到文件（UTF-8、纯 JSON、无代码围栏无注释）:
{proposal_path}

格式:
{{"round": {round}, "actions": [
  {{"action": "route", "net_id": "{net_id}", "waypoints": [[i,j], [i,j], ...], "layer": "F.Cu"}},
  {{"action": "submit"}}
]}}

- 一切坐标必须是整数格点 [i,j]；浮点数、毫米值、字符串坐标 = 整批拒收。
- waypoints ≥ 2 个，是**跳跃点**: 相邻两点之间按"先走 x 后走 y"的 L 形展开成实际路径（展开路径必须全程避开 # 格）。
- {attach_rule}
- via 动作的 grid 必须落在你自己的路径格点上（本批或已落盘均可）；无必要时不用 via。
- 批内最后一个动作必须是 submit，submit 后不得再有动作。
- 缺键、合同外键、未知动作 = 整批拒收。
{topology_note}
## 语义层拒收码（逐动作，改了再交; 单源=canvas.protocol.SEAT_REJECTION_CODES）
{rejection_codes}

## 交付
- 只写一个文件: {proposal_path}
- 内容 = 纯 JSON 文本。写完即止，不做其它操作。
{prior_block}"""


def _brief_sections(anchors, eps):
    """(terminals 块, 图例, 附着规则, via 提示)——两端/多端口径分流。"""
    n = len(anchors)
    names = ["A", "B"][:n] if n <= 2 else [str(k + 1) for k in range(n)]
    lines = ["- 端点 %s = 格点 %s（毫米 %s）" % (
        names[k], list(g), [round(v, 3) for v in m])
        for k, (g, m) in enumerate(zip(anchors, eps))]
    if n <= 2:
        lines.append("- 用铜走线把 A 与 B 连通。")
        legend = "A/B = 本网端点锚（走线首末点必须恰落在锚格点上）"
        attach = ("waypoints 的首点与末点必须恰为端点 A / B 的锚格点，"
                  "或本网 via 所在格点（多段衔接时; 见禁布区说明）。")
        via_hint = "本网单层直连一般不需要 via"
    else:
        lines.append("- 用铜走线把以上 %d 个端点连成一个连通整体（任意拓扑）。" % n)
        legend = ("地图上的数字 = 本网端点锚编号（走线首末点必须恰落在"
                  "锚格点或本网 via 格点上）")
        attach = ("每条 route 的首点与末点必须恰为该网任一端点锚格点，"
                  "或本网 via 所在格点（中途铜上挂接不算附着）。")
        via_hint = "多端网可在自己路径上放 via 作汇合附着点"
    return "\n".join(lines), legend, attach, via_hint


def _topology_note(n):
    """多端网拓扑规则节（两端网=空串）。规则全部对应验证器/连通账本机械事实:
    端点只在段首末附着（state.recompute_connectivity）、段间共享格点须 via、
    同网铜 same_net_exempt 豁免间距、批内 via+route 互担（batch_ctx）。"""
    if n <= 2:
        return ""
    return "\n".join([
        "",
        "## 多端网拓扑规则（本网 %d 端）" % n,
        "- 一批内发**多条 route 动作**（同一 net_id）合成一棵连通树，批内最后仍是 submit；动作顺序不限（编排器自动解依赖）。",
        "- **每个端点必须作为某条 route 的首点或末点出现**——走线只是途经某端点不算把它连通（连通账本硬规则）。",
        "- 推荐链式: 1→2、2→3、3→4 ……（在端点锚处分段相接，公共端点锚会自动桥接两段；最少 %d 段）。" % (n - 1),
        "- 也可汇合式: 先发一条 route 途经汇合格点，再发 via 落在该格点，其余端点的 route 以该格点为首/末点——via 格点是合法附着点，可接多条段。",
        "- 段与段可以任意交叉/重叠（同网铜自动合并，不做间距检查）；不同段可以用不同层。",
        "",
    ])


def _prior_rejection_block(result_path):
    """result.json → 回叫简报的上轮裁决节（拒收码+detail / 未连通审计，逐字）。"""
    with open(result_path, "r", encoding="utf-8") as f:
        res = json.load(f)
    lines = ["", "## 上一轮裁决记录（机械验证器，逐字）",
             "- 上轮 round: %s，verdict: %s" % (res.get("round"),
                                                res.get("verdict"))]
    for r in res.get("rejected") or []:
        lines.append("- %s: %s" % (r.get("code"), r.get("detail")))
    for n, cd in (res.get("chain_audit") or {}).items():
        lines.append("- 网 %s 的动作已被接受，但连通审计未通过: "
                     "dangling_segs=%s junctions_missing_via=%s"
                     % (n, cd.get("dangling_segs"),
                        cd.get("junctions_missing_via")))
        unconn = cd.get("unconnected_terminals")
        if unconn:
            lines.append("- **以下端点还没有任何段的端点附着（未接入树）: %s "
                         "——请布新段把它们接入。**" % unconn)
    if res.get("chain_audit") and not (res.get("rejected") or []):
        lines.append("- 可能原因: 有端点只是被走线途经而非某条 route 的首/末点，"
                     "或两段在共享格点处缺 via。请调整分段，让每个端点都是"
                     "某条 route 的首/末点（链式最稳）。")
        lines.append("- 地图不显示本网自己的铜（可任意重叠，不算障碍）。")
    lines.append("- 上面的地图是**最新状态**（含上轮已被接受的其它网铜）。"
                 "请修正后重新提交。")
    return "\n".join(lines)


def _slug(net_id):
    """net_id → 文件名安全的短标签（Net-(D1-Pad1) → D1）。"""
    import re
    m = re.search(r"\(([A-Za-z0-9]+)", net_id)
    return (m.group(1) if m else re.sub(r"[^A-Za-z0-9]", "", net_id))[:16]


def _board_has_pads(st):
    """板内任一分区带 pad_terminals 即"有焊盘板"（简报注记口径）。"""
    core = st._st if hasattr(st, "_st") else st
    return any(((core.board_partition(pid).get("geometry") or {})
                .get("pad_terminals") or [])
               for pid in sorted(core.known_partitions()))


def _rejection_codes_block():
    """拒收码节渲染（0.6.0 D-7 单源）: canvas.protocol.SEAT_REJECTION_CODES
    （恰 9 码，v1.2 表语义迁移入内）逐行渲染——自动补 v1.2 前缺失的
    V_HOLE_VIA; 漂移守卫见 net_agent_pilot/tests（对 PLAYBOOK-BRIEF.md）。"""
    from canvas.protocol import SEAT_REJECTION_CODES
    return "\n".join("- %s: %s" % (code, text)
                     for code, text in SEAT_REJECTION_CODES)


def cmd_slice(args):
    board, sha, board_path = load_board(_board_path(args))
    st = current_state(board, board_path, _run_dir(args))
    net_id = args.net
    if net_id not in st.known_nets():
        raise SystemExit("未知网 %r（板内网见 board.json）" % net_id)
    if st.connectivity.get(net_id):
        raise SystemExit("网 %s 已连通（先 ripup 才能重布——P1 不做）" % net_id)
    # 轮号防呆（run12 F-4: 两起显式轮号错位被 E_ROUND_MISMATCH 占位）:
    # 倒退=拒切; 超前>1=并行预留合法但披露; 缺省=尾轮+1。
    tail = _next_round(_run_dir(args)) - 1
    if getattr(args, "round", None) is not None and args.round <= tail:
        raise SystemExit("轮号 %d ≤ 台账尾轮 %d（倒退; 缺省=尾轮+1=%d）"
                         % (args.round, tail, tail + 1))
    round_no = args.round if getattr(args, "round", None) else \
        _next_round(_run_dir(args))
    if getattr(args, "round", None) and args.round > tail + 1:
        print(json.dumps({"warn": "round_ahead", "round": args.round,
                          "next": tail + 1,
                          "note": "并行切片预留轮号; 摄入顺序保证连续性"},
                         ensure_ascii=False))
    r5 = float(board["hard_rules"]["R5"]["min_clearance_mm"])
    obs = _obstacles(st, net_id)
    # 0.6.0 D-1: ROI 口径开关（缺省 full=板全域; legacy=旧 margin=12 端点
    # 周边，仅供 §3 机械 A/B 复现; facts.json 记 roi 模式）
    roi_mode = getattr(args, "roi", None) or "full"
    maps, groups, roi, stats = _ascii_map(st, net_id, obs, r5, roi_mode=roi_mode)
    map_scope_note = ("地图覆盖全板（ROI=板全域）。" if roi_mode == "full" else
                      "地图只覆盖端点周边 ROI，允许走 ROI 外"
                      "（地图外障碍需自行保守避让）。")
    stats = dict(stats, roi_mode=roi_mode)
    pids = st.net_partitions(net_id)
    anchors = [tuple(a) for pid in pids for a in st.effective_anchors(pid)]
    eps = [tuple(e) for pid in pids for e in st.effective_endpoint_mm(pid)]
    seg_layers = sorted({seg["layer"] for seg in st._st.segs.values()}
                        if hasattr(st, "_st") else
                        {seg["layer"] for seg in st.segs.values()})
    bcu = ("B.Cu 当前无已布铜。" if "B.Cu" not in seg_layers
           else "已布铜层: %s。" % "、".join(seg_layers))
    pad_note = ("本板焊盘为通孔（各信号层都在场）。" if _board_has_pads(st)
                else "本板无焊盘: 端点是纯附着点、自身无铜延展——间距只看"
                     "铜 vs 铜（他网走线贴经端点格不构成违例）。")
    zone_facts = ("- 禁布区坐标（毫米矩形，全板有效）: %s。" % "；".join(
        "%s = x[%g,%g] × y[%g,%g]（%s）" % (zid, r[0], r[2], r[1], r[3],
           "全层" if lays == "all" else str(lays))
        for zid, lays, r in obs["zones"]) + "\n" if obs["zones"] else "")
    zone_semantics = (
        "- 禁布区判定语义（机械事实）: **每条 route 按整条路径的外接矩形检查禁布区**"
        "——包围盒触区即该动作拒收，哪怕实际线段全部绕开。若端点在禁布区的 x 或 y 投影内"
        "且路径跨带（单条绕行的包围盒必然触区），须**拆成多条 route 动作**: 在转折格点放"
        "本网 via（格式 {{\"action\":\"via\",\"net_id\":\"{nid}\",\"grid\":[i,j]}}，"
        "grid 须在本网路径格点上），相邻段以该格点为首/末点衔接——via 格点是合法附着点，"
        "各段外接矩形小、可各自避开禁布区。批内动作顺序不限（编排器自动解依赖）。\n"
        .format(nid=net_id) if obs["zones"] else "")

    tag = args.tag or ("r%02d-%s" % (round_no, _slug(net_id)))
    rd = os.path.join(_run_dir(args), "rounds", tag)
    os.makedirs(rd, exist_ok=True)
    proposal_path = os.path.join(rd, "proposal.json")

    lat = st.lattice
    prior = (_prior_rejection_block(args.prior_rejection)
             if args.prior_rejection else "")
    playbook = ""
    if getattr(args, "playbook", None):
        with open(args.playbook, "r", encoding="utf-8") as f:
            body = f.read().strip()
        if body:
            playbook = ("\n## 前席经验（已机械验证筛选; 提示非裁决）\n"
                        + body + "\n")
    terminals, legend, attach, via_hint = _brief_sections(anchors, eps)
    brief = BRIEF_TEMPLATE.format(
        round=round_no, net_id=net_id,
        terminals=terminals, anchor_legend=legend,
        attach_rule=attach, via_hint=via_hint,
        topology_note=_topology_note(len(anchors)),
        pitch=lat.pitch, x0=lat.x0, y0=lat.y0,
        i_max=lat.i_max, j_max=lat.j_max,
        maps=maps, layers=" / ".join(st.signal_layers()), bcu_note=bcu,
        pad_note=pad_note, zone_facts=zone_facts,
        zone_semantics=zone_semantics, playbook_note=playbook,
        map_scope_note=map_scope_note,
        rejection_codes=_rejection_codes_block(),
        n_holes=len(obs["holes"]), n_zones=len(obs["zones"]),
        prior_block=prior,
        proposal_path=proposal_path.replace("\\", "/"))
    with open(os.path.join(rd, "brief.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(brief)
    facts = {
        "schema_version": "net-agent-p1/slice-v2",
        "generator": GENERATOR, "version": VERSION,
        "geometry_semantics": GEOMETRY_SEMANTICS_VERSION,   # OPT-04 声明披露键
        "board_id": board["board_id"], "board_sha256": sha,
        "state_sha256": st.sha256(), "round": round_no,
        "net_id": net_id, "terminals_grid": [list(a) for a in anchors],
        "terminals_mm": [[round(v, 3) for v in e] for e in eps],
        "lattice": lat.as_dict(), "layers": st.signal_layers(),
        "clearance_mm": r5, "track_half_mm": TRACK_HALF_MM,
        "obstacles": {"pads": len(obs["pads"]), "holes": len(obs["holes"]),
                      "holes_via_face": len(obs.get("holes_all", [])),
                      "foreign_segs": len(obs["segs"]),
                      "foreign_vias": len(obs["vias"]),
                      "keepout_zones": len(obs["zones"])},
        "map_groups": groups, "map_stats": stats,
    }
    with open(os.path.join(rd, "facts.json"), "wb") as f:
        f.write(canonical_json(facts))
    print(json.dumps({"tag": tag, "round": round_no, "brief": os.path.join(
        rd, "brief.md").replace("\\", "/"), "roi": stats["roi"],
        "blocked": stats["blocked_cells"]}, ensure_ascii=False))


# ---------------------------------------------------------------- 摄入

def _append_round(st, ledger, actions_text, round_no):
    """单轮批施加 + 台账落链（行格式与 canvas.loop 批模式逐字段同构；
    绕过 RunLoop.run 是因其 pack_view 不支持多端点分区——席位盲包已由
    slice 提供，SVG pack 非本 pilot 消费面。replay 兼容性由链字段保证）。"""
    import copy as _copy
    from canvas import protocol as _proto
    from canvas.pack import state_call
    prev, _last = canvas_loop._read_chain_tail(ledger)
    record = {
        "round": round_no, "prev_sha256": prev,
        "actions_sha256": canvas_loop.sha256_bytes(
            actions_text.encode("utf-8")),
        "verdict": canvas_loop.VERDICT_APPLIED,
    }
    try:
        actions = _proto.parse_batch(actions_text, round_no)
    except Exception as exc:
        if canvas_loop._is_batch_reject(exc):
            record["verdict"] = canvas_loop.VERDICT_BATCH_REJECTED
            record["accepted"] = []
            record["rejected"] = [{"index": None, "action": None,
                                   "code": getattr(exc, "code", None),
                                   "detail": str(exc)}]
            record["edit_list"] = []
            record["batch"] = []
        else:
            raise
    else:
        batch_actions = _proto.reorder_batch(_copy.deepcopy(actions))
        record["batch"] = batch_actions
        results = st.apply_batch(_copy.deepcopy(batch_actions), round_no)
        accepted, rejected, edit_list = canvas_loop._summarize_batch(
            batch_actions, results)
        record["accepted"] = accepted
        record["rejected"] = rejected
        record["edit_list"] = edit_list
    record["state_sha256"] = state_call(st, "state_sha256")
    ordered = {
        "round": record["round"], "prev_sha256": record["prev_sha256"],
        "state_sha256": record["state_sha256"],
        "actions_sha256": record["actions_sha256"],
        "accepted": record["accepted"], "rejected": record["rejected"],
        "edit_list": record["edit_list"], "verdict": record["verdict"],
        "batch": record["batch"],
    }
    canvas_loop._append_line(ledger, ordered)
    return ordered


def _unconnected_terminals(core, net_id):
    """网内尚无任何段以之为首/末点的端点锚（= 未接入树，回叫指位用）。"""
    terms = set()
    for pid in core.net_partitions(net_id):
        for a in core.effective_anchors(pid):
            terms.add(tuple(a))
    ends = set()
    for sid in sorted(core.segs):
        seg = core.segs[sid]
        if seg["net_id"] == net_id:
            ends.add(tuple(seg["grid"][0]))
            ends.add(tuple(seg["grid"][-1]))
    return sorted(list(t) for t in terms - ends)


def cmd_ingest(args):
    board, sha, board_path = load_board(_board_path(args))
    run_dir = _run_dir(args)
    rd = args.round_dir
    if not os.path.isabs(rd):
        rd = os.path.join(run_dir, rd)
    proposal_path = os.path.join(rd, "proposal.json")
    if not os.path.isfile(proposal_path):
        raise SystemExit("proposal 不存在: %s" % proposal_path)
    st = current_state(board, board_path, run_dir)
    round_no = _next_round(run_dir)
    ledger = _ledger_path(run_dir)
    with open(proposal_path, "r", encoding="utf-8") as f:
        actions_text = f.read()
    ordered = _append_round(st, ledger, actions_text, round_no)
    core = st._st if hasattr(st, "_st") else st
    nets_touched = sorted({a.get("net_id") for a in ordered["batch"]
                           if isinstance(a, dict) and a.get("net_id")})
    result = {
        "schema_version": "net-agent-p1/ingest-v2",
        "round": ordered["round"], "verdict": ordered["verdict"],
        "accepted": ordered["accepted"], "rejected": ordered["rejected"],
        "state_sha256": ordered["state_sha256"],
        "connectivity": {n: bool(core.connectivity.get(n))
                         for n in nets_touched},
        "chain_audit": {n: dict(
            core.chain_detail.get(n) or {},
            unconnected_terminals=_unconnected_terminals(core, n))
            for n in nets_touched
            if not core.connectivity.get(n)},
    }
    with open(os.path.join(rd, "result.json"), "wb") as f:
        f.write(canonical_json(result))
    print(json.dumps({"round": ordered["round"], "verdict": ordered["verdict"],
                      "n_accepted": len(ordered["accepted"]),
                      "rejected": ordered["rejected"],
                      "state_sha256": ordered["state_sha256"][:16]},
                     ensure_ascii=False))


# ---------------------------------------------------------------- 扫描/分叉


def _iter_board_paths(args):
    """--board 接受单板文件或目录（目录=其下全部 *.json，按名排序）。"""
    p = _board_path(args)
    if os.path.isdir(p):
        import glob
        return sorted(glob.glob(os.path.join(p, "*.json")))
    return [p]


def cmd_scan(args):
    """全板锚点口袋扫描（初始态）。

    死锁口袋判据 = run3 F1 机械证明的板级推广：任何附着走线必含强制
    stub 段 [端点真实毫米坐标 → 锚格心]（instantiate.segment_mm 首点=真实
    端点、首格点=锚格心），故该段到他网铜/板固孔的净距（**验证器同款
    原语 v5.clearance**，不扣自身半宽）< R5 ⟹ 该锚点方向/层/宽无关地
    不可附着。附带保守投影密度指标（席位地图同口径）。
    """
    from v5 import drc
    from v5.metrics import clearance as _clr

    boards = []
    for bp in _iter_board_paths(args):
        try:
            board, sha, board_path = load_board(bp)
            st = make_loop_state(build_state(board, board_path, sha))
        except Exception as exc:  # noqa: BLE001 —— 单板失败不拖垮全表，落表披露
            boards.append({"path": bp.replace("\\", "/"), "error": str(exc)})
            continue
        core = st._st if hasattr(st, "_st") else st
        lat, r5 = core.lattice, float(
            board["hard_rules"]["R5"]["min_clearance_mm"])
        ws = board["workspace"]
        area_mm2 = (ws["x_max"] - ws["x_min"]) * (ws["y_max"] - ws["y_min"])
        holes = list(drc.normalize_holes(board.get("holes")))

        pid2net = {}
        for n in core.known_nets():
            for pid in core.net_partitions(n):
                pid2net[pid] = n
        pads_all, dead, per_net, anchors_total = [], [], {}, 0
        for pid in sorted(core.known_partitions()):
            part = core.board_partition(pid)
            terms = (part.get("geometry") or {}).get("pad_terminals") or []
            eps = core.effective_endpoint_mm(pid)
            for t in sorted(terms, key=lambda q: q["endpoint"]):
                k = t.get("endpoint")
                if not isinstance(k, int) or k >= len(eps):
                    continue
                w = float(t["size_mm"][0])
                h = float(t["size_mm"][1]) if len(t["size_mm"]) > 1 else w
                pads_all.append((pid2net.get(pid, "?"), k,
                                  t.get("shape") == "circle",
                                  (eps[k][0], eps[k][1], w / 2.0) if
                                  t.get("shape") == "circle" else
                                  (eps[k][0], eps[k][1], w / 2.0, h / 2.0)))
        for n in sorted(core.known_nets()):
            pids = core.net_partitions(n)
            anchors = [tuple(a) for pid in pids
                       for a in core.effective_anchors(pid)]
            eps = [tuple(e) for pid in pids
                   for e in core.effective_endpoint_mm(pid)]
            own_eps = eps
            ndead = []
            for g, m in zip(anchors, eps):
                anchors_total += 1
                # 强制 stub 段 [真实端点 mm → 锚格心 mm]——每条附着走线必含
                # （instantiate.segment_mm 首点=真实端点、首格点=锚格心），
                # 与验证器同款距离原语（v5.clearance）算净距。
                stub_a, stub_b = m, lat.to_mm(*g)
                best = None
                for owner, k, is_circ, geom in pads_all:
                    if owner == n:
                        continue
                    gap = (_clr.pad_segment_distance(
                        (geom[0], geom[1]), geom[2], stub_a, stub_b)
                        if is_circ else
                        _clr.segment_rect_distance(
                            stub_a, stub_b,
                            {"x_min": geom[0] - geom[2],
                             "y_min": geom[1] - geom[3],
                             "x_max": geom[0] + geom[2],
                             "y_max": geom[1] + geom[3]}))
                    if best is None or gap < best[0]:
                        best = (gap, "pad:%s:%s" % (owner, k))
                for hi, (hx, hy, hr) in enumerate(holes):
                    if any(abs(hx - ex) <= 1e-9 and abs(hy - ey) <= 1e-9
                           for ex, ey in own_eps):
                        continue    # 本网端点孔豁免（同 _obstacles 口径;
                                    # EXEC-R3 第二刀 1e-9 全仓口径，逐轴比较）
                    gap = _clr.pad_segment_distance((hx, hy), hr,
                                                    stub_a, stub_b)
                    if best is None or gap < best[0]:
                        best = (gap, "hole:%d" % hi)
                edge_tight = not (ws["x_min"] + EDGE_MARGIN_MM + TRACK_HALF_MM
                                  <= m[0] <= ws["x_max"] - EDGE_MARGIN_MM
                                  - TRACK_HALF_MM and
                                  ws["y_min"] + EDGE_MARGIN_MM + TRACK_HALF_MM
                                  <= m[1] <= ws["y_max"] - EDGE_MARGIN_MM
                                  - TRACK_HALF_MM)
                if best is not None and best[0] < r5:
                    dead.append({"net": n, "anchor": list(g),
                                 "mm": [round(v, 3) for v in m],
                                 "gap_mm": round(best[0], 4),
                                 "blocker": best[1], "edge_tight": edge_tight})
                    ndead.append(list(g))
            per_net[n] = {"endpoints": len(anchors), "dead_anchors": ndead}

        # 保守投影全板拥塞（席位地图同口径：清障+半宽，含板边带与禁布区）
        ko_zones = [(z.get("zone_id", "zone"), z.get("layers") or "all",
                     (float((z.get("rect") or {})["x_min"]),
                      float((z.get("rect") or {})["y_min"]),
                      float((z.get("rect") or {})["x_max"]),
                      float((z.get("rect") or {})["y_max"])))
                    for z in (board.get("zones") or [])
                    if z.get("kind") == "keepout" and
                    set(("x_min", "y_min", "x_max", "y_max")) <=
                    set((z.get("rect") or {}))]
        union = {"pads": [p[3] for p in pads_all], "segs": [], "vias": [],
                 "holes": [tuple(h) for h in holes], "zones": ko_zones}
        total = blocked = 0
        for j in range(lat.j_max + 1):
            for i in range(lat.i_max + 1):
                total += 1
                if _edge_blocked(core, i, j) or _blocked_at(
                        lat.to_mm(i, j), union, "F.Cu", r5):
                    blocked += 1
        boards.append({
            "path": bp.replace("\\", "/"), "board_id": board["board_id"],
            "board_sha256": sha[:16], "grid": [lat.i_max + 1, lat.j_max + 1],
            "pitch_mm": lat.pitch, "r5_mm": r5,
            "workspace_mm": [round(ws["x_max"] - ws["x_min"], 1),
                             round(ws["y_max"] - ws["y_min"], 1)],
            "area_mm2": round(area_mm2, 1), "nets": len(per_net),
            "endpoints_total": anchors_total, "pads": len(pads_all),
            "holes": len(holes),
            "advisory_blocked_frac": round(blocked / float(total), 4),
            "keepout_zones": len(ko_zones),
            "dead_anchors": dead, "per_net": per_net,
        })

    for b in boards:
        if "error" in b:
            print("%-44s ERROR %s" % (os.path.basename(b["path"]),
                                      b["error"][:60]))
            continue
        viable = sum(1 for v in b["per_net"].values() if not v["dead_anchors"])
        print("%-44s nets=%d viable=%d eps=%d pads=%d holes=%d ko=%d "
              "blocked=%.1f%% dead=%d" % (
                  os.path.basename(b["path"]), b["nets"], viable,
                  b["endpoints_total"], b["pads"], b["holes"],
                  b["keepout_zones"], 100.0 * b["advisory_blocked_frac"],
                  len(b["dead_anchors"])))
    if getattr(args, "out", None):
        with open(args.out, "wb") as f:
            f.write(canonical_json({"schema_version": "net-agent-p1/scan-v1",
                                    "generator": GENERATOR, "version": VERSION,
                                    "boards": boards}))
        print("-> %s" % args.out.replace("\\", "/"))


def cmd_ripup(args):
    """ripup = 派生账本分叉（orchestrator 级，不动 canvas-edit-v2 协议面）。

    源台账 append-only 保全；目标 run 从初始态逐轮重放源 batch、过滤目标网
    全部动作后经 _append_round **全量重验** 落新链。安全性：被移除的只是他
    网障碍，V_CLEARANCE 对清障单调、其余 V_* 不依赖他网铜 ⟹ 保留动作重验
    必过；因目标网铜而被拒的动作在分叉世界重判（可能复活）——这正是
    「没有目标网的世界」的语义，非偏差。分叉后 verify 复核链完整性。

    0.5.1（run12 F-3）: 上述单调性论证只对「目标网铜移除」成立; 复活动作
    落铜会改变**后序轮**的重验环境，可能挤掉源世界已受理的动作（run12
    实例=GND/R1 两网丢连通）。故分叉产物对每动作产出源/新判定对照
    （revalidation.revived / .dropped），变静默转移为显式披露。
    """
    board, sha, board_path = load_board(_board_path(args))
    src_dir = _run_dir(args)
    src_ledger = _ledger_path(src_dir)
    if not os.path.isfile(src_ledger):
        raise SystemExit("源台账不存在: %s" % src_ledger)
    new_dir = args.new_run if os.path.isabs(args.new_run) else os.path.join(
        _REPO, OUT_ROOT, args.new_run)
    new_ledger = _ledger_path(new_dir)
    if os.path.isfile(new_ledger):
        raise SystemExit("目标台账已存在（防覆盖混链）: %s" % new_ledger)
    os.makedirs(new_dir, exist_ok=True)
    with open(src_ledger, "rb") as f:
        records = [json.loads(ln.decode("utf-8"))
                   for ln in f if ln.strip()]
    st = make_loop_state(build_state(board, board_path, sha))
    kept_rounds, removed_actions, rmap = 0, 0, {}
    revived, dropped = [], []
    for rec in records:
        if "batch" not in rec:
            raise SystemExit("旧式 edit_list 行不支持 ripup @round %s"
                             % rec.get("round"))
        pairs = [(i, a) for i, a in enumerate(rec["batch"]) if not (
            isinstance(a, dict) and a.get("net_id") == args.net)]
        acts = [a for _, a in pairs]
        removed_actions += len(rec["batch"]) - len(acts)
        if not any(a.get("action") != "submit" for a in acts):
            continue    # 过滤后仅剩 submit/空 = 空轮，跳过不占新轮号
        kept_rounds += 1
        rmap[rec["round"]] = kept_rounds
        text = json.dumps({"round": kept_rounds, "actions": acts},
                          ensure_ascii=False)
        ordered = _append_round(st, new_ledger, text, kept_rounds)
        # 重验对照（F-3 披露）: 同源动作在新旧两世界的判定翻转面。
        src_acc = {e["index"] for e in rec.get("accepted", [])}
        new_acc = {e["index"] for e in ordered.get("accepted", [])}
        new_rej = {e["index"]: e for e in ordered.get("rejected", [])}
        for pos, (src_idx, act) in enumerate(pairs):
            if not isinstance(act, dict):
                continue
            was, now = src_idx in src_acc, pos in new_acc
            if was and not now:
                e = new_rej.get(pos, {})
                dropped.append({
                    "src_round": rec["round"], "src_index": src_idx,
                    "action": act.get("action"), "net_id": act.get("net_id"),
                    "code": e.get("code"),
                    "detail": str(e.get("detail"))[:200]})
            elif now and not was:
                revived.append({
                    "src_round": rec["round"], "src_index": src_idx,
                    "action": act.get("action"), "net_id": act.get("net_id")})
    core = st._st if hasattr(st, "_st") else st
    prov = {
        "schema_version": "net-agent-p1/ripup-v2",
        "generator": GENERATOR, "version": VERSION,
        "src_run": src_dir.replace("\\", "/"), "net": args.net,
        "board_id": board["board_id"], "board_sha256": sha,
        "src_rounds": len(records), "kept_rounds": kept_rounds,
        "round_map": {str(k): v for k, v in sorted(rmap.items())},
        "removed_actions": removed_actions,
        "revalidation": {
            "note": "分叉=全量重验新世界（run12 F-3）: revived=源拒→新收"
                    "（占位撤除路径复活）; dropped=源收→新拒（复活铜改变"
                    "后序轮判定环境，附带损伤面）",
            "revived": revived, "dropped": dropped,
            "n_revived": len(revived), "n_dropped": len(dropped),
        },
        "net_connected_after": bool(core.connectivity.get(args.net)),
        "final_state_sha256": st.sha256(),
    }
    with open(os.path.join(new_dir, "ripup.json"), "wb") as f:
        f.write(canonical_json(prov))
    print(json.dumps({"new_run": new_dir.replace("\\", "/"),
                      "kept_rounds": kept_rounds,
                      "removed_actions": removed_actions,
                      "n_revived": len(revived), "n_dropped": len(dropped),
                      "net_connected_after": prov["net_connected_after"],
                      "final_state_sha256": prov["final_state_sha256"][:16]},
                     ensure_ascii=False))


# ---------------------------------------------------------------- 状态/导出/复核

def _reach_state(board, board_path, run_dir, round_cap):
    """round_cap=None → 全台账态; 否则截断至前 K 轮（截断链 tempfile 重放，
    replay 内建链+轮末态哈希校验照常——截断不破坏链完整性; v1 台账截断
    前缀同样走迁移重放，与全台账共用 _replay_ledger——0.6.0 D-6）。"""
    ledger = _ledger_path(run_dir)
    if round_cap is None or not os.path.isfile(ledger):
        return current_state(board, board_path, run_dir)
    with open(ledger, "rb") as f:
        lines = [ln for ln in f if ln.strip()]
    if not (1 <= round_cap <= len(lines)):
        raise SystemExit("--round 超界: 台账 %d 轮, 请求 %d"
                         % (len(lines), round_cap))
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".jsonl", prefix="reach-")
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.writelines(lines[:round_cap])
        return _replay_ledger(tmp, board, board_path)
    finally:
        os.remove(tmp)


def cmd_reach(args):
    """可达性/封锁扫描（0.4.0）: 台账态下网 N 在 route/via 动作空间的 BFS 精确刻画。

    run8/P8 货币化的 pre-dispatch 封锁扫描工具化（省额 86.5% 席位开销实测）。
    判据逐位镜像 canvas.validate 逐编辑检查（run8 fence-probes/seal-proof.py
    同源移植）: R5/同层 = _scene 全铜场景 + drc._actual_gap < R5−EPS（中心线
    口径）; 板边 = check_edge_clearance（判定点=折线顶点/焊盘圆心）; 板固孔 =
    hole_track_blocked（本网端点孔豁免）/ hole_via_blocked（**零豁免**）;
    via = 全层 pad 铜; 锚 stub（真实端点→锚格）按层复核——stub 被禁的层上
    无法起/落。keepout 区按**单位段 bbox** 判（check_keepout 实为整条
    polyline bbox）→ zone 板上本扫描是**过估**（可达 ⇏ 单条 route 可表达，
    须拆段+via）; **不可达 ⟹ 结构性不可布**——封锁方向判定可靠。
    多端网: 同网铜互不阻碍（same_net_exempt），锚 0 到其余各锚全可达 ⟺
    可布。已连通网直接报告。BFS 可达路径 ⟺ 席位 route/via 合法序列
    （0.5 栅格单位步 = L 展开路径; via 换层 = 全层盘检查）。
    """
    from collections import deque
    from canvas import validate as V
    from v5 import drc
    from v5.metrics import clearance as _clr
    from v5.kicad_export import via_model_params

    board, sha, board_path = load_board(_board_path(args))
    st = _reach_state(board, board_path, _run_dir(args), args.round)
    core = st._st if hasattr(st, "_st") else st
    net_id = args.net
    if net_id not in core.known_nets():
        raise SystemExit("未知网 %r（板内网见 board.json）" % net_id)
    out = {"schema_version": "net-agent-p1/reach-v1", "generator": GENERATOR,
           "version": VERSION, "geometry_semantics": GEOMETRY_SEMANTICS_VERSION,
           "board_sha256": sha, "net_id": net_id,
           "round_cap": args.round, "state_sha256": st.sha256()}
    if core.connectivity.get(net_id):
        out.update({"connected": True, "reachable": True,
                    "note": "已连通——无需扫描"})
        print(json.dumps(out, ensure_ascii=False))
        if getattr(args, "out", None):
            with open(args.out, "wb") as f:
                f.write(canonical_json(out))
        return
    lat = core.lattice
    r5 = float(board["hard_rules"]["R5"]["min_clearance_mm"])
    ws = V.ws_tuple(board)
    layers = list(core.signal_layers())
    foreign = [c for c in V._scene(core) if c.net_id != net_id]
    holes = list(drc.normalize_holes(board.get("holes")))
    exempt = V._hole_exempt(core, net_id)
    half = V.net_width(core, net_id,
                       V._effective_width_class(core, net_id)) / 2.0
    via_r = via_model_params(board)["radius"]
    zr = []
    for z in (board.get("zones") or []):
        if z.get("kind") != "keepout":
            continue
        r = z.get("rect") or {}
        zr.append((z.get("layers") or "all",
                   (float(r["x_min"]), float(r["y_min"]),
                    float(r["x_max"]), float(r["y_max"]))))

    def _zone_blocked(bbox, layer):
        bx0, by0, bx1, by1 = bbox
        for zlays, (x0, y0, x1, y1) in zr:
            if zlays not in ("all", "signal") and layer not in zlays:
                continue
            dx = max(x0 - bx1, bx0 - x1)
            dy = max(y0 - by1, by0 - y1)
            if dx <= 0.0 and dy <= 0.0:
                return True
        return False

    def seg_ok(p, q, layer):
        cand = drc.Copper(net_id, "reach:seg", layer,
                          polyline=[list(p), list(q)], half_width=half)
        if drc.check_edge_clearance([cand], ws):
            return False
        for fc in foreign:
            if fc.layer == layer and \
                    drc._actual_gap(cand, fc) < r5 - _clr.EPS:
                return False
        for hi, (hx, hy, hr) in enumerate(holes):
            if hi in exempt:
                continue
            if drc.hole_track_blocked((hx, hy), hr, p, q, half):
                return False
        xs, ys = (p[0], q[0]), (p[1], q[1])
        return not _zone_blocked((min(xs), min(ys), max(xs), max(ys)), layer)

    def via_ok(p):
        b = (p[0] - via_r, p[1] - via_r, p[0] + via_r, p[1] + via_r)
        for layer in layers:
            cand = drc.Copper(net_id, "reach:via", layer,
                              pad=((p[0], p[1]), via_r))
            if drc.check_edge_clearance([cand], ws):
                return False
            for fc in foreign:
                if fc.layer == layer and \
                        drc._actual_gap(cand, fc) < r5 - _clr.EPS:
                    return False
            if _zone_blocked(b, layer):
                return False
        for _hi, (hx, hy, hr) in enumerate(holes):
            if drc.hole_via_blocked((hx, hy), hr, p, via_r):
                return False
        return True

    pids = core.net_partitions(net_id)
    anchors = [tuple(a) for pid in pids
               for a in core.effective_anchors(pid)]
    eps = [tuple(e) for pid in pids for e in core.effective_endpoint_mm(pid)]
    out["terminals"] = len(anchors)

    stub_ok = [{} for _ in anchors]
    starts, stub_blocked = set(), []
    for k, (g, m) in enumerate(zip(anchors, eps)):
        gm = lat.to_mm(*g)
        for L in layers:
            stub_ok[k][L] = seg_ok(m, gm, L)
        if not any(stub_ok[k].values()):
            stub_blocked.append(list(g))
    if not stub_blocked:
        for L in layers:
            if stub_ok[0][L]:
                starts.add((anchors[0][0], anchors[0][1], L))
    if stub_blocked or not starts:
        out.update({"reachable": False, "reason": "stub-blocked",
                    "stub_blocked_anchors": stub_blocked})
        print(json.dumps(out, ensure_ascii=False))
        if getattr(args, "out", None):
            with open(args.out, "wb") as f:
                f.write(canonical_json(out))
        return

    dist = {s: 0 for s in starts}
    dq = deque(starts)
    while dq:
        n = dq.popleft()
        i, j, L = n
        p = lat.to_mm(i, j)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            i2, j2 = i + di, j + dj
            if not lat.in_bounds(i2, j2):
                continue
            n2 = (i2, j2, L)
            if n2 in dist:
                continue
            q = lat.to_mm(i2, j2)
            if seg_ok(p, q, L):
                dist[n2] = dist[n] + 1
                dq.append(n2)
        for L2 in layers:
            if L2 != L and (i, j, L2) not in dist and via_ok(p):
                dist[(i, j, L2)] = dist[n] + 1
                dq.append((i, j, L2))

    per, ok_all, best = [], True, None
    for k in range(1, len(anchors)):
        cand_cells = [(anchors[k][0], anchors[k][1], L)
                      for L in layers if stub_ok[k].get(L)]
        ds = [dist[c] for c in cand_cells if c in dist]
        hit = bool(ds)
        per.append({"anchor": list(anchors[k]), "reached": hit,
                    "steps": min(ds) if ds else None})
        ok_all = ok_all and hit
        if ds and (best is None or min(ds) < best):
            best = min(ds)
    out.update({"reachable": ok_all, "shortest_grid_steps": best,
                "per_terminal": per, "scanned_nodes": len(dist)})
    print(json.dumps(out, ensure_ascii=False))
    if getattr(args, "out", None):
        with open(args.out, "wb") as f:
            f.write(canonical_json(out))


# ---------------------------------------------------------------- 复盘（经验回流环）

DEBRIEF_TEMPLATE = """# 布线复盘任务 · {tag}（round {round}）

你是刚完成 round {round}（网 {net}）的 PCB 布线席位。现在回顾你当时的工作，
写一份**结构化复盘经验**——它将被汇总、经机械验证筛选后迭代进后续席位的
任务书。只写你亲历的、能被下面三份材料支撑的判断; 猜测性的泛泛之谈会被
筛选器丢弃，宁缺毋滥。

下面三份材料逐字给出。

## 材料一: 你当时的任务书（含地图与协议）
{brief}

## 材料二: 你当时的提案（逐字）
{proposal}

## 材料三: 机械验证器裁决（逐字）
{result}

## 输出
把一个 JSON 对象写到文件（UTF-8、纯 JSON、无代码围栏无注释）:
{out_path}

schema（键固定，值不确定处写 null; 数组可空）:
{{
  "round": {round},
  "net": "{net}",
  "outcome": "connected-first-shot | rejected-then-connected | rejected-exhausted",
  "failed_attempts": [
    {{"geometry_intent": "这次尝试想走什么几何（一句话）",
      "rejection": "对应的拒收码+detail（逐字）",
      "lesson": "你从中得到的、可复用的具体教训（一句话）"}}
  ],
  "successful_strategy": {{
    "description": "最终成功（或最接近成功）策略的几何描述",
    "key_moves": ["关键决策点，每条一句话（如换层/绕行/分段+via）"]
  }},
  "map_reading_notes": ["地图符号/坐标与实际裁决不一致或特别有用的地方"],
  "protocol_gaps": ["任务书没教、但你需要知道的事（若任务书已教则不写）"],
  "confidence": "high | medium | low"
}}

- 只写这一个文件。写完即止。最终回复只写一行 DONE。
"""


def cmd_debrief(args):
    """复盘包组装（0.5.0 经验回流环·发起点）: round 目录三材料（任务书/
    提案/裁决）逐字嵌入 DEBRIEF_TEMPLATE → rounds/<tag>/debrief-packet.md。
    复盘席位（harness 子智能体或外派）读包写 debrief.json; 主审汇总、
    机械验证筛选（PLAYBOOK）后迭代进简报/协议——经验不直接当散文喂
    （run8 实证: 席位对 # 的服从率在目标压力下衰减），必须过机械滤网。"""
    run_dir = _run_dir(args)
    rd = args.round_dir
    if not os.path.isabs(rd):
        rd = os.path.join(run_dir, rd)
    mats = []
    for name in ("brief.md", "proposal.json", "result.json"):
        p = os.path.join(rd, name)
        if not os.path.isfile(p):
            raise SystemExit("复盘材料缺失: %s" % p)
        with open(p, "r", encoding="utf-8") as f:
            mats.append(f.read().rstrip("\n"))
    tag = os.path.basename(os.path.normpath(rd))
    with open(os.path.join(rd, "result.json"), "r", encoding="utf-8") as f:
        res = json.load(f)
    net = ""
    if res.get("connectivity"):
        net = sorted(res["connectivity"])[0]
    packet = DEBRIEF_TEMPLATE.format(
        tag=tag, round=res.get("round"), net=net,
        brief=mats[0], proposal=mats[1], result=mats[2],
        out_path=os.path.join(rd, "debrief.json").replace("\\", "/"))
    out = os.path.join(rd, "debrief-packet.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(packet)
    print(json.dumps({"tag": tag, "packet": out.replace("\\", "/"),
                      "expect_debrief": os.path.join(
                          rd, "debrief.json").replace("\\", "/")},
                     ensure_ascii=False))


def cmd_status(args):
    board, sha, board_path = load_board(_board_path(args))
    st = current_state(board, board_path, _run_dir(args))
    out = {"state_sha256": st.sha256(),
           "routed": {n: bool(st.connectivity[n])
                      for n in sorted(st.connectivity)
                      if st.connectivity[n] or args.all},
           "segs": len(st.segs), "vias": len(st.vias)}
    print(json.dumps(out, ensure_ascii=False))


def _checked_pairs_count(cp):
    """checked_pairs 双型（0.6.0 D-3; b① run10 缺陷实录）: int 直用、
    序列取 len——v5.drc.check_all 传 int 计数、历史/旁路报告可能是对序列，
    两型都数得出数值，drc-report.json 落数值并附 checked_pairs_type 披露。"""
    if isinstance(cp, bool):
        raise TypeError("checked_pairs 布尔型无意义: %r" % (cp,))
    if isinstance(cp, int):
        return cp, "int"
    if isinstance(cp, (list, tuple, set, frozenset)):
        return len(cp), "sequence"
    raise TypeError("checked_pairs 未知型 %s" % type(cp).__name__)


def cmd_export(args):
    board, sha, board_path = load_board(_board_path(args))
    st = current_state(board, board_path, _run_dir(args))
    from canvas.validate import validate_full
    from canvas.export import export_kicad
    core = st._st if hasattr(st, "_st") else st
    report = validate_full(core)
    # 0.6.0 D-9: --out-dir 验证面（缺省 run/final 不变; 相对路径=repo 根起，
    # 与 --run/--board 同口径）。历史 run 目录零写纪律由此落（D-8）。
    out_dir = (os.path.normpath(os.path.join(_REPO, args.out_dir))
               if getattr(args, "out_dir", None)
               and not os.path.isabs(args.out_dir)
               else (getattr(args, "out_dir", None)
                     or os.path.join(_run_dir(args), "final")))
    exported = export_kicad(core, out_dir)
    n_pairs, cp_type = _checked_pairs_count(report.checked_pairs)
    rep = {"drc_violations": [v.as_dict() for v in report.violations],
           "checked_pairs": n_pairs,
           "checked_pairs_type": cp_type}
    with open(os.path.join(out_dir, "drc-report.json"), "wb") as f:
        f.write(canonical_json(rep))
    print(json.dumps({"exported": exported, "violations": len(
        rep["drc_violations"]), "checked_pairs": n_pairs,
        "checked_pairs_type": cp_type}, ensure_ascii=False))


def cmd_verify(args):
    """确定性复核: 台账 replay 终态哈希 == 链尾记录（链完整性由 replay 内建）。

    0.6.0 D-6 迁移感知: v1 语义台账（current_state 走迁移重放并挂
    pilot_migration_disclosure）→ 字节链+轮号已由迁移重放 fail-closed 核验、
    逐轮态哈希差异全行披露 = exit 0（输出 ``migration`` 块）; 链断/轮号不连续
    照旧 ValueError fail-closed（exit 1 路径不变）。"""
    board, sha, board_path = load_board(_board_path(args))
    run_dir = _run_dir(args)
    st = current_state(board, board_path, run_dir)
    disc = getattr(st, "pilot_migration_disclosure", None)
    with open(_ledger_path(run_dir), "rb") as f:
        lines = [ln for ln in f if ln.strip()]
    if disc is not None:
        ok_struct = (isinstance(disc.get("rows"), int)
                     and isinstance(disc.get("batch_rows"), int)
                     and isinstance(disc.get("diverged_rows"), list)
                     and isinstance(disc.get("final_state_sha256"), str)
                     and disc["rows"] == len(lines)
                     and set(disc["diverged_rows"])
                     <= set(range(1, len(lines) + 1)))
        if not ok_struct:
            raise SystemExit("迁移披露结构不完整: %r" % (disc,))
        print(json.dumps({"migration": disc, "rounds": len(lines)},
                         ensure_ascii=False))
        return
    tail = json.loads(lines[-1].decode("utf-8"))
    ok = st.sha256() == tail["state_sha256"]
    print(json.dumps({"ledger_tail_state_match": ok, "rounds": len(lines)},
                     ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--board", default=BOARD_DEFAULT)
    common.add_argument("--run", default="run1")
    ap = argparse.ArgumentParser(prog="net_agent_pilot.pilot",
                                 parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("slice", "ingest", "status", "export", "verify",
                 "scan", "ripup", "reach", "debrief"):
        sp = sub.add_parser(name, parents=[common])
        if name == "slice":
            sp.add_argument("--net", required=True)
            sp.add_argument("--tag")
            sp.add_argument("--prior-rejection",
                            help="上轮 result.json 路径（回叫简报嵌入拒收记录）")
            sp.add_argument("--playbook",
                            help="PLAYBOOK 条目文件（嵌入'前席经验'节）")
            sp.add_argument("--round", type=int,
                            help="显式轮号（并行切片预留轮号用；"
                                 "台账轮连续性由摄入顺序保证）")
            sp.add_argument("--roi", choices=("full", "legacy"), default="full",
                            help="ROI 口径（0.6.0 D-1: 缺省 full=板全域; "
                                 "legacy=旧 margin=12 端点周边口径，仅供 "
                                 "A/B 复现; facts.json 记 roi 模式）")
        elif name == "ingest":
            sp.add_argument("--round-dir", required=True)
        elif name == "status":
            sp.add_argument("--all", action="store_true")
        elif name == "scan":
            sp.add_argument("--out", help="结果 JSON 落盘路径（缺省仅 stdout）")
        elif name == "export":
            sp.add_argument("--out-dir", dest="out_dir",
                            help="导出目录（0.6.0 D-9 验证面; 缺省 run/final "
                                 "不变; 相对路径=repo 根起; 受 v5.sidecar "
                                 "合同约束只准 out/ 之下）")
        elif name == "ripup":
            sp.add_argument("--net", required=True)
            sp.add_argument("--new-run", required=True, dest="new_run",
                            help="目标 run 名（须不存在台账；分叉产物根）")
        elif name == "reach":
            sp.add_argument("--net", required=True)
            sp.add_argument("--round", type=int,
                            help="截断至台账前 K 轮的态（封锁扫描历史态用）")
            sp.add_argument("--out", help="证书 JSON 落盘路径（缺省仅 stdout）")
        elif name == "debrief":
            sp.add_argument("--round-dir", required=True)
    args = ap.parse_args()
    {"slice": cmd_slice, "ingest": cmd_ingest, "status": cmd_status,
     "export": cmd_export, "verify": cmd_verify, "scan": cmd_scan,
     "ripup": cmd_ripup, "reach": cmd_reach,
     "debrief": cmd_debrief}[args.cmd](args)


if __name__ == "__main__":
    main()
