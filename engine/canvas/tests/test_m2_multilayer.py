# -*- coding: utf-8 -*-
"""Lane-M2X 多层布线/夹具测试（test_m2_* 族共享板件构造器在本件，勿建 conftest）。

夹具板（全部经 v5.board.load_board 全校验+哈希链，仿 test_k1_fixtures 形态）:
- ``four_layer_state()``: k1 合成微板扩 stackup 至 4 信号层（F/In1/In2/B）——
  多层布线+via 过渡验证。
- ``hole_edge_state()``: 2 层板，板固孔 (5.85,5.0) 贴走线格带（track 合法/
  via 违例的 0.8≤d<0.95 环带）——V_HOLE_VIA 正例 + 衔接 via 被拒时的同层
  钉回（pin fallback）验证。
- ``ripup_state()``: 单层板，两网直连走廊必然相交（U/Z/门户绕行在
  per_net_retry 深度内都绕不开）——批量 ripup（shape_id 寻址）+ 守卫 +
  轮上限的确定性乒乓验证，终态 1 网如实 unresolved。
"""
import copy

from v5 import board as v5board

from canvas import state as cst
from canvas.tests.test_k1_fixtures import synth_state

_HARD_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}


def _finish(board):
    board["provenance"]["board_sha256"] = None
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)


def _build(board_id, board):
    lat = cst.Lattice.from_board(board)
    return cst.CanvasState(board, "<%s>" % board_id,
                           board["provenance"]["board_sha256"], lat,
                           cst.anchor_map(board, lat))


def _layer(layer_id):
    return {"id": layer_id, "kind": "signal",
            "preferred_direction": "any", "available": True}


# ------------------------------------------------------- 4 层合成板

def four_layer_board():
    """k1 合成微板（synth-k1 几何原样）扩 4 信号层。"""
    board = copy.deepcopy(synth_state().board)
    board["board_id"] = "synth-m2-4l"
    board["stackup"] = [_layer(x) for x in
                        ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")]
    return _finish(board)


def four_layer_state():
    st = _build("synth-m2-4l", four_layer_board())
    st.recompute_connectivity()
    return st


# ------------------------------------------------------- 孔环带板（2 层）

def hole_edge_board():
    """孔 (5.85,5.0) r0.4: 格点列 x=5.0 距孔心 0.85——track 禁布 0.8 合法、
    via 禁布 0.95 违例（min 档 hw=0.15、via r=0.3 时 0.8≤0.85<0.95 环带）。

    NET-X 双分区: P1 (5,4)-(5,5) 锚 (10,8)/(10,10); P2 (9,4)-(9,6) 锚
    (18,8)/(18,12)。链 (10,8)→(10,10)→(18,8)→(18,12): hop1 轮转层 B 的
    候选因衔接 via@ (10,10) 触孔被整批拒收 → 钉回 F 层候选收线。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "synth-m2-holeedge",
        "stackup": [_layer("F.Cu"), _layer("B.Cu")],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 12.0, "y_max": 10.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PX1", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[5.0, 4.0], [5.0, 5.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "PX2", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[9.0, 4.0], [9.0, 6.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
        ],
        "nets": [{"net_id": "NET-X", "partitions": ["PX1", "PX2"]}],
        "hard_rules": copy.deepcopy(_HARD_RULES),
        "holes": [{"drill_mm": 0.8, "plated": True,
                   "pos_mm": [5.85, 5.0], "shape": "circle"}],
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "m2-fixture",
                       "source_sha256": "0" * 64, "adapter": "canvas-m2",
                       "board_sha256": None},
    }
    return _finish(board)


def hole_edge_state():
    st = _build("synth-m2-holeedge", hole_edge_board())
    st.recompute_connectivity()
    return st


# ------------------------------------------------------- 单层 ripup 板

def ripup_board():
    """单层板: NET-A 行走廊 (2,4)-(10,4) 与 NET-B 列走廊 (6,1)-(6,7) 必然
    相交; per_net_retry=6 深度内 U/Z/门户绕行均绕不开对方全跨度走廊
    （行 x∈[2,10] / 列 y∈[1,7] 贯穿）→ 每网唯一出路=拆对方段。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "synth-m2-ripup",
        "stackup": [_layer("F.Cu")],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 12.0, "y_max": 8.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PR-A", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 4.0], [10.0, 4.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "PR-B", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[6.0, 1.0], [6.0, 7.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
        ],
        "nets": [
            {"net_id": "NET-A", "partitions": ["PR-A"]},
            {"net_id": "NET-B", "partitions": ["PR-B"]},
        ],
        "hard_rules": copy.deepcopy(_HARD_RULES),
        "holes": [],
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "m2-fixture",
                       "source_sha256": "0" * 64, "adapter": "canvas-m2",
                       "board_sha256": None},
    }
    return _finish(board)


def ripup_state():
    st = _build("synth-m2-ripup", ripup_board())
    st.recompute_connectivity()
    return st


# ================================================================ 测试

def test_four_layer_all_nets_connected_with_via_transitions():
    from canvas.runners.m2 import run_m2
    st = four_layer_state()
    summary = run_m2(st)
    assert summary["unresolved_nets"] == []
    assert summary["nets_connected_after"] == ["NET-A", "NET-B", "NET-C"]
    assert summary["rejected_count"] == 0
    # 多层: NET-C 各跳落在 ≥2 个不同信号层
    layers_used = sorted({st.segs[sid]["layer"] for sid in st.segs
                          if st.segs[sid]["net_id"] == "NET-C"})
    assert len(layers_used) >= 2, layers_used
    assert layers_used == ["B.Cu", "F.Cu", "In2.Cu"]  # 轮转 (2,3,0)%4
    # via 过渡: 双分区链两个衔接点各有 via 在场（画板纪律）
    via_grids = sorted(tuple(v["grid"]) for v in st.vias.values()
                       if v["net_id"] == "NET-C")
    assert via_grids == [(6, 10), (22, 10)], via_grids
    assert summary["via_cost_facts"]["vias_applied"] >= 2
    assert summary["via_cost_facts"]["vias_by_net"] == {"NET-C": 2}


def test_two_layer_synth_cross_layer_junction_via():
    """2 层 k1 合成板: NET-C 双分区链跨 F/B 层+衔接 via（波1 夹具复用）。"""
    from canvas.runners.m2 import run_m2
    st = synth_state()
    summary = run_m2(st)
    assert summary["unresolved_nets"] == []
    layers_used = sorted({st.segs[sid]["layer"] for sid in st.segs
                          if st.segs[sid]["net_id"] == "NET-C"})
    assert layers_used == ["B.Cu", "F.Cu"]
    assert summary["via_cost_facts"]["vias_applied"] >= 1
    assert summary["via_cost_facts"]["vias_by_net"].get("NET-C", 0) >= 1
    # via 在场纪律: 每个 via 都落在本网某段 waypoint 上
    for v in st.vias.values():
        on_path = any(
            any(tuple(p) == tuple(v["grid"]) for p in seg["grid"])
            for seg in st.segs.values()
            if seg["net_id"] == v["net_id"])
        assert on_path, v


def test_junction_via_hole_rejected_pins_to_same_layer():
    """孔环带板: 轮转层的衔接 via 触孔被拒 → 钉回前跳层仍连通（0 via）。"""
    from canvas.runners.m2 import run_m2
    st = hole_edge_state()
    summary = run_m2(st)
    assert summary["unresolved_nets"] == []
    assert st.connectivity["NET-X"] is True
    # 钉回证据: 全链单层、衔接 via 一个都没落（环带内 via 全被 V_HOLE_VIA 拒）
    assert len(st.segs) == 3
    assert {seg["layer"] for seg in st.segs.values()} == {"F.Cu"}
    assert summary["via_cost_facts"]["vias_applied"] == 0
    assert len(st.vias) == 0


def test_single_layer_ripup_pingpong_bounded_and_honest():
    """单层板: 走廊互锁 → 批量 ripup（shape_id 寻址）+ 守卫/轮上限封顶,
    终态 1 网连通、1 网如实 unresolved（确定性乒乓奇偶）。"""
    from canvas.runners.m2 import plan_actions, run_m2
    st = ripup_state()
    planned = plan_actions(st)
    ripup_shape = [a for a in planned
                   if a["action"] == "ripup" and "shape_id" in a]
    assert len(ripup_shape) >= 2, "应有跨网阻塞拆段（shape_id 寻址）"
    owners = set()
    for a in ripup_shape:
        assert a["shape_id"].startswith(("seg:", "via:"))
    summary = run_m2(st)
    assert summary["rejected_count"] == 0
    # 轮上限=3: R1 A 连通→B 拆 A 连通; R2 A 拆 B 连通; R3 B 拆 A 连通 → A 未连通
    assert summary["nets_connected_after"] == ["NET-B"]
    assert summary["unresolved_nets"] == ["NET-A"]
    assert summary["via_cost_facts"]["vias_applied"] == 0  # 单层无 via 候选


def test_hop_candidates_include_via_corner_and_deterministic():
    """候选发生器单元: 4 层板含跨层 via 角过渡（route/via/route 原子组）,
    生成确定性（两次生成 canonical 字节等）、键集符合合同 §2。"""
    from v5.canonical import canonical_json
    from canvas import protocol as cproto
    from canvas.runners.m2 import _hop_candidates
    st = four_layer_state()
    layers = st.signal_layers()
    assert layers == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    cands1 = _hop_candidates("NET-A", (4, 4), (20, 16), layers, 0, 3,
                             st.lattice)
    cands2 = _hop_candidates("NET-A", (4, 4), (20, 16), layers, 0, 3,
                             st.lattice)
    assert canonical_json(cands1) == canonical_json(cands2)
    via_corners = [c for c in cands1
                   if [a["action"] for a in c] == ["route", "via", "route"]]
    assert via_corners, "4 层板必须含跨层 via 角候选"
    for cand in via_corners:
        la, lb = cand[0]["layer"], cand[2]["layer"]
        assert la != lb
        assert cand[1]["grid"] == cand[0]["waypoints"][-1]
        assert cand[1]["grid"] == cand[2]["waypoints"][0]
    for cand in cands1:
        for a in cand:
            assert set(a) <= cproto.ALLOWED_KEYS[a["action"]]
            for w in a.get("waypoints", []) + ([a["grid"]]
                                               if "grid" in a else []):
                assert all(isinstance(x, int) and not isinstance(x, bool)
                           for x in w)
                assert st.lattice.in_bounds(*w)


def test_planned_actions_are_valid_protocol_batches():
    """runner 规划输出=合法 canvas-edit-v2 批（键集/格点纪律/parse 可过）。"""
    import json
    from canvas import protocol as cproto
    from canvas.runners.m2 import plan_actions
    for factory in (synth_state, four_layer_state, hole_edge_state,
                    ripup_state):
        st = factory()
        planned = plan_actions(st)
        for a in planned:
            assert a["action"] in cproto.REQUIRED_KEYS
            assert set(a) <= cproto.ALLOWED_KEYS[a["action"]]
        doc = json.dumps({"round": 1,
                          "actions": planned + [{"action": "submit"}]})
        acts = cproto.parse_batch(doc, 1)
        assert acts[-1]["action"] == "submit"
        assert len(acts) == len(planned) + 1
