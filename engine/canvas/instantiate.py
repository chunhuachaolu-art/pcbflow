# -*- coding: utf-8 -*-
"""canvas.instantiate -- 格点态 → mm 几何实例化（合同 §1 Lane-K1）。

路由无搜索: manhattan(from_grid, to_grid) 是唯一布线形态生成器（L 形直连、
拐点在格点上、先 x 后 y 确定性序）；无 A*、无绕障、无推挤——搜索负担归
席位/runner（被测假设本体）。放置合法化不在此（M4 placecheck）。

- seg → mm 折线（贴制造格点: 格点 mm = origin + i·pitch，9 位小数量化防
  尾差）；段首/末格点==覆盖后端点锚时端点绑定（V6-ANCHOR-R1 口径 v2/
  anchor semantics v2）: 物理铜以**真实端点 mm** 为起/终点、真实端点→
  次格点 L 形（先 x 后 y，与格点展开同构），锚格点降格附着标记
  （occupancy/connectivity 判据照用）不进物理铜折线——链首末点=分区
  真实端点（kicad 导出端点对齐、route_check 链审计同语义）。
- via → 孔 mm（铜盘半径 = v5.kicad_export.via_model_params 单源）。
- placement 覆盖 → 分区 pad 场 mm（端点 pad 按覆盖后真实端点位置实例化；
  无覆盖=原位）。
- tuning → 参数化几何（accordion/detour，公式见 tuning_polyline_mm
  docstring——原型披露，不冒称全阻抗 authority）。

routes 形态 = v5.kicad_export._validate 可消费的导出行（已照源码探明）:
每行 {partition_id, net_id, layer, polyline>=2 点 mm, width>0}；
routes_document() 包装为 v5.routes.v1 文档（schema_version/board_id/
board_sha256/routes）。tuning 几何只入 coppers（DRC 面），不入 routes 行
——参数化铜的导出接线随 M5 tuning runner 落（本车道设计披露，见 REPORT）。

导出行过孔（EXPORT-SEMANTICS-R1，D-CT-033 修复；合同 K1「via→孔 mm」的
routes 侧落地）：行可选 transition_vias=[[x,y],...]（v5 导出器逐点写全叠层
(via) 带 net、同网同坐标去重）——①画板 via（格点）→ mm 点集按网归入该网
首行；②锚端到达层 ∉ 该端点 pad 铜层集（如 B.Cu 段接单层 SMD 锚）→ 在
真实端点 mm 派生端点过孔（跨层连通由端点过孔承担——v5 世界模型既定规
则，同网孔穿自网焊盘）。层信息不可确证不派生。半布线孤立 via 导出后
kicad 侧可呈 via_dangling（画板态如实呈现，非导出缺陷）。
"""
from v5 import drc
from v5.kicad_export import via_model_params


def manhattan(from_grid, to_grid):
    """两格点 → L 形直连格点折线（先 x 后 y；拐点在格点上；无搜索）。

    返回 [from, 拐点?, to]（对齐/重合时退化为 2/1 点，无重复点）。"""
    a = (int(from_grid[0]), int(from_grid[1]))
    b = (int(to_grid[0]), int(to_grid[1]))
    if a == b:
        return [a]
    if a[0] == b[0] or a[1] == b[1]:
        return [a, b]
    return [a, (b[0], a[1]), b]


def expand_waypoints(grid_pts):
    """[[i,j],...] 跳跃点 → 相邻 L 形直连的**单位步**全格点序列（先 x 后
    y，去连续重复点）。逐格点入段是画板纪律消费面: via on-path 判定逐
    waypoint 比对、段 mm 折线逐格点贴合制造格点（v1 同源语义）。"""
    pts = [tuple(p) for p in grid_pts]
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        ci, cj = a
        while ci != b[0]:
            ci += 1 if b[0] > ci else -1
            out.append((ci, cj))
        while cj != b[1]:
            cj += 1 if b[1] > cj else -1
            out.append((ci, cj))
    dedup = [out[0]]
    for p in out[1:]:
        if p != dedup[-1]:
            dedup.append(p)
    return dedup


def _mm_l_shape(p_from, p_to):
    """mm 平面 L 形（先 x 后 y，与格点展开同构）——stub 专用。

    恒返回以 p_to 结尾的中间折点列表（直线退化时=[终点]）。"""
    (x0, y0), (x1, y1) = p_from, p_to
    if abs(x1 - x0) < 1e-12 and abs(y1 - y0) < 1e-12:
        return []
    if abs(x1 - x0) < 1e-12 or abs(y1 - y0) < 1e-12:
        return [(x1, y1)]
    return [(x1, y0), (x1, y1)]


def grid_path_mm(st, pts):
    """格点序列 → mm 序列（制造格点贴合: origin + i·pitch, 9 位量化）。"""
    return [st.lattice.to_mm(p[0], p[1]) for p in pts]


def segment_mm(st, seg):
    """段 → (mm 折线含首末绑定腿, stub_range)。

    V6-ANCHOR-R1 口径 v2（anchor semantics v2, 真端点绑定）: 段首/末格点
    ==覆盖后端点锚时，物理铜以真实端点 mm 为起/终点（真实端点→次
    waypoint 的 L 形，_mm_l_shape 先 x 后 y 同式）；锚格点不进物理铜折线。
    body waypoints 仍=格点 mm。端点取 effective_endpoint_mm（placement
    覆盖后；无覆盖=原位）。stub_range=head/tail 绑定腿段内索引范围（含
    真实端点与首/末 body 点；信息面——孔豁免/导出披露消费位，当前无
    外部消费者）。"""
    lat = st.lattice
    pid = seg["partition_id"]
    eps = st.effective_endpoint_mm(pid)
    anchors = [tuple(a) for a in st.effective_anchors(pid)]
    grid = [tuple(g) for g in seg["grid"]]
    h_bind = grid[0] in anchors
    t_bind = len(grid) >= 2 and grid[-1] in anchors
    body = grid[(1 if h_bind else 0):(len(grid) - 1 if t_bind else len(grid))]
    pts = []
    head = None
    tail = None
    if h_bind:
        real = eps[anchors.index(grid[0])]
        if body:
            target = lat.to_mm(*body[0])
            leg = _mm_l_shape(real, target)
            pts.append(real)
            pts.extend(leg)              # 真实端点→L→次格点(锚格不进铜)
            head = (0, len(pts) - 1) if leg else None
        elif t_bind:
            real2 = eps[anchors.index(grid[-1])]
            leg = _mm_l_shape(real, real2)
            pts.append(real)
            pts.extend(leg)              # 双端绑定无 body: 端点直连
            head = (0, len(pts) - 1) if leg else None
            tail = head
        else:
            leg = _mm_l_shape(real, lat.to_mm(*grid[0]))   # 单点退化: 附着腿
            pts.append(real)
            pts.extend(leg)
            head = (0, len(pts) - 1) if leg else None
    else:
        pts.append(lat.to_mm(*grid[0]))
    for g in (body[1:] if (h_bind and body) else body):
        pts.append(lat.to_mm(*g))
    if t_bind and body:
        real2 = eps[anchors.index(grid[-1])]
        leg = _mm_l_shape(lat.to_mm(*body[-1]), real2)
        n0 = len(pts) - 1                # 腿起点=末 body 点(已入列)
        pts.extend(leg)
        tail = (n0, len(pts) - 1) if leg else None
    return pts, {"head": head, "tail": tail}


def net_width_mm(st, net_id, width_class):
    """网宽 mm（width_class 词表 → mm；词表单源=canvas.validate.
    width_class_vocab，局部导入解 circular）。"""
    from . import validate
    vocab = validate.width_class_vocab(st.board)
    if width_class not in vocab:
        raise ValueError("未知 width_class %r（net=%s）" % (width_class, net_id))
    return float(vocab[width_class])


def seg_copper(st, seg):
    """段 → v5.drc.Copper（half_width=网宽/2；polyline 含 stub）。"""
    pts, _stub = segment_mm(st, seg)
    w = net_width_mm(st, seg["net_id"], seg["width_class"])
    cu = drc.Copper(seg["net_id"], seg["shape_id"], seg["layer"],
                    polyline=[(float(p[0]), float(p[1])) for p in pts],
                    half_width=w / 2.0)
    cu.partition_id = seg["partition_id"]
    return cu


def via_coppers(st, vias=None):
    """via → 每信号层一枚 pad 铜（半径 via_model_params 单源）。"""
    layers = st.signal_layers()
    r = via_model_params(st.board)["radius"]
    out = []
    if vias is None:
        src = [st.vias[sid] for sid in sorted(st.vias)]
    else:
        src = list(vias)
    for v in src:
        mm = st.lattice.to_mm(*v["grid"])
        for layer in layers:
            cu = drc.Copper(v["net_id"], v["shape_id"], layer, pad=(mm, r))
            cu.is_via = True
            out.append(cu)
    return out


def pad_coppers(st):
    """分区端点 pad 场（circle→pad 圆 / rect→band；layers="all"→每信号层
    一枚，列表→交集信号层；端点位置=placement 覆盖后真实端点 mm）。"""
    layers_all = st.signal_layers()
    out = []
    for pid in sorted(st.known_partitions()):
        part = st.board_partition(pid)
        net_id = st.partition_net(pid)
        if net_id is None:
            continue
        items = (part.get("geometry") or {}).get("pad_terminals") or []
        if not items:
            continue
        eps = st.effective_endpoint_mm(pid)
        for item in sorted(items, key=lambda q: q["endpoint"]):
            center = eps[item["endpoint"]]
            if item.get("layers") == "all":
                layers = layers_all
            elif isinstance(item.get("layers"), list):
                layers = [l for l in item["layers"] if l in layers_all]
            else:
                layers = layers_all
            for layer in layers:
                cid = "pad:%s:%d" % (pid, item["endpoint"])
                if item["shape"] == "circle":
                    cu = drc.Copper(net_id, cid, layer,
                                    pad=(center, float(item["size_mm"][0]) / 2.0))
                else:
                    hw = float(item["size_mm"][0]) / 2.0
                    hh = float(item["size_mm"][1]) / 2.0
                    cu = drc.Copper(net_id, cid, layer,
                                    band=(center[0] - hw, center[1] - hh,
                                          center[0] + hw, center[1] + hh))
                cu.partition_id = pid
                cu.is_pad_terminal = True
                out.append(cu)
    return out


def tuning_polyline_mm(st, tun):
    """tuning → 参数化 mm 折线（原型公式，来源披露、不冒称阻抗 authority）。

    - accordion {"amp_mm": a>0, "count": n>=1}: 基线（grid 展开 mm 折线）上
      均匀布 n 个矩形折返——第 k 个落于弧长 L·k/(n+1) 处，沿行进方向 d 前进
      一个 pitch 落回基线，垂直向 u 幅度 a（u = d 逆时针旋 90°）:
      [P, P+u·a, P+u·a+d·pitch, P+d·pitch]。
    - detour {"offset_mm": o≠0}: 最长轴对齐腿（并列取首个）侧移 |o|——
      [A, A+u·o, B+u·o, B]（u 同上，o 的符号决定侧移方向）。
    确定性: 基线/选腿/插点全为确定式，无随机无搜索。"""
    lat = st.lattice
    base = grid_path_mm(st, expand_waypoints(tun["grid"]))
    if len(base) < 2:
        return [(float(p[0]), float(p[1])) for p in base]
    kind = tun["kind"]
    params = tun["params"]
    if kind == "accordion":
        amp = float(params["amp_mm"])
        count = int(params["count"])
        segs = list(zip(base[:-1], base[1:]))
        lengths = [_hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
        total = sum(lengths)
        out = [base[0]]
        cursor = 0.0
        for (a, b), L in zip(segs, lengths):
            d = _unit(b[0] - a[0], b[1] - a[1])
            u = (-d[1], d[0])
            lo, hi = cursor, cursor + L
            for k in range(1, count + 1):
                s = total * k / (count + 1)
                if lo <= s < hi or (k == count and s >= total):
                    P = (a[0] + d[0] * (s - lo), a[1] + d[1] * (s - lo))
                    out.extend([
                        P,
                        (P[0] + u[0] * amp, P[1] + u[1] * amp),
                        (P[0] + u[0] * amp + d[0] * lat.pitch,
                         P[1] + u[1] * amp + d[1] * lat.pitch),
                        (P[0] + d[0] * lat.pitch, P[1] + d[1] * lat.pitch),
                    ])
            out.append(b)
            cursor = hi
        dedup = [out[0]]
        for p in out[1:]:
            if p != dedup[-1]:
                dedup.append(p)
        return [(float(p[0]), float(p[1])) for p in dedup]
    if kind == "detour":
        offset = float(params["offset_mm"])
        segs = list(zip(base[:-1], base[1:]))
        idx = max(range(len(segs)),
                  key=lambda q: (_hypot(segs[q][1][0] - segs[q][0][0],
                                        segs[q][1][1] - segs[q][0][1]), -q))
        a, b = segs[idx]
        d = _unit(b[0] - a[0], b[1] - a[1])
        u = (-d[1], d[0])
        out = []
        for n, (pa, pb) in enumerate(segs):
            if n == idx:
                out.extend([
                    pa,
                    (a[0] + u[0] * offset, a[1] + u[1] * offset),
                    (b[0] + u[0] * offset, b[1] + u[1] * offset),
                    pb,
                ])
            else:
                out.extend([pa, pb])
        dedup = [out[0]]
        for p in out[1:]:
            if p != dedup[-1]:
                dedup.append(p)
        return [(float(p[0]), float(p[1])) for p in dedup]
    raise ValueError("未知 tuning kind %r" % (kind,))


def _unit(dx, dy):
    L = _hypot(dx, dy)
    if L <= 0.0:
        return (0.0, 1.0)
    return (dx / L, dy / L)


def _hypot(x, y):
    import math
    return math.hypot(x, y)


def tuning_copper(st, tun):
    """tuning → v5.drc.Copper。层=本网首段（shape_id 序）的层——tuning 图元
    本身无层键（合同 §1），随基线段走；网无段则不入场（悬空调参段）。"""
    net_segs = [st.segs[sid] for sid in sorted(st.segs)
                if st.segs[sid]["net_id"] == tun["net_id"]]
    if not net_segs:
        return None
    cls = st.widths.get(tun["net_id"], net_segs[0]["width_class"])
    w = net_width_mm(st, tun["net_id"], cls)
    cu = drc.Copper(tun["net_id"], tun["shape_id"], net_segs[0]["layer"],
                    polyline=tuning_polyline_mm(st, tun),
                    half_width=w / 2.0)
    cu.is_tuning = True
    return cu


def _endpoint_pad_layers(st, pid, endpoint):
    """端点 pad 铜层集（导出面判定用，与 v5 导出器锚画法同口径）。

    pad_terminals[endpoint].layers=="all"（通孔标记）→全部信号层；显式
    列表→与信号层交集；无 pad_terminals / 条目缺失 / 交集空 → None
    （层信息不可确证，调用方不派生端点过孔——数据面问题由 v5 导出器
    fail-closed 把关，本件不发明层）。"""
    sig = st.signal_layers()
    part = st.board_partition(pid)
    items = (part.get("geometry") or {}).get("pad_terminals") if part else None
    if not items:
        return None
    for item in items:
        if item.get("endpoint") == endpoint:
            layers = item.get("layers")
            if layers == "all":
                return set(sig)
            if isinstance(layers, list):
                inter = {l for l in layers if l in sig}
                return inter or None
            return None
    return None


def _anchor_via_points(st, seg, pts):
    """锚端到达层 ∉ 该端点 pad 铜层集 → 在真实端点 mm 派生端点过孔点。

    跨层连通由端点过孔承担（v5 世界模型既定规则——SMD 锚按 D6-1 单层
    铜画，多层铜 SMD 被 kicad-cli 判 padstack 违例）；点=stub 终点=真实
    端点（同网孔穿自网焊盘）。非锚端（悬空/中间点）不生成；层信息不可
    确证（None）不生成。"""
    pid = seg["partition_id"]
    eps = [tuple(e) for e in st.effective_endpoint_mm(pid)]
    out = []
    for pt in (tuple(pts[0]), tuple(pts[-1])):
        for k, ep in enumerate(eps):
            pad_layers = _endpoint_pad_layers(st, pid, k)
            if (abs(pt[0] - ep[0]) < 1e-9 and abs(pt[1] - ep[1]) < 1e-9
                    and pad_layers is not None
                    and seg["layer"] not in pad_layers):
                out.append([float(pt[0]), float(pt[1])])
    return out


def instantiate(st):
    """格点态 → {coppers, routes, holes_norm, anchors_mm}（确定性序）。"""
    coppers = pad_coppers(st)
    seg_list = [st.segs[sid] for sid in sorted(st.segs)]
    for seg in seg_list:
        coppers.append(seg_copper(st, seg))
    coppers.extend(via_coppers(st))
    for sid in sorted(st.tunings):
        cu = tuning_copper(st, st.tunings[sid])
        if cu is not None:
            coppers.append(cu)
    # canvas via（格点）→ mm 点集，按网归集（导出面；DRC 面已由
    # via_coppers 覆盖）。合同 K1「via→孔 mm」的 routes 侧落地。
    net_via_mm = {}
    for sid in sorted(st.vias):
        v = st.vias[sid]
        mm = st.lattice.to_mm(*v["grid"])
        net_via_mm.setdefault(v["net_id"], []).append(
            [float(mm[0]), float(mm[1])])
    routes = []
    routed_nets = set()
    for seg in seg_list:
        pts, _stub = segment_mm(st, seg)
        row = {
            "partition_id": seg["partition_id"],
            "net_id": seg["net_id"],
            "layer": seg["layer"],
            "polyline": [[float(p[0]), float(p[1])] for p in pts],
            "width": net_width_mm(st, seg["net_id"], seg["width_class"]),
        }
        extra = _anchor_via_points(st, seg, pts)
        if seg["net_id"] not in routed_nets:
            routed_nets.add(seg["net_id"])
            extra = net_via_mm.get(seg["net_id"], []) + extra
        if extra:
            row["transition_vias"] = extra
        routes.append(row)
    holes_norm = drc.normalize_holes(st.board.get("holes"))
    anchors_mm = {}
    for pid in sorted(st.known_partitions()):
        anchors_mm[pid] = [
            list(st.lattice.to_mm(a[0], a[1]))
            for a in st.effective_anchors(pid)]
    return {"coppers": coppers, "routes": routes,
            "holes_norm": holes_norm, "anchors_mm": anchors_mm}


def routes_document(st, inst=None):
    """routes 行 → v5.routes.v1 完整文档（kicad_pcb_bytes 可直食；
    K2 export.py 的包装缝，本车道提供的便利件）。"""
    if inst is None:
        inst = instantiate(st)
    return {
        "schema_version": "v5.routes.v1",
        "board_id": st.board["board_id"],
        "board_sha256": st.board_sha256,
        "routes": inst["routes"],
    }
