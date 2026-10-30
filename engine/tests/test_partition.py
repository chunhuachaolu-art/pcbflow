# -*- coding: utf-8 -*-
"""L1 分区器测试：粒度溯源 fail-closed、确定性聚类、反事实、工件双跑字节等。"""
import hashlib
import json

import pytest

from v5 import canonical
from v5.board import compute_board_sha256
from v5.partition import (PartitionError, artifact_bytes, artifact_sha256,
                          build_partition_artifact, validate_partition_artifact)


# --------------------------------------------------------------- 夹具构造（内联小板）

def gran_entry(min_gap_mm=2.0, group_types=("BUS", "DIFF"), principle_id="P-PART-GRAN"):
    """分区聚类粒度先验条目（15 字段模板；source_hash=剔除自身后 canonical sha256）。"""
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
    """最小合法分区（schema 必填 7 字段 + 可选扩展）。"""
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


def make_board(partitions, zones=None, registry=None, board_id="t-l1", r1=None):
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
            "source_uri": "inline://l1-partition-test",
            "source_sha256": hashlib.sha256(b"l1-partition-test").hexdigest(),
            "adapter": "hand",
        },
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


# --------------------------------------------------------------- 双跑字节等 / 工件头

def test_artifact_double_run_bytes_equal():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "MISC", (10.0, 0.0), (11.0, 0.0))])
    a1 = build_partition_artifact(board)
    a2 = build_partition_artifact(board)
    assert artifact_bytes(a1) == artifact_bytes(a2)
    assert artifact_sha256(a1) == artifact_sha256(a2)
    assert artifact_bytes(a1) == canonical.canonical_json(a1)


def test_artifact_head_carries_board_provenance():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))], board_id="t-head")
    art = build_partition_artifact(board)
    assert art["artifact"] == "v5.partition.v1"
    assert art["board_id"] == "t-head"
    assert art["board_sha256"] == board["provenance"]["board_sha256"]
    assert validate_partition_artifact(art) is art


# --------------------------------------------------------------- 粒度先验 fail-closed

def test_missing_granularity_fails_closed():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))], registry=[])
    with pytest.raises(PartitionError) as ei:
        build_partition_artifact(board)
    text = str(ei.value)
    assert "principle_registry" in text          # 键路径
    assert "partition_granularity" in text       # 缺什么


def test_duplicate_granularity_fails_closed():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))],
                       registry=[gran_entry(), gran_entry(principle_id="P-PART-GRAN-2")])
    with pytest.raises(PartitionError) as ei:
        build_partition_artifact(board)
    text = str(ei.value)
    assert "2 条" in text
    assert "P-PART-GRAN" in text and "P-PART-GRAN-2" in text  # 多什么（列出全部 id）


def test_granularity_provenance_matches_board():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))],
                       registry=[gran_entry(min_gap_mm=2.0, group_types=("BUS", "DIFF"))])
    art = build_partition_artifact(board)
    # 键值与板内先验一致：数值参数逐条溯源到 principle_id
    assert art["granularity_provenance"] == [
        {"param": "min_gap_mm", "value": 2.0, "principle_id": "P-PART-GRAN"}]


def test_board_hash_tamper_fails_closed():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))])
    board["provenance"]["board_sha256"] = "0" * 64
    with pytest.raises(PartitionError) as ei:
        build_partition_artifact(board)
    assert "board_sha256" in str(ei.value)  # 入口内部 load_board 的哈希链复算拦截


# --------------------------------------------------------------- 聚类行为

def test_same_type_adjacent_merge():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "MISC", (2.5, 0.0), (3.5, 0.0))])  # 端点距 1.5 ≤ 2.0
    art = build_partition_artifact(board)
    assert [e["partition_id"] for e in art["partitions"]] == ["PG-1"]
    e = art["partitions"][0]
    assert e["source_partitions"] == ["PA", "PB"]          # 排序
    assert e["ptype"] == "MISC"                            # 成员共同 ptype
    assert e["net_ids"] == ["N-PA", "N-PB"]                # nets 反查并集
    assert e["geometry"]["endpoints"] == [[0.0, 0.0], [3.5, 0.0]]  # 包围盒对角
    assert "PA~PB" in e["note"] and "min_gap_mm" in e["note"]      # 合并理由留痕


def test_far_apart_no_merge_passthrough():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "MISC", (30.0, 0.0), (31.0, 0.0))])
    art = build_partition_artifact(board)
    assert [e["partition_id"] for e in art["partitions"]] == ["PA", "PB"]  # 原 id 透传
    for e in art["partitions"]:
        assert e["source_partitions"] == [e["partition_id"]]
        assert e["note"] == "未合并，原样透传"
    pa = art["partitions"][0]
    assert pa["ptype"] == "MISC"
    assert pa["width_prior"] == {"w_min": 0.2, "w_max": 0.2}
    assert pa["current_a"] == 0.0 and pa["speed_class"] == "low_speed"


def test_group_types_cross_type_merge():
    board = make_board([part("PA", "BUS", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "DIFF", (2.0, 0.0), (3.0, 0.0))])  # 距 1.0 ≤ 2.0
    art = build_partition_artifact(board)
    assert len(art["partitions"]) == 1
    e = art["partitions"][0]
    assert e["ptype"] == "BUS+DIFF"            # 跨类型合并：排序去重 "+" 连接（文档化）
    assert e["source_partitions"] == ["PA", "PB"]


def test_types_outside_group_do_not_merge():
    board = make_board([part("PA", "PWR", (0.0, 0.0), (1.0, 0.0)),
                        part("PB", "CLK", (2.0, 0.0), (3.0, 0.0))])
    art = build_partition_artifact(board)
    assert [e["partition_id"] for e in art["partitions"]] == ["PA", "PB"]


def test_copper_band_overlap_merges_far_endpoints():
    board = make_board([part("BA", "BUS", (0.0, 0.0), (2.0, 0.0), copper_band=(0.0, 5.0)),
                        part("BB", "BUS", (100.0, 0.0), (102.0, 0.0), copper_band=(4.0, 9.0))])
    art = build_partition_artifact(board)
    # 端点距 98 ≫ 2.0；仅靠 copper_band 区间重叠合并
    assert [e["partition_id"] for e in art["partitions"]] == ["PG-1"]
    assert "copper_band" in art["partitions"][0]["note"]


def test_copper_band_disjoint_no_merge():
    board = make_board([part("BA", "BUS", (0.0, 0.0), (2.0, 0.0), copper_band=(0.0, 3.0)),
                        part("BB", "BUS", (100.0, 0.0), (102.0, 0.0), copper_band=(4.0, 9.0))])
    art = build_partition_artifact(board)
    assert [e["partition_id"] for e in art["partitions"]] == ["BA", "BB"]


# --------------------------------------------------------------- 反事实（粒度先验驱动行为）

def _chain_board(min_gap):
    """三连 MISC：A-B 端点距 1.5，B-C 距 2.5（合并可传递）。"""
    return make_board([part("A", "MISC", (0.0, 0.0), (1.0, 0.0)),
                       part("B", "MISC", (2.5, 0.0), (3.5, 0.0)),
                       part("C", "MISC", (6.0, 0.0), (7.0, 0.0))],
                      registry=[gran_entry(min_gap_mm=min_gap, group_types=())])


def test_counterfactual_larger_gap_merges_more():
    base = build_partition_artifact(_chain_board(2.0))
    big = build_partition_artifact(_chain_board(5.0))
    assert len(base["partitions"]) == 2          # {A,B} + {C}
    assert len(big["partitions"]) == 1           # {A,B,C}
    # 合并数（粗分区条目数）随 min_gap_mm 增大不增（反事实单调性）
    assert len(big["partitions"]) <= len(base["partitions"])


def test_counterfactual_smaller_gap_merges_less():
    base = build_partition_artifact(_chain_board(2.0))
    small = build_partition_artifact(_chain_board(0.5))
    assert len(small["partitions"]) == 3         # 全部单例透传
    # 合并数（粗分区条目数）随 min_gap_mm 减小不减（反事实单调性）
    assert len(small["partitions"]) >= len(base["partitions"])


# --------------------------------------------------------------- 确定性编号 / 归属成员

def test_pg_numbering_by_min_member_lexicographic():
    board = make_board([part("PB", "MISC", (10.0, 0.0), (11.0, 0.0)),
                        part("PC", "MISC", (12.0, 0.0), (13.0, 0.0)),
                        part("PA", "MISC", (20.0, 0.0), (21.0, 0.0)),
                        part("PZ", "MISC", (22.0, 0.0), (23.0, 0.0))])
    art = build_partition_artifact(board)
    got = [(e["partition_id"], e["source_partitions"]) for e in art["partitions"]]
    # 簇按成员最小 id 字典序排：{PA,PZ} → PG-1，{PB,PC} → PG-2（与板注册序无关）
    assert got == [("PG-1", ["PA", "PZ"]), ("PG-2", ["PB", "PC"])]


def test_dominant_member_highest_current_wins():
    board = make_board([part("PX", "PWR", (0.0, 0.0), (1.0, 0.0),
                             width=(0.5, 0.9), current=0.5, speed="low_speed", policy="F.Cu"),
                        part("PY", "PWR", (2.0, 0.0), (3.0, 0.0),
                             width=(0.8, 1.6), current=2.0, speed="power", policy="B.Cu")])
    art = build_partition_artifact(board)
    assert len(art["partitions"]) == 1
    e = art["partitions"][0]
    assert e["current_a"] == 2.0                          # current_a 最大者胜
    assert e["width_prior"] == {"w_min": 0.8, "w_max": 1.6}
    assert e["layer_policy"] == "B.Cu"
    assert e["speed_class"] == "power"
    assert e["geometry"]["endpoints"] == [[0.0, 0.0], [3.0, 0.0]]  # 成员端点总体包围盒对角


# --------------------------------------------------------------- 工件形状自检

def test_validate_partition_artifact_rejects_corruptions():
    board = make_board([part("PA", "MISC", (0.0, 0.0), (1.0, 0.0))])
    art = build_partition_artifact(board)

    bad_tag = json.loads(json.dumps(art))
    bad_tag["artifact"] = "v4.partition.v1"
    with pytest.raises(PartitionError) as ei:
        validate_partition_artifact(bad_tag)
    assert "artifact" in str(ei.value)

    bad_prov = json.loads(json.dumps(art))
    del bad_prov["granularity_provenance"]
    with pytest.raises(PartitionError) as ei:
        validate_partition_artifact(bad_prov)
    assert "granularity_provenance" in str(ei.value)

    bad_src = json.loads(json.dumps(art))
    bad_src["partitions"][0]["source_partitions"] = ["PA", "PA"]  # 未去重
    with pytest.raises(PartitionError) as ei:
        validate_partition_artifact(bad_src)
    assert "source_partitions" in str(ei.value)

    bad_env = json.loads(json.dumps(art))
    bad_env["partitions"][0]["geometry"]["endpoints"] = [[3.0, 0.0], [0.0, 0.0]]  # 非升序
    with pytest.raises(PartitionError) as ei:
        validate_partition_artifact(bad_env)
    assert "geometry.endpoints" in str(ei.value)
