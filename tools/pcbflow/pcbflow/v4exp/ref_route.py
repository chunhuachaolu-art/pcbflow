"""V4exp 玩具构造式参考布线器（给 E0 提供带 route 的 fixture，不是 E1 求解器）。

口径（与派发合同一致，实现细化处在本 docstring 声明）：
- 0.5mm 格点；按 net_id 顺序布线；clock 走 F.Cu，其余先 F.Cu、被挡且下一格
  在 B.Cu 空闲时换层放 via（单次 F->B，若终点仍在 B.Cu 则在倒数第 2 格放
  回层 via，末段留 >= 0.5mm F.Cu 短茬；不在最后一步换层）。
- 路径候选 <= 3 段 Manhattan，按确定序尝试：先 x 后 y（XY）、先 y 后 x
  （YX）、XYX（中竖扫描）、YXY（中横扫描，从两端中点向两侧 ±0.5mm 步进
  至 ±10mm）；首个可行者胜。
- 占用检查：格点被其他 net 的 pad 外扩（Chebyshev 1 格 = 0.5mm）或已布
  路线外扩（同）或 keepout 占用则禁行；不同 net 中心线间隔保守取 2 格
  = 1.0mm（对 clearance 0.3 + 2x半宽 0.3/0.4 的最坏组合 0.7/0.8mm 保守），
  constraint_refs 口径统一为 C-clearance-030 + C-width-030/040。
- 换层处 route 对象断开：每个同层折线段一个 route；via 的 parent_id 取
  换层前那段。
- 某 net 全部候选失败则记入 unrouted_net_ids；任一失败则场景级
  reference_unrouted = true（f5 预期为 true）。

stdin 收 {"board_path": "...", "out_dir": "..."}（相对路径）；
写 ref-routes-<scenario_id>.json，stdout 打印摘要 JSON。零 argv。
"""

from __future__ import annotations

import os

from . import model
from .model import Board, Net, mm

STEP = 0.5


def _cells_along(pts):
    """角点序列（同轴相邻）展开为逐格 cell 序列（含首尾）。"""
    cells = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        dx = (b[0] > a[0]) - (b[0] < a[0])
        dy = (b[1] > a[1]) - (b[1] < a[1])
        c = a
        while c != b:
            c = (c[0] + dx, c[1] + dy)
            cells.append(c)
    return cells


def _compress(cells):
    """逐格序列压缩回角点序列（合同 polyline_mm 只存拐点）。"""
    if len(cells) <= 2:
        return list(cells)
    out = [cells[0]]
    for i in range(1, len(cells) - 1):
        ax, ay = out[-1]
        bx, by = cells[i]
        cx, cy = cells[i + 1]
        if (bx - ax) * (cy - by) != (by - ay) * (cx - bx):
            out.append(cells[i])  # 方向改变 → 拐点
    out.append(cells[-1])
    return out


class _Router:
    def __init__(self, board: Board):
        self.board = board
        self.x0, self.y0 = board.bbox_mm[0], board.bbox_mm[1]
        self.nx = int(round((board.bbox_mm[2] - self.x0) / STEP))
        self.ny = int(round((board.bbox_mm[3] - self.y0) / STEP))
        self.ko = {L: set() for L in board.layers}
        for k in board.keepouts:
            for L in k.layers:
                self.ko[L] |= self._rect_cells(k.rect_mm)
        self.occupied = {L: set() for L in board.layers}
        self.pad_cell = {p.pad_id: self.cell_of(p.x_mm, p.y_mm)
                         for p in board.pads}

    # ---- 坐标
    def cell_of(self, x, y):
        return (int(round((x - self.x0) / STEP)),
                int(round((y - self.y0) / STEP)))

    def cell_mm(self, c):
        return [mm(self.x0 + c[0] * STEP), mm(self.y0 + c[1] * STEP)]

    def in_bounds(self, c):
        return 0 <= c[0] <= self.nx and 0 <= c[1] <= self.ny

    def _rect_cells(self, rect):
        ix0 = max(0, int(round((rect[0] - self.x0) / STEP)))
        ix1 = min(self.nx, int(round((rect[2] - self.x0) / STEP)))
        iy0 = max(0, int(round((rect[1] - self.y0) / STEP)))
        iy1 = min(self.ny, int(round((rect[3] - self.y0) / STEP)))
        return {(i, j) for i in range(ix0, ix1 + 1)
                for j in range(iy0, iy1 + 1)}

    @staticmethod
    def _halo(c):
        return [(c[0] + dx, c[1] + dy)
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

    # ---- 占用
    def blocked_for(self, net: Net) -> dict:
        blk = {L: (self.ko[L] | self.occupied[L]) for L in self.board.layers}
        for p in self.board.pads:
            if p.net_id == net.net_id or p.pad_id not in self.pad_cell:
                continue
            blk[p.layer] |= set(self._halo(self.pad_cell[p.pad_id]))
        return blk

    def free(self, c, layer, blk):
        return self.in_bounds(c) and c not in blk[layer]

    # ---- 候选路径（确定序）
    def _mid_sweep(self, a, b, lo, hi):
        m = (a + b) // 2
        out = []
        for d in range(0, 21):
            for v in ((m + d, m - d) if d else (m,)):
                if lo <= v <= hi and v not in out:
                    out.append(v)
        return out

    def candidates(self, s, t):
        sx, sy = s
        tx, ty = t
        yield [s, t] if (sx == tx or sy == ty) else [s, (tx, sy), t]
        if not (sx == tx or sy == ty):
            yield [s, (sx, ty), t]
        for mx in self._mid_sweep(sx, tx, 0, self.nx):
            if mx != sx and mx != tx:
                yield [s, (mx, sy), (mx, ty), t]
        for my in self._mid_sweep(sy, ty, 0, self.ny):
            if my != sy and my != ty:
                yield [s, (sx, my), (tx, my), t]

    # ---- 走线（含换层）
    def walk(self, net: Net, pts, blk, allowed, pad_layer):
        cells = _cells_along(pts)
        base = self.board.layers[0]
        alt = self.board.layers[1] if len(allowed) > 1 else None
        cur = base
        switched = False
        runs = [[cells[0]]]
        run_layers = [cur]
        vias = []  # (cell, from_layer, to_layer, 换层前 run 下标)
        for idx in range(1, len(cells)):
            nxt = cells[idx]
            if self.free(nxt, cur, blk):
                runs[-1].append(nxt)
                continue
            last = idx == len(cells) - 1
            if (alt is not None and cur == base and not switched
                    and not last
                    and self.free(runs[-1][-1], alt, blk)
                    and self.free(nxt, alt, blk)):
                via_cell = runs[-1][-1]
                vias.append((via_cell, cur, alt, len(runs) - 1))
                runs.append([via_cell, nxt])
                run_layers.append(alt)
                cur = alt
                switched = True
                continue
            return None
        if cur != pad_layer:
            run = runs[-1]
            if len(run) < 3:
                return None
            via_cell = run[-2]
            if not self.free(via_cell, pad_layer, blk):
                return None
            runs[-1] = run[:-1]
            vias.append((via_cell, cur, pad_layer, len(runs) - 1))
            runs.append([via_cell, run[-1]])
            run_layers.append(pad_layer)
        return runs, run_layers, vias

    def route_net(self, net: Net):
        sp = self.board.pad_by_id(net.endpoints[0])
        tp = self.board.pad_by_id(net.endpoints[1])
        if sp is None or tp is None:
            return None
        s = self.pad_cell[sp.pad_id]
        t = self.pad_cell[tp.pad_id]
        blk = self.blocked_for(net)
        allowed = self.board.net_allowed_layers(net.net_class)
        for pts in self.candidates(s, t):
            res = self.walk(net, pts, blk, allowed, sp.layer)
            if res is not None:
                runs, run_layers, vias = res
                # 占用登记：路线外扩 Chebyshev 1 格；via 双层登记
                for run, L in zip(runs, run_layers):
                    for c in run:
                        self.occupied[L] |= set(self._halo(c))
                for via_cell, fl, tl, _ in vias:
                    for c in self._halo(via_cell):
                        self.occupied[fl].add(c)
                        self.occupied[tl].add(c)
                return runs, run_layers, vias
        return None


# ---------------------------------------------------------------- 组装

def _line_type(board: Board, net: Net) -> str:
    if net.net_class == "clock":
        return "clock"
    for r in board.relations:
        if r.relation_type == "bus" and net.net_id in r.members:
            return "bus_member"
    return "signal"


def route_board(board: Board) -> dict:
    router = _Router(board)
    routes = []
    vias = []
    unrouted = []
    seg_n = {}
    via_n = {}
    clearance = board.rules.clearance_mm
    for net in board.nets:
        res = router.route_net(net)
        width = board.net_class_width(net.net_class)
        refs = [model.constraint_ref("clearance", clearance),
                model.constraint_ref("width", width)]
        rel_ids = board.relation_ids_of_net(net.net_id)
        endpoints = list(net.endpoints)
        if res is None:
            unrouted.append(net.net_id)
            continue
        runs, run_layers, run_vias = res
        rid_by_idx = []
        for run, layer in zip(runs, run_layers):
            k = seg_n.get(net.net_id, 0) + 1
            seg_n[net.net_id] = k
            rid = f"{net.net_id}-S{k:02d}"
            rid_by_idx.append(rid)
            routes.append({
                "route_id": rid, "svg_id": f"route-{rid}",
                "net_id": net.net_id, "relation_ids": list(rel_ids),
                "line_type": _line_type(board, net), "parent_id": None,
                "layer": layer, "width_mm": width,
                "polyline_mm": [router.cell_mm(c) for c in _compress(run)],
                "endpoint_ids": endpoints, "constraint_refs": refs,
                "state": "baseline", "source": "generator"})
        for via_cell, fl, tl, seg_idx in run_vias:
            m = via_n.get(net.net_id, 0) + 1
            via_n[net.net_id] = m
            vid = f"{net.net_id}-V{m:02d}"
            vias.append({
                "via_id": vid, "net_id": net.net_id,
                "parent_id": rid_by_idx[seg_idx],
                "from_layer": fl, "to_layer": tl,
                "center_mm": router.cell_mm(via_cell),
                "drill_mm": board.rules.via.hole_mm,
                "annular_ring_mm": mm((board.rules.via.pad_mm
                                       - board.rules.via.hole_mm) / 2)})
    return {"scenario_id": board.scenario_id,
            "reference_unrouted": bool(unrouted),
            "unrouted_net_ids": unrouted,
            "routes": routes, "vias": vias}


def main() -> None:
    import json as _json
    import sys
    cfg = model.read_stdin_json()
    board = model.board_from_obj(model.read_json(cfg["board_path"]))
    ref = route_board(board)
    out_dir = cfg.get("out_dir") or "out/v4-experiment"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"ref-routes-{board.scenario_id}.json")
    model.write_json(path, ref)
    sys.stdout.write(_json.dumps(
        {"scenario_id": board.scenario_id, "path": path.replace("\\", "/"),
         "routes": len(ref["routes"]), "vias": len(ref["vias"]),
         "reference_unrouted": ref["reference_unrouted"]},
        sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
