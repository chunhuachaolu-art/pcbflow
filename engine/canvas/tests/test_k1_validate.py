# -*- coding: utf-8 -*-
"""Lane-K1 validate 测试: v5.drc 同源绑定一致性（≥8 对照）。

每例=同一几何两条路: (a) canvas.validate.validate_edit 判定;
(b) 测试内直接调 v5.drc 同名函数族——两者必须一致（禁止平行实现的
可证伪面: 判定分支全部转译为对 v5.drc 的直接对照）。
"""
import json

import pytest

from v5 import drc
from v5 import board as v5board
from v5.kicad_export import via_model_params

from canvas import instantiate as cin
from canvas import validate as cva
from canvas.tests.test_k1_fixtures import synth_state, run_batch


def _ws(st):
    w = st.board["workspace"]
    return (w["x_min"], w["y_min"], w["x_max"], w["y_max"])


def _cand_seg_copper(st, net_id, layer, waypoints):
    pid = st.net_partitions(net_id)[0]
    cls = st.widths.get(net_id, "min")
    fake = {"shape_id": "probe:seg", "net_id": net_id, "partition_id": pid,
            "layer": layer, "grid": [list(p) for p in
                                     cin.expand_waypoints(waypoints)],
            "width_class": cls}
    return cin.seg_copper(st, fake)


def _vk(v):
    return (v.rule, str(v.subject_a), str(v.subject_b),
            json.dumps(v.data, sort_keys=True))


def _scene(st):
    coppers = cin.pad_coppers(st)
    for sid in sorted(st.segs):
        coppers.append(cin.seg_copper(st, st.segs[sid]))
    coppers.extend(cin.via_coppers(st))
    for sid in sorted(st.tunings):
        cu = cin.tuning_copper(st, st.tunings[sid])
        if cu is not None:
            coppers.append(cu)
    return coppers


def _diff_new_violations_direct(st, cand):
    """测试内直算差集（不经 canvas.validate 内部）: base/full 两场景
    直接调 v5.drc.check_clearance / check_edge_clearance。"""
    minc = st.board["hard_rules"]["R5"]["min_clearance_mm"]
    base = _scene(st)

    def keys(scene):
        r5, _ = drc.check_clearance(scene, minc, same_net_exempt=True)
        edge = drc.check_edge_clearance(scene, _ws(st))
        return {_vk(v) for v in r5} | {_vk(v) for v in edge}

    return keys(base + [cand]) - keys(base)


def _hole_blocked_direct(st, pts, half_width):
    holes = drc.normalize_holes(st.board["holes"])
    return any(drc.hole_track_blocked(h[:2], h[2], a, b, half_width)
               for h in holes for a, b in zip(pts[:-1], pts[1:]))


def test_binding_route_corridor_scan_clearance_vs_hole():
    """走廊扫描绑定（9 例）: validate 判定 ⟺ 直调差集/孔谓词。
    拒收时 V_CLEARANCE ⟺ 差集非空; V_HOLE_TRACK ⟺ 直调孔谓词真。"""
    st = synth_state()
    hw = cva.width_class_vocab(st.board)["min"] / 2.0
    for j in (4, 5, 6, 7, 8, 9, 10, 11, 12):
        wps = [[4, 16], [4, j], [20, j], [20, 16]]
        action = {"action": "route", "net_id": "NET-B",
                  "waypoints": wps, "layer": "F.Cu"}
        accepted, code, _ = cva.validate_edit(st, action)
        cand = _cand_seg_copper(st, "NET-B", "F.Cu", wps)
        new_v = _diff_new_violations_direct(st, cand)
        hole_v = _hole_blocked_direct(st, cand.polyline, hw)
        if accepted:
            assert not new_v and not hole_v, \
                "validate 放行但直调有违例: j=%d new=%d hole=%s" % (
                    j, len(new_v), hole_v)
        elif code == "V_HOLE_TRACK":
            assert hole_v, "j=%d 直调孔谓词为假" % j
        else:
            assert code == "V_CLEARANCE" and new_v, \
                "j=%d 拒收码 %s 与直调不符 (new=%d hole=%s)" % (
                    j, code, len(new_v), hole_v)


def test_binding_route_edge_clearance():
    """edge 绑定: j=20（y=10=workspace 上界）→ 直调 check_edge_clearance
    顶点出内矩形 ⟺ validate 拒 V_EDGE；j=18 干净且放行。"""
    st = synth_state()
    for j, expect_edge in ((20, True), (18, False)):
        wps = [[4, 16], [4, j], [20, j], [20, 16]]
        accepted, code, _ = cva.validate_edit(
            st, {"action": "route", "net_id": "NET-B", "waypoints": wps,
                 "layer": "F.Cu"})
        cand = _cand_seg_copper(st, "NET-B", "F.Cu", wps)
        cand_edge = [v for v in drc.check_edge_clearance(
            [cand] + cin.pad_coppers(st), _ws(st))
            if v.subject_a == "probe:seg"]
        if expect_edge:
            assert (not accepted) and code == "V_EDGE"
            assert cand_edge, "直调未见 probe 段 edge 违例"
        else:
            assert accepted and code is None
            assert not cand_edge, "直调意外出现 edge 违例: %r" % (cand_edge,)


def test_binding_via_hole_face_predicate():
    """via 孔面绑定: hole_via_blocked 直调 ⟺ V_HOLE_VIA 判定
    （大 via_model 板: (16,10) 距孔 1.0<1.15 拒; (14,13) 距 1.5 过）。"""
    st = synth_state(via_model={"drill_mm": 0.6, "annular_mm": 0.2})
    run_batch(st, [
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[26, 10], [16, 10], [16, 13], [4, 13], [2, 10]],
         "layer": "F.Cu"},
    ])
    r = via_model_params(st.board)["radius"]
    holes = drc.normalize_holes(st.board["holes"])
    for grid, expect_blocked in (([16, 10], True), ([14, 13], False)):
        mm = st.lattice.to_mm(*grid)
        blocked = any(drc.hole_via_blocked(h[:2], h[2], mm, r)
                      for h in holes)
        assert blocked == expect_blocked, "直调 hole_via_blocked=%s" % blocked
        accepted, code, _ = cva.validate_edit(
            st, {"action": "via", "net_id": "NET-C", "grid": grid})
        assert (not accepted and code == "V_HOLE_VIA") == expect_blocked, \
            "via %s: validate=%s/%s 直调 blocked=%s" % (
                grid, accepted, code, blocked)


def test_binding_route_hole_track_predicate_with_exemption():
    """track 孔面绑定: hole_track_blocked 直调 ⟺ V_HOLE_TRACK；
    端点豁免同式（孔心==网端点 → 归责豁免转收）。"""
    st = synth_state()
    hw = cva.width_class_vocab(st.board)["min"] / 2.0
    wps = [[26, 10], [2, 10]]
    cand = _cand_seg_copper(st, "NET-C", "F.Cu", wps)
    assert _hole_blocked_direct(st, cand.polyline, hw)
    accepted, code, _ = cva.validate_edit(
        st, {"action": "route", "net_id": "NET-C", "waypoints": wps,
             "layer": "F.Cu"})
    assert (not accepted) and code == "V_HOLE_TRACK"
    # 孔挪到 NET-A 端点 (2,2) → 穿孔路由（端点豁免孔不归责）转收
    board = json.loads(json.dumps(st.board))
    board["holes"][0]["pos_mm"] = [2.0, 2.0]
    prov = dict(board["provenance"])
    prov.pop("board_sha256", None)
    board["provenance"] = prov
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    st2 = synth_state()
    st2.board = v5board.load_board(board)
    holes2 = drc.normalize_holes(st2.board["holes"])
    cand2 = _cand_seg_copper(st2, "NET-A", "F.Cu", [[4, 4], [20, 4]])
    raw_blocked = any(drc.hole_track_blocked(h[:2], h[2], a, b, hw)
                      for h in holes2 for a, b in zip(cand2.polyline[:-1],
                                                      cand2.polyline[1:]))
    assert raw_blocked, "孔在端点上: 几何上确实触带（豁免才放行）"
    accepted2, code2, _ = cva.validate_edit(
        st2, {"action": "route", "net_id": "NET-A",
              "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"})
    assert accepted2 and code2 is None


def test_binding_same_net_exempt():
    """同网豁免绑定: 同网同层完全重叠的第二段 → check_clearance(
    same_net_exempt=True) 对该对零违例 ⟺ validate 放行。"""
    st = synth_state()
    run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
    ])
    second = _cand_seg_copper(st, "NET-A", "F.Cu", [[4, 4], [20, 4]])
    scene = [second] + _scene(st)
    r5, _checked = drc.check_clearance(
        scene, st.board["hard_rules"]["R5"]["min_clearance_mm"],
        same_net_exempt=True)
    pair = [v for v in r5
            if {v.subject_a, v.subject_b} == {"probe:seg", "seg:NET-A:0"}]
    assert not pair, "same_net_exempt=True 直调不应给出同网对违例"
    accepted, code, _ = cva.validate_edit(
        st, {"action": "route", "net_id": "NET-A",
             "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"})
    assert accepted and code is None


def test_binding_via_clearance_pad_to_pad():
    """via R5 绑定: 异网 via pad vs 在场 via pad，pad_pad_distance 直调
    ⟺ V_CLEARANCE 且 detail 带 gap。"""
    st = synth_state()
    run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [4, 6], [20, 6], [20, 16]], "layer": "F.Cu"},
    ])
    accepted, code, detail = cva.validate_edit(
        st, {"action": "via", "net_id": "NET-B", "grid": [12, 6]})
    assert (not accepted) and code == "V_CLEARANCE"
    r = via_model_params(st.board)["radius"]
    a = drc.Copper("NET-B", "probe:via", "F.Cu",
                   pad=(st.lattice.to_mm(12, 6), r))
    b = drc.Copper("NET-A", "via:NET-A:12_4", "F.Cu",
                   pad=(st.lattice.to_mm(12, 4), r))
    gap = drc._actual_gap(a, b)
    assert gap < st.board["hard_rules"]["R5"]["min_clearance_mm"] - 1e-12
    assert "gap=%s" % (round(gap, 10),) in detail


def test_binding_validate_full_equals_check_all_plus_edge_hole():
    """全态绑定: validate_full 违例集 == drc.check_all(同场景) +
    check_edge_clearance 直调（干净态并集为空）。"""
    st = synth_state()
    run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
    ])
    scene = _scene(st)
    report = cva.validate_full(st)
    assert report.drc_version == drc.VERSION
    assert isinstance(report, drc.DRCReport)
    check_all_v = drc.check_all(scene, st.board["hard_rules"]).violations
    edge_v = drc.check_edge_clearance(scene, _ws(st))
    want = {(v.rule, str(v.subject_a), str(v.subject_b))
            for v in list(check_all_v) + list(edge_v)}
    got = {(v.rule, str(v.subject_a), str(v.subject_b))
           for v in report.violations}
    assert got == want
    # synth 干净态: 无违例（pads/走线/via 布点自证远离）
    empty = cva.validate_full(synth_state())
    assert empty.clean, "空态应无违例: %r" % ([v.as_dict() for v in
                                             empty.violations],)
    # 强制违例态（绕过 validate 直加边带段）: 聚合集含 edge 直调项
    st.add_seg("NET-A", "PA", "F.Cu", [[0, 4], [0, 10]], "min")
    st.recompute_connectivity()
    scene2 = _scene(st)
    check_all_v2 = drc.check_all(scene2, st.board["hard_rules"]).violations
    edge_v2 = drc.check_edge_clearance(scene2, _ws(st))
    want2 = {(v.rule, str(v.subject_a), str(v.subject_b))
             for v in list(check_all_v2) + list(edge_v2)}
    got2 = {(v.rule, str(v.subject_a), str(v.subject_b))
            for v in cva.validate_full(st).violations}
    assert got2 == want2 and want2     # 非空且逐项一致
    assert any(r == "edge_clearance" for r, _a, _b in got2)


def test_binding_gap_value_attribution():
    """归责细节绑定: V_CLEARANCE detail 的 gap 值=直调 check_clearance
    违例 data.gap_mm（round10 同值）。"""
    st = synth_state()
    wps = [[4, 16], [4, 5], [20, 5], [20, 16]]
    accepted, code, detail = cva.validate_edit(
        st, {"action": "route", "net_id": "NET-B", "waypoints": wps,
             "layer": "F.Cu"})
    assert (not accepted) and code == "V_CLEARANCE"
    cand = _cand_seg_copper(st, "NET-B", "F.Cu", wps)
    r5, _ = drc.check_clearance(
        [cand] + _scene(st), st.board["hard_rules"]["R5"]["min_clearance_mm"],
        same_net_exempt=True)
    probe = [v for v in r5 if v.subject_a == "probe:seg"
             or v.subject_b == "probe:seg"]
    assert probe, "直调未见 probe 段 R5 违例"
    assert "gap=%s" % (probe[0].data["gap_mm"],) in detail


def test_width_vocab_source_derivation():
    """词表来源绑定: 缺省表=hard_rules/partitions 推导; 显式 netclasses
    预留键优先; 非正宽度 fail-closed。"""
    board = synth_state().board
    assert cva.width_class_vocab(board) == {"min": 0.3, "nom": 0.55,
                                            "max": 0.8}
    st = synth_state()
    assert st.widths.get("NET-A", cva.default_width_class(st)) in \
        cva.width_class_vocab(board)
    explicit = dict(board)
    explicit["netclasses"] = {"thin": 0.25, "thick": 1.2}
    assert cva.width_class_vocab(explicit) == {"thin": 0.25, "thick": 1.2}
    with pytest.raises(ValueError):
        cva.width_class_vocab(dict(board, netclasses={"bad": -1}))


def test_validate_edit_placeholder_for_placements():
    """placecheck 接线（lane-m4 §5 契约，编排体 2026-09-25 收口）:
    move/rotate/flip 真实判定——合成板 PA 包络大，move 目标/rotate 翻转
    后包络越框拒 V_PLACEMENT_EDGE、flip 接受; 分区存在性=E_UNKNOWN_PARTITION
    （词表波2 追加码）; 折算单源=protocol.absolute_candidate。"""
    st = synth_state()
    assert cva.validate_edit(st, {"action": "flip",
                                  "partition_id": "PA"}) == (True, None, None)
    for action, code in (
            ({"action": "move", "partition_id": "PA", "target": [8, 8]},
             "V_PLACEMENT_EDGE"),
            ({"action": "rotate", "partition_id": "PA", "turns": 1},
             "V_PLACEMENT_EDGE"),
            ({"action": "move", "partition_id": "NOPE", "target": [8, 8]},
             "E_UNKNOWN_PARTITION")):
        got = cva.validate_edit(st, action)
        assert got[0] is False and got[1] == code, (action, got)
    # move 目标越界仍真实判（格点层先于放置判定）
    assert cva.validate_edit(st, {"action": "move", "partition_id": "PA",
                                  "target": [99, 8]}) == \
        (False, "E_GRID_OUT_OF_BOUNDS", [99, 8])
