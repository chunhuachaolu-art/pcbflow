# -*- coding: utf-8 -*-
"""Lane-M4 测试共享夹具（test_m4_* 族）。

- pc_board(): **placecheck 自有夹具**=合成 pad 场矩阵（最小 board dict
  消费面，不经 v5.board 校验——placecheck 是新 validator、非 v5.drc 绑定，
  夹具只钉 pad 场几何，两分区/三分区阵可控触发各 verdict 码）。
- blocked_state(): 中线堵塞合成微板（v5.board.load_board 全校验+哈希链，
  合同内 board.v1 形态）——PA↔PB 中心走廊被 PC2 堵塞，M4 runner 在此板
  存在确定性 score 改善（接受路径夹具）。
"""
import copy

from v5 import board as v5board

from canvas import state as cst
from canvas.tests.test_k1_fixtures import synth_state


def pc_board(parts, ws=(0.0, 0.0, 20.0, 12.0), r5=0.5):
    """合成 pad 场矩阵 board dict（placecheck/referee 自有夹具）。

    parts: [(pid, net_id, ((x0,y0),(x1,y1)) 端点 mm,
             [(w,h) ep0 pad 尺寸, (w,h) ep1 pad 尺寸])]——pad 全 rect
    （外接矩形=pad 自身矩形，直接控形）; 单元素尺寸=circle 外接方。
    无 stackup（Lattice/placecheck/referee 只消费 workspace/partitions/
    nets/hard_rules 面）。"""
    partitions = []
    nets = {}
    for pid, net, eps, sizes in parts:
        partitions.append({
            "partition_id": pid, "ptype": "MISC", "current_a": 0,
            "speed_class": "unknown", "layer_policy": "any",
            "width_prior": {"w_min": 0.3, "w_max": 0.8},
            "geometry": {
                "endpoints": [[float(e[0]), float(e[1])] for e in eps],
                "pad_terminals": [
                    {"endpoint": k,
                     "shape": "circle" if len(sizes[k]) == 1 else "rect",
                     "size_mm": [float(s) for s in sizes[k]], "layers": "all"}
                    for k in (0, 1)]}})
        nets.setdefault(net, []).append(pid)
    return {
        "partitions": partitions,
        "nets": [{"net_id": n, "partitions": pids}
                 for n, pids in sorted(nets.items())],
        "hard_rules": {"R5": {"min_clearance_mm": float(r5)}},
        "workspace": {"x_min": ws[0], "y_min": ws[1],
                      "x_max": ws[2], "y_max": ws[3]},
    }


def pc_lattice(board):
    return cst.Lattice.from_board(board)


def blocked_state():
    """中线堵塞微板: PC2 端点移至 (5,5)-(7,5)（堵在 PA↔PB 中心走廊列
    x=6mm 上）——run_m4 存在确定性改善（PA/PB 让出走走廊列）。"""
    base = synth_state()
    raw = copy.deepcopy(base.board)
    for p in raw["partitions"]:
        if p["partition_id"] == "PC2":
            p["geometry"]["endpoints"] = [[5.0, 5.0], [7.0, 5.0]]
    raw["provenance"]["board_sha256"] = v5board.compute_board_sha256(raw)
    board = v5board.load_board(raw)     # fail-closed 自证（schema+哈希链）
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(board, "<synth-m4-blocked>",
                         board["provenance"]["board_sha256"], lat,
                         cst.anchor_map(board, lat))
    st.recompute_connectivity()
    return st
