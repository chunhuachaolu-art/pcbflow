# -*- coding: utf-8 -*-
"""v5.overlay（L3 叠加与冲突检测 → v5.conflicts.v1）单元测试（V5.0 P2；stdlib+pytest）。

覆盖：六类检测器各至少 1 正 1 负（不该报的不报）；V2 数值锚点
（bottleneck 1.0<1.2、容量 7.05>4.3、净距 0.6-0.2=0.4<0.5、宽度 0.5<0.8）各一例
精确断言；conflict_id 连续编号确定性；工件双跑字节等；CF 列表对构造顺序稳定；
validate 拆坏字段报键路径；severity 映射；boards/d 真实板只读冒烟
（demo-01：capacity C1 + bottleneck P1 + width P8 + 净距 P7/P9；
adv-03：capacity COR-D）。内联小板构造后回填 provenance 再经 load_board 复检。
"""
import copy
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5.board import compute_board_sha256, load_board_file  # noqa: E402
from v5.overlay import (  # noqa: E402
    ARTIFACT_VERSION, DETECTOR_VERSION, OverlayError,
    artifact_bytes, artifact_sha256, build_conflicts,
    segment_intersects_rect, validate_conflicts_artifact,
)

BOARDS_D = os.path.join(ROOT, "boards", "d")

HARD_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}


# ---------------------------------------------------------------- 板构造助手

def _part(pid, a, b, planned=None, w_min=0.2, w_max=0.2, occupancy=None,
          ptype="MISC", bottleneck=None, layer="F.Cu"):
    geometry = {"endpoints": [list(a), list(b)]}
    if occupancy is not None:
        geometry["occupancy_mm"] = occupancy
    part = {"partition_id": pid, "ptype": ptype, "geometry": geometry,
            "layer_policy": layer, "width_prior": {"w_min": w_min, "w_max": w_max},
            "current_a": 0.0, "speed_class": "low_speed"}
    if planned is not None:
        part["planned_width"] = planned
    if bottleneck is not None:
        part["bottleneck"] = bottleneck
    return part


def _zone(zid, kind, rect, layers="all", capacity=None):
    zone = {"zone_id": zid, "kind": kind, "rect": rect, "layers": layers}
    if capacity is not None:
        zone["capacity"] = capacity
    return zone


def _board(partitions, zones, nets=None, board_id="overlay-case"):
    """内联小板；构造后回填 board_sha256（load_board 会复算哈希链）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "h",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": zones,
        "partitions": partitions,
        "nets": nets if nets is not None else [],
        "hard_rules": dict(HARD_RULES),
        "principle_registry": [],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "tests/test_overlay.py",
            "source_sha256": "a" * 64,
            "adapter": "hand",
        },
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def _build(partitions, zones, nets=None, board_id="overlay-case"):
    return build_conflicts(_board(partitions, zones, nets, board_id))


def _find(art, kind, subjects=None, zone=None):
    """按 (kind, subjects, zone) 取唯一冲突（无则 None；传 None 不过滤该维）。"""
    hits = [c for c in art["conflicts"]
            if c["kind"] == kind
            and (subjects is None or tuple(c["subjects"]) == tuple(subjects))
            and (zone is None or c["zone"] == zone)]
    assert len(hits) <= 1, "同 (kind, subjects, zone) 冲突至多一条: %r" % (hits,)
    return hits[0] if hits else None


def _summary(art):
    return [(c["conflict_id"], c["kind"], tuple(c["subjects"]), c["zone"])
            for c in art["conflicts"]]


def _load_d(name):
    return load_board_file(os.path.join(BOARDS_D, "%s.board.v1.json" % name))


# ---------------------------------------------------------------- 1. 工件头

def test_artifact_header_and_validate_roundtrip():
    """工件头字段齐全；validate 通过且原样返回；空场冲突为零。"""
    art = _build([_part("PA", (5.0, 5.0), (20.0, 5.0)),
                  _part("PB", (5.0, 30.0), (20.0, 30.0))], [])
    assert art["artifact"] == ARTIFACT_VERSION == "v5.conflicts.v1"
    assert art["board_id"] == "overlay-case"
    assert len(art["board_sha256"]) == 64
    assert art["detector_version"] == DETECTOR_VERSION == "v5.overlay/0.1.0"
    # 2 分区 × (0 穿区 zone + 0 容量走廊) + 2×C(2,2)=2 成对检查
    assert art["pairs_checked"] == 2
    assert art["conflicts"] == []
    assert validate_conflicts_artifact(art) is art


# ---------------------------------------------------------------- 2. 检测器 1 直线穿区

def test_zone_cross_keepout_blocking():
    """穿 keepout → blocking，zone 落名，layer null，arithmetic null。"""
    art = _build([_part("PA", (10.0, 20.0), (40.0, 20.0))],
                 [_zone("K1", "keepout",
                        {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0})])
    c = _find(art, "straight_zone_cross", ["PA"], "K1")
    assert c is not None
    assert c["severity"] == "blocking"
    assert c["layer"] is None
    assert c["arithmetic"] is None
    assert "K1" in c["basis"]
    assert len(art["conflicts"]) == 1


def test_zone_cross_sensitive_advisory():
    """穿 sensitive → advisory（V2 J1 型待裁决）。"""
    art = _build([_part("PA", (10.0, 20.0), (40.0, 20.0))],
                 [_zone("S1", "sensitive",
                        {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0},
                        layers="signal")])
    c = _find(art, "straight_zone_cross", ["PA"], "S1")
    assert c is not None
    assert c["severity"] == "advisory"
    assert len(art["conflicts"]) == 1


def test_zone_cross_negative_miss():
    """不穿区不报（负例）：直线段从禁布区外绕过。"""
    art = _build([_part("PA", (10.0, 5.0), (40.0, 5.0))],
                 [_zone("K1", "keepout",
                        {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0}),
                  _zone("S1", "sensitive",
                        {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0})])
    assert art["conflicts"] == []


def test_corridor_cross_not_reported():
    """穿 corridor 不算 straight_zone_cross；容量充足时整单零冲突。"""
    art = _build([_part("PA", (0.0, 20.0), (40.0, 20.0), planned=0.2,
                        w_min=0.2, w_max=0.2)],
                 [_zone("C1", "corridor",
                        {"x_min": 18.0, "y_min": 0.0, "x_max": 22.0, "y_max": 40.0},
                        layers="signal", capacity=1.0)])
    assert art["conflicts"] == []


def test_segment_intersects_rect_predicate():
    """线段-矩形相交判定六态：穿过/在外/贴边/端点在内/沿边/擦角而过。"""
    rect = {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0, "y_max": 10.0}
    assert segment_intersects_rect((-5.0, 5.0), (15.0, 5.0), rect)      # 横穿
    assert not segment_intersects_rect((-5.0, 15.0), (15.0, 15.0), rect)  # 在外
    assert segment_intersects_rect((-5.0, 0.0), (15.0, 0.0), rect)      # 贴下边（共线重叠）
    assert segment_intersects_rect((5.0, 5.0), (20.0, 20.0), rect)      # 端点在内
    # 切角（x+y=11 过 (10,1)/(1,10) 两边点）算相交
    assert segment_intersects_rect((-3.0, 14.0), (14.0, -3.0), rect)
    # 擦角而过（x+y=21 距角 (10,10) 0.707，矩形外）不算相交
    assert not segment_intersects_rect((0.5, 20.5), (20.5, 0.5), rect)


# ---------------------------------------------------------------- 3. 检测器 2 容量

def test_capacity_infeasible_multi_and_arithmetic():
    """多分区占用 0.3+0.3+0.5×1=1.1>1.0 → blocking（可复算式逐字符断言）。"""
    art = _build([_part("PA", (0.0, 20.0), (40.0, 20.0), planned=0.3,
                        w_min=0.3, w_max=0.3),
                  _part("PB", (0.0, 22.0), (40.0, 22.0), planned=0.3,
                        w_min=0.3, w_max=0.3)],
                 [_zone("C1", "corridor",
                        {"x_min": 18.0, "y_min": 0.0, "x_max": 22.0, "y_max": 40.0},
                        layers="signal", capacity=1.0)])
    c = _find(art, "capacity_infeasible", ["PA", "PB"], "C1")
    assert c is not None
    assert c["severity"] == "blocking"
    assert c["arithmetic"] == "0.3+0.3+0.5*1=1.1>1.0"
    assert len(art["conflicts"]) == 1


def test_capacity_ribbon_declared_preferred():
    """occupancy_mm 声明优先（ribbon/差分对口径）：单条 1.1>1.0（adv-03 镜像）。"""
    art = _build([_part("DP", (0.0, 20.0), (40.0, 20.0), occupancy=1.1,
                        w_min=0.3, w_max=0.3)],
                 [_zone("COR", "corridor",
                        {"x_min": 18.0, "y_min": 0.0, "x_max": 22.0, "y_max": 40.0},
                        layers="signal", capacity=1.0)])
    c = _find(art, "capacity_infeasible", ["DP"], "COR")
    assert c is not None
    assert c["arithmetic"] == "1.1>1.0"
    assert c["severity"] == "blocking"


def test_capacity_wmax_fallback_when_no_planned():
    """无 planned_width 时铜宽取 width_prior.w_max：0.9+0.9+0.5×1=2.3>1.0。"""
    art = _build([_part("PA", (0.0, 20.0), (40.0, 20.0), w_min=0.2, w_max=0.9),
                  _part("PB", (0.0, 24.0), (40.0, 24.0), w_min=0.2, w_max=0.9)],
                 [_zone("C1", "corridor",
                        {"x_min": 18.0, "y_min": 0.0, "x_max": 22.0, "y_max": 40.0},
                        layers="signal", capacity=1.0)])
    c = _find(art, "capacity_infeasible", ["PA", "PB"], "C1")
    assert c is not None
    assert c["arithmetic"] == "0.9+0.9+0.5*1=2.3>1.0"


def test_capacity_negative_fits_and_uncapacitated_corridor():
    """占用 ≤ 容量不报；corridor 未声明 capacity 不检（负例双查）。"""
    art = _build([_part("PA", (0.0, 20.0), (40.0, 20.0), planned=0.2,
                        w_min=0.2, w_max=0.2)],
                 [_zone("C1", "corridor",
                        {"x_min": 18.0, "y_min": 0.0, "x_max": 22.0, "y_max": 40.0},
                        layers="signal", capacity=1.0),
                  _zone("C2", "corridor",
                        {"x_min": 30.0, "y_min": 0.0, "x_max": 34.0, "y_max": 40.0},
                        layers="signal")])
    assert art["conflicts"] == []


# ---------------------------------------------------------------- 4. 检测器 3 瓶颈

def test_bottleneck_anchor_planned():
    """V2 锚点：usable 1.0 < planned 1.2 → blocking，arithmetic "1.0<1.2"。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=1.2,
                        w_min=0.6, w_max=1.4,
                        bottleneck={"span": [8.0, 10.0], "usable_width": 1.0})], [])
    c = _find(art, "bottleneck", ["PA"])
    assert c is not None
    assert c["severity"] == "blocking"
    assert c["zone"] is None
    assert c["layer"] is None
    assert c["arithmetic"] == "1.0<1.2"


def test_bottleneck_wmin_binding():
    """无 planned_width 时按先验下限判：usable 0.4 < w_min 0.6 → blocking。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0),
                        w_min=0.6, w_max=1.4,
                        bottleneck={"span": [8.0, 10.0], "usable_width": 0.4})], [])
    c = _find(art, "bottleneck", ["PA"])
    assert c is not None
    assert c["arithmetic"] == "0.4<0.6"


def test_bottleneck_stricter_of_two_wins():
    """双约束均违取缺口更严者：planned 缺 0.2 < w_min 缺 0.4 → 绑定 w_min。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=0.7,
                        w_min=0.9, w_max=1.4,
                        bottleneck={"span": [8.0, 10.0], "usable_width": 0.5})], [])
    c = _find(art, "bottleneck", ["PA"])
    assert c is not None
    assert c["arithmetic"] == "0.5<0.9"
    assert "取缺口更严者" in c["basis"]


def test_bottleneck_negative_and_edge_touch():
    """可用宽充足不报；擦边（usable == planned）合规不报。"""
    base = dict(w_min=0.6, w_max=1.4)
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=1.2,
                        bottleneck={"span": [8.0, 10.0], "usable_width": 1.5},
                        **base)], [])
    assert _find(art, "bottleneck") is None
    art2 = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=1.2,
                         bottleneck={"span": [8.0, 10.0], "usable_width": 1.2},
                         **base)], [])
    assert _find(art2, "bottleneck") is None


# ---------------------------------------------------------------- 5. 检测器 4 宽度缺陷

def test_seeded_width_defect_below_min_anchor():
    """V2 P8 锚点：planned 0.5 < w_min 0.8 → advisory，arithmetic "0.5<0.8"。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=0.5,
                        w_min=0.8, w_max=1.6)], [])
    c = _find(art, "seeded_width_defect", ["PA"])
    assert c is not None
    assert c["severity"] == "advisory"
    assert c["arithmetic"] == "0.5<0.8"


def test_seeded_width_defect_above_max():
    """超出上限：planned 1.8 > w_max 1.6 → advisory。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=1.8,
                        w_min=0.8, w_max=1.6)], [])
    c = _find(art, "seeded_width_defect", ["PA"])
    assert c is not None
    assert c["arithmetic"] == "1.8>1.6"


def test_seeded_width_defect_negative_inside_interval():
    """区间内（含边界擦边）不报；未声明 planned_width 不检。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0), planned=1.0,
                        w_min=0.8, w_max=1.6),
                  _part("PB", (0.0, 30.0), (40.0, 30.0),
                        w_min=0.8, w_max=1.6)], [])
    assert art["conflicts"] == []


# ---------------------------------------------------------------- 6. 检测器 5 净距缺陷

def test_seeded_clearance_anchor():
    """V2 P7/P9 锚点：距 0.6、宽 0.2/0.2 → advisory，arithmetic "0.6-0.2=0.4<0.5"。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                  _part("PB", (0.0, 10.6), (40.0, 10.6))], [])
    c = _find(art, "seeded_clearance_defect", ["PA", "PB"])
    assert c is not None
    assert c["severity"] == "advisory"
    assert c["arithmetic"] == "0.6-0.2=0.4<0.5"
    # 真缺陷对不进包络伪影披露（检测器 6 不重复报）
    assert _find(art, "envelope_overlap_diagnostic") is None
    assert len(art["conflicts"]) == 1


def test_seeded_clearance_negative_shared_endpoint_and_spacing():
    """负例：净距充足不报；共享端点（相连链）豁免不报。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                  _part("PB", (0.0, 10.95), (40.0, 10.95))], [])
    assert _find(art, "seeded_clearance_defect") is None
    art2 = _build([_part("PA", (0.0, 10.0), (20.0, 10.0)),
                   _part("PB", (20.0, 10.0), (30.0, 12.0))], [])
    assert _find(art2, "seeded_clearance_defect") is None
    assert art2["conflicts"] == []


def test_seeded_clearance_same_net_still_flagged():
    """文档化决定：按任务书字面口径仅豁免共享端点，同网近距对仍报（数据缺陷素材）。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                  _part("PB", (0.0, 10.6), (40.0, 10.6))], [],
                 nets=[{"net_id": "N1", "net_class": "MISC",
                        "partitions": ["PA", "PB"]}])
    c = _find(art, "seeded_clearance_defect", ["PA", "PB"])
    assert c is not None
    assert c["arithmetic"] == "0.6-0.2=0.4<0.5"


# ---------------------------------------------------------------- 7. 检测器 6 包络伪影

def test_envelope_overlap_diagnostic_positive():
    """包络(±0.6)重叠但净距 0.55 ≥ R5 → advisory，arithmetic "0.55>=0.5"。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                  _part("PB", (0.0, 10.75), (40.0, 10.75))], [])
    c = _find(art, "envelope_overlap_diagnostic", ["PA", "PB"])
    assert c is not None
    assert c["severity"] == "advisory"
    assert c["arithmetic"] == "0.55>=0.5"
    assert _find(art, "seeded_clearance_defect") is None
    assert len(art["conflicts"]) == 1


def test_envelope_overlap_diagnostic_negative():
    """负例：包络不重叠（相距 1.8）不报；净距充足且包络不交零冲突。"""
    art = _build([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                  _part("PB", (0.0, 13.0), (40.0, 13.0))], [])
    assert art["conflicts"] == []


# ---------------------------------------------------------------- 8. 编号/排序/确定性

def test_conflict_id_sequence_and_sort_order():
    """多类冲突并存：按 (kind, subjects, zone) 排序后连续编号 CF-001..。"""
    zones = [_zone("K1", "keepout",
                   {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0}),
             _zone("S1", "sensitive",
                   {"x_min": 30.0, "y_min": 0.0, "x_max": 40.0, "y_max": 10.0}),
             _zone("C1", "corridor",
                   {"x_min": 45.0, "y_min": 0.0, "x_max": 48.0, "y_max": 40.0},
                   layers="signal", capacity=1.0)]
    parts = [_part("PA", (0.0, 20.0), (50.0, 20.0), planned=0.9,
                   w_min=0.2, w_max=0.9),
             _part("PB", (0.0, 22.0), (50.0, 22.0), planned=0.3,
                   w_min=0.3, w_max=0.3),
             _part("PC", (0.0, 36.0), (50.0, 36.0), planned=0.6,
                   w_min=0.2, w_max=0.8,
                   bottleneck={"span": [0.0, 5.0], "usable_width": 0.1})]
    art = _build(parts, zones)
    assert _summary(art) == [
        ("CF-001", "bottleneck", ("PC",), None),
        ("CF-002", "capacity_infeasible", ("PA", "PB", "PC"), "C1"),
        ("CF-003", "straight_zone_cross", ("PA",), "K1"),
        ("CF-004", "straight_zone_cross", ("PB",), "K1"),
    ]
    cap = _find(art, "capacity_infeasible", ["PA", "PB", "PC"], "C1")
    assert cap["arithmetic"] == "0.9+0.3+0.6+0.5*2=2.8>1.0"
    # 3×2 穿区对 + 3×1 容量走廊 + 2×C(3,2) 成对检查 = 6+3+6 = 15
    assert art["pairs_checked"] == 15
    assert validate_conflicts_artifact(art)


def test_double_run_bytes_equal():
    """同板双跑：canonical 字节与 sha256 指纹严格相等（§3.4 硬性）。"""
    board = _board([_part("PA", (0.0, 10.0), (40.0, 10.0)),
                    _part("PB", (0.0, 10.6), (40.0, 10.6))],
                   [_zone("K1", "keepout",
                          {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0,
                           "y_max": 25.0})])
    a1 = build_conflicts(board)
    a2 = build_conflicts(copy.deepcopy(board))
    assert artifact_bytes(a1) == artifact_bytes(a2)
    assert artifact_sha256(a1) == artifact_sha256(a2)


def test_conflict_list_stable_under_construction_order():
    """换分区/zone 构造顺序：CF 列表与 pairs_checked 完全不变（board_sha256 随板变）。"""
    zones = [_zone("K1", "keepout",
                   {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0}),
             _zone("C1", "corridor",
                   {"x_min": 45.0, "y_min": 0.0, "x_max": 48.0, "y_max": 40.0},
                   layers="signal", capacity=1.0)]
    parts = [_part("PA", (0.0, 20.0), (50.0, 20.0), planned=0.9,
                   w_min=0.2, w_max=0.9),
             _part("PB", (0.0, 22.0), (50.0, 22.0), planned=0.3,
                   w_min=0.3, w_max=0.3)]
    art1 = build_conflicts(_board(parts, zones))
    art2 = build_conflicts(_board(list(reversed(parts)), list(reversed(zones))))
    assert art1["conflicts"] == art2["conflicts"]
    assert art1["pairs_checked"] == art2["pairs_checked"]
    assert art1["board_sha256"] != art2["board_sha256"]  # 板内容变 → 板哈希变，列表不变


# ---------------------------------------------------------------- 9. validate fail-closed

@pytest.fixture()
def rich_artifact():
    zones = [_zone("K1", "keepout",
                   {"x_min": 15.0, "y_min": 15.0, "x_max": 25.0, "y_max": 25.0}),
             _zone("C1", "corridor",
                   {"x_min": 45.0, "y_min": 0.0, "x_max": 48.0, "y_max": 40.0},
                   layers="signal", capacity=1.0)]
    parts = [_part("PA", (0.0, 20.0), (50.0, 20.0), planned=0.9,
                   w_min=0.2, w_max=0.9),
             _part("PB", (0.0, 22.0), (50.0, 22.0), planned=0.3,
                   w_min=0.3, w_max=0.3),
             _part("PC", (0.0, 36.0), (50.0, 36.0), planned=0.6,
                   w_min=0.2, w_max=0.8,
                   bottleneck={"span": [0.0, 5.0], "usable_width": 0.1})]
    return build_conflicts(_board(parts, zones, board_id="rich-case"))


def _renumber(conflicts):
    for i, c in enumerate(conflicts):
        c["conflict_id"] = "CF-%03d" % (i + 1)
    return conflicts


def test_validate_reports_key_paths(rich_artifact):
    """拆坏任一合同字段 → OverlayError 报具体键路径（fail-closed）。"""
    cases = [
        (lambda a: a.update(artifact="v5.other"), "artifact"),
        (lambda a: a.update(board_sha256="xyz"), "board_sha256"),
        (lambda a: a.update(detector_version="v5.overlay/9.9"), "detector_version"),
        (lambda a: a.update(pairs_checked=-1), "pairs_checked"),
        (lambda a: a["conflicts"][0].update(kind="nope"), "conflicts[0].kind"),
        (lambda a: a["conflicts"][0].update(severity="fatal"), "conflicts[0].severity"),
        (lambda a: a["conflicts"][0].update(zone="K9"), "conflicts[0].zone"),
        (lambda a: a["conflicts"][0].update(conflict_id="CF-009"),
         "conflicts[0].conflict_id"),
        (lambda a: a["conflicts"][0].update(subjects=["PC", "PC"]),
         "conflicts[0].subjects"),
        (lambda a: a["conflicts"][1].update(arithmetic=None),
         "conflicts[1].arithmetic"),
        (lambda a: a["conflicts"][1].update(subjects=[]), "conflicts[1].subjects"),
        (lambda a: a["conflicts"][2].update(arithmetic="1>0"),
         "conflicts[2].arithmetic"),
        (lambda a: a["conflicts"][2].pop("basis"), "conflicts[2].basis"),
        (lambda a: a["conflicts"][2].update(layer="F.Cu"), "conflicts[2].layer"),
        # 逐条合法但乱序（重编号后仍须按 (kind, subjects, zone) 升序）
        (lambda a: a.update(conflicts=_renumber([
            a["conflicts"][1], a["conflicts"][0], a["conflicts"][2]])),
         "conflicts"),
    ]
    for mutate, path in cases:
        art = copy.deepcopy(rich_artifact)
        assert validate_conflicts_artifact(art) is art  # 原件必过
        mutate(art)
        with pytest.raises(OverlayError) as excinfo:
            validate_conflicts_artifact(art)
        assert excinfo.value.path == path, (
            "期望键路径 %r，得到 %r（%s）" % (path, excinfo.value.path, excinfo.value))


def test_build_rejects_bad_board():
    """板未过 load_board（哈希链被拆）→ OverlayError，path="board"。"""
    board = _board([_part("PA", (0.0, 10.0), (40.0, 10.0))], [])
    board["provenance"]["board_sha256"] = "0" * 64
    with pytest.raises(OverlayError) as excinfo:
        build_conflicts(board)
    assert excinfo.value.path == "board"


# ---------------------------------------------------------------- 10. 真实板只读冒烟

EXPECTED_DEMO01 = [
    ("CF-001", "bottleneck", ("P1",), None),
    ("CF-002", "capacity_infeasible", ("P1", "P2", "P4", "P7", "P9"), "C1"),
    ("CF-003", "envelope_overlap_diagnostic", ("P3", "P7"), None),
    ("CF-004", "envelope_overlap_diagnostic", ("P4", "P7"), None),
    ("CF-005", "seeded_clearance_defect", ("P2", "P3"), None),
    ("CF-006", "seeded_clearance_defect", ("P2", "P4"), None),
    ("CF-007", "seeded_clearance_defect", ("P2", "P5"), None),
    ("CF-008", "seeded_clearance_defect", ("P3", "P9"), None),
    ("CF-009", "seeded_clearance_defect", ("P4", "P9"), None),
    ("CF-010", "seeded_clearance_defect", ("P7", "P9"), None),
    ("CF-011", "seeded_width_defect", ("P8",), None),
    ("CF-012", "straight_zone_cross", ("P2",), "ANA"),
    ("CF-013", "straight_zone_cross", ("P3",), "K1"),
    ("CF-014", "straight_zone_cross", ("P5",), "K2"),
]


def test_smoke_demo01():
    """demo-01 只读冒烟：C1 容量 7.05>4.3、P1 瓶颈 1.0<1.2、P8 宽缺陷 0.5<0.8、
    P7/P9 净距 0.4<0.5、K1/K2/ANA 穿区，全清单 14 条逐位对账。"""
    art = build_conflicts(_load_d("demo-01-v2-corridor"))
    assert validate_conflicts_artifact(art) is art
    assert _summary(art) == EXPECTED_DEMO01
    # 9 分区×(3 穿区 zone+1 容量走廊) + 2×C(9,2)=72 → 27+9+72 = 108
    assert art["pairs_checked"] == 108
    cap = _find(art, "capacity_infeasible", ["P1", "P2", "P4", "P7", "P9"], "C1")
    assert cap["arithmetic"] == "1.2+0.15+3.3+0.2+0.2+0.5*4=7.05>4.3"
    assert cap["severity"] == "blocking"
    bn = _find(art, "bottleneck", ["P1"])
    assert bn["arithmetic"] == "1.0<1.2"
    assert bn["severity"] == "blocking"
    wd = _find(art, "seeded_width_defect", ["P8"])
    assert wd["arithmetic"] == "0.5<0.8"
    assert wd["severity"] == "advisory"
    cl = _find(art, "seeded_clearance_defect", ["P7", "P9"])
    assert cl["arithmetic"] == "0.6-0.2=0.4<0.5"
    assert cl["severity"] == "advisory"
    by_zone = {c["zone"]: c for c in art["conflicts"]
               if c["kind"] == "straight_zone_cross"}
    assert by_zone["ANA"]["severity"] == "advisory"
    assert by_zone["K1"]["severity"] == "blocking"
    assert by_zone["K2"]["severity"] == "blocking"


def test_smoke_adv03():
    """adv-03 只读冒烟：COR-D 差分对容量 1.1>1.0 + 直线穿两道禁布墙，共 3 条。"""
    art = build_conflicts(_load_d("adv-03-diff-vs-capacity"))
    assert validate_conflicts_artifact(art) is art
    assert _summary(art) == [
        ("CF-001", "capacity_infeasible", ("DP1",), "COR-D"),
        ("CF-002", "straight_zone_cross", ("DP1",), "K-EAST"),
        ("CF-003", "straight_zone_cross", ("DP1",), "K-WEST"),
    ]
    cap = _find(art, "capacity_infeasible", ["DP1"], "COR-D")
    assert cap["arithmetic"] == "1.1>1.0"
    assert cap["severity"] == "blocking"
    for c in art["conflicts"]:
        if c["kind"] == "straight_zone_cross":
            assert c["severity"] == "blocking"
