# -*- coding: utf-8 -*-
"""L2 包络+容量账本测试：双跑字节等、包络精确值、current_a 驱动宽度先验、
V2 口径手算账本（4.0 fits / 4.7 not fits）、canonical 字节稳定、fail-closed 对账。"""
import hashlib
import json

import pytest

from v5 import canonical
from v5.board import compute_board_sha256
from v5.envelope_plan import (EnvelopePlanError, build_envelope_artifact,
                              envelope_artifact_bytes, envelope_artifact_sha256,
                              validate_envelope_artifact)
from v5.partition import build_partition_artifact
from v5.metrics import capacity as cap


# --------------------------------------------------------------- 夹具构造（内联小板）

def gran_entry(min_gap_mm=2.0, group_types=("BUS", "DIFF"), principle_id="P-PART-GRAN"):
    """粒度先验条目（L1 必需；source_hash=剔除自身后 canonical sha256）。"""
    entry = {
        "principle_id": principle_id,
        "name": "分区聚类粒度先验",
        "intent": {"protects": "走廊通行容量", "sacrifices": "细粒度自由"},
        "scope": "partitioning",
        "protected_resources": ["corridor_capacity"],
        "target_freedom": "corridor",
        "priority": 50,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": "partition_granularity",
                          "params": {"min_gap_mm": min_gap_mm,
                                     "group_types": list(group_types)}},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["V5.0-DEV-TASKBOOK §4 L1"],
        "version": "1.0.0",
    }
    entry["source_hash"] = canonical.canonical_sha256(entry)
    return entry


def part(pid, ptype, a, b, width=(0.2, 0.2), current=0.0, speed="low_speed",
         policy="F.Cu", planned_width=None, occupancy_mm=None, copper_band=None):
    geometry = {"endpoints": [[float(a[0]), float(a[1])], [float(b[0]), float(b[1])]]}
    if occupancy_mm is not None:
        geometry["occupancy_mm"] = occupancy_mm
    if copper_band is not None:
        geometry["copper_band"] = [float(copper_band[0]), float(copper_band[1])]
    p = {"partition_id": pid, "ptype": ptype, "geometry": geometry,
         "layer_policy": policy, "width_prior": {"w_min": width[0], "w_max": width[1]},
         "current_a": current, "speed_class": speed}
    if planned_width is not None:
        p["planned_width"] = planned_width
    return p


def make_board(partitions, zones=None, registry=None, board_id="t-l2", r1=None):
    """构造 v5.board.v1 实例；hard_rules/stackup 取 V2 值（tests/fixtures_v2.py 口径）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
            {"id": "In1.Cu", "kind": "signal", "preferred_direction": "v", "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0},
        "zones": zones or [],
        "partitions": partitions,
        "nets": [{"net_id": "N-" + p["partition_id"], "net_class": p["ptype"],
                  "partitions": [p["partition_id"]]} for p in partitions],
        "hard_rules": {
            "R1": {"k_a": (r1 or {}).get("k_a", 0.4),
                   "floor_mm": (r1 or {}).get("floor_mm", 0.3)},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": registry if registry is not None else [gran_entry()],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "inline://l2-envelope-test",
            "source_sha256": hashlib.sha256(b"l2-envelope-test").hexdigest(),
            "adapter": "hand",
        },
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def c1_zone(capacity=4.3, zone_id="C1"):
    return {"zone_id": zone_id, "kind": "corridor",
            "rect": {"x_min": 30.0, "y_min": 16.0, "x_max": 36.0, "y_max": 24.0},
            "layers": "signal", "capacity": capacity, "note": "唯一通道"}


def ledger_board(with_pb=True, board_id="t-l2"):
    """V2 口径走廊板：P4 ribbon 声明占用 3.3 + PA 0.2（+ PB 0.2）穿越 C1（capacity 4.3）。

    group_types=() ⇒ 三个分区 ptype 互异、全单例透传（账本条目与 L1 分区一一对应）。
    """
    zones = [c1_zone()]
    parts = [
        part("P4", "BUS", (32.6, 4.0), (32.6, 36.0), width=(0.15, 0.15),
             speed="bus_8bit", planned_width=0.15,
             occupancy_mm=3.3, copper_band=(30.95, 34.25)),
        part("PA", "HS", (33.5, 4.0), (33.5, 36.0), width=(0.2, 0.2),
             speed="hs_125M", planned_width=0.2),
    ]
    if with_pb:
        parts.append(part("PB", "MISC", (34.5, 10.0), (34.5, 30.0),
                          width=(0.2, 0.2), planned_width=0.2))
    return make_board(parts, zones=zones, board_id=board_id,
                      registry=[gran_entry(group_types=())])


def by_ref(artifact):
    return {e["partition_ref"]: e for e in artifact["per_partition"]}


# --------------------------------------------------------------- 双跑字节等 / 工件头

def test_envelope_artifact_double_run_bytes_equal():
    board = ledger_board(with_pb=False)
    l1 = build_partition_artifact(board)
    a1 = build_envelope_artifact(board, l1)
    a2 = build_envelope_artifact(board, build_partition_artifact(board))
    assert envelope_artifact_bytes(a1) == envelope_artifact_bytes(a2)
    assert envelope_artifact_sha256(a1) == envelope_artifact_sha256(a2)
    assert envelope_artifact_bytes(a1) == canonical.canonical_json(a1)


def test_envelope_artifact_head_and_refs():
    board = ledger_board(with_pb=False, board_id="t-l2-head")
    art = build_envelope_artifact(board, build_partition_artifact(board))
    assert art["artifact"] == "v5.envelope.v1"
    assert art["board_id"] == "t-l2-head"
    assert art["board_sha256"] == board["provenance"]["board_sha256"]
    assert [e["partition_ref"] for e in art["per_partition"]] == ["P4", "PA"]  # with_pb=False


# --------------------------------------------------------------- 包络精确值

def test_envelope_exact_margin_coordinates():
    board = ledger_board(with_pb=False)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    e = by_ref(art)["P4"]  # 几何端点 bbox [32.6, 4.0]~[32.6, 36.0]
    assert e["envelope_mm"] == pytest.approx([32.0, 3.4, 33.2, 36.6], abs=1e-9)
    assert e["margin_mm"] == 0.6


def test_envelope_uses_merged_cluster_bbox():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "MISC", (2.5, 0.0), (3.5, 0.0))])  # 合并 → PG-1
    art = build_envelope_artifact(board, build_partition_artifact(board))
    assert art["per_partition"][0]["partition_ref"] == "PG-1"
    # 合并包围盒 [0,0]~[3.5,0] ± 0.6
    assert art["per_partition"][0]["envelope_mm"] == pytest.approx([-0.6, -0.6, 4.1, 0.6],
                                                                   abs=1e-9)


# --------------------------------------------------------------- 宽度先验（current_a 驱动）

def test_width_prior_current_zero_passthrough():
    board = ledger_board(with_pb=False)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    e = by_ref(art)["PA"]
    assert e["width_prior"] == {"w_min": 0.2, "w_max": 0.2}   # 原值透传
    assert e["optimal_width"] == 0.2                          # 保守最优 = w_min


def test_width_prior_current_driven_recompute():
    board = make_board([part("PP", "PWR", (0.0, 0.0), (1.0, 0.0),
                             width=(0.8, 1.6), current=2.0, speed="power")])
    art = build_envelope_artifact(board, build_partition_artifact(board))
    e = art["per_partition"][0]
    # 载流下限 max(0.4×2.0, 0.3)=0.8；工艺最小取既有 w_min=0.8 ⇒ w_min=0.8
    assert e["width_prior"]["w_min"] == pytest.approx(0.8)
    # 无显著提升封顶：w_ref/(1−5%) = 1.6/0.95
    assert e["width_prior"]["w_max"] == pytest.approx(1.6 / 0.95)
    assert e["optimal_width"] == pytest.approx(e["width_prior"]["w_min"])


def test_width_prior_uses_board_r1_params():
    board = make_board([part("PP", "PWR", (0.0, 0.0), (1.0, 0.0),
                             width=(0.3, 1.0), current=2.0)],
                       r1={"k_a": 0.5, "floor_mm": 0.3})
    art = build_envelope_artifact(board, build_partition_artifact(board))
    # 板内 R1 参数被消费：0.5×2.0=1.0 > fab 0.3 ⇒ w_min=1.0
    assert art["per_partition"][0]["width_prior"]["w_min"] == pytest.approx(1.0)


# --------------------------------------------------------------- 容量账本（V2 口径手算一致）

def test_ledger_golden_fits_4_0():
    board = ledger_board(with_pb=False)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    led = art["corridor_ledger"]["C1"]
    # V2 手算口径：3.3（ribbon 声明占用）+ 0.2 + 0.5×1 = 4.0 ≤ 4.3 → fits
    assert led["capacity_mm"] == pytest.approx(4.3)
    assert led["occupancy_mm"] == pytest.approx(4.0)
    assert led["slack_mm"] == pytest.approx(0.3)
    assert led["fits"] is True
    assert [e["net_id"] for e in led["entries"]] == ["N-P4", "N-PA"]  # 板注册序
    assert led["entries"][0]["declared_occupancy"] == 3.3
    assert led["entries"][0]["span"] == [30.95, 34.25]
    assert led["entries"][1]["copper_width"] == 0.2


def test_ledger_golden_not_fits_4_7():
    board = ledger_board(with_pb=True)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    led = art["corridor_ledger"]["C1"]
    # V2 手算口径：3.3 + 0.2 + 0.2 + 0.5×2 = 4.7 > 4.3 → not fits（双留 F.Cu 不可行同款）
    assert led["capacity_mm"] == pytest.approx(4.3)
    assert led["occupancy_mm"] == pytest.approx(4.7)
    assert led["slack_mm"] == pytest.approx(-0.4)
    assert led["fits"] is False
    assert len(led["entries"]) == 3


def test_ledger_canonical_bytes_stable_and_matches_capacity():
    board = ledger_board(with_pb=False)
    a1 = build_envelope_artifact(board, build_partition_artifact(board))
    a2 = build_envelope_artifact(board, build_partition_artifact(board))
    b1 = canonical.canonical_json(a1["corridor_ledger"])
    assert b1 == canonical.canonical_json(a2["corridor_ledger"])
    # 与 metrics.capacity 自有 ledger 口径逐字节一致
    entries_by = {"C1": [cap.CapacityEntry("N-P4", 0.15, declared_occupancy=3.3,
                                           span=[30.95, 34.25]),
                         cap.CapacityEntry("N-PA", 0.2)]}
    assert b1 == cap.ledger_bytes(entries_by, {"C1": 4.3})


def test_capacity_notes_per_partition():
    board = ledger_board(with_pb=False)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    refs = by_ref(art)
    assert refs["P4"]["capacity_notes"] == [
        {"zone_id": "C1", "partition_ref": "P4",
         "kind": "corridor_occupancy", "occupancy_mm": 3.3}]
    assert refs["PA"]["capacity_notes"][0]["occupancy_mm"] == pytest.approx(0.2)
    # 未命中走廊的分区无 note
    other = make_board([part("PZ", "MISC", (0.0, 0.0), (1.0, 0.0))])
    art2 = build_envelope_artifact(other, build_partition_artifact(other))
    assert art2["per_partition"][0]["capacity_notes"] == []


# --------------------------------------------------------------- 走廊边界情形 / fail-closed 对账

def test_corridor_without_capacity_skipped():
    zone = c1_zone()
    zone.pop("capacity")
    board = make_board([part("PA", "MISC", (33.0, 10.0), (33.0, 30.0))], zones=[zone])
    art = build_envelope_artifact(board, build_partition_artifact(board))
    assert art["corridor_ledger"] == {}          # 无容量声明 → 无账可核（文档化决定）


def test_empty_corridor_zero_occupancy():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))], zones=[c1_zone()])
    led = build_envelope_artifact(board, build_partition_artifact(board))["corridor_ledger"]["C1"]
    assert led["occupancy_mm"] == 0.0
    assert led["entries"] == []
    assert led["fits"] is True
    assert led["slack_mm"] == pytest.approx(4.3)


def test_board_artifact_mismatch_fails_closed():
    board = ledger_board(with_pb=False)
    l1 = build_partition_artifact(board)
    other = ledger_board(with_pb=True)           # 分区集不同 ⇒ board_sha256 不同
    with pytest.raises(EnvelopePlanError) as ei:
        build_envelope_artifact(other, l1)
    assert "board_sha256" in str(ei.value)
    renamed = ledger_board(with_pb=False, board_id="renamed")
    with pytest.raises(EnvelopePlanError) as ei2:
        build_envelope_artifact(renamed, l1)
    assert "board_id" in str(ei2.value)


def test_validate_envelope_artifact_rejects_corruptions():
    board = ledger_board(with_pb=False)
    art = build_envelope_artifact(board, build_partition_artifact(board))
    assert validate_envelope_artifact(art) is art

    bad_env = json.loads(json.dumps(art))
    bad_env["per_partition"][0]["envelope_mm"] = [0.0, 0.0]
    with pytest.raises(EnvelopePlanError) as ei:
        validate_envelope_artifact(bad_env)
    assert "per_partition[0].envelope_mm" in str(ei.value)

    bad_opt = json.loads(json.dumps(art))
    bad_opt["per_partition"][0]["optimal_width"] = 9.9   # ≠ w_min，违反保守最优合同
    with pytest.raises(EnvelopePlanError) as ei:
        validate_envelope_artifact(bad_opt)
    assert "optimal_width" in str(ei.value)

    bad_led = json.loads(json.dumps(art))
    bad_led["corridor_ledger"]["C1"]["fits"] = "yes"
    with pytest.raises(EnvelopePlanError) as ei:
        validate_envelope_artifact(bad_led)
    assert "corridor_ledger.C1.fits" in str(ei.value)
