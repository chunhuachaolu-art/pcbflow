# -*- coding: utf-8 -*-
"""V5-R1 W-2/W-3/W-4 集成单测：adapter 全 pad 质心集+topology 落键+executor
逐拓扑边布线+route_check 拓扑审计。

合成多端网板（3/5 端钉值）；既有 2 端网行为面（endpoints 序=出现序去重）
与旧「最远两端」口径的差异面单独钉（W-2 翻转披露的测试侧锚）。
"""
import json

import pytest

from v5.adapters.kicad_adapter import (AdapterError, convert_bytes_with_report,
                                       convert_bytes)
from v5.board import load_board
from v5.executor import execute_candidate
from v5.planner import plan_candidates
from v5.steiner import steiner_topology

# 合成多端网板：3 pad 网 SIG3（多点）+2 pad 网 SIG2（对照）+单 pad 网 ONE。
MULTI_PCB = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.0)-1")
  (general (thickness 1.6))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 SIG3)
  (net 2 SIG2)
  (net 3 ONE)
  (module M:FP1 (layer F.Cu) (at 10 10 0)
    (pad 1 thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
    (pad 2 thru_hole circle (at 8 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
    (pad 3 thru_hole circle (at 0 8) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 SIG3))
  )
  (module M:FP2 (layer F.Cu) (at 30 10 0)
    (pad 1 thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 2 SIG2))
    (pad 2 thru_hole circle (at 0 8) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 2 SIG2))
  )
  (module M:FP3 (layer F.Cu) (at 50 10 0)
    (pad 1 smd rect (at 0 0) (size 1.5 1.5) (layers F.Cu) (net 3 ONE))
  )
  (gr_line (start 0 0) (end 60 0) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 60 0) (end 60 30) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 60 30) (end 0 30) (layer Edge.Cuts) (width 0.05))
  (gr_line (start 0 30) (end 0 0) (layer Edge.Cuts) (width 0.05))
)
"""


def _board():
    board, report = convert_bytes_with_report(
        MULTI_PCB.encode("utf-8"), "multi-demo", "test://multi")
    return board, report


def test_adapter_full_pad_centroids_and_topology():
    board, report = _board()
    parts = {p["partition_id"]: p for p in board["partitions"]}
    by_net = {}
    for n in board["nets"]:
        by_net[n["net_id"]] = parts[n["partitions"][0]]
    # W-2：多点网不折叠——SIG3=3 端（出现序），SIG2=2 端，ONE=退化两点重合
    eps3 = by_net["SIG3"]["geometry"]["endpoints"]
    assert len(eps3) == 3
    assert eps3 == [[10.0, 10.0], [18.0, 10.0], [10.0, 18.0]]
    assert len(by_net["SIG2"]["geometry"]["endpoints"]) == 2
    one = by_net["ONE"]["geometry"]["endpoints"]
    assert one[0] == one[1] == [50.0, 10.0]
    # pad_terminals 逐 pad 化：SIG3=3 项 endpoint=0/1/2
    pt3 = by_net["SIG3"]["geometry"]["pad_terminals"]
    assert [t["endpoint"] for t in pt3] == [0, 1, 2]
    # W-3：topology 恒落键（全分区）
    topo = board["topology"]
    assert set(topo) == set(parts)
    t3 = topo[by_net["SIG3"]["partition_id"]]
    assert t3["terminal_count"] == 3
    assert t3["provenance"]["algorithm"].startswith("v5.steiner/")
    assert t3["provenance"]["method"] in ("pot-table", "pot-miss-exact-dw",
                                          "exact-dw")
    # 拓扑=树（3 端 2 边；Steiner 点 (1,?) 形：L 形树=(10,10)-(18,10)-(10,18)
    # 的 RSMT：Steiner (10,10)? 由 steiner_topology 决定——钉 tree 合同）
    assert len(t3["edges"]) == len(t3["nodes"]) - 1
    # 报告键
    assert report["topology"]["multi_terminal_nets"] == 1
    load_board(board)  # schema 复验（含 topology 键）


def test_topology_matches_steiner_module():
    board, _ = _board()
    parts = {p["partition_id"]: p for p in board["partitions"]}
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    eps = [tuple(p) for p in parts[pid3]["geometry"]["endpoints"]]
    want = steiner_topology(eps)
    got = board["topology"][pid3]
    assert got["nodes"] == [[float(x), float(y)] for x, y in want["nodes"]]
    assert got["edges"] == want["edges"]


def test_execute_multi_terminal_net_routes():
    board, _ = _board()
    cands = plan_candidates(board, _artifact_stub(board)) if False else None
    # plan_candidates 需要 compiled artifact——合成面直接手工构造候选
    pids = sorted(p["partition_id"] for p in board["partitions"])
    candidate = {
        "candidate_id": "C-001",
        "arm": "no-principle",
        "provenance": {"generator": "test", "rules_consumed": [],
                       "compiled_sha256": "0" * 64},
        "route_order": list(pids),
        "layer_assignment": {pid: "F.Cu" for pid in pids},
        "polylines": {pid: [list(pt) for pt in
                            next(p for p in board["partitions"]
                                 if p["partition_id"] == pid)
                            ["geometry"]["endpoints"]]
                      for pid in pids},
        "generation_trace": [],
    }
    result = execute_candidate(board, candidate)
    assert result["verdict"] == "ROUTED", result["negotiation_log"][-5:]
    routes = result["routes"]["routes"]
    # 多端网 entry 全带 topology_edge 且 T* 恰覆盖
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    e3 = [e for e in routes if e["partition_id"] == pid3]
    topo = board["topology"][pid3]
    assert {e["topology_edge"] for e in e3} == \
        {"T%d" % k for k in range(len(topo["edges"]))}
    # 2 端网单边 T0；退化网零长 entry 无 topology_edge
    pid2 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG2"][0]
    e2 = [e for e in routes if e["partition_id"] == pid2]
    assert {e.get("topology_edge") for e in e2} == {"T0"}
    pid1 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "ONE"][0]
    e1 = [e for e in routes if e["partition_id"] == pid1]
    assert len(e1) == 1 and e1[0]["polyline"][0] == e1[0]["polyline"][-1]
    assert "topology_edge" not in e1[0]
    # 确定性双跑
    result2 = execute_candidate(board, candidate)
    assert result2["routes"] == result["routes"]


def _artifact_stub(board):  # pragma: no cover（占位防误用）
    return None


def test_execute_topology_hints_channel():
    """W-5 通道口：edge_order 软先验（permutation 合法消费；非法 fail-closed）。"""
    board, _ = _board()
    pids = sorted(p["partition_id"] for p in board["partitions"])
    candidate = {
        "candidate_id": "C-001", "arm": "no-principle",
        "provenance": {"generator": "test", "rules_consumed": [],
                       "compiled_sha256": "0" * 64},
        "route_order": list(pids),
        "layer_assignment": {pid: "F.Cu" for pid in pids},
        "polylines": {pid: [list(pt) for pt in
                            next(p for p in board["partitions"]
                                 if p["partition_id"] == pid)
                            ["geometry"]["endpoints"]] for pid in pids},
        "generation_trace": [],
    }
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    topo = board["topology"][pid3]
    order = ["T%d" % k for k in reversed(range(len(topo["edges"])))]
    r1 = execute_candidate(board, candidate,
                           topology_hints={pid3: {"edge_order": order}})
    assert r1["verdict"] == "ROUTED"
    assert any("topology-hints consumed" in line
               for line in r1["negotiation_log"])
    # 非法先验（非 permutation）fail-closed
    with pytest.raises(Exception):
        execute_candidate(board, candidate,
                          topology_hints={pid3: {"edge_order": ["T9"]}})


def test_multi_point_without_topology_fail_closed():
    board, _ = _board()
    board = json.loads(json.dumps(board))  # deep copy
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    del board["topology"][pid3]
    pids = sorted(p["partition_id"] for p in board["partitions"])
    candidate = {
        "candidate_id": "C-001", "arm": "no-principle",
        "provenance": {"generator": "test", "rules_consumed": [],
                       "compiled_sha256": "0" * 64},
        "route_order": list(pids),
        "layer_assignment": {pid: "F.Cu" for pid in pids},
        "polylines": {pid: [list(pt) for pt in
                            next(p for p in board["partitions"]
                                 if p["partition_id"] == pid)
                            ["geometry"]["endpoints"]] for pid in pids},
        "generation_trace": [],
    }
    with pytest.raises(Exception, match="topology"):
        execute_candidate(board, candidate)


# -------------------------------- V5-R1 W-6 修正 ED-1：同边多段审计口径

def _routed_doc():
    """execute_candidate 成功 routes doc（SIG3/SIG2/ONE 三网合成板）。"""
    board, _ = _board()
    pids = sorted(p["partition_id"] for p in board["partitions"])
    candidate = {
        "candidate_id": "C-001", "arm": "no-principle",
        "provenance": {"generator": "test", "rules_consumed": [],
                       "compiled_sha256": "0" * 64},
        "route_order": list(pids),
        "layer_assignment": {pid: "F.Cu" for pid in pids},
        "polylines": {pid: [list(pt) for pt in
                            next(p for p in board["partitions"]
                                 if p["partition_id"] == pid)
                            ["geometry"]["endpoints"]] for pid in pids},
        "generation_trace": [],
    }
    result = execute_candidate(board, candidate)
    assert result["verdict"] == "ROUTED"
    return board, result["routes"]


def test_same_edge_multi_segment_entries_allowed():
    """ED-1：同 topology_edge 多段 entry=executor 物理形态（entry=同层铜段），
    审计=去重后恰覆盖。原「网内唯一」判定与 entry 模型矛盾（crypto +3V3
    实证：13 边 18 entries 被 fail-closed 拦截）。"""
    from v5.route_check import validate_routes
    board, doc = _routed_doc()
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    doc = json.loads(json.dumps(doc))
    routes = doc["routes"]
    idx = [i for i, e in enumerate(routes)
           if e["partition_id"] == pid3][0]
    e = routes[idx]
    # 把 SIG3 第一条 entry 拆成两段同层 polyline（衔接点=原折线中点；
    # 同层共享衔接点=连通审计可过），两段同 topology_edge
    poly = e["polyline"]
    assert len(poly) >= 2
    mid = poly[len(poly) // 2]
    seg_a = dict(e, polyline=poly[:len(poly) // 2 + 1])
    seg_b = dict(e, polyline=poly[len(poly) // 2:])
    routes[idx:idx + 1] = [seg_a, seg_b]
    validate_routes(board, doc)   # 不抛=同边多段合法


def test_topology_edge_coverage_still_fail_closed():
    """ED-1 收紧面保持：缺边（去重后不覆盖）与 T*/M* 混用仍 fail-closed。"""
    from v5.route_check import RouteCheckError, validate_routes
    board, doc = _routed_doc()
    pid3 = [n["partitions"][0] for n in board["nets"]
            if n["net_id"] == "SIG3"][0]
    # 缺边：删一条 SIG3 entry
    d1 = json.loads(json.dumps(doc))
    idx = [i for i, e in enumerate(d1["routes"])
           if e["partition_id"] == pid3][0]
    del d1["routes"][idx]
    with pytest.raises(RouteCheckError, match="恰覆盖"):
        validate_routes(board, d1)
    # 混用：把一条 T* 改成 M0
    d2 = json.loads(json.dumps(doc))
    idx = [i for i, e in enumerate(d2["routes"])
           if e["partition_id"] == pid3][0]
    d2["routes"][idx]["topology_edge"] = "M0"
    with pytest.raises(RouteCheckError, match="混用"):
        validate_routes(board, d2)
