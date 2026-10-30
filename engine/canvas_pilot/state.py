# -*- coding: utf-8 -*-
"""state —— 画板状态（canonical JSON: 板引用+lattice+每网已落铜+违例清单+连通账本）。

- canonical 序列化复用 v5.canonical（canonical_json/canonical_sha256）。
- 图元: seg（单层折线, 格点 waypoints; 端点锚↔真实端点 stub 由 instantiate
  派生不落盘）/ via（格点孔）。shape_id 稳定寻址（ripup 消费）。
- 连通账本（引擎 v5.route_check 网级链审计同语义）: 首段首点=分区端点锚、
  末段末点=另一端点锚、相邻段在 via 格点衔接（跨层过渡孔=衔接点，画板统一
  纪律: 段衔接点必须有 via 在场）。
"""
import copy

from . import lattice as _lattice


def _seg_shape_id(net_id, seq):
    return "seg:%s:%d" % (net_id, seq)


def _via_shape_id(net_id, i, j):
    return "via:%s:%d_%d" % (net_id, i, j)


class CanvasState(object):
    """画板可变状态。board/lattice/anchors 为构造期冻结引用（画板垄断）。"""

    def __init__(self, board, board_path, board_sha256, lat, anchors):
        self.board = board
        self.board_path = board_path
        self.board_sha256 = board_sha256
        self.lattice = lat
        self.anchors = anchors            # partition_id -> [[i,j],[i,j]]
        self.segs = []                    # [{shape_id,net_id,partition_id,layer,grid:[[i,j],..]}]
        self.vias = []                    # [{shape_id,net_id,grid:[i,j]}]
        self._seg_seq = 0
        # 连通账本快照（每次变更后重算; routed=存在端到端链）
        self.connectivity = {n["net_id"]: False for n in board["nets"]}
        self.chain_detail = {}

    # ---------- 引用视图 ----------

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

    def board_endpoint_mm(self, pid):
        for p in self.board["partitions"]:
            if p["partition_id"] == pid:
                return [(float(e[0]), float(e[1]))
                        for e in p["geometry"]["endpoints"]]
        raise KeyError(pid)

    def signal_layers(self):
        return [s["id"] for s in self.board["stackup"]
                if s.get("kind") == "signal" and s.get("available") is True]

    def via_grids(self, net_id):
        return {tuple(v["grid"]) for v in self.vias if v["net_id"] == net_id}

    # ---------- 变更 ----------

    def add_seg(self, net_id, partition_id, layer, grid):
        shape_id = _seg_shape_id(net_id, self._seg_seq)
        self._seg_seq += 1
        seg = {"shape_id": shape_id, "net_id": net_id,
               "partition_id": partition_id, "layer": layer,
               "grid": [list(p) for p in grid]}
        self.segs.append(seg)
        return seg

    def add_via(self, net_id, grid):
        i, j = grid
        shape_id = _via_shape_id(net_id, i, j)
        via = {"shape_id": shape_id, "net_id": net_id, "grid": [i, j]}
        self.vias.append(via)
        return via

    def remove_shape(self, shape_id):
        before = len(self.segs) + len(self.vias)
        self.segs = [s for s in self.segs if s["shape_id"] != shape_id]
        self.vias = [v for v in self.vias if v["shape_id"] != shape_id]
        return len(self.segs) + len(self.vias) < before

    def remove_net(self, net_id):
        self.segs = [s for s in self.segs if s["net_id"] != net_id]
        self.vias = [v for v in self.vias if v["net_id"] != net_id]

    def gc_dangling_vias(self):
        """清除不在任何本网段 waypoint 上的 via（ripup 段后的悬空孔）。"""
        keep = []
        for v in self.vias:
            on_path = any(
                any(tuple(p) == tuple(v["grid"]) for p in s["grid"])
                for s in self.segs if s["net_id"] == v["net_id"])
            if on_path:
                keep.append(v)
        removed = len(self.vias) - len(keep)
        self.vias = keep
        return removed

    # ---------- 连通账本 ----------

    def recompute_connectivity(self):
        """链审计（v5.route_check 网级链审计同语义的格点版）。

        段附着点: 首/末格点 ∈ {端点锚A, 锚B} ∪ 本网 via 格点。
        连通=图上锚A 到锚B 有路径（段=边, via=衔接节点, 锚=端节点）。"""
        self.connectivity = {n["net_id"]: False for n in self.board["nets"]}
        self.chain_detail = {}
        for n in self.board["nets"]:
            nid = n["net_id"]
            pids = n["partitions"]
            if len(pids) != 1:
                continue  # 试点人口每网单分区（badgeleds/pmod-bme280 均如此）
            pid = pids[0]
            a0, a1 = tuple(self.anchors[pid][0]), tuple(self.anchors[pid][1])
            vias = self.via_grids(nid)
            attach = lambda g: (tuple(g) in (a0, a1)) or (tuple(g) in vias)
            edges = []
            for s in self.segs:
                if s["net_id"] != nid or len(s["grid"]) < 2:
                    continue
                h, t = tuple(s["grid"][0]), tuple(s["grid"][-1])
                if not (attach(h) and attach(t)):
                    continue  # 悬空段不入边（链存在即连通, 引擎链审计同语义）
                edges.append((h, t, s["shape_id"]))
            if not edges:
                continue
            # BFS: a0 → a1（节点=格点元组）
            adj = {}
            for h, t, _sid in edges:
                adj.setdefault(h, []).append(t)
                adj.setdefault(t, []).append(h)
            seen = {a0}
            frontier = [a0]
            found = False
            while frontier and not found:
                nxt = []
                for u in frontier:
                    for w in adj.get(u, ()):
                        if w == a1:
                            found = True
                            break
                        if w not in seen:
                            seen.add(w)
                            nxt.append(w)
                    if found:
                        break
                frontier = nxt
            self.connectivity[nid] = found
            self.chain_detail[nid] = {"routed": found, "segs": len(edges),
                                      "vias": len(vias)}

    def routed_nets(self):
        return sum(1 for v in self.connectivity.values() if v)

    # ---------- 序列化 ----------

    def as_dict(self):
        return {
            "canvas_version": "canvas-state/0.1.0",
            "board_path": self.board_path,
            "board_sha256": self.board_sha256,
            "board_id": self.board["board_id"],
            "lattice": self.lattice.as_dict(),
            "anchors": {k: v for k, v in sorted(self.anchors.items())},
            "seg_seq": self._seg_seq,
            "segs": [dict(s) for s in self.segs],
            "vias": [dict(v) for v in self.vias],
            "connectivity": {k: self.connectivity[k]
                             for k in sorted(self.connectivity)},
            "last_rejections": list(getattr(self, "last_rejections", [])),
        }

    @classmethod
    def from_dict(cls, d, board):
        st = cls.__new__(cls)
        st.board = board
        st.board_path = d["board_path"]
        st.board_sha256 = d["board_sha256"]
        st.lattice = _lattice.Lattice.from_dict(d["lattice"])
        st.anchors = {k: [list(a) for a in v]
                      for k, v in d["anchors"].items()}
        st.segs = [dict(s) for s in d["segs"]]
        st.vias = [dict(v) for v in d["vias"]]
        st._seg_seq = d["seg_seq"]
        st.connectivity = dict(d["connectivity"])
        st.chain_detail = {}
        st.last_rejections = list(d.get("last_rejections", []))
        return st

    def snapshot_for_hash(self):
        """链式哈希用状态摘要（canonical; 不含 board 引用本身——board_sha
        已锚定板身份）。"""
        d = copy.deepcopy(self.as_dict())
        return d
