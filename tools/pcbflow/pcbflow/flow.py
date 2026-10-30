"""确定性最小费用最大流（SPEC §10.1 ④ 匝道/车道求解内核）。

连续最短路（SPFA/Bellman-Ford）增广；整数容量/费用；边按插入序存储——
调用方以稳定键序插边 ⇒ 同输入同输出（无随机、无 wall-clock）。

三态契约（SPEC §10.3）：
  flow == demand          → SAT（赋值即 witness）
  flow <  demand          → UNSAT，附最小割证书（max-flow min-cut：
                            cut 容量 == flow 值即可独立复核）
  模型建不起来（缺 basis/依赖缺失）→ UNKNOWN，由调用方判定，本模块不管。

证书独立复核：verify_min_cut 重算 S 可达性与 cut 容量，不信任 solve 内部状态。
"""

from __future__ import annotations

from collections import deque

INF = float("inf")


class MinCostFlow:
    """节点 0..n-1；add_edge 按调用序追加（确定性）；solve 后可取最小割。"""

    def __init__(self, n: int):
        self.n = n
        self.graph = [[] for _ in range(n)]  # 每项 = 边 [to, cap, cost, rev_index]
        self.edges = []                      # (u, v, cap, cost) 原始边账（含 cap=0 无）

    def add_edge(self, u: int, v: int, cap: int, cost: int) -> int:
        idx = len(self.edges)
        fwd = len(self.graph[u])
        self.edges.append((u, v, cap, cost, fwd))
        self.graph[u].append([v, cap, cost, len(self.graph[v])])
        self.graph[v].append([u, 0, -cost, fwd])
        return idx

    def residual_of(self, edge_idx: int) -> int:
        """原始边的剩余容量（0 = 已满载 = 命中分配）。"""
        u, _v, _cap, _cost, fwd = self.edges[edge_idx]
        return self.graph[u][fwd][1]


    def solve(self, s: int, t: int):
        """连续最短路增广到无负费用可达路径。返回 (flow, cost)。"""
        flow = cost = 0
        while True:
            dist = [INF] * self.n
            in_q = [False] * self.n
            prev_v = [-1] * self.n
            prev_e = [-1] * self.n
            dist[s] = 0
            dq = deque([s])
            in_q[s] = True
            while dq:
                u = dq.popleft()
                in_q[u] = False
                for i, e in enumerate(self.graph[u]):
                    v, cap, c, _rev = e
                    if cap > 0 and dist[u] + c < dist[v]:
                        dist[v] = dist[u] + c
                        prev_v[v] = u
                        prev_e[v] = i
                        if not in_q[v]:
                            dq.append(v)
                            in_q[v] = True
            if dist[t] == INF:
                return flow, cost
            # 瓶颈（本模型全部边 cap=1 或整型上限；逐单位增广保持确定性）
            push = INF
            v = t
            while v != s:
                push = min(push, self.graph[prev_v[v]][prev_e[v]][1])
                v = prev_v[v]
            v = t
            while v != s:
                e = self.graph[prev_v[v]][prev_e[v]]
                e[1] -= push
                self.graph[v][e[3]][1] += push
                v = prev_v[v]
            flow += push
            cost += push * dist[t]

    def residual_reachable(self, s: int) -> set:
        """残量网络中从 s 可达的点集 S（最小割源侧）。"""
        seen = {s}
        dq = deque([s])
        while dq:
            u = dq.popleft()
            for v, cap, _c, _rev in self.graph[u]:
                if cap > 0 and v not in seen:
                    seen.add(v)
                    dq.append(v)
        return seen


def min_cut_certificate(mcmf: MinCostFlow, s: int, t: int, flow_value: int,
                        node_names) -> dict:
    """最小割证书：S/T 划分 + 割边账 + 容量核算（可独立复核）。"""
    side = mcmf.residual_reachable(s)
    cut = []
    cut_cap = 0
    for (u, v, cap, _cost, _fwd) in mcmf.edges:
        if cap > 0 and u in side and v not in side:
            cut.append({"from": node_names[u], "to": node_names[v],
                        "cap": cap})
            cut_cap += cap
    return {
        "kind": "min_cut",
        "s_side": sorted(node_names[x] for x in side),
        "s_size": len(side),
        "t_size": mcmf.n - len(side),
        "cut_edges": cut,
        "cut_capacity": cut_cap,
        "flow_value": flow_value,
        "verified": cut_cap == flow_value and t not in side,
        "note": "max-flow min-cut：cut_capacity==flow_value 即证书成立"
                "（SPEC §10.3：无证书不得写 UNSAT）",
    }


def verify_min_cut(n: int, edges, s: int, t: int, s_side_names, flow_value: int,
                   node_names) -> bool:
    """独立复核最小割证书（测试与调用方均可 用；不信任求解器状态）。

    edges = [(u_name, v_name, cap)]（仅正向原始边）。
    校验：s∈S、t∉S、S 内部边不割、割边容量和==flow_value。
    """
    idx = {name: i for i, name in enumerate(node_names)}
    if not (0 <= s < len(node_names)) or not (0 <= t < len(node_names)):
        return False
    side = {idx[x] for x in s_side_names if x in idx}
    if s not in side or t in side:
        return False
    cap_sum = 0
    for (un, vn, cap) in edges:
        u, v = idx[un], idx[vn]
        if u in side and v not in side:
            cap_sum += cap
        elif u in side and v in side:
            pass
    return cap_sum == flow_value
