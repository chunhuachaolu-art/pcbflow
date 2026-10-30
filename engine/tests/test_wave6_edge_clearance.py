# -*- coding: utf-8 -*-
"""P5⑥ D6-3 板边距入 v5 世界模型——B 包（执行+检查侧）测试。

合同 V5-P5-WAVE6 §2 D6-3（2026-09-16 照准）；验收钉四件：
- **禁布带宽度**：带值 = kicad-cli 生效缺省 copper_edge_clearance 0.2mm
  （drc.EDGE_CLEARANCE_MM 常量单源；board.json 现无显式边距字段——考证结论
  见 v5/drc.py 注），带 = workspace 内缩 0.2mm 环带，轮廓唯一源 = workspace
  矩形（禁第二轮廓源）；
- **贴边拒布**：executor 障碍栅格（edge_blocked/via_blocked）对带内段/孔位
  拒布，全信号层同带、无豁免档；端点入带 → 整网如实 FAILED；
- **归因类**：exhaustion-cause=edge-clearance（分类序首位，防 endpoint-sealed
  遮蔽——带内端点 sealed 同真但根因是带）；
- **edge_violations 键**：route_check 结果恒在场、可为空列表，元素
  {"net_id": str, "pos": [x, y]}，披露通道不入 feasible（板数据固定铜贴边
  不归责 routes 的既有纪律；执行侧拒布在 executor，检查侧只如实记铜）。
判定全出自 v5.drc.check_edge_clearance（A9 单源）；零长退化条目不构造铜
（升级件④缝）天然不参与。stdlib+pytest，无随机无时钟，确定性。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import drc  # noqa: E402
from v5.board import compute_board_sha256  # noqa: E402
from v5.drc import (EDGE_CLEARANCE_MM, VERSION as DRC_VERSION,  # noqa: E402
                    check_edge_clearance, edge_inner_rect)
from v5.executor import (EXECUTOR_VERSION, _Context, _exhaustion_cause,  # noqa: E402
                         execute_candidate)
from v5.route_check import (ROUTES_SCHEMA_VERSION, ROUTE_CHECK_VERSION,  # noqa: E402
                            check_edge_clearance as rc_check_edge_clearance,
                            check_routes)


# ---------------------------------------------------------------- 夹具与助手

def make_board(*, workspace, stackup, partitions, nets, zones=None,
               board_id="t", validate=True):
    """构造板 + provenance 落链（默认过 v5.board.load_board fail-closed）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup,
        "workspace": workspace,
        "zones": zones or [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    if validate:
        from v5.board import load_board
        return load_board(board)
    return board


SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True}]
WS = {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0}


def part(pid, a, b, ptype="MISC", layer="F.Cu", width=0.2, **geo):
    g = {"endpoints": [list(a), list(b)]}
    g.update(geo)
    return {"partition_id": pid, "ptype": ptype, "layer_policy": layer,
            "planned_width": width, "current_a": 0, "geometry": g,
            "speed_class": "low_speed",
            "width_prior": {"w_min": width, "w_max": 0.4}}


def net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def cand_for(board, cid="C-E1"):
    parts = [p["partition_id"] for p in board["partitions"]]
    return {"candidate_id": cid, "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": parts,
            "layer_assignment": {p["partition_id"]: p["layer_policy"]
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


def routes_doc(board, entries):
    """手工构造过 validate_routes 的 v5.routes.v1 工件（单网单/多段）。"""
    sha = compute_board_sha256(board)
    return {"schema_version": ROUTES_SCHEMA_VERSION,
            "board_id": board["board_id"],
            "board_sha256": sha,
            "routes": entries,
            "negotiation_log": [],
            "provenance": {"generator": "hand", "board_sha256": sha}}


def _entry(pid, nid, layer, poly, tv=None, rv=None, width=0.2):
    return {"partition_id": pid, "net_id": nid, "layer": layer,
            "polyline": [list(p) for p in poly], "width": width,
            "transition_vias": [list(p) for p in (tv or [])],
            "return_vias": [list(p) for p in (rv or [])]}


# ---------------------------------------------------------------- 版本/单源钉

def test_d63_versions_and_constant():
    """⑥ 版本钉：executor 0.4.0→0.5.0（合同 D6-3 钉死）、route_check 0.2.0→
    0.3.0（edge_violations 键）、drc 0.1.0→0.2.0（edge 判定入权威）；带值
    0.2mm 常量钉。"""
    # V5-D8 翻转披露（2026-09-22）：executor 0.6.0/route_check 0.4.0/
    # drc 0.3.0（板固孔禁布带，HOLE_TO_HOLE_MM 另钉于 test_d8_board_holes）
    # V5-SMALLWAVE 翻转披露（2026-09-23）：executor 0.6.0→0.6.1（geom-secondary
    # 几何二级归因 log 行，log-only）
    # V5-R2 翻转披露（2026-09-24）：executor 0.6.1→0.7.0（rip-up 有界深化
    # 2/8/20→5/12/30+W-2 联合重排+W-3 波次/档位导引+W-4 victim 定向探针）
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    # V5-R7 翻转披露（2026-10-04）：executor 0.9.0→0.10.0（保守 max 障碍栅格+
    # 轮廓带）、route_check 0.4.1→0.5.0（net_classes/outline_mm 消费）、
    # drc 0.3.0→0.4.0（R5 网对取值+OutlineBand）——R8 F1 先例同步
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步
    assert ROUTE_CHECK_VERSION == "v5.route_check/0.5.0"  # W-6 ED-2 翻新（0.4.0→0.4.1 PTH 孔筒 union）→R7 0.5.0
    assert DRC_VERSION == "v5.drc/0.4.0"   # V5-R7 同步（per-netclass R5+OutlineBand）
    assert EDGE_CLEARANCE_MM == 0.2


def test_band_single_source_across_three_modules():
    """单一事实源钉：executor/route_check 的带几何全部出自 v5.drc（禁第二
    轮廓源/第二带值源）——route_check 引用同一判定器对象，executor 上下文
    内矩形与 drc.edge_inner_rect 恒等。"""
    assert rc_check_edge_clearance is check_edge_clearance
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (5.0, 5.0), (9.0, 5.0))],
                       nets=[net("N1", ["P1"])])
    ctx = _Context(board)
    assert ctx.edge_inner == edge_inner_rect(ctx.view.workspace)
    assert ctx.edge_inner == (0.2, 0.2, 19.8, 19.8)


# ---------------------------------------------------------------- 禁布带宽度

def test_band_width_pinned_on_all_four_sides():
    """带宽钉：内矩形 = workspace 内缩 0.2mm；判定点恰在 0.2mm 处合规
    （擦边合规，与 R5 口径一致），0.1mm 处四侧全违例。"""
    ws = (0.0, 0.0, 10.0, 10.0)
    assert edge_inner_rect(ws) == (0.2, 0.2, 9.8, 9.8)
    cu = drc.Copper("N", "c", "F.Cu")
    pts_exact = [(0.2, 5.0), (9.8, 5.0), (5.0, 0.2), (5.0, 9.8)]
    pts_in = [(0.1, 5.0), (9.9, 5.0), (5.0, 0.1), (5.0, 9.9)]
    for pt in pts_exact:
        cu.polyline = [pt, (5.0, 5.0)]
        assert check_edge_clearance([cu], ws) == [], pt
    for pt in pts_in:
        cu.polyline = [pt, (5.0, 5.0)]
        vs = check_edge_clearance([cu], ws)
        assert len(vs) == 1 and vs[0].data["pos"] == [pt[0], pt[1]], pt


def test_drc_point_semantics_polyline_pad_band():
    """判定点语义钉（中心线口径）：折线=顶点、矩形带=角点、焊盘=圆心；
    内矩形凸 ⇒ 段触带 ⟺ 端点触带（中段穿带而两端在带外不可能）。逐违例点
    一枚 Violation（rule="edge_clearance"、subject_b="board-edge"、data 带
    pos/net_id/layer/margin_mm），序=输入序×点序。"""
    poly = drc.Copper("N1", "c1", "F.Cu", polyline=[[0.1, 5.0], [5.0, 5.0]])
    pad = drc.Copper("N2", "p1", "F.Cu", pad=((0.15, 5.0), 0.25))
    band = drc.Copper("N3", "b1", "F.Cu", band=(0.0, 1.0, 3.0, 1.2))
    clean = drc.Copper("N4", "c2", "F.Cu", polyline=[[1.0, 1.0], [2.0, 2.0]])
    vs = check_edge_clearance([poly, pad, band, clean], (0.0, 0.0, 10.0, 10.0))
    assert [(v.rule, v.subject_a, v.subject_b) for v in vs] == [
        ("edge_clearance", "c1", "board-edge"),
        ("edge_clearance", "p1", "board-edge"),
        ("edge_clearance", "b1", "board-edge"),
        ("edge_clearance", "b1", "board-edge")]
    assert vs[0].data == {"pos": [0.1, 5.0], "net_id": "N1", "layer": "F.Cu",
                          "margin_mm": 0.2}
    assert [v.data["pos"] for v in vs[2:]] == [[0.0, 1.0], [0.0, 1.2]]


# ---------------------------------------------------------------- 贴边拒布

def test_executor_edge_blocked_band_all_layers_and_via():
    """障碍栅格钉（_Context 单元）：带内段/孔位返 "edge-clearance"，擦边
    （0.2mm）与带外（0.25mm）放行；全信号层同带（逐层 loop 钉）；禁布带
    判定无同分区豁免档。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (5.0, 5.0), (9.0, 5.0))],
                       nets=[net("N1", ["P1"])])
    ctx = _Context(board)
    for layer in ctx.view.signal_layers:
        assert ctx.edge_blocked(layer, (0.1, 5.0), (5.0, 5.0), "N1", "P1", 0.2) \
            == "edge-clearance"
        assert ctx.edge_blocked(layer, (5.0, 0.1), (5.0, 9.0), "N1", "P1", 0.2) \
            == "edge-clearance"
        assert ctx.edge_blocked(layer, (19.9, 5.0), (5.0, 5.0), "N1", "P1", 0.2) \
            == "edge-clearance"
        assert ctx.edge_blocked(layer, (0.2, 5.0), (5.0, 5.0), "N1", "P1", 0.2) \
            is None
        assert ctx.edge_blocked(layer, (0.25, 5.0), (5.0, 5.0), "N1", "P1", 0.2) \
            is None
        # 孔位：带内封、带外放（孔铜同为铜，与折线同带同口径）
        assert ctx.via_blocked((0.1, 5.0), "N1") == "edge-clearance"
        assert ctx.via_blocked((0.25, 5.0), "N1") is None
        # 无豁免档：带内段不受 exempt_same_partition 影响
        assert ctx.edge_blocked(layer, (0.1, 5.0), (5.0, 5.0), "N1", "P1", 0.2,
                                exempt_same_partition=True) == "edge-clearance"


def test_executor_edge_hug_endpoint_rejected_e2e():
    """贴边拒布 e2e：端点入带（0.1mm 贴边）→ 整网 FAILED、routes=None
    （无半成品工件）；对照端点 0.25mm（带外）→ ROUTED。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (0.1, 5.0), (6.0, 5.0))],
                       nets=[net("N1", ["P1"])], board_id="t-hug")
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    board2 = make_board(workspace=WS, stackup=SIG,
                        partitions=[part("P1", (0.25, 5.0), (6.0, 5.0))],
                        nets=[net("N1", ["P1"])], board_id="t-ok")
    res2 = execute_candidate(board2, cand_for(board2))
    assert res2["verdict"] == "ROUTED"
    assert check_routes(board2, res2["routes"])["edge_violations"] == []


# ---------------------------------------------------------------- 归因类

def test_exhaustion_cause_edge_clearance_class():
    """归因类钉：端点入带 → exhaustion-cause=edge-clearance（行格式与分类序
    钉死；先于 endpoint-sealed——带内端点 sealed 同真但根因是带）；单位置
    直调 _exhaustion_cause 钉起/终两端触发面。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (0.1, 5.0), (6.0, 5.0))],
                       nets=[net("N1", ["P1"])], board_id="t-cause")
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "FAILED"
    causes = [l for l in res["negotiation_log"] if "exhaustion-cause=" in l]
    assert causes == ["net=N1 partition=P1 exhaustion-cause="
                      "edge-clearance（端点入板边禁布带，边距类）"]
    ctx = _Context(board)
    assert _exhaustion_cause(ctx, "P1", "N1", 0.2, (0.1, 5.0), (6.0, 5.0)) == \
        "edge-clearance（端点入板边禁布带，边距类）"
    assert _exhaustion_cause(ctx, "P1", "N1", 0.2, (6.0, 5.0), (19.9, 5.0)) == \
        "edge-clearance（端点入板边禁布带，边距类）"
    # 对照：端点全在带外 → 不归 edge-clearance（落兜底/他类）
    assert not _exhaustion_cause(ctx, "P1", "N1", 0.2,
                                 (5.0, 5.0), (9.0, 5.0)).startswith("edge-clearance")


# ------------------------------------------------- edge_violations 消费接口键

def test_route_check_edge_violations_key_contract():
    """接口键钉（兄弟包 C/D6-4 消费面，逐字）：恒在场、可为空列表；元素 =
    {"net_id": str, "pos": [x, y]}；route 点入带即记、带外不记；披露通道
    **不入** feasible（板数据贴边不归责 routes 的既有纪律）。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (0.5, 5.0), (6.0, 5.0))],
                       nets=[net("N1", ["P1"])], board_id="t-key")
    # 干净 route：键在场且为空列表
    rep = check_routes(board, routes_doc(board, [
        _entry("P1", "N1", "F.Cu", [(0.5, 5.0), (6.0, 5.0)])]))
    assert rep["edge_violations"] == []
    assert rep["feasible"] is True
    # route 点入带：逐字记 {"net_id", "pos"}；feasible 不因本键翻转
    rep2 = check_routes(board, routes_doc(board, [
        _entry("P1", "N1", "F.Cu", [(0.5, 5.0), (0.1, 5.0), (6.0, 5.0)])]))
    assert rep2["edge_violations"] == [{"net_id": "N1", "pos": [0.1, 5.0]}]
    assert all(set(e.keys()) == {"net_id", "pos"} for e in rep2["edge_violations"])
    assert isinstance(rep2["edge_violations"][0]["net_id"], str)
    assert rep2["feasible"] is True
    # 对照：同折线全带外 → 无记录
    rep3 = check_routes(board, routes_doc(board, [
        _entry("P1", "N1", "F.Cu", [(0.5, 5.0), (0.3, 5.0), (6.0, 5.0)])]))
    assert rep3["edge_violations"] == []


def test_route_check_dedup_same_point_via_two_layers():
    """去重钉：换层网孔位入带——折线顶点 + 每信号层一枚孔铜同位点（物理
    一孔）→ (net_id, pos) 去重首现序，恰一记。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (0.5, 5.0), (6.0, 8.0),
                                        layer="F.Cu")],
                       nets=[net("N1", ["P1"])], board_id="t-dedup")
    v = (0.1, 6.5)
    doc = routes_doc(board, [
        _entry("P1", "N1", "F.Cu", [(0.5, 5.0), v], tv=[v]),
        _entry("P1", "N1", "B.Cu", [v, (6.0, 8.0)], tv=[v])])
    rep = check_routes(board, doc)
    assert rep["edge_violations"] == [{"net_id": "N1", "pos": [0.1, 6.5]}]


def test_route_check_fixed_shape_edge_disclosure_not_blamed():
    """板数据固定铜贴边披露钉：既布（ROUTED）分区端点入带 → executor 照常
    ROUTED（板声明铜不经 A*、不拒布），route_check edge_violations 如实记
    铜、feasible 不归责翻转（board-data 固有态；kicad 残差由 D6-4 分类器
    同位归责）。ribbon 铜带角点同口径披露。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("PF", (0.0, 8.0), (4.0, 8.0),
                                        ptype="ROUTED"),
                                   part("PR", (0.1, 2.0), (0.1, 6.0),
                                        ptype="BUS", copper_band=[0.05, 0.5],
                                        occupancy_mm=0.45),
                                   part("P1", (4.0, 5.0), (9.0, 5.0))],
                       nets=[net("NF", ["PF"]), net("NR", ["PR"]),
                             net("N1", ["P1"])], board_id="t-fixed")
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    rep = check_routes(board, res["routes"])
    assert {"net_id": "NF", "pos": [0.0, 8.0]} in rep["edge_violations"]
    # ribbon 带角点（x=0.05 两侧角入带；x=0.5 角带外）
    ribbon_hits = [e for e in rep["edge_violations"] if e["net_id"] == "NR"]
    assert {"net_id": "NR", "pos": [0.05, 2.0]} in ribbon_hits
    assert {"net_id": "NR", "pos": [0.05, 6.0]} in ribbon_hits
    assert all(e["pos"][0] != 0.5 for e in ribbon_hits)
    assert rep["feasible"] is True


def test_route_check_degenerate_zero_length_seam_not_recorded():
    """④缝保持钉：退化分区（两端点重合，入带位置）= 零长条目零铜声明——
    不构造铜 → edge_violations 不记（零铜即无间距/边距交互）；执行照常
    ROUTED。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (0.1, 5.0), (0.1, 5.0))],
                       nets=[net("N1", ["P1"])], board_id="t-degen")
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    rep = check_routes(board, res["routes"])
    assert rep["edge_violations"] == []
