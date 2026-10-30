# -*- coding: utf-8 -*-
"""Lane-M2X v5.drc 绑定一致测试: run_m2 接受的 plan 在终态上 validate_full
（v5.drc.check_all 同源聚合）对照断言——无新增违例/逐违例归责/谓词同源
双向（正例+反例），含跨层 via 的 hole_via_blocked 绑定。

判定单源纪律: 一切几何断言经 canvas.validate / v5.drc 公有谓词直调，
本件零平行几何实现。计数 10 ≥ 合同下限 8。
"""
from v5 import drc
from v5.canonical import canonical_json
from v5.kicad_export import via_model_params

from canvas import instantiate as cinst
from canvas import validate as cval
from canvas.runners.m2 import run_m2
from canvas.tests.test_k1_fixtures import synth_state, run_batch, real_state
from canvas.tests.test_m2_multilayer import four_layer_state, hole_edge_state


def _vkeys(report):
    return set(canonical_json(v.as_dict()) for v in report.violations)


def _new_keys(base, final):
    return _vkeys(final) - _vkeys(base)


# ------------------------------------------------------- 无新增违例

def test_synth_run_m2_no_new_violations():
    base = cval.validate_full(synth_state())
    assert base.clean, "k1 合成微板基场景应全净"
    st = synth_state()
    run_m2(st)
    final = cval.validate_full(st)
    assert final.clean, [v.as_dict() for v in final.violations]


def test_real_badgeleds_run_m2_no_new_violations():
    """badgeleds 2 层实测: 终态违例键集 ⊆ 基场景键集（板固有 pad 对不归责
    runner——差集归责纪律与 v5.route_check 同构）。"""
    base_state = real_state()
    base = cval.validate_full(base_state)
    assert not base.clean, "badgeleds 基场景应含板固有 pad 对违例"
    st = real_state()
    summary = run_m2(st)
    final = cval.validate_full(st)
    assert _new_keys(base, final) == set()
    # 板固有违例原样保留（不静默吞、不新增）
    assert _vkeys(base) <= _vkeys(final)
    assert len(summary["unresolved_nets"]) == 2  # 板固有 pad 拥挤网（REPORT 归因）


def test_four_layer_run_m2_no_new_violations():
    st = four_layer_state()
    assert cval.validate_full(st).clean
    run_m2(st)
    assert cval.validate_full(st).clean


# ------------------------------------------------------- check_all 同源

def test_validate_full_is_drc_check_all_same_source():
    """validate_full 的 check_all 段与直调 v5.drc.check_all（同输入自公有缝
    复构）逐违例相等; 段外只允许 edge/hole 聚合（validate_full 口径）。"""
    st = synth_state()
    run_m2(st)
    coppers = cinst.instantiate(st)["coppers"]
    sensitive, keepout = cval.zone_rects(st.board)
    width_checks = []
    for net_id in sorted(st.known_nets()):
        has_cu = (any(s["net_id"] == net_id for s in st.segs.values())
                  or any(v["net_id"] == net_id for v in st.vias.values()))
        if has_cu:
            w = cval.net_width(st, net_id,
                               st.widths.get(net_id,
                                             cval.default_width_class(st)))
            width_checks.append((net_id, w,
                                 float(st.board["hard_rules"]["R1"]["floor_mm"])))
    direct = drc.check_all(coppers, st.board["hard_rules"],
                           sensitive_rects=sensitive, keepout_rects=keepout,
                           width_checks=width_checks)
    report = cval.validate_full(st)
    assert report.drc_version == drc.VERSION
    head = [v.as_dict() for v in report.violations[:len(direct.violations)]]
    assert head == [v.as_dict() for v in direct.violations]
    tail = report.violations[len(direct.violations):]
    assert all(v.rule in ("edge_clearance", "hole_to_hole") for v in tail)


# ------------------------------------------------------- 谓词同源双向

def test_hole_track_predicate_binding_positive():
    """V_HOLE_TRACK 拒收 ↔ drc.hole_track_blocked 同一几何为真（正例）。"""
    st = synth_state()
    action = {"action": "route", "net_id": "NET-C",
              "waypoints": [[6, 10], [22, 10]], "layer": "F.Cu"}
    ok, code, _detail = cval.validate_edit(st, action)
    assert (ok, code) == (False, cval._p.V_HOLE_TRACK)
    holes = drc.normalize_holes(st.board.get("holes"))
    hw = cval.net_width(st, "NET-C", "min") / 2.0
    pts = cinst.grid_path_mm(st, [(6, 10), (22, 10)])
    blocked = [hi for hi, (hx, hy, hr) in enumerate(holes)
               if any(drc.hole_track_blocked((hx, hy), hr, a, b, hw)
                      for a, b in zip(pts[:-1], pts[1:]))]
    assert blocked == [0], blocked


def test_hole_via_predicate_binding_positive_and_negative():
    """V_HOLE_VIA 拒收 ↔ drc.hole_via_blocked 同一几何为真; 环带外 via
    （合法走线上）谓词为假且 validate 放行——跨层 via 的孔绑定双向。"""
    st = hole_edge_state()
    run_batch(st, [{"action": "route", "net_id": "NET-X",
                    "waypoints": [[10, 8], [10, 10]], "layer": "F.Cu"}])
    holes = drc.normalize_holes(st.board.get("holes"))
    vm = via_model_params(st.board)
    mm_blocked = st.lattice.to_mm(10, 10)
    assert drc.hole_via_blocked(holes[0][:2], holes[0][2], mm_blocked,
                                vm["radius"]) is True
    ok, code, _ = cval.validate_edit(
        st, {"action": "via", "net_id": "NET-X", "grid": [10, 10]})
    assert (ok, code) == (False, cval._p.V_HOLE_VIA)
    # 反例: 同段上远离孔的格点 (10,8) mm=(5,4) 距孔心 1.05 ≥ 0.95
    mm_clear = st.lattice.to_mm(10, 8)
    assert drc.hole_via_blocked(holes[0][:2], holes[0][2], mm_clear,
                                vm["radius"]) is False
    ok2, code2, _ = cval.validate_edit(
        st, {"action": "via", "net_id": "NET-X", "grid": [10, 8]})
    assert ok2 is True, code2


def test_cross_layer_via_hole_binding_on_4l_final_state():
    """4 层终态: 全部在场 via 对全部板固孔的 hole_via_blocked 谓词为假,
    validate_full 无 hole_to_hole 违例（跨层 via 绑定同源核验）。"""
    st = four_layer_state()
    run_m2(st)
    assert st.vias, "4 层夹具应有衔接 via"
    holes = drc.normalize_holes(st.board.get("holes"))
    vm = via_model_params(st.board)
    for v in st.vias.values():
        mm = st.lattice.to_mm(*v["grid"])
        for hx, hy, hr in holes:
            assert drc.hole_via_blocked((hx, hy), hr, mm, vm["radius"]) is False
    report = cval.validate_full(st)
    assert not [v for v in report.violations if v.rule == "hole_to_hole"]


# ------------------------------------------------------- 逐违例归责

def test_violation_attribution_per_pair():
    """逐违例归责: 注入一条横穿 NET-A 段的 NET-B 列段（state 公有缝
    add_seg，不经 validate; v5.drc R5 折线对=中心线间距——0.5 格邻行恰
    合规、交叉=0 违例，故取交叉形态）→ validate_full 新增 R5 恰归责
    该对（subjects 一一对应注入段与既有段）。"""
    st = synth_state()
    run_m2(st)
    base = cval.validate_full(st)
    st.add_seg("NET-B", "PB", "F.Cu",
               cinst.expand_waypoints([[12, 2], [12, 7]]), "min")
    st.recompute_connectivity()
    final = cval.validate_full(st)
    new = [v for v in final.violations
           if canonical_json(v.as_dict()) not in _vkeys(base)]
    injected = [sid for sid in st.segs
                if st.segs[sid]["net_id"] == "NET-B"
                and st.segs[sid]["grid"][0] == [12, 2]]
    assert len(injected) == 1
    assert len(new) == 1, [v.as_dict() for v in new]
    v = new[0]
    assert v.rule == "R5"
    assert {v.subject_a, v.subject_b} == {injected[0], "seg:NET-A:0"}
    assert v.data["layer"] == "F.Cu"
    assert v.data["gap_mm"] == 0.0


def test_same_net_exempt_no_new_violation():
    """同网豁免绑定: 与本网既有段完全重叠的同网第二段不产生 R5
    （check_clearance same_net_exempt=True 同源口径）。"""
    st = synth_state()
    run_m2(st)
    base = cval.validate_full(st)
    st.add_seg("NET-A", "PA", "F.Cu",
               cinst.expand_waypoints([[4, 4], [20, 4]]), "min")
    st.recompute_connectivity()
    final = cval.validate_full(st)
    assert _new_keys(base, final) == set()


# ------------------------------------------------------- 宽度/板边绑定

def test_width_class_binding_matches_r1_floor():
    """每规划网 width_class="min" 落档 + drc.check_width（R1 载流下限谓词
    同源直调）逐网全净; 词表下界 ≥ floor 由 validate.vocab 单源保证。"""
    st = synth_state()
    summary = run_m2(st)
    vocab = cval.width_class_vocab(st.board)
    floor = float(st.board["hard_rules"]["R1"]["floor_mm"])
    assert min(vocab.values()) >= floor
    for net_id in st.widths:
        assert st.widths[net_id] in vocab
        w = cval.net_width(st, net_id, st.widths[net_id])
        assert drc.check_width(w, floor, net_id) is None
    assert summary["via_cost_facts"]["vias_by_net"]  # synth 有衔接 via


def test_edge_clearance_binding_positive():
    """V_EDGE 绑定: 贴板边（y=0 < 边带 0.2mm）注入段在 validate_full 报
    edge_clearance 且 drc.check_edge_clearance 直调同报（同源正例）。"""
    st = synth_state()
    run_m2(st)
    base = cval.validate_full(st)
    seg = st.add_seg("NET-B", "PB", "F.Cu",
                     cinst.expand_waypoints([[4, 0], [20, 0]]), "min")
    st.recompute_connectivity()
    final = cval.validate_full(st)
    new = [v for v in final.violations
           if canonical_json(v.as_dict()) not in _vkeys(base)]
    assert new and all(v.rule == "edge_clearance" for v in new)
    assert all(seg["shape_id"] in (v.subject_a, v.subject_b) for v in new)
    ws = cval.ws_tuple(st.board)
    direct = [v for v in drc.check_edge_clearance(cinst.instantiate(st)["coppers"], ws)
              if v.subject_a == seg["shape_id"]]
    assert direct, "直调 check_edge_clearance 应同报该段"
