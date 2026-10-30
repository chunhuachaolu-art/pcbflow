# -*- coding: utf-8 -*-
"""Lane-K1 instantiate 测试: 曼哈顿直连无搜索/制造格点贴合/stub 端点对齐/
placement pad 场/tuning 参数化几何/anchors_mm/kicad 导出可消费。"""
import json

from v5 import drc
from v5 import kicad_export

from canvas import instantiate as cin
from canvas import state as cst
from canvas import validate as cva
from canvas.tests.test_k1_fixtures import (
    synth_state, run_batch, apply_ok)


def test_manhattan_l_shape_corner_on_grid():
    assert cin.manhattan((0, 0), (3, 2)) == [(0, 0), (3, 0), (3, 2)]
    assert cin.manhattan((3, 2), (0, 0)) == [(3, 2), (0, 2), (0, 0)]
    assert cin.manhattan((1, 1), (5, 1)) == [(1, 1), (5, 1)]     # 对齐退化
    assert cin.manhattan((2, 2), (2, 2)) == [(2, 2)]             # 重合
    # 拐点必在格点上（整数对）
    for a, b in (((0, 0), (7, 5)), ((-3, 4), (6, -2))):
        for p in cin.manhattan(a, b):
            assert isinstance(p[0], int) and isinstance(p[1], int)


def test_expand_waypoints_dedup_and_monotone_legs():
    pts = cin.expand_waypoints([[0, 0], [3, 2], [3, 5]])
    assert pts == [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2),
                   (3, 3), (3, 4), (3, 5)]
    assert cin.expand_waypoints([[2, 2], [2, 2]]) == [(2, 2)]    # 自绞→单点
    assert cin.expand_waypoints([[0, 0], [0, 0], [1, 0]]) == [(0, 0), (1, 0)]


def test_manhattan_is_straight_connection_no_search():
    """无搜索无绕障: 路径点数=2(直)/3(拐)，总步长=曼哈顿距离。"""
    for a, b in (((0, 0), (4, 0)), ((0, 0), (0, 4)), ((1, 1), (6, 3)),
                 ((5, 5), (2, 9))):
        path = cin.manhattan(a, b)
        steps = sum(abs(p[0] - q[0]) + abs(p[1] - q[1])
                    for p, q in zip(path[:-1], path[1:]))
        assert steps == abs(a[0] - b[0]) + abs(a[1] - b[1])
        assert len(path) <= 3


def test_segment_mm_manufacturing_grid_and_stubs():
    st = synth_state()
    apply_ok(st, [{"action": "route", "net_id": "NET-A",
                   "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}])
    seg = st.segs["seg:NET-A:0"]
    pts, stub = cin.segment_mm(st, seg)
    # 贴制造格点: 除绑定腿端点外全部格点 mm
    lat = st.lattice
    for p in pts:
        assert p == lat.to_mm(*lat.snap(*p)) or p in [(2.0, 2.0), (10.0, 2.0)]
    # 首末点=分区真实端点（本夹具锚==端点 → 折线与格点重合）
    assert pts[0] == (2.0, 2.0) and pts[-1] == (10.0, 2.0)
    # V6-ANCHOR-R1 口径 v2: 绑定腿结构性在场（零位移时=首/末单位步,
    # stub_range 标记信息面; 旧口径零位移 stub=None 已废）
    assert stub == {"head": (0, 1), "tail": (15, 16)}


def test_segment_mm_stub_generated_when_anchor_differs():
    """端点不落格点时绑定腿=真端点直连（口径 v2: 双端绑定无 body →
    两真实端点 L 直连, 先 x 后 y; 锚格 mm (2.5,2.5) 不进物理铜）。"""
    import copy
    st = synth_state()
    board = copy.deepcopy(st.board)
    board["partitions"][0]["geometry"]["endpoints"] = [[2.4, 2.3], [10.0, 2.0]]
    prov = dict(board["provenance"])
    prov.pop("board_sha256", None)
    board["provenance"] = prov
    from v5 import board as v5board
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    st.board = v5board.load_board(board)
    st.anchors = cst.anchor_map(st.board, st.lattice)   # (5,5)-(20,4)
    st.recompute_connectivity()
    seg = st.add_seg("NET-A", "PA", "F.Cu", [[5, 5], [20, 4]], "min")
    pts, stub = cin.segment_mm(st, seg)
    assert stub["head"] == (0, 2) == stub["tail"]   # 双端绑定单腿（直连）
    assert pts[0] == (2.4, 2.3)
    assert (2.5, 2.5) not in pts                    # 锚格 mm 不进物理铜
    assert pts[1] == (10.0, 2.3) and pts[2] == (10.0, 2.0)   # 先 x 后 y L 形


def test_instantiate_shapes_and_anchors_mm():
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": 1.0}},
    ])
    inst = cin.instantiate(st)
    # coppers: 4 分区×2 端点×2 层 pads=16 + seg2 + via×2 层 + tuning1 = 21
    kinds = [cu.cid.split(":")[0] for cu in inst["coppers"]]
    assert kinds.count("pad") == 16
    assert sorted(c.cid for c in inst["coppers"] if c.cid.startswith("seg")) \
        == ["seg:NET-A:0", "seg:NET-A:1"]
    assert len([c for c in inst["coppers"] if c.cid == "via:NET-A:12_4"]) == 2
    assert len([c for c in inst["coppers"] if c.cid == "tun:NET-A:g:0"]) == 1
    assert all(isinstance(c, drc.Copper) for c in inst["coppers"])
    # routes: 每段一行、kicad _validate 消费形态（EXPORT-SEMANTICS-R1 起
    # 行可带可选 transition_vias 点表；本夹具画板 via (12,4) 归 NET-A 首行）
    assert [r["layer"] for r in inst["routes"]] == ["F.Cu", "B.Cu"]
    base_keys = {"partition_id", "net_id", "layer", "polyline", "width"}
    for r in inst["routes"]:
        assert base_keys <= set(r)
        assert set(r) - base_keys <= {"transition_vias"}
        assert r["partition_id"] == "PA" and r["net_id"] == "NET-A"
        assert len(r["polyline"]) >= 2 and r["width"] > 0
        for p in r["polyline"]:
            assert len(p) == 2
    assert inst["routes"][0]["transition_vias"] == [[6.0, 2.0]]
    assert "transition_vias" not in inst["routes"][1]
    # anchors_mm: 覆盖后端点锚 mm（无覆盖=构造锚）
    assert inst["anchors_mm"]["PA"] == [[2.0, 2.0], [10.0, 2.0]]
    # holes_norm 同源
    assert inst["holes_norm"] == drc.normalize_holes(st.board["holes"])


def test_routes_consumable_by_kicad_export_real_board():
    """真板: routes_document → kicad_pcb_bytes 直食（导出器合同自证）。"""
    from canvas.tests.test_k1_fixtures import real_state
    st = real_state()
    net = "Net-(D2-Pad1)"
    apply_ok(st, [
        {"action": "route", "net_id": net,
         "waypoints": [[27, 31], [27, 25], [55, 25]], "layer": "F.Cu"},
        {"action": "width_class", "net_id": net, "class": "max"},
    ])
    inst = cin.instantiate(st)
    assert len(inst["routes"]) == 1
    doc = cin.routes_document(st, inst)
    assert doc["schema_version"] == "v5.routes.v1"
    assert doc["board_sha256"] == st.board_sha256
    data = kicad_export.kicad_pcb_bytes(st.board, doc)
    assert b"(segment" in data
    pro = kicad_export.project_kicad_pro_bytes(st.board, doc)
    assert pro


def test_tuning_geometry_parametric():
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
    ])
    base = cin.grid_path_mm(st, cin.expand_waypoints([[4, 4], [20, 4]]))
    # accordion: n 个矩形折返，幅度=amp（基线 y=2 + 1.0）
    acc = {"shape_id": "t", "net_id": "NET-A", "group_id": "g",
           "kind": "accordion", "grid": [[4, 4], [20, 4]],
           "params": {"amp_mm": 1.0, "count": 3}}
    pts = cin.tuning_polyline_mm(st, acc)
    assert pts[0] == base[0] and pts[-1] == base[-1]
    assert len(pts) > len(base)                     # 折返点确有插入
    apex = [p for p in pts if abs(p[1] - 3.0) < 1e-9]
    assert len(apex) == 2 * 3                       # 每折返 2 顶线点(起/落)
    assert all(p[1] in (2.0, 3.0) for p in pts)     # 只在基线/顶线之间
    assert all(a != b for a, b in zip(pts[:-1], pts[1:]))   # 无重复点
    # detour: 最长腿侧移 offset（并列取首腿）
    det = {"shape_id": "t", "net_id": "NET-A", "group_id": "g",
           "kind": "detour", "grid": [[4, 4], [20, 4]],
           "params": {"offset_mm": 1.5}}
    pts2 = cin.tuning_polyline_mm(st, det)
    assert pts2[0] == base[0] and pts2[-1] == base[-1]
    assert any(abs(p[1] - 3.5) < 1e-9 for p in pts2)   # y=2+1.5 侧移点
    assert all(p[1] in (2.0, 3.5) for p in pts2)
    assert all(a != b for a, b in zip(pts2[:-1], pts2[1:]))


def test_placement_moves_pads_and_anchors():
    st = synth_state()
    st.set_placement("PA", move=[8, 8])       # 中心 (6,2)mm → to_mm(8,8)=(4,4)mm
    inst = cin.instantiate(st)
    pads = [c for c in inst["coppers"] if c.cid.startswith("pad:PA:")]
    assert pads
    centers = set()
    for c in pads:                            # pad 场跟随覆盖后位置
        x0, y0, x1, y1 = c.as_rect()
        centers.add((round((x0 + x1) / 2.0, 9), round((y0 + y1) / 2.0, 9)))
    assert centers == {(0.0, 4.0), (8.0, 4.0)}   # (2,2)/(10,2)+delta(-2,+2)
    assert inst["anchors_mm"]["PA"] == [[0.0, 4.0], [8.0, 4.0]]
    # 覆盖记录入 facts（序列化确定性）
    assert cst.state_facts(st)["placements"]["PA"]["move"] == [8, 8]


def test_instantiate_determinism_double_run():
    from canvas.tests.test_k1_fixtures import synth_state as fresh
    actions = [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "accordion", "params": {"amp_mm": 0.8, "count": 2}},
    ]
    outs = []
    for _ in range(2):
        st = fresh()
        apply_ok(st, actions)
        inst = cin.instantiate(st)
        outs.append({
            "coppers": [(c.net_id, c.cid, c.layer,
                         [(round(p[0], 9), round(p[1], 9)) for p in
                          (c.polyline or [])],
                         c.pad and (round(c.pad[0][0], 9),
                                    round(c.pad[0][1], 9), c.pad[1]),
                         c.band and tuple(round(x, 9) for x in c.band),
                         c.half_width) for c in inst["coppers"]],
            "routes": inst["routes"],
            "holes": inst["holes_norm"],
            "anchors": inst["anchors_mm"],
        })
    assert json.dumps(outs[0], sort_keys=True) == \
        json.dumps(outs[1], sort_keys=True)
