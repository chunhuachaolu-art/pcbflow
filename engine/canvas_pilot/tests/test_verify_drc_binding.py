# -*- coding: utf-8 -*-
"""验证核与 v5.drc 绑定一致 ≥10 例（已知好/坏夹具; 同源断言=画板判定与
直接调 v5.drc 的独立复算零失配）。

微板几何: N1 上行 (0.5,0.5)↔(9.5,0.5) 锚(1,1)/(19,1); N2 下行
(0.5,7.5)↔(9.5,7.5) 锚(1,15)/(19,15)。附着纪律: 段首末∈{锚, via}。"""
import json
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from v5 import drc
from canvas_pilot import lattice as _lat
from canvas_pilot import protocol, state as _state, verify
from canvas_pilot.conftest import micro_board


def make_state():
    board = micro_board()
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def route(st, wps, net="N1", layer="F.Cu", r=1):
    acts = [{"action": "route", "net_id": net, "waypoints": wps,
             "layer": layer}, {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": r, "actions": acts}), r), r)
    return out[0]


def test_binding_1_good_route_accepted():
    st = make_state()
    res = route(st, [[1, 1], [19, 1]])
    assert res["accepted"] is True
    assert st.connectivity["N1"] is True
    assert verify.full_check(st) == []


def test_binding_2_foreign_pad_violation():
    """异网铜间距不足（v5 R5 语义: polyline 中心线距; pad 参与半径）: N2
    绕行线触 N1 焊盘（线到 pad 圆心 0.5 - r 0.5 = gap 0 < 0.5）→ 画板拒收
    ⇔ v5.drc 直调同判。注: 平行线中心距恰 0.5=擦边合规（"<"才违例）。"""
    st = make_state()
    assert route(st, [[1, 1], [19, 1]], net="N1")["accepted"] is True
    res = route(st, [[1, 15], [1, 2], [19, 2], [19, 15]], net="N2", r=2)
    assert res["accepted"] is False and res["code"] == protocol.V_CLEARANCE
    # 独立复算: N1 焊盘 pad vs N2 垂直线（同一几何事实）
    pad = drc.Copper("N1", "pad:PT1:0", "F.Cu", pad=((0.5, 0.5), 0.5))
    line = drc.Copper("N2", "b", "F.Cu",
                      polyline=[(0.5, 1.0), (0.5, 7.5)], half_width=0.15)
    viols, _ = drc.check_clearance([pad, line], 0.5, same_net_exempt=True)
    assert len(viols) == 1 and viols[0].rule == "R5"
    # 平行线擦边对照（中心距恰 0.5）: 干净——与画板同源同判
    a = drc.Copper("N1", "a", "F.Cu",
                   polyline=[(0.5, 0.5), (9.5, 0.5)], half_width=0.15)
    b = drc.Copper("N2", "b", "F.Cu",
                   polyline=[(0.5, 1.0), (9.5, 1.0)], half_width=0.15)
    viols2, _ = drc.check_clearance([a, b], 0.5, same_net_exempt=True)
    assert viols2 == []


def test_binding_3_one_track_gap_clean():
    """绕行净空案（隔轨 1.0mm 中心距; 避异网焊盘）: 画板接受且 v5.drc 干净。"""
    st = make_state()
    assert route(st, [[1, 1], [19, 1]], net="N1")["accepted"] is True
    res = route(st, [[1, 15], [1, 3], [19, 3], [19, 15]], net="N2", r=2)
    assert res["accepted"] is True
    assert st.connectivity["N2"] is True
    assert verify.full_check(st) == []
    # 独立复算: 平行线对直调干净
    a = drc.Copper("N1", "a", "F.Cu",
                   polyline=[(0.5, 0.5), (9.5, 0.5)], half_width=0.15)
    b = drc.Copper("N2", "b", "F.Cu",
                   polyline=[(0.5, 1.5), (9.5, 1.5)], half_width=0.15)
    viols, _ = drc.check_clearance([a, b], 0.5, same_net_exempt=True)
    assert viols == []


def test_binding_4_same_net_exempt():
    """同网自交/贴邻: same_net_exempt=True（v5.drc 同参）→ 不违例。"""
    st = make_state()
    res = route(st, [[1, 1], [10, 1], [10, 5], [5, 5], [5, 1], [19, 1]],
                net="N1")
    assert res["accepted"] is True
    assert verify.full_check(st) == []


def test_binding_5_cross_layer_clean():
    """跨层（F/B.Cu）异网同线位重叠: v5.drc R5 只判同层 → 画板同样放行。"""
    st = make_state()
    assert route(st, [[1, 1], [19, 1]], net="N1", layer="F.Cu")["accepted"]
    res = route(st, [[1, 15], [19, 15]], net="N2", layer="F.Cu", r=2)
    assert res["accepted"] is True
    # 再放一条 N2 无关线跨层重叠于 N1（B.Cu 直压 N1 线位）—— 经由 via 链
    acts = [
        {"action": "route", "net_id": "N2", "waypoints": [[1, 15], [1, 1]],
         "layer": "F.Cu"},
        {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": 3, "actions": acts}), 3), 3)
    # x=0.5 垂直线 vs N1 水平线端点 (0.5,0.5): 异网同点 → 拒（同层）
    assert out[0]["accepted"] is False
    # 跨层版: N2 B.Cu 压 N1 线位
    st2 = make_state()
    assert route(st2, [[1, 1], [19, 1]], net="N1", layer="F.Cu")["accepted"]
    res = route(st2, [[1, 15], [1, 5], [19, 5], [19, 15]], net="N2",
                layer="B.Cu", r=2)
    assert res["accepted"] is True
    assert verify.full_check(st2) == []


def test_binding_6_edge_keepout():
    """板边禁布带: 贴边铜直调 v5.drc.check_edge_clearance 同判（带 0.2）。"""
    st = make_state()
    cu = drc.Copper("N1", "t", "F.Cu",
                    polyline=[(0.5, 0.0), (5.0, 0.0)], half_width=0.15)
    ev = drc.check_edge_clearance([cu], verify.ws_tuple(st.board))
    assert len(ev) >= 1 and ev[0].rule == "edge_clearance"
    # 画板面同源: 候选线压 j=0 一行（经 via 挂接不可能——端到端锚在 j=1,
    # 故 edge 判定在差集归责中以 v5.drc 直调断言为准; 此处补 ws_tuple 同值）
    from v5.drc import edge_inner_rect
    assert edge_inner_rect(verify.ws_tuple(st.board), 0.2) == \
        edge_inner_rect((0.0, 0.0, 10.0, 8.0), 0.2)


def _board_with_hole(hole):
    board = micro_board()
    board["holes"] = [hole]
    return board


def test_binding_7_hole_track_blocked_formula():
    """孔禁布 track face 同式: 画板 V_HOLE_TRACK ⇔ hole_track_blocked 真值。"""
    board = _board_with_hole({"drill_mm": 0.8, "plated": True,
                              "pos_mm": [5.0, 3.0], "shape": "circle"})
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    # N1 绕行路线展开含垂直段 x=4.5 y∈[0.5,2.5]: 孔 (5.0,3.0) 距段端
    # (4.5,2.5)=0.707 < 0.4+0.25+0.15=0.8 → 阻塞
    res = route(st, [[1, 1], [9, 1], [9, 5], [19, 1]])
    assert res["accepted"] is False and res["code"] == protocol.V_HOLE_TRACK
    holes = drc.normalize_holes(board["holes"])
    assert drc.hole_track_blocked(holes[0][:2], holes[0][2],
                                  (4.5, 0.5), (4.5, 2.5), 0.15) is True


def test_binding_8_hole_endpoint_exempt():
    """端点豁免同式: 孔心=分区端点 → 该网段不因此孔拒（route_check 同豁免）。"""
    board = _board_with_hole({"drill_mm": 0.8, "plated": True,
                              "pos_mm": [0.5, 0.5], "shape": "circle"})
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    res = route(st, [[1, 1], [19, 1]])
    assert res["accepted"] is True
    # 独立复算: 无豁免口径下同段会 blocked（豁免确在起作用）
    holes = drc.normalize_holes(board["holes"])
    assert drc.hole_track_blocked(holes[0][:2], holes[0][2],
                                  (0.5, 0.5), (9.5, 0.5), 0.15) is True


def test_binding_9_hole_via_zero_exempt():
    """孔禁布 via face 零豁免: hole_via_blocked 直调真值同源（画板路径中
    压孔 via 恒伴随压孔段先拒——几何带重叠, 故 via face 以谓词直调钉绑）。"""
    holes = drc.normalize_holes(
        [{"drill_mm": 0.8, "plated": True, "pos_mm": [5.0, 3.0],
          "shape": "circle"}])
    hx, hy, hr = holes[0]
    assert drc.hole_via_blocked((hx, hy), hr, (5.0, 3.0), 0.3) is True
    # 带值 0.4+0.25+0.3=0.95: d=0.9 仍阻; d=1.0 放行
    assert drc.hole_via_blocked((hx, hy), hr, (5.0, 4.0), 0.3) is False
    # 画板侧同谓词: check_via_candidate 对孔带格点拒收
    board = _board_with_hole({"drill_mm": 0.8, "plated": True,
                              "pos_mm": [5.0, 3.0], "shape": "circle"})
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    v = verify.check_via_candidate(st, "N1", (10, 6))  # (5.0,3.0)=孔心
    assert v and v[0]["code"] == "V_HOLE_VIA"


def test_binding_10_via_on_path_accepted():
    """via on-path 合法落孔: 链审计经 via 衔接的跨层两段全连通。"""
    st = make_state()
    acts = [
        {"action": "route", "net_id": "N1", "waypoints": [[1, 1], [10, 1]],
         "layer": "F.Cu"},
        {"action": "via", "net_id": "N1", "grid": [10, 1]},
        {"action": "route", "net_id": "N1", "waypoints": [[10, 1], [19, 1]],
         "layer": "B.Cu"},
        {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": 1, "actions": acts}), 1), 1)
    assert all(x["accepted"] for x in out[:3]), out
    assert st.connectivity["N1"] is True
    assert verify.full_check(st) == []


def test_binding_11_full_check_matches_candidate_path():
    """全量复核与候选判定零漂移: 逐条接受后 full_check 恒干净（不变量:
    语义拒收保证不落脏铜; 混合批后状态 DRC 干净且连通如实）。"""
    st = make_state()
    route(st, [[1, 1], [19, 1]], net="N1")
    route(st, [[1, 15], [1, 2], [19, 2], [19, 15]], net="N2", r=2)  # 拒
    assert verify.full_check(st) == []
    assert st.connectivity["N1"] is True and st.connectivity["N2"] is False
    route(st, [[1, 15], [1, 3], [19, 3], [19, 15]], net="N2", r=3)  # 隔轨过
    assert st.connectivity["N2"] is True
    assert verify.full_check(st) == []


def test_binding_12_expand_waypoints_manhattan():
    """实例化器曼哈顿展开确定性（先 x 后 y）: 无对角线、折点落格点。"""
    from canvas_pilot.instantiate import expand_waypoints
    assert expand_waypoints([[1, 1], [3, 3]]) == \
        [(1, 1), (2, 1), (3, 1), (3, 2), (3, 3)]
    assert expand_waypoints([[3, 3], [1, 1]]) == \
        [(3, 3), (2, 3), (1, 3), (1, 2), (1, 1)]


def test_binding_14_dead_anchor_repair(badgeleds_board):
    """锚修补确定性: badgeleds PT-C1-Pad1 锚0 最近锚 (27,55) 死锚（stub
    触异网 pad 0.4982<0.5 擦线）→ 按 8 邻域字典序修补至 (26,56), 修补后
    全部 18 锚四向起笔可用; 修补确定性双跑锚表等。"""
    from canvas_pilot import loop as _loop
    from canvas_pilot import state as _st
    board = badgeleds_board
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _st.CanvasState(board, "<probe>", "0" * 64, lat,
                         _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    assert st.anchors["PT-Net-_C1-Pad1_"][0] == [27, 55]
    assert _loop._dead_anchor(st, "PT-Net-_C1-Pad1_", 0) is True
    log = _loop._repair_dead_anchors(st, [])
    assert log == [{"partition_id": "PT-Net-_C1-Pad1_", "endpoint": 0,
                    "from": [27, 55], "to": [26, 56]}]
    for p in board["partitions"]:
        pid = p["partition_id"]
        for k in (0, 1):
            assert _loop._dead_anchor(st, pid, k) is False, (pid, k)
    st2 = _st.CanvasState(board, "<probe>", "0" * 64,
                          _lat.Lattice.from_board(board, 0.5),
                          _lat.anchor_map(board, _lat.Lattice.from_board(board, 0.5)))
    st2.recompute_connectivity()
    _loop._repair_dead_anchors(st2, [])
    assert st.anchors == st2.anchors


def test_binding_13_ripup_and_gc():
    """ripup 段后悬空 via GC; ripup(net) 整网清。"""
    st = make_state()
    acts = [
        {"action": "route", "net_id": "N1", "waypoints": [[1, 1], [10, 1]],
         "layer": "F.Cu"},
        {"action": "via", "net_id": "N1", "grid": [10, 1]},
        {"action": "route", "net_id": "N1", "waypoints": [[10, 1], [19, 1]],
         "layer": "B.Cu"},
        {"action": "submit"}]
    protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": 1, "actions": acts}), 1), 1)
    assert st.vias and st.connectivity["N1"] is True
    acts2 = [{"action": "ripup", "shape_id": "seg:N1:1"},
             {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": 2, "actions": acts2}), 2), 2)
    assert out[0]["accepted"] is True
    assert st.vias                                    # via 仍挂 seg0 → 不 GC
    acts3 = [{"action": "ripup", "shape_id": "seg:N1:0"},
             {"action": "submit"}]
    out = protocol.apply_batch(st, protocol.parse_batch(
        json.dumps({"round": 3, "actions": acts3}), 3), 3)
    assert out[0]["accepted"] is True
    assert st.vias == []                              # 两段皆拆 → via GC
    assert st.connectivity["N1"] is False
