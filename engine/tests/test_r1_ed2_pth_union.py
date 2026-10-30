# -*- coding: utf-8 -*-
"""V5-R1 W-6 ED-2 修复钉（route_check 0.4.1 PTH 孔筒 union）——用户四裁
裁 2 口径（2026-09-26）：跨层多端网合成场景（≥2 信号层+≥3 端+分支点经
PTH 焊盘异层触及=正钉过审；NPTH 同形态=fail-closed 仍崩钉）。

场景：3 端网双信号层，T0 边 F.Cu 收于 pad2、T1 边 B.Cu 起于 pad2（分支点
异层衔接、无 transition_via）——电气连通由 thru_hole pad 孔筒承担（KiCad
通孔焊盘语义：plated 孔筒沉铜连通所有铜层）。0.4.1 前=审计假阴性（真连
通判断链，crypto +3V3 ED-2 崩点同款形态）。
"""
import copy
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import board as board_mod
from v5.adapters.kicad_adapter import convert_bytes_with_report
from v5.route_check import ROUTE_CHECK_VERSION, RouteCheckError, validate_routes

# 3 端 thru_hole 网（双信号层）；pad 坐标 (10,10)/(18,10)/(10,18)。
PTH_PCB = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.0)-1")
  (general (thickness 1.6))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 SIG3)
  (module M:FP1 (layer F.Cu) (at 10 10 0)
    (pad 1 thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
    (pad 2 thru_hole circle (at 8 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
    (pad 3 thru_hole circle (at 0 8) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
  )
  (gr_line (start 0 0) (end 60 0) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 60 0) (end 60 30) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 60 30) (end 0 30) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 0 30) (end 0 0) (layer Edge.Cuts) (width 0.05))
)
"""


def _board():
    board, report = convert_bytes_with_report(
        PTH_PCB.encode("utf-8"), "pth-pin", "test://pth-pin")
    return board, report


def _pid3(board):
    return [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]


def _doc(board, entries):
    sha = board_mod.compute_board_sha256(board)
    return {
        "schema_version": "v5.routes.v1",
        "board_id": board["board_id"],
        "board_sha256": sha,
        "negotiation_log": [],
        "provenance": {"generator": "test-ed2-pth-pin", "board_sha256": sha},
        "routes": entries,
    }


def _entry(pid, layer, polyline, te):
    return {"partition_id": pid, "net_id": "SIG3", "layer": layer,
            "polyline": polyline, "width": 0.2,
            "transition_vias": [], "return_vias": [], "topology_edge": te}


def _cross_layer_entries(board):
    """T0: p1→p2（F.Cu）；T1: p2→p3（B.Cu）——分支点 p2 异层衔接无孔。"""
    pid = _pid3(board)
    eps = next(p for p in board["partitions"]
               if p["partition_id"] == pid)["geometry"]["endpoints"]
    return [_entry(pid, "F.Cu", [list(eps[0]), list(eps[1])], "T0"),
            _entry(pid, "B.Cu", [list(eps[1]), list(eps[2])], "T1")]


def _holes_at(board):
    return {(round(h["pos_mm"][0], 6), round(h["pos_mm"][1], 6)): h
            for h in board["holes"]}


def test_version_disclosure():
    assert ROUTE_CHECK_VERSION == "v5.route_check/0.5.0"  # V5-R7 同步


def test_cross_layer_pth_branch_point_passes():
    """正钉：分支点经 PTH 焊盘（plated=true）异层触及=过审（孔筒连通）。"""
    board, _ = _board()
    pid = _pid3(board)
    eps = next(p for p in board["partitions"]
               if p["partition_id"] == pid)["geometry"]["endpoints"]
    assert len(board["topology"][pid]["edges"]) == 2   # 3 端 2 边
    holes_at = _holes_at(board)
    # 钉前提：3 端 thru_hole pad 孔全量入 board.holes 且 plated=true（D8 面）
    for pt in eps:
        h = holes_at[(round(pt[0], 6), round(pt[1], 6))]
        assert h["plated"] is True
    assert validate_routes(board, _doc(board, _cross_layer_entries(board)))


def test_cross_layer_npth_same_shape_still_fail_closed():
    """负钉：NPTH 同形态=fail-closed 仍崩（非镀孔筒不承担层间连通）。"""
    board, _ = _board()
    pid = _pid3(board)
    eps = next(p for p in board["partitions"]
               if p["partition_id"] == pid)["geometry"]["endpoints"]
    p2 = (round(eps[1][0], 6), round(eps[1][1], 6))
    b2 = copy.deepcopy(board)
    _holes_at(b2)[p2]["plated"] = False
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(b2, _doc(b2, _cross_layer_entries(b2)))
    assert "2 个连通分量" in str(ei.value)


def test_cross_layer_no_hole_same_shape_still_fail_closed():
    """负钉：分支点无孔同形态=仍崩（对照面：union 仅由 plated 孔触发）。"""
    board, _ = _board()
    pid = _pid3(board)
    eps = next(p for p in board["partitions"]
               if p["partition_id"] == pid)["geometry"]["endpoints"]
    p2 = (round(eps[1][0], 6), round(eps[1][1], 6))
    b3 = copy.deepcopy(board)
    b3["holes"] = [h for h in b3["holes"]
                   if (round(h["pos_mm"][0], 6), round(h["pos_mm"][1], 6)) != p2]
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(b3, _doc(b3, _cross_layer_entries(b3)))
    assert "2 个连通分量" in str(ei.value)


def test_transition_via_form_still_passes_without_pth():
    """对照正钉：同跨层形态经 transition_vias 披露=过审（既有 ③ 语义不动）。"""
    board, _ = _board()
    pid = _pid3(board)
    eps = next(p for p in board["partitions"]
               if p["partition_id"] == pid)["geometry"]["endpoints"]
    b4 = copy.deepcopy(board)
    b4["holes"] = []   # 摘掉全部孔：仅靠 transition_vias 跨层
    entries = _cross_layer_entries(b4)
    p2 = [float(eps[1][0]), float(eps[1][1])]
    for e in entries:
        if e["polyline"][-1] == p2 or e["polyline"][0] == p2:
            e["transition_vias"] = [p2]
    assert validate_routes(b4, _doc(b4, entries))
