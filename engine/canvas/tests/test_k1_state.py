# -*- coding: utf-8 -*-
"""Lane-K1 state 测试: Lattice 语义/锚冲突 fail-closed/shape_id 规范/
连通账本纪律/placement 覆盖变换/序列化确定性（双跑字节等）。"""
import json
import math

import pytest

from v5 import canonical

from canvas import state as cst
from canvas.tests.test_k1_fixtures import (
    real_state, synth_state, run_batch, apply_ok)


# ---------------------------------------------------------------- Lattice

def test_lattice_origin_and_coverage():
    st = synth_state()
    lat = st.lattice
    assert lat.pitch == 0.5
    # origin = floor(workspace 下界/pitch)*pitch（下界外对齐，覆盖板框）
    assert lat.x0 == 0.0 and lat.y0 == 0.0
    assert lat.i_max == 28 and lat.j_max == 20     # 14/0.5, 10/0.5
    assert lat.in_bounds(0, 0) and lat.in_bounds(28, 20)
    assert not lat.in_bounds(-1, 0) and not lat.in_bounds(0, 21)
    assert lat.to_mm(4, 4) == (2.0, 2.0)
    assert lat.snap(2.24, 2.0) == (4, 4)           # 最近格点
    assert lat.snap(2.26, 2.0) == (5, 4)
    d = lat.as_dict()
    assert cst.Lattice.from_dict(d).as_dict() == d


def test_lattice_origin_floor_on_real_board():
    st = real_state()
    lat = st.lattice
    ws = st.board["workspace"]
    assert lat.x0 == math.floor(ws["x_min"] / 0.5) * 0.5
    assert lat.y0 == math.floor(ws["y_min"] / 0.5) * 0.5
    # 格点域覆盖板框: 右上角格点 mm ≥ workspace 上界−pitch
    mx, my = lat.to_mm(lat.i_max, lat.j_max)
    assert mx >= ws["x_max"] - 0.5 and my >= ws["y_max"] - 0.5


def test_anchor_map_and_conflict_fail_closed():
    st = synth_state()
    assert st.anchors["PA"] == [[4, 4], [20, 4]]
    assert st.anchors["PB"] == [[4, 16], [20, 16]]
    assert st.anchors["PC1"] == [[22, 10], [26, 10]]
    assert st.anchors["PC2"] == [[2, 10], [6, 10]]
    # 锚冲突 fail-closed: PB 端点改到 PA 端点上
    board = json.loads(json.dumps(st.board))
    board["partitions"][1]["geometry"]["endpoints"][0] = [2.0, 2.0]
    board["provenance"].pop("board_sha256", None)
    lat = cst.Lattice.from_board(board)
    with pytest.raises(cst.LatticeError):
        cst.anchor_map(board, lat)
    # 端点锚越界 fail-closed
    board2 = json.loads(json.dumps(st.board))
    board2["partitions"][1]["geometry"]["endpoints"][0] = [99.0, 99.0]
    board2["provenance"].pop("board_sha256", None)
    with pytest.raises(cst.LatticeError):
        cst.anchor_map(board2, cst.Lattice.from_board(board2))


# ---------------------------------------------------------------- 图元/账本

def test_shape_id_norms():
    st = synth_state()
    seg = st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [20, 4]], "min")
    via = st.add_via("NET-A", [12, 4])
    tun = st.add_tuning("NET-A", "g1", "detour", [[4, 4], [20, 4]],
                        {"offset_mm": 1.0})
    assert seg["shape_id"] == "seg:NET-A:0"
    assert via["shape_id"] == "via:NET-A:12_4"
    assert tun["shape_id"] == "tun:NET-A:g1:0"
    assert st.add_tuning("NET-A", "g1", "detour", [], {"offset_mm": 1.0})[
        "shape_id"] == "tun:NET-A:g1:1"
    assert st.add_tuning("NET-A", "g2", "detour", [], {"offset_mm": 1.0})[
        "shape_id"] == "tun:NET-A:g2:0"


def test_connectivity_single_seg_and_junction_discipline():
    st = synth_state()
    apply_ok(st, [{"action": "route", "net_id": "NET-A",
                   "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}])
    assert st.connectivity["NET-A"] is True
    # 两段在同格点衔接但无 via → 纪律 fail-closed（不连通 + 账本记录）。
    # （协议路径下无 via 的第二段会被附着纪律拒收，故经 state API 直落，
    #  验证账本纪律本身对无 via 衔接的判定。）
    st2 = synth_state()
    st2.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [12, 4]], "min")
    st2.add_seg("NET-A", "PA", "F.Cu", [[12, 4], [20, 4]], "min")
    st2.recompute_connectivity()
    assert st2.connectivity["NET-A"] is False
    assert st2.chain_detail["NET-A"]["junctions_missing_via"] == [[12, 4]]
    # 补 via 后连通（段衔接点有 via 在场）
    st2.add_via("NET-A", [12, 4])
    st2.recompute_connectivity()
    assert st2.connectivity["NET-A"] is True


def test_connectivity_multi_partition_net():
    st = synth_state()
    # NET-C 双分区: 单段只接通 2/4 端点锚 → 不连通; 每分区各一段+via 衔接后连通
    apply_ok(st, [
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[26, 10], [24, 13], [4, 13], [2, 10]], "layer": "F.Cu"},
    ])
    assert st.connectivity["NET-C"] is False
    assert st.chain_detail["NET-C"]["terminals"] == [
        [2, 10], [6, 10], [22, 10], [26, 10]]
    # PC1 内部段 + via @ (24,13) + 主干段（两端锚为 via/锚）→ 4 锚同分量
    apply_ok(st, [
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[22, 10], [24, 13]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[6, 10], [4, 13]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-C", "grid": [24, 13]},
        {"action": "via", "net_id": "NET-C", "grid": [4, 13]},
    ])
    assert st.connectivity["NET-C"] is True


def test_dangling_seg_breaks_chain_and_gc():
    st = synth_state()
    # 合法两段链（中点 via 衔接）→ 连通
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
    ])
    assert st.connectivity["NET-A"] is True
    # 拆末段: via 仍在首段路径上（保留），但锚 (20,4) 不可达 → 不连通
    apply_ok(st, [{"action": "ripup", "shape_id": "seg:NET-A:1"}], round_no=2)
    assert any(v["grid"] == [12, 4] for v in st.vias.values())
    assert st.connectivity["NET-A"] is False
    assert st.chain_detail["NET-A"]["dangling_segs"] == []
    # 再拆 via（显式）→ 首段尾点失去衔接 → 悬空段
    apply_ok(st, [{"action": "ripup", "shape_id": "via:NET-A:12_4"}],
             round_no=3)
    assert not st.vias
    assert st.connectivity["NET-A"] is False
    assert st.chain_detail["NET-A"]["dangling_segs"] == ["seg:NET-A:0"]
    # 悬空 via 的 gc: 拆掉唯一途经段后，via 不在任何段上 → 被清
    st2 = synth_state()
    apply_ok(st2, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
    ])
    apply_ok(st2, [{"action": "ripup", "shape_id": "seg:NET-A:0"}], round_no=2)
    assert st2.vias == {}


def test_width_class_restamp_invariant():
    st = synth_state()
    apply_ok(st, [{"action": "route", "net_id": "NET-A",
                   "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}])
    apply_ok(st, [{"action": "width_class", "net_id": "NET-A",
                   "class": "max"}])
    assert st.widths["NET-A"] == "max"
    assert all(s["width_class"] == "max"
               for s in st.segs.values() if s["net_id"] == "NET-A")


def test_placement_coverage_transform():
    st = synth_state()
    base_mm = st.effective_endpoint_mm("PA")
    assert base_mm == [(2.0, 2.0), (10.0, 2.0)]        # 无覆盖=原位
    assert st.effective_anchors("PA") == [[4, 4], [20, 4]]
    # rotate 2 turns（180°）: 端点互换（绕中心 (6,2)）
    st.set_placement("PA", rotate=2)
    assert st.effective_endpoint_mm("PA") == [(10.0, 2.0), (2.0, 2.0)]
    st.set_placement("PA", rotate=0)
    # flip（x 镜像）: 同上互换
    st.set_placement("PA", flip=True)
    assert st.effective_endpoint_mm("PA") == [(10.0, 2.0), (2.0, 2.0)]
    st.set_placement("PA", flip=False)
    # move（中心平移到目标格点 mm）+ 覆盖字段合成序 rotate→flip→move
    st.set_placement("PA", move=[24, 8])
    cx = (st.effective_endpoint_mm("PA")[0][0]
          + st.effective_endpoint_mm("PA")[1][0]) / 2.0
    cy = (st.effective_endpoint_mm("PA")[0][1]
          + st.effective_endpoint_mm("PA")[1][1]) / 2.0
    assert (cx, cy) == st.lattice.to_mm(24, 8)
    # 覆盖后锚=重新 snap 的格点
    st.set_placement("PA", move=[24, 8], rotate=1)
    assert all(len(a) == 2 and isinstance(a[0], int)
               for a in st.effective_anchors("PA"))
    # facts 中 placements 覆盖记录
    cov = cst.state_facts(st)["placements"]["PA"]
    assert cov == {"move": [24, 8], "rotate": 1, "flip": False}


# ---------------------------------------------------------------- 序列化/确定性

def _mixed_sequence(st):
    """同一动作序列（含接受与拒收）在任意 fresh state 上重放。"""
    return [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
        {"action": "width_class", "net_id": "NET-A", "class": "nom"},
        {"action": "route", "net_id": "NET-B",           # 拒收: 附着违例
         "waypoints": [[4, 16], [4, 5], [20, 5], [20, 16]], "layer": "F.Cu"},
        {"action": "move", "partition_id": "PA", "target": [8, 8]},  # 占位拒收
        {"action": "tuning", "net_id": "NET-A", "group_id": "g1",
         "kind": "detour", "params": {"offset_mm": 1.0}},
        {"action": "submit"},
    ]


def test_double_run_byte_equality_synth():
    a, b = synth_state(), synth_state()
    res_a = run_batch(a, _mixed_sequence(a))
    res_b = run_batch(b, _mixed_sequence(b))
    assert [r["accepted"] for r in res_a] == [r["accepted"] for r in res_b]
    assert a.connectivity == b.connectivity
    assert cst.state_sha256(a) == cst.state_sha256(b)
    ba = canonical.canonical_json(cst.state_facts(a))
    bb = canonical.canonical_json(cst.state_facts(b))
    assert ba == bb and ba == canonical.canonical_json(
        json.loads(ba.decode("utf-8")))          # round-trip 字节等


def test_double_run_byte_equality_real_board():
    def once():
        st = real_state()
        net = "Net-(D2-Pad1)"
        run_batch(st, [
            {"action": "route", "net_id": net,
             "waypoints": [[27, 31], [27, 25], [55, 25]], "layer": "F.Cu"},
            {"action": "width_class", "net_id": net, "class": "max"},
            {"action": "rotate", "partition_id": "PT-Net-_D2-Pad1_",
             "turns": 2},                        # 占位拒收（M4 未接线）
            {"action": "ripup", "shape_id": "seg:%s:0" % net},
        ])
        run_batch(st, [
            {"action": "route", "net_id": net,
             "waypoints": [[27, 31], [27, 25], [55, 25]], "layer": "F.Cu"},
        ], round_no=2)
        return st
    a, b = once(), once()
    assert a.connectivity == b.connectivity
    assert cst.state_sha256(a) == cst.state_sha256(b)
    assert canonical.canonical_json(cst.state_facts(a)) == \
        canonical.canonical_json(cst.state_facts(b))


def test_facts_no_dict_iteration_order_leak():
    # 相同逻辑内容、不同 dict 插入序构建 → facts 字节等（copy-on-write +
    # 排序构建; seg 序号保持同序，只有键控容器的插入序不同）
    a, b = synth_state(), synth_state()
    for st in (a, b):
        st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [12, 4]], "min")
        st.add_seg("NET-B", "PB", "B.Cu", [[4, 16], [12, 16]], "min")
    a.add_via("NET-A", [12, 4])
    a.add_via("NET-B", [12, 16])          # vias dict 两键插入序 A→B
    b.add_via("NET-B", [12, 16])
    b.add_via("NET-A", [12, 4])           # B→A
    a.widths = {"NET-A": "min"}
    a.widths["NET-B"] = "max"
    b.widths = {"NET-B": "max"}
    b.widths["NET-A"] = "min"             # widths 插入序相反
    a.set_placement("PA", rotate=1)
    b.set_placement("PB", flip=True)
    a.set_placement("PB", flip=True)
    b.set_placement("PA", rotate=1)       # placements 插入序相反
    for st in (a, b):
        st.recompute_connectivity()
    assert canonical.canonical_json(cst.state_facts(a)) == \
        canonical.canonical_json(cst.state_facts(b))
    assert cst.state_sha256(a) == cst.state_sha256(b)


def test_state_sha256_changes_on_mutation():
    st = synth_state()
    h0 = cst.state_sha256(st)
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [20, 4]], "min")
    assert cst.state_sha256(st) != h0
    st.recompute_connectivity()
    h1 = cst.state_sha256(st)
    st.recompute_connectivity()                  # 幂等重算不改 facts
    assert cst.state_sha256(st) == h1
