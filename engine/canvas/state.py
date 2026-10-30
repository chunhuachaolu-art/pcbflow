# -*- coding: utf-8 -*-
"""canvas.state -- 画板可变态单源（合同 CANVAS-API-CONTRACT §1 Lane-K1）。

结构（合同钉死）:
- 构造期冻结引用: board / board_path / board_sha256 / lat / anchors；
- 图元清单（shape_id 稳定寻址）:
  * segs:    {shape_id="seg:<net>:<seq>", net_id, partition_id, layer,
              grid:[[i,j],..], width_class}；
  * vias:    {shape_id="via:<net>:<i>_<j>", net_id, grid:[i,j]}；
  * widths:  网级宽度档 {net_id -> width_class}（无 shape_id，ripup 不寻址）；
  * placements: 分区放置覆盖 {partition_id -> {"move":[i,j]|None,
              "rotate":0|1|2|3, "flip":bool}}（只记覆盖，合法化检查归
              canvas.placecheck=M4 车道；无覆盖=原位）；
  * tunings: {shape_id="tun:<net>:<group>:<seq>", net_id, group_id, kind,
              grid, params}。
- 连通账本: connectivity{net_id->bool} + chain_detail{}——每次变更后重算；
  纪律=段衔接点必须有 via 在场（画板统一纪律，无 via 的共享格点不构成
  电连接——fail-closed），首段首点/末段末点=分区端点锚（placement 有
  覆盖时按覆盖后锚位）。
- 序列化: state_facts(st) / state_sha256(st) 复用 v5.canonical。
- 确定性: copy-on-write——一切变更构造新 dict，禁止 dict 迭代序渗入输出
  （facts 内列表一律按 shape_id/net_id/partition_id 排序构建）。

Lattice（本件内，画板坐标单源）:
- pitch 缺省 0.5mm；origin = floor(workspace 下界/pitch)*pitch（下界外对齐，
  格点域覆盖板框）；snap 取最近格点；端点锚冲突 fail-closed（语义与合同
  §0 依赖锚一致：板在该 pitch 下画板化不可行属数据源事实，不静默换 pitch）。

placement 覆盖的合成序（固定，docstring 级钉死；合法化判定不在本件）:
  真实端点 → rotate（绕分区中心 90°cw×turns，y 向下屏系 (dx,dy)->(-dy,dx)）
  → flip（绕中心 x 轴镜像 (dx,dy)->(-dx,dy)）→ move（平移使中心=目标格点 mm）
  → 重新 snap 到格点（画板锚恒为格点）。无覆盖字段=该步恒等。
"""
import math


class LatticeError(ValueError):
    pass


DEFAULT_PITCH_MM = 0.5


def _q(x):
    """mm 量化到 9 位小数（防浮点尾差渗入 canonical 输出；确定性纯函数）。"""
    return round(float(x), 9)


class Lattice(object):
    """整数格点阵（pitch/origin/覆盖板框的指标域）。"""

    def __init__(self, pitch_mm, x0, y0, i_max, j_max):
        if not (pitch_mm > 0.0):
            raise LatticeError("pitch 须为正（得到 %r）" % (pitch_mm,))
        self.pitch = float(pitch_mm)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.i_max = int(i_max)
        self.j_max = int(j_max)

    @classmethod
    def from_board(cls, board, pitch_mm=DEFAULT_PITCH_MM):
        ws = board["workspace"]
        x0 = math.floor(ws["x_min"] / pitch_mm) * pitch_mm
        y0 = math.floor(ws["y_min"] / pitch_mm) * pitch_mm
        i_max = int(math.floor((ws["x_max"] - x0) / pitch_mm))
        j_max = int(math.floor((ws["y_max"] - y0) / pitch_mm))
        return cls(pitch_mm, x0, y0, i_max, j_max)

    def to_mm(self, i, j):
        return (_q(self.x0 + int(i) * self.pitch),
                _q(self.y0 + int(j) * self.pitch))

    def snap(self, ex, ey):
        """mm → 最近格点指标（round-half-up，确定性）。"""
        fi = (float(ex) - self.x0) / self.pitch
        fj = (float(ey) - self.y0) / self.pitch
        return (int(math.floor(fi + 0.5)), int(math.floor(fj + 0.5)))

    def in_bounds(self, i, j):
        return 0 <= int(i) <= self.i_max and 0 <= int(j) <= self.j_max

    def as_dict(self):
        return {"pitch_mm": _q(self.pitch), "origin_mm": [_q(self.x0), _q(self.y0)],
                "i_max": self.i_max, "j_max": self.j_max}

    @classmethod
    def from_dict(cls, d):
        return cls(d["pitch_mm"], d["origin_mm"][0], d["origin_mm"][1],
                   d["i_max"], d["j_max"])


def anchor_map(board, lattice):
    """partition_id -> [[i,j] 端点0锚, [i,j] 端点1锚]（最近格点）。

    锚冲突（不同分区的端点同锚格点）fail-closed 抛 LatticeError。"""
    out = {}
    seen = {}
    for p in sorted(board["partitions"], key=lambda q: q["partition_id"]):
        pid = p["partition_id"]
        anchors = []
        for k, (ex, ey) in enumerate(p["geometry"]["endpoints"]):
            a = lattice.snap(ex, ey)
            key = tuple(a)
            if key in seen and seen[key][0] != pid:
                raise LatticeError(
                    "锚冲突 %s#%d 与 %s#%d 同锚 %s（pitch=%r 不可行）"
                    % (seen[key][0], seen[key][1], pid, k, list(a), lattice.pitch))
            seen[key] = (pid, k)
            if not lattice.in_bounds(*a):
                raise LatticeError("端点锚越界 %s %s" % (pid, list(a)))
            anchors.append(list(a))
        out[pid] = anchors
    return out


_KEEP = object()   # set_placement 的「本字段不变」哨兵


def _seg_shape_id(net_id, seq):
    return "seg:%s:%d" % (net_id, seq)


def _via_shape_id(net_id, i, j):
    return "via:%s:%d_%d" % (net_id, i, j)


def _tun_shape_id(net_id, group_id, seq):
    return "tun:%s:%s:%d" % (net_id, group_id, seq)


class CanvasState(object):
    """画板可变状态（board/lattice/anchors 构造期冻结引用）。"""

    def __init__(self, board, board_path, board_sha256, lat, anchors):
        self.board = board
        self.board_path = board_path
        self.board_sha256 = board_sha256
        self.lattice = lat
        self.anchors = anchors            # partition_id -> [[i,j],[i,j]]
        self.segs = {}                    # shape_id -> seg dict
        self.vias = {}                    # shape_id -> via dict
        self.widths = {}                  # net_id -> width_class
        self.placements = {}              # partition_id -> coverage dict
        self.tunings = {}                 # shape_id -> tuning dict
        self._seg_seq = 0
        self._tun_seq = {}                # net_id -> {group_id -> seq}
        self.connectivity = {n["net_id"]: False for n in board["nets"]}
        self.chain_detail = {}

    # ---------- 引用视图（只读） ----------

    def net_partitions(self, net_id):
        for n in self.board["nets"]:
            if n["net_id"] == net_id:
                return list(n["partitions"])
        return []

    def partition_net(self, pid):
        for n in self.board["nets"]:
            if pid in n["partitions"]:
                return n["net_id"]
        return None

    def board_partition(self, pid):
        for p in self.board["partitions"]:
            if p["partition_id"] == pid:
                return p
        return None

    def board_endpoint_mm(self, pid):
        p = self.board_partition(pid)
        if p is None:
            raise KeyError(pid)
        return [(float(e[0]), float(e[1])) for e in p["geometry"]["endpoints"]]

    def signal_layers(self):
        return [s["id"] for s in self.board["stackup"]
                if s.get("kind") == "signal" and s.get("available") is True]

    def known_nets(self):
        return {n["net_id"] for n in self.board["nets"]}

    def known_partitions(self):
        return {p["partition_id"] for p in self.board["partitions"]}

    def via_grids(self, net_id):
        return {tuple(v["grid"]) for v in self.vias.values()
                if v["net_id"] == net_id}

    def placement(self, pid):
        """覆盖记录（无覆盖=恒等覆盖原位）。"""
        cov = self.placements.get(pid)
        if cov is None:
            return {"move": None, "rotate": 0, "flip": False}
        return {"move": cov.get("move"), "rotate": cov.get("rotate", 0),
                "flip": bool(cov.get("flip", False))}

    def effective_endpoint_mm(self, pid):
        """真实端点 mm × placement 覆盖（合成序见模块 docstring）。"""
        pts = list(self.board_endpoint_mm(pid))
        cov = self.placement(pid)
        if cov["rotate"] or cov["flip"]:
            cx = (pts[0][0] + pts[1][0]) / 2.0
            cy = (pts[0][1] + pts[1][1]) / 2.0
            for _ in range(int(cov["rotate"]) % 4):
                pts = [(cx - (y - cy), cy + (x - cx)) for (x, y) in pts]
            if cov["flip"]:
                pts = [(cx - (x - cx), y) for (x, y) in pts]
        if cov["move"] is not None:
            tx, ty = self.lattice.to_mm(*cov["move"])
            cx = (pts[0][0] + pts[1][0]) / 2.0
            cy = (pts[0][1] + pts[1][1]) / 2.0
            pts = [(x + (tx - cx), y + (ty - cy)) for (x, y) in pts]
        return [(float(x), float(y)) for (x, y) in pts]

    def effective_anchors(self, pid):
        """覆盖后端点锚（格点；无覆盖=构造期锚）。"""
        if pid not in self.placements:
            return [list(a) for a in self.anchors[pid]]
        return [list(self.lattice.snap(x, y))
                for (x, y) in self.effective_endpoint_mm(pid)]

    # ---------- 变更（copy-on-write：新 dict 替换，不改旧条目） ----------

    def add_seg(self, net_id, partition_id, layer, grid, width_class):
        shape_id = _seg_shape_id(net_id, self._seg_seq)
        self._seg_seq += 1
        seg = {"shape_id": shape_id, "net_id": net_id,
               "partition_id": partition_id, "layer": layer,
               "grid": [list(p) for p in grid],
               "width_class": width_class}
        self.segs = dict(self.segs)
        self.segs[shape_id] = seg
        return seg

    def add_via(self, net_id, grid):
        i, j = grid
        shape_id = _via_shape_id(net_id, i, j)
        via = {"shape_id": shape_id, "net_id": net_id, "grid": [int(i), int(j)]}
        self.vias = dict(self.vias)
        self.vias[shape_id] = via
        return via

    def add_tuning(self, net_id, group_id, kind, grid, params):
        seq = self._tun_seq.get(net_id, {}).get(group_id, 0)
        self._tun_seq = dict(self._tun_seq)
        self._tun_seq[net_id] = dict(self._tun_seq.get(net_id, {}))
        self._tun_seq[net_id][group_id] = seq + 1
        shape_id = _tun_shape_id(net_id, group_id, seq)
        tun = {"shape_id": shape_id, "net_id": net_id, "group_id": group_id,
               "kind": kind, "grid": [list(p) for p in grid],
               "params": dict(params)}
        self.tunings = dict(self.tunings)
        self.tunings[shape_id] = tun
        return tun

    def set_width_class(self, net_id, width_class):
        """网级宽度档；同时重印本网既有 seg 的 width_class（不变量:
        seg.width_class == 生效网档，M3 宽度归一消费）。"""
        self.widths = dict(self.widths)
        self.widths[net_id] = width_class
        self.segs = {sid: (dict(seg, width_class=width_class)
                           if seg["net_id"] == net_id else seg)
                     for sid, seg in self.segs.items()}
        return self.widths

    def set_placement(self, partition_id, move=_KEEP, rotate=_KEEP,
                      flip=_KEEP):
        cov = self.placement(partition_id)
        new = {"move": cov["move"] if move is _KEEP else
               (list(move) if move is not None else None),
               "rotate": cov["rotate"] if rotate is _KEEP else int(rotate) % 4,
               "flip": cov["flip"] if flip is _KEEP else bool(flip)}
        self.placements = dict(self.placements)
        self.placements[partition_id] = new
        return new

    def remove_shape(self, shape_id):
        before = len(self.segs) + len(self.vias) + len(self.tunings)
        self.segs = {k: v for k, v in self.segs.items() if k != shape_id}
        self.vias = {k: v for k, v in self.vias.items() if k != shape_id}
        self.tunings = {k: v for k, v in self.tunings.items() if k != shape_id}
        after = len(self.segs) + len(self.vias) + len(self.tunings)
        return after < before

    def remove_net(self, net_id):
        """网级 ripup：清除该网 seg/via/tuning（widths 为网偏好非铜，保留）。"""
        had = (any(s["net_id"] == net_id for s in self.segs.values())
               or any(v["net_id"] == net_id for v in self.vias.values())
               or any(t["net_id"] == net_id for t in self.tunings.values()))
        self.segs = {k: v for k, v in self.segs.items()
                     if v["net_id"] != net_id}
        self.vias = {k: v for k, v in self.vias.items()
                     if v["net_id"] != net_id}
        self.tunings = {k: v for k, v in self.tunings.items()
                        if v["net_id"] != net_id}
        return had

    def gc_dangling_vias(self):
        """清除不在任何本网段/tuning waypoint 上的 via（ripup 后悬空孔）。"""
        keep = {}
        for sid, v in sorted(self.vias.items()):
            g = tuple(v["grid"])
            on_path = any(
                any(tuple(p) == g for p in s["grid"])
                for s in self.segs.values() if s["net_id"] == v["net_id"])
            if not on_path:
                on_path = any(
                    any(tuple(p) == g for p in t["grid"])
                    for t in self.tunings.values()
                    if t["net_id"] == v["net_id"])
            if on_path:
                keep[sid] = v
        removed = len(self.vias) - len(keep)
        self.vias = keep
        return removed

    # ---------- 连通账本 ----------

    def recompute_connectivity(self):
        """链审计（段衔接点必须 via；首末点=覆盖后分区端点锚）。

        图模型（fail-closed 纪律）: 节点=(格点, 域)，域∈{seg 段内点, via,
        term}。段内相邻 waypoint 连边；via 节点连接一切途经该格点的本网段
        （衔接必须 via——无 via 的共享格点不连边，记入
        junctions_missing_via）；端点锚 term 只经段首/末点附着。
        connectivity[net]=网内全部分区端点锚（覆盖后）落同一连通分量。"""
        self.connectivity = {n["net_id"]: False for n in self.board["nets"]}
        self.chain_detail = {}
        for n in sorted(self.board["nets"], key=lambda q: q["net_id"]):
            nid = n["net_id"]
            terminals = []
            for pid in n["partitions"]:
                for a in self.effective_anchors(pid):
                    terminals.append(tuple(a))
            term_set = set(terminals)
            via_pts = self.via_grids(nid)
            net_segs = [self.segs[sid] for sid in sorted(self.segs)
                        if self.segs[sid]["net_id"] == nid]
            net_tuns = [self.tunings[sid] for sid in sorted(self.tunings)
                        if self.tunings[sid]["net_id"] == nid]
            edges = []          # (node_key, node_key)
            dangling = []
            occupancy = {}      # pt -> {shape_id}
            for seg in net_segs:
                path = [tuple(p) for p in seg["grid"]]
                h, t = path[0], path[-1]
                attached = ((h in term_set or h in via_pts)
                            and (t in term_set or t in via_pts))
                if attached and len(path) >= 2:
                    for a, b in zip(path[:-1], path[1:]):
                        edges.append(((a, seg["shape_id"]),
                                      (b, seg["shape_id"])))
                else:
                    dangling.append(seg["shape_id"])
                for p in set(path):
                    occupancy.setdefault(p, set()).add(seg["shape_id"])
            for tun in net_tuns:
                path = [tuple(p) for p in tun["grid"]]
                for p in set(path):
                    occupancy.setdefault(p, set()).add(tun["shape_id"])
            junctions_no_via = sorted(
                pt for pt, owners in occupancy.items()
                if len(owners) >= 2 and pt not in via_pts)
            # union-find（节点序=sorted，确定性）
            parent = {}

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(x, y):
                rx, ry = find(x), find(y)
                if rx != ry:
                    parent[max(rx, ry)] = min(rx, ry)

            def node(k):
                if k not in parent:
                    parent[k] = k
                return k

            for u, v in edges:
                union(node(u), node(v))
            for pt in sorted(via_pts):
                via_node = node((pt, "via"))
                for seg in net_segs:
                    if any(tuple(p) == pt for p in seg["grid"]):
                        union(via_node, node((pt, seg["shape_id"])))
                for tun in net_tuns:
                    if any(tuple(p) == pt for p in tun["grid"]):
                        union(via_node, node((pt, tun["shape_id"])))
            for pt in sorted(term_set):
                term_node = node((pt, "term"))
                for seg in net_segs:
                    path = [tuple(p) for p in seg["grid"]]
                    if path[0] == pt or path[-1] == pt:
                        union(term_node, node((pt, seg["shape_id"])))
            routed = False
            if terminals and not dangling and edges:
                roots = {find((pt, "term")) for pt in term_set}
                routed = len(roots) == 1 and all(
                    (pt, "term") in parent for pt in term_set)
            self.connectivity[nid] = routed
            self.chain_detail[nid] = {
                "routed": routed,
                "terminals": sorted([list(pt) for pt in term_set]),
                "segs": len(net_segs),
                "vias": len(via_pts),
                "tunings": len(net_tuns),
                "dangling_segs": sorted(dangling),
                "junctions_missing_via": [list(pt) for pt in junctions_no_via],
            }

    def routed_nets(self):
        return sum(1 for k in sorted(self.connectivity)
                   if self.connectivity[k])

    # ---------- 序列化（facts=canonical dict；列表排序构建） ----------

    def facts(self):
        return state_facts(self)

    def sha256(self):
        return state_sha256(self)


def state_facts(st):
    """画板事实 dict（canonical_json 可直落；确定性：键序交 canonical_json，
    列表序在此按 shape_id/net_id/partition_id 排序钉死）。"""
    return {
        "canvas_version": "canvas-state/0.3.0",
        "anchor_semantics": "v2",
        "board_id": st.board["board_id"],
        "board_path": st.board_path,
        "board_sha256": st.board_sha256,
        "lattice": st.lattice.as_dict(),
        "anchors": {pid: [list(a) for a in st.anchors[pid]]
                    for pid in sorted(st.anchors)},
        "seg_seq": st._seg_seq,
        "tun_seq": {net: dict(st._tun_seq.get(net, {}))
                    for net in sorted(st._tun_seq)},
        "segs": [dict(st.segs[sid]) for sid in sorted(st.segs)],
        "vias": [dict(st.vias[sid]) for sid in sorted(st.vias)],
        "tunings": [dict(st.tunings[sid]) for sid in sorted(st.tunings)],
        "widths": {net: st.widths[net] for net in sorted(st.widths)},
        "placements": {pid: {"move": (list(cov["move"])
                                      if cov["move"] is not None else None),
                             "rotate": cov["rotate"], "flip": cov["flip"]}
                       for pid, cov in sorted(st.placements.items())},
        "connectivity": {net: st.connectivity[net]
                         for net in sorted(st.connectivity)},
        "chain_detail": {net: st.chain_detail.get(net, {})
                         for net in sorted(st.connectivity)
                         if net in st.chain_detail},
    }


def state_sha256(st):
    """链式台账锚（v5.canonical 同源；facts 字节等的哈希）。"""
    from v5 import canonical
    return canonical.canonical_sha256(state_facts(st))
