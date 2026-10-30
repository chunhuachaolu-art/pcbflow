# -*- coding: utf-8 -*-
"""直角 Steiner 最小树（RSMT）——FLUTE 查表形态自研复现（V5-R1 W-1，2026-09-25）。

形态合同（V5-R1-STEINER-TOPOLOGY-TASKBOOK §2 W-1 + 用户八裁① 2026-09-24：
「FLUTE 查表形态自研=按论文形态复现、不引入原始代码分发物」；2026-09-25
实证修订披露见下）：

- **分层查表段（去重端点数 ≤ FLUTE_TABLE_MAX_DEGREE=5）**：按 FLUTE 论文的
  核心洞察——最优 RSMT 的线网结构（wireset=水平段集+垂直段集）只取决于端点
  的 x/y **秩形态**（相对位置序），与具体间距无关；同秩形态实例共享有限的
  「可能最优结构」（POT, possibly optimal topology）集合。本模块内嵌离线
  生成的形态索引 POT 表（``_POT_TABLES``：度数 → 形态键 (σx,σy) → 结构桶；
  由 tools/build_steiner_tables.py **分层形态枚举采样**填满——每形态桶采够
  每桶实例数后 DW 精确求解收集结构并集），运行时按实例形态查桶、桶内结构
  按实际坐标算 cost 取最小（平手取结构字典序最小=确定性）。
- **DW 在线精确段（6 ≤ 度数 ≤ 9）**：``exact_rsmt``（Dreyfus-Wagner on
  Hanan 格点）直接求解。**与「低度数 ≤9 查表」裁定形态的实证偏差披露**：
  随机采样并集表在度数 ≥5 覆盖率崩塌（形态空间 (n!)² 爆炸），度数 6-9 的
  形态完备分层表规模/生成时间不可行（本批复核）；按用户八裁①附款「GeoSteiner
  精确解对照锚若自研成本过高→双实现互证替代并披露，不停线」收口——DW 从
  对照锚上移为 6-9 生产段，3-5 查表段与 DW 在交叉域（独立验证集）逐件对账
  =双实现互证。DW 正确性由小度数暴力枚举交叉验证背书（tests）。
- **精确对照锚**：``exact_rsmt`` = Hanan 格点图 Dreyfus-Wagner 精确 Steiner
  树（Hanan 定理：最优 RSMT 的 Steiner 点必在端点坐标交点集上）——tests
  对照+6-9 生产段+表生成器共用单源。
- **高度数（>9 端）分解**：x 中位确定性剖分递归（FLUTE 分解形态），两子树
  以曼哈顿最近点对 L 形连接边拼接（平手取坐标字典序最小）。分解树为次优
  近似（如实披露）；PCB 信号网常见度数 2–10，>9 网占比逐板入 R1 普查表。

确定性合同：全程无随机/无时钟/无集合序依赖；全部 tie-break=坐标或结构
字典序；同输入同机双跑字节等（canonical 序输出）。

输出合同（``steiner_topology(points)``）：
  {"nodes": [[x,y],...],        # 端点（输入去重保序）+ Steiner 分支点（字典序）
   "edges": [[u,v],...],        # 树边（u<v 规范、字典序排列；度 2 直通点已压入边几何）
   "total_mm": float,           # 树总长（曼哈顿）
   "terminal_count": int,       # 前 terminal_count 个节点=pad 端点
   "method": "trivial"|"pot-table"|"pot-miss-exact-dw"|"exact-dw"|"decomposed",
   "algorithm": STEINER_VERSION}                    # 算法指纹（provenance 用）
节点/边构成连通无环树（Steiner 分支点=树上度 ≥3 的非端点节点）。空/单点
输入=退化（nodes 原样、edges=[]）；两点=单边。
"""
import heapq

STEINER_VERSION = "v5.steiner/1.0.0"

#: 分层形态完备查表段的度数上限（去重端点数 ≤ 此值按**秩形态索引**查表；
#: 2026-09-25 实证修订（两次）：①随机采样并集表在度数 ≥5 覆盖率崩塌
#: （形态空间 (n!)² 爆炸）→改 FLUTE 论文真实形态=按秩形态分层索引的 POT
#: 表（n×n 网格全枚举+随机远间距补充）；②度数 5 表生成-验证协议长尾缺陷
#: （验证早停条件在低概率形态下不可达，实测 2h 未收敛）→表段收口=3-4 度
#: （独立验证集 cover/optimal=72/72、588/588 全绿），5-9 合并 DW 在线精确段
#: （与原「≤9 查表」裁定形态的偏差如实披露；双实现互证=表段与 DW 段在
#: 3-4 度交叉域对账）。
FLUTE_TABLE_MAX_DEGREE = 4

#: DW 在线精确段的度数上限（去重端点数 ≤ 此值精确求解；> 此值走分解）。
FLUTE_EXACT_MAX_DEGREE = 9

_EPS = 1e-9


# ---------------------------------------------------------------- 基础件

def _dedup_points(points):
    """端点去重保序（浮点精确相等去重——pad 质心同坐标折叠）。"""
    seen = set()
    out = []
    for p in points:
        key = (float(p[0]), float(p[1]))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _mst_edges(points):
    """曼哈顿 MST（Kruskal，确定性：全边按 (len, i, j) 序）。对照基线用。"""
    n = len(points)

    class _Uf:
        def __init__(self, k):
            self.p = list(range(k))

        def find(self, x):
            while self.p[x] != x:
                self.p[x] = self.p[self.p[x]]
                x = self.p[x]
            return x

        def union(self, a, b):
            ra, rb = self.find(a), self.find(b)
            if ra == rb:
                return False
            self.p[ra] = rb
            return True

    cands = []
    for i in range(n):
        for j in range(i + 1, n):
            d = abs(points[i][0] - points[j][0]) + abs(points[i][1] - points[j][1])
            cands.append((round(d, 9), i, j))
    cands.sort()
    uf = _Uf(n)
    edges = []
    for d, i, j in cands:
        if uf.union(i, j):
            edges.append((i, j))
    return edges


def _segments_to_tree(points, h_segs, v_segs):
    """线段结构（绝对坐标段）→ (nodes, edges, total)。

    线段端点+交点构造节点集（含 Steiner 点=度 ≥3 交点）；边=细分后的连通
    单位（同行段按 x 区间切、同列段按 y 区间切，交点为切点）。确定性：
    节点坐标字典序、边 (min,max) 字典序。
    """
    pts = {(float(p[0]), float(p[1])) for p in points}   # 端点锚（V5-R1 修：
    # 落在段中间的端点必须进细分点集——只靠段端点+交点会漏（tmp108 PT-A0
    # 实证：端点在 V 段中间非交点 → 树缺端点节点 → 拓扑畸形））
    for hy, hx0, hx1 in h_segs:
        pts.add((hx0, hy))
        pts.add((hx1, hy))
    for x0, y0, y1 in v_segs:
        pts.add((x0, y0))
        pts.add((x0, y1))
    # 水平段上的垂直段 x 交点（细分切点）；垂直段上的水平段 y 交点
    h_list = list(h_segs)
    v_list = list(v_segs)
    for hy, hx0, hx1 in h_list:
        for vx, vy0, vy1 in v_list:
            if hx0 - _EPS <= vx <= hx1 + _EPS and vy0 - _EPS <= hy <= vy1 + _EPS:
                pts.add((vx, hy))
    pt_list = sorted(pts)
    idx = {p: k for k, p in enumerate(pt_list)}
    adj = {k: set() for k in range(len(pt_list))}
    # 段 → 细分邻接（段上全部切点按坐标串接）
    for hy, hx0, hx1 in h_list:
        on = sorted(px for (px, py) in pt_list
                    if abs(py - hy) <= _EPS and hx0 - _EPS <= px <= hx1 + _EPS)
        for a, b in zip(on[:-1], on[1:]):
            adj[idx[(a, hy)]].add(idx[(b, hy)])
            adj[idx[(b, hy)]].add(idx[(a, hy)])
    for vx, vy0, vy1 in v_list:
        on = sorted(py for (px, py) in pt_list
                    if abs(px - vx) <= _EPS and vy0 - _EPS <= py <= vy1 + _EPS)
        for a, b in zip(on[:-1], on[1:]):
            adj[idx[(vx, a)]].add(idx[(vx, b)])
            adj[idx[(vx, b)]].add(idx[(vx, a)])
    edges = sorted(tuple(sorted((a, b))) for a in adj for b in adj[a])
    seen_e = set()
    edges = [e for e in edges if not (e in seen_e or seen_e.add(e))]
    total = sum(abs(pt_list[a][0] - pt_list[b][0]) +
                abs(pt_list[a][1] - pt_list[b][1]) for a, b in edges)
    nodes = [list(p) for p in pt_list]
    return nodes, [[a, b] for a, b in edges], total


# ---------------------------------------------------------------- 精确对照锚
# Dreyfus-Wagner 图 Steiner 精确解（Hanan 格点图；GeoSteiner 角色替代——
# 生产路径零调用，仅 tools/build_steiner_tables.py（表生成）与 tests（对照）
# 消费；双实现互证披露见模块 docstring。

def exact_rsmt(points):
    """Hanan 格点图 Dreyfus-Wagner 精确 RSMT。

    返回 (total_length, nodes, edges)（同 steiner_topology 合同的树分解）。
    复杂度 O(3^k·V + 2^k·V²)（k=端点数、V=格点数 ≤ k²）；k ≤ 9 工程可行。
    确定性：merge 划分枚举序、grow 松弛序全部确定；tie-break=节点索引序。
    """
    pts = _dedup_points(points)
    n = len(pts)
    if n == 0:
        return 0.0, [], []
    if n == 1:
        return 0.0, [list(pts[0])], []
    if n == 2:
        d = abs(pts[0][0] - pts[1][0]) + abs(pts[0][1] - pts[1][1])
        return float(d), [list(p) for p in pts], [[0, 1]]
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    grid = [(x, y) for y in ys for x in xs]     # 行主序（y 升序 × x 升序）
    gidx = {p: i for i, p in enumerate(grid)}
    term = [gidx[p] for p in pts]               # 端点格点索引（输入序）
    V = len(grid)
    term_set = set(term)

    def manh(a, b):
        return abs(grid[a][0] - grid[b][0]) + abs(grid[a][1] - grid[b][1])

    INF = float("inf")
    dp = [dict() for _ in range(1 << n)]        # dp[S][v]
    for i in range(n):
        base = {}
        for v in range(V):
            base[v] = manh(term[i], v)
        dp[1 << i] = base
    # 子集序枚举（popcount 升序等价于数值序的 DAG 性：S1|S2=S ⟹ S1,S2 < S）
    for S in range(1, 1 << n):
        if S & (S - 1) == 0:
            continue                             # 单点集已初始化
        cur = {}
        # merge：枚举 S 的真子集 S1（S2=S^S1），S1 取含最低位的子集防重
        low = S & (-S)
        sub = (S - 1) & S
        best = [INF] * V
        while sub:
            if sub & low:
                d1, d2 = dp[sub], dp[S ^ sub]
                for v in range(V):
                    a = d1.get(v, INF)
                    if a < INF:
                        b = d2.get(v)
                        if b is not None and a + b < best[v]:
                            best[v] = a + b
            sub = (sub - 1) & S
        # grow：dp[S][v] = min_u best[u] + d(u, v)——多源 Dijkstra on 网格
        # 邻接图（每格点上下左右 4 邻居；网格最短路=曼哈顿，与全对度量闭包
        # 等价、稀疏实现快 ~7×；确定性：heap 键 (dist, node_idx)）
        heap = [(best[v], v) for v in range(V) if best[v] < INF]
        heapq.heapify(heap)
        dist = list(best)
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u] + 0.0:
                continue
            ux, uy = u % len(xs), u // len(xs)      # 行主序 ↔ (ix, iy)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx_, ny_ = ux + dx, uy + dy
                if not (0 <= nx_ < len(xs) and 0 <= ny_ < len(ys)):
                    continue
                v = ny_ * len(xs) + nx_
                nd = d + abs(xs[nx_] - xs[ux]) + abs(ys[ny_] - ys[uy])
                if nd < dist[v] - _EPS:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        dp[S] = {v: dist[v] for v in range(V) if dist[v] < INF}
    full = (1 << n) - 1
    total = min(dp[full].values())

    # ---- 回溯提取树（确定性：字典序最小决策）----
    # used_segs 收集 (回溯路径的曼哈顿 Z 形分解=先 x 后 y；路径并集=树铜)
    segs_h, segs_v = [], []

    def add_path(u, v):
        (x0, y0), (x1, y1) = grid[u], grid[v]
        if abs(x0 - x1) <= _EPS and abs(y0 - y1) <= _EPS:
            return
        if abs(y0 - y1) <= _EPS:
            segs_h.append((y0, min(x0, x1), max(x0, x1)))
        elif abs(x0 - x1) <= _EPS:
            segs_v.append((x0, min(y0, y1), max(y0, y1)))
        else:
            # Z 形（先水平后垂直）；拐点=(x1,y0) 是 Hanan 格点
            segs_h.append((y0, min(x0, x1), max(x0, x1)))
            segs_v.append((x1, y0, y1) if y0 < y1 else (x1, y1, y0))

    def backtrack(S, v):
        """提取覆盖 S∪{v} 的最优树路径集（逆着 merge/grow 决策走）。"""
        if S == 0:
            return
        if S & (S - 1) == 0:
            i = S.bit_length() - 1
            add_path(term[i], v)
            return
        val = dp[S][v]
        # grow 候选：u with dp[S][u]+manh(u,v)==val 且 dp[S][u] 严格小于 val
        #（grow 链沿 dp 值严格递减——排除互为前驱的对称死循环；浮点 EPS 界）
        cands_u = [u for u in range(V)
                   if u != v and dp[S].get(u, INF) + manh(u, v) <= val + _EPS
                   and dp[S][u] < val - _EPS]
        merged = None
        low = S & (-S)
        sub = (S - 1) & S
        while sub:
            if sub & low:
                d1, d2 = dp[sub].get(v), dp[S ^ sub].get(v)
                if d1 is not None and d2 is not None and d1 + d2 <= val + _EPS:
                    merged = (sub, d1, d2)
                    break
            sub = (sub - 1) & S
        if merged is not None:
            backtrack(merged[0], v)
            backtrack(S ^ merged[0], v)
            return
        if cands_u:
            u = cands_u[0]
            add_path(u, v)
            backtrack(S, u)
            return
        raise AssertionError("DW 回溯失败（内部错误）")

    v_best = min(range(V), key=lambda vv: (dp[full][vv], vv))
    backtrack(full, v_best)
    nodes, edges, tot = _segments_to_tree(pts, segs_h, segs_v)
    return float(min(total, tot)), nodes, edges


# ---------------------------------------------------------------- POT 查表段

def _structure_cost(struct, xs, ys):
    """POT 结构在实例坐标（xs/ys=升序坐标值表）下的树总长。"""
    total = 0.0
    for row, lo, hi in struct[0]:
        total += xs[hi] - xs[lo]
    for col, lo, hi in struct[1]:
        total += ys[hi] - ys[lo]
    return total


def _structure_covers(struct, cells, k, l):
    """结构对实例的合法性：秩域 ⊆ 实例秩网格（k×l），且每个端点格落在
    某结构段上（覆盖端点）。秩形态不匹配的结构=非法（跳过）——自研表为
    采样并集，非全秩形态完备（披露见模块 docstring）。"""
    for row, lo, hi in struct[0]:
        if row >= l or hi >= k:
            return False
    for col, lo, hi in struct[1]:
        if col >= k or hi >= l:
            return False
    for cx, cy in cells:
        ok = any(row == cy and lo <= cx <= hi for row, lo, hi in struct[0]) or \
             any(col == cx and lo <= cy <= hi for col, lo, hi in struct[1])
        if not ok:
            return False
    return True


def _structure_tree(struct, xs, ys, term_cells):
    """POT 结构 + 实例端点 → 树分解（nodes/edges；绝对坐标）。

    term_cells=[(xi,yi) 秩对]（端点在秩网格的位置）。结构段以秩表达
    （H 段=(y 行秩, x_lo 秩, x_hi 秩)），换算绝对坐标后复用
    _segments_to_tree。
    """
    h_segs = [(ys[row], xs[lo], xs[hi]) for row, lo, hi in struct[0]]
    v_segs = [(xs[col], ys[lo], ys[hi]) for col, lo, hi in struct[1]]
    pts = [(xs[cx], ys[cy]) for cx, cy in term_cells]
    # 连通性核验（防御：结构生成时已验证；实例秩形态一致即连通）
    all_nodes = set(pts)
    nodes, edges, total = _segments_to_tree(list(all_nodes), h_segs, v_segs)
    return nodes, edges, total


def _shape_key(points):
    """秩形态键（FLUTE 布局索引的自研形态；规范形）：端点按 (x,y) 升序重排
    （σx 恒等化——RSMT 结构对端点标注序不敏感），键=(重排后各位置的 x 秩
    序列, y 秩序列)（秩=去重坐标升序索引；共 x/共 y 退化的 Hanan 网格尺寸
    差异由秩序列并列模式捕获——完备区分）。同键实例共享 POT 结构桶（结构
    cost=间距线性函数、最优结构只随形态切换——FLUTE 核心洞察）。"""
    order = sorted(points, key=lambda p: (p[0], p[1]))
    xr = {v: k for k, v in enumerate(sorted({p[0] for p in order}))}
    yr = {v: k for k, v in enumerate(sorted({p[1] for p in order}))}
    return (tuple(xr[p[0]] for p in order), tuple(yr[p[1]] for p in order))


def _pot_solve(points):
    """低度数查表段主路径：实例秩形态 → 表桶（同形态 POT 结构集）→ 逐结构
    核验覆盖后算 cost 取最小。桶缺失（表覆盖缺口，分层完备后不应发生=防御）
    → None（调用方走 DW 兜底）。"""
    bucket = _POT_TABLES.get(len(points), {}).get(_shape_key(points))
    if not bucket:
        return None
    xs = sorted({p[0] for p in points})
    ys = sorted({p[1] for p in points})
    xi = {v: k for k, v in enumerate(xs)}
    yi = {v: k for k, v in enumerate(ys)}
    cells = [(xi[p[0]], yi[p[1]]) for p in points]
    best = None
    best_cost = None
    for struct in bucket:
        if not _structure_covers(struct, cells, len(xs), len(ys)):
            continue
        c = _structure_cost(struct, xs, ys)
        if best_cost is None or c < best_cost - _EPS or \
                (abs(c - best_cost) <= _EPS and struct < best):
            best, best_cost = struct, c
    if best is None:
        return None
    return _structure_tree(best, xs, ys, cells)


# ---------------------------------------------------------------- 高度数分解

def _solve_exact(points):
    """≤9 端精确求解（表段+DW 段统一入口）：≤FLUTE_TABLE_MAX_DEGREE 先查表
    （缺口 DW 兜底，method 标注兜底来源）；其余 DW 在线精确。返回
    (nodes, edges, total, method)。"""
    n = len(points)
    if n <= FLUTE_TABLE_MAX_DEGREE:
        r = _pot_solve(points)
        if r is not None:
            return r[0], r[1], r[2], "pot-table"
        total, nodes, edges = exact_rsmt(points)
        return nodes, edges, total, "pot-miss-exact-dw"
    total, nodes, edges = exact_rsmt(points)
    return nodes, edges, total, "exact-dw"


def _spanning_edges(nodes, edges, connect_last=None):
    """合并边集 → 生成树边集（Kruskal；确定性）：自环剔除、边规范序排序
    （连接边殿后保分解语义），union-find 破环；返回 [[u,v]...] 规范序。"""
    uf = list(range(len(nodes)))

    def find(x):
        while uf[x] != x:
            uf[x] = uf[uf[x]]
            x = uf[x]
        return x

    def key(e):
        return (1, e) if tuple(e) == tuple(sorted(connect_last or (-1, -1)))             else (0, e)

    out = []
    for e in sorted((sorted([min(a, b), max(a, b)]) for a, b in edges
                     if a != b), key=lambda e: tuple(e)):
        ra, rb = find(e[0]), find(e[1])
        if ra != rb:
            uf[ra] = rb
            out.append(e)
    return sorted(out)


def _decompose_solve(points):
    """高度数（>9）分解段：x 中位剖分递归 + 最近点对 L 连接（FLUTE 分解形态）。"""
    n = len(points)

    def solve(pts):
        if len(pts) <= FLUTE_EXACT_MAX_DEGREE:
            nodes, edges, total, _m = _solve_exact(pts)
            return (nodes, edges, total), len(pts)
        order = sorted(pts)                      # 字典序=确定性剖分
        half = (len(order) + 1) // 2
        left, right = order[:half], order[half:]
        (nl, el, _tl), _ = solve(left)
        (nr, er, _tr), _ = solve(right)
        # 最近点对（曼哈顿；平手字典序）
        bp, bq, bd = None, None, None
        for p in nl:
            for q in nr:
                d = abs(p[0] - q[0]) + abs(p[1] - q[1])
                if bd is None or d < bd - _EPS or (abs(d - bd) <= _EPS and
                                                   (p, q) < (bp, bq)):
                    bp, bq, bd = p, q, d
        nodes = [list(p) for p in sorted(set(map(tuple, nl)) | set(map(tuple, nr)))]
        remap = {tuple(p): k for k, p in enumerate(nodes)}
        edges = [[remap[tuple(nl[a])], remap[tuple(nl[b])]] for a, b in el]
        edges += [[remap[tuple(nr[a])], remap[tuple(nr[b])]] for a, b in er]
        eb, eq = remap[tuple(bp)], remap[tuple(bq)]
        if eb != eq:
            edges.append([min(eb, eq), max(eb, eq)])
        # 树性收口（确定性）：子树节点集可能坐标重叠（左子树 Steiner 点=
        # 右子树端点等）→ 合并图可含环/共享点；Kruskal 生成树（边序=先子树
        # 边按规范字典序、连接边殿后）破环保连通——真板 495 端 GND 实证路径
        edges = _spanning_edges(nodes, edges, connect_last=(eb, eq))
        total = sum(abs(nodes[a][0] - nodes[b][0]) +
                    abs(nodes[a][1] - nodes[b][1]) for a, b in edges)
        return (nodes, edges, total), len(pts)

    (nodes, edges, total), _ = solve(list(points))
    return nodes, edges, total


def _mst_fallback(points):
    """MST 兜底树（表缺失防御路径 / W-4 Steiner 点不可达回退用）。"""
    edges = _mst_edges(points)
    nodes = [list(p) for p in points]
    total = sum(abs(points[a][0] - points[b][0]) +
                abs(points[a][1] - points[b][1]) for a, b in edges)
    return nodes, [[a, b] for a, b in edges], total


def _tree_to_topology(base_pts, nodes, edges):
    """细分树 → 拓扑规范形：节点=端点 ∪ 度 ≥3 分支点（度 2 直通点压入边
    几何）；nodes=端点（base_pts 输入序）在前+分支点（坐标字典序）在后；
    edges=[[u,v]] 规范字典序。返回 (nodes, edges, terminal_count)。"""
    node_t = [tuple(p) for p in nodes]
    is_term = {tuple(p) for p in base_pts}
    adj = {i: set() for i in range(len(node_t))}
    for u, v in edges:
        if u == v:
            continue                             # 自环剔除（防御）
        adj[u].add(v)
        adj[v].add(u)
    # 悬垂修剪（V5-R1）：度 1 非端点死枝迭代剪除——分解段合并（子树节点
    # 坐标重叠→Kruskal 破环）后叶子可为非端点；修剪只减总长，剪至全叶子
    # =端点后拓扑合同（节点=端点∪度 ≥3 分支点）成立。真板 495 端 GND 实证。
    while True:
        leaves = [i for i in adj
                  if len(adj[i]) == 1 and node_t[i] not in is_term]
        if not leaves:
            break
        for lf in leaves:
            nb = next(iter(adj[lf]))
            adj[nb].discard(lf)
            del adj[lf]
    # 分量补边（分解段破环/修剪可留孤立节点——thunderbolt 395 端网实证：
    # 修剪删 Steiner 悬垂后其挂接端点孤立）。保树性合同：分量间最近
    # 曼哈顿节点对逐次补边（确定性：距离、节点索引序），物理语义=孤立
    # 端点的 L 形补充连接（次优，如实披露于 R1-REPORT §1.3）。
    while True:
        comp = {}
        cid = 0
        for start in sorted(adj):
            if start in comp:
                continue
            stack = [start]
            comp[start] = cid
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if v not in comp:
                        comp[v] = cid
                        stack.append(v)
            cid += 1
        if cid <= 1:
            break
        best = None
        nodes_list = sorted(adj)
        for a in nodes_list:
            for b in nodes_list:
                if comp[a] == comp[b]:
                    continue
                d = (abs(node_t[a][0] - node_t[b][0])
                     + abs(node_t[a][1] - node_t[b][1]))
                if best is None or d < best[0] - _EPS:
                    best = (d, a, b)
        _d, a, b = best
        adj[a].add(b)
        adj[b].add(a)
    keep = set(i for i in adj
               if node_t[i] in is_term or len(adj[i]) >= 3)
    if not keep:                                   # 防御（空树）
        keep = {0} if node_t else set()
    tedges = set()
    for s in sorted(keep):
        for nxt in sorted(adj[s]):
            prev, cur = s, nxt
            while cur not in keep:
                nn = [x for x in adj[cur] if x != prev]
                prev, cur = cur, nn[0]
            a, b = (s, cur) if s < cur else (cur, s)
            if a != b:
                tedges.add((a, b))
    branch = sorted(node_t[i] for i in keep if node_t[i] not in is_term)
    order = list(base_pts) + branch
    remap = {p: k for k, p in enumerate(order)}
    out_nodes = [[float(p[0]), float(p[1])] for p in order]
    out_edges = sorted([sorted([remap[node_t[a]], remap[node_t[b]]])
                        for a, b in tedges])
    # 树性终检（fail-loud 防畸形拓扑落盘：细分端点锚缺失曾产 4 节点 1 边
    # 畸形——tmp108 PT-A0 实证；此处兜底为断言而非静默）
    if len(out_edges) != max(0, len(out_nodes) - 1):
        raise AssertionError(
            "拓扑规范形树性失守：%d 节点 %d 边（细分端点锚/修剪合同破坏）"
            % (len(out_nodes), len(out_edges)))
    return out_nodes, out_edges, len(base_pts)


# ---------------------------------------------------------------- 主入口

def steiner_topology(points):
    """RSMT 拓扑（生产入口；合同见模块 docstring）。

    输出 nodes 合同：端点（输入去重保序）在前 + 分支点（坐标字典序）在后；
    edges=[[u,v]] 规范字典序；``terminal_count``=前若干节点为 pad 端点。"""
    pts = _dedup_points(points)
    n = len(pts)
    if n == 0:
        return {"nodes": [], "edges": [], "total_mm": 0.0,
                "terminal_count": 0, "method": "trivial",
                "algorithm": STEINER_VERSION}
    if n == 1:
        return {"nodes": [list(pts[0])], "edges": [], "total_mm": 0.0,
                "terminal_count": 1, "method": "trivial",
                "algorithm": STEINER_VERSION}
    if n == 2:
        d = abs(pts[0][0] - pts[1][0]) + abs(pts[0][1] - pts[1][1])
        return {"nodes": [list(p) for p in pts], "edges": [[0, 1]],
                "total_mm": float(d), "terminal_count": 2,
                "method": "trivial", "algorithm": STEINER_VERSION}
    if n <= FLUTE_EXACT_MAX_DEGREE:
        nodes, edges, total, method = _solve_exact(pts)
        tn, te, _tc = _tree_to_topology(pts, nodes, edges)
        return {"nodes": tn, "edges": te, "total_mm": float(total),
                "terminal_count": n, "method": method,
                "algorithm": STEINER_VERSION}
    nodes, edges, total = _decompose_solve(pts)
    tn, te, _tc = _tree_to_topology(pts, nodes, edges)
    return {"nodes": tn, "edges": te, "total_mm": float(total),
            "terminal_count": n, "method": "decomposed",
            "algorithm": STEINER_VERSION}


# ================================================================ POT 表区
# （tools/build_steiner_tables.py 生成回填——勿手改；表={度数: {形态键:
#  [(H 段列表, V 段列表)...]}}；形态键=(x 秩序列, y 秩序列)=端点按 (x,y)
# 升序重排后的秩序列（规范形，与端点输入序无关）；段=(秩, 秩, 秩) 三元组）

_POT_TABLES = {
    3: {
        ((0, 0, 0), (0, 1, 2)): [
            ([], [(0, 0, 2)]),
        ],
        ((0, 0, 1), (0, 1, 0)): [
            ([(0, 0, 1)], [(0, 0, 1)]),
        ],
        ((0, 0, 1), (0, 1, 1)): [
            ([(1, 0, 1)], [(0, 0, 1)]),
        ],
        ((0, 0, 1), (0, 1, 2)): [
            ([(2, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1), (0, 2, 1)): [
            ([(1, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1), (1, 2, 0)): [
            ([(0, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 1, 1), (0, 0, 1)): [
            ([(0, 0, 1)], [(1, 0, 1)]),
        ],
        ((0, 1, 1), (0, 1, 2)): [
            ([(0, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1), (1, 0, 1)): [
            ([(1, 0, 1)], [(1, 0, 1)]),
        ],
        ((0, 1, 1), (1, 0, 2)): [
            ([(1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1), (2, 0, 1)): [
            ([(2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (0, 0, 0)): [
            ([(0, 0, 2)], []),
        ],
        ((0, 1, 2), (0, 0, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2), (0, 1, 0)): [
            ([(0, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2), (0, 1, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2), (0, 1, 2)): [
            ([(0, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (0, 2, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (1, 0, 0)): [
            ([(0, 0, 2)], [(0, 0, 1)]),
        ],
        ((0, 1, 2), (1, 0, 1)): [
            ([(1, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2), (1, 0, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (1, 1, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 1)]),
        ],
        ((0, 1, 2), (1, 2, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (2, 0, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2), (2, 1, 0)): [
            ([(0, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
    },
    4: {
        ((0, 0, 0, 0), (0, 1, 2, 3)): [
            ([], [(0, 0, 3)]),
        ],
        ((0, 0, 0, 1), (0, 1, 2, 0)): [
            ([(0, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 0, 1), (0, 1, 2, 1)): [
            ([(1, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 0, 1), (0, 1, 2, 2)): [
            ([(2, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 0, 1), (0, 1, 2, 3)): [
            ([(3, 0, 1)], [(0, 0, 3)]),
        ],
        ((0, 0, 0, 1), (0, 1, 3, 2)): [
            ([(2, 0, 1)], [(0, 0, 3)]),
        ],
        ((0, 0, 0, 1), (0, 2, 3, 1)): [
            ([(1, 0, 1)], [(0, 0, 3)]),
        ],
        ((0, 0, 0, 1), (1, 2, 3, 0)): [
            ([(0, 0, 1)], [(0, 0, 3)]),
        ],
        ((0, 0, 1, 1), (0, 1, 0, 1)): [
            ([(0, 0, 1)], [(0, 0, 1), (1, 0, 1)]),
            ([(0, 0, 1), (1, 0, 1)], [(0, 0, 1)]),
        ],
        ((0, 0, 1, 1), (0, 1, 0, 2)): [
            ([(0, 0, 1)], [(0, 0, 1), (1, 0, 2)]),
            ([(0, 0, 1), (2, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 1), (0, 1, 1, 2)): [
            ([(1, 0, 1)], [(0, 0, 1), (1, 1, 2)]),
        ],
        ((0, 0, 1, 1), (0, 1, 2, 3)): [
            ([(1, 0, 1)], [(0, 0, 1), (1, 1, 3)]),
        ],
        ((0, 0, 1, 1), (0, 2, 0, 1)): [
            ([(0, 0, 1)], [(0, 0, 2), (1, 0, 1)]),
            ([(0, 0, 1), (1, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 1), (0, 2, 1, 2)): [
            ([(0, 0, 1), (2, 0, 1)], [(1, 0, 2)]),
            ([(1, 0, 1)], [(0, 0, 2), (1, 1, 2)]),
        ],
        ((0, 0, 1, 1), (0, 2, 1, 3)): [
            ([(0, 0, 1), (2, 0, 1)], [(1, 0, 3)]),
            ([(1, 0, 1)], [(0, 0, 2), (1, 1, 3)]),
        ],
        ((0, 0, 1, 1), (0, 3, 1, 2)): [
            ([(0, 0, 1), (3, 0, 1)], [(1, 0, 3)]),
            ([(1, 0, 1)], [(0, 0, 3), (1, 1, 2)]),
        ],
        ((0, 0, 1, 1), (1, 2, 0, 1)): [
            ([(1, 0, 1)], [(0, 1, 2), (1, 0, 1)]),
        ],
        ((0, 0, 1, 1), (1, 2, 0, 2)): [
            ([(0, 0, 1), (2, 0, 1)], [(0, 0, 2)]),
            ([(1, 0, 1)], [(0, 1, 2), (1, 0, 2)]),
        ],
        ((0, 0, 1, 1), (1, 2, 0, 3)): [
            ([(0, 0, 1), (3, 0, 1)], [(0, 0, 3)]),
            ([(1, 0, 1)], [(0, 1, 2), (1, 0, 3)]),
        ],
        ((0, 0, 1, 1), (1, 3, 0, 2)): [
            ([(0, 0, 1), (2, 0, 1)], [(0, 0, 3)]),
            ([(1, 0, 1)], [(0, 1, 3), (1, 0, 2)]),
        ],
        ((0, 0, 1, 1), (2, 3, 0, 1)): [
            ([(1, 0, 1)], [(0, 1, 3), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 1, 0, 0)): [
            ([(0, 0, 2)], [(0, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 1, 0, 1)): [
            ([(0, 0, 1), (1, 0, 2)], [(0, 0, 1)]),
            ([(0, 0, 1), (1, 1, 2)], [(0, 0, 1), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 1, 0, 2)): [
            ([(0, 0, 1), (2, 0, 2)], [(0, 0, 2)]),
            ([(0, 0, 1), (2, 1, 2)], [(0, 0, 1), (1, 0, 2)]),
        ],
        ((0, 0, 1, 2), (0, 1, 1, 0)): [
            ([(0, 0, 2)], [(0, 0, 1), (1, 0, 1)]),
            ([(0, 0, 2), (1, 0, 1)], [(0, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 1, 1, 1)): [
            ([(1, 0, 2)], [(0, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 1, 1, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(0, 0, 1), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 1, 2, 0)): [
            ([(0, 0, 2)], [(0, 0, 1), (1, 0, 2)]),
            ([(0, 0, 2), (2, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 2), (0, 1, 2, 1)): [
            ([(1, 0, 2)], [(0, 0, 1), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 1, 2, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(0, 0, 1), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 1, 2, 3)): [
            ([(1, 0, 1), (3, 1, 2)], [(0, 0, 1), (1, 1, 3)]),
        ],
        ((0, 0, 1, 2), (0, 1, 3, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(0, 0, 1), (1, 1, 3)]),
        ],
        ((0, 0, 1, 2), (0, 2, 0, 1)): [
            ([(0, 0, 1), (1, 0, 2)], [(0, 0, 2)]),
            ([(0, 0, 1), (1, 1, 2)], [(0, 0, 2), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (0, 2, 1, 0)): [
            ([(0, 0, 2)], [(0, 0, 2), (1, 0, 1)]),
            ([(0, 0, 2), (1, 0, 1)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 2), (0, 2, 1, 1)): [
            ([(1, 0, 2)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 2), (0, 2, 1, 2)): [
            ([(0, 0, 1), (2, 0, 2)], [(1, 0, 2)]),
            ([(1, 0, 1), (2, 1, 2)], [(0, 0, 2), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 2, 1, 3)): [
            ([(0, 0, 1), (2, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
            ([(1, 0, 1), (3, 1, 2)], [(0, 0, 2), (1, 1, 3)]),
        ],
        ((0, 0, 1, 2), (0, 2, 2, 1)): [
            ([(0, 0, 1), (1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
            ([(1, 0, 2)], [(0, 0, 2), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 2, 3, 1)): [
            ([(0, 0, 1), (1, 1, 2), (2, 0, 1)], [(1, 0, 3)]),
            ([(1, 0, 2)], [(0, 0, 2), (1, 1, 3)]),
        ],
        ((0, 0, 1, 2), (0, 3, 1, 2)): [
            ([(0, 0, 1), (2, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
            ([(1, 0, 1), (2, 1, 2)], [(0, 0, 3), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (0, 3, 2, 1)): [
            ([(0, 0, 1), (1, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
            ([(1, 0, 2)], [(0, 0, 3), (1, 1, 2)]),
        ],
        ((0, 0, 1, 2), (1, 2, 0, 0)): [
            ([(0, 0, 2)], [(0, 0, 2)]),
        ],
        ((0, 0, 1, 2), (1, 2, 0, 1)): [
            ([(1, 0, 2)], [(0, 1, 2), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (1, 2, 0, 2)): [
            ([(0, 0, 1), (2, 0, 2)], [(0, 0, 2)]),
            ([(1, 0, 1), (2, 1, 2)], [(0, 1, 2), (1, 0, 2)]),
        ],
        ((0, 0, 1, 2), (1, 2, 0, 3)): [
            ([(0, 0, 1), (3, 0, 2)], [(0, 0, 3)]),
            ([(1, 0, 1), (3, 1, 2)], [(0, 1, 2), (1, 0, 3)]),
        ],
        ((0, 0, 1, 2), (1, 2, 1, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(0, 1, 2), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (1, 2, 2, 0)): [
            ([(0, 0, 2), (2, 0, 1)], [(0, 0, 2)]),
            ([(0, 1, 2), (1, 0, 1)], [(0, 1, 2), (1, 0, 2)]),
        ],
        ((0, 0, 1, 2), (1, 2, 3, 0)): [
            ([(0, 0, 2), (3, 0, 1)], [(0, 0, 3)]),
            ([(0, 1, 2), (1, 0, 1)], [(0, 1, 2), (1, 0, 3)]),
        ],
        ((0, 0, 1, 2), (1, 3, 0, 2)): [
            ([(0, 0, 1), (2, 0, 2)], [(0, 0, 3)]),
            ([(1, 0, 1), (2, 1, 2)], [(0, 1, 3), (1, 0, 2)]),
        ],
        ((0, 0, 1, 2), (1, 3, 2, 0)): [
            ([(0, 0, 2), (2, 0, 1)], [(0, 0, 3)]),
            ([(0, 1, 2), (1, 0, 1)], [(0, 1, 3), (1, 0, 2)]),
        ],
        ((0, 0, 1, 2), (2, 3, 0, 1)): [
            ([(1, 0, 2)], [(0, 1, 3), (1, 0, 1)]),
        ],
        ((0, 0, 1, 2), (2, 3, 1, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(0, 1, 3), (1, 0, 1)]),
        ],
        ((0, 1, 1, 1), (0, 0, 1, 2)): [
            ([(0, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 1), (0, 1, 2, 3)): [
            ([(0, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 1), (1, 0, 1, 2)): [
            ([(1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 1), (1, 0, 2, 3)): [
            ([(1, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 1), (2, 0, 1, 2)): [
            ([(2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 1), (2, 0, 1, 3)): [
            ([(2, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 1), (3, 0, 1, 2)): [
            ([(3, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (0, 0, 1, 0)): [
            ([(0, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 1, 2), (0, 0, 1, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 1, 2), (0, 0, 1, 2)): [
            ([(0, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (0, 0, 2, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (0, 1, 2, 0)): [
            ([(0, 0, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (0, 1, 2, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (0, 1, 2, 2)): [
            ([(0, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (0, 1, 2, 3)): [
            ([(0, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (0, 1, 3, 2)): [
            ([(0, 0, 1), (2, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (0, 2, 3, 1)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (1, 0, 1, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 1)]),
        ],
        ((0, 1, 1, 2), (1, 0, 1, 1)): [
            ([(1, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 1, 2), (1, 0, 1, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (1, 0, 2, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (1, 0, 2, 1)): [
            ([(1, 0, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (1, 0, 2, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (1, 0, 2, 3)): [
            ([(1, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (1, 0, 3, 2)): [
            ([(1, 0, 1), (2, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (1, 1, 2, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (1, 2, 3, 0)): [
            ([(0, 1, 2), (1, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (2, 0, 1, 0)): [
            ([(0, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (2, 0, 1, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (2, 0, 1, 2)): [
            ([(2, 0, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (2, 0, 1, 3)): [
            ([(2, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (2, 0, 2, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (2, 0, 3, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (2, 1, 2, 0)): [
            ([(0, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 1, 2), (2, 1, 3, 0)): [
            ([(0, 1, 2), (2, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (3, 0, 1, 2)): [
            ([(2, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (3, 0, 2, 1)): [
            ([(1, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 1, 2), (3, 1, 2, 0)): [
            ([(0, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
        ],
        ((0, 1, 2, 2), (0, 0, 0, 1)): [
            ([(0, 0, 2)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (0, 0, 1, 2)): [
            ([(0, 0, 2)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (0, 1, 0, 1)): [
            ([(0, 0, 2)], [(1, 0, 1), (2, 0, 1)]),
            ([(0, 0, 2), (1, 1, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 2), (0, 1, 0, 2)): [
            ([(0, 0, 2)], [(1, 0, 1), (2, 0, 2)]),
            ([(0, 0, 2), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 2), (0, 1, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 2), (0, 1, 2, 3)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 2), (0, 2, 0, 1)): [
            ([(0, 0, 2)], [(1, 0, 2), (2, 0, 1)]),
            ([(0, 0, 2), (1, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 2), (0, 2, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 2), (2, 1, 2)]),
            ([(0, 0, 2), (2, 1, 2)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (0, 2, 1, 3)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 2), (2, 1, 3)]),
            ([(0, 0, 2), (2, 1, 2)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 2), (0, 3, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2)], [(1, 0, 3), (2, 1, 2)]),
            ([(0, 0, 2), (3, 1, 2)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 2), (1, 0, 0, 1)): [
            ([(0, 0, 2)], [(0, 0, 1), (2, 0, 1)]),
            ([(0, 1, 2), (1, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 2), (1, 0, 0, 2)): [
            ([(0, 0, 2)], [(0, 0, 1), (2, 0, 2)]),
            ([(0, 1, 2), (1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 2), (1, 0, 1, 2)): [
            ([(1, 0, 2)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 2), (1, 0, 2, 3)): [
            ([(1, 0, 2)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 2), (1, 1, 0, 1)): [
            ([(1, 0, 2)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (1, 1, 0, 2)): [
            ([(1, 0, 2)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (1, 2, 0, 1)): [
            ([(1, 0, 2)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (1, 2, 0, 2)): [
            ([(0, 1, 2), (1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
            ([(1, 0, 2)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (1, 2, 0, 3)): [
            ([(0, 1, 2), (1, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
            ([(1, 0, 2)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 2), (1, 3, 0, 2)): [
            ([(0, 1, 2), (1, 0, 1), (2, 1, 2)], [(1, 0, 3)]),
            ([(1, 0, 2)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (2, 0, 0, 1)): [
            ([(0, 0, 2)], [(0, 0, 2), (2, 0, 1)]),
            ([(0, 1, 2), (1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 2), (2, 0, 1, 2)): [
            ([(0, 1, 2), (2, 0, 2)], [(2, 0, 2)]),
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 2), (2, 1, 2)]),
        ],
        ((0, 1, 2, 2), (2, 0, 1, 3)): [
            ([(0, 1, 2), (2, 0, 2)], [(2, 0, 3)]),
            ([(1, 1, 2), (2, 0, 1)], [(1, 0, 2), (2, 1, 3)]),
        ],
        ((0, 1, 2, 2), (2, 1, 0, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (2, 1, 0, 2)): [
            ([(0, 1, 2), (2, 0, 2)], [(1, 0, 2)]),
            ([(1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (2, 1, 0, 3)): [
            ([(0, 1, 2), (2, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
            ([(1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 2), (2, 2, 0, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (2, 3, 0, 1)): [
            ([(1, 1, 2), (2, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
        ((0, 1, 2, 2), (3, 0, 1, 2)): [
            ([(0, 1, 2), (3, 0, 2)], [(2, 0, 3)]),
            ([(1, 1, 2), (3, 0, 1)], [(1, 0, 3), (2, 1, 2)]),
        ],
        ((0, 1, 2, 2), (3, 1, 0, 2)): [
            ([(0, 1, 2), (2, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
            ([(1, 1, 2), (3, 0, 1)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 2), (3, 2, 0, 1)): [
            ([(1, 1, 2), (3, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 0, 0, 0)): [
            ([(0, 0, 3)], []),
        ],
        ((0, 1, 2, 3), (0, 0, 0, 1)): [
            ([(0, 0, 2), (1, 2, 3)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 0, 1, 0)): [
            ([(0, 0, 3)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 0, 1, 1)): [
            ([(0, 0, 2), (1, 2, 3)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 0, 1, 2)): [
            ([(0, 0, 2), (2, 2, 3)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 0, 2, 1)): [
            ([(0, 0, 2), (1, 2, 3)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 0, 0)): [
            ([(0, 0, 3)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 1, 0, 1)): [
            ([(0, 0, 2), (1, 1, 3)], [(1, 0, 1)]),
            ([(0, 0, 2), (1, 2, 3)], [(1, 0, 1), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 1, 0, 2)): [
            ([(0, 0, 2), (2, 1, 3)], [(1, 0, 2)]),
            ([(0, 0, 2), (2, 2, 3)], [(1, 0, 1), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 1, 0)): [
            ([(0, 0, 3)], [(1, 0, 1), (2, 0, 1)]),
            ([(0, 0, 3), (1, 1, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 1, 1, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 1, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 2, 0)): [
            ([(0, 0, 3)], [(1, 0, 1), (2, 0, 2)]),
            ([(0, 0, 3), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 2, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 2, 2)): [
            ([(0, 0, 1), (1, 1, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (0, 1, 2, 3)): [
            ([(0, 0, 1), (1, 1, 2), (3, 2, 3)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (0, 1, 3, 2)): [
            ([(0, 0, 1), (1, 1, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (0, 2, 0, 1)): [
            ([(0, 0, 2), (1, 1, 3)], [(1, 0, 2)]),
            ([(0, 0, 2), (1, 2, 3)], [(1, 0, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (0, 2, 1, 0)): [
            ([(0, 0, 3)], [(1, 0, 2), (2, 0, 1)]),
            ([(0, 0, 3), (1, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 2, 1, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 2, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2), (2, 2, 3)], [(1, 0, 2), (2, 1, 2)]),
            ([(0, 0, 2), (2, 1, 3)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 2, 1, 3)): [
            ([(0, 0, 1), (1, 1, 2), (3, 2, 3)], [(1, 0, 2), (2, 1, 3)]),
            ([(0, 0, 2), (2, 1, 2), (3, 2, 3)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (0, 2, 2, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 2), (2, 1, 2)]),
            ([(0, 0, 2), (1, 2, 3), (2, 1, 2)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (0, 2, 3, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 2), (2, 1, 3)]),
            ([(0, 0, 2), (1, 2, 3), (2, 1, 2)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (0, 3, 1, 2)): [
            ([(0, 0, 1), (1, 1, 2), (2, 2, 3)], [(1, 0, 3), (2, 1, 2)]),
            ([(0, 0, 2), (2, 2, 3), (3, 1, 2)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (0, 3, 2, 1)): [
            ([(0, 0, 1), (1, 1, 3)], [(1, 0, 3), (2, 1, 2)]),
            ([(0, 0, 2), (1, 2, 3), (3, 1, 2)], [(2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (1, 0, 0, 0)): [
            ([(0, 0, 3)], [(0, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 0, 0, 1)): [
            ([(0, 0, 2), (1, 2, 3)], [(0, 0, 1), (2, 0, 1)]),
            ([(0, 1, 2), (1, 0, 3)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 0, 0, 2)): [
            ([(0, 0, 2), (2, 2, 3)], [(0, 0, 1), (2, 0, 2)]),
            ([(0, 1, 2), (1, 0, 1), (2, 1, 3)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 0, 1, 0)): [
            ([(0, 0, 3)], [(0, 0, 1), (2, 0, 1)]),
            ([(0, 1, 3), (1, 0, 2)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 0, 1, 1)): [
            ([(1, 0, 3)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 0, 1, 2)): [
            ([(1, 0, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (1, 0, 2, 0)): [
            ([(0, 0, 3)], [(0, 0, 1), (2, 0, 2)]),
            ([(0, 1, 3), (1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 0, 2, 1)): [
            ([(1, 0, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (1, 0, 2, 2)): [
            ([(1, 0, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (1, 0, 2, 3)): [
            ([(1, 0, 2), (3, 2, 3)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (1, 0, 3, 2)): [
            ([(1, 0, 2), (2, 2, 3)], [(1, 0, 1), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (1, 1, 0, 0)): [
            ([(0, 1, 3), (1, 0, 1)], [(1, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 1, 0, 1)): [
            ([(1, 0, 3)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 1, 0, 2)): [
            ([(1, 0, 2), (2, 2, 3)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 1, 1, 0)): [
            ([(0, 2, 3), (1, 0, 2)], [(2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 1, 2, 0)): [
            ([(0, 2, 3), (1, 0, 2)], [(2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 2, 0, 0)): [
            ([(0, 1, 3), (1, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 2, 0, 1)): [
            ([(1, 0, 3)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 2, 0, 2)): [
            ([(0, 1, 2), (1, 0, 1), (2, 1, 3)], [(1, 0, 2)]),
            ([(1, 0, 2), (2, 2, 3)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 2, 0, 3)): [
            ([(0, 1, 2), (1, 0, 1), (3, 1, 3)], [(1, 0, 3)]),
            ([(1, 0, 2), (3, 2, 3)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (1, 2, 1, 0)): [
            ([(0, 2, 3), (1, 0, 2)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (1, 2, 2, 0)): [
            ([(0, 1, 3), (1, 0, 1), (2, 1, 2)], [(1, 0, 2)]),
            ([(0, 2, 3), (1, 0, 2)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 2, 3, 0)): [
            ([(0, 1, 3), (1, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
            ([(0, 2, 3), (1, 0, 2)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (1, 3, 0, 2)): [
            ([(0, 1, 2), (1, 0, 1), (2, 1, 3)], [(1, 0, 3)]),
            ([(1, 0, 2), (2, 2, 3)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (1, 3, 2, 0)): [
            ([(0, 1, 3), (1, 0, 1), (2, 1, 2)], [(1, 0, 3)]),
            ([(0, 2, 3), (1, 0, 2)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 0, 1)): [
            ([(0, 0, 2), (1, 2, 3)], [(0, 0, 2), (2, 0, 1)]),
            ([(0, 1, 2), (1, 1, 3), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 1, 0)): [
            ([(0, 0, 3)], [(0, 0, 2), (2, 0, 1)]),
            ([(0, 1, 3), (1, 1, 2), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 1, 1)): [
            ([(1, 1, 3), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 1, 2)): [
            ([(0, 1, 2), (2, 0, 3)], [(2, 0, 2)]),
            ([(1, 1, 2), (2, 0, 1), (2, 2, 3)], [(1, 0, 2), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 1, 3)): [
            ([(0, 1, 2), (2, 0, 2), (3, 2, 3)], [(2, 0, 3)]),
            ([(1, 1, 2), (2, 0, 1), (3, 2, 3)], [(1, 0, 2), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (2, 0, 2, 1)): [
            ([(0, 1, 2), (1, 2, 3), (2, 0, 2)], [(2, 0, 2)]),
            ([(1, 1, 3), (2, 0, 1)], [(1, 0, 2), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (2, 0, 3, 1)): [
            ([(0, 1, 2), (1, 2, 3), (2, 0, 2)], [(2, 0, 3)]),
            ([(1, 1, 3), (2, 0, 1)], [(1, 0, 2), (2, 1, 3)]),
        ],
        ((0, 1, 2, 3), (2, 1, 0, 0)): [
            ([(0, 1, 3), (2, 0, 1)], [(1, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 1, 0, 1)): [
            ([(1, 1, 3), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (2, 1, 0, 2)): [
            ([(0, 1, 2), (2, 0, 3)], [(1, 0, 2)]),
            ([(1, 1, 2), (2, 0, 1), (2, 2, 3)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 1, 0, 3)): [
            ([(0, 1, 2), (2, 0, 1), (3, 1, 3)], [(1, 0, 3)]),
            ([(1, 1, 2), (2, 0, 1), (3, 2, 3)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (2, 1, 1, 0)): [
            ([(0, 2, 3), (1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (2, 1, 2, 0)): [
            ([(0, 1, 3), (2, 0, 2)], [(1, 0, 2)]),
            ([(0, 2, 3), (1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (2, 1, 3, 0)): [
            ([(0, 1, 3), (2, 0, 1), (3, 1, 2)], [(1, 0, 3)]),
            ([(0, 2, 3), (1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 3)]),
        ],
        ((0, 1, 2, 3), (2, 2, 0, 1)): [
            ([(1, 1, 3), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (2, 2, 1, 0)): [
            ([(0, 2, 3), (1, 1, 2), (2, 0, 1)], [(1, 1, 2), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (2, 3, 0, 1)): [
            ([(1, 1, 3), (2, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (2, 3, 1, 0)): [
            ([(0, 2, 3), (1, 1, 2), (2, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (3, 0, 1, 2)): [
            ([(0, 1, 2), (2, 2, 3), (3, 0, 2)], [(2, 0, 3)]),
            ([(1, 1, 2), (2, 2, 3), (3, 0, 1)], [(1, 0, 3), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (3, 0, 2, 1)): [
            ([(0, 1, 2), (1, 2, 3), (3, 0, 2)], [(2, 0, 3)]),
            ([(1, 1, 3), (3, 0, 1)], [(1, 0, 3), (2, 1, 2)]),
        ],
        ((0, 1, 2, 3), (3, 1, 0, 2)): [
            ([(0, 1, 2), (2, 1, 3), (3, 0, 1)], [(1, 0, 3)]),
            ([(1, 1, 2), (2, 2, 3), (3, 0, 1)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (3, 1, 2, 0)): [
            ([(0, 1, 3), (2, 1, 2), (3, 0, 1)], [(1, 0, 3)]),
            ([(0, 2, 3), (1, 1, 2), (3, 0, 1)], [(1, 1, 3), (2, 0, 2)]),
        ],
        ((0, 1, 2, 3), (3, 2, 0, 1)): [
            ([(1, 1, 3), (3, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
        ((0, 1, 2, 3), (3, 2, 1, 0)): [
            ([(0, 2, 3), (1, 1, 2), (3, 0, 1)], [(1, 1, 3), (2, 0, 1)]),
        ],
    },
}
