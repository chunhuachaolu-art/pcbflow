# -*- coding: utf-8 -*-
"""v5.jitems 单测：三类映射、jid 确定编号、statement 不泄漏算术、
负向铁律（seeded/diagnostic 三类不产 J 项）、fail-closed、双跑字节等。
"""
import pytest

from fixtures_v2 import build_v2_board
from v5 import canonical
from v5.jitems import JItemError, build_j_items, jitems_canonical_bytes


# --------------------------------------------------------------- 夹具（内联冲突工件）

def _artifact(conflicts, board=None):
    board = board or build_v2_board()
    return {
        "artifact": "v5.conflicts.v1",
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "conflicts": conflicts,
    }


def _cf(cid, kind, subjects, basis, zone=None, severity="blocking", arithmetic=None):
    return {"conflict_id": cid, "kind": kind, "subjects": list(subjects),
            "zone": zone, "layer": None, "basis": basis,
            "arithmetic": arithmetic, "severity": severity}


# --------------------------------------------------------------- 映射一：straight_zone_cross

def test_straight_zone_cross_blocking_becomes_disposition():
    """V2 J1 型：「P2 直线路径穿过 ANA。给出处置。」逐字形态。"""
    art = _artifact([_cf("CF-001", "straight_zone_cross", ["P2"],
                         "P2 直线路径穿过 ANA", zone="ANA")])
    items = build_j_items(art)
    assert items == [{
        "jid": "J-1",
        "kind": "disposition",
        "subjects_partitions": ["P2"],
        "zone": "ANA",
        "joint_group": None,
        "statement": "P2 直线路径穿过 ANA。给出处置。",
        "source_conflicts": ["CF-001"],
    }]


def test_straight_zone_cross_advisory_also_disposition():
    """advisory 级 straight_zone_cross 同样产 disposition 项（合同不分级丢项）。"""
    art = _artifact([_cf("CF-009", "straight_zone_cross", ["P5"],
                         "P5 直线路径穿过 K2", zone="K2", severity="advisory")])
    items = build_j_items(art)
    assert len(items) == 1
    assert items[0]["kind"] == "disposition"
    assert items[0]["zone"] == "K2"
    assert items[0]["joint_group"] is None
    assert items[0]["statement"] == "P5 直线路径穿过 K2。给出处置。"


# --------------------------------------------------------------- 映射二：bottleneck

def test_bottleneck_becomes_disposition():
    """V2 J4 型：「瓶颈段…。给出处置。」zone/joint_group 均为 null。"""
    art = _artifact([_cf("CF-005", "bottleneck", ["P1"],
                         "P1 在 x∈[8,10] 瓶颈段可用宽度低于计划宽度")])
    items = build_j_items(art)
    assert items == [{
        "jid": "J-1",
        "kind": "disposition",
        "subjects_partitions": ["P1"],
        "zone": None,
        "joint_group": None,
        "statement": "P1 在 x∈[8,10] 瓶颈段可用宽度低于计划宽度。给出处置。",
        "source_conflicts": ["CF-005"],
    }]


# --------------------------------------------------------------- 映射三：capacity_infeasible

def test_capacity_same_zone_merges_to_single_joint():
    """同 zone 两条 capacity_infeasible 合并为一个 joint 项（subjects 并集）。"""
    art = _artifact([
        _cf("CF-002", "capacity_infeasible", ["P3"],
            "P3 若留 F.Cu 过 C1，占用合计将超单层剩余容量", zone="C1",
            arithmetic="3.3+0.5+0.2=4.0 > 4.3"),
        _cf("CF-003", "capacity_infeasible", ["P5"],
            "P5 若留 F.Cu 过 C1，占用合计将超单层剩余容量", zone="C1",
            arithmetic="3.3+0.5+0.2+0.2+0.5=4.7 > 4.3"),
    ])
    items = build_j_items(art)
    assert len(items) == 1
    it = items[0]
    assert it["jid"] == "J-1"
    assert it["kind"] == "joint"
    assert it["subjects_partitions"] == ["P3", "P5"]       # 并集，排序
    assert it["zone"] == "C1"
    assert it["joint_group"] == "C1"
    assert it["source_conflicts"] == ["CF-002", "CF-003"]  # 全组，排序
    assert it["statement"] == ("P3 若留 F.Cu 过 C1，占用合计将超单层剩余容量；"
                               "P5 若留 F.Cu 过 C1，占用合计将超单层剩余容量。"
                               "分区 P3 与 P5 共享走廊 C1，必须联合求解，"
                               "给出联合最优方案排序。")


def test_capacity_different_zones_separate_joints():
    """不同 zone 的 capacity_infeasible 各自成 joint 项，不跨组合并。"""
    art = _artifact([
        _cf("CF-002", "capacity_infeasible", ["P3"], "P3 过 CA 超容量", zone="CA"),
        _cf("CF-003", "capacity_infeasible", ["P5"], "P5 过 CB 超容量", zone="CB"),
    ])
    items = build_j_items(art)
    assert [(it["joint_group"], it["subjects_partitions"]) for it in items] \
        == [("CA", ["P3"]), ("CB", ["P5"])]


# --------------------------------------------------------------- 负向铁律：seeded/diagnostic 不产 J 项

@pytest.mark.parametrize("kind", ["seeded_width_defect", "seeded_clearance_defect",
                                  "envelope_overlap_diagnostic"])
def test_seeded_and_diagnostic_produce_no_j_items(kind):
    """三类 seeded/diagnostic 冲突一律不产 J 项：盲包绝不预先披露数据缺陷，
    缺陷必须留给模型 defect_scan 通道自己发现（模块 docstring 铁律）。"""
    bad = _cf("CF-BAD", kind, ["P8"], "P8 计划宽 0.5 低于 R1 下限 0.8",
              severity="advisory")
    good = _cf("CF-GOOD", "straight_zone_cross", ["P2"],
               "P2 直线路径穿过 ANA", zone="ANA")
    # 纯 bad → 空
    assert build_j_items(_artifact([bad])) == []
    # bad+good 混合 → 只剩 good（证明是逐条过滤而非整体放弃）
    items = build_j_items(_artifact([bad, good]))
    assert len(items) == 1
    assert items[0]["source_conflicts"] == ["CF-GOOD"]
    assert "P8" not in items[0]["subjects_partitions"]


# --------------------------------------------------------------- fail-closed

def test_unknown_kind_fail_closed():
    art = _artifact([_cf("CF-001", "mystery_kind", ["P2"], "某冲突")])
    with pytest.raises(JItemError) as ei:
        build_j_items(art)
    assert ei.value.path == "conflicts[0].kind"


def test_capacity_without_zone_fail_closed():
    art = _artifact([_cf("CF-002", "capacity_infeasible", ["P3"], "P3 超容量",
                         zone=None)])
    with pytest.raises(JItemError) as ei:
        build_j_items(art)
    assert ei.value.path == "conflicts[0].zone"


def test_bad_severity_fail_closed():
    art = _artifact([_cf("CF-001", "bottleneck", ["P1"], "瓶颈", severity="huge")])
    with pytest.raises(JItemError) as ei:
        build_j_items(art)
    assert ei.value.path == "conflicts[0].severity"


def test_duplicate_conflict_id_fail_closed():
    art = _artifact([
        _cf("CF-001", "bottleneck", ["P1"], "瓶颈一"),
        _cf("CF-001", "bottleneck", ["P2"], "瓶颈二"),
    ])
    with pytest.raises(JItemError) as ei:
        build_j_items(art)
    assert ei.value.path == "conflicts[1].conflict_id"


def test_artifact_tag_enforced():
    art = _artifact([])
    art["artifact"] = "v5.conflicts.v0"
    with pytest.raises(JItemError) as ei:
        build_j_items(art)
    assert ei.value.path == "artifact"


# --------------------------------------------------------------- 编号与确定性

def test_jid_numbering_sorted_and_consecutive():
    """五冲突 → 4 项：按 (subjects, kind) 排序后 J-1..J-4 连续编号。"""
    art = _artifact([
        _cf("CF-004", "straight_zone_cross", ["P5"], "P5 直线路径穿过 K2",
            zone="K2", severity="advisory"),
        _cf("CF-002", "capacity_infeasible", ["P3"], "P3 过 C1 超容量", zone="C1"),
        _cf("CF-005", "bottleneck", ["P1"], "P1 瓶颈段可用宽度不足"),
        _cf("CF-003", "capacity_infeasible", ["P5"], "P5 过 C1 超容量", zone="C1"),
        _cf("CF-001", "straight_zone_cross", ["P2"], "P2 直线路径穿过 ANA",
            zone="ANA"),
    ])
    items = build_j_items(art)
    got = [(it["jid"], tuple(it["subjects_partitions"]), it["kind"]) for it in items]
    # subjects 元组字典序：("P1",) < ("P2",) < ("P3","P5") < ("P5",)
    assert got == [("J-1", ("P1",), "disposition"),
                   ("J-2", ("P2",), "disposition"),
                   ("J-3", ("P3", "P5"), "joint"),
                   ("J-4", ("P5",), "disposition")]


def test_statement_excludes_arithmetic():
    """statement 绝不拼入 arithmetic（数值答案不泄漏给模型）。"""
    arith = "3.3+0.5+0.2=4.0 > 4.3"
    art = _artifact([_cf("CF-002", "capacity_infeasible", ["P3"],
                         "P3 若留 F.Cu 过 C1 将超单层剩余容量", zone="C1",
                         arithmetic=arith)])
    stmt = build_j_items(art)[0]["statement"]
    assert arith not in stmt
    assert "4.3" not in stmt
    assert stmt.endswith("给出联合最优方案排序。")


def test_double_run_byte_equal_and_order_insensitive():
    """双跑字节等；且冲突条目输入顺序翻转不影响输出（分组/排序全确定）。"""
    conflicts = [
        _cf("CF-001", "straight_zone_cross", ["P2"], "P2 直线路径穿过 ANA",
            zone="ANA"),
        _cf("CF-002", "capacity_infeasible", ["P3"], "P3 过 C1 超容量", zone="C1"),
        _cf("CF-003", "capacity_infeasible", ["P5"], "P5 过 C1 超容量", zone="C1"),
        _cf("CF-005", "bottleneck", ["P1"], "P1 瓶颈段可用宽度不足"),
    ]
    a = build_j_items(_artifact(conflicts))
    b = build_j_items(_artifact(conflicts))
    assert jitems_canonical_bytes(a) == jitems_canonical_bytes(b)
    rev = build_j_items(_artifact(list(reversed(conflicts))))
    assert canonical.canonical_json(a) == canonical.canonical_json(rev)


def test_empty_conflicts_empty_list():
    assert build_j_items(_artifact([])) == []
