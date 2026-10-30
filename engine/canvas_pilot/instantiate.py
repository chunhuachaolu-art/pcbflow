# -*- coding: utf-8 -*-
"""instantiate —— 实例化器: 格点意图 → 曼哈顿铜几何（无路径搜索）。

- expand_waypoints: 相邻 waypoint 曼哈顿 L 形直连（先 x 后 y, 确定性）; 折
  点落格点。无 A*、无绕行、无推挤——搜索负担归模型（被测假设本身）。
- segment_mm: 段格点 → mm 折线; 段首/末格点==端点 k 锚时自动生成 stub
  （锚格点 ↔ 真实端点 k 的 L 形, 画板垄断几何, 模型不控制）, 使链首末点
  =分区真实端点（引擎 v5.route_check 链审计同语义, kicad 导出端点对齐）。
"""


def expand_waypoints(grid_pts):
    """[[i,j],...]（跳跃点）→ 相邻 L 形展开的格点序列（去连续重复点）。"""
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
    """mm 平面 L 形（先 x 后 y; 与格点展开同构）——stub 专用。

    恒返回以 p_to 结尾的中间折点列表（直线退化时=[终点]）。"""
    (x0, y0), (x1, y1) = p_from, p_to
    if abs(x1 - x0) < 1e-12 and abs(y1 - y0) < 1e-12:
        return []
    if abs(x1 - x0) < 1e-12 or abs(y1 - y0) < 1e-12:
        return [(x1, y1)]
    return [(x1, y0), (x1, y1)]


def segment_mm(state, seg):
    """段 → (mm 折线含首末 stub, stub_range)。

    stub_range = {"head": (lo,hi) 段内索引范围或 None, "tail": 同}——索
    引指 pts 列表位置, 覆盖 stub 折点（含终点真实端点）; 孔豁免与导出披
    露消费。"""
    lat = state.lattice
    pid = seg["partition_id"]
    eps = state.board_endpoint_mm(pid)
    anchors = [tuple(a) for a in state.anchors[pid]]
    grid = [tuple(g) for g in seg["grid"]]
    pts = []
    head = None
    tail = None
    if grid[0] in anchors:
        k = anchors.index(grid[0])
        stub = _mm_l_shape(lat.to_mm(*grid[0]), eps[k])
        # polyline 首点=真实端点（validate_routes 链审计口径）: 端点→…→锚
        pts.extend(reversed(stub))
        pts.append(lat.to_mm(*grid[0]))
        head = (0, len(pts) - 1) if stub else None
    else:
        pts.append(lat.to_mm(*grid[0]))
    for g in grid[1:]:
        pts.append(lat.to_mm(*g))
    if grid[-1] in anchors:
        k = anchors.index(grid[-1])
        stub = _mm_l_shape(lat.to_mm(*grid[-1]), eps[k])
        n_before = len(pts)
        pts.extend(stub)
        tail = (n_before, len(pts) - 1) if stub else None
    return pts, {"head": head, "tail": tail}
